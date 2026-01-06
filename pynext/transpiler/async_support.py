"""
PyNext Transpiler - Async/Await Emitters

=============================================================================
WHAT THIS FILE DOES
=============================================================================
Transpiles Python async/await constructs to JavaScript async/await.

Handles:
- async def → async function (regular async functions)
- async def with yield → async function* (async generators)
- await expressions
- async for → for await
- async with → async try/finally (handled by context.py)
- asyncio.gather → Promise.all

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================
Python's async/await is similar to JavaScript's, but we need to:
1. Detect async functions and emit async function
2. Detect async generators (async def with yield) and emit async function*
3. Handle await expressions correctly
4. Convert async for to for await
5. Map asyncio.gather to Promise.all

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

Regular Async Function:
    async def fetch():           →    async function fetch() {
        data = await get()           const data = await get();
        return data                  return data;
                                    }

Async Generator:
    async def gen():             →    async function* gen() {
        yield await get()            yield await get();
                                    }

=============================================================================
EXAMPLES
=============================================================================

Async Function:
    Python:                          JavaScript:
    async def fetch():               async function fetch() {
        data = await get()               const data = await get();
        return data                      return data;
                                    }

Async Generator:
    Python:                          JavaScript:
    async def gen():                 async function* gen() {
        yield await get()                yield await get();
                                    }

Async For:
    Python:                          JavaScript:
    async for item in gen():         for await (const item of gen()) {
        await process(item)              await process(item);
                                    }

Async With:
    Python:                          JavaScript:
    async with resource() as r:      const r = await resource();
        await use(r)                     try {
                                            await use(r);
                                        } finally {
                                            await r.__aexit__();
                                        }
"""

from __future__ import annotations

from .nodes import AsyncFunctionDef, Await, For
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


def _emit_async_function_def(node: AsyncFunctionDef, indent: int) -> str:
    """
    Emit async function definition (regular async function or async generator).
    
    WHAT: Transpiles AsyncFunctionDef IR nodes to JavaScript async functions.
          Detects if the function contains yield/yield from and emits as
          `async function*` (async generator) or `async function` (regular async).
    
    WHY: Async generators enable progressive data loading, real-time streams,
         and chunked processing. They need different JavaScript syntax
         (`async function*`) and runtime support (`wrapAsyncGenerator`).
    
    HOW: 
        1. Check if AsyncFunctionDef contains Yield or YieldFrom nodes
        2. If yes: emit as `async function*` and mark as async generator in scope
        3. If no: emit as `async function` (regular async function)
        4. Emit function body (which may contain yield expressions)
    
    WHO: Called by emitter.py when emitting AsyncFunctionDef nodes.
    
    WHEN: During the emission phase, after parsing and IR transformation.
    
    WHERE: Part of async_support.py, called by the main emitter dispatch.
    
    Args:
        node: AsyncFunctionDef IR node to emit
        indent: Indentation level for the emitted code
    
    Returns:
        JavaScript source code for the async function or async generator
    
    Examples:
        Regular async function:
            Python:                          JavaScript:
            async def fetch():               async function fetch() {
                return await get()               return await get();
            }                               }
        
        Async generator:
            Python:                          JavaScript:
            async def gen():                 async function* gen() {
                yield await get()                yield await get();
            }                               }
        
        Async generator with yield from:
            Python:                          JavaScript:
            async def gen():                 async function* gen() {
                yield from other()               yield* other();
            }                               }
    
    Edge Cases:
        - Empty body: Emits `/* pass */` comment
        - Nested functions: Yield in nested functions doesn't affect detection
        - Complex yield expressions: `yield await fetch()` works correctly
        - Yield from: Delegates to another async generator
    
    Related:
        - generators.py: _method_contains_yield() - detects yield in function body
        - scope.py: declare_async_generator_function() - tracks async generators
        - emitter.py: _emit_call() - wraps async generator calls
        - generators.js: wrapAsyncGenerator() - runtime protocol support
    """
    from .functions import _build_params_full
    from .generators import _method_contains_yield
    from .nodes import Yield, YieldFrom
    
    prefix = make_indent(indent)
    emit = _get_emit()
    scope = get_scope()
    
    # ============================================================================
    # ASYNC GENERATOR DETECTION
    # ============================================================================
    # 
    # Check if this async function contains yield/yield from.
    # If yes, it's an async generator and should be emitted as `async function*`.
    # 
    # Detection algorithm:
    # 1. Use _method_contains_yield() from generators.py (reuses proven logic)
    # 2. This recursively searches the function body for Yield/YieldFrom nodes
    # 3. Respects function boundaries (nested functions don't affect detection)
    # 
    # Why separate from regular generators?
    # - Regular generators: `def gen(): yield x` → `function* gen()`
    # - Async generators: `async def gen(): yield x` → `async function* gen()`
    # - Different JavaScript syntax, different runtime wrappers
    # ============================================================================
    
    is_async_generator = _method_contains_yield(node)
    
    # Build function signature
    params_list = _build_params_full(node)
    params_js = ", ".join(params_list) if params_list else ""
    
    # Enter new ISOLATED scope for function body
    scope.enter_function_scope()
    
    # Declare parameters in function scope
    # Phase 33.1: Include positional-only args
    for arg in node.posonly_args:
        scope.declare(safe_js_name(arg))
    for arg in node.args:
        scope.declare(safe_js_name(arg))
    if node.vararg:
        scope.declare(safe_js_name(node.vararg))
    if node.kwarg:
        scope.declare(safe_js_name(node.kwarg))
    for arg in node.kwonly_args:
        scope.declare(safe_js_name(arg))
    
    # Build preamble for *args with **kwargs or keyword-only args handling
    # This extracts kwargs from the args array (same logic as regular functions)
    inner_prefix = make_indent(indent + 1)
    preamble_lines = []
    if node.vararg and (node.kwarg or node.kwonly_args):
        vararg_name = safe_js_name(node.vararg)
        kwarg_name = safe_js_name(node.kwarg) if node.kwarg else "__kwargs__"
        # Extract kwargs from last argument if it's marked as kwargs
        # In JS we can't have params after rest, so kwargs is passed as last positional
        preamble_lines.append(f"{inner_prefix}const {kwarg_name} = ({vararg_name}.length > 0 && {vararg_name}[{vararg_name}.length - 1]?.__kw__) ? {vararg_name}.pop() : {{}};")
    
    # Handle keyword-only args when there's a vararg (they come from kwargs)
    if node.vararg and node.kwonly_args:
        kwarg_name = safe_js_name(node.kwarg) if node.kwarg else "__kwargs__"
        for i, arg in enumerate(node.kwonly_args):
            arg_name = safe_js_name(arg)
            default = node.kwonly_defaults[i] if i < len(node.kwonly_defaults) else None
            if default:
                _emit_expr = _get_emit_expr()
                default_js = _emit_expr(default)
                preamble_lines.append(f"{inner_prefix}const {arg_name} = {kwarg_name}.{arg_name} ?? {default_js};")
            else:
                preamble_lines.append(f"{inner_prefix}const {arg_name} = {kwarg_name}.{arg_name};")
    
    if is_async_generator:
        # Async generator: emit as `async function*`
        # Mark in scope so calls to this function can be wrapped with wrapAsyncGenerator
        scope.declare_async_generator_function(safe_js_name(node.name))
        signature = f"async function* {safe_js_name(node.name)}({params_js})"
    else:
        # Regular async function: emit as `async function`
        signature = f"async function {safe_js_name(node.name)}({params_js})"
    
    # Emit body
    # The body may contain yield expressions (for async generators) or await
    # expressions (for both types). The emitter will handle these correctly.
    body_lines = []
    for stmt in node.body:
        body_lines.append(emit(stmt, indent + 1))
    
    # Combine preamble and body
    all_body = preamble_lines + body_lines
    
    if not all_body:
        all_body.append(f"{prefix}    /* pass */")
    
    body = "\n".join(all_body)
    
    # Exit function scope
    scope.exit_scope()
    
    return f"{prefix}{signature} {{\n{body}\n{prefix}}}"


def _emit_await(node: Await) -> str:
    """
    Emit await expression.
    
    Examples:
        await promise     → await promise
    
    Phase 33.2: Sets await context to prevent generator wrapping of function calls
    inside await expressions (async functions return Promises, not generators).
    """
    from ._internal.scope import get_scope
    
    emit_expr = _get_emit_expr()
    scope = get_scope()
    
    # Enter await context - this prevents generator wrapping in _emit_call
    scope.enter_await_context()
    try:
        value_js = emit_expr(node.value)
    finally:
        # Always exit await context, even if there's an error
        scope.exit_await_context()
    
    return f"await {value_js}"


def _emit_async_for(node: For, indent: int) -> str:
    """
    Emit async for loop.
    
    Examples:
        async for item in gen():    → for await (const item of gen()) {
            await process(item)         await process(item);
                                    }
    """
    prefix = make_indent(indent)
    emit = _get_emit_expr()
    emit_stmt = _get_emit()
    
    target_js = safe_js_name(node.target)
    emit_expr = _get_emit_expr()
    iter_js = emit_expr(node.iter)
    
    # Emit body
    body_lines = []
    for stmt in node.body:
        body_lines.append(emit_stmt(stmt, indent + 1))
    
    if not body_lines:
        body_lines.append(f"{prefix}    /* pass */")
    
    body = "\n".join(body_lines)
    
    # Emit else clause if present
    if node.orelse:
        orelse_lines = []
        for stmt in node.orelse:
            orelse_lines.append(emit_stmt(stmt, indent + 1))
        orelse_body = "\n".join(orelse_lines)
        return f"{prefix}for await (const {target_js} of {iter_js}) {{\n{body}\n{prefix}}} else {{\n{orelse_body}\n{prefix}}}"
    
    return f"{prefix}for await (const {target_js} of {iter_js}) {{\n{body}\n{prefix}}}"

