"""
Phase 34.4: Form Event Tests

Unit tests for form-related event transpilation covering:
- Submit and reset events
- Input and change events
- Focus and blur events
- SubmitEvent.submitter
- InputEvent.inputType

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


class TestSubmitEvents:
    """Tests for form submission events."""
    
    def test_prevent_default_on_submit(self):
        """preventDefault on submit should pass through."""
        code = '''
def on_submit(event):
    event.preventDefault()
    handle_form(event.target)
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert 'event.target' in result
        assert '__py.' not in result
    
    def test_submitter_property(self):
        """SubmitEvent.submitter should pass through."""
        code = '''
def on_submit(event):
    button = event.submitter
'''
        result = transpile(code)
        assert 'event.submitter' in result
    
    def test_submitter_value(self):
        """Getting submitter value should work."""
        code = '''
def on_submit(event):
    if event.submitter:
        action = event.submitter.value
'''
        result = transpile(code)
        assert 'event.submitter' in result


class TestInputEvents:
    """Tests for input events."""
    
    def test_input_type_passthrough(self):
        """InputEvent.inputType should pass through."""
        code = '''
def on_input(event):
    input_type = event.inputType
'''
        result = transpile(code)
        assert 'event.inputType' in result
        assert '__py.' not in result
    
    def test_input_data_passthrough(self):
        """InputEvent.data should pass through."""
        code = '''
def on_input(event):
    char = event.data
'''
        result = transpile(code)
        assert 'event.data' in result
    
    def test_is_composing(self):
        """InputEvent.isComposing should pass through."""
        code = '''
def on_input(event):
    if event.isComposing:
        return
'''
        result = transpile(code)
        assert 'event.isComposing' in result
    
    def test_input_target_value(self):
        """Getting target value should work."""
        code = '''
def on_input(event):
    value = event.target.value
'''
        result = transpile(code)
        assert 'event.target.value' in result


class TestChangeEvents:
    """Tests for change events."""
    
    def test_change_target_value(self):
        """Getting changed value should work."""
        code = '''
def on_change(event):
    new_value = event.target.value
'''
        result = transpile(code)
        assert 'event.target.value' in result
    
    def test_change_checked(self):
        """Getting checkbox checked state should work."""
        code = '''
def on_change(event):
    is_checked = event.target.checked
'''
        result = transpile(code)
        assert 'event.target.checked' in result


class TestFocusEvents:
    """Tests for focus/blur events."""
    
    def test_focus_target(self):
        """Focus event target should pass through."""
        code = '''
def on_focus(event):
    event.target.classList.add("focused")
'''
        result = transpile(code)
        assert 'event.target' in result
        assert '__py.' not in result
    
    def test_blur_target(self):
        """Blur event target should pass through."""
        code = '''
def on_blur(event):
    validate(event.target.value)
'''
        result = transpile(code)
        assert 'event.target.value' in result
    
    def test_focus_related_target(self):
        """FocusEvent.relatedTarget should pass through."""
        code = '''
def on_focus(event):
    from_element = event.relatedTarget
'''
        result = transpile(code)
        assert 'event.relatedTarget' in result
    
    def test_blur_related_target(self):
        """Blur relatedTarget should pass through."""
        code = '''
def on_blur(event):
    to_element = event.relatedTarget
'''
        result = transpile(code)
        assert 'event.relatedTarget' in result


class TestFormEventPatterns:
    """Tests for common form event patterns."""
    
    def test_form_validation_pattern(self):
        """Form validation on submit should work."""
        code = '''
def on_submit(event):
    event.preventDefault()
    form = event.target
    if validate_form(form):
        submit_form(form)
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert 'event.target' in result
    
    def test_input_debounce_pattern(self):
        """Input handler for debouncing should work."""
        code = '''
def on_input(event):
    if event.inputType == "insertText" or event.inputType == "deleteContentBackward":
        schedule_search(event.target.value)
'''
        result = transpile(code)
        assert 'event.inputType' in result
        assert 'event.target.value' in result
    
    def test_focus_ring_pattern(self):
        """Focus ring handling should work."""
        code = '''
def on_focus(event):
    event.target.classList.add("focus-ring")

def on_blur(event):
    event.target.classList.remove("focus-ring")
'''
        result = transpile(code)
        assert 'event.target.classList.add' in result
        assert 'event.target.classList.remove' in result
    
    def test_select_input_on_focus(self):
        """Selecting input text on focus should work."""
        code = '''
def on_focus(event):
    event.target.select()
'''
        result = transpile(code)
        assert 'event.target.select()' in result
    
    def test_prevent_form_reset(self):
        """Preventing form reset should work."""
        code = '''
def on_reset(event):
    if not confirm_reset():
        event.preventDefault()
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result

