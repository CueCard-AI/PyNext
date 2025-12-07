"""
Test Phase 7.7: Polymorphic Edge Cases.

Tests edge cases and error handling for polymorphic relationships.
"""

import pytest
from typing import Optional, Union
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    generic_fk,
    get_strategy,
    get_polymorphic_registry,
    reset_polymorphic_registry,
    instantiate_polymorphic,
    InheritanceStrategy,
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
# Test Missing Discriminator Value
# =============================================================================

class TestMissingDiscriminator:
    """Test handling of missing discriminator values."""
    
    def test_null_discriminator_uses_base(self):
        """Null discriminator uses base class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": "Test", "type": None}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Content)
        assert not isinstance(instance, Article)
    
    def test_missing_discriminator_uses_base(self):
        """Missing discriminator uses base class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": "Test"}  # No 'type' key
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Content)


# =============================================================================
# Test Unknown Discriminator Value
# =============================================================================

class TestUnknownDiscriminator:
    """Test handling of unknown discriminator values."""
    
    def test_unknown_type_uses_base(self):
        """Unknown type value uses base class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": "Test", "type": "unknown_type"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Content)
        assert type(instance).__name__ == "Content"
    
    def test_empty_string_type_uses_base(self):
        """Empty string type uses base class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        row = {"id": 1, "type": ""}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Content)


# =============================================================================
# Test Duplicate Registration
# =============================================================================

class TestDuplicateRegistration:
    """Test handling of duplicate registrations."""
    
    def test_duplicate_identity_overwrites(self):
        """Duplicate identity overwrites previous."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article1(Content):
            pass
        
        @polymorphic.subtype("article")
        class Article2(Content):
            pass
        
        registry = get_polymorphic_registry()
        # Last registration wins
        assert registry.get_class(Content, "article") == Article2


# =============================================================================
# Test Multiple Inheritance Hierarchies
# =============================================================================

class TestMultipleHierarchies:
    """Test multiple independent polymorphic hierarchies."""
    
    def test_independent_hierarchies(self):
        """Multiple hierarchies are independent."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic("vehicle_type")
        class Vehicle:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        @polymorphic.subtype("car")
        class Car(Vehicle):
            pass
        
        registry = get_polymorphic_registry()
        
        # Each hierarchy has its own subtypes
        assert registry.get_class(Content, "article") == Article
        assert registry.get_class(Content, "car") is None
        
        assert registry.get_class(Vehicle, "car") == Car
        assert registry.get_class(Vehicle, "article") is None
    
    def test_same_identity_different_hierarchies(self):
        """Same identity in different hierarchies."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic("type")
        class Vehicle:
            pass
        
        @polymorphic.subtype("special")
        class SpecialContent(Content):
            pass
        
        @polymorphic.subtype("special")
        class SpecialVehicle(Vehicle):
            pass
        
        registry = get_polymorphic_registry()
        
        assert registry.get_class(Content, "special") == SpecialContent
        assert registry.get_class(Vehicle, "special") == SpecialVehicle


# =============================================================================
# Test Special Characters
# =============================================================================

class TestSpecialCharacters:
    """Test special characters in identities."""
    
    def test_unicode_identity(self):
        """Unicode characters in identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("文章")
        class ChineseArticle(Content):
            pass
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "文章") == ChineseArticle
    
    def test_hyphen_identity(self):
        """Hyphen in identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("blog-post")
        class BlogPost(Content):
            pass
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "blog-post") == BlogPost
    
    def test_underscore_identity(self):
        """Underscore in identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("blog_post")
        class BlogPost(Content):
            pass
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "blog_post") == BlogPost
    
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


# =============================================================================
# Test Empty and Minimal Classes
# =============================================================================

class TestMinimalClasses:
    """Test minimal class definitions."""
    
    def test_empty_base(self):
        """Empty base class."""
        @polymorphic("type")
        class Empty:
            pass
        
        assert get_strategy(Empty) is not None
    
    def test_empty_subtype(self):
        """Empty subtype."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("empty")
        class Empty(Content):
            pass
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "empty") == Empty
    
    def test_base_only_no_subtypes(self):
        """Base class with no subtypes."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        row = {"id": 1, "type": "anything"}
        
        # Should use base class
        instance = strategy.instantiate_from_row(row)
        assert isinstance(instance, Content)


# =============================================================================
# Test Generic FK Edge Cases
# =============================================================================

class MockModel:
    __tablename__ = "mocks"
    
    def __init__(self, id):
        self.id = id


class TestGenericFKEdgeCases:
    """Test generic FK edge cases."""
    
    def test_null_target_type(self):
        """Null target type."""
        class Comment:
            target: Union[MockModel] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        comment = Comment(content="Test", target_type=None, target_id=1)
        
        assert comment.target.is_set is False
    
    def test_null_target_id(self):
        """Null target ID."""
        class Comment:
            target: Union[MockModel] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        comment = Comment(content="Test", target_type="mocks", target_id=None)
        
        assert comment.target.is_set is False
    
    def test_unknown_target_type(self):
        """Unknown target type in loader."""
        class OtherModel:
            __tablename__ = "others"
            
            def __init__(self, id):
                self.id = id
        
        class Comment:
            target: Union[MockModel] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        # Target type doesn't match any allowed types
        comment = Comment(content="Test", target_type="unknowns", target_id=1)
        
        # Loader won't find the class
        from pynext.db.polymorphic import get_generic_fk_config
        config = get_generic_fk_config(Comment, "target")
        
        assert config.get_type_class("unknowns") is None


# =============================================================================
# Test Strategy Edge Cases
# =============================================================================

class TestStrategyEdgeCases:
    """Test strategy edge cases."""
    
    def test_non_polymorphic_returns_none(self):
        """get_strategy on non-polymorphic returns None."""
        class Regular:
            pass
        
        assert get_strategy(Regular) is None
    
    def test_strategy_for_subtype(self):
        """get_strategy works on subtypes."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        strategy = get_strategy(Article)
        assert strategy is not None

