"""
Badge Component

A small status indicator with multiple variants.

Usage:
    from pynext.shadcn import Badge
    
    Badge()["Default"]
    Badge(variant="secondary")["Secondary"]
    Badge(variant="destructive")["Error"]
    Badge(variant="outline")["Outline"]
"""

from typing import Any, Optional, List, Union, Literal
from pynext.tw import cn


# Badge variant styles
BADGE_VARIANTS = {
    "default": "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
    "secondary": "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
    "destructive": "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
    "outline": "text-foreground",
}

# Badge base styles
BADGE_BASE = (
    "inline-flex items-center rounded-full border px-2.5 py-0.5 "
    "text-xs font-semibold transition-colors focus:outline-none "
    "focus:ring-2 focus:ring-ring focus:ring-offset-2"
)


BadgeVariant = Literal["default", "secondary", "destructive", "outline"]


class Badge:
    """
    A badge component for displaying status or labels.
    
    Attributes:
        variant: Visual style - "default", "secondary", "destructive", or "outline"
        class_: Additional CSS classes
    
    Example:
        Badge()["New"]
        Badge(variant="secondary")["In Progress"]
        Badge(variant="destructive")["Failed"]
        Badge(variant="outline")["Preview"]
    """
    
    def __init__(
        self,
        variant: BadgeVariant = "default",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.variant = variant
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Badge":
        """Add children using bracket syntax: Badge()["Status"]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """Render the badge as HTML."""
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        class_str = cn(
            BADGE_BASE,
            BADGE_VARIANTS.get(self.variant, BADGE_VARIANTS["default"]),
            self.extra_class
        )
        
        attrs_str = f'class="{class_str}"'
        
        for key, value in self.attrs.items():
            if key == "class_":
                continue
            attr_name = key.rstrip("_").replace("_", "-")
            if isinstance(value, bool):
                if value:
                    attrs_str += f' {attr_name}'
            else:
                attrs_str += f' {attr_name}="{value}"'
        
        return f'<div {attrs_str}>{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()

