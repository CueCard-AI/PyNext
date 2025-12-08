"""
Reactive Context - Ownership and Dependency Tracking

This module provides the core infrastructure for reactive tracking:
- Owner: Manages cleanup and nested reactive scopes
- Observer: Tracks which signals are read during computation
- Batching: Coalesces multiple updates into single notification round

The context system enables:
1. Automatic dependency tracking (no explicit dependency arrays)
2. Proper cleanup when components unmount
3. Glitch-free updates through topological sorting
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional, List, Set, TypeVar
from contextvars import ContextVar
from dataclasses import dataclass, field
from weakref import ref, WeakSet
import heapq

T = TypeVar("T")


# =============================================================================
# Context Variables (Thread-Local State)
# =============================================================================

_current_owner: ContextVar[Optional["Owner"]] = ContextVar("current_owner", default=None)
_current_observer: ContextVar[Optional["Computation"]] = ContextVar("current_observer", default=None)
_batch_depth: ContextVar[int] = ContextVar("batch_depth", default=0)
_pending_effects: ContextVar[List[Callable]] = ContextVar("pending_effects", default=None)
_transaction_depth: ContextVar[int] = ContextVar("transaction_depth", default=0)


def get_current_owner() -> Optional["Owner"]:
    """Get the current reactive owner (scope)."""
    return _current_owner.get()


def get_current_observer() -> Optional["Computation"]:
    """Get the current tracking computation (effect/memo)."""
    return _current_observer.get()


def is_batching() -> bool:
    """Check if we're inside a batch."""
    return _batch_depth.get() > 0


def schedule_effect(fn: Callable) -> None:
    """Schedule an effect to run after current batch completes."""
    pending = _pending_effects.get()
    if pending is None:
        pending = []
        _pending_effects.set(pending)
    pending.append(fn)


# =============================================================================
# Owner - Reactive Scope Management
# =============================================================================

@dataclass
class Owner:
    """
    A reactive owner manages a scope of computations and their cleanup.
    
    Owners form a tree structure that mirrors the component tree.
    When an owner is disposed, all its children and their cleanups are run.
    """
    parent: Optional["Owner"] = None
    children: List["Owner"] = field(default_factory=list)
    cleanups: List[Callable[[], None]] = field(default_factory=list)
    computations: List["Computation"] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    disposed: bool = False
    
    def __post_init__(self):
        if self.parent:
            self.parent.children.append(self)
    
    def dispose(self) -> None:
        """Dispose this owner and all children."""
        if self.disposed:
            return
        
        self.disposed = True
        
        # Dispose children first (reverse order)
        for child in reversed(self.children):
            child.dispose()
        self.children.clear()
        
        # Run cleanups (reverse order)
        for cleanup in reversed(self.cleanups):
            try:
                cleanup()
            except Exception:
                pass  # Don't let cleanup errors stop other cleanups
        self.cleanups.clear()
        
        # Dispose computations
        for computation in self.computations:
            computation.dispose()
        self.computations.clear()
        
        # Remove from parent
        if self.parent:
            try:
                self.parent.children.remove(self)
            except ValueError:
                pass
    
    def add_cleanup(self, fn: Callable[[], None]) -> None:
        """Register a cleanup function."""
        self.cleanups.append(fn)
    
    def add_computation(self, computation: "Computation") -> None:
        """Register a computation with this owner."""
        self.computations.append(computation)


def createRoot(fn: Callable[[Callable[[], None]], T]) -> T:
    """
    Create a new reactive root with manual disposal.
    
    Usage:
        dispose = createRoot(dispose_fn => {
            # Create reactive stuff here
            # Call dispose_fn() when done
        })
    """
    owner = Owner(parent=get_current_owner())
    
    prev_owner = _current_owner.get()
    _current_owner.set(owner)
    
    try:
        return fn(owner.dispose)
    finally:
        _current_owner.set(prev_owner)


def runWithOwner(owner: Optional[Owner], fn: Callable[[], T]) -> T:
    """Run a function with a specific owner."""
    prev = _current_owner.get()
    _current_owner.set(owner)
    try:
        return fn()
    finally:
        _current_owner.set(prev)


def getOwner() -> Optional[Owner]:
    """Get the current owner."""
    return get_current_owner()


# =============================================================================
# Computation - Base for Effects and Memos
# =============================================================================

@dataclass
class Computation:
    """
    Base class for reactive computations (Effects, Memos).
    
    A computation:
    1. Tracks which signals it reads (sources)
    2. Re-runs when any source changes
    3. Can be disposed to stop tracking
    """
    fn: Optional[Callable] = None
    owner: Optional[Owner] = None
    sources: Set[Any] = field(default_factory=set)  # Signals this computation depends on
    observers: WeakSet[Any] = field(default_factory=WeakSet)  # Computations that depend on this
    state: int = 0  # 0=clean, 1=check, 2=dirty
    pure: bool = False  # True for memos, False for effects
    disposed: bool = False
    
    def __post_init__(self):
        if self.owner:
            self.owner.add_computation(self)
    
    def _add_source(self, source: Any) -> None:
        """Add a signal as a source (dependency)."""
        self.sources.add(source)
    
    def _clear_sources(self) -> None:
        """Clear all source dependencies."""
        for source in self.sources:
            if hasattr(source, "_unsubscribe"):
                source._unsubscribe(self)
        self.sources.clear()
    
    def _notify(self) -> None:
        """Called when a source changes."""
        if self.disposed:
            return
        
        self.state = 2  # Mark dirty
        
        if is_batching():
            schedule_effect(self._run)
        else:
            self._run()
    
    def _run(self) -> Any:
        """Run the computation."""
        raise NotImplementedError
    
    def dispose(self) -> None:
        """Dispose this computation."""
        if self.disposed:
            return
        
        self.disposed = True
        self._clear_sources()
        self.fn = None


# =============================================================================
# Lifecycle Hooks
# =============================================================================

def onMount(fn: Callable[[], Optional[Callable[[], None]]]) -> None:
    """
    Run a function after the component mounts.
    
    If the function returns a cleanup function, it will be called on unmount.
    
    Usage:
        @component
        def MyComponent():
            onMount(lambda: print("Mounted!"))
            
            # With cleanup
            def setup():
                timer = setInterval(tick, 1000)
                return lambda: clearInterval(timer)
            
            onMount(setup)
    """
    owner = get_current_owner()
    if owner is None:
        # No owner, run immediately
        result = fn()
        return
    
    # Schedule to run after render
    def run_mount():
        result = fn()
        if callable(result):
            owner.add_cleanup(result)
    
    # In browser, this would be scheduled via queueMicrotask
    # For now, run immediately (will be handled by compiler)
    run_mount()


def onCleanup(fn: Callable[[], None]) -> None:
    """
    Register a cleanup function to run when the owner is disposed.
    
    Usage:
        @component
        def MyComponent():
            connection = connect()
            onCleanup(lambda: connection.close())
    """
    owner = get_current_owner()
    if owner:
        owner.add_cleanup(fn)


def onError(fn: Callable[[Exception], None]) -> None:
    """
    Register an error handler for the current scope.
    
    Usage:
        @component  
        def MyComponent():
            onError(lambda e: print(f"Error: {e}"))
    """
    owner = get_current_owner()
    if owner:
        # Store in context for error boundaries to use
        owner.context["error_handler"] = fn


# =============================================================================
# Update Scheduling
# =============================================================================

class UpdateQueue:
    """
    Priority queue for scheduling updates.
    
    Effects are sorted by their depth in the computation graph
    to ensure parents update before children (glitch-free updates).
    """
    
    def __init__(self):
        self._queue: List[tuple[int, int, Callable]] = []
        self._counter = 0
        self._processing = False
    
    def add(self, priority: int, fn: Callable) -> None:
        """Add a function to the queue with priority."""
        heapq.heappush(self._queue, (priority, self._counter, fn))
        self._counter += 1
    
    def flush(self) -> None:
        """Process all queued updates."""
        if self._processing:
            return
        
        self._processing = True
        try:
            while self._queue:
                _, _, fn = heapq.heappop(self._queue)
                try:
                    fn()
                except Exception as e:
                    # Log but don't stop processing
                    print(f"Error in update: {e}")
        finally:
            self._processing = False


_update_queue = UpdateQueue()


def flush_updates() -> None:
    """Flush all pending updates."""
    _update_queue.flush()
    
    # Also process pending effects
    pending = _pending_effects.get()
    if pending:
        _pending_effects.set([])
        for fn in pending:
            try:
                fn()
            except Exception as e:
                print(f"Error in effect: {e}")

