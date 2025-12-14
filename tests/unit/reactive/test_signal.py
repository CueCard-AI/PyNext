"""
Tests for PyNext Signal

55 tests covering:
- Creation (10): basic, with options, named, custom equality
- Reading (15): call, get, peek, tracking, no-tracking
- Writing (20): set, update, equality checks, no-op updates
- Serialization (10): to_json, get_js_init

Run with: pytest tests/unit/reactive/test_signal.py -v
"""

import gc
import pytest
from typing import List

from pynext.reactive.signal import (
    Signal,
    SignalOptions,
    createSignal,
    signal,
    isSignal,
)
from pynext.reactive.effect import Effect
from pynext.reactive.batch import batch, untrack


# =============================================================================
# SECTION 1: CREATION TESTS (10 tests)
# =============================================================================

class TestSignalCreation:
    """Tests for Signal creation and initialization."""
    
    def test_create_basic_signal(self):
        """Signal can be created with initial value."""
        sig = Signal(42)
        assert sig() == 42
    
    def test_create_signal_with_zero(self):
        """Signal can hold zero as value."""
        sig = Signal(0)
        assert sig() == 0
    
    def test_create_signal_with_string(self):
        """Signal can hold string value."""
        sig = Signal("hello")
        assert sig() == "hello"
    
    def test_create_signal_with_list(self):
        """Signal can hold list value."""
        sig = Signal([1, 2, 3])
        assert sig() == [1, 2, 3]
    
    def test_create_signal_with_dict(self):
        """Signal can hold dict value."""
        sig = Signal({"a": 1, "b": 2})
        assert sig() == {"a": 1, "b": 2}
    
    def test_create_signal_with_name(self):
        """Signal can be created with debug name."""
        sig = Signal(0, name="counter")
        assert sig.name == "counter"
    
    def test_create_signal_with_options(self):
        """Signal can be created with SignalOptions."""
        options = SignalOptions(name="my_signal")
        sig = Signal(0, options=options)
        assert sig.name == "my_signal"
    
    def test_create_signal_with_custom_equality(self):
        """Signal can be created with custom equality function."""
        # Custom equality: equal if both even or both odd
        sig = Signal(2, equals=lambda a, b: a % 2 == b % 2)
        sig.set(4)  # Same parity, no notification
        assert sig() == 2  # Value unchanged
    
    def test_create_signal_generates_unique_id(self):
        """Each signal gets a unique ID."""
        sig1 = Signal(0)
        sig2 = Signal(0)
        assert sig1.id != sig2.id
        assert sig1.id.startswith("sig_")
    
    def test_create_signal_factory_function(self):
        """signal() factory function works."""
        sig = signal(42)
        assert sig() == 42


# =============================================================================
# SECTION 2: READING TESTS (15 tests)
# =============================================================================

class TestSignalReading:
    """Tests for reading signal values."""
    
    def test_read_via_call(self):
        """Signal can be read via call syntax."""
        sig = Signal(42)
        assert sig() == 42
    
    def test_read_via_get(self):
        """Signal can be read via get() method."""
        sig = Signal(42)
        assert sig.get() == 42
    
    def test_read_via_peek(self):
        """Signal can be read via peek() without tracking."""
        sig = Signal(42)
        assert sig.peek() == 42
    
    def test_call_and_get_are_equivalent(self):
        """__call__ and get() return same value."""
        sig = Signal(42)
        assert sig() == sig.get()
    
    def test_read_tracks_dependency_in_effect(self):
        """Reading inside effect tracks dependency."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def track():
            sig()  # Should track
            call_count[0] += 1
        
        assert call_count[0] == 1
        sig.set(1)
        assert call_count[0] == 2  # Re-ran due to tracking
    
    def test_peek_does_not_track_dependency(self):
        """peek() does not track dependency."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def no_track():
            sig.peek()  # Should NOT track
            call_count[0] += 1
        
        assert call_count[0] == 1
        sig.set(1)
        assert call_count[0] == 1  # Did NOT re-run
    
    def test_read_outside_effect_returns_value(self):
        """Reading outside effect just returns value."""
        sig = Signal(42)
        value = sig()
        assert value == 42
    
    def test_read_multiple_times_same_value(self):
        """Multiple reads return same value."""
        sig = Signal(42)
        assert sig() == sig() == sig()
    
    def test_str_returns_value_string(self):
        """__str__ returns string of value."""
        sig = Signal(42)
        assert str(sig) == "42"
    
    def test_str_with_string_value(self):
        """__str__ works with string value."""
        sig = Signal("hello")
        assert str(sig) == "hello"
    
    def test_repr_shows_value_and_name(self):
        """__repr__ shows value and name."""
        sig = Signal(42, name="counter")
        assert "42" in repr(sig)
        assert "counter" in repr(sig)
    
    def test_read_after_write_returns_new_value(self):
        """Read after write returns new value."""
        sig = Signal(0)
        sig.set(42)
        assert sig() == 42
    
    def test_untrack_prevents_dependency(self):
        """untrack() wrapper prevents dependency."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def maybe_track():
            untrack(lambda: sig())
            call_count[0] += 1
        
        assert call_count[0] == 1
        sig.set(1)
        assert call_count[0] == 1  # Did NOT re-run
    
    def test_read_none_value(self):
        """Can read None value."""
        sig = Signal(None)
        assert sig() is None
    
    def test_read_boolean_false(self):
        """Can read False boolean value."""
        sig = Signal(False)
        assert sig() is False


# =============================================================================
# SECTION 3: WRITING TESTS (20 tests)
# =============================================================================

class TestSignalWriting:
    """Tests for writing signal values."""
    
    def test_set_changes_value(self):
        """set() changes the signal value."""
        sig = Signal(0)
        sig.set(42)
        assert sig() == 42
    
    def test_update_with_function(self):
        """update() applies function to value."""
        sig = Signal(10)
        sig.update(lambda x: x + 5)
        assert sig() == 15
    
    def test_set_same_value_no_notification(self):
        """set() with same value doesn't notify."""
        sig = Signal(42)
        call_count = [0]
        
        @Effect
        def counter():
            sig()
            call_count[0] += 1
        
        assert call_count[0] == 1
        sig.set(42)  # Same value
        assert call_count[0] == 1  # No additional call
    
    def test_set_different_value_notifies(self):
        """set() with different value notifies."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def counter():
            sig()
            call_count[0] += 1
        
        assert call_count[0] == 1
        sig.set(1)  # Different value
        assert call_count[0] == 2  # Re-ran
    
    def test_update_to_same_value_no_notification(self):
        """update() returning same value doesn't notify."""
        sig = Signal(42)
        call_count = [0]
        
        @Effect
        def counter():
            sig()
            call_count[0] += 1
        
        assert call_count[0] == 1
        sig.update(lambda x: x)  # Returns same value
        assert call_count[0] == 1  # No additional call
    
    def test_custom_equality_prevents_notification(self):
        """Custom equality can prevent notification."""
        # Equal if integer parts are same
        sig = Signal(1.0, equals=lambda a, b: int(a) == int(b))
        call_count = [0]
        
        @Effect
        def counter():
            sig()
            call_count[0] += 1
        
        assert call_count[0] == 1
        sig.set(1.5)  # Same integer part
        assert call_count[0] == 1  # No notification
        sig.set(2.0)  # Different integer part
        assert call_count[0] == 2  # Notified
    
    def test_write_none_value(self):
        """Can write None value."""
        sig = Signal(42)
        sig.set(None)
        assert sig() is None
    
    def test_write_to_none_signal(self):
        """Can write to signal initialized with None."""
        sig = Signal(None)
        sig.set(42)
        assert sig() == 42
    
    def test_multiple_writes(self):
        """Multiple writes work correctly."""
        sig = Signal(0)
        sig.set(1)
        sig.set(2)
        sig.set(3)
        assert sig() == 3
    
    def test_write_complex_object(self):
        """Can write complex object."""
        sig = Signal(None)
        obj = {"nested": {"value": [1, 2, 3]}}
        sig.set(obj)
        assert sig() == obj
    
    def test_update_increment(self):
        """update() can increment value."""
        sig = Signal(0)
        for _ in range(5):
            sig.update(lambda x: x + 1)
        assert sig() == 5
    
    def test_update_decrement(self):
        """update() can decrement value."""
        sig = Signal(10)
        sig.update(lambda x: x - 3)
        assert sig() == 7
    
    def test_update_multiply(self):
        """update() can multiply value."""
        sig = Signal(5)
        sig.update(lambda x: x * 2)
        assert sig() == 10
    
    def test_update_toggle_boolean(self):
        """update() can toggle boolean."""
        sig = Signal(True)
        sig.update(lambda x: not x)
        assert sig() is False
        sig.update(lambda x: not x)
        assert sig() is True
    
    def test_update_append_to_list(self):
        """update() can modify list."""
        sig = Signal([1, 2])
        sig.update(lambda x: x + [3])
        assert sig() == [1, 2, 3]
    
    def test_write_triggers_single_notification(self):
        """Each write triggers exactly one notification."""
        sig = Signal(0)
        notifications = []
        
        @Effect
        def tracker():
            notifications.append(sig())
        
        sig.set(1)
        sig.set(2)
        sig.set(3)
        
        assert notifications == [0, 1, 2, 3]
    
    def test_write_from_within_effect(self):
        """Writing signal from within effect works."""
        sig1 = Signal(0)
        sig2 = Signal(0)
        
        @Effect
        def sync():
            sig2.set(sig1() * 2)
        
        assert sig2() == 0
        sig1.set(5)
        assert sig2() == 10
    
    def test_batch_coalesces_updates(self):
        """batch() coalesces multiple updates."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def counter():
            sig()
            call_count[0] += 1
        
        batch(lambda: (sig.set(1), sig.set(2), sig.set(3)))
        
        assert call_count[0] == 2  # Initial + 1 batch
        assert sig() == 3
    
    def test_isSignal_function(self):
        """isSignal() correctly identifies signals."""
        sig = Signal(0)
        assert isSignal(sig) is True
        assert isSignal(42) is False
        assert isSignal("not a signal") is False


# =============================================================================
# SECTION 4: SERIALIZATION TESTS (10 tests)
# =============================================================================

class TestSignalSerialization:
    """Tests for signal serialization."""
    
    def test_to_json(self):
        """to_json creates correct structure."""
        sig = Signal(42, name="counter")
        json_data = sig.to_json()
        
        assert json_data["value"] == 42
        assert json_data["name"] == "counter"
        assert "id" in json_data
    
    def test_get_js_init(self):
        """get_js_init generates valid JS."""
        sig = Signal(42, name="counter")
        js = sig.get_js_init()
        
        assert "__pynext__.createSignal" in js
        assert "42" in js
    
    def test_to_json_with_string(self):
        """to_json works with string values."""
        sig = Signal("hello")
        json_data = sig.to_json()
        assert json_data["value"] == "hello"
    
    def test_to_json_with_list(self):
        """to_json works with list values."""
        sig = Signal([1, 2, 3])
        json_data = sig.to_json()
        assert json_data["value"] == [1, 2, 3]
    
    def test_to_json_with_dict(self):
        """to_json works with dict values."""
        sig = Signal({"key": "value"})
        json_data = sig.to_json()
        assert json_data["value"] == {"key": "value"}
    
    def test_to_json_has_id(self):
        """to_json includes id field."""
        sig = Signal(0)
        json_data = sig.to_json()
        assert "id" in json_data
        assert json_data["id"].startswith("sig_")
    
    def test_get_js_init_with_string(self):
        """get_js_init handles string values."""
        sig = Signal("hello")
        js = sig.get_js_init()
        assert '"hello"' in js
    
    def test_get_js_init_includes_id(self):
        """get_js_init includes signal ID."""
        sig = Signal(0)
        js = sig.get_js_init()
        assert sig.id in js
    
    def test_createSignal_returns_tuple(self):
        """createSignal returns (getter, setter) tuple."""
        getter, setter = createSignal(0)
        assert getter() == 0
        setter(42)
        assert getter() == 42
    
    def test_createSignal_setter_updates(self):
        """createSignal setter triggers updates."""
        getter, setter = createSignal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            getter()
            call_count[0] += 1
        
        setter(1)
        assert call_count[0] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
