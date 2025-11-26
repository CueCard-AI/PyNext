"""
Focus Trap Primitive

Traps keyboard focus within a container, essential for accessible modals
and dialogs. Users can tab through focusable elements but focus won't
escape the container.

Usage:
    FocusTrap()[
        Dialog()[...]
    ]
"""

from typing import Any, Optional, List, Union
from pynext.core.component import Component


class FocusTrap(Component):
    """
    Traps keyboard focus within its children.
    
    When active, pressing Tab or Shift+Tab cycles through focusable
    elements within the container instead of leaving it. This is
    essential for accessibility in modals and dialogs.
    
    Attributes:
        active: Whether the focus trap is active. Default True.
        auto_focus: Automatically focus the first focusable element.
        return_focus: Return focus to the previously focused element
                     when the trap is deactivated.
    
    Example:
        FocusTrap(active=modal_open)[
            div(class_="modal")[
                button()["Close"],
                input(placeholder="Name"),
                button()["Submit"]
            ]
        ]
    """
    
    def __init__(
        self,
        active: bool = True,
        auto_focus: bool = True,
        return_focus: bool = True,
        **attrs: Any
    ):
        self.active = active
        self.auto_focus = auto_focus
        self.return_focus = return_focus
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "FocusTrap":
        """Add children using bracket syntax: FocusTrap()[content]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """
        Render the focus trap container.
        
        The container has data attributes that the client-side JavaScript
        uses to manage focus trapping.
        """
        # Render children
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        # Build data attributes
        data_attrs = f'data-pynext-focus-trap="{"true" if self.active else "false"}"'
        if self.auto_focus:
            data_attrs += ' data-pynext-focus-trap-autofocus="true"'
        if self.return_focus:
            data_attrs += ' data-pynext-focus-trap-return="true"'
        
        return f'<div {data_attrs} style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


# Focusable element selector used by client-side JS
FOCUSABLE_SELECTOR = """
    a[href],
    area[href],
    input:not([disabled]),
    select:not([disabled]),
    textarea:not([disabled]),
    button:not([disabled]),
    iframe,
    object,
    embed,
    [tabindex]:not([tabindex="-1"]),
    [contenteditable]
""".replace("\n", "").replace("    ", "")

