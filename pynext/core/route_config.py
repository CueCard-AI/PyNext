"""
Route Segment Configuration.

Configure per-route behavior: rendering mode, caching, runtime.

Example:
    from pynext import route_config, page
    
    @route_config(dynamic="force", revalidate=60)
    @page
    def MyPage():
        return div("Hello")

Why This Matters:
    Different pages need different behavior:
    - Landing page: Static, cached forever
    - Product page: ISR, refresh every hour
    - Dashboard: Dynamic, never cache
    - API endpoint: Edge runtime for speed

SolidJS Principle: Fine-grained control at route level
AI-Friendly: Single decorator, clear parameters, sensible defaults
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union, Callable, Any, Dict
from enum import Enum
from functools import wraps


# ============================================
# Enums for Type Safety & IDE Support
# ============================================

class Dynamic(str, Enum):
    """
    Rendering mode for the route.
    
    Determines when and how the page is rendered:
    
    - AUTO: PyNext decides based on what you use in the page
    - FORCE: Always render at request time (dynamic)
    - ERROR: Error if any dynamic features are detected
    - STATIC: Force static generation at build time
    
    Example:
        @route_config(dynamic=Dynamic.FORCE)  # or dynamic="force"
        @page
        def DashboardPage():
            return div(user.name)  # Always fresh
    """
    AUTO = "auto"      # PyNext decides based on usage
    FORCE = "force"    # Always render dynamically
    ERROR = "error"    # Error if dynamic features detected
    STATIC = "static"  # Force static generation


class Cache(str, Enum):
    """
    Caching behavior for the route.
    
    Controls how responses are cached:
    
    - AUTO: PyNext decides based on dynamic mode and revalidate
    - FORCE: Always cache the response
    - NO_STORE: Never cache, always fresh
    
    Example:
        @route_config(cache=Cache.NO_STORE)  # or cache="no-store"
        @page
        def RealTimePage():
            return div(get_live_data())
    """
    AUTO = "auto"          # PyNext decides
    FORCE = "force"        # Always cache
    NO_STORE = "no-store"  # Never cache


class Runtime(str, Enum):
    """
    Execution runtime for the route.
    
    Where the code runs:
    
    - PYTHON: Standard Python runtime (default)
    - EDGE: Edge runtime (Cloudflare Workers, Vercel Edge, etc.)
    
    Edge runtime is faster but has limitations:
    - No filesystem access
    - Limited Python packages
    - Shorter execution time
    
    Example:
        @route_config(runtime=Runtime.EDGE)
        @api_route
        async def fast_api(request):
            return JSONResponse({"fast": True})
    """
    PYTHON = "python"  # Standard Python (default)
    EDGE = "edge"      # Edge runtime


# ============================================
# RouteConfig Dataclass
# ============================================

@dataclass
class RouteConfig:
    """
    Configuration for a route segment.
    
    All fields have sensible defaults - only override what you need.
    
    Attributes:
        dynamic: Rendering mode (auto/force/error/static)
        dynamic_params: Allow dynamic params beyond defined paths
        revalidate: ISR seconds (False=disabled, int=seconds, 0=every request)
        cache: Caching behavior (auto/force/no-store)
        tags: Cache tags for on-demand revalidation
        runtime: Execution runtime (python/edge)
        max_duration: Maximum execution time in seconds
        preferred_region: Deployment region hint
    
    Example:
        config = RouteConfig(
            dynamic=Dynamic.FORCE,
            revalidate=60,
            tags=["products"],
        )
    """
    # Rendering
    dynamic: Dynamic = Dynamic.AUTO
    dynamic_params: bool = True
    
    # Caching
    revalidate: Union[int, bool] = False
    cache: Cache = Cache.AUTO
    tags: List[str] = field(default_factory=list)
    
    # Runtime
    runtime: Runtime = Runtime.PYTHON
    max_duration: int = 60
    preferred_region: Union[str, List[str]] = "auto"
    
    # Internal tracking
    _source_file: Optional[str] = field(default=None, repr=False)
    _function_name: Optional[str] = field(default=None, repr=False)
    
    def __post_init__(self):
        """Convert string values to enums for flexibility."""
        if isinstance(self.dynamic, str):
            try:
                self.dynamic = Dynamic(self.dynamic)
            except ValueError:
                raise ValueError(
                    f"Invalid dynamic mode: '{self.dynamic}'. "
                    f"Must be one of: {[d.value for d in Dynamic]}"
                )
        
        if isinstance(self.cache, str):
            try:
                self.cache = Cache(self.cache)
            except ValueError:
                raise ValueError(
                    f"Invalid cache mode: '{self.cache}'. "
                    f"Must be one of: {[c.value for c in Cache]}"
                )
        
        if isinstance(self.runtime, str):
            try:
                self.runtime = Runtime(self.runtime)
            except ValueError:
                raise ValueError(
                    f"Invalid runtime: '{self.runtime}'. "
                    f"Must be one of: {[r.value for r in Runtime]}"
                )
        
        # Validate max_duration
        if self.max_duration <= 0:
            raise ValueError(f"max_duration must be positive, got {self.max_duration}")
        
        # Validate revalidate
        if isinstance(self.revalidate, int) and self.revalidate < 0:
            raise ValueError(f"revalidate must be >= 0, got {self.revalidate}")
    
    def should_cache(self) -> bool:
        """
        Determine if route should be cached.
        
        Returns:
            True if caching is enabled
        
        Logic:
            1. NO_STORE cache = never cache
            2. FORCE cache = always cache
            3. FORCE dynamic = don't cache (always fresh)
            4. Otherwise, cache if revalidate is set
        """
        if self.cache == Cache.NO_STORE:
            return False
        if self.cache == Cache.FORCE:
            return True
        if self.dynamic == Dynamic.FORCE:
            return False
        return self.revalidate is not False
    
    def get_cache_seconds(self) -> Optional[int]:
        """
        Get cache duration in seconds.
        
        Returns:
            Cache seconds if revalidate is int, None otherwise
        """
        # Check for int but not bool (bool is subclass of int in Python)
        if isinstance(self.revalidate, int) and not isinstance(self.revalidate, bool):
            return self.revalidate
        return None
    
    def is_static(self) -> bool:
        """
        Check if route is statically generated.
        
        Returns:
            True if dynamic mode is STATIC or ERROR
        """
        return self.dynamic in (Dynamic.STATIC, Dynamic.ERROR)
    
    def is_dynamic(self) -> bool:
        """
        Check if route is dynamically rendered.
        
        Returns:
            True if dynamic mode is FORCE
        """
        return self.dynamic == Dynamic.FORCE
    
    def is_edge(self) -> bool:
        """
        Check if route runs on edge runtime.
        
        Returns:
            True if runtime is EDGE
        """
        return self.runtime == Runtime.EDGE
    
    def to_headers(self) -> Dict[str, str]:
        """
        Generate HTTP cache headers based on config.
        
        Returns:
            Dict of header name to value
        
        Example:
            {"Cache-Control": "public, s-maxage=60, stale-while-revalidate"}
        """
        headers: Dict[str, str] = {}
        
        if self.cache == Cache.NO_STORE:
            headers["Cache-Control"] = "no-store, must-revalidate"
        elif self.cache == Cache.FORCE:
            headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            cache_seconds = self.get_cache_seconds()
            if cache_seconds is not None:
                if cache_seconds == 0:
                    headers["Cache-Control"] = "no-cache, must-revalidate"
                else:
                    headers["Cache-Control"] = f"public, s-maxage={cache_seconds}, stale-while-revalidate"
        
        # Add cache tags header for CDN invalidation
        if self.tags:
            headers["X-Cache-Tags"] = ",".join(self.tags)
        
        return headers
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary for serialization.
        
        Returns:
            Dict representation of config
        """
        return {
            "dynamic": self.dynamic.value,
            "dynamic_params": self.dynamic_params,
            "revalidate": self.revalidate,
            "cache": self.cache.value,
            "tags": self.tags,
            "runtime": self.runtime.value,
            "max_duration": self.max_duration,
            "preferred_region": self.preferred_region,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RouteConfig":
        """
        Create config from dictionary.
        
        Args:
            data: Dict with config values
        
        Returns:
            RouteConfig instance
        """
        return cls(
            dynamic=data.get("dynamic", "auto"),
            dynamic_params=data.get("dynamic_params", True),
            revalidate=data.get("revalidate", False),
            cache=data.get("cache", "auto"),
            tags=data.get("tags", []),
            runtime=data.get("runtime", "python"),
            max_duration=data.get("max_duration", 60),
            preferred_region=data.get("preferred_region", "auto"),
        )
    
    def merge_with(self, other: "RouteConfig") -> "RouteConfig":
        """
        Merge this config with another (other takes precedence).
        
        Useful for inheriting from parent routes.
        
        Args:
            other: Config to merge with
        
        Returns:
            New merged RouteConfig
        """
        return RouteConfig(
            dynamic=other.dynamic if other.dynamic != Dynamic.AUTO else self.dynamic,
            dynamic_params=other.dynamic_params,
            revalidate=other.revalidate if other.revalidate is not False else self.revalidate,
            cache=other.cache if other.cache != Cache.AUTO else self.cache,
            tags=list(set(self.tags + other.tags)),
            runtime=other.runtime if other.runtime != Runtime.PYTHON else self.runtime,
            max_duration=min(self.max_duration, other.max_duration),
            preferred_region=other.preferred_region if other.preferred_region != "auto" else self.preferred_region,
        )


# ============================================
# Global Registry
# ============================================

# Registry mapping function IDs to configs
_route_configs: Dict[str, RouteConfig] = {}

# Registry mapping route paths to configs (populated by router)
_path_configs: Dict[str, RouteConfig] = {}


def _get_function_id(fn: Callable) -> str:
    """Get unique identifier for a function."""
    module = getattr(fn, "__module__", "__main__")
    name = getattr(fn, "__name__", str(fn))
    return f"{module}.{name}"


def register_path_config(path: str, config: RouteConfig) -> None:
    """
    Register config for a route path (called by router).
    
    Args:
        path: Route path (e.g., "/products/[id]")
        config: RouteConfig for the path
    """
    _path_configs[path] = config


def get_config_by_path(path: str) -> Optional[RouteConfig]:
    """
    Get config by route path.
    
    Args:
        path: Route path
    
    Returns:
        RouteConfig if registered, None otherwise
    """
    return _path_configs.get(path)


def get_all_configs() -> Dict[str, RouteConfig]:
    """
    Get all registered route configs.
    
    Returns:
        Dict mapping function IDs to configs
    """
    return dict(_route_configs)


def clear_configs() -> None:
    """Clear all registered configs (for testing)."""
    _route_configs.clear()
    _path_configs.clear()


# ============================================
# Main Decorator
# ============================================

def route_config(
    dynamic: Union[Dynamic, str] = Dynamic.AUTO,
    revalidate: Union[int, bool] = False,
    cache: Union[Cache, str] = Cache.AUTO,
    tags: Optional[List[str]] = None,
    runtime: Union[Runtime, str] = Runtime.PYTHON,
    max_duration: int = 60,
    dynamic_params: bool = True,
    preferred_region: Union[str, List[str]] = "auto",
) -> Callable[[Callable], Callable]:
    """
    Configure route behavior with a single decorator.
    
    This decorator attaches configuration to your page or API route
    that controls how it's rendered and cached.
    
    Args:
        dynamic: Rendering mode
            - "auto" (default): PyNext decides
            - "force": Always render at request time
            - "error": Error if dynamic features used
            - "static": Force static generation
        
        revalidate: ISR (Incremental Static Regeneration)
            - False (default): No ISR
            - 0: Revalidate every request
            - 60: Revalidate every 60 seconds
        
        cache: Caching behavior
            - "auto" (default): PyNext decides
            - "force": Always cache
            - "no-store": Never cache
        
        tags: Cache tags for on-demand revalidation
            Use revalidate_tag("products") to invalidate
        
        runtime: Execution runtime
            - "python" (default): Standard Python
            - "edge": Edge runtime (faster, limited)
        
        max_duration: Max execution time in seconds
        
        dynamic_params: Allow dynamic params beyond defined paths
        
        preferred_region: Deployment region hint(s)
    
    Returns:
        Decorated function with __route_config__ attribute
    
    Example:
        # Static page with 1-hour ISR
        @route_config(revalidate=3600, tags=["products"])
        @page
        def ProductsPage():
            products = fetch_products()
            return ProductList(products)
        
        # Dynamic page (always fresh)
        @route_config(dynamic="force", cache="no-store")
        @page
        def DashboardPage():
            return Dashboard(get_user_data())
        
        # Edge API endpoint
        @route_config(runtime="edge", max_duration=10)
        @api_route
        async def fast_api(request):
            return JSONResponse({"fast": True})
    """
    # Create config object
    config = RouteConfig(
        dynamic=dynamic,
        revalidate=revalidate,
        cache=cache,
        tags=tags or [],
        runtime=runtime,
        max_duration=max_duration,
        dynamic_params=dynamic_params,
        preferred_region=preferred_region,
    )
    
    def decorator(fn: Callable) -> Callable:
        # Store source info for debugging
        config._source_file = getattr(fn, "__module__", None)
        config._function_name = getattr(fn, "__name__", None)
        
        # Store config on function
        fn.__route_config__ = config
        
        # Register globally by function ID
        fn_id = _get_function_id(fn)
        _route_configs[fn_id] = config
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        
        # Copy config to wrapper
        wrapper.__route_config__ = config
        
        return wrapper
    
    return decorator


def get_route_config(fn: Callable) -> Optional[RouteConfig]:
    """
    Get RouteConfig attached to a function.
    
    Args:
        fn: Function to check
    
    Returns:
        RouteConfig if decorated, None otherwise
    
    Example:
        @route_config(dynamic="force")
        @page
        def MyPage():
            pass
        
        config = get_route_config(MyPage)
        print(config.dynamic)  # Dynamic.FORCE
    """
    return getattr(fn, "__route_config__", None)


def has_route_config(fn: Callable) -> bool:
    """
    Check if function has RouteConfig attached.
    
    Args:
        fn: Function to check
    
    Returns:
        True if decorated with @route_config
    """
    return hasattr(fn, "__route_config__")


# ============================================
# Convenience Shortcuts
# ============================================

def static_route(
    revalidate: int = 3600,
    tags: Optional[List[str]] = None,
) -> Callable[[Callable], Callable]:
    """
    Shortcut for static routes with ISR.
    
    Creates a statically generated page that revalidates periodically.
    
    Args:
        revalidate: Seconds between revalidations (default: 1 hour)
        tags: Cache tags for on-demand revalidation
    
    Example:
        @static_route(revalidate=3600)  # Refresh every hour
        @page
        def BlogPage():
            return render_blog_posts()
    
    Equivalent to:
        @route_config(dynamic="static", revalidate=3600)
    """
    return route_config(
        dynamic=Dynamic.STATIC,
        revalidate=revalidate,
        tags=tags,
    )


def dynamic_route(
    cache: bool = False,
    max_duration: int = 60,
) -> Callable[[Callable], Callable]:
    """
    Shortcut for dynamic routes.
    
    Creates a page that's always rendered at request time.
    
    Args:
        cache: Whether to cache responses (default: False)
        max_duration: Max execution time in seconds
    
    Example:
        @dynamic_route()  # Always fresh
        @page
        def DashboardPage():
            return Dashboard(get_user_data())
    
    Equivalent to:
        @route_config(dynamic="force", cache="no-store")
    """
    return route_config(
        dynamic=Dynamic.FORCE,
        cache=Cache.AUTO if cache else Cache.NO_STORE,
        max_duration=max_duration,
    )


def edge_route(
    max_duration: int = 30,
    preferred_region: Union[str, List[str]] = "auto",
) -> Callable[[Callable], Callable]:
    """
    Shortcut for edge runtime.
    
    Runs the route on edge runtime (Cloudflare Workers, etc.)
    for lower latency.
    
    Args:
        max_duration: Max execution time (edge has lower limits)
        preferred_region: Where to run (affects latency)
    
    Example:
        @edge_route(max_duration=10)
        @api_route
        async def geo_api(request):
            return JSONResponse(get_nearest_server())
    
    Equivalent to:
        @route_config(runtime="edge", max_duration=30)
    """
    return route_config(
        runtime=Runtime.EDGE,
        max_duration=max_duration,
        preferred_region=preferred_region,
    )


def cached_route(
    seconds: int,
    tags: Optional[List[str]] = None,
) -> Callable[[Callable], Callable]:
    """
    Shortcut for cached routes with specific TTL.
    
    Creates a page with explicit cache duration.
    
    Args:
        seconds: Cache duration in seconds
        tags: Cache tags for on-demand invalidation
    
    Example:
        @cached_route(300, tags=["data"])  # 5 minute cache
        @page
        def DataPage():
            return render_data()
    
    Equivalent to:
        @route_config(revalidate=300, tags=["data"])
    """
    return route_config(
        revalidate=seconds,
        tags=tags,
    )


def no_cache_route(
    max_duration: int = 60,
) -> Callable[[Callable], Callable]:
    """
    Shortcut for routes that should never be cached.
    
    Args:
        max_duration: Max execution time in seconds
    
    Example:
        @no_cache_route()
        @api_route
        async def realtime_data(request):
            return JSONResponse(get_live_data())
    
    Equivalent to:
        @route_config(cache="no-store")
    """
    return route_config(
        cache=Cache.NO_STORE,
        max_duration=max_duration,
    )


# ============================================
# Default Config
# ============================================

# Default config for routes without explicit configuration
DEFAULT_CONFIG = RouteConfig()


def get_effective_config(fn: Callable) -> RouteConfig:
    """
    Get effective config for a function (explicit or default).
    
    Args:
        fn: Function to get config for
    
    Returns:
        Explicit RouteConfig if decorated, DEFAULT_CONFIG otherwise
    """
    return get_route_config(fn) or DEFAULT_CONFIG

