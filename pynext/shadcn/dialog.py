"""
Dialog Components

A modal dialog component for displaying content that requires user attention.

Usage:
    from pynext.shadcn import (
        Dialog, DialogTrigger, DialogContent,
        DialogHeader, DialogTitle, DialogDescription, DialogFooter
    )
    
    Dialog()[
        DialogTrigger()[Button()["Edit Profile"]],
        DialogContent()[
            DialogHeader()[
                DialogTitle()["Edit Profile"],
                DialogDescription()["Make changes to your profile here."]
            ],
            Input(placeholder="Name"),
            DialogFooter()[
                Button()["Save changes"]
            ]
        ]
    ]
"""

from typing import Any, Optional, List, Union, Callable
from pynext.tw import cn


# Dialog styles
DIALOG_OVERLAY_BASE = (
    "fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in "
    "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 "
    "data-[state=open]:fade-in-0"
)

DIALOG_CONTENT_BASE = (
    "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] "
    "translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 "
    "data-[state=open]:animate-in data-[state=closed]:animate-out "
    "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 "
    "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 "
    "data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] "
    "data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] "
    "sm:rounded-lg"
)

DIALOG_CLOSE_BASE = (
    "absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background "
    "transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 "
    "focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none "
    "data-[state=open]:bg-accent data-[state=open]:text-muted-foreground"
)

DIALOG_HEADER_BASE = "flex flex-col space-y-1.5 text-center sm:text-left"
DIALOG_FOOTER_BASE = "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2"
DIALOG_TITLE_BASE = "text-lg font-semibold leading-none tracking-tight"
DIALOG_DESCRIPTION_BASE = "text-sm text-muted-foreground"


class Dialog:
    """
    Root component for a dialog.
    
    Attributes:
        open: Controlled open state
        on_open_change: Callback when open state changes
    
    Example:
        Dialog()[
            DialogTrigger()[Button()["Open"]],
            DialogContent()[...]
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
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Dialog":
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
        
        import hashlib
        dialog_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        attrs_str = f'data-pynext-dialog="{dialog_id}"'
        if self.open is not None:
            attrs_str += f' data-state="{"open" if self.open else "closed"}"'
        
        return f'<div {attrs_str} style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class DialogTrigger:
    """Button that opens the dialog."""
    
    def __init__(self, as_child: bool = True, **attrs: Any):
        self.as_child = as_child
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DialogTrigger":
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
        return f'<div data-pynext-dialog-trigger style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class DialogContent:
    """The content container for the dialog."""
    
    def __init__(
        self,
        class_: Optional[str] = None,
        show_close: bool = True,
        **attrs: Any
    ):
        self.extra_class = class_
        self.show_close = show_close
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DialogContent":
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
        
        overlay_class = cn(DIALOG_OVERLAY_BASE)
        content_class = cn(DIALOG_CONTENT_BASE, self.extra_class)
        close_class = cn(DIALOG_CLOSE_BASE)
        
        # Close button with X icon
        close_button = ""
        if self.show_close:
            close_button = f'''
<button class="{close_class}" data-pynext-dialog-close>
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
        <path d="M18 6 6 18"></path>
        <path d="m6 6 12 12"></path>
    </svg>
    <span class="sr-only">Close</span>
</button>
'''
        
        return f'''
<div data-pynext-dialog-portal>
    <div class="{overlay_class}" data-pynext-dialog-overlay></div>
    <div class="{content_class}" role="dialog" aria-modal="true" data-pynext-dialog-content>
        {children_html}
        {close_button}
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class DialogHeader:
    """Header section of the dialog."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DialogHeader":
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
        class_str = cn(DIALOG_HEADER_BASE, self.extra_class)
        return f'<div class="{class_str}">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class DialogTitle:
    """Title of the dialog."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DialogTitle":
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
        class_str = cn(DIALOG_TITLE_BASE, self.extra_class)
        return f'<h2 class="{class_str}">{children_html}</h2>'
    
    def __str__(self) -> str:
        return self.render()


class DialogDescription:
    """Description text in the dialog."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DialogDescription":
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
        class_str = cn(DIALOG_DESCRIPTION_BASE, self.extra_class)
        return f'<p class="{class_str}">{children_html}</p>'
    
    def __str__(self) -> str:
        return self.render()


class DialogFooter:
    """Footer section with action buttons."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DialogFooter":
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
        class_str = cn(DIALOG_FOOTER_BASE, self.extra_class)
        return f'<div class="{class_str}">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()

