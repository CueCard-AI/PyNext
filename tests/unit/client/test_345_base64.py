"""
Phase 34.5: Base64 (btoa/atob) Tests

Comprehensive tests for base64 encoding and decoding.
All tests verify zero-runtime passthrough transpilation.

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestBtoa:
    """Tests for btoa (binary to ASCII/base64)."""
    
    def test_btoa_ascii(self):
        """Encode ASCII string."""
        code = '''
encoded = btoa("Hello, World!")
'''
        result = transpile(code)
        assert 'btoa("Hello, World!")' in result
        assert '__py.' not in result
    
    def test_btoa_variable(self):
        """Encode variable string."""
        code = '''
data = get_data()
encoded = btoa(data)
'''
        result = transpile(code)
        assert 'btoa(data)' in result
    
    def test_btoa_binary_chars(self):
        """Encode binary string (0-255 chars)."""
        code = '''
# Binary string from bytes
binary = "".join(chr(b) for b in bytes_array)
encoded = btoa(binary)
'''
        result = transpile(code)
        assert 'btoa(binary)' in result


class TestAtob:
    """Tests for atob (ASCII/base64 to binary)."""
    
    def test_atob_decode(self):
        """Decode base64 string."""
        code = '''
decoded = atob("SGVsbG8sIFdvcmxkIQ==")
'''
        result = transpile(code)
        assert 'atob("SGVsbG8sIFdvcmxkIQ==")' in result
    
    def test_atob_variable(self):
        """Decode variable string."""
        code = '''
base64 = get_base64()
decoded = atob(base64)
'''
        result = transpile(code)
        assert 'atob(base64)' in result
    
    def test_atob_to_bytes(self):
        """Convert atob result to bytes."""
        code = '''
binary = atob(base64_string)
bytes_arr = Uint8Array([ord(c) for c in binary])
'''
        result = transpile(code)
        assert 'atob(base64_string)' in result


class TestBase64Patterns:
    """Tests for common base64 patterns."""
    
    def test_unicode_to_base64_pattern(self):
        """Encode Unicode string to base64."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode("Hello, 世界!")
binary = "".join(chr(b) for b in bytes_arr)
base64 = btoa(binary)
'''
        result = transpile(code)
        # .encode() may use __py.str.encode helper
        assert 'encoder' in result
        assert 'btoa(binary)' in result
    
    def test_base64_to_unicode_pattern(self):
        """Decode base64 to Unicode string."""
        code = '''
binary = atob(base64_string)
bytes_arr = Uint8Array([ord(c) for c in binary])
decoder = TextDecoder()
text = decoder.decode(bytes_arr)
'''
        result = transpile(code)
        assert 'atob(base64_string)' in result
        assert 'decoder.decode' in result
    
    def test_data_url_pattern(self):
        """Create data URL."""
        code = '''
base64 = btoa(svg_content)
data_url = f"data:image/svg+xml;base64,{base64}"
'''
        result = transpile(code)
        assert 'btoa(svg_content)' in result
    
    def test_image_base64_pattern(self):
        """Decode base64 image data."""
        code = '''
base64_data = image_url.split(",")[1]
binary = atob(base64_data)
bytes_arr = Uint8Array([ord(c) for c in binary])
blob = Blob([bytes_arr], {"type": "image/png"})
'''
        result = transpile(code)
        assert 'atob(base64_data)' in result
        assert 'Blob' in result

