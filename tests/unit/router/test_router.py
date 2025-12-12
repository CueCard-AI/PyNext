"""
Comprehensive tests for Router component.

Tests cover:
1. Router initialization
2. Route collection
3. Route matching
4. SSR rendering
5. Outlet content
6. Context creation
7. Fallback handling
8. Base path support
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from pynext.reactive.router import (
    Router,
    Route,
    Link,
    compile_route_pattern,
    CompiledRoute,
    RouterContext,
    get_router_context,
    _create_router_context,
)
from pynext.reactive.signal import signal


# =============================================================================
# SECTION 1: ROUTE PATTERN COMPILATION
# =============================================================================

class TestRoutePatternCompilation:
    """Test route pattern compilation to regex."""
    
    def test_simple_path(self):
        """Simple path compiles correctly."""
        pattern, params = compile_route_pattern("/")
        assert params == []
        assert pattern.match("/")
        assert not pattern.match("/foo")
    
    def test_static_path(self):
        """Static paths compile correctly."""
        pattern, params = compile_route_pattern("/about")
        assert params == []
        assert pattern.match("/about")
        assert not pattern.match("/about/extra")
        assert not pattern.match("/other")
    
    def test_nested_static_path(self):
        """Nested static paths compile correctly."""
        pattern, params = compile_route_pattern("/users/settings")
        assert params == []
        assert pattern.match("/users/settings")
        assert not pattern.match("/users")
        assert not pattern.match("/users/settings/more")
    
    def test_single_param(self):
        """Single parameter extracts correctly."""
        pattern, params = compile_route_pattern("/users/:id")
        assert params == ["id"]
        
        m = pattern.match("/users/123")
        assert m
        assert m.group(1) == "123"
        
        m = pattern.match("/users/abc")
        assert m
        assert m.group(1) == "abc"
    
    def test_multiple_params(self):
        """Multiple parameters extract correctly."""
        pattern, params = compile_route_pattern("/users/:userId/posts/:postId")
        assert params == ["userId", "postId"]
        
        m = pattern.match("/users/1/posts/2")
        assert m
        assert m.group(1) == "1"
        assert m.group(2) == "2"
    
    def test_param_not_match_slash(self):
        """Parameters don't match slashes."""
        pattern, params = compile_route_pattern("/files/:path")
        
        assert pattern.match("/files/doc.txt")
        assert not pattern.match("/files/dir/doc.txt")
    
    def test_wildcard(self):
        """Wildcard matches everything."""
        pattern, params = compile_route_pattern("/files/*")
        assert "*" in params
        
        m = pattern.match("/files/path/to/file.txt")
        assert m
        assert "path/to/file.txt" in m.group(1)
    
    def test_param_naming(self):
        """Various param name formats."""
        # Underscore
        pattern, params = compile_route_pattern("/users/:user_id")
        assert params == ["user_id"]
        
        # Numbers
        pattern, params = compile_route_pattern("/v1/:version2")
        assert params == ["version2"]
        
        # CamelCase
        pattern, params = compile_route_pattern("/:userId")
        assert params == ["userId"]
    
    def test_special_chars_escaped(self):
        """Special regex characters are escaped."""
        pattern, params = compile_route_pattern("/api.v1/users")
        assert pattern.match("/api.v1/users")
        assert not pattern.match("/apixv1/users")
    
    def test_empty_path(self):
        """Empty path handling."""
        pattern, params = compile_route_pattern("")
        assert params == []


# =============================================================================
# SECTION 2: COMPILED ROUTE MATCHING
# =============================================================================

class TestCompiledRoute:
    """Test CompiledRoute matching."""
    
    def test_match_returns_params(self):
        """Matched route returns params dict."""
        route = Route("/users/:id", component=lambda: None).to_compiled()
        
        params = route.match("/users/123")
        assert params == {"id": "123"}
    
    def test_no_match_returns_none(self):
        """Non-matching route returns None."""
        route = Route("/users/:id", component=lambda: None).to_compiled()
        
        params = route.match("/posts/123")
        assert params is None
    
    def test_match_empty_params(self):
        """Static route returns empty params."""
        route = Route("/about", component=lambda: None).to_compiled()
        
        params = route.match("/about")
        assert params == {}
    
    def test_match_multiple_params(self):
        """Multiple params extracted correctly."""
        route = Route("/users/:userId/posts/:postId", component=lambda: None).to_compiled()
        
        params = route.match("/users/1/posts/2")
        assert params == {"userId": "1", "postId": "2"}
    
    def test_match_with_special_chars(self):
        """Params with special characters."""
        route = Route("/search/:query", component=lambda: None).to_compiled()
        
        params = route.match("/search/hello%20world")
        assert params == {"query": "hello%20world"}
    
    def test_match_uuid(self):
        """UUID-like params."""
        route = Route("/items/:id", component=lambda: None).to_compiled()
        
        params = route.match("/items/550e8400-e29b-41d4-a716-446655440000")
        assert params["id"] == "550e8400-e29b-41d4-a716-446655440000"


# =============================================================================
# SECTION 3: ROUTE COMPONENT
# =============================================================================

class TestRoute:
    """Test Route component."""
    
    def test_route_creation(self):
        """Route creates with path and component."""
        def MyComponent():
            return "Hello"
        
        route = Route(path="/", component=MyComponent)
        assert route.path == "/"
        assert route.component == MyComponent
    
    def test_route_default_exact(self):
        """Route defaults to exact matching."""
        route = Route(path="/", component=lambda: None)
        assert route.exact is True
    
    def test_route_non_exact(self):
        """Route can be non-exact."""
        route = Route(path="/", component=lambda: None, exact=False)
        assert route.exact is False
    
    def test_route_with_guards(self):
        """Route accepts guards."""
        guard = lambda: None
        route = Route(path="/", component=lambda: None, guards=[guard])
        assert route.guards == [guard]
    
    def test_route_repr(self):
        """Route has useful repr."""
        def MyPage():
            pass
        
        route = Route(path="/page", component=MyPage)
        assert "MyPage" in repr(route)
        assert "/page" in repr(route)
    
    def test_route_match_method(self):
        """Route has match method."""
        route = Route(path="/users/:id", component=lambda: None)
        
        assert route.match("/users/1") == {"id": "1"}
        assert route.match("/other") is None
    
    def test_route_to_compiled(self):
        """Route converts to CompiledRoute."""
        route = Route(path="/users/:id", component=lambda: None)
        compiled = route.to_compiled()
        
        assert isinstance(compiled, CompiledRoute)
        assert compiled.path == "/users/:id"


# =============================================================================
# SECTION 4: ROUTER COMPONENT
# =============================================================================

class TestRouter:
    """Test Router component."""
    
    def test_router_creation(self):
        """Router creates with default options."""
        router = Router()
        assert router.base == ""
        assert router.fallback is None
        assert router.routes == []
    
    def test_router_with_base(self):
        """Router accepts base path."""
        router = Router(base="/app")
        assert router.base == "/app"
    
    def test_router_with_fallback(self):
        """Router accepts fallback component."""
        def NotFound():
            return "404"
        
        router = Router(fallback=NotFound)
        assert router.fallback == NotFound
    
    def test_router_bracket_syntax(self):
        """Router accepts routes via [] syntax."""
        router = Router()[
            Route(path="/", component=lambda: "Home"),
            Route(path="/about", component=lambda: "About"),
        ]
        
        assert len(router.routes) == 2
        assert router.routes[0].path == "/"
        assert router.routes[1].path == "/about"
    
    def test_router_single_route(self):
        """Router handles single route."""
        router = Router()[
            Route(path="/", component=lambda: "Home"),
        ]
        
        assert len(router.routes) == 1
    
    def test_router_find_matching_route(self):
        """Router finds matching route."""
        def Home():
            return "Home"
        def About():
            return "About"
        
        router = Router()[
            Route(path="/", component=Home),
            Route(path="/about", component=About),
        ]
        
        matched, params = router._find_matching_route("/")
        assert matched.component == Home
        
        matched, params = router._find_matching_route("/about")
        assert matched.component == About
    
    def test_router_no_match(self):
        """Router returns None for no match."""
        router = Router()[
            Route(path="/", component=lambda: "Home"),
        ]
        
        matched, params = router._find_matching_route("/nonexistent")
        assert matched is None
        assert params == {}
    
    def test_router_params_extraction(self):
        """Router extracts params from matching route."""
        router = Router()[
            Route(path="/users/:id", component=lambda: "User"),
        ]
        
        matched, params = router._find_matching_route("/users/123")
        assert params == {"id": "123"}
    
    def test_router_render_matched(self):
        """Router renders matched component."""
        def Home():
            from pynext.core.html import div
            return div()["Home Content"]
        
        router = Router()[
            Route(path="/", component=Home),
        ]
        
        result = str(router)
        assert "Home Content" in result
        assert "data-pynext-router" in result
    
    def test_router_render_fallback(self):
        """Router renders fallback for no match."""
        def NotFound():
            from pynext.core.html import div
            return div()["Not Found"]
        
        # Simulate being at /unknown
        with patch.object(Router, '_get_initial_pathname', return_value="/unknown"):
            router = Router(fallback=NotFound)[
                Route(path="/", component=lambda: "Home"),
            ]
            
            result = str(router)
            assert "Not Found" in result
    
    def test_router_default_404(self):
        """Router shows default 404 without fallback."""
        with patch.object(Router, '_get_initial_pathname', return_value="/unknown"):
            router = Router()[
                Route(path="/", component=lambda: "Home"),
            ]
            
            result = str(router)
            assert "404" in result
    
    def test_router_repr(self):
        """Router has useful repr."""
        router = Router(base="/app")[
            Route(path="/", component=lambda: None),
        ]
        
        assert "/app" in repr(router)
        assert "1" in repr(router)  # route count


# =============================================================================
# SECTION 5: ROUTER CONTEXT
# =============================================================================

class TestRouterContext:
    """Test RouterContext for state management."""
    
    def test_context_creation(self):
        """Context creates with signals."""
        ctx = _create_router_context("/test")
        
        assert ctx.pathname() == "/test"
        assert ctx.params() == {}
        assert ctx.query() == {}
        assert ctx.hash_() == ""
    
    def test_context_with_query(self):
        """Context accepts initial query."""
        ctx = _create_router_context("/", initial_query={"q": "test"})
        
        assert ctx.query() == {"q": "test"}
    
    def test_context_with_hash(self):
        """Context accepts initial hash."""
        ctx = _create_router_context("/", initial_hash="section")
        
        assert ctx.hash_() == "section"
    
    def test_context_navigate(self):
        """Context navigate updates signals."""
        ctx = _create_router_context("/")
        ctx.routes = [Route("/users/:id", component=lambda: None).to_compiled()]
        
        ctx.navigate("/users/123")
        
        assert ctx.pathname() == "/users/123"
        assert ctx.params() == {"id": "123"}
    
    def test_context_navigate_with_query(self):
        """Context navigate handles query string."""
        ctx = _create_router_context("/")
        
        ctx.navigate("/search?q=test")
        
        assert ctx.pathname() == "/search"
        assert ctx.query() == {"q": "test"}
    
    def test_context_navigate_with_hash(self):
        """Context navigate handles hash."""
        ctx = _create_router_context("/")
        
        ctx.navigate("/page#section")
        
        assert ctx.pathname() == "/page"
        assert ctx.hash_() == "section"
    
    def test_context_navigate_replace(self):
        """Context navigate with replace flag."""
        ctx = _create_router_context("/")
        
        # Replace should work without error
        ctx.navigate("/new", replace=True)
        assert ctx.pathname() == "/new"
    
    def test_context_get_current_route(self):
        """Context returns current matched route."""
        ctx = _create_router_context("/users/1")
        route = Route("/users/:id", component=lambda: None).to_compiled()
        ctx.routes = [route]
        
        current = ctx.get_current_route()
        assert current == route
    
    def test_context_get_current_route_no_match(self):
        """Context returns None when no route matches."""
        ctx = _create_router_context("/unknown")
        ctx.routes = [Route("/", component=lambda: None).to_compiled()]
        
        current = ctx.get_current_route()
        assert current is None


# =============================================================================
# SECTION 6: EDGE CASES
# =============================================================================

class TestRouterEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_routes(self):
        """Router handles empty routes."""
        router = Router()
        matched, params = router._find_matching_route("/anything")
        assert matched is None
    
    def test_route_priority(self):
        """Routes match in order (first wins)."""
        router = Router()[
            Route(path="/users/:id", component=lambda: "Dynamic"),
            Route(path="/users/new", component=lambda: "Static"),
        ]
        
        # First route wins
        matched, params = router._find_matching_route("/users/new")
        assert params == {"id": "new"}
    
    def test_route_exact_vs_prefix(self):
        """Exact matching prevents prefix matches."""
        pattern, _ = compile_route_pattern("/users")
        
        assert pattern.match("/users")
        assert not pattern.match("/users/123")
        assert not pattern.match("/usersextra")
    
    def test_trailing_slash_handling(self):
        """Trailing slashes handled."""
        pattern, _ = compile_route_pattern("/users")
        
        assert pattern.match("/users")
        assert not pattern.match("/users/")  # Different path
    
    def test_unicode_in_path(self):
        """Unicode characters in path."""
        route = Route("/users/:name", component=lambda: None)
        
        params = route.match("/users/日本語")
        assert params == {"name": "日本語"}
    
    def test_very_long_path(self):
        """Very long paths handled."""
        long_path = "/" + "/".join(f"segment{i}" for i in range(50))
        pattern, _ = compile_route_pattern(long_path)
        
        assert pattern.match(long_path)
    
    def test_many_params(self):
        """Many parameters handled."""
        path = "/a/:a/b/:b/c/:c/d/:d/e/:e"
        pattern, params = compile_route_pattern(path)
        
        assert params == ["a", "b", "c", "d", "e"]
        
        m = pattern.match("/a/1/b/2/c/3/d/4/e/5")
        assert m
        assert m.groups() == ("1", "2", "3", "4", "5")


# =============================================================================
# SECTION 7: PERFORMANCE
# =============================================================================

class TestRouterPerformance:
    """Test router performance characteristics."""
    
    def test_route_compilation_cached(self):
        """Route pattern compiled once."""
        route = Route("/users/:id", component=lambda: None)
        
        # Pattern should be compiled in __init__
        assert route.pattern is not None
        assert route.param_names == ["id"]
    
    def test_matching_many_routes(self):
        """Matching against many routes."""
        routes = [
            Route(f"/path{i}/:id", component=lambda: None)
            for i in range(100)
        ]
        
        router = Router()
        router.routes = routes
        
        # Should find last route
        matched, params = router._find_matching_route("/path99/123")
        assert params == {"id": "123"}
    
    def test_no_regex_compilation_on_match(self):
        """Regex not recompiled on each match."""
        route = Route("/users/:id", component=lambda: None)
        compiled = route.pattern
        
        # Multiple matches use same compiled pattern
        route.match("/users/1")
        route.match("/users/2")
        route.match("/users/3")
        
        assert route.pattern is compiled

