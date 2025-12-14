"""
PyNext Batch - Update Batching and Performance Utilities

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This module provides utilities for PERFORMANCE OPTIMIZATION:

1. batch() - Group multiple signal updates into one notification round
2. untrack() - Read signals without creating dependencies
3. createRoot() - Create isolated reactive scopes with manual disposal
4. on() - Explicit dependency declaration
5. createReaction() - Manual track/trigger pattern

=============================================================================
WHY BATCHING MATTERS
=============================================================================

    Without batching:
        count.set(1)   # Effect runs
        name.set("A")  # Effect runs again
        age.set(25)    # Effect runs AGAIN
        = 3 effect executions
    
    With batching:
        batch(lambda: (
            count.set(1),
            name.set("A"),
            age.set(25)
        ))
        = 1 effect execution (at the end)

=============================================================================
"""

from __future__ import annotations

from typing import Any, Callable, Optional, TypeVar

# Re-export from context
from pynext.reactive.context import (
    batch,
    untrack,
    get_observer,
    set_observer,
    is_batching,
    schedule_effect,
)

T = TypeVar("T")


# =============================================================================
# CREATEROOT - Isolated Reactive Scope
# =============================================================================

def createRoot(fn: Callable[[Callable[[], None]], T]) -> T:
    """
    Create an isolated reactive scope with manual disposal.
    
    Example:
        def setup(dispose):
            count = signal(0)
            effect(lambda: print(count()))
            return count, dispose
        
        count, dispose = createRoot(setup)
        count.set(5)  # Effect runs
        dispose()     # Cleanup
    """
    disposed = False
    cleanups: list = []
    
    def dispose():
        nonlocal disposed
        if disposed:
            return
        disposed = True
        for cleanup in reversed(cleanups):
            try:
                cleanup()
            except Exception:
                pass
    
    return fn(dispose)


# =============================================================================
# ON - Explicit Dependency Declaration
# =============================================================================

def on(
    deps: Callable[[], Any],
    fn: Callable[[Any, Any], Any],
    defer: bool = False,
) -> Callable[[], None]:
    """
    Explicitly declare dependencies instead of auto-tracking.
    
    Returns a dispose function.
    
    Example:
        dispose = on(
            lambda: count(),  # Only track count
            lambda value, prev: print(f"Changed from {prev} to {value}"),
            defer=True  # Don't run immediately
        )
        dispose()  # Stop watching
    """
    from pynext.reactive.effect import Effect
    
    prev_value = [None]
    first_run = [True]
    
    def effect_fn():
        # Read dependencies (tracked)
        value = deps()
        
        if first_run[0]:
            first_run[0] = False
            if defer:
                prev_value[0] = value
                return
        
        # Call fn with current and previous values (untracked)
        result = untrack(lambda: fn(value, prev_value[0]))
        prev_value[0] = value
        return result
    
    eff = Effect(effect_fn)
    return eff.dispose


# =============================================================================
# CREATE REACTION - Manual Track/Trigger
# =============================================================================

def createReaction(
    track_fn: Callable[[], T] = None,
    react_fn: Callable[[T], None] = None,
) -> tuple[Callable[[], None], Callable[[], None]]:
    """
    Create a reaction with separate tracking and reacting phases.
    
    Returns (track, trigger) functions.
    
    - track(): Call in an effect to establish dependency
    - trigger(): Notify subscribers that data changed
    
    Example:
        track, trigger = createReaction()
        
        @effect
        def reaction():
            track()  # Subscribe to this reaction
            print("Reaction triggered!")
        
        trigger()  # Will re-run the effect
    """
    from pynext.reactive.signal import Signal
    
    # Internal signal for triggering
    sig = Signal(0)
    
    def track():
        """Call this inside an effect to subscribe."""
        sig()  # Read to establish dependency
    
    def trigger():
        """Call this to notify subscribers."""
        sig.set(sig._value + 1)  # Increment to trigger
    
    return track, trigger


# =============================================================================
# TRANSITIONS - Non-Urgent Updates
# =============================================================================

def startTransition(fn: Callable[[], None]) -> None:
    """
    Mark updates as non-urgent (transitions).
    
    Currently just runs the function immediately.
    Future: Will integrate with Suspense for concurrent rendering.
    """
    fn()


_deferred_effects = []  # Keep references to prevent GC

def deferredValue(source: Callable[[], T]) -> Callable[[], T]:
    """
    Create a deferred version of a signal.
    
    Returns a callable that returns the deferred value.
    """
    from pynext.reactive.signal import Signal
    from pynext.reactive.effect import Effect
    
    # Create internal signal to hold deferred value
    deferred = Signal(source())
    
    # Effect to sync with source
    def _effect_fn():
        deferred.set(source())
    
    eff = Effect(_effect_fn)
    
    # Keep reference to prevent GC
    _deferred_effects.append(eff)
    
    # Return a callable
    return deferred


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "batch",
    "untrack",
    "createRoot",
    "on",
    "createReaction",
    "startTransition",
    "deferredValue",
]
