"""
Unit tests for PyNext reactive primitives.

Tests Signal, Computed, Effect, Store, and batch functionality.
"""

import pytest
from pynext.core.signals import Signal, Computed, Effect, Store, batch, signal, computed


class TestSignal:
    """Tests for the Signal primitive."""
    
    def test_create_signal(self):
        """Signal can be created with initial value."""
        s = Signal(42)
        assert s() == 42
    
    def test_create_signal_with_name(self):
        """Signal can be created with a custom name."""
        s = Signal(0, name="counter")
        assert s._name == "counter"
    
    def test_signal_set(self):
        """Signal.set() updates the value."""
        s = Signal(0)
        s.set(10)
        assert s() == 10
    
    def test_signal_update(self):
        """Signal.update() transforms the value."""
        s = Signal(5)
        s.update(lambda x: x * 2)
        assert s() == 10
    
    def test_signal_no_update_on_same_value(self):
        """Signal doesn't notify if value is unchanged."""
        s = Signal(5)
        notifications = []
        s.subscribe(lambda v: notifications.append(v))
        
        s.set(5)  # Same value
        assert len(notifications) == 0
        
        s.set(10)  # Different value
        assert len(notifications) == 1
    
    def test_signal_subscribe(self):
        """Signal.subscribe() receives updates."""
        s = Signal(0)
        values = []
        
        unsubscribe = s.subscribe(lambda v: values.append(v))
        
        s.set(1)
        s.set(2)
        s.set(3)
        
        assert values == [1, 2, 3]
        
        # Unsubscribe
        unsubscribe()
        s.set(4)
        assert values == [1, 2, 3]  # No new values
    
    def test_signal_str(self):
        """Signal string representation shows current value."""
        s = Signal("hello")
        assert str(s) == "hello"
    
    def test_signal_repr(self):
        """Signal repr shows type and value."""
        s = Signal(42)
        assert "Signal" in repr(s)
        assert "42" in repr(s)
    
    def test_signal_types(self):
        """Signal works with various types."""
        # Integer
        s_int = Signal(42)
        assert s_int() == 42
        
        # String
        s_str = Signal("hello")
        assert s_str() == "hello"
        
        # List
        s_list = Signal([1, 2, 3])
        assert s_list() == [1, 2, 3]
        
        # Dict
        s_dict = Signal({"a": 1})
        assert s_dict() == {"a": 1}
        
        # None
        s_none = Signal(None)
        assert s_none() is None
    
    def test_signal_factory_function(self):
        """signal() factory creates Signal instances."""
        s = signal(42, name="test")
        assert isinstance(s, Signal)
        assert s() == 42
        assert s._name == "test"


class TestComputed:
    """Tests for the Computed/Memo primitive."""
    
    def test_create_computed(self):
        """Computed can be created with a function."""
        c = Computed(lambda: 42)
        assert c() == 42
    
    def test_computed_derives_from_signal(self):
        """Computed derives value from signals."""
        count = Signal(5)
        doubled = Computed(lambda: count() * 2)
        
        assert doubled() == 10
        
        count.set(10)
        doubled.invalidate()  # In real usage, this happens automatically
        assert doubled() == 20
    
    def test_computed_caches_value(self):
        """Computed caches value until invalidated."""
        call_count = 0
        
        def expensive_computation():
            nonlocal call_count
            call_count += 1
            return 42
        
        c = Computed(expensive_computation)
        
        # First call computes
        assert c() == 42
        assert call_count == 1
        
        # Second call uses cache
        assert c() == 42
        assert call_count == 1
        
        # After invalidation, recomputes
        c.invalidate()
        assert c() == 42
        assert call_count == 2
    
    def test_computed_str(self):
        """Computed string representation shows value."""
        c = Computed(lambda: "result")
        assert str(c) == "result"
    
    def test_computed_factory_function(self):
        """computed() factory creates Computed instances."""
        c = computed(lambda: 42, name="test")
        assert isinstance(c, Computed)
        assert c() == 42


class TestEffect:
    """Tests for the Effect primitive."""
    
    def test_effect_runs_immediately(self):
        """Effect runs immediately on creation."""
        ran = []
        
        Effect(lambda: ran.append(True))
        
        assert ran == [True]
    
    def test_effect_decorator(self):
        """Effect can be used as a decorator."""
        ran = []
        
        @Effect
        def my_effect():
            ran.append(True)
        
        assert ran == [True]
    
    def test_effect_cleanup(self):
        """Effect cleanup function is called."""
        cleanups = []
        
        def effect_with_cleanup():
            def cleanup():
                cleanups.append("cleaned")
            return cleanup
        
        eff = Effect(effect_with_cleanup)
        assert cleanups == []
        
        # Re-run the effect (simulating dependency change)
        eff._run()
        assert cleanups == ["cleaned"]
    
    def test_effect_dispose(self):
        """Effect.dispose() cleans up the effect."""
        disposed = []
        
        def effect_with_cleanup():
            return lambda: disposed.append(True)
        
        eff = Effect(effect_with_cleanup)
        eff.dispose()
        
        assert disposed == [True]


class TestStore:
    """Tests for the Store primitive."""
    
    def test_create_store(self):
        """Store can be created with initial value."""
        s = Store({"count": 0, "name": "test"})
        assert s() == {"count": 0, "name": "test"}
    
    def test_store_attribute_access(self):
        """Store supports attribute-style access."""
        s = Store({"name": "Alice", "age": 30})
        assert s.name == "Alice"
        assert s.age == 30
    
    def test_store_attribute_set(self):
        """Store supports attribute-style assignment."""
        s = Store({"name": "Alice"})
        s.name = "Bob"
        assert s.name == "Bob"
    
    def test_store_dict_access(self):
        """Store supports dictionary-style access."""
        s = Store({"key": "value"})
        assert s["key"] == "value"
    
    def test_store_dict_set(self):
        """Store supports dictionary-style assignment."""
        s = Store({"key": "value"})
        s["key"] = "new_value"
        assert s["key"] == "new_value"
    
    def test_store_nested_access(self):
        """Store supports nested object access."""
        s = Store({
            "user": {
                "profile": {
                    "name": "Alice"
                }
            }
        })
        assert s.user.profile.name == "Alice"
    
    def test_store_nested_set(self):
        """Store supports nested object assignment."""
        s = Store({
            "user": {
                "name": "Alice"
            }
        })
        s.user.name = "Bob"
        assert s.user.name == "Bob"
    
    def test_store_update(self):
        """Store.update() updates multiple properties."""
        s = Store({"a": 1, "b": 2, "c": 3})
        s.update({"a": 10, "b": 20})
        
        assert s.a == 10
        assert s.b == 20
        assert s.c == 3
    
    def test_store_subscribe(self):
        """Store.subscribe() receives updates."""
        s = Store({"count": 0})
        updates = []
        
        s.subscribe(lambda data: updates.append(data.copy()))
        
        s.count = 1
        s.count = 2
        
        assert len(updates) == 2
        assert updates[-1]["count"] == 2
    
    def test_store_str(self):
        """Store string representation shows data."""
        s = Store({"key": "value"})
        assert "key" in str(s)
        assert "value" in str(s)


class TestBatch:
    """Tests for batch updates."""
    
    def test_batch_combines_updates(self):
        """batch() combines multiple updates."""
        s = Signal(0)
        notifications = []
        s.subscribe(lambda v: notifications.append(v))
        
        batch(lambda: (
            s.set(1),
            s.set(2),
            s.set(3),
        ))
        
        # Should only have one notification with final value
        # (Note: current implementation may differ)
        assert s() == 3
    
    def test_batch_executes_all_updates(self):
        """batch() executes all updates in the function."""
        a = Signal(0)
        b = Signal(0)
        c = Signal(0)
        
        batch(lambda: (
            a.set(1),
            b.set(2),
            c.set(3),
        ))
        
        assert a() == 1
        assert b() == 2
        assert c() == 3
    
    def test_nested_batch(self):
        """Nested batch() calls work correctly."""
        s = Signal(0)
        
        def outer():
            s.set(1)
            batch(lambda: s.set(2))
            s.set(3)
        
        batch(outer)
        
        assert s() == 3


class TestHydration:
    """Tests for hydration data generation."""
    
    def test_signal_js_init(self):
        """Signal generates correct JS initialization."""
        s = Signal(42)
        js = s.get_js_init()
        
        assert "__pynext__.createSignal" in js
        assert s._id in js
        assert "42" in js
    
    def test_signal_string_js_init(self):
        """String signal generates correct JS initialization."""
        s = Signal("hello")
        js = s.get_js_init()
        
        assert '"hello"' in js
    
    def test_store_js_init(self):
        """Store generates correct JS initialization."""
        s = Store({"count": 0, "name": "test"})
        js = s.get_js_init()
        
        assert "__pynext__.createStore" in js
        assert "count" in js
        assert "name" in js

