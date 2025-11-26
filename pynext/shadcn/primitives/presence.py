"""
Presence Primitive

Manages mount/unmount animations for components. Delays unmounting
until exit animations complete.

Usage:
    Presence(present=is_visible)[
        AnimatedDialog()[...]
    ]
"""

from typing import Any, Optional, List, Union
from pynext.core.component import Component


class Presence(Component):
    """
    Manages component presence with animation support.
    
    When `present` changes from True to False, the component stays
    mounted until the exit animation completes. This prevents the
    common problem of components disappearing before their exit
    animation can play.
    
    Attributes:
        present: Whether the component should be visible.
        animation_duration: How long to wait before unmounting (ms).
    
    Example:
        is_open = Signal(True)
        
        Presence(present=is_open.value, animation_duration=200)[
            div(class_="modal animate-fade-in data-[closing]:animate-fade-out")[
                "Modal content"
            ]
        ]
    """
    
    def __init__(
        self,
        present: bool = True,
        animation_duration: int = 150,
        **attrs: Any
    ):
        self.present = present
        self.animation_duration = animation_duration
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Presence":
        """Add children using bracket syntax: Presence()[content]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """
        Render the presence container.
        
        The client-side JavaScript handles:
        1. Adding data-state="open" or data-state="closed"
        2. Waiting for animation duration before unmounting
        3. Cleaning up after animation completes
        """
        if not self.present:
            # When not present, don't render anything
            # (Client-side JS handles the exit animation timing)
            return ""
        
        # Render children
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        # Build data attributes for client-side handling
        data_attrs = f'data-pynext-presence="true"'
        data_attrs += f' data-pynext-presence-duration="{self.animation_duration}"'
        data_attrs += f' data-state="{"open" if self.present else "closed"}"'
        
        return f'<div {data_attrs} style="display:contents">{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()

