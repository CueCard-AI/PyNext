"""
PyNext Transpiler - Context Manager Emitters

=============================================================================
WHAT THIS FILE DOES
=============================================================================
Transpiles Python with statements to JavaScript try/finally blocks with
__enter__/__exit__ protocol support.

Handles:
- Single context manager: with resource() as r:
- Multiple context managers: with r1() as a, r2() as b:
- Async context managers: async with resource() as r:
- __enter__/__exit__ protocol
- __aenter__/__aexit__ protocol (async)

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================
Python's with statement provides resource management via context managers.
JavaScript doesn't have this, so we transpile to try/finally with explicit
__enter__/__exit__ calls.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    with resource() as r:      →    const r = await resource();
        use(r)                      try {
                                        await use(r);
                                    } finally {
                                        await r.__aexit__();
                                    }

=============================================================================
EXAMPLES
=============================================================================

Single Context Manager:
    Python:                          JavaScript:
    with open_file(path) as f:       const f = open_file(path);
        data = f.read()                  try {
                                        const data = f.read();
                                    } finally {
                                        f.__exit__();
                                    }

Multiple Context Managers:
    Python:                          JavaScript:
    with r1() as a, r2() as b:       const a = r1();
        process(a, b)                    try {
                                        const b = r2();
                                        try {
                                            process(a, b);
                                        } finally {
                                            b.__exit__();
                                        }
                                    } finally {
                                        a.__exit__();
                                    }
"""

from __future__ import annotations

from .nodes import With, WithItem
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


def _emit_with(node: With, indent: int) -> str:
    """
    Emit with statement to try/catch/finally pattern with proper exception handling.
    
    CRITICAL: Python's with statement:
    1. Calls __enter__() and assigns its return value
    2. On exception, passes (exc_type, exc_val, exc_tb) to __exit__
    3. If __exit__ returns True, exception is suppressed
    4. On normal exit, calls __exit__(None, None, None)
    
    JavaScript pattern:
        const _ctx = resource();
        const r = _ctx.__enter__();
        let _exc = null;
        try {
            use(r);
        } catch (_e) {
            _exc = _e;
            if (!_ctx.__exit__(_e.constructor, _e, _e.stack)) {
                throw _e;  // Re-throw if not suppressed
            }
        }
        if (!_exc) {
            _ctx.__exit__(null, null, null);
        }
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    emit_expr = _get_emit_expr()
    
    if not node.items:
        # Empty with statement
        body = "\n".join(emit(stmt, indent + 1) for stmt in node.body)
        return f"{prefix}try {{\n{body}\n{prefix}}}"
    
    # Handle multiple context managers with nested try/catch pattern
    lines = []
    context_vars = []  # Store context manager variables for __exit__ calls
    
    # Enter all context managers
    for i, item in enumerate(node.items):
        context_js = emit_expr(item.context_expr)
        
        # Create temporary variables
        ctx_var = f"_ctx{i}" if len(node.items) > 1 else "_ctx"
        exc_var = f"_exc{i}" if len(node.items) > 1 else "_exc"
        
        if item.is_async:
            # Async context manager
            lines.append(f"{prefix}const {ctx_var} = await {context_js};")
            if item.optional_vars:
                if isinstance(item.optional_vars, str):
                    var_name = safe_js_name(item.optional_vars)
                    lines.append(f"{prefix}const {var_name} = await {ctx_var}.__aenter__();")
                else:
                    var_name = safe_js_name(item.optional_vars[0] if item.optional_vars else "ctx")
                    lines.append(f"{prefix}const {var_name} = await {ctx_var}.__aenter__();")
            else:
                lines.append(f"{prefix}await {ctx_var}.__aenter__();")
        else:
            # Sync context manager
            lines.append(f"{prefix}const {ctx_var} = {context_js};")
            if item.optional_vars:
                if isinstance(item.optional_vars, str):
                    var_name = safe_js_name(item.optional_vars)
                    lines.append(f"{prefix}const {var_name} = {ctx_var}.__enter__();")
                else:
                    var_name = safe_js_name(item.optional_vars[0] if item.optional_vars else "ctx")
                    lines.append(f"{prefix}const {var_name} = {ctx_var}.__enter__();")
            else:
                lines.append(f"{prefix}{ctx_var}.__enter__();")
        
        # Initialize exception tracker
        lines.append(f"{prefix}let {exc_var} = null;")
        
        context_vars.append((ctx_var, exc_var, item.is_async))
    
    # Build nested try/catch blocks
    body_lines = []
    for stmt in node.body:
        body_lines.append(emit(stmt, indent + len(node.items)))
    
    if not body_lines:
        body_lines.append(f"{make_indent(indent + len(node.items))}/* pass */")
    
    current_indent = indent + len(node.items) - 1
    current_body = "\n".join(body_lines)
    
    # Add else clause if present
    if node.orelse:
        orelse_lines = []
        for stmt in node.orelse:
            orelse_lines.append(emit(stmt, current_indent + 1))
        orelse_body = "\n".join(orelse_lines)
        current_body += f"\n{make_indent(current_indent)}}} else {{\n{orelse_body}\n{make_indent(current_indent)}}}"
    
    # Wrap in try/catch for each context manager (innermost to outermost)
    for i in range(len(node.items) - 1, -1, -1):
        ctx_var, exc_var, is_async = context_vars[i]
        exit_method = "__aexit__" if is_async else "__exit__"
        ind = make_indent(current_indent)
        ind1 = make_indent(current_indent + 1)
        ind2 = make_indent(current_indent + 2)
        
        # Build try/catch/finally with proper exception handling
        try_block = f"{ind}try {{\n{current_body}\n{ind}}}"
        
        # Catch block: pass exception info to __exit__ and check if suppressed
        if is_async:
            catch_block = (
                f"{ind}catch (_e) {{\n"
                f"{ind1}{exc_var} = _e;\n"
                f"{ind1}const _suppressed = await {ctx_var}.{exit_method}(_e.constructor, _e, _e.stack || null);\n"
                f"{ind1}if (!_suppressed) {{\n"
                f"{ind2}throw _e;\n"
                f"{ind1}}}\n"
                f"{ind}}}"
            )
        else:
            catch_block = (
                f"{ind}catch (_e) {{\n"
                f"{ind1}{exc_var} = _e;\n"
                f"{ind1}const _suppressed = {ctx_var}.{exit_method}(_e.constructor, _e, _e.stack || null);\n"
                f"{ind1}if (!_suppressed) {{\n"
                f"{ind2}throw _e;\n"
                f"{ind1}}}\n"
                f"{ind}}}"
            )
        
        # Normal exit: call __exit__ with null args if no exception
        if is_async:
            normal_exit = (
                f"{ind}if (!{exc_var}) {{\n"
                f"{ind1}await {ctx_var}.{exit_method}(null, null, null);\n"
                f"{ind}}}"
            )
        else:
            normal_exit = (
                f"{ind}if (!{exc_var}) {{\n"
                f"{ind1}{ctx_var}.{exit_method}(null, null, null);\n"
                f"{ind}}}"
            )
        
        current_body = f"{try_block}\n{catch_block}\n{normal_exit}"
        current_indent -= 1
    
    lines.append(current_body)
    
    return "\n".join(lines)

