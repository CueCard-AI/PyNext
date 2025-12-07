"""
Tests for edge cases, inheritance, and multiple hooks.

Tests:
- Hook inheritance in subclasses
- Multiple hooks per relationship
- Edge cases and corner scenarios
- Hook decorator combinations
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
)
from pynext.db.relationships.hook_executor import (
    fire_on_append,
    fire_on_remove,
    fire_on_set,
    fire_before_delete,
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
# Test: Inheritance
# =============================================================================

class TestHookInheritance:
    """Test hook inheritance in subclasses."""
    
    def test_parent_hooks_available_in_child(self):
        """Parent hooks are inherited by child."""
        parent_calls = []
        
        class ParentModel(MockTable):
            @on_append("posts")
            def on_post_added(self, post):
                parent_calls.append("parent")
        
        class ChildModel(ParentModel):
            pass
        
        discover_hooks(ParentModel)
        discover_hooks(ChildModel)
        
        # Parent registry gets merged into child
        child_registry = get_hook_registry(ChildModel)
        child_registry.merge_from(get_hook_registry(ParentModel))
        
        child = ChildModel(id=1)
        fire_on_append(child, "posts", MockPost(id=1))
        
        assert "parent" in parent_calls
    
    def test_child_can_add_hooks(self):
        """Child can add its own hooks."""
        calls = []
        
        class ParentModel(MockTable):
            @on_append("posts")
            def parent_hook(self, post):
                calls.append("parent")
        
        class ChildModel(ParentModel):
            @on_append("posts")
            def child_hook(self, post):
                calls.append("child")
        
        discover_hooks(ParentModel)
        discover_hooks(ChildModel)
        
        child_registry = get_hook_registry(ChildModel)
        child_registry.merge_from(get_hook_registry(ParentModel))
        
        child = ChildModel(id=1)
        fire_on_append(child, "posts", MockPost(id=1))
        
        assert "parent" in calls
        assert "child" in calls
    
    def test_grandchild_inheritance(self):
        """Hooks are inherited through multiple levels."""
        calls = []
        
        class GrandparentModel(MockTable):
            @on_append("posts")
            def grandparent_hook(self, post):
                calls.append("grandparent")
        
        class ParentModel(GrandparentModel):
            @on_append("posts")
            def parent_hook(self, post):
                calls.append("parent")
        
        class ChildModel(ParentModel):
            @on_append("posts")
            def child_hook(self, post):
                calls.append("child")
        
        discover_hooks(GrandparentModel)
        discover_hooks(ParentModel)
        discover_hooks(ChildModel)
        
        # Merge parent into child
        child_registry = get_hook_registry(ChildModel)
        child_registry.merge_from(get_hook_registry(ParentModel))
        child_registry.merge_from(get_hook_registry(GrandparentModel))
        
        child = ChildModel(id=1)
        fire_on_append(child, "posts", MockPost(id=1))
        
        assert "grandparent" in calls
        assert "parent" in calls
        assert "child" in calls


# =============================================================================
# Test: Multiple Hooks
# =============================================================================

class TestMultipleHooks:
    """Test multiple hooks per relationship."""
    
    def test_multiple_on_append_hooks(self):
        """Multiple on_append hooks for same relationship."""
        calls = []
        
        class TestModel(MockTable):
            @on_append("posts")
            def hook1(self, post):
                calls.append("hook1")
            
            @on_append("posts")
            def hook2(self, post):
                calls.append("hook2")
            
            @on_append("posts")
            def hook3(self, post):
                calls.append("hook3")
        
        discover_hooks(TestModel)
        
        owner = TestModel(id=1)
        fire_on_append(owner, "posts", MockPost(id=1))
        
        assert len(calls) == 3
    
    def test_hooks_for_different_relationships(self):
        """Hooks for different relationships are independent."""
        calls = []
        
        class TestModel(MockTable):
            @on_append("posts")
            def posts_hook(self, item):
                calls.append("posts")
            
            @on_append("comments")
            def comments_hook(self, item):
                calls.append("comments")
            
            @on_append("tags")
            def tags_hook(self, item):
                calls.append("tags")
        
        discover_hooks(TestModel)
        
        owner = TestModel(id=1)
        fire_on_append(owner, "posts", MockPost(id=1))
        
        assert calls == ["posts"]
    
    def test_multiple_hook_types_same_relationship(self):
        """Different hook types for same relationship."""
        calls = []
        
        class TestModel(MockTable):
            @on_append("posts")
            def on_added(self, item):
                calls.append("added")
            
            @on_remove("posts")
            def on_removed(self, item):
                calls.append("removed")
        
        discover_hooks(TestModel)
        
        owner = TestModel(id=1)
        post = MockPost(id=1)
        
        fire_on_append(owner, "posts", post)
        fire_on_remove(owner, "posts", post)
        
        assert calls == ["added", "removed"]


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and corner scenarios."""
    
    def test_empty_relationship_name(self):
        """Hook with empty relationship name."""
        
        @on_append("")
        def handler(self, item):
            pass
        
        assert handler._pynext_hook.relationship == ""
    
    def test_special_characters_in_relationship(self):
        """Hook with special characters in relationship name."""
        
        @on_append("my_posts_123")
        def handler(self, item):
            pass
        
        assert handler._pynext_hook.relationship == "my_posts_123"
    
    def test_unicode_relationship_name(self):
        """Hook with unicode relationship name."""
        
        @on_append("投稿")
        def handler(self, item):
            pass
        
        assert handler._pynext_hook.relationship == "投稿"
    
    def test_very_long_relationship_name(self):
        """Hook with very long relationship name."""
        long_name = "a" * 1000
        
        @on_append(long_name)
        def handler(self, item):
            pass
        
        assert handler._pynext_hook.relationship == long_name
    
    def test_hook_with_none_item(self):
        """Hook handles None item."""
        
        class TestModel(MockTable):
            pass
        
        received = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", lambda s, i: received.append(i))
        
        owner = TestModel(id=1)
        fire_on_append(owner, "posts", None)
        
        assert received == [None]
    
    def test_hook_with_empty_list_item(self):
        """Hook handles empty list as item."""
        
        class TestModel(MockTable):
            pass
        
        received = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("items", lambda s, i: received.append(i))
        
        owner = TestModel(id=1)
        fire_on_append(owner, "items", [])
        
        assert received == [[]]
    
    def test_hook_with_dict_item(self):
        """Hook handles dict as item."""
        
        class TestModel(MockTable):
            pass
        
        received = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("items", lambda s, i: received.append(i))
        
        owner = TestModel(id=1)
        fire_on_append(owner, "items", {"key": "value"})
        
        assert received == [{"key": "value"}]
    
    def test_hook_modifies_item(self):
        """Hook can modify the item."""
        
        class TestModel(MockTable):
            pass
        
        def modifier_hook(self, item):
            item.modified = True
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", modifier_hook)
        
        owner = TestModel(id=1)
        post = MockPost(id=1)
        
        fire_on_append(owner, "posts", post)
        
        assert post.modified is True
    
    def test_hook_modifies_owner(self):
        """Hook can modify the owner."""
        
        class TestModel(MockTable):
            pass
        
        def modifier_hook(self, item):
            self.post_count = getattr(self, "post_count", 0) + 1
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", modifier_hook)
        
        owner = TestModel(id=1)
        
        fire_on_append(owner, "posts", MockPost(id=1))
        fire_on_append(owner, "posts", MockPost(id=2))
        
        assert owner.post_count == 2


# =============================================================================
# Test: Hook Decorator Combinations
# =============================================================================

class TestDecoratorCombinations:
    """Test hook decorator combinations."""
    
    def test_stacked_decorators_same_relationship(self):
        """Stacked decorators on same function."""
        
        # This should only take the outermost decorator
        @on_append("posts")
        @on_remove("posts")
        def handler(self, item):
            pass
        
        # Only the outer decorator (on_append) applies
        assert handler._pynext_hook.type == HookType.ON_APPEND
    
    def test_same_function_different_relationships(self):
        """Same function registered for different relationships."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def universal_hook(self, item):
            calls.append(item.id)
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", universal_hook)
        registry.register_on_append("comments", universal_hook)
        registry.register_on_append("tags", universal_hook)
        
        owner = TestModel(id=1)
        
        fire_on_append(owner, "posts", MockPost(id=1))
        fire_on_append(owner, "comments", MockPost(id=2))
        fire_on_append(owner, "tags", MockPost(id=3))
        
        assert calls == [1, 2, 3]
    
    def test_hook_with_default_args(self):
        """Hook function with default arguments."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def hook_with_defaults(self, item, extra="default"):
            calls.append((item.id, extra))
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", hook_with_defaults)
        
        owner = TestModel(id=1)
        fire_on_append(owner, "posts", MockPost(id=1))
        
        assert calls == [(1, "default")]
    
    def test_hook_lambda(self):
        """Lambda as hook."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", lambda s, i: calls.append(i.id))
        
        owner = TestModel(id=1)
        fire_on_append(owner, "posts", MockPost(id=42))
        
        assert calls == [42]


# =============================================================================
# Test: State and Side Effects
# =============================================================================

class TestStateAndSideEffects:
    """Test hooks with state and side effects."""
    
    def test_hook_with_closure(self):
        """Hook with closure captures state."""
        
        class TestModel(MockTable):
            pass
        
        counter = {"value": 0}
        
        def make_counter_hook():
            def hook(self, item):
                counter["value"] += 1
            return hook
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", make_counter_hook())
        
        owner = TestModel(id=1)
        
        for _ in range(5):
            fire_on_append(owner, "posts", MockPost(id=1))
        
        assert counter["value"] == 5
    
    def test_hook_appends_to_external_list(self):
        """Hook appends to external list."""
        
        class TestModel(MockTable):
            pass
        
        audit_log = []
        
        def audit_hook(self, item):
            audit_log.append({
                "owner_id": self.id,
                "item_id": item.id,
            })
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", audit_hook)
        
        owner = TestModel(id=100)
        
        fire_on_append(owner, "posts", MockPost(id=1))
        fire_on_append(owner, "posts", MockPost(id=2))
        
        assert len(audit_log) == 2
        assert audit_log[0]["owner_id"] == 100
        assert audit_log[0]["item_id"] == 1
    
    def test_hook_raises_stops_side_effects(self):
        """Error in hook stops subsequent side effects."""
        
        class TestModel(MockTable):
            pass
        
        effects = []
        
        def effect1(self, item):
            effects.append("effect1")
        
        def bad_hook(self, item):
            raise ValueError("Error")
        
        def effect2(self, item):
            effects.append("effect2")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", effect1)
        registry.register_on_append("posts", bad_hook)
        registry.register_on_append("posts", effect2)
        
        owner = TestModel(id=1)
        
        with pytest.raises(ValueError):
            fire_on_append(owner, "posts", MockPost(id=1))
        
        assert effects == ["effect1"]


# =============================================================================
# Test: Different Instance Types
# =============================================================================

class TestDifferentInstanceTypes:
    """Test hooks with different instance types."""
    
    def test_hook_with_different_owner_types(self):
        """Same hook type works with different owners."""
        
        class ModelA(MockTable):
            pass
        
        class ModelB(MockTable):
            pass
        
        calls_a = []
        calls_b = []
        
        get_hook_registry(ModelA).register_on_append("posts", lambda s, i: calls_a.append(s.id))
        get_hook_registry(ModelB).register_on_append("posts", lambda s, i: calls_b.append(s.id))
        
        owner_a = ModelA(id=1)
        owner_b = ModelB(id=2)
        
        fire_on_append(owner_a, "posts", MockPost(id=1))
        fire_on_append(owner_b, "posts", MockPost(id=2))
        
        assert calls_a == [1]
        assert calls_b == [2]


# =============================================================================
# Test: Thread Safety (Basic)
# =============================================================================

class TestThreadSafetyBasic:
    """Basic thread safety tests."""
    
    def test_concurrent_fires_same_relationship(self):
        """Concurrent fires on same relationship."""
        import threading
        
        class TestModel(MockTable):
            pass
        
        calls = []
        lock = threading.Lock()
        
        def hook(self, item):
            with lock:
                calls.append(item.id)
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", hook)
        
        owner = TestModel(id=1)
        
        def fire_many(start_id):
            for i in range(10):
                fire_on_append(owner, "posts", MockPost(id=start_id + i))
        
        threads = [
            threading.Thread(target=fire_many, args=(0,)),
            threading.Thread(target=fire_many, args=(100,)),
            threading.Thread(target=fire_many, args=(200,)),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(calls) == 30


# =============================================================================
# Test: Memory / Reference
# =============================================================================

class TestMemoryReferences:
    """Test memory and reference handling."""
    
    def test_hook_doesnt_prevent_gc(self):
        """Hook registration doesn't prevent garbage collection."""
        import gc
        import weakref
        
        class TestModel(MockTable):
            pass
        
        def hook(self, item):
            pass
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", hook)
        
        owner = TestModel(id=1)
        owner_ref = weakref.ref(owner)
        
        fire_on_append(owner, "posts", MockPost(id=1))
        
        del owner
        gc.collect()
        
        # Owner should be collected (hook doesn't hold reference)
        assert owner_ref() is None

