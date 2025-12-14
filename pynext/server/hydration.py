"""
PyNext Server Hydration - Server-Side Utilities for Client Hydration

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This module provides server-side utilities for preparing HTML responses
that can be hydrated (made interactive) on the client.

Key responsibilities:
1. Collect reactive state from rendered components
2. Serialize state to JSON for embedding in HTML
3. Inject hydration scripts into HTML responses
4. Manage hydration markers for client-side reconnection

=============================================================================
WHY THIS EXISTS
=============================================================================

Server-side rendering (SSR) gives us:
- Fast initial page load (HTML is ready immediately)
- SEO benefits (search engines see content)
- Works without JavaScript

Hydration connects the SSR'd HTML to client-side reactivity:
- Signals become live and update the DOM
- Event handlers become interactive
- The page "comes alive" seamlessly

This module bridges the server-side render and client-side hydration.

=============================================================================
HOW IT WORKS
=============================================================================

1. Server renders component → HTML + RenderContext
2. This module extracts state from RenderContext
3. State is serialized to __PYNEXT_HYDRATION__ JSON
4. JSON is embedded in a <script> tag
5. Client loads page, sees HTML immediately
6. Client-side reactive.js reads __PYNEXT_HYDRATION__
7. Signals are created with server values
8. Event handlers are attached
9. Page is now interactive!

=============================================================================
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.core.context import RenderContext
    from pynext.reactive import Signal, Store, Memo


# =============================================================================
# HYDRATION DATA COLLECTION
# =============================================================================

@dataclass
class HydrationData:
    """
    Container for all data needed for client-side hydration.
    
    This is the server-side representation of what will become
    window.__PYNEXT_HYDRATION__ on the client.
    """
    
    render_id: str = ""
    """Unique ID for this render pass."""
    
    signals: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    """Map of signal name → {id, value, elementId}."""
    
    stores: Dict[str, Any] = field(default_factory=dict)
    """Map of store name → store data."""
    
    effects: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    """Map of effect id → {dependencies, code}."""
    
    events: Dict[str, Dict[str, str]] = field(default_factory=dict)
    """Map of element id → {event: handler_code}."""
    
    actions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    """Map of action id → {name, args}."""
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "renderId": self.render_id,
            "signals": self.signals,
            "stores": self.stores,
            "effects": self.effects,
            "events": self.events,
            "actions": self.actions,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    def is_empty(self) -> bool:
        """Check if there's no reactive state to hydrate."""
        return (
            not self.signals and 
            not self.stores and 
            not self.effects and 
            not self.events
        )


def collect_hydration_data(ctx: "RenderContext") -> HydrationData:
    """
    Extract hydration data from a render context.
    
    Called after a component renders to gather all the reactive
    state that needs to be serialized for the client.
    
    Args:
        ctx: The RenderContext from rendering
        
    Returns:
        HydrationData ready for serialization
    """
    data = HydrationData(render_id=ctx.render_id)
    
    # Collect signals
    for name, reg in ctx.signals.items():
        data.signals[name] = {
            "id": reg.signal_id,
            "value": reg.initial_value,
            "elementId": reg.element_id,
        }
    
    # Collect stores
    data.stores = ctx.stores.copy()
    
    # Collect effects
    for eid, reg in ctx.effects.items():
        data.effects[eid] = {
            "id": reg.effect_id,
            "dependencies": reg.dependencies,
            "code": reg.code,
        }
    
    # Collect event handlers
    data.events = ctx.event_handlers.copy()
    
    # Collect actions
    for aid, binding in ctx.actions.items():
        data.actions[aid] = {
            "name": binding.action_name,
            "id": binding.action_id,
            "args": binding.args_template,
        }
    
    return data


# =============================================================================
# HTML INJECTION
# =============================================================================

def inject_hydration_script(html: str, data: HydrationData) -> str:
    """
    Inject hydration data into an HTML string.
    
    Finds the </body> tag and inserts a script tag with the
    serialized hydration data just before it.
    
    Args:
        html: The rendered HTML string
        data: The hydration data to inject
        
    Returns:
        HTML with hydration script inserted
    """
    if data.is_empty():
        return html
    
    script = generate_hydration_script(data)
    
    # Insert before </body>
    if "</body>" in html:
        return html.replace("</body>", f"{script}\n</body>")
    
    # Fallback: append to end
    return html + script


def generate_hydration_script(data: HydrationData) -> str:
    """
    Generate the <script> tag containing hydration data.
    
    Args:
        data: The hydration data
        
    Returns:
        HTML script tag string
    """
    json_str = data.to_json()
    
    # Escape any </script> in the JSON to prevent XSS
    json_str = json_str.replace("</script>", "<\\/script>")
    
    return f"""<script>
    window.__PYNEXT_HYDRATION__ = {json_str};
</script>"""


def generate_runtime_script(
    src: str = "/_pynext/runtime.js",
    defer: bool = True,
    inline: bool = False,
    inline_code: str = "",
) -> str:
    """
    Generate the runtime script tag.
    
    Args:
        src: URL path to the runtime script
        defer: Whether to defer loading
        inline: Whether to inline the code
        inline_code: Code to inline if inline=True
        
    Returns:
        HTML script tag string
    """
    if inline and inline_code:
        return f"<script>{inline_code}</script>"
    
    defer_attr = " defer" if defer else ""
    return f'<script src="{src}"{defer_attr}></script>'


# =============================================================================
# HYDRATION MARKERS
# =============================================================================

def add_hydration_markers(
    html: str,
    component_id: str,
    component_name: str,
) -> str:
    """
    Add data-pynext-* attributes to the root element of HTML.
    
    These markers help the client-side hydrator identify and
    process the component.
    
    Args:
        html: The component's rendered HTML
        component_id: Unique ID for this component instance
        component_name: Name of the component (e.g., "Counter")
        
    Returns:
        HTML with hydration markers added
    """
    # Find the first opening tag
    match = re.match(r'^(\s*<\w+)', html)
    if not match:
        return html
    
    tag = match.group(1)
    markers = f' data-pynext-component="{component_name}" data-pynext-id="{component_id}"'
    
    return html.replace(tag, tag + markers, 1)


def extract_component_markers(html: str) -> List[Dict[str, str]]:
    """
    Extract all component markers from HTML.
    
    Used for debugging and testing to see what components
    are marked for hydration.
    
    Args:
        html: HTML string to search
        
    Returns:
        List of {component, id} dicts
    """
    pattern = r'data-pynext-component="([^"]+)"\s+data-pynext-id="([^"]+)"'
    matches = re.findall(pattern, html)
    
    return [
        {"component": m[0], "id": m[1]}
        for m in matches
    ]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def render_with_hydration(
    component,
    *args,
    include_runtime: bool = True,
    **kwargs,
) -> str:
    """
    Render a component with full hydration support.
    
    This is a high-level function that handles the complete
    render-to-hydrated-HTML pipeline.
    
    Args:
        component: The component to render
        *args: Arguments to pass to the component
        include_runtime: Whether to include the runtime script
        **kwargs: Keyword arguments to pass to the component
        
    Returns:
        Complete HTML string ready for the browser
    """
    from pynext.core.context import render_context
    
    with render_context() as ctx:
        # Render the component
        if hasattr(component, 'render_full_page'):
            html = component.render_full_page(*args, **kwargs)
        elif hasattr(component, 'render'):
            html = component.render(*args, **kwargs)
        elif callable(component):
            result = component(*args, **kwargs)
            html = str(result)
        else:
            html = str(component)
        
        # If render_full_page was used, it already includes hydration
        if hasattr(component, 'render_full_page'):
            return html
        
        # Otherwise, inject hydration data
        data = collect_hydration_data(ctx)
        html = inject_hydration_script(html, data)
        
        if include_runtime:
            # Insert runtime script in <head> if present
            if "<head>" in html:
                runtime = generate_runtime_script()
                html = html.replace("</head>", f"    {runtime}\n</head>")
    
    return html


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "HydrationData",
    "collect_hydration_data",
    "inject_hydration_script",
    "generate_hydration_script",
    "generate_runtime_script",
    "add_hydration_markers",
    "extract_component_markers",
    "render_with_hydration",
]

