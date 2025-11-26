"""
DropdownMenu Components

A menu that appears on button click with a list of actions.

Usage:
    from pynext.shadcn import (
        DropdownMenu, DropdownMenuTrigger, DropdownMenuContent,
        DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel
    )
    
    DropdownMenu()[
        DropdownMenuTrigger()[Button()["Open Menu"]],
        DropdownMenuContent()[
            DropdownMenuLabel()["My Account"],
            DropdownMenuSeparator(),
            DropdownMenuItem()["Profile"],
            DropdownMenuItem()["Settings"],
            DropdownMenuSeparator(),
            DropdownMenuItem()["Log out"]
        ]
    ]
"""

from typing import Any, Optional, List, Union, Callable
from pynext.tw import cn


# DropdownMenu styles
DROPDOWN_CONTENT_BASE = (
    "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 "
    "text-popover-foreground shadow-md data-[state=open]:animate-in "
    "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 "
    "data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 "
    "data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 "
    "data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 "
    "data-[side=top]:slide-in-from-bottom-2"
)

DROPDOWN_ITEM_BASE = (
    "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 "
    "text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground "
    "data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
)

DROPDOWN_LABEL_BASE = "px-2 py-1.5 text-sm font-semibold"
DROPDOWN_SEPARATOR_BASE = "-mx-1 my-1 h-px bg-muted"


class DropdownMenu:
    """
    Root component for a dropdown menu.
    
    Example:
        DropdownMenu()[
            DropdownMenuTrigger()[Button()["Menu"]],
            DropdownMenuContent()[...]
        ]
    """
    
    def __init__(
        self,
        open: Optional[bool] = None,
        on_open_change: Optional[Callable[[bool], None]] = None,
        **attrs: Any
    ):
        self.open = open
        self.on_open_change = on_open_change
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DropdownMenu":
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
        menu_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        attrs_str = f'data-pynext-dropdown-menu="{menu_id}"'
        if self.open is not None:
            attrs_str += f' data-state="{"open" if self.open else "closed"}"'
        
        return f'<div {attrs_str} style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class DropdownMenuTrigger:
    """Button that opens the dropdown menu."""
    
    def __init__(self, as_child: bool = True, **attrs: Any):
        self.as_child = as_child
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DropdownMenuTrigger":
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
        return f'<div data-pynext-dropdown-trigger style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class DropdownMenuContent:
    """The dropdown menu content container."""
    
    def __init__(
        self,
        align: str = "center",
        side: str = "bottom",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.align = align
        self.side = side
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DropdownMenuContent":
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
        
        class_str = cn(DROPDOWN_CONTENT_BASE, self.extra_class)
        
        return f'''
<div data-pynext-dropdown-portal>
    <div class="{class_str}" role="menu" data-side="{self.side}" data-align="{self.align}" data-pynext-dropdown-content>
        {children_html}
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class DropdownMenuItem:
    """A single item in the dropdown menu."""
    
    def __init__(
        self,
        on_select: Optional[Callable] = None,
        disabled: bool = False,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.on_select = on_select
        self.disabled = disabled
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DropdownMenuItem":
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
        
        class_str = cn(DROPDOWN_ITEM_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}" role="menuitem"'
        if self.disabled:
            attrs_str += ' data-disabled'
        
        if self.on_select:
            import hashlib
            handler_id = hashlib.md5(str(id(self.on_select)).encode()).hexdigest()[:8]
            attrs_str += f' data-pynext-click="{handler_id}"'
        
        return f'<div {attrs_str}>{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class DropdownMenuLabel:
    """A label/header in the dropdown menu."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DropdownMenuLabel":
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
        class_str = cn(DROPDOWN_LABEL_BASE, self.extra_class)
        return f'<div class="{class_str}">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class DropdownMenuSeparator:
    """A visual separator between menu items."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn(DROPDOWN_SEPARATOR_BASE, self.extra_class)
        return f'<div class="{class_str}" role="separator"></div>'
    
    def __str__(self) -> str:
        return self.render()

