"""
Test Phase 7.5: Filter Integration with Loading Strategies.

These tests verify that:
1. Filters work with all loading strategies
2. Filters integrate correctly with query building
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Optional
from unittest.mock import Mock, MagicMock, patch

from pynext.db.relationships.conditions import (
    Condition,
    eq, ne, gt, gte, lt, lte,
    like, is_in, is_null,
)
from pynext.db.relationships.filter import RelationshipFilter, parse_filter
from pynext.db.relationships.core import (
    HasMany,
    HasOne,
    BelongsTo,
    ManyToMany,
    has_many,
    has_one,
    belongs_to,
    many_to_many,
)


# =============================================================================
# Test Filters with Select Loading
# =============================================================================

class TestFilterWithSelectLoading:
    """Test filter with select (lazy) loading."""
    
    def test_has_many_select_with_filter(self):
        """HasMany with select loading and filter."""
        hm = has_many("Post", lazy="select", filter=[eq("is_active", True)])
        assert hm.lazy == "select"
        assert hm.filter is not None
        assert hm.filter.conditions[0].field == "is_active"
    
    def test_has_one_select_with_filter(self):
        """HasOne with select loading and filter."""
        ho = has_one("Profile", lazy="select", filter=[eq("is_active", True)])
        assert ho.lazy == "select"
        assert ho.filter is not None
    
    def test_belongs_to_select_with_filter(self):
        """BelongsTo with select loading and filter."""
        bt = belongs_to("User", lazy="select", filter=[eq("is_active", True)])
        assert bt.lazy == "select"
        assert bt.filter is not None
    
    def test_m2m_select_with_filter(self):
        """ManyToMany with select loading and filter."""
        m2m = many_to_many("Course", lazy="select", filter=[eq("is_active", True)])
        assert m2m.lazy == "select"
        assert m2m.filter is not None


# =============================================================================
# Test Filters with Selectin Loading
# =============================================================================

class TestFilterWithSelectinLoading:
    """Test filter with selectin (batch) loading."""
    
    def test_has_many_selectin_with_filter(self):
        """HasMany with selectin loading and filter."""
        hm = has_many("Post", lazy="selectin", filter=[eq("is_active", True)])
        assert hm.lazy == "selectin"
        assert hm.filter is not None
    
    def test_has_one_selectin_with_filter(self):
        """HasOne with selectin loading and filter."""
        ho = has_one("Profile", lazy="selectin", filter=[eq("is_active", True)])
        assert ho.lazy == "selectin"
        assert ho.filter is not None
    
    def test_m2m_selectin_with_filter(self):
        """ManyToMany with selectin loading and filter."""
        m2m = many_to_many("Course", lazy="selectin", filter=[eq("is_active", True)])
        assert m2m.lazy == "selectin"
        assert m2m.filter is not None


# =============================================================================
# Test Filters with Subquery Loading
# =============================================================================

class TestFilterWithSubqueryLoading:
    """Test filter with subquery loading."""
    
    def test_has_many_subquery_with_filter(self):
        """HasMany with subquery loading and filter."""
        hm = has_many("Post", lazy="subquery", filter=[eq("is_active", True)])
        assert hm.lazy == "subquery"
        assert hm.filter is not None
    
    def test_m2m_subquery_with_filter(self):
        """ManyToMany with subquery loading and filter."""
        m2m = many_to_many("Course", lazy="subquery", filter=[eq("is_active", True)])
        assert m2m.lazy == "subquery"
        assert m2m.filter is not None


# =============================================================================
# Test Filters with Joined Loading
# =============================================================================

class TestFilterWithJoinedLoading:
    """Test filter with joined (eager) loading."""
    
    def test_has_one_joined_with_filter(self):
        """HasOne with joined loading and filter."""
        ho = has_one("Profile", lazy="joined", filter=[eq("is_active", True)])
        assert ho.lazy == "joined"
        assert ho.filter is not None
    
    def test_belongs_to_joined_with_filter(self):
        """BelongsTo with joined loading and filter."""
        bt = belongs_to("User", lazy="joined", filter=[eq("is_active", True)])
        assert bt.lazy == "joined"
        assert bt.filter is not None


# =============================================================================
# Test Filters with Raise Loading
# =============================================================================

class TestFilterWithRaiseLoading:
    """Test filter with raise loading (N+1 prevention)."""
    
    def test_has_many_raise_with_filter(self):
        """HasMany with raise loading and filter."""
        hm = has_many("Post", lazy="raise", filter=[eq("is_active", True)])
        assert hm.lazy == "raise"
        assert hm.filter is not None
    
    def test_has_one_raise_with_filter(self):
        """HasOne with raise loading and filter."""
        ho = has_one("Profile", lazy="raise", filter=[eq("is_active", True)])
        assert ho.lazy == "raise"
        assert ho.filter is not None
    
    def test_belongs_to_raise_with_filter(self):
        """BelongsTo with raise loading and filter."""
        bt = belongs_to("User", lazy="raise", filter=[eq("is_active", True)])
        assert bt.lazy == "raise"
        assert bt.filter is not None
    
    def test_m2m_raise_with_filter(self):
        """ManyToMany with raise loading and filter."""
        m2m = many_to_many("Course", lazy="raise", filter=[eq("is_active", True)])
        assert m2m.lazy == "raise"
        assert m2m.filter is not None


# =============================================================================
# Test Filters with Dynamic Loading
# =============================================================================

class TestFilterWithDynamicLoading:
    """Test filter with dynamic loading."""
    
    def test_has_many_dynamic_with_filter(self):
        """HasMany with dynamic loading and filter."""
        hm = has_many("Post", lazy="dynamic", filter=[eq("is_active", True)])
        assert hm.lazy == "dynamic"
        assert hm.filter is not None
    
    def test_m2m_dynamic_with_filter(self):
        """ManyToMany with dynamic loading and filter."""
        m2m = many_to_many("Course", lazy="dynamic", filter=[eq("is_active", True)])
        assert m2m.lazy == "dynamic"
        assert m2m.filter is not None


# =============================================================================
# Test Complex Filter + Loading Combinations
# =============================================================================

class TestComplexFilterLoadingCombinations:
    """Test complex filter and loading combinations."""
    
    def test_multiple_filters_with_selectin(self):
        """Multiple filters with selectin loading."""
        hm = has_many("Post", lazy="selectin", filter=[
            eq("is_active", True),
            gte("views", 100),
            is_null("deleted_at"),
        ])
        assert hm.lazy == "selectin"
        assert len(hm.filter.conditions) == 3
    
    def test_date_filter_with_selectin(self):
        """Date filter with selectin loading."""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        hm = has_many("Post", lazy="selectin", filter=[
            gte("created_at", thirty_days_ago),
        ])
        assert hm.lazy == "selectin"
        assert hm.filter.conditions[0].field == "created_at"
    
    def test_in_filter_with_subquery(self):
        """IN filter with subquery loading."""
        hm = has_many("Post", lazy="subquery", filter=[
            is_in("status", ["published", "featured"]),
        ])
        assert hm.lazy == "subquery"
        assert hm.filter.conditions[0].operator == "IN"
    
    def test_like_filter_with_dynamic(self):
        """LIKE filter with dynamic loading."""
        hm = has_many("Post", lazy="dynamic", filter=[
            like("title", "%python%"),
        ])
        assert hm.lazy == "dynamic"
        assert hm.filter.conditions[0].operator == "LIKE"


# =============================================================================
# Test Filter with Backref + Loading
# =============================================================================

class TestFilterWithBackrefAndLoading:
    """Test filter combined with backref and loading."""
    
    def test_filter_backref_selectin(self):
        """Filter + backref + selectin."""
        hm = has_many(
            "Post",
            backref="author",
            lazy="selectin",
            filter=[eq("is_active", True)],
        )
        assert hm.backref == "author"
        assert hm.lazy == "selectin"
        assert hm.filter is not None
    
    def test_filter_back_populates_joined(self):
        """Filter + back_populates + joined."""
        bt = belongs_to(
            "User",
            back_populates="posts",
            lazy="joined",
            filter=[eq("is_active", True)],
        )
        assert bt.back_populates == "posts"
        assert bt.lazy == "joined"
        assert bt.filter is not None
    
    def test_filter_backref_m2m_selectin(self):
        """Filter + backref + selectin for M2M."""
        m2m = many_to_many(
            "Course",
            backref="students",
            lazy="selectin",
            filter=[eq("is_active", True)],
        )
        assert m2m.backref == "students"
        assert m2m.lazy == "selectin"
        assert m2m.filter is not None


# =============================================================================
# Test Filter with Cascade + Loading
# =============================================================================

class TestFilterWithCascadeAndLoading:
    """Test filter combined with cascade and loading."""
    
    def test_filter_cascade_selectin(self):
        """Filter + cascade + selectin."""
        hm = has_many(
            "Post",
            on_delete="cascade",
            lazy="selectin",
            filter=[eq("is_active", True)],
        )
        assert hm.on_delete == "cascade"
        assert hm.lazy == "selectin"
        assert hm.filter is not None
    
    def test_filter_protect_raise(self):
        """Filter + protect + raise loading."""
        hm = has_many(
            "Post",
            on_delete="protect",
            lazy="raise",
            filter=[eq("is_active", True)],
        )
        assert hm.on_delete == "protect"
        assert hm.lazy == "raise"
        assert hm.filter is not None


# =============================================================================
# Test Filter Preservation Through Loading Strategy Changes
# =============================================================================

class TestFilterPreservation:
    """Test that filters are preserved correctly."""
    
    def test_filter_accessible_after_creation(self):
        """Filter is accessible after relationship creation."""
        hm = has_many("Post", lazy="selectin", filter=[eq("is_active", True)])
        # Access filter multiple times
        f1 = hm.filter
        f2 = hm.filter
        assert f1 is f2
        assert len(f1.conditions) == 1
    
    def test_filter_conditions_immutable(self):
        """Filter conditions are correctly stored."""
        conditions = [eq("is_active", True), gte("views", 100)]
        hm = has_many("Post", filter=conditions)
        assert len(hm.filter.conditions) == 2
        # Original conditions shouldn't affect filter
        conditions.append(eq("extra", True))
        assert len(hm.filter.conditions) == 2


# =============================================================================
# Test All Relationship Types with All Loading Strategies
# =============================================================================

class TestAllCombinations:
    """Test all relationship types with all loading strategies and filters."""
    
    def test_has_many_all_strategies(self):
        """HasMany with all loading strategies + filter."""
        strategies = ["select", "selectin", "subquery", "raise", "dynamic"]
        for strategy in strategies:
            hm = has_many("Post", lazy=strategy, filter=[eq("a", 1)])
            assert hm.lazy == strategy
            assert hm.filter is not None
    
    def test_has_one_all_strategies(self):
        """HasOne with all loading strategies + filter."""
        strategies = ["select", "joined", "selectin", "raise"]
        for strategy in strategies:
            ho = has_one("Profile", lazy=strategy, filter=[eq("a", 1)])
            assert ho.lazy == strategy
            assert ho.filter is not None
    
    def test_belongs_to_all_strategies(self):
        """BelongsTo with all loading strategies + filter."""
        strategies = ["select", "joined", "raise"]
        for strategy in strategies:
            bt = belongs_to("User", lazy=strategy, filter=[eq("a", 1)])
            assert bt.lazy == strategy
            assert bt.filter is not None
    
    def test_m2m_all_strategies(self):
        """ManyToMany with all loading strategies + filter."""
        strategies = ["select", "selectin", "subquery", "raise", "dynamic"]
        for strategy in strategies:
            m2m = many_to_many("Course", lazy=strategy, filter=[eq("a", 1)])
            assert m2m.lazy == strategy
            assert m2m.filter is not None


# =============================================================================
# Test Filter Edge Cases with Loading
# =============================================================================

class TestFilterLoadingEdgeCases:
    """Test edge cases for filter + loading combinations."""
    
    def test_empty_filter_with_selectin(self):
        """Empty filter list with selectin."""
        hm = has_many("Post", lazy="selectin", filter=[])
        assert hm.lazy == "selectin"
        # Empty filter should result in None or empty
        assert hm.filter is None or len(hm.filter.conditions) == 0
    
    def test_many_conditions_with_selectin(self):
        """Many filter conditions with selectin."""
        conditions = [eq(f"field_{i}", i) for i in range(20)]
        hm = has_many("Post", lazy="selectin", filter=conditions)
        assert len(hm.filter.conditions) == 20
    
    def test_complex_condition_with_dynamic(self):
        """Complex conditions with dynamic loading."""
        hm = has_many("Post", lazy="dynamic", filter=[
            eq("is_active", True),
            ne("status", "deleted"),
            gte("views", 100),
            lte("views", 10000),
            like("title", "%python%"),
            is_in("category", ["tech", "news"]),
            is_null("deleted_at"),
        ])
        assert hm.lazy == "dynamic"
        assert len(hm.filter.conditions) == 7

