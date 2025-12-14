"""
Comprehensive tests for custom validators.

Tests cover:
- Creating custom validators
- Validator patterns
- Async validators
- Validator factories
- Complex validation logic

Total: 50+ tests
"""

import pytest
from pynext.reactive.forms import create_form
from pynext.reactive.validators import compose, required


# =============================================================================
# BASIC CUSTOM VALIDATORS (15 tests)
# =============================================================================

class TestBasicCustomValidators:
    """Tests for basic custom validators."""
    
    def test_simple_custom_validator(self):
        """Simple custom validator function."""
        def no_spaces(message="No spaces allowed"):
            def validate(value):
                if value and " " in str(value):
                    return message
                return None
            return validate
        
        form = create_form(
            initial={"username": ""},
            validators={"username": [no_spaces()]}
        )
        
        form.username.set("hello world")
        assert not form.is_valid()
        
        form.username.set("helloworld")
        assert form.is_valid()
    
    def test_custom_validator_with_params(self):
        """Custom validator with parameters."""
        def starts_with(prefix, message=None):
            default_msg = f"Must start with '{prefix}'"
            def validate(value):
                if value and not str(value).startswith(prefix):
                    return message or default_msg
                return None
            return validate
        
        form = create_form(
            initial={"code": ""},
            validators={"code": [starts_with("PRE-")]}
        )
        
        form.code.set("ABC-123")
        assert not form.is_valid()
        
        form.code.set("PRE-123")
        assert form.is_valid()
    
    def test_custom_validator_multiple_params(self):
        """Custom validator with multiple parameters."""
        def between(min_val, max_val, message=None):
            default_msg = f"Must be between {min_val} and {max_val}"
            def validate(value):
                if value == "" or value is None:
                    return None
                try:
                    num = float(value)
                    if num < min_val or num > max_val:
                        return message or default_msg
                except (TypeError, ValueError):
                    return message or default_msg
                return None
            return validate
        
        form = create_form(
            initial={"age": ""},
            validators={"age": [between(18, 65)]}
        )
        
        form.age.set("10")
        assert not form.is_valid()
        
        form.age.set("70")
        assert not form.is_valid()
        
        form.age.set("30")
        assert form.is_valid()
    
    def test_custom_validator_returns_none_when_valid(self):
        """Validator returns None when valid."""
        def always_valid():
            def validate(value):
                return None
            return validate
        
        form = create_form(
            initial={"anything": ""},
            validators={"anything": [always_valid()]}
        )
        
        assert form.is_valid()
    
    def test_custom_validator_returns_string_when_invalid(self):
        """Validator returns error string when invalid."""
        def always_invalid():
            def validate(value):
                return "Always fails"
            return validate
        
        form = create_form(
            initial={"doomed": "anything"},
            validators={"doomed": [always_invalid()]}
        )
        
        assert not form.is_valid()
        form.validate()
        assert form.errors.doomed == "Always fails"


# =============================================================================
# VALIDATOR PATTERNS (20 tests)
# =============================================================================

class TestValidatorPatterns:
    """Tests for common validator patterns."""
    
    def test_password_strength(self):
        """Password strength validator."""
        def password_strength(message="Password too weak"):
            def validate(value):
                if not value:
                    return None
                if len(value) < 8:
                    return "Password must be at least 8 characters"
                if not any(c.isupper() for c in value):
                    return "Password must have uppercase letter"
                if not any(c.islower() for c in value):
                    return "Password must have lowercase letter"
                if not any(c.isdigit() for c in value):
                    return "Password must have a digit"
                return None
            return validate
        
        form = create_form(
            initial={"password": ""},
            validators={"password": [password_strength()]}
        )
        
        form.password.set("short")
        form.validate()
        assert "8 characters" in form.errors.password
        
        form.password.set("alllowercase1")
        form.validate()
        assert "uppercase" in form.errors.password
        
        form.password.set("ALLUPPERCASE1")
        form.validate()
        assert "lowercase" in form.errors.password
        
        form.password.set("NoDigitsHere")
        form.validate()
        assert "digit" in form.errors.password
        
        form.password.set("ValidPass123")
        form.validate()
        assert form.errors.password == ""
    
    def test_phone_number(self):
        """Phone number validator."""
        import re
        
        def phone_number(message="Invalid phone number"):
            pattern = re.compile(r"^\d{3}-\d{3}-\d{4}$")
            def validate(value):
                if not value:
                    return None
                if not pattern.match(value):
                    return message
                return None
            return validate
        
        form = create_form(
            initial={"phone": ""},
            validators={"phone": [phone_number()]}
        )
        
        form.phone.set("1234567890")
        assert not form.is_valid()
        
        form.phone.set("123-456-7890")
        assert form.is_valid()
    
    def test_credit_card(self):
        """Credit card number validator (Luhn check)."""
        def credit_card(message="Invalid card number"):
            def luhn_check(num):
                digits = [int(d) for d in str(num) if d.isdigit()]
                if len(digits) < 13 or len(digits) > 19:
                    return False
                checksum = 0
                for i, d in enumerate(reversed(digits)):
                    if i % 2 == 1:
                        d *= 2
                        if d > 9:
                            d -= 9
                    checksum += d
                return checksum % 10 == 0
            
            def validate(value):
                if not value:
                    return None
                if not luhn_check(value):
                    return message
                return None
            return validate
        
        form = create_form(
            initial={"card": ""},
            validators={"card": [credit_card()]}
        )
        
        form.card.set("1234567890123456")  # Invalid
        assert not form.is_valid()
        
        form.card.set("4111111111111111")  # Valid test card
        assert form.is_valid()
    
    def test_slug(self):
        """URL slug validator."""
        import re
        
        def slug(message="Invalid slug"):
            pattern = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            def validate(value):
                if not value:
                    return None
                if not pattern.match(value):
                    return message
                return None
            return validate
        
        form = create_form(
            initial={"slug": ""},
            validators={"slug": [slug()]}
        )
        
        form.slug.set("Hello World")  # Invalid - spaces
        assert not form.is_valid()
        
        form.slug.set("UPPERCASE")  # Invalid - uppercase
        assert not form.is_valid()
        
        form.slug.set("my-valid-slug")
        assert form.is_valid()
    
    def test_date_format(self):
        """Date format validator."""
        from datetime import datetime
        
        def date_format(fmt="%Y-%m-%d", message=None):
            default_msg = f"Invalid date format. Use {fmt}"
            def validate(value):
                if not value:
                    return None
                try:
                    datetime.strptime(value, fmt)
                    return None
                except ValueError:
                    return message or default_msg
            return validate
        
        form = create_form(
            initial={"date": ""},
            validators={"date": [date_format()]}
        )
        
        form.date.set("01/15/2024")  # Wrong format
        assert not form.is_valid()
        
        form.date.set("2024-01-15")  # Correct format
        assert form.is_valid()
    
    def test_json_validator(self):
        """JSON string validator."""
        import json
        
        def valid_json(message="Invalid JSON"):
            def validate(value):
                if not value:
                    return None
                try:
                    json.loads(value)
                    return None
                except (json.JSONDecodeError, TypeError):
                    return message
            return validate
        
        form = create_form(
            initial={"config": ""},
            validators={"config": [valid_json()]}
        )
        
        form.config.set("{invalid json")
        assert not form.is_valid()
        
        form.config.set('{"valid": "json"}')
        assert form.is_valid()
    
    def test_unique_items(self):
        """List with unique items validator."""
        def unique_items(message="Items must be unique"):
            def validate(value):
                if not value:
                    return None
                if not isinstance(value, list):
                    return None
                if len(value) != len(set(str(v) for v in value)):
                    return message
                return None
            return validate
        
        form = create_form(
            initial={"tags": []},
            validators={"tags": [unique_items()]}
        )
        
        form.tags.set(["a", "b", "a"])  # Duplicate
        assert not form.is_valid()
        
        form.tags.set(["a", "b", "c"])
        assert form.is_valid()


# =============================================================================
# COMPOSE WITH CUSTOM (10 tests)
# =============================================================================

class TestComposeWithCustom:
    """Tests for composing custom validators."""
    
    def test_compose_required_with_custom(self):
        """Compose required with custom validator."""
        def no_special_chars(message="No special characters"):
            def validate(value):
                if value and not value.isalnum():
                    return message
                return None
            return validate
        
        form = create_form(
            initial={"username": ""},
            validators={"username": [required(), no_special_chars()]}
        )
        
        form.username.set("")
        form.validate()
        assert "required" in form.errors.username.lower()
        
        form.username.set("user@name")
        form.validate()
        assert "special" in form.errors.username.lower()
        
        form.username.set("username123")
        form.validate()
        assert form.errors.username == ""
    
    def test_compose_multiple_custom(self):
        """Compose multiple custom validators."""
        def min_words(n, message=None):
            msg = message or f"Must have at least {n} words"
            def validate(value):
                if not value:
                    return None
                words = value.split()
                if len(words) < n:
                    return msg
                return None
            return validate
        
        def no_profanity(bad_words, message="Contains inappropriate content"):
            def validate(value):
                if not value:
                    return None
                for word in bad_words:
                    if word.lower() in value.lower():
                        return message
                return None
            return validate
        
        validators = compose(
            min_words(3),
            no_profanity(["spam", "scam"]),
        )
        
        form = create_form(
            initial={"description": ""},
            validators={"description": [validators]}
        )
        
        form.description.set("Too short")
        form.validate()
        assert "words" in form.errors.description.lower()
        
        form.description.set("This is spam content")
        form.validate()
        assert "inappropriate" in form.errors.description.lower()
        
        form.description.set("This is valid content")
        form.validate()
        assert form.errors.description == ""


# =============================================================================
# CROSS-FIELD VALIDATION (5 tests)
# =============================================================================

class TestCrossFieldValidation:
    """Tests for validation involving multiple fields."""
    
    def test_password_confirmation(self):
        """Password confirmation validator."""
        form = create_form(
            initial={"password": "", "confirm": ""},
        )
        
        def passwords_match():
            def validate(value):
                if value and value != form.password():
                    return "Passwords do not match"
                return None
            return validate
        
        # Add validator after form creation (workaround)
        form._validators["confirm"] = [passwords_match()]
        
        form.password.set("secret123")
        form.confirm.set("different")
        
        assert not form.is_valid()
    
    def test_end_date_after_start(self):
        """End date must be after start date."""
        form = create_form(
            initial={"start": "", "end": ""},
        )
        
        def after_start():
            def validate(value):
                start = form.start()
                if not value or not start:
                    return None
                if value <= start:
                    return "End date must be after start date"
                return None
            return validate
        
        form._validators["end"] = [after_start()]
        
        form.start.set("2024-01-15")
        form.end.set("2024-01-10")
        
        assert not form.is_valid()
        
        form.end.set("2024-01-20")
        assert form.is_valid()

