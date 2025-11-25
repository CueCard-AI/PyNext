"""
Resource primitive for async data fetching.

Inspired by SolidJS's createResource, this provides a reactive primitive
for handling async operations with automatic loading, error, and data states.

Usage:
    # Simple resource
    users = Resource(fetch_users)
    
    # Resource with reactive source
    user = Resource(fetch_user, source=user_id)  # Refetches when user_id changes
    
    # Access states
    if user.loading():
        return Loading()
    if user.error():
        return Error(user.error())
    return UserProfile(user())

Features:
    - Automatic loading/error/data state management
    - Reactive source parameter (refetch on change)
    - Server-side resolution with hydration
    - Client-side refetch and mutation
    - Deduplication of concurrent requests
    - Cache support with TTL
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
    overload,
)

from pynext.core.signals import Signal, Computed


T = TypeVar("T")
S = TypeVar("S")  # Source type


class ResourceState(Enum):
    """Resource fetch states."""
    UNRESOLVED = "unresolved"
    PENDING = "pending"
    READY = "ready"
    REFRESHING = "refreshing"
    ERRORED = "errored"


@dataclass
class ResourceInfo:
    """Information about a resource for serialization."""
    id: str
    state: ResourceState
    data: Any = None
    error: Optional[str] = None
    source: Any = None
    fetched_at: Optional[float] = None


class Resource(Generic[T, S]):
    """
    A reactive primitive for async data fetching.
    
    Similar to SolidJS's createResource, but for Python.
    
    Args:
        fetcher: Async function that fetches the data
        source: Optional reactive source. When source changes, resource refetches.
        initial_value: Optional initial value before first fetch
        name: Optional name for debugging
        cache_ttl: Optional cache TTL in seconds
    
    Example:
        # Simple usage
        users = Resource(fetch_all_users)
        
        # With reactive source (refetches when user_id changes)
        user_id = Signal(1)
        user = Resource(lambda id: fetch_user(id), source=user_id)
        
        # Access states
        user.loading()  # True while fetching
        user.error()    # Exception if errored
        user()          # The data (or None if not ready)
        user.latest     # Last successful data (even during refresh)
    """
    
    def __init__(
        self,
        fetcher: Callable[[S], Awaitable[T]] | Callable[[], Awaitable[T]],
        source: Optional[Signal[S] | Callable[[], S]] = None,
        initial_value: Optional[T] = None,
        name: Optional[str] = None,
        cache_ttl: Optional[float] = None,
    ):
        self._id = f"resource_{uuid.uuid4().hex[:8]}"
        self._name = name or self._id
        self._fetcher = fetcher
        self._source = source
        self._cache_ttl = cache_ttl
        
        # Internal state signals
        self._state = Signal(ResourceState.UNRESOLVED, name=f"{self._name}_state")
        self._data = Signal(initial_value, name=f"{self._name}_data")
        self._error_signal = Signal(None, name=f"{self._name}_error")
        self._latest = initial_value  # Last successful value (non-reactive for perf)
        
        # Fetch tracking
        self._fetch_count = 0
        self._last_fetch_id = 0
        self._fetched_at: Optional[float] = None
        self._current_source_value: Any = None
        
        # Pending fetch task
        self._pending_task: Optional[asyncio.Task] = None
    
    # =========================================================================
    # Core API
    # =========================================================================
    
    def __call__(self) -> Optional[T]:
        """
        Get the current data value.
        
        Returns None if not yet resolved or if errored.
        To distinguish, check .loading() or .error().
        """
        return self._data()
    
    @property
    def loading(self) -> Signal[bool]:
        """Signal that is True while the resource is fetching."""
        return Computed(
            lambda: self._state() in (ResourceState.PENDING, ResourceState.REFRESHING),
            name=f"{self._name}_loading"
        )
    
    @property
    def error(self) -> Signal[Optional[Exception]]:
        """Signal containing the error if fetch failed."""
        return self._error_signal
    
    @property
    def state(self) -> Signal[ResourceState]:
        """Signal containing the current resource state."""
        return self._state
    
    @property
    def latest(self) -> Optional[T]:
        """
        The last successfully fetched value.
        
        Unlike __call__, this doesn't change during a refresh.
        Useful for showing stale data while refreshing.
        """
        return self._latest
    
    # =========================================================================
    # Fetch Operations
    # =========================================================================
    
    async def fetch(self, refetch: bool = False) -> T:
        """
        Fetch the resource data.
        
        Args:
            refetch: If True, always refetch even if cached
        
        Returns:
            The fetched data
        
        Raises:
            Exception: If the fetch fails
        """
        # Get source value
        source_value = self._get_source_value()
        
        # Check cache
        if not refetch and self._is_cached(source_value):
            return self._data()
        
        # Track this fetch
        self._fetch_count += 1
        fetch_id = self._fetch_count
        self._last_fetch_id = fetch_id
        self._current_source_value = source_value
        
        # Update state
        if self._state() == ResourceState.READY:
            self._state.set(ResourceState.REFRESHING)
        else:
            self._state.set(ResourceState.PENDING)
        
        self._error_signal.set(None)
        
        try:
            # Call fetcher
            if source_value is not None:
                result = await self._fetcher(source_value)
            else:
                result = await self._fetcher()
            
            # Only update if this is still the latest fetch
            if fetch_id == self._last_fetch_id:
                self._data.set(result)
                self._latest = result
                self._state.set(ResourceState.READY)
                self._fetched_at = time.time()
            
            return result
            
        except Exception as e:
            # Only update if this is still the latest fetch
            if fetch_id == self._last_fetch_id:
                self._error_signal.set(e)
                self._state.set(ResourceState.ERRORED)
            raise
    
    async def refetch(self) -> T:
        """Force a refetch, ignoring cache."""
        return await self.fetch(refetch=True)
    
    async def mutate(self, value: T) -> T:
        """
        Optimistically update the resource value.
        
        Useful for optimistic updates before server confirmation.
        """
        self._data.set(value)
        self._latest = value
        self._state.set(ResourceState.READY)
        return value
    
    def invalidate(self) -> None:
        """
        Mark the resource as stale.
        
        Next access will trigger a refetch.
        """
        self._fetched_at = None
        self._state.set(ResourceState.UNRESOLVED)
    
    # =========================================================================
    # Internal Helpers
    # =========================================================================
    
    def _get_source_value(self) -> Any:
        """Get the current source value."""
        if self._source is None:
            return None
        if callable(self._source) and not isinstance(self._source, Signal):
            return self._source()
        if isinstance(self._source, Signal):
            return self._source()
        return self._source
    
    def _is_cached(self, source_value: Any) -> bool:
        """Check if we have valid cached data."""
        if self._state() not in (ResourceState.READY, ResourceState.REFRESHING):
            return False
        
        # Source changed
        if source_value != self._current_source_value:
            return False
        
        # Check TTL
        if self._cache_ttl and self._fetched_at:
            age = time.time() - self._fetched_at
            if age > self._cache_ttl:
                return False
        
        return True
    
    # =========================================================================
    # Serialization for Hydration
    # =========================================================================
    
    def get_info(self) -> ResourceInfo:
        """Get resource info for serialization."""
        error_str = None
        if self._error_signal():
            error_str = str(self._error_signal())
        
        return ResourceInfo(
            id=self._id,
            state=self._state(),
            data=self._data(),
            error=error_str,
            source=self._current_source_value,
            fetched_at=self._fetched_at,
        )
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        import json as json_module
        
        info = self.get_info()
        
        # Serialize data safely
        try:
            import orjson
            data_json = orjson.dumps(info.data).decode() if info.data is not None else "null"
        except:
            data_json = json_module.dumps(info.data) if info.data is not None else "null"
        
        error_json = json_module.dumps(info.error)
        
        return f"""__pynext__.createResource("{self._id}", {{
  state: "{info.state.value}",
  data: {data_json},
  error: {error_json},
  fetchedAt: {info.fetched_at or "null"}
}});"""
    
    def __repr__(self) -> str:
        return f"Resource({self._name}, state={self._state().value})"


# =============================================================================
# Resource Factory Functions
# =============================================================================

def create_resource(
    fetcher: Callable[[S], Awaitable[T]] | Callable[[], Awaitable[T]],
    source: Optional[Signal[S] | Callable[[], S]] = None,
    initial_value: Optional[T] = None,
    name: Optional[str] = None,
) -> Resource[T, S]:
    """
    Create a new Resource for async data fetching.
    
    This is the primary way to create resources, similar to SolidJS's createResource.
    
    Args:
        fetcher: Async function that fetches data
        source: Optional reactive source that triggers refetch when changed
        initial_value: Optional initial value before first fetch
        name: Optional name for debugging
    
    Returns:
        A new Resource instance
    
    Example:
        # Simple resource
        users = create_resource(fetch_users)
        
        # With source
        user_id = Signal(1)
        user = create_resource(fetch_user, source=user_id)
    """
    return Resource(
        fetcher=fetcher,
        source=source,
        initial_value=initial_value,
        name=name,
    )


# =============================================================================
# Resource Registry for Hydration
# =============================================================================

class ResourceRegistry:
    """
    Registry for tracking resources during SSR.
    
    Used to:
    - Track all resources that need to be resolved before sending response
    - Serialize resource state for hydration
    - Support streaming as resources resolve
    """
    
    _instance: Optional["ResourceRegistry"] = None
    
    def __new__(cls) -> "ResourceRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._resources = {}
            cls._instance._pending = set()
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._resources: dict[str, Resource] = {}
            self._pending: set[str] = set()
            self._initialized = True
    
    def register(self, resource: Resource) -> None:
        """Register a resource."""
        self._resources[resource._id] = resource
    
    def unregister(self, resource_id: str) -> None:
        """Unregister a resource."""
        self._resources.pop(resource_id, None)
        self._pending.discard(resource_id)
    
    def mark_pending(self, resource_id: str) -> None:
        """Mark a resource as pending fetch."""
        self._pending.add(resource_id)
    
    def mark_resolved(self, resource_id: str) -> None:
        """Mark a resource as resolved."""
        self._pending.discard(resource_id)
    
    def has_pending(self) -> bool:
        """Check if any resources are pending."""
        return len(self._pending) > 0
    
    async def wait_all(self, timeout: Optional[float] = None) -> None:
        """Wait for all pending resources to resolve."""
        if not self._pending:
            return
        
        pending_resources = [
            self._resources[rid] 
            for rid in self._pending 
            if rid in self._resources
        ]
        
        if not pending_resources:
            return
        
        tasks = [r.fetch() for r in pending_resources]
        
        if timeout:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
        else:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_hydration_data(self) -> dict:
        """Get all resource data for hydration."""
        return {
            rid: resource.get_info().__dict__
            for rid, resource in self._resources.items()
        }
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization for all resources."""
        inits = [r.get_js_init() for r in self._resources.values()]
        return "\n".join(inits)
    
    def clear(self) -> None:
        """Clear all resources (for testing)."""
        self._resources.clear()
        self._pending.clear()


def get_resource_registry() -> ResourceRegistry:
    """Get the global resource registry."""
    return ResourceRegistry()


# =============================================================================
# Utility Functions
# =============================================================================

async def suspend_until_ready(*resources: Resource) -> None:
    """
    Wait until all resources are ready.
    
    Used by Suspense to know when to show content vs fallback.
    
    Args:
        resources: Resources to wait for
    
    Raises:
        Exception: If any resource fails
    """
    tasks = []
    
    for resource in resources:
        if resource.state() in (ResourceState.UNRESOLVED, ResourceState.PENDING):
            tasks.append(resource.fetch())
    
    if tasks:
        await asyncio.gather(*tasks)


def is_pending(*resources: Resource) -> bool:
    """Check if any resources are pending."""
    return any(
        r.state() in (ResourceState.UNRESOLVED, ResourceState.PENDING)
        for r in resources
    )

