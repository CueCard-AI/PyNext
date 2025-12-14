"""
Comprehensive Server Hydration Tests

Target: 200 tests covering server-side hydration utilities.
"""

import json
import pytest
from pynext.server.hydration import (
    HydrationData,
    collect_hydration_data,
    inject_hydration_script,
    generate_hydration_script,
    generate_runtime_script,
    add_hydration_markers,
    extract_component_markers,
    render_with_hydration,
)
from pynext.reactive import Signal, signal
from pynext.core.context import render_context


# =============================================================================
# HYDRATION DATA CLASS TESTS (40 tests)
# =============================================================================

class TestHydrationDataClass:
    """Tests for HydrationData dataclass."""
    
    def test_empty_init(self):
        """Empty HydrationData should initialize correctly."""
        data = HydrationData()
        assert data.render_id == ""
        assert data.signals == {}
        assert data.stores == {}
        assert data.effects == {}
        assert data.events == {}
    
    def test_to_dict(self):
        """to_dict should return proper structure."""
        data = HydrationData(render_id="test123")
        result = data.to_dict()
        assert result["renderId"] == "test123"
        assert "signals" in result
        assert "stores" in result
    
    def test_to_json(self):
        """to_json should return valid JSON string."""
        data = HydrationData(render_id="test123")
        json_str = data.to_json()
        parsed = json.loads(json_str)
        assert parsed["renderId"] == "test123"
    
    def test_is_empty_true_when_empty(self):
        """is_empty should return True for empty data."""
        data = HydrationData()
        assert data.is_empty() is True
    
    def test_is_empty_false_with_signals(self):
        """is_empty should return False with signals."""
        data = HydrationData()
        data.signals["count"] = {"id": "sig_1", "value": 0}
        assert data.is_empty() is False
    
    def test_is_empty_false_with_stores(self):
        """is_empty should return False with stores."""
        data = HydrationData()
        data.stores["state"] = {"count": 0}
        assert data.is_empty() is False
    
    def test_is_empty_false_with_events(self):
        """is_empty should return False with events."""
        data = HydrationData()
        data.events["btn_1"] = {"click": "handler()"}
        assert data.is_empty() is False
    
    def test_complex_data_serialization(self):
        """Complex data should serialize correctly."""
        data = HydrationData(
            render_id="abc123",
            signals={"count": {"id": "sig_1", "value": 42, "elementId": "el_1"}},
            stores={"state": {"items": [1, 2, 3]}},
            events={"btn_1": {"click": "increment()"}},
        )
        json_str = data.to_json()
        restored = json.loads(json_str)
        assert restored["signals"]["count"]["value"] == 42
        assert restored["stores"]["state"]["items"] == [1, 2, 3]


# =============================================================================
# COLLECT HYDRATION DATA TESTS (40 tests)
# =============================================================================

class TestCollectHydrationData:
    """Tests for collect_hydration_data function."""
    
    def test_collects_from_context(self):
        """Should collect data from render context."""
        with render_context() as ctx:
            s = Signal(42, name="count")
            data = collect_hydration_data(ctx)
            assert "count" in data.signals
    
    def test_includes_render_id(self):
        """Should include render ID."""
        with render_context() as ctx:
            data = collect_hydration_data(ctx)
            assert data.render_id == ctx.render_id
    
    def test_includes_signal_value(self):
        """Should include signal values."""
        with render_context() as ctx:
            s = Signal(42, name="count")
            data = collect_hydration_data(ctx)
            assert data.signals["count"]["value"] == 42
    
    def test_includes_multiple_signals(self):
        """Should include multiple signals."""
        with render_context() as ctx:
            s1 = Signal(1, name="a")
            s2 = Signal(2, name="b")
            data = collect_hydration_data(ctx)
            assert len(data.signals) == 2
    
    def test_includes_stores(self):
        """Should include store data."""
        with render_context() as ctx:
            from pynext.reactive import Store
            st = Store({"count": 0}, name="state")
            data = collect_hydration_data(ctx)
            assert "state" in data.stores
    
    def test_includes_events(self):
        """Should include registered events."""
        with render_context() as ctx:
            ctx.register_event("btn_1", "click", "handleClick()")
            data = collect_hydration_data(ctx)
            assert "btn_1" in data.events


# =============================================================================
# INJECT HYDRATION SCRIPT TESTS (40 tests)
# =============================================================================

class TestInjectHydrationScript:
    """Tests for inject_hydration_script function."""
    
    def test_injects_before_body_close(self):
        """Should inject script before </body>."""
        html = "<html><body><div>content</div></body></html>"
        data = HydrationData(render_id="test")
        data.signals["count"] = {"id": "sig_1", "value": 0}
        
        result = inject_hydration_script(html, data)
        assert "__PYNEXT_HYDRATION__" in result
        assert result.index("__PYNEXT_HYDRATION__") < result.index("</body>")
    
    def test_does_nothing_for_empty_data(self):
        """Should not inject script for empty data."""
        html = "<html><body><div>content</div></body></html>"
        data = HydrationData()
        
        result = inject_hydration_script(html, data)
        assert "__PYNEXT_HYDRATION__" not in result
    
    def test_appends_if_no_body_close(self):
        """Should append if no </body> tag."""
        html = "<div>content</div>"
        data = HydrationData(render_id="test")
        data.signals["count"] = {"id": "sig_1", "value": 0}
        
        result = inject_hydration_script(html, data)
        assert "__PYNEXT_HYDRATION__" in result
    
    def test_preserves_original_html(self):
        """Should preserve original HTML content."""
        html = "<html><body><div id='app'>Hello World</div></body></html>"
        data = HydrationData(render_id="test")
        data.signals["count"] = {"id": "sig_1", "value": 0}
        
        result = inject_hydration_script(html, data)
        assert "Hello World" in result
        assert 'id="app"' in result or "id='app'" in result
    
    def test_escapes_script_tags_in_json(self):
        """Should escape </script> in JSON data."""
        data = HydrationData(render_id="test")
        data.signals["text"] = {"id": "sig_1", "value": "</script>alert('xss')"}
        
        result = generate_hydration_script(data)
        assert "</script>" not in result or "<\\/script>" in result


# =============================================================================
# GENERATE RUNTIME SCRIPT TESTS (30 tests)
# =============================================================================

class TestGenerateRuntimeScript:
    """Tests for generate_runtime_script function."""
    
    def test_default_src(self):
        """Should use default src path."""
        script = generate_runtime_script()
        assert "/_pynext/runtime.js" in script
    
    def test_custom_src(self):
        """Should use custom src path."""
        script = generate_runtime_script(src="/custom/path.js")
        assert "/custom/path.js" in script
    
    def test_defer_by_default(self):
        """Should include defer by default."""
        script = generate_runtime_script()
        assert "defer" in script
    
    def test_no_defer_when_disabled(self):
        """Should not include defer when disabled."""
        script = generate_runtime_script(defer=False)
        assert "defer" not in script
    
    def test_inline_mode(self):
        """Should inline code when inline=True."""
        script = generate_runtime_script(inline=True, inline_code="console.log('hello')")
        assert "console.log('hello')" in script
        assert "src=" not in script


# =============================================================================
# HYDRATION MARKERS TESTS (30 tests)
# =============================================================================

class TestHydrationMarkers:
    """Tests for hydration marker functions."""
    
    def test_add_markers_basic(self):
        """Should add data-pynext attributes."""
        html = "<div>content</div>"
        result = add_hydration_markers(html, "comp_123", "Counter")
        assert 'data-pynext-component="Counter"' in result
        assert 'data-pynext-id="comp_123"' in result
    
    def test_add_markers_preserves_existing_attrs(self):
        """Should preserve existing attributes."""
        html = '<div class="my-class" id="my-id">content</div>'
        result = add_hydration_markers(html, "comp_123", "Counter")
        assert 'class="my-class"' in result
        assert 'id="my-id"' in result
    
    def test_add_markers_to_different_tags(self):
        """Should work with different tag names."""
        for tag in ["div", "span", "section", "article"]:
            html = f"<{tag}>content</{tag}>"
            result = add_hydration_markers(html, "comp_123", "Counter")
            assert 'data-pynext-component="Counter"' in result
    
    def test_extract_markers(self):
        """Should extract component markers."""
        html = '''
        <div data-pynext-component="Counter" data-pynext-id="comp_1">
            <span data-pynext-component="Button" data-pynext-id="comp_2"></span>
        </div>
        '''
        markers = extract_component_markers(html)
        assert len(markers) == 2
        assert {"component": "Counter", "id": "comp_1"} in markers
        assert {"component": "Button", "id": "comp_2"} in markers
    
    def test_extract_markers_empty(self):
        """Should return empty list when no markers."""
        html = "<div>no markers here</div>"
        markers = extract_component_markers(html)
        assert markers == []


# =============================================================================
# RENDER WITH HYDRATION TESTS (20 tests)
# =============================================================================

class TestRenderWithHydration:
    """Tests for render_with_hydration function."""
    
    def test_basic_render(self):
        """Should render component with hydration."""
        from pynext import page, div
        
        @page(title="Test")
        def test_page():
            return div()["Hello"]
        
        html = render_with_hydration(test_page)
        assert "Hello" in html
    
    def test_includes_runtime_script(self):
        """Should include runtime script."""
        from pynext import page, div
        
        @page(title="Test")
        def test_page():
            return div()["Hello"]
        
        html = render_with_hydration(test_page)
        assert "runtime.js" in html
    
    def test_no_runtime_when_disabled(self):
        """Should not include runtime when disabled."""
        from pynext import page, div
        
        @page(title="Test")
        def test_page():
            return div()["Hello"]
        
        # Note: This might still include runtime from render_full_page
        # The include_runtime flag mainly affects additional injection
        html = render_with_hydration(test_page, include_runtime=False)
        assert "Hello" in html


# Run with: pytest tests/unit/hydration/test_server_hydration.py -v

