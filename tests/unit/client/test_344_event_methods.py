"""
Phase 34.4: Event Methods Tests

Unit tests for Event methods transpilation covering:
- preventDefault()
- stopPropagation()
- stopImmediatePropagation()
- composedPath()
- target and currentTarget properties

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


class TestPreventDefault:
    """Tests for preventDefault method."""
    
    def test_prevent_default_basic(self):
        """preventDefault should pass through unchanged."""
        code = '''
def handle(event):
    event.preventDefault()
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert '__py.' not in result
    
    def test_prevent_default_conditional(self):
        """Conditional preventDefault should work."""
        code = '''
def handle(event):
    if should_prevent:
        event.preventDefault()
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
    
    def test_check_default_prevented(self):
        """defaultPrevented property should pass through."""
        code = '''
def handle(event):
    if event.defaultPrevented:
        return
'''
        result = transpile(code)
        assert 'event.defaultPrevented' in result
    
    def test_check_cancelable(self):
        """cancelable property should pass through."""
        code = '''
def handle(event):
    if event.cancelable:
        event.preventDefault()
'''
        result = transpile(code)
        assert 'event.cancelable' in result


class TestStopPropagation:
    """Tests for stopPropagation methods."""
    
    def test_stop_propagation_basic(self):
        """stopPropagation should pass through unchanged."""
        code = '''
def handle(event):
    event.stopPropagation()
'''
        result = transpile(code)
        assert 'event.stopPropagation()' in result
        assert '__py.' not in result
    
    def test_stop_immediate_propagation(self):
        """stopImmediatePropagation should pass through."""
        code = '''
def handle(event):
    event.stopImmediatePropagation()
'''
        result = transpile(code)
        assert 'event.stopImmediatePropagation()' in result
    
    def test_stop_both(self):
        """Using both stop methods should work."""
        code = '''
def handle(event):
    event.stopPropagation()
    event.preventDefault()
'''
        result = transpile(code)
        assert 'event.stopPropagation()' in result
        assert 'event.preventDefault()' in result


class TestComposedPath:
    """Tests for composedPath method."""
    
    def test_composed_path_basic(self):
        """composedPath should pass through unchanged."""
        code = '''
def handle(event):
    path = event.composedPath()
'''
        result = transpile(code)
        assert 'event.composedPath()' in result
        assert '__py.' not in result
    
    def test_composed_path_iteration(self):
        """Iterating over composedPath should work."""
        code = '''
def handle(event):
    for el in event.composedPath():
        process(el)
'''
        result = transpile(code)
        assert 'event.composedPath()' in result


class TestEventTargets:
    """Tests for target and currentTarget properties."""
    
    def test_target_passthrough(self):
        """target should pass through unchanged."""
        code = '''
def handle(event):
    el = event.target
'''
        result = transpile(code)
        assert 'event.target' in result
        assert '__py.' not in result
    
    def test_current_target_passthrough(self):
        """currentTarget should pass through unchanged."""
        code = '''
def handle(event):
    listener = event.currentTarget
'''
        result = transpile(code)
        assert 'event.currentTarget' in result
    
    def test_target_property_access(self):
        """Accessing target properties should work."""
        code = '''
def handle(event):
    id = event.target.id
    value = event.target.value
'''
        result = transpile(code)
        assert 'event.target.id' in result
        assert 'event.target.value' in result
    
    def test_target_method_call(self):
        """Calling methods on target should work."""
        code = '''
def handle(event):
    event.target.focus()
'''
        result = transpile(code)
        assert 'event.target.focus()' in result
    
    def test_target_comparison(self):
        """Comparing targets should work."""
        code = '''
def handle(event):
    if event.target == event.currentTarget:
        handle_self_click()
'''
        result = transpile(code)
        assert 'event.target' in result
        assert 'event.currentTarget' in result


class TestEventStateProperties:
    """Tests for event state properties."""
    
    def test_event_type(self):
        """type property should pass through."""
        code = '''
def handle(event):
    event_name = event.type
'''
        result = transpile(code)
        assert 'event.type' in result
    
    def test_event_phase(self):
        """eventPhase should pass through."""
        code = '''
def handle(event):
    phase = event.eventPhase
'''
        result = transpile(code)
        assert 'event.eventPhase' in result
    
    def test_bubbles_property(self):
        """bubbles property should pass through."""
        code = '''
def handle(event):
    can_bubble = event.bubbles
'''
        result = transpile(code)
        assert 'event.bubbles' in result
    
    def test_is_trusted(self):
        """isTrusted property should pass through."""
        code = '''
def handle(event):
    if not event.isTrusted:
        log_synthetic_event()
'''
        result = transpile(code)
        assert 'event.isTrusted' in result
    
    def test_timestamp(self):
        """timeStamp property should pass through."""
        code = '''
def handle(event):
    when = event.timeStamp
'''
        result = transpile(code)
        assert 'event.timeStamp' in result

