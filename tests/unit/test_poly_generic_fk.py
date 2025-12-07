"""
Test Phase 7.7: Generic Foreign Keys.

Tests the Union-type generic foreign key implementation.
"""

import pytest
from typing import Optional, Union
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from pynext.db.polymorphic import (
    generic_fk,
    GenericForeignKey,
    GenericFKConfig,
    GenericFKLoader,
    get_generic_fk_config,
    get_all_generic_fk_configs,
    reset_polymorphic_registry,
)


# =============================================================================
# Mock Models for Testing
# =============================================================================

class MockArticle:
    """Mock Article model."""
    __tablename__ = "articles"
    
    def __init__(self, id: int, title: str):
        self.id = id
        self.title = title
    
    @classmethod
    async def get(cls, id: int):
        if id == 1:
            return cls(id=1, title="Test Article")
        return None


class MockVideo:
    """Mock Video model."""
    __tablename__ = "videos"
    
    def __init__(self, id: int, title: str, url: str = ""):
        self.id = id
        self.title = title
        self.url = url
    
    @classmethod
    async def get(cls, id: int):
        if id == 1:
            return cls(id=1, title="Test Video", url="http://example.com")
        return None


class MockPhoto:
    """Mock Photo model."""
    __tablename__ = "photos"
    
    def __init__(self, id: int, url: str):
        self.id = id
        self.url = url
    
    @classmethod
    async def get(cls, id: int):
        if id == 1:
            return cls(id=1, url="http://example.com/photo.jpg")
        return None


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
def comment_class():
    """Create a Comment class with generic FK."""
    class Comment:
        content: str
        author_id: int
        target: Union[MockArticle, MockVideo, MockPhoto] = generic_fk()
        
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    return Comment


# =============================================================================
# Test generic_fk() Factory
# =============================================================================

class TestGenericFKFactory:
    """Test the generic_fk() factory function."""
    
    def test_creates_descriptor(self):
        """generic_fk() creates a GenericForeignKey."""
        class Comment:
            target: Union[MockArticle, MockVideo] = generic_fk()
        
        # Accessing on class returns the descriptor
        assert isinstance(Comment.__dict__['target'], GenericForeignKey)
    
    def test_custom_column_names(self):
        """Custom column names."""
        class Comment:
            parent: Union[MockArticle, MockVideo] = generic_fk(
                type_column="parent_type",
                id_column="parent_id"
            )
        
        config = get_generic_fk_config(Comment, "parent")
        assert config.type_column == "parent_type"
        assert config.id_column == "parent_id"
    
    def test_default_column_names(self, comment_class):
        """Default column names based on field name."""
        config = get_generic_fk_config(comment_class, "target")
        
        assert config.type_column == "target_type"
        assert config.id_column == "target_id"


# =============================================================================
# Test GenericFKConfig
# =============================================================================

class TestGenericFKConfig:
    """Test GenericFKConfig."""
    
    def test_allowed_types(self, comment_class):
        """Config stores allowed types."""
        config = get_generic_fk_config(comment_class, "target")
        
        assert MockArticle in config.allowed_types
        assert MockVideo in config.allowed_types
        assert MockPhoto in config.allowed_types
    
    def test_validate_target_valid(self, comment_class):
        """Validate valid target types."""
        config = get_generic_fk_config(comment_class, "target")
        
        article = MockArticle(id=1, title="Test")
        assert config.validate_target(article) is True
    
    def test_validate_target_invalid(self, comment_class):
        """Validate invalid target types."""
        config = get_generic_fk_config(comment_class, "target")
        
        class Other:
            pass
        
        other = Other()
        assert config.validate_target(other) is False
    
    def test_validate_target_none(self, comment_class):
        """None is valid (nullable FK)."""
        config = get_generic_fk_config(comment_class, "target")
        assert config.validate_target(None) is True
    
    def test_get_type_name(self, comment_class):
        """Get type name from target."""
        config = get_generic_fk_config(comment_class, "target")
        
        article = MockArticle(id=1, title="Test")
        assert config.get_type_name(article) == "articles"
    
    def test_get_target_id(self, comment_class):
        """Get ID from target."""
        config = get_generic_fk_config(comment_class, "target")
        
        article = MockArticle(id=42, title="Test")
        assert config.get_target_id(article) == 42
    
    def test_get_type_class(self, comment_class):
        """Get class from type name."""
        config = get_generic_fk_config(comment_class, "target")
        
        assert config.get_type_class("articles") == MockArticle
        assert config.get_type_class("videos") == MockVideo


# =============================================================================
# Test Setting Generic FK
# =============================================================================

class TestSetGenericFK:
    """Test setting generic FK values."""
    
    def test_set_with_model_instance(self, comment_class):
        """Set generic FK with model instance."""
        comment = comment_class(content="Great!")
        article = MockArticle(id=5, title="Test")
        
        comment.target = article
        
        assert comment.target_type == "articles"
        assert comment.target_id == 5
    
    def test_set_with_none(self, comment_class):
        """Set generic FK to None."""
        comment = comment_class(content="Great!")
        article = MockArticle(id=5, title="Test")
        
        comment.target = article
        comment.target = None
        
        assert comment.target_type is None
        assert comment.target_id is None
    
    def test_set_with_dict(self, comment_class):
        """Set generic FK with dict."""
        comment = comment_class(content="Great!")
        
        comment.target = {"type": "articles", "id": 5}
        
        assert comment.target_type == "articles"
        assert comment.target_id == 5
    
    def test_set_invalid_type_raises(self, comment_class):
        """Setting invalid type raises TypeError."""
        comment = comment_class(content="Great!")
        
        class Other:
            id = 1
        
        with pytest.raises(TypeError, match="Invalid target type"):
            comment.target = Other()
    
    def test_set_video(self, comment_class):
        """Set generic FK to Video."""
        comment = comment_class(content="Great!")
        video = MockVideo(id=10, title="Test Video")
        
        comment.target = video
        
        assert comment.target_type == "videos"
        assert comment.target_id == 10


# =============================================================================
# Test Getting Generic FK (Sync)
# =============================================================================

class TestGetGenericFKSync:
    """Test getting generic FK values (sync operations)."""
    
    def test_get_returns_loader(self, comment_class):
        """Getting returns a loader."""
        comment = comment_class(content="Great!", target_type="articles", target_id=1)
        
        result = comment.target
        
        assert isinstance(result, GenericFKLoader)
    
    def test_loader_has_target_type(self, comment_class):
        """Loader has target_type property."""
        comment = comment_class(content="Great!", target_type="articles", target_id=1)
        
        loader = comment.target
        
        assert loader.target_type == "articles"
    
    def test_loader_has_target_id(self, comment_class):
        """Loader has target_id property."""
        comment = comment_class(content="Great!", target_type="articles", target_id=5)
        
        loader = comment.target
        
        assert loader.target_id == 5
    
    def test_loader_is_set(self, comment_class):
        """Loader.is_set property."""
        comment1 = comment_class(content="Great!", target_type="articles", target_id=1)
        comment2 = comment_class(content="Empty")
        
        assert comment1.target.is_set is True
        assert comment2.target.is_set is False


# =============================================================================
# Test Getting Generic FK (Async)
# =============================================================================

class TestGetGenericFKAsync:
    """Test loading generic FK targets asynchronously."""
    
    @pytest.mark.asyncio
    async def test_load_article(self, comment_class):
        """Load Article target."""
        comment = comment_class(content="Great!", target_type="articles", target_id=1)
        
        target = await comment.target
        
        assert isinstance(target, MockArticle)
        assert target.id == 1
    
    @pytest.mark.asyncio
    async def test_load_video(self, comment_class):
        """Load Video target."""
        comment = comment_class(content="Great!", target_type="videos", target_id=1)
        
        target = await comment.target
        
        assert isinstance(target, MockVideo)
        assert target.id == 1
    
    @pytest.mark.asyncio
    async def test_load_none_when_not_set(self, comment_class):
        """Load returns None when not set."""
        comment = comment_class(content="Empty")
        
        target = await comment.target
        
        assert target is None
    
    @pytest.mark.asyncio
    async def test_load_none_for_missing(self, comment_class):
        """Load returns None when target doesn't exist."""
        comment = comment_class(content="Great!", target_type="articles", target_id=999)
        
        target = await comment.target
        
        assert target is None
    
    @pytest.mark.asyncio
    async def test_load_caches_result(self, comment_class):
        """Load caches the result."""
        comment = comment_class(content="Great!", target_type="articles", target_id=1)
        
        loader = comment.target
        
        # Load twice
        target1 = await loader
        target2 = await loader
        
        # Same instance
        assert target1 is target2


# =============================================================================
# Test Column Generation
# =============================================================================

class TestColumnGeneration:
    """Test that columns are added to the class."""
    
    def test_columns_added_to_annotations(self, comment_class):
        """Type and ID columns added to annotations."""
        assert "target_type" in comment_class.__annotations__
        assert "target_id" in comment_class.__annotations__
    
    def test_columns_are_optional(self, comment_class):
        """Columns are Optional types."""
        # Should be Optional[str] and Optional[int]
        assert comment_class.__annotations__["target_type"] == Optional[str]
        assert comment_class.__annotations__["target_id"] == Optional[int]


# =============================================================================
# Test Multiple Generic FKs
# =============================================================================

class TestMultipleGenericFKs:
    """Test multiple generic FKs on one class."""
    
    def test_two_generic_fks(self):
        """Two generic FKs on one class."""
        class Reaction:
            target: Union[MockArticle, MockVideo] = generic_fk()
            author: Union[MockArticle, MockPhoto] = generic_fk()
        
        configs = get_all_generic_fk_configs(Reaction)
        
        assert "target" in configs
        assert "author" in configs
    
    def test_independent_configs(self):
        """Each FK has independent config."""
        class Reaction:
            target: Union[MockArticle, MockVideo] = generic_fk()
            author: Union[MockPhoto] = generic_fk()
        
        target_config = get_generic_fk_config(Reaction, "target")
        author_config = get_generic_fk_config(Reaction, "author")
        
        assert MockVideo in target_config.allowed_types
        assert MockVideo not in author_config.allowed_types


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestGenericFKEdgeCases:
    """Test edge cases."""
    
    def test_single_type_union(self):
        """Union with single type."""
        # Note: Union[X] where X is a single type collapses to just X
        # Python's typing behavior means we can't get types from Union[SingleType]
        # So we test with at least 2 types
        class Comment:
            target: Union[MockArticle, MockVideo] = generic_fk()
        
        config = get_generic_fk_config(Comment, "target")
        assert len(config.allowed_types) == 2
    
    def test_custom_table_name_attribute(self):
        """Class with _table_name attribute."""
        class CustomModel:
            _table_name = "custom_items"
            
            def __init__(self, id):
                self.id = id
        
        class Comment:
            target: Union[CustomModel] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        config = get_generic_fk_config(Comment, "target")
        custom = CustomModel(id=1)
        
        assert config.get_type_name(custom) == "custom_items"
    
    def test_fallback_table_name(self):
        """Fallback to lowercase class name."""
        class SomeModel:
            def __init__(self, id):
                self.id = id
        
        class Comment:
            target: Union[SomeModel] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        config = get_generic_fk_config(Comment, "target")
        some = SomeModel(id=1)
        
        assert config.get_type_name(some) == "somemodel"

