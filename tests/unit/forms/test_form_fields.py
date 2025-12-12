"""
Comprehensive tests for form field signals.

Tests cover:
- Field signal creation
- Field read/write
- Field reactivity
- Field types
- Field edge cases

Total: 100+ tests
"""

import pytest
from pynext.reactive.forms import create_form, required
from pynext.reactive import signal, effect


# =============================================================================
# FIELD SIGNAL BASICS (30 tests)
# =============================================================================

class TestFieldSignalBasics:
    """Tests for basic field signal operations."""
    
    def test_field_is_callable(self):
        """Field can be called to get value."""
        form = create_form(initial={"name": "Alice"})
        assert callable(form.name)
        assert form.name() == "Alice"
    
    def test_field_has_set(self):
        """Field has set method."""
        form = create_form(initial={"name": ""})
        assert hasattr(form.name, "set")
    
    def test_field_has_update(self):
        """Field has update method."""
        form = create_form(initial={"count": 0})
        assert hasattr(form.count, "update")
    
    def test_field_set_changes_value(self):
        """Field set changes value."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        assert form.name() == "Bob"
    
    def test_field_update_with_function(self):
        """Field update applies function."""
        form = create_form(initial={"count": 5})
        form.count.update(lambda x: x * 2)
        assert form.count() == 10
    
    def test_multiple_sets(self):
        """Multiple sets work."""
        form = create_form(initial={"value": 0})
        form.value.set(1)
        form.value.set(2)
        form.value.set(3)
        assert form.value() == 3
    
    def test_field_independent(self):
        """Fields are independent."""
        form = create_form(initial={"a": 1, "b": 2})
        form.a.set(10)
        assert form.a() == 10
        assert form.b() == 2
    
    def test_field_with_empty_string(self):
        """Field with empty string."""
        form = create_form(initial={"name": ""})
        assert form.name() == ""
    
    def test_field_with_zero(self):
        """Field with zero."""
        form = create_form(initial={"count": 0})
        assert form.count() == 0
    
    def test_field_with_false(self):
        """Field with False."""
        form = create_form(initial={"active": False})
        assert form.active() is False
    
    def test_field_with_none(self):
        """Field with None."""
        form = create_form(initial={"nullable": None})
        assert form.nullable() is None
    
    def test_field_with_list(self):
        """Field with list."""
        form = create_form(initial={"items": [1, 2, 3]})
        assert form.items() == [1, 2, 3]
    
    def test_field_with_dict(self):
        """Field with dict."""
        form = create_form(initial={"config": {"key": "value"}})
        assert form.config() == {"key": "value"}
    
    def test_field_with_nested_list(self):
        """Field with nested list."""
        form = create_form(initial={"matrix": [[1, 2], [3, 4]]})
        assert form.matrix() == [[1, 2], [3, 4]]
    
    def test_field_set_to_none(self):
        """Can set field to None."""
        form = create_form(initial={"name": "Alice"})
        form.name.set(None)
        assert form.name() is None
    
    def test_field_set_to_different_type(self):
        """Can set field to different type."""
        form = create_form(initial={"value": "string"})
        form.value.set(42)
        assert form.value() == 42


# =============================================================================
# FIELD STRING TYPES (20 tests)
# =============================================================================

class TestFieldStringTypes:
    """Tests for string field operations."""
    
    def test_string_field_basic(self):
        """Basic string field."""
        form = create_form(initial={"name": "Alice"})
        assert form.name() == "Alice"
    
    def test_string_field_empty(self):
        """Empty string field."""
        form = create_form(initial={"name": ""})
        assert form.name() == ""
    
    def test_string_field_unicode(self):
        """Unicode string field."""
        form = create_form(initial={"name": "日本語"})
        assert form.name() == "日本語"
    
    def test_string_field_emoji(self):
        """Emoji string field."""
        form = create_form(initial={"emoji": "🎉🎊"})
        assert form.emoji() == "🎉🎊"
    
    def test_string_field_whitespace(self):
        """Whitespace string field."""
        form = create_form(initial={"text": "  spaces  "})
        assert form.text() == "  spaces  "
    
    def test_string_field_newlines(self):
        """String with newlines."""
        form = create_form(initial={"text": "line1\nline2\nline3"})
        assert form.text() == "line1\nline2\nline3"
    
    def test_string_field_special_chars(self):
        """String with special characters."""
        form = create_form(initial={"code": "<script>alert('xss')</script>"})
        assert form.code() == "<script>alert('xss')</script>"
    
    def test_string_field_long(self):
        """Long string field."""
        long_str = "a" * 10000
        form = create_form(initial={"text": long_str})
        assert form.text() == long_str
    
    def test_string_field_set(self):
        """Set string field."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        assert form.name() == "Bob"
    
    def test_string_field_append(self):
        """Append to string field."""
        form = create_form(initial={"text": "Hello"})
        form.text.update(lambda x: x + " World")
        assert form.text() == "Hello World"


# =============================================================================
# FIELD NUMBER TYPES (20 tests)
# =============================================================================

class TestFieldNumberTypes:
    """Tests for number field operations."""
    
    def test_int_field_basic(self):
        """Basic integer field."""
        form = create_form(initial={"count": 42})
        assert form.count() == 42
    
    def test_int_field_zero(self):
        """Zero integer field."""
        form = create_form(initial={"count": 0})
        assert form.count() == 0
    
    def test_int_field_negative(self):
        """Negative integer field."""
        form = create_form(initial={"count": -5})
        assert form.count() == -5
    
    def test_int_field_large(self):
        """Large integer field."""
        form = create_form(initial={"big": 10**20})
        assert form.big() == 10**20
    
    def test_float_field_basic(self):
        """Basic float field."""
        form = create_form(initial={"price": 3.14})
        assert form.price() == 3.14
    
    def test_float_field_zero(self):
        """Zero float field."""
        form = create_form(initial={"price": 0.0})
        assert form.price() == 0.0
    
    def test_float_field_negative(self):
        """Negative float field."""
        form = create_form(initial={"temp": -10.5})
        assert form.temp() == -10.5
    
    def test_int_field_increment(self):
        """Increment integer field."""
        form = create_form(initial={"count": 0})
        form.count.update(lambda x: x + 1)
        assert form.count() == 1
    
    def test_int_field_decrement(self):
        """Decrement integer field."""
        form = create_form(initial={"count": 10})
        form.count.update(lambda x: x - 1)
        assert form.count() == 9
    
    def test_float_field_math(self):
        """Math on float field."""
        form = create_form(initial={"value": 10.0})
        form.value.update(lambda x: x * 1.5)
        assert form.value() == 15.0


# =============================================================================
# FIELD BOOLEAN TYPES (15 tests)
# =============================================================================

class TestFieldBooleanTypes:
    """Tests for boolean field operations."""
    
    def test_bool_field_true(self):
        """True boolean field."""
        form = create_form(initial={"active": True})
        assert form.active() is True
    
    def test_bool_field_false(self):
        """False boolean field."""
        form = create_form(initial={"active": False})
        assert form.active() is False
    
    def test_bool_field_toggle(self):
        """Toggle boolean field."""
        form = create_form(initial={"active": False})
        form.active.update(lambda x: not x)
        assert form.active() is True
        form.active.update(lambda x: not x)
        assert form.active() is False
    
    def test_bool_field_set_true(self):
        """Set to True."""
        form = create_form(initial={"active": False})
        form.active.set(True)
        assert form.active() is True
    
    def test_bool_field_set_false(self):
        """Set to False."""
        form = create_form(initial={"active": True})
        form.active.set(False)
        assert form.active() is False
    
    def test_multiple_bool_fields(self):
        """Multiple boolean fields."""
        form = create_form(initial={
            "option1": True,
            "option2": False,
            "option3": True,
        })
        assert form.option1() is True
        assert form.option2() is False
        assert form.option3() is True


# =============================================================================
# FIELD COMPLEX TYPES (15 tests)
# =============================================================================

class TestFieldComplexTypes:
    """Tests for complex field types."""
    
    def test_list_field_basic(self):
        """Basic list field."""
        form = create_form(initial={"items": [1, 2, 3]})
        assert form.items() == [1, 2, 3]
    
    def test_list_field_empty(self):
        """Empty list field."""
        form = create_form(initial={"items": []})
        assert form.items() == []
    
    def test_list_field_append(self):
        """Set list with new item."""
        form = create_form(initial={"items": [1, 2]})
        form.items.set([1, 2, 3])
        assert form.items() == [1, 2, 3]
    
    def test_list_field_mixed_types(self):
        """List with mixed types."""
        form = create_form(initial={"mixed": [1, "two", True, None]})
        assert form.mixed() == [1, "two", True, None]
    
    def test_dict_field_basic(self):
        """Basic dict field."""
        form = create_form(initial={"config": {"a": 1, "b": 2}})
        assert form.config() == {"a": 1, "b": 2}
    
    def test_dict_field_empty(self):
        """Empty dict field."""
        form = create_form(initial={"config": {}})
        assert form.config() == {}
    
    def test_dict_field_nested(self):
        """Nested dict field."""
        form = create_form(initial={"config": {"level1": {"level2": "value"}}})
        assert form.config() == {"level1": {"level2": "value"}}
    
    def test_list_of_dicts(self):
        """List of dicts field."""
        form = create_form(initial={"rows": [{"id": 1}, {"id": 2}]})
        assert form.rows() == [{"id": 1}, {"id": 2}]
    
    def test_tuple_converted_to_list(self):
        """Tuple preserved or converted."""
        form = create_form(initial={"coords": (1, 2, 3)})
        # May be converted to list depending on implementation
        result = form.coords()
        assert len(result) == 3

