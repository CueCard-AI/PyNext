"""
Signal - Core Reactive Primitive

A Signal is a reactive value container that:
1. Tracks dependencies automatically when read inside effects
2. Notifies all subscribers when value changes
3. Supports batched updates for performance
4. Integrates with the ownership system for cleanup

This implementation is designed to be compiled to efficient JavaScript
at build time, matching SolidJS performance characteristics.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Generic, Optional, TypeVar, Union, overload
from weakref import WeakSet
from dataclasses import dataclass, field

from pynext.reactive.context import (
    get_current_observer,
    get_current_owner,
    schedule_effect,
    is_batching,
)

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class SignalOptions:
    """Options for Signal creation."""
    name: Optional[str] = None
    equals: Optional[Callable[[T, T], bool]] = None  # Custom equality check


class Signal(Generic[T]):
    """
    A reactive value container with automatic dependency tracking.
    
    Signals are the foundation of PyNext's reactivity system. When read inside
    an Effect or Memo, they automatically register as dependencies. When their
    value changes, all dependent computations are re-executed.
    
    Usage:
        count = Signal(0)
        
        # Read (triggers dependency tracking if inside effect)
        current = count()
        
        # Write (triggers updates)
        count.set(5)
        
        # Update based on previous value
        count.update(lambda x: x + 1)
    
    Performance:
        - O(1) reads and writes
        - O(n) notification where n is number of subscribers
        - Batched updates coalesce multiple changes into single notification
    """
    
    __slots__ = (
        "_value",
        "_id", 
        "_name",
        "_subscribers",
        "_equals",
        "_pending",
        "_owner",
    )
    
    # Marker for type checking
    _is_signal: bool = True
    _is_reactive: bool = True
    
    def __init__(
        self,
        initial_value: T,
        options: Optional[SignalOptions] = None,
        *,
        name: Optional[str] = None,
        equals: Optional[Callable[[T, T], bool]] = None,
    ):
        """
        Create a new Signal with an initial value.
        
        Args:
            initial_value: The initial value of the signal
            options: SignalOptions for configuration
            name: Optional name for debugging
            equals: Custom equality function (default: !=)
        """
        self._value: T = initial_value
        self._id: str = f"sig_{uuid.uuid4().hex[:12]}"
        self._name: str = name or (options and options.name) or self._id
        self._subscribers: WeakSet[Any] = WeakSet()  # Effects/Memos watching this signal
        self._equals: Optional[Callable[[T, T], bool]] = equals or (options and options.equals)
        self._pending: bool = False  # Whether update is pending in batch
        self._owner = get_current_owner()  # Owner for cleanup
    
    def __call__(self) -> T:
        """
        Read the signal value.
        
        If called inside an Effect or Memo, automatically registers
        this signal as a dependency.
        
        Returns:
            The current value
        """
        # Track dependency if we're inside an effect/memo
        observer = get_current_observer()
        if observer is not None:
            self._subscribe(observer)
            observer._add_source(self)
        
        return self._value
    
    def get(self) -> T:
        """Alias for __call__. Read the current value."""
        return self()
    
    def peek(self) -> T:
        """
        Read value without tracking dependency.
        
        Useful when you need to read a signal inside an effect
        but don't want changes to trigger re-execution.
        """
        return self._value
    
    def set(self, value: T) -> T:
        """
        Set a new value.
        
        If the value is different (according to equality check),
        notifies all subscribers.
        
        Args:
            value: The new value
            
        Returns:
            The new value
        """
        return self._write(value)
    
    def update(self, fn: Callable[[T], T]) -> T:
        """
        Update value using a function.
        
        The function receives the current value and returns the new value.
        
        Args:
            fn: Function that takes current value and returns new value
            
        Returns:
            The new value
        """
        return self._write(fn(self._value))
    
    def _write(self, value: T) -> T:
        """Internal write implementation."""
        # Check equality
        if self._equals:
            if self._equals(self._value, value):
                return self._value
        elif self._value == value:
            return self._value
        
        # Update value
        old_value = self._value
        self._value = value
        
        # Notify subscribers
        if is_batching():
            self._pending = True
            schedule_effect(self._notify)
        else:
            self._notify()
        
        return value
    
    def _subscribe(self, observer: Any) -> None:
        """Add a subscriber (effect/memo)."""
        self._subscribers.add(observer)
    
    def _unsubscribe(self, observer: Any) -> None:
        """Remove a subscriber."""
        self._subscribers.discard(observer)
    
    def _notify(self) -> None:
        """Notify all subscribers of value change."""
        self._pending = False
        
        # Create a copy to avoid modification during iteration
        subscribers = list(self._subscribers)
        
        for subscriber in subscribers:
            if hasattr(subscriber, "_notify"):
                subscriber._notify()
    
    @property
    def id(self) -> str:
        """Get the unique ID of this signal."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get the name of this signal."""
        return self._name
    
    def __str__(self) -> str:
        """String representation for template rendering."""
        return str(self._value)
    
    def __repr__(self) -> str:
        return f"Signal({self._value!r}, name={self._name!r})"
    
    # Serialization for hydration
    def to_json(self) -> dict:
        """Serialize for hydration data."""
        import json
        return {
            "id": self._id,
            "name": self._name,
            "value": self._value,
        }
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        import json
        value_json = json.dumps(self._value)
        return f"__pynext__.createSignal('{self._id}', {value_json})"


# Type aliases for compatibility
ReadSignal = Callable[[], T]
WriteSignal = Callable[[T], T]
SignalTuple = tuple[ReadSignal[T], WriteSignal[T]]


def createSignal(
    initial_value: T,
    options: Optional[SignalOptions] = None,
) -> tuple[Callable[[], T], Callable[[T], T]]:
    """
    Create a signal and return a tuple of (getter, setter).
    
    This is the SolidJS-style API.
    
    Usage:
        count, setCount = createSignal(0)
        print(count())  # 0
        setCount(5)
        print(count())  # 5
    
    Args:
        initial_value: The initial value
        options: Optional SignalOptions
        
    Returns:
        Tuple of (getter, setter) functions
    """
    sig = Signal(initial_value, options)
    return (sig.get, sig.set)


def signal(initial_value: T, name: Optional[str] = None) -> Signal[T]:
    """
    Create a new Signal with the given initial value.
    
    Convenience function for Signal creation.
    
    Usage:
        count = signal(0)
        count.set(5)
    """
    return Signal(initial_value, name=name)


# Accessor type for compiled output
@dataclass
class Accessor(Generic[T]):
    """
    An accessor is a read-only signal reference.
    
    Used in compiled output where we need to pass signal reads
    as props without exposing the setter.
    """
    _getter: Callable[[], T]
    
    def __call__(self) -> T:
        return self._getter()
    
    def get(self) -> T:
        return self._getter()


def isSignal(value: Any) -> bool:
    """Check if a value is a Signal."""
    return hasattr(value, "_is_signal") and value._is_signal


def isAccessor(value: Any) -> bool:
    """Check if a value is callable (accessor pattern)."""
    return callable(value) and not hasattr(value, "set")

