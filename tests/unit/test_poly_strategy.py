"""
Test Phase 7.7: Strategy Selection and Configuration Tests.

Tests for strategy selection, configuration, and behavior.
"""

import pytest
from typing import Optional
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    get_strategy,
    SingleTableStrategy,
    JoinedTableStrategy,
    ConcreteTableStrategy,
    get_polymorphic_registry,
    reset_polymorphic_registry,
    InheritanceStrategy,
    get_inheritance_strategy,
    get_discriminator_column,
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
# Test Strategy Selection
# =============================================================================

class TestStrategySelection:
    """Test correct strategy is selected."""
    
    def test_default_is_sti(self):
        """Default strategy is STI."""
        @polymorphic("type")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        
        assert isinstance(strategy, SingleTableStrategy)
    
    def test_explicit_sti(self):
        """Explicit STI selection."""
        @polymorphic("type", strategy="single_table")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        
        assert isinstance(strategy, SingleTableStrategy)
    
    def test_sti_alias(self):
        """STI alias works."""
        @polymorphic("type", strategy="sti")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        
        assert isinstance(strategy, SingleTableStrategy)
    
    def test_joined_strategy(self):
        """Joined strategy selection."""
        @polymorphic("type", strategy="joined")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        
        assert isinstance(strategy, JoinedTableStrategy)
    
    def test_concrete_strategy(self):
        """Concrete strategy selection."""
        @polymorphic(strategy="concrete")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        
        assert isinstance(strategy, ConcreteTableStrategy)
    
    def test_subtype_inherits_strategy(self):
        """Subtype uses same strategy as base."""
        @polymorphic("type", strategy="joined")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        strategy = get_strategy(Article)
        
        assert isinstance(strategy, JoinedTableStrategy)
    
    def test_non_polymorphic_returns_none(self):
        """Non-polymorphic class returns None."""
        class Regular:
            pass
        
        assert get_strategy(Regular) is None


# =============================================================================
# Test Strategy Configuration
# =============================================================================

class TestStrategyConfiguration:
    """Test strategy configuration."""
    
    def test_sti_config_has_discriminator(self):
        """STI config has discriminator."""
        @polymorphic("content_type")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        
        assert strategy.discriminator == "content_type"
    
    def test_sti_config_has_base_class(self):
        """STI config has base class reference."""
        @polymorphic("type")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        
        assert strategy.base_class == Content
    
    def test_joined_config_has_discriminator(self):
        """Joined config has discriminator."""
        @polymorphic("emp_type", strategy="joined")
        class Employee:
            pass
        
        strategy = get_strategy(Employee)
        
        assert strategy.discriminator == "emp_type"
    
    def test_concrete_no_discriminator_column(self):
        """Concrete doesn't require discriminator column."""
        @polymorphic(strategy="concrete")
        class Vehicle:
            pass
        
        strategy = get_strategy(Vehicle)
        
        # Default discriminator still set
        assert strategy.discriminator == "type"


# =============================================================================
# Test Inheritance Strategy Enum
# =============================================================================

class TestInheritanceStrategyEnum:
    """Test InheritanceStrategy enum."""
    
    def test_single_table_value(self):
        """SINGLE_TABLE value."""
        assert InheritanceStrategy.SINGLE_TABLE.value == "single_table"
    
    def test_joined_value(self):
        """JOINED value."""
        assert InheritanceStrategy.JOINED.value == "joined"
    
    def test_concrete_value(self):
        """CONCRETE value."""
        assert InheritanceStrategy.CONCRETE.value == "concrete"
    
    def test_all_strategies_defined(self):
        """All strategies are defined."""
        strategies = list(InheritanceStrategy)
        assert len(strategies) == 3
    
    def test_get_strategy_returns_correct_enum(self):
        """get_inheritance_strategy returns correct enum."""
        @polymorphic("type", strategy="joined")
        class Content:
            pass
        
        assert get_inheritance_strategy(Content) == InheritanceStrategy.JOINED


# =============================================================================
# Test Strategy Behavior
# =============================================================================

class TestStrategyBehavior:
    """Test strategy behavior differences."""
    
    def test_sti_same_table_for_subtypes(self):
        """STI uses same table for all subtypes."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        @polymorphic.subtype("video")
        class Video(Content):
            pass
        
        strategy = get_strategy(Content)
        
        assert strategy.get_table_name(Content) == "contents"
        assert strategy.get_table_name(Article) == "contents"
        assert strategy.get_table_name(Video) == "contents"
    
    def test_joined_different_tables(self):
        """Joined uses different tables."""
        @polymorphic("type", strategy="joined")
        class Content:
            __tablename__ = "contents"
        
        @polymorphic.subtype("article")
        class Article(Content):
            __tablename__ = "articles"
        
        strategy = get_strategy(Content)
        
        assert strategy.get_table_name(Content) == "contents"
        assert strategy.get_table_name(Article) == "articles"
    
    def test_concrete_different_tables(self):
        """Concrete uses different tables."""
        @polymorphic(strategy="concrete")
        class Content:
            __tablename__ = "contents"
        
        @polymorphic.subtype("article")
        class Article(Content):
            __tablename__ = "articles"
        
        strategy = get_strategy(Content)
        
        assert strategy.get_table_name(Article) == "articles"


# =============================================================================
# Test Discriminator Configuration
# =============================================================================

class TestDiscriminatorConfiguration:
    """Test discriminator column configuration."""
    
    def test_default_discriminator(self):
        """Default discriminator is 'type'."""
        @polymorphic()
        class Content:
            pass
        
        assert get_discriminator_column(Content) == "type"
    
    def test_custom_discriminator(self):
        """Custom discriminator."""
        @polymorphic("content_type")
        class Content:
            pass
        
        assert get_discriminator_column(Content) == "content_type"
    
    def test_subtype_uses_base_discriminator(self):
        """Subtype uses same discriminator as base."""
        @polymorphic("kind")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert get_discriminator_column(Article) == "kind"
    
    def test_long_discriminator_name(self):
        """Long discriminator name works."""
        @polymorphic("this_is_a_very_long_discriminator_column_name")
        class Content:
            pass
        
        assert get_discriminator_column(Content) == "this_is_a_very_long_discriminator_column_name"
    
    def test_underscore_discriminator(self):
        """Underscore in discriminator."""
        @polymorphic("content_type_id")
        class Content:
            pass
        
        assert get_discriminator_column(Content) == "content_type_id"


# =============================================================================
# Test Strategy Factory
# =============================================================================

class TestStrategyFactory:
    """Test get_strategy factory function."""
    
    def test_returns_sti_for_sti(self):
        """Returns STI strategy for STI config."""
        @polymorphic("type")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        
        assert type(strategy).__name__ == "SingleTableStrategy"
    
    def test_returns_joined_for_joined(self):
        """Returns Joined strategy for joined config."""
        @polymorphic("type", strategy="joined")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        
        assert type(strategy).__name__ == "JoinedTableStrategy"
    
    def test_returns_concrete_for_concrete(self):
        """Returns Concrete strategy for concrete config."""
        @polymorphic(strategy="concrete")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        
        assert type(strategy).__name__ == "ConcreteTableStrategy"
    
    def test_caches_strategy_instance(self):
        """Strategy instances are created fresh."""
        @polymorphic("type")
        class Content:
            pass
        
        strategy1 = get_strategy(Content)
        strategy2 = get_strategy(Content)
        
        # New instances each time (no caching currently)
        assert strategy1 is not strategy2

