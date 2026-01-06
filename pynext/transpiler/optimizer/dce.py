"""
PyNext Transpiler Optimizer - Dead Code Elimination

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Removes unused code and collects runtime dependencies for tree-shaking.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

1. Importing the full __py runtime adds code that may not be needed
2. Some code paths are unreachable (if False:, etc.)
3. Unused imports increase bundle size

=============================================================================
FEATURES
=============================================================================

1. Collect runtime dependencies (which __py.* functions are used)
2. Remove unreachable code (if False:, if True: else:)
3. Generate minimal import statement

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler import parse
from pynext.transpiler.optimizer.dce import collect_runtime_deps

ir = parse("x = items[-1]; y = x > 0")
deps = collect_runtime_deps(ir)
# → {"at"}  (only __py.at is used)
```
"""

from __future__ import annotations
from dataclasses import replace
from typing import Set

from pynext.transpiler.nodes import (
    JSNode, Program,
    If, IfExp, ExprStmt,
    Name, Constant, BinOp, Call, Attribute,
)
from ._internal.visitor import IRVisitor


# =============================================================================
# PUBLIC API
# =============================================================================

def collect_runtime_deps(ir: Program) -> Set[str]:
    """
    Collect all __py.* methods used in the IR.
    
    Returns a set of method names like {"bool", "at", "eq"}.
    """
    deps = set()
    collector = RuntimeDepCollector()
    collector.visit(ir)
    return collector.deps


def eliminate_dead_code(ir: Program) -> Program:
    """
    Remove unreachable code from the IR.
    
    - if False: ... → removed
    - if True: ... else: ... → just the if body
    """
    optimizer = DCEOptimizer()
    return optimizer.visit(ir)


def generate_import(deps: Set[str]) -> str:
    """
    Generate minimal import statement for the given dependencies.
    
    Args:
        deps: Set of __py method names like {"bool", "at"}
    
    Returns:
        Import statement like "import { __py_bool, __py_at } from 'pynext/runtime';"
    """
    if not deps:
        return ""
    
    # Sort for consistent output
    sorted_deps = sorted(deps)
    imports = ", ".join(f"__py_{d}" for d in sorted_deps)
    return f"import {{ {imports} }} from 'pynext/runtime';"


def count_unreachable_blocks(ir: Program) -> int:
    """Count blocks that will be eliminated."""
    count = 0
    
    def visit(node):
        nonlocal count
        
        if isinstance(node, If):
            if is_always_false(node.test):
                count += 1
            elif is_always_true(node.test) and node.orelse:
                count += 1
        
        # Recurse
        for attr in ['body', 'orelse']:
            child = getattr(node, attr, None)
            if child is not None:
                for c in child:
                    visit(c)
    
    for stmt in ir.body:
        visit(stmt)
    
    return count


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_always_true(node: JSNode) -> bool:
    """Check if a node is always True."""
    if isinstance(node, Constant):
        return node.value is True or (isinstance(node.value, int) and node.value != 0)
    return False


def is_always_false(node: JSNode) -> bool:
    """Check if a node is always False."""
    if isinstance(node, Constant):
        return node.value is False or node.value == 0 or node.value is None
    return False


# =============================================================================
# RUNTIME DEPENDENCY COLLECTOR
# =============================================================================

class RuntimeDepCollector(IRVisitor):
    """Collects __py.* dependencies from the IR."""
    
    def __init__(self):
        self.deps: Set[str] = set()
    
    def visit_Call(self, node: Call) -> Call:
        """Check if this is a __py.* call and record the dependency."""
        if isinstance(node.func, Attribute):
            if isinstance(node.func.value, Name):
                if node.func.value.id == "__py":
                    self.deps.add(node.func.attr)
        
        # Continue visiting children
        return self.generic_visit(node)


# =============================================================================
# DCE OPTIMIZER
# =============================================================================

class DCEOptimizer(IRVisitor):
    """
    Optimizer that eliminates dead code.
    """
    
    def __init__(self):
        self.eliminated_count = 0
    
    def visit_Program(self, node: Program) -> Program:
        """Process program, filtering out dead statements."""
        new_body = []
        
        for stmt in node.body:
            result = self.visit(stmt)
            if result is not None:
                if isinstance(result, (list, tuple)):
                    new_body.extend(result)
                else:
                    new_body.append(result)
        
        return replace(node, body=tuple(new_body))
    
    def visit_If(self, node: If) -> JSNode:
        """Handle if statements - remove unreachable branches."""
        # Check for always-true condition
        if is_always_true(node.test):
            self.eliminated_count += 1
            # Return just the body statements
            return tuple(self.visit(stmt) for stmt in node.body)
        
        # Check for always-false condition
        if is_always_false(node.test):
            self.eliminated_count += 1
            if node.orelse:
                # Return just the else statements
                return tuple(self.visit(stmt) for stmt in node.orelse)
            else:
                # Remove entirely
                return None
        
        # Otherwise, process normally
        return self.generic_visit(node)
    
    def visit_IfExp(self, node: IfExp) -> JSNode:
        """Handle IfExp (ternary) - simplify when condition is constant."""
        # Check for always-true condition
        if is_always_true(node.test):
            self.eliminated_count += 1
            # Return just the body (true branch)
            return self.visit(node.body)
        
        # Check for always-false condition
        if is_always_false(node.test):
            self.eliminated_count += 1
            # Return just the orelse (false branch)
            return self.visit(node.orelse)
        
        # Otherwise, process normally
        return self.generic_visit(node)


# =============================================================================
# STATISTICS
# =============================================================================

def get_dep_stats(ir: Program) -> dict:
    """Get statistics about runtime dependencies."""
    deps = collect_runtime_deps(ir)
    
    return {
        "total_deps": len(deps),
        "deps": sorted(deps),
        "has_bool": "bool" in deps,
        "has_eq": "eq" in deps,
        "has_at": "at" in deps,
        "has_slice": "slice" in deps,
        "has_add": "add" in deps,
        "has_mul": "mul" in deps,
        "has_mod": "mod" in deps,
    }
