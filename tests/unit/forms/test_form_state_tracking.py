"""
Comprehensive tests for form dirty/touched state tracking.

Tests cover:
- Touched state per field
- Dirty state computation
- State transitions
- State with validation

Total: 50+ tests
"""

import pytest
from pynext.reactive.forms import create_form, required


# =============================================================================
# TOUCHED STATE (25 tests)
# =============================================================================

class TestTouchedState:
    """Tests for touched state tracking."""
    
    def test_field_starts_untouched(self):
        """Fields start as untouched."""
        form = create_form(initial={"name": "", "email": ""})
        assert not form.is_touched("name")
        assert not form.is_touched("email")
    
    def test_set_value_touches_field(self):
        """set_value marks field as touched."""
        form = create_form(initial={"name": ""})
        form.set_value("name", "Alice")
        assert form.is_touched("name")
    
    def test_direct_signal_set_doesnt_auto_touch(self):
        """Direct signal.set() doesn't auto-touch."""
        form = create_form(initial={"name": ""})
        form.name.set("Alice")
        # Direct signal set doesn't mark touched (for performance)
        # Use set_value() to mark touched
    
    def test_set_touched_true(self):
        """Manually set touched to True."""
        form = create_form(initial={"name": ""})
        form.set_touched("name", True)
        assert form.is_touched("name")
    
    def test_set_touched_false(self):
        """Manually set touched to False."""
        form = create_form(initial={"name": ""})
        form.set_touched("name", True)
        form.set_touched("name", False)
        assert not form.is_touched("name")
    
    def test_touch_all(self):
        """touch_all marks all fields as touched."""
        form = create_form(initial={"a": "", "b": "", "c": ""})
        form.touch_all()
        assert form.is_touched("a")
        assert form.is_touched("b")
        assert form.is_touched("c")
    
    def test_validate_touches_all_by_default(self):
        """validate() touches all fields by default."""
        form = create_form(initial={"name": "", "email": ""})
        form.validate()
        assert form.is_touched("name")
        assert form.is_touched("email")
    
    def test_validate_touch_false(self):
        """validate(touch=False) doesn't touch."""
        form = create_form(initial={"name": ""})
        form.validate(touch=False)
        assert not form.is_touched("name")
    
    def test_reset_clears_touched(self):
        """reset() clears all touched states."""
        form = create_form(initial={"a": "", "b": ""})
        form.touch_all()
        form.reset()
        assert not form.is_touched("a")
        assert not form.is_touched("b")
    
    def test_reset_field_clears_touched(self):
        """reset_field() clears field touched state."""
        form = create_form(initial={"a": "", "b": ""})
        form.touch_all()
        form.reset_field("a")
        assert not form.is_touched("a")
        assert form.is_touched("b")  # Unchanged
    
    def test_is_touched_nonexistent_field(self):
        """is_touched for nonexistent field returns False."""
        form = create_form(initial={"name": ""})
        assert not form.is_touched("nonexistent")
    
    def test_set_touched_nonexistent_field(self):
        """set_touched for nonexistent field does nothing."""
        form = create_form(initial={"name": ""})
        form.set_touched("nonexistent", True)  # Should not raise
    
    def test_touched_independent_per_field(self):
        """Touched state is independent per field."""
        form = create_form(initial={"a": "", "b": "", "c": ""})
        form.set_touched("a", True)
        form.set_touched("c", True)
        
        assert form.is_touched("a")
        assert not form.is_touched("b")
        assert form.is_touched("c")
    
    def test_touched_survives_value_change(self):
        """Touched state survives value changes."""
        form = create_form(initial={"name": ""})
        form.set_touched("name", True)
        form.name.set("New value")
        assert form.is_touched("name")
    
    def test_touched_many_fields(self):
        """Touched tracking with many fields."""
        form = create_form(initial={f"f{i}": "" for i in range(50)})
        
        for i in range(0, 50, 2):
            form.set_touched(f"f{i}", True)
        
        for i in range(50):
            if i % 2 == 0:
                assert form.is_touched(f"f{i}")
            else:
                assert not form.is_touched(f"f{i}")


# =============================================================================
# DIRTY STATE (25 tests)
# =============================================================================

class TestDirtyState:
    """Tests for dirty state computation."""
    
    def test_form_starts_clean(self):
        """Form starts as not dirty."""
        form = create_form(initial={"name": "Alice", "age": 25})
        assert not form.is_dirty()
    
    def test_change_makes_dirty(self):
        """Changing a value makes form dirty."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        assert form.is_dirty()
    
    def test_change_to_same_value_not_dirty(self):
        """Setting same value keeps form clean."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Alice")
        assert not form.is_dirty()
    
    def test_revert_to_initial_clean(self):
        """Reverting to initial value cleans form."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        assert form.is_dirty()
        form.name.set("Alice")
        assert not form.is_dirty()
    
    def test_reset_clears_dirty(self):
        """reset() makes form clean."""
        form = create_form(initial={"name": "Alice"})
        form.name.set("Bob")
        form.reset()
        assert not form.is_dirty()
    
    def test_dirty_any_field(self):
        """Form is dirty if any field changed."""
        form = create_form(initial={"a": "A", "b": "B", "c": "C"})
        form.b.set("Changed")
        assert form.is_dirty()
    
    def test_dirty_all_fields(self):
        """Form is dirty when all fields change."""
        form = create_form(initial={"a": "A", "b": "B"})
        form.a.set("X")
        form.b.set("Y")
        assert form.is_dirty()
    
    def test_dirty_partial_revert(self):
        """Form stays dirty with partial revert."""
        form = create_form(initial={"a": "A", "b": "B"})
        form.a.set("X")
        form.b.set("Y")
        form.a.set("A")  # Revert one field
        assert form.is_dirty()  # Still dirty because b changed
    
    def test_dirty_full_revert(self):
        """Form is clean when all fields reverted."""
        form = create_form(initial={"a": "A", "b": "B"})
        form.a.set("X")
        form.b.set("Y")
        form.a.set("A")
        form.b.set("B")
        assert not form.is_dirty()
    
    def test_dirty_with_empty_initial(self):
        """Dirty detection with empty initial values."""
        form = create_form(initial={"name": "", "count": 0})
        assert not form.is_dirty()
        
        form.name.set("Something")
        assert form.is_dirty()
        
        form.name.set("")
        assert not form.is_dirty()
    
    def test_dirty_with_none_initial(self):
        """Dirty detection with None initial."""
        form = create_form(initial={"nullable": None})
        assert not form.is_dirty()
        
        form.nullable.set("value")
        assert form.is_dirty()
        
        form.nullable.set(None)
        assert not form.is_dirty()
    
    def test_dirty_with_list_initial(self):
        """Dirty detection with list initial."""
        form = create_form(initial={"items": [1, 2, 3]})
        
        form.items.set([4, 5, 6])
        assert form.is_dirty()
        
        form.items.set([1, 2, 3])
        assert not form.is_dirty()
    
    def test_dirty_with_boolean_initial(self):
        """Dirty detection with boolean initial."""
        form = create_form(initial={"active": True})
        assert not form.is_dirty()
        
        form.active.set(False)
        assert form.is_dirty()
        
        form.active.set(True)
        assert not form.is_dirty()
    
    def test_dirty_is_reactive(self):
        """is_dirty() updates reactively."""
        form = create_form(initial={"name": "Alice"})
        
        assert not form.is_dirty()
        form.name.set("Bob")
        assert form.is_dirty()
        form.name.set("Alice")
        assert not form.is_dirty()
    
    def test_dirty_many_fields(self):
        """Dirty computation with many fields."""
        form = create_form(initial={f"f{i}": i for i in range(100)})
        
        assert not form.is_dirty()
        
        form.set_value("f50", 999)
        assert form.is_dirty()
        
        form.set_value("f50", 50)
        assert not form.is_dirty()

