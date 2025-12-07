"""
Test Phase 7.7: Single Table Inheritance Advanced Tests.

Advanced STI tests for complex scenarios.
"""

import pytest
from typing import Optional, List
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    get_strategy,
    get_polymorphic_registry,
    reset_polymorphic_registry,
    instantiate_polymorphic,
    is_polymorphic,
    is_polymorphic_base,
    is_polymorphic_subtype,
    get_polymorphic_identity,
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
# Test Many Subtypes
# =============================================================================

class TestManySubtypes:
    """Test with many subtypes."""
    
    def test_ten_subtypes(self):
        """Ten subtypes from one base."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        subtypes = []
        for i in range(10):
            @polymorphic.subtype(f"type_{i}")
            class SubType(Content):
                pass
            SubType.__name__ = f"SubType{i}"
            subtypes.append(SubType)
        
        registry = get_polymorphic_registry()
        assert len(registry.get_all_subtypes(Content)) == 10
    
    def test_instantiate_each_subtype(self):
        """Instantiate each of multiple subtypes."""
        @polymorphic("type")
        class Event:
            __tablename__ = "events"
            id: int
            timestamp: datetime
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("click")
        class ClickEvent(Event):
            x: int
            y: int
        
        @polymorphic.subtype("scroll")
        class ScrollEvent(Event):
            position: int
        
        @polymorphic.subtype("keypress")
        class KeypressEvent(Event):
            key: str
        
        @polymorphic.subtype("submit")
        class SubmitEvent(Event):
            form_id: str
        
        @polymorphic.subtype("view")
        class ViewEvent(Event):
            page: str
        
        strategy = get_strategy(Event)
        
        rows = [
            {"id": 1, "type": "click", "x": 100, "y": 200, "timestamp": None},
            {"id": 2, "type": "scroll", "position": 500, "timestamp": None},
            {"id": 3, "type": "keypress", "key": "Enter", "timestamp": None},
            {"id": 4, "type": "submit", "form_id": "login", "timestamp": None},
            {"id": 5, "type": "view", "page": "/home", "timestamp": None},
        ]
        
        instances = [strategy.instantiate_from_row(row) for row in rows]
        
        assert isinstance(instances[0], ClickEvent)
        assert isinstance(instances[1], ScrollEvent)
        assert isinstance(instances[2], KeypressEvent)
        assert isinstance(instances[3], SubmitEvent)
        assert isinstance(instances[4], ViewEvent)


# =============================================================================
# Test Query Building
# =============================================================================

class TestSTIQueryBuilding:
    """Test STI query building."""
    
    def test_select_all_columns(self):
        """SELECT * for base class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        query, params = strategy.build_select_query(Content)
        
        assert "SELECT *" in query
        assert "FROM contents" in query
        assert params == []
    
    def test_select_specific_columns(self):
        """SELECT specific columns."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            body: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        query, params = strategy.build_select_query(
            Content,
            columns=["id", "title"]
        )
        
        assert "SELECT id, title" in query
    
    def test_subtype_query_filter(self):
        """Subtype query adds discriminator filter."""
        @polymorphic("kind")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("blog")
        class Blog(Content):
            pass
        
        strategy = get_strategy(Blog)
        query, params = strategy.build_select_query(Blog)
        
        assert "WHERE kind = $1" in query
        assert params == ["blog"]


# =============================================================================
# Test Insert Operations
# =============================================================================

class TestSTIInsert:
    """Test STI insert operations."""
    
    def test_base_insert(self):
        """Insert into base class."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Content)
        query, params = strategy.build_insert_query(
            Content,
            {"id": 1, "title": "Test"}
        )
        
        assert "INSERT INTO contents" in query
        assert "RETURNING *" in query
    
    def test_subtype_insert_adds_discriminator(self):
        """Subtype insert adds discriminator."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("post")
        class Post(Content):
            body: str
        
        strategy = get_strategy(Post)
        query, params = strategy.build_insert_query(
            Post,
            {"id": 1, "title": "Test", "body": "Content"}
        )
        
        assert "type" in query
        assert "post" in params
    
    def test_insert_all_fields(self):
        """Insert with all fields."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            created_at: datetime
            published: bool
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
            author_id: int
        
        strategy = get_strategy(Article)
        now = datetime.now()
        query, params = strategy.build_insert_query(
            Article,
            {
                "id": 1,
                "title": "My Article",
                "created_at": now,
                "published": True,
                "body": "Content here",
                "author_id": 42
            }
        )
        
        assert "title" in query
        assert "body" in query
        assert "author_id" in query


# =============================================================================
# Test Class Attributes
# =============================================================================

class TestClassAttributes:
    """Test attributes added to classes."""
    
    def test_base_has_polymorphic_config(self):
        """Base class has _polymorphic_config."""
        @polymorphic("type")
        class Content:
            pass
        
        assert hasattr(Content, '_polymorphic_config')
    
    def test_base_has_is_polymorphic_base(self):
        """Base class has _is_polymorphic_base."""
        @polymorphic("type")
        class Content:
            pass
        
        assert Content._is_polymorphic_base is True
    
    def test_subtype_has_identity(self):
        """Subtype has _polymorphic_identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert Article._polymorphic_identity == "article"
    
    def test_subtype_has_base_reference(self):
        """Subtype has _polymorphic_base."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert Article._polymorphic_base == Content
    
    def test_subtype_has_is_subtype_flag(self):
        """Subtype has _is_polymorphic_subtype."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert Article._is_polymorphic_subtype is True


# =============================================================================
# Test Discriminator Variations
# =============================================================================

class TestDiscriminatorVariations:
    """Test different discriminator configurations."""
    
    def test_custom_discriminator_name(self):
        """Custom discriminator column name."""
        @polymorphic("content_type")
        class Content:
            pass
        
        assert get_discriminator_column(Content) == "content_type"
    
    def test_discriminator_with_default(self):
        """Default discriminator name."""
        @polymorphic()
        class Content:
            pass
        
        assert get_discriminator_column(Content) == "type"
    
    def test_base_with_identity(self):
        """Base class with its own identity."""
        @polymorphic("type", identity="base")
        class Content:
            __tablename__ = "contents"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "base") == Content
    
    def test_long_discriminator_name(self):
        """Long discriminator column name."""
        @polymorphic("this_is_a_very_long_discriminator_column_name")
        class Content:
            pass
        
        assert get_discriminator_column(Content) == "this_is_a_very_long_discriminator_column_name"


# =============================================================================
# Test Strategy Aliases
# =============================================================================

class TestStrategyAliases:
    """Test strategy name aliases."""
    
    def test_single_table_explicit(self):
        """Explicit single_table strategy."""
        @polymorphic("type", strategy="single_table")
        class Content:
            pass
        
        assert get_strategy(Content) is not None
    
    def test_sti_alias(self):
        """STI alias for single_table."""
        @polymorphic("type", strategy="sti")
        class Content:
            pass
        
        strategy = get_strategy(Content)
        assert strategy is not None
    
    def test_default_is_single_table(self):
        """Default strategy is single_table."""
        @polymorphic("type")
        class Content:
            pass
        
        registry = get_polymorphic_registry()
        from pynext.db.polymorphic import InheritanceStrategy
        assert registry.get_strategy(Content) == InheritanceStrategy.SINGLE_TABLE


# =============================================================================
# Test Error Conditions
# =============================================================================

class TestErrorConditions:
    """Test error handling."""
    
    def test_invalid_strategy_raises(self):
        """Invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            @polymorphic("type", strategy="invalid_strategy")
            class Content:
                pass
    
    def test_subtype_without_base_raises(self):
        """Subtype without polymorphic base raises."""
        class NotPolymorphic:
            pass
        
        with pytest.raises(ValueError, match="must inherit from a @polymorphic base"):
            @polymorphic.subtype("article")
            class Article(NotPolymorphic):
                pass


# =============================================================================
# Test Helper Functions
# =============================================================================

class TestHelperFunctions:
    """Test helper functions."""
    
    def test_is_polymorphic_true_for_base(self):
        """is_polymorphic True for base."""
        @polymorphic("type")
        class Content:
            pass
        
        assert is_polymorphic(Content) is True
    
    def test_is_polymorphic_true_for_subtype(self):
        """is_polymorphic True for subtype."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert is_polymorphic(Article) is True
    
    def test_is_polymorphic_false_for_regular(self):
        """is_polymorphic False for regular class."""
        class Regular:
            pass
        
        assert is_polymorphic(Regular) is False
    
    def test_get_polymorphic_identity_for_subtype(self):
        """get_polymorphic_identity returns identity."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert get_polymorphic_identity(Article) == "article"
    
    def test_get_polymorphic_identity_none_for_base(self):
        """get_polymorphic_identity None for base without identity."""
        @polymorphic("type")
        class Content:
            pass
        
        assert get_polymorphic_identity(Content) is None

