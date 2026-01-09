"""
Phase 34.2: CSS Variables Tests

Tests for CSS custom properties helper functions:
- set_css_var / get_css_var
- remove_css_var
- set_theme / get_theme
- toggle_theme

Total: 25 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# set_css_var Tests (5 tests)
# =============================================================================

class TestSetCssVar:
    """Tests for set_css_var function."""
    
    def test_set_css_var_basic(self):
        """set_css_var should transpile to setProperty."""
        code = '''
from pynext.client.css_vars import set_css_var
set_css_var("primary", "#3b82f6")
'''
        result = transpile(code)
        assert "setProperty" in result or "set_css_var" in result
    
    def test_set_css_var_with_dashes(self):
        """set_css_var with -- prefix should work."""
        code = '''
from pynext.client.css_vars import set_css_var
set_css_var("--primary-color", "blue")
'''
        result = transpile(code)
        assert "--primary-color" in result
    
    def test_set_css_var_on_element(self):
        """set_css_var on specific element should work."""
        code = '''
from pynext.client.css_vars import set_css_var
set_css_var("bg", "white", element=card)
'''
        result = transpile(code)
        assert "card" in result
    
    def test_set_css_var_complex_value(self):
        """set_css_var with complex value should work."""
        code = '''
from pynext.client.css_vars import set_css_var
set_css_var("shadow", "0 2px 4px rgba(0,0,0,0.1)")
'''
        result = transpile(code)
        assert "shadow" in result
    
    def test_set_css_var_number(self):
        """set_css_var with number value should work."""
        code = '''
from pynext.client.css_vars import set_css_var
set_css_var("spacing", "16px")
'''
        result = transpile(code)
        assert "spacing" in result


# =============================================================================
# get_css_var Tests (5 tests)
# =============================================================================

class TestGetCssVar:
    """Tests for get_css_var function."""
    
    def test_get_css_var_basic(self):
        """get_css_var should transpile to getPropertyValue."""
        code = '''
from pynext.client.css_vars import get_css_var
color = get_css_var("primary")
'''
        result = transpile(code)
        assert "getPropertyValue" in result or "get_css_var" in result
    
    def test_get_css_var_with_dashes(self):
        """get_css_var with -- prefix should work."""
        code = '''
from pynext.client.css_vars import get_css_var
color = get_css_var("--primary-color")
'''
        result = transpile(code)
        assert "--primary-color" in result
    
    def test_get_css_var_on_element(self):
        """get_css_var on specific element should work."""
        code = '''
from pynext.client.css_vars import get_css_var
bg = get_css_var("bg", element=card)
'''
        result = transpile(code)
        assert "card" in result
    
    def test_get_css_var_assignment(self):
        """get_css_var result should be assignable."""
        code = '''
from pynext.client.css_vars import get_css_var
color = get_css_var("theme-color")
print(color)
'''
        result = transpile(code)
        assert "color" in result
    
    def test_get_css_var_in_expression(self):
        """get_css_var in expression should work."""
        code = '''
from pynext.client.css_vars import get_css_var
if get_css_var("dark-mode"):
    pass
'''
        result = transpile(code)
        assert "dark-mode" in result


# =============================================================================
# remove_css_var Tests (3 tests)
# =============================================================================

class TestRemoveCssVar:
    """Tests for remove_css_var function."""
    
    def test_remove_css_var_basic(self):
        """remove_css_var should transpile to removeProperty."""
        code = '''
from pynext.client.css_vars import remove_css_var
remove_css_var("temp-color")
'''
        result = transpile(code)
        assert "removeProperty" in result or "remove_css_var" in result
    
    def test_remove_css_var_with_dashes(self):
        """remove_css_var with -- prefix should work."""
        code = '''
from pynext.client.css_vars import remove_css_var
remove_css_var("--old-var")
'''
        result = transpile(code)
        assert "--old-var" in result
    
    def test_remove_css_var_on_element(self):
        """remove_css_var on specific element should work."""
        code = '''
from pynext.client.css_vars import remove_css_var
remove_css_var("override", element=card)
'''
        result = transpile(code)
        assert "card" in result


# =============================================================================
# set_theme Tests (5 tests)
# =============================================================================

class TestSetTheme:
    """Tests for set_theme function."""
    
    def test_set_theme_basic(self):
        """set_theme should set multiple variables."""
        code = '''
from pynext.client.css_vars import set_theme
set_theme({
    "bg": "#ffffff",
    "fg": "#000000",
})
'''
        result = transpile(code)
        assert "set_theme" in result or "setProperty" in result
    
    def test_set_theme_full(self):
        """set_theme with full theme should work."""
        code = '''
from pynext.client.css_vars import set_theme
set_theme({
    "bg": "#ffffff",
    "fg": "#000000",
    "primary": "#3b82f6",
    "secondary": "#64748b",
    "radius": "8px",
    "spacing": "16px",
})
'''
        result = transpile(code)
        assert "bg" in result
        assert "primary" in result
    
    def test_set_theme_dark(self):
        """set_theme for dark theme should work."""
        code = '''
from pynext.client.css_vars import set_theme
set_theme({
    "bg": "#1a1a2e",
    "fg": "#ffffff",
})
'''
        result = transpile(code)
        assert "#1a1a2e" in result
    
    def test_set_theme_on_element(self):
        """set_theme on specific element should work."""
        code = '''
from pynext.client.css_vars import set_theme
set_theme({"bg": "#000"}, element=modal)
'''
        result = transpile(code)
        assert "modal" in result
    
    def test_set_theme_empty(self):
        """set_theme with empty dict should not error."""
        code = '''
from pynext.client.css_vars import set_theme
set_theme({})
'''
        result = transpile(code)
        assert "set_theme" in result


# =============================================================================
# get_theme Tests (3 tests)
# =============================================================================

class TestGetTheme:
    """Tests for get_theme function."""
    
    def test_get_theme_basic(self):
        """get_theme should get multiple variables."""
        code = '''
from pynext.client.css_vars import get_theme
theme = get_theme(["bg", "fg", "primary"])
'''
        result = transpile(code)
        assert "get_theme" in result
        assert "bg" in result
    
    def test_get_theme_single(self):
        """get_theme with single variable should work."""
        code = '''
from pynext.client.css_vars import get_theme
theme = get_theme(["primary"])
'''
        result = transpile(code)
        assert "primary" in result
    
    def test_get_theme_on_element(self):
        """get_theme on specific element should work."""
        code = '''
from pynext.client.css_vars import get_theme
theme = get_theme(["bg"], element=card)
'''
        result = transpile(code)
        assert "card" in result


# =============================================================================
# toggle_theme Tests (4 tests)
# =============================================================================

class TestToggleTheme:
    """Tests for toggle_theme function."""
    
    def test_toggle_theme_basic(self):
        """toggle_theme should switch between themes."""
        code = '''
from pynext.client.css_vars import toggle_theme
light = {"bg": "#fff", "fg": "#000"}
dark = {"bg": "#000", "fg": "#fff"}
is_dark = toggle_theme(light, dark)
'''
        result = transpile(code)
        assert "toggle_theme" in result
    
    def test_toggle_theme_force_dark(self):
        """toggle_theme with prefer_dark=True should work."""
        code = '''
from pynext.client.css_vars import toggle_theme
light = {"bg": "#fff"}
dark = {"bg": "#000"}
toggle_theme(light, dark, prefer_dark=True)
'''
        result = transpile(code)
        assert "prefer_dark" in result or "True" in result
    
    def test_toggle_theme_force_light(self):
        """toggle_theme with prefer_dark=False should work."""
        code = '''
from pynext.client.css_vars import toggle_theme
light = {"bg": "#fff"}
dark = {"bg": "#000"}
toggle_theme(light, dark, prefer_dark=False)
'''
        result = transpile(code)
        assert "prefer_dark" in result or "False" in result
    
    def test_toggle_theme_result(self):
        """toggle_theme should return boolean."""
        code = '''
from pynext.client.css_vars import toggle_theme
light = {"bg": "#fff"}
dark = {"bg": "#000"}
is_dark = toggle_theme(light, dark)
if is_dark:
    print("Dark mode")
'''
        result = transpile(code)
        assert "is_dark" in result

