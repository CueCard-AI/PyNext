"""
Card Components

A container component with header, content, and footer sections.

Usage:
    from pynext.shadcn import Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
    
    Card()[
        CardHeader()[
            CardTitle()["Card Title"],
            CardDescription()["Card description goes here"]
        ],
        CardContent()[
            "Main card content"
        ],
        CardFooter()[
            Button()["Action"]
        ]
    ]
"""

from typing import Any, Optional, List, Union
from pynext.tw import cn


# Card component styles
CARD_BASE = "rounded-lg border bg-card text-card-foreground shadow-sm"
CARD_HEADER_BASE = "flex flex-col space-y-1.5 p-6"
CARD_TITLE_BASE = "text-2xl font-semibold leading-none tracking-tight"
CARD_DESCRIPTION_BASE = "text-sm text-muted-foreground"
CARD_CONTENT_BASE = "p-6 pt-0"
CARD_FOOTER_BASE = "flex items-center p-6 pt-0"


class Card:
    """
    A card container component.
    
    Provides a styled container with rounded corners, border, and shadow.
    Use with CardHeader, CardContent, and CardFooter for structured layouts.
    
    Attributes:
        class_: Additional CSS classes
    
    Example:
        Card()[
            CardHeader()[CardTitle()["Dashboard"]],
            CardContent()["Content here"],
            CardFooter()[Button()["Save"]]
        ]
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Card":
        """Add children using bracket syntax."""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """Render the card."""
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        class_str = cn(CARD_BASE, self.extra_class)
        
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


class CardHeader:
    """
    The header section of a card.
    
    Typically contains CardTitle and CardDescription.
    
    Example:
        CardHeader()[
            CardTitle()["Account Settings"],
            CardDescription()["Manage your account preferences"]
        ]
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CardHeader":
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
        
        class_str = cn(CARD_HEADER_BASE, self.extra_class)
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


class CardTitle:
    """
    The title element of a card header.
    
    Renders as an h3 heading by default.
    
    Example:
        CardTitle()["Dashboard Overview"]
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CardTitle":
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
        
        class_str = cn(CARD_TITLE_BASE, self.extra_class)
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
        
        return f'<h3 {attrs_str}>{children_html}</h3>'
    
    def __str__(self) -> str:
        return self.render()


class CardDescription:
    """
    A description/subtitle in a card header.
    
    Renders in a muted color below the title.
    
    Example:
        CardDescription()["Configure your notification settings"]
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CardDescription":
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
        
        class_str = cn(CARD_DESCRIPTION_BASE, self.extra_class)
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
        
        return f'<p {attrs_str}>{children_html}</p>'
    
    def __str__(self) -> str:
        return self.render()


class CardContent:
    """
    The main content area of a card.
    
    Example:
        CardContent()[
            "Your main content goes here",
            Input(placeholder="Enter value")
        ]
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CardContent":
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
        
        class_str = cn(CARD_CONTENT_BASE, self.extra_class)
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


class CardFooter:
    """
    The footer section of a card.
    
    Typically contains action buttons.
    
    Example:
        CardFooter()[
            Button(variant="outline")["Cancel"],
            Button()["Save"]
        ]
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CardFooter":
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
        
        class_str = cn(CARD_FOOTER_BASE, self.extra_class)
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

