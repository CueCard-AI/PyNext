"""
Tooltip Component

A popup that displays information when hovering over or focusing on an element.
Fully accessible with keyboard support.

Usage:
    from pynext.shadcn import Tooltip, TooltipTrigger, TooltipContent
    
    Tooltip()[
        TooltipTrigger()[
            Button(variant="outline")["Hover me"]
        ],
        TooltipContent()["This is the tooltip content"]
    ]
    
    # With custom placement
    Tooltip()[
        TooltipTrigger()[Button()["Bottom"]],
        TooltipContent(side="bottom")["Appears below"]
    ]
    
    # With delay
    Tooltip(delay=500)[
        TooltipTrigger()[...],
        TooltipContent()[...]
    ]
"""

from typing import Any, Optional, List, Union, Literal
from pynext.tw import cn
import hashlib


# Tooltip content styles
TOOLTIP_CONTENT_BASE = (
    "z-50 overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-sm "
    "text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95 "
    "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 "
    "data-[state=closed]:zoom-out-95"
)

# Position-specific animation classes
TOOLTIP_POSITION_CLASSES = {
    "top": "data-[side=top]:slide-in-from-bottom-2",
    "bottom": "data-[side=bottom]:slide-in-from-top-2",
    "left": "data-[side=left]:slide-in-from-right-2",
    "right": "data-[side=right]:slide-in-from-left-2",
}

# Arrow styles
TOOLTIP_ARROW_BASE = "fill-popover"


class TooltipProvider:
    """
    Context provider for tooltips. Wrap your app to configure defaults.
    
    Attributes:
        delay_duration: Default delay before showing tooltips (ms)
        skip_delay_duration: Delay when moving between tooltips (ms)
    
    Example:
        TooltipProvider(delay_duration=400)[
            App()
        ]
    """
    
    def __init__(
        self,
        delay_duration: int = 700,
        skip_delay_duration: int = 300,
        **attrs: Any
    ):
        self.delay_duration = delay_duration
        self.skip_delay_duration = skip_delay_duration
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "TooltipProvider":
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
<div data-pynext-tooltip-provider 
     data-delay-duration="{self.delay_duration}"
     data-skip-delay-duration="{self.skip_delay_duration}"
     style="display:contents">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class Tooltip:
    """
    Root component for a tooltip.
    
    Attributes:
        delay: Delay before showing (ms), defaults to 700
        open: Controlled open state
        default_open: Initial open state for uncontrolled mode
    
    Example:
        Tooltip()[
            TooltipTrigger()[Button()["Hover"]],
            TooltipContent()["Tooltip text"]
        ]
    """
    
    def __init__(
        self,
        delay: int = 700,
        open: Optional[bool] = None,
        default_open: bool = False,
        **attrs: Any
    ):
        self.delay = delay
        self.open = open
        self.default_open = default_open
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Tooltip":
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
        
        tooltip_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        state = "closed"
        if self.open is True or self.default_open:
            state = "open"
        
        return f'''
<div data-pynext-tooltip="{tooltip_id}" 
     data-state="{state}" 
     data-delay="{self.delay}"
     style="display:inline-block;position:relative">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class TooltipTrigger:
    """
    The element that triggers the tooltip on hover/focus.
    
    Attributes:
        as_child: If True, merges props onto child element
    
    Example:
        TooltipTrigger()[
            Button()["Hover me"]
        ]
    """
    
    def __init__(self, as_child: bool = True, **attrs: Any):
        self.as_child = as_child
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "TooltipTrigger":
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
<div data-pynext-tooltip-trigger 
     tabindex="0"
     style="display:inline-block">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class TooltipContent:
    """
    The content displayed in the tooltip popup.
    
    Attributes:
        side: Placement relative to trigger ("top", "bottom", "left", "right")
        side_offset: Distance from trigger in pixels
        align: Alignment along the side ("start", "center", "end")
        align_offset: Offset from alignment
        arrow: Whether to show a pointing arrow
        class_: Additional CSS classes
    
    Example:
        TooltipContent(side="bottom", align="start")[
            "Aligned to start, appears below"
        ]
    """
    
    def __init__(
        self,
        side: Literal["top", "bottom", "left", "right"] = "top",
        side_offset: int = 4,
        align: Literal["start", "center", "end"] = "center",
        align_offset: int = 0,
        arrow: bool = False,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.side = side
        self.side_offset = side_offset
        self.align = align
        self.align_offset = align_offset
        self.arrow = arrow
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "TooltipContent":
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
        position_class = TOOLTIP_POSITION_CLASSES.get(self.side, "")
        class_str = cn(TOOLTIP_CONTENT_BASE, position_class, self.extra_class)
        
        # Position styles based on side
        position_styles = self._get_position_styles()
        
        # Arrow element
        arrow_html = ""
        if self.arrow:
            arrow_html = self._render_arrow()
        
        return f'''
<div data-pynext-tooltip-content
     data-side="{self.side}"
     data-align="{self.align}"
     data-state="closed"
     class="{class_str}"
     role="tooltip"
     style="display:none;position:absolute;{position_styles}">
    {children_html}
    {arrow_html}
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
    
    def _render_arrow(self) -> str:
        """Render the arrow pointing at the trigger."""
        arrow_position = ""
        
        if self.side == "top":
            arrow_position = "bottom:-4px;left:50%;transform:translateX(-50%) rotate(180deg)"
        elif self.side == "bottom":
            arrow_position = "top:-4px;left:50%;transform:translateX(-50%)"
        elif self.side == "left":
            arrow_position = "right:-4px;top:50%;transform:translateY(-50%) rotate(90deg)"
        elif self.side == "right":
            arrow_position = "left:-4px;top:50%;transform:translateY(-50%) rotate(-90deg)"
        
        return f'''
<svg data-pynext-tooltip-arrow
     class="{TOOLTIP_ARROW_BASE}"
     width="10" height="5"
     viewBox="0 0 10 5"
     style="position:absolute;{arrow_position}">
    <polygon points="0,0 5,5 10,0" />
</svg>
'''
    
    def __str__(self) -> str:
        return self.render()

