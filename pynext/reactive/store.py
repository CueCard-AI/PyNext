"""
PyNext Store - Deep Reactive Objects

=============================================================================
WHAT THIS FILE DOES
=============================================================================

A Store is a DEEPLY REACTIVE OBJECT. Any property change at any depth
triggers reactivity.

    todos = store({"items": [], "filter": "all"})
    
    todos["filter"] = "active"      # Triggers reactivity
    todos["items"].append({"text": "New"})  # Also triggers!
    todos["items"][0]["done"] = True  # Deep changes too!

Stores are for complex nested state. Signals are for simple values.

=============================================================================
WHY THIS EXISTS (vs Signals)
=============================================================================

Signals work great for simple values:

    count = signal(0)
    count.set(1)  # Easy!

But for complex objects, signals require replacing the entire object:

    # AWKWARD with signals
    user = signal({"name": "Alice", "age": 30})
    user.set({**user(), "age": 31})  # Must copy entire object!

Stores allow direct mutation:

    # NATURAL with stores
    user = store({"name": "Alice", "age": 30})
    user["age"] = 31  # Just set the property!

Stores use JavaScript-style Proxy to intercept all property access.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    ┌─────────────────────────────────────────────────────────────────┐
    │  todos = store({"items": [], "filter": "all"})                  │
    │                                                                  │
    │  Implementation uses Proxy-like behavior:                        │
    │                                                                  │
    │  todos["filter"]  ──► __getitem__("filter")                     │
    │                       1. Track this path as dependency          │
    │                       2. Return value (wrapped if nested)       │
    │                                                                  │
    │  todos["filter"] = "active"  ──► __setitem__("filter", ...)     │
    │                                  1. Update internal dict        │
    │                                  2. Notify subscribers          │
    │                                                                  │
    │  todos["items"].append(x)  ──► Returns wrapped list             │
    │                                append() is intercepted          │
    │                                Notifies store subscribers       │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
ARRAY MUTATIONS
=============================================================================

Stores track these array mutations:
- append / push
- pop
- insert
- remove
- extend
- clear
- sort
- reverse
- __setitem__ (index assignment)
- __delitem__

All trigger reactivity automatically.

=============================================================================
WHO USES THIS
=============================================================================

1. Application developers:
       todos = store({"items": [], "filter": "all"})
       todos["items"].append(new_item)

2. Control flow (control_flow.py):
       For(each=lambda: todos["items"])[...]

3. Compiler (Phase 17.4):
       Generates createStore() calls in JS bundle

=============================================================================
WHEN TO USE
=============================================================================

Use store() when:
    - You have nested data structures
    - You want to mutate properties directly
    - You have lists that grow/shrink

Use signal() when:
    - You have a single primitive value
    - You replace the entire value each time

=============================================================================
COMPILATION (How This Becomes JS)
=============================================================================

Python:
    todos = store({"items": [], "filter": "all"})
    todos["items"].append({"text": "New"})

Compiles to JavaScript:
    const todos = createStore({items: [], filter: "all"});
    todos.items.push({text: "New"});

The JS runtime uses Proxy to intercept all mutations.

=============================================================================
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterator, List, Optional, TypeVar, Union
from pynext.reactive.context import get_observer, schedule_effect

T = TypeVar("T")


# =============================================================================
# REACTIVE LIST WRAPPER
# =============================================================================

class ReactiveList(list):
    """
    A list that notifies the store on mutations.
    
    Wraps a regular list and intercepts all mutating operations.
    """
    
    __slots__ = ("_store", "_path")
    
    def __init__(self, items: list, store: "Store", path: str):
        super().__init__(items)
        object.__setattr__(self, "_store", store)
        object.__setattr__(self, "_path", path)
    
    def _notify(self) -> None:
        """Notify the parent store of changes."""
        self._store._notify()
    
    def _wrap_item(self, item: Any, index: int) -> Any:
        """Wrap nested items for deep reactivity."""
        if isinstance(item, dict):
            return ReactiveDict(item, self._store, f"{self._path}[{index}]")
        elif isinstance(item, list):
            return ReactiveList(item, self._store, f"{self._path}[{index}]")
        return item
    
    def __getitem__(self, index: int) -> Any:
        # Track access
        self._store._track()
        item = super().__getitem__(index)
        return self._wrap_item(item, index)
    
    def __setitem__(self, index: int, value: Any) -> None:
        super().__setitem__(index, value)
        self._notify()
    
    def __delitem__(self, index: int) -> None:
        super().__delitem__(index)
        self._notify()
    
    def append(self, item: Any) -> None:
        super().append(item)
        self._notify()
    
    def extend(self, items: list) -> None:
        super().extend(items)
        self._notify()
    
    def insert(self, index: int, item: Any) -> None:
        super().insert(index, item)
        self._notify()
    
    def remove(self, item: Any) -> None:
        super().remove(item)
        self._notify()
    
    def pop(self, index: int = -1) -> Any:
        result = super().pop(index)
        self._notify()
        return result
    
    def clear(self) -> None:
        super().clear()
        self._notify()
    
    def sort(self, **kwargs) -> None:
        super().sort(**kwargs)
        self._notify()
    
    def reverse(self) -> None:
        super().reverse()
        self._notify()
    
    def __iter__(self) -> Iterator:
        self._store._track()
        for i, item in enumerate(list.__iter__(self)):
            yield self._wrap_item(item, i)
    
    def __len__(self) -> int:
        self._store._track()
        return super().__len__()


# =============================================================================
# REACTIVE DICT WRAPPER
# =============================================================================

class ReactiveDict(dict):
    """
    A dict that notifies the store on mutations.
    
    Wraps a regular dict and intercepts all mutating operations.
    Supports both dict-style and attribute-style access.
    """
    
    def __init__(self, data: dict, store: "Store", path: str):
        super().__init__(data)
        object.__setattr__(self, "_store", store)
        object.__setattr__(self, "_path", path)
        object.__setattr__(self, "_wrappers", {})  # Cache for nested wrappers
    
    def _notify(self) -> None:
        """Notify the parent store of changes."""
        self._store._notify()
    
    def _wrap_value(self, value: Any, key: str) -> Any:
        """Wrap nested values for deep reactivity."""
        path = f"{self._path}.{key}" if self._path else key
        wrappers = object.__getattribute__(self, "_wrappers")
        
        if isinstance(value, dict) and not isinstance(value, ReactiveDict):
            # Check cache first
            if key in wrappers and isinstance(wrappers[key], ReactiveDict):
                # Update the wrapper's data
                wrapper = wrappers[key]
                wrapper.clear()
                wrapper.update(value)
                return wrapper
            # Create new wrapper and cache it
            wrapper = ReactiveDict(value, self._store, path)
            # Store wrapper reference back to parent for write-through
            object.__setattr__(wrapper, "_parent", self)
            object.__setattr__(wrapper, "_parent_key", key)
            wrappers[key] = wrapper
            return wrapper
        elif isinstance(value, list) and not isinstance(value, ReactiveList):
            if key in wrappers and isinstance(wrappers[key], ReactiveList):
                wrapper = wrappers[key]
                wrapper.clear()
                wrapper.extend(value)
                return wrapper
            wrapper = ReactiveList(value, self._store, path)
            wrappers[key] = wrapper
            return wrapper
        return value
    
    def __getitem__(self, key: str) -> Any:
        self._store._track()
        value = super().__getitem__(key)
        return self._wrap_value(value, key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, value)
        # Invalidate wrapper cache for this key
        wrappers = object.__getattribute__(self, "_wrappers")
        if key in wrappers:
            del wrappers[key]
        
        # Propagate change to parent if this is a nested dict
        try:
            parent = object.__getattribute__(self, "_parent")
            parent_key = object.__getattribute__(self, "_parent_key")
            # Update parent's copy with our current state
            dict.__setitem__(parent, parent_key, dict(self))
        except AttributeError:
            pass  # No parent, this is the root
        
        self._notify()
    
    def __getattr__(self, key: str) -> Any:
        """Support attribute access (dict.key)."""
        if key.startswith("_"):
            return object.__getattribute__(self, key)
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{key}'")
    
    def __setattr__(self, key: str, value: Any) -> None:
        """Support attribute assignment (dict.key = value)."""
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self[key] = value
    
    def __delitem__(self, key: str) -> None:
        super().__delitem__(key)
        self._notify()
    
    def get(self, key: str, default: Any = None) -> Any:
        self._store._track()
        if key in self:
            return self._wrap_value(super().__getitem__(key), key)
        return default
    
    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        self._notify()
    
    def pop(self, key: str, *args) -> Any:
        result = super().pop(key, *args)
        self._notify()
        return result
    
    def clear(self) -> None:
        super().clear()
        self._notify()
    
    def setdefault(self, key: str, default: Any = None) -> Any:
        if key not in self:
            self[key] = default
        return self[key]
    
    def __iter__(self) -> Iterator:
        self._store._track()
        return super().__iter__()
    
    def keys(self):
        self._store._track()
        return super().keys()
    
    def values(self):
        self._store._track()
        for key in super().keys():
            yield self._wrap_value(super().__getitem__(key), key)
    
    def items(self):
        self._store._track()
        for key in super().keys():
            yield key, self._wrap_value(super().__getitem__(key), key)


# =============================================================================
# STORE CLASS
# =============================================================================

class Store:
    """
    A deeply reactive object/dict.
    
    All property access and mutations at any depth are tracked.
    Supports both dict-style and attribute-style access.
    
    Example:
        todos = store({"items": [], "filter": "all"})
        
        @effect
        def log():
            print(f"Filter: {todos['filter']}")
            # or: print(f"Filter: {todos.filter}")
        
        todos["filter"] = "active"  # Triggers effect
        todos.filter = "active"     # Also works
        todos["items"].append({"text": "New"})  # Also triggers!
    
    Attributes:
        _data: The wrapped reactive data
        _subscribers: Effects that depend on this store
    """
    
    # Compilation marker
    __pynext_type__ = "store"
    is_store = True
    is_reactive = True
    
    def __init__(self, initial: dict, name: Optional[str] = None):
        """
        Create a new store.
        
        Args:
            initial: The initial dict (will be wrapped for reactivity)
            name: Human-readable name for debugging
        """
        object.__setattr__(self, "_subscribers", set())
        object.__setattr__(self, "_id", f"store_{id(self)}")
        object.__setattr__(self, "_name", name or f"store_{id(self)}")
        object.__setattr__(self, "_signals", {})  # For path tracking
        
        # Wrap the initial data
        object.__setattr__(self, "_data", ReactiveDict(initial, self, ""))
        
        # Auto-register with render context for SSR hydration
        self._register_with_context()
    
    def _register_with_context(self) -> None:
        """
        Auto-register this store with the current render context (if any).
        
        Called during __init__ to ensure stores are tracked for SSR hydration.
        """
        try:
            from pynext.core.context import get_context
            ctx = get_context()
            if ctx is not None:
                ctx.register_store(self)
        except ImportError:
            pass
    
    def _track(self) -> None:
        """Track the current observer as a subscriber."""
        observer = get_observer()
        if observer is not None:
            self._subscribers.add(observer)
    
    def _notify(self) -> None:
        """Notify all subscribers of changes."""
        for subscriber in list(self._subscribers):
            schedule_effect(subscriber)
    
    def __call__(self) -> dict:
        """Get the entire store data as a dict."""
        self._track()
        return dict(self._data)
    
    def __getitem__(self, key: str) -> Any:
        """Get a property from the store."""
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set a property on the store."""
        self._data[key] = value
    
    def __delitem__(self, key: str) -> None:
        """Delete a property from the store."""
        del self._data[key]
    
    def __getattribute__(self, key: str) -> Any:
        """Get a property - data keys take priority over methods."""
        # Always allow access to private attributes and special methods
        if key.startswith("_") or key in ("is_store", "is_reactive", "__class__", "__dict__"):
            return object.__getattribute__(self, key)
        
        # Check for special method names that should be methods
        if key in ("get", "update", "to_json", "subscribe", "get_js_init", "to_hydration_state", "keys", "values"):
            return object.__getattribute__(self, key)
        
        # Check for special accessor methods
        if key == "get_id":
            return lambda: object.__getattribute__(self, "_id")
        if key == "get_name":
            return lambda: object.__getattribute__(self, "_name")
        
        # For all other keys, try data first
        try:
            data = object.__getattribute__(self, "_data")
            if key in data:
                return data[key]
        except AttributeError:
            pass
        
        # Fall back to normal attribute lookup
        return object.__getattribute__(self, key)
    
    def __setattr__(self, key: str, value: Any) -> None:
        """Set a property using attribute syntax (store.key = value)."""
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self._data[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Check if a key exists."""
        self._track()
        return key in self._data
    
    def __iter__(self) -> Iterator:
        """Iterate over keys."""
        return iter(self._data)
    
    def __len__(self) -> int:
        """Get the number of keys."""
        self._track()
        return len(self._data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a property with a default."""
        return self._data.get(key, default)
    
    def keys(self):
        """Get all keys (dict method - use _keys() to avoid conflict with data)."""
        return dict.keys(self._data)
    
    def values(self):
        """Get all values (dict method - use _values() to avoid conflict with data)."""
        return dict.values(self._data)
    
    def items(self):
        """Get all key-value pairs."""
        return dict.items(self._data)
    
    def update(self, *args, **kwargs) -> None:
        """Update multiple properties."""
        self._data.update(*args, **kwargs)
    
    def to_json(self) -> str:
        """Serialize store to JSON string."""
        import json
        return json.dumps(dict(self._data))
    
    def subscribe(self, fn: Callable[[dict], None]) -> Callable[[], None]:
        """
        Subscribe to store changes (callback-style).
        
        Returns an unsubscribe function.
        """
        class CallbackEffect:
            def execute(self_inner):
                fn(dict(self._data))
        
        cb_effect = CallbackEffect()
        self._subscribers.add(cb_effect)
        
        def unsubscribe():
            self._subscribers.discard(cb_effect)
        
        return unsubscribe
    
    def get_js_init(self) -> str:
        """
        Get JavaScript initialization code.
        
        Returns:
            JavaScript code to create this store on client
        """
        import json
        return f"__pynext__.createStore({json.dumps(dict(self._data))})"
    
    # =========================================================================
    # HYDRATION SUPPORT
    # =========================================================================
    
    def to_hydration_state(self) -> dict:
        """
        Serialize this store for __PYNEXT_DATA__.
        
        Returns:
            Dict with store name and current data
        """
        # Convert reactive wrappers back to plain dicts/lists
        def unwrap(obj):
            if isinstance(obj, (ReactiveDict, dict)):
                return {k: unwrap(v) for k, v in dict.items(obj)}
            elif isinstance(obj, (ReactiveList, list)):
                return [unwrap(item) for item in list.__iter__(obj)]
            return obj
        
        return {self._name: unwrap(self._data)}
    
    def __repr__(self) -> str:
        return f"Store({dict(self._data)!r})"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def store(initial: dict, name: Optional[str] = None) -> Store:
    """
    Create a deeply reactive store.
    
    Args:
        initial: Initial dict (will be made reactive)
        name: Optional name for debugging
    
    Returns:
        Store object with reactive properties
    
    Example:
        todos = store({"items": [], "filter": "all"})
        todos["filter"] = "active"  # Reactive!
        todos["items"].append({"text": "New"})  # Also reactive!
    """
    return Store(initial, name=name)


# SolidJS-style API returns tuple (store, setter)
def createStore(initial: dict, name: Optional[str] = None) -> tuple:
    """
    SolidJS-style createStore - returns (store, setter).
    
    Example:
        state, setState = createStore({"count": 0})
        print(state.count)  # 0
        setState("count", 5)  # or setState({"count": 5})
    """
    s = Store(initial, name=name)
    
    def setter(*args):
        """Update store values."""
        if len(args) == 1 and isinstance(args[0], dict):
            # setState({"key": value})
            for k, v in args[0].items():
                s[k] = v
        elif len(args) == 2:
            # setState("key", value)
            s[args[0]] = args[1]
        elif len(args) >= 3:
            # setState("path", "key", value)
            obj = s
            for key in args[:-2]:
                obj = obj[key]
            obj[args[-2]] = args[-1]
    
    return (s, setter)


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

# StoreProxy is an alias for the reactive wrappers
StoreProxy = ReactiveDict


class StoreOptions:
    """Options for store creation (backward compatibility)."""
    def __init__(self, name: str = None):
        self.name = name


def produce(store_obj: Store, fn: Callable[[dict], None]) -> None:
    """
    Immer-like produce for immutable-style updates.
    
    Allows mutation syntax while maintaining reactivity.
    """
    fn(store_obj._data)


def reconcile(store_obj: Store, new_data: dict) -> None:
    """
    Replace store contents with new data.
    
    Efficiently updates only changed properties.
    """
    # Clear old data
    for key in list(store_obj._data.keys()):
        if key not in new_data:
            del store_obj._data[key]
    
    # Update with new data
    store_obj._data.update(new_data)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "Store",
    "store",
    "createStore",
    "ReactiveList",
    "ReactiveDict",
    "StoreProxy",
    "StoreOptions",
    "produce",
    "reconcile",
]
