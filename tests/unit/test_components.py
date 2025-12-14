"""
Unit tests for PyNext component decorators.

Tests @component, @page, @layout, @loading, @error, @not_found.
"""

import pytest
from pynext.core.component import (
    component, page, layout, loading, error, not_found,
    Component, PageComponent, LayoutComponent, LoadingComponent,
    ErrorComponent, NotFoundComponent,
    ComponentMeta, Show, For,
)
from pynext.core.html import div, h1, p, span, button, ul, li
from pynext.reactive import Signal


class TestComponentDecorator:
    """Tests for the @component decorator."""
    
    def test_component_decorator(self):
        """@component wraps a function as a Component."""
        @component
        def MyComponent():
            return div()["Hello"]
        
        assert isinstance(MyComponent, Component)
    
    def test_component_renders(self):
        """Component can be rendered."""
        @component
        def MyComponent():
            return div(class_="test")["Content"]
        
        result = MyComponent()
        assert hasattr(result, 'render')
        assert "Content" in result.render()
    
    def test_component_with_name(self):
        """@component can specify a custom name."""
        @component(name="CustomName")
        def MyComponent():
            return div()["Hello"]
        
        assert MyComponent.name == "CustomName"
    
    def test_component_with_args(self):
        """Component can accept arguments."""
        @component
        def Greeting(name: str):
            return div()[f"Hello, {name}!"]
        
        result = Greeting("Alice")
        assert "Hello, Alice!" in result.render()
    
    def test_component_with_kwargs(self):
        """Component can accept keyword arguments."""
        @component
        def Card(title: str = "Default", content: str = ""):
            return div()[
                h1()[title],
                p()[content]
            ]
        
        result = Card(title="My Card", content="Some content")
        rendered = result.render()
        
        assert "My Card" in rendered
        assert "Some content" in rendered
    
    def test_component_render_to_string(self):
        """Component.render_to_string() returns HTML string."""
        @component
        def MyComponent():
            return div()["Test"]
        
        html = MyComponent.render_to_string()
        assert isinstance(html, str)
        assert "<div>" in html


class TestPageDecorator:
    """Tests for the @page decorator."""
    
    def test_page_decorator(self):
        """@page wraps a function as a PageComponent."""
        @page
        def my_page():
            return div()["Page content"]
        
        assert isinstance(my_page, PageComponent)
    
    def test_page_with_title(self):
        """@page can specify a title."""
        @page(title="My Page Title")
        def my_page():
            return div()["Content"]
        
        assert my_page._meta.title == "My Page Title"
    
    def test_page_with_meta_tags(self):
        """@page can specify meta tags."""
        @page(meta=[
            {"name": "description", "content": "Page description"},
            {"name": "keywords", "content": "test, page"},
        ])
        def my_page():
            return div()["Content"]
        
        assert len(my_page._meta.meta_tags) == 2
    
    def test_page_render_full_page(self):
        """PageComponent.render_full_page() returns complete HTML document."""
        @page(title="Test Page")
        def my_page():
            return div()["Page content"]
        
        html = my_page.render_full_page()
        
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "<head>" in html
        assert "<title>Test Page</title>" in html
        assert "<body>" in html
        assert "Page content" in html
        assert "__PYNEXT_HYDRATION__" in html
    
    def test_page_is_page_property(self):
        """PageComponent.is_page is True."""
        @page
        def my_page():
            return div()["Content"]
        
        assert my_page.is_page is True


class TestLayoutDecorator:
    """Tests for the @layout decorator."""
    
    def test_layout_decorator(self):
        """@layout wraps a function as a LayoutComponent."""
        @layout
        def my_layout(children):
            return div()[children]
        
        assert isinstance(my_layout, LayoutComponent)
    
    def test_layout_receives_children(self):
        """Layout receives children and renders them."""
        @layout
        def my_layout(children):
            return div(class_="layout")[
                div(class_="header")["Header"],
                div(class_="content")[children],
                div(class_="footer")["Footer"],
            ]
        
        # Simulate rendering with children
        from pynext.core.html import raw_html
        result = my_layout._render(children=raw_html("<p>Child content</p>"))
        rendered = result.render()
        
        assert "Header" in rendered
        assert "Child content" in rendered
        assert "Footer" in rendered
    
    def test_layout_is_layout_property(self):
        """LayoutComponent.is_layout is True."""
        @layout
        def my_layout(children):
            return div()[children]
        
        assert my_layout.is_layout is True


class TestLoadingDecorator:
    """Tests for the @loading decorator."""
    
    def test_loading_decorator(self):
        """@loading wraps a function as a LoadingComponent."""
        @loading
        def my_loading():
            return div(class_="spinner")["Loading..."]
        
        assert isinstance(my_loading, LoadingComponent)
    
    def test_loading_renders(self):
        """LoadingComponent renders correctly."""
        @loading
        def my_loading():
            return div(class_="loading")[
                span(class_="spinner")[""],
                p()["Please wait..."]
            ]
        
        result = my_loading()
        rendered = result.render()
        
        assert "loading" in rendered
        assert "Please wait..." in rendered
    
    def test_loading_is_loading_property(self):
        """LoadingComponent.is_loading is True."""
        @loading
        def my_loading():
            return div()["Loading"]
        
        assert my_loading.is_loading is True


class TestErrorDecorator:
    """Tests for the @error decorator."""
    
    def test_error_decorator(self):
        """@error wraps a function as an ErrorComponent."""
        @error
        def my_error(error, reset):
            return div()[str(error)]
        
        assert isinstance(my_error, ErrorComponent)
    
    def test_error_receives_error_prop(self):
        """ErrorComponent receives error prop."""
        @error
        def my_error(error, reset):
            return div(class_="error")[
                h1()["Error occurred"],
                p()[str(error)],
            ]
        
        html = my_error.render_error(Exception("Test error"))
        
        assert "Error occurred" in html
        assert "Test error" in html
    
    def test_error_is_error_property(self):
        """ErrorComponent.is_error is True."""
        @error
        def my_error(error, reset):
            return div()[str(error)]
        
        assert my_error.is_error is True


class TestNotFoundDecorator:
    """Tests for the @not_found decorator."""
    
    def test_not_found_decorator(self):
        """@not_found wraps a function as a NotFoundComponent."""
        @not_found
        def my_404():
            return div()["Page not found"]
        
        assert isinstance(my_404, NotFoundComponent)
    
    def test_not_found_renders(self):
        """NotFoundComponent renders correctly."""
        @not_found
        def my_404():
            return div(class_="not-found")[
                h1()["404"],
                p()["The page you are looking for does not exist."]
            ]
        
        result = my_404()
        rendered = result.render()
        
        assert "404" in rendered
        assert "does not exist" in rendered
    
    def test_not_found_render_page(self):
        """NotFoundComponent.render_page() returns complete HTML."""
        @not_found
        def my_404():
            return div()["Not Found"]
        
        html = my_404.render_page()
        
        assert "<!DOCTYPE html>" in html
        assert "404 - Not Found" in html
        assert "Not Found" in html
    
    def test_not_found_is_not_found_property(self):
        """NotFoundComponent.is_not_found is True."""
        @not_found
        def my_404():
            return div()["Not Found"]
        
        assert my_404.is_not_found is True


class TestShow:
    """Tests for the Show conditional component."""
    
    def test_show_when_true(self):
        """Show renders children when condition is true."""
        show = Show(when=True)[
            div()["Visible content"]
        ]
        rendered = show.render()
        
        assert "Visible content" in rendered
    
    def test_show_when_false(self):
        """Show renders nothing when condition is false."""
        show = Show(when=False)[
            div()["Hidden content"]
        ]
        rendered = show.render()
        
        assert "Hidden content" not in rendered
        assert rendered == ""
    
    def test_show_with_fallback(self):
        """Show renders fallback when condition is false."""
        show = Show(when=False)[
            div()["Main content"]
        ].fallback(
            div()["Fallback content"]
        )
        rendered = show.render()
        
        assert "Main content" not in rendered
        assert "Fallback content" in rendered
    
    def test_show_str(self):
        """Show can be converted to string."""
        show = Show(when=True)[div()["Content"]]
        assert "<div>Content</div>" in str(show)


class TestFor:
    """Tests for the For list rendering component."""
    
    def test_for_renders_list(self):
        """For renders a list of items."""
        items = ["Apple", "Banana", "Cherry"]
        
        for_component = For(items)[
            lambda item, index: li()[item]
        ]
        rendered = for_component.render()
        
        assert "Apple" in rendered
        assert "Banana" in rendered
        assert "Cherry" in rendered
    
    def test_for_with_index(self):
        """For provides index to render function."""
        items = ["A", "B", "C"]
        
        for_component = For(items)[
            lambda item, index: li()[f"{index}: {item}"]
        ]
        rendered = for_component.render()
        
        assert "0: A" in rendered
        assert "1: B" in rendered
        assert "2: C" in rendered
    
    def test_for_with_key(self):
        """For supports custom key function."""
        items = [{"id": 1, "name": "One"}, {"id": 2, "name": "Two"}]
        
        for_component = For(items, key=lambda x: x["id"])[
            lambda item, index: li()[item["name"]]
        ]
        rendered = for_component.render()
        
        assert "One" in rendered
        assert "Two" in rendered
        assert 'data-key="1"' in rendered
        assert 'data-key="2"' in rendered
    
    def test_for_empty_list(self):
        """For handles empty list."""
        for_component = For([])[
            lambda item, index: li()[item]
        ]
        rendered = for_component.render()
        
        assert rendered == ""


class TestComponentWithSignals:
    """Tests for components using signals."""
    
    def test_component_with_signal(self):
        """Component can use signals."""
        @component
        def Counter():
            count = Signal(0)
            return div()[
                span()[count],
                button()["Increment"]
            ]
        
        result = Counter()
        rendered = result.render()
        
        assert "<span" in rendered
        assert "<button" in rendered
    
    def test_signal_in_render(self):
        """Signal value is rendered."""
        @component
        def Display():
            message = Signal("Hello, World!")
            return div()[message]
        
        result = Display()
        rendered = result.render()
        
        # Signal should serialize to data-signal attribute
        assert "data-signal" in rendered or "Hello, World!" in rendered

