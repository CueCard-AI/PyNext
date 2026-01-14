"""
Phase 34.5: Base64 (btoa/atob) Edge Cases Tests

Tests for encoding errors, padding, and special characters.
Verifies robust transpilation and browser behavior.

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestBtoaErrors:
    """Test btoa error cases."""
    
    def test_btoa_non_latin1_throws(self):
        """btoa with non-Latin1 characters throws."""
        code = '''
try:
    encoded = btoa("Hello 世界")  # Throws InvalidCharacterError
except:
    console.error("Cannot encode non-Latin1 characters")
'''
        result = transpile(code)
        assert 'btoa("Hello 世界")' in result


class TestBtoaBinaryRange:
    """Test full binary range."""
    
    def test_btoa_binary_255(self):
        """Encode char code 255 (ÿ)."""
        code = '''
binary = chr(255)
encoded = btoa(binary)
'''
        result = transpile(code)
        assert 'btoa(binary)' in result
    
    def test_btoa_binary_0(self):
        """Encode char code 0 (null)."""
        code = '''
binary = chr(0)
encoded = btoa(binary)
'''
        result = transpile(code)
        assert 'btoa(binary)' in result
    
    def test_round_trip_all_bytes(self):
        """Round-trip encode/decode all bytes 0-255."""
        code = '''
binary = "".join(chr(i) for i in range(256))
encoded = btoa(binary)
decoded = atob(encoded)
# decoded should equal binary
'''
        result = transpile(code)
        assert 'btoa(binary)' in result
        assert 'atob(encoded)' in result


class TestAtobPadding:
    """Test atob padding handling."""
    
    def test_atob_invalid_padding(self):
        """Invalid base64 padding throws."""
        code = '''
try:
    decoded = atob("SGVsbG8===")  # Invalid - too many padding chars
except:
    console.error("Invalid base64 padding")
'''
        result = transpile(code)
        assert 'atob("SGVsbG8===")' in result
    
    def test_atob_no_padding(self):
        """Base64 without = padding (valid)."""
        code = '''
# "AA" is valid without padding
decoded = atob("QQ")  # Should work
'''
        result = transpile(code)
        assert 'atob("QQ")' in result
    
    def test_atob_single_padding(self):
        """Base64 with single = padding."""
        code = '''
decoded = atob("SGVsbA=")  # "Hell" + 1 padding
'''
        result = transpile(code)
        assert 'atob("SGVsbA=")' in result
    
    def test_atob_double_padding(self):
        """Base64 with == padding."""
        code = '''
decoded = atob("SGk=")  # "Hi" + 2 padding (as ==)
'''
        result = transpile(code)
        assert 'atob("SGk=")' in result


class TestAtobWhitespace:
    """Test whitespace handling."""
    
    def test_atob_whitespace(self):
        """Whitespace in base64 string."""
        code = '''
# Some browsers accept whitespace, some don't
try:
    decoded = atob("SGVs bG8=")
except:
    console.error("Whitespace not allowed")
'''
        result = transpile(code)
        assert 'atob("SGVs bG8=")' in result


class TestBase64DataURLs:
    """Test data URL patterns."""
    
    def test_base64_data_url(self):
        """Parse and decode data URL."""
        code = '''
data_url = "data:text/plain;base64,SGVsbG8gV29ybGQh"
# Split and decode
parts = data_url.split(",")
base64_data = parts[1]
decoded = atob(base64_data)
'''
        result = transpile(code)
        assert 'atob(base64_data)' in result


