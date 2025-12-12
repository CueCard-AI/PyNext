"""
Comprehensive tests for P0/P1 form hydration fixes.

These tests verify:
1. Validator serialization for hydration
2. Form binding marker generation in html.py
3. Context form registration
4. Hydration data structure correctness

Tests target the specific issues identified:
- P0: Validators not serialized
- P0: bind= doesn't create hydration markers
- P1: Forms missing from hydration data
"""

import json
import pytest
from typing import Any, Dict

from pynext.reactive.forms import create_form, FormState
from pynext.reactive.validators import (
    required, min_length, max_length, email, pattern,
    min_value, max_value, one_of, url, integer, number, length,
    _mark_validator,
)
from pynext.core.context import (
    RenderContext, set_context, reset_context, get_context,
    FormBinding,
)
from pynext.core.html import Element, input_, div


# =============================================================================
# SECTION 1: Validator Marker Tests
# =============================================================================

class TestValidatorMarkers:
    """Test that validators have proper serialization markers."""
    
    def test_required_has_marker(self):
        """required() should have _validator_type marker."""
        v = required()
        assert hasattr(v, "_validator_type")
        assert v._validator_type == "required"
    
    def test_required_args_empty(self):
        """required() args should be empty by default."""
        v = required()
        assert v._validator_args == []
    
    def test_required_custom_message_in_marker(self):
        """required() with custom message should be stored."""
        v = required("Field cannot be empty")
        assert v._validator_message == "Field cannot be empty"
    
    def test_min_length_has_marker(self):
        """min_length() should have proper markers."""
        v = min_length(5)
        assert v._validator_type == "min_length"
        assert v._validator_args == [5]
    
    def test_min_length_custom_message(self):
        """min_length() with custom message."""
        v = min_length(3, "Too short!")
        assert v._validator_type == "min_length"
        assert v._validator_args == [3]
        assert v._validator_message == "Too short!"
    
    def test_max_length_has_marker(self):
        """max_length() should have proper markers."""
        v = max_length(100)
        assert v._validator_type == "max_length"
        assert v._validator_args == [100]
    
    def test_email_has_marker(self):
        """email() should have proper markers."""
        v = email()
        assert v._validator_type == "email"
        assert v._validator_args == []
    
    def test_pattern_has_marker(self):
        """pattern() should serialize regex string."""
        v = pattern(r"^\d{5}$")
        assert v._validator_type == "pattern"
        assert v._validator_args == [r"^\d{5}$"]
    
    def test_min_value_has_marker(self):
        """min_value() should have proper markers."""
        v = min_value(0)
        assert v._validator_type == "min_value"
        assert v._validator_args == [0]
    
    def test_max_value_has_marker(self):
        """max_value() should have proper markers."""
        v = max_value(100)
        assert v._validator_type == "max_value"
        assert v._validator_args == [100]
    
    def test_one_of_has_marker(self):
        """one_of() should serialize options list."""
        v = one_of(["a", "b", "c"])
        assert v._validator_type == "one_of"
        assert v._validator_args == [["a", "b", "c"]]
    
    def test_url_has_marker(self):
        """url() should have proper markers."""
        v = url()
        assert v._validator_type == "url"
    
    def test_integer_has_marker(self):
        """integer() should have proper markers."""
        v = integer()
        assert v._validator_type == "integer"
    
    def test_number_has_marker(self):
        """number() should have proper markers."""
        v = number()
        assert v._validator_type == "number"
    
    def test_length_has_marker(self):
        """length() should have proper markers."""
        v = length(10)
        assert v._validator_type == "length"
        assert v._validator_args == [10]


# =============================================================================
# SECTION 2: FormState Validator Serialization Tests
# =============================================================================

class TestFormValidatorSerialization:
    """Test FormState._serialize_validators() method."""
    
    def test_serialize_empty_validators(self):
        """Empty validators should serialize to empty dict."""
        form = create_form({"name": ""})
        result = form._serialize_validators()
        assert result == {}
    
    def test_serialize_single_validator(self):
        """Single validator should serialize correctly."""
        form = create_form(
            {"name": ""},
            validators={"name": [required()]}
        )
        result = form._serialize_validators()
        assert "name" in result
        assert len(result["name"]) == 1
        assert result["name"][0]["type"] == "required"
    
    def test_serialize_multiple_validators(self):
        """Multiple validators should all serialize."""
        form = create_form(
            {"email": ""},
            validators={"email": [required(), email()]}
        )
        result = form._serialize_validators()
        assert len(result["email"]) == 2
        types = [v["type"] for v in result["email"]]
        assert "required" in types
        assert "email" in types
    
    def test_serialize_validators_with_args(self):
        """Validators with args should include them."""
        form = create_form(
            {"password": ""},
            validators={"password": [min_length(8), max_length(128)]}
        )
        result = form._serialize_validators()
        assert result["password"][0]["args"] == [8]
        assert result["password"][1]["args"] == [128]
    
    def test_serialize_validators_with_messages(self):
        """Custom messages should be included."""
        form = create_form(
            {"name": ""},
            validators={"name": [required("Name is required")]}
        )
        result = form._serialize_validators()
        assert result["name"][0]["message"] == "Name is required"
    
    def test_serialize_pattern_validator(self):
        """Pattern regex should be stored as string."""
        form = create_form(
            {"zip": ""},
            validators={"zip": [pattern(r"^\d{5}$", "Invalid ZIP")]}
        )
        result = form._serialize_validators()
        assert result["zip"][0]["type"] == "pattern"
        assert result["zip"][0]["args"] == [r"^\d{5}$"]
    
    def test_serialize_one_of_validator(self):
        """one_of options should be serialized as list."""
        form = create_form(
            {"status": ""},
            validators={"status": [one_of(["draft", "published"])]}
        )
        result = form._serialize_validators()
        assert result["status"][0]["args"] == [["draft", "published"]]


class TestFormHydrationState:
    """Test FormState.to_hydration_state() includes validators."""
    
    def test_hydration_state_has_validators(self):
        """to_hydration_state() should include validators."""
        form = create_form(
            {"name": ""},
            validators={"name": [required()]}
        )
        result = form.to_hydration_state()
        assert "validators" in result
    
    def test_hydration_state_validators_format(self):
        """Validators should be in correct format."""
        form = create_form(
            {"name": ""},
            validators={"name": [required(), min_length(2)]}
        )
        result = form.to_hydration_state()
        assert len(result["validators"]["name"]) == 2
    
    def test_hydration_state_is_json_serializable(self):
        """to_hydration_state() result should be JSON-serializable."""
        form = create_form(
            {"name": "", "age": 0},
            validators={
                "name": [required(), min_length(2)],
                "age": [min_value(0), max_value(150)],
            }
        )
        result = form.to_hydration_state()
        json_str = json.dumps(result)
        assert json_str
        # Roundtrip should work
        parsed = json.loads(json_str)
        assert parsed["validators"]["name"][0]["type"] == "required"
    
    def test_hydration_state_has_all_fields(self):
        """to_hydration_state() should have type, id, initial, values, validators."""
        form = create_form({"x": 1}, validators={"x": [required()]})
        result = form.to_hydration_state()
        assert result["type"] == "form"
        assert "id" in result
        assert "initial" in result
        assert "values" in result
        assert "validators" in result


class TestFormGetJsInit:
    """Test FormState.get_js_init() includes validators."""
    
    def test_get_js_init_includes_validators(self):
        """get_js_init() should include validator calls."""
        form = create_form(
            {"name": ""},
            validators={"name": [required()]}
        )
        js = form.get_js_init()
        assert "createForm(" in js
        assert "required" in js
    
    def test_get_js_init_minlength_uses_camelcase(self):
        """min_length should become minLength in JS."""
        form = create_form(
            {"name": ""},
            validators={"name": [min_length(5)]}
        )
        js = form.get_js_init()
        assert "minLength" in js
    
    def test_get_js_init_with_args(self):
        """Validator args should be in JS output."""
        form = create_form(
            {"count": 0},
            validators={"count": [min_value(0), max_value(100)]}
        )
        js = form.get_js_init()
        assert "minValue(0" in js
        assert "maxValue(100" in js


# =============================================================================
# SECTION 3: Context Form Registration Tests
# =============================================================================

class TestContextFormRegistration:
    """Test RenderContext form registration."""
    
    def test_context_has_forms_dict(self):
        """RenderContext should have forms dict."""
        ctx = RenderContext()
        assert hasattr(ctx, "forms")
        assert isinstance(ctx.forms, dict)
    
    def test_context_has_form_bindings(self):
        """RenderContext should have form_bindings dict."""
        ctx = RenderContext()
        assert hasattr(ctx, "form_bindings")
        assert isinstance(ctx.form_bindings, dict)
    
    def test_register_form(self):
        """register_form() should add form to context."""
        ctx = RenderContext()
        form = create_form({"name": ""})
        form_id = ctx.register_form(form)
        assert form_id in ctx.forms
    
    def test_register_form_includes_hydration_state(self):
        """Registered form should use to_hydration_state()."""
        ctx = RenderContext()
        form = create_form(
            {"name": ""},
            validators={"name": [required()]}
        )
        form_id = ctx.register_form(form)
        assert "validators" in ctx.forms[form_id]
    
    def test_register_form_binding(self):
        """register_form_binding() should create FormBinding."""
        ctx = RenderContext()
        ctx.register_form_binding("input_1", "form_123", "name", "value")
        assert "input_1" in ctx.form_bindings
        binding = ctx.form_bindings["input_1"]
        assert binding.form_id == "form_123"
        assert binding.field_name == "name"
        assert binding.bind_type == "value"
    
    def test_register_form_binding_checkbox(self):
        """Checkbox binding should use 'checked' type."""
        ctx = RenderContext()
        ctx.register_form_binding("cb_1", "form_123", "agree", "checked")
        binding = ctx.form_bindings["cb_1"]
        assert binding.bind_type == "checked"


class TestContextHydrationData:
    """Test get_hydration_data() includes forms."""
    
    def test_hydration_data_has_forms(self):
        """get_hydration_data() should include forms."""
        ctx = RenderContext()
        data = ctx.get_hydration_data()
        assert "forms" in data
    
    def test_hydration_data_has_form_bindings(self):
        """get_hydration_data() should include formBindings."""
        ctx = RenderContext()
        data = ctx.get_hydration_data()
        assert "formBindings" in data
    
    def test_hydration_data_form_bindings_format(self):
        """formBindings should have correct format."""
        ctx = RenderContext()
        ctx.register_form_binding("el_1", "form_1", "email", "value")
        data = ctx.get_hydration_data()
        
        assert "el_1" in data["formBindings"]
        binding = data["formBindings"]["el_1"]
        assert binding["elementId"] == "el_1"
        assert binding["formId"] == "form_1"
        assert binding["fieldName"] == "email"
        assert binding["bindType"] == "value"
    
    def test_hydration_data_is_json_serializable(self):
        """Full hydration data should be JSON-serializable."""
        ctx = RenderContext()
        form = create_form({"name": ""}, validators={"name": [required()]})
        ctx.register_form(form)
        ctx.register_form_binding("el_1", str(id(form)), "name", "value")
        
        data = ctx.get_hydration_data()
        json_str = json.dumps(data)
        assert json_str


# =============================================================================
# SECTION 4: HTML bind= Attribute Tests
# =============================================================================

class TestBindAttributeMarkers:
    """Test that bind= creates proper hydration markers."""
    
    def setup_method(self):
        """Set up render context for each test."""
        self.ctx = RenderContext()
        self.token = set_context(self.ctx)
    
    def teardown_method(self):
        """Reset render context."""
        reset_context(self.token)
    
    def test_bind_creates_internal_marker(self):
        """bind= should create _pynext_bind marker."""
        from pynext.reactive import signal
        sig = signal("")
        el = input_(bind=sig)
        assert "_pynext_bind" in el.attrs
    
    def test_bind_sets_value_attr(self):
        """bind= should also set value attr."""
        from pynext.reactive import signal
        sig = signal("hello")
        el = input_(bind=sig)
        assert "value" in el.attrs
    
    def test_bind_sets_oninput(self):
        """bind= should create oninput handler."""
        from pynext.reactive import signal
        sig = signal("")
        el = input_(bind=sig)
        assert "oninput" in el.attrs
        assert callable(el.attrs["oninput"])
    
    def test_bind_checkbox_sets_type(self):
        """bind= on checkbox should set bind_type to 'checked'."""
        from pynext.reactive import signal
        sig = signal(False)
        el = input_(type="checkbox", bind=sig)
        assert el.attrs.get("_pynext_bind_type") == "checked"
    
    def test_bind_regular_input_sets_value_type(self):
        """bind= on regular input should set bind_type to 'value'."""
        from pynext.reactive import signal
        sig = signal("")
        el = input_(bind=sig)
        assert el.attrs.get("_pynext_bind_type") == "value"


class TestBindAttributeRendering:
    """Test that bind= renders with data attributes."""
    
    def setup_method(self):
        """Set up render context for each test."""
        self.ctx = RenderContext()
        self.token = set_context(self.ctx)
    
    def teardown_method(self):
        """Reset render context."""
        reset_context(self.token)
    
    def test_render_includes_data_pynext_bind(self):
        """Rendered HTML should include data-pynext-bind attribute."""
        from pynext.reactive import signal
        sig = signal("test")
        el = input_(bind=sig)
        html = el.render()
        assert "data-pynext-bind=" in html
    
    def test_render_includes_data_pynext_bind_type(self):
        """Rendered HTML should include data-pynext-bind-type attribute."""
        from pynext.reactive import signal
        sig = signal("test")
        el = input_(bind=sig)
        html = el.render()
        assert "data-pynext-bind-type=" in html
    
    def test_render_has_element_id(self):
        """Rendered element with bind= should have id for hydration."""
        from pynext.reactive import signal
        sig = signal("")
        el = input_(bind=sig)
        html = el.render()
        assert 'id="' in html
    
    def test_context_registers_form_binding(self):
        """Rendering bind= should register form binding in context."""
        from pynext.reactive import signal
        sig = signal("")
        el = input_(bind=sig)
        el.render()
        # Should have at least one form binding
        assert len(self.ctx.form_bindings) >= 1


# =============================================================================
# SECTION 5: Integration Tests
# =============================================================================

class TestFullFormHydrationFlow:
    """Test complete form hydration flow from Python to hydration data."""
    
    def setup_method(self):
        """Set up render context for each test."""
        self.ctx = RenderContext()
        self.token = set_context(self.ctx)
    
    def teardown_method(self):
        """Reset render context."""
        reset_context(self.token)
    
    def test_form_with_bound_inputs_generates_complete_data(self):
        """Form with bound inputs should generate complete hydration data."""
        from pynext.reactive import signal
        
        # Create a form
        form = create_form(
            {"name": "", "email": ""},
            validators={
                "name": [required(), min_length(2)],
                "email": [required(), email()],
            }
        )
        
        # Register form
        form_id = self.ctx.register_form(form)
        
        # Create bound inputs (simulate component rendering)
        name_input = input_(bind=form.name)
        email_input = input_(type="email", bind=form.email)
        
        # Render
        name_input.render()
        email_input.render()
        
        # Get hydration data
        data = self.ctx.get_hydration_data()
        
        # Verify forms included
        assert form_id in data["forms"]
        form_data = data["forms"][form_id]
        
        # Verify validators included
        assert "validators" in form_data
        assert "name" in form_data["validators"]
        assert "email" in form_data["validators"]
        
        # Verify form bindings included
        assert len(data["formBindings"]) >= 2
    
    def test_hydration_data_roundtrip(self):
        """Hydration data should survive JSON roundtrip."""
        form = create_form(
            {"username": "", "password": ""},
            validators={
                "username": [required(), min_length(3), max_length(20)],
                "password": [required(), min_length(8), pattern(r".*\d.*", "Must contain a number")],
            }
        )
        
        form_id = self.ctx.register_form(form)
        data = self.ctx.get_hydration_data()
        
        # Serialize and deserialize
        json_str = json.dumps(data)
        restored = json.loads(json_str)
        
        # Verify structure preserved
        assert form_id in restored["forms"]
        form_data = restored["forms"][form_id]
        
        # Check validators
        assert len(form_data["validators"]["username"]) == 3
        assert form_data["validators"]["password"][2]["args"] == [r".*\d.*"]


class TestValidatorReconstruction:
    """Test that serialized validators can be understood by JS runtime."""
    
    def test_all_builtin_validators_serializable(self):
        """All built-in validators should serialize properly."""
        validators_to_test = [
            ("required", required()),
            ("min_length", min_length(5)),
            ("max_length", max_length(100)),
            ("email", email()),
            ("pattern", pattern(r"^\d+$")),
            ("min_value", min_value(0)),
            ("max_value", max_value(100)),
            ("one_of", one_of(["a", "b"])),
            ("url", url()),
            ("integer", integer()),
            ("number", number()),
            ("length", length(5)),
        ]
        
        for name, validator in validators_to_test:
            form = create_form({"field": ""}, validators={"field": [validator]})
            result = form._serialize_validators()
            
            assert "field" in result, f"{name} not serialized"
            assert len(result["field"]) == 1, f"{name} has wrong length"
            
            v_data = result["field"][0]
            assert "type" in v_data, f"{name} missing type"
            assert v_data["type"] != "unknown", f"{name} serialized as unknown"
    
    def test_complex_form_serialization(self):
        """Complex form with many fields should serialize correctly."""
        form = create_form(
            {
                "name": "",
                "email": "",
                "age": 0,
                "website": "",
                "status": "draft",
                "bio": "",
            },
            validators={
                "name": [required(), min_length(2), max_length(50)],
                "email": [required(), email()],
                "age": [min_value(0), max_value(150), integer()],
                "website": [url()],
                "status": [one_of(["draft", "published", "archived"])],
                "bio": [max_length(500)],
            }
        )
        
        result = form._serialize_validators()
        
        # Verify all fields present
        for field in ["name", "email", "age", "website", "status", "bio"]:
            assert field in result
        
        # Verify correct counts
        assert len(result["name"]) == 3
        assert len(result["email"]) == 2
        assert len(result["age"]) == 3
        assert len(result["website"]) == 1
        assert len(result["status"]) == 1
        assert len(result["bio"]) == 1


# =============================================================================
# SECTION 6: Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Test edge cases in form hydration."""
    
    def test_empty_form_serializes(self):
        """Form with no fields should serialize."""
        form = create_form({})
        result = form.to_hydration_state()
        assert result["type"] == "form"
        assert result["validators"] == {}
    
    def test_form_with_none_validators(self):
        """Form with None validators should work."""
        form = create_form({"name": ""}, validators=None)
        result = form._serialize_validators()
        assert result == {}
    
    def test_nested_list_values(self):
        """Form with list values should serialize."""
        form = create_form({"tags": ["a", "b"]})
        result = form.to_hydration_state()
        json.dumps(result)  # Should not raise
    
    def test_nested_dict_values(self):
        """Form with dict values should serialize."""
        form = create_form({"config": {"a": 1, "b": 2}})
        result = form.to_hydration_state()
        json.dumps(result)  # Should not raise
    
    def test_special_characters_in_messages(self):
        """Validators with special characters should serialize."""
        form = create_form(
            {"name": ""},
            validators={"name": [required("Can't be empty \"quoted\"")]}
        )
        result = form.to_hydration_state()
        json_str = json.dumps(result)
        assert "Can't be empty" in json_str
    
    def test_unicode_in_validators(self):
        """Unicode in validator messages should work."""
        form = create_form(
            {"name": ""},
            validators={"name": [required("名前は必須です")]}
        )
        result = form.to_hydration_state()
        json_str = json.dumps(result, ensure_ascii=False)
        assert "名前は必須です" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

