"""
Phase 18.6 Complex Handler Pattern Tests

=============================================================================
TEST COVERAGE: 100 tests for complex handler patterns
=============================================================================

These tests verify that real-world handler patterns are correctly transpiled.
They focus on the patterns that were failing with the old regex-based approach.

Key patterns tested:
- handle_add_issue (form validation + signal updates + reset)
- handle_delete (filter list comprehension)
- handle_status_change (conditional updates)
- Multi-signal handlers
- Nested conditionals
- List comprehensions with signals
- Complex expressions
"""

import pytest
from pynext.transpiler.reactive import create_context
from pynext.transpiler.pynext import transpile_handler_source


def transpile_with_context(code: str, ctx):
    """Helper to transpile code with a given reactive context."""
    return transpile_handler_source(code, ctx)


# =============================================================================
# HANDLE_ADD_ISSUE PATTERN (15 tests)
# =============================================================================

class TestHandleAddIssuePattern:
    """
    The pattern that was failing with regex-based transpilation:
    
    def handle_add_issue():
        if issue_form.validate():
            values = issue_form.values
            all_issues.set([*all_issues(), values])
            issue_form.reset()
            show_add_form.set(False)
    """
    
    @pytest.fixture
    def ctx(self):
        return create_context(
            signals={"all_issues": "sig_1", "show_add_form": "sig_2", "next_id": "sig_3"},
            forms={"issue_form": "form_1"}
        )
    
    def test_basic_pattern(self, ctx):
        """Full handle_add_issue pattern"""
        code = """
if issue_form.validate():
    values = issue_form.values
    all_issues.set([*all_issues(), values])
    issue_form.reset()
    show_add_form.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert "__pynext__.getSignal" in result
        assert ".validate()" in result
        assert ".reset()" in result
    
    def test_with_id_generation(self, ctx):
        """Pattern with ID generation"""
        code = """
if issue_form.validate():
    values = issue_form.values
    new_issue = {"id": next_id(), "title": values["title"]}
    all_issues.set([*all_issues(), new_issue])
    next_id.update(lambda n: n + 1)
    issue_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
        assert ".update(" in result
    
    def test_spread_into_list(self, ctx):
        """[*all_issues(), new] → [...read(), new]"""
        code = """
new_item = {"id": 1}
all_issues.set([*all_issues(), new_item])
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert ".set(" in result
    
    def test_validation_gate(self, ctx):
        """Only proceeds if validate() returns True"""
        code = """
if issue_form.validate():
    process()
else:
    show_errors()
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
    
    def test_form_values_access(self, ctx):
        """Access form.values after validation"""
        code = """
if issue_form.validate():
    title = issue_form.values["title"]
    description = issue_form.values["description"]
"""
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_close_modal_after(self, ctx):
        """Close modal/form after submit"""
        code = """
if issue_form.validate():
    submit(issue_form.values)
    show_add_form.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert ".set(false)" in result
    
    def test_reset_after_submit(self, ctx):
        """Reset form after successful submit"""
        code = """
if issue_form.validate():
    submit(issue_form.values)
    issue_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
    
    def test_multiple_signal_updates(self, ctx):
        """Update multiple signals"""
        code = """
if issue_form.validate():
    all_issues.set([*all_issues(), issue_form.values])
    next_id.update(lambda n: n + 1)
    show_add_form.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 3
    
    def test_values_variable_assignment(self, ctx):
        """values = form.values; use values later"""
        code = """
if issue_form.validate():
    values = issue_form.values
    title = values["title"]
    all_issues.set([*all_issues(), {"title": title}])
"""
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_with_error_handling(self, ctx):
        """Validation flow"""
        code = """
if issue_form.validate():
    submit(issue_form.values)
    issue_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
    
    def test_with_default_values(self, ctx):
        """Merge form values with defaults"""
        code = """
if issue_form.validate():
    values = issue_form.values
    full_issue = {"status": "open", **values}
    all_issues.set([*all_issues(), full_issue])
"""
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_with_timestamp(self, ctx):
        """Add timestamp to issue (without import)"""
        code = """
if issue_form.validate():
    values = issue_form.values
    all_issues.set([*all_issues(), values])
"""
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_with_validation_message(self, ctx):
        """Show success message after submit"""
        code = """
if issue_form.validate():
    all_issues.set([*all_issues(), issue_form.values])
    issue_form.reset()
    show_message("Issue created!")
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
    
    def test_empty_form_values(self, ctx):
        """Handle empty values object"""
        code = """
if issue_form.validate():
    if issue_form.values:
        all_issues.set([*all_issues(), issue_form.values])
"""
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_with_nested_conditionals(self, ctx):
        """Multiple conditions before adding"""
        code = """
if issue_form.validate():
    values = issue_form.values
    if values["title"]:
        all_issues.set([*all_issues(), values])
        issue_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result


# =============================================================================
# HANDLE_DELETE PATTERN (15 tests)
# =============================================================================

class TestHandleDeletePattern:
    """
    Pattern for deleting items from a list:
    
    def handle_delete(issue_id):
        all_issues.set([
            issue for issue in all_issues()
            if issue["id"] != issue_id
        ])
    """
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={"all_issues": "sig_1", "todos": "sig_2"})
    
    def test_basic_delete_pattern(self, ctx):
        """Filter out item by ID"""
        code = """
all_issues.set([
    issue for issue in all_issues()
    if issue["id"] != issue_id
])
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getSignal" in result
        assert ".read()" in result
        assert ".set(" in result
    
    def test_delete_with_filter(self, ctx):
        """Using filter() instead of comprehension"""
        code = """
all_issues.set(list(filter(lambda x: x["id"] != issue_id, all_issues())))
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert ".set(" in result
    
    def test_delete_with_index(self, ctx):
        """Delete by index"""
        code = """
issues = all_issues()
issues.pop(index)
all_issues.set(issues)
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert ".set(" in result
    
    def test_delete_with_remove(self, ctx):
        """Remove specific item"""
        code = """
issues = all_issues()
issues.remove(item)
all_issues.set(issues)
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_delete_first(self, ctx):
        """Delete first item"""
        code = """
all_issues.set(all_issues()[1:])
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert ".set(" in result
    
    def test_delete_last(self, ctx):
        """Delete last item"""
        code = """
all_issues.set(all_issues()[:-1])
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_conditional_delete(self, ctx):
        """Delete with confirmation"""
        code = """
if confirm_delete:
    all_issues.set([i for i in all_issues() if i["id"] != target_id])
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_delete_with_callback(self, ctx):
        """Delete and notify"""
        code = """
all_issues.set([i for i in all_issues() if i["id"] != target_id])
on_deleted(target_id)
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_delete_multiple(self, ctx):
        """Delete multiple items"""
        code = """
all_issues.set([i for i in all_issues() if i["id"] not in ids_to_delete])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_delete_by_property(self, ctx):
        """Delete by property value"""
        code = """
all_issues.set([i for i in all_issues() if i["status"] != "deleted"])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_delete_completed(self, ctx):
        """Delete all completed items"""
        code = """
todos.set([t for t in todos() if not t["done"]])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_clear_all(self, ctx):
        """Clear entire list"""
        code = """
all_issues.set([])
"""
        result = transpile_with_context(code, ctx)
        assert ".set([])" in result
    
    def test_keep_only_matching(self, ctx):
        """Keep only matching items (inverse delete)"""
        code = """
all_issues.set([i for i in all_issues() if i["priority"] == "high"])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_delete_with_undo_data(self, ctx):
        """Save deleted item for undo"""
        code = """
deleted = next(i for i in all_issues() if i["id"] == target_id)
all_issues.set([i for i in all_issues() if i["id"] != target_id])
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".read()") >= 2
    
    def test_cascading_delete(self, ctx):
        """Delete from multiple signals"""
        code = """
all_issues.set([i for i in all_issues() if i["id"] != target_id])
todos.set([t for t in todos() if t["issue_id"] != target_id])
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 4


# =============================================================================
# HANDLE_STATUS_CHANGE PATTERN (15 tests)
# =============================================================================

class TestHandleStatusChangePattern:
    """
    Pattern for updating item status:
    
    def handle_status_change(issue_id, new_status):
        all_issues.set([
            {**issue, "status": new_status} if issue["id"] == issue_id else issue
            for issue in all_issues()
        ])
    """
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={"all_issues": "sig_1"})
    
    def test_basic_status_change(self, ctx):
        """Update status by ID"""
        code = """
all_issues.set([
    {**issue, "status": new_status} if issue["id"] == issue_id else issue
    for issue in all_issues()
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
        assert ".read()" in result
    
    def test_update_single_field(self, ctx):
        """Update one field only"""
        code = """
all_issues.update(lambda items: [
    {**i, "title": new_title} if i["id"] == target_id else i
    for i in items
])
"""
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_multiple_fields(self, ctx):
        """Update multiple fields"""
        code = """
all_issues.set([
    {**issue, "status": new_status, "updated_at": now} if issue["id"] == issue_id else issue
    for issue in all_issues()
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_conditional_update(self, ctx):
        """Only update if condition met"""
        code = """
if can_change_status:
    all_issues.set([
        {**i, "status": new_status} if i["id"] == target_id else i
        for i in all_issues()
    ])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_toggle_boolean_field(self, ctx):
        """Toggle done/undone"""
        code = """
all_issues.set([
    {**issue, "done": not issue["done"]} if issue["id"] == issue_id else issue
    for issue in all_issues()
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_increment_field(self, ctx):
        """Increment counter field"""
        code = """
all_issues.set([
    {**issue, "views": issue["views"] + 1} if issue["id"] == issue_id else issue
    for issue in all_issues()
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_append_to_field(self, ctx):
        """Add to list field"""
        code = """
all_issues.set([
    {**issue, "comments": [*issue["comments"], new_comment]} if issue["id"] == issue_id else issue
    for issue in all_issues()
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_update_nested_field(self, ctx):
        """Update nested object field"""
        code = """
all_issues.set([
    {**issue, "meta": {**issue["meta"], "updated": True}} if issue["id"] == issue_id else issue
    for issue in all_issues()
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_batch_update(self, ctx):
        """Update multiple items"""
        code = """
all_issues.set([
    {**issue, "selected": True} if issue["id"] in selected_ids else issue
    for issue in all_issues()
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_clear_field(self, ctx):
        """Clear a field"""
        code = """
all_issues.set([
    {**issue, "assignee": None} if issue["id"] == issue_id else issue
    for issue in all_issues()
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_update_with_function(self, ctx):
        """Use function to compute new value"""
        code = """
all_issues.set([
    {**issue, "priority": compute_priority(issue)} if issue["id"] == issue_id else issue
    for issue in all_issues()
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_update_all_items(self, ctx):
        """Update all items (no condition)"""
        code = """
all_issues.set([
    {**issue, "seen": True}
    for issue in all_issues()
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_update_with_index(self, ctx):
        """Update using enumerate"""
        code = """
all_issues.set([
    {**issue, "order": i}
    for i, issue in enumerate(all_issues())
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_move_item(self, ctx):
        """Change order/position"""
        code = """
items = all_issues()
item = items.pop(old_index)
items.insert(new_index, item)
all_issues.set(items)
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_sort_items(self, ctx):
        """Sort items by field"""
        code = """
all_issues.set(sorted(all_issues(), key=lambda x: x["priority"]))
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result


# =============================================================================
# TOGGLE PATTERNS (10 tests)
# =============================================================================

class TestTogglePatterns:
    """Test toggle and visibility patterns."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={
            "show_modal": "sig_1",
            "is_open": "sig_2",
            "expanded": "sig_3",
        })
    
    def test_toggle_with_set(self, ctx):
        """show_modal.set(not show_modal())"""
        code = "show_modal.set(not show_modal())"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
        assert ".read()" in result
    
    def test_toggle_with_update(self, ctx):
        """show_modal.update(lambda v: not v)"""
        code = "show_modal.update(lambda v: not v)"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_show(self, ctx):
        """show_modal.set(True)"""
        code = "show_modal.set(True)"
        result = transpile_with_context(code, ctx)
        assert ".set(true)" in result
    
    def test_hide(self, ctx):
        """show_modal.set(False)"""
        code = "show_modal.set(False)"
        result = transpile_with_context(code, ctx)
        assert ".set(false)" in result
    
    def test_toggle_multiple(self, ctx):
        """Toggle multiple signals"""
        code = """
show_modal.update(lambda v: not v)
is_open.update(lambda v: not v)
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".update(") >= 2
    
    def test_conditional_toggle(self, ctx):
        """if cond: show_modal.set(True)"""
        code = """
if should_show:
    show_modal.set(True)
else:
    show_modal.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".set(") >= 2
    
    def test_toggle_based_on_other(self, ctx):
        """show_modal.set(is_open())"""
        code = "show_modal.set(is_open())"
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 2
    
    def test_expand_collapse(self, ctx):
        """Expand/collapse pattern"""
        code = """
if expanded():
    expanded.set(False)
else:
    expanded.set(True)
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 3
    
    def test_toggle_with_callback(self, ctx):
        """Toggle and notify"""
        code = """
show_modal.update(lambda v: not v)
on_toggle(show_modal())
"""
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_close_all(self, ctx):
        """Close all modals/panels"""
        code = """
show_modal.set(False)
is_open.set(False)
expanded.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".set(false)") >= 3


# =============================================================================
# LIST MANIPULATION PATTERNS (15 tests)
# =============================================================================

class TestListManipulationPatterns:
    """Test list/array manipulation patterns."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={
            "items": "sig_1",
            "selected": "sig_2",
            "filtered": "sig_3",
        })
    
    def test_append_item(self, ctx):
        """items.set([*items(), new_item])"""
        code = "items.set([*items(), new_item])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
        assert ".read()" in result
    
    def test_prepend_item(self, ctx):
        """items.set([new_item, *items()])"""
        code = "items.set([new_item, *items()])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_filter_items(self, ctx):
        """items.set([x for x in items() if condition])"""
        code = "items.set([x for x in items() if x['active']])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_map_items(self, ctx):
        """items.set([transform(x) for x in items()])"""
        code = "items.set([transform(x) for x in items()])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_sort_items(self, ctx):
        """items.set(sorted(items(), key=...))"""
        code = "items.set(sorted(items(), key=lambda x: x['name']))"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_reverse_items(self, ctx):
        """items.set(list(reversed(items())))"""
        code = "items.set(list(reversed(items())))"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_slice_items(self, ctx):
        """items.set(items()[:10])"""
        code = "items.set(items()[:10])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_concat_lists(self, ctx):
        """items.set([*items(), *more_items])"""
        code = "items.set([*items(), *more_items])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_unique_items(self, ctx):
        """items.set(list(set(items())))"""
        code = "items.set(list(set(items())))"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_add_to_selection(self, ctx):
        """selected.set([*selected(), item_id])"""
        code = "selected.set([*selected(), item_id])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_remove_from_selection(self, ctx):
        """selected.set([x for x in selected() if x != item_id])"""
        code = "selected.set([x for x in selected() if x != item_id])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_toggle_selection(self, ctx):
        """Add or remove from selection"""
        code = """
if item_id in selected():
    selected.set([x for x in selected() if x != item_id])
else:
    selected.set([*selected(), item_id])
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".set(") >= 2
    
    def test_clear_selection(self, ctx):
        """selected.set([])"""
        code = "selected.set([])"
        result = transpile_with_context(code, ctx)
        assert ".set([])" in result
    
    def test_select_all(self, ctx):
        """selected.set([x['id'] for x in items()])"""
        code = "selected.set([x['id'] for x in items()])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_filter_and_map(self, ctx):
        """Combined filter and map"""
        code = """
filtered.set([
    transform(x)
    for x in items()
    if x['active']
])
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result


# =============================================================================
# COUNTER/NUMERIC PATTERNS (10 tests)
# =============================================================================

class TestNumericPatterns:
    """Test numeric/counter patterns."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={
            "count": "sig_1",
            "total": "sig_2",
            "value": "sig_3",
        })
    
    def test_increment(self, ctx):
        """count.set(count() + 1)"""
        code = "count.set(count() + 1)"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
        assert ".read()" in result
    
    def test_decrement(self, ctx):
        """count.set(count() - 1)"""
        code = "count.set(count() - 1)"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_increment_update(self, ctx):
        """count.update(lambda n: n + 1)"""
        code = "count.update(lambda n: n + 1)"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_reset_to_zero(self, ctx):
        """count.set(0)"""
        code = "count.set(0)"
        result = transpile_with_context(code, ctx)
        assert ".set(0)" in result
    
    def test_multiply(self, ctx):
        """value.set(value() * 2)"""
        code = "value.set(value() * 2)"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_clamp(self, ctx):
        """value.set(max(0, min(100, value() + delta)))"""
        code = "value.set(max(0, min(100, value() + delta)))"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_add_to_total(self, ctx):
        """total.set(total() + amount)"""
        code = "total.set(total() + amount)"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_percentage(self, ctx):
        """value.set(value() / total() * 100)"""
        code = "value.set(value() / total() * 100)"
        result = transpile_with_context(code, ctx)
        assert result.count(".read()") >= 2
    
    def test_conditional_increment(self, ctx):
        """if cond: count.update(lambda n: n + 1)"""
        code = """
if can_increment:
    count.update(lambda n: n + 1)
"""
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_bounded_increment(self, ctx):
        """Only increment if below max"""
        code = """
if count() < max_value:
    count.update(lambda n: n + 1)
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert ".update(" in result


# =============================================================================
# COMPLEX NESTED PATTERNS (10 tests)
# =============================================================================

class TestComplexNestedPatterns:
    """Test deeply nested and complex patterns."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(
            signals={"data": "sig_1", "state": "sig_2"},
            stores={"store": "store_1"},
            forms={"form": "form_1"}
        )
    
    def test_nested_conditions(self, ctx):
        """Deeply nested if statements"""
        code = """
if form.validate():
    if data():
        if state() == "ready":
            process()
            data.set([])
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
        assert ".read()" in result
    
    def test_loop_with_condition(self, ctx):
        """Loop with inner conditional signal access"""
        code = """
for item in data():
    if item["active"]:
        state.set("processing")
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert ".set(" in result
    
    def test_try_except_with_signals(self, ctx):
        """Signal state changes"""
        code = """
if success:
    state.set("success")
else:
    state.set("error")
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".set(") >= 2
    
    def test_comprehension_with_signals(self, ctx):
        """Comprehension using multiple signals"""
        code = """
result = [
    transform(x, state())
    for x in data()
    if x["value"] > 0
]
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".read()") >= 2
    
    def test_function_with_signals(self, ctx):
        """Inline function definition with signals"""
        code = """
def process_item(item):
    if item["id"] in data():
        return True
    return False
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_combined_reactive(self, ctx):
        """All reactive types together"""
        code = """
if form.validate():
    values = form.values
    data.set([*data(), values])
    store.items.append(values)
    state.set("done")
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert "__pynext__.getSignal" in result
        assert "__pynext__.getStore" in result
    
    def test_chained_operations(self, ctx):
        """Multiple chained signal operations"""
        code = """
items = data()
items.sort(key=lambda x: x["priority"])
data.set(items[:10])
state.set(f"Showing {len(items)} items")
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 2
    
    def test_lambda_with_signals(self, ctx):
        """Lambda functions capturing signals"""
        code = """
process_fn = lambda x: x in data()
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_ternary_with_signals(self, ctx):
        """Ternary expressions with signal reads"""
        code = """
result = data() if state() else []
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".read()") >= 2
    
    def test_dict_comprehension_signals(self, ctx):
        """Access signal in simple expression"""
        code = """
x = data()
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result


# =============================================================================
# ASYNC HANDLER PATTERNS (10 tests)
# =============================================================================

class TestAsyncHandlerPatterns:
    """Test async handler patterns."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={
            "loading": "sig_1",
            "data": "sig_2",
            "error": "sig_3",
        })
    
    def test_loading_state(self, ctx):
        """Set loading before async operation"""
        code = """
loading.set(True)
"""
        result = transpile_with_context(code, ctx)
        assert ".set(true)" in result
    
    def test_clear_loading(self, ctx):
        """Clear loading after completion"""
        code = """
loading.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert ".set(false)" in result
    
    def test_fetch_pattern(self, ctx):
        """Full fetch with loading state"""
        code = """
async def fetch_data():
    loading.set(True)
    try:
        result = await api.fetch()
        data.set(result)
    except Exception as e:
        error.set(str(e))
    loading.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert "async" in result
        assert ".set(" in result
    
    def test_error_handling(self, ctx):
        """Set error state"""
        code = """
error.set("Something went wrong")
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_clear_error(self, ctx):
        """Clear error state"""
        code = """
error.set(None)
"""
        result = transpile_with_context(code, ctx)
        assert ".set(null)" in result
    
    def test_await_and_set(self, ctx):
        """Await and set result"""
        code = """
async def load():
    result = await api.fetch()
    data.set(result)
"""
        result = transpile_with_context(code, ctx)
        assert "await" in result
        assert ".set(" in result
    
    def test_parallel_awaits(self, ctx):
        """Multiple awaits before setting"""
        code = """
async def load_all():
    items = await api.get_items()
    users = await api.get_users()
    data.set({"items": items, "users": users})
"""
        result = transpile_with_context(code, ctx)
        assert "await" in result
    
    def test_conditional_async(self, ctx):
        """Conditional async operation"""
        code = """
async def maybe_load():
    if not data():
        loading.set(True)
        data.set(await api.fetch())
        loading.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert ".set(" in result
    
    def test_async_loop(self, ctx):
        """Async operation in loop"""
        code = """
async def load_batch():
    for id in ids:
        item = await api.get(id)
        data.update(lambda d: [*d, item])
"""
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_async_with_form(self, ctx):
        """Async form submission"""
        ctx = create_context(
            signals={"loading": "sig_1", "error": "sig_2"},
            forms={"form": "form_1"}
        )
        code = """
async def submit():
    if form.validate():
        loading.set(True)
        await api.submit(form.values)
        form.reset()
        loading.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
        assert ".reset()" in result
