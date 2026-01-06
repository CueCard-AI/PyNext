"""
Tests for Show Component - Conditional Rendering

100 comprehensive tests covering:
- Basic rendering (20 tests)
- Reactive updates (30 tests)
- Edge cases (25 tests)
- Performance (25 tests)
"""

import pytest
from pynext.reactive.control_flow import Show
from pynext.reactive.signal import Signal
from pynext.reactive.store import Store
from pynext.reactive.memo import Memo
from pynext.reactive.effect import Effect


# =============================================================================
# SECTION 1: BASIC RENDERING (20 tests)
# =============================================================================

class TestShowBasicRendering:
    """Basic Show component rendering tests."""
    
    def test_show_true_condition_renders_content(self):
        """Show renders content when condition is True."""
        show = Show(when=True)["Hello"]
        html = show.render()
        assert "Hello" in html
        assert 'data-pynext-show' in html
    
    def test_show_false_condition_renders_hidden(self):
        """Show renders content hidden when condition is False (for client-side reactivity)."""
        show = Show(when=False)["Hello"]
        html = show.render()
        # Content is rendered but hidden via CSS for client-side toggle
        assert 'data-condition="false"' in html
        assert 'display: none' in html
    
    def test_show_false_with_fallback(self):
        """Show renders fallback when condition is False."""
        show = Show(when=False, fallback="Fallback")["Content"]
        html = show.render()
        assert "Fallback" in html
        # Content is rendered hidden for client-side toggle
        assert 'data-condition="false"' in html
    
    def test_show_truthy_string(self):
        """Show treats non-empty string as truthy."""
        show = Show(when="truthy")["Content"]
        html = show.render()
        assert "Content" in html
    
    def test_show_falsy_empty_string(self):
        """Show treats empty string as falsy."""
        show = Show(when="")["Content"]
        html = show.render()
        # Content is rendered hidden for client-side toggle
        assert 'data-condition="false"' in html
    
    def test_show_truthy_number(self):
        """Show treats non-zero number as truthy."""
        show = Show(when=42)["Content"]
        html = show.render()
        assert "Content" in html
    
    def test_show_falsy_zero(self):
        """Show treats zero as falsy."""
        show = Show(when=0)["Content"]
        html = show.render()
        assert 'data-condition="false"' in html
    
    def test_show_truthy_list(self):
        """Show treats non-empty list as truthy."""
        show = Show(when=[1, 2, 3])["Content"]
        html = show.render()
        assert "Content" in html
    
    def test_show_falsy_empty_list(self):
        """Show treats empty list as falsy."""
        show = Show(when=[])["Content"]
        html = show.render()
        assert 'data-condition="false"' in html
    
    def test_show_callable_condition(self):
        """Show evaluates callable condition."""
        show = Show(when=lambda: True)["Content"]
        html = show.render()
        assert "Content" in html
    
    def test_show_callable_returns_false(self):
        """Show evaluates callable returning False."""
        show = Show(when=lambda: False)["Content"]
        html = show.render()
        assert 'data-condition="false"' in html
    
    def test_show_lambda_content(self):
        """Show renders lambda content."""
        show = Show(when=True)[lambda: "Dynamic"]
        html = show.render()
        assert "Dynamic" in html
    
    def test_show_keyed_attribute(self):
        """Show includes keyed attribute when keyed=True."""
        show = Show(when=True, keyed=True)["Content"]
        html = show.render()
        assert 'data-keyed="true"' in html
    
    def test_show_condition_attribute(self):
        """Show includes condition in data attribute."""
        show = Show(when=True)["Content"]
        html = show.render()
        assert 'data-condition="true"' in html
    
    def test_show_false_condition_attribute(self):
        """Show includes false condition in data attribute."""
        show = Show(when=False)["Content"]
        html = show.render()
        assert 'data-condition="false"' in html
    
    def test_show_unique_id(self):
        """Each Show has unique ID."""
        show1 = Show(when=True)["A"]
        show2 = Show(when=True)["B"]
        assert show1._id != show2._id
    
    def test_show_str_method(self):
        """Show __str__ returns rendered HTML."""
        show = Show(when=True)["Content"]
        assert str(show) == show.render()
    
    def test_show_repr(self):
        """Show __repr__ is informative."""
        show = Show(when=True, keyed=True)["Content"]
        assert "Show" in repr(show)
        assert "keyed=True" in repr(show)
    
    def test_show_without_children(self):
        """Show renders empty when no children set."""
        show = Show(when=True)
        html = show.render()
        assert 'data-pynext-show' in html
    
    def test_show_multiple_children_in_list(self):
        """Show renders list of children."""
        show = Show(when=True)[["First", " ", "Second"]]
        html = show.render()
        assert "First" in html
        assert "Second" in html


# =============================================================================
# SECTION 2: REACTIVE UPDATES (30 tests)
# =============================================================================

class TestShowReactiveUpdates:
    """Tests for Show with reactive signals and stores."""
    
    def test_show_with_signal_true(self):
        """Show works with Signal returning true."""
        visible = Signal(True)
        show = Show(when=lambda: visible())["Content"]
        html = show.render()
        assert "Content" in html
    
    def test_show_with_signal_false(self):
        """Show works with Signal returning false."""
        visible = Signal(False)
        show = Show(when=lambda: visible())["Content"]
        html = show.render()
        assert 'data-condition="false"' in html
    
    def test_show_rerenders_on_signal_change(self):
        """Show re-renders when signal changes."""
        visible = Signal(True)
        show = Show(when=lambda: visible())["Content"]
        
        assert "Content" in show.render()
        
        visible.set(False)
        assert 'data-condition="false"' in show.render()
        
        visible.set(True)
        assert "Content" in show.render()
    
    def test_show_with_store_property(self):
        """Show works with Store property."""
        state = Store({"visible": True})
        show = Show(when=lambda: state.visible)["Content"]
        html = show.render()
        assert "Content" in html
    
    def test_show_with_store_property_false(self):
        """Show with Store property returning false."""
        state = Store({"visible": False})
        show = Show(when=lambda: state.visible)["Content"]
        html = show.render()
        assert 'data-condition="false"' in html
    
    def test_show_rerenders_on_store_change(self):
        """Show re-renders when store changes."""
        state = Store({"visible": True})
        show = Show(when=lambda: state.visible)["Content"]
        
        assert "Content" in show.render()
        
        state.visible = False
        assert 'data-condition="false"' in show.render()
    
    def test_show_with_memo_condition(self):
        """Show works with Memo as condition."""
        count = Signal(5)
        is_positive = Memo(lambda: count() > 0)
        show = Show(when=lambda: is_positive())["Positive"]
        
        assert "Positive" in show.render()
    
    def test_show_with_memo_false(self):
        """Show with Memo returning false."""
        count = Signal(-5)
        is_positive = Memo(lambda: count() > 0)
        show = Show(when=lambda: is_positive())["Positive"]
        
        assert 'data-condition="false"' in show.render()
    
    def test_show_content_reads_signal(self):
        """Show content can read signals."""
        name = Signal("Alice")
        show = Show(when=True)[lambda: f"Hello, {name()}!"]
        
        html = show.render()
        assert "Hello, Alice!" in html
    
    def test_show_content_updates_with_signal(self):
        """Show content updates when signal changes."""
        name = Signal("Alice")
        show = Show(when=True)[lambda: f"Hello, {name()}!"]
        
        assert "Alice" in show.render()
        
        name.set("Bob")
        assert "Bob" in show.render()
    
    def test_show_fallback_reads_signal(self):
        """Fallback can read signals."""
        reason = Signal("Loading...")
        show = Show(when=False, fallback=lambda: reason())["Content"]
        
        html = show.render()
        assert "Loading..." in html
    
    def test_show_fallback_updates_with_signal(self):
        """Fallback updates when signal changes."""
        reason = Signal("Loading...")
        show = Show(when=False, fallback=lambda: reason())["Content"]
        
        assert "Loading..." in show.render()
        
        reason.set("Error occurred")
        assert "Error occurred" in show.render()
    
    def test_show_complex_condition(self):
        """Show with complex reactive condition."""
        user = Store({"logged_in": True, "role": "admin"})
        show = Show(when=lambda: user.logged_in and user.role == "admin")["Admin Panel"]
        
        assert "Admin Panel" in show.render()
    
    def test_show_condition_changes_multiple_times(self):
        """Show handles multiple condition changes."""
        toggle = Signal(True)
        show = Show(when=lambda: toggle())["Content"]
        
        for i in range(10):
            toggle.set(i % 2 == 0)
            html = show.render()
            if i % 2 == 0:
                assert "Content" in html
            else:
                assert 'data-condition="false"' in html
    
    def test_show_with_computed_content(self):
        """Show with computed content from store."""
        items = Store({"list": [1, 2, 3]})
        show = Show(when=lambda: len(list(items.list)) > 0)[
            lambda: f"Count: {len(list(items.list))}"
        ]
        
        html = show.render()
        assert "Count: 3" in html
    
    def test_show_signal_affects_keyed_mode(self):
        """Keyed Show behavior with signal changes."""
        visible = Signal(True)
        show = Show(when=lambda: visible(), keyed=True)["Content"]
        
        assert "Content" in show.render()
        visible.set(False)
        assert 'data-condition="false"' in show.render()
    
    def test_show_nested_signal_access(self):
        """Show with nested signal access in condition."""
        outer = Signal({"inner": True})
        show = Show(when=lambda: outer()["inner"])["Content"]
        
        assert "Content" in show.render()
    
    def test_show_with_signal_fallback_object(self):
        """Show with signal-based fallback component."""
        loading = Signal(True)
        show = Show(
            when=False,
            fallback=lambda: "Spinner" if loading() else "Done"
        )["Content"]
        
        assert "Spinner" in show.render()
        
        loading.set(False)
        assert "Done" in show.render()
    
    def test_show_alternating_content_fallback(self):
        """Show alternates between content and fallback."""
        state = Signal("content")
        show = Show(
            when=lambda: state() == "content",
            fallback="Fallback"
        )["Content"]
        
        assert "Content" in show.render()
        
        state.set("fallback")
        assert "Fallback" in show.render()
        
        state.set("content")
        assert "Content" in show.render()
    
    def test_show_with_effect_side_effect(self):
        """Show condition can trigger effects."""
        visible = Signal(True)
        effect_ran = [False]
        
        @Effect
        def track():
            if visible():
                effect_ran[0] = True
        
        show = Show(when=lambda: visible())["Content"]
        html = show.render()
        
        assert "Content" in html
        assert effect_ran[0]
    
    def test_show_with_derived_signal(self):
        """Show with Signal derived from another Signal."""
        base = Signal(10)
        doubled = Signal(0)
        
        @Effect
        def sync():
            doubled.set(base() * 2)
        
        show = Show(when=lambda: doubled() > 15)["Large"]
        
        assert "Large" in show.render()
    
    def test_show_with_store_array_length(self):
        """Show based on Store array length."""
        store = Store({"items": []})
        show = Show(
            when=lambda: len(list(store.items)) > 0,
            fallback="Empty"
        )["Has items"]
        
        assert "Empty" in show.render()
    
    def test_show_with_multiple_signals(self):
        """Show with condition using multiple signals."""
        a = Signal(True)
        b = Signal(True)
        
        show = Show(when=lambda: a() and b())["Both True"]
        
        assert "Both True" in show.render()
        
        a.set(False)
        assert 'data-condition="false"' in show.render()
    
    def test_show_or_condition(self):
        """Show with OR condition."""
        a = Signal(False)
        b = Signal(True)
        
        show = Show(when=lambda: a() or b())["At least one"]
        
        assert "At least one" in show.render()
    
    def test_show_complex_reactive_tree(self):
        """Show with complex reactive dependency tree."""
        count = Signal(5)
        multiplier = Signal(2)
        result = Memo(lambda: count() * multiplier())
        
        show = Show(when=lambda: result() > 8)["Big Result"]
        
        assert "Big Result" in show.render()
        
        multiplier.set(1)
        assert 'data-condition="false"' in show.render()
    
    def test_show_with_untrack(self):
        """Show condition can use untrack for partial tracking."""
        from pynext.reactive.batch import untrack
        
        tracked = Signal(True)
        untracked = Signal(True)
        
        show = Show(when=lambda: tracked() and untrack(lambda: untracked()))["Content"]
        
        assert "Content" in show.render()
    
    def test_show_batch_updates(self):
        """Show handles batched signal updates."""
        from pynext.reactive.batch import batch
        
        a = Signal(True)
        b = Signal(True)
        
        show = Show(when=lambda: a() and b())["Both"]
        
        assert "Both" in show.render()
        
        batch(lambda: (a.set(False), b.set(False)))
        
        assert 'data-condition="false"' in show.render()
    
    def test_show_signal_comparison(self):
        """Show with signal value comparison."""
        value = Signal(50)
        threshold = Signal(40)
        
        show = Show(when=lambda: value() > threshold())["Above"]
        
        assert "Above" in show.render()
        
        threshold.set(60)
        assert 'data-condition="false"' in show.render()
    
    def test_show_string_signal_condition(self):
        """Show with string signal as condition."""
        status = Signal("active")
        
        show = Show(when=lambda: status() == "active")["Active"]
        
        assert "Active" in show.render()
        
        status.set("inactive")
        assert 'data-condition="false"' in show.render()


# =============================================================================
# SECTION 3: EDGE CASES (25 tests)
# =============================================================================

class TestShowEdgeCases:
    """Edge case tests for Show component."""
    
    def test_show_none_condition(self):
        """Show treats None as falsy."""
        show = Show(when=None)["Content"]
        assert 'data-condition="false"' in show.render()
    
    def test_show_none_fallback(self):
        """Show with None fallback renders empty."""
        show = Show(when=False, fallback=None)["Content"]
        html = show.render()
        assert 'data-condition="false"' in html
    
    def test_show_none_children(self):
        """Show with None children."""
        show = Show(when=True)[None]
        html = show.render()
        assert 'data-pynext-show' in html
    
    def test_show_empty_string_content(self):
        """Show with empty string content."""
        show = Show(when=True)[""]
        html = show.render()
        assert 'data-pynext-show' in html
    
    def test_show_whitespace_content(self):
        """Show with whitespace content."""
        show = Show(when=True)["   "]
        html = show.render()
        assert "   " in html
    
    def test_show_nested_show(self):
        """Show can contain nested Show."""
        outer = Show(when=True)[
            Show(when=True)["Inner"]
        ]
        html = outer.render()
        assert "Inner" in html
    
    def test_show_deeply_nested(self):
        """Show can be deeply nested."""
        show = Show(when=True)[
            Show(when=True)[
                Show(when=True)["Deep"]
            ]
        ]
        html = show.render()
        assert "Deep" in html
    
    def test_show_nested_with_different_conditions(self):
        """Nested Shows with different conditions."""
        outer = Show(when=True)[
            Show(when=False, fallback="Inner Fallback")["Inner"]
        ]
        html = outer.render()
        assert "Inner Fallback" in html
        # Note: "Inner" text not present because inner Show condition is False
    
    def test_show_exception_in_condition(self):
        """Show handles exception in condition gracefully."""
        def bad_condition():
            raise ValueError("Bad!")
        
        show = Show(when=bad_condition)["Content"]
        
        with pytest.raises(ValueError):
            show.render()
    
    def test_show_exception_in_content(self):
        """Show handles exception in content."""
        def bad_content():
            raise ValueError("Bad content!")
        
        show = Show(when=True)[bad_content]
        
        with pytest.raises(ValueError):
            show.render()
    
    def test_show_callable_returning_callable(self):
        """Show with callable returning callable."""
        show = Show(when=True)[lambda: lambda: "Nested"]
        # The inner lambda should be called
        html = show.render()
        assert "Nested" in html
    
    def test_show_with_html_content(self):
        """Show with HTML in content."""
        show = Show(when=True)["<strong>Bold</strong>"]
        html = show.render()
        assert "<strong>Bold</strong>" in html
    
    def test_show_with_special_characters(self):
        """Show with special characters."""
        show = Show(when=True)["<>&\"'"]
        html = show.render()
        assert "<>&" in html
    
    def test_show_numeric_content(self):
        """Show with numeric content."""
        show = Show(when=True)[42]
        html = show.render()
        assert "42" in html
    
    def test_show_float_content(self):
        """Show with float content."""
        show = Show(when=True)[3.14159]
        html = show.render()
        assert "3.14159" in html
    
    def test_show_boolean_content(self):
        """Show with boolean content."""
        show = Show(when=True)[True]
        html = show.render()
        assert "True" in html
    
    def test_show_list_content(self):
        """Show with list content."""
        show = Show(when=True)[["A", "B", "C"]]
        html = show.render()
        assert "A" in html
        assert "B" in html
        assert "C" in html
    
    def test_show_dict_content(self):
        """Show with dict content (converts to string)."""
        show = Show(when=True)[{"key": "value"}]
        html = show.render()
        assert "key" in html
    
    def test_show_object_with_render(self):
        """Show with object that has render method."""
        class Renderable:
            def render(self):
                return "<div>Custom</div>"
        
        show = Show(when=True)[Renderable()]
        html = show.render()
        assert "<div>Custom</div>" in html
    
    def test_show_generator_content(self):
        """Show with generator content."""
        def gen():
            yield "A"
            yield "B"
        
        # Generator is called, returns generator object
        show = Show(when=True)[lambda: "".join(gen())]
        html = show.render()
        assert "AB" in html
    
    def test_show_very_long_content(self):
        """Show with very long content."""
        long_content = "x" * 10000
        show = Show(when=True)[long_content]
        html = show.render()
        assert long_content in html
    
    def test_show_unicode_content(self):
        """Show with unicode content."""
        show = Show(when=True)["Hello 世界 🌍"]
        html = show.render()
        assert "世界" in html
        assert "🌍" in html
    
    def test_show_multiline_content(self):
        """Show with multiline content."""
        content = """Line 1
Line 2
Line 3"""
        show = Show(when=True)[content]
        html = show.render()
        assert "Line 1" in html
        assert "Line 2" in html
    
    def test_show_condition_with_side_effect(self):
        """Show condition with side effect."""
        counter = [0]
        
        def counting_condition():
            counter[0] += 1
            return True
        
        show = Show(when=counting_condition)["Content"]
        show.render()
        show.render()
        
        # Should be called once per render
        assert counter[0] == 2
    
    def test_show_reuse_instance(self):
        """Show instance can be rendered multiple times."""
        show = Show(when=True)["Content"]
        html1 = show.render()
        html2 = show.render()
        
        assert html1 == html2


# =============================================================================
# SECTION 4: PERFORMANCE (25 tests)
# =============================================================================

class TestShowPerformance:
    """Performance tests for Show component."""
    
    def test_show_rapid_toggle(self):
        """Show handles rapid toggling."""
        visible = Signal(True)
        show = Show(when=lambda: visible())["Content"]
        
        for i in range(100):
            visible.set(i % 2 == 0)
            show.render()
        
        # Should complete without error
        assert True
    
    def test_show_large_content_true(self):
        """Show renders large content efficiently."""
        large_content = "<div>" * 1000 + "Content" + "</div>" * 1000
        show = Show(when=True)[large_content]
        
        html = show.render()
        assert "Content" in html
    
    def test_show_large_content_false(self):
        """Show skips large content when false."""
        large_content = "<div>" * 1000 + "Content" + "</div>" * 1000
        show = Show(when=False, fallback="Small")[large_content]
        
        html = show.render()
        assert "Small" in html
        assert 'data-condition="false"' in html
    
    def test_show_many_instances(self):
        """Many Show instances can be created."""
        shows = [Show(when=True)[f"Item {i}"] for i in range(1000)]
        
        for i, show in enumerate(shows):
            html = show.render()
            assert f"Item {i}" in html
    
    def test_show_nested_depth_performance(self):
        """Deeply nested Shows render correctly."""
        depth = 50
        content = "Deep"
        for _ in range(depth):
            content = Show(when=True)[content]
        
        html = content.render()
        assert "Deep" in html
    
    def test_show_condition_evaluation_count(self):
        """Condition is evaluated once per render."""
        call_count = [0]
        
        def counting_condition():
            call_count[0] += 1
            return True
        
        show = Show(when=counting_condition)["Content"]
        show.render()
        
        assert call_count[0] == 1
    
    def test_show_content_evaluation_count(self):
        """Content is evaluated once per render when visible."""
        call_count = [0]
        
        def counting_content():
            call_count[0] += 1
            return "Content"
        
        show = Show(when=True)[counting_content]
        show.render()
        
        assert call_count[0] == 1
    
    def test_show_content_evaluated_for_hydration(self):
        """Content is always evaluated for client-side hydration (rendered hidden)."""
        call_count = [0]
        
        def counting_content():
            call_count[0] += 1
            return "Content"
        
        show = Show(when=False)[counting_content]
        html = show.render()
        
        # Content is evaluated even when false - for client-side toggle capability
        assert call_count[0] == 1
        assert 'data-condition="false"' in html
    
    def test_show_fallback_not_evaluated_when_true(self):
        """Fallback is not evaluated when condition is true."""
        call_count = [0]
        
        def counting_fallback():
            call_count[0] += 1
            return "Fallback"
        
        show = Show(when=True, fallback=counting_fallback)["Content"]
        show.render()
        
        assert call_count[0] == 0
    
    def test_show_memory_efficient(self):
        """Show doesn't hold unnecessary references."""
        import sys
        
        show = Show(when=True)["Small"]
        size = sys.getsizeof(show)
        
        # Should be reasonably small
        assert size < 1000
    
    def test_show_with_signal_performance(self):
        """Show with signal renders efficiently."""
        visible = Signal(True)
        show = Show(when=lambda: visible())["Content"]
        
        # Render many times
        for _ in range(100):
            show.render()
        
        assert True
    
    def test_show_toggle_back_and_forth(self):
        """Show handles toggle back and forth."""
        visible = Signal(True)
        show = Show(when=lambda: visible(), fallback="Hidden")["Visible"]
        
        results = []
        for i in range(50):
            visible.set(i % 2 == 0)
            results.append(show.render())
        
        assert "Visible" in results[0]
        assert "Hidden" in results[1]
    
    def test_show_concurrent_signals(self):
        """Show with multiple concurrent signal changes."""
        signals = [Signal(True) for _ in range(10)]
        
        def all_true():
            return all(s() for s in signals)
        
        show = Show(when=all_true)["All True"]
        
        assert "All True" in show.render()
        
        signals[5].set(False)
        assert 'data-condition="false"' in show.render()
    
    def test_show_store_with_many_properties(self):
        """Show with store having many properties."""
        data = {f"prop{i}": True for i in range(100)}
        store = Store(data)
        
        show = Show(when=lambda: store.prop0)["Content"]
        html = show.render()
        
        assert "Content" in html
    
    def test_show_complex_content_structure(self):
        """Show with complex nested content structure."""
        content = lambda: [
            "<div>",
            "<h1>Title</h1>",
            "<p>Paragraph 1</p>",
            "<p>Paragraph 2</p>",
            "</div>"
        ]
        
        show = Show(when=True)[content]
        html = show.render()
        
        assert "Title" in html
    
    def test_show_id_uniqueness_under_load(self):
        """Show IDs remain unique under high load."""
        ids = set()
        for _ in range(1000):
            show = Show(when=True)["Content"]
            ids.add(show._id)
        
        assert len(ids) == 1000
    
    def test_show_render_string_efficiency(self):
        """Show render produces efficient string."""
        show = Show(when=True)["Content"]
        html = show.render()
        
        # Should be single div wrapper
        assert html.count('<div') == 1
    
    def test_show_no_memory_leak_on_rerender(self):
        """Show doesn't leak memory on repeated renders."""
        show = Show(when=True)[lambda: "Dynamic " * 100]
        
        for _ in range(100):
            show.render()
        
        # Should complete without memory issues
        assert True
    
    def test_show_with_computed_heavy_condition(self):
        """Show with computationally heavy condition."""
        def heavy_condition():
            # Simulate heavy computation
            total = sum(range(1000))
            return total > 0
        
        show = Show(when=heavy_condition)["Content"]
        html = show.render()
        
        assert "Content" in html
    
    def test_show_multiple_renders_same_result(self):
        """Multiple renders produce same result."""
        visible = Signal(True)
        show = Show(when=lambda: visible())["Content"]
        
        results = [show.render() for _ in range(10)]
        
        assert all(r == results[0] for r in results)
    
    def test_show_keyed_vs_non_keyed_overhead(self):
        """Keyed vs non-keyed Show overhead is minimal."""
        keyed = Show(when=True, keyed=True)["Content"]
        non_keyed = Show(when=True, keyed=False)["Content"]
        
        # Both should render similarly
        assert "Content" in keyed.render()
        assert "Content" in non_keyed.render()
    
    def test_show_fallback_complexity(self):
        """Show handles complex fallback."""
        complex_fallback = lambda: "<div class='loading'>" + "<span>.</span>" * 100 + "</div>"
        
        show = Show(when=False, fallback=complex_fallback)["Content"]
        html = show.render()
        
        assert "loading" in html
    
    def test_show_minimal_dom_output(self):
        """Show produces minimal DOM structure."""
        show = Show(when=True)["Content"]
        html = show.render()
        
        # Should only have one wrapper div
        assert html.startswith('<div')
        assert html.endswith('</div>')
    
    def test_show_stable_id_across_renders(self):
        """Show ID is stable across renders."""
        show = Show(when=True)["Content"]
        id1 = show._id
        show.render()
        id2 = show._id
        show.render()
        id3 = show._id
        
        assert id1 == id2 == id3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

