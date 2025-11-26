"""
Sheet Component (Drawer)

A slide-out panel that appears from the edge of the screen.
Perfect for navigation, forms, or detailed views.

Usage:
    from pynext.shadcn import (
        Sheet, SheetTrigger, SheetContent, SheetHeader, 
        SheetTitle, SheetDescription, SheetFooter, SheetClose
    )
    
    Sheet()[
        SheetTrigger()[
            Button()["Open Settings"]
        ],
        SheetContent(side="right")[
            SheetHeader()[
                SheetTitle()["Settings"],
                SheetDescription()["Configure your preferences"]
            ],
            div(class_="py-4")[
                # Form content
            ],
            SheetFooter()[
                Button()["Save changes"]
            ]
        ]
    ]
    
    # From left side
    Sheet()[
        SheetTrigger()[Button()["Menu"]],
        SheetContent(side="left")[
            # Navigation menu
        ]
    ]
"""

from typing import Any, Optional, List, Union, Literal, Callable
from pynext.tw import cn
import hashlib


# Sheet overlay styles
SHEET_OVERLAY_BASE = (
    "fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in "
    "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 "
    "data-[state=open]:fade-in-0"
)

# Sheet content base styles
SHEET_CONTENT_BASE = (
    "fixed z-50 gap-4 bg-background p-6 shadow-lg transition ease-in-out "
    "data-[state=open]:animate-in data-[state=closed]:animate-out "
    "data-[state=closed]:duration-300 data-[state=open]:duration-500"
)

# Position-specific styles
SHEET_SIDE_CLASSES = {
    "top": (
        "inset-x-0 top-0 border-b "
        "data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top"
    ),
    "bottom": (
        "inset-x-0 bottom-0 border-t "
        "data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom"
    ),
    "left": (
        "inset-y-0 left-0 h-full w-3/4 border-r sm:max-w-sm "
        "data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left"
    ),
    "right": (
        "inset-y-0 right-0 h-full w-3/4 border-l sm:max-w-sm "
        "data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right"
    ),
}

# Close button styles
SHEET_CLOSE_BASE = (
    "absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background "
    "transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 "
    "focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none "
    "data-[state=open]:bg-secondary"
)

SHEET_HEADER_BASE = "flex flex-col space-y-2 text-center sm:text-left"
SHEET_FOOTER_BASE = "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2"
SHEET_TITLE_BASE = "text-lg font-semibold text-foreground"
SHEET_DESCRIPTION_BASE = "text-sm text-muted-foreground"


class Sheet:
    """
    Root component for a sheet/drawer.
    
    Attributes:
        open: Controlled open state
        on_open_change: Callback when open state changes
    
    Example:
        Sheet()[
            SheetTrigger()[Button()["Open"]],
            SheetContent()[...]
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
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Sheet":
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
        
        sheet_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        attrs_str = f'data-pynext-sheet="{sheet_id}"'
        if self.open is not None:
            attrs_str += f' data-state="{"open" if self.open else "closed"}"'
        else:
            attrs_str += ' data-state="closed"'
        
        return f'<div {attrs_str} style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class SheetTrigger:
    """Button that opens the sheet."""
    
    def __init__(self, as_child: bool = True, **attrs: Any):
        self.as_child = as_child
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "SheetTrigger":
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
        return f'<div data-pynext-sheet-trigger style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class SheetContent:
    """
    The sliding panel content.
    
    Attributes:
        side: Which edge to slide from ("top", "bottom", "left", "right")
        class_: Additional CSS classes
        show_close: Whether to show the close button
    
    Example:
        SheetContent(side="left", class_="w-80")[
            # Navigation items
        ]
    """
    
    def __init__(
        self,
        side: Literal["top", "bottom", "left", "right"] = "right",
        class_: Optional[str] = None,
        show_close: bool = True,
        **attrs: Any
    ):
        self.side = side
        self.extra_class = class_
        self.show_close = show_close
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "SheetContent":
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
        
        overlay_class = cn(SHEET_OVERLAY_BASE)
        side_class = SHEET_SIDE_CLASSES.get(self.side, SHEET_SIDE_CLASSES["right"])
        content_class = cn(SHEET_CONTENT_BASE, side_class, self.extra_class)
        close_class = cn(SHEET_CLOSE_BASE)
        
        close_button = ""
        if self.show_close:
            close_button = f'''
<button class="{close_class}" data-pynext-sheet-close>
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
        <path d="M18 6 6 18"></path>
        <path d="m6 6 12 12"></path>
    </svg>
    <span class="sr-only">Close</span>
</button>
'''
        
        return f'''
<div data-pynext-sheet-portal>
    <div class="{overlay_class}" data-pynext-sheet-overlay style="display:none"></div>
    <div class="{content_class}" 
         role="dialog" 
         aria-modal="true" 
         data-pynext-sheet-content
         data-side="{self.side}"
         style="display:none">
        {children_html}
        {close_button}
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class SheetHeader:
    """Header section of the sheet."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "SheetHeader":
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
        class_str = cn(SHEET_HEADER_BASE, self.extra_class)
        return f'<div class="{class_str}">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class SheetTitle:
    """Title of the sheet."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "SheetTitle":
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
        class_str = cn(SHEET_TITLE_BASE, self.extra_class)
        return f'<h2 class="{class_str}">{children_html}</h2>'
    
    def __str__(self) -> str:
        return self.render()


class SheetDescription:
    """Description text in the sheet."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "SheetDescription":
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
        class_str = cn(SHEET_DESCRIPTION_BASE, self.extra_class)
        return f'<p class="{class_str}">{children_html}</p>'
    
    def __str__(self) -> str:
        return self.render()


class SheetFooter:
    """Footer section with action buttons."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "SheetFooter":
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
        class_str = cn(SHEET_FOOTER_BASE, self.extra_class)
        return f'<div class="{class_str}">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class SheetClose:
    """A button that closes the sheet."""
    
    def __init__(self, as_child: bool = True, **attrs: Any):
        self.as_child = as_child
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "SheetClose":
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
        return f'<div data-pynext-sheet-close style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()

