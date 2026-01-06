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
    Emit with statement to try/finally pattern.
    
    CRITICAL: Python's with statement calls __enter__() and assigns its return value.
    We must:
    1. Store the context manager object in a temporary variable
    2. Call __enter__() and assign its return value to the user's variable
    3. Call __exit__() on the original context manager object (not the user's variable)
    
    Examples:
        with resource() as r:     → const _ctx = resource();
                                        const r = _ctx.__enter__();
                                        try { use(r); } finally { _ctx.__exit__(); }
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    emit_expr = _get_emit_expr()
    
    if not node.items:
        # Empty with statement
        body = "\n".join(emit(stmt, indent + 1) for stmt in node.body)
        return f"{prefix}try {{\n{body}\n{prefix}}}"
    
    # Handle multiple context managers with nested try/finally
    lines = []
    context_vars = []  # Store context manager variables for __exit__ calls
    
    # Enter all context managers
    for i, item in enumerate(node.items):
        context_js = emit_expr(item.context_expr)
        
        # Create a temporary variable for the context manager itself
        # Use _ctx for single context manager, _ctx0, _ctx1, etc. for multiple
        ctx_var = f"_ctx{i}" if len(node.items) > 1 else "_ctx"
        
        if item.is_async:
            # Async context manager
            lines.append(f"{prefix}const {ctx_var} = await {context_js};")
            if item.optional_vars:
                if isinstance(item.optional_vars, str):
                    var_name = safe_js_name(item.optional_vars)
                    lines.append(f"{prefix}const {var_name} = await {ctx_var}.__aenter__();")
                else:
                    # Multiple variables (tuple unpacking)
                    # For now, handle as single variable
                    var_name = safe_js_name(item.optional_vars[0] if item.optional_vars else "ctx")
                    lines.append(f"{prefix}const {var_name} = await {ctx_var}.__aenter__();")
            else:
                lines.append(f"{prefix}await {ctx_var}.__aenter__();")
        else:
            # Sync context manager - CRITICAL: Call __enter__() and assign its return value
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
        
        context_vars.append((ctx_var, item.is_async))
    
    # Build nested try/finally blocks
    # Start with innermost (last item)
    body_lines = []
    for stmt in node.body:
        body_lines.append(emit(stmt, indent + len(node.items)))
    
    if not body_lines:
        body_lines.append(f"{make_indent(indent + len(node.items))}/* pass */")
    
    # Build nested structure
    current_indent = indent + len(node.items) - 1
    current_body = "\n".join(body_lines)
    
    # Add else clause if present
    if node.orelse:
        orelse_lines = []
        for stmt in node.orelse:
            orelse_lines.append(emit(stmt, current_indent + 1))
        orelse_body = "\n".join(orelse_lines)
        current_body += f"\n{make_indent(current_indent)}}} else {{\n{orelse_body}\n{make_indent(current_indent)}}}"
    
    # Wrap in try/finally for each context manager (innermost to outermost)
    # Use the stored context manager variables for __exit__ calls
    for i in range(len(node.items) - 1, -1, -1):
        ctx_var, is_async = context_vars[i]
        exit_method = "__aexit__" if is_async else "__exit__"
        
        try_block = f"{make_indent(current_indent)}try {{\n{current_body}\n{make_indent(current_indent)}}}"
        finally_block = f"{make_indent(current_indent)}finally {{\n{make_indent(current_indent + 1)}"
        
        if is_async:
            finally_block += f"await {ctx_var}.{exit_method}();"
        else:
            finally_block += f"{ctx_var}.{exit_method}();"
        
        finally_block += f"\n{make_indent(current_indent)}}}"
        
        current_body = f"{try_block}\n{finally_block}"
        current_indent -= 1
    
    lines.append(current_body)
    
    return "\n".join(lines)

