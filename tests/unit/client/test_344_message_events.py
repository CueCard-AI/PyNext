"""
Phase 34.4: Message Event Tests

Unit tests for MessageEvent transpilation covering:
- postMessage communication
- WebSocket messages
- BroadcastChannel
- MessagePort
- Origin verification

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestMessageEventBasics:
    """Tests for basic MessageEvent properties."""
    
    def test_data_property(self):
        """MessageEvent.data should pass through."""
        code = '''
def on_message(event):
    data = event.data
'''
        result = transpile(code)
        assert 'event.data' in result
        assert '__py.' not in result
    
    def test_origin_property(self):
        """MessageEvent.origin should pass through."""
        code = '''
def on_message(event):
    origin = event.origin
'''
        result = transpile(code)
        assert 'event.origin' in result
        assert '__py.' not in result
    
    def test_source_property(self):
        """MessageEvent.source should pass through."""
        code = '''
def on_message(event):
    source = event.source
'''
        result = transpile(code)
        assert 'event.source' in result
        assert '__py.' not in result
    
    def test_ports_property(self):
        """MessageEvent.ports should pass through."""
        code = '''
def on_message(event):
    ports = event.ports
'''
        result = transpile(code)
        assert 'event.ports' in result
        assert '__py.' not in result
    
    def test_last_event_id_property(self):
        """MessageEvent.lastEventId should pass through."""
        code = '''
def on_message(event):
    event_id = event.lastEventId
'''
        result = transpile(code)
        assert 'event.lastEventId' in result
        assert '__py.' not in result


class TestPostMessagePatterns:
    """Tests for postMessage communication patterns."""
    
    def test_window_message_listener(self):
        """Window message listener should work."""
        code = '''
from pynext.client import window

def on_message(event):
    handle_message(event.data)

window.addEventListener("message", on_message)
'''
        result = transpile(code)
        assert 'addEventListener("message"' in result
    
    def test_origin_verification(self):
        """Origin verification pattern should work."""
        code = '''
from pynext.client import window

def on_message(event):
    if event.origin == "https://trusted.com":
        handle_message(event.data)

window.addEventListener("message", on_message)
'''
        result = transpile(code)
        assert 'event.origin' in result
    
    def test_send_to_iframe(self):
        """Sending message to iframe should work."""
        code = '''
def send_to_iframe(iframe, data, origin):
    iframe.contentWindow.postMessage(data, origin)
'''
        result = transpile(code)
        assert 'postMessage' in result
    
    def test_reply_to_source(self):
        """Replying to message source should work."""
        code = '''
def on_message(event):
    response = {"status": "ok"}
    event.source.postMessage(response, event.origin)
'''
        result = transpile(code)
        assert 'event.source.postMessage' in result
        assert 'event.origin' in result


class TestWebSocketPatterns:
    """Tests for WebSocket message patterns."""
    
    def test_websocket_message_listener(self):
        """WebSocket message listener should work."""
        code = '''
ws = WebSocket("wss://api.example.com")

def on_message(event):
    data = JSON.parse(event.data)
    handle_data(data)

ws.addEventListener("message", on_message)
'''
        result = transpile(code)
        assert 'addEventListener("message"' in result
        assert 'event.data' in result
    
    def test_websocket_open_close(self):
        """WebSocket open/close events should work."""
        code = '''
ws = WebSocket("wss://api.example.com")

def on_open(event):
    show_connected()

def on_close(event):
    show_disconnected()

ws.addEventListener("open", on_open)
ws.addEventListener("close", on_close)
'''
        result = transpile(code)
        assert 'addEventListener("open"' in result
        assert 'addEventListener("close"' in result
    
    def test_websocket_send(self):
        """WebSocket send should work."""
        code = '''
def send_message(ws, data):
    ws.send(JSON.stringify(data))
'''
        result = transpile(code)
        assert 'ws.send' in result


class TestBroadcastChannelPatterns:
    """Tests for BroadcastChannel patterns."""
    
    def test_broadcast_channel_create(self):
        """BroadcastChannel creation should work."""
        code = '''
channel = BroadcastChannel("my-channel")
'''
        result = transpile(code)
        assert 'BroadcastChannel' in result
    
    def test_broadcast_channel_message(self):
        """BroadcastChannel message handling should work."""
        code = '''
channel = BroadcastChannel("sync")

def on_message(event):
    sync_data(event.data)

channel.addEventListener("message", on_message)
'''
        result = transpile(code)
        assert 'addEventListener("message"' in result
        assert 'event.data' in result
    
    def test_broadcast_channel_post(self):
        """BroadcastChannel postMessage should work."""
        code = '''
channel = BroadcastChannel("updates")

def broadcast_update(data):
    channel.postMessage(data)
'''
        result = transpile(code)
        assert 'postMessage' in result

