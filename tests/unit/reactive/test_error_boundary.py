"""
Tests for ErrorBoundary Component - Error Catching and Recovery

50 comprehensive tests covering:
- Catching errors (20 tests)
- Recovery (15 tests)
- Edge cases (15 tests)
"""

import pytest
from pynext.reactive.control_flow import ErrorBoundary
from pynext.reactive.signal import Signal


# =============================================================================
# SECTION 1: CATCHING ERRORS (20 tests)
# =============================================================================

class TestErrorBoundaryCatching:
    """Tests for ErrorBoundary catching errors."""
    
    def test_error_boundary_renders_content(self):
        """ErrorBoundary renders content when no error."""
        eb = ErrorBoundary(fallback=lambda err, reset: "Error!")["Content"]
        html = eb.render()
        
        assert "Content" in html
        assert "Error" not in html
    
    def test_error_boundary_catches_render_error(self):
        """ErrorBoundary catches error in render."""
        def bad_content():
            raise ValueError("Bad!")
        
        eb = ErrorBoundary(
            fallback=lambda err, reset: f"Caught: {err}"
        )[bad_content]
        html = eb.render()
        
        assert "Caught" in html
        assert "Bad!" in html
    
    def test_error_boundary_provides_error_object(self):
        """ErrorBoundary provides error object to fallback."""
        caught_error = [None]
        
        def capture_error(err, reset):
            caught_error[0] = err
            return "Fallback"
        
        def raise_error():
            raise RuntimeError("Test error")
        
        eb = ErrorBoundary(fallback=capture_error)[raise_error]
        eb.render()
        
        assert isinstance(caught_error[0], RuntimeError)
        assert str(caught_error[0]) == "Test error"
    
    def test_error_boundary_provides_reset_function(self):
        """ErrorBoundary provides reset function to fallback."""
        reset_fn = [None]
        
        def capture_reset(err, reset):
            reset_fn[0] = reset
            return "Fallback"
        
        def raise_error():
            raise ValueError("Error")
        
        eb = ErrorBoundary(fallback=capture_reset)[raise_error]
        eb.render()
        
        assert callable(reset_fn[0])
    
    def test_error_boundary_data_attribute(self):
        """ErrorBoundary includes data-error-boundary attribute."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")["Content"]
        html = eb.render()
        
        assert 'data-error-boundary=' in html
    
    def test_error_boundary_has_error_attribute(self):
        """ErrorBoundary sets data-has-error when error."""
        def raise_error():
            raise ValueError("Error")
        
        eb = ErrorBoundary(fallback=lambda e, r: "Fallback")[raise_error]
        html = eb.render()
        
        assert 'data-has-error="true"' in html
    
    def test_error_boundary_no_error_attribute(self):
        """ErrorBoundary doesn't set data-has-error when no error."""
        eb = ErrorBoundary(fallback=lambda e, r: "Fallback")["Content"]
        html = eb.render()
        
        assert 'data-has-error="true"' not in html
    
    def test_error_boundary_unique_id(self):
        """Each ErrorBoundary has unique ID."""
        eb1 = ErrorBoundary(fallback=lambda e, r: "A")["Content"]
        eb2 = ErrorBoundary(fallback=lambda e, r: "B")["Content"]
        
        assert eb1._id != eb2._id
    
    def test_error_boundary_str_method(self):
        """ErrorBoundary __str__ returns rendered HTML."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")["Content"]
        assert str(eb) == eb.render()
    
    def test_error_boundary_repr(self):
        """ErrorBoundary __repr__ is informative."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")["Content"]
        assert "ErrorBoundary" in repr(eb)
    
    def test_error_boundary_catches_attribute_error(self):
        """ErrorBoundary catches AttributeError."""
        def raise_attr_error():
            return None.foo
        
        eb = ErrorBoundary(fallback=lambda e, r: "Caught")[raise_attr_error]
        html = eb.render()
        
        assert "Caught" in html
    
    def test_error_boundary_catches_type_error(self):
        """ErrorBoundary catches TypeError."""
        def raise_type_error():
            return "string" + 5
        
        eb = ErrorBoundary(fallback=lambda e, r: "Caught")[raise_type_error]
        html = eb.render()
        
        assert "Caught" in html
    
    def test_error_boundary_catches_key_error(self):
        """ErrorBoundary catches KeyError."""
        def raise_key_error():
            d = {}
            return d["missing"]
        
        eb = ErrorBoundary(fallback=lambda e, r: "Caught")[raise_key_error]
        html = eb.render()
        
        assert "Caught" in html
    
    def test_error_boundary_catches_index_error(self):
        """ErrorBoundary catches IndexError."""
        def raise_index_error():
            lst = []
            return lst[0]
        
        eb = ErrorBoundary(fallback=lambda e, r: "Caught")[raise_index_error]
        html = eb.render()
        
        assert "Caught" in html
    
    def test_error_boundary_catches_zero_division(self):
        """ErrorBoundary catches ZeroDivisionError."""
        def raise_zero_div():
            return 1 / 0
        
        eb = ErrorBoundary(fallback=lambda e, r: "Caught")[raise_zero_div]
        html = eb.render()
        
        assert "Caught" in html
    
    def test_error_boundary_stores_error(self):
        """ErrorBoundary stores error in error attribute."""
        def raise_error():
            raise ValueError("Stored")
        
        eb = ErrorBoundary(fallback=lambda e, r: "Fallback")[raise_error]
        eb.render()
        
        assert isinstance(eb.error, ValueError)
    
    def test_error_boundary_error_initially_none(self):
        """ErrorBoundary error is None initially."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")["Content"]
        
        assert eb.error is None
    
    def test_error_boundary_error_none_after_success(self):
        """ErrorBoundary error is None after successful render."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")["Content"]
        eb.render()
        
        assert eb.error is None
    
    def test_error_boundary_fallback_html_content(self):
        """ErrorBoundary fallback can return HTML."""
        def raise_error():
            raise ValueError("Error")
        
        eb = ErrorBoundary(
            fallback=lambda e, r: "<div class='error'>Error!</div>"
        )[raise_error]
        html = eb.render()
        
        assert "class='error'" in html
    
    def test_error_boundary_with_signal_content(self):
        """ErrorBoundary works with Signal content."""
        value = Signal(5)
        
        eb = ErrorBoundary(
            fallback=lambda e, r: "Error"
        )[lambda: str(value())]
        html = eb.render()
        
        assert "5" in html


# =============================================================================
# SECTION 2: RECOVERY (15 tests)
# =============================================================================

class TestErrorBoundaryRecovery:
    """Tests for ErrorBoundary recovery functionality."""
    
    def test_error_boundary_reset_clears_error(self):
        """Reset clears error state."""
        def raise_error():
            raise ValueError("Error")
        
        eb = ErrorBoundary(fallback=lambda e, r: "Fallback")[raise_error]
        eb.render()
        
        assert eb.error is not None
        
        eb.reset()
        
        assert eb.error is None
    
    def test_error_boundary_reset_via_callback(self):
        """Reset can be called via callback."""
        reset_fn = [None]
        
        def capture_reset(err, reset):
            reset_fn[0] = reset
            return "Fallback"
        
        def raise_error():
            raise ValueError("Error")
        
        eb = ErrorBoundary(fallback=capture_reset)[raise_error]
        eb.render()
        
        assert eb.error is not None
        
        reset_fn[0]()
        
        assert eb.error is None
    
    def test_error_boundary_rerender_after_reset(self):
        """ErrorBoundary can re-render after reset with fixed content."""
        should_error = [True]
        
        def maybe_error():
            if should_error[0]:
                raise ValueError("Error")
            return "Success"
        
        eb = ErrorBoundary(fallback=lambda e, r: "Fallback")[maybe_error]
        
        html1 = eb.render()
        assert "Fallback" in html1
        
        should_error[0] = False
        eb.reset()
        
        html2 = eb.render()
        assert "Success" in html2
    
    def test_error_boundary_error_persists_across_renders(self):
        """Error persists across renders until reset."""
        def raise_error():
            raise ValueError("Error")
        
        eb = ErrorBoundary(fallback=lambda e, r: "Fallback")[raise_error]
        
        eb.render()
        assert "Fallback" in eb.render()
        assert "Fallback" in eb.render()
        
        assert eb.error is not None
    
    def test_error_boundary_fallback_with_reset_button(self):
        """Fallback can include reset button pattern."""
        def raise_error():
            raise ValueError("Error")
        
        def fallback(err, reset):
            return f"<div><p>{err}</p><button onclick='reset()'>Retry</button></div>"
        
        eb = ErrorBoundary(fallback=fallback)[raise_error]
        html = eb.render()
        
        assert "Retry" in html
    
    def test_error_boundary_multiple_resets(self):
        """Multiple resets work correctly."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")["Content"]
        
        eb.error = ValueError("Test")
        eb.reset()
        assert eb.error is None
        
        eb.error = RuntimeError("Test2")
        eb.reset()
        assert eb.error is None
    
    def test_error_boundary_reset_idempotent(self):
        """Reset is idempotent."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")["Content"]
        
        eb.reset()
        eb.reset()
        eb.reset()
        
        assert eb.error is None
    
    def test_error_boundary_error_details_in_fallback(self):
        """Fallback can display error details."""
        def raise_error():
            raise ValueError("Detailed error message")
        
        def detailed_fallback(err, reset):
            return f"<div class='error'><h2>Error</h2><p>{type(err).__name__}: {err}</p></div>"
        
        eb = ErrorBoundary(fallback=detailed_fallback)[raise_error]
        html = eb.render()
        
        assert "ValueError" in html
        assert "Detailed error message" in html
    
    def test_error_boundary_reset_reenables_content(self):
        """Reset re-enables content rendering."""
        error_count = [0]
        
        def sometimes_error():
            error_count[0] += 1
            if error_count[0] == 1:
                raise ValueError("First call")
            return "Success"
        
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[sometimes_error]
        
        html1 = eb.render()
        assert "Error" in html1
        
        eb.reset()
        
        html2 = eb.render()
        assert "Success" in html2
    
    def test_error_boundary_conditional_error(self):
        """ErrorBoundary handles conditional errors."""
        should_error = Signal(True)
        
        def conditional_error():
            if should_error():
                raise ValueError("Error")
            return "OK"
        
        eb = ErrorBoundary(fallback=lambda e, r: "Fallback")[conditional_error]
        
        html1 = eb.render()
        assert "Fallback" in html1
        
        should_error.set(False)
        eb.reset()
        
        html2 = eb.render()
        assert "OK" in html2
    
    def test_error_boundary_retry_pattern(self):
        """ErrorBoundary supports retry pattern."""
        attempts = [0]
        
        def unreliable():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError(f"Attempt {attempts[0]} failed")
            return "Finally worked!"
        
        eb = ErrorBoundary(fallback=lambda e, r: f"Error: {e}")[unreliable]
        
        # First attempt fails
        html1 = eb.render()
        assert "Attempt 1 failed" in html1
        
        # Second attempt after reset also fails
        eb.reset()
        html2 = eb.render()
        assert "Attempt 2 failed" in html2
        
        # Third attempt succeeds
        eb.reset()
        html3 = eb.render()
        assert "Finally worked!" in html3
    
    def test_error_boundary_fallback_with_details(self):
        """Fallback receives full error object."""
        captured = [None]
        
        def capture(err, reset):
            captured[0] = {
                "type": type(err).__name__,
                "message": str(err),
                "args": err.args
            }
            return "Captured"
        
        def raise_detailed():
            raise ValueError("message", "extra", 123)
        
        eb = ErrorBoundary(fallback=capture)[raise_detailed]
        eb.render()
        
        assert captured[0]["type"] == "ValueError"
        assert "extra" in captured[0]["args"]
    
    def test_error_boundary_reset_called_multiple_times(self):
        """Reset can be called multiple times safely."""
        reset_calls = [0]
        
        def counting_fallback(err, reset):
            def wrapped_reset():
                reset_calls[0] += 1
                reset()
            return "Error"
        
        def raise_error():
            raise ValueError("Error")
        
        eb = ErrorBoundary(fallback=counting_fallback)[raise_error]
        eb.render()
        
        eb.reset()
        eb.reset()
        eb.reset()
        
        assert eb.error is None
    
    def test_error_boundary_preserves_children(self):
        """ErrorBoundary preserves children reference."""
        children = "Preserved Content"
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[children]
        
        assert eb.children == children


# =============================================================================
# SECTION 3: EDGE CASES (15 tests)
# =============================================================================

class TestErrorBoundaryEdgeCases:
    """Edge case tests for ErrorBoundary."""
    
    def test_error_boundary_none_children(self):
        """ErrorBoundary handles None children."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[None]
        html = eb.render()
        
        assert 'data-error-boundary=' in html
    
    def test_error_boundary_empty_children(self):
        """ErrorBoundary handles empty children."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[""]
        html = eb.render()
        
        assert 'data-error-boundary=' in html
    
    def test_error_boundary_nested(self):
        """Nested ErrorBoundaries work correctly."""
        outer = ErrorBoundary(fallback=lambda e, r: "Outer Error")[
            ErrorBoundary(fallback=lambda e, r: "Inner Error")["Content"]
        ]
        html = outer.render()
        
        assert "Content" in html
    
    def test_error_boundary_nested_error_inner(self):
        """Inner ErrorBoundary catches its own errors."""
        def raise_inner():
            raise ValueError("Inner error")
        
        outer = ErrorBoundary(fallback=lambda e, r: "Outer Error")[
            ErrorBoundary(fallback=lambda e, r: "Inner Caught")[raise_inner]
        ]
        html = outer.render()
        
        assert "Inner Caught" in html
        assert "Outer Error" not in html
    
    def test_error_boundary_fallback_error(self):
        """Error in fallback propagates."""
        def raise_error():
            raise ValueError("Content error")
        
        def bad_fallback(err, reset):
            raise RuntimeError("Fallback error")
        
        eb = ErrorBoundary(fallback=bad_fallback)[raise_error]
        
        with pytest.raises(RuntimeError):
            eb.render()
    
    def test_error_boundary_callable_children(self):
        """ErrorBoundary handles callable children."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[lambda: "Dynamic"]
        html = eb.render()
        
        assert "Dynamic" in html
    
    def test_error_boundary_list_children(self):
        """ErrorBoundary handles list children."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[["Part 1", " ", "Part 2"]]
        html = eb.render()
        
        assert "Part 1" in html
        assert "Part 2" in html
    
    def test_error_boundary_unicode_error(self):
        """ErrorBoundary handles unicode in error."""
        def raise_unicode():
            raise ValueError("Error with 日本語 and 🎉")
        
        eb = ErrorBoundary(
            fallback=lambda e, r: f"Caught: {e}"
        )[raise_unicode]
        html = eb.render()
        
        assert "日本語" in html
    
    def test_error_boundary_long_error_message(self):
        """ErrorBoundary handles long error message."""
        def raise_long():
            raise ValueError("x" * 10000)
        
        eb = ErrorBoundary(
            fallback=lambda e, r: "Long error caught"
        )[raise_long]
        html = eb.render()
        
        assert "Long error caught" in html
    
    def test_error_boundary_custom_exception(self):
        """ErrorBoundary handles custom exceptions."""
        class CustomError(Exception):
            pass
        
        def raise_custom():
            raise CustomError("Custom!")
        
        eb = ErrorBoundary(
            fallback=lambda e, r: f"Type: {type(e).__name__}"
        )[raise_custom]
        html = eb.render()
        
        assert "CustomError" in html
    
    def test_error_boundary_html_in_children(self):
        """ErrorBoundary renders HTML children."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")[
            "<div class='content'>HTML Content</div>"
        ]
        html = eb.render()
        
        assert "class='content'" in html
    
    def test_error_boundary_multiple_errors(self):
        """ErrorBoundary handles multiple sequential errors."""
        error_num = [0]
        
        def sequential_error():
            error_num[0] += 1
            raise ValueError(f"Error {error_num[0]}")
        
        eb = ErrorBoundary(
            fallback=lambda e, r: f"Caught: {e}"
        )[sequential_error]
        
        html1 = eb.render()
        assert "Error 1" in html1
        
        eb.reset()
        
        html2 = eb.render()
        assert "Error 2" in html2
    
    def test_error_boundary_error_with_traceback(self):
        """ErrorBoundary catches error with full traceback."""
        import traceback
        captured_tb = [None]
        
        def capture_with_tb(err, reset):
            captured_tb[0] = traceback.format_exc()
            return "Caught"
        
        def raise_with_stack():
            def inner():
                raise ValueError("Deep error")
            inner()
        
        eb = ErrorBoundary(fallback=capture_with_tb)[raise_with_stack]
        eb.render()
        
        assert "inner" in captured_tb[0]
    
    def test_error_boundary_rerender_stability(self):
        """ErrorBoundary renders consistently."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")["Content"]
        
        html1 = eb.render()
        html2 = eb.render()
        
        assert html1 == html2
    
    def test_error_boundary_no_children_set(self):
        """ErrorBoundary without children set."""
        eb = ErrorBoundary(fallback=lambda e, r: "Error")
        html = eb.render()
        
        assert 'data-error-boundary=' in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

