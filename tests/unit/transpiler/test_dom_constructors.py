"""
Transpiler Core Fix: DOM Constructor Tests

Tests that verify DOM constructors emit 'new' keyword in JavaScript.

Python: url = URL("https://example.com")
JS:     let url = new URL("https://example.com");

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


class TestURLConstructors:
    """Test URL-related constructors emit 'new'."""

    def test_url_constructor(self):
        """URL constructor should emit 'new URL(...)'."""
        code = 'url = URL("https://example.com")'
        result = transpile(code)
        assert 'new URL("https://example.com")' in result

    def test_urlsearchparams_constructor(self):
        """URLSearchParams constructor should emit 'new'."""
        code = 'params = URLSearchParams("a=1&b=2")'
        result = transpile(code)
        assert 'new URLSearchParams("a=1&b=2")' in result

    def test_urlsearchparams_empty(self):
        """URLSearchParams with no args should emit 'new'."""
        code = 'params = URLSearchParams()'
        result = transpile(code)
        assert 'new URLSearchParams()' in result


class TestEncodingConstructors:
    """Test encoding-related constructors emit 'new'."""

    def test_textencoder_constructor(self):
        """TextEncoder constructor should emit 'new'."""
        code = 'encoder = TextEncoder()'
        result = transpile(code)
        assert 'new TextEncoder()' in result

    def test_textdecoder_constructor(self):
        """TextDecoder constructor should emit 'new'."""
        code = 'decoder = TextDecoder("utf-8")'
        result = transpile(code)
        assert 'new TextDecoder("utf-8")' in result

    def test_textdecoder_with_options(self):
        """TextDecoder with options should emit 'new'."""
        code = 'decoder = TextDecoder("utf-8", {"fatal": True})'
        result = transpile(code)
        assert 'new TextDecoder("utf-8"' in result


class TestBinaryDataConstructors:
    """Test binary data constructors emit 'new'."""

    def test_blob_constructor(self):
        """Blob constructor should emit 'new'."""
        code = 'blob = Blob(["Hello"], {"type": "text/plain"})'
        result = transpile(code)
        assert 'new Blob(["Hello"]' in result

    def test_arraybuffer_constructor(self):
        """ArrayBuffer constructor should emit 'new'."""
        code = 'buffer = ArrayBuffer(256)'
        result = transpile(code)
        assert 'new ArrayBuffer(256)' in result

    def test_uint8array_constructor(self):
        """Uint8Array constructor should emit 'new'."""
        code = 'arr = Uint8Array([1, 2, 3])'
        result = transpile(code)
        assert 'new Uint8Array([1, 2, 3])' in result

    def test_dataview_constructor(self):
        """DataView constructor should emit 'new'."""
        code = 'view = DataView(buffer)'
        result = transpile(code)
        assert 'new DataView(buffer)' in result

    def test_file_constructor(self):
        """File constructor should emit 'new'."""
        code = 'file = File(["content"], "file.txt", {"type": "text/plain"})'
        result = transpile(code)
        assert 'new File(["content"]' in result


class TestNetworkConstructors:
    """Test network-related constructors emit 'new'."""

    def test_headers_constructor(self):
        """Headers constructor should emit 'new'."""
        code = 'headers = Headers()'
        result = transpile(code)
        assert 'new Headers()' in result

    def test_request_constructor(self):
        """Request constructor should emit 'new'."""
        code = 'req = Request("https://api.example.com/data")'
        result = transpile(code)
        assert 'new Request("https://api.example.com/data")' in result

    def test_formdata_constructor(self):
        """FormData constructor should emit 'new'."""
        code = 'form = FormData()'
        result = transpile(code)
        assert 'new FormData()' in result

    def test_websocket_constructor(self):
        """WebSocket constructor should emit 'new'."""
        code = 'ws = WebSocket("wss://example.com/socket")'
        result = transpile(code)
        assert 'new WebSocket("wss://example.com/socket")' in result


class TestEventConstructors:
    """Test event constructors emit 'new'."""

    def test_event_constructor(self):
        """Event constructor should emit 'new'."""
        code = 'event = Event("click")'
        result = transpile(code)
        assert 'new Event("click")' in result

    def test_customevent_constructor(self):
        """CustomEvent constructor should emit 'new'."""
        code = 'event = CustomEvent("myevent", {"detail": data})'
        result = transpile(code)
        assert 'new CustomEvent("myevent"' in result


class TestObserverConstructors:
    """Test observer constructors emit 'new'."""

    def test_mutationobserver_constructor(self):
        """MutationObserver constructor should emit 'new'."""
        code = 'observer = MutationObserver(callback)'
        result = transpile(code)
        assert 'new MutationObserver(callback)' in result

    def test_abortcontroller_constructor(self):
        """AbortController constructor should emit 'new'."""
        code = 'controller = AbortController()'
        result = transpile(code)
        assert 'new AbortController()' in result


class TestStaticMethodsDoNotGetNew:
    """Test that static methods do NOT get 'new' keyword."""

    def test_url_createobjecturl_static(self):
        """URL.createObjectURL is static, should NOT have 'new'."""
        code = 'url_str = URL.createObjectURL(blob)'
        result = transpile(code)
        assert 'URL.createObjectURL(blob)' in result
        assert 'new URL.createObjectURL' not in result

    def test_url_revokeobjecturl_static(self):
        """URL.revokeObjectURL is static, should NOT have 'new'."""
        code = 'URL.revokeObjectURL(url_str)'
        result = transpile(code)
        assert 'URL.revokeObjectURL(url_str)' in result
        assert 'new URL.revokeObjectURL' not in result

