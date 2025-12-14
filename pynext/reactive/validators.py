"""
PyNext Form Validators - Composable Validation Functions

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Validators are functions that check if a value is valid. Each validator:
- Takes configuration (e.g., min_length(5))
- Returns a validate function
- The validate function takes a value and returns:
  - None if valid
  - Error message string if invalid

This design allows composing validators and custom error messages.

=============================================================================
WHY THIS EXISTS (vs React)
=============================================================================

React form libraries (Formik, react-hook-form) have complex validation:
- Schema-based (Yup, Zod) - external dependencies, complex setup
- Or inline validation functions - scattered, hard to reuse

PyNext validators are:
- Simple functions (no schema DSL to learn)
- Composable (combine with `compose()`)
- Tree-shakeable (import only what you use)
- Type-safe (full type hints)

=============================================================================
HOW TO USE
=============================================================================

    from pynext.reactive.validators import required, min_length, email, compose
    
    # Single validator
    check = required("Email is required")
    error = check("")  # Returns "Email is required"
    error = check("a@b.com")  # Returns None (valid)
    
    # Multiple validators
    validators = [
        required("Email is required"),
        email("Must be a valid email"),
    ]
    
    # In a form
    form = create_form(
        initial={"email": ""},
        validators={"email": validators}
    )

=============================================================================
CUSTOM VALIDATORS
=============================================================================

Create your own validator:

    def password_strength(message: str = "Password too weak"):
        def validate(value):
            if len(value) < 8:
                return message
            if not any(c.isupper() for c in value):
                return message
            if not any(c.isdigit() for c in value):
                return message
            return None  # Valid
        return validate

=============================================================================
"""

from __future__ import annotations

import re
from typing import Any, Callable, List, Optional, Pattern, Union


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

# A validator function takes a value and returns None (valid) or error message
ValidatorFn = Callable[[Any], Optional[str]]

# A validator factory takes config and returns a ValidatorFn
ValidatorFactory = Callable[..., ValidatorFn]


# =============================================================================
# CORE VALIDATORS
# =============================================================================

def _mark_validator(fn: ValidatorFn, validator_type: str, args: List = None, message: str = None) -> ValidatorFn:
    """
    Mark a validator function with metadata for serialization.
    
    This allows validators to be serialized for hydration and
    reconstructed on the client.
    """
    fn._validator_type = validator_type
    fn._validator_args = args or []
    fn._validator_message = message
    return fn


def required(message: str = "This field is required") -> ValidatorFn:
    """
    Value must not be empty.
    
    Empty values:
    - None
    - Empty string ""
    - Empty list []
    - Empty dict {}
    - Whitespace-only strings (after strip)
    
    Args:
        message: Error message when validation fails
    
    Returns:
        Validator function
    
    Example:
        >>> check = required()
        >>> check("")
        'This field is required'
        >>> check("hello")
        None
    """
    def validate(value: Any) -> Optional[str]:
        if value is None:
            return message
        if isinstance(value, str) and value.strip() == "":
            return message
        if isinstance(value, (list, dict)) and len(value) == 0:
            return message
        return None
    
    return _mark_validator(validate, "required", [], message if message != "This field is required" else None)


def min_length(length: int, message: Optional[str] = None) -> ValidatorFn:
    """
    Value must have at least N characters.
    
    Works with strings and any object with __len__.
    
    Args:
        length: Minimum length required
        message: Custom error message (optional)
    
    Returns:
        Validator function
    
    Example:
        >>> check = min_length(3)
        >>> check("ab")
        'Must be at least 3 characters'
        >>> check("abc")
        None
    """
    default_msg = f"Must be at least {length} characters"
    
    def validate(value: Any) -> Optional[str]:
        if value is None:
            return message or default_msg
        try:
            if len(str(value)) < length:
                return message or default_msg
        except TypeError:
            return message or default_msg
        return None
    
    return _mark_validator(validate, "min_length", [length], message)


def max_length(length: int, message: Optional[str] = None) -> ValidatorFn:
    """
    Value must have at most N characters.
    
    Works with strings and any object with __len__.
    
    Args:
        length: Maximum length allowed
        message: Custom error message (optional)
    
    Returns:
        Validator function
    
    Example:
        >>> check = max_length(10)
        >>> check("hello")
        None
        >>> check("hello world!")
        'Must be at most 10 characters'
    """
    default_msg = f"Must be at most {length} characters"
    
    def validate(value: Any) -> Optional[str]:
        if value is None:
            return None  # max_length doesn't require a value
        try:
            if len(str(value)) > length:
                return message or default_msg
        except TypeError:
            pass
        return None
    
    return _mark_validator(validate, "max_length", [length], message)


def email(message: str = "Must be a valid email address") -> ValidatorFn:
    """
    Value must be a valid email address.
    
    Uses a simple regex that catches most cases without being overly strict.
    For strict validation, use pattern() with a custom regex.
    
    Args:
        message: Error message when validation fails
    
    Returns:
        Validator function
    
    Example:
        >>> check = email()
        >>> check("not-an-email")
        'Must be a valid email address'
        >>> check("user@example.com")
        None
    """
    # Simple email regex - catches most cases
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def validate(value: Any) -> Optional[str]:
        if value is None or value == "":
            return None  # email() doesn't require a value - use with required()
        if not isinstance(value, str):
            return message
        if not email_pattern.match(value):
            return message
        return None
    
    return _mark_validator(validate, "email", [], message if message != "Must be a valid email address" else None)


def pattern(regex: Union[str, Pattern], message: str = "Invalid format") -> ValidatorFn:
    """
    Value must match a regex pattern.
    
    Args:
        regex: Regular expression string or compiled pattern
        message: Error message when validation fails
    
    Returns:
        Validator function
    
    Example:
        >>> check = pattern(r'^[A-Z]{3}$', "Must be 3 uppercase letters")
        >>> check("abc")
        'Must be 3 uppercase letters'
        >>> check("ABC")
        None
    """
    if isinstance(regex, str):
        compiled = re.compile(regex)
    else:
        compiled = regex
    
    def validate(value: Any) -> Optional[str]:
        if value is None or value == "":
            return None  # pattern() doesn't require a value
        if not isinstance(value, str):
            return message
        if not compiled.match(value):
            return message
        return None
    
    # For pattern, store the regex as a string for serialization
    regex_str = regex if isinstance(regex, str) else regex.pattern
    return _mark_validator(validate, "pattern", [regex_str], message if message != "Invalid format" else None)


def min_value(minimum: Union[int, float], message: Optional[str] = None) -> ValidatorFn:
    """
    Numeric value must be at least N.
    
    Args:
        minimum: Minimum value allowed
        message: Custom error message (optional)
    
    Returns:
        Validator function
    
    Example:
        >>> check = min_value(0)
        >>> check(-1)
        'Must be at least 0'
        >>> check(5)
        None
    """
    default_msg = f"Must be at least {minimum}"
    
    def validate(value: Any) -> Optional[str]:
        if value is None or value == "":
            return None  # min_value() doesn't require a value
        try:
            num_value = float(value)
            if num_value < minimum:
                return message or default_msg
        except (TypeError, ValueError):
            return message or default_msg
        return None
    
    return _mark_validator(validate, "min_value", [minimum], message)


def max_value(maximum: Union[int, float], message: Optional[str] = None) -> ValidatorFn:
    """
    Numeric value must be at most N.
    
    Args:
        maximum: Maximum value allowed
        message: Custom error message (optional)
    
    Returns:
        Validator function
    
    Example:
        >>> check = max_value(100)
        >>> check(150)
        'Must be at most 100'
        >>> check(50)
        None
    """
    default_msg = f"Must be at most {maximum}"
    
    def validate(value: Any) -> Optional[str]:
        if value is None or value == "":
            return None  # max_value() doesn't require a value
        try:
            num_value = float(value)
            if num_value > maximum:
                return message or default_msg
        except (TypeError, ValueError):
            return message or default_msg
        return None
    
    return _mark_validator(validate, "max_value", [maximum], message)


def one_of(options: List[Any], message: Optional[str] = None) -> ValidatorFn:
    """
    Value must be one of the allowed options.
    
    Args:
        options: List of allowed values
        message: Custom error message (optional)
    
    Returns:
        Validator function
    
    Example:
        >>> check = one_of(["low", "medium", "high"])
        >>> check("invalid")
        'Must be one of: low, medium, high'
        >>> check("medium")
        None
    """
    options_str = ", ".join(str(o) for o in options)
    default_msg = f"Must be one of: {options_str}"
    
    def validate(value: Any) -> Optional[str]:
        if value is None or value == "":
            return None  # one_of() doesn't require a value
        if value not in options:
            return message or default_msg
        return None
    
    return _mark_validator(validate, "one_of", [options], message)


def url(message: str = "Must be a valid URL") -> ValidatorFn:
    """
    Value must be a valid URL.
    
    Args:
        message: Error message when validation fails
    
    Returns:
        Validator function
    
    Example:
        >>> check = url()
        >>> check("not-a-url")
        'Must be a valid URL'
        >>> check("https://example.com")
        None
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    def validate(value: Any) -> Optional[str]:
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            return message
        if not url_pattern.match(value):
            return message
        return None
    
    return _mark_validator(validate, "url", [], message if message != "Must be a valid URL" else None)


def integer(message: str = "Must be a whole number") -> ValidatorFn:
    """
    Value must be an integer (or string representing an integer).
    
    Args:
        message: Error message when validation fails
    
    Returns:
        Validator function
    
    Example:
        >>> check = integer()
        >>> check("3.14")
        'Must be a whole number'
        >>> check("42")
        None
    """
    def validate(value: Any) -> Optional[str]:
        if value is None or value == "":
            return None
        try:
            int(str(value))
            return None
        except (TypeError, ValueError):
            return message
    
    return _mark_validator(validate, "integer", [], message if message != "Must be a whole number" else None)


def number(message: str = "Must be a number") -> ValidatorFn:
    """
    Value must be a number (int or float).
    
    Args:
        message: Error message when validation fails
    
    Returns:
        Validator function
    
    Example:
        >>> check = number()
        >>> check("abc")
        'Must be a number'
        >>> check("3.14")
        None
    """
    def validate(value: Any) -> Optional[str]:
        if value is None or value == "":
            return None
        try:
            float(str(value))
            return None
        except (TypeError, ValueError):
            return message
    
    return _mark_validator(validate, "number", [], message if message != "Must be a number" else None)


def equals(other_value: Any, message: Optional[str] = None) -> ValidatorFn:
    """
    Value must equal another value.
    
    Useful for password confirmation fields.
    
    Args:
        other_value: Value to compare against (can be a callable)
        message: Custom error message (optional)
    
    Returns:
        Validator function
    
    Example:
        >>> check = equals("expected")
        >>> check("different")
        'Values do not match'
        >>> check("expected")
        None
        
        # With callable (for comparing to another field):
        >>> password = signal("secret")
        >>> check = equals(password)
        >>> check("wrong")
        'Values do not match'
    """
    default_msg = "Values do not match"
    
    def validate(value: Any) -> Optional[str]:
        # Support callable for comparing to signals
        compare_to = other_value() if callable(other_value) else other_value
        if value != compare_to:
            return message or default_msg
        return None
    
    # Note: equals with callable can't be serialized for hydration
    return _mark_validator(validate, "equals", [other_value if not callable(other_value) else None], message)


def length(exact: int, message: Optional[str] = None) -> ValidatorFn:
    """
    Value must be exactly N characters.
    
    Args:
        exact: Required length
        message: Custom error message (optional)
    
    Returns:
        Validator function
    
    Example:
        >>> check = length(5)
        >>> check("abc")
        'Must be exactly 5 characters'
        >>> check("hello")
        None
    """
    default_msg = f"Must be exactly {exact} characters"
    
    def validate(value: Any) -> Optional[str]:
        if value is None:
            return message or default_msg
        try:
            if len(str(value)) != exact:
                return message or default_msg
        except TypeError:
            return message or default_msg
        return None
    
    return _mark_validator(validate, "length", [exact], message)


# =============================================================================
# COMPOSITION UTILITIES
# =============================================================================

def compose(*validators: ValidatorFn) -> ValidatorFn:
    """
    Combine multiple validators into one.
    
    Returns the first error encountered, or None if all pass.
    
    Args:
        *validators: Validator functions to combine
    
    Returns:
        Combined validator function
    
    Example:
        >>> check = compose(
        ...     required("Name is required"),
        ...     min_length(2, "Name too short"),
        ...     max_length(50, "Name too long"),
        ... )
        >>> check("")
        'Name is required'
        >>> check("A")
        'Name too short'
        >>> check("Alice")
        None
    """
    def validate(value: Any) -> Optional[str]:
        for validator in validators:
            error = validator(value)
            if error is not None:
                return error
        return None
    return validate


def when(condition: Callable[[], bool], *validators: ValidatorFn) -> ValidatorFn:
    """
    Only run validators when a condition is true.
    
    Useful for conditional validation based on other fields.
    
    Args:
        condition: Function that returns True when validation should run
        *validators: Validators to run when condition is True
    
    Returns:
        Conditional validator function
    
    Example:
        >>> is_premium = signal(False)
        >>> check = when(is_premium, required("Premium users need a company name"))
        >>> check("")
        None  # Not premium, so no validation
        >>> is_premium.set(True)
        >>> check("")
        'Premium users need a company name'
    """
    def validate(value: Any) -> Optional[str]:
        if condition():
            return compose(*validators)(value)
        return None
    return validate


def validate_all(value: Any, validators: List[ValidatorFn]) -> List[str]:
    """
    Run all validators and return all errors.
    
    Unlike compose(), this doesn't short-circuit - it returns all errors.
    
    Args:
        value: Value to validate
        validators: List of validators to run
    
    Returns:
        List of error messages (empty if valid)
    
    Example:
        >>> errors = validate_all("", [
        ...     required("Required"),
        ...     min_length(3, "Too short"),
        ... ])
        >>> errors
        ['Required', 'Too short']
    """
    errors = []
    for validator in validators:
        error = validator(value)
        if error is not None:
            errors.append(error)
    return errors


def run_validators(validators: Union[ValidatorFn, List[ValidatorFn], None], value: Any) -> Optional[str]:
    """
    Run a validator or list of validators on a value.
    
    Convenience function that handles both single validators and lists.
    Returns the first error or None.
    
    Args:
        validators: Single validator or list of validators, or None
        value: Value to validate
    
    Returns:
        First error message, or None if valid
    """
    if validators is None:
        return None
    
    if callable(validators) and not isinstance(validators, list):
        # Single validator
        return validators(value)
    else:
        # List of validators
        for validator in validators:
            error = validator(value)
            if error is not None:
                return error
        return None


# =============================================================================
# ASYNC VALIDATORS (for server-side validation)
# =============================================================================

async def async_validate_all(
    value: Any, 
    validators: List[Union[ValidatorFn, Callable[[Any], Any]]]
) -> List[str]:
    """
    Run validators including async ones.
    
    Args:
        value: Value to validate
        validators: List of sync or async validators
    
    Returns:
        List of error messages (empty if valid)
    
    Example:
        >>> async def check_unique_email(email):
        ...     exists = await db.users.exists(email=email)
        ...     return "Email already taken" if exists else None
        >>> 
        >>> errors = await async_validate_all("test@example.com", [
        ...     required(),
        ...     email(),
        ...     check_unique_email,
        ... ])
    """
    import asyncio
    
    errors = []
    for validator in validators:
        result = validator(value)
        if asyncio.iscoroutine(result):
            result = await result
        if result is not None:
            errors.append(result)
    return errors


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Type definitions
    "ValidatorFn",
    "ValidatorFactory",
    
    # Core validators
    "required",
    "min_length",
    "max_length",
    "email",
    "pattern",
    "min_value",
    "max_value",
    "one_of",
    "url",
    "integer",
    "number",
    "equals",
    "length",
    
    # Composition
    "compose",
    "when",
    "validate_all",
    "run_validators",
    "async_validate_all",
]

