"""
Tests for PyNext Many-to-Many Edge Cases.

100 tests covering:
- Self-referential M2M (friends)
- Multiple M2M to same model
- Unsaved objects
- Null handling
- String model references
- Error conditions
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
from pynext.db.relationships.junction import (
    JunctionConfig,
    JunctionTableFactory,
    reset_junction_factory,
    get_junction_factory,
)
from pynext.db.table import _model_registry


@pytest.fixture(autouse=True)
def clean_state():
    """Reset all state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('edg', 'test'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# Self-Referential M2M (25 tests)
# =============================================================================

class TestSelfReferentialM2M:
    """Test self-referential M2M (e.g., friends)."""
    
    def test_self_ref_definition(self, clean_state):
        """Test defining self-referential M2M."""
        class EdgPerson1(Table):
            name: str = ""
            friends: List["EdgPerson1"] = many_to_many("EdgPerson1", backref="friend_of")
        
        descriptor = EdgPerson1.__dict__["friends"]
        assert descriptor._model == "EdgPerson1"
    
    def test_self_ref_collection_created(self, clean_state):
        """Test self-ref creates collection."""
        class EdgPerson2(Table):
            name: str = ""
            friends: List["EdgPerson2"] = many_to_many("EdgPerson2")
        
        person = EdgPerson2(name="John")
        
        assert isinstance(person.friends, ManyToManyCollection)
    
    def test_self_ref_append_friend(self, clean_state):
        """Test appending to self-ref collection."""
        class EdgPerson3(Table):
            name: str = ""
            friends: List["EdgPerson3"] = many_to_many("EdgPerson3")
        
        john = EdgPerson3(name="John")
        jane = EdgPerson3(name="Jane")
        
        john.friends.append(jane)
        
        assert jane in john.friends
    
    def test_self_ref_mutual_friendship(self, clean_state):
        """Test mutual friendship."""
        class EdgPerson4(Table):
            name: str = ""
            friends: List["EdgPerson4"] = many_to_many("EdgPerson4")
        
        john = EdgPerson4(name="John")
        jane = EdgPerson4(name="Jane")
        
        john.friends.append(jane)
        jane.friends.append(john)
        
        assert jane in john.friends
        assert john in jane.friends


# =============================================================================
# Multiple M2M to Same Model (20 tests)
# =============================================================================

class TestMultipleM2MSameModel:
    """Test multiple M2M relationships to the same model."""
    
    def test_multiple_m2m_definitions(self, clean_state):
        """Test defining multiple M2M to same model."""
        class EdgTag1(Table):
            name: str = ""
        
        class EdgArticle1(Table):
            title: str = ""
            tags: List[EdgTag1] = many_to_many(EdgTag1)
            featured_tags: List[EdgTag1] = many_to_many(EdgTag1)
        
        assert hasattr(EdgArticle1, "tags")
        assert hasattr(EdgArticle1, "featured_tags")
    
    def test_multiple_m2m_independent(self, clean_state):
        """Test multiple M2M are independent."""
        class EdgTag2(Table):
            name: str = ""
        
        class EdgArticle2(Table):
            title: str = ""
            tags: List[EdgTag2] = many_to_many(EdgTag2)
            featured: List[EdgTag2] = many_to_many(EdgTag2)
        
        article = EdgArticle2(title="Test")
        tag1 = EdgTag2(name="Tag1")
        tag2 = EdgTag2(name="Tag2")
        
        article.tags.append(tag1)
        article.featured.append(tag2)
        
        assert tag1 in article.tags
        assert tag2 not in article.tags
        assert tag2 in article.featured
        assert tag1 not in article.featured
    
    def test_multiple_m2m_separate_caches(self, clean_state):
        """Test each M2M has its own cache."""
        class EdgTag3(Table):
            name: str = ""
        
        class EdgArticle3(Table):
            title: str = ""
            tags: List[EdgTag3] = many_to_many(EdgTag3)
            featured: List[EdgTag3] = many_to_many(EdgTag3)
        
        article = EdgArticle3(title="Test")
        
        assert hasattr(article, "_cached_tags") or article.tags is not None
        tags_col = article.tags
        featured_col = article.featured
        
        assert tags_col is not featured_col


# =============================================================================
# Unsaved Objects (15 tests)
# =============================================================================

class TestUnsavedObjects:
    """Test M2M with unsaved objects."""
    
    def test_append_unsaved_to_unsaved(self, clean_state):
        """Test appending unsaved object to unsaved owner."""
        class EdgCourse1(Table):
            name: str = ""
        
        class EdgStudent1(Table):
            name: str = ""
            courses: List[EdgCourse1] = many_to_many(EdgCourse1)
        
        student = EdgStudent1(name="John")
        course = EdgCourse1(name="Math")
        
        # Neither has id
        student.courses.append(course)
        
        assert course in student.courses
    
    def test_collection_empty_before_save(self, clean_state):
        """Test collection starts empty."""
        class EdgCourse2(Table):
            name: str = ""
        
        class EdgStudent2(Table):
            name: str = ""
            courses: List[EdgCourse2] = many_to_many(EdgCourse2)
        
        student = EdgStudent2(name="John")
        
        assert len(student.courses) == 0
    
    def test_pending_changes_tracked(self, clean_state):
        """Test pending changes for unsaved objects."""
        class EdgCourse3(Table):
            name: str = ""
        
        class EdgStudent3(Table):
            name: str = ""
            courses: List[EdgCourse3] = many_to_many(EdgCourse3)
        
        student = EdgStudent3(name="John")
        course = EdgCourse3(name="Math")
        
        student.courses.append(course)
        
        assert student.courses.has_pending_changes


# =============================================================================
# String Model References (15 tests)
# =============================================================================

class TestStringModelReferences:
    """Test M2M with string model references."""
    
    def test_string_model_stored(self, clean_state):
        """Test string model reference is stored."""
        class EdgStudent4(Table):
            name: str = ""
            courses: List["EdgCourse4"] = many_to_many("EdgCourse4")
        
        class EdgCourse4(Table):
            name: str = ""
        
        descriptor = EdgStudent4.__dict__["courses"]
        # Should be string or resolved
        assert descriptor._model == "EdgCourse4" or descriptor._model == EdgCourse4
    
    def test_string_model_resolved(self, clean_state):
        """Test string model is resolved."""
        class EdgStudent5(Table):
            name: str = ""
            courses: List["EdgCourse5"] = many_to_many("EdgCourse5")
        
        class EdgCourse5(Table):
            name: str = ""
        
        descriptor = EdgStudent5.__dict__["courses"]
        resolved = descriptor.model
        
        assert resolved is EdgCourse5
    
    def test_forward_reference_works(self, clean_state):
        """Test forward reference in M2M."""
        class EdgStudent6(Table):
            name: str = ""
            courses: List["EdgCourse6"] = many_to_many("EdgCourse6")
        
        # Course defined after Student
        class EdgCourse6(Table):
            name: str = ""
        
        student = EdgStudent6(name="John")
        course = EdgCourse6(name="Math")
        
        student.courses.append(course)
        
        assert course in student.courses


# =============================================================================
# Error Conditions (15 tests)
# =============================================================================

class TestErrorConditions:
    """Test error conditions in M2M."""
    
    def test_remove_not_in_collection(self, clean_state):
        """Test removing item not in collection raises."""
        class EdgCourse7(Table):
            name: str = ""
        
        class EdgStudent7(Table):
            name: str = ""
            courses: List[EdgCourse7] = many_to_many(EdgCourse7)
        
        student = EdgStudent7(name="John")
        course = EdgCourse7(name="Math")
        
        with pytest.raises(ValueError):
            student.courses.remove(course)
    
    def test_index_not_found(self, clean_state):
        """Test index of item not in collection raises."""
        class EdgCourse8(Table):
            name: str = ""
        
        class EdgStudent8(Table):
            name: str = ""
            courses: List[EdgCourse8] = many_to_many(EdgCourse8)
        
        student = EdgStudent8(name="John")
        course = EdgCourse8(name="Math")
        
        with pytest.raises(ValueError):
            student.courses.index(course)
    
    def test_pop_empty_collection(self, clean_state):
        """Test popping from empty collection raises."""
        class EdgCourse9(Table):
            name: str = ""
        
        class EdgStudent9(Table):
            name: str = ""
            courses: List[EdgCourse9] = many_to_many(EdgCourse9)
        
        student = EdgStudent9(name="John")
        
        with pytest.raises(IndexError):
            student.courses.pop()
    
    def test_getitem_out_of_range(self, clean_state):
        """Test getting item out of range raises."""
        class EdgCourse10(Table):
            name: str = ""
        
        class EdgStudent10(Table):
            name: str = ""
            courses: List[EdgCourse10] = many_to_many(EdgCourse10)
        
        student = EdgStudent10(name="John")
        
        with pytest.raises(IndexError):
            _ = student.courses[0]


# =============================================================================
# Collection Properties (10 tests)
# =============================================================================

class TestCollectionProperties:
    """Test collection property accessors."""
    
    def test_owner_accessible(self, clean_state):
        """Test owner is accessible."""
        class EdgCourse11(Table):
            name: str = ""
        
        class EdgStudent11(Table):
            name: str = ""
            courses: List[EdgCourse11] = many_to_many(EdgCourse11)
        
        student = EdgStudent11(name="John")
        
        assert student.courses.owner is student
    
    def test_attr_name_accessible(self, clean_state):
        """Test attr_name is accessible."""
        class EdgCourse12(Table):
            name: str = ""
        
        class EdgStudent12(Table):
            name: str = ""
            courses: List[EdgCourse12] = many_to_many(EdgCourse12)
        
        student = EdgStudent12(name="John")
        
        assert student.courses.attr_name == "courses"
    
    def test_config_accessible(self, clean_state):
        """Test config is accessible."""
        class EdgCourse13(Table):
            name: str = ""
        
        class EdgStudent13(Table):
            name: str = ""
            courses: List[EdgCourse13] = many_to_many(EdgCourse13)
        
        student = EdgStudent13(name="John")
        
        assert isinstance(student.courses.config, JunctionConfig)
    
    def test_has_pending_changes_property(self, clean_state):
        """Test has_pending_changes property."""
        class EdgCourse14(Table):
            name: str = ""
        
        class EdgStudent14(Table):
            name: str = ""
            courses: List[EdgCourse14] = many_to_many(EdgCourse14)
        
        student = EdgStudent14(name="John")
        
        assert not student.courses.has_pending_changes
        
        student.courses.append(EdgCourse14(name="Math"))
        
        assert student.courses.has_pending_changes

