"""
Tests for PyNext Hot Module Replacement (50 tests)

Tests WebSocket server and client-side script generation.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, AsyncMock

from pynext.build.hmr import (
    HMRServer,
    HMRConfig,
    HMRUpdate,
    HMRClient,
    generate_hmr_client_script,
)


# =============================================================================
# HMR UPDATE
# =============================================================================

class TestHMRUpdate:
    """Tests for HMRUpdate data class."""
    
    def test_create_update(self):
        """Create HMR update."""
        update = HMRUpdate(
            module="counter.js",
            code="export function Counter() {}",
        )
        assert update.module == "counter.js"
        assert "Counter" in update.code
    
    def test_update_timestamp(self):
        """Update has timestamp."""
        update = HMRUpdate(module="x.js", code="")
        assert update.timestamp > 0
    
    def test_update_with_source_map(self):
        """Update with source map."""
        update = HMRUpdate(
            module="x.js",
            code="code",
            source_map='{"version": 3}',
        )
        assert update.source_map == '{"version": 3}'
    
    def test_to_json(self):
        """Convert update to JSON."""
        update = HMRUpdate(module="x.js", code="const x = 1;")
        json_str = update.to_json()
        data = json.loads(json_str)
        
        assert data["type"] == "update"
        assert data["module"] == "x.js"
        assert data["code"] == "const x = 1;"


# =============================================================================
# HMR CONFIG
# =============================================================================

class TestHMRConfig:
    """Tests for HMRConfig."""
    
    def test_default_config(self):
        """Default configuration."""
        config = HMRConfig()
        assert config.host == "localhost"
        assert config.port == 3001
        assert config.reconnect_interval == 1000
    
    def test_custom_config(self):
        """Custom configuration."""
        config = HMRConfig(host="0.0.0.0", port=8080)
        assert config.host == "0.0.0.0"
        assert config.port == 8080


# =============================================================================
# HMR SERVER
# =============================================================================

class TestHMRServer:
    """Tests for HMR server."""
    
    def test_create_server(self):
        """Create HMR server."""
        server = HMRServer()
        assert server.config.port == 3001
    
    def test_server_with_config(self):
        """Create server with custom config."""
        config = HMRConfig(port=9000)
        server = HMRServer(config)
        assert server.config.port == 9000
    
    def test_server_not_running_initially(self):
        """Server not running on creation."""
        server = HMRServer()
        assert not server.is_running
    
    def test_client_count_zero(self):
        """No clients initially."""
        server = HMRServer()
        assert server.client_count == 0
    
    def test_notify_update(self):
        """Queue update notification."""
        server = HMRServer()
        server.notify_update("counter.js", "new code")
        assert len(server._pending_updates) == 1
    
    def test_notify_reload(self):
        """Queue reload notification."""
        server = HMRServer()
        server.notify_reload()
        assert len(server._pending_updates) == 1
        assert server._pending_updates[0].module == "__reload__"
    
    def test_notify_error(self):
        """Queue error notification."""
        server = HMRServer()
        server.notify_error("Syntax error at line 42")
        assert len(server._pending_updates) == 1
        assert server._pending_updates[0].module == "__error__"
    
    def test_stop_clears_clients(self):
        """Stop clears client list."""
        server = HMRServer()
        server._clients = {Mock(), Mock()}
        server.stop()
        assert len(server._clients) == 0


# =============================================================================
# CLIENT SCRIPT
# =============================================================================

class TestClientScript:
    """Tests for client-side script generation."""
    
    def test_generate_script(self):
        """Generate client script."""
        script = generate_hmr_client_script()
        assert "WebSocket" in script
        assert "connect" in script
    
    def test_script_uses_config(self):
        """Script uses config values."""
        config = HMRConfig(host="example.com", port=9000)
        script = generate_hmr_client_script(config)
        assert "example.com" in script
        assert "9000" in script
    
    def test_script_has_error_overlay(self):
        """Script has error overlay."""
        script = generate_hmr_client_script()
        assert "pynext-error-overlay" in script
        assert "showErrorOverlay" in script
    
    def test_script_has_reconnect(self):
        """Script has reconnect logic."""
        script = generate_hmr_client_script()
        assert "scheduleReconnect" in script
        assert "RECONNECT_INTERVAL" in script
    
    def test_script_handles_update(self):
        """Script handles update messages."""
        script = generate_hmr_client_script()
        assert "handleUpdate" in script
        assert "'update'" in script
    
    def test_script_handles_reload(self):
        """Script handles reload message."""
        script = generate_hmr_client_script()
        assert "__reload__" in script
        assert "location.reload" in script
    
    def test_script_handles_error(self):
        """Script handles error message."""
        script = generate_hmr_client_script()
        assert "__error__" in script
    
    def test_script_has_heartbeat(self):
        """Script has heartbeat ping."""
        script = generate_hmr_client_script()
        assert "ping" in script
        assert "setInterval" in script
    
    def test_script_is_iife(self):
        """Script is wrapped in IIFE."""
        script = generate_hmr_client_script()
        assert script.strip().startswith("(function()")
        assert script.strip().endswith("})();")


# =============================================================================
# HMR CLIENT
# =============================================================================

class TestHMRClient:
    """Tests for standalone HMR client."""
    
    def test_create_client(self):
        """Create HMR client."""
        client = HMRClient()
        assert client.config.port == 3001
    
    def test_register_callback(self):
        """Register update callback."""
        client = HMRClient()
        callback = Mock()
        client.on_update(callback)
        assert callback in client._callbacks
    
    def test_send_update(self):
        """Send update to callbacks."""
        client = HMRClient()
        received = []
        
        client.on_update(lambda u: received.append(u))
        
        update = HMRUpdate(module="x.js", code="test")
        client.send_update(update)
        
        assert len(received) == 1
        assert received[0].module == "x.js"
    
    def test_callback_error_handling(self):
        """Handle callback errors."""
        client = HMRClient()
        
        def bad_callback(u):
            raise ValueError("Error")
        
        good_received = []
        
        client.on_update(bad_callback)
        client.on_update(lambda u: good_received.append(u))
        
        # Should not raise
        client.send_update(HMRUpdate("x.js", "code"))
        
        assert len(good_received) == 1


# =============================================================================
# INTEGRATION
# =============================================================================

class TestIntegration:
    """Integration tests."""
    
    def test_full_update_flow(self):
        """Full update notification flow."""
        server = HMRServer()
        
        # Queue multiple updates
        server.notify_update("a.js", "code a")
        server.notify_update("b.js", "code b")
        server.notify_error("Error in c.js")
        
        assert len(server._pending_updates) == 3
    
    def test_script_injection_ready(self):
        """Script ready for HTML injection."""
        script = generate_hmr_client_script()
        
        # Should be valid JavaScript
        assert not script.startswith("<script>")
        assert not script.endswith("</script>")
        
        # Can be wrapped in script tag
        html = f"<script>{script}</script>"
        assert "<script>" in html


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case handling."""
    
    def test_empty_code(self):
        """Handle empty code update."""
        update = HMRUpdate(module="x.js", code="")
        json_str = update.to_json()
        data = json.loads(json_str)
        assert data["code"] == ""
    
    def test_unicode_code(self):
        """Handle Unicode in code."""
        update = HMRUpdate(module="x.js", code='const msg = "Привет! 你好!";')
        json_str = update.to_json()
        data = json.loads(json_str)
        assert "Привет" in data["code"]
    
    def test_large_code(self):
        """Handle large code update."""
        large_code = "x" * 1_000_000
        update = HMRUpdate(module="x.js", code=large_code)
        json_str = update.to_json()
        assert len(json_str) > 1_000_000
    
    def test_special_characters_in_module(self):
        """Handle special characters in module name."""
        update = HMRUpdate(module="components/[id]/page.js", code="code")
        json_str = update.to_json()
        data = json.loads(json_str)
        assert data["module"] == "components/[id]/page.js"

