"""
Tests for query-time ordering override.

Tests cover:
- Overriding relationship ordering at query time
- Merging orderings
- OrderingConfig override_with and merge_with
"""

import pytest
from typing import List

from pynext.db.relationships.ordering import (
    OrderSpec,
    OrderingConfig,
    parse_order_by,
    build_order_clause,
)
from pynext.db.relationships.core import has_many, many_to_many


# =============================================================================
# Mock Models
# =============================================================================

class MockPost:
    """Mock Post model."""
    pass


class MockComment:
    """Mock Comment model."""
    pass


# =============================================================================
# Test: OrderingConfig.override_with
# =============================================================================

class TestOverrideWith:
    """Test OrderingConfig.override_with method."""
    
    def test_override_replaces_when_has_ordering(self):
        """Override replaces when other has ordering."""
        base = OrderingConfig.from_order_by("created_at desc")
        override = OrderingConfig.from_order_by("name asc")
        
        result = base.override_with(override)
        
        assert len(result.specs) == 1
        assert result.specs[0].column == "name"
    
    def test_override_keeps_when_empty(self):
        """Override keeps base when other is empty."""
        base = OrderingConfig.from_order_by("created_at desc")
        override = OrderingConfig()
        
        result = base.override_with(override)
        
        assert len(result.specs) == 1
        assert result.specs[0].column == "created_at"
    
    def test_override_keeps_when_none(self):
        """Override keeps base when other has no specs."""
        base = OrderingConfig.from_order_by("created_at desc")
        override = OrderingConfig(specs=[])
        
        result = base.override_with(override)
        
        assert result.specs[0].column == "created_at"
    
    def test_override_with_multiple_columns(self):
        """Override with multiple columns."""
        base = OrderingConfig.from_order_by("created_at desc")
        override = OrderingConfig.from_order_by(["pinned desc", "name"])
        
        result = base.override_with(override)
        
        assert len(result.specs) == 2
        assert result.specs[0].column == "pinned"
        assert result.specs[1].column == "name"
    
    def test_override_both_empty(self):
        """Override when both are empty."""
        base = OrderingConfig()
        override = OrderingConfig()
        
        result = base.override_with(override)
        
        assert not result.has_ordering


class TestMergeWith:
    """Test OrderingConfig.merge_with method."""
    
    def test_merge_combines_orderings(self):
        """Merge combines both orderings."""
        first = OrderingConfig.from_order_by("pinned desc")
        second = OrderingConfig.from_order_by("created_at desc")
        
        result = first.merge_with(second)
        
        assert len(result.specs) == 2
        assert result.specs[0].column == "pinned"
        assert result.specs[1].column == "created_at"
    
    def test_merge_preserves_order(self):
        """Merge preserves order (first's specs come first)."""
        first = OrderingConfig.from_order_by(["a", "b"])
        second = OrderingConfig.from_order_by(["c", "d"])
        
        result = first.merge_with(second)
        
        columns = [s.column for s in result.specs]
        assert columns == ["a", "b", "c", "d"]
    
    def test_merge_with_empty(self):
        """Merge with empty keeps first's ordering."""
        first = OrderingConfig.from_order_by("name")
        second = OrderingConfig()
        
        result = first.merge_with(second)
        
        assert len(result.specs) == 1
        assert result.specs[0].column == "name"
    
    def test_merge_empty_with_ordering(self):
        """Empty merged with ordering gets the ordering."""
        first = OrderingConfig()
        second = OrderingConfig.from_order_by("name")
        
        result = first.merge_with(second)
        
        assert len(result.specs) == 1
        assert result.specs[0].column == "name"
    
    def test_merge_multiple_with_multiple(self):
        """Merge multiple columns with multiple columns."""
        first = OrderingConfig.from_order_by(["a desc", "b"])
        second = OrderingConfig.from_order_by(["c", "d desc"])
        
        result = first.merge_with(second)
        
        assert len(result.specs) == 4


class TestOverrideScenarios:
    """Test real-world override scenarios."""
    
    def test_relationship_default_then_query_override(self):
        """Relationship has default, query overrides."""
        # Relationship default: created_at desc
        rel_ordering = OrderingConfig.from_order_by("created_at desc")
        
        # Query wants: name asc
        query_ordering = OrderingConfig.from_order_by("name asc")
        
        # Query override wins
        result = rel_ordering.override_with(query_ordering)
        
        assert result.specs[0].column == "name"
    
    def test_no_query_override_uses_default(self):
        """No query override uses relationship default."""
        rel_ordering = OrderingConfig.from_order_by("created_at desc")
        query_ordering = OrderingConfig()  # No override
        
        result = rel_ordering.override_with(query_ordering)
        
        assert result.specs[0].column == "created_at"
    
    def test_add_secondary_sort(self):
        """Add secondary sort via merge."""
        # Primary sort
        primary = OrderingConfig.from_order_by("category")
        
        # Add secondary sort
        secondary = OrderingConfig.from_order_by("name")
        
        result = primary.merge_with(secondary)
        
        assert result.specs[0].column == "category"
        assert result.specs[1].column == "name"


class TestOverrideWithRelationships:
    """Test override with has_many/many_to_many."""
    
    def test_has_many_can_be_overridden(self):
        """has_many ordering can be overridden."""
        rel = has_many(MockPost, order_by="created_at desc")
        rel.rel_name = "posts"
        
        # Get relationship ordering
        rel_ordering = rel.ordering
        
        # Create query override
        query_ordering = OrderingConfig.from_order_by("title asc")
        
        # Override
        result = rel_ordering.override_with(query_ordering)
        
        assert result.specs[0].column == "title"
    
    def test_m2m_can_be_overridden(self):
        """many_to_many ordering can be overridden."""
        rel = many_to_many(MockPost, order_by="name")
        rel.rel_name = "tags"
        
        rel_ordering = rel.ordering
        query_ordering = OrderingConfig.from_order_by("position")
        
        result = rel_ordering.override_with(query_ordering)
        
        assert result.specs[0].column == "position"


class TestOverrideSqlGeneration:
    """Test SQL generation with overrides."""
    
    def test_override_sql(self):
        """Overridden ordering generates correct SQL."""
        base = OrderingConfig.from_order_by("created_at desc")
        override = OrderingConfig.from_order_by("name asc")
        
        result = base.override_with(override)
        sql = result.to_sql()
        
        assert sql == "ORDER BY name ASC"
    
    def test_merge_sql(self):
        """Merged ordering generates correct SQL."""
        first = OrderingConfig.from_order_by("pinned desc")
        second = OrderingConfig.from_order_by("name")
        
        result = first.merge_with(second)
        sql = result.to_sql()
        
        assert sql == "ORDER BY pinned DESC, name ASC"


class TestOverrideChaining:
    """Test chaining multiple overrides/merges."""
    
    def test_chain_multiple_merges(self):
        """Chain multiple merge calls."""
        config = OrderingConfig.from_order_by("a")
        config = config.merge_with(OrderingConfig.from_order_by("b"))
        config = config.merge_with(OrderingConfig.from_order_by("c"))
        
        columns = [s.column for s in config.specs]
        assert columns == ["a", "b", "c"]
    
    def test_override_then_merge(self):
        """Override then merge."""
        base = OrderingConfig.from_order_by("original")
        override = OrderingConfig.from_order_by("new")
        additional = OrderingConfig.from_order_by("extra")
        
        result = base.override_with(override).merge_with(additional)
        
        columns = [s.column for s in result.specs]
        assert columns == ["new", "extra"]
    
    def test_merge_then_override(self):
        """Merge then override (override wins completely)."""
        first = OrderingConfig.from_order_by("a")
        second = OrderingConfig.from_order_by("b")
        override = OrderingConfig.from_order_by("final")
        
        merged = first.merge_with(second)
        result = merged.override_with(override)
        
        assert len(result.specs) == 1
        assert result.specs[0].column == "final"


class TestOverrideEdgeCases:
    """Test edge cases for override/merge."""
    
    def test_override_with_nulls(self):
        """Override preserves NULLS."""
        base = OrderingConfig.from_order_by("priority desc")
        override = OrderingConfig.from_order_by("due_date nulls last")
        
        result = base.override_with(override)
        
        assert result.specs[0].nulls == "last"
    
    def test_merge_with_nulls(self):
        """Merge preserves NULLS."""
        first = OrderingConfig.from_order_by("priority desc nulls first")
        second = OrderingConfig.from_order_by("due_date nulls last")
        
        result = first.merge_with(second)
        
        assert result.specs[0].nulls == "first"
        assert result.specs[1].nulls == "last"
    
    def test_override_none_ordering(self):
        """Override None with actual ordering."""
        base = None
        override = OrderingConfig.from_order_by("name")
        
        # Handle None case
        if base is None:
            result = override
        else:
            result = base.override_with(override)
        
        assert result.specs[0].column == "name"

