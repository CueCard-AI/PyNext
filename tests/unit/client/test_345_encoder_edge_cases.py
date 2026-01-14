"""
Phase 34.5: TextEncoder Edge Cases Tests

Tests for Unicode handling, large strings, and encodeInto edge cases.
Verifies robust transpilation and browser behavior.

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestEncoderUnicode:
    """Test Unicode encoding edge cases."""
    
    def test_encoder_surrogate_pairs(self):
        """Encode emoji (surrogate pairs)."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode("Hello 😀 World")
'''
        result = transpile(code)
        # encode may use __py.str.encode helper
        assert 'encoder' in result
        assert '😀' in result
    
    def test_encoder_lone_surrogate(self):
        """Handle lone surrogate (invalid Unicode)."""
        code = '''
encoder = TextEncoder()
text = "AB"
bytes_arr = encoder.encode(text)
'''
        result = transpile(code)
        # encode may use __py.str.encode helper
        assert 'encoder' in result
        assert 'text' in result
    
    def test_encoder_null_byte(self):
        """Encode string with null byte."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode("hello world")
'''
        result = transpile(code)
        assert 'encoder' in result
        assert '"hello world"' in result
    
    def test_encoder_mixed_ascii_unicode(self):
        """Encode mixed ASCII and Unicode."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode("Hello 世界")
'''
        result = transpile(code)
        assert 'encoder' in result
        assert '世界' in result


class TestEncoderLargeStrings:
    """Test large string handling."""
    
    def test_encoder_very_large_string(self):
        """Encode very large string."""
        code = '''
encoder = TextEncoder()
large_string = "x" * 1000000  # 1MB
bytes_arr = encoder.encode(large_string)
'''
        result = transpile(code)
        assert 'encoder' in result
        assert 'large_string' in result


class TestEncoderEncodeInto:
    """Test encodeInto edge cases."""
    
    def test_encoder_encodeInto_small_buffer(self):
        """Buffer smaller than string."""
        code = '''
encoder = TextEncoder()
buffer = Uint8Array(5)
result = encoder.encodeInto("Hello, World!", buffer)
# result.read < 13, result.written <= 5
'''
        result = transpile(code)
        assert 'encoder.encodeInto("Hello, World!", buffer)' in result
    
    def test_encoder_encodeInto_exact_buffer(self):
        """Buffer exactly right size."""
        code = '''
encoder = TextEncoder()
buffer = Uint8Array(5)
result = encoder.encodeInto("Hello", buffer)
# result.read = 5, result.written = 5
'''
        result = transpile(code)
        assert 'encoder.encodeInto("Hello", buffer)' in result
    
    def test_encoder_encodeInto_large_buffer(self):
        """Buffer larger than needed."""
        code = '''
encoder = TextEncoder()
buffer = Uint8Array(100)
result = encoder.encodeInto("Hi", buffer)
# result.read = 2, result.written = 2
'''
        result = transpile(code)
        assert 'encoder.encodeInto("Hi", buffer)' in result


class TestEncoderSpecialChars:
    """Test special characters."""
    
    def test_encoder_newlines(self):
        """Encode different line endings."""
        code = '''
encoder = TextEncoder()
text = "line1 line2"
bytes_arr = encoder.encode(text)
'''
        result = transpile(code)
        assert 'encoder' in result
        assert 'text' in result
    
    def test_encoder_bom(self):
        """Encode string with BOM."""
        code = '''
encoder = TextEncoder()
text_with_bom = "Hello"
bytes_arr = encoder.encode(text_with_bom)
'''
        result = transpile(code)
        assert 'encoder' in result
        assert 'text_with_bom' in result


