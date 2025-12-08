"""
Memo - Memoized Reactive Computations

A Memo (also called Computed) is a derived value that:
1. Automatically tracks signal dependencies
2. Caches its value until dependencies change
3. Only recomputes when actually read (lazy evaluation)
4. Can be read like a signal

Memos are used for derived state:
- Filtered/sorted lists
- Computed properties
- Complex calculations
"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Generic, Optional, TypeVar
from dataclasses import dataclass, field
from weakref import WeakSet

from pynext.reactive.context import (
    Computation,
    get_current_owner,
    get_current_observer,
    is_batching,
    _current_observer,
)

T = TypeVar("T")


@dataclass
class MemoOptions:
    """Options for Memo creation."""
    name: Optional[str] = None
    equals: Optional[Callable[[T, T], bool]] = None


class Memo(Computation, Generic[T]):
    """
    A memoized reactive computation.
    
    Memos cache their computed value and only recompute when their
    dependencies change. They're lazy - computation only happens when
    the value is actually read.
    
    Usage:
        count = Signal(0)
        
        # Create a memo
        doubled = Memo(lambda: count() * 2)
        
        # Read like a signal
        print(doubled())  # 0
        
        count.set(5)
        print(doubled())  # 10 (recomputed)
        print(doubled())  # 10 (cached, no recomputation)
    """
    
    __slots__ = (
        "_id",
        "_name",
        "_value",
        "_equals",
        "_computing",
    )
    
    _is_signal: bool = True  # Can be read like a signal
    _is_memo: bool = True
    _is_reactive: bool = True
    
    def __init__(
        self,
        fn: Callable[[], T],
        options: Optional[MemoOptions] = None,
        *,
        name: Optional[str] = None,
        equals: Optional[Callable[[T, T], bool]] = None,
    ):
        """
        Create a new Memo.
        
        Args:
            fn: The computation function
            options: MemoOptions for configuration
            name: Optional name for debugging
            equals: Custom equality function
        """
        super().__init__(
            fn=fn,
            owner=get_current_owner(),
            pure=True,
        )
        
        self._id: str = f"memo_{uuid.uuid4().hex[:12]}"
        self._name: str = name or (options and options.name) or self._id
        self._value: Optional[T] = None
        self._equals: Optional[Callable[[T, T], bool]] = equals or (options and options.equals)
        self._computing: bool = False
        
        # Mark as dirty initially
        self.state = 2  # Dirty
    
    def __call__(self) -> T:
        """
        Read the memoized value.
        
        If dirty, recomputes first. Tracks dependency if inside effect.
        """
        # Track dependency
        observer = get_current_observer()
        if observer is not None:
            self.observers.add(observer)
            observer._add_source(self)
        
        # Recompute if dirty
        if self.state == 2:  # Dirty
            self._run()
        
        return self._value  # type: ignore
    
    def get(self) -> T:
        """Alias for __call__."""
        return self()
    
    def peek(self) -> T:
        """Read without tracking dependency."""
        if self.state == 2:
            self._run()
        return self._value  # type: ignore
    
    def _run(self) -> T:
        """Recompute the memoized value."""
        if self.disposed or self._computing:
            return self._value  # type: ignore
        
        self._computing = True
        
        try:
            # Clear old dependencies
            self._clear_sources()
            
            # Set this as current observer for tracking
            prev_observer = _current_observer.get()
            _current_observer.set(self)
            
            try:
                # Compute new value
                if self.fn:
                    new_value = self.fn()
                    
                    # Check if value changed
                    if self._value is not None:
                        if self._equals:
                            if self._equals(self._value, new_value):
                                self.state = 0  # Clean
                                return self._value
                        elif self._value == new_value:
                            self.state = 0
                            return self._value
                    
                    old_value = self._value
                    self._value = new_value
                    
                    # Notify observers if value changed
                    if old_value is not None:
                        self._notify_observers()
                        
            finally:
                _current_observer.set(prev_observer)
                self.state = 0  # Clean
                
        finally:
            self._computing = False
        
        return self._value  # type: ignore
    
    def _notify(self) -> None:
        """Called when a source signal changes."""
        if self.disposed:
            return
        
        # Just mark dirty - don't recompute yet (lazy)
        self.state = 2  # Dirty
        
        # Notify observers that we might have changed
        self._notify_observers()
    
    def _notify_observers(self) -> None:
        """Notify computations that depend on this memo."""
        observers = list(self.observers)
        for observer in observers:
            if hasattr(observer, "_notify"):
                observer._notify()
    
    def _subscribe(self, observer: Any) -> None:
        """Add an observer (effect/memo that depends on this)."""
        self.observers.add(observer)
    
    def _unsubscribe(self, observer: Any) -> None:
        """Remove an observer."""
        self.observers.discard(observer)
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    def __str__(self) -> str:
        return str(self())
    
    def __repr__(self) -> str:
        return f"Memo({self._name!r}, value={self._value!r})"
    
    def to_json(self) -> dict:
        """Serialize for hydration."""
        return {
            "id": self._id,
            "name": self._name,
            "value": self(),
        }


# Alias for compatibility
Computed = Memo


def createMemo(
    fn: Callable[[], T],
    options: Optional[MemoOptions] = None,
) -> Callable[[], T]:
    """
    Create a memoized computation.
    
    SolidJS-style API - returns a getter function.
    
    Usage:
        doubled = createMemo(lambda: count() * 2)
        print(doubled())
    """
    m = Memo(fn, options)
    return m.get


def memo(
    fn: Callable[[], T],
    name: Optional[str] = None,
) -> Memo[T]:
    """
    Create a memoized computation.
    
    Returns the Memo object directly.
    
    Usage:
        doubled = memo(lambda: count() * 2)
        print(doubled())
    """
    return Memo(fn, name=name)


def computed(
    fn: Callable[[], T],
    name: Optional[str] = None,
) -> Memo[T]:
    """Alias for memo()."""
    return Memo(fn, name=name)


def createSelector(
    source: Callable[[], T],
    fn: Optional[Callable[[T, T], bool]] = None,
) -> Callable[[T], bool]:
    """
    Create a conditional signal selector.
    
    Useful for optimizing list selection where only one item
    should be "selected" at a time.
    
    Usage:
        selected_id = Signal(1)
        is_selected = createSelector(selected_id)
        
        for item in items:
            if is_selected(item.id):
                # Only this item updates when selection changes
                highlight(item)
    """
    prev_value: Optional[T] = None
    selected_items: set = set()
    
    def selector(key: T) -> bool:
        nonlocal prev_value
        
        if fn:
            return fn(source(), key)
        return source() == key
    
    return selector

