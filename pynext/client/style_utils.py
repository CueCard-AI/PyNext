"""
PyNext Client - Style Utilities

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides utility functions for common styling patterns including:
- classes() - Conditional class name builder (like clsx/classnames)
- set_styles() - Bulk style updates
- toggle_class() - Conditional class toggling

=============================================================================
WHY THIS EXISTS
=============================================================================

Common patterns in web development made simpler and more Pythonic:
- Building conditional class strings is verbose in plain Python
- Bulk style updates require multiple lines
- Class toggling based on state is a common pattern

=============================================================================
HOW IT WORKS
=============================================================================

These functions compile to efficient JavaScript:

    classes("btn", ("active", is_active))
    -> "btn" + (is_active ? " active" : "")

=============================================================================
WHO USES THIS
=============================================================================

- Component developers building conditional UIs
- Developers migrating from React (familiar with clsx/classnames)
- Anyone doing dynamic styling

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client.style_utils import classes, set_styles, toggle_class
    
    # Conditional classes
    el.className = classes(
        "card",
        "shadow",
        ("active", is_selected),
        ("disabled", not is_enabled),
        {"error": has_error, "success": is_success},
    )
    
    # Bulk styles
    set_styles(el, {
        "display": "flex",
        "gap": "8px",
        "padding": "16px",
    })
    
    # Toggle class based on condition
    toggle_class(el, "visible", should_show)
"""

from __future__ import annotations
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Union,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from pynext.client.dom import Element


# Type for classes() arguments
ClassValue = Union[
    str,                          # "class-name"
    None,                         # Ignored
    bool,                         # Ignored if False
    Tuple[str, bool],            # ("class", condition)
    List[str],                   # ["class1", "class2"]
    Dict[str, bool],             # {"class": condition}
]


def classes(*args: ClassValue) -> str:
    """
    Build a class string from conditional values.
    
    WHO: Developers building dynamic class names
    WHAT: Combines class names based on conditions
    WHEN: Use when class names depend on component state
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Cleaner than string concatenation with conditions
    HOW: Similar to clsx/classnames libraries in JavaScript
    
    Args:
        *args: Class values in various formats:
            - str: Always included
            - None/False: Ignored
            - (str, bool): Included if condition is True
            - [str, ...]: All strings included
            - {str: bool}: Each class included if its condition is True
    
    Returns:
        Space-separated class string
    
    Example:
        # Basic usage
        classes("btn", "primary")  # "btn primary"
        
        # Conditional with tuple
        classes("btn", ("active", is_active))  # "btn active" if is_active
        
        # Dictionary style
        classes("card", {"selected": is_selected, "disabled": is_disabled})
        
        # Mixed
        el.className = classes(
            "card",
            "shadow-md",
            ("hover:scale-105", enable_hover),
            ["rounded-lg", "border"],
            {
                "bg-blue-500": variant == "primary",
                "bg-gray-500": variant == "secondary",
                "opacity-50": is_disabled,
            },
        )
    """
    result: List[str] = []
    
    for arg in args:
        if arg is None or arg is False:
            continue
        
        if isinstance(arg, str):
            if arg:
                result.append(arg)
        
        elif isinstance(arg, tuple) and len(arg) == 2:
            class_name, condition = arg
            if condition and class_name:
                result.append(class_name)
        
        elif isinstance(arg, list):
            for class_name in arg:
                if class_name:
                    result.append(class_name)
        
        elif isinstance(arg, dict):
            for class_name, condition in arg.items():
                if condition and class_name:
                    result.append(class_name)
    
    return " ".join(result)


def set_styles(element: Element, styles: Dict[str, str]) -> None:
    """
    Set multiple inline styles at once.
    
    WHO: Developers applying multiple styles
    WHAT: Sets multiple CSS properties on an element
    WHEN: Use when setting multiple related styles together
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Cleaner than multiple property assignments
    HOW: Transpiles to multiple setProperty calls
    
    Args:
        element: Target DOM element
        styles: Dictionary of style property-value pairs (camelCase or kebab-case)
    
    Example:
        set_styles(el, {
            "display": "flex",
            "flexDirection": "column",  # camelCase works
            "gap": "8px",
            "padding": "16px",
            "background-color": "white",  # kebab-case also works
        })
    """
    for prop, value in styles.items():
        element.style.setProperty(prop, value)


def toggle_class(
    element: Element,
    class_name: str,
    condition: bool
) -> None:
    """
    Add or remove a class based on a condition.
    
    WHO: Developers toggling classes based on state
    WHAT: Adds class if condition is True, removes if False
    WHEN: Use when a single class depends on a boolean
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Cleaner than if/else with add/remove
    HOW: Transpiles to classList.toggle(class, force)
    
    Args:
        element: Target DOM element
        class_name: Class to toggle
        condition: True to add, False to remove
    
    Example:
        toggle_class(btn, "active", is_selected)
        toggle_class(modal, "visible", should_show)
        toggle_class(input, "error", has_validation_error)
    """
    element.classList.toggle(class_name, condition)


def add_classes(element: Element, *class_names: str) -> None:
    """
    Add multiple classes to an element.
    
    WHO: Developers adding multiple classes
    WHAT: Adds one or more classes to an element
    WHEN: Use when adding several classes at once
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Cleaner than multiple classList.add calls
    HOW: Transpiles to classList.add(class1, class2, ...)
    
    Args:
        element: Target DOM element
        *class_names: Classes to add
    
    Example:
        add_classes(el, "card", "shadow", "rounded")
    """
    element.classList.add(*class_names)


def remove_classes(element: Element, *class_names: str) -> None:
    """
    Remove multiple classes from an element.
    
    WHO: Developers removing multiple classes
    WHAT: Removes one or more classes from an element
    WHEN: Use when removing several classes at once
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Cleaner than multiple classList.remove calls
    HOW: Transpiles to classList.remove(class1, class2, ...)
    
    Args:
        element: Target DOM element
        *class_names: Classes to remove
    
    Example:
        remove_classes(el, "hidden", "disabled")
    """
    element.classList.remove(*class_names)


def has_class(element: Element, class_name: str) -> bool:
    """
    Check if an element has a class.
    
    WHO: Developers checking class presence
    WHAT: Returns True if element has the class
    WHEN: Use for conditional logic based on classes
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Shorter than classList.contains
    HOW: Transpiles to classList.contains(class)
    
    Args:
        element: Target DOM element
        class_name: Class to check
    
    Returns:
        True if element has the class
    
    Example:
        if has_class(el, "active"):
            do_something()
    """
    return element.classList.contains(class_name)


def replace_class(
    element: Element,
    old_class: str,
    new_class: str
) -> bool:
    """
    Replace one class with another.
    
    WHO: Developers swapping classes
    WHAT: Replaces old_class with new_class
    WHEN: Use for state transitions (e.g., "loading" -> "loaded")
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Atomic operation, cleaner than remove + add
    HOW: Transpiles to classList.replace(old, new)
    
    Args:
        element: Target DOM element
        old_class: Class to remove
        new_class: Class to add
    
    Returns:
        True if old_class was found and replaced
    
    Example:
        replace_class(btn, "loading", "loaded")
        replace_class(card, "collapsed", "expanded")
    """
    return element.classList.replace(old_class, new_class)


def clear_styles(element: Element) -> None:
    """
    Remove all inline styles from an element.
    
    WHO: Developers resetting styles
    WHAT: Clears all inline styles
    WHEN: Use to reset to stylesheet defaults
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Single call to clear all inline styles
    HOW: Transpiles to style.cssText = ""
    
    Args:
        element: Target DOM element
    
    Example:
        clear_styles(el)  # Element uses stylesheet styles only
    """
    element.style.cssText = ""


def get_style(element: Element, property: str) -> str:
    """
    Get an inline style value.
    
    WHO: Developers reading inline styles
    WHAT: Gets the inline style value for a property
    WHEN: Use when you need the inline (not computed) value
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Simpler than style.getPropertyValue
    HOW: Transpiles to style.getPropertyValue(prop)
    
    Args:
        element: Target DOM element
        property: CSS property name (kebab-case or camelCase)
    
    Returns:
        The inline style value, or empty string if not set
    
    Example:
        display = get_style(el, "display")
        bg = get_style(el, "background-color")
    """
    return element.style.getPropertyValue(property)


__all__ = [
    "classes",
    "set_styles",
    "toggle_class",
    "add_classes",
    "remove_classes",
    "has_class",
    "replace_class",
    "clear_styles",
    "get_style",
]

