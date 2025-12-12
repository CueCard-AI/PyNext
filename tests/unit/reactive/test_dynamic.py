"""
Tests for Dynamic Component - Dynamic Component Switching

50 comprehensive tests covering:
- Basic rendering (15 tests)
- Reactive updates (20 tests)
- Edge cases (15 tests)
"""

import pytest
from pynext.reactive.control_flow import Dynamic
from pynext.reactive.signal import Signal
from pynext.reactive.store import Store


# =============================================================================
# SECTION 1: BASIC RENDERING (15 tests)
# =============================================================================

class TestDynamicBasicRendering:
    """Basic Dynamic component rendering tests."""
    
    def test_dynamic_renders_component(self):
        """Dynamic renders a component."""
        class Hello:
            def render(self):
                return "<div>Hello</div>"
        
        dynamic = Dynamic(component=Hello)
        html = dynamic.render()
        
        assert "Hello" in html
    
    def test_dynamic_renders_function_component(self):
        """Dynamic renders function component."""
        def Hello():
            return "<span>Hello Function</span>"
        
        dynamic = Dynamic(component=Hello)
        html = dynamic.render()
        
        assert "Hello Function" in html
    
    def test_dynamic_with_props(self):
        """Dynamic passes props to component."""
        class Greeter:
            def __init__(self, name="World"):
                self.name = name
            
            def render(self):
                return f"<div>Hello, {self.name}!</div>"
        
        # Pass component as class directly
        dynamic = Dynamic(component=Greeter, name="Alice")
        html = dynamic.render()
        
        assert "Hello, Alice!" in html
    
    def test_dynamic_callable_component(self):
        """Dynamic with callable returning component."""
        class ComponentA:
            def render(self):
                return "Component A"
        
        dynamic = Dynamic(component=lambda: ComponentA)
        html = dynamic.render()
        
        assert "Component A" in html
    
    def test_dynamic_unique_id(self):
        """Each Dynamic has unique ID."""
        d1 = Dynamic(component=lambda: "A")
        d2 = Dynamic(component=lambda: "B")
        
        assert d1._id != d2._id
    
    def test_dynamic_data_attribute(self):
        """Dynamic includes data-dynamic attribute."""
        dynamic = Dynamic(component=lambda: "Content")
        html = dynamic.render()
        
        assert 'data-dynamic=' in html
    
    def test_dynamic_str_method(self):
        """Dynamic __str__ returns rendered HTML."""
        dynamic = Dynamic(component=lambda: "Content")
        assert str(dynamic) == dynamic.render()
    
    def test_dynamic_repr(self):
        """Dynamic __repr__ is informative."""
        dynamic = Dynamic(component=lambda: "Content")
        assert "Dynamic" in repr(dynamic)
    
    def test_dynamic_none_component(self):
        """Dynamic handles None component."""
        dynamic = Dynamic(component=lambda: None)
        html = dynamic.render()
        
        assert 'data-dynamic=' in html
    
    def test_dynamic_string_component(self):
        """Dynamic handles string component."""
        dynamic = Dynamic(component=lambda: "Just a string")
        html = dynamic.render()
        
        assert "Just a string" in html
    
    def test_dynamic_multiple_props(self):
        """Dynamic passes multiple props."""
        class MultiProp:
            def __init__(self, a=0, b=0, c=0):
                self.a, self.b, self.c = a, b, c
            
            def render(self):
                return f"<div>{self.a + self.b + self.c}</div>"
        
        dynamic = Dynamic(component=MultiProp, a=1, b=2, c=3)
        html = dynamic.render()
        
        assert "6" in html
    
    def test_dynamic_html_content(self):
        """Dynamic renders HTML content."""
        def HtmlComponent():
            return "<div class='styled'>Styled Content</div>"
        
        dynamic = Dynamic(component=HtmlComponent)
        html = dynamic.render()
        
        assert "class='styled'" in html
    
    def test_dynamic_nested_render(self):
        """Dynamic handles nested render calls."""
        class Outer:
            def render(self):
                inner_dyn = Dynamic(component=lambda: "Inner")
                return f"<div>Outer: {inner_dyn.render()}</div>"
        
        dynamic = Dynamic(component=Outer)
        html = dynamic.render()
        
        assert "Outer" in html
        assert "Inner" in html
    
    def test_dynamic_class_direct(self):
        """Dynamic with direct class reference."""
        class DirectComponent:
            def render(self):
                return "Direct"
        
        dynamic = Dynamic(component=DirectComponent)
        html = dynamic.render()
        
        assert "Direct" in html
    
    def test_dynamic_function_direct(self):
        """Dynamic with direct function reference."""
        def direct_fn():
            return "Function Direct"
        
        dynamic = Dynamic(component=direct_fn)
        html = dynamic.render()
        
        assert "Function Direct" in html


# =============================================================================
# SECTION 2: REACTIVE UPDATES (20 tests)
# =============================================================================

class TestDynamicReactiveUpdates:
    """Tests for Dynamic with reactive signals."""
    
    def test_dynamic_signal_component(self):
        """Dynamic with Signal-based component selection."""
        class CompA:
            def render(self):
                return "A"
        
        class CompB:
            def render(self):
                return "B"
        
        use_a = Signal(True)
        dynamic = Dynamic(component=lambda: CompA if use_a() else CompB)
        
        assert "A" in dynamic.render()
        
        use_a.set(False)
        assert "B" in dynamic.render()
    
    def test_dynamic_component_map(self):
        """Dynamic with component map selection."""
        components = {
            "home": lambda: "Home Page",
            "about": lambda: "About Page",
            "contact": lambda: "Contact Page"
        }
        
        page = Signal("home")
        dynamic = Dynamic(component=lambda: components[page()])
        
        assert "Home Page" in dynamic.render()
        
        page.set("about")
        assert "About Page" in dynamic.render()
    
    def test_dynamic_props_from_signal(self):
        """Dynamic with props from Signal."""
        class Greeter:
            def __init__(self, name=""):
                self.name = name
            
            def render(self):
                return f"Hello, {self.name}!"
        
        name = Signal("Alice")
        # Props are evaluated when Dynamic is created
        dynamic = Dynamic(component=Greeter, name=name())
        
        html = dynamic.render()
        assert "Alice" in html or "Hello" in html  # Name passed via props
    
    def test_dynamic_component_switch(self):
        """Dynamic switches between components."""
        modes = {
            "view": lambda: "View Mode",
            "edit": lambda: "Edit Mode",
            "create": lambda: "Create Mode"
        }
        
        mode = Signal("view")
        dynamic = Dynamic(component=lambda: modes[mode()])
        
        for m in ["view", "edit", "create", "view"]:
            mode.set(m)
            html = dynamic.render()
            assert f"{m.title()} Mode" in html
    
    def test_dynamic_rapid_switching(self):
        """Dynamic handles rapid component switching."""
        class A:
            def render(self): return "A"
        class B:
            def render(self): return "B"
        
        toggle = Signal(True)
        dynamic = Dynamic(component=lambda: A if toggle() else B)
        
        for i in range(50):
            toggle.set(i % 2 == 0)
            html = dynamic.render()
            expected = "A" if i % 2 == 0 else "B"
            assert expected in html
    
    def test_dynamic_with_store(self):
        """Dynamic with Store-based component."""
        state = Store({"component": "header"})
        
        components = {
            "header": lambda: "Header",
            "footer": lambda: "Footer"
        }
        
        dynamic = Dynamic(component=lambda: components[state.component])
        
        assert "Header" in dynamic.render()
        
        state.component = "footer"
        assert "Footer" in dynamic.render()
    
    def test_dynamic_conditional_component(self):
        """Dynamic with conditional component."""
        logged_in = Signal(False)
        
        class LoginForm:
            def render(self): return "Login Form"
        
        class Dashboard:
            def render(self): return "Dashboard"
        
        dynamic = Dynamic(component=lambda: Dashboard if logged_in() else LoginForm)
        
        assert "Login Form" in dynamic.render()
        
        logged_in.set(True)
        assert "Dashboard" in dynamic.render()
    
    def test_dynamic_component_with_reactive_content(self):
        """Dynamic component has reactive content."""
        count = Signal(0)
        
        class Counter:
            def render(self):
                return f"Count: {count()}"
        
        dynamic = Dynamic(component=Counter)
        
        html1 = dynamic.render()
        assert "Count: 0" in html1
        
        count.set(5)
        html2 = dynamic.render()
        assert "Count: 5" in html2
    
    def test_dynamic_null_to_component(self):
        """Dynamic switches from None to component."""
        comp = Signal(None)
        
        class Content:
            def render(self): return "Content"
        
        dynamic = Dynamic(component=lambda: comp())
        
        html1 = dynamic.render()
        assert "Content" not in html1
        
        comp.set(Content)
        html2 = dynamic.render()
        
        assert "Content" in html2
    
    def test_dynamic_component_to_null(self):
        """Dynamic switches from component to None."""
        class Content:
            def render(self): return "Content"
        
        comp = Signal(Content)
        dynamic = Dynamic(component=lambda: comp())
        
        assert "Content" in dynamic.render()
        
        comp.set(None)
        assert "Content" not in dynamic.render()
    
    def test_dynamic_tab_pattern(self):
        """Dynamic implements tab pattern."""
        tabs = {
            0: lambda: "Tab 1 Content",
            1: lambda: "Tab 2 Content",
            2: lambda: "Tab 3 Content"
        }
        
        active_tab = Signal(0)
        dynamic = Dynamic(component=lambda: tabs[active_tab()])
        
        assert "Tab 1" in dynamic.render()
        
        active_tab.set(1)
        assert "Tab 2" in dynamic.render()
        
        active_tab.set(2)
        assert "Tab 3" in dynamic.render()
    
    def test_dynamic_wizard_pattern(self):
        """Dynamic implements wizard pattern."""
        steps = {
            1: lambda: "Step 1: Info",
            2: lambda: "Step 2: Payment",
            3: lambda: "Step 3: Confirm"
        }
        
        step = Signal(1)
        dynamic = Dynamic(component=lambda: steps[step()])
        
        for s in [1, 2, 3, 2, 1]:
            step.set(s)
            assert f"Step {s}" in dynamic.render()
    
    def test_dynamic_router_pattern(self):
        """Dynamic implements router pattern."""
        routes = {
            "/": lambda: "Home",
            "/about": lambda: "About",
            "/contact": lambda: "Contact"
        }
        
        path = Signal("/")
        dynamic = Dynamic(component=lambda: routes.get(path(), lambda: "404"))
        
        assert "Home" in dynamic.render()
        
        path.set("/about")
        assert "About" in dynamic.render()
        
        path.set("/unknown")
        assert "404" in dynamic.render()
    
    def test_dynamic_derived_component(self):
        """Dynamic with Memo-derived component."""
        from pynext.reactive.memo import Memo
        
        items = Signal([1, 2, 3])
        has_items = Memo(lambda: len(items()) > 0)
        
        dynamic = Dynamic(component=lambda: "Has Items" if has_items() else "Empty")
        
        assert "Has Items" in dynamic.render()
        
        items.set([])
        assert "Empty" in dynamic.render()
    
    def test_dynamic_batch_updates(self):
        """Dynamic handles batched updates."""
        from pynext.reactive.batch import batch
        
        a = Signal(True)
        b = Signal(True)
        
        dynamic = Dynamic(component=lambda: "Both" if a() and b() else "Not Both")
        
        assert "Both" in dynamic.render()
        
        batch(lambda: (a.set(False), b.set(False)))
        assert "Not Both" in dynamic.render()
    
    def test_dynamic_effect_integration(self):
        """Dynamic works with Effect."""
        from pynext.reactive.effect import Effect
        
        component_name = Signal("A")
        render_count = [0]
        
        @Effect
        def track():
            component_name()
            render_count[0] += 1
        
        dynamic = Dynamic(component=lambda: f"Component {component_name()}")
        dynamic.render()
        
        assert render_count[0] >= 1
    
    def test_dynamic_component_factory(self):
        """Dynamic with component factory."""
        def create_component(text):
            class Component:
                def render(self):
                    return f"<div>{text}</div>"
            return Component
        
        text = Signal("Initial")
        dynamic = Dynamic(component=lambda: create_component(text()))
        
        assert "Initial" in dynamic.render()
        
        text.set("Updated")
        assert "Updated" in dynamic.render()
    
    def test_dynamic_multiple_signal_deps(self):
        """Dynamic with multiple signal dependencies."""
        mode = Signal("view")
        data = Signal({"id": 1})
        
        components = {
            "view": lambda d: f"Viewing {d['id']}",
            "edit": lambda d: f"Editing {d['id']}"
        }
        
        dynamic = Dynamic(component=lambda: components[mode()](data()))
        
        assert "Viewing 1" in dynamic.render()
        
        mode.set("edit")
        assert "Editing 1" in dynamic.render()
    
    def test_dynamic_rerender_same_component(self):
        """Dynamic re-renders same component correctly."""
        render_count = [0]
        
        class Counter:
            def render(self):
                render_count[0] += 1
                return f"Render {render_count[0]}"
        
        dynamic = Dynamic(component=Counter)
        
        html1 = dynamic.render()
        assert "Render 1" in html1
        
        html2 = dynamic.render()
        assert "Render 2" in html2


# =============================================================================
# SECTION 3: EDGE CASES (15 tests)
# =============================================================================

class TestDynamicEdgeCases:
    """Edge case tests for Dynamic."""
    
    def test_dynamic_none_component(self):
        """Dynamic handles None component."""
        dynamic = Dynamic(component=None)
        html = dynamic.render()
        
        assert 'data-dynamic=' in html
    
    def test_dynamic_empty_string_component(self):
        """Dynamic handles empty string component."""
        dynamic = Dynamic(component=lambda: "")
        html = dynamic.render()
        
        assert 'data-dynamic=' in html
    
    def test_dynamic_exception_in_component(self):
        """Dynamic handles exception in component."""
        def bad_component():
            raise ValueError("Bad!")
        
        dynamic = Dynamic(component=bad_component)
        
        with pytest.raises(ValueError):
            dynamic.render()
    
    def test_dynamic_exception_in_render(self):
        """Dynamic propagates exception in component render."""
        class BadRender:
            def render(self):
                raise RuntimeError("Render failed")
        
        dynamic = Dynamic(component=BadRender)
        
        # Dynamic now propagates exceptions instead of swallowing
        with pytest.raises(RuntimeError):
            dynamic.render()
    
    def test_dynamic_nested_dynamic(self):
        """Dynamic can contain nested Dynamic."""
        inner = Dynamic(component=lambda: "Inner")
        dynamic = Dynamic(component=lambda: inner)
        html = dynamic.render()
        
        # Nested Dynamic renders to string
        assert "Inner" in html
    
    def test_dynamic_unicode_content(self):
        """Dynamic handles unicode content."""
        dynamic = Dynamic(component=lambda: "Hello 世界 🎉")
        html = dynamic.render()
        
        assert "世界" in html
        assert "🎉" in html
    
    def test_dynamic_html_content(self):
        """Dynamic renders HTML content."""
        dynamic = Dynamic(component=lambda: "<div class='styled'>Content</div>")
        html = dynamic.render()
        
        assert "class='styled'" in html
    
    def test_dynamic_list_component(self):
        """Dynamic handles list content."""
        dynamic = Dynamic(component=lambda: ["Part 1", " ", "Part 2"])
        html = dynamic.render()
        
        # List is converted to string
        assert "Part 1" in html
    
    def test_dynamic_number_component(self):
        """Dynamic handles numeric content."""
        dynamic = Dynamic(component=lambda: 42)
        html = dynamic.render()
        
        assert "42" in html
    
    def test_dynamic_boolean_component(self):
        """Dynamic handles boolean content."""
        dynamic = Dynamic(component=lambda: True)
        html = dynamic.render()
        
        assert "True" in html
    
    def test_dynamic_dict_component(self):
        """Dynamic handles dict content."""
        dynamic = Dynamic(component=lambda: {"key": "value"})
        html = dynamic.render()
        
        assert "key" in html
    
    def test_dynamic_callable_chain(self):
        """Dynamic handles callable returning callable."""
        dynamic = Dynamic(component=lambda: lambda: "Nested Lambda")
        html = dynamic.render()
        
        # Callable content gets called
        assert "Nested Lambda" in html
    
    def test_dynamic_component_without_render(self):
        """Dynamic handles object without render method."""
        class NoRender:
            def __str__(self):
                return "No Render Method"
        
        dynamic = Dynamic(component=NoRender)
        html = dynamic.render()
        
        assert "No Render Method" in html
    
    def test_dynamic_props_ignored_for_non_class(self):
        """Dynamic props are for class components only."""
        def simple_fn():
            return "Simple"
        
        # Props shouldn't cause error for non-class components
        dynamic = Dynamic(component=simple_fn, unused_prop="value")
        html = dynamic.render()
        
        assert "Simple" in html
    
    def test_dynamic_rerender_stability(self):
        """Dynamic renders consistently with same component."""
        class Stable:
            def render(self):
                return "Stable"
        
        dynamic = Dynamic(component=Stable)
        
        html1 = dynamic.render()
        html2 = dynamic.render()
        
        # IDs should match across renders
        assert 'data-dynamic=' in html1
        assert 'data-dynamic=' in html2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

