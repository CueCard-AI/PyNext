"""
Tests for DOM update functions (updateShow, updateText, etc.)

These tests verify the server-side rendering of elements
that will be updated on the client.
"""

import pytest
from pynext.reactive import Signal
from pynext.reactive.control_flow import Show, For
from pynext.core.html import div, span, p, button
from pynext.core.context import RenderContext, set_context, clear_context


class TestShowDOMUpdates:
    """Tests for Show component DOM structure."""
    
    def test_show_renders_wrapper_div(self):
        """Show renders a wrapper div."""
        show = Show(when=True)["Content"]
        html = show.render()
        assert html.startswith("<div")
        assert html.endswith("</div>")
    
    def test_show_has_id(self):
        """Show has unique ID for client binding."""
        show = Show(when=True)["Content"]
        html = show.render()
        assert f'id="{show._id}"' in html
    
    def test_show_true_no_display_none(self):
        """Show with true condition has no display:none."""
        show = Show(when=True)["Content"]
        html = show.render()
        assert 'display: none' not in html
    
    def test_show_false_has_display_none(self):
        """Show with false condition has display:none."""
        show = Show(when=False)["Content"]
        html = show.render()
        assert 'style="display: none;"' in html
    
    def test_show_data_condition_attribute(self):
        """Show has data-condition attribute."""
        show_true = Show(when=True)["A"]
        show_false = Show(when=False)["B"]
        
        assert 'data-condition="true"' in show_true.render()
        assert 'data-condition="false"' in show_false.render()
    
    def test_show_content_always_rendered(self):
        """Content is rendered even when hidden."""
        show = Show(when=False)["Hidden Content"]
        html = show.render()
        assert "Hidden Content" in html


class TestForDOMUpdates:
    """Tests for For component DOM structure."""
    
    def test_for_renders_wrapper_div(self):
        """For renders a wrapper div."""
        for_comp = For(each=[1, 2])[lambda x, i: str(x)]
        html = for_comp.render()
        assert html.startswith("<div")
        assert html.endswith("</div>")
    
    def test_for_has_id(self):
        """For has unique ID for client binding."""
        for_comp = For(each=[1])[lambda x, i: str(x)]
        html = for_comp.render()
        assert f'id="{for_comp._id}"' in html
    
    def test_for_items_have_key(self):
        """For items have data-for-item attribute."""
        items = [{"id": 1}, {"id": 2}]
        for_comp = For(each=items)[lambda x, i: str(x["id"])]
        html = for_comp.render()
        assert 'data-for-item="1"' in html
        assert 'data-for-item="2"' in html
    
    def test_for_pynext_for_attribute(self):
        """For has data-pynext-for attribute."""
        for_comp = For(each=[1])[lambda x, i: str(x)]
        html = for_comp.render()
        assert 'data-pynext-for="true"' in html


class TestTextDOMUpdates:
    """Tests for text content DOM structure."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_signal_text_has_span(self):
        """Signal as text is wrapped in span."""
        count = Signal(42, name="count")
        el = div()[count]
        html = el.render()
        assert "<span" in html
        assert "</span>" in html
    
    def test_signal_text_span_has_id(self):
        """Signal text span has ID."""
        count = Signal(42, name="count")
        el = div()[count]
        html = el.render()
        assert f'id="text_{count._id}"' in html
    
    def test_signal_text_has_data_attr(self):
        """Signal text span has data-pynext-text attribute."""
        count = Signal(42, name="count")
        el = div()[count]
        html = el.render()
        assert 'data-pynext-text' in html


class TestCallableAttrDOMUpdates:
    """Tests for callable attribute DOM structure."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_callable_class_renders_initial(self):
        """Callable class renders initial value."""
        active = Signal(True, name="active")
        el = div(class_=lambda: "active" if active() else "")
        html = el.render()
        assert 'class="active"' in html
    
    def test_callable_class_false_condition(self):
        """Callable class with false condition."""
        active = Signal(False, name="active")
        el = div(class_=lambda: "active" if active() else "")
        html = el.render()
        assert 'class=""' in html
    
    def test_callable_style_renders_initial(self):
        """Callable style renders initial value."""
        color = Signal("red", name="color")
        el = div(style=lambda: {"color": color()})
        html = el.render()
        assert "color: red" in html
    
    def test_callable_disabled_true(self):
        """Callable disabled renders disabled attr."""
        loading = Signal(True, name="loading")
        el = button(disabled=lambda: loading())["Click"]
        html = el.render()
        assert "disabled" in html
    
    def test_element_has_id_for_binding(self):
        """Element with callable attr has ID for binding."""
        active = Signal(True, name="active")
        el = div(class_=lambda: "active" if active() else "")
        html = el.render()
        assert 'id="' in html


class TestNestedDOMUpdates:
    """Tests for nested reactive DOM structures."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_show_inside_div(self):
        """Show inside a div."""
        visible = Signal(True, name="visible")
        el = div()[Show(when=lambda: visible())["Inner"]]
        html = el.render()
        assert "Inner" in html
        assert 'data-pynext-show="true"' in html
    
    def test_for_inside_div(self):
        """For inside a div."""
        items = [1, 2, 3]
        el = div()[For(each=items)[lambda x, i: str(x)]]
        html = el.render()
        assert 'data-pynext-for="true"' in html
    
    def test_signal_inside_show(self):
        """Signal text inside Show."""
        count = Signal(42, name="count")
        show = Show(when=True)[count]
        html = show.render()
        assert "42" in html
        # Signal inside Show may or may not have text marker depending on context
    
    def test_callable_attr_inside_for(self):
        """Callable attr inside For item."""
        active = Signal(True, name="active")
        items = [1, 2]
        for_comp = For(each=items)[
            lambda x, i: div(class_=lambda: "active" if active() else "")[str(x)]
        ]
        html = for_comp.render()
        assert 'class="active"' in html


class TestMultipleBindings:
    """Tests for multiple bindings in same render."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_multiple_show_bindings(self):
        """Multiple Show components register multiple bindings."""
        a = Signal(True, name="a")
        b = Signal(False, name="b")
        
        el = div()[
            Show(when=lambda: a())["A"],
            Show(when=lambda: b())["B"],
        ]
        el.render()
        
        show_bindings = [b for b in self.ctx.bindings if b.binding_type == "show"]
        assert len(show_bindings) == 2
    
    def test_mixed_binding_types(self):
        """Mix of different binding types."""
        visible = Signal(True, name="visible")
        color = Signal("red", name="color")
        count = Signal(42, name="count")
        
        el = div()[
            Show(when=lambda: visible())["Content"],
            div(style=lambda: {"color": color()})["Styled"],
            count,
        ]
        el.render()
        
        types = {b.binding_type for b in self.ctx.bindings}
        assert "show" in types
        assert "style" in types
        assert "text" in types


class TestHydrationMarkers:
    """Tests for hydration marker attributes."""
    
    def test_show_marker(self):
        """Show has hydration marker."""
        show = Show(when=True)["Content"]
        html = show.render()
        assert 'data-pynext-show="true"' in html
    
    def test_for_marker(self):
        """For has hydration marker."""
        for_comp = For(each=[1])[lambda x, i: str(x)]
        html = for_comp.render()
        assert 'data-pynext-for="true"' in html
    
    def test_text_marker(self):
        """Text signal has hydration marker."""
        ctx = RenderContext()
        set_context(ctx)
        
        count = Signal(42, name="count")
        el = div()[count]
        html = el.render()
        
        clear_context()
        
        assert 'data-pynext-text' in html


class TestDOMStructureEdgeCases:
    """Edge cases for DOM structure."""
    
    def test_empty_show(self):
        """Empty Show renders valid HTML."""
        show = Show(when=True)
        html = show.render()
        assert "<div" in html
        assert "</div>" in html
    
    def test_empty_for(self):
        """Empty For renders valid HTML."""
        for_comp = For(each=[], fallback="None")[lambda x, i: str(x)]
        html = for_comp.render()
        assert "<div" in html
        assert "None" in html
    
    def test_deeply_nested(self):
        """Deeply nested reactive elements."""
        visible = Signal(True, name="visible")
        
        el = div()[
            Show(when=lambda: visible())[
                div()[
                    Show(when=lambda: visible())[
                        "Deep"
                    ]
                ]
            ]
        ]
        html = el.render()
        assert "Deep" in html

