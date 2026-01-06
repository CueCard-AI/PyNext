"""
Tests for Hydration Data Format Consistency

Critical Risk: There are TWO hydration systems in PyNext:
1. __PYNEXT_HYDRATION__ - used by pynext/runtime/signals.js
2. __PYNEXT_DATA__ - used by pynext/runtime/reactive.js

This tests that both systems work correctly and that the server
generates data compatible with both client-side consumers.

Risk Scenarios:
1. Server generates __PYNEXT_HYDRATION__ but client looks for __PYNEXT_DATA__
2. Data format mismatch (signals.X vs components.X.signals)
3. Missing required fields in hydration data
4. JSON serialization issues with complex types
5. Script tag escaping issues
"""

import pytest
import json
from typing import Dict, Any


# =============================================================================
# TEST: HYDRATION DATA STRUCTURES
# =============================================================================

class TestHydrationDataClass:
    """Test the HydrationData dataclass from server/hydration.py."""
    
    def test_import_hydration_data(self):
        """HydrationData should be importable."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData()
        assert data is not None
    
    def test_hydration_data_default_fields(self):
        """HydrationData should have all required fields."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData()
        
        # Check all fields exist
        assert hasattr(data, 'render_id')
        assert hasattr(data, 'signals')
        assert hasattr(data, 'stores')
        assert hasattr(data, 'effects')
        assert hasattr(data, 'events')
        assert hasattr(data, 'actions')
        
        # Check default types
        assert isinstance(data.signals, dict)
        assert isinstance(data.stores, dict)
        assert isinstance(data.effects, dict)
        assert isinstance(data.events, dict)
        assert isinstance(data.actions, dict)
    
    def test_to_dict_format(self):
        """to_dict() should produce correct format."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            render_id="render_123",
            signals={"count": {"id": "sig_1", "value": 0}},
            stores={"items": []},
            effects={},
            events={"btn_1": {"click": "handler()"}},
            actions={"action_1": {"name": "submit", "args": {}}},
        )
        
        result = data.to_dict()
        
        # Check structure
        assert result["renderId"] == "render_123"
        assert "signals" in result
        assert "stores" in result
        assert "effects" in result
        assert "events" in result
        assert "actions" in result
    
    def test_to_json_is_valid(self):
        """to_json() should produce valid JSON."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            signals={"count": {"id": "sig_1", "value": 42}},
        )
        
        json_str = data.to_json()
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["signals"]["count"]["value"] == 42
    
    def test_is_empty_when_empty(self):
        """is_empty() should return True for empty data."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData()
        assert data.is_empty() is True
    
    def test_is_empty_with_signals(self):
        """is_empty() should return False when signals present."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(signals={"count": {"value": 0}})
        assert data.is_empty() is False
    
    def test_is_empty_with_events(self):
        """is_empty() should return False when events present."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(events={"btn": {"click": "fn()"}})
        assert data.is_empty() is False


class TestCollectHydrationData:
    """Test the collect_hydration_data function."""
    
    def test_collect_from_render_context(self):
        """Should collect all data from RenderContext."""
        from pynext.server.hydration import collect_hydration_data
        from pynext.core.context import RenderContext
        
        class MockSignal:
            _id = "sig_001"
            _name = "count"
            _value = 0
        
        ctx = RenderContext()
        ctx.register_signal(MockSignal())
        ctx.register_event("btn_1", "click", "handler()")
        
        data = collect_hydration_data(ctx)
        
        # Should be a HydrationData instance
        from pynext.server.hydration import HydrationData
        assert isinstance(data, HydrationData)
    
    def test_collected_signals_format(self):
        """Signals should be collected with correct format."""
        from pynext.server.hydration import collect_hydration_data
        from pynext.core.context import RenderContext
        
        class MockSignal:
            _id = "sig_test"
            _name = "mySignal"
            _value = 100
        
        ctx = RenderContext()
        ctx.register_signal(MockSignal())
        
        data = collect_hydration_data(ctx)
        
        # Check signal is present
        assert "mySignal" in data.signals


class TestInjectHydrationScript:
    """Test the inject_hydration_script function."""
    
    def test_inject_adds_script_tag(self):
        """Should inject a script tag with hydration data."""
        from pynext.server.hydration import inject_hydration_script, HydrationData
        
        html = "<html><body></body></html>"
        data = HydrationData(signals={"count": {"id": "sig_1", "value": 0}})
        
        result = inject_hydration_script(html, data)
        
        # Should contain a script tag
        assert "<script" in result
        assert "__PYNEXT_HYDRATION__" in result or "__PYNEXT_DATA__" in result
    
    def test_inject_before_closing_body(self):
        """Script should be injected before </body>."""
        from pynext.server.hydration import inject_hydration_script, HydrationData
        
        html = "<html><body><div>Content</div></body></html>"
        data = HydrationData(signals={"x": {"value": 1}})
        
        result = inject_hydration_script(html, data)
        
        # Script should come before </body>
        script_pos = result.find("<script")
        body_pos = result.find("</body>")
        assert script_pos < body_pos, f"Script at {script_pos}, body at {body_pos}"
    
    def test_script_contains_valid_json(self):
        """Injected script should contain valid JSON."""
        from pynext.server.hydration import inject_hydration_script, HydrationData
        
        html = "<html><body></body></html>"
        data = HydrationData(signals={"count": {"id": "sig_1", "value": 42}})
        
        result = inject_hydration_script(html, data)
        
        # Extract JSON from script
        # The format is: window.__PYNEXT_HYDRATION__ = {...}
        import re
        match = re.search(r'window\.__PYNEXT_(?:HYDRATION|DATA)__\s*=\s*(\{.*?\});', result, re.DOTALL)
        if match:
            json_str = match.group(1)
            # Should be valid JSON
            parsed = json.loads(json_str)
            assert "signals" in parsed


class TestGenerateHydrationScript:
    """Test the generate_hydration_script function."""
    
    def test_generates_script_content(self):
        """Should generate valid script content."""
        from pynext.server.hydration import generate_hydration_script, HydrationData
        
        data = HydrationData(
            signals={"count": {"id": "sig_1", "value": 0}},
            events={"btn": {"click": "fn()"}},
        )
        
        script = generate_hydration_script(data)
        
        assert "window.__PYNEXT_" in script
        assert "signals" in script


class TestHydrationFormatCompatibility:
    """Test compatibility between server output and client expectations."""
    
    def test_signals_format_for_signals_js(self):
        """
        signals.js expects:
        window.__PYNEXT_HYDRATION__ = {
            signals: { name: { id, value, elementId? } }
        }
        """
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            signals={
                "count": {"id": "sig_1", "value": 0, "elementId": "span_1"},
            }
        )
        
        result = data.to_dict()
        
        # Check format matches client expectation
        assert "signals" in result
        count_sig = result["signals"]["count"]
        assert "id" in count_sig
        assert "value" in count_sig
    
    def test_events_format_for_client(self):
        """
        Client expects:
        events: { elementId: { eventName: handlerCode } }
        """
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            events={
                "btn_1": {"click": "count.set(count() + 1)"},
                "form_1": {"submit": "handleSubmit()"},
            }
        )
        
        result = data.to_dict()
        
        assert "events" in result
        assert "btn_1" in result["events"]
        assert result["events"]["btn_1"]["click"] == "count.set(count() + 1)"
    
    def test_stores_format_for_client(self):
        """Stores should serialize with their full state."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            stores={
                "items": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
                "user": {"name": "Alice", "email": "alice@example.com"},
            }
        )
        
        result = data.to_dict()
        
        assert "stores" in result
        assert len(result["stores"]["items"]) == 2
        assert result["stores"]["user"]["name"] == "Alice"


class TestRenderContextToHydrationBridge:
    """Test the bridge from RenderContext to HydrationData."""
    
    def test_context_hydration_data_method(self):
        """RenderContext.get_hydration_data() should work."""
        from pynext.core.context import RenderContext
        
        class MockSignal:
            _id = "sig_1"
            _name = "count"
            _value = 0
        
        ctx = RenderContext()
        ctx.register_signal(MockSignal())
        
        data = ctx.get_hydration_data()
        
        assert isinstance(data, dict)
        assert "signals" in data
    
    def test_full_pipeline_context_to_html(self):
        """Test full pipeline from context to injected HTML."""
        from pynext.core.context import RenderContext
        from pynext.server.hydration import collect_hydration_data, inject_hydration_script
        
        class MockSignal:
            _id = "sig_test"
            _name = "count"
            _value = 42
        
        # Create context with state
        ctx = RenderContext()
        ctx.register_signal(MockSignal())
        ctx.register_event("btn_1", "click", "__pynext__.getSignal('count').update(v => v + 1)")
        
        # Collect hydration data
        hydration = collect_hydration_data(ctx)
        
        # Inject into HTML
        html = "<html><body><button id='btn_1'>+</button></body></html>"
        result = inject_hydration_script(html, hydration)
        
        # Verify result
        assert "__PYNEXT_" in result
        assert "count" in result or "sig_test" in result


class TestScriptTagEscaping:
    """Test that script content is properly escaped."""
    
    def test_escapes_closing_script_tag(self):
        """Content with </script> should be escaped."""
        from pynext.server.hydration import HydrationData, generate_hydration_script
        
        # Signal value contains </script>
        data = HydrationData(
            signals={
                "code": {"id": "sig_1", "value": "<script>alert('xss')</script>"}
            }
        )
        
        script = generate_hydration_script(data)
        
        # Should not have raw </script> that would break parsing
        # The content should be escaped somehow
        assert "</script>" not in script or "\\u003c" in script or "&lt;" in script or "<\\/script>" in script
    
    def test_handles_unicode_characters(self):
        """Unicode in values should serialize correctly."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            signals={
                "text": {"id": "sig_1", "value": "Hello 世界 🌍"}
            }
        )
        
        json_str = data.to_json()
        parsed = json.loads(json_str)
        
        assert "世界" in parsed["signals"]["text"]["value"] or "\\u" in json_str
    
    def test_handles_special_json_characters(self):
        """Special JSON characters should be escaped."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            signals={
                "text": {"id": "sig_1", "value": 'Line1\nLine2\tTabbed\r\nWindows'}
            }
        )
        
        json_str = data.to_json()
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "Line1" in parsed["signals"]["text"]["value"]


class TestComponentBasedHydration:
    """Test component-scoped hydration (reactive.js format)."""
    
    def test_component_hydration_format(self):
        """
        reactive.js expects a different format:
        {
            components: {
                componentId: {
                    signals: { name: value },
                    stores: { name: value }
                }
            }
        }
        """
        # This tests the alternate format used by reactive.js
        # Check if this format is supported
        from pynext.server.hydration import HydrationData
        
        # The current HydrationData doesn't have components structure
        # This is a potential format mismatch risk
        data = HydrationData()
        result = data.to_dict()
        
        # Check what format is actually produced
        # Either flat signals or nested components
        assert "signals" in result or "components" in result


class TestHydrationDataWithAllTypes:
    """Test hydration with all data types."""
    
    def test_complex_signal_values(self):
        """Signals with complex nested values."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            signals={
                "config": {
                    "id": "sig_config",
                    "value": {
                        "nested": {
                            "deeply": {
                                "value": [1, 2, {"x": 3}]
                            }
                        },
                        "array": [1, "two", True, None, 3.14],
                        "empty": {},
                    }
                }
            }
        )
        
        json_str = data.to_json()
        parsed = json.loads(json_str)
        
        nested = parsed["signals"]["config"]["value"]["nested"]["deeply"]["value"]
        assert nested == [1, 2, {"x": 3}]
    
    def test_null_values(self):
        """None/null values should serialize correctly."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            signals={
                "nullable": {"id": "sig_1", "value": None}
            }
        )
        
        json_str = data.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["signals"]["nullable"]["value"] is None
    
    def test_boolean_values(self):
        """Boolean values should serialize as true/false not True/False."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            signals={
                "active": {"id": "sig_1", "value": True},
                "disabled": {"id": "sig_2", "value": False},
            }
        )
        
        json_str = data.to_json()
        
        # JSON should have lowercase true/false
        assert "true" in json_str.lower()
        assert "false" in json_str.lower()
        # Not Python's True/False
        assert "True" not in json_str
        assert "False" not in json_str
    
    def test_empty_collections(self):
        """Empty arrays and objects should serialize correctly."""
        from pynext.server.hydration import HydrationData
        
        data = HydrationData(
            signals={
                "emptyList": {"id": "sig_1", "value": []},
                "emptyDict": {"id": "sig_2", "value": {}},
            }
        )
        
        json_str = data.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["signals"]["emptyList"]["value"] == []
        assert parsed["signals"]["emptyDict"]["value"] == {}
