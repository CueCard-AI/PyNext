"""
Unit tests for Browser API Hooks

Tests for:
- use_event_source() — SSE connections
- use_visibility() — Tab visibility tracking
- use_online() — Network status detection
- SSEHandle — Connection control
- JavaScript runtime generation
"""

import pytest
import json


class TestUseEventSource:
    """Tests for SSE connection hook."""
    
    def test_returns_sse_handle(self):
        from pynext.core.client import use_event_source, SSEHandle, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {
            "message": lambda data: None
        })
        
        assert isinstance(handle, SSEHandle)
    
    def test_generates_connect_js(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {
            "message": lambda data: None
        })
        
        js = handle.get_js_init()
        assert "__pynext__.sse.connect" in js
    
    def test_url_is_stored(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/my-events", {
            "update": lambda data: None
        })
        
        assert handle.url == "/api/my-events"
    
    def test_single_handler(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {
            "notification": lambda data: print(data)
        })
        
        config = handle.to_dict()
        assert "notification" in config["handlers"]
    
    def test_multiple_handlers(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {
            "notification": lambda data: None,
            "task_update": lambda data: None,
            "user_join": lambda data: None,
        })
        
        config = handle.to_dict()
        assert len(config["handlers"]) == 3
        assert "notification" in config["handlers"]
        assert "task_update" in config["handlers"]
        assert "user_join" in config["handlers"]
    
    def test_handler_generates_js_function(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {
            "test": lambda data: print(data)
        })
        
        config = handle.to_dict()
        handler_js = config["handlers"]["test"]
        
        # Should be a JS function string
        assert "function" in handler_js or "=>" in handler_js or handler_js.startswith("function")
    
    def test_default_options(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None})
        
        config = handle.to_dict()
        assert config["options"]["reconnect"] == True
        assert config["options"]["reconnectDelay"] == 1000
    
    def test_reconnect_enabled(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None}, {
            "reconnect": True
        })
        
        config = handle.to_dict()
        assert config["options"]["reconnect"] == True
    
    def test_reconnect_delay_custom(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None}, {
            "reconnect_delay": 5000
        })
        
        config = handle.to_dict()
        assert config["options"]["reconnectDelay"] == 5000
    
    def test_reconnect_disabled(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None}, {
            "reconnect": False
        })
        
        config = handle.to_dict()
        assert config["options"]["reconnect"] == False
    
    def test_close_generates_js(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None})
        
        js = handle.close()
        assert "__pynext__.sse.close" in js
        assert handle.id in js
    
    def test_handle_has_connection_id(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None})
        
        assert handle.id is not None
        assert handle.id.startswith("sse_")
    
    def test_empty_handlers_dict(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {})
        
        config = handle.to_dict()
        assert config["handlers"] == {}
    
    def test_special_chars_in_url(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events?user=123&token=abc", {"msg": lambda d: None})
        
        assert handle.url == "/api/events?user=123&token=abc"
        config = handle.to_dict()
        assert config["url"] == "/api/events?user=123&token=abc"


class TestUseVisibility:
    """Tests for tab visibility tracking hook."""
    
    def test_returns_signal(self):
        from pynext.core.client import use_visibility, VisibilitySignal, reset_client_state
        reset_client_state()
        
        signal = use_visibility()
        
        assert isinstance(signal, VisibilitySignal)
    
    def test_initial_value_true(self):
        from pynext.core.client import use_visibility, reset_client_state
        reset_client_state()
        
        signal = use_visibility()
        
        # Initial value should be True (assuming visible)
        assert signal.value == True
        assert signal() == True
    
    def test_generates_init_js(self):
        from pynext.core.client import use_visibility, reset_client_state
        reset_client_state()
        
        signal = use_visibility()
        
        js = signal.get_js_init()
        assert "__pynext__.browser.initVisibility" in js
        assert signal.id in js
    
    def test_signal_has_value_property(self):
        from pynext.core.client import use_visibility, reset_client_state
        reset_client_state()
        
        signal = use_visibility()
        
        assert hasattr(signal, 'value')
        assert isinstance(signal.value, bool)
    
    def test_signal_id_is_unique(self):
        from pynext.core.client import use_visibility, reset_client_state
        reset_client_state()
        
        signal = use_visibility()
        
        assert signal.id is not None
        assert signal.id.startswith("visibility_")
    
    def test_to_dict_includes_type(self):
        from pynext.core.client import use_visibility, reset_client_state
        reset_client_state()
        
        signal = use_visibility()
        
        data = signal.to_dict()
        assert data["type"] == "visibility"
        assert data["id"] == signal.id
    
    def test_callable_returns_value(self):
        from pynext.core.client import use_visibility, reset_client_state
        reset_client_state()
        
        signal = use_visibility()
        
        # Should be callable
        result = signal()
        assert result == signal.value
    
    def test_multiple_calls_same_signal(self):
        from pynext.core.client import use_visibility, reset_client_state
        reset_client_state()
        
        signal1 = use_visibility()
        signal2 = use_visibility()
        
        # Should return same signal (singleton)
        assert signal1 is signal2


class TestUseOnline:
    """Tests for network status hook."""
    
    def test_returns_signal(self):
        from pynext.core.client import use_online, OnlineSignal, reset_client_state
        reset_client_state()
        
        signal = use_online()
        
        assert isinstance(signal, OnlineSignal)
    
    def test_initial_value_true(self):
        from pynext.core.client import use_online, reset_client_state
        reset_client_state()
        
        signal = use_online()
        
        # Initial value should be True (assuming online)
        assert signal.value == True
        assert signal() == True
    
    def test_generates_init_js(self):
        from pynext.core.client import use_online, reset_client_state
        reset_client_state()
        
        signal = use_online()
        
        js = signal.get_js_init()
        assert "__pynext__.browser.initOnline" in js
        assert signal.id in js
    
    def test_signal_has_value_property(self):
        from pynext.core.client import use_online, reset_client_state
        reset_client_state()
        
        signal = use_online()
        
        assert hasattr(signal, 'value')
        assert isinstance(signal.value, bool)
    
    def test_signal_id_is_unique(self):
        from pynext.core.client import use_online, reset_client_state
        reset_client_state()
        
        signal = use_online()
        
        assert signal.id is not None
        assert signal.id.startswith("online_")
    
    def test_to_dict_includes_type(self):
        from pynext.core.client import use_online, reset_client_state
        reset_client_state()
        
        signal = use_online()
        
        data = signal.to_dict()
        assert data["type"] == "online"
        assert data["id"] == signal.id
    
    def test_callable_returns_value(self):
        from pynext.core.client import use_online, reset_client_state
        reset_client_state()
        
        signal = use_online()
        
        # Should be callable
        result = signal()
        assert result == signal.value
    
    def test_multiple_calls_same_signal(self):
        from pynext.core.client import use_online, reset_client_state
        reset_client_state()
        
        signal1 = use_online()
        signal2 = use_online()
        
        # Should return same signal (singleton)
        assert signal1 is signal2


class TestSSEHandle:
    """Tests for SSE connection handle."""
    
    def test_close_method_exists(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None})
        
        assert hasattr(handle, 'close')
        assert callable(handle.close)
    
    def test_close_returns_js_string(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None})
        
        result = handle.close()
        assert isinstance(result, str)
        assert "__pynext__.sse.close" in result
    
    def test_connection_id_accessible(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None})
        
        assert handle.id is not None
        assert isinstance(handle.id, str)
    
    def test_url_accessible(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/my-endpoint", {"msg": lambda d: None})
        
        assert handle.url == "/api/my-endpoint"
    
    def test_is_connected_property(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None})
        
        # Should return JS expression
        assert "__pynext__.sse.isConnected" in handle.is_connected
        assert handle.id in handle.is_connected
    
    def test_reconnect_method(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/events", {"msg": lambda d: None})
        
        assert hasattr(handle, 'reconnect')
        js = handle.reconnect()
        assert "__pynext__.sse.reconnect" in js


class TestJavaScriptRuntime:
    """Tests for JavaScript runtime file content."""
    
    def test_sse_js_exists(self):
        import os
        sse_path = os.path.join(
            os.path.dirname(__file__), 
            "../../pynext/runtime/sse.js"
        )
        assert os.path.exists(sse_path)
    
    def test_sse_js_has_connections_object(self):
        import os
        sse_path = os.path.join(os.path.dirname(__file__), "../../pynext/runtime/sse.js")
        with open(sse_path) as f:
            content = f.read()
        
        assert "connections:" in content
    
    def test_sse_js_has_connect_function(self):
        import os
        sse_path = os.path.join(os.path.dirname(__file__), "../../pynext/runtime/sse.js")
        with open(sse_path) as f:
            content = f.read()
        
        assert "connect:" in content or "connect: function" in content
    
    def test_sse_js_has_close_function(self):
        import os
        sse_path = os.path.join(os.path.dirname(__file__), "../../pynext/runtime/sse.js")
        with open(sse_path) as f:
            content = f.read()
        
        assert "close:" in content or "close: function" in content
    
    def test_sse_js_error_handler(self):
        import os
        sse_path = os.path.join(os.path.dirname(__file__), "../../pynext/runtime/sse.js")
        with open(sse_path) as f:
            content = f.read()
        
        assert "onerror" in content
    
    def test_browser_js_exists(self):
        import os
        browser_path = os.path.join(
            os.path.dirname(__file__), 
            "../../pynext/runtime/browser.js"
        )
        assert os.path.exists(browser_path)
    
    def test_browser_js_has_init_visibility(self):
        import os
        browser_path = os.path.join(os.path.dirname(__file__), "../../pynext/runtime/browser.js")
        with open(browser_path) as f:
            content = f.read()
        
        assert "initVisibility" in content
    
    def test_browser_js_has_init_online(self):
        import os
        browser_path = os.path.join(os.path.dirname(__file__), "../../pynext/runtime/browser.js")
        with open(browser_path) as f:
            content = f.read()
        
        assert "initOnline" in content
    
    def test_browser_js_visibility_uses_hidden(self):
        import os
        browser_path = os.path.join(os.path.dirname(__file__), "../../pynext/runtime/browser.js")
        with open(browser_path) as f:
            content = f.read()
        
        assert "document.hidden" in content
    
    def test_browser_js_online_uses_navigator(self):
        import os
        browser_path = os.path.join(os.path.dirname(__file__), "../../pynext/runtime/browser.js")
        with open(browser_path) as f:
            content = f.read()
        
        assert "navigator.onLine" in content


class TestExports:
    """Tests for proper module exports."""
    
    def test_use_event_source_exported_from_pynext(self):
        from pynext import use_event_source
        assert use_event_source is not None
    
    def test_use_visibility_exported_from_pynext(self):
        from pynext import use_visibility
        assert use_visibility is not None
    
    def test_use_online_exported_from_pynext(self):
        from pynext import use_online
        assert use_online is not None
    
    def test_sse_handle_exported(self):
        from pynext import SSEHandle
        assert SSEHandle is not None
    
    def test_visibility_signal_exported(self):
        from pynext import VisibilitySignal
        assert VisibilitySignal is not None
    
    def test_online_signal_exported(self):
        from pynext import OnlineSignal
        assert OnlineSignal is not None


class TestHydrationData:
    """Tests for hydration data generation."""
    
    def test_hydration_includes_sse(self):
        from pynext.core.client import (
            use_event_source, 
            get_client_hydration_data, 
            reset_client_state
        )
        reset_client_state()
        
        use_event_source("/api/events", {"msg": lambda d: None})
        
        data = get_client_hydration_data()
        assert "sse" in data
        assert len(data["sse"]) == 1
    
    def test_hydration_includes_visibility(self):
        from pynext.core.client import (
            use_visibility, 
            get_client_hydration_data, 
            reset_client_state
        )
        reset_client_state()
        
        use_visibility()
        
        data = get_client_hydration_data()
        assert "visibility" in data
        assert data["visibility"] is not None
    
    def test_hydration_includes_online(self):
        from pynext.core.client import (
            use_online, 
            get_client_hydration_data, 
            reset_client_state
        )
        reset_client_state()
        
        use_online()
        
        data = get_client_hydration_data()
        assert "online" in data
        assert data["online"] is not None
    
    def test_reset_clears_all(self):
        from pynext.core.client import (
            use_event_source,
            use_visibility,
            use_online,
            get_client_hydration_data, 
            reset_client_state
        )
        
        use_event_source("/api/events", {"msg": lambda d: None})
        use_visibility()
        use_online()
        
        reset_client_state()
        
        data = get_client_hydration_data()
        assert data["sse"] == []
        assert data["visibility"] is None
        assert data["online"] is None


class TestIntegrationPatterns:
    """Tests for common usage patterns."""
    
    def test_sse_with_multiple_events(self):
        from pynext.core.client import use_event_source, reset_client_state
        reset_client_state()
        
        handle = use_event_source("/api/live", {
            "notification": lambda d: None,
            "task_update": lambda d: None,
            "user_status": lambda d: None,
        }, {
            "reconnect": True,
            "reconnect_delay": 2000,
        })
        
        config = handle.to_dict()
        assert len(config["handlers"]) == 3
        assert config["options"]["reconnectDelay"] == 2000
    
    def test_visibility_signal_usage(self):
        from pynext.core.client import use_visibility, reset_client_state
        reset_client_state()
        
        is_visible = use_visibility()
        
        # Simulate conditional logic
        if is_visible.value:
            action = "poll"
        else:
            action = "pause"
        
        assert action == "poll"  # Initially visible
    
    def test_online_signal_usage(self):
        from pynext.core.client import use_online, reset_client_state
        reset_client_state()
        
        is_online = use_online()
        
        # Simulate conditional logic
        button_disabled = not is_online.value
        
        assert button_disabled == False  # Initially online
    
    def test_combined_browser_apis(self):
        from pynext.core.client import (
            use_event_source,
            use_visibility,
            use_online,
            get_client_hydration_data,
            reset_client_state
        )
        reset_client_state()
        
        # Use all three APIs together
        sse = use_event_source("/api/events", {"update": lambda d: None})
        is_visible = use_visibility()
        is_online = use_online()
        
        # All should be registered
        data = get_client_hydration_data()
        assert len(data["sse"]) == 1
        assert data["visibility"] is not None
        assert data["online"] is not None
        
        # All should be usable
        assert sse.url == "/api/events"
        assert is_visible.value == True
        assert is_online.value == True

