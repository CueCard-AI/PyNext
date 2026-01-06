"""
Button Component

A button component with multiple variants and sizes, matching ShadCN/ui design.

Usage:
    from pynext.shadcn import Button
    
    Button()["Click me"]
    Button(variant="destructive")["Delete"]
    Button(variant="outline", size="lg")["Large Outline"]
"""

from typing import Any, Optional, List, Union, Callable, Literal
from pynext.tw import cn


# Button variant styles
BUTTON_VARIANTS = {
    "default": "bg-primary text-primary-foreground hover:bg-primary/90",
    "destructive": "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    "outline": "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
    "secondary": "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    "ghost": "hover:bg-accent hover:text-accent-foreground",
    "link": "text-primary underline-offset-4 hover:underline",
}

# Button size styles
BUTTON_SIZES = {
    "default": "h-10 px-4 py-2",
    "sm": "h-9 rounded-md px-3",
    "lg": "h-11 rounded-md px-8",
    "icon": "h-10 w-10",
}

# Base button styles
BUTTON_BASE = (
    "inline-flex items-center justify-center whitespace-nowrap rounded-md "
    "text-sm font-medium ring-offset-background transition-colors "
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring "
    "focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
)


ButtonVariant = Literal["default", "destructive", "outline", "secondary", "ghost", "link"]
ButtonSize = Literal["default", "sm", "lg", "icon"]


class Button:
    """
    A versatile button component with multiple variants and sizes.
    
    Attributes:
        variant: Visual style - "default", "destructive", "outline", 
                 "secondary", "ghost", or "link"
        size: Button size - "default", "sm", "lg", or "icon"
        disabled: Whether the button is disabled
        type: HTML button type - "button", "submit", or "reset"
        on_click: Click handler function
        as_child: If True, merges props onto child instead of rendering button
        class_: Additional CSS classes
    
    Example:
        # Basic usage
        Button()["Click me"]
        
        # Variants
        Button(variant="destructive")["Delete"]
        Button(variant="outline")["Cancel"]
        
        # Sizes
        Button(size="sm")["Small"]
        Button(size="lg")["Large"]
        
        # With click handler
        Button(on_click=handle_click)["Submit"]
        
        # As a link (using as_child)
        Button(as_child=True)[
            a(href="/dashboard")["Dashboard"]
        ]
    """
    
    def __init__(
        self,
        variant: ButtonVariant = "default",
        size: ButtonSize = "default",
        disabled: bool = False,
        type: Literal["button", "submit", "reset"] = "button",
        on_click: Optional[Callable] = None,
        as_child: bool = False,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.variant = variant
        self.size = size
        self.disabled = disabled
        self.type = type
        self.on_click = on_click
        self.as_child = as_child
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Button":
        """Add children using bracket syntax: Button()["Click me"]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def get_class(self) -> str:
        """Build the complete class string for the button."""
        return cn(
            BUTTON_BASE,
            BUTTON_VARIANTS.get(self.variant, BUTTON_VARIANTS["default"]),
            BUTTON_SIZES.get(self.size, BUTTON_SIZES["default"]),
            self.extra_class
        )
    
    def render(self) -> str:
        """Render the button as HTML."""
        # Render children
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        # If as_child, use Slot to merge props onto child
        if self.as_child and self._children:
            from .primitives.slot import Slot
            props = {
                "class_": self.get_class(),
                "disabled": self.disabled,
                **self.attrs
            }
            return Slot(props=props)[self._children[0]].render()
        
        # Build attributes
        attrs_str = f'class="{self.get_class()}"'
        attrs_str += f' type="{self.type}"'
        
        if self.disabled:
            attrs_str += ' disabled'
        
        # Handle click events - transpile Python lambda to JavaScript
        if self.on_click:
            from pynext.transpiler.pynext import transpile_handler_body
            from pynext.transpiler.reactive import analyze_handler
            
            # CRITICAL FIX: Auto-detect reactive context from handler's closure
            # This finds signals, forms, memos, stores that the handler uses
            ctx = analyze_handler(self.on_click)
            try:
                js_code = transpile_handler_body(self.on_click, ctx)
                # Escape double quotes for HTML attribute safety
                import html
                js_code_escaped = html.escape(js_code, quote=True)
                
                # Only add 'return' for simple expressions, not statement blocks
                # Check if the JS starts with a statement keyword
                js_trimmed = js_code.strip()
                is_statement_block = any(js_trimmed.startswith(kw) for kw in ['if ', 'if(', 'for ', 'for(', 'while ', 'while(', 'let ', 'const ', 'var ', 'try ', 'try{', 'switch ', 'switch('])
                
                if is_statement_block:
                    # Multi-statement block - wrap in IIFE
                    attrs_str += f' data-pynext-on-click="(function() {{ {js_code_escaped} }})();"'
                else:
                    # Simple expression - transpiler already added 'return' keyword
                    # DON'T add another 'return' here!
                    attrs_str += f' data-pynext-on-click="{js_code_escaped};"'
            except Exception as e:
                # If transpilation fails, skip the handler
                import sys
                print(f"[Button] Transpilation failed: {e}", file=sys.stderr)
                pass
        
        # Add any extra attributes
        for key, value in self.attrs.items():
            if key == "class_":
                continue  # Already handled
            attr_name = key.rstrip("_").replace("_", "-")
            if isinstance(value, bool):
                if value:
                    attrs_str += f' {attr_name}'
            else:
                attrs_str += f' {attr_name}="{value}"'
        
        return f'<button {attrs_str}>{children_html}</button>'
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"Button(variant={self.variant!r}, size={self.size!r})"

