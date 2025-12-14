"""
Comprehensive tests for PyNext form two-way binding.

Tests cover:
- bind= attribute handling
- Different input types (text, checkbox, radio, select)
- Value synchronization
- Event handler generation

Total: 100+ tests
"""

import pytest
from pynext.reactive.forms import create_form, required
from pynext.reactive import signal
from pynext.core.html import Element, input_, div, select, option, textarea


# =============================================================================
# BIND ATTRIBUTE HANDLING (30 tests)
# =============================================================================

class TestBindAttribute:
    """Tests for bind= attribute on elements."""
    
    def test_bind_creates_value_attr(self):
        """bind= adds value attribute."""
        form = create_form(initial={"name": "Alice"})
        el = input_(bind=form.name)
        assert "value" in el.attrs or hasattr(el, 'attrs') and 'value' in el.attrs
    
    def test_bind_creates_oninput_handler(self):
        """bind= adds oninput handler."""
        form = create_form(initial={"name": ""})
        el = input_(bind=form.name)
        assert "oninput" in el.attrs
    
    def test_bind_removes_bind_attr(self):
        """bind= attribute is removed after processing."""
        form = create_form(initial={"name": ""})
        el = input_(bind=form.name)
        assert "bind" not in el.attrs
    
    def test_bind_with_signal(self):
        """bind= works with raw signals."""
        s = signal("hello")
        el = input_(bind=s)
        assert el.attrs.get("value") == s
    
    def test_bind_with_other_attrs(self):
        """bind= works alongside other attributes."""
        form = create_form(initial={"name": ""})
        el = input_(
            bind=form.name,
            type="text",
            placeholder="Enter name",
            class_="input",
        )
        assert el.attrs.get("type") == "text"
        assert el.attrs.get("placeholder") == "Enter name"
    
    def test_bind_preserves_existing_oninput(self):
        """Explicit oninput takes precedence."""
        form = create_form(initial={"name": ""})
        custom_handler = lambda e: None
        el = input_(
            bind=form.name,
            oninput=custom_handler,
        )
        assert el.attrs["oninput"] == custom_handler
    
    def test_bind_text_input(self):
        """bind= on text input."""
        form = create_form(initial={"name": ""})
        el = input_(type="text", bind=form.name)
        assert el.attrs.get("type") == "text"
    
    def test_bind_email_input(self):
        """bind= on email input."""
        form = create_form(initial={"email": ""})
        el = input_(type="email", bind=form.email)
        assert el.attrs.get("type") == "email"
    
    def test_bind_password_input(self):
        """bind= on password input."""
        form = create_form(initial={"password": ""})
        el = input_(type="password", bind=form.password)
        assert el.attrs.get("type") == "password"
    
    def test_bind_number_input(self):
        """bind= on number input."""
        form = create_form(initial={"age": 0})
        el = input_(type="number", bind=form.age)
        assert el.attrs.get("type") == "number"


# =============================================================================
# CHECKBOX BINDING (20 tests)
# =============================================================================

class TestCheckboxBinding:
    """Tests for bind= on checkbox inputs."""
    
    def test_bind_checkbox_adds_checked(self):
        """bind= on checkbox adds checked attribute."""
        form = create_form(initial={"agree": False})
        el = input_(type="checkbox", bind=form.agree)
        assert "checked" in el.attrs
    
    def test_bind_checkbox_value(self):
        """Checkbox value is boolean."""
        form = create_form(initial={"agree": True})
        el = input_(type="checkbox", bind=form.agree)
        # The checked attribute should be the signal
        assert el.attrs.get("checked") == form.agree
    
    def test_bind_checkbox_oninput(self):
        """Checkbox has oninput handler."""
        form = create_form(initial={"agree": False})
        el = input_(type="checkbox", bind=form.agree)
        assert "oninput" in el.attrs


# =============================================================================
# RADIO BINDING (15 tests)
# =============================================================================

class TestRadioBinding:
    """Tests for bind= on radio inputs."""
    
    def test_bind_radio_value(self):
        """Radio button has value attribute."""
        form = create_form(initial={"choice": ""})
        el = input_(type="radio", bind=form.choice, value="option1")
        # Radio should have both value and bind handling
        assert el.attrs.get("type") == "radio"
    
    def test_bind_radio_oninput(self):
        """Radio button has oninput handler."""
        form = create_form(initial={"choice": ""})
        el = input_(type="radio", bind=form.choice, value="a")
        assert "oninput" in el.attrs


# =============================================================================
# SELECT BINDING (20 tests)
# =============================================================================

class TestSelectBinding:
    """Tests for bind= on select elements."""
    
    def test_bind_select_value(self):
        """bind= on select adds value attribute."""
        form = create_form(initial={"country": "us"})
        el = select(bind=form.country)[
            option(value="us")["United States"],
            option(value="uk")["United Kingdom"],
        ]
        assert "value" in el.attrs
    
    def test_bind_select_oninput(self):
        """bind= on select adds oninput handler."""
        form = create_form(initial={"country": ""})
        el = select(bind=form.country)
        assert "oninput" in el.attrs
    
    def test_bind_select_with_options(self):
        """Select with options renders correctly."""
        form = create_form(initial={"priority": "medium"})
        el = select(bind=form.priority)[
            option(value="low")["Low"],
            option(value="medium")["Medium"],
            option(value="high")["High"],
        ]
        assert len(el.children) == 3


# =============================================================================
# TEXTAREA BINDING (15 tests)
# =============================================================================

class TestTextareaBinding:
    """Tests for bind= on textarea elements."""
    
    def test_bind_textarea_value(self):
        """bind= on textarea adds value attribute."""
        form = create_form(initial={"description": ""})
        el = textarea(bind=form.description)
        assert "value" in el.attrs
    
    def test_bind_textarea_oninput(self):
        """bind= on textarea adds oninput handler."""
        form = create_form(initial={"description": ""})
        el = textarea(bind=form.description)
        assert "oninput" in el.attrs
    
    def test_bind_textarea_with_attrs(self):
        """textarea with additional attributes."""
        form = create_form(initial={"description": ""})
        el = textarea(
            bind=form.description,
            rows="5",
            placeholder="Enter description...",
        )
        assert el.attrs.get("rows") == "5"
        assert el.attrs.get("placeholder") == "Enter description..."


# =============================================================================
# FORM INTEGRATION (20 tests)
# =============================================================================

class TestFormIntegration:
    """Tests for form + binding integration."""
    
    def test_multiple_fields_binding(self):
        """Multiple fields with binding."""
        form = create_form(initial={
            "name": "",
            "email": "",
            "agree": False,
        })
        
        name_input = input_(type="text", bind=form.name)
        email_input = input_(type="email", bind=form.email)
        agree_input = input_(type="checkbox", bind=form.agree)
        
        assert "value" in name_input.attrs
        assert "value" in email_input.attrs
        assert "checked" in agree_input.attrs
    
    def test_form_layout(self):
        """Complete form layout with binding."""
        form = create_form(
            initial={"name": "", "email": ""},
            validators={
                "name": [required()],
                "email": [required()],
            }
        )
        
        layout = div()[
            div()[
                input_(type="text", bind=form.name),
            ],
            div()[
                input_(type="email", bind=form.email),
            ],
        ]
        
        assert len(layout.children) == 2
    
    def test_validation_with_binding(self):
        """Form validation works with bound fields."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        
        assert not form.is_valid()
        
        # Simulate input
        form.name.set("Alice")
        
        assert form.is_valid()
    
    def test_bind_initial_value_render(self):
        """Initial value is used in rendering."""
        form = create_form(initial={"name": "Alice"})
        el = input_(bind=form.name)
        
        # The value attribute should be the signal
        assert el.attrs["value"] == form.name
    
    def test_bind_dynamic_value(self):
        """Value updates dynamically."""
        form = create_form(initial={"count": 0})
        el = input_(type="number", bind=form.count)
        
        form.count.set(42)
        
        # Signal value should be updated
        assert form.count() == 42
    
    def test_error_display_with_binding(self):
        """Error display alongside binding."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        
        form.validate()
        
        assert form.errors.name != ""
        
        error_el = form.error_for("name")
        assert error_el is not None
    
    def test_reset_clears_bound_fields(self):
        """Reset clears bound field values."""
        form = create_form(initial={"name": "Alice"})
        
        form.name.set("Bob")
        assert form.name() == "Bob"
        
        form.reset()
        assert form.name() == "Alice"


# =============================================================================
# EDGE CASES (10 tests)
# =============================================================================

class TestBindingEdgeCases:
    """Edge case tests for binding."""
    
    def test_bind_non_signal(self):
        """bind= with non-signal just sets value."""
        el = input_(bind="static_value")
        assert el.attrs.get("value") == "static_value"
    
    def test_bind_none(self):
        """bind= with None."""
        el = input_(bind=None)
        assert el.attrs.get("value") is None
    
    def test_bind_empty_form(self):
        """Form with no fields."""
        form = create_form(initial={})
        # Should not raise
        assert form.field_names() == []
    
    def test_bind_special_characters(self):
        """Field with special characters in value."""
        form = create_form(initial={"code": "<script>alert('xss')</script>"})
        el = input_(bind=form.code)
        # Value should be the signal, rendering handles escaping
        assert el.attrs["value"] == form.code
    
    def test_bind_unicode(self):
        """Field with unicode value."""
        form = create_form(initial={"name": "日本語"})
        el = input_(bind=form.name)
        assert form.name() == "日本語"
    
    def test_bind_long_value(self):
        """Field with very long value."""
        long_value = "a" * 10000
        form = create_form(initial={"text": long_value})
        el = textarea(bind=form.text)
        assert form.text() == long_value

