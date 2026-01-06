"""
Test Chained Comparisons

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests for Python chained comparisons transpiled to JavaScript:
- 0 < x < 10 → (0 < x) && (x < 10)
- a == b == c → __py.eq(a, b) && __py.eq(b, c)
- Mixed operators: 0 <= x < 10
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# SIMPLE CHAINED COMPARISONS
# =============================================================================

class TestSimpleChained:
    """Test simple two-operator chains."""
    
    def test_less_than_chain(self):
        """0 < x < 10"""
        result = transpile("y = 0 < x < 10")
        assert "(0 < x)" in result and "(x < 10)" in result
        assert "&&" in result
    
    def test_less_than_equal_chain(self):
        """0 <= x <= 10"""
        result = transpile("y = 0 <= x <= 10")
        assert "(0 <= x)" in result and "(x <= 10)" in result
    
    def test_greater_than_chain(self):
        """10 > x > 0"""
        result = transpile("y = 10 > x > 0")
        assert "(10 > x)" in result and "(x > 0)" in result
    
    def test_greater_than_equal_chain(self):
        """10 >= x >= 0"""
        result = transpile("y = 10 >= x >= 0")
        assert "(10 >= x)" in result and "(x >= 0)" in result
    
    def test_equality_chain(self):
        """a == b == c"""
        result = transpile("y = a == b == c")
        assert "__py.eq(a, b)" in result and "__py.eq(b, c)" in result
    
    def test_inequality_chain(self):
        """a != b != c"""
        result = transpile("y = a != b != c")
        assert "!__py.eq(a, b)" in result and "!__py.eq(b, c)" in result


# =============================================================================
# MIXED OPERATOR CHAINS
# =============================================================================

class TestMixedOperators:
    """Test chains with different operators."""
    
    def test_less_than_and_less_equal(self):
        """0 < x <= 10"""
        result = transpile("y = 0 < x <= 10")
        assert "(0 < x)" in result and "(x <= 10)" in result
    
    def test_less_equal_and_less_than(self):
        """0 <= x < 10"""
        result = transpile("y = 0 <= x < 10")
        assert "(0 <= x)" in result and "(x < 10)" in result
    
    def test_greater_and_greater_equal(self):
        """10 > x >= 0"""
        result = transpile("y = 10 > x >= 0")
        assert "(10 > x)" in result and "(x >= 0)" in result
    
    def test_equality_and_less_than(self):
        """a == b < c - valid Python but unusual"""
        result = transpile("y = a == b < c")
        assert "__py.eq(a, b)" in result and "(b < c)" in result


# =============================================================================
# THREE OR MORE COMPARISONS
# =============================================================================

class TestLongChains:
    """Test chains with 3+ comparisons."""
    
    def test_triple_less_than(self):
        """a < b < c < d"""
        result = transpile("y = a < b < c < d")
        assert "(a < b)" in result
        assert "(b < c)" in result
        assert "(c < d)" in result
        assert result.count("&&") == 2
    
    def test_triple_equality(self):
        """a == b == c == d"""
        result = transpile("y = a == b == c == d")
        assert "__py.eq(a, b)" in result
        assert "__py.eq(b, c)" in result
        assert "__py.eq(c, d)" in result
    
    def test_quad_chain(self):
        """0 < a < b < c < 100"""
        result = transpile("y = 0 < a < b < c < 100")
        assert result.count("&&") == 3


# =============================================================================
# WITH EXPRESSIONS
# =============================================================================

class TestWithExpressions:
    """Test chains involving expressions."""
    
    def test_with_function_calls(self):
        """0 < len(x) < 10"""
        result = transpile("y = 0 < len(x) < 10")
        assert "len(x)" in result or "x.length" in result
    
    def test_with_arithmetic(self):
        """0 < x + 1 < 10"""
        from tests.unit.transpiler.test_utils import assert_has_runtime_function
        result = transpile("y = 0 < x + 1 < 10")
        # Should have the arithmetic expression - uses dunder runtime
        assert_has_runtime_function(result, "add")
    
    def test_with_attribute(self):
        """0 < obj.value < 10"""
        result = transpile("y = 0 < obj.value < 10")
        assert "obj.value" in result
    
    def test_with_subscript(self):
        """0 < items[0] < 10"""
        result = transpile("y = 0 < items[0] < 10")
        # Phase 33.2: Uses __py.getitem() for __getitem__ dunder support
        assert "__py.getitem(items, 0)" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestChainEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_single_comparison_still_works(self):
        """x < 10 (not chained)"""
        result = transpile("y = x < 10")
        assert "(x < 10)" in result
        assert "&&" not in result
    
    def test_identity_chain(self):
        """a is b is None"""
        result = transpile("y = a is b is None")
        assert "===" in result
    
    def test_in_chain(self):
        """1 in x in y - unusual but valid"""
        result = transpile("y = 1 in x in y")
        assert "__py.in" in result
    
    def test_not_in_chain(self):
        """1 not in x not in y"""
        result = transpile("y = 1 not in x not in y")
        assert "!__py.in" in result
    
    def test_in_if_statement(self):
        """if 0 < x < 10: pass"""
        result = transpile("if 0 < x < 10:\n    pass")
        assert "if" in result
        assert "&&" in result
    
    def test_negative_numbers(self):
        """-10 < x < 10"""
        result = transpile("y = -10 < x < 10")
        assert "-10" in result
    
    def test_float_literals(self):
        """0.5 < x < 1.5"""
        result = transpile("y = 0.5 < x < 1.5")
        assert "0.5" in result and "1.5" in result


# =============================================================================
# REAL-WORLD PATTERNS
# =============================================================================

class TestRealWorldPatterns:
    """Test patterns commonly used in real code."""
    
    def test_range_check(self):
        """Common: 0 <= index < len(items)"""
        result = transpile("valid = 0 <= index < len(items)")
        assert "0 <= index" in result or "(0 <= index)" in result
    
    def test_percentage_check(self):
        """0 <= percent <= 100"""
        result = transpile("valid = 0 <= percent <= 100")
        assert "&&" in result
    
    def test_character_range(self):
        """'a' <= char <= 'z'"""
        result = transpile("is_lower = 'a' <= char <= 'z'")
        # Strings may be single or double quoted in output
        assert ("'a'" in result or '"a"' in result) and ("'z'" in result or '"z"' in result)
    
    def test_in_handler(self):
        """Check in an event handler"""
        code = """
def handle_input(value):
    if 0 <= value <= 100:
        process(value)
"""
        result = transpile(code)
        assert "&&" in result


# =============================================================================
# PARENTHESIZATION
# =============================================================================

class TestParenthesization:
    """Test correct parenthesization of output."""
    
    def test_parts_are_parenthesized(self):
        """Each comparison should be in parens"""
        result = transpile("y = a < b < c")
        # Each part should be wrapped
        assert "(a < b)" in result
        assert "(b < c)" in result
    
    def test_whole_expression_is_correct(self):
        """Overall structure should be correct"""
        result = transpile("y = a < b < c")
        # Should be (a < b) && (b < c)
        assert "(a < b) && (b < c)" in result or "(a < b) && (b < c)" in result
