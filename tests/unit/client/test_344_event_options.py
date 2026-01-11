"""
Phase 34.4: Event Options Tests

Unit tests for event constructor options:
- bubbles option
- cancelable option
- composed option
- Event phase handling

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestBubblesOption:
    """Tests for bubbles option."""
    
    def test_bubbles_true(self):
        """bubbles: true should work."""
        code = '''
event = Event("custom", {"bubbles": True})
'''
        result = transpile(code)
        assert 'bubbles' in result
        assert 'true' in result.lower()
    
    def test_bubbles_false(self):
        """bubbles: false should work."""
        code = '''
event = Event("custom", {"bubbles": False})
'''
        result = transpile(code)
        assert 'bubbles' in result
        assert 'false' in result.lower()
    
    def test_check_bubbles_property(self):
        """event.bubbles property should work."""
        code = '''
def handle(event):
    if event.bubbles:
        propagate()
'''
        result = transpile(code)
        assert 'event.bubbles' in result


class TestCancelableOption:
    """Tests for cancelable option."""
    
    def test_cancelable_true(self):
        """cancelable: true should work."""
        code = '''
event = Event("action", {"cancelable": True})
'''
        result = transpile(code)
        assert 'cancelable' in result
    
    def test_cancelable_false(self):
        """cancelable: false should work."""
        code = '''
event = Event("notify", {"cancelable": False})
'''
        result = transpile(code)
        assert 'cancelable' in result
    
    def test_check_cancelable_property(self):
        """event.cancelable property should work."""
        code = '''
def handle(event):
    can_cancel = event.cancelable
'''
        result = transpile(code)
        assert 'event.cancelable' in result
        assert '__py.' not in result


class TestComposedOption:
    """Tests for composed option (Shadow DOM)."""
    
    def test_composed_true(self):
        """composed: true should work."""
        code = '''
event = CustomEvent("update", {"composed": True, "bubbles": True})
'''
        result = transpile(code)
        assert 'composed' in result
    
    def test_check_composed_property(self):
        """event.composed property should work."""
        code = '''
def handle(event):
    crosses_shadow = event.composed
'''
        result = transpile(code)
        assert 'event.composed' in result
        assert '__py.' not in result


class TestEventPhase:
    """Tests for event phase handling."""
    
    def test_event_phase_property(self):
        """event.eventPhase property should work."""
        code = '''
def handle(event):
    phase = event.eventPhase
    if phase == 1:  # CAPTURING_PHASE
        handle_capture()
    elif phase == 2:  # AT_TARGET
        handle_target()
    elif phase == 3:  # BUBBLING_PHASE
        handle_bubble()
'''
        result = transpile(code)
        assert 'event.eventPhase' in result
    
    def test_default_prevented_property(self):
        """event.defaultPrevented property should work."""
        code = '''
def handle(event):
    if not event.defaultPrevented:
        do_default_action()
'''
        result = transpile(code)
        assert 'event.defaultPrevented' in result

