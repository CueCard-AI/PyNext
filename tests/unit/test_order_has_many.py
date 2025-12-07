"""
Tests for has_many with ordering.

Tests cover:
- has_many with order_by parameter
- Single and multiple column ordering
- Direction handling (asc/desc)
- NULLS FIRST/LAST
- Integration with HasMany descriptor
"""

import pytest
from typing import List, Optional
from datetime import datetime, date

from pynext.db.relationships.core import HasMany, has_many
from pynext.db.relationships.ordering import OrderSpec, OrderingConfig


# =============================================================================
# Mock Models for Testing
# =============================================================================

class MockTable:
    """Base mock table for testing."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockUser(MockTable):
    """Mock User model."""
    pass


class MockPost(MockTable):
    """Mock Post model with various orderable fields."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = kwargs.get("title", "Untitled")
        self.created_at = kwargs.get("created_at", datetime.now())
        self.pinned = kwargs.get("pinned", False)
        self.priority = kwargs.get("priority")
        self.author_id = kwargs.get("author_id")


class MockComment(MockTable):
    """Mock Comment model."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.content = kwargs.get("content", "")
        self.created_at = kwargs.get("created_at", datetime.now())
        self.pinned = kwargs.get("pinned", False)


# =============================================================================
# Test: has_many with order_by
# =============================================================================

class TestHasManyOrderBy:
    """Test has_many function with order_by."""
    
    def test_has_many_accepts_order_by_string(self):
        """has_many accepts order_by string."""
        rel = has_many(MockPost, order_by="created_at desc")
        assert rel._order_by_input == "created_at desc"
    
    def test_has_many_accepts_order_by_list(self):
        """has_many accepts order_by list."""
        rel = has_many(MockPost, order_by=["pinned desc", "created_at desc"])
        assert rel._order_by_input == ["pinned desc", "created_at desc"]
    
    def test_has_many_order_by_none_default(self):
        """has_many order_by defaults to None."""
        rel = has_many(MockPost)
        assert rel._order_by_input is None
    
    def test_has_many_ordering_property(self):
        """HasMany.ordering property returns OrderingConfig."""
        rel = has_many(MockPost, order_by="name desc")
        # Need to set rel_name for the descriptor
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert isinstance(ordering, OrderingConfig)
        assert ordering.has_ordering
        assert len(ordering) == 1
    
    def test_has_many_ordering_none_when_no_order_by(self):
        """HasMany.ordering is None when no order_by."""
        rel = has_many(MockPost)
        rel.rel_name = "posts"
        
        assert rel.ordering is None
    
    def test_has_many_order_by_property(self):
        """HasMany.order_by returns raw value."""
        rel = has_many(MockPost, order_by="name")
        rel.rel_name = "posts"
        
        assert rel.order_by == "name"


class TestHasManyWithSingleColumn:
    """Test has_many with single column ordering."""
    
    def test_single_column_asc(self):
        """Single column ascending."""
        rel = has_many(MockPost, order_by="title")
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 1
        assert ordering.specs[0].column == "title"
        assert ordering.specs[0].direction == "asc"
    
    def test_single_column_desc(self):
        """Single column descending."""
        rel = has_many(MockPost, order_by="created_at desc")
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert ordering.specs[0].direction == "desc"
    
    def test_single_column_sql(self):
        """Single column generates correct SQL."""
        rel = has_many(MockPost, order_by="created_at desc")
        rel.rel_name = "posts"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY created_at DESC"


class TestHasManyWithMultipleColumns:
    """Test has_many with multiple column ordering."""
    
    def test_multiple_columns(self):
        """Multiple columns parsed correctly."""
        rel = has_many(MockPost, order_by=["pinned desc", "created_at desc"])
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 2
        assert ordering.specs[0].column == "pinned"
        assert ordering.specs[1].column == "created_at"
    
    def test_multiple_columns_mixed_direction(self):
        """Multiple columns with mixed directions."""
        rel = has_many(MockPost, order_by=["pinned desc", "title asc"])
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert ordering.specs[0].direction == "desc"
        assert ordering.specs[1].direction == "asc"
    
    def test_multiple_columns_sql(self):
        """Multiple columns generate correct SQL."""
        rel = has_many(MockPost, order_by=["pinned desc", "title"])
        rel.rel_name = "posts"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY pinned DESC, title ASC"
    
    def test_three_columns(self):
        """Three column ordering."""
        rel = has_many(MockPost, order_by=["priority desc", "pinned desc", "title"])
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 3
    
    def test_four_columns(self):
        """Four column ordering."""
        rel = has_many(MockPost, order_by=[
            "priority desc", "pinned desc", "created_at desc", "title"
        ])
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 4


class TestHasManyWithNulls:
    """Test has_many with NULLS FIRST/LAST."""
    
    def test_nulls_first(self):
        """NULLS FIRST parsed correctly."""
        rel = has_many(MockPost, order_by="priority desc nulls first")
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert ordering.specs[0].nulls == "first"
    
    def test_nulls_last(self):
        """NULLS LAST parsed correctly."""
        rel = has_many(MockPost, order_by="due_date nulls last")
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert ordering.specs[0].nulls == "last"
    
    def test_nulls_sql(self):
        """NULLS generates correct SQL."""
        rel = has_many(MockPost, order_by="priority desc nulls first")
        rel.rel_name = "posts"
        
        sql = rel.ordering.to_sql()
        assert "NULLS FIRST" in sql
    
    def test_multiple_with_nulls(self):
        """Multiple columns with NULLS handling."""
        rel = has_many(MockPost, order_by=[
            "priority desc nulls first",
            "due_date nulls last"
        ])
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert ordering.specs[0].nulls == "first"
        assert ordering.specs[1].nulls == "last"


class TestHasManyDescriptor:
    """Test HasMany descriptor with ordering."""
    
    def test_has_many_class_stores_ordering(self):
        """HasMany class stores ordering config."""
        descriptor = HasMany(
            rel_name="posts",
            model=MockPost,
            foreign_key="author_id",
            order_by="created_at desc"
        )
        
        assert descriptor._order_by_input == "created_at desc"
    
    def test_ordering_lazy_init(self):
        """Ordering is lazily initialized."""
        descriptor = HasMany(
            rel_name="posts",
            model=MockPost,
            foreign_key="author_id",
            order_by="created_at desc"
        )
        
        # Initially None
        assert descriptor._ordering is None
        
        # Access triggers creation
        ordering = descriptor.ordering
        assert ordering is not None
        assert descriptor._ordering is not None
    
    def test_ordering_cached(self):
        """Ordering is cached after first access."""
        descriptor = HasMany(
            rel_name="posts",
            model=MockPost,
            foreign_key="author_id",
            order_by="created_at desc"
        )
        
        ordering1 = descriptor.ordering
        ordering2 = descriptor.ordering
        
        assert ordering1 is ordering2


class TestHasManyWithOtherOptions:
    """Test has_many ordering combined with other options."""
    
    def test_with_backref(self):
        """Order_by works with backref."""
        rel = has_many(
            MockPost,
            backref="author",
            order_by="created_at desc"
        )
        rel.rel_name = "posts"
        
        assert rel.backref == "author"
        assert rel.ordering.has_ordering
    
    def test_with_lazy(self):
        """Order_by works with lazy loading."""
        rel = has_many(
            MockPost,
            lazy="selectin",
            order_by="created_at desc"
        )
        rel.rel_name = "posts"
        
        assert rel.lazy == "selectin"
        assert rel.ordering.has_ordering
    
    def test_with_filter(self):
        """Order_by works with filter."""
        rel = has_many(
            MockPost,
            filter=[("is_active", "=", True)],  # Use tuple syntax
            order_by="created_at desc"
        )
        rel.rel_name = "posts"
        
        assert rel._filter_input is not None
        assert rel.ordering.has_ordering
    
    def test_with_cascade(self):
        """Order_by works with cascade."""
        rel = has_many(
            MockPost,
            on_delete="cascade",
            order_by="created_at desc"
        )
        rel.rel_name = "posts"
        
        assert rel.on_delete == "cascade"
        assert rel.ordering.has_ordering
    
    def test_with_all_options(self):
        """Order_by works with all options combined."""
        rel = has_many(
            MockPost,
            foreign_key="author_id",
            backref="author",
            lazy="selectin",
            on_delete="cascade",
            order_by=["pinned desc", "created_at desc"]
        )
        rel.rel_name = "posts"
        
        assert rel.foreign_key == "author_id"
        assert rel.backref == "author"
        assert rel.lazy == "selectin"
        assert rel.on_delete == "cascade"
        assert len(rel.ordering.specs) == 2


class TestHasManyOrderingSql:
    """Test SQL generation for has_many ordering."""
    
    def test_sql_with_alias(self):
        """SQL with table alias."""
        rel = has_many(MockPost, order_by="created_at desc")
        rel.rel_name = "posts"
        
        sql = rel.ordering.to_sql(table_alias="p")
        assert sql == "ORDER BY p.created_at DESC"
    
    def test_sql_without_keyword(self):
        """SQL without ORDER BY keyword."""
        rel = has_many(MockPost, order_by="created_at desc")
        rel.rel_name = "posts"
        
        sql = rel.ordering.to_sql(include_keyword=False)
        assert sql == "created_at DESC"
    
    def test_get_columns_list(self):
        """Get ordered column list."""
        rel = has_many(MockPost, order_by=["pinned desc", "title"])
        rel.rel_name = "posts"
        
        columns = rel.ordering.get_columns()
        assert columns == ["pinned DESC", "title ASC"]


class TestHasManyEdgeCases:
    """Test edge cases for has_many ordering."""
    
    def test_empty_list_order_by(self):
        """Empty list order_by."""
        rel = has_many(MockPost, order_by=[])
        rel.rel_name = "posts"
        
        # Should not have ordering
        assert rel._order_by_input == []
        if rel.ordering:
            assert not rel.ordering.has_ordering
    
    def test_single_item_list(self):
        """Single item list order_by."""
        rel = has_many(MockPost, order_by=["created_at"])
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 1
    
    def test_underscore_column_names(self):
        """Underscore column names work."""
        rel = has_many(MockPost, order_by="created_at desc")
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert ordering.specs[0].column == "created_at"
    
    def test_numeric_suffix_column_names(self):
        """Column names with numeric suffixes."""
        rel = has_many(MockPost, order_by="field1 desc")
        rel.rel_name = "posts"
        
        ordering = rel.ordering
        assert ordering.specs[0].column == "field1"


class TestHasManyTyping:
    """Test has_many typing with ordering."""
    
    def test_return_type(self):
        """has_many returns HasMany."""
        rel = has_many(MockPost, order_by="name")
        assert isinstance(rel, HasMany)
    
    def test_generic_type_preserved(self):
        """Generic type is preserved."""
        rel = has_many(MockPost, order_by="name")
        # The model is stored
        assert rel._model == MockPost

