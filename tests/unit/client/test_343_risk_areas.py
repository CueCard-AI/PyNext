"""
Phase 34.3: CSS Typed OM Risk Area Tests

Comprehensive tests for edge cases and risk areas:
- Unit conversion edge cases
- CSS.supports() feature detection
- CSSUnparsedValue for custom properties
- Shorthand property expansion
- Type mismatch handling
- Empty/null value handling
- Long transform chains
- Deeply nested calc()
- Serialization round-trip
- Browser fallback patterns

Total: 25 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Unit Conversion Edge Cases (4 tests)
# =============================================================================

class TestUnitConversion:
    """Tests for unit conversion with .to() method."""
    
    def test_to_same_unit(self):
        """Converting to the same unit should work (identity)."""
        code = '''
width = CSS.px(100)
same = width.to("px")
'''
        result = transpile(code)
        assert 'to("px")' in result
    
    def test_to_compatible_unit(self):
        """Converting between compatible units should work."""
        code = '''
angle_deg = CSS.deg(180)
angle_rad = angle_deg.to("rad")
'''
        result = transpile(code)
        assert 'to("rad")' in result
    
    def test_to_with_precision(self):
        """Conversion should maintain precision."""
        code = '''
centimeters = CSS.cm(2.54)
pixels = centimeters.to("px")  # 2.54cm ≈ 96px
'''
        result = transpile(code)
        assert 'CSS.cm(2.54)' in result
        assert 'to("px")' in result
    
    def test_to_method_chain(self):
        """Conversion can be chained."""
        code = '''
val = CSS.deg(180).to("rad").to("deg")
'''
        result = transpile(code)
        assert 'to("rad")' in result
        assert 'to("deg")' in result


# =============================================================================
# CSS.supports() Feature Detection (3 tests)
# =============================================================================

class TestCSSSupports:
    """Tests for CSS.supports() feature detection."""
    
    def test_supports_property_value(self):
        """CSS.supports() with property and value."""
        code = '''
if CSS.supports("display", "grid"):
    use_grid = True
'''
        result = transpile(code)
        assert 'CSS.supports("display", "grid")' in result
    
    def test_supports_condition_string(self):
        """CSS.supports() with condition string."""
        code = '''
if CSS.supports("(display: flex) and (gap: 10px)"):
    use_flex_gap = True
'''
        result = transpile(code)
        assert 'CSS.supports(' in result
    
    def test_supports_in_conditional(self):
        """CSS.supports() in ternary/conditional expression."""
        code = '''
layout = "grid" if CSS.supports("display", "grid") else "flex"
'''
        result = transpile(code)
        assert 'CSS.supports' in result


# =============================================================================
# CSSUnparsedValue for Custom Properties (3 tests)
# =============================================================================

class TestCSSUnparsedValue:
    """Tests for CSSUnparsedValue with CSS custom properties."""
    
    def test_get_custom_property(self):
        """Getting a custom property may return CSSUnparsedValue."""
        code = '''
custom = el.computedStyleMap().get("--my-spacing")
'''
        result = transpile(code)
        # Transpiler uses __py.dict.get helper for .get() calls
        assert '--my-spacing' in result
        assert 'computedStyleMap()' in result
    
    def test_custom_property_with_var(self):
        """Custom properties can contain var() references."""
        code = '''
el.attributeStyleMap.set("--derived", "calc(var(--base) + 10px)")
'''
        result = transpile(code)
        assert 'set("--derived"' in result
        assert 'var(--base)' in result
    
    def test_iterate_unparsed_tokens(self):
        """CSSUnparsedValue can be iterated for tokens."""
        code = '''
unparsed = el.computedStyleMap().get("--complex")
for token in unparsed:
    print(token)
'''
        result = transpile(code)
        assert 'for' in result


# =============================================================================
# Shorthand Property Expansion (3 tests)
# =============================================================================

class TestShorthandExpansion:
    """Tests for shorthand property expansion with getAll()."""
    
    def test_getall_margin(self):
        """getAll() on margin returns expanded values."""
        code = '''
margins = el.computedStyleMap().getAll("margin")
'''
        result = transpile(code)
        assert 'getAll("margin")' in result
    
    def test_getall_padding(self):
        """getAll() on padding returns expanded values."""
        code = '''
paddings = el.attributeStyleMap.getAll("padding")
'''
        result = transpile(code)
        assert 'getAll("padding")' in result
    
    def test_getall_iteration(self):
        """Can iterate over getAll() results."""
        code = '''
for value in el.computedStyleMap().getAll("margin"):
    total = total + value.value
'''
        result = transpile(code)
        assert 'getAll("margin")' in result


# =============================================================================
# Type Mismatch Handling (3 tests)
# =============================================================================

class TestTypeMismatch:
    """Tests for handling type mismatches gracefully."""
    
    def test_px_with_variable(self):
        """CSS.px() with a variable should transpile correctly."""
        code = '''
size = get_size()
width = CSS.px(size)
'''
        result = transpile(code)
        assert 'CSS.px(size)' in result
    
    def test_px_with_expression(self):
        """CSS.px() with an expression should work."""
        code = '''
width = CSS.px(base_width * 2)
'''
        result = transpile(code)
        assert 'CSS.px(' in result
        assert 'base_width' in result
    
    def test_factory_with_calculation(self):
        """Factory method with inline calculation."""
        code = '''
angle = CSS.deg(360 / segments)
'''
        result = transpile(code)
        assert 'CSS.deg(' in result


# =============================================================================
# Empty/Null Value Handling (3 tests)
# =============================================================================

class TestNullHandling:
    """Tests for empty/null value edge cases."""
    
    def test_get_nonexistent_property(self):
        """get() on non-existent property should be handled."""
        code = '''
value = el.attributeStyleMap.get("nonexistent-property")
if value is None:
    use_default = True
'''
        result = transpile(code)
        # Transpiler uses __py.dict.get helper for .get() calls
        assert 'nonexistent-property' in result
        assert 'attributeStyleMap' in result
        assert 'null' in result  # Python None → JS null
    
    def test_conditional_set(self):
        """Conditionally setting a style based on value."""
        code = '''
width = get_width()
if width is not None:
    el.attributeStyleMap.set("width", CSS.px(width))
'''
        result = transpile(code)
        assert 'set("width"' in result
    
    def test_optional_style_application(self):
        """Applying style only if value exists."""
        code = '''
color = theme.get("primary")
if color:
    el.attributeStyleMap.set("color", color)
'''
        result = transpile(code)
        assert 'set("color"' in result


# =============================================================================
# Long Transform Chains (2 tests)
# =============================================================================

class TestLongTransformChains:
    """Tests for very long transform chains."""
    
    def test_many_transforms_list(self):
        """CSSTransformValue with many transforms."""
        code = '''
transforms = CSSTransformValue([
    CSS.translateX(CSS.px(10)),
    CSS.translateY(CSS.px(20)),
    CSS.rotate(CSS.deg(45)),
    CSS.scale(1.5),
    CSS.skewX(CSS.deg(10)),
])
'''
        result = transpile(code)
        assert 'CSSTransformValue' in result
        assert 'translateX' in result
        assert 'rotate' in result
        assert 'scale' in result
    
    def test_transform_applied_to_element(self):
        """Long transform applied to element."""
        code = '''
el.attributeStyleMap.set("transform", CSSTransformValue([
    CSS.translate(CSS.px(100), CSS.px(50)),
    CSS.rotate(CSS.deg(45)),
    CSS.scale(2, 2),
]))
'''
        result = transpile(code)
        assert 'set("transform"' in result
        assert 'CSSTransformValue' in result


# =============================================================================
# Deeply Nested calc() (2 tests)
# =============================================================================

class TestNestedCalc:
    """Tests for deeply nested calc() expressions."""
    
    def test_nested_calc(self):
        """Nested calc() expressions should work."""
        code = '''
width = CSS.calc("calc(100% - 20px) / 2")
'''
        result = transpile(code)
        assert 'CSS.calc(' in result
        assert 'calc(100%' in result
    
    def test_complex_calc_expression(self):
        """Complex calc with multiple operations."""
        code = '''
size = CSS.calc("min(100%, 500px) - max(10px, 2vw)")
'''
        result = transpile(code)
        assert 'CSS.calc(' in result
        assert 'min(' in result
        assert 'max(' in result


# =============================================================================
# Serialization Round-Trip (2 tests)
# =============================================================================

class TestSerializationRoundTrip:
    """Tests for value → string → parse → value round-trip."""
    
    def test_tostring_and_parse(self):
        """toString() and parse() should be inverses."""
        code = '''
original = CSS.px(100)
serialized = original.toString()
parsed = CSS.parse("width", serialized)
'''
        result = transpile(code)
        assert 'toString()' in result
        assert 'CSS.parse(' in result
    
    def test_transform_tostring(self):
        """CSSTransformValue.toString() should work."""
        code = '''
transform = CSSTransformValue([CSS.rotate(CSS.deg(45))])
css_string = transform.toString()
'''
        result = transpile(code)
        assert 'CSSTransformValue' in result
        assert 'toString()' in result

