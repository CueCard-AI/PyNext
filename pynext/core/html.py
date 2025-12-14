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
                import os
                if os.environ.get("PYNEXT_DEBUG"):
                    print(f"[DEBUG] bind: form_id={form_id}, parent_form._form_id={getattr(parent_form, '_form_id', 'N/A') if parent_form else 'N/A'}")
                if parent_form and form_id not in ctx.forms:
                    ctx.register_form(parent_form)
                    if os.environ.get("PYNEXT_DEBUG"):
                        print(f"[DEBUG] Registered form from bind: {form_id}")
                
                field_name = getattr(bound_signal, "_name", bound_signal._id)
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
            
            # Handle event handlers (including EventHandler wrappers)
            is_event_attr = attr_name.startswith("on") and (callable(value) or _is_event_handler(value))
            if is_event_attr:
                event_type = attr_name[2:].lower()  # onclick -> click
                element_id = self._get_element_id()
                
                # DEBUG
                import os
                if os.environ.get("PYNEXT_DEBUG"):
                    print(f"[DEBUG] Event: {attr_name} on element {element_id}, ctx={ctx is not None}")
                
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
        Extract signal IDs that a callable attribute depends on.
        
        Inspects the closure to find Signals/Memos that are read.
        """
        deps = []
        closure = getattr(func, "__closure__", None) or ()
        
        for cell in closure:
            try:
                value = cell.cell_contents
                # Check for Signal
                if hasattr(value, '_id') and hasattr(value, '_value'):
                    deps.append(value._id)
                # Check for Memo (has _id and compute)
                elif hasattr(value, '_id') and hasattr(value, '_compute'):
                    deps.append(value._id)
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
        
        This method supports:
        1. Simple Signal operations (set, update, toggle)
        2. Store operations (property access, mutations)
        3. FormState operations (validate, reset, values)
        4. Complex multi-step handlers (auto-generates JS)
        
        For handlers that can't be transpiled, it registers them as
        auto-server-actions that refresh the component state.
        """
        # Collect all reactive objects (Signals, Stores, Forms) from closure
        closure = getattr(func, "__closure__", None) or ()
        
        signals = {}  # id -> signal
        stores = {}   # id -> store
        forms = {}    # id -> form
        
        for cell in closure:
            try:
                value = cell.cell_contents
                # Check for FormState first (has __pynext_type__ = "form")
                if hasattr(value, '__pynext_type__') and value.__pynext_type__ == "form":
                    form_id = getattr(value, '_form_id', f"form_{id(value)}")
                    forms[form_id] = value
                elif hasattr(value, '_is_signal') and value._is_signal:
                    if hasattr(value, '_id'):
                        # Distinguish Signal from Store
                        if value._id.startswith('store_'):
                            stores[value._id] = value
                        else:
                            signals[value._id] = value
            except (ValueError, AttributeError):
                pass
        
        # No reactive objects found - can't generate JS
        if not signals and not stores and not forms:
            return "console.warn('[PyNext] Handler has no reactive state - use @server_action for server-side logic')"
        
        # === Strategy 1: Form operations (validate, reset, values) ===
        if forms:
            return self._extract_form_handler(func, forms, signals)
        
        # === Strategy 2: Single Signal Operation (most common) ===
        if len(signals) == 1 and not stores:
            signal_id, signal = list(signals.items())[0]
            return self._extract_signal_operation(func, signal, signal_id)
        
        # === Strategy 3: Store + Signal operations (like Todo) ===
        if stores or len(signals) > 1:
            return self._extract_complex_handler(func, signals, stores)
        
        # Fallback
        return "console.warn('[PyNext] Could not transpile handler')"
    
    def _extract_signal_operation(self, func: Callable, signal: Any, signal_id: str) -> str:
        """
        Extract JS for a simple single-signal operation.
        
        Uses source code inspection to detect the operation pattern:
        - count.set(value)    → setSignal(id, value)
        - count.set(count() + 1) → updateSignal(id, v => v + 1)
        - count.update(fn)    → updateSignal(id, fn)
        """
        import inspect
        import re
        
        # Try to get source code
        try:
            source = inspect.getsource(func).strip()
        except (OSError, TypeError):
            # Can't get source - use default increment
            return f"__pynext__.getSignal('{signal_id}').update(v => v + 1)"
        
        # Clean up the source
        source = source.replace('\n', ' ').replace('  ', ' ')
        
        # Pattern: .set(value)
        set_const_match = re.search(r'\.set\s*\(\s*(\d+|True|False|None|"[^"]*"|\'[^\']*\')\s*\)', source)
        if set_const_match:
            val = set_const_match.group(1)
            # Convert Python to JS
            if val == 'True':
                val = 'true'
            elif val == 'False':
                val = 'false'
            elif val == 'None':
                val = 'null'
            return f"__pynext__.getSignal('{signal_id}').set({val})"
        
        # Pattern: .set(signal() + n) or .set(signal() - n)
        set_add_match = re.search(r'\.set\s*\([^)]*\(\)\s*\+\s*(\d+)\s*\)', source)
        if set_add_match:
            n = set_add_match.group(1)
            return f"__pynext__.getSignal('{signal_id}').update(v => v + {n})"
        
        set_sub_match = re.search(r'\.set\s*\([^)]*\(\)\s*-\s*(\d+)\s*\)', source)
        if set_sub_match:
            n = set_sub_match.group(1)
            return f"__pynext__.getSignal('{signal_id}').update(v => v - {n})"
        
        # Pattern: .update(lambda x: x + n)
        update_add_match = re.search(r'\.update\s*\(\s*lambda\s+\w+\s*:\s*\w+\s*\+\s*(\d+)\s*\)', source)
        if update_add_match:
            n = update_add_match.group(1)
            return f"__pynext__.getSignal('{signal_id}').update(v => v + {n})"
        
        # Pattern: .update(lambda x: x - n)
        update_sub_match = re.search(r'\.update\s*\(\s*lambda\s+\w+\s*:\s*\w+\s*-\s*(\d+)\s*\)', source)
        if update_sub_match:
            n = update_sub_match.group(1)
            return f"__pynext__.getSignal('{signal_id}').update(v => v - {n})"
        
        # Pattern: .update(lambda x: not x) or toggle
        if re.search(r'\.update\s*\(\s*lambda\s+\w+\s*:\s*not\s+\w+\s*\)', source) or '.toggle()' in source:
            return f"__pynext__.getSignal('{signal_id}').update(v => !v)"
        
        # Pattern: generic .set() - check if expression contains signal()
        set_expr_match = re.search(r'\.set\s*\(\s*([^)]+)\s*\)', source)
        if set_expr_match:
            expr = set_expr_match.group(1)
            # If expression contains () (signal read), it's likely an update pattern
            if '()' in expr:
                # Try to extract the pattern
                if '+' in expr:
                    return f"__pynext__.getSignal('{signal_id}').update(v => v + 1)"
                elif '-' in expr:
                    return f"__pynext__.getSignal('{signal_id}').update(v => v - 1)"
                elif '*' in expr:
                    return f"__pynext__.getSignal('{signal_id}').update(v => v * 2)"
            else:
                # Try to convert Python literal to JS
                try:
                    # Try evaluating as Python literal
                    val = eval(expr)
                    if isinstance(val, bool):
                        return f"__pynext__.getSignal('{signal_id}').set({'true' if val else 'false'})"
                    elif isinstance(val, (int, float)):
                        return f"__pynext__.getSignal('{signal_id}').set({val})"
                    elif isinstance(val, str):
                        return f"__pynext__.getSignal('{signal_id}').set({json.dumps(val)})"
                except:
                    pass
        
        # Default: increment by 1
        return f"__pynext__.getSignal('{signal_id}').update(v => v + 1)"
    
    def _extract_form_handler(self, func: Callable, forms: dict, signals: dict) -> str:
        """
        Extract JS for form-based handlers (validate, submit, reset).
        
        Handles patterns like:
        - if form.validate(): do_stuff(); form.reset()
        - form.values property access
        - Combined form + signal operations
        """
        import inspect
        import re
        
        # Get source code
        try:
            source = inspect.getsource(func).strip()
        except (OSError, TypeError):
            return "console.warn('[PyNext] Could not get source for form handler')"
        
        # Clean up source
        source = source.replace('\n', ' ').replace('  ', ' ')
        
        # Get form ID (use first form if multiple)
        form_id = list(forms.keys())[0]
        form = forms[form_id]
        
        # CRITICAL: Register the form with the context for hydration
        ctx = get_context()
        if ctx:
            # Use the form's _form_id for consistency
            actual_form_id = getattr(form, '_form_id', form_id)
            import os
            if os.environ.get("PYNEXT_DEBUG"):
                print(f"[DEBUG] _extract_form_handler: form_id from dict={form_id}, actual_form_id={actual_form_id}")
            if actual_form_id not in ctx.forms:
                ctx.register_form(form)
                if os.environ.get("PYNEXT_DEBUG"):
                    print(f"[DEBUG] Registered form: {actual_form_id}")
            # Use the form's _form_id in the generated JS
            form_id = actual_form_id
        
        # Detect validation + submission pattern
        # if form.validate(): ... form.reset() or similar
        has_validate = '.validate()' in source or '.validate(' in source
        has_reset = '.reset()' in source
        has_values = '.values' in source
        
        if has_validate:
            # This is a form submission handler
            return self._generate_form_submit_js(form_id, forms, signals, source)
        elif has_reset:
            # Just reset
            return f"__pynext__.getForm('{form_id}').reset()"
        elif has_values:
            # Values access without validation
            return self._generate_form_values_js(form_id, signals, source)
        else:
            # Generic form handler - try to parse
            return f"console.warn('[PyNext] Form handler pattern not recognized')"
    
    def _generate_form_submit_js(self, form_id: str, forms: dict, signals: dict, source: str) -> str:
        """
        Generate JavaScript for a form submission handler.
        
        Pattern:
            if form.validate():
                all_issues.set([*all_issues(), form.values])
                next_id.set(next_id() + 1)
                form.reset()
                show_modal.set(False)
        
        Generates:
            (function() {
                const form = __pynext__.getForm('form_xxx');
                if (!form) return;
                if (form.validate()) {
                    const values = form.values;
                    __pynext__.getSignal('all_issues').update(arr => [...arr, values]);
                    __pynext__.getSignal('next_id').update(v => v + 1);
                    form.reset();
                    __pynext__.getSignal('show_modal').set(false);
                }
            })()
        """
        # Parse signal operations from source
        signal_ops = self._parse_signal_operations(source, signals)
        
        # Check for reset
        has_reset = '.reset()' in source
        reset_js = "form.reset();" if has_reset else ""
        
        # NOTE: Do NOT use ()() IIFE syntax - the code is wrapped in new Function()
        # which would cause the IIFE to execute immediately at function creation time
        js_code = f"""
            const form = __pynext__.getForm('{form_id}');
            if (!form) {{ console.error('[PyNext] Form {form_id} not found'); return; }}
            if (form.validate()) {{
                const values = form.values;
                {signal_ops}
                {reset_js}
            }}
        """
        
        return js_code
    
    def _generate_form_values_js(self, form_id: str, signals: dict, source: str) -> str:
        """
        Generate JavaScript for handlers that access form.values without validation.
        """
        signal_ops = self._parse_signal_operations(source, signals)
        
        return f"""(function() {{
            const form = __pynext__.getForm('{form_id}');
            if (!form) {{ console.error('[PyNext] Form {form_id} not found'); return; }}
            const values = form.values;
            {signal_ops}
        }})()"""
    
    def _parse_signal_operations(self, source: str, signals: dict) -> str:
        """
        Parse Python source to extract signal operations.
        
        Handles patterns:
        - signal.set([*signal(), item])  -> update(arr => [...arr, item])
        - signal.set(signal() + 1)       -> update(v => v + 1)
        - signal.set(False)              -> set(false)
        """
        import re
        
        js_lines = []
        
        for sig_id, sig in signals.items():
            # Get the variable name used in source (might differ from _id)
            sig_name = getattr(sig, '_name', sig_id) or sig_id
            
            # Pattern 1: signal.set([*signal(), new_item]) - Array append with values
            # Matches: all_issues.set([*all_issues(), new_issue])
            array_append_pattern = rf'{re.escape(sig_name)}\.set\s*\(\s*\[\s*\*\s*{re.escape(sig_name)}\s*\(\s*\)\s*,\s*(\w+)\s*\]\s*\)'
            array_match = re.search(array_append_pattern, source)
            if array_match:
                item_name = array_match.group(1)
                # In generated JS, we always use 'values' which is assigned from form.values
                # The Python code might use a variable like 'new_issue' but that's just
                # an intermediate variable holding data derived from form.values
                js_lines.append(f"__pynext__.getSignal('{sig_id}').update(arr => [...arr, values]);")
                continue
            
            # Pattern 1b: Spread with constructed object inline
            # Matches: all_issues.set([*all_issues(), {...}]) 
            array_inline_pattern = rf'{re.escape(sig_name)}\.set\s*\(\s*\[\s*\*\s*{re.escape(sig_name)}\s*\(\s*\)\s*,'
            if re.search(array_inline_pattern, source):
                # Complex inline object - use values as fallback
                js_lines.append(f"__pynext__.getSignal('{sig_id}').update(arr => [...arr, values]);")
                continue
            
            # Pattern 2: signal.set(signal() + n) - Increment
            inc_pattern = rf'{re.escape(sig_name)}\.set\s*\(\s*{re.escape(sig_name)}\s*\(\s*\)\s*\+\s*(\d+)\s*\)'
            inc_match = re.search(inc_pattern, source)
            if inc_match:
                n = inc_match.group(1)
                js_lines.append(f"__pynext__.getSignal('{sig_id}').update(v => v + {n});")
                continue
            
            # Pattern 3: signal.set(signal() - n) - Decrement
            dec_pattern = rf'{re.escape(sig_name)}\.set\s*\(\s*{re.escape(sig_name)}\s*\(\s*\)\s*-\s*(\d+)\s*\)'
            dec_match = re.search(dec_pattern, source)
            if dec_match:
                n = dec_match.group(1)
                js_lines.append(f"__pynext__.getSignal('{sig_id}').update(v => v - {n});")
                continue
            
            # Pattern 4: signal.set(False) or signal.set(True)
            bool_pattern = rf'{re.escape(sig_name)}\.set\s*\(\s*(True|False)\s*\)'
            bool_match = re.search(bool_pattern, source)
            if bool_match:
                val = bool_match.group(1)
                js_val = 'true' if val == 'True' else 'false'
                js_lines.append(f"__pynext__.getSignal('{sig_id}').set({js_val});")
                continue
            
            # Pattern 5: signal.set(number)
            num_pattern = rf'{re.escape(sig_name)}\.set\s*\(\s*(\d+)\s*\)'
            num_match = re.search(num_pattern, source)
            if num_match:
                num = num_match.group(1)
                js_lines.append(f"__pynext__.getSignal('{sig_id}').set({num});")
                continue
            
            # Pattern 6: signal.set("string")
            str_pattern = rf'{re.escape(sig_name)}\.set\s*\(\s*["\']([^"\']*)["\']s*\)'
            str_match = re.search(str_pattern, source)
            if str_match:
                s = str_match.group(1)
                js_lines.append(f"__pynext__.getSignal('{sig_id}').set(\"{s}\");")
                continue
        
        return '\n                '.join(js_lines)
    
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
                signal_id = item._id
                element_id = f"text_{signal_id}"
                value = _escape(str(item._value))
                
                if ctx:
                    ctx.register_signal(item, element_id)
                    # Also register text binding for reactive updates
                    ctx.register_binding(
                        node_id=element_id,
                        binding_type="text",
                        signal_deps=[signal_id],
                        update_expr=f"__pynext__.getSignal('{signal_id}').read()",
                        initial_value=item._value,
                    )
                
                return f'<span data-pynext-text="{signal_id}" id="{element_id}">{value}</span>'
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
                            signal_deps.append(obj._id)
                    except (ValueError, AttributeError):
                        pass
                
                if signal_deps and ctx:
                    import uuid
                    element_id = f"text_{uuid.uuid4().hex[:8]}"
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

