"""
Phase 34.4: Focus Management Edge Cases

Tests for focus handling in complex UI patterns:
- Focus trapping in modals
- Focus restoration
- activeElement tracking

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestFocusTrap:
    """Tests for focus trapping in modals/dialogs."""
    
    def test_focus_first_element(self):
        """Focus first focusable element in modal."""
        code = '''
def open_modal(modal):
    focusable = modal.querySelector("button, input, [tabindex]")
    if focusable:
        focusable.focus()
'''
        result = transpile(code)
        assert 'modal.querySelector' in result
        assert 'focusable.focus()' in result
    
    def test_trap_focus_on_tab(self):
        """Trap focus within modal on Tab key."""
        code = '''
def on_keydown(event):
    if event.key == "Tab":
        focusables = modal.querySelectorAll("button, input, [tabindex]")
        first = focusables[0]
        last = focusables[focusables.length - 1]
        
        if event.shiftKey and document.activeElement == first:
            event.preventDefault()
            last.focus()
        elif not event.shiftKey and document.activeElement == last:
            event.preventDefault()
            first.focus()
'''
        result = transpile(code)
        assert 'document.activeElement' in result
        assert 'event.shiftKey' in result
        assert 'event.preventDefault()' in result
    
    def test_get_all_focusables(self):
        """Query all focusable elements."""
        code = '''
FOCUSABLE_SELECTOR = "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"

def get_focusables(container):
    return container.querySelectorAll(FOCUSABLE_SELECTOR)
'''
        result = transpile(code)
        assert 'querySelectorAll' in result


class TestFocusRestoration:
    """Tests for restoring focus after modal close."""
    
    def test_save_previous_focus(self):
        """Save previously focused element before modal."""
        code = '''
previous_focus = None

def open_modal():
    global previous_focus
    previous_focus = document.activeElement
    modal.classList.add("open")
    modal.querySelector("button").focus()
'''
        result = transpile(code)
        assert 'document.activeElement' in result
    
    def test_restore_focus_on_close(self):
        """Restore focus when modal closes."""
        code = '''
def close_modal():
    modal.classList.remove("open")
    if previous_focus:
        previous_focus.focus()
'''
        result = transpile(code)
        assert 'previous_focus.focus()' in result
    
    def test_focus_restoration_if_removed(self):
        """Handle case where previous element was removed."""
        code = '''
def close_modal():
    modal.classList.remove("open")
    if previous_focus and document.contains(previous_focus):
        previous_focus.focus()
    else:
        document.body.focus()
'''
        result = transpile(code)
        assert 'document.contains' in result


class TestActiveElementTracking:
    """Tests for document.activeElement behavior."""
    
    def test_active_element_during_blur(self):
        """activeElement changes during blur sequence."""
        code = '''
def on_blur(event):
    # activeElement may be body during blur
    setTimeout(lambda: check_focus(), 0)

def check_focus():
    active = document.activeElement
    if active == document.body:
        handle_focus_lost()
'''
        result = transpile(code)
        assert 'document.activeElement' in result
        assert 'document.body' in result
    
    def test_focus_within_shadow_dom(self):
        """Access activeElement in shadow root."""
        code = '''
def get_deep_active_element():
    active = document.activeElement
    while active and active.shadowRoot:
        active = active.shadowRoot.activeElement
    return active
'''
        result = transpile(code)
        assert 'shadowRoot' in result
        assert 'activeElement' in result
    
    def test_programmatic_focus(self):
        """Programmatically set focus."""
        code = '''
def focus_input(input_id):
    element = document.getElementById(input_id)
    if element:
        element.focus()
        element.select()  # Select text if input
'''
        result = transpile(code)
        assert 'element.focus()' in result
        assert 'element.select()' in result


class TestFocusEvents:
    """Tests for focus/blur event edge cases."""
    
    def test_focusin_bubbles(self):
        """focusin event bubbles (unlike focus)."""
        code = '''
def on_focusin(event):
    container = event.currentTarget
    container.classList.add("has-focus")
'''
        result = transpile(code)
        assert 'event.currentTarget' in result
    
    def test_focusout_related_target(self):
        """Check where focus is going on focusout."""
        code = '''
def on_focusout(event):
    if not event.relatedTarget:
        # Focus left the document
        save_draft()
    elif not event.currentTarget.contains(event.relatedTarget):
        # Focus left this container
        validate_form()
'''
        result = transpile(code)
        assert 'event.relatedTarget' in result
        assert 'contains' in result
    
    def test_focus_visible_detection(self):
        """Detect keyboard vs mouse focus."""
        code = '''
def on_focus(event):
    if event.target.matches(":focus-visible"):
        show_focus_ring()
    else:
        hide_focus_ring()
'''
        result = transpile(code)
        assert ':focus-visible' in result
    
    def test_prevent_focus_steal(self):
        """Prevent element from stealing focus."""
        code = '''
def on_mousedown(event):
    if event.target.classList.contains("no-focus"):
        event.preventDefault()  # Prevents focus
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
    
    def test_tabindex_management(self):
        """Manage tabindex for roving focus."""
        code = '''
def set_roving_tabindex(items, active_index):
    for i, item in enumerate(items):
        if i == active_index:
            item.tabIndex = 0
        else:
            item.tabIndex = -1
'''
        result = transpile(code)
        assert 'tabIndex' in result

