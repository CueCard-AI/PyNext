"""
PyNext Transpiler - Generator Emitters

=============================================================================
WHAT THIS FILE DOES
=============================================================================
Transpiles Python generator functions (with yield/yield from) to JavaScript
generator functions (function*), preserving Python generator semantics.

Handles:
- Generator functions (def with yield)
- yield expressions
- yield from expressions (generator delegation)
- Generator protocol (send, throw, close)

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================
Python generators use yield to create iterators. JavaScript has native
generator functions (function*) that work similarly, but we need to:
1. Detect generator functions (contain yield)
2. Emit function* instead of function
3. Handle yield and yield from correctly
4. Support generator protocol (send, throw, close)

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    FunctionDef with yield
         │
         ▼
    ┌─────────────────────────────────────────────────────────┐
    │  Check if function contains yield                       │
    │      │                                                   │
    │      ├── Yes → Emit as function*                        │
    │      │   - yield → yield                                │
    │      │   - yield from → yield*                          │
    │      │                                                   │
    │      └── No → Emit as regular function                  │
    └─────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================
- emitter.py: Calls generator emitters when emitting functions with yield
- Functions with yield: Automatically use generator transpilation

=============================================================================
EXAMPLES
=============================================================================

Generator Function:
    Python:                          JavaScript:
    def countdown(n):                function* countdown(n) {
        while n > 0:                     while (n > 0) {
            yield n                         yield n;
            n -= 1                          n -= 1;
                                        }
                                    }

Yield From:
    Python:                          JavaScript:
    def flatten(nested):            function* flatten(nested) {
        for item in nested:             for (const item of nested) {
            if isinstance(item, list):      if (Array.isArray(item)) {
                yield from flatten(item)        yield* flatten(item);
            else:                           } else {
                yield item                      yield item;
                                            }
                                        }
                                    }
"""

from __future__ import annotations

from .nodes import Yield, YieldFrom, FunctionDef
from ._internal.utils import make_indent, safe_js_name
from ._internal.scope import get_scope


def _get_emit():
    """Lazy import to avoid circular dependency."""
    from .emitter import emit
    return emit


def _get_emit_expr():
    """Lazy import to avoid circular dependency."""
    from .emitter import _emit_expr
    return _emit_expr


def _method_contains_yield(node) -> bool:
    """
    Check if a method contains yield or yield from (Phase 33.2).
    
    Works with both FunctionDef and MethodDef nodes.
    """
    def has_yield(n):
        if isinstance(n, (Yield, YieldFrom)):
            return True
        # Check children - only if n is iterable and not a string/primitive
        if hasattr(n, 'body') and isinstance(n.body, (list, tuple)):
            for child in n.body:
                if has_yield(child):
                    return True
        if hasattr(n, 'value') and n.value:
            if has_yield(n.value):
                return True
        if hasattr(n, 'test') and n.test:
            if has_yield(n.test):
                return True
        if hasattr(n, 'orelse') and isinstance(n.orelse, (list, tuple)):
            for child in n.orelse:
                if has_yield(child):
                    return True
        # Check for other iterable attributes
        for attr_name in ['args', 'keywords', 'patterns', 'cases', 'items']:
            if hasattr(n, attr_name):
                attr_value = getattr(n, attr_name)
                if isinstance(attr_value, (list, tuple)):
                    for child in attr_value:
                        if has_yield(child):
                            return True
        return False
    
    # Check method body
    if hasattr(node, 'body') and isinstance(node.body, (list, tuple)):
        for stmt in node.body:
            if has_yield(stmt):
                return True
    return False


def _function_contains_yield(node: FunctionDef) -> bool:
    """
    Check if a function contains yield or yield from.
    
    Recursively searches the function body for Yield or YieldFrom nodes.
    """
    return _method_contains_yield(node)


def _emit_yield(node: Yield, indent: int) -> str:
    """
    Emit yield expression.
    
    Examples:
        yield value     → yield value;
        yield           → yield;
    """
    prefix = make_indent(indent)
    emit_expr = _get_emit_expr()
    
    if node.value:
        value_js = emit_expr(node.value)
        return f"{prefix}yield {value_js};"
    else:
        return f"{prefix}yield;"


def _emit_yield_from(node: YieldFrom, indent: int) -> str:
    """
    Emit yield from expression.
    
    Examples:
        yield from gen  → yield* gen;
    """
    prefix = make_indent(indent)
    emit_expr = _get_emit_expr()
    
    value_js = emit_expr(node.value)
    return f"{prefix}yield* {value_js};"


def _emit_generator_function(node: FunctionDef, indent: int) -> str:
    """
    Emit generator function (function*).
    
    This is called when a function contains yield/yield from.
    The function is emitted as a JavaScript generator function.
    
    Phase 33.2: Marks the function as a generator in scope so calls to it
    can be wrapped with wrapGenerator to add send(), throw(), close().
    """
    from .functions import _build_params_full
    from ._internal.scope import get_scope
    
    prefix = make_indent(indent)
    emit = _get_emit()
    
    # Phase 33.2: Mark this function as a generator in scope
    scope = get_scope()
    scope.declare_generator_function(safe_js_name(node.name))
    
    # Build function signature with * for generator
    params_list = _build_params_full(node)
    params_js = ", ".join(params_list) if params_list else ""
    signature = f"function* {safe_js_name(node.name)}({params_js})"
    
    # Emit body
    body_lines = []
    for stmt in node.body:
        body_lines.append(emit(stmt, indent + 1))
    
    if not body_lines:
        body_lines.append(f"{prefix}    /* pass */")
    
    body = "\n".join(body_lines)
    
    return f"{prefix}{signature} {{\n{body}\n{prefix}}}"


def _emit_generator_method(node, indent: int) -> str:
    """
    Emit generator method (*methodName) within a class (Phase 33.2).
    
    Examples:
        def items(self):        → *items() {
            yield item               yield item;
                                → }
    """
    from .nodes import MethodDef
    from ._internal.utils import make_indent, safe_js_name
    from .functions import _build_params_full
    from .classes import _replace_self_with_this, _transform_super_calls
    
    prefix = make_indent(indent)
    inner_ind = make_indent(indent + 1)
    emit = _get_emit()
    
    # Build method signature with * for generator
    # Convert MethodDef to FunctionDef-like structure for parameter building
    class MethodParams:
        posonly_args = getattr(node, 'posonly_args', ())
        posonly_defaults = getattr(node, 'posonly_defaults', ())
        args = node.args
        defaults = node.defaults
        vararg = getattr(node, 'vararg', None)
        kwarg = getattr(node, 'kwarg', None)
        kwonly_args = getattr(node, 'kwonly_args', ())
        kwonly_defaults = getattr(node, 'kwonly_defaults', ())
    
    method_params = MethodParams()
    params_list = _build_params_full(method_params)
    params_js = ", ".join(params_list) if params_list else ""
    
    # Build prefix (static, async, etc.)
    method_prefix = ""
    if node.is_async:
        method_prefix += "async "
    if node.is_static or node.is_classmethod:
        method_prefix += "static "
    
    # Generator methods use *methodName syntax
    method_name = safe_js_name(node.name)
    signature = f"{method_prefix}*{method_name}({params_js})"
    
    # Emit body
    body_lines = []
    is_constructor = node.name == "constructor"
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Replace self. with this. (avoiding string literals)
        emitted = _replace_self_with_this(emitted)
        # Transform super() calls
        emitted = _transform_super_calls(emitted, is_constructor)
        body_lines.append(emitted)
    
    if not body_lines:
        body_lines.append(f"{inner_ind}/* pass */")
    
    body = "\n".join(body_lines)
    
    return f"{prefix}{signature} {{\n{body}\n{prefix}}}"

