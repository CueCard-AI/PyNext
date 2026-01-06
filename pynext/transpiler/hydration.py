"""
PyNext Hydration Integration - Generate Hydration-Compatible JavaScript

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This module generates JavaScript code that works with PyNext's hydration
system. The generated code uses the `__pynext__.*` runtime API to:

1. Look up signals/stores/forms by ID at runtime
2. Attach event handlers to server-rendered DOM
3. Enable reactivity after page load

=============================================================================
WHY THIS EXISTS
=============================================================================

PyNext uses server-side rendering (SSR) with client-side hydration:

    Server (Python):
    ┌─────────────────────────────────────────────────────────────────┐
    │  count = signal(0)                                              │
    │  button(onclick=lambda: count.set(count() + 1))["Click"]       │
    │                                                                  │
    │  Renders to:                                                     │
    │  <button data-pynext-click="handler_abc123">Click</button>      │
    │  + hydration data: { signals: { count: 0 }, handlers: {...} }   │
    └─────────────────────────────────────────────────────────────────┘

    Client (JavaScript):
    ┌─────────────────────────────────────────────────────────────────┐
    │  hydrate() reads __PYNEXT_DATA__ and:                          │
    │  1. Creates signals with server values                          │
    │  2. Attaches event handlers to DOM elements                     │
    │  3. Wires up reactive bindings                                  │
    └─────────────────────────────────────────────────────────────────┘

This module generates the handler code that hydrate() will execute.

=============================================================================
HOW IT WORKS
=============================================================================

    Python Handler + ReactiveContext
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  transpile_for_hydration(func, ctx)                            │
    │                                                                  │
    │  1. Get handler source code                                      │
    │  2. Parse to IR nodes                                           │
    │  3. Transform using PyNextTransformer                           │
    │  4. Emit JavaScript                                              │
    │  5. Optionally wrap in function or IIFE                         │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
           │
           ▼
    JavaScript code using __pynext__.getSignal(), etc.

=============================================================================
OUTPUT FORMATS
=============================================================================

1. **Inline Handler** (for simple expressions):
   `__pynext__.getSignal('sig_1').set(true)`

2. **Function Body** (for multi-statement handlers):
   ```javascript
   const form = __pynext__.getForm('form_1');
   if (form.validate()) {
       __pynext__.getSignal('sig_2').update(arr => [...arr, form.values]);
       form.reset();
   }
   ```

3. **Full Function** (for named handlers):
   ```javascript
   function handle_add_issue() {
       const form = __pynext__.getForm('form_1');
       // ...
   }
   ```

=============================================================================
WHO USES THIS
=============================================================================

- pynext/core/html.py: Generates handler code for event attributes
- pynext/transpiler/cli.py: CLI debugging tool
- Tests: Verify hydration output

=============================================================================
"""

from __future__ import annotations

import inspect
import textwrap
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

from .reactive import (
    ReactiveContext,
    ReactiveObjectInfo,
    analyze_handler,
    get_handler_source,
    get_handler_name,
    get_handler_args,
    create_context,
)
from .pynext import (
    PyNextTransformer,
    transpile_handler,
    transpile_handler_source,
    transpile_handler_body,
)
from .errors import TranspileError


# =============================================================================
# HYDRATION OUTPUT OPTIONS
# =============================================================================

@dataclass
class HydrationOptions:
    """
    Options for hydration code generation.
    
    Attributes:
        wrap_in_function: If True, wrap in function definition
        function_name: Name for the wrapper function (or auto-detect)
        include_comments: If True, include source code as comments
        minify: If True, minimize whitespace
        source_map: If True, include source map data
    """
    wrap_in_function: bool = True
    function_name: Optional[str] = None
    include_comments: bool = False
    minify: bool = False
    source_map: bool = False


# =============================================================================
# MAIN TRANSPILATION FUNCTIONS
# =============================================================================

def transpile_for_hydration(
    func: Callable,
    ctx: ReactiveContext = None,
    options: HydrationOptions = None,
) -> str:
    """
    Transpile a Python handler for client-side hydration.
    
    This is the main entry point for generating hydration-compatible
    JavaScript from Python event handlers.
    
    Args:
        func: The Python function to transpile
        ctx: ReactiveContext (auto-detected if not provided)
        options: HydrationOptions for output formatting
    
    Returns:
        JavaScript code string
    
    Raises:
        TranspileError: If transpilation fails
    
    Example:
        def handle_click():
            count.set(count() + 1)
        
        js = transpile_for_hydration(handle_click, ctx)
        # → "function handle_click() {
        #       __pynext__.getSignal('sig_1').set(
        #           __pynext__.getSignal('sig_1').read() + 1
        #       );
        #   }"
    """
    if options is None:
        options = HydrationOptions()
    
    # Auto-detect reactive context
    if ctx is None:
        ctx = analyze_handler(func)
    
    # Get handler metadata
    handler_name = options.function_name or get_handler_name(func)
    handler_args = get_handler_args(func)
    source = get_handler_source(func)
    
    if source is None:
        raise TranspileError(
            message=f"Cannot get source code for {handler_name}",
            source="",
        )
    
    try:
        if options.wrap_in_function:
            # Full function output
            js = transpile_handler(func, ctx)
            
            if options.include_comments and source:
                js = _add_source_comments(js, source, handler_name)
            
            return js
        else:
            # Just the body statements
            js = transpile_handler_body(func, ctx)
            
            if options.include_comments and source:
                js = _add_source_comments(js, source, handler_name)
            
            return js
    
    except Exception as e:
        raise TranspileError(
            message=f"Failed to transpile {handler_name}: {e}",
            source=source,
        )


def transpile_inline_handler(
    func: Callable,
    ctx: ReactiveContext = None,
) -> str:
    """
    Transpile a handler for inline use (no function wrapper).
    
    Use this for simple lambda handlers that can be inlined:
    
        onclick=lambda: count.set(True)
        → onclick="__pynext__.getSignal('sig_1').set(true)"
    
    Args:
        func: The Python function (usually a lambda)
        ctx: ReactiveContext
    
    Returns:
        JavaScript expression or statements (no function wrapper)
    """
    if ctx is None:
        ctx = analyze_handler(func)
    
    return transpile_handler_body(func, ctx)


def transpile_source_for_hydration(
    source: str,
    ctx: ReactiveContext,
    options: HydrationOptions = None,
) -> str:
    """
    Transpile Python source code for hydration.
    
    Use this when you have source code but not the function object.
    
    Args:
        source: Python source code
        ctx: ReactiveContext with name→id mappings
        options: HydrationOptions for output formatting
    
    Returns:
        JavaScript code string
    """
    if options is None:
        options = HydrationOptions()
    
    try:
        js = transpile_handler_source(source, ctx)
        
        if options.include_comments:
            js = _add_source_comments(js, source, "handler")
        
        return js
    
    except Exception as e:
        raise TranspileError(
            message=f"Failed to transpile source: {e}",
            source=source,
        )


# =============================================================================
# COMMENT GENERATION
# =============================================================================

def _add_source_comments(js: str, python_source: str, handler_name: str) -> str:
    """
    Add Python source as comments above the JavaScript.
    
    Example output:
    ```javascript
    // ─────────────────────────────────────────────────────────────────────────────
    // Original Python:
    //
    //   def handle_click():
    //       count.set(count() + 1)
    //
    // ─────────────────────────────────────────────────────────────────────────────
    function handle_click() {
        __pynext__.getSignal('sig_1').set(...);
    }
    ```
    """
    # Clean up source
    source_lines = textwrap.dedent(python_source).strip().split("\n")
    
    # Build comment block
    separator = "// " + "─" * 77
    lines = [
        separator,
        f"// Original Python ({handler_name}):",
        "//",
    ]
    
    for line in source_lines:
        lines.append(f"//   {line}")
    
    lines.extend([
        "//",
        separator,
    ])
    
    return "\n".join(lines) + "\n" + js


# =============================================================================
# BATCH TRANSPILATION
# =============================================================================

@dataclass
class HandlerInfo:
    """Information about a transpiled handler."""
    name: str
    python_source: str
    javascript: str
    reactive_objects: Dict[str, str]  # name → type
    error: Optional[str] = None


def transpile_handlers_batch(
    handlers: Dict[str, Callable],
    ctx: ReactiveContext,
    options: HydrationOptions = None,
) -> Dict[str, HandlerInfo]:
    """
    Transpile multiple handlers in a batch.
    
    Useful for transpiling all handlers in a page at once.
    
    Args:
        handlers: Dict of name → function
        ctx: Shared ReactiveContext
        options: HydrationOptions
    
    Returns:
        Dict of name → HandlerInfo
    """
    if options is None:
        options = HydrationOptions()
    
    results = {}
    
    for name, func in handlers.items():
        try:
            js = transpile_for_hydration(func, ctx, options)
            source = get_handler_source(func) or ""
            
            # Collect reactive objects used
            handler_ctx = analyze_handler(func)
            reactive_objects = {}
            for sig_name in handler_ctx.signals:
                reactive_objects[sig_name] = "signal"
            for store_name in handler_ctx.stores:
                reactive_objects[store_name] = "store"
            for form_name in handler_ctx.forms:
                reactive_objects[form_name] = "form"
            for memo_name in handler_ctx.memos:
                reactive_objects[memo_name] = "memo"
            
            results[name] = HandlerInfo(
                name=name,
                python_source=source,
                javascript=js,
                reactive_objects=reactive_objects,
            )
        
        except Exception as e:
            results[name] = HandlerInfo(
                name=name,
                python_source=get_handler_source(func) or "",
                javascript="",
                reactive_objects={},
                error=str(e),
            )
    
    return results


# =============================================================================
# DEPENDENCY ANALYSIS
# =============================================================================

def get_runtime_dependencies(
    func: Callable,
    ctx: ReactiveContext = None,
) -> Set[str]:
    """
    Get the __py and __pynext__ runtime functions used by a handler.
    
    Useful for dead-code elimination and debugging.
    
    Args:
        func: The Python function
        ctx: ReactiveContext
    
    Returns:
        Set of runtime function names (e.g., {"__pynext__.getSignal", "__py.eq"})
    """
    if ctx is None:
        ctx = analyze_handler(func)
    
    js = transpile_for_hydration(func, ctx)
    
    deps = set()
    
    # Find __pynext__.* calls
    import re
    for match in re.finditer(r'__pynext__\.(\w+)', js):
        deps.add(f"__pynext__.{match.group(1)}")
    
    # Find __py.* calls
    for match in re.finditer(r'__py\.(\w+)', js):
        deps.add(f"__py.{match.group(1)}")
    
    return deps


def get_signal_dependencies(
    func: Callable,
    ctx: ReactiveContext = None,
) -> Set[str]:
    """
    Get the signal IDs that a handler depends on.
    
    Useful for determining which signals a handler reads/writes.
    
    Args:
        func: The Python function
        ctx: ReactiveContext
    
    Returns:
        Set of signal IDs
    """
    if ctx is None:
        ctx = analyze_handler(func)
    
    return set(info.id for info in ctx.signals.values())


# =============================================================================
# UTILITIES
# =============================================================================

def can_transpile(func: Callable) -> bool:
    """
    Check if a function can be transpiled.
    
    Returns False if:
    - Source code cannot be retrieved
    - Function uses unsupported syntax
    
    Args:
        func: The Python function
    
    Returns:
        True if transpilation is likely to succeed
    """
    source = get_handler_source(func)
    if source is None:
        return False
    
    try:
        from . import is_supported
        return is_supported(source)
    except ImportError:
        # Fallback: try parsing
        try:
            import ast
            ast.parse(source)
            return True
        except SyntaxError:
            return False


def get_transpile_error(func: Callable) -> Optional[str]:
    """
    Get the error message if a function cannot be transpiled.
    
    Args:
        func: The Python function
    
    Returns:
        Error message, or None if transpilation would succeed
    """
    source = get_handler_source(func)
    if source is None:
        return "Cannot retrieve source code"
    
    try:
        ctx = analyze_handler(func)
        transpile_for_hydration(func, ctx)
        return None
    except TranspileError as e:
        return str(e)
    except Exception as e:
        return f"Unexpected error: {e}"


# =============================================================================
# DEBUG OUTPUT
# =============================================================================

def generate_debug_output(
    func: Callable,
    ctx: ReactiveContext = None,
) -> str:
    """
    Generate detailed debug output for a handler.
    
    Includes:
    - Original Python source
    - Detected reactive objects
    - Generated JavaScript
    - Runtime dependencies
    
    Args:
        func: The Python function
        ctx: ReactiveContext
    
    Returns:
        Multi-line debug string
    """
    if ctx is None:
        ctx = analyze_handler(func)
    
    name = get_handler_name(func)
    source = get_handler_source(func) or "(source unavailable)"
    
    lines = [
        "═" * 79,
        f"Handler: {name}",
        "═" * 79,
        "",
        "─── Python Source ───",
        "",
        textwrap.indent(textwrap.dedent(source), "    "),
        "",
        "─── Reactive Objects ───",
        "",
    ]
    
    for sig_name, info in ctx.signals.items():
        lines.append(f"    Signal: {sig_name} → {info.id}")
    for store_name, info in ctx.stores.items():
        lines.append(f"    Store: {store_name} → {info.id}")
    for form_name, info in ctx.forms.items():
        lines.append(f"    Form: {form_name} → {info.id}")
    for memo_name, info in ctx.memos.items():
        lines.append(f"    Memo: {memo_name} → {info.id}")
    
    if ctx.is_empty():
        lines.append("    (none detected)")
    
    lines.extend([
        "",
        "─── Generated JavaScript ───",
        "",
    ])
    
    try:
        js = transpile_for_hydration(func, ctx)
        lines.append(textwrap.indent(js, "    "))
    except Exception as e:
        lines.append(f"    ERROR: {e}")
    
    lines.extend([
        "",
        "─── Runtime Dependencies ───",
        "",
    ])
    
    try:
        deps = get_runtime_dependencies(func, ctx)
        for dep in sorted(deps):
            lines.append(f"    {dep}")
        if not deps:
            lines.append("    (none)")
    except Exception:
        lines.append("    (could not determine)")
    
    lines.extend([
        "",
        "═" * 79,
    ])
    
    return "\n".join(lines)
