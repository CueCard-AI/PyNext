"""
Tests for asc/desc direction handling.

Tests cover:
- Default direction (asc)
- Explicit asc
- Explicit desc
- Case insensitivity
- Direction in SQL generation
"""

import pytest

from pynext.db.relationships.ordering import (
    OrderSpec,
    OrderingConfig,
    parse_order_by,
    parse_order_spec,
    build_order_clause,
    asc,
    desc,
)
from pynext.db.relationships.core import has_many


# =============================================================================
# Mock Models
# =============================================================================

class MockPost:
    """Mock Post model."""
    pass


# =============================================================================
# Test: Default Direction
# =============================================================================

class TestDefaultDirection:
    """Test default direction is ascending."""
    
    def test_order_spec_default(self):
        """OrderSpec defaults to asc."""
        spec = OrderSpec("name")
        assert spec.direction == "asc"
    
    def test_parse_column_only(self):
        """Parsing column only defaults to asc."""
        spec = parse_order_spec("name")
        assert spec.direction == "asc"
    
    def test_parse_order_by_default(self):
        """parse_order_by defaults to asc."""
        specs = parse_order_by("name")
        assert specs[0].direction == "asc"
    
    def test_has_many_default(self):
        """has_many order_by defaults to asc."""
        rel = has_many(MockPost, order_by="name")
        rel.rel_name = "posts"
        
        assert rel.ordering.specs[0].direction == "asc"
    
    def test_sql_default(self):
        """SQL generation includes ASC for default."""
        spec = OrderSpec("name")
        assert spec.to_sql() == "name ASC"


class TestExplicitAsc:
    """Test explicit ascending direction."""
    
    def test_order_spec_explicit_asc(self):
        """OrderSpec with explicit asc."""
        spec = OrderSpec("name", "asc")
        assert spec.direction == "asc"
    
    def test_parse_explicit_asc(self):
        """Parse explicit asc."""
        spec = parse_order_spec("name asc")
        assert spec.direction == "asc"
    
    def test_sql_explicit_asc(self):
        """SQL for explicit asc."""
        spec = parse_order_spec("name asc")
        assert spec.to_sql() == "name ASC"
    
    def test_asc_function(self):
        """asc() function creates ascending spec."""
        spec = asc("name")
        assert spec.direction == "asc"


class TestExplicitDesc:
    """Test explicit descending direction."""
    
    def test_order_spec_explicit_desc(self):
        """OrderSpec with explicit desc."""
        spec = OrderSpec("name", "desc")
        assert spec.direction == "desc"
    
    def test_parse_explicit_desc(self):
        """Parse explicit desc."""
        spec = parse_order_spec("name desc")
        assert spec.direction == "desc"
    
    def test_sql_explicit_desc(self):
        """SQL for explicit desc."""
        spec = parse_order_spec("name desc")
        assert spec.to_sql() == "name DESC"
    
    def test_desc_function(self):
        """desc() function creates descending spec."""
        spec = desc("name")
        assert spec.direction == "desc"


class TestCaseInsensitivity:
    """Test direction is case insensitive."""
    
    def test_asc_uppercase(self):
        """ASC uppercase works."""
        spec = parse_order_spec("name ASC")
        assert spec.direction == "asc"
    
    def test_desc_uppercase(self):
        """DESC uppercase works."""
        spec = parse_order_spec("name DESC")
        assert spec.direction == "desc"
    
    def test_asc_mixed_case(self):
        """Asc mixed case works."""
        spec = parse_order_spec("name Asc")
        assert spec.direction == "asc"
    
    def test_desc_mixed_case(self):
        """Desc mixed case works."""
        spec = parse_order_spec("name Desc")
        assert spec.direction == "desc"
    
    def test_order_spec_normalizes(self):
        """OrderSpec normalizes to lowercase."""
        spec = OrderSpec("name", "DESC")
        assert spec.direction == "desc"
        
        spec2 = OrderSpec("name", "ASC")
        assert spec2.direction == "asc"


class TestDirectionValidation:
    """Test direction validation."""
    
    def test_invalid_direction_raises(self):
        """Invalid direction raises ValueError."""
        with pytest.raises(ValueError):
            OrderSpec("name", "ascending")
    
    def test_invalid_direction_desc_typo(self):
        """Typo in desc raises."""
        with pytest.raises(ValueError):
            OrderSpec("name", "descc")
    
    def test_invalid_direction_empty(self):
        """Empty direction raises."""
        with pytest.raises(ValueError):
            OrderSpec("name", "")


class TestDirectionInMultipleColumns:
    """Test direction in multiple column ordering."""
    
    def test_all_asc(self):
        """All columns ascending."""
        specs = parse_order_by(["a", "b", "c"])
        for spec in specs:
            assert spec.direction == "asc"
    
    def test_all_desc(self):
        """All columns descending."""
        specs = parse_order_by(["a desc", "b desc", "c desc"])
        for spec in specs:
            assert spec.direction == "desc"
    
    def test_mixed_directions(self):
        """Mixed directions."""
        specs = parse_order_by(["a desc", "b", "c desc", "d"])
        assert specs[0].direction == "desc"
        assert specs[1].direction == "asc"
        assert specs[2].direction == "desc"
        assert specs[3].direction == "asc"


class TestDirectionWithNulls:
    """Test direction combined with NULLS."""
    
    def test_asc_nulls_first(self):
        """ASC with NULLS FIRST."""
        spec = parse_order_spec("name asc nulls first")
        assert spec.direction == "asc"
        assert spec.nulls == "first"
    
    def test_desc_nulls_last(self):
        """DESC with NULLS LAST."""
        spec = parse_order_spec("name desc nulls last")
        assert spec.direction == "desc"
        assert spec.nulls == "last"
    
    def test_default_with_nulls(self):
        """Default direction with NULLS."""
        spec = parse_order_spec("name nulls last")
        assert spec.direction == "asc"
        assert spec.nulls == "last"


class TestDirectionSqlOutput:
    """Test direction in SQL output."""
    
    def test_asc_uppercase_in_sql(self):
        """ASC is uppercase in SQL."""
        spec = OrderSpec("name", "asc")
        assert "ASC" in spec.to_sql()
    
    def test_desc_uppercase_in_sql(self):
        """DESC is uppercase in SQL."""
        spec = OrderSpec("name", "desc")
        assert "DESC" in spec.to_sql()
    
    def test_multiple_directions_sql(self):
        """Multiple directions in SQL."""
        specs = parse_order_by(["a desc", "b"])
        sql = build_order_clause(specs)
        assert "a DESC" in sql
        assert "b ASC" in sql


class TestDirectionWithTableAlias:
    """Test direction with table alias."""
    
    def test_asc_with_alias(self):
        """ASC with table alias."""
        spec = OrderSpec("name", "asc")
        assert spec.to_sql("t") == "t.name ASC"
    
    def test_desc_with_alias(self):
        """DESC with table alias."""
        spec = OrderSpec("name", "desc")
        assert spec.to_sql("t") == "t.name DESC"

