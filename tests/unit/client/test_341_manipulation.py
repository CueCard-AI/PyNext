"""
Phase 34.1: DOM Manipulation Tests

Tests for Element DOM manipulation including appendChild, remove, cloneNode,
and other mutation methods.

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# DOM Manipulation Tests (15 tests)
# =============================================================================

class TestDOMManipulation:
    """Tests for DOM manipulation methods."""
    
    def test_append_child(self):
        """appendChild should pass through."""
        code = 'parent.appendChild(child)'
        result = transpile(code)
        assert 'parent.appendChild(child)' in result
    
    def test_insert_before(self):
        """insertBefore should pass through."""
        code = 'parent.insertBefore(new_child, reference)'
        result = transpile(code)
        assert 'parent.insertBefore(new_child, reference)' in result
    
    def test_remove_child(self):
        """removeChild should pass through."""
        code = 'removed = parent.removeChild(child)'
        result = transpile(code)
        assert 'parent.removeChild(child)' in result
    
    def test_replace_child(self):
        """replaceChild should pass through."""
        code = 'old = parent.replaceChild(new_child, old_child)'
        result = transpile(code)
        assert 'parent.replaceChild(new_child, old_child)' in result
    
    def test_remove_self(self):
        """remove() on element should pass through."""
        code = 'el.remove()'
        result = transpile(code)
        assert 'el.remove()' in result
    
    def test_clone_node_shallow(self):
        """cloneNode() shallow should pass through."""
        code = 'clone = el.cloneNode()'
        result = transpile(code)
        assert 'el.cloneNode()' in result
    
    def test_clone_node_deep(self):
        """cloneNode(True) deep should pass through."""
        code = 'clone = el.cloneNode(True)'
        result = transpile(code)
        assert 'el.cloneNode(true)' in result
    
    def test_append_multiple(self):
        """append() with multiple nodes should pass through."""
        code = 'el.append(child1, child2, child3)'
        result = transpile(code)
        assert 'el.append(child1, child2, child3)' in result
    
    def test_append_with_string(self):
        """append() with string - Note: single-arg append is ambiguous with list.append().
        
        The transpiler converts single-arg append to push() for Python list semantics.
        To use DOM append with a single argument, use the explicit form with multiple args
        or rely on the runtime.
        """
        code = 'el.append("text1", "text2")'  # Multiple args clearly indicates DOM append
        result = transpile(code)
        assert 'el.append("text1", "text2")' in result
    
    def test_prepend(self):
        """prepend() should pass through."""
        code = 'el.prepend(header)'
        result = transpile(code)
        assert 'el.prepend(header)' in result
    
    def test_after(self):
        """after() should pass through."""
        code = 'el.after(sibling)'
        result = transpile(code)
        assert 'el.after(sibling)' in result
    
    def test_before(self):
        """before() should pass through."""
        code = 'el.before(sibling)'
        result = transpile(code)
        assert 'el.before(sibling)' in result
    
    def test_replace_with(self):
        """replaceWith() should pass through."""
        code = 'el.replaceWith(new_element)'
        result = transpile(code)
        assert 'el.replaceWith(new_element)' in result
    
    def test_replace_children(self):
        """replaceChildren() should pass through."""
        code = 'el.replaceChildren(child1, child2)'
        result = transpile(code)
        assert 'el.replaceChildren(child1, child2)' in result
    
    def test_focus(self):
        """focus() should pass through."""
        code = 'input_el.focus()'
        result = transpile(code)
        assert 'input_el.focus()' in result
    
    def test_blur(self):
        """blur() should pass through."""
        code = 'input_el.blur()'
        result = transpile(code)
        assert 'input_el.blur()' in result
    
    def test_click(self):
        """click() should pass through."""
        code = 'button.click()'
        result = transpile(code)
        assert 'button.click()' in result


class TestComplexManipulation:
    """Tests for complex DOM manipulation patterns."""
    
    def test_create_and_insert(self):
        """Creating and inserting elements should work."""
        code = '''
li = document.createElement("li")
li.textContent = "New item"
li.classList.add("list-item")
ul.appendChild(li)
'''
        result = transpile(code)
        assert 'document.createElement("li")' in result
        assert 'li.textContent = "New item"' in result
        assert 'li.classList.add("list-item")' in result
        assert 'ul.appendChild(li)' in result
        assert "__py." not in result
    
    def test_fragment_batch_insert(self):
        """Using DocumentFragment for batch inserts."""
        code = '''
fragment = document.createDocumentFragment()
for i in range(10):
    item = document.createElement("div")
    item.textContent = str(i)
    fragment.appendChild(item)
container.appendChild(fragment)
'''
        result = transpile(code)
        assert 'document.createDocumentFragment()' in result
        assert 'document.createElement("div")' in result
        assert 'fragment.appendChild(item)' in result
        assert 'container.appendChild(fragment)' in result

