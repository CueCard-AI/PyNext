"""
Tests for NULLS FIRST/LAST handling.

Tests cover:
- NULLS FIRST
- NULLS LAST
- Default NULL behavior
- SQL generation with NULLS
- Validation
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
    sort_items,
)
from pynext.db.relationships.core import has_many, many_to_many


# =============================================================================
# Mock Models
# =============================================================================

class MockTask:
    """Mock Task with nullable fields."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")
        self.priority = kwargs.get("priority")
        self.due_date = kwargs.get("due_date")


# =============================================================================
# Test: NULLS FIRST
# =============================================================================

class TestNullsFirst:
    """Test NULLS FIRST handling."""
    
    def test_parse_nulls_first(self):
        """Parse NULLS FIRST."""
        spec = parse_order_spec("priority nulls first")
        assert spec.nulls == "first"
    
    def test_order_spec_nulls_first(self):
        """OrderSpec with NULLS FIRST."""
        spec = OrderSpec("priority", "asc", "first")
        assert spec.nulls == "first"
    
    def test_sql_nulls_first(self):
        """SQL with NULLS FIRST."""
        spec = OrderSpec("priority", "desc", "first")
        sql = spec.to_sql()
        assert "NULLS FIRST" in sql
    
    def test_with_asc(self):
        """NULLS FIRST with ASC."""
        spec = parse_order_spec("priority asc nulls first")
        assert spec.direction == "asc"
        assert spec.nulls == "first"
        assert spec.to_sql() == "priority ASC NULLS FIRST"
    
    def test_with_desc(self):
        """NULLS FIRST with DESC."""
        spec = parse_order_spec("priority desc nulls first")
        assert spec.direction == "desc"
        assert spec.nulls == "first"
        assert spec.to_sql() == "priority DESC NULLS FIRST"


class TestNullsLast:
    """Test NULLS LAST handling."""
    
    def test_parse_nulls_last(self):
        """Parse NULLS LAST."""
        spec = parse_order_spec("due_date nulls last")
        assert spec.nulls == "last"
    
    def test_order_spec_nulls_last(self):
        """OrderSpec with NULLS LAST."""
        spec = OrderSpec("due_date", "asc", "last")
        assert spec.nulls == "last"
    
    def test_sql_nulls_last(self):
        """SQL with NULLS LAST."""
        spec = OrderSpec("due_date", "asc", "last")
        sql = spec.to_sql()
        assert "NULLS LAST" in sql
    
    def test_with_asc(self):
        """NULLS LAST with ASC."""
        spec = parse_order_spec("due_date asc nulls last")
        assert spec.direction == "asc"
        assert spec.nulls == "last"
        assert spec.to_sql() == "due_date ASC NULLS LAST"
    
    def test_with_desc(self):
        """NULLS LAST with DESC."""
        spec = parse_order_spec("due_date desc nulls last")
        assert spec.direction == "desc"
        assert spec.nulls == "last"
        assert spec.to_sql() == "due_date DESC NULLS LAST"


class TestDefaultNullBehavior:
    """Test default NULL behavior (no NULLS clause)."""
    
    def test_default_is_none(self):
        """Default nulls is None."""
        spec = OrderSpec("name")
        assert spec.nulls is None
    
    def test_parse_without_nulls(self):
        """Parsing without NULLS gives None."""
        spec = parse_order_spec("name desc")
        assert spec.nulls is None
    
    def test_sql_without_nulls(self):
        """SQL without NULLS clause."""
        spec = OrderSpec("name", "desc")
        sql = spec.to_sql()
        assert "NULLS" not in sql


class TestNullsCaseInsensitivity:
    """Test NULLS is case insensitive."""
    
    def test_nulls_uppercase(self):
        """NULLS FIRST uppercase."""
        spec = parse_order_spec("name NULLS FIRST")
        assert spec.nulls == "first"
    
    def test_first_uppercase(self):
        """FIRST uppercase."""
        spec = parse_order_spec("name nulls FIRST")
        assert spec.nulls == "first"
    
    def test_last_uppercase(self):
        """LAST uppercase."""
        spec = parse_order_spec("name nulls LAST")
        assert spec.nulls == "last"
    
    def test_mixed_case(self):
        """Mixed case."""
        spec = parse_order_spec("name Nulls First")
        assert spec.nulls == "first"
    
    def test_order_spec_normalizes(self):
        """OrderSpec normalizes nulls to lowercase."""
        spec = OrderSpec("name", "asc", "FIRST")
        assert spec.nulls == "first"
        
        spec2 = OrderSpec("name", "asc", "LAST")
        assert spec2.nulls == "last"


class TestNullsValidation:
    """Test NULLS validation."""
    
    def test_invalid_nulls_raises(self):
        """Invalid nulls value raises."""
        with pytest.raises(ValueError):
            OrderSpec("name", "asc", "beginning")
    
    def test_invalid_nulls_middle(self):
        """Invalid: middle is not valid."""
        with pytest.raises(ValueError):
            OrderSpec("name", "asc", "middle")
    
    def test_invalid_nulls_never(self):
        """Invalid: never is not valid."""
        with pytest.raises(ValueError):
            OrderSpec("name", "asc", "never")


class TestNullsInMultipleColumns:
    """Test NULLS in multiple column ordering."""
    
    def test_first_column_has_nulls(self):
        """First column has NULLS."""
        specs = parse_order_by(["priority desc nulls first", "name"])
        assert specs[0].nulls == "first"
        assert specs[1].nulls is None
    
    def test_second_column_has_nulls(self):
        """Second column has NULLS."""
        specs = parse_order_by(["name", "due_date nulls last"])
        assert specs[0].nulls is None
        assert specs[1].nulls == "last"
    
    def test_both_columns_have_nulls(self):
        """Both columns have NULLS."""
        specs = parse_order_by([
            "priority desc nulls first",
            "due_date nulls last"
        ])
        assert specs[0].nulls == "first"
        assert specs[1].nulls == "last"
    
    def test_sql_multiple_with_nulls(self):
        """SQL with multiple columns and NULLS."""
        specs = parse_order_by([
            "priority desc nulls first",
            "name",
            "due_date nulls last"
        ])
        sql = build_order_clause(specs)
        assert "priority DESC NULLS FIRST" in sql
        assert "name ASC" in sql
        assert "due_date ASC NULLS LAST" in sql


class TestNullsInRelationships:
    """Test NULLS in has_many/many_to_many."""
    
    def test_has_many_nulls_first(self):
        """has_many with NULLS FIRST."""
        rel = has_many(MockTask, order_by="priority desc nulls first")
        rel.rel_name = "tasks"
        
        assert rel.ordering.specs[0].nulls == "first"
    
    def test_has_many_nulls_last(self):
        """has_many with NULLS LAST."""
        rel = has_many(MockTask, order_by="due_date nulls last")
        rel.rel_name = "tasks"
        
        assert rel.ordering.specs[0].nulls == "last"
    
    def test_m2m_nulls_first(self):
        """many_to_many with NULLS FIRST."""
        rel = many_to_many(MockTask, order_by="priority desc nulls first")
        rel.rel_name = "tasks"
        
        assert rel.ordering.specs[0].nulls == "first"
    
    def test_m2m_nulls_last(self):
        """many_to_many with NULLS LAST."""
        rel = many_to_many(MockTask, order_by="due_date nulls last")
        rel.rel_name = "tasks"
        
        assert rel.ordering.specs[0].nulls == "last"


class TestNullsWithConvenienceFunctions:
    """Test NULLS with asc()/desc() functions."""
    
    def test_asc_nulls_first(self):
        """asc() with NULLS FIRST."""
        spec = asc("priority", "first")
        assert spec.direction == "asc"
        assert spec.nulls == "first"
    
    def test_asc_nulls_last(self):
        """asc() with NULLS LAST."""
        spec = asc("priority", "last")
        assert spec.direction == "asc"
        assert spec.nulls == "last"
    
    def test_desc_nulls_first(self):
        """desc() with NULLS FIRST."""
        spec = desc("priority", "first")
        assert spec.direction == "desc"
        assert spec.nulls == "first"
    
    def test_desc_nulls_last(self):
        """desc() with NULLS LAST."""
        spec = desc("priority", "last")
        assert spec.direction == "desc"
        assert spec.nulls == "last"


class TestNullsSqlGeneration:
    """Test SQL generation with NULLS."""
    
    def test_full_sql_nulls_first(self):
        """Full SQL with NULLS FIRST."""
        spec = OrderSpec("priority", "desc", "first")
        sql = spec.to_sql()
        assert sql == "priority DESC NULLS FIRST"
    
    def test_full_sql_nulls_last(self):
        """Full SQL with NULLS LAST."""
        spec = OrderSpec("due_date", "asc", "last")
        sql = spec.to_sql()
        assert sql == "due_date ASC NULLS LAST"
    
    def test_with_table_alias(self):
        """NULLS with table alias."""
        spec = OrderSpec("priority", "desc", "first")
        sql = spec.to_sql("t")
        assert sql == "t.priority DESC NULLS FIRST"
    
    def test_ordering_config_to_sql(self):
        """OrderingConfig to_sql with NULLS."""
        config = OrderingConfig.from_order_by("priority desc nulls first")
        sql = config.to_sql()
        assert sql == "ORDER BY priority DESC NULLS FIRST"


class TestSortItemsWithNulls:
    """Test sort_items with NULLS handling."""
    
    def test_nulls_first_sorting(self):
        """Null values sorted first."""
        tasks = [
            MockTask(name="A", priority=1),
            MockTask(name="B", priority=None),
            MockTask(name="C", priority=2),
        ]
        
        specs = [OrderSpec("priority", "asc", "first")]
        sorted_tasks = sort_items(tasks, specs)
        
        # Null should be first
        assert sorted_tasks[0].name == "B"
    
    def test_nulls_last_sorting(self):
        """Null values sorted last."""
        tasks = [
            MockTask(name="A", priority=None),
            MockTask(name="B", priority=1),
            MockTask(name="C", priority=2),
        ]
        
        specs = [OrderSpec("priority", "asc", "last")]
        sorted_tasks = sort_items(tasks, specs)
        
        # Null should be last
        assert sorted_tasks[-1].name == "A"

