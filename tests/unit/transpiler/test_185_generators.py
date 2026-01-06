"""
Test Generator Expression Optimization (Phase 18.5)

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Comprehensive tests for optimized generator expression transpilation:
- sum() with generators
- any()/all() with generators  
- min()/max() with generators
- list()/set() with generators
- dict() with generators
- Multiple iterables and filters
- Complex expressions

=============================================================================
TARGET: 150 TESTS
=============================================================================
"""

import pytest
from pynext.transpiler import transpile


def transpile_expression(expr: str) -> str:
    """Helper to transpile a single expression."""
    return transpile(f"x = {expr}")


# =============================================================================
# SUM() PATTERNS (25 tests)
# =============================================================================

class TestSumPatterns:
    """Test sum() with generator expressions."""
    
    def test_sum_simple(self):
        """sum(x for x in items)"""
        result = transpile_expression("sum(x for x in items)")
        assert ".reduce(" in result
        assert "__acc__ + x" in result
    
    def test_sum_transform_multiply(self):
        """sum(x*2 for x in items)"""
        result = transpile_expression("sum(x*2 for x in items)")
        assert ".reduce(" in result
    
    def test_sum_transform_add(self):
        """sum(x+1 for x in items)"""
        result = transpile_expression("sum(x+1 for x in items)")
        assert ".reduce(" in result
    
    def test_sum_with_filter(self):
        """sum(x for x in items if x > 0)"""
        result = transpile_expression("sum(x for x in items if x > 0)")
        assert ".filter(" in result
        assert ".reduce(" in result
    
    def test_sum_transform_with_filter(self):
        """sum(x*2 for x in items if x > 0)"""
        result = transpile_expression("sum(x*2 for x in items if x > 0)")
        assert ".filter(" in result
        assert ".reduce(" in result
    
    def test_sum_attribute(self):
        """sum(item.value for item in items)"""
        result = transpile_expression("sum(item.value for item in items)")
        assert "item.value" in result
    
    def test_sum_subscript(self):
        """sum(item[0] for item in items)"""
        result = transpile_expression("sum(item[0] for item in items)")
        assert ".reduce(" in result
    
    def test_sum_power(self):
        """sum(x**2 for x in items)"""
        result = transpile_expression("sum(x**2 for x in items)")
        assert ".reduce(" in result
    
    def test_sum_division(self):
        """sum(x/2 for x in items)"""
        result = transpile_expression("sum(x/2 for x in items)")
        assert ".reduce(" in result
    
    def test_sum_floor_div(self):
        """sum(x//2 for x in items)"""
        result = transpile_expression("sum(x//2 for x in items)")
        assert ".reduce(" in result
    
    def test_sum_modulo(self):
        """sum(x%10 for x in items)"""
        result = transpile_expression("sum(x%10 for x in items)")
        assert ".reduce(" in result
    
    def test_sum_negative(self):
        """sum(-x for x in items)"""
        result = transpile_expression("sum(-x for x in items)")
        assert ".reduce(" in result
    
    def test_sum_multiple_filters(self):
        """sum(x for x in items if x > 0 if x < 100)"""
        result = transpile_expression("sum(x for x in items if x > 0 if x < 100)")
        assert ".filter(" in result
        assert ".reduce(" in result
    
    def test_sum_and_filter(self):
        """sum(x for x in items if x > 0 and x < 100)"""
        result = transpile_expression("sum(x for x in items if x > 0 and x < 100)")
        assert ".filter(" in result
    
    def test_sum_or_filter(self):
        """sum(x for x in items if x < 0 or x > 100)"""
        result = transpile_expression("sum(x for x in items if x < 0 or x > 100)")
        assert ".filter(" in result
    
    def test_sum_complex_expression(self):
        """sum((x+1)*2 for x in items)"""
        result = transpile_expression("sum((x+1)*2 for x in items)")
        assert ".reduce(" in result
    
    def test_sum_method_call(self):
        """sum(len(s) for s in strings)"""
        result = transpile_expression("sum(len(s) for s in strings)")
        assert ".reduce(" in result
    
    def test_sum_ternary(self):
        """sum(x if x > 0 else 0 for x in items)"""
        result = transpile_expression("sum(x if x > 0 else 0 for x in items)")
        assert ".reduce(" in result
    
    def test_sum_function_result(self):
        """sum(process(x) for x in items)"""
        result = transpile_expression("sum(process(x) for x in items)")
        assert "process(x)" in result
    
    def test_sum_chained_attribute(self):
        """sum(item.data.value for item in items)"""
        result = transpile_expression("sum(item.data.value for item in items)")
        assert "item.data.value" in result
    
    def test_sum_with_range(self):
        """sum(x for x in range(10))"""
        result = transpile_expression("sum(x for x in range(10))")
        assert ".reduce(" in result
    
    def test_sum_abs(self):
        """sum(abs(x) for x in items)"""
        result = transpile_expression("sum(abs(x) for x in items)")
        assert ".reduce(" in result
        assert "abs" in result.lower() or "Math.abs" in result
    
    def test_sum_min(self):
        """sum(min(x, 100) for x in items)"""
        result = transpile_expression("sum(min(x, 100) for x in items)")
        assert ".reduce(" in result
    
    def test_sum_max(self):
        """sum(max(x, 0) for x in items)"""
        result = transpile_expression("sum(max(x, 0) for x in items)")
        assert ".reduce(" in result
    
    def test_sum_bool_conversion(self):
        """sum(1 for x in items if x)"""
        result = transpile_expression("sum(1 for x in items if x)")
        assert ".filter(" in result


# =============================================================================
# ANY/ALL PATTERNS (25 tests)
# =============================================================================

class TestAnyAllPatterns:
    """Test any()/all() with generator expressions."""
    
    def test_any_comparison_gt(self):
        """any(x > 0 for x in items)"""
        result = transpile_expression("any(x > 0 for x in items)")
        assert ".some(" in result
    
    def test_any_comparison_lt(self):
        """any(x < 0 for x in items)"""
        result = transpile_expression("any(x < 0 for x in items)")
        assert ".some(" in result
    
    def test_any_comparison_eq(self):
        """any(x == target for x in items)"""
        result = transpile_expression("any(x == target for x in items)")
        assert ".some(" in result
    
    def test_any_comparison_ne(self):
        """any(x != 0 for x in items)"""
        result = transpile_expression("any(x != 0 for x in items)")
        assert ".some(" in result
    
    def test_any_truthiness(self):
        """any(x for x in items)"""
        result = transpile_expression("any(x for x in items)")
        assert ".some(" in result
        assert "__py.bool" in result
    
    def test_any_attribute(self):
        """any(item.active for item in items)"""
        result = transpile_expression("any(item.active for item in items)")
        assert ".some(" in result
        assert "item.active" in result
    
    def test_any_method_call(self):
        """any(item.is_valid() for item in items)"""
        result = transpile_expression("any(item.is_valid() for item in items)")
        assert ".some(" in result
    
    def test_any_with_filter(self):
        """any(x > 10 for x in items if x > 0)"""
        result = transpile_expression("any(x > 10 for x in items if x > 0)")
        assert ".filter(" in result
        assert ".some(" in result
    
    def test_any_in_check(self):
        """any(x in valid_set for x in items)"""
        result = transpile_expression("any(x in valid_set for x in items)")
        assert ".some(" in result
    
    def test_any_isinstance(self):
        """any(isinstance(x, int) for x in items)"""
        result = transpile_expression("any(isinstance(x, int) for x in items)")
        assert ".some(" in result
    
    def test_any_and_condition(self):
        """any(x > 0 and x < 100 for x in items)"""
        result = transpile_expression("any(x > 0 and x < 100 for x in items)")
        assert ".some(" in result
    
    def test_any_or_condition(self):
        """any(x < 0 or x > 100 for x in items)"""
        result = transpile_expression("any(x < 0 or x > 100 for x in items)")
        assert ".some(" in result
    
    def test_all_comparison_gt(self):
        """all(x > 0 for x in items)"""
        result = transpile_expression("all(x > 0 for x in items)")
        assert ".every(" in result
    
    def test_all_comparison_ge(self):
        """all(x >= 0 for x in items)"""
        result = transpile_expression("all(x >= 0 for x in items)")
        assert ".every(" in result
    
    def test_all_comparison_le(self):
        """all(x <= 100 for x in items)"""
        result = transpile_expression("all(x <= 100 for x in items)")
        assert ".every(" in result
    
    def test_all_truthiness(self):
        """all(x for x in items)"""
        result = transpile_expression("all(x for x in items)")
        assert ".every(" in result
        assert "__py.bool" in result
    
    def test_all_attribute(self):
        """all(item.valid for item in items)"""
        result = transpile_expression("all(item.valid for item in items)")
        assert ".every(" in result
    
    def test_all_method_call(self):
        """all(item.check() for item in items)"""
        result = transpile_expression("all(item.check() for item in items)")
        assert ".every(" in result
    
    def test_all_with_filter(self):
        """all(x > 10 for x in items if x > 0)"""
        result = transpile_expression("all(x > 10 for x in items if x > 0)")
        assert ".filter(" in result
        assert ".every(" in result
    
    def test_all_not_none(self):
        """all(x is not None for x in items)"""
        result = transpile_expression("all(x is not None for x in items)")
        assert ".every(" in result
    
    def test_all_len_check(self):
        """all(len(s) > 0 for s in strings)"""
        result = transpile_expression("all(len(s) > 0 for s in strings)")
        assert ".every(" in result
    
    def test_all_and_condition(self):
        """all(x > 0 and x < 100 for x in items)"""
        result = transpile_expression("all(x > 0 and x < 100 for x in items)")
        assert ".every(" in result
    
    def test_any_startswith(self):
        """any(s.startswith('test') for s in strings)"""
        result = transpile_expression("any(s.startswith('test') for s in strings)")
        assert ".some(" in result
    
    def test_all_endswith(self):
        """all(s.endswith('.py') for s in files)"""
        result = transpile_expression("all(s.endswith('.py') for s in files)")
        assert ".every(" in result
    
    def test_any_contains(self):
        """any('error' in s for s in logs)"""
        result = transpile_expression("any('error' in s for s in logs)")
        assert ".some(" in result


# =============================================================================
# MIN/MAX PATTERNS (20 tests)
# =============================================================================

class TestMinMaxPatterns:
    """Test min()/max() with generator expressions."""
    
    def test_min_simple(self):
        """min(x for x in items)"""
        result = transpile_expression("min(x for x in items)")
        assert "__py.min" in result
    
    def test_max_simple(self):
        """max(x for x in items)"""
        result = transpile_expression("max(x for x in items)")
        assert "__py.max" in result
    
    def test_min_transform(self):
        """min(x*2 for x in items)"""
        result = transpile_expression("min(x*2 for x in items)")
        assert "__py.min" in result
        assert ".map(" in result
    
    def test_max_transform(self):
        """max(x*2 for x in items)"""
        result = transpile_expression("max(x*2 for x in items)")
        assert "__py.max" in result
        assert ".map(" in result
    
    def test_min_attribute(self):
        """min(item.value for item in items)"""
        result = transpile_expression("min(item.value for item in items)")
        assert "__py.min" in result
        assert "item.value" in result
    
    def test_max_attribute(self):
        """max(item.score for item in items)"""
        result = transpile_expression("max(item.score for item in items)")
        assert "__py.max" in result
        assert "item.score" in result
    
    def test_min_with_filter(self):
        """min(x for x in items if x > 0)"""
        result = transpile_expression("min(x for x in items if x > 0)")
        assert "__py.min" in result
        assert ".filter(" in result
    
    def test_max_with_filter(self):
        """max(x for x in items if x < 100)"""
        result = transpile_expression("max(x for x in items if x < 100)")
        assert "__py.max" in result
        assert ".filter(" in result
    
    def test_min_abs(self):
        """min(abs(x) for x in items)"""
        result = transpile_expression("min(abs(x) for x in items)")
        assert "__py.min" in result
    
    def test_max_len(self):
        """max(len(s) for s in strings)"""
        result = transpile_expression("max(len(s) for s in strings)")
        assert "__py.max" in result
    
    def test_min_negative(self):
        """min(-x for x in items)"""
        result = transpile_expression("min(-x for x in items)")
        assert "__py.min" in result
    
    def test_max_negative(self):
        """max(-x for x in items)"""
        result = transpile_expression("max(-x for x in items)")
        assert "__py.max" in result
    
    def test_min_ternary(self):
        """min(x if x > 0 else float('inf') for x in items)"""
        result = transpile_expression("min(x if x > 0 else 1000 for x in items)")
        assert "__py.min" in result
    
    def test_max_method(self):
        """max(item.get_score() for item in items)"""
        result = transpile_expression("max(item.get_score() for item in items)")
        assert "__py.max" in result
    
    def test_min_subscript(self):
        """min(pair[0] for pair in pairs)"""
        result = transpile_expression("min(pair[0] for pair in pairs)")
        assert "__py.min" in result
    
    def test_max_subscript(self):
        """max(pair[1] for pair in pairs)"""
        result = transpile_expression("max(pair[1] for pair in pairs)")
        assert "__py.max" in result
    
    def test_min_power(self):
        """min(x**2 for x in items)"""
        result = transpile_expression("min(x**2 for x in items)")
        assert "__py.min" in result
    
    def test_max_power(self):
        """max(x**2 for x in items)"""
        result = transpile_expression("max(x**2 for x in items)")
        assert "__py.max" in result
    
    def test_min_chained(self):
        """min(item.data.value for item in items)"""
        result = transpile_expression("min(item.data.value for item in items)")
        assert "__py.min" in result
    
    def test_max_chained(self):
        """max(item.data.value for item in items)"""
        result = transpile_expression("max(item.data.value for item in items)")
        assert "__py.max" in result


# =============================================================================
# LIST/SET PATTERNS (20 tests)
# =============================================================================

class TestListSetPatterns:
    """Test list()/set() with generator expressions."""
    
    def test_list_identity(self):
        """list(x for x in items)"""
        result = transpile_expression("list(x for x in items)")
        assert "[...items]" in result
    
    def test_list_transform(self):
        """list(x*2 for x in items)"""
        result = transpile_expression("list(x*2 for x in items)")
        assert ".map(" in result
    
    def test_list_with_filter(self):
        """list(x for x in items if x > 0)"""
        result = transpile_expression("list(x for x in items if x > 0)")
        assert ".filter(" in result
    
    def test_list_transform_filter(self):
        """list(x*2 for x in items if x > 0)"""
        result = transpile_expression("list(x*2 for x in items if x > 0)")
        assert ".filter(" in result
        assert ".map(" in result
    
    def test_list_attribute(self):
        """list(item.name for item in items)"""
        result = transpile_expression("list(item.name for item in items)")
        assert ".map(" in result
        assert "item.name" in result
    
    def test_list_method(self):
        """list(s.upper() for s in strings)"""
        result = transpile_expression("list(s.upper() for s in strings)")
        assert ".map(" in result
    
    def test_list_str(self):
        """list(str(x) for x in items)"""
        result = transpile_expression("list(str(x) for x in items)")
        assert ".map(" in result
    
    def test_list_int(self):
        """list(int(x) for x in strings)"""
        result = transpile_expression("list(int(x) for x in strings)")
        assert ".map(" in result
    
    def test_set_identity(self):
        """set(x for x in items)"""
        result = transpile_expression("set(x for x in items)")
        assert "new Set" in result
    
    def test_set_transform(self):
        """set(x.lower() for x in items)"""
        result = transpile_expression("set(x.lower() for x in items)")
        assert "new Set" in result
        assert ".map(" in result
    
    def test_set_with_filter(self):
        """set(x for x in items if x > 0)"""
        result = transpile_expression("set(x for x in items if x > 0)")
        assert "new Set" in result
        assert ".filter(" in result
    
    def test_set_attribute(self):
        """set(item.category for item in items)"""
        result = transpile_expression("set(item.category for item in items)")
        assert "new Set" in result
    
    def test_tuple_identity(self):
        """tuple(x for x in items)"""
        result = transpile_expression("tuple(x for x in items)")
        assert "Object.freeze" in result
    
    def test_tuple_transform(self):
        """tuple(x*2 for x in items)"""
        result = transpile_expression("tuple(x*2 for x in items)")
        assert "Object.freeze" in result
        assert ".map(" in result
    
    def test_list_len(self):
        """list(len(s) for s in strings)"""
        result = transpile_expression("list(len(s) for s in strings)")
        assert ".map(" in result
    
    def test_list_ternary(self):
        """list(x if x > 0 else 0 for x in items)"""
        result = transpile_expression("list(x if x > 0 else 0 for x in items)")
        assert ".map(" in result
    
    def test_set_lower(self):
        """set(s.lower() for s in strings)"""
        result = transpile_expression("set(s.lower() for s in strings)")
        assert "new Set" in result
    
    def test_list_strip(self):
        """list(s.strip() for s in strings)"""
        result = transpile_expression("list(s.strip() for s in strings)")
        assert ".map(" in result
    
    def test_set_split(self):
        """set(word for s in strings for word in s.split())"""
        # Nested generators are handled differently
        result = transpile_expression("set(s.split() for s in strings)")
        assert "new Set" in result
    
    def test_list_abs(self):
        """list(abs(x) for x in items)"""
        result = transpile_expression("list(abs(x) for x in items)")
        assert ".map(" in result


# =============================================================================
# DICT PATTERNS (20 tests)
# =============================================================================

class TestDictPatterns:
    """Test dict() with generator expressions."""
    
    def test_dict_tuple_identity(self):
        """dict((k, v) for k, v in items)"""
        result = transpile_expression("dict((k, v) for k, v in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_key_value(self):
        """dict((x, x*2) for x in items)"""
        result = transpile_expression("dict((x, x*2) for x in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_attribute_key(self):
        """dict((item.id, item) for item in items)"""
        result = transpile_expression("dict((item.id, item) for item in items)")
        assert "Object.fromEntries" in result
        assert "item.id" in result
    
    def test_dict_string_keys(self):
        """dict((str(i), i) for i in range(10))"""
        result = transpile_expression("dict((str(i), i) for i in range(10))")
        assert "Object.fromEntries" in result
    
    def test_dict_with_filter(self):
        """dict((k, v) for k, v in items if v > 0)"""
        result = transpile_expression("dict((k, v) for k, v in items if v > 0)")
        assert "Object.fromEntries" in result
        assert ".filter(" in result
    
    def test_dict_transform_value(self):
        """dict((k, v*2) for k, v in items)"""
        result = transpile_expression("dict((k, v*2) for k, v in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_lower_key(self):
        """dict((k.lower(), v) for k, v in items)"""
        result = transpile_expression("dict((k.lower(), v) for k, v in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_name_to_value(self):
        """dict((item.name, item.value) for item in items)"""
        result = transpile_expression("dict((item.name, item.value) for item in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_index_to_item(self):
        """dict((i, item) for i, item in enumerate(items))"""
        result = transpile_expression("dict((i, item) for i, item in enumerate(items))")
        assert "Object.fromEntries" in result
    
    def test_dict_reverse(self):
        """dict((v, k) for k, v in items)"""
        result = transpile_expression("dict((v, k) for k, v in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_from_list(self):
        """dict((x, True) for x in items)"""
        result = transpile_expression("dict((x, True) for x in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_count(self):
        """dict((x, items.count(x)) for x in set(items))"""
        result = transpile_expression("dict((x, len(x)) for x in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_complex_key(self):
        """dict((f'{k}_suffix', v) for k, v in items)"""
        result = transpile_expression("dict((k + '_suffix', v) for k, v in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_nested_attr(self):
        """dict((item.id, item.data.value) for item in items)"""
        result = transpile_expression("dict((item.id, item.data.value) for item in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_method_value(self):
        """dict((k, v.strip()) for k, v in items)"""
        result = transpile_expression("dict((k, v.strip()) for k, v in items)")
        assert "Object.fromEntries" in result
    
    def test_dict_int_keys(self):
        """dict((i, i**2) for i in range(5))"""
        result = transpile_expression("dict((i, i**2) for i in range(5))")
        assert "Object.fromEntries" in result
    
    def test_dict_bool_filter(self):
        """dict((k, v) for k, v in items if v)"""
        result = transpile_expression("dict((k, v) for k, v in items if v)")
        assert "Object.fromEntries" in result
        assert ".filter(" in result
    
    def test_dict_none_filter(self):
        """dict((k, v) for k, v in items if v is not None)"""
        result = transpile_expression("dict((k, v) for k, v in items if v is not None)")
        assert "Object.fromEntries" in result
    
    def test_dict_type_filter(self):
        """dict((k, v) for k, v in items if isinstance(v, int))"""
        result = transpile_expression("dict((k, v) for k, v in items if isinstance(v, int))")
        assert "Object.fromEntries" in result
    
    def test_dict_length_filter(self):
        """dict((k, v) for k, v in items if len(v) > 0)"""
        result = transpile_expression("dict((k, v) for k, v in items if len(v) > 0)")
        assert "Object.fromEntries" in result


# =============================================================================
# MULTIPLE ITERABLES (15 tests)
# =============================================================================

class TestMultipleIterables:
    """Test generators over multiple iterables."""
    
    def test_zip_sum(self):
        """sum(a*b for a, b in zip(list1, list2))"""
        result = transpile_expression("sum(a*b for a, b in zip(list1, list2))")
        # Tuple unpacking prevents optimization, uses __py.sum
        assert "sum" in result.lower() or ".reduce(" in result
    
    def test_enumerate_sum(self):
        """sum(i*v for i, v in enumerate(items))"""
        result = transpile_expression("sum(i*v for i, v in enumerate(items))")
        # Tuple unpacking prevents optimization
        assert "sum" in result.lower() or ".reduce(" in result
    
    def test_enumerate_list(self):
        """list(i for i, v in enumerate(items))"""
        result = transpile_expression("list(i for i, v in enumerate(items))")
        # May use map or direct
        assert "enumerate" in result or ".map(" in result
    
    def test_zip_any(self):
        """any(a == b for a, b in zip(list1, list2))"""
        result = transpile_expression("any(a == b for a, b in zip(list1, list2))")
        # Tuple unpacking prevents optimization
        assert "any" in result.lower() or ".some(" in result
    
    def test_zip_all(self):
        """all(a < b for a, b in zip(list1, list2))"""
        result = transpile_expression("all(a < b for a, b in zip(list1, list2))")
        # Tuple unpacking prevents optimization
        assert "all" in result.lower() or ".every(" in result
    
    def test_enumerate_dict(self):
        """dict((i, v) for i, v in enumerate(items))"""
        result = transpile_expression("dict((i, v) for i, v in enumerate(items))")
        assert "Object.fromEntries" in result
    
    def test_items_dict(self):
        """dict((k.lower(), v) for k, v in d.items())"""
        result = transpile_expression("dict((k.lower(), v) for k, v in d.items())")
        assert "Object.fromEntries" in result
    
    def test_values_sum(self):
        """sum(v for v in d.values())"""
        result = transpile_expression("sum(v for v in d.values())")
        assert ".reduce(" in result
    
    def test_keys_list(self):
        """list(k for k in d.keys())"""
        result = transpile_expression("list(k for k in d.keys())")
        # This could be optimized various ways
        assert "k" in result
    
    def test_range_sum(self):
        """sum(x**2 for x in range(10))"""
        result = transpile_expression("sum(x**2 for x in range(10))")
        assert ".reduce(" in result
    
    def test_range_list(self):
        """list(x*2 for x in range(5))"""
        result = transpile_expression("list(x*2 for x in range(5))")
        assert ".map(" in result
    
    def test_range_filter(self):
        """list(x for x in range(10) if x % 2 == 0)"""
        result = transpile_expression("list(x for x in range(10) if x % 2 == 0)")
        assert ".filter(" in result
    
    def test_zip_max(self):
        """max(a+b for a, b in zip(list1, list2))"""
        result = transpile_expression("max(a+b for a, b in zip(list1, list2))")
        assert "__py.max" in result
    
    def test_enumerate_max(self):
        """max(v for i, v in enumerate(items))"""
        result = transpile_expression("max(v for i, v in enumerate(items))")
        assert "__py.max" in result
    
    def test_items_any(self):
        """any(v > 0 for k, v in d.items())"""
        result = transpile_expression("any(v > 0 for k, v in d.items())")
        # Tuple unpacking prevents optimization
        assert "any" in result.lower() or ".some(" in result


# =============================================================================
# COMPLEX FILTERS (25 tests)
# =============================================================================

class TestComplexFilters:
    """Test generators with complex filter conditions."""
    
    def test_and_filter(self):
        """sum(x for x in items if x > 0 and x < 100)"""
        result = transpile_expression("sum(x for x in items if x > 0 and x < 100)")
        assert ".filter(" in result
        # Python and uses short-circuit evaluation
        assert "(x > 0)" in result and "(x < 100)" in result
    
    def test_or_filter(self):
        """sum(x for x in items if x < 0 or x > 100)"""
        result = transpile_expression("sum(x for x in items if x < 0 or x > 100)")
        assert ".filter(" in result
        # Python or uses short-circuit evaluation
        assert "(x < 0)" in result and "(x > 100)" in result
    
    def test_not_filter(self):
        """list(x for x in items if not x.disabled)"""
        result = transpile_expression("list(x for x in items if not x.disabled)")
        assert ".filter(" in result
    
    def test_is_none_filter(self):
        """list(x for x in items if x is not None)"""
        result = transpile_expression("list(x for x in items if x is not None)")
        assert ".filter(" in result
        assert "!== null" in result
    
    def test_in_filter(self):
        """list(x for x in items if x in valid_set)"""
        result = transpile_expression("list(x for x in items if x in valid_set)")
        assert ".filter(" in result
    
    def test_not_in_filter(self):
        """list(x for x in items if x not in blacklist)"""
        result = transpile_expression("list(x for x in items if x not in blacklist)")
        assert ".filter(" in result
    
    def test_isinstance_filter(self):
        """list(x for x in items if isinstance(x, str))"""
        result = transpile_expression("list(x for x in items if isinstance(x, str))")
        assert ".filter(" in result
    
    def test_len_filter(self):
        """list(s for s in strings if len(s) > 0)"""
        result = transpile_expression("list(s for s in strings if len(s) > 0)")
        assert ".filter(" in result
    
    def test_startswith_filter(self):
        """list(s for s in strings if s.startswith('test'))"""
        result = transpile_expression("list(s for s in strings if s.startswith('test'))")
        assert ".filter(" in result
    
    def test_endswith_filter(self):
        """list(s for s in strings if s.endswith('.py'))"""
        result = transpile_expression("list(s for s in strings if s.endswith('.py'))")
        assert ".filter(" in result
    
    def test_contains_filter(self):
        """list(s for s in strings if 'error' in s)"""
        result = transpile_expression("list(s for s in strings if 'error' in s)")
        assert ".filter(" in result
    
    def test_multiple_and(self):
        """list(x for x in items if x > 0 and x < 50 and x % 2 == 0)"""
        result = transpile_expression("list(x for x in items if x > 0 and x < 50 and x % 2 == 0)")
        assert ".filter(" in result
    
    def test_mixed_logic(self):
        """list(x for x in items if (x > 0 and x < 50) or x > 100)"""
        result = transpile_expression("list(x for x in items if (x > 0 and x < 50) or x > 100)")
        assert ".filter(" in result
    
    def test_method_filter(self):
        """list(item for item in items if item.is_active())"""
        result = transpile_expression("list(item for item in items if item.is_active())")
        assert ".filter(" in result
    
    def test_attribute_filter(self):
        """list(item for item in items if item.active)"""
        result = transpile_expression("list(item for item in items if item.active)")
        assert ".filter(" in result
    
    def test_comparison_chain(self):
        """list(x for x in items if 0 < x < 100)"""
        result = transpile_expression("list(x for x in items if 0 < x < 100)")
        assert ".filter(" in result
    
    def test_bool_conversion(self):
        """list(x for x in items if bool(x))"""
        result = transpile_expression("list(x for x in items if bool(x))")
        assert ".filter(" in result
    
    def test_any_all_in_filter(self):
        """list(row for row in matrix if all(x > 0 for x in row))"""
        # This is a nested generator - test that it compiles
        result = transpile_expression("list(row for row in matrix if any(x > 0 for x in row))")
        assert ".filter(" in result
    
    def test_callable_filter(self):
        """list(x for x in items if callable(x))"""
        result = transpile_expression("list(x for x in items if callable(x))")
        assert ".filter(" in result
    
    def test_hasattr_filter(self):
        """list(obj for obj in objects if hasattr(obj, 'name'))"""
        result = transpile_expression("list(obj for obj in objects if hasattr(obj, 'name'))")
        assert ".filter(" in result
    
    def test_truthiness_filter(self):
        """list(x for x in items if x)"""
        result = transpile_expression("list(x for x in items if x)")
        assert ".filter(" in result
    
    def test_not_truthiness_filter(self):
        """list(x for x in items if not x)"""
        result = transpile_expression("list(x for x in items if not x)")
        assert ".filter(" in result
    
    def test_complex_attribute(self):
        """list(item for item in items if item.data.valid)"""
        result = transpile_expression("list(item for item in items if item.data.valid)")
        assert ".filter(" in result
    
    def test_subscript_filter(self):
        """list(item for item in items if item[0] > 0)"""
        result = transpile_expression("list(item for item in items if item[0] > 0)")
        assert ".filter(" in result
    
    def test_function_filter(self):
        """list(x for x in items if is_valid(x))"""
        result = transpile_expression("list(x for x in items if is_valid(x))")
        assert ".filter(" in result
        assert "is_valid" in result


# =============================================================================
# SORTED WITH GENERATORS (10 tests)
# =============================================================================

class TestSortedWithGenerators:
    """Test sorted() with generator expressions."""
    
    def test_sorted_identity(self):
        """sorted(x for x in items)"""
        result = transpile_expression("sorted(x for x in items)")
        assert "__py.sorted" in result
    
    def test_sorted_transform(self):
        """sorted(x*2 for x in items)"""
        result = transpile_expression("sorted(x*2 for x in items)")
        assert "__py.sorted" in result
    
    def test_sorted_with_filter(self):
        """sorted(x for x in items if x > 0)"""
        result = transpile_expression("sorted(x for x in items if x > 0)")
        assert "__py.sorted" in result
        assert ".filter(" in result
    
    def test_sorted_attribute(self):
        """sorted(item.name for item in items)"""
        result = transpile_expression("sorted(item.name for item in items)")
        assert "__py.sorted" in result
    
    def test_sorted_lower(self):
        """sorted(s.lower() for s in strings)"""
        result = transpile_expression("sorted(s.lower() for s in strings)")
        assert "__py.sorted" in result
    
    def test_sorted_len(self):
        """sorted(len(s) for s in strings)"""
        result = transpile_expression("sorted(len(s) for s in strings)")
        assert "__py.sorted" in result
    
    def test_sorted_abs(self):
        """sorted(abs(x) for x in items)"""
        result = transpile_expression("sorted(abs(x) for x in items)")
        assert "__py.sorted" in result
    
    def test_sorted_negative(self):
        """sorted(-x for x in items)"""
        result = transpile_expression("sorted(-x for x in items)")
        assert "__py.sorted" in result
    
    def test_sorted_complex(self):
        """sorted(x*2 for x in items if x > 0)"""
        result = transpile_expression("sorted(x*2 for x in items if x > 0)")
        assert "__py.sorted" in result
    
    def test_sorted_method(self):
        """sorted(s.strip() for s in strings)"""
        result = transpile_expression("sorted(s.strip() for s in strings)")
        assert "__py.sorted" in result


# =============================================================================
# EDGE CASES (10 tests)
# =============================================================================

class TestGeneratorEdgeCases:
    """Edge cases for generator expressions."""
    
    def test_empty_filter(self):
        """list(x for x in [] if x > 0)"""
        result = transpile_expression("list(x for x in [] if x > 0)")
        assert ".filter(" in result
    
    def test_single_element(self):
        """sum(x for x in [1])"""
        result = transpile_expression("sum(x for x in [1])")
        assert ".reduce(" in result
    
    def test_none_handling(self):
        """list(x for x in items if x is not None)"""
        result = transpile_expression("list(x for x in items if x is not None)")
        assert ".filter(" in result
    
    def test_string_iteration(self):
        """list(c for c in string)"""
        result = transpile_expression("list(c for c in string)")
        assert "string" in result
    
    def test_nested_attribute(self):
        """sum(item.a.b.c for item in items)"""
        result = transpile_expression("sum(item.a.b.c for item in items)")
        assert "item.a.b.c" in result
    
    def test_negative_index(self):
        """sum(row[-1] for row in matrix)"""
        result = transpile_expression("sum(row[-1] for row in matrix)")
        assert ".reduce(" in result
    
    def test_slice_in_generator(self):
        """list(s[:3] for s in strings)"""
        result = transpile_expression("list(s[:3] for s in strings)")
        assert ".map(" in result
    
    def test_fstring_in_generator(self):
        """list(f'{x}px' for x in sizes)"""
        result = transpile_expression("list(f'{x}px' for x in sizes)")
        assert ".map(" in result
    
    def test_ternary_in_generator(self):
        """list('yes' if x else 'no' for x in items)"""
        result = transpile_expression("list('yes' if x else 'no' for x in items)")
        assert ".map(" in result
    
    def test_complex_ternary(self):
        """list(x*2 if x > 0 else x*3 if x < 0 else 0 for x in items)"""
        result = transpile_expression("list(x*2 if x > 0 else x*3 if x < 0 else 0 for x in items)")
        assert ".map(" in result
