"""
Test Phase 7.7: Instance Creation Tests.

Tests for creating instances from database rows across all strategies.
"""

import pytest
from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    get_strategy,
    instantiate_polymorphic,
    get_polymorphic_registry,
    reset_polymorphic_registry,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_registry():
    """Reset registry before each test."""
    reset_polymorphic_registry()
    yield
    reset_polymorphic_registry()


# =============================================================================
# Test STI Instantiation
# =============================================================================

class TestSTIInstantiation:
    """Test STI instance creation."""
    
    def test_instantiate_base(self):
        """Instantiate base class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": "Test"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Content)
        assert instance.id == 1
        assert instance.title == "Test"
    
    def test_instantiate_subtype_by_discriminator(self):
        """Instantiate subtype based on discriminator."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        strategy = get_strategy(Content)
        row = {"id": 1, "type": "article", "body": "Content"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Article)
        assert instance.body == "Content"
    
    def test_unknown_type_uses_base(self):
        """Unknown type uses base class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        strategy = get_strategy(Content)
        row = {"id": 1, "type": "unknown"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Content)
        assert type(instance).__name__ == "Content"
    
    def test_null_type_uses_base(self):
        """Null type uses base class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        row = {"id": 1, "type": None}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Content)
    
    def test_missing_type_uses_base(self):
        """Missing type uses base class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        row = {"id": 1}  # No type key
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Content)
    
    def test_force_target_class(self):
        """Force specific target class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        strategy = get_strategy(Content)
        row = {"id": 1, "type": "article"}
        
        # Force Content instead of Article
        instance = strategy.instantiate_from_row(row, target_class=Content)
        
        assert type(instance).__name__ == "Content"


# =============================================================================
# Test Joined Instantiation
# =============================================================================

class TestJoinedInstantiation:
    """Test Joined instance creation."""
    
    def test_instantiate_with_all_fields(self):
        """Instantiate with base and subtype fields."""
        @polymorphic("type", strategy="joined")
        class Employee:
            __tablename__ = "employees"
            id: int
            name: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("manager")
        class Manager(Employee):
            __tablename__ = "managers"
            department: str
        
        strategy = get_strategy(Employee)
        row = {
            "id": 1,
            "name": "Jane",
            "type": "manager",
            "department": "Engineering"
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Manager)
        assert instance.name == "Jane"
        assert instance.department == "Engineering"
    
    def test_null_subtype_fields(self):
        """Null values in subtype fields."""
        @polymorphic("type", strategy="joined")
        class Employee:
            __tablename__ = "employees"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("manager")
        class Manager(Employee):
            __tablename__ = "managers"
            department: str
        
        strategy = get_strategy(Employee)
        row = {"id": 1, "type": "manager", "department": None}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Manager)
        assert instance.department is None


# =============================================================================
# Test Concrete Instantiation
# =============================================================================

class TestConcreteInstantiation:
    """Test Concrete instance creation."""
    
    def test_instantiate_with_type_column(self):
        """Instantiate using _type column."""
        @polymorphic(strategy="concrete")
        class Vehicle:
            __tablename__ = "vehicles"
            id: int
            make: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("car")
        class Car(Vehicle):
            __tablename__ = "cars"
            doors: int
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "make": "Toyota", "_type": "car", "doors": 4}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Car)
        assert instance.doors == 4
    
    def test_type_column_removed(self):
        """_type column not in instance."""
        @polymorphic(strategy="concrete")
        class Vehicle:
            __tablename__ = "vehicles"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("car")
        class Car(Vehicle):
            __tablename__ = "cars"
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "_type": "car"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert not hasattr(instance, '_type')


# =============================================================================
# Test instantiate_polymorphic Helper
# =============================================================================

class TestInstantiatePolymorphicHelper:
    """Test instantiate_polymorphic helper function."""
    
    def test_with_polymorphism_default(self):
        """Polymorphism enabled by default."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        row = {"id": 1, "type": "article"}
        instance = instantiate_polymorphic(Content, row)
        
        assert isinstance(instance, Article)
    
    def test_without_polymorphism(self):
        """Polymorphism disabled."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        row = {"id": 1, "type": "article"}
        instance = instantiate_polymorphic(Content, row, use_polymorphism=False)
        
        assert type(instance).__name__ == "Content"
    
    def test_non_polymorphic_class(self):
        """Non-polymorphic class just uses constructor."""
        class Regular:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        row = {"id": 1, "name": "Test"}
        instance = instantiate_polymorphic(Regular, row)
        
        assert isinstance(instance, Regular)
        assert instance.name == "Test"


# =============================================================================
# Test Field Types
# =============================================================================

class TestFieldTypes:
    """Test various field types in instantiation."""
    
    def test_string_field(self):
        """String field."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            title: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        instance = strategy.instantiate_from_row({"title": "Hello World"})
        
        assert instance.title == "Hello World"
    
    def test_int_field(self):
        """Integer field."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            count: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        instance = strategy.instantiate_from_row({"count": 42})
        
        assert instance.count == 42
    
    def test_float_field(self):
        """Float field."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            score: float
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        instance = strategy.instantiate_from_row({"score": 3.14})
        
        assert instance.score == 3.14
    
    def test_bool_field(self):
        """Boolean field."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            published: bool
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        instance = strategy.instantiate_from_row({"published": True})
        
        assert instance.published is True
    
    def test_datetime_field(self):
        """Datetime field."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            created_at: datetime
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        now = datetime.now()
        strategy = get_strategy(Content)
        instance = strategy.instantiate_from_row({"created_at": now})
        
        assert instance.created_at == now
    
    def test_none_field(self):
        """None value."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            title: Optional[str]
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        instance = strategy.instantiate_from_row({"title": None})
        
        assert instance.title is None


# =============================================================================
# Test Multiple Instances
# =============================================================================

class TestMultipleInstances:
    """Test creating multiple instances."""
    
    def test_batch_instantiation(self):
        """Create multiple instances."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        @polymorphic.subtype("video")
        class Video(Content):
            pass
        
        strategy = get_strategy(Content)
        rows = [
            {"id": 1, "type": "article"},
            {"id": 2, "type": "video"},
            {"id": 3, "type": "article"},
            {"id": 4, "type": "video"},
            {"id": 5, "type": "unknown"},
        ]
        
        instances = [strategy.instantiate_from_row(row) for row in rows]
        
        assert isinstance(instances[0], Article)
        assert isinstance(instances[1], Video)
        assert isinstance(instances[2], Article)
        assert isinstance(instances[3], Video)
        assert isinstance(instances[4], Content)  # Unknown falls back
    
    def test_instances_are_independent(self):
        """Instances don't share state."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        
        instance1 = strategy.instantiate_from_row({"id": 1, "title": "First"})
        instance2 = strategy.instantiate_from_row({"id": 2, "title": "Second"})
        
        assert instance1.id != instance2.id
        assert instance1.title != instance2.title
        
        # Modify one doesn't affect other
        instance1.title = "Modified"
        assert instance2.title == "Second"

