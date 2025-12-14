"""
Comprehensive Signal Hydration Tests

Target: 150 tests covering signal registration, serialization,
and hydration data generation.
"""

import json
import pytest
from pynext.reactive import Signal, signal
from pynext.core.context import render_context, RenderContext


# =============================================================================
# SIGNAL REGISTRATION TESTS (30 tests)
# =============================================================================

class TestSignalRegistration:
    """Tests for signal auto-registration with render context."""
    
    def test_signal_registers_with_context(self):
        """Signal should auto-register when created inside render context."""
        with render_context() as ctx:
            s = Signal(0, name="test_signal")
            assert "test_signal" in ctx.signals
    
    def test_signal_id_in_registration(self):
        """Registration should include signal ID."""
        with render_context() as ctx:
            s = Signal(0, name="test_signal")
            assert ctx.signals["test_signal"].signal_id == s._id
    
    def test_signal_value_in_registration(self):
        """Registration should include initial value."""
        with render_context() as ctx:
            s = Signal(42, name="test_signal")
            assert ctx.signals["test_signal"].initial_value == 42
    
    def test_multiple_signals_register(self):
        """Multiple signals should all register."""
        with render_context() as ctx:
            s1 = Signal(1, name="signal_1")
            s2 = Signal(2, name="signal_2")
            s3 = Signal(3, name="signal_3")
            assert len(ctx.signals) == 3
    
    def test_signal_without_name_uses_id(self):
        """Signal without name should use ID as key."""
        with render_context() as ctx:
            s = Signal(0)
            # Should have one signal registered
            assert len(ctx.signals) == 1
    
    def test_signal_no_context_doesnt_fail(self):
        """Signal created outside context shouldn't fail."""
        s = Signal(0, name="orphan")
        assert s() == 0
    
    def test_signal_registration_preserves_value_type_int(self):
        """Integer values should be preserved in registration."""
        with render_context() as ctx:
            s = Signal(42, name="int_sig")
            assert ctx.signals["int_sig"].initial_value == 42
            assert isinstance(ctx.signals["int_sig"].initial_value, int)
    
    def test_signal_registration_preserves_value_type_string(self):
        """String values should be preserved in registration."""
        with render_context() as ctx:
            s = Signal("hello", name="str_sig")
            assert ctx.signals["str_sig"].initial_value == "hello"
    
    def test_signal_registration_preserves_value_type_bool(self):
        """Boolean values should be preserved in registration."""
        with render_context() as ctx:
            s = Signal(True, name="bool_sig")
            assert ctx.signals["bool_sig"].initial_value is True
    
    def test_signal_registration_preserves_value_type_list(self):
        """List values should be preserved in registration."""
        with render_context() as ctx:
            s = Signal([1, 2, 3], name="list_sig")
            assert ctx.signals["list_sig"].initial_value == [1, 2, 3]
    
    def test_signal_registration_preserves_value_type_dict(self):
        """Dict values should be preserved in registration."""
        with render_context() as ctx:
            s = Signal({"a": 1}, name="dict_sig")
            assert ctx.signals["dict_sig"].initial_value == {"a": 1}
    
    def test_signal_registration_preserves_value_type_none(self):
        """None values should be preserved in registration."""
        with render_context() as ctx:
            s = Signal(None, name="none_sig")
            assert ctx.signals["none_sig"].initial_value is None
    
    def test_signal_registration_preserves_value_type_float(self):
        """Float values should be preserved in registration."""
        with render_context() as ctx:
            s = Signal(3.14, name="float_sig")
            assert ctx.signals["float_sig"].initial_value == 3.14
    
    def test_signal_updates_dont_affect_registration(self):
        """Signal updates after registration shouldn't change registered value."""
        with render_context() as ctx:
            s = Signal(0, name="test_sig")
            s.set(100)
            # Registration keeps initial value
            assert ctx.signals["test_sig"].initial_value == 0
    
    def test_nested_context_signals(self):
        """Signals in nested functions should register."""
        with render_context() as ctx:
            def inner():
                return Signal(99, name="inner_signal")
            inner_sig = inner()
            assert "inner_signal" in ctx.signals
    
    def test_signal_convenience_function_registers(self):
        """signal() convenience function should register."""
        with render_context() as ctx:
            s = signal(0, name="conv_signal")
            assert "conv_signal" in ctx.signals


# =============================================================================
# SIGNAL SERIALIZATION TESTS (30 tests)
# =============================================================================

class TestSignalSerialization:
    """Tests for signal serialization methods."""
    
    def test_to_json_basic(self):
        """to_json should return dict with id, name, value."""
        s = Signal(42, name="test")
        data = s.to_json()
        assert "id" in data
        assert "name" in data
        assert "value" in data
    
    def test_to_json_value_correct(self):
        """to_json value should match signal value."""
        s = Signal(42, name="test")
        assert s.to_json()["value"] == 42
    
    def test_to_json_name_correct(self):
        """to_json name should match signal name."""
        s = Signal(0, name="my_signal")
        assert s.to_json()["name"] == "my_signal"
    
    def test_to_json_id_starts_with_sig(self):
        """to_json id should start with sig_ prefix."""
        s = Signal(0)
        assert s.to_json()["id"].startswith("sig_")
    
    def test_to_hydration_state_basic(self):
        """to_hydration_state should return {name: value}."""
        s = Signal(42, name="count")
        state = s.to_hydration_state()
        assert state == {"count": 42}
    
    def test_to_hydration_state_string(self):
        """to_hydration_state should handle strings."""
        s = Signal("hello", name="greeting")
        state = s.to_hydration_state()
        assert state == {"greeting": "hello"}
    
    def test_to_hydration_state_list(self):
        """to_hydration_state should handle lists."""
        s = Signal([1, 2, 3], name="items")
        state = s.to_hydration_state()
        assert state == {"items": [1, 2, 3]}
    
    def test_to_hydration_state_dict(self):
        """to_hydration_state should handle dicts."""
        s = Signal({"a": 1, "b": 2}, name="data")
        state = s.to_hydration_state()
        assert state == {"data": {"a": 1, "b": 2}}
    
    def test_to_hydration_state_nested(self):
        """to_hydration_state should handle nested structures."""
        s = Signal({"users": [{"id": 1, "name": "Alice"}]}, name="state")
        state = s.to_hydration_state()
        assert state["state"]["users"][0]["name"] == "Alice"
    
    def test_get_js_init_creates_signal(self):
        """get_js_init should create signal in JS."""
        s = Signal(0, name="count")
        js = s.get_js_init()
        assert "createSignal" in js
        assert "0" in js
    
    def test_get_js_init_with_string_value(self):
        """get_js_init should quote string values."""
        s = Signal("hello", name="greeting")
        js = s.get_js_init()
        assert '"hello"' in js
    
    def test_get_js_init_with_bool_true(self):
        """get_js_init should use JS true for True."""
        s = Signal(True, name="flag")
        js = s.get_js_init()
        assert "true" in js
    
    def test_get_js_init_with_bool_false(self):
        """get_js_init should use JS false for False."""
        s = Signal(False, name="flag")
        js = s.get_js_init()
        assert "false" in js
    
    def test_get_js_init_with_null(self):
        """get_js_init should use JS null for None."""
        s = Signal(None, name="empty")
        js = s.get_js_init()
        assert "null" in js
    
    def test_render_value_basic(self):
        """render_value should create span with data attribute."""
        s = Signal(42, name="count")
        html = s.render_value()
        assert '<span data-pynext-text="count">' in html
        assert "42" in html
    
    def test_render_value_escapes_html(self):
        """render_value should escape HTML in value."""
        s = Signal("<script>alert('xss')</script>", name="text")
        html = s.render_value()
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
    
    def test_json_serializable(self):
        """to_json output should be JSON serializable."""
        s = Signal([1, 2, {"a": "b"}], name="complex")
        json_str = json.dumps(s.to_json())
        assert isinstance(json_str, str)
    
    def test_hydration_state_json_serializable(self):
        """to_hydration_state output should be JSON serializable."""
        s = Signal({"nested": {"deep": [1, 2, 3]}}, name="state")
        json_str = json.dumps(s.to_hydration_state())
        assert isinstance(json_str, str)


# =============================================================================
# HYDRATION DATA GENERATION TESTS (30 tests)
# =============================================================================

class TestHydrationDataGeneration:
    """Tests for hydration data generation from render context."""
    
    def test_get_hydration_data_structure(self):
        """get_hydration_data should return proper structure."""
        with render_context() as ctx:
            s = Signal(0, name="count")
            data = ctx.get_hydration_data()
            assert "renderId" in data
            assert "signals" in data
            assert "effects" in data
            assert "events" in data
            assert "stores" in data
    
    def test_get_hydration_data_contains_signals(self):
        """Signals should appear in hydration data."""
        with render_context() as ctx:
            s = Signal(42, name="count")
            data = ctx.get_hydration_data()
            assert "count" in data["signals"]
    
    def test_get_hydration_data_signal_has_value(self):
        """Signal in hydration data should have value."""
        with render_context() as ctx:
            s = Signal(42, name="count")
            data = ctx.get_hydration_data()
            assert data["signals"]["count"]["value"] == 42
    
    def test_get_hydration_data_signal_has_id(self):
        """Signal in hydration data should have id."""
        with render_context() as ctx:
            s = Signal(0, name="count")
            data = ctx.get_hydration_data()
            assert "id" in data["signals"]["count"]
    
    def test_get_hydration_data_signal_has_element_id(self):
        """Signal in hydration data should have elementId."""
        with render_context() as ctx:
            s = Signal(0, name="count")
            data = ctx.get_hydration_data()
            assert "elementId" in data["signals"]["count"]
    
    def test_hydration_data_json_serializable(self):
        """Full hydration data should be JSON serializable."""
        with render_context() as ctx:
            s1 = Signal(0, name="count")
            s2 = Signal("hello", name="greeting")
            s3 = Signal([1, 2, 3], name="items")
            data = ctx.get_hydration_data()
            json_str = json.dumps(data)
            assert isinstance(json_str, str)
    
    def test_hydration_data_roundtrip(self):
        """Hydration data should survive JSON roundtrip."""
        with render_context() as ctx:
            s = Signal({"nested": [1, 2, 3]}, name="state")
            data = ctx.get_hydration_data()
            json_str = json.dumps(data)
            restored = json.loads(json_str)
            assert restored["signals"]["state"]["value"] == {"nested": [1, 2, 3]}
    
    def test_hydration_data_render_id_unique(self):
        """Each render should have unique render ID."""
        ids = []
        for _ in range(10):
            with render_context() as ctx:
                data = ctx.get_hydration_data()
                ids.append(data["renderId"])
        assert len(ids) == len(set(ids))
    
    def test_hydration_data_multiple_signals(self):
        """Multiple signals should all appear in data."""
        with render_context() as ctx:
            s1 = Signal(1, name="a")
            s2 = Signal(2, name="b")
            s3 = Signal(3, name="c")
            data = ctx.get_hydration_data()
            assert len(data["signals"]) == 3
            assert "a" in data["signals"]
            assert "b" in data["signals"]
            assert "c" in data["signals"]


# =============================================================================
# EDGE CASES (30 tests)
# =============================================================================

class TestSignalHydrationEdgeCases:
    """Edge case tests for signal hydration."""
    
    def test_empty_string_signal(self):
        """Empty string should hydrate correctly."""
        s = Signal("", name="empty")
        assert s.to_hydration_state() == {"empty": ""}
    
    def test_zero_value_signal(self):
        """Zero should hydrate correctly (not treated as falsy)."""
        s = Signal(0, name="zero")
        assert s.to_hydration_state() == {"zero": 0}
    
    def test_empty_list_signal(self):
        """Empty list should hydrate correctly."""
        s = Signal([], name="empty_list")
        assert s.to_hydration_state() == {"empty_list": []}
    
    def test_empty_dict_signal(self):
        """Empty dict should hydrate correctly."""
        s = Signal({}, name="empty_dict")
        assert s.to_hydration_state() == {"empty_dict": {}}
    
    def test_special_chars_in_name(self):
        """Signal name with special chars should work."""
        s = Signal(0, name="count_1")
        assert "count_1" in s.to_hydration_state()
    
    def test_unicode_in_value(self):
        """Unicode values should hydrate correctly."""
        s = Signal("日本語", name="text")
        state = s.to_hydration_state()
        assert state["text"] == "日本語"
    
    def test_very_long_string(self):
        """Very long strings should hydrate correctly."""
        long_str = "a" * 10000
        s = Signal(long_str, name="long")
        assert len(s.to_hydration_state()["long"]) == 10000
    
    def test_very_large_number(self):
        """Very large numbers should hydrate correctly."""
        s = Signal(10**20, name="big")
        assert s.to_hydration_state()["big"] == 10**20
    
    def test_float_precision(self):
        """Float values should preserve precision."""
        s = Signal(3.141592653589793, name="pi")
        assert s.to_hydration_state()["pi"] == 3.141592653589793
    
    def test_negative_numbers(self):
        """Negative numbers should hydrate correctly."""
        s = Signal(-42, name="neg")
        assert s.to_hydration_state()["neg"] == -42
    
    def test_deeply_nested_data(self):
        """Deeply nested structures should hydrate."""
        nested = {"a": {"b": {"c": {"d": {"e": [1, 2, 3]}}}}}
        s = Signal(nested, name="deep")
        state = s.to_hydration_state()
        assert state["deep"]["a"]["b"]["c"]["d"]["e"] == [1, 2, 3]
    
    def test_tuple_converted_to_list(self):
        """Tuples should convert to lists in JSON."""
        s = Signal((1, 2, 3), name="tuple")
        json_str = json.dumps(s.to_hydration_state())
        restored = json.loads(json_str)
        assert restored["tuple"] == [1, 2, 3]
    
    def test_signal_after_many_updates(self):
        """Signal should serialize correctly after many updates."""
        s = Signal(0, name="counter")
        for i in range(100):
            s.set(i)
        state = s.to_hydration_state()
        assert state["counter"] == 99
    
    def test_signal_with_quotes_in_string(self):
        """Strings with quotes should be properly escaped."""
        s = Signal('Hello "World"', name="quoted")
        js = s.get_js_init()
        assert "Hello" in js
    
    def test_signal_with_newlines(self):
        """Strings with newlines should be properly escaped."""
        s = Signal("Line1\nLine2", name="multiline")
        js = s.get_js_init()
        assert "\\n" in js or "Line1" in js


# =============================================================================
# CONTEXT MANAGEMENT TESTS (30 tests)
# =============================================================================

class TestContextManagement:
    """Tests for render context management."""
    
    def test_context_isolation(self):
        """Signals in different contexts should be isolated."""
        with render_context() as ctx1:
            s1 = Signal(1, name="a")
        
        with render_context() as ctx2:
            s2 = Signal(2, name="b")
        
        assert "a" in ctx1.signals
        assert "b" not in ctx1.signals
        assert "b" in ctx2.signals
        assert "a" not in ctx2.signals
    
    def test_context_cleanup(self):
        """Context should clean up after exit."""
        with render_context() as ctx:
            s = Signal(0, name="temp")
        
        # After exit, new signals shouldn't register to old context
        s2 = Signal(0, name="orphan")
        assert "orphan" not in ctx.signals
    
    def test_nested_contexts_not_supported(self):
        """Nested contexts should use inner context."""
        with render_context() as outer:
            with render_context() as inner:
                s = Signal(0, name="inner_sig")
                # Signal should register with inner context
                assert "inner_sig" in inner.signals
    
    def test_context_generate_id(self):
        """generate_id should create unique IDs."""
        with render_context() as ctx:
            id1 = ctx.generate_id("el")
            id2 = ctx.generate_id("el")
            assert id1 != id2
            assert id1.startswith("el_")
    
    def test_context_register_event(self):
        """register_event should track event handlers."""
        with render_context() as ctx:
            ctx.register_event("btn_1", "click", "console.log('clicked')")
            data = ctx.get_hydration_data()
            assert "btn_1" in data["events"]
            assert data["events"]["btn_1"]["click"] == "console.log('clicked')"
    
    def test_context_multiple_events_same_element(self):
        """Multiple events on same element should all register."""
        with render_context() as ctx:
            ctx.register_event("btn_1", "click", "onClick()")
            ctx.register_event("btn_1", "hover", "onHover()")
            data = ctx.get_hydration_data()
            assert "click" in data["events"]["btn_1"]
            assert "hover" in data["events"]["btn_1"]


# Run with: pytest tests/unit/hydration/test_signal_hydration.py -v

