"""
Phase 34.4: Event Listener Options Tests

Unit tests for addEventListener options transpilation covering:
- capture option
- once option
- passive option
- signal option (AbortController)
- Combined options

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestCaptureOption:
    """Tests for capture phase option."""
    
    def test_capture_boolean(self):
        """Capture as boolean should pass through."""
        code = '''
from pynext.client import document

el.addEventListener("click", handler, True)
'''
        result = transpile(code)
        assert 'addEventListener("click", handler, true)' in result
        assert '__py.' not in result
    
    def test_capture_in_options(self):
        """Capture in options object should work."""
        code = '''
el.addEventListener("click", handler, {"capture": True})
'''
        result = transpile(code)
        assert 'addEventListener' in result
        assert 'capture' in result


class TestOnceOption:
    """Tests for once option."""
    
    def test_once_option(self):
        """once option should pass through."""
        code = '''
el.addEventListener("click", handler, {"once": True})
'''
        result = transpile(code)
        assert 'addEventListener' in result
        assert 'once' in result
    
    def test_once_with_capture(self):
        """once with capture should work."""
        code = '''
el.addEventListener("click", handler, {"once": True, "capture": True})
'''
        result = transpile(code)
        assert 'once' in result
        assert 'capture' in result


class TestPassiveOption:
    """Tests for passive option."""
    
    def test_passive_true(self):
        """passive: true should pass through."""
        code = '''
el.addEventListener("scroll", handler, {"passive": True})
'''
        result = transpile(code)
        assert 'passive' in result
    
    def test_passive_false(self):
        """passive: false should pass through."""
        code = '''
el.addEventListener("touchmove", handler, {"passive": False})
'''
        result = transpile(code)
        assert 'passive' in result


class TestSignalOption:
    """Tests for AbortController signal option."""
    
    def test_signal_option(self):
        """signal option should pass through."""
        code = '''
controller = AbortController()
el.addEventListener("click", handler, {"signal": controller.signal})
'''
        result = transpile(code)
        assert 'AbortController()' in result
        assert 'signal' in result


class TestRemoveEventListener:
    """Tests for removeEventListener."""
    
    def test_remove_basic(self):
        """Basic removeEventListener should pass through."""
        code = '''
el.removeEventListener("click", handler)
'''
        result = transpile(code)
        assert 'removeEventListener("click", handler)' in result
        assert '__py.' not in result
    
    def test_remove_with_capture(self):
        """removeEventListener with capture should work."""
        code = '''
el.removeEventListener("click", handler, True)
'''
        result = transpile(code)
        assert 'removeEventListener("click", handler, true)' in result
    
    def test_remove_with_options(self):
        """removeEventListener with options should work."""
        code = '''
el.removeEventListener("click", handler, {"capture": True})
'''
        result = transpile(code)
        assert 'removeEventListener' in result
        assert 'capture' in result


class TestListenerPatterns:
    """Tests for common event listener patterns."""
    
    def test_document_listener(self):
        """Adding listener to document should work."""
        code = '''
from pynext.client import document

document.addEventListener("DOMContentLoaded", on_ready)
'''
        result = transpile(code)
        assert 'document.addEventListener("DOMContentLoaded"' in result
    
    def test_window_listener(self):
        """Adding listener to window should work."""
        code = '''
from pynext.client import window

window.addEventListener("resize", on_resize)
'''
        result = transpile(code)
        assert 'window.addEventListener("resize"' in result
    
    def test_lambda_handler(self):
        """Lambda event handler should work."""
        code = '''
el.addEventListener("click", lambda e: e.preventDefault())
'''
        result = transpile(code)
        assert 'addEventListener' in result
        assert 'preventDefault' in result
    
    def test_all_options_combined(self):
        """All options combined should work."""
        code = '''
el.addEventListener("touchstart", handler, {
    "capture": True,
    "once": True,
    "passive": True
})
'''
        result = transpile(code)
        assert 'capture' in result
        assert 'once' in result
        assert 'passive' in result

