"""
Comprehensive tests for useParams hook.

Tests cover:
1. Parameter access
2. Reactive updates
3. Type handling
4. Edge cases
"""

import pytest
from unittest.mock import Mock, patch

from pynext.reactive.router import (
    useParams,
    _create_router_context,
    Route,
    Router,
)


# =============================================================================
# SECTION 1: BASIC PARAMETER ACCESS
# =============================================================================

class TestBasicParams:
    """Test basic parameter access."""
    
    def test_use_params_returns_dict(self):
        """useParams returns a dict."""
        ctx = _create_router_context("/")
        
        params = useParams()
        
        assert isinstance(params, dict)
    
    def test_empty_params_when_no_route_params(self):
        """Returns empty dict for static route."""
        ctx = _create_router_context("/about")
        ctx.params.set({})
        
        params = useParams()
        
        assert params == {}
    
    def test_single_param(self):
        """Access single parameter."""
        ctx = _create_router_context("/users/123")
        ctx.params.set({"id": "123"})
        
        params = useParams()
        
        assert params["id"] == "123"
    
    def test_multiple_params(self):
        """Access multiple parameters."""
        ctx = _create_router_context("/users/1/posts/2")
        ctx.params.set({"userId": "1", "postId": "2"})
        
        params = useParams()
        
        assert params["userId"] == "1"
        assert params["postId"] == "2"
    
    def test_params_are_strings(self):
        """All params are strings."""
        ctx = _create_router_context("/items/42")
        ctx.params.set({"id": "42"})
        
        params = useParams()
        
        assert isinstance(params["id"], str)


# =============================================================================
# SECTION 2: REACTIVE UPDATES
# =============================================================================

class TestParamsReactivity:
    """Test params reactivity."""
    
    def test_params_update_on_navigation(self):
        """Params update when navigation occurs."""
        ctx = _create_router_context("/users/1")
        ctx.params.set({"id": "1"})
        ctx.routes = [Route("/users/:id", component=lambda: None).to_compiled()]
        
        # Initial params
        assert useParams()["id"] == "1"
        
        # Navigate
        ctx.navigate("/users/2")
        
        # Params updated
        assert useParams()["id"] == "2"
    
    def test_params_clear_on_different_route(self):
        """Params clear when navigating to different route."""
        ctx = _create_router_context("/users/1")
        ctx.params.set({"id": "1"})
        ctx.routes = [
            Route("/users/:id", component=lambda: None).to_compiled(),
            Route("/about", component=lambda: None).to_compiled(),
        ]
        
        # Navigate to static route
        ctx.navigate("/about")
        
        assert useParams() == {}


# =============================================================================
# SECTION 3: SPECIAL PARAM VALUES
# =============================================================================

class TestSpecialParamValues:
    """Test special parameter values."""
    
    def test_numeric_param(self):
        """Numeric parameter value."""
        ctx = _create_router_context("/items/123")
        ctx.params.set({"id": "123"})
        
        params = useParams()
        
        assert params["id"] == "123"
        assert int(params["id"]) == 123
    
    def test_uuid_param(self):
        """UUID parameter value."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        ctx = _create_router_context(f"/items/{uuid}")
        ctx.params.set({"id": uuid})
        
        params = useParams()
        
        assert params["id"] == uuid
    
    def test_slug_param(self):
        """Slug parameter value."""
        ctx = _create_router_context("/articles/my-awesome-article")
        ctx.params.set({"slug": "my-awesome-article"})
        
        params = useParams()
        
        assert params["slug"] == "my-awesome-article"
    
    def test_encoded_param(self):
        """URL-encoded parameter value."""
        ctx = _create_router_context("/search/hello%20world")
        ctx.params.set({"query": "hello%20world"})
        
        params = useParams()
        
        assert params["query"] == "hello%20world"
    
    def test_unicode_param(self):
        """Unicode parameter value."""
        ctx = _create_router_context("/users/日本語")
        ctx.params.set({"name": "日本語"})
        
        params = useParams()
        
        assert params["name"] == "日本語"
    
    def test_empty_string_param(self):
        """Empty string parameter."""
        ctx = _create_router_context("/users/")
        ctx.params.set({"id": ""})
        
        params = useParams()
        
        assert params["id"] == ""
    
    def test_special_chars_param(self):
        """Special characters in parameter."""
        ctx = _create_router_context("/files/doc.pdf")
        ctx.params.set({"filename": "doc.pdf"})
        
        params = useParams()
        
        assert params["filename"] == "doc.pdf"


# =============================================================================
# SECTION 4: PARAM DICT OPERATIONS
# =============================================================================

class TestParamDictOperations:
    """Test dict operations on params."""
    
    def test_get_with_default(self):
        """Get param with default."""
        ctx = _create_router_context("/")
        ctx.params.set({})
        
        params = useParams()
        
        assert params.get("missing", "default") == "default"
    
    def test_in_operator(self):
        """Check if param exists."""
        ctx = _create_router_context("/users/1")
        ctx.params.set({"id": "1"})
        
        params = useParams()
        
        assert "id" in params
        assert "missing" not in params
    
    def test_keys(self):
        """Get param keys."""
        ctx = _create_router_context("/")
        ctx.params.set({"a": "1", "b": "2"})
        
        params = useParams()
        
        assert set(params.keys()) == {"a", "b"}
    
    def test_values(self):
        """Get param values."""
        ctx = _create_router_context("/")
        ctx.params.set({"a": "1", "b": "2"})
        
        params = useParams()
        
        assert set(params.values()) == {"1", "2"}
    
    def test_items(self):
        """Get param items."""
        ctx = _create_router_context("/")
        ctx.params.set({"a": "1", "b": "2"})
        
        params = useParams()
        
        assert set(params.items()) == {("a", "1"), ("b", "2")}
    
    def test_len(self):
        """Get number of params."""
        ctx = _create_router_context("/")
        ctx.params.set({"a": "1", "b": "2", "c": "3"})
        
        params = useParams()
        
        assert len(params) == 3


# =============================================================================
# SECTION 5: WILDCARD PARAMS
# =============================================================================

class TestWildcardParams:
    """Test wildcard (*) parameter handling."""
    
    def test_wildcard_param(self):
        """Access wildcard parameter."""
        ctx = _create_router_context("/files/path/to/file.txt")
        ctx.params.set({"*": "path/to/file.txt"})
        
        params = useParams()
        
        assert params["*"] == "path/to/file.txt"
    
    def test_wildcard_empty(self):
        """Empty wildcard parameter."""
        ctx = _create_router_context("/files/")
        ctx.params.set({"*": ""})
        
        params = useParams()
        
        assert params["*"] == ""
    
    def test_wildcard_with_other_params(self):
        """Wildcard with other parameters."""
        ctx = _create_router_context("/users/1/files/path/to/doc")
        ctx.params.set({"id": "1", "*": "path/to/doc"})
        
        params = useParams()
        
        assert params["id"] == "1"
        assert params["*"] == "path/to/doc"


# =============================================================================
# SECTION 6: ERROR HANDLING
# =============================================================================

class TestParamsErrorHandling:
    """Test error handling for params."""
    
    def test_missing_param_raises_keyerror(self):
        """Missing param raises KeyError."""
        ctx = _create_router_context("/")
        ctx.params.set({})
        
        params = useParams()
        
        with pytest.raises(KeyError):
            _ = params["nonexistent"]
    
    def test_get_returns_none_for_missing(self):
        """Get returns None for missing param."""
        ctx = _create_router_context("/")
        ctx.params.set({})
        
        params = useParams()
        
        assert params.get("missing") is None


# =============================================================================
# SECTION 7: INTEGRATION
# =============================================================================

class TestParamsIntegration:
    """Test params with full router setup."""
    
    def test_params_from_router(self):
        """Params from Router context."""
        def UserPage():
            params = useParams()
            from pynext.core.html import div
            return div()[f"User: {params.get('id', 'none')}"]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/users/42"):
            router = Router()[
                Route("/users/:id", component=UserPage),
            ]
            
            result = str(router)
        
        assert "User: 42" in result

