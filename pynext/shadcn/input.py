"""
Input, Label, and Textarea Components

Form input components matching ShadCN/ui design.

Usage:
    from pynext.shadcn import Input, Label, Textarea
    
    Label(html_for="email")["Email"]
    Input(id="email", type="email", placeholder="you@example.com")
    
    Label(html_for="bio")["Bio"]
    Textarea(id="bio", placeholder="Tell us about yourself")
"""

from typing import Any, Optional, List, Union, Callable, Literal
from pynext.tw import cn


# Input base styles
INPUT_BASE = (
    "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 "
    "text-sm ring-offset-background file:border-0 file:bg-transparent "
    "file:text-sm file:font-medium placeholder:text-muted-foreground "
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring "
    "focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
)

# Label base styles
LABEL_BASE = (
    "text-sm font-medium leading-none peer-disabled:cursor-not-allowed "
    "peer-disabled:opacity-70"
)

# Textarea base styles
TEXTAREA_BASE = (
    "flex min-h-[80px] w-full rounded-md border border-input bg-background "
    "px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground "
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring "
    "focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
)


class Input:
    """
    An input field component for forms.
    
    Attributes:
        type: Input type - "text", "email", "password", "number", etc.
        placeholder: Placeholder text
        disabled: Whether the input is disabled
        value: Current value
        on_change: Change handler function
        class_: Additional CSS classes
    
    Example:
        Input(type="email", placeholder="you@example.com")
        Input(type="password", placeholder="••••••••")
        Input(value=name, on_change=set_name)
    """
    
    def __init__(
        self,
        type: str = "text",
        placeholder: Optional[str] = None,
        disabled: bool = False,
        value: Optional[str] = None,
        on_change: Optional[Callable] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.type = type
        self.placeholder = placeholder
        self.disabled = disabled
        self.value = value
        self.on_change = on_change
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        """Render the input as HTML."""
        class_str = cn(INPUT_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' type="{self.type}"'
        
        if self.placeholder:
            attrs_str += f' placeholder="{self.placeholder}"'
        
        if self.disabled:
            attrs_str += ' disabled'
        
        if self.value is not None:
            attrs_str += f' value="{self.value}"'
        
        if self.on_change:
            import hashlib
            handler_id = hashlib.md5(str(id(self.on_change)).encode()).hexdigest()[:8]
            attrs_str += f' data-pynext-change="{handler_id}"'
        
        # Add any extra attributes
        for key, value in self.attrs.items():
            if key == "class_":
                continue
            attr_name = key.rstrip("_").replace("_", "-")
            if isinstance(value, bool):
                if value:
                    attrs_str += f' {attr_name}'
            else:
                attrs_str += f' {attr_name}="{value}"'
        
        return f'<input {attrs_str} />'
    
    def __str__(self) -> str:
        return self.render()


class Label:
    """
    A label component for form inputs.
    
    Attributes:
        html_for: ID of the input this label is for
        class_: Additional CSS classes
    
    Example:
        Label(html_for="email")["Email Address"]
    """
    
    def __init__(
        self,
        html_for: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.html_for = html_for
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Label":
        """Add children using bracket syntax: Label()["Email"]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """Render the label as HTML."""
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        class_str = cn(LABEL_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        
        if self.html_for:
            attrs_str += f' for="{self.html_for}"'
        
        for key, value in self.attrs.items():
            if key == "class_":
                continue
            attr_name = key.rstrip("_").replace("_", "-")
            if isinstance(value, bool):
                if value:
                    attrs_str += f' {attr_name}'
            else:
                attrs_str += f' {attr_name}="{value}"'
        
        return f'<label {attrs_str}>{children_html}</label>'
    
    def __str__(self) -> str:
        return self.render()


class Textarea:
    """
    A textarea component for multi-line input.
    
    Attributes:
        placeholder: Placeholder text
        disabled: Whether the textarea is disabled
        value: Current value
        rows: Number of visible rows
        on_change: Change handler function
        class_: Additional CSS classes
    
    Example:
        Textarea(placeholder="Tell us about yourself")
        Textarea(rows=6, value=bio, on_change=set_bio)
    """
    
    def __init__(
        self,
        placeholder: Optional[str] = None,
        disabled: bool = False,
        value: Optional[str] = None,
        rows: Optional[int] = None,
        on_change: Optional[Callable] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.placeholder = placeholder
        self.disabled = disabled
        self.value = value
        self.rows = rows
        self.on_change = on_change
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        """Render the textarea as HTML."""
        class_str = cn(TEXTAREA_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        
        if self.placeholder:
            attrs_str += f' placeholder="{self.placeholder}"'
        
        if self.disabled:
            attrs_str += ' disabled'
        
        if self.rows:
            attrs_str += f' rows="{self.rows}"'
        
        if self.on_change:
            import hashlib
            handler_id = hashlib.md5(str(id(self.on_change)).encode()).hexdigest()[:8]
            attrs_str += f' data-pynext-change="{handler_id}"'
        
        for key, value in self.attrs.items():
            if key == "class_":
                continue
            attr_name = key.rstrip("_").replace("_", "-")
            if isinstance(value, bool):
                if value:
                    attrs_str += f' {attr_name}'
            else:
                attrs_str += f' {attr_name}="{value}"'
        
        content = self.value if self.value is not None else ""
        
        return f'<textarea {attrs_str}>{content}</textarea>'
    
    def __str__(self) -> str:
        return self.render()

