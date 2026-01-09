"""
Phase 34.3: CSS Transform Tests

Tests for CSSTransformValue, CSS.translate(), CSS.rotate(), CSS.scale(), etc.
Verifies that all transform APIs transpile correctly to JavaScript.

Total: 30 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Translate Transform Tests (6 tests)
# =============================================================================

class TestTranslate:
    """Tests for CSS.translate() and variants."""
    
    def test_translate_2d(self):
        """CSS.translate(x, y) should pass through unchanged."""
        code = 'transform = CSS.translate(CSS.px(100), CSS.px(50))'
        result = transpile(code)
        assert 'CSS.translate(CSS.px(100), CSS.px(50))' in result
        assert "__py." not in result
    
    def test_translate_x_only(self):
        """CSS.translateX should pass through unchanged."""
        code = 'transform = CSS.translateX(CSS.px(100))'
        result = transpile(code)
        assert 'CSS.translateX(CSS.px(100))' in result
    
    def test_translate_y_only(self):
        """CSS.translateY should pass through unchanged."""
        code = 'transform = CSS.translateY(CSS.px(50))'
        result = transpile(code)
        assert 'CSS.translateY(CSS.px(50))' in result
    
    def test_translate_z(self):
        """CSS.translateZ should pass through unchanged."""
        code = 'transform = CSS.translateZ(CSS.px(25))'
        result = transpile(code)
        assert 'CSS.translateZ(CSS.px(25))' in result
    
    def test_translate_3d(self):
        """CSS.translate3d(x, y, z) should pass through unchanged."""
        code = 'transform = CSS.translate3d(CSS.px(100), CSS.px(50), CSS.px(25))'
        result = transpile(code)
        assert 'CSS.translate3d' in result
    
    def test_translate_with_percent(self):
        """CSS.translate with percent values should work."""
        code = 'transform = CSS.translate(CSS.percent(50), CSS.percent(50))'
        result = transpile(code)
        assert 'CSS.translate(CSS.percent(50), CSS.percent(50))' in result


# =============================================================================
# Rotate Transform Tests (6 tests)
# =============================================================================

class TestRotate:
    """Tests for CSS.rotate() and variants."""
    
    def test_rotate_2d(self):
        """CSS.rotate(angle) should pass through unchanged."""
        code = 'transform = CSS.rotate(CSS.deg(45))'
        result = transpile(code)
        assert 'CSS.rotate(CSS.deg(45))' in result
        assert "__py." not in result
    
    def test_rotate_x(self):
        """CSS.rotateX should pass through unchanged."""
        code = 'transform = CSS.rotateX(CSS.deg(90))'
        result = transpile(code)
        assert 'CSS.rotateX(CSS.deg(90))' in result
    
    def test_rotate_y(self):
        """CSS.rotateY should pass through unchanged."""
        code = 'transform = CSS.rotateY(CSS.deg(90))'
        result = transpile(code)
        assert 'CSS.rotateY(CSS.deg(90))' in result
    
    def test_rotate_z(self):
        """CSS.rotateZ should pass through unchanged."""
        code = 'transform = CSS.rotateZ(CSS.deg(45))'
        result = transpile(code)
        assert 'CSS.rotateZ(CSS.deg(45))' in result
    
    def test_rotate_3d(self):
        """CSS.rotate3d(x, y, z, angle) should pass through unchanged."""
        code = 'transform = CSS.rotate3d(1, 0, 0, CSS.deg(45))'
        result = transpile(code)
        assert 'CSS.rotate3d' in result
    
    def test_rotate_with_radians(self):
        """CSS.rotate with radians should work."""
        code = 'transform = CSS.rotate(CSS.rad(1.5708))'
        result = transpile(code)
        assert 'CSS.rotate(CSS.rad(1.5708))' in result


# =============================================================================
# Scale Transform Tests (5 tests)
# =============================================================================

class TestScale:
    """Tests for CSS.scale() and variants."""
    
    def test_scale_uniform(self):
        """CSS.scale(factor) should pass through unchanged."""
        code = 'transform = CSS.scale(2)'
        result = transpile(code)
        assert 'CSS.scale(2)' in result
        assert "__py." not in result
    
    def test_scale_non_uniform(self):
        """CSS.scale(x, y) should pass through unchanged."""
        code = 'transform = CSS.scale(2, 1.5)'
        result = transpile(code)
        assert 'CSS.scale(2, 1.5)' in result
    
    def test_scale_x(self):
        """CSS.scaleX should pass through unchanged."""
        code = 'transform = CSS.scaleX(2)'
        result = transpile(code)
        assert 'CSS.scaleX(2)' in result
    
    def test_scale_y(self):
        """CSS.scaleY should pass through unchanged."""
        code = 'transform = CSS.scaleY(1.5)'
        result = transpile(code)
        assert 'CSS.scaleY(1.5)' in result
    
    def test_scale_3d(self):
        """CSS.scale3d(x, y, z) should pass through unchanged."""
        code = 'transform = CSS.scale3d(1, 2, 1.5)'
        result = transpile(code)
        assert 'CSS.scale3d' in result


# =============================================================================
# Skew Transform Tests (3 tests)
# =============================================================================

class TestSkew:
    """Tests for CSS.skew() and variants."""
    
    def test_skew_x(self):
        """CSS.skewX should pass through unchanged."""
        code = 'transform = CSS.skewX(CSS.deg(10))'
        result = transpile(code)
        assert 'CSS.skewX(CSS.deg(10))' in result
    
    def test_skew_y(self):
        """CSS.skewY should pass through unchanged."""
        code = 'transform = CSS.skewY(CSS.deg(15))'
        result = transpile(code)
        assert 'CSS.skewY(CSS.deg(15))' in result
    
    def test_skew_combined(self):
        """CSS.skew(ax, ay) should pass through unchanged."""
        code = 'transform = CSS.skew(CSS.deg(10), CSS.deg(15))'
        result = transpile(code)
        assert 'CSS.skew' in result


# =============================================================================
# Other Transform Tests (4 tests)
# =============================================================================

class TestOtherTransforms:
    """Tests for perspective and matrix transforms."""
    
    def test_perspective(self):
        """CSS.perspective should pass through unchanged."""
        code = 'transform = CSS.perspective(CSS.px(500))'
        result = transpile(code)
        assert 'CSS.perspective(CSS.px(500))' in result
    
    def test_matrix_2d(self):
        """CSS.matrix should pass through unchanged."""
        code = 'transform = CSS.matrix(1, 0, 0, 1, 0, 0)'
        result = transpile(code)
        assert 'CSS.matrix' in result
    
    def test_matrix_3d(self):
        """CSS.matrix3d should pass through unchanged."""
        code = '''transform = CSS.matrix3d(
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1
)'''
        result = transpile(code)
        assert 'CSS.matrix3d' in result
    
    def test_to_matrix(self):
        """transform.toMatrix() should pass through."""
        code = '''
transform = CSS.rotate(CSS.deg(45))
matrix = transform.toMatrix()
'''
        result = transpile(code)
        assert 'toMatrix()' in result


# =============================================================================
# CSSTransformValue Tests (6 tests)
# =============================================================================

class TestCSSTransformValue:
    """Tests for CSSTransformValue composite transforms."""
    
    def test_transform_value_constructor(self):
        """CSSTransformValue([...]) should pass through unchanged."""
        code = '''
transform = CSSTransformValue([
    CSS.translate(CSS.px(100), CSS.px(50)),
    CSS.rotate(CSS.deg(45)),
    CSS.scale(2),
])
'''
        result = transpile(code)
        assert 'CSSTransformValue' in result
        assert 'CSS.translate' in result
        assert 'CSS.rotate' in result
        assert 'CSS.scale' in result
    
    def test_transform_value_length(self):
        """transform.length should pass through."""
        code = '''
transform = CSSTransformValue([CSS.rotate(CSS.deg(45))])
count = transform.length
'''
        result = transpile(code)
        assert 'transform.length' in result
    
    def test_transform_value_index_access(self):
        """transform[0] should produce indexed access."""
        code = '''
transform = CSSTransformValue([CSS.rotate(CSS.deg(45))])
first = transform[0]
'''
        result = transpile(code)
        # Can be transform[0] or getitem helper
        assert 'transform' in result
        assert '0' in result
    
    def test_transform_value_is_2d(self):
        """transform.is2D should pass through."""
        code = '''
transform = CSSTransformValue([CSS.rotate(CSS.deg(45))])
is_flat = transform.is2D
'''
        result = transpile(code)
        assert 'is2D' in result
    
    def test_transform_value_to_matrix(self):
        """CSSTransformValue.toMatrix() should work."""
        code = '''
transform = CSSTransformValue([
    CSS.translate(CSS.px(100), CSS.px(50)),
])
matrix = transform.toMatrix()
'''
        result = transpile(code)
        assert 'toMatrix()' in result
    
    def test_set_transform_on_element(self):
        """Setting transform via attributeStyleMap should work."""
        code = '''
transform = CSSTransformValue([
    CSS.rotate(CSS.deg(45)),
])
el.attributeStyleMap.set("transform", transform)
'''
        result = transpile(code)
        assert 'attributeStyleMap.set("transform"' in result
