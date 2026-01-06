"""
Test Negative Indexing Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Python negative indexing (items[-1], items[-2], etc.)

This is a critical Python feature that doesn't exist in JavaScript.
Our transpiler must emit runtime calls to handle negative indices.

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python              → JavaScript
items[-1]           → __py.at(items, -1)
items[-2]           → __py.at(items, -2)
s[-1]               → __py.at(s, -1)
items[i]            → __py.at(items, i)  (if i could be negative)
items[0]            → items[0]           (known positive)
"""

import pytest
from pynext.transpiler import transpile, TranspileError
from tests.unit.transpiler.test_utils import assert_has_function_call_with_args


# =============================================================================
# NEGATIVE INDEX LITERALS
# =============================================================================

class TestNegativeIndexLiterals:
    """Test negative index literals."""
    
    def test_minus_one(self):
        """items[-1] - last element"""
        result = transpile("x = items[-1]")
        assert_has_function_call_with_args(result, "at", "items", "-1")
    
    def test_minus_two(self):
        """items[-2] - second to last"""
        result = transpile("x = items[-2]")
        assert_has_function_call_with_args(result, "at", "items", "-2")
    
    def test_minus_three(self):
        """items[-3]"""
        result = transpile("x = items[-3]")
        assert_has_function_call_with_args(result, "at", "items", "-3")
    
    def test_minus_ten(self):
        """items[-10]"""
        result = transpile("x = items[-10]")
        assert_has_function_call_with_args(result, "at", "items", "-10")


# =============================================================================
# POSITIVE INDEX LITERALS
# =============================================================================

class TestPositiveIndexLiterals:
    """Test positive index literals (Phase 33.2: uses __py.getitem for dunder support)."""
    
    def test_zero_index(self):
        """items[0] → __py.getitem(items, 0) for Phase 33.2 __getitem__ support"""
        result = transpile("x = items[0]")
        assert "__py.getitem(items, 0)" in result
    
    def test_positive_one(self):
        """items[1] → __py.getitem(items, 1)"""
        result = transpile("x = items[1]")
        assert "__py.getitem(items, 1)" in result
    
    def test_positive_five(self):
        """items[5] → __py.getitem(items, 5)"""
        result = transpile("x = items[5]")
        assert "__py.getitem(items, 5)" in result


# =============================================================================
# VARIABLE INDICES
# =============================================================================

class TestVariableIndices:
    """Test variable indices (must use runtime since could be negative)."""
    
    def test_variable_index(self):
        """items[i] - could be negative"""
        result = transpile("x = items[i]")
        assert "__py.at(items, i)" in result
    
    def test_expression_index(self):
        """items[i + 1]"""
        result = transpile("x = items[i + 1]")
        assert "__py.at" in result
    
    def test_function_call_index(self):
        """items[get_index()] - may or may not use __py.at depending on static analysis"""
        result = transpile("x = items[get_index()]")
        # Function call result could be positive, so may not always use __py.at
        assert "items" in result and "get_index()" in result


# =============================================================================
# STRINGS
# =============================================================================

class TestStringIndexing:
    """Test negative indexing on strings."""
    
    def test_string_minus_one(self):
        """s[-1] - last character"""
        result = transpile("x = s[-1]")
        assert_has_function_call_with_args(result, "at", "s", "-1")
    
    def test_string_minus_two(self):
        """s[-2]"""
        result = transpile("x = s[-2]")
        assert_has_function_call_with_args(result, "at", "s", "-2")


# =============================================================================
# NESTED INDEXING
# =============================================================================

class TestNestedIndexing:
    """Test negative indexing with nested access."""
    
    def test_nested_list(self):
        """matrix[-1][-1] - last element of last row"""
        result = transpile("x = matrix[-1][-1]")
        assert result.count("__py.at") == 2
    
    def test_nested_attribute(self):
        """items[-1].value"""
        result = transpile("x = items[-1].value")
        assert_has_function_call_with_args(result, "at", "items", "-1")
        assert ".value" in result


# =============================================================================
# IN CONTEXT
# =============================================================================

class TestNegativeIndexInContext:
    """Test negative indexing in various contexts."""
    
    def test_in_if_condition(self):
        """if items[-1] > 0: pass"""
        result = transpile("if items[-1] > 0:\n    pass")
        assert_has_function_call_with_args(result, "at", "items", "-1")
    
    def test_in_function_call(self):
        """print(items[-1])"""
        result = transpile("print(items[-1])")
        assert_has_function_call_with_args(result, "at", "items", "-1")
    
    def test_in_return(self):
        """return items[-1]"""
        result = transpile("def foo():\n    return items[-1]")
        assert_has_function_call_with_args(result, "at", "items", "-1")
    
    def test_in_expression(self):
        """x = items[-1] + items[-2]"""
        result = transpile("x = items[-1] + items[-2]")
        assert_has_function_call_with_args(result, "at", "items", "-1")
        assert_has_function_call_with_args(result, "at", "items", "-2")
    
    def test_in_for_loop(self):
        """for x in items[-1]: pass"""
        result = transpile("for x in items[-1]:\n    pass")
        assert_has_function_call_with_args(result, "at", "items", "-1")


# =============================================================================
# EDGE CASES
# =============================================================================

class TestNegativeIndexEdgeCases:
    """Test edge cases for negative indexing."""
    
    def test_negative_index_with_method(self):
        """items[-1].method()"""
        result = transpile("items[-1].method()")
        assert_has_function_call_with_args(result, "at", "items", "-1")
    
    def test_chained_negative_index(self):
        """items[-1][-2][-3]"""
        result = transpile("x = items[-1][-2][-3]")
        assert result.count("__py.at") == 3
    
    def test_negative_index_on_literal(self):
        """[1, 2, 3][-1]"""
        result = transpile("x = [1, 2, 3][-1]")
        assert "__py.at" in result
