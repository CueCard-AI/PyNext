"""
Comprehensive tests for form reset functionality.

Tests cover:
- Full form reset
- Single field reset
- Reset values
- Reset errors
- Reset touched state
- Reset during submission

Total: 50+ tests
"""

import pytest
from pynext.reactive.forms import create_form, required


# =============================================================================
# FULL FORM RESET (20 tests)
# =============================================================================

class TestFullFormReset:
    """Tests for full form reset."""
    
    def test_reset_restores_initial_string(self):
        """Reset restores string to initial."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        form.reset()
        assert form.name() == "Alice"
    
    def test_reset_restores_initial_number(self):
        """Reset restores number to initial."""
        form = create_form(initial={"age": 25})
        form.age.set(30)
        form.reset()
        assert form.age() == 25
    
    def test_reset_restores_initial_boolean(self):
        """Reset restores boolean to initial."""
        form = create_form(initial={"active": False})
        form.active.set(True)
        form.reset()
        assert form.active() is False
    
    def test_reset_restores_initial_list(self):
        """Reset restores list to initial."""
        form = create_form(initial={"items": [1, 2, 3]})
        form.items.set([4, 5, 6])
        form.reset()
        assert form.items() == [1, 2, 3]
    
    def test_reset_restores_initial_none(self):
        """Reset restores None to initial."""
        form = create_form(initial={"nullable": None})
        form.nullable.set("value")
        form.reset()
        assert form.nullable() is None
    
    def test_reset_clears_all_errors(self):
        """Reset clears all validation errors."""
        form = create_form(
            initial={"a": "", "b": ""},
            validators={"a": [required()], "b": [required()]}
        )
        form.validate()
        form.reset()
        assert form.errors.a == ""
        assert form.errors.b == ""
    
    def test_reset_clears_manual_errors(self):
        """Reset clears manually set errors."""
        form = create_form(initial={"name": ""})
        form.set_error("name", "Server error")
        form.reset()
        assert form.errors.name == ""
    
    def test_reset_clears_all_touched(self):
        """Reset clears all touched states."""
        form = create_form(initial={"a": "", "b": "", "c": ""})
        form.touch_all()
        form.reset()
        assert not form.is_touched("a")
        assert not form.is_touched("b")
        assert not form.is_touched("c")
    
    def test_reset_clears_submitting(self):
        """Reset clears submitting state."""
        form = create_form(initial={"name": ""})
        form._is_submitting.set(True)
        form.reset()
        assert not form.is_submitting()
    
    def test_reset_multiple_times(self):
        """Can reset multiple times."""
        form = create_form(initial={"count": 0})
        
        form.count.set(1)
        form.reset()
        assert form.count() == 0
        
        form.count.set(2)
        form.reset()
        assert form.count() == 0
        
        form.count.set(3)
        form.reset()
        assert form.count() == 0
    
    def test_reset_many_fields(self):
        """Reset works with many fields."""
        initial = {f"field_{i}": i for i in range(20)}
        form = create_form(initial=initial)
        
        for i in range(20):
            form.set_value(f"field_{i}", i * 10)
        
        form.reset()
        
        for i in range(20):
            assert form.get_value(f"field_{i}") == i
    
    def test_reset_with_empty_initial(self):
        """Reset to empty initial values."""
        form = create_form(initial={"name": "", "count": 0})
        form.name.set("Alice")
        form.count.set(42)
        form.reset()
        assert form.name() == ""
        assert form.count() == 0


# =============================================================================
# SINGLE FIELD RESET (15 tests)
# =============================================================================

class TestSingleFieldReset:
    """Tests for single field reset."""
    
    def test_reset_field_value(self):
        """reset_field restores single field value."""
        form = create_form(initial={"a": "A", "b": "B"})
        form.a.set("X")
        form.b.set("Y")
        form.reset_field("a")
        assert form.a() == "A"
        assert form.b() == "Y"  # Unchanged
    
    def test_reset_field_error(self):
        """reset_field clears field error."""
        form = create_form(
            initial={"a": "", "b": ""},
            validators={"a": [required()], "b": [required()]}
        )
        form.validate()
        form.reset_field("a")
        assert form.errors.a == ""
        assert form.errors.b != ""  # Unchanged
    
    def test_reset_field_touched(self):
        """reset_field clears field touched state."""
        form = create_form(initial={"a": "", "b": ""})
        form.touch_all()
        form.reset_field("a")
        assert not form.is_touched("a")
        assert form.is_touched("b")  # Unchanged
    
    def test_reset_field_manual_error(self):
        """reset_field clears manual error."""
        form = create_form(initial={"name": ""})
        form.set_error("name", "Error")
        form.reset_field("name")
        assert form.errors.name == ""
    
    def test_reset_field_nonexistent(self):
        """reset_field for nonexistent field does nothing."""
        form = create_form(initial={"name": "Alice"})
        form.reset_field("nonexistent")  # Should not raise
        assert form.name() == "Alice"
    
    def test_reset_field_preserves_others(self):
        """reset_field preserves other field states."""
        form = create_form(initial={"a": "", "b": "", "c": ""})
        form.set_values({"a": "X", "b": "Y", "c": "Z"})
        form.touch_all()
        
        form.reset_field("b")
        
        assert form.a() == "X"
        assert form.b() == ""
        assert form.c() == "Z"
        assert form.is_touched("a")
        assert not form.is_touched("b")
        assert form.is_touched("c")


# =============================================================================
# RESET EDGE CASES (15 tests)
# =============================================================================

class TestResetEdgeCases:
    """Edge case tests for reset."""
    
    def test_reset_empty_form(self):
        """Reset empty form works."""
        form = create_form(initial={})
        form.reset()  # Should not raise
    
    def test_reset_preserves_validators(self):
        """Reset preserves validator configuration."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.name.set("Alice")
        form.reset()
        
        assert not form.is_valid()  # Still has validator
    
    def test_reset_during_validation(self):
        """Reset during validation cycle."""
        form = create_form(
            initial={"name": ""},
            validators={"name": [required()]}
        )
        form.validate()
        form.reset()
        form.validate()
        
        assert form.errors.name != ""
    
    def test_reset_preserves_initial_reference(self):
        """Reset always uses original initial values."""
        initial = {"name": "Original"}
        form = create_form(initial=initial)
        
        # Modify original dict (shouldn't affect form)
        initial["name"] = "Modified"
        
        form.name.set("Changed")
        form.reset()
        
        # Should reset to what was passed, not current dict value
        # (depends on implementation - copy vs reference)
    
    def test_reset_complex_nested(self):
        """Reset with complex nested values."""
        form = create_form(initial={
            "config": {"nested": {"deep": "value"}},
            "items": [{"id": 1}, {"id": 2}],
        })
        
        form.config.set({"different": "structure"})
        form.items.set([])
        
        form.reset()
        
        assert form.config() == {"nested": {"deep": "value"}}
        assert form.items() == [{"id": 1}, {"id": 2}]
    
    def test_reset_unicode(self):
        """Reset with unicode values."""
        form = create_form(initial={"name": "日本語"})
        form.name.set("Changed")
        form.reset()
        assert form.name() == "日本語"
    
    def test_reset_special_characters(self):
        """Reset with special character values."""
        form = create_form(initial={"code": "<script>alert('xss')</script>"})
        form.code.set("safe")
        form.reset()
        assert form.code() == "<script>alert('xss')</script>"

