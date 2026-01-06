from __future__ import annotations

"""
PyNext Transpiler - Control Flow Emitters

Phase 33.1: Control flow transpilation including:
- if/elif/else statements
- for loops (including for...else)
- while loops (including while...else)
- try/except/finally statements
- assert statements
"""

from .nodes import (
    For, ForUnpack, While, Try, Assert,
    Call, Attribute, Constant, Compare, BoolOp, UnaryOp, NamedExpr, JSNode
)
from ._internal.utils import make_indent, safe_js_name
from ._internal.exception_context import (
    push_exception_context,
    pop_exception_context,
)


def _get_emit():
    """Lazy import to avoid circular dependency."""
    from .emitter import emit
    return emit


def _get_emit_expr():
    """Lazy import to avoid circular dependency."""
    from .emitter import _emit_expr
    return _emit_expr


def _collect_named_exprs(node: JSNode) -> list[str]:
    """
    Recursively collect all variable names from NamedExpr (walrus) nodes.
    
    Used to pre-declare variables before conditions that use walrus operator.
    
    Example:
        if (x := get_value()):  → needs "let x;" before the if
    """
    result = []
    
    if isinstance(node, NamedExpr):
        result.append(node.target)
        # Also check the value for nested walrus
        result.extend(_collect_named_exprs(node.value))
    elif hasattr(node, '__dataclass_fields__'):
        # Recursively check all fields
        for field_name in node.__dataclass_fields__:
            field_value = getattr(node, field_name)
            if isinstance(field_value, JSNode):
                result.extend(_collect_named_exprs(field_value))
            elif isinstance(field_value, (list, tuple)):
                for item in field_value:
                    if isinstance(item, JSNode):
                        result.extend(_collect_named_exprs(item))
    
    return result


def _needs_bool_wrapper(node: JSNode) -> bool:
    """
    Determine if an expression needs __py.bool() wrapper for truthiness check.
    
    Returns False (no wrapper needed) for:
    - Comparisons (x > 0, a == b) - always return boolean
    - BoolOp (and, or) - already handle truthiness internally
    - UnaryOp with 'not' - already uses __py.bool
    - Literal True/False - already boolean
    - Call to bool() - already boolean
    
    Returns True (wrapper needed) for:
    - Variables (could be empty list/dict)
    - Function calls (could return empty list/dict)
    - Subscripts, attributes, etc.
    
    This prevents the Python/JS semantic difference where:
    - Python: if []: is falsy
    - JavaScript: if ([]) is truthy
    """
    # Comparisons always return boolean
    if isinstance(node, Compare):
        return False
    
    # BoolOp already handles truthiness
    if isinstance(node, BoolOp):
        return False
    
    # UnaryOp 'not' already uses __py.bool
    if isinstance(node, UnaryOp) and node.op == "not":
        return False
    
    # Literal booleans
    if isinstance(node, Constant):
        if isinstance(node.value, bool):
            return False
    
    # NamedExpr (walrus) - check the value
    if isinstance(node, NamedExpr):
        return _needs_bool_wrapper(node.value)
    
    # Everything else needs wrapper (could be empty list/dict)
    return True


def _emit_truthiness(node: JSNode) -> str:
    """
    Emit an expression with proper Python truthiness semantics.
    
    Wraps in __py.bool() when needed to handle:
    - Empty list [] being falsy in Python but truthy in JS
    - Empty dict {} being falsy in Python but truthy in JS
    - Empty string being falsy
    - 0 and None being falsy
    """
    _emit_expr = _get_emit_expr()
    expr_js = _emit_expr(node)
    
    if _needs_bool_wrapper(node):
        return f"__py.bool({expr_js})"
    else:
        return expr_js


def _is_dict_method(node: Call, methods: tuple) -> bool:
    """Check if a call is a dict method like .keys(), .values(), .items()"""
    if isinstance(node.func, Attribute):
        return node.func.attr in methods
    return False


def _emit_for(node: For, indent: int) -> str:
    """
    Emit for loop.
    """
    prefix = make_indent(indent)
    target = safe_js_name(node.target)
    lines = []
    emit = _get_emit()
    _emit_expr = _get_emit_expr()

    if node.is_range and node.range_args:
        # for i in range(...) → for (let i = start; i < stop; i += step)
        lines.append(_emit_for_range(node, indent))
    else:
        # Regular for-of loop
        iter_js = _emit_expr(node.iter)
        
        # Phase 33.1: Handle for...else - use flag to track if loop completed normally
        has_else = len(node.orelse) > 0
        if has_else:
            lines.append(f"{prefix}let _loop_completed = true;")
        
        # Check if iterating over dict method (already returns iterable)
        if isinstance(node.iter, Call) and _is_dict_method(node.iter, ("keys", "values", "items")):
            lines.append(f"{prefix}for (const {target} of {iter_js}) {{")
        else:
            # Wrap with __py.iter() to handle dicts (iterate keys) and other iterables
            lines.append(f"{prefix}for (const {target} of __py.iter({iter_js})) {{")

        for stmt in node.body:
            emitted = emit(stmt, indent + 1)
            # Phase 33.1: Track break statements for for...else
            if has_else and "break" in emitted:
                # Insert _loop_completed = false before break
                emitted = emitted.replace("break;", "_loop_completed = false;\n" + make_indent(indent + 1) + "break;")
            lines.append(emitted)
        
        lines.append(f"{prefix}}}")
        
        # Phase 33.1: Emit else clause if loop completed normally
        if has_else:
            lines.append(f"{prefix}if (_loop_completed) {{")
            for stmt in node.orelse:
                lines.append(emit(stmt, indent + 1))
            lines.append(f"{prefix}}}")

    return "\n".join(lines)


def _emit_for_range(node: For, indent: int) -> str:
    """Emit for-range loop with C-style for."""
    prefix = make_indent(indent)
    target = safe_js_name(node.target)
    lines = []
    emit = _get_emit()
    _emit_expr = _get_emit_expr()
    
    # Phase 33.1: Handle for...else - use flag to track if loop completed normally
    has_else = len(node.orelse) > 0
    if has_else:
        lines.append(f"{prefix}let _loop_completed = true;")
    
    args = node.range_args
    if len(args) == 1:
        # range(stop)
        stop_js = _emit_expr(args[0])
        lines.append(f"{prefix}for (let {target} = 0; {target} < {stop_js}; {target}++) {{")
    elif len(args) == 2:
        # range(start, stop)
        start_js = _emit_expr(args[0])
        stop_js = _emit_expr(args[1])
        lines.append(f"{prefix}for (let {target} = {start_js}; {target} < {stop_js}; {target}++) {{")
    else:
        # range(start, stop, step)
        start_js = _emit_expr(args[0])
        stop_js = _emit_expr(args[1])
        step_js = _emit_expr(args[2])
        
        # Handle negative step
        if isinstance(args[2], Constant) and isinstance(args[2].value, (int, float)):
            if args[2].value < 0:
                lines.append(f"{prefix}for (let {target} = {start_js}; {target} > {stop_js}; {target} += {step_js}) {{")
            else:
                lines.append(f"{prefix}for (let {target} = {start_js}; {target} < {stop_js}; {target} += {step_js}) {{")
        else:
            # Dynamic step - use conditional
            lines.append(f"{prefix}for (let {target} = {start_js}; ({step_js} > 0 ? {target} < {stop_js} : {target} > {stop_js}); {target} += {step_js}) {{")
    
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Phase 33.1: Track break statements for for...else
        if has_else and "break" in emitted:
            # Insert _loop_completed = false before break
            emitted = emitted.replace("break;", "_loop_completed = false;\n" + make_indent(indent + 1) + "break;")
        lines.append(emitted)
    
    lines.append(f"{prefix}}}")
    
    # Phase 33.1: Emit else clause if loop completed normally
    if has_else:
        lines.append(f"{prefix}if (_loop_completed) {{")
        for stmt in node.orelse:
            lines.append(emit(stmt, indent + 1))
        lines.append(f"{prefix}}}")
    
    return "\n".join(lines)


def _emit_for_unpack(node: ForUnpack, indent: int) -> str:
    """
    Emit for loop with tuple unpacking: for a, b in items.
    """
    prefix = make_indent(indent)
    lines = []
    emit = _get_emit()
    _emit_expr = _get_emit_expr()
    
    # Phase 33.1: Handle for...else - use flag to track if loop completed normally
    has_else = len(node.orelse) > 0
    if has_else:
        lines.append(f"{prefix}let _loop_completed = true;")
    
    # Build destructuring pattern
    targets_parts = []
    for t in node.targets:
        if t.startswith("*"):
            targets_parts.append(f"...{safe_js_name(t[1:])}")
        else:
            targets_parts.append(safe_js_name(t))
    targets_js = ", ".join(targets_parts)
    
    iter_js = _emit_expr(node.iter)
    
    # Use __py.iter() to handle both arrays and dicts
    lines.append(f"{prefix}for (const [{targets_js}] of __py.iter({iter_js})) {{")
    
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Phase 33.1: Track break statements for for...else
        if has_else and "break" in emitted:
            # Insert _loop_completed = false before break
            emitted = emitted.replace("break;", "_loop_completed = false;\n" + make_indent(indent + 1) + "break;")
        lines.append(emitted)
    
    lines.append(f"{prefix}}}")
    
    # Phase 33.1: Emit else clause if loop completed normally
    if has_else:
        lines.append(f"{prefix}if (_loop_completed) {{")
        for stmt in node.orelse:
            lines.append(emit(stmt, indent + 1))
        lines.append(f"{prefix}}}")
    
    return "\n".join(lines)


def _emit_while(node: While, indent: int) -> str:
    """
    Emit while loop.
    
    Handles:
    - Walrus operator by pre-declaring variables
    - Python truthiness with __py.bool() wrapper when needed
    """
    prefix = make_indent(indent)
    lines = []
    emit = _get_emit()
    
    # Check for walrus operator in condition and pre-declare
    walrus_vars = _collect_named_exprs(node.test)
    for var in walrus_vars:
        lines.append(f"{prefix}let {var};")
    
    # Phase 33.1: Handle while...else - use flag to track if loop completed normally
    has_else = len(node.orelse) > 0
    if has_else:
        lines.append(f"{prefix}let _loop_completed = true;")
    
    # Wrap test in __py.bool() if needed for Python truthiness
    test_js = _emit_truthiness(node.test)
    lines.append(f"{prefix}while ({test_js}) {{")
    
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Phase 33.1: Track break statements for while...else
        if has_else and "break" in emitted:
            # Insert _loop_completed = false before break
            emitted = emitted.replace("break;", "_loop_completed = false;\n" + make_indent(indent + 1) + "break;")
        lines.append(emitted)
    
    lines.append(f"{prefix}}}")
    
    # Phase 33.1: Emit else clause if loop completed normally
    if has_else:
        lines.append(f"{prefix}if (_loop_completed) {{")
        for stmt in node.orelse:
            lines.append(emit(stmt, indent + 1))
        lines.append(f"{prefix}}}")
    
    return "\n".join(lines)


def _map_exception_type(exc_type: str) -> str:
    """
    Map Python exception type to JavaScript condition.
    
    Most Python exceptions don't have direct JS equivalents, so we
    check for the exception name as a property or use a generic check.
    """
    # Standard Python exceptions that might be emulated
    PYTHON_TO_JS = {
        "Exception": "true",  # Catches everything
        "BaseException": "true",
        "ValueError": "_e instanceof Error && _e.name === 'ValueError'",
        "TypeError": "_e instanceof TypeError",
        "KeyError": "_e instanceof Error && _e.name === 'KeyError'",
        "IndexError": "_e instanceof RangeError",
        "AttributeError": "_e instanceof Error && _e.name === 'AttributeError'",
        "RuntimeError": "_e instanceof Error && _e.name === 'RuntimeError'",
        "ZeroDivisionError": "_e instanceof Error && _e.name === 'ZeroDivisionError'",
        "StopIteration": "_e instanceof Error && _e.name === 'StopIteration'",
    }
    
    return PYTHON_TO_JS.get(exc_type, f"_e instanceof Error && _e.name === '{exc_type}'")


def _emit_try(node: Try, indent: int) -> str:
    """
    Emit try/except/else/finally statement.
    
    JavaScript try/catch differs from Python's except:
    - Python can match exception types: except ValueError
    - Python can bind exception: except ValueError as e
    - Python can have multiple except clauses
    - Python has else clause (runs if no exception)
    
    We emit:
        try {
            ...body...
        } catch (_e) {
            if (_e instanceof ValueError) { let e = _e; ...handler... }
            else if (_e instanceof TypeError) { ...handler... }
            else { ...bare except handler... }
        } finally {
            ...finalbody...
        }
    
    The else clause is tricky - it runs only if no exception was raised.
    We use a flag variable to track this:
        let _no_exc = true;
        try {
            ...body...
        } catch (_e) {
            _no_exc = false;
            ...handlers...
        } finally {
            if (_no_exc) { ...orelse... }
            ...finalbody...
        }
    """
    prefix = make_indent(indent)
    inner_prefix = make_indent(indent + 1)
    lines = []
    emit = _get_emit()
    
    has_else = len(node.orelse) > 0
    has_finally = len(node.finalbody) > 0
    has_handlers = len(node.handlers) > 0
    
    # If there's an else clause, we need a flag to track whether exception occurred
    if has_else:
        lines.append(f"{prefix}let _no_exc = true;")
    
    # try block
    lines.append(f"{prefix}try {{")
    for stmt in node.body:
        lines.append(emit(stmt, indent + 1))
    lines.append(f"{prefix}}}")
    
    # catch block
    if has_handlers:
        lines.append(f"{prefix}catch (_e) {{")
        
        # Phase 33.3: Track exception context for automatic __context__ setting
        # Push _e onto exception context stack so raises inside handlers set __context__
        push_exception_context("_e")
        
        if has_else:
            lines.append(f"{inner_prefix}_no_exc = false;")
        
        # Emit handler conditions
        first_handler = True
        has_bare_except = False
        
        for handler in node.handlers:
            if handler.type is None:
                # Bare except: - always matches
                has_bare_except = True
                if first_handler:
                    lines.append(f"{inner_prefix}{{")
                else:
                    lines.append(f"{inner_prefix}}} else {{")
                
                # Bind exception variable if named
                if handler.name:
                    lines.append(f"{make_indent(indent + 2)}let {handler.name} = _e;")
                
                for stmt in handler.body:
                    lines.append(emit(stmt, indent + 2))
                
                lines.append(f"{inner_prefix}}}")
                break  # Bare except catches everything
            else:
                # Typed except: except ValueError as e:
                exc_type = handler.type
                
                # Map Python exception types to JS equivalents
                js_exc_type = _map_exception_type(exc_type)
                
                if first_handler:
                    lines.append(f"{inner_prefix}if ({js_exc_type}) {{")
                else:
                    lines.append(f"{inner_prefix}}} else if ({js_exc_type}) {{")
                
                first_handler = False
                
                # Bind exception variable if named
                if handler.name:
                    lines.append(f"{make_indent(indent + 2)}let {handler.name} = _e;")
                
                for stmt in handler.body:
                    lines.append(emit(stmt, indent + 2))
        
        # Close last handler if not bare except
        if not has_bare_except and has_handlers:
            lines.append(f"{inner_prefix}}}")
        
        # Phase 33.3: Pop exception context when leaving catch block
        pop_exception_context()
        
        lines.append(f"{prefix}}}")
    
    # finally block (or else handling)
    if has_finally or has_else:
        if has_finally:
            lines.append(f"{prefix}finally {{")
        
        if has_else:
            # Else runs only if no exception
            if has_finally:
                lines.append(f"{inner_prefix}if (_no_exc) {{")
                for stmt in node.orelse:
                    lines.append(emit(stmt, indent + 2))
                lines.append(f"{inner_prefix}}}")
            else:
                # No finally, emit else as a standalone block after try/catch
                lines.append(f"{prefix}if (_no_exc) {{")
                for stmt in node.orelse:
                    lines.append(emit(stmt, indent + 1))
                lines.append(f"{prefix}}}")
        
        if has_finally:
            for stmt in node.finalbody:
                lines.append(emit(stmt, indent + 1))
            lines.append(f"{prefix}}}")
    
    return "\n".join(lines)


def _emit_assert(node: Assert, indent: int) -> str:
    """
    Emit an assert statement.
    
    Examples:
        assert x > 0                    → if (!(x > 0)) {
                                        →     throw new Error("AssertionError");
                                        → }
        
        assert x > 0, "must be pos"     → if (!(x > 0)) {
                                        →     throw new Error("AssertionError: must be pos");
                                        → }
    """
    ind = make_indent(indent)
    inner_ind = make_indent(indent + 1)
    _emit_expr = _get_emit_expr()
    
    test = _emit_expr(node.test)
    
    if node.msg:
        msg_expr = _emit_expr(node.msg)
        error_msg = f'"AssertionError: " + {msg_expr}'
    else:
        error_msg = '"AssertionError"'
    
    return (
        f"{ind}if (!({test})) {{\n"
        f"{inner_ind}throw new Error({error_msg});\n"
        f"{ind}}}"
    )

