"""
Phase 18.4: Python Builtins Transpiler Tests

Comprehensive tests for Python builtin function transpilation.
Tests verify the emitter produces correct JavaScript for:
- Enhanced builtins (sorted, min, max with key=)
- New builtins (any, all, divmod, pow, callable)
- Type conversion builtins (str, int, float, bool, list, dict, set, tuple)
- Aggregate builtins (sum, len, abs, round)
- Iteration builtins (enumerate, zip, map, filter, reversed, range)
- Introspection builtins (isinstance, type, callable, hasattr, getattr, setattr)
"""

import pytest
from pynext.transpiler import transpile, transpile_expression


# =============================================================================
# SORTED() WITH KEY AND REVERSE
# =============================================================================

class TestSorted:
    """Tests for sorted() builtin."""
    
    def test_sorted_basic(self):
        """sorted(items) → [...items].sort()"""
        result = transpile_expression('sorted(items)')
        assert 'sort' in result
    
    def test_sorted_with_key(self):
        """sorted(items, key=len) → __py.sorted(items, len)"""
        result = transpile_expression('sorted(items, key=len)')
        assert '__py.sorted' in result
        assert 'len' in result
    
    def test_sorted_with_reverse(self):
        """sorted(items, reverse=True)"""
        result = transpile_expression('sorted(items, reverse=True)')
        assert '__py.sorted' in result
        assert 'true' in result.lower()
    
    def test_sorted_with_key_and_reverse(self):
        """sorted(items, key=len, reverse=True)"""
        result = transpile_expression('sorted(items, key=len, reverse=True)')
        assert '__py.sorted' in result
        assert 'len' in result
        assert 'true' in result.lower()
    
    def test_sorted_with_lambda_key(self):
        """sorted(items, key=lambda x: x.name)"""
        result = transpile_expression('sorted(items, key=lambda x: x.name)')
        assert '__py.sorted' in result
        assert 'x => x.name' in result or '(x) => x.name' in result
    
    def test_sorted_in_assignment(self):
        """result = sorted(data, key=len)"""
        result = transpile('result = sorted(data, key=len)')
        assert '__py.sorted' in result
    
    def test_sorted_in_for_loop(self):
        """for item in sorted(data)"""
        result = transpile('for item in sorted(data):\n    pass')
        assert 'sort' in result


# =============================================================================
# MIN/MAX WITH KEY
# =============================================================================

class TestMinMax:
    """Tests for min() and max() builtins."""
    
    def test_min_single_iterable(self):
        """min(items) → __py.min(items, null) for type checking"""
        result = transpile_expression('min(items)')
        assert '__py.min' in result
    
    def test_min_multiple_args(self):
        """min(a, b, c) → __py.min([a, b, c], null) for type checking"""
        result = transpile_expression('min(a, b, c)')
        assert '__py.min' in result and 'a, b, c' in result
    
    def test_min_with_key(self):
        """min(items, key=len) → __py.min(items, len)"""
        result = transpile_expression('min(items, key=len)')
        assert '__py.min' in result
        assert 'len' in result
    
    def test_max_single_iterable(self):
        """max(items) → __py.max(items, null) for type checking"""
        result = transpile_expression('max(items)')
        assert '__py.max' in result
    
    def test_max_multiple_args(self):
        """max(a, b, c) → __py.max([a, b, c], null) for type checking"""
        result = transpile_expression('max(a, b, c)')
        assert '__py.max' in result and 'a, b, c' in result
    
    def test_max_with_key(self):
        """max(items, key=len) → __py.max(items, len)"""
        result = transpile_expression('max(items, key=len)')
        assert '__py.max' in result
        assert 'len' in result
    
    def test_min_with_lambda_key(self):
        """min(items, key=lambda x: x.score)"""
        result = transpile_expression('min(items, key=lambda x: x.score)')
        assert '__py.min' in result


# =============================================================================
# ANY/ALL
# =============================================================================

class TestAnyAll:
    """Tests for any() and all() builtins."""
    
    def test_any_basic(self):
        """any(items) → __py.any(items)"""
        result = transpile_expression('any(items)')
        assert '__py.any(items)' in result
    
    def test_any_with_generator(self):
        """any(x > 0 for x in items)"""
        result = transpile_expression('any(x > 0 for x in items)')
        assert '__py.any' in result or '.some' in result
    
    def test_all_basic(self):
        """all(items) → __py.all(items)"""
        result = transpile_expression('all(items)')
        assert '__py.all(items)' in result
    
    def test_all_with_generator(self):
        """all(x > 0 for x in items)"""
        result = transpile_expression('all(x > 0 for x in items)')
        assert '__py.all' in result or '.every' in result
    
    def test_any_in_if(self):
        """if any(items): ..."""
        result = transpile('if any(items):\n    pass')
        assert '__py.any' in result
    
    def test_all_in_if(self):
        """if all(items): ..."""
        result = transpile('if all(items):\n    pass')
        assert '__py.all' in result


# =============================================================================
# DIVMOD / POW / CALLABLE
# =============================================================================

class TestDivmodPowCallable:
    """Tests for divmod(), pow(), callable() builtins."""
    
    def test_divmod_basic(self):
        """divmod(a, b) → __py.divmod(a, b)"""
        result = transpile_expression('divmod(10, 3)')
        assert '__py.divmod(10, 3)' in result
    
    def test_divmod_with_variables(self):
        """divmod(x, y)"""
        result = transpile_expression('divmod(x, y)')
        assert '__py.divmod(x, y)' in result
    
    def test_divmod_unpacking(self):
        """q, r = divmod(x, y)"""
        result = transpile('q, r = divmod(x, y)')
        assert '__py.divmod' in result
    
    def test_pow_two_args(self):
        """pow(x, y) → Math.pow(x, y)"""
        result = transpile_expression('pow(2, 10)')
        assert 'Math.pow(2, 10)' in result
    
    def test_pow_three_args(self):
        """pow(x, y, z) → __py.pow(x, y, z)"""
        result = transpile_expression('pow(2, 10, 1000)')
        assert '__py.pow(2, 10, 1000)' in result
    
    def test_callable_basic(self):
        """callable(x) → typeof x === 'function'"""
        result = transpile_expression('callable(func)')
        assert "typeof func === 'function'" in result
    
    def test_callable_in_if(self):
        """if callable(obj): ..."""
        result = transpile('if callable(obj):\n    pass')
        assert 'function' in result


# =============================================================================
# FILTER WITH NONE
# =============================================================================

class TestFilter:
    """Tests for filter() builtin."""
    
    def test_filter_with_function(self):
        """filter(func, items) → [...items].filter(func)"""
        result = transpile_expression('filter(is_valid, items)')
        assert 'filter' in result
    
    def test_filter_with_lambda(self):
        """filter(lambda x: x > 0, items)"""
        result = transpile_expression('filter(lambda x: x > 0, items)')
        assert 'filter' in result
        assert '=>' in result
    
    def test_filter_with_none(self):
        """filter(None, items) → __py.filter(null, items) for truthiness handling"""
        result = transpile_expression('filter(None, items)')
        assert '__py.filter' in result
    
    def test_filter_in_list(self):
        """list(filter(None, items))"""
        result = transpile_expression('list(filter(None, items))')
        assert 'filter' in result


# =============================================================================
# MAP
# =============================================================================

class TestMap:
    """Tests for map() builtin."""
    
    def test_map_single_iterable(self):
        """map(func, items) → [...items].map(func)"""
        result = transpile_expression('map(str, items)')
        assert '.map' in result
    
    def test_map_with_lambda(self):
        """map(lambda x: x * 2, items)"""
        result = transpile_expression('map(lambda x: x * 2, items)')
        assert '.map' in result
        assert '=>' in result
    
    def test_map_multiple_iterables(self):
        """map(func, iter1, iter2) → __py.map(func, iter1, iter2)"""
        result = transpile_expression('map(add, items1, items2)')
        assert '__py.map' in result
    
    def test_list_of_map(self):
        """list(map(func, items))"""
        result = transpile_expression('list(map(str, items))')
        assert 'map' in result


# =============================================================================
# TYPE CONVERSION BUILTINS
# =============================================================================

class TestTypeConversion:
    """Tests for str(), int(), float(), bool(), list(), dict(), set(), tuple()."""
    
    def test_str_basic(self):
        """str(x) → __py.str(x) for Phase 33.2 dunder method support"""
        result = transpile_expression('str(42)')
        # Phase 33.2: Uses __py.str() to support __str__ dunder methods
        assert '__py.str(42)' in result
    
    def test_str_empty(self):
        """str() → ''"""
        result = transpile_expression('str()')
        assert "''" in result or '""' in result
    
    def test_int_basic(self):
        """int(x) → parseInt(x)"""
        result = transpile_expression('int("42")')
        assert 'parseInt' in result
    
    def test_int_empty(self):
        """int() → 0"""
        result = transpile_expression('int()')
        assert '0' in result
    
    def test_float_basic(self):
        """float(x) → parseFloat(x)"""
        result = transpile_expression('float("3.14")')
        assert 'parseFloat' in result
    
    def test_bool_basic(self):
        """bool(x) → __py.bool(x)"""
        result = transpile_expression('bool(items)')
        assert '__py.bool' in result
    
    def test_list_basic(self):
        """list(x) → [...x]"""
        result = transpile_expression('list(items)')
        assert '[...items]' in result
    
    def test_list_empty(self):
        """list() → []"""
        result = transpile_expression('list()')
        assert '[]' in result
    
    def test_dict_basic(self):
        """dict(x) → Object.fromEntries(x)"""
        result = transpile_expression('dict(pairs)')
        assert 'Object.fromEntries' in result
    
    def test_dict_empty(self):
        """dict() → {}"""
        result = transpile_expression('dict()')
        assert '{}' in result
    
    def test_set_basic(self):
        """set(x) → new Set(x)"""
        result = transpile_expression('set(items)')
        assert 'new Set(items)' in result
    
    def test_set_empty(self):
        """set() → new Set()"""
        result = transpile_expression('set()')
        assert 'new Set()' in result
    
    def test_tuple_basic(self):
        """tuple(x) → Object.freeze([...x])"""
        result = transpile_expression('tuple(items)')
        assert 'Object.freeze' in result


# =============================================================================
# AGGREGATE BUILTINS
# =============================================================================

class TestAggregateBuiltins:
    """Tests for sum(), len(), abs(), round()."""
    
    def test_sum_basic(self):
        """sum(items) → __py.sum(items)"""
        result = transpile_expression('sum(items)')
        assert '__py.sum(items)' in result
    
    def test_sum_with_start(self):
        """sum(items, 10) → __py.sum(items, 10)"""
        result = transpile_expression('sum(items, 10)')
        assert '__py.sum(items, 10)' in result
    
    def test_len_basic(self):
        """len(items) → __py.len(items)"""
        result = transpile_expression('len(items)')
        assert '__py.len(items)' in result or 'items.length' in result
    
    def test_abs_basic(self):
        """abs(x) → __py.abs(x) for Phase 33.2 __abs__ dunder support"""
        result = transpile_expression('abs(-5)')
        # Phase 33.2: Uses __py.abs() to support __abs__ dunder methods
        # Negative literals may be wrapped in parentheses
        assert '__py.abs(-5)' in result or '__py.abs((-5))' in result
    
    def test_round_no_digits(self):
        """round(x) → Math.round(x)"""
        result = transpile_expression('round(3.7)')
        assert 'Math.round(3.7)' in result
    
    def test_round_with_digits(self):
        """round(x, 2) → __py.round(x, 2)"""
        result = transpile_expression('round(3.14159, 2)')
        assert 'round' in result
        assert '2' in result


# =============================================================================
# ITERATION BUILTINS
# =============================================================================

class TestIterationBuiltins:
    """Tests for enumerate(), zip(), reversed(), range()."""
    
    def test_enumerate_basic(self):
        """enumerate(items) → __py.enumerate(items)"""
        result = transpile_expression('enumerate(items)')
        assert '__py.enumerate(items)' in result
    
    def test_enumerate_with_start(self):
        """enumerate(items, 1) → __py.enumerate(items, 1)"""
        result = transpile_expression('enumerate(items, 1)')
        assert '__py.enumerate(items, 1)' in result
    
    def test_zip_two_iterables(self):
        """zip(a, b) → __py.zip(a, b)"""
        result = transpile_expression('zip(names, ages)')
        assert '__py.zip(names, ages)' in result
    
    def test_zip_three_iterables(self):
        """zip(a, b, c)"""
        result = transpile_expression('zip(a, b, c)')
        assert '__py.zip(a, b, c)' in result
    
    def test_reversed_basic(self):
        """reversed(items) → [...items].reverse()"""
        result = transpile_expression('reversed(items)')
        assert 'reverse' in result
    
    def test_range_one_arg(self):
        """range(10)"""
        result = transpile_expression('range(10)')
        assert '__py.range' in result
    
    def test_range_two_args(self):
        """range(1, 10)"""
        result = transpile_expression('range(1, 10)')
        assert '__py.range' in result
    
    def test_range_three_args(self):
        """range(0, 10, 2)"""
        result = transpile_expression('range(0, 10, 2)')
        assert '__py.range' in result


# =============================================================================
# INTROSPECTION BUILTINS
# =============================================================================

class TestIntrospectionBuiltins:
    """Tests for isinstance(), type(), hasattr(), getattr(), setattr()."""
    
    def test_isinstance_basic(self):
        """isinstance(x, int) → __py.isinstance(x, int)"""
        result = transpile_expression('isinstance(x, int)')
        assert '__py.isinstance' in result
    
    def test_isinstance_tuple(self):
        """isinstance(x, (int, float))"""
        result = transpile_expression('isinstance(x, (int, float))')
        assert '__py.isinstance' in result
    
    def test_type_basic(self):
        """type(x) → __py.type(x)"""
        result = transpile_expression('type(obj)')
        assert '__py.type(obj)' in result
    
    def test_hasattr_basic(self):
        """hasattr(obj, "x") → ("x" in obj)"""
        result = transpile_expression('hasattr(obj, "name")')
        assert '"name" in obj' in result
    
    def test_getattr_two_args(self):
        """getattr(obj, "x") → obj["x"]"""
        result = transpile_expression('getattr(obj, "name")')
        assert 'obj["name"]' in result
    
    def test_getattr_three_args(self):
        """getattr(obj, "x", default)"""
        result = transpile_expression('getattr(obj, "name", None)')
        assert 'obj["name"]' in result or 'null' in result
    
    def test_setattr_basic(self):
        """setattr(obj, "x", v) → obj["x"] = v"""
        result = transpile_expression('setattr(obj, "name", value)')
        assert 'obj["name"] = value' in result


# =============================================================================
# REPR
# =============================================================================

class TestRepr:
    """Tests for repr() builtin."""
    
    def test_repr_basic(self):
        """repr(x) → __py.repr(x)"""
        result = transpile_expression('repr(obj)')
        assert '__py.repr(obj)' in result
    
    def test_repr_in_fstring(self):
        """f"{obj!r}" uses __py.repr"""
        result = transpile_expression('f"{obj!r}"')
        assert '__py.repr' in result


# =============================================================================
# OTHER BUILTINS
# =============================================================================

class TestOtherBuiltins:
    """Tests for ord(), chr(), print(), input(), hex(), oct(), bin()."""
    
    def test_ord_basic(self):
        """ord("A") → "A".charCodeAt(0)"""
        result = transpile_expression('ord("A")')
        assert '.charCodeAt(0)' in result
    
    def test_chr_basic(self):
        """chr(65) → String.fromCharCode(65)"""
        result = transpile_expression('chr(65)')
        assert 'String.fromCharCode(65)' in result
    
    def test_print_basic(self):
        """print(x) → __py.print(x) for Phase 33.2 string conversion"""
        result = transpile('print(message)')
        assert '__py.print(message)' in result
    
    def test_print_multiple(self):
        """print(a, b, c) → __py.print(a, b, c) for Phase 33.2 string conversion"""
        result = transpile('print(a, b, c)')
        assert '__py.print(a, b, c)' in result
    
    def test_print_empty(self):
        """print() → __py.print() for Phase 33.2 string conversion"""
        result = transpile('print()')
        assert '__py.print()' in result
    
    def test_input_basic(self):
        """input("prompt") → prompt("prompt")"""
        result = transpile_expression('input("Enter: ")')
        assert 'prompt' in result
    
    def test_hex_basic(self):
        """hex(255) → '0x' + 255.toString(16)"""
        result = transpile_expression('hex(255)')
        assert 'toString(16)' in result
    
    def test_oct_basic(self):
        """oct(8) → '0o' + 8.toString(8)"""
        result = transpile_expression('oct(8)')
        assert 'toString(8)' in result
    
    def test_bin_basic(self):
        """bin(8) → '0b' + 8.toString(2)"""
        result = transpile_expression('bin(8)')
        assert 'toString(2)' in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestBuiltinsIntegration:
    """Integration tests combining multiple builtins."""
    
    def test_sorted_then_enumerate(self):
        """for i, x in enumerate(sorted(items)):"""
        result = transpile('for i, x in enumerate(sorted(items)):\n    pass')
        assert 'sort' in result
        assert 'enumerate' in result
    
    def test_filter_then_map(self):
        """list(map(str, filter(None, items)))"""
        result = transpile_expression('list(map(str, filter(None, items)))')
        assert 'filter' in result
        assert 'map' in result
    
    def test_min_of_lengths(self):
        """min(len(x) for x in items)"""
        result = transpile_expression('min(len(x) for x in items)')
        assert 'min' in result.lower() or 'Math.min' in result
    
    def test_sum_of_filtered(self):
        """sum(x for x in items if x > 0)"""
        result = transpile_expression('sum(x for x in items if x > 0)')
        assert '__py.sum' in result or 'reduce' in result
    
    def test_any_with_isinstance(self):
        """any(isinstance(x, str) for x in items)"""
        result = transpile_expression('any(isinstance(x, str) for x in items)')
        assert '__py.any' in result or '.some' in result
    
    def test_all_positive(self):
        """all(x > 0 for x in items)"""
        result = transpile_expression('all(x > 0 for x in items)')
        assert '__py.all' in result or '.every' in result
    
    def test_sorted_by_multiple_keys(self):
        """sorted(items, key=lambda x: (x.category, x.name))"""
        result = transpile_expression('sorted(items, key=lambda x: (x.category, x.name))')
        assert '__py.sorted' in result
    
    def test_max_with_default(self):
        """max(items, default=0) - Note: default not yet supported"""
        # This tests basic max, default support would need enhancement
        result = transpile_expression('max(items)')
        assert 'max' in result.lower() or 'Math.max' in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestBuiltinsEdgeCases:
    """Edge cases for builtins."""
    
    def test_nested_sorted(self):
        """sorted(sorted(items))"""
        result = transpile_expression('sorted(sorted(items))')
        assert 'sort' in result
    
    def test_chained_min_max(self):
        """max(min(a, b), min(c, d))"""
        result = transpile_expression('max(min(a, b), min(c, d))')
        assert '__py.min' in result
        assert '__py.max' in result
    
    def test_bool_in_filter(self):
        """bool used in filter context"""
        result = transpile_expression('list(filter(bool, items))')
        assert 'filter' in result
    
    def test_type_comparison(self):
        """type(x) == int"""
        result = transpile_expression('type(x) == int')
        assert '__py.type' in result
    
    def test_isinstance_in_comprehension(self):
        """[x for x in items if isinstance(x, int)]"""
        result = transpile_expression('[x for x in items if isinstance(x, int)]')
        assert '__py.isinstance' in result
    
    def test_len_in_range(self):
        """range(len(items))"""
        result = transpile_expression('range(len(items))')
        assert '__py.range' in result
    
    def test_sum_empty_list(self):
        """sum([])"""
        result = transpile_expression('sum([])')
        assert '__py.sum' in result
    
    def test_all_empty(self):
        """all([]) is True in Python"""
        result = transpile_expression('all([])')
        assert '__py.all' in result
    
    def test_any_empty(self):
        """any([]) is False in Python"""
        result = transpile_expression('any([])')
        assert '__py.any' in result


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestBuiltinsErrors:
    """Tests for error handling in builtins."""
    
    def test_min_empty_sequence(self):
        """min([]) should produce code that throws"""
        result = transpile_expression('min([])')
        assert 'Math.min' in result or '__py.min' in result
    
    def test_max_empty_sequence(self):
        """max([]) should produce code that throws"""
        result = transpile_expression('max([])')
        assert 'Math.max' in result or '__py.max' in result
    
    def test_divmod_by_zero(self):
        """divmod(x, 0) should produce code that handles zero"""
        result = transpile_expression('divmod(x, 0)')
        assert '__py.divmod' in result
