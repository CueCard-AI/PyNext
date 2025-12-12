"""
Performance-focused tests for the router.

Tests verify that route operations are fast and efficient.
"""

import pytest
import time

from pynext.reactive.router import (
    Router,
    Route,
    compile_route_pattern,
    _create_router_context,
    useNavigate,
)


# =============================================================================
# SECTION 1: ROUTE COMPILATION PERFORMANCE
# =============================================================================

class TestRouteCompilationPerformance:
    """Test route pattern compilation performance."""
    
    def test_compile_simple_route(self):
        """Simple route compiles quickly."""
        start = time.perf_counter()
        for _ in range(1000):
            compile_route_pattern("/about")
        duration = time.perf_counter() - start
        
        # Should complete in under 100ms
        assert duration < 0.1
    
    def test_compile_dynamic_route(self):
        """Dynamic route compiles quickly."""
        start = time.perf_counter()
        for _ in range(1000):
            compile_route_pattern("/users/:id")
        duration = time.perf_counter() - start
        
        assert duration < 0.1
    
    def test_compile_complex_route(self):
        """Complex route compiles quickly."""
        start = time.perf_counter()
        for _ in range(1000):
            compile_route_pattern("/users/:userId/posts/:postId/comments/:commentId")
        duration = time.perf_counter() - start
        
        assert duration < 0.1
    
    def test_compile_many_routes(self):
        """Many routes compile quickly."""
        patterns = [f"/path{i}/:id" for i in range(100)]
        
        start = time.perf_counter()
        for pattern in patterns:
            compile_route_pattern(pattern)
        duration = time.perf_counter() - start
        
        # 100 routes should compile in under 50ms
        assert duration < 0.05


# =============================================================================
# SECTION 2: ROUTE MATCHING PERFORMANCE
# =============================================================================

class TestRouteMatchingPerformance:
    """Test route matching performance."""
    
    def test_match_static_route(self):
        """Static route matches quickly."""
        route = Route("/about", component=lambda: None)
        
        start = time.perf_counter()
        for _ in range(10000):
            route.match("/about")
        duration = time.perf_counter() - start
        
        # 10k matches in under 100ms
        assert duration < 0.1
    
    def test_match_dynamic_route(self):
        """Dynamic route matches quickly."""
        route = Route("/users/:id", component=lambda: None)
        
        start = time.perf_counter()
        for _ in range(10000):
            route.match("/users/123")
        duration = time.perf_counter() - start
        
        assert duration < 0.1
    
    def test_match_no_match(self):
        """Non-matching is fast."""
        route = Route("/users/:id", component=lambda: None)
        
        start = time.perf_counter()
        for _ in range(10000):
            route.match("/posts/123")
        duration = time.perf_counter() - start
        
        assert duration < 0.1
    
    def test_match_many_routes(self):
        """Matching against many routes."""
        routes = [Route(f"/path{i}/:id", component=lambda: None) for i in range(100)]
        router = Router()
        router.routes = routes
        
        start = time.perf_counter()
        for _ in range(1000):
            router._find_matching_route("/path99/123")
        duration = time.perf_counter() - start
        
        # 1k searches in 100 routes under 100ms
        assert duration < 0.1


# =============================================================================
# SECTION 3: NAVIGATION PERFORMANCE
# =============================================================================

class TestNavigationPerformance:
    """Test navigation performance."""
    
    def test_navigate_speed(self):
        """Navigation is fast."""
        ctx = _create_router_context("/")
        ctx.routes = [Route("/page", component=lambda: None).to_compiled()]
        
        navigate = useNavigate()
        
        start = time.perf_counter()
        for _ in range(1000):
            navigate("/page")
        duration = time.perf_counter() - start
        
        # 1k navigations in under 100ms
        assert duration < 0.1
    
    def test_navigate_with_params(self):
        """Navigation with params is fast."""
        ctx = _create_router_context("/")
        ctx.routes = [Route("/users/:id", component=lambda: None).to_compiled()]
        
        navigate = useNavigate()
        
        start = time.perf_counter()
        for i in range(1000):
            navigate(f"/users/{i}")
        duration = time.perf_counter() - start
        
        assert duration < 0.1
    
    def test_navigate_with_query(self):
        """Navigation with query is fast."""
        ctx = _create_router_context("/")
        
        navigate = useNavigate()
        
        start = time.perf_counter()
        for i in range(1000):
            navigate(f"/search?q=query{i}&page={i}")
        duration = time.perf_counter() - start
        
        assert duration < 0.1


# =============================================================================
# SECTION 4: ROUTER INITIALIZATION PERFORMANCE
# =============================================================================

class TestRouterInitPerformance:
    """Test router initialization performance."""
    
    def test_router_with_many_routes(self):
        """Router with many routes initializes quickly."""
        start = time.perf_counter()
        
        router = Router()
        for i in range(100):
            router.routes.append(Route(f"/path{i}/:id", component=lambda: None))
        
        duration = time.perf_counter() - start
        
        # 100 routes in under 50ms
        assert duration < 0.05
    
    def test_router_context_creation(self):
        """Router context creates quickly."""
        start = time.perf_counter()
        for _ in range(1000):
            _create_router_context("/test")
        duration = time.perf_counter() - start
        
        assert duration < 0.1


# =============================================================================
# SECTION 5: MEMORY EFFICIENCY
# =============================================================================

class TestMemoryEfficiency:
    """Test memory efficiency of router."""
    
    def test_compiled_route_size(self):
        """Compiled route is lightweight."""
        route = Route("/users/:userId/posts/:postId", component=lambda: None)
        compiled = route.to_compiled()
        
        # Should have minimal attributes
        assert hasattr(compiled, 'path')
        assert hasattr(compiled, 'pattern')
        assert hasattr(compiled, 'param_names')
        assert hasattr(compiled, 'component')
    
    def test_router_context_minimal(self):
        """Router context is minimal."""
        ctx = _create_router_context("/")
        
        # Only essential signals
        assert ctx.pathname is not None
        assert ctx.params is not None
        assert ctx.query is not None
        assert ctx.hash_ is not None


# =============================================================================
# SECTION 6: STRESS TESTS
# =============================================================================

class TestStressTests:
    """Stress tests for router."""
    
    def test_rapid_navigation(self):
        """Handle rapid navigation."""
        ctx = _create_router_context("/")
        ctx.routes = [Route(f"/page{i}", component=lambda: None).to_compiled() for i in range(10)]
        
        navigate = useNavigate()
        
        # Navigate rapidly between pages
        for _ in range(100):
            for i in range(10):
                navigate(f"/page{i}")
        
        # Should not crash
        assert ctx.pathname() is not None
    
    def test_many_params(self):
        """Handle routes with many params."""
        path = "/a/:a/b/:b/c/:c/d/:d/e/:e/f/:f/g/:g"
        route = Route(path, component=lambda: None)
        
        match_path = "/a/1/b/2/c/3/d/4/e/5/f/6/g/7"
        
        params = route.match(match_path)
        
        assert params == {"a": "1", "b": "2", "c": "3", "d": "4", "e": "5", "f": "6", "g": "7"}
    
    def test_long_path(self):
        """Handle very long paths."""
        segments = "/".join(f"segment{i}" for i in range(100))
        path = f"/{segments}"
        
        route = Route(path, component=lambda: None)
        
        assert route.match(path) == {}

