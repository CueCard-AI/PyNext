"""
Phase 34.4: Event Edge Cases Tests

Unit tests for edge cases and special scenarios covering:
- Null/undefined handling
- Type guards
- Chained property access
- Multiple events
- Event constructor edge cases

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestNullHandling:
    """Tests for null/undefined edge cases."""
    
    def test_optional_related_target(self):
        """relatedTarget may be null."""
        code = '''
def handle(event):
    if event.relatedTarget:
        from_el = event.relatedTarget
'''
        result = transpile(code)
        assert 'event.relatedTarget' in result
    
    def test_optional_submitter(self):
        """submitter may be null."""
        code = '''
def handle(event):
    if event.submitter:
        action = event.submitter.value
'''
        result = transpile(code)
        assert 'event.submitter' in result
    
    def test_optional_data_transfer(self):
        """dataTransfer may be null."""
        code = '''
def handle(event):
    if event.dataTransfer:
        files = event.dataTransfer.files
'''
        result = transpile(code)
        assert 'event.dataTransfer' in result


class TestChainedAccess:
    """Tests for chained property access."""
    
    def test_deep_target_chain(self):
        """Deep target property chain should work."""
        code = '''
def handle(event):
    parent_id = event.target.parentElement.id
'''
        result = transpile(code)
        assert 'event.target.parentElement.id' in result
    
    def test_target_class_list_chain(self):
        """target.classList chaining should work."""
        code = '''
def handle(event):
    event.target.classList.add("active")
    event.target.classList.remove("inactive")
'''
        result = transpile(code)
        assert 'event.target.classList.add' in result
        assert 'event.target.classList.remove' in result
    
    def test_data_transfer_files_chain(self):
        """dataTransfer.files chaining should work."""
        code = '''
def handle(event):
    first_file_name = event.dataTransfer.files[0].name
'''
        result = transpile(code)
        assert 'event.dataTransfer.files' in result


class TestMultipleEvents:
    """Tests for handling multiple event types."""
    
    def test_multiple_listeners_same_element(self):
        """Multiple listeners on same element should work."""
        code = '''
from pynext.client import document

el = document.getElementById("btn")
el.addEventListener("mouseenter", on_enter)
el.addEventListener("mouseleave", on_leave)
el.addEventListener("click", on_click)
'''
        result = transpile(code)
        assert 'addEventListener("mouseenter"' in result
        assert 'addEventListener("mouseleave"' in result
        assert 'addEventListener("click"' in result
    
    def test_same_handler_multiple_events(self):
        """Same handler for multiple events should work."""
        code = '''
def unified_handler(event):
    handle(event.type, event.target)

el.addEventListener("focus", unified_handler)
el.addEventListener("blur", unified_handler)
'''
        result = transpile(code)
        assert 'event.type' in result


class TestEventConstruction:
    """Tests for Event/CustomEvent constructor edge cases."""
    
    def test_event_constructor(self):
        """Base Event constructor should work."""
        code = '''
event = Event("custom-type")
'''
        result = transpile(code)
        assert 'Event("custom-type")' in result
    
    def test_event_with_options(self):
        """Event with options should work."""
        code = '''
event = Event("custom", {"bubbles": True, "cancelable": True})
'''
        result = transpile(code)
        assert 'Event(' in result
        assert 'bubbles' in result
    
    def test_mouse_event_constructor(self):
        """MouseEvent constructor should work."""
        code = '''
event = MouseEvent("click", {"clientX": 100, "clientY": 200})
'''
        result = transpile(code)
        assert 'MouseEvent("click"' in result
    
    def test_keyboard_event_constructor(self):
        """KeyboardEvent constructor should work."""
        code = '''
event = KeyboardEvent("keydown", {"key": "Enter", "code": "Enter"})
'''
        result = transpile(code)
        assert 'KeyboardEvent("keydown"' in result


class TestComplexPatterns:
    """Tests for complex event handling patterns."""
    
    def test_event_delegation(self):
        """Event delegation pattern should work."""
        code = '''
def handle(event):
    target = event.target
    while target and target != event.currentTarget:
        if target.matches(".clickable"):
            handle_click(target)
            break
        target = target.parentElement
'''
        result = transpile(code)
        assert 'event.target' in result
        assert 'event.currentTarget' in result
        assert 'target.matches' in result
    
    def test_conditional_prevent(self):
        """Conditional preventDefault pattern should work."""
        code = '''
def handle(event):
    if event.target.tagName == "A" and event.target.href:
        event.preventDefault()
        navigate(event.target.href)
'''
        result = transpile(code)
        assert 'event.target.tagName' in result
        assert 'event.preventDefault()' in result

