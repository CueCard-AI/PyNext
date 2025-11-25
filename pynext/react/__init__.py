"""
React integration for PyNext.

Provides ReactComponent for rendering React npm packages
using Preact as an efficient runtime (~4KB vs ~40KB).
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Callable, Optional, Union
from dataclasses import dataclass, field

from pynext.core.context import get_context
from pynext.core.html import Element, _escape


def _is_signal(obj: Any) -> bool:
    """Check if an object is a Signal."""
    return hasattr(obj, "_is_signal") and obj._is_signal


@dataclass
class ReactComponentDef:
    """Definition for a React component to be rendered."""
    
    package: str
    component: str
    props: dict[str, Any] = field(default_factory=dict)
    children: Optional[Union[str, list, "Element"]] = None
    element_id: str = field(default_factory=lambda: f"react_{uuid.uuid4().hex[:8]}")


class ReactComponent:
    """
    Wrapper for rendering React components from npm packages.
    
    React components are rendered via Preact for optimal performance,
    reducing bundle size from ~40KB to ~4KB while maintaining compatibility.
    
    Usage:
        from pynext.react import ReactComponent
        
        # Basic usage
        ReactComponent(
            package="@mui/material",
            component="Button",
            props={"variant": "contained", "color": "primary"},
            children="Click Me"
        )
        
        # With PyNext signals (reactive props)
        count = Signal(0)
        ReactComponent(
            package="@mui/material",
            component="Slider",
            props={
                "value": count,              # Signal passed as prop
                "onChange": count.set,        # Signal setter as callback
                "min": 0,
                "max": 100
            }
        )
    """
    
    def __init__(
        self,
        package: str,
        component: str,
        props: Optional[dict[str, Any]] = None,
        children: Optional[Union[str, list, Element]] = None,
    ):
        """
        Create a React component instance.
        
        Args:
            package: NPM package name (e.g., "@mui/material")
            component: Component name to import (e.g., "Button")
            props: Props to pass to the React component
            children: Children to render inside the component
        """
        self.package = package
        self.component = component
        self.props = props or {}
        self.children = children
        self._id = f"react_{uuid.uuid4().hex[:8]}"
        self._signal_bindings: dict[str, str] = {}  # prop_name -> signal_id
        self._callback_bindings: dict[str, str] = {}  # prop_name -> signal_setter_code
        
        # Process props for signals and callbacks
        self._process_props()
    
    def _process_props(self) -> None:
        """Process props to extract signal bindings and callbacks."""
        processed_props = {}
        
        for key, value in self.props.items():
            if _is_signal(value):
                # Bind signal to prop
                self._signal_bindings[key] = value._id
                processed_props[key] = value()  # Use current value for SSR
            elif callable(value) and hasattr(value, "__self__"):
                # Check if it's a signal method (like signal.set)
                if hasattr(value.__self__, "_is_signal") and value.__self__._is_signal:
                    signal = value.__self__
                    method_name = value.__name__
                    self._callback_bindings[key] = f"__pynext__.getSignal('{signal._id}').{method_name}"
                    processed_props[key] = None  # Will be bound in JS
            elif callable(value):
                # Regular callback - try to serialize or skip
                processed_props[key] = None  # Will need special handling
            else:
                processed_props[key] = value
        
        self._processed_props = processed_props
    
    def _serialize_props(self) -> str:
        """Serialize props to JSON for hydration."""
        serializable = {}
        for key, value in self._processed_props.items():
            if value is not None:
                try:
                    json.dumps(value)
                    serializable[key] = value
                except (TypeError, ValueError):
                    pass  # Skip non-serializable
        return json.dumps(serializable)
    
    def _render_children(self) -> str:
        """Render children to HTML."""
        if self.children is None:
            return ""
        
        if isinstance(self.children, str):
            return _escape(self.children)
        elif isinstance(self.children, Element):
            return self.children.render()
        elif isinstance(self.children, list):
            parts = []
            for child in self.children:
                if isinstance(child, str):
                    parts.append(_escape(child))
                elif isinstance(child, Element):
                    parts.append(child.render())
                elif hasattr(child, "render"):
                    parts.append(child.render())
                elif child is not None:
                    parts.append(_escape(str(child)))
            return "".join(parts)
        else:
            return _escape(str(self.children))
    
    def _get_hydration_data(self) -> dict:
        """Get data needed for client-side hydration."""
        return {
            "id": self._id,
            "package": self.package,
            "component": self.component,
            "props": self._processed_props,
            "signalBindings": self._signal_bindings,
            "callbackBindings": self._callback_bindings,
            "hasChildren": self.children is not None,
        }
    
    def render(self) -> str:
        """Render the React component placeholder for SSR."""
        ctx = get_context()
        
        # Register with render context for hydration
        if ctx:
            if not hasattr(ctx, "react_components"):
                ctx.react_components = []
            ctx.react_components.append(self._get_hydration_data())
        
        # Render placeholder div that will be hydrated
        children_html = self._render_children()
        props_json = _escape(self._serialize_props())
        
        return f'''<div 
            id="{self._id}" 
            data-react-component="{self.component}"
            data-react-package="{self.package}"
            data-react-props="{props_json}"
            class="pynext-react-root"
        >{children_html}</div>'''
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"ReactComponent({self.package}/{self.component}, id={self._id})"


class ReactIsland:
    """
    Create an isolated React island for complex React component trees.
    
    Use this when you need multiple React components that share
    React context or need to communicate via React state.
    
    Usage:
        ReactIsland(
            children=[
                ReactComponent("@mui/material", "ThemeProvider", props={"theme": dark_theme})[
                    ReactComponent("@mui/material", "Button")["Click"],
                    ReactComponent("@mui/material", "TextField"),
                ]
            ]
        )
    """
    
    def __init__(
        self,
        children: Optional[list[ReactComponent]] = None,
        shared_context: Optional[dict] = None,
    ):
        self.children = children or []
        self.shared_context = shared_context or {}
        self._id = f"react_island_{uuid.uuid4().hex[:8]}"
    
    def render(self) -> str:
        """Render the React island container."""
        children_html = "".join(
            child.render() if hasattr(child, "render") else str(child)
            for child in self.children
        )
        
        context_json = _escape(json.dumps(self.shared_context))
        
        return f'''<div 
            id="{self._id}" 
            data-react-island="true"
            data-react-context="{context_json}"
            class="pynext-react-island"
        >{children_html}</div>'''
    
    def __str__(self) -> str:
        return self.render()


# Export all
__all__ = [
    "ReactComponent",
    "ReactIsland",
]

