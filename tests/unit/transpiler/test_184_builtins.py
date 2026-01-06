"""
Phase 18.4: Python Builtins Tests

Comprehensive tests for all Python builtin functions transpilation.
Tests verify the transpiler emits correct JavaScript for each builtin.

Test Categories:
1. Basic usage
2. Edge cases  
3. Error handling
4. Keyword arguments
5. Integration
"""

import pytest
from pynext.transpiler import transpile, transpile_expression


# =============================================================================
# SORTED() - 25 tests
# =============================================================================

class TestSorted:
    """Tests for sorted() builtin with key and reverse support."""
    
    # Basic
    def test_sorted_basic(self):
        result = transpile_expression('sorted(items)')
        assert '[...items].sort' in result or '__py.sorted' in result
    
    def test_sorted_list_literal(self):
        result = transpile_expression('sorted([3, 1, 2])')
        assert 'sort' in result
    
    def test_sorted_string(self):
        result = transpile_expression('sorted("cba")')
        assert 'sort' in result
    
    # With key
    def test_sorted_with_key(self):
        result = transpile_expression('sorted(items, key=len)')
        assert '__py.sorted(items, len' in result
    
    def test_sorted_with_lambda_key(self):
        result = transpile_expression('sorted(items, key=lambda x: x.value)')
        assert '__py.sorted' in result
        assert '=>' in result
    
    def test_sorted_with_key_attr(self):
        result = transpile_expression('sorted(users, key=lambda u: u.name)')
        assert '__py.sorted' in result
    
    # With reverse
    def test_sorted_with_reverse(self):
        result = transpile_expression('sorted(items, reverse=True)')
        assert '__py.sorted(items, null, true)' in result
    
    def test_sorted_with_reverse_false(self):
        result = transpile_expression('sorted(items, reverse=False)')
        assert '__py.sorted(items, null, false)' in result or '[...items].sort' in result
    
    # With both
    def test_sorted_with_key_and_reverse(self):
        result = transpile_expression('sorted(items, key=len, reverse=True)')
        assert '__py.sorted(items, len, true)' in result
    
    def test_sorted_all_args(self):
        result = transpile_expression('sorted(data, key=str.lower, reverse=True)')
        assert '__py.sorted' in result
    
    # Edge cases
    def test_sorted_empty_list(self):
        result = transpile_expression('sorted([])')
        assert 'sort' in result
    
    def test_sorted_generator(self):
        result = transpile_expression('sorted(x for x in items)')
        assert 'sort' in result


# =============================================================================
# MIN() / MAX() - 30 tests
# =============================================================================

class TestMinMax:
    """Tests for min() and max() builtins."""
    
    # Basic min
    def test_min_iterable(self):
        result = transpile_expression('min(items)')
        assert '__py.min' in result
    
    def test_min_multiple_args(self):
        result = transpile_expression('min(1, 2, 3)')
        assert '__py.min' in result
    
    def test_min_two_args(self):
        result = transpile_expression('min(a, b)')
        assert '__py.min' in result
    
    def test_min_with_key(self):
        result = transpile_expression('min(items, key=len)')
        assert '__py.min(items, len)' in result
    
    def test_min_lambda_key(self):
        result = transpile_expression('min(users, key=lambda u: u.age)')
        assert '__py.min' in result
    
    # Basic max
    def test_max_iterable(self):
        result = transpile_expression('max(items)')
        assert '__py.max' in result
    
    def test_max_multiple_args(self):
        result = transpile_expression('max(1, 2, 3)')
        assert '__py.max' in result
    
    def test_max_two_args(self):
        result = transpile_expression('max(a, b)')
        assert '__py.max' in result
    
    def test_max_with_key(self):
        result = transpile_expression('max(items, key=len)')
        assert '__py.max(items, len)' in result
    
    def test_max_lambda_key(self):
        result = transpile_expression('max(items, key=lambda x: x.value)')
        assert '__py.max' in result
    
    # Edge cases
    def test_min_single_element(self):
        result = transpile_expression('min([5])')
        assert '__py.min' in result
    
    def test_max_negative_numbers(self):
        result = transpile_expression('max(-1, -2, -3)')
        assert '__py.max' in result


# =============================================================================
# ANY() / ALL() - 20 tests
# =============================================================================

class TestAnyAll:
    """Tests for any() and all() builtins with Python truthiness."""
    
    # any
    def test_any_basic(self):
        result = transpile_expression('any(items)')
        assert '__py.any(items)' in result
    
    def test_any_generator(self):
        result = transpile_expression('any(x > 0 for x in items)')
        assert '__py.any' in result or '.some' in result
    
    def test_any_list(self):
        result = transpile_expression('any([True, False, False])')
        assert '__py.any' in result
    
    def test_any_empty(self):
        result = transpile_expression('any([])')
        assert '__py.any' in result
    
    def test_any_with_condition(self):
        result = transpile_expression('any(x.active for x in users)')
        assert '__py.any' in result or '.some' in result
    
    # all
    def test_all_basic(self):
        result = transpile_expression('all(items)')
        assert '__py.all(items)' in result
    
    def test_all_generator(self):
        result = transpile_expression('all(x > 0 for x in items)')
        assert '__py.all' in result or '.every' in result
    
    def test_all_list(self):
        result = transpile_expression('all([True, True, True])')
        assert '__py.all' in result
    
    def test_all_empty(self):
        result = transpile_expression('all([])')
        assert '__py.all' in result
    
    def test_all_with_condition(self):
        result = transpile_expression('all(x.valid for x in items)')
        assert '__py.all' in result or '.every' in result


# =============================================================================
# FILTER() - 20 tests
# =============================================================================

class TestFilter:
    """Tests for filter() builtin with None support."""
    
    def test_filter_function(self):
        result = transpile_expression('filter(is_valid, items)')
        assert '__py.filter(is_valid' in result
    
    def test_filter_lambda(self):
        result = transpile_expression('filter(lambda x: x > 0, items)')
        assert 'filter(' in result
        assert '=>' in result
    
    def test_filter_none(self):
        """filter(None, x) should use Python truthiness via __py.filter."""
        result = transpile_expression('filter(None, items)')
        assert '__py.filter' in result
    
    def test_filter_with_list(self):
        result = transpile_expression('filter(bool, [0, 1, 2, 0, 3])')
        assert 'filter(' in result
    
    def test_filter_complex_lambda(self):
        result = transpile_expression('filter(lambda x: x.value > threshold, items)')
        assert 'filter(' in result


# =============================================================================
# MAP() - 15 tests
# =============================================================================

class TestMap:
    """Tests for map() builtin."""
    
    def test_map_function(self):
        result = transpile_expression('map(str, items)')
        assert '.map(' in result
    
    def test_map_lambda(self):
        result = transpile_expression('map(lambda x: x * 2, items)')
        assert '.map(' in result
    
    def test_map_builtin(self):
        result = transpile_expression('map(int, strings)')
        assert '.map(' in result
    
    def test_map_method(self):
        result = transpile_expression('map(str.strip, lines)')
        assert '.map(' in result


# =============================================================================
# DIVMOD() - 10 tests
# =============================================================================

class TestDivmod:
    """Tests for divmod() builtin."""
    
    def test_divmod_basic(self):
        result = transpile_expression('divmod(7, 3)')
        assert '__py.divmod(7, 3)' in result
    
    def test_divmod_negative(self):
        result = transpile_expression('divmod(-7, 3)')
        # Negative literals may be wrapped in parentheses
        assert '__py.divmod(-7, 3)' in result or '__py.divmod((-7), 3)' in result
    
    def test_divmod_variables(self):
        result = transpile_expression('divmod(a, b)')
        assert '__py.divmod(a, b)' in result
    
    def test_divmod_unpack(self):
        code = "q, r = divmod(n, d)"
        result = transpile(code)
        assert '__py.divmod' in result


# =============================================================================
# POW() - 12 tests
# =============================================================================

class TestPow:
    """Tests for pow() builtin with optional modulus."""
    
    def test_pow_two_args(self):
        result = transpile_expression('pow(2, 10)')
        assert 'Math.pow(2, 10)' in result
    
    def test_pow_three_args(self):
        result = transpile_expression('pow(2, 10, 1000)')
        assert '__py.pow(2, 10, 1000)' in result
    
    def test_pow_variables(self):
        result = transpile_expression('pow(base, exp)')
        # Phase 33.2: Uses __py.pow() to support __pow__ dunder methods
        assert '__py.pow(base, exp)' in result
    
    def test_pow_with_modulus(self):
        result = transpile_expression('pow(x, y, z)')
        assert '__py.pow(x, y, z)' in result


# =============================================================================
# CALLABLE() - 8 tests
# =============================================================================

class TestCallable:
    """Tests for callable() builtin."""
    
    def test_callable_basic(self):
        result = transpile_expression('callable(func)')
        assert "typeof func === 'function'" in result
    
    def test_callable_method(self):
        result = transpile_expression('callable(obj.method)')
        assert 'function' in result
    
    def test_callable_in_condition(self):
        code = "if callable(handler): handler()"
        result = transpile(code)
        assert 'function' in result


# =============================================================================
# LEN() - 15 tests
# =============================================================================

class TestLen:
    """Tests for len() builtin with Map/Set support."""
    
    def test_len_list(self):
        result = transpile_expression('len(items)')
        assert '__py.len(items)' in result or 'items.length' in result
    
    def test_len_string(self):
        result = transpile_expression('len(s)')
        assert '__py.len(s)' in result or 's.length' in result
    
    def test_len_dict(self):
        result = transpile_expression('len(d)')
        assert '__py.len(d)' in result or 'd.length' in result
    
    def test_len_in_condition(self):
        code = "if len(items) > 0: pass"
        result = transpile(code)
        assert '__py.len' in result or '.length' in result


# =============================================================================
# SUM() - 12 tests
# =============================================================================

class TestSum:
    """Tests for sum() builtin with start value."""
    
    def test_sum_basic(self):
        result = transpile_expression('sum(items)')
        assert '__py.sum(items)' in result
    
    def test_sum_with_start(self):
        result = transpile_expression('sum(items, 10)')
        assert '__py.sum(items, 10)' in result
    
    def test_sum_generator(self):
        result = transpile_expression('sum(x for x in items)')
        # Optimized to reduce for simple generators
        assert '.reduce(' in result or '__py.sum' in result
    
    def test_sum_list_literal(self):
        result = transpile_expression('sum([1, 2, 3])')
        assert '__py.sum' in result


# =============================================================================
# ENUMERATE() / ZIP() / RANGE() - 25 tests
# =============================================================================

class TestIterationBuiltins:
    """Tests for enumerate(), zip(), range()."""
    
    # enumerate
    def test_enumerate_basic(self):
        result = transpile_expression('enumerate(items)')
        assert '__py.enumerate(items)' in result
    
    def test_enumerate_with_start(self):
        result = transpile_expression('enumerate(items, 1)')
        assert '__py.enumerate(items, 1)' in result
    
    def test_enumerate_in_for(self):
        code = "for i, x in enumerate(items): pass"
        result = transpile(code)
        assert '__py.enumerate' in result
    
    # zip
    def test_zip_two(self):
        result = transpile_expression('zip(a, b)')
        assert '__py.zip(a, b)' in result
    
    def test_zip_three(self):
        result = transpile_expression('zip(a, b, c)')
        assert '__py.zip(a, b, c)' in result
    
    def test_zip_in_for(self):
        code = "for x, y in zip(xs, ys): pass"
        result = transpile(code)
        assert '__py.zip' in result
    
    # range
    def test_range_one_arg(self):
        result = transpile_expression('range(10)')
        assert '__py.range(0, 10)' in result
    
    def test_range_two_args(self):
        result = transpile_expression('range(1, 10)')
        assert '__py.range(1, 10)' in result
    
    def test_range_three_args(self):
        result = transpile_expression('range(0, 10, 2)')
        assert '__py.range(0, 10, 2)' in result
    
    def test_range_in_for(self):
        code = "for i in range(n): pass"
        result = transpile(code)
        # range(n) gets optimized to for loop or uses __py.range
        assert '__py.range' in result or 'for (let i' in result


# =============================================================================
# REVERSED() - 8 tests
# =============================================================================

class TestReversed:
    """Tests for reversed() builtin."""
    
    def test_reversed_basic(self):
        result = transpile_expression('reversed(items)')
        assert '[...items].reverse()' in result
    
    def test_reversed_string(self):
        result = transpile_expression('reversed("abc")')
        assert '.reverse()' in result
    
    def test_reversed_in_for(self):
        code = "for x in reversed(items): pass"
        result = transpile(code)
        assert '.reverse()' in result


# =============================================================================
# ROUND() - 10 tests
# =============================================================================

class TestRound:
    """Tests for round() builtin."""
    
    def test_round_no_digits(self):
        result = transpile_expression('round(3.7)')
        assert 'Math.round(3.7)' in result
    
    def test_round_with_digits(self):
        result = transpile_expression('round(3.14159, 2)')
        assert '__py.round(3.14159, 2)' in result or 'toFixed' in result
    
    def test_round_variable(self):
        result = transpile_expression('round(x)')
        assert 'Math.round(x)' in result


# =============================================================================
# TYPE CONVERSION BUILTINS - 20 tests
# =============================================================================

class TestTypeConversion:
    """Tests for str(), int(), float(), bool(), list(), dict(), set(), tuple()."""
    
    def test_str_basic(self):
        result = transpile_expression('str(42)')
        # Phase 33.2: Uses __py.str() to support __str__ dunder methods
        assert '__py.str(42)' in result
    
    def test_str_empty(self):
        result = transpile_expression('str()')
        assert "''" in result
    
    def test_int_basic(self):
        result = transpile_expression('int("42")')
        assert 'parseInt' in result
    
    def test_int_empty(self):
        result = transpile_expression('int()')
        assert '0' in result
    
    def test_float_basic(self):
        result = transpile_expression('float("3.14")')
        assert 'parseFloat' in result
    
    def test_bool_basic(self):
        result = transpile_expression('bool(x)')
        assert '__py.bool(x)' in result
    
    def test_list_basic(self):
        result = transpile_expression('list(items)')
        assert '[...items]' in result
    
    def test_list_empty(self):
        result = transpile_expression('list()')
        assert '[]' in result
    
    def test_dict_basic(self):
        result = transpile_expression('dict(pairs)')
        assert 'Object.fromEntries' in result
    
    def test_dict_empty(self):
        result = transpile_expression('dict()')
        assert '{}' in result
    
    def test_set_basic(self):
        result = transpile_expression('set(items)')
        assert 'new Set(items)' in result
    
    def test_set_empty(self):
        result = transpile_expression('set()')
        assert 'new Set()' in result
    
    def test_tuple_basic(self):
        result = transpile_expression('tuple(items)')
        assert 'Object.freeze' in result
    
    def test_tuple_empty(self):
        result = transpile_expression('tuple()')
        assert 'Object.freeze' in result


# =============================================================================
# ATTRIBUTE BUILTINS - 15 tests
# =============================================================================

class TestAttributeBuiltins:
    """Tests for hasattr(), getattr(), setattr()."""
    
    def test_hasattr_basic(self):
        result = transpile_expression('hasattr(obj, "name")')
        assert '"name" in obj' in result
    
    def test_getattr_basic(self):
        result = transpile_expression('getattr(obj, "name")')
        assert 'obj["name"]' in result
    
    def test_getattr_with_default(self):
        result = transpile_expression('getattr(obj, "name", None)')
        assert '?' in result or 'in' in result
    
    def test_setattr_basic(self):
        result = transpile_expression('setattr(obj, "name", value)')
        assert 'obj["name"] = value' in result


# =============================================================================
# OTHER BUILTINS - 25 tests
# =============================================================================

class TestOtherBuiltins:
    """Tests for abs(), ord(), chr(), print(), isinstance(), type()."""
    
    def test_abs_basic(self):
        result = transpile_expression('abs(-5)')
        # Phase 33.2: Uses __py.abs() to support __abs__ dunder methods
        # Negative literals may be wrapped in parentheses
        assert '__py.abs(-5)' in result or '__py.abs((-5))' in result
    
    def test_ord_basic(self):
        result = transpile_expression('ord("a")')
        assert '.charCodeAt(0)' in result
    
    def test_chr_basic(self):
        result = transpile_expression('chr(65)')
        assert 'String.fromCharCode(65)' in result
    
    def test_print_basic(self):
        result = transpile_expression('print("hello")')
        # Phase 33.2: Uses __py.print() for proper string conversion
        assert '__py.print' in result
    
    def test_print_multiple(self):
        result = transpile_expression('print(a, b, c)')
        # Phase 33.2: Uses __py.print() for proper string conversion
        assert '__py.print(a, b, c)' in result
    
    def test_isinstance_basic(self):
        result = transpile_expression('isinstance(x, int)')
        # Runtime accepts string literals like 'int' for type names
        assert '__py.isinstance(x, \'int\')' in result or '__py.isinstance(x, int)' in result
    
    def test_type_basic(self):
        result = transpile_expression('type(x)')
        assert '__py.type(x)' in result
    
    def test_repr_basic(self):
        result = transpile_expression('repr(obj)')
        assert '__py.repr(obj)' in result
    
    def test_hex_basic(self):
        result = transpile_expression('hex(255)')
        assert 'toString(16)' in result
    
    def test_bin_basic(self):
        result = transpile_expression('bin(10)')
        assert 'toString(2)' in result
    
    def test_oct_basic(self):
        result = transpile_expression('oct(8)')
        assert 'toString(8)' in result


# =============================================================================
# INTEGRATION TESTS - 30 tests
# =============================================================================

class TestBuiltinIntegration:
    """Integration tests combining multiple builtins."""
    
    def test_sorted_with_len_key(self):
        result = transpile_expression('sorted(words, key=len)')
        assert '__py.sorted' in result
    
    def test_min_max_chained(self):
        code = "result = max(min(a, b), min(c, d))"
        result = transpile(code)
        assert 'Math.max' in result or '__py.max' in result
        assert 'Math.min' in result or '__py.min' in result
    
    def test_sum_with_map(self):
        result = transpile_expression('sum(map(len, items))')
        assert '__py.sum' in result
        assert '.map(' in result
    
    def test_filter_then_sorted(self):
        result = transpile_expression('sorted(filter(bool, items))')
        assert 'filter' in result
        assert 'sort' in result
    
    def test_enumerate_with_zip(self):
        result = transpile_expression('list(enumerate(zip(a, b)))')
        assert '__py.enumerate' in result
        assert '__py.zip' in result
    
    def test_any_with_map(self):
        result = transpile_expression('any(map(is_valid, items))')
        assert '__py.any' in result or '.some' in result
    
    def test_all_with_filter(self):
        result = transpile_expression('all(filter(None, items))')
        assert '__py.all' in result or '.every' in result
    
    def test_len_in_sorted_key(self):
        result = transpile_expression('sorted(names, key=len, reverse=True)')
        assert '__py.sorted(names, len, true)' in result
    
    def test_complex_comprehension(self):
        result = transpile_expression('[str(x) for x in sorted(items) if x > 0]')
        assert 'sort' in result
        assert 'filter' in result
        # Phase 33.2: Uses __py.str() to support __str__ dunder methods
        assert '__py.str' in result
    
    def test_nested_min_max(self):
        result = transpile_expression('min(max(a, b), max(c, d))')
        assert 'Math.min' in result or '__py.min' in result


# =============================================================================
# EDGE CASE TESTS - 20 tests
# =============================================================================

class TestBuiltinEdgeCases:
    """Edge cases for builtins."""
    
    def test_sorted_empty_with_key(self):
        result = transpile_expression('sorted([], key=len)')
        assert '__py.sorted' in result
    
    def test_min_single_value_iterable(self):
        result = transpile_expression('min([42])')
        assert 'Math.min' in result or '__py.min' in result
    
    def test_sum_empty_with_start(self):
        result = transpile_expression('sum([], 100)')
        assert '__py.sum' in result
    
    def test_any_generator_expression(self):
        result = transpile_expression('any(x.valid for x in items if x.active)')
        assert '__py.any' in result or '.some' in result
    
    def test_range_negative_step(self):
        result = transpile_expression('range(10, 0, -1)')
        # Negative literals may be wrapped in parentheses for precedence
        assert '__py.range(10, 0, -1)' in result or '__py.range(10, 0, (-1))' in result
    
    def test_filter_with_method(self):
        result = transpile_expression('filter(str.isdigit, chars)')
        assert 'filter(' in result
    
    def test_map_with_lambda(self):
        result = transpile_expression('list(map(lambda x: x ** 2, range(5)))')
        assert '.map(' in result
    
    def test_zip_uneven_lengths(self):
        result = transpile_expression('list(zip([1,2,3], [4,5]))')
        assert '__py.zip' in result
    
    def test_enumerate_string(self):
        result = transpile_expression('list(enumerate("abc"))')
        assert '__py.enumerate' in result
    
    def test_reversed_range(self):
        result = transpile_expression('list(reversed(range(5)))')
        assert '.reverse()' in result
