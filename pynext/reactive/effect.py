"""
Effect - Reactive Side Effects

An Effect is a computation that:
1. Automatically tracks signal dependencies
2. Re-runs when any dependency changes
3. Supports cleanup functions for resource management
4. Integrates with the ownership system

Effects are used for side effects like:
- DOM updates
- Network requests
- Logging
- Timers
"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Optional, TypeVar, Union
from dataclasses import dataclass, field
from weakref import WeakSet

from pynext.reactive.context import (
    Computation,
    Owner,
    get_current_owner,
    get_current_observer,
    is_batching,
    schedule_effect,
    _current_observer,
)

T = TypeVar("T")


@dataclass
class EffectOptions:
    """Options for Effect creation."""
    name: Optional[str] = None
    defer: bool = False  # Defer first execution


class Effect(Computation):
    """
    A reactive side effect that auto-tracks dependencies.
    
    Effects run immediately and re-run whenever their dependencies change.
    They support cleanup functions for resource management.
    
    Usage:
        count = Signal(0)
        
        # Simple effect
        @Effect
        def log_count():
            print(f"Count is: {count()}")
        
        # Effect with cleanup
        def setup_timer():
            timer_id = setInterval(tick, 1000)
            return lambda: clearInterval(timer_id)
        
        effect(setup_timer)
        
        # Updating count triggers the effect
        count.set(5)  # Logs: "Count is: 5"
    """
    
    __slots__ = (
        "_id",
        "_name",
        "_cleanup",
        "_defer",
        "_running",
    )
    
    _is_effect: bool = True
    
    def __init__(
        self,
        fn: Optional[Callable[[], Optional[Callable[[], None]]]] = None,
        options: Optional[EffectOptions] = None,
        *,
        name: Optional[str] = None,
        defer: bool = False,
    ):
        """
        Create a new Effect.
        
        Args:
            fn: The effect function (can return a cleanup function)
            options: EffectOptions for configuration
            name: Optional name for debugging
            defer: If True, don't run immediately
        """
        super().__init__(
            fn=fn,
            owner=get_current_owner(),
            pure=False,
        )
        
        self._id: str = f"eff_{uuid.uuid4().hex[:12]}"
        self._name: str = name or (options and options.name) or self._id
        self._cleanup: Optional[Callable[[], None]] = None
        self._defer: bool = defer or (options and options.defer) or False
        self._running: bool = False
        
        # Run immediately unless deferred
        if fn and not self._defer:
            self._run()
    
    def __call__(
        self,
        fn: Callable[[], Optional[Callable[[], None]]]
    ) -> "Effect":
        """
        Decorator form - allows using @Effect syntax.
        
        Usage:
            @Effect
            def my_effect():
                print(count())
        """
        self.fn = fn
        if not self._defer:
            self._run()
        return self
    
    def _run(self) -> None:
        """Execute the effect function."""
        if self.disposed or self._running:
            return
        
        self._running = True
        
        try:
            # Run cleanup from previous execution
            if self._cleanup:
                try:
                    self._cleanup()
                except Exception:
                    pass
                self._cleanup = None
            
            # Clear old dependencies
            self._clear_sources()
            
            # Set this as current observer for tracking
            prev_observer = _current_observer.get()
            _current_observer.set(self)
            
            try:
                # Run the effect
                if self.fn:
                    result = self.fn()
                    
                    # If it returned a cleanup function, store it
                    if callable(result):
                        self._cleanup = result
                        
            finally:
                _current_observer.set(prev_observer)
                self.state = 0  # Clean
                
        finally:
            self._running = False
    
    def _notify(self) -> None:
        """Called when a source signal changes."""
        if self.disposed or self._running:
            return
        
        self.state = 2  # Dirty
        
        if is_batching():
            schedule_effect(self._run)
        else:
            self._run()
    
    def dispose(self) -> None:
        """Dispose the effect and run cleanup."""
        if self.disposed:
            return
        
        # Run cleanup
        if self._cleanup:
            try:
                self._cleanup()
            except Exception:
                pass
            self._cleanup = None
        
        super().dispose()
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    def __repr__(self) -> str:
        return f"Effect(name={self._name!r}, disposed={self.disposed})"


def createEffect(
    fn: Callable[[], Optional[Callable[[], None]]],
    options: Optional[EffectOptions] = None,
) -> Effect:
    """
    Create a new effect.
    
    SolidJS-style API.
    
    Usage:
        createEffect(lambda: print(count()))
        
        # With cleanup
        createEffect(lambda: (
            subscribe_to_events(),
            lambda: unsubscribe()
        ))
    """
    return Effect(fn, options)


def effect(
    fn: Callable[[], Optional[Callable[[], None]]],
    name: Optional[str] = None,
) -> Effect:
    """
    Create a new effect.
    
    Convenience function.
    
    Usage:
        effect(lambda: print(count()))
    """
    return Effect(fn, name=name)


class RenderEffect(Effect):
    """
    A render effect runs synchronously during rendering.
    
    Unlike regular effects which are batched, render effects
    run immediately and are used for DOM updates.
    """
    
    def _notify(self) -> None:
        """Run immediately, no batching."""
        if self.disposed or self._running:
            return
        self.state = 2
        self._run()


def createRenderEffect(
    fn: Callable[[], Optional[Callable[[], None]]],
) -> RenderEffect:
    """Create a render effect that runs synchronously."""
    return RenderEffect(fn)


class ComputationEffect(Effect):
    """
    An effect that only runs when explicitly triggered.
    
    Used for derived computations that need side effects.
    """
    
    def __init__(self, *args, **kwargs):
        kwargs["defer"] = True
        super().__init__(*args, **kwargs)
    
    def trigger(self) -> None:
        """Manually trigger the effect."""
        self._run()

