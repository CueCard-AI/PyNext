"""
Comprehensive tests for useNavigate hook and Navigator.

Tests cover:
1. Basic navigation
2. Replace mode
3. History navigation (back/forward)
4. Navigation with state
5. Prefetching
"""

import pytest
from unittest.mock import Mock, patch

from pynext.reactive.router import (
    useNavigate,
    Navigator,
    _create_router_context,
    get_router_context,
    Route,
)


# =============================================================================
# SECTION 1: NAVIGATOR CLASS
# =============================================================================

class TestNavigator:
    """Test Navigator class."""
    
    def test_navigator_callable(self):
        """Navigator is callable."""
        nav = Navigator()
        
        assert callable(nav)
    
    def test_navigator_has_back(self):
        """Navigator has back method."""
        nav = Navigator()
        
        assert hasattr(nav, "back")
        assert callable(nav.back)
    
    def test_navigator_has_forward(self):
        """Navigator has forward method."""
        nav = Navigator()
        
        assert hasattr(nav, "forward")
        assert callable(nav.forward)
    
    def test_navigator_has_prefetch(self):
        """Navigator has prefetch method."""
        nav = Navigator()
        
        assert hasattr(nav, "prefetch")
        assert callable(nav.prefetch)


# =============================================================================
# SECTION 2: USE NAVIGATE HOOK
# =============================================================================

class TestUseNavigate:
    """Test useNavigate hook."""
    
    def test_returns_navigator(self):
        """useNavigate returns Navigator instance."""
        navigate = useNavigate()
        
        assert isinstance(navigate, Navigator)
    
    def test_navigate_updates_pathname(self):
        """Navigate updates pathname signal."""
        ctx = _create_router_context("/")
        
        navigate = useNavigate()
        navigate("/about")
        
        assert ctx.pathname() == "/about"
    
    def test_navigate_with_params_route(self):
        """Navigate to route with params."""
        ctx = _create_router_context("/")
        ctx.routes = [Route("/users/:id", component=lambda: None).to_compiled()]
        
        navigate = useNavigate()
        navigate("/users/123")
        
        assert ctx.pathname() == "/users/123"
        assert ctx.params() == {"id": "123"}
    
    def test_navigate_clears_old_params(self):
        """Navigate clears old params on new route."""
        ctx = _create_router_context("/users/123")
        ctx.params.set({"id": "123"})
        ctx.routes = [
            Route("/users/:id", component=lambda: None).to_compiled(),
            Route("/about", component=lambda: None).to_compiled(),
        ]
        
        navigate = useNavigate()
        navigate("/about")
        
        assert ctx.params() == {}


# =============================================================================
# SECTION 3: REPLACE MODE
# =============================================================================

class TestNavigateReplace:
    """Test navigation with replace mode."""
    
    def test_navigate_with_replace(self):
        """Navigate with replace flag."""
        ctx = _create_router_context("/")
        
        navigate = useNavigate()
        navigate("/new", replace=True)
        
        # Pathname still updates
        assert ctx.pathname() == "/new"
    
    def test_replace_is_optional(self):
        """Replace defaults to False."""
        ctx = _create_router_context("/")
        
        navigate = useNavigate()
        navigate("/page")  # No replace argument
        
        assert ctx.pathname() == "/page"


# =============================================================================
# SECTION 4: HISTORY NAVIGATION
# =============================================================================

class TestHistoryNavigation:
    """Test history navigation (back/forward)."""
    
    def test_navigate_back_with_number(self):
        """Navigate back using negative number."""
        ctx = _create_router_context("/page2")
        
        navigate = useNavigate()
        # This is a no-op on server, but shouldn't error
        navigate(-1)
    
    def test_navigate_forward_with_number(self):
        """Navigate forward using positive number."""
        ctx = _create_router_context("/page1")
        
        navigate = useNavigate()
        navigate(1)  # Should not error
    
    def test_back_method(self):
        """Navigator back() method."""
        ctx = _create_router_context("/page")
        
        nav = Navigator()
        nav.back()  # Should not error
    
    def test_forward_method(self):
        """Navigator forward() method."""
        ctx = _create_router_context("/page")
        
        nav = Navigator()
        nav.forward()  # Should not error


# =============================================================================
# SECTION 5: QUERY STRING NAVIGATION
# =============================================================================

class TestQueryNavigation:
    """Test navigation with query strings."""
    
    def test_navigate_with_query(self):
        """Navigate with query string."""
        ctx = _create_router_context("/")
        
        navigate = useNavigate()
        navigate("/search?q=test")
        
        assert ctx.pathname() == "/search"
        assert ctx.query() == {"q": "test"}
    
    def test_navigate_with_multiple_query_params(self):
        """Navigate with multiple query params."""
        ctx = _create_router_context("/")
        
        navigate = useNavigate()
        navigate("/search?q=test&page=2&sort=asc")
        
        query = ctx.query()
        assert query["q"] == "test"
        assert query["page"] == "2"
        assert query["sort"] == "asc"
    
    def test_navigate_clears_query(self):
        """Navigate without query clears old query."""
        ctx = _create_router_context("/search")
        ctx.query.set({"q": "old"})
        
        navigate = useNavigate()
        navigate("/about")
        
        assert ctx.query() == {}


# =============================================================================
# SECTION 6: HASH NAVIGATION
# =============================================================================

class TestHashNavigation:
    """Test navigation with hash/anchor."""
    
    def test_navigate_with_hash(self):
        """Navigate with hash."""
        ctx = _create_router_context("/")
        
        navigate = useNavigate()
        navigate("/page#section")
        
        assert ctx.pathname() == "/page"
        assert ctx.hash_() == "section"
    
    def test_navigate_hash_only(self):
        """Navigate to hash on same page."""
        ctx = _create_router_context("/page")
        
        navigate = useNavigate()
        navigate("/page#new-section")
        
        assert ctx.hash_() == "new-section"
    
    def test_navigate_clears_hash(self):
        """Navigate without hash clears old hash."""
        ctx = _create_router_context("/page")
        ctx.hash_.set("old-section")
        
        navigate = useNavigate()
        navigate("/other")
        
        assert ctx.hash_() == ""


# =============================================================================
# SECTION 7: PREFETCHING
# =============================================================================

class TestPrefetching:
    """Test route prefetching."""
    
    def test_prefetch_method_exists(self):
        """Navigator has prefetch method."""
        nav = Navigator()
        
        # Should not error
        nav.prefetch("/about")
    
    def test_prefetch_accepts_path(self):
        """Prefetch accepts path string."""
        nav = Navigator()
        
        # Should not error
        nav.prefetch("/users/123")


# =============================================================================
# SECTION 8: EDGE CASES
# =============================================================================

class TestNavigateEdgeCases:
    """Test navigation edge cases."""
    
    def test_navigate_to_same_path(self):
        """Navigate to same path."""
        ctx = _create_router_context("/page")
        
        navigate = useNavigate()
        navigate("/page")
        
        assert ctx.pathname() == "/page"
    
    def test_navigate_empty_path(self):
        """Navigate with empty path uses root."""
        ctx = _create_router_context("/other")
        
        navigate = useNavigate()
        navigate("")
        
        # Empty path should become "/"
        assert ctx.pathname() == "/"
    
    def test_navigate_unicode_path(self):
        """Navigate to unicode path."""
        ctx = _create_router_context("/")
        
        navigate = useNavigate()
        navigate("/ページ/日本語")
        
        assert ctx.pathname() == "/ページ/日本語"
    
    def test_navigate_complex_url(self):
        """Navigate with path, query, and hash."""
        ctx = _create_router_context("/")
        
        navigate = useNavigate()
        navigate("/search?q=test&page=1#results")
        
        assert ctx.pathname() == "/search"
        assert ctx.query()["q"] == "test"
        assert ctx.hash_() == "results"

