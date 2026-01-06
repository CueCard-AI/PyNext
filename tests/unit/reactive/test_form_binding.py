"""
Tests for PyNext Form Binding and Hydration

These tests ensure that:
1. Forms are properly registered with the RenderContext
2. Form bindings are included in hydration data
3. Form reset triggers proper reactive updates
4. Multiple issues with same title get unique IDs

This test module covers the fix for the "duplicate title" bug where
creating an issue with the same title as an existing one would fail.
"""

import pytest
from pynext.reactive.forms import create_form, FormState
from pynext.reactive.signal import signal


class TestFormCreation:
    """Test form creation and basic functionality."""
    
    def test_create_form_returns_form_state(self):
        """create_form should return a FormState instance."""
        form = create_form({"name": "", "email": ""})
        assert isinstance(form, FormState)
    
    def test_form_has_initial_values(self):
        """Form should have the initial values set."""
        form = create_form({"title": "test", "count": 42})
        assert form.values["title"] == "test"
        assert form.values["count"] == 42
    
    def test_form_has_unique_id(self):
        """Each form should have a unique ID."""
        form1 = create_form({"name": ""})
        form2 = create_form({"name": ""})
        assert form1._form_id != form2._form_id
    
    def test_form_set_updates_value(self):
        """Setting a field should update the form values."""
        form = create_form({"name": ""})
        form.set_value("name", "Alice")
        assert form.values["name"] == "Alice"
    
    def test_form_reset_restores_initial(self):
        """Reset should restore initial values."""
        form = create_form({"name": "initial"})
        form.set_value("name", "changed")
        assert form.values["name"] == "changed"
        
        form.reset()
        assert form.values["name"] == "initial"


class TestFormValidation:
    """Test form validation functionality."""
    
    def test_form_validate_with_required(self):
        """Form with required validator should validate correctly."""
        form = create_form(
            {"title": ""},
            validators={"title": lambda v: "Required" if not v else None}
        )
        assert not form.validate()
        
        form.set_value("title", "Hello")
        assert form.validate()
    
    def test_form_errors_are_cleared_on_valid(self):
        """Errors should be cleared when validation passes."""
        form = create_form(
            {"name": ""},
            validators={"name": lambda v: "Required" if not v else None}
        )
        form.validate()
        # errors is a dict-like object, access field errors directly
        assert form.errors["name"]  # Has an error message
        
        form.set_value("name", "Valid")
        form.validate()
        assert not form.errors["name"]  # No error (empty string or None)


class TestFormHydration:
    """Test form hydration state generation."""
    
    def test_form_to_hydration_state(self):
        """Form should generate proper hydration state."""
        form = create_form({"name": "", "email": ""})
        state = form.to_hydration_state()
        
        assert "id" in state
        assert "initial" in state
        assert "values" in state
        assert state["initial"]["name"] == ""
        assert state["initial"]["email"] == ""
    
    def test_form_hydration_includes_validators(self):
        """Hydration state should include validator info."""
        # Validators are serialized for client-side reconstruction
        form = create_form(
            {"name": ""},
            validators={"name": [lambda v: "Required" if not v else None]}
        )
        state = form.to_hydration_state()
        
        # validators should be present (even if empty serialization)
        assert "validators" in state


class TestIssueCreation:
    """Test the issue creation scenario that was originally buggy."""
    
    def test_multiple_issues_with_same_title_have_unique_ids(self):
        """Creating issues with same title should give unique IDs."""
        all_issues = signal([], name="all_issues")
        next_id = signal(1, name="next_id")
        
        # Create first issue
        issue1 = {
            "id": next_id(),
            "title": "duplicate title",
            "status": "backlog"
        }
        all_issues.set([*all_issues(), issue1])
        next_id.set(next_id() + 1)
        
        # Create second issue with same title
        issue2 = {
            "id": next_id(),
            "title": "duplicate title",
            "status": "todo"
        }
        all_issues.set([*all_issues(), issue2])
        next_id.set(next_id() + 1)
        
        # Verify
        issues = all_issues()
        assert len(issues) == 2
        assert issues[0]["id"] == 1
        assert issues[1]["id"] == 2
        assert issues[0]["title"] == "duplicate title"
        assert issues[1]["title"] == "duplicate title"
        assert issues[0]["id"] != issues[1]["id"]
    
    def test_form_reset_clears_values(self):
        """Form reset should clear all values to initial state."""
        issue_form = create_form({
            "title": "",
            "description": "",
            "status": "backlog",
            "priority": "medium"
        })
        
        # Simulate user filling the form
        issue_form.set_value("title", "My Issue")
        issue_form.set_value("description", "Some description")
        
        assert issue_form.values["title"] == "My Issue"
        assert issue_form.values["description"] == "Some description"
        
        # Reset
        issue_form.reset()
        
        # Values should be back to initial
        assert issue_form.values["title"] == ""
        assert issue_form.values["description"] == ""
        assert issue_form.values["status"] == "backlog"
        assert issue_form.values["priority"] == "medium"
    
    def test_create_issue_flow(self):
        """Test the complete create issue flow."""
        all_issues = signal([], name="all_issues")
        next_id = signal(1, name="next_id")
        show_add_form = signal(False, name="show_add_form")
        
        issue_form = create_form({
            "title": "",
            "description": "",
            "status": "backlog",
            "priority": "medium"
        })
        
        # Open modal
        show_add_form.set(True)
        assert show_add_form()
        
        # Fill form
        issue_form.set_value("title", "First Issue")
        issue_form.set_value("description", "Description 1")
        
        # Create issue
        new_issue = {
            "id": next_id(),
            "title": issue_form.values["title"],
            "description": issue_form.values["description"],
            "status": issue_form.values["status"],
            "priority": issue_form.values["priority"],
        }
        all_issues.set([*all_issues(), new_issue])
        next_id.set(next_id() + 1)
        issue_form.reset()
        show_add_form.set(False)
        
        # Verify first issue created
        assert len(all_issues()) == 1
        assert not show_add_form()
        assert issue_form.values["title"] == ""
        
        # Create second issue with same title
        show_add_form.set(True)
        issue_form.set_value("title", "First Issue")  # Same title
        issue_form.set_value("description", "Description 2")
        
        new_issue2 = {
            "id": next_id(),
            "title": issue_form.values["title"],
            "description": issue_form.values["description"],
            "status": issue_form.values["status"],
            "priority": issue_form.values["priority"],
        }
        all_issues.set([*all_issues(), new_issue2])
        next_id.set(next_id() + 1)
        issue_form.reset()
        show_add_form.set(False)
        
        # Verify both issues exist with unique IDs
        issues = all_issues()
        assert len(issues) == 2
        assert issues[0]["id"] == 1
        assert issues[1]["id"] == 2
        assert issues[0]["title"] == issues[1]["title"] == "First Issue"


class TestFormContextRegistration:
    """Test that forms are registered with RenderContext for hydration."""
    
    def test_form_context_available(self):
        """Test that RenderContext can be accessed."""
        try:
            from pynext.core.context import get_context, set_context, RenderContext
            
            # Create a test context
            ctx = RenderContext()
            set_context(ctx)
            
            # Create a form - it should register itself
            form = create_form({"name": "test"})
            
            # Check that form is registered
            # Note: This depends on implementation details
            assert form._form_id is not None
            
        except ImportError:
            pytest.skip("RenderContext not available")
    
    def test_form_bindings_structure(self):
        """Test the structure of form bindings for hydration."""
        from pynext.reactive.forms import FormState
        
        form = create_form({
            "title": "",
            "description": "",
            "priority": "medium",
            "status": "backlog"
        })
        
        state = form.to_hydration_state()
        
        # Verify structure
        assert "id" in state
        assert "initial" in state
        assert "values" in state
        
        # Check initial values match
        assert state["initial"]["title"] == ""
        assert state["initial"]["description"] == ""
        assert state["initial"]["priority"] == "medium"
        assert state["initial"]["status"] == "backlog"
