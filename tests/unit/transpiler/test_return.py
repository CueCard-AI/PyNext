"""
Test Return Statement Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Return statements.

Covers:
- Bare return
- Return with value
- Return with expression
- Return in conditionals
- Multiple returns

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python                      → JavaScript
return                      → return;
return 5                    → return 5;
return x + 1                → return (x + 1);
return None                 → return null;
return x, y                 → return [x, y];
"""

import pytest
from pynext.transpiler import transpile, TranspileError
from tests.unit.transpiler.test_utils import assert_has_runtime_function


# =============================================================================
# BARE RETURN
# =============================================================================

class TestBareReturn:
    """Test bare return statements."""
    
    def test_return_only(self):
        """return"""
        result = transpile("def foo():\n    return")
        assert "return;" in result
    
    def test_return_in_if(self):
        """if x: return"""
        result = transpile("def foo():\n    if x:\n        return")
        assert "return;" in result


# =============================================================================
# RETURN WITH VALUE
# =============================================================================

class TestReturnWithValue:
    """Test return statements with values."""
    
    def test_return_int(self):
        """return 5"""
        result = transpile("def foo():\n    return 5")
        assert "return 5;" in result
    
    def test_return_negative_int(self):
        """return -5"""
        result = transpile("def foo():\n    return -5")
        assert "return -5;" in result or "return (-5);" in result
    
    def test_return_float(self):
        """return 3.14"""
        result = transpile("def foo():\n    return 3.14")
        assert "return 3.14;" in result
    
    def test_return_string(self):
        """return "hello" """
        result = transpile('def foo():\n    return "hello"')
        assert 'return "hello";' in result
    
    def test_return_true(self):
        """return True"""
        result = transpile("def foo():\n    return True")
        assert "return true;" in result
    
    def test_return_false(self):
        """return False"""
        result = transpile("def foo():\n    return False")
        assert "return false;" in result
    
    def test_return_none(self):
        """return None"""
        result = transpile("def foo():\n    return None")
        assert "return null;" in result
    
    def test_return_variable(self):
        """return x"""
        result = transpile("def foo():\n    return x")
        assert "return x;" in result
    
    def test_return_list(self):
        """return [1, 2, 3]"""
        result = transpile("def foo():\n    return [1, 2, 3]")
        assert "return [1, 2, 3];" in result
    
    def test_return_dict(self):
        """return {"a": 1}"""
        result = transpile('def foo():\n    return {"a": 1}')
        assert "return" in result and '"a"' in result


# =============================================================================
# RETURN WITH EXPRESSION
# =============================================================================

class TestReturnWithExpression:
    """Test return statements with expressions."""
    
    def test_return_addition(self):
        """return x + 1 → uses dunder runtime"""
        result = transpile("def foo():\n    return x + 1")
        assert "return" in result
        assert_has_runtime_function(result, "add")
    
    def test_return_multiplication(self):
        """return x * 2 → uses dunder runtime"""
        result = transpile("def foo():\n    return x * 2")
        assert "return" in result
        assert_has_runtime_function(result, "mul")
    
    def test_return_function_call(self):
        """return len(items)"""
        result = transpile("def foo():\n    return len(items)")
        assert "return items.length" in result or "return __py.len(items)" in result
    
    def test_return_method_call(self):
        """return s.lower()"""
        result = transpile("def foo():\n    return s.lower()")
        assert "return s.toLowerCase();" in result
    
    def test_return_ternary(self):
        """return a if cond else b"""
        result = transpile("def foo():\n    return a if cond else b")
        assert "?" in result and ":" in result
    
    def test_return_comparison(self):
        """return x > 0"""
        result = transpile("def foo():\n    return x > 0")
        assert "return" in result and "> 0" in result


# =============================================================================
# RETURN TUPLE
# =============================================================================

class TestReturnTuple:
    """Test return statements with tuples (becomes array)."""
    
    def test_return_tuple_literal(self):
        """return (1, 2)"""
        result = transpile("def foo():\n    return (1, 2)")
        assert "[1, 2]" in result
    
    def test_return_tuple_implicit(self):
        """return x, y"""
        result = transpile("def foo():\n    return x, y")
        assert "[x, y]" in result
    
    def test_return_triple(self):
        """return a, b, c"""
        result = transpile("def foo():\n    return a, b, c")
        assert "[a, b, c]" in result


# =============================================================================
# CONDITIONAL RETURN
# =============================================================================

class TestConditionalReturn:
    """Test return in conditional statements."""
    
    def test_early_return(self):
        """if not valid: return"""
        result = transpile("def foo():\n    if not valid:\n        return\n    work()")
        assert "return;" in result
    
    def test_return_in_else(self):
        """if x: return a else: return b"""
        code = "def foo():\n    if x:\n        return a\n    else:\n        return b"
        result = transpile(code)
        assert "return a;" in result
        assert "return b;" in result
    
    def test_multiple_returns(self):
        """Multiple return points"""
        code = "def foo():\n    if x:\n        return 1\n    elif y:\n        return 2\n    return 3"
        result = transpile(code)
        assert "return 1;" in result
        assert "return 2;" in result
        assert "return 3;" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestReturnEdgeCases:
    """Test edge cases for return statements."""
    
    def test_return_zero(self):
        """return 0"""
        result = transpile("def foo():\n    return 0")
        assert "return 0;" in result
    
    def test_return_empty_string(self):
        """return '' """
        result = transpile("def foo():\n    return ''")
        assert 'return ""' in result
    
    def test_return_empty_list(self):
        """return []"""
        result = transpile("def foo():\n    return []")
        assert "return [];" in result
    
    def test_return_empty_dict(self):
        """return {}"""
        result = transpile("def foo():\n    return {}")
        assert "return {};" in result
