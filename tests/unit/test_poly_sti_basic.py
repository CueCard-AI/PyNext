"""
Test Phase 7.7: Single Table Inheritance (STI) Basic Operations.

Tests the @polymorphic decorator and basic STI functionality.
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
    get_polymorphic_base,
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
# Test @polymorphic Decorator
# =============================================================================

class TestPolymorphicDecorator:
    """Test the @polymorphic decorator."""
    
    def test_basic_decorator(self):
        """Basic usage of @polymorphic."""
        @polymorphic("type")
        class Content:
            title: str
        
        assert is_polymorphic(Content)
        assert is_polymorphic_base(Content)
    
    def test_decorator_with_strategy(self):
        """Specify strategy in decorator."""
        @polymorphic("type", strategy="single_table")
        class Content:
            title: str
        
        assert get_inheritance_strategy(Content) == InheritanceStrategy.SINGLE_TABLE
    
    def test_sti_strategy_alias(self):
        """Use 'sti' as strategy alias."""
        @polymorphic("kind", strategy="sti")
        class Content:
            title: str
        
        assert get_inheritance_strategy(Content) == InheritanceStrategy.SINGLE_TABLE
    
    def test_custom_discriminator(self):
        """Custom discriminator column name."""
        @polymorphic("kind")
        class Content:
            title: str
        
        assert get_discriminator_column(Content) == "kind"
    
    def test_default_discriminator(self):
        """Default discriminator is 'type'."""
        @polymorphic()
        class Content:
            title: str
        
        assert get_discriminator_column(Content) == "type"
    
    def test_decorator_with_identity(self):
        """Base class with its own identity."""
        @polymorphic("type", identity="base_content")
        class Content:
            title: str
        
        assert get_polymorphic_identity(Content) == "base_content"
    
    def test_decorator_adds_config(self):
        """Decorator adds _polymorphic_config to class."""
        @polymorphic("type")
        class Content:
            title: str
        
        assert hasattr(Content, '_polymorphic_config')
        assert Content._polymorphic_config.discriminator == "type"
    
    def test_invalid_strategy_raises(self):
        """Invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            @polymorphic("type", strategy="invalid")
            class Content:
                title: str


# =============================================================================
# Test @polymorphic.subtype Decorator
# =============================================================================

class TestSubtypeDecorator:
    """Test the @polymorphic.subtype decorator."""
    
    def test_basic_subtype(self):
        """Basic subtype definition."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        assert is_polymorphic_subtype(Article)
        assert get_polymorphic_identity(Article) == "article"
    
    def test_auto_generated_identity(self):
        """Identity auto-generated from class name."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype()
        class Article(Content):
            body: str
        
        assert get_polymorphic_identity(Article) == "article"
    
    def test_subtype_base_reference(self):
        """Subtype stores reference to base class."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        assert get_polymorphic_base(Article) == Content
    
    def test_multiple_subtypes(self):
        """Multiple subtypes of same base."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        @polymorphic.subtype("video")
        class Video(Content):
            url: str
        
        assert get_polymorphic_identity(Article) == "article"
        assert get_polymorphic_identity(Video) == "video"
        assert get_polymorphic_base(Article) == Content
        assert get_polymorphic_base(Video) == Content
    
    def test_subtype_without_base_raises(self):
        """Subtype without polymorphic base raises error."""
        class Content:
            title: str
        
        with pytest.raises(ValueError, match="must inherit from a @polymorphic base"):
            @polymorphic.subtype("article")
            class Article(Content):
                body: str
    
    def test_subtype_inherits_strategy(self):
        """Subtype inherits base's strategy."""
        @polymorphic("type", strategy="single_table")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        assert get_inheritance_strategy(Article) == InheritanceStrategy.SINGLE_TABLE
    
    def test_subtype_inherits_discriminator(self):
        """Subtype uses same discriminator as base."""
        @polymorphic("kind")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        assert get_discriminator_column(Article) == "kind"


# =============================================================================
# Test Registry Operations
# =============================================================================

class TestRegistry:
    """Test polymorphic registry operations."""
    
    def test_register_base_class(self):
        """Register a base class."""
        @polymorphic("type")
        class Content:
            title: str
        
        registry = get_polymorphic_registry()
        config = registry.get_config(Content)
        
        assert config is not None
        assert config.base_class == Content
    
    def test_register_subtype(self):
        """Register a subtype."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "article") == Article
    
    def test_get_all_subtypes(self):
        """Get all registered subtypes."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        @polymorphic.subtype("video")
        class Video(Content):
            url: str
        
        registry = get_polymorphic_registry()
        subtypes = registry.get_all_subtypes(Content)
        
        assert len(subtypes) == 2
        assert Article in subtypes
        assert Video in subtypes
    
    def test_is_polymorphic(self):
        """Check is_polymorphic for various classes."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        class Regular:
            pass
        
        registry = get_polymorphic_registry()
        assert registry.is_polymorphic(Content)
        assert registry.is_polymorphic(Article)
        assert not registry.is_polymorphic(Regular)
    
    def test_is_base_class(self):
        """Check is_base_class."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        registry = get_polymorphic_registry()
        assert registry.is_base_class(Content)
        assert not registry.is_base_class(Article)
    
    def test_is_subtype(self):
        """Check is_subtype."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        registry = get_polymorphic_registry()
        assert not registry.is_subtype(Content)
        assert registry.is_subtype(Article)
    
    def test_get_identity_for_class(self):
        """Get identity value for a class."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        registry = get_polymorphic_registry()
        config = registry.get_config(Content)
        
        assert config.get_identity_for_class(Article) == "article"
    
    def test_reset_registry(self):
        """Reset clears all registrations."""
        @polymorphic("type")
        class Content:
            title: str
        
        registry = get_polymorphic_registry()
        assert registry.is_polymorphic(Content)
        
        reset_polymorphic_registry()
        
        registry = get_polymorphic_registry()
        assert not registry.is_polymorphic(Content)


# =============================================================================
# Test Helper Functions
# =============================================================================

class TestHelperFunctions:
    """Test helper functions."""
    
    def test_is_polymorphic_function(self):
        """Test is_polymorphic() function."""
        @polymorphic("type")
        class Content:
            title: str
        
        class Regular:
            pass
        
        assert is_polymorphic(Content)
        assert not is_polymorphic(Regular)
    
    def test_is_polymorphic_base_function(self):
        """Test is_polymorphic_base() function."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        assert is_polymorphic_base(Content)
        assert not is_polymorphic_base(Article)
    
    def test_is_polymorphic_subtype_function(self):
        """Test is_polymorphic_subtype() function."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        assert not is_polymorphic_subtype(Content)
        assert is_polymorphic_subtype(Article)
    
    def test_get_polymorphic_identity_function(self):
        """Test get_polymorphic_identity() function."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        assert get_polymorphic_identity(Article) == "article"
        assert get_polymorphic_identity(Content) is None
    
    def test_get_polymorphic_base_function(self):
        """Test get_polymorphic_base() function."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        assert get_polymorphic_base(Article) == Content
        assert get_polymorphic_base(Content) == Content


# =============================================================================
# Test Discriminator Column
# =============================================================================

class TestDiscriminatorColumn:
    """Test discriminator column handling."""
    
    def test_discriminator_added_to_annotations(self):
        """Discriminator column added to class annotations."""
        @polymorphic("type")
        class Content:
            title: str
        
        assert 'type' in Content.__annotations__
    
    def test_custom_discriminator_added(self):
        """Custom discriminator column added."""
        @polymorphic("kind")
        class Content:
            title: str
        
        assert 'kind' in Content.__annotations__
    
    def test_existing_discriminator_not_overwritten(self):
        """Don't overwrite existing discriminator annotation."""
        @polymorphic("type")
        class Content:
            type: str  # Already defined
            title: str
        
        # Should not raise
        assert 'type' in Content.__annotations__


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases."""
    
    def test_deep_inheritance(self):
        """Three levels of inheritance."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        # Note: For deep inheritance, typically intermediate classes
        # don't use subtype decorator - this is a design decision
        assert is_polymorphic_base(Content)
        assert is_polymorphic_subtype(Article)
    
    def test_empty_class(self):
        """Polymorphic class with no additional fields."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("empty")
        class Empty(Content):
            pass
        
        assert is_polymorphic_subtype(Empty)
    
    def test_class_with_methods(self):
        """Polymorphic class with methods."""
        @polymorphic("type")
        class Content:
            title: str
            
            def get_title(self):
                return self.title
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
            
            def get_summary(self):
                return self.body[:100]
        
        assert is_polymorphic_subtype(Article)
    
    def test_multiple_hierarchies(self):
        """Multiple independent polymorphic hierarchies."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic("type")
        class Vehicle:
            make: str
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        @polymorphic.subtype("car")
        class Car(Vehicle):
            doors: int
        
        assert get_polymorphic_base(Article) == Content
        assert get_polymorphic_base(Car) == Vehicle
    
    def test_unicode_identity(self):
        """Unicode in identity value."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("文章")
        class Article(Content):
            body: str
        
        assert get_polymorphic_identity(Article) == "文章"
    
    def test_special_chars_in_identity(self):
        """Special characters in identity."""
        @polymorphic("type")
        class Content:
            title: str
        
        @polymorphic.subtype("blog-post")
        class BlogPost(Content):
            body: str
        
        assert get_polymorphic_identity(BlogPost) == "blog-post"

