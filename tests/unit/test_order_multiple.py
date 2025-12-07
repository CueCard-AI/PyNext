"""
Tests for multiple order columns.

Tests cover:
- Two column ordering
- Three or more column ordering
- Mixed directions
- SQL generation for multiple columns
"""

import pytest
from typing import List

from pynext.db.relationships.ordering import (
    OrderSpec,
    OrderingConfig,
    parse_order_by,
    build_order_clause,
    build_order_columns,
)
from pynext.db.relationships.core import has_many, many_to_many


# =============================================================================
# Mock Models
# =============================================================================

class MockTable:
    """Base mock table."""
    pass


class MockPost(MockTable):
    """Mock Post model."""
    pass


class MockComment(MockTable):
    """Mock Comment model."""
    pass


# =============================================================================
# Test: Two Column Ordering
# =============================================================================

class TestTwoColumnOrdering:
    """Test two column ordering."""
    
    def test_two_columns_asc(self):
        """Two columns ascending."""
        specs = parse_order_by(["a", "b"])
        assert len(specs) == 2
        assert specs[0].column == "a"
        assert specs[0].direction == "asc"
        assert specs[1].column == "b"
        assert specs[1].direction == "asc"
    
    def test_two_columns_desc(self):
        """Two columns descending."""
        specs = parse_order_by(["a desc", "b desc"])
        assert specs[0].direction == "desc"
        assert specs[1].direction == "desc"
    
    def test_two_columns_mixed(self):
        """Two columns mixed direction."""
        specs = parse_order_by(["a desc", "b asc"])
        assert specs[0].direction == "desc"
        assert specs[1].direction == "asc"
    
    def test_two_columns_sql(self):
        """Two columns SQL generation."""
        specs = parse_order_by(["a desc", "b"])
        sql = build_order_clause(specs)
        assert sql == "ORDER BY a DESC, b ASC"
    
    def test_two_columns_with_alias(self):
        """Two columns with table alias."""
        specs = parse_order_by(["a", "b desc"])
        sql = build_order_clause(specs, table_alias="t")
        assert sql == "ORDER BY t.a ASC, t.b DESC"


class TestThreeColumnOrdering:
    """Test three column ordering."""
    
    def test_three_columns(self):
        """Three columns parsed."""
        specs = parse_order_by(["a", "b desc", "c"])
        assert len(specs) == 3
        assert specs[0].column == "a"
        assert specs[1].column == "b"
        assert specs[2].column == "c"
    
    def test_three_columns_sql(self):
        """Three columns SQL generation."""
        specs = parse_order_by(["a desc", "b", "c desc"])
        sql = build_order_clause(specs)
        assert sql == "ORDER BY a DESC, b ASC, c DESC"
    
    def test_three_columns_all_directions(self):
        """Three columns with various directions."""
        specs = parse_order_by(["a asc", "b desc", "c asc"])
        assert specs[0].direction == "asc"
        assert specs[1].direction == "desc"
        assert specs[2].direction == "asc"


class TestFourPlusColumnOrdering:
    """Test four or more column ordering."""
    
    def test_four_columns(self):
        """Four columns parsed."""
        specs = parse_order_by(["a", "b", "c", "d"])
        assert len(specs) == 4
    
    def test_five_columns(self):
        """Five columns parsed."""
        specs = parse_order_by(["a", "b", "c", "d", "e"])
        assert len(specs) == 5
    
    def test_many_columns_sql(self):
        """Many columns SQL generation."""
        specs = parse_order_by(["a desc", "b", "c desc", "d", "e desc"])
        sql = build_order_clause(specs)
        assert sql == "ORDER BY a DESC, b ASC, c DESC, d ASC, e DESC"


class TestMultipleColumnsWithNulls:
    """Test multiple columns with NULLS handling."""
    
    def test_two_columns_first_has_nulls(self):
        """First column has NULLS, second doesn't."""
        specs = parse_order_by(["a desc nulls first", "b"])
        assert specs[0].nulls == "first"
        assert specs[1].nulls is None
    
    def test_two_columns_second_has_nulls(self):
        """Second column has NULLS, first doesn't."""
        specs = parse_order_by(["a", "b nulls last"])
        assert specs[0].nulls is None
        assert specs[1].nulls == "last"
    
    def test_two_columns_both_have_nulls(self):
        """Both columns have NULLS."""
        specs = parse_order_by(["a nulls first", "b nulls last"])
        assert specs[0].nulls == "first"
        assert specs[1].nulls == "last"
    
    def test_multiple_nulls_sql(self):
        """Multiple columns with NULLS SQL generation."""
        specs = parse_order_by(["a desc nulls first", "b nulls last"])
        sql = build_order_clause(specs)
        assert sql == "ORDER BY a DESC NULLS FIRST, b ASC NULLS LAST"


class TestMultipleColumnsInRelationships:
    """Test multiple columns in has_many/many_to_many."""
    
    def test_has_many_two_columns(self):
        """has_many with two columns."""
        rel = has_many(MockPost, order_by=["pinned desc", "created_at desc"])
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 2
    
    def test_has_many_three_columns(self):
        """has_many with three columns."""
        rel = has_many(MockPost, order_by=["priority desc", "pinned desc", "title"])
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 3
    
    def test_m2m_two_columns(self):
        """many_to_many with two columns."""
        rel = many_to_many(MockPost, order_by=["position", "name"])
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 2
    
    def test_m2m_three_columns(self):
        """many_to_many with three columns."""
        rel = many_to_many(MockPost, order_by=["group", "position", "name"])
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 3


class TestBuildOrderColumns:
    """Test build_order_columns for multiple columns."""
    
    def test_returns_list(self):
        """Returns list of column expressions."""
        specs = parse_order_by(["a", "b desc"])
        columns = build_order_columns(specs)
        assert isinstance(columns, list)
        assert len(columns) == 2
    
    def test_correct_expressions(self):
        """Returns correct expressions."""
        specs = parse_order_by(["a desc", "b", "c desc"])
        columns = build_order_columns(specs)
        assert columns == ["a DESC", "b ASC", "c DESC"]
    
    def test_with_alias(self):
        """Expressions with table alias."""
        specs = parse_order_by(["a", "b desc"])
        columns = build_order_columns(specs, table_alias="t")
        assert columns == ["t.a ASC", "t.b DESC"]
    
    def test_with_nulls(self):
        """Expressions with NULLS."""
        specs = parse_order_by(["a nulls first", "b desc nulls last"])
        columns = build_order_columns(specs)
        assert columns == ["a ASC NULLS FIRST", "b DESC NULLS LAST"]


class TestOrderingConfigMultiple:
    """Test OrderingConfig with multiple columns."""
    
    def test_from_list(self):
        """Create from list."""
        config = OrderingConfig.from_order_by(["a desc", "b"])
        assert len(config) == 2
    
    def test_has_ordering(self):
        """has_ordering is True."""
        config = OrderingConfig.from_order_by(["a", "b"])
        assert config.has_ordering
    
    def test_to_sql(self):
        """to_sql for multiple columns."""
        config = OrderingConfig.from_order_by(["a desc", "b"])
        assert config.to_sql() == "ORDER BY a DESC, b ASC"
    
    def test_get_columns(self):
        """get_columns for multiple columns."""
        config = OrderingConfig.from_order_by(["a desc", "b"])
        columns = config.get_columns()
        assert len(columns) == 2
    
    def test_merge_with(self):
        """Merge two multi-column configs."""
        config1 = OrderingConfig.from_order_by(["a", "b"])
        config2 = OrderingConfig.from_order_by(["c", "d"])
        merged = config1.merge_with(config2)
        assert len(merged) == 4


class TestMultipleColumnRealWorld:
    """Test real-world multiple column scenarios."""
    
    def test_blog_posts_pinned_first(self):
        """Blog posts: pinned first, then by date."""
        rel = has_many(MockPost, order_by=["pinned desc", "created_at desc"])
        rel.rel_name = "posts"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY pinned DESC, created_at DESC"
    
    def test_comments_highlighted_then_votes(self):
        """Comments: highlighted first, then by votes, then by date."""
        rel = has_many(MockComment, order_by=[
            "highlighted desc",
            "votes desc",
            "created_at desc"
        ])
        rel.rel_name = "comments"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY highlighted DESC, votes DESC, created_at DESC"
    
    def test_tasks_priority_queue(self):
        """Tasks: by priority, then due date (nulls last), then created."""
        rel = has_many(MockPost, order_by=[
            "priority desc",
            "due_date nulls last",
            "created_at"
        ])
        rel.rel_name = "tasks"
        
        sql = rel.ordering.to_sql()
        assert "priority DESC" in sql
        assert "due_date ASC NULLS LAST" in sql
        assert "created_at ASC" in sql
    
    def test_products_category_position(self):
        """Products: by category, position in category, then name."""
        rel = has_many(MockPost, order_by=[
            "category",
            "position",
            "name"
        ])
        rel.rel_name = "products"
        
        columns = rel.ordering.get_columns()
        assert columns == ["category ASC", "position ASC", "name ASC"]

