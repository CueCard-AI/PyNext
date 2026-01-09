"""
Phase 34.1: Element Attributes Tests

Tests for Element attribute manipulation including getAttribute, setAttribute,
classList, and dataset.

Test Categories:
- Attribute Methods (10 tests): get/set/remove/hasAttribute, toggleAttribute
- Dataset (3 tests): data-* attribute access
- ClassList (7 tests): add, remove, toggle, contains, replace

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Attribute Method Tests (10 tests)
# =============================================================================

class TestElementAttributes:
    """Tests for element attribute methods."""
    
    def test_get_attribute(self):
        """getAttribute should pass through unchanged."""
        code = 'href = el.getAttribute("href")'
        result = transpile(code)
        assert 'el.getAttribute("href")' in result
        assert "__py." not in result
    
    def test_set_attribute(self):
        """setAttribute should pass through unchanged."""
        code = 'el.setAttribute("data-id", "123")'
        result = transpile(code)
        assert 'el.setAttribute("data-id", "123")' in result
    
    def test_remove_attribute(self):
        """removeAttribute should pass through unchanged."""
        code = 'el.removeAttribute("disabled")'
        result = transpile(code)
        assert 'el.removeAttribute("disabled")' in result
    
    def test_has_attribute_true(self):
        """hasAttribute should pass through unchanged."""
        code = 'has_id = el.hasAttribute("id")'
        result = transpile(code)
        assert 'el.hasAttribute("id")' in result
    
    def test_has_attribute_false(self):
        """hasAttribute in condition should work."""
        code = '''
if el.hasAttribute("disabled"):
    el.removeAttribute("disabled")
'''
        result = transpile(code)
        assert 'el.hasAttribute("disabled")' in result
        assert 'el.removeAttribute("disabled")' in result
    
    def test_toggle_attribute_on(self):
        """toggleAttribute without force should pass through."""
        code = 'el.toggleAttribute("hidden")'
        result = transpile(code)
        assert 'el.toggleAttribute("hidden")' in result
    
    def test_toggle_attribute_off(self):
        """toggleAttribute can toggle off."""
        code = 'was_on = el.toggleAttribute("readonly")'
        result = transpile(code)
        assert 'el.toggleAttribute("readonly")' in result
    
    def test_toggle_attribute_force_true(self):
        """toggleAttribute with force=True should pass through."""
        code = 'el.toggleAttribute("disabled", True)'
        result = transpile(code)
        assert 'el.toggleAttribute("disabled", true)' in result
    
    def test_toggle_attribute_force_false(self):
        """toggleAttribute with force=False should pass through."""
        code = 'el.toggleAttribute("disabled", False)'
        result = transpile(code)
        assert 'el.toggleAttribute("disabled", false)' in result
    
    def test_get_attribute_names(self):
        """getAttributeNames should pass through unchanged."""
        code = 'attrs = el.getAttributeNames()'
        result = transpile(code)
        assert 'el.getAttributeNames()' in result


# =============================================================================
# Dataset Tests (3 tests)
# =============================================================================

class TestElementDataset:
    """Tests for element dataset (data-* attributes)."""
    
    def test_dataset_read_single(self):
        """Reading from dataset should pass through."""
        code = 'user_id = el.dataset.userId'
        result = transpile(code)
        assert 'el.dataset.userId' in result
    
    def test_dataset_read_camel_case(self):
        """Dataset camelCase should work."""
        code = 'item_name = el.dataset.itemName'
        result = transpile(code)
        assert 'el.dataset.itemName' in result
    
    def test_dataset_write(self):
        """Writing to dataset should pass through."""
        code = 'el.dataset.role = "admin"'
        result = transpile(code)
        assert 'el.dataset.role = "admin"' in result


# =============================================================================
# ClassList Tests (7 tests)
# =============================================================================

class TestElementClassList:
    """Tests for element classList."""
    
    def test_class_list_add(self):
        """classList.add should pass through unchanged."""
        code = 'el.classList.add("active")'
        result = transpile(code)
        assert 'el.classList.add("active")' in result
    
    def test_class_list_add_multiple(self):
        """classList.add with multiple classes."""
        code = 'el.classList.add("active", "visible", "highlighted")'
        result = transpile(code)
        assert 'el.classList.add("active", "visible", "highlighted")' in result
    
    def test_class_list_remove(self):
        """classList.remove should pass through unchanged."""
        code = 'el.classList.remove("hidden")'
        result = transpile(code)
        assert 'el.classList.remove("hidden")' in result
    
    def test_class_list_toggle(self):
        """classList.toggle should pass through unchanged."""
        code = 'el.classList.toggle("active")'
        result = transpile(code)
        assert 'el.classList.toggle("active")' in result
    
    def test_class_list_toggle_force(self):
        """classList.toggle with force should pass through."""
        code = 'el.classList.toggle("visible", True)'
        result = transpile(code)
        assert 'el.classList.toggle("visible", true)' in result
    
    def test_class_list_contains(self):
        """classList.contains should pass through unchanged."""
        code = 'has_active = el.classList.contains("active")'
        result = transpile(code)
        assert 'el.classList.contains("active")' in result
    
    def test_class_list_replace(self):
        """classList.replace should pass through unchanged."""
        code = 'el.classList.replace("old-class", "new-class")'
        result = transpile(code)
        assert 'el.classList.replace("old-class", "new-class")' in result
    
    def test_class_name_read(self):
        """className read should pass through."""
        code = 'classes = el.className'
        result = transpile(code)
        assert 'el.className' in result
    
    def test_class_name_write(self):
        """className write should pass through."""
        code = 'el.className = "foo bar baz"'
        result = transpile(code)
        assert 'el.className = "foo bar baz"' in result

