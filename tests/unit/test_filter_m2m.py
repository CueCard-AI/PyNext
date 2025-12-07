"""
Test Phase 7.5: ManyToMany with Filters.

These tests verify that:
1. ManyToMany accepts filter parameter
2. Filter is correctly parsed and stored
3. Filter integrates with loading strategies
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Optional

from pynext.db.relationships.conditions import (
    Condition,
    eq, ne, gt, gte, lt, lte,
    like, is_in, is_null,
)
from pynext.db.relationships.filter import RelationshipFilter
from pynext.db.relationships.core import (
    ManyToMany,
    many_to_many,
)


# =============================================================================
# Test ManyToMany with filter Parameter
# =============================================================================

class TestManyToManyFilterParameter:
    """Test ManyToMany descriptor with filter parameter."""
    
    def test_m2m_no_filter(self):
        """ManyToMany without filter."""
        m2m = ManyToMany(
            rel_name="courses",
            model="Course",
        )
        assert m2m._filter_input is None
        assert m2m.filter is None
    
    def test_m2m_with_filter_functions(self):
        """ManyToMany with condition function filters."""
        m2m = ManyToMany(
            rel_name="active_courses",
            model="Course",
            filter=[eq("is_active", True)],
        )
        assert m2m._filter_input is not None
        assert m2m.filter is not None
        assert len(m2m.filter.conditions) == 1
    
    def test_m2m_with_filter_tuples(self):
        """ManyToMany with tuple filters."""
        m2m = ManyToMany(
            rel_name="courses",
            model="Course",
            filter=[("is_active", "=", True)],
        )
        assert m2m.filter is not None
        assert m2m.filter.conditions[0].operator == "="
    
    def test_m2m_with_filter_mixed(self):
        """ManyToMany with mixed filters."""
        m2m = ManyToMany(
            rel_name="courses",
            model="Course",
            filter=[
                eq("is_active", True),
                ("credits", ">=", 3),
            ],
        )
        assert len(m2m.filter.conditions) == 2
    
    def test_m2m_filter_lazy_parse(self):
        """Filter is lazily parsed."""
        conditions = [eq("is_active", True)]
        m2m = ManyToMany(
            rel_name="courses",
            model="Course",
            filter=conditions,
        )
        assert m2m._filter is None
        _ = m2m.filter
        assert m2m._filter is not None


# =============================================================================
# Test many_to_many Factory Function with Filter
# =============================================================================

class TestManyToManyFactoryWithFilter:
    """Test many_to_many() factory function with filter."""
    
    def test_m2m_factory_no_filter(self):
        """many_to_many() without filter."""
        m2m = many_to_many("Course")
        assert m2m._filter_input is None
    
    def test_m2m_factory_with_filter(self):
        """many_to_many() with filter."""
        m2m = many_to_many("Course", filter=[eq("is_active", True)])
        assert m2m._filter_input is not None
    
    def test_m2m_factory_filter_and_backref(self):
        """many_to_many() with both filter and backref."""
        m2m = many_to_many(
            "Course",
            backref="students",
            filter=[eq("is_active", True)],
        )
        assert m2m.backref == "students"
        assert m2m._filter_input is not None
    
    def test_m2m_factory_filter_and_lazy(self):
        """many_to_many() with both filter and lazy."""
        m2m = many_to_many(
            "Course",
            lazy="selectin",
            filter=[eq("is_active", True)],
        )
        assert m2m.lazy == "selectin"
        assert m2m._filter_input is not None
    
    def test_m2m_factory_filter_and_through(self):
        """many_to_many() with filter and through."""
        m2m = many_to_many(
            "Course",
            through="Enrollment",
            filter=[eq("is_active", True)],
        )
        assert m2m.through == "Enrollment"
        assert m2m._filter_input is not None
    
    def test_m2m_factory_filter_and_extra(self):
        """many_to_many() with filter and extra columns."""
        m2m = many_to_many(
            "Course",
            extra={"grade": str},
            filter=[eq("is_active", True)],
        )
        assert m2m.extra == {"grade": str}
        assert m2m._filter_input is not None
    
    def test_m2m_factory_filter_and_cascade(self):
        """many_to_many() with filter and cascade."""
        m2m = many_to_many(
            "Course",
            on_delete="cascade",
            filter=[eq("is_active", True)],
        )
        assert m2m.on_delete == "cascade"
        assert m2m._filter_input is not None


# =============================================================================
# Test Multiple Filters
# =============================================================================

class TestManyToManyMultipleFilters:
    """Test ManyToMany with multiple filter conditions."""
    
    def test_two_conditions(self):
        """Two filter conditions."""
        m2m = many_to_many("Course", filter=[
            eq("is_active", True),
            gte("credits", 3),
        ])
        assert len(m2m.filter.conditions) == 2
    
    def test_three_conditions(self):
        """Three filter conditions."""
        m2m = many_to_many("Course", filter=[
            eq("is_active", True),
            gte("credits", 3),
            is_null("deleted_at"),
        ])
        assert len(m2m.filter.conditions) == 3
    
    def test_many_conditions(self):
        """Many filter conditions."""
        conditions = [eq(f"field_{i}", i) for i in range(10)]
        m2m = many_to_many("Course", filter=conditions)
        assert len(m2m.filter.conditions) == 10
    
    def test_all_operator_types(self):
        """All operator types in filter."""
        m2m = many_to_many("Course", filter=[
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
        assert len(m2m.filter.conditions) == 9


# =============================================================================
# Test Real-World Filter Patterns
# =============================================================================

class TestManyToManyRealWorldPatterns:
    """Test real-world filter patterns with ManyToMany."""
    
    def test_active_courses_filter(self):
        """Only active courses."""
        m2m = many_to_many("Course", filter=[eq("is_active", True)])
        cond = m2m.filter.conditions[0]
        assert cond.field == "is_active"
        assert cond.value is True
    
    def test_current_semester_filter(self):
        """Courses from current semester."""
        m2m = many_to_many("Course", filter=[eq("semester", "Fall 2024")])
        cond = m2m.filter.conditions[0]
        assert cond.value == "Fall 2024"
    
    def test_minimum_credits_filter(self):
        """Courses with minimum credits."""
        m2m = many_to_many("Course", filter=[gte("credits", 3)])
        cond = m2m.filter.conditions[0]
        assert cond.value == 3
    
    def test_non_deleted_filter(self):
        """Non-deleted courses (soft delete)."""
        m2m = many_to_many("Course", filter=[is_null("deleted_at")])
        cond = m2m.filter.conditions[0]
        assert cond.operator == "IS NULL"
    
    def test_department_filter(self):
        """Courses in specific departments."""
        m2m = many_to_many("Course", filter=[is_in("department", ["CS", "Math"])])
        cond = m2m.filter.conditions[0]
        assert cond.value == ["CS", "Math"]
    
    def test_complex_filter(self):
        """Complex filter with multiple conditions."""
        m2m = many_to_many("Course", filter=[
            eq("is_active", True),
            is_null("deleted_at"),
            gte("credits", 3),
            is_in("level", ["undergraduate", "graduate"]),
        ])
        assert len(m2m.filter.conditions) == 4
    
    def test_search_filter(self):
        """Course name search filter."""
        m2m = many_to_many("Course", filter=[like("name", "%programming%")])
        cond = m2m.filter.conditions[0]
        assert cond.operator == "LIKE"


# =============================================================================
# Test ManyToMany with Loading Strategies + Filter
# =============================================================================

class TestManyToManyFilterWithLoading:
    """Test ManyToMany filter combined with loading strategies."""
    
    def test_filter_with_select(self):
        """Filter with select loading."""
        m2m = many_to_many("Course", lazy="select", filter=[eq("is_active", True)])
        assert m2m.lazy == "select"
        assert m2m.filter is not None
    
    def test_filter_with_selectin(self):
        """Filter with selectin loading."""
        m2m = many_to_many("Course", lazy="selectin", filter=[eq("is_active", True)])
        assert m2m.lazy == "selectin"
        assert m2m.filter is not None
    
    def test_filter_with_subquery(self):
        """Filter with subquery loading."""
        m2m = many_to_many("Course", lazy="subquery", filter=[eq("is_active", True)])
        assert m2m.lazy == "subquery"
    
    def test_filter_with_raise(self):
        """Filter with raise loading."""
        m2m = many_to_many("Course", lazy="raise", filter=[eq("is_active", True)])
        assert m2m.lazy == "raise"
    
    def test_filter_with_dynamic(self):
        """Filter with dynamic loading."""
        m2m = many_to_many("Course", lazy="dynamic", filter=[eq("is_active", True)])
        assert m2m.lazy == "dynamic"
        assert m2m.filter is not None


# =============================================================================
# Test ManyToMany Filter Edge Cases
# =============================================================================

class TestManyToManyFilterEdgeCases:
    """Test edge cases for ManyToMany with filter."""
    
    def test_empty_filter_list(self):
        """Empty filter list."""
        m2m = many_to_many("Course", filter=[])
        assert m2m.filter is None or len(m2m.filter.conditions) == 0
    
    def test_filter_with_empty_string_value(self):
        """Filter with empty string value."""
        m2m = many_to_many("Course", filter=[ne("description", "")])
        assert m2m.filter.conditions[0].value == ""
    
    def test_filter_with_zero_value(self):
        """Filter with zero value."""
        m2m = many_to_many("Course", filter=[gt("credits", 0)])
        assert m2m.filter.conditions[0].value == 0
    
    def test_filter_same_field_twice(self):
        """Same field filtered twice (range)."""
        m2m = many_to_many("Course", filter=[
            gte("credits", 1),
            lte("credits", 6),
        ])
        assert len(m2m.filter.conditions) == 2
        assert m2m.filter.conditions[0].field == "credits"
        assert m2m.filter.conditions[1].field == "credits"


# =============================================================================
# Test ManyToMany Filter Attribute Access
# =============================================================================

class TestManyToManyFilterAccess:
    """Test accessing filter from ManyToMany."""
    
    def test_filter_property_returns_filter(self):
        """filter property returns RelationshipFilter."""
        m2m = many_to_many("Course", filter=[eq("is_active", True)])
        assert isinstance(m2m.filter, RelationshipFilter)
    
    def test_filter_conditions_accessible(self):
        """Filter conditions are accessible."""
        m2m = many_to_many("Course", filter=[eq("is_active", True)])
        conditions = m2m.filter.conditions
        assert len(conditions) == 1
        assert conditions[0].field == "is_active"
    
    def test_filter_property_cached(self):
        """filter property is cached after first access."""
        m2m = many_to_many("Course", filter=[eq("is_active", True)])
        filter1 = m2m.filter
        filter2 = m2m.filter
        assert filter1 is filter2


# =============================================================================
# Test ManyToMany with All Parameters
# =============================================================================

class TestManyToManyAllParameters:
    """Test ManyToMany with all parameters including filter."""
    
    def test_all_parameters(self):
        """ManyToMany with all parameters."""
        m2m = ManyToMany(
            rel_name="courses",
            model="Course",
            through="Enrollment",
            backref="students",
            back_populates=None,
            lazy="selectin",
            extra={"grade": str},
            on_delete="cascade",
            cascade=None,
            filter=[eq("is_active", True)],
        )
        assert m2m.rel_name == "courses"
        assert m2m.through == "Enrollment"
        assert m2m.backref == "students"
        assert m2m.lazy == "selectin"
        assert m2m.extra == {"grade": str}
        assert m2m.on_delete == "cascade"
        assert m2m.filter is not None
    
    def test_factory_all_parameters(self):
        """many_to_many factory with all parameters."""
        m2m = many_to_many(
            "Course",
            through="Enrollment",
            backref="students",
            lazy="selectin",
            extra={"grade": str},
            on_delete="cascade",
            filter=[eq("is_active", True)],
        )
        assert m2m.through == "Enrollment"
        assert m2m.backref == "students"
        assert m2m.lazy == "selectin"
        assert m2m._filter_input is not None


# =============================================================================
# Test ManyToMany Filter Value Types
# =============================================================================

class TestManyToManyFilterValues:
    """Test ManyToMany with various filter value types."""
    
    def test_filter_boolean(self):
        """Filter with boolean."""
        m2m = many_to_many("Course", filter=[eq("is_active", True)])
        assert m2m.filter.conditions[0].value is True
    
    def test_filter_integer(self):
        """Filter with integer."""
        m2m = many_to_many("Course", filter=[gte("credits", 3)])
        assert m2m.filter.conditions[0].value == 3
    
    def test_filter_string(self):
        """Filter with string."""
        m2m = many_to_many("Course", filter=[eq("level", "advanced")])
        assert m2m.filter.conditions[0].value == "advanced"
    
    def test_filter_datetime(self):
        """Filter with datetime."""
        dt = datetime.now() - timedelta(days=30)
        m2m = many_to_many("Course", filter=[gte("created_at", dt)])
        assert m2m.filter.conditions[0].value == dt
    
    def test_filter_list(self):
        """Filter with list (IN)."""
        m2m = many_to_many("Course", filter=[is_in("department", ["CS", "Math"])])
        assert m2m.filter.conditions[0].value == ["CS", "Math"]


# =============================================================================
# Test ManyToMany with Backref Disabled + Filter
# =============================================================================

class TestManyToManyBackrefDisabledWithFilter:
    """Test ManyToMany with backref=False and filter."""
    
    def test_backref_false_with_filter(self):
        """Backref disabled with filter."""
        m2m = many_to_many(
            "Course",
            backref=False,
            filter=[eq("is_active", True)],
        )
        assert m2m._backref_disabled is True
        assert m2m.filter is not None
    
    def test_backref_none_with_filter(self):
        """Default backref with filter."""
        m2m = many_to_many(
            "Course",
            filter=[eq("is_active", True)],
        )
        # Default backref is None (auto-generated later)
        assert m2m._backref_raw is None
        assert m2m.filter is not None

