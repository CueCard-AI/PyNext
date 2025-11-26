"""
Toggle Components

A two-state button that can be on or off.

Usage:
    from pynext.shadcn import Toggle, ToggleGroup
    
    Toggle(pressed=bold, on_pressed_change=set_bold)[BoldIcon()]
    
    ToggleGroup(type="single")[
        Toggle(value="left")[AlignLeftIcon()],
        Toggle(value="center")[AlignCenterIcon()],
        Toggle(value="right")[AlignRightIcon()]
    ]
"""

from typing import Any, Optional, List, Union, Callable, Literal
from pynext.tw import cn


# Toggle styles
TOGGLE_VARIANTS = {
    "default": "bg-transparent",
    "outline": "border border-input bg-transparent hover:bg-accent hover:text-accent-foreground",
}

TOGGLE_SIZES = {
    "default": "h-10 px-3",
    "sm": "h-9 px-2.5",
    "lg": "h-11 px-5",
}

TOGGLE_BASE = (
    "inline-flex items-center justify-center rounded-md text-sm font-medium "
    "ring-offset-background transition-colors hover:bg-muted hover:text-muted-foreground "
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring "
    "focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 "
    "data-[state=on]:bg-accent data-[state=on]:text-accent-foreground"
)


ToggleVariant = Literal["default", "outline"]
ToggleSize = Literal["default", "sm", "lg"]


class Toggle:
    """
    A toggle button with pressed/unpressed states.
    
    Attributes:
        pressed: Whether the toggle is pressed
        default_pressed: Initial pressed state
        on_pressed_change: Callback when pressed state changes
        variant: Visual style
        size: Toggle size
        disabled: Whether the toggle is disabled
    
    Example:
        Toggle(pressed=is_bold, on_pressed_change=set_is_bold)[
            BoldIcon()
        ]
    """
    
    def __init__(
        self,
        pressed: Optional[bool] = None,
        default_pressed: bool = False,
        on_pressed_change: Optional[Callable[[bool], None]] = None,
        variant: ToggleVariant = "default",
        size: ToggleSize = "default",
        disabled: bool = False,
        value: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.pressed = pressed
        self.default_pressed = default_pressed
        self.on_pressed_change = on_pressed_change
        self.variant = variant
        self.size = size
        self.disabled = disabled
        self.value = value
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Toggle":
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
        
        is_pressed = self.pressed if self.pressed is not None else self.default_pressed
        
        class_str = cn(
            TOGGLE_BASE,
            TOGGLE_VARIANTS.get(self.variant, TOGGLE_VARIANTS["default"]),
            TOGGLE_SIZES.get(self.size, TOGGLE_SIZES["default"]),
            self.extra_class
        )
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' data-state="{"on" if is_pressed else "off"}"'
        attrs_str += f' aria-pressed="{"true" if is_pressed else "false"}"'
        attrs_str += ' data-pynext-toggle'
        
        if self.value:
            attrs_str += f' data-value="{self.value}"'
        
        if self.disabled:
            attrs_str += ' disabled'
        
        if self.on_pressed_change:
            import hashlib
            handler_id = hashlib.md5(str(id(self.on_pressed_change)).encode()).hexdigest()[:8]
            attrs_str += f' data-pynext-change="{handler_id}"'
        
        return f'<button type="button" {attrs_str}>{children_html}</button>'
    
    def __str__(self) -> str:
        return self.render()


class ToggleGroup:
    """
    A group of toggles that work together.
    
    Attributes:
        type: "single" (one at a time) or "multiple" (multiple selections)
        value: Selected value(s)
        on_value_change: Callback when selection changes
    
    Example:
        ToggleGroup(type="single", value=alignment)[
            Toggle(value="left")[AlignLeftIcon()],
            Toggle(value="center")[AlignCenterIcon()],
            Toggle(value="right")[AlignRightIcon()]
        ]
    """
    
    def __init__(
        self,
        type: Literal["single", "multiple"] = "single",
        value: Optional[Union[str, List[str]]] = None,
        default_value: Optional[Union[str, List[str]]] = None,
        on_value_change: Optional[Callable] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.type = type
        self.value = value
        self.default_value = default_value
        self.on_value_change = on_value_change
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "ToggleGroup":
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
        
        class_str = cn("flex items-center justify-center gap-1", self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' data-pynext-toggle-group'
        attrs_str += f' data-type="{self.type}"'
        attrs_str += ' role="group"'
        
        return f'<div {attrs_str}>{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()

