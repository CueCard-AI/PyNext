"""
Phase 34.4: Keyboard Event Tests

Unit tests for KeyboardEvent transpilation covering:
- key and code properties
- repeat and isComposing properties
- location property
- Modifier keys
- Common keyboard patterns

Total: 25 tests
"""

import pytest
from pynext.transpiler import transpile


class TestKeyboardKeyProperties:
    """Tests for key identification properties."""
    
    def test_key_passthrough(self):
        """key property should pass through unchanged."""
        code = '''
def handle(event):
    k = event.key
'''
        result = transpile(code)
        assert 'event.key' in result
        assert '__py.' not in result
    
    def test_code_passthrough(self):
        """code property should pass through unchanged."""
        code = '''
def handle(event):
    c = event.code
'''
        result = transpile(code)
        assert 'event.code' in result
        assert '__py.' not in result
    
    def test_key_escape_check(self):
        """Checking for Escape key should work."""
        code = '''
def handle(event):
    if event.key == "Escape":
        close_modal()
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.key' in result and '"Escape"' in result
    
    def test_key_arrow_check(self):
        """Checking for arrow keys should work."""
        code = '''
def handle(event):
    if event.key == "ArrowUp":
        move_up()
    elif event.key == "ArrowDown":
        move_down()
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.key' in result and '"ArrowUp"' in result
        assert '"ArrowDown"' in result


class TestKeyboardStateProperties:
    """Tests for keyboard state properties."""
    
    def test_repeat_passthrough(self):
        """repeat property should pass through unchanged."""
        code = '''
def handle(event):
    r = event.repeat
'''
        result = transpile(code)
        assert 'event.repeat' in result
        assert '__py.' not in result
    
    def test_is_composing_passthrough(self):
        """isComposing property should pass through unchanged."""
        code = '''
def handle(event):
    composing = event.isComposing
'''
        result = transpile(code)
        assert 'event.isComposing' in result
        assert '__py.' not in result
    
    def test_location_passthrough(self):
        """location property should pass through unchanged."""
        code = '''
def handle(event):
    loc = event.location
'''
        result = transpile(code)
        assert 'event.location' in result
        assert '__py.' not in result


class TestKeyboardModifiers:
    """Tests for keyboard modifier properties."""
    
    def test_ctrl_key(self):
        """ctrlKey should pass through."""
        code = '''
def handle(event):
    ctrl = event.ctrlKey
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert '__py.' not in result
    
    def test_alt_key(self):
        """altKey should pass through."""
        code = '''
def handle(event):
    if event.altKey:
        show_shortcuts()
'''
        result = transpile(code)
        assert 'event.altKey' in result
    
    def test_shift_key(self):
        """shiftKey should pass through."""
        code = '''
def handle(event):
    if event.shiftKey and event.key == "Tab":
        focus_previous()
'''
        result = transpile(code)
        assert 'event.shiftKey' in result
    
    def test_meta_key(self):
        """metaKey should pass through."""
        code = '''
def handle(event):
    if event.metaKey and event.key == "k":
        open_command_palette()
'''
        result = transpile(code)
        assert 'event.metaKey' in result
    
    def test_get_modifier_state(self):
        """getModifierState should pass through."""
        code = '''
def handle(event):
    caps_on = event.getModifierState("CapsLock")
    num_on = event.getModifierState("NumLock")
'''
        result = transpile(code)
        assert 'event.getModifierState("CapsLock")' in result
        assert 'event.getModifierState("NumLock")' in result


class TestKeyboardEventMethods:
    """Tests for keyboard event methods."""
    
    def test_prevent_default(self):
        """preventDefault should pass through."""
        code = '''
def handle(event):
    if event.key == "Tab":
        event.preventDefault()
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
    
    def test_stop_propagation(self):
        """stopPropagation should pass through."""
        code = '''
def handle(event):
    event.stopPropagation()
'''
        result = transpile(code)
        assert 'event.stopPropagation()' in result
    
    def test_stop_immediate_propagation(self):
        """stopImmediatePropagation should pass through."""
        code = '''
def handle(event):
    event.stopImmediatePropagation()
'''
        result = transpile(code)
        assert 'event.stopImmediatePropagation()' in result


class TestKeyboardPatterns:
    """Tests for common keyboard handling patterns."""
    
    def test_keyboard_shortcut_handler(self):
        """Complete keyboard shortcut handler should work."""
        code = '''
def on_keydown(event):
    if event.ctrlKey or event.metaKey:
        if event.key == "s":
            event.preventDefault()
            save_document()
        elif event.key == "z":
            event.preventDefault()
            undo()
        elif event.key == "y":
            event.preventDefault()
            redo()
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert 'event.metaKey' in result
        assert 'event.key' in result
        assert 'event.preventDefault()' in result
        # Truthiness/comparison checks may use __py helpers
    
    def test_form_navigation(self):
        """Form navigation with Tab should work."""
        code = '''
def handle(event):
    if event.key == "Tab":
        if event.shiftKey:
            focus_previous_field()
        else:
            focus_next_field()
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.key' in result and '"Tab"' in result
        assert 'event.shiftKey' in result
    
    def test_escape_close_pattern(self):
        """Escape key close pattern should work."""
        code = '''
def handle(event):
    if event.key == "Escape":
        event.stopPropagation()
        close_overlay()
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.key' in result and '"Escape"' in result
        assert 'event.stopPropagation()' in result
    
    def test_enter_submit_pattern(self):
        """Enter key submit pattern should work."""
        code = '''
def handle(event):
    if event.key == "Enter" and not event.shiftKey:
        event.preventDefault()
        submit_form()
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.key' in result and '"Enter"' in result
        assert 'event.shiftKey' in result
        assert 'event.preventDefault()' in result
    
    def test_arrow_key_navigation(self):
        """Arrow key navigation should work."""
        code = '''
def handle(event):
    if event.key == "ArrowUp":
        select_previous()
    elif event.key == "ArrowDown":
        select_next()
    elif event.key == "ArrowLeft":
        collapse()
    elif event.key == "ArrowRight":
        expand()
'''
        result = transpile(code)
        assert 'ArrowUp' in result
        assert 'ArrowDown' in result
        assert 'ArrowLeft' in result
        assert 'ArrowRight' in result
    
    def test_ignore_repeated_keys(self):
        """Ignoring repeated keydown events should work."""
        code = '''
def handle(event):
    if event.repeat:
        return
    trigger_action(event.key)
'''
        result = transpile(code)
        assert 'event.repeat' in result
    
    def test_physical_key_check(self):
        """Physical key check with code should work."""
        code = '''
def handle(event):
    # WASD controls regardless of keyboard layout
    if event.code == "KeyW":
        move_forward()
    elif event.code == "KeyA":
        move_left()
    elif event.code == "KeyS":
        move_backward()
    elif event.code == "KeyD":
        move_right()
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.code' in result and '"KeyW"' in result
        assert '"KeyA"' in result
        assert '"KeyS"' in result
        assert '"KeyD"' in result

