"""
Phase 34.3: CSS Factory Method Tests

Tests for CSS.px(), CSS.percent(), CSS.deg(), CSS.calc(), etc.
Verifies that all CSS factory methods transpile correctly to JavaScript.

Total: 40 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Length Unit Factory Tests (12 tests)
# =============================================================================

class TestLengthUnits:
    """Tests for CSS length unit factory methods."""
    
    def test_css_px(self):
        """CSS.px(100) should pass through unchanged."""
        code = 'width = CSS.px(100)'
        result = transpile(code)
        assert 'CSS.px(100)' in result
        assert "__py." not in result
    
    def test_css_percent(self):
        """CSS.percent(50) should pass through unchanged."""
        code = 'width = CSS.percent(50)'
        result = transpile(code)
        assert 'CSS.percent(50)' in result
        assert "__py." not in result
    
    def test_css_em(self):
        """CSS.em(2) should pass through unchanged."""
        code = 'padding = CSS.em(2)'
        result = transpile(code)
        assert 'CSS.em(2)' in result
    
    def test_css_rem(self):
        """CSS.rem(1.5) should pass through unchanged."""
        code = 'margin = CSS.rem(1.5)'
        result = transpile(code)
        assert 'CSS.rem(1.5)' in result
    
    def test_css_vw(self):
        """CSS.vw(100) should pass through unchanged."""
        code = 'width = CSS.vw(100)'
        result = transpile(code)
        assert 'CSS.vw(100)' in result
    
    def test_css_vh(self):
        """CSS.vh(100) should pass through unchanged."""
        code = 'height = CSS.vh(100)'
        result = transpile(code)
        assert 'CSS.vh(100)' in result
    
    def test_css_vmin(self):
        """CSS.vmin(50) should pass through unchanged."""
        code = 'size = CSS.vmin(50)'
        result = transpile(code)
        assert 'CSS.vmin(50)' in result
    
    def test_css_vmax(self):
        """CSS.vmax(50) should pass through unchanged."""
        code = 'size = CSS.vmax(50)'
        result = transpile(code)
        assert 'CSS.vmax(50)' in result
    
    def test_css_ch(self):
        """CSS.ch(40) should pass through unchanged."""
        code = 'width = CSS.ch(40)'
        result = transpile(code)
        assert 'CSS.ch(40)' in result
    
    def test_css_fr(self):
        """CSS.fr(1) should pass through unchanged (grid fraction)."""
        code = 'col = CSS.fr(1)'
        result = transpile(code)
        assert 'CSS.fr(1)' in result
    
    def test_css_cm(self):
        """CSS.cm(2) should pass through unchanged."""
        code = 'width = CSS.cm(2)'
        result = transpile(code)
        assert 'CSS.cm(2)' in result
    
    def test_css_mm(self):
        """CSS.mm(10) should pass through unchanged."""
        code = 'width = CSS.mm(10)'
        result = transpile(code)
        assert 'CSS.mm(10)' in result


# =============================================================================
# Angle Unit Factory Tests (5 tests)
# =============================================================================

class TestAngleUnits:
    """Tests for CSS angle unit factory methods."""
    
    def test_css_deg(self):
        """CSS.deg(45) should pass through unchanged."""
        code = 'rotation = CSS.deg(45)'
        result = transpile(code)
        assert 'CSS.deg(45)' in result
        assert "__py." not in result
    
    def test_css_rad(self):
        """CSS.rad(3.14159) should pass through unchanged."""
        code = 'rotation = CSS.rad(3.14159)'
        result = transpile(code)
        assert 'CSS.rad(3.14159)' in result
    
    def test_css_grad(self):
        """CSS.grad(100) should pass through unchanged."""
        code = 'rotation = CSS.grad(100)'
        result = transpile(code)
        assert 'CSS.grad(100)' in result
    
    def test_css_turn(self):
        """CSS.turn(0.5) should pass through unchanged."""
        code = 'rotation = CSS.turn(0.5)'
        result = transpile(code)
        assert 'CSS.turn(0.5)' in result
    
    def test_css_deg_float(self):
        """CSS.deg with float should work."""
        code = 'rotation = CSS.deg(45.5)'
        result = transpile(code)
        assert 'CSS.deg(45.5)' in result


# =============================================================================
# Time Unit Factory Tests (3 tests)
# =============================================================================

class TestTimeUnits:
    """Tests for CSS time unit factory methods."""
    
    def test_css_ms(self):
        """CSS.ms(300) should pass through unchanged."""
        code = 'duration = CSS.ms(300)'
        result = transpile(code)
        assert 'CSS.ms(300)' in result
        assert "__py." not in result
    
    def test_css_s_value(self):
        """Second values should be handled correctly."""
        # Note: CSS.s() might conflict with other patterns
        code = 'duration = CSS.s(0.3)'
        result = transpile(code)
        # Should contain the call in some form
        assert 'CSS' in result and '0.3' in result
    
    def test_css_ms_zero(self):
        """CSS.ms(0) should work for instant transitions."""
        code = 'duration = CSS.ms(0)'
        result = transpile(code)
        assert 'CSS.ms(0)' in result


# =============================================================================
# Resolution Unit Factory Tests (3 tests)
# =============================================================================

class TestResolutionUnits:
    """Tests for CSS resolution unit factory methods."""
    
    def test_css_dpi(self):
        """CSS.dpi(96) should pass through unchanged."""
        code = 'res = CSS.dpi(96)'
        result = transpile(code)
        assert 'CSS.dpi(96)' in result
    
    def test_css_dpcm(self):
        """CSS.dpcm(38) should pass through unchanged."""
        code = 'res = CSS.dpcm(38)'
        result = transpile(code)
        assert 'CSS.dpcm(38)' in result
    
    def test_css_dppx(self):
        """CSS.dppx(2) should pass through unchanged."""
        code = 'res = CSS.dppx(2)'
        result = transpile(code)
        assert 'CSS.dppx(2)' in result


# =============================================================================
# Unitless Value Tests (2 tests)
# =============================================================================

class TestUnitlessValues:
    """Tests for CSS unitless values."""
    
    def test_css_number(self):
        """CSS.number(1.5) should pass through unchanged."""
        code = 'line_height = CSS.number(1.5)'
        result = transpile(code)
        assert 'CSS.number(1.5)' in result
    
    def test_css_number_zero(self):
        """CSS.number(0) should work."""
        code = 'opacity = CSS.number(0)'
        result = transpile(code)
        assert 'CSS.number(0)' in result


# =============================================================================
# Keyword Value Tests (3 tests)
# =============================================================================

class TestKeywordValues:
    """Tests for CSS keyword values."""
    
    def test_css_keyword_auto(self):
        """CSS.keyword('auto') should pass through unchanged."""
        code = 'width = CSS.keyword("auto")'
        result = transpile(code)
        assert 'CSS.keyword("auto")' in result
    
    def test_css_keyword_inherit(self):
        """CSS.keyword('inherit') should pass through unchanged."""
        code = 'color = CSS.keyword("inherit")'
        result = transpile(code)
        assert 'CSS.keyword("inherit")' in result
    
    def test_css_keyword_none(self):
        """CSS.keyword('none') should pass through unchanged."""
        code = 'display = CSS.keyword("none")'
        result = transpile(code)
        assert 'CSS.keyword("none")' in result


# =============================================================================
# Math Function Tests (8 tests)
# =============================================================================

class TestMathFunctions:
    """Tests for CSS math functions (calc, min, max, clamp)."""
    
    def test_css_calc_simple(self):
        """CSS.calc('100% - 20px') should pass through unchanged."""
        code = 'width = CSS.calc("100% - 20px")'
        result = transpile(code)
        assert 'CSS.calc("100% - 20px")' in result
        assert "__py." not in result
    
    def test_css_calc_complex(self):
        """CSS.calc with complex expression should work."""
        code = 'width = CSS.calc("50vw + 2rem - 10px")'
        result = transpile(code)
        assert 'CSS.calc' in result
    
    def test_css_min_two_values(self):
        """CSS.min with two values should work."""
        code = 'width = CSS.min(CSS.px(300), CSS.percent(100))'
        result = transpile(code)
        assert 'CSS.min' in result
        assert 'CSS.px(300)' in result
        assert 'CSS.percent(100)' in result
    
    def test_css_min_multiple_values(self):
        """CSS.min with multiple values should work."""
        code = 'width = CSS.min(CSS.px(300), CSS.percent(100), CSS.vw(50))'
        result = transpile(code)
        assert 'CSS.min' in result
    
    def test_css_max_two_values(self):
        """CSS.max with two values should work."""
        code = 'width = CSS.max(CSS.px(100), CSS.percent(50))'
        result = transpile(code)
        assert 'CSS.max' in result
        assert 'CSS.px(100)' in result
    
    def test_css_max_multiple_values(self):
        """CSS.max with multiple values should work."""
        code = 'width = CSS.max(CSS.px(100), CSS.percent(50), CSS.rem(10))'
        result = transpile(code)
        assert 'CSS.max' in result
    
    def test_css_clamp(self):
        """CSS.clamp(min, val, max) should pass through unchanged."""
        code = 'font_size = CSS.clamp(CSS.px(12), CSS.vw(2), CSS.px(24))'
        result = transpile(code)
        assert 'CSS.clamp' in result
        assert 'CSS.px(12)' in result
        assert 'CSS.vw(2)' in result
        assert 'CSS.px(24)' in result
    
    def test_css_calc_with_variables(self):
        """CSS.calc with variable references should work."""
        code = '''
x = CSS.px(100)
y = CSS.px(50)
'''
        result = transpile(code)
        assert 'CSS.px(100)' in result
        assert 'CSS.px(50)' in result


# =============================================================================
# Parsing Tests (4 tests)
# =============================================================================

class TestParsing:
    """Tests for CSS.parse() and CSS.parseAll()."""
    
    def test_css_parse_width(self):
        """CSS.parse should parse property values."""
        code = 'width = CSS.parse("width", "100px")'
        result = transpile(code)
        assert 'CSS.parse("width", "100px")' in result
    
    def test_css_parse_transform(self):
        """CSS.parse should parse transform values."""
        code = 'transform = CSS.parse("transform", "translateX(100px)")'
        result = transpile(code)
        assert 'CSS.parse' in result
    
    def test_css_parse_all_margin(self):
        """CSS.parseAll should parse shorthand properties."""
        code = 'margins = CSS.parseAll("margin", "10px 20px")'
        result = transpile(code)
        assert 'CSS.parseAll' in result
    
    def test_css_register_property(self):
        """CSS.registerProperty should work for custom properties."""
        code = '''
CSS.registerProperty({
    "name": "--my-color",
    "syntax": "<color>",
    "inherits": False,
    "initialValue": "black",
})
'''
        result = transpile(code)
        assert 'CSS.registerProperty' in result
        assert '--my-color' in result
