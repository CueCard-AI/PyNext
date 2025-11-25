"""
Benchmark tests for PyNext routing performance.

Tracks route matching speed and scalability.
Compares trie-based O(1) matching vs linear O(n) matching.
"""

import pytest
from pathlib import Path
from pynext.router.file_router import FileRouter
from pynext.router.dynamic import file_path_to_route, match_route
from pynext.router.trie import RouteTrie, LayoutCache


@pytest.mark.benchmark
class TestRouteMatchingBenchmarks:
    """Benchmarks for route matching."""
    
    def test_static_route_match(self, benchmark):
        """Benchmark matching a static route."""
        pattern = file_path_to_route("about.py")
        
        result = benchmark(match_route, "/about", pattern)
        
        assert result is not None
    
    def test_dynamic_route_match(self, benchmark):
        """Benchmark matching a dynamic route."""
        pattern = file_path_to_route("users/[id].py")
        
        result = benchmark(match_route, "/users/123", pattern)
        
        assert result is not None
        assert result["id"] == "123"
    
    def test_catch_all_route_match(self, benchmark):
        """Benchmark matching a catch-all route."""
        pattern = file_path_to_route("docs/[...slug].py")
        
        result = benchmark(match_route, "/docs/api/reference/signals", pattern)
        
        assert result is not None
    
    def test_deep_nested_route(self, benchmark):
        """Benchmark matching a deeply nested route."""
        pattern = file_path_to_route("a/b/c/d/e/[id].py")
        
        result = benchmark(match_route, "/a/b/c/d/e/123", pattern)
        
        assert result is not None


@pytest.mark.benchmark
class TestRouterBenchmarks:
    """Benchmarks for FileRouter operations."""
    
    @pytest.fixture
    def router_100_routes(self, large_route_set):
        """Router with 100+ routes."""
        router = FileRouter(str(large_route_set))
        router.scan()
        return router
    
    def test_router_scan_performance(self, benchmark, large_route_set):
        """Benchmark scanning a large pages directory."""
        def scan():
            router = FileRouter(str(large_route_set))
            router.scan()
            return router
        
        router = benchmark(scan)
        
        assert len(router.routes) > 100
    
    def test_router_match_first_route(self, benchmark, router_100_routes):
        """Benchmark matching the first route (best case)."""
        # Get the first route pattern
        first_route = router_100_routes.routes[0]
        path = first_route.pattern.url_pattern
        
        result = benchmark(router_100_routes.match, path)
        
        assert result[0] is not None
    
    def test_router_match_last_route(self, benchmark, router_100_routes):
        """Benchmark matching the last route (worst case)."""
        # Get the last route pattern - will scan all routes
        last_route = router_100_routes.routes[-1]
        path = last_route.pattern.url_pattern
        
        result = benchmark(router_100_routes.match, path)
        
        assert result[0] is not None
    
    def test_router_no_match(self, benchmark, router_100_routes):
        """Benchmark when no route matches (worst case)."""
        result = benchmark(router_100_routes.match, "/nonexistent/deep/path")
        
        assert result[0] is None


@pytest.mark.benchmark
class TestRoutePatternBenchmarks:
    """Benchmarks for route pattern creation."""
    
    def test_create_static_pattern(self, benchmark):
        """Benchmark creating a static route pattern."""
        result = benchmark(file_path_to_route, "about.py")
        
        assert result is not None
    
    def test_create_dynamic_pattern(self, benchmark):
        """Benchmark creating a dynamic route pattern."""
        result = benchmark(file_path_to_route, "users/[id]/posts/[postId].py")
        
        assert result is not None
    
    def test_create_catch_all_pattern(self, benchmark):
        """Benchmark creating a catch-all route pattern."""
        result = benchmark(file_path_to_route, "docs/[...slug].py")
        
        assert result is not None


@pytest.mark.benchmark
class TestTrieVsLinearBenchmarks:
    """Benchmarks comparing trie vs linear route matching."""
    
    @pytest.fixture
    def trie_100_routes(self):
        """Create a trie with 100 routes."""
        trie = RouteTrie()
        
        # 50 static routes
        for i in range(50):
            trie.insert(f"/static/page{i}", f"handler_{i}")
        
        # 30 dynamic routes
        for i in range(30):
            trie.insert(f"/dynamic/section{i}/:id", f"dynamic_{i}")
        
        # 20 nested routes
        for i in range(20):
            trie.insert(f"/nested/level1/level2/page{i}", f"nested_{i}")
        
        return trie
    
    @pytest.fixture
    def linear_100_patterns(self):
        """Create 100 route patterns for linear matching."""
        patterns = []
        
        # 50 static routes
        for i in range(50):
            patterns.append(file_path_to_route(f"static/page{i}.py"))
        
        # 30 dynamic routes
        for i in range(30):
            patterns.append(file_path_to_route(f"dynamic/section{i}/[id].py"))
        
        # 20 nested routes
        for i in range(20):
            patterns.append(file_path_to_route(f"nested/level1/level2/page{i}.py"))
        
        return patterns
    
    def test_trie_static_match_100_routes(self, benchmark, trie_100_routes):
        """Benchmark trie matching static route (100 routes)."""
        # Match a route in the middle
        result = benchmark(trie_100_routes.match, "/static/page25")
        
        assert result[0] == "handler_25"
    
    def test_linear_static_match_100_routes(self, benchmark, linear_100_patterns):
        """Benchmark linear matching static route (100 routes)."""
        patterns = linear_100_patterns
        
        def linear_match():
            for p in patterns:
                result = match_route("/static/page25", p)
                if result is not None:
                    return result
            return None
        
        result = benchmark(linear_match)
        
        assert result is not None
    
    def test_trie_dynamic_match_100_routes(self, benchmark, trie_100_routes):
        """Benchmark trie matching dynamic route (100 routes)."""
        result = benchmark(trie_100_routes.match, "/dynamic/section15/12345")
        
        route, params = result
        assert route == "dynamic_15"
        assert params["id"] == "12345"
    
    def test_trie_worst_case_match(self, benchmark, trie_100_routes):
        """Benchmark trie when route is last (worst case for linear)."""
        result = benchmark(trie_100_routes.match, "/nested/level1/level2/page19")
        
        assert result[0] == "nested_19"
    
    def test_trie_no_match(self, benchmark, trie_100_routes):
        """Benchmark trie when no route matches."""
        result = benchmark(trie_100_routes.match, "/nonexistent/path")
        
        assert result[0] is None


@pytest.mark.benchmark
class TestLayoutCacheBenchmarks:
    """Benchmarks for layout cache."""
    
    @pytest.fixture
    def layout_cache(self):
        """Create a layout cache with nested layouts."""
        cache = LayoutCache()
        cache.add_layout("", "root")
        cache.add_layout("dashboard", "dashboard")
        cache.add_layout("dashboard/settings", "settings")
        cache.add_layout("dashboard/settings/profile", "profile")
        return cache
    
    def test_cached_lookup(self, benchmark, layout_cache):
        """Benchmark cached layout chain lookup."""
        # First call computes, subsequent calls use cache
        layout_cache.get_chain("dashboard/settings/profile")
        
        result = benchmark(layout_cache.get_chain, "dashboard/settings/profile")
        
        assert len(result) == 4  # root, dashboard, settings, profile
    
    def test_first_lookup(self, benchmark):
        """Benchmark first layout chain computation."""
        def create_and_lookup():
            cache = LayoutCache()
            cache.add_layout("", "root")
            cache.add_layout("a", "a")
            cache.add_layout("a/b", "b")
            cache.add_layout("a/b/c", "c")
            return cache.get_chain("a/b/c")
        
        result = benchmark(create_and_lookup)
        
        assert len(result) == 4

