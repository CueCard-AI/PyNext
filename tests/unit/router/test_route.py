"""
Comprehensive tests for Route component and pattern matching.

Tests cover:
1. Path pattern syntax
2. Parameter extraction
3. Wildcard routes
4. Optional segments
5. Route guards
6. Route metadata
"""

import pytest
from unittest.mock import Mock

from pynext.reactive.router import (
    Route,
    CompiledRoute,
    compile_route_pattern,
    Redirect,
    createRouteGuard,
)


# =============================================================================
# SECTION 1: BASIC ROUTE PATTERNS
# =============================================================================

class TestBasicPatterns:
    """Test basic route patterns."""
    
    def test_root_path(self):
        """Root path matches only root."""
        route = Route("/", component=lambda: None)
        
        assert route.match("/") == {}
        assert route.match("/anything") is None
    
    def test_static_segment(self):
        """Static segment matches exactly."""
        route = Route("/about", component=lambda: None)
        
        assert route.match("/about") == {}
        assert route.match("/about-us") is None
        assert route.match("/about/team") is None
    
    def test_multiple_static_segments(self):
        """Multiple static segments."""
        route = Route("/api/v1/users", component=lambda: None)
        
        assert route.match("/api/v1/users") == {}
        assert route.match("/api/v2/users") is None
    
    def test_single_param(self):
        """Single dynamic parameter."""
        route = Route("/users/:id", component=lambda: None)
        
        assert route.match("/users/123") == {"id": "123"}
        assert route.match("/users/abc") == {"id": "abc"}
        assert route.match("/users/") is None
    
    def test_param_at_start(self):
        """Parameter at start of path."""
        route = Route("/:category/items", component=lambda: None)
        
        assert route.match("/electronics/items") == {"category": "electronics"}
    
    def test_param_at_end(self):
        """Parameter at end of path."""
        route = Route("/items/:id", component=lambda: None)
        
        assert route.match("/items/456") == {"id": "456"}
    
    def test_multiple_params(self):
        """Multiple parameters."""
        route = Route("/users/:userId/posts/:postId", component=lambda: None)
        
        params = route.match("/users/1/posts/2")
        assert params == {"userId": "1", "postId": "2"}
    
    def test_adjacent_params(self):
        """Adjacent parameters with static segment."""
        route = Route("/compare/:a/vs/:b", component=lambda: None)
        
        params = route.match("/compare/apple/vs/orange")
        assert params == {"a": "apple", "b": "orange"}


# =============================================================================
# SECTION 2: PARAMETER NAMING
# =============================================================================

class TestParameterNaming:
    """Test parameter naming conventions."""
    
    def test_lowercase_param(self):
        """Lowercase parameter name."""
        route = Route("/users/:id", component=lambda: None)
        assert route.param_names == ["id"]
    
    def test_uppercase_param(self):
        """Uppercase in parameter name."""
        route = Route("/users/:userId", component=lambda: None)
        assert route.param_names == ["userId"]
    
    def test_underscore_param(self):
        """Underscore in parameter name."""
        route = Route("/users/:user_id", component=lambda: None)
        assert route.param_names == ["user_id"]
    
    def test_number_in_param(self):
        """Number in parameter name."""
        route = Route("/v1/:version2", component=lambda: None)
        assert route.param_names == ["version2"]
    
    def test_starts_with_underscore(self):
        """Parameter starting with underscore."""
        route = Route("/items/:_id", component=lambda: None)
        assert route.param_names == ["_id"]
    
    def test_long_param_name(self):
        """Long parameter name."""
        route = Route("/items/:veryLongParameterNameHere", component=lambda: None)
        assert route.param_names == ["veryLongParameterNameHere"]


# =============================================================================
# SECTION 3: WILDCARD ROUTES
# =============================================================================

class TestWildcardRoutes:
    """Test wildcard (*) routes."""
    
    def test_wildcard_basic(self):
        """Wildcard matches any path."""
        route = Route("/files/*", component=lambda: None)
        
        params = route.match("/files/path/to/file.txt")
        assert params["*"] == "path/to/file.txt"
    
    def test_wildcard_single_segment(self):
        """Wildcard matches single segment."""
        route = Route("/docs/*", component=lambda: None)
        
        params = route.match("/docs/readme")
        assert params["*"] == "readme"
    
    def test_wildcard_empty(self):
        """Wildcard with empty path."""
        route = Route("/files/*", component=lambda: None)
        
        params = route.match("/files/")
        assert params is not None
        assert params["*"] == ""
    
    def test_wildcard_with_params(self):
        """Wildcard with other parameters."""
        pattern, param_names = compile_route_pattern("/users/:id/files/*")
        
        assert param_names == ["id", "*"]
        
        m = pattern.match("/users/123/files/path/to/file")
        assert m.group(1) == "123"
        assert m.group(2) == "path/to/file"


# =============================================================================
# SECTION 4: SPECIAL CHARACTERS
# =============================================================================

class TestSpecialCharacters:
    """Test handling of special characters."""
    
    def test_dot_in_path(self):
        """Dot in static path."""
        route = Route("/api.v1/users", component=lambda: None)
        
        assert route.match("/api.v1/users") == {}
        assert route.match("/apixv1/users") is None
    
    def test_hyphen_in_path(self):
        """Hyphen in static path."""
        route = Route("/about-us", component=lambda: None)
        
        assert route.match("/about-us") == {}
        assert route.match("/about_us") is None
    
    def test_dot_in_param(self):
        """Dot in parameter value."""
        route = Route("/files/:filename", component=lambda: None)
        
        params = route.match("/files/document.pdf")
        assert params == {"filename": "document.pdf"}
    
    def test_hyphen_in_param(self):
        """Hyphen in parameter value."""
        route = Route("/articles/:slug", component=lambda: None)
        
        params = route.match("/articles/my-article-title")
        assert params == {"slug": "my-article-title"}
    
    def test_encoded_chars_in_param(self):
        """URL-encoded characters in parameter."""
        route = Route("/search/:query", component=lambda: None)
        
        params = route.match("/search/hello%20world")
        assert params == {"query": "hello%20world"}
    
    def test_plus_sign_in_param(self):
        """Plus sign in parameter."""
        route = Route("/search/:q", component=lambda: None)
        
        params = route.match("/search/hello+world")
        assert params == {"q": "hello+world"}


# =============================================================================
# SECTION 5: ROUTE GUARDS
# =============================================================================

class TestRouteGuards:
    """Test route guard functionality."""
    
    def test_route_with_guard(self):
        """Route accepts guard function."""
        guard = lambda: None
        route = Route("/admin", component=lambda: None, guards=[guard])
        
        assert guard in route.guards
    
    def test_route_multiple_guards(self):
        """Route with multiple guards."""
        guard1 = lambda: None
        guard2 = lambda: None
        
        route = Route("/admin", component=lambda: None, guards=[guard1, guard2])
        
        assert len(route.guards) == 2
    
    def test_redirect_dataclass(self):
        """Redirect has correct attributes."""
        redirect = Redirect(to="/login")
        
        assert redirect.to == "/login"
        assert redirect.replace is True
    
    def test_redirect_no_replace(self):
        """Redirect with replace=False."""
        redirect = Redirect(to="/login", replace=False)
        
        assert redirect.replace is False
    
    def test_create_route_guard(self):
        """createRouteGuard creates guard function."""
        check_called = []
        
        def check():
            check_called.append(True)
            return None
        
        guard = createRouteGuard(check)
        result = guard()
        
        assert check_called == [True]
        assert result is None
    
    def test_guard_returns_redirect(self):
        """Guard that returns Redirect."""
        guard = createRouteGuard(lambda: Redirect("/login"))
        result = guard()
        
        assert isinstance(result, Redirect)
        assert result.to == "/login"


# =============================================================================
# SECTION 6: ROUTE TO COMPILED
# =============================================================================

class TestRouteToCompiled:
    """Test Route to CompiledRoute conversion."""
    
    def test_to_compiled_preserves_path(self):
        """Compiled route has same path."""
        route = Route("/users/:id", component=lambda: None)
        compiled = route.to_compiled()
        
        assert compiled.path == "/users/:id"
    
    def test_to_compiled_preserves_component(self):
        """Compiled route has same component."""
        def MyComponent():
            pass
        
        route = Route("/", component=MyComponent)
        compiled = route.to_compiled()
        
        assert compiled.component is MyComponent
    
    def test_to_compiled_preserves_exact(self):
        """Compiled route has same exact flag."""
        route = Route("/", component=lambda: None, exact=False)
        compiled = route.to_compiled()
        
        assert compiled.exact is False
    
    def test_to_compiled_preserves_guards(self):
        """Compiled route has same guards."""
        guard = lambda: None
        route = Route("/", component=lambda: None, guards=[guard])
        compiled = route.to_compiled()
        
        assert compiled.guards == [guard]
    
    def test_to_compiled_has_pattern(self):
        """Compiled route has regex pattern."""
        route = Route("/users/:id", component=lambda: None)
        compiled = route.to_compiled()
        
        assert compiled.pattern.match("/users/123")
    
    def test_to_compiled_has_param_names(self):
        """Compiled route has param names."""
        route = Route("/users/:userId/posts/:postId", component=lambda: None)
        compiled = route.to_compiled()
        
        assert compiled.param_names == ["userId", "postId"]


# =============================================================================
# SECTION 7: COMPILED ROUTE MATCHING
# =============================================================================

class TestCompiledRouteMatching:
    """Test CompiledRoute match method."""
    
    def test_match_returns_dict(self):
        """Match returns params dict."""
        route = Route("/users/:id", component=lambda: None).to_compiled()
        
        result = route.match("/users/123")
        
        assert isinstance(result, dict)
        assert result == {"id": "123"}
    
    def test_no_match_returns_none(self):
        """No match returns None."""
        route = Route("/users/:id", component=lambda: None).to_compiled()
        
        result = route.match("/posts/123")
        
        assert result is None
    
    def test_match_order_preserved(self):
        """Parameters in order."""
        route = Route("/a/:a/b/:b/c/:c", component=lambda: None).to_compiled()
        
        result = route.match("/a/1/b/2/c/3")
        
        assert result == {"a": "1", "b": "2", "c": "3"}
    
    def test_match_empty_segment_fails(self):
        """Empty segment doesn't match."""
        route = Route("/users/:id/posts", component=lambda: None).to_compiled()
        
        assert route.match("/users//posts") is None


# =============================================================================
# SECTION 8: EDGE CASES
# =============================================================================

class TestRouteEdgeCases:
    """Test edge cases for routes."""
    
    def test_empty_path(self):
        """Empty path handling."""
        route = Route("", component=lambda: None)
        
        assert route.match("") == {}
    
    def test_very_long_path(self):
        """Very long path."""
        segments = "/".join(f"seg{i}" for i in range(100))
        path = f"/{segments}"
        
        route = Route(path, component=lambda: None)
        assert route.match(path) == {}
    
    def test_many_params(self):
        """Many parameters in path."""
        path = "/" + "/".join(f":p{i}" for i in range(20))
        route = Route(path, component=lambda: None)
        
        assert len(route.param_names) == 20
    
    def test_unicode_path(self):
        """Unicode in path."""
        route = Route("/ページ/:id", component=lambda: None)
        
        params = route.match("/ページ/123")
        assert params == {"id": "123"}
    
    def test_unicode_param_value(self):
        """Unicode parameter value."""
        route = Route("/items/:name", component=lambda: None)
        
        params = route.match("/items/日本語")
        assert params == {"name": "日本語"}
    
    def test_route_repr_with_lambda(self):
        """Route repr with lambda component."""
        route = Route("/", component=lambda: None)
        
        # Should not crash
        repr_str = repr(route)
        assert "/" in repr_str

