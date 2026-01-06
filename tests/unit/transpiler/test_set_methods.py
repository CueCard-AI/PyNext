"""
Tests for Python Set Methods Transpilation (Phase 18.3)

This file tests the transpilation of Python set methods to JavaScript.
Target: 200 tests
"""

import pytest
from pynext.transpiler import transpile, transpile_expression


# =============================================================================
# ADD / REMOVE / DISCARD
# =============================================================================

class TestSetAdd:
    """Tests for s.add(x)"""
    
    def test_basic(self):
        result = transpile_expression('s.add(x)')
        assert 's.add(x)' in result
    
    def test_with_literal(self):
        result = transpile_expression('s.add(5)')
        assert 's.add(5)' in result


class TestSetRemove:
    """Tests for s.remove(x) - throws if missing
    
    Note: Without type info, uses list.remove (same behavior - throws on not found).
    """
    
    def test_basic(self):
        result = transpile_expression('seen.remove(x)')
        # Uses list.remove which has same semantics
        assert '.remove(seen, x)' in result
    
    def test_with_literal(self):
        result = transpile_expression('seen.remove(5)')
        assert '.remove(seen, 5)' in result


class TestSetDiscard:
    """Tests for s.discard(x) - ignores missing"""
    
    def test_basic(self):
        result = transpile_expression('seen.discard(x)')
        assert '__py.set.discard(seen, x)' in result
    
    def test_with_literal(self):
        result = transpile_expression('seen.discard(5)')
        assert '__py.set.discard(seen, 5)' in result


# =============================================================================
# POP
# =============================================================================

class TestSetPop:
    """Tests for s.pop()
    
    Note: Without type info, uses standard pop().
    """
    
    def test_basic(self):
        result = transpile_expression('seen.pop()')
        assert 'seen.pop()' in result
    
    def test_assigned(self):
        result = transpile('x = seen.pop()')
        assert 'seen.pop()' in result


# =============================================================================
# UPDATE
# =============================================================================

class TestSetUpdate:
    """Tests for s.update(other)
    
    Note: Without type info, uses dict.update pattern.
    """
    
    def test_basic(self):
        result = transpile_expression('seen.update(items)')
        # May use dict.update
        assert '.update(seen, items)' in result
    
    def test_with_list(self):
        result = transpile_expression('seen.update([1, 2, 3])')
        assert '.update(seen, [1, 2, 3])' in result


# =============================================================================
# SET OPERATIONS
# =============================================================================

class TestSetUnion:
    """Tests for s.union(other)"""
    
    def test_basic(self):
        result = transpile_expression('seen.union(other)')
        assert '__py.set.union(seen, other)' in result
    
    def test_with_multiple(self):
        result = transpile_expression('seen.union(a, b)')
        assert '__py.set.union(seen, a, b)' in result


class TestSetIntersection:
    """Tests for s.intersection(other)"""
    
    def test_basic(self):
        result = transpile_expression('seen.intersection(other)')
        assert '__py.set.intersection(seen, other)' in result


class TestSetDifference:
    """Tests for s.difference(other)"""
    
    def test_basic(self):
        result = transpile_expression('seen.difference(other)')
        assert '__py.set.difference(seen, other)' in result


class TestSetSymmetricDifference:
    """Tests for s.symmetric_difference(other)"""
    
    def test_basic(self):
        result = transpile_expression('seen.symmetric_difference(other)')
        assert '__py.set.symmetric_difference(seen, other)' in result


# =============================================================================
# IN-PLACE OPERATIONS
# =============================================================================

class TestSetIntersectionUpdate:
    """Tests for s.intersection_update(other)"""
    
    def test_basic(self):
        result = transpile_expression('seen.intersection_update(other)')
        assert '__py.set.intersection_update(seen, other)' in result


class TestSetDifferenceUpdate:
    """Tests for s.difference_update(other)"""
    
    def test_basic(self):
        result = transpile_expression('seen.difference_update(other)')
        assert '__py.set.difference_update(seen, other)' in result


class TestSetSymmetricDifferenceUpdate:
    """Tests for s.symmetric_difference_update(other)"""
    
    def test_basic(self):
        result = transpile_expression('seen.symmetric_difference_update(other)')
        assert '__py.set.symmetric_difference_update(seen, other)' in result


# =============================================================================
# COMPARISON METHODS
# =============================================================================

class TestSetIssubset:
    """Tests for s.issubset(other)"""
    
    def test_basic(self):
        result = transpile_expression('seen.issubset(other)')
        assert '__py.set.issubset(seen, other)' in result


class TestSetIssuperset:
    """Tests for s.issuperset(other)"""
    
    def test_basic(self):
        result = transpile_expression('seen.issuperset(other)')
        assert '__py.set.issuperset(seen, other)' in result


class TestSetIsdisjoint:
    """Tests for s.isdisjoint(other)"""
    
    def test_basic(self):
        result = transpile_expression('seen.isdisjoint(other)')
        assert '__py.set.isdisjoint(seen, other)' in result


# =============================================================================
# COPY / CLEAR
# =============================================================================

class TestSetCopy:
    """Tests for s.copy()
    
    Note: Without type info, uses list spread pattern.
    """
    
    def test_basic(self):
        result = transpile_expression('seen.copy()')
        # Uses list spread
        assert '[...seen]' in result or '__py.set.copy' in result


class TestSetClear:
    """Tests for s.clear()
    
    Note: Without type info, uses list pattern.
    """
    
    def test_basic(self):
        result = transpile_expression('visited.clear()')
        # May use list pattern
        assert '.clear()' in result or '.length = 0' in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestSetMethodsInComprehensions:
    """Tests for set methods in comprehensions."""
    
    def test_union_in_list_comp(self):
        result = transpile_expression('[s.union(other) for s in sets]')
        assert '__py.set.union' in result


class TestSetMethodsInConditions:
    """Tests for set methods in conditions."""
    
    def test_issubset_in_if(self):
        result = transpile('if seen.issubset(allowed):\n    pass')
        assert '__py.set.issubset' in result
    
    def test_isdisjoint_in_if(self):
        result = transpile('if seen.isdisjoint(forbidden):\n    pass')
        assert '__py.set.isdisjoint' in result


class TestSetMethodsWithVariables:
    """Tests for set methods with variable arguments."""
    
    def test_add_with_expression(self):
        result = transpile_expression('seen.add(x + 1)')
        assert 'seen.add(' in result
    
    def test_union_with_variable(self):
        result = transpile_expression('seen.union(other_set)')
        assert '__py.set.union(seen, other_set)' in result


class TestSetMethodsOnFunctionResults:
    """Tests for set methods on function return values."""
    
    def test_union_on_function_result(self):
        result = transpile_expression('get_set().union(other)')
        assert '__py.set.union(get_set(), other)' in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestSetEdgeCases:
    """Edge cases for set methods."""
    
    def test_chained_operations(self):
        result = transpile('seen.add(x)\nseen.discard(y)')
        assert '.add(' in result
        assert '__py.set.discard' in result
    
    def test_method_on_subscript(self):
        result = transpile_expression('sets[0].union(sets[1])')
        assert '__py.set.union' in result


class TestSetMethodsInFStrings:
    """Tests for set methods in f-strings."""
    
    def test_issubset_in_fstring(self):
        result = transpile_expression('f"Is subset: {seen.issubset(other)}"')
        assert '__py.set.issubset' in result


class TestMultipleSetOperations:
    """Tests for multiple set operations."""
    
    def test_add_and_remove(self):
        result = transpile('seen.add(x)\nseen.remove(y)')
        assert '.add(' in result
        assert '.remove(seen, y)' in result  # May be list or set remove
    
    def test_union_and_intersection(self):
        result = transpile_expression('seen.union(a).intersection(b)')
        assert '__py.set.union' in result
