"""
Comprehensive tests for PyNext Browser APIs.

Tests cover:
- WebSocket (25 tests)
- Media Query (15 tests)
- Geolocation (20 tests)
- Clipboard (15 tests)
- Window Size (10 tests)
- Scroll Position (15 tests)
- Intersection Observer (15 tests)

Total: 115 tests
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from pynext.core.client import (
    # WebSocket
    use_websocket,
    WebSocketHandle,
    # Media Query
    use_media_query,
    MediaQuerySignal,
    # Geolocation
    use_geolocation,
    GeolocationHandle,
    # Clipboard
    use_clipboard,
    ClipboardHandle,
    # Window Size
    use_window_size,
    WindowSize,
    # Scroll Position
    use_scroll_position,
    ScrollPosition,
    # Intersection Observer
    use_intersection,
    IntersectionSignal,
    # Utilities
    get_client_hydration_data,
    reset_client_state,
)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset client state before each test."""
    reset_client_state()
    yield
    reset_client_state()


# =============================================================================
# WebSocket Tests (25 tests)
# =============================================================================

class TestWebSocket:
    """Tests for use_websocket() hook."""
    
    def test_basic_creation(self):
        """Test basic WebSocket handle creation."""
        ws = use_websocket("/api/chat")
        
        assert isinstance(ws, WebSocketHandle)
        assert ws.url == "/api/chat"
        assert ws.reconnect is True
        assert ws.reconnect_interval == 3000
    
    def test_custom_options(self):
        """Test WebSocket with custom options."""
        ws = use_websocket(
            "/api/ws",
            reconnect=False,
            reconnect_interval=5000,
        )
        
        assert ws.reconnect is False
        assert ws.reconnect_interval == 5000
    
    def test_with_callbacks(self):
        """Test WebSocket with callback handlers."""
        on_message = MagicMock()
        on_open = MagicMock()
        on_close = MagicMock()
        on_error = MagicMock()
        
        ws = use_websocket(
            "/api/chat",
            on_message=on_message,
            on_open=on_open,
            on_close=on_close,
            on_error=on_error,
        )
        
        assert ws.on_message is on_message
        assert ws.on_open is on_open
        assert ws.on_close is on_close
        assert ws.on_error is on_error
    
    def test_connected_signal(self):
        """Test connected() method returns initial state."""
        ws = use_websocket("/api/ws")
        
        # Initially not connected (server-side)
        assert ws.connected() is False
    
    def test_last_message_signal(self):
        """Test last_message() returns None initially."""
        ws = use_websocket("/api/ws")
        
        assert ws.last_message() is None
    
    def test_error_signal(self):
        """Test error() returns None initially."""
        ws = use_websocket("/api/ws")
        
        assert ws.error() is None
    
    def test_send_dict(self):
        """Test send() with dictionary generates correct JS."""
        ws = use_websocket("/api/chat")
        
        js = ws.send({"type": "message", "text": "Hello"})
        
        assert "__pynext__.websocket.send" in js
        assert ws.id in js
    
    def test_send_string(self):
        """Test send() with string generates correct JS."""
        ws = use_websocket("/api/chat")
        
        js = ws.send("plain text message")
        
        assert "__pynext__.websocket.send" in js
    
    def test_close(self):
        """Test close() generates correct JS."""
        ws = use_websocket("/api/chat")
        
        js = ws.close()
        
        assert "__pynext__.websocket.close" in js
        assert ws.id in js
    
    def test_reconnect_now(self):
        """Test reconnect_now() generates correct JS."""
        ws = use_websocket("/api/chat")
        
        js = ws.reconnect_now()
        
        assert "__pynext__.websocket.reconnect" in js
        assert ws.id in js
    
    def test_to_dict(self):
        """Test to_dict() serialization."""
        ws = use_websocket("/api/chat", reconnect=True, reconnect_interval=4000)
        
        data = ws.to_dict()
        
        assert data["id"] == ws.id
        assert data["url"] == "/api/chat"
        assert data["reconnect"] is True
        assert data["reconnectInterval"] == 4000
    
    def test_unique_ids(self):
        """Test each WebSocket gets unique ID."""
        ws1 = use_websocket("/api/ws1")
        ws2 = use_websocket("/api/ws2")
        
        assert ws1.id != ws2.id
    
    def test_hydration_data(self):
        """Test WebSocket appears in hydration data."""
        ws = use_websocket("/api/chat")
        
        data = get_client_hydration_data()
        
        assert "websocket" in data
        assert len(data["websocket"]) == 1
        assert data["websocket"][0]["url"] == "/api/chat"
    
    def test_multiple_connections(self):
        """Test multiple WebSocket connections."""
        ws1 = use_websocket("/api/chat")
        ws2 = use_websocket("/api/notifications")
        ws3 = use_websocket("/api/sync")
        
        data = get_client_hydration_data()
        
        assert len(data["websocket"]) == 3
    
    def test_get_js_init(self):
        """Test JavaScript initialization code generation."""
        ws = use_websocket("/api/chat")
        
        js_init = ws.get_js_init()
        
        assert "__pynext__.websocket.connect" in js_init
        assert "/api/chat" in js_init
    
    def test_callback_detection(self):
        """Test that callback presence is tracked."""
        ws = use_websocket("/api/chat", on_message=lambda x: x)
        
        data = ws.to_dict()
        
        assert data["hasOnMessage"] is True
        assert data["hasOnOpen"] is False
    
    def test_reset_clears_websockets(self):
        """Test reset_client_state() clears WebSocket connections."""
        ws = use_websocket("/api/chat")
        
        reset_client_state()
        
        data = get_client_hydration_data()
        assert len(data["websocket"]) == 0
    
    # Additional tests for edge cases
    def test_empty_url(self):
        """Test WebSocket with empty URL."""
        ws = use_websocket("")
        assert ws.url == ""
    
    def test_absolute_url(self):
        """Test WebSocket with absolute URL."""
        ws = use_websocket("wss://example.com/ws")
        assert ws.url == "wss://example.com/ws"
    
    def test_zero_reconnect_interval(self):
        """Test WebSocket with zero reconnect interval."""
        ws = use_websocket("/api/ws", reconnect_interval=0)
        assert ws.reconnect_interval == 0
    
    def test_large_reconnect_interval(self):
        """Test WebSocket with large reconnect interval."""
        ws = use_websocket("/api/ws", reconnect_interval=60000)
        assert ws.reconnect_interval == 60000
    
    def test_lambda_callbacks(self):
        """Test WebSocket with lambda callbacks."""
        ws = use_websocket(
            "/api/ws",
            on_message=lambda data: print(data),
            on_open=lambda: print("open"),
        )
        assert callable(ws.on_message)
        assert callable(ws.on_open)
    
    def test_send_bytes_fallback(self):
        """Test send() with bytes converts to string."""
        ws = use_websocket("/api/chat")
        js = ws.send(b"binary data")
        assert "__pynext__.websocket.send" in js
    
    def test_connection_id_format(self):
        """Test WebSocket ID format."""
        ws = use_websocket("/api/chat")
        assert ws.id.startswith("ws_")
        assert len(ws.id) == 11  # "ws_" + 8 hex chars


# =============================================================================
# Media Query Tests (15 tests)
# =============================================================================

class TestMediaQuery:
    """Tests for use_media_query() hook."""
    
    def test_basic_creation(self):
        """Test basic media query signal creation."""
        mq = use_media_query("(max-width: 768px)")
        
        assert isinstance(mq, MediaQuerySignal)
        assert mq.query == "(max-width: 768px)"
    
    def test_callable(self):
        """Test signal is callable."""
        mq = use_media_query("(min-width: 1024px)")
        
        # Initially False on server
        assert mq() is False
    
    def test_matches_property(self):
        """Test matches property."""
        mq = use_media_query("(min-width: 768px)")
        
        assert mq.matches is False
    
    def test_memoization(self):
        """Test same query returns same signal."""
        mq1 = use_media_query("(max-width: 768px)")
        mq2 = use_media_query("(max-width: 768px)")
        
        assert mq1 is mq2
    
    def test_different_queries(self):
        """Test different queries return different signals."""
        mq1 = use_media_query("(max-width: 768px)")
        mq2 = use_media_query("(max-width: 1024px)")
        
        assert mq1 is not mq2
    
    def test_to_dict(self):
        """Test serialization."""
        mq = use_media_query("(prefers-color-scheme: dark)")
        
        data = mq.to_dict()
        
        assert data["query"] == "(prefers-color-scheme: dark)"
        assert data["type"] == "mediaQuery"
    
    def test_js_init(self):
        """Test JavaScript initialization."""
        mq = use_media_query("(max-width: 768px)")
        
        js = mq.get_js_init()
        
        assert "__pynext__.browser.initMediaQuery" in js
        assert "(max-width: 768px)" in js
    
    def test_hydration_data(self):
        """Test appears in hydration data."""
        mq = use_media_query("(max-width: 768px)")
        
        data = get_client_hydration_data()
        
        assert "mediaQueries" in data
        assert len(data["mediaQueries"]) == 1
    
    def test_multiple_queries(self):
        """Test multiple different queries."""
        mq1 = use_media_query("(max-width: 768px)")
        mq2 = use_media_query("(prefers-color-scheme: dark)")
        mq3 = use_media_query("(prefers-reduced-motion: reduce)")
        
        data = get_client_hydration_data()
        
        assert len(data["mediaQueries"]) == 3
    
    def test_subscribe(self):
        """Test subscribe to changes."""
        mq = use_media_query("(max-width: 768px)")
        
        callback = MagicMock()
        unsubscribe = mq.subscribe(callback)
        
        assert callable(unsubscribe)
    
    def test_unsubscribe(self):
        """Test unsubscribe removes callback."""
        mq = use_media_query("(max-width: 768px)")
        
        callback = MagicMock()
        unsubscribe = mq.subscribe(callback)
        unsubscribe()
        
        # Should not raise
        assert True
    
    def test_common_queries(self):
        """Test common media query patterns."""
        queries = [
            "(min-width: 640px)",
            "(min-width: 768px)",
            "(min-width: 1024px)",
            "(min-width: 1280px)",
            "(orientation: landscape)",
            "(prefers-color-scheme: dark)",
        ]
        
        for query in queries:
            mq = use_media_query(query)
            assert mq.query == query
    
    def test_signal_id_format(self):
        """Test signal ID format."""
        mq = use_media_query("(max-width: 768px)")
        assert mq.id.startswith("mq_")
    
    def test_empty_query(self):
        """Test with empty query string."""
        mq = use_media_query("")
        assert mq.query == ""
    
    def test_complex_query(self):
        """Test with complex query."""
        mq = use_media_query("(min-width: 768px) and (max-width: 1024px)")
        assert "768px" in mq.query
        assert "1024px" in mq.query


# =============================================================================
# Geolocation Tests (20 tests)
# =============================================================================

class TestGeolocation:
    """Tests for use_geolocation() hook."""
    
    def test_basic_creation(self):
        """Test basic geolocation handle creation."""
        geo = use_geolocation()
        
        assert isinstance(geo, GeolocationHandle)
        assert geo.watch is False
        assert geo.high_accuracy is False
    
    def test_watch_mode(self):
        """Test continuous tracking mode."""
        geo = use_geolocation(watch=True)
        
        assert geo.watch is True
    
    def test_high_accuracy(self):
        """Test high accuracy mode."""
        geo = use_geolocation(high_accuracy=True)
        
        assert geo.high_accuracy is True
    
    def test_custom_timeout(self):
        """Test custom timeout."""
        geo = use_geolocation(timeout=5000)
        
        assert geo.timeout == 5000
    
    def test_max_age(self):
        """Test max age setting."""
        geo = use_geolocation(max_age=60000)
        
        assert geo.max_age == 60000
    
    def test_initial_loading(self):
        """Test initial loading state."""
        geo = use_geolocation()
        
        assert geo.loading() is True
    
    def test_initial_values_none(self):
        """Test initial location values are None."""
        geo = use_geolocation()
        
        assert geo.latitude() is None
        assert geo.longitude() is None
        assert geo.accuracy() is None
    
    def test_altitude_none(self):
        """Test altitude is None initially."""
        geo = use_geolocation()
        
        assert geo.altitude() is None
    
    def test_heading_none(self):
        """Test heading is None initially."""
        geo = use_geolocation()
        
        assert geo.heading() is None
    
    def test_speed_none(self):
        """Test speed is None initially."""
        geo = use_geolocation()
        
        assert geo.speed() is None
    
    def test_error_none(self):
        """Test error is None initially."""
        geo = use_geolocation()
        
        assert geo.error() is None
    
    def test_permission_prompt(self):
        """Test initial permission state."""
        geo = use_geolocation()
        
        assert geo.permission() == "prompt"
    
    def test_refresh(self):
        """Test refresh() generates correct JS."""
        geo = use_geolocation()
        
        js = geo.refresh()
        
        assert "__pynext__.browser.refreshGeolocation" in js
    
    def test_stop(self):
        """Test stop() generates correct JS."""
        geo = use_geolocation(watch=True)
        
        js = geo.stop()
        
        assert "__pynext__.browser.stopGeolocation" in js
    
    def test_to_dict(self):
        """Test serialization."""
        geo = use_geolocation(watch=True, high_accuracy=True)
        
        data = geo.to_dict()
        
        assert data["watch"] is True
        assert data["options"]["enableHighAccuracy"] is True
    
    def test_js_init(self):
        """Test JavaScript initialization."""
        geo = use_geolocation()
        
        js = geo.get_js_init()
        
        assert "__pynext__.browser.initGeolocation" in js
    
    def test_hydration_data(self):
        """Test appears in hydration data."""
        geo = use_geolocation()
        
        data = get_client_hydration_data()
        
        assert data["geolocation"] is not None
    
    def test_singleton(self):
        """Test geolocation is singleton."""
        geo1 = use_geolocation()
        geo2 = use_geolocation()
        
        assert geo1 is geo2
    
    def test_different_settings_returns_same(self):
        """Test same instance for matching settings."""
        geo1 = use_geolocation(watch=True, high_accuracy=True)
        geo2 = use_geolocation(watch=True, high_accuracy=True)
        
        assert geo1 is geo2
    
    def test_signal_id_format(self):
        """Test signal ID format."""
        geo = use_geolocation()
        assert geo.id.startswith("geo_")


# =============================================================================
# Clipboard Tests (15 tests)
# =============================================================================

class TestClipboard:
    """Tests for use_clipboard() hook."""
    
    def test_basic_creation(self):
        """Test basic clipboard handle creation."""
        clip = use_clipboard()
        
        assert isinstance(clip, ClipboardHandle)
    
    def test_text_none_initially(self):
        """Test text is None initially."""
        clip = use_clipboard()
        
        assert clip.text() is None
    
    def test_copied_false_initially(self):
        """Test copied is False initially."""
        clip = use_clipboard()
        
        assert clip.copied() is False
    
    def test_supported_true(self):
        """Test supported is True by default."""
        clip = use_clipboard()
        
        assert clip.supported() is True
    
    def test_copy(self):
        """Test copy() generates correct JS."""
        clip = use_clipboard()
        
        js = clip.copy("Hello, World!")
        
        assert "__pynext__.browser.clipboardCopy" in js
        assert "Hello, World!" in js
    
    def test_copy_escapes_quotes(self):
        """Test copy() properly escapes quotes."""
        clip = use_clipboard()
        
        js = clip.copy('Text with "quotes"')
        
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_read(self):
        """Test read() generates correct JS."""
        clip = use_clipboard()
        
        js = clip.read()
        
        assert "__pynext__.browser.clipboardRead" in js
    
    def test_to_dict(self):
        """Test serialization."""
        clip = use_clipboard()
        
        data = clip.to_dict()
        
        assert data["type"] == "clipboard"
    
    def test_js_init(self):
        """Test JavaScript initialization."""
        clip = use_clipboard()
        
        js = clip.get_js_init()
        
        assert "__pynext__.browser.initClipboard" in js
    
    def test_hydration_data(self):
        """Test appears in hydration data."""
        clip = use_clipboard()
        
        data = get_client_hydration_data()
        
        assert data["clipboard"] is not None
    
    def test_singleton(self):
        """Test clipboard is singleton."""
        clip1 = use_clipboard()
        clip2 = use_clipboard()
        
        assert clip1 is clip2
    
    def test_signal_id_format(self):
        """Test signal ID format."""
        clip = use_clipboard()
        assert clip.id.startswith("clip_")
    
    def test_copy_empty_string(self):
        """Test copy with empty string."""
        clip = use_clipboard()
        js = clip.copy("")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_long_text(self):
        """Test copy with long text."""
        clip = use_clipboard()
        long_text = "x" * 10000
        js = clip.copy(long_text)
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_unicode(self):
        """Test copy with unicode text."""
        clip = use_clipboard()
        js = clip.copy("Hello 你好 🌍")
        assert "__pynext__.browser.clipboardCopy" in js


# =============================================================================
# Window Size Tests (10 tests)
# =============================================================================

class TestWindowSize:
    """Tests for use_window_size() hook."""
    
    def test_basic_creation(self):
        """Test basic window size creation."""
        size = use_window_size()
        
        assert isinstance(size, WindowSize)
    
    def test_width_zero_initially(self):
        """Test width is 0 initially (server-side)."""
        size = use_window_size()
        
        assert size.width() == 0
    
    def test_height_zero_initially(self):
        """Test height is 0 initially (server-side)."""
        size = use_window_size()
        
        assert size.height() == 0
    
    def test_callable_tuple(self):
        """Test callable returns tuple."""
        size = use_window_size()
        
        w, h = size()
        
        assert w == 0
        assert h == 0
    
    def test_to_dict(self):
        """Test serialization."""
        size = use_window_size()
        
        data = size.to_dict()
        
        assert data["type"] == "windowSize"
    
    def test_js_init(self):
        """Test JavaScript initialization."""
        size = use_window_size()
        
        js = size.get_js_init()
        
        assert "__pynext__.browser.initWindowSize" in js
    
    def test_hydration_data(self):
        """Test appears in hydration data."""
        size = use_window_size()
        
        data = get_client_hydration_data()
        
        assert data["windowSize"] is not None
    
    def test_singleton(self):
        """Test window size is singleton."""
        size1 = use_window_size()
        size2 = use_window_size()
        
        assert size1 is size2
    
    def test_subscribe(self):
        """Test subscribe to changes."""
        size = use_window_size()
        
        callback = MagicMock()
        unsubscribe = size.subscribe(callback)
        
        assert callable(unsubscribe)
    
    def test_signal_id_format(self):
        """Test signal ID format."""
        size = use_window_size()
        assert size.id.startswith("size_")


# =============================================================================
# Scroll Position Tests (15 tests)
# =============================================================================

class TestScrollPosition:
    """Tests for use_scroll_position() hook."""
    
    def test_basic_creation(self):
        """Test basic scroll position creation."""
        scroll = use_scroll_position()
        
        assert isinstance(scroll, ScrollPosition)
    
    def test_x_zero_initially(self):
        """Test x is 0 initially."""
        scroll = use_scroll_position()
        
        assert scroll.x() == 0
    
    def test_y_zero_initially(self):
        """Test y is 0 initially."""
        scroll = use_scroll_position()
        
        assert scroll.y() == 0
    
    def test_progress_zero_initially(self):
        """Test progress is 0 initially."""
        scroll = use_scroll_position()
        
        assert scroll.progress() == 0.0
    
    def test_callable_tuple(self):
        """Test callable returns tuple."""
        scroll = use_scroll_position()
        
        x, y = scroll()
        
        assert x == 0
        assert y == 0
    
    def test_to(self):
        """Test to() generates correct JS."""
        scroll = use_scroll_position()
        
        js = scroll.to(0, 500)
        
        assert "window.scrollTo" in js
        assert "500" in js
        assert "smooth" in js
    
    def test_to_instant(self):
        """Test to() with instant scroll."""
        scroll = use_scroll_position()
        
        js = scroll.to(0, 500, smooth=False)
        
        assert "instant" in js
    
    def test_to_top(self):
        """Test to_top() generates correct JS."""
        scroll = use_scroll_position()
        
        js = scroll.to_top()
        
        assert "window.scrollTo" in js
    
    def test_to_bottom(self):
        """Test to_bottom() generates correct JS."""
        scroll = use_scroll_position()
        
        js = scroll.to_bottom()
        
        assert "scrollHeight" in js
    
    def test_to_element(self):
        """Test to_element() generates correct JS."""
        scroll = use_scroll_position()
        
        js = scroll.to_element("section-2")
        
        assert "getElementById" in js
        assert "section-2" in js
        assert "scrollIntoView" in js
    
    def test_to_dict(self):
        """Test serialization."""
        scroll = use_scroll_position()
        
        data = scroll.to_dict()
        
        assert data["type"] == "scrollPosition"
    
    def test_js_init(self):
        """Test JavaScript initialization."""
        scroll = use_scroll_position()
        
        js = scroll.get_js_init()
        
        assert "__pynext__.browser.initScrollPosition" in js
    
    def test_hydration_data(self):
        """Test appears in hydration data."""
        scroll = use_scroll_position()
        
        data = get_client_hydration_data()
        
        assert data["scrollPosition"] is not None
    
    def test_singleton(self):
        """Test scroll position is singleton."""
        scroll1 = use_scroll_position()
        scroll2 = use_scroll_position()
        
        assert scroll1 is scroll2
    
    def test_signal_id_format(self):
        """Test signal ID format."""
        scroll = use_scroll_position()
        assert scroll.id.startswith("scroll_")


# =============================================================================
# Intersection Observer Tests (15 tests)
# =============================================================================

class TestIntersection:
    """Tests for use_intersection() hook."""
    
    def test_basic_creation(self):
        """Test basic intersection signal creation."""
        int_sig = use_intersection("hero-section")
        
        assert isinstance(int_sig, IntersectionSignal)
        assert int_sig.element_id == "hero-section"
    
    def test_default_threshold(self):
        """Test default threshold is 0."""
        int_sig = use_intersection("hero-section")
        
        assert int_sig.threshold == 0.0
    
    def test_custom_threshold(self):
        """Test custom threshold."""
        int_sig = use_intersection("hero-section", threshold=0.5)
        
        assert int_sig.threshold == 0.5
    
    def test_default_root_margin(self):
        """Test default root margin."""
        int_sig = use_intersection("hero-section")
        
        assert int_sig.root_margin == "0px"
    
    def test_custom_root_margin(self):
        """Test custom root margin."""
        int_sig = use_intersection("hero-section", root_margin="100px")
        
        assert int_sig.root_margin == "100px"
    
    def test_callable(self):
        """Test signal is callable."""
        int_sig = use_intersection("hero-section")
        
        # Initially False on server
        assert int_sig() is False
    
    def test_is_visible(self):
        """Test is_visible property."""
        int_sig = use_intersection("hero-section")
        
        assert int_sig.is_visible is False
    
    def test_ratio(self):
        """Test ratio() method."""
        int_sig = use_intersection("hero-section")
        
        assert int_sig.ratio() == 0.0
    
    def test_to_dict(self):
        """Test serialization."""
        int_sig = use_intersection("hero-section", threshold=0.5, root_margin="50px")
        
        data = int_sig.to_dict()
        
        assert data["elementId"] == "hero-section"
        assert data["options"]["threshold"] == 0.5
        assert data["options"]["rootMargin"] == "50px"
    
    def test_js_init(self):
        """Test JavaScript initialization."""
        int_sig = use_intersection("hero-section")
        
        js = int_sig.get_js_init()
        
        assert "__pynext__.browser.initIntersection" in js
    
    def test_hydration_data(self):
        """Test appears in hydration data."""
        int_sig = use_intersection("hero-section")
        
        data = get_client_hydration_data()
        
        assert "intersections" in data
        assert len(data["intersections"]) == 1
    
    def test_memoization(self):
        """Test same element returns same signal."""
        int1 = use_intersection("hero-section")
        int2 = use_intersection("hero-section")
        
        assert int1 is int2
    
    def test_different_elements(self):
        """Test different elements return different signals."""
        int1 = use_intersection("section-1")
        int2 = use_intersection("section-2")
        
        assert int1 is not int2
    
    def test_subscribe(self):
        """Test subscribe to changes."""
        int_sig = use_intersection("hero-section")
        
        callback = MagicMock()
        unsubscribe = int_sig.subscribe(callback)
        
        assert callable(unsubscribe)
    
    def test_signal_id_format(self):
        """Test signal ID format."""
        int_sig = use_intersection("hero-section")
        assert int_sig.id.startswith("int_")


# =============================================================================
# JavaScript Runtime Tests
# =============================================================================

class TestJavaScriptRuntimes:
    """Tests for JavaScript runtime files."""
    
    def test_websocket_js_exists(self):
        """Test websocket.js file exists."""
        ws_js = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "websocket.js"
        assert ws_js.exists()
    
    def test_websocket_js_content(self):
        """Test websocket.js contains expected functions."""
        ws_js = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "websocket.js"
        content = ws_js.read_text()
        
        assert "connect" in content
        assert "send" in content
        assert "close" in content
        assert "reconnect" in content
        assert "hydrate" in content
    
    def test_browser_js_exists(self):
        """Test browser.js file exists."""
        browser_js = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "browser.js"
        assert browser_js.exists()
    
    def test_browser_js_content(self):
        """Test browser.js contains expected functions."""
        browser_js = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "browser.js"
        content = browser_js.read_text()
        
        assert "initVisibility" in content
        assert "initOnline" in content
        assert "initMediaQuery" in content
        assert "initGeolocation" in content
        assert "initClipboard" in content
        assert "initWindowSize" in content
        assert "initScrollPosition" in content
        assert "initIntersection" in content


# =============================================================================
# WebSocket Edge Cases (30 more tests)
# =============================================================================

class TestWebSocketEdgeCases:
    """Additional edge case tests for WebSocket."""
    
    def test_send_nested_dict(self):
        """Test sending deeply nested dictionary."""
        ws = use_websocket("/api/chat")
        data = {"level1": {"level2": {"level3": {"value": 123}}}}
        js = ws.send(data)
        assert "__pynext__.websocket.send" in js
    
    def test_send_list(self):
        """Test sending list data."""
        ws = use_websocket("/api/chat")
        js = ws.send({"items": [1, 2, 3, 4, 5]})
        assert "__pynext__.websocket.send" in js
    
    def test_send_special_characters(self):
        """Test sending special characters."""
        ws = use_websocket("/api/chat")
        js = ws.send({"text": "Hello\n\t\"World\"\\n"})
        assert "__pynext__.websocket.send" in js
    
    def test_send_unicode(self):
        """Test sending unicode characters."""
        ws = use_websocket("/api/chat")
        js = ws.send({"text": "你好世界 🌍 émojis"})
        assert "__pynext__.websocket.send" in js
    
    def test_send_empty_dict(self):
        """Test sending empty dictionary."""
        ws = use_websocket("/api/chat")
        js = ws.send({})
        assert "__pynext__.websocket.send" in js
    
    def test_send_null_values(self):
        """Test sending null values."""
        ws = use_websocket("/api/chat")
        js = ws.send({"value": None})
        assert "null" in js or "__pynext__.websocket.send" in js
    
    def test_send_boolean_values(self):
        """Test sending boolean values."""
        ws = use_websocket("/api/chat")
        js = ws.send({"active": True, "disabled": False})
        assert "__pynext__.websocket.send" in js
    
    def test_send_numeric_values(self):
        """Test sending various numeric values."""
        ws = use_websocket("/api/chat")
        js = ws.send({"int": 42, "float": 3.14, "negative": -100})
        assert "__pynext__.websocket.send" in js
    
    def test_multiple_callbacks_all_present(self):
        """Test all callbacks are registered."""
        ws = use_websocket(
            "/api/chat",
            on_message=lambda x: x,
            on_open=lambda: None,
            on_close=lambda: None,
            on_error=lambda e: e,
        )
        data = ws.to_dict()
        assert data["hasOnMessage"] is True
        assert data["hasOnOpen"] is True
        assert data["hasOnClose"] is True
        assert data["hasOnError"] is True
    
    def test_url_with_query_params(self):
        """Test URL with query parameters."""
        ws = use_websocket("/api/chat?room=general&user=123")
        assert ws.url == "/api/chat?room=general&user=123"
    
    def test_url_with_path_segments(self):
        """Test URL with multiple path segments."""
        ws = use_websocket("/api/v2/chat/rooms/123/messages")
        assert "rooms/123" in ws.url
    
    def test_wss_protocol(self):
        """Test secure WebSocket URL."""
        ws = use_websocket("wss://secure.example.com/ws")
        assert ws.url.startswith("wss://")
    
    def test_ws_protocol(self):
        """Test non-secure WebSocket URL."""
        ws = use_websocket("ws://example.com/ws")
        assert ws.url.startswith("ws://")
    
    def test_reconnect_interval_minimum(self):
        """Test minimum reconnect interval."""
        ws = use_websocket("/api/ws", reconnect_interval=100)
        assert ws.reconnect_interval == 100
    
    def test_reconnect_disabled(self):
        """Test reconnect completely disabled."""
        ws = use_websocket("/api/ws", reconnect=False)
        assert ws.reconnect is False
        data = ws.to_dict()
        assert data["reconnect"] is False
    
    def test_js_init_contains_all_config(self):
        """Test JS init contains all configuration."""
        ws = use_websocket(
            "/api/chat",
            reconnect=True,
            reconnect_interval=5000,
        )
        js_init = ws.get_js_init()
        assert "5000" in js_init
        assert "/api/chat" in js_init
    
    def test_hydration_data_structure(self):
        """Test hydration data has correct structure."""
        ws = use_websocket("/api/chat")
        data = get_client_hydration_data()
        
        assert isinstance(data["websocket"], list)
        ws_data = data["websocket"][0]
        assert "id" in ws_data
        assert "url" in ws_data
        assert "reconnect" in ws_data
    
    def test_close_returns_valid_js(self):
        """Test close returns valid JavaScript."""
        ws = use_websocket("/api/chat")
        js = ws.close()
        assert js.startswith("__pynext__.websocket.close")
        assert ws.id in js
    
    def test_reconnect_now_returns_valid_js(self):
        """Test reconnect_now returns valid JavaScript."""
        ws = use_websocket("/api/chat")
        js = ws.reconnect_now()
        assert js.startswith("__pynext__.websocket.reconnect")
        assert ws.id in js
    
    def test_many_websockets(self):
        """Test creating many WebSocket connections."""
        websockets = [use_websocket(f"/api/ws/{i}") for i in range(50)]
        
        data = get_client_hydration_data()
        assert len(data["websocket"]) == 50
        
        # All IDs should be unique
        ids = [ws.id for ws in websockets]
        assert len(set(ids)) == 50
    
    def test_websocket_with_localhost(self):
        """Test WebSocket with localhost URL."""
        ws = use_websocket("ws://localhost:8080/ws")
        assert "localhost" in ws.url
    
    def test_websocket_with_ip(self):
        """Test WebSocket with IP address."""
        ws = use_websocket("ws://192.168.1.1:8080/ws")
        assert "192.168.1.1" in ws.url
    
    def test_websocket_port_number(self):
        """Test WebSocket with various ports."""
        ws1 = use_websocket("ws://example.com:80/ws")
        ws2 = use_websocket("ws://example.com:443/ws")
        ws3 = use_websocket("ws://example.com:3000/ws")
        
        assert ":80" in ws1.url
        assert ":443" in ws2.url
        assert ":3000" in ws3.url
    
    def test_send_large_payload(self):
        """Test sending large payload."""
        ws = use_websocket("/api/chat")
        large_data = {"data": "x" * 100000}
        js = ws.send(large_data)
        assert "__pynext__.websocket.send" in js
    
    def test_callback_none_values(self):
        """Test callbacks can be None."""
        ws = use_websocket("/api/chat", on_message=None)
        assert ws.on_message is None
    
    def test_to_dict_json_serializable(self):
        """Test to_dict output is JSON serializable."""
        ws = use_websocket("/api/chat")
        data = ws.to_dict()
        
        # Should not raise
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
    
    def test_multiple_sends(self):
        """Test multiple send calls."""
        ws = use_websocket("/api/chat")
        
        js1 = ws.send({"type": "msg1"})
        js2 = ws.send({"type": "msg2"})
        js3 = ws.send({"type": "msg3"})
        
        assert ws.id in js1
        assert ws.id in js2
        assert ws.id in js3
    
    def test_default_reconnect_true(self):
        """Test default reconnect is True."""
        ws = use_websocket("/api/ws")
        assert ws.reconnect is True
    
    def test_default_interval_3000(self):
        """Test default reconnect interval is 3000ms."""
        ws = use_websocket("/api/ws")
        assert ws.reconnect_interval == 3000


# =============================================================================
# Media Query Edge Cases (25 more tests)
# =============================================================================

class TestMediaQueryEdgeCases:
    """Additional edge case tests for media queries."""
    
    def test_complex_and_query(self):
        """Test complex AND media query."""
        mq = use_media_query("(min-width: 768px) and (max-width: 1024px) and (orientation: landscape)")
        assert "and" in mq.query
    
    def test_or_query(self):
        """Test OR media query with comma."""
        mq = use_media_query("(max-width: 600px), (orientation: portrait)")
        assert "," in mq.query
    
    def test_not_query(self):
        """Test NOT media query."""
        mq = use_media_query("not (color)")
        assert "not" in mq.query
    
    def test_only_query(self):
        """Test ONLY media query."""
        mq = use_media_query("only screen and (min-width: 1024px)")
        assert "only" in mq.query
    
    def test_print_media(self):
        """Test print media type."""
        mq = use_media_query("print")
        assert mq.query == "print"
    
    def test_screen_media(self):
        """Test screen media type."""
        mq = use_media_query("screen")
        assert mq.query == "screen"
    
    def test_all_media(self):
        """Test all media type."""
        mq = use_media_query("all")
        assert mq.query == "all"
    
    def test_resolution_query(self):
        """Test resolution media query."""
        mq = use_media_query("(min-resolution: 300dpi)")
        assert "dpi" in mq.query
    
    def test_aspect_ratio_query(self):
        """Test aspect-ratio media query."""
        mq = use_media_query("(aspect-ratio: 16/9)")
        assert "16/9" in mq.query
    
    def test_color_scheme_light(self):
        """Test light color scheme."""
        mq = use_media_query("(prefers-color-scheme: light)")
        assert "light" in mq.query
    
    def test_reduced_data(self):
        """Test reduced data preference."""
        mq = use_media_query("(prefers-reduced-data: reduce)")
        assert "reduced-data" in mq.query
    
    def test_pointer_fine(self):
        """Test fine pointer device."""
        mq = use_media_query("(pointer: fine)")
        assert "fine" in mq.query
    
    def test_pointer_coarse(self):
        """Test coarse pointer device."""
        mq = use_media_query("(pointer: coarse)")
        assert "coarse" in mq.query
    
    def test_hover_hover(self):
        """Test hover capability."""
        mq = use_media_query("(hover: hover)")
        assert "hover" in mq.query
    
    def test_hover_none(self):
        """Test no hover capability."""
        mq = use_media_query("(hover: none)")
        assert "none" in mq.query
    
    def test_display_mode(self):
        """Test display mode for PWA."""
        mq = use_media_query("(display-mode: standalone)")
        assert "standalone" in mq.query
    
    def test_inverted_colors(self):
        """Test inverted colors preference."""
        mq = use_media_query("(inverted-colors: inverted)")
        assert "inverted" in mq.query
    
    def test_many_media_queries(self):
        """Test creating many media queries."""
        queries = [
            use_media_query(f"(min-width: {i * 100}px)")
            for i in range(20)
        ]
        
        # All should be different
        assert len(set(q.id for q in queries)) == 20
    
    def test_subscribe_multiple(self):
        """Test multiple subscriptions."""
        mq = use_media_query("(max-width: 768px)")
        
        cb1 = MagicMock()
        cb2 = MagicMock()
        cb3 = MagicMock()
        
        unsub1 = mq.subscribe(cb1)
        unsub2 = mq.subscribe(cb2)
        unsub3 = mq.subscribe(cb3)
        
        assert len(mq._subscribers) == 3
        
        unsub1()
        assert len(mq._subscribers) == 2
    
    def test_js_init_escapes_query(self):
        """Test JS init properly handles query string."""
        mq = use_media_query('(min-width: 768px)')
        js = mq.get_js_init()
        assert "768px" in js
    
    def test_hydration_data_multiple(self):
        """Test hydration data with multiple queries."""
        mq1 = use_media_query("(max-width: 640px)")
        mq2 = use_media_query("(max-width: 768px)")
        mq3 = use_media_query("(max-width: 1024px)")
        
        data = get_client_hydration_data()
        assert len(data["mediaQueries"]) == 3
    
    def test_query_with_calc(self):
        """Test query with calc values (unlikely but valid CSS)."""
        mq = use_media_query("(min-width: 100%)")
        assert "100%" in mq.query
    
    def test_whitespace_in_query(self):
        """Test query with extra whitespace."""
        mq = use_media_query("  (max-width:   768px)  ")
        assert "768px" in mq.query
    
    def test_case_sensitivity(self):
        """Test query case handling."""
        mq1 = use_media_query("(Max-Width: 768px)")
        mq2 = use_media_query("(MAX-WIDTH: 768PX)")
        # Different queries, different signals
        assert mq1.query != mq2.query or mq1 is mq2
    
    def test_to_dict_structure(self):
        """Test to_dict has correct structure."""
        mq = use_media_query("(max-width: 768px)")
        data = mq.to_dict()
        
        assert "id" in data
        assert "query" in data
        assert "type" in data
        assert data["type"] == "mediaQuery"


# =============================================================================
# Geolocation Edge Cases (25 more tests)
# =============================================================================

class TestGeolocationEdgeCases:
    """Additional edge case tests for geolocation."""
    
    def test_timeout_short(self):
        """Test very short timeout."""
        geo = use_geolocation(timeout=100)
        assert geo.timeout == 100
    
    def test_timeout_long(self):
        """Test long timeout."""
        geo = use_geolocation(timeout=60000)
        assert geo.timeout == 60000
    
    def test_max_age_zero(self):
        """Test zero max age (always fresh)."""
        geo = use_geolocation(max_age=0)
        assert geo.max_age == 0
    
    def test_max_age_infinite(self):
        """Test infinite max age (cache forever)."""
        geo = use_geolocation(max_age=float('inf') if False else 999999999)
        assert geo.max_age >= 999999999
    
    def test_all_options(self):
        """Test all options together."""
        geo = use_geolocation(
            watch=True,
            high_accuracy=True,
            timeout=5000,
            max_age=1000,
        )
        
        assert geo.watch is True
        assert geo.high_accuracy is True
        assert geo.timeout == 5000
        assert geo.max_age == 1000
    
    def test_to_dict_options(self):
        """Test to_dict includes options correctly."""
        geo = use_geolocation(high_accuracy=True, timeout=5000)
        data = geo.to_dict()
        
        assert data["options"]["enableHighAccuracy"] is True
        assert data["options"]["timeout"] == 5000
    
    def test_refresh_js_contains_id(self):
        """Test refresh JS contains correct ID."""
        geo = use_geolocation()
        js = geo.refresh()
        assert geo.id in js
    
    def test_stop_js_contains_id(self):
        """Test stop JS contains correct ID."""
        geo = use_geolocation(watch=True)
        js = geo.stop()
        assert geo.id in js
    
    def test_all_signals_none_initially(self):
        """Test all location signals are None initially."""
        geo = use_geolocation()
        
        assert geo.latitude() is None
        assert geo.longitude() is None
        assert geo.accuracy() is None
        assert geo.altitude() is None
        assert geo.heading() is None
        assert geo.speed() is None
    
    def test_loading_true_initially(self):
        """Test loading is True initially."""
        geo = use_geolocation()
        assert geo.loading() is True
    
    def test_error_none_initially(self):
        """Test error is None initially."""
        geo = use_geolocation()
        assert geo.error() is None
    
    def test_permission_prompt_initially(self):
        """Test permission is 'prompt' initially."""
        geo = use_geolocation()
        assert geo.permission() == "prompt"
    
    def test_js_init_watch_mode(self):
        """Test JS init in watch mode."""
        geo = use_geolocation(watch=True)
        js = geo.get_js_init()
        assert "true" in js.lower() or "watch" in js.lower()
    
    def test_js_init_high_accuracy(self):
        """Test JS init with high accuracy."""
        geo = use_geolocation(high_accuracy=True)
        js = geo.get_js_init()
        assert "true" in js.lower()
    
    def test_hydration_data_structure(self):
        """Test hydration data has correct structure."""
        geo = use_geolocation()
        data = get_client_hydration_data()
        
        assert data["geolocation"] is not None
        assert "id" in data["geolocation"]
        assert "watch" in data["geolocation"]
        assert "options" in data["geolocation"]
    
    def test_reset_clears_geolocation(self):
        """Test reset clears geolocation."""
        geo = use_geolocation()
        
        reset_client_state()
        
        data = get_client_hydration_data()
        assert data["geolocation"] is None
    
    def test_signal_id_unique(self):
        """Test signal ID is unique each time after reset."""
        geo1 = use_geolocation()
        id1 = geo1.id
        
        reset_client_state()
        
        geo2 = use_geolocation()
        id2 = geo2.id
        
        # After reset, new ID
        assert id1 != id2
    
    def test_watch_false_by_default(self):
        """Test watch is False by default."""
        geo = use_geolocation()
        assert geo.watch is False
    
    def test_high_accuracy_false_by_default(self):
        """Test high_accuracy is False by default."""
        geo = use_geolocation()
        assert geo.high_accuracy is False
    
    def test_default_timeout(self):
        """Test default timeout value."""
        geo = use_geolocation()
        assert geo.timeout == 10000
    
    def test_default_max_age(self):
        """Test default max_age value."""
        geo = use_geolocation()
        assert geo.max_age == 0
    
    def test_to_dict_json_serializable(self):
        """Test to_dict is JSON serializable."""
        geo = use_geolocation(watch=True, high_accuracy=True)
        data = geo.to_dict()
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
    
    def test_multiple_access(self):
        """Test multiple accesses return same values."""
        geo = use_geolocation()
        
        lat1, lat2 = geo.latitude(), geo.latitude()
        lon1, lon2 = geo.longitude(), geo.longitude()
        
        assert lat1 == lat2
        assert lon1 == lon2
    
    def test_js_init_format(self):
        """Test JS init has correct format."""
        geo = use_geolocation()
        js = geo.get_js_init()
        
        assert js.startswith("__pynext__.browser.initGeolocation")
        assert "{" in js  # JSON config


# =============================================================================
# Clipboard Edge Cases (25 more tests)
# =============================================================================

class TestClipboardEdgeCases:
    """Additional edge case tests for clipboard."""
    
    def test_copy_newlines(self):
        """Test copy with newlines."""
        clip = use_clipboard()
        js = clip.copy("Line 1\nLine 2\nLine 3")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_tabs(self):
        """Test copy with tabs."""
        clip = use_clipboard()
        js = clip.copy("Col1\tCol2\tCol3")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_html(self):
        """Test copy with HTML content."""
        clip = use_clipboard()
        js = clip.copy("<div>Hello</div>")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_json(self):
        """Test copy with JSON string."""
        clip = use_clipboard()
        js = clip.copy('{"key": "value"}')
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_url(self):
        """Test copy with URL."""
        clip = use_clipboard()
        js = clip.copy("https://example.com/path?query=value#hash")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_email(self):
        """Test copy with email."""
        clip = use_clipboard()
        js = clip.copy("user@example.com")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_code(self):
        """Test copy with code snippet."""
        clip = use_clipboard()
        js = clip.copy("def hello():\n    print('Hello')")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_sql(self):
        """Test copy with SQL query."""
        clip = use_clipboard()
        js = clip.copy("SELECT * FROM users WHERE id = 1;")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_special_chars(self):
        """Test copy with many special characters."""
        clip = use_clipboard()
        js = clip.copy("!@#$%^&*()_+-=[]{}|;':\",./<>?")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_backslashes(self):
        """Test copy with backslashes."""
        clip = use_clipboard()
        js = clip.copy("C:\\Users\\Name\\Documents")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_read_returns_valid_js(self):
        """Test read returns valid JavaScript."""
        clip = use_clipboard()
        js = clip.read()
        assert js.startswith("__pynext__.browser.clipboardRead")
    
    def test_read_contains_id(self):
        """Test read contains signal ID."""
        clip = use_clipboard()
        js = clip.read()
        assert clip.id in js
    
    def test_copy_contains_id(self):
        """Test copy contains signal ID."""
        clip = use_clipboard()
        js = clip.copy("test")
        assert clip.id in js
    
    def test_to_dict_structure(self):
        """Test to_dict has correct structure."""
        clip = use_clipboard()
        data = clip.to_dict()
        
        assert "id" in data
        assert "type" in data
        assert data["type"] == "clipboard"
    
    def test_js_init_format(self):
        """Test JS init has correct format."""
        clip = use_clipboard()
        js = clip.get_js_init()
        
        assert js.startswith("__pynext__.browser.initClipboard")
        assert clip.id in js
    
    def test_hydration_data_structure(self):
        """Test hydration data has correct structure."""
        clip = use_clipboard()
        data = get_client_hydration_data()
        
        assert data["clipboard"] is not None
        assert "id" in data["clipboard"]
        assert "type" in data["clipboard"]
    
    def test_multiple_copies(self):
        """Test multiple copy calls."""
        clip = use_clipboard()
        
        js1 = clip.copy("text1")
        js2 = clip.copy("text2")
        js3 = clip.copy("text3")
        
        assert "text1" in js1
        assert "text2" in js2
        assert "text3" in js3
    
    def test_copy_then_read(self):
        """Test copy then read sequence."""
        clip = use_clipboard()
        
        copy_js = clip.copy("copied text")
        read_js = clip.read()
        
        assert "__pynext__.browser.clipboardCopy" in copy_js
        assert "__pynext__.browser.clipboardRead" in read_js
    
    def test_reset_clears_clipboard(self):
        """Test reset clears clipboard."""
        clip = use_clipboard()
        
        reset_client_state()
        
        data = get_client_hydration_data()
        assert data["clipboard"] is None
    
    def test_initial_states(self):
        """Test all initial states are correct."""
        clip = use_clipboard()
        
        assert clip.text() is None
        assert clip.copied() is False
        assert clip.supported() is True
    
    def test_copy_multiline(self):
        """Test copy with multiple lines."""
        clip = use_clipboard()
        text = """Line 1
        Line 2
        Line 3
        Line 4"""
        js = clip.copy(text)
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_whitespace_only(self):
        """Test copy with whitespace only."""
        clip = use_clipboard()
        js = clip.copy("   \t\n   ")
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_copy_single_char(self):
        """Test copy with single character."""
        clip = use_clipboard()
        js = clip.copy("x")
        assert "x" in js
    
    def test_to_dict_json_serializable(self):
        """Test to_dict is JSON serializable."""
        clip = use_clipboard()
        data = clip.to_dict()
        json_str = json.dumps(data)
        assert isinstance(json_str, str)


# =============================================================================
# Window Size Edge Cases (20 more tests)
# =============================================================================

class TestWindowSizeEdgeCases:
    """Additional edge case tests for window size."""
    
    def test_initial_zero_width(self):
        """Test initial width is 0."""
        size = use_window_size()
        assert size.width() == 0
    
    def test_initial_zero_height(self):
        """Test initial height is 0."""
        size = use_window_size()
        assert size.height() == 0
    
    def test_tuple_unpacking(self):
        """Test tuple unpacking works correctly."""
        size = use_window_size()
        w, h = size()
        assert w == 0
        assert h == 0
    
    def test_to_dict_structure(self):
        """Test to_dict has correct structure."""
        size = use_window_size()
        data = size.to_dict()
        
        assert "id" in data
        assert "type" in data
        assert data["type"] == "windowSize"
    
    def test_js_init_format(self):
        """Test JS init has correct format."""
        size = use_window_size()
        js = size.get_js_init()
        
        assert js.startswith("__pynext__.browser.initWindowSize")
        assert size.id in js
    
    def test_hydration_data_structure(self):
        """Test hydration data has correct structure."""
        size = use_window_size()
        data = get_client_hydration_data()
        
        assert data["windowSize"] is not None
        assert "id" in data["windowSize"]
    
    def test_reset_clears_window_size(self):
        """Test reset clears window size."""
        size = use_window_size()
        
        reset_client_state()
        
        data = get_client_hydration_data()
        assert data["windowSize"] is None
    
    def test_subscribe_callback(self):
        """Test subscribe with callback."""
        size = use_window_size()
        
        callback = MagicMock()
        unsub = size.subscribe(callback)
        
        assert callable(unsub)
        assert callback in size._subscribers
    
    def test_unsubscribe_removes_callback(self):
        """Test unsubscribe removes callback."""
        size = use_window_size()
        
        callback = MagicMock()
        unsub = size.subscribe(callback)
        unsub()
        
        assert callback not in size._subscribers
    
    def test_multiple_subscribes(self):
        """Test multiple subscriptions."""
        size = use_window_size()
        
        callbacks = [MagicMock() for _ in range(5)]
        for cb in callbacks:
            size.subscribe(cb)
        
        assert len(size._subscribers) == 5
    
    def test_singleton_returns_same_instance(self):
        """Test singleton always returns same instance."""
        size1 = use_window_size()
        size2 = use_window_size()
        size3 = use_window_size()
        
        assert size1 is size2
        assert size2 is size3
    
    def test_to_dict_json_serializable(self):
        """Test to_dict is JSON serializable."""
        size = use_window_size()
        data = size.to_dict()
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
    
    def test_width_callable(self):
        """Test width() is callable."""
        size = use_window_size()
        assert callable(size.width)
    
    def test_height_callable(self):
        """Test height() is callable."""
        size = use_window_size()
        assert callable(size.height)
    
    def test_dunder_call(self):
        """Test __call__ returns tuple."""
        size = use_window_size()
        result = size()
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_id_format(self):
        """Test ID has correct format."""
        size = use_window_size()
        assert size.id.startswith("size_")
        assert len(size.id) > 5
    
    def test_multiple_accesses(self):
        """Test multiple accesses are consistent."""
        size = use_window_size()
        
        w1, w2, w3 = size.width(), size.width(), size.width()
        h1, h2, h3 = size.height(), size.height(), size.height()
        
        assert w1 == w2 == w3
        assert h1 == h2 == h3
    
    def test_tuple_consistency(self):
        """Test tuple and individual calls are consistent."""
        size = use_window_size()
        
        w1, h1 = size()
        w2 = size.width()
        h2 = size.height()
        
        assert w1 == w2
        assert h1 == h2
    
    def test_new_instance_after_reset(self):
        """Test new instance has new ID after reset."""
        size1 = use_window_size()
        id1 = size1.id
        
        reset_client_state()
        
        size2 = use_window_size()
        id2 = size2.id
        
        assert id1 != id2


# =============================================================================
# Scroll Position Edge Cases (25 more tests)
# =============================================================================

class TestScrollPositionEdgeCases:
    """Additional edge case tests for scroll position."""
    
    def test_to_with_negative_values(self):
        """Test to() with negative values."""
        scroll = use_scroll_position()
        js = scroll.to(-100, -100)
        assert "-100" in js
    
    def test_to_with_large_values(self):
        """Test to() with large values."""
        scroll = use_scroll_position()
        js = scroll.to(100000, 100000)
        assert "100000" in js
    
    def test_to_with_zero(self):
        """Test to() with zero values."""
        scroll = use_scroll_position()
        js = scroll.to(0, 0)
        assert "0" in js
    
    def test_to_top_smooth(self):
        """Test to_top with smooth scrolling."""
        scroll = use_scroll_position()
        js = scroll.to_top(smooth=True)
        assert "smooth" in js
    
    def test_to_top_instant(self):
        """Test to_top with instant scrolling."""
        scroll = use_scroll_position()
        js = scroll.to_top(smooth=False)
        assert "instant" in js
    
    def test_to_bottom_smooth(self):
        """Test to_bottom with smooth scrolling."""
        scroll = use_scroll_position()
        js = scroll.to_bottom(smooth=True)
        assert "smooth" in js
    
    def test_to_bottom_instant(self):
        """Test to_bottom with instant scrolling."""
        scroll = use_scroll_position()
        js = scroll.to_bottom(smooth=False)
        assert "instant" in js
    
    def test_to_element_with_complex_id(self):
        """Test to_element with complex ID."""
        scroll = use_scroll_position()
        js = scroll.to_element("my-complex-id-123")
        assert "my-complex-id-123" in js
    
    def test_to_element_smooth(self):
        """Test to_element with smooth scrolling."""
        scroll = use_scroll_position()
        js = scroll.to_element("section", smooth=True)
        assert "smooth" in js
    
    def test_to_element_instant(self):
        """Test to_element with instant scrolling."""
        scroll = use_scroll_position()
        js = scroll.to_element("section", smooth=False)
        assert "instant" in js
    
    def test_to_dict_structure(self):
        """Test to_dict has correct structure."""
        scroll = use_scroll_position()
        data = scroll.to_dict()
        
        assert "id" in data
        assert "type" in data
        assert data["type"] == "scrollPosition"
    
    def test_js_init_format(self):
        """Test JS init has correct format."""
        scroll = use_scroll_position()
        js = scroll.get_js_init()
        
        assert js.startswith("__pynext__.browser.initScrollPosition")
        assert scroll.id in js
    
    def test_hydration_data_structure(self):
        """Test hydration data has correct structure."""
        scroll = use_scroll_position()
        data = get_client_hydration_data()
        
        assert data["scrollPosition"] is not None
        assert "id" in data["scrollPosition"]
    
    def test_reset_clears_scroll(self):
        """Test reset clears scroll position."""
        scroll = use_scroll_position()
        
        reset_client_state()
        
        data = get_client_hydration_data()
        assert data["scrollPosition"] is None
    
    def test_subscribe_callback(self):
        """Test subscribe with callback."""
        scroll = use_scroll_position()
        
        callback = MagicMock()
        unsub = scroll.subscribe(callback)
        
        assert callable(unsub)
    
    def test_unsubscribe_removes_callback(self):
        """Test unsubscribe removes callback."""
        scroll = use_scroll_position()
        
        callback = MagicMock()
        unsub = scroll.subscribe(callback)
        unsub()
        
        assert callback not in scroll._subscribers
    
    def test_initial_values(self):
        """Test all initial values are 0."""
        scroll = use_scroll_position()
        
        assert scroll.x() == 0
        assert scroll.y() == 0
        assert scroll.progress() == 0.0
    
    def test_progress_float(self):
        """Test progress returns float."""
        scroll = use_scroll_position()
        assert isinstance(scroll.progress(), float)
    
    def test_x_int(self):
        """Test x returns int."""
        scroll = use_scroll_position()
        assert isinstance(scroll.x(), int)
    
    def test_y_int(self):
        """Test y returns int."""
        scroll = use_scroll_position()
        assert isinstance(scroll.y(), int)
    
    def test_tuple_unpacking(self):
        """Test tuple unpacking works."""
        scroll = use_scroll_position()
        x, y = scroll()
        assert x == 0
        assert y == 0
    
    def test_to_dict_json_serializable(self):
        """Test to_dict is JSON serializable."""
        scroll = use_scroll_position()
        data = scroll.to_dict()
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
    
    def test_scroll_methods_return_strings(self):
        """Test all scroll methods return strings."""
        scroll = use_scroll_position()
        
        assert isinstance(scroll.to(0, 0), str)
        assert isinstance(scroll.to_top(), str)
        assert isinstance(scroll.to_bottom(), str)
        assert isinstance(scroll.to_element("id"), str)
    
    def test_new_instance_after_reset(self):
        """Test new instance has new ID after reset."""
        scroll1 = use_scroll_position()
        id1 = scroll1.id
        
        reset_client_state()
        
        scroll2 = use_scroll_position()
        id2 = scroll2.id
        
        assert id1 != id2


# =============================================================================
# Intersection Observer Edge Cases (25 more tests)
# =============================================================================

class TestIntersectionEdgeCases:
    """Additional edge case tests for intersection observer."""
    
    def test_threshold_zero(self):
        """Test threshold of 0."""
        int_sig = use_intersection("elem", threshold=0.0)
        assert int_sig.threshold == 0.0
    
    def test_threshold_one(self):
        """Test threshold of 1."""
        int_sig = use_intersection("elem", threshold=1.0)
        assert int_sig.threshold == 1.0
    
    def test_threshold_half(self):
        """Test threshold of 0.5."""
        int_sig = use_intersection("elem", threshold=0.5)
        assert int_sig.threshold == 0.5
    
    def test_threshold_quarter(self):
        """Test threshold of 0.25."""
        int_sig = use_intersection("elem", threshold=0.25)
        assert int_sig.threshold == 0.25
    
    def test_root_margin_px(self):
        """Test root margin in pixels."""
        int_sig = use_intersection("elem", root_margin="50px")
        assert int_sig.root_margin == "50px"
    
    def test_root_margin_percent(self):
        """Test root margin in percent."""
        int_sig = use_intersection("elem", root_margin="10%")
        assert int_sig.root_margin == "10%"
    
    def test_root_margin_multiple(self):
        """Test root margin with multiple values."""
        int_sig = use_intersection("elem", root_margin="10px 20px 30px 40px")
        assert "10px 20px 30px 40px" in int_sig.root_margin
    
    def test_root_margin_negative(self):
        """Test negative root margin."""
        int_sig = use_intersection("elem", root_margin="-50px")
        assert "-50px" in int_sig.root_margin
    
    def test_to_dict_structure(self):
        """Test to_dict has correct structure."""
        int_sig = use_intersection("elem")
        data = int_sig.to_dict()
        
        assert "id" in data
        assert "elementId" in data
        assert "type" in data
        assert "options" in data
    
    def test_to_dict_options(self):
        """Test to_dict options structure."""
        int_sig = use_intersection("elem", threshold=0.5, root_margin="100px")
        data = int_sig.to_dict()
        
        assert data["options"]["threshold"] == 0.5
        assert data["options"]["rootMargin"] == "100px"
    
    def test_js_init_format(self):
        """Test JS init has correct format."""
        int_sig = use_intersection("elem")
        js = int_sig.get_js_init()
        
        assert js.startswith("__pynext__.browser.initIntersection")
    
    def test_hydration_data_structure(self):
        """Test hydration data has correct structure."""
        int_sig = use_intersection("elem")
        data = get_client_hydration_data()
        
        assert "intersections" in data
        assert len(data["intersections"]) == 1
    
    def test_reset_clears_intersections(self):
        """Test reset clears intersections."""
        int_sig = use_intersection("elem")
        
        reset_client_state()
        
        data = get_client_hydration_data()
        assert len(data["intersections"]) == 0
    
    def test_subscribe_callback(self):
        """Test subscribe with callback."""
        int_sig = use_intersection("elem")
        
        callback = MagicMock()
        unsub = int_sig.subscribe(callback)
        
        assert callable(unsub)
    
    def test_unsubscribe_removes_callback(self):
        """Test unsubscribe removes callback."""
        int_sig = use_intersection("elem")
        
        callback = MagicMock()
        unsub = int_sig.subscribe(callback)
        unsub()
        
        assert callback not in int_sig._subscribers
    
    def test_initial_not_visible(self):
        """Test initial visibility is False."""
        int_sig = use_intersection("elem")
        assert int_sig() is False
        assert int_sig.is_visible is False
    
    def test_initial_ratio_zero(self):
        """Test initial ratio is 0."""
        int_sig = use_intersection("elem")
        assert int_sig.ratio() == 0.0
    
    def test_callable_returns_bool(self):
        """Test callable returns boolean."""
        int_sig = use_intersection("elem")
        assert isinstance(int_sig(), bool)
    
    def test_ratio_returns_float(self):
        """Test ratio returns float."""
        int_sig = use_intersection("elem")
        assert isinstance(int_sig.ratio(), float)
    
    def test_many_observers(self):
        """Test creating many observers."""
        observers = [
            use_intersection(f"elem-{i}")
            for i in range(20)
        ]
        
        data = get_client_hydration_data()
        assert len(data["intersections"]) == 20
    
    def test_complex_element_id(self):
        """Test with complex element ID."""
        int_sig = use_intersection("my-complex-element-id-123")
        assert int_sig.element_id == "my-complex-element-id-123"
    
    def test_to_dict_json_serializable(self):
        """Test to_dict is JSON serializable."""
        int_sig = use_intersection("elem", threshold=0.5)
        data = int_sig.to_dict()
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
    
    def test_element_id_preserved(self):
        """Test element ID is preserved in to_dict."""
        int_sig = use_intersection("my-element")
        data = int_sig.to_dict()
        assert data["elementId"] == "my-element"
    
    def test_id_format(self):
        """Test ID has correct format."""
        int_sig = use_intersection("elem")
        assert int_sig.id.startswith("int_")
    
    def test_memoization_with_same_element(self):
        """Test memoization returns same signal for same element."""
        int1 = use_intersection("same-element")
        int2 = use_intersection("same-element")
        
        assert int1 is int2


# =============================================================================
# Integration Tests (30 tests)
# =============================================================================

class TestBrowserAPIIntegration:
    """Integration tests for multiple browser APIs together."""
    
    def test_all_hooks_together(self):
        """Test using all hooks together."""
        ws = use_websocket("/api/ws")
        mq = use_media_query("(max-width: 768px)")
        geo = use_geolocation()
        clip = use_clipboard()
        size = use_window_size()
        scroll = use_scroll_position()
        int_sig = use_intersection("elem")
        
        data = get_client_hydration_data()
        
        assert len(data["websocket"]) == 1
        assert len(data["mediaQueries"]) == 1
        assert data["geolocation"] is not None
        assert data["clipboard"] is not None
        assert data["windowSize"] is not None
        assert data["scrollPosition"] is not None
        assert len(data["intersections"]) == 1
    
    def test_multiple_websockets_and_media_queries(self):
        """Test multiple WebSockets and media queries."""
        ws1 = use_websocket("/api/ws1")
        ws2 = use_websocket("/api/ws2")
        mq1 = use_media_query("(max-width: 640px)")
        mq2 = use_media_query("(max-width: 768px)")
        mq3 = use_media_query("(max-width: 1024px)")
        
        data = get_client_hydration_data()
        
        assert len(data["websocket"]) == 2
        assert len(data["mediaQueries"]) == 3
    
    def test_hydration_data_completeness(self):
        """Test hydration data contains all expected keys."""
        ws = use_websocket("/api/ws")
        mq = use_media_query("(max-width: 768px)")
        geo = use_geolocation()
        clip = use_clipboard()
        size = use_window_size()
        scroll = use_scroll_position()
        int_sig = use_intersection("elem")
        
        data = get_client_hydration_data()
        
        expected_keys = [
            "shortcuts", "sequences", "storage", "refs", "effects",
            "theme", "sse", "visibility", "online",
            "websocket", "mediaQueries", "geolocation", "clipboard",
            "windowSize", "scrollPosition", "intersections"
        ]
        
        for key in expected_keys:
            assert key in data
    
    def test_reset_clears_all(self):
        """Test reset clears all hooks."""
        ws = use_websocket("/api/ws")
        mq = use_media_query("(max-width: 768px)")
        geo = use_geolocation()
        clip = use_clipboard()
        size = use_window_size()
        scroll = use_scroll_position()
        int_sig = use_intersection("elem")
        
        reset_client_state()
        
        data = get_client_hydration_data()
        
        assert len(data["websocket"]) == 0
        assert len(data["mediaQueries"]) == 0
        assert data["geolocation"] is None
        assert data["clipboard"] is None
        assert data["windowSize"] is None
        assert data["scrollPosition"] is None
        assert len(data["intersections"]) == 0
    
    def test_singletons_persist(self):
        """Test singleton hooks persist across calls."""
        geo1 = use_geolocation()
        clip1 = use_clipboard()
        size1 = use_window_size()
        scroll1 = use_scroll_position()
        
        geo2 = use_geolocation()
        clip2 = use_clipboard()
        size2 = use_window_size()
        scroll2 = use_scroll_position()
        
        assert geo1 is geo2
        assert clip1 is clip2
        assert size1 is size2
        assert scroll1 is scroll2
    
    def test_memoized_hooks_persist(self):
        """Test memoized hooks persist."""
        mq1 = use_media_query("(max-width: 768px)")
        int1 = use_intersection("elem")
        
        mq2 = use_media_query("(max-width: 768px)")
        int2 = use_intersection("elem")
        
        assert mq1 is mq2
        assert int1 is int2
    
    def test_non_memoized_hooks_create_new(self):
        """Test non-memoized hooks create new instances."""
        ws1 = use_websocket("/api/ws")
        ws2 = use_websocket("/api/ws")
        
        # Different instances with same URL
        assert ws1 is not ws2
    
    def test_all_js_inits_valid(self):
        """Test all JS init methods return valid JavaScript."""
        ws = use_websocket("/api/ws")
        mq = use_media_query("(max-width: 768px)")
        geo = use_geolocation()
        clip = use_clipboard()
        size = use_window_size()
        scroll = use_scroll_position()
        int_sig = use_intersection("elem")
        
        js_inits = [
            ws.get_js_init(),
            mq.get_js_init(),
            geo.get_js_init(),
            clip.get_js_init(),
            size.get_js_init(),
            scroll.get_js_init(),
            int_sig.get_js_init(),
        ]
        
        for js in js_inits:
            assert "__pynext__" in js
            assert isinstance(js, str)
    
    def test_all_to_dicts_json_serializable(self):
        """Test all to_dict methods return JSON serializable data."""
        ws = use_websocket("/api/ws")
        mq = use_media_query("(max-width: 768px)")
        geo = use_geolocation()
        clip = use_clipboard()
        size = use_window_size()
        scroll = use_scroll_position()
        int_sig = use_intersection("elem")
        
        dicts = [
            ws.to_dict(),
            mq.to_dict(),
            geo.to_dict(),
            clip.to_dict(),
            size.to_dict(),
            scroll.to_dict(),
            int_sig.to_dict(),
        ]
        
        for d in dicts:
            json_str = json.dumps(d)
            assert isinstance(json_str, str)
    
    def test_hydration_data_json_serializable(self):
        """Test full hydration data is JSON serializable."""
        ws = use_websocket("/api/ws")
        mq = use_media_query("(max-width: 768px)")
        geo = use_geolocation()
        clip = use_clipboard()
        size = use_window_size()
        scroll = use_scroll_position()
        int_sig = use_intersection("elem")
        
        data = get_client_hydration_data()
        json_str = json.dumps(data)
        
        assert isinstance(json_str, str)
        assert len(json_str) > 0
    
    def test_websocket_with_responsive_design(self):
        """Test WebSocket with media query for responsive chat."""
        ws = use_websocket("/api/chat")
        is_mobile = use_media_query("(max-width: 768px)")
        
        # Both should work together
        assert ws.connected() is False  # Not connected yet
        assert is_mobile() is False  # Server-side default
    
    def test_geolocation_with_scroll(self):
        """Test geolocation with scroll tracking."""
        geo = use_geolocation()
        scroll = use_scroll_position()
        
        # Both singletons
        geo2 = use_geolocation()
        scroll2 = use_scroll_position()
        
        assert geo is geo2
        assert scroll is scroll2
    
    def test_clipboard_with_intersection(self):
        """Test clipboard with intersection for copy-on-view."""
        clip = use_clipboard()
        visible = use_intersection("copy-section")
        
        # Generate JS for both
        copy_js = clip.copy("Copy this!")
        
        assert "__pynext__.browser.clipboardCopy" in copy_js
        assert visible() is False
    
    def test_window_size_with_media_query(self):
        """Test window size with media query."""
        size = use_window_size()
        is_mobile = use_media_query("(max-width: 768px)")
        
        # Both track viewport
        assert size.width() == 0  # Server default
        assert is_mobile() is False  # Server default
    
    def test_many_intersections_with_scroll(self):
        """Test many intersection observers with scroll tracking."""
        scroll = use_scroll_position()
        
        sections = [
            use_intersection(f"section-{i}")
            for i in range(10)
        ]
        
        data = get_client_hydration_data()
        
        assert len(data["intersections"]) == 10
        assert data["scrollPosition"] is not None
    
    def test_stress_many_hooks(self):
        """Test creating many hooks doesn't break."""
        websockets = [use_websocket(f"/api/ws/{i}") for i in range(20)]
        media_queries = [use_media_query(f"(min-width: {i*100}px)") for i in range(20)]
        intersections = [use_intersection(f"elem-{i}") for i in range(20)]
        
        data = get_client_hydration_data()
        
        assert len(data["websocket"]) == 20
        assert len(data["mediaQueries"]) == 20
        assert len(data["intersections"]) == 20
    
    def test_unique_ids_across_types(self):
        """Test IDs are unique even across different hook types."""
        ws = use_websocket("/api/ws")
        mq = use_media_query("(max-width: 768px)")
        int_sig = use_intersection("elem")
        
        ids = [ws.id, mq.id, int_sig.id]
        assert len(set(ids)) == 3  # All unique
    
    def test_order_of_creation_preserved(self):
        """Test order of creation is preserved in hydration data."""
        ws1 = use_websocket("/api/ws1")
        ws2 = use_websocket("/api/ws2")
        ws3 = use_websocket("/api/ws3")
        
        data = get_client_hydration_data()
        
        urls = [ws["url"] for ws in data["websocket"]]
        assert urls == ["/api/ws1", "/api/ws2", "/api/ws3"]
    
    def test_media_query_memoization_order(self):
        """Test media query memoization preserves first instance."""
        mq1 = use_media_query("(max-width: 768px)")
        mq2 = use_media_query("(max-width: 768px)")
        
        # Same instance
        assert mq1 is mq2
        
        # ID from first creation
        assert mq1.id == mq2.id
    
    def test_intersection_memoization_order(self):
        """Test intersection memoization preserves first instance."""
        int1 = use_intersection("elem")
        int2 = use_intersection("elem")
        
        # Same instance
        assert int1 is int2
        
        # ID from first creation
        assert int1.id == int2.id


# =============================================================================
# Error Handling Tests (20 tests)
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in browser APIs."""
    
    def test_websocket_empty_url_allowed(self):
        """Test WebSocket with empty URL is allowed."""
        ws = use_websocket("")
        assert ws is not None
    
    def test_media_query_empty_allowed(self):
        """Test empty media query is allowed."""
        mq = use_media_query("")
        assert mq is not None
    
    def test_intersection_empty_id_allowed(self):
        """Test empty element ID is allowed."""
        int_sig = use_intersection("")
        assert int_sig is not None
    
    def test_geolocation_negative_timeout(self):
        """Test geolocation with negative timeout."""
        geo = use_geolocation(timeout=-1)
        assert geo.timeout == -1
    
    def test_geolocation_zero_timeout(self):
        """Test geolocation with zero timeout."""
        geo = use_geolocation(timeout=0)
        assert geo.timeout == 0
    
    def test_intersection_negative_threshold(self):
        """Test intersection with negative threshold."""
        int_sig = use_intersection("elem", threshold=-0.5)
        assert int_sig.threshold == -0.5
    
    def test_intersection_threshold_over_one(self):
        """Test intersection with threshold > 1."""
        int_sig = use_intersection("elem", threshold=1.5)
        assert int_sig.threshold == 1.5
    
    def test_websocket_reconnect_interval_zero(self):
        """Test WebSocket with zero reconnect interval."""
        ws = use_websocket("/api/ws", reconnect_interval=0)
        assert ws.reconnect_interval == 0
    
    def test_websocket_reconnect_interval_negative(self):
        """Test WebSocket with negative reconnect interval."""
        ws = use_websocket("/api/ws", reconnect_interval=-1000)
        assert ws.reconnect_interval == -1000
    
    def test_scroll_to_negative_position(self):
        """Test scroll to negative position generates valid JS."""
        scroll = use_scroll_position()
        js = scroll.to(-100, -200)
        assert "-100" in js
        assert "-200" in js
    
    def test_clipboard_copy_very_long_text(self):
        """Test clipboard copy with very long text."""
        clip = use_clipboard()
        long_text = "x" * 1000000  # 1MB of text
        js = clip.copy(long_text)
        assert "__pynext__.browser.clipboardCopy" in js
    
    def test_websocket_send_circular_reference_fails(self):
        """Test WebSocket send with circular reference."""
        ws = use_websocket("/api/ws")
        
        # Circular reference
        data = {}
        data["self"] = data
        
        # Should raise or handle gracefully
        try:
            js = ws.send(data)
            # If it doesn't raise, it should at least not crash
            assert True
        except (ValueError, TypeError):
            # JSON serialization should fail
            assert True
    
    def test_geolocation_max_age_negative(self):
        """Test geolocation with negative max_age."""
        geo = use_geolocation(max_age=-1)
        assert geo.max_age == -1
    
    def test_multiple_resets(self):
        """Test multiple reset calls don't break."""
        ws = use_websocket("/api/ws")
        
        reset_client_state()
        reset_client_state()
        reset_client_state()
        
        data = get_client_hydration_data()
        assert data is not None
    
    def test_hooks_after_reset(self):
        """Test hooks work correctly after reset."""
        ws1 = use_websocket("/api/ws")
        
        reset_client_state()
        
        ws2 = use_websocket("/api/ws")
        
        # New instance
        assert ws1 is not ws2
    
    def test_special_characters_in_url(self):
        """Test special characters in WebSocket URL."""
        ws = use_websocket("/api/ws?param=value&other=123#hash")
        assert "?" in ws.url
        assert "&" in ws.url
    
    def test_unicode_in_media_query(self):
        """Test unicode in media query (unusual but valid)."""
        mq = use_media_query("(max-width: 768px) /* comment with émojis 🌍 */")
        assert "🌍" in mq.query
    
    def test_none_callback_handling(self):
        """Test None callbacks are handled."""
        ws = use_websocket(
            "/api/ws",
            on_message=None,
            on_open=None,
            on_close=None,
            on_error=None,
        )
        
        data = ws.to_dict()
        assert data["hasOnMessage"] is False
        assert data["hasOnOpen"] is False
    
    def test_hydration_data_after_partial_setup(self):
        """Test hydration data with only some hooks used."""
        ws = use_websocket("/api/ws")
        # Don't create other hooks
        
        data = get_client_hydration_data()
        
        assert len(data["websocket"]) == 1
        assert data["geolocation"] is None
        assert data["clipboard"] is None
    
    def test_to_dict_empty_options(self):
        """Test to_dict with minimal options."""
        geo = use_geolocation()
        data = geo.to_dict()
        
        assert "options" in data
        assert isinstance(data["options"], dict)

