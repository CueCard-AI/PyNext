"""
Test Augmented Assignment Statement Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Augmented assignment statements: x += value, x -= value, etc.

Covers:
- All arithmetic operators (+=, -=, *=, /=, //=, %=, **=)
- Bitwise operators (&=, |=, ^=, <<=, >>=)
- Edge cases with different value types

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python                  → JavaScript
x += 1                  → x += 1; (native JS for numeric literals)
x += y                  → x = __py.dunders.iadd(x, y); (dunder runtime for unknown types)
x //= 2                 → x = __py.dunders.ifloordiv(x, 2); (in-place dunder runtime)
x %= 3                  → x = __py.dunders.imod(x, 3); (in-place dunder runtime)
x **= 2                 → x = __py.dunders.ipow(x, 2); (in-place dunder runtime)
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# ADDITION ASSIGNMENT
# =============================================================================

class TestAdditionAssignment:
    """Test += operator."""
    
    def test_add_int(self):
        """x += 1"""
        assert transpile("x += 1") == "x += 1;"
    
    def test_add_zero(self):
        """x += 0"""
        assert transpile("x += 0") == "x += 0;"
    
    def test_add_negative(self):
        """x += -5 → x += (-5); (parentheses for precedence)"""
        result = transpile("x += -5")
        # Parentheses are correct for precedence - accept either format
        assert result == "x += (-5);" or result == "x += -5;"
    
    def test_add_float(self):
        """x += 0.5"""
        assert transpile("x += 0.5") == "x += 0.5;"
    
    def test_add_variable(self):
        """x += y → uses dunder runtime for unknown types"""
        result = transpile("x += y")
        assert "__py.dunders.iadd" in result
        assert "x" in result
        assert "y" in result
    
    def test_add_expression(self):
        """x += a + b → uses dunder runtime for unknown types"""
        result = transpile("x += a + b")
        assert "__py.dunders.iadd" in result
        assert "x" in result


# =============================================================================
# SUBTRACTION ASSIGNMENT
# =============================================================================

class TestSubtractionAssignment:
    """Test -= operator."""
    
    def test_sub_int(self):
        """x -= 1"""
        assert transpile("x -= 1") == "x -= 1;"
    
    def test_sub_zero(self):
        """x -= 0"""
        assert transpile("x -= 0") == "x -= 0;"
    
    def test_sub_negative(self):
        """x -= -5 → x -= (-5); (parentheses for precedence)"""
        result = transpile("x -= -5")
        # Parentheses are correct for precedence - accept either format
        assert result == "x -= (-5);" or result == "x -= -5;"
    
    def test_sub_variable(self):
        """x -= y → uses dunder runtime for unknown types"""
        result = transpile("x -= y")
        assert "__py.dunders.isub" in result
        assert "x" in result
        assert "y" in result


# =============================================================================
# MULTIPLICATION ASSIGNMENT
# =============================================================================

class TestMultiplicationAssignment:
    """Test *= operator."""
    
    def test_mul_int(self):
        """x *= 2"""
        assert transpile("x *= 2") == "x *= 2;"
    
    def test_mul_zero(self):
        """x *= 0"""
        assert transpile("x *= 0") == "x *= 0;"
    
    def test_mul_one(self):
        """x *= 1"""
        assert transpile("x *= 1") == "x *= 1;"
    
    def test_mul_float(self):
        """x *= 1.5"""
        assert transpile("x *= 1.5") == "x *= 1.5;"
    
    def test_mul_variable(self):
        """x *= y → uses dunder runtime for unknown types"""
        result = transpile("x *= y")
        assert "__py.dunders.imul" in result
        assert "x" in result
        assert "y" in result


# =============================================================================
# DIVISION ASSIGNMENT
# =============================================================================

class TestDivisionAssignment:
    """Test /= operator."""
    
    def test_div_int(self):
        """x /= 2"""
        assert transpile("x /= 2") == "x /= 2;"
    
    def test_div_float(self):
        """x /= 0.5"""
        assert transpile("x /= 0.5") == "x /= 0.5;"
    
    def test_div_variable(self):
        """x /= y → uses dunder runtime for unknown types"""
        result = transpile("x /= y")
        assert "__py.dunders.itruediv" in result
        assert "x" in result
        assert "y" in result


# =============================================================================
# FLOOR DIVISION ASSIGNMENT
# =============================================================================

class TestFloorDivisionAssignment:
    """Test //= operator."""
    
    def test_floordiv_int(self):
        """x //= 2 → uses in-place dunder runtime"""
        result = transpile("x //= 2")
        assert "__py.dunders.ifloordiv" in result
        assert "x" in result
        assert "2" in result
    
    def test_floordiv_variable(self):
        """x //= y → uses in-place dunder runtime"""
        result = transpile("x //= y")
        assert "__py.dunders.ifloordiv" in result
        assert "x" in result
        assert "y" in result


# =============================================================================
# MODULO ASSIGNMENT
# =============================================================================

class TestModuloAssignment:
    """Test %= operator."""
    
    def test_mod_int(self):
        """x %= 3 → uses in-place dunder runtime"""
        result = transpile("x %= 3")
        assert "__py.dunders.imod" in result
        assert "x" in result
        assert "3" in result
    
    def test_mod_variable(self):
        """x %= y → uses in-place dunder runtime"""
        result = transpile("x %= y")
        assert "__py.dunders.imod" in result
        assert "x" in result
        assert "y" in result


# =============================================================================
# POWER ASSIGNMENT
# =============================================================================

class TestPowerAssignment:
    """Test **= operator."""
    
    def test_pow_int(self):
        """x **= 2 → uses in-place dunder runtime"""
        result = transpile("x **= 2")
        assert "__py.dunders.ipow" in result
        assert "x" in result
        assert "2" in result
    
    def test_pow_variable(self):
        """x **= y → uses in-place dunder runtime"""
        result = transpile("x **= y")
        assert "__py.dunders.ipow" in result
        assert "x" in result
        assert "y" in result


# =============================================================================
# BITWISE OPERATORS
# =============================================================================

class TestBitwiseAssignment:
    """Test bitwise assignment operators."""
    
    def test_bitand(self):
        """x &= 0xff"""
        assert transpile("x &= 0xff") == "x &= 255;"
    
    def test_bitor(self):
        """x |= 1"""
        assert transpile("x |= 1") == "x |= 1;"
    
    def test_bitxor(self):
        """x ^= 1"""
        assert transpile("x ^= 1") == "x ^= 1;"
    
    def test_lshift(self):
        """x <<= 2"""
        assert transpile("x <<= 2") == "x <<= 2;"
    
    def test_rshift(self):
        """x >>= 2"""
        assert transpile("x >>= 2") == "x >>= 2;"
