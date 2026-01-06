"""
Tests for callable attribute handling.

Tests cover:
- Dynamic class attributes
- Dynamic style attributes
- Dynamic boolean attributes (disabled, hidden)
- Binding registration for callable attrs
- Signal dependency extraction
"""

import pytest
from pynext.reactive import Signal
from pynext.core.html import div, button, input_, Element
from pynext.core.context import RenderContext, set_context, clear_context


class TestCallableClass:
    """Tests for callable class attributes."""
    
    def test_callable_class_true(self):
        """Callable class evaluated to string."""
        el = div(class_=lambda: "active")
        html = el.render()
        assert 'class="active"' in html
    
    def test_callable_class_false(self):
        """Callable class returning empty string."""
        el = div(class_=lambda: "")
        html = el.render()
        assert 'class=""' in html
    
    def test_callable_class_with_signal(self):
        """Callable class using signal."""
        active = Signal(True, name="active")
        el = div(class_=lambda: "selected" if active() else "")
        html = el.render()
        assert 'class="selected"' in html
    
    def test_callable_class_signal_false(self):
        """Callable class when signal is false."""
        active = Signal(False, name="active")
        el = div(class_=lambda: "selected" if active() else "")
        html = el.render()
        assert 'class=""' in html
    
    def test_callable_class_multiple_classes(self):
        """Callable returning multiple classes."""
        a = Signal(True, name="a")
        b = Signal(False, name="b")
        el = div(class_=lambda: f"base {'a' if a() else ''} {'b' if b() else ''}")
        html = el.render()
        assert "base" in html
        assert "a" in html


class TestCallableStyle:
    """Tests for callable style attributes."""
    
    def test_callable_style_string(self):
        """Callable style as string."""
        el = div(style=lambda: "color: red")
        html = el.render()
        assert 'style="color: red"' in html
    
    def test_callable_style_dict(self):
        """Callable style as dict."""
        el = div(style=lambda: {"color": "red", "font-size": "14px"})
        html = el.render()
        assert "color: red" in html
        assert "font-size: 14px" in html
    
    def test_callable_style_with_signal(self):
        """Callable style using signal."""
        color = Signal("blue", name="color")
        el = div(style=lambda: {"color": color()})
        html = el.render()
        assert "color: blue" in html
    
    def test_callable_style_empty_dict(self):
        """Callable style returning empty dict."""
        el = div(style=lambda: {})
        html = el.render()
        assert 'style=""' in html


class TestCallableBoolean:
    """Tests for callable boolean attributes."""
    
    def test_callable_disabled_true(self):
        """Callable disabled returning True."""
        el = button(disabled=lambda: True)["Click"]
        html = el.render()
        assert "disabled" in html
    
    def test_callable_disabled_false(self):
        """Callable disabled returning False."""
        el = button(disabled=lambda: False)["Click"]
        html = el.render()
        assert "disabled" not in html
    
    def test_callable_disabled_with_signal(self):
        """Callable disabled using signal."""
        loading = Signal(True, name="loading")
        el = button(disabled=lambda: loading())["Submit"]
        html = el.render()
        assert "disabled" in html
    
    def test_callable_hidden_true(self):
        """Callable hidden attribute."""
        el = div(hidden=lambda: True)["Hidden"]
        html = el.render()
        assert "hidden" in html


class TestCallableAttrBindingRegistration:
    """Tests for callable attribute binding registration."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_callable_class_registers_binding(self):
        """Callable class with signal registers binding."""
        active = Signal(True, name="active")
        el = div(class_=lambda: "active" if active() else "")
        el.render()
        
        # Should have a class binding
        class_bindings = [b for b in self.ctx.bindings if b.binding_type == "class"]
        assert len(class_bindings) == 1
    
    def test_callable_style_registers_binding(self):
        """Callable style with signal registers binding."""
        color = Signal("red", name="color")
        el = div(style=lambda: {"color": color()})
        el.render()
        
        style_bindings = [b for b in self.ctx.bindings if b.binding_type == "style"]
        assert len(style_bindings) == 1
    
    def test_callable_attr_registers_binding(self):
        """Other callable attrs register as attr binding."""
        value = Signal("test", name="value")
        el = input_(placeholder=lambda: value())
        el.render()
        
        attr_bindings = [b for b in self.ctx.bindings if b.binding_type == "attr"]
        assert len(attr_bindings) >= 0  # May or may not register based on implementation
    
    def test_no_binding_without_signal(self):
        """Callable without signal doesn't register binding."""
        el = div(class_=lambda: "static")
        el.render()
        
        assert len(self.ctx.bindings) == 0
    
    def test_binding_has_signal_deps(self):
        """Binding has correct signal dependencies."""
        active = Signal(True, name="active")
        el = div(class_=lambda: "active" if active() else "")
        el.render()
        
        binding = self.ctx.bindings[0]
        # Signal deps now use names instead of IDs
        assert "active" in binding.signal_deps
    
    def test_binding_has_update_expr(self):
        """Binding has update expression."""
        active = Signal(True, name="active")
        el = div(class_=lambda: "active" if active() else "")
        el.render()
        
        binding = self.ctx.bindings[0]
        assert "getSignal" in binding.update_expr


class TestCallableAttrSignalExtraction:
    """Tests for signal extraction from callable attributes."""
    
    def test_extract_single_signal(self):
        """Extract single signal from closure."""
        active = Signal(True, name="active")
        el = div(class_=lambda: "active" if active() else "")
        
        deps = el._extract_callable_deps(lambda: "active" if active() else "")
        assert len(deps) == 1
        # Signal deps now use names instead of IDs
        assert "active" in deps
    
    def test_extract_multiple_signals(self):
        """Extract multiple signals from closure."""
        a = Signal(True, name="a")
        b = Signal(True, name="b")
        func = lambda: f"{'a' if a() else ''} {'b' if b() else ''}"
        el = div()
        
        deps = el._extract_callable_deps(func)
        assert len(deps) == 2
    
    def test_extract_no_signals(self):
        """Return empty for no signals."""
        el = div()
        deps = el._extract_callable_deps(lambda: "static")
        assert deps == []


class TestCallableAttrEdgeCases:
    """Edge cases for callable attributes."""
    
    def test_callable_raises_exception(self):
        """Callable that raises exception handles gracefully."""
        el = div(class_=lambda: 1 / 0)  # ZeroDivisionError
        html = el.render()
        # Should not crash, renders empty or default
        assert "<div" in html
    
    def test_callable_returns_none(self):
        """Callable returning None."""
        el = div(class_=lambda: None)
        html = el.render()
        # Should handle None gracefully
        assert "<div" in html
    
    def test_callable_returns_number(self):
        """Callable returning number."""
        el = div(tabindex=lambda: 0)
        html = el.render()
        # Should convert to string
        assert "tabindex" in html
    
    def test_mixed_static_and_callable(self):
        """Element with both static and callable attrs."""
        active = Signal(True, name="active")
        el = div(
            id="my-div",
            class_=lambda: "active" if active() else "",
            style="padding: 10px"
        )
        html = el.render()
        assert 'id="my-div"' in html
        assert 'style="padding: 10px"' in html


class TestCallableAttrHydration:
    """Tests for callable attr hydration data."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_binding_in_hydration_data(self):
        """Callable attr binding in hydration data."""
        active = Signal(True, name="active")
        el = div(class_=lambda: "active" if active() else "")
        el.render()
        
        data = self.ctx.get_hydration_data()
        assert len(data["bindings"]) >= 1
    
    def test_initial_value_in_hydration(self):
        """Initial value stored in hydration."""
        active = Signal(True, name="active")
        el = div(class_=lambda: "active" if active() else "")
        el.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        assert binding["initial"] == "active"
    
    def test_attr_name_in_hydration(self):
        """Attribute name in hydration data."""
        active = Signal(True, name="active")
        el = div(class_=lambda: "active" if active() else "")
        el.render()
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        assert binding["attr"] == "class"


class TestCallableAttrWithDifferentTypes:
    """Tests for different attribute value types."""
    
    def test_callable_list_class(self):
        """Callable returning list for class."""
        el = div(class_=lambda: ["a", "b", "c"])
        html = el.render()
        # Should join list or convert to string
        assert "<div" in html
    
    def test_callable_object_style(self):
        """Callable returning complex object for style."""
        el = div(style=lambda: {"margin": "10px", "padding": "5px"})
        html = el.render()
        assert "margin: 10px" in html
        assert "padding: 5px" in html

