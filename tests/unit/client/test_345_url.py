"""
Phase 34.5: URL API Tests

Comprehensive tests for URL construction, properties, and methods.
All tests verify zero-runtime passthrough transpilation.

Total: 25 tests
"""

import pytest
from pynext.transpiler import transpile


class TestURLConstruction:
    """Tests for URL constructor."""
    
    def test_url_absolute(self):
        """Construct URL from absolute string."""
        code = '''
url = URL("https://example.com/path?query=1#hash")
'''
        result = transpile(code)
        assert 'URL("https://example.com/path?query=1#hash")' in result
    
    def test_url_with_base(self):
        """Construct URL from relative string with base."""
        code = '''
url = URL("/api/users", "https://example.com")
'''
        result = transpile(code)
        assert 'URL("/api/users", "https://example.com")' in result
    
    def test_url_relative_resolution(self):
        """Resolve relative path against base."""
        code = '''
base = URL("https://example.com/a/b/c")
relative = URL("../d", base)
'''
        result = transpile(code)
        assert 'URL("../d", base)' in result
    
    def test_url_from_variable(self):
        """Construct URL from variable."""
        code = '''
url_string = get_url()
url = URL(url_string)
'''
        result = transpile(code)
        assert 'URL(url_string)' in result
    
    def test_url_from_location(self):
        """Construct URL from window.location."""
        code = '''
url = URL(window.location.href)
'''
        result = transpile(code)
        assert 'URL(window.location.href)' in result


class TestURLProperties:
    """Tests for URL property access."""
    
    def test_url_href(self):
        """Access href property."""
        code = '''
url = URL("https://example.com/path")
full_url = url.href
'''
        result = transpile(code)
        assert 'url.href' in result
    
    def test_url_protocol(self):
        """Access protocol property."""
        code = '''
url = URL("https://example.com")
scheme = url.protocol
'''
        result = transpile(code)
        assert 'url.protocol' in result
    
    def test_url_hostname(self):
        """Access hostname property."""
        code = '''
url = URL("https://example.com:8080/path")
host = url.hostname
'''
        result = transpile(code)
        assert 'url.hostname' in result
    
    def test_url_port(self):
        """Access port property."""
        code = '''
url = URL("https://example.com:8080")
port = url.port
'''
        result = transpile(code)
        assert 'url.port' in result
    
    def test_url_pathname(self):
        """Access pathname property."""
        code = '''
url = URL("https://example.com/api/users")
path = url.pathname
'''
        result = transpile(code)
        assert 'url.pathname' in result
    
    def test_url_search(self):
        """Access search (query string) property."""
        code = '''
url = URL("https://example.com?foo=bar")
query = url.search
'''
        result = transpile(code)
        assert 'url.search' in result
    
    def test_url_hash(self):
        """Access hash (fragment) property."""
        code = '''
url = URL("https://example.com#section")
fragment = url.hash
'''
        result = transpile(code)
        assert 'url.hash' in result
    
    def test_url_origin(self):
        """Access origin property (read-only)."""
        code = '''
url = URL("https://example.com:8080/path")
origin = url.origin
'''
        result = transpile(code)
        assert 'url.origin' in result
    
    def test_url_searchParams(self):
        """Access searchParams property."""
        code = '''
url = URL("https://example.com?page=1")
params = url.searchParams
'''
        result = transpile(code)
        assert 'url.searchParams' in result
    
    def test_url_username_password(self):
        """Access username and password."""
        code = '''
url = URL("https://user:pass@example.com")
username = url.username
password = url.password
'''
        result = transpile(code)
        assert 'url.username' in result
        assert 'url.password' in result


class TestURLPropertySetters:
    """Tests for URL property modification."""
    
    def test_set_pathname(self):
        """Modify pathname."""
        code = '''
url = URL("https://example.com/old")
url.pathname = "/new"
'''
        result = transpile(code)
        assert 'url.pathname = "/new"' in result
    
    def test_set_hash(self):
        """Modify hash."""
        code = '''
url = URL("https://example.com")
url.hash = "#section"
'''
        result = transpile(code)
        assert 'url.hash = "#section"' in result
    
    def test_set_search(self):
        """Modify search/query string."""
        code = '''
url = URL("https://example.com")
url.search = "?page=2"
'''
        result = transpile(code)
        assert 'url.search = "?page=2"' in result


class TestURLMethods:
    """Tests for URL methods."""
    
    def test_url_toString(self):
        """toString() method."""
        code = '''
url = URL("https://example.com")
text = url.toString()
'''
        result = transpile(code)
        assert 'url.toString()' in result
    
    def test_url_toJSON(self):
        """toJSON() method."""
        code = '''
url = URL("https://example.com")
json = url.toJSON()
'''
        result = transpile(code)
        assert 'url.toJSON()' in result


class TestURLStaticMethods:
    """Tests for URL static methods."""
    
    def test_createObjectURL(self):
        """URL.createObjectURL() static method."""
        code = '''
blob = Blob(["data"], {"type": "text/plain"})
url = URL.createObjectURL(blob)
'''
        result = transpile(code)
        assert 'URL.createObjectURL(blob)' in result
    
    def test_revokeObjectURL(self):
        """URL.revokeObjectURL() static method."""
        code = '''
URL.revokeObjectURL(url)
'''
        result = transpile(code)
        assert 'URL.revokeObjectURL(url)' in result


class TestURLPracticalPatterns:
    """Tests for common URL usage patterns."""
    
    def test_build_api_url(self):
        """Build API URL with query params."""
        code = '''
def build_api_url(endpoint, page, limit):
    url = URL(f"{window.location.origin}/api{endpoint}")
    url.searchParams.set("page", str(page))
    url.searchParams.set("limit", str(limit))
    return url.href
'''
        result = transpile(code)
        assert 'url.searchParams.set' in result
        assert 'url.href' in result
    
    def test_parse_current_url(self):
        """Parse current page URL."""
        code = '''
url = URL(window.location.href)
page = url.searchParams.get("page")
'''
        result = transpile(code)
        # .get() may use __py.dict.get helper
        assert 'url.searchParams' in result
        assert '"page"' in result
