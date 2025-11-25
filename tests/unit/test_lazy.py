"""
Unit tests for PyNext Lazy Loading (Code Splitting).

Tests cover:
- lazy() function
- LazyComponent class
- LazyBoundary rendering
- lazy_route decorator
- Prefetch strategies
- Route bundling
"""

import pytest
import asyncio
from pynext.core.lazy import (
    lazy,
    lazy_route,
    LazyComponent,
    LazyBoundary,
    LazyMetadata,
    LoadingState,
    PrefetchStrategy,
    PrefetchConfig,
    RouteBundler,
    RouteChunk,
    LazyRegistry,
    import_component,
    prefetch_link,
    get_lazy_registry,
    generate_lazy_scripts,
)
from pynext.core.html import div, button, span
from pathlib import Path


class TestLazyFunction:
    """Tests for lazy() factory function."""
    
    def test_basic_lazy(self):
        """Create a basic lazy component."""
        def SimpleComponent():
            return div()["Simple"]
        
        lazy_comp = lazy(lambda: SimpleComponent)
        
        assert isinstance(lazy_comp, LazyComponent)
        assert lazy_comp.state == LoadingState.IDLE
        assert lazy_comp.component is None
    
    def test_lazy_with_name(self):
        """Lazy component with custom name."""
        lazy_comp = lazy(
            lambda: div()["Test"],
            name="TestComponent"
        )
        
        assert lazy_comp.metadata.name == "TestComponent"
    
    def test_lazy_with_preload(self):
        """Lazy component with preload enabled."""
        lazy_comp = lazy(
            lambda: div()["Preload"],
            preload=True
        )
        
        assert lazy_comp.metadata.preload is True
    
    def test_lazy_with_chunk_name(self):
        """Lazy component with custom chunk name."""
        lazy_comp = lazy(
            lambda: div()["Chunk"],
            chunk_name="custom-chunk"
        )
        
        assert lazy_comp.metadata.chunk_name == "custom-chunk"
    
    def test_lazy_unique_ids(self):
        """Each lazy component gets unique ID."""
        lazy1 = lazy(lambda: div()["1"])
        lazy2 = lazy(lambda: div()["2"])
        
        assert lazy1.id != lazy2.id


class TestLazyComponent:
    """Tests for LazyComponent class."""
    
    def test_lazy_call_returns_boundary(self):
        """Calling lazy component returns LazyBoundary."""
        lazy_comp = lazy(lambda: div()["Test"])
        
        result = lazy_comp()
        
        assert isinstance(result, LazyBoundary)
        assert result.lazy_component is lazy_comp
    
    def test_lazy_call_with_args(self):
        """Lazy component call captures arguments."""
        lazy_comp = lazy(lambda: div()["Test"])
        
        result = lazy_comp("arg1", kwarg1="value1")
        
        assert result.args == ("arg1",)
        assert result.kwargs == {"kwarg1": "value1"}
    
    @pytest.mark.asyncio
    async def test_lazy_load(self):
        """Load a lazy component."""
        def MyComponent():
            return div()["Loaded"]
        
        lazy_comp = lazy(lambda: MyComponent)
        
        result = await lazy_comp.load()
        
        assert lazy_comp.state == LoadingState.LOADED
        assert lazy_comp.component is MyComponent
        assert result is MyComponent
    
    @pytest.mark.asyncio
    async def test_lazy_load_deduplication(self):
        """Multiple load calls are deduplicated."""
        call_count = 0
        
        def MyComponent():
            nonlocal call_count
            call_count += 1
            return div()["Test"]
        
        lazy_comp = lazy(lambda: MyComponent())
        
        # Start multiple loads
        await asyncio.gather(
            lazy_comp.load(),
            lazy_comp.load(),
            lazy_comp.load(),
        )
        
        # Loader should only be called once
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_lazy_load_cached(self):
        """Loaded component is cached."""
        lazy_comp = lazy(lambda: div()["Cached"])
        
        result1 = await lazy_comp.load()
        result2 = await lazy_comp.load()
        
        assert result1 is result2
    
    @pytest.mark.asyncio
    async def test_lazy_load_error(self):
        """Error during load is captured."""
        def failing_loader():
            raise ValueError("Load failed")
        
        lazy_comp = lazy(failing_loader)
        
        with pytest.raises(ValueError):
            await lazy_comp.load()
        
        assert lazy_comp.state == LoadingState.ERROR
        assert lazy_comp.error is not None
    
    def test_lazy_chunk_url(self):
        """Get chunk URL for component."""
        lazy_comp = lazy(lambda: div(), chunk_name="my-chunk")
        
        url = lazy_comp.get_chunk_url()
        
        assert url == "/__pynext__/chunks/my-chunk.js"
    
    def test_lazy_preload_tag(self):
        """Get preload tag for component."""
        lazy_comp = lazy(lambda: div(), chunk_name="preload-test")
        
        tag = lazy_comp.get_preload_tag()
        
        assert 'rel="modulepreload"' in tag
        assert "preload-test.js" in tag


class TestLazyBoundary:
    """Tests for LazyBoundary rendering."""
    
    def test_render_placeholder(self):
        """Render placeholder when not loaded."""
        lazy_comp = lazy(lambda: div()["Content"])
        boundary = lazy_comp()
        
        html = boundary.render()
        
        assert "data-lazy=" in html
        assert "data-state=\"idle\"" in html
        assert "data-lazy-fallback" in html
    
    def test_render_custom_fallback(self):
        """Render with custom fallback."""
        lazy_comp = lazy(lambda: div()["Content"])
        boundary = LazyBoundary(
            lazy_component=lazy_comp,
            fallback=span()["Custom loading..."]
        )
        
        html = boundary.render()
        
        assert "Custom loading..." in html
    
    @pytest.mark.asyncio
    async def test_render_loaded(self):
        """Render loaded component."""
        def MyComponent():
            return div()["Loaded Content"]
        
        lazy_comp = lazy(lambda: MyComponent)
        await lazy_comp.load()
        
        boundary = lazy_comp()
        html = boundary.render()
        
        assert "Loaded Content" in html
    
    def test_hydration_script(self):
        """Generate hydration script."""
        lazy_comp = lazy(lambda: div(), chunk_name="test-chunk")
        boundary = lazy_comp(name="Test")
        
        script = boundary.get_hydration_script()
        
        assert "__pynext__.registerLazy" in script
        assert lazy_comp.id in script
        assert '"name": "Test"' in script


class TestLazyRoute:
    """Tests for lazy_route decorator."""
    
    def test_lazy_route_basic(self):
        """Basic lazy route creation."""
        @lazy_route("/dashboard")
        def DashboardPage():
            return div()["Dashboard"]
        
        assert isinstance(DashboardPage, LazyComponent)
        assert DashboardPage.metadata.chunk_name == "dashboard"
    
    def test_lazy_route_with_preload(self):
        """Lazy route with preloading."""
        @lazy_route("/critical", preload=True)
        def CriticalPage():
            return div()["Critical"]
        
        assert CriticalPage.metadata.preload is True
    
    def test_lazy_route_nested_path(self):
        """Lazy route with nested path."""
        @lazy_route("/users/profile")
        def ProfilePage():
            return div()["Profile"]
        
        assert ProfilePage.metadata.chunk_name == "users-profile"
    
    def test_lazy_route_registered(self):
        """Lazy route is registered globally."""
        registry = get_lazy_registry()
        initial_count = len(registry.get_all())
        
        @lazy_route("/new-page")
        def NewPage():
            return div()["New"]
        
        assert len(registry.get_all()) == initial_count + 1


class TestPrefetchStrategies:
    """Tests for prefetch strategies."""
    
    def test_prefetch_hover(self):
        """Prefetch on hover."""
        attrs = prefetch_link("/page", strategy=PrefetchStrategy.HOVER)
        
        assert attrs["data-prefetch"] == "hover"
        assert attrs["href"] == "/page"
    
    def test_prefetch_visible(self):
        """Prefetch when visible."""
        attrs = prefetch_link("/page", strategy=PrefetchStrategy.VISIBLE)
        
        assert attrs["data-prefetch"] == "visible"
    
    def test_prefetch_idle(self):
        """Prefetch when idle."""
        attrs = prefetch_link("/page", strategy=PrefetchStrategy.IDLE)
        
        assert attrs["data-prefetch"] == "idle"
    
    def test_prefetch_none(self):
        """No prefetching."""
        attrs = prefetch_link("/page", strategy=PrefetchStrategy.NONE)
        
        assert attrs["data-prefetch"] == "none"
    
    def test_prefetch_config(self):
        """Prefetch configuration."""
        config = PrefetchConfig(
            default_strategy=PrefetchStrategy.VISIBLE,
            always_prefetch=["/dashboard", "/home"],
            never_prefetch=["/admin"],
            max_concurrent=3
        )
        
        assert config.default_strategy == PrefetchStrategy.VISIBLE
        assert len(config.always_prefetch) == 2
        assert config.max_concurrent == 3


class TestRouteBundler:
    """Tests for route-based bundling."""
    
    def test_bundler_creation(self):
        """Create route bundler."""
        bundler = RouteBundler(output_dir=Path("/tmp/chunks"))
        
        assert bundler.output_dir == Path("/tmp/chunks")
        assert len(bundler.chunks) == 0
    
    def test_analyze_route(self):
        """Analyze route dependencies."""
        bundler = RouteBundler(output_dir=Path("/tmp"))
        
        def MyComponent():
            return div()["Test"]
        
        deps = bundler.analyze_route("/test", MyComponent)
        
        # Should include component's module
        assert isinstance(deps, set)
    
    def test_generate_chunk(self):
        """Generate route chunk."""
        bundler = RouteBundler(output_dir=Path("/tmp/chunks"))
        
        chunk = bundler.generate_chunk("/dashboard", {"module.dashboard"})
        
        assert isinstance(chunk, RouteChunk)
        assert chunk.route == "/dashboard"
        assert chunk.chunk_path == Path("/tmp/chunks/dashboard.js")
    
    def test_route_to_chunk_name(self):
        """Convert route to chunk name."""
        bundler = RouteBundler(output_dir=Path("/tmp"))
        
        assert bundler._route_to_chunk_name("/") == "index"
        assert bundler._route_to_chunk_name("/dashboard") == "dashboard"
        assert bundler._route_to_chunk_name("/users/profile") == "users-profile"
        assert bundler._route_to_chunk_name("/users/[id]") == "users-id"
    
    def test_get_preload_hints(self):
        """Get preload hints for route."""
        bundler = RouteBundler(output_dir=Path("/tmp"))
        bundler.generate_chunk("/", set())
        
        hints = bundler.get_preload_hints("/")
        
        assert isinstance(hints, list)


class TestLazyRegistry:
    """Tests for LazyRegistry."""
    
    def test_registry_register(self):
        """Register lazy component."""
        registry = LazyRegistry()
        lazy_comp = lazy(lambda: div())
        
        registry.register(lazy_comp)
        
        assert registry.get(lazy_comp.id) is lazy_comp
    
    def test_registry_get_all(self):
        """Get all registered components."""
        registry = LazyRegistry()
        comp1 = lazy(lambda: div()["1"])
        comp2 = lazy(lambda: div()["2"])
        
        registry.register(comp1)
        registry.register(comp2)
        
        all_comps = registry.get_all()
        
        assert len(all_comps) == 2
    
    def test_registry_chunk_grouping(self):
        """Components grouped by chunk."""
        registry = LazyRegistry()
        
        comp1 = lazy(lambda: div(), chunk_name="chunk-a")
        comp2 = lazy(lambda: div(), chunk_name="chunk-a")
        comp3 = lazy(lambda: div(), chunk_name="chunk-b")
        
        registry.register(comp1)
        registry.register(comp2)
        registry.register(comp3)
        
        chunk_a = registry.get_chunk_components("chunk-a")
        chunk_b = registry.get_chunk_components("chunk-b")
        
        assert len(chunk_a) == 2
        assert len(chunk_b) == 1


class TestImportComponent:
    """Tests for import_component helper."""
    
    def test_import_builtin(self):
        """Import a built-in module."""
        # This should work with standard library
        json_module = import_component("json")
        
        assert json_module is not None
    
    def test_import_with_component_name(self):
        """Import specific name from module."""
        loads = import_component("json", "loads")
        
        assert callable(loads)


class TestGenerateLazyScripts:
    """Tests for script generation."""
    
    def test_empty_list(self):
        """No scripts for empty list."""
        script = generate_lazy_scripts([])
        
        assert script == ""
    
    def test_single_component(self):
        """Generate script for single component."""
        lazy_comp = lazy(lambda: div(), chunk_name="test")
        
        script = generate_lazy_scripts([lazy_comp])
        
        assert "<script>" in script
        assert "__pynext__.registerLazy" in script
        assert "__pynext__.initLazyLoading()" in script
    
    def test_multiple_components(self):
        """Generate script for multiple components."""
        comps = [
            lazy(lambda: div(), chunk_name=f"chunk-{i}")
            for i in range(5)
        ]
        
        script = generate_lazy_scripts(comps)
        
        # Should have registrations for all
        assert script.count("registerLazy") == 5


class TestLoadingState:
    """Tests for LoadingState enum."""
    
    def test_all_states(self):
        """All loading states defined."""
        assert LoadingState.IDLE.value == "idle"
        assert LoadingState.LOADING.value == "loading"
        assert LoadingState.LOADED.value == "loaded"
        assert LoadingState.ERROR.value == "error"


class TestPrefetchStrategy:
    """Tests for PrefetchStrategy enum."""
    
    def test_all_strategies(self):
        """All prefetch strategies defined."""
        assert PrefetchStrategy.HOVER.value == "hover"
        assert PrefetchStrategy.VISIBLE.value == "visible"
        assert PrefetchStrategy.IDLE.value == "idle"
        assert PrefetchStrategy.NONE.value == "none"

