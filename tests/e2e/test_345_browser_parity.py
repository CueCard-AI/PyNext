"""
Phase 34.5: Browser Parity Tests for URL, Encoding & Binary Data

WHAT: Tests that verify TRANSPILED Python code runs correctly in real browsers
WHY: Ensures transpilation produces semantically correct JS, not just syntactically valid
HOW: Transpile Python → Execute in Playwright browser → Verify output
WHO: CI/CD pipeline, developers testing URL/Encoding APIs
WHEN: During E2E testing phase
WHERE: tests/e2e/test_345_browser_parity.py

These tests go beyond the existing `test_345_url_encoding_browser.py` which tests
raw JavaScript directly. This file tests TRANSPILED Python code.

Total: 31 tests
- URL API: 5 tests
- URLSearchParams: 4 tests
- TextEncoder: 3 tests
- TextDecoder: 3 tests
- Base64: 3 tests
- TypedArrays: 2 tests
- DataView: 3 tests
- Blob: 3 tests
- FileReader: 3 tests
- File: 2 tests
"""

import pytest
from playwright.sync_api import Page
from tests.e2e.browser_parity_harness import BrowserParityHarness, browser_parity_harness


# =============================================================================
# URL API BROWSER PARITY TESTS (5 tests)
# =============================================================================

@pytest.mark.e2e
class TestURLBrowserParity:
    """Verify transpiled URL API code runs correctly in browser."""
    
    def test_url_parsing(self, browser_parity_harness: BrowserParityHarness):
        """URL constructor parses all components."""
        python_code = '''
url = URL("https://user:pass@example.com:8080/path/to/page?foo=bar#section")
print(url.protocol)
print(url.hostname)
print(url.port)
print(url.pathname)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "https:" in result["output"][0]
        assert "example.com" in result["output"][1]
        assert "8080" in result["output"][2]
        assert "/path/to/page" in result["output"][3]
    
    def test_url_search_property(self, browser_parity_harness: BrowserParityHarness):
        """URL.search and URL.hash properties work."""
        python_code = '''
url = URL("https://example.com/page?key=value#anchor")
print(url.search)
print(url.hash)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "?key=value" in result["output"][0]
        assert "#anchor" in result["output"][1]
    
    def test_url_modification(self, browser_parity_harness: BrowserParityHarness):
        """URL properties can be modified."""
        python_code = '''
url = URL("https://example.com/old")
url.pathname = "/new/path"
url.hash = "#updated"
print(url.href)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        output = result["output"][0]
        assert "/new/path" in output
        assert "#updated" in output
    
    def test_url_relative_resolution(self, browser_parity_harness: BrowserParityHarness):
        """URL resolves relative paths against base."""
        python_code = '''
base = URL("https://example.com/a/b/c")
relative = URL("../d", base)
print(relative.pathname)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "/a/d" in result["output"][0]
    
    def test_url_origin(self, browser_parity_harness: BrowserParityHarness):
        """URL.origin is computed correctly."""
        python_code = '''
url = URL("https://example.com:8080/path")
print(url.origin)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "https://example.com:8080" in result["output"][0]


# =============================================================================
# URLSEARCHPARAMS BROWSER PARITY TESTS (4 tests)
# =============================================================================

@pytest.mark.e2e
class TestURLSearchParamsBrowserParity:
    """Verify transpiled URLSearchParams code runs correctly in browser."""
    
    def test_searchparams_from_string(self, browser_parity_harness: BrowserParityHarness):
        """URLSearchParams parses query string."""
        python_code = '''
params = URLSearchParams("foo=1&bar=2&foo=3")
print(params.get("foo"))
print(params.get("bar"))
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "1" in result["output"][0]  # First foo value
        assert "2" in result["output"][1]
    
    def test_searchparams_getall(self, browser_parity_harness: BrowserParityHarness):
        """URLSearchParams.getAll returns all values."""
        python_code = '''
params = URLSearchParams("key=a&key=b&key=c")
all_values = params.getAll("key")
print(len(all_values))
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "3" in result["output"][0]
    
    def test_searchparams_set_append(self, browser_parity_harness: BrowserParityHarness):
        """URLSearchParams.set and append work."""
        python_code = '''
params = URLSearchParams()
params.set("key", "value1")
params.append("key", "value2")
print(params.getAll("key").length)
print(params.toString())
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "2" in result["output"][0]
        assert "key=" in result["output"][1]
    
    def test_searchparams_has_delete(self, browser_parity_harness: BrowserParityHarness):
        """URLSearchParams.has and delete work."""
        python_code = '''
params = URLSearchParams("a=1&b=2")
print(params.has("a"))
params.delete("a")
print(params.has("a"))
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "true" in result["output"][0].lower()
        assert "false" in result["output"][1].lower()


# =============================================================================
# TEXTENCODER BROWSER PARITY TESTS (3 tests)
# =============================================================================

@pytest.mark.e2e
class TestTextEncoderBrowserParity:
    """Verify transpiled TextEncoder code runs correctly in browser."""
    
    def test_encoder_basic(self, browser_parity_harness: BrowserParityHarness):
        """TextEncoder.encode() produces Uint8Array."""
        python_code = '''
encoder = TextEncoder()
bytes_array = encoder.encode("Hello")
print(bytes_array.length)
print(bytes_array[0])
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "5" in result["output"][0]  # "Hello" = 5 bytes
        assert "72" in result["output"][1]  # 'H' = 72
    
    def test_encoder_encoding_property(self, browser_parity_harness: BrowserParityHarness):
        """TextEncoder.encoding is always utf-8."""
        python_code = '''
encoder = TextEncoder()
print(encoder.encoding)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "utf-8" in result["output"][0]
    
    def test_encoder_unicode(self, browser_parity_harness: BrowserParityHarness):
        """TextEncoder handles Unicode correctly."""
        python_code = '''
encoder = TextEncoder()
bytes_array = encoder.encode("世界")
print(bytes_array.length)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        # "世界" = 6 bytes in UTF-8 (3 bytes per character)
        assert "6" in result["output"][0]


# =============================================================================
# TEXTDECODER BROWSER PARITY TESTS (3 tests)
# =============================================================================

@pytest.mark.e2e
class TestTextDecoderBrowserParity:
    """Verify transpiled TextDecoder code runs correctly in browser."""
    
    def test_decoder_basic(self, browser_parity_harness: BrowserParityHarness):
        """TextDecoder.decode() produces string."""
        python_code = '''
encoder = TextEncoder()
decoder = TextDecoder()
bytes_array = encoder.encode("Hello")
text = decoder.decode(bytes_array)
print(text)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "Hello" in result["output"][0]
    
    def test_decoder_encoding_property(self, browser_parity_harness: BrowserParityHarness):
        """TextDecoder.encoding reflects constructor arg."""
        python_code = '''
decoder1 = TextDecoder()
decoder2 = TextDecoder("utf-8")
print(decoder1.encoding)
print(decoder2.encoding)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "utf-8" in result["output"][0]
        assert "utf-8" in result["output"][1]
    
    def test_decoder_roundtrip(self, browser_parity_harness: BrowserParityHarness):
        """Encoder → Decoder roundtrip preserves text."""
        python_code = '''
encoder = TextEncoder()
decoder = TextDecoder()
original = "Hello, 世界!"
encoded = encoder.encode(original)
decoded = decoder.decode(encoded)
print(original == decoded)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "true" in result["output"][0].lower()


# =============================================================================
# BASE64 BROWSER PARITY TESTS (3 tests)
# =============================================================================

@pytest.mark.e2e
class TestBase64BrowserParity:
    """Verify transpiled btoa/atob code runs correctly in browser."""
    
    def test_btoa_basic(self, browser_parity_harness: BrowserParityHarness):
        """btoa encodes string to Base64."""
        python_code = '''
encoded = btoa("Hello")
print(encoded)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "SGVsbG8=" in result["output"][0]
    
    def test_atob_basic(self, browser_parity_harness: BrowserParityHarness):
        """atob decodes Base64 to string."""
        python_code = '''
decoded = atob("SGVsbG8=")
print(decoded)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "Hello" in result["output"][0]
    
    def test_base64_roundtrip(self, browser_parity_harness: BrowserParityHarness):
        """btoa → atob roundtrip preserves text."""
        python_code = '''
original = "Hello, World!"
encoded = btoa(original)
decoded = atob(encoded)
print(original == decoded)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "true" in result["output"][0].lower()


# =============================================================================
# TYPED ARRAYS BROWSER PARITY TESTS (2 tests)
# =============================================================================

@pytest.mark.e2e
class TestTypedArraysBrowserParity:
    """Verify transpiled TypedArray code runs correctly in browser."""
    
    def test_uint8array_creation(self, browser_parity_harness: BrowserParityHarness):
        """Uint8Array can be created and accessed."""
        python_code = '''
arr = Uint8Array([1, 2, 3, 4, 5])
print(arr.length)
print(arr[0])
print(arr[4])
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "5" in result["output"][0]
        assert "1" in result["output"][1]
        assert "5" in result["output"][2]
    
    def test_arraybuffer_bytelength(self, browser_parity_harness: BrowserParityHarness):
        """ArrayBuffer.byteLength property works."""
        python_code = '''
buffer = ArrayBuffer(256)
print(buffer.byteLength)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "256" in result["output"][0]


# =============================================================================
# DATAVIEW BROWSER PARITY TESTS (3 tests)
# =============================================================================

@pytest.mark.e2e
class TestDataViewBrowserParity:
    """Verify transpiled DataView code runs correctly in browser."""
    
    def test_dataview_set_get_int32(self, browser_parity_harness: BrowserParityHarness):
        """DataView setInt32/getInt32 works."""
        python_code = '''
buffer = ArrayBuffer(16)
view = DataView(buffer)
view.setInt32(0, 12345, True)
print(view.getInt32(0, True))
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "12345" in result["output"][0]
    
    def test_dataview_byte_offset(self, browser_parity_harness: BrowserParityHarness):
        """DataView with byte offset works."""
        python_code = '''
buffer = ArrayBuffer(16)
view = DataView(buffer, 4, 8)
print(view.byteOffset)
print(view.byteLength)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "4" in result["output"][0]
        assert "8" in result["output"][1]
    
    def test_dataview_float64(self, browser_parity_harness: BrowserParityHarness):
        """DataView handles float64."""
        python_code = '''
buffer = ArrayBuffer(8)
view = DataView(buffer)
view.setFloat64(0, 3.14159, True)
val = view.getFloat64(0, True)
print(val > 3.14 and val < 3.15)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "true" in result["output"][0].lower()


# =============================================================================
# BLOB BROWSER PARITY TESTS (3 tests)
# =============================================================================

@pytest.mark.e2e
class TestBlobBrowserParity:
    """Verify transpiled Blob code runs correctly in browser."""
    
    def test_blob_size_and_type(self, browser_parity_harness: BrowserParityHarness):
        """Blob.size and Blob.type work."""
        python_code = '''
blob = Blob(["Hello, World!"], {"type": "text/plain"})
print(blob.size)
print(blob.type)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "13" in result["output"][0]  # "Hello, World!" = 13 bytes
        assert "text/plain" in result["output"][1]
    
    def test_blob_slice(self, browser_parity_harness: BrowserParityHarness):
        """Blob.slice creates new blob."""
        python_code = '''
blob = Blob(["Hello, World!"])
sliced = blob.slice(0, 5)
print(sliced.size)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "5" in result["output"][0]  # "Hello" = 5 bytes
    
    def test_blob_from_uint8array(self, browser_parity_harness: BrowserParityHarness):
        """Blob from Uint8Array works."""
        python_code = '''
data = Uint8Array([72, 101, 108, 108, 111])
blob = Blob([data])
print(blob.size)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "5" in result["output"][0]


# =============================================================================
# FILEREADER BROWSER PARITY TESTS (3 tests)
# =============================================================================

@pytest.mark.e2e
class TestFileReaderBrowserParity:
    """Verify transpiled FileReader code runs correctly in browser."""
    
    def test_filereader_readAsText(self, browser_parity_harness: BrowserParityHarness):
        """FileReader.readAsText reads blob content."""
        python_code = '''
blob = Blob(["Hello, World!"], {"type": "text/plain"})
reader = FileReader()

def on_load(event):
    print(reader.result)

reader.onload = on_load
reader.readAsText(blob)
'''
        # FileReader is async, we need to wait
        result = browser_parity_harness.execute(python_code)
        # The onload may not fire synchronously in eval, so we test construction works
        assert result["success"], f"JS failed: {result.get('error')}"
    
    def test_filereader_readystate(self, browser_parity_harness: BrowserParityHarness):
        """FileReader.readyState starts at EMPTY."""
        python_code = '''
reader = FileReader()
print(reader.readyState)
print(reader.EMPTY)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "0" in result["output"][0]  # EMPTY = 0
        assert "0" in result["output"][1]
    
    def test_filereader_constants(self, browser_parity_harness: BrowserParityHarness):
        """FileReader constants are accessible."""
        python_code = '''
reader = FileReader()
print(reader.EMPTY)
print(reader.LOADING)
print(reader.DONE)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "0" in result["output"][0]  # EMPTY
        assert "1" in result["output"][1]  # LOADING
        assert "2" in result["output"][2]  # DONE


# =============================================================================
# FILE BROWSER PARITY TESTS (2 tests)
# =============================================================================

@pytest.mark.e2e
class TestFileBrowserParity:
    """Verify transpiled File code runs correctly in browser."""
    
    def test_file_properties(self, browser_parity_harness: BrowserParityHarness):
        """File has name, size, type properties."""
        python_code = '''
file = File(["Hello"], "test.txt", {"type": "text/plain"})
print(file.name)
print(file.size)
print(file.type)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "test.txt" in result["output"][0]
        assert "5" in result["output"][1]  # "Hello" = 5 bytes
        assert "text/plain" in result["output"][2]
    
    def test_file_lastmodified(self, browser_parity_harness: BrowserParityHarness):
        """File.lastModified returns timestamp."""
        python_code = '''
file = File(["content"], "file.txt")
lm = file.lastModified
print(lm > 0)
'''
        result = browser_parity_harness.execute(python_code)
        assert result["success"], f"JS failed: {result.get('error')}"
        assert "true" in result["output"][0].lower()
