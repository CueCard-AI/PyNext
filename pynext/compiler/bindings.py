"""
PyNext Compiler - Reactive Bindings

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This module extracts reactive bindings from Python component templates. A 
binding connects a DOM node to one or more signals, enabling fine-grained
DOM updates when signals change (SolidJS-style reactivity).

When a signal changes, only the specific DOM nodes that depend on it update.
No Virtual DOM diffing required.

=============================================================================
BINDING TYPES
=============================================================================

1. TEXT - Signal value in text content
   span()[count()]  →  text updates when count changes

2. ATTR - Signal value in an attribute
   div(class_=active_class())  →  class updates when active_class changes

3. SHOW - Conditional visibility
   Show(when=lambda: visible())[content]  →  show/hide when visible changes

4. FOR - List rendering
   For(each=lambda: items())[...]  →  add/remove/reorder when items changes

5. STYLE - Dynamic styles
   div(style=lambda: f"opacity: {opacity()}")  →  style updates

6. CLASS - Dynamic class list
   button(class_=lambda: "btn " + ("active" if selected() else ""))

=============================================================================
HOW IT WORKS
=============================================================================

1. Server renders HTML with data-pynext-* attributes marking reactive nodes
2. Hydration data includes a "bindings" array
3. Client runtime creates effects for each binding
4. When signal changes, the effect runs and updates the specific DOM node

=============================================================================
"""

from __future__ import annotations

import ast
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Any, Callable


class BindingType(Enum):
    """Types of reactive bindings."""
    TEXT = "text"           # Text content: span()[count()]
    ATTR = "attr"           # Attribute: div(id=computed_id())
    CLASS = "class"         # Class list: div(class_=...)
    STYLE = "style"         # Style: div(style=...)
    SHOW = "show"           # Conditional: Show(when=...)
    FOR = "for"             # List: For(each=...)
    SWITCH = "switch"       # Multi-branch: Switch()[...]
    PROP = "prop"           # Generic property


@dataclass
class Binding:
    """
    A reactive binding between a DOM node and signal(s).
    
    Attributes:
        node_id: ID of the DOM element (e.g., "el_abc123_1")
        type: Type of binding (text, attr, show, etc.)
        signal_deps: List of signal IDs this binding depends on
        update_expr: JavaScript expression to compute the new value
        attr_name: For ATTR/CLASS/STYLE, which attribute to update
        initial_value: Server-rendered initial value (for hydration)
    """
    node_id: str
    type: BindingType
    signal_deps: List[str]
    update_expr: str
    attr_name: Optional[str] = None
    initial_value: Any = None


@dataclass
class BindingExtractor:
    """
    Extracts reactive bindings from a rendered component.
    
    Used during server rendering to collect all reactive expressions
    and generate the binding data for hydration.
    """
    bindings: List[Binding] = field(default_factory=list)
    signal_map: Dict[str, str] = field(default_factory=dict)  # name -> id
    _node_counter: int = 0
    _render_id: str = ""
    
    def set_render_id(self, render_id: str) -> None:
        """Set the render ID for element ID generation."""
        self._render_id = render_id
    
    def set_signal_map(self, signal_map: Dict[str, str]) -> None:
        """Set mapping from signal names to IDs."""
        self.signal_map = signal_map
    
    def next_node_id(self) -> str:
        """Generate the next unique node ID."""
        self._node_counter += 1
        return f"el_{self._render_id}_{self._node_counter}"
    
    def add_text_binding(
        self,
        node_id: str,
        signal_name: str,
        initial_value: Any = None,
    ) -> None:
        """Add a text content binding."""
        signal_id = self.signal_map.get(signal_name, signal_name)
        
        binding = Binding(
            node_id=node_id,
            type=BindingType.TEXT,
            signal_deps=[signal_id],
            update_expr=f"__pynext__.getSignal('{signal_id}').read()",
            initial_value=initial_value,
        )
        self.bindings.append(binding)
    
    def add_attr_binding(
        self,
        node_id: str,
        attr_name: str,
        signal_deps: List[str],
        update_expr: str,
        initial_value: Any = None,
    ) -> None:
        """Add an attribute binding."""
        # Convert signal names to IDs
        signal_ids = [self.signal_map.get(s, s) for s in signal_deps]
        
        binding = Binding(
            node_id=node_id,
            type=BindingType.ATTR,
            signal_deps=signal_ids,
            update_expr=update_expr,
            attr_name=attr_name,
            initial_value=initial_value,
        )
        self.bindings.append(binding)
    
    def add_class_binding(
        self,
        node_id: str,
        signal_deps: List[str],
        update_expr: str,
        initial_value: str = "",
    ) -> None:
        """Add a class binding."""
        signal_ids = [self.signal_map.get(s, s) for s in signal_deps]
        
        binding = Binding(
            node_id=node_id,
            type=BindingType.CLASS,
            signal_deps=signal_ids,
            update_expr=update_expr,
            attr_name="class",
            initial_value=initial_value,
        )
        self.bindings.append(binding)
    
    def add_style_binding(
        self,
        node_id: str,
        signal_deps: List[str],
        update_expr: str,
        initial_value: str = "",
    ) -> None:
        """Add a style binding."""
        signal_ids = [self.signal_map.get(s, s) for s in signal_deps]
        
        binding = Binding(
            node_id=node_id,
            type=BindingType.STYLE,
            signal_deps=signal_ids,
            update_expr=update_expr,
            attr_name="style",
            initial_value=initial_value,
        )
        self.bindings.append(binding)
    
    def add_show_binding(
        self,
        node_id: str,
        signal_deps: List[str],
        condition_expr: str,
        initial_visible: bool = True,
    ) -> None:
        """Add a Show/hide binding."""
        signal_ids = [self.signal_map.get(s, s) for s in signal_deps]
        
        binding = Binding(
            node_id=node_id,
            type=BindingType.SHOW,
            signal_deps=signal_ids,
            update_expr=condition_expr,
            initial_value=initial_visible,
        )
        self.bindings.append(binding)
    
    def add_for_binding(
        self,
        node_id: str,
        signal_deps: List[str],
        each_expr: str,
        template_id: str,
        key_expr: Optional[str] = None,
    ) -> None:
        """Add a For loop binding."""
        signal_ids = [self.signal_map.get(s, s) for s in signal_deps]
        
        binding = Binding(
            node_id=node_id,
            type=BindingType.FOR,
            signal_deps=signal_ids,
            update_expr=each_expr,
            attr_name=template_id,  # Store template ID in attr_name
            initial_value={"key": key_expr} if key_expr else None,
        )
        self.bindings.append(binding)
    
    def to_hydration_data(self) -> List[Dict[str, Any]]:
        """Convert bindings to hydration data format."""
        result = []
        
        for binding in self.bindings:
            data = {
                "nodeId": binding.node_id,
                "type": binding.type.value,
                "signals": binding.signal_deps,
                "update": binding.update_expr,
            }
            
            if binding.attr_name:
                data["attr"] = binding.attr_name
            
            if binding.initial_value is not None:
                data["initial"] = binding.initial_value
            
            result.append(data)
        
        return result
    
    def clear(self) -> None:
        """Clear all bindings."""
        self.bindings = []
        self._node_counter = 0


# =============================================================================
# SIGNAL DEPENDENCY DETECTION
# =============================================================================

def find_signal_deps_in_expr(
    expr: str,
    signal_names: Set[str],
) -> List[str]:
    """
    Find signal dependencies in a Python expression string.
    
    Looks for patterns like:
    - signal_name()  (signal read)
    - signal_name.set(...)  (signal write - not a dep)
    
    Args:
        expr: Python expression as string
        signal_names: Known signal names
    
    Returns:
        List of signal names that are read in the expression
    """
    deps = []
    
    try:
        tree = ast.parse(expr, mode='eval')
        deps = _find_signal_reads_in_ast(tree, signal_names)
    except SyntaxError:
        # If parsing fails, do simple string matching
        for name in signal_names:
            if f"{name}()" in expr:
                deps.append(name)
    
    return deps


def _find_signal_reads_in_ast(
    node: ast.AST,
    signal_names: Set[str],
) -> List[str]:
    """Find signal reads in an AST node."""
    reads: Set[str] = set()
    
    class SignalReadVisitor(ast.NodeVisitor):
        def visit_Call(self, call_node: ast.Call):
            # Check for signal() pattern
            if isinstance(call_node.func, ast.Name):
                name = call_node.func.id
                if name in signal_names:
                    reads.add(name)
            
            # Continue visiting
            self.generic_visit(call_node)
    
    visitor = SignalReadVisitor()
    visitor.visit(node)
    
    return list(reads)


def extract_signal_deps_from_callable(
    func: Callable,
    signal_names: Set[str],
) -> List[str]:
    """
    Extract signal dependencies from a callable (lambda or function).
    
    Uses source code inspection to find signal reads.
    """
    import inspect
    
    try:
        source = inspect.getsource(func)
        return find_signal_deps_in_expr(source, signal_names)
    except (OSError, TypeError):
        # Can't get source - inspect closure variables
        deps = []
        if hasattr(func, '__closure__') and func.__closure__:
            for cell in func.__closure__:
                try:
                    obj = cell.cell_contents
                    if hasattr(obj, '_name') and obj._name in signal_names:
                        deps.append(obj._name)
                    elif hasattr(obj, '_id'):
                        # It's a signal object
                        deps.append(obj._id)
                except (ValueError, AttributeError):
                    pass
        return deps


# =============================================================================
# PYTHON TO JAVASCRIPT EXPRESSION CONVERSION
# =============================================================================

def python_expr_to_js(
    expr: str,
    signal_map: Dict[str, str],
) -> str:
    """
    Convert a Python expression to JavaScript.
    
    Handles:
    - Signal reads: count() → __pynext__.getSignal('sig_1').read()
    - String formatting: f"text {x}" → `text ${x}`
    - Ternary: a if b else c → b ? a : c
    - Comparisons: == → ===, != → !==
    
    Args:
        expr: Python expression string
        signal_map: Mapping from signal names to IDs
    
    Returns:
        JavaScript expression string
    """
    try:
        tree = ast.parse(expr, mode='eval')
        return _ast_to_js(tree.body, signal_map)
    except SyntaxError:
        # Fallback: simple string replacement
        js = expr
        for name, sig_id in signal_map.items():
            js = js.replace(f"{name}()", f"__pynext__.getSignal('{sig_id}').read()")
        return js


def _ast_to_js(node: ast.AST, signal_map: Dict[str, str]) -> str:
    """Convert an AST node to JavaScript."""
    
    if isinstance(node, ast.Constant):
        return json.dumps(node.value)
    
    if isinstance(node, ast.Name):
        return node.id
    
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            name = node.func.id
            # Signal read
            if name in signal_map:
                sig_id = signal_map[name]
                return f"__pynext__.getSignal('{sig_id}').read()"
            # Regular function call
            args = ", ".join(_ast_to_js(a, signal_map) for a in node.args)
            return f"{name}({args})"
        
        if isinstance(node.func, ast.Attribute):
            obj = _ast_to_js(node.func.value, signal_map)
            method = node.func.attr
            args = ", ".join(_ast_to_js(a, signal_map) for a in node.args)
            return f"{obj}.{method}({args})"
    
    if isinstance(node, ast.BinOp):
        left = _ast_to_js(node.left, signal_map)
        right = _ast_to_js(node.right, signal_map)
        
        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
        }
        op = op_map.get(type(node.op), "+")
        return f"({left} {op} {right})"
    
    if isinstance(node, ast.Compare):
        left = _ast_to_js(node.left, signal_map)
        
        for op, comp in zip(node.ops, node.comparators):
            right = _ast_to_js(comp, signal_map)
            
            if isinstance(op, ast.Eq):
                left = f"({left} === {right})"
            elif isinstance(op, ast.NotEq):
                left = f"({left} !== {right})"
            elif isinstance(op, ast.Lt):
                left = f"({left} < {right})"
            elif isinstance(op, ast.LtE):
                left = f"({left} <= {right})"
            elif isinstance(op, ast.Gt):
                left = f"({left} > {right})"
            elif isinstance(op, ast.GtE):
                left = f"({left} >= {right})"
        
        return left
    
    if isinstance(node, ast.IfExp):
        test = _ast_to_js(node.test, signal_map)
        body = _ast_to_js(node.body, signal_map)
        orelse = _ast_to_js(node.orelse, signal_map)
        return f"({test} ? {body} : {orelse})"
    
    if isinstance(node, ast.BoolOp):
        op = "&&" if isinstance(node.op, ast.And) else "||"
        values = [_ast_to_js(v, signal_map) for v in node.values]
        return f"({' '.join([values[0]] + [f'{op} {v}' for v in values[1:]])})"
    
    if isinstance(node, ast.UnaryOp):
        operand = _ast_to_js(node.operand, signal_map)
        if isinstance(node.op, ast.Not):
            return f"!{operand}"
        elif isinstance(node.op, ast.USub):
            return f"-{operand}"
        return operand
    
    if isinstance(node, ast.Subscript):
        value = _ast_to_js(node.value, signal_map)
        if isinstance(node.slice, ast.Constant):
            key = json.dumps(node.slice.value)
        else:
            key = _ast_to_js(node.slice, signal_map)
        return f"{value}[{key}]"
    
    if isinstance(node, ast.Attribute):
        value = _ast_to_js(node.value, signal_map)
        return f"{value}.{node.attr}"
    
    if isinstance(node, ast.JoinedStr):
        # f-string → template literal
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                expr = _ast_to_js(value.value, signal_map)
                parts.append(f"${{{expr}}}")
        return f"`{''.join(parts)}`"
    
    if isinstance(node, ast.List):
        elements = ", ".join(_ast_to_js(e, signal_map) for e in node.elts)
        return f"[{elements}]"
    
    if isinstance(node, ast.Dict):
        pairs = []
        for k, v in zip(node.keys, node.values):
            if k is None:
                continue
            key = _ast_to_js(k, signal_map)
            val = _ast_to_js(v, signal_map)
            pairs.append(f"{key}: {val}")
        return f"{{{', '.join(pairs)}}}"
    
    # Fallback
    return "null"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "BindingType",
    "Binding", 
    "BindingExtractor",
    "find_signal_deps_in_expr",
    "extract_signal_deps_from_callable",
    "python_expr_to_js",
]

