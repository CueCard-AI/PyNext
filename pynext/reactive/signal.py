"""
PyNext Signal - The Core Reactive Primitive

=============================================================================
WHAT THIS FILE DOES
=============================================================================

A Signal is a REACTIVE VALUE CONTAINER. It's the atomic unit of reactivity.

    count = signal(0)       # Create with initial value
    value = count()         # Read (tracks dependency if inside effect)
    count.set(5)           # Write (notifies all subscribers)
    count.update(lambda x: x + 1)  # Update based on current value
    count.peek()           # Read WITHOUT tracking

Think of a Signal as a variable that notifies listeners when it changes.

=============================================================================
WHY THIS EXISTS (React vs Signal)
=============================================================================

React setState (Virtual DOM):
    setState(5)
    └─► Re-render entire component tree
        └─► Create new Virtual DOM
            └─► Diff with previous VDOM (O(n) where n = tree size)
                └─► Patch real DOM
    
    Performance: O(component tree size) - SLOW for large apps

Signal set (Fine-grained):
    signal.set(5)
    └─► Notify only subscribed effects
        └─► Each effect updates its specific DOM node
    
    Performance: O(number of subscribers) - FAST, constant time

This is why SolidJS (which uses signals) benchmarks 10-50x faster than React.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    ┌─────────────────────────────────────────────────────────────────┐
    │  Signal(initial_value)                                          │
    │                                                                  │
    │  ┌──────────┐   ┌────────────────────────┐   ┌───────────────┐ │
    │  │ _value   │   │ _subscribers: set()    │   │ _id: "sig_x"  │ │
    │  │   = 0    │   │   {effect1, effect2}   │   │ _name: "count"│ │
    │  └──────────┘   └────────────────────────┘   └───────────────┘ │
    │                                                                  │
    │  signal()  ──► Check get_observer()                             │
    │               If observer exists → _subscribers.add(observer)   │
    │               Return _value                                      │
    │                                                                  │
    │  signal.set(5) ──► If _value != 5:                              │
    │                       _value = 5                                 │
    │                       For each sub: schedule_effect(sub)         │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

1. Application developers:
       count = signal(0)
       count.set(1)

2. Effect system (effect.py):
       Effects subscribe to signals when they read them

3. Memo system (memo.py):
       Memos are computed signals that track other signals

4. Store system (store.py):
       Stores use signals internally for each tracked path

5. Compiler (Phase 17.4):
       Extracts signal declarations to generate equivalent JS

=============================================================================
WHEN TO USE (vs Alternatives)
=============================================================================

Use signal() when:
    - You have a single value that changes
    - Multiple UI elements depend on this value
    - You want automatic re-rendering when it changes

Use store() instead when:
    - You have a complex nested object { user: { name: "..." } }
    - You need deep reactivity (nested property changes)

Use memo() instead when:
    - The value is derived from other signals
    - Computation is expensive and should be cached

=============================================================================
COMPILATION (How This Becomes JS)
=============================================================================

Python:
    count = signal(0)
    
Compiles to JavaScript:
    const count = createSignal(0);

Python:
    span()[count()]
    
Compiles to HTML + hydration marker:
    <span data-pynext-text="count">0</span>

Python:
    button(onclick=lambda: count.set(count() + 1))
    
Compiles to:
    <button data-pynext-click="count.set(count() + 1)">

The Python-to-JS compiler in Phase 17.4 reads signal declarations and
generates equivalent createSignal() calls in the JS bundle.

=============================================================================
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Optional, TypeVar, Union
from pynext.reactive.context import get_observer, schedule_effect

T = TypeVar("T")

# Counter for generating unique IDs
_signal_counter = 0


def _next_id() -> str:
    """Generate a unique signal ID."""
    global _signal_counter
    _signal_counter += 1
    return f"sig_{_signal_counter}"


# =============================================================================
# SIGNAL CLASS
# =============================================================================

class Signal(Generic[T]):
    """
    A reactive value container.
    
    Signals are the foundation of PyNext's reactivity. When a signal's value
    changes, all subscribers (effects/memos) are automatically notified.
    
    Example:
        count = signal(0)
        
        @effect
        def log():
            print(f"Count is: {count()}")  # Subscribes automatically
        
        count.set(5)  # Triggers log() → prints "Count is: 5"
    
    Attributes:
        _value: The current value
        _subscribers: Set of effects that depend on this signal
        _id: Unique identifier for hydration
        _name: Human-readable name for debugging
        _equals: Custom equality function
    """
    
    __slots__ = ("_value", "_subscribers", "_id", "_name", "_equals", "_form_id", "_parent_form")
    
    # Compilation marker - compiler uses this to identify signals
    __pynext_type__ = "signal"
    _is_signal = True
    _is_reactive = True
    
    def __init__(
        self,
        initial: T,
        name: Optional[str] = None,
        equals: Optional[Callable[[T, T], bool]] = None,
        options: Optional["SignalOptions"] = None,
    ):
        """
        Create a new signal.
        
        Args:
            initial: The initial value
            name: Human-readable name (for debugging/hydration)
            equals: Custom equality function. If provided, signal only
                    notifies when equals(old, new) returns False.
            options: SignalOptions object (legacy API)
        """
        # Handle options object (legacy API)
        if options is not None:
            name = name or getattr(options, 'name', None)
            equals = equals or getattr(options, 'equals', None)
        
        self._value: T = initial
        self._subscribers: set = set()
        self._id: str = _next_id()
        self._name: str = name or self._id
        self._equals: Callable[[T, T], bool] = equals or (lambda a, b: a == b)
        
        # Auto-register with render context for SSR hydration
        self._register_with_context()
    
    @property
    def id(self) -> str:
        """Get the signal ID."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get the signal name."""
        return self._name
    
    def __call__(self) -> T:
        """
        Read the current value.
        
        If called inside an effect, the effect subscribes to this signal
        and will re-run when the value changes.
        
        Returns:
            The current value
        
        Example:
            count = signal(0)
            print(count())  # 0
        """
        observer = get_observer()
        if observer is not None:
            self._subscribers.add(observer)
        return self._value
    
    def get(self) -> T:
        """Alias for __call__() - read the current value."""
        return self()
    
    def set(self, value: T) -> T:
        """
        Set a new value and notify subscribers.
        
        Only notifies if the value actually changed (according to equals).
        
        Args:
            value: The new value
        
        Returns:
            The new value
        
        Example:
            count.set(5)
            count.set(5)  # No notification - value unchanged
        """
        if not self._equals(self._value, value):
            self._value = value
            self._notify()
        return self._value
    
    def update(self, fn: Callable[[T], T]) -> T:
        """
        Update the value using a function.
        
        Safer than set(signal() + 1) because it's atomic.
        
        Args:
            fn: Function that takes current value and returns new value
        
        Returns:
            The new value
        
        Example:
            count.update(lambda x: x + 1)
            count.update(lambda x: x * 2)
        """
        return self.set(fn(self._value))
    
    def peek(self) -> T:
        """
        Read the current value WITHOUT subscribing.
        
        Use when you need the value but don't want the enclosing
        effect to re-run when this signal changes.
        
        Returns:
            The current value (no subscription created)
        
        Example:
            @effect
            def log():
                # Only re-runs when count changes, not when other changes
                print(f"Count: {count()}, Other: {other.peek()}")
        """
        return self._value
    
    def _notify(self) -> None:
        """Notify all subscribers that the value changed."""
        # Copy to avoid issues if subscriber list changes during iteration
        for subscriber in list(self._subscribers):
            schedule_effect(subscriber)
    
    def subscribe(self, fn: Callable[[T], None]) -> Callable[[], None]:
        """
        Subscribe to value changes (callback-style).
        
        Returns an unsubscribe function.
        
        Example:
            unsubscribe = count.subscribe(lambda v: print(v))
            count.set(5)  # Prints: 5
            unsubscribe()
        """
        signal_ref = self
        
        class CallbackEffect:
            def execute(self_inner):
                fn(signal_ref._value)
        
        cb_effect = CallbackEffect()
        self._subscribers.add(cb_effect)
        
        def unsubscribe():
            self._subscribers.discard(cb_effect)
        
        return unsubscribe
    
    # =========================================================================
    # HYDRATION SUPPORT (SSR → Client handoff)
    # =========================================================================
    
    def render_value(self) -> str:
        """
        Render the current value with a hydration marker.
        
        Used during SSR to output HTML that the client can hydrate.
        
        Returns:
            HTML string with data-pynext-text attribute
        
        Example:
            count.render_value()
            # → '<span data-pynext-text="count">0</span>'
        """
        from html import escape
        value_str = escape(str(self._value))
        return f'<span data-pynext-text="{self._name}">{value_str}</span>'
    
    def _register_with_context(self) -> None:
        """
        Auto-register this signal with the current render context (if any).
        
        Called during __init__ to ensure signals are tracked for SSR hydration.
        This is a no-op if there's no active render context (e.g., client-side).
        """
        try:
            from pynext.core.context import get_context
            ctx = get_context()
            if ctx is not None:
                ctx.register_signal(self)
        except ImportError:
            # Context module not available (e.g., in tests)
            pass
    
    def to_hydration_state(self) -> dict:
        """
        Serialize this signal for __PYNEXT_DATA__.
        
        Returns:
            Dict mapping signal name to current value
        
        Example:
            count.to_hydration_state()
            # → {"count": 0}
        """
        return {self._name: self._value}
    
    def get_js_init(self) -> str:
        """
        Get JavaScript initialization code.
        
        Returns:
            JavaScript code to create this signal on client
        
        Example:
            count.get_js_init()
            # → "const sig_1 = __pynext__.createSignal(0)"
        """
        import json
        return f"const {self._id} = __pynext__.createSignal({json.dumps(self._value)})"
    
    # =========================================================================
    # PYTHON MAGIC METHODS
    # =========================================================================
    
    def __repr__(self) -> str:
        return f"Signal({self._value!r}, name={self._name!r})"
    
    def __str__(self) -> str:
        return str(self._value)
    
    def to_json(self) -> dict:
        """Serialize signal to JSON-compatible dict."""
        return {
            "id": self._id,
            "name": self._name,
            "value": self._value,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def signal(
    initial: T,
    name: Optional[str] = None,
    equals: Optional[Callable[[T, T], bool]] = None,
) -> Signal[T]:
    """
    Create a reactive signal.
    
    This is the preferred way to create signals (lowercase, function-style).
    
    Args:
        initial: The initial value
        name: Human-readable name (optional)
        equals: Custom equality function (optional)
    
    Returns:
        A new Signal instance
    
    Example:
        count = signal(0)
        name = signal("Alice", name="user_name")
        
        # Custom equality for objects
        user = signal(
            {"id": 1, "name": "Alice"},
            equals=lambda a, b: a["id"] == b["id"]
        )
    """
    return Signal(initial, name=name, equals=equals)


# Alias for SolidJS-style API - returns (getter, setter) tuple
def createSignal(initial: T, name: Optional[str] = None) -> tuple:
    """
    SolidJS-style createSignal - returns (getter, setter) tuple.
    
    Example:
        get, set = createSignal(0)
        print(get())  # 0
        set(5)
        print(get())  # 5
    """
    sig = Signal(initial, name=name)
    return (sig, sig.set)


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

# Type alias for signal accessor (the callable)
Accessor = Signal

# Options class (for backward compat - not really used in new API)
class SignalOptions:
    """Options for signal creation (backward compatibility)."""
    def __init__(self, name: str = None, equals: Callable = None):
        self.name = name
        self.equals = equals


def isSignal(obj: Any) -> bool:
    """Check if an object is a Signal."""
    return isinstance(obj, Signal)


def isAccessor(obj: Any) -> bool:
    """Check if an object is callable like a Signal."""
    return callable(obj) and hasattr(obj, "__pynext_type__")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "Signal",
    "signal",
    "createSignal",
    "SignalOptions",
    "Accessor",
    "isSignal",
    "isAccessor",
]
