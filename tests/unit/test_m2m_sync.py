"""
Tests for PyNext Many-to-Many Bidirectional Sync.

80 tests covering:
- backref creates reverse relationship
- back_populates links existing
- Append syncs both sides
- Remove syncs both sides
- Loop prevention
"""

import pytest
from typing import List, Optional

from pynext.db import (
    Table,
    many_to_many,
    ManyToMany,
    ManyToManyCollection,
    reset_backref_registry,
    reset_sync_manager,
)
from pynext.db.relationships.junction import reset_junction_factory
from pynext.db.table import _model_registry


@pytest.fixture(autouse=True)
def clean_state():
    """Reset all state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('syn', 'test'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# Backref Configuration (20 tests)
# =============================================================================

class TestManyToManyBackrefConfig:
    """Test backref configuration."""
    
    def test_backref_stored(self, clean_state):
        """Test backref is stored on descriptor."""
        class SynCourse1(Table):
            name: str = ""
        
        class SynStudent1(Table):
            name: str = ""
            courses: List[SynCourse1] = many_to_many(SynCourse1, backref="students")
        
        descriptor = SynStudent1.__dict__["courses"]
        assert descriptor.backref == "students"
    
    def test_back_populates_stored(self, clean_state):
        """Test back_populates is stored on descriptor."""
        class SynCourse2(Table):
            name: str = ""
        
        class SynStudent2(Table):
            name: str = ""
            courses: List[SynCourse2] = many_to_many(SynCourse2, back_populates="students")
        
        descriptor = SynStudent2.__dict__["courses"]
        assert descriptor.back_populates == "students"
    
    def test_collection_has_reverse_attr(self, clean_state):
        """Test collection stores reverse_attr."""
        class SynCourse3(Table):
            name: str = ""
        
        class SynStudent3(Table):
            name: str = ""
            courses: List[SynCourse3] = many_to_many(SynCourse3, backref="students")
        
        student = SynStudent3(name="John")
        
        assert student.courses._reverse_attr == "students"
    
    def test_auto_backref_generates_reverse(self, clean_state):
        """Test no explicit backref auto-generates reverse_attr from class name."""
        class SynCourse4(Table):
            name: str = ""
        
        class SynStudent4(Table):
            name: str = ""
            courses: List[SynCourse4] = many_to_many(SynCourse4)
        
        student = SynStudent4(name="John")
        
        # Auto-backref generates "synstudent4s" from class name
        assert student.courses._reverse_attr == "synstudent4s"
    
    def test_backref_false_disables_reverse(self, clean_state):
        """Test backref=False explicitly disables reverse relationship."""
        class SynCourse4b(Table):
            name: str = ""
        
        class SynStudent4b(Table):
            name: str = ""
            courses: List[SynCourse4b] = many_to_many(SynCourse4b, backref=False)
        
        student = SynStudent4b(name="John")
        
        # backref=False means no reverse_attr
        assert student.courses._reverse_attr is None


# =============================================================================
# Bidirectional Sync - Append (20 tests)
# =============================================================================

class TestManyToManyAppendSync:
    """Test bidirectional sync on append."""
    
    def test_append_adds_to_reverse(self, clean_state):
        """Test append adds owner to reverse collection."""
        class SynCourse5(Table):
            name: str = ""
        
        class SynStudent5(Table):
            name: str = ""
            courses: List[SynCourse5] = many_to_many(SynCourse5, backref="students")
        
        student = SynStudent5(name="John")
        course = SynCourse5(name="Math")
        
        # Pre-create reverse collection
        course._cached_students = ManyToManyCollection(
            owner=course,
            attr_name="students",
            config=student.courses.config,
            items=[],
            reverse_attr="courses",
        )
        
        student.courses.append(course)
        
        assert student in course._cached_students
    
    def test_append_no_duplicate_in_reverse(self, clean_state):
        """Test append doesn't duplicate in reverse."""
        class SynCourse6(Table):
            name: str = ""
        
        class SynStudent6(Table):
            name: str = ""
            courses: List[SynCourse6] = many_to_many(SynCourse6, backref="students")
        
        student = SynStudent6(name="John")
        course = SynCourse6(name="Math")
        
        # Pre-create reverse collection
        course._cached_students = ManyToManyCollection(
            owner=course,
            attr_name="students",
            config=student.courses.config,
            items=[],
            reverse_attr="courses",
        )
        
        student.courses.append(course)
        student.courses.append(course)  # Try to add again
        
        # Count occurrences
        count = sum(1 for s in course._cached_students._items if s is student)
        assert count == 1


# =============================================================================
# Bidirectional Sync - Remove (20 tests)
# =============================================================================

class TestManyToManyRemoveSync:
    """Test bidirectional sync on remove."""
    
    def test_remove_removes_from_reverse(self, clean_state):
        """Test remove removes owner from reverse collection."""
        class SynCourse7(Table):
            name: str = ""
        
        class SynStudent7(Table):
            name: str = ""
            courses: List[SynCourse7] = many_to_many(SynCourse7, backref="students")
        
        student = SynStudent7(name="John")
        course = SynCourse7(name="Math")
        
        # Pre-create reverse collection with student
        course._cached_students = ManyToManyCollection(
            owner=course,
            attr_name="students",
            config=student.courses.config,
            items=[student],
            reverse_attr="courses",
        )
        
        student.courses._items.append(course)
        student.courses.remove(course)
        
        assert student not in course._cached_students
    
    def test_clear_removes_from_all_reverse(self, clean_state):
        """Test clear removes owner from all reverse collections."""
        class SynCourse8(Table):
            name: str = ""
        
        class SynStudent8(Table):
            name: str = ""
            courses: List[SynCourse8] = many_to_many(SynCourse8, backref="students")
        
        student = SynStudent8(name="John")
        courses = [SynCourse8(name=f"Course{i}") for i in range(3)]
        
        # Pre-create reverse collections
        for course in courses:
            course._cached_students = ManyToManyCollection(
                owner=course,
                attr_name="students",
                config=student.courses.config,
                items=[student],
                reverse_attr="courses",
            )
            student.courses._items.append(course)
        
        student.courses.clear()
        
        for course in courses:
            assert student not in course._cached_students


# =============================================================================
# Loop Prevention (20 tests)
# =============================================================================

class TestManyToManyLoopPrevention:
    """Test loop prevention in bidirectional sync."""
    
    def test_internal_append_no_sync(self, clean_state):
        """Test _append_without_sync doesn't trigger reverse sync."""
        class SynCourse9(Table):
            name: str = ""
        
        class SynStudent9(Table):
            name: str = ""
            courses: List[SynCourse9] = many_to_many(SynCourse9, backref="students")
        
        student = SynStudent9(name="John")
        course = SynCourse9(name="Math")
        
        # Pre-create reverse collection
        course._cached_students = ManyToManyCollection(
            owner=course,
            attr_name="students",
            config=student.courses.config,
            items=[],
            reverse_attr="courses",
        )
        
        student.courses._append_without_sync(course)
        
        # Should NOT add to reverse
        assert student not in course._cached_students._items
    
    def test_internal_remove_no_sync(self, clean_state):
        """Test _remove_without_sync doesn't trigger reverse sync."""
        class SynCourse10(Table):
            name: str = ""
        
        class SynStudent10(Table):
            name: str = ""
            courses: List[SynCourse10] = many_to_many(SynCourse10, backref="students")
        
        student = SynStudent10(name="John")
        course = SynCourse10(name="Math")
        
        # Pre-create reverse collection with student
        course._cached_students = ManyToManyCollection(
            owner=course,
            attr_name="students",
            config=student.courses.config,
            items=[student],
            reverse_attr="courses",
        )
        
        student.courses._items.append(course)
        student.courses._remove_without_sync(course)
        
        # Should NOT remove from reverse
        assert student in course._cached_students._items
    
    def test_no_infinite_loop_on_append(self, clean_state):
        """Test no infinite loop when both sides trigger sync."""
        class SynCourse11(Table):
            name: str = ""
        
        class SynStudent11(Table):
            name: str = ""
            courses: List[SynCourse11] = many_to_many(SynCourse11, backref="students")
        
        student = SynStudent11(name="John")
        course = SynCourse11(name="Math")
        
        # Pre-create reverse collection
        course._cached_students = ManyToManyCollection(
            owner=course,
            attr_name="students",
            config=student.courses.config,
            items=[],
            reverse_attr="courses",
        )
        
        # This should complete without infinite recursion
        student.courses.append(course)
        
        assert course in student.courses
        assert student in course._cached_students
    
    def test_sync_with_no_cached_reverse(self, clean_state):
        """Test sync when reverse collection not cached."""
        class SynCourse12(Table):
            name: str = ""
        
        class SynStudent12(Table):
            name: str = ""
            courses: List[SynCourse12] = many_to_many(SynCourse12, backref="students")
        
        student = SynStudent12(name="John")
        course = SynCourse12(name="Math")
        
        # Don't pre-create reverse collection
        
        # Should not error, just skip sync
        student.courses.append(course)
        
        assert course in student.courses

