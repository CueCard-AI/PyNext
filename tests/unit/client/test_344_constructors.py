"""
Phase 34.4: Event Constructor Tests

Comprehensive tests for event constructor behavior:
- Default values
- Init dict options
- Different event types
- Edge cases with options

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestEventDefaults:
    """Tests for Event constructor defaults."""
    
    def test_event_no_init_dict(self):
        """Event with just type, no options."""
        code = '''
event = Event("custom")
'''
        result = transpile(code)
        assert 'Event("custom")' in result
        assert '__py.' not in result
    
    def test_event_partial_init(self):
        """Event with partial init dict."""
        code = '''
event = Event("custom", {"bubbles": True})
'''
        result = transpile(code)
        assert 'Event("custom"' in result
        assert 'bubbles' in result


class TestMouseEventConstructor:
    """Tests for MouseEvent constructor."""
    
    def test_mouse_event_with_coords(self):
        """MouseEvent with clientX/Y in init."""
        code = '''
event = MouseEvent("click", {
    "clientX": 100,
    "clientY": 200,
    "bubbles": True
})
'''
        result = transpile(code)
        assert 'MouseEvent("click"' in result
        assert 'clientX' in result
        assert 'clientY' in result
    
    def test_mouse_event_with_button(self):
        """MouseEvent with button in init."""
        code = '''
event = MouseEvent("click", {
    "button": 2,
    "buttons": 4
})
'''
        result = transpile(code)
        assert 'MouseEvent("click"' in result
        assert 'button' in result


class TestKeyboardEventConstructor:
    """Tests for KeyboardEvent constructor."""
    
    def test_keyboard_event_with_key(self):
        """KeyboardEvent with key and code."""
        code = '''
event = KeyboardEvent("keydown", {
    "key": "Enter",
    "code": "Enter",
    "bubbles": True
})
'''
        result = transpile(code)
        assert 'KeyboardEvent("keydown"' in result
        assert '"key"' in result
        assert '"code"' in result


class TestCustomEventConstructor:
    """Tests for CustomEvent constructor."""
    
    def test_custom_event_with_detail(self):
        """CustomEvent with detail property."""
        code = '''
event = CustomEvent("notify", {
    "detail": {"message": "Hello", "id": 123},
    "bubbles": True
})
'''
        result = transpile(code)
        assert 'CustomEvent("notify"' in result
        assert 'detail' in result


class TestEventOptions:
    """Tests for event options behavior."""
    
    def test_bubbles_false_option(self):
        """Event with bubbles: false."""
        code = '''
event = Event("local", {"bubbles": False})
'''
        result = transpile(code)
        assert 'bubbles' in result
        assert 'false' in result.lower()
    
    def test_cancelable_false_option(self):
        """Event with cancelable: false."""
        code = '''
event = Event("notify", {"cancelable": False})
'''
        result = transpile(code)
        assert 'cancelable' in result
    
    def test_composed_true_option(self):
        """Event with composed: true (crosses shadow DOM)."""
        code = '''
event = CustomEvent("update", {
    "composed": True,
    "bubbles": True,
    "detail": data
})
'''
        result = transpile(code)
        assert 'composed' in result
        assert 'true' in result.lower()
    
    def test_touch_event_constructor(self):
        """TouchEvent constructor (complex)."""
        code = '''
touch = Touch({
    "identifier": 0,
    "target": element,
    "clientX": 100,
    "clientY": 200
})
'''
        result = transpile(code)
        assert 'Touch(' in result
        assert 'identifier' in result

