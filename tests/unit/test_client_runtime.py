"""
Tests for PyNext Client Runtime

Tests the keyboard, theme, focus, and storage modules.
"""

import pytest
from unittest.mock import MagicMock, patch


# =============================================================================
# Client Primitives Tests
# =============================================================================

class TestClientPrimitives:
    """Test pynext.core.client primitives."""
    
    def test_on_keydown_decorator(self):
        """Test keyboard shortcut decorator."""
        from pynext.core.client import on_keydown, reset_client_state, _shortcuts
        
        reset_client_state()
        
        @on_keydown("cmd+k")
        def open_search():
            pass
        
        # Check shortcut was registered
        assert len(_shortcuts) == 1
        shortcut = list(_shortcuts.values())[0]
        assert shortcut.key == "k"
        assert "meta" in shortcut.modifiers
        
        reset_client_state()
    
    def test_on_keydown_with_context(self):
        """Test shortcut with context option."""
        from pynext.core.client import on_keydown, reset_client_state, _shortcuts
        
        reset_client_state()
        
        @on_keydown("escape", context="dialog")
        def close_dialog():
            pass
        
        shortcut = list(_shortcuts.values())[0]
        assert shortcut.key == "escape"
        assert shortcut.context == "dialog"
        
        reset_client_state()
    
    def test_on_key_sequence_decorator(self):
        """Test key sequence decorator."""
        from pynext.core.client import on_key_sequence, reset_client_state, _sequences
        
        reset_client_state()
        
        @on_key_sequence("g d")
        def go_dashboard():
            pass
        
        assert len(_sequences) == 1
        sequence = list(_sequences.values())[0]
        assert sequence.keys == ["g", "d"]
        
        reset_client_state()
    
    def test_parse_key_combo(self):
        """Test key combination parsing."""
        from pynext.core.client import _parse_key_combo
        
        # Test cmd+k
        key, mods = _parse_key_combo("cmd+k")
        assert key == "k"
        assert "meta" in mods
        
        # Test ctrl+shift+s
        key, mods = _parse_key_combo("ctrl+shift+s")
        assert key == "s"
        assert "ctrl" in mods
        assert "shift" in mods
        
        # Test single key
        key, mods = _parse_key_combo("escape")
        assert key == "escape"
        assert len(mods) == 0
    
    def test_use_storage(self):
        """Test storage signal creation."""
        from pynext.core.client import use_storage, reset_client_state
        
        reset_client_state()
        
        theme = use_storage("theme", default="light")
        
        assert theme() == "light"
        assert theme.key == "theme"
        assert theme.storage_type == "local"
        
        theme.set("dark")
        assert theme() == "dark"
        
        reset_client_state()
    
    def test_use_storage_session(self):
        """Test session storage signal."""
        from pynext.core.client import use_storage, reset_client_state
        
        reset_client_state()
        
        temp = use_storage("temp_data", default={}, storage="session")
        
        assert temp.storage_type == "session"
        
        reset_client_state()
    
    def test_use_ref(self):
        """Test ref creation."""
        from pynext.core.client import use_ref, reset_client_state
        
        reset_client_state()
        
        ref = use_ref()
        
        assert ref.id.startswith("ref_")
        assert ref.current is None
        
        # With name
        named_ref = use_ref("input")
        assert "input" in named_ref.id
        
        reset_client_state()
    
    def test_client_effect(self):
        """Test client effect decorator."""
        from pynext.core.client import client_effect, reset_client_state, _client_effects
        
        reset_client_state()
        
        @client_effect
        def setup_listener():
            pass
        
        assert len(_client_effects) == 1
        
        reset_client_state()
    
    def test_client_effect_with_deps(self):
        """Test client effect with dependencies."""
        from pynext.core.client import client_effect, reset_client_state, _client_effects
        
        reset_client_state()
        
        @client_effect(dependencies=["theme", "count"])
        def update_ui():
            pass
        
        effect = list(_client_effects.values())[0]
        assert effect.dependencies == ["theme", "count"]
        
        reset_client_state()
    
    def test_use_theme(self):
        """Test theme signal creation."""
        from pynext.core import client
        
        client.reset_client_state()
        
        theme = client.use_theme()
        
        assert theme() == "system"
        assert client._theme_state is not None
        assert client._theme_state.storage_key == "theme"
        
        client.reset_client_state()
    
    def test_get_client_hydration_data(self):
        """Test hydration data generation."""
        from pynext.core.client import (
            on_keydown, on_key_sequence, use_storage,
            get_client_hydration_data, reset_client_state
        )
        
        reset_client_state()
        
        @on_keydown("cmd+k")
        def search():
            pass
        
        @on_key_sequence("g d")
        def dashboard():
            pass
        
        theme = use_storage("theme", default="light")
        
        data = get_client_hydration_data()
        
        assert len(data["shortcuts"]) == 1
        assert len(data["sequences"]) == 1
        assert len(data["storage"]) == 1
        
        reset_client_state()


# =============================================================================
# Keyboard Module Tests
# =============================================================================

class TestKeyboardModule:
    """Test pynext.keyboard module."""
    
    def test_format_shortcut(self):
        """Test shortcut formatting."""
        from pynext.keyboard import format_shortcut
        from pynext.core.client import KeyboardShortcut
        
        shortcut = KeyboardShortcut(
            id="test",
            key="k",
            modifiers=["meta"],
            handler_id="h1",
        )
        
        # Mac format
        formatted = format_shortcut(shortcut, platform="mac")
        assert "⌘" in formatted or "K" in formatted
        
        # Windows format
        formatted = format_shortcut(shortcut, platform="windows")
        assert "Ctrl" in formatted
    
    def test_format_sequence(self):
        """Test sequence formatting."""
        from pynext.keyboard import format_sequence
        from pynext.core.client import KeySequence
        
        seq = KeySequence(
            id="test",
            keys=["g", "d"],
            handler_id="h1",
        )
        
        formatted = format_sequence(seq)
        assert "G" in formatted
        assert "D" in formatted
        assert "→" in formatted
    
    def test_get_all_shortcuts(self):
        """Test getting all shortcuts."""
        from pynext.keyboard import on_keydown, get_all_shortcuts
        from pynext.core.client import reset_client_state
        
        reset_client_state()
        
        @on_keydown("cmd+s")
        def save():
            pass
        
        shortcuts = get_all_shortcuts()
        assert len(shortcuts) == 1
        assert shortcuts[0]["key"] == "s"
        
        reset_client_state()


# =============================================================================
# Theme Module Tests
# =============================================================================

class TestThemeModule:
    """Test pynext.theme module."""
    
    def test_get_flash_prevention_script(self):
        """Test flash prevention script generation."""
        from pynext.theme import get_flash_prevention_script
        
        script = get_flash_prevention_script()
        
        assert "localStorage" in script
        assert "dark" in script
        assert "prefers-color-scheme" in script
    
    def test_custom_storage_key(self):
        """Test custom storage key in flash script."""
        from pynext.theme import get_flash_prevention_script
        
        script = get_flash_prevention_script("color-mode")
        
        assert "color-mode" in script


# =============================================================================
# Focus Module Tests
# =============================================================================

class TestFocusModule:
    """Test pynext.focus module."""
    
    def test_get_focusable_selector(self):
        """Test focusable selector generation."""
        from pynext.focus import get_focusable_selector
        
        selector = get_focusable_selector()
        
        assert "a[href]" in selector
        assert "button" in selector
        assert "input" in selector
        assert "tabindex" in selector


# =============================================================================
# Lambda Transpilation Tests
# =============================================================================

class TestLambdaTranspilation:
    """Test Python to JavaScript transpilation."""
    
    def test_simple_constant(self):
        """Test transpiling a lambda that returns a constant."""
        from pynext.core.signals import _transpile_ast
        import ast
        
        tree = ast.parse("lambda: 5")
        js = _transpile_ast(tree)
        
        # Should contain the arrow function
        assert "=>" in js
        assert "5" in js
    
    def test_binary_operation(self):
        """Test transpiling binary operations."""
        from pynext.core.signals import _transpile_ast
        import ast
        
        tree = ast.parse("lambda x: x + 1")
        js = _transpile_ast(tree)
        
        assert "x" in js
        assert "+" in js
    
    def test_comparison(self):
        """Test transpiling comparisons."""
        from pynext.core.signals import _transpile_ast
        import ast
        
        tree = ast.parse("lambda x: x == 5")
        js = _transpile_ast(tree)
        
        assert "===" in js
    
    def test_ternary(self):
        """Test transpiling ternary expressions."""
        from pynext.core.signals import _transpile_ast
        import ast
        
        tree = ast.parse("lambda x: 'a' if x else 'b'")
        js = _transpile_ast(tree)
        
        assert "?" in js


# =============================================================================
# Integration Tests
# =============================================================================

class TestClientRuntimeIntegration:
    """Integration tests for client runtime."""
    
    def test_keyboard_with_signal(self):
        """Test keyboard shortcut that updates a signal."""
        from pynext.core.signals import Signal
        from pynext.core.client import on_keydown, reset_client_state
        
        reset_client_state()
        
        count = Signal(0)
        
        @on_keydown("cmd+plus")
        def increment():
            count.update(lambda x: x + 1)
        
        # Simulate handler call
        increment()
        assert count() == 1
        
        reset_client_state()
    
    def test_theme_toggle_pattern(self):
        """Test theme toggle pattern."""
        from pynext.core.client import use_theme, use_storage, reset_client_state
        
        reset_client_state()
        
        theme = use_theme(default="light")
        
        def toggle():
            current = theme()
            theme.set("dark" if current == "light" else "light")
        
        assert theme() == "light"
        toggle()
        assert theme() == "dark"
        toggle()
        assert theme() == "light"
        
        reset_client_state()
    
    def test_storage_subscription(self):
        """Test storage signal subscription."""
        from pynext.core.client import use_storage, reset_client_state
        
        reset_client_state()
        
        storage = use_storage("test", default=0)
        changes = []
        
        storage.subscribe(lambda v: changes.append(v))
        
        storage.set(1)
        storage.set(2)
        
        assert changes == [1, 2]
        
        reset_client_state()


# =============================================================================
# Component Tests
# =============================================================================

class TestComponents:
    """Test component rendering."""
    
    def test_focus_trap_renders(self):
        """Test FocusTrap component renders."""
        from pynext.focus import FocusTrap
        
        component = FocusTrap()["Content"]
        
        # Should render without error
        assert component is not None
    
    def test_roving_focus_renders(self):
        """Test RovingFocus component renders."""
        from pynext.focus import RovingFocus, RovingFocusItem
        
        component = RovingFocus()[
            RovingFocusItem()["Item 1"],
            RovingFocusItem()["Item 2"],
        ]
        
        assert component is not None
    
    def test_skip_link_renders(self):
        """Test SkipLink component renders."""
        from pynext.focus import SkipLink
        
        component = SkipLink("main", "Skip to main")
        
        assert component is not None

