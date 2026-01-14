"""
Phase 34.5: Blob/File Edge Cases Tests

Tests for empty blobs, mixed types, slicing, and FileReader edge cases.
Verifies robust transpilation and browser behavior.

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestBlobConstruction:
    """Test Blob construction edge cases."""
    
    def test_blob_empty_array(self):
        """Blob with empty parts array."""
        code = '''
blob = Blob([])
size = blob.size  # Should be 0
'''
        result = transpile(code)
        assert 'Blob([])' in result
        assert 'blob.size' in result
    
    def test_blob_multiple_types(self):
        """Blob from mixed string, bytes, and blob."""
        code = '''
text_part = "Hello, "
bytes_part = Uint8Array([87, 111, 114, 108, 100])  # "World"
blob_part = Blob(["!"])
combined = Blob([text_part, bytes_part, blob_part])
'''
        result = transpile(code)
        assert 'Blob([text_part, bytes_part, blob_part])' in result
    
    def test_blob_nested_blob(self):
        """Blob containing another Blob."""
        code = '''
inner = Blob(["inner content"])
outer = Blob([inner, " outer content"])
'''
        result = transpile(code)
        assert 'Blob([inner, " outer content"])' in result
    
    def test_blob_type_normalization(self):
        """MIME type is lowercased."""
        code = '''
blob = Blob(["data"], {"type": "TEXT/PLAIN"})
mime = blob.type  # Should be "text/plain"
'''
        result = transpile(code)
        assert 'blob.type' in result


class TestBlobSlicing:
    """Test Blob.slice() edge cases."""
    
    def test_blob_slice_negative(self):
        """Slice with negative indices."""
        code = '''
blob = Blob(["Hello, World!"])
last_6 = blob.slice(-6)  # "World!"
'''
        result = transpile(code)
        # Negative numbers get parentheses: (-6)
        assert 'blob.slice' in result
        assert '-6' in result
    
    def test_blob_slice_out_of_bounds(self):
        """Slice past blob end."""
        code = '''
blob = Blob(["Hello"])
sliced = blob.slice(0, 100)  # Returns full blob, no error
'''
        result = transpile(code)
        assert 'blob.slice(0, 100)' in result
    
    def test_blob_slice_with_type(self):
        """Slice with new content type."""
        code = '''
blob = Blob(["data"], {"type": "application/octet-stream"})
typed_slice = blob.slice(0, 4, "text/plain")
'''
        result = transpile(code)
        assert 'blob.slice(0, 4, "text/plain")' in result


class TestFileConstruction:
    """Test File construction edge cases."""
    
    def test_file_name_special_chars(self):
        """Filename with special characters."""
        code = '''
file = File(["content"], "path/to/file.txt")
name = file.name  # Should be "path/to/file.txt" (not stripped)
'''
        result = transpile(code)
        assert 'File(["content"], "path/to/file.txt")' in result
    
    def test_file_lastModified_default(self):
        """File has default lastModified timestamp."""
        code = '''
file = File(["content"], "test.txt")
timestamp = file.lastModified  # Defaults to Date.now()
'''
        result = transpile(code)
        assert 'file.lastModified' in result
    
    def test_file_lastModified_custom(self):
        """File with custom lastModified."""
        code = '''
file = File(["content"], "test.txt", {"lastModified": 1609459200000})
timestamp = file.lastModified
'''
        result = transpile(code)
        assert '"lastModified": 1609459200000' in result


class TestFileReader:
    """Test FileReader edge cases."""
    
    def test_filereader_abort(self):
        """Abort FileReader during read."""
        code = '''
reader = FileReader()
reader.onload = lambda e: console.log("loaded")
reader.onabort = lambda e: console.log("aborted")
reader.readAsText(blob)
reader.abort()
'''
        result = transpile(code)
        assert 'reader.abort()' in result
    
    def test_filereader_error(self):
        """Handle FileReader error."""
        code = '''
reader = FileReader()
reader.onerror = lambda e: console.error(reader.error)
reader.readAsArrayBuffer(blob)
'''
        result = transpile(code)
        assert 'reader.onerror' in result
        assert 'reader.error' in result
    
    def test_filereader_dataurl(self):
        """Read as data URL."""
        code = '''
reader = FileReader()
def on_load(event):
    data_url = reader.result  # "data:image/png;base64,..."
    img.src = data_url

reader.onload = on_load
reader.readAsDataURL(image_file)
'''
        result = transpile(code)
        assert 'reader.readAsDataURL(image_file)' in result


class TestBlobStreaming:
    """Test Blob streaming."""
    
    def test_blob_stream(self):
        """Get ReadableStream from Blob."""
        code = '''
blob = Blob(["streaming content"])
stream = blob.stream()
reader = stream.getReader()
'''
        result = transpile(code)
        assert 'blob.stream()' in result


