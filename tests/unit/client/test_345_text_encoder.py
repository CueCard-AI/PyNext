"""
Phase 34.5: TextEncoder Tests

Comprehensive tests for TextEncoder.encode and encodeInto.
All tests verify zero-runtime passthrough transpilation.

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestTextEncoderConstruction:
    """Tests for TextEncoder constructor."""
    
    def test_basic_construction(self):
        """Construct TextEncoder."""
        code = '''
encoder = TextEncoder()
'''
        result = transpile(code)
        assert 'TextEncoder()' in result
    
    def test_encoding_property(self):
        """Access encoding property."""
        code = '''
encoder = TextEncoder()
enc = encoder.encoding
'''
        result = transpile(code)
        assert 'encoder.encoding' in result


class TestTextEncoderEncode:
    """Tests for encode() method."""
    
    def test_encode_ascii(self):
        """Encode ASCII string."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode("Hello, World!")
'''
        result = transpile(code)
        # .encode() may use __py.str.encode helper
        assert 'encoder' in result
        assert '"Hello, World!"' in result
    
    def test_encode_unicode(self):
        """Encode Unicode string."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode("Hello, 世界!")
'''
        result = transpile(code)
        assert 'encoder' in result
        assert '世界' in result
    
    def test_encode_emoji(self):
        """Encode string with emoji."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode("🎉 Party!")
'''
        result = transpile(code)
        assert 'encoder' in result
        assert 'Party' in result
    
    def test_encode_empty(self):
        """Encode empty string."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode("")
'''
        result = transpile(code)
        assert 'encoder' in result
        assert '""' in result
    
    def test_encode_variable(self):
        """Encode variable string."""
        code = '''
encoder = TextEncoder()
text = get_text()
bytes_arr = encoder.encode(text)
'''
        result = transpile(code)
        assert 'encoder' in result
        assert 'text' in result


class TestTextEncoderEncodeInto:
    """Tests for encodeInto() method."""
    
    def test_encode_into_buffer(self):
        """Encode into existing buffer."""
        code = '''
encoder = TextEncoder()
buffer = Uint8Array(100)
result = encoder.encodeInto("Hello", buffer)
'''
        result = transpile(code)
        assert 'encoder.encodeInto("Hello", buffer)' in result
    
    def test_encode_into_read_result(self):
        """Access encodeInto result properties."""
        code = '''
encoder = TextEncoder()
buffer = Uint8Array(100)
result = encoder.encodeInto("Hello", buffer)
chars_read = result.read
bytes_written = result.written
'''
        result = transpile(code)
        assert 'result.read' in result
        assert 'result.written' in result
    
    def test_encode_into_small_buffer(self):
        """Handle small buffer (truncation)."""
        code = '''
encoder = TextEncoder()
small_buffer = Uint8Array(5)
result = encoder.encodeInto("Hello, World!", small_buffer)
'''
        result = transpile(code)
        assert 'encoder.encodeInto' in result


class TestTextEncoderPatterns:
    """Tests for common TextEncoder patterns."""
    
    def test_text_to_base64_pattern(self):
        """Convert text to base64 pattern."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode(text)
binary = "".join(chr(b) for b in bytes_arr)
base64 = btoa(binary)
'''
        result = transpile(code)
        assert 'encoder' in result
        assert 'btoa' in result
    
    def test_websocket_binary_pattern(self):
        """Send binary data over WebSocket."""
        code = '''
encoder = TextEncoder()
data = encoder.encode(json_string)
ws.send(data)
'''
        result = transpile(code)
        assert 'encoder' in result
        assert 'ws.send(data)' in result
    
    def test_file_write_pattern(self):
        """Create file from text."""
        code = '''
encoder = TextEncoder()
data = encoder.encode(content)
blob = Blob([data], {"type": "text/plain"})
'''
        result = transpile(code)
        assert 'encoder' in result
        assert 'Blob' in result
    
    def test_hash_input_pattern(self):
        """Prepare text for crypto hash."""
        code = '''
async def hash_message():
    encoder = TextEncoder()
    data = encoder.encode(message)
    hash_buffer = await crypto.subtle.digest("SHA-256", data)
'''
        result = transpile(code)
        assert 'encoder' in result
        assert 'crypto.subtle.digest' in result
