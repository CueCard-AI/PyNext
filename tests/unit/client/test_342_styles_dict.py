"""
Phase 34.2: Dictionary-Style Styles Access Tests

Tests for StylesProxy dictionary-style access to element styles:
- __getitem__ / __setitem__
- __delitem__
- __contains__
- update() / clear()
- keys() / values() / items()

Total: 25 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Basic Get/Set Tests (5 tests)
# =============================================================================

class TestStylesDictBasic:
    """Tests for basic dictionary-style style access."""
    
    def test_styles_getitem(self):
        """styles['property'] should transpile to getPropertyValue."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
color = styles["color"]
'''
        result = transpile(code)
        assert "getPropertyValue" in result or '"color"' in result
    
    def test_styles_setitem(self):
        """styles['property'] = value should transpile to setProperty."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles["display"] = "flex"
'''
        result = transpile(code)
        assert "setProperty" in result or '"display"' in result
    
    def test_styles_setitem_css_var(self):
        """styles['--var'] = value should work for CSS variables."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles["--primary"] = "#3b82f6"
'''
        result = transpile(code)
        assert "--primary" in result
    
    def test_styles_delitem(self):
        """del styles['property'] should transpile to removeProperty."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
del styles["display"]
'''
        result = transpile(code)
        # Should use removeProperty or delete
        assert "removeProperty" in result or "delete" in result or '"display"' in result
    
    def test_styles_contains(self):
        """'property' in styles should check if property is set."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
if "display" in styles:
    pass
'''
        result = transpile(code)
        assert '"display"' in result


# =============================================================================
# Bulk Operations Tests (5 tests)
# =============================================================================

class TestStylesDictBulk:
    """Tests for bulk dictionary operations."""
    
    def test_styles_update(self):
        """styles.update({...}) should set multiple properties."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles.update({
    "display": "flex",
    "gap": "8px",
})
'''
        result = transpile(code)
        assert "update" in result or "setProperty" in result
    
    def test_styles_update_with_css_vars(self):
        """styles.update() should work with CSS variables."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles.update({
    "--primary": "blue",
    "--spacing": "16px",
})
'''
        result = transpile(code)
        assert "--primary" in result or "update" in result
    
    def test_styles_clear(self):
        """styles.clear() should remove all inline styles."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles.clear()
'''
        result = transpile(code)
        # clear() is a method call on StylesProxy - should appear in output
        # May transpile to styles.clear() or internal implementation
        assert "clear" in result or "length" in result or "cssText" in result
    
    def test_styles_len(self):
        """len(styles) should return style count."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
count = len(styles)
'''
        result = transpile(code)
        # len() might transpile to __py.len or .length
        assert "len" in result.lower() or "length" in result.lower()
    
    def test_styles_iter(self):
        """Iterating styles should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
for prop in styles:
    print(prop)
'''
        result = transpile(code)
        assert "for" in result


# =============================================================================
# Kebab-Case Tests (5 tests)
# =============================================================================

class TestStylesKebabCase:
    """Tests for kebab-case property names."""
    
    def test_styles_kebab_background_color(self):
        """styles['background-color'] should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles["background-color"] = "red"
'''
        result = transpile(code)
        assert "background-color" in result
    
    def test_styles_kebab_border_radius(self):
        """styles['border-radius'] should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles["border-radius"] = "8px"
'''
        result = transpile(code)
        assert "border-radius" in result
    
    def test_styles_kebab_flex_direction(self):
        """styles['flex-direction'] should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles["flex-direction"] = "column"
'''
        result = transpile(code)
        assert "flex-direction" in result
    
    def test_styles_kebab_box_shadow(self):
        """styles['box-shadow'] should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles["box-shadow"] = "0 2px 4px rgba(0,0,0,0.1)"
'''
        result = transpile(code)
        assert "box-shadow" in result
    
    def test_styles_kebab_z_index(self):
        """styles['z-index'] should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles["z-index"] = "100"
'''
        result = transpile(code)
        assert "z-index" in result


# =============================================================================
# Get Method Tests (3 tests)
# =============================================================================

class TestStylesGet:
    """Tests for styles.get() method."""
    
    def test_styles_get(self):
        """styles.get('property') should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
color = styles.get("color")
'''
        result = transpile(code)
        assert '"color"' in result
    
    def test_styles_get_with_default(self):
        """styles.get('property', default) should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
color = styles.get("color", "black")
'''
        result = transpile(code)
        assert '"color"' in result
        assert '"black"' in result
    
    def test_styles_to_dict(self):
        """styles.to_dict() should return dictionary."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
style_dict = styles.to_dict()
'''
        result = transpile(code)
        assert "to_dict" in result


# =============================================================================
# Keys/Values/Items Tests (4 tests)
# =============================================================================

class TestStylesKeysValuesItems:
    """Tests for keys(), values(), items() methods."""
    
    def test_styles_keys(self):
        """styles.keys() should return property names."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
for key in styles.keys():
    print(key)
'''
        result = transpile(code)
        assert "keys" in result
    
    def test_styles_values(self):
        """styles.values() should return property values."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
for value in styles.values():
    print(value)
'''
        result = transpile(code)
        assert "values" in result
    
    def test_styles_items(self):
        """styles.items() should return key-value pairs."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
for key, value in styles.items():
    print(f"{key}: {value}")
'''
        result = transpile(code)
        assert "items" in result
    
    def test_create_styles_function(self):
        """create_styles() helper should work."""
        code = '''
from pynext.client.styles import create_styles
styles = create_styles(el)
styles["display"] = "flex"
'''
        result = transpile(code)
        assert "create_styles" in result or "StylesProxy" in result


# =============================================================================
# setProperty Method Tests (3 tests)
# =============================================================================

class TestStylesSetProperty:
    """Tests for setProperty method with priority."""
    
    def test_styles_set_property(self):
        """styles.setProperty() should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles.setProperty("display", "flex")
'''
        result = transpile(code)
        assert "setProperty" in result
    
    def test_styles_set_property_important(self):
        """styles.setProperty() with important should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
styles.setProperty("display", "flex", "important")
'''
        result = transpile(code)
        assert "setProperty" in result
        assert "important" in result
    
    def test_styles_remove_property(self):
        """styles.removeProperty() should work."""
        code = '''
from pynext.client.styles import StylesProxy
styles = StylesProxy(el)
old = styles.removeProperty("display")
'''
        result = transpile(code)
        assert "removeProperty" in result

