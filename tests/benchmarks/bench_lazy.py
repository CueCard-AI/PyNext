"""
Benchmarks for PyNext Lazy Loading & Code Splitting.

Measures:
1. Lazy component creation overhead
2. Chunk URL generation
3. Hydration script generation
4. Route chunk analysis
5. Bundle size estimation

Run with:
    python -m pytest tests/benchmarks/bench_lazy.py -v --benchmark-only
"""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import MagicMock

from pynext.core.lazy import (
    lazy,
    lazy_route,
    LazyComponent,
    LazyBoundary,
    LoadingState,
    PrefetchStrategy,
    RouteBundler,
    LazyRegistry,
    import_component,
    prefetch_link,
    generate_lazy_scripts,
)
from pynext.core.html import div, button, span, section, article, h1, p
from pynext.bundler.route_chunks import RouteChunkGenerator, RouteChunkInfo


# =============================================================================
# Lazy Component Creation Benchmarks
# =============================================================================

class TestLazyCreationBenchmarks:
    """Benchmarks for lazy component creation."""
    
    def test_lazy_creation(self, benchmark):
        """Create a lazy component."""
        def create():
            return lazy(lambda: div()["Content"])
        
        result = benchmark(create)
        assert isinstance(result, LazyComponent)
    
    def test_lazy_with_options(self, benchmark):
        """Create lazy with all options."""
        def create():
            return lazy(
                lambda: div()["Content"],
                name="CustomName",
                preload=False,
                chunk_name="custom-chunk"
            )
        
        result = benchmark(create)
        assert result.metadata.name == "CustomName"
    
    def test_lazy_call(self, benchmark):
        """Call lazy component to get boundary."""
        comp = lazy(lambda: div()["Test"])
        
        def call():
            return comp(id="test", count=42)
        
        result = benchmark(call)
        assert isinstance(result, LazyBoundary)
    
    def test_multiple_lazy_creation(self, benchmark):
        """Create multiple lazy components."""
        def create_many():
            return [lazy(lambda i=i: div()[f"Component {i}"]) for i in range(10)]
        
        result = benchmark(create_many)
        assert len(result) == 10


# =============================================================================
# Lazy Boundary Rendering Benchmarks
# =============================================================================

class TestLazyRenderingBenchmarks:
    """Benchmarks for lazy boundary rendering."""
    
    def test_placeholder_render(self, benchmark):
        """Render placeholder (not loaded)."""
        comp = lazy(lambda: div()["Content"], chunk_name="test")
        boundary = comp()
        
        def render():
            return boundary.render()
        
        html = benchmark(render)
        assert "data-lazy=" in html
    
    def test_placeholder_with_fallback(self, benchmark):
        """Render placeholder with custom fallback."""
        comp = lazy(lambda: div()["Content"])
        boundary = LazyBoundary(
            lazy_component=comp,
            fallback=span()["Loading..."]
        )
        
        def render():
            return boundary.render()
        
        html = benchmark(render)
        assert "Loading..." in html
    
    @pytest.mark.asyncio
    async def test_loaded_render(self, benchmark):
        """Render loaded component."""
        def MyComponent():
            return div()["Loaded Content"]
        
        comp = lazy(lambda: MyComponent)
        await comp.load()
        boundary = comp()
        
        def render():
            return boundary.render()
        
        html = benchmark(render)
        assert "Loaded Content" in html


# =============================================================================
# Chunk URL Generation Benchmarks
# =============================================================================

class TestChunkURLBenchmarks:
    """Benchmarks for chunk URL generation."""
    
    def test_chunk_url(self, benchmark):
        """Generate chunk URL."""
        comp = lazy(lambda: div(), chunk_name="dashboard")
        
        def get_url():
            return comp.get_chunk_url()
        
        url = benchmark(get_url)
        assert "dashboard.js" in url
    
    def test_preload_tag(self, benchmark):
        """Generate preload tag."""
        comp = lazy(lambda: div(), chunk_name="widgets")
        
        def get_tag():
            return comp.get_preload_tag()
        
        tag = benchmark(get_tag)
        assert 'rel="modulepreload"' in tag


# =============================================================================
# Hydration Script Benchmarks
# =============================================================================

class TestHydrationScriptBenchmarks:
    """Benchmarks for hydration script generation."""
    
    def test_single_script(self, benchmark):
        """Generate script for single component."""
        comp = lazy(lambda: div(), chunk_name="test")
        boundary = comp(id="widget")
        
        def generate():
            return boundary.get_hydration_script()
        
        script = benchmark(generate)
        assert "registerLazy" in script
    
    def test_multiple_scripts(self, benchmark):
        """Generate scripts for multiple components."""
        comps = [lazy(lambda: div(), chunk_name=f"chunk-{i}") for i in range(10)]
        
        def generate():
            return generate_lazy_scripts(comps)
        
        script = benchmark(generate)
        assert script.count("registerLazy") == 10


# =============================================================================
# Route Bundler Benchmarks
# =============================================================================

class TestRouteBundlerBenchmarks:
    """Benchmarks for route bundler."""
    
    def test_bundler_creation(self, benchmark):
        """Create route bundler."""
        def create():
            return RouteBundler(output_dir=Path("/tmp/chunks"))
        
        bundler = benchmark(create)
        assert bundler.output_dir == Path("/tmp/chunks")
    
    def test_route_to_chunk_name(self, benchmark):
        """Convert route to chunk name."""
        bundler = RouteBundler(output_dir=Path("/tmp"))
        
        routes = [
            "/",
            "/dashboard",
            "/users/[id]",
            "/posts/[...slug]",
            "/admin/settings/profile",
        ]
        
        def convert():
            return [bundler._route_to_chunk_name(r) for r in routes]
        
        names = benchmark(convert)
        assert len(names) == 5
    
    def test_generate_chunk(self, benchmark):
        """Generate a single chunk."""
        bundler = RouteBundler(output_dir=Path("/tmp/test-chunks"))
        
        def generate():
            return bundler.generate_chunk("/dashboard", {"module.dashboard"})
        
        chunk = benchmark(generate)
        assert chunk.route == "/dashboard"


# =============================================================================
# Registry Benchmarks
# =============================================================================

class TestRegistryBenchmarks:
    """Benchmarks for lazy registry."""
    
    def test_register(self, benchmark):
        """Register a lazy component."""
        registry = LazyRegistry()
        
        def register():
            comp = lazy(lambda: div())
            registry.register(comp)
            return comp
        
        comp = benchmark(register)
        assert registry.get(comp.id) is comp
    
    def test_get(self, benchmark):
        """Get a registered component."""
        registry = LazyRegistry()
        comp = lazy(lambda: div())
        registry.register(comp)
        
        def get():
            return registry.get(comp.id)
        
        result = benchmark(get)
        assert result is comp
    
    def test_get_all(self, benchmark):
        """Get all registered components."""
        registry = LazyRegistry()
        for i in range(100):
            comp = lazy(lambda i=i: div()[f"Comp {i}"])
            registry.register(comp)
        
        def get_all():
            return registry.get_all()
        
        all_comps = benchmark(get_all)
        assert len(all_comps) == 100


# =============================================================================
# Prefetch Link Benchmarks
# =============================================================================

class TestPrefetchBenchmarks:
    """Benchmarks for prefetch utilities."""
    
    def test_prefetch_link(self, benchmark):
        """Generate prefetch link attributes."""
        def generate():
            return prefetch_link("/dashboard", strategy=PrefetchStrategy.HOVER)
        
        attrs = benchmark(generate)
        assert attrs["data-prefetch"] == "hover"
    
    def test_prefetch_all_strategies(self, benchmark):
        """Generate prefetch for all strategies."""
        def generate_all():
            return [
                prefetch_link("/page", strategy=s)
                for s in PrefetchStrategy
            ]
        
        results = benchmark(generate_all)
        assert len(results) == 4


# =============================================================================
# Async Loading Benchmarks
# =============================================================================

class TestAsyncBenchmarks:
    """Benchmarks for async loading."""
    
    @pytest.mark.asyncio
    async def test_load_simple(self, benchmark):
        """Load a simple component."""
        def MyComponent():
            return div()["Simple"]
        
        comp = lazy(lambda: MyComponent)
        
        async def load():
            return await comp.load()
        
        # Can't use benchmark with async directly
        result = await load()
        assert result is MyComponent
    
    @pytest.mark.asyncio
    async def test_load_cached(self, benchmark):
        """Load a cached component."""
        def MyComponent():
            return div()["Cached"]
        
        comp = lazy(lambda: MyComponent)
        await comp.load()  # First load
        
        async def load_again():
            return await comp.load()
        
        result = await load_again()
        assert result is MyComponent


# =============================================================================
# Route Chunk Info Benchmarks
# =============================================================================

class TestRouteChunkInfoBenchmarks:
    """Benchmarks for RouteChunkInfo operations."""
    
    def test_chunk_info_creation(self, benchmark):
        """Create RouteChunkInfo."""
        def create():
            return RouteChunkInfo(
                route="/dashboard",
                chunk_name="dashboard",
                needs_signals=True,
                needs_resource=True,
            )
        
        info = benchmark(create)
        assert info.route == "/dashboard"
    
    def test_chunk_info_serialization(self, benchmark):
        """Serialize chunk info to JSON."""
        info = RouteChunkInfo(
            route="/dashboard",
            chunk_name="dashboard",
            needs_signals=True,
            needs_resource=True,
            size=1024,
            hash="abc12345",
        )
        
        def serialize():
            return json.dumps({
                "route": info.route,
                "chunk": info.chunk_name,
                "size": info.size,
                "hash": info.hash,
            })
        
        data = benchmark(serialize)
        assert '"route"' in data


# =============================================================================
# Payload Size Analysis
# =============================================================================

class TestPayloadSizeBenchmarks:
    """Analyze payload sizes for lazy loading."""
    
    def test_lazy_boundary_html_size(self):
        """Measure lazy boundary HTML size."""
        comp = lazy(lambda: div()["Content"], chunk_name="widget")
        boundary = comp()
        html = boundary.render()
        
        size = len(html.encode('utf-8'))
        print(f"\nLazy boundary HTML: {size} bytes")
        
        assert size < 500  # Should be compact
    
    def test_hydration_script_size(self):
        """Measure hydration script size."""
        comp = lazy(lambda: div(), chunk_name="widget")
        boundary = comp(id="test")
        script = boundary.get_hydration_script()
        
        size = len(script.encode('utf-8'))
        print(f"\nSingle lazy script: {size} bytes")
        
        assert size < 300
    
    def test_multiple_lazy_script_size(self):
        """Measure script size for multiple components."""
        comps = [lazy(lambda: div(), chunk_name=f"chunk-{i}") for i in range(10)]
        script = generate_lazy_scripts(comps)
        
        size = len(script.encode('utf-8'))
        print(f"\n10 lazy components script: {size} bytes")
        
        assert size < 3000
    
    def test_overhead_comparison(self):
        """Compare lazy vs static overhead."""
        # Static
        static_html = div()["Hello World"].render()
        static_size = len(static_html.encode('utf-8'))
        
        # Lazy
        comp = lazy(lambda: div()["Hello World"], chunk_name="hello")
        boundary = comp()
        lazy_html = boundary.render()
        lazy_size = len(lazy_html.encode('utf-8'))
        
        script = boundary.get_hydration_script()
        script_size = len(script.encode('utf-8'))
        
        total_lazy = lazy_size + script_size
        overhead = total_lazy - static_size
        
        print(f"\nStatic: {static_size} bytes")
        print(f"Lazy HTML: {lazy_size} bytes")
        print(f"Lazy Script: {script_size} bytes")
        print(f"Total Lazy: {total_lazy} bytes")
        print(f"Overhead: {overhead} bytes")


# =============================================================================
# Real-World Scenario Benchmarks
# =============================================================================

class TestRealWorldBenchmarks:
    """Benchmark real-world usage patterns."""
    
    def test_dashboard_with_lazy_widgets(self, benchmark):
        """Dashboard page with lazy-loaded widgets."""
        # Create lazy widgets
        UserWidget = lazy(lambda: div()["User Info"], chunk_name="widgets/user")
        ChartWidget = lazy(lambda: div()["Charts"], chunk_name="widgets/chart")
        StatsWidget = lazy(lambda: div()["Statistics"], chunk_name="widgets/stats")
        
        def render_dashboard():
            return div()[
                h1()["Dashboard"],
                section()[
                    UserWidget(),
                    ChartWidget(),
                    StatsWidget(),
                ],
                p()["Footer"],
            ].render()
        
        html = benchmark(render_dashboard)
        assert "Dashboard" in html
    
    def test_blog_with_lazy_comments(self, benchmark):
        """Blog page with lazy-loaded comments section."""
        # Comments are heavy, load lazily
        CommentsSection = lazy(
            lambda: div()["Comments..."],
            chunk_name="blog/comments"
        )
        
        def render_blog():
            content = article()[
                h1()["Blog Post"],
                p()["Lorem ipsum " * 50],
                div()["Share buttons"],
                CommentsSection(),  # Lazy
            ].render()
            return content
        
        html = benchmark(render_blog)
        assert "Blog Post" in html
    
    def test_prefetch_many_routes(self, benchmark):
        """Generate prefetch hints for many routes."""
        routes = [f"/page-{i}" for i in range(20)]
        
        def generate_hints():
            return [
                prefetch_link(route, strategy=PrefetchStrategy.IDLE)
                for route in routes
            ]
        
        hints = benchmark(generate_hints)
        assert len(hints) == 20


# =============================================================================
# Summary Stats
# =============================================================================

def test_print_summary_stats():
    """Print summary statistics for lazy loading."""
    print("\n" + "=" * 70)
    print("LAZY LOADING - PERFORMANCE SUMMARY")
    print("=" * 70)
    
    # Component creation overhead
    import time
    
    start = time.perf_counter()
    for _ in range(1000):
        lazy(lambda: div())
    creation_time = (time.perf_counter() - start) * 1000
    
    print(f"\n1000 lazy() calls: {creation_time:.2f}ms ({creation_time/1000*1000:.2f}μs/call)")
    
    # Boundary rendering
    comp = lazy(lambda: div(), chunk_name="test")
    
    start = time.perf_counter()
    for _ in range(1000):
        comp().render()
    render_time = (time.perf_counter() - start) * 1000
    
    print(f"1000 boundary renders: {render_time:.2f}ms ({render_time/1000*1000:.2f}μs/render)")
    
    # Script generation
    comps = [lazy(lambda: div(), chunk_name=f"c{i}") for i in range(10)]
    
    start = time.perf_counter()
    for _ in range(100):
        generate_lazy_scripts(comps)
    script_time = (time.perf_counter() - start) * 1000
    
    print(f"100 script generations (10 components each): {script_time:.2f}ms")
    
    # Size analysis
    single_script = comps[0]().get_hydration_script()
    all_scripts = generate_lazy_scripts(comps)
    
    print(f"\nSingle component script: {len(single_script)} bytes")
    print(f"10 component script: {len(all_scripts)} bytes")
    print(f"Per-component overhead: {(len(all_scripts) - len('<script>...</script>')) // 10} bytes")
    
    print("\nPrefetch Strategies:")
    for strategy in PrefetchStrategy:
        print(f"  - {strategy.value}")
    
    print("\n" + "=" * 70)

