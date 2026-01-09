"""
PyNext Client - CSS Variable Utilities

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides convenience functions for working with CSS custom properties 
(CSS variables). These make theming and dynamic styling much easier.

=============================================================================
WHY THIS EXISTS
=============================================================================

CSS variables are essential for:
- Theming (dark/light mode)
- Dynamic styling
- Design tokens
- Component customization

These helpers make common patterns simpler and more Pythonic.

=============================================================================
HOW IT WORKS
=============================================================================

All functions transpile to efficient DOM API calls:

    set_css_var("primary", "blue")
    -> document.documentElement.style.setProperty("--primary", "blue")

    get_css_var("primary") 
    -> getComputedStyle(document.documentElement).getPropertyValue("--primary")

=============================================================================
WHO USES THIS
=============================================================================

- Developers implementing theming
- Dynamic styling based on user preferences
- Design system implementations

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client.css_vars import set_css_var, get_css_var, set_theme
    
    # Set a single variable on :root
    set_css_var("primary-color", "#3b82f6")
    
    # Get a variable's computed value
    color = get_css_var("primary-color")
    
    # Set theme with multiple variables
    set_theme({
        "bg": "#ffffff",
        "fg": "#000000", 
        "primary": "#3b82f6",
        "secondary": "#64748b",
        "radius": "8px",
        "spacing": "16px",
    })
    
    # Set on specific element (scoped theming)
    card = document.getElementById("card")
    set_css_var("bg", "#f0f0f0", element=card)
"""

from __future__ import annotations
from typing import (
    Dict,
    Optional,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from pynext.client.dom import Element


def _ensure_var_prefix(name: str) -> str:
    """Ensure CSS variable name starts with --."""
    if name.startswith("--"):
        return name
    return f"--{name}"


def set_css_var(
    name: str,
    value: str,
    element: Optional[Element] = None
) -> None:
    """
    Set a CSS custom property (variable).
    
    WHO: Developers implementing dynamic styling or theming
    WHAT: Sets a CSS variable on an element or document root
    WHEN: Use for theming, dynamic values, design tokens
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Simpler API than raw setProperty with -- prefix handling
    HOW: Transpiles to element.style.setProperty("--name", value)
    
    Args:
        name: Variable name (with or without -- prefix)
        value: Variable value
        element: Target element (default: document.documentElement for :root)
    
    Example:
        # Set on :root (global)
        set_css_var("primary-color", "#3b82f6")
        set_css_var("--spacing", "16px")  # -- prefix works too
        
        # Set on specific element (scoped)
        card = document.getElementById("card")
        set_css_var("bg-color", "#ffffff", element=card)
    
    Transpiles to:
        document.documentElement.style.setProperty("--primary-color", "#3b82f6")
    """
    # Import here to avoid circular imports
    from pynext.client.dom import document
    
    target = element if element is not None else document.documentElement
    var_name = _ensure_var_prefix(name)
    target.style.setProperty(var_name, value)


def get_css_var(
    name: str,
    element: Optional[Element] = None
) -> str:
    """
    Get a CSS custom property's computed value.
    
    WHO: Developers reading dynamic CSS values
    WHAT: Gets the computed value of a CSS variable
    WHEN: Use to read current theme values or computed styles
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Simpler API than raw getComputedStyle + getPropertyValue
    HOW: Transpiles to getComputedStyle(el).getPropertyValue("--name")
    
    Args:
        name: Variable name (with or without -- prefix)
        element: Target element (default: document.documentElement for :root)
    
    Returns:
        The computed value, or empty string if not set
    
    Example:
        # Get from :root
        color = get_css_var("primary-color")
        spacing = get_css_var("--spacing")
        
        # Get from specific element (includes inheritance)
        card = document.getElementById("card")
        bg = get_css_var("bg-color", element=card)
    
    Transpiles to:
        getComputedStyle(document.documentElement).getPropertyValue("--primary-color")
    """
    from pynext.client.dom import document
    from pynext.client.window import window
    
    target = element if element is not None else document.documentElement
    var_name = _ensure_var_prefix(name)
    return window.getComputedStyle(target).getPropertyValue(var_name).strip()


def remove_css_var(
    name: str,
    element: Optional[Element] = None
) -> None:
    """
    Remove a CSS custom property.
    
    WHO: Developers managing dynamic styles
    WHAT: Removes a CSS variable from an element
    WHEN: Use to reset to inherited value or remove scoped override
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Clean up variables when no longer needed
    HOW: Transpiles to element.style.removeProperty("--name")
    
    Args:
        name: Variable name (with or without -- prefix)
        element: Target element (default: document.documentElement for :root)
    
    Example:
        # Remove from :root
        remove_css_var("temp-color")
        
        # Remove from specific element
        remove_css_var("override-bg", element=card)
    """
    from pynext.client.dom import document
    
    target = element if element is not None else document.documentElement
    var_name = _ensure_var_prefix(name)
    target.style.removeProperty(var_name)


def set_theme(
    variables: Dict[str, str],
    element: Optional[Element] = None
) -> None:
    """
    Set multiple CSS variables at once.
    
    WHO: Developers implementing theming systems
    WHAT: Sets multiple CSS variables in a single call
    WHEN: Use for theme switching, design token updates
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Cleaner than multiple set_css_var calls
    HOW: Transpiles to multiple setProperty calls
    
    Args:
        variables: Dictionary of variable names to values
        element: Target element (default: document.documentElement for :root)
    
    Example:
        # Light theme
        set_theme({
            "bg": "#ffffff",
            "fg": "#000000",
            "primary": "#3b82f6",
            "secondary": "#64748b",
            "border": "#e2e8f0",
            "radius": "8px",
            "spacing": "16px",
        })
        
        # Dark theme
        set_theme({
            "bg": "#1a1a2e",
            "fg": "#ffffff",
            "primary": "#60a5fa",
            "secondary": "#94a3b8",
            "border": "#334155",
        })
        
        # Scoped theme on a component
        modal = document.getElementById("modal")
        set_theme({"bg": "#000000", "fg": "#ffffff"}, element=modal)
    """
    from pynext.client.dom import document
    
    target = element if element is not None else document.documentElement
    for name, value in variables.items():
        var_name = _ensure_var_prefix(name)
        target.style.setProperty(var_name, value)


def get_theme(
    names: list[str],
    element: Optional[Element] = None
) -> Dict[str, str]:
    """
    Get multiple CSS variable values at once.
    
    WHO: Developers reading theme values
    WHAT: Gets multiple CSS variable values in a single call
    WHEN: Use for reading current theme state
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Cleaner than multiple get_css_var calls
    HOW: Transpiles to multiple getPropertyValue calls
    
    Args:
        names: List of variable names to get
        element: Target element (default: document.documentElement for :root)
    
    Returns:
        Dictionary of variable names to values
    
    Example:
        theme = get_theme(["bg", "fg", "primary"])
        # {"bg": "#ffffff", "fg": "#000000", "primary": "#3b82f6"}
    """
    from pynext.client.dom import document
    from pynext.client.window import window
    
    target = element if element is not None else document.documentElement
    computed = window.getComputedStyle(target)
    result = {}
    for name in names:
        var_name = _ensure_var_prefix(name)
        result[name] = computed.getPropertyValue(var_name).strip()
    return result


def toggle_theme(
    light_vars: Dict[str, str],
    dark_vars: Dict[str, str],
    prefer_dark: Optional[bool] = None
) -> bool:
    """
    Toggle between light and dark themes.
    
    WHO: Developers implementing dark mode
    WHAT: Switches between two theme variable sets
    WHEN: User preference change or system theme detection
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Common pattern made easy
    HOW: Uses matchMedia to detect preference, then sets appropriate theme
    
    Args:
        light_vars: CSS variables for light theme
        dark_vars: CSS variables for dark theme
        prefer_dark: Override system preference (None = use system)
    
    Returns:
        True if dark theme was applied, False if light
    
    Example:
        light = {"bg": "#ffffff", "fg": "#000000"}
        dark = {"bg": "#1a1a2e", "fg": "#ffffff"}
        
        # Use system preference
        is_dark = toggle_theme(light, dark)
        
        # Force dark mode
        toggle_theme(light, dark, prefer_dark=True)
    """
    from pynext.client.window import window
    
    if prefer_dark is None:
        # Detect system preference
        prefer_dark = window.matchMedia("(prefers-color-scheme: dark)").matches
    
    if prefer_dark:
        set_theme(dark_vars)
    else:
        set_theme(light_vars)
    
    return prefer_dark


__all__ = [
    "set_css_var",
    "get_css_var",
    "remove_css_var",
    "set_theme",
    "get_theme",
    "toggle_theme",
]

