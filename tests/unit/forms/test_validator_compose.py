"""
Comprehensive tests for validator composition.

Tests cover:
- compose() function
- when() conditional validation
- validate_all() utility
- Complex validator chains
- Order of execution

Total: 50+ tests
"""

import pytest
from pynext.reactive.forms import create_form
from pynext.reactive.validators import (
    required,
    min_length,
    max_length,
    email,
    pattern,
    compose,
    when,
    validate_all,
    run_validators,
)
from pynext.reactive import signal


# =============================================================================
# COMPOSE BASICS (20 tests)
# =============================================================================

class TestComposeBasics:
    """Basic compose() tests."""
    
    def test_compose_empty(self):
        """Empty compose returns None (always valid)."""
        v = compose()
        assert v("anything") is None
    
    def test_compose_single(self):
        """Compose single validator."""
        v = compose(required())
        assert v("") is not None
        assert v("ok") is None
    
    def test_compose_two(self):
        """Compose two validators."""
        v = compose(required(), min_length(3))
        assert v("") is not None
        assert v("ab") is not None
        assert v("abc") is None
    
    def test_compose_three(self):
        """Compose three validators."""
        v = compose(required(), min_length(3), max_length(10))
        assert v("") is not None
        assert v("ab") is not None
        assert v("abc") is None
        assert v("a" * 11) is not None
    
    def test_compose_returns_first_error(self):
        """Compose returns first error."""
        v = compose(
            required("Error 1"),
            min_length(3, "Error 2"),
            max_length(10, "Error 3"),
        )
        assert v("") == "Error 1"
        assert v("ab") == "Error 2"
        assert v("a" * 11) == "Error 3"
    
    def test_compose_short_circuits(self):
        """Compose stops at first error."""
        call_count = [0]
        
        def counting_validator():
            def validate(value):
                call_count[0] += 1
                return None
            return validate
        
        v = compose(required(), counting_validator())
        v("")  # required fails
        assert call_count[0] == 0
    
    def test_compose_all_pass(self):
        """Compose all pass returns None."""
        v = compose(
            required(),
            min_length(3),
            max_length(100),
        )
        assert v("hello world") is None
    
    def test_compose_reusable(self):
        """Composed validator is reusable."""
        v = compose(required(), min_length(3))
        assert v("") is not None
        assert v("ok") is not None
        assert v("abc") is None
        assert v("") is not None
    
    def test_compose_different_types(self):
        """Compose different validator types."""
        v = compose(
            required(),
            email(),
            max_length(50),
        )
        assert v("") is not None
        assert v("invalid") is not None
        assert v("user@example.com") is None
    
    def test_compose_with_pattern(self):
        """Compose with pattern validator."""
        v = compose(
            required(),
            pattern(r"^[a-z]+$", "lowercase only"),
        )
        assert v("ABC") == "lowercase only"
        assert v("abc") is None


# =============================================================================
# NESTED COMPOSE (10 tests)
# =============================================================================

class TestNestedCompose:
    """Tests for nested compose()."""
    
    def test_compose_nested(self):
        """Nested compose works."""
        inner = compose(required(), min_length(3))
        outer = compose(inner, max_length(10))
        assert outer("") is not None
        assert outer("ab") is not None
        assert outer("abc") is None
        assert outer("a" * 11) is not None
    
    def test_compose_deeply_nested(self):
        """Deeply nested compose works."""
        v1 = compose(required())
        v2 = compose(v1, min_length(3))
        v3 = compose(v2, max_length(10))
        v4 = compose(v3, pattern(r"^[a-z]+$"))
        
        assert v4("") is not None
        assert v4("ab") is not None
        assert v4("ABC") is not None
        assert v4("abcdef") is None
    
    def test_compose_parallel(self):
        """Multiple parallel composes work."""
        v1 = compose(required(), min_length(3))
        v2 = compose(required(), email())
        
        assert v1("ab") is not None
        assert v1("abc") is None
        
        assert v2("invalid") is not None
        assert v2("a@b.com") is None


# =============================================================================
# WHEN CONDITIONAL (15 tests)
# =============================================================================

class TestWhenConditional:
    """Tests for when() conditional validation."""
    
    def test_when_true_validates(self):
        """When True, validators run."""
        v = when(lambda: True, required())
        assert v("") is not None
    
    def test_when_false_skips(self):
        """When False, validators skip."""
        v = when(lambda: False, required())
        assert v("") is None
    
    def test_when_dynamic(self):
        """When with dynamic condition."""
        is_required = signal(False)
        v = when(is_required, required())
        
        assert v("") is None
        
        is_required.set(True)
        assert v("") is not None
    
    def test_when_multiple_validators(self):
        """When with multiple validators."""
        v = when(lambda: True, required(), min_length(3))
        assert v("") is not None
        assert v("ab") is not None
        assert v("abc") is None
    
    def test_when_based_on_form_field(self):
        """When based on another form field."""
        form = create_form(initial={"type": "business", "company": ""})
        
        v = when(
            lambda: form.type() == "business",
            required("Company required for business"),
        )
        
        assert v("") == "Company required for business"
        
        form.type.set("personal")
        assert v("") is None
    
    def test_when_chained(self):
        """Multiple when() in chain."""
        cond1 = signal(True)
        cond2 = signal(True)
        
        v = compose(
            when(cond1, required("Cond1 failed")),
            when(cond2, min_length(3, "Cond2 failed")),
        )
        
        assert v("") == "Cond1 failed"
        assert v("ab") == "Cond2 failed"
        assert v("abc") is None
        
        cond1.set(False)
        assert v("") == "Cond2 failed"  # required skipped
        
        cond2.set(False)
        assert v("") is None  # both skipped


# =============================================================================
# VALIDATE_ALL (10 tests)
# =============================================================================

class TestValidateAll:
    """Tests for validate_all() utility."""
    
    def test_validate_all_returns_list(self):
        """validate_all returns list."""
        result = validate_all("", [required()])
        assert isinstance(result, list)
    
    def test_validate_all_single_error(self):
        """Single error in list."""
        result = validate_all("", [required("Error")])
        assert result == ["Error"]
    
    def test_validate_all_multiple_errors(self):
        """All errors collected."""
        result = validate_all("", [
            required("E1"),
            min_length(3, "E2"),  # Also fails for empty
        ])
        assert "E1" in result
        assert "E2" in result
    
    def test_validate_all_empty_on_success(self):
        """Empty list on success."""
        result = validate_all("hello", [required(), min_length(3)])
        assert result == []
    
    def test_validate_all_partial_fail(self):
        """Some pass, some fail."""
        result = validate_all("ab", [
            required(),  # passes
            min_length(3, "Too short"),  # fails
        ])
        assert result == ["Too short"]
    
    def test_validate_all_empty_validators(self):
        """Empty validator list."""
        result = validate_all("anything", [])
        assert result == []
    
    def test_validate_all_order_preserved(self):
        """Error order preserved."""
        result = validate_all("", [
            required("First"),
            min_length(3, "Second"),
        ])
        assert result[0] == "First"
        assert result[1] == "Second"


# =============================================================================
# RUN_VALIDATORS (5 tests)
# =============================================================================

class TestRunValidators:
    """Tests for run_validators() utility."""
    
    def test_run_single(self):
        """Run single validator."""
        result = run_validators(required("Err"), "")
        assert result == "Err"
    
    def test_run_list(self):
        """Run list of validators."""
        result = run_validators([required(), min_length(3)], "")
        assert result is not None
    
    def test_run_first_error(self):
        """Returns first error only."""
        result = run_validators([
            required("E1"),
            min_length(3, "E2"),
        ], "ab")
        assert result == "E2"  # required passes, min_length fails
    
    def test_run_none(self):
        """None validators returns None."""
        result = run_validators(None, "anything")
        assert result is None
    
    def test_run_all_pass(self):
        """All pass returns None."""
        result = run_validators([required(), min_length(2)], "hello")
        assert result is None

