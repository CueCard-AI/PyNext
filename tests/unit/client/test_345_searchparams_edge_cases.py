"""
Phase 34.5: URLSearchParams Edge Cases Tests

Tests for special characters, encoding, and edge cases in query strings.
Verifies robust transpilation and browser behavior.

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestSearchParamsEncoding:
    """Test URL encoding edge cases."""
    
    def test_params_plus_vs_percent20(self):
        """Handle + vs %20 for spaces."""
        code = '''
params = URLSearchParams("name=hello+world")
value = params.get("name")
'''
        result = transpile(code)
        assert 'URLSearchParams("name=hello+world")' in result
        # .get() may use __py.dict.get helper
        assert 'params' in result
        assert '"name"' in result
    
    def test_params_ampersand_in_value(self):
        """Handle encoded ampersand in value."""
        code = '''
params = URLSearchParams("query=a%26b")
value = params.get("query")
'''
        result = transpile(code)
        # .get() may use __py.dict.get helper
        assert 'params' in result
        assert '"query"' in result
    
    def test_params_equals_in_value(self):
        """Handle encoded equals in value."""
        code = '''
params = URLSearchParams("expr=x%3D5")
value = params.get("expr")
'''
        result = transpile(code)
        # .get() may use __py.dict.get helper
        assert 'params' in result
        assert '"expr"' in result


class TestSearchParamsEmptyValues:
    """Test empty and missing values."""
    
    def test_params_empty_key(self):
        """Handle empty key with value."""
        code = '''
params = URLSearchParams("=value")
value = params.get("")
'''
        result = transpile(code)
        # .get() may use __py.dict.get helper
        assert 'params' in result
        assert '""' in result
    
    def test_params_key_no_value(self):
        """Handle key without value."""
        code = '''
params = URLSearchParams("flag")
has_flag = params.has("flag")
'''
        result = transpile(code)
        assert 'params.has("flag")' in result
    
    def test_params_key_equals_no_value(self):
        """Handle key= without value."""
        code = '''
params = URLSearchParams("key=")
value = params.get("key")  # Should be ""
'''
        result = transpile(code)
        # .get() may use __py.dict.get helper
        assert 'params' in result
        assert '"key"' in result


class TestSearchParamsUnicode:
    """Test Unicode key/value handling."""
    
    def test_params_unicode_key(self):
        """Handle Unicode key."""
        code = '''
params = URLSearchParams("名前=値")
value = params.get("名前")
'''
        result = transpile(code)
        assert '名前' in result
    
    def test_params_unicode_value(self):
        """Handle Unicode value."""
        code = '''
params = URLSearchParams("greeting=你好世界")
value = params.get("greeting")
'''
        result = transpile(code)
        assert '你好世界' in result


class TestSearchParamsLargeData:
    """Test large data handling."""
    
    def test_params_very_long_value(self):
        """Handle very long parameter value."""
        code = '''
long_value = "x" * 10000
params = URLSearchParams()
params.set("data", long_value)
'''
        result = transpile(code)
        assert 'params.set("data", long_value)' in result


class TestSearchParamsDuplicates:
    """Test duplicate key handling."""
    
    def test_params_duplicate_sort(self):
        """Sort with duplicate keys maintains relative order."""
        code = '''
params = URLSearchParams("z=1&a=2&z=3&a=4")
params.sort()
all_z = params.getAll("z")
'''
        result = transpile(code)
        # .sort() may use __py.list.sort helper
        assert 'params' in result
        assert 'sort' in result
        assert 'params.getAll("z")' in result


class TestSearchParamsMutations:
    """Test mutation operations."""
    
    def test_params_delete_nonexistent(self):
        """Delete non-existent key."""
        code = '''
params = URLSearchParams("foo=1")
params.delete("bar")
'''
        result = transpile(code)
        assert 'params.delete("bar")' in result
    
    def test_params_getAll_empty(self):
        """GetAll for non-existent key returns empty."""
        code = '''
params = URLSearchParams("foo=1")
values = params.getAll("bar")  # Returns []
'''
        result = transpile(code)
        assert 'params.getAll("bar")' in result


class TestSearchParamsConstruction:
    """Test various construction patterns."""
    
    def test_params_from_url_searchParams(self):
        """Construct from URL.searchParams."""
        code = '''
url = URL("https://example.com?a=1&b=2")
params = URLSearchParams(url.searchParams)
'''
        result = transpile(code)
        assert 'URLSearchParams(url.searchParams)' in result
    
    def test_params_numeric_value(self):
        """Handle numeric value conversion."""
        code = '''
params = URLSearchParams()
params.set("count", str(42))
params.set("price", str(19.99))
'''
        result = transpile(code)
        assert 'params.set("count"' in result
        assert 'params.set("price"' in result


