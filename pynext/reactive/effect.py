"""
PyNext Effect - Reactive Side Effects

=============================================================================
WHAT THIS FILE DOES
=============================================================================

An Effect is a function that RE-RUNS when its dependencies change.

    @effect
    def log_count():
        print(f"Count: {count()}")  # Auto-tracks count as dependency
    
    count.set(5)  # Triggers log_count automatically → prints "Count: 5"

Effects are the bridge between reactive data (signals) and the outside world
(DOM updates, console logs, API calls, etc).

=============================================================================
WHY THIS EXISTS (vs React useEffect)
=============================================================================

React useEffect:
    useEffect(() => {
        console.log(count);
    }, [count]);  // MANUAL dependency array - easy to get wrong!
    
    Problems:
    - Forget a dependency → stale closure bugs
    - Include wrong dependency → infinite loops
    - ESLint rules try to help but can't catch everything

PyNext effect:
    @effect
    def log():
        print(count())  # AUTOMATIC tracking - no array needed!
    
    Benefits:
    - Impossible to forget dependencies
    - Impossible to include wrong dependencies
    - Works correctly by construction

This is the key innovation from SolidJS that eliminates an entire class of bugs.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    ┌─────────────────────────────────────────────────────────────────┐
    │  @effect                                                         │
    │  def my_effect():                                                │
    │      print(count())                                              │
    │                                                                  │
    │  Execution Flow:                                                 │
    │  1. Create Effect object with fn=my_effect                       │
    │  2. effect.execute() called immediately                          │
    │  3. prev = set_observer(effect)  ← "I'm the one running now"    │
    │  4. my_effect() runs                                             │
    │  5. count() sees observer=effect, does: subscribers.add(effect)  │
    │  6. set_observer(prev)  ← Restore previous observer              │
    │                                                                  │
    │  Later, when count.set(5):                                       │
    │  1. count._notify() loops through subscribers                    │
    │  2. schedule_effect(effect) is called                            │
    │  3. effect.execute() runs (steps 3-6 repeat)                     │
    │  4. Dependencies are re-tracked each execution                   │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

1. Application developers:
       @effect
       def sync_to_dom():
           element.textContent = count()

2. Memo system (memo.py):
       Memos are special effects that cache their return value

3. Control flow (control_flow.py):
       Show, For, etc. use effects internally for reactive updates

4. Compiler (Phase 17.4):
       Generates createEffect() calls in JS bundle

=============================================================================
WHEN TO USE
=============================================================================

Use effect() when:
    - You need to perform side effects (DOM updates, logs, API calls)
    - The side effect should re-run when data changes

Use memo() instead when:
    - You're computing a derived value (no side effects)
    - The value should be cached

Don't use effect() for:
    - Computing values (use memo instead)
    - One-time setup (use onMount instead)

=============================================================================
CLEANUP
=============================================================================

Effects can return a cleanup function:

    @effect
    def setup_timer():
        timer_id = setInterval(tick, 1000)
        return lambda: clearInterval(timer_id)  # Cleanup

Cleanup runs:
    - Before each re-execution (to clean up previous run)
    - When the effect is disposed

=============================================================================
COMPILATION (How This Becomes JS)
=============================================================================

Python:
    @effect
    def log():
        print(count())

Compiles to JavaScript:
    createEffect(() => {
        console.log(count());
    });

The structure maps 1:1 to the JS runtime.

=============================================================================
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Union
from pynext.reactive.context import set_observer, get_observer, schedule_effect


# =============================================================================
# EFFECT CLASS
# =============================================================================

_effect_counter = 0


def _next_effect_id() -> str:
    """Generate a unique effect ID."""
    global _effect_counter
    _effect_counter += 1
    return f"eff_{_effect_counter}"


class Effect:
    """
    A reactive side effect that re-runs when dependencies change.
    
    Effects automatically track which signals they read and re-run
    when any of those signals change.
    
    Example:
        count = signal(0)
        
        @effect
        def log():
            print(f"Count: {count()}")
        
        count.set(5)  # Prints: "Count: 5"
    
    With cleanup:
        @effect
        def timer():
            id = setInterval(tick, 1000)
            return lambda: clearInterval(id)
    
    Attributes:
        _fn: The effect function
        _cleanup: Optional cleanup function from last run
        _disposed: Whether this effect has been disposed
    """
    
    __slots__ = ("_fn", "_cleanup", "_disposed", "_id", "_name", "_defer", "_pure", "_state")
    
    # Compilation marker
    __pynext_type__ = "effect"
    _is_effect = True
    
    def __init__(
        self,
        fn: Callable[[], Optional[Callable[[], None]]],
        name: Optional[str] = None,
        options: Optional["EffectOptions"] = None,
        defer: bool = False,
    ):
        """
        Create a new effect.
        
        Args:
            fn: The effect function. May return a cleanup function.
            name: Human-readable name for debugging
            options: EffectOptions object (legacy API)
            defer: If True, don't run immediately
        """
        # Handle options object
        if options is not None:
            name = name or getattr(options, 'name', None)
            defer = defer or getattr(options, 'defer', False)
        
        self._fn = fn
        self._cleanup: Optional[Callable[[], None]] = None
        self._disposed = False
        self._id = _next_effect_id()
        self._name = name or self._id
        self._defer = defer
        self._pure = False
        self._state = "clean"
        
        # Run immediately unless deferred
        if not defer:
            self.execute()
    
    @property
    def id(self) -> str:
        """Get the effect ID."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get the effect name."""
        return self._name
    
    @property
    def fn(self):
        """Get the effect function."""
        return self._fn
    
    def execute(self) -> None:
        """
        Execute the effect, tracking dependencies.
        
        This is called:
        - Once when the effect is created
        - Each time a dependency (signal) changes
        
        Steps:
        1. Skip if disposed
        2. Run cleanup from previous execution
        3. Set self as current observer
        4. Execute user function
        5. Store new cleanup if returned
        6. Restore previous observer
        """
        if self._disposed:
            return
        
        # Run cleanup from previous execution
        if self._cleanup is not None:
            try:
                self._cleanup()
            except Exception:
                pass  # Don't let cleanup errors stop execution
            self._cleanup = None
        
        # Track dependencies during execution
        prev_observer = set_observer(self)
        
        try:
            result = self._fn()
            
            # If fn returns a function, it's the cleanup
            if callable(result):
                self._cleanup = result
                
        finally:
            set_observer(prev_observer)
    
    def dispose(self) -> None:
        """
        Stop the effect and run cleanup.
        
        After disposal, the effect will never run again.
        
        Example:
            e = effect(lambda: print(count()))
            e.dispose()  # No more prints
            count.set(5)  # Nothing happens
        """
        if self._disposed:
            return
            
        self._disposed = True
        
        if self._cleanup is not None:
            try:
                self._cleanup()
            except Exception:
                pass
            self._cleanup = None
    
    def _run(self) -> None:
        """Backward compatibility alias for execute()."""
        self.execute()
    
    def __repr__(self) -> str:
        status = "disposed" if self._disposed else "active"
        return f"Effect({self._fn.__name__ if hasattr(self._fn, '__name__') else '?'}, {status})"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def effect(fn: Callable[[], Optional[Callable[[], None]]]) -> Effect:
    """
    Create a reactive effect.
    
    Can be used as a decorator or called directly.
    
    As decorator:
        @effect
        def log():
            print(count())
    
    Direct call:
        e = effect(lambda: print(count()))
        e.dispose()  # Stop the effect
    
    With cleanup:
        @effect
        def timer():
            id = start_timer()
            return lambda: stop_timer(id)
    
    Args:
        fn: The effect function. May return a cleanup function.
    
    Returns:
        Effect object with .dispose() method
    """
    return Effect(fn)


# Alias for SolidJS-style API
def createEffect(fn: Callable[[], Optional[Callable[[], None]]]) -> Effect:
    """SolidJS-style alias for effect()."""
    return Effect(fn)


# =============================================================================
# RENDER EFFECT (Synchronous DOM updates)
# =============================================================================

class RenderEffect(Effect):
    """
    A synchronous effect for DOM updates.
    
    Unlike regular effects which may be batched, render effects
    run synchronously for immediate DOM updates.
    """
    
    __pynext_type__ = "render_effect"


def createRenderEffect(fn: Callable[[], Optional[Callable[[], None]]]) -> RenderEffect:
    """Create a synchronous render effect."""
    return RenderEffect(fn)


# =============================================================================
# COMPUTATION EFFECT (Manual triggering)
# =============================================================================

class ComputationEffect(Effect):
    """
    An effect that can be manually triggered.
    
    Unlike auto-tracking effects, computation effects can be
    triggered explicitly via .run() method.
    """
    
    __pynext_type__ = "computation_effect"
    
    def __init__(self, fn: Callable):
        self._fn = fn
        self._cleanup = None
        self._disposed = False
        # Don't auto-run on creation
    
    def run(self) -> None:
        """Manually run the effect."""
        self.execute()


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

class EffectOptions:
    """Options for effect creation (backward compatibility)."""
    def __init__(self, name: str = None):
        self.name = name


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "Effect",
    "effect",
    "createEffect",
    "EffectOptions",
    "RenderEffect",
    "createRenderEffect",
    "ComputationEffect",
]
