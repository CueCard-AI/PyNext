"""
Tests for @before_delete relationship hooks.

Tests the before_delete decorator and its integration with cascade deletion.
"""

import pytest
from typing import List, Optional, Any

from pynext.db.relationships.hooks import (
    HookType,
    HookConfig,
    HookRegistry,
    before_delete,
    get_hook_registry,
    reset_hook_registries,
    discover_hooks,
)
from pynext.db.relationships.hook_executor import (
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


class MockUser(MockTable):
    """Mock user for testing."""
    __table_name__ = "users"
    
    def __init__(self, id: int = 1, name: str = "Test User", email: str = "test@test.com"):
        super().__init__(id=id, name=name, email=email)


class MockPost(MockTable):
    """Mock post for testing."""
    __table_name__ = "posts"
    
    def __init__(self, id: int = 1, title: str = "Test Post"):
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
# Test: @before_delete Decorator Basic
# =============================================================================

class TestBeforeDeleteDecoratorBasic:
    """Test basic @before_delete decorator functionality."""
    
    def test_decorator_marks_function(self):
        """before_delete decorator marks function with hook config."""
        @before_delete()
        def handler(self):
            pass
        
        assert hasattr(handler, "_pynext_hook")
        assert handler._pynext_hook.type == HookType.BEFORE_DELETE
        assert handler._pynext_hook.relationship is None
    
    def test_decorator_preserves_function_name(self):
        """before_delete decorator preserves function name."""
        @before_delete()
        def my_cleanup_handler(self):
            pass
        
        assert my_cleanup_handler.__name__ == "my_cleanup_handler"
    
    def test_decorator_with_priority(self):
        """before_delete decorator accepts priority parameter."""
        @before_delete(priority=10)
        def handler(self):
            pass
        
        assert handler._pynext_hook.priority == 10
    
    def test_decorator_default_priority_is_zero(self):
        """Default priority is 0."""
        @before_delete()
        def handler(self):
            pass
        
        assert handler._pynext_hook.priority == 0
    
    def test_decorator_no_relationship(self):
        """before_delete has no relationship (applies to whole instance)."""
        @before_delete()
        def handler(self):
            pass
        
        assert handler._pynext_hook.relationship is None


# =============================================================================
# Test: HookRegistry before_delete Registration
# =============================================================================

class TestHookRegistryBeforeDelete:
    """Test HookRegistry before_delete registration."""
    
    def test_register_single_hook(self):
        """Register single before_delete hook."""
        registry = HookRegistry()
        
        def handler(self):
            pass
        
        registry.register_before_delete(handler)
        
        assert len(registry._before_delete) == 1
        assert handler in registry._before_delete
    
    def test_register_multiple_hooks(self):
        """Register multiple before_delete hooks."""
        registry = HookRegistry()
        
        def handler1(self):
            pass
        
        def handler2(self):
            pass
        
        registry.register_before_delete(handler1)
        registry.register_before_delete(handler2)
        
        assert len(registry._before_delete) == 2
        assert handler1 in registry._before_delete
        assert handler2 in registry._before_delete
    
    def test_get_hook_count_includes_before_delete(self):
        """get_hook_count includes before_delete hooks."""
        registry = HookRegistry()
        
        assert registry.get_hook_count() == 0
        
        registry.register_before_delete(lambda self: None)
        assert registry.get_hook_count() == 1
        
        registry.register_before_delete(lambda self: None)
        assert registry.get_hook_count() == 2


# =============================================================================
# Test: HookRegistry fire_before_delete
# =============================================================================

class TestHookRegistryFireBeforeDelete:
    """Test HookRegistry.fire_before_delete()."""
    
    def test_fire_calls_registered_hook(self):
        """fire_before_delete calls registered hook."""
        registry = HookRegistry()
        called_with = []
        
        def handler(self):
            called_with.append(self)
        
        registry.register_before_delete(handler)
        
        user = MockUser(id=1)
        
        registry.fire_before_delete(user)
        
        assert len(called_with) == 1
        assert called_with[0] is user
    
    def test_fire_calls_all_registered_hooks(self):
        """fire_before_delete calls all registered hooks."""
        registry = HookRegistry()
        calls = []
        
        def handler1(self):
            calls.append("handler1")
        
        def handler2(self):
            calls.append("handler2")
        
        registry.register_before_delete(handler1)
        registry.register_before_delete(handler2)
        
        user = MockUser(id=1)
        
        registry.fire_before_delete(user)
        
        assert calls == ["handler1", "handler2"]
    
    def test_fire_does_nothing_when_no_hooks(self):
        """fire_before_delete does nothing when no hooks registered."""
        registry = HookRegistry()
        
        user = MockUser(id=1)
        
        # Should not raise
        registry.fire_before_delete(user)


# =============================================================================
# Test: fire_before_delete Convenience Function
# =============================================================================

class TestFireBeforeDeleteFunction:
    """Test fire_before_delete convenience function."""
    
    def test_fire_before_delete_with_registered_hooks(self):
        """fire_before_delete fires hooks from registry."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def handler(self):
            calls.append(("handler", self))
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        instance = TestModel(id=1, name="Test")
        
        fire_before_delete(instance)
        
        assert len(calls) == 1
        assert calls[0][0] == "handler"
        assert calls[0][1] is instance
    
    def test_fire_before_delete_no_hooks_doesnt_error(self):
        """fire_before_delete with no hooks doesn't error."""
        class TestModel(MockTable):
            pass
        
        instance = TestModel(id=1)
        
        # Should not raise
        fire_before_delete(instance)


# =============================================================================
# Test: Discover Hooks
# =============================================================================

class TestDiscoverBeforeDeleteHooks:
    """Test discover_hooks function for before_delete."""
    
    def test_discover_before_delete_hook(self):
        """discover_hooks finds before_delete decorated methods."""
        
        class TestModel(MockTable):
            @before_delete()
            def cleanup(self):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert len(registry._before_delete) == 1
    
    def test_discover_multiple_before_delete_hooks(self):
        """discover_hooks finds multiple before_delete hooks."""
        
        class TestModel(MockTable):
            @before_delete()
            def cleanup1(self):
                pass
            
            @before_delete()
            def cleanup2(self):
                pass
        
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert len(registry._before_delete) == 2


# =============================================================================
# Test: Common Use Cases
# =============================================================================

class TestBeforeDeleteUseCases:
    """Test common use cases for before_delete hooks."""
    
    def test_archive_before_delete(self):
        """Hook can archive data before deletion."""
        
        class TestModel(MockTable):
            pass
        
        archive = []
        
        def handler(self):
            archive.append({
                "id": self.id,
                "name": self.name,
                "archived_at": "now",
            })
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        user = TestModel(id=42, name="John Doe")
        
        fire_before_delete(user)
        
        assert len(archive) == 1
        assert archive[0]["id"] == 42
        assert archive[0]["name"] == "John Doe"
    
    def test_send_notification_before_delete(self):
        """Hook can send notification before deletion."""
        
        class TestModel(MockTable):
            pass
        
        notifications = []
        
        def handler(self):
            notifications.append(f"User {self.id} is being deleted")
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        user = TestModel(id=100)
        
        fire_before_delete(user)
        
        assert notifications == ["User 100 is being deleted"]
    
    def test_cleanup_external_resources(self):
        """Hook can cleanup external resources."""
        
        class TestModel(MockTable):
            pass
        
        cleanup_log = []
        
        def handler(self):
            cleanup_log.append(f"cleanup_files_{self.id}")
            cleanup_log.append(f"cleanup_cache_{self.id}")
            cleanup_log.append(f"cleanup_sessions_{self.id}")
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        user = TestModel(id=5)
        
        fire_before_delete(user)
        
        assert cleanup_log == [
            "cleanup_files_5",
            "cleanup_cache_5",
            "cleanup_sessions_5",
        ]
    
    def test_audit_log_before_delete(self):
        """Hook can create audit log entry."""
        
        class TestModel(MockTable):
            pass
        
        audit_log = []
        
        def handler(self):
            audit_log.append({
                "action": "delete",
                "entity_type": "user",
                "entity_id": self.id,
                "entity_data": {"name": self.name, "email": self.email},
            })
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        user = TestModel(id=1, name="Alice", email="alice@example.com")
        
        fire_before_delete(user)
        
        assert len(audit_log) == 1
        assert audit_log[0]["action"] == "delete"
        assert audit_log[0]["entity_id"] == 1


# =============================================================================
# Test: Hook Execution Order
# =============================================================================

class TestBeforeDeleteOrder:
    """Test before_delete hook execution order."""
    
    def test_hooks_execute_in_registration_order(self):
        """Hooks execute in the order they were registered."""
        
        class TestModel(MockTable):
            pass
        
        order = []
        
        def handler1(self):
            order.append(1)
        
        def handler2(self):
            order.append(2)
        
        def handler3(self):
            order.append(3)
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler1)
        registry.register_before_delete(handler2)
        registry.register_before_delete(handler3)
        
        instance = TestModel(id=1)
        
        fire_before_delete(instance)
        
        assert order == [1, 2, 3]


# =============================================================================
# Test: Hook Error Handling
# =============================================================================

class TestBeforeDeleteErrorHandling:
    """Test before_delete hook error handling."""
    
    def test_hook_exception_propagates(self):
        """Hook exception propagates by default."""
        
        class TestModel(MockTable):
            pass
        
        def bad_handler(self):
            raise ValueError("Cleanup failed")
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(bad_handler)
        
        instance = TestModel(id=1)
        
        with pytest.raises(ValueError, match="Cleanup failed"):
            fire_before_delete(instance)
    
    def test_error_in_first_hook_prevents_subsequent(self):
        """Error in first hook prevents subsequent hooks from running."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def bad_handler(self):
            calls.append("bad")
            raise ValueError("Error")
        
        def good_handler(self):
            calls.append("good")
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(bad_handler)
        registry.register_before_delete(good_handler)
        
        instance = TestModel(id=1)
        
        with pytest.raises(ValueError):
            fire_before_delete(instance)
        
        assert calls == ["bad"]


# =============================================================================
# Test: Hook Access to Instance Data
# =============================================================================

class TestBeforeDeleteInstanceAccess:
    """Test before_delete hooks can access instance data."""
    
    def test_hook_accesses_all_attributes(self):
        """Hook can access all instance attributes."""
        
        class TestModel(MockTable):
            pass
        
        captured = []
        
        def handler(self):
            captured.append({
                "id": self.id,
                "name": self.name,
                "email": self.email,
                "is_active": self.is_active,
            })
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        user = TestModel(
            id=123,
            name="Bob Smith",
            email="bob@smith.com",
            is_active=True,
        )
        
        fire_before_delete(user)
        
        assert len(captured) == 1
        assert captured[0]["id"] == 123
        assert captured[0]["name"] == "Bob Smith"
        assert captured[0]["email"] == "bob@smith.com"
        assert captured[0]["is_active"] is True


# =============================================================================
# Test: Hook Registry Merge (Inheritance)
# =============================================================================

class TestBeforeDeleteHookRegistryMerge:
    """Test HookRegistry.merge_from for before_delete hooks."""
    
    def test_merge_before_delete_hooks(self):
        """merge_from copies before_delete hooks."""
        parent_registry = HookRegistry()
        child_registry = HookRegistry()
        
        def parent_handler(self):
            pass
        
        parent_registry.register_before_delete(parent_handler)
        child_registry.merge_from(parent_registry)
        
        assert len(child_registry._before_delete) == 1
        assert parent_handler in child_registry._before_delete
    
    def test_merge_preserves_existing_hooks(self):
        """merge_from preserves existing before_delete hooks."""
        parent_registry = HookRegistry()
        child_registry = HookRegistry()
        
        def parent_handler(self):
            pass
        
        def child_handler(self):
            pass
        
        parent_registry.register_before_delete(parent_handler)
        child_registry.register_before_delete(child_handler)
        
        child_registry.merge_from(parent_registry)
        
        assert len(child_registry._before_delete) == 2


# =============================================================================
# Test: Multiple Deletions
# =============================================================================

class TestBeforeDeleteMultiple:
    """Test before_delete with multiple instances."""
    
    def test_hook_called_for_each_instance(self):
        """Hook is called for each deleted instance."""
        
        class TestModel(MockTable):
            pass
        
        deleted_ids = []
        
        def handler(self):
            deleted_ids.append(self.id)
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        for i in range(5):
            instance = TestModel(id=i)
            fire_before_delete(instance)
        
        assert deleted_ids == [0, 1, 2, 3, 4]


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestBeforeDeleteEdgeCases:
    """Test edge cases for before_delete hooks."""
    
    def test_hook_with_no_instance_attributes(self):
        """Hook works with minimal instance."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def handler(self):
            calls.append("called")
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        # Instance with no custom attributes
        instance = TestModel()
        
        fire_before_delete(instance)
        
        assert calls == ["called"]
    
    def test_multiple_before_delete_decorators(self):
        """Multiple before_delete decorators work independently."""
        
        class TestModel(MockTable):
            @before_delete()
            def cleanup1(self):
                pass
            
            @before_delete()
            def cleanup2(self):
                pass
        
        # Both should be discovered
        discover_hooks(TestModel)
        
        registry = get_hook_registry(TestModel)
        assert len(registry._before_delete) == 2


# =============================================================================
# Test: Performance
# =============================================================================

class TestBeforeDeletePerformance:
    """Test performance of before_delete hooks."""
    
    def test_no_hooks_minimal_overhead(self):
        """No hooks means minimal overhead."""
        import time
        
        class TestModel(MockTable):
            pass
        
        instance = TestModel(id=1)
        
        start = time.perf_counter()
        for _ in range(1000):
            fire_before_delete(instance)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    def test_with_hooks_reasonable_overhead(self):
        """With hooks, overhead is still reasonable."""
        import time
        
        class TestModel(MockTable):
            pass
        
        def handler(self):
            pass
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(handler)
        
        instance = TestModel(id=1)
        
        start = time.perf_counter()
        for _ in range(1000):
            fire_before_delete(instance)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.2

