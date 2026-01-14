"""
Phase 34.5: Streaming TextDecoder Tests

Tests for the streaming decode pattern for chunked data.

Total: 5 tests

WHO: Developers processing chunked binary data
WHAT: Streaming TextDecoder for incremental decoding
WHEN: Processing large files, WebSocket streams, fetch responses
WHERE: Client-side transpiled code
WHY: Complete Phase 34.5 coverage
HOW: Direct passthrough to native TextDecoder streaming API
"""

import pytest
from pynext.transpiler import transpile


class TestStreamingTextDecoder:
    """Tests for streaming TextDecoder usage."""

    def test_streaming_option(self):
        """TextDecoder with stream option should emit correctly."""
        code = 'decoder = TextDecoder("utf-8", {"stream": True})'
        result = transpile(code)
        assert 'new TextDecoder("utf-8"' in result
        assert '"stream": true' in result or '"stream":true' in result

    def test_decode_with_stream_flag(self):
        """decode() with stream option should pass through."""
        code = '''
decoder = TextDecoder("utf-8")
text = decoder.decode(chunk, {"stream": True})
'''
        result = transpile(code)
        assert 'decoder.decode(chunk' in result
        assert '"stream": true' in result or '"stream":true' in result

    def test_decode_flush(self):
        """decode() with no args to flush should pass through."""
        code = '''
decoder = TextDecoder("utf-8")
final = decoder.decode()
'''
        result = transpile(code)
        assert 'decoder.decode()' in result

    def test_multibyte_streaming_pattern(self):
        """Full streaming pattern for multibyte characters."""
        code = '''
decoder = TextDecoder("utf-8")
chunk1 = decoder.decode(first_bytes, {"stream": True})
chunk2 = decoder.decode(second_bytes, {"stream": True})
final = decoder.decode()
result = chunk1 + chunk2 + final
'''
        result = transpile(code)
        # All decode calls should be passthrough
        assert 'decoder.decode(first_bytes' in result
        assert 'decoder.decode(second_bytes' in result
        assert 'decoder.decode()' in result

    def test_streaming_decode_sequence(self):
        """Complete streaming decode sequence in function."""
        code = '''
def process_stream(chunks):
    decoder = TextDecoder("utf-8")
    result = ""
    for chunk in chunks:
        result = result + decoder.decode(chunk, {"stream": True})
    result = result + decoder.decode()
    return result
'''
        result = transpile(code)
        assert 'new TextDecoder("utf-8")' in result
        assert 'decoder.decode(chunk' in result
        assert 'decoder.decode()' in result

