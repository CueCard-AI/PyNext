"""
PyNext Partial Prerendering (PPR) - Component-Level Static/Dynamic Split.

Unlike Next.js which implements PPR at page level, PyNext provides
component-level granularity for maximum optimization.

SolidJS Principles Applied:
- Build-time static shell extraction
- Component-level (not page-level) granularity
- Zero hydration for static parts
- Fine-grained streaming of dynamic content
- Out-of-order placeholder resolution

Performance Advantages over Next.js:
- Component-level vs page-level granularity
- Static parts never hydrate (zero JS)
- Smaller streaming payloads
- Better caching (granular invalidation)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Union,
    TypeVar,
    Generic,
)
import uuid
import hashlib
import inspect
import asyncio
import contextvars
import functools

from pynext.reactive import Signal
from pynext.core.html import div, Fragment


T = TypeVar('T')


class PPRMode(Enum):
    """PPR rendering modes."""
    STATIC = "static"       # Fully static, rendered at build
    DYNAMIC = "dynamic"     # Fully dynamic, rendered at request
    HYBRID = "hybrid"       # Static shell + dynamic holes


class ComponentType(Enum):
    """Component classification for PPR."""
    STATIC = "static"           # No signals, no async, no props from request
    DYNAMIC = "dynamic"         # Uses signals, async data, or request data
    STATIC_SHELL = "shell"      # Static wrapper around dynamic content
    STREAMING = "streaming"     # Async component for streaming


@dataclass
class PPRBoundary:
    """
    A boundary between static and dynamic content.
    
    Marks where the static shell ends and dynamic content begins.
    """
    id: str
    placeholder_html: str       # Shown while loading
    static_shell: Optional[str] = None  # Pre-rendered shell
    is_resolved: bool = False
    resolved_content: Optional[str] = None


@dataclass
class PPRAnalysis:
    """Analysis result for a component."""
    component_type: ComponentType
    has_signals: bool
    has_async: bool
    has_request_data: bool
    static_props: Set[str]      # Props that are static (literals)
    dynamic_props: Set[str]     # Props that vary per request
    estimated_render_time: float  # ms


# Context for PPR rendering
_ppr_context: contextvars.ContextVar[Optional["PPRContext"]] = contextvars.ContextVar(
    "ppr_context", default=None
)


@dataclass
class PPRContext:
    """Context for PPR rendering."""
    mode: PPRMode = PPRMode.HYBRID
    boundaries: Dict[str, PPRBoundary] = field(default_factory=dict)
    static_cache: Dict[str, str] = field(default_factory=dict)
    dynamic_pending: List[str] = field(default_factory=list)
    
    def add_boundary(self, boundary: PPRBoundary) -> None:
        """Add a PPR boundary."""
        self.boundaries[boundary.id] = boundary
        if not boundary.is_resolved:
            self.dynamic_pending.append(boundary.id)
    
    def resolve_boundary(self, boundary_id: str, content: str) -> None:
        """Mark a boundary as resolved with content."""
        if boundary_id in self.boundaries:
            self.boundaries[boundary_id].is_resolved = True
            self.boundaries[boundary_id].resolved_content = content
            if boundary_id in self.dynamic_pending:
                self.dynamic_pending.remove(boundary_id)


def get_ppr_context() -> Optional[PPRContext]:
    """Get current PPR context."""
    return _ppr_context.get()


def create_ppr_context(mode: PPRMode = PPRMode.HYBRID) -> PPRContext:
    """Create a new PPR context."""
    ctx = PPRContext(mode=mode)
    _ppr_context.set(ctx)
    return ctx


# =============================================================================
# PPR Decorators
# =============================================================================

def partial_prerender(
    fallback: Optional[Callable[[], Any]] = None,
    timeout: float = 3.0,
    cache_key: Optional[str] = None,
):
    """
    Mark a page/component for partial prerendering.
    
    The decorator analyzes the component to identify static and dynamic
    parts. Static parts are rendered at build time, dynamic parts are
    streamed at request time.
    
    Args:
        fallback: Skeleton/loading component to show for dynamic parts
        timeout: Max time to wait for dynamic content before showing fallback
        cache_key: Custom cache key for static shell
    
    Example:
        @partial_prerender(fallback=ProductSkeleton)
        def product_page(id: str):
            return div()[
                StaticHeader(),
                Suspense(fallback=Skeleton())[
                    ProductDetails(id),  # Dynamic
                ],
                StaticFooter(),
            ]
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # Get or create PPR context
            ctx = get_ppr_context()
            if ctx is None:
                ctx = create_ppr_context()
            
            # Generate cache key
            key = cache_key or _generate_cache_key(fn, args, kwargs)
            
            # Check if we have cached static shell
            if key in ctx.static_cache:
                static_html = ctx.static_cache[key]
            else:
                # Render in static mode first
                static_html = _render_static_shell(fn, args, kwargs, fallback)
                ctx.static_cache[key] = static_html
            
            # For dynamic parts, create boundaries
            result = fn(*args, **kwargs)
            
            return result
        
        wrapper._ppr_enabled = True
        wrapper._ppr_fallback = fallback
        wrapper._ppr_timeout = timeout
        wrapper._ppr_cache_key = cache_key
        
        return wrapper
    
    return decorator


def static_part(fn: Callable[..., T]) -> Callable[..., T]:
    """
    Mark a component as fully static.
    
    This component will be rendered at build time and never re-rendered
    at request time. Use for headers, footers, navigation, etc.
    
    Example:
        @static_part
        def Header():
            return header()[
                Logo(),
                Navigation(),
            ]
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        
        # Mark result as static for PPR
        if hasattr(result, '__ppr_static__'):
            result.__ppr_static__ = True
        
        return result
    
    wrapper._ppr_static = True
    return wrapper


def dynamic_part(
    fallback: Optional[Callable[[], Any]] = None,
    cache: bool = False,
    cache_ttl: int = 60,
):
    """
    Mark a component as dynamic.
    
    This component will be rendered at request time and streamed
    to the client after the static shell.
    
    Args:
        fallback: Loading component to show while this renders
        cache: Whether to cache the result
        cache_ttl: Cache TTL in seconds
    
    Example:
        @dynamic_part(fallback=ProductSkeleton)
        async def ProductDetails(id: str):
            product = await fetch_product(id)
            return div()[
                h1()[product.name],
                p()[product.description],
            ]
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            ctx = get_ppr_context()
            
            # Create boundary
            boundary_id = f"ppr_{uuid.uuid4().hex[:8]}"
            
            # Render fallback as placeholder
            placeholder = ""
            if fallback:
                fb = fallback()
                if hasattr(fb, 'render'):
                    placeholder = fb.render()
                else:
                    placeholder = str(fb)
            else:
                placeholder = '<div class="ppr-loading"></div>'
            
            boundary = PPRBoundary(
                id=boundary_id,
                placeholder_html=placeholder,
            )
            
            if ctx:
                ctx.add_boundary(boundary)
            
            # Return placeholder with data attribute for streaming replacement
            placeholder_html = f'<div data-ppr="{boundary_id}" data-state="pending">{placeholder}</div>'
            
            # Schedule async render
            if inspect.iscoroutinefunction(fn):
                result = await fn(*args, **kwargs)
            else:
                result = fn(*args, **kwargs)
            
            # Render result
            if hasattr(result, 'render'):
                content = result.render()
            else:
                content = str(result)
            
            if ctx:
                ctx.resolve_boundary(boundary_id, content)
            
            return result
        
        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, just render with placeholder
            ctx = get_ppr_context()
            
            boundary_id = f"ppr_{uuid.uuid4().hex[:8]}"
            
            placeholder = ""
            if fallback:
                fb = fallback()
                if hasattr(fb, 'render'):
                    placeholder = fb.render()
                else:
                    placeholder = str(fb)
            
            boundary = PPRBoundary(
                id=boundary_id,
                placeholder_html=placeholder,
            )
            
            if ctx:
                ctx.add_boundary(boundary)
            
            result = fn(*args, **kwargs)
            
            if hasattr(result, 'render'):
                content = result.render()
            else:
                content = str(result)
            
            if ctx:
                ctx.resolve_boundary(boundary_id, content)
            
            return result
        
        if inspect.iscoroutinefunction(fn):
            wrapper = async_wrapper
        else:
            wrapper = sync_wrapper
        
        wrapper._ppr_dynamic = True
        wrapper._ppr_fallback = fallback
        wrapper._ppr_cache = cache
        wrapper._ppr_cache_ttl = cache_ttl
        
        return wrapper
    
    return decorator


# =============================================================================
# PPR Analysis
# =============================================================================

class PPRAnalyzer:
    """
    Analyzes components for PPR optimization.
    
    Determines which parts are static (can be pre-rendered at build)
    and which parts are dynamic (must be rendered at request time).
    """
    
    def __init__(self):
        self._cache: Dict[str, PPRAnalysis] = {}
    
    def analyze(self, fn: Callable) -> PPRAnalysis:
        """Analyze a component function."""
        # Check cache
        fn_id = f"{fn.__module__}.{fn.__qualname__}"
        if fn_id in self._cache:
            return self._cache[fn_id]
        
        # Get source for analysis
        try:
            source = inspect.getsource(fn)
        except (OSError, TypeError):
            source = ""
        
        # Check for signals
        has_signals = self._check_signals(source)
        
        # Check for async
        has_async = inspect.iscoroutinefunction(fn) or 'await ' in source
        
        # Check for request data access
        has_request_data = self._check_request_data(source)
        
        # Analyze parameters
        sig = inspect.signature(fn)
        static_props = set()
        dynamic_props = set()
        
        for param_name, param in sig.parameters.items():
            if param.default is not inspect.Parameter.empty:
                static_props.add(param_name)
            else:
                dynamic_props.add(param_name)
        
        # Determine component type
        if has_signals or has_async or has_request_data:
            component_type = ComponentType.DYNAMIC
        elif dynamic_props:
            component_type = ComponentType.STATIC_SHELL
        else:
            component_type = ComponentType.STATIC
        
        # Check for PPR decorators
        if hasattr(fn, '_ppr_static'):
            component_type = ComponentType.STATIC
        elif hasattr(fn, '_ppr_dynamic'):
            component_type = ComponentType.DYNAMIC
        
        analysis = PPRAnalysis(
            component_type=component_type,
            has_signals=has_signals,
            has_async=has_async,
            has_request_data=has_request_data,
            static_props=static_props,
            dynamic_props=dynamic_props,
            estimated_render_time=self._estimate_render_time(source),
        )
        
        self._cache[fn_id] = analysis
        return analysis
    
    def _check_signals(self, source: str) -> bool:
        """Check if source uses signals."""
        signal_patterns = [
            r'Signal\s*\(',
            r'signal\s*\(',
            r'Effect\s*\(',
            r'effect\s*\(',
            r'Computed\s*\(',
            r'computed\s*\(',
            r'Store\s*\(',
            r'store\s*\(',
            r'create_resource\s*\(',
            r'Resource\s*\(',
        ]
        
        import re
        for pattern in signal_patterns:
            if re.search(pattern, source):
                return True
        return False
    
    def _check_request_data(self, source: str) -> bool:
        """Check if source accesses request data."""
        request_patterns = [
            r'get_params\s*\(',
            r'get_query\s*\(',
            r'request\.',
            r'cookies\.',
            r'headers\.',
        ]
        
        import re
        for pattern in request_patterns:
            if re.search(pattern, source):
                return True
        return False
    
    def _estimate_render_time(self, source: str) -> float:
        """Estimate render time in milliseconds."""
        # Very rough heuristic based on source complexity
        lines = len(source.split('\n'))
        has_async = 'await ' in source
        has_loop = 'for ' in source or 'while ' in source
        
        base = 0.1  # Base render time
        if has_async:
            base += 10.0  # Async operations add latency
        if has_loop:
            base += 1.0  # Loops add complexity
        
        return base + (lines * 0.01)
    
    def is_fully_static(self, fn: Callable) -> bool:
        """Check if component is fully static (no JS needed)."""
        analysis = self.analyze(fn)
        return (
            analysis.component_type == ComponentType.STATIC and
            not analysis.has_signals and
            not analysis.has_async and
            not analysis.has_request_data
        )


# Global analyzer
_ppr_analyzer = PPRAnalyzer()


def get_ppr_analyzer() -> PPRAnalyzer:
    """Get the global PPR analyzer."""
    return _ppr_analyzer


def analyze_component(fn: Callable) -> PPRAnalysis:
    """Analyze a component for PPR."""
    return _ppr_analyzer.analyze(fn)


# =============================================================================
# PPR Rendering
# =============================================================================

def _generate_cache_key(fn: Callable, args: tuple, kwargs: dict) -> str:
    """Generate a cache key for a PPR component."""
    parts = [fn.__module__, fn.__qualname__]
    
    # Add args (only static values)
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            parts.append(str(arg))
    
    # Add kwargs (only static values)
    for key, value in sorted(kwargs.items()):
        if isinstance(value, (str, int, float, bool)):
            parts.append(f"{key}={value}")
    
    return hashlib.md5(":".join(parts).encode()).hexdigest()[:16]


def _render_static_shell(
    fn: Callable,
    args: tuple,
    kwargs: dict,
    fallback: Optional[Callable],
) -> str:
    """Render the static shell of a component."""
    # Create a mock PPR context that captures placeholders
    ctx = PPRContext(mode=PPRMode.STATIC)
    token = _ppr_context.set(ctx)
    
    try:
        result = fn(*args, **kwargs)
        
        if hasattr(result, 'render'):
            html = result.render()
        else:
            html = str(result)
        
        return html
    finally:
        _ppr_context.reset(token)


async def render_ppr_page(
    page_fn: Callable,
    args: tuple = (),
    kwargs: Optional[dict] = None,
    timeout: float = 5.0,
) -> str:
    """
    Render a page with PPR.
    
    Returns complete HTML with all dynamic content resolved.
    """
    kwargs = kwargs or {}
    
    # Create PPR context
    ctx = create_ppr_context(mode=PPRMode.HYBRID)
    
    # Render static shell
    if inspect.iscoroutinefunction(page_fn):
        result = await page_fn(*args, **kwargs)
    else:
        result = page_fn(*args, **kwargs)
    
    if hasattr(result, 'render'):
        html = result.render()
    else:
        html = str(result)
    
    # Wait for all dynamic boundaries to resolve
    try:
        await asyncio.wait_for(
            _wait_for_boundaries(ctx),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        pass  # Use fallbacks for unresolved boundaries
    
    # Replace placeholders with resolved content
    html = _replace_ppr_placeholders(html, ctx)
    
    return html


async def _wait_for_boundaries(ctx: PPRContext) -> None:
    """Wait for all dynamic boundaries to resolve."""
    while ctx.dynamic_pending:
        await asyncio.sleep(0.01)


def _replace_ppr_placeholders(html: str, ctx: PPRContext) -> str:
    """Replace PPR placeholders with resolved content."""
    import re
    
    for boundary_id, boundary in ctx.boundaries.items():
        placeholder_pattern = f'<div data-ppr="{boundary_id}"[^>]*>.*?</div>'
        
        if boundary.is_resolved and boundary.resolved_content:
            replacement = boundary.resolved_content
        else:
            # Keep fallback
            replacement = boundary.placeholder_html
        
        html = re.sub(placeholder_pattern, replacement, html, flags=re.DOTALL)
    
    return html


# =============================================================================
# Streaming Integration
# =============================================================================

async def stream_ppr_page(
    page_fn: Callable,
    args: tuple = (),
    kwargs: Optional[dict] = None,
):
    """
    Stream a PPR page with progressive enhancement.
    
    Yields:
        HTML chunks as content becomes available
    """
    kwargs = kwargs or {}
    
    ctx = create_ppr_context(mode=PPRMode.HYBRID)
    
    # Render and yield static shell immediately
    if inspect.iscoroutinefunction(page_fn):
        result = await page_fn(*args, **kwargs)
    else:
        result = page_fn(*args, **kwargs)
    
    if hasattr(result, 'render'):
        shell_html = result.render()
    else:
        shell_html = str(result)
    
    yield shell_html
    
    # Stream dynamic content as it resolves
    resolved = set()
    
    while len(resolved) < len(ctx.boundaries):
        for boundary_id, boundary in ctx.boundaries.items():
            if boundary_id in resolved:
                continue
            
            if boundary.is_resolved and boundary.resolved_content:
                # Yield replacement script
                content = boundary.resolved_content.replace('`', '\\`').replace('$', '\\$')
                yield f"""
<script>
(function() {{
  var el = document.querySelector('[data-ppr="{boundary_id}"]');
  if (el) {{
    el.outerHTML = `{content}`;
  }}
}})();
</script>
"""
                resolved.add(boundary_id)
        
        await asyncio.sleep(0.01)


# =============================================================================
# PPR Helper Components
# =============================================================================

class StaticShell:
    """
    Component that marks its content as a static shell.
    
    Content inside will be pre-rendered at build time.
    
    Example:
        StaticShell()[
            Header(),
            nav()[links],
        ]
    """
    
    def __init__(self):
        self.children: List[Any] = []
    
    def __getitem__(self, children: Any) -> "StaticShell":
        if isinstance(children, tuple):
            self.children = list(children)
        elif isinstance(children, list):
            self.children = children
        else:
            self.children = [children]
        return self
    
    def render(self) -> str:
        parts = []
        for child in self.children:
            if hasattr(child, 'render'):
                parts.append(child.render())
            elif callable(child):
                result = child()
                if hasattr(result, 'render'):
                    parts.append(result.render())
                else:
                    parts.append(str(result))
            else:
                parts.append(str(child))
        
        return "".join(parts)


class DynamicHole:
    """
    Component that marks a dynamic content hole.
    
    Content will be streamed after the static shell.
    
    Example:
        DynamicHole(fallback=ProductSkeleton)[
            ProductDetails(id=product_id)
        ]
    """
    
    def __init__(
        self,
        fallback: Optional[Callable[[], Any]] = None,
        id: Optional[str] = None,
    ):
        self.fallback = fallback
        self.id = id or f"hole_{uuid.uuid4().hex[:8]}"
        self.children: List[Any] = []
    
    def __getitem__(self, children: Any) -> "DynamicHole":
        if isinstance(children, tuple):
            self.children = list(children)
        elif isinstance(children, list):
            self.children = children
        else:
            self.children = [children]
        return self
    
    def render(self) -> str:
        ctx = get_ppr_context()
        
        # Render fallback
        fallback_html = ""
        if self.fallback:
            fb = self.fallback()
            if hasattr(fb, 'render'):
                fallback_html = fb.render()
            else:
                fallback_html = str(fb)
        else:
            fallback_html = '<div class="ppr-skeleton"></div>'
        
        # Create boundary
        boundary = PPRBoundary(
            id=self.id,
            placeholder_html=fallback_html,
        )
        
        if ctx:
            ctx.add_boundary(boundary)
        
        # Return placeholder
        return f'<div data-ppr="{self.id}" data-state="pending">{fallback_html}</div>'
    
    async def resolve(self) -> str:
        """Resolve the dynamic content."""
        ctx = get_ppr_context()
        
        # Render children
        parts = []
        for child in self.children:
            if hasattr(child, 'render'):
                parts.append(child.render())
            elif inspect.iscoroutinefunction(child):
                result = await child()
                if hasattr(result, 'render'):
                    parts.append(result.render())
                else:
                    parts.append(str(result))
            elif callable(child):
                result = child()
                if hasattr(result, 'render'):
                    parts.append(result.render())
                else:
                    parts.append(str(result))
            else:
                parts.append(str(child))
        
        content = "".join(parts)
        
        if ctx:
            ctx.resolve_boundary(self.id, content)
        
        return content


# =============================================================================
# Client Runtime for PPR
# =============================================================================

def get_ppr_runtime_js() -> str:
    """
    Get minimal JS runtime for PPR client-side updates.
    
    This is only needed if the page has dynamic holes.
    """
    return """
(function() {
  // PPR client runtime
  window.__pynext__ = window.__pynext__ || {};
  window.__pynext__.ppr = {
    // Resolve a PPR boundary with new content
    resolve: function(id, content) {
      var el = document.querySelector('[data-ppr="' + id + '"]');
      if (el) {
        var temp = document.createElement('div');
        temp.innerHTML = content;
        el.replaceWith(temp.firstElementChild || temp.firstChild);
      }
    },
    
    // Mark boundary as loading
    setLoading: function(id) {
      var el = document.querySelector('[data-ppr="' + id + '"]');
      if (el) {
        el.setAttribute('data-state', 'loading');
      }
    },
    
    // Mark boundary as error
    setError: function(id, message) {
      var el = document.querySelector('[data-ppr="' + id + '"]');
      if (el) {
        el.setAttribute('data-state', 'error');
        el.innerHTML = '<div class="ppr-error">' + message + '</div>';
      }
    }
  };
})();
"""


def needs_ppr_runtime() -> bool:
    """Check if the current page needs PPR runtime."""
    ctx = get_ppr_context()
    return ctx is not None and len(ctx.boundaries) > 0

