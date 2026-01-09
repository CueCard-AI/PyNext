"""
Phase 34.3: CSS Typed OM Edge Case Tests

Tests for edge cases in CSS Typed OM:
- Negative values
- Zero values
- Very large numbers
- Float precision
- Arithmetic edge cases

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Negative Value Tests (5 tests)
# =============================================================================

class TestNegativeValues:
    """Tests for negative CSS values."""
    
    def test_negative_px(self):
        """CSS.px(-100) should handle negative values."""
        code = 'margin = CSS.px(-100)'
        result = transpile(code)
        assert 'CSS.px(-100)' in result or 'CSS.px((-100))' in result
        assert 'margin' in result
    
    def test_negative_deg(self):
        """CSS.deg(-45) should handle negative angles."""
        code = 'rotation = CSS.deg(-45)'
        result = transpile(code)
        assert 'CSS.deg' in result
        assert '45' in result
    
    def test_negative_percent(self):
        """CSS.percent(-50) should handle negative percentages."""
        code = 'offset = CSS.percent(-50)'
        result = transpile(code)
        assert 'CSS.percent' in result
        assert '50' in result
    
    def test_negative_rem(self):
        """CSS.rem(-2) should handle negative rem."""
        code = 'margin = CSS.rem(-2)'
        result = transpile(code)
        assert 'CSS.rem' in result
        assert '2' in result
    
    def test_negative_in_arithmetic(self):
        """Arithmetic with negative values should work."""
        code = '''
positive = CSS.px(100)
negative = positive.mul(-1)
'''
        result = transpile(code)
        assert 'mul(-1)' in result or 'mul((-1))' in result


# =============================================================================
# Zero Value Tests (4 tests)
# =============================================================================

class TestZeroValues:
    """Tests for zero CSS values."""
    
    def test_zero_px(self):
        """CSS.px(0) should handle zero values."""
        code = 'margin = CSS.px(0)'
        result = transpile(code)
        assert 'CSS.px(0)' in result
    
    def test_zero_percent(self):
        """CSS.percent(0) should handle zero percentages."""
        code = 'width = CSS.percent(0)'
        result = transpile(code)
        assert 'CSS.percent(0)' in result
    
    def test_zero_deg(self):
        """CSS.deg(0) should handle zero angles."""
        code = 'rotation = CSS.deg(0)'
        result = transpile(code)
        assert 'CSS.deg(0)' in result
    
    def test_zero_in_clamp(self):
        """CSS.clamp with zero should work."""
        code = 'size = CSS.clamp(CSS.px(0), CSS.percent(50), CSS.px(100))'
        result = transpile(code)
        assert 'CSS.clamp' in result
        assert 'CSS.px(0)' in result


# =============================================================================
# Large Number Tests (3 tests)
# =============================================================================

class TestLargeNumbers:
    """Tests for very large CSS values."""
    
    def test_large_px(self):
        """CSS.px(1000000) should handle large values."""
        code = 'width = CSS.px(1000000)'
        result = transpile(code)
        assert 'CSS.px(1000000)' in result
    
    def test_large_vw(self):
        """CSS.vw(9999) should handle large viewport values."""
        code = 'width = CSS.vw(9999)'
        result = transpile(code)
        assert 'CSS.vw(9999)' in result
    
    def test_large_number_arithmetic(self):
        """Arithmetic with large numbers should work."""
        code = '''
big = CSS.px(1000000)
doubled = big.mul(2)
'''
        result = transpile(code)
        assert 'CSS.px(1000000)' in result
        assert 'mul(2)' in result


# =============================================================================
# Float Precision Tests (4 tests)
# =============================================================================

class TestFloatPrecision:
    """Tests for float precision in CSS values."""
    
    def test_small_float(self):
        """CSS.px(0.001) should handle small floats."""
        code = 'size = CSS.px(0.001)'
        result = transpile(code)
        assert 'CSS.px(0.001)' in result
    
    def test_repeating_decimal(self):
        """CSS.rem(0.333) should handle repeating decimals."""
        code = 'margin = CSS.rem(0.333)'
        result = transpile(code)
        assert 'CSS.rem(0.333)' in result
    
    def test_many_decimals(self):
        """CSS.em(1.23456789) should handle many decimal places."""
        code = 'size = CSS.em(1.23456789)'
        result = transpile(code)
        assert 'CSS.em(1.23456789)' in result
    
    def test_float_division_result(self):
        """Division resulting in float should work."""
        code = '''
value = CSS.px(100)
third = value.div(3)
'''
        result = transpile(code)
        assert 'div(3)' in result


# =============================================================================
# Arithmetic Edge Cases (4 tests)
# =============================================================================

class TestArithmeticEdgeCases:
    """Tests for arithmetic edge cases."""
    
    def test_multiply_by_zero(self):
        """Multiplying by zero should work."""
        code = '''
value = CSS.px(100)
zero = value.mul(0)
'''
        result = transpile(code)
        assert 'mul(0)' in result
    
    def test_divide_by_small_number(self):
        """Dividing by small number should work."""
        code = '''
value = CSS.px(100)
large = value.div(0.001)
'''
        result = transpile(code)
        assert 'div(0.001)' in result
    
    def test_chained_operations(self):
        """Long chains of operations should work."""
        code = '''
value = CSS.px(100)
result = value.mul(2).div(2).add(CSS.px(50)).sub(CSS.px(25))
'''
        result = transpile(code)
        assert 'mul(2)' in result
        assert 'div(2)' in result
        assert 'add(' in result
        assert 'sub(' in result
    
    def test_identity_operations(self):
        """Identity operations (mul 1, div 1, add 0) should work."""
        code = '''
value = CSS.px(100)
same = value.mul(1).div(1).add(CSS.px(0))
'''
        result = transpile(code)
        assert 'mul(1)' in result
        assert 'div(1)' in result
        assert 'add(CSS.px(0))' in result

