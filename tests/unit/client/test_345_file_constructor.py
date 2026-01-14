"""
Phase 34.5: File Constructor Tests

Tests for the File constructor options and properties.

Total: 5 tests

WHO: Developers creating files programmatically
WHAT: File constructor with name, type, and lastModified
WHEN: Creating downloadable files, testing file handling
WHERE: Client-side transpiled code
WHY: Complete Phase 34.5 coverage
HOW: Direct passthrough to native File API
"""

import pytest
from pynext.transpiler import transpile


class TestFileConstructor:
    """Tests for File constructor and properties."""

    def test_file_with_name(self):
        """File constructor with name should emit correctly."""
        code = 'file = File(["content"], "file.txt")'
        result = transpile(code)
        assert 'new File(["content"], "file.txt")' in result

    def test_file_with_options(self):
        """File constructor with options should emit correctly."""
        code = 'file = File(["content"], "file.txt", {"type": "text/plain"})'
        result = transpile(code)
        assert 'new File(["content"], "file.txt"' in result
        assert '"type": "text/plain"' in result or '"type":"text/plain"' in result

    def test_file_last_modified(self):
        """File with lastModified option should emit correctly."""
        code = 'file = File(["content"], "file.txt", {"type": "text/plain", "lastModified": 1234567890})'
        result = transpile(code)
        assert 'new File(' in result
        assert '"lastModified": 1234567890' in result or '"lastModified":1234567890' in result

    def test_file_name_property(self):
        """File.name property should pass through."""
        code = '''
file = File(["content"], "myfile.txt")
name = file.name
'''
        result = transpile(code)
        assert 'file.name' in result

    def test_file_inherits_from_blob(self):
        """File should inherit .size and .type from Blob."""
        code = '''
file = File(["Hello World"], "hello.txt", {"type": "text/plain"})
size = file.size
type_val = file.type
last_mod = file.lastModified
'''
        result = transpile(code)
        assert 'file.size' in result
        assert 'file.type' in result
        assert 'file.lastModified' in result

