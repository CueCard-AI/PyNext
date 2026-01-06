"""
Tests for text interpolation with signals.

Tests cover:
- Signal as text content
- Callable text content
- Text binding registration
- Span wrapping for reactive text
"""

import pytest
from pynext.reactive import Signal
from pynext.core.html import div, span, p
from pynext.core.context import RenderContext, set_context, clear_context


class TestSignalAsText:
    """Tests for signals used as text content."""
    
    def test_signal_renders_value(self):
        """Signal as text renders its current value."""
        count = Signal(42, name="count")
        el = div()[count]
        html = el.render()
        assert "42" in html
    
    def test_signal_wrapped_in_span(self):
        """Signal is wrapped in span with data attribute."""
        count = Signal(42, name="count")
        el = div()[count]
        html = el.render()
        assert "data-pynext-text" in html
        assert "<span" in html
    
    def test_signal_span_has_id(self):
        """Signal span has unique ID."""
        count = Signal(42, name="count")
        el = div()[count]
        html = el.render()
        # Now uses signal name for stable ID
        assert 'id="text_count"' in html
    
    def test_signal_string_value(self):
        """Signal with string value."""
        name = Signal("John", name="name")
        el = div()[name]
        html = el.render()
        assert "John" in html
    
    def test_signal_escapes_html(self):
        """Signal value is HTML escaped."""
        text = Signal("<script>alert(1)</script>", name="text")
        el = div()[text]
        html = el.render()
        assert "&lt;script&gt;" in html
        assert "<script>" not in html


class TestCallableAsText:
    """Tests for callables used as text content."""
    
    def test_callable_evaluates(self):
        """Callable text is evaluated."""
        el = div()[lambda: "Hello"]
        html = el.render()
        assert "Hello" in html
    
    def test_callable_with_signal_wrapped(self):
        """Callable with signal dependency is wrapped."""
        count = Signal(5, name="count")
        el = div()[lambda: f"Count: {count()}"]
        html = el.render()
        assert "Count: 5" in html
    
    def test_callable_escapes_html(self):
        """Callable result is HTML escaped."""
        el = div()[lambda: "<b>bold</b>"]
        html = el.render()
        assert "&lt;b&gt;" in html


class TestTextBindingRegistration:
    """Tests for text binding registration."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_signal_registers_binding(self):
        """Signal as text registers binding."""
        count = Signal(42, name="count")
        el = div()[count]
        el.render()
        
        text_bindings = [b for b in self.ctx.bindings if b.binding_type == "text"]
        assert len(text_bindings) == 1
    
    def test_binding_has_signal_dep(self):
        """Text binding has signal dependency."""
        count = Signal(42, name="count")
        el = div()[count]
        el.render()
        
        binding = self.ctx.bindings[0]
        # Signal deps now use names instead of IDs
        assert "count" in binding.signal_deps
    
    def test_binding_has_update_expr(self):
        """Text binding has update expression."""
        count = Signal(42, name="count")
        el = div()[count]
        el.render()
        
        binding = self.ctx.bindings[0]
        assert "getSignal" in binding.update_expr
        # Signal deps now use names instead of IDs
        assert "count" in binding.update_expr
    
    def test_callable_with_signal_registers(self):
        """Callable with signal registers binding."""
        count = Signal(42, name="count")
        el = div()[lambda: f"Count: {count()}"]
        el.render()
        
        text_bindings = [b for b in self.ctx.bindings if b.binding_type == "text"]
        assert len(text_bindings) >= 1
    
    def test_static_callable_no_binding(self):
        """Static callable without signal doesn't register."""
        el = div()[lambda: "Static text"]
        el.render()
        
        assert len(self.ctx.bindings) == 0


class TestTextHydration:
    """Tests for text hydration data."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_text_binding_in_hydration(self):
        """Text binding in hydration data."""
        count = Signal(42, name="count")
        el = div()[count]
        el.render()
        
        data = self.ctx.get_hydration_data()
        assert len(data["bindings"]) >= 1
    
    def test_text_type_in_hydration(self):
        """Binding type is 'text' in hydration."""
        count = Signal(42, name="count")
        el = div()[count]
        el.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        assert binding["type"] == "text"
    
    def test_initial_value_in_hydration(self):
        """Initial value in hydration data."""
        count = Signal(42, name="count")
        el = div()[count]
        el.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        assert binding["initial"] == 42


class TestMixedTextContent:
    """Tests for mixed text and signal content."""
    
    def test_text_before_signal(self):
        """Static text before signal."""
        count = Signal(5, name="count")
        el = div()["Count: ", count]
        html = el.render()
        assert "Count:" in html
        assert "5" in html
    
    def test_signal_before_text(self):
        """Signal before static text."""
        count = Signal(5, name="count")
        el = div()[count, " items"]
        html = el.render()
        assert "5" in html
        assert "items" in html
    
    def test_multiple_signals(self):
        """Multiple signals as text."""
        a = Signal(1, name="a")
        b = Signal(2, name="b")
        el = div()[a, " + ", b]
        html = el.render()
        assert "1" in html
        assert "2" in html
        assert "+" in html


class TestTextEdgeCases:
    """Edge cases for text interpolation."""
    
    def test_none_signal_value(self):
        """Signal with None value."""
        value = Signal(None, name="value")
        el = div()[value]
        html = el.render()
        assert "None" in html or '<span' in html
    
    def test_empty_string_signal(self):
        """Signal with empty string."""
        text = Signal("", name="text")
        el = div()[text]
        html = el.render()
        assert '<span' in html
    
    def test_number_signal(self):
        """Signal with number value."""
        num = Signal(3.14159, name="num")
        el = div()[num]
        html = el.render()
        assert "3.14159" in html
    
    def test_boolean_signal(self):
        """Signal with boolean value."""
        flag = Signal(True, name="flag")
        el = div()[flag]
        html = el.render()
        assert "True" in html
    
    def test_list_signal(self):
        """Signal with list value."""
        items = Signal([1, 2, 3], name="items")
        el = div()[items]
        html = el.render()
        assert "<span" in html
    
    def test_callable_exception(self):
        """Callable that throws exception."""
        el = div()[lambda: 1/0]  # ZeroDivisionError
        html = el.render()
        # Should handle gracefully
        assert "<div" in html
    
    def test_nested_signal_in_element(self):
        """Signal inside nested element."""
        count = Signal(42, name="count")
        el = div()[span()[count]]
        html = el.render()
        assert "42" in html


class TestSignalRegistration:
    """Tests for signal registration with context."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_signal_registered_with_context(self):
        """Signal is registered with render context."""
        count = Signal(42, name="count")
        el = div()[count]
        el.render()
        
        assert "count" in self.ctx.signals
    
    def test_signal_element_id_recorded(self):
        """Signal's element ID is recorded."""
        count = Signal(42, name="count")
        el = div()[count]
        el.render()
        
        reg = self.ctx.signals["count"]
        # Now uses signal name for stable ID
        assert "text_count" == reg.element_id

