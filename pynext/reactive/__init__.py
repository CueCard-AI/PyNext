"""
PyNext Reactive System - SolidJS-Like Fine-Grained Reactivity

This module provides production-grade reactive primitives with build-time compilation
support for achieving SolidJS-level performance.

Core Primitives:
- Signal: Reactive value container with automatic dependency tracking
- Effect: Side effects that auto-track and re-run on dependency changes
- Memo: Memoized computed values with lazy evaluation
- Store: Deep reactive objects with proxy-based tracking
- Batch: Update coalescing for performance

Control Flow (DOM Primitives):
- Show: Conditional rendering
- For: Keyed list reconciliation
- Switch/Match: Multi-branch conditionals
- Portal: Render outside component tree
- ErrorBoundary: Error catching and recovery

Lifecycle:
- onMount: Run after DOM insertion
- onCleanup: Cleanup on unmount
- createContext/useContext: Dependency injection

Usage:
    from pynext.reactive import Signal, Effect, Memo, Store, Show, For
    
    count = Signal(0)
    doubled = Memo(lambda: count() * 2)
    
    @Effect
    def log_changes():
        print(f"Count: {count()}, Doubled: {doubled()}")
    
    count.set(5)  # Triggers effect
"""

from __future__ import annotations

# Core Reactive Primitives
from pynext.reactive.signal import (
    Signal,
    signal,
    createSignal,
)

from pynext.reactive.effect import (
    Effect,
    effect,
    createEffect,
)

from pynext.reactive.memo import (
    Memo,
    Computed,
    memo,
    computed,
    createMemo,
)

from pynext.reactive.store import (
    Store,
    store,
    createStore,
    produce,
    reconcile,
)

from pynext.reactive.batch import (
    batch,
    untrack,
    createRoot,
)

from pynext.reactive.context import (
    Owner,
    getOwner,
    runWithOwner,
    onCleanup,
    onMount,
    onError,
)

# Control Flow Components (DOM Primitives)
from pynext.reactive.control_flow import (
    Show,
    For,
    Index,
    Switch,
    Match,
    Portal,
    Dynamic,
    ErrorBoundary,
    Suspense,
)

# Context API
from pynext.reactive.context_api import (
    createContext,
    useContext,
    Context,
)

# Lifecycle Hooks
from pynext.reactive.lifecycle import (
    createResource,
    Resource,
)

# Refs
from pynext.reactive.refs import (
    createRef,
    Ref,
)

__all__ = [
    # Core Primitives
    "Signal",
    "signal",
    "createSignal",
    "Effect",
    "effect", 
    "createEffect",
    "Memo",
    "Computed",
    "memo",
    "computed",
    "createMemo",
    "Store",
    "store",
    "createStore",
    "produce",
    "reconcile",
    
    # Batching & Ownership
    "batch",
    "untrack",
    "createRoot",
    "Owner",
    "getOwner",
    "runWithOwner",
    "onCleanup",
    "onMount",
    "onError",
    
    # Control Flow
    "Show",
    "For",
    "Index",
    "Switch",
    "Match",
    "Portal",
    "Dynamic",
    "ErrorBoundary",
    "Suspense",
    
    # Context
    "createContext",
    "useContext",
    "Context",
    
    # Resources
    "createResource",
    "Resource",
    
    # Refs
    "createRef",
    "Ref",
]

