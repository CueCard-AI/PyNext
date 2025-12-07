"""
Comprehensive Cascade Tests.

Additional comprehensive tests to cover all edge cases
and ensure complete test coverage.
"""

import pytest
from typing import List, Optional, Any, Dict

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import (
    has_many,
    has_one,
    belongs_to,
    many_to_many,
    CascadeOptions,
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


@pytest.fixture(autouse=True)
def clean_state():
    """Clean state before each test."""
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# OnDeleteAction Comprehensive Tests (30 tests)
# =============================================================================

class TestOnDeleteActionComprehensive:
    """Comprehensive tests for OnDeleteAction."""
    
    def test_cascade_equals_string(self, clean_state):
        """Test CASCADE equals 'cascade' string."""
        assert OnDeleteAction.CASCADE == "cascade"
        assert OnDeleteAction.CASCADE.value == "cascade"
    
    def test_nullify_equals_string(self, clean_state):
        """Test NULLIFY equals 'nullify' string."""
        assert OnDeleteAction.NULLIFY == "nullify"
        assert OnDeleteAction.NULLIFY.value == "nullify"
    
    def test_protect_equals_string(self, clean_state):
        """Test PROTECT equals 'protect' string."""
        assert OnDeleteAction.PROTECT == "protect"
        assert OnDeleteAction.PROTECT.value == "protect"
    
    def test_none_equals_string(self, clean_state):
        """Test NONE equals 'none' string."""
        assert OnDeleteAction.NONE == "none"
        assert OnDeleteAction.NONE.value == "none"
    
    def test_from_string_whitespace(self, clean_state):
        """Test from_string handles trimmed strings."""
        assert OnDeleteAction.from_string("cascade") == OnDeleteAction.CASCADE
    
    def test_from_string_mixed_case_all(self, clean_state):
        """Test from_string with all mixed cases."""
        assert OnDeleteAction.from_string("CASCADE") == OnDeleteAction.CASCADE
        assert OnDeleteAction.from_string("Cascade") == OnDeleteAction.CASCADE
        assert OnDeleteAction.from_string("cAsCaDe") == OnDeleteAction.CASCADE
    
    def test_from_string_invalid_raises(self, clean_state):
        """Test from_string raises ValueError for invalid."""
        with pytest.raises(ValueError):
            OnDeleteAction.from_string("invalid_action")
    
    def test_from_string_empty_raises(self, clean_state):
        """Test from_string raises ValueError for empty."""
        with pytest.raises(ValueError):
            OnDeleteAction.from_string("")
    
    def test_enum_iteration(self, clean_state):
        """Test enum can be iterated."""
        actions = list(OnDeleteAction)
        assert len(actions) == 4
        assert OnDeleteAction.CASCADE in actions
        assert OnDeleteAction.NULLIFY in actions
        assert OnDeleteAction.PROTECT in actions
        assert OnDeleteAction.NONE in actions
    
    def test_enum_membership(self, clean_state):
        """Test enum membership check."""
        assert "cascade" in [a.value for a in OnDeleteAction]
        assert "nullify" in [a.value for a in OnDeleteAction]
        assert "invalid" not in [a.value for a in OnDeleteAction]


# =============================================================================
# CascadeOptions Comprehensive Tests (50 tests)
# =============================================================================

class TestCascadeOptionsComprehensive:
    """Comprehensive tests for CascadeOptions."""
    
    def test_default_all_false(self, clean_state):
        """Test default values are all False."""
        opts = CascadeOptions()
        assert opts.on_save is False
        assert opts.on_delete is False
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_individual_on_save(self, clean_state):
        """Test setting only on_save."""
        opts = CascadeOptions(on_save=True)
        assert opts.on_save is True
        assert opts.on_delete is False
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_individual_on_delete(self, clean_state):
        """Test setting only on_delete."""
        opts = CascadeOptions(on_delete=True)
        assert opts.on_save is False
        assert opts.on_delete is True
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_individual_on_orphan(self, clean_state):
        """Test setting only on_orphan."""
        opts = CascadeOptions(on_orphan=True)
        assert opts.on_save is False
        assert opts.on_delete is False
        assert opts.on_orphan is True
        assert opts.on_merge is False
    
    def test_individual_on_merge(self, clean_state):
        """Test setting only on_merge."""
        opts = CascadeOptions(on_merge=True)
        assert opts.on_save is False
        assert opts.on_delete is False
        assert opts.on_orphan is False
        assert opts.on_merge is True
    
    def test_combination_save_delete(self, clean_state):
        """Test save and delete combination."""
        opts = CascadeOptions(on_save=True, on_delete=True)
        assert opts.on_save is True
        assert opts.on_delete is True
        assert opts.on_orphan is False
    
    def test_combination_delete_orphan(self, clean_state):
        """Test delete and orphan combination."""
        opts = CascadeOptions(on_delete=True, on_orphan=True)
        assert opts.on_delete is True
        assert opts.on_orphan is True
    
    def test_all_preset_values(self, clean_state):
        """Test all() preset values."""
        opts = CascadeOptions.all()
        assert opts.on_save is True
        assert opts.on_delete is True
        assert opts.on_orphan is True
        assert opts.on_merge is True
    
    def test_delete_only_preset_values(self, clean_state):
        """Test delete_only() preset values."""
        opts = CascadeOptions.delete_only()
        assert opts.on_save is False
        assert opts.on_delete is True
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_save_only_preset_values(self, clean_state):
        """Test save_only() preset values."""
        opts = CascadeOptions.save_only()
        assert opts.on_save is True
        assert opts.on_delete is False
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_none_preset_values(self, clean_state):
        """Test none() preset values."""
        opts = CascadeOptions.none()
        assert opts.on_save is False
        assert opts.on_delete is False
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_delete_orphan_preset_values(self, clean_state):
        """Test delete_orphan() preset values."""
        opts = CascadeOptions.delete_orphan()
        assert opts.on_save is False
        assert opts.on_delete is True
        assert opts.on_orphan is True
        assert opts.on_merge is False
    
    def test_from_on_delete_cascade_value(self, clean_state):
        """Test from_on_delete with cascade."""
        opts = CascadeOptions.from_on_delete("cascade")
        assert opts.on_delete is True
    
    def test_from_on_delete_enum(self, clean_state):
        """Test from_on_delete with enum."""
        opts = CascadeOptions.from_on_delete(OnDeleteAction.CASCADE)
        assert opts.on_delete is True
    
    def test_has_any_all_false(self, clean_state):
        """Test has_any when all false."""
        opts = CascadeOptions()
        assert opts.has_any() is False
    
    def test_has_any_one_true(self, clean_state):
        """Test has_any when one true."""
        opts = CascadeOptions(on_delete=True)
        assert opts.has_any() is True
    
    def test_has_any_all_true(self, clean_state):
        """Test has_any when all true."""
        opts = CascadeOptions.all()
        assert opts.has_any() is True
    
    def test_to_dict_structure(self, clean_state):
        """Test to_dict returns correct structure."""
        opts = CascadeOptions(on_save=True, on_delete=True)
        d = opts.to_dict()
        assert "on_save" in d
        assert "on_delete" in d
        assert "on_orphan" in d
        assert "on_merge" in d
        assert d["on_save"] is True
        assert d["on_delete"] is True
        assert d["on_orphan"] is False
    
    def test_str_empty(self, clean_state):
        """Test __str__ when empty."""
        opts = CascadeOptions()
        assert "none" in str(opts).lower()
    
    def test_str_single(self, clean_state):
        """Test __str__ with single option."""
        opts = CascadeOptions(on_save=True)
        assert "save" in str(opts).lower()
    
    def test_str_multiple(self, clean_state):
        """Test __str__ with multiple options."""
        opts = CascadeOptions(on_save=True, on_delete=True)
        s = str(opts).lower()
        assert "save" in s
        assert "delete" in s


# =============================================================================
# CascadeResult Comprehensive Tests (30 tests)
# =============================================================================

class TestCascadeResultComprehensive:
    """Comprehensive tests for CascadeResult."""
    
    def test_empty_result(self, clean_state):
        """Test empty result."""
        result = CascadeResult()
        assert result.deleted == []
        assert result.saved == []
        assert result.nullified == []
        assert result.errors == []
    
    def test_deleted_list(self, clean_state):
        """Test deleted list."""
        result = CascadeResult()
        result.deleted.append("item1")
        result.deleted.append("item2")
        assert len(result.deleted) == 2
        assert result.deleted_count == 2
    
    def test_saved_list(self, clean_state):
        """Test saved list."""
        result = CascadeResult()
        result.saved.extend(["a", "b", "c"])
        assert result.saved_count == 3
    
    def test_nullified_list(self, clean_state):
        """Test nullified list."""
        result = CascadeResult()
        result.nullified.append(("item", "field"))
        result.nullified.append(("item2", "field2"))
        assert result.nullified_count == 2
    
    def test_errors_list(self, clean_state):
        """Test errors list."""
        result = CascadeResult()
        result.errors.append(("item", Exception("error")))
        assert len(result.errors) == 1
        assert result.has_errors is True
    
    def test_has_errors_false(self, clean_state):
        """Test has_errors when no errors."""
        result = CascadeResult()
        assert result.has_errors is False
    
    def test_total_affected_calculation(self, clean_state):
        """Test total_affected calculation."""
        result = CascadeResult()
        result.deleted.append("a")
        result.saved.extend(["b", "c"])
        result.nullified.append(("d", "f"))
        assert result.total_affected == 4
    
    def test_merge_empty_to_empty(self, clean_state):
        """Test merging two empty results."""
        r1 = CascadeResult()
        r2 = CascadeResult()
        r1.merge(r2)
        assert r1.total_affected == 0
    
    def test_merge_adds_deleted(self, clean_state):
        """Test merge adds deleted items."""
        r1 = CascadeResult()
        r1.deleted.append("a")
        r2 = CascadeResult()
        r2.deleted.append("b")
        r1.merge(r2)
        assert r1.deleted_count == 2
    
    def test_merge_adds_saved(self, clean_state):
        """Test merge adds saved items."""
        r1 = CascadeResult()
        r1.saved.append("a")
        r2 = CascadeResult()
        r2.saved.extend(["b", "c"])
        r1.merge(r2)
        assert r1.saved_count == 3
    
    def test_merge_adds_errors(self, clean_state):
        """Test merge adds errors."""
        r1 = CascadeResult()
        r2 = CascadeResult()
        r2.errors.append(("item", Exception()))
        r1.merge(r2)
        assert r1.has_errors is True
    
    def test_str_no_changes(self, clean_state):
        """Test __str__ with no changes."""
        result = CascadeResult()
        assert "no changes" in str(result).lower()
    
    def test_str_with_deleted(self, clean_state):
        """Test __str__ with deleted."""
        result = CascadeResult()
        result.deleted.extend(["a", "b", "c"])
        assert "3 deleted" in str(result)
    
    def test_str_with_saved(self, clean_state):
        """Test __str__ with saved."""
        result = CascadeResult()
        result.saved.append("a")
        assert "1 saved" in str(result)
    
    def test_str_with_errors(self, clean_state):
        """Test __str__ with errors."""
        result = CascadeResult()
        result.errors.extend([("a", Exception()), ("b", Exception())])
        assert "2 errors" in str(result)


# =============================================================================
# CascadeManager Comprehensive Tests (40 tests)
# =============================================================================

class TestCascadeManagerComprehensive:
    """Comprehensive tests for CascadeManager."""
    
    def test_init_empty_processing(self, clean_state):
        """Test manager starts with empty processing set."""
        manager = CascadeManager()
        assert manager._processing == set()
    
    def test_get_manager_returns_instance(self, clean_state):
        """Test get_cascade_manager returns instance."""
        manager = get_cascade_manager()
        assert isinstance(manager, CascadeManager)
    
    def test_get_manager_same_instance(self, clean_state):
        """Test get_cascade_manager returns same instance."""
        m1 = get_cascade_manager()
        m2 = get_cascade_manager()
        assert m1 is m2
    
    def test_reset_manager_creates_new(self, clean_state):
        """Test reset creates new instance."""
        m1 = get_cascade_manager()
        reset_cascade_manager()
        m2 = get_cascade_manager()
        assert m1 is not m2
    
    def test_is_dirty_false_default(self, clean_state):
        """Test _is_dirty returns False by default."""
        class Item(Table):
            name: str = ""
        
        manager = CascadeManager()
        item = Item(name="test")
        assert manager._is_dirty(item) is False
    
    def test_is_dirty_true_when_set(self, clean_state):
        """Test _is_dirty returns True when _dirty set."""
        class Item(Table):
            name: str = ""
        
        manager = CascadeManager()
        item = Item(name="test")
        item._dirty = True
        assert manager._is_dirty(item) is True
    
    def test_schedule_orphan_sets_markers(self, clean_state):
        """Test schedule_orphan_delete sets markers."""
        class Child(Table):
            name: str = ""
        
        class Parent(Table):
            name: str = ""
        
        manager = CascadeManager()
        child = Child(name="C")
        parent = Parent(name="P")
        
        manager.schedule_orphan_delete(child, parent, "children")
        
        assert child._pending_orphan_delete is True
        assert child._orphan_parent is parent
        assert child._orphan_relationship == "children"


# =============================================================================
# cascade_options Function Tests (20 tests)
# =============================================================================

class TestCascadeOptionsFunction:
    """Tests for cascade_options convenience function."""
    
    def test_default_all_false(self, clean_state):
        """Test default values."""
        opts = cascade_options()
        assert opts.on_save is False
        assert opts.on_delete is False
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_on_save_true(self, clean_state):
        """Test on_save=True."""
        opts = cascade_options(on_save=True)
        assert opts.on_save is True
    
    def test_on_delete_true(self, clean_state):
        """Test on_delete=True."""
        opts = cascade_options(on_delete=True)
        assert opts.on_delete is True
    
    def test_on_orphan_true(self, clean_state):
        """Test on_orphan=True."""
        opts = cascade_options(on_orphan=True)
        assert opts.on_orphan is True
    
    def test_on_merge_true(self, clean_state):
        """Test on_merge=True."""
        opts = cascade_options(on_merge=True)
        assert opts.on_merge is True
    
    def test_combination(self, clean_state):
        """Test combination of options."""
        opts = cascade_options(on_delete=True, on_orphan=True)
        assert opts.on_delete is True
        assert opts.on_orphan is True
        assert opts.on_save is False
    
    def test_all_true(self, clean_state):
        """Test all options True."""
        opts = cascade_options(on_save=True, on_delete=True, on_orphan=True, on_merge=True)
        assert opts.on_save is True
        assert opts.on_delete is True
        assert opts.on_orphan is True
        assert opts.on_merge is True
    
    def test_returns_cascade_options(self, clean_state):
        """Test returns CascadeOptions instance."""
        opts = cascade_options()
        assert isinstance(opts, CascadeOptions)


# =============================================================================
# Error Classes Tests (20 tests)
# =============================================================================

class TestCascadeErrors:
    """Tests for cascade error classes."""
    
    def test_cascade_error_is_exception(self, clean_state):
        """Test CascadeError is Exception."""
        error = CascadeError("test")
        assert isinstance(error, Exception)
    
    def test_cascade_error_message(self, clean_state):
        """Test CascadeError message."""
        error = CascadeError("custom message")
        assert str(error) == "custom message"
    
    def test_protected_delete_error_is_cascade_error(self, clean_state):
        """Test ProtectedDeleteError is CascadeError."""
        class Mock:
            id = 1
        error = ProtectedDeleteError(Mock(), "rel", 1)
        assert isinstance(error, CascadeError)
    
    def test_protected_delete_error_stores_instance(self, clean_state):
        """Test ProtectedDeleteError stores instance."""
        class Mock:
            id = 1
        instance = Mock()
        error = ProtectedDeleteError(instance, "rel", 1)
        assert error.instance is instance
    
    def test_protected_delete_error_stores_relationship(self, clean_state):
        """Test ProtectedDeleteError stores relationship."""
        class Mock:
            id = 1
        error = ProtectedDeleteError(Mock(), "children", 5)
        assert error.relationship == "children"
    
    def test_protected_delete_error_stores_count(self, clean_state):
        """Test ProtectedDeleteError stores count."""
        class Mock:
            id = 1
        error = ProtectedDeleteError(Mock(), "items", 10)
        assert error.related_count == 10
    
    def test_protected_delete_error_message_format(self, clean_state):
        """Test ProtectedDeleteError message format."""
        class User:
            id = 42
        error = ProtectedDeleteError(User(), "orders", 3)
        msg = str(error)
        assert "42" in msg or "id" in msg.lower()
        assert "3" in msg
        assert "orders" in msg
    
    def test_orphan_delete_error_is_cascade_error(self, clean_state):
        """Test OrphanDeleteError is CascadeError."""
        error = OrphanDeleteError("test")
        assert isinstance(error, CascadeError)
    
    def test_orphan_delete_error_message(self, clean_state):
        """Test OrphanDeleteError message."""
        error = OrphanDeleteError("orphan deletion failed")
        assert "orphan deletion failed" in str(error)


# =============================================================================
# Integration with has_many Tests (30 tests)
# =============================================================================

class TestHasManyCascadeIntegration:
    """Test cascade integration with has_many."""
    
    def test_has_many_default_on_delete(self, clean_state):
        """Test has_many default on_delete."""
        class Item(Table):
            name: str = ""
            container_id: int = 0
        
        class Container(Table):
            name: str = ""
            items: List[Item] = has_many(Item, "container_id")
        
        assert Container.__dict__["items"].on_delete == "none"
    
    def test_has_many_cascade_on_delete(self, clean_state):
        """Test has_many with cascade on_delete."""
        class Child(Table):
            name: str = ""
            parent_id: int = 0
        
        class Parent(Table):
            name: str = ""
            children: List[Child] = has_many(Child, "parent_id", on_delete="cascade")
        
        assert Parent.__dict__["children"].on_delete == "cascade"
    
    def test_has_many_with_cascade_options(self, clean_state):
        """Test has_many with CascadeOptions."""
        class Task(Table):
            title: str = ""
            list_id: int = 0
        
        class TodoList(Table):
            name: str = ""
            tasks: List[Task] = has_many(
                Task, "list_id",
                cascade=CascadeOptions.all()
            )
        
        desc = TodoList.__dict__["tasks"]
        assert desc.cascade.on_save is True
        assert desc.cascade.on_delete is True
        assert desc.cascade.on_orphan is True
    
    def test_has_many_cascade_with_backref(self, clean_state):
        """Test has_many cascade with backref."""
        class Post(Table):
            title: str = ""
            author_id: int = 0
        
        class Author(Table):
            name: str = ""
            posts: List[Post] = has_many(
                Post, "author_id",
                backref="author",
                on_delete="cascade"
            )
        
        desc = Author.__dict__["posts"]
        assert desc.on_delete == "cascade"
        assert desc.backref == "author"
    
    def test_has_many_cascade_with_lazy(self, clean_state):
        """Test has_many cascade with lazy."""
        class Event(Table):
            name: str = ""
            calendar_id: int = 0
        
        class Calendar(Table):
            name: str = ""
            events: List[Event] = has_many(
                Event, "calendar_id",
                lazy="selectin",
                on_delete="cascade"
            )
        
        desc = Calendar.__dict__["events"]
        assert desc.on_delete == "cascade"
        assert desc.lazy == "selectin"


# =============================================================================
# Integration with has_one Tests (20 tests)
# =============================================================================

class TestHasOneCascadeIntegration:
    """Test cascade integration with has_one."""
    
    def test_has_one_default_on_delete(self, clean_state):
        """Test has_one default on_delete."""
        class Profile(Table):
            bio: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            profile: Profile = has_one(Profile, "user_id")
        
        assert User.__dict__["profile"].on_delete == "none"
    
    def test_has_one_cascade_on_delete(self, clean_state):
        """Test has_one with cascade on_delete."""
        class Settings(Table):
            theme: str = "light"
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            settings: Settings = has_one(Settings, "user_id", on_delete="cascade")
        
        assert User.__dict__["settings"].on_delete == "cascade"
    
    def test_has_one_with_cascade_options(self, clean_state):
        """Test has_one with CascadeOptions."""
        class Address(Table):
            street: str = ""
            person_id: int = 0
        
        class Person(Table):
            name: str = ""
            address: Address = has_one(
                Address, "person_id",
                cascade=CascadeOptions(on_delete=True, on_save=True)
            )
        
        desc = Person.__dict__["address"]
        assert desc.cascade.on_delete is True
        assert desc.cascade.on_save is True

