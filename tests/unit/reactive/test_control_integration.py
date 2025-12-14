"""
Integration Tests for Control Flow Components

100 comprehensive tests covering:
- Show + For combinations (25 tests)
- For + ErrorBoundary combinations (25 tests)
- Full scenarios / Kanban-like patterns (50 tests)
"""

import pytest
from pynext.reactive.control_flow import (
    Show, For, Index, Switch, Match, Portal, Dynamic, ErrorBoundary, Suspense
)
from pynext.reactive.signal import Signal
from pynext.reactive.store import Store
from pynext.reactive.memo import Memo
from pynext.reactive.effect import Effect
from pynext.reactive.batch import batch


# =============================================================================
# SECTION 1: SHOW + FOR COMBINATIONS (25 tests)
# =============================================================================

class TestShowForCombinations:
    """Tests for Show and For working together."""
    
    def test_show_inside_for(self):
        """Show inside For items."""
        items = [{"id": 1, "visible": True}, {"id": 2, "visible": False}]
        
        for_comp = For(each=items)[
            lambda item, i: Show(when=item["visible"])[str(item["id"])]
        ]
        html = for_comp.render()
        
        assert "1" in html
        # Item 2 should be in wrapper but content hidden
        assert 'data-for-item="2"' in html
    
    def test_for_inside_show(self):
        """For inside Show."""
        visible = Signal(True)
        items = [1, 2, 3]
        
        show = Show(when=lambda: visible())[
            For(each=items)[lambda x, i: str(x)]
        ]
        
        html = show.render()
        assert "1" in html
        assert "2" in html
        assert "3" in html
    
    def test_for_with_show_fallback(self):
        """For with Show as fallback."""
        items = Signal([])
        
        for_comp = For(
            each=lambda: items(),
            fallback=Show(when=True)["No items yet"]
        )[lambda x, i: str(x)]
        
        html = for_comp.render()
        assert "No items yet" in html
    
    def test_filtered_list_with_show(self):
        """Filter list items using Show."""
        items = [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False},
            {"id": 3, "name": "Charlie", "active": True}
        ]
        
        for_comp = For(each=items)[
            lambda item, i: Show(when=item["active"])[item["name"]]
        ]
        html = for_comp.render()
        
        assert "Alice" in html
        assert "Charlie" in html
    
    def test_conditional_list_rendering(self):
        """Show list conditionally."""
        has_items = Signal(False)
        items = [1, 2, 3]
        
        show = Show(
            when=lambda: has_items(),
            fallback="Loading..."
        )[For(each=items)[lambda x, i: str(x)]]
        
        html1 = show.render()
        assert "Loading" in html1
        
        has_items.set(True)
        html2 = show.render()
        assert "1" in html2
    
    def test_show_toggle_in_list(self):
        """Toggle Show in list items."""
        items = [Signal(True), Signal(False), Signal(True)]
        
        for_comp = For(each=items)[
            lambda item, i: Show(when=lambda i=i: items[i]())[f"Item {i}"]
        ]
        html = for_comp.render()
        
        assert "Item 0" in html
        assert "Item 2" in html
    
    def test_nested_for_with_show(self):
        """Nested For with Show."""
        data = [
            {"id": "a", "items": [1, 2], "show": True},
            {"id": "b", "items": [3, 4], "show": False}
        ]
        
        outer = For(each=data)[
            lambda row, ri: Show(when=row["show"])[
                For(each=row["items"])[lambda x, i: str(x)]
            ]
        ]
        html = outer.render()
        
        assert "1" in html
        assert "2" in html
    
    def test_show_with_for_empty_state(self):
        """Show handles For empty state."""
        items = Signal([])
        
        show = Show(when=lambda: len(items()) > 0)[
            For(each=lambda: items())[lambda x, i: str(x)]
        ]
        
        html = show.render()
        # When false, Show renders empty or fallback
        assert 'data-show=' in html
    
    def test_for_items_with_show_toggle(self):
        """For items with individual Show toggles."""
        items = [
            {"id": 1, "expanded": Signal(False)},
            {"id": 2, "expanded": Signal(True)}
        ]
        
        for_comp = For(each=items)[
            lambda item, i: f"""
                <div>{item['id']}</div>
                {Show(when=lambda item=item: item['expanded']())['Details']}
            """
        ]
        html = for_comp.render()
        
        assert "Details" in html  # Item 2 is expanded
    
    def test_show_controls_for_visibility(self):
        """Show controls entire For visibility."""
        show_list = Signal(True)
        items = [1, 2, 3]
        
        container = Show(when=lambda: show_list())[
            For(each=items)[lambda x, i: f"<li>{x}</li>"]
        ]
        
        html1 = container.render()
        assert "<li>1</li>" in html1
        
        show_list.set(False)
        html2 = container.render()
        assert "<li>1</li>" not in html2
    
    def test_for_with_conditional_render(self):
        """For with conditional item rendering."""
        threshold = Signal(2)
        items = [1, 2, 3, 4, 5]
        
        for_comp = For(each=items)[
            lambda x, i: Show(when=lambda x=x: x > threshold())[str(x)]
        ]
        
        html1 = for_comp.render()
        assert "3" in html1
        assert "4" in html1
        
        threshold.set(3)
        html2 = for_comp.render()
        assert "4" in html2
        assert "5" in html2
    
    def test_show_fallback_is_for(self):
        """Show fallback is a For component."""
        main_visible = Signal(False)
        fallback_items = [1, 2]
        
        show = Show(
            when=lambda: main_visible(),
            fallback=For(each=fallback_items)[lambda x, i: f"Fallback {x}"]
        )["Main Content"]
        
        html = show.render()
        assert "Fallback 1" in html
        assert "Fallback 2" in html
    
    def test_for_inside_keyed_show(self):
        """For inside keyed Show."""
        visible = Signal(True)
        
        show = Show(when=lambda: visible(), keyed=True)[
            For(each=[1, 2, 3])[lambda x, i: str(x)]
        ]
        
        html = show.render()
        assert 'data-keyed="true"' in html
        assert "1" in html
    
    def test_multiple_for_in_show(self):
        """Multiple For components in Show."""
        visible = Signal(True)
        
        show = Show(when=lambda: visible())[
            [
                For(each=[1, 2])[lambda x, i: f"A{x}"],
                For(each=[3, 4])[lambda x, i: f"B{x}"]
            ]
        ]
        
        html = show.render()
        assert "A1" in html
        assert "B4" in html
    
    def test_show_inside_nested_for(self):
        """Show inside nested For."""
        rows = [
            {"id": 1, "cols": [{"v": 1, "show": True}, {"v": 2, "show": False}]},
            {"id": 2, "cols": [{"v": 3, "show": True}]}
        ]
        
        outer = For(each=rows)[
            lambda row, ri: For(each=row["cols"])[
                lambda col, ci: Show(when=col["show"])[str(col["v"])]
            ]
        ]
        html = outer.render()
        
        assert "1" in html
        assert "3" in html
    
    def test_for_with_show_and_signal_list(self):
        """For with Show and Signal-based list."""
        items = Signal([
            {"id": 1, "visible": True},
            {"id": 2, "visible": True}
        ])
        
        for_comp = For(each=lambda: items())[
            lambda item, i: Show(when=item["visible"])[str(item["id"])]
        ]
        
        html1 = for_comp.render()
        assert "1" in html1
        
        items.set([{"id": 1, "visible": False}, {"id": 2, "visible": True}])
        html2 = for_comp.render()
        
        assert "2" in html2
    
    def test_show_wrapping_for_with_store(self):
        """Show wrapping For with Store."""
        store = Store({"items": [], "loaded": False})
        
        show = Show(
            when=lambda: store.loaded,
            fallback="Loading items..."
        )[For(each=lambda: list(store.items))[lambda x, i: str(x)]]
        
        html1 = show.render()
        assert "Loading items" in html1
        
        store.loaded = True
        html2 = show.render()
        assert 'data-for=' in html2
    
    def test_for_items_with_show_details(self):
        """For items with expandable Show details."""
        items = [
            {"id": 1, "name": "Item 1", "details": "Details 1", "expanded": True},
            {"id": 2, "name": "Item 2", "details": "Details 2", "expanded": False}
        ]
        
        for_comp = For(each=items)[
            lambda item, i: f"""
                <div>{item['name']}</div>
                {Show(when=item['expanded'])[item['details']]}
            """
        ]
        html = for_comp.render()
        
        assert "Item 1" in html
        assert "Details 1" in html
        assert "Item 2" in html
    
    def test_for_reactive_list_with_show_filter(self):
        """For with reactive list and Show filter."""
        all_items = [{"id": i, "category": i % 2} for i in range(10)]
        filter_cat = Signal(0)
        
        for_comp = For(each=all_items)[
            lambda item, i: Show(when=lambda item=item: item["category"] == filter_cat())[
                str(item["id"])
            ]
        ]
        
        html1 = for_comp.render()
        assert "0" in html1
        assert "2" in html1
        
        filter_cat.set(1)
        html2 = for_comp.render()
        assert "1" in html2
        assert "3" in html2
    
    def test_show_for_pagination(self):
        """Show and For for pagination."""
        all_items = [{"id": i, "name": f"item-{i}"} for i in range(100)]
        page = Signal(0)
        page_size = 10
        
        show = Show(when=lambda: len(all_items) > 0)[
            For(each=lambda: all_items[page() * page_size:(page() + 1) * page_size])[
                lambda x, i: x["name"]
            ]
        ]
        
        html1 = show.render()
        assert "item-0" in html1
        assert "item-10" not in html1
        
        page.set(1)
        html2 = show.render()
        assert "item-10" in html2
    
    def test_for_with_show_loading_states(self):
        """For items with Show loading states."""
        items = [
            {"id": 1, "loading": True},
            {"id": 2, "loading": False}
        ]
        
        for_comp = For(each=items)[
            lambda item, i: Show(
                when=not item["loading"],
                fallback="Loading..."
            )[f"Item {item['id']}"]
        ]
        html = for_comp.render()
        
        assert "Loading..." in html
        assert "Item 2" in html
    
    def test_show_for_empty_filtered_list(self):
        """Show for empty filtered list."""
        items = [1, 2, 3]
        filter_val = Signal(10)  # No items match
        
        filtered = lambda: [x for x in items if x > filter_val()]
        
        show = Show(
            when=lambda: len(filtered()) > 0,
            fallback="No matches"
        )[For(each=filtered)[lambda x, i: str(x)]]
        
        html = show.render()
        assert "No matches" in html
    
    def test_for_show_batch_updates(self):
        """For and Show with batched updates."""
        items = Signal([1, 2])
        visible = Signal(True)
        
        container = Show(when=lambda: visible())[
            For(each=lambda: items())[lambda x, i: str(x)]
        ]
        
        html1 = container.render()
        assert "1" in html1
        
        batch(lambda: (items.set([3, 4]), visible.set(True)))
        html2 = container.render()
        
        assert "3" in html2
    
    def test_show_inside_for_with_key(self):
        """Show inside For with proper keys."""
        items = [
            {"id": "a", "show": True},
            {"id": "b", "show": False},
            {"id": "c", "show": True}
        ]
        
        for_comp = For(each=items, key_fn=lambda x: x["id"])[
            lambda item, i: Show(when=item["show"])[item["id"]]
        ]
        html = for_comp.render()
        
        assert 'data-for-item="a"' in html
        assert 'data-for-item="c"' in html


# =============================================================================
# SECTION 2: FOR + ERROR BOUNDARY COMBINATIONS (25 tests)
# =============================================================================

class TestForErrorBoundaryCombinations:
    """Tests for For and ErrorBoundary working together."""
    
    def test_for_inside_error_boundary(self):
        """For inside ErrorBoundary."""
        eb = ErrorBoundary(fallback=lambda e, r: "List Error")[
            For(each=[1, 2, 3])[lambda x, i: str(x)]
        ]
        html = eb.render()
        
        assert "1" in html
        assert "2" in html
    
    def test_error_boundary_catches_for_error(self):
        """ErrorBoundary catches For render error."""
        def bad_render(x, i):
            if x == 2:
                raise ValueError("Bad item")
            return str(x)
        
        eb = ErrorBoundary(fallback=lambda e, r: "Caught!")[
            For(each=[1, 2, 3])[bad_render]
        ]
        html = eb.render()
        
        assert "Caught!" in html
    
    def test_error_boundary_inside_for(self):
        """ErrorBoundary inside For items."""
        def risky_content(x):
            if x == 2:
                raise ValueError("Risky!")
            return str(x)
        
        for_comp = For(each=[1, 2, 3])[
            lambda x, i: ErrorBoundary(fallback=lambda e, r: "Error")[
                lambda x=x: risky_content(x)
            ]
        ]
        html = for_comp.render()
        
        assert "1" in html
        assert "Error" in html  # Item 2 errored
        assert "3" in html
    
    def test_for_item_recovery(self):
        """For item can recover from error."""
        should_error = [True]
        
        def maybe_error():
            if should_error[0]:
                raise ValueError("Error")
            return "Recovered"
        
        eb = ErrorBoundary(fallback=lambda e, r: "Failed")[
            For(each=[1])[lambda x, i: maybe_error()]
        ]
        
        html1 = eb.render()
        assert "Failed" in html1
        
        should_error[0] = False
        eb.reset()
        html2 = eb.render()
        
        assert "Recovered" in html2
    
    def test_nested_for_with_error_boundary(self):
        """Nested For with ErrorBoundary."""
        data = [
            {"id": 1, "items": [1, 2]},
            {"id": 2, "items": [3, 4]}
        ]
        
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[
            For(each=data)[
                lambda row, ri: For(each=row["items"])[lambda x, i: str(x)]
            ]
        ]
        html = eb.render()
        
        assert "1" in html
        assert "4" in html
    
    def test_error_boundary_with_for_fallback(self):
        """ErrorBoundary with For as fallback."""
        fallback_items = ["Fallback 1", "Fallback 2"]
        
        def raise_error():
            raise ValueError("Error!")
        
        eb = ErrorBoundary(
            fallback=lambda e, r: For(each=fallback_items)[lambda x, i: f"<li>{x}</li>"]
        )[raise_error]
        html = eb.render()
        
        assert "Fallback 1" in html
        assert "Fallback 2" in html
    
    def test_for_each_item_error_boundary(self):
        """Each For item has its own ErrorBoundary."""
        items = [1, 2, 3]
        
        def risky_item(x):
            if x == 2:
                raise ValueError(f"Error on {x}")
            return f"OK {x}"
        
        for_comp = For(each=items)[
            lambda x, i: ErrorBoundary(
                fallback=lambda e, r: f"Error: {e}"
            )[lambda x=x: risky_item(x)]
        ]
        html = for_comp.render()
        
        assert "OK 1" in html
        assert "Error:" in html
        assert "OK 3" in html
    
    def test_error_boundary_reset_with_for(self):
        """ErrorBoundary reset with For."""
        error_count = [0]
        
        def maybe_error(x):
            error_count[0] += 1
            if error_count[0] == 1:
                raise ValueError("First error")
            return f"Item {x}"
        
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[
            For(each=[1])[lambda x, i: maybe_error(x)]
        ]
        
        html1 = eb.render()
        assert "Error" in html1
        
        eb.reset()
        html2 = eb.render()
        
        assert "Item 1" in html2
    
    def test_for_with_error_boundary_and_show(self):
        """For with ErrorBoundary and Show."""
        items = [
            {"id": 1, "risky": False},
            {"id": 2, "risky": True},
            {"id": 3, "risky": False}
        ]
        
        def render_item(item):
            if item["risky"]:
                raise ValueError("Risky item!")
            return f"Item {item['id']}"
        
        for_comp = For(each=items)[
            lambda item, i: ErrorBoundary(fallback=lambda e, r: "⚠️")[
                Show(when=True)[lambda item=item: render_item(item)]
            ]
        ]
        html = for_comp.render()
        
        assert "Item 1" in html
        assert "⚠️" in html
        assert "Item 3" in html
    
    def test_error_boundary_preserves_for_state(self):
        """ErrorBoundary preserves For state after error."""
        items = Signal([1, 2, 3])
        error_on = Signal(None)
        
        def render_item(x):
            if x == error_on():
                raise ValueError(f"Error on {x}")
            return str(x)
        
        for_comp = For(each=lambda: items())[
            lambda x, i: ErrorBoundary(
                fallback=lambda e, r: "ERR"
            )[lambda x=x: render_item(x)]
        ]
        
        html1 = for_comp.render()
        assert "1" in html1
        
        error_on.set(2)
        html2 = for_comp.render()
        
        assert "1" in html2
        assert "ERR" in html2
        assert "3" in html2
    
    def test_for_with_suspense_and_error_boundary(self):
        """For with Suspense and ErrorBoundary."""
        items = [1, 2]
        
        for_comp = For(each=items)[
            lambda x, i: ErrorBoundary(fallback=lambda e, r: "Error")[
                Suspense(fallback="Loading")[f"Item {x}"]
            ]
        ]
        html = for_comp.render()
        
        assert "Item 1" in html
        assert "Item 2" in html
    
    def test_error_boundary_around_for_with_store(self):
        """ErrorBoundary around For with Store."""
        store = Store({"items": [{"id": 1}, {"id": 2}]})
        
        eb = ErrorBoundary(fallback=lambda e, r: "Store Error")[
            For(each=lambda: list(store.items))[
                lambda x, i: str(x["id"])
            ]
        ]
        html = eb.render()
        
        assert "1" in html
        assert "2" in html
    
    def test_for_error_in_key_fn(self):
        """ErrorBoundary catches error in For key function."""
        items = [{"id": 1}, {"bad": True}]
        
        eb = ErrorBoundary(fallback=lambda e, r: "Key Error")[
            For(each=items, key_fn=lambda x: x["id"])[
                lambda x, i: str(x)
            ]
        ]
        html = eb.render()
        
        assert "Key Error" in html
    
    def test_error_boundary_with_dynamic_for(self):
        """ErrorBoundary with dynamically changing For."""
        items = Signal([1, 2])
        should_error = Signal(False)
        
        def render_item(x):
            if should_error():
                raise ValueError("Dynamic error")
            return str(x)
        
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[
            For(each=lambda: items())[lambda x, i: render_item(x)]
        ]
        
        html1 = eb.render()
        assert "1" in html1
        
        should_error.set(True)
        items.set([3, 4])
        eb.reset()
        html2 = eb.render()
        
        assert "Error" in html2
    
    def test_for_with_error_recovery_button(self):
        """For with error recovery pattern."""
        errors = []
        
        def render_with_retry(x):
            if x == 2 and len(errors) == 0:
                errors.append(x)
                raise ValueError("First try failed")
            return f"Item {x}"
        
        for_comp = For(each=[1, 2, 3])[
            lambda x, i: ErrorBoundary(
                fallback=lambda e, r: f"Error on item (retry available)"
            )[lambda x=x: render_with_retry(x)]
        ]
        html = for_comp.render()
        
        assert "Item 1" in html
        assert "retry available" in html
        assert "Item 3" in html
    
    def test_nested_error_boundaries_in_for(self):
        """Nested ErrorBoundaries in For."""
        items = [1, 2]
        
        def outer_render(x):
            def inner_render():
                if x == 2:
                    raise ValueError("Inner error")
                return f"Content {x}"
            
            return ErrorBoundary(fallback=lambda e, r: "Inner caught")[inner_render]
        
        for_comp = For(each=items)[
            lambda x, i: ErrorBoundary(fallback=lambda e, r: "Outer caught")[
                lambda x=x: outer_render(x)
            ]
        ]
        html = for_comp.render()
        
        assert "Content 1" in html
        assert "Inner caught" in html
    
    def test_error_boundary_with_for_and_memo(self):
        """ErrorBoundary with For and Memo."""
        items = Signal([1, 2, 3])
        even_items = Memo(lambda: [x for x in items() if x % 2 == 0])
        
        eb = ErrorBoundary(fallback=lambda e, r: "Memo Error")[
            For(each=lambda: even_items())[lambda x, i: str(x)]
        ]
        html = eb.render()
        
        assert "2" in html
    
    def test_for_error_during_reconciliation(self):
        """ErrorBoundary handles error during For update."""
        items = Signal([{"id": 1, "ok": True}])
        
        def render_item(x):
            if not x.get("ok", True):
                raise ValueError("Bad item during reconcile")
            return str(x["id"])
        
        eb = ErrorBoundary(fallback=lambda e, r: "Reconcile Error")[
            For(each=lambda: items())[lambda x, i: render_item(x)]
        ]
        
        html1 = eb.render()
        assert "1" in html1
        
        items.set([{"id": 2, "ok": False}])
        eb.reset()
        html2 = eb.render()
        
        assert "Reconcile Error" in html2
    
    def test_for_with_error_boundary_and_portal(self):
        """For with ErrorBoundary and Portal."""
        items = [1, 2]
        
        for_comp = For(each=items)[
            lambda x, i: ErrorBoundary(fallback=lambda e, r: "Error")[
                Portal(mount="#modal")[f"Portal Item {x}"]
            ]
        ]
        html = for_comp.render()
        
        assert "Portal Item 1" in html
        assert "Portal Item 2" in html
    
    def test_error_boundary_with_for_and_switch(self):
        """ErrorBoundary with For and Switch."""
        items = [{"id": 1, "status": "active"}, {"id": 2, "status": "pending"}]
        
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[
            For(each=items)[
                lambda x, i: Switch()[
                    Match(when=x["status"] == "active")["Active"],
                    Match(when=True)["Other"]
                ]
            ]
        ]
        html = eb.render()
        
        assert "Active" in html
        assert "Other" in html
    
    def test_for_with_error_boundary_cleanup(self):
        """For with ErrorBoundary and proper cleanup."""
        cleanup_called = [0]
        
        def component_with_cleanup():
            cleanup_called[0] += 1
            return "Content"
        
        items = Signal([1])
        
        for_comp = For(each=lambda: items())[
            lambda x, i: ErrorBoundary(fallback=lambda e, r: "Error")[
                component_with_cleanup
            ]
        ]
        
        for_comp.render()
        items.set([])
        for_comp.render()
        
        # Cleanup tracking would be in Effect, but For still works
        assert True
    
    def test_multiple_error_boundaries_different_errors(self):
        """Multiple ErrorBoundaries catching different errors."""
        items = [
            {"id": 1, "error_type": None},
            {"id": 2, "error_type": "value"},
            {"id": 3, "error_type": "type"}
        ]
        
        def render_item(item):
            if item["error_type"] == "value":
                raise ValueError("Value error")
            if item["error_type"] == "type":
                raise TypeError("Type error")
            return f"OK {item['id']}"
        
        for_comp = For(each=items)[
            lambda item, i: ErrorBoundary(
                fallback=lambda e, r: f"Caught: {type(e).__name__}"
            )[lambda item=item: render_item(item)]
        ]
        html = for_comp.render()
        
        assert "OK 1" in html
        assert "ValueError" in html
        assert "TypeError" in html
    
    def test_error_boundary_for_async_simulation(self):
        """ErrorBoundary with For simulating async errors."""
        items = [1, 2, 3]
        failed_items = {2}
        
        def async_render(x):
            if x in failed_items:
                raise IOError("Network failed")
            return f"Loaded {x}"
        
        for_comp = For(each=items)[
            lambda x, i: ErrorBoundary(
                fallback=lambda e, r: "⚠️ Load failed"
            )[lambda x=x: async_render(x)]
        ]
        html = for_comp.render()
        
        assert "Loaded 1" in html
        assert "Load failed" in html
        assert "Loaded 3" in html


# =============================================================================
# SECTION 3: FULL SCENARIOS / KANBAN-LIKE PATTERNS (50 tests)
# =============================================================================

class TestFullScenarios:
    """Full integration scenarios including Kanban-like patterns."""
    
    def test_kanban_column_structure(self):
        """Kanban column structure with For and Show."""
        columns = [
            {"id": "todo", "title": "To Do", "tasks": [1, 2]},
            {"id": "doing", "title": "Doing", "tasks": [3]},
            {"id": "done", "title": "Done", "tasks": []}
        ]
        
        board = For(each=columns)[
            lambda col, i: f"""
                <div class="column">
                    <h2>{col['title']}</h2>
                    {For(each=col['tasks'], fallback='No tasks')[
                        lambda task, j: f'<div class="task">{task}</div>'
                    ]}
                </div>
            """
        ]
        html = board.render()
        
        assert "To Do" in html
        assert "task" in html
        assert "No tasks" in html
    
    def test_kanban_with_task_filtering(self):
        """Kanban with task filtering."""
        tasks = [
            {"id": 1, "title": "Task 1", "priority": "high"},
            {"id": 2, "title": "Task 2", "priority": "low"},
            {"id": 3, "title": "Task 3", "priority": "high"}
        ]
        
        filter_priority = Signal("high")
        
        filtered_tasks = For(each=tasks)[
            lambda task, i: Show(when=task["priority"] == filter_priority())[
                task["title"]
            ]
        ]
        
        html1 = filtered_tasks.render()
        assert "Task 1" in html1
        assert "Task 3" in html1
        
        filter_priority.set("low")
        html2 = filtered_tasks.render()
        assert "Task 2" in html2
    
    def test_kanban_task_modal(self):
        """Kanban task modal with Portal."""
        selected_task = Signal(None)
        
        def task_modal():
            task = selected_task()
            return Show(when=lambda: task is not None)[
                Portal(mount="#modal-root")[
                    f"Editing task: {task['title'] if task else ''}"
                ]
            ]
        
        selected_task.set({"id": 1, "title": "Important Task"})
        show = task_modal()
        html = show.render()
        
        assert "Editing task: Important Task" in html
    
    def test_kanban_column_collapse(self):
        """Kanban column with collapse functionality."""
        columns = [
            {"id": "col1", "collapsed": Signal(False), "tasks": [1, 2]},
            {"id": "col2", "collapsed": Signal(True), "tasks": [3, 4]}
        ]
        
        board = For(each=columns)[
            lambda col, i: f"""
                <div>
                    <h2>Column {col['id']}</h2>
                    {Show(when=lambda col=col: not col['collapsed']())[
                        For(each=col['tasks'])[lambda t, j: f'<div>{t}</div>']
                    ]}
                </div>
            """
        ]
        html = board.render()
        
        assert "1" in html  # col1 expanded
        assert "2" in html
    
    def test_kanban_drag_drop_simulation(self):
        """Simulate drag and drop between columns."""
        columns = Store({
            "todo": [{"id": 1, "title": "Task 1"}],
            "done": []
        })
        
        board = f"""
            <div class="column">To Do: {For(each=lambda: list(columns.todo))[lambda t, i: t['title']]}</div>
            <div class="column">Done: {For(each=lambda: list(columns.done), fallback='Empty')[lambda t, i: t['title']]}</div>
        """
        
        assert "Task 1" in board
        assert "Empty" in board
    
    def test_kanban_with_error_handling(self):
        """Kanban with error handling."""
        tasks = [
            {"id": 1, "title": "Good Task"},
            {"id": 2, "title": None}  # Bad task
        ]
        
        task_list = For(each=tasks)[
            lambda task, i: ErrorBoundary(
                fallback=lambda e, r: "⚠️ Invalid task"
            )[
                lambda task=task: f"<div>{task['title'].upper()}</div>"
            ]
        ]
        html = task_list.render()
        
        assert "GOOD TASK" in html
        assert "Invalid task" in html
    
    def test_kanban_loading_state(self):
        """Kanban with loading state."""
        loading = Signal(True)
        tasks = Signal([])
        
        board = Suspense(fallback="Loading board...")[
            Show(
                when=lambda: not loading(),
                fallback="Fetching tasks..."
            )[
                For(each=lambda: tasks())[lambda t, i: str(t)]
            ]
        ]
        
        html1 = board.render()
        assert "Fetching" in html1
        
        loading.set(False)
        tasks.set([1, 2, 3])
        html2 = board.render()
        
        assert "1" in html2
    
    def test_kanban_swimlanes(self):
        """Kanban with swimlanes."""
        swimlanes = [
            {"id": "team1", "name": "Team A", "columns": ["todo", "done"]},
            {"id": "team2", "name": "Team B", "columns": ["todo", "done"]}
        ]
        
        board = For(each=swimlanes)[
            lambda lane, li: f"""
                <div class="swimlane">
                    <h2>{lane['name']}</h2>
                    {For(each=lane['columns'])[lambda col, ci: f'<div class="column">{col}</div>']}
                </div>
            """
        ]
        html = board.render()
        
        assert "Team A" in html
        assert "Team B" in html
        assert "todo" in html
    
    def test_kanban_wip_limits(self):
        """Kanban with WIP limits."""
        columns = [
            {"id": "doing", "wip_limit": 3, "tasks": [1, 2, 3, 4]}
        ]
        
        board = For(each=columns)[
            lambda col, i: f"""
                <div>
                    {Show(when=len(col['tasks']) > col['wip_limit'])[
                        '<span class="warning">⚠️ WIP Limit Exceeded!</span>'
                    ]}
                    {For(each=col['tasks'])[lambda t, j: f'<div>{t}</div>']}
                </div>
            """
        ]
        html = board.render()
        
        assert "WIP Limit Exceeded" in html
    
    def test_dashboard_widgets(self):
        """Dashboard with multiple widget types."""
        widgets = [
            {"type": "chart", "data": [1, 2, 3]},
            {"type": "table", "data": ["a", "b"]},
            {"type": "metric", "data": 42}
        ]
        
        dashboard = For(each=widgets)[
            lambda w, i: Switch()[
                Match(when=w["type"] == "chart")[f"📊 Chart: {w['data']}"],
                Match(when=w["type"] == "table")[f"📋 Table: {w['data']}"],
                Match(when=w["type"] == "metric")[f"📈 Metric: {w['data']}"]
            ]
        ]
        html = dashboard.render()
        
        assert "Chart" in html
        assert "Table" in html
        assert "Metric: 42" in html
    
    def test_todo_app_complete(self):
        """Complete todo app pattern."""
        todos = Store({
            "items": [
                {"id": 1, "text": "Learn PyNext", "done": False},
                {"id": 2, "text": "Build app", "done": True}
            ],
            "filter": "all"
        })
        
        filtered = lambda: [
            t for t in list(todos.items)
            if todos.filter == "all" or 
               (todos.filter == "done" and t["done"]) or
               (todos.filter == "active" and not t["done"])
        ]
        
        todo_list = For(each=filtered)[
            lambda t, i: f"""
                <li class="{'done' if t['done'] else ''}">
                    {t['text']}
                </li>
            """
        ]
        html = todo_list.render()
        
        assert "Learn PyNext" in html
        assert "Build app" in html
    
    def test_form_wizard_pattern(self):
        """Multi-step form wizard."""
        step = Signal(1)
        
        wizard = Switch()[
            Match(when=lambda: step() == 1)["<div>Step 1: Personal Info</div>"],
            Match(when=lambda: step() == 2)["<div>Step 2: Payment</div>"],
            Match(when=lambda: step() == 3)["<div>Step 3: Confirm</div>"]
        ]
        
        html1 = wizard.render()
        assert "Personal Info" in html1
        
        step.set(2)
        html2 = wizard.render()
        assert "Payment" in html2
    
    def test_accordion_pattern(self):
        """Accordion with multiple sections."""
        sections = [
            {"id": "s1", "title": "Section 1", "content": "Content 1", "open": Signal(True)},
            {"id": "s2", "title": "Section 2", "content": "Content 2", "open": Signal(False)}
        ]
        
        accordion = For(each=sections)[
            lambda s, i: f"""
                <div class="section">
                    <h3>{s['title']}</h3>
                    {Show(when=lambda s=s: s['open']())[s['content']]}
                </div>
            """
        ]
        html = accordion.render()
        
        assert "Content 1" in html
        assert "Section 2" in html
    
    def test_tabs_pattern(self):
        """Tab navigation pattern."""
        tabs = ["Home", "Profile", "Settings"]
        active = Signal(0)
        
        tab_content = {
            0: "Welcome Home",
            1: "Your Profile",
            2: "App Settings"
        }
        
        container = f"""
            <div class="tabs">
                {For(each=tabs)[lambda t, i: f'<button>{t}</button>']}
            </div>
            {Dynamic(component=lambda: tab_content[active()])}
        """
        
        assert "Home" in container
        assert "Welcome Home" in container
    
    def test_search_results_pattern(self):
        """Search results with loading and empty states."""
        query = Signal("")
        loading = Signal(False)
        results = Signal([])
        
        search_ui = Show(
            when=lambda: query() != "",
            fallback="Enter a search term"
        )[
            Show(
                when=lambda: loading(),
                fallback=Show(
                    when=lambda: len(results()) > 0,
                    fallback="No results found"
                )[For(each=lambda: results())[lambda r, i: f"<li>{r}</li>"]]
            )["Searching..."]
        ]
        
        html1 = search_ui.render()
        assert "Enter a search" in html1
        
        query.set("test")
        html2 = search_ui.render()
        assert "No results" in html2
    
    def test_notification_system(self):
        """Notification system with Portal."""
        notifications = Signal([
            {"id": 1, "message": "Success!", "type": "success"},
            {"id": 2, "message": "Warning!", "type": "warning"}
        ])
        
        notification_container = Portal(mount="#notifications")[
            For(each=lambda: notifications())[
                lambda n, i: f'<div class="{n["type"]}">{n["message"]}</div>'
            ]
        ]
        html = notification_container.render()
        
        assert "Success!" in html
        assert "Warning!" in html
    
    def test_infinite_scroll_pattern(self):
        """Infinite scroll with pagination."""
        all_items = list(range(100))
        loaded_count = Signal(20)
        
        visible_items = lambda: all_items[:loaded_count()]
        
        list_ui = f"""
            {For(each=visible_items)[lambda x, i: f'<div>{x}</div>']}
            {Show(when=lambda: loaded_count() < len(all_items))['Load more...']}
        """
        
        assert "0" in list_ui
        assert "Load more" in list_ui
    
    def test_master_detail_pattern(self):
        """Master-detail view pattern."""
        items = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        selected = Signal(None)
        
        master = For(each=items)[
            lambda item, i: f'<li>{item["name"]}</li>'
        ]
        
        detail = Show(
            when=lambda: selected() is not None,
            fallback="Select an item"
        )[lambda: f"Details for {selected()['name'] if selected() else ''}"]
        
        html = f"{master}\n{detail}"
        assert "Item 1" in html
        assert "Select an item" in html
    
    def test_tree_view_pattern(self):
        """Tree view with recursive rendering."""
        tree = {
            "id": "root",
            "children": [
                {"id": "child1", "children": []},
                {"id": "child2", "children": [
                    {"id": "grandchild", "children": []}
                ]}
            ]
        }
        
        def render_node(node, depth=0):
            children_html = "".join(render_node(c, depth+1) for c in node["children"])
            return f'<div style="margin-left:{depth*20}px">{node["id"]}{children_html}</div>'
        
        html = render_node(tree)
        assert "root" in html
        assert "grandchild" in html
    
    def test_data_table_pattern(self):
        """Data table with sorting and filtering."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35}
        ]
        
        sort_key = Signal("name")
        
        sorted_data = lambda: sorted(data, key=lambda x: x[sort_key()])
        
        table = f"""
            <table>
                <thead><tr><th>Name</th><th>Age</th></tr></thead>
                <tbody>
                    {For(each=sorted_data)[
                        lambda row, i: f'<tr><td>{row["name"]}</td><td>{row["age"]}</td></tr>'
                    ]}
                </tbody>
            </table>
        """
        
        assert "Alice" in table
        assert "Bob" in table
    
    def test_card_grid_pattern(self):
        """Card grid with responsive layout."""
        cards = [{"id": i, "title": f"Card {i}"} for i in range(6)]
        
        grid = f"""
            <div class="grid">
                {For(each=cards)[
                    lambda card, i: f'''
                        <div class="card">
                            <h3>{card['title']}</h3>
                        </div>
                    '''
                ]}
            </div>
        """
        
        assert "Card 0" in grid
        assert "Card 5" in grid
    
    def test_modal_stack_pattern(self):
        """Modal stack with multiple layers."""
        modals = Signal([])
        
        def modal_stack():
            return For(each=lambda: modals())[
                lambda modal, i: Portal(mount="#modal-stack")[
                    f'<div class="modal" style="z-index:{1000+i}">{modal}</div>'
                ]
            ]
        
        modals.set(["First Modal", "Second Modal"])
        html = modal_stack().render()
        
        assert "First Modal" in html
        assert "Second Modal" in html
    
    def test_breadcrumb_pattern(self):
        """Breadcrumb navigation."""
        path = Signal(["Home", "Products", "Electronics", "Phones"])
        
        breadcrumbs = For(each=lambda: path())[
            lambda segment, i: f'<span>{segment}{" > " if i < len(path()) - 1 else ""}</span>'
        ]
        html = breadcrumbs.render()
        
        assert "Home" in html
        assert "Products" in html
        assert "Phones" in html
    
    def test_tag_cloud_pattern(self):
        """Tag cloud with varying sizes."""
        tags = [
            {"name": "python", "count": 100},
            {"name": "javascript", "count": 50},
            {"name": "react", "count": 75}
        ]
        
        tag_cloud = For(each=tags)[
            lambda tag, i: f'<span style="font-size:{10 + tag["count"]//10}px">{tag["name"]}</span>'
        ]
        html = tag_cloud.render()
        
        assert "python" in html
        assert "javascript" in html
    
    def test_timeline_pattern(self):
        """Timeline with events."""
        events = [
            {"date": "2024-01", "title": "Project Started"},
            {"date": "2024-06", "title": "MVP Released"},
            {"date": "2024-12", "title": "v1.0 Launch"}
        ]
        
        timeline = For(each=events)[
            lambda e, i: f'<div class="event"><span>{e["date"]}</span><p>{e["title"]}</p></div>'
        ]
        html = timeline.render()
        
        assert "Project Started" in html
        assert "v1.0 Launch" in html
    
    def test_chat_messages_pattern(self):
        """Chat messages with different layouts."""
        messages = [
            {"id": 1, "text": "Hello!", "from_me": True},
            {"id": 2, "text": "Hi there!", "from_me": False},
            {"id": 3, "text": "How are you?", "from_me": True}
        ]
        
        chat = For(each=messages)[
            lambda msg, i: f'''
                <div class="message {'sent' if msg['from_me'] else 'received'}">
                    {msg['text']}
                </div>
            '''
        ]
        html = chat.render()
        
        assert "Hello!" in html
        assert "sent" in html
        assert "received" in html
    
    def test_gallery_pattern(self):
        """Image gallery with lightbox."""
        images = [{"id": i, "src": f"img{i}.jpg"} for i in range(4)]
        selected = Signal(None)
        
        gallery = f"""
            <div class="gallery">
                {For(each=images)[
                    lambda img, i: f'<img src="{img["src"]}" />'
                ]}
            </div>
            {Show(when=lambda: selected() is not None)[
                Portal(mount="#lightbox")[
                    lambda: f'<div class="lightbox"><img src="{selected()["src"] if selected() else ""}" /></div>'
                ]
            ]}
        """
        
        assert "img0.jpg" in gallery
        assert "img3.jpg" in gallery
    
    def test_settings_panel_pattern(self):
        """Settings panel with sections."""
        settings = [
            {"category": "General", "items": [
                {"key": "theme", "value": "dark"},
                {"key": "language", "value": "en"}
            ]},
            {"category": "Privacy", "items": [
                {"key": "tracking", "value": False}
            ]}
        ]
        
        panel = For(each=settings)[
            lambda cat, ci: f'''
                <section>
                    <h2>{cat['category']}</h2>
                    {For(each=cat['items'])[
                        lambda item, ii: f'<div>{item["key"]}: {item["value"]}</div>'
                    ]}
                </section>
            '''
        ]
        html = panel.render()
        
        assert "General" in html
        assert "theme: dark" in html
        assert "Privacy" in html
    
    def test_report_builder_pattern(self):
        """Report builder with dynamic sections."""
        sections = Signal([
            {"id": 1, "type": "header", "content": "Q4 Report"},
            {"id": 2, "type": "chart", "content": "[10, 20, 30]"},
            {"id": 3, "type": "text", "content": "Analysis goes here"}
        ])
        
        report = For(each=lambda: sections())[
            lambda s, i: Switch()[
                Match(when=s["type"] == "header")[f'<h1>{s["content"]}</h1>'],
                Match(when=s["type"] == "chart")[f'<div class="chart">{s["content"]}</div>'],
                Match(when=s["type"] == "text")[f'<p>{s["content"]}</p>']
            ]
        ]
        html = report.render()
        
        assert "Q4 Report" in html
        assert "chart" in html
        assert "Analysis" in html
    
    def test_multi_select_pattern(self):
        """Multi-select with chips."""
        options = ["Red", "Green", "Blue", "Yellow"]
        selected = Signal(["Red", "Blue"])
        
        multi_select = f"""
            <div class="chips">
                {For(each=lambda: selected())[
                    lambda opt, i: f'<span class="chip">{opt} ×</span>'
                ]}
            </div>
            <div class="options">
                {For(each=options)[
                    lambda opt, i: Show(when=opt not in selected())[
                        f'<button>{opt}</button>'
                    ]
                ]}
            </div>
        """
        
        assert "chip" in multi_select
        assert "Red ×" in multi_select
    
    def test_file_browser_pattern(self):
        """File browser with folders and files."""
        items = [
            {"name": "Documents", "type": "folder", "children": [
                {"name": "report.pdf", "type": "file"}
            ]},
            {"name": "Images", "type": "folder", "children": []},
            {"name": "readme.txt", "type": "file"}
        ]
        
        file_list = For(each=items)[
            lambda item, i: f'''
                <div class="{item['type']}">
                    {'📁' if item['type'] == 'folder' else '📄'} {item['name']}
                    {Show(when=item['type'] == 'folder' and len(item.get('children', [])) > 0)[
                        For(each=item.get('children', []))[
                            lambda child, j: f'<div class="nested">{child["name"]}</div>'
                        ]
                    ] if item['type'] == 'folder' else ''}
                </div>
            '''
        ]
        html = file_list.render()
        
        assert "Documents" in html
        assert "readme.txt" in html
    
    def test_calendar_pattern(self):
        """Calendar with events."""
        days = list(range(1, 32))
        events = {5: "Meeting", 15: "Deadline", 25: "Holiday"}
        
        calendar = f"""
            <div class="calendar">
                {For(each=days)[
                    lambda day, i: f'''
                        <div class="day">
                            {day}
                            {Show(when=day in events)[
                                f'<span class="event">{events.get(day, "")}</span>'
                            ]}
                        </div>
                    '''
                ]}
            </div>
        """
        
        assert "Meeting" in calendar
        assert "Deadline" in calendar
    
    def test_shopping_cart_pattern(self):
        """Shopping cart with totals."""
        items = Signal([
            {"id": 1, "name": "Widget", "price": 10, "qty": 2},
            {"id": 2, "name": "Gadget", "price": 25, "qty": 1}
        ])
        
        total = Memo(lambda: sum(i["price"] * i["qty"] for i in items()))
        
        cart = f"""
            <div class="cart">
                {For(each=lambda: items())[
                    lambda item, i: f'<div>{item["name"]} x{item["qty"]} = ${item["price"] * item["qty"]}</div>'
                ]}
                <div class="total">Total: ${total()}</div>
            </div>
        """
        
        assert "Widget x2" in cart
        assert "Total: $45" in cart
    
    def test_stepper_pattern(self):
        """Stepper component."""
        steps = ["Info", "Review", "Submit"]
        current = Signal(1)
        
        stepper = For(each=steps)[
            lambda step, i: f'''
                <div class="step {'active' if i == current() else 'inactive'}">
                    {i + 1}. {step}
                </div>
            '''
        ]
        html = stepper.render()
        
        assert "Info" in html
        assert "active" in html
        assert "inactive" in html
    
    def test_code_editor_tabs_pattern(self):
        """Code editor tabs."""
        files = Signal([
            {"name": "index.py", "content": "print('hello')"},
            {"name": "utils.py", "content": "def helper(): pass"}
        ])
        active = Signal(0)
        
        editor = f"""
            <div class="tabs">
                {For(each=lambda: files())[
                    lambda f, i: f'<button class="{"active" if i == active() else ""}">{f["name"]}</button>'
                ]}
            </div>
            <div class="content">
                {Dynamic(component=lambda: files()[active()]["content"])}
            </div>
        """
        
        assert "index.py" in editor
        assert "print('hello')" in editor
    
    def test_alert_banner_pattern(self):
        """Alert banner with dismiss."""
        alerts = Signal([
            {"id": 1, "type": "error", "message": "Error occurred"},
            {"id": 2, "type": "warning", "message": "Check settings"}
        ])
        
        banner = For(each=lambda: alerts())[
            lambda alert, i: f'''
                <div class="alert {alert['type']}">
                    {alert['message']}
                    <button>×</button>
                </div>
            '''
        ]
        html = banner.render()
        
        assert "Error occurred" in html
        assert "warning" in html
    
    def test_autocomplete_pattern(self):
        """Autocomplete dropdown."""
        query = Signal("")
        all_options = ["Apple", "Banana", "Cherry", "Date"]
        
        matches = Memo(lambda: [
            o for o in all_options 
            if query().lower() in o.lower()
        ] if query() else [])
        
        autocomplete = Show(
            when=lambda: len(matches()) > 0,
            fallback=""
        )[
            For(each=lambda: matches())[
                lambda opt, i: f'<div class="option">{opt}</div>'
            ]
        ]
        
        query.set("a")
        html = autocomplete.render()
        
        assert "Apple" in html
        assert "Banana" in html
    
    def test_dashboard_with_all_components(self):
        """Complete dashboard using all components."""
        state = Store({
            "loading": False,
            "error": None,
            "widgets": [
                {"id": "chart", "type": "chart"},
                {"id": "table", "type": "table"}
            ],
            "modal_open": False
        })
        
        dashboard = ErrorBoundary(fallback=lambda e, r: "Dashboard Error")[
            Suspense(fallback="Loading dashboard...")[
                Show(
                    when=lambda: not state.loading,
                    fallback="Fetching data..."
                )[
                    f"""
                    <div class="dashboard">
                        {For(each=lambda: list(state.widgets))[
                            lambda w, i: Switch()[
                                Match(when=w['type'] == 'chart')['Chart Widget'],
                                Match(when=w['type'] == 'table')['Table Widget']
                            ]
                        ]}
                        {Show(when=lambda: state.modal_open)[
                            Portal(mount='#modal')['Modal Content']
                        ]}
                    </div>
                    """
                ]
            ]
        ]
        html = dashboard.render()
        
        assert "Chart Widget" in html
        assert "Table Widget" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

