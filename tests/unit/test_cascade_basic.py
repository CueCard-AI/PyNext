"""
Basic Cascade Tests.

Tests for the core cascade functionality including:
- OnDeleteAction enum
- CascadeOptions dataclass
- CascadeManager basic operations
- Simple cascade presets
"""

import pytest
from typing import List, Optional

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import (
    has_many,
    has_one,
    belongs_to,
    many_to_many,
)
from pynext.db.relationships.cascade import (
    OnDeleteAction,
    CascadeOptions,
    CascadeResult,
    CascadeError,
    ProtectedDeleteError,
    OrphanDeleteError,
    CascadeManager,
    get_cascade_manager,
    reset_cascade_manager,
    cascade_options,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clean_state():
    """Clean model registry and cascade manager before each test."""
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# OnDeleteAction Enum Tests (15 tests)
# =============================================================================

class TestOnDeleteAction:
    """Test OnDeleteAction enum."""
    
    def test_cascade_value(self):
        """Test CASCADE value."""
        assert OnDeleteAction.CASCADE.value == "cascade"
    
    def test_nullify_value(self):
        """Test NULLIFY value."""
        assert OnDeleteAction.NULLIFY.value == "nullify"
    
    def test_protect_value(self):
        """Test PROTECT value."""
        assert OnDeleteAction.PROTECT.value == "protect"
    
    def test_none_value(self):
        """Test NONE value."""
        assert OnDeleteAction.NONE.value == "none"
    
    def test_from_string_cascade(self):
        """Test from_string with cascade."""
        assert OnDeleteAction.from_string("cascade") == OnDeleteAction.CASCADE
    
    def test_from_string_nullify(self):
        """Test from_string with nullify."""
        assert OnDeleteAction.from_string("nullify") == OnDeleteAction.NULLIFY
    
    def test_from_string_protect(self):
        """Test from_string with protect."""
        assert OnDeleteAction.from_string("protect") == OnDeleteAction.PROTECT
    
    def test_from_string_none(self):
        """Test from_string with none."""
        assert OnDeleteAction.from_string("none") == OnDeleteAction.NONE
    
    def test_from_string_uppercase(self):
        """Test from_string handles uppercase."""
        assert OnDeleteAction.from_string("CASCADE") == OnDeleteAction.CASCADE
    
    def test_from_string_mixed_case(self):
        """Test from_string handles mixed case."""
        assert OnDeleteAction.from_string("Cascade") == OnDeleteAction.CASCADE
    
    def test_from_string_invalid(self):
        """Test from_string raises on invalid value."""
        with pytest.raises(ValueError) as exc_info:
            OnDeleteAction.from_string("invalid")
        assert "Invalid on_delete value" in str(exc_info.value)
    
    def test_enum_is_string(self):
        """Test enum values are strings."""
        assert isinstance(OnDeleteAction.CASCADE.value, str)
        assert isinstance(OnDeleteAction.NULLIFY.value, str)
    
    def test_enum_comparison(self):
        """Test enum comparison."""
        assert OnDeleteAction.CASCADE == OnDeleteAction.CASCADE
        assert OnDeleteAction.CASCADE != OnDeleteAction.NULLIFY
    
    def test_enum_string_comparison(self):
        """Test enum can be compared to strings."""
        assert OnDeleteAction.CASCADE == "cascade"
        assert OnDeleteAction.NULLIFY == "nullify"
    
    def test_all_values_unique(self):
        """Test all enum values are unique."""
        values = [a.value for a in OnDeleteAction]
        assert len(values) == len(set(values))


# =============================================================================
# CascadeOptions Tests (25 tests)
# =============================================================================

class TestCascadeOptions:
    """Test CascadeOptions dataclass."""
    
    def test_default_values(self):
        """Test default values are all False."""
        opts = CascadeOptions()
        assert opts.on_save is False
        assert opts.on_delete is False
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_on_save_true(self):
        """Test setting on_save to True."""
        opts = CascadeOptions(on_save=True)
        assert opts.on_save is True
        assert opts.on_delete is False
    
    def test_on_delete_true(self):
        """Test setting on_delete to True."""
        opts = CascadeOptions(on_delete=True)
        assert opts.on_delete is True
        assert opts.on_save is False
    
    def test_on_orphan_true(self):
        """Test setting on_orphan to True."""
        opts = CascadeOptions(on_orphan=True)
        assert opts.on_orphan is True
    
    def test_on_merge_true(self):
        """Test setting on_merge to True."""
        opts = CascadeOptions(on_merge=True)
        assert opts.on_merge is True
    
    def test_multiple_options(self):
        """Test setting multiple options."""
        opts = CascadeOptions(on_save=True, on_delete=True)
        assert opts.on_save is True
        assert opts.on_delete is True
        assert opts.on_orphan is False


class TestCascadeOptionsPresets:
    """Test CascadeOptions factory methods."""
    
    def test_all_preset(self):
        """Test CascadeOptions.all() preset."""
        opts = CascadeOptions.all()
        assert opts.on_save is True
        assert opts.on_delete is True
        assert opts.on_orphan is True
        assert opts.on_merge is True
    
    def test_delete_only_preset(self):
        """Test CascadeOptions.delete_only() preset."""
        opts = CascadeOptions.delete_only()
        assert opts.on_delete is True
        assert opts.on_save is False
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_delete_orphan_preset(self):
        """Test CascadeOptions.delete_orphan() preset."""
        opts = CascadeOptions.delete_orphan()
        assert opts.on_delete is True
        assert opts.on_orphan is True
        assert opts.on_save is False
    
    def test_save_only_preset(self):
        """Test CascadeOptions.save_only() preset."""
        opts = CascadeOptions.save_only()
        assert opts.on_save is True
        assert opts.on_delete is False
    
    def test_none_preset(self):
        """Test CascadeOptions.none() preset."""
        opts = CascadeOptions.none()
        assert opts.on_save is False
        assert opts.on_delete is False
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_from_on_delete_cascade(self):
        """Test from_on_delete with cascade."""
        opts = CascadeOptions.from_on_delete("cascade")
        assert opts.on_delete is True
    
    def test_from_on_delete_nullify(self):
        """Test from_on_delete with nullify."""
        opts = CascadeOptions.from_on_delete("nullify")
        # Nullify doesn't set on_delete - it's handled differently
        assert opts.on_delete is False
    
    def test_from_on_delete_protect(self):
        """Test from_on_delete with protect."""
        opts = CascadeOptions.from_on_delete("protect")
        # Protect doesn't set on_delete - it's a check
        assert opts.on_delete is False
    
    def test_from_on_delete_none(self):
        """Test from_on_delete with none."""
        opts = CascadeOptions.from_on_delete("none")
        assert opts.on_delete is False


class TestCascadeOptionsUtilities:
    """Test CascadeOptions utility methods."""
    
    def test_has_any_false(self):
        """Test has_any when all False."""
        opts = CascadeOptions()
        assert opts.has_any() is False
    
    def test_has_any_true(self):
        """Test has_any when any True."""
        opts = CascadeOptions(on_save=True)
        assert opts.has_any() is True
    
    def test_to_dict(self):
        """Test to_dict method."""
        opts = CascadeOptions(on_save=True, on_delete=True)
        d = opts.to_dict()
        assert d == {
            "on_save": True,
            "on_delete": True,
            "on_orphan": False,
            "on_merge": False,
        }
    
    def test_str_none(self):
        """Test __str__ with no options."""
        opts = CascadeOptions()
        assert str(opts) == "CascadeOptions(none)"
    
    def test_str_single(self):
        """Test __str__ with single option."""
        opts = CascadeOptions(on_delete=True)
        assert str(opts) == "CascadeOptions(delete)"
    
    def test_str_multiple(self):
        """Test __str__ with multiple options."""
        opts = CascadeOptions(on_save=True, on_delete=True)
        assert "save" in str(opts)
        assert "delete" in str(opts)


# =============================================================================
# CascadeResult Tests (15 tests)
# =============================================================================

class TestCascadeResult:
    """Test CascadeResult dataclass."""
    
    def test_empty_result(self):
        """Test empty result."""
        result = CascadeResult()
        assert result.deleted_count == 0
        assert result.saved_count == 0
        assert result.nullified_count == 0
        assert result.has_errors is False
    
    def test_deleted_count(self):
        """Test deleted count."""
        result = CascadeResult()
        result.deleted.append("item1")
        result.deleted.append("item2")
        assert result.deleted_count == 2
    
    def test_saved_count(self):
        """Test saved count."""
        result = CascadeResult()
        result.saved.append("item1")
        assert result.saved_count == 1
    
    def test_nullified_count(self):
        """Test nullified count."""
        result = CascadeResult()
        result.nullified.append(("item", "field"))
        assert result.nullified_count == 1
    
    def test_has_errors_false(self):
        """Test has_errors when no errors."""
        result = CascadeResult()
        assert result.has_errors is False
    
    def test_has_errors_true(self):
        """Test has_errors when errors exist."""
        result = CascadeResult()
        result.errors.append(("item", Exception("error")))
        assert result.has_errors is True
    
    def test_total_affected(self):
        """Test total_affected count."""
        result = CascadeResult()
        result.deleted.extend(["a", "b"])
        result.saved.append("c")
        result.nullified.append(("d", "field"))
        assert result.total_affected == 4
    
    def test_merge(self):
        """Test merging results."""
        r1 = CascadeResult()
        r1.deleted.append("a")
        
        r2 = CascadeResult()
        r2.deleted.append("b")
        r2.saved.append("c")
        
        r1.merge(r2)
        
        assert r1.deleted_count == 2
        assert r1.saved_count == 1
    
    def test_str_empty(self):
        """Test __str__ with empty result."""
        result = CascadeResult()
        assert str(result) == "CascadeResult(no changes)"
    
    def test_str_with_changes(self):
        """Test __str__ with changes."""
        result = CascadeResult()
        result.deleted.append("item")
        assert "1 deleted" in str(result)


# =============================================================================
# CascadeError Tests (10 tests)
# =============================================================================

class TestCascadeErrors:
    """Test cascade error classes."""
    
    def test_cascade_error_base(self):
        """Test CascadeError is an Exception."""
        error = CascadeError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"
    
    def test_protected_delete_error(self):
        """Test ProtectedDeleteError."""
        class MockUser:
            id = 1
            __class__.__name__ = "User"
        
        error = ProtectedDeleteError(
            instance=MockUser(),
            relationship="posts",
            related_count=5,
        )
        
        assert error.relationship == "posts"
        assert error.related_count == 5
        assert "User" in str(error)
        assert "5" in str(error)
        assert "posts" in str(error)
    
    def test_orphan_delete_error(self):
        """Test OrphanDeleteError."""
        error = OrphanDeleteError("Failed to delete orphan")
        assert isinstance(error, CascadeError)


# =============================================================================
# CascadeManager Basic Tests (20 tests)
# =============================================================================

class TestCascadeManager:
    """Test CascadeManager basic functionality."""
    
    def test_init(self):
        """Test manager initialization."""
        manager = CascadeManager()
        assert manager._processing == set()
    
    def test_get_cascade_manager(self):
        """Test global manager getter."""
        manager = get_cascade_manager()
        assert isinstance(manager, CascadeManager)
    
    def test_get_cascade_manager_singleton(self):
        """Test manager is singleton."""
        m1 = get_cascade_manager()
        m2 = get_cascade_manager()
        assert m1 is m2
    
    def test_reset_cascade_manager(self):
        """Test manager reset."""
        m1 = get_cascade_manager()
        reset_cascade_manager()
        m2 = get_cascade_manager()
        assert m1 is not m2


# =============================================================================
# cascade_options Function Tests (5 tests)
# =============================================================================

class TestCascadeOptionsFunction:
    """Test the cascade_options convenience function."""
    
    def test_cascade_options_default(self):
        """Test cascade_options with defaults."""
        opts = cascade_options()
        assert opts.on_save is False
        assert opts.on_delete is False
    
    def test_cascade_options_on_delete(self):
        """Test cascade_options with on_delete."""
        opts = cascade_options(on_delete=True)
        assert opts.on_delete is True
    
    def test_cascade_options_on_save(self):
        """Test cascade_options with on_save."""
        opts = cascade_options(on_save=True)
        assert opts.on_save is True
    
    def test_cascade_options_on_orphan(self):
        """Test cascade_options with on_orphan."""
        opts = cascade_options(on_orphan=True)
        assert opts.on_orphan is True
    
    def test_cascade_options_combined(self):
        """Test cascade_options with multiple options."""
        opts = cascade_options(on_delete=True, on_orphan=True)
        assert opts.on_delete is True
        assert opts.on_orphan is True


# =============================================================================
# Relationship Descriptor with Cascade Tests (15 tests)
# =============================================================================

class TestRelationshipCascadeParams:
    """Test cascade parameters on relationship descriptors."""
    
    def test_has_many_on_delete_default(self, clean_state):
        """Test has_many default on_delete is none."""
        class Post(Table):
            title: str = ""
            author_id: int = 0
        
        class User(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "author_id")
        
        descriptor = User.__dict__["posts"]
        assert descriptor.on_delete == "none"
    
    def test_has_many_on_delete_cascade(self, clean_state):
        """Test has_many with on_delete=cascade."""
        class Post(Table):
            title: str = ""
            author_id: int = 0
        
        class User(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "author_id", on_delete="cascade")
        
        descriptor = User.__dict__["posts"]
        assert descriptor.on_delete == "cascade"
    
    def test_has_many_on_delete_nullify(self, clean_state):
        """Test has_many with on_delete=nullify."""
        class Comment(Table):
            text: str = ""
            author_id: int = 0
        
        class User(Table):
            name: str = ""
            comments: List[Comment] = has_many(Comment, "author_id", on_delete="nullify")
        
        descriptor = User.__dict__["comments"]
        assert descriptor.on_delete == "nullify"
    
    def test_has_many_on_delete_protect(self, clean_state):
        """Test has_many with on_delete=protect."""
        class Order(Table):
            total: float = 0.0
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            orders: List[Order] = has_many(Order, "user_id", on_delete="protect")
        
        descriptor = User.__dict__["orders"]
        assert descriptor.on_delete == "protect"
    
    def test_has_many_cascade_options(self, clean_state):
        """Test has_many with CascadeOptions."""
        class Log(Table):
            message: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            logs: List[Log] = has_many(Log, "user_id", cascade=CascadeOptions.all())
        
        descriptor = User.__dict__["logs"]
        assert descriptor.cascade.on_save is True
        assert descriptor.cascade.on_delete is True
        assert descriptor.cascade.on_orphan is True
    
    def test_has_one_on_delete_cascade(self, clean_state):
        """Test has_one with on_delete=cascade."""
        class Profile(Table):
            bio: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            profile: Profile = has_one(Profile, "user_id", on_delete="cascade")
        
        descriptor = User.__dict__["profile"]
        assert descriptor.on_delete == "cascade"
    
    def test_has_one_cascade_options(self, clean_state):
        """Test has_one with CascadeOptions."""
        class Settings(Table):
            theme: str = "light"
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            settings: Settings = has_one(
                Settings, "user_id", 
                cascade=CascadeOptions(on_delete=True, on_save=True)
            )
        
        descriptor = User.__dict__["settings"]
        assert descriptor.cascade.on_delete is True
        assert descriptor.cascade.on_save is True
    
    def test_many_to_many_on_delete_cascade(self, clean_state):
        """Test many_to_many with on_delete=cascade."""
        class Tag(Table):
            name: str = ""
        
        class Post(Table):
            title: str = ""
            tags: List[Tag] = many_to_many(Tag, on_delete="cascade")
        
        descriptor = Post.__dict__["tags"]
        assert descriptor.on_delete == "cascade"
    
    def test_combined_on_delete_and_backref(self, clean_state):
        """Test on_delete combined with backref."""
        class Post(Table):
            title: str = ""
            author_id: int = 0
        
        class User(Table):
            name: str = ""
            posts: List[Post] = has_many(
                Post, "author_id", 
                backref="author",
                on_delete="cascade"
            )
        
        descriptor = User.__dict__["posts"]
        assert descriptor.on_delete == "cascade"
        assert descriptor.backref == "author"
    
    def test_combined_cascade_and_lazy(self, clean_state):
        """Test cascade combined with lazy loading."""
        class Item(Table):
            name: str = ""
            container_id: int = 0
        
        class Container(Table):
            name: str = ""
            items: List[Item] = has_many(
                Item, "container_id",
                lazy="selectin",
                on_delete="cascade"
            )
        
        descriptor = Container.__dict__["items"]
        assert descriptor.on_delete == "cascade"
        assert descriptor.lazy == "selectin"

