"""
Phase 34.2: classList Tests

Tests for classList operations and style utility functions:
- classList.add / remove / toggle / contains / replace
- classList.item / length / iteration
- classes() conditional class builder
- toggle_class / add_classes / remove_classes helpers

Total: 23 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# classList Basic Tests (11 tests)
# =============================================================================

class TestClassListBasic:
    """Tests for basic classList operations including item, length, and iteration."""
    
    def test_classlist_add(self):
        """classList.add should pass through unchanged."""
        code = 'el.classList.add("active")'
        result = transpile(code)
        assert 'el.classList.add("active")' in result
        assert "__py." not in result
    
    def test_classlist_add_multiple(self):
        """classList.add with multiple classes should work."""
        code = 'el.classList.add("active", "visible", "selected")'
        result = transpile(code)
        assert 'classList.add("active", "visible", "selected")' in result
    
    def test_classlist_remove(self):
        """classList.remove should pass through unchanged."""
        code = 'el.classList.remove("hidden")'
        result = transpile(code)
        assert 'el.classList.remove("hidden")' in result
    
    def test_classlist_remove_multiple(self):
        """classList.remove with multiple classes should work."""
        code = 'el.classList.remove("hidden", "disabled")'
        result = transpile(code)
        assert 'classList.remove("hidden", "disabled")' in result
    
    def test_classlist_toggle(self):
        """classList.toggle should pass through unchanged."""
        code = 'el.classList.toggle("active")'
        result = transpile(code)
        assert 'classList.toggle("active")' in result
    
    def test_classlist_toggle_force(self):
        """classList.toggle with force should work."""
        code = 'el.classList.toggle("active", True)'
        result = transpile(code)
        assert 'classList.toggle("active"' in result
        assert "True" in result or "true" in result
    
    def test_classlist_contains(self):
        """classList.contains should pass through unchanged."""
        code = 'has_active = el.classList.contains("active")'
        result = transpile(code)
        assert 'classList.contains("active")' in result
    
    def test_classlist_replace(self):
        """classList.replace should pass through unchanged."""
        code = 'el.classList.replace("old", "new")'
        result = transpile(code)
        assert 'classList.replace("old", "new")' in result
    
    def test_classlist_item(self):
        """classList.item(index) should pass through unchanged."""
        code = 'first_class = el.classList.item(0)'
        result = transpile(code)
        assert 'classList.item(0)' in result
        assert "__py." not in result
    
    def test_classlist_length(self):
        """classList.length should pass through unchanged."""
        code = 'num_classes = el.classList.length'
        result = transpile(code)
        assert 'classList.length' in result
        assert "__py." not in result
    
    def test_classlist_iteration(self):
        """Iteration over classList should transpile correctly."""
        code = '''
for cls in el.classList:
    print(cls)
'''
        result = transpile(code)
        # Should iterate over classList
        assert 'classList' in result
        assert 'for' in result.lower() or 'forEach' in result


# =============================================================================
# classes() Helper Tests (6 tests)
# =============================================================================

class TestClassesHelper:
    """Tests for classes() conditional class builder."""
    
    def test_classes_string(self):
        """classes() with strings should work."""
        code = '''
from pynext.client.style_utils import classes
cls = classes("btn", "primary")
'''
        result = transpile(code)
        assert "classes" in result
        assert '"btn"' in result
    
    def test_classes_tuple_conditional(self):
        """classes() with tuple conditional should work."""
        code = '''
from pynext.client.style_utils import classes
cls = classes("btn", ("active", is_active))
'''
        result = transpile(code)
        assert '"btn"' in result
        assert '"active"' in result
        assert "is_active" in result
    
    def test_classes_dict_conditional(self):
        """classes() with dict conditional should work."""
        code = '''
from pynext.client.style_utils import classes
cls = classes("btn", {"error": has_error, "success": is_success})
'''
        result = transpile(code)
        assert '"btn"' in result
        assert '"error"' in result
    
    def test_classes_mixed(self):
        """classes() with mixed args should work."""
        code = '''
from pynext.client.style_utils import classes
el.className = classes(
    "card",
    "shadow",
    ("active", is_selected),
    {"error": has_error},
)
'''
        result = transpile(code)
        assert '"card"' in result
        assert '"shadow"' in result
        assert '"active"' in result
    
    def test_classes_list(self):
        """classes() with list should work."""
        code = '''
from pynext.client.style_utils import classes
cls = classes("base", ["class1", "class2"])
'''
        result = transpile(code)
        assert '"base"' in result
        assert '"class1"' in result
    
    def test_classes_with_none(self):
        """classes() should ignore None values."""
        code = '''
from pynext.client.style_utils import classes
cls = classes("btn", None, "primary")
'''
        result = transpile(code)
        assert '"btn"' in result
        assert '"primary"' in result


# =============================================================================
# Style Utils Helper Tests (6 tests)
# =============================================================================

class TestStyleUtilsHelpers:
    """Tests for style utility helper functions."""
    
    def test_toggle_class(self):
        """toggle_class should work."""
        code = '''
from pynext.client.style_utils import toggle_class
toggle_class(el, "active", is_selected)
'''
        result = transpile(code)
        assert "toggle_class" in result or "classList.toggle" in result
    
    def test_add_classes(self):
        """add_classes should work."""
        code = '''
from pynext.client.style_utils import add_classes
add_classes(el, "card", "shadow", "rounded")
'''
        result = transpile(code)
        assert "add_classes" in result or "classList.add" in result
    
    def test_remove_classes(self):
        """remove_classes should work."""
        code = '''
from pynext.client.style_utils import remove_classes
remove_classes(el, "hidden", "disabled")
'''
        result = transpile(code)
        assert "remove_classes" in result or "classList.remove" in result
    
    def test_has_class(self):
        """has_class should work."""
        code = '''
from pynext.client.style_utils import has_class
if has_class(el, "active"):
    print("Active!")
'''
        result = transpile(code)
        assert "has_class" in result or "classList.contains" in result
    
    def test_replace_class(self):
        """replace_class should work."""
        code = '''
from pynext.client.style_utils import replace_class
replace_class(el, "loading", "loaded")
'''
        result = transpile(code)
        assert "replace_class" in result or "classList.replace" in result
    
    def test_set_styles(self):
        """set_styles should work."""
        code = '''
from pynext.client.style_utils import set_styles
set_styles(el, {
    "display": "flex",
    "gap": "8px",
})
'''
        result = transpile(code)
        assert "set_styles" in result or "setProperty" in result

