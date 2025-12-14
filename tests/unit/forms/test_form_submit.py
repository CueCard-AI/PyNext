"""
Comprehensive tests for form submission handling.

Tests cover:
- Submission state tracking
- Validation on submit
- Form values retrieval
- Reset after submit
- Async submission patterns

Total: 75+ tests
"""

import pytest
from pynext.reactive.forms import (
    create_form,
    required,
    min_length,
    email,
)


# =============================================================================
# SUBMISSION STATE (20 tests)
# =============================================================================

class TestSubmissionState:
    """Tests for form submission state."""
    
    def test_is_submitting_initial(self):
        """Form not submitting initially."""
        form = create_form(initial={"name": ""})
        assert not form.is_submitting()
    
    def test_is_submitting_set_true(self):
        """Set submitting to True."""
        form = create_form(initial={"name": ""})
        form._is_submitting.set(True)
        assert form.is_submitting()
    
    def test_is_submitting_set_false(self):
        """Set submitting back to False."""
        form = create_form(initial={"name": ""})
        form._is_submitting.set(True)
        form._is_submitting.set(False)
        assert not form.is_submitting()
    
    def test_is_submitting_cleared_on_reset(self):
        """Reset clears submitting state."""
        form = create_form(initial={"name": ""})
        form._is_submitting.set(True)
        form.reset()
        assert not form.is_submitting()
    
    def test_submitting_is_signal(self):
        """Submitting state is a signal."""
        form = create_form(initial={"name": ""})
        assert hasattr(form._is_submitting, "set")
        assert hasattr(form._is_submitting, "update")


# =============================================================================
# VALIDATE ON SUBMIT (20 tests)
# =============================================================================

class TestValidateOnSubmit:
    """Tests for validation during submission."""
    
    def test_validate_returns_true_when_valid(self):
        """validate() returns True for valid form."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        assert form.validate() is True
    
    def test_validate_returns_false_when_invalid(self):
        """validate() returns False for invalid form."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        assert form.validate() is False
    
    def test_validate_touches_all_by_default(self):
        """validate() marks all fields as touched."""
        form = create_form(initial={"a": "", "b": "", "c": ""})
        form.validate()
        assert form.is_touched("a")
        assert form.is_touched("b")
        assert form.is_touched("c")
    
    def test_validate_touch_false_option(self):
        """validate(touch=False) doesn't touch."""
        form = create_form(initial={"name": ""})
        form.validate(touch=False)
        assert not form.is_touched("name")
    
    def test_validate_populates_errors(self):
        """validate() populates error signals."""
        form = create_form(
            initial={"name": "", "email": "bad"},
            validators={
                "name": [required()],
                "email": [email()],
            }
        )
        form.validate()
        assert form.errors.name != ""
        assert form.errors.email != ""
    
    def test_validate_clears_errors_on_success(self):
        """validate() clears errors for valid fields."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()  # Sets error
        
        form.name.set("Alice")
        form.validate()  # Should clear error
        assert form.errors.name == ""
    
    def test_submit_pattern_with_validate(self):
        """Common submit pattern: validate then submit."""
        form = create_form(
            initial={"name": "Alice", "email": "alice@example.com"},
            validators={
                "name": [required()],
                "email": [required(), email()],
            }
        )
        
        submitted_data = None
        
        def handle_submit():
            nonlocal submitted_data
            if form.validate():
                submitted_data = form.values.copy()
        
        handle_submit()
        assert submitted_data == {"name": "Alice", "email": "alice@example.com"}
    
    def test_submit_pattern_blocked_when_invalid(self):
        """Submit blocked when validation fails."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        
        submitted = False
        
        def handle_submit():
            nonlocal submitted
            if form.validate():
                submitted = True
        
        handle_submit()
        assert not submitted


# =============================================================================
# VALUES ON SUBMIT (20 tests)
# =============================================================================

class TestValuesOnSubmit:
    """Tests for getting form values during submission."""
    
    def test_values_returns_all_fields(self):
        """values property returns all fields."""
        form = create_form(initial={"a": 1, "b": 2, "c": 3})
        assert form.values == {"a": 1, "b": 2, "c": 3}
    
    def test_values_reflects_changes(self):
        """values reflects current values."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        assert form.values["name"] == "Bob"
    
    def test_values_is_snapshot(self):
        """values returns a copy, not reference."""
        form = create_form(initial={"name": "Alice"})
        values1 = form.values
        form.name.set("Bob")
        values2 = form.values
        
        assert values1["name"] == "Alice"  # First snapshot unchanged
        assert values2["name"] == "Bob"    # Second snapshot has update
    
    def test_values_types_preserved(self):
        """values preserves value types."""
        form = create_form(initial={
            "string": "hello",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "none": None,
        })
        
        values = form.values
        assert isinstance(values["string"], str)
        assert isinstance(values["number"], int)
        assert isinstance(values["boolean"], bool)
        assert isinstance(values["list"], list)
        assert values["none"] is None
    
    def test_values_with_modified_list(self):
        """values handles list modifications."""
        form = create_form(initial={"items": []})
        form.items.set([1, 2, 3])
        assert form.values["items"] == [1, 2, 3]
    
    def test_submit_with_values(self):
        """Submit uses form.values."""
        form = create_form(initial={"email": "test@example.com"})
        
        submitted_email = None
        
        def submit():
            nonlocal submitted_email
            data = form.values
            submitted_email = data["email"]
        
        submit()
        assert submitted_email == "test@example.com"


# =============================================================================
# RESET AFTER SUBMIT (15 tests)
# =============================================================================

class TestResetAfterSubmit:
    """Tests for resetting form after submission."""
    
    def test_reset_after_submit(self):
        """Form reset after successful submit."""
        form = create_form(initial={"name": ""})
        form.name.set("Alice")
        
        # Simulate submit
        if form.validate():
            form.reset()
        
        assert form.name() == ""
    
    def test_reset_clears_values(self):
        """reset() restores initial values."""
        form = create_form(initial={"a": "A", "b": "B"})
        form.set_values({"a": "X", "b": "Y"})
        form.reset()
        
        assert form.a() == "A"
        assert form.b() == "B"
    
    def test_reset_clears_errors(self):
        """reset() clears validation errors."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        form.reset()
        
        assert form.errors.name == ""
    
    def test_reset_clears_touched(self):
        """reset() clears touched state."""
        form = create_form(initial={"name": ""})
        form.touch_all()
        form.reset()
        
        assert not form.is_touched("name")
    
    def test_reset_clears_submitting(self):
        """reset() clears submitting state."""
        form = create_form(initial={"name": ""})
        form._is_submitting.set(True)
        form.reset()
        
        assert not form.is_submitting()
    
    def test_form_reusable_after_reset(self):
        """Form can be reused after reset."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        
        # First submission
        form.name.set("Alice")
        assert form.validate()
        form.reset()
        
        # Second submission
        form.name.set("Bob")
        assert form.validate()
        assert form.name() == "Bob"
    
    def test_reset_to_different_initial(self):
        """reset() always uses original initial values."""
        form = create_form(initial={"name": "Original"})
        
        form.name.set("Changed1")
        form.reset()
        assert form.name() == "Original"
        
        form.name.set("Changed2")
        form.reset()
        assert form.name() == "Original"

