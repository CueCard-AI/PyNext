"""
Layout Primitives

Simple, Pythonic layout components that abstract away flexbox.

Usage:
    from pynext.shadcn import Row, Column, Stack, Center
    
    Row(gap="md", align="center")[
        "Left content",
        "Right content"
    ]
    
    Column(gap="lg")[
        "Top",
        "Middle", 
        "Bottom"
    ]
"""

from typing import Any, Optional, List, Union, Literal
from pynext.tw import cn


# Gap sizes (Tailwind spacing scale)
GAP_SIZES = {
    "none": "gap-0",
    "xs": "gap-1",      # 4px
    "sm": "gap-2",      # 8px
    "md": "gap-4",      # 16px
    "lg": "gap-6",      # 24px
    "xl": "gap-8",      # 32px
    "2xl": "gap-12",    # 48px
}

# Alignment options
ALIGN_OPTIONS = {
    "start": "items-start",
    "center": "items-center",
    "end": "items-end",
    "stretch": "items-stretch",
    "baseline": "items-baseline",
}

JUSTIFY_OPTIONS = {
    "start": "justify-start",
    "center": "justify-center",
    "end": "justify-end",
    "between": "justify-between",
    "around": "justify-around",
    "evenly": "justify-evenly",
}

# Padding sizes
PADDING_SIZES = {
    "none": "",
    "xs": "p-1",
    "sm": "p-2",
    "md": "p-4",
    "lg": "p-6",
    "xl": "p-8",
}


GapSize = Literal["none", "xs", "sm", "md", "lg", "xl", "2xl"]
AlignOption = Literal["start", "center", "end", "stretch", "baseline"]
JustifyOption = Literal["start", "center", "end", "between", "around", "evenly"]
PaddingSize = Literal["none", "xs", "sm", "md", "lg", "xl"]


class Row:
    """
    A horizontal flex container.
    
    Think of it as placing items side-by-side, left to right.
    
    Attributes:
        gap: Space between items - "none", "xs", "sm", "md", "lg", "xl", "2xl"
        align: Vertical alignment - "start", "center", "end", "stretch", "baseline"
        justify: Horizontal distribution - "start", "center", "end", "between", "around", "evenly"
        wrap: Whether items wrap to next line
        class_: Additional CSS classes
    
    Example:
        # Basic row
        Row()[item1, item2, item3]
        
        # Centered with gap
        Row(gap="md", align="center")[icon, text]
        
        # Space between (like justify-content: space-between)
        Row(justify="between")[left_content, right_content]
    """
    
    def __init__(
        self,
        gap: GapSize = "none",
        align: AlignOption = "stretch",
        justify: JustifyOption = "start",
        wrap: bool = False,
        padding: PaddingSize = "none",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.gap = gap
        self.align = align
        self.justify = justify
        self.wrap = wrap
        self.padding = padding
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Row":
        """Add children using bracket syntax: Row()[item1, item2]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """Render the row as HTML."""
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        class_str = cn(
            "flex flex-row",
            GAP_SIZES.get(self.gap, ""),
            ALIGN_OPTIONS.get(self.align, ""),
            JUSTIFY_OPTIONS.get(self.justify, ""),
            "flex-wrap" if self.wrap else "",
            PADDING_SIZES.get(self.padding, ""),
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


class Column:
    """
    A vertical flex container.
    
    Think of it as stacking items top to bottom.
    
    Attributes:
        gap: Space between items - "none", "xs", "sm", "md", "lg", "xl", "2xl"
        align: Horizontal alignment - "start", "center", "end", "stretch"
        justify: Vertical distribution - "start", "center", "end", "between", "around", "evenly"
        class_: Additional CSS classes
    
    Example:
        # Basic column
        Column()[header, content, footer]
        
        # Centered with gap
        Column(gap="lg", align="center")[title, subtitle]
    """
    
    def __init__(
        self,
        gap: GapSize = "none",
        align: AlignOption = "stretch",
        justify: JustifyOption = "start",
        padding: PaddingSize = "none",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.gap = gap
        self.align = align
        self.justify = justify
        self.padding = padding
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Column":
        """Add children using bracket syntax: Column()[item1, item2]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """Render the column as HTML."""
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        class_str = cn(
            "flex flex-col",
            GAP_SIZES.get(self.gap, ""),
            ALIGN_OPTIONS.get(self.align, ""),
            JUSTIFY_OPTIONS.get(self.justify, ""),
            PADDING_SIZES.get(self.padding, ""),
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


# Alias for Column - some developers prefer "Stack"
Stack = Column


class Center:
    """
    A container that centers its content both horizontally and vertically.
    
    Example:
        Center()[
            "This is centered!"
        ]
    """
    
    def __init__(
        self,
        padding: PaddingSize = "none",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.padding = padding
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Center":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        class_str = cn(
            "flex items-center justify-center",
            PADDING_SIZES.get(self.padding, ""),
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


class Spacer:
    """
    A flexible spacer that pushes items apart.
    
    Use inside Row or Column to create space between items.
    
    Example:
        Row()[
            logo,
            Spacer(),  # Pushes nav to the right
            nav_links
        ]
    """
    
    def __init__(self, class_: Optional[str] = None):
        self.extra_class = class_
    
    def render(self) -> str:
        class_str = cn("flex-1", self.extra_class)
        return f'<div class="{class_str}"></div>'
    
    def __str__(self) -> str:
        return self.render()


