"""
Phase 34.3: CSS Typed OM Complete Coverage Tests

Additional tests for complete coverage:
- CSS.escape() for identifier escaping
- DOMMatrix operations
- Animation integration with typed values
- Type checking/narrowing
- matchMedia with typed values

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# CSS.escape() Tests (3 tests)
# =============================================================================

class TestCSSEscape:
    """Tests for CSS.escape() identifier escaping."""
    
    def test_escape_special_characters(self):
        """CSS.escape() should escape special characters in selectors."""
        code = '''
safe_id = CSS.escape("my#special.class")
el = document.querySelector("#" + safe_id)
'''
        result = transpile(code)
        assert 'CSS.escape(' in result
        assert 'my#special.class' in result
    
    def test_escape_with_template(self):
        """CSS.escape() in template string."""
        code = '''
user_id = get_user_id()
safe_id = CSS.escape(user_id)
'''
        result = transpile(code)
        assert 'CSS.escape(user_id)' in result
    
    def test_escape_in_queryselector(self):
        """CSS.escape() used directly in querySelector."""
        code = '''
el = document.querySelector("[data-id='" + CSS.escape(item_id) + "']")
'''
        result = transpile(code)
        assert 'CSS.escape(item_id)' in result
        assert 'querySelector' in result


# =============================================================================
# DOMMatrix Operations Tests (4 tests)
# =============================================================================

class TestDOMMatrixOperations:
    """Tests for DOMMatrix arithmetic operations."""
    
    def test_matrix_inverse(self):
        """matrix.inverse() should pass through."""
        code = '''
transform = CSSTransformValue([CSS.rotate(CSS.deg(45))])
matrix = transform.toMatrix()
inverted = matrix.inverse()
'''
        result = transpile(code)
        assert 'toMatrix()' in result
        assert 'inverse()' in result
    
    def test_matrix_multiply(self):
        """matrix.multiply(other) should pass through."""
        code = '''
m1 = transform1.toMatrix()
m2 = transform2.toMatrix()
combined = m1.multiply(m2)
'''
        result = transpile(code)
        assert 'multiply(' in result
    
    def test_matrix_transform_point(self):
        """matrix.transformPoint() should pass through."""
        code = '''
matrix = transform.toMatrix()
point = matrix.transformPoint({"x": 10, "y": 20})
'''
        result = transpile(code)
        assert 'transformPoint(' in result
    
    def test_matrix_scale_method(self):
        """matrix.scale() should pass through."""
        code = '''
matrix = transform.toMatrix()
scaled = matrix.scale(2, 2)
'''
        result = transpile(code)
        assert 'toMatrix()' in result
        assert 'scale(2, 2)' in result


# =============================================================================
# Animation Integration Tests (3 tests)
# =============================================================================

class TestAnimationIntegration:
    """Tests for integrating CSS Typed OM with Web Animations API."""
    
    def test_animate_with_typed_duration(self):
        """element.animate() with typed duration value."""
        code = '''
duration = CSS.ms(300)
el.animate(keyframes, {"duration": duration.value})
'''
        result = transpile(code)
        assert 'CSS.ms(300)' in result
        assert 'animate(' in result
        assert 'duration.value' in result
    
    def test_animate_with_typed_transform(self):
        """Using typed transforms in animation keyframes."""
        code = '''
start_pos = CSS.translate(CSS.px(0), CSS.px(0))
end_pos = CSS.translate(CSS.px(100), CSS.px(50))
'''
        result = transpile(code)
        assert 'CSS.translate' in result
        assert 'CSS.px(0)' in result
        assert 'CSS.px(100)' in result
    
    def test_animate_timing_with_seconds(self):
        """Using CSS.s() for animation timing."""
        code = '''
duration = CSS.s(0.5)
delay = CSS.s(0.1)
options = {"duration": duration.value * 1000, "delay": delay.value * 1000}
'''
        result = transpile(code)
        assert 'CSS.s(0.5)' in result
        assert 'CSS.s(0.1)' in result
        assert 'duration.value' in result


# =============================================================================
# Type Checking/Narrowing Tests (3 tests)
# =============================================================================

class TestTypeNarrowing:
    """Tests for type checking CSS values."""
    
    def test_isinstance_cssunitvalue(self):
        """isinstance check for CSSUnitValue."""
        code = '''
value = style_map.get("width")
if isinstance(value, CSSUnitValue):
    print(value.value, value.unit)
'''
        result = transpile(code)
        assert 'CSSUnitValue' in result
    
    def test_isinstance_csskeywordvalue(self):
        """isinstance check for CSSKeywordValue."""
        code = '''
value = style_map.get("display")
if isinstance(value, CSSKeywordValue):
    print(value.value)
'''
        result = transpile(code)
        assert 'CSSKeywordValue' in result
    
    def test_type_based_dispatch(self):
        """Type-based dispatch on CSS values."""
        code = '''
value = el.computedStyleMap().get("width")
if isinstance(value, CSSUnitValue):
    width_px = value.value
elif isinstance(value, CSSKeywordValue):
    width_px = 0 if value.value == "auto" else None
'''
        result = transpile(code)
        assert 'CSSUnitValue' in result
        assert 'CSSKeywordValue' in result


# =============================================================================
# matchMedia with Typed Values Tests (2 tests)
# =============================================================================

class TestMatchMediaTypedValues:
    """Tests for matchMedia with typed values."""
    
    def test_matchmedia_responsive_styles(self):
        """Using matchMedia with typed style application."""
        code = '''
if window.matchMedia("(min-width: 768px)").matches:
    el.attributeStyleMap.set("width", CSS.px(800))
else:
    el.attributeStyleMap.set("width", CSS.percent(100))
'''
        result = transpile(code)
        assert 'matchMedia' in result
        assert 'CSS.px(800)' in result
        assert 'CSS.percent(100)' in result
    
    def test_matchmedia_listener_with_styles(self):
        """matchMedia change listener with typed styles."""
        code = '''
query = window.matchMedia("(prefers-color-scheme: dark)")
def on_change(e):
    if e.matches:
        el.attributeStyleMap.set("background-color", CSS.keyword("black"))
'''
        result = transpile(code)
        assert 'matchMedia' in result
        assert 'prefers-color-scheme' in result

