"""
Component decorators for PyNext.

Provides @component, @page, @layout, @loading, @error, and @not_found
decorators for defining UI components with automatic render context management.
"""

from __future__ import annotations

import inspect
import functools
import json
from typing import Any, Callable, Optional, TypeVar, Union, overload, TYPE_CHECKING

from pynext.core.context import RenderContext, render_context, get_context
from pynext.core.html import Element, Fragment

if TYPE_CHECKING:
    from pynext.core.metadata import Metadata, MetadataGenerator


T = TypeVar("T")


class ComponentMeta:
    """Metadata for a component."""
    
    def __init__(
        self,
        name: str,
        fn: Callable,
        is_page: bool = False,
        is_layout: bool = False,
        is_loading: bool = False,
        is_error: bool = False,
        is_not_found: bool = False,
        layout: Optional[str] = None,
        title: Optional[str] = None,
        meta_tags: Optional[list[dict]] = None,
        metadata: Optional[Union["Metadata", Callable]] = None,
        hydration: str = "islands",
    ):
        self.name = name
        self.fn = fn
        self.is_page = is_page
        self.is_layout = is_layout
        self.is_loading = is_loading
        self.is_error = is_error
        self.is_not_found = is_not_found
        self.layout = layout
        self.title = title
        self.meta_tags = meta_tags or []
        self.metadata = metadata
        self.hydration = hydration  # "islands" (default) or "full"


class Component:
    """
    A wrapped component function with render context management.
    
    Components can be called to render their content, and they
    automatically manage the reactive context.
    """
    
    def __init__(self, meta: ComponentMeta):
        self._meta = meta
        self._fn = meta.fn
        functools.update_wrapper(self, meta.fn)
    
    def __call__(self, *args, **kwargs) -> Union[Element, Fragment, str]:
        """Render the component."""
        # Check if we're already in a render context
        existing_ctx = get_context()
        
        if existing_ctx:
            # Use existing context for nested components
            return self._render(*args, **kwargs)
        else:
            # Create new context for top-level render
            with render_context() as ctx:
                return self._render(*args, **kwargs)
    
    def _render(self, *args, **kwargs) -> Union[Element, Fragment, str]:
        """Execute the component function."""
        result = self._fn(*args, **kwargs)
        
        # Handle different return types
        if isinstance(result, (Element, Fragment)):
            return result
        elif isinstance(result, str):
            return result
        elif result is None:
            return Fragment()
        else:
            # Try to convert to string
            return str(result)
    
    def render_to_string(self, *args, **kwargs) -> str:
        """Render the component to an HTML string."""
        result = self(*args, **kwargs)
        
        if isinstance(result, (Element, Fragment)):
            return result.render()
        return str(result)
    
    def render_full_page(
        self, 
        *args, 
        layouts: Optional[list["LayoutComponent"]] = None,
        **kwargs
    ) -> str:
        """
        Render as a full HTML page with hydration script.
        
        This is used for page components to generate complete HTML.
        Optionally wraps content in nested layouts.
        """
        with render_context() as ctx:
            # Render the page content
            result = self._render(*args, **kwargs)
            
            if isinstance(result, (Element, Fragment)):
                content = result.render()
            else:
                content = str(result)
            
            # Wrap in layouts (innermost to outermost)
            if layouts:
                for layout_component in reversed(layouts):
                    # Create a wrapper element with the content
                    from pynext.core.html import raw_html
                    wrapped = layout_component._render(children=raw_html(content))
                    if isinstance(wrapped, (Element, Fragment)):
                        content = wrapped.render()
                    else:
                        content = str(wrapped)
            
            # Generate hydration data
            hydration_data = ctx.get_hydration_data()
            
            # Add React component data if present
            if hasattr(ctx, "react_components") and ctx.react_components:
                hydration_data["reactComponents"] = ctx.react_components
            
            hydration_json = json.dumps(hydration_data)
            
            # Build metadata
            title = self._meta.title or self._meta.name
            meta_tags_html = ""
            link_tags_html = ""
            
            # Use Metadata API if available
            if self._meta.metadata:
                from pynext.core.metadata import Metadata
                metadata = self._meta.metadata
                if isinstance(metadata, Metadata):
                    if metadata.title:
                        title = metadata.title
                    meta_tags_html = metadata.render_head()
            
            # Fallback to legacy meta_tags
            if not meta_tags_html and self._meta.meta_tags:
                meta_tag_list = []
                for tag in self._meta.meta_tags:
                    attrs = " ".join(f'{k}="{v}"' for k, v in tag.items())
                    meta_tag_list.append(f"<meta {attrs} />")
                meta_tags_html = "\n    ".join(meta_tag_list)
            
            # Check if React components are used
            has_react = hasattr(ctx, "react_components") and ctx.react_components
            react_scripts = ""
            if has_react:
                react_scripts = """
    <script src="/_pynext/react-bridge.js" defer></script>"""
            
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    {meta_tags_html}
    {link_tags_html}
    <script src="/_pynext/runtime.js" defer></script>{react_scripts}
    <link rel="stylesheet" href="https://unpkg.com/tailwindcss@^2/dist/tailwind.min.css" />
    <link rel="stylesheet" href="/_pynext/styles.css" />
</head>
<body>
    <div id="__pynext">{content}</div>
    <script>
        window.__PYNEXT_HYDRATION__ = {hydration_json};
    </script>
</body>
</html>"""
    
    @property
    def name(self) -> str:
        return self._meta.name
    
    @property
    def is_page(self) -> bool:
        return self._meta.is_page


class PageComponent(Component):
    """
    A page component with additional page-specific features.
    
    Pages are entry points for routes and include metadata
    for SEO and layout configuration.
    """
    
    def __init__(self, meta: ComponentMeta):
        super().__init__(meta)
        self._layouts: list["LayoutComponent"] = []
    
    def set_layouts(self, layouts: list["LayoutComponent"]) -> None:
        """Set the layout chain for this page."""
        self._layouts = layouts
    
    async def handle_request(self, request, layouts: Optional[list] = None) -> str:
        """
        Handle an HTTP request and return the rendered page.
        
        Extracts params from the request and passes them to the component.
        """
        # Extract route params and query params
        params = getattr(request, "path_params", {})
        query = dict(request.query_params) if hasattr(request, "query_params") else {}
        
        # Handle dynamic metadata if needed
        if self._meta.metadata and callable(self._meta.metadata) and not isinstance(self._meta.metadata, type):
            from pynext.core.metadata import resolve_metadata
            resolved_metadata = await resolve_metadata(self._meta.metadata, params)
            if resolved_metadata:
                # Create a new meta with resolved metadata
                self._meta.metadata = resolved_metadata
        
        # Check function signature to see what params it accepts
        sig = inspect.signature(self._fn)
        kwargs = {}
        
        for param_name, param in sig.parameters.items():
            if param_name in params:
                kwargs[param_name] = params[param_name]
            elif param_name in query:
                kwargs[param_name] = query[param_name]
            elif param_name == "request":
                kwargs["request"] = request
            elif param_name == "params":
                kwargs["params"] = params
            elif param_name == "query":
                kwargs["query"] = query
        
        # Use provided layouts or instance layouts
        page_layouts = layouts if layouts is not None else self._layouts
        
        return self.render_full_page(layouts=page_layouts, **kwargs)


@overload
def component(fn: Callable[..., Union[Element, Fragment, str]]) -> Component: ...

@overload
def component(
    *,
    name: Optional[str] = None,
) -> Callable[[Callable[..., Union[Element, Fragment, str]]], Component]: ...


def component(
    fn: Optional[Callable[..., Union[Element, Fragment, str]]] = None,
    *,
    name: Optional[str] = None,
):
    """
    Decorator to define a PyNext component.
    
    Usage:
        @component
        def MyComponent():
            return div()["Hello World"]
        
        # Or with options:
        @component(name="CustomName")
        def MyComponent():
            return div()["Hello World"]
    """
    def decorator(fn: Callable[..., Union[Element, Fragment, str]]) -> Component:
        meta = ComponentMeta(
            name=name or fn.__name__,
            fn=fn,
            is_page=False,
        )
        return Component(meta)
    
    if fn is not None:
        return decorator(fn)
    return decorator


@overload
def page(fn: Callable[..., Union[Element, Fragment, str]]) -> PageComponent: ...

@overload
def page(
    *,
    title: Optional[str] = None,
    layout: Optional[str] = None,
    meta: Optional[list[dict]] = None,
    metadata: Optional[Union["Metadata", Callable]] = None,
    hydration: str = "islands",
) -> Callable[[Callable[..., Union[Element, Fragment, str]]], PageComponent]: ...


def page(
    fn: Optional[Callable[..., Union[Element, Fragment, str]]] = None,
    *,
    title: Optional[str] = None,
    layout: Optional[str] = None,
    meta: Optional[list[dict]] = None,
    metadata: Optional[Union["Metadata", Callable]] = None,
    hydration: str = "islands",
):
    """
    Decorator to define a PyNext page component.
    
    Pages are special components that:
    - Serve as route entry points
    - Can have titles and meta tags for SEO
    - Can specify a layout wrapper
    - Render as complete HTML documents
    
    Args:
        title: Page title for <title> tag
        layout: Layout name to wrap this page
        meta: Legacy meta tags (list of dicts)
        metadata: Modern Metadata object or async function
        hydration: Hydration mode - "islands" (default) or "full"
                   - "islands": Only @island components become interactive
                   - "full": Entire page becomes reactive (like SPA)
    
    Usage:
        @page
        def index():
            return div()["Welcome to PyNext"]
        
        # With legacy meta:
        @page(title="About Us", meta=[{"name": "description", "content": "About page"}])
        def about():
            return div()["About content"]
        
        # With full hydration (entire page is reactive):
        @page(title="App", hydration="full")
        def app():
            count = signal(0)
            return div()[
                button(onclick=lambda: count.set(count() + 1))["Click"],
                span()[count()]
            ]
        
        # With Metadata API:
        @page(metadata=Metadata(
            title="Dashboard",
            description="Your dashboard",
            openGraph={"image": "/og.png"}
        ))
        def dashboard():
            return div()["Dashboard"]
    """
    def decorator(fn: Callable[..., Union[Element, Fragment, str]]) -> PageComponent:
        component_meta = ComponentMeta(
            name=fn.__name__,
            fn=fn,
            is_page=True,
            layout=layout,
            title=title,
            meta_tags=meta or [],
            metadata=metadata,
            hydration=hydration,
        )
        return PageComponent(component_meta)
    
    if fn is not None:
        return decorator(fn)
    return decorator


# =============================================================================
# Layout Component
# =============================================================================

class LayoutComponent(Component):
    """
    A layout component that wraps page content.
    
    Layouts receive a `children` prop containing the nested content.
    """
    
    def __init__(self, meta: ComponentMeta):
        super().__init__(meta)
    
    @property
    def is_layout(self) -> bool:
        return True


def layout(fn: Callable[..., Union[Element, Fragment, str]]) -> LayoutComponent:
    """
    Decorator to define a layout component.
    
    Layouts wrap pages and nested layouts, receiving content via `children`.
    
    Usage:
        # pages/layout.py (root layout)
        @layout
        def root_layout(children):
            return html()[
                head()[title()["My App"]],
                body()[
                    nav()["Navigation"],
                    main()[children],
                    footer()["Footer"]
                ]
            ]
        
        # pages/dashboard/layout.py (nested layout)
        @layout
        def dashboard_layout(children):
            return div(class_="dashboard")[
                aside()["Sidebar"],
                div(class_="content")[children]
            ]
    """
    meta = ComponentMeta(
        name=fn.__name__,
        fn=fn,
        is_layout=True,
    )
    return LayoutComponent(meta)


# =============================================================================
# Loading Component
# =============================================================================

class LoadingComponent(Component):
    """
    A loading component shown while page content is loading.
    """
    
    def __init__(self, meta: ComponentMeta):
        super().__init__(meta)
    
    @property
    def is_loading(self) -> bool:
        return True


def loading(fn: Callable[..., Union[Element, Fragment, str]]) -> LoadingComponent:
    """
    Decorator to define a loading component.
    
    Loading components are shown while page content is loading.
    
    Usage:
        # pages/loading.py (global loading)
        @loading
        def global_loading():
            return div(class_="loading")[
                div(class_="spinner"),
                p()["Loading..."]
            ]
        
        # pages/dashboard/loading.py (route-specific)
        @loading
        def dashboard_loading():
            return div(class_="skeleton")[
                div(class_="skeleton-header"),
                div(class_="skeleton-content")
            ]
    """
    meta = ComponentMeta(
        name=fn.__name__,
        fn=fn,
        is_loading=True,
    )
    return LoadingComponent(meta)


# =============================================================================
# Error Component
# =============================================================================

class ErrorComponent(Component):
    """
    An error boundary component shown when errors occur.
    
    Receives `error` and `reset` props.
    """
    
    def __init__(self, meta: ComponentMeta):
        super().__init__(meta)
    
    @property
    def is_error(self) -> bool:
        return True
    
    def render_error(self, error: Exception, reset_fn: Optional[Callable] = None) -> str:
        """Render the error component with the given error."""
        with render_context() as ctx:
            result = self._fn(error=error, reset=reset_fn)
            
            if isinstance(result, (Element, Fragment)):
                return result.render()
            return str(result)


def error(fn: Callable[..., Union[Element, Fragment, str]]) -> ErrorComponent:
    """
    Decorator to define an error boundary component.
    
    Error components receive `error` and `reset` props.
    
    Usage:
        # pages/error.py (global error)
        @error
        def global_error(error, reset):
            return div(class_="error")[
                h1()["Something went wrong!"],
                p()[str(error)],
                button(onclick=reset)["Try again"]
            ]
        
        # pages/dashboard/error.py (route-specific)
        @error
        def dashboard_error(error, reset):
            return div(class_="dashboard-error")[
                h2()["Dashboard Error"],
                pre()[str(error)],
                button(onclick=reset)["Reload Dashboard"]
            ]
    """
    meta = ComponentMeta(
        name=fn.__name__,
        fn=fn,
        is_error=True,
    )
    return ErrorComponent(meta)


# =============================================================================
# Not Found Component
# =============================================================================

class NotFoundComponent(Component):
    """
    A 404 not found component.
    """
    
    def __init__(self, meta: ComponentMeta):
        super().__init__(meta)
    
    @property
    def is_not_found(self) -> bool:
        return True
    
    def render_page(self) -> str:
        """Render as a full 404 page."""
        with render_context() as ctx:
            result = self._render()
            
            if isinstance(result, (Element, Fragment)):
                content = result.render()
            else:
                content = str(result)
            
            hydration_data = ctx.get_hydration_data()
            hydration_json = json.dumps(hydration_data)
            
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>404 - Not Found</title>
    <script src="/_pynext/runtime.js" defer></script>
    <link rel="stylesheet" href="/_pynext/styles.css" />
</head>
<body>
    <div id="__pynext">{content}</div>
    <script>
        window.__PYNEXT_HYDRATION__ = {hydration_json};
    </script>
</body>
</html>"""


def not_found(fn: Callable[..., Union[Element, Fragment, str]]) -> NotFoundComponent:
    """
    Decorator to define a 404 not found component.
    
    Usage:
        # pages/not-found.py (global 404)
        @not_found
        def custom_404():
            return div(class_="not-found")[
                h1()["404 - Page Not Found"],
                p()["The page you're looking for doesn't exist."],
                a(href="/")["Go Home"]
            ]
    """
    meta = ComponentMeta(
        name=fn.__name__,
        fn=fn,
        is_not_found=True,
    )
    return NotFoundComponent(meta)


# =============================================================================
# Component composition helpers
# =============================================================================

def children(*elements: Union[Element, Fragment, str]) -> list:
    """Helper to pass multiple children to a component."""
    return list(elements)


def slot(name: str = "default") -> Element:
    """
    Placeholder for content injection in layouts.
    
    Usage in layout:
        @component
        def Layout(children):
            return div(class_="layout")[
                header()["My App"],
                main()[children],
                footer()["Footer"]
            ]
    """
    from pynext.core.html import Element
    return Element("slot", {"name": name})


class Show:
    """
    Conditional rendering component.
    
    Usage:
        Show(when=user.logged_in)[
            div()["Welcome back!"]
        ].fallback(
            div()["Please log in"]
        )
    """
    
    def __init__(self, when: bool):
        self._condition = when
        self._children: list = []
        self._fallback_content: Optional[Union[Element, Fragment, str]] = None
    
    def __getitem__(self, children) -> "Show":
        if not isinstance(children, tuple):
            children = (children,)
        self._children = list(children)
        return self
    
    def fallback(self, content: Union[Element, Fragment, str]) -> "Show":
        """Set fallback content when condition is false."""
        self._fallback_content = content
        return self
    
    def render(self) -> str:
        if self._condition:
            parts = []
            for child in self._children:
                if isinstance(child, (Element, Fragment)):
                    parts.append(child.render())
                elif child is not None:
                    parts.append(str(child))
            return "".join(parts)
        elif self._fallback_content:
            if isinstance(self._fallback_content, (Element, Fragment)):
                return self._fallback_content.render()
            return str(self._fallback_content)
        return ""
    
    def __str__(self) -> str:
        return self.render()


class For:
    """
    List rendering component.
    
    Usage:
        For(items, key=lambda item: item.id)[
            lambda item, index: li()[item.name]
        ]
    """
    
    def __init__(self, items: list, key: Optional[Callable[[Any], str]] = None):
        self._items = items
        self._key_fn = key or (lambda x: str(id(x)))
        self._render_fn: Optional[Callable[[Any, int], Union[Element, Fragment, str]]] = None
    
    def __getitem__(self, render_fn: Callable[[Any, int], Union[Element, Fragment, str]]) -> "For":
        self._render_fn = render_fn
        return self
    
    def render(self) -> str:
        if not self._render_fn:
            return ""
        
        parts = []
        for index, item in enumerate(self._items):
            key = self._key_fn(item)
            result = self._render_fn(item, index)
            
            if isinstance(result, (Element, Fragment)):
                rendered = result.render()
            else:
                rendered = str(result) if result is not None else ""
            
            # Wrap with key for reconciliation
            parts.append(f'<template data-key="{key}">{rendered}</template>')
        
        return "".join(parts)
    
    def __str__(self) -> str:
        return self.render()

