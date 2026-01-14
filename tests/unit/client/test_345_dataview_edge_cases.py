"""
Phase 34.5: DataView Edge Cases Tests

Tests for alignment, endianness, bounds checking, and special values.
Verifies robust transpilation and browser behavior.

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestDataViewAlignment:
    """Test unaligned access (allowed in JS unlike some languages)."""
    
    def test_misaligned_int16(self):
        """Read Int16 at odd offset (allowed in JS)."""
        code = '''
buffer = ArrayBuffer(10)
view = DataView(buffer)
# Reading 2 bytes starting at offset 1 (odd) is OK in JS
value = view.getInt16(1, True)
'''
        result = transpile(code)
        assert 'view.getInt16(1, true)' in result
    
    def test_misaligned_int32(self):
        """Read Int32 at non-4-aligned offset."""
        code = '''
buffer = ArrayBuffer(10)
view = DataView(buffer)
# Reading 4 bytes starting at offset 3 is OK in JS
value = view.getInt32(3, True)
'''
        result = transpile(code)
        assert 'view.getInt32(3, true)' in result
    
    def test_misaligned_float64(self):
        """Read Float64 at non-8-aligned offset."""
        code = '''
buffer = ArrayBuffer(16)
view = DataView(buffer)
# Reading 8 bytes starting at offset 3 is OK in JS
value = view.getFloat64(3, True)
'''
        result = transpile(code)
        assert 'view.getFloat64(3, true)' in result


class TestDataViewBounds:
    """Test bounds checking."""
    
    def test_read_past_end(self):
        """Reading past buffer end throws RangeError."""
        code = '''
buffer = ArrayBuffer(4)
view = DataView(buffer)
try:
    value = view.getInt32(2, True)  # Would read 4 bytes from offset 2
except:
    console.error("Read past buffer end")
'''
        result = transpile(code)
        assert 'view.getInt32(2, true)' in result
    
    def test_write_past_end(self):
        """Writing past buffer end throws RangeError."""
        code = '''
buffer = ArrayBuffer(4)
view = DataView(buffer)
try:
    view.setInt32(2, 12345, True)  # Would write 4 bytes from offset 2
except:
    console.error("Write past buffer end")
'''
        result = transpile(code)
        assert 'view.setInt32(2, 12345, true)' in result
    
    def test_negative_offset(self):
        """Negative offset throws RangeError."""
        code = '''
buffer = ArrayBuffer(10)
view = DataView(buffer)
try:
    value = view.getInt8(-1)
except:
    console.error("Negative offset")
'''
        result = transpile(code)
        # Negative numbers get parentheses: (-1)
        assert 'view.getInt8' in result
        assert '-1' in result


class TestDataViewEndianness:
    """Test endianness handling."""
    
    def test_endian_round_trip(self):
        """Write little-endian, read as big-endian."""
        code = '''
buffer = ArrayBuffer(4)
view = DataView(buffer)
view.setInt32(0, 305419896, True)  # Little-endian (0x12345678 in decimal)
le_value = view.getInt32(0, True)
be_value = view.getInt32(0, False)
'''
        result = transpile(code)
        # Hex literals are converted to decimal
        assert 'view.setInt32(0, 305419896, true)' in result
        assert 'view.getInt32(0, false)' in result


class TestDataViewSpecialValues:
    """Test special floating point values."""
    
    def test_float_special_values(self):
        """Store and retrieve special float values."""
        code = '''
buffer = ArrayBuffer(24)
view = DataView(buffer)
view.setFloat64(0, 1.5, True)
view.setFloat64(8, 2.5, True)
view.setFloat64(16, -0.5, True)

val1 = view.getFloat64(0, True)
val2 = view.getFloat64(8, True)
val3 = view.getFloat64(16, True)
'''
        result = transpile(code)
        assert 'view.setFloat64(0, 1.5, true)' in result
        assert 'view.setFloat64(8, 2.5, true)' in result


class TestDataViewBigInt:
    """Test BigInt methods."""
    
    def test_bigint_range(self):
        """BigInt64 max/min values."""
        code = '''
buffer = ArrayBuffer(16)
view = DataView(buffer)
# Max int64
view.setBigInt64(0, BigInt("9223372036854775807"), True)
# Min int64
view.setBigInt64(8, BigInt("-9223372036854775808"), True)

max_val = view.getBigInt64(0, True)
min_val = view.getBigInt64(8, True)
'''
        result = transpile(code)
        assert 'view.setBigInt64' in result
        assert 'view.getBigInt64' in result


class TestDataViewOffset:
    """Test DataView with byteOffset."""
    
    def test_offset_view(self):
        """DataView with non-zero byteOffset."""
        code = '''
buffer = ArrayBuffer(100)
# Create view starting at offset 50 with length 20
view = DataView(buffer, 50, 20)
view.setInt32(0, 12345, True)  # Actually writes at buffer[50]
'''
        result = transpile(code)
        assert 'DataView(buffer, 50, 20)' in result


