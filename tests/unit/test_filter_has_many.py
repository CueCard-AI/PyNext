"""
Test Phase 7.5: HasMany with Filters.

These tests verify that:
1. HasMany accepts filter parameter
2. Filter is correctly parsed and stored
3. Filter integrates with loading strategies
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Optional
from unittest.mock import Mock, patch

from pynext.db.relationships.conditions import (
    Condition,
    eq, ne, gt, gte, lt, lte,
    like, is_in, is_null,
)
from pynext.db.relationships.filter import RelationshipFilter
from pynext.db.relationships.core import (
    HasMany,
    has_many,
)


# =============================================================================
# Test HasMany with filter Parameter
# =============================================================================

class TestHasManyFilterParameter:
    """Test HasMany descriptor with filter parameter."""
    
    def test_has_many_no_filter(self):
        """HasMany without filter."""
        hm = HasMany(
            rel_name="posts",
            model="Post",
            foreign_key="author_id",
        )
        assert hm._filter_input is None
        assert hm.filter is None
    
    def test_has_many_with_filter_functions(self):
        """HasMany with condition function filters."""
        hm = HasMany(
            rel_name="active_posts",
            model="Post",
            foreign_key="author_id",
            filter=[eq("is_active", True)],
        )
        assert hm._filter_input is not None
        assert hm.filter is not None
        assert len(hm.filter.conditions) == 1
    
    def test_has_many_with_filter_tuples(self):
        """HasMany with tuple filters."""
        hm = HasMany(
            rel_name="active_posts",
            model="Post",
            foreign_key="author_id",
            filter=[("is_active", "=", True)],
        )
        assert hm.filter is not None
        assert hm.filter.conditions[0].operator == "="
    
    def test_has_many_with_filter_mixed(self):
        """HasMany with mixed filters."""
        hm = HasMany(
            rel_name="filtered_posts",
            model="Post",
            foreign_key="author_id",
            filter=[
                eq("is_active", True),
                ("views", ">=", 100),
            ],
        )
        assert len(hm.filter.conditions) == 2
    
    def test_has_many_filter_lazy_parse(self):
        """Filter is lazily parsed."""
        conditions = [eq("is_active", True)]
        hm = HasMany(
            rel_name="posts",
            model="Post",
            foreign_key="author_id",
            filter=conditions,
        )
        # Before accessing .filter property, _filter should be None
        assert hm._filter is None
        # Access triggers parsing
        _ = hm.filter
        assert hm._filter is not None


# =============================================================================
# Test has_many Factory Function with Filter
# =============================================================================

class TestHasManyFactoryWithFilter:
    """Test has_many() factory function with filter."""
    
    def test_has_many_factory_no_filter(self):
        """has_many() without filter."""
        hm = has_many("Post")
        assert hm._filter_input is None
    
    def test_has_many_factory_with_filter(self):
        """has_many() with filter."""
        hm = has_many("Post", filter=[eq("is_active", True)])
        assert hm._filter_input is not None
    
    def test_has_many_factory_filter_and_backref(self):
        """has_many() with both filter and backref."""
        hm = has_many(
            "Post",
            backref="author",
            filter=[eq("is_active", True)],
        )
        assert hm.backref == "author"
        assert hm._filter_input is not None
    
    def test_has_many_factory_filter_and_lazy(self):
        """has_many() with both filter and lazy."""
        hm = has_many(
            "Post",
            lazy="selectin",
            filter=[eq("is_active", True)],
        )
        assert hm.lazy == "selectin"
        assert hm._filter_input is not None
    
    def test_has_many_factory_filter_and_cascade(self):
        """has_many() with filter and cascade."""
        hm = has_many(
            "Post",
            on_delete="cascade",
            filter=[eq("is_active", True)],
        )
        assert hm.on_delete == "cascade"
        assert hm._filter_input is not None


# =============================================================================
# Test Multiple Filters
# =============================================================================

class TestHasManyMultipleFilters:
    """Test HasMany with multiple filter conditions."""
    
    def test_two_conditions(self):
        """Two filter conditions."""
        hm = has_many("Post", filter=[
            eq("is_active", True),
            gte("views", 100),
        ])
        assert len(hm.filter.conditions) == 2
    
    def test_three_conditions(self):
        """Three filter conditions."""
        hm = has_many("Post", filter=[
            eq("is_active", True),
            gte("views", 100),
            like("title", "%python%"),
        ])
        assert len(hm.filter.conditions) == 3
    
    def test_many_conditions(self):
        """Many filter conditions."""
        conditions = [eq(f"field_{i}", i) for i in range(10)]
        hm = has_many("Post", filter=conditions)
        assert len(hm.filter.conditions) == 10
    
    def test_all_operator_types(self):
        """All operator types in filter."""
        hm = has_many("Post", filter=[
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
        assert len(hm.filter.conditions) == 9


# =============================================================================
# Test Filter Value Types
# =============================================================================

class TestHasManyFilterValues:
    """Test HasMany with various filter value types."""
    
    def test_filter_boolean_true(self):
        """Filter with True boolean."""
        hm = has_many("Post", filter=[eq("is_active", True)])
        assert hm.filter.conditions[0].value is True
    
    def test_filter_boolean_false(self):
        """Filter with False boolean."""
        hm = has_many("Post", filter=[eq("is_deleted", False)])
        assert hm.filter.conditions[0].value is False
    
    def test_filter_integer(self):
        """Filter with integer."""
        hm = has_many("Post", filter=[gte("views", 100)])
        assert hm.filter.conditions[0].value == 100
    
    def test_filter_string(self):
        """Filter with string."""
        hm = has_many("Post", filter=[eq("status", "published")])
        assert hm.filter.conditions[0].value == "published"
    
    def test_filter_datetime(self):
        """Filter with datetime."""
        dt = datetime.now() - timedelta(days=30)
        hm = has_many("Post", filter=[gte("created_at", dt)])
        assert hm.filter.conditions[0].value == dt
    
    def test_filter_list(self):
        """Filter with list (IN)."""
        hm = has_many("Post", filter=[is_in("status", ["a", "b"])])
        assert hm.filter.conditions[0].value == ["a", "b"]


# =============================================================================
# Test Real-World Filter Patterns
# =============================================================================

class TestHasManyRealWorldPatterns:
    """Test real-world filter patterns with HasMany."""
    
    def test_active_posts_filter(self):
        """Only active posts."""
        hm = has_many("Post", filter=[eq("is_active", True)])
        cond = hm.filter.conditions[0]
        assert cond.field == "is_active"
        assert cond.value is True
    
    def test_recent_posts_filter(self):
        """Posts from last 30 days."""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        hm = has_many("Post", filter=[gte("created_at", thirty_days_ago)])
        cond = hm.filter.conditions[0]
        assert cond.field == "created_at"
        assert cond.operator == ">="
    
    def test_popular_posts_filter(self):
        """Posts with high views."""
        hm = has_many("Post", filter=[gte("views", 1000)])
        cond = hm.filter.conditions[0]
        assert cond.field == "views"
        assert cond.value == 1000
    
    def test_non_deleted_filter(self):
        """Non-deleted posts (soft delete)."""
        hm = has_many("Post", filter=[is_null("deleted_at")])
        cond = hm.filter.conditions[0]
        assert cond.operator == "IS NULL"
    
    def test_published_status_filter(self):
        """Published posts only."""
        hm = has_many("Post", filter=[eq("status", "published")])
        cond = hm.filter.conditions[0]
        assert cond.value == "published"
    
    def test_category_filter(self):
        """Posts in specific categories."""
        hm = has_many("Post", filter=[is_in("category", ["tech", "news"])])
        cond = hm.filter.conditions[0]
        assert cond.value == ["tech", "news"]
    
    def test_complex_filter(self):
        """Complex filter with multiple conditions."""
        hm = has_many("Post", filter=[
            eq("is_active", True),
            is_null("deleted_at"),
            gte("views", 100),
            ne("status", "draft"),
        ])
        assert len(hm.filter.conditions) == 4
    
    def test_search_filter(self):
        """Title search filter."""
        hm = has_many("Post", filter=[like("title", "%python%")])
        cond = hm.filter.conditions[0]
        assert cond.operator == "LIKE"
        assert cond.value == "%python%"


# =============================================================================
# Test HasMany with Loading Strategies + Filter
# =============================================================================

class TestHasManyFilterWithLoading:
    """Test HasMany filter combined with loading strategies."""
    
    def test_filter_with_select(self):
        """Filter with select loading."""
        hm = has_many("Post", lazy="select", filter=[eq("is_active", True)])
        assert hm.lazy == "select"
        assert hm.filter is not None
    
    def test_filter_with_selectin(self):
        """Filter with selectin loading."""
        hm = has_many("Post", lazy="selectin", filter=[eq("is_active", True)])
        assert hm.lazy == "selectin"
        assert hm.filter is not None
    
    def test_filter_with_subquery(self):
        """Filter with subquery loading."""
        hm = has_many("Post", lazy="subquery", filter=[eq("is_active", True)])
        assert hm.lazy == "subquery"
    
    def test_filter_with_raise(self):
        """Filter with raise loading."""
        hm = has_many("Post", lazy="raise", filter=[eq("is_active", True)])
        assert hm.lazy == "raise"
    
    def test_filter_with_dynamic(self):
        """Filter with dynamic loading."""
        hm = has_many("Post", lazy="dynamic", filter=[eq("is_active", True)])
        assert hm.lazy == "dynamic"
        assert hm.filter is not None


# =============================================================================
# Test HasMany Filter Edge Cases
# =============================================================================

class TestHasManyFilterEdgeCases:
    """Test edge cases for HasMany with filter."""
    
    def test_empty_filter_list(self):
        """Empty filter list."""
        hm = has_many("Post", filter=[])
        # Empty list should result in None filter
        assert hm.filter is None or len(hm.filter.conditions) == 0
    
    def test_filter_with_empty_string_value(self):
        """Filter with empty string value."""
        hm = has_many("Post", filter=[ne("title", "")])
        assert hm.filter.conditions[0].value == ""
    
    def test_filter_with_zero_value(self):
        """Filter with zero value."""
        hm = has_many("Post", filter=[gt("price", 0)])
        assert hm.filter.conditions[0].value == 0
    
    def test_filter_with_negative_value(self):
        """Filter with negative value."""
        hm = has_many("Post", filter=[gt("balance", -100)])
        assert hm.filter.conditions[0].value == -100
    
    def test_filter_same_field_twice(self):
        """Same field filtered twice (range)."""
        hm = has_many("Post", filter=[
            gte("price", 10),
            lte("price", 100),
        ])
        assert len(hm.filter.conditions) == 2
        assert hm.filter.conditions[0].field == "price"
        assert hm.filter.conditions[1].field == "price"


# =============================================================================
# Test HasMany Filter Attribute Access
# =============================================================================

class TestHasManyFilterAccess:
    """Test accessing filter from HasMany."""
    
    def test_filter_property_returns_filter(self):
        """filter property returns RelationshipFilter."""
        hm = has_many("Post", filter=[eq("is_active", True)])
        assert isinstance(hm.filter, RelationshipFilter)
    
    def test_filter_conditions_accessible(self):
        """Filter conditions are accessible."""
        hm = has_many("Post", filter=[eq("is_active", True)])
        conditions = hm.filter.conditions
        assert len(conditions) == 1
        assert conditions[0].field == "is_active"
    
    def test_filter_property_cached(self):
        """filter property is cached after first access."""
        hm = has_many("Post", filter=[eq("is_active", True)])
        filter1 = hm.filter
        filter2 = hm.filter
        assert filter1 is filter2


# =============================================================================
# Test HasMany with All Parameters
# =============================================================================

class TestHasManyAllParameters:
    """Test HasMany with all parameters including filter."""
    
    def test_all_parameters(self):
        """HasMany with all parameters."""
        hm = HasMany(
            rel_name="posts",
            model="Post",
            foreign_key="author_id",
            backref="author",
            back_populates=None,
            lazy="selectin",
            on_delete="cascade",
            cascade=None,
            filter=[eq("is_active", True)],
        )
        assert hm.rel_name == "posts"
        assert hm.foreign_key == "author_id"
        assert hm.backref == "author"
        assert hm.lazy == "selectin"
        assert hm.on_delete == "cascade"
        assert hm.filter is not None
    
    def test_factory_all_parameters(self):
        """has_many factory with all parameters."""
        hm = has_many(
            "Post",
            foreign_key="author_id",
            backref="author",
            lazy="selectin",
            on_delete="cascade",
            filter=[eq("is_active", True)],
        )
        assert hm.backref == "author"
        assert hm.lazy == "selectin"
        assert hm.on_delete == "cascade"
        assert hm._filter_input is not None

