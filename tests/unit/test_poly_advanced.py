"""
Test Phase 7.7: Advanced Polymorphic Tests.

Advanced edge cases and complex scenarios.
"""

import pytest
from typing import Optional, Union, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    generic_fk,
    get_strategy,
    get_polymorphic_registry,
    reset_polymorphic_registry,
    InheritanceStrategy,
    get_inheritance_strategy,
    is_polymorphic,
    is_polymorphic_base,
    is_polymorphic_subtype,
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
# Test Deep Hierarchies
# =============================================================================

class TestDeepHierarchies:
    """Test deep inheritance hierarchies."""
    
    def test_many_subtypes(self):
        """Many subtypes from one base."""
        @polymorphic("type")
        class Event:
            __tablename__ = "events"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        # Create 20 subtypes
        subtypes = []
        for i in range(20):
            @polymorphic.subtype(f"event_{i}")
            class EventType(Event):
                pass
            EventType.__name__ = f"EventType{i}"
            subtypes.append(EventType)
        
        registry = get_polymorphic_registry()
        assert len(registry.get_all_subtypes(Event)) == 20
    
    def test_instantiate_many_subtypes(self):
        """Instantiate from many subtypes."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("type_a")
        class TypeA(Content):
            pass
        
        @polymorphic.subtype("type_b")
        class TypeB(Content):
            pass
        
        @polymorphic.subtype("type_c")
        class TypeC(Content):
            pass
        
        @polymorphic.subtype("type_d")
        class TypeD(Content):
            pass
        
        @polymorphic.subtype("type_e")
        class TypeE(Content):
            pass
        
        strategy = get_strategy(Content)
        
        rows = [
            {"id": 1, "type": "type_a"},
            {"id": 2, "type": "type_b"},
            {"id": 3, "type": "type_c"},
            {"id": 4, "type": "type_d"},
            {"id": 5, "type": "type_e"},
        ]
        
        instances = [strategy.instantiate_from_row(row) for row in rows]
        
        assert isinstance(instances[0], TypeA)
        assert isinstance(instances[1], TypeB)
        assert isinstance(instances[2], TypeC)
        assert isinstance(instances[3], TypeD)
        assert isinstance(instances[4], TypeE)


# =============================================================================
# Test Mixed Hierarchies
# =============================================================================

class TestMixedHierarchies:
    """Test multiple polymorphic hierarchies."""
    
    def test_independent_registries(self):
        """Multiple hierarchies don't interfere."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic("type")
        class Vehicle:
            pass
        
        @polymorphic("type")
        class User:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        @polymorphic.subtype("car")
        class Car(Vehicle):
            pass
        
        @polymorphic.subtype("admin")
        class Admin(User):
            pass
        
        registry = get_polymorphic_registry()
        
        # Each hierarchy is separate
        assert registry.get_class(Content, "article") == Article
        assert registry.get_class(Content, "car") is None
        assert registry.get_class(Content, "admin") is None
        
        assert registry.get_class(Vehicle, "car") == Car
        assert registry.get_class(Vehicle, "article") is None
        
        assert registry.get_class(User, "admin") == Admin
    
    def test_same_identity_different_bases(self):
        """Same identity in different hierarchies."""
        @polymorphic("type")
        class A:
            pass
        
        @polymorphic("type")
        class B:
            pass
        
        @polymorphic.subtype("same")
        class ASame(A):
            pass
        
        @polymorphic.subtype("same")
        class BSame(B):
            pass
        
        registry = get_polymorphic_registry()
        
        assert registry.get_class(A, "same") == ASame
        assert registry.get_class(B, "same") == BSame
        assert ASame != BSame


# =============================================================================
# Test Special Identities
# =============================================================================

class TestSpecialIdentities:
    """Test special identity values."""
    
    def test_unicode_identity(self):
        """Unicode in identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("文章")
        class ChineseContent(Content):
            pass
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "文章") == ChineseContent
    
    def test_emoji_identity(self):
        """Emoji in identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("📄")
        class DocumentContent(Content):
            pass
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "📄") == DocumentContent
    
    def test_whitespace_identity(self):
        """Identity with spaces."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("blog post")
        class BlogPost(Content):
            pass
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "blog post") == BlogPost
    
    def test_numeric_identity(self):
        """Numeric identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("123")
        class Type123(Content):
            pass
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "123") == Type123
    
    def test_long_identity(self):
        """Very long identity."""
        @polymorphic("type")
        class Content:
            pass
        
        long_identity = "a" * 200
        
        @polymorphic.subtype(long_identity)
        class LongType(Content):
            pass
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, long_identity) == LongType


# =============================================================================
# Test Complex Fields
# =============================================================================

class TestComplexFields:
    """Test complex field types."""
    
    def test_list_field(self):
        """List field in subtype."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("gallery")
        class Gallery(Content):
            images: List[str]
        
        strategy = get_strategy(Content)
        row = {"id": 1, "type": "gallery", "images": ["a.jpg", "b.jpg"]}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Gallery)
        assert instance.images == ["a.jpg", "b.jpg"]
    
    def test_dict_field(self):
        """Dict field in subtype."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("config")
        class ConfigContent(Content):
            settings: Dict[str, Any]
        
        strategy = get_strategy(Content)
        row = {"id": 1, "type": "config", "settings": {"key": "value"}}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, ConfigContent)
        assert instance.settings == {"key": "value"}
    
    def test_decimal_field(self):
        """Decimal field."""
        @polymorphic("type")
        class Product:
            __tablename__ = "products"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("physical")
        class PhysicalProduct(Product):
            price: Decimal
            weight: Decimal
        
        strategy = get_strategy(Product)
        row = {
            "id": 1,
            "type": "physical",
            "price": Decimal("19.99"),
            "weight": Decimal("0.5")
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, PhysicalProduct)
        assert instance.price == Decimal("19.99")


# =============================================================================
# Test Performance Patterns
# =============================================================================

class TestPerformancePatterns:
    """Test patterns that could affect performance."""
    
    def test_large_batch_instantiation(self):
        """Instantiate many rows."""
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
        
        # 1000 rows
        rows = [
            {"id": i, "type": "article" if i % 2 == 0 else "video"}
            for i in range(1000)
        ]
        
        instances = [strategy.instantiate_from_row(row) for row in rows]
        
        assert len(instances) == 1000
        assert all(isinstance(i, (Article, Video)) for i in instances)
    
    def test_registry_lookup_performance(self):
        """Registry lookup is fast."""
        @polymorphic("type")
        class Content:
            pass
        
        # Register many subtypes
        for i in range(100):
            @polymorphic.subtype(f"type_{i}")
            class SubType(Content):
                pass
            SubType.__name__ = f"SubType{i}"
        
        registry = get_polymorphic_registry()
        
        # Lookups should be O(1)
        for i in range(100):
            cls = registry.get_class(Content, f"type_{i}")
            assert cls is not None


# =============================================================================
# Test Error Recovery
# =============================================================================

class TestErrorRecovery:
    """Test error recovery and graceful degradation."""
    
    def test_missing_type_graceful(self):
        """Missing type falls back gracefully."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        row = {"id": 1}  # No type
        
        # Should not raise
        instance = strategy.instantiate_from_row(row)
        assert isinstance(instance, Content)
    
    def test_unknown_type_graceful(self):
        """Unknown type falls back gracefully."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("known")
        class Known(Content):
            pass
        
        strategy = get_strategy(Content)
        row = {"id": 1, "type": "unknown"}
        
        # Should not raise, falls back to base
        instance = strategy.instantiate_from_row(row)
        assert isinstance(instance, Content)
        assert type(instance).__name__ == "Content"
    
    def test_extra_fields_accepted(self):
        """Extra fields in row are accepted."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        row = {"id": 1, "type": None, "extra_field": "value", "another": 123}
        
        instance = strategy.instantiate_from_row(row)
        
        assert instance.extra_field == "value"
        assert instance.another == 123

