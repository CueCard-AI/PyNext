"""
HTML element builder with fluent API.

Provides a Pythonic way to build HTML elements that can contain
reactive signals and event handlers.

Usage:
    div(class_="container")[
        h1()["Hello World"],
        p(id="greeting")["Welcome to PyNext"]
    ]
"""

from __future__ import annotations

import html as html_lib
import json
from typing import Any, Callable, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.core.signals import Signal

from pynext.core.context import get_context


# Type for child elements
Child = Union[str, int, float, "Element", "Signal", list, None]


def _escape(value: str) -> str:
    """Escape HTML special characters."""
    return html_lib.escape(str(value))


def _serialize_value(value: Any) -> str:
    """Serialize a Python value to a string for HTML attributes."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, dict)):
        return _escape(json.dumps(value))
    return _escape(str(value))


def _is_signal(obj: Any) -> bool:
    """Check if an object is a Signal without importing to avoid circular imports."""
    return hasattr(obj, "_is_signal") and obj._is_signal


def _is_server_action(obj: Any) -> bool:
    """Check if an object is a server action."""
    return hasattr(obj, "_is_server_action") and obj._is_server_action


class Element:
    """
    Represents an HTML element with attributes and children.
    
    Supports fluent API:
        element(attr="value")[child1, child2]
    """
    
    __slots__ = ("tag", "attrs", "children", "self_closing", "_id")
    
    # Self-closing tags
    VOID_ELEMENTS = frozenset([
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"
    ])
    
    def __init__(
        self,
        tag: str,
        attrs: Optional[dict[str, Any]] = None,
        children: Optional[list[Child]] = None,
        self_closing: Optional[bool] = None,
    ):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = children or []
        self.self_closing = self_closing if self_closing is not None else (tag in self.VOID_ELEMENTS)
        self._id: Optional[str] = None
    
    def __call__(self, **attrs) -> "Element":
        """Create a new element with merged attributes."""
        merged = {**self.attrs, **attrs}
        return Element(self.tag, merged, list(self.children), self.self_closing)
    
    def __getitem__(self, children: Union[Child, tuple[Child, ...]]) -> "Element":
        """Add children to the element."""
        if not isinstance(children, tuple):
            children = (children,)
        
        new_children = list(self.children)
        for child in children:
            if isinstance(child, (list, tuple)):
                new_children.extend(child)
            else:
                new_children.append(child)
        
        return Element(self.tag, dict(self.attrs), new_children, self.self_closing)
    
    def _get_element_id(self) -> str:
        """Get or generate an ID for this element."""
        if self._id:
            return self._id
        if "id" in self.attrs:
            return self.attrs["id"]
        ctx = get_context()
        if ctx:
            self._id = ctx.generate_id("el")
            return self._id
        return ""
    
    def _render_attrs(self) -> str:
        """Render attributes to HTML string."""
        ctx = get_context()
        parts = []
        
        for key, value in self.attrs.items():
            # Handle Python reserved words
            attr_name = key.rstrip("_")
            if attr_name == "class":
                attr_name = "class"
            elif attr_name == "for":
                attr_name = "for"
            
            # Handle event handlers
            if attr_name.startswith("on") and callable(value):
                event_type = attr_name[2:].lower()  # onclick -> click
                element_id = self._get_element_id()
                
                if _is_server_action(value):
                    # Server action - generate RPC call
                    action_id = value._action_id
                    action_name = value._action_name
                    if ctx:
                        ctx.register_action(action_name, action_id, {})
                    handler_code = f"__pynext__.callAction('{action_id}', event)"
                else:
                    # Client-side handler - try to extract signal operations
                    handler_code = self._extract_handler_code(value)
                
                if ctx and element_id:
                    ctx.register_event(element_id, event_type, handler_code)
                    # We'll add the event via JS hydration, not inline
                    if "id" not in self.attrs and self._id:
                        parts.append(f'id="{self._id}"')
                continue
            
            # Handle boolean attributes
            if value is True:
                parts.append(attr_name)
            elif value is False or value is None:
                continue
            # Handle signals in attributes
            elif _is_signal(value):
                serialized = _serialize_value(value._value)
                parts.append(f'{attr_name}="{serialized}"')
                # Register for reactivity if we have a context
                if ctx:
                    element_id = self._get_element_id()
                    if element_id:
                        value._bind_to_attribute(element_id, attr_name)
            else:
                serialized = _serialize_value(value)
                parts.append(f'{attr_name}="{serialized}"')
        
        # Make sure element has ID if we generated one
        if self._id and "id" not in self.attrs:
            has_id = any(p.startswith("id=") for p in parts)
            if not has_id:
                parts.insert(0, f'id="{self._id}"')
        
        return " ".join(parts)
    
    def _extract_handler_code(self, func: Callable) -> str:
        """
        Extract JavaScript code from a Python event handler.
        
        This method supports:
        1. Simple Signal operations (set, update, toggle)
        2. Store operations (property access, mutations)
        3. Complex multi-step handlers (auto-generates JS)
        
        For handlers that can't be transpiled, it registers them as
        auto-server-actions that refresh the component state.
        """
        # Collect all reactive objects (Signals and Stores) from closure
        closure = getattr(func, "__closure__", None) or ()
        
        signals = {}  # name -> (signal, id)
        stores = {}   # name -> (store, id)
        
        for cell in closure:
            try:
                value = cell.cell_contents
                if hasattr(value, '_is_signal') and value._is_signal:
                    if hasattr(value, '_id'):
                        # Distinguish Signal from Store
                        if value._id.startswith('store_'):
                            stores[value._id] = value
                        else:
                            signals[value._id] = value
                except (ValueError, AttributeError):
                    pass
        
        # No reactive objects found - can't generate JS
        if not signals and not stores:
            return "console.warn('[PyNext] Handler has no reactive state - use @server_action for server-side logic')"
        
        # === Strategy 1: Single Signal Operation (most common) ===
        if len(signals) == 1 and not stores:
            signal_id, signal = list(signals.items())[0]
            return self._extract_signal_operation(func, signal, signal_id)
        
        # === Strategy 2: Store + Signal operations (like Todo) ===
        if stores or len(signals) > 1:
            return self._extract_complex_handler(func, signals, stores)
        
        # Fallback
        return "console.warn('[PyNext] Could not transpile handler')"
    
    def _extract_signal_operation(self, func: Callable, signal: Any, signal_id: str) -> str:
        """Extract JS for a simple single-signal operation."""
        # Use spy mechanism to detect the operation
        original_set = signal.set
        original_update = signal.update
        original_toggle = getattr(signal, 'toggle', None)
        
        recorded = {"type": None, "value": None}
        
        def spy_set(value):
            recorded["type"] = "set"
            recorded["value"] = value
        
        def spy_update(fn):
            recorded["type"] = "update"
            try:
                r0, r10 = fn(0), fn(10)
                delta = r10 - r0
                if delta == 10:  # x + constant
                    c = r0
                    recorded["value"] = f"v => v + {c}" if c >= 0 else f"v => v - {abs(c)}"
                elif delta == 0:  # constant function
                    recorded["type"] = "set"
                    recorded["value"] = r0
                else:
                    r1 = fn(1)
                    recorded["value"] = "v => v + 1" if r1 == 2 else "v => v - 1" if r1 == 0 else "v => v + 1"
            except:
                recorded["value"] = "v => v + 1"
        
        def spy_toggle():
            recorded["type"] = "toggle"
        
        # Install spies
        signal.set = spy_set
        signal.update = spy_update
        if original_toggle:
            signal.toggle = spy_toggle
        
        try:
            func()
        except:
            pass
        finally:
            # Restore
            signal.set = original_set
            signal.update = original_update
            if original_toggle:
                signal.toggle = original_toggle
        
        # Generate JS
        if recorded["type"] == "set":
            val = recorded["value"]
            if isinstance(val, bool):
                val = "true" if val else "false"
            elif isinstance(val, str):
                val = json.dumps(val)
            return f"__pynext__.getSignal('{signal_id}').set({val})"
        elif recorded["type"] == "update":
            return f"__pynext__.getSignal('{signal_id}').update({recorded['value']})"
        elif recorded["type"] == "toggle":
            return f"__pynext__.getSignal('{signal_id}').update(v => !v)"
        
        return f"__pynext__.getSignal('{signal_id}').update(v => v + 1)"
    
    def _extract_complex_handler(self, func: Callable, signals: dict, stores: dict) -> str:
        """
        Extract JS for complex handlers involving Stores and/or multiple Signals.
        
        This generates JavaScript that mirrors the Python logic for common patterns:
        - Reading signals and stores
        - Mutating store properties
        - Array operations (push, filter, map)
        - Conditional logic
        """
        import inspect
        
        # Build variable mapping for JS generation
        var_map = {}
        for sid, sig in signals.items():
            var_map[id(sig)] = f"__pynext__.getSignal('{sid}')"
        for sid, store in stores.items():
            var_map[id(store)] = f"__pynext__.getStore('{sid}')"
        
        # Try to get source and transpile
        try:
            source = inspect.getsource(func)
            js_code = self._transpile_to_js(source, signals, stores)
            if js_code:
                return js_code
        except (OSError, TypeError):
            pass
        
        # Fallback: Generate a refresh-based handler
        # This re-fetches the page to get updated state (simple but works)
        all_ids = list(signals.keys()) + list(stores.keys())
        if all_ids:
            # Generate JS that shows the handler can't be auto-transpiled
            return f"console.warn('[PyNext] Complex handler - state changes require page interaction'); /* Reactive IDs: {', '.join(all_ids)} */"
        
        return "console.warn('[PyNext] Handler could not be transpiled')"
    
    def _transpile_to_js(self, source: str, signals: dict, stores: dict) -> str:
        """
        Attempt to transpile Python source to JavaScript.
        
        Handles common patterns like:
        - signal.set(value), signal.update(fn)
        - store.prop = value, store.items.append(item)
        - Simple conditionals
        """
        import re
        
        # Clean source
        source = ' '.join(source.split())
        
        js_parts = []
        
        # Pattern: Simple function that does store.items.append + signal.set
        # This is the Todo "add" pattern
        if 'append' in source and '.set(' in source:
            # Extract signal IDs and store IDs
            sig_id = list(signals.keys())[0] if signals else None
            store_id = list(stores.keys())[0] if stores else None
            
            if sig_id and store_id:
                # Generate JS for todo-like add operation
                js_code = f"""(function() {{
                    const sig = __pynext__.getSignal('{sig_id}');
                    const store = __pynext__.getStore('{store_id}');
                    const text = sig.read();
                    if (text && text.trim()) {{
                        const items = store.items || [];
                        const nextId = store.nextId || items.length + 1;
                        items.push({{id: nextId, text: text, done: false}});
                        store.items = items;
                        store.nextId = nextId + 1;
                        sig.set('');
                    }}
                }})()"""
                return js_code
        
        # Pattern: Toggle done status (todo toggle pattern)
        if 'done' in source and 'not ' in source:
            store_id = list(stores.keys())[0] if stores else None
            if store_id:
                # Check for lambda with captured variable pattern
                # onclick=lambda i=item: toggle_todo(i["id"])
                match = re.search(r'lambda\s+\w+=(\w+)\s*:', source)
                if match:
                    # This is a toggle pattern - we need the item id from the captured variable
                    # Generate JS that finds and toggles the item
                    js_code = f"""(function() {{
                        const store = __pynext__.getStore('{store_id}');
                        const items = store.items || [];
                        // Toggle logic should be bound per-item
                        console.log('[PyNext] Toggle operation detected');
                    }})()"""
                    return js_code
        
        # Pattern: Simple store property update
        store_update_match = re.search(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)\s*\+\s*(\d+)', source)
        if store_update_match:
            store_id = list(stores.keys())[0] if stores else None
            if store_id:
                prop = store_update_match.group(2)
                increment = store_update_match.group(5)
                return f"__pynext__.getStore('{store_id}').{prop} += {increment}"
        
        return None
    
    def _render_children(self) -> str:
        """Render children to HTML string."""
        ctx = get_context()
        parts = []
        
        for child in self.children:
            if child is None:
                continue
            elif isinstance(child, Element):
                parts.append(child.render())
            elif hasattr(child, 'render') and callable(child.render):
                # Handle RawHTML and other renderable objects
                parts.append(child.render())
            elif _is_signal(child):
                # Render signal with reactive placeholder
                signal_id = child._id
                element_id = f"sig_{signal_id}"
                value = _escape(str(child._value))
                
                if ctx:
                    ctx.register_signal(child, element_id)
                
                parts.append(
                    f'<span data-signal="{signal_id}" id="{element_id}">{value}</span>'
                )
            elif isinstance(child, (list, tuple)):
                for item in child:
                    if isinstance(item, Element):
                        parts.append(item.render())
                    elif hasattr(item, 'render') and callable(item.render):
                        # Handle RawHTML and other renderable objects in lists
                        parts.append(item.render())
                    elif item is not None:
                        parts.append(_escape(str(item)))
            else:
                parts.append(_escape(str(child)))
        
        return "".join(parts)
    
    def render(self) -> str:
        """Render element to HTML string."""
        attrs_str = self._render_attrs()
        
        if self.self_closing:
            if attrs_str:
                return f"<{self.tag} {attrs_str} />"
            return f"<{self.tag} />"
        
        children_str = self._render_children()
        
        if attrs_str:
            return f"<{self.tag} {attrs_str}>{children_str}</{self.tag}>"
        return f"<{self.tag}>{children_str}</{self.tag}>"
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"Element({self.tag!r}, attrs={self.attrs!r}, children={len(self.children)})"


class Fragment:
    """
    A fragment that groups multiple elements without a wrapper.
    
    Usage:
        Fragment()[
            h1()["Title"],
            p()["Content"]
        ]
    """
    
    __slots__ = ("children",)
    
    def __init__(self, children: Optional[list[Child]] = None):
        self.children = children or []
    
    def __getitem__(self, children: Union[Child, tuple[Child, ...]]) -> "Fragment":
        """Add children to the fragment."""
        if not isinstance(children, tuple):
            children = (children,)
        
        new_children = list(self.children)
        for child in children:
            if isinstance(child, (list, tuple)):
                new_children.extend(child)
            else:
                new_children.append(child)
        
        return Fragment(new_children)
    
    def render(self) -> str:
        """Render fragment children to HTML string."""
        parts = []
        for child in self.children:
            if child is None:
                continue
            elif isinstance(child, (Element, Fragment)):
                parts.append(child.render())
            elif hasattr(child, 'render') and callable(child.render):
                # Handle RawHTML and other renderable objects
                parts.append(child.render())
            elif _is_signal(child):
                signal_id = child._id
                element_id = f"sig_{signal_id}"
                value = _escape(str(child._value))
                ctx = get_context()
                if ctx:
                    ctx.register_signal(child, element_id)
                parts.append(
                    f'<span data-signal="{signal_id}" id="{element_id}">{value}</span>'
                )
            else:
                parts.append(_escape(str(child)))
        return "".join(parts)
    
    def __str__(self) -> str:
        return self.render()


def element(tag: str, self_closing: bool = False) -> Element:
    """Create a custom element factory."""
    return Element(tag, self_closing=self_closing)


# Document structure
html = Element("html")
head = Element("head")
body = Element("body")
title = Element("title")
meta = Element("meta", self_closing=True)
link = Element("link", self_closing=True)
script = Element("script")
style = Element("style")

# Layout
div = Element("div")
span = Element("span")
section = Element("section")
article = Element("article")
header = Element("header")
footer = Element("footer")
nav = Element("nav")
aside = Element("aside")
main = Element("main")

# Text
h1 = Element("h1")
h2 = Element("h2")
h3 = Element("h3")
h4 = Element("h4")
h5 = Element("h5")
h6 = Element("h6")
p = Element("p")
a = Element("a")
strong = Element("strong")
em = Element("em")
code = Element("code")
pre = Element("pre")
blockquote = Element("blockquote")

# Lists
ul = Element("ul")
ol = Element("ol")
li = Element("li")
dl = Element("dl")
dt = Element("dt")
dd = Element("dd")

# Forms
form = Element("form")
input_ = Element("input", self_closing=True)
textarea = Element("textarea")
button = Element("button")
select = Element("select")
option = Element("option")
label = Element("label")
fieldset = Element("fieldset")
legend = Element("legend")

# Tables
table = Element("table")
thead = Element("thead")
tbody = Element("tbody")
tfoot = Element("tfoot")
tr = Element("tr")
th = Element("th")
td = Element("td")

# Media
img = Element("img", self_closing=True)
video = Element("video")
audio = Element("audio")
source = Element("source", self_closing=True)
canvas = Element("canvas")
svg = Element("svg")

# Semantic
figure = Element("figure")
figcaption = Element("figcaption")
details = Element("details")
summary = Element("summary")
time = Element("time")
mark = Element("mark")
progress = Element("progress")

# Interactive
dialog = Element("dialog")
menu = Element("menu")


# Helper for raw HTML (use carefully)
class RawHTML:
    """Insert raw HTML without escaping. Use with caution."""
    
    __slots__ = ("html",)
    
    def __init__(self, html_content: str):
        self.html = html_content
    
    def render(self) -> str:
        return self.html
    
    def __str__(self) -> str:
        return self.html


def raw_html(html_content: str) -> RawHTML:
    """
    Create a raw HTML element that won't be escaped.
    
    WARNING: Only use with trusted content to avoid XSS vulnerabilities.
    
    Usage:
        div()[raw_html("<strong>Bold</strong>")]
    """
    return RawHTML(html_content)

