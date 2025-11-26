"""
Portal Primitive

Renders content outside the normal DOM tree, typically used for modals,
dropdowns, and tooltips that need to escape parent overflow/z-index contexts.

Usage:
    Portal()[
        Dialog()[...]
    ]
"""

from typing import Any, Optional, List, Union
from pynext.core.component import Component


class Portal(Component):
    """
    Renders children into a different part of the DOM.
    
    By default, renders into document.body. This allows modals and
    dropdowns to escape parent containers with overflow: hidden or
    complex stacking contexts.
    
    Attributes:
        container: CSS selector for the container to render into.
                   Defaults to "body".
        
    Example:
        Portal()[
            div(class_="modal-overlay")[
                div(class_="modal-content")[
                    "Modal content here"
                ]
            ]
        ]
    """
    
    def __init__(
        self,
        container: str = "body",
        **attrs: Any
    ):
        self.container = container
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Portal":
        """Add children using bracket syntax: Portal()[content]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """
        Render the portal.
        
        The portal is rendered with a data attribute that the client-side
        JavaScript uses to move it to the target container.
        """
        from pynext.core.html import div
        
        # Render children
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        # Wrap in a portal container that JS will process
        return f'<div data-pynext-portal="{self.container}" style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


# Client-side JavaScript for portal functionality is in pynext/runtime/ui.js

