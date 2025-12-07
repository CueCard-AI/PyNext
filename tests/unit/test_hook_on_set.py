"""
Tests for @on_set relationship hooks.

Tests the on_set decorator for scalar relationships:
- belongs_to relationships
- has_one relationships
"""

import pytest
from typing import List, Optional, Any

from pynext.db.relationships.hooks import (
    HookType,
    HookConfig,
    HookRegistry,
    on_set,
    get_hook_registry,
    reset_hook_registries,
    discover_hooks,
)
from pynext.db.relationships.hook_executor import (
    fire_on_set,
    reset_hook_executor,
)


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


class MockUser(MockTable):
    """Mock user for testing."""
    __table_name__ = "users"
    
    def __init__(self, id: int = 1, name: str = "Test User"):
        super().__init__(id=id, name=name)


class MockProfile(MockTable):
    """Mock profile for testing."""
    __table_name__ = "profiles"
    
    def __init__(self, id: int = 1, bio: str = "Test bio"):
        super().__init__(id=id, bio=bio)


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
# Test: @on_set Decorator Basic
# =============================================================================

class TestOnSetDecoratorBasic:
    """Test basic @on_set decorator functionality."""
    
    def test_decorator_marks_function(self):
        """on_set decorator marks function with hook config."""
        @on_set("profile")
        def handler(self, old_value, new_value):
            pass
        
        assert hasattr(handler, "_pynext_hook")
        assert handler._pynext_hook.type == HookType.ON_SET
        assert handler._pynext_hook.relationship == "profile"
    
    def test_decorator_preserves_function_name(self):
        """on_set decorator preserves function name."""
        @on_set("profile")
        def my_custom_handler(self, old, new):
            pass
        
        assert my_custom_handler.__name__ == "my_custom_handler"
    
    def test_decorator_with_priority(self):
        """on_set decorator accepts priority parameter."""
        @on_set("profile", priority=5)
        def handler(self, old, new):
            pass
        
        assert handler._pynext_hook.priority == 5
    
    def test_decorator_default_priority_is_zero(self):
        """Default priority is 0."""
        @on_set("profile")
        def handler(self, old, new):
            pass
        
        assert handler._pynext_hook.priority == 0
    
    def test_decorator_with_different_relationships(self):
        """on_set works with different relationship names."""
        @on_set("profile")
        def profile_handler(self, old, new):
            pass
        
        @on_set("author")
        def author_handler(self, old, new):
            pass
        
        @on_set("category")
        def category_handler(self, old, new):
            pass
        
        assert profile_handler._pynext_hook.relationship == "profile"
        assert author_handler._pynext_hook.relationship == "author"
        assert category_handler._pynext_hook.relationship == "category"


# =============================================================================
# Test: HookRegistry on_set Registration
# =============================================================================

class TestHookRegistryOnSet:
    """Test HookRegistry on_set registration."""
    
    def test_register_single_hook(self):
        """Register single on_set hook."""
        registry = HookRegistry()
        
        def handler(self, old, new):
            pass
        
        registry.register_on_set("profile", handler)
        
        assert "profile" in registry._on_set
        assert handler in registry._on_set["profile"]
    
    def test_register_multiple_hooks_same_relationship(self):
        """Register multiple hooks for same relationship."""
        registry = HookRegistry()
        
        def handler1(self, old, new):
            pass
        
        def handler2(self, old, new):
            pass
        
        registry.register_on_set("profile", handler1)
        registry.register_on_set("profile", handler2)
        
        assert len(registry._on_set["profile"]) == 2
        assert handler1 in registry._on_set["profile"]
        assert handler2 in registry._on_set["profile"]
    
    def test_register_hooks_different_relationships(self):
        """Register hooks for different relationships."""
        registry = HookRegistry()
        
        def profile_handler(self, old, new):
            pass
        
        def author_handler(self, old, new):
            pass
        
        registry.register_on_set("profile", profile_handler)
        registry.register_on_set("author", author_handler)
        
        assert "profile" in registry._on_set
        assert "author" in registry._on_set
    
    def test_has_hooks_for_returns_true_when_hooks_exist(self):
        """has_hooks_for returns True when on_set hooks exist."""
        registry = HookRegistry()
        registry.register_on_set("profile", lambda self, o, n: None)
        
        assert registry.has_hooks_for("profile") is True
    
    def test_get_hook_count_includes_set_hooks(self):
        """get_hook_count includes on_set hooks."""
        registry = HookRegistry()
        
        assert registry.get_hook_count() == 0
        
        registry.register_on_set("profile", lambda self, o, n: None)
        assert registry.get_hook_count() == 1


# =============================================================================
# Test: HookRegistry fire_on_set
# =============================================================================

class TestHookRegistryFireOnSet:
    """Test HookRegistry.fire_on_set()."""
    
    def test_fire_calls_registered_hook(self):
        """fire_on_set calls registered hook."""
        registry = HookRegistry()
        called_with = []
        
        def handler(self, old, new):
            called_with.append((self, old, new))
        
        registry.register_on_set("profile", handler)
        
        owner = MockTable(id=1)
        old_profile = MockProfile(id=1)
        new_profile = MockProfile(id=2)
        
        registry.fire_on_set(owner, "profile", old_profile, new_profile)
        
        assert len(called_with) == 1
        assert called_with[0][0] is owner
        assert called_with[0][1] is old_profile
        assert called_with[0][2] is new_profile
    
    def test_fire_calls_all_registered_hooks(self):
        """fire_on_set calls all registered hooks."""
        registry = HookRegistry()
        calls = []
        
        def handler1(self, old, new):
            calls.append("handler1")
        
        def handler2(self, old, new):
            calls.append("handler2")
        
        registry.register_on_set("profile", handler1)
        registry.register_on_set("profile", handler2)
        
        owner = MockTable(id=1)
        
        registry.fire_on_set(owner, "profile", None, MockProfile(id=1))
        
        assert calls == ["handler1", "handler2"]
    
    def test_fire_does_nothing_for_unregistered_relationship(self):
        """fire_on_set does nothing for unregistered relationship."""
        registry = HookRegistry()
        calls = []
        
        def handler(self, old, new):
            calls.append("called")
        
        registry.register_on_set("profile", handler)
        
        owner = MockTable(id=1)
        
        # Fire for different relationship
        registry.fire_on_set(owner, "author", None, MockUser(id=1))
        
        assert calls == []


# =============================================================================
# Test: fire_on_set Convenience Function
# =============================================================================

class TestFireOnSetFunction:
    """Test fire_on_set convenience function."""
    
    def test_fire_on_set_with_registered_hooks(self):
        """fire_on_set fires hooks from registry."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def handler(self, old, new):
            calls.append(("handler", self, old, new))
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        owner = TestModel(id=1)
        old_profile = MockProfile(id=1)
        new_profile = MockProfile(id=2)
        
        fire_on_set(owner, "profile", old_profile, new_profile)
        
        assert len(calls) == 1
        assert calls[0][0] == "handler"
        assert calls[0][1] is owner
        assert calls[0][2] is old_profile
        assert calls[0][3] is new_profile
    
    def test_fire_on_set_no_hooks_doesnt_error(self):
        """fire_on_set with no hooks doesn't error."""
        class TestModel(MockTable):
            pass
        
        owner = TestModel(id=1)
        
        # Should not raise
        fire_on_set(owner, "profile", None, MockProfile(id=1))


# =============================================================================
# Test: Discover Hooks
# =============================================================================

class TestDiscoverSetHooks:
    """Test discover_hooks function for on_set."""
    
    def test_discover_on_set_hook(self):
        """discover_hooks finds on_set decorated methods."""
        
        class TestModel(MockTable):
            @on_set("profile")
            def on_profile_changed(self, old, new):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert "profile" in registry._on_set
        assert len(registry._on_set["profile"]) == 1
    
    def test_discover_multiple_on_set_hooks(self):
        """discover_hooks finds multiple on_set hooks."""
        
        class TestModel(MockTable):
            @on_set("profile")
            def on_profile_changed(self, old, new):
                pass
            
            @on_set("author")
            def on_author_changed(self, old, new):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert "profile" in registry._on_set
        assert "author" in registry._on_set


# =============================================================================
# Test: Hook with Old and New Values
# =============================================================================

class TestOnSetOldNewValues:
    """Test hooks receive correct old and new values."""
    
    def test_hook_receives_old_value(self):
        """Hook receives the old value correctly."""
        
        class TestModel(MockTable):
            pass
        
        received = []
        
        def handler(self, old, new):
            received.append({"old": old, "new": new})
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        owner = TestModel(id=1)
        old_profile = MockProfile(id=1, bio="Old bio")
        new_profile = MockProfile(id=2, bio="New bio")
        
        fire_on_set(owner, "profile", old_profile, new_profile)
        
        assert len(received) == 1
        assert received[0]["old"] is old_profile
        assert received[0]["new"] is new_profile
    
    def test_hook_receives_none_old_value(self):
        """Hook receives None as old value when initially setting."""
        
        class TestModel(MockTable):
            pass
        
        received = []
        
        def handler(self, old, new):
            received.append({"old": old, "new": new})
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        owner = TestModel(id=1)
        new_profile = MockProfile(id=1)
        
        fire_on_set(owner, "profile", None, new_profile)
        
        assert len(received) == 1
        assert received[0]["old"] is None
        assert received[0]["new"] is new_profile
    
    def test_hook_receives_none_new_value(self):
        """Hook receives None as new value when clearing."""
        
        class TestModel(MockTable):
            pass
        
        received = []
        
        def handler(self, old, new):
            received.append({"old": old, "new": new})
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        owner = TestModel(id=1)
        old_profile = MockProfile(id=1)
        
        fire_on_set(owner, "profile", old_profile, None)
        
        assert len(received) == 1
        assert received[0]["old"] is old_profile
        assert received[0]["new"] is None
    
    def test_hook_receives_both_none(self):
        """Hook receives both None values."""
        
        class TestModel(MockTable):
            pass
        
        received = []
        
        def handler(self, old, new):
            received.append({"old": old, "new": new})
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        owner = TestModel(id=1)
        
        fire_on_set(owner, "profile", None, None)
        
        assert len(received) == 1
        assert received[0]["old"] is None
        assert received[0]["new"] is None


# =============================================================================
# Test: Common Use Cases
# =============================================================================

class TestOnSetUseCases:
    """Test common use cases for on_set hooks."""
    
    def test_log_profile_change(self):
        """Hook can log profile changes."""
        
        class TestModel(MockTable):
            pass
        
        audit_log = []
        
        def handler(self, old, new):
            old_id = old.id if old else None
            new_id = new.id if new else None
            audit_log.append(f"Profile changed: {old_id} -> {new_id}")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        owner = TestModel(id=1)
        
        fire_on_set(owner, "profile", MockProfile(id=1), MockProfile(id=2))
        
        assert audit_log == ["Profile changed: 1 -> 2"]
    
    def test_detect_assignment(self):
        """Hook can detect initial assignment."""
        
        class TestModel(MockTable):
            pass
        
        events = []
        
        def handler(self, old, new):
            if old is None and new is not None:
                events.append("initial_set")
            elif old is not None and new is not None:
                events.append("changed")
            elif old is not None and new is None:
                events.append("cleared")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        owner = TestModel(id=1)
        
        # Initial set
        fire_on_set(owner, "profile", None, MockProfile(id=1))
        # Change
        fire_on_set(owner, "profile", MockProfile(id=1), MockProfile(id=2))
        # Clear
        fire_on_set(owner, "profile", MockProfile(id=2), None)
        
        assert events == ["initial_set", "changed", "cleared"]
    
    def test_track_author_changes(self):
        """Hook can track author changes for a post."""
        
        class TestModel(MockTable):
            pass
        
        history = []
        
        def handler(self, old_author, new_author):
            history.append({
                "post_id": self.id,
                "old_author": old_author.name if old_author else None,
                "new_author": new_author.name if new_author else None,
            })
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("author", handler)
        
        post = TestModel(id=42)
        
        fire_on_set(post, "author", None, MockUser(name="Alice"))
        fire_on_set(post, "author", MockUser(name="Alice"), MockUser(name="Bob"))
        
        assert len(history) == 2
        assert history[0]["old_author"] is None
        assert history[0]["new_author"] == "Alice"
        assert history[1]["old_author"] == "Alice"
        assert history[1]["new_author"] == "Bob"


# =============================================================================
# Test: Hook Error Handling
# =============================================================================

class TestOnSetErrorHandling:
    """Test on_set hook error handling."""
    
    def test_hook_exception_propagates(self):
        """Hook exception propagates by default."""
        
        class TestModel(MockTable):
            pass
        
        def bad_handler(self, old, new):
            raise ValueError("Set hook error")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", bad_handler)
        
        owner = TestModel(id=1)
        
        with pytest.raises(ValueError, match="Set hook error"):
            fire_on_set(owner, "profile", None, MockProfile(id=1))


# =============================================================================
# Test: Hook Registry Merge (Inheritance)
# =============================================================================

class TestOnSetHookRegistryMerge:
    """Test HookRegistry.merge_from for on_set hooks."""
    
    def test_merge_on_set_hooks(self):
        """merge_from copies on_set hooks."""
        parent_registry = HookRegistry()
        child_registry = HookRegistry()
        
        def parent_handler(self, old, new):
            pass
        
        parent_registry.register_on_set("profile", parent_handler)
        child_registry.merge_from(parent_registry)
        
        assert "profile" in child_registry._on_set
        assert parent_handler in child_registry._on_set["profile"]
    
    def test_merge_preserves_existing_set_hooks(self):
        """merge_from preserves existing on_set hooks."""
        parent_registry = HookRegistry()
        child_registry = HookRegistry()
        
        def parent_handler(self, old, new):
            pass
        
        def child_handler(self, old, new):
            pass
        
        parent_registry.register_on_set("profile", parent_handler)
        child_registry.register_on_set("profile", child_handler)
        
        child_registry.merge_from(parent_registry)
        
        assert len(child_registry._on_set["profile"]) == 2


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestOnSetEdgeCases:
    """Test edge cases for on_set hooks."""
    
    def test_same_old_and_new_value(self):
        """Hook fires even when old == new (same object)."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def handler(self, old, new):
            calls.append((old, new))
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        owner = TestModel(id=1)
        profile = MockProfile(id=1)
        
        # Set to same object
        fire_on_set(owner, "profile", profile, profile)
        
        assert len(calls) == 1
        assert calls[0][0] is profile
        assert calls[0][1] is profile
    
    def test_empty_relationship_name(self):
        """on_set works with empty relationship name."""
        
        @on_set("")
        def handler(self, old, new):
            pass
        
        assert handler._pynext_hook.relationship == ""


# =============================================================================
# Test: Performance
# =============================================================================

class TestOnSetPerformance:
    """Test performance of on_set hooks."""
    
    def test_no_hooks_minimal_overhead(self):
        """No hooks means minimal overhead."""
        import time
        
        class TestModel(MockTable):
            pass
        
        owner = TestModel(id=1)
        
        start = time.perf_counter()
        for _ in range(1000):
            fire_on_set(owner, "profile", None, MockProfile(id=1))
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    def test_with_hooks_reasonable_overhead(self):
        """With hooks, overhead is still reasonable."""
        import time
        
        class TestModel(MockTable):
            pass
        
        def handler(self, old, new):
            pass
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", handler)
        
        owner = TestModel(id=1)
        
        start = time.perf_counter()
        for _ in range(1000):
            fire_on_set(owner, "profile", None, MockProfile(id=1))
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.2

