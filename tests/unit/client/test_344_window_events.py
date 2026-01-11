"""
Phase 34.4: Window and Document Event Tests

Unit tests for window/document event transpilation covering:
- resize, scroll events
- beforeunload, hashchange, popstate
- visibilitychange, online/offline
- DOMContentLoaded, load, error

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


class TestResizeEvents:
    """Tests for window resize events."""
    
    def test_resize_event_listener(self):
        """Window resize listener should pass through."""
        code = '''
from pynext.client import window

def on_resize(event):
    handle_resize()

window.addEventListener("resize", on_resize)
'''
        result = transpile(code)
        assert 'addEventListener("resize"' in result
        assert '__py.' not in result
    
    def test_resize_with_dimensions(self):
        """Getting window dimensions on resize should work."""
        code = '''
from pynext.client import window

def on_resize(event):
    width = window.innerWidth
    height = window.innerHeight
    update_layout(width, height)

window.addEventListener("resize", on_resize)
'''
        result = transpile(code)
        assert 'window.innerWidth' in result
        assert 'window.innerHeight' in result
    
    def test_resize_passive(self):
        """Passive resize listener should work."""
        code = '''
window.addEventListener("resize", on_resize, {"passive": True})
'''
        result = transpile(code)
        assert 'passive' in result


class TestScrollEvents:
    """Tests for scroll events."""
    
    def test_window_scroll_event(self):
        """Window scroll event should pass through."""
        code = '''
from pynext.client import window

def on_scroll(event):
    handle_scroll()

window.addEventListener("scroll", on_scroll)
'''
        result = transpile(code)
        assert 'addEventListener("scroll"' in result
    
    def test_document_scroll_position(self):
        """Getting scroll position should work."""
        code = '''
from pynext.client import document

def on_scroll(event):
    scroll_top = document.documentElement.scrollTop
    scroll_height = document.documentElement.scrollHeight
'''
        result = transpile(code)
        assert 'document.documentElement.scrollTop' in result
        assert 'document.documentElement.scrollHeight' in result
    
    def test_element_scroll_event(self):
        """Element scroll event should work."""
        code = '''
def on_scroll(event):
    top = event.target.scrollTop
    left = event.target.scrollLeft

container.addEventListener("scroll", on_scroll)
'''
        result = transpile(code)
        assert 'event.target.scrollTop' in result
        assert 'event.target.scrollLeft' in result
    
    def test_passive_scroll(self):
        """Passive scroll listener should work."""
        code = '''
window.addEventListener("scroll", on_scroll, {"passive": True})
'''
        result = transpile(code)
        assert 'passive' in result


class TestBeforeUnloadEvents:
    """Tests for beforeunload events."""
    
    def test_beforeunload_listener(self):
        """beforeunload listener should pass through."""
        code = '''
from pynext.client import window

def on_beforeunload(event):
    if has_unsaved_changes():
        event.preventDefault()
        event.returnValue = ""

window.addEventListener("beforeunload", on_beforeunload)
'''
        result = transpile(code)
        assert 'addEventListener("beforeunload"' in result
        assert 'event.returnValue' in result


class TestHistoryEvents:
    """Tests for browser history events."""
    
    def test_hashchange_event(self):
        """hashchange event should pass through."""
        code = '''
from pynext.client import window

def on_hashchange(event):
    new_hash = location.hash
    navigate_to_section(new_hash)

window.addEventListener("hashchange", on_hashchange)
'''
        result = transpile(code)
        assert 'addEventListener("hashchange"' in result
    
    def test_popstate_event(self):
        """popstate event should pass through."""
        code = '''
from pynext.client import window

def on_popstate(event):
    state = event.state
    if state:
        restore_state(state)

window.addEventListener("popstate", on_popstate)
'''
        result = transpile(code)
        assert 'addEventListener("popstate"' in result
        assert 'event.state' in result
    
    def test_popstate_with_history(self):
        """popstate with history API should work."""
        code = '''
from pynext.client import window, history

def on_popstate(event):
    if event.state:
        page = event.state["page"]
        render_page(page)

window.addEventListener("popstate", on_popstate)
'''
        result = transpile(code)
        assert 'event.state' in result


class TestVisibilityEvents:
    """Tests for page visibility events."""
    
    def test_visibilitychange_event(self):
        """visibilitychange event should pass through."""
        code = '''
from pynext.client import document

def on_visibility_change(event):
    if document.hidden:
        pause_video()
    else:
        resume_video()

document.addEventListener("visibilitychange", on_visibility_change)
'''
        result = transpile(code)
        assert 'addEventListener("visibilitychange"' in result
        assert 'document.hidden' in result
    
    def test_visibility_state(self):
        """document.visibilityState should pass through."""
        code = '''
from pynext.client import document

def check_visibility():
    state = document.visibilityState
    if state == "hidden":
        pause_all()
'''
        result = transpile(code)
        assert 'document.visibilityState' in result


class TestNetworkEvents:
    """Tests for network status events."""
    
    def test_online_event(self):
        """online event should pass through."""
        code = '''
from pynext.client import window

def on_online(event):
    show_notification("Back online")
    sync_data()

window.addEventListener("online", on_online)
'''
        result = transpile(code)
        assert 'addEventListener("online"' in result
    
    def test_offline_event(self):
        """offline event should pass through."""
        code = '''
from pynext.client import window

def on_offline(event):
    show_notification("You are offline")
    enable_offline_mode()

window.addEventListener("offline", on_offline)
'''
        result = transpile(code)
        assert 'addEventListener("offline"' in result


class TestLoadEvents:
    """Tests for page load events."""
    
    def test_dom_content_loaded(self):
        """DOMContentLoaded event should pass through."""
        code = '''
from pynext.client import document

def on_ready(event):
    initialize_app()

document.addEventListener("DOMContentLoaded", on_ready)
'''
        result = transpile(code)
        assert 'addEventListener("DOMContentLoaded"' in result
    
    def test_window_load(self):
        """window load event should pass through."""
        code = '''
from pynext.client import window

def on_load(event):
    all_resources_loaded()

window.addEventListener("load", on_load)
'''
        result = transpile(code)
        assert 'addEventListener("load"' in result


class TestErrorEvents:
    """Tests for error events."""
    
    def test_window_error(self):
        """window error event should pass through."""
        code = '''
from pynext.client import window

def on_error(event):
    log_error(event.message)
    event.preventDefault()

window.addEventListener("error", on_error)
'''
        result = transpile(code)
        assert 'addEventListener("error"' in result
    
    def test_unhandled_rejection(self):
        """unhandledrejection event should pass through."""
        code = '''
from pynext.client import window

def on_rejection(event):
    log_rejection(event.reason)

window.addEventListener("unhandledrejection", on_rejection)
'''
        result = transpile(code)
        assert 'addEventListener("unhandledrejection"' in result

