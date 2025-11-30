"""
CSS Module API - Simple, Pythonic CSS Scoping

The main user-facing API for CSS Modules in PyNext.
Provides two ways to define scoped CSS:

1. Inline CSS with css():
   styles = css('''
       .button { padding: 8px; }
   ''')
   
2. External files with css_module():
   styles = css_module("./Button.module.css")

Both return a CSSModule object where class names are
accessed as attributes: styles.button
"""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Set, Union

from .scoper import CSSScoper, ScopedCSS, get_global_scoper


@dataclass
class CSSModule:
    """
    A scoped CSS module with attribute access to class names.
    
    This is the primary way to use CSS in PyNext components.
    Class names are accessed as attributes for IDE autocomplete.
    
    Example:
        styles = css('''
            .button { padding: 8px 16px; }
            .primary { background: blue; }
        ''')
        
        button(class_=styles.button)["Click"]
        button(class_=f"{styles.button} {styles.primary}")["Primary"]
        
    Attributes:
        _scoped: The underlying ScopedCSS result
        _source: Source file path or "inline"
        _component: Component name
    """
    _scoped: ScopedCSS
    _source: str = "inline"
    _component: str = "Unknown"
    
    def __getattr__(self, name: str) -> str:
        """
        Access scoped class names as attributes.
        
        Args:
            name: Original class name
            
        Returns:
            Scoped class name string
            
        Raises:
            AttributeError: If class not defined in CSS
            
        Example:
            >>> styles.button
            'Button_button_x7f3d'
        """
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._scoped[name]
        except KeyError:
            raise AttributeError(
                f"CSS class '{name}' not defined in {self._source}. "
                f"Available: {', '.join(self._scoped.all().keys())}"
            )
    
    def __getitem__(self, name: str) -> str:
        """Access class via bracket notation: styles['button']"""
        try:
            return self._scoped[name]
        except KeyError:
            raise KeyError(
                f"CSS class '{name}' not defined in {self._source}"
            )
    
    def __contains__(self, name: str) -> bool:
        """Check if class exists: 'button' in styles"""
        return self._scoped.has(name)
    
    def __repr__(self) -> str:
        classes = ", ".join(self._scoped.all().keys())
        return f"CSSModule({self._component}, classes=[{classes}])"
    
    def get(self, name: str, default: str = "") -> str:
        """
        Get class name with fallback.
        
        Args:
            name: Class name to get
            default: Fallback if not found
            
        Returns:
            Scoped class name or default
        """
        return self._scoped.get(name, default)
    
    def classes(self, *names: str) -> str:
        """
        Combine multiple class names.
        
        Args:
            *names: Class names to combine
            
        Returns:
            Space-separated scoped class names
            
        Example:
            styles.classes("button", "primary")
            # -> "Button_button_x7f3d Button_primary_a2b1c"
        """
        return " ".join(
            self._scoped.get(name, name) for name in names if name
        )
    
    def conditional(self, **conditions: bool) -> str:
        """
        Apply classes conditionally.
        
        Args:
            **conditions: class_name=boolean pairs
            
        Returns:
            Space-separated classes where condition is True
            
        Example:
            styles.conditional(button=True, primary=is_primary)
        """
        return " ".join(
            self._scoped.get(name, name)
            for name, condition in conditions.items()
            if condition
        )
    
    @property
    def css(self) -> str:
        """Get the scoped CSS string."""
        return self._scoped.css
    
    @property
    def all_classes(self) -> Dict[str, str]:
        """Get mapping of original to scoped names."""
        return self._scoped.all()
    
    @property 
    def component(self) -> str:
        """Get the component name."""
        return self._component
    
    @property
    def hash(self) -> str:
        """Get the hash used for scoping."""
        return self._scoped.hash


def css(
    styles: str,
    component: Optional[str] = None,
) -> CSSModule:
    """
    Create a scoped CSS module from inline CSS.
    
    Automatically detects the component name from the calling
    context (file name or class name).
    
    Args:
        styles: Raw CSS string
        component: Optional component name override
        
    Returns:
        CSSModule with scoped class names
        
    Example:
        # In components/Button.py
        styles = css('''
            .button {
                padding: 8px 16px;
                background: blue;
                color: white;
                border: none;
                border-radius: 4px;
            }
            
            .button:hover {
                background: darkblue;
            }
            
            .primary {
                background: green;
            }
            
            .secondary {
                background: gray;
            }
        ''')
        
        @component
        def Button(variant="default", children=None):
            variant_class = styles.get(variant, "")
            return button(class_=f"{styles.button} {variant_class}")[
                children
            ]
    """
    # Auto-detect component name from caller
    if component is None:
        component = _detect_component_name()
    
    # Scope the CSS
    scoper = CSSScoper(component)
    scoped = scoper.scope(styles)
    
    # Register with global scoper for bundling
    global_scoper = get_global_scoper()
    global_scoper.register(component, styles)
    
    return CSSModule(
        _scoped=scoped,
        _source="inline",
        _component=component,
    )


def css_module(
    path: str,
    component: Optional[str] = None,
) -> CSSModule:
    """
    Load a CSS module from an external file.
    
    Supports .css and .module.css files. The file is read
    at import time and scoped based on the component name.
    
    Args:
        path: Path to CSS file (relative to caller or absolute)
        component: Optional component name override
        
    Returns:
        CSSModule with scoped class names
        
    Raises:
        FileNotFoundError: If CSS file doesn't exist
        
    Example:
        # Button.module.css:
        # .button { padding: 8px; }
        # .primary { background: blue; }
        
        # Button.py:
        from pynext import css_module
        
        styles = css_module("./Button.module.css")
        
        @component
        def Button(variant="default"):
            return button(class_=styles.button)["Click"]
    """
    # Resolve path relative to caller
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    caller_dir = Path(caller_file).parent
    
    # Handle relative paths
    if path.startswith("./") or path.startswith("../"):
        css_path = caller_dir / path
    else:
        css_path = Path(path)
    
    css_path = css_path.resolve()
    
    if not css_path.exists():
        raise FileNotFoundError(
            f"CSS file not found: {css_path}\n"
            f"Relative to: {caller_file}"
        )
    
    # Read CSS content
    styles = css_path.read_text(encoding="utf-8")
    
    # Determine component name
    if component is None:
        # Use filename without .module.css or .css
        name = css_path.name
        if name.endswith(".module.css"):
            component = name[:-11]  # Remove .module.css
        elif name.endswith(".css"):
            component = name[:-4]  # Remove .css
        else:
            component = name
    
    # Scope the CSS
    scoper = CSSScoper(component)
    scoped = scoper.scope(styles)
    
    # Register with global scoper
    global_scoper = get_global_scoper()
    global_scoper.register(component, styles)
    
    return CSSModule(
        _scoped=scoped,
        _source=str(css_path),
        _component=component,
    )


def _detect_component_name() -> str:
    """
    Auto-detect component name from calling context.
    
    Looks at the call stack to find:
    1. The filename of the calling module
    2. The class name if called from a class definition
    
    Returns:
        Detected component name or "Component"
    """
    # Walk up the stack to find the real caller
    for frame_info in inspect.stack()[2:]:
        filename = frame_info.filename
        
        # Skip internal modules
        if "pynext" in filename and "css" in filename:
            continue
        
        # Get component name from filename
        path = Path(filename)
        name = path.stem
        
        # Handle common patterns
        if name in ("__init__", "__main__", "index"):
            name = path.parent.name
        
        # Check if we're in a class definition
        if frame_info.function != "<module>":
            # Try to use class name from locals
            local_vars = frame_info.frame.f_locals
            if "self" in local_vars:
                return type(local_vars["self"]).__name__
            if "__qualname__" in local_vars:
                return local_vars["__qualname__"].split(".")[0]
        
        # PascalCase the name
        return _to_pascal_case(name)
    
    return "Component"


def _to_pascal_case(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    words = name.replace("-", "_").split("_")
    return "".join(word.capitalize() for word in words if word)

