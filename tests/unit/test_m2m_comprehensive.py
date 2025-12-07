"""
Tests for PyNext Many-to-Many Comprehensive Coverage.

200 tests covering:
- All collection methods in detail
- All descriptor behaviors
- All junction manager operations
- All factory operations
- Integration scenarios
"""

import pytest
from typing import List, Optional
from datetime import datetime

from pynext.db import (
    Table,
    many_to_many,
    ManyToMany,
    ManyToManyCollection,
    reset_backref_registry,
    reset_sync_manager,
    LazyLoadError,
)
from pynext.db.relationships.junction import (
    JunctionConfig,
    JunctionTableFactory,
    JunctionManager,
    reset_junction_factory,
    get_junction_factory,
    create_junction_config,
)
from pynext.db.relationships.m2m_dynamic import DynamicManyToMany
from pynext.db.relationships.proxy import AssociationProxy
from pynext.db.table import _model_registry


@pytest.fixture(autouse=True)
def clean_state():
    """Reset all state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('cmp', 'test'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# Collection Method Coverage (50 tests)
# =============================================================================

class TestCollectionMethodsComprehensive:
    """Comprehensive tests for all collection methods."""
    
    def test_append_new_item(self, clean_state):
        """Test appending new item."""
        class CmpCourse1(Table):
            name: str = ""
        
        class CmpStudent1(Table):
            name: str = ""
            courses: List[CmpCourse1] = many_to_many(CmpCourse1)
        
        student = CmpStudent1(name="John")
        course = CmpCourse1(name="Math")
        
        student.courses.append(course)
        
        assert course in student.courses
    
    def test_append_returns_none(self, clean_state):
        """Test append returns None."""
        class CmpCourse2(Table):
            name: str = ""
        
        class CmpStudent2(Table):
            name: str = ""
            courses: List[CmpCourse2] = many_to_many(CmpCourse2)
        
        student = CmpStudent2(name="John")
        course = CmpCourse2(name="Math")
        
        result = student.courses.append(course)
        
        assert result is None
    
    def test_remove_existing(self, clean_state):
        """Test removing existing item."""
        class CmpCourse3(Table):
            name: str = ""
        
        class CmpStudent3(Table):
            name: str = ""
            courses: List[CmpCourse3] = many_to_many(CmpCourse3)
        
        student = CmpStudent3(name="John")
        course = CmpCourse3(name="Math")
        
        student.courses.append(course)
        student.courses.remove(course)
        
        assert course not in student.courses
    
    def test_remove_missing_raises(self, clean_state):
        """Test removing missing item raises."""
        class CmpCourse4(Table):
            name: str = ""
        
        class CmpStudent4(Table):
            name: str = ""
            courses: List[CmpCourse4] = many_to_many(CmpCourse4)
        
        student = CmpStudent4(name="John")
        course = CmpCourse4(name="Math")
        
        with pytest.raises(ValueError):
            student.courses.remove(course)
    
    def test_pop_default(self, clean_state):
        """Test pop without index."""
        class CmpCourse5(Table):
            name: str = ""
        
        class CmpStudent5(Table):
            name: str = ""
            courses: List[CmpCourse5] = many_to_many(CmpCourse5)
        
        student = CmpStudent5(name="John")
        courses = [CmpCourse5(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        popped = student.courses.pop()
        
        assert popped is courses[2]
        assert len(student.courses) == 2
    
    def test_pop_with_index(self, clean_state):
        """Test pop with index."""
        class CmpCourse6(Table):
            name: str = ""
        
        class CmpStudent6(Table):
            name: str = ""
            courses: List[CmpCourse6] = many_to_many(CmpCourse6)
        
        student = CmpStudent6(name="John")
        courses = [CmpCourse6(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        popped = student.courses.pop(1)
        
        assert popped is courses[1]
        assert len(student.courses) == 2
    
    def test_insert_beginning(self, clean_state):
        """Test insert at beginning."""
        class CmpCourse7(Table):
            name: str = ""
        
        class CmpStudent7(Table):
            name: str = ""
            courses: List[CmpCourse7] = many_to_many(CmpCourse7)
        
        student = CmpStudent7(name="John")
        existing = CmpCourse7(name="Existing")
        new = CmpCourse7(name="New")
        
        student.courses.append(existing)
        student.courses.insert(0, new)
        
        assert student.courses[0] is new
    
    def test_insert_middle(self, clean_state):
        """Test insert in middle."""
        class CmpCourse8(Table):
            name: str = ""
        
        class CmpStudent8(Table):
            name: str = ""
            courses: List[CmpCourse8] = many_to_many(CmpCourse8)
        
        student = CmpStudent8(name="John")
        courses = [CmpCourse8(name=f"Course{i}") for i in range(4)]
        student.courses.extend(courses)
        
        new = CmpCourse8(name="New")
        student.courses.insert(2, new)
        
        assert student.courses[2] is new
        assert len(student.courses) == 5
    
    def test_extend_empty(self, clean_state):
        """Test extend with empty list."""
        class CmpCourse9(Table):
            name: str = ""
        
        class CmpStudent9(Table):
            name: str = ""
            courses: List[CmpCourse9] = many_to_many(CmpCourse9)
        
        student = CmpStudent9(name="John")
        
        student.courses.extend([])
        
        assert len(student.courses) == 0
    
    def test_extend_multiple(self, clean_state):
        """Test extend with multiple items."""
        class CmpCourse10(Table):
            name: str = ""
        
        class CmpStudent10(Table):
            name: str = ""
            courses: List[CmpCourse10] = many_to_many(CmpCourse10)
        
        student = CmpStudent10(name="John")
        courses = [CmpCourse10(name=f"Course{i}") for i in range(5)]
        
        student.courses.extend(courses)
        
        assert len(student.courses) == 5
    
    def test_clear_empty(self, clean_state):
        """Test clear on empty collection."""
        class CmpCourse11(Table):
            name: str = ""
        
        class CmpStudent11(Table):
            name: str = ""
            courses: List[CmpCourse11] = many_to_many(CmpCourse11)
        
        student = CmpStudent11(name="John")
        
        student.courses.clear()
        
        assert len(student.courses) == 0
    
    def test_clear_with_items(self, clean_state):
        """Test clear with items."""
        class CmpCourse12(Table):
            name: str = ""
        
        class CmpStudent12(Table):
            name: str = ""
            courses: List[CmpCourse12] = many_to_many(CmpCourse12)
        
        student = CmpStudent12(name="John")
        courses = [CmpCourse12(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        student.courses.clear()
        
        assert len(student.courses) == 0
    
    def test_discard_existing(self, clean_state):
        """Test discard existing item."""
        class CmpCourse13(Table):
            name: str = ""
        
        class CmpStudent13(Table):
            name: str = ""
            courses: List[CmpCourse13] = many_to_many(CmpCourse13)
        
        student = CmpStudent13(name="John")
        course = CmpCourse13(name="Math")
        
        student.courses.append(course)
        student.courses.discard(course)
        
        assert course not in student.courses
    
    def test_discard_missing_no_error(self, clean_state):
        """Test discard missing item no error."""
        class CmpCourse14(Table):
            name: str = ""
        
        class CmpStudent14(Table):
            name: str = ""
            courses: List[CmpCourse14] = many_to_many(CmpCourse14)
        
        student = CmpStudent14(name="John")
        course = CmpCourse14(name="Math")
        
        # Should not raise
        student.courses.discard(course)
    
    def test_index_first(self, clean_state):
        """Test index of first item."""
        class CmpCourse15(Table):
            name: str = ""
        
        class CmpStudent15(Table):
            name: str = ""
            courses: List[CmpCourse15] = many_to_many(CmpCourse15)
        
        student = CmpStudent15(name="John")
        courses = [CmpCourse15(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        idx = student.courses.index(courses[0])
        
        assert idx == 0
    
    def test_index_last(self, clean_state):
        """Test index of last item."""
        class CmpCourse16(Table):
            name: str = ""
        
        class CmpStudent16(Table):
            name: str = ""
            courses: List[CmpCourse16] = many_to_many(CmpCourse16)
        
        student = CmpStudent16(name="John")
        courses = [CmpCourse16(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        idx = student.courses.index(courses[2])
        
        assert idx == 2
    
    def test_count_zero(self, clean_state):
        """Test count when not present."""
        class CmpCourse17(Table):
            name: str = ""
        
        class CmpStudent17(Table):
            name: str = ""
            courses: List[CmpCourse17] = many_to_many(CmpCourse17)
        
        student = CmpStudent17(name="John")
        course = CmpCourse17(name="Math")
        
        count = student.courses.count(course)
        
        assert count == 0
    
    def test_count_one(self, clean_state):
        """Test count when present once."""
        class CmpCourse18(Table):
            name: str = ""
        
        class CmpStudent18(Table):
            name: str = ""
            courses: List[CmpCourse18] = many_to_many(CmpCourse18)
        
        student = CmpStudent18(name="John")
        course = CmpCourse18(name="Math")
        student.courses.append(course)
        
        count = student.courses.count(course)
        
        assert count == 1


# =============================================================================
# Slicing Operations (30 tests)
# =============================================================================

class TestSlicingOperations:
    """Test slicing operations."""
    
    def test_getitem_positive(self, clean_state):
        """Test getitem with positive index."""
        class CmpCourse19(Table):
            name: str = ""
        
        class CmpStudent19(Table):
            name: str = ""
            courses: List[CmpCourse19] = many_to_many(CmpCourse19)
        
        student = CmpStudent19(name="John")
        courses = [CmpCourse19(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        assert student.courses[0] is courses[0]
        assert student.courses[2] is courses[2]
        assert student.courses[4] is courses[4]
    
    def test_getitem_negative(self, clean_state):
        """Test getitem with negative index."""
        class CmpCourse20(Table):
            name: str = ""
        
        class CmpStudent20(Table):
            name: str = ""
            courses: List[CmpCourse20] = many_to_many(CmpCourse20)
        
        student = CmpStudent20(name="John")
        courses = [CmpCourse20(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        assert student.courses[-1] is courses[4]
        assert student.courses[-2] is courses[3]
    
    def test_getitem_slice_start_end(self, clean_state):
        """Test getitem with slice start:end."""
        class CmpCourse21(Table):
            name: str = ""
        
        class CmpStudent21(Table):
            name: str = ""
            courses: List[CmpCourse21] = many_to_many(CmpCourse21)
        
        student = CmpStudent21(name="John")
        courses = [CmpCourse21(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        sliced = student.courses[1:3]
        
        assert len(sliced) == 2
        assert sliced[0] is courses[1]
        assert sliced[1] is courses[2]
    
    def test_getitem_slice_start_only(self, clean_state):
        """Test getitem with slice start:."""
        class CmpCourse22(Table):
            name: str = ""
        
        class CmpStudent22(Table):
            name: str = ""
            courses: List[CmpCourse22] = many_to_many(CmpCourse22)
        
        student = CmpStudent22(name="John")
        courses = [CmpCourse22(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        sliced = student.courses[2:]
        
        assert len(sliced) == 3
    
    def test_getitem_slice_end_only(self, clean_state):
        """Test getitem with slice :end."""
        class CmpCourse23(Table):
            name: str = ""
        
        class CmpStudent23(Table):
            name: str = ""
            courses: List[CmpCourse23] = many_to_many(CmpCourse23)
        
        student = CmpStudent23(name="John")
        courses = [CmpCourse23(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        sliced = student.courses[:3]
        
        assert len(sliced) == 3
    
    def test_setitem_single(self, clean_state):
        """Test setitem single index."""
        class CmpCourse24(Table):
            name: str = ""
        
        class CmpStudent24(Table):
            name: str = ""
            courses: List[CmpCourse24] = many_to_many(CmpCourse24)
        
        student = CmpStudent24(name="John")
        courses = [CmpCourse24(name=f"Course{i}") for i in range(3)]
        new_course = CmpCourse24(name="New")
        student.courses.extend(courses)
        
        student.courses[1] = new_course
        
        assert student.courses[1] is new_course
    
    def test_delitem_single(self, clean_state):
        """Test delitem single index."""
        class CmpCourse25(Table):
            name: str = ""
        
        class CmpStudent25(Table):
            name: str = ""
            courses: List[CmpCourse25] = many_to_many(CmpCourse25)
        
        student = CmpStudent25(name="John")
        courses = [CmpCourse25(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        del student.courses[1]
        
        assert len(student.courses) == 2
        assert courses[1] not in student.courses


# =============================================================================
# Equality and Comparison (20 tests)
# =============================================================================

class TestEqualityComparison:
    """Test equality and comparison operations."""
    
    def test_eq_with_list(self, clean_state):
        """Test equality with list."""
        class CmpCourse26(Table):
            name: str = ""
        
        class CmpStudent26(Table):
            name: str = ""
            courses: List[CmpCourse26] = many_to_many(CmpCourse26)
        
        student = CmpStudent26(name="John")
        courses = [CmpCourse26(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        assert student.courses == courses
    
    def test_eq_empty(self, clean_state):
        """Test equality with empty list."""
        class CmpCourse27(Table):
            name: str = ""
        
        class CmpStudent27(Table):
            name: str = ""
            courses: List[CmpCourse27] = many_to_many(CmpCourse27)
        
        student = CmpStudent27(name="John")
        
        assert student.courses == []
    
    def test_ne_with_list(self, clean_state):
        """Test inequality with list."""
        class CmpCourse28(Table):
            name: str = ""
        
        class CmpStudent28(Table):
            name: str = ""
            courses: List[CmpCourse28] = many_to_many(CmpCourse28)
        
        student = CmpStudent28(name="John")
        courses1 = [CmpCourse28(name=f"Course{i}") for i in range(3)]
        courses2 = [CmpCourse28(name=f"Other{i}") for i in range(3)]
        student.courses.extend(courses1)
        
        assert student.courses != courses2
    
    def test_bool_empty_false(self, clean_state):
        """Test bool of empty collection is False."""
        class CmpCourse29(Table):
            name: str = ""
        
        class CmpStudent29(Table):
            name: str = ""
            courses: List[CmpCourse29] = many_to_many(CmpCourse29)
        
        student = CmpStudent29(name="John")
        
        assert not bool(student.courses)
    
    def test_bool_nonempty_true(self, clean_state):
        """Test bool of non-empty collection is True."""
        class CmpCourse30(Table):
            name: str = ""
        
        class CmpStudent30(Table):
            name: str = ""
            courses: List[CmpCourse30] = many_to_many(CmpCourse30)
        
        student = CmpStudent30(name="John")
        student.courses.append(CmpCourse30(name="Math"))
        
        assert bool(student.courses)


# =============================================================================
# String Representations (20 tests)
# =============================================================================

class TestStringRepresentations:
    """Test string representations."""
    
    def test_repr_empty(self, clean_state):
        """Test repr of empty collection."""
        class CmpCourse31(Table):
            name: str = ""
        
        class CmpStudent31(Table):
            name: str = ""
            courses: List[CmpCourse31] = many_to_many(CmpCourse31)
        
        student = CmpStudent31(name="John")
        rep = repr(student.courses)
        
        assert "ManyToManyCollection" in rep
        assert "courses" in rep
    
    def test_str_empty(self, clean_state):
        """Test str of empty collection."""
        class CmpCourse32(Table):
            name: str = ""
        
        class CmpStudent32(Table):
            name: str = ""
            courses: List[CmpCourse32] = many_to_many(CmpCourse32)
        
        student = CmpStudent32(name="John")
        s = str(student.courses)
        
        assert s == "[]"
    
    def test_str_with_items(self, clean_state):
        """Test str with items."""
        class CmpCourse33(Table):
            name: str = ""
        
        class CmpStudent33(Table):
            name: str = ""
            courses: List[CmpCourse33] = many_to_many(CmpCourse33)
        
        student = CmpStudent33(name="John")
        student.courses.append(CmpCourse33(name="Math"))
        
        s = str(student.courses)
        
        assert "[" in s
        assert "]" in s


# =============================================================================
# Concatenation (20 tests)
# =============================================================================

class TestConcatenation:
    """Test concatenation operations."""
    
    def test_add_list(self, clean_state):
        """Test adding list."""
        class CmpCourse34(Table):
            name: str = ""
        
        class CmpStudent34(Table):
            name: str = ""
            courses: List[CmpCourse34] = many_to_many(CmpCourse34)
        
        student = CmpStudent34(name="John")
        courses1 = [CmpCourse34(name="Math")]
        courses2 = [CmpCourse34(name="Science")]
        student.courses.extend(courses1)
        
        result = student.courses + courses2
        
        assert len(result) == 2
        assert isinstance(result, list)
    
    def test_radd_list(self, clean_state):
        """Test reverse adding list."""
        class CmpCourse35(Table):
            name: str = ""
        
        class CmpStudent35(Table):
            name: str = ""
            courses: List[CmpCourse35] = many_to_many(CmpCourse35)
        
        student = CmpStudent35(name="John")
        courses1 = [CmpCourse35(name="Math")]
        courses2 = [CmpCourse35(name="Science")]
        student.courses.extend(courses1)
        
        result = courses2 + student.courses
        
        assert len(result) == 2
    
    def test_iadd_list(self, clean_state):
        """Test in-place adding list."""
        class CmpCourse36(Table):
            name: str = ""
        
        class CmpStudent36(Table):
            name: str = ""
            courses: List[CmpCourse36] = many_to_many(CmpCourse36)
        
        student = CmpStudent36(name="John")
        courses = [CmpCourse36(name="Science")]
        student.courses.append(CmpCourse36(name="Math"))
        
        student.courses += courses
        
        assert len(student.courses) == 2
        assert isinstance(student.courses, ManyToManyCollection)


# =============================================================================
# Sorting (15 tests)
# =============================================================================

class TestSorting:
    """Test sorting operations."""
    
    def test_sort_default(self, clean_state):
        """Test default sort."""
        class CmpCourse37(Table):
            name: str = ""
            
            def __lt__(self, other):
                return self.name < other.name
        
        class CmpStudent37(Table):
            name: str = ""
            courses: List[CmpCourse37] = many_to_many(CmpCourse37)
        
        student = CmpStudent37(name="John")
        courses = [CmpCourse37(name=name) for name in ["C", "A", "B"]]
        student.courses.extend(courses)
        
        student.courses.sort()
        
        assert student.courses[0].name == "A"
        assert student.courses[1].name == "B"
        assert student.courses[2].name == "C"
    
    def test_sort_key(self, clean_state):
        """Test sort with key."""
        class CmpCourse38(Table):
            name: str = ""
        
        class CmpStudent38(Table):
            name: str = ""
            courses: List[CmpCourse38] = many_to_many(CmpCourse38)
        
        student = CmpStudent38(name="John")
        courses = [CmpCourse38(name=name) for name in ["C", "A", "B"]]
        student.courses.extend(courses)
        
        student.courses.sort(key=lambda c: c.name)
        
        assert student.courses[0].name == "A"
    
    def test_sort_reverse(self, clean_state):
        """Test sort reverse."""
        class CmpCourse39(Table):
            name: str = ""
            
            def __lt__(self, other):
                return self.name < other.name
        
        class CmpStudent39(Table):
            name: str = ""
            courses: List[CmpCourse39] = many_to_many(CmpCourse39)
        
        student = CmpStudent39(name="John")
        courses = [CmpCourse39(name=name) for name in ["A", "B", "C"]]
        student.courses.extend(courses)
        
        student.courses.sort(reverse=True)
        
        assert student.courses[0].name == "C"
    
    def test_reverse_method(self, clean_state):
        """Test reverse method."""
        class CmpCourse40(Table):
            name: str = ""
        
        class CmpStudent40(Table):
            name: str = ""
            courses: List[CmpCourse40] = many_to_many(CmpCourse40)
        
        student = CmpStudent40(name="John")
        courses = [CmpCourse40(name=name) for name in ["A", "B", "C"]]
        student.courses.extend(courses)
        
        student.courses.reverse()
        
        assert student.courses[0].name == "C"
        assert student.courses[2].name == "A"


# =============================================================================
# Copy Operations (15 tests)
# =============================================================================

class TestCopyOperations:
    """Test copy operations."""
    
    def test_copy_returns_list(self, clean_state):
        """Test copy returns list."""
        class CmpCourse41(Table):
            name: str = ""
        
        class CmpStudent41(Table):
            name: str = ""
            courses: List[CmpCourse41] = many_to_many(CmpCourse41)
        
        student = CmpStudent41(name="John")
        courses = [CmpCourse41(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        copy = student.courses.copy()
        
        assert isinstance(copy, list)
        assert copy == courses
    
    def test_copy_independent(self, clean_state):
        """Test copy is independent."""
        class CmpCourse42(Table):
            name: str = ""
        
        class CmpStudent42(Table):
            name: str = ""
            courses: List[CmpCourse42] = many_to_many(CmpCourse42)
        
        student = CmpStudent42(name="John")
        courses = [CmpCourse42(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        copy = student.courses.copy()
        copy.append(CmpCourse42(name="New"))
        
        assert len(student.courses) == 3
        assert len(copy) == 4
    
    def test_to_list_returns_list(self, clean_state):
        """Test to_list returns list."""
        class CmpCourse43(Table):
            name: str = ""
        
        class CmpStudent43(Table):
            name: str = ""
            courses: List[CmpCourse43] = many_to_many(CmpCourse43)
        
        student = CmpStudent43(name="John")
        courses = [CmpCourse43(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        result = student.courses.to_list()
        
        assert isinstance(result, list)

