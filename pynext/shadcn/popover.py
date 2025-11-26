"""
Popover Component

A floating panel with rich content that appears on click.
Supports focus trapping and close on outside click.

Usage:
    from pynext.shadcn import Popover, PopoverTrigger, PopoverContent
    
    Popover()[
        PopoverTrigger()[
            Button(variant="outline")["Open popover"]
        ],
        PopoverContent()[
            div(class_="grid gap-4")[
                div(class_="space-y-2")[
                    h4(class_="font-medium leading-none")["Dimensions"],
                    p(class_="text-sm text-muted-foreground")[
                        "Set the dimensions for the layer."
                    ],
                ],
                div(class_="grid gap-2")[
                    Input(id="width", placeholder="Width"),
                    Input(id="height", placeholder="Height"),
                ],
            ]
        ]
    ]
"""

from typing import Any, Optional, List, Union, Literal, Callable
from pynext.tw import cn
import hashlib


# Popover content styles
POPOVER_CONTENT_BASE = (
    "z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md "
    "outline-none data-[state=open]:animate-in data-[state=closed]:animate-out "
    "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 "
    "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
)

# Position-specific animation classes
POPOVER_POSITION_CLASSES = {
    "top": "data-[side=top]:slide-in-from-bottom-2",
    "bottom": "data-[side=bottom]:slide-in-from-top-2",
    "left": "data-[side=left]:slide-in-from-right-2",
    "right": "data-[side=right]:slide-in-from-left-2",
}


class Popover:
    """
    Root component for a popover.
    
    Attributes:
        open: Controlled open state
        default_open: Initial open state for uncontrolled mode
        on_open_change: Callback when open state changes
        modal: If True, blocks interaction with outside elements
    
    Example:
        Popover()[
            PopoverTrigger()[Button()["Click"]],
            PopoverContent()[...]
        ]
    """
    
    def __init__(
        self,
        open: Optional[bool] = None,
        default_open: bool = False,
        on_open_change: Optional[Callable[[bool], None]] = None,
        modal: bool = False,
        **attrs: Any
    ):
        self.open = open
        self.default_open = default_open
        self.on_open_change = on_open_change
        self.modal = modal
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Popover":
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
        
        popover_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        state = "closed"
        if self.open is True or self.default_open:
            state = "open"
        
        modal_attr = 'data-modal="true"' if self.modal else ""
        
        return f'''
<div data-pynext-popover="{popover_id}" 
     data-state="{state}" 
     {modal_attr}
     style="display:inline-block;position:relative">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class PopoverTrigger:
    """
    The button/element that toggles the popover.
    
    Attributes:
        as_child: If True, merges props onto child element
    
    Example:
        PopoverTrigger()[
            Button()["Click me"]
        ]
    """
    
    def __init__(self, as_child: bool = True, **attrs: Any):
        self.as_child = as_child
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "PopoverTrigger":
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
        
        return f'''
<div data-pynext-popover-trigger 
     aria-haspopup="dialog"
     style="display:inline-block">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class PopoverAnchor:
    """
    An optional anchor element for positioning the popover.
    
    Use when you want the popover positioned relative to something
    other than the trigger.
    
    Example:
        Popover()[
            PopoverAnchor()[div()["Position me here"]],
            PopoverTrigger()[Button()["Open"]],
            PopoverContent()[...]
        ]
    """
    
    def __init__(self, **attrs: Any):
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "PopoverAnchor":
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
        
        return f'''
<div data-pynext-popover-anchor style="display:contents">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class PopoverContent:
    """
    The content container for the popover.
    
    Attributes:
        side: Placement relative to trigger ("top", "bottom", "left", "right")
        side_offset: Distance from trigger in pixels
        align: Alignment along the side ("start", "center", "end")
        align_offset: Offset from alignment
        class_: Additional CSS classes
        trap_focus: Whether to trap focus inside (default True)
        close_on_escape: Close when Escape is pressed (default True)
        close_on_outside_click: Close when clicking outside (default True)
    
    Example:
        PopoverContent(side="bottom", align="start")[
            div(class_="p-4")["Content goes here"]
        ]
    """
    
    def __init__(
        self,
        side: Literal["top", "bottom", "left", "right"] = "bottom",
        side_offset: int = 4,
        align: Literal["start", "center", "end"] = "center",
        align_offset: int = 0,
        class_: Optional[str] = None,
        trap_focus: bool = True,
        close_on_escape: bool = True,
        close_on_outside_click: bool = True,
        **attrs: Any
    ):
        self.side = side
        self.side_offset = side_offset
        self.align = align
        self.align_offset = align_offset
        self.extra_class = class_
        self.trap_focus = trap_focus
        self.close_on_escape = close_on_escape
        self.close_on_outside_click = close_on_outside_click
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "PopoverContent":
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
        
        # Build class list
        position_class = POPOVER_POSITION_CLASSES.get(self.side, "")
        class_str = cn(POPOVER_CONTENT_BASE, position_class, self.extra_class)
        
        # Position styles
        position_styles = self._get_position_styles()
        
        # Data attributes for behavior
        data_attrs = [
            f'data-side="{self.side}"',
            f'data-align="{self.align}"',
            'data-state="closed"',
        ]
        if self.trap_focus:
            data_attrs.append('data-pynext-focus-trap="true"')
        if self.close_on_escape:
            data_attrs.append('data-close-on-escape="true"')
        if self.close_on_outside_click:
            data_attrs.append('data-close-on-outside-click="true"')
        
        return f'''
<div data-pynext-popover-content
     {' '.join(data_attrs)}
     class="{class_str}"
     role="dialog"
     tabindex="-1"
     style="display:none;position:absolute;{position_styles}">
    {children_html}
</div>
'''
    
    def _get_position_styles(self) -> str:
        """Generate CSS position styles based on side and alignment."""
        styles = []
        offset = self.side_offset
        
        if self.side == "top":
            styles.append(f"bottom:100%")
            styles.append(f"margin-bottom:{offset}px")
        elif self.side == "bottom":
            styles.append(f"top:100%")
            styles.append(f"margin-top:{offset}px")
        elif self.side == "left":
            styles.append(f"right:100%")
            styles.append(f"margin-right:{offset}px")
        elif self.side == "right":
            styles.append(f"left:100%")
            styles.append(f"margin-left:{offset}px")
        
        # Alignment
        if self.side in ("top", "bottom"):
            if self.align == "start":
                styles.append(f"left:{self.align_offset}px")
            elif self.align == "end":
                styles.append(f"right:{self.align_offset}px")
            else:  # center
                styles.append("left:50%")
                styles.append("transform:translateX(-50%)")
        else:  # left or right
            if self.align == "start":
                styles.append(f"top:{self.align_offset}px")
            elif self.align == "end":
                styles.append(f"bottom:{self.align_offset}px")
            else:  # center
                styles.append("top:50%")
                styles.append("transform:translateY(-50%)")
        
        return ";".join(styles)
    
    def __str__(self) -> str:
        return self.render()


class PopoverClose:
    """
    A button that closes the popover.
    
    Example:
        PopoverContent()[
            PopoverClose()[
                Button(variant="ghost", size="sm")["×"]
            ]
        ]
    """
    
    def __init__(self, as_child: bool = True, **attrs: Any):
        self.as_child = as_child
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "PopoverClose":
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
        
        return f'''
<div data-pynext-popover-close style="display:contents">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()

