"""
Phase 34.2: CSS Edge Case Tests

Tests for edge cases and potential breaking scenarios in CSS styling:
- Empty string style removal
- Numeric properties (zIndex, opacity, flexGrow)
- CSS variable fallback syntax
- Chained DOM calls transpilation
- Conditional styling transpilation
- classList edge cases
- Vendor prefix edge cases
- CSS keyword values (inherit, initial, unset)
- Invalid CSS value handling

Total: 26 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Empty String Style Removal Tests (3 tests)
# =============================================================================

class TestEmptyStringStyleRemoval:
    """Tests for setting empty string to remove style properties."""
    
    def test_empty_string_removes_display(self):
        """Setting style to empty string should transpile correctly."""
        code = 'el.style.display = ""'
        result = transpile(code)
        assert 'el.style.display = ""' in result
        assert "__py." not in result
    
    def test_empty_string_via_set_property(self):
        """setProperty with empty string should work."""
        code = 'el.style.setProperty("display", "")'
        result = transpile(code)
        assert 'setProperty("display", "")' in result
    
    def test_empty_css_text_clears_all(self):
        """Setting cssText to empty should clear all inline styles."""
        code = 'el.style.cssText = ""'
        result = transpile(code)
        assert 'el.style.cssText = ""' in result


# =============================================================================
# Numeric Property Tests (4 tests)
# =============================================================================

class TestNumericProperties:
    """Tests for CSS properties that accept unitless numbers."""
    
    def test_z_index_numeric(self):
        """zIndex can be set as number."""
        code = 'el.style.zIndex = 10'
        result = transpile(code)
        # Should allow numeric value
        assert 'zIndex' in result
        assert '10' in result
    
    def test_z_index_string(self):
        """zIndex can also be set as string."""
        code = 'el.style.zIndex = "100"'
        result = transpile(code)
        assert 'zIndex' in result
        assert '"100"' in result
    
    def test_opacity_numeric(self):
        """opacity can be set as number (0-1)."""
        code = 'el.style.opacity = 0.5'
        result = transpile(code)
        assert 'opacity' in result
        assert '0.5' in result
    
    def test_flex_grow_numeric(self):
        """flexGrow can be set as number."""
        code = 'el.style.flexGrow = 1'
        result = transpile(code)
        assert 'flexGrow' in result
        assert '1' in result


# =============================================================================
# CSS Variable Fallback Tests (3 tests)
# =============================================================================

class TestCSSVariableFallback:
    """Tests for CSS variable fallback syntax in var()."""
    
    def test_var_with_fallback(self):
        """var() with fallback value should pass through."""
        code = 'el.style.color = "var(--primary, blue)"'
        result = transpile(code)
        assert 'var(--primary, blue)' in result
    
    def test_var_with_nested_fallback(self):
        """var() with nested var() fallback should work."""
        code = 'el.style.color = "var(--primary, var(--fallback, red))"'
        result = transpile(code)
        assert 'var(--primary, var(--fallback, red))' in result
    
    def test_var_in_calc(self):
        """var() inside calc() should pass through."""
        code = 'el.style.width = "calc(var(--base-width) + 20px)"'
        result = transpile(code)
        assert 'calc(var(--base-width) + 20px)' in result


# =============================================================================
# Chained DOM Calls Tests (3 tests)
# =============================================================================

class TestChainedDOMCalls:
    """Tests for chained DOM method calls in style operations."""
    
    def test_chained_getelementbyid_style(self):
        """Chained getElementById().style should transpile correctly."""
        code = 'document.getElementById("box").style.display = "flex"'
        result = transpile(code)
        assert 'getElementById("box")' in result
        assert '.style.display' in result
        assert '"flex"' in result
    
    def test_chained_queryselector_style(self):
        """Chained querySelector().style should work."""
        code = 'document.querySelector(".card").style.backgroundColor = "red"'
        result = transpile(code)
        assert 'querySelector(".card")' in result
        assert '.style.backgroundColor' in result
    
    def test_chained_classlist(self):
        """Chained element access with classList should work."""
        code = 'document.getElementById("btn").classList.add("active")'
        result = transpile(code)
        assert 'getElementById("btn")' in result
        assert 'classList.add("active")' in result


# =============================================================================
# Conditional Styling Tests (3 tests)
# =============================================================================

class TestConditionalStyling:
    """Tests for conditional/ternary expressions in style assignments."""
    
    def test_ternary_style_value(self):
        """Ternary expression in style value should transpile."""
        code = 'el.style.display = "flex" if is_visible else "none"'
        result = transpile(code)
        assert 'display' in result
        assert '"flex"' in result
        assert '"none"' in result
        # Should use ternary operator
        assert '?' in result or 'if' in result.lower()
    
    def test_ternary_class_toggle(self):
        """Conditional class toggle should work."""
        code = 'el.className = "active" if is_active else ""'
        result = transpile(code)
        assert 'className' in result
        assert '"active"' in result
    
    def test_or_default_style(self):
        """Using 'or' for default value should transpile."""
        code = 'el.style.color = custom_color or "black"'
        result = transpile(code)
        assert 'color' in result
        assert '"black"' in result


# =============================================================================
# classList Edge Cases Tests (2 tests)
# =============================================================================

class TestClassListEdgeCases:
    """Tests for classList edge case handling."""
    
    def test_toggle_force_false(self):
        """classList.toggle with force=False should work."""
        code = 'el.classList.toggle("active", False)'
        result = transpile(code)
        assert 'classList.toggle("active"' in result
        # Should have False/false
        assert 'False' in result or 'false' in result
    
    def test_add_multiple_same_class(self):
        """Adding same class multiple times should work (browser dedupes)."""
        code = 'el.classList.add("x", "x", "y")'
        result = transpile(code)
        assert 'classList.add(' in result


# =============================================================================
# Vendor Prefix Edge Cases (2 tests)
# =============================================================================

class TestVendorPrefixEdgeCases:
    """Tests for vendor prefix handling edge cases."""
    
    def test_moz_transform(self):
        """-moz- prefix should transpile correctly."""
        code = 'el.style.MozTransform = "rotate(45deg)"'
        result = transpile(code)
        assert 'MozTransform' in result or 'mozTransform' in result
    
    def test_ms_transform(self):
        """-ms- prefix (IE) should transpile correctly."""
        code = 'el.style.msTransform = "rotate(45deg)"'
        result = transpile(code)
        assert 'msTransform' in result


# =============================================================================
# CSS Keyword Values Tests (3 tests)
# =============================================================================

class TestCSSKeywordValues:
    """Tests for CSS keyword values like inherit, initial, unset."""
    
    def test_inherit_keyword(self):
        """inherit keyword should pass through."""
        code = 'el.style.color = "inherit"'
        result = transpile(code)
        assert '"inherit"' in result
    
    def test_initial_keyword(self):
        """initial keyword should pass through."""
        code = 'el.style.display = "initial"'
        result = transpile(code)
        assert '"initial"' in result
    
    def test_unset_keyword(self):
        """unset keyword should pass through."""
        code = 'el.style.margin = "unset"'
        result = transpile(code)
        assert '"unset"' in result


# =============================================================================
# Invalid CSS Value Tests (3 tests)
# =============================================================================

class TestInvalidCSSValues:
    """Tests for handling invalid CSS values (transpiler doesn't validate, browser does)."""
    
    def test_invalid_value_transpiles(self):
        """Invalid value should still transpile (browser will ignore)."""
        code = 'el.style.width = "banana"'
        result = transpile(code)
        # Transpiler doesn't validate CSS values, just passes through
        assert '"banana"' in result
        assert 'el.style.width' in result
    
    def test_mixed_valid_invalid(self):
        """Mix of valid and invalid should transpile."""
        code = '''
el.style.width = "100px"
el.style.height = "invalid"
el.style.display = "flex"
'''
        result = transpile(code)
        assert '"100px"' in result
        assert '"invalid"' in result
        assert '"flex"' in result
    
    def test_empty_after_value(self):
        """Setting empty string after a value should work."""
        code = '''
el.style.width = "100px"
el.style.width = ""
'''
        result = transpile(code)
        assert '"100px"' in result
        assert '""' in result


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

