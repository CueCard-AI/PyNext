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

