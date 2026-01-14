"""
Phase 34.4: Synthetic Event Tests

Unit tests for creating and dispatching events programmatically:
- Event constructors
- dispatchEvent
- Custom event creation
- Event simulation

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestEventConstructors:
    """Tests for creating events with constructors."""
    
    def test_basic_event_constructor(self):
        """Basic Event constructor should work."""
        code = '''
event = Event("custom")
'''
        result = transpile(code)
        assert 'Event("custom")' in result
        assert '__py.' not in result
    
    def test_event_with_options(self):
        """Event constructor with options should work."""
        code = '''
event = Event("custom", {"bubbles": True, "cancelable": True})
'''
        result = transpile(code)
        assert 'Event("custom"' in result
        assert 'bubbles' in result
        assert 'cancelable' in result
    
    def test_custom_event_constructor(self):
        """CustomEvent constructor should work."""
        code = '''
event = CustomEvent("notify", {"detail": {"message": "Hello"}})
'''
        result = transpile(code)
        assert 'CustomEvent("notify"' in result
        assert 'detail' in result
    
    def test_mouse_event_constructor(self):
        """MouseEvent constructor should work."""
        code = '''
event = MouseEvent("click", {
    "bubbles": True,
    "clientX": 100,
    "clientY": 200
})
'''
        result = transpile(code)
        assert 'MouseEvent("click"' in result
        assert 'clientX' in result
    
    def test_keyboard_event_constructor(self):
        """KeyboardEvent constructor should work."""
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


class TestDispatchEvent:
    """Tests for dispatching events."""
    
    def test_dispatch_event(self):
        """dispatchEvent should work."""
        code = '''
el = document.getElementById("btn")
event = Event("click")
el.dispatchEvent(event)
'''
        result = transpile(code)
        assert 'dispatchEvent(event)' in result
    
    def test_dispatch_custom_event(self):
        """Dispatching custom event should work."""
        code = '''
def notify(element, data):
    event = CustomEvent("notify", {"detail": data, "bubbles": True})
    element.dispatchEvent(event)
'''
        result = transpile(code)
        assert 'dispatchEvent' in result
    
    def test_dispatch_returns_boolean(self):
        """dispatchEvent return value should work."""
        code = '''
def try_action(element):
    event = Event("action", {"cancelable": True})
    if element.dispatchEvent(event):
        do_action()
'''
        result = transpile(code)
        assert 'dispatchEvent(event)' in result
    
    def test_dispatch_inline(self):
        """Creating and dispatching inline should work."""
        code = '''
el.dispatchEvent(Event("refresh"))
'''
        result = transpile(code)
        # Event constructor now emits with 'new' keyword (Transpiler Core Fix)
        assert 'dispatchEvent(new Event("refresh"))' in result


class TestEventSimulation:
    """Tests for simulating user events."""
    
    def test_simulate_click(self):
        """Simulating click should work."""
        code = '''
def simulate_click(element):
    event = MouseEvent("click", {
        "bubbles": True,
        "cancelable": True,
        "view": window
    })
    element.dispatchEvent(event)
'''
        result = transpile(code)
        assert 'MouseEvent("click"' in result
        assert 'dispatchEvent' in result
    
    def test_simulate_keypress(self):
        """Simulating keypress should work."""
        code = '''
def press_enter(element):
    event = KeyboardEvent("keydown", {
        "key": "Enter",
        "code": "Enter",
        "keyCode": 13,
        "bubbles": True
    })
    element.dispatchEvent(event)
'''
        result = transpile(code)
        assert 'KeyboardEvent("keydown"' in result
    
    def test_simulate_input(self):
        """Simulating input should work."""
        code = '''
def simulate_typing(element, text):
    element.value = text
    event = InputEvent("input", {
        "bubbles": True,
        "inputType": "insertText",
        "data": text
    })
    element.dispatchEvent(event)
'''
        result = transpile(code)
        assert 'InputEvent("input"' in result
    
    def test_trigger_submit(self):
        """Triggering form submit should work."""
        code = '''
def trigger_submit(form):
    event = SubmitEvent("submit", {"bubbles": True, "cancelable": True})
    form.dispatchEvent(event)
'''
        result = transpile(code)
        assert 'SubmitEvent("submit"' in result
    
    def test_trigger_focus(self):
        """Triggering focus events should work."""
        code = '''
def trigger_blur(element):
    event = FocusEvent("blur", {"bubbles": False})
    element.dispatchEvent(event)
'''
        result = transpile(code)
        assert 'FocusEvent("blur"' in result

