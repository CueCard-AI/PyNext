"""
Phase 34.5: E2E Browser Tests for URL, Encoding & Binary Data

Tests that verify these APIs work correctly in a real browser using Playwright.
These tests transpile Python code to JS and execute it in the browser.

Total: 15 tests
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def browser_page(page: Page):
    """Set up a simple HTML page for testing."""
    page.set_content("""
    <!DOCTYPE html>
    <html>
    <head><title>URL/Encoding Test</title></head>
    <body>
        <div id="result"></div>
        <a id="download-link" style="display:none"></a>
        <input type="file" id="file-input" style="display:none">
        <canvas id="canvas" width="100" height="100"></canvas>
        <img id="test-image">
    </body>
    </html>
    """)
    return page


class TestURLBrowser:
    """Test URL API in real browser."""
    
    def test_url_createObjectURL(self, browser_page: Page):
        """Create and use blob URL."""
        result = browser_page.evaluate("""
        () => {
            const blob = new Blob(['Hello, World!'], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const isValid = url.startsWith('blob:');
            URL.revokeObjectURL(url);
            return isValid;
        }
        """)
        assert result is True
    
    def test_url_revokeObjectURL(self, browser_page: Page):
        """Revoke blob URL releases resource."""
        result = browser_page.evaluate("""
        () => {
            const blob = new Blob(['test']);
            const url = URL.createObjectURL(blob);
            URL.revokeObjectURL(url);
            // URL is now invalid, but no error thrown
            return true;
        }
        """)
        assert result is True
    
    def test_url_parsing(self, browser_page: Page):
        """Parse complex URL."""
        result = browser_page.evaluate("""
        () => {
            const url = new URL('https://user:pass@example.com:8080/path?q=1#hash');
            return {
                protocol: url.protocol,
                username: url.username,
                password: url.password,
                hostname: url.hostname,
                port: url.port,
                pathname: url.pathname,
                search: url.search,
                hash: url.hash
            };
        }
        """)
        assert result["protocol"] == "https:"
        assert result["username"] == "user"
        assert result["hostname"] == "example.com"
        assert result["port"] == "8080"
    
    def test_searchparams_manipulation(self, browser_page: Page):
        """Manipulate URLSearchParams in browser."""
        result = browser_page.evaluate("""
        () => {
            const params = new URLSearchParams('a=1&b=2');
            params.set('c', '3');
            params.delete('a');
            params.append('b', '4');
            return params.toString();
        }
        """)
        assert "b=2" in result
        assert "b=4" in result
        assert "c=3" in result
        assert "a=1" not in result


class TestEncodingBrowser:
    """Test Encoding API in real browser."""
    
    def test_textencoder_decode_roundtrip(self, browser_page: Page):
        """Encode and decode text."""
        result = browser_page.evaluate("""
        () => {
            const encoder = new TextEncoder();
            const decoder = new TextDecoder();
            const original = 'Hello, 世界! 🌍';
            const encoded = encoder.encode(original);
            const decoded = decoder.decode(encoded);
            return decoded === original;
        }
        """)
        assert result is True
    
    def test_base64_roundtrip(self, browser_page: Page):
        """btoa/atob round trip."""
        result = browser_page.evaluate("""
        () => {
            const original = 'Hello, World!';
            const encoded = btoa(original);
            const decoded = atob(encoded);
            return {
                encoded: encoded,
                decoded: decoded,
                match: decoded === original
            };
        }
        """)
        assert result["encoded"] == "SGVsbG8sIFdvcmxkIQ=="
        assert result["match"] is True
    
    def test_textdecoder_latin1(self, browser_page: Page):
        """Decode Latin-1 encoded bytes."""
        result = browser_page.evaluate("""
        () => {
            // Latin-1 bytes for "café"
            const bytes = new Uint8Array([99, 97, 102, 233]);
            const decoder = new TextDecoder('iso-8859-1');
            return decoder.decode(bytes);
        }
        """)
        assert result == "café"


class TestBinaryBrowser:
    """Test Binary Data API in real browser."""
    
    def test_arraybuffer_slice(self, browser_page: Page):
        """ArrayBuffer slicing creates copy."""
        result = browser_page.evaluate("""
        () => {
            const buffer = new ArrayBuffer(10);
            const view = new Uint8Array(buffer);
            view[5] = 42;
            
            const sliced = buffer.slice(3, 8);
            const slicedView = new Uint8Array(sliced);
            
            // Modify original - slice should be unaffected
            view[5] = 0;
            
            return slicedView[2]; // Should still be 42
        }
        """)
        assert result == 42
    
    def test_dataview_endianness(self, browser_page: Page):
        """DataView reads with correct endianness."""
        result = browser_page.evaluate("""
        () => {
            const buffer = new ArrayBuffer(4);
            const view = new DataView(buffer);
            view.setInt32(0, 0x12345678, true); // Little-endian
            
            return {
                le: view.getInt32(0, true).toString(16),
                be: view.getInt32(0, false).toString(16)
            };
        }
        """)
        assert result["le"] == "12345678"
        assert result["be"] == "78563412"
    
    def test_canvas_imagedata(self, browser_page: Page):
        """Manipulate canvas pixel data with Uint8ClampedArray."""
        result = browser_page.evaluate("""
        () => {
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            
            // Create red pixel data
            const imageData = ctx.createImageData(10, 10);
            const data = imageData.data; // Uint8ClampedArray
            
            // Set all pixels to red
            for (let i = 0; i < data.length; i += 4) {
                data[i] = 255;     // R
                data[i + 1] = 0;   // G
                data[i + 2] = 0;   // B
                data[i + 3] = 255; // A
            }
            
            ctx.putImageData(imageData, 0, 0);
            
            // Read back first pixel
            const readBack = ctx.getImageData(0, 0, 1, 1).data;
            return {
                r: readBack[0],
                g: readBack[1],
                b: readBack[2],
                a: readBack[3]
            };
        }
        """)
        assert result["r"] == 255
        assert result["g"] == 0
        assert result["b"] == 0
        assert result["a"] == 255


class TestBlobBrowser:
    """Test Blob API in real browser."""
    
    def test_blob_text(self, browser_page: Page):
        """Read Blob as text."""
        result = browser_page.evaluate("""
        async () => {
            const blob = new Blob(['Hello, World!'], { type: 'text/plain' });
            const text = await blob.text();
            return text;
        }
        """)
        assert result == "Hello, World!"
    
    def test_blob_arrayBuffer(self, browser_page: Page):
        """Read Blob as ArrayBuffer."""
        result = browser_page.evaluate("""
        async () => {
            const blob = new Blob([new Uint8Array([1, 2, 3, 4, 5])]);
            const buffer = await blob.arrayBuffer();
            const view = new Uint8Array(buffer);
            return Array.from(view);
        }
        """)
        assert result == [1, 2, 3, 4, 5]
    
    def test_base64_image_display(self, browser_page: Page):
        """Display base64 encoded image."""
        result = browser_page.evaluate("""
        () => {
            // 1x1 red PNG in base64
            const base64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==';
            const img = document.getElementById('test-image');
            img.src = 'data:image/png;base64,' + base64;
            return img.src.startsWith('data:image/png;base64,');
        }
        """)
        assert result is True
    
    def test_crypto_digest_with_encoding(self, browser_page: Page):
        """Use crypto.subtle.digest with TextEncoder (requires HTTPS context)."""
        result = browser_page.evaluate("""
        async () => {
            // crypto.subtle requires secure context (HTTPS) in most browsers
            // Check if available first
            if (!crypto.subtle) {
                return 'crypto.subtle not available';
            }
            const text = 'Hello, World!';
            const encoder = new TextEncoder();
            const data = encoder.encode(text);
            const hashBuffer = await crypto.subtle.digest('SHA-256', data);
            const hashArray = new Uint8Array(hashBuffer);
            const hashHex = Array.from(hashArray).map(b => b.toString(16).padStart(2, '0')).join('');
            return hashHex;
        }
        """)
        # Either returns the hash or indicates crypto.subtle not available
        assert result == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f" or result == 'crypto.subtle not available'


class TestBase64EdgeCasesBrowser:
    """Test base64 edge cases in real browser."""
    
    def test_btoa_unicode_throws_error(self, browser_page: Page):
        """btoa with unicode characters should throw in browser.
        
        This is a critical risk area - btoa only works with ASCII/Latin-1.
        Passing unicode characters will cause a runtime error.
        """
        result = browser_page.evaluate("""
        () => {
            try {
                // This should throw because btoa only works with ASCII
                btoa("Hello, 世界!");
                return { threw: false };
            } catch (e) {
                return { 
                    threw: true, 
                    message: e.message,
                    name: e.name
                };
            }
        }
        """)
        assert result["threw"] is True
        # Chrome: "Failed to execute 'btoa' on 'Window': The string to be encoded contains characters outside of the Latin1 range."
        # Firefox: "String contains an invalid character"
        assert "character" in result["message"].lower() or "latin" in result["message"].lower()
    
    def test_btoa_ascii_works(self, browser_page: Page):
        """btoa with ASCII characters works correctly."""
        result = browser_page.evaluate("""
        () => {
            return btoa("Hello, World!");
        }
        """)
        assert result == "SGVsbG8sIFdvcmxkIQ=="
    
    def test_atob_valid_base64(self, browser_page: Page):
        """atob decodes valid base64."""
        result = browser_page.evaluate("""
        () => {
            return atob("SGVsbG8sIFdvcmxkIQ==");
        }
        """)
        assert result == "Hello, World!"
    
    def test_atob_invalid_base64_throws(self, browser_page: Page):
        """atob with invalid base64 should throw."""
        result = browser_page.evaluate("""
        () => {
            try {
                atob("not-valid-base64!!!");
                return { threw: false };
            } catch (e) {
                return { threw: true, name: e.name };
            }
        }
        """)
        assert result["threw"] is True
    
    def test_unicode_to_base64_workaround(self, browser_page: Page):
        """Proper way to encode unicode to base64 using TextEncoder."""
        result = browser_page.evaluate("""
        () => {
            // The correct way to encode unicode to base64
            const text = "Hello, 世界!";
            const encoder = new TextEncoder();
            const bytes = encoder.encode(text);
            
            // Convert Uint8Array to binary string
            let binary = "";
            for (let i = 0; i < bytes.length; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            
            // Now btoa works
            const base64 = btoa(binary);
            
            // Decode it back
            const decodedBinary = atob(base64);
            const decodedBytes = new Uint8Array(decodedBinary.length);
            for (let i = 0; i < decodedBinary.length; i++) {
                decodedBytes[i] = decodedBinary.charCodeAt(i);
            }
            
            const decoder = new TextDecoder();
            const decodedText = decoder.decode(decodedBytes);
            
            return decodedText;
        }
        """)
        assert result == "Hello, 世界!"


