"""
Tests for @on_append relationship hooks.

Tests the on_append decorator and its integration with:
- SyncedList (has_many collections)
- ManyToManyCollection (M2M collections)
- Various collection mutation methods
"""

import pytest
from typing import List, Optional, Any
from dataclasses import dataclass, field

from pynext.db.relationships.hooks import (
    HookType,
    HookConfig,
    HookRegistry,
    on_append,
    get_hook_registry,
    reset_hook_registries,
    discover_hooks,
)
from pynext.db.relationships.hook_executor import (
    fire_on_append,
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
# Test: @on_append Decorator Basic
# =============================================================================

class TestOnAppendDecoratorBasic:
    """Test basic @on_append decorator functionality."""
    
    def test_decorator_marks_function(self):
        """on_append decorator marks function with hook config."""
        @on_append("posts")
        def handler(self, post):
            pass
        
        assert hasattr(handler, "_pynext_hook")
        assert handler._pynext_hook.type == HookType.ON_APPEND
        assert handler._pynext_hook.relationship == "posts"
    
    def test_decorator_preserves_function_name(self):
        """on_append decorator preserves function name."""
        @on_append("posts")
        def my_custom_handler(self, post):
            pass
        
        assert my_custom_handler.__name__ == "my_custom_handler"
    
    def test_decorator_with_priority(self):
        """on_append decorator accepts priority parameter."""
        @on_append("posts", priority=10)
        def handler(self, post):
            pass
        
        assert handler._pynext_hook.priority == 10
    
    def test_decorator_default_priority_is_zero(self):
        """Default priority is 0."""
        @on_append("posts")
        def handler(self, post):
            pass
        
        assert handler._pynext_hook.priority == 0
    
    def test_decorator_with_different_relationships(self):
        """on_append works with different relationship names."""
        @on_append("posts")
        def posts_handler(self, item):
            pass
        
        @on_append("comments")
        def comments_handler(self, item):
            pass
        
        @on_append("tags")
        def tags_handler(self, item):
            pass
        
        assert posts_handler._pynext_hook.relationship == "posts"
        assert comments_handler._pynext_hook.relationship == "comments"
        assert tags_handler._pynext_hook.relationship == "tags"


# =============================================================================
# Test: HookRegistry on_append Registration
# =============================================================================

class TestHookRegistryOnAppend:
    """Test HookRegistry on_append registration."""
    
    def test_register_single_hook(self):
        """Register single on_append hook."""
        registry = HookRegistry()
        
        def handler(self, item):
            pass
        
        registry.register_on_append("posts", handler)
        
        assert "posts" in registry._on_append
        assert handler in registry._on_append["posts"]
    
    def test_register_multiple_hooks_same_relationship(self):
        """Register multiple hooks for same relationship."""
        registry = HookRegistry()
        
        def handler1(self, item):
            pass
        
        def handler2(self, item):
            pass
        
        registry.register_on_append("posts", handler1)
        registry.register_on_append("posts", handler2)
        
        assert len(registry._on_append["posts"]) == 2
        assert handler1 in registry._on_append["posts"]
        assert handler2 in registry._on_append["posts"]
    
    def test_register_hooks_different_relationships(self):
        """Register hooks for different relationships."""
        registry = HookRegistry()
        
        def posts_handler(self, item):
            pass
        
        def comments_handler(self, item):
            pass
        
        registry.register_on_append("posts", posts_handler)
        registry.register_on_append("comments", comments_handler)
        
        assert "posts" in registry._on_append
        assert "comments" in registry._on_append
        assert posts_handler in registry._on_append["posts"]
        assert comments_handler in registry._on_append["comments"]
    
    def test_has_hooks_for_returns_true_when_hooks_exist(self):
        """has_hooks_for returns True when hooks exist."""
        registry = HookRegistry()
        registry.register_on_append("posts", lambda self, item: None)
        
        assert registry.has_hooks_for("posts") is True
    
    def test_has_hooks_for_returns_false_when_no_hooks(self):
        """has_hooks_for returns False when no hooks."""
        registry = HookRegistry()
        
        assert registry.has_hooks_for("posts") is False
    
    def test_get_hook_count(self):
        """get_hook_count returns correct count."""
        registry = HookRegistry()
        
        assert registry.get_hook_count() == 0
        
        registry.register_on_append("posts", lambda self, item: None)
        assert registry.get_hook_count() == 1
        
        registry.register_on_append("posts", lambda self, item: None)
        assert registry.get_hook_count() == 2
        
        registry.register_on_append("comments", lambda self, item: None)
        assert registry.get_hook_count() == 3


# =============================================================================
# Test: HookRegistry fire_on_append
# =============================================================================

class TestHookRegistryFireOnAppend:
    """Test HookRegistry.fire_on_append()."""
    
    def test_fire_calls_registered_hook(self):
        """fire_on_append calls registered hook."""
        registry = HookRegistry()
        called_with = []
        
        def handler(self, item):
            called_with.append((self, item))
        
        registry.register_on_append("posts", handler)
        
        owner = MockTable(id=1)
        post = MockPost(id=2)
        
        registry.fire_on_append(owner, "posts", post)
        
        assert len(called_with) == 1
        assert called_with[0][0] is owner
        assert called_with[0][1] is post
    
    def test_fire_calls_all_registered_hooks(self):
        """fire_on_append calls all registered hooks."""
        registry = HookRegistry()
        calls = []
        
        def handler1(self, item):
            calls.append("handler1")
        
        def handler2(self, item):
            calls.append("handler2")
        
        registry.register_on_append("posts", handler1)
        registry.register_on_append("posts", handler2)
        
        owner = MockTable(id=1)
        post = MockPost(id=2)
        
        registry.fire_on_append(owner, "posts", post)
        
        assert calls == ["handler1", "handler2"]
    
    def test_fire_does_nothing_for_unregistered_relationship(self):
        """fire_on_append does nothing for unregistered relationship."""
        registry = HookRegistry()
        calls = []
        
        def handler(self, item):
            calls.append("called")
        
        registry.register_on_append("posts", handler)
        
        # Fire for different relationship
        owner = MockTable(id=1)
        comment = MockComment(id=2)
        
        registry.fire_on_append(owner, "comments", comment)
        
        assert calls == []
    
    def test_fire_passes_correct_item(self):
        """fire_on_append passes the correct item."""
        registry = HookRegistry()
        received_items = []
        
        def handler(self, item):
            received_items.append(item)
        
        registry.register_on_append("posts", handler)
        
        owner = MockTable(id=1)
        post1 = MockPost(id=1)
        post2 = MockPost(id=2)
        
        registry.fire_on_append(owner, "posts", post1)
        registry.fire_on_append(owner, "posts", post2)
        
        assert received_items[0] is post1
        assert received_items[1] is post2


# =============================================================================
# Test: fire_on_append Convenience Function
# =============================================================================

class TestFireOnAppendFunction:
    """Test fire_on_append convenience function."""
    
    def test_fire_on_append_with_registered_hooks(self):
        """fire_on_append fires hooks from registry."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def handler(self, item):
            calls.append(("handler", self, item))
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=2)
        
        fire_on_append(owner, "posts", post)
        
        assert len(calls) == 1
        assert calls[0][0] == "handler"
        assert calls[0][1] is owner
        assert calls[0][2] is post
    
    def test_fire_on_append_no_hooks_doesnt_error(self):
        """fire_on_append with no hooks doesn't error."""
        class TestModel(MockTable):
            pass
        
        owner = TestModel(id=1)
        post = MockPost(id=2)
        
        # Should not raise
        fire_on_append(owner, "posts", post)


# =============================================================================
# Test: Discover Hooks
# =============================================================================

class TestDiscoverHooks:
    """Test discover_hooks function."""
    
    def test_discover_on_append_hook(self):
        """discover_hooks finds on_append decorated methods."""
        
        class TestModel(MockTable):
            @on_append("posts")
            def on_post_added(self, post):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert "posts" in registry._on_append
        assert len(registry._on_append["posts"]) == 1
    
    def test_discover_multiple_on_append_hooks(self):
        """discover_hooks finds multiple on_append hooks."""
        
        class TestModel(MockTable):
            @on_append("posts")
            def on_post_added(self, post):
                pass
            
            @on_append("comments")
            def on_comment_added(self, comment):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert "posts" in registry._on_append
        assert "comments" in registry._on_append
    
    def test_discover_multiple_hooks_same_relationship(self):
        """discover_hooks finds multiple hooks for same relationship."""
        
        class TestModel(MockTable):
            @on_append("posts")
            def on_post_added_1(self, post):
                pass
            
            @on_append("posts")
            def on_post_added_2(self, post):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert len(registry._on_append["posts"]) == 2


# =============================================================================
# Test: Hook Execution with Instance Data
# =============================================================================

class TestHookExecutionWithData:
    """Test hooks can access instance data."""
    
    def test_hook_can_access_owner_attributes(self):
        """Hook can access owner instance attributes."""
        
        class TestModel(MockTable):
            def __init__(self, id: int, name: str):
                super().__init__(id=id, name=name)
        
        accessed_data = []
        
        def handler(self, item):
            accessed_data.append({
                "owner_id": self.id,
                "owner_name": self.name,
                "item_id": item.id,
            })
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        owner = TestModel(id=5, name="TestUser")
        post = MockPost(id=10, title="Test Post")
        
        fire_on_append(owner, "posts", post)
        
        assert len(accessed_data) == 1
        assert accessed_data[0]["owner_id"] == 5
        assert accessed_data[0]["owner_name"] == "TestUser"
        assert accessed_data[0]["item_id"] == 10
    
    def test_hook_can_modify_item(self):
        """Hook can modify the appended item."""
        
        class TestModel(MockTable):
            pass
        
        def handler(self, item):
            item.modified_by_hook = True
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=2)
        
        fire_on_append(owner, "posts", post)
        
        assert hasattr(post, "modified_by_hook")
        assert post.modified_by_hook is True


# =============================================================================
# Test: Hook Error Handling
# =============================================================================

class TestHookErrorHandling:
    """Test hook error handling."""
    
    def test_hook_exception_propagates(self):
        """Hook exception propagates by default."""
        
        class TestModel(MockTable):
            pass
        
        def bad_handler(self, item):
            raise ValueError("Hook error")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", bad_handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=2)
        
        with pytest.raises(ValueError, match="Hook error"):
            fire_on_append(owner, "posts", post)
    
    def test_error_in_first_hook_prevents_subsequent_hooks(self):
        """Error in first hook prevents subsequent hooks from running."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def bad_handler(self, item):
            calls.append("bad")
            raise ValueError("Hook error")
        
        def good_handler(self, item):
            calls.append("good")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", bad_handler)
        registry.register_on_append("posts", good_handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=2)
        
        with pytest.raises(ValueError):
            fire_on_append(owner, "posts", post)
        
        # Only first hook was called
        assert calls == ["bad"]


# =============================================================================
# Test: Multiple Items
# =============================================================================

class TestMultipleItems:
    """Test hooks with multiple items."""
    
    def test_hook_called_for_each_item(self):
        """Hook is called once for each item."""
        
        class TestModel(MockTable):
            pass
        
        items_received = []
        
        def handler(self, item):
            items_received.append(item)
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        owner = TestModel(id=1)
        
        posts = [MockPost(id=i) for i in range(5)]
        for post in posts:
            fire_on_append(owner, "posts", post)
        
        assert len(items_received) == 5
        for i, post in enumerate(posts):
            assert items_received[i] is post


# =============================================================================
# Test: Different Owners
# =============================================================================

class TestDifferentOwners:
    """Test hooks with different owner instances."""
    
    def test_hook_receives_correct_owner(self):
        """Hook receives the correct owner for each call."""
        
        class TestModel(MockTable):
            pass
        
        owners_received = []
        
        def handler(self, item):
            owners_received.append(self)
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        owner1 = TestModel(id=1)
        owner2 = TestModel(id=2)
        post = MockPost(id=1)
        
        fire_on_append(owner1, "posts", post)
        fire_on_append(owner2, "posts", post)
        
        assert len(owners_received) == 2
        assert owners_received[0] is owner1
        assert owners_received[1] is owner2


# =============================================================================
# Test: Hook with Side Effects
# =============================================================================

class TestHookSideEffects:
    """Test hooks with side effects."""
    
    def test_hook_can_append_to_external_list(self):
        """Hook can append to external list."""
        
        class TestModel(MockTable):
            pass
        
        external_log = []
        
        def handler(self, item):
            external_log.append(f"Added {item.id} to {self.id}")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        owner = TestModel(id=100)
        post = MockPost(id=200)
        
        fire_on_append(owner, "posts", post)
        
        assert len(external_log) == 1
        assert external_log[0] == "Added 200 to 100"
    
    def test_hook_can_set_counter(self):
        """Hook can increment counter."""
        
        class Counter:
            value = 0
        
        class TestModel(MockTable):
            pass
        
        def handler(self, item):
            Counter.value += 1
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        owner = TestModel(id=1)
        
        for i in range(10):
            fire_on_append(owner, "posts", MockPost(id=i))
        
        assert Counter.value == 10


# =============================================================================
# Test: Hook Registry Merge (Inheritance)
# =============================================================================

class TestHookRegistryMerge:
    """Test HookRegistry.merge_from for inheritance."""
    
    def test_merge_on_append_hooks(self):
        """merge_from copies on_append hooks."""
        parent_registry = HookRegistry()
        child_registry = HookRegistry()
        
        def parent_handler(self, item):
            pass
        
        parent_registry.register_on_append("posts", parent_handler)
        child_registry.merge_from(parent_registry)
        
        assert "posts" in child_registry._on_append
        assert parent_handler in child_registry._on_append["posts"]
    
    def test_merge_preserves_existing_hooks(self):
        """merge_from preserves existing hooks."""
        parent_registry = HookRegistry()
        child_registry = HookRegistry()
        
        def parent_handler(self, item):
            pass
        
        def child_handler(self, item):
            pass
        
        parent_registry.register_on_append("posts", parent_handler)
        child_registry.register_on_append("posts", child_handler)
        
        child_registry.merge_from(parent_registry)
        
        assert len(child_registry._on_append["posts"]) == 2
        assert child_handler in child_registry._on_append["posts"]
        assert parent_handler in child_registry._on_append["posts"]


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestOnAppendEdgeCases:
    """Test edge cases for on_append hooks."""
    
    def test_hook_with_none_item(self):
        """Hook works with None item."""
        
        class TestModel(MockTable):
            pass
        
        received = []
        
        def handler(self, item):
            received.append(item)
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        owner = TestModel(id=1)
        fire_on_append(owner, "posts", None)
        
        assert received == [None]
    
    def test_hook_with_empty_relationship_name(self):
        """Hook works with empty relationship name."""
        
        @on_append("")
        def handler(self, item):
            pass
        
        assert handler._pynext_hook.relationship == ""
    
    def test_hook_with_special_characters_in_relationship(self):
        """Hook works with special characters in relationship name."""
        
        @on_append("my_posts_123")
        def handler(self, item):
            pass
        
        assert handler._pynext_hook.relationship == "my_posts_123"
    
    def test_multiple_decorators_on_same_function(self):
        """Multiple on_append decorators on same function takes last one."""
        
        @on_append("comments")
        @on_append("posts")
        def handler(self, item):
            pass
        
        # The outer decorator (comments) wins
        assert handler._pynext_hook.relationship == "comments"


# =============================================================================
# Test: Performance
# =============================================================================

class TestOnAppendPerformance:
    """Test performance characteristics of on_append hooks."""
    
    def test_no_hooks_minimal_overhead(self):
        """No hooks means minimal overhead."""
        import time
        
        class TestModel(MockTable):
            pass
        
        owner = TestModel(id=1)
        post = MockPost(id=1)
        
        start = time.perf_counter()
        for _ in range(1000):
            fire_on_append(owner, "posts", post)
        elapsed = time.perf_counter() - start
        
        # Should be very fast (less than 0.1 seconds for 1000 calls)
        assert elapsed < 0.1
    
    def test_with_hooks_reasonable_overhead(self):
        """With hooks, overhead is still reasonable."""
        import time
        
        class TestModel(MockTable):
            pass
        
        def handler(self, item):
            pass
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", handler)
        
        owner = TestModel(id=1)
        post = MockPost(id=1)
        
        start = time.perf_counter()
        for _ in range(1000):
            fire_on_append(owner, "posts", post)
        elapsed = time.perf_counter() - start
        
        # Should still be very fast (less than 0.2 seconds for 1000 calls)
        assert elapsed < 0.2

