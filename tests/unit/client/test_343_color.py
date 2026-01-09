"""
Phase 34.3: CSS Color Tests

Tests for CSS color factory methods and CSSColor manipulation.
Verifies that all color APIs transpile correctly to JavaScript.

Total: 35 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Color Factory Tests - Basic Color Spaces (10 tests)
# =============================================================================

class TestColorFactory:
    """Tests for CSS color factory methods."""
    
    def test_css_rgb(self):
        """CSS.rgb(r, g, b) should pass through unchanged."""
        code = 'color = CSS.rgb(255, 0, 0)'
        result = transpile(code)
        assert 'CSS.rgb(255, 0, 0)' in result
        assert "__py." not in result
    
    def test_css_rgba(self):
        """CSS.rgb with alpha should pass through unchanged."""
        code = 'color = CSS.rgb(255, 0, 0, 0.5)'
        result = transpile(code)
        assert 'CSS.rgb(255, 0, 0, 0.5)' in result
    
    def test_css_hsl(self):
        """CSS.hsl(h, s, l) should pass through unchanged."""
        code = 'color = CSS.hsl(0, 100, 50)'
        result = transpile(code)
        assert 'CSS.hsl(0, 100, 50)' in result
    
    def test_css_hsla(self):
        """CSS.hsl with alpha should pass through unchanged."""
        code = 'color = CSS.hsl(240, 100, 50, 0.8)'
        result = transpile(code)
        assert 'CSS.hsl(240, 100, 50, 0.8)' in result
    
    def test_css_hwb(self):
        """CSS.hwb should pass through unchanged."""
        code = 'color = CSS.hwb(0, 0, 0)'
        result = transpile(code)
        assert 'CSS.hwb(0, 0, 0)' in result
    
    def test_css_oklch(self):
        """CSS.oklch should pass through unchanged."""
        code = 'color = CSS.oklch(0.7, 0.15, 30)'
        result = transpile(code)
        assert 'CSS.oklch(0.7, 0.15, 30)' in result
    
    def test_css_oklab(self):
        """CSS.oklab should pass through unchanged."""
        code = 'color = CSS.oklab(0.7, 0.1, 0.1)'
        result = transpile(code)
        assert 'CSS.oklab(0.7, 0.1, 0.1)' in result
    
    def test_css_lab(self):
        """CSS.lab should pass through unchanged."""
        code = 'color = CSS.lab(50, 40, -60)'
        result = transpile(code)
        # Negative numbers may get parentheses
        assert 'CSS.lab' in result
        assert '50' in result and '40' in result and '60' in result
    
    def test_css_lch(self):
        """CSS.lch should pass through unchanged."""
        code = 'color = CSS.lch(50, 100, 30)'
        result = transpile(code)
        assert 'CSS.lch(50, 100, 30)' in result
    
    def test_css_named_color(self):
        """CSS.color('name') should pass through unchanged."""
        code = 'color = CSS.color("rebeccapurple")'
        result = transpile(code)
        assert 'CSS.color("rebeccapurple")' in result


# =============================================================================
# Color Manipulation Tests (12 tests)
# =============================================================================

class TestColorManipulation:
    """Tests for CSSColor manipulation methods."""
    
    def test_lighten(self):
        """color.lighten(20) should pass through unchanged."""
        code = '''
color = CSS.rgb(100, 100, 100)
lighter = color.lighten(20)
'''
        result = transpile(code)
        assert 'lighten(20)' in result
        assert "__py." not in result
    
    def test_darken(self):
        """color.darken(20) should pass through unchanged."""
        code = '''
color = CSS.rgb(200, 200, 200)
darker = color.darken(20)
'''
        result = transpile(code)
        assert 'darken(20)' in result
    
    def test_saturate(self):
        """color.saturate(20) should pass through unchanged."""
        code = '''
color = CSS.hsl(0, 50, 50)
more_vivid = color.saturate(20)
'''
        result = transpile(code)
        assert 'saturate(20)' in result
    
    def test_desaturate(self):
        """color.desaturate(20) should pass through unchanged."""
        code = '''
color = CSS.hsl(0, 100, 50)
muted = color.desaturate(20)
'''
        result = transpile(code)
        assert 'desaturate(20)' in result
    
    def test_rotate_hue(self):
        """color.rotate(180) should pass through (complement)."""
        code = '''
color = CSS.hsl(0, 100, 50)
complement = color.rotate(180)
'''
        result = transpile(code)
        assert 'rotate(180)' in result
    
    def test_invert_color(self):
        """color.invert() should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 0, 0)
inverted = color.invert()
'''
        result = transpile(code)
        assert 'invert()' in result
    
    def test_grayscale(self):
        """color.grayscale() should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 128, 0)
gray = color.grayscale()
'''
        result = transpile(code)
        assert 'grayscale()' in result
    
    def test_set_alpha(self):
        """color.setAlpha(0.5) should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 0, 0)
transparent = color.setAlpha(0.5)
'''
        result = transpile(code)
        assert 'setAlpha(0.5)' in result
    
    def test_fade_in(self):
        """color.fadeIn(0.2) should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 0, 0, 0.5)
more_opaque = color.fadeIn(0.2)
'''
        result = transpile(code)
        assert 'fadeIn(0.2)' in result
    
    def test_fade_out(self):
        """color.fadeOut(0.2) should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 0, 0)
more_transparent = color.fadeOut(0.2)
'''
        result = transpile(code)
        assert 'fadeOut(0.2)' in result
    
    def test_mix_colors(self):
        """color.mix(other, weight) should pass through unchanged."""
        code = '''
red = CSS.rgb(255, 0, 0)
blue = CSS.rgb(0, 0, 255)
purple = red.mix(blue, 0.5)
'''
        result = transpile(code)
        assert 'mix(' in result
    
    def test_chained_manipulation(self):
        """Chained color manipulation should work."""
        code = '''
base = CSS.rgb(100, 100, 100)
result = base.lighten(20).saturate(10)
'''
        result = transpile(code)
        assert 'lighten(20)' in result
        assert 'saturate(10)' in result


# =============================================================================
# Color Conversion Tests (6 tests)
# =============================================================================

class TestColorConversion:
    """Tests for CSSColor conversion methods."""
    
    def test_to_rgb(self):
        """color.toRGB() should pass through unchanged."""
        code = '''
color = CSS.hsl(0, 100, 50)
rgb = color.toRGB()
'''
        result = transpile(code)
        assert 'toRGB()' in result
    
    def test_to_hsl(self):
        """color.toHSL() should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 0, 0)
hsl = color.toHSL()
'''
        result = transpile(code)
        assert 'toHSL()' in result
    
    def test_to_oklch(self):
        """color.toOKLCH() should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 0, 0)
oklch = color.toOKLCH()
'''
        result = transpile(code)
        assert 'toOKLCH()' in result
    
    def test_to_string(self):
        """color.toString() should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 0, 0)
s = color.toString()
'''
        result = transpile(code)
        assert 'toString()' in result
    
    def test_to_hex(self):
        """color.toHex() should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 0, 0)
hex_str = color.toHex()
'''
        result = transpile(code)
        assert 'toHex()' in result
    
    def test_hex_factory(self):
        """CSS.hex('#ff0000') should pass through unchanged."""
        code = 'color = CSS.hex("#ff0000")'
        result = transpile(code)
        assert 'CSS.hex("#ff0000")' in result


# =============================================================================
# Color Property Tests (4 tests)
# =============================================================================

class TestColorProperties:
    """Tests for CSSColor property access."""
    
    def test_red_component(self):
        """color.red should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 128, 64)
r = color.red
'''
        result = transpile(code)
        assert 'color.red' in result
    
    def test_green_component(self):
        """color.green should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 128, 64)
g = color.green
'''
        result = transpile(code)
        assert 'color.green' in result
    
    def test_hue_component(self):
        """color.hue should pass through unchanged."""
        code = '''
color = CSS.hsl(180, 100, 50)
h = color.hue
'''
        result = transpile(code)
        assert 'color.hue' in result
    
    def test_alpha_component(self):
        """color.alpha should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 0, 0, 0.5)
a = color.alpha
'''
        result = transpile(code)
        assert 'color.alpha' in result


# =============================================================================
# Color Utility Tests (3 tests)
# =============================================================================

class TestColorUtilities:
    """Tests for CSSColor utility methods."""
    
    def test_luminance(self):
        """color.luminance() should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 255, 255)
lum = color.luminance()
'''
        result = transpile(code)
        assert 'luminance()' in result
    
    def test_is_light(self):
        """color.isLight() should pass through unchanged."""
        code = '''
color = CSS.rgb(255, 255, 255)
light = color.isLight()
'''
        result = transpile(code)
        assert 'isLight()' in result
    
    def test_contrast_selection(self):
        """color.contrast(light, dark) should pass through unchanged."""
        code = '''
bg = CSS.rgb(200, 200, 200)
white = CSS.rgb(255, 255, 255)
black = CSS.rgb(0, 0, 0)
text = bg.contrast(white, black)
'''
        result = transpile(code)
        assert 'contrast(' in result
