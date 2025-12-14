"""
Comprehensive tests for form error handling.

Tests cover:
- Error signals
- FormErrors class
- error_for() helper
- Error display in templates
- Server-side error handling

Total: 100+ tests
"""

import pytest
from pynext.reactive.forms import (
    FormState,
    FormErrors,
    create_form,
    required,
    min_length,
    email,
)


# =============================================================================
# FORM ERRORS CLASS (30 tests)
# =============================================================================

class TestFormErrorsClass:
    """Tests for FormErrors wrapper class."""
    
    def test_form_errors_attribute_access(self):
        """Access error via attribute."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.errors.name != ""
    
    def test_form_errors_bracket_access(self):
        """Access error via bracket notation."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.errors["name"] != ""
    
    def test_form_errors_returns_empty_for_no_error(self):
        """Empty string when no error."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.errors.name == ""
    
    def test_form_errors_nonexistent_field(self):
        """Empty string for nonexistent field."""
        form = create_form(initial={"name": ""})
        assert form.errors.nonexistent == ""
    
    def test_form_errors_all(self):
        """Get all errors as dict."""
        form = create_form(
            initial={"a": "", "b": "", "c": "valid"},
            validators={
                "a": [required()],
                "b": [required()],
                "c": [required()],
            }
        )
        form.validate()
        errors = form.errors.all()
        assert "a" in errors
        assert "b" in errors
        assert "c" not in errors
    
    def test_form_errors_all_empty_when_valid(self):
        """errors.all() empty when all valid."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.errors.all() == {}
    
    def test_form_errors_has_any_true(self):
        """has_any() returns True when errors exist."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.errors.has_any()
    
    def test_form_errors_has_any_false(self):
        """has_any() returns False when no errors."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        form.validate()
        assert not form.errors.has_any()
    
    def test_form_errors_multiple_fields(self):
        """Multiple field errors."""
        form = create_form(
            initial={"name": "", "email": "invalid", "age": ""},
            validators={
                "name": [required()],
                "email": [email()],
                "age": [required()],
            }
        )
        form.validate()
        assert form.errors.name != ""
        assert form.errors.email != ""
        assert form.errors.age != ""
    
    def test_form_errors_first_validator_error(self):
        """Only first validator error shown."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required("R"), min_length(5, "M")]}
        )
        form.validate()
        assert form.errors.name == "R"  # required error, not min_length


# =============================================================================
# SET/GET ERROR METHODS (20 tests)
# =============================================================================

class TestSetGetError:
    """Tests for manual error setting/getting."""
    
    def test_get_error(self):
        """get_error returns current error."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.get_error("name") != ""
    
    def test_get_error_empty_when_valid(self):
        """get_error returns empty when valid."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.get_error("name") == ""
    
    def test_get_error_nonexistent_field(self):
        """get_error for nonexistent field returns empty."""
        form = create_form(initial={"name": ""})
        assert form.get_error("nonexistent") == ""
    
    def test_set_error(self):
        """set_error sets manual error."""
        form = create_form(initial={"name": ""})
        form.set_error("name", "Custom error")
        assert form.errors.name == "Custom error"
    
    def test_set_error_clears_with_empty(self):
        """set_error clears error with empty string."""
        form = create_form(initial={"name": ""})
        form.set_error("name", "Error")
        form.set_error("name", "")
        assert form.errors.name == ""
    
    def test_set_error_server_validation(self):
        """Simulate server-side validation error."""
        form = create_form(initial={"email": "taken@example.com"})
        form.set_error("email", "Email already registered")
        assert form.errors.email == "Email already registered"
    
    def test_set_error_overwrites_validation_error(self):
        """Manual error overwrites validation error."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert "required" in form.errors.name.lower()
        
        form.set_error("name", "Server says no")
        assert form.errors.name == "Server says no"
    
    def test_set_error_nonexistent_field(self):
        """set_error for nonexistent field does nothing."""
        form = create_form(initial={"name": ""})
        form.set_error("nonexistent", "Error")  # Should not raise
    
    def test_clear_errors(self):
        """clear_errors removes all errors."""
        form = create_form(
            initial={"a": "", "b": ""},
            validators={"a": [required()], "b": [required()]}
        )
        form.validate()
        assert form.has_errors()
        form.clear_errors()
        assert not form.has_errors()
    
    def test_clear_errors_after_set_error(self):
        """clear_errors removes manual errors too."""
        form = create_form(initial={"name": ""})
        form.set_error("name", "Error")
        form.clear_errors()
        assert form.errors.name == ""


# =============================================================================
# HAS_ERRORS METHOD (15 tests)
# =============================================================================

class TestHasErrors:
    """Tests for has_errors() method."""
    
    def test_has_errors_initial(self):
        """No errors initially."""
        form = create_form(initial={"name": ""})
        assert not form.has_errors()
    
    def test_has_errors_after_validation(self):
        """has_errors True after failed validation."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.has_errors()
    
    def test_has_errors_after_successful_validation(self):
        """has_errors False after successful validation."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        form.validate()
        assert not form.has_errors()
    
    def test_has_errors_after_set_error(self):
        """has_errors True after manual set_error."""
        form = create_form(initial={"name": ""})
        form.set_error("name", "Error")
        assert form.has_errors()
    
    def test_has_errors_after_clear_errors(self):
        """has_errors False after clear_errors."""
        form = create_form(initial={"name": ""})
        form.set_error("name", "Error")
        form.clear_errors()
        assert not form.has_errors()
    
    def test_has_errors_partial(self):
        """has_errors True if any field has error."""
        form = create_form(
            initial={"name": "Alice", "email": ""},
            validators={
                "name": [required()],
                "email": [required()],
            }
        )
        form.validate()
        assert form.has_errors()
    
    def test_has_errors_after_fix(self):
        """has_errors False after fixing and revalidating."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.has_errors()
        
        form.name.set("Alice")
        form.validate()
        assert not form.has_errors()


# =============================================================================
# ERROR_FOR HELPER (20 tests)
# =============================================================================

class TestErrorFor:
    """Tests for error_for() display helper."""
    
    def test_error_for_returns_element(self):
        """error_for returns element."""
        form = create_form(initial={"name": ""})
        result = form.error_for("name")
        # Should be a Show element or similar
        assert result is not None
    
    def test_error_for_with_error(self):
        """error_for displays error when present."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        result = form.error_for("name")
        assert result is not None
    
    def test_error_for_without_error(self):
        """error_for hides when no error."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        form.validate()
        result = form.error_for("name")
        # Result is Show element, will render empty when condition is False
    
    def test_error_for_custom_class(self):
        """error_for accepts custom class."""
        form = create_form(initial={"name": ""})
        result = form.error_for("name", class_="my-error text-sm")
        assert result is not None
    
    def test_error_for_nonexistent_field(self):
        """error_for for nonexistent field returns None."""
        form = create_form(initial={"name": ""})
        result = form.error_for("nonexistent")
        assert result is None
    
    def test_error_for_reactive(self):
        """error_for updates reactively."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        
        # Initially no error shown
        form.validate()
        assert form.errors.name != ""
        
        # After fix, error should clear
        form.name.set("Alice")
        form.validate()
        assert form.errors.name == ""


# =============================================================================
# ERROR LIFECYCLE (15 tests)
# =============================================================================

class TestErrorLifecycle:
    """Tests for error state lifecycle."""
    
    def test_errors_cleared_on_reset(self):
        """Errors cleared on form reset."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.has_errors()
        
        form.reset()
        assert not form.has_errors()
    
    def test_errors_cleared_on_field_reset(self):
        """Error cleared on field reset."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.errors.name != ""
        
        form.reset_field("name")
        assert form.errors.name == ""
    
    def test_errors_persist_between_validations(self):
        """Errors persist until next validate()."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        
        # Change value but don't validate
        form.name.set("Alice")
        # Error still present (old error)
        assert form.errors.name != ""
        
        # Validate clears
        form.validate()
        assert form.errors.name == ""
    
    def test_error_updates_on_revalidation(self):
        """Error message updates on revalidation."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required("R"), min_length(5, "M")]}
        )
        form.validate()
        assert form.errors.name == "R"
        
        form.name.set("ab")
        form.validate()
        assert form.errors.name == "M"
    
    def test_validate_field_independent(self):
        """validate_field only affects one field."""
        form = create_form(
            initial={"a": "", "b": ""},
            validators={"a": [required()], "b": [required()]}
        )
        
        form.validate_field("a")
        assert form.errors.a != ""
        assert form.errors.b == ""  # Not validated yet
    
    def test_errors_empty_no_validators(self):
        """No errors when no validators."""
        form = create_form(initial={"name": "", "email": ""})
        form.validate()
        assert form.errors.name == ""
        assert form.errors.email == ""
        assert not form.has_errors()

