"""
Batch - Update Batching and Untracking

This module provides utilities for:
- Batching multiple updates into single notification round
- Untracking signal reads (prevent dependency tracking)
- Creating reactive roots with manual disposal

Batching is critical for performance:
- Multiple signal updates → single DOM update
- Prevents cascading re-renders
- Ensures consistent state during updates
"""

from __future__ import annotations

from typing import Any, Callable, Optional, TypeVar
from pynext.reactive.context import (
    _batch_depth,
    _pending_effects,
    _current_observer,
    flush_updates,
    Owner,
    _current_owner,
    get_current_owner,
)

T = TypeVar("T")


def batch(fn: Callable[[], T]) -> T:
    """
    Batch multiple signal updates into a single notification round.
    
    All signal updates inside the batch are collected and their
    effects only run once at the end, preventing cascading updates.
    
    Usage:
        count = Signal(0)
        name = Signal("")
        
        # Without batch: 2 effect runs
        count.set(1)
        name.set("test")
        
        # With batch: 1 effect run
        batch(lambda: (
            count.set(1),
            name.set("test")
        ))
    
    Performance:
        - O(1) overhead for entering/exiting batch
        - Effects run once per batch, not once per update
        - Nested batches are supported (only outermost flushes)
    """
    # Increment batch depth
    current_depth = _batch_depth.get()
    _batch_depth.set(current_depth + 1)
    
    try:
        result = fn()
        return result
    finally:
        # Decrement batch depth
        new_depth = _batch_depth.get() - 1
        _batch_depth.set(new_depth)
        
        # If we're exiting the outermost batch, flush updates
        if new_depth == 0:
            flush_updates()


def untrack(fn: Callable[[], T]) -> T:
    """
    Execute a function without tracking signal dependencies.
    
    Useful when you need to read a signal inside an effect
    but don't want changes to that signal to trigger re-execution.
    
    Usage:
        count = Signal(0)
        name = Signal("")
        
        @Effect
        def my_effect():
            # Only tracks 'count', not 'name'
            print(f"Count: {count()}, Name: {untrack(lambda: name())}")
        
        count.set(1)  # Triggers effect
        name.set("test")  # Does NOT trigger effect
    """
    # Save current observer
    prev_observer = _current_observer.get()
    
    # Clear observer (no tracking)
    _current_observer.set(None)
    
    try:
        return fn()
    finally:
        # Restore observer
        _current_observer.set(prev_observer)


def createRoot(fn: Callable[[Callable[[], None]], T]) -> T:
    """
    Create a new reactive root with manual disposal.
    
    A root is an ownership boundary - when disposed, all reactive
    computations created within it are cleaned up.
    
    Usage:
        dispose = None
        
        def setup(dispose_fn):
            global dispose
            dispose = dispose_fn
            
            count = Signal(0)
            
            @Effect
            def log():
                print(count())
            
            return count
        
        count = createRoot(setup)
        
        count.set(5)  # Logs: 5
        dispose()  # Cleans up effect
        count.set(10)  # No log (effect disposed)
    """
    owner = Owner(parent=get_current_owner())
    
    prev_owner = _current_owner.get()
    _current_owner.set(owner)
    
    try:
        return fn(owner.dispose)
    finally:
        _current_owner.set(prev_owner)


def on(
    deps: Callable[[], Any],
    fn: Callable[[Any, Any], None],
    defer: bool = False,
) -> Callable[[], None]:
    """
    Explicitly declare effect dependencies.
    
    Unlike automatic tracking, 'on' lets you specify exactly
    which signals should trigger the effect.
    
    Usage:
        a = Signal(1)
        b = Signal(2)
        
        # Only runs when 'a' changes, even though 'b' is read
        on(
            deps=lambda: a(),
            fn=lambda value, prev: print(f"a changed from {prev} to {value}, b is {b()}")
        )
    """
    from pynext.reactive.effect import Effect
    
    prev_value: Any = None
    
    def effect_fn():
        nonlocal prev_value
        
        # Get current dependency value (tracked)
        current_value = deps()
        
        # Run callback with current and previous
        if not defer or prev_value is not None:
            # Run user function untracked
            untrack(lambda: fn(current_value, prev_value))
        
        prev_value = current_value
    
    effect = Effect(effect_fn)
    return effect.dispose


def createReaction(
    on_update: Callable[[], None],
    options: Optional[dict] = None,
) -> tuple[Callable[[], None], Callable[[], None]]:
    """
    Create a reaction that can be manually tracked and triggered.
    
    Returns (track, trigger) functions.
    
    Usage:
        track, trigger = createReaction(lambda: print("Updated!"))
        
        @Effect
        def my_effect():
            track()  # Register this effect
            # Do something
        
        trigger()  # Manually trigger all tracked effects
    """
    from pynext.reactive.signal import Signal
    
    _signal = Signal(0, name="_reaction_signal")
    
    def track():
        """Call this to register the current effect."""
        _signal()  # Creates dependency
    
    def trigger():
        """Call this to trigger all tracked effects."""
        _signal.update(lambda x: x + 1)
    
    return track, trigger


def startTransition(fn: Callable[[], None]) -> None:
    """
    Mark updates as non-urgent (transition).
    
    Transitions can be interrupted by more urgent updates,
    useful for keeping UI responsive during large updates.
    
    Usage:
        def search(query):
            # Urgent: update input immediately
            search_input.set(query)
            
            # Non-urgent: update results (can be interrupted)
            startTransition(lambda: search_results.set(fetch_results(query)))
    """
    # For now, just run the function
    # Full implementation would use a scheduler
    fn()


def deferredValue(source: Callable[[], T]) -> Callable[[], T]:
    """
    Create a deferred version of a value.
    
    The deferred value updates with a delay, useful for
    expensive renders that shouldn't block input.
    
    Usage:
        search_query = Signal("")
        deferred_query = deferredValue(lambda: search_query())
        
        # Immediate update
        search_query.set("hello")
        
        # deferred_query() updates later
    """
    from pynext.reactive.signal import Signal
    from pynext.reactive.effect import Effect
    
    deferred = Signal(source())
    
    @Effect
    def sync_deferred():
        value = source()
        # In browser: use requestIdleCallback
        # For now: immediate update
        deferred.set(value)
    
    return deferred.get

