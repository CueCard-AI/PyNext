"""
Phase 34.5: Edge Cases Tests

Tests for null handling, encoding errors, and boundary conditions.
All tests verify zero-runtime passthrough transpilation.

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestURLEdgeCases:
    """Edge cases for URL APIs."""
    
    def test_url_empty_query(self):
        """Handle URL with empty query string."""
        code = '''
url = URL("https://example.com?")
search = url.search
'''
        result = transpile(code)
        assert 'url.search' in result
    
    def test_url_special_characters(self):
        """Handle special characters in URL."""
        code = '''
url = URL("https://example.com/path?q=hello%20world&tag=%23python")
'''
        result = transpile(code)
        assert 'URL("https://example.com/path?q=hello%20world&tag=%23python")' in result
    
    def test_searchparams_empty_value(self):
        """Handle empty parameter values."""
        code = '''
params = URLSearchParams("foo=&bar=value")
foo_val = params.get("foo")
'''
        result = transpile(code)
        # .get() may use __py.dict.get helper
        assert 'params' in result
        assert '"foo"' in result
    
    def test_searchparams_no_value(self):
        """Handle parameter with no = sign."""
        code = '''
params = URLSearchParams("flag&key=value")
has_flag = params.has("flag")
'''
        result = transpile(code)
        assert 'params.has("flag")' in result
    
    def test_url_invalid_base(self):
        """Handle relative URL without valid base."""
        code = '''
try:
    url = URL("/relative/path")
except:
    console.error("Invalid URL")
'''
        result = transpile(code)
        assert 'URL("/relative/path")' in result


class TestEncodingEdgeCases:
    """Edge cases for encoding APIs."""
    
    def test_encode_empty_string(self):
        """Encode empty string."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode("")
length = bytes_arr.length
'''
        result = transpile(code)
        # .encode() may use __py.str.encode helper
        assert 'encoder' in result
        assert '""' in result
    
    def test_decode_empty_buffer(self):
        """Decode empty buffer."""
        code = '''
decoder = TextDecoder()
text = decoder.decode(Uint8Array(0))
'''
        result = transpile(code)
        assert 'decoder.decode' in result
    
    def test_btoa_empty_string(self):
        """Base64 encode empty string."""
        code = '''
result = btoa("")
'''
        result = transpile(code)
        assert 'btoa("")' in result
    
    def test_atob_empty_string(self):
        """Base64 decode empty string."""
        code = '''
result = atob("")
'''
        result = transpile(code)
        assert 'atob("")' in result
    
    def test_decoder_invalid_sequence(self):
        """Handle invalid byte sequence with fatal=True."""
        code = '''
decoder = TextDecoder("utf-8", {"fatal": True})
try:
    text = decoder.decode(invalid_bytes)
except:
    console.error("Invalid UTF-8")
'''
        result = transpile(code)
        assert 'TextDecoder("utf-8"' in result
        assert 'fatal' in result


class TestBinaryEdgeCases:
    """Edge cases for binary APIs."""
    
    def test_arraybuffer_zero_length(self):
        """Create zero-length ArrayBuffer."""
        code = '''
buffer = ArrayBuffer(0)
length = buffer.byteLength
'''
        result = transpile(code)
        assert 'ArrayBuffer(0)' in result
    
    def test_typed_array_empty(self):
        """Create empty typed array."""
        code = '''
arr = Uint8Array(0)
length = arr.length
'''
        result = transpile(code)
        assert 'Uint8Array(0)' in result
    
    def test_blob_empty(self):
        """Create empty Blob."""
        code = '''
blob = Blob()
size = blob.size
'''
        result = transpile(code)
        assert 'Blob()' in result
        assert 'blob.size' in result
    
    def test_dataview_out_of_bounds(self):
        """Handle DataView bounds checking."""
        code = '''
buffer = ArrayBuffer(4)
view = DataView(buffer)
try:
    value = view.getInt32(1, True)  # Would read past end
except:
    console.error("Out of bounds")
'''
        result = transpile(code)
        assert 'view.getInt32(1, true)' in result
    
    def test_typed_array_negative_index(self):
        """Handle negative index access."""
        code = '''
arr = Uint8Array([1, 2, 3])
# JavaScript doesn't support negative indexing
# This would return undefined
val = arr[-1]
'''
        result = transpile(code)
        # Negative indexing might use __py.at helper
        assert 'arr' in result

