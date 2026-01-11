"""
Phase 34.4: Mouse Event Tests

Unit tests for MouseEvent transpilation covering:
- Position properties (clientX/Y, pageX/Y, screenX/Y, offsetX/Y, movementX/Y)
- Button properties (button, buttons)
- Modifier keys (altKey, ctrlKey, shiftKey, metaKey)
- Related target
- getModifierState method

Total: 30 tests
"""

import pytest
from pynext.transpiler import transpile


class TestMousePositionProperties:
    """Tests for mouse position coordinate properties."""
    
    def test_client_x_passthrough(self):
        """clientX should pass through unchanged."""
        code = '''
def handle(event):
    x = event.clientX
'''
        result = transpile(code)
        assert 'event.clientX' in result
        assert '__py.' not in result
    
    def test_client_y_passthrough(self):
        """clientY should pass through unchanged."""
        code = '''
def handle(event):
    y = event.clientY
'''
        result = transpile(code)
        assert 'event.clientY' in result
        assert '__py.' not in result
    
    def test_page_x_passthrough(self):
        """pageX should pass through unchanged."""
        code = '''
def handle(event):
    x = event.pageX
'''
        result = transpile(code)
        assert 'event.pageX' in result
        assert '__py.' not in result
    
    def test_page_y_passthrough(self):
        """pageY should pass through unchanged."""
        code = '''
def handle(event):
    y = event.pageY
'''
        result = transpile(code)
        assert 'event.pageY' in result
        assert '__py.' not in result
    
    def test_screen_x_passthrough(self):
        """screenX should pass through unchanged."""
        code = '''
def handle(event):
    x = event.screenX
'''
        result = transpile(code)
        assert 'event.screenX' in result
        assert '__py.' not in result
    
    def test_screen_y_passthrough(self):
        """screenY should pass through unchanged."""
        code = '''
def handle(event):
    y = event.screenY
'''
        result = transpile(code)
        assert 'event.screenY' in result
        assert '__py.' not in result
    
    def test_offset_x_passthrough(self):
        """offsetX should pass through unchanged."""
        code = '''
def handle(event):
    x = event.offsetX
'''
        result = transpile(code)
        assert 'event.offsetX' in result
        assert '__py.' not in result
    
    def test_offset_y_passthrough(self):
        """offsetY should pass through unchanged."""
        code = '''
def handle(event):
    y = event.offsetY
'''
        result = transpile(code)
        assert 'event.offsetY' in result
        assert '__py.' not in result
    
    def test_movement_x_passthrough(self):
        """movementX should pass through unchanged."""
        code = '''
def handle(event):
    dx = event.movementX
'''
        result = transpile(code)
        assert 'event.movementX' in result
        assert '__py.' not in result
    
    def test_movement_y_passthrough(self):
        """movementY should pass through unchanged."""
        code = '''
def handle(event):
    dy = event.movementY
'''
        result = transpile(code)
        assert 'event.movementY' in result
        assert '__py.' not in result
    
    def test_all_position_properties(self):
        """All position properties together."""
        code = '''
def handle(event):
    pos = {
        "clientX": event.clientX,
        "clientY": event.clientY,
        "pageX": event.pageX,
        "pageY": event.pageY,
        "offsetX": event.offsetX,
        "offsetY": event.offsetY,
    }
'''
        result = transpile(code)
        assert 'event.clientX' in result
        assert 'event.clientY' in result
        assert 'event.pageX' in result
        assert 'event.pageY' in result
        assert 'event.offsetX' in result
        assert 'event.offsetY' in result


class TestMouseButtonProperties:
    """Tests for mouse button properties."""
    
    def test_button_passthrough(self):
        """button should pass through unchanged."""
        code = '''
def handle(event):
    btn = event.button
'''
        result = transpile(code)
        assert 'event.button' in result
        assert '__py.' not in result
    
    def test_buttons_passthrough(self):
        """buttons bitmask should pass through unchanged."""
        code = '''
def handle(event):
    btns = event.buttons
'''
        result = transpile(code)
        assert 'event.buttons' in result
        assert '__py.' not in result
    
    def test_button_value_check(self):
        """Checking button values should work."""
        code = '''
def handle(event):
    if event.button == 2:
        show_context_menu()
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.button' in result and '2' in result


class TestMouseModifierKeys:
    """Tests for modifier key properties."""
    
    def test_alt_key_passthrough(self):
        """altKey should pass through unchanged."""
        code = '''
def handle(event):
    alt = event.altKey
'''
        result = transpile(code)
        assert 'event.altKey' in result
        assert '__py.' not in result
    
    def test_ctrl_key_passthrough(self):
        """ctrlKey should pass through unchanged."""
        code = '''
def handle(event):
    ctrl = event.ctrlKey
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert '__py.' not in result
    
    def test_shift_key_passthrough(self):
        """shiftKey should pass through unchanged."""
        code = '''
def handle(event):
    shift = event.shiftKey
'''
        result = transpile(code)
        assert 'event.shiftKey' in result
        assert '__py.' not in result
    
    def test_meta_key_passthrough(self):
        """metaKey should pass through unchanged."""
        code = '''
def handle(event):
    meta = event.metaKey
'''
        result = transpile(code)
        assert 'event.metaKey' in result
        assert '__py.' not in result
    
    def test_combined_modifiers(self):
        """Combining modifiers should work."""
        code = '''
def handle(event):
    if event.ctrlKey and event.shiftKey:
        ctrl_shift_click()
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert 'event.shiftKey' in result
    
    def test_get_modifier_state(self):
        """getModifierState method should pass through."""
        code = '''
def handle(event):
    caps = event.getModifierState("CapsLock")
'''
        result = transpile(code)
        assert 'event.getModifierState("CapsLock")' in result
        assert '__py.' not in result


class TestRelatedTarget:
    """Tests for relatedTarget property."""
    
    def test_related_target_passthrough(self):
        """relatedTarget should pass through unchanged."""
        code = '''
def handle(event):
    target = event.relatedTarget
'''
        result = transpile(code)
        assert 'event.relatedTarget' in result
        assert '__py.' not in result
    
    def test_related_target_comparison(self):
        """Comparing relatedTarget should work."""
        code = '''
def handle(event):
    if event.relatedTarget != event.target:
        handle_transition()
'''
        result = transpile(code)
        assert 'event.relatedTarget' in result
        assert 'event.target' in result


class TestMouseEventMethods:
    """Tests for mouse event methods."""
    
    def test_prevent_default(self):
        """preventDefault should pass through."""
        code = '''
def handle(event):
    event.preventDefault()
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert '__py.' not in result
    
    def test_stop_propagation(self):
        """stopPropagation should pass through."""
        code = '''
def handle(event):
    event.stopPropagation()
'''
        result = transpile(code)
        assert 'event.stopPropagation()' in result
        assert '__py.' not in result
    
    def test_composed_path(self):
        """composedPath should pass through."""
        code = '''
def handle(event):
    path = event.composedPath()
'''
        result = transpile(code)
        assert 'event.composedPath()' in result
        assert '__py.' not in result


class TestComplexMouseHandlers:
    """Tests for complex mouse event handler patterns."""
    
    def test_drag_tracking(self):
        """Complete drag tracking handler should work."""
        code = '''
def on_mouse_move(event):
    dx = event.movementX
    dy = event.movementY
    btns = event.buttons
    drag_element(event.clientX, event.clientY)
'''
        result = transpile(code)
        assert 'event.movementX' in result
        assert 'event.movementY' in result
        assert 'event.buttons' in result
        assert 'event.clientX' in result
        assert '__py.' not in result
    
    def test_click_handler_with_modifiers(self):
        """Click handler checking modifiers should work."""
        code = '''
def on_click(event):
    if event.ctrlKey or event.metaKey:
        open_in_new_tab()
    elif event.shiftKey:
        select_range()
    else:
        navigate()
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert 'event.metaKey' in result
        assert 'event.shiftKey' in result
        # Truthiness checks may use __py.bool, but event properties pass through

