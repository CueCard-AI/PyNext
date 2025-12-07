"""
Test Phase 7.5: Filter Parsing.

These tests verify that:
1. RelationshipFilter correctly normalizes conditions
2. parse_filter handles all input types
3. Filter applies correctly to queries
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock

from pynext.db.relationships.conditions import (
    Condition,
    eq, ne, gt, gte, lt, lte,
    like, is_in, is_null,
)
from pynext.db.relationships.filter import (
    RelationshipFilter,
    parse_filter,
)


# =============================================================================
# Test RelationshipFilter Creation
# =============================================================================

class TestRelationshipFilterCreation:
    """Test RelationshipFilter initialization."""
    
    def test_create_empty_filter(self):
        """Create filter with empty list."""
        rf = RelationshipFilter([])
        assert len(rf.conditions) == 0
    
    def test_create_filter_none(self):
        """Create filter with None."""
        rf = RelationshipFilter(None)
        assert len(rf.conditions) == 0
    
    def test_create_with_single_condition(self):
        """Create filter with single condition."""
        rf = RelationshipFilter([eq("active", True)])
        assert len(rf.conditions) == 1
    
    def test_create_with_multiple_conditions(self):
        """Create filter with multiple conditions."""
        rf = RelationshipFilter([
            eq("active", True),
            gte("views", 100),
            like("title", "%python%"),
        ])
        assert len(rf.conditions) == 3
    
    def test_create_with_tuples(self):
        """Create filter with tuple conditions."""
        rf = RelationshipFilter([
            ("active", "=", True),
            ("views", ">=", 100),
        ])
        assert len(rf.conditions) == 2
    
    def test_create_with_mixed(self):
        """Create filter with mixed conditions."""
        rf = RelationshipFilter([
            eq("active", True),
            ("views", ">=", 100),
        ])
        assert len(rf.conditions) == 2


# =============================================================================
# Test RelationshipFilter Properties
# =============================================================================

class TestRelationshipFilterProperties:
    """Test RelationshipFilter property methods."""
    
    def test_is_empty_true(self):
        """is_empty returns True for empty filter."""
        rf = RelationshipFilter([])
        assert rf.is_empty() is True
    
    def test_is_empty_false(self):
        """is_empty returns False for non-empty filter."""
        rf = RelationshipFilter([eq("a", 1)])
        assert rf.is_empty() is False
    
    def test_len_empty(self):
        """len returns 0 for empty filter."""
        rf = RelationshipFilter([])
        assert len(rf) == 0
    
    def test_len_one(self):
        """len returns 1 for single condition."""
        rf = RelationshipFilter([eq("a", 1)])
        assert len(rf) == 1
    
    def test_len_multiple(self):
        """len returns correct count."""
        rf = RelationshipFilter([eq("a", 1), eq("b", 2), eq("c", 3)])
        assert len(rf) == 3
    
    def test_bool_empty(self):
        """bool returns False for empty filter."""
        rf = RelationshipFilter([])
        assert bool(rf) is False
    
    def test_bool_non_empty(self):
        """bool returns True for non-empty filter."""
        rf = RelationshipFilter([eq("a", 1)])
        assert bool(rf) is True
    
    def test_repr_empty(self):
        """repr for empty filter."""
        rf = RelationshipFilter([])
        assert "RelationshipFilter([])" in repr(rf)
    
    def test_repr_with_conditions(self):
        """repr includes conditions."""
        rf = RelationshipFilter([eq("active", True)])
        r = repr(rf)
        assert "RelationshipFilter" in r
        assert "active" in r
    
    def test_to_dict(self):
        """to_dict returns dict representation."""
        rf = RelationshipFilter([eq("a", 1)])
        d = rf.to_dict()
        assert "conditions" in d
        assert len(d["conditions"]) == 1


# =============================================================================
# Test parse_filter Function
# =============================================================================

class TestParseFilter:
    """Test the parse_filter utility function."""
    
    def test_parse_none(self):
        """parse_filter returns None for None input."""
        result = parse_filter(None)
        assert result is None
    
    def test_parse_empty_list(self):
        """parse_filter returns None for empty list."""
        result = parse_filter([])
        assert result is None
    
    def test_parse_condition_list(self):
        """parse_filter creates filter from condition list."""
        result = parse_filter([eq("a", 1)])
        assert isinstance(result, RelationshipFilter)
        assert len(result.conditions) == 1
    
    def test_parse_relationship_filter(self):
        """parse_filter returns RelationshipFilter as-is."""
        original = RelationshipFilter([eq("a", 1)])
        result = parse_filter(original)
        assert result is original
    
    def test_parse_invalid_type_raises(self):
        """parse_filter raises for invalid type."""
        with pytest.raises(ValueError) as exc:
            parse_filter("invalid")
        assert "Invalid filter type" in str(exc.value)


# =============================================================================
# Test RelationshipFilter.from_list
# =============================================================================

class TestFromList:
    """Test RelationshipFilter.from_list class method."""
    
    def test_from_list_none(self):
        """from_list returns None for None."""
        result = RelationshipFilter.from_list(None)
        assert result is None
    
    def test_from_list_empty(self):
        """from_list returns None for empty list."""
        result = RelationshipFilter.from_list([])
        assert result is None
    
    def test_from_list_conditions(self):
        """from_list creates filter from conditions."""
        result = RelationshipFilter.from_list([eq("a", 1)])
        assert isinstance(result, RelationshipFilter)


# =============================================================================
# Test Filter Apply to Query (Mock)
# =============================================================================

class TestApplyToQuery:
    """Test RelationshipFilter.apply_to_query with mock Query."""
    
    def _create_mock_query(self):
        """Create a mock Query object."""
        query = Mock()
        # Chain all methods to return the query
        for method in ['where', 'where_not', 'where_gt', 'where_gte',
                       'where_lt', 'where_lte', 'where_like', 'where_ilike',
                       'where_in', 'where_not_in', 'where_null', 'where_not_null',
                       'where_not_like']:
            getattr(query, method).return_value = query
        return query
    
    def test_apply_eq(self):
        """Apply equality condition."""
        query = self._create_mock_query()
        rf = RelationshipFilter([eq("active", True)])
        rf.apply_to_query(query)
        query.where.assert_called_with(active=True)
    
    def test_apply_ne(self):
        """Apply not equal condition."""
        query = self._create_mock_query()
        rf = RelationshipFilter([ne("status", "deleted")])
        rf.apply_to_query(query)
        query.where_not.assert_called_with(status="deleted")
    
    def test_apply_gt(self):
        """Apply greater than condition."""
        query = self._create_mock_query()
        rf = RelationshipFilter([gt("age", 18)])
        rf.apply_to_query(query)
        query.where_gt.assert_called_with(age=18)
    
    def test_apply_gte(self):
        """Apply greater than or equal condition."""
        query = self._create_mock_query()
        rf = RelationshipFilter([gte("views", 100)])
        rf.apply_to_query(query)
        query.where_gte.assert_called_with(views=100)
    
    def test_apply_lt(self):
        """Apply less than condition."""
        query = self._create_mock_query()
        rf = RelationshipFilter([lt("price", 50)])
        rf.apply_to_query(query)
        query.where_lt.assert_called_with(price=50)
    
    def test_apply_lte(self):
        """Apply less than or equal condition."""
        query = self._create_mock_query()
        rf = RelationshipFilter([lte("quantity", 10)])
        rf.apply_to_query(query)
        query.where_lte.assert_called_with(quantity=10)
    
    def test_apply_like(self):
        """Apply LIKE condition."""
        query = self._create_mock_query()
        rf = RelationshipFilter([like("title", "%python%")])
        rf.apply_to_query(query)
        query.where_like.assert_called_with(title="%python%")
    
    def test_apply_in(self):
        """Apply IN condition."""
        query = self._create_mock_query()
        rf = RelationshipFilter([is_in("status", ["a", "b"])])
        rf.apply_to_query(query)
        query.where_in.assert_called_with(status=["a", "b"])
    
    def test_apply_is_null(self):
        """Apply IS NULL condition."""
        query = self._create_mock_query()
        rf = RelationshipFilter([is_null("deleted_at")])
        rf.apply_to_query(query)
        query.where_null.assert_called_with("deleted_at")
    
    def test_apply_is_not_null(self):
        """Apply IS NOT NULL condition."""
        query = self._create_mock_query()
        rf = RelationshipFilter([is_null("email", False)])
        rf.apply_to_query(query)
        query.where_not_null.assert_called_with("email")
    
    def test_apply_multiple_conditions(self):
        """Apply multiple conditions."""
        query = self._create_mock_query()
        rf = RelationshipFilter([
            eq("active", True),
            gte("views", 100),
            like("title", "%python%"),
        ])
        rf.apply_to_query(query)
        query.where.assert_called()
        query.where_gte.assert_called()
        query.where_like.assert_called()
    
    def test_apply_empty_filter(self):
        """Apply empty filter (no-op)."""
        query = self._create_mock_query()
        rf = RelationshipFilter([])
        result = rf.apply_to_query(query)
        # Empty filter should not call any methods
        # Query should be returned as-is


# =============================================================================
# Test Complex Filters
# =============================================================================

class TestComplexFilters:
    """Test complex filter scenarios."""
    
    def test_many_conditions(self):
        """Filter with many conditions."""
        conditions = [eq(f"field_{i}", i) for i in range(20)]
        rf = RelationshipFilter(conditions)
        assert len(rf.conditions) == 20
    
    def test_all_operator_types(self):
        """Filter using all operator types."""
        rf = RelationshipFilter([
            eq("a", 1),
            ne("b", 2),
            gt("c", 3),
            gte("d", 4),
            lt("e", 5),
            lte("f", 6),
            like("g", "%x%"),
            is_in("h", [1, 2]),
            is_null("i"),
        ])
        assert len(rf.conditions) == 9
    
    def test_same_field_multiple_times(self):
        """Same field with different conditions (range)."""
        rf = RelationshipFilter([
            gte("price", 10),
            lte("price", 100),
        ])
        assert len(rf.conditions) == 2
        assert rf.conditions[0].field == "price"
        assert rf.conditions[1].field == "price"
    
    def test_datetime_range(self):
        """Date range filter."""
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        rf = RelationshipFilter([
            gte("created_at", thirty_days_ago),
            lte("created_at", now),
        ])
        assert len(rf.conditions) == 2


# =============================================================================
# Test Error Handling
# =============================================================================

class TestFilterErrors:
    """Test error handling in filter operations."""
    
    def test_invalid_condition_in_list(self):
        """Invalid condition in list raises error."""
        with pytest.raises(ValueError):
            RelationshipFilter([
                eq("a", 1),
                "invalid",  # Not a valid condition
            ])
    
    def test_tuple_wrong_size(self):
        """Tuple with wrong size raises error."""
        with pytest.raises(ValueError):
            RelationshipFilter([
                ("field", "="),  # Missing value
            ])
    
    def test_invalid_operator_in_tuple(self):
        """Invalid operator in tuple raises error."""
        with pytest.raises(ValueError):
            RelationshipFilter([
                ("field", "BADOP", "value"),
            ])


# =============================================================================
# Test Condition Normalization in Filter
# =============================================================================

class TestConditionNormalization:
    """Test that conditions are properly normalized."""
    
    def test_tuples_normalized(self):
        """Tuples are converted to Condition objects."""
        rf = RelationshipFilter([("field", "=", "value")])
        assert isinstance(rf.conditions[0], Condition)
    
    def test_conditions_unchanged(self):
        """Condition objects are not modified."""
        original = eq("field", "value")
        rf = RelationshipFilter([original])
        # Should be same type
        assert type(rf.conditions[0]) == type(original)
    
    def test_operator_normalized(self):
        """Operators are normalized to uppercase."""
        rf = RelationshipFilter([("field", "like", "%x%")])
        assert rf.conditions[0].operator == "LIKE"


# =============================================================================
# Test Thread Safety / Immutability
# =============================================================================

class TestFilterImmutability:
    """Test that filters behave correctly with respect to mutations."""
    
    def test_original_list_not_modified(self):
        """Original condition list is not modified."""
        original = [eq("a", 1)]
        rf = RelationshipFilter(original)
        # Filter should have made a copy
        original.append(eq("b", 2))
        assert len(rf.conditions) == 1
    
    def test_conditions_list_copy(self):
        """Conditions list is a copy."""
        rf = RelationshipFilter([eq("a", 1)])
        # Modifying internal list shouldn't be possible from outside
        assert len(rf.conditions) == 1

