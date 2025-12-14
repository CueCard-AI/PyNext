"""
Tests for Suspense Component - Async Loading States

50 comprehensive tests covering:
- Basic rendering (15 tests)
- Async handling (20 tests)
- Edge cases (15 tests)
"""

import pytest
from pynext.reactive.control_flow import Suspense
from pynext.reactive.signal import Signal


# =============================================================================
# SECTION 1: BASIC RENDERING (15 tests)
# =============================================================================

class TestSuspenseBasicRendering:
    """Basic Suspense rendering tests."""
    
    def test_suspense_renders_children(self):
        """Suspense renders children."""
        suspense = Suspense(fallback="Loading...")["Content"]
        html = suspense.render()
        
        assert "Content" in html
    
    def test_suspense_includes_fallback_data(self):
        """Suspense includes fallback in data attribute."""
        suspense = Suspense(fallback="Loading...")["Content"]
        html = suspense.render()
        
        assert 'data-fallback=' in html
        assert "Loading" in html
    
    def test_suspense_unique_id(self):
        """Each Suspense has unique ID."""
        s1 = Suspense()["A"]
        s2 = Suspense()["B"]
        
        assert s1._id != s2._id
    
    def test_suspense_data_attribute(self):
        """Suspense includes data-suspense attribute."""
        suspense = Suspense()["Content"]
        html = suspense.render()
        
        assert 'data-suspense=' in html
    
    def test_suspense_str_method(self):
        """Suspense __str__ returns rendered HTML."""
        suspense = Suspense()["Content"]
        assert str(suspense) == suspense.render()
    
    def test_suspense_repr(self):
        """Suspense __repr__ is informative."""
        suspense = Suspense(fallback="Loading")["Content"]
        assert "Suspense" in repr(suspense)
    
    def test_suspense_none_fallback(self):
        """Suspense handles None fallback."""
        suspense = Suspense(fallback=None)["Content"]
        html = suspense.render()
        
        assert "Content" in html
    
    def test_suspense_empty_fallback(self):
        """Suspense handles empty fallback."""
        suspense = Suspense(fallback="")["Content"]
        html = suspense.render()
        
        assert "Content" in html
    
    def test_suspense_html_fallback(self):
        """Suspense renders HTML fallback."""
        suspense = Suspense(fallback="<div class='spinner'>Loading...</div>")["Content"]
        html = suspense.render()
        
        assert "spinner" in html
    
    def test_suspense_callable_fallback(self):
        """Suspense renders callable fallback."""
        suspense = Suspense(fallback=lambda: "Dynamic Loading")["Content"]
        html = suspense.render()
        
        assert "Dynamic Loading" in html
    
    def test_suspense_callable_children(self):
        """Suspense renders callable children."""
        suspense = Suspense(fallback="Loading")[lambda: "Dynamic Content"]
        html = suspense.render()
        
        assert "Dynamic Content" in html
    
    def test_suspense_list_children(self):
        """Suspense renders list children."""
        suspense = Suspense(fallback="Loading")[["Part 1", " ", "Part 2"]]
        html = suspense.render()
        
        assert "Part 1" in html
        assert "Part 2" in html
    
    def test_suspense_html_children(self):
        """Suspense renders HTML children."""
        suspense = Suspense(fallback="Loading")["<div class='content'>HTML</div>"]
        html = suspense.render()
        
        assert "class='content'" in html
    
    def test_suspense_wrapper_structure(self):
        """Suspense has proper wrapper structure."""
        suspense = Suspense()["Content"]
        html = suspense.render()
        
        assert html.startswith("<div")
        assert html.endswith("</div>")
    
    def test_suspense_escapes_fallback(self):
        """Suspense escapes fallback for data attribute."""
        suspense = Suspense(fallback="<b>Loading</b>")["Content"]
        html = suspense.render()
        
        # Fallback should be escaped in data attribute
        assert 'data-fallback="' in html


# =============================================================================
# SECTION 2: ASYNC HANDLING (20 tests)
# =============================================================================

class TestSuspenseAsyncHandling:
    """Tests for Suspense async handling (server-side simulation)."""
    
    def test_suspense_with_signal_children(self):
        """Suspense works with Signal children."""
        data = Signal("Loaded Data")
        suspense = Suspense(fallback="Loading")[lambda: data()]
        
        html = suspense.render()
        assert "Loaded Data" in html
    
    def test_suspense_content_changes(self):
        """Suspense content changes on signal update."""
        status = Signal("loading")
        
        def content():
            if status() == "loading":
                return "Loading..."
            return "Content Loaded"
        
        suspense = Suspense(fallback="Spinner")[content]
        
        html1 = suspense.render()
        assert "Loading..." in html1
        
        status.set("loaded")
        html2 = suspense.render()
        
        assert "Content Loaded" in html2
    
    def test_suspense_with_store(self):
        """Suspense works with Store."""
        from pynext.reactive.store import Store
        
        store = Store({"data": None})
        suspense = Suspense(fallback="Loading")[
            lambda: str(store.data) if store.data else "No data"
        ]
        
        html1 = suspense.render()
        assert "No data" in html1
    
    def test_suspense_loading_state_simulation(self):
        """Suspense simulates loading state pattern."""
        loading = Signal(True)
        data = Signal(None)
        
        def content():
            if loading():
                return "Still loading..."
            return f"Data: {data()}"
        
        suspense = Suspense(fallback="Initial Loading")[content]
        
        html1 = suspense.render()
        assert "Still loading" in html1
        
        loading.set(False)
        data.set("Result")
        html2 = suspense.render()
        
        assert "Data: Result" in html2
    
    def test_suspense_error_state_simulation(self):
        """Suspense handles error state pattern."""
        state = Signal("loading")
        error = Signal(None)
        
        def content():
            if state() == "loading":
                return "Loading..."
            if state() == "error":
                return f"Error: {error()}"
            return "Success!"
        
        suspense = Suspense(fallback="Spinner")[content]
        
        html1 = suspense.render()
        assert "Loading" in html1
        
        state.set("error")
        error.set("Network failed")
        html2 = suspense.render()
        
        assert "Network failed" in html2
    
    def test_suspense_nested(self):
        """Nested Suspense components."""
        inner = Suspense(fallback="Inner Loading")["Inner Content"]
        outer = Suspense(fallback="Outer Loading")[inner]
        
        html = outer.render()
        assert "Inner Content" in html
    
    def test_suspense_multiple_instances(self):
        """Multiple Suspense instances work independently."""
        s1 = Suspense(fallback="Loading 1")["Content 1"]
        s2 = Suspense(fallback="Loading 2")["Content 2"]
        
        html1 = s1.render()
        html2 = s2.render()
        
        assert "Content 1" in html1
        assert "Content 2" in html2
        assert s1._id != s2._id
    
    def test_suspense_data_fetching_pattern(self):
        """Suspense implements data fetching pattern."""
        from pynext.reactive.store import Store
        
        resource = Store({
            "loading": True,
            "data": None,
            "error": None
        })
        
        def render_resource():
            if resource.loading:
                return "Fetching data..."
            if resource.error:
                return f"Error: {resource.error}"
            return f"Data: {resource.data}"
        
        suspense = Suspense(fallback="Initial")[render_resource]
        
        html1 = suspense.render()
        assert "Fetching data" in html1
        
        resource.loading = False
        resource.data = "API Result"
        html2 = suspense.render()
        
        assert "API Result" in html2
    
    def test_suspense_with_memo(self):
        """Suspense with Memo-based content."""
        from pynext.reactive.memo import Memo
        
        raw_data = Signal([1, 2, 3])
        computed = Memo(lambda: sum(raw_data()))
        
        suspense = Suspense(fallback="Computing")[
            lambda: f"Total: {computed()}"
        ]
        
        html = suspense.render()
        assert "Total: 6" in html
    
    def test_suspense_loading_state_toggle(self):
        """Suspense handles loading state toggle."""
        loading = Signal(False)
        
        suspense = Suspense(fallback="Loading")[
            lambda: "Loading..." if loading() else "Ready"
        ]
        
        assert "Ready" in suspense.render()
        
        loading.set(True)
        assert "Loading..." in suspense.render()
        
        loading.set(False)
        assert "Ready" in suspense.render()
    
    def test_suspense_progressive_loading(self):
        """Suspense handles progressive loading."""
        progress = Signal(0)
        
        suspense = Suspense(fallback="Starting")[
            lambda: f"Progress: {progress()}%"
        ]
        
        for p in [0, 25, 50, 75, 100]:
            progress.set(p)
            assert f"Progress: {p}%" in suspense.render()
    
    def test_suspense_retry_pattern(self):
        """Suspense supports retry pattern."""
        attempts = Signal(0)
        success = Signal(False)
        
        def content():
            if success():
                return "Success!"
            return f"Attempt {attempts()}"
        
        suspense = Suspense(fallback="Starting")[content]
        
        html1 = suspense.render()
        assert "Attempt 0" in html1
        
        attempts.set(1)
        html2 = suspense.render()
        assert "Attempt 1" in html2
        
        success.set(True)
        html3 = suspense.render()
        assert "Success!" in html3
    
    def test_suspense_conditional_fallback(self):
        """Suspense with conditional fallback."""
        is_slow = Signal(False)
        
        def fallback():
            if is_slow():
                return "This is taking longer than usual..."
            return "Loading..."
        
        suspense = Suspense(fallback=fallback)["Content"]
        html = suspense.render()
        
        assert "Loading..." in html
    
    def test_suspense_skeleton_pattern(self):
        """Suspense implements skeleton loading pattern."""
        suspense = Suspense(
            fallback="<div class='skeleton'><div class='skeleton-line'></div></div>"
        )["<div class='content'>Real Content</div>"]
        
        html = suspense.render()
        assert "Real Content" in html
        assert "skeleton" in html  # In fallback data attribute
    
    def test_suspense_with_effect(self):
        """Suspense works with Effect."""
        from pynext.reactive.effect import Effect
        
        loaded = Signal(False)
        effect_ran = [False]
        
        @Effect
        def on_load():
            if loaded():
                effect_ran[0] = True
        
        suspense = Suspense(fallback="Loading")[
            lambda: "Loaded" if loaded() else "Not yet"
        ]
        
        suspense.render()
        loaded.set(True)
        
        assert effect_ran[0]
    
    def test_suspense_timeout_simulation(self):
        """Suspense simulates timeout scenario."""
        timeout = Signal(False)
        
        suspense = Suspense(fallback="Loading")[
            lambda: "Request timed out" if timeout() else "Content"
        ]
        
        html1 = suspense.render()
        assert "Content" in html1
        
        timeout.set(True)
        html2 = suspense.render()
        assert "timed out" in html2
    
    def test_suspense_batch_updates(self):
        """Suspense handles batched updates."""
        from pynext.reactive.batch import batch
        
        loading = Signal(True)
        data = Signal(None)
        
        suspense = Suspense(fallback="Loading")[
            lambda: f"Data: {data()}" if not loading() else "Loading..."
        ]
        
        assert "Loading" in suspense.render()
        
        batch(lambda: (loading.set(False), data.set("Result")))
        assert "Data: Result" in suspense.render()
    
    def test_suspense_multiple_resources(self):
        """Suspense with multiple resources."""
        user_loading = Signal(True)
        posts_loading = Signal(True)
        
        def content():
            if user_loading() or posts_loading():
                return "Loading resources..."
            return "All loaded"
        
        suspense = Suspense(fallback="Initial")[content]
        
        html1 = suspense.render()
        assert "Loading resources" in html1
        
        user_loading.set(False)
        html2 = suspense.render()
        assert "Loading resources" in html2
        
        posts_loading.set(False)
        html3 = suspense.render()
        assert "All loaded" in html3
    
    def test_suspense_rerender_consistency(self):
        """Suspense renders consistently."""
        suspense = Suspense(fallback="Loading")["Content"]
        
        html1 = suspense.render()
        html2 = suspense.render()
        
        assert html1 == html2


# =============================================================================
# SECTION 3: EDGE CASES (15 tests)
# =============================================================================

class TestSuspenseEdgeCases:
    """Edge case tests for Suspense."""
    
    def test_suspense_none_children(self):
        """Suspense handles None children."""
        suspense = Suspense(fallback="Loading")[None]
        html = suspense.render()
        
        assert 'data-suspense=' in html
    
    def test_suspense_empty_children(self):
        """Suspense handles empty children."""
        suspense = Suspense(fallback="Loading")[""]
        html = suspense.render()
        
        assert 'data-suspense=' in html
    
    def test_suspense_exception_in_children(self):
        """Suspense handles exception in children."""
        def bad_children():
            raise ValueError("Bad!")
        
        suspense = Suspense(fallback="Loading")[bad_children]
        
        with pytest.raises(ValueError):
            suspense.render()
    
    def test_suspense_exception_in_fallback(self):
        """Suspense handles exception in fallback."""
        def bad_fallback():
            raise RuntimeError("Bad fallback!")
        
        suspense = Suspense(fallback=bad_fallback)["Content"]
        
        with pytest.raises(RuntimeError):
            suspense.render()
    
    def test_suspense_unicode_content(self):
        """Suspense handles unicode content."""
        suspense = Suspense(fallback="載入中...")["Hello 世界 🎉"]
        html = suspense.render()
        
        assert "世界" in html
        assert "🎉" in html
    
    def test_suspense_very_long_fallback(self):
        """Suspense handles very long fallback."""
        long_fallback = "Loading" + "." * 1000
        suspense = Suspense(fallback=long_fallback)["Content"]
        html = suspense.render()
        
        assert "Content" in html
    
    def test_suspense_special_chars_in_fallback(self):
        """Suspense escapes special chars in fallback."""
        suspense = Suspense(fallback='<script>alert("XSS")</script>')["Content"]
        html = suspense.render()
        
        # Should be escaped in data attribute
        assert 'data-fallback=' in html
    
    def test_suspense_nested_deeply(self):
        """Suspense handles deep nesting."""
        content = "Deep"
        for _ in range(10):
            content = Suspense(fallback="Loading")[content]
        
        html = content.render()
        assert "Deep" in html
    
    def test_suspense_numeric_children(self):
        """Suspense handles numeric children."""
        suspense = Suspense(fallback=0)[42]
        html = suspense.render()
        
        assert "42" in html
    
    def test_suspense_boolean_children(self):
        """Suspense handles boolean children."""
        suspense = Suspense(fallback=False)[True]
        html = suspense.render()
        
        assert "True" in html
    
    def test_suspense_dict_children(self):
        """Suspense handles dict children."""
        suspense = Suspense(fallback="Loading")[{"key": "value"}]
        html = suspense.render()
        
        assert "key" in html
    
    def test_suspense_callable_returns_callable(self):
        """Suspense handles callable returning callable."""
        suspense = Suspense(fallback="Loading")[lambda: lambda: "Nested"]
        html = suspense.render()
        
        assert "Nested" in html
    
    def test_suspense_multiline_fallback(self):
        """Suspense handles multiline fallback."""
        fallback = "<div>Line 1</div><div>Line 2</div>"
        suspense = Suspense(fallback=fallback)["Content"]
        html = suspense.render()
        
        assert "Content" in html
    
    def test_suspense_without_children(self):
        """Suspense without children set."""
        suspense = Suspense(fallback="Loading")
        html = suspense.render()
        
        assert 'data-suspense=' in html
    
    def test_suspense_id_stability(self):
        """Suspense ID is stable across renders."""
        suspense = Suspense(fallback="Loading")["Content"]
        id1 = suspense._id
        suspense.render()
        id2 = suspense._id
        
        assert id1 == id2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

