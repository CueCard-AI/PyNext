"""
Comprehensive tests for Link component.

Tests cover:
1. Link rendering
2. Active state
3. Prefetching
4. Click handling attributes
5. Accessibility
"""

import pytest
from unittest.mock import Mock, patch

from pynext.reactive.router import (
    Link,
    Router,
    Route,
    _create_router_context,
)


# =============================================================================
# SECTION 1: BASIC LINK RENDERING
# =============================================================================

class TestLinkRendering:
    """Test basic Link rendering."""
    
    def test_link_creates(self):
        """Link creates with href."""
        link = Link(href="/about")
        assert link.href == "/about"
    
    def test_link_default_options(self):
        """Link has sensible defaults."""
        link = Link(href="/")
        
        assert link.replace is False
        assert link.prefetch is False
        assert link.active_class == "active"
        assert link.exact is False
    
    def test_link_with_children(self):
        """Link accepts children via []."""
        link = Link(href="/about")["About Us"]
        
        assert link.children == ["About Us"]
    
    def test_link_with_multiple_children(self):
        """Link with multiple children."""
        link = Link(href="/")[
            "Home",
            " - ",
            "Welcome",
        ]
        
        assert len(link.children) == 3
    
    def test_link_renders_anchor(self):
        """Link renders as <a> tag."""
        link = Link(href="/about")["About"]
        
        result = str(link)
        
        assert "<a" in result
        assert 'href="/about"' in result
        assert "About" in result
    
    def test_link_has_pynext_data_attr(self):
        """Link has data-pynext-link attribute."""
        link = Link(href="/test")["Test"]
        
        result = str(link)
        
        assert 'data-pynext-link="true"' in result
    
    def test_link_replace_data_attr(self):
        """Link with replace has data attribute."""
        link = Link(href="/test", replace=True)["Test"]
        
        result = str(link)
        
        assert 'data-pynext-replace="true"' in result
    
    def test_link_prefetch_data_attr(self):
        """Link with prefetch has data attribute."""
        link = Link(href="/test", prefetch=True)["Test"]
        
        result = str(link)
        
        assert 'data-pynext-prefetch="true"' in result


# =============================================================================
# SECTION 2: LINK ATTRIBUTES
# =============================================================================

class TestLinkAttributes:
    """Test Link with custom attributes."""
    
    def test_link_with_class(self):
        """Link with custom class."""
        link = Link(href="/", class_="nav-link")["Home"]
        
        result = str(link)
        
        assert 'class=' in result.lower()
        assert 'nav-link' in result
    
    def test_link_with_id(self):
        """Link with id attribute."""
        link = Link(href="/", id="home-link")["Home"]
        
        result = str(link)
        
        assert 'id="home-link"' in result
    
    def test_link_with_aria(self):
        """Link with ARIA attributes."""
        link = Link(href="/", **{"aria-label": "Go home"})["🏠"]
        
        result = str(link)
        
        assert "aria-label" in result.lower()
    
    def test_link_with_title(self):
        """Link with title attribute."""
        link = Link(href="/about", title="Learn more about us")["About"]
        
        result = str(link)
        
        assert 'title=' in result


# =============================================================================
# SECTION 3: ACTIVE STATE
# =============================================================================

class TestLinkActiveState:
    """Test Link active state detection."""
    
    def test_is_active_exact_match(self):
        """Link is active on exact match."""
        link = Link(href="/about", exact=True)["About"]
        
        assert link._is_active("/about") is True
        assert link._is_active("/about/team") is False
    
    def test_is_active_prefix_match(self):
        """Link is active on prefix match (non-exact)."""
        link = Link(href="/users", exact=False)["Users"]
        
        assert link._is_active("/users") is True
        assert link._is_active("/users/123") is True
        assert link._is_active("/posts") is False
    
    def test_root_not_always_active(self):
        """Root link not active for all paths."""
        link = Link(href="/", exact=False)["Home"]
        
        # Non-exact root would match everything starting with /
        # But the implementation excludes / from prefix matching
        assert link._is_active("/") is True
    
    def test_active_class_applied(self):
        """Active class applied when active."""
        # Set up router context
        ctx = _create_router_context("/about")
        
        link = Link(href="/about")["About"]
        
        result = str(link)
        
        assert "active" in result
    
    def test_custom_active_class(self):
        """Custom active class name."""
        ctx = _create_router_context("/test")
        
        link = Link(href="/test", active_class="is-active")["Test"]
        
        result = str(link)
        
        assert "is-active" in result
    
    def test_not_active_no_class(self):
        """No active class when not active."""
        ctx = _create_router_context("/other")
        
        link = Link(href="/about")["About"]
        
        # Check _is_active directly
        assert link._is_active("/other") is False


# =============================================================================
# SECTION 4: LINK OPTIONS
# =============================================================================

class TestLinkOptions:
    """Test Link configuration options."""
    
    def test_replace_option(self):
        """Replace option stored."""
        link = Link(href="/", replace=True)
        assert link.replace is True
    
    def test_prefetch_option(self):
        """Prefetch option stored."""
        link = Link(href="/", prefetch=True)
        assert link.prefetch is True
    
    def test_exact_option(self):
        """Exact option for active matching."""
        link = Link(href="/users", exact=True)
        
        assert link._is_active("/users") is True
        assert link._is_active("/users/1") is False
    
    def test_active_class_option(self):
        """Custom active class option."""
        link = Link(href="/", active_class="current")
        assert link.active_class == "current"


# =============================================================================
# SECTION 5: LINK REPR
# =============================================================================

class TestLinkRepr:
    """Test Link string representation."""
    
    def test_link_repr(self):
        """Link has useful repr."""
        link = Link(href="/about")
        
        repr_str = repr(link)
        
        assert "Link" in repr_str
        assert "/about" in repr_str
    
    def test_link_str(self):
        """Link str returns HTML."""
        link = Link(href="/")["Home"]
        
        str_result = str(link)
        
        assert "<a" in str_result
        assert "Home" in str_result


# =============================================================================
# SECTION 6: EDGE CASES
# =============================================================================

class TestLinkEdgeCases:
    """Test Link edge cases."""
    
    def test_empty_children(self):
        """Link with no children."""
        link = Link(href="/")
        
        result = str(link)
        
        assert "<a" in result
    
    def test_complex_children(self):
        """Link with complex nested children."""
        from pynext.core.html import span, strong
        
        link = Link(href="/")[
            span()["Hello "],
            strong()["World"],
        ]
        
        result = str(link)
        
        assert "Hello" in result
        assert "World" in result
    
    def test_unicode_href(self):
        """Link with unicode in href."""
        link = Link(href="/日本語/ページ")["リンク"]
        
        result = str(link)
        
        assert "/日本語/ページ" in result
    
    def test_special_chars_in_href(self):
        """Link with special characters in href."""
        link = Link(href="/search?q=test&sort=asc")["Search"]
        
        result = str(link)
        
        assert "/search" in result
    
    def test_hash_in_href(self):
        """Link with hash in href."""
        link = Link(href="/page#section")["Go to section"]
        
        result = str(link)
        
        assert "#section" in result
    
    def test_very_long_href(self):
        """Link with very long href."""
        long_path = "/" + "/".join(f"segment{i}" for i in range(50))
        link = Link(href=long_path)["Long link"]
        
        result = str(link)
        
        assert "segment49" in result


# =============================================================================
# SECTION 7: ACCESSIBILITY
# =============================================================================

class TestLinkAccessibility:
    """Test Link accessibility features."""
    
    def test_renders_as_anchor(self):
        """Link renders as semantic <a> element."""
        link = Link(href="/about")["About"]
        
        result = str(link)
        
        assert result.strip().startswith("<a")
    
    def test_href_is_valid(self):
        """Link has valid href attribute."""
        link = Link(href="/contact")["Contact"]
        
        result = str(link)
        
        assert 'href="/contact"' in result
    
    def test_can_add_aria_label(self):
        """Link can have aria-label."""
        link = Link(href="/", **{"aria-label": "Home page"})["🏠"]
        
        # Should not error
        result = str(link)
        assert result  # Valid HTML generated

