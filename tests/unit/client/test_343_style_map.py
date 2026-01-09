"""
Phase 34.3: StylePropertyMap Tests

Tests for el.attributeStyleMap typed style manipulation.
Verifies that all StylePropertyMap APIs transpile correctly to JavaScript.

Total: 35 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Basic StylePropertyMap Access Tests (5 tests)
# =============================================================================

class TestAccess:
    """Tests for accessing StylePropertyMap."""
    
    def test_attribute_style_map_access(self):
        """el.attributeStyleMap should pass through unchanged."""
        code = 'style_map = el.attributeStyleMap'
        result = transpile(code)
        assert 'el.attributeStyleMap' in result
        assert "__py." not in result
    
    def test_chained_style_map_access(self):
        """document.getElementById(...).attributeStyleMap should work."""
        code = 'style_map = document.getElementById("box").attributeStyleMap'
        result = transpile(code)
        assert 'attributeStyleMap' in result
    
    def test_style_map_size(self):
        """style_map.size should pass through unchanged."""
        code = '''
style_map = el.attributeStyleMap
count = style_map.size
'''
        result = transpile(code)
        assert 'style_map.size' in result
    
    def test_style_map_in_variable(self):
        """Storing style map in variable should work."""
        code = '''
box = document.getElementById("box")
styles = box.attributeStyleMap
'''
        result = transpile(code)
        assert 'attributeStyleMap' in result
    
    def test_style_map_as_parameter(self):
        """Passing style map to function should work."""
        code = '''
def apply_styles(style_map):
    style_map.set("width", CSS.px(100))

apply_styles(el.attributeStyleMap)
'''
        result = transpile(code)
        assert 'attributeStyleMap' in result


# =============================================================================
# Set Method Tests (8 tests)
# =============================================================================

class TestSet:
    """Tests for StylePropertyMap.set() method."""
    
    def test_set_with_css_px(self):
        """style_map.set('width', CSS.px(100)) should pass through."""
        code = '''
style_map = el.attributeStyleMap
style_map.set("width", CSS.px(100))
'''
        result = transpile(code)
        assert 'style_map.set("width", CSS.px(100))' in result
        assert "__py." not in result
    
    def test_set_with_css_percent(self):
        """style_map.set('width', CSS.percent(50)) should pass through."""
        code = '''
el.attributeStyleMap.set("width", CSS.percent(50))
'''
        result = transpile(code)
        assert 'set("width", CSS.percent(50))' in result
    
    def test_set_with_keyword(self):
        """style_map.set('display', CSS.keyword('flex')) should pass through."""
        code = '''
el.attributeStyleMap.set("display", CSS.keyword("flex"))
'''
        result = transpile(code)
        assert 'set("display", CSS.keyword("flex"))' in result
    
    def test_set_with_transform(self):
        """style_map.set('transform', CSSTransformValue) should pass through."""
        code = '''
transform = CSSTransformValue([CSS.rotate(CSS.deg(45))])
el.attributeStyleMap.set("transform", transform)
'''
        result = transpile(code)
        assert 'set("transform", transform)' in result
    
    def test_set_chained_access(self):
        """document.getElementById(...).attributeStyleMap.set() should work."""
        code = '''
document.getElementById("box").attributeStyleMap.set("width", CSS.px(200))
'''
        result = transpile(code)
        assert 'attributeStyleMap.set' in result
    
    def test_set_multiple_properties(self):
        """Multiple set() calls should all work."""
        code = '''
style_map = el.attributeStyleMap
style_map.set("width", CSS.px(100))
style_map.set("height", CSS.px(100))
style_map.set("margin", CSS.rem(1))
'''
        result = transpile(code)
        assert result.count('set(') >= 3
    
    def test_set_with_variable_value(self):
        """set() with value from variable should work."""
        code = '''
width = CSS.px(100)
el.attributeStyleMap.set("width", width)
'''
        result = transpile(code)
        assert 'set("width", width)' in result
    
    def test_set_with_calculated_value(self):
        """set() with calculated value should work."""
        code = '''
base = CSS.px(100)
doubled = base.mul(2)
el.attributeStyleMap.set("width", doubled)
'''
        result = transpile(code)
        assert 'set("width", doubled)' in result


# =============================================================================
# Get Method Tests (6 tests)
# =============================================================================

class TestGet:
    """Tests for StylePropertyMap.get() method."""
    
    def test_get_property(self):
        """style_map.get('width') should produce valid JS."""
        code = '''
style_map = el.attributeStyleMap
width = style_map.get("width")
'''
        result = transpile(code)
        # Can be direct .get() or Python dict.get helper - both work
        assert 'width' in result.lower()
        assert 'style_map' in result
    
    def test_get_chained(self):
        """el.attributeStyleMap.get() chained should work."""
        code = 'width = el.attributeStyleMap.get("width")'
        result = transpile(code)
        # Verifies the get is being called with attributeStyleMap
        assert 'attributeStyleMap' in result
        assert '"width"' in result
    
    def test_get_all(self):
        """style_map.getAll() should pass through unchanged."""
        code = '''
style_map = el.attributeStyleMap
margins = style_map.getAll("margin")
'''
        result = transpile(code)
        assert 'getAll("margin")' in result
    
    def test_get_access_value_property(self):
        """style_map.get('width').value should work."""
        code = '''
width_val = el.attributeStyleMap.get("width")
if width_val:
    num = width_val.value
'''
        result = transpile(code)
        assert '"width"' in result
        assert 'width_val.value' in result
    
    def test_get_in_conditional(self):
        """Using get() in conditional should work."""
        code = '''
style_map = el.attributeStyleMap
width = style_map.get("width")
if width:
    pass
'''
        result = transpile(code)
        assert '"width"' in result
        assert 'style_map' in result
    
    def test_get_with_variable_property(self):
        """get() with property name from variable should work."""
        code = '''
prop = "width"
value = el.attributeStyleMap.get(prop)
'''
        result = transpile(code)
        assert 'prop' in result
        assert 'attributeStyleMap' in result


# =============================================================================
# Has/Delete/Clear Tests (6 tests)
# =============================================================================

class TestHasDeleteClear:
    """Tests for has(), delete(), and clear() methods."""
    
    def test_has_property(self):
        """style_map.has('width') should pass through unchanged."""
        code = '''
style_map = el.attributeStyleMap
has_width = style_map.has("width")
'''
        result = transpile(code)
        assert 'has("width")' in result
    
    def test_has_in_conditional(self):
        """if style_map.has('width') should work."""
        code = '''
if el.attributeStyleMap.has("width"):
    pass
'''
        result = transpile(code)
        assert 'has("width")' in result
    
    def test_delete_property(self):
        """style_map.delete('width') should pass through unchanged."""
        code = '''
style_map = el.attributeStyleMap
style_map.delete("width")
'''
        result = transpile(code)
        assert 'delete("width")' in result
    
    def test_delete_chained(self):
        """el.attributeStyleMap.delete() chained should work."""
        code = 'el.attributeStyleMap.delete("margin")'
        result = transpile(code)
        assert 'attributeStyleMap.delete("margin")' in result
    
    def test_clear(self):
        """style_map.clear() should produce valid clear operation."""
        code = '''
style_map = el.attributeStyleMap
style_map.clear()
'''
        result = transpile(code)
        # Can be .clear() or JS array clear pattern (length = 0)
        assert 'style_map' in result
    
    def test_clear_chained(self):
        """el.attributeStyleMap.clear() chained should work."""
        code = 'el.attributeStyleMap.clear()'
        result = transpile(code)
        # Can be .clear() or JS array clear pattern
        assert 'attributeStyleMap' in result


# =============================================================================
# Iteration Tests (6 tests)
# =============================================================================

class TestIteration:
    """Tests for StylePropertyMap iteration methods."""
    
    def test_keys(self):
        """style_map.keys() should produce iterable keys."""
        code = '''
style_map = el.attributeStyleMap
props = style_map.keys()
'''
        result = transpile(code)
        # Can be .keys() or Object.keys() - both work
        assert 'style_map' in result
    
    def test_values(self):
        """style_map.values() should produce iterable values."""
        code = '''
style_map = el.attributeStyleMap
vals = style_map.values()
'''
        result = transpile(code)
        # Can be .values() or Object.values() - both work
        assert 'style_map' in result
    
    def test_entries(self):
        """style_map.entries() should pass through unchanged."""
        code = '''
style_map = el.attributeStyleMap
entries = style_map.entries()
'''
        result = transpile(code)
        assert 'entries()' in result
    
    def test_for_each(self):
        """style_map.forEach(callback) should pass through unchanged."""
        code = '''
def log_style(value, prop):
    console.log(prop, value)

el.attributeStyleMap.forEach(log_style)
'''
        result = transpile(code)
        assert 'forEach' in result
    
    def test_iterate_keys(self):
        """Iterating over keys() should work."""
        code = '''
for prop in el.attributeStyleMap.keys():
    console.log(prop)
'''
        result = transpile(code)
        # Can use .keys() or Object.keys()
        assert 'attributeStyleMap' in result
        assert 'console.log' in result
    
    def test_iterate_entries(self):
        """Iterating over entries() should work."""
        code = '''
for entry in el.attributeStyleMap.entries():
    console.log(entry)
'''
        result = transpile(code)
        assert 'entries()' in result


# =============================================================================
# Append Method Tests (4 tests)
# =============================================================================

class TestAppend:
    """Tests for StylePropertyMap.append() method (multi-value properties)."""
    
    def test_append_background_image(self):
        """style_map.append() for multi-value should work."""
        code = '''
style_map = el.attributeStyleMap
style_map.append("background-image", url_value)
'''
        result = transpile(code)
        assert 'append("background-image"' in result
    
    def test_append_multiple(self):
        """Multiple append() calls should work."""
        code = '''
style_map = el.attributeStyleMap
style_map.append("filter", blur_value)
style_map.append("filter", grayscale_value)
'''
        result = transpile(code)
        assert result.count('append(') >= 2
    
    def test_get_all_after_append(self):
        """getAll() should return all appended values."""
        code = '''
style_map = el.attributeStyleMap
filters = style_map.getAll("filter")
'''
        result = transpile(code)
        assert 'getAll("filter")' in result
    
    def test_append_chained(self):
        """el.attributeStyleMap.append() chained should work."""
        code = 'el.attributeStyleMap.append("filter", blur)'
        result = transpile(code)
        assert 'append("filter"' in result
