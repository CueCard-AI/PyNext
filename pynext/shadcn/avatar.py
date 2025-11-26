"""
Avatar Component

A user avatar with image and fallback support.

Usage:
    from pynext.shadcn import Avatar, AvatarImage, AvatarFallback
    
    Avatar()[
        AvatarImage(src="/avatar.jpg", alt="User"),
        AvatarFallback()["JD"]
    ]
"""

from typing import Any, Optional, List, Union
from pynext.tw import cn


# Avatar styles
AVATAR_BASE = "relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full"
AVATAR_IMAGE_BASE = "aspect-square h-full w-full"
AVATAR_FALLBACK_BASE = (
    "flex h-full w-full items-center justify-center rounded-full "
    "bg-muted"
)


class Avatar:
    """
    Container for avatar image and fallback.
    
    Attributes:
        class_: Additional CSS classes
    
    Example:
        Avatar()[
            AvatarImage(src="https://example.com/avatar.jpg"),
            AvatarFallback()["JD"]
        ]
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Avatar":
        """Add children using bracket syntax."""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """Render the avatar container."""
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        class_str = cn(AVATAR_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        
        for key, value in self.attrs.items():
            if key == "class_":
                continue
            attr_name = key.rstrip("_").replace("_", "-")
            if isinstance(value, bool):
                if value:
                    attrs_str += f' {attr_name}'
            else:
                attrs_str += f' {attr_name}="{value}"'
        
        return f'<span {attrs_str}>{children_html}</span>'
    
    def __str__(self) -> str:
        return self.render()


class AvatarImage:
    """
    The avatar image element.
    
    Attributes:
        src: Image source URL
        alt: Alt text for accessibility
        class_: Additional CSS classes
    
    Example:
        AvatarImage(src="/avatar.jpg", alt="John Doe")
    """
    
    def __init__(
        self,
        src: str,
        alt: str = "",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.src = src
        self.alt = alt
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        """Render the avatar image."""
        class_str = cn(AVATAR_IMAGE_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' src="{self.src}"'
        attrs_str += f' alt="{self.alt}"'
        
        for key, value in self.attrs.items():
            if key == "class_":
                continue
            attr_name = key.rstrip("_").replace("_", "-")
            if isinstance(value, bool):
                if value:
                    attrs_str += f' {attr_name}'
            else:
                attrs_str += f' {attr_name}="{value}"'
        
        # Use data attribute for JS to handle image load/error
        return f'<img {attrs_str} data-pynext-avatar-image />'
    
    def __str__(self) -> str:
        return self.render()


class AvatarFallback:
    """
    Fallback shown when image fails to load or while loading.
    
    Typically shows initials or an icon.
    
    Attributes:
        delay_ms: Delay before showing fallback (allows image to load)
        class_: Additional CSS classes
    
    Example:
        AvatarFallback()["JD"]
        AvatarFallback()[UserIcon()]
    """
    
    def __init__(
        self,
        delay_ms: int = 600,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.delay_ms = delay_ms
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AvatarFallback":
        """Add children using bracket syntax: AvatarFallback()["JD"]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """Render the avatar fallback."""
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        class_str = cn(AVATAR_FALLBACK_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' data-pynext-avatar-fallback'
        attrs_str += f' data-delay="{self.delay_ms}"'
        
        for key, value in self.attrs.items():
            if key == "class_":
                continue
            attr_name = key.rstrip("_").replace("_", "-")
            if isinstance(value, bool):
                if value:
                    attrs_str += f' {attr_name}'
            else:
                attrs_str += f' {attr_name}="{value}"'
        
        return f'<span {attrs_str}>{children_html}</span>'
    
    def __str__(self) -> str:
        return self.render()

