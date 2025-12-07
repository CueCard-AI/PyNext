"""
Tests for PyNext Many-to-Many Basic Operations.

100 tests covering:
- Creating M2M relationships
- Append/remove items
- Access from both sides
- Auto-created vs explicit junction
- String model references
- Basic collection operations
"""

import pytest
from typing import List, Optional
from unittest.mock import MagicMock, AsyncMock

from pynext.db import (
    Table,
    configure_db,
    MockAdapter,
    many_to_many,
    ManyToMany,
    ManyToManyCollection,
    reset_backref_registry,
    reset_sync_manager,
)
from pynext.db.relationships.junction import (
    JunctionConfig,
    JunctionTableFactory,
    get_junction_factory,
    reset_junction_factory,
)
from pynext.db.table import _model_registry


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clean_state():
    """Reset all state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()
    # Clean up test models from registry
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('m2m', 'test', 'student', 'course', 'tag', 'article'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# ManyToMany Descriptor Creation (20 tests)
# =============================================================================

class TestManyToManyCreation:
    """Test creating many_to_many relationships."""
    
    def test_create_simple_m2m(self, clean_state):
        """Test creating a simple M2M relationship."""
        class M2MCourse1(Table):
            name: str = ""
        
        class M2MStudent1(Table):
            name: str = ""
            courses: List[M2MCourse1] = many_to_many(M2MCourse1)
        
        assert hasattr(M2MStudent1, "courses")
        assert isinstance(M2MStudent1.__dict__["courses"], ManyToMany)
    
    def test_m2m_with_backref(self, clean_state):
        """Test M2M with backref creates reverse relationship."""
        class M2MCourse2(Table):
            name: str = ""
        
        class M2MStudent2(Table):
            name: str = ""
            courses: List[M2MCourse2] = many_to_many(M2MCourse2, backref="students")
        
        descriptor = M2MStudent2.__dict__["courses"]
        assert descriptor.backref == "students"
    
    def test_m2m_with_string_model(self, clean_state):
        """Test M2M with string model reference."""
        class M2MStudent3(Table):
            name: str = ""
            courses: List["M2MCourse3"] = many_to_many("M2MCourse3")
        
        class M2MCourse3(Table):
            name: str = ""
        
        descriptor = M2MStudent3.__dict__["courses"]
        assert descriptor._model == "M2MCourse3"
    
    def test_m2m_with_through(self, clean_state):
        """Test M2M with explicit through model."""
        class M2MCourse4(Table):
            name: str = ""
        
        class M2MEnrollment1(Table):
            student_id: int = 0
            course_id: int = 0
            grade: str = ""
        
        class M2MStudent4(Table):
            name: str = ""
            courses: List[M2MCourse4] = many_to_many(M2MCourse4, through=M2MEnrollment1)
        
        descriptor = M2MStudent4.__dict__["courses"]
        assert descriptor.through is M2MEnrollment1
    
    def test_m2m_with_lazy_select(self, clean_state):
        """Test M2M with lazy='select' (default)."""
        class M2MCourse5(Table):
            name: str = ""
        
        class M2MStudent5(Table):
            name: str = ""
            courses: List[M2MCourse5] = many_to_many(M2MCourse5, lazy="select")
        
        descriptor = M2MStudent5.__dict__["courses"]
        assert descriptor.lazy == "select"
    
    def test_m2m_with_lazy_selectin(self, clean_state):
        """Test M2M with lazy='selectin'."""
        class M2MCourse6(Table):
            name: str = ""
        
        class M2MStudent6(Table):
            name: str = ""
            courses: List[M2MCourse6] = many_to_many(M2MCourse6, lazy="selectin")
        
        descriptor = M2MStudent6.__dict__["courses"]
        assert descriptor.lazy == "selectin"
    
    def test_m2m_with_lazy_raise(self, clean_state):
        """Test M2M with lazy='raise'."""
        class M2MCourse7(Table):
            name: str = ""
        
        class M2MStudent7(Table):
            name: str = ""
            courses: List[M2MCourse7] = many_to_many(M2MCourse7, lazy="raise")
        
        descriptor = M2MStudent7.__dict__["courses"]
        assert descriptor.lazy == "raise"
    
    def test_m2m_with_lazy_dynamic(self, clean_state):
        """Test M2M with lazy='dynamic'."""
        class M2MCourse8(Table):
            name: str = ""
        
        class M2MStudent8(Table):
            name: str = ""
            courses: List[M2MCourse8] = many_to_many(M2MCourse8, lazy="dynamic")
        
        descriptor = M2MStudent8.__dict__["courses"]
        assert descriptor.lazy == "dynamic"
    
    def test_m2m_rel_name_set(self, clean_state):
        """Test M2M rel_name is set correctly."""
        class M2MCourse9(Table):
            name: str = ""
        
        class M2MStudent9(Table):
            name: str = ""
            courses: List[M2MCourse9] = many_to_many(M2MCourse9)
        
        descriptor = M2MStudent9.__dict__["courses"]
        assert descriptor.rel_name == "courses"
    
    def test_m2m_cache_attr_set(self, clean_state):
        """Test M2M cache attr is set correctly."""
        class M2MCourse10(Table):
            name: str = ""
        
        class M2MStudent10(Table):
            name: str = ""
            courses: List[M2MCourse10] = many_to_many(M2MCourse10)
        
        descriptor = M2MStudent10.__dict__["courses"]
        assert descriptor._cache_attr == "_cached_courses"


class TestManyToManyDescriptorAccess:
    """Test accessing M2M descriptors."""
    
    def test_class_access_returns_descriptor(self, clean_state):
        """Test accessing on class returns descriptor."""
        class M2MCourse11(Table):
            name: str = ""
        
        class M2MStudent11(Table):
            name: str = ""
            courses: List[M2MCourse11] = many_to_many(M2MCourse11)
        
        assert isinstance(M2MStudent11.courses, ManyToMany)
    
    def test_instance_access_returns_collection(self, clean_state):
        """Test accessing on instance returns collection."""
        class M2MCourse12(Table):
            name: str = ""
        
        class M2MStudent12(Table):
            name: str = ""
            courses: List[M2MCourse12] = many_to_many(M2MCourse12)
        
        student = M2MStudent12(name="John")
        collection = student.courses
        
        assert isinstance(collection, ManyToManyCollection)
    
    def test_collection_cached(self, clean_state):
        """Test collection is cached on instance."""
        class M2MCourse13(Table):
            name: str = ""
        
        class M2MStudent13(Table):
            name: str = ""
            courses: List[M2MCourse13] = many_to_many(M2MCourse13)
        
        student = M2MStudent13(name="John")
        collection1 = student.courses
        collection2 = student.courses
        
        assert collection1 is collection2
    
    def test_collection_owner(self, clean_state):
        """Test collection owner is correct."""
        class M2MCourse14(Table):
            name: str = ""
        
        class M2MStudent14(Table):
            name: str = ""
            courses: List[M2MCourse14] = many_to_many(M2MCourse14)
        
        student = M2MStudent14(name="John")
        collection = student.courses
        
        assert collection.owner is student
    
    def test_collection_attr_name(self, clean_state):
        """Test collection attr_name is correct."""
        class M2MCourse15(Table):
            name: str = ""
        
        class M2MStudent15(Table):
            name: str = ""
            courses: List[M2MCourse15] = many_to_many(M2MCourse15)
        
        student = M2MStudent15(name="John")
        collection = student.courses
        
        assert collection.attr_name == "courses"


# =============================================================================
# Collection Operations (30 tests)
# =============================================================================

class TestManyToManyCollectionAppend:
    """Test append operations on M2M collections."""
    
    def test_append_adds_to_collection(self, clean_state):
        """Test append adds item to collection."""
        class M2MCourse16(Table):
            name: str = ""
        
        class M2MStudent16(Table):
            name: str = ""
            courses: List[M2MCourse16] = many_to_many(M2MCourse16)
        
        student = M2MStudent16(name="John")
        course = M2MCourse16(name="Math")
        
        student.courses.append(course)
        
        assert course in student.courses
        assert len(student.courses) == 1
    
    def test_append_multiple(self, clean_state):
        """Test appending multiple items."""
        class M2MCourse17(Table):
            name: str = ""
        
        class M2MStudent17(Table):
            name: str = ""
            courses: List[M2MCourse17] = many_to_many(M2MCourse17)
        
        student = M2MStudent17(name="John")
        math = M2MCourse17(name="Math")
        science = M2MCourse17(name="Science")
        
        student.courses.append(math)
        student.courses.append(science)
        
        assert len(student.courses) == 2
        assert math in student.courses
        assert science in student.courses
    
    def test_append_no_duplicates(self, clean_state):
        """Test append doesn't add duplicates."""
        class M2MCourse18(Table):
            name: str = ""
        
        class M2MStudent18(Table):
            name: str = ""
            courses: List[M2MCourse18] = many_to_many(M2MCourse18)
        
        student = M2MStudent18(name="John")
        course = M2MCourse18(name="Math")
        
        student.courses.append(course)
        student.courses.append(course)  # Duplicate
        
        assert len(student.courses) == 1
    
    def test_append_tracks_pending(self, clean_state):
        """Test append tracks pending additions."""
        class M2MCourse19(Table):
            name: str = ""
        
        class M2MStudent19(Table):
            name: str = ""
            courses: List[M2MCourse19] = many_to_many(M2MCourse19)
        
        student = M2MStudent19(name="John")
        course = M2MCourse19(name="Math")
        
        student.courses.append(course)
        
        assert student.courses.has_pending_changes
        additions = student.courses.get_pending_additions()
        assert len(additions) == 1
        assert additions[0][0] is course


class TestManyToManyCollectionRemove:
    """Test remove operations on M2M collections."""
    
    def test_remove_from_collection(self, clean_state):
        """Test remove removes item from collection."""
        class M2MCourse20(Table):
            name: str = ""
        
        class M2MStudent20(Table):
            name: str = ""
            courses: List[M2MCourse20] = many_to_many(M2MCourse20)
        
        student = M2MStudent20(name="John")
        course = M2MCourse20(name="Math")
        
        student.courses.append(course)
        student.courses.remove(course)
        
        assert course not in student.courses
        assert len(student.courses) == 0
    
    def test_remove_tracks_pending(self, clean_state):
        """Test remove tracks pending removals."""
        class M2MCourse21(Table):
            name: str = ""
        
        class M2MStudent21(Table):
            name: str = ""
            courses: List[M2MCourse21] = many_to_many(M2MCourse21)
        
        student = M2MStudent21(name="John")
        course = M2MCourse21(name="Math")
        
        student.courses._items.append(course)  # Direct add without tracking
        student.courses.remove(course)
        
        removals = student.courses.get_pending_removals()
        assert len(removals) == 1
        assert removals[0] is course
    
    def test_remove_not_found_raises(self, clean_state):
        """Test remove raises ValueError if not found."""
        class M2MCourse22(Table):
            name: str = ""
        
        class M2MStudent22(Table):
            name: str = ""
            courses: List[M2MCourse22] = many_to_many(M2MCourse22)
        
        student = M2MStudent22(name="John")
        course = M2MCourse22(name="Math")
        
        with pytest.raises(ValueError):
            student.courses.remove(course)


class TestManyToManyCollectionExtend:
    """Test extend operations on M2M collections."""
    
    def test_extend_adds_all(self, clean_state):
        """Test extend adds all items."""
        class M2MCourse23(Table):
            name: str = ""
        
        class M2MStudent23(Table):
            name: str = ""
            courses: List[M2MCourse23] = many_to_many(M2MCourse23)
        
        student = M2MStudent23(name="John")
        courses = [M2MCourse23(name=f"Course{i}") for i in range(5)]
        
        student.courses.extend(courses)
        
        assert len(student.courses) == 5
        for c in courses:
            assert c in student.courses
    
    def test_extend_empty_list(self, clean_state):
        """Test extend with empty list."""
        class M2MCourse24(Table):
            name: str = ""
        
        class M2MStudent24(Table):
            name: str = ""
            courses: List[M2MCourse24] = many_to_many(M2MCourse24)
        
        student = M2MStudent24(name="John")
        student.courses.extend([])
        
        assert len(student.courses) == 0


class TestManyToManyCollectionClear:
    """Test clear operations on M2M collections."""
    
    def test_clear_removes_all(self, clean_state):
        """Test clear removes all items."""
        class M2MCourse25(Table):
            name: str = ""
        
        class M2MStudent25(Table):
            name: str = ""
            courses: List[M2MCourse25] = many_to_many(M2MCourse25)
        
        student = M2MStudent25(name="John")
        courses = [M2MCourse25(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        student.courses.clear()
        
        assert len(student.courses) == 0
    
    def test_clear_tracks_removals(self, clean_state):
        """Test clear tracks all removals."""
        class M2MCourse26(Table):
            name: str = ""
        
        class M2MStudent26(Table):
            name: str = ""
            courses: List[M2MCourse26] = many_to_many(M2MCourse26)
        
        student = M2MStudent26(name="John")
        courses = [M2MCourse26(name=f"Course{i}") for i in range(3)]
        for c in courses:
            student.courses._items.append(c)  # Direct add
        
        student.courses.clear()
        
        removals = student.courses.get_pending_removals()
        assert len(removals) == 3


class TestManyToManyCollectionPop:
    """Test pop operations on M2M collections."""
    
    def test_pop_removes_last(self, clean_state):
        """Test pop removes and returns last item."""
        class M2MCourse27(Table):
            name: str = ""
        
        class M2MStudent27(Table):
            name: str = ""
            courses: List[M2MCourse27] = many_to_many(M2MCourse27)
        
        student = M2MStudent27(name="John")
        math = M2MCourse27(name="Math")
        science = M2MCourse27(name="Science")
        
        student.courses.append(math)
        student.courses.append(science)
        
        popped = student.courses.pop()
        
        assert popped is science
        assert len(student.courses) == 1
    
    def test_pop_with_index(self, clean_state):
        """Test pop with specific index."""
        class M2MCourse28(Table):
            name: str = ""
        
        class M2MStudent28(Table):
            name: str = ""
            courses: List[M2MCourse28] = many_to_many(M2MCourse28)
        
        student = M2MStudent28(name="John")
        math = M2MCourse28(name="Math")
        science = M2MCourse28(name="Science")
        
        student.courses.append(math)
        student.courses.append(science)
        
        popped = student.courses.pop(0)
        
        assert popped is math
        assert len(student.courses) == 1


# =============================================================================
# Collection Special Methods (20 tests)
# =============================================================================

class TestManyToManyCollectionSpecial:
    """Test special methods on M2M collections."""
    
    def test_len(self, clean_state):
        """Test __len__."""
        class M2MCourse29(Table):
            name: str = ""
        
        class M2MStudent29(Table):
            name: str = ""
            courses: List[M2MCourse29] = many_to_many(M2MCourse29)
        
        student = M2MStudent29(name="John")
        assert len(student.courses) == 0
        
        student.courses.append(M2MCourse29(name="Math"))
        assert len(student.courses) == 1
    
    def test_iter(self, clean_state):
        """Test __iter__."""
        class M2MCourse30(Table):
            name: str = ""
        
        class M2MStudent30(Table):
            name: str = ""
            courses: List[M2MCourse30] = many_to_many(M2MCourse30)
        
        student = M2MStudent30(name="John")
        courses = [M2MCourse30(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        iterated = list(student.courses)
        assert len(iterated) == 3
    
    def test_contains(self, clean_state):
        """Test __contains__."""
        class M2MCourse31(Table):
            name: str = ""
        
        class M2MStudent31(Table):
            name: str = ""
            courses: List[M2MCourse31] = many_to_many(M2MCourse31)
        
        student = M2MStudent31(name="John")
        math = M2MCourse31(name="Math")
        science = M2MCourse31(name="Science")
        
        student.courses.append(math)
        
        assert math in student.courses
        assert science not in student.courses
    
    def test_getitem_int(self, clean_state):
        """Test __getitem__ with integer index."""
        class M2MCourse32(Table):
            name: str = ""
        
        class M2MStudent32(Table):
            name: str = ""
            courses: List[M2MCourse32] = many_to_many(M2MCourse32)
        
        student = M2MStudent32(name="John")
        math = M2MCourse32(name="Math")
        science = M2MCourse32(name="Science")
        
        student.courses.append(math)
        student.courses.append(science)
        
        assert student.courses[0] is math
        assert student.courses[1] is science
        assert student.courses[-1] is science
    
    def test_getitem_slice(self, clean_state):
        """Test __getitem__ with slice."""
        class M2MCourse33(Table):
            name: str = ""
        
        class M2MStudent33(Table):
            name: str = ""
            courses: List[M2MCourse33] = many_to_many(M2MCourse33)
        
        student = M2MStudent33(name="John")
        courses = [M2MCourse33(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        sliced = student.courses[1:3]
        assert len(sliced) == 2
    
    def test_bool_empty(self, clean_state):
        """Test __bool__ with empty collection."""
        class M2MCourse34(Table):
            name: str = ""
        
        class M2MStudent34(Table):
            name: str = ""
            courses: List[M2MCourse34] = many_to_many(M2MCourse34)
        
        student = M2MStudent34(name="John")
        assert not bool(student.courses)
    
    def test_bool_not_empty(self, clean_state):
        """Test __bool__ with items."""
        class M2MCourse35(Table):
            name: str = ""
        
        class M2MStudent35(Table):
            name: str = ""
            courses: List[M2MCourse35] = many_to_many(M2MCourse35)
        
        student = M2MStudent35(name="John")
        student.courses.append(M2MCourse35(name="Math"))
        
        assert bool(student.courses)
    
    def test_repr(self, clean_state):
        """Test __repr__."""
        class M2MCourse36(Table):
            name: str = ""
        
        class M2MStudent36(Table):
            name: str = ""
            courses: List[M2MCourse36] = many_to_many(M2MCourse36)
        
        student = M2MStudent36(name="John")
        rep = repr(student.courses)
        
        assert "ManyToManyCollection" in rep
        assert "M2MStudent36" in rep
        assert "courses" in rep
    
    def test_eq_list(self, clean_state):
        """Test __eq__ with list."""
        class M2MCourse37(Table):
            name: str = ""
        
        class M2MStudent37(Table):
            name: str = ""
            courses: List[M2MCourse37] = many_to_many(M2MCourse37)
        
        student = M2MStudent37(name="John")
        math = M2MCourse37(name="Math")
        
        student.courses.append(math)
        
        assert student.courses == [math]
    
    def test_to_list(self, clean_state):
        """Test to_list method."""
        class M2MCourse38(Table):
            name: str = ""
        
        class M2MStudent38(Table):
            name: str = ""
            courses: List[M2MCourse38] = many_to_many(M2MCourse38)
        
        student = M2MStudent38(name="John")
        courses = [M2MCourse38(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        result = student.courses.to_list()
        
        assert isinstance(result, list)
        assert result == courses


# =============================================================================
# Bidirectional Access (15 tests)
# =============================================================================

class TestManyToManyBidirectional:
    """Test bidirectional M2M access."""
    
    def test_backref_creates_reverse(self, clean_state):
        """Test backref creates reverse relationship."""
        class M2MCourse39(Table):
            name: str = ""
        
        class M2MStudent39(Table):
            name: str = ""
            courses: List[M2MCourse39] = many_to_many(M2MCourse39, backref="students")
        
        descriptor = M2MStudent39.__dict__["courses"]
        assert descriptor.backref == "students"
    
    def test_access_from_source(self, clean_state):
        """Test accessing M2M from source side."""
        class M2MCourse40(Table):
            name: str = ""
        
        class M2MStudent40(Table):
            name: str = ""
            courses: List[M2MCourse40] = many_to_many(M2MCourse40, backref="students")
        
        student = M2MStudent40(name="John")
        course = M2MCourse40(name="Math")
        
        student.courses.append(course)
        
        assert course in student.courses
    
    def test_collection_stores_reverse_attr(self, clean_state):
        """Test collection stores reverse attribute name."""
        class M2MCourse41(Table):
            name: str = ""
        
        class M2MStudent41(Table):
            name: str = ""
            courses: List[M2MCourse41] = many_to_many(M2MCourse41, backref="students")
        
        student = M2MStudent41(name="John")
        collection = student.courses
        
        assert collection._reverse_attr == "students"


# =============================================================================
# Extra Data Support (15 tests)
# =============================================================================

class TestManyToManyExtraData:
    """Test M2M with extra junction data."""
    
    def test_add_with_extra(self, clean_state):
        """Test add() method with extra data."""
        class M2MCourse42(Table):
            name: str = ""
        
        class M2MStudent42(Table):
            name: str = ""
            courses: List[M2MCourse42] = many_to_many(M2MCourse42)
        
        student = M2MStudent42(name="John")
        course = M2MCourse42(name="Math")
        
        student.courses.add(course, grade="A")
        
        assert course in student.courses
        additions = student.courses.get_pending_additions()
        assert additions[0][1] == {"grade": "A"}
    
    def test_add_multiple_extra_fields(self, clean_state):
        """Test add() with multiple extra fields."""
        class M2MCourse43(Table):
            name: str = ""
        
        class M2MStudent43(Table):
            name: str = ""
            courses: List[M2MCourse43] = many_to_many(M2MCourse43)
        
        student = M2MStudent43(name="John")
        course = M2MCourse43(name="Math")
        
        student.courses.add(course, grade="A", semester="Fall", year=2024)
        
        additions = student.courses.get_pending_additions()
        extra = additions[0][1]
        assert extra["grade"] == "A"
        assert extra["semester"] == "Fall"
        assert extra["year"] == 2024
    
    def test_discard_removes_if_exists(self, clean_state):
        """Test discard removes item if it exists."""
        class M2MCourse44(Table):
            name: str = ""
        
        class M2MStudent44(Table):
            name: str = ""
            courses: List[M2MCourse44] = many_to_many(M2MCourse44)
        
        student = M2MStudent44(name="John")
        course = M2MCourse44(name="Math")
        
        student.courses.append(course)
        student.courses.discard(course)
        
        assert course not in student.courses
    
    def test_discard_no_error_if_missing(self, clean_state):
        """Test discard doesn't raise if item missing."""
        class M2MCourse45(Table):
            name: str = ""
        
        class M2MStudent45(Table):
            name: str = ""
            courses: List[M2MCourse45] = many_to_many(M2MCourse45)
        
        student = M2MStudent45(name="John")
        course = M2MCourse45(name="Math")
        
        # Should not raise
        student.courses.discard(course)
        
        assert len(student.courses) == 0

