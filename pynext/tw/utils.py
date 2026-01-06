"""
Tailwind CSS Utility Functions

Provides utilities for conditional class merging, similar to clsx/classnames
libraries in JavaScript.

Usage:
    from pynext.tw import cn
    
    # Conditional classes
    cn("base-class", condition and "conditional-class")
    
    # Multiple conditions
    cn(
        "px-4 py-2 rounded",
        is_primary and "bg-blue-500 text-white",
        is_disabled and "opacity-50 cursor-not-allowed",
        size == "lg" and "text-lg",
    )
    
    # With TailwindBuilder
    cn(tw.flex.items_center, "custom-class", show_border and "border")
"""

from typing import Union, Optional, Any, List
from .builder import TailwindBuilder


def clsx(*args: Any) -> str:
    """
    Construct class strings conditionally.
    
    Accepts:
    - Strings: added directly
    - TailwindBuilder: converted to string
    - Falsy values (None, False, "", 0): ignored
    - Lists/tuples: flattened and processed
    - Dicts: keys added if values are truthy
    
    Examples:
        clsx("foo", "bar")                    # "foo bar"
        clsx("foo", False and "bar")          # "foo"
        clsx("foo", {"bar": True, "baz": 0})  # "foo bar"
        clsx(["foo", "bar"])                  # "foo bar"
    """
    classes: List[str] = []
    
    for arg in args:
        if not arg:
            # Skip falsy values (None, False, "", 0, [])
            continue
        
        if isinstance(arg, str):
            # Add string classes
            classes.extend(arg.split())
        
        elif isinstance(arg, TailwindBuilder):
            # Convert TailwindBuilder to string
            classes.extend(str(arg).split())
        
        elif isinstance(arg, dict):
            # Add keys where values are truthy
            for key, value in arg.items():
                if value:
                    classes.extend(key.split())
        
        elif isinstance(arg, (list, tuple)):
            # Recursively process lists/tuples
            result = clsx(*arg)
            if result:
                classes.extend(result.split())
    
    return " ".join(classes)


def cn(*args: Any) -> str:
    """
    Merge Tailwind CSS classes with conflict resolution.
    
    Like clsx, but also handles Tailwind class conflicts by keeping
    the last occurrence of conflicting classes.
    
    Examples:
        cn("p-4", "p-2")                      # "p-2" (last wins)
        cn("text-red-500", "text-blue-500")   # "text-blue-500"
        cn("px-4 py-2", is_large and "px-6")  # "py-2 px-6"
    
    This is the PyNext equivalent of shadcn/ui's `cn` function.
    """
    # First, get all classes using clsx
    all_classes = clsx(*args)
    
    if not all_classes:
        return ""
    
    # Split into individual classes
    class_list = all_classes.split()
    
    # Track class prefixes to detect conflicts
    # e.g., "p-4" and "p-2" both have prefix "p"
    # e.g., "text-red-500" and "text-blue-500" both have prefix "text"
    prefix_map: dict[str, str] = {}
    result: List[str] = []
    
    # Process in reverse so later classes override earlier ones
    for cls in reversed(class_list):
        prefix = _get_class_prefix(cls)
        
        if prefix in prefix_map:
            # Conflict: skip this class (earlier occurrence)
            continue
        
        prefix_map[prefix] = cls
        result.append(cls)
    
    # Reverse back to original order
    result.reverse()
    
    return " ".join(result)


def _get_class_prefix(cls: str) -> str:
    """
    Extract the prefix from a Tailwind class to detect conflicts.
    
    Examples:
        "p-4" → "p"
        "px-4" → "px"
        "text-red-500" → "text"
        "hover:bg-blue-500" → "hover:bg"
        "md:flex" → "md:flex" (no value, use whole class)
        "flex" → "flex" (no value, use whole class)
    """
    # Handle modifiers (hover:, md:, etc.)
    if ":" in cls:
        parts = cls.split(":")
        modifier_prefix = ":".join(parts[:-1])
        base_class = parts[-1]
        base_prefix = _get_base_prefix(base_class)
        return f"{modifier_prefix}:{base_prefix}"
    
    return _get_base_prefix(cls)


def _get_base_prefix(cls: str) -> str:
    """
    Get the prefix from a base Tailwind class (no modifiers).
    
    Examples:
        "p-4" → "p"
        "bg-red-500" → "bg"
        "flex" → "flex"
        "items-center" → "items"
    """
    # Classes without values - these should use the full class as prefix
    # to avoid conflicts with similar-named classes
    no_value_classes = {
        "flex", "block", "inline", "hidden", "grid",
        "absolute", "relative", "fixed", "sticky", "static",
        "overflow-hidden", "overflow-auto", "overflow-scroll",
        "underline", "no-underline", "uppercase", "lowercase", "capitalize",
        "truncate", "break-words", "break-all",
        "cursor-pointer", "cursor-default", "cursor-not-allowed",
        "select-none", "select-text", "select-all",
        "sr-only", "not-sr-only",
        # Flex direction classes - should NOT conflict with "flex"
        "flex-row", "flex-col", "flex-row-reverse", "flex-col-reverse",
        "flex-wrap", "flex-nowrap", "flex-wrap-reverse",
        "flex-1", "flex-auto", "flex-initial", "flex-none",
        # Inline-flex should not conflict with inline or flex
        "inline-flex", "inline-block", "inline-grid",
    }
    
    if cls in no_value_classes:
        return cls
    
    # Find the last dash that separates prefix from value
    # e.g., "text-red-500" → prefix is "text", value is "red-500"
    # e.g., "p-4" → prefix is "p", value is "4"
    
    # Common prefixes that can have complex values
    complex_prefixes = [
        "bg", "text", "border", "ring", "shadow", "rounded",
        "font", "leading", "tracking", "decoration",
        "fill", "stroke",
        "from", "via", "to",  # gradients
        "divide", "space",
        "translate", "rotate", "scale", "skew",
        "origin", "accent", "caret", "outline",
    ]
    
    for prefix in complex_prefixes:
        if cls.startswith(f"{prefix}-"):
            return prefix
    
    # For other classes, split on first dash
    if "-" in cls:
        return cls.split("-")[0]
    
    # No dash, use whole class
    return cls


def merge_classes(*args: Any) -> str:
    """
    Alias for cn() for those who prefer a more descriptive name.
    """
    return cn(*args)

