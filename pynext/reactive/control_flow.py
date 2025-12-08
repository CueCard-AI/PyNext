"""
Control Flow - DOM Primitives for Reactive Rendering

These components enable declarative control flow in templates:
- Show: Conditional rendering
- For: Keyed list reconciliation
- Switch/Match: Multi-branch conditionals
- Portal: Render outside component tree
- ErrorBoundary: Error catching

Note: Full implementation requires Phase 17.3 (Python-to-JS compiler)
for client-side rendering. This file provides the Python API.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, List, Optional, TypeVar, Union
from dataclasses import dataclass

T = TypeVar("T")
U = TypeVar("U")


class Show(Generic[T]):
    """
    Conditional rendering component.
    
    Renders children when condition is truthy, otherwise renders fallback.
    
    Usage:
        Show(
            when=lambda: user() is not None,
            fallback=p()["Please log in"]
        )[
            lambda: div()[f"Welcome, {user().name}!"]
        ]
    """
    
    def __init__(
        self,
        when: Union[bool, Callable[[], bool]],
        fallback: Optional[Any] = None,
        keyed: bool = False,
    ):
        """
        Create a Show component.
        
        Args:
            when: Condition (value or accessor)
            fallback: Content to show when condition is false
            keyed: If True, recreate children when condition changes
        """
        self.when = when
        self.fallback = fallback
        self.keyed = keyed
        self.children: Optional[Callable[[], Any]] = None
    
    def __getitem__(self, children: Union[Any, Callable[[], Any]]) -> "Show":
        """Set the children content."""
        self.children = children if callable(children) else lambda: children
        return self
    
    def render(self) -> str:
        """Render to HTML (server-side)."""
        condition = self.when() if callable(self.when) else self.when
        
        if condition:
            if self.children:
                result = self.children() if callable(self.children) else self.children
                return _render_child(result)
            return ""
        else:
            return _render_child(self.fallback) if self.fallback else ""
    
    def __str__(self) -> str:
        return self.render()


class For(Generic[T]):
    """
    Keyed list rendering with reconciliation.
    
    Efficiently renders lists with proper key-based reconciliation
    for optimal DOM updates.
    
    Usage:
        For(
            each=lambda: todos(),
            fallback=p()["No items"]
        )[
            lambda item, index: li(key=item.id)[item.text]
        ]
    """
    
    def __init__(
        self,
        each: Union[List[T], Callable[[], List[T]]],
        fallback: Optional[Any] = None,
    ):
        """
        Create a For component.
        
        Args:
            each: List or accessor returning list
            fallback: Content to show when list is empty
        """
        self.each = each
        self.fallback = fallback
        self.render_fn: Optional[Callable[[T, int], Any]] = None
    
    def __getitem__(self, render_fn: Callable[[T, int], Any]) -> "For":
        """Set the render function for each item."""
        self.render_fn = render_fn
        return self
    
    def render(self) -> str:
        """Render to HTML (server-side)."""
        items = self.each() if callable(self.each) else self.each
        
        if not items:
            return _render_child(self.fallback) if self.fallback else ""
        
        if not self.render_fn:
            return ""
        
        parts = []
        for index, item in enumerate(items):
            result = self.render_fn(item, index)
            parts.append(_render_child(result))
        
        return "".join(parts)
    
    def __str__(self) -> str:
        return self.render()


class Index(Generic[T]):
    """
    Index-based list rendering (non-keyed).
    
    Unlike For, Index doesn't use keys and is optimized for
    lists where items don't change identity (like arrays of primitives).
    
    Usage:
        Index(each=lambda: numbers())[
            lambda item, index: div()[f"Item {index}: {item}"]
        ]
    """
    
    def __init__(
        self,
        each: Union[List[T], Callable[[], List[T]]],
        fallback: Optional[Any] = None,
    ):
        self.each = each
        self.fallback = fallback
        self.render_fn: Optional[Callable[[Callable[[], T], int], Any]] = None
    
    def __getitem__(self, render_fn: Callable[[Callable[[], T], int], Any]) -> "Index":
        self.render_fn = render_fn
        return self
    
    def render(self) -> str:
        items = self.each() if callable(self.each) else self.each
        
        if not items:
            return _render_child(self.fallback) if self.fallback else ""
        
        if not self.render_fn:
            return ""
        
        parts = []
        for index, item in enumerate(items):
            # Create accessor for item
            item_accessor = lambda i=item: i
            result = self.render_fn(item_accessor, index)
            parts.append(_render_child(result))
        
        return "".join(parts)
    
    def __str__(self) -> str:
        return self.render()


class Switch:
    """
    Multi-branch conditional rendering.
    
    Renders the first Match whose condition is true.
    
    Usage:
        Switch()[
            Match(when=lambda: status() == "loading")[Spinner()],
            Match(when=lambda: status() == "error")[ErrorMessage()],
            Match(when=lambda: status() == "success")[Content()],
        ]
    """
    
    def __init__(self):
        self.matches: List[Match] = []
    
    def __getitem__(self, matches: Union[List["Match"], "Match"]) -> "Switch":
        if isinstance(matches, Match):
            self.matches = [matches]
        else:
            self.matches = list(matches)
        return self
    
    def render(self) -> str:
        for match in self.matches:
            condition = match.when() if callable(match.when) else match.when
            if condition:
                return match.render()
        return ""
    
    def __str__(self) -> str:
        return self.render()


class Match:
    """
    A branch in a Switch statement.
    
    Usage:
        Match(when=lambda: condition())[content]
    """
    
    def __init__(self, when: Union[bool, Callable[[], bool]]):
        self.when = when
        self.children: Any = None
    
    def __getitem__(self, children: Any) -> "Match":
        self.children = children
        return self
    
    def render(self) -> str:
        return _render_child(self.children)
    
    def __str__(self) -> str:
        return self.render()


class Portal:
    """
    Render content outside the component tree.
    
    Useful for modals, tooltips, dropdowns that need to escape
    their container's CSS context.
    
    Usage:
        Portal(mount="body")[
            Modal()[content]
        ]
    """
    
    def __init__(
        self,
        mount: str = "body",
        use_shadow: bool = False,
        is_svg: bool = False,
    ):
        """
        Create a Portal.
        
        Args:
            mount: CSS selector or element ID to mount to
            use_shadow: Whether to use shadow DOM
            is_svg: Whether content is SVG
        """
        self.mount = mount
        self.use_shadow = use_shadow
        self.is_svg = is_svg
        self.children: Any = None
    
    def __getitem__(self, children: Any) -> "Portal":
        self.children = children
        return self
    
    def render(self) -> str:
        """Server-side: render inline with portal marker."""
        content = _render_child(self.children)
        return f'<div data-portal="{self.mount}">{content}</div>'
    
    def __str__(self) -> str:
        return self.render()


class Dynamic(Generic[T]):
    """
    Dynamic component rendering.
    
    Renders different components based on a reactive value.
    
    Usage:
        Dynamic(
            component=lambda: components[selected()]
        )
    """
    
    def __init__(
        self,
        component: Union[type, Callable[[], type]],
        **props: Any,
    ):
        self.component = component
        self.props = props
    
    def render(self) -> str:
        comp = self.component() if callable(self.component) else self.component
        if comp is None:
            return ""
        
        # Try to instantiate and render
        if callable(comp):
            instance = comp(**self.props)
            if hasattr(instance, "render"):
                return instance.render()
            return str(instance)
        return ""
    
    def __str__(self) -> str:
        return self.render()


class ErrorBoundary:
    """
    Catch and handle errors in child components.
    
    Renders fallback UI when an error occurs in children.
    
    Usage:
        ErrorBoundary(
            fallback=lambda err, reset: div()[
                f"Error: {err}",
                button(onclick=reset)["Retry"]
            ]
        )[
            RiskyComponent()
        ]
    """
    
    def __init__(
        self,
        fallback: Callable[[Exception, Callable[[], None]], Any],
    ):
        """
        Create an ErrorBoundary.
        
        Args:
            fallback: Function receiving (error, reset) and returning UI
        """
        self.fallback = fallback
        self.children: Any = None
        self.error: Optional[Exception] = None
    
    def __getitem__(self, children: Any) -> "ErrorBoundary":
        self.children = children
        return self
    
    def reset(self) -> None:
        """Reset the error state."""
        self.error = None
    
    def render(self) -> str:
        if self.error:
            return _render_child(self.fallback(self.error, self.reset))
        
        try:
            return _render_child(self.children)
        except Exception as e:
            self.error = e
            return _render_child(self.fallback(e, self.reset))
    
    def __str__(self) -> str:
        return self.render()


class Suspense:
    """
    Show fallback while async content loads.
    
    Usage:
        Suspense(fallback=Spinner())[
            AsyncComponent()
        ]
    """
    
    def __init__(self, fallback: Any = None):
        self.fallback = fallback
        self.children: Any = None
    
    def __getitem__(self, children: Any) -> "Suspense":
        self.children = children
        return self
    
    def render(self) -> str:
        """Server-side: render with suspense boundary marker."""
        content = _render_child(self.children)
        fallback = _render_child(self.fallback) if self.fallback else ""
        
        return f'''<div data-suspense="true" data-fallback="{fallback}">{content}</div>'''
    
    def __str__(self) -> str:
        return self.render()


def _render_child(child: Any) -> str:
    """Helper to render any child to string."""
    if child is None:
        return ""
    
    if hasattr(child, "render"):
        return child.render()
    
    if callable(child):
        result = child()
        return _render_child(result)
    
    return str(child)

