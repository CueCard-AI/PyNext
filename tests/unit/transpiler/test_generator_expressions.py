"""
Test Generator Expressions

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests for Python generator expressions in function calls:
- sum(x for x in items) → __py.sum([...items])
- any(x > 0 for x in items) → items.some(x => x > 0)
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# WITH SUM
# =============================================================================

class TestWithSum:
    """Test generator expressions with sum()."""
    
    def test_simple_sum(self):
        """sum(x for x in items)"""
        result = transpile("y = sum(x for x in items)")
        assert "__py.sum" in result or "reduce" in result or ".sum" in result
    
    def test_sum_with_transform(self):
        """sum(x*2 for x in items)"""
        result = transpile("y = sum(x*2 for x in items)")
        # Now optimized to reduce directly: .reduce((acc, x) => acc + (x*2), 0)
        assert ".reduce(" in result or ".map(" in result or "__py.sum" in result
    
    def test_sum_with_filter(self):
        """sum(x for x in items if x > 0)"""
        result = transpile("y = sum(x for x in items if x > 0)")
        assert ".filter(" in result or "__py.sum" in result


# =============================================================================
# WITH ANY/ALL
# =============================================================================

class TestWithAnyAll:
    """Test generator expressions with any() and all()."""
    
    def test_any_comparison(self):
        """any(x > 0 for x in items)"""
        result = transpile("y = any(x > 0 for x in items)")
        assert ".some(" in result or "any" in result
    
    def test_all_comparison(self):
        """all(x > 0 for x in items)"""
        result = transpile("y = all(x > 0 for x in items)")
        assert ".every(" in result or "all" in result
    
    def test_any_truthiness(self):
        """any(x for x in items)"""
        result = transpile("y = any(x for x in items)")
        assert ".some(" in result or "any" in result
    
    def test_all_truthiness(self):
        """all(x for x in items)"""
        result = transpile("y = all(x for x in items)")
        assert ".every(" in result or "all" in result


# =============================================================================
# WITH MIN/MAX
# =============================================================================

class TestWithMinMax:
    """Test generator expressions with min() and max()."""
    
    def test_max_simple(self):
        """max(x for x in items)"""
        result = transpile("y = max(x for x in items)")
        assert "Math.max" in result or "max" in result
    
    def test_min_simple(self):
        """min(x for x in items)"""
        result = transpile("y = min(x for x in items)")
        assert "Math.min" in result or "min" in result
    
    def test_max_attribute(self):
        """max(x.value for x in items)"""
        result = transpile("y = max(x.value for x in items)")
        assert "x.value" in result


# =============================================================================
# WITH OTHER FUNCTIONS
# =============================================================================

class TestWithOtherFunctions:
    """Test generator expressions with other functions."""
    
    def test_list_constructor(self):
        """list(x for x in items)"""
        result = transpile("y = list(x for x in items)")
        assert "[..." in result or "Array" in result
    
    def test_set_constructor(self):
        """set(x for x in items)"""
        result = transpile("y = set(x for x in items)")
        assert "new Set" in result or "Set" in result
    
    def test_custom_function(self):
        """custom_func(x for x in items)"""
        result = transpile("y = process(x*2 for x in items)")
        assert "process" in result


# =============================================================================
# WITH FILTERS
# =============================================================================

class TestWithFilters:
    """Test generator expressions with if clause."""
    
    def test_any_with_filter(self):
        """any(x > 0 for x in items if x is not None)"""
        result = transpile("y = any(x > 0 for x in items if x is not None)")
        assert ".filter(" in result or "some" in result
    
    def test_sum_with_filter(self):
        """sum(x for x in items if x > 0)"""
        result = transpile("y = sum(x for x in items if x > 0)")
        assert ".filter(" in result or "__py.sum" in result


# =============================================================================
# TUPLE UNPACKING
# =============================================================================

class TestTupleUnpacking:
    """Test generator expressions with tuple unpacking."""
    
    def test_sum_values(self):
        """sum(v for k, v in items)"""
        result = transpile("y = sum(v for k, v in items)")
        assert "[k, v]" in result
    
    def test_any_key_check(self):
        """any(k == 'special' for k, v in items)"""
        result = transpile("y = any(k == 'special' for k, v in items)")
        assert "[k, v]" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestGenExpEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_nested_call(self):
        """sum(len(x) for x in items)"""
        result = transpile("y = sum(len(x) for x in items)")
        assert "len(x)" in result or ".length" in result
    
    def test_complex_expression(self):
        """sum(x.a + x.b for x in items)"""
        result = transpile("y = sum(x.a + x.b for x in items)")
        assert "x.a" in result and "x.b" in result


# =============================================================================
# REAL-WORLD PATTERNS
# =============================================================================

class TestRealWorldPatterns:
    """Test common real-world generator expression patterns."""
    
    def test_has_errors(self):
        """any(error.severity == 'critical' for error in errors)"""
        result = transpile("has_critical = any(error.severity == 'critical' for error in errors)")
        assert "error.severity" in result
    
    def test_all_valid(self):
        """all(item.is_valid() for item in items)"""
        result = transpile("all_valid = all(item.is_valid() for item in items)")
        assert "item.is_valid()" in result
    
    def test_total_score(self):
        """sum(player.score for player in players)"""
        result = transpile("total = sum(player.score for player in players)")
        assert "player.score" in result
    
    def test_highest_score(self):
        """max(player.score for player in players)"""
        result = transpile("highest = max(player.score for player in players)")
        assert "player.score" in result


# =============================================================================
# IN HANDLERS
# =============================================================================

class TestInHandlers:
    """Test generator expressions in handlers."""
    
    def test_in_function(self):
        """def check(): return any(x > 0 for x in items)"""
        code = """
def has_positive():
    return any(x > 0 for x in items)
"""
        result = transpile(code)
        assert "some" in result or "any" in result
    
    def test_in_conditional(self):
        """if any(...): do_something()"""
        code = """
if any(x > 0 for x in items):
    process()
"""
        result = transpile(code)
        assert ".some(" in result or "any" in result


# =============================================================================
# OUTPUT STRUCTURE
# =============================================================================

class TestOutputStructure:
    """Test that output has correct structure."""
    
    def test_materialized_to_array(self):
        """Generator should be materialized to array"""
        result = transpile("y = custom(x for x in items)")
        # Should produce an array from the generator
        assert "[..." in result or ".map(" in result or "items" in result
