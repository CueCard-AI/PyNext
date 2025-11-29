"""
PyNext Testing - Component Rendering

Stupid simple component rendering for tests.
ONE LINE to render, ONE LINE to assert.

Example:
    from pynext.testing import render, assert_text
    
    def test_button():
        result = render(Button, label="Click me")
        assert_text(result, "Click me")

Why This Exists:
    Testing React components typically requires:
    - Setting up JSDOM or a real browser
    - Complex mounting/unmounting lifecycle
    - Waiting for async renders
    - Virtual DOM diffing
    
    PyNext components are just Python functions that return HTML.
    We can test them instantly without any DOM setup.
    This is 20x faster than Jest + React Testing Library.

SolidJS Principles:
    - Direct signal access (no virtual DOM)
    - No re-render simulation needed
    - Fine-grained reactivity testing
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union
from html.parser import HTMLParser

from pynext.core.signals import Signal


# =============================================================================
# HTML Parsing for Assertions
# =============================================================================

class HTMLNode:
    """
    Represents a parsed HTML element.
    
    Like a simplified DOM node, but pure Python.
    No browser needed, no JSDOM overhead.
    """
    
    def __init__(
        self,
        tag: str,
        attrs: Dict[str, str],
        children: List[Union[str, "HTMLNode"]] = None,
        parent: Optional["HTMLNode"] = None,
    ):
        self.tag = tag
        self.attrs = attrs
        self.children = children or []
        self.parent = parent
    
    @property
    def text(self) -> str:
        """Get all text content, recursively."""
        parts = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            elif isinstance(child, HTMLNode):
                parts.append(child.text)
        return "".join(parts)
    
    @property
    def classes(self) -> List[str]:
        """Get list of CSS classes."""
        class_str = self.attrs.get("class", "")
        return class_str.split() if class_str else []
    
    def has_class(self, class_name: str) -> bool:
        """Check if element has a CSS class."""
        return class_name in self.classes
    
    def has_attribute(self, name: str, value: Optional[str] = None) -> bool:
        """Check if element has an attribute (optionally with specific value)."""
        if name not in self.attrs:
            return False
        if value is None:
            return True
        return self.attrs[name] == value
    
    def find_all(self, tag: str) -> List["HTMLNode"]:
        """Find all descendants with given tag."""
        results = []
        for child in self.children:
            if isinstance(child, HTMLNode):
                if child.tag == tag:
                    results.append(child)
                results.extend(child.find_all(tag))
        return results
    
    def find(self, tag: str) -> Optional["HTMLNode"]:
        """Find first descendant with given tag."""
        for child in self.children:
            if isinstance(child, HTMLNode):
                if child.tag == tag:
                    return child
                found = child.find(tag)
                if found:
                    return found
        return None
    
    def query_selector(self, selector: str) -> Optional["HTMLNode"]:
        """
        Simple CSS selector support.
        
        Supports:
            - Tag: "div"
            - Class: ".btn"
            - ID: "#main"
            - Tag.class: "button.primary"
        """
        # Parse selector
        if selector.startswith("#"):
            # ID selector
            target_id = selector[1:]
            return self._find_by_id(target_id)
        elif selector.startswith("."):
            # Class selector
            target_class = selector[1:]
            return self._find_by_class(target_class)
        elif "." in selector:
            # Tag.class
            tag, class_name = selector.split(".", 1)
            return self._find_by_tag_and_class(tag, class_name)
        else:
            # Tag selector
            return self.find(selector)
    
    def query_selector_all(self, selector: str) -> List["HTMLNode"]:
        """Find all elements matching selector."""
        results = []
        
        if selector.startswith("#"):
            target_id = selector[1:]
            found = self._find_by_id(target_id)
            if found:
                results.append(found)
        elif selector.startswith("."):
            target_class = selector[1:]
            results = self._find_all_by_class(target_class)
        elif "." in selector:
            tag, class_name = selector.split(".", 1)
            results = self._find_all_by_tag_and_class(tag, class_name)
        else:
            results = self.find_all(selector)
        
        return results
    
    def _find_by_id(self, target_id: str) -> Optional["HTMLNode"]:
        if self.attrs.get("id") == target_id:
            return self
        for child in self.children:
            if isinstance(child, HTMLNode):
                found = child._find_by_id(target_id)
                if found:
                    return found
        return None
    
    def _find_by_class(self, target_class: str) -> Optional["HTMLNode"]:
        if self.has_class(target_class):
            return self
        for child in self.children:
            if isinstance(child, HTMLNode):
                found = child._find_by_class(target_class)
                if found:
                    return found
        return None
    
    def _find_all_by_class(self, target_class: str) -> List["HTMLNode"]:
        results = []
        if self.has_class(target_class):
            results.append(self)
        for child in self.children:
            if isinstance(child, HTMLNode):
                results.extend(child._find_all_by_class(target_class))
        return results
    
    def _find_by_tag_and_class(self, tag: str, class_name: str) -> Optional["HTMLNode"]:
        if self.tag == tag and self.has_class(class_name):
            return self
        for child in self.children:
            if isinstance(child, HTMLNode):
                found = child._find_by_tag_and_class(tag, class_name)
                if found:
                    return found
        return None
    
    def _find_all_by_tag_and_class(self, tag: str, class_name: str) -> List["HTMLNode"]:
        results = []
        if self.tag == tag and self.has_class(class_name):
            results.append(self)
        for child in self.children:
            if isinstance(child, HTMLNode):
                results.extend(child._find_all_by_tag_and_class(tag, class_name))
        return results


class PyNextHTMLParser(HTMLParser):
    """Parse HTML string into HTMLNode tree."""
    
    def __init__(self):
        super().__init__()
        self.root: Optional[HTMLNode] = None
        self.stack: List[HTMLNode] = []
    
    def handle_starttag(self, tag: str, attrs: list):
        attrs_dict = dict(attrs)
        node = HTMLNode(tag, attrs_dict)
        
        if self.stack:
            node.parent = self.stack[-1]
            self.stack[-1].children.append(node)
        else:
            self.root = node
        
        # Don't push self-closing tags
        if tag not in ("br", "hr", "img", "input", "meta", "link", "area", "base", "col", "embed", "param", "source", "track", "wbr"):
            self.stack.append(node)
    
    def handle_endtag(self, tag: str):
        if self.stack and self.stack[-1].tag == tag:
            self.stack.pop()
    
    def handle_data(self, data: str):
        text = data.strip()
        if text and self.stack:
            self.stack[-1].children.append(text)


def parse_html(html: str) -> HTMLNode:
    """
    Parse HTML string into HTMLNode tree.
    
    Args:
        html: HTML string to parse
        
    Returns:
        Root HTMLNode of the parsed tree
    """
    parser = PyNextHTMLParser()
    parser.feed(html)
    
    if parser.root is None:
        # Return empty div if no HTML
        return HTMLNode("div", {}, [])
    
    return parser.root


# =============================================================================
# RenderResult - The Heart of Testing
# =============================================================================

@dataclass
class RenderResult:
    """
    Result of rendering a PyNext component.
    
    This is what you get back from render(). It contains:
    - The rendered HTML string
    - A parsed DOM tree for assertions
    - Any signals the component uses
    - Timing information
    
    Think of it as a "snapshot" of your component that you can
    query and assert against, without needing a browser.
    
    Example:
        result = render(Button, label="Click")
        
        # Access raw HTML
        print(result.html)
        
        # Query the DOM
        button = result.query_selector("button")
        
        # Check signals
        result.signals["count"].set(5)
    """
    
    # The raw HTML output
    html: str
    
    # Parsed DOM tree
    root: HTMLNode = field(default=None)
    
    # Component signals (for reactivity testing)
    signals: Dict[str, Signal] = field(default_factory=dict)
    
    # The component instance (if applicable)
    component: Any = None
    
    # Render timing
    render_time_ms: float = 0.0
    
    # Console output during render
    console_logs: List[str] = field(default_factory=list)
    console_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Parse HTML into DOM tree after initialization."""
        if self.root is None and self.html:
            self.root = parse_html(self.html)
    
    # -------------------------------------------------------------------------
    # DOM Queries (like document.querySelector)
    # -------------------------------------------------------------------------
    
    def query_selector(self, selector: str) -> Optional[HTMLNode]:
        """
        Find first element matching CSS selector.
        
        Example:
            button = result.query_selector("button.primary")
            header = result.query_selector("#main-header")
        """
        if self.root is None:
            return None
        return self.root.query_selector(selector)
    
    def query_selector_all(self, selector: str) -> List[HTMLNode]:
        """
        Find all elements matching CSS selector.
        
        Example:
            items = result.query_selector_all("li")
            buttons = result.query_selector_all(".btn")
        """
        if self.root is None:
            return []
        return self.root.query_selector_all(selector)
    
    def find(self, tag: str) -> Optional[HTMLNode]:
        """Find first element with tag name."""
        if self.root is None:
            return None
        return self.root.find(tag)
    
    def find_all(self, tag: str) -> List[HTMLNode]:
        """Find all elements with tag name."""
        if self.root is None:
            return []
        return self.root.find_all(tag)
    
    # -------------------------------------------------------------------------
    # Text Content
    # -------------------------------------------------------------------------
    
    @property
    def text(self) -> str:
        """Get all text content from rendered output."""
        if self.root is None:
            return ""
        return self.root.text
    
    def contains_text(self, text: str) -> bool:
        """Check if rendered output contains text."""
        return text in self.text
    
    # -------------------------------------------------------------------------
    # Re-render (for signal testing)
    # -------------------------------------------------------------------------
    
    def update(self) -> "RenderResult":
        """
        Re-render the component with current signal values.
        
        This is useful for testing reactivity:
        
            result = render(Counter, initial=0)
            result.signals["count"].set(5)
            result = result.update()
            assert_text(result, "Count: 5")
        """
        if self.component is None:
            return self
        
        # Re-render component
        start = time.perf_counter()
        html = self.component.render() if hasattr(self.component, "render") else str(self.component)
        end = time.perf_counter()
        
        return RenderResult(
            html=html,
            signals=self.signals,
            component=self.component,
            render_time_ms=(end - start) * 1000,
            console_logs=self.console_logs,
            console_errors=self.console_errors,
        )


# =============================================================================
# render() - The Main Entry Point
# =============================================================================

def render(
    component: Union[Type, Callable, Any],
    *args,
    **kwargs,
) -> RenderResult:
    """
    Render a PyNext component for testing.
    
    This is THE function you'll use in every test. It:
    1. Instantiates your component
    2. Renders it to HTML
    3. Parses the HTML into a queryable DOM
    4. Captures any signals for reactivity testing
    5. Returns a RenderResult you can assert against
    
    Args:
        component: Component class, function, or instance
        *args: Positional arguments for the component
        **kwargs: Keyword arguments (props) for the component
        
    Returns:
        RenderResult with HTML, DOM, and signals
        
    Example:
        # Render a function component
        result = render(Button, label="Click me", variant="primary")
        
        # Render a class component
        result = render(Card, title="Hello", children="World")
        
        # Render an already-instantiated component
        btn = Button(label="Test")
        result = render(btn)
    """
    signals: Dict[str, Signal] = {}
    console_logs: List[str] = []
    console_errors: List[str] = []
    
    # Start timing
    start = time.perf_counter()
    
    try:
        # Handle different component types
        if isinstance(component, type):
            # Class component - instantiate it
            instance = component(*args, **kwargs)
        elif callable(component):
            # Function component - call it
            instance = component(*args, **kwargs)
        else:
            # Already an instance
            instance = component
        
        # Render to HTML
        if hasattr(instance, "render"):
            html = instance.render()
        elif hasattr(instance, "__html__"):
            html = instance.__html__()
        elif hasattr(instance, "to_html"):
            html = instance.to_html()
        else:
            html = str(instance)
        
        # Extract signals from component
        if hasattr(instance, "__dict__"):
            for name, value in instance.__dict__.items():
                if isinstance(value, Signal):
                    signals[name] = value
        
        # Also check class-level signals
        if hasattr(instance, "__class__"):
            for name in dir(instance.__class__):
                if not name.startswith("_"):
                    try:
                        value = getattr(instance, name)
                        if isinstance(value, Signal):
                            signals[name] = value
                    except:
                        pass
        
    except Exception as e:
        console_errors.append(str(e))
        html = ""
        instance = None
    
    end = time.perf_counter()
    
    return RenderResult(
        html=html,
        signals=signals,
        component=instance,
        render_time_ms=(end - start) * 1000,
        console_logs=console_logs,
        console_errors=console_errors,
    )


def render_to_string(
    component: Union[Type, Callable, Any],
    *args,
    **kwargs,
) -> str:
    """
    Render component and return just the HTML string.
    
    Convenience function when you don't need the full RenderResult.
    
    Example:
        html = render_to_string(Button, label="Test")
        assert "<button" in html
    """
    result = render(component, *args, **kwargs)
    return result.html


# =============================================================================
# Signal Testing Utilities
# =============================================================================

def update_signal(result: RenderResult, name: str, value: Any) -> None:
    """
    Update a signal in a rendered component.
    
    This is the SolidJS way to test reactivity:
    - Directly manipulate signals
    - No simulated events needed
    - Instant feedback
    
    Args:
        result: The RenderResult from render()
        name: Name of the signal to update
        value: New value for the signal
        
    Example:
        result = render(Counter)
        update_signal(result, "count", 5)
        result = result.update()
        assert_text(result, "5")
    """
    if name not in result.signals:
        available = list(result.signals.keys())
        raise ValueError(
            f"Signal '{name}' not found. "
            f"Available signals: {available}"
        )
    
    signal = result.signals[name]
    signal.set(value)


def get_signal_value(result: RenderResult, name: str) -> Any:
    """
    Get current value of a signal in a rendered component.
    
    Args:
        result: The RenderResult from render()
        name: Name of the signal to read
        
    Returns:
        Current value of the signal
    """
    if name not in result.signals:
        available = list(result.signals.keys())
        raise ValueError(
            f"Signal '{name}' not found. "
            f"Available signals: {available}"
        )
    
    return result.signals[name]()

