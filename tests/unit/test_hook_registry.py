"""
Tests for HookRegistry and hook management.

Tests the core hook registry functionality, discovery, and global management.
"""

import pytest
from typing import List, Optional, Any

from pynext.db.relationships.hooks import (
    HookType,
    HookConfig,
    HookRegistry,
    on_append,
    on_remove,
    on_set,
    before_delete,
    get_hook_registry,
    reset_hook_registries,
    discover_hooks,
    has_hooks,
    get_hooks_for_relationship,
    fire_hooks,
)
from pynext.db.relationships.hook_executor import reset_hook_executor


# =============================================================================
# Mock Classes for Testing
# =============================================================================

class MockTable:
    """Base mock table for testing."""
    _fields = {}
    __table_name__ = "mock_table"
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockPost(MockTable):
    """Mock post for testing."""
    __table_name__ = "posts"
    
    def __init__(self, id: int = 1, title: str = "Test"):
        super().__init__(id=id, title=title)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_registries():
    """Reset all registries before each test."""
    reset_hook_registries()
    reset_hook_executor()
    yield
    reset_hook_registries()
    reset_hook_executor()


# =============================================================================
# Test: HookRegistry Initialization
# =============================================================================

class TestHookRegistryInitialization:
    """Test HookRegistry initialization."""
    
    def test_empty_registry(self):
        """New registry is empty."""
        registry = HookRegistry()
        
        assert registry._on_append == {}
        assert registry._on_remove == {}
        assert registry._on_set == {}
        assert registry._before_delete == []
    
    def test_get_hook_count_empty(self):
        """Empty registry has count 0."""
        registry = HookRegistry()
        
        assert registry.get_hook_count() == 0
    
    def test_has_hooks_for_empty(self):
        """Empty registry has no hooks."""
        registry = HookRegistry()
        
        assert registry.has_hooks_for("anything") is False


# =============================================================================
# Test: HookRegistry Registration
# =============================================================================

class TestHookRegistryRegistration:
    """Test hook registration."""
    
    def test_register_on_append(self):
        """Register on_append hook."""
        registry = HookRegistry()
        handler = lambda self, item: None
        
        registry.register_on_append("posts", handler)
        
        assert "posts" in registry._on_append
        assert handler in registry._on_append["posts"]
    
    def test_register_on_remove(self):
        """Register on_remove hook."""
        registry = HookRegistry()
        handler = lambda self, item: None
        
        registry.register_on_remove("posts", handler)
        
        assert "posts" in registry._on_remove
        assert handler in registry._on_remove["posts"]
    
    def test_register_on_set(self):
        """Register on_set hook."""
        registry = HookRegistry()
        handler = lambda self, old, new: None
        
        registry.register_on_set("profile", handler)
        
        assert "profile" in registry._on_set
        assert handler in registry._on_set["profile"]
    
    def test_register_before_delete(self):
        """Register before_delete hook."""
        registry = HookRegistry()
        handler = lambda self: None
        
        registry.register_before_delete(handler)
        
        assert handler in registry._before_delete
    
    def test_register_same_hook_twice(self):
        """Registering same hook twice adds it twice."""
        registry = HookRegistry()
        handler = lambda self, item: None
        
        registry.register_on_append("posts", handler)
        registry.register_on_append("posts", handler)
        
        assert len(registry._on_append["posts"]) == 2


# =============================================================================
# Test: HookRegistry Firing
# =============================================================================

class TestHookRegistryFiring:
    """Test hook firing."""
    
    def test_fire_on_append(self):
        """Fire on_append hooks."""
        registry = HookRegistry()
        calls = []
        
        registry.register_on_append("posts", lambda self, item: calls.append((self, item)))
        
        owner = MockTable(id=1)
        item = MockPost(id=2)
        
        registry.fire_on_append(owner, "posts", item)
        
        assert len(calls) == 1
    
    def test_fire_on_remove(self):
        """Fire on_remove hooks."""
        registry = HookRegistry()
        calls = []
        
        registry.register_on_remove("posts", lambda self, item: calls.append((self, item)))
        
        owner = MockTable(id=1)
        item = MockPost(id=2)
        
        registry.fire_on_remove(owner, "posts", item)
        
        assert len(calls) == 1
    
    def test_fire_on_set(self):
        """Fire on_set hooks."""
        registry = HookRegistry()
        calls = []
        
        registry.register_on_set("profile", lambda self, old, new: calls.append((self, old, new)))
        
        owner = MockTable(id=1)
        old = MockTable(id=2)
        new = MockTable(id=3)
        
        registry.fire_on_set(owner, "profile", old, new)
        
        assert len(calls) == 1
    
    def test_fire_before_delete(self):
        """Fire before_delete hooks."""
        registry = HookRegistry()
        calls = []
        
        registry.register_before_delete(lambda self: calls.append(self))
        
        owner = MockTable(id=1)
        
        registry.fire_before_delete(owner)
        
        assert len(calls) == 1


# =============================================================================
# Test: HookRegistry Counting
# =============================================================================

class TestHookRegistryCounting:
    """Test hook counting."""
    
    def test_count_all_hooks(self):
        """Count all types of hooks."""
        registry = HookRegistry()
        
        registry.register_on_append("posts", lambda s, i: None)
        registry.register_on_append("comments", lambda s, i: None)
        registry.register_on_remove("posts", lambda s, i: None)
        registry.register_on_set("profile", lambda s, o, n: None)
        registry.register_before_delete(lambda s: None)
        
        assert registry.get_hook_count() == 5
    
    def test_has_hooks_for_append(self):
        """has_hooks_for detects append hooks."""
        registry = HookRegistry()
        
        registry.register_on_append("posts", lambda s, i: None)
        
        assert registry.has_hooks_for("posts") is True
        assert registry.has_hooks_for("comments") is False
    
    def test_has_hooks_for_remove(self):
        """has_hooks_for detects remove hooks."""
        registry = HookRegistry()
        
        registry.register_on_remove("posts", lambda s, i: None)
        
        assert registry.has_hooks_for("posts") is True
    
    def test_has_hooks_for_set(self):
        """has_hooks_for detects set hooks."""
        registry = HookRegistry()
        
        registry.register_on_set("profile", lambda s, o, n: None)
        
        assert registry.has_hooks_for("profile") is True


# =============================================================================
# Test: HookRegistry Merge
# =============================================================================

class TestHookRegistryMerge:
    """Test hook registry merging for inheritance."""
    
    def test_merge_empty_into_empty(self):
        """Merge empty registry into empty."""
        parent = HookRegistry()
        child = HookRegistry()
        
        child.merge_from(parent)
        
        assert child.get_hook_count() == 0
    
    def test_merge_populated_into_empty(self):
        """Merge populated registry into empty."""
        parent = HookRegistry()
        child = HookRegistry()
        
        handler = lambda s, i: None
        parent.register_on_append("posts", handler)
        
        child.merge_from(parent)
        
        assert "posts" in child._on_append
        assert handler in child._on_append["posts"]
    
    def test_merge_empty_into_populated(self):
        """Merge empty registry into populated."""
        parent = HookRegistry()
        child = HookRegistry()
        
        handler = lambda s, i: None
        child.register_on_append("posts", handler)
        
        child.merge_from(parent)
        
        assert child.get_hook_count() == 1
    
    def test_merge_both_populated(self):
        """Merge when both registries have hooks."""
        parent = HookRegistry()
        child = HookRegistry()
        
        parent_handler = lambda s, i: None
        child_handler = lambda s, i: None
        
        parent.register_on_append("posts", parent_handler)
        child.register_on_append("posts", child_handler)
        
        child.merge_from(parent)
        
        assert len(child._on_append["posts"]) == 2
    
    def test_merge_all_hook_types(self):
        """Merge all hook types."""
        parent = HookRegistry()
        child = HookRegistry()
        
        parent.register_on_append("posts", lambda s, i: None)
        parent.register_on_remove("posts", lambda s, i: None)
        parent.register_on_set("profile", lambda s, o, n: None)
        parent.register_before_delete(lambda s: None)
        
        child.merge_from(parent)
        
        assert child.get_hook_count() == 4


# =============================================================================
# Test: Global Registry Functions
# =============================================================================

class TestGlobalRegistryFunctions:
    """Test global registry management functions."""
    
    def test_get_hook_registry_creates_new(self):
        """get_hook_registry creates new registry for class."""
        
        class TestModel(MockTable):
            pass
        
        registry = get_hook_registry(TestModel)
        
        assert isinstance(registry, HookRegistry)
    
    def test_get_hook_registry_returns_same(self):
        """get_hook_registry returns same registry for class."""
        
        class TestModel(MockTable):
            pass
        
        registry1 = get_hook_registry(TestModel)
        registry2 = get_hook_registry(TestModel)
        
        assert registry1 is registry2
    
    def test_get_hook_registry_different_classes(self):
        """get_hook_registry returns different registries for different classes."""
        
        class TestModel1(MockTable):
            pass
        
        class TestModel2(MockTable):
            pass
        
        registry1 = get_hook_registry(TestModel1)
        registry2 = get_hook_registry(TestModel2)
        
        assert registry1 is not registry2
    
    def test_reset_hook_registries(self):
        """reset_hook_registries clears all registries."""
        
        class TestModel(MockTable):
            pass
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", lambda s, i: None)
        
        reset_hook_registries()
        
        # New registry should be empty
        new_registry = get_hook_registry(TestModel)
        assert new_registry.get_hook_count() == 0


# =============================================================================
# Test: discover_hooks Function
# =============================================================================

class TestDiscoverHooks:
    """Test discover_hooks function."""
    
    def test_discover_on_append_hook(self):
        """Discover on_append hook."""
        
        class TestModel(MockTable):
            @on_append("posts")
            def on_post_added(self, post):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert "posts" in registry._on_append
    
    def test_discover_on_remove_hook(self):
        """Discover on_remove hook."""
        
        class TestModel(MockTable):
            @on_remove("posts")
            def on_post_removed(self, post):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert "posts" in registry._on_remove
    
    def test_discover_on_set_hook(self):
        """Discover on_set hook."""
        
        class TestModel(MockTable):
            @on_set("profile")
            def on_profile_changed(self, old, new):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert "profile" in registry._on_set
    
    def test_discover_before_delete_hook(self):
        """Discover before_delete hook."""
        
        class TestModel(MockTable):
            @before_delete()
            def cleanup(self):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert len(registry._before_delete) == 1
    
    def test_discover_all_hook_types(self):
        """Discover all hook types."""
        
        class TestModel(MockTable):
            @on_append("posts")
            def on_post_added(self, post):
                pass
            
            @on_remove("posts")
            def on_post_removed(self, post):
                pass
            
            @on_set("profile")
            def on_profile_changed(self, old, new):
                pass
            
            @before_delete()
            def cleanup(self):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert registry.get_hook_count() == 4
    
    def test_discover_ignores_non_hook_methods(self):
        """Discover ignores methods without hook decorator."""
        
        class TestModel(MockTable):
            def regular_method(self):
                pass
            
            @on_append("posts")
            def on_post_added(self, post):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert registry.get_hook_count() == 1


# =============================================================================
# Test: has_hooks Function
# =============================================================================

class TestHasHooksFunction:
    """Test has_hooks function."""
    
    def test_has_hooks_false_when_empty(self):
        """has_hooks returns False when no hooks."""
        
        class TestModel(MockTable):
            pass
        
        assert has_hooks(TestModel) is False
    
    def test_has_hooks_true_when_hooks_exist(self):
        """has_hooks returns True when hooks exist."""
        
        class TestModel(MockTable):
            pass
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", lambda s, i: None)
        
        assert has_hooks(TestModel) is True


# =============================================================================
# Test: get_hooks_for_relationship Function
# =============================================================================

class TestGetHooksForRelationship:
    """Test get_hooks_for_relationship function."""
    
    def test_get_on_append_hooks(self):
        """Get on_append hooks for relationship."""
        
        class TestModel(MockTable):
            pass
        
        handler = lambda s, i: None
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        hooks = get_hooks_for_relationship(TestModel, "posts", HookType.ON_APPEND)
        
        assert handler in hooks
    
    def test_get_on_remove_hooks(self):
        """Get on_remove hooks for relationship."""
        
        class TestModel(MockTable):
            pass
        
        handler = lambda s, i: None
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", handler)
        
        hooks = get_hooks_for_relationship(TestModel, "posts", HookType.ON_REMOVE)
        
        assert handler in hooks
    
    def test_get_on_set_hooks(self):
        """Get on_set hooks for relationship."""
        
        class TestModel(MockTable):
            pass
        
        handler = lambda s, o, n: None
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        hooks = get_hooks_for_relationship(TestModel, "profile", HookType.ON_SET)
        
        assert handler in hooks
    
    def test_get_before_delete_hooks(self):
        """Get before_delete hooks."""
        
        class TestModel(MockTable):
            pass
        
        handler = lambda s: None
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        hooks = get_hooks_for_relationship(TestModel, "", HookType.BEFORE_DELETE)
        
        assert handler in hooks
    
    def test_get_hooks_empty_list_when_none(self):
        """Get empty list when no hooks."""
        
        class TestModel(MockTable):
            pass
        
        hooks = get_hooks_for_relationship(TestModel, "posts", HookType.ON_APPEND)
        
        assert hooks == []


# =============================================================================
# Test: fire_hooks Function
# =============================================================================

class TestFireHooksFunction:
    """Test fire_hooks function."""
    
    def test_fire_on_append(self):
        """fire_hooks for ON_APPEND."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        handler = lambda s, i: calls.append((s, i))
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        owner = TestModel(id=1)
        item = MockPost(id=2)
        
        fire_hooks(owner, HookType.ON_APPEND, relationship="posts", item=item)
        
        assert len(calls) == 1
    
    def test_fire_on_remove(self):
        """fire_hooks for ON_REMOVE."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        handler = lambda s, i: calls.append((s, i))
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", handler)
        
        owner = TestModel(id=1)
        item = MockPost(id=2)
        
        fire_hooks(owner, HookType.ON_REMOVE, relationship="posts", item=item)
        
        assert len(calls) == 1
    
    def test_fire_on_set(self):
        """fire_hooks for ON_SET."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        handler = lambda s, o, n: calls.append((s, o, n))
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        owner = TestModel(id=1)
        
        fire_hooks(owner, HookType.ON_SET, relationship="profile", old_value=None, new_value=MockTable(id=2))
        
        assert len(calls) == 1
    
    def test_fire_before_delete(self):
        """fire_hooks for BEFORE_DELETE."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        handler = lambda s: calls.append(s)
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        owner = TestModel(id=1)
        
        fire_hooks(owner, HookType.BEFORE_DELETE)
        
        assert len(calls) == 1

