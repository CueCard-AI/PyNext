"""
Tests for PyNext Database Validation.

Tests for type validation, coercion, constraints, and custom validators.
"""

import pytest
from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Dict, Optional
from uuid import UUID, uuid4

from pynext.db.fields import FieldInfo, SQLType
from pynext.db.validation import (
    validate_type,
    validate_constraints,
    validate_field,
    validate_data,
    run_validators,
    Validator,
    MinLength,
    MaxLength,
    MinValue,
    MaxValue,
    Regex,
    Email,
    URL,
    OneOf,
    NotEmpty,
    Lowercase,
    Uppercase,
    Strip,
)
from pynext.db.exceptions import ValidationError


# =============================================================================
# Type Validation Tests (40 tests)
# =============================================================================

class TestTypeValidation:
    """Tests for validate_type function."""
    
    def test_str_valid(self):
        """Test valid string."""
        field = FieldInfo("name", str, SQLType.VARCHAR)
        assert validate_type("hello", field) == "hello"
    
    def test_str_from_int(self):
        """Test string coercion from int."""
        field = FieldInfo("name", str, SQLType.VARCHAR)
        assert validate_type(42, field) == "42"
    
    def test_str_from_float(self):
        """Test string coercion from float."""
        field = FieldInfo("name", str, SQLType.VARCHAR)
        assert validate_type(3.14, field) == "3.14"
    
    def test_str_from_bool(self):
        """Test string coercion from bool."""
        field = FieldInfo("name", str, SQLType.VARCHAR)
        assert validate_type(True, field) == "True"
    
    def test_int_valid(self):
        """Test valid integer."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        assert validate_type(42, field) == 42
    
    def test_int_from_str(self):
        """Test integer coercion from string."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        assert validate_type("42", field) == 42
    
    def test_int_from_float_whole(self):
        """Test integer coercion from whole float."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        assert validate_type(42.0, field) == 42
    
    def test_int_from_float_decimal_fails(self):
        """Test integer coercion from decimal float fails."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        with pytest.raises(ValidationError) as exc:
            validate_type(42.5, field)
        assert "decimal part" in str(exc.value)
    
    def test_int_from_invalid_str_fails(self):
        """Test integer coercion from invalid string fails."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        with pytest.raises(ValidationError) as exc:
            validate_type("abc", field)
        assert "count" in str(exc.value)
    
    def test_float_valid(self):
        """Test valid float."""
        field = FieldInfo("price", float, SQLType.REAL)
        assert validate_type(3.14, field) == 3.14
    
    def test_float_from_int(self):
        """Test float coercion from int."""
        field = FieldInfo("price", float, SQLType.REAL)
        assert validate_type(42, field) == 42.0
    
    def test_float_from_str(self):
        """Test float coercion from string."""
        field = FieldInfo("price", float, SQLType.REAL)
        assert validate_type("3.14", field) == 3.14
    
    def test_float_from_invalid_str_fails(self):
        """Test float coercion from invalid string fails."""
        field = FieldInfo("price", float, SQLType.REAL)
        with pytest.raises(ValidationError):
            validate_type("abc", field)
    
    def test_bool_valid_true(self):
        """Test valid boolean True."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type(True, field) is True
    
    def test_bool_valid_false(self):
        """Test valid boolean False."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type(False, field) is False
    
    def test_bool_from_int_1(self):
        """Test boolean coercion from 1."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type(1, field) is True
    
    def test_bool_from_int_0(self):
        """Test boolean coercion from 0."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type(0, field) is False
    
    def test_bool_from_str_true(self):
        """Test boolean coercion from 'true'."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type("true", field) is True
    
    def test_bool_from_str_false(self):
        """Test boolean coercion from 'false'."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type("false", field) is False
    
    def test_bool_from_str_yes(self):
        """Test boolean coercion from 'yes'."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type("yes", field) is True
    
    def test_bool_from_str_no(self):
        """Test boolean coercion from 'no'."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type("no", field) is False
    
    def test_bool_from_invalid_str_fails(self):
        """Test boolean coercion from invalid string fails."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        with pytest.raises(ValidationError) as exc:
            validate_type("maybe", field)
        assert "true/false" in str(exc.value)
    
    def test_datetime_valid(self):
        """Test valid datetime."""
        field = FieldInfo("timestamp", datetime, SQLType.TIMESTAMP)
        dt = datetime(2024, 1, 15, 12, 30, 45)
        assert validate_type(dt, field) == dt
    
    def test_datetime_from_str(self):
        """Test datetime coercion from ISO string."""
        field = FieldInfo("timestamp", datetime, SQLType.TIMESTAMP)
        result = validate_type("2024-01-15T12:30:45", field)
        assert result == datetime(2024, 1, 15, 12, 30, 45)
    
    def test_datetime_from_date(self):
        """Test datetime coercion from date."""
        field = FieldInfo("timestamp", datetime, SQLType.TIMESTAMP)
        result = validate_type(date(2024, 1, 15), field)
        assert result.date() == date(2024, 1, 15)
    
    def test_datetime_from_invalid_str_fails(self):
        """Test datetime coercion from invalid string fails."""
        field = FieldInfo("timestamp", datetime, SQLType.TIMESTAMP)
        with pytest.raises(ValidationError) as exc:
            validate_type("not a date", field)
        assert "ISO format" in str(exc.value)
    
    def test_date_valid(self):
        """Test valid date."""
        field = FieldInfo("birthday", date, SQLType.DATE)
        d = date(2024, 1, 15)
        assert validate_type(d, field) == d
    
    def test_date_from_str(self):
        """Test date coercion from ISO string."""
        field = FieldInfo("birthday", date, SQLType.DATE)
        result = validate_type("2024-01-15", field)
        assert result == date(2024, 1, 15)
    
    def test_date_from_datetime(self):
        """Test date coercion from datetime."""
        field = FieldInfo("birthday", date, SQLType.DATE)
        result = validate_type(datetime(2024, 1, 15, 12, 30), field)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_uuid_valid(self):
        """Test valid UUID."""
        field = FieldInfo("external_id", UUID, SQLType.UUID)
        u = uuid4()
        assert validate_type(u, field) == u
    
    def test_uuid_from_str(self):
        """Test UUID coercion from string."""
        field = FieldInfo("external_id", UUID, SQLType.UUID)
        u = uuid4()
        result = validate_type(str(u), field)
        assert result == u
    
    def test_uuid_from_invalid_str_fails(self):
        """Test UUID coercion from invalid string fails."""
        field = FieldInfo("external_id", UUID, SQLType.UUID)
        with pytest.raises(ValidationError):
            validate_type("not-a-uuid", field)
    
    def test_list_valid(self):
        """Test valid list."""
        field = FieldInfo("tags", list, SQLType.JSON)
        data = ["a", "b", "c"]
        assert validate_type(data, field) == data
    
    def test_list_from_tuple(self):
        """Test list coercion from tuple."""
        field = FieldInfo("tags", list, SQLType.JSON)
        assert validate_type(("a", "b", "c"), field) == ["a", "b", "c"]
    
    def test_list_from_json_str(self):
        """Test list coercion from JSON string."""
        field = FieldInfo("tags", list, SQLType.JSON)
        assert validate_type('["a", "b", "c"]', field) == ["a", "b", "c"]
    
    def test_dict_valid(self):
        """Test valid dict."""
        field = FieldInfo("metadata", dict, SQLType.JSON)
        data = {"key": "value"}
        assert validate_type(data, field) == data
    
    def test_dict_from_json_str(self):
        """Test dict coercion from JSON string."""
        field = FieldInfo("metadata", dict, SQLType.JSON)
        assert validate_type('{"key": "value"}', field) == {"key": "value"}
    
    def test_nullable_allows_none(self):
        """Test nullable field allows None."""
        field = FieldInfo("bio", str, SQLType.VARCHAR, nullable=True)
        assert validate_type(None, field) is None
    
    def test_required_rejects_none(self):
        """Test required field rejects None."""
        field = FieldInfo("name", str, SQLType.VARCHAR, nullable=False)
        with pytest.raises(ValidationError) as exc:
            validate_type(None, field)
        assert "required" in str(exc.value)
    
    def test_decimal_valid(self):
        """Test valid Decimal."""
        field = FieldInfo("amount", Decimal, SQLType.DECIMAL)
        d = Decimal("123.45")
        assert validate_type(d, field) == d
    
    def test_decimal_from_int(self):
        """Test Decimal coercion from int."""
        field = FieldInfo("amount", Decimal, SQLType.DECIMAL)
        result = validate_type(100, field)
        assert result == Decimal("100")
    
    def test_decimal_from_str(self):
        """Test Decimal coercion from string."""
        field = FieldInfo("amount", Decimal, SQLType.DECIMAL)
        result = validate_type("123.45", field)
        assert result == Decimal("123.45")


# =============================================================================
# Constraint Validation Tests (20 tests)
# =============================================================================

class TestConstraintValidation:
    """Tests for validate_constraints function."""
    
    def test_max_length_valid(self):
        """Test max_length constraint passes."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=10)
        validate_constraints("hello", field)  # Should not raise
    
    def test_max_length_exact(self):
        """Test max_length at exact limit."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=5)
        validate_constraints("hello", field)  # Should not raise
    
    def test_max_length_exceeded(self):
        """Test max_length constraint fails."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=3)
        with pytest.raises(ValidationError) as exc:
            validate_constraints("hello", field)
        assert "max length 3" in str(exc.value)
        assert "got 5 chars" in str(exc.value)
    
    def test_empty_string_non_nullable(self):
        """Test empty string fails for non-nullable field."""
        field = FieldInfo("name", str, SQLType.VARCHAR, nullable=False)
        with pytest.raises(ValidationError) as exc:
            validate_constraints("", field)
        assert "cannot be empty" in str(exc.value)
    
    def test_empty_string_nullable(self):
        """Test empty string allowed for nullable field."""
        field = FieldInfo("bio", str, SQLType.VARCHAR, nullable=True)
        validate_constraints("", field)  # Should not raise
    
    def test_none_skipped(self):
        """Test None value skips constraints."""
        field = FieldInfo("bio", str, SQLType.VARCHAR, nullable=True, max_length=5)
        validate_constraints(None, field)  # Should not raise
    
    def test_non_string_skips_max_length(self):
        """Test non-string skips max_length."""
        field = FieldInfo("count", int, SQLType.INTEGER, max_length=5)
        validate_constraints(12345678, field)  # Should not raise


# =============================================================================
# Custom Validator Tests (30 tests)
# =============================================================================

class TestCustomValidators:
    """Tests for custom validator functions and classes."""
    
    def test_run_validator_success(self):
        """Test running a successful validator."""
        def uppercase(v):
            return v.upper()
        
        field = FieldInfo("name", str, SQLType.VARCHAR, validators=[uppercase])
        result = run_validators("hello", field)
        assert result == "HELLO"
    
    def test_run_validator_failure(self):
        """Test running a failing validator."""
        def must_be_email(v):
            if "@" not in v:
                raise ValueError("must be an email")
            return v
        
        field = FieldInfo("email", str, SQLType.VARCHAR, validators=[must_be_email])
        with pytest.raises(ValidationError) as exc:
            run_validators("notanemail", field)
        assert "must be an email" in str(exc.value)
    
    def test_run_multiple_validators(self):
        """Test running multiple validators in order."""
        def strip(v):
            return v.strip()
        
        def lowercase(v):
            return v.lower()
        
        field = FieldInfo("name", str, SQLType.VARCHAR, validators=[strip, lowercase])
        result = run_validators("  HELLO  ", field)
        assert result == "hello"
    
    def test_min_length_valid(self):
        """Test MinLength validator passes."""
        validator = MinLength(3)
        assert validator("hello") == "hello"
    
    def test_min_length_fails(self):
        """Test MinLength validator fails."""
        validator = MinLength(10)
        with pytest.raises(ValueError) as exc:
            validator("hi")
        assert "at least 10" in str(exc.value)
    
    def test_max_length_valid(self):
        """Test MaxLength validator passes."""
        validator = MaxLength(10)
        assert validator("hello") == "hello"
    
    def test_max_length_fails(self):
        """Test MaxLength validator fails."""
        validator = MaxLength(3)
        with pytest.raises(ValueError) as exc:
            validator("hello")
        assert "at most 3" in str(exc.value)
    
    def test_min_value_valid(self):
        """Test MinValue validator passes."""
        validator = MinValue(0)
        assert validator(5) == 5
    
    def test_min_value_fails(self):
        """Test MinValue validator fails."""
        validator = MinValue(0)
        with pytest.raises(ValueError) as exc:
            validator(-5)
        assert "at least 0" in str(exc.value)
    
    def test_max_value_valid(self):
        """Test MaxValue validator passes."""
        validator = MaxValue(100)
        assert validator(50) == 50
    
    def test_max_value_fails(self):
        """Test MaxValue validator fails."""
        validator = MaxValue(100)
        with pytest.raises(ValueError) as exc:
            validator(150)
        assert "at most 100" in str(exc.value)
    
    def test_regex_valid(self):
        """Test Regex validator passes."""
        validator = Regex(r"^[a-z]+$")
        assert validator("hello") == "hello"
    
    def test_regex_fails(self):
        """Test Regex validator fails."""
        validator = Regex(r"^[a-z]+$", "must be lowercase letters only")
        with pytest.raises(ValueError) as exc:
            validator("Hello123")
        assert "lowercase letters only" in str(exc.value)
    
    def test_email_valid(self):
        """Test Email validator passes."""
        validator = Email()
        assert validator("test@example.com") == "test@example.com"
    
    def test_email_lowercases(self):
        """Test Email validator lowercases."""
        validator = Email()
        assert validator("TEST@Example.COM") == "test@example.com"
    
    def test_email_fails_no_at(self):
        """Test Email validator fails without @."""
        validator = Email()
        with pytest.raises(ValueError) as exc:
            validator("notanemail")
        assert "valid email" in str(exc.value)
    
    def test_email_fails_no_domain(self):
        """Test Email validator fails without domain dot."""
        validator = Email()
        with pytest.raises(ValueError) as exc:
            validator("test@localhost")
        assert "valid email" in str(exc.value)
    
    def test_url_valid_http(self):
        """Test URL validator passes for http."""
        validator = URL()
        assert validator("http://example.com") == "http://example.com"
    
    def test_url_valid_https(self):
        """Test URL validator passes for https."""
        validator = URL()
        assert validator("https://example.com") == "https://example.com"
    
    def test_url_fails(self):
        """Test URL validator fails for invalid URL."""
        validator = URL()
        with pytest.raises(ValueError) as exc:
            validator("not a url")
        assert "valid URL" in str(exc.value)
    
    def test_one_of_valid(self):
        """Test OneOf validator passes."""
        validator = OneOf(["admin", "user", "guest"])
        assert validator("admin") == "admin"
    
    def test_one_of_fails(self):
        """Test OneOf validator fails."""
        validator = OneOf(["admin", "user", "guest"])
        with pytest.raises(ValueError) as exc:
            validator("superuser")
        assert "'admin'" in str(exc.value)
    
    def test_not_empty_valid(self):
        """Test NotEmpty validator passes."""
        validator = NotEmpty()
        assert validator("hello") == "hello"
    
    def test_not_empty_fails_str(self):
        """Test NotEmpty validator fails for empty string."""
        validator = NotEmpty()
        with pytest.raises(ValueError) as exc:
            validator("")
        assert "cannot be empty" in str(exc.value)
    
    def test_not_empty_fails_list(self):
        """Test NotEmpty validator fails for empty list."""
        validator = NotEmpty()
        with pytest.raises(ValueError):
            validator([])
    
    def test_lowercase_transforms(self):
        """Test Lowercase transformer."""
        validator = Lowercase()
        assert validator("HELLO") == "hello"
    
    def test_uppercase_transforms(self):
        """Test Uppercase transformer."""
        validator = Uppercase()
        assert validator("hello") == "HELLO"
    
    def test_strip_transforms(self):
        """Test Strip transformer."""
        validator = Strip()
        assert validator("  hello  ") == "hello"
    
    def test_custom_validator_class(self):
        """Test custom Validator subclass."""
        class PositiveOnly(Validator):
            def __call__(self, value):
                if value <= 0:
                    raise ValueError("must be positive")
                return value
        
        validator = PositiveOnly()
        assert validator(5) == 5
        with pytest.raises(ValueError):
            validator(-5)


# =============================================================================
# Full Field Validation Tests (10 tests)
# =============================================================================

class TestFullFieldValidation:
    """Tests for validate_field function (full pipeline)."""
    
    def test_full_pipeline_simple(self):
        """Test full validation pipeline."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=10)
        result = validate_field("hello", field)
        assert result == "hello"
    
    def test_full_pipeline_with_coercion(self):
        """Test pipeline with type coercion."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        result = validate_field("42", field)
        assert result == 42
    
    def test_full_pipeline_with_validators(self):
        """Test pipeline with custom validators."""
        field = FieldInfo(
            "email", str, SQLType.VARCHAR,
            validators=[Email()]
        )
        result = validate_field("TEST@Example.COM", field)
        assert result == "test@example.com"
    
    def test_full_pipeline_all_steps(self):
        """Test pipeline with all steps."""
        field = FieldInfo(
            "name", str, SQLType.VARCHAR,
            max_length=20,
            validators=[Strip(), Lowercase()]
        )
        result = validate_field("  HELLO WORLD  ", field)
        assert result == "hello world"
    
    def test_full_pipeline_fails_type(self):
        """Test pipeline fails on type validation."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        with pytest.raises(ValidationError):
            validate_field("not a number", field)
    
    def test_full_pipeline_fails_constraint(self):
        """Test pipeline fails on constraint."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=3)
        with pytest.raises(ValidationError):
            validate_field("hello", field)
    
    def test_full_pipeline_fails_validator(self):
        """Test pipeline fails on validator."""
        field = FieldInfo(
            "role", str, SQLType.VARCHAR,
            validators=[OneOf(["admin", "user"])]
        )
        with pytest.raises(ValidationError):
            validate_field("superuser", field)


# =============================================================================
# Data Validation Tests (20 tests)
# =============================================================================

class TestDataValidation:
    """Tests for validate_data function."""
    
    def test_validate_data_simple(self):
        """Test validating simple data dict."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        result = validate_data({"name": "John"}, fields)
        assert result["name"] == "John"
    
    def test_validate_data_with_defaults(self):
        """Test validation uses defaults."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR),
            "role": FieldInfo("role", str, SQLType.VARCHAR, default="user"),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        result = validate_data({"name": "John"}, fields)
        assert result["role"] == "user"
    
    def test_validate_data_missing_required(self):
        """Test validation fails for missing required field."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR),
            "email": FieldInfo("email", str, SQLType.VARCHAR),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        with pytest.raises(ValidationError) as exc:
            validate_data({"name": "John"}, fields)
        assert "email" in str(exc.value)
        assert "required" in str(exc.value)
    
    def test_validate_data_unknown_field(self):
        """Test validation fails for unknown field."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        with pytest.raises(ValidationError) as exc:
            validate_data({"name": "John", "unknown": "value"}, fields)
        assert "unknown" in str(exc.value)
    
    def test_validate_data_partial(self):
        """Test partial validation for updates."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR),
            "email": FieldInfo("email", str, SQLType.VARCHAR),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        # Should not fail for missing email in partial mode
        result = validate_data({"name": "Jane"}, fields, partial=True)
        assert result["name"] == "Jane"
        assert "email" not in result
    
    def test_validate_data_multiple_errors(self):
        """Test validation collects multiple errors."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR),
            "email": FieldInfo("email", str, SQLType.VARCHAR),
            "age": FieldInfo("age", int, SQLType.INTEGER),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        with pytest.raises(ValidationError) as exc:
            validate_data({}, fields)
        # Should mention multiple missing fields
        assert "name" in str(exc.value)
        assert "email" in str(exc.value)
    
    def test_validate_data_type_coercion(self):
        """Test data validation with type coercion."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "count": FieldInfo("count", int, SQLType.INTEGER),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        result = validate_data({"count": "42"}, fields)
        assert result["count"] == 42
    
    def test_validate_data_nullable_default(self):
        """Test nullable field gets None as default."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR),
            "bio": FieldInfo("bio", str, SQLType.VARCHAR, nullable=True),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        result = validate_data({"name": "John"}, fields)
        assert result["bio"] is None
    
    def test_validate_data_excludes_auto_id(self):
        """Test id is excluded from validation by default."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        # Should not fail for missing id
        result = validate_data({"name": "John"}, fields)
        assert "id" not in result or result.get("id") is None
    
    def test_validate_data_passes_provided_id(self):
        """Test provided id is passed through."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        result = validate_data({"id": 123, "name": "John"}, fields)
        assert result["id"] == 123


# =============================================================================
# Advanced Type Validation Tests (40 additional tests)
# =============================================================================

class TestAdvancedTypeValidation:
    """Advanced tests for type validation edge cases."""
    
    def test_str_from_object_with_str_method(self):
        """Test string coercion from object with __str__."""
        class CustomObj:
            def __str__(self):
                return "custom"
        
        field = FieldInfo("name", str, SQLType.VARCHAR)
        result = validate_type(CustomObj(), field)
        assert result == "custom"
    
    def test_int_from_negative_str(self):
        """Test integer coercion from negative string."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        assert validate_type("-42", field) == -42
    
    def test_int_from_zero_str(self):
        """Test integer coercion from zero string."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        assert validate_type("0", field) == 0
    
    def test_float_from_negative_str(self):
        """Test float coercion from negative string."""
        field = FieldInfo("price", float, SQLType.REAL)
        assert validate_type("-3.14", field) == -3.14
    
    def test_float_from_scientific_notation(self):
        """Test float coercion from scientific notation."""
        field = FieldInfo("price", float, SQLType.REAL)
        assert validate_type("1e10", field) == 1e10
    
    def test_bool_from_str_1(self):
        """Test boolean coercion from '1'."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type("1", field) is True
    
    def test_bool_from_str_0(self):
        """Test boolean coercion from '0'."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type("0", field) is False
    
    def test_bool_from_str_on(self):
        """Test boolean coercion from 'on'."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type("on", field) is True
    
    def test_bool_from_str_off(self):
        """Test boolean coercion from 'off'."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert validate_type("off", field) is False
    
    def test_datetime_from_date_sets_midnight(self):
        """Test datetime from date sets time to midnight."""
        field = FieldInfo("timestamp", datetime, SQLType.TIMESTAMP)
        result = validate_type(date(2024, 1, 15), field)
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
    
    def test_datetime_from_str_with_microseconds(self):
        """Test datetime coercion with microseconds."""
        field = FieldInfo("timestamp", datetime, SQLType.TIMESTAMP)
        result = validate_type("2024-01-15T12:30:45.123456", field)
        assert result.microsecond == 123456
    
    def test_time_from_str_minimal(self):
        """Test time coercion from minimal format."""
        field = FieldInfo("alarm", time, SQLType.TIME)
        result = validate_type("12:30", field)
        assert result.hour == 12
        assert result.minute == 30
    
    def test_list_from_set(self):
        """Test list coercion from set."""
        field = FieldInfo("tags", list, SQLType.JSON)
        result = validate_type({"a", "b", "c"}, field)
        assert isinstance(result, list)
        assert set(result) == {"a", "b", "c"}
    
    def test_decimal_from_float(self):
        """Test Decimal coercion from float."""
        field = FieldInfo("amount", Decimal, SQLType.DECIMAL)
        result = validate_type(3.14, field)
        assert isinstance(result, Decimal)
    
    def test_type_error_includes_field_name(self):
        """Test error message includes field name."""
        field = FieldInfo("my_field", int, SQLType.INTEGER)
        with pytest.raises(ValidationError) as exc:
            validate_type("abc", field)
        assert "my_field" in str(exc.value)
    
    def test_type_error_includes_expected_type(self):
        """Test error message includes expected type."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        with pytest.raises(ValidationError) as exc:
            validate_type("abc", field)
        assert "int" in str(exc.value)
    
    def test_type_error_includes_got_type(self):
        """Test error message includes received type."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        with pytest.raises(ValidationError) as exc:
            validate_type("abc", field)
        assert "str" in str(exc.value)
    
    def test_none_on_required_shows_field_name(self):
        """Test None on required field shows field name."""
        field = FieldInfo("email", str, SQLType.VARCHAR, nullable=False)
        with pytest.raises(ValidationError) as exc:
            validate_type(None, field)
        assert "email" in str(exc.value)


class TestAdvancedConstraintValidation:
    """Advanced tests for constraint validation."""
    
    def test_max_length_exact_boundary(self):
        """Test max_length at exact boundary."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=5)
        validate_constraints("hello", field)  # Exactly 5 - should pass
    
    def test_max_length_one_over(self):
        """Test max_length one character over."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=5)
        with pytest.raises(ValidationError):
            validate_constraints("hello!", field)  # 6 chars
    
    def test_max_length_with_unicode(self):
        """Test max_length counts unicode chars correctly."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=5)
        validate_constraints("日本語🎉!", field)  # 5 chars
    
    def test_empty_string_allowed_nullable(self):
        """Test empty string is allowed when nullable."""
        field = FieldInfo("bio", str, SQLType.VARCHAR, nullable=True)
        validate_constraints("", field)  # Should not raise


class TestAdvancedValidatorChains:
    """Advanced tests for validator chains."""
    
    def test_validator_chain_order(self):
        """Test validators run in order."""
        calls = []
        
        def first(v):
            calls.append("first")
            return v + "1"
        
        def second(v):
            calls.append("second")
            return v + "2"
        
        field = FieldInfo("name", str, SQLType.VARCHAR, validators=[first, second])
        result = run_validators("x", field)
        
        assert calls == ["first", "second"]
        assert result == "x12"
    
    def test_validator_short_circuits_on_error(self):
        """Test validation stops on first error."""
        calls = []
        
        def failing(v):
            calls.append("failing")
            raise ValueError("failed")
        
        def never_called(v):
            calls.append("never")
            return v
        
        field = FieldInfo("name", str, SQLType.VARCHAR, validators=[failing, never_called])
        
        with pytest.raises(ValidationError):
            run_validators("x", field)
        
        assert calls == ["failing"]
    
    def test_min_length_exact_boundary(self):
        """Test MinLength at exact boundary."""
        validator = MinLength(5)
        assert validator("hello") == "hello"
    
    def test_min_length_one_under(self):
        """Test MinLength one under boundary."""
        validator = MinLength(5)
        with pytest.raises(ValueError):
            validator("hell")
    
    def test_regex_complex_pattern(self):
        """Test Regex with complex pattern."""
        validator = Regex(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", "must be valid email")
        assert validator("test@example.com") == "test@example.com"
    
    def test_regex_fails_complex_pattern(self):
        """Test Regex fails complex pattern."""
        validator = Regex(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", "must be valid email")
        with pytest.raises(ValueError):
            validator("not-an-email")
    
    def test_one_of_with_numbers(self):
        """Test OneOf with number options."""
        validator = OneOf([1, 2, 3])
        assert validator(2) == 2
    
    def test_one_of_fails_with_numbers(self):
        """Test OneOf fails with invalid number."""
        validator = OneOf([1, 2, 3])
        with pytest.raises(ValueError):
            validator(4)
    
    def test_not_empty_with_none(self):
        """Test NotEmpty with None-like falsy value."""
        validator = NotEmpty()
        with pytest.raises(ValueError):
            validator(None)
    
    def test_strip_with_tabs(self):
        """Test Strip removes tabs."""
        validator = Strip()
        assert validator("\t\thello\t\t") == "hello"
    
    def test_strip_with_newlines(self):
        """Test Strip removes newlines."""
        validator = Strip()
        assert validator("\n\nhello\n\n") == "hello"
    
    def test_combined_validators(self):
        """Test combining multiple validators."""
        field = FieldInfo(
            "email", str, SQLType.VARCHAR,
            validators=[Strip(), Lowercase(), Email()]
        )
        result = run_validators("  TEST@EXAMPLE.COM  ", field)
        assert result == "test@example.com"


class TestMultipleValidationErrors:
    """Tests for collecting multiple validation errors."""
    
    def test_multiple_missing_fields(self):
        """Test multiple missing required fields."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR),
            "email": FieldInfo("email", str, SQLType.VARCHAR),
            "age": FieldInfo("age", int, SQLType.INTEGER),
            "created_at": FieldInfo("created_at", datetime, SQLType.TIMESTAMP, auto_now_add=True),
            "updated_at": FieldInfo("updated_at", datetime, SQLType.TIMESTAMP, auto_now=True),
        }
        
        with pytest.raises(ValidationError) as exc:
            validate_data({}, fields)
        
        error_str = str(exc.value)
        assert "name" in error_str
        assert "email" in error_str
        assert "age" in error_str
    
    def test_validation_error_multiple_has_errors_list(self):
        """Test ValidationError.multiple has errors list."""
        errors = [
            ValidationError.required_field("name"),
            ValidationError.required_field("email"),
        ]
        combined = ValidationError.multiple(errors)
        
        assert len(combined.errors) == 2
    
    def test_validation_error_type_mismatch_factory(self):
        """Test ValidationError.type_mismatch factory."""
        error = ValidationError.type_mismatch("count", "int", "str", "abc")
        
        assert error.field == "count"
        assert error.expected == "int"
        assert error.got == "str"
        assert error.value == "abc"
    
    def test_validation_error_required_field_factory(self):
        """Test ValidationError.required_field factory."""
        error = ValidationError.required_field("email")
        
        assert error.field == "email"
        assert "required" in error.message
    
    def test_validation_error_empty_value_factory(self):
        """Test ValidationError.empty_value factory."""
        error = ValidationError.empty_value("name")
        
        assert error.field == "name"
        assert "empty" in error.message


class TestValidationEdgeCases:
    """Edge case tests for validation."""
    
    def test_validate_whitespace_string(self):
        """Test validating whitespace-only string."""
        field = FieldInfo("name", str, SQLType.VARCHAR)
        result = validate_type("   ", field)
        assert result == "   "
    
    def test_validate_newline_string(self):
        """Test validating string with newlines."""
        field = FieldInfo("content", str, SQLType.VARCHAR, max_length=1000)
        result = validate_type("line1\nline2\nline3", field)
        assert "\n" in result
    
    def test_validate_tab_string(self):
        """Test validating string with tabs."""
        field = FieldInfo("content", str, SQLType.VARCHAR, max_length=100)
        result = validate_type("col1\tcol2\tcol3", field)
        assert "\t" in result
    
    def test_validate_emoji_string(self):
        """Test validating string with emojis."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=100)
        result = validate_type("Hello 🎉🎊🎁", field)
        assert "🎉" in result
    
    def test_validate_very_large_int(self):
        """Test validating very large integer."""
        field = FieldInfo("big_num", int, SQLType.INTEGER)
        result = validate_type(10**18, field)
        assert result == 10**18
    
    def test_validate_very_small_int(self):
        """Test validating very negative integer."""
        field = FieldInfo("neg_num", int, SQLType.INTEGER)
        result = validate_type(-10**18, field)
        assert result == -10**18
    
    def test_validate_float_infinity(self):
        """Test validating float infinity."""
        field = FieldInfo("inf", float, SQLType.REAL)
        result = validate_type(float('inf'), field)
        assert result == float('inf')
    
    def test_validate_float_nan(self):
        """Test validating float NaN."""
        import math
        field = FieldInfo("nan", float, SQLType.REAL)
        result = validate_type(float('nan'), field)
        assert math.isnan(result)
    
    def test_validate_deeply_nested_dict(self):
        """Test validating deeply nested dict."""
        field = FieldInfo("nested", dict, SQLType.JSON)
        data = {"a": {"b": {"c": {"d": {"e": "value"}}}}}
        result = validate_type(data, field)
        assert result["a"]["b"]["c"]["d"]["e"] == "value"
    
    def test_validate_list_of_mixed_types(self):
        """Test validating list with mixed types."""
        field = FieldInfo("mixed", list, SQLType.JSON)
        data = [1, "two", 3.0, True, None]
        result = validate_type(data, field)
        assert result == [1, "two", 3.0, True, None]
    
    def test_validate_empty_json_string(self):
        """Test validating empty JSON objects/arrays from strings."""
        dict_field = FieldInfo("obj", dict, SQLType.JSON)
        result = validate_type("{}", dict_field)
        assert result == {}
        
        list_field = FieldInfo("arr", list, SQLType.JSON)
        result = validate_type("[]", list_field)
        assert result == []


class TestValidatorCombinations:
    """Tests for combining multiple validators."""
    
    def test_strip_then_min_length(self):
        """Test strip + min_length validators."""
        field = FieldInfo(
            "name", str, SQLType.VARCHAR,
            validators=[Strip(), MinLength(3)]
        )
        
        # Whitespace is stripped first, then length checked
        with pytest.raises(ValidationError):
            validate_field("  ab  ", field)  # After strip: "ab" (2 chars)
    
    def test_lowercase_then_email(self):
        """Test lowercase + email validators."""
        field = FieldInfo(
            "email", str, SQLType.VARCHAR,
            validators=[Lowercase(), Email()]
        )
        
        result = validate_field("TEST@EXAMPLE.COM", field)
        assert result == "test@example.com"
    
    def test_min_max_length_together(self):
        """Test min and max length together."""
        field = FieldInfo(
            "code", str, SQLType.VARCHAR,
            validators=[MinLength(3), MaxLength(10)]
        )
        
        # Valid
        assert validate_field("12345", field) == "12345"
        
        # Too short
        with pytest.raises(ValidationError):
            validate_field("ab", field)
        
        # Too long
        with pytest.raises(ValidationError):
            validate_field("12345678901", field)
    
    def test_min_max_value_together(self):
        """Test min and max value together."""
        field = FieldInfo(
            "percentage", int, SQLType.INTEGER,
            validators=[MinValue(0), MaxValue(100)]
        )
        
        # Valid
        assert validate_field(50, field) == 50
        
        # Too low
        with pytest.raises(ValidationError):
            validate_field(-1, field)
        
        # Too high
        with pytest.raises(ValidationError):
            validate_field(101, field)


class TestValidationMessages:
    """Tests for validation error messages."""
    
    def test_type_error_message_format(self):
        """Test type error message has correct format."""
        field = FieldInfo("age", int, SQLType.INTEGER)
        with pytest.raises(ValidationError) as exc:
            validate_type("not_a_number", field)
        
        msg = str(exc.value)
        assert "age" in msg
        assert "int" in msg
    
    def test_min_length_error_message(self):
        """Test min length error message."""
        validator = MinLength(5)
        with pytest.raises(ValueError) as exc:
            validator("abc")
        
        assert "at least 5" in str(exc.value)
    
    def test_max_length_error_message(self):
        """Test max length error message."""
        validator = MaxLength(3)
        with pytest.raises(ValueError) as exc:
            validator("toolong")
        
        assert "at most 3" in str(exc.value)
    
    def test_one_of_error_shows_options(self):
        """Test one_of error shows available options."""
        validator = OneOf(["a", "b", "c"])
        with pytest.raises(ValueError) as exc:
            validator("d")
        
        msg = str(exc.value)
        assert "'a'" in msg
        assert "'b'" in msg
        assert "'c'" in msg

