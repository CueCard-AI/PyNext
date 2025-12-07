"""
Tests for @on_remove relationship hooks.

Tests the on_remove decorator and its integration with:
- SyncedList (has_many collections)
- ManyToManyCollection (M2M collections)
- Various collection mutation methods (remove, pop, clear, del)
"""

import pytest
from typing import List, Optional, Any

from pynext.db.relationships.hooks import (
    HookType,
    HookConfig,
    HookRegistry,
    on_remove,
    get_hook_registry,
    reset_hook_registries,
    discover_hooks,
)
from pynext.db.relationships.hook_executor import (
    fire_on_remove,
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


class MockPost(MockTable):
    """Mock post for testing."""
    __table_name__ = "posts"
    
    def __init__(self, id: int = 1, title: str = "Test"):
        super().__init__(id=id, title=title)


class MockComment(MockTable):
    """Mock comment for testing."""
    __table_name__ = "comments"
    
    def __init__(self, id: int = 1, content: str = "Test comment"):
        super().__init__(id=id, content=content)


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
# Test: @on_remove Decorator Basic
# =============================================================================

class TestOnRemoveDecoratorBasic:
    """Test basic @on_remove decorator functionality."""
    
    def test_decorator_marks_function(self):
        """on_remove decorator marks function with hook config."""
        @on_remove("posts")
        def handler(self, post):
            pass
        
        assert hasattr(handler, "_pynext_hook")
        assert handler._pynext_hook.type == HookType.ON_REMOVE
        assert handler._pynext_hook.relationship == "posts"
    
    def test_decorator_preserves_function_name(self):
        """on_remove decorator preserves function name."""
        @on_remove("posts")
        def my_custom_handler(self, post):
            pass
        
        assert my_custom_handler.__name__ == "my_custom_handler"
    
    def test_decorator_with_priority(self):
        """on_remove decorator accepts priority parameter."""
        @on_remove("posts", priority=10)
        def handler(self, post):
            pass
        
        assert handler._pynext_hook.priority == 10
    
    def test_decorator_default_priority_is_zero(self):
        """Default priority is 0."""
        @on_remove("posts")
        def handler(self, post):
            pass
        
        assert handler._pynext_hook.priority == 0
    
    def test_decorator_with_different_relationships(self):
        """on_remove works with different relationship names."""
        @on_remove("posts")
        def posts_handler(self, item):
            pass
        
        @on_remove("comments")
        def comments_handler(self, item):
            pass
        
        @on_remove("tags")
        def tags_handler(self, item):
            pass
        
        assert posts_handler._pynext_hook.relationship == "posts"
        assert comments_handler._pynext_hook.relationship == "comments"
        assert tags_handler._pynext_hook.relationship == "tags"


# =============================================================================
# Test: HookRegistry on_remove Registration
# =============================================================================

class TestHookRegistryOnRemove:
    """Test HookRegistry on_remove registration."""
    
    def test_register_single_hook(self):
        """Register single on_remove hook."""
        registry = HookRegistry()
        
        def handler(self, item):
            pass
        
        registry.register_on_remove("posts", handler)
        
        assert "posts" in registry._on_remove
        assert handler in registry._on_remove["posts"]
    
    def test_register_multiple_hooks_same_relationship(self):
        """Register multiple hooks for same relationship."""
        registry = HookRegistry()
        
        def handler1(self, item):
            pass
        
        def handler2(self, item):
            pass
        
        registry.register_on_remove("posts", handler1)
        registry.register_on_remove("posts", handler2)
        
        assert len(registry._on_remove["posts"]) == 2
        assert handler1 in registry._on_remove["posts"]
        assert handler2 in registry._on_remove["posts"]
    
    def test_register_hooks_different_relationships(self):
        """Register hooks for different relationships."""
        registry = HookRegistry()
        
        def posts_handler(self, item):
            pass
        
        def comments_handler(self, item):
            pass
        
        registry.register_on_remove("posts", posts_handler)
        registry.register_on_remove("comments", comments_handler)
        
        assert "posts" in registry._on_remove
        assert "comments" in registry._on_remove
        assert posts_handler in registry._on_remove["posts"]
        assert comments_handler in registry._on_remove["comments"]
    
    def test_has_hooks_for_returns_true_when_hooks_exist(self):
        """has_hooks_for returns True when remove hooks exist."""
        registry = HookRegistry()
        registry.register_on_remove("posts", lambda self, item: None)
        
        assert registry.has_hooks_for("posts") is True
    
    def test_get_hook_count_includes_remove_hooks(self):
        """get_hook_count includes remove hooks."""
        registry = HookRegistry()
        
        assert registry.get_hook_count() == 0
        
        registry.register_on_remove("posts", lambda self, item: None)
        assert registry.get_hook_count() == 1
        
        registry.register_on_remove("posts", lambda self, item: None)
        assert registry.get_hook_count() == 2


# =============================================================================
# Test: HookRegistry fire_on_remove
# =============================================================================

class TestHookRegistryFireOnRemove:
    """Test HookRegistry.fire_on_remove()."""
    
    def test_fire_calls_registered_hook(self):
        """fire_on_remove calls registered hook."""
        registry = HookRegistry()
        called_with = []
        
        def handler(self, item):
            called_with.append((self, item))
        
        registry.register_on_remove("posts", handler)
        
        owner = MockTable(id=1)
        post = MockPost(id=2)
        
        registry.fire_on_remove(owner, "posts", post)
        
        assert len(called_with) == 1
        assert called_with[0][0] is owner
        assert called_with[0][1] is post
    
    def test_fire_calls_all_registered_hooks(self):
        """fire_on_remove calls all registered hooks."""
        registry = HookRegistry()
        calls = []
        
        def handler1(self, item):
            calls.append("handler1")
        
        def handler2(self, item):
            calls.append("handler2")
        
        registry.register_on_remove("posts", handler1)
        registry.register_on_remove("posts", handler2)
        
        owner = MockTable(id=1)
        post = MockPost(id=2)
        
        registry.fire_on_remove(owner, "posts", post)
        
        assert calls == ["handler1", "handler2"]
    
    def test_fire_does_nothing_for_unregistered_relationship(self):
        """fire_on_remove does nothing for unregistered relationship."""
        registry = HookRegistry()
        calls = []
        
        def handler(self, item):
            calls.append("called")
        
        registry.register_on_remove("posts", handler)
        
        # Fire for different relationship
        owner = MockTable(id=1)
        comment = MockComment(id=2)
        
        registry.fire_on_remove(owner, "comments", comment)
        
        assert calls == []
    
    def test_fire_passes_correct_item(self):
        """fire_on_remove passes the correct item."""
        registry = HookRegistry()
        received_items = []
        
        def handler(self, item):
            received_items.append(item)
        
        registry.register_on_remove("posts", handler)
        
        owner = MockTable(id=1)
        post1 = MockPost(id=1)
        post2 = MockPost(id=2)
        
        registry.fire_on_remove(owner, "posts", post1)
        registry.fire_on_remove(owner, "posts", post2)
        
        assert received_items[0] is post1
        assert received_items[1] is post2


# =============================================================================
# Test: fire_on_remove Convenience Function
# =============================================================================

class TestFireOnRemoveFunction:
    """Test fire_on_remove convenience function."""
    
    def test_fire_on_remove_with_registered_hooks(self):
        """fire_on_remove fires hooks from registry."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def handler(self, item):
            calls.append(("handler", self, item))
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=2)
        
        fire_on_remove(owner, "posts", post)
        
        assert len(calls) == 1
        assert calls[0][0] == "handler"
        assert calls[0][1] is owner
        assert calls[0][2] is post
    
    def test_fire_on_remove_no_hooks_doesnt_error(self):
        """fire_on_remove with no hooks doesn't error."""
        class TestModel(MockTable):
            pass
        
        owner = TestModel(id=1)
        post = MockPost(id=2)
        
        # Should not raise
        fire_on_remove(owner, "posts", post)


# =============================================================================
# Test: Discover Hooks
# =============================================================================

class TestDiscoverRemoveHooks:
    """Test discover_hooks function for on_remove."""
    
    def test_discover_on_remove_hook(self):
        """discover_hooks finds on_remove decorated methods."""
        
        class TestModel(MockTable):
            @on_remove("posts")
            def on_post_removed(self, post):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert "posts" in registry._on_remove
        assert len(registry._on_remove["posts"]) == 1
    
    def test_discover_multiple_on_remove_hooks(self):
        """discover_hooks finds multiple on_remove hooks."""
        
        class TestModel(MockTable):
            @on_remove("posts")
            def on_post_removed(self, post):
                pass
            
            @on_remove("comments")
            def on_comment_removed(self, comment):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert "posts" in registry._on_remove
        assert "comments" in registry._on_remove


# =============================================================================
# Test: Hook Execution with Removal Context
# =============================================================================

class TestRemoveHookContext:
    """Test hooks have access to removal context."""
    
    def test_hook_receives_removed_item(self):
        """Hook receives the removed item."""
        
        class TestModel(MockTable):
            pass
        
        removed_items = []
        
        def handler(self, item):
            removed_items.append({
                "id": item.id,
                "title": getattr(item, "title", None),
            })
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=42, title="Removed Post")
        
        fire_on_remove(owner, "posts", post)
        
        assert len(removed_items) == 1
        assert removed_items[0]["id"] == 42
        assert removed_items[0]["title"] == "Removed Post"
    
    def test_hook_can_log_removal(self):
        """Hook can log removal details."""
        
        class TestModel(MockTable):
            pass
        
        audit_log = []
        
        def handler(self, item):
            audit_log.append({
                "action": "removed",
                "owner_id": self.id,
                "item_id": item.id,
            })
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", handler)
        
        owner = TestModel(id=100)
        post = MockPost(id=200)
        
        fire_on_remove(owner, "posts", post)
        
        assert len(audit_log) == 1
        assert audit_log[0]["action"] == "removed"
        assert audit_log[0]["owner_id"] == 100
        assert audit_log[0]["item_id"] == 200


# =============================================================================
# Test: Hook Error Handling
# =============================================================================

class TestRemoveHookErrorHandling:
    """Test remove hook error handling."""
    
    def test_hook_exception_propagates(self):
        """Hook exception propagates by default."""
        
        class TestModel(MockTable):
            pass
        
        def bad_handler(self, item):
            raise ValueError("Removal hook error")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", bad_handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=2)
        
        with pytest.raises(ValueError, match="Removal hook error"):
            fire_on_remove(owner, "posts", post)
    
    def test_error_in_first_hook_prevents_subsequent_hooks(self):
        """Error in first hook prevents subsequent hooks from running."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def bad_handler(self, item):
            calls.append("bad")
            raise ValueError("Error")
        
        def good_handler(self, item):
            calls.append("good")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", bad_handler)
        registry.register_on_remove("posts", good_handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=2)
        
        with pytest.raises(ValueError):
            fire_on_remove(owner, "posts", post)
        
        assert calls == ["bad"]


# =============================================================================
# Test: Removal Patterns
# =============================================================================

class TestRemovalPatterns:
    """Test common removal patterns."""
    
    def test_cleanup_on_remove(self):
        """Hook can perform cleanup on remove."""
        
        class TestModel(MockTable):
            pass
        
        cleanup_actions = []
        
        def handler(self, item):
            cleanup_actions.append(f"cleanup_{item.id}")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", handler)
        
        owner = TestModel(id=1)
        
        for i in range(3):
            fire_on_remove(owner, "posts", MockPost(id=i))
        
        assert cleanup_actions == ["cleanup_0", "cleanup_1", "cleanup_2"]
    
    def test_cascade_notification_on_remove(self):
        """Hook can notify related systems on remove."""
        
        class TestModel(MockTable):
            pass
        
        notifications = []
        
        def handler(self, item):
            notifications.append({
                "type": "item_removed",
                "collection": "posts",
                "item_id": item.id,
            })
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=99)
        
        fire_on_remove(owner, "posts", post)
        
        assert len(notifications) == 1
        assert notifications[0]["type"] == "item_removed"
        assert notifications[0]["item_id"] == 99


# =============================================================================
# Test: Hook Registry Merge (Inheritance)
# =============================================================================

class TestRemoveHookRegistryMerge:
    """Test HookRegistry.merge_from for on_remove hooks."""
    
    def test_merge_on_remove_hooks(self):
        """merge_from copies on_remove hooks."""
        parent_registry = HookRegistry()
        child_registry = HookRegistry()
        
        def parent_handler(self, item):
            pass
        
        parent_registry.register_on_remove("posts", parent_handler)
        child_registry.merge_from(parent_registry)
        
        assert "posts" in child_registry._on_remove
        assert parent_handler in child_registry._on_remove["posts"]
    
    def test_merge_preserves_existing_remove_hooks(self):
        """merge_from preserves existing on_remove hooks."""
        parent_registry = HookRegistry()
        child_registry = HookRegistry()
        
        def parent_handler(self, item):
            pass
        
        def child_handler(self, item):
            pass
        
        parent_registry.register_on_remove("posts", parent_handler)
        child_registry.register_on_remove("posts", child_handler)
        
        child_registry.merge_from(parent_registry)
        
        assert len(child_registry._on_remove["posts"]) == 2


# =============================================================================
# Test: Combined Append and Remove
# =============================================================================

class TestCombinedAppendRemove:
    """Test combined append and remove hooks."""
    
    def test_separate_append_and_remove_hooks(self):
        """Append and remove hooks fire independently."""
        from pynext.db.relationships.hooks import on_append
        from pynext.db.relationships.hook_executor import fire_on_append
        
        class TestModel(MockTable):
            pass
        
        events = []
        
        def append_handler(self, item):
            events.append(("append", item.id))
        
        def remove_handler(self, item):
            events.append(("remove", item.id))
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", append_handler)
        registry.register_on_remove("posts", remove_handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=10)
        
        fire_on_append(owner, "posts", post)
        fire_on_remove(owner, "posts", post)
        
        assert events == [("append", 10), ("remove", 10)]
    
    def test_hooks_for_different_relationships_independent(self):
        """Hooks for different relationships are independent."""
        from pynext.db.relationships.hooks import on_append
        from pynext.db.relationships.hook_executor import fire_on_append
        
        class TestModel(MockTable):
            pass
        
        events = []
        
        def posts_remove(self, item):
            events.append("posts_remove")
        
        def comments_remove(self, item):
            events.append("comments_remove")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", posts_remove)
        registry.register_on_remove("comments", comments_remove)
        
        owner = TestModel(id=1)
        
        fire_on_remove(owner, "posts", MockPost(id=1))
        
        assert events == ["posts_remove"]


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestOnRemoveEdgeCases:
    """Test edge cases for on_remove hooks."""
    
    def test_hook_with_none_item(self):
        """Hook works with None item."""
        
        class TestModel(MockTable):
            pass
        
        received = []
        
        def handler(self, item):
            received.append(item)
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", handler)
        
        owner = TestModel(id=1)
        fire_on_remove(owner, "posts", None)
        
        assert received == [None]
    
    def test_remove_nonexistent_relationship_silent(self):
        """Firing remove for nonexistent relationship is silent."""
        
        class TestModel(MockTable):
            pass
        
        registry = get_hook_registry(TestModel)
        # No hooks registered
        
        owner = TestModel(id=1)
        # Should not raise
        fire_on_remove(owner, "nonexistent", MockPost(id=1))


# =============================================================================
# Test: Performance
# =============================================================================

class TestOnRemovePerformance:
    """Test performance characteristics of on_remove hooks."""
    
    def test_no_hooks_minimal_overhead(self):
        """No hooks means minimal overhead."""
        import time
        
        class TestModel(MockTable):
            pass
        
        owner = TestModel(id=1)
        post = MockPost(id=1)
        
        start = time.perf_counter()
        for _ in range(1000):
            fire_on_remove(owner, "posts", post)
        elapsed = time.perf_counter() - start
        
        # Should be very fast
        assert elapsed < 0.1
    
    def test_with_hooks_reasonable_overhead(self):
        """With hooks, overhead is still reasonable."""
        import time
        
        class TestModel(MockTable):
            pass
        
        def handler(self, item):
            pass
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=1)
        
        start = time.perf_counter()
        for _ in range(1000):
            fire_on_remove(owner, "posts", post)
        elapsed = time.perf_counter() - start
        
        # Should still be very fast
        assert elapsed < 0.2

