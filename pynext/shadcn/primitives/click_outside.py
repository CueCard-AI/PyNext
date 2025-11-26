"""
Click Outside Primitive

Detects clicks outside of a container, commonly used to close
dropdowns, modals, and popovers when clicking away.

Usage:
    ClickOutside(on_click_outside=close_menu)[
        DropdownContent()[...]
    ]
"""

from typing import Any, Optional, List, Union, Callable
from pynext.core.component import Component


class ClickOutside(Component):
    """
    Detects and handles clicks outside the container.
    
    When a click occurs outside the children of this component,
    the on_click_outside callback is triggered. This is useful
    for dismissing modals, dropdowns, and popovers.
    
    Attributes:
        on_click_outside: Callback function when clicking outside.
        enabled: Whether detection is active. Default True.
        ignore_selector: CSS selector for elements to ignore.
    
    Example:
        is_open = Signal(True)
        
        ClickOutside(
            on_click_outside=lambda: is_open.set(False),
            enabled=is_open.value
        )[
            div(class_="dropdown")[
                "Dropdown content"
            ]
        ]
    """
    
    def __init__(
        self,
        on_click_outside: Optional[Callable] = None,
        enabled: bool = True,
        ignore_selector: Optional[str] = None,
        **attrs: Any
    ):
        self.on_click_outside = on_click_outside
        self.enabled = enabled
        self.ignore_selector = ignore_selector
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "ClickOutside":
        """Add children using bracket syntax: ClickOutside()[content]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """
        Render the click outside container.
        
        Uses data attributes for client-side JavaScript to handle
        click detection.
        """
        # Render children
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        # Build data attributes
        data_attrs = f'data-pynext-click-outside="{"true" if self.enabled else "false"}"'
        
        if self.ignore_selector:
            data_attrs += f' data-pynext-click-outside-ignore="{self.ignore_selector}"'
        
        # The actual callback is handled via signals or server actions
        # The client-side JS dispatches a custom event that PyNext handles
        if self.on_click_outside:
            # Generate a unique ID for this handler
            import hashlib
            handler_id = hashlib.md5(str(id(self.on_click_outside)).encode()).hexdigest()[:8]
            data_attrs += f' data-pynext-click-outside-handler="{handler_id}"'
        
        return f'<div {data_attrs} style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()

