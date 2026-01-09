"""
Phase 34.3: CSS Image Value Tests

Tests for CSS image value factory methods:
- CSS.url() - URL images
- CSS.linearGradient() - linear gradients
- CSS.radialGradient() - radial gradients
- CSS.conicGradient() - conic gradients

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# CSS.url() Tests (3 tests)
# =============================================================================

class TestURLImageFactory:
    """Tests for CSS.url() factory method."""
    
    def test_url_basic(self):
        """CSS.url() should create a URL image value."""
        code = 'bg = CSS.url("/images/background.png")'
        result = transpile(code)
        assert 'CSS.url(' in result
        assert '/images/background.png' in result
    
    def test_url_in_style_map(self):
        """CSS.url() should work with attributeStyleMap."""
        code = '''
image = CSS.url("/hero.jpg")
el.attributeStyleMap.set("background-image", image)
'''
        result = transpile(code)
        assert 'CSS.url("/hero.jpg")' in result
        assert 'set("background-image"' in result
    
    def test_url_with_external_source(self):
        """CSS.url() should handle external URLs."""
        code = 'icon = CSS.url("https://example.com/icon.svg")'
        result = transpile(code)
        assert 'CSS.url("https://example.com/icon.svg")' in result


# =============================================================================
# CSS.linearGradient() Tests (3 tests)
# =============================================================================

class TestLinearGradientFactory:
    """Tests for CSS.linearGradient() factory method."""
    
    def test_linear_gradient_basic(self):
        """CSS.linearGradient() should create a linear gradient."""
        code = 'gradient = CSS.linearGradient("to right", ["red", "blue"])'
        result = transpile(code)
        assert 'CSS.linearGradient' in result
        assert 'to right' in result
    
    def test_linear_gradient_angle(self):
        """CSS.linearGradient() should handle angle syntax."""
        code = 'gradient = CSS.linearGradient("45deg", ["#ff0000", "#0000ff"])'
        result = transpile(code)
        assert 'CSS.linearGradient' in result
        assert '45deg' in result
    
    def test_linear_gradient_multiple_stops(self):
        """CSS.linearGradient() should handle multiple color stops."""
        code = 'rainbow = CSS.linearGradient("to right", ["red", "orange", "yellow", "green", "blue"])'
        result = transpile(code)
        assert 'CSS.linearGradient' in result


# =============================================================================
# CSS.radialGradient() Tests (2 tests)
# =============================================================================

class TestRadialGradientFactory:
    """Tests for CSS.radialGradient() factory method."""
    
    def test_radial_gradient_circle(self):
        """CSS.radialGradient() should create a circle gradient."""
        code = 'glow = CSS.radialGradient("circle", ["yellow", "transparent"])'
        result = transpile(code)
        assert 'CSS.radialGradient' in result
        assert 'circle' in result
    
    def test_radial_gradient_ellipse(self):
        """CSS.radialGradient() should handle ellipse shapes."""
        code = 'oval = CSS.radialGradient("ellipse at center", ["white", "gray"])'
        result = transpile(code)
        assert 'CSS.radialGradient' in result
        assert 'ellipse' in result


# =============================================================================
# CSS.conicGradient() Tests (2 tests)
# =============================================================================

class TestConicGradientFactory:
    """Tests for CSS.conicGradient() factory method."""
    
    def test_conic_gradient_basic(self):
        """CSS.conicGradient() should create a conic gradient."""
        code = 'pie = CSS.conicGradient("from 0deg", ["red", "blue", "red"])'
        result = transpile(code)
        assert 'CSS.conicGradient' in result
        assert 'from 0deg' in result
    
    def test_conic_gradient_position(self):
        """CSS.conicGradient() should handle position syntax."""
        code = 'dial = CSS.conicGradient("from 90deg at center", ["black", "white", "black"])'
        result = transpile(code)
        assert 'CSS.conicGradient' in result
        assert 'from 90deg at center' in result

