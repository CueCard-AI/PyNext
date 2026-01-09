"""
Phase 34.1: DOM Traversal Tests

Tests for Element DOM tree traversal including parent/child/sibling access,
closest(), matches(), and other navigation methods.

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# DOM Traversal Tests (20 tests)
# =============================================================================

class TestDOMTraversal:
    """Tests for DOM traversal properties and methods."""
    
    def test_parent_element(self):
        """parentElement should pass through."""
        code = 'parent = el.parentElement'
        result = transpile(code)
        assert 'el.parentElement' in result
    
    def test_parent_node(self):
        """parentNode should pass through."""
        code = 'parent = el.parentNode'
        result = transpile(code)
        assert 'el.parentNode' in result
    
    def test_children(self):
        """children should pass through."""
        code = 'kids = el.children'
        result = transpile(code)
        assert 'el.children' in result
    
    def test_child_nodes(self):
        """childNodes should pass through."""
        code = 'nodes = el.childNodes'
        result = transpile(code)
        assert 'el.childNodes' in result
    
    def test_first_element_child(self):
        """firstElementChild should pass through."""
        code = 'first = el.firstElementChild'
        result = transpile(code)
        assert 'el.firstElementChild' in result
    
    def test_last_element_child(self):
        """lastElementChild should pass through."""
        code = 'last = el.lastElementChild'
        result = transpile(code)
        assert 'el.lastElementChild' in result
    
    def test_first_child(self):
        """firstChild should pass through."""
        code = 'first = el.firstChild'
        result = transpile(code)
        assert 'el.firstChild' in result
    
    def test_last_child(self):
        """lastChild should pass through."""
        code = 'last = el.lastChild'
        result = transpile(code)
        assert 'el.lastChild' in result
    
    def test_next_element_sibling(self):
        """nextElementSibling should pass through."""
        code = 'next_el = el.nextElementSibling'
        result = transpile(code)
        assert 'el.nextElementSibling' in result
    
    def test_previous_element_sibling(self):
        """previousElementSibling should pass through."""
        code = 'prev_el = el.previousElementSibling'
        result = transpile(code)
        assert 'el.previousElementSibling' in result
    
    def test_next_sibling(self):
        """nextSibling should pass through."""
        code = 'next_node = el.nextSibling'
        result = transpile(code)
        assert 'el.nextSibling' in result
    
    def test_previous_sibling(self):
        """previousSibling should pass through."""
        code = 'prev_node = el.previousSibling'
        result = transpile(code)
        assert 'el.previousSibling' in result
    
    def test_closest_immediate(self):
        """closest() for immediate parent should work."""
        code = 'parent = el.closest(".parent")'
        result = transpile(code)
        assert 'el.closest(".parent")' in result
    
    def test_closest_ancestor(self):
        """closest() for ancestor should work."""
        code = 'container = el.closest("[data-container]")'
        result = transpile(code)
        assert 'el.closest("[data-container]")' in result
    
    def test_closest_not_found(self):
        """closest() can return null (handled in JS)."""
        code = '''
wrapper = el.closest(".wrapper")
if wrapper:
    wrapper.classList.add("found")
'''
        result = transpile(code)
        assert 'el.closest(".wrapper")' in result
    
    def test_matches_true(self):
        """matches() should pass through."""
        code = 'is_button = el.matches("button.primary")'
        result = transpile(code)
        assert 'el.matches("button.primary")' in result
    
    def test_matches_false(self):
        """matches() in condition."""
        code = '''
if el.matches(".active"):
    el.classList.remove("active")
'''
        result = transpile(code)
        assert 'el.matches(".active")' in result
    
    def test_child_element_count(self):
        """childElementCount should pass through."""
        code = 'count = el.childElementCount'
        result = transpile(code)
        assert 'el.childElementCount' in result
    
    def test_is_connected(self):
        """isConnected should pass through."""
        code = 'in_dom = el.isConnected'
        result = transpile(code)
        assert 'el.isConnected' in result
    
    def test_owner_document(self):
        """ownerDocument should pass through."""
        code = 'doc = el.ownerDocument'
        result = transpile(code)
        assert 'el.ownerDocument' in result

