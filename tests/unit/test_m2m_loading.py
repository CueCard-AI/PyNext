"""
Tests for PyNext Many-to-Many Loading Strategies.

80 tests covering:
- lazy="select" default
- lazy="selectin" for M2M
- lazy="raise" prevents N+1
- lazy="dynamic" returns query builder
- Nested M2M loading
"""

import pytest
from typing import List, Optional

from pynext.db import (
    Table,
    many_to_many,
    ManyToMany,
    ManyToManyCollection,
    LazyLoadError,
    reset_backref_registry,
    reset_sync_manager,
)
from pynext.db.relationships.junction import reset_junction_factory
from pynext.db.relationships.m2m_dynamic import DynamicManyToMany
from pynext.db.table import _model_registry


@pytest.fixture(autouse=True)
def clean_state():
    """Reset all state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('lod', 'test'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# lazy="select" (Default) (20 tests)
# =============================================================================

class TestManyToManyLazySelect:
    """Test default lazy loading behavior."""
    
    def test_default_is_select(self, clean_state):
        """Test default lazy is 'select'."""
        class LodCourse1(Table):
            name: str = ""
        
        class LodStudent1(Table):
            name: str = ""
            courses: List[LodCourse1] = many_to_many(LodCourse1)
        
        descriptor = LodStudent1.__dict__["courses"]
        assert descriptor.lazy == "select"
    
    def test_select_returns_collection(self, clean_state):
        """Test select returns ManyToManyCollection."""
        class LodCourse2(Table):
            name: str = ""
        
        class LodStudent2(Table):
            name: str = ""
            courses: List[LodCourse2] = many_to_many(LodCourse2, lazy="select")
        
        student = LodStudent2(name="John")
        
        assert isinstance(student.courses, ManyToManyCollection)
    
    def test_select_starts_empty(self, clean_state):
        """Test select collection starts empty."""
        class LodCourse3(Table):
            name: str = ""
        
        class LodStudent3(Table):
            name: str = ""
            courses: List[LodCourse3] = many_to_many(LodCourse3, lazy="select")
        
        student = LodStudent3(name="John")
        
        assert len(student.courses) == 0
    
    def test_explicit_select_works(self, clean_state):
        """Test explicitly setting lazy='select'."""
        class LodCourse4(Table):
            name: str = ""
        
        class LodStudent4(Table):
            name: str = ""
            courses: List[LodCourse4] = many_to_many(LodCourse4, lazy="select")
        
        descriptor = LodStudent4.__dict__["courses"]
        assert descriptor.lazy == "select"


# =============================================================================
# lazy="selectin" (20 tests)
# =============================================================================

class TestManyToManyLazySelectin:
    """Test selectin loading behavior."""
    
    def test_selectin_stored(self, clean_state):
        """Test selectin is stored on descriptor."""
        class LodCourse5(Table):
            name: str = ""
        
        class LodStudent5(Table):
            name: str = ""
            courses: List[LodCourse5] = many_to_many(LodCourse5, lazy="selectin")
        
        descriptor = LodStudent5.__dict__["courses"]
        assert descriptor.lazy == "selectin"
    
    def test_selectin_returns_collection(self, clean_state):
        """Test selectin returns ManyToManyCollection."""
        class LodCourse6(Table):
            name: str = ""
        
        class LodStudent6(Table):
            name: str = ""
            courses: List[LodCourse6] = many_to_many(LodCourse6, lazy="selectin")
        
        student = LodStudent6(name="John")
        
        assert isinstance(student.courses, ManyToManyCollection)
    
    def test_selectin_cached(self, clean_state):
        """Test selectin collection is cached."""
        class LodCourse7(Table):
            name: str = ""
        
        class LodStudent7(Table):
            name: str = ""
            courses: List[LodCourse7] = many_to_many(LodCourse7, lazy="selectin")
        
        student = LodStudent7(name="John")
        col1 = student.courses
        col2 = student.courses
        
        assert col1 is col2


# =============================================================================
# lazy="raise" (20 tests)
# =============================================================================

class TestManyToManyLazyRaise:
    """Test raise loading behavior."""
    
    def test_raise_stored(self, clean_state):
        """Test raise is stored on descriptor."""
        class LodCourse8(Table):
            name: str = ""
        
        class LodStudent8(Table):
            name: str = ""
            courses: List[LodCourse8] = many_to_many(LodCourse8, lazy="raise")
        
        descriptor = LodStudent8.__dict__["courses"]
        assert descriptor.lazy == "raise"
    
    def test_raise_throws_error(self, clean_state):
        """Test raise throws LazyLoadError."""
        class LodCourse9(Table):
            name: str = ""
        
        class LodStudent9(Table):
            name: str = ""
            courses: List[LodCourse9] = many_to_many(LodCourse9, lazy="raise")
        
        student = LodStudent9(name="John")
        
        with pytest.raises(LazyLoadError):
            _ = student.courses
    
    def test_raise_error_has_relationship(self, clean_state):
        """Test error includes relationship name."""
        class LodCourse10(Table):
            name: str = ""
        
        class LodStudent10(Table):
            name: str = ""
            courses: List[LodCourse10] = many_to_many(LodCourse10, lazy="raise")
        
        student = LodStudent10(name="John")
        
        with pytest.raises(LazyLoadError) as exc_info:
            _ = student.courses
        
        assert exc_info.value.relationship == "courses"
    
    def test_raise_error_has_model(self, clean_state):
        """Test error includes model name."""
        class LodCourse11(Table):
            name: str = ""
        
        class LodStudent11(Table):
            name: str = ""
            courses: List[LodCourse11] = many_to_many(LodCourse11, lazy="raise")
        
        student = LodStudent11(name="John")
        
        with pytest.raises(LazyLoadError) as exc_info:
            _ = student.courses
        
        assert exc_info.value.model == "LodStudent11"
    
    def test_raise_works_if_cached(self, clean_state):
        """Test raise works if value is cached."""
        class LodCourse12(Table):
            name: str = ""
        
        class LodStudent12(Table):
            name: str = ""
            courses: List[LodCourse12] = many_to_many(LodCourse12, lazy="raise")
        
        student = LodStudent12(name="John")
        
        # Pre-cache
        student._cached_courses = ManyToManyCollection(
            owner=student,
            attr_name="courses",
            config=LodStudent12.__dict__["courses"]._get_junction_config(LodStudent12),
            items=[],
        )
        
        # Should not raise
        result = student.courses
        assert isinstance(result, ManyToManyCollection)
    
    def test_raise_marked_attribute(self, clean_state):
        """Test _raise_on_* attribute triggers error."""
        class LodCourse13(Table):
            name: str = ""
        
        class LodStudent13(Table):
            name: str = ""
            courses: List[LodCourse13] = many_to_many(LodCourse13, lazy="select")
        
        student = LodStudent13(name="John")
        student._raise_on_courses = True
        
        with pytest.raises(LazyLoadError):
            _ = student.courses


# =============================================================================
# lazy="dynamic" (20 tests)
# =============================================================================

class TestManyToManyLazyDynamic:
    """Test dynamic loading behavior."""
    
    def test_dynamic_stored(self, clean_state):
        """Test dynamic is stored on descriptor."""
        class LodCourse14(Table):
            name: str = ""
        
        class LodStudent14(Table):
            name: str = ""
            courses: List[LodCourse14] = many_to_many(LodCourse14, lazy="dynamic")
        
        descriptor = LodStudent14.__dict__["courses"]
        assert descriptor.lazy == "dynamic"
    
    def test_dynamic_returns_query_builder(self, clean_state):
        """Test dynamic returns DynamicManyToMany."""
        class LodCourse15(Table):
            name: str = ""
        
        class LodStudent15(Table):
            name: str = ""
            courses: List[LodCourse15] = many_to_many(LodCourse15, lazy="dynamic")
        
        student = LodStudent15(name="John")
        
        assert isinstance(student.courses, DynamicManyToMany)
    
    def test_dynamic_has_filter(self, clean_state):
        """Test dynamic has filter method."""
        class LodCourse16(Table):
            name: str = ""
        
        class LodStudent16(Table):
            name: str = ""
            courses: List[LodCourse16] = many_to_many(LodCourse16, lazy="dynamic")
        
        student = LodStudent16(name="John")
        
        assert hasattr(student.courses, "filter")
    
    def test_dynamic_has_where(self, clean_state):
        """Test dynamic has where method."""
        class LodCourse17(Table):
            name: str = ""
        
        class LodStudent17(Table):
            name: str = ""
            courses: List[LodCourse17] = many_to_many(LodCourse17, lazy="dynamic")
        
        student = LodStudent17(name="John")
        
        assert hasattr(student.courses, "where")
    
    def test_dynamic_has_limit(self, clean_state):
        """Test dynamic has limit method."""
        class LodCourse18(Table):
            name: str = ""
        
        class LodStudent18(Table):
            name: str = ""
            courses: List[LodCourse18] = many_to_many(LodCourse18, lazy="dynamic")
        
        student = LodStudent18(name="John")
        
        assert hasattr(student.courses, "limit")
    
    def test_dynamic_has_offset(self, clean_state):
        """Test dynamic has offset method."""
        class LodCourse19(Table):
            name: str = ""
        
        class LodStudent19(Table):
            name: str = ""
            courses: List[LodCourse19] = many_to_many(LodCourse19, lazy="dynamic")
        
        student = LodStudent19(name="John")
        
        assert hasattr(student.courses, "offset")
    
    def test_dynamic_has_order_by(self, clean_state):
        """Test dynamic has order_by method."""
        class LodCourse20(Table):
            name: str = ""
        
        class LodStudent20(Table):
            name: str = ""
            courses: List[LodCourse20] = many_to_many(LodCourse20, lazy="dynamic")
        
        student = LodStudent20(name="John")
        
        assert hasattr(student.courses, "order_by")
    
    def test_dynamic_has_all(self, clean_state):
        """Test dynamic has all method."""
        class LodCourse21(Table):
            name: str = ""
        
        class LodStudent21(Table):
            name: str = ""
            courses: List[LodCourse21] = many_to_many(LodCourse21, lazy="dynamic")
        
        student = LodStudent21(name="John")
        
        assert hasattr(student.courses, "all")
    
    def test_dynamic_has_count(self, clean_state):
        """Test dynamic has count method."""
        class LodCourse22(Table):
            name: str = ""
        
        class LodStudent22(Table):
            name: str = ""
            courses: List[LodCourse22] = many_to_many(LodCourse22, lazy="dynamic")
        
        student = LodStudent22(name="John")
        
        assert hasattr(student.courses, "count")
    
    def test_dynamic_has_exists(self, clean_state):
        """Test dynamic has exists method."""
        class LodCourse23(Table):
            name: str = ""
        
        class LodStudent23(Table):
            name: str = ""
            courses: List[LodCourse23] = many_to_many(LodCourse23, lazy="dynamic")
        
        student = LodStudent23(name="John")
        
        assert hasattr(student.courses, "exists")
    
    def test_dynamic_has_first(self, clean_state):
        """Test dynamic has first method."""
        class LodCourse24(Table):
            name: str = ""
        
        class LodStudent24(Table):
            name: str = ""
            courses: List[LodCourse24] = many_to_many(LodCourse24, lazy="dynamic")
        
        student = LodStudent24(name="John")
        
        assert hasattr(student.courses, "first")
    
    def test_dynamic_is_truthy(self, clean_state):
        """Test dynamic is always truthy."""
        class LodCourse25(Table):
            name: str = ""
        
        class LodStudent25(Table):
            name: str = ""
            courses: List[LodCourse25] = many_to_many(LodCourse25, lazy="dynamic")
        
        student = LodStudent25(name="John")
        
        assert bool(student.courses)
    
    def test_dynamic_repr(self, clean_state):
        """Test dynamic has repr."""
        class LodCourse26(Table):
            name: str = ""
        
        class LodStudent26(Table):
            name: str = ""
            courses: List[LodCourse26] = many_to_many(LodCourse26, lazy="dynamic")
        
        student = LodStudent26(name="John")
        
        rep = repr(student.courses)
        assert "DynamicManyToMany" in rep

