"""
Test Phase 7.5: HasOne with Filters.

These tests verify that:
1. HasOne accepts filter parameter
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
    HasOne,
    has_one,
)


# =============================================================================
# Test HasOne with filter Parameter
# =============================================================================

class TestHasOneFilterParameter:
    """Test HasOne descriptor with filter parameter."""
    
    def test_has_one_no_filter(self):
        """HasOne without filter."""
        ho = HasOne(
            rel_name="profile",
            model="Profile",
            foreign_key="user_id",
        )
        assert ho._filter_input is None
        assert ho.filter is None
    
    def test_has_one_with_filter_functions(self):
        """HasOne with condition function filters."""
        ho = HasOne(
            rel_name="active_profile",
            model="Profile",
            foreign_key="user_id",
            filter=[eq("is_active", True)],
        )
        assert ho._filter_input is not None
        assert ho.filter is not None
        assert len(ho.filter.conditions) == 1
    
    def test_has_one_with_filter_tuples(self):
        """HasOne with tuple filters."""
        ho = HasOne(
            rel_name="profile",
            model="Profile",
            foreign_key="user_id",
            filter=[("is_active", "=", True)],
        )
        assert ho.filter is not None
        assert ho.filter.conditions[0].operator == "="
    
    def test_has_one_with_filter_mixed(self):
        """HasOne with mixed filters."""
        ho = HasOne(
            rel_name="profile",
            model="Profile",
            foreign_key="user_id",
            filter=[
                eq("is_active", True),
                ("verified", "=", True),
            ],
        )
        assert len(ho.filter.conditions) == 2
    
    def test_has_one_filter_lazy_parse(self):
        """Filter is lazily parsed."""
        conditions = [eq("is_active", True)]
        ho = HasOne(
            rel_name="profile",
            model="Profile",
            foreign_key="user_id",
            filter=conditions,
        )
        assert ho._filter is None
        _ = ho.filter
        assert ho._filter is not None


# =============================================================================
# Test has_one Factory Function with Filter
# =============================================================================

class TestHasOneFactoryWithFilter:
    """Test has_one() factory function with filter."""
    
    def test_has_one_factory_no_filter(self):
        """has_one() without filter."""
        ho = has_one("Profile")
        assert ho._filter_input is None
    
    def test_has_one_factory_with_filter(self):
        """has_one() with filter."""
        ho = has_one("Profile", filter=[eq("is_active", True)])
        assert ho._filter_input is not None
    
    def test_has_one_factory_filter_and_backref(self):
        """has_one() with both filter and backref."""
        ho = has_one(
            "Profile",
            backref="user",
            filter=[eq("is_active", True)],
        )
        assert ho.backref == "user"
        assert ho._filter_input is not None
    
    def test_has_one_factory_filter_and_lazy(self):
        """has_one() with both filter and lazy."""
        ho = has_one(
            "Profile",
            lazy="joined",
            filter=[eq("is_active", True)],
        )
        assert ho.lazy == "joined"
        assert ho._filter_input is not None
    
    def test_has_one_factory_filter_and_cascade(self):
        """has_one() with filter and cascade."""
        ho = has_one(
            "Profile",
            on_delete="cascade",
            filter=[eq("is_active", True)],
        )
        assert ho.on_delete == "cascade"
        assert ho._filter_input is not None


# =============================================================================
# Test Multiple Filters
# =============================================================================

class TestHasOneMultipleFilters:
    """Test HasOne with multiple filter conditions."""
    
    def test_two_conditions(self):
        """Two filter conditions."""
        ho = has_one("Profile", filter=[
            eq("is_active", True),
            eq("verified", True),
        ])
        assert len(ho.filter.conditions) == 2
    
    def test_three_conditions(self):
        """Three filter conditions."""
        ho = has_one("Profile", filter=[
            eq("is_active", True),
            eq("verified", True),
            is_null("deleted_at"),
        ])
        assert len(ho.filter.conditions) == 3
    
    def test_all_operator_types(self):
        """All operator types in filter."""
        ho = has_one("Profile", filter=[
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
        assert len(ho.filter.conditions) == 9


# =============================================================================
# Test Real-World Filter Patterns
# =============================================================================

class TestHasOneRealWorldPatterns:
    """Test real-world filter patterns with HasOne."""
    
    def test_active_profile_filter(self):
        """Only active profile."""
        ho = has_one("Profile", filter=[eq("is_active", True)])
        cond = ho.filter.conditions[0]
        assert cond.field == "is_active"
        assert cond.value is True
    
    def test_verified_profile_filter(self):
        """Only verified profile."""
        ho = has_one("Profile", filter=[eq("verified", True)])
        cond = ho.filter.conditions[0]
        assert cond.field == "verified"
    
    def test_non_deleted_filter(self):
        """Non-deleted profile (soft delete)."""
        ho = has_one("Profile", filter=[is_null("deleted_at")])
        cond = ho.filter.conditions[0]
        assert cond.operator == "IS NULL"
    
    def test_type_filter(self):
        """Profile of specific type."""
        ho = has_one("Profile", filter=[eq("type", "premium")])
        cond = ho.filter.conditions[0]
        assert cond.value == "premium"
    
    def test_complex_filter(self):
        """Complex filter with multiple conditions."""
        ho = has_one("Profile", filter=[
            eq("is_active", True),
            is_null("deleted_at"),
            eq("verified", True),
        ])
        assert len(ho.filter.conditions) == 3


# =============================================================================
# Test HasOne with Loading Strategies + Filter
# =============================================================================

class TestHasOneFilterWithLoading:
    """Test HasOne filter combined with loading strategies."""
    
    def test_filter_with_select(self):
        """Filter with select loading."""
        ho = has_one("Profile", lazy="select", filter=[eq("is_active", True)])
        assert ho.lazy == "select"
        assert ho.filter is not None
    
    def test_filter_with_joined(self):
        """Filter with joined loading."""
        ho = has_one("Profile", lazy="joined", filter=[eq("is_active", True)])
        assert ho.lazy == "joined"
        assert ho.filter is not None
    
    def test_filter_with_selectin(self):
        """Filter with selectin loading."""
        ho = has_one("Profile", lazy="selectin", filter=[eq("is_active", True)])
        assert ho.lazy == "selectin"
    
    def test_filter_with_raise(self):
        """Filter with raise loading."""
        ho = has_one("Profile", lazy="raise", filter=[eq("is_active", True)])
        assert ho.lazy == "raise"


# =============================================================================
# Test HasOne Filter Edge Cases
# =============================================================================

class TestHasOneFilterEdgeCases:
    """Test edge cases for HasOne with filter."""
    
    def test_empty_filter_list(self):
        """Empty filter list."""
        ho = has_one("Profile", filter=[])
        assert ho.filter is None or len(ho.filter.conditions) == 0
    
    def test_filter_with_empty_string_value(self):
        """Filter with empty string value."""
        ho = has_one("Profile", filter=[ne("bio", "")])
        assert ho.filter.conditions[0].value == ""
    
    def test_filter_same_field_twice(self):
        """Same field filtered twice (range)."""
        ho = has_one("Profile", filter=[
            gte("age", 18),
            lte("age", 65),
        ])
        assert len(ho.filter.conditions) == 2


# =============================================================================
# Test HasOne Filter Attribute Access
# =============================================================================

class TestHasOneFilterAccess:
    """Test accessing filter from HasOne."""
    
    def test_filter_property_returns_filter(self):
        """filter property returns RelationshipFilter."""
        ho = has_one("Profile", filter=[eq("is_active", True)])
        assert isinstance(ho.filter, RelationshipFilter)
    
    def test_filter_conditions_accessible(self):
        """Filter conditions are accessible."""
        ho = has_one("Profile", filter=[eq("is_active", True)])
        conditions = ho.filter.conditions
        assert len(conditions) == 1
        assert conditions[0].field == "is_active"
    
    def test_filter_property_cached(self):
        """filter property is cached after first access."""
        ho = has_one("Profile", filter=[eq("is_active", True)])
        filter1 = ho.filter
        filter2 = ho.filter
        assert filter1 is filter2


# =============================================================================
# Test HasOne with All Parameters
# =============================================================================

class TestHasOneAllParameters:
    """Test HasOne with all parameters including filter."""
    
    def test_all_parameters(self):
        """HasOne with all parameters."""
        ho = HasOne(
            rel_name="profile",
            model="Profile",
            foreign_key="user_id",
            backref="user",
            back_populates=None,
            lazy="joined",
            on_delete="cascade",
            cascade=None,
            filter=[eq("is_active", True)],
        )
        assert ho.rel_name == "profile"
        assert ho.foreign_key == "user_id"
        assert ho.backref == "user"
        assert ho.lazy == "joined"
        assert ho.on_delete == "cascade"
        assert ho.filter is not None
    
    def test_factory_all_parameters(self):
        """has_one factory with all parameters."""
        ho = has_one(
            "Profile",
            foreign_key="user_id",
            backref="user",
            lazy="joined",
            on_delete="cascade",
            filter=[eq("is_active", True)],
        )
        assert ho.backref == "user"
        assert ho.lazy == "joined"
        assert ho.on_delete == "cascade"
        assert ho._filter_input is not None


# =============================================================================
# Test HasOne Filter Value Types
# =============================================================================

class TestHasOneFilterValues:
    """Test HasOne with various filter value types."""
    
    def test_filter_boolean(self):
        """Filter with boolean."""
        ho = has_one("Profile", filter=[eq("is_active", True)])
        assert ho.filter.conditions[0].value is True
    
    def test_filter_integer(self):
        """Filter with integer."""
        ho = has_one("Profile", filter=[gte("level", 5)])
        assert ho.filter.conditions[0].value == 5
    
    def test_filter_string(self):
        """Filter with string."""
        ho = has_one("Profile", filter=[eq("type", "premium")])
        assert ho.filter.conditions[0].value == "premium"
    
    def test_filter_datetime(self):
        """Filter with datetime."""
        dt = datetime.now() - timedelta(days=30)
        ho = has_one("Profile", filter=[gte("created_at", dt)])
        assert ho.filter.conditions[0].value == dt
    
    def test_filter_list(self):
        """Filter with list (IN)."""
        ho = has_one("Profile", filter=[is_in("type", ["a", "b"])])
        assert ho.filter.conditions[0].value == ["a", "b"]

