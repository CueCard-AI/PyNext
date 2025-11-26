"""
Alert Components

A callout component for displaying important messages.

Usage:
    from pynext.shadcn import Alert, AlertTitle, AlertDescription
    
    Alert()[
        AlertTitle()["Heads up!"],
        AlertDescription()["You can add components to your app using the cli."]
    ]
    
    Alert(variant="destructive")[
        AlertTitle()["Error"],
        AlertDescription()["Your session has expired. Please log in again."]
    ]
"""

from typing import Any, Optional, List, Union, Literal
from pynext.tw import cn


# Alert variant styles
ALERT_VARIANTS = {
    "default": "bg-background text-foreground",
    "destructive": (
        "border-destructive/50 text-destructive dark:border-destructive "
        "[&>svg]:text-destructive"
    ),
}

# Alert base styles
ALERT_BASE = (
    "relative w-full rounded-lg border p-4 "
    "[&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute "
    "[&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground"
)

ALERT_TITLE_BASE = "mb-1 font-medium leading-none tracking-tight"
ALERT_DESCRIPTION_BASE = "text-sm [&_p]:leading-relaxed"


AlertVariant = Literal["default", "destructive"]


class Alert:
    """
    An alert/callout component for displaying messages.
    
    Attributes:
        variant: Visual style - "default" or "destructive"
        class_: Additional CSS classes
    
    Example:
        Alert()[
            AlertTitle()["Success!"],
            AlertDescription()["Your changes have been saved."]
        ]
        
        Alert(variant="destructive")[
            AlertTitle()["Error"],
            AlertDescription()["Something went wrong."]
        ]
    """
    
    def __init__(
        self,
        variant: AlertVariant = "default",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.variant = variant
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Alert":
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
            ALERT_BASE,
            ALERT_VARIANTS.get(self.variant, ALERT_VARIANTS["default"]),
            self.extra_class
        )
        
        attrs_str = f'class="{class_str}"'
        attrs_str += ' role="alert"'
        
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


class AlertTitle:
    """
    The title of an alert.
    
    Example:
        AlertTitle()["Important Notice"]
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertTitle":
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
        
        class_str = cn(ALERT_TITLE_BASE, self.extra_class)
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
        
        return f'<h5 {attrs_str}>{children_html}</h5>'
    
    def __str__(self) -> str:
        return self.render()


class AlertDescription:
    """
    The description/body of an alert.
    
    Example:
        AlertDescription()["Please check your email for further instructions."]
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertDescription":
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
        
        class_str = cn(ALERT_DESCRIPTION_BASE, self.extra_class)
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

