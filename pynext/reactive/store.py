"""
Store - Deep Reactive State Management

A Store provides reactive access to nested objects and arrays.
Unlike Signals (which track a single value), Stores track individual
properties at any depth, enabling fine-grained updates.

Key features:
- Proxy-based tracking
- Nested reactivity
- Array mutation detection
- Immutable update helpers (produce, reconcile)
"""

from __future__ import annotations

import uuid
import copy
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union, overload
from dataclasses import dataclass, field
from weakref import WeakSet

from pynext.reactive.context import (
    get_current_owner,
    get_current_observer,
    is_batching,
    schedule_effect,
)
from pynext.reactive.signal import Signal

T = TypeVar("T")


@dataclass
class StoreOptions:
    """Options for Store creation."""
    name: Optional[str] = None


class StoreProxy:
    """
    A proxy wrapper that tracks property access and mutations.
    
    This enables fine-grained reactivity - only the specific
    properties that changed will trigger updates.
    """
    
    __slots__ = (
        "_target",
        "_store",
        "_path",
        "_parent",
    )
    
    def __init__(
        self,
        target: Any,
        store: "Store",
        path: tuple = (),
        parent: Optional["StoreProxy"] = None,
    ):
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_store", store)
        object.__setattr__(self, "_path", path)
        object.__setattr__(self, "_parent", parent)
    
    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        # Track dependency
        store._track((*path, name))
        
        if isinstance(target, dict):
            value = target.get(name)
        else:
            value = getattr(target, name, None)
        
        # Wrap nested objects
        if isinstance(value, (dict, list)):
            return StoreProxy(value, store, (*path, name), self)
        
        return value
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        # Unwrap if value is a proxy
        if isinstance(value, StoreProxy):
            value = object.__getattribute__(value, "_target")
        
        # Set the value
        if isinstance(target, dict):
            old_value = target.get(name)
            if old_value != value:
                target[name] = value
                store._notify((*path, name))
        else:
            old_value = getattr(target, name, None)
            if old_value != value:
                setattr(target, name, value)
                store._notify((*path, name))
    
    def __getitem__(self, key: Any) -> Any:
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        # Track dependency
        store._track((*path, key))
        
        value = target[key]
        
        # Wrap nested objects
        if isinstance(value, (dict, list)):
            return StoreProxy(value, store, (*path, key), self)
        
        return value
    
    def __setitem__(self, key: Any, value: Any) -> None:
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        # Unwrap if value is a proxy
        if isinstance(value, StoreProxy):
            value = object.__getattribute__(value, "_target")
        
        old_value = target[key] if key in target else None
        if old_value != value:
            target[key] = value
            store._notify((*path, key))
    
    def __len__(self) -> int:
        target = object.__getattribute__(self, "_target")
        return len(target)
    
    def __iter__(self):
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        if isinstance(target, list):
            for i, item in enumerate(target):
                store._track((*path, i))
                if isinstance(item, (dict, list)):
                    yield StoreProxy(item, store, (*path, i), self)
                else:
                    yield item
        else:
            for key in target:
                store._track((*path, key))
                value = target[key]
                if isinstance(value, (dict, list)):
                    yield StoreProxy(value, store, (*path, key), self)
                else:
                    yield value
    
    def __contains__(self, item: Any) -> bool:
        target = object.__getattribute__(self, "_target")
        return item in target
    
    def __repr__(self) -> str:
        target = object.__getattribute__(self, "_target")
        return f"StoreProxy({target!r})"
    
    def __str__(self) -> str:
        target = object.__getattribute__(self, "_target")
        return str(target)
    
    # List methods that mutate
    def append(self, item: Any) -> None:
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        if isinstance(item, StoreProxy):
            item = object.__getattribute__(item, "_target")
        
        target.append(item)
        store._notify(path)  # Notify that the list changed
    
    def pop(self, index: int = -1) -> Any:
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        result = target.pop(index)
        store._notify(path)
        return result
    
    def insert(self, index: int, item: Any) -> None:
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        if isinstance(item, StoreProxy):
            item = object.__getattribute__(item, "_target")
        
        target.insert(index, item)
        store._notify(path)
    
    def remove(self, item: Any) -> None:
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        target.remove(item)
        store._notify(path)
    
    def clear(self) -> None:
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        target.clear()
        store._notify(path)
    
    def extend(self, items: List) -> None:
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        target.extend(items)
        store._notify(path)
    
    # Dict methods
    def keys(self):
        target = object.__getattribute__(self, "_target")
        return target.keys()
    
    def values(self):
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        for key in target:
            store._track((*path, key))
            value = target[key]
            if isinstance(value, (dict, list)):
                yield StoreProxy(value, store, (*path, key), self)
            else:
                yield value
    
    def items(self):
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        for key in target:
            store._track((*path, key))
            value = target[key]
            if isinstance(value, (dict, list)):
                yield key, StoreProxy(value, store, (*path, key), self)
            else:
                yield key, value
    
    def get(self, key: Any, default: Any = None) -> Any:
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        store._track((*path, key))
        value = target.get(key, default)
        
        if isinstance(value, (dict, list)):
            return StoreProxy(value, store, (*path, key), self)
        return value
    
    def update(self, data: Dict) -> None:
        target = object.__getattribute__(self, "_target")
        store = object.__getattribute__(self, "_store")
        path = object.__getattribute__(self, "_path")
        
        target.update(data)
        store._notify(path)


class Store(Generic[T]):
    """
    A deep reactive store for complex nested state.
    
    Stores wrap objects/arrays and track access at any depth.
    When a nested property changes, only effects that read that
    specific property are notified.
    
    Usage:
        user = Store({
            "name": "John",
            "profile": {
                "email": "john@example.com",
                "settings": {"theme": "dark"}
            }
        })
        
        # Access triggers dependency tracking
        print(user.name)  # "John"
        print(user.profile.email)  # "john@example.com"
        
        # Mutation triggers fine-grained updates
        user.profile.settings.theme = "light"  # Only theme observers notified
    """
    
    __slots__ = (
        "_data",
        "_id",
        "_name",
        "_signals",
        "_owner",
    )
    
    _is_store: bool = True
    _is_reactive: bool = True
    
    def __init__(
        self,
        initial_value: T,
        options: Optional[StoreOptions] = None,
        *,
        name: Optional[str] = None,
    ):
        """
        Create a new Store.
        
        Args:
            initial_value: The initial data (dict or list)
            options: StoreOptions for configuration
            name: Optional name for debugging
        """
        # Deep copy to avoid mutation of original
        self._data: T = copy.deepcopy(initial_value)
        self._id: str = f"store_{uuid.uuid4().hex[:12]}"
        self._name: str = name or (options and options.name) or self._id
        
        # Signals for each tracked path
        self._signals: Dict[tuple, Signal] = {}
        
        self._owner = get_current_owner()
    
    def __call__(self) -> T:
        """Get the entire store value."""
        self._track(())
        return self._wrap(self._data, ())
    
    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        
        data = object.__getattribute__(self, "_data")
        self._track((name,))
        
        if isinstance(data, dict):
            value = data.get(name)
        else:
            value = getattr(data, name, None)
        
        return self._wrap(value, (name,))
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        
        data = object.__getattribute__(self, "_data")
        
        if isinstance(data, dict):
            old = data.get(name)
            if old != value:
                data[name] = value
                self._notify((name,))
        else:
            old = getattr(data, name, None)
            if old != value:
                setattr(data, name, value)
                self._notify((name,))
    
    def __getitem__(self, key: Any) -> Any:
        data = object.__getattribute__(self, "_data")
        self._track((key,))
        return self._wrap(data[key], (key,))
    
    def __setitem__(self, key: Any, value: Any) -> None:
        data = object.__getattribute__(self, "_data")
        old = data[key] if key in data else None
        if old != value:
            data[key] = value
            self._notify((key,))
    
    def _wrap(self, value: Any, path: tuple) -> Any:
        """Wrap nested objects in proxies for tracking."""
        if isinstance(value, (dict, list)):
            return StoreProxy(value, self, path, None)
        return value
    
    def _get_signal(self, path: tuple) -> Signal:
        """Get or create a signal for a path."""
        if path not in self._signals:
            self._signals[path] = Signal(None, name=f"{self._name}.{'.'.join(str(p) for p in path)}")
        return self._signals[path]
    
    def _track(self, path: tuple) -> None:
        """Track access to a path."""
        observer = get_current_observer()
        if observer is not None:
            signal = self._get_signal(path)
            signal._subscribe(observer)
            observer._add_source(signal)
    
    def _notify(self, path: tuple) -> None:
        """Notify that a path changed."""
        # Notify the specific path
        if path in self._signals:
            self._signals[path]._notify()
        
        # Also notify parent paths (for length changes, etc.)
        for i in range(len(path)):
            parent_path = path[:i]
            if parent_path in self._signals:
                self._signals[parent_path]._notify()
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    def __repr__(self) -> str:
        return f"Store({self._data!r}, name={self._name!r})"
    
    def __str__(self) -> str:
        return str(self._data)
    
    def to_json(self) -> dict:
        """Serialize for hydration."""
        return {
            "id": self._id,
            "name": self._name,
            "data": self._data,
        }


def createStore(
    initial_value: T,
    options: Optional[StoreOptions] = None,
) -> tuple[StoreProxy, Callable[[Callable[[T], None]], None]]:
    """
    Create a store and return (proxy, setter).
    
    SolidJS-style API.
    
    Usage:
        state, setState = createStore({"count": 0, "items": []})
        
        print(state.count)  # 0
        
        setState(lambda s: s.update({"count": 1}))
        # or
        state.count = 1
    """
    store = Store(initial_value, options)
    proxy = StoreProxy(store._data, store, (), None)
    
    def setter(fn: Callable[[Any], None]) -> None:
        fn(proxy)
    
    return proxy, setter


def store(initial_value: T, name: Optional[str] = None) -> Store[T]:
    """Create a Store. Convenience function."""
    return Store(initial_value, name=name)


def produce(fn: Callable[[T], None]) -> Callable[[T], T]:
    """
    Create an immutable updater function.
    
    Like Immer's produce - allows mutable-style updates
    that are actually immutable.
    
    Usage:
        state, setState = createStore({"items": []})
        
        setState(produce(lambda s: s.items.append({"id": 1})))
    """
    def updater(state: T) -> T:
        draft = copy.deepcopy(state)
        fn(draft)
        return draft
    return updater


def reconcile(value: T) -> Callable[[Any], T]:
    """
    Replace store contents with new value.
    
    Unlike produce which mutates, reconcile replaces.
    Useful for API responses.
    
    Usage:
        state, setState = createStore({})
        
        # Replace entire store
        setState(reconcile(api_response))
    """
    def updater(_: Any) -> T:
        return value
    return updater

