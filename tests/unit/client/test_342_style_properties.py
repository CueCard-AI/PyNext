"""
Phase 34.2: Style Properties Tests

Tests for direct style property access via element.style.*, including:
- Common CSS properties (display, visibility, position, etc.)
- Flexbox and Grid properties
- Transform and animation properties
- Vendor prefixes
- cssText and length

Total: 35 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Display & Visibility Tests (5 tests)
# =============================================================================

class TestDisplayVisibility:
    """Tests for display and visibility style properties."""
    
    def test_style_display(self):
        """el.style.display should pass through unchanged."""
        code = 'el.style.display = "flex"'
        result = transpile(code)
        assert 'el.style.display = "flex"' in result
        assert "__py." not in result
    
    def test_style_visibility(self):
        """el.style.visibility should pass through unchanged."""
        code = 'el.style.visibility = "hidden"'
        result = transpile(code)
        assert 'el.style.visibility = "hidden"' in result
    
    def test_style_opacity(self):
        """el.style.opacity should pass through unchanged."""
        code = 'el.style.opacity = "0.5"'
        result = transpile(code)
        assert 'el.style.opacity = "0.5"' in result
    
    def test_style_pointer_events(self):
        """el.style.pointerEvents should pass through unchanged."""
        code = 'el.style.pointerEvents = "none"'
        result = transpile(code)
        assert 'el.style.pointerEvents = "none"' in result
    
    def test_style_z_index(self):
        """el.style.zIndex should pass through unchanged."""
        code = 'el.style.zIndex = "100"'
        result = transpile(code)
        assert 'el.style.zIndex = "100"' in result


# =============================================================================
# Position Tests (5 tests)
# =============================================================================

class TestPosition:
    """Tests for positioning style properties."""
    
    def test_style_position(self):
        """el.style.position should pass through unchanged."""
        code = 'el.style.position = "absolute"'
        result = transpile(code)
        assert 'el.style.position = "absolute"' in result
    
    def test_style_top(self):
        """el.style.top should pass through unchanged."""
        code = 'el.style.top = "10px"'
        result = transpile(code)
        assert 'el.style.top = "10px"' in result
    
    def test_style_left(self):
        """el.style.left should pass through unchanged."""
        code = 'el.style.left = "20px"'
        result = transpile(code)
        assert 'el.style.left = "20px"' in result
    
    def test_style_inset(self):
        """el.style.inset should pass through unchanged."""
        code = 'el.style.inset = "0"'
        result = transpile(code)
        assert 'el.style.inset = "0"' in result
    
    def test_style_float(self):
        """el.style.float should pass through unchanged (reserved word)."""
        code = 'el.style.cssFloat = "left"'
        result = transpile(code)
        assert "cssFloat" in result or "float" in result


# =============================================================================
# Box Model Tests (5 tests)
# =============================================================================

class TestBoxModel:
    """Tests for box model style properties."""
    
    def test_style_width_height(self):
        """el.style.width/height should pass through unchanged."""
        code = '''
el.style.width = "100px"
el.style.height = "200px"
'''
        result = transpile(code)
        assert 'el.style.width = "100px"' in result
        assert 'el.style.height = "200px"' in result
    
    def test_style_margin(self):
        """el.style.margin should pass through unchanged."""
        code = 'el.style.margin = "10px 20px"'
        result = transpile(code)
        assert 'el.style.margin = "10px 20px"' in result
    
    def test_style_padding(self):
        """el.style.padding should pass through unchanged."""
        code = 'el.style.padding = "16px"'
        result = transpile(code)
        assert 'el.style.padding = "16px"' in result
    
    def test_style_border(self):
        """el.style.border should pass through unchanged."""
        code = 'el.style.border = "1px solid black"'
        result = transpile(code)
        assert 'el.style.border = "1px solid black"' in result
    
    def test_style_box_sizing(self):
        """el.style.boxSizing should pass through unchanged."""
        code = 'el.style.boxSizing = "border-box"'
        result = transpile(code)
        assert 'el.style.boxSizing = "border-box"' in result


# =============================================================================
# Background & Color Tests (5 tests)
# =============================================================================

class TestBackgroundColor:
    """Tests for background and color style properties."""
    
    def test_style_background_color(self):
        """el.style.backgroundColor should pass through unchanged."""
        code = 'el.style.backgroundColor = "red"'
        result = transpile(code)
        assert 'el.style.backgroundColor = "red"' in result
    
    def test_style_color(self):
        """el.style.color should pass through unchanged."""
        code = 'el.style.color = "#333"'
        result = transpile(code)
        assert 'el.style.color = "#333"' in result
    
    def test_style_background_image(self):
        """el.style.backgroundImage should pass through unchanged."""
        code = 'el.style.backgroundImage = "url(bg.png)"'
        result = transpile(code)
        assert 'el.style.backgroundImage = "url(bg.png)"' in result
    
    def test_style_backdrop_filter(self):
        """el.style.backdropFilter should pass through unchanged."""
        code = 'el.style.backdropFilter = "blur(10px)"'
        result = transpile(code)
        assert 'el.style.backdropFilter = "blur(10px)"' in result
    
    def test_style_filter(self):
        """el.style.filter should pass through unchanged."""
        code = 'el.style.filter = "grayscale(100%)"'
        result = transpile(code)
        assert 'el.style.filter = "grayscale(100%)"' in result


# =============================================================================
# Flexbox Tests (5 tests)
# =============================================================================

class TestFlexbox:
    """Tests for flexbox style properties."""
    
    def test_style_flex_direction(self):
        """el.style.flexDirection should pass through unchanged."""
        code = 'el.style.flexDirection = "column"'
        result = transpile(code)
        assert 'el.style.flexDirection = "column"' in result
    
    def test_style_justify_content(self):
        """el.style.justifyContent should pass through unchanged."""
        code = 'el.style.justifyContent = "space-between"'
        result = transpile(code)
        assert 'el.style.justifyContent = "space-between"' in result
    
    def test_style_align_items(self):
        """el.style.alignItems should pass through unchanged."""
        code = 'el.style.alignItems = "center"'
        result = transpile(code)
        assert 'el.style.alignItems = "center"' in result
    
    def test_style_gap(self):
        """el.style.gap should pass through unchanged."""
        code = 'el.style.gap = "8px"'
        result = transpile(code)
        assert 'el.style.gap = "8px"' in result
    
    def test_style_flex(self):
        """el.style.flex should pass through unchanged."""
        code = 'el.style.flex = "1 0 auto"'
        result = transpile(code)
        assert 'el.style.flex = "1 0 auto"' in result


# =============================================================================
# Transform & Animation Tests (5 tests)
# =============================================================================

class TestTransformAnimation:
    """Tests for transform and animation style properties."""
    
    def test_style_transform(self):
        """el.style.transform should pass through unchanged."""
        code = 'el.style.transform = "rotate(45deg)"'
        result = transpile(code)
        assert 'el.style.transform = "rotate(45deg)"' in result
    
    def test_style_transition(self):
        """el.style.transition should pass through unchanged."""
        code = 'el.style.transition = "all 0.3s ease"'
        result = transpile(code)
        assert 'el.style.transition = "all 0.3s ease"' in result
    
    def test_style_animation(self):
        """el.style.animation should pass through unchanged."""
        code = 'el.style.animation = "fade 1s infinite"'
        result = transpile(code)
        assert 'el.style.animation = "fade 1s infinite"' in result
    
    def test_style_will_change(self):
        """el.style.willChange should pass through unchanged."""
        code = 'el.style.willChange = "transform"'
        result = transpile(code)
        assert 'el.style.willChange = "transform"' in result
    
    def test_style_transform_origin(self):
        """el.style.transformOrigin should pass through unchanged."""
        code = 'el.style.transformOrigin = "center center"'
        result = transpile(code)
        assert 'el.style.transformOrigin = "center center"' in result


# =============================================================================
# Vendor Prefix Tests (3 tests)
# =============================================================================

class TestVendorPrefixes:
    """Tests for vendor-prefixed style properties."""
    
    def test_webkit_transform(self):
        """el.style.webkitTransform should pass through unchanged."""
        code = 'el.style.webkitTransform = "rotate(45deg)"'
        result = transpile(code)
        assert 'el.style.webkitTransform = "rotate(45deg)"' in result
    
    def test_webkit_backdrop_filter(self):
        """el.style.WebkitBackdropFilter should pass through unchanged."""
        code = 'el.style.WebkitBackdropFilter = "blur(10px)"'
        result = transpile(code)
        assert "WebkitBackdropFilter" in result or "webkitBackdropFilter" in result
    
    def test_moz_transform(self):
        """el.style.mozTransform should pass through unchanged."""
        code = 'el.style.mozTransform = "scale(1.5)"'
        result = transpile(code)
        assert 'el.style.mozTransform = "scale(1.5)"' in result


# =============================================================================
# cssText and Length Tests (2 tests)
# =============================================================================

class TestCssTextLength:
    """Tests for cssText and length properties."""
    
    def test_style_css_text_set(self):
        """el.style.cssText should pass through unchanged."""
        code = 'el.style.cssText = "display: flex; gap: 8px;"'
        result = transpile(code)
        assert 'el.style.cssText = "display: flex; gap: 8px;"' in result
    
    def test_style_length(self):
        """el.style.length should pass through unchanged."""
        code = '''
for i in range(el.style.length):
    prop = el.style.item(i)
'''
        result = transpile(code)
        assert "el.style.length" in result
        assert "el.style.item" in result

