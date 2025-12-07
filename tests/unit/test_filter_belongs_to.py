"""
Test Phase 7.5: BelongsTo with Filters.

These tests verify that:
1. BelongsTo accepts filter parameter
2. Filter is correctly parsed and stored
3. Filter integrates with loading strategies
"""

import pytest
from datetime import datetime, timedelta
from typing import Optional

from pynext.db.relationships.conditions import (
    Condition,
    eq, ne, gt, gte, lt, lte,
    like, is_in, is_null,
)
from pynext.db.relationships.filter import RelationshipFilter
from pynext.db.relationships.core import (
    BelongsTo,
    belongs_to,
)


# =============================================================================
# Test BelongsTo with filter Parameter
# =============================================================================

class TestBelongsToFilterParameter:
    """Test BelongsTo descriptor with filter parameter."""
    
    def test_belongs_to_no_filter(self):
        """BelongsTo without filter."""
        bt = BelongsTo(
            rel_name="author",
            model="User",
            foreign_key="author_id",
        )
        assert bt._filter_input is None
        assert bt.filter is None
    
    def test_belongs_to_with_filter_functions(self):
        """BelongsTo with condition function filters."""
        bt = BelongsTo(
            rel_name="active_author",
            model="User",
            foreign_key="author_id",
            filter=[eq("is_active", True)],
        )
        assert bt._filter_input is not None
        assert bt.filter is not None
        assert len(bt.filter.conditions) == 1
    
    def test_belongs_to_with_filter_tuples(self):
        """BelongsTo with tuple filters."""
        bt = BelongsTo(
            rel_name="author",
            model="User",
            foreign_key="author_id",
            filter=[("is_active", "=", True)],
        )
        assert bt.filter is not None
        assert bt.filter.conditions[0].operator == "="
    
    def test_belongs_to_with_filter_mixed(self):
        """BelongsTo with mixed filters."""
        bt = BelongsTo(
            rel_name="author",
            model="User",
            foreign_key="author_id",
            filter=[
                eq("is_active", True),
                ("verified", "=", True),
            ],
        )
        assert len(bt.filter.conditions) == 2
    
    def test_belongs_to_filter_lazy_parse(self):
        """Filter is lazily parsed."""
        conditions = [eq("is_active", True)]
        bt = BelongsTo(
            rel_name="author",
            model="User",
            foreign_key="author_id",
            filter=conditions,
        )
        assert bt._filter is None
        _ = bt.filter
        assert bt._filter is not None


# =============================================================================
# Test belongs_to Factory Function with Filter
# =============================================================================

class TestBelongsToFactoryWithFilter:
    """Test belongs_to() factory function with filter."""
    
    def test_belongs_to_factory_no_filter(self):
        """belongs_to() without filter."""
        bt = belongs_to("User")
        assert bt._filter_input is None
    
    def test_belongs_to_factory_with_filter(self):
        """belongs_to() with filter."""
        bt = belongs_to("User", filter=[eq("is_active", True)])
        assert bt._filter_input is not None
    
    def test_belongs_to_factory_filter_and_backref(self):
        """belongs_to() with both filter and backref."""
        bt = belongs_to(
            "User",
            backref="posts",
            filter=[eq("is_active", True)],
        )
        assert bt.backref == "posts"
        assert bt._filter_input is not None
    
    def test_belongs_to_factory_filter_and_lazy(self):
        """belongs_to() with both filter and lazy."""
        bt = belongs_to(
            "User",
            lazy="joined",
            filter=[eq("is_active", True)],
        )
        assert bt.lazy == "joined"
        assert bt._filter_input is not None
    
    def test_belongs_to_factory_filter_and_foreign_key(self):
        """belongs_to() with filter and foreign_key."""
        bt = belongs_to(
            "User",
            foreign_key="author_id",
            filter=[eq("is_active", True)],
        )
        assert bt.foreign_key == "author_id"
        assert bt._filter_input is not None


# =============================================================================
# Test Multiple Filters
# =============================================================================

class TestBelongsToMultipleFilters:
    """Test BelongsTo with multiple filter conditions."""
    
    def test_two_conditions(self):
        """Two filter conditions."""
        bt = belongs_to("User", filter=[
            eq("is_active", True),
            eq("verified", True),
        ])
        assert len(bt.filter.conditions) == 2
    
    def test_three_conditions(self):
        """Three filter conditions."""
        bt = belongs_to("User", filter=[
            eq("is_active", True),
            eq("verified", True),
            is_null("deleted_at"),
        ])
        assert len(bt.filter.conditions) == 3
    
    def test_all_operator_types(self):
        """All operator types in filter."""
        bt = belongs_to("User", filter=[
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
        assert len(bt.filter.conditions) == 9


# =============================================================================
# Test Real-World Filter Patterns
# =============================================================================

class TestBelongsToRealWorldPatterns:
    """Test real-world filter patterns with BelongsTo."""
    
    def test_active_author_filter(self):
        """Only active author."""
        bt = belongs_to("User", filter=[eq("is_active", True)])
        cond = bt.filter.conditions[0]
        assert cond.field == "is_active"
        assert cond.value is True
    
    def test_verified_author_filter(self):
        """Only verified author."""
        bt = belongs_to("User", filter=[eq("verified", True)])
        cond = bt.filter.conditions[0]
        assert cond.field == "verified"
    
    def test_non_deleted_filter(self):
        """Non-deleted user (soft delete)."""
        bt = belongs_to("User", filter=[is_null("deleted_at")])
        cond = bt.filter.conditions[0]
        assert cond.operator == "IS NULL"
    
    def test_role_filter(self):
        """User of specific role."""
        bt = belongs_to("User", filter=[eq("role", "admin")])
        cond = bt.filter.conditions[0]
        assert cond.value == "admin"
    
    def test_complex_filter(self):
        """Complex filter with multiple conditions."""
        bt = belongs_to("User", filter=[
            eq("is_active", True),
            is_null("deleted_at"),
            is_in("role", ["admin", "editor"]),
        ])
        assert len(bt.filter.conditions) == 3


# =============================================================================
# Test BelongsTo with Loading Strategies + Filter
# =============================================================================

class TestBelongsToFilterWithLoading:
    """Test BelongsTo filter combined with loading strategies."""
    
    def test_filter_with_select(self):
        """Filter with select loading."""
        bt = belongs_to("User", lazy="select", filter=[eq("is_active", True)])
        assert bt.lazy == "select"
        assert bt.filter is not None
    
    def test_filter_with_joined(self):
        """Filter with joined loading."""
        bt = belongs_to("User", lazy="joined", filter=[eq("is_active", True)])
        assert bt.lazy == "joined"
        assert bt.filter is not None
    
    def test_filter_with_raise(self):
        """Filter with raise loading."""
        bt = belongs_to("User", lazy="raise", filter=[eq("is_active", True)])
        assert bt.lazy == "raise"


# =============================================================================
# Test BelongsTo Filter Edge Cases
# =============================================================================

class TestBelongsToFilterEdgeCases:
    """Test edge cases for BelongsTo with filter."""
    
    def test_empty_filter_list(self):
        """Empty filter list."""
        bt = belongs_to("User", filter=[])
        assert bt.filter is None or len(bt.filter.conditions) == 0
    
    def test_filter_with_empty_string_value(self):
        """Filter with empty string value."""
        bt = belongs_to("User", filter=[ne("name", "")])
        assert bt.filter.conditions[0].value == ""
    
    def test_filter_same_field_twice(self):
        """Same field filtered twice (range)."""
        bt = belongs_to("User", filter=[
            gte("age", 18),
            lte("age", 65),
        ])
        assert len(bt.filter.conditions) == 2


# =============================================================================
# Test BelongsTo Filter Attribute Access
# =============================================================================

class TestBelongsToFilterAccess:
    """Test accessing filter from BelongsTo."""
    
    def test_filter_property_returns_filter(self):
        """filter property returns RelationshipFilter."""
        bt = belongs_to("User", filter=[eq("is_active", True)])
        assert isinstance(bt.filter, RelationshipFilter)
    
    def test_filter_conditions_accessible(self):
        """Filter conditions are accessible."""
        bt = belongs_to("User", filter=[eq("is_active", True)])
        conditions = bt.filter.conditions
        assert len(conditions) == 1
        assert conditions[0].field == "is_active"
    
    def test_filter_property_cached(self):
        """filter property is cached after first access."""
        bt = belongs_to("User", filter=[eq("is_active", True)])
        filter1 = bt.filter
        filter2 = bt.filter
        assert filter1 is filter2


# =============================================================================
# Test BelongsTo with All Parameters
# =============================================================================

class TestBelongsToAllParameters:
    """Test BelongsTo with all parameters including filter."""
    
    def test_all_parameters(self):
        """BelongsTo with all parameters."""
        bt = BelongsTo(
            rel_name="author",
            model="User",
            foreign_key="author_id",
            backref="posts",
            back_populates=None,
            lazy="joined",
            filter=[eq("is_active", True)],
        )
        assert bt.rel_name == "author"
        assert bt.foreign_key == "author_id"
        assert bt.backref == "posts"
        assert bt.lazy == "joined"
        assert bt.filter is not None
    
    def test_factory_all_parameters(self):
        """belongs_to factory with all parameters."""
        bt = belongs_to(
            "User",
            foreign_key="author_id",
            backref="posts",
            lazy="joined",
            filter=[eq("is_active", True)],
        )
        assert bt.backref == "posts"
        assert bt.lazy == "joined"
        assert bt._filter_input is not None


# =============================================================================
# Test BelongsTo Filter Value Types
# =============================================================================

class TestBelongsToFilterValues:
    """Test BelongsTo with various filter value types."""
    
    def test_filter_boolean(self):
        """Filter with boolean."""
        bt = belongs_to("User", filter=[eq("is_active", True)])
        assert bt.filter.conditions[0].value is True
    
    def test_filter_integer(self):
        """Filter with integer."""
        bt = belongs_to("User", filter=[gte("level", 5)])
        assert bt.filter.conditions[0].value == 5
    
    def test_filter_string(self):
        """Filter with string."""
        bt = belongs_to("User", filter=[eq("role", "admin")])
        assert bt.filter.conditions[0].value == "admin"
    
    def test_filter_datetime(self):
        """Filter with datetime."""
        dt = datetime.now() - timedelta(days=30)
        bt = belongs_to("User", filter=[gte("created_at", dt)])
        assert bt.filter.conditions[0].value == dt
    
    def test_filter_list(self):
        """Filter with list (IN)."""
        bt = belongs_to("User", filter=[is_in("role", ["a", "b"])])
        assert bt.filter.conditions[0].value == ["a", "b"]

