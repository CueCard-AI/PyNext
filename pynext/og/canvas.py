"""
OG Image Canvas.

Build OG images with a chainable, fluent API.

Example:
    canvas = (
        OGCanvas(background="gradient:blue")
        .add_text("Hello World", x=60, y=200, font_size=64)
        .add_image("avatar.png", x=60, y=400, width=80, height=80)
    )

Why This Matters:
    OG images need multiple elements (text, images, shapes).
    The Canvas pattern lets you build them step-by-step
    with a clean, readable API.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union


# ============================================
# Element Types
# ============================================

@dataclass
class TextElement:
    """
    Text element for OG canvas.
    
    Attributes:
        text: The text content
        x: X position in pixels
        y: Y position in pixels
        font_size: Font size in pixels
        font_weight: normal or bold
        font_family: Font family name
        color: Text color (hex, rgb, rgba)
        max_width: Max width before wrapping
        line_height: Line height multiplier
        align: Text alignment (left, center, right)
    """
    text: str
    x: int
    y: int
    font_size: int = 32
    font_weight: Literal["normal", "bold"] = "normal"
    font_family: str = "Inter"
    color: str = "#000000"
    max_width: Optional[int] = None
    line_height: float = 1.4
    align: Literal["left", "center", "right"] = "left"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": "text",
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "font_family": self.font_family,
            "color": self.color,
            "max_width": self.max_width,
            "line_height": self.line_height,
            "align": self.align,
        }


@dataclass
class ImageElement:
    """
    Image element for OG canvas.
    
    Attributes:
        src: Image source (URL or local path)
        x: X position in pixels
        y: Y position in pixels
        width: Image width
        height: Image height
        border_radius: Corner radius for rounded images
        object_fit: How to fit image (cover, contain, fill)
    """
    src: str
    x: int
    y: int
    width: int
    height: int
    border_radius: int = 0
    object_fit: Literal["cover", "contain", "fill"] = "cover"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": "image",
            "src": self.src,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "border_radius": self.border_radius,
            "object_fit": self.object_fit,
        }


@dataclass
class RectElement:
    """
    Rectangle element for OG canvas.
    
    Attributes:
        x: X position in pixels
        y: Y position in pixels
        width: Rectangle width
        height: Rectangle height
        color: Fill color
        border_radius: Corner radius
        opacity: Opacity (0.0 to 1.0)
    """
    x: int
    y: int
    width: int
    height: int
    color: str = "#000000"
    border_radius: int = 0
    opacity: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": "rect",
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "color": self.color,
            "border_radius": self.border_radius,
            "opacity": self.opacity,
        }


# Type alias for any element
Element = Union[TextElement, ImageElement, RectElement]


# ============================================
# OG Canvas
# ============================================

@dataclass
class OGCanvas:
    """
    Canvas for building OG images.
    
    Standard OG image size is 1200x630 pixels.
    Use chainable methods to add elements.
    
    Attributes:
        width: Canvas width (default 1200)
        height: Canvas height (default 630)
        background: Background color, gradient, or image
        quality: Image quality for JPEG (1-100)
    
    Example:
        canvas = (
            OGCanvas(background="gradient:blue")
            .add_text("My Title", x=60, y=200, font_size=64, font_weight="bold")
            .add_text("Subtitle", x=60, y=300, font_size=32, color="#666666")
            .add_image("logo.png", x=60, y=500, width=100, height=100)
        )
    """
    width: int = 1200
    height: int = 630
    background: str = "#ffffff"
    quality: int = 90
    
    # Internal element storage
    _elements: List[Element] = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        """Validate canvas dimensions."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Canvas dimensions must be positive")
        
        if not 1 <= self.quality <= 100:
            raise ValueError("Quality must be between 1 and 100")
    
    def add_text(
        self,
        text: str,
        x: int,
        y: int,
        font_size: int = 32,
        font_weight: Literal["normal", "bold"] = "normal",
        font_family: str = "Inter",
        color: str = "#000000",
        max_width: Optional[int] = None,
        line_height: float = 1.4,
        align: Literal["left", "center", "right"] = "left",
    ) -> "OGCanvas":
        """
        Add text to the canvas.
        
        Args:
            text: Text content to display
            x: X position in pixels from left
            y: Y position in pixels from top
            font_size: Font size in pixels
            font_weight: "normal" or "bold"
            font_family: Font family name
            color: Text color (hex, rgb, rgba)
            max_width: Maximum width before text wraps
            line_height: Line height multiplier
            align: Text alignment
        
        Returns:
            Self for chaining
        
        Example:
            canvas.add_text("Hello", x=60, y=100, font_size=48, color="white")
        """
        element = TextElement(
            text=text,
            x=x,
            y=y,
            font_size=font_size,
            font_weight=font_weight,
            font_family=font_family,
            color=color,
            max_width=max_width,
            line_height=line_height,
            align=align,
        )
        self._elements.append(element)
        return self
    
    def add_image(
        self,
        src: str,
        x: int,
        y: int,
        width: int,
        height: int,
        border_radius: int = 0,
        object_fit: Literal["cover", "contain", "fill"] = "cover",
    ) -> "OGCanvas":
        """
        Add an image to the canvas.
        
        Args:
            src: Image source (URL or local path)
            x: X position in pixels from left
            y: Y position in pixels from top
            width: Image width in pixels
            height: Image height in pixels
            border_radius: Corner radius for rounded images
            object_fit: How to fit image in bounds
        
        Returns:
            Self for chaining
        
        Example:
            canvas.add_image("avatar.png", x=60, y=400, width=80, height=80, border_radius=40)
        """
        element = ImageElement(
            src=src,
            x=x,
            y=y,
            width=width,
            height=height,
            border_radius=border_radius,
            object_fit=object_fit,
        )
        self._elements.append(element)
        return self
    
    def add_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: str = "#000000",
        border_radius: int = 0,
        opacity: float = 1.0,
    ) -> "OGCanvas":
        """
        Add a rectangle to the canvas.
        
        Args:
            x: X position in pixels from left
            y: Y position in pixels from top
            width: Rectangle width in pixels
            height: Rectangle height in pixels
            color: Fill color
            border_radius: Corner radius
            opacity: Opacity (0.0 to 1.0)
        
        Returns:
            Self for chaining
        
        Example:
            canvas.add_rect(x=0, y=500, width=1200, height=130, color="#000000", opacity=0.5)
        """
        element = RectElement(
            x=x,
            y=y,
            width=width,
            height=height,
            color=color,
            border_radius=border_radius,
            opacity=opacity,
        )
        self._elements.append(element)
        return self
    
    @property
    def elements(self) -> List[Element]:
        """Get all elements on the canvas."""
        return self._elements.copy()
    
    def clear(self) -> "OGCanvas":
        """
        Remove all elements from the canvas.
        
        Returns:
            Self for chaining
        """
        self._elements.clear()
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert canvas to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "width": self.width,
            "height": self.height,
            "background": self.background,
            "quality": self.quality,
            "elements": [el.to_dict() for el in self._elements],
        }
    
    def clone(self) -> "OGCanvas":
        """
        Create a copy of this canvas.
        
        Returns:
            New OGCanvas with same properties and elements
        """
        new_canvas = OGCanvas(
            width=self.width,
            height=self.height,
            background=self.background,
            quality=self.quality,
        )
        new_canvas._elements = self._elements.copy()
        return new_canvas


# ============================================
# Convenience Functions
# ============================================

def create_canvas(
    background: str = "#ffffff",
    width: int = 1200,
    height: int = 630,
) -> OGCanvas:
    """
    Create a new OG canvas with defaults.
    
    Args:
        background: Background color or gradient
        width: Canvas width
        height: Canvas height
    
    Returns:
        New OGCanvas
    
    Example:
        canvas = create_canvas(background="gradient:blue")
    """
    return OGCanvas(width=width, height=height, background=background)

