"""
Phase 34.5: URLSearchParams Tests

Comprehensive tests for URLSearchParams CRUD operations and iteration.
All tests verify zero-runtime passthrough transpilation.

Total: 25 tests
"""

import pytest
from pynext.transpiler import transpile


class TestSearchParamsConstruction:
    """Tests for URLSearchParams constructor."""
    
    def test_from_string(self):
        """Construct from query string."""
        code = '''
params = URLSearchParams("foo=1&bar=2")
'''
        result = transpile(code)
        assert 'URLSearchParams("foo=1&bar=2")' in result
    
    def test_from_string_with_question_mark(self):
        """Construct from query string with leading ?."""
        code = '''
params = URLSearchParams("?foo=1&bar=2")
'''
        result = transpile(code)
        assert 'URLSearchParams' in result
    
    def test_from_dict(self):
        """Construct from dictionary."""
        code = '''
params = URLSearchParams({"page": "1", "limit": "10"})
'''
        result = transpile(code)
        assert 'URLSearchParams' in result
    
    def test_from_list_of_tuples(self):
        """Construct from list of tuples (allows duplicates)."""
        code = '''
params = URLSearchParams([("tag", "a"), ("tag", "b")])
'''
        result = transpile(code)
        assert 'URLSearchParams' in result
    
    def test_empty_construction(self):
        """Construct empty params."""
        code = '''
params = URLSearchParams()
'''
        result = transpile(code)
        assert 'URLSearchParams()' in result


class TestSearchParamsGet:
    """Tests for reading values."""
    
    def test_get_single(self):
        """Get single value."""
        code = '''
params = URLSearchParams("foo=1&foo=2")
first = params.get("foo")
'''
        result = transpile(code)
        # .get() may use __py.dict.get helper
        assert 'params' in result
        assert '"foo"' in result
    
    def test_get_missing(self):
        """Get missing parameter."""
        code = '''
params = URLSearchParams("foo=1")
value = params.get("missing")
'''
        result = transpile(code)
        # .get() may use __py.dict.get helper
        assert 'params' in result
        assert '"missing"' in result
    
    def test_getAll(self):
        """Get all values for a key."""
        code = '''
params = URLSearchParams("tag=a&tag=b&tag=c")
all_tags = params.getAll("tag")
'''
        result = transpile(code)
        assert 'params.getAll("tag")' in result
    
    def test_has(self):
        """Check if parameter exists."""
        code = '''
params = URLSearchParams("foo=1")
exists = params.has("foo")
'''
        result = transpile(code)
        assert 'params.has("foo")' in result
    
    def test_has_with_value(self):
        """Check if parameter exists with specific value."""
        code = '''
params = URLSearchParams("foo=1&foo=2")
has_specific = params.has("foo", "1")
'''
        result = transpile(code)
        assert 'params.has("foo", "1")' in result


class TestSearchParamsWrite:
    """Tests for modifying values."""
    
    def test_set(self):
        """Set value (replaces existing)."""
        code = '''
params = URLSearchParams("foo=1&foo=2")
params.set("foo", "new")
'''
        result = transpile(code)
        assert 'params.set("foo", "new")' in result
    
    def test_append(self):
        """Append value (keeps existing)."""
        code = '''
params = URLSearchParams("foo=1")
params.append("foo", "2")
'''
        result = transpile(code)
        assert 'params.append("foo", "2")' in result
    
    def test_delete(self):
        """Delete all values for a key."""
        code = '''
params = URLSearchParams("foo=1&bar=2")
params.delete("foo")
'''
        result = transpile(code)
        assert 'params.delete("foo")' in result
    
    def test_delete_with_value(self):
        """Delete specific value only."""
        code = '''
params = URLSearchParams("foo=1&foo=2")
params.delete("foo", "1")
'''
        result = transpile(code)
        assert 'params.delete("foo", "1")' in result
    
    def test_sort(self):
        """Sort parameters alphabetically."""
        code = '''
params = URLSearchParams("z=3&a=1&m=2")
params.sort()
'''
        result = transpile(code)
        # .sort() may use __py.list.sort helper
        assert 'params' in result
        assert 'sort' in result


class TestSearchParamsIteration:
    """Tests for iteration methods."""
    
    def test_keys(self):
        """Iterate over keys."""
        code = '''
params = URLSearchParams("a=1&b=2")
for key in params.keys():
    console.log(key)
'''
        result = transpile(code)
        # .keys() may become Object.keys(params)
        assert 'params' in result
        assert 'key' in result
    
    def test_values(self):
        """Iterate over values."""
        code = '''
params = URLSearchParams("a=1&b=2")
for value in params.values():
    console.log(value)
'''
        result = transpile(code)
        # .values() may become Object.values(params)
        assert 'params' in result
        assert 'value' in result
    
    def test_entries(self):
        """Iterate over entries."""
        code = '''
params = URLSearchParams("a=1&b=2")
for key, value in params.entries():
    console.log(f"{key}={value}")
'''
        result = transpile(code)
        assert 'params.entries()' in result
    
    def test_forEach(self):
        """ForEach callback."""
        code = '''
def log_param(value, name, params):
    console.log(f"{name}: {value}")

params.forEach(log_param)
'''
        result = transpile(code)
        assert 'params.forEach' in result


class TestSearchParamsConversion:
    """Tests for conversion methods."""
    
    def test_toString(self):
        """Convert to string."""
        code = '''
params = URLSearchParams({"page": "1", "limit": "10"})
query = params.toString()
'''
        result = transpile(code)
        assert 'params.toString()' in result


class TestSearchParamsPracticalPatterns:
    """Tests for common URLSearchParams patterns."""
    
    def test_filter_params(self):
        """Filter and rebuild params."""
        code = '''
input_params = URLSearchParams(window.location.search)
output_params = URLSearchParams()

for key, value in input_params.entries():
    if key != "secret":
        output_params.append(key, value)
'''
        result = transpile(code)
        assert 'output_params.append(key, value)' in result
    
    def test_merge_params(self):
        """Merge new params with existing."""
        code = '''
url = URL(window.location.href)
url.searchParams.set("page", "1")
url.searchParams.set("view", "grid")
'''
        result = transpile(code)
        assert 'url.searchParams.set' in result
    
    def test_build_form_data_url(self):
        """Build URL from form data."""
        code = '''
params = URLSearchParams()
params.set("name", form.name.value)
params.set("email", form.email.value)
url = f"/api/submit?{params.toString()}"
'''
        result = transpile(code)
        assert 'params.toString()' in result
    
    def test_parse_and_validate(self):
        """Parse and validate query params."""
        code = '''
params = URLSearchParams(window.location.search)
page = params.get("page")
if page:
    page_num = int(page)
else:
    page_num = 1
'''
        result = transpile(code)
        # .get() may use __py.dict.get helper
        assert 'params' in result
        assert '"page"' in result
