"""
PyNext Reactive System - Fine-Grained Reactivity for Python

=============================================================================
WHAT THIS MODULE DOES
=============================================================================

This is PyNext's reactive system, inspired by SolidJS. It provides:

- **signal()**: Reactive values that notify when they change
- **effect()**: Side effects that re-run when dependencies change
- **memo()**: Cached computations (derived values)
- **store()**: Deep reactive objects (nested data structures)
- **batch()**: Coalesce multiple updates into one notification
- **untrack()**: Read values without creating dependencies

Plus control flow components for SSR:
- **Show**: Conditional rendering
- **For**: List rendering with reconciliation
- **Switch/Match**: Multi-branch conditionals

=============================================================================
WHY THIS EXISTS
=============================================================================

This replaces both:
- `pynext.core.signals` (old SSR-focused signals)
- Previous `pynext.reactive` (over-engineered SolidJS-like system)

With ONE unified system that:
- Works for SSR (server-side rendering)
- Compiles to JavaScript (Phase 17.4)
- Matches the JS runtime API exactly
- Is simple and AI-friendly

=============================================================================
QUICK START
=============================================================================

    from pynext.reactive import signal, effect, memo, store
    
    # Signal - reactive value
    count = signal(0)
    print(count())      # 0
    count.set(5)        # Notifies subscribers
    print(count())      # 5
    
    # Effect - reactive side effect
    @effect
    def log():
        print(f"Count: {count()}")  # Auto-tracks count
    
    count.set(10)  # Prints: "Count: 10"
    
    # Memo - cached computation
    doubled = memo(lambda: count() * 2)
    print(doubled())  # 20
    
    # Store - deep reactive object
    todos = store({"items": [], "filter": "all"})
    todos["items"].append({"text": "New"})  # Reactive!

=============================================================================
MIGRATION FROM OLD IMPORTS
=============================================================================

    # OLD (deprecated):
    from pynext.core.signals import Signal, Effect, Computed, Store, batch
    
    # NEW:
    from pynext.reactive import signal, effect, memo, store, batch

The new API uses lowercase factory functions (signal, effect, memo, store)
instead of uppercase classes. Classes are still available for type hints.

=============================================================================
"""

from __future__ import annotations

# =============================================================================
# CORE PRIMITIVES
# =============================================================================

# Context system (internal, but some advanced users need these)
from pynext.reactive.context import (
    batch,
    untrack,
    get_observer,
    set_observer,
    is_batching,
    schedule_effect,
)

# Signal - reactive value container
from pynext.reactive.signal import (
    Signal,
    signal,
    createSignal,
)

# Effect - reactive side effects
from pynext.reactive.effect import (
    Effect,
    effect,
    createEffect,
)

# Memo - cached computations
from pynext.reactive.memo import (
    Memo,
    memo,
    computed,
    createMemo,
    Computed,  # Alias for Memo
)

# Store - deep reactive objects
from pynext.reactive.store import (
    Store,
    store,
    createStore,
)

# =============================================================================
# HYDRATION
# =============================================================================

from pynext.reactive.hydration import (
    ComponentState,
    HydrationState,
    hydration_attrs,
    text_binding,
    click_handler,
    event_handler,
    next_component_id,
    reset_component_ids,
)

# =============================================================================
# CONTROL FLOW (will be updated in next step)
# =============================================================================

# Import control flow components if they exist
try:
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
except ImportError:
    # Control flow not yet rewritten - will be added
    pass

# =============================================================================
# FORMS
# =============================================================================

from pynext.reactive.forms import (
    FormState,
    FormErrors,
    create_form,
)

from pynext.reactive.validators import (
    required,
    min_length,
    max_length,
    email,
    pattern,
    min_value,
    max_value,
    one_of,
    url,
    integer,
    number,
    equals,
    length,
    compose,
    when,
    run_validators,
    ValidatorFn,
)

# =============================================================================
# ROUTER
# =============================================================================

from pynext.reactive.router import (
    Router,
    Route,
    Link,
    Outlet,
    useNavigate,
    useParams,
    useSearchParams,
    useLocation,
    useMatch,
    Navigator,
    Location,
    Redirect,
    createRouteGuard,
)

# =============================================================================
# LEGACY ALIASES (for backwards compatibility)
# =============================================================================

# Some code uses these directly
def createRoot(fn):
    """Create a reactive root (for cleanup)."""
    return fn()


def onCleanup(fn):
    """Register a cleanup function (placeholder)."""
    pass


def onMount(fn):
    """Register a mount callback (placeholder)."""
    fn()


def onError(fn):
    """Register an error handler (placeholder)."""
    pass


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Core primitives
    "Signal",
    "signal",
    "createSignal",
    "Effect", 
    "effect",
    "createEffect",
    "Memo",
    "memo",
    "computed",
    "createMemo",
    "Computed",
    "Store",
    "store",
    "createStore",
    
    # Batching & tracking
    "batch",
    "untrack",
    
    # Hydration
    "ComponentState",
    "HydrationState",
    "hydration_attrs",
    "text_binding",
    "click_handler",
    "event_handler",
    "next_component_id",
    "reset_component_ids",
    
    # Control flow (when available)
    "Show",
    "For",
    "Index",
    "Switch",
    "Match",
    "Portal",
    "Dynamic",
    "ErrorBoundary",
    "Suspense",
    
    # Legacy aliases
    "createRoot",
    "onCleanup",
    "onMount",
    "onError",
    
    # Forms
    "FormState",
    "FormErrors",
    "create_form",
    
    # Validators
    "required",
    "min_length",
    "max_length",
    "email",
    "pattern",
    "min_value",
    "max_value",
    "one_of",
    "url",
    "integer",
    "number",
    "equals",
    "length",
    "compose",
    "when",
    "run_validators",
    "ValidatorFn",
    
    # Router
    "Router",
    "Route",
    "Link",
    "Outlet",
    "useNavigate",
    "useParams",
    "useSearchParams",
    "useLocation",
    "useMatch",
    "Navigator",
    "Location",
    "Redirect",
    "createRouteGuard",
]
