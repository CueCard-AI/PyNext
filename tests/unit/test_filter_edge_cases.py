"""
Test Phase 7.5: Filter Edge Cases.

These tests verify edge cases and error handling.
"""

import pytest
from datetime import datetime, timedelta

from pynext.db.relationships.conditions import (
    Condition,
    eq, ne, gt, gte, lt, lte,
    like, ilike, not_like,
    is_in, not_in, is_null,
    normalize_condition,
    normalize_conditions,
)
from pynext.db.relationships.filter import (
    RelationshipFilter,
    parse_filter,
)
from pynext.db.relationships.core import (
    has_many,
    has_one,
    belongs_to,
    many_to_many,
)


# =============================================================================
# Test Condition Validation Edge Cases
# =============================================================================

class TestConditionValidation:
    """Test condition validation edge cases."""
    
    def test_whitespace_field_name(self):
        """Field name with only spaces should fail."""
        with pytest.raises(ValueError) as exc:
            Condition("   ", "=", "value")
        assert "cannot be empty" in str(exc.value)
    
    def test_operator_with_spaces_works(self):
        """Operator with surrounding spaces is normalized."""
        c = Condition("field", " LIKE ", "%x%")
        assert c.operator == "LIKE"
    
    def test_unicode_field_name(self):
        """Unicode in field name."""
        c = eq("名前", "value")  # Japanese for "name"
        assert c.field == "名前"
    
    def test_unicode_value(self):
        """Unicode in value."""
        c = eq("name", "日本語")  # Japanese
        assert c.value == "日本語"
    
    def test_very_long_field_name(self):
        """Very long field name."""
        long_name = "a" * 1000
        c = eq(long_name, "value")
        assert len(c.field) == 1000
    
    def test_very_long_value(self):
        """Very long string value."""
        long_value = "x" * 10000
        c = eq("field", long_value)
        assert len(c.value) == 10000
    
    def test_special_chars_in_field(self):
        """Special characters in field name."""
        c = eq("field_with_underscore_123", "value")
        assert c.field == "field_with_underscore_123"
    
    def test_newline_in_value(self):
        """Newline in string value."""
        c = eq("field", "line1\nline2")
        assert "\n" in c.value
    
    def test_tab_in_value(self):
        """Tab in string value."""
        c = eq("field", "col1\tcol2")
        assert "\t" in c.value


# =============================================================================
# Test is_in Edge Cases
# =============================================================================

class TestIsInEdgeCases:
    """Test is_in function edge cases."""
    
    def test_is_in_single_item(self):
        """IN with single item list."""
        c = is_in("status", ["active"])
        assert c.value == ["active"]
    
    def test_is_in_many_items(self):
        """IN with many items."""
        values = list(range(100))
        c = is_in("id", values)
        assert len(c.value) == 100
    
    def test_is_in_mixed_types(self):
        """IN with mixed types in list."""
        c = is_in("value", [1, "two", 3.0, True, None])
        assert len(c.value) == 5
    
    def test_is_in_nested_list(self):
        """IN with nested lists."""
        c = is_in("data", [[1, 2], [3, 4]])
        assert c.value == [[1, 2], [3, 4]]
    
    def test_is_in_with_dict_values(self):
        """IN with dict values (JSON)."""
        c = is_in("config", [{"a": 1}, {"b": 2}])
        assert len(c.value) == 2
    
    def test_not_in_empty_list(self):
        """NOT IN with empty list."""
        c = not_in("id", [])
        assert c.value == []
    
    def test_is_in_duplicate_values(self):
        """IN with duplicate values."""
        c = is_in("status", ["a", "a", "b", "b"])
        assert c.value == ["a", "a", "b", "b"]  # Preserves duplicates


# =============================================================================
# Test like Pattern Edge Cases
# =============================================================================

class TestLikeEdgeCases:
    """Test LIKE pattern edge cases."""
    
    def test_like_with_percent(self):
        """LIKE with percent in value."""
        c = like("discount", "50%")
        assert c.value == "50%"
    
    def test_like_with_underscore(self):
        """LIKE with underscore (single char wildcard)."""
        c = like("code", "A_B")
        assert c.value == "A_B"
    
    def test_like_with_backslash(self):
        """LIKE with backslash."""
        c = like("path", "C:\\Users\\%")
        assert "\\" in c.value
    
    def test_like_empty_pattern(self):
        """LIKE with empty pattern."""
        c = like("field", "")
        assert c.value == ""
    
    def test_like_only_wildcards(self):
        """LIKE with only wildcards."""
        c = like("field", "%%%")
        assert c.value == "%%%"


# =============================================================================
# Test Null Edge Cases
# =============================================================================

class TestNullEdgeCases:
    """Test IS NULL edge cases."""
    
    def test_is_null_default(self):
        """is_null with default (True)."""
        c = is_null("field")
        assert c.operator == "IS NULL"
    
    def test_is_null_explicit_true(self):
        """is_null with explicit True."""
        c = is_null("field", True)
        assert c.operator == "IS NULL"
    
    def test_is_null_explicit_false(self):
        """is_null with explicit False (IS NOT NULL)."""
        c = is_null("field", False)
        assert c.operator == "IS NOT NULL"


# =============================================================================
# Test Tuple Normalization Edge Cases
# =============================================================================

class TestTupleEdgeCases:
    """Test tuple normalization edge cases."""
    
    def test_tuple_with_none_value(self):
        """Tuple with None value."""
        c = normalize_condition(("field", "=", None))
        assert c.value is None
    
    def test_tuple_with_bool_value(self):
        """Tuple with boolean value."""
        c = normalize_condition(("active", "=", True))
        assert c.value is True
    
    def test_tuple_empty_string_value(self):
        """Tuple with empty string value."""
        c = normalize_condition(("name", "!=", ""))
        assert c.value == ""
    
    def test_tuple_negative_number(self):
        """Tuple with negative number."""
        c = normalize_condition(("balance", "<", -100.50))
        assert c.value == -100.50
    
    def test_tuple_datetime_value(self):
        """Tuple with datetime value."""
        dt = datetime(2024, 12, 25, 10, 30, 0)
        c = normalize_condition(("created", ">=", dt))
        assert c.value == dt


# =============================================================================
# Test Filter List Edge Cases
# =============================================================================

class TestFilterListEdgeCases:
    """Test filter list edge cases."""
    
    def test_filter_with_duplicate_conditions(self):
        """Filter with duplicate conditions."""
        rf = RelationshipFilter([
            eq("active", True),
            eq("active", True),  # Duplicate
        ])
        assert len(rf.conditions) == 2  # Both preserved
    
    def test_filter_contradictory_conditions(self):
        """Filter with contradictory conditions (AND logic)."""
        rf = RelationshipFilter([
            eq("active", True),
            eq("active", False),  # Contradicts
        ])
        # Both preserved (AND would return empty result)
        assert len(rf.conditions) == 2
    
    def test_filter_same_field_different_ops(self):
        """Filter with same field, different operators (range)."""
        rf = RelationshipFilter([
            gte("price", 10),
            lte("price", 100),
            ne("price", 50),
        ])
        assert len(rf.conditions) == 3
    
    def test_filter_many_different_fields(self):
        """Filter with many different fields."""
        conditions = [eq(f"field_{i}", i) for i in range(50)]
        rf = RelationshipFilter(conditions)
        assert len(rf.conditions) == 50


# =============================================================================
# Test Relationship Filter Edge Cases
# =============================================================================

class TestRelationshipFilterEdgeCases:
    """Test relationship with filter edge cases."""
    
    def test_filter_accessed_multiple_times(self):
        """Filter property accessed multiple times."""
        hm = has_many("Post", filter=[eq("active", True)])
        f1 = hm.filter
        f2 = hm.filter
        f3 = hm.filter
        assert f1 is f2 is f3
    
    def test_filter_with_special_field_names(self):
        """Filter with database-reserved field names."""
        hm = has_many("Post", filter=[
            eq("select", True),
            eq("from", "table"),
            eq("where", "clause"),
        ])
        assert len(hm.filter.conditions) == 3
    
    def test_filter_with_json_path(self):
        """Filter with JSON path-like field."""
        hm = has_many("Post", filter=[
            eq("metadata.key", "value"),
        ])
        assert hm.filter.conditions[0].field == "metadata.key"


# =============================================================================
# Test Error Messages
# =============================================================================

class TestErrorMessages:
    """Test that error messages are clear and helpful."""
    
    def test_invalid_operator_error_message(self):
        """Invalid operator shows valid operators."""
        with pytest.raises(ValueError) as exc:
            Condition("field", "BADOP", "value")
        error_msg = str(exc.value)
        assert "Invalid operator" in error_msg
        assert "BADOP" in error_msg
    
    def test_empty_field_error_message(self):
        """Empty field shows clear message."""
        with pytest.raises(ValueError) as exc:
            Condition("", "=", "value")
        assert "cannot be empty" in str(exc.value)
    
    def test_is_in_non_list_error_message(self):
        """is_in with non-list shows clear message."""
        with pytest.raises(ValueError) as exc:
            is_in("field", "not a list")
        assert "requires a list" in str(exc.value)
    
    def test_tuple_wrong_size_error_message(self):
        """Tuple with wrong size shows count."""
        with pytest.raises(ValueError) as exc:
            normalize_condition(("field", "="))
        assert "3 elements" in str(exc.value)
    
    def test_invalid_condition_type_error_message(self):
        """Invalid condition type shows type."""
        with pytest.raises(ValueError) as exc:
            normalize_condition(123)
        assert "Invalid condition type" in str(exc.value)
        assert "int" in str(exc.value)


# =============================================================================
# Test Type Coercion
# =============================================================================

class TestTypeHandling:
    """Test handling of various Python types."""
    
    def test_condition_with_int(self):
        """Condition with int value."""
        c = eq("count", 42)
        assert c.value == 42
        assert isinstance(c.value, int)
    
    def test_condition_with_float(self):
        """Condition with float value."""
        c = eq("price", 19.99)
        assert c.value == 19.99
        assert isinstance(c.value, float)
    
    def test_condition_with_complex(self):
        """Condition with complex number (unusual but valid)."""
        c = eq("data", complex(1, 2))
        assert c.value == complex(1, 2)
    
    def test_condition_with_bytes(self):
        """Condition with bytes value."""
        c = eq("data", b"binary")
        assert c.value == b"binary"
    
    def test_condition_with_frozenset(self):
        """Condition with frozenset value."""
        c = eq("tags", frozenset(["a", "b"]))
        assert c.value == frozenset(["a", "b"])
    
    def test_is_in_with_generator(self):
        """is_in converts generator to list."""
        def gen():
            yield 1
            yield 2
            yield 3
        with pytest.raises(ValueError):
            # Generator is not a list/tuple/set
            is_in("id", gen())


# =============================================================================
# Test Memory and Performance Edge Cases
# =============================================================================

class TestPerformanceEdgeCases:
    """Test edge cases related to memory and performance."""
    
    def test_large_in_list(self):
        """Very large IN list."""
        values = list(range(10000))
        c = is_in("id", values)
        assert len(c.value) == 10000
    
    def test_deeply_nested_filter(self):
        """Many conditions in filter."""
        conditions = [eq(f"f{i}", i) for i in range(100)]
        rf = RelationshipFilter(conditions)
        assert len(rf.conditions) == 100
    
    def test_filter_repr_large(self):
        """Filter repr with many conditions."""
        conditions = [eq(f"f{i}", i) for i in range(10)]
        rf = RelationshipFilter(conditions)
        r = repr(rf)
        assert "RelationshipFilter" in r
    
    def test_to_dict_preserves_all(self):
        """to_dict preserves all condition data."""
        c = Condition("field", "LIKE", "%test%")
        d = c.to_dict()
        assert d["field"] == "field"
        assert d["operator"] == "LIKE"
        assert d["value"] == "%test%"


# =============================================================================
# Test Boundary Values
# =============================================================================

class TestBoundaryValues:
    """Test boundary values."""
    
    def test_int_max(self):
        """Maximum integer value."""
        import sys
        c = lt("count", sys.maxsize)
        assert c.value == sys.maxsize
    
    def test_int_min(self):
        """Minimum integer value."""
        import sys
        c = gt("count", -sys.maxsize - 1)
        assert c.value == -sys.maxsize - 1
    
    def test_float_inf(self):
        """Infinity float value."""
        import math
        c = lt("value", math.inf)
        assert c.value == math.inf
    
    def test_float_neg_inf(self):
        """Negative infinity float value."""
        import math
        c = gt("value", -math.inf)
        assert c.value == -math.inf
    
    def test_float_nan(self):
        """NaN float value (unusual but valid)."""
        import math
        c = ne("value", math.nan)
        assert math.isnan(c.value)

