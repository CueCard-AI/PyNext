"""
Phase 34.1: Document API Tests

Tests for Document interface transpilation including queries, creation, and properties.
All tests verify that DOM APIs pass through unchanged (zero runtime overhead).

Test Categories:
- Document Queries (12 tests): getElementById, querySelector, querySelectorAll, etc.
- Document Creation (8 tests): createElement, createTextNode, etc.
- Document Properties (10 tests): body, head, title, etc.

Total: 30 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Document Query Tests (12 tests)
# =============================================================================

class TestDocumentQueries:
    """Tests for document query methods."""
    
    def test_get_element_by_id_basic(self):
        """getElementById should pass through unchanged."""
        code = 'el = document.getElementById("app")'
        result = transpile(code)
        assert 'document.getElementById("app")' in result
        assert "__py." not in result  # No runtime wrapper
    
    def test_get_element_by_id_transpiles_directly(self):
        """getElementById should be emitted without transformation."""
        code = 'app = document.getElementById("main-container")'
        result = transpile(code)
        assert 'let app = document.getElementById("main-container");' in result
    
    def test_get_element_by_id_no_runtime_wrapper(self):
        """DOM calls should not use __py runtime helpers."""
        code = '''
el = document.getElementById("test")
el.innerHTML = "Hello"
'''
        result = transpile(code)
        assert "__py." not in result
        assert "document.getElementById" in result
        assert ".innerHTML" in result
    
    def test_query_selector_class(self):
        """querySelector with class selector."""
        code = 'btn = document.querySelector(".primary-button")'
        result = transpile(code)
        assert 'document.querySelector(".primary-button")' in result
    
    def test_query_selector_id(self):
        """querySelector with ID selector."""
        code = 'el = document.querySelector("#header")'
        result = transpile(code)
        assert 'document.querySelector("#header")' in result
    
    def test_query_selector_complex(self):
        """querySelector with complex CSS selector."""
        code = 'card = document.querySelector("div.card > .content:first-child")'
        result = transpile(code)
        assert 'document.querySelector("div.card > .content:first-child")' in result
    
    def test_query_selector_all_basic(self):
        """querySelectorAll should pass through unchanged."""
        code = 'items = document.querySelectorAll(".item")'
        result = transpile(code)
        assert 'document.querySelectorAll(".item")' in result
    
    def test_query_selector_all_transpiles_directly(self):
        """querySelectorAll should not use runtime helpers."""
        code = '''
buttons = document.querySelectorAll("button")
for btn in buttons:
    btn.disabled = True
'''
        result = transpile(code)
        assert 'document.querySelectorAll("button")' in result
        assert "__py.querySelectorAll" not in result
    
    def test_get_elements_by_class_name(self):
        """getElementsByClassName should pass through unchanged."""
        code = 'items = document.getElementsByClassName("list-item")'
        result = transpile(code)
        assert 'document.getElementsByClassName("list-item")' in result
    
    def test_get_elements_by_tag_name(self):
        """getElementsByTagName should pass through unchanged."""
        code = 'divs = document.getElementsByTagName("div")'
        result = transpile(code)
        assert 'document.getElementsByTagName("div")' in result
    
    def test_get_elements_by_name(self):
        """getElementsByName should pass through unchanged."""
        code = 'radios = document.getElementsByName("color")'
        result = transpile(code)
        assert 'document.getElementsByName("color")' in result
    
    def test_chained_queries(self):
        """Chained query methods should work."""
        code = '''
container = document.getElementById("container")
items = container.querySelectorAll(".item")
'''
        result = transpile(code)
        assert 'document.getElementById("container")' in result
        assert 'container.querySelectorAll(".item")' in result


# =============================================================================
# Document Creation Tests (8 tests)
# =============================================================================

class TestDocumentCreation:
    """Tests for document element creation methods."""
    
    def test_create_element_div(self):
        """createElement for div should pass through."""
        code = 'div = document.createElement("div")'
        result = transpile(code)
        assert 'document.createElement("div")' in result
    
    def test_create_element_span(self):
        """createElement for span should pass through."""
        code = 'span = document.createElement("span")'
        result = transpile(code)
        assert 'document.createElement("span")' in result
    
    def test_create_element_ns_svg(self):
        """createElementNS for SVG should pass through."""
        code = 'circle = document.createElementNS("http://www.w3.org/2000/svg", "circle")'
        result = transpile(code)
        assert 'document.createElementNS("http://www.w3.org/2000/svg", "circle")' in result
    
    def test_create_element_ns_mathml(self):
        """createElementNS for MathML should pass through."""
        code = 'math = document.createElementNS("http://www.w3.org/1998/Math/MathML", "math")'
        result = transpile(code)
        assert 'document.createElementNS(' in result
        assert '"math"' in result
    
    def test_create_text_node(self):
        """createTextNode should pass through."""
        code = 'text = document.createTextNode("Hello, World!")'
        result = transpile(code)
        assert 'document.createTextNode("Hello, World!")' in result
    
    def test_create_comment(self):
        """createComment should pass through."""
        code = 'comment = document.createComment("TODO: Add feature")'
        result = transpile(code)
        assert 'document.createComment("TODO: Add feature")' in result
    
    def test_create_document_fragment(self):
        """createDocumentFragment should pass through."""
        code = 'fragment = document.createDocumentFragment()'
        result = transpile(code)
        assert 'document.createDocumentFragment()' in result
    
    def test_create_and_append_chain(self):
        """Create element and append in chain."""
        code = '''
div = document.createElement("div")
text = document.createTextNode("Content")
div.appendChild(text)
document.body.appendChild(div)
'''
        result = transpile(code)
        assert 'document.createElement("div")' in result
        assert 'document.createTextNode("Content")' in result
        assert 'div.appendChild(text)' in result
        assert 'document.body.appendChild(div)' in result
        assert "__py." not in result


# =============================================================================
# Document Properties Tests (10 tests)
# =============================================================================

class TestDocumentProperties:
    """Tests for document property access."""
    
    def test_document_body(self):
        """document.body should pass through."""
        code = 'body = document.body'
        result = transpile(code)
        assert 'document.body' in result
    
    def test_document_head(self):
        """document.head should pass through."""
        code = 'head = document.head'
        result = transpile(code)
        assert 'document.head' in result
    
    def test_document_document_element(self):
        """document.documentElement should pass through."""
        code = 'html = document.documentElement'
        result = transpile(code)
        assert 'document.documentElement' in result
    
    def test_document_title_read(self):
        """Reading document.title should pass through."""
        code = 'title = document.title'
        result = transpile(code)
        assert 'document.title' in result
    
    def test_document_title_write(self):
        """Writing document.title should pass through."""
        code = 'document.title = "My App"'
        result = transpile(code)
        assert 'document.title = "My App"' in result
    
    def test_document_active_element(self):
        """document.activeElement should pass through."""
        code = 'focused = document.activeElement'
        result = transpile(code)
        assert 'document.activeElement' in result
    
    def test_document_ready_state(self):
        """document.readyState should pass through."""
        code = 'state = document.readyState'
        result = transpile(code)
        assert 'document.readyState' in result
    
    def test_document_hidden(self):
        """document.hidden should pass through."""
        code = 'is_hidden = document.hidden'
        result = transpile(code)
        assert 'document.hidden' in result
    
    def test_document_visibility_state(self):
        """document.visibilityState should pass through."""
        code = 'visibility = document.visibilityState'
        result = transpile(code)
        assert 'document.visibilityState' in result
    
    def test_document_cookie_read(self):
        """Reading document.cookie should pass through."""
        code = 'cookies = document.cookie'
        result = transpile(code)
        assert 'document.cookie' in result
    
    def test_document_cookie_write(self):
        """Writing document.cookie should pass through."""
        code = 'document.cookie = "name=value; path=/"'
        result = transpile(code)
        assert 'document.cookie = "name=value; path=/"' in result

