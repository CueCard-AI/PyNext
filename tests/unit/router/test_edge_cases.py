"""
Edge case tests for the router.

Tests cover unusual inputs, boundary conditions, and error handling.
"""

import pytest
from unittest.mock import Mock, patch

from pynext.reactive.router import (
    Router,
    Route,
    Link,
    compile_route_pattern,
    _create_router_context,
    useNavigate,
    useParams,
    useSearchParams,
    useLocation,
    useMatch,
    get_router_context,
    Redirect,
)


# =============================================================================
# SECTION 1: UNUSUAL PATH PATTERNS
# =============================================================================

class TestUnusualPathPatterns:
    """Test unusual path patterns."""
    
    def test_double_slash(self):
        """Path with double slash."""
        pattern, _ = compile_route_pattern("//about")
        assert pattern.match("//about")
    
    def test_trailing_slash(self):
        """Path with trailing slash."""
        pattern, _ = compile_route_pattern("/about/")
        assert pattern.match("/about/")
        assert not pattern.match("/about")
    
    def test_only_param(self):
        """Path with only param."""
        route = Route("/:id", component=lambda: None)
        
        assert route.match("/123") == {"id": "123"}
    
    def test_empty_static_segment(self):
        """Empty segment between slashes."""
        pattern, _ = compile_route_pattern("/a//b")
        assert pattern.match("/a//b")
    
    def test_param_like_segment(self):
        """Static segment that looks like param."""
        pattern, _ = compile_route_pattern("/literal:colon")
        assert pattern.match("/literal:colon")
    
    def test_hyphenated_param_value(self):
        """Param value with hyphens."""
        route = Route("/:slug", component=lambda: None)
        
        params = route.match("/my-awesome-article-title")
        assert params == {"slug": "my-awesome-article-title"}
    
    def test_dotted_param_value(self):
        """Param value with dots."""
        route = Route("/:file", component=lambda: None)
        
        params = route.match("/document.v2.final.pdf")
        assert params == {"file": "document.v2.final.pdf"}
    
    def test_underscore_param_value(self):
        """Param value with underscores."""
        route = Route("/:id", component=lambda: None)
        
        params = route.match("/user_profile_123")
        assert params == {"id": "user_profile_123"}


# =============================================================================
# SECTION 2: UNICODE AND SPECIAL CHARACTERS
# =============================================================================

class TestUnicodeAndSpecialChars:
    """Test unicode and special character handling."""
    
    def test_japanese_path(self):
        """Japanese characters in path."""
        route = Route("/日本語/:id", component=lambda: None)
        
        params = route.match("/日本語/123")
        assert params == {"id": "123"}
    
    def test_chinese_path(self):
        """Chinese characters in path."""
        route = Route("/中文/:id", component=lambda: None)
        
        params = route.match("/中文/abc")
        assert params == {"id": "abc"}
    
    def test_emoji_in_param(self):
        """Emoji in param value."""
        route = Route("/:emoji", component=lambda: None)
        
        params = route.match("/🎉🎊🎁")
        assert params == {"emoji": "🎉🎊🎁"}
    
    def test_arabic_path(self):
        """Arabic characters in path."""
        route = Route("/العربية/:id", component=lambda: None)
        
        params = route.match("/العربية/123")
        assert params == {"id": "123"}
    
    def test_cyrillic_path(self):
        """Cyrillic characters in path."""
        route = Route("/русский/:id", component=lambda: None)
        
        params = route.match("/русский/123")
        assert params == {"id": "123"}
    
    def test_percent_encoded_param(self):
        """Percent-encoded param value."""
        route = Route("/:query", component=lambda: None)
        
        params = route.match("/hello%20world")
        assert params == {"query": "hello%20world"}
    
    def test_plus_in_param(self):
        """Plus sign in param."""
        route = Route("/:query", component=lambda: None)
        
        params = route.match("/hello+world")
        assert params == {"query": "hello+world"}


# =============================================================================
# SECTION 3: BOUNDARY CONDITIONS
# =============================================================================

class TestBoundaryConditions:
    """Test boundary conditions."""
    
    def test_empty_path(self):
        """Empty path pattern."""
        pattern, params = compile_route_pattern("")
        assert params == []
    
    def test_root_only(self):
        """Root path only."""
        route = Route("/", component=lambda: None)
        
        assert route.match("/") == {}
        assert route.match("/a") is None
    
    def test_single_char_path(self):
        """Single character path."""
        route = Route("/a", component=lambda: None)
        
        assert route.match("/a") == {}
    
    def test_single_char_param_name(self):
        """Single character param name."""
        route = Route("/:x", component=lambda: None)
        
        assert route.match("/value") == {"x": "value"}
    
    def test_very_long_param_value(self):
        """Very long param value."""
        route = Route("/:id", component=lambda: None)
        
        long_value = "a" * 1000
        params = route.match(f"/{long_value}")
        
        assert params == {"id": long_value}
    
    def test_single_char_param_value(self):
        """Single character param value."""
        route = Route("/:id", component=lambda: None)
        
        assert route.match("/a") == {"id": "a"}
    
    def test_numeric_param_value(self):
        """Pure numeric param value."""
        route = Route("/:id", component=lambda: None)
        
        assert route.match("/12345") == {"id": "12345"}


# =============================================================================
# SECTION 4: CONTEXT EDGE CASES
# =============================================================================

class TestContextEdgeCases:
    """Test router context edge cases."""
    
    def test_context_reinitialization(self):
        """Context can be reinitialized."""
        ctx1 = _create_router_context("/a")
        ctx2 = _create_router_context("/b")
        
        # Latest context is active
        assert get_router_context().pathname() == "/b"
    
    def test_empty_query(self):
        """Empty query params."""
        ctx = _create_router_context("/", initial_query={})
        
        params, _ = useSearchParams()
        assert params == {}
    
    def test_null_query_value(self):
        """Query with empty string value."""
        ctx = _create_router_context("/")
        ctx.query.set({"flag": ""})
        
        params, _ = useSearchParams()
        assert params["flag"] == ""
    
    def test_navigate_empty_string(self):
        """Navigate to empty string."""
        ctx = _create_router_context("/old")
        
        navigate = useNavigate()
        navigate("")
        
        # Empty should become root
        assert ctx.pathname() == "/"
    
    def test_navigate_to_current(self):
        """Navigate to current path."""
        ctx = _create_router_context("/current")
        
        navigate = useNavigate()
        navigate("/current")
        
        assert ctx.pathname() == "/current"


# =============================================================================
# SECTION 5: LINK EDGE CASES
# =============================================================================

class TestLinkEdgeCases:
    """Test Link edge cases."""
    
    def test_link_empty_href(self):
        """Link with empty href."""
        link = Link(href="")["Empty"]
        
        result = str(link)
        assert 'href=""' in result
    
    def test_link_hash_only(self):
        """Link with hash only."""
        link = Link(href="#section")["Section"]
        
        result = str(link)
        assert 'href="#section"' in result
    
    def test_link_query_only(self):
        """Link with query only."""
        link = Link(href="?q=test")["Search"]
        
        result = str(link)
        assert 'href="?q=test"' in result
    
    def test_link_absolute_url(self):
        """Link with absolute URL."""
        link = Link(href="https://example.com")["External"]
        
        result = str(link)
        assert "https://example.com" in result
    
    def test_link_no_children(self):
        """Link with no children."""
        link = Link(href="/")
        
        result = str(link)
        assert "<a" in result


# =============================================================================
# SECTION 6: ROUTER EDGE CASES
# =============================================================================

class TestRouterEdgeCases:
    """Test Router edge cases."""
    
    def test_router_no_routes(self):
        """Router with no routes."""
        with patch.object(Router, '_get_initial_pathname', return_value="/"):
            router = Router()
            
            matched, params = router._find_matching_route("/anything")
            assert matched is None
    
    def test_router_duplicate_paths(self):
        """Router with duplicate paths (first wins)."""
        def First():
            return "First"
        
        def Second():
            return "Second"
        
        router = Router()[
            Route("/same", component=First),
            Route("/same", component=Second),
        ]
        
        matched, _ = router._find_matching_route("/same")
        assert matched.component == First
    
    def test_router_overlapping_routes(self):
        """Router with overlapping routes."""
        router = Router()[
            Route("/users/:id", component=lambda: "Dynamic"),
            Route("/users/new", component=lambda: "Static"),
        ]
        
        # First route matches
        matched, params = router._find_matching_route("/users/new")
        assert params == {"id": "new"}


# =============================================================================
# SECTION 7: REDIRECT EDGE CASES
# =============================================================================

class TestRedirectEdgeCases:
    """Test Redirect edge cases."""
    
    def test_redirect_to_same_page(self):
        """Redirect to same page."""
        redirect = Redirect(to="/current")
        assert redirect.to == "/current"
    
    def test_redirect_with_long_query(self):
        """Redirect with long query string."""
        long_query = "&".join(f"param{i}=value{i}" for i in range(50))
        redirect = Redirect(to=f"/page?{long_query}")
        
        assert len(redirect.to) > 500
    
    def test_redirect_with_unicode(self):
        """Redirect with unicode path."""
        redirect = Redirect(to="/日本語/ページ")
        assert redirect.to == "/日本語/ページ"


# =============================================================================
# SECTION 8: MATCH EDGE CASES
# =============================================================================

class TestMatchEdgeCases:
    """Test useMatch edge cases."""
    
    def test_match_with_special_regex_chars(self):
        """Match pattern with special regex chars."""
        ctx = _create_router_context("/api.v1/users")
        
        result = useMatch("/api.v1/users")
        assert result == {}
    
    def test_match_partial_path(self):
        """Match doesn't match partial paths."""
        ctx = _create_router_context("/users/123/extra")
        
        result = useMatch("/users/:id")
        assert result is None  # Doesn't match because of /extra
    
    def test_match_case_sensitive(self):
        """Match is case sensitive."""
        ctx = _create_router_context("/users")
        
        assert useMatch("/users") == {}
        assert useMatch("/Users") is None
        assert useMatch("/USERS") is None


# =============================================================================
# SECTION 9: QUERY EDGE CASES
# =============================================================================

class TestQueryEdgeCases:
    """Test query string edge cases."""
    
    def test_query_special_chars(self):
        """Query with special characters."""
        ctx = _create_router_context("/")
        navigate = useNavigate()
        
        navigate("/search?q=hello%26world")
        
        # URL decoding handled by parser
        query = ctx.query()
        # Note: our parser doesn't decode, just passes through
        assert "hello" in query.get("q", "")
    
    def test_query_array_params(self):
        """Query with array-like params."""
        ctx = _create_router_context("/")
        ctx.query.set({"tags[]": "a"})
        
        params, _ = useSearchParams()
        assert "tags[]" in params
    
    def test_query_numeric_key(self):
        """Query with numeric key."""
        ctx = _create_router_context("/")
        ctx.query.set({"123": "value"})
        
        params, _ = useSearchParams()
        assert params["123"] == "value"


# =============================================================================
# SECTION 10: NAVIGATION EDGE CASES
# =============================================================================

class TestNavigationEdgeCases:
    """Test navigation edge cases."""
    
    def test_navigate_history_zero(self):
        """Navigate with history delta 0."""
        ctx = _create_router_context("/page")
        
        navigate = useNavigate()
        navigate(0)  # Should not crash
    
    def test_navigate_large_history_delta(self):
        """Navigate with large history delta."""
        ctx = _create_router_context("/page")
        
        navigate = useNavigate()
        navigate(-100)  # Should not crash
        navigate(100)   # Should not crash
    
    def test_navigate_with_all_url_parts(self):
        """Navigate with path, query, and hash."""
        ctx = _create_router_context("/")
        
        navigate = useNavigate()
        navigate("/page?q=test&p=2#section")
        
        assert ctx.pathname() == "/page"
        assert ctx.query()["q"] == "test"
        assert ctx.hash_() == "section"

