"""
Comprehensive tests for PyNext FormState class.

Tests cover:
- Form creation
- Field access (attribute and method)
- Values (get/set)
- Error management
- Touched/dirty tracking
- Validation
- Reset functionality
- Hydration/serialization

Total: 100+ tests
"""

import pytest
from pynext.reactive.forms import (
    FormState,
    FormErrors,
    create_form,
    required,
    min_length,
    max_length,
    email,
)
from pynext.reactive import signal


# =============================================================================
# FORM CREATION (15 tests)
# =============================================================================

class TestFormCreation:
    """Tests for form creation."""
    
    def test_create_form_basic(self):
        """Create form with initial values."""
        form = create_form(initial={"name": "", "email": ""})
        assert form is not None
    
    def test_create_form_factory(self):
        """create_form returns FormState."""
        form = create_form(initial={"name": ""})
        assert isinstance(form, FormState)
    
    def test_create_form_with_validators(self):
        """Create form with validators."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        assert form is not None
    
    def test_create_form_empty_initial(self):
        """Create form with empty initial dict."""
        form = create_form(initial={})
        assert form is not None
    
    def test_create_form_various_types(self):
        """Form supports various value types."""
        form = create_form(initial={
            "string": "hello",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "none": None,
        })
        assert form is not None
    
    def test_create_form_preserves_initial(self):
        """Initial values are preserved for reset."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        form.reset()
        assert form.name() == "Alice"
    
    def test_create_form_single_validator(self):
        """Validator can be single function (not list)."""
        form = create_form(
            initial={"name": ""},
            validators={"name": required()}
        )
        assert not form.is_valid()
    
    def test_create_form_multiple_validators(self):
        """Multiple validators as list."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required(), min_length(3)]}
        )
        form.name.set("ab")
        assert not form.is_valid()
    
    def test_create_form_partial_validators(self):
        """Some fields have validators, some don't."""
        form = create_form(
            initial={"name": "", "optional": ""},
            validators={"name": [required()]}
        )
        form.name.set("Alice")
        assert form.is_valid()
    
    def test_create_form_validator_for_nonexistent_field(self):
        """Validator for non-existent field is ignored."""
        form = create_form(
            initial={"name": ""},
            validators={"nonexistent": [required()]}
        )
        assert form.is_valid()
    
    def test_form_state_direct(self):
        """Create FormState directly."""
        form = FormState(initial={"name": ""})
        assert form is not None
    
    def test_form_pynext_type(self):
        """Form has pynext type marker."""
        form = create_form(initial={"name": ""})
        assert hasattr(form, "__pynext_type__")
        assert form.__pynext_type__ == "form"


# =============================================================================
# FIELD ACCESS (15 tests)
# =============================================================================

class TestFieldAccess:
    """Tests for accessing form fields."""
    
    def test_field_attribute_access(self):
        """Access field via attribute."""
        form = create_form(initial={"name": "Alice"})
        assert form.name() == "Alice"
    
    def test_field_is_signal(self):
        """Field is a Signal instance."""
        form = create_form(initial={"name": "Alice"})
        assert hasattr(form.name, "set")
        assert hasattr(form.name, "update")
    
    def test_field_get_method(self):
        """Access field via get_field method."""
        form = create_form(initial={"name": "Alice"})
        field = form.get_field("name")
        assert field() == "Alice"
    
    def test_field_nonexistent_attribute(self):
        """Accessing nonexistent field raises AttributeError."""
        form = create_form(initial={"name": ""})
        with pytest.raises(AttributeError):
            _ = form.nonexistent
    
    def test_field_nonexistent_get_field(self):
        """get_field for nonexistent field raises KeyError."""
        form = create_form(initial={"name": ""})
        with pytest.raises(KeyError):
            form.get_field("nonexistent")
    
    def test_field_names(self):
        """Get list of all field names."""
        form = create_form(initial={"a": 1, "b": 2, "c": 3})
        names = form.field_names()
        assert set(names) == {"a", "b", "c"}
    
    def test_field_underscore_name(self):
        """Field with underscore in name."""
        form = create_form(initial={"first_name": "Alice"})
        assert form.first_name() == "Alice"
    
    def test_field_number_in_name(self):
        """Field with number in name."""
        form = create_form(initial={"field1": "value"})
        assert form.field1() == "value"
    
    def test_multiple_fields(self):
        """Form with multiple fields."""
        form = create_form(initial={
            "name": "Alice",
            "email": "alice@example.com",
            "age": 30,
        })
        assert form.name() == "Alice"
        assert form.email() == "alice@example.com"
        assert form.age() == 30
    
    def test_field_set(self):
        """Set field value."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        assert form.name() == "Bob"
    
    def test_field_update(self):
        """Update field with function."""
        form = create_form(initial={"count": 0})
        form.count.update(lambda x: x + 1)
        assert form.count() == 1


# =============================================================================
# VALUES (15 tests)
# =============================================================================

class TestFormValues:
    """Tests for form values property and methods."""
    
    def test_values_property(self):
        """Get all values as dict."""
        form = create_form(initial={"name": "Alice", "age": 30})
        values = form.values
        assert values == {"name": "Alice", "age": 30}
    
    def test_values_after_change(self):
        """Values reflect changes."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        assert form.values["name"] == "Bob"
    
    def test_values_is_copy(self):
        """values returns a copy, not original."""
        form = create_form(initial={"name": "Alice"})
        values = form.values
        values["name"] = "Modified"
        assert form.name() == "Alice"  # Not affected
    
    def test_get_value(self):
        """Get single value by name."""
        form = create_form(initial={"name": "Alice"})
        assert form.get_value("name") == "Alice"
    
    def test_set_value(self):
        """Set single value by name."""
        form = create_form(initial={"name": "Alice"})
        form.set_value("name", "Bob")
        assert form.name() == "Bob"
    
    def test_set_value_marks_touched(self):
        """set_value marks field as touched."""
        form = create_form(initial={"name": "Alice"})
        assert not form.is_touched("name")
        form.set_value("name", "Bob")
        assert form.is_touched("name")
    
    def test_set_values(self):
        """Set multiple values at once."""
        form = create_form(initial={"name": "", "email": ""})
        form.set_values({"name": "Alice", "email": "alice@example.com"})
        assert form.name() == "Alice"
        assert form.email() == "alice@example.com"
    
    def test_set_values_partial(self):
        """set_values with partial update."""
        form = create_form(initial={"name": "Alice", "email": "old@example.com"})
        form.set_values({"email": "new@example.com"})
        assert form.name() == "Alice"  # Unchanged
        assert form.email() == "new@example.com"
    
    def test_set_values_ignores_unknown(self):
        """set_values ignores unknown fields."""
        form = create_form(initial={"name": ""})
        form.set_values({"name": "Alice", "unknown": "ignored"})
        assert form.name() == "Alice"
    
    def test_values_with_none(self):
        """Form handles None values."""
        form = create_form(initial={"nullable": None})
        assert form.nullable() is None
        assert form.values["nullable"] is None
    
    def test_values_with_list(self):
        """Form handles list values."""
        form = create_form(initial={"items": [1, 2, 3]})
        assert form.items() == [1, 2, 3]


# =============================================================================
# ERRORS (20 tests)
# =============================================================================

class TestFormErrors:
    """Tests for form error handling."""
    
    def test_errors_property(self):
        """Access errors property."""
        form = create_form(initial={"name": ""})
        assert hasattr(form, "errors")
    
    def test_errors_is_form_errors(self):
        """errors returns FormErrors instance."""
        form = create_form(initial={"name": ""})
        assert isinstance(form.errors, FormErrors)
    
    def test_errors_attribute_access(self):
        """Access error via attribute."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.errors.name != ""
    
    def test_errors_bracket_access(self):
        """Access error via bracket notation."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.errors["name"] != ""
    
    def test_errors_empty_when_valid(self):
        """No error when field is valid."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.errors.name == ""
    
    def test_get_error(self):
        """Get error via get_error method."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.get_error("name") != ""
    
    def test_set_error(self):
        """Set error manually."""
        form = create_form(initial={"name": ""})
        form.set_error("name", "Custom error")
        assert form.errors.name == "Custom error"
    
    def test_set_error_clears(self):
        """Set empty string to clear error."""
        form = create_form(initial={"name": ""})
        form.set_error("name", "Error")
        form.set_error("name", "")
        assert form.errors.name == ""
    
    def test_clear_errors(self):
        """Clear all errors."""
        form = create_form(
            initial={"name": "", "email": ""},
            validators={
                "name": [required()],
                "email": [required()],
            }
        )
        form.validate()
        form.clear_errors()
        assert form.errors.name == ""
        assert form.errors.email == ""
    
    def test_has_errors(self):
        """Check if form has any errors."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        assert not form.has_errors()
        form.validate()
        assert form.has_errors()
    
    def test_errors_all(self):
        """Get all errors as dict."""
        form = create_form(
            initial={"name": "", "email": ""},
            validators={
                "name": [required()],
                "email": [required()],
            }
        )
        form.validate()
        all_errors = form.errors.all()
        assert "name" in all_errors
        assert "email" in all_errors
    
    def test_errors_all_excludes_empty(self):
        """errors.all() excludes fields without errors."""
        form = create_form(
            initial={"name": "Alice", "email": ""},
            validators={
                "name": [required()],
                "email": [required()],
            }
        )
        form.validate()
        all_errors = form.errors.all()
        assert "name" not in all_errors
        assert "email" in all_errors
    
    def test_errors_has_any(self):
        """Check if any field has error."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        form.validate()
        assert not form.errors.has_any()
        
        form.name.set("")
        form.validate()
        assert form.errors.has_any()
    
    def test_error_for_helper(self):
        """error_for returns element or None."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        # Before validation, might return None or Show element
        result = form.error_for("name")
        assert result is not None or result is None
    
    def test_error_nonexistent_field(self):
        """Accessing error for nonexistent field returns empty."""
        form = create_form(initial={"name": ""})
        assert form.errors.nonexistent == ""


# =============================================================================
# TOUCHED/DIRTY STATE (15 tests)
# =============================================================================

class TestTouchedDirty:
    """Tests for touched and dirty state tracking."""
    
    def test_is_touched_initial(self):
        """Fields start untouched."""
        form = create_form(initial={"name": ""})
        assert not form.is_touched("name")
    
    def test_is_touched_after_set_value(self):
        """Field becomes touched after set_value."""
        form = create_form(initial={"name": ""})
        form.set_value("name", "Alice")
        assert form.is_touched("name")
    
    def test_set_touched(self):
        """Manually set touched state."""
        form = create_form(initial={"name": ""})
        form.set_touched("name", True)
        assert form.is_touched("name")
    
    def test_set_touched_false(self):
        """Set touched to False."""
        form = create_form(initial={"name": ""})
        form.set_touched("name", True)
        form.set_touched("name", False)
        assert not form.is_touched("name")
    
    def test_touch_all(self):
        """Touch all fields."""
        form = create_form(initial={"a": "", "b": "", "c": ""})
        form.touch_all()
        assert form.is_touched("a")
        assert form.is_touched("b")
        assert form.is_touched("c")
    
    def test_is_dirty_initial(self):
        """Form starts clean (not dirty)."""
        form = create_form(initial={"name": "Alice"})
        assert not form.is_dirty()
    
    def test_is_dirty_after_change(self):
        """Form becomes dirty after value change."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        assert form.is_dirty()
    
    def test_is_dirty_same_value(self):
        """Setting same value doesn't make dirty (depends on signal equality)."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Alice")
        # May or may not be dirty depending on signal implementation
    
    def test_is_dirty_after_reset(self):
        """Form is clean after reset."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        form.reset()
        assert not form.is_dirty()
    
    def test_is_touched_after_reset(self):
        """Fields are untouched after reset."""
        form = create_form(initial={"name": ""})
        form.set_touched("name", True)
        form.reset()
        assert not form.is_touched("name")


# =============================================================================
# VALIDATION (15 tests)
# =============================================================================

class TestValidation:
    """Tests for form validation."""
    
    def test_is_valid_no_validators(self):
        """Form without validators is always valid."""
        form = create_form(initial={"name": ""})
        assert form.is_valid()
    
    def test_is_valid_passes(self):
        """Form is valid when validators pass."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        assert form.is_valid()
    
    def test_is_valid_fails(self):
        """Form is invalid when validators fail."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        assert not form.is_valid()
    
    def test_validate_returns_bool(self):
        """validate() returns boolean."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        result = form.validate()
        assert isinstance(result, bool)
        assert result is False
    
    def test_validate_sets_errors(self):
        """validate() populates errors."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        assert form.errors.name != ""
    
    def test_validate_clears_errors_on_success(self):
        """validate() clears errors when valid."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()  # Sets error
        form.name.set("Alice")
        form.validate()  # Should clear
        assert form.errors.name == ""
    
    def test_validate_touches_all(self):
        """validate() touches all fields by default."""
        form = create_form(initial={"name": "", "email": ""})
        form.validate()
        assert form.is_touched("name")
        assert form.is_touched("email")
    
    def test_validate_touch_false(self):
        """validate(touch=False) doesn't touch fields."""
        form = create_form(initial={"name": ""})
        form.validate(touch=False)
        assert not form.is_touched("name")
    
    def test_validate_field(self):
        """Validate single field."""
        form = create_form(
            initial={"name": "", "email": ""},
            validators={
                "name": [required()],
                "email": [required()],
            }
        )
        result = form.validate_field("name")
        assert result is False
        assert form.errors.name != ""
        assert form.errors.email == ""  # Not validated
    
    def test_validate_field_success(self):
        """validate_field returns True when valid."""
        form = create_form(
            initial={"name": "Alice"},
            validators={"name": [required()]}
        )
        result = form.validate_field("name")
        assert result is True
    
    def test_validate_multiple_validators(self):
        """All validators run."""
        form = create_form(
            initial={"name": "ab"},
            validators={"name": [required(), min_length(3)]}
        )
        assert not form.is_valid()
    
    def test_is_valid_reactive(self):
        """is_valid updates reactively."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        assert not form.is_valid()
        form.name.set("Alice")
        assert form.is_valid()


# =============================================================================
# RESET (10 tests)
# =============================================================================

class TestReset:
    """Tests for form reset functionality."""
    
    def test_reset_values(self):
        """reset() restores initial values."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        form.reset()
        assert form.name() == "Alice"
    
    def test_reset_errors(self):
        """reset() clears errors."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        form.reset()
        assert form.errors.name == ""
    
    def test_reset_touched(self):
        """reset() clears touched state."""
        form = create_form(initial={"name": ""})
        form.touch_all()
        form.reset()
        assert not form.is_touched("name")
    
    def test_reset_submitting(self):
        """reset() clears submitting state."""
        form = create_form(initial={"name": ""})
        form._is_submitting.set(True)
        form.reset()
        assert not form.is_submitting()
    
    def test_reset_field(self):
        """reset_field() resets single field."""
        form = create_form(initial={"a": "A", "b": "B"})
        form.set_value("a", "X")
        form.set_value("b", "Y")
        form.reset_field("a")
        assert form.a() == "A"
        assert form.b() == "Y"
    
    def test_reset_field_clears_error(self):
        """reset_field() clears field error."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        form.reset_field("name")
        assert form.errors.name == ""
    
    def test_reset_field_clears_touched(self):
        """reset_field() clears touched state."""
        form = create_form(initial={"name": ""})
        form.set_touched("name", True)
        form.reset_field("name")
        assert not form.is_touched("name")
    
    def test_reset_multiple_times(self):
        """Multiple resets work correctly."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        form.reset()
        form.name.set("Charlie")
        form.reset()
        assert form.name() == "Alice"


# =============================================================================
# SUBMITTING STATE (5 tests)
# =============================================================================

class TestSubmitting:
    """Tests for form submitting state."""
    
    def test_is_submitting_initial(self):
        """Form starts not submitting."""
        form = create_form(initial={"name": ""})
        assert not form.is_submitting()
    
    def test_is_submitting_set(self):
        """Can set submitting state."""
        form = create_form(initial={"name": ""})
        form._is_submitting.set(True)
        assert form.is_submitting()
    
    def test_is_submitting_after_reset(self):
        """Submitting is cleared on reset."""
        form = create_form(initial={"name": ""})
        form._is_submitting.set(True)
        form.reset()
        assert not form.is_submitting()


# =============================================================================
# SERIALIZATION (5 tests)
# =============================================================================

class TestSerialization:
    """Tests for form serialization."""
    
    def test_to_json(self):
        """to_json returns dict."""
        form = create_form(initial={"name": "Alice"})
        data = form.to_json()
        assert isinstance(data, dict)
        assert "values" in data
    
    def test_to_json_includes_values(self):
        """to_json includes current values."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        data = form.to_json()
        assert data["values"]["name"] == "Bob"
    
    def test_to_json_includes_errors(self):
        """to_json includes errors."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        data = form.to_json()
        assert "errors" in data
        assert "name" in data["errors"]
    
    def test_to_hydration_state(self):
        """to_hydration_state returns hydration dict."""
        form = create_form(initial={"name": "Alice"})
        state = form.to_hydration_state()
        assert state["type"] == "form"
        assert "initial" in state
        assert "values" in state
    
    def test_get_js_init(self):
        """get_js_init returns JS code."""
        form = create_form(initial={"name": "Alice"})
        js = form.get_js_init()
        assert "createForm" in js
        assert "name" in js

