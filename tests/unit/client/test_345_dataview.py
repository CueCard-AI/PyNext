"""
Phase 34.5: DataView Tests

Comprehensive tests for DataView get/set methods.
All tests verify zero-runtime passthrough transpilation.

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestDataViewConstruction:
    """Tests for DataView constructor."""
    
    def test_basic_construction(self):
        """Construct DataView from buffer."""
        code = '''
buffer = ArrayBuffer(256)
view = DataView(buffer)
'''
        result = transpile(code)
        assert 'DataView(buffer)' in result
    
    def test_with_offset(self):
        """Construct with offset."""
        code = '''
buffer = ArrayBuffer(256)
view = DataView(buffer, 10)
'''
        result = transpile(code)
        assert 'DataView(buffer, 10)' in result
    
    def test_with_offset_and_length(self):
        """Construct with offset and length."""
        code = '''
buffer = ArrayBuffer(256)
view = DataView(buffer, 10, 50)
'''
        result = transpile(code)
        assert 'DataView(buffer, 10, 50)' in result


class TestDataViewProperties:
    """Tests for DataView properties."""
    
    def test_properties(self):
        """Access DataView properties."""
        code = '''
view = DataView(buffer)
buf = view.buffer
length = view.byteLength
offset = view.byteOffset
'''
        result = transpile(code)
        assert 'view.buffer' in result
        assert 'view.byteLength' in result
        assert 'view.byteOffset' in result


class TestDataViewGetters:
    """Tests for DataView get methods."""
    
    def test_get_int8(self):
        """Read Int8."""
        code = '''
view = DataView(buffer)
value = view.getInt8(0)
'''
        result = transpile(code)
        assert 'view.getInt8(0)' in result
    
    def test_get_int32_little_endian(self):
        """Read Int32 little-endian."""
        code = '''
view = DataView(buffer)
value = view.getInt32(0, True)
'''
        result = transpile(code)
        assert 'view.getInt32(0, true)' in result
    
    def test_get_float64(self):
        """Read Float64."""
        code = '''
view = DataView(buffer)
value = view.getFloat64(0, True)
'''
        result = transpile(code)
        assert 'view.getFloat64(0, true)' in result


class TestDataViewSetters:
    """Tests for DataView set methods."""
    
    def test_set_int32(self):
        """Write Int32."""
        code = '''
view = DataView(buffer)
view.setInt32(0, 12345, True)
'''
        result = transpile(code)
        assert 'view.setInt32(0, 12345, true)' in result
    
    def test_set_float32(self):
        """Write Float32."""
        code = '''
view = DataView(buffer)
view.setFloat32(0, 3.14159, True)
'''
        result = transpile(code)
        assert 'view.setFloat32' in result


class TestDataViewPatterns:
    """Tests for common DataView patterns."""
    
    def test_binary_protocol_pattern(self):
        """Read binary protocol header."""
        code = '''
view = DataView(buffer)
magic = view.getUint32(0, False)  # Big-endian magic number
version = view.getUint16(4, False)
payload_size = view.getUint32(6, False)
'''
        result = transpile(code)
        assert 'view.getUint32' in result
        assert 'view.getUint16' in result

