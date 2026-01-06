"""
Test Boolean Operators

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests for Python boolean operators with correct semantics:
- x and y → returns x if falsy, else y (not just true/false)
- x or y → returns x if truthy, else y (not just true/false)
- not x → uses __py.bool for truthiness
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# AND OPERATOR
# =============================================================================

class TestAndOperator:
    """Test 'and' operator with Python semantics."""
    
    def test_simple_and(self):
        """x and y"""
        result = transpile("z = x and y")
        assert "__py.bool(x)" in result
        assert "?" in result  # Ternary
    
    def test_and_returns_value(self):
        """and should return value, not boolean"""
        result = transpile("z = a and b")
        # Should be: __py.bool(a) ? b : a
        assert "?" in result and ":" in result
    
    def test_triple_and(self):
        """a and b and c"""
        result = transpile("z = a and b and c")
        assert result.count("__py.bool") >= 2
    
    def test_and_with_literal(self):
        """x and 5"""
        result = transpile("z = x and 5")
        assert "5" in result
    
    def test_and_with_string(self):
        """x and 'hello'"""
        result = transpile('z = x and "hello"')
        assert "hello" in result
    
    def test_and_with_list(self):
        """x and [1, 2]"""
        result = transpile("z = x and [1, 2]")
        assert "[1, 2]" in result


# =============================================================================
# OR OPERATOR
# =============================================================================

class TestOrOperator:
    """Test 'or' operator with Python semantics."""
    
    def test_simple_or(self):
        """x or y"""
        result = transpile("z = x or y")
        assert "__py.bool(x)" in result
    
    def test_or_returns_value(self):
        """or should return value, not boolean"""
        result = transpile("z = a or b")
        # Should be: __py.bool(a) ? a : b
        assert "?" in result and ":" in result
    
    def test_triple_or(self):
        """a or b or c"""
        result = transpile("z = a or b or c")
        assert result.count("__py.bool") >= 2
    
    def test_or_with_default(self):
        """name or 'Anonymous' (default value pattern)"""
        result = transpile("z = name or 'Anonymous'")
        assert "Anonymous" in result
    
    def test_or_with_empty_list(self):
        """items or [] (default list pattern)"""
        result = transpile("z = items or []")
        assert "[]" in result


# =============================================================================
# NOT OPERATOR
# =============================================================================

class TestNotOperator:
    """Test 'not' operator with truthiness."""
    
    def test_simple_not(self):
        """not x"""
        result = transpile("z = not x")
        assert "!__py.bool(x)" in result
    
    def test_not_with_call(self):
        """not func()"""
        result = transpile("z = not func()")
        assert "!__py.bool(func())" in result
    
    def test_not_not(self):
        """not not x (double negation)"""
        result = transpile("z = not not x")
        assert result.count("__py.bool") >= 2
    
    def test_not_comparison(self):
        """not (x > 0)"""
        result = transpile("z = not (x > 0)")
        assert "!__py.bool" in result


# =============================================================================
# COMBINED OPERATORS
# =============================================================================

class TestCombinedOperators:
    """Test combinations of and/or/not."""
    
    def test_and_or(self):
        """a and b or c"""
        result = transpile("z = a and b or c")
        assert "__py.bool" in result
    
    def test_or_and(self):
        """a or b and c"""
        result = transpile("z = a or b and c")
        assert "__py.bool" in result
    
    def test_not_and(self):
        """not a and b"""
        result = transpile("z = not a and b")
        assert "!__py.bool(a)" in result
    
    def test_not_or(self):
        """not a or b"""
        result = transpile("z = not a or b")
        assert "!__py.bool(a)" in result
    
    def test_complex_expression(self):
        """(a and b) or (c and d)"""
        result = transpile("z = (a and b) or (c and d)")
        assert result.count("__py.bool") >= 2


# =============================================================================
# WITH COMPARISONS
# =============================================================================

class TestWithComparisons:
    """Test boolean ops with comparisons."""
    
    def test_and_with_comparison(self):
        """x > 0 and x < 10"""
        result = transpile("z = x > 0 and x < 10")
        assert ">" in result and "<" in result
    
    def test_or_with_comparison(self):
        """x < 0 or x > 100"""
        result = transpile("z = x < 0 or x > 100")
        assert "__py.bool" in result
    
    def test_not_with_in(self):
        """not x in items"""
        result = transpile("z = not x in items")
        # This is "not (x in items)"
        assert "__py.in" in result or "!__py.bool" in result


# =============================================================================
# TRUTHINESS EDGE CASES
# =============================================================================

class TestTruthinessEdgeCases:
    """Test edge cases related to truthiness."""
    
    def test_empty_list_falsy(self):
        """[] should be falsy"""
        result = transpile("z = [] and x")
        assert "__py.bool" in result
    
    def test_empty_dict_falsy(self):
        """{} should be falsy"""
        result = transpile("z = {} and x")
        assert "__py.bool" in result
    
    def test_zero_falsy(self):
        """0 should be falsy"""
        result = transpile("z = 0 and x")
        assert "__py.bool" in result
    
    def test_empty_string_falsy(self):
        """'' should be falsy"""
        result = transpile("z = '' and x")
        assert "__py.bool" in result


# =============================================================================
# IN CONTROL FLOW
# =============================================================================

class TestInControlFlow:
    """Test boolean ops in if/while statements."""
    
    def test_in_if_and(self):
        """if x and y:"""
        result = transpile("if x and y:\n    pass")
        assert "__py.bool" in result
    
    def test_in_if_or(self):
        """if x or y:"""
        result = transpile("if x or y:\n    pass")
        assert "__py.bool" in result
    
    def test_in_if_not(self):
        """if not x:"""
        result = transpile("if not x:\n    pass")
        assert "!__py.bool(x)" in result
    
    def test_in_while(self):
        """while x and running:"""
        result = transpile("while x and running:\n    pass")
        assert "__py.bool" in result
    
    def test_in_ternary(self):
        """a if x and y else b"""
        result = transpile("z = a if x and y else b")
        assert "__py.bool" in result


# =============================================================================
# SHORT-CIRCUIT EVALUATION
# =============================================================================

class TestShortCircuit:
    """Test that short-circuit semantics are preserved."""
    
    def test_and_short_circuit_structure(self):
        """and should use ternary for short-circuit"""
        result = transpile("z = x and expensive_call()")
        # Should be ternary to avoid calling expensive_call if x is falsy
        assert "?" in result
    
    def test_or_short_circuit_structure(self):
        """or should use ternary for short-circuit"""
        result = transpile("z = x or expensive_call()")
        assert "?" in result


# =============================================================================
# REAL-WORLD PATTERNS
# =============================================================================

class TestRealWorldPatterns:
    """Test common real-world patterns."""
    
    def test_default_value_pattern(self):
        """value or default"""
        result = transpile("name = input_name or 'Guest'")
        assert "Guest" in result
    
    def test_guard_pattern(self):
        """user and user.is_admin"""
        result = transpile("is_admin = user and user.is_admin")
        assert "user.is_admin" in result
    
    def test_validation_pattern(self):
        """value and value > 0"""
        result = transpile("valid = value and value > 0")
        assert "__py.bool" in result
    
    def test_none_check_pattern(self):
        """x is not None and x > 0"""
        result = transpile("valid = x is not None and x > 0")
        assert "!==" in result or "!== null" in result
