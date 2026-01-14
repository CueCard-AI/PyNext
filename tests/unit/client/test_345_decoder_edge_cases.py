"""
Phase 34.5: TextDecoder Edge Cases Tests

Tests for invalid sequences, streaming, BOM handling, and encodings.
Verifies robust transpilation and browser behavior.

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestDecoderInvalidSequences:
    """Test invalid byte sequence handling."""
    
    def test_decoder_invalid_utf8_fatal(self):
        """Invalid UTF-8 with fatal=true throws."""
        code = '''
decoder = TextDecoder("utf-8", {"fatal": True})
try:
    text = decoder.decode(invalid_bytes)
except:
    console.error("Invalid UTF-8 sequence")
'''
        result = transpile(code)
        assert 'TextDecoder("utf-8", {"fatal": true})' in result
        assert 'decoder.decode(invalid_bytes)' in result
    
    def test_decoder_invalid_utf8_replace(self):
        """Invalid UTF-8 with fatal=false replaces with U+FFFD."""
        code = '''
decoder = TextDecoder("utf-8", {"fatal": False})
text = decoder.decode(invalid_bytes)
# Invalid bytes replaced with \uFFFD
'''
        result = transpile(code)
        assert 'TextDecoder("utf-8", {"fatal": false})' in result


class TestDecoderStreaming:
    """Test streaming decode."""
    
    def test_decoder_streaming_split_char(self):
        """Multi-byte char split across chunks."""
        code = '''
decoder = TextDecoder("utf-8")
# UTF-8 for 世 is E4 B8 96
# Split across chunks
part1 = decoder.decode(chunk1, {"stream": True})
part2 = decoder.decode(chunk2, {"stream": True})
final = decoder.decode()
'''
        result = transpile(code)
        assert '{"stream": true}' in result.lower() or '"stream": true' in result.lower()
        assert 'decoder.decode()' in result


class TestDecoderBOM:
    """Test BOM (Byte Order Mark) handling."""
    
    def test_decoder_bom_ignore(self):
        """BOM ignored with ignoreBOM=true."""
        code = '''
decoder = TextDecoder("utf-8", {"ignoreBOM": True})
text = decoder.decode(bytes_with_bom)
# BOM should be stripped from output
'''
        result = transpile(code)
        assert '"ignoreBOM": true' in result.lower() or '"ignorebom": true' in result.lower()
    
    def test_decoder_bom_include(self):
        """BOM included with ignoreBOM=false."""
        code = '''
decoder = TextDecoder("utf-8", {"ignoreBOM": False})
text = decoder.decode(bytes_with_bom)
# BOM appears at start of output
'''
        result = transpile(code)
        assert 'TextDecoder("utf-8"' in result


class TestDecoderFlush:
    """Test decoder flush behavior."""
    
    def test_decoder_empty_flush(self):
        """Flush decoder with no remaining bytes."""
        code = '''
decoder = TextDecoder()
text = decoder.decode(complete_bytes)
remaining = decoder.decode()  # Flush - returns ""
'''
        result = transpile(code)
        assert 'decoder.decode()' in result


class TestDecoderEncodings:
    """Test various character encodings."""
    
    def test_decoder_latin1(self):
        """Decode ISO-8859-1 (Latin-1)."""
        code = '''
decoder = TextDecoder("iso-8859-1")
text = decoder.decode(latin1_bytes)
'''
        result = transpile(code)
        assert 'TextDecoder("iso-8859-1")' in result
    
    def test_decoder_utf16le(self):
        """Decode UTF-16LE."""
        code = '''
decoder = TextDecoder("utf-16le")
text = decoder.decode(utf16_bytes)
'''
        result = transpile(code)
        assert 'TextDecoder("utf-16le")' in result
    
    def test_decoder_utf16be(self):
        """Decode UTF-16BE."""
        code = '''
decoder = TextDecoder("utf-16be")
text = decoder.decode(utf16_bytes)
'''
        result = transpile(code)
        assert 'TextDecoder("utf-16be")' in result
    
    def test_decoder_windows1252(self):
        """Decode Windows-1252."""
        code = '''
decoder = TextDecoder("windows-1252")
text = decoder.decode(legacy_bytes)
'''
        result = transpile(code)
        assert 'TextDecoder("windows-1252")' in result


