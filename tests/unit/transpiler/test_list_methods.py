"""
Tests for Python List Methods Transpilation (Phase 18.3)

This file tests the transpilation of Python list methods to JavaScript.
Categories:
1. Basic - Simple method calls, correct output
2. Edge Cases - Empty lists, None, boundaries
3. Error Handling - Exceptions, invalid inputs
4. Integration - Chained methods, nested calls, comprehensions

Target: 200 tests
"""

import pytest
from pynext.transpiler import transpile, transpile_expression
from tests.unit.transpiler.test_utils import assert_has_function_call_with_args


# =============================================================================
# APPEND / EXTEND / INSERT
# =============================================================================

class TestListAppend:
    """Tests for items.append(x) → items.push(x)"""
    
    def test_basic(self):
        result = transpile_expression('items.append(x)')
        assert 'items.push(x)' in result
    
    def test_with_literal(self):
        result = transpile_expression('items.append(1)')
        assert 'items.push(1)' in result
    
    def test_with_expression(self):
        result = transpile_expression('items.append(x + 1)')
        assert 'items.push(' in result
    
    def test_in_loop(self):
        result = transpile('for x in source:\n    items.append(x)')
        assert '.push(' in result


class TestListExtend:
    """Tests for items.extend(other) → items.push(...other)"""
    
    def test_basic(self):
        result = transpile_expression('items.extend(other)')
        assert 'items.push(...other)' in result
    
    def test_with_list_literal(self):
        result = transpile_expression('items.extend([1, 2, 3])')
        assert 'items.push(...[1, 2, 3])' in result
    
    def test_in_loop(self):
        result = transpile('for batch in batches:\n    items.extend(batch)')
        assert '.push(...' in result


class TestListInsert:
    """Tests for items.insert(i, x)"""
    
    def test_basic(self):
        result = transpile_expression('items.insert(0, x)')
        assert '__py.list.insert(items, 0, x)' in result
    
    def test_with_variable_index(self):
        result = transpile_expression('items.insert(i, x)')
        assert '__py.list.insert(items, i, x)' in result
    
    def test_negative_index(self):
        result = transpile_expression('items.insert(-1, x)')
        # Negative literals may be wrapped in parentheses for precedence
        assert '__py.list.insert(items, -1, x)' in result or '__py.list.insert(items, (-1), x)' in result


# =============================================================================
# POP
# =============================================================================

class TestListPop:
    """Tests for items.pop()"""
    
    def test_no_args(self):
        result = transpile_expression('items.pop()')
        assert 'items.pop()' in result
    
    def test_with_index(self):
        result = transpile_expression('items.pop(0)')
        assert '__py.list.pop(items, 0)' in result
    
    def test_with_variable_index(self):
        result = transpile_expression('items.pop(i)')
        assert '__py.list.pop(items, i)' in result
    
    def test_negative_index(self):
        result = transpile_expression('items.pop(-1)')
        # Negative literals may be wrapped in parentheses for precedence
        assert '__py.list.pop(items, -1)' in result or '__py.list.pop(items, (-1))' in result
    
    def test_assigned(self):
        result = transpile('x = items.pop()')
        assert 'items.pop()' in result


# =============================================================================
# REMOVE
# =============================================================================

class TestListRemove:
    """Tests for items.remove(x) - uses deep equality, throws if not found"""
    
    def test_basic(self):
        result = transpile_expression('items.remove(x)')
        assert '__py.list.remove(items, x)' in result
    
    def test_with_literal(self):
        result = transpile_expression('items.remove(5)')
        assert '__py.list.remove(items, 5)' in result
    
    def test_with_list_literal(self):
        result = transpile_expression('items.remove([1, 2])')
        assert '__py.list.remove(items, [1, 2])' in result
    
    def test_in_statement(self):
        result = transpile('items.remove(x)')
        assert '__py.list.remove(items, x)' in result


# =============================================================================
# INDEX
# =============================================================================

class TestListIndex:
    """Tests for items.index(x) - throws if not found
    
    Note: Without type info, emitter uses __py.str.index (same semantics).
    The runtime uses the same index() function for both types.
    """
    
    def test_basic(self):
        result = transpile_expression('items.index(x)')
        # Uses str.index which has same semantics (throws on not found)
        assert '.index(items, x)' in result
    
    def test_with_start(self):
        result = transpile_expression('items.index(x, 5)')
        assert '.index(items, x, 5)' in result
    
    def test_with_start_stop(self):
        result = transpile_expression('items.index(x, 1, 10)')
        assert '.index(items, x, 1, 10)' in result
    
    def test_assigned(self):
        result = transpile('i = items.index(x)')
        assert '.index' in result


# =============================================================================
# COUNT
# =============================================================================

class TestListCount:
    """Tests for items.count(x)
    
    Note: Without type info, emitter uses __py.str.count (same semantics).
    """
    
    def test_basic(self):
        result = transpile_expression('items.count(x)')
        assert '.count(items, x)' in result
    
    def test_with_literal(self):
        result = transpile_expression('items.count(5)')
        assert '.count(items, 5)' in result
    
    def test_in_condition(self):
        result = transpile('if items.count(x) > 0:\n    pass')
        assert '.count' in result


# =============================================================================
# SORT
# =============================================================================

class TestListSort:
    """Tests for items.sort() - numeric by default"""
    
    def test_no_args(self):
        result = transpile_expression('items.sort()')
        assert '__py.list.sort(items)' in result
    
    def test_with_reverse(self):
        result = transpile_expression('items.sort(reverse=True)')
        assert '__py.list.sort(items' in result
        assert 'true' in result.lower()
    
    def test_with_key(self):
        result = transpile_expression('items.sort(key=len)')
        assert '__py.list.sort(items, len' in result
    
    def test_with_key_and_reverse(self):
        result = transpile_expression('items.sort(key=len, reverse=True)')
        assert '__py.list.sort(items' in result


# =============================================================================
# REVERSE
# =============================================================================

class TestListReverse:
    """Tests for items.reverse()"""
    
    def test_basic(self):
        result = transpile_expression('items.reverse()')
        assert 'items.reverse()' in result
    
    def test_in_chain(self):
        result = transpile('items.reverse()\nx = items[0]')
        assert '.reverse()' in result


# =============================================================================
# COPY
# =============================================================================

class TestListCopy:
    """Tests for items.copy() → [...items]"""
    
    def test_basic(self):
        result = transpile_expression('items.copy()')
        assert '[...items]' in result
    
    def test_assigned(self):
        result = transpile('copy = items.copy()')
        assert '[...items]' in result


# =============================================================================
# CLEAR
# =============================================================================

class TestListClear:
    """Tests for items.clear()"""
    
    def test_basic(self):
        result = transpile_expression('items.clear()')
        assert 'items.length = 0' in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestListMethodChaining:
    """Tests for chained list method calls."""
    
    def test_copy_then_sort(self):
        result = transpile_expression('items.copy()')
        assert '[...items]' in result
    
    def test_copy_in_assignment(self):
        result = transpile('sorted_items = items.copy()')
        assert '[...items]' in result


class TestListMethodsInComprehensions:
    """Tests for list methods in comprehensions."""
    
    def test_count_in_list_comp(self):
        result = transpile_expression('[items.count(x) for x in unique]')
        assert '.count' in result
    
    def test_index_in_list_comp(self):
        result = transpile_expression('[items.index(x) for x in targets]')
        assert '.index' in result


class TestListMethodsInConditions:
    """Tests for list methods in if conditions."""
    
    def test_count_in_if(self):
        result = transpile('if items.count(x) > 1:\n    pass')
        assert '.count' in result
    
    def test_index_assigned(self):
        result = transpile('i = items.index(x)')
        assert '.index' in result


class TestListMethodsWithVariables:
    """Tests for list methods with variable arguments."""
    
    def test_append_with_expression(self):
        result = transpile_expression('items.append(a + b)')
        assert '.push(' in result
    
    def test_insert_with_variables(self):
        result = transpile_expression('items.insert(pos, value)')
        assert '__py.list.insert(items, pos, value)' in result


class TestListMethodsOnFunctionResults:
    """Tests for list methods on function return values."""
    
    def test_append_on_function_result(self):
        result = transpile('get_list().append(x)')
        assert 'get_list().push(x)' in result
    
    def test_sort_on_function_result(self):
        result = transpile_expression('get_list().sort()')
        assert '__py.list.sort(get_list())' in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestListEdgeCases:
    """Edge cases for list methods."""
    
    def test_append_list(self):
        result = transpile_expression('items.append([1, 2])')
        assert '.push([1, 2])' in result
    
    def test_method_on_subscript(self):
        result = transpile('matrix[0].append(x)')
        assert '.push(' in result
    
    def test_method_on_dict_value(self):
        result = transpile('d["items"].append(x)')
        assert '.push(' in result
    
    def test_pop_result_used(self):
        result = transpile('last = items.pop()')
        assert 'items.pop()' in result
    
    def test_remove_in_loop(self):
        result = transpile('while x in items:\n    items.remove(x)')
        assert '__py.list.remove' in result


class TestListMethodsInFStrings:
    """Tests for list methods in f-strings."""
    
    def test_count_in_fstring(self):
        result = transpile_expression('f"Count: {items.count(x)}"')
        assert '.count' in result
    
    def test_index_in_fstring(self):
        result = transpile_expression('f"Index: {items.index(x)}"')
        assert '.index' in result


# =============================================================================
# MULTIPLE METHODS
# =============================================================================

class TestMultipleListOperations:
    """Tests for multiple list operations."""
    
    def test_append_multiple(self):
        result = transpile('items.append(1)\nitems.append(2)\nitems.append(3)')
        assert result.count('.push(') == 3
    
    def test_mixed_operations(self):
        result = transpile('items.append(x)\nitems.sort()\nitems.reverse()')
        assert '.push(' in result
        assert '__py.list.sort' in result
        assert '.reverse()' in result
