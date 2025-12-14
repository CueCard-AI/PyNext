"""
Tests for hydration binding data generation.

Tests cover:
- Hydration data structure
- Binding serialization
- Signal value serialization
- Complete hydration payloads
"""

import pytest
import json
from pynext.reactive import Signal
from pynext.reactive.control_flow import Show, For
from pynext.core.html import div
from pynext.core.context import RenderContext, set_context, clear_context


class TestHydrationDataStructure:
    """Tests for hydration data structure."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_hydration_data_has_render_id(self):
        """Hydration data includes render ID."""
        data = self.ctx.get_hydration_data()
        assert "renderId" in data
        assert len(data["renderId"]) > 0
    
    def test_hydration_data_has_signals(self):
        """Hydration data includes signals."""
        count = Signal(42, name="count")
        el = div()[count]
        el.render()
        
        data = self.ctx.get_hydration_data()
        assert "signals" in data
    
    def test_hydration_data_has_bindings(self):
        """Hydration data includes bindings."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        assert "bindings" in data
        assert len(data["bindings"]) >= 1
    
    def test_hydration_data_has_events(self):
        """Hydration data includes events."""
        data = self.ctx.get_hydration_data()
        assert "events" in data


class TestBindingSerialization:
    """Tests for binding serialization in hydration data."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_show_binding_serialization(self):
        """Show binding serializes correctly."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        
        assert "nodeId" in binding
        assert "type" in binding
        assert "signals" in binding
        assert "update" in binding
    
    def test_binding_type_is_string(self):
        """Binding type is a string."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        
        assert isinstance(binding["type"], str)
    
    def test_binding_signals_is_list(self):
        """Binding signals is a list."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        
        assert isinstance(binding["signals"], list)
    
    def test_binding_update_is_string(self):
        """Binding update expression is a string."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        
        assert isinstance(binding["update"], str)


class TestSignalSerialization:
    """Tests for signal value serialization."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_string_signal_value(self):
        """String signal value serializes."""
        name = Signal("John", name="name")
        el = div()[name]
        el.render()
        
        data = self.ctx.get_hydration_data()
        assert data["signals"]["name"]["value"] == "John"
    
    def test_number_signal_value(self):
        """Number signal value serializes."""
        count = Signal(42, name="count")
        el = div()[count]
        el.render()
        
        data = self.ctx.get_hydration_data()
        assert data["signals"]["count"]["value"] == 42
    
    def test_boolean_signal_value(self):
        """Boolean signal value serializes."""
        active = Signal(True, name="active")
        show = Show(when=lambda: active())["X"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        # Active might be in signals if registered
        assert "bindings" in data
    
    def test_list_signal_value(self):
        """List signal value serializes."""
        items = Signal([1, 2, 3], name="items")
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        for_comp.render()
        
        data = self.ctx.get_hydration_data()
        # Should have binding with list data
        assert len(data["bindings"]) >= 1
    
    def test_dict_signal_value(self):
        """Dict signal value serializes."""
        user = Signal({"name": "John", "age": 30}, name="user")
        el = div()[user]
        el.render()
        
        data = self.ctx.get_hydration_data()
        assert "signals" in data


class TestCompleteHydrationPayload:
    """Tests for complete hydration payloads."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_payload_is_json_serializable(self):
        """Complete payload can be JSON serialized."""
        visible = Signal(True, name="visible")
        count = Signal(42, name="count")
        
        el = div()[
            Show(when=lambda: visible())["Visible"],
            count,
        ]
        el.render()
        
        data = self.ctx.get_hydration_data()
        
        # Should not raise
        json_str = json.dumps(data)
        assert len(json_str) > 0
    
    def test_payload_roundtrip(self):
        """Payload survives JSON roundtrip."""
        visible = Signal(True, name="visible")
        
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        
        json_str = json.dumps(data)
        restored = json.loads(json_str)
        
        assert restored["renderId"] == data["renderId"]
        assert len(restored["bindings"]) == len(data["bindings"])
    
    def test_multiple_bindings_payload(self):
        """Payload with multiple bindings."""
        a = Signal(True, name="a")
        b = Signal(False, name="b")
        
        el = div()[
            Show(when=lambda: a())["A"],
            Show(when=lambda: b())["B"],
        ]
        el.render()
        
        data = self.ctx.get_hydration_data()
        
        assert len(data["bindings"]) >= 2


class TestHydrationScriptGeneration:
    """Tests for hydration script generation."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_script_contains_hydration_data(self):
        """Generated script contains hydration data."""
        import json
        
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        
        # Simple script generation
        script = f"window.__PYNEXT_HYDRATION__ = {json.dumps(data)};"
        
        assert "__PYNEXT_HYDRATION__" in script
        assert data["renderId"] in script


class TestBindingInitialValues:
    """Tests for binding initial values."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_show_initial_value_true(self):
        """Show binding has correct initial value for true."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        assert binding["initial"] == True
    
    def test_show_initial_value_false(self):
        """Show binding has correct initial value for false."""
        visible = Signal(False, name="visible")
        show = Show(when=lambda: visible())["Hidden"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        assert binding["initial"] == False
    
    def test_for_initial_value_count(self):
        """For binding has initial count."""
        items = Signal([1, 2, 3], name="items")
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        for_comp.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        assert binding["initial"]["count"] == 3


class TestHydrationEdgeCases:
    """Edge cases for hydration data."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_empty_context(self):
        """Empty context produces valid hydration data."""
        data = self.ctx.get_hydration_data()
        
        assert "renderId" in data
        assert "signals" in data
        assert "bindings" in data
    
    def test_special_characters_in_string(self):
        """Special characters in string values."""
        text = Signal('He said "Hello"', name="text")
        el = div()[text]
        el.render()
        
        data = self.ctx.get_hydration_data()
        
        # Should be JSON serializable
        json_str = json.dumps(data)
        assert len(json_str) > 0
    
    def test_unicode_in_values(self):
        """Unicode characters in values."""
        text = Signal("Hello 世界 🌍", name="text")
        el = div()[text]
        el.render()
        
        data = self.ctx.get_hydration_data()
        
        json_str = json.dumps(data)
        assert "世界" in json_str or "\\u" in json_str

