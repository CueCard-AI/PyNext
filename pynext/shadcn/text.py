"""
Text Component

A typography component for rendering text with consistent styling.

Usage:
    from pynext.shadcn import Text
    
    Text("Hello world")
    Text("Title", size="xl", weight="bold")
    Text("Muted text", color="muted")
"""

from typing import Any, Optional, List, Union, Literal
from pynext.tw import cn


# Text sizes
TEXT_SIZES = {
    "xs": "text-xs",       # 12px
    "sm": "text-sm",       # 14px
    "base": "text-base",   # 16px
    "lg": "text-lg",       # 18px
    "xl": "text-xl",       # 20px
    "2xl": "text-2xl",     # 24px
    "3xl": "text-3xl",     # 30px
    "4xl": "text-4xl",     # 36px
}

# Font weights
TEXT_WEIGHTS = {
    "normal": "font-normal",
    "medium": "font-medium",
    "semibold": "font-semibold",
    "bold": "font-bold",
}

# Text colors (semantic)
TEXT_COLORS = {
    "default": "text-foreground",
    "muted": "text-muted-foreground",
    "primary": "text-primary",
    "secondary": "text-secondary-foreground",
    "destructive": "text-destructive",
    "success": "text-green-600",
    "warning": "text-yellow-600",
}


TextSize = Literal["xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl"]
TextWeight = Literal["normal", "medium", "semibold", "bold"]
TextColor = Literal["default", "muted", "primary", "secondary", "destructive", "success", "warning"]


class Text:
    """
    A text component for consistent typography.
    
    Attributes:
        size: Font size - "xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl"
        weight: Font weight - "normal", "medium", "semibold", "bold"
        color: Text color - "default", "muted", "primary", "secondary", "destructive", "success", "warning"
        as_element: HTML element to render as - "span", "p", "div", "label"
        truncate: Whether to truncate with ellipsis
        class_: Additional CSS classes
    
    Example:
        # Basic text
        Text("Hello world")
        
        # Styled text
        Text("Important!", size="lg", weight="bold", color="primary")
        
        # Muted helper text
        Text("Optional field", size="sm", color="muted")
        
        # As paragraph
        Text("Long paragraph...", as_element="p")
    """
    
    def __init__(
        self,
        content: Optional[str] = None,
        size: TextSize = "base",
        weight: TextWeight = "normal",
        color: TextColor = "default",
        as_element: Literal["span", "p", "div", "label"] = "span",
        truncate: bool = False,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.content = content
        self.size = size
        self.weight = weight
        self.color = color
        self.as_element = as_element
        self.truncate = truncate
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Text":
        """Add children using bracket syntax: Text()["content"]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """Render the text as HTML."""
        # Use content if provided, otherwise use children
        if self.content is not None:
            children_html = str(self.content)
        else:
            children_html = ""
            for child in self._children:
                if hasattr(child, 'render'):
                    children_html += child.render()
                else:
                    children_html += str(child)
        
        class_str = cn(
            TEXT_SIZES.get(self.size, "text-base"),
            TEXT_WEIGHTS.get(self.weight, ""),
            TEXT_COLORS.get(self.color, ""),
            "truncate" if self.truncate else "",
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
        
        tag = self.as_element
        return f'<{tag} {attrs_str}>{children_html}</{tag}>'
    
    def __str__(self) -> str:
        return self.render()


class Heading:
    """
    A heading component for titles.
    
    Attributes:
        level: Heading level 1-6 (h1, h2, etc.)
        size: Override font size
        class_: Additional CSS classes
    
    Example:
        Heading(level=1)["Page Title"]
        Heading(level=2)["Section Title"]
    """
    
    # Default sizes for each heading level
    LEVEL_SIZES = {
        1: "text-4xl font-bold tracking-tight",
        2: "text-3xl font-semibold tracking-tight",
        3: "text-2xl font-semibold",
        4: "text-xl font-semibold",
        5: "text-lg font-medium",
        6: "text-base font-medium",
    }
    
    def __init__(
        self,
        level: Literal[1, 2, 3, 4, 5, 6] = 2,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.level = level
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Heading":
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
            self.LEVEL_SIZES.get(self.level, self.LEVEL_SIZES[2]),
            "text-foreground",
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
        
        tag = f"h{self.level}"
        return f'<{tag} {attrs_str}>{children_html}</{tag}>'
    
    def __str__(self) -> str:
        return self.render()


