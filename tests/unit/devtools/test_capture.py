"""
Tests for Event Capture - Filter and Enrich Browser Events.

Tests cover:
- DebugEvent creation and serialization
- EventCapture filtering logic
- Console message handling
- Network request/response handling
- Error and exception handling
- PyNext-specific message parsing
- Deduplication
- Signal and component tracking
"""

import pytest
import time
from unittest.mock import Mock, patch

from pynext.devtools.capture import EventCapture, DebugEvent, EventType


# ============================================
# DebugEvent Tests
# ============================================

class TestDebugEvent:
    """Tests for DebugEvent dataclass."""
    
    def test_to_dict(self):
        """Test event serialization to dict."""
        event = DebugEvent(
            seq=42,
            ts=1702345678.123,
            type=EventType.CONSOLE_LOG,
            data={"text": "Hello"},
            summary="console.log: Hello",
        )
        
        result = event.to_dict()
        
        assert result["seq"] == 42
        assert result["ts"] == 1702345678.123
        assert result["type"] == "console_log"
        assert result["data"] == {"text": "Hello"}
        assert result["summary"] == "console.log: Hello"
    
    def test_to_dict_with_screenshot(self):
        """Test serialization with screenshot."""
        event = DebugEvent(
            seq=1,
            ts=1.0,
            type=EventType.CLICK,
            screenshot="screenshots/001_click.png",
        )
        
        result = event.to_dict()
        
        assert result["screenshot"] == "screenshots/001_click.png"
    
    def test_to_dict_with_source(self):
        """Test serialization with source location."""
        event = DebugEvent(
            seq=1,
            ts=1.0,
            type=EventType.JS_EXCEPTION,
            source="app.js:42:10",
        )
        
        result = event.to_dict()
        
        assert result["source"] == "app.js:42:10"
    
    def test_to_dict_omits_none_values(self):
        """Test that None values are omitted."""
        event = DebugEvent(
            seq=1,
            ts=1.0,
            type=EventType.PAGE_LOAD,
        )
        
        result = event.to_dict()
        
        assert "screenshot" not in result
        assert "source" not in result
    
    def test_from_dict(self):
        """Test event deserialization."""
        data = {
            "seq": 42,
            "ts": 1702345678.123,
            "type": "signal_change",
            "data": {"signal_name": "count", "old_value": 0, "new_value": 1},
            "summary": "Signal count: 0 → 1",
        }
        
        event = DebugEvent.from_dict(data)
        
        assert event.seq == 42
        assert event.type == EventType.SIGNAL_CHANGE
        assert event.data["signal_name"] == "count"
    
    def test_from_dict_with_optional_fields(self):
        """Test deserialization with optional fields."""
        data = {
            "seq": 1,
            "ts": 1.0,
            "type": "click",
            "data": {},
            "summary": "Click",
            "screenshot": "screenshots/001.png",
            "source": "app.js:10",
        }
        
        event = DebugEvent.from_dict(data)
        
        assert event.screenshot == "screenshots/001.png"
        assert event.source == "app.js:10"


class TestEventType:
    """Tests for EventType enum."""
    
    def test_all_types_have_string_values(self):
        """Test that all event types have valid string values."""
        for event_type in EventType:
            assert isinstance(event_type.value, str)
            assert len(event_type.value) > 0
    
    def test_console_types(self):
        """Test console event types."""
        assert EventType.CONSOLE_LOG.value == "console_log"
        assert EventType.CONSOLE_WARN.value == "console_warn"
        assert EventType.CONSOLE_ERROR.value == "console_error"
    
    def test_pynext_types(self):
        """Test PyNext-specific event types."""
        assert EventType.SIGNAL_CHANGE.value == "signal_change"
        assert EventType.EFFECT_RUN.value == "effect_run"
        assert EventType.HYDRATION_COMPLETE.value == "hydration_complete"


# ============================================
# EventCapture Tests
# ============================================

class TestEventCapture:
    """Tests for EventCapture event processor."""
    
    def test_init(self):
        """Test capture initialization."""
        capture = EventCapture()
        
        assert capture.event_count == 0
        assert capture.last_event_time == 0.0
    
    def test_on_event_registers_callback(self):
        """Test callback registration."""
        capture = EventCapture()
        callback = Mock()
        
        capture.on_event(callback)
        
        assert callback in capture._callbacks
    
    def test_remove_callback(self):
        """Test callback removal."""
        capture = EventCapture()
        callback = Mock()
        
        capture.on_event(callback)
        capture.remove_callback(callback)
        
        assert callback not in capture._callbacks
    
    def test_event_count_increments(self):
        """Test that event count increments."""
        capture = EventCapture()
        
        capture.emit_debug_start()
        assert capture.event_count == 1
        
        capture.emit_debug_end()
        assert capture.event_count == 2
    
    def test_last_event_time_updates(self):
        """Test that last event time updates."""
        capture = EventCapture()
        
        before = time.time()
        capture.emit_debug_start()
        after = time.time()
        
        assert before <= capture.last_event_time <= after


class TestEventCaptureConsole:
    """Tests for console message handling."""
    
    def test_handle_console_log(self):
        """Test console.log handling."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Console.messageAdded"
        message.params = {
            "message": {
                "level": "log",
                "text": "Hello World",
                "source": "javascript",
                "url": "http://localhost:3000/app.js",
                "line": 42,
            }
        }
        
        capture.process_cdp_event(message)
        
        assert len(events) == 1
        assert events[0].type == EventType.CONSOLE_LOG
        assert events[0].data["text"] == "Hello World"
    
    def test_handle_console_error(self):
        """Test console.error handling."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Console.messageAdded"
        message.params = {
            "message": {
                "level": "error",
                "text": "Something went wrong",
                "source": "javascript",
            }
        }
        
        capture.process_cdp_event(message)
        
        assert len(events) == 1
        assert events[0].type == EventType.CONSOLE_ERROR
    
    def test_handle_console_warn(self):
        """Test console.warn handling."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Console.messageAdded"
        message.params = {
            "message": {"level": "warning", "text": "Deprecation warning"}
        }
        
        capture.process_cdp_event(message)
        
        assert events[0].type == EventType.CONSOLE_WARN
    
    def test_ignore_empty_console(self):
        """Test that empty console messages are ignored."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Console.messageAdded"
        message.params = {"message": {"level": "log", "text": "   "}}
        
        capture.process_cdp_event(message)
        
        assert len(events) == 0
    
    def test_ignore_deprecation_source(self):
        """Test that deprecation messages are ignored."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Console.messageAdded"
        message.params = {
            "message": {
                "level": "warning",
                "text": "Some deprecation",
                "source": "deprecation",
            }
        }
        
        capture.process_cdp_event(message)
        
        assert len(events) == 0


class TestEventCaptureNetwork:
    """Tests for network event handling."""
    
    def test_handle_network_request(self):
        """Test network request handling."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Network.requestWillBeSent"
        message.params = {
            "requestId": "req123",
            "request": {
                "url": "http://localhost:3000/api/users",
                "method": "GET",
            }
        }
        
        capture.process_cdp_event(message)
        
        assert len(events) == 1
        assert events[0].type == EventType.NETWORK_REQUEST
        assert "/api/users" in events[0].data["url"]
    
    def test_handle_network_response(self):
        """Test network response handling."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        # First send request
        req_msg = Mock()
        req_msg.method = "Network.requestWillBeSent"
        req_msg.params = {
            "requestId": "req123",
            "request": {
                "url": "http://localhost:3000/api/users",
                "method": "GET",
            }
        }
        capture.process_cdp_event(req_msg)
        
        # Then response
        res_msg = Mock()
        res_msg.method = "Network.responseReceived"
        res_msg.params = {
            "requestId": "req123",
            "response": {
                "url": "http://localhost:3000/api/users",
                "status": 200,
            }
        }
        capture.process_cdp_event(res_msg)
        
        assert len(events) == 2
        assert events[1].type == EventType.NETWORK_RESPONSE
        assert events[1].data["status"] == 200
    
    def test_handle_network_error(self):
        """Test network error handling."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        # Add pending request
        capture._pending_requests["req123"] = {
            "url": "http://localhost:3000/api/data",
            "method": "POST",
            "start_time": time.time(),
        }
        
        message = Mock()
        message.method = "Network.loadingFailed"
        message.params = {
            "requestId": "req123",
            "errorText": "net::ERR_CONNECTION_REFUSED",
        }
        
        capture.process_cdp_event(message)
        
        assert len(events) == 1
        assert events[0].type == EventType.NETWORK_ERROR
    
    def test_ignore_static_assets(self):
        """Test that static assets are ignored."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        for ext in [".png", ".jpg", ".gif", ".woff", ".ico"]:
            message = Mock()
            message.method = "Network.requestWillBeSent"
            message.params = {
                "requestId": f"req_{ext}",
                "request": {
                    "url": f"http://localhost:3000/assets/image{ext}",
                    "method": "GET",
                }
            }
            capture.process_cdp_event(message)
        
        assert len(events) == 0


class TestEventCapturePyNext:
    """Tests for PyNext-specific message handling."""
    
    def test_handle_signal_change(self):
        """Test PyNext signal change message."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Console.messageAdded"
        message.params = {
            "message": {
                "level": "log",
                "text": "[PyNext] SIGNAL: view_mode = \"kanban\" (was: \"list\")",
                "url": "http://localhost:3000/issues.py",
                "line": 45,
            }
        }
        
        capture.process_cdp_event(message)
        
        assert len(events) == 1
        assert events[0].type == EventType.SIGNAL_CHANGE
        assert events[0].data["signal_name"] == "view_mode"
    
    def test_handle_hydration_message(self):
        """Test PyNext hydration message."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Console.messageAdded"
        message.params = {
            "message": {
                "level": "log",
                "text": "[PyNext] HYDRATION: complete",
            }
        }
        
        capture.process_cdp_event(message)
        
        assert len(events) == 1
        assert events[0].type == EventType.HYDRATION_COMPLETE
    
    def test_handle_effect_message(self):
        """Test PyNext effect message."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Console.messageAdded"
        message.params = {
            "message": {
                "level": "log",
                "text": "[PyNext] EFFECT: effect_123 deps=[sig_1,sig_2]",
            }
        }
        
        capture.process_cdp_event(message)
        
        assert len(events) == 1
        assert events[0].type == EventType.EFFECT_RUN


class TestEventCaptureExceptions:
    """Tests for JavaScript exception handling."""
    
    def test_handle_exception(self):
        """Test JavaScript exception handling."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Runtime.exceptionThrown"
        message.params = {
            "exceptionDetails": {
                "text": "Uncaught TypeError",
                "url": "http://localhost:3000/app.js",
                "lineNumber": 42,
                "columnNumber": 10,
                "exception": {
                    "description": "TypeError: Cannot read property 'x' of undefined"
                },
                "stackTrace": {
                    "callFrames": [
                        {
                            "functionName": "handleClick",
                            "url": "http://localhost:3000/app.js",
                            "lineNumber": 42,
                            "columnNumber": 10,
                        }
                    ]
                }
            }
        }
        
        capture.process_cdp_event(message)
        
        assert len(events) == 1
        assert events[0].type == EventType.JS_EXCEPTION
        assert "TypeError" in events[0].data["text"]
        assert len(events[0].data["stack"]) == 1
    
    def test_exception_source_location(self):
        """Test that exception includes source location."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Runtime.exceptionThrown"
        message.params = {
            "exceptionDetails": {
                "text": "Error",
                "url": "http://localhost:3000/main.js",
                "lineNumber": 100,
                "columnNumber": 5,
                "exception": {"description": "Error: Test"},
            }
        }
        
        capture.process_cdp_event(message)
        
        assert events[0].source == "main.js:100:5"


class TestEventCaptureDeduplication:
    """Tests for event deduplication."""
    
    def test_dedupe_rapid_console_messages(self):
        """Test that rapid duplicate messages are deduped."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        # Send same message twice rapidly
        message = Mock()
        message.method = "Console.messageAdded"
        message.params = {
            "message": {"level": "log", "text": "Repeated message"}
        }
        
        capture.process_cdp_event(message)
        capture.process_cdp_event(message)  # Should be deduped
        
        assert len(events) == 1
    
    def test_allow_after_dedupe_window(self):
        """Test that messages are allowed after dedupe window."""
        capture = EventCapture()
        capture._dedup_window = 0.01  # 10ms for testing
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = "Console.messageAdded"
        message.params = {
            "message": {"level": "log", "text": "Test message"}
        }
        
        capture.process_cdp_event(message)
        
        import time
        time.sleep(0.02)  # Wait past dedupe window
        
        capture.process_cdp_event(message)
        
        assert len(events) == 2


class TestEventCaptureEmitMethods:
    """Tests for emit helper methods."""
    
    def test_emit_click(self):
        """Test click event emission."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        event = capture.emit_click(
            element={"tagName": "button", "id": "submit", "selector": "#submit"},
            x=100,
            y=200,
        )
        
        assert event.type == EventType.CLICK
        assert event.data["x"] == 100
        assert event.data["y"] == 200
    
    def test_emit_manual_snapshot(self):
        """Test manual snapshot emission."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        event = capture.emit_manual_snapshot("Checking modal")
        
        assert event.type == EventType.MANUAL_SNAPSHOT
        assert event.data["note"] == "Checking modal"
    
    def test_emit_debug_start(self):
        """Test debug start emission."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        event = capture.emit_debug_start()
        
        assert event.type == EventType.DEBUG_START
    
    def test_emit_debug_end(self):
        """Test debug end emission."""
        capture = EventCapture()
        capture.emit_debug_start()
        capture.emit_debug_start()
        
        events = []
        capture.on_event(lambda e: events.append(e))
        
        event = capture.emit_debug_end()
        
        assert event.type == EventType.DEBUG_END
        assert event.data["total_events"] == 3


class TestEventCaptureSignalTracking:
    """Tests for signal registration and tracking."""
    
    def test_register_signal(self):
        """Test signal registration."""
        capture = EventCapture()
        
        capture.register_signal(
            signal_id="sig_124",
            signal_name="view_mode",
            component="issues.py",
            line=45,
        )
        
        info = capture.get_signal_info("sig_124")
        
        assert info is not None
        assert info["name"] == "view_mode"
        assert info["component"] == "issues.py"
        assert info["line"] == 45
    
    def test_get_unknown_signal(self):
        """Test getting info for unknown signal."""
        capture = EventCapture()
        
        info = capture.get_signal_info("unknown_signal")
        
        assert info is None


class TestEventCaptureIgnoredMethods:
    """Tests for ignored CDP methods."""
    
    def test_ignore_noisy_events(self):
        """Test that noisy events are filtered."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        ignored_methods = [
            "Network.dataReceived",
            "Network.loadingFinished",
            "DOM.documentUpdated",
            "Page.frameNavigated",
        ]
        
        for method in ignored_methods:
            message = Mock()
            message.method = method
            message.params = {}
            capture.process_cdp_event(message)
        
        assert len(events) == 0
    
    def test_ignore_non_event_messages(self):
        """Test that non-event messages are ignored."""
        capture = EventCapture()
        events = []
        capture.on_event(lambda e: events.append(e))
        
        message = Mock()
        message.method = None
        message.params = {}
        
        result = capture.process_cdp_event(message)
        
        assert result is None
        assert len(events) == 0

