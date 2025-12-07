"""
Test Phase 7.7: Decorator Tests.

Tests for @polymorphic and @polymorphic.subtype decorators.
"""

import pytest
from typing import Optional
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    is_polymorphic,
    is_polymorphic_base,
    is_polymorphic_subtype,
    get_polymorphic_identity,
    get_discriminator_column,
    get_inheritance_strategy,
    get_polymorphic_registry,
    reset_polymorphic_registry,
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
# Test @polymorphic Decorator Syntax
# =============================================================================

class TestPolymorphicDecoratorSyntax:
    """Test @polymorphic decorator syntax variations."""
    
    def test_with_discriminator(self):
        """Basic usage with discriminator."""
        @polymorphic("type")
        class Content:
            pass
        
        assert is_polymorphic_base(Content)
        assert get_discriminator_column(Content) == "type"
    
    def test_without_parentheses(self):
        """Usage without parentheses."""
        @polymorphic
        class Content:
            pass
        
        assert is_polymorphic_base(Content)
        assert get_discriminator_column(Content) == "type"
    
    def test_with_empty_parentheses(self):
        """Usage with empty parentheses."""
        @polymorphic()
        class Content:
            pass
        
        assert is_polymorphic_base(Content)
        assert get_discriminator_column(Content) == "type"
    
    def test_with_strategy(self):
        """Specify strategy."""
        @polymorphic("type", strategy="joined")
        class Content:
            pass
        
        assert get_inheritance_strategy(Content) == InheritanceStrategy.JOINED
    
    def test_with_identity(self):
        """Specify base identity."""
        @polymorphic("type", identity="base")
        class Content:
            pass
        
        assert get_polymorphic_identity(Content) == "base"
    
    def test_all_parameters(self):
        """All parameters."""
        @polymorphic("kind", strategy="concrete", identity="base_content")
        class Content:
            pass
        
        assert get_discriminator_column(Content) == "kind"
        assert get_inheritance_strategy(Content) == InheritanceStrategy.CONCRETE
        assert get_polymorphic_identity(Content) == "base_content"


# =============================================================================
# Test @polymorphic.subtype Decorator
# =============================================================================

class TestSubtypeDecorator:
    """Test @polymorphic.subtype decorator."""
    
    def test_with_identity(self):
        """Specify identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert get_polymorphic_identity(Article) == "article"
    
    def test_auto_identity(self):
        """Auto-generated identity from class name."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype()
        class Article(Content):
            pass
        
        assert get_polymorphic_identity(Article) == "article"
    
    def test_with_empty_parentheses(self):
        """Empty parentheses for auto identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype()
        class MyArticle(Content):
            pass
        
        assert get_polymorphic_identity(MyArticle) == "myarticle"
    
    def test_custom_identity_string(self):
        """Custom identity string."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("blog-post")
        class BlogPost(Content):
            pass
        
        assert get_polymorphic_identity(BlogPost) == "blog-post"


# =============================================================================
# Test Decorator Class Modification
# =============================================================================

class TestDecoratorClassModification:
    """Test how decorator modifies the class."""
    
    def test_adds_polymorphic_config(self):
        """Adds _polymorphic_config."""
        @polymorphic("type")
        class Content:
            pass
        
        assert hasattr(Content, '_polymorphic_config')
    
    def test_adds_is_polymorphic_base_flag(self):
        """Adds _is_polymorphic_base."""
        @polymorphic("type")
        class Content:
            pass
        
        assert Content._is_polymorphic_base is True
    
    def test_subtype_adds_identity(self):
        """Subtype adds _polymorphic_identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert Article._polymorphic_identity == "article"
    
    def test_subtype_adds_base_reference(self):
        """Subtype adds _polymorphic_base."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert Article._polymorphic_base == Content
    
    def test_subtype_adds_is_subtype_flag(self):
        """Subtype adds _is_polymorphic_subtype."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert Article._is_polymorphic_subtype is True
    
    def test_discriminator_added_to_annotations(self):
        """Discriminator added to __annotations__."""
        @polymorphic("type")
        class Content:
            title: str
        
        assert "type" in Content.__annotations__


# =============================================================================
# Test Decorator Error Handling
# =============================================================================

class TestDecoratorErrors:
    """Test decorator error handling."""
    
    def test_invalid_strategy(self):
        """Invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            @polymorphic("type", strategy="invalid")
            class Content:
                pass
    
    def test_subtype_without_base(self):
        """Subtype without polymorphic base raises."""
        class RegularClass:
            pass
        
        with pytest.raises(ValueError, match="must inherit from a @polymorphic base"):
            @polymorphic.subtype("article")
            class Article(RegularClass):
                pass


# =============================================================================
# Test Decorator Preservation
# =============================================================================

class TestDecoratorPreservation:
    """Test that decorator preserves class behavior."""
    
    def test_preserves_class_name(self):
        """Class name is preserved."""
        @polymorphic("type")
        class Content:
            pass
        
        assert Content.__name__ == "Content"
    
    def test_preserves_methods(self):
        """Class methods are preserved."""
        @polymorphic("type")
        class Content:
            def get_title(self):
                return "Title"
        
        instance = Content()
        assert instance.get_title() == "Title"
    
    def test_preserves_class_attributes(self):
        """Class attributes are preserved."""
        @polymorphic("type")
        class Content:
            DEFAULT_TITLE = "Untitled"
        
        assert Content.DEFAULT_TITLE == "Untitled"
    
    def test_preserves_annotations(self):
        """Annotations are preserved."""
        @polymorphic("type")
        class Content:
            title: str
            body: str
        
        assert "title" in Content.__annotations__
        assert "body" in Content.__annotations__
    
    def test_preserves_docstring(self):
        """Docstring is preserved."""
        @polymorphic("type")
        class Content:
            """Content class docstring."""
            pass
        
        assert Content.__doc__ == "Content class docstring."


# =============================================================================
# Test Multiple Decorators
# =============================================================================

class TestMultipleDecorators:
    """Test multiple @polymorphic hierarchies."""
    
    def test_independent_hierarchies(self):
        """Multiple hierarchies are independent."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic("type")
        class Vehicle:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        @polymorphic.subtype("car")
        class Car(Vehicle):
            pass
        
        registry = get_polymorphic_registry()
        
        assert registry.get_class(Content, "article") == Article
        assert registry.get_class(Content, "car") is None
        
        assert registry.get_class(Vehicle, "car") == Car
        assert registry.get_class(Vehicle, "article") is None
    
    def test_multiple_subtypes(self):
        """Multiple subtypes from same base."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        @polymorphic.subtype("video")
        class Video(Content):
            pass
        
        @polymorphic.subtype("gallery")
        class Gallery(Content):
            pass
        
        registry = get_polymorphic_registry()
        subtypes = registry.get_all_subtypes(Content)
        
        assert len(subtypes) == 3
        assert Article in subtypes
        assert Video in subtypes
        assert Gallery in subtypes

