"""
Test Phase 7.5: Filter Conditions - Condition Functions.

These tests verify that:
1. All condition functions create correct Condition objects
2. Operators are normalized correctly
3. Validation works for invalid inputs
"""

import pytest
from datetime import datetime, timedelta

from pynext.db.relationships.conditions import (
    Condition,
    eq, ne, gt, gte, lt, lte,
    like, ilike, not_like,
    is_in, not_in, is_null,
    equals, not_equals,
    greater_than, greater_than_or_equal,
    less_than, less_than_or_equal,
    contains,
    normalize_condition,
    normalize_conditions,
)


# =============================================================================
# Test Condition Class
# =============================================================================

class TestConditionClass:
    """Test the Condition dataclass."""
    
    def test_create_basic_condition(self):
        """Create a basic condition."""
        c = Condition("name", "=", "John")
        assert c.field == "name"
        assert c.operator == "="
        assert c.value == "John"
    
    def test_operator_normalized_to_uppercase(self):
        """Operators should be normalized to uppercase."""
        c = Condition("name", "like", "%test%")
        assert c.operator == "LIKE"
    
    def test_condition_to_dict(self):
        """Convert condition to dict."""
        c = Condition("age", ">=", 18)
        d = c.to_dict()
        assert d == {"field": "age", "operator": ">=", "value": 18}
    
    def test_condition_repr(self):
        """Test string representation."""
        c = Condition("active", "=", True)
        r = repr(c)
        assert "active" in r
        assert "=" in r
        assert "True" in r
    
    def test_empty_field_raises_error(self):
        """Empty field should raise ValueError."""
        with pytest.raises(ValueError) as exc:
            Condition("", "=", "test")
        assert "cannot be empty" in str(exc.value)
    
    def test_invalid_operator_raises_error(self):
        """Invalid operator should raise ValueError."""
        with pytest.raises(ValueError) as exc:
            Condition("name", "INVALID", "test")
        assert "Invalid operator" in str(exc.value)
    
    def test_valid_operators(self):
        """Test all valid operators."""
        valid_ops = ["=", "!=", "<>", ">", ">=", "<", "<=", 
                     "LIKE", "ILIKE", "NOT LIKE", "IN", "NOT IN",
                     "IS NULL", "IS NOT NULL"]
        for op in valid_ops:
            c = Condition("field", op, "value")
            assert c.operator == op.upper()


# =============================================================================
# Test eq() Function
# =============================================================================

class TestEqFunction:
    """Test the eq() condition function."""
    
    def test_eq_string(self):
        """Equality with string value."""
        c = eq("name", "John")
        assert c.field == "name"
        assert c.operator == "="
        assert c.value == "John"
    
    def test_eq_integer(self):
        """Equality with integer value."""
        c = eq("age", 25)
        assert c.value == 25
        assert c.operator == "="
    
    def test_eq_boolean(self):
        """Equality with boolean value."""
        c = eq("is_active", True)
        assert c.value is True
    
    def test_eq_none(self):
        """Equality with None (though is_null is preferred)."""
        c = eq("deleted_at", None)
        assert c.value is None
    
    def test_eq_float(self):
        """Equality with float value."""
        c = eq("price", 19.99)
        assert c.value == 19.99
    
    def test_eq_datetime(self):
        """Equality with datetime value."""
        dt = datetime.now()
        c = eq("created_at", dt)
        assert c.value == dt


# =============================================================================
# Test ne() Function
# =============================================================================

class TestNeFunction:
    """Test the ne() condition function."""
    
    def test_ne_string(self):
        """Not equal with string."""
        c = ne("status", "deleted")
        assert c.operator == "!="
        assert c.value == "deleted"
    
    def test_ne_integer(self):
        """Not equal with integer."""
        c = ne("count", 0)
        assert c.operator == "!="
        assert c.value == 0
    
    def test_ne_boolean(self):
        """Not equal with boolean."""
        c = ne("verified", False)
        assert c.value is False


# =============================================================================
# Test gt() Function
# =============================================================================

class TestGtFunction:
    """Test the gt() condition function."""
    
    def test_gt_integer(self):
        """Greater than with integer."""
        c = gt("age", 18)
        assert c.operator == ">"
        assert c.value == 18
    
    def test_gt_float(self):
        """Greater than with float."""
        c = gt("price", 9.99)
        assert c.value == 9.99
    
    def test_gt_datetime(self):
        """Greater than with datetime."""
        dt = datetime.now()
        c = gt("created_at", dt)
        assert c.value == dt


# =============================================================================
# Test gte() Function
# =============================================================================

class TestGteFunction:
    """Test the gte() condition function."""
    
    def test_gte_integer(self):
        """Greater than or equal with integer."""
        c = gte("views", 100)
        assert c.operator == ">="
        assert c.value == 100
    
    def test_gte_zero(self):
        """Greater than or equal to zero."""
        c = gte("balance", 0)
        assert c.value == 0


# =============================================================================
# Test lt() Function
# =============================================================================

class TestLtFunction:
    """Test the lt() condition function."""
    
    def test_lt_integer(self):
        """Less than with integer."""
        c = lt("quantity", 10)
        assert c.operator == "<"
        assert c.value == 10
    
    def test_lt_float(self):
        """Less than with float."""
        c = lt("price", 50.00)
        assert c.value == 50.00


# =============================================================================
# Test lte() Function
# =============================================================================

class TestLteFunction:
    """Test the lte() condition function."""
    
    def test_lte_integer(self):
        """Less than or equal with integer."""
        c = lte("priority", 5)
        assert c.operator == "<="
        assert c.value == 5


# =============================================================================
# Test like() Function
# =============================================================================

class TestLikeFunction:
    """Test the like() condition function."""
    
    def test_like_prefix(self):
        """LIKE with prefix wildcard."""
        c = like("email", "%@gmail.com")
        assert c.operator == "LIKE"
        assert c.value == "%@gmail.com"
    
    def test_like_suffix(self):
        """LIKE with suffix wildcard."""
        c = like("name", "John%")
        assert c.value == "John%"
    
    def test_like_contains(self):
        """LIKE with both wildcards (contains)."""
        c = like("title", "%python%")
        assert c.value == "%python%"
    
    def test_like_exact(self):
        """LIKE without wildcards (exact match)."""
        c = like("code", "ABC123")
        assert c.value == "ABC123"


# =============================================================================
# Test ilike() Function
# =============================================================================

class TestIlikeFunction:
    """Test the ilike() condition function."""
    
    def test_ilike_case_insensitive(self):
        """ILIKE for case-insensitive matching."""
        c = ilike("name", "%john%")
        assert c.operator == "ILIKE"
        assert c.value == "%john%"


# =============================================================================
# Test not_like() Function
# =============================================================================

class TestNotLikeFunction:
    """Test the not_like() condition function."""
    
    def test_not_like(self):
        """NOT LIKE pattern."""
        c = not_like("email", "%@test.com")
        assert c.operator == "NOT LIKE"
        assert c.value == "%@test.com"


# =============================================================================
# Test is_in() Function
# =============================================================================

class TestIsInFunction:
    """Test the is_in() condition function."""
    
    def test_is_in_strings(self):
        """IN with list of strings."""
        c = is_in("status", ["active", "pending"])
        assert c.operator == "IN"
        assert c.value == ["active", "pending"]
    
    def test_is_in_integers(self):
        """IN with list of integers."""
        c = is_in("category_id", [1, 2, 3])
        assert c.value == [1, 2, 3]
    
    def test_is_in_tuple(self):
        """IN with tuple (converts to list)."""
        c = is_in("id", (1, 2, 3))
        assert c.value == [1, 2, 3]
    
    def test_is_in_set(self):
        """IN with set (converts to list)."""
        c = is_in("type", {"a", "b"})
        assert isinstance(c.value, list)
        assert set(c.value) == {"a", "b"}
    
    def test_is_in_non_list_raises(self):
        """Non-list/tuple/set should raise ValueError."""
        with pytest.raises(ValueError) as exc:
            is_in("id", "not a list")
        assert "requires a list" in str(exc.value)
    
    def test_is_in_empty_list(self):
        """Empty list is valid (though probably not useful)."""
        c = is_in("id", [])
        assert c.value == []


# =============================================================================
# Test not_in() Function
# =============================================================================

class TestNotInFunction:
    """Test the not_in() condition function."""
    
    def test_not_in(self):
        """NOT IN with list."""
        c = not_in("status", ["deleted", "archived"])
        assert c.operator == "NOT IN"
        assert c.value == ["deleted", "archived"]
    
    def test_not_in_non_list_raises(self):
        """Non-list should raise ValueError."""
        with pytest.raises(ValueError):
            not_in("id", 123)


# =============================================================================
# Test is_null() Function
# =============================================================================

class TestIsNullFunction:
    """Test the is_null() condition function."""
    
    def test_is_null_true(self):
        """IS NULL check."""
        c = is_null("deleted_at")
        assert c.operator == "IS NULL"
    
    def test_is_null_explicit_true(self):
        """IS NULL with explicit True."""
        c = is_null("deleted_at", True)
        assert c.operator == "IS NULL"
    
    def test_is_null_false(self):
        """IS NOT NULL check."""
        c = is_null("email", False)
        assert c.operator == "IS NOT NULL"


# =============================================================================
# Test Aliases
# =============================================================================

class TestAliases:
    """Test condition function aliases."""
    
    def test_equals_is_eq(self):
        """equals is alias for eq."""
        c = equals("name", "test")
        assert c.operator == "="
    
    def test_not_equals_is_ne(self):
        """not_equals is alias for ne."""
        c = not_equals("status", "deleted")
        assert c.operator == "!="
    
    def test_greater_than_is_gt(self):
        """greater_than is alias for gt."""
        c = greater_than("age", 18)
        assert c.operator == ">"
    
    def test_greater_than_or_equal_is_gte(self):
        """greater_than_or_equal is alias for gte."""
        c = greater_than_or_equal("views", 100)
        assert c.operator == ">="
    
    def test_less_than_is_lt(self):
        """less_than is alias for lt."""
        c = less_than("price", 50)
        assert c.operator == "<"
    
    def test_less_than_or_equal_is_lte(self):
        """less_than_or_equal is alias for lte."""
        c = less_than_or_equal("quantity", 0)
        assert c.operator == "<="
    
    def test_contains_is_like(self):
        """contains is alias for like."""
        c = contains("title", "%python%")
        assert c.operator == "LIKE"


# =============================================================================
# Test normalize_condition()
# =============================================================================

class TestNormalizeCondition:
    """Test normalize_condition function."""
    
    def test_normalize_condition_object(self):
        """Condition object returned as-is."""
        original = eq("name", "test")
        normalized = normalize_condition(original)
        assert normalized is original
    
    def test_normalize_tuple(self):
        """Tuple converted to Condition."""
        normalized = normalize_condition(("age", ">", 18))
        assert isinstance(normalized, Condition)
        assert normalized.field == "age"
        assert normalized.operator == ">"
        assert normalized.value == 18
    
    def test_normalize_tuple_wrong_length_raises(self):
        """Tuple with wrong length raises ValueError."""
        with pytest.raises(ValueError) as exc:
            normalize_condition(("field", "="))
        assert "3 elements" in str(exc.value)
    
    def test_normalize_invalid_type_raises(self):
        """Invalid type raises ValueError."""
        with pytest.raises(ValueError) as exc:
            normalize_condition("invalid")
        assert "Invalid condition type" in str(exc.value)
    
    def test_normalize_list_raises(self):
        """List (not tuple) raises ValueError."""
        with pytest.raises(ValueError):
            normalize_condition(["field", "=", "value"])


# =============================================================================
# Test normalize_conditions()
# =============================================================================

class TestNormalizeConditions:
    """Test normalize_conditions function."""
    
    def test_normalize_empty_list(self):
        """Empty list returns empty list."""
        result = normalize_conditions([])
        assert result == []
    
    def test_normalize_all_conditions(self):
        """All Condition objects."""
        conditions = [eq("a", 1), ne("b", 2)]
        result = normalize_conditions(conditions)
        assert len(result) == 2
        assert all(isinstance(c, Condition) for c in result)
    
    def test_normalize_all_tuples(self):
        """All tuples."""
        conditions = [("a", "=", 1), ("b", "!=", 2)]
        result = normalize_conditions(conditions)
        assert len(result) == 2
        assert all(isinstance(c, Condition) for c in result)
    
    def test_normalize_mixed(self):
        """Mixed Condition objects and tuples."""
        conditions = [
            eq("a", 1),
            ("b", ">", 2),
            gte("c", 3),
        ]
        result = normalize_conditions(conditions)
        assert len(result) == 3
        assert result[0].operator == "="
        assert result[1].operator == ">"
        assert result[2].operator == ">="


# =============================================================================
# Test Various Value Types
# =============================================================================

class TestValueTypes:
    """Test conditions with various value types."""
    
    def test_condition_with_list_value(self):
        """Condition with list value (for IN)."""
        c = is_in("tags", ["python", "web"])
        assert c.value == ["python", "web"]
    
    def test_condition_with_datetime(self):
        """Condition with datetime value."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        c = gte("created_at", dt)
        assert c.value == dt
    
    def test_condition_with_negative_number(self):
        """Condition with negative number."""
        c = lt("balance", -100)
        assert c.value == -100
    
    def test_condition_with_zero(self):
        """Condition with zero."""
        c = eq("count", 0)
        assert c.value == 0
    
    def test_condition_with_empty_string(self):
        """Condition with empty string."""
        c = ne("name", "")
        assert c.value == ""
    
    def test_condition_with_dict_value(self):
        """Condition with dict value (JSON)."""
        c = eq("metadata", {"key": "value"})
        assert c.value == {"key": "value"}

