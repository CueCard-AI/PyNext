"""
Test Phase 7.7: Polymorphic Query Extensions.

Tests the query mixin and helper functions.
"""

import pytest
from typing import Optional, Union
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    generic_fk,
    PolymorphicQueryMixin,
    PolymorphicQueryBuilder,
    polymorphic_query,
    instantiate_polymorphic,
    reset_polymorphic_registry,
    get_strategy,
)


# =============================================================================
# Mock Models
# =============================================================================

class MockArticle:
    __tablename__ = "articles"
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockVideo:
    __tablename__ = "videos"
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


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
    """Create content hierarchy."""
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
    
    return Content, Article, Video


@pytest.fixture
def comment_with_gfk():
    """Create comment with generic FK."""
    class Comment:
        content: str
        target: Union[MockArticle, MockVideo] = generic_fk()
        
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    return Comment


# =============================================================================
# Test PolymorphicQueryMixin
# =============================================================================

class TestPolymorphicQueryMixin:
    """Test the query mixin."""
    
    def test_without_polymorphism(self, content_hierarchy):
        """without_polymorphism() disables type resolution."""
        Content, Article, Video = content_hierarchy
        
        class TestQuery(PolymorphicQueryMixin):
            _model_class = Content
        
        query = TestQuery()
        assert query._use_polymorphism is True
        
        query.without_polymorphism()
        assert query._use_polymorphism is False
    
    def test_with_polymorphism(self, content_hierarchy):
        """with_polymorphism() enables type resolution."""
        Content, Article, Video = content_hierarchy
        
        class TestQuery(PolymorphicQueryMixin):
            _model_class = Content
        
        query = TestQuery()
        query._use_polymorphism = False
        
        query.with_polymorphism()
        assert query._use_polymorphism is True
    
    def test_chaining(self, content_hierarchy):
        """Methods return self for chaining."""
        Content, Article, Video = content_hierarchy
        
        class TestQuery(PolymorphicQueryMixin):
            _model_class = Content
        
        query = TestQuery()
        result = query.without_polymorphism()
        
        assert result is query


# =============================================================================
# Test where_target_type
# =============================================================================

class TestWhereTargetType:
    """Test where_target_type method."""
    
    def test_adds_type_filter(self, comment_with_gfk):
        """where_target_type adds filter."""
        Comment = comment_with_gfk
        
        class TestQuery(PolymorphicQueryMixin):
            _model_class = Comment
            _conditions = {}
            
            def where(self, **kwargs):
                self._conditions.update(kwargs)
                return self
        
        query = TestQuery()
        query.where_target_type(MockArticle)
        
        assert query._conditions.get("target_type") == "articles"
    
    def test_custom_field_name(self, comment_with_gfk):
        """Custom field name."""
        # Create class with different field name
        class Comment2:
            content: str
            parent: Union[MockArticle, MockVideo] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        class TestQuery(PolymorphicQueryMixin):
            _model_class = Comment2
            _conditions = {}
            
            def where(self, **kwargs):
                self._conditions.update(kwargs)
                return self
        
        query = TestQuery()
        query.where_target_type(MockVideo, field_name="parent")
        
        assert query._conditions.get("parent_type") == "videos"
    
    def test_invalid_field_raises(self, content_hierarchy):
        """Invalid field name raises ValueError."""
        Content, Article, Video = content_hierarchy
        
        class TestQuery(PolymorphicQueryMixin):
            _model_class = Content
            
            def where(self, **kwargs):
                return self
        
        query = TestQuery()
        
        with pytest.raises(ValueError, match="not a generic foreign key"):
            query.where_target_type(MockArticle, field_name="nonexistent")


# =============================================================================
# Test where_target
# =============================================================================

class TestWhereTarget:
    """Test where_target method."""
    
    def test_adds_type_and_id_filter(self, comment_with_gfk):
        """where_target adds both type and ID filters."""
        Comment = comment_with_gfk
        
        class TestQuery(PolymorphicQueryMixin):
            _model_class = Comment
            _conditions = {}
            
            def where(self, **kwargs):
                self._conditions.update(kwargs)
                return self
        
        article = MockArticle(id=5, title="Test")
        
        query = TestQuery()
        query.where_target(article)
        
        assert query._conditions.get("target_type") == "articles"
        assert query._conditions.get("target_id") == 5


# =============================================================================
# Test _instantiate_polymorphic
# =============================================================================

class TestInstantiatePolymorphic:
    """Test _instantiate_polymorphic method."""
    
    def test_with_polymorphism(self, content_hierarchy):
        """Instantiate with polymorphism enabled."""
        Content, Article, Video = content_hierarchy
        
        class TestQuery(PolymorphicQueryMixin):
            _model_class = Content
            _use_polymorphism = True
        
        query = TestQuery()
        row = {"id": 1, "title": "Test", "type": "article", "body": "X"}
        
        instance = query._instantiate_polymorphic(row)
        
        assert isinstance(instance, Article)
    
    def test_without_polymorphism(self, content_hierarchy):
        """Instantiate with polymorphism disabled."""
        Content, Article, Video = content_hierarchy
        
        class TestQuery(PolymorphicQueryMixin):
            _model_class = Content
            _use_polymorphism = False
        
        query = TestQuery()
        row = {"id": 1, "title": "Test", "type": "article", "body": "X"}
        
        instance = query._instantiate_polymorphic(row)
        
        assert type(instance) == Content


# =============================================================================
# Test PolymorphicQueryBuilder
# =============================================================================

class TestPolymorphicQueryBuilder:
    """Test the standalone query builder."""
    
    def test_create_builder(self, content_hierarchy):
        """Create a polymorphic query builder."""
        Content, Article, Video = content_hierarchy
        
        builder = PolymorphicQueryBuilder(Content)
        
        assert builder._model_class == Content
        assert builder._use_polymorphism is True
    
    def test_where_chaining(self, content_hierarchy):
        """where() method chains."""
        Content, Article, Video = content_hierarchy
        
        builder = PolymorphicQueryBuilder(Content)
        result = builder.where(title="Test")
        
        assert result is builder
    
    def test_limit_chaining(self, content_hierarchy):
        """limit() method chains."""
        Content, Article, Video = content_hierarchy
        
        builder = PolymorphicQueryBuilder(Content)
        result = builder.limit(10)
        
        assert result is builder
        assert builder._limit_value == 10
    
    def test_offset_chaining(self, content_hierarchy):
        """offset() method chains."""
        Content, Article, Video = content_hierarchy
        
        builder = PolymorphicQueryBuilder(Content)
        result = builder.offset(20)
        
        assert result is builder
        assert builder._offset_value == 20
    
    def test_order_by_asc(self, content_hierarchy):
        """order_by() ascending."""
        Content, Article, Video = content_hierarchy
        
        builder = PolymorphicQueryBuilder(Content)
        builder.order_by("title")
        
        assert builder._order_by == "title ASC"
    
    def test_order_by_desc(self, content_hierarchy):
        """order_by() descending."""
        Content, Article, Video = content_hierarchy
        
        builder = PolymorphicQueryBuilder(Content)
        builder.order_by("created_at", desc=True)
        
        assert builder._order_by == "created_at DESC"


# =============================================================================
# Test polymorphic_query Helper
# =============================================================================

class TestPolymorphicQueryHelper:
    """Test polymorphic_query() helper function."""
    
    def test_creates_builder(self, content_hierarchy):
        """polymorphic_query() creates a builder."""
        Content, Article, Video = content_hierarchy
        
        builder = polymorphic_query(Content)
        
        assert isinstance(builder, PolymorphicQueryBuilder)
        assert builder._model_class == Content


# =============================================================================
# Test instantiate_polymorphic Function
# =============================================================================

class TestInstantiatePolymorphicFunction:
    """Test the instantiate_polymorphic function."""
    
    def test_with_polymorphism(self, content_hierarchy):
        """Use polymorphism by default."""
        Content, Article, Video = content_hierarchy
        
        row = {"id": 1, "title": "Test", "type": "video", "url": "http://x.com"}
        instance = instantiate_polymorphic(Content, row)
        
        assert isinstance(instance, Video)
    
    def test_without_polymorphism(self, content_hierarchy):
        """Disable polymorphism."""
        Content, Article, Video = content_hierarchy
        
        row = {"id": 1, "title": "Test", "type": "video", "url": "http://x.com"}
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

