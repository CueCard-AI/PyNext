"""
Separator Component

A visual divider between content sections.

Usage:
    from pynext.shadcn import Separator
    
    Separator()  # Horizontal line
    Separator(orientation="vertical")  # Vertical line
"""

from typing import Any, Optional, Literal
from pynext.tw import cn


# Separator styles
SEPARATOR_BASE = "shrink-0 bg-border"
SEPARATOR_HORIZONTAL = "h-[1px] w-full"
SEPARATOR_VERTICAL = "h-full w-[1px]"


class Separator:
    """
    A visual separator/divider component.
    
    Attributes:
        orientation: "horizontal" or "vertical"
        decorative: If True, separator is purely visual (hidden from screen readers)
        class_: Additional CSS classes
    
    Example:
        # Horizontal separator
        div()[
            "Section 1",
            Separator(),
            "Section 2"
        ]
        
        # Vertical separator in a flex row
        div(class_="flex items-center gap-4")[
            "Left",
            Separator(orientation="vertical", class_="h-6"),
            "Right"
        ]
    """
    
    def __init__(
        self,
        orientation: Literal["horizontal", "vertical"] = "horizontal",
        decorative: bool = True,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.orientation = orientation
        self.decorative = decorative
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        """Render the separator."""
        orientation_class = (
            SEPARATOR_HORIZONTAL 
            if self.orientation == "horizontal" 
            else SEPARATOR_VERTICAL
        )
        
        class_str = cn(SEPARATOR_BASE, orientation_class, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' data-orientation="{self.orientation}"'
        
        # Accessibility
        if self.decorative:
            attrs_str += ' role="none"'
        else:
            attrs_str += ' role="separator"'
            attrs_str += f' aria-orientation="{self.orientation}"'
        
        for key, value in self.attrs.items():
            if key == "class_":
                continue
            attr_name = key.rstrip("_").replace("_", "-")
            if isinstance(value, bool):
                if value:
                    attrs_str += f' {attr_name}'
            else:
                attrs_str += f' {attr_name}="{value}"'
        
        return f'<div {attrs_str}></div>'
    
    def __str__(self) -> str:
        return self.render()

