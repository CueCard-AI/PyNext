"""
Phase 34.4: Clipboard Event Tests

Unit tests for ClipboardEvent transpilation covering:
- copy, cut, paste events
- clipboardData access
- Custom clipboard content

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestClipboardEventBasics:
    """Tests for basic clipboard events."""
    
    def test_copy_event(self):
        """copy event should pass through."""
        code = '''
def on_copy(event):
    event.preventDefault()
    event.clipboardData.setData("text/plain", custom_text)

el.addEventListener("copy", on_copy)
'''
        result = transpile(code)
        assert 'addEventListener("copy"' in result
        assert '__py.' not in result
    
    def test_cut_event(self):
        """cut event should pass through."""
        code = '''
def on_cut(event):
    event.preventDefault()
    event.clipboardData.setData("text/plain", selected_text)
    clear_selection()

el.addEventListener("cut", on_cut)
'''
        result = transpile(code)
        assert 'addEventListener("cut"' in result
    
    def test_paste_event(self):
        """paste event should pass through."""
        code = '''
def on_paste(event):
    event.preventDefault()
    text = event.clipboardData.getData("text/plain")
    insert_text(text)

el.addEventListener("paste", on_paste)
'''
        result = transpile(code)
        assert 'addEventListener("paste"' in result


class TestClipboardData:
    """Tests for clipboardData access."""
    
    def test_get_data(self):
        """clipboardData.getData should pass through."""
        code = '''
def on_paste(event):
    text = event.clipboardData.getData("text/plain")
'''
        result = transpile(code)
        assert 'clipboardData.getData' in result
    
    def test_set_data(self):
        """clipboardData.setData should pass through."""
        code = '''
def on_copy(event):
    event.clipboardData.setData("text/plain", "Hello")
    event.clipboardData.setData("text/html", "<b>Hello</b>")
'''
        result = transpile(code)
        assert 'clipboardData.setData' in result
    
    def test_clipboard_types(self):
        """clipboardData.types should pass through."""
        code = '''
def on_paste(event):
    types = event.clipboardData.types
    if "text/html" in types:
        html = event.clipboardData.getData("text/html")
'''
        result = transpile(code)
        assert 'clipboardData.types' in result


class TestClipboardPatterns:
    """Tests for common clipboard patterns."""
    
    def test_custom_copy_handler(self):
        """Custom copy handler should work."""
        code = '''
def on_copy(event):
    event.preventDefault()
    selected = get_selected_nodes()
    json_data = serialize_nodes(selected)
    event.clipboardData.setData("application/json", json_data)
    event.clipboardData.setData("text/plain", get_text_repr(selected))
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert 'clipboardData.setData' in result
    
    def test_paste_with_type_check(self):
        """Paste with type checking should work."""
        code = '''
def on_paste(event):
    event.preventDefault()
    
    if "image/png" in event.clipboardData.types:
        handle_image_paste(event.clipboardData)
    elif "text/html" in event.clipboardData.types:
        html = event.clipboardData.getData("text/html")
        handle_html_paste(html)
    else:
        text = event.clipboardData.getData("text/plain")
        handle_text_paste(text)
'''
        result = transpile(code)
        assert 'clipboardData.types' in result
        assert 'clipboardData.getData' in result
    
    def test_prevent_default_copy(self):
        """Preventing default copy should work."""
        code = '''
def on_copy(event):
    if should_block_copy():
        event.preventDefault()
        show_copy_blocked_message()
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
    
    def test_rich_text_paste(self):
        """Rich text paste should work."""
        code = '''
def on_paste(event):
    event.preventDefault()
    
    # Try HTML first, fall back to plain text
    html = event.clipboardData.getData("text/html")
    if html:
        insert_html(html)
    else:
        text = event.clipboardData.getData("text/plain")
        insert_text(text)
'''
        result = transpile(code)
        assert 'getData("text/html")' in result
        assert 'getData("text/plain")' in result

