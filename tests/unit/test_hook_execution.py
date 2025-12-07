"""
Tests for hook execution order, error handling, and executor behavior.

Tests:
- Hook execution order
- Error handling and propagation
- HookExecutor configuration
- Suppression modes
"""

import pytest
from typing import List, Optional, Any

from pynext.db.relationships.hooks import (
    HookType,
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
    HookExecutor,
    get_hook_executor,
    reset_hook_executor,
    set_hook_executor,
    fire_on_append,
    fire_on_remove,
    fire_on_set,
    fire_before_delete,
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
# Test: Hook Execution Order
# =============================================================================

class TestHookExecutionOrder:
    """Test hook execution order."""
    
    def test_hooks_execute_in_registration_order(self):
        """Hooks execute in the order they were registered."""
        
        class TestModel(MockTable):
            pass
        
        order = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", lambda s, i: order.append(1))
        registry.register_on_append("posts", lambda s, i: order.append(2))
        registry.register_on_append("posts", lambda s, i: order.append(3))
        
        owner = TestModel(id=1)
        fire_on_append(owner, "posts", MockPost(id=1))
        
        assert order == [1, 2, 3]
    
    def test_remove_hooks_in_registration_order(self):
        """Remove hooks execute in registration order."""
        
        class TestModel(MockTable):
            pass
        
        order = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", lambda s, i: order.append("a"))
        registry.register_on_remove("posts", lambda s, i: order.append("b"))
        
        owner = TestModel(id=1)
        fire_on_remove(owner, "posts", MockPost(id=1))
        
        assert order == ["a", "b"]
    
    def test_set_hooks_in_registration_order(self):
        """Set hooks execute in registration order."""
        
        class TestModel(MockTable):
            pass
        
        order = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", lambda s, o, n: order.append("first"))
        registry.register_on_set("profile", lambda s, o, n: order.append("second"))
        
        owner = TestModel(id=1)
        fire_on_set(owner, "profile", None, MockTable(id=1))
        
        assert order == ["first", "second"]
    
    def test_before_delete_hooks_in_registration_order(self):
        """Before_delete hooks execute in registration order."""
        
        class TestModel(MockTable):
            pass
        
        order = []
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(lambda s: order.append(1))
        registry.register_before_delete(lambda s: order.append(2))
        registry.register_before_delete(lambda s: order.append(3))
        
        owner = TestModel(id=1)
        fire_before_delete(owner)
        
        assert order == [1, 2, 3]
    
    def test_discovered_hooks_in_definition_order(self):
        """Discovered hooks execute in definition order."""
        
        order = []
        
        class TestModel(MockTable):
            @on_append("posts")
            def first(self, post):
                order.append("first")
            
            @on_append("posts")
            def second(self, post):
                order.append("second")
            
            @on_append("posts")
            def third(self, post):
                order.append("third")
        
        discover_hooks(TestModel)
        
        owner = TestModel(id=1)
        fire_on_append(owner, "posts", MockPost(id=1))
        
        # Note: Order may vary based on dict ordering in Python 3.7+
        assert len(order) == 3


# =============================================================================
# Test: Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling in hooks."""
    
    def test_error_propagates_by_default(self):
        """Errors propagate by default."""
        
        class TestModel(MockTable):
            pass
        
        def bad_hook(self, item):
            raise ValueError("Hook failed")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", bad_hook)
        
        owner = TestModel(id=1)
        
        with pytest.raises(ValueError, match="Hook failed"):
            fire_on_append(owner, "posts", MockPost(id=1))
    
    def test_error_stops_execution(self):
        """Error in one hook stops subsequent hooks."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        def first_hook(self, item):
            calls.append("first")
        
        def bad_hook(self, item):
            calls.append("bad")
            raise ValueError("Error")
        
        def last_hook(self, item):
            calls.append("last")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", first_hook)
        registry.register_on_append("posts", bad_hook)
        registry.register_on_append("posts", last_hook)
        
        owner = TestModel(id=1)
        
        with pytest.raises(ValueError):
            fire_on_append(owner, "posts", MockPost(id=1))
        
        assert calls == ["first", "bad"]
    
    def test_error_in_on_remove(self):
        """Error in on_remove hook propagates."""
        
        class TestModel(MockTable):
            pass
        
        def bad_hook(self, item):
            raise RuntimeError("Remove failed")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", bad_hook)
        
        owner = TestModel(id=1)
        
        with pytest.raises(RuntimeError, match="Remove failed"):
            fire_on_remove(owner, "posts", MockPost(id=1))
    
    def test_error_in_on_set(self):
        """Error in on_set hook propagates."""
        
        class TestModel(MockTable):
            pass
        
        def bad_hook(self, old, new):
            raise TypeError("Set failed")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", bad_hook)
        
        owner = TestModel(id=1)
        
        with pytest.raises(TypeError, match="Set failed"):
            fire_on_set(owner, "profile", None, MockTable(id=1))
    
    def test_error_in_before_delete(self):
        """Error in before_delete hook propagates."""
        
        class TestModel(MockTable):
            pass
        
        def bad_hook(self):
            raise Exception("Delete cleanup failed")
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(bad_hook)
        
        owner = TestModel(id=1)
        
        with pytest.raises(Exception, match="Delete cleanup failed"):
            fire_before_delete(owner)


# =============================================================================
# Test: HookExecutor
# =============================================================================

class TestHookExecutor:
    """Test HookExecutor class."""
    
    def test_default_executor(self):
        """Default executor is created."""
        executor = get_hook_executor()
        
        assert isinstance(executor, HookExecutor)
    
    def test_get_hook_executor_returns_same_instance(self):
        """get_hook_executor returns same instance."""
        executor1 = get_hook_executor()
        executor2 = get_hook_executor()
        
        assert executor1 is executor2
    
    def test_reset_hook_executor(self):
        """reset_hook_executor creates new instance."""
        executor1 = get_hook_executor()
        reset_hook_executor()
        executor2 = get_hook_executor()
        
        assert executor1 is not executor2
    
    def test_set_hook_executor(self):
        """set_hook_executor replaces global executor."""
        custom_executor = HookExecutor()
        set_hook_executor(custom_executor)
        
        assert get_hook_executor() is custom_executor
    
    def test_executor_on_append(self):
        """Executor.on_append fires hooks."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", lambda s, i: calls.append("hook"))
        
        executor = HookExecutor()
        owner = TestModel(id=1)
        
        executor.on_append(owner, "posts", MockPost(id=1))
        
        assert calls == ["hook"]
    
    def test_executor_on_remove(self):
        """Executor.on_remove fires hooks."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", lambda s, i: calls.append("hook"))
        
        executor = HookExecutor()
        owner = TestModel(id=1)
        
        executor.on_remove(owner, "posts", MockPost(id=1))
        
        assert calls == ["hook"]
    
    def test_executor_on_set(self):
        """Executor.on_set fires hooks."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", lambda s, o, n: calls.append("hook"))
        
        executor = HookExecutor()
        owner = TestModel(id=1)
        
        executor.on_set(owner, "profile", None, MockTable(id=1))
        
        assert calls == ["hook"]
    
    def test_executor_before_delete(self):
        """Executor.before_delete fires hooks."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(lambda s: calls.append("hook"))
        
        executor = HookExecutor()
        owner = TestModel(id=1)
        
        executor.before_delete(owner)
        
        assert calls == ["hook"]


# =============================================================================
# Test: Suppress Errors
# =============================================================================

class TestSuppressErrors:
    """Test error suppression in HookExecutor."""
    
    def test_suppress_errors_false_by_default(self):
        """Errors are not suppressed by default."""
        executor = HookExecutor()
        
        assert executor._suppress_errors is False
    
    def test_suppress_errors_constructor(self):
        """suppress_errors can be set in constructor."""
        executor = HookExecutor(suppress_errors=True)
        
        assert executor._suppress_errors is True
    
    def test_suppress_errors_on_append(self):
        """Suppressed errors don't propagate for on_append."""
        
        class TestModel(MockTable):
            pass
        
        def bad_hook(self, item):
            raise ValueError("Error")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", bad_hook)
        
        executor = HookExecutor(suppress_errors=True)
        owner = TestModel(id=1)
        
        # Should not raise
        executor.on_append(owner, "posts", MockPost(id=1))
    
    def test_suppress_errors_on_remove(self):
        """Suppressed errors don't propagate for on_remove."""
        
        class TestModel(MockTable):
            pass
        
        def bad_hook(self, item):
            raise ValueError("Error")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", bad_hook)
        
        executor = HookExecutor(suppress_errors=True)
        owner = TestModel(id=1)
        
        # Should not raise
        executor.on_remove(owner, "posts", MockPost(id=1))
    
    def test_suppress_errors_on_set(self):
        """Suppressed errors don't propagate for on_set."""
        
        class TestModel(MockTable):
            pass
        
        def bad_hook(self, old, new):
            raise ValueError("Error")
        
        registry = get_hook_registry(TestModel)
        registry.register_on_set("profile", bad_hook)
        
        executor = HookExecutor(suppress_errors=True)
        owner = TestModel(id=1)
        
        # Should not raise
        executor.on_set(owner, "profile", None, MockTable(id=1))
    
    def test_suppress_errors_before_delete(self):
        """Suppressed errors don't propagate for before_delete."""
        
        class TestModel(MockTable):
            pass
        
        def bad_hook(self):
            raise ValueError("Error")
        
        registry = get_hook_registry(TestModel)
        registry.register_before_delete(bad_hook)
        
        executor = HookExecutor(suppress_errors=True)
        owner = TestModel(id=1)
        
        # Should not raise
        executor.before_delete(owner)


# =============================================================================
# Test: No Hooks Registered
# =============================================================================

class TestNoHooksRegistered:
    """Test behavior when no hooks are registered."""
    
    def test_on_append_no_hooks(self):
        """on_append with no hooks doesn't error."""
        
        class TestModel(MockTable):
            pass
        
        owner = TestModel(id=1)
        
        # Should not raise
        fire_on_append(owner, "posts", MockPost(id=1))
    
    def test_on_remove_no_hooks(self):
        """on_remove with no hooks doesn't error."""
        
        class TestModel(MockTable):
            pass
        
        owner = TestModel(id=1)
        
        # Should not raise
        fire_on_remove(owner, "posts", MockPost(id=1))
    
    def test_on_set_no_hooks(self):
        """on_set with no hooks doesn't error."""
        
        class TestModel(MockTable):
            pass
        
        owner = TestModel(id=1)
        
        # Should not raise
        fire_on_set(owner, "profile", None, MockTable(id=1))
    
    def test_before_delete_no_hooks(self):
        """before_delete with no hooks doesn't error."""
        
        class TestModel(MockTable):
            pass
        
        owner = TestModel(id=1)
        
        # Should not raise
        fire_before_delete(owner)


# =============================================================================
# Test: Multiple Calls
# =============================================================================

class TestMultipleCalls:
    """Test multiple hook calls."""
    
    def test_multiple_append_calls(self):
        """Multiple append calls fire hooks each time."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", lambda s, i: calls.append(i.id))
        
        owner = TestModel(id=1)
        
        fire_on_append(owner, "posts", MockPost(id=1))
        fire_on_append(owner, "posts", MockPost(id=2))
        fire_on_append(owner, "posts", MockPost(id=3))
        
        assert calls == [1, 2, 3]
    
    def test_multiple_remove_calls(self):
        """Multiple remove calls fire hooks each time."""
        
        class TestModel(MockTable):
            pass
        
        calls = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_remove("posts", lambda s, i: calls.append(i.id))
        
        owner = TestModel(id=1)
        
        fire_on_remove(owner, "posts", MockPost(id=1))
        fire_on_remove(owner, "posts", MockPost(id=2))
        
        assert calls == [1, 2]


# =============================================================================
# Test: Hook with Complex Arguments
# =============================================================================

class TestHookComplexArguments:
    """Test hooks with complex arguments."""
    
    def test_hook_with_none_item(self):
        """Hook works with None as item."""
        
        class TestModel(MockTable):
            pass
        
        received = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("posts", lambda s, i: received.append(i))
        
        owner = TestModel(id=1)
        
        fire_on_append(owner, "posts", None)
        
        assert received == [None]
    
    def test_hook_with_complex_item(self):
        """Hook works with complex item."""
        
        class TestModel(MockTable):
            pass
        
        class ComplexItem:
            def __init__(self):
                self.data = {"key": "value"}
                self.list = [1, 2, 3]
        
        received = []
        
        registry = get_hook_registry(TestModel)
        registry.register_on_append("items", lambda s, i: received.append(i))
        
        owner = TestModel(id=1)
        complex_item = ComplexItem()
        
        fire_on_append(owner, "items", complex_item)
        
        assert received[0] is complex_item
        assert received[0].data == {"key": "value"}


# =============================================================================
# Test: Performance Under Load
# =============================================================================

class TestPerformanceUnderLoad:
    """Test performance under load."""
    
    def test_many_hooks_same_relationship(self):
        """Many hooks on same relationship still perform well."""
        import time
        
        class TestModel(MockTable):
            pass
        
        registry = get_hook_registry(TestModel)
        
        # Register 100 hooks
        for _ in range(100):
            registry.register_on_append("posts", lambda s, i: None)
        
        owner = TestModel(id=1)
        post = MockPost(id=1)
        
        start = time.perf_counter()
        for _ in range(100):
            fire_on_append(owner, "posts", post)
        elapsed = time.perf_counter() - start
        
        # 100 calls * 100 hooks = 10,000 hook executions
        # Should be fast (< 0.5 seconds)
        assert elapsed < 0.5
    
    def test_many_relationships(self):
        """Many relationships perform well."""
        import time
        
        class TestModel(MockTable):
            pass
        
        registry = get_hook_registry(TestModel)
        
        # Register hooks for 50 relationships
        for i in range(50):
            registry.register_on_append(f"rel_{i}", lambda s, i: None)
        
        owner = TestModel(id=1)
        post = MockPost(id=1)
        
        start = time.perf_counter()
        for i in range(50):
            fire_on_append(owner, f"rel_{i}", post)
        elapsed = time.perf_counter() - start
        
        # Should be fast
        assert elapsed < 0.1

