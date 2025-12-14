"""
Comprehensive tests for useSearchParams hook.

Tests cover:
1. Query param access
2. Query param updates
3. Multiple params
4. Special characters
5. Array params
"""

import pytest
from unittest.mock import Mock, patch

from pynext.reactive.router import (
    useSearchParams,
    useLocation,
    _create_router_context,
)


# =============================================================================
# SECTION 1: BASIC QUERY ACCESS
# =============================================================================

class TestBasicQueryAccess:
    """Test basic query parameter access."""
    
    def test_use_search_params_returns_tuple(self):
        """useSearchParams returns tuple."""
        ctx = _create_router_context("/")
        
        result = useSearchParams()
        
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_empty_query(self):
        """Empty query returns empty dict."""
        ctx = _create_router_context("/search")
        ctx.query.set({})
        
        params, _ = useSearchParams()
        
        assert params == {}
    
    def test_single_param(self):
        """Access single query param."""
        ctx = _create_router_context("/search")
        ctx.query.set({"q": "test"})
        
        params, _ = useSearchParams()
        
        assert params["q"] == "test"
    
    def test_multiple_params(self):
        """Access multiple query params."""
        ctx = _create_router_context("/search")
        ctx.query.set({"q": "test", "page": "1", "sort": "asc"})
        
        params, _ = useSearchParams()
        
        assert params["q"] == "test"
        assert params["page"] == "1"
        assert params["sort"] == "asc"


# =============================================================================
# SECTION 2: QUERY UPDATES
# =============================================================================

class TestQueryUpdates:
    """Test query parameter updates."""
    
    def test_set_params_updates(self):
        """Setting params updates signal."""
        ctx = _create_router_context("/search")
        ctx.query.set({})
        
        _, setParams = useSearchParams()
        setParams({"q": "new"})
        
        assert ctx.query()["q"] == "new"
    
    def test_set_replaces_all_params(self):
        """Setting params replaces all."""
        ctx = _create_router_context("/search")
        ctx.query.set({"old": "value"})
        
        _, setParams = useSearchParams()
        setParams({"new": "value"})
        
        query = ctx.query()
        assert "old" not in query
        assert query["new"] == "value"
    
    def test_clear_params(self):
        """Clear all params."""
        ctx = _create_router_context("/search")
        ctx.query.set({"q": "test"})
        
        _, setParams = useSearchParams()
        setParams({})
        
        assert ctx.query() == {}


# =============================================================================
# SECTION 3: SPECIAL CHARACTERS
# =============================================================================

class TestQuerySpecialChars:
    """Test special characters in query params."""
    
    def test_space_in_value(self):
        """Space in query value."""
        ctx = _create_router_context("/")
        ctx.query.set({"q": "hello world"})
        
        params, _ = useSearchParams()
        
        assert params["q"] == "hello world"
    
    def test_unicode_value(self):
        """Unicode in query value."""
        ctx = _create_router_context("/")
        ctx.query.set({"q": "日本語"})
        
        params, _ = useSearchParams()
        
        assert params["q"] == "日本語"
    
    def test_special_chars_value(self):
        """Special characters in value."""
        ctx = _create_router_context("/")
        ctx.query.set({"q": "test&value=123"})
        
        params, _ = useSearchParams()
        
        assert params["q"] == "test&value=123"
    
    def test_empty_value(self):
        """Empty query value."""
        ctx = _create_router_context("/")
        ctx.query.set({"flag": ""})
        
        params, _ = useSearchParams()
        
        assert params["flag"] == ""


# =============================================================================
# SECTION 4: NAVIGATION WITH QUERY
# =============================================================================

class TestNavigationWithQuery:
    """Test query params during navigation."""
    
    def test_query_preserved_on_path_change(self):
        """Query updated independently of pathname."""
        ctx = _create_router_context("/page1")
        ctx.query.set({"q": "test"})
        
        # Navigate to new path with new query
        ctx.navigate("/page2?q=newtest")
        
        params, _ = useSearchParams()
        assert params["q"] == "newtest"
    
    def test_query_cleared_on_navigation_without_query(self):
        """Query cleared when navigating without query."""
        ctx = _create_router_context("/search")
        ctx.query.set({"q": "test"})
        
        ctx.navigate("/about")
        
        assert ctx.query() == {}


# =============================================================================
# SECTION 5: USE LOCATION
# =============================================================================

class TestUseLocation:
    """Test useLocation hook."""
    
    def test_location_returns_location(self):
        """useLocation returns Location object."""
        ctx = _create_router_context("/page")
        
        location = useLocation()
        
        assert hasattr(location, "pathname")
        assert hasattr(location, "search")
        assert hasattr(location, "hash")
    
    def test_location_pathname(self):
        """Location has correct pathname."""
        ctx = _create_router_context("/users/123")
        
        location = useLocation()
        
        assert location.pathname == "/users/123"
    
    def test_location_search(self):
        """Location has correct search string."""
        ctx = _create_router_context("/search")
        ctx.query.set({"q": "test"})
        
        location = useLocation()
        
        assert "q=test" in location.search
    
    def test_location_hash(self):
        """Location has correct hash."""
        ctx = _create_router_context("/page")
        ctx.hash_.set("section")
        
        location = useLocation()
        
        assert location.hash == "#section"
    
    def test_location_empty_search(self):
        """Location with no query."""
        ctx = _create_router_context("/page")
        ctx.query.set({})
        
        location = useLocation()
        
        assert location.search == ""
    
    def test_location_empty_hash(self):
        """Location with no hash."""
        ctx = _create_router_context("/page")
        ctx.hash_.set("")
        
        location = useLocation()
        
        assert location.hash == ""


# =============================================================================
# SECTION 6: DICT OPERATIONS
# =============================================================================

class TestQueryDictOperations:
    """Test dict operations on query params."""
    
    def test_get_with_default(self):
        """Get param with default."""
        ctx = _create_router_context("/")
        ctx.query.set({})
        
        params, _ = useSearchParams()
        
        assert params.get("missing", "default") == "default"
    
    def test_in_operator(self):
        """Check if param exists."""
        ctx = _create_router_context("/")
        ctx.query.set({"exists": "yes"})
        
        params, _ = useSearchParams()
        
        assert "exists" in params
        assert "missing" not in params
    
    def test_len(self):
        """Get number of params."""
        ctx = _create_router_context("/")
        ctx.query.set({"a": "1", "b": "2", "c": "3"})
        
        params, _ = useSearchParams()
        
        assert len(params) == 3


# =============================================================================
# SECTION 7: EDGE CASES
# =============================================================================

class TestQueryEdgeCases:
    """Test query edge cases."""
    
    def test_very_long_value(self):
        """Very long query value."""
        long_value = "x" * 1000
        ctx = _create_router_context("/")
        ctx.query.set({"long": long_value})
        
        params, _ = useSearchParams()
        
        assert params["long"] == long_value
    
    def test_many_params(self):
        """Many query parameters."""
        many_params = {f"param{i}": f"value{i}" for i in range(50)}
        ctx = _create_router_context("/")
        ctx.query.set(many_params)
        
        params, _ = useSearchParams()
        
        assert len(params) == 50
    
    def test_numeric_key(self):
        """Numeric-looking key."""
        ctx = _create_router_context("/")
        ctx.query.set({"123": "value"})
        
        params, _ = useSearchParams()
        
        assert params["123"] == "value"

