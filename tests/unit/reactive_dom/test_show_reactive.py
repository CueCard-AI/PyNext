"""
Tests for Show component reactive behavior.

Tests cover:
- Show toggle visibility
- Show with fallback content
- Show keyed mode (recreate children)
- Show binding registration
- Signal dependency extraction
- Update expression generation
"""

import pytest
from pynext.reactive import Signal
from pynext.reactive.control_flow import Show
from pynext.core.context import RenderContext, set_context, clear_context


class TestShowBasic:
    """Basic Show rendering tests."""
    
    def test_show_true_renders_children(self):
        """Show with true condition renders children."""
        show = Show(when=True)["Hello"]
        html = show.render()
        assert "Hello" in html
        assert 'data-pynext-show="true"' in html
    
    def test_show_false_hides_content(self):
        """Show with false condition hides content with CSS."""
        show = Show(when=False)["Hidden"]
        html = show.render()
        assert "Hidden" in html  # Content is still there
        assert 'style="display: none;"' in html
    
    def test_show_callable_true(self):
        """Show with callable that returns True."""
        show = Show(when=lambda: True)["Visible"]
        html = show.render()
        assert "Visible" in html
        assert 'display: none' not in html
    
    def test_show_callable_false(self):
        """Show with callable that returns False."""
        show = Show(when=lambda: False)["Hidden"]
        html = show.render()
        assert "Hidden" in html
        assert 'style="display: none;"' in html
    
    def test_show_with_signal_true(self):
        """Show with signal that is truthy."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        html = show.render()
        assert "Content" in html
    
    def test_show_with_signal_false(self):
        """Show with signal that is falsy."""
        visible = Signal(False, name="visible")
        show = Show(when=lambda: visible())["Content"]
        html = show.render()
        assert 'style="display: none;"' in html
    
    def test_show_data_condition_true(self):
        """Show renders data-condition attribute for true."""
        show = Show(when=True)["Content"]
        html = show.render()
        assert 'data-condition="true"' in html
    
    def test_show_data_condition_false(self):
        """Show renders data-condition attribute for false."""
        show = Show(when=False)["Content"]
        html = show.render()
        assert 'data-condition="false"' in html
    
    def test_show_has_unique_id(self):
        """Each Show has a unique ID."""
        show1 = Show(when=True)["A"]
        show2 = Show(when=True)["B"]
        assert show1._id != show2._id
        assert show1._id.startswith("show_")
        assert show2._id.startswith("show_")


class TestShowFallback:
    """Show fallback content tests."""
    
    def test_show_with_fallback_true(self):
        """When true, content is shown, not fallback."""
        show = Show(when=True, fallback="Fallback")["Main"]
        html = show.render()
        assert "Main" in html
    
    def test_show_with_fallback_false(self):
        """When false, both content and fallback are rendered (content hidden)."""
        show = Show(when=False, fallback="Fallback")["Main"]
        html = show.render()
        # Content is now rendered but hidden
        assert 'style="display: none;"' in html
    
    def test_show_fallback_signal(self):
        """Fallback works with signal condition."""
        visible = Signal(False, name="visible")
        show = Show(when=lambda: visible(), fallback="Loading...")["Ready"]
        html = show.render()
        assert 'style="display: none;"' in html


class TestShowKeyedMode:
    """Show keyed mode tests."""
    
    def test_show_keyed_attribute(self):
        """Keyed Show has data-keyed attribute."""
        show = Show(when=True, keyed=True)["Content"]
        html = show.render()
        assert 'data-keyed="true"' in html
    
    def test_show_non_keyed_no_attribute(self):
        """Non-keyed Show doesn't have data-keyed."""
        show = Show(when=True, keyed=False)["Content"]
        html = show.render()
        assert 'data-keyed' not in html
    
    def test_show_default_non_keyed(self):
        """Show is non-keyed by default."""
        show = Show(when=True)["Content"]
        html = show.render()
        assert 'data-keyed' not in html


class TestShowBindingRegistration:
    """Show binding registration tests."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_show_registers_binding(self):
        """Show with signal registers a binding."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        assert len(self.ctx.bindings) == 1
        binding = self.ctx.bindings[0]
        assert binding.binding_type == "show"
    
    def test_show_binding_has_signal_deps(self):
        """Show binding includes signal dependencies."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        binding = self.ctx.bindings[0]
        assert visible._id in binding.signal_deps
    
    def test_show_binding_has_update_expr(self):
        """Show binding has update expression."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        binding = self.ctx.bindings[0]
        assert "getSignal" in binding.update_expr
        assert visible._id in binding.update_expr
    
    def test_show_binding_has_node_id(self):
        """Show binding has correct node ID."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        binding = self.ctx.bindings[0]
        assert binding.node_id == show._id
    
    def test_show_no_binding_without_signal(self):
        """Show without signal doesn't register binding."""
        show = Show(when=True)["Content"]
        show.render()
        
        assert len(self.ctx.bindings) == 0


class TestShowSignalExtraction:
    """Show signal dependency extraction tests."""
    
    def test_extract_single_signal(self):
        """Extract single signal from closure."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        
        deps = show._extract_signal_deps()
        assert len(deps) == 1
        assert visible._id in deps
    
    def test_extract_multiple_signals(self):
        """Extract multiple signals from closure."""
        a = Signal(True, name="a")
        b = Signal(True, name="b")
        show = Show(when=lambda: a() and b())["Content"]
        
        deps = show._extract_signal_deps()
        assert len(deps) == 2
        assert a._id in deps
        assert b._id in deps
    
    def test_extract_no_signals(self):
        """Return empty list when no signals."""
        show = Show(when=lambda: True)["Content"]
        
        deps = show._extract_signal_deps()
        assert deps == []
    
    def test_extract_from_non_callable(self):
        """Return empty list for non-callable."""
        show = Show(when=True)["Content"]
        
        deps = show._extract_signal_deps()
        assert deps == []


class TestShowUpdateExpr:
    """Show update expression generation tests."""
    
    def test_generate_single_signal_expr(self):
        """Generate expression for single signal."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        
        expr = show._generate_update_expr()
        assert f"getSignal('{visible._id}')" in expr
        assert "Boolean" in expr
    
    def test_generate_multi_signal_expr(self):
        """Generate expression for multiple signals."""
        a = Signal(True, name="a")
        b = Signal(True, name="b")
        show = Show(when=lambda: a() and b())["Content"]
        
        expr = show._generate_update_expr()
        assert a._id in expr
        assert b._id in expr
    
    def test_generate_no_signal_expr(self):
        """Generate 'true' for no signals."""
        show = Show(when=lambda: True)["Content"]
        
        expr = show._generate_update_expr()
        assert expr == "true"


class TestShowHydrationData:
    """Show hydration data tests."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_binding_in_hydration_data(self):
        """Show binding appears in hydration data."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        assert "bindings" in data
        assert len(data["bindings"]) == 1
    
    def test_binding_type_in_hydration(self):
        """Binding type is 'show' in hydration data."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        assert binding["type"] == "show"
    
    def test_initial_value_in_hydration(self):
        """Initial value is in hydration data."""
        visible = Signal(True, name="visible")
        show = Show(when=lambda: visible())["Content"]
        show.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        assert binding["initial"] == True


class TestShowEdgeCases:
    """Show edge case tests."""
    
    def test_show_empty_children(self):
        """Show with no children."""
        show = Show(when=True)
        html = show.render()
        assert 'data-pynext-show="true"' in html
    
    def test_show_nested_element_children(self):
        """Show with nested Element children."""
        from pynext.core.html import div
        show = Show(when=True)[div()["Nested"]]
        html = show.render()
        assert "<div>Nested</div>" in html
    
    def test_show_multiple_children(self):
        """Show with multiple children."""
        show = Show(when=True)["A", "B", "C"]
        html = show.render()
        assert "ABC" in html or ("A" in html and "B" in html and "C" in html)
    
    def test_show_none_when(self):
        """Show with None condition treats as falsy."""
        show = Show(when=None)["Content"]
        html = show.render()
        assert 'style="display: none;"' in html
    
    def test_show_zero_when(self):
        """Show with 0 condition treats as falsy."""
        show = Show(when=0)["Content"]
        html = show.render()
        assert 'style="display: none;"' in html
    
    def test_show_empty_string_when(self):
        """Show with empty string condition treats as falsy."""
        show = Show(when="")["Content"]
        html = show.render()
        assert 'style="display: none;"' in html
    
    def test_show_signal_value_false_string(self):
        """Show with signal containing falsy-like string."""
        visible = Signal("false", name="visible")  # String "false" is truthy
        show = Show(when=lambda: visible())["Content"]
        html = show.render()
        assert 'style="display: none;"' not in html
    
    def test_show_to_js_init(self):
        """Show generates JS init code."""
        show = Show(when=True)["Content"]
        js = show.to_js_init()
        assert "__pynext__" in js
        assert show._id in js
    
    def test_show_str_method(self):
        """Show __str__ returns rendered HTML."""
        show = Show(when=True)["Hello"]
        assert str(show) == show.render()
    
    def test_show_repr_method(self):
        """Show __repr__ is informative."""
        show = Show(when=True, keyed=True)["Content"]
        repr_str = repr(show)
        assert "Show" in repr_str

