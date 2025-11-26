"""
AlertDialog Components

A modal dialog for important confirmations that requires user action.

Usage:
    from pynext.shadcn import (
        AlertDialog, AlertDialogTrigger, AlertDialogContent,
        AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
        AlertDialogFooter, AlertDialogCancel, AlertDialogAction
    )
    
    AlertDialog()[
        AlertDialogTrigger()[Button()["Delete Account"]],
        AlertDialogContent()[
            AlertDialogHeader()[
                AlertDialogTitle()["Are you absolutely sure?"],
                AlertDialogDescription()[
                    "This action cannot be undone."
                ]
            ],
            AlertDialogFooter()[
                AlertDialogCancel()["Cancel"],
                AlertDialogAction()["Continue"]
            ]
        ]
    ]
"""

from typing import Any, Optional, List, Union, Callable
from pynext.tw import cn


# AlertDialog styles
ALERT_DIALOG_OVERLAY_BASE = (
    "fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in "
    "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 "
    "data-[state=open]:fade-in-0"
)

ALERT_DIALOG_CONTENT_BASE = (
    "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] "
    "translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 "
    "data-[state=open]:animate-in data-[state=closed]:animate-out "
    "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 "
    "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 "
    "data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] "
    "data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] "
    "sm:rounded-lg"
)

ALERT_DIALOG_HEADER_BASE = "flex flex-col space-y-2 text-center sm:text-left"
ALERT_DIALOG_FOOTER_BASE = "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2"
ALERT_DIALOG_TITLE_BASE = "text-lg font-semibold"
ALERT_DIALOG_DESCRIPTION_BASE = "text-sm text-muted-foreground"

ALERT_DIALOG_ACTION_BASE = (
    "inline-flex h-10 items-center justify-center rounded-md bg-primary "
    "px-4 py-2 text-sm font-semibold text-primary-foreground ring-offset-background "
    "transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 "
    "focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
)

ALERT_DIALOG_CANCEL_BASE = (
    "inline-flex h-10 items-center justify-center rounded-md border border-input "
    "bg-background px-4 py-2 text-sm font-semibold ring-offset-background "
    "transition-colors hover:bg-accent hover:text-accent-foreground focus:outline-none "
    "focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none "
    "disabled:opacity-50 mt-2 sm:mt-0"
)


class AlertDialog:
    """
    Root component for an alert dialog.
    
    Attributes:
        open: Controlled open state
        on_open_change: Callback when open state changes
    
    Example:
        AlertDialog(open=is_open, on_open_change=set_is_open)[
            AlertDialogTrigger()[...],
            AlertDialogContent()[...]
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
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertDialog":
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
        
        # Generate unique ID for this dialog
        import hashlib
        dialog_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        attrs_str = f'data-pynext-alert-dialog="{dialog_id}"'
        
        if self.open is not None:
            attrs_str += f' data-state="{"open" if self.open else "closed"}"'
        
        return f'<div {attrs_str} style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class AlertDialogTrigger:
    """
    The button that triggers the alert dialog.
    
    Example:
        AlertDialogTrigger()[Button()["Open Dialog"]]
    """
    
    def __init__(
        self,
        as_child: bool = True,
        **attrs: Any
    ):
        self.as_child = as_child
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertDialogTrigger":
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
        
        return f'<div data-pynext-alert-dialog-trigger style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class AlertDialogContent:
    """
    The content container for the alert dialog.
    
    Example:
        AlertDialogContent()[
            AlertDialogHeader()[...],
            AlertDialogFooter()[...]
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
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertDialogContent":
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
        
        overlay_class = cn(ALERT_DIALOG_OVERLAY_BASE)
        content_class = cn(ALERT_DIALOG_CONTENT_BASE, self.extra_class)
        
        # The content is wrapped in a portal and overlay
        return f'''
<div data-pynext-alert-dialog-portal>
    <div class="{overlay_class}" data-pynext-alert-dialog-overlay></div>
    <div class="{content_class}" role="alertdialog" aria-modal="true" data-pynext-alert-dialog-content>
        {children_html}
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class AlertDialogHeader:
    """Header section of the alert dialog."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertDialogHeader":
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
        class_str = cn(ALERT_DIALOG_HEADER_BASE, self.extra_class)
        return f'<div class="{class_str}">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class AlertDialogTitle:
    """Title of the alert dialog."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertDialogTitle":
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
        class_str = cn(ALERT_DIALOG_TITLE_BASE, self.extra_class)
        return f'<h2 class="{class_str}">{children_html}</h2>'
    
    def __str__(self) -> str:
        return self.render()


class AlertDialogDescription:
    """Description text in the alert dialog."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertDialogDescription":
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
        class_str = cn(ALERT_DIALOG_DESCRIPTION_BASE, self.extra_class)
        return f'<p class="{class_str}">{children_html}</p>'
    
    def __str__(self) -> str:
        return self.render()


class AlertDialogFooter:
    """Footer section with action buttons."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertDialogFooter":
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
        class_str = cn(ALERT_DIALOG_FOOTER_BASE, self.extra_class)
        return f'<div class="{class_str}">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class AlertDialogAction:
    """Primary action button (confirms the action)."""
    
    def __init__(
        self,
        on_click: Optional[Callable] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.on_click = on_click
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertDialogAction":
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
        class_str = cn(ALERT_DIALOG_ACTION_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += ' data-pynext-alert-dialog-action'
        
        if self.on_click:
            import hashlib
            handler_id = hashlib.md5(str(id(self.on_click)).encode()).hexdigest()[:8]
            attrs_str += f' data-pynext-click="{handler_id}"'
        
        return f'<button {attrs_str}>{children_html}</button>'
    
    def __str__(self) -> str:
        return self.render()


class AlertDialogCancel:
    """Cancel button (closes the dialog without action)."""
    
    def __init__(
        self,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AlertDialogCancel":
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
        class_str = cn(ALERT_DIALOG_CANCEL_BASE, self.extra_class)
        return f'<button class="{class_str}" data-pynext-alert-dialog-cancel>{children_html}</button>'
    
    def __str__(self) -> str:
        return self.render()

