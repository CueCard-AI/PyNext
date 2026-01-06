"""
Test Slicing Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Python slicing (items[1:3], items[::-1], etc.)

This is a complex Python feature that requires runtime support.

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python              → JavaScript
items[1:3]          → __py.slice(items, 1, 3)
items[:3]           → __py.slice(items, null, 3)
items[1:]           → __py.slice(items, 1, null)
items[:]            → __py.slice(items, null, null)
items[::2]          → __py.slice(items, null, null, 2)
items[::-1]         → __py.slice(items, null, null, -1)
items[1:5:2]        → __py.slice(items, 1, 5, 2)
"""

import pytest
from pynext.transpiler import transpile, TranspileError
from tests.unit.transpiler.test_utils import assert_has_function_call_with_args


# =============================================================================
# BASIC SLICING
# =============================================================================

class TestBasicSlicing:
    """Test basic slice operations."""
    
    def test_slice_start_stop(self):
        """items[1:3]"""
        result = transpile("x = items[1:3]")
        assert "__py.slice(items, 1, 3)" in result
    
    def test_slice_start_only(self):
        """items[1:]"""
        result = transpile("x = items[1:]")
        assert "__py.slice(items, 1, null)" in result
    
    def test_slice_stop_only(self):
        """items[:3]"""
        result = transpile("x = items[:3]")
        assert "__py.slice(items, null, 3)" in result
    
    def test_slice_copy(self):
        """items[:] - full copy"""
        result = transpile("x = items[:]")
        assert "__py.slice(items, null, null)" in result


# =============================================================================
# SLICING WITH STEP
# =============================================================================

class TestSlicingWithStep:
    """Test slicing with step parameter."""
    
    def test_slice_step_2(self):
        """items[::2] - every other element"""
        result = transpile("x = items[::2]")
        assert "__py.slice(items, null, null, 2)" in result
    
    def test_slice_step_3(self):
        """items[::3]"""
        result = transpile("x = items[::3]")
        assert "__py.slice(items, null, null, 3)" in result
    
    def test_slice_full(self):
        """items[1:5:2]"""
        result = transpile("x = items[1:5:2]")
        assert "__py.slice(items, 1, 5, 2)" in result
    
    def test_slice_start_step(self):
        """items[1::2]"""
        result = transpile("x = items[1::2]")
        assert "__py.slice(items, 1, null, 2)" in result
    
    def test_slice_stop_step(self):
        """items[:5:2]"""
        result = transpile("x = items[:5:2]")
        assert "__py.slice(items, null, 5, 2)" in result


# =============================================================================
# NEGATIVE SLICING
# =============================================================================

class TestNegativeSlicing:
    """Test slicing with negative indices."""
    
    def test_negative_start(self):
        """items[-3:]"""
        result = transpile("x = items[-3:]")
        assert_has_function_call_with_args(result, "slice", "items", "-3", "null")
    
    def test_negative_stop(self):
        """items[:-1]"""
        result = transpile("x = items[:-1]")
        assert_has_function_call_with_args(result, "slice", "items", "null", "-1")
    
    def test_negative_both(self):
        """items[-3:-1]"""
        result = transpile("x = items[-3:-1]")
        assert_has_function_call_with_args(result, "slice", "items", "-3", "-1")
    
    def test_reverse(self):
        """items[::-1] - reverse"""
        result = transpile("x = items[::-1]")
        assert_has_function_call_with_args(result, "slice", "items", "null", "null", "-1")
    
    def test_reverse_step_2(self):
        """items[::-2]"""
        result = transpile("x = items[::-2]")
        assert_has_function_call_with_args(result, "slice", "items", "null", "null", "-2")


# =============================================================================
# STRING SLICING
# =============================================================================

class TestStringSlicing:
    """Test slicing strings."""
    
    def test_string_slice(self):
        """s[1:3]"""
        result = transpile("x = s[1:3]")
        assert "__py.slice(s, 1, 3)" in result
    
    def test_string_reverse(self):
        """s[::-1] - reverse string"""
        result = transpile("x = s[::-1]")
        assert_has_function_call_with_args(result, "slice", "s", "null", "null", "-1")
    
    def test_string_first_n(self):
        """s[:5]"""
        result = transpile("x = s[:5]")
        assert "__py.slice(s, null, 5)" in result
    
    def test_string_last_n(self):
        """s[-5:]"""
        result = transpile("x = s[-5:]")
        assert_has_function_call_with_args(result, "slice", "s", "-5", "null")


# =============================================================================
# VARIABLE BOUNDS
# =============================================================================

class TestVariableBounds:
    """Test slicing with variable bounds."""
    
    def test_variable_start(self):
        """items[start:]"""
        result = transpile("x = items[start:]")
        assert "__py.slice(items, start, null)" in result
    
    def test_variable_stop(self):
        """items[:end]"""
        result = transpile("x = items[:end]")
        assert "__py.slice(items, null, end)" in result
    
    def test_variable_both(self):
        """items[start:end]"""
        result = transpile("x = items[start:end]")
        assert "__py.slice(items, start, end)" in result
    
    def test_variable_step(self):
        """items[::step]"""
        result = transpile("x = items[::step]")
        assert "__py.slice(items, null, null, step)" in result
    
    def test_all_variables(self):
        """items[start:end:step]"""
        result = transpile("x = items[start:end:step]")
        assert "__py.slice(items, start, end, step)" in result


# =============================================================================
# NESTED AND CHAINED
# =============================================================================

class TestNestedSlicing:
    """Test slicing with nested/chained access."""
    
    def test_slice_then_index(self):
        """items[1:3][0]"""
        result = transpile("x = items[1:3][0]")
        assert "__py.slice" in result
    
    def test_index_then_slice(self):
        """matrix[0][1:3]"""
        result = transpile("x = matrix[0][1:3]")
        assert "__py.slice" in result
    
    def test_multiple_slices(self):
        """items[1:5][1:3]"""
        result = transpile("x = items[1:5][1:3]")
        assert result.count("__py.slice") == 2


# =============================================================================
# IN CONTEXT
# =============================================================================

class TestSlicingInContext:
    """Test slicing in various contexts."""
    
    def test_slice_in_for(self):
        """for x in items[1:]: pass"""
        result = transpile("for x in items[1:]:\n    pass")
        assert "__py.slice" in result
    
    def test_slice_in_return(self):
        """return items[:5]"""
        result = transpile("def foo():\n    return items[:5]")
        assert "__py.slice" in result
    
    def test_slice_in_call(self):
        """process(items[1:3])"""
        result = transpile("process(items[1:3])")
        assert "__py.slice" in result
    
    def test_slice_comparison(self):
        """if items[:3] == target: pass"""
        result = transpile("if items[:3] == target:\n    pass")
        assert "__py.slice" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestSlicingEdgeCases:
    """Test edge cases for slicing."""
    
    def test_empty_slice(self):
        """items[5:5] - empty result"""
        result = transpile("x = items[5:5]")
        assert "__py.slice(items, 5, 5)" in result
    
    def test_zero_step(self):
        """Step of 0 should still transpile (runtime will error)"""
        result = transpile("x = items[::0]")
        assert "__py.slice" in result
    
    def test_large_indices(self):
        """items[100:200]"""
        result = transpile("x = items[100:200]")
        assert "__py.slice(items, 100, 200)" in result
    
    def test_expression_bounds(self):
        """items[a+1:b-1]"""
        result = transpile("x = items[a+1:b-1]")
        assert "__py.slice" in result
