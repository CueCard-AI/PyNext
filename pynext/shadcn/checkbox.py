"""
Checkbox Component

A checkbox input for boolean selections.

Usage:
    from pynext.shadcn import Checkbox
    
    Checkbox(checked=accepted, on_checked_change=set_accepted)
    
    # With label
    div(class_="flex items-center gap-2")[
        Checkbox(id="terms"),
        Label(html_for="terms")["Accept terms and conditions"]
    ]
"""

from typing import Any, Optional, Callable, Literal
from pynext.tw import cn


# Checkbox styles
CHECKBOX_BASE = (
    "peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background "
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring "
    "focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 "
    "data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground"
)


CheckedState = Literal[True, False, "indeterminate"]


class Checkbox:
    """
    A checkbox component.
    
    Attributes:
        checked: Whether the checkbox is checked (True/False/"indeterminate")
        default_checked: Initial checked state
        on_checked_change: Callback when checked state changes
        disabled: Whether the checkbox is disabled
        name: Form field name
        value: Form field value
    
    Example:
        Checkbox(checked=agreed, on_checked_change=set_agreed)
        
        # Indeterminate state (for "select all")
        Checkbox(checked="indeterminate")
    """
    
    def __init__(
        self,
        checked: Optional[CheckedState] = None,
        default_checked: bool = False,
        on_checked_change: Optional[Callable[[CheckedState], None]] = None,
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
        
        if is_checked == "indeterminate":
            state = "indeterminate"
            aria_checked = "mixed"
        elif is_checked:
            state = "checked"
            aria_checked = "true"
        else:
            state = "unchecked"
            aria_checked = "false"
        
        class_str = cn(CHECKBOX_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' role="checkbox"'
        attrs_str += f' aria-checked="{aria_checked}"'
        attrs_str += f' data-state="{state}"'
        attrs_str += ' data-pynext-checkbox'
        
        if self.id:
            attrs_str += f' id="{self.id}"'
        
        if self.disabled:
            attrs_str += ' disabled'
            attrs_str += ' data-disabled'
        
        if self.on_checked_change:
            import hashlib
            handler_id = hashlib.md5(str(id(self.on_checked_change)).encode()).hexdigest()[:8]
            attrs_str += f' data-pynext-change="{handler_id}"'
        
        # Checkmark icon (only shown when checked)
        check_icon = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4" style="display: none;" data-checkbox-icon>
    <polyline points="20 6 9 17 4 12"></polyline>
</svg>
'''
        
        # Indeterminate icon
        indeterminate_icon = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4" style="display: none;" data-checkbox-indeterminate>
    <line x1="5" y1="12" x2="19" y2="12"></line>
</svg>
'''
        
        # Hidden input for form submission
        hidden_input = ""
        if self.name and is_checked is True:
            hidden_input = f'<input type="hidden" name="{self.name}" value="{self.value}" />'
        
        return f'''
<button type="button" {attrs_str}>
    {check_icon}
    {indeterminate_icon}
</button>
{hidden_input}
'''
    
    def __str__(self) -> str:
        return self.render()

