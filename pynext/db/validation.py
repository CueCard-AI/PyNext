"""
PyNext Database Validation System.

Pydantic-style validation with clear, helpful error messages.
Validates data on create and update operations automatically.

Design: Catch errors early with messages that tell you exactly what's wrong.
"""

from __future__ import annotations

from datetime import datetime, date, time
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Type, get_origin, get_args, Union
from uuid import UUID

from pynext.db.exceptions import ValidationError
from pynext.db.fields import FieldInfo


def validate_type(value: Any, field: FieldInfo) -> Any:
    """
    Validate and coerce a value to the expected type.
    
    Type coercion rules:
    - str: Any value -> str (via str())
    - int: "5" -> 5, 5.0 -> 5, but "abc" raises error
    - float: "5.5" -> 5.5, 5 -> 5.0
    - bool: 1/0, "true"/"false", "yes"/"no"
    - datetime: ISO string -> datetime
    - list/dict: JSON string -> list/dict
    
    Raises:
        ValidationError: If value cannot be coerced to expected type
    """
    if value is None:
        if field.nullable:
            return None
        raise ValidationError.required_field(field.name)
    
    python_type = field.python_type
    
    # Already correct type
    if isinstance(value, python_type):
        return value
    
    # String coercion
    if python_type is str:
        if isinstance(value, (int, float, bool)):
            return str(value)
        if hasattr(value, "__str__"):
            return str(value)
        raise ValidationError.type_mismatch(
            field.name, "str", type(value).__name__, value
        )
    
    # Integer coercion
    if python_type is int:
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            raise ValidationError(
                f"{field.name}: cannot convert float {value} to int (has decimal part)",
                field=field.name,
                value=value,
            )
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                raise ValidationError.type_mismatch(
                    field.name, "int", f"str '{value}'", value
                )
        if isinstance(value, bool):
            return int(value)
        raise ValidationError.type_mismatch(
            field.name, "int", type(value).__name__, value
        )
    
    # Float coercion
    if python_type is float:
        if isinstance(value, (int, Decimal)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                raise ValidationError.type_mismatch(
                    field.name, "float", f"str '{value}'", value
                )
        raise ValidationError.type_mismatch(
            field.name, "float", type(value).__name__, value
        )
    
    # Boolean coercion
    if python_type is bool:
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            lower = value.lower()
            if lower in ("true", "yes", "1", "on"):
                return True
            if lower in ("false", "no", "0", "off"):
                return False
            raise ValidationError(
                f"{field.name}: cannot convert '{value}' to bool (use true/false/yes/no/1/0)",
                field=field.name,
                value=value,
            )
        raise ValidationError.type_mismatch(
            field.name, "bool", type(value).__name__, value
        )
    
    # Datetime coercion
    if python_type is datetime:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValidationError(
                    f"{field.name}: invalid datetime format '{value}' (use ISO format: YYYY-MM-DDTHH:MM:SS)",
                    field=field.name,
                    value=value,
                )
        if isinstance(value, date) and not isinstance(value, datetime):
            return datetime.combine(value, datetime.min.time())
        raise ValidationError.type_mismatch(
            field.name, "datetime", type(value).__name__, value
        )
    
    # Date coercion
    if python_type is date:
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValidationError(
                    f"{field.name}: invalid date format '{value}' (use ISO format: YYYY-MM-DD)",
                    field=field.name,
                    value=value,
                )
        if isinstance(value, datetime):
            return value.date()
        raise ValidationError.type_mismatch(
            field.name, "date", type(value).__name__, value
        )
    
    # Time coercion
    if python_type is time:
        if isinstance(value, str):
            try:
                return time.fromisoformat(value)
            except ValueError:
                raise ValidationError(
                    f"{field.name}: invalid time format '{value}' (use ISO format: HH:MM:SS)",
                    field=field.name,
                    value=value,
                )
        if isinstance(value, datetime):
            return value.time()
        raise ValidationError.type_mismatch(
            field.name, "time", type(value).__name__, value
        )
    
    # UUID coercion
    if python_type is UUID:
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                raise ValidationError(
                    f"{field.name}: invalid UUID format '{value}'",
                    field=field.name,
                    value=value,
                )
        raise ValidationError.type_mismatch(
            field.name, "UUID", type(value).__name__, value
        )
    
    # List coercion
    if python_type is list:
        if isinstance(value, (tuple, set)):
            return list(value)
        if isinstance(value, str):
            import json
            try:
                result = json.loads(value)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass
            raise ValidationError(
                f"{field.name}: cannot parse '{value}' as list (use JSON format: [1, 2, 3])",
                field=field.name,
                value=value,
            )
        raise ValidationError.type_mismatch(
            field.name, "list", type(value).__name__, value
        )
    
    # Dict coercion
    if python_type is dict:
        if isinstance(value, str):
            import json
            try:
                result = json.loads(value)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass
            raise ValidationError(
                f"{field.name}: cannot parse '{value}' as dict (use JSON format: {{\"key\": \"value\"}})",
                field=field.name,
                value=value,
            )
        raise ValidationError.type_mismatch(
            field.name, "dict", type(value).__name__, value
        )
    
    # Decimal coercion
    if python_type is Decimal:
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            try:
                return Decimal(value)
            except:
                raise ValidationError(
                    f"{field.name}: invalid decimal format '{value}'",
                    field=field.name,
                    value=value,
                )
        raise ValidationError.type_mismatch(
            field.name, "Decimal", type(value).__name__, value
        )
    
    # Unknown type - try direct conversion
    try:
        return python_type(value)
    except (TypeError, ValueError) as e:
        raise ValidationError.type_mismatch(
            field.name, python_type.__name__, type(value).__name__, value
        )


def validate_constraints(value: Any, field: FieldInfo) -> None:
    """
    Validate field constraints (max_length, etc.).
    
    Raises:
        ValidationError: If constraint is violated
    """
    if value is None:
        return
    
    # String max length
    if field.max_length is not None and isinstance(value, str):
        if len(value) > field.max_length:
            raise ValidationError(
                f"{field.name}: exceeds max length {field.max_length} (got {len(value)} chars)",
                field=field.name,
                value=value,
            )
    
    # Empty string check (for non-nullable strings)
    if not field.nullable and isinstance(value, str) and value == "":
        raise ValidationError.empty_value(field.name)


def run_validators(value: Any, field: FieldInfo) -> Any:
    """
    Run custom validators on a value.
    
    Each validator can:
    - Return the value (optionally transformed)
    - Raise ValueError with message
    
    Raises:
        ValidationError: If any validator fails
    """
    for validator in field.validators:
        try:
            value = validator(value)
        except ValueError as e:
            raise ValidationError(
                f"{field.name}: {str(e)}",
                field=field.name,
                value=value,
            )
    return value


def validate_field(value: Any, field: FieldInfo) -> Any:
    """
    Full validation pipeline for a single field.
    
    Pipeline:
    1. Type validation/coercion
    2. Constraint validation
    3. Custom validators
    
    Returns:
        The validated (and possibly coerced) value
        
    Raises:
        ValidationError: If any validation step fails
    """
    # 1. Type validation
    value = validate_type(value, field)
    
    # 2. Constraint validation
    validate_constraints(value, field)
    
    # 3. Custom validators
    value = run_validators(value, field)
    
    return value


def validate_data(
    data: Dict[str, Any],
    fields: Dict[str, FieldInfo],
    *,
    partial: bool = False,
    exclude_auto: bool = True,
) -> Dict[str, Any]:
    """
    Validate a full data dict against field definitions.
    
    Args:
        data: Data to validate
        fields: Field definitions
        partial: If True, missing fields are OK (for updates)
        exclude_auto: If True, skip auto-generated fields (id, created_at, updated_at)
    
    Returns:
        Validated data dict with coerced values
        
    Raises:
        ValidationError: If any field fails validation (includes all errors)
    """
    auto_fields = {"id", "created_at", "updated_at"}
    errors: List[ValidationError] = []
    validated: Dict[str, Any] = {}
    
    for name, field in fields.items():
        # Skip auto-generated fields if requested
        if exclude_auto and name in auto_fields:
            if name in data:
                validated[name] = data[name]
            continue
        
        # Check if field is present
        if name not in data:
            if partial:
                continue
            if field.has_default:
                validated[name] = field.get_default()
                continue
            if field.nullable:
                validated[name] = None
                continue
            if not field.primary_key and not field.auto_now and not field.auto_now_add:
                errors.append(ValidationError.required_field(name))
            continue
        
        # Validate the value
        try:
            validated[name] = validate_field(data[name], field)
        except ValidationError as e:
            errors.append(e)
    
    # Check for unknown fields
    known_fields = set(fields.keys())
    unknown_fields = set(data.keys()) - known_fields
    for unknown in unknown_fields:
        errors.append(ValidationError(
            f"{unknown}: unknown field",
            field=unknown,
        ))
    
    if errors:
        if len(errors) == 1:
            raise errors[0]
        raise ValidationError.multiple(errors)
    
    return validated


class Validator:
    """
    Base class for custom validators.
    
    Subclass this to create reusable validators:
    
        class EmailValidator(Validator):
            def __call__(self, value: str) -> str:
                if "@" not in value:
                    raise ValueError("must contain @")
                return value.lower()
        
        class User(Table):
            email: str = Field(validators=[EmailValidator()])
    """
    
    def __call__(self, value: Any) -> Any:
        """Validate and optionally transform the value."""
        return value


class MinLength(Validator):
    """Validate minimum string length."""
    
    def __init__(self, min_length: int):
        self.min_length = min_length
    
    def __call__(self, value: str) -> str:
        if len(value) < self.min_length:
            raise ValueError(f"must be at least {self.min_length} characters")
        return value


class MaxLength(Validator):
    """Validate maximum string length."""
    
    def __init__(self, max_length: int):
        self.max_length = max_length
    
    def __call__(self, value: str) -> str:
        if len(value) > self.max_length:
            raise ValueError(f"must be at most {self.max_length} characters")
        return value


class MinValue(Validator):
    """Validate minimum numeric value."""
    
    def __init__(self, min_value: float):
        self.min_value = min_value
    
    def __call__(self, value: float) -> float:
        if value < self.min_value:
            raise ValueError(f"must be at least {self.min_value}")
        return value


class MaxValue(Validator):
    """Validate maximum numeric value."""
    
    def __init__(self, max_value: float):
        self.max_value = max_value
    
    def __call__(self, value: float) -> float:
        if value > self.max_value:
            raise ValueError(f"must be at most {self.max_value}")
        return value


class Regex(Validator):
    """Validate string against regex pattern."""
    
    def __init__(self, pattern: str, message: Optional[str] = None):
        import re
        self.pattern = re.compile(pattern)
        self.message = message or f"must match pattern {pattern}"
    
    def __call__(self, value: str) -> str:
        if not self.pattern.match(value):
            raise ValueError(self.message)
        return value


class Email(Validator):
    """Validate email format."""
    
    def __call__(self, value: str) -> str:
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("must be a valid email address")
        return value.lower()


class URL(Validator):
    """Validate URL format."""
    
    def __call__(self, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("must be a valid URL (start with http:// or https://)")
        return value


class OneOf(Validator):
    """Validate value is one of allowed options."""
    
    def __init__(self, options: List[Any]):
        self.options = options
    
    def __call__(self, value: Any) -> Any:
        if value not in self.options:
            options_str = ", ".join(repr(o) for o in self.options)
            raise ValueError(f"must be one of: {options_str}")
        return value


class NotEmpty(Validator):
    """Validate value is not empty."""
    
    def __call__(self, value: Any) -> Any:
        if not value:
            raise ValueError("cannot be empty")
        return value


class Lowercase(Validator):
    """Transform string to lowercase."""
    
    def __call__(self, value: str) -> str:
        return value.lower()


class Uppercase(Validator):
    """Transform string to uppercase."""
    
    def __call__(self, value: str) -> str:
        return value.upper()


class Strip(Validator):
    """Strip whitespace from string."""
    
    def __call__(self, value: str) -> str:
        return value.strip()

