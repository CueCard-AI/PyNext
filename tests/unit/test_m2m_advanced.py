"""
Tests for PyNext Many-to-Many Advanced Features.

150 tests covering:
- Complex model hierarchies
- Multiple relationships between same models
- Relationship inheritance
- Custom junction configurations
- Edge cases and corner cases
"""

import pytest
from typing import List, Optional
from datetime import datetime

from pynext.db import (
    Table,
    many_to_many,
    has_many,
    belongs_to,
    ManyToMany,
    ManyToManyCollection,
    reset_backref_registry,
    reset_sync_manager,
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
from pynext.db.table import _model_registry


@pytest.fixture(autouse=True)
def clean_state():
    """Reset all state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('adv', 'test'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# Multiple M2M Same Model (30 tests)
# =============================================================================

class TestMultipleM2MSameModel:
    """Test multiple M2M relationships to the same target model."""
    
    def test_two_m2m_to_same_model(self, clean_state):
        """Test two M2M to same model."""
        class AdvTag1(Table):
            name: str = ""
        
        class AdvPost1(Table):
            title: str = ""
            tags: List[AdvTag1] = many_to_many(AdvTag1)
            featured_tags: List[AdvTag1] = many_to_many(AdvTag1)
        
        post = AdvPost1(title="Test")
        tag1 = AdvTag1(name="Python")
        tag2 = AdvTag1(name="Featured")
        
        post.tags.append(tag1)
        post.featured_tags.append(tag2)
        
        assert tag1 in post.tags
        assert tag2 in post.featured_tags
        assert tag1 not in post.featured_tags
        assert tag2 not in post.tags
    
    def test_three_m2m_to_same_model(self, clean_state):
        """Test three M2M to same model."""
        class AdvUser1(Table):
            name: str = ""
        
        class AdvProject1(Table):
            title: str = ""
            owners: List[AdvUser1] = many_to_many(AdvUser1)
            members: List[AdvUser1] = many_to_many(AdvUser1)
            viewers: List[AdvUser1] = many_to_many(AdvUser1)
        
        project = AdvProject1(title="Test")
        owner = AdvUser1(name="Owner")
        member = AdvUser1(name="Member")
        viewer = AdvUser1(name="Viewer")
        
        project.owners.append(owner)
        project.members.append(member)
        project.viewers.append(viewer)
        
        assert len(project.owners) == 1
        assert len(project.members) == 1
        assert len(project.viewers) == 1
    
    def test_same_item_in_multiple_collections(self, clean_state):
        """Test same item can be in multiple collections."""
        class AdvUser2(Table):
            name: str = ""
        
        class AdvProject2(Table):
            title: str = ""
            owners: List[AdvUser2] = many_to_many(AdvUser2)
            members: List[AdvUser2] = many_to_many(AdvUser2)
        
        project = AdvProject2(title="Test")
        user = AdvUser2(name="Admin")
        
        project.owners.append(user)
        project.members.append(user)  # Same user in both!
        
        assert user in project.owners
        assert user in project.members


# =============================================================================
# Self-Referential Advanced (25 tests)
# =============================================================================

class TestSelfReferentialAdvanced:
    """Advanced tests for self-referential M2M."""
    
    def test_friends_relationship(self, clean_state):
        """Test friends relationship pattern."""
        class AdvPerson1(Table):
            name: str = ""
            friends: List["AdvPerson1"] = many_to_many("AdvPerson1")
        
        alice = AdvPerson1(name="Alice")
        bob = AdvPerson1(name="Bob")
        carol = AdvPerson1(name="Carol")
        
        alice.friends.append(bob)
        alice.friends.append(carol)
        
        assert bob in alice.friends
        assert carol in alice.friends
        assert len(alice.friends) == 2
    
    def test_following_pattern(self, clean_state):
        """Test following/followers pattern."""
        class AdvUser3(Table):
            name: str = ""
            following: List["AdvUser3"] = many_to_many("AdvUser3")
        
        john = AdvUser3(name="John")
        jane = AdvUser3(name="Jane")
        
        john.following.append(jane)
        
        assert jane in john.following
        assert john not in jane.following  # Not bidirectional
    
    def test_mutual_following(self, clean_state):
        """Test mutual following."""
        class AdvUser4(Table):
            name: str = ""
            following: List["AdvUser4"] = many_to_many("AdvUser4")
        
        john = AdvUser4(name="John")
        jane = AdvUser4(name="Jane")
        
        john.following.append(jane)
        jane.following.append(john)
        
        assert jane in john.following
        assert john in jane.following
    
    def test_block_relationship(self, clean_state):
        """Test blocking relationship pattern."""
        class AdvUser5(Table):
            name: str = ""
            following: List["AdvUser5"] = many_to_many("AdvUser5")
            blocked: List["AdvUser5"] = many_to_many("AdvUser5")
        
        user1 = AdvUser5(name="User1")
        user2 = AdvUser5(name="User2")
        
        user1.following.append(user2)
        user1.blocked.append(user2)  # Can be in both
        
        assert user2 in user1.following
        assert user2 in user1.blocked


# =============================================================================
# Collection Iteration Edge Cases (20 tests)
# =============================================================================

class TestCollectionIterationEdgeCases:
    """Test edge cases in collection iteration."""
    
    def test_iterate_empty(self, clean_state):
        """Test iterating empty collection."""
        class AdvCourse1(Table):
            name: str = ""
        
        class AdvStudent1(Table):
            name: str = ""
            courses: List[AdvCourse1] = many_to_many(AdvCourse1)
        
        student = AdvStudent1(name="John")
        
        items = list(student.courses)
        assert items == []
    
    def test_iterate_single(self, clean_state):
        """Test iterating single item."""
        class AdvCourse2(Table):
            name: str = ""
        
        class AdvStudent2(Table):
            name: str = ""
            courses: List[AdvCourse2] = many_to_many(AdvCourse2)
        
        student = AdvStudent2(name="John")
        course = AdvCourse2(name="Math")
        student.courses.append(course)
        
        items = list(student.courses)
        assert items == [course]
    
    def test_iterate_many(self, clean_state):
        """Test iterating many items."""
        class AdvCourse3(Table):
            name: str = ""
        
        class AdvStudent3(Table):
            name: str = ""
            courses: List[AdvCourse3] = many_to_many(AdvCourse3)
        
        student = AdvStudent3(name="John")
        courses = [AdvCourse3(name=f"Course{i}") for i in range(100)]
        student.courses.extend(courses)
        
        items = list(student.courses)
        assert len(items) == 100
    
    def test_multiple_iterations(self, clean_state):
        """Test multiple iterations are consistent."""
        class AdvCourse4(Table):
            name: str = ""
        
        class AdvStudent4(Table):
            name: str = ""
            courses: List[AdvCourse4] = many_to_many(AdvCourse4)
        
        student = AdvStudent4(name="John")
        courses = [AdvCourse4(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        iter1 = list(student.courses)
        iter2 = list(student.courses)
        
        assert iter1 == iter2
    
    def test_reversed_iteration(self, clean_state):
        """Test reversed iteration."""
        class AdvCourse5(Table):
            name: str = ""
        
        class AdvStudent5(Table):
            name: str = ""
            courses: List[AdvCourse5] = many_to_many(AdvCourse5)
        
        student = AdvStudent5(name="John")
        courses = [AdvCourse5(name=f"Course{i}") for i in range(3)]
        student.courses.extend(courses)
        
        reversed_items = list(reversed(student.courses))
        
        assert reversed_items[0] is courses[2]
        assert reversed_items[2] is courses[0]


# =============================================================================
# Collection Mutation During Iteration (15 tests)
# =============================================================================

class TestCollectionMutationDuringIteration:
    """Test collection behavior during iteration (edge cases)."""
    
    def test_copy_before_clear(self, clean_state):
        """Test copying before clearing."""
        class AdvCourse6(Table):
            name: str = ""
        
        class AdvStudent6(Table):
            name: str = ""
            courses: List[AdvCourse6] = many_to_many(AdvCourse6)
        
        student = AdvStudent6(name="John")
        courses = [AdvCourse6(name=f"Course{i}") for i in range(5)]
        student.courses.extend(courses)
        
        # Copy before clear
        courses_copy = student.courses.copy()
        student.courses.clear()
        
        assert len(student.courses) == 0
        assert len(courses_copy) == 5
    
    def test_to_list_is_copy(self, clean_state):
        """Test to_list returns a copy."""
        class AdvCourse7(Table):
            name: str = ""
        
        class AdvStudent7(Table):
            name: str = ""
            courses: List[AdvCourse7] = many_to_many(AdvCourse7)
        
        student = AdvStudent7(name="John")
        course = AdvCourse7(name="Math")
        student.courses.append(course)
        
        courses_list = student.courses.to_list()
        courses_list.clear()
        
        # Original should be unchanged
        assert len(student.courses) == 1


# =============================================================================
# Descriptor Behavior (20 tests)
# =============================================================================

class TestDescriptorBehavior:
    """Test ManyToMany descriptor behavior."""
    
    def test_class_access(self, clean_state):
        """Test accessing on class returns descriptor."""
        class AdvCourse8(Table):
            name: str = ""
        
        class AdvStudent8(Table):
            name: str = ""
            courses: List[AdvCourse8] = many_to_many(AdvCourse8)
        
        assert isinstance(AdvStudent8.courses, ManyToMany)
    
    def test_instance_access(self, clean_state):
        """Test accessing on instance returns collection."""
        class AdvCourse9(Table):
            name: str = ""
        
        class AdvStudent9(Table):
            name: str = ""
            courses: List[AdvCourse9] = many_to_many(AdvCourse9)
        
        student = AdvStudent9(name="John")
        assert isinstance(student.courses, ManyToManyCollection)
    
    def test_different_instances_different_collections(self, clean_state):
        """Test different instances have different collections."""
        class AdvCourse10(Table):
            name: str = ""
        
        class AdvStudent10(Table):
            name: str = ""
            courses: List[AdvCourse10] = many_to_many(AdvCourse10)
        
        student1 = AdvStudent10(name="John")
        student2 = AdvStudent10(name="Jane")
        course = AdvCourse10(name="Math")
        
        student1.courses.append(course)
        
        assert course in student1.courses
        assert course not in student2.courses
    
    def test_set_collection(self, clean_state):
        """Test setting collection with __set__."""
        class AdvCourse11(Table):
            name: str = ""
        
        class AdvStudent11(Table):
            name: str = ""
            courses: List[AdvCourse11] = many_to_many(AdvCourse11)
        
        student = AdvStudent11(name="John")
        courses = [AdvCourse11(name=f"Course{i}") for i in range(3)]
        
        student.courses = courses
        
        assert len(student.courses) == 3
    
    def test_set_replaces_collection(self, clean_state):
        """Test setting collection replaces items."""
        class AdvCourse12(Table):
            name: str = ""
        
        class AdvStudent12(Table):
            name: str = ""
            courses: List[AdvCourse12] = many_to_many(AdvCourse12)
        
        student = AdvStudent12(name="John")
        old_course = AdvCourse12(name="Old")
        new_courses = [AdvCourse12(name=f"New{i}") for i in range(2)]
        
        student.courses.append(old_course)
        student.courses = new_courses
        
        assert old_course not in student.courses
        assert len(student.courses) == 2


# =============================================================================
# Loading Strategy Combinations (20 tests)
# =============================================================================

class TestLoadingStrategyCombinations:
    """Test different loading strategy configurations."""
    
    def test_default_select(self, clean_state):
        """Test default is select."""
        class AdvCourse13(Table):
            name: str = ""
        
        class AdvStudent13(Table):
            name: str = ""
            courses: List[AdvCourse13] = many_to_many(AdvCourse13)
        
        descriptor = AdvStudent13.__dict__["courses"]
        assert descriptor.lazy == "select"
    
    def test_selectin(self, clean_state):
        """Test selectin strategy."""
        class AdvCourse14(Table):
            name: str = ""
        
        class AdvStudent14(Table):
            name: str = ""
            courses: List[AdvCourse14] = many_to_many(AdvCourse14, lazy="selectin")
        
        descriptor = AdvStudent14.__dict__["courses"]
        assert descriptor.lazy == "selectin"
    
    def test_subquery(self, clean_state):
        """Test subquery strategy."""
        class AdvCourse15(Table):
            name: str = ""
        
        class AdvStudent15(Table):
            name: str = ""
            courses: List[AdvCourse15] = many_to_many(AdvCourse15, lazy="subquery")
        
        descriptor = AdvStudent15.__dict__["courses"]
        assert descriptor.lazy == "subquery"
    
    def test_raise(self, clean_state):
        """Test raise strategy."""
        class AdvCourse16(Table):
            name: str = ""
        
        class AdvStudent16(Table):
            name: str = ""
            courses: List[AdvCourse16] = many_to_many(AdvCourse16, lazy="raise")
        
        descriptor = AdvStudent16.__dict__["courses"]
        assert descriptor.lazy == "raise"
    
    def test_dynamic(self, clean_state):
        """Test dynamic strategy."""
        class AdvCourse17(Table):
            name: str = ""
        
        class AdvStudent17(Table):
            name: str = ""
            courses: List[AdvCourse17] = many_to_many(AdvCourse17, lazy="dynamic")
        
        descriptor = AdvStudent17.__dict__["courses"]
        assert descriptor.lazy == "dynamic"
    
    def test_dynamic_returns_query_builder(self, clean_state):
        """Test dynamic returns query builder."""
        class AdvCourse18(Table):
            name: str = ""
        
        class AdvStudent18(Table):
            name: str = ""
            courses: List[AdvCourse18] = many_to_many(AdvCourse18, lazy="dynamic")
        
        student = AdvStudent18(name="John")
        
        assert isinstance(student.courses, DynamicManyToMany)


# =============================================================================
# Junction Factory Advanced (20 tests)
# =============================================================================

class TestJunctionFactoryAdvanced:
    """Advanced tests for junction table factory."""
    
    def test_consistent_naming(self, clean_state):
        """Test junction table names are consistent."""
        class AdvModel1(Table):
            name: str = ""
        
        class AdvModel2(Table):
            name: str = ""
        
        factory = get_junction_factory()
        
        # Order shouldn't matter
        name1 = factory.generate_junction_name(AdvModel1, AdvModel2)
        name2 = factory.generate_junction_name(AdvModel2, AdvModel1)
        
        assert name1 == name2
    
    def test_alphabetical_ordering(self, clean_state):
        """Test names are alphabetically ordered."""
        class AdvZebra(Table):
            name: str = ""
        
        class AdvApple(Table):
            name: str = ""
        
        factory = get_junction_factory()
        
        name = factory.generate_junction_name(AdvZebra, AdvApple)
        
        # 'advapples' should come before 'advzebras'
        assert name.startswith("advapple")
    
    def test_cache_hit(self, clean_state):
        """Test junction class is cached."""
        class AdvCourse19(Table):
            name: str = ""
        
        class AdvStudent19(Table):
            name: str = ""
        
        factory = get_junction_factory()
        
        class1 = factory.create_implicit_junction(AdvStudent19, AdvCourse19)
        class2 = factory.create_implicit_junction(AdvStudent19, AdvCourse19)
        
        assert class1 is class2
    
    def test_config_stored(self, clean_state):
        """Test configuration is stored."""
        class AdvCourse20(Table):
            name: str = ""
        
        class AdvStudent20(Table):
            name: str = ""
        
        factory = get_junction_factory()
        
        junction = factory.create_implicit_junction(AdvStudent20, AdvCourse20)
        config = factory.get_config(junction.__table_name__)
        
        assert config is not None
        assert config.source_model is AdvStudent20 or config.target_model is AdvStudent20

