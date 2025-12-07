"""
Test Phase 7.7: Generic Foreign Keys Advanced Tests.

Advanced tests for generic foreign key functionality.
"""

import pytest
from typing import Optional, Union, List
from datetime import datetime
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
# Mock Models
# =============================================================================

class MockPost:
    __tablename__ = "posts"
    
    def __init__(self, id: int, title: str):
        self.id = id
        self.title = title
    
    @classmethod
    async def get(cls, id: int):
        return cls(id=id, title=f"Post {id}")


class MockComment:
    __tablename__ = "comments"
    
    def __init__(self, id: int, content: str):
        self.id = id
        self.content = content
    
    @classmethod
    async def get(cls, id: int):
        return cls(id=id, content=f"Comment {id}")


class MockUser:
    __tablename__ = "users"
    
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
    
    @classmethod
    async def get(cls, id: int):
        return cls(id=id, name=f"User {id}")


class MockImage:
    __tablename__ = "images"
    
    def __init__(self, id: int, url: str):
        self.id = id
        self.url = url
    
    @classmethod
    async def get(cls, id: int):
        return cls(id=id, url=f"http://img/{id}")


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
# Test Multiple Generic FKs
# =============================================================================

class TestMultipleGenericFKs:
    """Test multiple generic FKs on one class."""
    
    def test_two_generic_fks(self):
        """Two generic FKs."""
        class Activity:
            actor: Union[MockUser, MockImage] = generic_fk()
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        configs = get_all_generic_fk_configs(Activity)
        assert len(configs) == 2
    
    def test_three_generic_fks(self):
        """Three generic FKs."""
        class Notification:
            actor: Union[MockUser, MockImage] = generic_fk()
            target: Union[MockPost, MockComment] = generic_fk()
            origin: Union[MockPost, MockUser] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        configs = get_all_generic_fk_configs(Notification)
        assert len(configs) == 3
    
    def test_independent_setting(self):
        """Set each FK independently."""
        class Activity:
            # Note: Union needs at least 2 types for proper type extraction
            actor: Union[MockUser, MockImage] = generic_fk()
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        user = MockUser(id=1, name="Alice")
        post = MockPost(id=5, title="Hello")
        
        activity = Activity()
        activity.actor = user
        activity.target = post
        
        assert activity.actor_type == "users"
        assert activity.actor_id == 1
        assert activity.target_type == "posts"
        assert activity.target_id == 5
    
    def test_independent_columns(self):
        """Each FK has own columns."""
        class Activity:
            actor: Union[MockUser, MockImage] = generic_fk()
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        assert "actor_type" in Activity.__annotations__
        assert "actor_id" in Activity.__annotations__
        assert "target_type" in Activity.__annotations__
        assert "target_id" in Activity.__annotations__


# =============================================================================
# Test Custom Column Names
# =============================================================================

class TestCustomColumnNames:
    """Test custom column names for generic FKs."""
    
    def test_custom_type_column(self):
        """Custom type column name."""
        class Comment:
            parent: Union[MockPost, MockComment] = generic_fk(
                type_column="parent_model"
            )
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        config = get_generic_fk_config(Comment, "parent")
        assert config.type_column == "parent_model"
    
    def test_custom_id_column(self):
        """Custom ID column name."""
        class Comment:
            parent: Union[MockPost, MockComment] = generic_fk(
                id_column="parent_pk"
            )
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        config = get_generic_fk_config(Comment, "parent")
        assert config.id_column == "parent_pk"
    
    def test_both_custom_columns(self):
        """Both custom column names."""
        class Comment:
            parent: Union[MockPost, MockComment] = generic_fk(
                type_column="parent_model",
                id_column="parent_pk"
            )
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        config = get_generic_fk_config(Comment, "parent")
        assert config.type_column == "parent_model"
        assert config.id_column == "parent_pk"
    
    def test_custom_columns_added_to_class(self):
        """Custom column names added to annotations."""
        class Comment:
            parent: Union[MockPost] = generic_fk(
                type_column="parent_model",
                id_column="parent_pk"
            )
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        assert "parent_model" in Comment.__annotations__
        assert "parent_pk" in Comment.__annotations__


# =============================================================================
# Test Async Loading
# =============================================================================

class TestAsyncLoading:
    """Test async loading of generic FK targets."""
    
    @pytest.mark.asyncio
    async def test_load_post(self):
        """Load Post target."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity(target_type="posts", target_id=1)
        
        target = await activity.target
        
        assert isinstance(target, MockPost)
        assert target.id == 1
    
    @pytest.mark.asyncio
    async def test_load_comment(self):
        """Load Comment target."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity(target_type="comments", target_id=5)
        
        target = await activity.target
        
        assert isinstance(target, MockComment)
        assert target.id == 5
    
    @pytest.mark.asyncio
    async def test_load_none_when_unset(self):
        """Load returns None when not set."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity()
        
        target = await activity.target
        
        assert target is None
    
    @pytest.mark.asyncio
    async def test_caching(self):
        """Loaded target is cached."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity(target_type="posts", target_id=1)
        
        loader = activity.target
        target1 = await loader
        target2 = await loader
        
        assert target1 is target2


# =============================================================================
# Test Type Validation
# =============================================================================

class TestTypeValidation:
    """Test type validation for generic FKs."""
    
    def test_valid_type_accepted(self):
        """Valid type is accepted."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        post = MockPost(id=1, title="Test")
        
        activity = Activity()
        activity.target = post  # Should not raise
        
        assert activity.target_type == "posts"
    
    def test_invalid_type_raises(self):
        """Invalid type raises TypeError."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        user = MockUser(id=1, name="Alice")
        
        activity = Activity()
        
        with pytest.raises(TypeError, match="Invalid target type"):
            activity.target = user
    
    def test_none_accepted(self):
        """None is accepted."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity(target_type="posts", target_id=1)
        activity.target = None
        
        assert activity.target_type is None
        assert activity.target_id is None


# =============================================================================
# Test Dict Setting
# =============================================================================

class TestDictSetting:
    """Test setting generic FK with dict."""
    
    def test_set_with_dict(self):
        """Set with type and id dict."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity()
        activity.target = {"type": "posts", "id": 42}
        
        assert activity.target_type == "posts"
        assert activity.target_id == 42
    
    def test_set_with_partial_dict(self):
        """Set with partial dict."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity()
        activity.target = {"type": "posts"}
        
        assert activity.target_type == "posts"
        assert activity.target_id is None


# =============================================================================
# Test Loader Properties
# =============================================================================

class TestLoaderProperties:
    """Test GenericFKLoader properties."""
    
    def test_target_type_property(self):
        """target_type property."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity(target_type="posts", target_id=1)
        
        assert activity.target.target_type == "posts"
    
    def test_target_id_property(self):
        """target_id property."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity(target_type="posts", target_id=42)
        
        assert activity.target.target_id == 42
    
    def test_is_set_true(self):
        """is_set True when set."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity(target_type="posts", target_id=1)
        
        assert activity.target.is_set is True
    
    def test_is_set_false_when_type_missing(self):
        """is_set False when type is None."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity(target_type=None, target_id=1)
        
        assert activity.target.is_set is False
    
    def test_is_set_false_when_id_missing(self):
        """is_set False when id is None."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity(target_type="posts", target_id=None)
        
        assert activity.target.is_set is False
    
    def test_is_set_false_when_unset(self):
        """is_set False when never set."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        activity = Activity()
        
        assert activity.target.is_set is False


# =============================================================================
# Test Config Type Resolution
# =============================================================================

class TestConfigTypeResolution:
    """Test GenericFKConfig type resolution."""
    
    def test_get_type_class_by_tablename(self):
        """Get class by tablename."""
        class Activity:
            target: Union[MockPost, MockComment, MockUser] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        config = get_generic_fk_config(Activity, "target")
        
        assert config.get_type_class("posts") == MockPost
        assert config.get_type_class("comments") == MockComment
        assert config.get_type_class("users") == MockUser
    
    def test_get_type_class_unknown(self):
        """Unknown type returns None."""
        class Activity:
            target: Union[MockPost, MockComment] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        config = get_generic_fk_config(Activity, "target")
        
        assert config.get_type_class("unknown") is None

