"""
Phase 34.4: WebSocket Chat Tests

Comprehensive tests for WebSocket real-time chat patterns:
- CloseEvent properties
- WebSocket readyState checks
- WebSocket constants (OPEN, CLOSED, etc.)
- Error handling
- Reconnection patterns
- Complete chat example from cookbook

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestCloseEventProperties:
    """Tests for CloseEvent properties."""
    
    def test_code_property(self):
        """CloseEvent.code should pass through."""
        code = '''
def on_close(event):
    close_code = event.code
'''
        result = transpile(code)
        assert 'event.code' in result
        assert '__py.' not in result
    
    def test_reason_property(self):
        """CloseEvent.reason should pass through."""
        code = '''
def on_close(event):
    close_reason = event.reason
'''
        result = transpile(code)
        assert 'event.reason' in result
        assert '__py.' not in result
    
    def test_was_clean_property(self):
        """CloseEvent.wasClean should pass through."""
        code = '''
def on_close(event):
    was_clean = event.wasClean
'''
        result = transpile(code)
        assert 'event.wasClean' in result
        assert '__py.' not in result
    
    def test_close_event_pattern(self):
        """Complete close event handling pattern."""
        code = '''
def on_close(event):
    if event.wasClean:
        console.log(f"Closed cleanly: {event.code}")
    else:
        console.error(f"Connection lost: {event.code} - {event.reason}")
'''
        result = transpile(code)
        assert 'event.wasClean' in result
        assert 'event.code' in result
        assert 'event.reason' in result


class TestWebSocketReadyState:
    """Tests for WebSocket readyState checks."""
    
    def test_readystate_property(self):
        """WebSocket.readyState should pass through."""
        code = '''
def check_connection(ws):
    state = ws.readyState
'''
        result = transpile(code)
        assert 'ws.readyState' in result
        assert '__py.' not in result
    
    def test_readystate_comparison(self):
        """Comparing readyState to WebSocket.OPEN."""
        code = '''
def is_connected(ws):
    return ws.readyState == WebSocket.OPEN
'''
        result = transpile(code)
        assert 'ws.readyState' in result
        assert 'WebSocket.OPEN' in result
    
    def test_readystate_guard_pattern(self):
        """Guard pattern for sending only when open."""
        code = '''
def safe_send(ws, data):
    if ws.readyState == WebSocket.OPEN:
        ws.send(JSON.stringify(data))
    else:
        queue_message(data)
'''
        result = transpile(code)
        assert 'ws.readyState' in result
        assert 'WebSocket.OPEN' in result
        assert 'ws.send' in result


class TestWebSocketConstants:
    """Tests for WebSocket state constants."""
    
    def test_websocket_open_constant(self):
        """WebSocket.OPEN constant should work."""
        code = '''
is_open = ws.readyState == WebSocket.OPEN
'''
        result = transpile(code)
        assert 'WebSocket.OPEN' in result
    
    def test_websocket_closed_constant(self):
        """WebSocket.CLOSED constant should work."""
        code = '''
is_closed = ws.readyState == WebSocket.CLOSED
'''
        result = transpile(code)
        assert 'WebSocket.CLOSED' in result
    
    def test_websocket_connecting_constant(self):
        """WebSocket.CONNECTING constant should work."""
        code = '''
is_connecting = ws.readyState == WebSocket.CONNECTING
'''
        result = transpile(code)
        assert 'WebSocket.CONNECTING' in result
    
    def test_websocket_closing_constant(self):
        """WebSocket.CLOSING constant should work."""
        code = '''
is_closing = ws.readyState == WebSocket.CLOSING
'''
        result = transpile(code)
        assert 'WebSocket.CLOSING' in result


class TestWebSocketErrorHandling:
    """Tests for WebSocket error handling."""
    
    def test_error_event_listener(self):
        """WebSocket error event listener should work."""
        code = '''
ws = WebSocket("wss://api.example.com")

def on_error(event):
    console.error("WebSocket error occurred")

ws.addEventListener("error", on_error)
'''
        result = transpile(code)
        assert 'addEventListener("error"' in result


class TestReconnectionPatterns:
    """Tests for WebSocket reconnection patterns."""
    
    def test_reconnection_with_timeout(self):
        """Reconnection using setTimeout should work."""
        code = '''
reconnect_delay = 1000

def on_close(event):
    setTimeout(connect, reconnect_delay)
'''
        result = transpile(code)
        assert 'setTimeout' in result
    
    def test_exponential_backoff(self):
        """Exponential backoff pattern should work."""
        code = '''
reconnect_delay = 1000
max_delay = 30000

def on_close(event):
    global reconnect_delay
    setTimeout(connect, reconnect_delay)
    reconnect_delay = Math.min(reconnect_delay * 2, max_delay)
'''
        result = transpile(code)
        assert 'setTimeout' in result
        assert 'Math.min' in result


class TestCompleteChatExample:
    """Tests for the complete chat example from cookbook."""
    
    def test_chat_client_transpiles(self):
        """Complete chat client from cookbook should transpile."""
        code = '''
def create_chat_client(ws_url, message_handler):
    reconnect_delay = 1000
    max_delay = 30000
    
    def connect():
        nonlocal reconnect_delay
        ws = WebSocket(ws_url)
        
        def on_open(event):
            nonlocal reconnect_delay
            console.log("Connected to chat server")
            reconnect_delay = 1000
        
        def on_message(event):
            data = JSON.parse(event.data)
            message_handler(data)
        
        def on_close(event):
            console.log(f"Disconnected: {event.code}")
            setTimeout(connect, reconnect_delay)
            reconnect_delay = Math.min(reconnect_delay * 2, max_delay)
        
        def on_error(event):
            console.error("WebSocket error")
        
        ws.addEventListener("open", on_open)
        ws.addEventListener("message", on_message)
        ws.addEventListener("close", on_close)
        ws.addEventListener("error", on_error)
        
        return ws
    
    ws = connect()
    
    def send_message(message):
        if ws.readyState == WebSocket.OPEN:
            ws.send(JSON.stringify(message))
    
    return {"send": send_message}
'''
        result = transpile(code)
        # Verify core WebSocket patterns
        assert 'WebSocket(' in result
        assert 'addEventListener("open"' in result
        assert 'addEventListener("message"' in result
        assert 'addEventListener("close"' in result
        assert 'addEventListener("error"' in result
        assert 'JSON.parse' in result
        assert 'event.data' in result
        assert 'event.code' in result
        assert 'ws.readyState' in result
        assert 'WebSocket.OPEN' in result
        assert 'ws.send' in result
        assert 'setTimeout' in result
        assert 'Math.min' in result

