"""
Tests for OrderSpec parsing and validation.

Tests cover:
- OrderSpec creation
- parse_order_spec() function
- parse_order_by() function
- OrderingConfig class
- SQL generation
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
    asc,
    desc,
)


# =============================================================================
# Test: OrderSpec Creation
# =============================================================================

class TestOrderSpecCreation:
    """Test OrderSpec class creation."""
    
    def test_create_basic(self):
        """Create basic OrderSpec."""
        spec = OrderSpec("name", "asc")
        assert spec.column == "name"
        assert spec.direction == "asc"
        assert spec.nulls is None
    
    def test_create_desc(self):
        """Create descending OrderSpec."""
        spec = OrderSpec("created_at", "desc")
        assert spec.column == "created_at"
        assert spec.direction == "desc"
    
    def test_create_with_nulls_first(self):
        """Create OrderSpec with NULLS FIRST."""
        spec = OrderSpec("priority", "desc", "first")
        assert spec.column == "priority"
        assert spec.direction == "desc"
        assert spec.nulls == "first"
    
    def test_create_with_nulls_last(self):
        """Create OrderSpec with NULLS LAST."""
        spec = OrderSpec("due_date", "asc", "last")
        assert spec.nulls == "last"
    
    def test_default_direction_is_asc(self):
        """Default direction is ascending."""
        spec = OrderSpec("name")
        assert spec.direction == "asc"
    
    def test_direction_normalized_to_lowercase(self):
        """Direction is normalized to lowercase."""
        spec = OrderSpec("name", "DESC")
        assert spec.direction == "desc"
        
        spec2 = OrderSpec("name", "ASC")
        assert spec2.direction == "asc"
    
    def test_nulls_normalized_to_lowercase(self):
        """Nulls is normalized to lowercase."""
        spec = OrderSpec("name", "asc", "FIRST")
        assert spec.nulls == "first"
        
        spec2 = OrderSpec("name", "asc", "LAST")
        assert spec2.nulls == "last"


class TestOrderSpecValidation:
    """Test OrderSpec validation."""
    
    def test_invalid_direction_raises(self):
        """Invalid direction raises ValueError."""
        with pytest.raises(ValueError) as exc:
            OrderSpec("name", "ascending")
        assert "direction" in str(exc.value).lower()
    
    def test_invalid_nulls_raises(self):
        """Invalid nulls raises ValueError."""
        with pytest.raises(ValueError) as exc:
            OrderSpec("name", "asc", "beginning")
        assert "nulls" in str(exc.value).lower()
    
    def test_empty_column_raises(self):
        """Empty column name raises ValueError."""
        with pytest.raises(ValueError) as exc:
            OrderSpec("", "asc")
        assert "column" in str(exc.value).lower()
    
    def test_invalid_column_name_raises(self):
        """Invalid column name raises ValueError."""
        with pytest.raises(ValueError) as exc:
            OrderSpec("name; DROP TABLE users", "asc")
        assert "column" in str(exc.value).lower()
    
    def test_column_with_spaces_invalid(self):
        """Column with spaces is invalid."""
        with pytest.raises(ValueError):
            OrderSpec("column name", "asc")
    
    def test_valid_column_names(self):
        """Valid column names work."""
        valid_names = ["name", "created_at", "_private", "Column1", "a"]
        for name in valid_names:
            spec = OrderSpec(name, "asc")
            assert spec.column == name


class TestOrderSpecToSql:
    """Test OrderSpec to_sql() method."""
    
    def test_simple_asc(self):
        """Simple ascending to SQL."""
        spec = OrderSpec("name", "asc")
        assert spec.to_sql() == "name ASC"
    
    def test_simple_desc(self):
        """Simple descending to SQL."""
        spec = OrderSpec("created_at", "desc")
        assert spec.to_sql() == "created_at DESC"
    
    def test_with_nulls_first(self):
        """With NULLS FIRST to SQL."""
        spec = OrderSpec("priority", "desc", "first")
        assert spec.to_sql() == "priority DESC NULLS FIRST"
    
    def test_with_nulls_last(self):
        """With NULLS LAST to SQL."""
        spec = OrderSpec("due_date", "asc", "last")
        assert spec.to_sql() == "due_date ASC NULLS LAST"
    
    def test_with_table_alias(self):
        """With table alias."""
        spec = OrderSpec("name", "asc")
        assert spec.to_sql("t") == "t.name ASC"
    
    def test_with_alias_and_nulls(self):
        """With table alias and NULLS."""
        spec = OrderSpec("priority", "desc", "last")
        assert spec.to_sql("posts") == "posts.priority DESC NULLS LAST"


class TestOrderSpecStr:
    """Test OrderSpec string representations."""
    
    def test_str_simple(self):
        """Simple __str__."""
        spec = OrderSpec("name", "asc")
        assert str(spec) == "name asc"
    
    def test_str_with_nulls(self):
        """__str__ with nulls."""
        spec = OrderSpec("priority", "desc", "last")
        assert str(spec) == "priority desc nulls last"
    
    def test_repr(self):
        """__repr__ format."""
        spec = OrderSpec("name", "asc")
        assert "OrderSpec" in repr(spec)
        assert "name" in repr(spec)
    
    def test_repr_with_nulls(self):
        """__repr__ includes nulls."""
        spec = OrderSpec("priority", "desc", "first")
        assert "nulls='first'" in repr(spec)


# =============================================================================
# Test: parse_order_spec
# =============================================================================

class TestParseOrderSpec:
    """Test parse_order_spec() function."""
    
    def test_column_only(self):
        """Parse column only (default asc)."""
        spec = parse_order_spec("name")
        assert spec.column == "name"
        assert spec.direction == "asc"
    
    def test_column_asc(self):
        """Parse column with asc."""
        spec = parse_order_spec("name asc")
        assert spec.column == "name"
        assert spec.direction == "asc"
    
    def test_column_desc(self):
        """Parse column with desc."""
        spec = parse_order_spec("created_at desc")
        assert spec.column == "created_at"
        assert spec.direction == "desc"
    
    def test_case_insensitive(self):
        """Parse is case insensitive."""
        spec1 = parse_order_spec("NAME DESC")
        assert spec1.column == "name"
        assert spec1.direction == "desc"
        
        spec2 = parse_order_spec("Created_At ASC")
        assert spec2.column == "created_at"
        assert spec2.direction == "asc"
    
    def test_nulls_first(self):
        """Parse with NULLS FIRST."""
        spec = parse_order_spec("priority desc nulls first")
        assert spec.column == "priority"
        assert spec.direction == "desc"
        assert spec.nulls == "first"
    
    def test_nulls_last(self):
        """Parse with NULLS LAST."""
        spec = parse_order_spec("due_date nulls last")
        assert spec.column == "due_date"
        assert spec.direction == "asc"
        assert spec.nulls == "last"
    
    def test_extra_whitespace(self):
        """Handle extra whitespace."""
        spec = parse_order_spec("  name   desc   ")
        assert spec.column == "name"
        assert spec.direction == "desc"
    
    def test_empty_raises(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError):
            parse_order_spec("")
    
    def test_whitespace_only_raises(self):
        """Whitespace only raises ValueError."""
        with pytest.raises(ValueError):
            parse_order_spec("   ")
    
    def test_invalid_format_raises(self):
        """Invalid format raises ValueError."""
        with pytest.raises(ValueError):
            parse_order_spec("name desc extra stuff")


# =============================================================================
# Test: parse_order_by
# =============================================================================

class TestParseOrderBy:
    """Test parse_order_by() function."""
    
    def test_none_returns_empty(self):
        """None returns empty list."""
        result = parse_order_by(None)
        assert result == []
    
    def test_single_string(self):
        """Parse single string."""
        result = parse_order_by("name desc")
        assert len(result) == 1
        assert result[0].column == "name"
        assert result[0].direction == "desc"
    
    def test_list_of_strings(self):
        """Parse list of strings."""
        result = parse_order_by(["pinned desc", "name asc"])
        assert len(result) == 2
        assert result[0].column == "pinned"
        assert result[0].direction == "desc"
        assert result[1].column == "name"
        assert result[1].direction == "asc"
    
    def test_tuple_of_strings(self):
        """Parse tuple of strings."""
        result = parse_order_by(("a", "b desc"))
        assert len(result) == 2
        assert result[0].column == "a"
        assert result[1].column == "b"
    
    def test_single_item_list(self):
        """Parse single item list."""
        result = parse_order_by(["created_at"])
        assert len(result) == 1
        assert result[0].column == "created_at"
    
    def test_invalid_type_raises(self):
        """Invalid type raises TypeError."""
        with pytest.raises(TypeError):
            parse_order_by(123)
    
    def test_empty_list_returns_empty(self):
        """Empty list returns empty list."""
        result = parse_order_by([])
        assert result == []


# =============================================================================
# Test: build_order_clause
# =============================================================================

class TestBuildOrderClause:
    """Test build_order_clause() function."""
    
    def test_empty_specs(self):
        """Empty specs returns empty string."""
        result = build_order_clause([])
        assert result == ""
    
    def test_single_spec(self):
        """Single spec."""
        specs = [OrderSpec("name", "asc")]
        result = build_order_clause(specs)
        assert result == "ORDER BY name ASC"
    
    def test_multiple_specs(self):
        """Multiple specs."""
        specs = [OrderSpec("pinned", "desc"), OrderSpec("name", "asc")]
        result = build_order_clause(specs)
        assert result == "ORDER BY pinned DESC, name ASC"
    
    def test_with_table_alias(self):
        """With table alias."""
        specs = [OrderSpec("name", "asc")]
        result = build_order_clause(specs, table_alias="t")
        assert result == "ORDER BY t.name ASC"
    
    def test_without_keyword(self):
        """Without ORDER BY keyword."""
        specs = [OrderSpec("name", "asc")]
        result = build_order_clause(specs, include_keyword=False)
        assert result == "name ASC"
    
    def test_with_nulls(self):
        """With NULLS handling."""
        specs = [OrderSpec("priority", "desc", "first")]
        result = build_order_clause(specs)
        assert result == "ORDER BY priority DESC NULLS FIRST"


class TestBuildOrderColumns:
    """Test build_order_columns() function."""
    
    def test_empty(self):
        """Empty specs returns empty list."""
        result = build_order_columns([])
        assert result == []
    
    def test_single(self):
        """Single spec."""
        specs = [OrderSpec("name", "asc")]
        result = build_order_columns(specs)
        assert result == ["name ASC"]
    
    def test_multiple(self):
        """Multiple specs."""
        specs = [OrderSpec("a", "desc"), OrderSpec("b", "asc")]
        result = build_order_columns(specs)
        assert result == ["a DESC", "b ASC"]
    
    def test_with_alias(self):
        """With table alias."""
        specs = [OrderSpec("name", "asc")]
        result = build_order_columns(specs, "t")
        assert result == ["t.name ASC"]


# =============================================================================
# Test: validate_order_by
# =============================================================================

class TestValidateOrderBy:
    """Test validate_order_by() function."""
    
    def test_valid_column(self):
        """Valid column passes."""
        result = validate_order_by("name", allowed_columns=["name", "id"])
        assert len(result) == 1
        assert result[0].column == "name"
    
    def test_invalid_column_raises(self):
        """Invalid column raises ValueError."""
        with pytest.raises(ValueError) as exc:
            validate_order_by("invalid", allowed_columns=["name", "id"])
        assert "invalid" in str(exc.value)
    
    def test_no_allowed_columns(self):
        """No allowed_columns means any column ok."""
        result = validate_order_by("anything")
        assert len(result) == 1
    
    def test_multiple_columns_validated(self):
        """All columns in list are validated."""
        result = validate_order_by(
            ["name", "id desc"],
            allowed_columns=["name", "id", "created_at"]
        )
        assert len(result) == 2
    
    def test_one_invalid_in_list_raises(self):
        """One invalid column in list raises."""
        with pytest.raises(ValueError):
            validate_order_by(
                ["name", "invalid"],
                allowed_columns=["name", "id"]
            )


# =============================================================================
# Test: normalize_order_by
# =============================================================================

class TestNormalizeOrderBy:
    """Test normalize_order_by() function."""
    
    def test_none_returns_none(self):
        """None returns None."""
        result = normalize_order_by(None)
        assert result is None
    
    def test_single_normalized(self):
        """Single string normalized."""
        result = normalize_order_by("NAME DESC")
        assert result == ["name desc"]
    
    def test_list_normalized(self):
        """List normalized."""
        result = normalize_order_by(["PINNED desc", "name ASC"])
        assert result == ["pinned desc", "name asc"]
    
    def test_adds_direction(self):
        """Adds direction if missing."""
        result = normalize_order_by("name")
        assert result == ["name asc"]


# =============================================================================
# Test: OrderingConfig
# =============================================================================

class TestOrderingConfig:
    """Test OrderingConfig class."""
    
    def test_from_order_by_none(self):
        """Create from None."""
        config = OrderingConfig.from_order_by(None)
        assert not config.has_ordering
        assert len(config) == 0
    
    def test_from_order_by_string(self):
        """Create from string."""
        config = OrderingConfig.from_order_by("name desc")
        assert config.has_ordering
        assert len(config) == 1
    
    def test_from_order_by_list(self):
        """Create from list."""
        config = OrderingConfig.from_order_by(["a", "b desc"])
        assert len(config) == 2
    
    def test_has_ordering_false(self):
        """has_ordering False when empty."""
        config = OrderingConfig()
        assert not config.has_ordering
        assert not config
    
    def test_has_ordering_true(self):
        """has_ordering True when has specs."""
        config = OrderingConfig.from_order_by("name")
        assert config.has_ordering
        assert config
    
    def test_to_sql(self):
        """to_sql generates clause."""
        config = OrderingConfig.from_order_by("name desc")
        assert config.to_sql() == "ORDER BY name DESC"
    
    def test_get_columns(self):
        """get_columns returns list."""
        config = OrderingConfig.from_order_by(["a", "b desc"])
        columns = config.get_columns()
        assert columns == ["a ASC", "b DESC"]
    
    def test_merge_with(self):
        """merge_with combines configs."""
        config1 = OrderingConfig.from_order_by("a")
        config2 = OrderingConfig.from_order_by("b desc")
        merged = config1.merge_with(config2)
        assert len(merged) == 2
        assert merged.specs[0].column == "a"
        assert merged.specs[1].column == "b"
    
    def test_override_with_replaces(self):
        """override_with replaces when other has ordering."""
        config1 = OrderingConfig.from_order_by("a")
        config2 = OrderingConfig.from_order_by("b")
        result = config1.override_with(config2)
        assert len(result) == 1
        assert result.specs[0].column == "b"
    
    def test_override_with_keeps_when_empty(self):
        """override_with keeps self when other is empty."""
        config1 = OrderingConfig.from_order_by("a")
        config2 = OrderingConfig()
        result = config1.override_with(config2)
        assert len(result) == 1
        assert result.specs[0].column == "a"
    
    def test_repr(self):
        """__repr__ works."""
        config = OrderingConfig.from_order_by("name")
        assert "OrderingConfig" in repr(config)


# =============================================================================
# Test: asc/desc Functions
# =============================================================================

class TestAscDescFunctions:
    """Test asc() and desc() convenience functions."""
    
    def test_asc_basic(self):
        """asc() creates ascending OrderSpec."""
        spec = asc("name")
        assert spec.column == "name"
        assert spec.direction == "asc"
        assert spec.nulls is None
    
    def test_asc_with_nulls(self):
        """asc() with nulls."""
        spec = asc("due_date", "last")
        assert spec.column == "due_date"
        assert spec.direction == "asc"
        assert spec.nulls == "last"
    
    def test_desc_basic(self):
        """desc() creates descending OrderSpec."""
        spec = desc("created_at")
        assert spec.column == "created_at"
        assert spec.direction == "desc"
    
    def test_desc_with_nulls(self):
        """desc() with nulls."""
        spec = desc("priority", "first")
        assert spec.nulls == "first"

