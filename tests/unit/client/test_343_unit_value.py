"""
Phase 34.3: CSSUnitValue Tests

Tests for CSSUnitValue properties, arithmetic, and conversion methods.
Verifies that all CSSUnitValue operations transpile correctly to JavaScript.

Total: 35 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Property Access Tests (7 tests)
# =============================================================================

class TestProperties:
    """Tests for CSSUnitValue property access."""
    
    def test_value_property_read(self):
        """width.value should pass through unchanged."""
        code = '''
width = CSS.px(100)
v = width.value
'''
        result = transpile(code)
        assert 'width.value' in result
        assert "__py." not in result
    
    def test_unit_property_read(self):
        """width.unit should pass through unchanged."""
        code = '''
width = CSS.px(100)
u = width.unit
'''
        result = transpile(code)
        assert 'width.unit' in result
    
    def test_value_property_set(self):
        """width.value = 200 should pass through unchanged."""
        code = '''
width = CSS.px(100)
width.value = 200
'''
        result = transpile(code)
        assert 'width.value = 200' in result
    
    def test_unit_property_set(self):
        """width.unit = 'em' should pass through unchanged."""
        code = '''
width = CSS.px(100)
width.unit = "em"
'''
        result = transpile(code)
        assert 'width.unit = "em"' in result
    
    def test_value_in_expression(self):
        """Using .value in expressions should work."""
        code = '''
width = CSS.px(100)
doubled = width.value * 2
'''
        result = transpile(code)
        # Multiplication can use native * or __py.dunders.mul
        assert 'width.value' in result
        assert '2' in result
    
    def test_unit_in_conditional(self):
        """Using .unit in conditionals should work."""
        code = '''
width = CSS.px(100)
if width.unit == "px":
    pass
'''
        result = transpile(code)
        assert 'width.unit' in result
    
    def test_chained_value_access(self):
        """CSS.px(100).value should work directly."""
        code = 'v = CSS.px(100).value'
        result = transpile(code)
        assert 'CSS.px(100).value' in result


# =============================================================================
# String Conversion Tests (4 tests)
# =============================================================================

class TestStringConversion:
    """Tests for CSSUnitValue string conversion."""
    
    def test_to_string_method(self):
        """width.toString() should pass through."""
        code = '''
width = CSS.px(100)
s = width.toString()
'''
        result = transpile(code)
        assert 'toString()' in result
    
    def test_str_conversion_implicit(self):
        """Using value in string context."""
        code = '''
width = CSS.px(100)
s = f"Width: {width}"
'''
        result = transpile(code)
        # Should contain template literal or string concat
        assert 'width' in result.lower()
    
    def test_to_string_chained(self):
        """CSS.px(100).toString() chained should work."""
        code = 's = CSS.px(100).toString()'
        result = transpile(code)
        assert 'CSS.px(100).toString()' in result
    
    def test_to_string_assigned(self):
        """Assigning toString result should work."""
        code = '''
width = CSS.px(100)
css_string = width.toString()
'''
        result = transpile(code)
        assert 'toString()' in result


# =============================================================================
# Arithmetic Tests (12 tests)
# =============================================================================

class TestArithmetic:
    """Tests for CSSNumericValue arithmetic methods."""
    
    def test_add_single(self):
        """width.add(CSS.px(50)) should pass through."""
        code = '''
width = CSS.px(100)
total = width.add(CSS.px(50))
'''
        result = transpile(code)
        assert 'width.add(CSS.px(50))' in result
        assert "__py." not in result
    
    def test_add_multiple(self):
        """width.add(a, b, c) should pass through."""
        code = '''
base = CSS.px(100)
total = base.add(CSS.px(10), CSS.px(20), CSS.px(30))
'''
        result = transpile(code)
        assert 'add(' in result
    
    def test_sub_single(self):
        """width.sub(CSS.px(30)) should pass through."""
        code = '''
width = CSS.px(100)
smaller = width.sub(CSS.px(30))
'''
        result = transpile(code)
        assert 'width.sub(CSS.px(30))' in result
    
    def test_sub_multiple(self):
        """width.sub(a, b) should pass through."""
        code = '''
base = CSS.px(100)
result = base.sub(CSS.px(10), CSS.px(20))
'''
        result = transpile(code)
        assert 'sub(' in result
    
    def test_mul_scalar(self):
        """width.mul(2) should pass through."""
        code = '''
width = CSS.px(100)
doubled = width.mul(2)
'''
        result = transpile(code)
        assert 'width.mul(2)' in result
    
    def test_mul_float(self):
        """width.mul(0.5) should pass through."""
        code = '''
width = CSS.px(100)
half = width.mul(0.5)
'''
        result = transpile(code)
        assert 'width.mul(0.5)' in result
    
    def test_div_scalar(self):
        """width.div(2) should pass through."""
        code = '''
width = CSS.px(100)
half = width.div(2)
'''
        result = transpile(code)
        assert 'width.div(2)' in result
    
    def test_div_float(self):
        """width.div(0.5) should work (doubles the value)."""
        code = '''
width = CSS.px(100)
doubled = width.div(0.5)
'''
        result = transpile(code)
        assert 'width.div(0.5)' in result
    
    def test_negate(self):
        """width.negate() should pass through."""
        code = '''
width = CSS.px(100)
neg = width.negate()
'''
        result = transpile(code)
        assert 'negate()' in result
    
    def test_invert(self):
        """width.invert() should pass through."""
        code = '''
width = CSS.px(100)
inv = width.invert()
'''
        result = transpile(code)
        assert 'invert()' in result
    
    def test_chained_arithmetic(self):
        """Chained arithmetic should work."""
        code = '''
width = CSS.px(100)
result = width.mul(2).sub(CSS.px(50))
'''
        result = transpile(code)
        assert 'mul(2)' in result
        assert 'sub(' in result
    
    def test_arithmetic_with_different_units(self):
        """Adding different units should work (browser handles conversion)."""
        code = '''
total = CSS.px(100).add(CSS.percent(50))
'''
        result = transpile(code)
        assert 'CSS.px(100).add(CSS.percent(50))' in result


# =============================================================================
# Comparison Tests (4 tests)
# =============================================================================

class TestComparison:
    """Tests for CSSNumericValue comparison methods."""
    
    def test_equals_same_value(self):
        """a.equals(b) should pass through."""
        code = '''
a = CSS.px(100)
b = CSS.px(100)
same = a.equals(b)
'''
        result = transpile(code)
        assert 'equals(' in result
    
    def test_equals_different_value(self):
        """a.equals(b) with different values."""
        code = '''
a = CSS.px(100)
b = CSS.px(200)
same = a.equals(b)
'''
        result = transpile(code)
        assert 'equals(' in result
    
    def test_equals_multiple(self):
        """a.equals(b, c) with multiple values."""
        code = '''
a = CSS.px(100)
b = CSS.px(100)
c = CSS.px(100)
all_same = a.equals(b, c)
'''
        result = transpile(code)
        assert 'equals(' in result
    
    def test_equals_chained(self):
        """CSS.px(100).equals(CSS.px(100)) chained."""
        code = 'result = CSS.px(100).equals(CSS.px(100))'
        result = transpile(code)
        assert 'CSS.px(100).equals(CSS.px(100))' in result


# =============================================================================
# Unit Conversion Tests (5 tests)
# =============================================================================

class TestUnitConversion:
    """Tests for CSSNumericValue unit conversion."""
    
    def test_to_same_unit(self):
        """width.to('px') with same unit should work."""
        code = '''
width = CSS.px(100)
px_val = width.to("px")
'''
        result = transpile(code)
        assert 'to("px")' in result
    
    def test_to_different_unit_angle(self):
        """Converting degrees to radians should work."""
        code = '''
deg = CSS.deg(180)
rad = deg.to("rad")
'''
        result = transpile(code)
        assert 'to("rad")' in result
    
    def test_to_different_unit_time(self):
        """Converting ms to s should work."""
        code = '''
ms = CSS.ms(1000)
sec = ms.to("s")
'''
        result = transpile(code)
        assert 'to("s")' in result or 'to(\\"s\\")' in result
    
    def test_to_sum(self):
        """width.toSum('px', '%') should work."""
        code = '''
width = CSS.calc("50% + 100px")
sum_val = width.toSum("px", "percent")
'''
        result = transpile(code)
        assert 'toSum(' in result
    
    def test_type_method(self):
        """width.type() should return type info."""
        code = '''
width = CSS.px(100)
type_info = width.type()
'''
        result = transpile(code)
        assert 'type()' in result


# =============================================================================
# Constructor Tests (3 tests)
# =============================================================================

class TestConstructor:
    """Tests for CSSUnitValue constructor."""
    
    def test_direct_constructor(self):
        """CSSUnitValue(100, 'px') should work."""
        code = 'width = CSSUnitValue(100, "px")'
        result = transpile(code)
        assert 'CSSUnitValue' in result
        assert '100' in result
        assert 'px' in result
    
    def test_constructor_with_float(self):
        """CSSUnitValue(1.5, 'rem') should work."""
        code = 'margin = CSSUnitValue(1.5, "rem")'
        result = transpile(code)
        assert 'CSSUnitValue' in result
        assert '1.5' in result
    
    def test_constructor_assigned(self):
        """Assigning constructor result should work."""
        code = '''
unit_val = CSSUnitValue(50, "percent")
el.attributeStyleMap.set("width", unit_val)
'''
        result = transpile(code)
        assert 'CSSUnitValue' in result
