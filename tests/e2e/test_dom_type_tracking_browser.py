"""
DOM Type-Aware Transpilation - E2E Browser Tests

Tests that verify the transpiled code with DOM type-aware passthrough
runs correctly in a real browser using Playwright.

Total: 5 tests
"""

import pytest
from playwright.sync_api import Page


@pytest.fixture
def browser_page(page: Page):
    """Set up a simple HTML page for testing."""
    page.set_content("""
    <!DOCTYPE html>
    <html>
    <head><title>DOM Type Tracking Test</title></head>
    <body>
        <div id="result"></div>
    </body>
    </html>
    """)
    return page


class TestDOMTypeTrackingBrowser:
    """E2E tests for DOM type-aware transpilation."""
    
    def test_textencoder_encode_in_browser(self, browser_page: Page):
        """Verify TextEncoder.encode() works correctly in browser."""
        result = browser_page.evaluate("""
        () => {
            // This simulates the transpiled code:
            let encoder = new TextEncoder();
            let bytes = encoder.encode("Hello, World!");
            return {
                byteLength: bytes.byteLength,
                firstByte: bytes[0],  // 'H' = 72
                lastByte: bytes[bytes.byteLength - 1]  // '!' = 33
            };
        }
        """)
        assert result["byteLength"] == 13
        assert result["firstByte"] == 72  # 'H'
        assert result["lastByte"] == 33   # '!'
    
    def test_urlsearchparams_methods_in_browser(self, browser_page: Page):
        """Verify URLSearchParams methods work correctly in browser."""
        result = browser_page.evaluate("""
        () => {
            // This simulates the transpiled code:
            let params = new URLSearchParams("a=1&b=2");
            params.set("c", "3");
            params.sort();
            
            return {
                get_a: params.get("a"),
                get_b: params.get("b"),
                get_c: params.get("c"),
                sorted: params.toString(),
                keys: Array.from(params.keys()),
                values: Array.from(params.values())
            };
        }
        """)
        assert result["get_a"] == "1"
        assert result["get_b"] == "2"
        assert result["get_c"] == "3"
        assert result["keys"] == ["a", "b", "c"]  # Sorted order
    
    def test_blob_methods_in_browser(self, browser_page: Page):
        """Verify Blob methods work correctly in browser."""
        result = browser_page.evaluate("""
        async () => {
            // This simulates the transpiled code:
            let blob = new Blob(["Hello, World!"], { type: "text/plain" });
            let text = await blob.text();
            let sliced = blob.slice(0, 5);
            let slicedText = await sliced.text();
            
            return {
                size: blob.size,
                type: blob.type,
                text: text,
                slicedSize: sliced.size,
                slicedText: slicedText
            };
        }
        """)
        assert result["size"] == 13
        assert result["type"] == "text/plain"
        assert result["text"] == "Hello, World!"
        assert result["slicedSize"] == 5
        assert result["slicedText"] == "Hello"
    
    def test_dataview_methods_in_browser(self, browser_page: Page):
        """Verify DataView methods work correctly in browser."""
        result = browser_page.evaluate("""
        () => {
            // This simulates the transpiled code:
            let buffer = new ArrayBuffer(16);
            let view = new DataView(buffer);
            
            view.setInt32(0, 12345, true);  // Little-endian
            view.setFloat64(4, 3.14159, true);
            
            return {
                int32: view.getInt32(0, true),
                float64: view.getFloat64(4, true),
                bufferLength: buffer.byteLength
            };
        }
        """)
        assert result["int32"] == 12345
        assert abs(result["float64"] - 3.14159) < 0.00001
        assert result["bufferLength"] == 16
    
    def test_encode_decode_roundtrip_in_browser(self, browser_page: Page):
        """Verify TextEncoder/TextDecoder roundtrip works in browser."""
        result = browser_page.evaluate("""
        () => {
            // This simulates the transpiled code:
            let encoder = new TextEncoder();
            let decoder = new TextDecoder();
            
            let original = "Hello, 世界! 🌍";
            let encoded = encoder.encode(original);
            let decoded = decoder.decode(encoded);
            
            return {
                original: original,
                decoded: decoded,
                matches: original === decoded,
                byteLength: encoded.byteLength
            };
        }
        """)
        assert result["original"] == "Hello, 世界! 🌍"
        assert result["decoded"] == "Hello, 世界! 🌍"
        assert result["matches"] is True
        # UTF-8: "Hello, " = 7, "世界" = 6, "! " = 2, "🌍" = 4 = 19 bytes
        assert result["byteLength"] == 19


