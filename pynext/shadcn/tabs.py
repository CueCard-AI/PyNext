"""
Tabs Components

A tabbed interface for organizing content.

Usage:
    from pynext.shadcn import Tabs, TabsList, TabsTrigger, TabsContent
    
    Tabs(default_value="account")[
        TabsList()[
            TabsTrigger(value="account")["Account"],
            TabsTrigger(value="password")["Password"]
        ],
        TabsContent(value="account")["Account settings here"],
        TabsContent(value="password")["Password settings here"]
    ]
"""

from typing import Any, Optional, List, Union, Callable
from pynext.tw import cn


# Tabs styles
TABS_LIST_BASE = (
    "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 "
    "text-muted-foreground"
)

TABS_TRIGGER_BASE = (
    "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 "
    "text-sm font-medium ring-offset-background transition-all focus-visible:outline-none "
    "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 "
    "disabled:pointer-events-none disabled:opacity-50 "
    "data-[state=active]:bg-background data-[state=active]:text-foreground "
    "data-[state=active]:shadow-sm"
)

TABS_CONTENT_BASE = (
    "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 "
    "focus-visible:ring-ring focus-visible:ring-offset-2"
)


class Tabs:
    """
    Root component for tabs.
    
    Attributes:
        default_value: The initially active tab value
        value: Controlled active tab value
        on_value_change: Callback when active tab changes
    
    Example:
        Tabs(default_value="tab1")[
            TabsList()[
                TabsTrigger(value="tab1")["Tab 1"],
                TabsTrigger(value="tab2")["Tab 2"]
            ],
            TabsContent(value="tab1")["Content 1"],
            TabsContent(value="tab2")["Content 2"]
        ]
    """
    
    def __init__(
        self,
        default_value: Optional[str] = None,
        value: Optional[str] = None,
        on_value_change: Optional[Callable[[str], None]] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.default_value = default_value
        self.value = value
        self.on_value_change = on_value_change
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Tabs":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        
        import hashlib
        tabs_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        active_value = self.value or self.default_value or ""
        
        attrs_str = f'data-pynext-tabs="{tabs_id}"'
        attrs_str += f' data-active-tab="{active_value}"'
        
        if self.extra_class:
            attrs_str += f' class="{self.extra_class}"'
        
        return f'<div {attrs_str}>{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class TabsList:
    """Container for tab triggers."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "TabsList":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        class_str = cn(TABS_LIST_BASE, self.extra_class)
        return f'<div class="{class_str}" role="tablist">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class TabsTrigger:
    """A tab trigger button."""
    
    def __init__(
        self,
        value: str,
        disabled: bool = False,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.value = value
        self.disabled = disabled
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "TabsTrigger":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        
        class_str = cn(TABS_TRIGGER_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' role="tab"'
        attrs_str += f' data-pynext-tabs-trigger'
        attrs_str += f' data-value="{self.value}"'
        
        if self.disabled:
            attrs_str += ' disabled'
        
        return f'<button {attrs_str}>{children_html}</button>'
    
    def __str__(self) -> str:
        return self.render()


class TabsContent:
    """Content panel for a tab."""
    
    def __init__(
        self,
        value: str,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.value = value
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "TabsContent":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        
        class_str = cn(TABS_CONTENT_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' role="tabpanel"'
        attrs_str += f' data-pynext-tabs-content'
        attrs_str += f' data-value="{self.value}"'
        
        return f'<div {attrs_str}>{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()

