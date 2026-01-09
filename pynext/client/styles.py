"""
PyNext Client - Pythonic Style Access

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides a Pythonic dictionary-style interface for accessing element styles.
Instead of the JavaScript-style camelCase property access, you can use 
kebab-case strings and dictionary operations.

=============================================================================
WHY THIS EXISTS
=============================================================================

Python developers expect dictionary-like access patterns:
- `el.styles["background-color"] = "red"` feels more Pythonic
- Supports CSS custom properties naturally: `el.styles["--primary"] = "blue"`
- Enables bulk updates: `el.styles.update({"display": "flex", "gap": "8px"})`
- Supports `in` operator: `if "display" in el.styles`

=============================================================================
HOW IT WORKS
=============================================================================

The StylesProxy class wraps an element's style object and transpiles to
efficient JavaScript using setProperty/getPropertyValue:

    Python:  el.styles["background-color"] = "red"
    JavaScript: el.style.setProperty("background-color", "red")

=============================================================================
WHO USES THIS
=============================================================================

- Python developers who prefer dict-like syntax
- Code working with dynamic style keys
- Bulk style updates

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client import document
    from pynext.client.styles import StylesProxy
    
    el = document.getElementById("box")
    styles = StylesProxy(el)
    
    # Set styles using kebab-case
    styles["background-color"] = "red"
    styles["border-radius"] = "8px"
    
    # CSS custom properties work naturally
    styles["--primary-color"] = "#3b82f6"
    styles["--spacing"] = "16px"
    
    # Bulk update
    styles.update({
        "display": "flex",
        "flex-direction": "column",
        "gap": "8px",
    })
    
    # Check and delete
    if "display" in styles:
        del styles["display"]
    
    # Get computed value
    bg = styles["background-color"]  # Returns current value
    
    # Clear all inline styles
    styles.clear()
"""

from __future__ import annotations
from typing import (
    Dict,
    Iterator,
    Optional,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from pynext.client.dom import Element


class StylesProxy:
    """
    WHO: Python developers preferring dict-like style access
    WHAT: Dictionary-style interface for element.style
    WHEN: Use for dynamic style keys, bulk updates, or kebab-case preference
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: More Pythonic than camelCase property access
    HOW: Wraps style object, transpiles to setProperty/getPropertyValue
    
    Transpilation Examples:
        styles["color"] = "red"           -> el.style.setProperty("color", "red")
        styles["--primary"] = "blue"      -> el.style.setProperty("--primary", "blue")
        del styles["display"]             -> el.style.removeProperty("display")
        "color" in styles                 -> el.style.getPropertyValue("color") !== ""
        styles.update({...})              -> multiple setProperty calls
        styles.clear()                    -> el.style.cssText = ""
    
    Example:
        el = document.getElementById("card")
        styles = StylesProxy(el)
        
        # Set individual properties
        styles["display"] = "flex"
        styles["--card-bg"] = "#ffffff"
        
        # Bulk update
        styles.update({
            "padding": "16px",
            "border-radius": "8px",
            "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
        })
        
        # Check if property is set
        if "background-color" in styles:
            print(styles["background-color"])
        
        # Remove property
        del styles["padding"]
    """
    
    _element: Element
    
    def __init__(self, element: Element) -> None:
        """
        Create a StylesProxy for an element.
        
        Args:
            element: The DOM element to wrap
        """
        object.__setattr__(self, "_element", element)
    
    def __getitem__(self, key: str) -> str:
        """
        Get a style property value.
        
        Supports both kebab-case and CSS custom properties.
        
        Args:
            key: Property name (e.g., "background-color", "--primary")
        
        Returns:
            The property value, or empty string if not set
        
        Example:
            color = styles["color"]
            primary = styles["--primary-color"]
        """
        return self._element.style.getPropertyValue(key)
    
    def __setitem__(self, key: str, value: str) -> None:
        """
        Set a style property.
        
        Args:
            key: Property name (e.g., "background-color", "--primary")
            value: The value to set
        
        Example:
            styles["display"] = "flex"
            styles["--theme-color"] = "#3b82f6"
        """
        self._element.style.setProperty(key, value)
    
    def __delitem__(self, key: str) -> None:
        """
        Remove a style property.
        
        Args:
            key: Property name to remove
        
        Example:
            del styles["background-color"]
            del styles["--custom-var"]
        """
        self._element.style.removeProperty(key)
    
    def __contains__(self, key: str) -> bool:
        """
        Check if a property is set.
        
        Args:
            key: Property name to check
        
        Returns:
            True if the property has a non-empty value
        
        Example:
            if "display" in styles:
                print("Display is set")
        """
        return self._element.style.getPropertyValue(key) != ""
    
    def __len__(self) -> int:
        """
        Get number of style properties set.
        
        Returns:
            Number of inline style properties
        """
        return self._element.style.length
    
    def __iter__(self) -> Iterator[str]:
        """
        Iterate over property names.
        
        Yields:
            Property names (kebab-case)
        
        Example:
            for prop in styles:
                print(f"{prop}: {styles[prop]}")
        """
        for i in range(self._element.style.length):
            yield self._element.style.item(i)
    
    def get(self, key: str, default: str = "") -> str:
        """
        Get a property value with default.
        
        Args:
            key: Property name
            default: Default value if not set
        
        Returns:
            The property value or default
        
        Example:
            color = styles.get("color", "black")
        """
        value = self._element.style.getPropertyValue(key)
        return value if value else default
    
    def update(self, styles: Dict[str, str]) -> None:
        """
        Bulk update multiple styles.
        
        Args:
            styles: Dictionary of property-value pairs
        
        Example:
            styles.update({
                "display": "flex",
                "gap": "8px",
                "padding": "16px",
                "--primary": "#3b82f6",
            })
        """
        for key, value in styles.items():
            self._element.style.setProperty(key, value)
    
    def clear(self) -> None:
        """
        Remove all inline styles.
        
        Example:
            styles.clear()  # Element returns to stylesheet defaults
        """
        self._element.style.cssText = ""
    
    def keys(self) -> Iterator[str]:
        """
        Get all property names.
        
        Yields:
            Property names (kebab-case)
        """
        return iter(self)
    
    def values(self) -> Iterator[str]:
        """
        Get all property values.
        
        Yields:
            Property values
        """
        for key in self:
            yield self._element.style.getPropertyValue(key)
    
    def items(self) -> Iterator[tuple[str, str]]:
        """
        Get all property name-value pairs.
        
        Yields:
            Tuples of (property_name, value)
        
        Example:
            for prop, value in styles.items():
                print(f"{prop}: {value}")
        """
        for key in self:
            yield key, self._element.style.getPropertyValue(key)
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert to a regular dictionary.
        
        Returns:
            Dictionary of all inline styles
        
        Example:
            style_dict = styles.to_dict()
            # {"display": "flex", "gap": "8px", ...}
        """
        return dict(self.items())
    
    def setProperty(
        self,
        property: str,
        value: str,
        priority: str = ""
    ) -> None:
        """
        Set a property with optional priority.
        
        Args:
            property: Property name
            value: Property value
            priority: "important" or "" (default)
        
        Example:
            styles.setProperty("display", "flex")
            styles.setProperty("color", "red", "important")
        """
        self._element.style.setProperty(property, value, priority)
    
    def removeProperty(self, property: str) -> str:
        """
        Remove a property and return its old value.
        
        Args:
            property: Property name
        
        Returns:
            The old value
        """
        return self._element.style.removeProperty(property)


def create_styles(element: Element) -> StylesProxy:
    """
    Create a StylesProxy for an element.
    
    Convenience function for creating a StylesProxy.
    
    Args:
        element: The DOM element
    
    Returns:
        StylesProxy wrapping the element
    
    Example:
        from pynext.client.styles import create_styles
        
        el = document.getElementById("box")
        styles = create_styles(el)
        styles["display"] = "flex"
    """
    return StylesProxy(element)


__all__ = [
    "StylesProxy",
    "create_styles",
]

