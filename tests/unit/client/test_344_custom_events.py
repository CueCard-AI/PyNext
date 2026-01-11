"""
Phase 34.4: Custom Event Tests

Unit tests for CustomEvent transpilation covering:
- CustomEvent constructor
- detail property
- dispatchEvent
- Event bubbling and capturing

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


class TestCustomEventConstruction:
    """Tests for CustomEvent constructor."""
    
    def test_custom_event_simple(self):
        """Simple CustomEvent should pass through."""
        code = '''
event = CustomEvent("my-event")
'''
        result = transpile(code)
        assert 'CustomEvent("my-event")' in result
        assert '__py.' not in result
    
    def test_custom_event_with_detail(self):
        """CustomEvent with detail should pass through."""
        code = '''
event = CustomEvent("user-login", {"detail": {"userId": 123}})
'''
        result = transpile(code)
        assert 'CustomEvent' in result
        assert 'user-login' in result
    
    def test_custom_event_with_bubbles(self):
        """CustomEvent with bubbles option should work."""
        code = '''
event = CustomEvent("notification", {"bubbles": True, "detail": data})
'''
        result = transpile(code)
        assert 'CustomEvent' in result
        assert 'bubbles' in result
    
    def test_custom_event_all_options(self):
        """CustomEvent with all options should work."""
        code = '''
event = CustomEvent("custom", {
    "bubbles": True,
    "cancelable": True,
    "composed": True,
    "detail": {"key": "value"}
})
'''
        result = transpile(code)
        assert 'CustomEvent' in result
        assert 'bubbles' in result
        assert 'cancelable' in result
        assert 'composed' in result


class TestCustomEventDetail:
    """Tests for accessing CustomEvent detail."""
    
    def test_detail_access(self):
        """Accessing detail should pass through."""
        code = '''
def handle(event):
    data = event.detail
'''
        result = transpile(code)
        assert 'event.detail' in result
        assert '__py.' not in result
    
    def test_detail_property_access(self):
        """Accessing detail properties should work."""
        code = '''
def handle(event):
    user_id = event.detail["userId"]
'''
        result = transpile(code)
        assert 'event.detail' in result
    
    def test_detail_nested_access(self):
        """Nested detail access should work."""
        code = '''
def handle(event):
    name = event.detail["user"]["name"]
'''
        result = transpile(code)
        assert 'event.detail' in result


class TestDispatchEvent:
    """Tests for dispatching events."""
    
    def test_dispatch_event_basic(self):
        """dispatchEvent should pass through."""
        code = '''
from pynext.client import document

event = CustomEvent("my-event")
el.dispatchEvent(event)
'''
        result = transpile(code)
        assert 'dispatchEvent' in result
        assert '__py.' not in result
    
    def test_dispatch_on_element(self):
        """Dispatching on element should work."""
        code = '''
from pynext.client import document

el = document.getElementById("app")
el.dispatchEvent(CustomEvent("loaded"))
'''
        result = transpile(code)
        assert 'dispatchEvent' in result
    
    def test_dispatch_on_document(self):
        """Dispatching on document should work."""
        code = '''
from pynext.client import document

document.dispatchEvent(CustomEvent("app-ready"))
'''
        result = transpile(code)
        assert 'document.dispatchEvent' in result


class TestEventBaseProperties:
    """Tests for base Event properties on CustomEvent."""
    
    def test_event_type(self):
        """event.type should pass through."""
        code = '''
def handle(event):
    event_name = event.type
'''
        result = transpile(code)
        assert 'event.type' in result
    
    def test_event_target(self):
        """event.target should pass through."""
        code = '''
def handle(event):
    source = event.target
'''
        result = transpile(code)
        assert 'event.target' in result
    
    def test_event_current_target(self):
        """event.currentTarget should pass through."""
        code = '''
def handle(event):
    listener = event.currentTarget
'''
        result = transpile(code)
        assert 'event.currentTarget' in result
    
    def test_event_bubbles(self):
        """event.bubbles should pass through."""
        code = '''
def handle(event):
    will_bubble = event.bubbles
'''
        result = transpile(code)
        assert 'event.bubbles' in result


class TestCustomEventPatterns:
    """Tests for common custom event patterns."""
    
    def test_component_communication(self):
        """Component-to-component communication should work."""
        code = '''
from pynext.client import document

def notify_parent(data):
    event = CustomEvent("child-action", {
        "bubbles": True,
        "detail": data
    })
    el.dispatchEvent(event)

def on_child_action(event):
    handle_action(event.detail)
'''
        result = transpile(code)
        assert 'CustomEvent' in result
        assert 'dispatchEvent' in result
        assert 'event.detail' in result
    
    def test_event_listener_registration(self):
        """Adding custom event listener should work."""
        code = '''
from pynext.client import document

el = document.getElementById("app")
el.addEventListener("my-event", handler)
'''
        result = transpile(code)
        assert 'addEventListener("my-event"' in result
    
    def test_remove_custom_listener(self):
        """Removing custom event listener should work."""
        code = '''
el.removeEventListener("my-event", handler)
'''
        result = transpile(code)
        assert 'removeEventListener("my-event"' in result
    
    def test_stop_custom_event_propagation(self):
        """Stopping custom event propagation should work."""
        code = '''
def handle(event):
    event.stopPropagation()
'''
        result = transpile(code)
        assert 'event.stopPropagation()' in result
    
    def test_prevent_custom_event_default(self):
        """Preventing custom event default should work."""
        code = '''
def handle(event):
    event.preventDefault()
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result

