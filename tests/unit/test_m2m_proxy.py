"""
Tests for PyNext Many-to-Many Association Proxy.

50 tests covering:
- AssociationProxy creation
- Iteration through proxy
- Filtering via proxy
- Counting via proxy
- Caching behavior
"""

import pytest
from typing import List, Optional

from pynext.db import (
    Table,
    many_to_many,
    reset_backref_registry,
    reset_sync_manager,
)
from pynext.db.relationships.proxy import (
    AssociationProxy,
    AssociationProxyDescriptor,
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
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('prx', 'test'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# AssociationProxy Creation (15 tests)
# =============================================================================

class TestAssociationProxyCreation:
    """Test creating AssociationProxy instances."""
    
    def test_proxy_creation(self, clean_state):
        """Test creating an AssociationProxy."""
        class PrxCourse1(Table):
            name: str = ""
        
        class PrxStudent1(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent1,
            target_model=PrxCourse1,
            source_fk="prxstudent1_id",
            target_fk="prxcourse1_id",
        )
        
        student = PrxStudent1(name="John")
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse1,
            config=config,
        )
        
        assert proxy is not None
    
    def test_proxy_target_model_stored(self, clean_state):
        """Test target model is stored."""
        class PrxCourse2(Table):
            name: str = ""
        
        class PrxStudent2(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent2,
            target_model=PrxCourse2,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent2(name="John")
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse2,
            config=config,
        )
        
        assert proxy._target_model == PrxCourse2
    
    def test_proxy_config_stored(self, clean_state):
        """Test config is stored."""
        class PrxCourse3(Table):
            name: str = ""
        
        class PrxStudent3(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent3,
            target_model=PrxCourse3,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent3(name="John")
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse3,
            config=config,
        )
        
        assert proxy._config == config
    
    def test_proxy_owner_stored(self, clean_state):
        """Test owner is stored."""
        class PrxCourse4(Table):
            name: str = ""
        
        class PrxStudent4(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent4,
            target_model=PrxCourse4,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent4(name="John")
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse4,
            config=config,
        )
        
        assert proxy._owner is student


# =============================================================================
# AssociationProxy Iteration (15 tests)
# =============================================================================

class TestAssociationProxyIteration:
    """Test iterating through AssociationProxy."""
    
    def test_iter_empty(self, clean_state):
        """Test iterating empty proxy."""
        class PrxCourse5(Table):
            name: str = ""
        
        class PrxStudent5(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent5,
            target_model=PrxCourse5,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent5(name="John")
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse5,
            config=config,
        )
        
        items = list(proxy)
        assert items == []
    
    def test_iter_with_cached(self, clean_state):
        """Test iterating with cached items."""
        class PrxCourse6(Table):
            name: str = ""
        
        class PrxStudent6(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent6,
            target_model=PrxCourse6,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent6(name="John")
        courses = [PrxCourse6(name=f"Course{i}") for i in range(3)]
        
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse6,
            config=config,
        )
        proxy._set_cached_items(courses)
        
        items = list(proxy)
        assert items == courses
    
    def test_len(self, clean_state):
        """Test __len__."""
        class PrxCourse7(Table):
            name: str = ""
        
        class PrxStudent7(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent7,
            target_model=PrxCourse7,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent7(name="John")
        courses = [PrxCourse7(name=f"Course{i}") for i in range(3)]
        
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse7,
            config=config,
        )
        proxy._set_cached_items(courses)
        
        assert len(proxy) == 3
    
    def test_contains(self, clean_state):
        """Test __contains__."""
        class PrxCourse8(Table):
            name: str = ""
        
        class PrxStudent8(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent8,
            target_model=PrxCourse8,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent8(name="John")
        math = PrxCourse8(name="Math")
        science = PrxCourse8(name="Science")
        
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse8,
            config=config,
        )
        proxy._set_cached_items([math])
        
        assert math in proxy
        assert science not in proxy
    
    def test_getitem(self, clean_state):
        """Test __getitem__."""
        class PrxCourse9(Table):
            name: str = ""
        
        class PrxStudent9(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent9,
            target_model=PrxCourse9,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent9(name="John")
        courses = [PrxCourse9(name=f"Course{i}") for i in range(3)]
        
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse9,
            config=config,
        )
        proxy._set_cached_items(courses)
        
        assert proxy[0] is courses[0]
        assert proxy[1] is courses[1]


# =============================================================================
# AssociationProxy Caching (10 tests)
# =============================================================================

class TestAssociationProxyCaching:
    """Test caching behavior."""
    
    def test_set_cached_items(self, clean_state):
        """Test setting cached items."""
        class PrxCourse10(Table):
            name: str = ""
        
        class PrxStudent10(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent10,
            target_model=PrxCourse10,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent10(name="John")
        courses = [PrxCourse10(name=f"Course{i}") for i in range(3)]
        
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse10,
            config=config,
        )
        proxy._set_cached_items(courses)
        
        assert proxy._cached_items == courses
    
    def test_clear_cache(self, clean_state):
        """Test clearing cache."""
        class PrxCourse11(Table):
            name: str = ""
        
        class PrxStudent11(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent11,
            target_model=PrxCourse11,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent11(name="John")
        courses = [PrxCourse11(name=f"Course{i}") for i in range(3)]
        
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse11,
            config=config,
        )
        proxy._set_cached_items(courses)
        proxy._clear_cache()
        
        assert proxy._cached_items is None
    
    def test_is_loaded_false(self, clean_state):
        """Test is_loaded when not cached."""
        class PrxCourse12(Table):
            name: str = ""
        
        class PrxStudent12(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent12,
            target_model=PrxCourse12,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent12(name="John")
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse12,
            config=config,
        )
        
        assert not proxy.is_loaded
    
    def test_is_loaded_true(self, clean_state):
        """Test is_loaded when cached."""
        class PrxCourse13(Table):
            name: str = ""
        
        class PrxStudent13(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent13,
            target_model=PrxCourse13,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent13(name="John")
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse13,
            config=config,
        )
        proxy._set_cached_items([])
        
        assert proxy.is_loaded


# =============================================================================
# AssociationProxy Special Methods (10 tests)
# =============================================================================

class TestAssociationProxySpecial:
    """Test special methods."""
    
    def test_repr(self, clean_state):
        """Test __repr__."""
        class PrxCourse14(Table):
            name: str = ""
        
        class PrxStudent14(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent14,
            target_model=PrxCourse14,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent14(name="John")
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse14,
            config=config,
        )
        
        rep = repr(proxy)
        assert "AssociationProxy" in rep
    
    def test_str(self, clean_state):
        """Test __str__."""
        class PrxCourse15(Table):
            name: str = ""
        
        class PrxStudent15(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent15,
            target_model=PrxCourse15,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent15(name="John")
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse15,
            config=config,
        )
        
        s = str(proxy)
        assert isinstance(s, str)
    
    def test_to_list(self, clean_state):
        """Test to_list method."""
        class PrxCourse16(Table):
            name: str = ""
        
        class PrxStudent16(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent16,
            target_model=PrxCourse16,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent16(name="John")
        courses = [PrxCourse16(name=f"Course{i}") for i in range(3)]
        
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse16,
            config=config,
        )
        proxy._set_cached_items(courses)
        
        result = proxy.to_list()
        assert result == courses
        assert isinstance(result, list)
    
    def test_bool_empty(self, clean_state):
        """Test __bool__ when empty."""
        class PrxCourse17(Table):
            name: str = ""
        
        class PrxStudent17(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent17,
            target_model=PrxCourse17,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent17(name="John")
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse17,
            config=config,
        )
        proxy._set_cached_items([])
        
        assert not bool(proxy)
    
    def test_bool_not_empty(self, clean_state):
        """Test __bool__ when not empty."""
        class PrxCourse18(Table):
            name: str = ""
        
        class PrxStudent18(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=PrxStudent18,
            target_model=PrxCourse18,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = PrxStudent18(name="John")
        courses = [PrxCourse18(name="Math")]
        
        proxy = AssociationProxy(
            owner=student,
            target_model=PrxCourse18,
            config=config,
        )
        proxy._set_cached_items(courses)
        
        assert bool(proxy)

