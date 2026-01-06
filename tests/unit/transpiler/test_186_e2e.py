"""
Phase 18.6 End-to-End Tests

=============================================================================
TEST COVERAGE: E2E tests for Linear app handler transpilation
=============================================================================

These tests verify that the actual handlers from the Linear app example
are correctly transpiled using the new AST-based transpiler.

Key patterns from Linear app:
- handle_add_issue (form validation + signal updates)
- handle_delete (filter list)
- handle_status_change (update item in list)
- View switching
- Form toggling
"""

import pytest
from pynext.transpiler.reactive import create_context
from pynext.transpiler.pynext import transpile_handler_source


def transpile_with_context(code: str, ctx):
    """Helper to transpile code with a given reactive context."""
    return transpile_handler_source(code, ctx)


# =============================================================================
# LINEAR APP CONTEXT
# =============================================================================

@pytest.fixture
def linear_ctx():
    """
    Context matching the Linear app's reactive objects.
    
    Based on examples/linear/pages/issues.py
    """
    return create_context(
        signals={
            "all_issues": "sig_all_issues",
            "show_add_form": "sig_show_add",
            "current_view": "sig_view",
            "filter_status": "sig_filter",
            "search_query": "sig_search",
            "selected_issues": "sig_selected",
            "next_id": "sig_next_id",
        },
        forms={
            "issue_form": "form_issue",
        },
        stores={
            "ui_state": "store_ui",
        }
    )


# =============================================================================
# HANDLE_ADD_ISSUE E2E TESTS (10 tests)
# =============================================================================

class TestHandleAddIssueE2E:
    """
    Test the handle_add_issue pattern from Linear app.
    
    This was the primary failing case with regex-based transpilation.
    """
    
    def test_full_pattern(self, linear_ctx):
        """Complete handle_add_issue implementation"""
        code = """
def handle_add_issue():
    if issue_form.validate():
        values = issue_form.values
        new_issue = {
            "id": next_id(),
            "title": values["title"],
            "status": "todo",
            "priority": values.get("priority", "medium")
        }
        all_issues.set([*all_issues(), new_issue])
        next_id.update(lambda n: n + 1)
        issue_form.reset()
        show_add_form.set(False)
"""
        result = transpile_with_context(code, linear_ctx)
        
        # Must have all key components
        assert "__pynext__.getForm" in result
        assert "__pynext__.getSignal" in result
        assert ".validate()" in result
        assert ".values" in result
        assert ".reset()" in result
        assert ".set(" in result
        assert ".update(" in result
    
    def test_validation_gate(self, linear_ctx):
        """Validation must gate the submission"""
        code = """
def handle_add_issue():
    if issue_form.validate():
        all_issues.set([*all_issues(), issue_form.values])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".validate()" in result
    
    def test_id_increment(self, linear_ctx):
        """ID should increment after adding"""
        code = """
def handle_add_issue():
    if issue_form.validate():
        all_issues.set([*all_issues(), {"id": next_id()}])
        next_id.update(lambda n: n + 1)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".update(" in result
    
    def test_form_reset(self, linear_ctx):
        """Form should reset after submission"""
        code = """
def handle_add_issue():
    if issue_form.validate():
        process(issue_form.values)
        issue_form.reset()
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".reset()" in result
    
    def test_modal_close(self, linear_ctx):
        """Modal should close after submission"""
        code = """
def handle_add_issue():
    if issue_form.validate():
        all_issues.set([*all_issues(), issue_form.values])
        show_add_form.set(False)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(false)" in result
    
    def test_values_access(self, linear_ctx):
        """Form values should be accessible"""
        code = """
def handle_add_issue():
    if issue_form.validate():
        title = issue_form.values["title"]
        description = issue_form.values["description"]
        all_issues.set([*all_issues(), {"title": title, "description": description}])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".values" in result
    
    def test_with_defaults(self, linear_ctx):
        """Merge with default values"""
        code = """
def handle_add_issue():
    if issue_form.validate():
        defaults = {"status": "open", "priority": "medium"}
        new_issue = {**defaults, **issue_form.values, "id": next_id()}
        all_issues.set([*all_issues(), new_issue])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".values" in result
    
    def test_error_case(self, linear_ctx):
        """Handle validation failure"""
        code = """
def handle_add_issue():
    if issue_form.validate():
        all_issues.set([*all_issues(), issue_form.values])
    else:
        show_errors(issue_form.errors)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".validate()" in result
    
    def test_async_submission(self, linear_ctx):
        """Async submission pattern"""
        code = """
async def handle_add_issue():
    if issue_form.validate():
        await api.create(issue_form.values)
        all_issues.set([*all_issues(), issue_form.values])
        issue_form.reset()
"""
        result = transpile_with_context(code, linear_ctx)
        assert "async" in result
        assert "await" in result
    
    def test_optimistic_update(self, linear_ctx):
        """Optimistic update pattern"""
        code = """
def handle_add_issue():
    if issue_form.validate():
        values = issue_form.values
        temp_id = f"temp_{next_id()}"
        all_issues.set([*all_issues(), {**values, "id": temp_id}])
        issue_form.reset()
        show_add_form.set(False)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result


# =============================================================================
# HANDLE_DELETE E2E TESTS (10 tests)
# =============================================================================

class TestHandleDeleteE2E:
    """Test the handle_delete pattern from Linear app."""
    
    def test_full_pattern(self, linear_ctx):
        """Complete handle_delete implementation"""
        code = """
def handle_delete(issue_id):
    all_issues.set([
        issue for issue in all_issues()
        if issue["id"] != issue_id
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
        assert ".read()" in result
    
    def test_with_confirmation(self, linear_ctx):
        """Delete with confirmation"""
        code = """
def handle_delete(issue_id):
    if confirm_delete:
        all_issues.set([
            issue for issue in all_issues()
            if issue["id"] != issue_id
        ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_batch_delete(self, linear_ctx):
        """Delete multiple items"""
        code = """
def handle_delete_selected():
    selected = selected_issues()
    all_issues.set([
        issue for issue in all_issues()
        if issue["id"] not in selected
    ])
    selected_issues.set([])
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count("__pynext__.getSignal") >= 3
    
    def test_delete_by_status(self, linear_ctx):
        """Delete all with specific status"""
        code = """
def handle_clear_completed():
    all_issues.set([
        issue for issue in all_issues()
        if issue["status"] != "done"
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_with_undo(self, linear_ctx):
        """Delete with undo capability"""
        code = """
def handle_delete(issue_id):
    issues = all_issues()
    deleted = next(i for i in issues if i["id"] == issue_id)
    all_issues.set([i for i in issues if i["id"] != issue_id])
    # Could save deleted for undo
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result
    
    def test_soft_delete(self, linear_ctx):
        """Soft delete (mark as deleted)"""
        code = """
def handle_delete(issue_id):
    all_issues.set([
        {**issue, "deleted": True} if issue["id"] == issue_id else issue
        for issue in all_issues()
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_filter_after_delete(self, linear_ctx):
        """Update filter after delete"""
        code = """
def handle_delete(issue_id):
    all_issues.set([
        issue for issue in all_issues()
        if issue["id"] != issue_id
    ])
    # Reset filter if list is empty
    if not all_issues():
        filter_status.set("all")
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count("__pynext__.getSignal") >= 2
    
    def test_delete_first(self, linear_ctx):
        """Delete first item"""
        code = """
def handle_delete_first():
    all_issues.set(all_issues()[1:])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_clear_all(self, linear_ctx):
        """Clear all issues"""
        code = """
def handle_clear_all():
    all_issues.set([])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set([])" in result
    
    def test_archive_instead_of_delete(self, linear_ctx):
        """Archive pattern (move to another list)"""
        code = """
def handle_archive(issue_id):
    issues = all_issues()
    archived = next(i for i in issues if i["id"] == issue_id)
    all_issues.set([i for i in issues if i["id"] != issue_id])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result


# =============================================================================
# HANDLE_STATUS_CHANGE E2E TESTS (10 tests)
# =============================================================================

class TestHandleStatusChangeE2E:
    """Test the handle_status_change pattern from Linear app."""
    
    def test_full_pattern(self, linear_ctx):
        """Complete handle_status_change implementation"""
        code = """
def handle_status_change(issue_id, new_status):
    all_issues.set([
        {**issue, "status": new_status} if issue["id"] == issue_id else issue
        for issue in all_issues()
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
        assert ".read()" in result
    
    def test_toggle_done(self, linear_ctx):
        """Toggle done/undone"""
        code = """
def handle_toggle_done(issue_id):
    all_issues.set([
        {**issue, "done": not issue["done"]} if issue["id"] == issue_id else issue
        for issue in all_issues()
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_update_priority(self, linear_ctx):
        """Update issue priority"""
        code = """
def handle_priority_change(issue_id, new_priority):
    all_issues.set([
        {**issue, "priority": new_priority} if issue["id"] == issue_id else issue
        for issue in all_issues()
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_update_multiple_fields(self, linear_ctx):
        """Update multiple fields at once"""
        code = """
def handle_update_issue(issue_id, updates):
    all_issues.set([
        {**issue, **updates} if issue["id"] == issue_id else issue
        for issue in all_issues()
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_drag_drop_reorder(self, linear_ctx):
        """Kanban drag-drop status change"""
        code = """
def handle_drag_drop(issue_id, new_column):
    all_issues.set([
        {**issue, "status": new_column, "order": new_order} if issue["id"] == issue_id else issue
        for issue in all_issues()
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_batch_status_change(self, linear_ctx):
        """Change status for multiple items"""
        code = """
def handle_batch_status_change(new_status):
    selected = selected_issues()
    all_issues.set([
        {**issue, "status": new_status} if issue["id"] in selected else issue
        for issue in all_issues()
    ])
    selected_issues.set([])
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count("__pynext__.getSignal") >= 3
    
    def test_update_with_timestamp(self, linear_ctx):
        """Update status"""
        code = """
def handle_status_change(issue_id, new_status):
    all_issues.set([
        {**issue, "status": new_status} if issue["id"] == issue_id else issue
        for issue in all_issues()
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_conditional_update(self, linear_ctx):
        """Only update if allowed"""
        code = """
def handle_status_change(issue_id, new_status):
    if can_change_status(issue_id, new_status):
        all_issues.set([
            {**issue, "status": new_status} if issue["id"] == issue_id else issue
            for issue in all_issues()
        ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_move_between_columns(self, linear_ctx):
        """Kanban column move"""
        code = """
def handle_move(issue_id, from_column, to_column):
    all_issues.set([
        {**issue, "status": to_column} if issue["id"] == issue_id and issue["status"] == from_column else issue
        for issue in all_issues()
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_update_with_callback(self, linear_ctx):
        """Notify after update"""
        code = """
def handle_status_change(issue_id, new_status):
    all_issues.set([
        {**issue, "status": new_status} if issue["id"] == issue_id else issue
        for issue in all_issues()
    ])
    on_status_changed(issue_id, new_status)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result


# =============================================================================
# VIEW SWITCHING E2E TESTS (10 tests)
# =============================================================================

class TestViewSwitchingE2E:
    """Test view switching patterns from Linear app."""
    
    def test_switch_view(self, linear_ctx):
        """Switch between list/kanban views"""
        code = """
def switch_to_kanban():
    current_view.set("kanban")
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_toggle_view(self, linear_ctx):
        """Toggle between views"""
        code = """
def toggle_view():
    current_view.set("kanban" if current_view() == "list" else "list")
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
        assert ".read()" in result
    
    def test_filter_change(self, linear_ctx):
        """Change filter status"""
        code = """
def handle_filter_change(status):
    filter_status.set(status)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_search(self, linear_ctx):
        """Update search query"""
        code = """
def handle_search(query):
    search_query.set(query)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_clear_search(self, linear_ctx):
        """Clear search"""
        code = """
def handle_clear_search():
    search_query.set("")
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_reset_filters(self, linear_ctx):
        """Reset all filters"""
        code = """
def handle_reset_filters():
    filter_status.set("all")
    search_query.set("")
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count(".set(") >= 2
    
    def test_sort_change(self, linear_ctx):
        """Change sort order"""
        code = """
def handle_sort_change(sort_by):
    ui_state.sort_by = sort_by
"""
        result = transpile_with_context(code, linear_ctx)
        assert "__pynext__.getStore" in result
    
    def test_save_view_state(self, linear_ctx):
        """Save view state to store"""
        code = """
def save_view_state():
    ui_state.view = current_view()
    ui_state.filter = filter_status()
"""
        result = transpile_with_context(code, linear_ctx)
        assert "__pynext__.getSignal" in result
        assert "__pynext__.getStore" in result
    
    def test_restore_view_state(self, linear_ctx):
        """Restore view state from store"""
        code = """
def restore_view_state():
    current_view.set(ui_state.view)
    filter_status.set(ui_state.filter)
"""
        result = transpile_with_context(code, linear_ctx)
        assert "__pynext__.getSignal" in result
        assert "__pynext__.getStore" in result
    
    def test_group_by_status(self, linear_ctx):
        """Group issues by status for Kanban"""
        code = """
def get_issues_by_status():
    issues = all_issues()
    return {
        "todo": [i for i in issues if i["status"] == "todo"],
        "in_progress": [i for i in issues if i["status"] == "in_progress"],
        "done": [i for i in issues if i["status"] == "done"],
    }
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result


# =============================================================================
# FORM TOGGLE E2E TESTS (10 tests)
# =============================================================================

class TestFormToggleE2E:
    """Test form toggle patterns from Linear app."""
    
    def test_show_form(self, linear_ctx):
        """Show add form"""
        code = """
def handle_show_form():
    show_add_form.set(True)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(true)" in result
    
    def test_hide_form(self, linear_ctx):
        """Hide add form"""
        code = """
def handle_hide_form():
    show_add_form.set(False)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(false)" in result
    
    def test_toggle_form(self, linear_ctx):
        """Toggle form visibility"""
        code = """
def handle_toggle_form():
    show_add_form.set(not show_add_form())
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
        assert ".read()" in result
    
    def test_cancel_form(self, linear_ctx):
        """Cancel form and reset"""
        code = """
def handle_cancel():
    issue_form.reset()
    show_add_form.set(False)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".reset()" in result
        assert ".set(false)" in result
    
    def test_close_on_escape(self, linear_ctx):
        """Close form on escape key"""
        code = """
def handle_escape():
    if show_add_form():
        issue_form.reset()
        show_add_form.set(False)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result
        assert ".reset()" in result
    
    def test_close_on_click_outside(self, linear_ctx):
        """Close when clicking outside"""
        code = """
def handle_click_outside():
    show_add_form.set(False)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(false)" in result
    
    def test_edit_mode_toggle(self, linear_ctx):
        """Toggle between view and edit mode"""
        code = """
def handle_edit_mode(issue_id):
    if current_editing() == issue_id:
        current_editing.set(None)
    else:
        current_editing.set(issue_id)
"""
        ctx = create_context(signals={"current_editing": "sig_edit"})
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert ".set(" in result
    
    def test_form_submit_close(self, linear_ctx):
        """Submit and close form"""
        code = """
def handle_submit():
    if issue_form.validate():
        all_issues.set([*all_issues(), issue_form.values])
        issue_form.reset()
        show_add_form.set(False)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".validate()" in result
        assert ".reset()" in result
        assert ".set(false)" in result
    
    def test_quick_add(self, linear_ctx):
        """Quick add without form"""
        code = """
def handle_quick_add(title):
    new_issue = {"id": next_id(), "title": title, "status": "todo"}
    all_issues.set([*all_issues(), new_issue])
    next_id.update(lambda n: n + 1)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
        assert ".update(" in result
    
    def test_form_prefill(self, linear_ctx):
        """Prefill form for editing"""
        code = """
def handle_edit(issue_id):
    issue = next(i for i in all_issues() if i["id"] == issue_id)
    issue_form.title.set(issue["title"])
    issue_form.description.set(issue["description"])
    show_add_form.set(True)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result
        assert ".set(" in result


# =============================================================================
# SELECTION E2E TESTS (10 tests)
# =============================================================================

class TestSelectionE2E:
    """Test selection patterns from Linear app."""
    
    def test_select_issue(self, linear_ctx):
        """Select an issue"""
        code = """
def handle_select(issue_id):
    selected_issues.set([*selected_issues(), issue_id])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_deselect_issue(self, linear_ctx):
        """Deselect an issue"""
        code = """
def handle_deselect(issue_id):
    selected_issues.set([
        id for id in selected_issues()
        if id != issue_id
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_toggle_selection(self, linear_ctx):
        """Toggle issue selection"""
        code = """
def handle_toggle_select(issue_id):
    if issue_id in selected_issues():
        selected_issues.set([id for id in selected_issues() if id != issue_id])
    else:
        selected_issues.set([*selected_issues(), issue_id])
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count("__pynext__.getSignal") >= 3
    
    def test_select_all(self, linear_ctx):
        """Select all issues"""
        code = """
def handle_select_all():
    selected_issues.set([issue["id"] for issue in all_issues()])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_clear_selection(self, linear_ctx):
        """Clear all selections"""
        code = """
def handle_clear_selection():
    selected_issues.set([])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set([])" in result
    
    def test_invert_selection(self, linear_ctx):
        """Invert selection"""
        code = """
def handle_invert_selection():
    current = selected_issues()
    all_ids = [issue["id"] for issue in all_issues()]
    selected_issues.set([id for id in all_ids if id not in current])
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count("__pynext__.getSignal") >= 3
    
    def test_select_by_status(self, linear_ctx):
        """Select all with specific status"""
        code = """
def handle_select_by_status(status):
    selected_issues.set([
        issue["id"] for issue in all_issues()
        if issue["status"] == status
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_batch_action(self, linear_ctx):
        """Perform action on selection"""
        code = """
def handle_batch_delete():
    selected = selected_issues()
    all_issues.set([
        issue for issue in all_issues()
        if issue["id"] not in selected
    ])
    selected_issues.set([])
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count("__pynext__.getSignal") >= 4
    
    def test_is_selected(self, linear_ctx):
        """Check if issue is selected"""
        code = """
def is_selected(issue_id):
    return issue_id in selected_issues()
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result
    
    def test_selection_count(self, linear_ctx):
        """Get selection count"""
        code = """
def get_selection_count():
    return len(selected_issues())
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result


# =============================================================================
# FULL INTEGRATION TESTS (20 tests)
# =============================================================================

class TestFullIntegration:
    """Full integration tests combining multiple patterns."""
    
    def test_complete_crud_flow(self, linear_ctx):
        """Complete CRUD operations"""
        code = """
# Create
def handle_create():
    if issue_form.validate():
        all_issues.set([*all_issues(), issue_form.values])
        issue_form.reset()

# Read (implicit in reactive bindings)

# Update
def handle_update(issue_id, updates):
    all_issues.set([
        {**issue, **updates} if issue["id"] == issue_id else issue
        for issue in all_issues()
    ])

# Delete
def handle_delete(issue_id):
    all_issues.set([
        issue for issue in all_issues()
        if issue["id"] != issue_id
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".validate()" in result
        assert ".reset()" in result
        assert result.count(".set(") >= 3
    
    def test_form_with_validation_errors(self, linear_ctx):
        """Handle validation errors gracefully"""
        code = """
def handle_submit():
    if not issue_form.validate():
        # Show errors
        return
    all_issues.set([*all_issues(), issue_form.values])
    issue_form.reset()
    show_add_form.set(False)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".validate()" in result
    
    def test_optimistic_update_with_rollback(self, linear_ctx):
        """Optimistic update pattern"""
        code = """
async def handle_update(issue_id, updates):
    old_issues = all_issues()
    all_issues.set([
        {**issue, **updates} if issue["id"] == issue_id else issue
        for issue in old_issues
    ])
    await api.update(issue_id, updates)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_filter_and_sort(self, linear_ctx):
        """Combined filter and sort"""
        code = """
def get_filtered_issues():
    issues = all_issues()
    # Filter by status
    if filter_status() != "all":
        issues = [i for i in issues if i["status"] == filter_status()]
    # Filter by search
    query = search_query()
    if query:
        issues = [i for i in issues if query.lower() in i["title"].lower()]
    return issues
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count(".read()") >= 3
    
    def test_kanban_drag_drop(self, linear_ctx):
        """Kanban drag and drop"""
        code = """
def handle_drag_drop(issue_id, from_status, to_status, position):
    all_issues.set([
        {**issue, "status": to_status, "order": position} if issue["id"] == issue_id else issue
        for issue in all_issues()
    ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_undo_redo_pattern(self, linear_ctx):
        """Undo/redo with history"""
        code = """
def handle_action():
    # Save current state for undo
    current = all_issues()
    # Perform action
    all_issues.set([*current, new_issue])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result
        assert ".set(" in result
    
    def test_auto_save(self, linear_ctx):
        """Auto-save pattern"""
        code = """
async def auto_save():
    data = all_issues()
    await api.save(data)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result
    
    def test_bulk_import(self, linear_ctx):
        """Bulk import issues"""
        code = """
def handle_import(imported_issues):
    current = all_issues()
    max_id = max(i["id"] for i in current) if current else 0
    new_issues = [
        {**issue, "id": max_id + i + 1}
        for i, issue in enumerate(imported_issues)
    ]
    all_issues.set([*current, *new_issues])
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_export_data(self, linear_ctx):
        """Export issues data"""
        code = """
def handle_export():
    data = {
        "issues": all_issues(),
        "view": current_view(),
        "filter": filter_status(),
    }
    return json.dumps(data)
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count(".read()") >= 3
    
    def test_keyboard_shortcuts(self, linear_ctx):
        """Keyboard shortcut handlers"""
        code = """
def handle_keydown(key):
    if key == "n":
        show_add_form.set(True)
    elif key == "Escape":
        show_add_form.set(False)
    elif key == "a":
        selected_issues.set([i["id"] for i in all_issues()])
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count(".set(") >= 3
    
    def test_real_time_updates(self, linear_ctx):
        """Handle real-time updates from server"""
        code = """
def handle_server_update(update):
    if update["type"] == "create":
        all_issues.set([*all_issues(), update["issue"]])
    elif update["type"] == "update":
        all_issues.set([
            update["issue"] if i["id"] == update["issue"]["id"] else i
            for i in all_issues()
        ])
    elif update["type"] == "delete":
        all_issues.set([
            i for i in all_issues()
            if i["id"] != update["issue_id"]
        ])
"""
        result = transpile_with_context(code, linear_ctx)
        assert result.count(".set(") >= 3
    
    def test_offline_sync(self, linear_ctx):
        """Offline sync pattern"""
        code = """
async def sync_offline_changes():
    pending = ui_state.pending_changes
    for change in pending:
        await api.sync(change)
    ui_state.pending_changes = []
"""
        result = transpile_with_context(code, linear_ctx)
        assert "__pynext__.getStore" in result
    
    def test_computed_stats(self, linear_ctx):
        """Compute statistics from issues"""
        code = """
def get_stats():
    issues = all_issues()
    return {
        "total": len(issues),
        "todo": len([i for i in issues if i["status"] == "todo"]),
        "in_progress": len([i for i in issues if i["status"] == "in_progress"]),
        "done": len([i for i in issues if i["status"] == "done"]),
    }
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result
    
    def test_pagination(self, linear_ctx):
        """Pagination controls"""
        code = """
def get_page(page_num, page_size=10):
    issues = all_issues()
    start = page_num * page_size
    end = start + page_size
    return issues[start:end]
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result
    
    def test_search_with_debounce(self, linear_ctx):
        """Search with debounce"""
        code = """
def handle_search_input(value):
    search_query.set(value)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_notification_after_action(self, linear_ctx):
        """Show notification after action"""
        code = """
def handle_delete(issue_id):
    all_issues.set([i for i in all_issues() if i["id"] != issue_id])
    show_notification("Issue deleted")
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(" in result
    
    def test_confirm_dialog_pattern(self, linear_ctx):
        """Confirm dialog before action"""
        code = """
def handle_delete_with_confirm(issue_id):
    if not ui_state.confirm_delete:
        ui_state.pending_delete = issue_id
        ui_state.show_confirm = True
        return
    
    all_issues.set([i for i in all_issues() if i["id"] != issue_id])
    ui_state.show_confirm = False
"""
        result = transpile_with_context(code, linear_ctx)
        assert "__pynext__.getStore" in result
        assert "__pynext__.getSignal" in result
    
    def test_accessibility_focus(self, linear_ctx):
        """Manage focus for accessibility"""
        code = """
def handle_close_modal():
    show_add_form.set(False)
    # Focus returns to trigger button
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".set(false)" in result
    
    def test_error_boundary(self, linear_ctx):
        """Handler with signal read"""
        code = """
def handle_action():
    data = all_issues()
    process(data)
"""
        result = transpile_with_context(code, linear_ctx)
        assert ".read()" in result
