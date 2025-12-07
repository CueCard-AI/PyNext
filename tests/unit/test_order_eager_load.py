"""
Tests for ordering with eager loading.

Tests cover:
- Ordering with selectinload
- Ordering with joinedload
- Ordering preserved in eager loaded collections
- Override at load time
"""

import pytest
from typing import List, Optional
from datetime import datetime

from pynext.db.relationships.ordering import (
    OrderSpec,
    OrderingConfig,
    parse_order_by,
    build_order_clause,
)
from pynext.db.relationships.core import HasMany, ManyToMany, has_many, many_to_many


# =============================================================================
# Mock Models
# =============================================================================

class MockTable:
    """Base mock table."""
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockUser(MockTable):
    """Mock User model."""
    pass


class MockPost(MockTable):
    """Mock Post model."""
    pass


class MockComment(MockTable):
    """Mock Comment model."""
    pass


class MockTag(MockTable):
    """Mock Tag model."""
    pass


# =============================================================================
# Test: Ordering Configuration for Eager Loading
# =============================================================================

class TestOrderingForEagerLoad:
    """Test ordering configuration for eager loading."""
    
    def test_has_many_ordering_for_selectin(self):
        """has_many ordering available for selectin loading."""
        rel = has_many(MockPost, lazy="selectin", order_by="created_at desc")
        rel.rel_name = "posts"
        
        # Ordering should be configured
        assert rel.ordering is not None
        assert rel.ordering.has_ordering
        
        # SQL can be generated for the eager load query
        sql = rel.ordering.to_sql()
        assert "ORDER BY created_at DESC" in sql
    
    def test_has_many_ordering_for_subquery(self):
        """has_many ordering for subquery loading."""
        rel = has_many(MockPost, lazy="subquery", order_by="title")
        rel.rel_name = "posts"
        
        assert rel.ordering.has_ordering
        sql = rel.ordering.to_sql()
        assert "ORDER BY title ASC" in sql
    
    def test_m2m_ordering_for_selectin(self):
        """many_to_many ordering for selectin loading."""
        rel = many_to_many(MockTag, lazy="selectin", order_by="name")
        rel.rel_name = "tags"
        
        assert rel.ordering.has_ordering
        sql = rel.ordering.to_sql()
        assert "ORDER BY name ASC" in sql


class TestOrderingSqlForJoins:
    """Test SQL generation for JOIN-based loading."""
    
    def test_ordering_with_alias_for_join(self):
        """Ordering with table alias for LEFT JOIN."""
        config = OrderingConfig.from_order_by("created_at desc")
        
        # For LEFT JOIN, we'd alias the joined table
        sql = config.to_sql(table_alias="posts_1")
        assert sql == "ORDER BY posts_1.created_at DESC"
    
    def test_multiple_ordering_with_alias(self):
        """Multiple columns with table alias."""
        config = OrderingConfig.from_order_by(["pinned desc", "created_at desc"])
        
        sql = config.to_sql(table_alias="p")
        assert "p.pinned DESC" in sql
        assert "p.created_at DESC" in sql
    
    def test_ordering_columns_without_keyword(self):
        """Get ordering columns without ORDER BY keyword."""
        config = OrderingConfig.from_order_by(["a desc", "b"])
        
        # For appending to existing ORDER BY
        columns = config.get_columns(table_alias="t")
        assert columns == ["t.a DESC", "t.b ASC"]


class TestOrderingPreservation:
    """Test that ordering is preserved in descriptors."""
    
    def test_has_many_preserves_ordering(self):
        """HasMany preserves ordering configuration."""
        rel = has_many(MockPost, order_by=["pinned desc", "created_at desc"])
        rel.rel_name = "posts"
        
        # Access multiple times - should be same instance
        ordering1 = rel.ordering
        ordering2 = rel.ordering
        
        assert ordering1 is ordering2
        assert len(ordering1.specs) == 2
    
    def test_m2m_preserves_ordering(self):
        """ManyToMany preserves ordering configuration."""
        rel = many_to_many(MockTag, order_by="name")
        rel.rel_name = "tags"
        
        ordering1 = rel.ordering
        ordering2 = rel.ordering
        
        assert ordering1 is ordering2


class TestEagerLoadOrderingPatterns:
    """Test common eager loading ordering patterns."""
    
    def test_posts_with_recent_comments(self):
        """Posts with comments ordered by date."""
        # User -> Posts (pinned first, then date)
        # Each Post -> Comments (newest first)
        
        user_posts = has_many(MockPost, order_by=["pinned desc", "created_at desc"])
        user_posts.rel_name = "posts"
        
        post_comments = has_many(MockComment, order_by="created_at desc")
        post_comments.rel_name = "comments"
        
        # Both have ordering
        assert user_posts.ordering.has_ordering
        assert post_comments.ordering.has_ordering
    
    def test_nested_ordering_sql(self):
        """Generate SQL for nested eager loads."""
        # Level 1: Posts ordered by date
        posts_config = OrderingConfig.from_order_by("created_at desc")
        
        # Level 2: Comments ordered by votes
        comments_config = OrderingConfig.from_order_by("votes desc")
        
        # Each generates its own ORDER BY
        posts_sql = posts_config.to_sql(table_alias="p")
        comments_sql = comments_config.to_sql(table_alias="c")
        
        assert "p.created_at DESC" in posts_sql
        assert "c.votes DESC" in comments_sql


class TestOrderingOverrideAtLoadTime:
    """Test overriding ordering at load time."""
    
    def test_override_relationship_ordering(self):
        """Override relationship default ordering."""
        # Relationship default: created_at desc
        rel = has_many(MockPost, order_by="created_at desc")
        rel.rel_name = "posts"
        
        default_ordering = rel.ordering
        
        # Query-time override: title asc
        query_ordering = OrderingConfig.from_order_by("title asc")
        
        # Apply override
        final_ordering = default_ordering.override_with(query_ordering)
        
        assert final_ordering.specs[0].column == "title"
        assert final_ordering.specs[0].direction == "asc"
    
    def test_no_override_uses_default(self):
        """No override uses relationship default."""
        rel = has_many(MockPost, order_by="created_at desc")
        rel.rel_name = "posts"
        
        default_ordering = rel.ordering
        
        # No query-time override
        no_override = OrderingConfig()
        
        final_ordering = default_ordering.override_with(no_override)
        
        assert final_ordering.specs[0].column == "created_at"
    
    def test_merge_additional_ordering(self):
        """Merge additional ordering columns."""
        rel = has_many(MockPost, order_by="pinned desc")
        rel.rel_name = "posts"
        
        default_ordering = rel.ordering
        
        # Add secondary sort at query time
        additional = OrderingConfig.from_order_by("created_at desc")
        
        merged = default_ordering.merge_with(additional)
        
        assert len(merged.specs) == 2
        assert merged.specs[0].column == "pinned"
        assert merged.specs[1].column == "created_at"


class TestEagerLoadWithAllOptions:
    """Test eager loading with all ordering options combined."""
    
    def test_with_nulls_handling(self):
        """Eager load with NULLS FIRST/LAST."""
        rel = has_many(MockPost, lazy="selectin", order_by="due_date nulls last")
        rel.rel_name = "tasks"
        
        sql = rel.ordering.to_sql(table_alias="t")
        assert "t.due_date ASC NULLS LAST" in sql
    
    def test_with_multiple_columns(self):
        """Eager load with multiple order columns."""
        rel = has_many(MockPost, lazy="selectin", order_by=[
            "priority desc nulls first",
            "due_date nulls last",
            "created_at"
        ])
        rel.rel_name = "tasks"
        
        columns = rel.ordering.get_columns()
        assert len(columns) == 3
    
    def test_with_backref_and_ordering(self):
        """Eager load with backref and ordering."""
        rel = has_many(
            MockPost,
            backref="author",
            lazy="selectin",
            order_by="created_at desc"
        )
        rel.rel_name = "posts"
        
        assert rel.backref == "author"
        assert rel.lazy == "selectin"
        assert rel.ordering.has_ordering


class TestDynamicRelationshipOrdering:
    """Test ordering with dynamic (query builder) relationships."""
    
    def test_dynamic_has_ordering_configured(self):
        """Dynamic relationship has ordering configured."""
        rel = has_many(MockPost, lazy="dynamic", order_by="created_at desc")
        rel.rel_name = "posts"
        
        # Even dynamic relationships have ordering config
        assert rel._order_by_input == "created_at desc"
    
    def test_dynamic_ordering_for_builder(self):
        """Dynamic relationship ordering available for query builder."""
        rel = has_many(MockPost, lazy="dynamic", order_by=["pinned desc", "title"])
        rel.rel_name = "posts"
        
        # Query builder would use this
        assert rel.ordering is not None
        assert len(rel.ordering.specs) == 2


class TestRaiseLoadingWithOrdering:
    """Test ordering with raise loading (N+1 prevention)."""
    
    def test_raise_loading_has_ordering(self):
        """raise loading still has ordering configured."""
        rel = has_many(MockPost, lazy="raise", order_by="created_at desc")
        rel.rel_name = "posts"
        
        # Ordering is configured (would be used if explicitly loaded)
        assert rel.ordering.has_ordering
    
    def test_raise_ordering_available_for_explicit_load(self):
        """raise ordering available when explicitly loaded."""
        rel = has_many(MockPost, lazy="raise", order_by=["pinned desc", "created_at desc"])
        rel.rel_name = "posts"
        
        # When explicitly loaded via selectinload(), ordering applies
        sql = rel.ordering.to_sql()
        assert "ORDER BY pinned DESC, created_at DESC" in sql


class TestOrderingWithSelectIn:
    """Test ordering specifically for selectin loading."""
    
    def test_selectin_sql_generation(self):
        """Generate SQL for selectin loading."""
        rel = has_many(MockPost, lazy="selectin", order_by="created_at desc")
        rel.rel_name = "posts"
        
        # SQL for: SELECT * FROM posts WHERE author_id IN (...) ORDER BY created_at DESC
        order_sql = rel.ordering.to_sql()
        assert order_sql == "ORDER BY created_at DESC"
    
    def test_selectin_with_table_prefix(self):
        """selectin with table prefix in ORDER BY."""
        rel = has_many(MockPost, lazy="selectin", order_by=["pinned desc", "created_at desc"])
        rel.rel_name = "posts"
        
        # Full SQL would include table alias
        order_sql = rel.ordering.to_sql(table_alias="posts")
        assert "posts.pinned DESC" in order_sql
        assert "posts.created_at DESC" in order_sql


class TestOrderingWithJoinedLoad:
    """Test ordering for joined loading (LEFT JOIN)."""
    
    def test_joined_ordering_with_alias(self):
        """Joined load needs unique alias for ORDER BY."""
        config = OrderingConfig.from_order_by("name")
        
        # Each joined table gets a unique alias
        sql = config.to_sql(table_alias="tags_1")
        assert sql == "ORDER BY tags_1.name ASC"
    
    def test_joined_multiple_relationships(self):
        """Multiple joined relationships each with own ordering."""
        # User.posts (joined)
        posts_ordering = OrderingConfig.from_order_by("created_at desc")
        posts_sql = posts_ordering.to_sql(table_alias="posts_1")
        
        # User.comments (joined)
        comments_ordering = OrderingConfig.from_order_by("votes desc")
        comments_sql = comments_ordering.to_sql(table_alias="comments_1")
        
        assert "posts_1.created_at DESC" in posts_sql
        assert "comments_1.votes DESC" in comments_sql

