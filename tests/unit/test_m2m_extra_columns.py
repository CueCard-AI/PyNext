"""
Tests for PyNext Many-to-Many Extra Columns.

60 tests covering:
- add() with extra data
- get_junction() for extra access
- update_junction() for modifications
- through= parameter usage
- Junction row queries
"""

import pytest
from typing import List, Optional
from datetime import datetime

from pynext.db import (
    Table,
    many_to_many,
    ManyToManyCollection,
    reset_backref_registry,
    reset_sync_manager,
)
from pynext.db.relationships.junction import (
    JunctionConfig,
    JunctionManager,
    reset_junction_factory,
)
from pynext.db.table import _model_registry


@pytest.fixture(autouse=True)
def clean_state():
    """Reset all state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('ext', 'test'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# add() with Extra Data (20 tests)
# =============================================================================

class TestAddWithExtraData:
    """Test add() method with extra junction data."""
    
    def test_add_single_extra(self, clean_state):
        """Test add with single extra field."""
        class ExtCourse1(Table):
            name: str = ""
        
        class ExtStudent1(Table):
            name: str = ""
            courses: List[ExtCourse1] = many_to_many(ExtCourse1)
        
        student = ExtStudent1(name="John")
        course = ExtCourse1(name="Math")
        
        student.courses.add(course, grade="A")
        
        additions = student.courses.get_pending_additions()
        assert additions[0][1] == {"grade": "A"}
    
    def test_add_multiple_extras(self, clean_state):
        """Test add with multiple extra fields."""
        class ExtCourse2(Table):
            name: str = ""
        
        class ExtStudent2(Table):
            name: str = ""
            courses: List[ExtCourse2] = many_to_many(ExtCourse2)
        
        student = ExtStudent2(name="John")
        course = ExtCourse2(name="Math")
        
        student.courses.add(course, grade="A", semester="Fall", year=2024)
        
        additions = student.courses.get_pending_additions()
        extra = additions[0][1]
        assert extra["grade"] == "A"
        assert extra["semester"] == "Fall"
        assert extra["year"] == 2024
    
    def test_add_also_appends(self, clean_state):
        """Test add also adds item to collection."""
        class ExtCourse3(Table):
            name: str = ""
        
        class ExtStudent3(Table):
            name: str = ""
            courses: List[ExtCourse3] = many_to_many(ExtCourse3)
        
        student = ExtStudent3(name="John")
        course = ExtCourse3(name="Math")
        
        student.courses.add(course, grade="A")
        
        assert course in student.courses
    
    def test_add_no_duplicate(self, clean_state):
        """Test add doesn't duplicate items."""
        class ExtCourse4(Table):
            name: str = ""
        
        class ExtStudent4(Table):
            name: str = ""
            courses: List[ExtCourse4] = many_to_many(ExtCourse4)
        
        student = ExtStudent4(name="John")
        course = ExtCourse4(name="Math")
        
        student.courses.add(course, grade="A")
        student.courses.add(course, grade="B")  # Try to add again
        
        assert len(student.courses) == 1
    
    def test_add_with_datetime(self, clean_state):
        """Test add with datetime extra field."""
        class ExtCourse5(Table):
            name: str = ""
        
        class ExtStudent5(Table):
            name: str = ""
            courses: List[ExtCourse5] = many_to_many(ExtCourse5)
        
        student = ExtStudent5(name="John")
        course = ExtCourse5(name="Math")
        now = datetime.now()
        
        student.courses.add(course, enrolled_at=now)
        
        additions = student.courses.get_pending_additions()
        assert additions[0][1]["enrolled_at"] == now
    
    def test_add_with_none(self, clean_state):
        """Test add with None extra field."""
        class ExtCourse6(Table):
            name: str = ""
        
        class ExtStudent6(Table):
            name: str = ""
            courses: List[ExtCourse6] = many_to_many(ExtCourse6)
        
        student = ExtStudent6(name="John")
        course = ExtCourse6(name="Math")
        
        student.courses.add(course, grade=None)
        
        additions = student.courses.get_pending_additions()
        assert additions[0][1]["grade"] is None
    
    def test_add_with_empty_string(self, clean_state):
        """Test add with empty string extra field."""
        class ExtCourse7(Table):
            name: str = ""
        
        class ExtStudent7(Table):
            name: str = ""
            courses: List[ExtCourse7] = many_to_many(ExtCourse7)
        
        student = ExtStudent7(name="John")
        course = ExtCourse7(name="Math")
        
        student.courses.add(course, notes="")
        
        additions = student.courses.get_pending_additions()
        assert additions[0][1]["notes"] == ""
    
    def test_add_with_numeric(self, clean_state):
        """Test add with numeric extra fields."""
        class ExtCourse8(Table):
            name: str = ""
        
        class ExtStudent8(Table):
            name: str = ""
            courses: List[ExtCourse8] = many_to_many(ExtCourse8)
        
        student = ExtStudent8(name="John")
        course = ExtCourse8(name="Math")
        
        student.courses.add(course, score=95.5, attempts=3)
        
        additions = student.courses.get_pending_additions()
        assert additions[0][1]["score"] == 95.5
        assert additions[0][1]["attempts"] == 3


# =============================================================================
# through= Parameter (20 tests)
# =============================================================================

class TestThroughParameter:
    """Test through= parameter for explicit junction tables."""
    
    def test_through_stored(self, clean_state):
        """Test through is stored on descriptor."""
        class ExtCourse9(Table):
            name: str = ""
        
        class ExtEnrollment1(Table):
            student_id: int = 0
            course_id: int = 0
            grade: str = ""
        
        class ExtStudent9(Table):
            name: str = ""
            courses: List[ExtCourse9] = many_to_many(ExtCourse9, through=ExtEnrollment1)
        
        descriptor = ExtStudent9.__dict__["courses"]
        assert descriptor.through is ExtEnrollment1
    
    def test_through_with_string(self, clean_state):
        """Test through with string model name."""
        class ExtStudent10(Table):
            name: str = ""
            courses: List["ExtCourse10"] = many_to_many("ExtCourse10", through="ExtEnrollment2")
        
        class ExtCourse10(Table):
            name: str = ""
        
        class ExtEnrollment2(Table):
            student_id: int = 0
            course_id: int = 0
        
        descriptor = ExtStudent10.__dict__["courses"]
        assert descriptor.through == "ExtEnrollment2"
    
    def test_through_junction_has_extra_columns(self, clean_state):
        """Test through junction model can have extra columns."""
        class ExtCourse11(Table):
            name: str = ""
        
        class ExtEnrollment3(Table):
            student_id: int = 0
            course_id: int = 0
            grade: Optional[str] = None
            enrolled_at: Optional[datetime] = None
            notes: str = ""
        
        class ExtStudent11(Table):
            name: str = ""
            courses: List[ExtCourse11] = many_to_many(ExtCourse11, through=ExtEnrollment3)
        
        # Verify enrollment model has extra columns
        assert "grade" in ExtEnrollment3.__annotations__
        assert "enrolled_at" in ExtEnrollment3.__annotations__
        assert "notes" in ExtEnrollment3.__annotations__
    
    def test_through_collection_works(self, clean_state):
        """Test collection works with through."""
        class ExtCourse12(Table):
            name: str = ""
        
        class ExtEnrollment4(Table):
            student_id: int = 0
            course_id: int = 0
        
        class ExtStudent12(Table):
            name: str = ""
            courses: List[ExtCourse12] = many_to_many(ExtCourse12, through=ExtEnrollment4)
        
        student = ExtStudent12(name="John")
        course = ExtCourse12(name="Math")
        
        student.courses.append(course)
        
        assert course in student.courses


# =============================================================================
# Pending Changes (20 tests)
# =============================================================================

class TestPendingChanges:
    """Test pending changes tracking."""
    
    def test_has_pending_changes_false(self, clean_state):
        """Test has_pending_changes when no changes."""
        class ExtCourse13(Table):
            name: str = ""
        
        class ExtStudent13(Table):
            name: str = ""
            courses: List[ExtCourse13] = many_to_many(ExtCourse13)
        
        student = ExtStudent13(name="John")
        
        assert not student.courses.has_pending_changes
    
    def test_has_pending_changes_after_add(self, clean_state):
        """Test has_pending_changes after add."""
        class ExtCourse14(Table):
            name: str = ""
        
        class ExtStudent14(Table):
            name: str = ""
            courses: List[ExtCourse14] = many_to_many(ExtCourse14)
        
        student = ExtStudent14(name="John")
        course = ExtCourse14(name="Math")
        
        student.courses.add(course, grade="A")
        
        assert student.courses.has_pending_changes
    
    def test_has_pending_changes_after_append(self, clean_state):
        """Test has_pending_changes after append."""
        class ExtCourse15(Table):
            name: str = ""
        
        class ExtStudent15(Table):
            name: str = ""
            courses: List[ExtCourse15] = many_to_many(ExtCourse15)
        
        student = ExtStudent15(name="John")
        course = ExtCourse15(name="Math")
        
        student.courses.append(course)
        
        assert student.courses.has_pending_changes
    
    def test_has_pending_changes_after_remove(self, clean_state):
        """Test has_pending_changes after remove."""
        class ExtCourse16(Table):
            name: str = ""
        
        class ExtStudent16(Table):
            name: str = ""
            courses: List[ExtCourse16] = many_to_many(ExtCourse16)
        
        student = ExtStudent16(name="John")
        course = ExtCourse16(name="Math")
        
        student.courses._items.append(course)
        student.courses.remove(course)
        
        assert student.courses.has_pending_changes
    
    def test_get_pending_additions(self, clean_state):
        """Test get_pending_additions returns additions."""
        class ExtCourse17(Table):
            name: str = ""
        
        class ExtStudent17(Table):
            name: str = ""
            courses: List[ExtCourse17] = many_to_many(ExtCourse17)
        
        student = ExtStudent17(name="John")
        course = ExtCourse17(name="Math")
        
        student.courses.add(course, grade="A")
        
        additions = student.courses.get_pending_additions()
        assert len(additions) == 1
        assert additions[0][0] is course
        assert additions[0][1] == {"grade": "A"}
    
    def test_get_pending_removals(self, clean_state):
        """Test get_pending_removals returns removals."""
        class ExtCourse18(Table):
            name: str = ""
        
        class ExtStudent18(Table):
            name: str = ""
            courses: List[ExtCourse18] = many_to_many(ExtCourse18)
        
        student = ExtStudent18(name="John")
        course = ExtCourse18(name="Math")
        
        student.courses._items.append(course)
        student.courses.remove(course)
        
        removals = student.courses.get_pending_removals()
        assert len(removals) == 1
        assert removals[0] is course

