"""
RadioGroup Components

A set of radio buttons where only one can be selected.

Usage:
    from pynext.shadcn import RadioGroup, RadioGroupItem, Label
    
    RadioGroup(value=selected, on_value_change=set_selected)[
        div(class_="flex items-center gap-2")[
            RadioGroupItem(value="option1", id="option1"),
            Label(html_for="option1")["Option 1"]
        ],
        div(class_="flex items-center gap-2")[
            RadioGroupItem(value="option2", id="option2"),
            Label(html_for="option2")["Option 2"]
        ]
    ]
"""

from typing import Any, Optional, List, Union, Callable
from pynext.tw import cn


# RadioGroup styles
RADIO_GROUP_BASE = "grid gap-2"

RADIO_ITEM_BASE = (
    "aspect-square h-4 w-4 rounded-full border border-primary text-primary "
    "ring-offset-background focus:outline-none focus-visible:ring-2 "
    "focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed "
    "disabled:opacity-50"
)

RADIO_INDICATOR_BASE = "flex items-center justify-center"


class RadioGroup:
    """
    A group of radio buttons.
    
    Attributes:
        value: Currently selected value
        default_value: Initial selected value
        on_value_change: Callback when selection changes
        disabled: Whether the entire group is disabled
        name: Form field name
    
    Example:
        RadioGroup(value=size, on_value_change=set_size)[
            RadioGroupItem(value="sm")["Small"],
            RadioGroupItem(value="md")["Medium"],
            RadioGroupItem(value="lg")["Large"]
        ]
    """
    
    def __init__(
        self,
        value: Optional[str] = None,
        default_value: Optional[str] = None,
        on_value_change: Optional[Callable[[str], None]] = None,
        disabled: bool = False,
        name: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.value = value
        self.default_value = default_value
        self.on_value_change = on_value_change
        self.disabled = disabled
        self.name = name
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "RadioGroup":
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
        group_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        class_str = cn(RADIO_GROUP_BASE, self.extra_class)
        
        selected_value = self.value if self.value is not None else self.default_value
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' role="radiogroup"'
        attrs_str += f' data-pynext-radio-group="{group_id}"'
        
        if selected_value:
            attrs_str += f' data-value="{selected_value}"'
        
        if self.disabled:
            attrs_str += ' data-disabled'
        
        return f'<div {attrs_str}>{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class RadioGroupItem:
    """
    A single radio button within a RadioGroup.
    
    Attributes:
        value: The value of this radio option
        disabled: Whether this option is disabled
    
    Example:
        RadioGroupItem(value="option1", id="r1")
    """
    
    def __init__(
        self,
        value: str,
        disabled: bool = False,
        id: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.value = value
        self.disabled = disabled
        self.id = id
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "RadioGroupItem":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        class_str = cn(RADIO_ITEM_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' role="radio"'
        attrs_str += f' data-pynext-radio-item'
        attrs_str += f' data-value="{self.value}"'
        
        if self.id:
            attrs_str += f' id="{self.id}"'
        
        if self.disabled:
            attrs_str += ' disabled'
            attrs_str += ' data-disabled'
        
        # Radio indicator (circle that appears when selected)
        indicator = f'''
<span class="{RADIO_INDICATOR_BASE}">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-2.5 w-2.5" style="display: none;" data-radio-indicator>
        <circle cx="12" cy="12" r="6"></circle>
    </svg>
</span>
'''
        
        return f'<button type="button" {attrs_str}>{indicator}</button>'
    
    def __str__(self) -> str:
        return self.render()

