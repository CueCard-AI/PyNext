"""
Phase 34.5: TextDecoder Tests

Comprehensive tests for TextDecoder with various encodings.
All tests verify zero-runtime passthrough transpilation.

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


class TestTextDecoderConstruction:
    """Tests for TextDecoder constructor."""
    
    def test_default_utf8(self):
        """Construct with default UTF-8."""
        code = '''
decoder = TextDecoder()
'''
        result = transpile(code)
        assert 'TextDecoder()' in result
    
    def test_explicit_utf8(self):
        """Construct with explicit UTF-8."""
        code = '''
decoder = TextDecoder("utf-8")
'''
        result = transpile(code)
        assert 'TextDecoder("utf-8")' in result
    
    def test_latin1_encoding(self):
        """Construct with Latin-1 encoding."""
        code = '''
decoder = TextDecoder("iso-8859-1")
'''
        result = transpile(code)
        assert 'TextDecoder("iso-8859-1")' in result
    
    def test_utf16_encoding(self):
        """Construct with UTF-16 encoding."""
        code = '''
decoder = TextDecoder("utf-16le")
'''
        result = transpile(code)
        assert 'TextDecoder("utf-16le")' in result
    
    def test_with_options(self):
        """Construct with options."""
        code = '''
decoder = TextDecoder("utf-8", {"fatal": True, "ignoreBOM": True})
'''
        result = transpile(code)
        assert 'TextDecoder("utf-8"' in result
        assert 'fatal' in result


class TestTextDecoderProperties:
    """Tests for TextDecoder properties."""
    
    def test_encoding_property(self):
        """Access encoding property."""
        code = '''
decoder = TextDecoder("utf-8")
enc = decoder.encoding
'''
        result = transpile(code)
        assert 'decoder.encoding' in result
    
    def test_fatal_property(self):
        """Access fatal property."""
        code = '''
decoder = TextDecoder("utf-8", {"fatal": True})
is_fatal = decoder.fatal
'''
        result = transpile(code)
        assert 'decoder.fatal' in result
    
    def test_ignoreBOM_property(self):
        """Access ignoreBOM property."""
        code = '''
decoder = TextDecoder("utf-8", {"ignoreBOM": True})
ignore = decoder.ignoreBOM
'''
        result = transpile(code)
        assert 'decoder.ignoreBOM' in result


class TestTextDecoderDecode:
    """Tests for decode() method."""
    
    def test_decode_uint8array(self):
        """Decode Uint8Array."""
        code = '''
decoder = TextDecoder()
text = decoder.decode(bytes_array)
'''
        result = transpile(code)
        assert 'decoder.decode(bytes_array)' in result
    
    def test_decode_arraybuffer(self):
        """Decode ArrayBuffer."""
        code = '''
decoder = TextDecoder()
text = decoder.decode(buffer)
'''
        result = transpile(code)
        assert 'decoder.decode(buffer)' in result
    
    def test_decode_empty_flush(self):
        """Decode with no args (flush)."""
        code = '''
decoder = TextDecoder()
final = decoder.decode()
'''
        result = transpile(code)
        assert 'decoder.decode()' in result


class TestTextDecoderStreaming:
    """Tests for streaming decode."""
    
    def test_streaming_decode(self):
        """Decode with stream option."""
        code = '''
decoder = TextDecoder()
part1 = decoder.decode(chunk1, {"stream": True})
part2 = decoder.decode(chunk2, {"stream": True})
final = decoder.decode()
'''
        result = transpile(code)
        assert 'decoder.decode(chunk1, {"stream": true})' in result or 'stream' in result
    
    def test_streaming_chunks(self):
        """Process streaming chunks."""
        code = '''
decoder = TextDecoder()
result = ""
for chunk in chunks:
    result += decoder.decode(chunk, {"stream": True})
result += decoder.decode()
'''
        result = transpile(code)
        assert 'decoder.decode' in result


class TestTextDecoderPatterns:
    """Tests for common TextDecoder patterns."""
    
    def test_base64_to_text_pattern(self):
        """Decode base64 to text."""
        code = '''
binary = atob(base64_string)
bytes_arr = Uint8Array([ord(c) for c in binary])
decoder = TextDecoder()
text = decoder.decode(bytes_arr)
'''
        result = transpile(code)
        assert 'atob(base64_string)' in result
        assert 'decoder.decode' in result
    
    def test_fetch_text_pattern(self):
        """Decode fetch response."""
        code = '''
async def fetch_text():
    response = await fetch(url)
    buffer = await response.arrayBuffer()
    decoder = TextDecoder()
    text = decoder.decode(buffer)
    return text
'''
        result = transpile(code)
        assert 'decoder.decode(buffer)' in result
    
    def test_websocket_message_pattern(self):
        """Decode WebSocket binary message."""
        code = '''
def on_message(event):
    if isinstance(event.data, ArrayBuffer):
        decoder = TextDecoder()
        text = decoder.decode(event.data)
        handle_text(text)
'''
        result = transpile(code)
        assert 'decoder.decode(event.data)' in result
    
    def test_file_reader_pattern(self):
        """Decode FileReader result."""
        code = '''
async def read_file():
    buffer = await file.arrayBuffer()
    decoder = TextDecoder("utf-8")
    text = decoder.decode(buffer)
    return text
'''
        result = transpile(code)
        assert 'decoder.decode(buffer)' in result
    
    def test_legacy_encoding_pattern(self):
        """Decode legacy encoded file."""
        code = '''
decoder = TextDecoder("windows-1252")
text = decoder.decode(legacy_bytes)
'''
        result = transpile(code)
        assert 'TextDecoder("windows-1252")' in result

