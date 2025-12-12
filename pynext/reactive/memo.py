"""
PyNext Memo - Cached Reactive Computations

=============================================================================
WHAT THIS FILE DOES
=============================================================================

A Memo is a CACHED DERIVED VALUE. It only recomputes when dependencies change.

    count = signal(0)
    doubled = memo(lambda: count() * 2)
    
    print(doubled())  # 0 - computes once
    print(doubled())  # 0 - returns cached value (no recompute)
    
    count.set(5)
    print(doubled())  # 10 - recomputes because count changed

Memos are like spreadsheet cells that recalculate only when inputs change.

=============================================================================
WHY THIS EXISTS (Performance)
=============================================================================

Without memos, expensive computations would run every time:

    # BAD: Recomputes every read
    def get_filtered_items():
        return [i for i in items() if i.active]  # O(n) every time!
    
    for _ in range(100):
        get_filtered_items()  # 100 * O(n) = slow!

With memos:

    # GOOD: Caches until items changes
    filtered = memo(lambda: [i for i in items() if i.active])
    
    for _ in range(100):
        filtered()  # O(1) after first call - instant!

Memos also enable "diamond dependency" patterns without glitches.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    ┌─────────────────────────────────────────────────────────────────┐
    │  doubled = memo(lambda: count() * 2)                            │
    │                                                                  │
    │  ┌──────────┐   ┌───────────┐   ┌─────────────────────────────┐│
    │  │ _value   │   │ _dirty    │   │ _subscribers: set()         ││
    │  │   = None │   │   = True  │   │   {effect1, effect2}        ││
    │  └──────────┘   └───────────┘   └─────────────────────────────┘│
    │                                                                  │
    │  doubled() read flow:                                           │
    │  1. Am I dirty? (dependencies changed since last compute)       │
    │     Yes → Recompute: run fn(), cache result, dirty = False      │
    │     No  → Return cached _value                                  │
    │  2. Add current observer to my subscribers                      │
    │  3. Return _value                                               │
    │                                                                  │
    │  When count changes:                                            │
    │  1. Memo receives notification                                  │
    │  2. Sets _dirty = True                                          │
    │  3. Notifies its own subscribers (they might need to rerun)     │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
LAZY EVALUATION
=============================================================================

Memos are LAZY - they don't compute until read:

    expensive = memo(lambda: slow_computation())  # No computation yet
    
    # ... lots of code ...
    
    if needed:
        value = expensive()  # NOW it computes

This is different from effects which run immediately.

=============================================================================
DIAMOND DEPENDENCY (Glitch-Free)
=============================================================================

    source = signal(1)
    left = memo(lambda: source() * 2)
    right = memo(lambda: source() * 3)
    combined = memo(lambda: left() + right())
    
    @effect
    def log():
        print(combined())
    
    source.set(2)
    # Prints: 10 (not 7 then 10)
    # "Glitch-free" = no intermediate states observed

=============================================================================
COMPILATION (How This Becomes JS)
=============================================================================

Python:
    doubled = memo(lambda: count() * 2)

Compiles to JavaScript:
    const doubled = createMemo(() => count() * 2);

=============================================================================
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Optional, TypeVar
from pynext.reactive.context import set_observer, get_observer, schedule_effect

T = TypeVar("T")


# =============================================================================
# MEMO CLASS
# =============================================================================

_memo_counter = 0


def _next_memo_id() -> str:
    """Generate a unique memo ID."""
    global _memo_counter
    _memo_counter += 1
    return f"memo_{_memo_counter}"


class Memo(Generic[T]):
    """
    A cached reactive computation.
    
    Memos track their dependencies and only recompute when those
    dependencies change. Results are cached for multiple reads.
    
    Example:
        count = signal(0)
        doubled = memo(lambda: count() * 2)
        
        print(doubled())  # 0 - computes
        print(doubled())  # 0 - cached
        
        count.set(5)
        print(doubled())  # 10 - recomputes
    
    Attributes:
        _fn: The computation function
        _value: Cached result
        _dirty: Whether recomputation is needed
        _subscribers: Effects/memos that depend on this memo
        _equals: Custom equality function
    """
    
    __slots__ = ("_fn", "_value", "_dirty", "_subscribers", "_equals", "_computing", "_id", "_name")
    
    # Compilation marker
    __pynext_type__ = "memo"
    _is_memo = True
    
    def __init__(
        self,
        fn: Callable[[], T],
        equals: Optional[Callable[[T, T], bool]] = None,
        name: Optional[str] = None,
        options: Optional["MemoOptions"] = None,
    ):
        """
        Create a new memo.
        
        Args:
            fn: The computation function
            equals: Custom equality for determining if value changed
            name: Human-readable name for debugging
            options: MemoOptions object (legacy API)
        """
        # Handle options object
        if options is not None:
            name = name or getattr(options, 'name', None)
            equals = equals or getattr(options, 'equals', None)
        
        self._fn = fn
        self._value: Optional[T] = None
        self._dirty = True  # Needs computation on first read
        self._subscribers: set = set()
        self._equals: Callable[[T, T], bool] = equals or (lambda a, b: a == b)
        self._computing = False  # Prevent infinite recursion
        self._id = _next_memo_id()
        self._name = name or self._id
        
        # Auto-register with render context for SSR hydration
        self._register_with_context()
    
    @property
    def id(self) -> str:
        """Get the memo ID."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get the memo name."""
        return self._name
    
    @property
    def fn(self):
        """Get the memo function."""
        return self._fn
    
    def __call__(self) -> T:
        """
        Get the memoized value.
        
        If dirty (dependencies changed), recomputes first.
        Subscribes the current observer if inside an effect.
        
        Returns:
            The cached or freshly computed value
        """
        # Subscribe current observer
        observer = get_observer()
        if observer is not None:
            self._subscribers.add(observer)
        
        # Recompute if dirty
        if self._dirty and not self._computing:
            self._recompute()
        
        return self._value  # type: ignore
    
    def _recompute(self) -> None:
        """Recompute the cached value."""
        self._computing = True
        prev_observer = set_observer(self)
        
        try:
            new_value = self._fn()
            
            # Only notify subscribers if value actually changed
            value_changed = self._value is None or not self._equals(self._value, new_value)
            self._value = new_value
            self._dirty = False
            
            if value_changed:
                self._notify_subscribers()
                
        finally:
            set_observer(prev_observer)
            self._computing = False
    
    def _notify_subscribers(self) -> None:
        """Notify subscribers that our value changed."""
        for subscriber in list(self._subscribers):
            schedule_effect(subscriber)
    
    def execute(self) -> None:
        """
        Called when a dependency changes.
        
        Marks this memo as dirty and notifies downstream subscribers.
        The actual recomputation happens lazily on next read.
        """
        if not self._dirty:
            self._dirty = True
            # Notify subscribers they might need to update
            for subscriber in list(self._subscribers):
                schedule_effect(subscriber)
    
    def peek(self) -> T:
        """
        Read the cached value WITHOUT subscribing.
        
        If dirty, computes first (but without creating subscription).
        
        Returns:
            The cached value
        """
        if self._dirty and not self._computing:
            # Compute but don't track
            prev = set_observer(None)
            try:
                self._recompute()
            finally:
                set_observer(prev)
        
        return self._value  # type: ignore
    
    def invalidate(self) -> None:
        """
        Force the memo to recompute on next read.
        
        Marks the memo as dirty without notifying subscribers.
        """
        self._dirty = True
    
    # =========================================================================
    # HYDRATION SUPPORT
    # =========================================================================
    
    def _register_with_context(self) -> None:
        """
        Auto-register this memo with the current render context (if any).
        
        Called during __init__ to ensure memos are tracked for SSR hydration.
        This is a no-op if there's no active render context.
        """
        try:
            from pynext.core.context import get_context
            ctx = get_context()
            if ctx is not None:
                ctx.register_memo(self)
        except ImportError:
            # Context module not available
            pass
    
    def to_json(self) -> dict:
        """
        Serialize memo to JSON-compatible dict.
        
        Returns:
            Dict with id, name, and current value
        
        Example:
            doubled = memo(lambda: count() * 2, name="doubled")
            doubled.to_json()
            # → {"id": "memo_1", "name": "doubled", "value": 0}
        """
        # Ensure we have a computed value
        if self._dirty and not self._computing:
            self._recompute()
        
        return {
            "id": self._id,
            "name": self._name,
            "value": self._value,
        }
    
    def get_js_init(self) -> str:
        """
        Get JavaScript initialization code for this memo.
        
        Returns:
            JavaScript code to create this memo on client
        
        Example:
            doubled.get_js_init()
            # → "const memo_1 = __pynext__.createMemo(() => 0)"
        
        Note:
            The compiled value is static (server-computed). For dynamic
            behavior, the compiler generates the full computation.
        """
        import json
        
        # Ensure we have a computed value
        if self._dirty and not self._computing:
            self._recompute()
        
        return f"const {self._id} = __pynext__.createMemo(() => {json.dumps(self._value)})"
    
    def to_hydration_state(self) -> dict:
        """
        Serialize this memo for __PYNEXT_DATA__.
        
        Returns:
            Dict mapping memo name to current value
        
        Example:
            doubled.to_hydration_state()
            # → {"doubled": 0}
        """
        # Ensure we have a computed value
        if self._dirty and not self._computing:
            self._recompute()
        
        return {self._name: self._value}
    
    def render_value(self) -> str:
        """
        Render this memo's value as HTML with hydration marker.
        
        Returns:
            HTML span with data-pynext-memo attribute
        
        Example:
            doubled.render_value()
            # → '<span data-pynext-memo="doubled">0</span>'
        """
        from html import escape
        
        # Ensure we have a computed value
        if self._dirty and not self._computing:
            self._recompute()
        
        value_str = escape(str(self._value))
        return f'<span data-pynext-memo="{self._name}">{value_str}</span>'
    
    def __repr__(self) -> str:
        status = "dirty" if self._dirty else f"cached={self._value!r}"
        return f"Memo({status})"
    
    def __str__(self) -> str:
        """Return string representation of the cached value."""
        if self._dirty and not self._computing:
            self._recompute()
        return str(self._value)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def memo(
    fn: Callable[[], T],
    equals: Optional[Callable[[T, T], bool]] = None,
    name: Optional[str] = None,
) -> Memo[T]:
    """
    Create a memoized computation.
    
    The computation runs lazily on first read, then caches until
    any dependency changes.
    
    Args:
        fn: The computation function
        equals: Custom equality for change detection
        name: Human-readable name for debugging/hydration
    
    Returns:
        Memo object (callable to get value)
    
    Example:
        count = signal(0)
        doubled = memo(lambda: count() * 2, name="doubled")
        
        print(doubled())  # 0
        count.set(5)
        print(doubled())  # 10
    """
    return Memo(fn, equals=equals, name=name)


# Alias for compatibility
def computed(fn: Callable[[], T], name: Optional[str] = None) -> Memo[T]:
    """Alias for memo() - some prefer 'computed'."""
    return Memo(fn)


# SolidJS-style alias
def createMemo(fn: Callable[[], T]) -> Memo[T]:
    """SolidJS-style alias for memo()."""
    return Memo(fn)


# Legacy class alias
Computed = Memo


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

class MemoOptions:
    """Options for memo creation (backward compatibility)."""
    def __init__(self, name: str = None, equals: Callable = None):
        self.name = name
        self.equals = equals


def createSelector(source: Callable, fn: Callable[[T], bool] = None):
    """
    Create a conditional signal selector.
    
    Returns a function that returns true only for the selected key.
    """
    def selector(key):
        return memo(lambda: fn(source()) if fn else source() == key)
    return selector


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "Memo",
    "memo",
    "computed",
    "createMemo",
    "Computed",
    "MemoOptions",
    "createSelector",
]
