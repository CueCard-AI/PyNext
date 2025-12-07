"""
Test Phase 7.5: Filter Conditions - Tuple Syntax.

These tests verify that:
1. Tuple syntax creates correct Condition objects
2. All operators work with tuple syntax
3. Mixed syntax (functions + tuples) works
"""

import pytest
from datetime import datetime

from pynext.db.relationships.conditions import (
    Condition,
    eq, gte,
    normalize_condition,
    normalize_conditions,
)
from pynext.db.relationships.filter import (
    RelationshipFilter,
    parse_filter,
)


# =============================================================================
# Test Basic Tuple Syntax
# =============================================================================

class TestBasicTupleSyntax:
    """Test basic tuple syntax for conditions."""
    
    def test_equality_tuple(self):
        """Tuple for equality."""
        c = normalize_condition(("is_active", "=", True))
        assert c.field == "is_active"
        assert c.operator == "="
        assert c.value is True
    
    def test_not_equal_tuple(self):
        """Tuple for not equal."""
        c = normalize_condition(("status", "!=", "deleted"))
        assert c.operator == "!="
        assert c.value == "deleted"
    
    def test_not_equal_alternate(self):
        """Alternate not equal operator (<>)."""
        c = normalize_condition(("status", "<>", "deleted"))
        assert c.operator == "<>"
    
    def test_greater_than_tuple(self):
        """Tuple for greater than."""
        c = normalize_condition(("age", ">", 18))
        assert c.operator == ">"
        assert c.value == 18
    
    def test_greater_equal_tuple(self):
        """Tuple for greater than or equal."""
        c = normalize_condition(("views", ">=", 100))
        assert c.operator == ">="
    
    def test_less_than_tuple(self):
        """Tuple for less than."""
        c = normalize_condition(("price", "<", 50))
        assert c.operator == "<"
    
    def test_less_equal_tuple(self):
        """Tuple for less than or equal."""
        c = normalize_condition(("quantity", "<=", 10))
        assert c.operator == "<="
    
    def test_like_tuple(self):
        """Tuple for LIKE."""
        c = normalize_condition(("title", "LIKE", "%python%"))
        assert c.operator == "LIKE"
        assert c.value == "%python%"
    
    def test_like_lowercase(self):
        """LIKE operator case-insensitive."""
        c = normalize_condition(("title", "like", "%test%"))
        assert c.operator == "LIKE"
    
    def test_ilike_tuple(self):
        """Tuple for ILIKE."""
        c = normalize_condition(("name", "ILIKE", "%john%"))
        assert c.operator == "ILIKE"
    
    def test_not_like_tuple(self):
        """Tuple for NOT LIKE."""
        c = normalize_condition(("email", "NOT LIKE", "%@test.com"))
        assert c.operator == "NOT LIKE"
    
    def test_in_tuple(self):
        """Tuple for IN."""
        c = normalize_condition(("status", "IN", ["active", "pending"]))
        assert c.operator == "IN"
        assert c.value == ["active", "pending"]
    
    def test_not_in_tuple(self):
        """Tuple for NOT IN."""
        c = normalize_condition(("status", "NOT IN", ["deleted"]))
        assert c.operator == "NOT IN"
    
    def test_is_null_tuple(self):
        """Tuple for IS NULL."""
        c = normalize_condition(("deleted_at", "IS NULL", True))
        assert c.operator == "IS NULL"
    
    def test_is_not_null_tuple(self):
        """Tuple for IS NOT NULL."""
        c = normalize_condition(("email", "IS NOT NULL", True))
        assert c.operator == "IS NOT NULL"


# =============================================================================
# Test Tuple with Various Values
# =============================================================================

class TestTupleValues:
    """Test tuple syntax with various value types."""
    
    def test_tuple_with_string(self):
        """Tuple with string value."""
        c = normalize_condition(("name", "=", "John"))
        assert c.value == "John"
    
    def test_tuple_with_integer(self):
        """Tuple with integer value."""
        c = normalize_condition(("count", "=", 42))
        assert c.value == 42
    
    def test_tuple_with_float(self):
        """Tuple with float value."""
        c = normalize_condition(("price", "<=", 19.99))
        assert c.value == 19.99
    
    def test_tuple_with_boolean_true(self):
        """Tuple with True value."""
        c = normalize_condition(("is_active", "=", True))
        assert c.value is True
    
    def test_tuple_with_boolean_false(self):
        """Tuple with False value."""
        c = normalize_condition(("is_deleted", "=", False))
        assert c.value is False
    
    def test_tuple_with_none(self):
        """Tuple with None value."""
        c = normalize_condition(("parent_id", "=", None))
        assert c.value is None
    
    def test_tuple_with_datetime(self):
        """Tuple with datetime value."""
        dt = datetime(2024, 1, 1)
        c = normalize_condition(("created_at", ">=", dt))
        assert c.value == dt
    
    def test_tuple_with_list(self):
        """Tuple with list value (for IN)."""
        c = normalize_condition(("category", "IN", [1, 2, 3]))
        assert c.value == [1, 2, 3]
    
    def test_tuple_with_empty_string(self):
        """Tuple with empty string."""
        c = normalize_condition(("code", "!=", ""))
        assert c.value == ""


# =============================================================================
# Test Mixed Syntax in Filter
# =============================================================================

class TestMixedSyntax:
    """Test mixing condition functions and tuple syntax."""
    
    def test_filter_all_functions(self):
        """Filter with all function-style conditions."""
        rf = RelationshipFilter([
            eq("is_active", True),
            gte("views", 100),
        ])
        assert len(rf.conditions) == 2
    
    def test_filter_all_tuples(self):
        """Filter with all tuple-style conditions."""
        rf = RelationshipFilter([
            ("is_active", "=", True),
            ("views", ">=", 100),
        ])
        assert len(rf.conditions) == 2
    
    def test_filter_mixed_function_tuple(self):
        """Filter mixing functions and tuples."""
        rf = RelationshipFilter([
            eq("is_active", True),      # Function
            ("views", ">=", 100),       # Tuple
            gte("created_at", datetime(2024, 1, 1)),  # Function
            ("status", "IN", ["a", "b"]),  # Tuple
        ])
        assert len(rf.conditions) == 4
        assert rf.conditions[0].operator == "="
        assert rf.conditions[1].operator == ">="
        assert rf.conditions[2].operator == ">="
        assert rf.conditions[3].operator == "IN"
    
    def test_filter_single_condition(self):
        """Filter with single condition."""
        rf = RelationshipFilter([eq("active", True)])
        assert len(rf.conditions) == 1
    
    def test_filter_single_tuple(self):
        """Filter with single tuple."""
        rf = RelationshipFilter([("active", "=", True)])
        assert len(rf.conditions) == 1


# =============================================================================
# Test Invalid Tuples
# =============================================================================

class TestInvalidTuples:
    """Test error handling for invalid tuples."""
    
    def test_tuple_too_short(self):
        """Tuple with only 2 elements."""
        with pytest.raises(ValueError) as exc:
            normalize_condition(("field", "="))
        assert "3 elements" in str(exc.value)
    
    def test_tuple_too_long(self):
        """Tuple with 4 elements."""
        with pytest.raises(ValueError) as exc:
            normalize_condition(("field", "=", "value", "extra"))
        assert "3 elements" in str(exc.value)
    
    def test_tuple_invalid_operator(self):
        """Tuple with invalid operator."""
        with pytest.raises(ValueError) as exc:
            normalize_condition(("field", "INVALID", "value"))
        assert "Invalid operator" in str(exc.value)
    
    def test_tuple_empty_field(self):
        """Tuple with empty field name."""
        with pytest.raises(ValueError) as exc:
            normalize_condition(("", "=", "value"))
        assert "cannot be empty" in str(exc.value)


# =============================================================================
# Test Operator Case Insensitivity
# =============================================================================

class TestOperatorCase:
    """Test that operators are case-insensitive."""
    
    def test_like_lowercase(self):
        """LIKE in lowercase."""
        c = normalize_condition(("title", "like", "%test%"))
        assert c.operator == "LIKE"
    
    def test_in_lowercase(self):
        """IN in lowercase."""
        c = normalize_condition(("status", "in", ["a"]))
        assert c.operator == "IN"
    
    def test_is_null_mixed_case(self):
        """IS NULL in mixed case."""
        c = normalize_condition(("field", "Is Null", True))
        assert c.operator == "IS NULL"
    
    def test_is_not_null_mixed_case(self):
        """IS NOT NULL in mixed case."""
        c = normalize_condition(("field", "is not null", True))
        assert c.operator == "IS NOT NULL"
    
    def test_not_in_lowercase(self):
        """NOT IN in lowercase."""
        c = normalize_condition(("status", "not in", ["x"]))
        assert c.operator == "NOT IN"


# =============================================================================
# Test normalize_conditions with Tuples
# =============================================================================

class TestNormalizeConditionsWithTuples:
    """Test normalize_conditions with tuple input."""
    
    def test_all_tuples(self):
        """All conditions as tuples."""
        result = normalize_conditions([
            ("a", "=", 1),
            ("b", ">", 2),
            ("c", "LIKE", "%x%"),
        ])
        assert len(result) == 3
        assert all(isinstance(c, Condition) for c in result)
    
    def test_mixed_input(self):
        """Mixed functions and tuples."""
        result = normalize_conditions([
            eq("a", 1),
            ("b", ">", 2),
        ])
        assert result[0].field == "a"
        assert result[1].field == "b"
    
    def test_preserves_order(self):
        """Order of conditions is preserved."""
        result = normalize_conditions([
            ("z", "=", 1),
            ("a", "=", 2),
            ("m", "=", 3),
        ])
        assert result[0].field == "z"
        assert result[1].field == "a"
        assert result[2].field == "m"


# =============================================================================
# Test SQL-like Syntax Patterns
# =============================================================================

class TestSQLPatterns:
    """Test common SQL-like patterns with tuple syntax."""
    
    def test_basic_equality(self):
        """Basic WHERE field = value."""
        c = normalize_condition(("status", "=", "active"))
        assert c.operator == "="
    
    def test_comparison_chain(self):
        """Multiple comparisons."""
        conditions = normalize_conditions([
            ("price", ">=", 10),
            ("price", "<=", 100),
        ])
        assert conditions[0].operator == ">="
        assert conditions[1].operator == "<="
    
    def test_string_pattern(self):
        """String pattern matching."""
        c = normalize_condition(("name", "LIKE", "John%"))
        assert c.operator == "LIKE"
    
    def test_in_list(self):
        """IN list of values."""
        c = normalize_condition(("category", "IN", ["books", "music", "movies"]))
        assert c.operator == "IN"
        assert len(c.value) == 3
    
    def test_null_check(self):
        """NULL checking."""
        null_cond = normalize_condition(("deleted_at", "IS NULL", True))
        not_null_cond = normalize_condition(("email", "IS NOT NULL", True))
        assert null_cond.operator == "IS NULL"
        assert not_null_cond.operator == "IS NOT NULL"


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestTupleEdgeCases:
    """Test edge cases for tuple syntax."""
    
    def test_field_with_underscore(self):
        """Field name with underscores."""
        c = normalize_condition(("created_at_utc", ">=", datetime(2024, 1, 1)))
        assert c.field == "created_at_utc"
    
    def test_field_with_numbers(self):
        """Field name with numbers."""
        c = normalize_condition(("level2_score", ">", 50))
        assert c.field == "level2_score"
    
    def test_value_with_special_chars(self):
        """Value with special characters."""
        c = normalize_condition(("email", "LIKE", "%@example.com"))
        assert c.value == "%@example.com"
    
    def test_value_with_quotes(self):
        """Value containing quotes."""
        c = normalize_condition(("title", "=", "It's a test"))
        assert c.value == "It's a test"
    
    def test_very_long_list(self):
        """IN with very long list."""
        values = list(range(1000))
        c = normalize_condition(("id", "IN", values))
        assert len(c.value) == 1000
    
    def test_nested_list_value(self):
        """Value that is a nested list."""
        c = normalize_condition(("data", "=", [[1, 2], [3, 4]]))
        assert c.value == [[1, 2], [3, 4]]

