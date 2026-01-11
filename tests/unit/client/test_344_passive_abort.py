"""
Phase 34.4: Passive Listeners and AbortController Tests

Unit tests for passive listener options and AbortController patterns:
- passive: true/false
- AbortController creation and signal
- abort() cleanup
- Combined options

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestPassiveListeners:
    """Tests for passive listener options."""
    
    def test_passive_true(self):
        """passive: true should pass through."""
        code = '''
el.addEventListener("scroll", handler, {"passive": True})
'''
        result = transpile(code)
        assert 'passive' in result
        assert 'true' in result.lower()
    
    def test_passive_false(self):
        """passive: false should pass through."""
        code = '''
el.addEventListener("touchmove", handler, {"passive": False})
'''
        result = transpile(code)
        assert 'passive' in result
        assert 'false' in result.lower()
    
    def test_passive_with_prevent_default(self):
        """passive: false with preventDefault should work."""
        code = '''
def on_touchmove(event):
    event.preventDefault()
    handle_drag(event)

el.addEventListener("touchmove", on_touchmove, {"passive": False})
'''
        result = transpile(code)
        assert 'passive' in result
        assert 'event.preventDefault()' in result
    
    def test_default_passive_for_scroll(self):
        """Scroll listeners can be passive by default."""
        code = '''
window.addEventListener("scroll", handler, {"passive": True})
'''
        result = transpile(code)
        assert 'passive' in result


class TestAbortControllerCreation:
    """Tests for AbortController creation."""
    
    def test_create_abort_controller(self):
        """AbortController creation should pass through."""
        code = '''
controller = AbortController()
'''
        result = transpile(code)
        assert 'AbortController()' in result
        assert '__py.' not in result
    
    def test_access_signal(self):
        """AbortController.signal should pass through."""
        code = '''
controller = AbortController()
signal = controller.signal
'''
        result = transpile(code)
        assert 'controller.signal' in result
    
    def test_signal_aborted_property(self):
        """AbortSignal.aborted should pass through."""
        code = '''
controller = AbortController()
if controller.signal.aborted:
    handle_aborted()
'''
        result = transpile(code)
        assert 'signal.aborted' in result
    
    def test_signal_reason_property(self):
        """AbortSignal.reason should pass through."""
        code = '''
controller = AbortController()
reason = controller.signal.reason
'''
        result = transpile(code)
        assert 'signal.reason' in result


class TestAbortControllerUsage:
    """Tests for AbortController usage patterns."""
    
    def test_add_listener_with_signal(self):
        """addEventListener with signal should pass through."""
        code = '''
controller = AbortController()
el.addEventListener("click", handler, {"signal": controller.signal})
'''
        result = transpile(code)
        assert 'signal' in result
        assert 'controller.signal' in result
    
    def test_abort_call(self):
        """controller.abort() should pass through."""
        code = '''
controller = AbortController()
controller.abort()
'''
        result = transpile(code)
        assert 'controller.abort()' in result
    
    def test_abort_with_reason(self):
        """controller.abort(reason) should pass through."""
        code = '''
controller = AbortController()
controller.abort("User cancelled")
'''
        result = transpile(code)
        assert 'abort("User cancelled")' in result


class TestAbortControllerPatterns:
    """Tests for common AbortController patterns."""
    
    def test_component_cleanup_pattern(self):
        """Component cleanup pattern should work."""
        code = '''
from pynext.client import document

class Component:
    def __init__(self, element):
        self.element = element
        self.controller = AbortController()
    
    def mount(self):
        signal = self.controller.signal
        self.element.addEventListener("click", self.on_click, {"signal": signal})
        document.addEventListener("keydown", self.on_keydown, {"signal": signal})
        window.addEventListener("resize", self.on_resize, {"signal": signal})
    
    def unmount(self):
        self.controller.abort()
    
    def on_click(self, event):
        pass
    
    def on_keydown(self, event):
        pass
    
    def on_resize(self, event):
        pass
'''
        result = transpile(code)
        assert 'AbortController()' in result
        assert result.count('signal') >= 3
        assert 'abort()' in result
    
    def test_multiple_listeners_same_signal(self):
        """Multiple listeners on same signal should work."""
        code = '''
controller = AbortController()
signal = controller.signal

el.addEventListener("click", handler1, {"signal": signal})
el.addEventListener("mouseover", handler2, {"signal": signal})
el.addEventListener("keydown", handler3, {"signal": signal})

# All listeners removed with one call
controller.abort()
'''
        result = transpile(code)
        assert result.count('"signal"') == 3 or result.count("signal:") == 3
        assert 'abort()' in result
    
    def test_combined_options(self):
        """Combined listener options should work."""
        code = '''
controller = AbortController()

el.addEventListener("click", handler, {
    "signal": controller.signal,
    "capture": True,
    "once": True
})
'''
        result = transpile(code)
        assert 'signal' in result
        assert 'capture' in result
        assert 'once' in result
    
    def test_fetch_abort_pattern(self):
        """Abort pattern with fetch-like usage should work."""
        code = '''
controller = AbortController()

def start_operation():
    # Start listening
    el.addEventListener("progress", on_progress, {"signal": controller.signal})
    el.addEventListener("complete", on_complete, {"signal": controller.signal})

def cancel_operation():
    controller.abort("Operation cancelled by user")
'''
        result = transpile(code)
        assert 'AbortController()' in result
        assert 'abort(' in result

