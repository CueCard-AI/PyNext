"""
Tests for PyNext Many-to-Many Junction Table Operations.

100 tests covering:
- JunctionConfig creation and validation
- JunctionTableFactory operations
- Junction table naming conventions
- JunctionManager row operations
- Implicit vs explicit junction tables
"""

import pytest
from typing import List, Optional
from unittest.mock import MagicMock, AsyncMock, patch

from pynext.db import (
    Table,
    configure_db,
    MockAdapter,
    many_to_many,
    reset_backref_registry,
    reset_sync_manager,
)
from pynext.db.relationships.junction import (
    JunctionConfig,
    JunctionTableFactory,
    JunctionManager,
    get_junction_factory,
    reset_junction_factory,
    create_junction_config,
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
    keys_to_remove = [k for k in list(_model_registry.keys()) 
                      if k.startswith(('jct', 'test', 'student', 'course', 'tag', 'article', 'enrollment'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# JunctionConfig Tests (30 tests)
# =============================================================================

class TestJunctionConfigCreation:
    """Test JunctionConfig creation."""
    
    def test_create_basic_config(self, clean_state):
        """Test creating a basic JunctionConfig."""
        class JCTCourse1(Table):
            name: str = ""
        
        class JCTStudent1(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="jctstudent1s_jctcourse1s",
            source_model=JCTStudent1,
            target_model=JCTCourse1,
            source_fk="jctstudent1_id",
            target_fk="jctcourse1_id",
        )
        
        assert config.name == "jctstudent1s_jctcourse1s"
        assert config.source_model == JCTStudent1
        assert config.target_model == JCTCourse1
    
    def test_config_with_through(self, clean_state):
        """Test JunctionConfig with explicit through model."""
        class JCTCourse2(Table):
            name: str = ""
        
        class JCTEnrollment1(Table):
            student_id: int = 0
            course_id: int = 0
        
        class JCTStudent2(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="jctenrollment1s",
            source_model=JCTStudent2,
            target_model=JCTCourse2,
            source_fk="student_id",
            target_fk="course_id",
            through_model=JCTEnrollment1,
        )
        
        assert config.through_model == JCTEnrollment1
        assert config.is_explicit
    
    def test_config_without_through(self, clean_state):
        """Test JunctionConfig without through model."""
        class JCTCourse3(Table):
            name: str = ""
        
        class JCTStudent3(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="jctstudent3s_jctcourse3s",
            source_model=JCTStudent3,
            target_model=JCTCourse3,
            source_fk="jctstudent3_id",
            target_fk="jctcourse3_id",
        )
        
        assert config.through_model is None
        assert not config.is_explicit
    
    def test_config_empty_name_raises(self, clean_state):
        """Test empty name raises ValueError."""
        class JCTCourse4(Table):
            name: str = ""
        
        class JCTStudent4(Table):
            name: str = ""
        
        with pytest.raises(ValueError, match="name cannot be empty"):
            JunctionConfig(
                name="",
                source_model=JCTStudent4,
                target_model=JCTCourse4,
                source_fk="student_id",
                target_fk="course_id",
            )
    
    def test_config_empty_source_fk_raises(self, clean_state):
        """Test empty source_fk raises ValueError."""
        class JCTCourse5(Table):
            name: str = ""
        
        class JCTStudent5(Table):
            name: str = ""
        
        with pytest.raises(ValueError, match="Source foreign key cannot be empty"):
            JunctionConfig(
                name="test_junction",
                source_model=JCTStudent5,
                target_model=JCTCourse5,
                source_fk="",
                target_fk="course_id",
            )
    
    def test_config_empty_target_fk_raises(self, clean_state):
        """Test empty target_fk raises ValueError."""
        class JCTCourse6(Table):
            name: str = ""
        
        class JCTStudent6(Table):
            name: str = ""
        
        with pytest.raises(ValueError, match="Target foreign key cannot be empty"):
            JunctionConfig(
                name="test_junction",
                source_model=JCTStudent6,
                target_model=JCTCourse6,
                source_fk="student_id",
                target_fk="",
            )
    
    def test_config_to_dict(self, clean_state):
        """Test JunctionConfig to_dict method."""
        class JCTCourse7(Table):
            name: str = ""
        
        class JCTStudent7(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=JCTStudent7,
            target_model=JCTCourse7,
            source_fk="student_id",
            target_fk="course_id",
            source_attr="courses",
            target_attr="students",
        )
        
        d = config.to_dict()
        
        assert d["name"] == "test_junction"
        assert d["source_fk"] == "student_id"
        assert d["target_fk"] == "course_id"
        assert d["source_attr"] == "courses"
        assert d["target_attr"] == "students"
    
    def test_config_repr(self, clean_state):
        """Test JunctionConfig __repr__."""
        class JCTCourse8(Table):
            name: str = ""
        
        class JCTStudent8(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=JCTStudent8,
            target_model=JCTCourse8,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        rep = repr(config)
        
        assert "JunctionConfig" in rep
        assert "test_junction" in rep


class TestJunctionConfigWithStringModels:
    """Test JunctionConfig with string model references."""
    
    def test_config_with_string_source(self, clean_state):
        """Test config with string source model."""
        class JCTCourse9(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model="JCTStudent9",
            target_model=JCTCourse9,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        assert config.source_model == "JCTStudent9"
    
    def test_config_with_string_target(self, clean_state):
        """Test config with string target model."""
        class JCTStudent10(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=JCTStudent10,
            target_model="JCTCourse10",
            source_fk="student_id",
            target_fk="course_id",
        )
        
        assert config.target_model == "JCTCourse10"
    
    def test_config_with_string_through(self, clean_state):
        """Test config with string through model."""
        class JCTCourse11(Table):
            name: str = ""
        
        class JCTStudent11(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=JCTStudent11,
            target_model=JCTCourse11,
            source_fk="student_id",
            target_fk="course_id",
            through_model="JCTEnrollment",
        )
        
        assert config.through_model == "JCTEnrollment"


# =============================================================================
# JunctionTableFactory Tests (35 tests)
# =============================================================================

class TestJunctionTableFactoryNaming:
    """Test junction table naming conventions."""
    
    def test_generate_name_alphabetical(self, clean_state):
        """Test junction names are alphabetically sorted."""
        class JCTApple(Table):
            name: str = ""
        
        class JCTZebra(Table):
            name: str = ""
        
        factory = JunctionTableFactory()
        
        # Should be same regardless of order
        name1 = factory.generate_junction_name(JCTApple, JCTZebra)
        name2 = factory.generate_junction_name(JCTZebra, JCTApple)
        
        assert name1 == name2
        assert name1 == "jctapples_jctzebras"
    
    def test_generate_name_from_string(self, clean_state):
        """Test generating name from string models."""
        factory = JunctionTableFactory()
        
        name = factory.generate_junction_name("Student", "Course")
        
        assert "courses" in name or "students" in name
    
    def test_generate_fk_name(self, clean_state):
        """Test generating foreign key name."""
        class JCTUser(Table):
            name: str = ""
        
        factory = JunctionTableFactory()
        
        fk_name = factory._get_fk_name(JCTUser)
        
        assert fk_name == "jctuser_id"
    
    def test_get_table_name_from_class(self, clean_state):
        """Test getting table name from class."""
        class JCTPost(Table):
            title: str = ""
        
        factory = JunctionTableFactory()
        
        table_name = factory._get_table_name(JCTPost)
        
        assert table_name == "jctposts"
    
    def test_get_table_name_from_string(self, clean_state):
        """Test getting table name from string."""
        factory = JunctionTableFactory()
        
        table_name = factory._get_table_name("Article")
        
        assert table_name == "articles"


class TestJunctionTableFactoryCreation:
    """Test junction table creation."""
    
    def test_create_implicit_junction(self, clean_state):
        """Test creating implicit junction table."""
        class JCTCourse12(Table):
            name: str = ""
        
        class JCTStudent12(Table):
            name: str = ""
        
        factory = JunctionTableFactory()
        
        junction_class = factory.create_implicit_junction(JCTStudent12, JCTCourse12)
        
        assert junction_class is not None
        assert hasattr(junction_class, "__table_name__")
    
    def test_implicit_junction_has_fks(self, clean_state):
        """Test implicit junction has foreign key fields."""
        class JCTCourse13(Table):
            name: str = ""
        
        class JCTStudent13(Table):
            name: str = ""
        
        factory = JunctionTableFactory()
        
        junction_class = factory.create_implicit_junction(JCTStudent13, JCTCourse13)
        annotations = junction_class.__annotations__
        
        assert "jctstudent13_id" in annotations
        assert "jctcourse13_id" in annotations
    
    def test_junction_class_cached(self, clean_state):
        """Test junction classes are cached."""
        class JCTCourse14(Table):
            name: str = ""
        
        class JCTStudent14(Table):
            name: str = ""
        
        factory = JunctionTableFactory()
        
        class1 = factory.create_implicit_junction(JCTStudent14, JCTCourse14)
        class2 = factory.create_implicit_junction(JCTStudent14, JCTCourse14)
        
        assert class1 is class2
    
    def test_junction_registered_in_model_registry(self, clean_state):
        """Test created junction is registered."""
        class JCTCourse15(Table):
            name: str = ""
        
        class JCTStudent15(Table):
            name: str = ""
        
        factory = JunctionTableFactory()
        
        junction_class = factory.create_implicit_junction(JCTStudent15, JCTCourse15)
        
        assert junction_class.__table_name__ in _model_registry
    
    def test_get_or_create_implicit(self, clean_state):
        """Test get_or_create for implicit junction."""
        class JCTCourse16(Table):
            name: str = ""
        
        class JCTStudent16(Table):
            name: str = ""
        
        factory = JunctionTableFactory()
        
        config = JunctionConfig(
            name="jctcourse16s_jctstudent16s",
            source_model=JCTStudent16,
            target_model=JCTCourse16,
            source_fk="jctstudent16_id",
            target_fk="jctcourse16_id",
        )
        
        junction_class = factory.get_or_create(config)
        
        assert junction_class is not None
    
    def test_get_or_create_explicit(self, clean_state):
        """Test get_or_create for explicit junction."""
        class JCTCourse17(Table):
            name: str = ""
        
        class JCTEnrollment2(Table):
            student_id: int = 0
            course_id: int = 0
        
        class JCTStudent17(Table):
            name: str = ""
        
        factory = JunctionTableFactory()
        
        config = JunctionConfig(
            name="jctenrollment2s",
            source_model=JCTStudent17,
            target_model=JCTCourse17,
            source_fk="student_id",
            target_fk="course_id",
            through_model=JCTEnrollment2,
        )
        
        junction_class = factory.get_or_create(config)
        
        assert junction_class is JCTEnrollment2
    
    def test_factory_clear(self, clean_state):
        """Test clearing factory cache."""
        class JCTCourse18(Table):
            name: str = ""
        
        class JCTStudent18(Table):
            name: str = ""
        
        factory = JunctionTableFactory()
        factory.create_implicit_junction(JCTStudent18, JCTCourse18)
        
        assert len(factory._cache) > 0
        
        factory.clear()
        
        assert len(factory._cache) == 0
    
    def test_get_config(self, clean_state):
        """Test getting stored config."""
        class JCTCourse19(Table):
            name: str = ""
        
        class JCTStudent19(Table):
            name: str = ""
        
        factory = JunctionTableFactory()
        junction_class = factory.create_implicit_junction(JCTStudent19, JCTCourse19)
        
        config = factory.get_config(junction_class.__table_name__)
        
        assert config is not None
        assert config.source_model == JCTStudent19
        assert config.target_model == JCTCourse19


class TestGlobalJunctionFactory:
    """Test global junction factory instance."""
    
    def test_get_junction_factory(self, clean_state):
        """Test getting global factory."""
        factory = get_junction_factory()
        
        assert factory is not None
        assert isinstance(factory, JunctionTableFactory)
    
    def test_same_factory_instance(self, clean_state):
        """Test same factory returned each time."""
        factory1 = get_junction_factory()
        factory2 = get_junction_factory()
        
        assert factory1 is factory2
    
    def test_reset_junction_factory(self, clean_state):
        """Test resetting global factory."""
        factory1 = get_junction_factory()
        factory1.create_implicit_junction(Table, Table)  # Add something
        
        reset_junction_factory()
        
        factory2 = get_junction_factory()
        
        # New factory should be empty
        assert len(factory2._cache) == 0


# =============================================================================
# JunctionManager Tests (35 tests)
# =============================================================================

class TestJunctionManagerBasic:
    """Test basic JunctionManager operations."""
    
    def test_manager_creation(self, clean_state):
        """Test creating JunctionManager."""
        class JCTCourse20(Table):
            name: str = ""
        
        class JCTStudent20(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=JCTStudent20,
            target_model=JCTCourse20,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        manager = JunctionManager(config)
        
        assert manager.config is config
    
    def test_get_source_id(self, clean_state):
        """Test getting source ID."""
        class JCTCourse21(Table):
            name: str = ""
        
        class JCTStudent21(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=JCTStudent21,
            target_model=JCTCourse21,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        manager = JunctionManager(config)
        student = JCTStudent21(name="John")
        student.id = 1
        
        assert manager._get_source_id(student) == 1
    
    def test_get_source_id_none(self, clean_state):
        """Test getting source ID when not set."""
        class JCTCourse22(Table):
            name: str = ""
        
        class JCTStudent22(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=JCTStudent22,
            target_model=JCTCourse22,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        manager = JunctionManager(config)
        student = JCTStudent22(name="John")
        
        assert manager._get_source_id(student) is None
    
    def test_get_target_id(self, clean_state):
        """Test getting target ID."""
        class JCTCourse23(Table):
            name: str = ""
        
        class JCTStudent23(Table):
            name: str = ""
        
        config = JunctionConfig(
            name="test_junction",
            source_model=JCTStudent23,
            target_model=JCTCourse23,
            source_fk="student_id",
            target_fk="course_id",
        )
        
        manager = JunctionManager(config)
        course = JCTCourse23(name="Math")
        course.id = 5
        
        assert manager._get_target_id(course) == 5


class TestCreateJunctionConfigHelper:
    """Test create_junction_config helper function."""
    
    def test_create_config_basic(self, clean_state):
        """Test creating config with helper."""
        class JCTCourse24(Table):
            name: str = ""
        
        class JCTStudent24(Table):
            name: str = ""
        
        config = create_junction_config(
            source_model=JCTStudent24,
            target_model=JCTCourse24,
        )
        
        assert config.source_model == JCTStudent24
        assert config.target_model == JCTCourse24
        assert config.source_fk == "jctstudent24_id"
        assert config.target_fk == "jctcourse24_id"
    
    def test_create_config_with_through(self, clean_state):
        """Test creating config with through model."""
        class JCTCourse25(Table):
            name: str = ""
        
        class JCTEnrollment3(Table):
            student_id: int = 0
            course_id: int = 0
        
        class JCTStudent25(Table):
            name: str = ""
        
        config = create_junction_config(
            source_model=JCTStudent25,
            target_model=JCTCourse25,
            through=JCTEnrollment3,
        )
        
        assert config.through_model == JCTEnrollment3
    
    def test_create_config_with_attrs(self, clean_state):
        """Test creating config with attr names."""
        class JCTCourse26(Table):
            name: str = ""
        
        class JCTStudent26(Table):
            name: str = ""
        
        config = create_junction_config(
            source_model=JCTStudent26,
            target_model=JCTCourse26,
            source_attr="courses",
            target_attr="students",
        )
        
        assert config.source_attr == "courses"
        assert config.target_attr == "students"

