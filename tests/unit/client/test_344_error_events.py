"""
Phase 34.4: Error Event Tests

Unit tests for ErrorEvent transpilation covering:
- window.onerror handling
- Error properties
- unhandledrejection
- Error reporting patterns

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestErrorEventBasics:
    """Tests for basic ErrorEvent properties."""
    
    def test_message_property(self):
        """ErrorEvent.message should pass through."""
        code = '''
def on_error(event):
    msg = event.message
'''
        result = transpile(code)
        assert 'event.message' in result
        assert '__py.' not in result
    
    def test_filename_property(self):
        """ErrorEvent.filename should pass through."""
        code = '''
def on_error(event):
    file = event.filename
'''
        result = transpile(code)
        assert 'event.filename' in result
        assert '__py.' not in result
    
    def test_lineno_property(self):
        """ErrorEvent.lineno should pass through."""
        code = '''
def on_error(event):
    line = event.lineno
'''
        result = transpile(code)
        assert 'event.lineno' in result
        assert '__py.' not in result
    
    def test_colno_property(self):
        """ErrorEvent.colno should pass through."""
        code = '''
def on_error(event):
    col = event.colno
'''
        result = transpile(code)
        assert 'event.colno' in result
        assert '__py.' not in result
    
    def test_error_property(self):
        """ErrorEvent.error should pass through."""
        code = '''
def on_error(event):
    err = event.error
'''
        result = transpile(code)
        assert 'event.error' in result
        assert '__py.' not in result


class TestErrorHandlingPatterns:
    """Tests for error handling patterns."""
    
    def test_window_error_listener(self):
        """Window error listener should work."""
        code = '''
from pynext.client import window

def on_error(event):
    log_error(event.message)

window.addEventListener("error", on_error)
'''
        result = transpile(code)
        assert 'addEventListener("error"' in result
    
    def test_error_stack_access(self):
        """Accessing error stack should work."""
        code = '''
def on_error(event):
    if event.error:
        stack = event.error.stack
        log_stack(stack)
'''
        result = transpile(code)
        assert 'event.error.stack' in result
    
    def test_unhandled_rejection(self):
        """unhandledrejection event should work."""
        code = '''
from pynext.client import window

def on_rejection(event):
    reason = event.reason
    log_rejection(reason)

window.addEventListener("unhandledrejection", on_rejection)
'''
        result = transpile(code)
        assert 'addEventListener("unhandledrejection"' in result
        assert 'event.reason' in result
    
    def test_error_report_pattern(self):
        """Error reporting pattern should work."""
        code = '''
from pynext.client import window

def setup_error_reporting(endpoint):
    def on_error(event):
        error_info = {
            "message": event.message,
            "file": event.filename,
            "line": event.lineno,
            "col": event.colno
        }
        fetch(endpoint, {"method": "POST", "body": JSON.stringify(error_info)})
    
    window.addEventListener("error", on_error)
'''
        result = transpile(code)
        assert 'event.message' in result
        assert 'event.filename' in result
        assert 'event.lineno' in result
        assert 'event.colno' in result
    
    def test_prevent_default_error(self):
        """Preventing default error handling should work."""
        code = '''
def on_error(event):
    if should_suppress(event.message):
        event.preventDefault()
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result

