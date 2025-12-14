"""
Comprehensive tests for route prefetching.

Tests cover:
1. Link prefetch attribute
2. Programmatic prefetching
3. Prefetch strategies
"""

import pytest
from unittest.mock import Mock, patch

from pynext.reactive.router import (
    Link,
    useNavigate,
    Navigator,
)


# =============================================================================
# SECTION 1: LINK PREFETCH ATTRIBUTE
# =============================================================================

class TestLinkPrefetch:
    """Test Link prefetch attribute."""
    
    def test_prefetch_default_false(self):
        """Prefetch defaults to False."""
        link = Link(href="/page")
        
        assert link.prefetch is False
    
    def test_prefetch_true(self):
        """Prefetch can be enabled."""
        link = Link(href="/page", prefetch=True)
        
        assert link.prefetch is True
    
    def test_prefetch_renders_data_attr(self):
        """Prefetch adds data attribute."""
        link = Link(href="/page", prefetch=True)["Page"]
        
        result = str(link)
        
        assert "data-pynext-prefetch" in result
    
    def test_no_prefetch_no_data_attr(self):
        """No prefetch means no data attribute."""
        link = Link(href="/page", prefetch=False)["Page"]
        
        result = str(link)
        
        assert "data-pynext-prefetch" not in result


# =============================================================================
# SECTION 2: PROGRAMMATIC PREFETCHING
# =============================================================================

class TestProgrammaticPrefetch:
    """Test programmatic prefetching."""
    
    def test_navigator_has_prefetch(self):
        """Navigator has prefetch method."""
        nav = Navigator()
        
        assert hasattr(nav, "prefetch")
    
    def test_prefetch_callable(self):
        """Prefetch is callable."""
        nav = Navigator()
        
        # Should not error
        nav.prefetch("/about")
    
    def test_prefetch_via_use_navigate(self):
        """Prefetch via useNavigate hook."""
        navigate = useNavigate()
        
        # Should not error
        navigate.prefetch("/page")
    
    def test_prefetch_multiple_paths(self):
        """Prefetch multiple paths."""
        nav = Navigator()
        
        # Should not error
        nav.prefetch("/page1")
        nav.prefetch("/page2")
        nav.prefetch("/page3")


# =============================================================================
# SECTION 3: PREFETCH WITH PARAMS
# =============================================================================

class TestPrefetchWithParams:
    """Test prefetching dynamic routes."""
    
    def test_prefetch_with_param(self):
        """Prefetch path with parameter."""
        nav = Navigator()
        
        # Should not error
        nav.prefetch("/users/123")
    
    def test_prefetch_with_multiple_params(self):
        """Prefetch with multiple params."""
        nav = Navigator()
        
        nav.prefetch("/users/1/posts/2")
    
    def test_prefetch_with_query(self):
        """Prefetch with query string."""
        nav = Navigator()
        
        nav.prefetch("/search?q=test")


# =============================================================================
# SECTION 4: LINK PREFETCH PATTERNS
# =============================================================================

class TestLinkPrefetchPatterns:
    """Test common prefetch patterns."""
    
    def test_navigation_links_with_prefetch(self):
        """Navigation links can prefetch."""
        links = [
            Link(href="/", prefetch=True)["Home"],
            Link(href="/about", prefetch=True)["About"],
            Link(href="/contact", prefetch=True)["Contact"],
        ]
        
        for link in links:
            result = str(link)
            assert "data-pynext-prefetch" in result
    
    def test_selective_prefetch(self):
        """Only some links prefetch."""
        important = Link(href="/dashboard", prefetch=True)["Dashboard"]
        less_important = Link(href="/settings", prefetch=False)["Settings"]
        
        assert "data-pynext-prefetch" in str(important)
        assert "data-pynext-prefetch" not in str(less_important)


# =============================================================================
# SECTION 5: EDGE CASES
# =============================================================================

class TestPrefetchEdgeCases:
    """Test prefetch edge cases."""
    
    def test_prefetch_same_path(self):
        """Prefetch current path."""
        nav = Navigator()
        
        # Should not error
        nav.prefetch("/")
    
    def test_prefetch_empty_path(self):
        """Prefetch empty path."""
        nav = Navigator()
        
        nav.prefetch("")
    
    def test_prefetch_with_hash(self):
        """Prefetch with hash."""
        nav = Navigator()
        
        nav.prefetch("/page#section")
    
    def test_prefetch_unicode_path(self):
        """Prefetch unicode path."""
        nav = Navigator()
        
        nav.prefetch("/ページ/日本語")

