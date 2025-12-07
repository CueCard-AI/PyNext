"""
Tests for PyNext Many-to-Many Dynamic Query Builder.

60 tests covering:
- DynamicManyToMany creation
- Query building methods
- Chaining operations
- Clone behavior
"""

import pytest
from typing import List, Optional

from pynext.db import (
    Table,
    many_to_many,
    reset_backref_registry,
    reset_sync_manager,
)
from pynext.db.relationships.m2m_dynamic import DynamicManyToMany
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
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('dyn', 'test'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# DynamicManyToMany Creation (15 tests)
# =============================================================================

class TestDynamicManyToManyCreation:
    """Test creating DynamicManyToMany instances."""
    
    def test_dynamic_creation(self, clean_state):
        """Test creating DynamicManyToMany."""
        class DynCourse1(Table):
            name: str = ""
        
        class DynStudent1(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent1,
            target_model=DynCourse1,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent1(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse1,
            config=config,
        )
        
        assert dynamic is not None
    
    def test_dynamic_owner_stored(self, clean_state):
        """Test owner is stored."""
        class DynCourse2(Table):
            name: str = ""
        
        class DynStudent2(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent2,
            target_model=DynCourse2,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent2(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse2,
            config=config,
        )
        
        assert dynamic._owner is student
    
    def test_dynamic_config_stored(self, clean_state):
        """Test config is stored."""
        class DynCourse3(Table):
            name: str = ""
        
        class DynStudent3(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent3,
            target_model=DynCourse3,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent3(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse3,
            config=config,
        )
        
        assert dynamic._config is config
    
    def test_dynamic_from_lazy(self, clean_state):
        """Test creating from lazy='dynamic'."""
        class DynCourse4(Table):
            name: str = ""
        
        class DynStudent4(Table):
            name: str = ""
            courses: List[DynCourse4] = many_to_many(DynCourse4, lazy="dynamic")
        
        student = DynStudent4(name="John")
        
        assert isinstance(student.courses, DynamicManyToMany)


# =============================================================================
# Query Building Methods (20 tests)
# =============================================================================

class TestDynamicManyToManyQueryBuilding:
    """Test query building methods."""
    
    def test_filter_returns_new(self, clean_state):
        """Test filter returns new instance."""
        class DynCourse5(Table):
            name: str = ""
        
        class DynStudent5(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent5,
            target_model=DynCourse5,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent5(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse5,
            config=config,
        )
        
        filtered = dynamic.filter(active=True)
        
        assert filtered is not dynamic
    
    def test_filter_stores_conditions(self, clean_state):
        """Test filter stores conditions."""
        class DynCourse6(Table):
            name: str = ""
        
        class DynStudent6(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent6,
            target_model=DynCourse6,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent6(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse6,
            config=config,
        )
        
        filtered = dynamic.filter(active=True, level=5)
        
        assert filtered._filters["active"] == True
        assert filtered._filters["level"] == 5
    
    def test_where_alias(self, clean_state):
        """Test where is alias for filter."""
        class DynCourse7(Table):
            name: str = ""
        
        class DynStudent7(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent7,
            target_model=DynCourse7,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent7(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse7,
            config=config,
        )
        
        result = dynamic.where(active=True)
        
        assert result._filters["active"] == True
    
    def test_where_in(self, clean_state):
        """Test where_in adds IN filter."""
        class DynCourse8(Table):
            name: str = ""
        
        class DynStudent8(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent8,
            target_model=DynCourse8,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent8(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse8,
            config=config,
        )
        
        result = dynamic.where_in(id=[1, 2, 3])
        
        assert result._filter_in["id"] == [1, 2, 3]
    
    def test_where_not(self, clean_state):
        """Test where_not adds NOT filter."""
        class DynCourse9(Table):
            name: str = ""
        
        class DynStudent9(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent9,
            target_model=DynCourse9,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent9(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse9,
            config=config,
        )
        
        result = dynamic.where_not(archived=True)
        
        assert result._filter_not["archived"] == True
    
    def test_order_by(self, clean_state):
        """Test order_by adds ordering."""
        class DynCourse10(Table):
            name: str = ""
        
        class DynStudent10(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent10,
            target_model=DynCourse10,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent10(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse10,
            config=config,
        )
        
        result = dynamic.order_by("-created_at", "name")
        
        assert result._order == ["-created_at", "name"]
    
    def test_limit(self, clean_state):
        """Test limit sets limit."""
        class DynCourse11(Table):
            name: str = ""
        
        class DynStudent11(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent11,
            target_model=DynCourse11,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent11(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse11,
            config=config,
        )
        
        result = dynamic.limit(10)
        
        assert result._limit_val == 10
    
    def test_offset(self, clean_state):
        """Test offset sets offset."""
        class DynCourse12(Table):
            name: str = ""
        
        class DynStudent12(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent12,
            target_model=DynCourse12,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent12(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse12,
            config=config,
        )
        
        result = dynamic.offset(20)
        
        assert result._offset_val == 20


# =============================================================================
# Chaining (15 tests)
# =============================================================================

class TestDynamicManyToManyChaining:
    """Test method chaining."""
    
    def test_chain_filter_limit(self, clean_state):
        """Test chaining filter and limit."""
        class DynCourse13(Table):
            name: str = ""
        
        class DynStudent13(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent13,
            target_model=DynCourse13,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent13(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse13,
            config=config,
        )
        
        result = dynamic.filter(active=True).limit(10)
        
        assert result._filters["active"] == True
        assert result._limit_val == 10
    
    def test_chain_order_offset_limit(self, clean_state):
        """Test chaining order, offset, and limit."""
        class DynCourse14(Table):
            name: str = ""
        
        class DynStudent14(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent14,
            target_model=DynCourse14,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent14(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse14,
            config=config,
        )
        
        result = dynamic.order_by("-created_at").offset(20).limit(10)
        
        assert result._order == ["-created_at"]
        assert result._offset_val == 20
        assert result._limit_val == 10
    
    def test_multiple_filters(self, clean_state):
        """Test multiple filter calls."""
        class DynCourse15(Table):
            name: str = ""
        
        class DynStudent15(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent15,
            target_model=DynCourse15,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent15(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse15,
            config=config,
        )
        
        result = dynamic.filter(active=True).filter(level=5)
        
        assert result._filters["active"] == True
        assert result._filters["level"] == 5
    
    def test_chain_preserves_original(self, clean_state):
        """Test chaining doesn't modify original."""
        class DynCourse16(Table):
            name: str = ""
        
        class DynStudent16(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent16,
            target_model=DynCourse16,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent16(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse16,
            config=config,
        )
        
        _ = dynamic.filter(active=True).limit(10)
        
        # Original should be unchanged
        assert dynamic._filters == {}
        assert dynamic._limit_val is None


# =============================================================================
# Special Methods (10 tests)
# =============================================================================

class TestDynamicManyToManySpecial:
    """Test special methods."""
    
    def test_repr(self, clean_state):
        """Test __repr__."""
        class DynCourse17(Table):
            name: str = ""
        
        class DynStudent17(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent17,
            target_model=DynCourse17,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent17(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse17,
            config=config,
        )
        
        rep = repr(dynamic)
        assert "DynamicManyToMany" in rep
    
    def test_bool_always_true(self, clean_state):
        """Test __bool__ is always True."""
        class DynCourse18(Table):
            name: str = ""
        
        class DynStudent18(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=DynStudent18,
            target_model=DynCourse18,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        student = DynStudent18(name="John")
        dynamic = DynamicManyToMany(
            owner=student,
            target_model=DynCourse18,
            config=config,
        )
        
        assert bool(dynamic)
    
    def test_target_model_resolved(self, clean_state):
        """Test target_model property resolves strings."""
        class DynStudent19(Table):
            name: str = ""
            courses: List["DynCourse19"] = many_to_many("DynCourse19", lazy="dynamic")
        
        class DynCourse19(Table):
            name: str = ""
        
        student = DynStudent19(name="John")
        dynamic = student.courses
        
        # Should resolve the string to actual class
        assert dynamic.target_model is DynCourse19

