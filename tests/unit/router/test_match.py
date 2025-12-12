"""
Comprehensive tests for useMatch hook.

Tests cover:
1. Pattern matching
2. Param extraction
3. No match cases
4. Dynamic matching
"""

import pytest
from unittest.mock import Mock, patch

from pynext.reactive.router import (
    useMatch,
    _create_router_context,
)


# =============================================================================
# SECTION 1: BASIC MATCHING
# =============================================================================

class TestBasicMatch:
    """Test basic pattern matching."""
    
    def test_exact_match(self):
        """Exact path matches."""
        ctx = _create_router_context("/about")
        
        result = useMatch("/about")
        
        assert result == {}
    
    def test_no_match(self):
        """Non-matching path returns None."""
        ctx = _create_router_context("/about")
        
        result = useMatch("/contact")
        
        assert result is None
    
    def test_root_match(self):
        """Root path matches."""
        ctx = _create_router_context("/")
        
        result = useMatch("/")
        
        assert result == {}


# =============================================================================
# SECTION 2: PARAM MATCHING
# =============================================================================

class TestParamMatch:
    """Test matching with parameters."""
    
    def test_single_param_match(self):
        """Match with single param."""
        ctx = _create_router_context("/users/123")
        
        result = useMatch("/users/:id")
        
        assert result == {"id": "123"}
    
    def test_multiple_param_match(self):
        """Match with multiple params."""
        ctx = _create_router_context("/users/1/posts/2")
        
        result = useMatch("/users/:userId/posts/:postId")
        
        assert result == {"userId": "1", "postId": "2"}
    
    def test_param_no_match(self):
        """Param pattern doesn't match different structure."""
        ctx = _create_router_context("/posts/123")
        
        result = useMatch("/users/:id")
        
        assert result is None


# =============================================================================
# SECTION 3: REACTIVE MATCHING
# =============================================================================

class TestReactiveMatch:
    """Test reactive behavior of useMatch."""
    
    def test_match_updates_on_navigation(self):
        """Match result changes on navigation."""
        ctx = _create_router_context("/users/1")
        
        # Initial match
        result1 = useMatch("/users/:id")
        assert result1 == {"id": "1"}
        
        # Navigate
        ctx.pathname.set("/users/2")
        
        # New match
        result2 = useMatch("/users/:id")
        assert result2 == {"id": "2"}
    
    def test_match_becomes_none(self):
        """Match becomes None when route changes."""
        ctx = _create_router_context("/users/1")
        
        # Initial match
        result1 = useMatch("/users/:id")
        assert result1 is not None
        
        # Navigate away
        ctx.pathname.set("/about")
        
        # No longer matches
        result2 = useMatch("/users/:id")
        assert result2 is None


# =============================================================================
# SECTION 4: CONDITIONAL RENDERING
# =============================================================================

class TestConditionalRendering:
    """Test useMatch for conditional rendering."""
    
    def test_match_truthy_when_matched(self):
        """Match is truthy when matched."""
        ctx = _create_router_context("/users/1")
        
        result = useMatch("/users/:id")
        
        assert result  # Truthy (non-empty dict)
    
    def test_match_falsy_when_not_matched(self):
        """Match is falsy when not matched."""
        ctx = _create_router_context("/about")
        
        result = useMatch("/users/:id")
        
        assert not result  # Falsy (None)
    
    def test_conditional_pattern(self):
        """Common conditional rendering pattern."""
        ctx = _create_router_context("/users/123")
        
        match = useMatch("/users/:id")
        if match:
            user_id = match["id"]
            assert user_id == "123"
        else:
            pytest.fail("Should have matched")


# =============================================================================
# SECTION 5: WILDCARD MATCHING
# =============================================================================

class TestWildcardMatch:
    """Test wildcard pattern matching."""
    
    def test_wildcard_match(self):
        """Wildcard pattern matches."""
        ctx = _create_router_context("/files/path/to/file.txt")
        
        result = useMatch("/files/*")
        
        assert result is not None
        assert result["*"] == "path/to/file.txt"
    
    def test_wildcard_empty(self):
        """Wildcard with empty path."""
        ctx = _create_router_context("/files/")
        
        result = useMatch("/files/*")
        
        assert result is not None


# =============================================================================
# SECTION 6: EDGE CASES
# =============================================================================

class TestMatchEdgeCases:
    """Test edge cases for useMatch."""
    
    def test_match_similar_paths(self):
        """Match distinguishes similar paths."""
        ctx = _create_router_context("/users")
        
        # Exact match
        assert useMatch("/users") == {}
        
        # Should not match with extra segment
        assert useMatch("/users/:id") is None
    
    def test_match_unicode_path(self):
        """Match with unicode path."""
        ctx = _create_router_context("/ユーザー/123")
        
        result = useMatch("/ユーザー/:id")
        
        assert result == {"id": "123"}
    
    def test_match_encoded_chars(self):
        """Match with encoded characters."""
        ctx = _create_router_context("/search/hello%20world")
        
        result = useMatch("/search/:query")
        
        assert result == {"query": "hello%20world"}
    
    def test_multiple_matches_in_component(self):
        """Multiple useMatch calls in same context."""
        ctx = _create_router_context("/users/1")
        
        user_match = useMatch("/users/:id")
        post_match = useMatch("/posts/:id")
        
        assert user_match == {"id": "1"}
        assert post_match is None

