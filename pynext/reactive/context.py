"""
PyNext Reactive Context - The Foundation Layer

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This file manages GLOBAL STATE for the reactive system:

- Who is currently reading signals? (_current_observer)
- Are we in a batch? (_batch_depth)
- What effects are pending? (_pending_effects)

Without this, signals wouldn't know who to notify.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Automatic dependency tracking needs to know "who's asking":

    @effect
    def my_effect():
        print(count())  # How does count() know my_effect reads it?
        
Answer: When my_effect runs, we set _current_observer = my_effect.
Then count() checks _current_observer and adds it to subscribers.

This is the key insight from SolidJS that makes fine-grained reactivity work.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    ┌────────────────────────────────────────────────────────────────┐
    │  Global State (Thread-Local via ContextVar)                     │
    │                                                                 │
    │  _current_observer = None  ──► Who is currently executing?     │
    │  _batch_depth = 0          ──► Nested batch() call count       │
    │  _pending_effects = set()  ──► Effects waiting for batch end   │
    │                                                                 │
    │  Effect runs:                                                   │
    │  1. prev = _current_observer                                    │
    │  2. _current_observer = effect                                  │
    │  3. effect.fn() executes                                        │
    │  4. signal() sees _current_observer, subscribes effect          │
    │  5. _current_observer = prev                                    │
    │                                                                 │
    │  Batch runs:                                                    │
    │  1. _batch_depth += 1                                           │
    │  2. User code runs, signals queue effects in _pending_effects   │
    │  3. _batch_depth -= 1                                           │
    │  4. If _batch_depth == 0: flush _pending_effects                │
    └────────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

1. signal.py - Checks get_observer() to know who to subscribe
2. effect.py - Calls set_observer() before running user function
3. memo.py - Same as effect (memos are computations)
4. batch.py - Uses batch() and schedule_effect()

=============================================================================
WHEN TO USE
=============================================================================

Most users never touch this directly. It's internal plumbing.

Use batch() when updating multiple signals and you want one notification.
Use untrack() when reading a signal without creating a dependency.

=============================================================================
COMPILATION (Phase 17.4)
=============================================================================

This file has no direct compilation output - it's Python-side only.
The JS runtime has equivalent globals in reactive.js:
    
    let currentObserver = null;
    let batchDepth = 0;
    const pendingEffects = new Set();

=============================================================================
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Callable, Optional, Set

if TYPE_CHECKING:
    from pynext.reactive.effect import Effect


# =============================================================================
# GLOBAL STATE (Thread-safe via ContextVar)
# =============================================================================
#
# ContextVar ensures each thread/async task has its own state.
# This is crucial for SSR where multiple requests run concurrently.
# =============================================================================

_current_observer: ContextVar[Optional["Effect"]] = ContextVar(
    "_current_observer", 
    default=None
)
"""The effect/memo currently running. Signals check this to subscribe."""

_batch_depth: ContextVar[int] = ContextVar(
    "_batch_depth", 
    default=0
)
"""Nested batch() call count. When > 0, effects queue instead of run."""

_pending_effects: ContextVar[Set["Effect"]] = ContextVar(
    "_pending_effects", 
    default=None  # Will be initialized to set() on first use
)
"""Effects waiting to run after batch completes."""


def _get_pending() -> Set["Effect"]:
    """Get or create the pending effects set."""
    pending = _pending_effects.get()
    if pending is None:
        pending = set()
        _pending_effects.set(pending)
    return pending


# =============================================================================
# OBSERVER TRACKING
# =============================================================================

def get_observer() -> Optional["Effect"]:
    """
    Get the currently executing effect (for dependency tracking).
    
    Returns None if not inside an effect.
    Signals call this to know who to subscribe.
    """
    return _current_observer.get()


def set_observer(effect: Optional["Effect"]) -> Optional["Effect"]:
    """
    Set the current observer and return the previous one.
    
    Called by Effect.execute() before running user function.
    Returns previous observer so it can be restored after.
    """
    prev = _current_observer.get()
    _current_observer.set(effect)
    return prev


# =============================================================================
# BATCHING
# =============================================================================

def is_batching() -> bool:
    """
    Are we inside a batch() call?
    
    When True, effects queue in _pending_effects instead of running.
    """
    return _batch_depth.get() > 0


def schedule_effect(effect_or_fn) -> None:
    """
    Schedule an effect to run.
    
    If batching: add to pending queue
    If not batching: run immediately
    
    Accepts either an Effect object or a plain function.
    """
    if is_batching():
        _get_pending().add(effect_or_fn)
    else:
        if hasattr(effect_or_fn, 'execute'):
            effect_or_fn.execute()
        elif callable(effect_or_fn):
            effect_or_fn()


def batch(fn: Callable[[], Any]) -> Any:
    """
    Batch multiple updates into one notification cycle.
    
    All signal updates inside the batch are collected.
    Effects only run once after ALL updates complete.
    
    Example:
        def update_both():
            count.set(1)
            name.set("Alice")
        
        batch(update_both)
        # Effects run once after both updates, not twice
    
    Can be nested - effects only flush after outermost batch.
    """
    depth = _batch_depth.get()
    _batch_depth.set(depth + 1)
    
    try:
        result = fn()
    finally:
        _batch_depth.set(depth)
        
        # Only flush on outermost batch exit
        if depth == 0:
            _flush_pending()
    
    return result


def _flush_pending() -> None:
    """Flush all pending effects after batch completes."""
    pending = _get_pending()
    
    # Copy and clear to handle effects that schedule more effects
    while pending:
        effects = list(pending)
        pending.clear()
        
        for effect in effects:
            if hasattr(effect, 'execute'):
                effect.execute()
            elif callable(effect):
                effect()


# =============================================================================
# UNTRACKING
# =============================================================================

def untrack(fn: Callable[[], Any]) -> Any:
    """
    Execute fn without tracking dependencies.
    
    Signals read inside fn will NOT subscribe the current effect.
    
    Example:
        @effect
        def my_effect():
            tracked = count()  # This IS tracked
            untracked = untrack(lambda: other())  # NOT tracked
    
    Use when you need a signal's value but don't want re-runs.
    """
    prev = set_observer(None)
    try:
        return fn()
    finally:
        set_observer(prev)


# =============================================================================
# OWNER AND COMPUTATION (for backward compatibility)
# =============================================================================

class Owner:
    """
    Represents a reactive scope with cleanup.
    
    For backward compatibility with tests that expect Owner class.
    """
    
    __slots__ = ("_children", "_cleanups", "_disposed")
    
    def __init__(self):
        self._children: list = []
        self._cleanups: list = []
        self._disposed = False
    
    def dispose(self) -> None:
        """Dispose this owner and all children."""
        if self._disposed:
            return
        self._disposed = True
        
        for cleanup in reversed(self._cleanups):
            try:
                cleanup()
            except Exception:
                pass
        
        for child in reversed(self._children):
            child.dispose()


class Computation:
    """
    Base class for Effect and Memo.
    
    For backward compatibility with tests.
    """
    
    __slots__ = ("_fn", "_disposed")
    
    def __init__(self, fn):
        self._fn = fn
        self._disposed = False
    
    def execute(self) -> None:
        if not self._disposed:
            self._fn()
    
    def dispose(self) -> None:
        self._disposed = True


# Owner context variable
_current_owner: ContextVar[Optional[Owner]] = ContextVar(
    "_current_owner",
    default=None
)


def get_current_owner() -> Optional[Owner]:
    """Get the current owner scope."""
    return _current_owner.get()


def get_current_observer():
    """Alias for get_observer()."""
    return get_observer()


def flush_updates() -> None:
    """Flush any pending updates immediately."""
    _flush_pending()


# =============================================================================
# LIFECYCLE HOOKS (for backward compatibility)
# =============================================================================

def onMount(fn: Callable[[], None]) -> None:
    """
    Register a callback to run after component mounts.
    
    Currently runs immediately (SSR).
    """
    fn()


def onCleanup(fn: Callable[[], None]) -> None:
    """
    Register a cleanup function.
    
    Currently a no-op (SSR doesn't need cleanup).
    """
    owner = _current_owner.get()
    if owner:
        owner._cleanups.append(fn)


def onError(fn: Callable[[Exception], None]) -> None:
    """
    Register an error handler.
    
    Currently a no-op.
    """
    pass


def runWithOwner(owner: Owner, fn: Callable[[], Any]) -> Any:
    """Run function within an owner context."""
    prev = _current_owner.get()
    _current_owner.set(owner)
    try:
        return fn()
    finally:
        _current_owner.set(prev)


def getOwner() -> Optional[Owner]:
    """Get the current owner."""
    return _current_owner.get()


# Alias for SolidJS-style API
def createRoot(fn: Callable) -> Any:
    """Create a reactive root."""
    owner = Owner()
    prev = _current_owner.get()
    _current_owner.set(owner)
    try:
        return fn(owner.dispose)
    finally:
        _current_owner.set(prev)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Core
    "get_observer",
    "set_observer", 
    "is_batching",
    "schedule_effect",
    "batch",
    "untrack",
    
    # Owner/Computation
    "Owner",
    "Computation",
    "get_current_owner",
    "get_current_observer",
    "flush_updates",
    "_current_owner",
    "_current_observer",
    "_batch_depth",
    "_pending_effects",
    
    # Lifecycle
    "onMount",
    "onCleanup",
    "onError",
    "runWithOwner",
    "getOwner",
    "createRoot",
]
