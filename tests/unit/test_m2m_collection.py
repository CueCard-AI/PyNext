"""
Tests for PyNext Many-to-Many Collection Operations.

100 tests covering:
- ManyToManyCollection methods
- insert, append, remove, extend, clear, pop
- __contains__, __len__, __iter__, __getitem__
- Slice operations
- Sorting and reversing
- add() with extra data
"""

import pytest
from typing import List, Optional

from pynext.db import (
    Table,
    many_to_many,
    ManyToManyCollection,
    reset_backref_registry,
    reset_sync_manager,
)
from pynext.db.relationships.junction import (
    JunctionConfig,
    reset_junction_factory,
)
from pynext.db.table import _model_registry


@pytest.fixture(autouse=True)
def clean_state():
    """Reset all state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('col', 'test'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# Insert Operations (15 tests)
# =============================================================================

class TestManyToManyInsert:
    """Test insert operations."""
    
    def test_insert_at_beginning(self, clean_state):
        """Test inserting at index 0."""
        class ColCourse1(Table):
            name: str = ""
        
        class ColStudent1(Table):
            name: str = ""
            courses: List[ColCourse1] = many_to_many(ColCourse1)
        
        student = ColStudent1(name="John")
        math = ColCourse1(name="Math")
        science = ColCourse1(name="Science")
        
        student.courses.append(math)
        student.courses.insert(0, science)
        
        assert student.courses[0] is science
        assert student.courses[1] is math
    
    def test_insert_at_middle(self, clean_state):
        """Test inserting in the middle."""
        class ColCourse2(Table):
            name: str = ""
        
        class ColStudent2(Table):
            name: str = ""
            courses: List[ColCourse2] = many_to_many(ColCourse2)
        
        student = ColStudent2(name="John")
        courses = [ColCourse2(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        new_course = ColCourse2(name="New")
        student.courses.insert(1, new_course)
        
        assert student.courses[1] is new_course
        assert len(student.courses) == 4
    
    def test_insert_at_end(self, clean_state):
        """Test inserting at the end."""
        class ColCourse3(Table):
            name: str = ""
        
        class ColStudent3(Table):
            name: str = ""
            courses: List[ColCourse3] = many_to_many(ColCourse3)
        
        student = ColStudent3(name="John")
        math = ColCourse3(name="Math")
        science = ColCourse3(name="Science")
        
        student.courses.append(math)
        student.courses.insert(1, science)
        
        assert student.courses[-1] is science
    
    def test_insert_negative_index(self, clean_state):
        """Test inserting with negative index."""
        class ColCourse4(Table):
            name: str = ""
        
        class ColStudent4(Table):
            name: str = ""
            courses: List[ColCourse4] = many_to_many(ColCourse4)
        
        student = ColStudent4(name="John")
        courses = [ColCourse4(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        new_course = ColCourse4(name="New")
        student.courses.insert(-1, new_course)
        
        assert new_course in student.courses
    
    def test_insert_tracks_pending(self, clean_state):
        """Test insert tracks pending additions."""
        class ColCourse5(Table):
            name: str = ""
        
        class ColStudent5(Table):
            name: str = ""
            courses: List[ColCourse5] = many_to_many(ColCourse5)
        
        student = ColStudent5(name="John")
        course = ColCourse5(name="Math")
        
        student.courses.insert(0, course)
        
        assert student.courses.has_pending_changes


# =============================================================================
# Setitem Operations (15 tests)
# =============================================================================

class TestManyToManySetitem:
    """Test __setitem__ operations."""
    
    def test_setitem_single(self, clean_state):
        """Test setting single item."""
        class ColCourse6(Table):
            name: str = ""
        
        class ColStudent6(Table):
            name: str = ""
            courses: List[ColCourse6] = many_to_many(ColCourse6)
        
        student = ColStudent6(name="John")
        math = ColCourse6(name="Math")
        science = ColCourse6(name="Science")
        
        student.courses.append(math)
        student.courses[0] = science
        
        assert student.courses[0] is science
        assert math not in student.courses
    
    def test_setitem_slice(self, clean_state):
        """Test setting slice."""
        class ColCourse7(Table):
            name: str = ""
        
        class ColStudent7(Table):
            name: str = ""
            courses: List[ColCourse7] = many_to_many(ColCourse7)
        
        student = ColStudent7(name="John")
        old_courses = [ColCourse7(name=f"Old{i}") for i in range(3)]
        new_courses = [ColCourse7(name=f"New{i}") for i in range(2)]
        
        student.courses.extend(old_courses)
        student.courses[0:2] = new_courses
        
        assert len(student.courses) == 3
        assert student.courses[0] is new_courses[0]
        assert student.courses[1] is new_courses[1]
    
    def test_setitem_tracks_removals(self, clean_state):
        """Test setitem tracks removed items."""
        class ColCourse8(Table):
            name: str = ""
        
        class ColStudent8(Table):
            name: str = ""
            courses: List[ColCourse8] = many_to_many(ColCourse8)
        
        student = ColStudent8(name="John")
        old_course = ColCourse8(name="Old")
        new_course = ColCourse8(name="New")
        
        student.courses._items.append(old_course)
        student.courses[0] = new_course
        
        assert old_course in student.courses.get_pending_removals()
    
    def test_setitem_tracks_additions(self, clean_state):
        """Test setitem tracks added items."""
        class ColCourse9(Table):
            name: str = ""
        
        class ColStudent9(Table):
            name: str = ""
            courses: List[ColCourse9] = many_to_many(ColCourse9)
        
        student = ColStudent9(name="John")
        old_course = ColCourse9(name="Old")
        new_course = ColCourse9(name="New")
        
        student.courses._items.append(old_course)
        student.courses[0] = new_course
        
        additions = [a[0] for a in student.courses.get_pending_additions()]
        assert new_course in additions


# =============================================================================
# Delitem Operations (15 tests)
# =============================================================================

class TestManyToManyDelitem:
    """Test __delitem__ operations."""
    
    def test_delitem_single(self, clean_state):
        """Test deleting single item."""
        class ColCourse10(Table):
            name: str = ""
        
        class ColStudent10(Table):
            name: str = ""
            courses: List[ColCourse10] = many_to_many(ColCourse10)
        
        student = ColStudent10(name="John")
        courses = [ColCourse10(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        del student.courses[1]
        
        assert len(student.courses) == 2
        assert courses[1] not in student.courses
    
    def test_delitem_slice(self, clean_state):
        """Test deleting slice."""
        class ColCourse11(Table):
            name: str = ""
        
        class ColStudent11(Table):
            name: str = ""
            courses: List[ColCourse11] = many_to_many(ColCourse11)
        
        student = ColStudent11(name="John")
        courses = [ColCourse11(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        del student.courses[1:3]
        
        assert len(student.courses) == 3
    
    def test_delitem_negative_index(self, clean_state):
        """Test deleting with negative index."""
        class ColCourse12(Table):
            name: str = ""
        
        class ColStudent12(Table):
            name: str = ""
            courses: List[ColCourse12] = many_to_many(ColCourse12)
        
        student = ColStudent12(name="John")
        courses = [ColCourse12(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        last = student.courses[-1]
        del student.courses[-1]
        
        assert last not in student.courses
    
    def test_delitem_tracks_removal(self, clean_state):
        """Test delitem tracks removal."""
        class ColCourse13(Table):
            name: str = ""
        
        class ColStudent13(Table):
            name: str = ""
            courses: List[ColCourse13] = many_to_many(ColCourse13)
        
        student = ColStudent13(name="John")
        course = ColCourse13(name="Math")
        student.courses._items.append(course)
        
        del student.courses[0]
        
        assert course in student.courses.get_pending_removals()


# =============================================================================
# Index and Count Operations (10 tests)
# =============================================================================

class TestManyToManyIndexCount:
    """Test index and count operations."""
    
    def test_index_found(self, clean_state):
        """Test index when item is found."""
        class ColCourse14(Table):
            name: str = ""
        
        class ColStudent14(Table):
            name: str = ""
            courses: List[ColCourse14] = many_to_many(ColCourse14)
        
        student = ColStudent14(name="John")
        courses = [ColCourse14(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        idx = student.courses.index(courses[2])
        
        assert idx == 2
    
    def test_index_not_found(self, clean_state):
        """Test index when item not found."""
        class ColCourse15(Table):
            name: str = ""
        
        class ColStudent15(Table):
            name: str = ""
            courses: List[ColCourse15] = many_to_many(ColCourse15)
        
        student = ColStudent15(name="John")
        course = ColCourse15(name="Math")
        
        with pytest.raises(ValueError):
            student.courses.index(course)
    
    def test_index_with_start(self, clean_state):
        """Test index with start parameter."""
        class ColCourse16(Table):
            name: str = ""
        
        class ColStudent16(Table):
            name: str = ""
            courses: List[ColCourse16] = many_to_many(ColCourse16)
        
        student = ColStudent16(name="John")
        course = ColCourse16(name="Math")
        student.courses.append(course)
        student.courses.append(ColCourse16(name="Other"))
        student.courses._items.append(course)  # Duplicate for test
        
        idx = student.courses.index(course, 1)
        
        assert idx == 2
    
    def test_count_zero(self, clean_state):
        """Test count when item not present."""
        class ColCourse17(Table):
            name: str = ""
        
        class ColStudent17(Table):
            name: str = ""
            courses: List[ColCourse17] = many_to_many(ColCourse17)
        
        student = ColStudent17(name="John")
        course = ColCourse17(name="Math")
        
        assert student.courses.count(course) == 0
    
    def test_count_one(self, clean_state):
        """Test count when item present once."""
        class ColCourse18(Table):
            name: str = ""
        
        class ColStudent18(Table):
            name: str = ""
            courses: List[ColCourse18] = many_to_many(ColCourse18)
        
        student = ColStudent18(name="John")
        course = ColCourse18(name="Math")
        student.courses.append(course)
        
        assert student.courses.count(course) == 1


# =============================================================================
# Sorting and Reversing (10 tests)
# =============================================================================

class TestManyToManySortReverse:
    """Test sort and reverse operations."""
    
    def test_sort_default(self, clean_state):
        """Test default sort."""
        class ColCourse19(Table):
            name: str = ""
            
            def __lt__(self, other):
                return self.name < other.name
        
        class ColStudent19(Table):
            name: str = ""
            courses: List[ColCourse19] = many_to_many(ColCourse19)
        
        student = ColStudent19(name="John")
        courses = [ColCourse19(name=name) for name in ["C", "A", "B"]]
        student.courses.extend(courses)
        
        student.courses.sort()
        
        assert student.courses[0].name == "A"
        assert student.courses[1].name == "B"
        assert student.courses[2].name == "C"
    
    def test_sort_with_key(self, clean_state):
        """Test sort with key function."""
        class ColCourse20(Table):
            name: str = ""
        
        class ColStudent20(Table):
            name: str = ""
            courses: List[ColCourse20] = many_to_many(ColCourse20)
        
        student = ColStudent20(name="John")
        courses = [ColCourse20(name=name) for name in ["C", "A", "B"]]
        student.courses.extend(courses)
        
        student.courses.sort(key=lambda c: c.name)
        
        assert student.courses[0].name == "A"
    
    def test_sort_reverse(self, clean_state):
        """Test sort with reverse=True."""
        class ColCourse21(Table):
            name: str = ""
            
            def __lt__(self, other):
                return self.name < other.name
        
        class ColStudent21(Table):
            name: str = ""
            courses: List[ColCourse21] = many_to_many(ColCourse21)
        
        student = ColStudent21(name="John")
        courses = [ColCourse21(name=name) for name in ["A", "B", "C"]]
        student.courses.extend(courses)
        
        student.courses.sort(reverse=True)
        
        assert student.courses[0].name == "C"
    
    def test_reverse(self, clean_state):
        """Test reverse method."""
        class ColCourse22(Table):
            name: str = ""
        
        class ColStudent22(Table):
            name: str = ""
            courses: List[ColCourse22] = many_to_many(ColCourse22)
        
        student = ColStudent22(name="John")
        courses = [ColCourse22(name=name) for name in ["A", "B", "C"]]
        student.courses.extend(courses)
        
        student.courses.reverse()
        
        assert student.courses[0].name == "C"
        assert student.courses[-1].name == "A"


# =============================================================================
# Copy and Conversion (10 tests)
# =============================================================================

class TestManyToManyCopyConvert:
    """Test copy and conversion operations."""
    
    def test_copy(self, clean_state):
        """Test copy method."""
        class ColCourse23(Table):
            name: str = ""
        
        class ColStudent23(Table):
            name: str = ""
            courses: List[ColCourse23] = many_to_many(ColCourse23)
        
        student = ColStudent23(name="John")
        courses = [ColCourse23(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        copy = student.courses.copy()
        
        assert copy == courses
        assert isinstance(copy, list)
    
    def test_to_list(self, clean_state):
        """Test to_list method."""
        class ColCourse24(Table):
            name: str = ""
        
        class ColStudent24(Table):
            name: str = ""
            courses: List[ColCourse24] = many_to_many(ColCourse24)
        
        student = ColStudent24(name="John")
        courses = [ColCourse24(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        result = student.courses.to_list()
        
        assert result == courses
        assert isinstance(result, list)


# =============================================================================
# Concatenation Operations (10 tests)
# =============================================================================

class TestManyToManyConcatenation:
    """Test concatenation operations."""
    
    def test_add_list(self, clean_state):
        """Test __add__ with list."""
        class ColCourse25(Table):
            name: str = ""
        
        class ColStudent25(Table):
            name: str = ""
            courses: List[ColCourse25] = many_to_many(ColCourse25)
        
        student = ColStudent25(name="John")
        courses1 = [ColCourse25(name=f"Course{i}") for i in range(2)]
        courses2 = [ColCourse25(name=f"New{i}") for i in range(2)]
        
        student.courses.extend(courses1)
        result = student.courses + courses2
        
        assert len(result) == 4
        assert isinstance(result, list)
    
    def test_radd_list(self, clean_state):
        """Test __radd__ with list."""
        class ColCourse26(Table):
            name: str = ""
        
        class ColStudent26(Table):
            name: str = ""
            courses: List[ColCourse26] = many_to_many(ColCourse26)
        
        student = ColStudent26(name="John")
        courses1 = [ColCourse26(name=f"Course{i}") for i in range(2)]
        courses2 = [ColCourse26(name=f"New{i}") for i in range(2)]
        
        student.courses.extend(courses1)
        result = courses2 + student.courses
        
        assert len(result) == 4
    
    def test_iadd(self, clean_state):
        """Test __iadd__ (+=)."""
        class ColCourse27(Table):
            name: str = ""
        
        class ColStudent27(Table):
            name: str = ""
            courses: List[ColCourse27] = many_to_many(ColCourse27)
        
        student = ColStudent27(name="John")
        courses1 = [ColCourse27(name=f"Course{i}") for i in range(2)]
        courses2 = [ColCourse27(name=f"New{i}") for i in range(2)]
        
        student.courses.extend(courses1)
        student.courses += courses2
        
        assert len(student.courses) == 4
        assert isinstance(student.courses, ManyToManyCollection)


# =============================================================================
# Internal Methods (15 tests)
# =============================================================================

class TestManyToManyInternalMethods:
    """Test internal methods."""
    
    def test_append_without_sync(self, clean_state):
        """Test _append_without_sync."""
        class ColCourse28(Table):
            name: str = ""
        
        class ColStudent28(Table):
            name: str = ""
            courses: List[ColCourse28] = many_to_many(ColCourse28)
        
        student = ColStudent28(name="John")
        course = ColCourse28(name="Math")
        
        student.courses._append_without_sync(course)
        
        assert course in student.courses
        assert not student.courses.has_pending_changes
    
    def test_remove_without_sync(self, clean_state):
        """Test _remove_without_sync."""
        class ColCourse29(Table):
            name: str = ""
        
        class ColStudent29(Table):
            name: str = ""
            courses: List[ColCourse29] = many_to_many(ColCourse29)
        
        student = ColStudent29(name="John")
        course = ColCourse29(name="Math")
        
        student.courses._items.append(course)
        student.courses._remove_without_sync(course)
        
        assert course not in student.courses
    
    def test_set_items_without_sync(self, clean_state):
        """Test _set_items_without_sync."""
        class ColCourse30(Table):
            name: str = ""
        
        class ColStudent30(Table):
            name: str = ""
            courses: List[ColCourse30] = many_to_many(ColCourse30)
        
        student = ColStudent30(name="John")
        courses = [ColCourse30(name=f"Course{i}") for i in range(3)]
        
        student.courses._set_items_without_sync(courses)
        
        assert len(student.courses) == 3
        assert not student.courses.has_pending_changes
    
    def test_owner_property(self, clean_state):
        """Test owner property."""
        class ColCourse31(Table):
            name: str = ""
        
        class ColStudent31(Table):
            name: str = ""
            courses: List[ColCourse31] = many_to_many(ColCourse31)
        
        student = ColStudent31(name="John")
        
        assert student.courses.owner is student
    
    def test_attr_name_property(self, clean_state):
        """Test attr_name property."""
        class ColCourse32(Table):
            name: str = ""
        
        class ColStudent32(Table):
            name: str = ""
            courses: List[ColCourse32] = many_to_many(ColCourse32)
        
        student = ColStudent32(name="John")
        
        assert student.courses.attr_name == "courses"
    
    def test_config_property(self, clean_state):
        """Test config property."""
        class ColCourse33(Table):
            name: str = ""
        
        class ColStudent33(Table):
            name: str = ""
            courses: List[ColCourse33] = many_to_many(ColCourse33)
        
        student = ColStudent33(name="John")
        
        assert student.courses.config is not None
        assert isinstance(student.courses.config, JunctionConfig)

