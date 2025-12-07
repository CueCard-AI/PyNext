"""
Tests for ordering edge cases.

Tests cover:
- Empty orderings
- Invalid inputs
- Special characters
- Extreme cases
- Error handling
"""

import pytest
from typing import List

from pynext.db.relationships.ordering import (
    OrderSpec,
    OrderingConfig,
    parse_order_by,
    parse_order_spec,
    build_order_clause,
    build_order_columns,
    validate_order_by,
    normalize_order_by,
    sort_items,
)
from pynext.db.relationships.core import has_many, many_to_many


# =============================================================================
# Mock Models
# =============================================================================

class MockItem:
    """Mock item for testing."""
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# =============================================================================
# Test: Empty Orderings
# =============================================================================

class TestEmptyOrderings:
    """Test empty ordering cases."""
    
    def test_parse_none(self):
        """Parse None returns empty list."""
        result = parse_order_by(None)
        assert result == []
    
    def test_parse_empty_list(self):
        """Parse empty list returns empty list."""
        result = parse_order_by([])
        assert result == []
    
    def test_ordering_config_empty(self):
        """Empty OrderingConfig."""
        config = OrderingConfig()
        assert not config.has_ordering
        assert len(config) == 0
        assert not config  # Boolean False
    
    def test_from_none(self):
        """OrderingConfig from None."""
        config = OrderingConfig.from_order_by(None)
        assert not config.has_ordering
    
    def test_build_clause_empty(self):
        """Build clause from empty specs."""
        result = build_order_clause([])
        assert result == ""
    
    def test_build_columns_empty(self):
        """Build columns from empty specs."""
        result = build_order_columns([])
        assert result == []
    
    def test_sort_items_empty_specs(self):
        """Sort items with empty specs returns copy."""
        items = [MockItem(name="A"), MockItem(name="B")]
        result = sort_items(items, [])
        assert result == items
        assert result is not items  # Should be new list


class TestInvalidInputs:
    """Test invalid input handling."""
    
    def test_parse_spec_empty_string(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError):
            parse_order_spec("")
    
    def test_parse_spec_whitespace(self):
        """Whitespace only raises ValueError."""
        with pytest.raises(ValueError):
            parse_order_spec("   ")
    
    def test_parse_order_by_invalid_type(self):
        """Invalid type raises TypeError."""
        with pytest.raises(TypeError):
            parse_order_by(123)
    
    def test_parse_order_by_dict(self):
        """Dict raises TypeError."""
        with pytest.raises(TypeError):
            parse_order_by({"column": "name"})
    
    def test_order_spec_empty_column(self):
        """Empty column raises ValueError."""
        with pytest.raises(ValueError):
            OrderSpec("", "asc")
    
    def test_order_spec_invalid_direction(self):
        """Invalid direction raises ValueError."""
        with pytest.raises(ValueError):
            OrderSpec("name", "sideways")
    
    def test_order_spec_invalid_nulls(self):
        """Invalid nulls raises ValueError."""
        with pytest.raises(ValueError):
            OrderSpec("name", "asc", "middle")


class TestSpecialColumnNames:
    """Test special column name handling."""
    
    def test_underscore_prefix(self):
        """Column with underscore prefix."""
        spec = parse_order_spec("_private")
        assert spec.column == "_private"
    
    def test_underscore_suffix(self):
        """Column with underscore suffix."""
        spec = parse_order_spec("column_")
        assert spec.column == "column_"
    
    def test_multiple_underscores(self):
        """Column with multiple underscores."""
        spec = parse_order_spec("created_at_date")
        assert spec.column == "created_at_date"
    
    def test_single_char_column(self):
        """Single character column."""
        spec = parse_order_spec("x")
        assert spec.column == "x"
    
    def test_numeric_suffix(self):
        """Column with numeric suffix."""
        spec = parse_order_spec("field1")
        assert spec.column == "field1"
    
    def test_all_caps_column(self):
        """All caps column (normalized to lowercase)."""
        spec = parse_order_spec("NAME")
        assert spec.column == "name"


class TestInvalidColumnNames:
    """Test invalid column name handling."""
    
    def test_sql_injection_attempt(self):
        """SQL injection attempt raises ValueError."""
        with pytest.raises(ValueError):
            OrderSpec("name; DROP TABLE users", "asc")
    
    def test_space_in_column(self):
        """Space in column raises ValueError."""
        with pytest.raises(ValueError):
            OrderSpec("column name", "asc")
    
    def test_hyphen_in_column(self):
        """Hyphen in column raises ValueError."""
        with pytest.raises(ValueError):
            OrderSpec("column-name", "asc")
    
    def test_dot_in_column(self):
        """Dot in column raises ValueError."""
        with pytest.raises(ValueError):
            OrderSpec("table.column", "asc")
    
    def test_special_chars(self):
        """Special characters raise ValueError."""
        invalid_names = ["col!", "col@", "col#", "col$", "col%", "col^"]
        for name in invalid_names:
            with pytest.raises(ValueError):
                OrderSpec(name, "asc")
    
    def test_starts_with_number(self):
        """Column starting with number raises ValueError."""
        with pytest.raises(ValueError):
            OrderSpec("1column", "asc")


class TestParsingEdgeCases:
    """Test parsing edge cases."""
    
    def test_extra_whitespace_handled(self):
        """Extra whitespace is handled."""
        spec = parse_order_spec("  name   desc  ")
        assert spec.column == "name"
        assert spec.direction == "desc"
    
    def test_tabs_handled(self):
        """Tabs are handled like spaces."""
        spec = parse_order_spec("name\tdesc")
        assert spec.column == "name"
        assert spec.direction == "desc"
    
    def test_newline_handled(self):
        """Newlines are handled like spaces."""
        spec = parse_order_spec("name\ndesc")
        assert spec.column == "name"
        assert spec.direction == "desc"
    
    def test_list_with_empty_string(self):
        """List with empty string raises."""
        with pytest.raises(ValueError):
            parse_order_by(["name", ""])
    
    def test_list_with_whitespace_only(self):
        """List with whitespace-only string raises."""
        with pytest.raises(ValueError):
            parse_order_by(["name", "   "])


class TestValidateOrderBy:
    """Test validate_order_by edge cases."""
    
    def test_none_with_allowed(self):
        """None with allowed columns returns empty."""
        result = validate_order_by(None, allowed_columns=["name"])
        assert result == []
    
    def test_column_not_in_allowed(self):
        """Column not in allowed raises."""
        with pytest.raises(ValueError) as exc:
            validate_order_by("invalid", allowed_columns=["name", "id"])
        assert "invalid" in str(exc.value)
    
    def test_one_of_many_invalid(self):
        """One invalid column in list raises."""
        with pytest.raises(ValueError):
            validate_order_by(
                ["name", "invalid", "id"],
                allowed_columns=["name", "id"]
            )
    
    def test_empty_allowed_columns(self):
        """Empty allowed_columns list means nothing allowed."""
        with pytest.raises(ValueError):
            validate_order_by("name", allowed_columns=[])


class TestNormalizeOrderBy:
    """Test normalize_order_by edge cases."""
    
    def test_normalize_none(self):
        """Normalize None returns None."""
        result = normalize_order_by(None)
        assert result is None
    
    def test_normalize_preserves_count(self):
        """Normalize preserves column count."""
        result = normalize_order_by(["a", "b", "c"])
        assert len(result) == 3
    
    def test_normalize_uppercase_to_lower(self):
        """Normalize uppercases to lowercase."""
        result = normalize_order_by("NAME DESC")
        assert result == ["name desc"]


class TestOrderingConfigEdgeCases:
    """Test OrderingConfig edge cases."""
    
    def test_len_empty(self):
        """len() on empty config."""
        config = OrderingConfig()
        assert len(config) == 0
    
    def test_bool_empty(self):
        """bool() on empty config is False."""
        config = OrderingConfig()
        assert not config
    
    def test_bool_with_specs(self):
        """bool() with specs is True."""
        config = OrderingConfig.from_order_by("name")
        assert config
    
    def test_repr_empty(self):
        """repr() on empty config."""
        config = OrderingConfig()
        assert "OrderingConfig" in repr(config)
    
    def test_to_sql_empty(self):
        """to_sql on empty returns empty string."""
        config = OrderingConfig()
        assert config.to_sql() == ""
    
    def test_get_columns_empty(self):
        """get_columns on empty returns empty list."""
        config = OrderingConfig()
        assert config.get_columns() == []


class TestSortItemsEdgeCases:
    """Test sort_items edge cases."""
    
    def test_empty_items(self):
        """Empty items list."""
        result = sort_items([], [OrderSpec("name")])
        assert result == []
    
    def test_single_item(self):
        """Single item list."""
        items = [MockItem(name="A")]
        specs = [OrderSpec("name")]
        result = sort_items(items, specs)
        assert len(result) == 1
    
    def test_missing_attribute(self):
        """Item missing sort attribute returns None."""
        items = [MockItem(name="A"), MockItem(other="B")]
        specs = [OrderSpec("name")]
        result = sort_items(items, specs)
        # Should handle gracefully - None values
        assert len(result) == 2
    
    def test_all_none_values(self):
        """All items have None for sort column."""
        items = [
            MockItem(name=None),
            MockItem(name=None),
            MockItem(name=None),
        ]
        specs = [OrderSpec("name")]
        result = sort_items(items, specs)
        assert len(result) == 3


class TestRelationshipEdgeCases:
    """Test has_many/many_to_many edge cases."""
    
    def test_has_many_empty_list_order(self):
        """has_many with empty list order_by."""
        rel = has_many(MockItem, order_by=[])
        rel.rel_name = "items"
        
        if rel.ordering:
            assert not rel.ordering.has_ordering
    
    def test_many_to_many_empty_list_order(self):
        """many_to_many with empty list order_by."""
        rel = many_to_many(MockItem, order_by=[])
        rel.rel_name = "items"
        
        if rel.ordering:
            assert not rel.ordering.has_ordering
    
    def test_ordering_accessed_multiple_times(self):
        """Ordering property cached on multiple access."""
        rel = has_many(MockItem, order_by="name")
        rel.rel_name = "items"
        
        ordering1 = rel.ordering
        ordering2 = rel.ordering
        ordering3 = rel.ordering
        
        assert ordering1 is ordering2
        assert ordering2 is ordering3


class TestTypeErrors:
    """Test type error handling."""
    
    def test_order_by_int(self):
        """order_by as int raises."""
        with pytest.raises(TypeError):
            parse_order_by(123)
    
    def test_order_by_float(self):
        """order_by as float raises."""
        with pytest.raises(TypeError):
            parse_order_by(1.5)
    
    def test_order_by_bool(self):
        """order_by as bool raises."""
        with pytest.raises(TypeError):
            parse_order_by(True)
    
    def test_order_by_set(self):
        """order_by as set raises."""
        with pytest.raises(TypeError):
            parse_order_by({"name", "id"})

