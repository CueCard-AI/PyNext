"""
DOM Type-Aware Transpilation Tests

Tests for compile-time DOM type tracking that enables zero-runtime passthrough
for DOM API methods, eliminating __py.* wrappers and reducing bundle size.

Total: 50 tests
- Type Tracking (15 tests)
- Method Dispatch (20 tests)
- Integration (10 tests)
- E2E Browser (5 tests) - in separate file
"""

import pytest
from pynext.transpiler import transpile
from pynext.transpiler._internal.scope import ScopeTracker


# =============================================================================
# TYPE TRACKING TESTS (15 tests)
# =============================================================================

class TestDOMTypeTrackingBasic:
    """Test basic DOM type tracking in ScopeTracker."""
    
    def test_declare_dom_type(self):
        """Test declaring a DOM type for a variable."""
        scope = ScopeTracker()
        scope.declare_dom_type("encoder", "TextEncoder")
        
        assert scope.get_dom_type("encoder") == "TextEncoder"
    
    def test_get_dom_type_returns_none_for_unknown(self):
        """Test that unknown variables return None."""
        scope = ScopeTracker()
        
        assert scope.get_dom_type("unknown") is None
    
    def test_clear_dom_type(self):
        """Test clearing a DOM type."""
        scope = ScopeTracker()
        scope.declare_dom_type("encoder", "TextEncoder")
        scope.clear_dom_type("encoder")
        
        assert scope.get_dom_type("encoder") is None
    
    def test_clear_dom_type_nonexistent(self):
        """Test clearing a non-existent DOM type doesn't error."""
        scope = ScopeTracker()
        scope.clear_dom_type("nonexistent")  # Should not raise
        
        assert scope.get_dom_type("nonexistent") is None
    
    def test_multiple_variables(self):
        """Test tracking multiple DOM-typed variables."""
        scope = ScopeTracker()
        scope.declare_dom_type("encoder", "TextEncoder")
        scope.declare_dom_type("decoder", "TextDecoder")
        scope.declare_dom_type("params", "URLSearchParams")
        
        assert scope.get_dom_type("encoder") == "TextEncoder"
        assert scope.get_dom_type("decoder") == "TextDecoder"
        assert scope.get_dom_type("params") == "URLSearchParams"
    
    def test_overwrite_dom_type(self):
        """Test that reassigning to different DOM type updates tracking."""
        scope = ScopeTracker()
        scope.declare_dom_type("obj", "TextEncoder")
        scope.declare_dom_type("obj", "TextDecoder")
        
        assert scope.get_dom_type("obj") == "TextDecoder"
    
    def test_reset_clears_dom_types(self):
        """Test that reset() clears all DOM type tracking."""
        scope = ScopeTracker()
        scope.declare_dom_type("encoder", "TextEncoder")
        scope.reset()
        
        assert scope.get_dom_type("encoder") is None


class TestDOMTypeTrackingFromTranspilation:
    """Test that transpilation correctly records DOM types."""
    
    def test_textencoder_constructor_tracking(self):
        """TextEncoder constructor should be tracked."""
        code = '''
encoder = TextEncoder()
'''
        result = transpile(code)
        assert 'TextEncoder()' in result
    
    def test_urlsearchparams_constructor_tracking(self):
        """URLSearchParams constructor should be tracked."""
        code = '''
params = URLSearchParams("a=1")
'''
        result = transpile(code)
        assert 'URLSearchParams("a=1")' in result
    
    def test_blob_constructor_tracking(self):
        """Blob constructor should be tracked."""
        code = '''
blob = Blob(["hello"])
'''
        result = transpile(code)
        assert 'Blob(["hello"])' in result
    
    def test_uint8array_constructor_tracking(self):
        """Uint8Array constructor should be tracked."""
        code = '''
arr = Uint8Array(10)
'''
        result = transpile(code)
        assert 'Uint8Array(10)' in result
    
    def test_dataview_constructor_tracking(self):
        """DataView constructor should be tracked."""
        code = '''
buffer = ArrayBuffer(16)
view = DataView(buffer)
'''
        result = transpile(code)
        assert 'DataView(buffer)' in result
    
    def test_formdata_constructor_tracking(self):
        """FormData constructor should be tracked."""
        code = '''
form = FormData()
'''
        result = transpile(code)
        assert 'FormData()' in result
    
    def test_headers_constructor_tracking(self):
        """Headers constructor should be tracked."""
        code = '''
headers = Headers()
'''
        result = transpile(code)
        assert 'Headers()' in result
    
    def test_websocket_constructor_tracking(self):
        """WebSocket constructor should be tracked."""
        code = '''
ws = WebSocket("wss://example.com")
'''
        result = transpile(code)
        assert 'WebSocket("wss://example.com")' in result


# =============================================================================
# METHOD DISPATCH TESTS (20 tests)
# =============================================================================

class TestDOMMethodPassthrough:
    """Test that DOM methods on tracked types passthrough directly."""
    
    def test_textencoder_encode_passthrough(self):
        """TextEncoder.encode() should passthrough."""
        code = '''
encoder = TextEncoder()
bytes_arr = encoder.encode("Hello")
'''
        result = transpile(code)
        assert 'encoder.encode("Hello")' in result
        assert '__py.str.encode' not in result
    
    def test_textencoder_encodeinto_passthrough(self):
        """TextEncoder.encodeInto() should passthrough."""
        code = '''
encoder = TextEncoder()
buffer = Uint8Array(10)
result = encoder.encodeInto("Hi", buffer)
'''
        result = transpile(code)
        assert 'encoder.encodeInto("Hi", buffer)' in result
    
    def test_textdecoder_decode_passthrough(self):
        """TextDecoder.decode() should passthrough."""
        code = '''
decoder = TextDecoder()
text = decoder.decode(bytes_arr)
'''
        result = transpile(code)
        assert 'decoder.decode(bytes_arr)' in result
    
    def test_urlsearchparams_get_passthrough(self):
        """URLSearchParams.get() should passthrough."""
        code = '''
params = URLSearchParams("a=1")
value = params.get("a")
'''
        result = transpile(code)
        assert 'params.get("a")' in result
        assert '__py.dict.get' not in result
    
    def test_urlsearchparams_set_passthrough(self):
        """URLSearchParams.set() should passthrough."""
        code = '''
params = URLSearchParams()
params.set("key", "value")
'''
        result = transpile(code)
        assert 'params.set("key", "value")' in result
    
    def test_urlsearchparams_sort_passthrough(self):
        """URLSearchParams.sort() should passthrough."""
        code = '''
params = URLSearchParams("z=1&a=2")
params.sort()
'''
        result = transpile(code)
        assert 'params.sort()' in result
        assert '__py.list.sort' not in result
    
    def test_urlsearchparams_keys_passthrough(self):
        """URLSearchParams.keys() should passthrough."""
        code = '''
params = URLSearchParams("a=1&b=2")
keys = params.keys()
'''
        result = transpile(code)
        assert 'params.keys()' in result
        assert 'Object.keys(params)' not in result
    
    def test_urlsearchparams_values_passthrough(self):
        """URLSearchParams.values() should passthrough."""
        code = '''
params = URLSearchParams("a=1&b=2")
values = params.values()
'''
        result = transpile(code)
        assert 'params.values()' in result
    
    def test_urlsearchparams_entries_passthrough(self):
        """URLSearchParams.entries() should passthrough."""
        code = '''
params = URLSearchParams("a=1&b=2")
entries = params.entries()
'''
        result = transpile(code)
        assert 'params.entries()' in result
    
    def test_blob_text_passthrough(self):
        """Blob.text() should passthrough."""
        code = '''
blob = Blob(["hello"])
async def get_text():
    text = await blob.text()
'''
        result = transpile(code)
        assert 'blob.text()' in result
    
    def test_blob_arraybuffer_passthrough(self):
        """Blob.arrayBuffer() should passthrough."""
        code = '''
blob = Blob(["hello"])
async def get_buffer():
    buffer = await blob.arrayBuffer()
'''
        result = transpile(code)
        assert 'blob.arrayBuffer()' in result
    
    def test_blob_slice_passthrough(self):
        """Blob.slice() should passthrough."""
        code = '''
blob = Blob(["hello world"])
part = blob.slice(0, 5)
'''
        result = transpile(code)
        assert 'blob.slice(0, 5)' in result
    
    def test_uint8array_subarray_passthrough(self):
        """Uint8Array.subarray() should passthrough."""
        code = '''
arr = Uint8Array(10)
sub = arr.subarray(2, 8)
'''
        result = transpile(code)
        assert 'arr.subarray(2, 8)' in result
    
    def test_dataview_getint32_passthrough(self):
        """DataView.getInt32() should passthrough."""
        code = '''
buffer = ArrayBuffer(16)
view = DataView(buffer)
value = view.getInt32(0, True)
'''
        result = transpile(code)
        assert 'view.getInt32(0, true)' in result
    
    def test_dataview_setfloat64_passthrough(self):
        """DataView.setFloat64() should passthrough."""
        code = '''
buffer = ArrayBuffer(16)
view = DataView(buffer)
view.setFloat64(0, 3.14, True)
'''
        result = transpile(code)
        assert 'view.setFloat64(0, 3.14, true)' in result
    
    def test_formdata_get_passthrough(self):
        """FormData.get() should passthrough."""
        code = '''
form = FormData()
value = form.get("key")
'''
        result = transpile(code)
        assert 'form.get("key")' in result
        assert '__py.dict.get' not in result
    
    def test_headers_get_passthrough(self):
        """Headers.get() should passthrough."""
        code = '''
headers = Headers()
value = headers.get("Content-Type")
'''
        result = transpile(code)
        assert 'headers.get("Content-Type")' in result
        assert '__py.dict.get' not in result


class TestPythonMethodsPreserved:
    """Test that Python methods still use __py helpers."""
    
    def test_dict_get_uses_py_helper(self):
        """dict.get() should use __py.dict.get."""
        code = '''
d = {"a": 1}
value = d.get("a")
'''
        result = transpile(code)
        assert '__py.dict.get(d, "a", null)' in result
    
    def test_list_sort_uses_py_helper(self):
        """list.sort() should use __py.list.sort."""
        code = '''
items = [3, 1, 2]
items.sort()
'''
        result = transpile(code)
        assert '__py.list.sort(items)' in result
    
    def test_str_encode_uses_py_helper_when_not_textencoder(self):
        """str.encode() should use __py.str.encode when not TextEncoder."""
        code = '''
s = "hello"
bytes_arr = s.encode("utf-8")
'''
        result = transpile(code)
        assert '__py.str.encode(s, "utf-8")' in result


# =============================================================================
# INTEGRATION TESTS (10 tests)
# =============================================================================

class TestDOMTypeTrackingIntegration:
    """Integration tests for complete transpilation scenarios."""
    
    def test_mixed_dom_and_python_code(self):
        """DOM types and Python types coexist correctly."""
        code = '''
encoder = TextEncoder()
data = {"key": "value"}
bytes_arr = encoder.encode("Hello")
value = data.get("key")
'''
        result = transpile(code)
        assert 'encoder.encode("Hello")' in result
        assert '__py.dict.get(data, "key", null)' in result
    
    def test_multiple_dom_constructors(self):
        """Multiple DOM types tracked correctly."""
        code = '''
encoder = TextEncoder()
decoder = TextDecoder()
params = URLSearchParams("a=1")
encoded = encoder.encode("test")
decoded = decoder.decode(encoded)
value = params.get("a")
'''
        result = transpile(code)
        assert 'encoder.encode("test")' in result
        assert 'decoder.decode(encoded)' in result
        assert 'params.get("a")' in result
    
    def test_dom_type_in_function(self):
        """DOM type tracking works inside functions."""
        code = '''
def encode_text(text):
    encoder = TextEncoder()
    return encoder.encode(text)
'''
        result = transpile(code)
        assert 'encoder.encode(text)' in result
    
    def test_url_api_full_usage(self):
        """Complete URL API usage example."""
        code = '''
url = URL("https://example.com/path?a=1")
params = url.searchParams
params.set("b", "2")
params.sort()
href = url.toString()
'''
        result = transpile(code)
        # url.searchParams should passthrough
        assert 'url.searchParams' in result
        # Note: params here is not tracked from constructor
        # but should still work due to DOM method detection
    
    def test_encoding_roundtrip(self):
        """Encode and decode roundtrip."""
        code = '''
encoder = TextEncoder()
decoder = TextDecoder()
encoded = encoder.encode("Hello, World!")
decoded = decoder.decode(encoded)
'''
        result = transpile(code)
        assert 'encoder.encode("Hello, World!")' in result
        assert 'decoder.decode(encoded)' in result
    
    def test_binary_data_manipulation(self):
        """Binary data manipulation with TypedArrays."""
        code = '''
buffer = ArrayBuffer(16)
view = DataView(buffer)
view.setInt32(0, 12345, True)
value = view.getInt32(0, True)
'''
        result = transpile(code)
        assert 'view.setInt32(0, 12345, true)' in result
        assert 'view.getInt32(0, true)' in result
    
    def test_typed_array_operations(self):
        """TypedArray method passthrough."""
        code = '''
arr = Uint8Array(100)
sub = arr.subarray(10, 50)
arr.fill(0)
idx = arr.indexOf(0)
'''
        result = transpile(code)
        assert 'arr.subarray(10, 50)' in result
        assert 'arr.fill(0)' in result
        assert 'arr.indexOf(0)' in result
    
    def test_formdata_usage(self):
        """FormData API usage."""
        code = '''
form = FormData()
form.append("name", "John")
form.set("email", "john@example.com")
name = form.get("name")
form.delete("email")
'''
        result = transpile(code)
        assert 'form.append("name", "John")' in result
        assert 'form.set("email", "john@example.com")' in result
        assert 'form.get("name")' in result
        assert 'form.delete("email")' in result
    
    def test_headers_usage(self):
        """Headers API usage."""
        code = '''
headers = Headers()
headers.set("Content-Type", "application/json")
headers.append("Accept", "application/json")
content_type = headers.get("Content-Type")
'''
        result = transpile(code)
        assert 'headers.set("Content-Type", "application/json")' in result
        assert 'headers.get("Content-Type")' in result
    
    def test_websocket_usage(self):
        """WebSocket API usage."""
        code = '''
ws = WebSocket("wss://example.com")
ws.send("Hello")
ws.close()
'''
        result = transpile(code)
        assert 'ws.send("Hello")' in result
        assert 'ws.close()' in result


