"""
Phase 34.5: Blob and File Tests

Comprehensive tests for Blob construction and methods.
All tests verify zero-runtime passthrough transpilation.

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestBlobConstruction:
    """Tests for Blob constructor."""
    
    def test_blob_from_string(self):
        """Construct Blob from string."""
        code = '''
blob = Blob(["Hello, World!"], {"type": "text/plain"})
'''
        result = transpile(code)
        assert 'Blob(["Hello, World!"]' in result
    
    def test_blob_from_bytes(self):
        """Construct Blob from Uint8Array."""
        code = '''
data = Uint8Array([0x89, 0x50, 0x4E, 0x47])
blob = Blob([data], {"type": "image/png"})
'''
        result = transpile(code)
        assert 'Blob([data]' in result
    
    def test_blob_multiple_parts(self):
        """Construct Blob from multiple parts."""
        code = '''
blob = Blob([header, body, footer], {"type": "application/octet-stream"})
'''
        result = transpile(code)
        assert 'Blob([header, body, footer]' in result
    
    def test_blob_empty(self):
        """Construct empty Blob."""
        code = '''
blob = Blob()
'''
        result = transpile(code)
        assert 'Blob()' in result


class TestBlobProperties:
    """Tests for Blob properties."""
    
    def test_blob_size(self):
        """Access size property."""
        code = '''
blob = Blob(["Hello"])
size = blob.size
'''
        result = transpile(code)
        assert 'blob.size' in result
    
    def test_blob_type(self):
        """Access type property."""
        code = '''
blob = Blob(["data"], {"type": "text/csv"})
mime = blob.type
'''
        result = transpile(code)
        assert 'blob.type' in result


class TestBlobMethods:
    """Tests for Blob methods."""
    
    def test_blob_slice(self):
        """Slice blob."""
        code = '''
blob = Blob(["Hello, World!"])
first_five = blob.slice(0, 5)
'''
        result = transpile(code)
        assert 'blob.slice(0, 5)' in result
    
    def test_blob_text(self):
        """Read blob as text."""
        code = '''
async def read_blob():
    text = await blob.text()
    return text
'''
        result = transpile(code)
        assert 'blob.text()' in result
    
    def test_blob_arrayBuffer(self):
        """Read blob as ArrayBuffer."""
        code = '''
async def read_blob():
    buffer = await blob.arrayBuffer()
    return buffer
'''
        result = transpile(code)
        assert 'blob.arrayBuffer()' in result


class TestBlobPatterns:
    """Tests for common Blob patterns."""
    
    def test_download_pattern(self):
        """Create downloadable file."""
        code = '''
blob = Blob([csv_content], {"type": "text/csv"})
url = URL.createObjectURL(blob)
a = document.createElement("a")
a.href = url
a.download = "data.csv"
a.click()
URL.revokeObjectURL(url)
'''
        result = transpile(code)
        assert 'Blob([csv_content]' in result
        assert 'URL.createObjectURL(blob)' in result
        assert 'URL.revokeObjectURL(url)' in result

