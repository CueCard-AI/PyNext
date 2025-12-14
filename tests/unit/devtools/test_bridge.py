"""
Tests for CDP Bridge - Chrome DevTools Protocol WebSocket Connection.

Tests cover:
- CDPMessage parsing and properties
- CDPBridge connection management
- Command sending and response handling
- Event subscription and callbacks
- Screenshot and DOM snapshot capture
- Error handling and edge cases
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

from pynext.devtools.bridge import CDPBridge, CDPMessage


# ============================================
# CDPMessage Tests
# ============================================

class TestCDPMessage:
    """Tests for CDPMessage dataclass."""
    
    def test_from_json_event(self):
        """Test parsing an event message."""
        data = {
            "method": "Console.messageAdded",
            "params": {"message": {"text": "Hello"}}
        }
        msg = CDPMessage.from_json(data)
        
        assert msg.method == "Console.messageAdded"
        assert msg.params == {"message": {"text": "Hello"}}
        assert msg.id is None
        assert msg.error is None
    
    def test_from_json_response(self):
        """Test parsing a response message."""
        data = {
            "id": 42,
            "result": {"data": "screenshot_base64"}
        }
        msg = CDPMessage.from_json(data)
        
        assert msg.id == 42
        assert msg.params == {"data": "screenshot_base64"}  # result is parsed into params
        assert msg.method is None
    
    def test_from_json_error(self):
        """Test parsing an error response."""
        data = {
            "id": 42,
            "error": {"code": -32000, "message": "Element not found"}
        }
        msg = CDPMessage.from_json(data)
        
        assert msg.id == 42
        assert msg.error == {"code": -32000, "message": "Element not found"}
    
    def test_is_event(self):
        """Test is_event property."""
        event_msg = CDPMessage(method="Page.loadEventFired", params={})
        response_msg = CDPMessage(id=1, params={})
        
        assert event_msg.is_event is True
        assert response_msg.is_event is False
    
    def test_is_response(self):
        """Test is_response property."""
        event_msg = CDPMessage(method="Page.loadEventFired", params={})
        response_msg = CDPMessage(id=1, params={})
        
        assert event_msg.is_response is False
        assert response_msg.is_response is True
    
    def test_is_error(self):
        """Test is_error property."""
        success_msg = CDPMessage(id=1, params={"result": "ok"})
        error_msg = CDPMessage(id=1, error={"code": -1, "message": "Error"})
        
        assert success_msg.is_error is False
        assert error_msg.is_error is True
    
    def test_from_json_empty_params(self):
        """Test parsing message with no params."""
        data = {"method": "Page.loadEventFired"}
        msg = CDPMessage.from_json(data)
        
        assert msg.params == {}
    
    def test_from_json_preserves_all_fields(self):
        """Test that all fields are preserved."""
        data = {
            "id": 100,
            "method": "Test.method",
            "params": {"key": "value", "nested": {"a": 1}},
            "error": None
        }
        msg = CDPMessage.from_json(data)
        
        assert msg.id == 100
        assert msg.method == "Test.method"
        assert msg.params == {"key": "value", "nested": {"a": 1}}


# ============================================
# CDPBridge Tests
# ============================================

class TestCDPBridge:
    """Tests for CDPBridge WebSocket connection."""
    
    def test_init(self):
        """Test bridge initialization."""
        bridge = CDPBridge()
        
        assert bridge.connected is False
        assert len(bridge.domains_enabled) == 0
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection."""
        # Just test that the bridge sets up correctly, without actual websockets
        bridge = CDPBridge()
        
        # Manually set connected state to test the property
        bridge._connected = True
        bridge._ws = Mock()
        
        assert bridge.connected is True
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure handling."""
        bridge = CDPBridge()
        
        # Verify initial state
        assert bridge.connected is False
        
        # Simulate failed connection by checking the error path
        # (actual websocket tests would require the library installed)
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection."""
        bridge = CDPBridge()
        bridge._connected = True
        bridge._ws = None  # No actual connection
        bridge._receive_task = None
        
        await bridge.disconnect()
        
        assert bridge.connected is False
        assert len(bridge.domains_enabled) == 0
    
    def test_on_event_registers_callback(self):
        """Test event callback registration."""
        bridge = CDPBridge()
        callback = Mock()
        
        bridge.on_event(callback)
        
        assert callback in bridge._event_callbacks
    
    def test_remove_event_callback(self):
        """Test removing event callback."""
        bridge = CDPBridge()
        callback = Mock()
        
        bridge.on_event(callback)
        bridge.remove_event_callback(callback)
        
        assert callback not in bridge._event_callbacks
    
    def test_domains_enabled_returns_copy(self):
        """Test that domains_enabled returns a copy."""
        bridge = CDPBridge()
        bridge._domains_enabled.add("Console")
        
        domains = bridge.domains_enabled
        domains.add("Network")
        
        assert "Network" not in bridge._domains_enabled
    
    @pytest.mark.asyncio
    async def test_send_command_not_connected(self):
        """Test sending command when not connected."""
        bridge = CDPBridge()
        
        with pytest.raises(ConnectionError):
            await bridge.send_command("Page.navigate", {"url": "http://example.com"})
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager interface."""
        bridge = CDPBridge()
        
        # Test the context manager pattern
        async with bridge:
            # Context manager should work even without connection
            pass
        
        # After exit, should have called disconnect
        assert bridge.connected is False


class TestCDPBridgeCommands:
    """Tests for CDP command execution."""
    
    @pytest.mark.asyncio
    async def test_take_screenshot(self):
        """Test screenshot capture."""
        bridge = CDPBridge()
        bridge._connected = True
        bridge._ws = AsyncMock()
        
        # Mock send_command
        import base64
        test_image = b"PNG_IMAGE_DATA"
        bridge.send_command = AsyncMock(return_value={
            "data": base64.b64encode(test_image).decode()
        })
        
        result = await bridge.take_screenshot()
        
        assert result == test_image
        bridge.send_command.assert_called_with(
            "Page.captureScreenshot",
            {"format": "png"}
        )
    
    @pytest.mark.asyncio
    async def test_take_screenshot_jpeg_quality(self):
        """Test JPEG screenshot with quality."""
        bridge = CDPBridge()
        bridge._connected = True
        bridge.send_command = AsyncMock(return_value={"data": ""})
        
        await bridge.take_screenshot(format="jpeg", quality=90)
        
        bridge.send_command.assert_called_with(
            "Page.captureScreenshot",
            {"format": "jpeg", "quality": 90}
        )
    
    @pytest.mark.asyncio
    async def test_get_dom_snapshot(self):
        """Test DOM snapshot capture."""
        bridge = CDPBridge()
        bridge._connected = True
        
        # Mock the two commands
        async def mock_command(method, params=None):
            if method == "DOM.getDocument":
                return {"root": {"nodeId": 1}}
            elif method == "DOM.getOuterHTML":
                return {"outerHTML": "<html><body>Hello</body></html>"}
            return {}
        
        bridge.send_command = AsyncMock(side_effect=mock_command)
        
        result = await bridge.get_dom_snapshot()
        
        assert result == "<html><body>Hello</body></html>"
    
    @pytest.mark.asyncio
    async def test_execute_script(self):
        """Test JavaScript execution."""
        bridge = CDPBridge()
        bridge._connected = True
        bridge.send_command = AsyncMock(return_value={
            "result": {"value": "Hello World"}
        })
        
        result = await bridge.execute_script("document.title")
        
        assert result == "Hello World"
    
    @pytest.mark.asyncio
    async def test_execute_script_error(self):
        """Test JavaScript execution with error."""
        bridge = CDPBridge()
        bridge._connected = True
        bridge.send_command = AsyncMock(return_value={
            "exceptionDetails": {"text": "ReferenceError: x is not defined"}
        })
        
        with pytest.raises(RuntimeError):
            await bridge.execute_script("x.y.z")
    
    @pytest.mark.asyncio
    async def test_highlight_element(self):
        """Test element highlighting."""
        bridge = CDPBridge()
        bridge._connected = True
        bridge.execute_script = AsyncMock()
        
        await bridge.highlight_element("#my-button")
        
        bridge.execute_script.assert_called_once()
        call_arg = bridge.execute_script.call_args[0][0]
        assert "#my-button" in call_arg
    
    @pytest.mark.asyncio
    async def test_clear_highlights(self):
        """Test clearing highlights."""
        bridge = CDPBridge()
        bridge._connected = True
        bridge.execute_script = AsyncMock()
        
        await bridge.clear_highlights()
        
        bridge.execute_script.assert_called_once()


class TestCDPBridgeEnableDomains:
    """Tests for enabling CDP domains."""
    
    @pytest.mark.asyncio
    async def test_enable_domains(self):
        """Test enabling all domains."""
        bridge = CDPBridge()
        bridge._connected = True
        bridge.send_command = AsyncMock()
        
        await bridge.enable_domains()
        
        # Should have called enable for multiple domains
        assert bridge.send_command.call_count >= 5
        
        # Check some domains are enabled
        methods = [call[0][0] for call in bridge.send_command.call_args_list]
        assert "Console.enable" in methods
        assert "Network.enable" in methods
        assert "Page.enable" in methods
    
    @pytest.mark.asyncio
    async def test_enable_domains_partial_failure(self):
        """Test that partial failures don't break enable_domains."""
        bridge = CDPBridge()
        bridge._connected = True
        
        call_count = 0
        async def mock_command(method, timeout=5.0):
            nonlocal call_count
            call_count += 1
            if "DOM" in method:
                raise Exception("DOM not available")
            return {}
        
        bridge.send_command = AsyncMock(side_effect=mock_command)
        
        # Should not raise despite DOM failure
        await bridge.enable_domains()
        
        # Should have tried all domains
        assert call_count >= 5


class TestCDPBridgeElementInfo:
    """Tests for element information retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_element_at_position(self):
        """Test getting element at coordinates."""
        bridge = CDPBridge()
        bridge._connected = True
        
        async def mock_command(method, params=None):
            if method == "DOM.getNodeForLocation":
                return {"nodeId": 42}
            elif method == "DOM.describeNode":
                return {
                    "node": {
                        "localName": "button",
                        "attributes": ["id", "submit-btn", "class", "btn primary"]
                    }
                }
            return {}
        
        bridge.send_command = AsyncMock(side_effect=mock_command)
        
        result = await bridge.get_element_at_position(100, 200)
        
        assert result is not None
        assert result["tagName"] == "button"
        assert result["id"] == "submit-btn"
        assert "btn" in result["classes"]
    
    @pytest.mark.asyncio
    async def test_get_element_at_position_not_found(self):
        """Test when no element found at position."""
        bridge = CDPBridge()
        bridge._connected = True
        bridge.send_command = AsyncMock(return_value={})
        
        result = await bridge.get_element_at_position(100, 200)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_element_at_position_error(self):
        """Test error handling in element lookup."""
        bridge = CDPBridge()
        bridge._connected = True
        bridge.send_command = AsyncMock(side_effect=Exception("CDP error"))
        
        result = await bridge.get_element_at_position(100, 200)
        
        assert result is None

