"""
PyNext Static Site Generation (SSG) - Selective Hydration.

Unlike Next.js which hydrates the full React tree even for static pages,
PyNext uses SolidJS principles to ship zero JS for fully static pages
and only hydrate interactive "islands" when needed.

SolidJS Principles Applied:
- Components run once (no re-renders)
- Zero JS for static content
- Fine-grained updates only for interactive parts
- Build-time work over runtime processing
"""

from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
    Awaitable,
    Tuple,
)
import asyncio
import hashlib
import inspect
import json

from pynext.core.island import is_interactive, collect_islands, HydrationStrategy


T = TypeVar("T")
PageFunc = Callable[..., Any]
PropsFunc = Callable[..., Union[Dict[str, Any], Awaitable[Dict[str, Any]]]]
PathsFunc = Callable[[], Union[List[Dict[str, str]], Awaitable[List[Dict[str, str]]]]]


class GenerationMode(Enum):
    """Page generation mode."""
    STATIC = "static"          # Build-time only
    SSR = "ssr"                # Server-side on each request
    ISR = "isr"                # Incremental static regeneration
    HYBRID = "hybrid"          # Static shell + client hydration


@dataclass
class StaticPageConfig:
    """Configuration for a static page."""
    mode: GenerationMode = GenerationMode.STATIC
    revalidate: Optional[int] = None  # Seconds for ISR
    fallback: bool = False  # For dynamic paths not generated at build
    
    # Hydration settings
    hydrate_islands_only: bool = True  # Only hydrate @island components
    ship_zero_js: bool = True  # Attempt to ship no JS if page is fully static
    
    # Caching
    cache_control: str = "public, max-age=31536000, immutable"
    
    # Build settings
    parallel: bool = True  # Build paths in parallel


@dataclass
class StaticPath:
    """Represents a single static path to generate."""
    params: Dict[str, str]
    locale: Optional[str] = None
    
    def get_path(self, pattern: str) -> str:
        """Generate URL path from pattern and params."""
        path = pattern
        for key, value in self.params.items():
            path = path.replace(f"[{key}]", value)
            path = path.replace(f"[...{key}]", value)
        return path


@dataclass
class StaticBuildResult:
    """Result of building a static page."""
    path: str
    html: str
    js_bundle: Optional[str] = None  # None = zero JS
    css: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Build info
    generated_at: float = 0
    hash: str = ""
    has_islands: bool = False
    island_count: int = 0
    
    def needs_js(self) -> bool:
        """Check if this page needs any JavaScript."""
        return self.has_islands and self.js_bundle is not None


# Registry for static pages
_static_pages: Dict[str, "StaticPageMeta"] = {}
_static_props_funcs: Dict[str, PropsFunc] = {}
_static_paths_funcs: Dict[str, PathsFunc] = {}


@dataclass
class StaticPageMeta:
    """Metadata for a registered static page."""
    page_func: PageFunc
    config: StaticPageConfig
    props_func: Optional[PropsFunc] = None
    paths_func: Optional[PathsFunc] = None
    route_pattern: str = ""


def static_page(
    config: Optional[StaticPageConfig] = None,
    **kwargs
) -> Callable[[PageFunc], PageFunc]:
    """
    Decorator to mark a page for static generation.
    
    Example:
        @static_page()
        def about():
            return div(
                h1("About Us"),
                p("This is a static page with zero JavaScript.")
            )
        
        @static_page(config=StaticPageConfig(revalidate=60))
        def blog():
            return div(h1("Blog"))
    """
    if config is None:
        config = StaticPageConfig(**kwargs)
    
    def decorator(func: PageFunc) -> PageFunc:
        # Get route pattern from function location
        module = inspect.getmodule(func)
        route_pattern = _get_route_pattern(module, func.__name__)
        
        # Register the page
        _static_pages[route_pattern] = StaticPageMeta(
            page_func=func,
            config=config,
            route_pattern=route_pattern,
        )
        
        # Mark function
        func._is_static_page = True
        func._static_config = config
        func._route_pattern = route_pattern
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def static_props(
    func: Optional[PropsFunc] = None,
    *,
    revalidate: Optional[int] = None
) -> Union[PropsFunc, Callable[[PropsFunc], PropsFunc]]:
    """
    Decorator for build-time data fetching (like getStaticProps).
    
    The function receives the current path params and returns props
    that will be passed to the page component.
    
    Example:
        @static_props
        async def get_blog_props(params: dict) -> dict:
            post = await fetch_post(params["slug"])
            return {"post": post}
    
        @static_props(revalidate=60)
        async def get_products_props(params: dict) -> dict:
            products = await fetch_products()
            return {"products": products}
    """
    def decorator(fn: PropsFunc) -> PropsFunc:
        # Find associated page
        module = inspect.getmodule(fn)
        route_pattern = _get_route_pattern(module, "page")
        
        _static_props_funcs[route_pattern] = fn
        
        # Update page meta if exists
        if route_pattern in _static_pages:
            _static_pages[route_pattern].props_func = fn
            if revalidate is not None:
                _static_pages[route_pattern].config.revalidate = revalidate
        
        fn._is_static_props = True
        fn._revalidate = revalidate
        
        return fn
    
    if func is not None:
        return decorator(func)
    return decorator


def static_paths(
    func: Optional[PathsFunc] = None,
    *,
    fallback: bool = False
) -> Union[PathsFunc, Callable[[PathsFunc], PathsFunc]]:
    """
    Decorator for generating dynamic paths at build time (like getStaticPaths).
    
    Returns a list of param objects, each representing a path to generate.
    
    Example:
        @static_paths
        async def get_blog_paths() -> list:
            posts = await fetch_all_posts()
            return [{"params": {"slug": post.slug}} for post in posts]
        
        @static_paths(fallback=True)
        async def get_product_paths() -> list:
            # Only generate top products, others on-demand
            products = await fetch_top_products()
            return [{"params": {"id": str(p.id)}} for p in products]
    """
    def decorator(fn: PathsFunc) -> PathsFunc:
        module = inspect.getmodule(fn)
        route_pattern = _get_route_pattern(module, "page")
        
        _static_paths_funcs[route_pattern] = fn
        
        if route_pattern in _static_pages:
            _static_pages[route_pattern].paths_func = fn
            _static_pages[route_pattern].config.fallback = fallback
        
        fn._is_static_paths = True
        fn._fallback = fallback
        
        return fn
    
    if func is not None:
        return decorator(func)
    return decorator


def _get_route_pattern(module: Any, func_name: str) -> str:
    """Extract route pattern from module file path."""
    if module is None or not hasattr(module, "__file__"):
        return f"/{func_name}"
    
    file_path = Path(module.__file__)
    
    # Find pages directory
    parts = file_path.parts
    try:
        pages_idx = parts.index("pages")
        route_parts = parts[pages_idx + 1:]
    except ValueError:
        # Not in pages directory
        return f"/{file_path.stem}"
    
    # Build route pattern
    route = "/" + "/".join(route_parts)
    
    # Remove .py extension
    if route.endswith(".py"):
        route = route[:-3]
    
    # Handle index files
    if route.endswith("/index"):
        route = route[:-6] or "/"
    
    return route


def get_static_pages() -> Dict[str, StaticPageMeta]:
    """Get all registered static pages."""
    return _static_pages.copy()


def get_static_props_func(route: str) -> Optional[PropsFunc]:
    """Get static props function for a route."""
    return _static_props_funcs.get(route)


def get_static_paths_func(route: str) -> Optional[PathsFunc]:
    """Get static paths function for a route."""
    return _static_paths_funcs.get(route)


class StaticAnalyzer:
    """
    Analyzes components to determine if they can be fully static.
    
    A component is fully static if it:
    - Has no Signals/Stores
    - Has no event handlers (onclick, etc.)
    - Has no Effects
    - Has no Resources (async data)
    - Has no @island decorated children
    
    Fully static components result in zero JavaScript.
    """
    
    def __init__(self):
        self._cache: Dict[str, bool] = {}
    
    def is_fully_static(self, component: Any) -> bool:
        """
        Check if a component tree is fully static.
        
        Returns True if no JavaScript is needed.
        """
        # Check cache
        comp_id = id(component)
        if comp_id in self._cache:
            return self._cache[comp_id]
        
        # Check if component is interactive
        if is_interactive(component):
            self._cache[comp_id] = False
            return False
        
        # Check for islands
        islands = collect_islands(component)
        if islands:
            self._cache[comp_id] = False
            return False
        
        # Component is static
        self._cache[comp_id] = True
        return True
    
    def get_required_js(self, component: Any) -> Optional[str]:
        """
        Get minimal JavaScript bundle needed for component.
        
        Returns None for fully static components (zero JS).
        """
        if self.is_fully_static(component):
            return None
        
        # Collect islands and determine required runtime
        islands = collect_islands(component)
        
        if not islands:
            return None
        
        # Generate minimal JS for islands only
        return self._generate_islands_js(islands)
    
    def _generate_islands_js(self, islands: List[Any]) -> str:
        """Generate JavaScript for island hydration only."""
        island_data = []
        
        for island in islands:
            island_data.append({
                "id": island.id,
                "strategy": island.strategy.value,
                "props": island.props,
            })
        
        return f"""
(function() {{
    const islands = {json.dumps(island_data)};
    
    function hydrateIsland(data) {{
        const el = document.getElementById(data.id);
        if (!el) return;
        
        const strategy = data.strategy;
        
        if (strategy === 'load') {{
            __pynext__.hydrateIsland(el, data.props);
        }} else if (strategy === 'visible') {{
            const observer = new IntersectionObserver((entries) => {{
                if (entries[0].isIntersecting) {{
                    __pynext__.hydrateIsland(el, data.props);
                    observer.disconnect();
                }}
            }});
            observer.observe(el);
        }} else if (strategy === 'idle') {{
            requestIdleCallback(() => __pynext__.hydrateIsland(el, data.props));
        }}
    }}
    
    islands.forEach(hydrateIsland);
}})();
"""
    
    def clear_cache(self) -> None:
        """Clear analysis cache."""
        self._cache.clear()


# Global analyzer instance
_analyzer = StaticAnalyzer()


def get_static_analyzer() -> StaticAnalyzer:
    """Get the global static analyzer."""
    return _analyzer


def analyze_page(page_component: Any) -> Dict[str, Any]:
    """
    Analyze a page to determine its static/dynamic characteristics.
    
    Returns analysis report.
    """
    analyzer = get_static_analyzer()
    islands = collect_islands(page_component)
    
    return {
        "is_fully_static": analyzer.is_fully_static(page_component),
        "needs_js": not analyzer.is_fully_static(page_component),
        "island_count": len(islands),
        "islands": [
            {
                "id": i.id,
                "strategy": i.strategy.value,
                "interactive": is_interactive(i.component),
            }
            for i in islands
        ],
        "recommended_mode": (
            GenerationMode.STATIC if analyzer.is_fully_static(page_component)
            else GenerationMode.HYBRID
        ),
    }


async def get_build_paths(route: str) -> List[StaticPath]:
    """
    Get all paths to build for a static route.
    
    For routes with [params], calls the static_paths function.
    For static routes, returns single path.
    """
    paths_func = get_static_paths_func(route)
    
    if paths_func is None:
        # No dynamic params, single path
        return [StaticPath(params={})]
    
    # Call paths function
    result = paths_func()
    if asyncio.iscoroutine(result):
        result = await result
    
    return [
        StaticPath(
            params=item.get("params", {}),
            locale=item.get("locale")
        )
        for item in result
    ]


async def get_page_props(route: str, params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get props for a page at build time.
    
    Calls the static_props function if defined.
    """
    props_func = get_static_props_func(route)
    
    if props_func is None:
        return {"params": params}
    
    result = props_func(params)
    if asyncio.iscoroutine(result):
        result = await result
    
    return result


def compute_page_hash(html: str, props: Dict[str, Any]) -> str:
    """Compute hash of page content for cache invalidation."""
    content = html + json.dumps(props, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()[:12]

