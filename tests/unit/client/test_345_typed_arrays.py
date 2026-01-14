"""
Phase 34.5: TypedArrays Tests

Comprehensive tests for ArrayBuffer and all TypedArray types.
All tests verify zero-runtime passthrough transpilation.

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


class TestArrayBuffer:
    """Tests for ArrayBuffer."""
    
    def test_arraybuffer_construction(self):
        """Construct ArrayBuffer."""
        code = '''
buffer = ArrayBuffer(256)
'''
        result = transpile(code)
        assert 'ArrayBuffer(256)' in result
    
    def test_arraybuffer_byteLength(self):
        """Access byteLength property."""
        code = '''
buffer = ArrayBuffer(100)
size = buffer.byteLength
'''
        result = transpile(code)
        assert 'buffer.byteLength' in result
    
    def test_arraybuffer_slice(self):
        """Slice ArrayBuffer."""
        code = '''
buffer = ArrayBuffer(100)
first_half = buffer.slice(0, 50)
'''
        result = transpile(code)
        assert 'buffer.slice(0, 50)' in result
    
    def test_arraybuffer_isView(self):
        """Check if value is view."""
        code = '''
is_view = ArrayBuffer.isView(arr)
'''
        result = transpile(code)
        assert 'ArrayBuffer.isView(arr)' in result


class TestUint8Array:
    """Tests for Uint8Array."""
    
    def test_uint8_from_length(self):
        """Construct from length."""
        code = '''
arr = Uint8Array(10)
'''
        result = transpile(code)
        assert 'Uint8Array(10)' in result
    
    def test_uint8_from_list(self):
        """Construct from list."""
        code = '''
arr = Uint8Array([1, 2, 3, 4, 5])
'''
        result = transpile(code)
        assert 'Uint8Array' in result
    
    def test_uint8_from_buffer(self):
        """Construct from ArrayBuffer."""
        code = '''
buffer = ArrayBuffer(100)
arr = Uint8Array(buffer)
'''
        result = transpile(code)
        assert 'Uint8Array(buffer)' in result
    
    def test_uint8_with_offset(self):
        """Construct with offset and length."""
        code = '''
buffer = ArrayBuffer(100)
arr = Uint8Array(buffer, 10, 20)
'''
        result = transpile(code)
        assert 'Uint8Array(buffer, 10, 20)' in result
    
    def test_uint8_properties(self):
        """Access TypedArray properties."""
        code = '''
arr = Uint8Array(10)
length = arr.length
byte_length = arr.byteLength
offset = arr.byteOffset
buf = arr.buffer
'''
        result = transpile(code)
        assert 'arr.length' in result
        assert 'arr.byteLength' in result
        assert 'arr.byteOffset' in result
        assert 'arr.buffer' in result


class TestTypedArrayMethods:
    """Tests for TypedArray methods."""
    
    def test_set_method(self):
        """Set values from array."""
        code = '''
arr = Uint8Array(10)
arr.set([1, 2, 3], 0)
'''
        result = transpile(code)
        assert 'arr.set' in result
    
    def test_subarray_method(self):
        """Create subarray (view)."""
        code = '''
arr = Uint8Array(10)
sub = arr.subarray(2, 5)
'''
        result = transpile(code)
        assert 'arr.subarray(2, 5)' in result
    
    def test_slice_method(self):
        """Create slice (copy)."""
        code = '''
arr = Uint8Array(10)
copy = arr.slice(0, 5)
'''
        result = transpile(code)
        assert 'arr.slice(0, 5)' in result
    
    def test_fill_method(self):
        """Fill with value."""
        code = '''
arr = Uint8Array(10)
arr.fill(255)
'''
        result = transpile(code)
        assert 'arr.fill(255)' in result
    
    def test_find_indexOf(self):
        """Find and indexOf methods."""
        code = '''
arr = Uint8Array([1, 2, 3, 4, 5])
idx = arr.indexOf(3)
'''
        result = transpile(code)
        assert 'arr.indexOf(3)' in result


class TestOtherTypedArrays:
    """Tests for other TypedArray types."""
    
    def test_int32array(self):
        """Int32Array construction."""
        code = '''
arr = Int32Array(10)
'''
        result = transpile(code)
        assert 'Int32Array(10)' in result
    
    def test_float32array(self):
        """Float32Array construction."""
        code = '''
arr = Float32Array([1.5, 2.5, 3.5])
'''
        result = transpile(code)
        assert 'Float32Array' in result
    
    def test_float64array(self):
        """Float64Array construction."""
        code = '''
arr = Float64Array(buffer)
'''
        result = transpile(code)
        assert 'Float64Array(buffer)' in result
    
    def test_uint8clampedarray(self):
        """Uint8ClampedArray (for ImageData)."""
        code = '''
pixels = Uint8ClampedArray(width * height * 4)
'''
        result = transpile(code)
        assert 'Uint8ClampedArray' in result


class TestTypedArrayPatterns:
    """Tests for common TypedArray patterns."""
    
    def test_image_data_pattern(self):
        """Process ImageData pixels."""
        code = '''
pixels = Uint8ClampedArray(image_data.data)
for i in range(0, len(pixels), 4):
    r = pixels[i]
    g = pixels[i + 1]
    b = pixels[i + 2]
'''
        result = transpile(code)
        assert 'Uint8ClampedArray' in result

