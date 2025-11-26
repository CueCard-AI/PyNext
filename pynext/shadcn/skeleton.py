"""
Skeleton Component

A loading placeholder that mimics the shape of content while it's loading.
Uses a subtle pulse animation to indicate loading state.

Usage:
    from pynext.shadcn import Skeleton
    
    # Basic skeleton
    Skeleton(class_="h-4 w-[250px]")
    
    # Card skeleton
    div(class_="flex items-center space-x-4")[
        Skeleton(class_="h-12 w-12 rounded-full"),  # Avatar
        div(class_="space-y-2")[
            Skeleton(class_="h-4 w-[250px]"),  # Title
            Skeleton(class_="h-4 w-[200px]"),  # Subtitle
        ]
    ]
    
    # Table skeleton
    div(class_="space-y-2")[
        Skeleton(class_="h-8 w-full"),  # Header row
        Skeleton(class_="h-6 w-full"),  # Data row 1
        Skeleton(class_="h-6 w-full"),  # Data row 2
        Skeleton(class_="h-6 w-full"),  # Data row 3
    ]
"""

from typing import Any, Optional, Literal
from pynext.tw import cn


# Base skeleton styles
SKELETON_BASE = "animate-pulse rounded-md bg-muted"


class Skeleton:
    """
    A loading placeholder component.
    
    Displays a pulsing placeholder that mimics the shape of content.
    Use the class_ parameter to set the size and shape.
    
    Attributes:
        class_: Additional CSS classes for sizing/shaping
        variant: "default" (rectangle), "circle", or "text"
    
    Example:
        # Rectangle (default)
        Skeleton(class_="h-4 w-32")
        
        # Circle (for avatars)
        Skeleton(class_="h-12 w-12", variant="circle")
        
        # Text line
        Skeleton(variant="text", class_="w-3/4")
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        variant: Literal["default", "circle", "text"] = "default",
        **attrs: Any
    ):
        self.extra_class = class_
        self.variant = variant
        self.attrs = attrs
    
    def render(self) -> str:
        variant_classes = {
            "default": "",
            "circle": "rounded-full",
            "text": "h-4",
        }
        
        class_str = cn(
            SKELETON_BASE,
            variant_classes.get(self.variant, ""),
            self.extra_class
        )
        
        # Build attrs string
        attrs_parts = [f'class="{class_str}"']
        for key, value in self.attrs.items():
            attr_name = key.replace("_", "-")
            attrs_parts.append(f'{attr_name}="{value}"')
        
        return f'<div {" ".join(attrs_parts)}></div>'
    
    def __str__(self) -> str:
        return self.render()


class SkeletonCard:
    """
    Pre-built skeleton for a typical card layout.
    
    Includes avatar, title, and description placeholders.
    
    Example:
        SkeletonCard()
    """
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn("flex items-center space-x-4", self.extra_class)
        
        return f'''
<div class="{class_str}">
    <div class="{cn(SKELETON_BASE, "h-12 w-12 rounded-full")}"></div>
    <div class="space-y-2">
        <div class="{cn(SKELETON_BASE, "h-4 w-[250px]")}"></div>
        <div class="{cn(SKELETON_BASE, "h-4 w-[200px]")}"></div>
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class SkeletonTable:
    """
    Pre-built skeleton for table loading state.
    
    Attributes:
        rows: Number of rows to display
        columns: Number of columns (affects width variation)
    
    Example:
        SkeletonTable(rows=5)
    """
    
    def __init__(
        self,
        rows: int = 5,
        columns: int = 4,
        class_: Optional[str] = None,
        show_header: bool = True,
        **attrs: Any
    ):
        self.rows = rows
        self.columns = columns
        self.extra_class = class_
        self.show_header = show_header
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn("space-y-3", self.extra_class)
        
        # Header row
        header = ""
        if self.show_header:
            header = f'<div class="{cn(SKELETON_BASE, "h-10 w-full")}"></div>'
        
        # Data rows with varying widths for visual interest
        widths = ["w-full", "w-11/12", "w-10/12", "w-full", "w-9/12"]
        rows_html = "\n".join([
            f'<div class="{cn(SKELETON_BASE, "h-8", widths[i % len(widths)])}"></div>'
            for i in range(self.rows)
        ])
        
        return f'''
<div class="{class_str}">
    {header}
    {rows_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class SkeletonText:
    """
    Pre-built skeleton for text paragraphs.
    
    Attributes:
        lines: Number of lines to display
    
    Example:
        SkeletonText(lines=3)
    """
    
    def __init__(
        self,
        lines: int = 3,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.lines = lines
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn("space-y-2", self.extra_class)
        
        # Varying widths for natural text appearance
        widths = ["w-full", "w-11/12", "w-10/12", "w-full", "w-8/12"]
        lines_html = "\n".join([
            f'<div class="{cn(SKELETON_BASE, "h-4", widths[i % len(widths)])}"></div>'
            for i in range(self.lines)
        ])
        
        return f'''
<div class="{class_str}">
    {lines_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()

