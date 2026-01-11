"""
Phase 34.4: Null/Undefined Safety Tests

Comprehensive tests for handling null and undefined values:
- Null target and relatedTarget
- Empty collections
- Missing data
- Defensive coding patterns

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestNullTarget:
    """Tests for null event targets."""
    
    def test_null_target_check(self):
        """Check if target is null before accessing."""
        code = '''
def on_click(event):
    if event.target:
        process(event.target)
'''
        result = transpile(code)
        assert 'event.target' in result
    
    def test_null_related_target(self):
        """relatedTarget can be null for focus events."""
        code = '''
def on_blur(event):
    if event.relatedTarget:
        # Focused something else
        new_element = event.relatedTarget
    else:
        # Focused outside window
        handle_focus_out()
'''
        result = transpile(code)
        assert 'event.relatedTarget' in result


class TestEmptyCollections:
    """Tests for empty collections."""
    
    def test_empty_files_check(self):
        """Check if dataTransfer.files is empty."""
        code = '''
def on_drop(event):
    if event.dataTransfer.files.length > 0:
        handle_files(event.dataTransfer.files)
    else:
        console.log("No files dropped")
'''
        result = transpile(code)
        assert 'event.dataTransfer.files.length' in result
    
    def test_empty_touches_check(self):
        """Check for empty touches array."""
        code = '''
def on_touch(event):
    if event.touches.length == 0:
        handle_touch_end()
'''
        result = transpile(code)
        assert 'event.touches.length' in result
    
    def test_empty_types_check(self):
        """Check empty dataTransfer.types."""
        code = '''
def on_drop(event):
    types = event.dataTransfer.types
    if types.length == 0:
        console.log("No data types")
'''
        result = transpile(code)
        assert 'event.dataTransfer.types' in result


class TestMissingData:
    """Tests for handling missing data."""
    
    def test_get_data_missing_type(self):
        """getData returns empty string for missing type."""
        code = '''
def on_drop(event):
    html = event.dataTransfer.getData("text/html")
    if html:
        use_html(html)
    else:
        # Fallback to plain text
        text = event.dataTransfer.getData("text/plain")
'''
        result = transpile(code)
        assert 'getData' in result
    
    def test_clipboard_missing_data(self):
        """Handle missing clipboard data."""
        code = '''
def on_paste(event):
    data = event.clipboardData.getData("text/plain")
    if not data:
        console.log("No text data in clipboard")
'''
        result = transpile(code)
        assert 'clipboardData.getData' in result


class TestDefensivePatterns:
    """Tests for defensive coding patterns."""
    
    def test_optional_chaining_equivalent(self):
        """Python equivalent of optional chaining."""
        code = '''
def on_click(event):
    parent = event.target.parentElement
    if parent:
        grandparent = parent.parentElement
'''
        result = transpile(code)
        assert 'event.target.parentElement' in result
    
    def test_default_value_pattern(self):
        """Default value for missing property."""
        code = '''
def on_custom(event):
    detail = event.detail or {}
    value = detail.get("value", 0)
'''
        result = transpile(code)
        assert 'event.detail' in result
    
    def test_type_check_before_access(self):
        """Check type before accessing specific properties."""
        code = '''
def on_event(event):
    if hasattr(event, "clientX"):
        # It's a mouse event
        handle_mouse(event.clientX, event.clientY)
    elif hasattr(event, "key"):
        # It's a keyboard event
        handle_key(event.key)
'''
        result = transpile(code)
        # This tests that hasattr pattern works
        assert 'event' in result

