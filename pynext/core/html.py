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
import os
from typing import Any, Callable, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.reactive import Signal
    from pynext.events import EventHandler

from pynext.core.context import get_context


def _is_event_handler(value: Any) -> bool:
    """Check if value is an EventHandler wrapper."""
    # Import here to avoid circular import
    try:
        from pynext.events import EventHandler
        return isinstance(value, EventHandler)
    except ImportError:
        return False


def _unwrap_event_handler(value: Any) -> tuple[Callable, dict]:
    """
    Unwrap an EventHandler to get the function and modifiers.
    
    Returns:
        Tuple of (handler_function, modifiers_dict)
    """
    if _is_event_handler(value):
        from pynext.events import EventHandler
        handler: EventHandler = value
        return handler.fn, handler.get_modifiers()
    return value, {}


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
    
    __slots__ = ("tag", "attrs", "children", "self_closing", "_id", "_source")
    
    # Self-closing tags
    VOID_ELEMENTS = frozenset([
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"
    ])
    
    # Global flag to enable source tracking (set by AI debug mode)
    _track_source: bool = False
    
    def __init__(
        self,
        tag: str,
        attrs: Optional[dict[str, Any]] = None,
        children: Optional[list[Child]] = None,
        self_closing: Optional[bool] = None,
        _source: Optional[str] = None,
    ):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = children or []
        self.self_closing = self_closing if self_closing is not None else (tag in self.VOID_ELEMENTS)
        self._id: Optional[str] = None
        self._source: Optional[str] = _source
        
        # Capture source location if tracking is enabled
        if Element._track_source and _source is None:
            self._source = self._capture_source()
    
    def _capture_source(self) -> Optional[str]:
        """Capture the source file and line where this element was created."""
        import traceback
        
        # Get the call stack
        stack = traceback.extract_stack()
        
        # Find the first frame outside of html.py (the user's code)
        for frame in reversed(stack[:-1]):  # Exclude the current frame
            # Skip internal frames
            if "pynext/core/html.py" in frame.filename:
                continue
            if "pynext/reactive/" in frame.filename:
                continue
            if "<" in frame.filename:  # Skip <stdin>, <module>, etc.
                continue
            
            # Get just the filename (not full path)
            import os
            filename = os.path.basename(frame.filename)
            return f"{filename}:{frame.lineno}"
        
        return None
    
    @classmethod
    def enable_source_tracking(cls, enable: bool = True) -> None:
        """Enable or disable source tracking for AI debugging."""
        cls._track_source = enable
    
    def __call__(self, **attrs) -> "Element":
        """Create a new element with merged attributes."""
        merged = {**self.attrs, **attrs}
        
        # Handle bind= attribute (two-way binding)
        # bind=signal is sugar for value=signal + oninput=lambda e: signal.set(e.target.value)
        # Also registers hydration markers for client-side reconnection
        if "bind" in merged:
            bound_signal = merged.pop("bind")
            
            # Check if it's a signal (has set method)
            if hasattr(bound_signal, "set") and hasattr(bound_signal, "_value"):
                # Set value to the signal (will render current value)
                merged["value"] = bound_signal
                
                # Mark that this element has a binding (for hydration)
                # The actual registration happens in _render_attrs
                merged["_pynext_bind"] = bound_signal
                
                # Determine bind type based on element type
                bind_type = "value"
                if merged.get("type") == "checkbox":
                    bind_type = "checked"
                    merged["checked"] = bound_signal
                    if "oninput" not in merged:
                        merged["oninput"] = lambda e, sig=bound_signal: sig.set(e.target.checked if hasattr(e, 'target') else True)
                elif merged.get("type") == "radio":
                    if "oninput" not in merged:
                        merged["oninput"] = lambda e, sig=bound_signal: sig.set(e.target.value if hasattr(e, 'target') else "")
                else:
                    if "oninput" not in merged:
                        merged["oninput"] = lambda e, sig=bound_signal: sig.set(e.target.value if hasattr(e, 'target') else "")
                
                merged["_pynext_bind_type"] = bind_type
            else:
                # Not a signal, just use as value
                merged["value"] = bound_signal
        
        return Element(self.tag, merged, list(self.children), self.self_closing, self._source)
    
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
        
        return Element(self.tag, dict(self.attrs), new_children, self.self_closing, self._source)
    
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
        
        # Add source location for AI debugging (if tracking enabled)
        if Element._track_source and self._source:
            parts.append(f'data-pynext-source="{self._source}"')
        
        # Handle form bindings first (needs element ID)
        bound_signal = self.attrs.get("_pynext_bind")
        bind_type = self.attrs.get("_pynext_bind_type", "value")
        if bound_signal and ctx:
            element_id = self._get_element_id()
            if element_id and hasattr(bound_signal, "_id"):
                # Get form ID if signal is part of a form
                form_id = getattr(bound_signal, "_form_id", None)
                parent_form = getattr(bound_signal, "_parent_form", None)
                
                if form_id is None:
                    # Fallback - shouldn't happen with updated FormState
                    form_id = f"form_{id(bound_signal)}"
                
                # Register the parent form for hydration if not already registered
                if parent_form and form_id not in ctx.forms:
                    ctx.register_form(parent_form)
                
                # Use _field_name (actual field key) if available, fallback to _name
                field_name = getattr(bound_signal, "_field_name", None) or getattr(bound_signal, "_name", bound_signal._id)
                ctx.register_form_binding(element_id, form_id, field_name, bind_type)
                
                # Also add data attribute for client-side discovery
                parts.append(f'data-pynext-bind="{bound_signal._id}"')
                parts.append(f'data-pynext-bind-type="{bind_type}"')
        
        for key, value in self.attrs.items():
            # Skip internal markers
            if key.startswith("_pynext_"):
                continue
            
            # Handle Python reserved words
            attr_name = key.rstrip("_")
            if attr_name == "class":
                attr_name = "class"
            elif attr_name == "for":
                attr_name = "for"
            
            # FUNDAMENTAL FIX: Convert data_* attributes to data-* for HTML5 compliance
            # Python uses underscores (data_issue_id) but HTML5 data attributes use hyphens (data-issue-id)
            # This is required for the dataset API to work correctly in JavaScript
            if attr_name.startswith("data_"):
                attr_name = attr_name.replace("_", "-")
            
            # Handle event handlers (including EventHandler wrappers)
            is_event_attr = attr_name.startswith("on") and (callable(value) or _is_event_handler(value))
            if is_event_attr:
                event_type = attr_name[2:].lower()  # onclick -> click
                element_id = self._get_element_id()
                
                # Unwrap EventHandler to get function and modifiers
                handler_func, event_mods = _unwrap_event_handler(value)
                
                if _is_server_action(handler_func):
                    # Server action - generate RPC call
                    action_id = handler_func._action_id
                    action_name = handler_func._action_name
                    if ctx:
                        ctx.register_action(action_name, action_id, {})
                    handler_code = f"__pynext__.callAction('{action_id}', event)"
                else:
                    # Client-side handler - try to extract signal operations
                    handler_code = self._extract_handler_code(handler_func)
                
                # DEBUG
                if os.environ.get("PYNEXT_DEBUG"):
                    print(f"[DEBUG] handler_code={handler_code[:80] if handler_code else 'None'}...")
                
                if ctx and element_id:
                    # Register event with modifiers
                    ctx.register_event(element_id, event_type, handler_code, event_mods)
                    # We'll add the event via JS hydration, not inline
                    if "id" not in self.attrs and self._id:
                        parts.append(f'id="{self._id}"')
                    
                    # FUNDAMENTAL FIX: Also store handler on element itself for For loop cloning
                    # This allows event handlers to be re-attached when items are cloned
                    # Similar to how Alpine.js stores x-on:click on elements
                    import json
                    escaped_code = handler_code.replace('"', '&quot;').replace("'", "&#39;")
                    mods_str = json.dumps(event_mods) if event_mods else "{}"
                    escaped_mods = mods_str.replace('"', '&quot;')
                    parts.append(f'data-pynext-on-{event_type}="{escaped_code}"')
                    if event_mods:
                        parts.append(f'data-pynext-mods-{event_type}="{escaped_mods}"')
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
                # Register signal for reactivity if we have a context
                if ctx:
                    element_id = self._get_element_id()
                    if element_id:
                        # Register signal with the context for hydration
                        ctx.register_signal(value, element_id)
            # Handle callable attributes (class=lambda, style=lambda, disabled=lambda)
            elif callable(value) and not attr_name.startswith("on"):
                # Evaluate callable to get initial value
                try:
                    initial_value = value()
                except Exception:
                    initial_value = ""
                
                # Serialize initial value
                if isinstance(initial_value, dict):
                    # Style dict: {"color": "red", "font-size": "12px"}
                    style_parts = [f"{k}: {v}" for k, v in initial_value.items()]
                    serialized = "; ".join(style_parts)
                elif isinstance(initial_value, bool):
                    if initial_value:
                        parts.append(attr_name)
                    continue
                else:
                    serialized = _serialize_value(initial_value)
                
                parts.append(f'{attr_name}="{serialized}"')
                
                # Register binding for reactivity
                if ctx:
                    element_id = self._get_element_id()
                    if element_id:
                        # Determine binding type based on attribute
                        if attr_name in ("class", "className"):
                            binding_type = "class"
                        elif attr_name == "style":
                            binding_type = "style"
                        else:
                            binding_type = "attr"
                        
                        # Extract signal dependencies from closure
                        signal_deps = self._extract_callable_deps(value)
                        if signal_deps:
                            update_expr = self._generate_attr_update_expr(value, signal_deps)
                            ctx.register_binding(
                                node_id=element_id,
                                binding_type=binding_type,
                                signal_deps=signal_deps,
                                update_expr=update_expr,
                                attr_name=attr_name,
                                initial_value=initial_value,
                            )
            else:
                serialized = _serialize_value(value)
                parts.append(f'{attr_name}="{serialized}"')
        
        # Make sure element has ID if we generated one
        if self._id and "id" not in self.attrs:
            has_id = any(p.startswith("id=") for p in parts)
            if not has_id:
                parts.insert(0, f'id="{self._id}"')
        
        return " ".join(parts)
    
    def _extract_callable_deps(self, func: Callable) -> list[str]:
        """
        Extract signal names that a callable attribute depends on.
        
        Inspects the closure to find Signals/Memos that are read.
        Uses signal names (not IDs) for stable client-side lookups.
        """
        deps = []
        closure = getattr(func, "__closure__", None) or ()
        
        for cell in closure:
            try:
                value = cell.cell_contents
                # Check for Signal
                if hasattr(value, '_id') and hasattr(value, '_value'):
                    # Use signal name for stable lookups (not ID which changes per render)
                    signal_name = getattr(value, '_name', None) or value._id
                    deps.append(signal_name)
                # Check for Memo (has _id and compute)
                elif hasattr(value, '_id') and hasattr(value, '_compute'):
                    memo_name = getattr(value, '_name', None) or value._id
                    deps.append(memo_name)
            except (ValueError, AttributeError):
                pass
        
        return deps
    
    def _generate_attr_update_expr(self, func: Callable, signal_deps: list[str]) -> str:
        """
        Generate JavaScript expression for a callable attribute.
        
        For simple cases like `class=lambda: "active" if x() else ""`,
        generates: `__pynext__.getSignal('x').read() ? "active" : ""`
        """
        # For now, generate a simple expression that re-evaluates by reading signals
        # A more sophisticated implementation would inspect the source code
        if len(signal_deps) == 1:
            return f"__pynext__.getSignal('{signal_deps[0]}').read()"
        elif signal_deps:
            # Multiple signals - generate expression that reads all
            reads = ", ".join(f"__pynext__.getSignal('{d}').read()" for d in signal_deps)
            return f"({reads})"
        return "''"
    
    def _extract_handler_code(self, func: Callable) -> str:
        """
        Extract JavaScript code from a Python event handler.
        
        =====================================================================
        PHASE 18.6: AST-BASED TRANSPILATION (NO REGEX FALLBACK)
        =====================================================================
        
        This method uses the Phase 18.1-18.5 transpiler to convert Python
        handlers to JavaScript. The transpiler:
        
        1. Analyzes the handler's closure to detect reactive objects
        2. Parses Python source to IR nodes using proper AST parsing
        3. Transforms IR to use __pynext__ API
        4. Emits clean, correct JavaScript
        
        FUNDAMENTAL: This uses proper AST parsing - no regex patterns.
        All handler patterns are handled by the transpiler infrastructure.
        """
        try:
            return self._extract_handler_code_ast(func)
        except Exception as e:
            # Log the error for debugging
            if os.environ.get("PYNEXT_DEBUG"):
                import traceback
                print(f"[DEBUG] AST transpile failed for handler: {e}")
                traceback.print_exc()
            
            # Return a helpful error message instead of silently failing
            return f"console.warn('[PyNext] Handler transpilation failed: {str(e).replace(chr(39), chr(92)+chr(39))}')"
    
    def _extract_handler_code_ast(self, func: Callable) -> str:
        """
        Extract JavaScript using AST-based transpilation (Phase 18.6).
        
        This is the new, correct approach that handles complex handlers.
        """
        from pynext.transpiler.reactive import analyze_handler, get_handler_source
        from pynext.transpiler.hydration import transpile_inline_handler
        from pynext.transpiler.errors import TranspileError
        
        # Get source code
        source = get_handler_source(func)
        if source is None:
            raise ValueError("Cannot get source code")
        
        # Analyze to detect reactive objects
        ctx = analyze_handler(func)
        
        if ctx.is_empty():
            return "console.warn('[PyNext] Handler has no reactive state - use @server_action for server-side logic')"
        
        # Register forms with the rendering context for hydration
        render_ctx = get_context()
        if render_ctx:
            for form_name, info in ctx.forms.items():
                if info.obj is not None and hasattr(info.obj, '_form_id'):
                    if info.obj._form_id not in render_ctx.forms:
                        render_ctx.register_form(info.obj)
        
        # Transpile using the new system
        try:
            js_code = transpile_inline_handler(func, ctx)
            return js_code
        except TranspileError as e:
            raise ValueError(f"Transpile error: {e}")
    
    # =========================================================================
    # LEGACY METHODS REMOVED (Phase 18.6)
    # =========================================================================
    # The following legacy regex-based methods have been removed in favor of
    # proper AST-based transpilation via the transpiler module:
    # - _extract_handler_code_legacy
    # - _extract_signal_operation
    # - _extract_form_handler (3 duplicate definitions removed)
    # - _extract_complex_handler
    # - _transpile_to_js
    # - _generate_form_submit_js (3 duplicate definitions removed)
    # - _generate_form_values_js (3 duplicate definitions removed)
    # - _parse_signal_operations (3 duplicate definitions removed)
    #
    # All handler transpilation now goes through _extract_handler_code_ast()
    # which uses the proper AST-based transpiler in pynext/transpiler/.
    # =========================================================================

    def _render_children(self) -> str:
        """Render children to HTML string."""
        ctx = get_context()
        parts = []
        
        def render_item(item):
            """Render a single item to string, handling nested Elements."""
            if item is None:
                return ""
            elif isinstance(item, Element):
                return item.render()
            elif hasattr(item, 'render') and callable(item.render):
                # Handle Router, Link, RawHTML and other renderable objects
                rendered = item.render()
                # If render() returns an Element, render it to string
                if isinstance(rendered, Element):
                    return rendered.render()
                return str(rendered) if rendered else ""
            elif _is_signal(item):
                # Render signal with reactive placeholder for text binding
                # Use signal name for stable lookups (not ID which changes per render)
                signal_name = getattr(item, '_name', None) or item._id
                element_id = f"text_{signal_name}"
                value = _escape(str(item._value))
                
                if ctx:
                    ctx.register_signal(item, element_id)
                    # Also register text binding for reactive updates
                    ctx.register_binding(
                        node_id=element_id,
                        binding_type="text",
                        signal_deps=[signal_name],
                        update_expr=f"__pynext__.getSignal('{signal_name}').read()",
                        initial_value=item._value,
                    )
                
                return f'<span data-pynext-text="{signal_name}" id="{element_id}">{value}</span>'
            elif callable(item) and not hasattr(item, 'render'):
                # Callable text content (lambda returning string)
                # Evaluate to get initial value
                try:
                    initial_value = item()
                    value = _escape(str(initial_value))
                except Exception:
                    value = ""
                    initial_value = ""
                
                # Try to extract signal dependencies
                signal_deps = []
                closure = getattr(item, '__closure__', None) or ()
                for cell in closure:
                    try:
                        obj = cell.cell_contents
                        if hasattr(obj, '_id') and hasattr(obj, '_value'):
                            # Use signal name for stable lookups (not ID which changes per render)
                            signal_name = getattr(obj, '_name', None) or obj._id
                            signal_deps.append(signal_name)
                    except (ValueError, AttributeError):
                        pass
                
                if signal_deps and ctx:
                    import uuid
                    element_id = f"text_{signal_deps[0]}"
                    update_expr = f"__pynext__.getSignal('{signal_deps[0]}').read()"
                    
                    ctx.register_binding(
                        node_id=element_id,
                        binding_type="text",
                        signal_deps=signal_deps,
                        update_expr=update_expr,
                        initial_value=initial_value,
                    )
                    
                    return f'<span data-pynext-text="dynamic" id="{element_id}">{value}</span>'
                
                return value
            else:
                return _escape(str(item))
        
        for child in self.children:
            if child is None:
                continue
            elif isinstance(child, (list, tuple)):
                for item in child:
                    result = render_item(item)
                    if result:
                        parts.append(result)
            else:
                result = render_item(child)
                if result:
                    parts.append(result)
        
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

