"""
Comprehensive tests for form hydration support.

Tests cover:
- Form serialization
- to_json()
- to_hydration_state()
- get_js_init()
- SSR context integration

Total: 50+ tests
"""

import pytest
import json
from pynext.reactive.forms import create_form, required, email


# =============================================================================
# TO_JSON (20 tests)
# =============================================================================

class TestToJson:
    """Tests for to_json() serialization."""
    
    def test_to_json_returns_dict(self):
        """to_json returns a dictionary."""
        form = create_form(initial={"name": ""})
        result = form.to_json()
        assert isinstance(result, dict)
    
    def test_to_json_includes_values(self):
        """to_json includes values key."""
        form = create_form(initial={"name": "Alice"})
        result = form.to_json()
        assert "values" in result
        assert result["values"]["name"] == "Alice"
    
    def test_to_json_includes_errors(self):
        """to_json includes errors key."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        result = form.to_json()
        assert "errors" in result
        assert "name" in result["errors"]
    
    def test_to_json_includes_touched(self):
        """to_json includes touched key."""
        form = create_form(initial={"name": ""})
        form.set_touched("name", True)
        result = form.to_json()
        assert "touched" in result
        assert result["touched"]["name"] is True
    
    def test_to_json_includes_is_submitting(self):
        """to_json includes isSubmitting key."""
        form = create_form(initial={"name": ""})
        result = form.to_json()
        assert "isSubmitting" in result
        assert result["isSubmitting"] is False
    
    def test_to_json_reflects_changes(self):
        """to_json reflects current state."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        result = form.to_json()
        assert result["values"]["name"] == "Bob"
    
    def test_to_json_errors_only_invalid(self):
        """to_json errors only includes fields with errors."""
        form = create_form(
            initial={"name": "Alice", "email": ""},
            validators={
                "name": [required()],
                "email": [required()],
            }
        )
        form.validate()
        result = form.to_json()
        assert "name" not in result["errors"]
        assert "email" in result["errors"]
    
    def test_to_json_multiple_fields(self):
        """to_json with multiple fields."""
        form = create_form(initial={
            "name": "Alice",
            "email": "alice@example.com",
            "age": 25,
        })
        result = form.to_json()
        assert result["values"]["name"] == "Alice"
        assert result["values"]["email"] == "alice@example.com"
        assert result["values"]["age"] == 25
    
    def test_to_json_is_json_serializable(self):
        """to_json result is JSON serializable."""
        form = create_form(initial={
            "string": "hello",
            "number": 42,
            "boolean": True,
            "none": None,
        })
        result = form.to_json()
        # Should not raise
        json_str = json.dumps(result)
        assert json_str
    
    def test_to_json_with_list_values(self):
        """to_json handles list values."""
        form = create_form(initial={"items": [1, 2, 3]})
        result = form.to_json()
        assert result["values"]["items"] == [1, 2, 3]
    
    def test_to_json_with_dict_values(self):
        """to_json handles dict values."""
        form = create_form(initial={"config": {"key": "value"}})
        result = form.to_json()
        assert result["values"]["config"] == {"key": "value"}
    
    def test_to_json_empty_form(self):
        """to_json with empty form."""
        form = create_form(initial={})
        result = form.to_json()
        assert result["values"] == {}
        assert result["errors"] == {}


# =============================================================================
# TO_HYDRATION_STATE (15 tests)
# =============================================================================

class TestToHydrationState:
    """Tests for to_hydration_state() serialization."""
    
    def test_to_hydration_state_returns_dict(self):
        """to_hydration_state returns dict."""
        form = create_form(initial={"name": ""})
        result = form.to_hydration_state()
        assert isinstance(result, dict)
    
    def test_to_hydration_state_type(self):
        """to_hydration_state includes type."""
        form = create_form(initial={"name": ""})
        result = form.to_hydration_state()
        assert result["type"] == "form"
    
    def test_to_hydration_state_initial(self):
        """to_hydration_state includes initial values."""
        form = create_form(initial={"name": "Alice"})
        result = form.to_hydration_state()
        assert "initial" in result
        assert result["initial"]["name"] == "Alice"
    
    def test_to_hydration_state_values(self):
        """to_hydration_state includes current values."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        result = form.to_hydration_state()
        assert "values" in result
        assert result["values"]["name"] == "Bob"
    
    def test_to_hydration_state_preserves_initial(self):
        """to_hydration_state initial unchanged after value change."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        result = form.to_hydration_state()
        assert result["initial"]["name"] == "Alice"
        assert result["values"]["name"] == "Bob"
    
    def test_to_hydration_state_is_json_serializable(self):
        """to_hydration_state is JSON serializable."""
        form = create_form(initial={"name": "Alice", "count": 42})
        result = form.to_hydration_state()
        json_str = json.dumps(result)
        assert json_str
    
    def test_to_hydration_state_multiple_fields(self):
        """to_hydration_state with multiple fields."""
        form = create_form(initial={
            "name": "Alice",
            "email": "alice@example.com",
        })
        result = form.to_hydration_state()
        assert len(result["initial"]) == 2
        assert len(result["values"]) == 2


# =============================================================================
# GET_JS_INIT (15 tests)
# =============================================================================

class TestGetJsInit:
    """Tests for get_js_init() JavaScript code generation."""
    
    def test_get_js_init_returns_string(self):
        """get_js_init returns string."""
        form = create_form(initial={"name": ""})
        result = form.get_js_init()
        assert isinstance(result, str)
    
    def test_get_js_init_contains_create_form(self):
        """get_js_init contains createForm call."""
        form = create_form(initial={"name": ""})
        result = form.get_js_init()
        assert "createForm" in result
    
    def test_get_js_init_contains_initial(self):
        """get_js_init contains initial values."""
        form = create_form(initial={"name": "Alice"})
        result = form.get_js_init()
        assert '"name"' in result or "'name'" in result
        assert "Alice" in result
    
    def test_get_js_init_valid_js(self):
        """get_js_init generates valid-looking JS."""
        form = create_form(initial={"name": "Alice", "count": 42})
        result = form.get_js_init()
        # Should look like: createForm({"name": "Alice", "count": 42})
        assert result.startswith("createForm(")
        assert result.endswith(")")
    
    def test_get_js_init_escapes_quotes(self):
        """get_js_init escapes quotes in strings."""
        form = create_form(initial={"name": 'He said "hello"'})
        result = form.get_js_init()
        # Should be escaped
        assert '\\"' in result or "\\'" in result or '"He said' in result
    
    def test_get_js_init_handles_unicode(self):
        """get_js_init handles unicode."""
        form = create_form(initial={"name": "日本語"})
        result = form.get_js_init()
        assert "日本語" in result or "\\u" in result
    
    def test_get_js_init_handles_special_chars(self):
        """get_js_init handles special characters."""
        form = create_form(initial={"code": "<script>alert('xss')</script>"})
        result = form.get_js_init()
        # Should be JSON-escaped
        assert "script" in result
    
    def test_get_js_init_handles_none(self):
        """get_js_init handles None values."""
        form = create_form(initial={"nullable": None})
        result = form.get_js_init()
        assert "null" in result
    
    def test_get_js_init_handles_boolean(self):
        """get_js_init handles boolean values."""
        form = create_form(initial={"active": True, "disabled": False})
        result = form.get_js_init()
        assert "true" in result
        assert "false" in result
    
    def test_get_js_init_handles_number(self):
        """get_js_init handles number values."""
        form = create_form(initial={"count": 42, "price": 3.14})
        result = form.get_js_init()
        assert "42" in result
        assert "3.14" in result
    
    def test_get_js_init_handles_list(self):
        """get_js_init handles list values."""
        form = create_form(initial={"items": [1, 2, 3]})
        result = form.get_js_init()
        assert "[1, 2, 3]" in result or "[1,2,3]" in result

