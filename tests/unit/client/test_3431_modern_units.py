"""
Phase 34.3.1: Modern CSS Units Tests

Comprehensive tests for modern CSS units:
- Dynamic Viewport Units (svw, svh, lvw, lvh, dvw, dvh)
- Container Query Units (cqw, cqh, cqi, cqb, cqmin, cqmax)
- Advanced Typography Units (cap, ic, lh, rlh)

These are CSS Level 4 features with excellent modern browser support.

Total: 40 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Dynamic Viewport Units - Small Viewport (4 tests)
# =============================================================================

class TestSmallViewportUnits:
    """Tests for small viewport units (svw, svh)."""
    
    def test_svw_basic(self):
        """CSS.svw() should create small viewport width value."""
        code = 'width = CSS.svw(100)'
        result = transpile(code)
        assert 'CSS.svw(100)' in result
    
    def test_svh_basic(self):
        """CSS.svh() should create small viewport height value."""
        code = 'height = CSS.svh(100)'
        result = transpile(code)
        assert 'CSS.svh(100)' in result
    
    def test_svh_mobile_hero(self):
        """svh for mobile-safe hero sections."""
        code = '''
hero_height = CSS.svh(100)
el.attributeStyleMap.set("height", hero_height)
'''
        result = transpile(code)
        assert 'CSS.svh(100)' in result
        assert 'set("height"' in result
    
    def test_svw_percentage(self):
        """CSS.svw() with percentage value."""
        code = 'half_width = CSS.svw(50)'
        result = transpile(code)
        assert 'CSS.svw(50)' in result


# =============================================================================
# Dynamic Viewport Units - Large Viewport (4 tests)
# =============================================================================

class TestLargeViewportUnits:
    """Tests for large viewport units (lvw, lvh)."""
    
    def test_lvw_basic(self):
        """CSS.lvw() should create large viewport width value."""
        code = 'width = CSS.lvw(100)'
        result = transpile(code)
        assert 'CSS.lvw(100)' in result
    
    def test_lvh_basic(self):
        """CSS.lvh() should create large viewport height value."""
        code = 'height = CSS.lvh(100)'
        result = transpile(code)
        assert 'CSS.lvh(100)' in result
    
    def test_lvh_fullscreen_layout(self):
        """lvh for fullscreen layouts when browser UI is hidden."""
        code = '''
container_height = CSS.lvh(100)
el.attributeStyleMap.set("min-height", container_height)
'''
        result = transpile(code)
        assert 'CSS.lvh(100)' in result
        assert 'min-height' in result
    
    def test_lvw_lvh_combined(self):
        """Using both lvw and lvh together."""
        code = '''
width = CSS.lvw(100)
height = CSS.lvh(100)
'''
        result = transpile(code)
        assert 'CSS.lvw(100)' in result
        assert 'CSS.lvh(100)' in result


# =============================================================================
# Dynamic Viewport Units - Dynamic (4 tests)
# =============================================================================

class TestDynamicViewportUnits:
    """Tests for dynamic viewport units (dvw, dvh)."""
    
    def test_dvw_basic(self):
        """CSS.dvw() should create dynamic viewport width value."""
        code = 'width = CSS.dvw(100)'
        result = transpile(code)
        assert 'CSS.dvw(100)' in result
    
    def test_dvh_basic(self):
        """CSS.dvh() should create dynamic viewport height value."""
        code = 'height = CSS.dvh(100)'
        result = transpile(code)
        assert 'CSS.dvh(100)' in result
    
    def test_dvh_adaptive_layout(self):
        """dvh for layouts that adapt to browser UI changes."""
        code = '''
# Hero that smoothly adapts as mobile browser UI appears/disappears
hero = CSS.dvh(100)
el.attributeStyleMap.set("height", hero)
'''
        result = transpile(code)
        assert 'CSS.dvh(100)' in result
    
    def test_dvh_arithmetic(self):
        """Arithmetic with dynamic viewport units."""
        code = '''
full_height = CSS.dvh(100)
content_height = full_height.sub(CSS.px(60))  # Minus header
'''
        result = transpile(code)
        assert 'CSS.dvh(100)' in result
        assert 'sub(' in result


# =============================================================================
# Container Query Units - Width/Height (4 tests)
# =============================================================================

class TestContainerQueryWidthHeight:
    """Tests for container query width/height units (cqw, cqh)."""
    
    def test_cqw_basic(self):
        """CSS.cqw() should create container query width value."""
        code = 'width = CSS.cqw(50)'
        result = transpile(code)
        assert 'CSS.cqw(50)' in result
    
    def test_cqh_basic(self):
        """CSS.cqh() should create container query height value."""
        code = 'height = CSS.cqh(50)'
        result = transpile(code)
        assert 'CSS.cqh(50)' in result
    
    def test_cqw_responsive_card(self):
        """cqw for responsive card layouts."""
        code = '''
# Card that takes 50% of its container
card_width = CSS.cqw(50)
el.attributeStyleMap.set("width", card_width)
'''
        result = transpile(code)
        assert 'CSS.cqw(50)' in result
    
    def test_cqw_cqh_combined(self):
        """Using both cqw and cqh together."""
        code = '''
width = CSS.cqw(100)
height = CSS.cqh(50)
'''
        result = transpile(code)
        assert 'CSS.cqw(100)' in result
        assert 'CSS.cqh(50)' in result


# =============================================================================
# Container Query Units - Inline/Block (4 tests)
# =============================================================================

class TestContainerQueryInlineBlock:
    """Tests for container query inline/block units (cqi, cqb)."""
    
    def test_cqi_basic(self):
        """CSS.cqi() should create container query inline-size value."""
        code = 'inline_size = CSS.cqi(100)'
        result = transpile(code)
        assert 'CSS.cqi(100)' in result
    
    def test_cqb_basic(self):
        """CSS.cqb() should create container query block-size value."""
        code = 'block_size = CSS.cqb(100)'
        result = transpile(code)
        assert 'CSS.cqb(100)' in result
    
    def test_cqi_writing_mode_aware(self):
        """cqi is writing-mode aware."""
        code = '''
# Works correctly in both horizontal and vertical writing modes
size = CSS.cqi(50)
el.attributeStyleMap.set("inline-size", size)
'''
        result = transpile(code)
        assert 'CSS.cqi(50)' in result
    
    def test_cqb_logical_layout(self):
        """cqb for logical (writing-mode aware) layouts."""
        code = '''
block = CSS.cqb(100)
el.attributeStyleMap.set("block-size", block)
'''
        result = transpile(code)
        assert 'CSS.cqb(100)' in result


# =============================================================================
# Container Query Units - Min/Max (4 tests)
# =============================================================================

class TestContainerQueryMinMax:
    """Tests for container query min/max units (cqmin, cqmax)."""
    
    def test_cqmin_basic(self):
        """CSS.cqmin() should create container query min value."""
        code = 'size = CSS.cqmin(50)'
        result = transpile(code)
        assert 'CSS.cqmin(50)' in result
    
    def test_cqmax_basic(self):
        """CSS.cqmax() should create container query max value."""
        code = 'size = CSS.cqmax(50)'
        result = transpile(code)
        assert 'CSS.cqmax(50)' in result
    
    def test_cqmin_square_element(self):
        """cqmin for elements that should be square within container."""
        code = '''
# Square element based on smaller container dimension
size = CSS.cqmin(50)
el.attributeStyleMap.set("width", size)
el.attributeStyleMap.set("height", size)
'''
        result = transpile(code)
        assert 'CSS.cqmin(50)' in result
    
    def test_cqmax_for_larger_dimension(self):
        """cqmax for sizing based on larger container dimension."""
        code = '''
large_size = CSS.cqmax(100)
'''
        result = transpile(code)
        assert 'CSS.cqmax(100)' in result


# =============================================================================
# Advanced Typography Units - Cap Height (3 tests)
# =============================================================================

class TestCapHeightUnit:
    """Tests for cap-height unit (cap)."""
    
    def test_cap_basic(self):
        """CSS.cap() should create cap-height value."""
        code = 'height = CSS.cap(1)'
        result = transpile(code)
        assert 'CSS.cap(1)' in result
    
    def test_cap_icon_sizing(self):
        """cap for sizing icons to match capital letters."""
        code = '''
# Icon sized to match capital letter height
icon_size = CSS.cap(1)
el.attributeStyleMap.set("height", icon_size)
'''
        result = transpile(code)
        assert 'CSS.cap(1)' in result
    
    def test_cap_multiple(self):
        """CSS.cap() with multiple cap-heights."""
        code = 'spacing = CSS.cap(2)'
        result = transpile(code)
        assert 'CSS.cap(2)' in result


# =============================================================================
# Advanced Typography Units - Ideographic (3 tests)
# =============================================================================

class TestIdeographicUnit:
    """Tests for ideographic character unit (ic)."""
    
    def test_ic_basic(self):
        """CSS.ic() should create ideographic character value."""
        code = 'width = CSS.ic(10)'
        result = transpile(code)
        assert 'CSS.ic(10)' in result
    
    def test_ic_cjk_text(self):
        """ic for CJK text layouts with uniform character width."""
        code = '''
# Text column width for 20 CJK characters
column_width = CSS.ic(20)
el.attributeStyleMap.set("width", column_width)
'''
        result = transpile(code)
        assert 'CSS.ic(20)' in result
    
    def test_ic_fraction(self):
        """CSS.ic() with fractional value."""
        code = 'half_char = CSS.ic(0.5)'
        result = transpile(code)
        assert 'CSS.ic(0.5)' in result


# =============================================================================
# Advanced Typography Units - Line Height (5 tests)
# =============================================================================

class TestLineHeightUnits:
    """Tests for line-height units (lh, rlh)."""
    
    def test_lh_basic(self):
        """CSS.lh() should create line-height value."""
        code = 'spacing = CSS.lh(1)'
        result = transpile(code)
        assert 'CSS.lh(1)' in result
    
    def test_rlh_basic(self):
        """CSS.rlh() should create root line-height value."""
        code = 'spacing = CSS.rlh(1)'
        result = transpile(code)
        assert 'CSS.rlh(1)' in result
    
    def test_lh_vertical_rhythm(self):
        """lh for maintaining vertical rhythm."""
        code = '''
# Margin of exactly one line of text
margin = CSS.lh(1)
el.attributeStyleMap.set("margin-bottom", margin)
'''
        result = transpile(code)
        assert 'CSS.lh(1)' in result
    
    def test_rlh_consistent_spacing(self):
        """rlh for consistent spacing across components."""
        code = '''
# Spacing consistent with root line-height
gap = CSS.rlh(2)
el.attributeStyleMap.set("gap", gap)
'''
        result = transpile(code)
        assert 'CSS.rlh(2)' in result
    
    def test_lh_fractional(self):
        """CSS.lh() with fractional value."""
        code = 'half_line = CSS.lh(0.5)'
        result = transpile(code)
        assert 'CSS.lh(0.5)' in result


# =============================================================================
# Cross-Unit Integration Tests (5 tests)
# =============================================================================

class TestCrossUnitIntegration:
    """Tests for combining modern units with existing features."""
    
    def test_dvh_with_calc(self):
        """Combining dvh with calc()."""
        code = '''
height = CSS.calc("100dvh - 60px")
'''
        result = transpile(code)
        assert 'CSS.calc' in result
        assert '100dvh' in result
    
    def test_cqw_with_clamp(self):
        """Combining cqw with clamp()."""
        code = '''
width = CSS.clamp(CSS.px(200), CSS.cqw(50), CSS.px(500))
'''
        result = transpile(code)
        assert 'CSS.clamp' in result
        assert 'CSS.cqw(50)' in result
    
    def test_modern_units_in_style_map(self):
        """All modern units work with StylePropertyMap."""
        code = '''
el.attributeStyleMap.set("width", CSS.cqw(100))
el.attributeStyleMap.set("height", CSS.dvh(50))
el.attributeStyleMap.set("padding", CSS.lh(1))
'''
        result = transpile(code)
        assert 'CSS.cqw(100)' in result
        assert 'CSS.dvh(50)' in result
        assert 'CSS.lh(1)' in result
    
    def test_viewport_comparison(self):
        """Using different viewport unit types together."""
        code = '''
# Small for safe minimum, dynamic for actual
min_height = CSS.svh(100)
actual_height = CSS.dvh(100)
'''
        result = transpile(code)
        assert 'CSS.svh(100)' in result
        assert 'CSS.dvh(100)' in result
    
    def test_container_vs_viewport(self):
        """Container units vs viewport units."""
        code = '''
# Component uses container units for responsive within container
# Fallback to viewport for full-page contexts
component_width = CSS.cqw(100)
page_width = CSS.vw(100)
'''
        result = transpile(code)
        assert 'CSS.cqw(100)' in result
        assert 'CSS.vw(100)' in result

