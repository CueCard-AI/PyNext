"""
Test Phase 7.7: Single Table Inheritance (STI) Queries.

Tests query generation and execution for STI models.
"""

import pytest
from typing import Optional, Dict, Any
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    get_strategy,
    SingleTableStrategy,
    get_polymorphic_registry,
    reset_polymorphic_registry,
    instantiate_polymorphic,
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


@pytest.fixture
def content_hierarchy():
    """Create a content hierarchy for testing."""
    @polymorphic("type")
    class Content:
        __tablename__ = "contents"
        id: int
        title: str
        type: str
        
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    @polymorphic.subtype("article")
    class Article(Content):
        body: str
    
    @polymorphic.subtype("video")
    class Video(Content):
        url: str
        duration: int
    
    return Content, Article, Video


# =============================================================================
# Test Strategy Selection
# =============================================================================

class TestStrategySelection:
    """Test strategy is correctly selected."""
    
    def test_sti_strategy_for_base(self, content_hierarchy):
        """STI strategy for base class."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        
        assert strategy is not None
        assert isinstance(strategy, SingleTableStrategy)
    
    def test_sti_strategy_for_subtype(self, content_hierarchy):
        """STI strategy for subtype."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Article)
        
        assert strategy is not None
        assert isinstance(strategy, SingleTableStrategy)
    
    def test_no_strategy_for_regular(self):
        """No strategy for non-polymorphic class."""
        class Regular:
            pass
        
        assert get_strategy(Regular) is None


# =============================================================================
# Test Table Name
# =============================================================================

class TestTableName:
    """Test table name resolution for STI."""
    
    def test_base_table_name(self, content_hierarchy):
        """Base class table name."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        
        assert strategy.get_table_name(Content) == "contents"
    
    def test_subtype_uses_base_table(self, content_hierarchy):
        """Subtype uses base class table (STI characteristic)."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Article)
        
        # STI: All types use the same table
        assert strategy.get_table_name(Article) == "contents"
    
    def test_fallback_table_name(self):
        """Fallback table name from class name."""
        @polymorphic("type")
        class MyModel:
            title: str
        
        strategy = get_strategy(MyModel)
        
        assert strategy.get_table_name(MyModel) == "mymodels"


# =============================================================================
# Test SELECT Query Generation
# =============================================================================

class TestSelectQuery:
    """Test SELECT query generation for STI."""
    
    def test_base_class_select_all(self, content_hierarchy):
        """SELECT all from base class."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        query, params = strategy.build_select_query(Content)
        
        assert "SELECT" in query
        assert "FROM contents" in query
        assert len(params) == 0  # No discriminator filter
    
    def test_subtype_select_with_filter(self, content_hierarchy):
        """SELECT subtype adds discriminator filter."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Article)
        query, params = strategy.build_select_query(Article)
        
        assert "SELECT" in query
        assert "FROM contents" in query
        assert "WHERE type = $1" in query
        assert params == ["article"]
    
    def test_select_specific_columns(self, content_hierarchy):
        """SELECT with specific columns."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        query, params = strategy.build_select_query(
            Content, 
            columns=["id", "title"]
        )
        
        assert "SELECT id, title" in query
    
    def test_video_subtype_filter(self, content_hierarchy):
        """Video subtype uses correct identity."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Video)
        query, params = strategy.build_select_query(Video)
        
        assert params == ["video"]


# =============================================================================
# Test INSERT Query Generation
# =============================================================================

class TestInsertQuery:
    """Test INSERT query generation for STI."""
    
    def test_base_insert_no_identity(self, content_hierarchy):
        """INSERT into base without identity."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        query, params = strategy.build_insert_query(
            Content,
            {"title": "Test", "id": 1}
        )
        
        assert "INSERT INTO contents" in query
        assert "RETURNING *" in query
    
    def test_subtype_insert_adds_identity(self, content_hierarchy):
        """INSERT subtype adds discriminator value."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Article)
        query, params = strategy.build_insert_query(
            Article,
            {"title": "My Article", "body": "Content here", "id": 1}
        )
        
        assert "INSERT INTO contents" in query
        assert "type" in query  # Discriminator column
        assert "article" in params  # Discriminator value
    
    def test_insert_preserves_data(self, content_hierarchy):
        """INSERT preserves all data fields."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Video)
        data = {"title": "My Video", "url": "http://example.com", "duration": 120}
        query, params = strategy.build_insert_query(Video, data)
        
        assert "title" in query
        assert "url" in query
        assert "duration" in query


# =============================================================================
# Test Instance Creation
# =============================================================================

class TestInstanceCreation:
    """Test creating instances from database rows."""
    
    def test_instantiate_article(self, content_hierarchy):
        """Instantiate Article from row."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": "Test", "type": "article", "body": "Content"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Article)
        assert instance.title == "Test"
        assert instance.body == "Content"
    
    def test_instantiate_video(self, content_hierarchy):
        """Instantiate Video from row."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": "Test", "type": "video", "url": "http://x.com", "duration": 60}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Video)
        assert instance.url == "http://x.com"
    
    def test_instantiate_unknown_type(self, content_hierarchy):
        """Unknown type falls back to base class."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": "Test", "type": "unknown"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Content)
        assert not isinstance(instance, Article)
        assert not isinstance(instance, Video)
    
    def test_instantiate_no_discriminator(self, content_hierarchy):
        """No discriminator value uses base class."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": "Test"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Content)
    
    def test_instantiate_with_target_class(self, content_hierarchy):
        """Force specific target class."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": "Test", "type": "article", "body": "X"}
        
        # Force Content class even though type says article
        instance = strategy.instantiate_from_row(row, target_class=Content)
        
        assert type(instance) == Content


# =============================================================================
# Test instantiate_polymorphic Function
# =============================================================================

class TestInstantiatePolymorphic:
    """Test the instantiate_polymorphic helper."""
    
    def test_with_polymorphism(self, content_hierarchy):
        """Instantiate with polymorphism enabled."""
        Content, Article, Video = content_hierarchy
        
        row = {"id": 1, "title": "Test", "type": "article", "body": "X"}
        instance = instantiate_polymorphic(Content, row, use_polymorphism=True)
        
        assert isinstance(instance, Article)
    
    def test_without_polymorphism(self, content_hierarchy):
        """Instantiate with polymorphism disabled."""
        Content, Article, Video = content_hierarchy
        
        row = {"id": 1, "title": "Test", "type": "article", "body": "X"}
        instance = instantiate_polymorphic(Content, row, use_polymorphism=False)
        
        assert type(instance) == Content
    
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
# Test Query with Multiple Subtypes
# =============================================================================

class TestMultipleSubtypes:
    """Test queries with multiple subtypes."""
    
    def test_each_subtype_has_correct_identity(self, content_hierarchy):
        """Each subtype generates correct identity filter."""
        Content, Article, Video = content_hierarchy
        
        article_strategy = get_strategy(Article)
        video_strategy = get_strategy(Video)
        
        _, article_params = article_strategy.build_select_query(Article)
        _, video_params = video_strategy.build_select_query(Video)
        
        assert article_params == ["article"]
        assert video_params == ["video"]
    
    def test_base_query_no_filter(self, content_hierarchy):
        """Base query returns all types."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        query, params = strategy.build_select_query(Content)
        
        # No WHERE clause for base
        assert "WHERE" not in query
        assert params == []


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases in STI queries."""
    
    def test_empty_data_insert(self, content_hierarchy):
        """Insert with minimal data."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Article)
        query, params = strategy.build_insert_query(Article, {"id": 1})
        
        assert "INSERT" in query
        assert "type" in query  # Discriminator added
    
    def test_null_values_in_row(self, content_hierarchy):
        """Handle null values in row."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": None, "type": "article", "body": None}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Article)
        assert instance.title is None
    
    def test_extra_columns_in_row(self, content_hierarchy):
        """Extra columns in row are passed to constructor."""
        Content, Article, Video = content_hierarchy
        
        strategy = get_strategy(Content)
        row = {"id": 1, "title": "Test", "type": "article", "body": "X", "extra": "data"}
        
        instance = strategy.instantiate_from_row(row)
        
        # Extra attribute should be set
        assert hasattr(instance, 'extra')
        assert instance.extra == "data"

