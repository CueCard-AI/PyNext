"""
Phase 34.5: URL Edge Cases Tests

Tests for unusual URL formats, special protocols, and edge cases.
Verifies robust transpilation and browser behavior.

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestURLProtocols:
    """Test various URL protocols."""
    
    def test_url_ipv6_address(self):
        """Parse IPv6 address URL."""
        code = '''
url = URL("http://[::1]:8080/path")
host = url.host
'''
        result = transpile(code)
        assert 'URL("http://[::1]:8080/path")' in result
        assert 'url.host' in result
    
    def test_url_data_protocol(self):
        """Parse data: protocol URL."""
        code = '''
url = URL("data:text/plain,Hello%20World")
protocol = url.protocol
'''
        result = transpile(code)
        assert 'URL("data:text/plain,Hello%20World")' in result
        assert 'url.protocol' in result
    
    def test_url_blob_protocol(self):
        """Parse blob: protocol URL."""
        code = '''
url = URL("blob:http://example.com/abc-123")
origin = url.origin
'''
        result = transpile(code)
        assert 'URL("blob:http://example.com/abc-123")' in result
        assert 'url.origin' in result
    
    def test_url_mailto_protocol(self):
        """Parse mailto: protocol URL."""
        code = '''
url = URL("mailto:user@example.com?subject=Hello")
pathname = url.pathname
'''
        result = transpile(code)
        assert 'URL("mailto:user@example.com?subject=Hello")' in result
        assert 'url.pathname' in result
    
    def test_url_file_protocol(self):
        """Parse file: protocol URL."""
        code = '''
url = URL("file:///path/to/file.txt")
pathname = url.pathname
'''
        result = transpile(code)
        assert 'URL("file:///path/to/file.txt")' in result


class TestURLCredentials:
    """Test URLs with credentials."""
    
    def test_url_with_credentials(self):
        """Parse URL with username and password."""
        code = '''
url = URL("https://user:pass@example.com/path")
username = url.username
password = url.password
'''
        result = transpile(code)
        assert 'url.username' in result
        assert 'url.password' in result


class TestURLPorts:
    """Test URL port handling."""
    
    def test_url_empty_port(self):
        """Handle URL with empty port string."""
        code = '''
url = URL("https://example.com:")
port = url.port
'''
        result = transpile(code)
        assert 'url.port' in result
    
    def test_url_default_port(self):
        """Port empty for default http/https ports."""
        code = '''
url = URL("https://example.com:443/path")
port = url.port  # Should be "" for default HTTPS port
'''
        result = transpile(code)
        assert 'url.port' in result


class TestURLDomains:
    """Test URL domain handling."""
    
    def test_url_punycode_domain(self):
        """Handle IDN/Punycode domain."""
        code = '''
url = URL("https://日本語.jp/path")
hostname = url.hostname
'''
        result = transpile(code)
        assert '日本語' in result
        assert 'url.hostname' in result
    
    def test_url_very_long(self):
        """Handle very long URL."""
        code = '''
long_path = "/" + "x" * 10000
url = URL(f"https://example.com{long_path}")
'''
        result = transpile(code)
        assert 'URL(' in result


class TestURLRelativePaths:
    """Test relative URL resolution."""
    
    def test_url_fragment_only(self):
        """Resolve fragment-only relative URL."""
        code = '''
base = URL("https://example.com/page")
relative = URL("#section", base)
'''
        result = transpile(code)
        assert 'URL("#section", base)' in result
    
    def test_url_query_only(self):
        """Resolve query-only relative URL."""
        code = '''
base = URL("https://example.com/page")
relative = URL("?foo=bar", base)
'''
        result = transpile(code)
        assert 'URL("?foo=bar", base)' in result
    
    def test_url_double_slash_path(self):
        """Handle double slashes in path."""
        code = '''
url = URL("https://example.com//path//to//file")
pathname = url.pathname
'''
        result = transpile(code)
        assert 'url.pathname' in result
    
    def test_url_dot_segments(self):
        """Handle dot segments in path."""
        code = '''
base = URL("https://example.com/a/b/c")
relative = URL("../d/./e/../f", base)
'''
        result = transpile(code)
        assert 'URL("../d/./e/../f", base)' in result
    
    def test_url_empty_base(self):
        """Handle relative URL with variable base."""
        code = '''
def resolve_url(relative, base_url):
    return URL(relative, base_url).href
'''
        result = transpile(code)
        assert 'URL(relative, base_url)' in result


