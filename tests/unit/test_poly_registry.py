"""
Test Phase 7.7: Polymorphic Type Registry.

Tests the PolymorphicRegistry and related classes.
"""

import pytest
from typing import Optional
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    PolymorphicRegistry,
    PolymorphicConfig,
    InheritanceStrategy,
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
# Test PolymorphicConfig
# =============================================================================

class TestPolymorphicConfig:
    """Test PolymorphicConfig class."""
    
    def test_create_config(self):
        """Create a config."""
        class Content:
            pass
        
        config = PolymorphicConfig(
            base_class=Content,
            discriminator="type",
            strategy=InheritanceStrategy.SINGLE_TABLE,
        )
        
        assert config.base_class == Content
        assert config.discriminator == "type"
        assert config.strategy == InheritanceStrategy.SINGLE_TABLE
    
    def test_register_subtype(self):
        """Register a subtype."""
        class Content:
            pass
        
        class Article:
            pass
        
        config = PolymorphicConfig(base_class=Content, discriminator="type")
        config.register_subtype("article", Article)
        
        assert config.get_subtype("article") == Article
    
    def test_get_subtype_not_found(self):
        """get_subtype returns None for unknown."""
        class Content:
            pass
        
        config = PolymorphicConfig(base_class=Content, discriminator="type")
        
        assert config.get_subtype("unknown") is None
    
    def test_get_all_subtypes(self):
        """Get all registered subtypes."""
        class Content:
            pass
        
        class Article:
            pass
        
        class Video:
            pass
        
        config = PolymorphicConfig(base_class=Content, discriminator="type")
        config.register_subtype("article", Article)
        config.register_subtype("video", Video)
        
        subtypes = config.get_all_subtypes()
        
        assert len(subtypes) == 2
        assert Article in subtypes
        assert Video in subtypes
    
    def test_get_identity_for_class(self):
        """Get identity value for a class."""
        class Content:
            pass
        
        class Article:
            pass
        
        config = PolymorphicConfig(base_class=Content, discriminator="type")
        config.register_subtype("article", Article)
        
        assert config.get_identity_for_class(Article) == "article"
    
    def test_get_identity_for_unknown_class(self):
        """Get identity for unknown class returns None."""
        class Content:
            pass
        
        class Other:
            pass
        
        config = PolymorphicConfig(base_class=Content, discriminator="type")
        
        assert config.get_identity_for_class(Other) is None


# =============================================================================
# Test InheritanceStrategy Enum
# =============================================================================

class TestInheritanceStrategy:
    """Test the InheritanceStrategy enum."""
    
    def test_single_table_value(self):
        """SINGLE_TABLE has correct value."""
        assert InheritanceStrategy.SINGLE_TABLE.value == "single_table"
    
    def test_joined_value(self):
        """JOINED has correct value."""
        assert InheritanceStrategy.JOINED.value == "joined"
    
    def test_concrete_value(self):
        """CONCRETE has correct value."""
        assert InheritanceStrategy.CONCRETE.value == "concrete"
    
    def test_all_strategies(self):
        """All strategies are defined."""
        strategies = list(InheritanceStrategy)
        assert len(strategies) == 3


# =============================================================================
# Test PolymorphicRegistry Singleton
# =============================================================================

class TestRegistrySingleton:
    """Test registry singleton behavior."""
    
    def test_singleton(self):
        """Registry is a singleton."""
        registry1 = get_polymorphic_registry()
        registry2 = get_polymorphic_registry()
        
        assert registry1 is registry2
    
    def test_reset_creates_new(self):
        """Reset creates new registry."""
        registry1 = get_polymorphic_registry()
        reset_polymorphic_registry()
        registry2 = get_polymorphic_registry()
        
        # After reset, configs should be empty
        assert len(registry2._configs) == 0


# =============================================================================
# Test Registry Base Class Operations
# =============================================================================

class TestRegistryBaseOperations:
    """Test registry base class operations."""
    
    def test_register_base(self):
        """Register a base class."""
        class Content:
            pass
        
        registry = get_polymorphic_registry()
        config = registry.register_base(
            Content,
            discriminator="type",
            strategy=InheritanceStrategy.SINGLE_TABLE,
        )
        
        assert config is not None
        assert config.base_class == Content
    
    def test_register_base_with_identity(self):
        """Register base with its own identity."""
        class Content:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(
            Content,
            discriminator="type",
            identity="base_content",
        )
        
        assert registry.get_identity(Content) == "base_content"
    
    def test_get_config(self):
        """Get config for registered class."""
        class Content:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="type")
        
        config = registry.get_config(Content)
        
        assert config is not None
        assert config.discriminator == "type"
    
    def test_get_config_not_registered(self):
        """Get config for unregistered class returns None."""
        class NotRegistered:
            pass
        
        registry = get_polymorphic_registry()
        
        assert registry.get_config(NotRegistered) is None


# =============================================================================
# Test Registry Subtype Operations
# =============================================================================

class TestRegistrySubtypeOperations:
    """Test registry subtype operations."""
    
    def test_register_subtype(self):
        """Register a subtype."""
        class Content:
            pass
        
        class Article:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="type")
        registry.register_subtype(Content, "article", Article)
        
        assert registry.get_class(Content, "article") == Article
    
    def test_register_subtype_without_base_raises(self):
        """Register subtype without base raises error."""
        class Content:
            pass
        
        class Article:
            pass
        
        registry = get_polymorphic_registry()
        
        with pytest.raises(ValueError, match="not registered as polymorphic"):
            registry.register_subtype(Content, "article", Article)
    
    def test_get_class(self):
        """Get class by identity."""
        class Content:
            pass
        
        class Article:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="type")
        registry.register_subtype(Content, "article", Article)
        
        assert registry.get_class(Content, "article") == Article
    
    def test_get_class_not_found(self):
        """Get class for unknown identity returns None."""
        class Content:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="type")
        
        assert registry.get_class(Content, "unknown") is None
    
    def test_get_all_subtypes(self):
        """Get all subtypes for a base."""
        class Content:
            pass
        
        class Article:
            pass
        
        class Video:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="type")
        registry.register_subtype(Content, "article", Article)
        registry.register_subtype(Content, "video", Video)
        
        subtypes = registry.get_all_subtypes(Content)
        
        assert len(subtypes) == 2


# =============================================================================
# Test Registry Query Methods
# =============================================================================

class TestRegistryQueryMethods:
    """Test registry query methods."""
    
    def test_is_polymorphic(self):
        """is_polymorphic check."""
        class Content:
            pass
        
        class Regular:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="type")
        
        assert registry.is_polymorphic(Content) is True
        assert registry.is_polymorphic(Regular) is False
    
    def test_is_base_class(self):
        """is_base_class check."""
        class Content:
            pass
        
        class Article:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="type")
        registry.register_subtype(Content, "article", Article)
        
        assert registry.is_base_class(Content) is True
        assert registry.is_base_class(Article) is False
    
    def test_is_subtype(self):
        """is_subtype check."""
        class Content:
            pass
        
        class Article:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="type")
        registry.register_subtype(Content, "article", Article)
        
        assert registry.is_subtype(Content) is False
        assert registry.is_subtype(Article) is True
    
    def test_get_base_class(self):
        """get_base_class returns base for subtype."""
        class Content:
            pass
        
        class Article:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="type")
        registry.register_subtype(Content, "article", Article)
        
        assert registry.get_base_class(Article) == Content
        assert registry.get_base_class(Content) == Content
    
    def test_get_discriminator(self):
        """get_discriminator returns column name."""
        class Content:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="kind")
        
        assert registry.get_discriminator(Content) == "kind"
    
    def test_get_strategy(self):
        """get_strategy returns strategy enum."""
        class Content:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(
            Content,
            discriminator="type",
            strategy=InheritanceStrategy.JOINED,
        )
        
        assert registry.get_strategy(Content) == InheritanceStrategy.JOINED


# =============================================================================
# Test Registry Clear
# =============================================================================

class TestRegistryClear:
    """Test registry clear operation."""
    
    def test_clear(self):
        """Clear removes all registrations."""
        class Content:
            pass
        
        registry = get_polymorphic_registry()
        registry.register_base(Content, discriminator="type")
        
        assert registry.is_polymorphic(Content)
        
        registry.clear()
        
        assert not registry.is_polymorphic(Content)
    
    def test_clear_preserves_singleton(self):
        """Clear preserves the singleton."""
        registry = get_polymorphic_registry()
        registry.clear()
        
        registry2 = get_polymorphic_registry()
        assert registry is registry2

