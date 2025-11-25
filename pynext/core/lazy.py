"""
Lazy Loading & Code Splitting for PyNext.

Enables dynamic component loading to reduce initial bundle size:
- Load components only when needed
- Route-based code splitting
- Prefetching for instant navigation
- Integration with Suspense for loading states

Example:
    # Define a lazy component
    HeavyChart = lazy(lambda: import_component("components.chart"))
    
    # Use with Suspense for loading states
    @page
    def Dashboard():
        return Suspense(fallback=ChartSkeleton())[
            HeavyChart(data=chart_data)
        ]
    
    # Or use lazy route loading
    @lazy_route("/analytics")
    def AnalyticsPage():
        return import_component("pages.analytics")
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from pynext.core.html import Element


T = TypeVar('T')


class LoadingState(Enum):
    """State of a lazy component."""
    
    IDLE = "idle"           # Not yet requested
    LOADING = "loading"     # Currently loading
    LOADED = "loaded"       # Successfully loaded
    ERROR = "error"         # Failed to load


@dataclass
class LazyMetadata:
    """Metadata for a lazy component."""
    
    # Unique ID for this lazy component
    id: str
    
    # Human-readable name
    name: str
    
    # Module path (for bundling)
    module_path: Optional[str] = None
    
    # Bundle chunk name
    chunk_name: Optional[str] = None
    
    # Preload strategy
    preload: bool = False
    
    # Dependencies (other chunks needed)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class LazyComponent(Generic[T]):
    """
    A lazily-loaded component.
    
    The component is not imported until first render.
    Works with Suspense to show loading states.
    """
    
    # Unique ID
    id: str
    
    # Loader function that returns the component
    loader: Callable[[], T]
    
    # Metadata
    metadata: LazyMetadata
    
    # Current state
    state: LoadingState = LoadingState.IDLE
    
    # Loaded component (None until loaded)
    component: Optional[T] = None
    
    # Error if loading failed
    error: Optional[Exception] = None
    
    # Pending promise for deduplication
    _loading_task: Optional[asyncio.Task] = None
    
    def __call__(self, *args, **kwargs) -> "LazyBoundary":
        """
        Create a lazy boundary that will load and render the component.
        """
        return LazyBoundary(
            lazy_component=self,
            args=args,
            kwargs=kwargs,
        )
    
    async def load(self) -> T:
        """
        Load the component.
        
        Returns the loaded component, or raises if loading fails.
        """
        if self.state == LoadingState.LOADED and self.component is not None:
            return self.component
        
        if self.state == LoadingState.ERROR and self.error is not None:
            raise self.error
        
        if self._loading_task is not None:
            # Already loading, wait for it
            return await self._loading_task
        
        self.state = LoadingState.LOADING
        
        try:
            # Create loading task
            self._loading_task = asyncio.create_task(self._do_load())
            result = await self._loading_task
            
            self.component = result
            self.state = LoadingState.LOADED
            self._loading_task = None
            
            return result
            
        except Exception as e:
            self.error = e
            self.state = LoadingState.ERROR
            self._loading_task = None
            raise
    
    async def _do_load(self) -> T:
        """Actually perform the loading."""
        # Call the loader
        result = self.loader()
        
        # If it's a coroutine, await it
        if asyncio.iscoroutine(result):
            result = await result
        
        return result
    
    def preload(self) -> None:
        """
        Start loading the component in the background.
        
        Useful for prefetching on hover.
        """
        if self.state == LoadingState.IDLE:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.load())
            except RuntimeError:
                # No running event loop - schedule for later
                # This happens during module initialization
                pass
    
    def get_chunk_url(self) -> str:
        """Get the URL for this component's JavaScript chunk."""
        chunk_name = self.metadata.chunk_name or self.id
        return f"/__pynext__/chunks/{chunk_name}.js"
    
    def get_preload_tag(self) -> str:
        """Get HTML preload tag for this chunk."""
        return f'<link rel="modulepreload" href="{self.get_chunk_url()}">'


@dataclass
class LazyBoundary:
    """
    A boundary that renders a lazy component.
    
    Shows loading state while the component is being loaded.
    Integrates with Suspense for consistent loading UI.
    """
    
    # The lazy component
    lazy_component: LazyComponent
    
    # Args passed to the component
    args: tuple = field(default_factory=tuple)
    
    # Kwargs passed to the component
    kwargs: Dict[str, Any] = field(default_factory=dict)
    
    # Custom fallback (optional, usually uses Suspense)
    fallback: Optional[Any] = None
    
    def render(self) -> str:
        """
        Render the lazy boundary.
        
        If the component is loaded, render it.
        Otherwise, render a placeholder with loading data.
        """
        if self.lazy_component.state == LoadingState.LOADED:
            # Component is ready, render it
            component = self.lazy_component.component
            if callable(component):
                result = component(*self.args, **self.kwargs)
                if hasattr(result, 'render'):
                    return result.render()
                return str(result)
            return str(component)
        
        # Component not ready, render placeholder
        return self._render_placeholder()
    
    async def render_async(self) -> str:
        """
        Render asynchronously, waiting for the component to load.
        """
        await self.lazy_component.load()
        return self.render()
    
    def _render_placeholder(self) -> str:
        """Render a placeholder for the lazy component."""
        chunk_url = self.lazy_component.get_chunk_url()
        
        fallback_html = ""
        if self.fallback:
            if hasattr(self.fallback, 'render'):
                fallback_html = self.fallback.render()
            else:
                fallback_html = str(self.fallback)
        else:
            fallback_html = '<div class="lazy-loading">Loading...</div>'
        
        return f'''<div data-lazy="{self.lazy_component.id}" data-chunk="{chunk_url}" data-state="{self.lazy_component.state.value}">
  <div data-lazy-fallback>{fallback_html}</div>
</div>'''
    
    def get_hydration_script(self) -> str:
        """Get JavaScript to hydrate this lazy component."""
        props_json = json.dumps(self.kwargs)
        
        return f'''
__pynext__.registerLazy("{self.lazy_component.id}", {{
  chunk: "{self.lazy_component.get_chunk_url()}",
  props: {props_json},
  preload: {str(self.lazy_component.metadata.preload).lower()}
}});
'''


# =============================================================================
# Lazy Factory Functions
# =============================================================================

def lazy(
    loader: Callable[[], T],
    *,
    name: Optional[str] = None,
    preload: bool = False,
    chunk_name: Optional[str] = None,
) -> LazyComponent[T]:
    """
    Create a lazy-loaded component.
    
    Args:
        loader: Function that imports/returns the component.
                Can be sync or async.
        name: Human-readable name for debugging.
        preload: Whether to start loading immediately.
        chunk_name: Custom name for the JavaScript chunk.
    
    Returns:
        A LazyComponent that loads the actual component on first use.
    
    Example:
        # Simple lazy import
        HeavyChart = lazy(lambda: import_module("components.chart").Chart)
        
        # With preloading
        CriticalWidget = lazy(
            lambda: import_module("components.widget").Widget,
            preload=True
        )
        
        # Async loader
        RemoteComponent = lazy(
            async lambda: await fetch_component("remote-widget")
        )
    """
    # Generate ID from loader
    component_id = f"lazy-{uuid.uuid4().hex[:8]}"
    component_name = name or getattr(loader, '__name__', 'anonymous')
    
    metadata = LazyMetadata(
        id=component_id,
        name=component_name,
        chunk_name=chunk_name,
        preload=preload,
    )
    
    lazy_comp = LazyComponent(
        id=component_id,
        loader=loader,
        metadata=metadata,
    )
    
    # Start preloading if requested
    if preload:
        lazy_comp.preload()
    
    return lazy_comp


def import_component(module_path: str, component_name: Optional[str] = None) -> Any:
    """
    Import a component from a module path.
    
    Args:
        module_path: Dotted module path (e.g., "components.chart")
        component_name: Name of component to import (default: module name)
    
    Returns:
        The imported component.
    
    Example:
        Chart = import_component("components.chart")
        # Equivalent to: from components.chart import Chart
        
        BarChart = import_component("components.chart", "BarChart")
        # Equivalent to: from components.chart import BarChart
    """
    module = importlib.import_module(module_path)
    
    if component_name:
        return getattr(module, component_name)
    
    # Default to a component with the same name as the module
    default_name = module_path.split('.')[-1]
    default_name = ''.join(word.capitalize() for word in default_name.split('_'))
    
    if hasattr(module, default_name):
        return getattr(module, default_name)
    
    # Return the module itself
    return module


# =============================================================================
# Route-Based Code Splitting
# =============================================================================

@dataclass
class RouteChunk:
    """A JavaScript chunk for a specific route."""
    
    # Route pattern
    route: str
    
    # Chunk file path
    chunk_path: Path
    
    # Components included in this chunk
    components: List[str]
    
    # Dependencies (other chunks)
    dependencies: List[str]
    
    # File size in bytes
    size: int = 0
    
    # Hash for cache busting
    hash: Optional[str] = None


class RouteBundler:
    """
    Generates per-route JavaScript bundles.
    
    Analyzes the component tree for each route and generates
    optimized bundles containing only the code needed for that route.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.chunks: Dict[str, RouteChunk] = {}
        self.shared_chunk: Optional[RouteChunk] = None
    
    def analyze_route(self, route: str, component: Any) -> Set[str]:
        """
        Analyze a route to determine its dependencies.
        
        Returns set of module paths used by this route.
        """
        dependencies = set()
        
        # Get the component's module
        if hasattr(component, '__module__'):
            dependencies.add(component.__module__)
        
        # Analyze component tree for lazy components
        if hasattr(component, '_lazy_dependencies'):
            dependencies.update(component._lazy_dependencies)
        
        return dependencies
    
    def generate_chunk(self, route: str, dependencies: Set[str]) -> RouteChunk:
        """Generate a JavaScript chunk for a route."""
        chunk_name = self._route_to_chunk_name(route)
        chunk_path = self.output_dir / f"{chunk_name}.js"
        
        chunk = RouteChunk(
            route=route,
            chunk_path=chunk_path,
            components=list(dependencies),
            dependencies=[],
        )
        
        self.chunks[route] = chunk
        return chunk
    
    def _route_to_chunk_name(self, route: str) -> str:
        """Convert a route to a chunk file name."""
        # /users/[id] -> users-id
        name = route.strip('/')
        name = name.replace('[', '').replace(']', '')
        name = name.replace('/', '-')
        return name or 'index'
    
    def get_chunk_for_route(self, route: str) -> Optional[RouteChunk]:
        """Get the chunk for a specific route."""
        return self.chunks.get(route)
    
    def get_preload_hints(self, route: str) -> List[str]:
        """Get preload hints for a route's dependencies."""
        chunk = self.get_chunk_for_route(route)
        if not chunk:
            return []
        
        hints = []
        for dep in chunk.dependencies:
            dep_chunk = self.chunks.get(dep)
            if dep_chunk:
                hints.append(f'<link rel="modulepreload" href="/__pynext__/chunks/{dep_chunk.chunk_path.name}">')
        
        return hints


# =============================================================================
# Prefetching
# =============================================================================

class PrefetchStrategy(Enum):
    """When to prefetch a route's code."""
    
    HOVER = "hover"       # Prefetch on link hover
    VISIBLE = "visible"   # Prefetch when link is visible
    IDLE = "idle"         # Prefetch when browser is idle
    NONE = "none"         # Don't prefetch


@dataclass
class PrefetchConfig:
    """Configuration for prefetching."""
    
    # Default strategy
    default_strategy: PrefetchStrategy = PrefetchStrategy.HOVER
    
    # Routes to always prefetch
    always_prefetch: List[str] = field(default_factory=list)
    
    # Routes to never prefetch
    never_prefetch: List[str] = field(default_factory=list)
    
    # Max concurrent prefetches
    max_concurrent: int = 2


def prefetch_link(
    href: str,
    strategy: PrefetchStrategy = PrefetchStrategy.HOVER,
) -> Dict[str, str]:
    """
    Get attributes for a prefetching link.
    
    Args:
        href: Link destination
        strategy: When to prefetch
    
    Returns:
        Dictionary of HTML attributes.
    
    Example:
        a(**prefetch_link("/dashboard"), href="/dashboard")["Dashboard"]
    """
    return {
        "href": href,
        "data-prefetch": strategy.value,
    }


# =============================================================================
# Lazy Loading Registry
# =============================================================================

class LazyRegistry:
    """
    Global registry of lazy components.
    
    Tracks all lazy components for:
    - Bundle generation
    - Preloading coordination
    - Chunk dependency analysis
    """
    
    def __init__(self):
        self._components: Dict[str, LazyComponent] = {}
        self._chunks: Dict[str, Set[str]] = {}  # chunk_name -> component IDs
    
    def register(self, component: LazyComponent) -> None:
        """Register a lazy component."""
        self._components[component.id] = component
        
        chunk = component.metadata.chunk_name or 'main'
        if chunk not in self._chunks:
            self._chunks[chunk] = set()
        self._chunks[chunk].add(component.id)
    
    def get(self, component_id: str) -> Optional[LazyComponent]:
        """Get a lazy component by ID."""
        return self._components.get(component_id)
    
    def get_all(self) -> List[LazyComponent]:
        """Get all registered lazy components."""
        return list(self._components.values())
    
    def get_chunk_components(self, chunk_name: str) -> List[LazyComponent]:
        """Get all components in a chunk."""
        component_ids = self._chunks.get(chunk_name, set())
        return [self._components[id] for id in component_ids if id in self._components]
    
    def preload_all(self, chunk_name: Optional[str] = None) -> None:
        """Start preloading all components (optionally filtered by chunk)."""
        components = (
            self.get_chunk_components(chunk_name)
            if chunk_name
            else self.get_all()
        )
        for comp in components:
            comp.preload()


# Global registry
_lazy_registry = LazyRegistry()


def get_lazy_registry() -> LazyRegistry:
    """Get the global lazy component registry."""
    return _lazy_registry


# =============================================================================
# HTML Generation Helpers
# =============================================================================

def generate_lazy_scripts(components: List[LazyComponent]) -> str:
    """Generate JavaScript for lazy component hydration."""
    if not components:
        return ""
    
    scripts = []
    for comp in components:
        boundary = comp()  # Create a boundary to get the script
        scripts.append(boundary.get_hydration_script())
    
    return f'''<script>
(function() {{
  {"".join(scripts)}
  __pynext__.initLazyLoading();
}})();
</script>'''


def generate_preload_tags(routes: List[str], bundler: RouteBundler) -> str:
    """Generate preload tags for routes."""
    tags = []
    for route in routes:
        chunk = bundler.get_chunk_for_route(route)
        if chunk:
            tags.append(f'<link rel="modulepreload" href="/__pynext__/chunks/{chunk.chunk_path.name}">')
    return "\n".join(tags)


# =============================================================================
# Lazy Route Decorator
# =============================================================================

def lazy_route(
    path: str,
    *,
    preload: bool = False,
    prefetch: PrefetchStrategy = PrefetchStrategy.HOVER,
):
    """
    Decorator to make a route lazy-loaded.
    
    The route's component will be loaded on-demand when navigating to it.
    
    Args:
        path: Route path pattern
        preload: Whether to preload this route on page load
        prefetch: When to prefetch this route
    
    Example:
        @lazy_route("/analytics")
        def AnalyticsPage():
            # This component is only loaded when visiting /analytics
            return div()[HeavyAnalytics()]
    """
    def decorator(func: Callable) -> LazyComponent:
        # Create lazy wrapper
        lazy_comp = lazy(
            func,
            name=func.__name__,
            preload=preload,
            chunk_name=path.strip('/').replace('/', '-') or 'index',
        )
        
        # Store route metadata
        lazy_comp.metadata.module_path = path
        
        # Register in global registry
        _lazy_registry.register(lazy_comp)
        
        return lazy_comp
    
    return decorator

