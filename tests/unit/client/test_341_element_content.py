"""
Phase 34.1: Element Content Tests

Tests for Element content manipulation including innerHTML, textContent, value,
and other content-related properties.

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Element Content Tests (15 tests)
# =============================================================================

class TestElementContent:
    """Tests for element content properties."""
    
    def test_inner_html_read(self):
        """Reading innerHTML should pass through."""
        code = 'html = el.innerHTML'
        result = transpile(code)
        assert 'el.innerHTML' in result
    
    def test_inner_html_write(self):
        """Writing innerHTML should pass through."""
        code = 'el.innerHTML = "<span>Hello</span>"'
        result = transpile(code)
        assert 'el.innerHTML = "<span>Hello</span>"' in result
    
    def test_inner_html_with_variable(self):
        """innerHTML with variable should work."""
        code = '''
content = "<h1>Title</h1>"
el.innerHTML = content
'''
        result = transpile(code)
        assert 'el.innerHTML = content' in result
    
    def test_outer_html_read(self):
        """Reading outerHTML should pass through."""
        code = 'full_html = el.outerHTML'
        result = transpile(code)
        assert 'el.outerHTML' in result
    
    def test_inner_text_read(self):
        """Reading innerText should pass through."""
        code = 'visible_text = el.innerText'
        result = transpile(code)
        assert 'el.innerText' in result
    
    def test_inner_text_write(self):
        """Writing innerText should pass through."""
        code = 'el.innerText = "Visible text"'
        result = transpile(code)
        assert 'el.innerText = "Visible text"' in result
    
    def test_text_content_read(self):
        """Reading textContent should pass through."""
        code = 'text = el.textContent'
        result = transpile(code)
        assert 'el.textContent' in result
    
    def test_text_content_write(self):
        """Writing textContent should pass through."""
        code = 'el.textContent = "All text content"'
        result = transpile(code)
        assert 'el.textContent = "All text content"' in result
    
    def test_value_input(self):
        """Reading/writing value on input should work."""
        code = '''
input_el = document.getElementById("name-input")
name = input_el.value
input_el.value = "New value"
'''
        result = transpile(code)
        assert 'input_el.value' in result
        assert 'input_el.value = "New value"' in result
    
    def test_value_textarea(self):
        """value on textarea should pass through."""
        code = 'textarea.value = "Long text content"'
        result = transpile(code)
        assert 'textarea.value = "Long text content"' in result
    
    def test_id_read(self):
        """Reading id should pass through."""
        code = 'element_id = el.id'
        result = transpile(code)
        assert 'el.id' in result
    
    def test_id_write(self):
        """Writing id should pass through."""
        code = 'el.id = "new-id"'
        result = transpile(code)
        assert 'el.id = "new-id"' in result
    
    def test_tag_name(self):
        """tagName should pass through."""
        code = 'tag = el.tagName'
        result = transpile(code)
        assert 'el.tagName' in result
    
    def test_hidden_read(self):
        """Reading hidden should pass through."""
        code = 'is_hidden = el.hidden'
        result = transpile(code)
        assert 'el.hidden' in result
    
    def test_hidden_write(self):
        """Writing hidden should pass through."""
        code = 'el.hidden = True'
        result = transpile(code)
        assert 'el.hidden = true' in result
    
    def test_tab_index(self):
        """tabIndex should pass through."""
        code = 'el.tabIndex = 0'
        result = transpile(code)
        assert 'el.tabIndex = 0' in result

