"""
Phase 34.4: Event Target Type Narrowing Tests

Tests for safely accessing event.target properties when
the actual target may differ from expected element type.

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestTargetTypeChecks:
    """Tests for checking target element type before access."""
    
    def test_tagname_check_before_access(self):
        """Check tagName before accessing element-specific props."""
        code = '''
def on_click(event):
    if event.target.tagName == "BUTTON":
        event.target.disabled = True
'''
        result = transpile(code)
        assert 'event.target.tagName' in result
        assert 'event.target.disabled' in result
    
    def test_instanceof_check_pattern(self):
        """Use isinstance-equivalent check for element types."""
        code = '''
def on_click(event):
    target = event.target
    if hasattr(target, "value"):
        process_input(target.value)
'''
        result = transpile(code)
        assert 'event.target' in result
    
    def test_closest_for_delegation(self):
        """Use closest() for event delegation safety."""
        code = '''
def on_click(event):
    button = event.target.closest("button")
    if button:
        handle_button_click(button)
'''
        result = transpile(code)
        assert 'event.target.closest("button")' in result
    
    def test_matches_selector_check(self):
        """Use matches() to verify element type."""
        code = '''
def on_click(event):
    if event.target.matches("input[type='checkbox']"):
        toggle_state(event.target.checked)
'''
        result = transpile(code)
        assert 'event.target.matches' in result


class TestCurrentTargetVsTarget:
    """Tests for currentTarget (listener element) vs target (actual clicked)."""
    
    def test_current_target_is_listener(self):
        """currentTarget is always the element with the listener."""
        code = '''
def on_click(event):
    container = event.currentTarget
    clicked = event.target
    container.classList.add("active")
'''
        result = transpile(code)
        assert 'event.currentTarget' in result
        assert 'event.target' in result
    
    def test_delegation_with_data_attribute(self):
        """Use data attributes for delegation identification."""
        code = '''
def on_click(event):
    item = event.target.closest("[data-item-id]")
    if item:
        item_id = item.dataset.itemId
        select_item(item_id)
'''
        result = transpile(code)
        assert 'closest' in result
        assert 'dataset' in result
    
    def test_prevent_bubbling_from_child(self):
        """Prevent action if click was on specific child."""
        code = '''
def on_container_click(event):
    if event.target.classList.contains("delete-btn"):
        return  # Let delete handler handle it
    select_item(event.currentTarget)
'''
        result = transpile(code)
        assert 'event.target.classList.contains' in result


class TestNullTargetSafety:
    """Tests for handling potentially null targets."""
    
    def test_target_removed_during_event(self):
        """Handle case where target is removed from DOM during event."""
        code = '''
def on_click(event):
    parent = event.target.parentElement
    if parent:
        process(parent)
'''
        result = transpile(code)
        assert 'event.target.parentElement' in result
    
    def test_related_target_null_check(self):
        """relatedTarget can be null for focus/blur."""
        code = '''
def on_blur(event):
    if event.relatedTarget:
        if event.relatedTarget.closest(".dropdown"):
            return  # Staying in dropdown
    close_dropdown()
'''
        result = transpile(code)
        assert 'event.relatedTarget' in result
    
    def test_composed_path_empty(self):
        """Handle empty composedPath for detached events."""
        code = '''
def on_custom(event):
    path = event.composedPath()
    if len(path) > 0:
        root = path[-1]
'''
        result = transpile(code)
        assert 'event.composedPath()' in result


class TestFormElementTargets:
    """Tests for form element target specifics."""
    
    def test_input_value_access(self):
        """Access input.value safely."""
        code = '''
def on_input(event):
    if event.target.tagName == "INPUT":
        value = event.target.value
        validate(value)
'''
        result = transpile(code)
        assert 'event.target.value' in result
    
    def test_checkbox_checked_access(self):
        """Access checkbox.checked safely."""
        code = '''
def on_change(event):
    if event.target.type == "checkbox":
        is_checked = event.target.checked
        update_state(is_checked)
'''
        result = transpile(code)
        assert 'event.target.checked' in result
    
    def test_select_selected_option(self):
        """Access select.selectedOptions safely."""
        code = '''
def on_change(event):
    if event.target.tagName == "SELECT":
        selected = event.target.selectedOptions[0]
        if selected:
            handle_selection(selected.value)
'''
        result = transpile(code)
        assert 'event.target.selectedOptions' in result
    
    def test_form_elements_collection(self):
        """Access form.elements collection."""
        code = '''
def on_submit(event):
    form = event.target
    username = form.elements["username"].value
    password = form.elements["password"].value
'''
        result = transpile(code)
        assert 'form.elements' in result
    
    def test_fieldset_disabled_check(self):
        """Check if parent fieldset is disabled."""
        code = '''
def on_click(event):
    fieldset = event.target.closest("fieldset")
    if fieldset and fieldset.disabled:
        return  # Ignore clicks in disabled fieldset
'''
        result = transpile(code)
        assert 'fieldset.disabled' in result

