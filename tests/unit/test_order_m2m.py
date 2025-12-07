"""
Tests for many_to_many with ordering.

Tests cover:
- many_to_many with order_by parameter
- Single and multiple column ordering
- Integration with ManyToMany descriptor
- Ordering with junction tables
"""

import pytest
from typing import List, Optional, Dict, Any
from datetime import datetime

from pynext.db.relationships.core import ManyToMany, many_to_many
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


class MockStudent(MockTable):
    """Mock Student model."""
    pass


class MockCourse(MockTable):
    """Mock Course model."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = kwargs.get("name", "Course")
        self.code = kwargs.get("code", "C101")
        self.created_at = kwargs.get("created_at", datetime.now())


class MockTag(MockTable):
    """Mock Tag model."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = kwargs.get("name", "Tag")
        self.position = kwargs.get("position", 0)


class MockEnrollment(MockTable):
    """Mock junction table."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.student_id = kwargs.get("student_id")
        self.course_id = kwargs.get("course_id")
        self.enrolled_at = kwargs.get("enrolled_at", datetime.now())
        self.grade = kwargs.get("grade")


# =============================================================================
# Test: many_to_many with order_by
# =============================================================================

class TestManyToManyOrderBy:
    """Test many_to_many function with order_by."""
    
    def test_many_to_many_accepts_order_by_string(self):
        """many_to_many accepts order_by string."""
        rel = many_to_many(MockCourse, order_by="name")
        assert rel._order_by_input == "name"
    
    def test_many_to_many_accepts_order_by_list(self):
        """many_to_many accepts order_by list."""
        rel = many_to_many(MockCourse, order_by=["code", "name desc"])
        assert rel._order_by_input == ["code", "name desc"]
    
    def test_many_to_many_order_by_none_default(self):
        """many_to_many order_by defaults to None."""
        rel = many_to_many(MockCourse)
        assert rel._order_by_input is None
    
    def test_many_to_many_ordering_property(self):
        """ManyToMany.ordering property returns OrderingConfig."""
        rel = many_to_many(MockCourse, order_by="name desc")
        rel.rel_name = "courses"
        
        ordering = rel.ordering
        assert isinstance(ordering, OrderingConfig)
        assert ordering.has_ordering
    
    def test_many_to_many_ordering_none_when_no_order_by(self):
        """ManyToMany.ordering is None when no order_by."""
        rel = many_to_many(MockCourse)
        rel.rel_name = "courses"
        
        assert rel.ordering is None
    
    def test_many_to_many_order_by_property(self):
        """ManyToMany.order_by returns raw value."""
        rel = many_to_many(MockCourse, order_by="name")
        rel.rel_name = "courses"
        
        assert rel.order_by == "name"


class TestManyToManyWithSingleColumn:
    """Test many_to_many with single column ordering."""
    
    def test_single_column_asc(self):
        """Single column ascending."""
        rel = many_to_many(MockCourse, order_by="name")
        rel.rel_name = "courses"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 1
        assert ordering.specs[0].column == "name"
        assert ordering.specs[0].direction == "asc"
    
    def test_single_column_desc(self):
        """Single column descending."""
        rel = many_to_many(MockCourse, order_by="created_at desc")
        rel.rel_name = "courses"
        
        ordering = rel.ordering
        assert ordering.specs[0].direction == "desc"
    
    def test_single_column_sql(self):
        """Single column generates correct SQL."""
        rel = many_to_many(MockCourse, order_by="name desc")
        rel.rel_name = "courses"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY name DESC"


class TestManyToManyWithMultipleColumns:
    """Test many_to_many with multiple column ordering."""
    
    def test_multiple_columns(self):
        """Multiple columns parsed correctly."""
        rel = many_to_many(MockCourse, order_by=["code", "name"])
        rel.rel_name = "courses"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 2
        assert ordering.specs[0].column == "code"
        assert ordering.specs[1].column == "name"
    
    def test_multiple_columns_mixed_direction(self):
        """Multiple columns with mixed directions."""
        rel = many_to_many(MockTag, order_by=["position", "name desc"])
        rel.rel_name = "tags"
        
        ordering = rel.ordering
        assert ordering.specs[0].direction == "asc"
        assert ordering.specs[1].direction == "desc"
    
    def test_multiple_columns_sql(self):
        """Multiple columns generate correct SQL."""
        rel = many_to_many(MockCourse, order_by=["code", "name desc"])
        rel.rel_name = "courses"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY code ASC, name DESC"


class TestManyToManyWithNulls:
    """Test many_to_many with NULLS FIRST/LAST."""
    
    def test_nulls_first(self):
        """NULLS FIRST parsed correctly."""
        rel = many_to_many(MockCourse, order_by="code nulls first")
        rel.rel_name = "courses"
        
        ordering = rel.ordering
        assert ordering.specs[0].nulls == "first"
    
    def test_nulls_last(self):
        """NULLS LAST parsed correctly."""
        rel = many_to_many(MockCourse, order_by="name nulls last")
        rel.rel_name = "courses"
        
        ordering = rel.ordering
        assert ordering.specs[0].nulls == "last"


class TestManyToManyDescriptor:
    """Test ManyToMany descriptor with ordering."""
    
    def test_many_to_many_class_stores_ordering(self):
        """ManyToMany class stores ordering config."""
        descriptor = ManyToMany(
            rel_name="courses",
            model=MockCourse,
            order_by="name desc"
        )
        
        assert descriptor._order_by_input == "name desc"
    
    def test_ordering_lazy_init(self):
        """Ordering is lazily initialized."""
        descriptor = ManyToMany(
            rel_name="courses",
            model=MockCourse,
            order_by="name desc"
        )
        
        # Initially None
        assert descriptor._ordering is None
        
        # Access triggers creation
        ordering = descriptor.ordering
        assert ordering is not None
    
    def test_ordering_cached(self):
        """Ordering is cached after first access."""
        descriptor = ManyToMany(
            rel_name="courses",
            model=MockCourse,
            order_by="name desc"
        )
        
        ordering1 = descriptor.ordering
        ordering2 = descriptor.ordering
        
        assert ordering1 is ordering2


class TestManyToManyWithOtherOptions:
    """Test many_to_many ordering combined with other options."""
    
    def test_with_backref(self):
        """Order_by works with backref."""
        rel = many_to_many(
            MockCourse,
            backref="students",
            order_by="name"
        )
        rel.rel_name = "courses"
        
        assert rel.backref == "students"
        assert rel.ordering.has_ordering
    
    def test_with_through(self):
        """Order_by works with through table."""
        rel = many_to_many(
            MockCourse,
            through=MockEnrollment,
            order_by="name"
        )
        rel.rel_name = "courses"
        
        assert rel.through == MockEnrollment
        assert rel.ordering.has_ordering
    
    def test_with_lazy(self):
        """Order_by works with lazy loading."""
        rel = many_to_many(
            MockCourse,
            lazy="selectin",
            order_by="name"
        )
        rel.rel_name = "courses"
        
        assert rel.lazy == "selectin"
        assert rel.ordering.has_ordering
    
    def test_with_extra(self):
        """Order_by works with extra columns."""
        rel = many_to_many(
            MockCourse,
            extra={"grade": Optional[str]},
            order_by="name"
        )
        rel.rel_name = "courses"
        
        assert rel.extra == {"grade": Optional[str]}
        assert rel.ordering.has_ordering
    
    def test_with_all_options(self):
        """Order_by works with all options combined."""
        rel = many_to_many(
            MockCourse,
            through=MockEnrollment,
            backref="students",
            lazy="selectin",
            order_by=["code", "name desc"]
        )
        rel.rel_name = "courses"
        
        assert rel.through == MockEnrollment
        assert rel.backref == "students"
        assert rel.lazy == "selectin"
        assert len(rel.ordering.specs) == 2


class TestManyToManyOrderingSql:
    """Test SQL generation for many_to_many ordering."""
    
    def test_sql_with_alias(self):
        """SQL with table alias."""
        rel = many_to_many(MockCourse, order_by="name desc")
        rel.rel_name = "courses"
        
        sql = rel.ordering.to_sql(table_alias="c")
        assert sql == "ORDER BY c.name DESC"
    
    def test_sql_without_keyword(self):
        """SQL without ORDER BY keyword."""
        rel = many_to_many(MockCourse, order_by="name desc")
        rel.rel_name = "courses"
        
        sql = rel.ordering.to_sql(include_keyword=False)
        assert sql == "name DESC"
    
    def test_get_columns_list(self):
        """Get ordered column list."""
        rel = many_to_many(MockCourse, order_by=["code", "name desc"])
        rel.rel_name = "courses"
        
        columns = rel.ordering.get_columns()
        assert columns == ["code ASC", "name DESC"]


class TestManyToManyEdgeCases:
    """Test edge cases for many_to_many ordering."""
    
    def test_empty_list_order_by(self):
        """Empty list order_by."""
        rel = many_to_many(MockCourse, order_by=[])
        rel.rel_name = "courses"
        
        assert rel._order_by_input == []
    
    def test_single_item_list(self):
        """Single item list order_by."""
        rel = many_to_many(MockCourse, order_by=["name"])
        rel.rel_name = "courses"
        
        ordering = rel.ordering
        assert len(ordering.specs) == 1
    
    def test_disabled_backref_with_order(self):
        """Ordering works with disabled backref."""
        rel = many_to_many(
            MockCourse,
            backref=False,
            order_by="name"
        )
        rel.rel_name = "courses"
        
        assert rel._backref_disabled == True
        assert rel.ordering.has_ordering


class TestManyToManyTyping:
    """Test many_to_many typing with ordering."""
    
    def test_return_type(self):
        """many_to_many returns ManyToMany."""
        rel = many_to_many(MockCourse, order_by="name")
        assert isinstance(rel, ManyToMany)
    
    def test_generic_type_preserved(self):
        """Generic type is preserved."""
        rel = many_to_many(MockCourse, order_by="name")
        assert rel._model == MockCourse

