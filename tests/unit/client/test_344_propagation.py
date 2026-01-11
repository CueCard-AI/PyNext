"""
Phase 34.4: Event Propagation Tests

Comprehensive tests for event propagation behavior:
- Capture vs bubble phase
- stopPropagation and stopImmediatePropagation
- Multiple listeners and execution order
- Listener management edge cases

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestPropagationPhases:
    """Tests for capture and bubble phase behavior."""
    
    def test_capture_phase_listener(self):
        """Capture phase listener with {capture: true}."""
        code = '''
def on_click(event):
    console.log("captured")

el.addEventListener("click", on_click, {"capture": True})
'''
        result = transpile(code)
        assert 'addEventListener("click"' in result
        assert 'capture' in result
        assert 'true' in result.lower()
    
    def test_bubble_phase_default(self):
        """Default listener is bubble phase."""
        code = '''
def on_click(event):
    console.log("bubbled")

el.addEventListener("click", on_click)
'''
        result = transpile(code)
        assert 'addEventListener("click"' in result
        # No capture means bubble phase (default)


class TestStopPropagation:
    """Tests for stopping event propagation."""
    
    def test_stop_propagation(self):
        """stopPropagation prevents further bubbling."""
        code = '''
def on_click(event):
    event.stopPropagation()
    handle_locally()
'''
        result = transpile(code)
        assert 'event.stopPropagation()' in result
        assert '__py.' not in result
    
    def test_stop_immediate_propagation(self):
        """stopImmediatePropagation stops all listeners."""
        code = '''
def on_click(event):
    event.stopImmediatePropagation()
    # No other listeners will run
'''
        result = transpile(code)
        assert 'event.stopImmediatePropagation()' in result
        assert '__py.' not in result
    
    def test_propagation_check(self):
        """Check if propagation was stopped."""
        code = '''
def on_click(event):
    if not event.cancelBubble:
        bubble_up()
'''
        result = transpile(code)
        assert 'event.cancelBubble' in result


class TestMultipleListeners:
    """Tests for multiple listener management."""
    
    def test_multiple_listeners_same_event(self):
        """Multiple listeners on same element and event."""
        code = '''
def handler1(event):
    console.log("first")

def handler2(event):
    console.log("second")

el.addEventListener("click", handler1)
el.addEventListener("click", handler2)
'''
        result = transpile(code)
        assert result.count('addEventListener("click"') == 2
    
    def test_listener_removal(self):
        """Remove a specific listener."""
        code = '''
def on_click(event):
    console.log("clicked")

el.addEventListener("click", on_click)
el.removeEventListener("click", on_click)
'''
        result = transpile(code)
        assert 'addEventListener' in result
        assert 'removeEventListener' in result
    
    def test_listener_removal_with_capture(self):
        """Remove listener with capture must match options."""
        code = '''
def on_click(event):
    pass

el.addEventListener("click", on_click, {"capture": True})
el.removeEventListener("click", on_click, {"capture": True})
'''
        result = transpile(code)
        assert 'removeEventListener' in result


class TestEventPhaseProperties:
    """Tests for event phase properties."""
    
    def test_event_phase_property(self):
        """Access eventPhase property."""
        code = '''
def on_click(event):
    phase = event.eventPhase
    if phase == 1:  # CAPTURING_PHASE
        console.log("capturing")
    elif phase == 2:  # AT_TARGET
        console.log("at target")
    elif phase == 3:  # BUBBLING_PHASE
        console.log("bubbling")
'''
        result = transpile(code)
        assert 'event.eventPhase' in result
    
    def test_composed_path(self):
        """composedPath returns event path through DOM."""
        code = '''
def on_click(event):
    path = event.composedPath()
    for element in path:
        console.log(element.tagName)
'''
        result = transpile(code)
        assert 'event.composedPath()' in result

