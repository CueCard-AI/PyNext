"""
PyNext Compiler - Analyzer (Dependency Analysis)

=============================================================================
WHAT THIS FILE DOES
=============================================================================

The analyzer is the SECOND stage of the compiler pipeline. It takes the IR
from the parser and analyzes signal dependencies to enable SolidJS-style
fine-grained updates.

    IR (from parser) → [ANALYZER] → IR (with dependencies)

For each handler and effect, the analyzer determines:
- Which signals are READ (dependencies)
- Which signals are WRITTEN (mutations)

This information is CRITICAL for generating optimized JavaScript that only
updates exactly what changed.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

React re-renders entire components when state changes. This is SLOW.

SolidJS (and PyNext) do SURGICAL UPDATES - only the exact DOM nodes that
depend on a signal are updated. To achieve this, we need to know:

    "When signal X changes, which DOM nodes need to update?"

The analyzer builds this dependency graph by walking the AST and finding
all signal reads (x()) and writes (x.set(), x.update()).

Example:
```python
@island
def Counter():
    count = signal(0)
    name = signal("hello")
    
    # When count changes, only _el0's text updates
    # When name changes, nothing updates (it's not read)
    return button(onclick=lambda: count.set(count() + 1))[count()]
```

The analyzer produces:
- handler.reads = ["count"]
- handler.writes = ["count"]
- dom_tree reactive bindings depend on ["count"]

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    IslandIR (from parser)
         │
         ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │  For each handler:                                                     │
    │      handler.reads  = find_signal_reads(handler.body)   # count()     │
    │      handler.writes = find_signal_writes(handler.body)  # count.set() │
    │                                                                        │
    │  For each effect:                                                      │
    │      effect.dependencies = find_signal_reads(effect.body)             │
    │                                                                        │
    │  For each memo:                                                        │
    │      memo.dependencies = find_signal_reads(memo.fn)                   │
    │                                                                        │
    │  For reactive DOM nodes:                                               │
    │      node.dependencies = find_signal_reads(node.expr)                 │
    │                                                                        │
    │  Check for unused signals → Warning                                    │
    │  Check for infinite loops → Error                                      │
    └───────────────────────────────────────────────────────────────────────┘
         │
         ▼
    IslandIR (with dependencies filled in)

=============================================================================
WHO USES THIS
=============================================================================

- __init__.py: Called after parse_island()
- emitter.py: Uses dependency info to generate createEffect() calls

=============================================================================
WHEN TO USE (vs Alternatives)
=============================================================================

Always called as part of compile_island(). You typically don't call
analyze_dependencies() directly unless debugging.

=============================================================================
COMPILATION (Input → Output)
=============================================================================

INPUT (handler from parser):
```
HandlerDef(
    event="click",
    element_id="_el0",
    body=Lambda(body=Call(
        func=Attribute(value=Name("count"), attr="set"),
        args=[BinOp(left=Call(func=Name("count")), op=Add, right=Constant(1))]
    )),
    reads=[],   # Empty!
    writes=[],  # Empty!
)
```

OUTPUT (handler with dependencies):
```
HandlerDef(
    event="click",
    element_id="_el0",
    body=...,
    reads=["count"],   # count() is read
    writes=["count"],  # count.set() is called
)
```
=============================================================================
"""

from __future__ import annotations

import ast
from typing import List, Set, Dict, Optional
from dataclasses import dataclass

from .parser import IslandIR, DOMNode, DOMNodeType, HandlerDef, EffectDef, MemoDef
from .errors import CompileWarning, unused_signal


def analyze_dependencies(ir: IslandIR) -> IslandIR:
    """
    Analyze signal dependencies in the island IR.
    
    This function walks through all handlers, effects, memos, and reactive
    DOM expressions to determine which signals they read and write.
    
    Args:
        ir: IslandIR from the parser
    
    Returns:
        The same IslandIR with dependency information filled in
    
    Example:
        >>> ir = parse_island(source, "counter.py")
        >>> ir = analyze_dependencies(ir)
        >>> 
        >>> for handler in ir.handlers:
        ...     print(f"{handler.event}: reads={handler.reads}, writes={handler.writes}")
    """
    # Analyze handlers
    for handler in ir.handlers:
        handler.reads = _find_signal_reads(handler.body, ir.signal_names, ir.memo_names)
        handler.writes = _find_signal_writes(handler.body, ir.signal_names)
    
    # Analyze effects
    for effect in ir.effects:
        effect.dependencies = _find_signal_reads(effect.body, ir.signal_names, ir.memo_names)
    
    # Analyze memos
    for memo in ir.memos:
        if memo.fn:
            memo.dependencies = _find_signal_reads(memo.fn, ir.signal_names, ir.memo_names)
    
    # Analyze reactive DOM nodes
    if ir.dom_tree:
        _analyze_dom_dependencies(ir.dom_tree, ir.signal_names, ir.memo_names)
    
    # Check for unused signals
    used_signals = _collect_all_reads(ir)
    for sig in ir.signals:
        if sig.name not in used_signals:
            ir.warnings.append(unused_signal(ir.filename, sig.line, sig.name))
    
    return ir


def _find_signal_reads(node: ast.AST, signal_names: Set[str], memo_names: Set[str]) -> List[str]:
    """
    Find all signal/memo reads in an AST node.
    
    A signal read is: count() - calling the signal to get its value
    A memo read is: doubled() - calling the memo to get its value
    
    Args:
        node: AST node to analyze
        signal_names: Set of known signal names
        memo_names: Set of known memo names
    
    Returns:
        List of signal/memo names that are read
    """
    reads: Set[str] = set()
    
    class ReadVisitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            # Check for signal/memo call: count()
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if name in signal_names or name in memo_names:
                    reads.add(name)
            
            # Continue visiting children
            self.generic_visit(node)
    
    visitor = ReadVisitor()
    visitor.visit(node)
    
    return list(reads)


def _find_signal_writes(node: ast.AST, signal_names: Set[str]) -> List[str]:
    """
    Find all signal writes in an AST node.
    
    A signal write is:
    - count.set(x) - setting a new value
    - count.update(fn) - updating via function
    
    Args:
        node: AST node to analyze
        signal_names: Set of known signal names
    
    Returns:
        List of signal names that are written
    """
    writes: Set[str] = set()
    
    class WriteVisitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            # Check for signal.set() or signal.update()
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ("set", "update"):
                    if isinstance(node.func.value, ast.Name):
                        name = node.func.value.id
                        if name in signal_names:
                            writes.add(name)
            
            # Continue visiting children
            self.generic_visit(node)
    
    visitor = WriteVisitor()
    visitor.visit(node)
    
    return list(writes)


def _analyze_dom_dependencies(node: DOMNode, signal_names: Set[str], memo_names: Set[str]) -> None:
    """
    Analyze dependencies in DOM tree, adding dependency info to nodes.
    
    This modifies DOMNode objects in place to add dependency information.
    """
    # Analyze reactive expression
    if node.type == DOMNodeType.REACTIVE and node.expr:
        deps = _find_signal_reads(node.expr, signal_names, memo_names)
        # Store dependencies in control_props (reusing existing field)
        node.control_props["dependencies"] = deps
    
    # Analyze reactive attributes
    for attr_name, attr_expr in node.reactive_attrs.items():
        deps = _find_signal_reads(attr_expr, signal_names, memo_names)
        # Store per-attribute dependencies
        if "attr_deps" not in node.control_props:
            node.control_props["attr_deps"] = {}
        node.control_props["attr_deps"][attr_name] = deps
    
    # Analyze control flow props
    if node.type == DOMNodeType.CONTROL:
        for prop_name, prop_value in list(node.control_props.items()):
            if isinstance(prop_value, ast.AST):
                deps = _find_signal_reads(prop_value, signal_names, memo_names)
                node.control_props[f"{prop_name}_deps"] = deps
    
    # Recurse into children
    for child in node.children:
        _analyze_dom_dependencies(child, signal_names, memo_names)


def _collect_all_reads(ir: IslandIR) -> Set[str]:
    """Collect all signal/memo names that are read anywhere."""
    used: Set[str] = set()
    
    # From handlers
    for handler in ir.handlers:
        used.update(handler.reads)
    
    # From effects
    for effect in ir.effects:
        used.update(effect.dependencies)
    
    # From memos
    for memo in ir.memos:
        used.update(memo.dependencies)
    
    # From DOM tree
    if ir.dom_tree:
        used.update(_collect_dom_reads(ir.dom_tree))
    
    return used


def _collect_dom_reads(node: DOMNode) -> Set[str]:
    """Collect all signal reads from DOM tree."""
    reads: Set[str] = set()
    
    # From reactive expression
    if "dependencies" in node.control_props:
        reads.update(node.control_props["dependencies"])
    
    # From reactive attributes
    if "attr_deps" in node.control_props:
        for deps in node.control_props["attr_deps"].values():
            reads.update(deps)
    
    # From control flow
    for key, value in node.control_props.items():
        if key.endswith("_deps") and isinstance(value, list):
            reads.update(value)
    
    # From children
    for child in node.children:
        reads.update(_collect_dom_reads(child))
    
    return reads


# =============================================================================
# ADVANCED ANALYSIS (for optimization)
# =============================================================================

def find_reactive_boundaries(ir: IslandIR) -> Dict[str, List[str]]:
    """
    Find which DOM elements depend on which signals.
    
    Returns a mapping from element_id to list of signal dependencies.
    This is used by the emitter to generate minimal createEffect() calls.
    
    Example return:
        {
            "_el0": ["count"],          # Button text depends on count
            "_el1": ["name", "count"],  # Div content depends on both
        }
    """
    boundaries: Dict[str, List[str]] = {}
    
    if ir.dom_tree:
        _collect_boundaries(ir.dom_tree, boundaries)
    
    return boundaries


def _collect_boundaries(node: DOMNode, boundaries: Dict[str, List[str]]) -> None:
    """Recursively collect reactive boundaries."""
    
    deps: Set[str] = set()
    
    # Collect from reactive expression
    if "dependencies" in node.control_props:
        deps.update(node.control_props["dependencies"])
    
    # Collect from reactive attributes
    if "attr_deps" in node.control_props:
        for attr_deps in node.control_props["attr_deps"].values():
            deps.update(attr_deps)
    
    if deps and node.element_id:
        boundaries[node.element_id] = list(deps)
    
    # Recurse
    for child in node.children:
        _collect_boundaries(child, boundaries)


def detect_infinite_loops(ir: IslandIR) -> List[CompileWarning]:
    """
    Detect potential infinite loops in reactive updates.
    
    An infinite loop can occur when:
    - An effect reads AND writes the same signal
    - A memo depends on itself (circular dependency)
    
    Returns:
        List of warnings about potential infinite loops
    """
    warnings: List[CompileWarning] = []
    
    # Check effects
    for effect in ir.effects:
        # Find what the effect writes
        writes = _find_signal_writes(effect.body, ir.signal_names)
        
        # If it reads and writes the same signal, warn
        for sig in writes:
            if sig in effect.dependencies:
                warnings.append(CompileWarning(
                    message=f"Effect '{effect.name}' reads and writes signal '{sig}' - potential infinite loop",
                    filename=ir.filename,
                    line=effect.line,
                    suggestion=f"Use untrack() to read '{sig}' without tracking, or split into separate effects",
                    warning_code="W100",
                ))
    
    # Check for circular memo dependencies
    memo_deps = {m.name: set(m.dependencies) for m in ir.memos}
    
    for memo_name, deps in memo_deps.items():
        visited: Set[str] = set()
        if _has_circular_dep(memo_name, memo_deps, visited, ir.memo_names):
            warnings.append(CompileWarning(
                message=f"Memo '{memo_name}' has circular dependency",
                filename=ir.filename,
                suggestion="Memos cannot depend on themselves directly or indirectly",
                warning_code="W101",
            ))
    
    return warnings


def _has_circular_dep(name: str, memo_deps: Dict[str, Set[str]], visited: Set[str], memo_names: Set[str]) -> bool:
    """Check if a memo has circular dependencies."""
    if name in visited:
        return True
    
    if name not in memo_deps:
        return False
    
    visited.add(name)
    
    for dep in memo_deps[name]:
        if dep in memo_names:  # Only check memo deps, not signal deps
            if _has_circular_dep(dep, memo_deps, visited.copy(), memo_names):
                return True
    
    return False


def compute_update_order(ir: IslandIR) -> List[str]:
    """
    Compute the order in which signals/memos should be updated.
    
    This ensures that when a signal changes:
    1. First, memos that depend on it recompute
    2. Then, effects that depend on signals OR memos run
    
    Returns:
        List of names in update order (signals first, then memos by dependency)
    """
    order: List[str] = []
    
    # Signals come first (they're the sources)
    for sig in ir.signals:
        order.append(sig.name)
    
    # Topological sort memos by dependencies
    remaining_memos = list(ir.memos)
    memo_names = {m.name for m in ir.memos}
    added: Set[str] = set(order)
    
    while remaining_memos:
        # Find memos whose dependencies are all satisfied
        for memo in remaining_memos[:]:
            deps_in_memos = set(memo.dependencies) & memo_names
            if deps_in_memos <= added:
                order.append(memo.name)
                added.add(memo.name)
                remaining_memos.remove(memo)
                break
        else:
            # No progress - there might be a cycle
            # Just add remaining in any order
            for memo in remaining_memos:
                order.append(memo.name)
            break
    
    return order

