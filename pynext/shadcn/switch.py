"""
Switch Component

A toggle switch for boolean values.

Usage:
    from pynext.shadcn import Switch
    
    Switch(checked=notifications, on_checked_change=set_notifications)
"""

from typing import Any, Optional, Callable
from pynext.tw import cn


# Switch styles
SWITCH_BASE = (
    "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full "
    "border-2 border-transparent transition-colors focus-visible:outline-none "
    "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 "
    "focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 "
    "data-[state=checked]:bg-primary data-[state=unchecked]:bg-input"
)

SWITCH_THUMB_BASE = (
    "pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 "
    "transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0"
)


class Switch:
    """
    A toggle switch component.
    
    Attributes:
        checked: Whether the switch is checked
        default_checked: Initial checked state
        on_checked_change: Callback when checked state changes
        disabled: Whether the switch is disabled
        name: Form field name
        value: Form field value
    
    Example:
        Switch(checked=enabled, on_checked_change=set_enabled)
        
        # With label
        div(class_="flex items-center gap-2")[
            Switch(id="notifications", checked=notifications),
            Label(html_for="notifications")["Enable notifications"]
        ]
    """
    
    def __init__(
        self,
        checked: Optional[bool] = None,
        default_checked: bool = False,
        on_checked_change: Optional[Callable[[bool], None]] = None,
        disabled: bool = False,
        name: Optional[str] = None,
        value: str = "on",
        id: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.checked = checked
        self.default_checked = default_checked
        self.on_checked_change = on_checked_change
        self.disabled = disabled
        self.name = name
        self.value = value
        self.id = id
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        is_checked = self.checked if self.checked is not None else self.default_checked
        state = "checked" if is_checked else "unchecked"
        
        switch_class = cn(SWITCH_BASE, self.extra_class)
        
        attrs_str = f'class="{switch_class}"'
        attrs_str += f' role="switch"'
        attrs_str += f' aria-checked="{"true" if is_checked else "false"}"'
        attrs_str += f' data-state="{state}"'
        attrs_str += ' data-pynext-switch'
        
        if self.id:
            attrs_str += f' id="{self.id}"'
        
        if self.disabled:
            attrs_str += ' disabled'
            attrs_str += ' data-disabled'
        
        if self.on_checked_change:
            import hashlib
            handler_id = hashlib.md5(str(id(self.on_checked_change)).encode()).hexdigest()[:8]
            attrs_str += f' data-pynext-change="{handler_id}"'
        
        # Hidden input for form submission
        hidden_input = ""
        if self.name:
            hidden_input = f'<input type="hidden" name="{self.name}" value="{self.value if is_checked else ""}" />'
        
        return f'''
<button type="button" {attrs_str}>
    <span class="{SWITCH_THUMB_BASE}" data-state="{state}"></span>
</button>
{hidden_input}
'''
    
    def __str__(self) -> str:
        return self.render()

