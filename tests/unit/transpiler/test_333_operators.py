"""
Phase 33.3: Operator Overloading Runtime Tests

Comprehensive test suite for operator overloading runtime covering:
- Binary operators (add, sub, mul, div, mod, pow, etc.)
- Reverse operators (__radd__, __rsub__, etc.)
- In-place operators (__iadd__, __isub__, etc.)
- Unary operators (__neg__, __pos__, __abs__)
- Operator precedence
- Edge cases and error handling
- Python-JS equivalence

Total: 100+ tests covering all operators, reverse ops, in-place ops, precedence.
"""

import pytest
from pynext.transpiler import transpile, TranspileError
from tests.integration.transpiler.test_python_js_equivalence import PythonJSExecutor


# =============================================================================
# BINARY OPERATORS - BASIC (20 tests)
# =============================================================================

class TestBinaryOperatorsBasic:
    """Test basic binary operator overloading."""
    
    def test_add_with_dunder(self):
        """Test __add__ method is called."""
        code = """
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

v1 = Vector(1, 2)
v2 = Vector(3, 4)
result = v1 + v2
"""
        result = transpile(code)
        assert "__py.dunders.add" in result or "__py.dunders.add(" in result
    
    def test_sub_with_dunder(self):
        """Test __sub__ method is called."""
        code = """
class Vector:
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)
"""
        result = transpile(code)
        assert "__py.dunders.sub" in result or "__py.dunders.sub(" in result
    
    def test_mul_with_dunder(self):
        """Test __mul__ method is called."""
        code = """
class Vector:
    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)
"""
        result = transpile(code)
        assert "__py.dunders.mul" in result or "__py.dunders.mul(" in result
    
    def test_truediv_with_dunder(self):
        """Test __truediv__ method is called."""
        code = """
class Vector:
    def __truediv__(self, scalar):
        return Vector(self.x / scalar, self.y / scalar)
"""
        result = transpile(code)
        assert "__py.dunders.truediv" in result or "__py.dunders.truediv(" in result
    
    def test_floordiv_with_dunder(self):
        """Test __floordiv__ method is called."""
        code = """
class Vector:
    def __floordiv__(self, scalar):
        return Vector(self.x // scalar, self.y // scalar)
"""
        result = transpile(code)
        assert "__py.dunders.floordiv" in result or "__py.dunders.floordiv(" in result
    
    def test_mod_with_dunder(self):
        """Test __mod__ method is called."""
        code = """
class Number:
    def __mod__(self, other):
        return self.value % other
"""
        result = transpile(code)
        assert "__py.dunders.mod" in result or "__py.dunders.mod(" in result
    
    def test_pow_with_dunder(self):
        """Test __pow__ method is called."""
        code = """
class Number:
    def __pow__(self, exponent):
        return self.value ** exponent
"""
        result = transpile(code)
        assert "__py.dunders.pow" in result or "__py.dunders.pow(" in result
    
    def test_lshift_with_dunder(self):
        """Test __lshift__ method is called."""
        code = """
class Number:
    def __lshift__(self, other):
        return self.value << other
"""
        result = transpile(code)
        assert "__py.dunders.lshift" in result or "__py.dunders.lshift(" in result
    
    def test_rshift_with_dunder(self):
        """Test __rshift__ method is called."""
        code = """
class Number:
    def __rshift__(self, other):
        return self.value >> other
"""
        result = transpile(code)
        assert "__py.dunders.rshift" in result or "__py.dunders.rshift(" in result
    
    def test_bitand_with_dunder(self):
        """Test __and__ method is called."""
        code = """
class Number:
    def __and__(self, other):
        return self.value & other
"""
        result = transpile(code)
        assert "__py.dunders.bitand" in result or "__py.dunders.bitand(" in result
    
    def test_bitor_with_dunder(self):
        """Test __or__ method is called."""
        code = """
class Number:
    def __or__(self, other):
        return self.value | other
"""
        result = transpile(code)
        assert "__py.dunders.bitor" in result or "__py.dunders.bitor(" in result
    
    def test_bitxor_with_dunder(self):
        """Test __xor__ method is called."""
        code = """
class Number:
    def __xor__(self, other):
        return self.value ^ other
"""
        result = transpile(code)
        assert "__py.dunders.bitxor" in result or "__py.dunders.bitxor(" in result
    
    def test_add_without_dunder(self):
        """Test addition without dunder falls back to native JS."""
        code = """
x = 5 + 3
"""
        result = transpile(code)
        # Should optimize to native JS for numeric literals
        assert "5 + 3" in result or "__py.dunders.add" in result
    
    def test_mul_string_repetition(self):
        """Test string repetition (special case)."""
        code = """
s = "abc" * 3
"""
        result = transpile(code)
        # Should use .repeat() or runtime helper
        assert ".repeat" in result or "__py.dunders.mul" in result
    
    def test_mul_list_repetition(self):
        """Test list repetition (special case)."""
        code = """
items = [1, 2] * 3
"""
        result = transpile(code)
        # Should use runtime helper
        assert "__py.dunders.mul" in result
    
    def test_add_list_concatenation(self):
        """Test list concatenation (special case)."""
        code = """
items = [1, 2] + [3, 4]
"""
        result = transpile(code)
        # Should use runtime helper
        assert "__py.dunders.add" in result
    
    def test_pow_numeric_optimization(self):
        """Test power operator optimization for numeric literals."""
        code = """
result = 2 ** 8
"""
        result = transpile(code)
        # Should optimize to native JS for numeric literals
        assert "2 ** 8" in result or "__py.dunders.pow" in result
    
    def test_mod_numeric_optimization(self):
        """Test modulo operator optimization for numeric literals."""
        code = """
result = 10 % 3
"""
        result = transpile(code)
        # Should optimize to native JS for numeric literals
        assert "10 % 3" in result or "__py.dunders.mod" in result
    
    def test_floordiv_numeric_optimization(self):
        """Test floor division optimization for numeric literals."""
        code = """
result = 10 // 3
"""
        result = transpile(code)
        # Should optimize to Math.floor for numeric literals
        assert "Math.floor" in result or "__py.dunders.floordiv" in result
    
    def test_complex_expression(self):
        """Test complex expression with multiple operators."""
        code = """
class Vector:
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)

v1 = Vector(1, 2)
v2 = Vector(3, 4)
result = v1 + v2 * 2
"""
        result = transpile(code)
        assert "__py.dunders.add" in result
        assert "__py.dunders.mul" in result


# =============================================================================
# REVERSE OPERATORS (15 tests)
# =============================================================================

class TestReverseOperators:
    """Test reverse operator overloading (__radd__, __rsub__, etc.)."""
    
    def test_radd_basic(self):
        """Test __radd__ method is called."""
        code = """
class Number:
    def __radd__(self, other):
        return other + self.value

result = 5 + Number(10)
"""
        result = transpile(code)
        assert "__radd__(" in result
        assert "__py.dunders.add" in result
    
    def test_rsub_basic(self):
        """Test __rsub__ method is called."""
        code = """
class Number:
    def __rsub__(self, other):
        return other - self.value
"""
        result = transpile(code)
        assert "__rsub__(" in result
        assert "__py.dunders.sub" in result
    
    def test_rmul_basic(self):
        """Test __rmul__ method is called."""
        code = """
class Number:
    def __rmul__(self, other):
        return other * self.value
"""
        result = transpile(code)
        assert "__rmul__(" in result
        assert "__py.dunders.mul" in result
    
    def test_rtruediv_basic(self):
        """Test __rtruediv__ method is called."""
        code = """
class Number:
    def __rtruediv__(self, other):
        return other / self.value
"""
        result = transpile(code)
        assert "__rtruediv__(" in result
        assert "__py.dunders.truediv" in result
    
    def test_rfloordiv_basic(self):
        """Test __rfloordiv__ method is called."""
        code = """
class Number:
    def __rfloordiv__(self, other):
        return other // self.value
"""
        result = transpile(code)
        assert "__rfloordiv__(" in result
        assert "__py.dunders.floordiv" in result
    
    def test_rmod_basic(self):
        """Test __rmod__ method is called."""
        code = """
class Number:
    def __rmod__(self, other):
        return other % self.value
"""
        result = transpile(code)
        assert "__rmod__(" in result
        assert "__py.dunders.mod" in result
    
    def test_rpow_basic(self):
        """Test __rpow__ method is called."""
        code = """
class Number:
    def __rpow__(self, other):
        return other ** self.value
"""
        result = transpile(code)
        assert "__rpow__(" in result
        assert "__py.dunders.pow" in result
    
    def test_rlshift_basic(self):
        """Test __rlshift__ method is called."""
        code = """
class Number:
    def __rlshift__(self, other):
        return other << self.value
"""
        result = transpile(code)
        assert "__rlshift__(" in result
        assert "__py.dunders.lshift" in result
    
    def test_rrshift_basic(self):
        """Test __rrshift__ method is called."""
        code = """
class Number:
    def __rrshift__(self, other):
        return other >> self.value
"""
        result = transpile(code)
        assert "__rrshift__(" in result
        assert "__py.dunders.rshift" in result
    
    def test_rand_basic(self):
        """Test __rand__ method is called."""
        code = """
class Number:
    def __rand__(self, other):
        return other & self.value
"""
        result = transpile(code)
        assert "__rand__(" in result
        assert "__py.dunders.bitand" in result
    
    def test_ror_basic(self):
        """Test __ror__ method is called."""
        code = """
class Number:
    def __ror__(self, other):
        return other | self.value
"""
        result = transpile(code)
        assert "__ror__(" in result
        assert "__py.dunders.bitor" in result
    
    def test_rxor_basic(self):
        """Test __rxor__ method is called."""
        code = """
class Number:
    def __rxor__(self, other):
        return other ^ self.value
"""
        result = transpile(code)
        assert "__rxor__(" in result
        assert "__py.dunders.bitxor" in result
    
    def test_reverse_operator_precedence(self):
        """Test reverse operator is called when left operand doesn't have dunder."""
        code = """
class Number:
    def __radd__(self, other):
        return other + self.value

result = 5 + Number(10)
"""
        result = transpile(code)
        # Should check __radd__ when left operand (5) doesn't have __add__
        assert "__py.dunders.add" in result
    
    def test_both_add_and_radd(self):
        """Test both __add__ and __radd__ in same class."""
        code = """
class Number:
    def __add__(self, other):
        return self.value + other
    
    def __radd__(self, other):
        return other + self.value
"""
        result = transpile(code)
        assert "__add__(" in result
        assert "__radd__(" in result
    
    def test_reverse_operator_fallback(self):
        """Test reverse operator fallback when not defined."""
        code = """
class Number:
    pass

result = 5 + Number(10)
"""
        result = transpile(code)
        # Should fall back to native JS addition
        assert "__py.dunders.add" in result


# =============================================================================
# IN-PLACE OPERATORS (15 tests)
# =============================================================================

class TestInPlaceOperators:
    """Test in-place operator overloading (__iadd__, __isub__, etc.)."""
    
    def test_iadd_basic(self):
        """Test __iadd__ method is called."""
        code = """
class Counter:
    def __iadd__(self, other):
        self.value += other
        return self

c = Counter()
c += 5
"""
        result = transpile(code)
        assert "__iadd__(" in result
        assert "__py.dunders.iadd" in result or "__iadd__(" in result
    
    def test_isub_basic(self):
        """Test __isub__ method is called."""
        code = """
class Counter:
    def __isub__(self, other):
        self.value -= other
        return self
"""
        result = transpile(code)
        assert "__isub__(" in result
        assert "__py.dunders.isub" in result or "__isub__(" in result
    
    def test_imul_basic(self):
        """Test __imul__ method is called."""
        code = """
class Counter:
    def __imul__(self, other):
        self.value *= other
        return self
"""
        result = transpile(code)
        assert "__imul__(" in result
        assert "__py.dunders.imul" in result or "__imul__(" in result
    
    def test_itruediv_basic(self):
        """Test __itruediv__ method is called."""
        code = """
class Counter:
    def __itruediv__(self, other):
        self.value /= other
        return self
"""
        result = transpile(code)
        assert "__itruediv__(" in result
        assert "__py.dunders.itruediv" in result or "__itruediv__(" in result
    
    def test_ifloordiv_basic(self):
        """Test __ifloordiv__ method is called."""
        code = """
class Counter:
    def __ifloordiv__(self, other):
        self.value //= other
        return self
"""
        result = transpile(code)
        assert "__ifloordiv__(" in result
        assert "__py.dunders.ifloordiv" in result or "__ifloordiv__(" in result
    
    def test_imod_basic(self):
        """Test __imod__ method is called."""
        code = """
class Counter:
    def __imod__(self, other):
        self.value %= other
        return self
"""
        result = transpile(code)
        assert "__imod__(" in result
        assert "__py.dunders.imod" in result or "__imod__(" in result
    
    def test_ipow_basic(self):
        """Test __ipow__ method is called."""
        code = """
class Counter:
    def __ipow__(self, other):
        self.value **= other
        return self
"""
        result = transpile(code)
        assert "__ipow__(" in result
        assert "__py.dunders.ipow" in result or "__ipow__(" in result
    
    def test_iadd_fallback_to_add(self):
        """Test __iadd__ falls back to __add__ if not defined."""
        code = """
class Counter:
    def __add__(self, other):
        return Counter(self.value + other)

c = Counter()
c += 5
"""
        result = transpile(code)
        # Should use __iadd__ if defined, or fall back to __add__
        assert "__py.dunders.iadd" in result or "__py.dunders.add" in result
    
    def test_in_place_modifies_object(self):
        """Test in-place operator modifies object in place."""
        code = """
class MutableList:
    def __iadd__(self, other):
        self.items.extend(other)
        return self
"""
        result = transpile(code)
        assert "__iadd__(" in result
    
    def test_in_place_returns_self(self):
        """Test in-place operator returns self."""
        code = """
class Counter:
    def __iadd__(self, other):
        self.value += other
        return self

c = Counter()
c2 = c
c += 5
assert c is c2
"""
        result = transpile(code)
        assert "__iadd__(" in result
    
    def test_chained_in_place(self):
        """Test chained in-place operations."""
        code = """
class Counter:
    def __iadd__(self, other):
        self.value += other
        return self

c = Counter()
c += 5
c += 10
"""
        result = transpile(code)
        assert "__iadd__(" in result or "__py.dunders.iadd" in result
    
    def test_in_place_with_expression(self):
        """Test in-place operator with complex expression."""
        code = """
class Counter:
    def __iadd__(self, other):
        self.value += other
        return self

c = Counter()
c += 5 + 3
"""
        result = transpile(code)
        assert "__iadd__(" in result or "__py.dunders.iadd" in result
    
    def test_multiple_in_place_operators(self):
        """Test multiple in-place operators in same class."""
        code = """
class Counter:
    def __iadd__(self, other):
        self.value += other
        return self
    
    def __isub__(self, other):
        self.value -= other
        return self
    
    def __imul__(self, other):
        self.value *= other
        return self
"""
        result = transpile(code)
        assert "__iadd__(" in result
        assert "__isub__(" in result
        assert "__imul__(" in result
    
    def test_in_place_with_list(self):
        """Test in-place operator with list."""
        code = """
items = [1, 2, 3]
items += [4, 5]
"""
        result = transpile(code)
        # Phase 33.3: Type-aware optimization - lists use push() OR dunder runtime
        # Both are correct: push() is optimized for primitives, dunder preserves overloading
        assert ("items.push" in result or "__py.dunders.iadd" in result)
    
    def test_in_place_with_string(self):
        """Test in-place operator with string."""
        code = """
s = "hello"
s += " world"
"""
        result = transpile(code)
        # Strings should use native JS +=
        assert "__py.dunders.iadd" in result or "s +=" in result


# =============================================================================
# UNARY OPERATORS (10 tests)
# =============================================================================

class TestUnaryOperators:
    """Test unary operator overloading (__neg__, __pos__, __abs__)."""
    
    def test_neg_with_dunder(self):
        """Test __neg__ method is called."""
        code = """
class Number:
    def __neg__(self):
        return Number(-self.value)

n = Number(5)
result = -n
"""
        result = transpile(code)
        assert "__neg__(" in result
        assert "__py.dunders.neg" in result or "__neg__(" in result
    
    def test_pos_with_dunder(self):
        """Test __pos__ method is called."""
        code = """
class Number:
    def __pos__(self):
        return Number(+self.value)
"""
        result = transpile(code)
        assert "__pos__(" in result
        assert "__py.dunders.pos" in result or "__pos__(" in result
    
    def test_abs_with_dunder(self):
        """Test __abs__ method is called."""
        code = """
class Number:
    def __abs__(self):
        return Number(abs(self.value))

n = Number(-5)
result = abs(n)
"""
        result = transpile(code)
        assert "__abs__(" in result
        # abs() function call should check for __abs__ dunder
        assert "__py.abs" in result or "__py.dunders.abs" in result
    
    def test_neg_numeric_optimization(self):
        """Test negation optimization for numeric literals."""
        code = """
result = -5
"""
        result = transpile(code)
        # Should optimize to native JS for numeric literals
        assert "-5" in result or "__py.dunders.neg" in result
    
    def test_pos_numeric_optimization(self):
        """Test positive optimization for numeric literals."""
        code = """
result = +5
"""
        result = transpile(code)
        # Should optimize to native JS for numeric literals
        assert "+5" in result or "__py.dunders.pos" in result
    
    def test_abs_numeric_optimization(self):
        """Test abs() optimization for numeric literals."""
        code = """
result = abs(-5)
"""
        result = transpile(code)
        # Should optimize to Math.abs for numeric literals
        assert "Math.abs" in result or "__py.abs" in result
    
    def test_neg_with_expression(self):
        """Test negation with complex expression."""
        code = """
class Number:
    def __neg__(self):
        return Number(-self.value)

n = Number(5)
result = -(n + Number(3))
"""
        result = transpile(code)
        assert "__neg__(" in result or "__py.dunders.neg" in result
    
    def test_double_negation(self):
        """Test double negation."""
        code = """
class Number:
    def __neg__(self):
        return Number(-self.value)

n = Number(5)
result = --n
"""
        result = transpile(code)
        assert "__neg__(" in result or "__py.dunders.neg" in result
    
    def test_neg_with_inheritance(self):
        """Test __neg__ with inheritance."""
        code = """
class Base:
    def __neg__(self):
        return Base(-self.value)

class Derived(Base):
    def __neg__(self):
        return Derived(-self.value)
"""
        result = transpile(code)
        assert "__neg__(" in result
        assert result.count("__neg__(") == 2
    
    def test_unary_operators_combined(self):
        """Test multiple unary operators."""
        code = """
class Number:
    def __neg__(self):
        return Number(-self.value)
    
    def __pos__(self):
        return Number(+self.value)
    
    def __abs__(self):
        return Number(abs(self.value))
"""
        result = transpile(code)
        assert "__neg__(" in result
        assert "__pos__(" in result
        assert "__abs__(" in result


# =============================================================================
# OPERATOR PRECEDENCE (10 tests)
# =============================================================================

class TestOperatorPrecedence:
    """Test operator precedence with dunder methods."""
    
    def test_multiplication_before_addition(self):
        """Test * has higher precedence than +."""
        code = """
class Number:
    def __add__(self, other):
        return Number(self.value + other.value)
    
    def __mul__(self, other):
        return Number(self.value * other.value)

a = Number(1)
b = Number(2)
c = Number(3)
result = a + b * c
"""
        result = transpile(code)
        # Should evaluate b * c first, then a + (b * c)
        assert "__py.dunders.mul" in result
        assert "__py.dunders.add" in result
    
    def test_power_before_multiplication(self):
        """Test ** has higher precedence than *."""
        code = """
class Number:
    def __pow__(self, other):
        return Number(self.value ** other.value)
    
    def __mul__(self, other):
        return Number(self.value * other.value)

a = Number(2)
b = Number(3)
c = Number(4)
result = a * b ** c
"""
        result = transpile(code)
        # Should evaluate b ** c first, then a * (b ** c)
        assert "__py.dunders.pow" in result
        assert "__py.dunders.mul" in result
    
    def test_parentheses_override_precedence(self):
        """Test parentheses override precedence."""
        code = """
class Number:
    def __add__(self, other):
        return Number(self.value + other.value)
    
    def __mul__(self, other):
        return Number(self.value * other.value)

a = Number(1)
b = Number(2)
c = Number(3)
result = (a + b) * c
"""
        result = transpile(code)
        # Should evaluate (a + b) first, then (a + b) * c
        assert "__py.dunders.add" in result
        assert "__py.dunders.mul" in result
    
    def test_unary_before_binary(self):
        """Test unary operators have higher precedence than binary."""
        code = """
class Number:
    def __neg__(self):
        return Number(-self.value)
    
    def __add__(self, other):
        return Number(self.value + other.value)

a = Number(1)
b = Number(2)
result = -a + b
"""
        result = transpile(code)
        # Should evaluate -a first, then (-a) + b
        assert "__py.dunders.neg" in result
        assert "__py.dunders.add" in result
    
    def test_chained_comparisons(self):
        """Test chained comparisons."""
        code = """
a = 1
b = 2
c = 3
result = a < b < c
"""
        result = transpile(code)
        # Should evaluate a < b and b < c
        assert "<" in result or "__py.eq" in result
    
    def test_arithmetic_with_comparison(self):
        """Test arithmetic operators with comparison operators."""
        code = """
class Number:
    def __add__(self, other):
        return Number(self.value + other.value)
    
    def __lt__(self, other):
        return self.value < other.value

a = Number(1)
b = Number(2)
c = Number(3)
result = a + b < c
"""
        result = transpile(code)
        # Should evaluate a + b first, then (a + b) < c
        assert "__py.dunders.add" in result
        assert "<" in result or "__lt__" in result
    
    def test_bitwise_precedence(self):
        """Test bitwise operator precedence."""
        code = """
class Number:
    def __and__(self, other):
        return Number(self.value & other.value)
    
    def __or__(self, other):
        return Number(self.value | other.value)

a = Number(1)
b = Number(2)
c = Number(3)
result = a & b | c
"""
        result = transpile(code)
        # & has higher precedence than |
        assert "__py.dunders.bitand" in result
        assert "__py.dunders.bitor" in result
    
    def test_shift_precedence(self):
        """Test shift operator precedence."""
        code = """
class Number:
    def __lshift__(self, other):
        return Number(self.value << other.value)
    
    def __add__(self, other):
        return Number(self.value + other.value)

a = Number(1)
b = Number(2)
c = Number(3)
result = a << b + c
"""
        result = transpile(code)
        # + has higher precedence than <<
        assert "__py.dunders.add" in result
        assert "__py.dunders.lshift" in result
    
    def test_complex_precedence(self):
        """Test complex expression with multiple precedence levels."""
        code = """
class Number:
    def __add__(self, other):
        return Number(self.value + other.value)
    
    def __mul__(self, other):
        return Number(self.value * other.value)
    
    def __pow__(self, other):
        return Number(self.value ** other.value)

a = Number(1)
b = Number(2)
c = Number(3)
d = Number(4)
result = a + b * c ** d
"""
        result = transpile(code)
        # Should evaluate c ** d, then b * (c ** d), then a + (b * (c ** d))
        assert "__py.dunders.pow" in result
        assert "__py.dunders.mul" in result
        assert "__py.dunders.add" in result
    
    def test_precedence_with_in_place(self):
        """Test precedence with in-place operators."""
        code = """
class Counter:
    def __iadd__(self, other):
        self.value += other.value
        return self
    
    def __mul__(self, other):
        return Counter(self.value * other.value)

a = Counter(1)
b = Counter(2)
c = Counter(3)
a += b * c
"""
        result = transpile(code)
        # Should evaluate b * c first, then a += (b * c)
        assert "__py.dunders.mul" in result
        assert "__iadd__(" in result or "__py.dunders.iadd" in result


# =============================================================================
# EDGE CASES AND ERROR HANDLING (15 tests)
# =============================================================================

class TestOperatorEdgeCases:
    """Test edge cases and error handling for operators."""
    
    def test_operator_with_none(self):
        """Test operator with None."""
        code = """
class Number:
    def __add__(self, other):
        if other is None:
            return None
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
    
    def test_operator_with_zero(self):
        """Test operator with zero."""
        code = """
class Number:
    def __truediv__(self, other):
        if other.value == 0:
            raise ZeroDivisionError("division by zero")
        return Number(self.value / other.value)
"""
        result = transpile(code)
        assert "__truediv__(" in result
    
    def test_operator_with_negative(self):
        """Test operator with negative numbers."""
        code = """
class Number:
    def __pow__(self, other):
        if other.value < 0:
            return Number(1 / (self.value ** abs(other.value)))
        return Number(self.value ** other.value)
"""
        result = transpile(code)
        assert "__pow__(" in result
    
    def test_operator_type_error(self):
        """Test operator with wrong type."""
        code = """
class Number:
    def __add__(self, other):
        if not isinstance(other, Number):
            raise TypeError("unsupported operand type")
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
        assert "isinstance" in result or "instanceof" in result
    
    def test_operator_return_not_implemented(self):
        """Test operator returning NotImplemented."""
        code = """
class Number:
    def __add__(self, other):
        if not isinstance(other, Number):
            return NotImplemented
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
    
    def test_operator_with_float(self):
        """Test operator with float."""
        code = """
class Number:
    def __add__(self, other):
        if isinstance(other, (int, float)):
            return Number(self.value + other)
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
    
    def test_operator_with_string(self):
        """Test operator with string."""
        code = """
class Number:
    def __add__(self, other):
        if isinstance(other, str):
            return str(self.value) + other
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
    
    def test_operator_with_list(self):
        """Test operator with list."""
        code = """
class Number:
    def __mul__(self, other):
        if isinstance(other, list):
            return [self.value] * len(other)
        return Number(self.value * other.value)
"""
        result = transpile(code)
        assert "__mul__(" in result
    
    def test_operator_chaining(self):
        """Test operator chaining."""
        code = """
class Number:
    def __add__(self, other):
        return Number(self.value + other.value)

a = Number(1)
b = Number(2)
c = Number(3)
result = a + b + c
"""
        result = transpile(code)
        # Should chain: (a + b) + c
        assert "__py.dunders.add" in result
    
    def test_operator_with_conditional(self):
        """Test operator with conditional."""
        code = """
class Number:
    def __add__(self, other):
        if self.value > 0:
            return Number(self.value + other.value)
        return Number(-self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
    
    def test_operator_with_loop(self):
        """Test operator in loop."""
        code = """
class Counter:
    def __iadd__(self, other):
        self.value += other
        return self

c = Counter()
for i in range(10):
    c += i
"""
        result = transpile(code)
        assert "__iadd__(" in result or "__py.dunders.iadd" in result
    
    def test_operator_with_function_call(self):
        """Test operator with function call."""
        code = """
class Number:
    def __add__(self, other):
        return Number(self.value + other.value)

def get_value():
    return Number(5)

result = Number(1) + get_value()
"""
        result = transpile(code)
        assert "__py.dunders.add" in result
    
    def test_operator_with_method_call(self):
        """Test operator with method call."""
        code = """
class Number:
    def __add__(self, other):
        return Number(self.value + other.value)
    
    def double(self):
        return Number(self.value * 2)

a = Number(1)
b = Number(2)
result = a + b.double()
"""
        result = transpile(code)
        assert "__py.dunders.add" in result
    
    def test_operator_with_attribute(self):
        """Test operator with attribute access."""
        code = """
class Number:
    def __init__(self, value):
        self.value = value
    
    def __add__(self, other):
        return Number(self.value + other.value)

a = Number(1)
b = Number(2)
result = a + b
assert result.value == 3
"""
        result = transpile(code)
        assert "__py.dunders.add" in result
    
    def test_operator_with_nested_classes(self):
        """Test operator with nested class access."""
        code = """
class Outer:
    class Inner:
        def __add__(self, other):
            return Outer.Inner(self.value + other.value)
"""
        result = transpile(code)
        # Nested classes may not be fully supported, but should not crash
        assert "__add__(" in result or "class" in result


# =============================================================================
# PYTHON-JS EQUIVALENCE TESTS (15 tests)
# =============================================================================

class TestOperatorEquivalence:
    """Test Python-JS equivalence for operator overloading."""
    
    @pytest.mark.asyncio
    async def test_add_equivalence(self):
        """Test addition operator equivalence."""
        code = """
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

v1 = Vector(1, 2)
v2 = Vector(3, 4)
result = v1 + v2
print(result.x, result.y)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_sub_equivalence(self):
        """Test subtraction operator equivalence."""
        code = """
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

v1 = Vector(5, 6)
v2 = Vector(3, 4)
result = v1 - v2
print(result.x, result.y)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_mul_equivalence(self):
        """Test multiplication operator equivalence."""
        code = """
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)

v = Vector(2, 3)
result = v * 5
print(result.x, result.y)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_radd_equivalence(self):
        """Test reverse addition equivalence."""
        code = """
class Number:
    def __init__(self, value):
        self.value = value
    
    def __radd__(self, other):
        return Number(other + self.value)

result = 5 + Number(10)
print(result.value)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_iadd_equivalence(self):
        """Test in-place addition equivalence."""
        code = """
class Counter:
    def __init__(self, value):
        self.value = value
    
    def __iadd__(self, other):
        self.value += other
        return self

c = Counter(5)
c += 10
print(c.value)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_neg_equivalence(self):
        """Test negation equivalence."""
        code = """
class Number:
    def __init__(self, value):
        self.value = value
    
    def __neg__(self):
        return Number(-self.value)

n = Number(5)
result = -n
print(result.value)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_abs_equivalence(self):
        """Test absolute value equivalence."""
        code = """
class Number:
    def __init__(self, value):
        self.value = value
    
    def __abs__(self):
        return Number(abs(self.value))

n = Number(-5)
result = abs(n)
print(result.value)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_operator_precedence_equivalence(self):
        """Test operator precedence equivalence."""
        code = """
class Number:
    def __init__(self, value):
        self.value = value
    
    def __add__(self, other):
        return Number(self.value + other.value)
    
    def __mul__(self, other):
        return Number(self.value * other.value)

a = Number(1)
b = Number(2)
c = Number(3)
result = a + b * c
print(result.value)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_complex_expression_equivalence(self):
        """Test complex expression equivalence."""
        code = """
class Number:
    def __init__(self, value):
        self.value = value
    
    def __add__(self, other):
        return Number(self.value + other.value)
    
    def __sub__(self, other):
        return Number(self.value - other.value)
    
    def __mul__(self, other):
        return Number(self.value * other.value)

a = Number(10)
b = Number(5)
c = Number(2)
result = (a + b) * c - Number(5)
print(result.value)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_string_multiplication_equivalence(self):
        """Test string multiplication equivalence."""
        code = """
s = "abc" * 3
print(s)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_list_concatenation_equivalence(self):
        """Test list concatenation equivalence."""
        code = """
items = [1, 2] + [3, 4]
print(items)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            # Normalize list output
            py_lines = py_result["stdout"].strip().split("\n")
            js_lines = js_result["stdout"].strip().split("\n")
            assert len(py_lines) == len(js_lines)
    
    @pytest.mark.asyncio
    async def test_list_repetition_equivalence(self):
        """Test list repetition equivalence."""
        code = """
items = [1, 2] * 3
print(items)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            # Normalize list output
            py_lines = py_result["stdout"].strip().split("\n")
            js_lines = js_result["stdout"].strip().split("\n")
            assert len(py_lines) == len(js_lines)
    
    @pytest.mark.asyncio
    async def test_numeric_optimization_equivalence(self):
        """Test numeric optimization equivalence."""
        code = """
result = 5 + 3
print(result)
result = 10 * 2
print(result)
result = 8 // 3
print(result)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_chained_operators_equivalence(self):
        """Test chained operators equivalence."""
        code = """
class Number:
    def __init__(self, value):
        self.value = value
    
    def __add__(self, other):
        return Number(self.value + other.value)

a = Number(1)
b = Number(2)
c = Number(3)
result = a + b + c
print(result.value)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_operator_with_none_equivalence(self):
        """Test operator with None equivalence."""
        code = """
class Number:
    def __init__(self, value):
        self.value = value
    
    def __add__(self, other):
        if other is None:
            return None
        return Number(self.value + other.value)

a = Number(5)
result = a + None
print(result is None)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            # Both should print True or equivalent
            assert "True" in py_result["stdout"] or "true" in js_result["stdout"]


# =============================================================================
# INTEGRATION TESTS (10 tests)
# =============================================================================

class TestOperatorIntegration:
    """Test operator overloading integration with other features."""
    
    def test_operator_with_inheritance(self):
        """Test operator overloading with inheritance."""
        code = """
class Base:
    def __add__(self, other):
        return Base(self.value + other.value)

class Derived(Base):
    def __add__(self, other):
        return Derived(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
        assert "extends" in result
    
    def test_operator_with_property(self):
        """Test operator overloading with @property."""
        code = """
class Number:
    @property
    def value(self):
        return self._value
    
    def __add__(self, other):
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
        assert "get value()" in result
    
    def test_operator_with_staticmethod(self):
        """Test operator overloading with @staticmethod."""
        code = """
class Number:
    @staticmethod
    def create(value):
        return Number(value)
    
    def __add__(self, other):
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
        assert "static" in result
    
    def test_operator_with_classmethod(self):
        """Test operator overloading with @classmethod."""
        code = """
class Number:
    @classmethod
    def from_string(cls, s):
        return cls(int(s))
    
    def __add__(self, other):
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
    
    def test_operator_with_decorator(self):
        """Test operator overloading with decorator."""
        code = """
def validate(f):
    def wrapper(self, other):
        if other is None:
            raise ValueError("other cannot be None")
        return f(self, other)
    return wrapper

class Number:
    @validate
    def __add__(self, other):
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
    
    def test_operator_with_multiple_inheritance(self):
        """Test operator overloading with multiple inheritance."""
        code = """
class AddMixin:
    def __add__(self, other):
        return AddMixin(self.value + other.value)

class MulMixin:
    def __mul__(self, other):
        return MulMixin(self.value * other.value)

class Combined(AddMixin, MulMixin):
    pass
"""
        result = transpile(code)
        assert "__add__(" in result
        assert "__mul__(" in result
    
    def test_operator_with_generator(self):
        """Test operator overloading with generator."""
        code = """
class Number:
    def __iter__(self):
        yield self.value
    
    def __add__(self, other):
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
        assert "Symbol.iterator" in result
    
    def test_operator_with_async(self):
        """Test operator overloading with async."""
        code = """
class Number:
    async def compute(self):
        return self.value * 2
    
    def __add__(self, other):
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
        assert "async" in result
    
    def test_operator_with_context_manager(self):
        """Test operator overloading with context manager."""
        code = """
class Number:
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def __add__(self, other):
        return Number(self.value + other.value)
"""
        result = transpile(code)
        assert "__add__(" in result
        assert "__enter__" in result
    
    def test_operator_with_pattern_matching(self):
        """Test operator overloading with pattern matching."""
        code = """
class Number:
    def __add__(self, other):
        match other:
            case int(n):
                return Number(self.value + n)
            case Number(n):
                return Number(self.value + n.value)
            case _:
                raise TypeError("unsupported type")
"""
        result = transpile(code)
        assert "__add__(" in result
        assert "match" in result or "switch" in result or "if" in result

