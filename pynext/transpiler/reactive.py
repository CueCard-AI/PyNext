"""
PyNext Reactive Context Analyzer

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This module analyzes Python event handlers to detect reactive objects
(signals, stores, forms, memos) from their closures. This information is
used by the transpiler to generate correct JavaScript that uses the
`__pynext__.*` API.

=============================================================================
WHY THIS EXISTS
=============================================================================

When transpiling a handler like:

    def handle_click():
        count.set(count() + 1)

We need to know that `count` is a Signal with ID "sig_1" so we can emit:

    function handle_click() {
        __pynext__.getSignal('sig_1').set(
            __pynext__.getSignal('sig_1').read() + 1
        );
    }

The handler function captures `count` in its closure. This module extracts
that closure, identifies reactive objects, and maps variable names to IDs.

=============================================================================
HOW IT WORKS
=============================================================================

    Handler Function (Python)
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  analyze_handler(func)                                          │
    │                                                                  │
    │  1. Get func.__closure__ (captured variables)                   │
    │  2. Get func.__code__.co_freevars (variable names)              │
    │  3. For each (name, cell):                                       │
    │     - Check cell.cell_contents for __pynext_type__              │
    │     - Categorize as signal/store/form/memo                      │
    │     - Extract ID and name for mapping                           │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
           │
           ▼
    ReactiveContext(signals={...}, stores={...}, forms={...}, memos={...})

=============================================================================
WHO USES THIS
=============================================================================

- pynext/transpiler/pynext.py: Uses context to transform IR nodes
- pynext/core/html.py: Calls analyze_handler() before transpilation

=============================================================================
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.reactive.signal import Signal
    from pynext.reactive.store import Store
    from pynext.reactive.forms import FormState
    from pynext.reactive.memo import Memo


# =============================================================================
# REACTIVE OBJECT INFO
# =============================================================================

@dataclass
class ReactiveObjectInfo:
    """
    Information about a single reactive object.
    
    Attributes:
        name: Variable name in Python code (e.g., "count", "all_issues")
        id: Runtime ID for __pynext__.getSignal() lookup
        type: One of "signal", "store", "form", "memo"
        obj: The actual reactive object (for inspection)
    """
    name: str
    id: str
    type: str
    obj: Any


# =============================================================================
# REACTIVE CONTEXT
# =============================================================================

@dataclass
class ReactiveContext:
    """
    Collected reactive objects from a handler's closure.
    
    This is the main output of analyze_handler(). It contains all reactive
    objects the handler depends on, organized by type.
    
    Example:
        ctx = analyze_handler(handle_add_issue)
        
        ctx.signals = {
            "all_issues": ReactiveObjectInfo(name="all_issues", id="sig_1", ...),
            "show_add_form": ReactiveObjectInfo(name="show_add_form", id="sig_2", ...),
        }
        ctx.forms = {
            "issue_form": ReactiveObjectInfo(name="issue_form", id="form_1", ...),
        }
        ctx.constants = {
            "STATUS_LABELS": {"backlog": "Backlog", "todo": "Todo", ...},
        }
    """
    
    # Signals: signal(value) - simple reactive values
    signals: Dict[str, ReactiveObjectInfo] = field(default_factory=dict)
    
    # Stores: store(obj) - deeply reactive objects
    stores: Dict[str, ReactiveObjectInfo] = field(default_factory=dict)
    
    # Forms: create_form(...) - form state with validation
    forms: Dict[str, ReactiveObjectInfo] = field(default_factory=dict)
    
    # Memos: memo(fn) - computed/derived values
    memos: Dict[str, ReactiveObjectInfo] = field(default_factory=dict)
    
    # Constants: serializable Python constants (dicts, lists, primitives) that
    # need to be available client-side for transpiled code to work correctly.
    constants: Dict[str, Any] = field(default_factory=dict)
    
    def is_empty(self) -> bool:
        """Check if no reactive objects or constants were found."""
        return not (self.signals or self.stores or self.forms or self.memos or self.constants)
    
    def get_all(self) -> Dict[str, ReactiveObjectInfo]:
        """Get all reactive objects as a single dict."""
        result = {}
        result.update(self.signals)
        result.update(self.stores)
        result.update(self.forms)
        result.update(self.memos)
        return result
    
    def get_by_name(self, name: str) -> Optional[ReactiveObjectInfo]:
        """Look up a reactive object by its variable name."""
        for collection in [self.signals, self.stores, self.forms, self.memos]:
            if name in collection:
                return collection[name]
        return None
    
    def get_signal_id(self, name: str) -> Optional[str]:
        """Get the runtime ID for a signal by name."""
        if name in self.signals:
            return self.signals[name].id
        return None
    
    def get_store_id(self, name: str) -> Optional[str]:
        """Get the runtime ID for a store by name."""
        if name in self.stores:
            return self.stores[name].id
        return None
    
    def get_form_id(self, name: str) -> Optional[str]:
        """Get the runtime ID for a form by name."""
        if name in self.forms:
            return self.forms[name].id
        return None
    
    def get_memo_id(self, name: str) -> Optional[str]:
        """Get the runtime ID for a memo by name."""
        if name in self.memos:
            return self.memos[name].id
        return None


# =============================================================================
# TYPE DETECTION HELPERS
# =============================================================================

def _is_serializable_constant(value: Any) -> bool:
    """
    Check if a value can be JSON-serialized for client-side use.
    
    This is used to identify Python constants (dicts, lists, primitives) that
    are referenced in transpiled code and need to be available in JavaScript.
    
    Examples of serializable constants:
        - STATUS_LABELS = {"backlog": "Backlog", "todo": "Todo"}
        - PRIORITY_LEVELS = ["low", "medium", "high"]
        - MAX_RETRIES = 3
    
    Examples of non-serializable values:
        - Functions/lambdas
        - Classes
        - Modules
        - Objects with custom types
    
    Args:
        value: The Python value to check
        
    Returns:
        True if the value can be safely serialized to JSON
    """
    if isinstance(value, (str, int, float, bool, type(None))):
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_serializable_constant(v) for v in value)
    if isinstance(value, dict):
        return all(
            isinstance(k, str) and _is_serializable_constant(v) 
            for k, v in value.items()
        )
    return False


def _get_pynext_type(obj: Any) -> Optional[str]:
    """
    Get the PyNext type of an object.
    
    Returns one of: "signal", "store", "form", "memo", "effect", or None.
    """
    return getattr(obj, "__pynext_type__", None)


def _is_signal(obj: Any) -> bool:
    """Check if object is a Signal."""
    return _get_pynext_type(obj) == "signal"


def _is_store(obj: Any) -> bool:
    """Check if object is a Store."""
    return _get_pynext_type(obj) == "store"


def _is_form(obj: Any) -> bool:
    """Check if object is a FormState."""
    return _get_pynext_type(obj) == "form"


def _is_memo(obj: Any) -> bool:
    """Check if object is a Memo."""
    return _get_pynext_type(obj) == "memo"


def _get_object_id(obj: Any) -> str:
    """
    Get the runtime ID of a reactive object.
    
    Different types store their ID in different attributes:
    - Signal: _id
    - Store: _id, _store_id
    - Form: _form_id, _id
    - Memo: _id
    
    CRITICAL FIX: Forms use _form_id, not just _id. We must check for it!
    """
    # Try common ID attribute names - order matters!
    # Check _form_id first for forms, then the generic _id
    for attr in ("_form_id", "_id", "id", "_store_id"):
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            if isinstance(value, str):
                return value
    
    # Fallback: generate from object ID
    return f"reactive_{id(obj)}"


def _get_object_name(obj: Any) -> Optional[str]:
    """Get the human-readable name of a reactive object (if set)."""
    return getattr(obj, "_name", None)


# =============================================================================
# CLOSURE EXTRACTION
# =============================================================================

def _extract_closure_vars(func: Callable) -> Dict[str, Any]:
    """
    Extract captured variables from a function's closure.
    
    Python closures store captured variables in:
    - func.__closure__: tuple of cell objects
    - func.__code__.co_freevars: tuple of variable names
    
    Returns:
        Dict mapping variable names to their values
    
    Example:
        count = signal(0)
        def handler():
            count.set(1)
        
        _extract_closure_vars(handler)
        # → {"count": <Signal object>}
    """
    closure_cells = getattr(func, "__closure__", None) or ()
    free_vars = getattr(func, "__code__", None)
    
    if free_vars is None:
        return {}
    
    free_var_names = free_vars.co_freevars
    
    if len(closure_cells) != len(free_var_names):
        return {}
    
    result = {}
    for name, cell in zip(free_var_names, closure_cells):
        try:
            value = cell.cell_contents
            result[name] = value
            
            # CRITICAL FIX: For nested closures, if the cell contains
            # a function, recursively extract ITS closure too.
            # This handles patterns like:
            #
            #   def outer():
            #       count = signal(0)
            #       def inner():
            #           count.set(1)  # count is in outer's closure
            #       return inner
            #
            if callable(value) and hasattr(value, "__closure__"):
                nested = _extract_closure_vars(value)
                # Don't override direct captures with nested ones
                for k, v in nested.items():
                    if k not in result:
                        result[k] = v
        except ValueError:
            # Cell is empty (variable deleted)
            pass
    
    return result


def _extract_nested_closure_vars(func: Callable, max_depth: int = 5) -> Dict[str, Any]:
    """
    Extract variables from nested closures up to a maximum depth.
    
    This handles deeply nested function patterns where reactive objects
    might be captured multiple levels up.
    
    Args:
        func: The function to analyze
        max_depth: Maximum nesting depth to traverse
    
    Returns:
        Dict mapping variable names to their values
    """
    result = {}
    visited = set()
    
    def extract_recursive(f: Callable, depth: int):
        if depth > max_depth:
            return
        
        func_id = id(f)
        if func_id in visited:
            return
        visited.add(func_id)
        
        closure_cells = getattr(f, "__closure__", None) or ()
        code = getattr(f, "__code__", None)
        
        if code is None:
            return
        
        free_var_names = code.co_freevars
        
        if len(closure_cells) != len(free_var_names):
            return
        
        for name, cell in zip(free_var_names, closure_cells):
            try:
                value = cell.cell_contents
                if name not in result:
                    result[name] = value
                
                # Recurse into callable values
                if callable(value) and hasattr(value, "__closure__"):
                    extract_recursive(value, depth + 1)
            except ValueError:
                pass
    
    extract_recursive(func, 0)
    return result


def _extract_globals(func: Callable) -> Dict[str, Any]:
    """
    Extract global variables referenced by a function.
    
    This catches cases where reactive objects are module-level globals
    rather than closures.
    """
    if not hasattr(func, "__globals__"):
        return {}
    
    # Get the global names referenced by the function
    code = getattr(func, "__code__", None)
    if code is None:
        return {}
    
    global_names = code.co_names
    func_globals = func.__globals__
    
    result = {}
    for name in global_names:
        if name in func_globals:
            result[name] = func_globals[name]
    
    return result


# =============================================================================
# MAIN ANALYZER
# =============================================================================

def analyze_handler(func: Callable) -> ReactiveContext:
    """
    Analyze a Python event handler to extract reactive objects.
    
    This is the main entry point for reactive analysis. It examines the
    function's closure and globals to find all signals, stores, forms,
    and memos that the handler depends on.
    
    CRITICAL: Also extracts form field signals (form.field is a Signal).
    
    Args:
        func: The Python function to analyze
        
    Returns:
        ReactiveContext with all found reactive objects
        
    Example:
        def handle_click():
            count.set(count() + 1)
            
        ctx = analyze_handler(handle_click)
        assert "count" in ctx.signals
        assert ctx.signals["count"].id == "sig_1"
    """
    ctx = ReactiveContext()
    
    # Extract from closure (captured variables) - now handles nested closures
    closure_vars = _extract_closure_vars(func)
    
    # Also check globals (module-level reactive objects)
    global_vars = _extract_globals(func)
    
    # Combine, preferring closure over globals
    all_vars = {**global_vars, **closure_vars}
    
    # Skip these built-in names when detecting constants
    BUILTIN_NAMES = frozenset({
        '__builtins__', '__name__', '__doc__', '__file__', 
        '__package__', '__spec__', '__loader__', '__cached__',
        '__annotations__', '__dict__', '__module__', '__qualname__',
    })
    
    # Categorize each variable
    for name, obj in all_vars.items():
        if obj is None:
            continue
        
        pynext_type = _get_pynext_type(obj)
        
        if pynext_type is not None:
            # This is a reactive object (signal, store, form, memo)
            obj_id = _get_object_id(obj)
            # CRITICAL FIX: Use the signal's registered name (obj_name), not the variable name
            # This fixes the issue where `expanded` Signal with name="issue_1_expanded"
            # was being looked up as "expanded" instead of "issue_1_expanded"
            obj_name = _get_object_name(obj) or name
            
            info = ReactiveObjectInfo(
                name=obj_name,  # Use the signal's registered name for correct client-side lookup
                id=obj_id,
                type=pynext_type,
                obj=obj,
            )
            
            if pynext_type == "signal":
                ctx.signals[name] = info
            elif pynext_type == "store":
                ctx.stores[name] = info
            elif pynext_type == "form":
                ctx.forms[name] = info
                # CRITICAL FIX: Extract form field signals
                # Form fields like form.email, form.password are themselves signals
                _extract_form_field_signals(obj, name, ctx)
            elif pynext_type == "memo":
                ctx.memos[name] = info
        elif name not in BUILTIN_NAMES and _is_serializable_constant(obj):
            # This is a serializable constant (dict, list, primitive)
            # Track it so it can be injected into the client-side scope
            ctx.constants[name] = obj
    
    return ctx


def _extract_form_field_signals(form_obj: Any, form_name: str, ctx: ReactiveContext):
    """
    Extract field signals from a form object.
    
    Form fields are signals themselves: form.email() reads the email signal,
    form.email.set("x") sets it. We need to track these for proper transformation.
    
    Args:
        form_obj: The FormState object
        form_name: The variable name of the form (e.g., "login_form")
        ctx: ReactiveContext to update
    """
    # Try to get form fields - forms expose them as attributes
    if not hasattr(form_obj, "_fields"):
        return
    
    try:
        fields = form_obj._fields
        if not isinstance(fields, dict):
            return
        
        for field_name, field_obj in fields.items():
            # Each field should be a Signal
            field_type = _get_pynext_type(field_obj)
            if field_type == "signal":
                field_id = _get_object_id(field_obj)
                
                # Store as "form_name.field_name" for lookup
                qualified_name = f"{form_name}.{field_name}"
                
                info = ReactiveObjectInfo(
                    name=qualified_name,
                    id=field_id,
                    type="signal",
                    obj=field_obj,
                )
                ctx.signals[qualified_name] = info
    except Exception:
        # If we can't access fields, silently continue
        pass


def analyze_function_source(source: str, context_vars: Dict[str, Any] = None) -> ReactiveContext:
    """
    Analyze Python source code with provided context variables.
    
    This is useful for testing or when you have source code but not
    the actual function object.
    
    Args:
        source: Python source code of the function
        context_vars: Dict of variables to use as context
                     (simulating closure capture)
    
    Returns:
        ReactiveContext built from context_vars
    """
    ctx = ReactiveContext()
    
    if context_vars is None:
        return ctx
    
    for name, obj in context_vars.items():
        if obj is None:
            continue
        
        pynext_type = _get_pynext_type(obj)
        
        if pynext_type is None:
            continue
        
        obj_id = _get_object_id(obj)
        
        info = ReactiveObjectInfo(
            name=name,
            id=obj_id,
            type=pynext_type,
            obj=obj,
        )
        
        if pynext_type == "signal":
            ctx.signals[name] = info
        elif pynext_type == "store":
            ctx.stores[name] = info
        elif pynext_type == "form":
            ctx.forms[name] = info
        elif pynext_type == "memo":
            ctx.memos[name] = info
    
    return ctx


# =============================================================================
# CONTEXT FROM EXPLICIT MAPPINGS
# =============================================================================

def create_context(
    signals: Dict[str, str] = None,
    stores: Dict[str, str] = None,
    forms: Dict[str, str] = None,
    memos: Dict[str, str] = None,
) -> ReactiveContext:
    """
    Create a ReactiveContext from explicit name→id mappings.
    
    This is useful for testing or when you know the IDs ahead of time.
    
    Args:
        signals: Dict of signal name → signal ID
        stores: Dict of store name → store ID
        forms: Dict of form name → form ID
        memos: Dict of memo name → memo ID
    
    Returns:
        ReactiveContext with the specified mappings
    
    Example:
        ctx = create_context(
            signals={"count": "sig_1", "name": "sig_2"},
            forms={"login_form": "form_1"},
        )
    """
    ctx = ReactiveContext()
    
    if signals:
        for name, id_ in signals.items():
            ctx.signals[name] = ReactiveObjectInfo(
                name=name,
                id=id_,
                type="signal",
                obj=None,
            )
    
    if stores:
        for name, id_ in stores.items():
            ctx.stores[name] = ReactiveObjectInfo(
                name=name,
                id=id_,
                type="store",
                obj=None,
            )
    
    if forms:
        for name, id_ in forms.items():
            ctx.forms[name] = ReactiveObjectInfo(
                name=name,
                id=id_,
                type="form",
                obj=None,
            )
    
    if memos:
        for name, id_ in memos.items():
            ctx.memos[name] = ReactiveObjectInfo(
                name=name,
                id=id_,
                type="memo",
                obj=None,
            )
    
    return ctx


# =============================================================================
# UTILITIES
# =============================================================================

def get_handler_source(func: Callable) -> Optional[str]:
    """
    Get the source code of a handler function.
    
    Returns None if source cannot be retrieved (e.g., built-in functions).
    
    CRITICAL FIX: Handles lambda functions specially since inspect.getsource()
    often fails for inline lambdas.
    
    CRITICAL FIX #2: Uses textwrap.dedent() to strip leading indentation.
    When a handler is defined inside a class method or nested function,
    inspect.getsource() returns the code with its original indentation,
    which causes parsing errors like "unexpected indent". Dedenting fixes this.
    
    CRITICAL FIX #3: Strips trailing comma from lambda sources.
    When a lambda is defined as an argument in a function call:
        memo(lambda: [...], name="foo")
    inspect.getsource() returns "lambda: [...],\n" with the trailing comma.
    This makes Python parse it as a tuple, breaking transpilation.
    """
    import textwrap
    import re
    
    try:
        # CRITICAL FIX: Clear linecache to avoid stale source when file was modified
        # This fixes issues where Python's linecache returns old source after file edits
        import linecache
        if hasattr(func, '__code__') and hasattr(func.__code__, 'co_filename'):
            linecache.checkcache(func.__code__.co_filename)
        
        source = inspect.getsource(func)
        # Dedent the source to remove leading whitespace
        # This fixes the "unexpected indent" error when parsing handlers
        # that are defined inside methods/functions
        source = textwrap.dedent(source)
        
        # CRITICAL FIX #3: For lambdas, strip trailing comma that comes from
        # being an argument in a function call like: memo(lambda: x, name="y")
        if func.__name__ == "<lambda>":
            # Remove trailing comma and whitespace after the lambda body
            source = source.rstrip()
            if source.endswith(','):
                source = source[:-1]
        
        return source
    except (OSError, TypeError):
        pass
    
    # Fallback for lambdas: try to extract from bytecode if possible
    # This handles cases like: onclick=lambda: count.set(True)
    if hasattr(func, "__name__") and func.__name__ == "<lambda>":
        return _extract_lambda_source(func)
    
    return None


def _extract_lambda_source(func: Callable) -> Optional[str]:
    """
    Extract source code from a lambda function.
    
    This is a fallback when inspect.getsource() fails for inline lambdas.
    We attempt to reconstruct the lambda from bytecode analysis.
    
    Args:
        func: The lambda function
    
    Returns:
        Source code string, or None if extraction fails
    """
    import dis
    
    try:
        code = func.__code__
        
        # Get bytecode instructions
        instructions = list(dis.get_instructions(code))
        
        # Simple heuristic: reconstruct from closure vars and code info
        closure_vars = _extract_closure_vars(func)
        arg_names = code.co_varnames[:code.co_argcount]
        
        # Build a placeholder lambda that calls the reactive methods
        if not closure_vars and not arg_names:
            # No-arg lambda with no closure - likely a simple expression
            # We can't reliably extract, so return None
            return None
        
        # For lambdas with reactive objects, create a synthetic source
        # that captures the most common patterns
        args = ", ".join(arg_names) if arg_names else ""
        
        # Check if it's a simple signal call pattern
        for name, obj in closure_vars.items():
            pynext_type = _get_pynext_type(obj)
            if pynext_type == "signal":
                # Common pattern: lambda: signal.set(value)
                # We generate a placeholder that the transpiler can handle
                return f"lambda {args}: {name}.set(True) if {name}() else {name}.set(False)"
        
        # If we can't determine the pattern, return a generic placeholder
        # that at least parses correctly
        return None
        
    except Exception:
        return None


def get_lambda_body_from_bytecode(func: Callable) -> Optional[str]:
    """
    Attempt to extract just the body expression of a lambda from its bytecode.
    
    This is a best-effort approach for inline lambdas where source is unavailable.
    It handles common reactive patterns:
    
    - lambda: signal.set(True)
    - lambda: signal.set(signal() + 1)
    - lambda e: form.field.set(e.target.value)
    
    Returns None if the pattern cannot be determined.
    """
    import dis
    import types
    
    try:
        code = func.__code__
        instructions = list(dis.get_instructions(code))
        
        # Analyze the bytecode to determine the pattern
        parts = []
        stack = []
        
        for instr in instructions:
            if instr.opname == "LOAD_DEREF":
                # Loading a closure variable
                stack.append(instr.argval)
            elif instr.opname == "LOAD_ATTR":
                if stack:
                    base = stack.pop()
                    stack.append(f"{base}.{instr.argval}")
            elif instr.opname == "LOAD_CONST":
                stack.append(repr(instr.argval))
            elif instr.opname == "CALL":
                # Method call - reconstruct
                if stack:
                    method = stack.pop()
                    parts.append(f"{method}()")
        
        if parts:
            return " ".join(parts)
        
        return None
        
    except Exception:
        return None


def get_handler_name(func: Callable) -> str:
    """Get the name of a handler function."""
    return getattr(func, "__name__", "anonymous")


def get_handler_args(func: Callable) -> list[str]:
    """Get the argument names of a handler function."""
    try:
        sig = inspect.signature(func)
        return list(sig.parameters.keys())
    except (ValueError, TypeError):
        return []
