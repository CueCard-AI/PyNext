"""
SolidJS-inspired reactive primitives for PyNext.

Provides Signal, Effect, Memo, and Store for fine-grained reactivity.
These primitives serialize to hydration markers for client-side activation.
"""

from __future__ import annotations

import uuid
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional, TypeVar, Union
from functools import wraps

from pynext.core.context import get_context


T = TypeVar("T")
U = TypeVar("U")


# Batching support
_batching = False
_batch_queue: list[Callable[[], None]] = []


def batch(fn: Callable[[], None]) -> None:
    """
    Batch multiple signal updates to prevent intermediate re-renders.
    
    Usage:
        batch(lambda: (
            count.set(count() + 1),
            name.set("updated")
        ))
    """
    global _batching, _batch_queue
    
    if _batching:
        fn()
        return
    
    _batching = True
    _batch_queue = []
    
    try:
        fn()
        # Execute all queued effects
        for effect_fn in _batch_queue:
            effect_fn()
    finally:
        _batching = False
        _batch_queue = []


class Signal(Generic[T]):
    """
    A reactive primitive that holds a value and notifies subscribers on change.
    
    Usage:
        count = Signal(0)
        current = count()      # Read
        count.set(5)           # Write
        count.update(lambda x: x + 1)  # Update based on current value
    """
    
    _is_signal = True
    
    def __init__(self, initial_value: T, name: Optional[str] = None):
        self._value: T = initial_value
        self._id: str = f"sig_{uuid.uuid4().hex[:8]}"
        self._name: str = name or self._id
        self._subscribers: list[Callable[[T], None]] = []
        self._attribute_bindings: list[tuple[str, str]] = []  # (element_id, attr_name)
        
        # Register with current render context if available
        ctx = get_context()
        if ctx:
            # Will be registered when rendered
            pass
    
    def __call__(self) -> T:
        """Read the current value."""
        return self._value
    
    def set(self, value: T) -> None:
        """Set a new value and notify subscribers."""
        if self._value != value:
            self._value = value
            self._notify()
    
    def update(self, fn: Callable[[T], T]) -> None:
        """Update the value using a function."""
        self.set(fn(self._value))
    
    def subscribe(self, fn: Callable[[T], None]) -> Callable[[], None]:
        """
        Subscribe to value changes.
        
        Returns an unsubscribe function.
        """
        self._subscribers.append(fn)
        return lambda: self._subscribers.remove(fn)
    
    def _notify(self) -> None:
        """Notify all subscribers of a value change."""
        global _batching, _batch_queue
        
        for subscriber in self._subscribers:
            if _batching:
                _batch_queue.append(lambda s=subscriber: s(self._value))
            else:
                subscriber(self._value)
    
    def _bind_to_attribute(self, element_id: str, attr_name: str) -> None:
        """Bind this signal to an element attribute for reactive updates."""
        self._attribute_bindings.append((element_id, attr_name))
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        value_json = json.dumps(self._value)
        return f"__pynext__.createSignal('{self._id}', {value_json})"
    
    def __str__(self) -> str:
        """Return string representation of current value."""
        return str(self._value)
    
    def __repr__(self) -> str:
        return f"Signal({self._value!r}, id={self._id!r})"


class Computed(Generic[T]):
    """
    A derived value that automatically updates when dependencies change.
    
    Alias for Memo - use whichever name feels more natural.
    
    Usage:
        count = Signal(5)
        doubled = Computed(lambda: count() * 2)
    """
    
    _is_signal = True
    
    def __init__(self, fn: Callable[[], T], name: Optional[str] = None):
        self._fn = fn
        self._id: str = f"comp_{uuid.uuid4().hex[:8]}"
        self._name: str = name or self._id
        self._value: Optional[T] = None
        self._dependencies: set[str] = set()
        self._dirty = True
        
    def __call__(self) -> T:
        """Get the computed value, recalculating if needed."""
        if self._dirty:
            self._value = self._fn()
            self._dirty = False
        return self._value  # type: ignore
    
    def invalidate(self) -> None:
        """Mark as dirty to force recalculation."""
        self._dirty = True
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        # For computed values, we need to serialize the computation
        # This is a simplified version - real implementation would need AST analysis
        deps = list(self._dependencies)
        return f"__pynext__.createMemo('{self._id}', {json.dumps(deps)})"
    
    def __str__(self) -> str:
        return str(self())
    
    def __repr__(self) -> str:
        return f"Computed(id={self._id!r})"


# Alias for consistency with SolidJS naming
Memo = Computed


class Effect:
    """
    A side effect that runs when its dependencies change.
    
    Usage:
        count = Signal(0)
        
        @Effect
        def log_count():
            print(f"Count is now: {count()}")
    """
    
    def __init__(
        self, 
        fn: Optional[Callable[[], Optional[Callable[[], None]]]] = None,
        *,
        js_code: Optional[str] = None,
    ):
        self._fn = fn
        self._id: str = f"eff_{uuid.uuid4().hex[:8]}"
        self._dependencies: set[str] = set()
        self._cleanup: Optional[Callable[[], None]] = None
        self._js_code = js_code
        
        # If function provided, run it immediately
        if fn:
            self._run()
            
            # Register with context
            ctx = get_context()
            if ctx:
                ctx.register_effect(self)
    
    def __call__(self, fn: Callable[[], Optional[Callable[[], None]]]) -> "Effect":
        """Allow use as a decorator."""
        self._fn = fn
        self._run()
        
        ctx = get_context()
        if ctx:
            ctx.register_effect(self)
            
        return self
    
    def _run(self) -> None:
        """Execute the effect function."""
        if self._cleanup:
            self._cleanup()
            self._cleanup = None
        
        if self._fn:
            result = self._fn()
            if callable(result):
                self._cleanup = result
    
    def dispose(self) -> None:
        """Clean up the effect."""
        if self._cleanup:
            self._cleanup()
            self._cleanup = None
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        deps = list(self._dependencies)
        code = self._js_code or ""
        return f"__pynext__.createEffect('{self._id}', {json.dumps(deps)}, {json.dumps(code)})"


class Store(Generic[T]):
    """
    A reactive store for complex nested state.
    
    Usage:
        user = Store({
            "name": "John",
            "age": 30,
            "address": {"city": "NYC"}
        })
        
        # Read
        user.name  # "John"
        user["address"]["city"]  # "NYC"
        
        # Write
        user.name = "Jane"
        user.update({"age": 31})
    """
    
    _is_signal = True
    
    def __init__(self, initial_value: T, name: Optional[str] = None):
        object.__setattr__(self, "_data", initial_value)
        object.__setattr__(self, "_id", f"store_{uuid.uuid4().hex[:8]}")
        object.__setattr__(self, "_name", name or object.__getattribute__(self, "_id"))
        object.__setattr__(self, "_subscribers", [])
        object.__setattr__(self, "_path", [])
        
        # Register with context
        ctx = get_context()
        if ctx:
            ctx.stores[self._id] = initial_value
    
    def __call__(self) -> T:
        """Get the entire store value."""
        return object.__getattribute__(self, "_data")
    
    def __getattr__(self, name: str) -> Any:
        """Access store properties."""
        data = object.__getattribute__(self, "_data")
        if isinstance(data, dict) and name in data:
            value = data[name]
            if isinstance(value, dict):
                # Return a proxy for nested access
                return _StoreProxy(self, [name], value)
            return value
        raise AttributeError(f"Store has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Set store properties."""
        data = object.__getattribute__(self, "_data")
        if isinstance(data, dict):
            data[name] = value
            self._notify([name])
        else:
            object.__setattr__(self, name, value)
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access."""
        data = object.__getattribute__(self, "_data")
        if isinstance(data, dict):
            value = data[key]
            if isinstance(value, dict):
                return _StoreProxy(self, [key], value)
            return value
        raise KeyError(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Dictionary-style assignment."""
        data = object.__getattribute__(self, "_data")
        if isinstance(data, dict):
            data[key] = value
            self._notify([key])
        else:
            raise TypeError("Store does not support item assignment")
    
    def update(self, updates: dict) -> None:
        """Update multiple properties at once."""
        data = object.__getattribute__(self, "_data")
        if isinstance(data, dict):
            data.update(updates)
            self._notify(list(updates.keys()))
    
    def subscribe(self, fn: Callable[[T], None]) -> Callable[[], None]:
        """Subscribe to store changes."""
        subscribers = object.__getattribute__(self, "_subscribers")
        subscribers.append(fn)
        return lambda: subscribers.remove(fn)
    
    def _notify(self, paths: list[str]) -> None:
        """Notify subscribers of changes."""
        data = object.__getattribute__(self, "_data")
        subscribers = object.__getattribute__(self, "_subscribers")
        for subscriber in subscribers:
            subscriber(data)
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        data = object.__getattribute__(self, "_data")
        store_id = object.__getattribute__(self, "_id")
        return f"__pynext__.createStore('{store_id}', {json.dumps(data)})"
    
    def __str__(self) -> str:
        data = object.__getattribute__(self, "_data")
        return str(data)
    
    def __repr__(self) -> str:
        store_id = object.__getattribute__(self, "_id")
        data = object.__getattribute__(self, "_data")
        return f"Store({data!r}, id={store_id!r})"


class _StoreProxy:
    """Proxy for nested store access."""
    
    def __init__(self, store: Store, path: list[str], data: dict):
        object.__setattr__(self, "_store", store)
        object.__setattr__(self, "_path", path)
        object.__setattr__(self, "_data", data)
    
    def __getattr__(self, name: str) -> Any:
        data = object.__getattribute__(self, "_data")
        if name in data:
            value = data[name]
            if isinstance(value, dict):
                path = object.__getattribute__(self, "_path")
                store = object.__getattribute__(self, "_store")
                return _StoreProxy(store, path + [name], value)
            return value
        raise AttributeError(f"Store path has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        data = object.__getattribute__(self, "_data")
        if isinstance(data, dict):
            data[name] = value
            store = object.__getattribute__(self, "_store")
            path = object.__getattribute__(self, "_path")
            store._notify(path + [name])
    
    def __getitem__(self, key: str) -> Any:
        data = object.__getattribute__(self, "_data")
        value = data[key]
        if isinstance(value, dict):
            path = object.__getattribute__(self, "_path")
            store = object.__getattribute__(self, "_store")
            return _StoreProxy(store, path + [key], value)
        return value
    
    def __setitem__(self, key: str, value: Any) -> None:
        data = object.__getattribute__(self, "_data")
        data[key] = value
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        store._notify(path + [key])
    
    def __str__(self) -> str:
        return str(object.__getattribute__(self, "_data"))


# Convenience function for creating signals with type inference
def signal(value: T, name: Optional[str] = None) -> Signal[T]:
    """Create a new Signal with the given initial value."""
    return Signal(value, name)


def computed(fn: Callable[[], T], name: Optional[str] = None) -> Computed[T]:
    """Create a new Computed/Memo with the given function."""
    return Computed(fn, name)


def effect(fn: Callable[[], Optional[Callable[[], None]]]) -> Effect:
    """Create a new Effect with the given function."""
    return Effect(fn)


def store(value: T, name: Optional[str] = None) -> Store[T]:
    """Create a new Store with the given initial value."""
    return Store(value, name)


# =============================================================================
# Event Handler Transpilation
# =============================================================================

def transpile_handler(handler: Callable) -> str:
    """
    Transpile a Python event handler to JavaScript.
    
    Supports:
    - Signal reads: signal()
    - Signal writes: signal.set(value), signal.update(fn)
    - Server action calls: action(args)
    - Navigation: navigate(url)
    - Simple lambdas with basic operations
    
    Usage:
        count = Signal(0)
        
        # This Python handler:
        onclick = lambda: count.update(lambda x: x + 1)
        
        # Transpiles to:
        # () => __pynext__.getSignal('sig_xxx').update(x => x + 1)
    """
    import inspect
    import ast as ast_module
    
    # Get source code if possible
    try:
        source = inspect.getsource(handler)
    except (OSError, TypeError):
        # Can't get source, try to analyze the closure
        return _transpile_from_closure(handler)
    
    # Parse and transpile
    try:
        tree = ast_module.parse(source.strip())
        return _transpile_ast(tree)
    except SyntaxError:
        return _transpile_from_closure(handler)


def _transpile_from_closure(handler: Callable) -> str:
    """
    Transpile a handler by analyzing its closure variables.
    
    This handles cases where we can't get source code.
    """
    # Check for common patterns
    closure = handler.__closure__ or ()
    
    # Look for signals in closure
    signals = []
    for cell in closure:
        try:
            value = cell.cell_contents
            if hasattr(value, '_is_signal') and value._is_signal:
                signals.append(value)
        except ValueError:
            continue
    
    if len(signals) == 1:
        signal = signals[0]
        # Common pattern: toggle or increment
        return f"() => __pynext__.getSignal('{signal._id}').update(x => !x)"
    
    # Fallback: can't transpile
    return ""


def _transpile_ast(tree) -> str:
    """Transpile an AST to JavaScript."""
    import ast
    
    class JSTranspiler(ast.NodeVisitor):
        def __init__(self):
            self.signal_map = {}
        
        def visit_Lambda(self, node: ast.Lambda) -> str:
            args = ", ".join(arg.arg for arg in node.args.args)
            body = self.visit(node.body)
            return f"({args}) => {body}"
        
        def visit_Call(self, node: ast.Call) -> str:
            func = self.visit(node.func)
            args = ", ".join(self.visit(arg) for arg in node.args)
            
            # Check for signal operations
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "set":
                    obj = self.visit(node.func.value)
                    return f"{obj}.write({args})"
                elif node.func.attr == "update":
                    obj = self.visit(node.func.value)
                    return f"{obj}.update({args})"
            
            # Check for navigate
            if isinstance(node.func, ast.Name) and node.func.id == "navigate":
                return f"__pynext__.navigate({args})"
            
            return f"{func}({args})"
        
        def visit_Attribute(self, node: ast.Attribute) -> str:
            value = self.visit(node.value)
            return f"{value}.{node.attr}"
        
        def visit_Name(self, node: ast.Name) -> str:
            name = node.id
            # Check if it's a known signal
            if name in self.signal_map:
                signal_id = self.signal_map[name]
                return f"__pynext__.getSignal('{signal_id}')"
            return name
        
        def visit_BinOp(self, node: ast.BinOp) -> str:
            left = self.visit(node.left)
            right = self.visit(node.right)
            op = self._get_binop(node.op)
            return f"({left} {op} {right})"
        
        def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
            operand = self.visit(node.operand)
            op = self._get_unaryop(node.op)
            return f"{op}{operand}"
        
        def visit_Compare(self, node: ast.Compare) -> str:
            left = self.visit(node.left)
            parts = [left]
            for op, comp in zip(node.ops, node.comparators):
                parts.append(self._get_cmpop(op))
                parts.append(self.visit(comp))
            return " ".join(parts)
        
        def visit_IfExp(self, node: ast.IfExp) -> str:
            test = self.visit(node.test)
            body = self.visit(node.body)
            orelse = self.visit(node.orelse)
            return f"({test} ? {body} : {orelse})"
        
        def visit_Constant(self, node: ast.Constant) -> str:
            if isinstance(node.value, str):
                return json.dumps(node.value)
            elif isinstance(node.value, bool):
                return "true" if node.value else "false"
            elif node.value is None:
                return "null"
            return str(node.value)
        
        def visit_List(self, node: ast.List) -> str:
            items = ", ".join(self.visit(elt) for elt in node.elts)
            return f"[{items}]"
        
        def visit_Dict(self, node: ast.Dict) -> str:
            pairs = []
            for k, v in zip(node.keys, node.values):
                key = self.visit(k)
                val = self.visit(v)
                pairs.append(f"{key}: {val}")
            return f"{{{', '.join(pairs)}}}"
        
        def _get_binop(self, op: ast.operator) -> str:
            ops = {
                ast.Add: "+",
                ast.Sub: "-",
                ast.Mult: "*",
                ast.Div: "/",
                ast.Mod: "%",
                ast.Pow: "**",
                ast.BitOr: "|",
                ast.BitAnd: "&",
                ast.BitXor: "^",
            }
            return ops.get(type(op), "+")
        
        def _get_unaryop(self, op: ast.unaryop) -> str:
            ops = {
                ast.Not: "!",
                ast.USub: "-",
                ast.UAdd: "+",
                ast.Invert: "~",
            }
            return ops.get(type(op), "")
        
        def _get_cmpop(self, op: ast.cmpop) -> str:
            ops = {
                ast.Eq: "===",
                ast.NotEq: "!==",
                ast.Lt: "<",
                ast.LtE: "<=",
                ast.Gt: ">",
                ast.GtE: ">=",
                ast.In: "in",
            }
            return ops.get(type(op), "===")
        
        def generic_visit(self, node: ast.AST) -> str:
            return ""
    
    transpiler = JSTranspiler()
    
    # Find the lambda or function
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda):
            return transpiler.visit(node)
    
    return ""


def compile_onclick(handler: Callable) -> str:
    """
    Compile an onclick handler to JavaScript.
    
    Usage:
        count = Signal(0)
        
        button(onclick=compile_onclick(lambda: count.update(lambda x: x + 1)))
    """
    js = transpile_handler(handler)
    if js:
        return js
    
    # Fallback: try to generate a server action call
    if hasattr(handler, '_action_id'):
        action_id = handler._action_id
        return f"(e) => __pynext__.callAction('{action_id}', e)"
    
    return ""


def compile_event_handler(handler: Callable, event_type: str = "click") -> dict:
    """
    Compile an event handler and return hydration data.
    
    Usage:
        data = compile_event_handler(lambda: count.set(5))
        # Returns: {"js": "() => ...", "type": "click"}
    """
    js = transpile_handler(handler)
    return {
        "js": js,
        "type": event_type,
        "valid": bool(js),
    }

