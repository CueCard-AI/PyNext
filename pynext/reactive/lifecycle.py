"""
Lifecycle - Resource Management and Async Data

This module provides:
- createResource: Async data fetching with reactive state
- Resource: Wrapper for async operations

Resources handle the common pattern of:
1. Fetch data asynchronously
2. Track loading/error/success states
3. Refetch when dependencies change
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Generic, Optional, TypeVar, Union
from dataclasses import dataclass
from enum import Enum

from pynext.reactive.signal import Signal
from pynext.reactive.effect import Effect
from pynext.reactive.context import get_current_owner, onCleanup

T = TypeVar("T")
S = TypeVar("S")


class ResourceState(Enum):
    """State of a Resource."""
    UNRESOLVED = "unresolved"
    PENDING = "pending"
    READY = "ready"
    REFRESHING = "refreshing"
    ERROR = "error"


@dataclass
class ResourceOptions:
    """Options for Resource creation."""
    name: Optional[str] = None
    initial_value: Any = None
    defer: bool = False  # Don't fetch on creation
    storage: Optional[Any] = None  # For SSR hydration


class Resource(Generic[T]):
    """
    A reactive resource for async data fetching.
    
    Resources provide reactive wrappers around async operations
    with automatic loading/error state management.
    
    Usage:
        async def fetch_user(id):
            response = await http.get(f"/api/users/{id}")
            return response.json()
        
        user = createResource(
            source=lambda: user_id(),  # Reactive dependency
            fetcher=fetch_user
        )
        
        # Access states
        if user.loading():
            return Spinner()
        if user.error():
            return ErrorMessage(user.error())
        return UserCard(user())
    """
    
    def __init__(
        self,
        fetcher: Callable[[S], T],
        source: Optional[Callable[[], S]] = None,
        options: Optional[ResourceOptions] = None,
    ):
        """
        Create a Resource.
        
        Args:
            fetcher: Async function that fetches data
            source: Optional reactive source that triggers refetch
            options: ResourceOptions for configuration
        """
        self._fetcher = fetcher
        self._source = source
        self._options = options or ResourceOptions()
        
        # State signals
        self._value: Signal[Optional[T]] = Signal(
            self._options.initial_value,
            name=f"{self._options.name or 'resource'}_value"
        )
        self._error: Signal[Optional[Exception]] = Signal(
            None,
            name=f"{self._options.name or 'resource'}_error"
        )
        self._state: Signal[ResourceState] = Signal(
            ResourceState.UNRESOLVED,
            name=f"{self._options.name or 'resource'}_state"
        )
        
        # Track current fetch for cancellation
        self._current_fetch: Optional[asyncio.Task] = None
        
        # Set up reactive refetch if source provided
        if source and not self._options.defer:
            @Effect
            def auto_fetch():
                source_value = source()
                self._fetch(source_value)
        elif not self._options.defer:
            # Fetch immediately without source
            self._fetch(None)
    
    def __call__(self) -> Optional[T]:
        """Read the resource value."""
        return self._value()
    
    def get(self) -> Optional[T]:
        """Alias for __call__."""
        return self._value()
    
    def loading(self) -> bool:
        """Check if resource is loading."""
        state = self._state()
        return state in (ResourceState.PENDING, ResourceState.REFRESHING)
    
    def error(self) -> Optional[Exception]:
        """Get the error if any."""
        return self._error()
    
    def state(self) -> ResourceState:
        """Get the current state."""
        return self._state()
    
    def latest(self) -> Optional[T]:
        """
        Get the latest value, even while refreshing.
        
        Unlike __call__, this returns the previous value during refresh
        instead of None.
        """
        return self._value.peek()
    
    def refetch(self) -> None:
        """Manually trigger a refetch."""
        source_value = self._source() if self._source else None
        self._fetch(source_value)
    
    def mutate(self, value: T) -> None:
        """
        Manually update the resource value.
        
        Useful for optimistic updates.
        """
        self._value.set(value)
        self._state.set(ResourceState.READY)
        self._error.set(None)
    
    def _fetch(self, source_value: S) -> None:
        """Internal fetch implementation."""
        # Cancel previous fetch if still running
        if self._current_fetch and not self._current_fetch.done():
            self._current_fetch.cancel()
        
        # Update state
        current_state = self._state()
        if current_state == ResourceState.READY:
            self._state.set(ResourceState.REFRESHING)
        else:
            self._state.set(ResourceState.PENDING)
        
        # Start fetch
        async def do_fetch():
            try:
                result = self._fetcher(source_value)
                
                # Handle async fetcher
                if asyncio.iscoroutine(result):
                    result = await result
                
                self._value.set(result)
                self._state.set(ResourceState.READY)
                self._error.set(None)
                
            except asyncio.CancelledError:
                pass  # Ignore cancellation
            except Exception as e:
                self._error.set(e)
                self._state.set(ResourceState.ERROR)
        
        # Run the fetch
        try:
            loop = asyncio.get_event_loop()
            self._current_fetch = loop.create_task(do_fetch())
        except RuntimeError:
            # No event loop, run synchronously
            result = self._fetcher(source_value)
            if not asyncio.iscoroutine(result):
                self._value.set(result)
                self._state.set(ResourceState.READY)


def createResource(
    fetcher: Callable[[S], T],
    source: Optional[Callable[[], S]] = None,
    options: Optional[ResourceOptions] = None,
) -> Resource[T]:
    """
    Create a reactive resource for async data.
    
    Usage:
        # Simple fetch
        data = createResource(lambda: fetch("/api/data"))
        
        # With reactive source
        user = createResource(
            source=lambda: user_id(),
            fetcher=lambda id: fetch(f"/api/users/{id}")
        )
        
        # Access data
        Show(when=lambda: not user.loading())[
            lambda: div()[user().name]
        ]
    
    Args:
        fetcher: Function that fetches data (can be async)
        source: Optional reactive source that triggers refetch
        options: Optional ResourceOptions
        
    Returns:
        Resource object with reactive state
    """
    return Resource(fetcher, source, options)


def lazy(
    fn: Callable[[], T],
) -> Callable[[], T]:
    """
    Create a lazily-loaded component.
    
    The component is only loaded when first rendered.
    
    Usage:
        HeavyComponent = lazy(lambda: import_component("./HeavyComponent"))
        
        # In template
        Suspense(fallback=Spinner())[
            HeavyComponent()
        ]
    """
    loaded: list = []
    loading = False
    
    def wrapper() -> T:
        nonlocal loading
        
        if loaded:
            return loaded[0]
        
        if not loading:
            loading = True
            result = fn()
            loaded.append(result)
        
        return loaded[0] if loaded else None  # type: ignore
    
    return wrapper

