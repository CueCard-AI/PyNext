"""
Phase 34.4: History Event Tests

Unit tests for history event transpilation covering:
- hashchange events
- popstate events
- beforeunload events
- History API integration

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestHashChangeEvent:
    """Tests for HashChangeEvent."""
    
    def test_hashchange_listener(self):
        """hashchange listener should work."""
        code = '''
from pynext.client import window

def on_hashchange(event):
    handle_hash()

window.addEventListener("hashchange", on_hashchange)
'''
        result = transpile(code)
        assert 'addEventListener("hashchange"' in result
    
    def test_old_url_property(self):
        """HashChangeEvent.oldURL should pass through."""
        code = '''
def on_hashchange(event):
    old = event.oldURL
'''
        result = transpile(code)
        assert 'event.oldURL' in result
        assert '__py.' not in result
    
    def test_new_url_property(self):
        """HashChangeEvent.newURL should pass through."""
        code = '''
def on_hashchange(event):
    new = event.newURL
'''
        result = transpile(code)
        assert 'event.newURL' in result
        assert '__py.' not in result


class TestPopStateEvent:
    """Tests for PopStateEvent."""
    
    def test_popstate_listener(self):
        """popstate listener should work."""
        code = '''
from pynext.client import window

def on_popstate(event):
    handle_navigation()

window.addEventListener("popstate", on_popstate)
'''
        result = transpile(code)
        assert 'addEventListener("popstate"' in result
    
    def test_state_property(self):
        """PopStateEvent.state should pass through."""
        code = '''
def on_popstate(event):
    state = event.state
'''
        result = transpile(code)
        assert 'event.state' in result
        assert '__py.' not in result
    
    def test_state_access_pattern(self):
        """Accessing state data should work."""
        code = '''
def on_popstate(event):
    if event.state:
        route = event.state["route"]
        render_route(route)
    else:
        render_home()
'''
        result = transpile(code)
        assert 'event.state' in result


class TestBeforeUnloadEvent:
    """Tests for BeforeUnloadEvent."""
    
    def test_beforeunload_listener(self):
        """beforeunload listener should work."""
        code = '''
from pynext.client import window

def on_beforeunload(event):
    handle_unload()

window.addEventListener("beforeunload", on_beforeunload)
'''
        result = transpile(code)
        assert 'addEventListener("beforeunload"' in result
    
    def test_return_value_property(self):
        """BeforeUnloadEvent.returnValue should pass through."""
        code = '''
def on_beforeunload(event):
    event.returnValue = ""
'''
        result = transpile(code)
        assert 'event.returnValue' in result
    
    def test_unsaved_changes_pattern(self):
        """Unsaved changes warning pattern should work."""
        code = '''
from pynext.client import window

has_unsaved_changes = False

def on_beforeunload(event):
    if has_unsaved_changes:
        event.preventDefault()
        event.returnValue = ""

window.addEventListener("beforeunload", on_beforeunload)
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert 'event.returnValue' in result
    
    def test_history_push_state(self):
        """history.pushState should work."""
        code = '''
from pynext.client import history

def navigate_to(route):
    history.pushState({"route": route}, "", route)
'''
        result = transpile(code)
        assert 'history.pushState' in result

