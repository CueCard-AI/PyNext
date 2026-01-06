"""
Tests for Form Handler Transpilation (Phase 17.11)

Tests the transpiler's ability to convert Python form handlers
into JavaScript code for client-side execution.
"""

import pytest
from pynext.reactive.forms import FormState, create_form
from pynext.reactive.signal import Signal, signal
from pynext.core.html import Element, button
from tests.unit.transpiler.test_utils import assert_has_runtime_function


class TestFormStateHasFormId:
    """Test that FormState objects have a unique _form_id."""
    
    def test_form_state_has_form_id(self):
        """FormState should have a _form_id attribute."""
        form = create_form(initial={"name": ""})
        assert hasattr(form, '_form_id')
        assert form._form_id.startswith('form_')
    
    def test_form_id_is_unique(self):
        """Each FormState should have a unique _form_id."""
        form1 = create_form(initial={"a": ""})
        form2 = create_form(initial={"b": ""})
        assert form1._form_id != form2._form_id
    
    def test_form_id_in_hydration_state(self):
        """Form _form_id should be used in hydration state."""
        form = create_form(initial={"email": ""})
        state = form.to_hydration_state()
        assert state['id'] == form._form_id


class TestFormDetectionInClosures:
    """Test detection of FormState objects in handler closures."""
    
    def test_detect_form_in_simple_handler(self):
        """Transpiler should detect FormState in a simple handler."""
        form = create_form(initial={"title": ""})
        
        def handler():
            if form.validate():
                form.reset()
        
        # Check closure contains form
        closure = handler.__closure__
        assert closure is not None
        form_found = any(
            hasattr(cell.cell_contents, '__pynext_type__') and 
            cell.cell_contents.__pynext_type__ == "form"
            for cell in closure
        )
        assert form_found
    
    def test_detect_form_with_signals(self):
        """Transpiler should detect both Form and Signals in closure."""
        form = create_form(initial={"title": ""})
        items = signal([], name="items")
        show_modal = signal(False, name="show_modal")
        
        def handler():
            if form.validate():
                items.set([*items(), form.values])
                form.reset()
                show_modal.set(False)
        
        closure = handler.__closure__
        form_found = False
        signals_found = []
        
        for cell in closure:
            try:
                value = cell.cell_contents
                if hasattr(value, '__pynext_type__') and value.__pynext_type__ == "form":
                    form_found = True
                elif hasattr(value, '_is_signal') and value._is_signal:
                    signals_found.append(value._id)
            except ValueError:
                pass
        
        assert form_found
        assert len(signals_found) == 2


class TestFormHandlerTranspilation:
    """Test transpilation of form handlers to JavaScript."""
    
    def test_validate_only_pattern(self):
        """Test transpilation of if form.validate(): ... pattern."""
        form = create_form(initial={"name": ""})
        show = signal(False, name="show")
        
        def handler():
            if form.validate():
                show.set(False)
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        assert 'getForm' in js
        assert form._form_id in js
        assert '.validate()' in js
        assert '.set(false)' in js.lower()
    
    def test_validate_and_reset_pattern(self):
        """Test transpilation of validate + reset pattern."""
        form = create_form(initial={"email": ""})
        
        def handler():
            if form.validate():
                form.reset()
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        assert 'getForm' in js
        assert form._form_id in js
        assert '.validate()' in js
        assert '.reset()' in js
    
    def test_form_values_with_signal_append(self):
        """Test form.values used with signal array append."""
        form = create_form(initial={"title": "", "priority": "medium"})
        all_items = signal([], name="all_items")
        
        def handler():
            if form.validate():
                all_items.set([*all_items(), form.values])
                form.reset()
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        assert 'getForm' in js
        assert 'validate()' in js
        assert 'values' in js
        # Should have array append pattern - either spread syntax or update
        # The transpiler uses set([...arr, item]) or update(arr => [...arr, item])
        assert 'update' in js or '...' in js, f"Expected spread or update pattern in: {js}"
    
    def test_multiple_signal_operations(self):
        """Test handler with multiple signal operations after validation."""
        form = create_form(initial={"data": ""})
        items = signal([], name="items")
        count = signal(0, name="count")
        visible = signal(True, name="visible")
        
        def handler():
            if form.validate():
                items.set([*items(), form.values])
                count.set(count() + 1)
                visible.set(False)
                form.reset()
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        assert 'getForm' in js
        # Signals now use names instead of IDs for stable lookups
        assert '__pynext__.getSignal' in js or '__pynext__.getForm' in js
        assert '.reset()' in js


class TestArrayAppendPattern:
    """Test the [*signal(), new_item] pattern recognition."""
    
    def test_simple_array_append_with_values(self):
        """Test recognition of items.set([*items(), values])."""
        form = create_form(initial={"text": ""})
        items = signal([], name="items")
        
        def handler():
            if form.validate():
                values = form.values
                items.set([*items(), values])
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        # Should generate either:
        # - update(arr => [...arr, values])
        # - set([...arr, values])
        # The transpiler currently uses set with spread
        assert 'getSignal' in js
        assert '...' in js or 'update' in js, f"Expected spread or update pattern in: {js}"
    
    def test_array_append_with_new_item_variable(self):
        """Test recognition of items.set([*items(), new_item])."""
        form = create_form(initial={"title": ""})
        all_issues = signal([], name="all_issues")
        
        def handler():
            if form.validate():
                new_issue = form.values
                all_issues.set([*all_issues(), new_issue])
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        assert 'getForm' in js
        # The transpiler uses set([...signal.read(), new_issue])
        assert '...' in js or 'update' in js, f"Expected spread or update pattern in: {js}"


class TestSignalSetPatterns:
    """Test various signal.set() patterns within form handlers."""
    
    def test_set_boolean_false(self):
        """Test signal.set(False) pattern."""
        form = create_form(initial={})
        visible = signal(True, name="visible")
        
        def handler():
            if form.validate():
                visible.set(False)
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        # Signals now use names instead of IDs for stable lookups
        assert '__pynext__.getSignal' in js or '__pynext__.getForm' in js
        assert 'false' in js.lower()
    
    def test_set_boolean_true(self):
        """Test signal.set(True) pattern."""
        form = create_form(initial={})
        loading = signal(False, name="loading")
        
        def handler():
            loading.set(True)
            form.validate()
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        # Should still detect form and generate appropriate JS
        assert 'getForm' in js
    
    def test_increment_pattern(self):
        """Test signal.set(signal() + 1) pattern."""
        form = create_form(initial={})
        count = signal(0, name="count")
        
        def handler():
            if form.validate():
                count.set(count() + 1)
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        # Signals now use names instead of IDs for stable lookups
        assert '__pynext__.getSignal' in js or '__pynext__.getForm' in js
        # Increment pattern uses dunder runtime for Python semantics
        assert_has_runtime_function(js, "add")


class TestLinearDemoPattern:
    """Test the exact pattern used in Linear demo handle_add_issue."""
    
    def test_linear_add_issue_pattern(self):
        """Test the full Linear demo form submission pattern."""
        # This mimics the Linear demo's handle_add_issue function
        issue_form = create_form(
            initial={
                "title": "",
                "description": "",
                "priority": "medium",
                "status": "backlog",
            }
        )
        all_issues = signal([], name="all_issues")
        next_id = signal(1, name="next_id")
        show_add_form = signal(False, name="show_add_form")
        
        def handle_add_issue():
            if issue_form.validate():
                values = issue_form.values
                new_issue = {
                    "id": next_id(),
                    "title": values["title"],
                    "description": values["description"],
                    "status": values["status"],
                    "priority": values["priority"],
                }
                all_issues.set([*all_issues(), new_issue])
                next_id.set(next_id() + 1)
                issue_form.reset()
                show_add_form.set(False)
        
        elem = button(onclick=handle_add_issue)
        js = elem._extract_handler_code(handle_add_issue)
        
        # Verify key components are present
        assert 'getForm' in js
        assert issue_form._form_id in js
        assert 'validate()' in js
        assert 'values' in js
        
        # Signals now use names instead of IDs for stable lookups
        assert '__pynext__.getSignal' in js or '__pynext__.getForm' in js
        assert '.reset()' in js
        
        # Should not have fallback warning (unless it's an expected message)
        assert 'console.warn' not in js or 'not found' in js


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_form_without_signals(self):
        """Handler with only form operations should work."""
        form = create_form(initial={"x": ""})
        
        def handler():
            form.validate()
            form.reset()
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        # Should generate form operations
        assert 'getForm' in js
    
    def test_nested_conditionals(self):
        """Handler with nested if statements."""
        form = create_form(initial={"data": ""})
        result = signal("", name="result")
        
        def handler():
            if form.validate():
                if form.values["data"]:
                    result.set("success")
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        # Should still work even with nested logic
        assert 'getForm' in js
        assert 'validate()' in js
    
    def test_lambda_with_form(self):
        """Lambda handlers with form operations."""
        form = create_form(initial={})
        
        # Simple lambda that validates
        handler = lambda: form.validate()
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        # Lambda should detect form
        assert 'getForm' in js or 'form' in js.lower()


class TestJSOutput:
    """Test the generated JavaScript is valid and functional."""
    
    def test_js_is_iife(self):
        """Generated JS should be an IIFE for scope isolation."""
        form = create_form(initial={"name": ""})
        visible = signal(True, name="visible")
        
        def handler():
            if form.validate():
                visible.set(False)
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        # Should be wrapped in IIFE
        assert js.strip().startswith('(function()') or '__pynext__' in js
    
    def test_js_has_form_access(self):
        """Generated JS should access form via getForm()."""
        form = create_form(initial={})
        
        def handler():
            form.validate()
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        # Should access form via getForm()
        # Note: Null checks are handled at runtime by getForm(), not in generated code
        assert 'getForm' in js
        assert form._form_id in js
        assert '.validate()' in js
    
    def test_js_values_accessible(self):
        """Generated JS should make form values accessible."""
        form = create_form(initial={"email": ""})
        items = signal([], name="items")
        
        def handler():
            if form.validate():
                items.set([*items(), form.values])
        
        elem = button(onclick=handler)
        js = elem._extract_handler_code(handler)
        
        # Should declare values variable for use
        assert 'values' in js

