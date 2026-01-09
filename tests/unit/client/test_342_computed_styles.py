"""
Phase 34.2: Computed Styles Tests

Tests for window.getComputedStyle and computed style access:
- Basic getComputedStyle
- Pseudo-element styles
- Property access
- CSS variable access

Total: 25 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Basic getComputedStyle Tests (8 tests)
# =============================================================================

class TestGetComputedStyleBasic:
    """Tests for basic window.getComputedStyle usage."""
    
    def test_get_computed_style_basic(self):
        """window.getComputedStyle should pass through unchanged."""
        code = '''
from pynext.client import window
computed = window.getComputedStyle(el)
'''
        result = transpile(code)
        assert "window.getComputedStyle" in result
        assert "__py." not in result
    
    def test_get_computed_style_property(self):
        """Accessing computed style property should work."""
        code = '''
from pynext.client import window
computed = window.getComputedStyle(el)
width = computed.width
'''
        result = transpile(code)
        assert "getComputedStyle" in result
        assert "width" in result
    
    def test_get_computed_style_background(self):
        """Accessing computed backgroundColor should work."""
        code = '''
from pynext.client import window
computed = window.getComputedStyle(el)
bg = computed.backgroundColor
'''
        result = transpile(code)
        assert "backgroundColor" in result
    
    def test_get_computed_style_chained(self):
        """Chained computed style access should work."""
        code = '''
from pynext.client import window
width = window.getComputedStyle(el).width
'''
        result = transpile(code)
        assert "getComputedStyle" in result
        assert "width" in result
    
    def test_get_computed_style_multiple_props(self):
        """Accessing multiple computed properties should work."""
        code = '''
from pynext.client import window
computed = window.getComputedStyle(el)
w = computed.width
h = computed.height
bg = computed.backgroundColor
'''
        result = transpile(code)
        assert "width" in result
        assert "height" in result
        assert "backgroundColor" in result
    
    def test_get_computed_style_from_document(self):
        """getComputedStyle on document element should work."""
        code = '''
from pynext.client import window, document
computed = window.getComputedStyle(document.body)
'''
        result = transpile(code)
        assert "document.body" in result
    
    def test_get_computed_style_font_size(self):
        """Accessing computed fontSize should work."""
        code = '''
from pynext.client import window
computed = window.getComputedStyle(el)
size = computed.fontSize
'''
        result = transpile(code)
        assert "fontSize" in result
    
    def test_get_computed_style_transform(self):
        """Accessing computed transform should work."""
        code = '''
from pynext.client import window
computed = window.getComputedStyle(el)
transform = computed.transform
'''
        result = transpile(code)
        assert "transform" in result


# =============================================================================
# Pseudo-Element Tests (5 tests)
# =============================================================================

class TestGetComputedStylePseudo:
    """Tests for computed styles on pseudo-elements."""
    
    def test_computed_style_before(self):
        """getComputedStyle with ::before should work."""
        code = '''
from pynext.client import window
before = window.getComputedStyle(el, "::before")
'''
        result = transpile(code)
        assert "::before" in result
    
    def test_computed_style_after(self):
        """getComputedStyle with ::after should work."""
        code = '''
from pynext.client import window
after = window.getComputedStyle(el, "::after")
'''
        result = transpile(code)
        assert "::after" in result
    
    def test_computed_style_before_content(self):
        """Accessing ::before content should work."""
        code = '''
from pynext.client import window
before = window.getComputedStyle(el, "::before")
content = before.content
'''
        result = transpile(code)
        assert "::before" in result
        assert "content" in result
    
    def test_computed_style_after_background(self):
        """Accessing ::after backgroundColor should work."""
        code = '''
from pynext.client import window
after = window.getComputedStyle(el, "::after")
bg = after.backgroundColor
'''
        result = transpile(code)
        assert "::after" in result
        assert "backgroundColor" in result
    
    def test_computed_style_placeholder(self):
        """getComputedStyle with ::placeholder should work."""
        code = '''
from pynext.client import window
placeholder = window.getComputedStyle(input_el, "::placeholder")
color = placeholder.color
'''
        result = transpile(code)
        assert "::placeholder" in result


# =============================================================================
# getPropertyValue Tests (5 tests)
# =============================================================================

class TestGetPropertyValue:
    """Tests for getPropertyValue on computed styles."""
    
    def test_computed_get_property_value(self):
        """getPropertyValue on computed style should work."""
        code = '''
from pynext.client import window
computed = window.getComputedStyle(el)
width = computed.getPropertyValue("width")
'''
        result = transpile(code)
        assert "getPropertyValue" in result
        assert '"width"' in result
    
    def test_computed_get_css_var(self):
        """getPropertyValue for CSS variable should work."""
        code = '''
from pynext.client import window
computed = window.getComputedStyle(el)
primary = computed.getPropertyValue("--primary-color")
'''
        result = transpile(code)
        assert "--primary-color" in result
    
    def test_computed_get_kebab_case(self):
        """getPropertyValue with kebab-case should work."""
        code = '''
from pynext.client import window
computed = window.getComputedStyle(el)
bg = computed.getPropertyValue("background-color")
'''
        result = transpile(code)
        assert "background-color" in result
    
    def test_computed_get_root_var(self):
        """getPropertyValue on :root CSS variable should work."""
        code = '''
from pynext.client import window, document
computed = window.getComputedStyle(document.documentElement)
theme = computed.getPropertyValue("--theme-color")
'''
        result = transpile(code)
        assert "documentElement" in result
        assert "--theme-color" in result
    
    def test_computed_chained_get_property(self):
        """Chained getPropertyValue should work."""
        code = '''
from pynext.client import window
width = window.getComputedStyle(el).getPropertyValue("width")
'''
        result = transpile(code)
        assert "getPropertyValue" in result


# =============================================================================
# matchMedia Tests (7 tests)
# =============================================================================

class TestMatchMedia:
    """Tests for window.matchMedia."""
    
    def test_match_media_basic(self):
        """window.matchMedia should pass through unchanged."""
        code = '''
from pynext.client import window
mql = window.matchMedia("(max-width: 768px)")
'''
        result = transpile(code)
        assert "window.matchMedia" in result
        assert "(max-width: 768px)" in result
    
    def test_match_media_matches(self):
        """matchMedia.matches should work."""
        code = '''
from pynext.client import window
is_mobile = window.matchMedia("(max-width: 768px)").matches
'''
        result = transpile(code)
        assert "matches" in result
    
    def test_match_media_dark_mode(self):
        """matchMedia for dark mode should work."""
        code = '''
from pynext.client import window
prefers_dark = window.matchMedia("(prefers-color-scheme: dark)").matches
'''
        result = transpile(code)
        assert "prefers-color-scheme: dark" in result
    
    def test_match_media_reduced_motion(self):
        """matchMedia for reduced motion should work."""
        code = '''
from pynext.client import window
reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
'''
        result = transpile(code)
        assert "prefers-reduced-motion" in result
    
    def test_match_media_in_condition(self):
        """matchMedia in condition should work."""
        code = '''
from pynext.client import window
if window.matchMedia("(min-width: 1024px)").matches:
    layout = "desktop"
else:
    layout = "mobile"
'''
        result = transpile(code)
        assert "matchMedia" in result
        assert "matches" in result
    
    def test_match_media_media_property(self):
        """matchMedia.media should work."""
        code = '''
from pynext.client import window
mql = window.matchMedia("(max-width: 768px)")
query = mql.media
'''
        result = transpile(code)
        assert "media" in result
    
    def test_match_media_event_listener(self):
        """matchMedia addEventListener should work."""
        code = '''
from pynext.client import window

def on_change(event):
    if event.matches:
        print("Mobile")

mql = window.matchMedia("(max-width: 768px)")
mql.addEventListener("change", on_change)
'''
        result = transpile(code)
        assert "addEventListener" in result
        assert '"change"' in result

