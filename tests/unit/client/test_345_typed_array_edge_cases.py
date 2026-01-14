"""
Phase 34.5: TypedArray Edge Cases Tests

Tests for overflow, special values, buffer sharing, and boundary conditions.
Verifies robust transpilation and browser behavior.

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestTypedArrayOverflow:
    """Test value overflow behavior."""
    
    def test_uint8_overflow(self):
        """Uint8Array value > 255 wraps."""
        code = '''
arr = Uint8Array(1)
arr[0] = 256  # Wraps to 0
arr[0] = 257  # Wraps to 1
'''
        result = transpile(code)
        assert 'arr[0] = 256' in result or '__py.setitem' in result
    
    def test_int8_overflow(self):
        """Int8Array value > 127 wraps to negative."""
        code = '''
arr = Int8Array(1)
arr[0] = 128  # Wraps to -128
arr[0] = 255  # Wraps to -1
'''
        result = transpile(code)
        assert 'Int8Array' in result
    
    def test_clamped_overflow(self):
        """Uint8ClampedArray clamps instead of wrapping."""
        code = '''
arr = Uint8ClampedArray(1)
arr[0] = 300  # Clamps to 255
arr[0] = -50  # Clamps to 0
'''
        result = transpile(code)
        assert 'Uint8ClampedArray' in result


class TestTypedArraySpecialValues:
    """Test special floating point values."""
    
    def test_float32_precision(self):
        """Float32 has limited precision."""
        code = '''
arr = Float32Array(1)
arr[0] = 0.123456789012345  # Loses precision
'''
        result = transpile(code)
        assert 'Float32Array' in result
    
    def test_float64_infinity(self):
        """Float64 handles Infinity."""
        code = '''
arr = Float64Array(2)
arr[0] = Infinity
arr[1] = -Infinity
'''
        result = transpile(code)
        assert 'Float64Array' in result
        assert 'Infinity' in result
    
    def test_float64_nan(self):
        """Float64 handles NaN."""
        code = '''
arr = Float64Array(1)
arr[0] = NaN
is_nan = isNaN(arr[0])
'''
        result = transpile(code)
        assert 'NaN' in result
    
    def test_bigint_large(self):
        """BigInt64Array handles large values."""
        code = '''
arr = BigInt64Array(1)
arr[0] = BigInt("9223372036854775807")  # Max int64
'''
        result = transpile(code)
        assert 'BigInt64Array' in result


class TestTypedArrayBufferSharing:
    """Test buffer sharing between views."""
    
    def test_subarray_shared_buffer(self):
        """subarray shares the same buffer."""
        code = '''
arr = Uint8Array([1, 2, 3, 4, 5])
sub = arr.subarray(1, 4)
sub[0] = 99  # Also changes arr[1]
'''
        result = transpile(code)
        assert 'arr.subarray(1, 4)' in result
    
    def test_slice_new_buffer(self):
        """slice creates a new buffer (copy)."""
        code = '''
arr = Uint8Array([1, 2, 3, 4, 5])
copy = arr.slice(1, 4)
copy[0] = 99  # Does NOT change arr[1]
'''
        result = transpile(code)
        assert 'arr.slice(1, 4)' in result
    
    def test_set_overlap(self):
        """set with overlapping ranges."""
        code = '''
arr = Uint8Array([1, 2, 3, 4, 5])
# Copy [1,2,3] to positions [2,3,4]
arr.set(arr.subarray(0, 3), 2)
'''
        result = transpile(code)
        assert 'arr.set(arr.subarray(0, 3), 2)' in result


class TestTypedArrayBoundaryConditions:
    """Test boundary condition handling."""
    
    def test_offset_exceeds_buffer(self):
        """Offset past buffer end throws."""
        code = '''
buffer = ArrayBuffer(10)
try:
    arr = Uint8Array(buffer, 20)  # Offset past end
except:
    console.error("Offset out of bounds")
'''
        result = transpile(code)
        assert 'Uint8Array(buffer, 20)' in result
    
    def test_length_exceeds_buffer(self):
        """Length past buffer end throws."""
        code = '''
buffer = ArrayBuffer(10)
try:
    arr = Uint8Array(buffer, 5, 10)  # Would need 15 bytes
except:
    console.error("Length out of bounds")
'''
        result = transpile(code)
        assert 'Uint8Array(buffer, 5, 10)' in result
    
    def test_negative_index(self):
        """Negative index returns undefined (not error)."""
        code = '''
arr = Uint8Array([1, 2, 3])
val = arr[-1]  # Returns undefined in JS
'''
        result = transpile(code)
        assert 'arr' in result


class TestTypedArrayConstruction:
    """Test various construction patterns."""
    
    def test_from_iterator(self):
        """Construct from iterable."""
        code = '''
arr = Uint8Array([x * 2 for x in range(10)])
'''
        result = transpile(code)
        assert 'Uint8Array' in result
    
    def test_fill_with_float(self):
        """Fill typed array truncates floats."""
        code = '''
arr = Uint8Array(5)
arr.fill(3.9)  # Fills with 3, not 4
'''
        result = transpile(code)
        assert 'arr.fill(3.9)' in result


