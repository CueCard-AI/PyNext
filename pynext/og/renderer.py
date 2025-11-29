"""
OG Image Renderer.

Render OGCanvas to image bytes using Pillow.

Example:
    from pynext.og import OGCanvas, OGRenderer
    
    canvas = OGCanvas(background="gradient:blue").add_text("Hello", x=60, y=200)
    renderer = OGRenderer()
    image_bytes = renderer.render(canvas)

Why This Matters:
    The renderer converts the abstract canvas representation
    into actual image bytes that can be served to browsers.
"""

from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re
import math

from pynext.og.canvas import OGCanvas, TextElement, ImageElement, RectElement, Element
from pynext.og.templates import GRADIENTS


# ============================================
# Color Utilities
# ============================================

def parse_color(color: str) -> Tuple[int, int, int, int]:
    """
    Parse color string to RGBA tuple.
    
    Supports:
    - Hex: #RGB, #RRGGBB, #RRGGBBAA
    - RGB: rgb(r, g, b)
    - RGBA: rgba(r, g, b, a)
    - Named colors: white, black, etc.
    
    Args:
        color: Color string
    
    Returns:
        (R, G, B, A) tuple with values 0-255
    """
    color = color.strip()
    
    # Named colors
    named_colors = {
        "white": (255, 255, 255, 255),
        "black": (0, 0, 0, 255),
        "red": (255, 0, 0, 255),
        "green": (0, 255, 0, 255),
        "blue": (0, 0, 255, 255),
        "transparent": (0, 0, 0, 0),
    }
    
    if color.lower() in named_colors:
        return named_colors[color.lower()]
    
    # Hex colors
    if color.startswith("#"):
        hex_color = color[1:]
        
        if len(hex_color) == 3:
            # #RGB -> #RRGGBB
            hex_color = "".join(c * 2 for c in hex_color)
        
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b, 255)
        
        if len(hex_color) == 8:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16)
            return (r, g, b, a)
    
    # rgba(r, g, b, a)
    rgba_match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)', color)
    if rgba_match:
        r, g, b = int(rgba_match.group(1)), int(rgba_match.group(2)), int(rgba_match.group(3))
        a = float(rgba_match.group(4)) if rgba_match.group(4) else 1.0
        return (r, g, b, int(a * 255))
    
    # Default to black
    return (0, 0, 0, 255)


def parse_gradient(gradient: str) -> List[Tuple[Tuple[int, int, int, int], float]]:
    """
    Parse linear-gradient CSS to color stops.
    
    Args:
        gradient: CSS gradient string
    
    Returns:
        List of (color, position) tuples
    """
    # Extract colors from linear-gradient
    match = re.match(r'linear-gradient\s*\(\s*(\d+)deg\s*,\s*(.+)\s*\)', gradient)
    if not match:
        # Try without angle
        match = re.match(r'linear-gradient\s*\(\s*(.+)\s*\)', gradient)
        if not match:
            return [(parse_color("#ffffff"), 0.0), (parse_color("#000000"), 1.0)]
        colors_str = match.group(1)
    else:
        colors_str = match.group(2)
    
    # Parse color stops
    colors = []
    parts = [p.strip() for p in colors_str.split(",")]
    
    for i, part in enumerate(parts):
        color = parse_color(part)
        position = i / max(len(parts) - 1, 1)
        colors.append((color, position))
    
    return colors


# ============================================
# OG Renderer
# ============================================

class OGRenderer:
    """
    Render OGCanvas to image bytes using Pillow.
    
    Uses Pillow (PIL) for image generation.
    Caches fonts for performance.
    
    Example:
        renderer = OGRenderer()
        
        canvas = OGCanvas(background="gradient:blue").add_text("Hello", x=60, y=200)
        image_bytes = renderer.render(canvas)
        
        # Save to file
        with open("og.png", "wb") as f:
            f.write(image_bytes)
    """
    
    def __init__(self, fonts_dir: Optional[Path] = None):
        """
        Initialize renderer.
        
        Args:
            fonts_dir: Directory containing font files
        """
        self.fonts_dir = fonts_dir
        self._font_cache: Dict[str, Any] = {}
    
    def render(self, canvas: OGCanvas, format: str = "png") -> bytes:
        """
        Render canvas to image bytes.
        
        Args:
            canvas: OGCanvas to render
            format: Output format (png, jpeg, webp)
        
        Returns:
            Image bytes
        """
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            raise ImportError("Pillow is required for OG image rendering. Install with: pip install Pillow")
        
        # Create base image
        img = Image.new("RGBA", (canvas.width, canvas.height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Render background
        self._render_background(img, draw, canvas.background)
        
        # Render elements in order
        for element in canvas.elements:
            if isinstance(element, TextElement):
                self._render_text(img, draw, element)
            elif isinstance(element, RectElement):
                self._render_rect(img, draw, element)
            elif isinstance(element, ImageElement):
                self._render_image(img, element)
        
        # Convert to bytes
        buffer = BytesIO()
        
        # Convert RGBA to RGB for JPEG
        if format.lower() == "jpeg":
            img = img.convert("RGB")
        
        save_format = format.upper()
        if save_format == "JPG":
            save_format = "JPEG"
        
        img.save(buffer, format=save_format, quality=canvas.quality)
        return buffer.getvalue()
    
    def _render_background(self, img: Any, draw: Any, background: str):
        """Render background color or gradient."""
        from PIL import Image
        
        # Check for gradient shorthand
        if background.startswith("gradient:"):
            name = background.split(":")[1]
            background = GRADIENTS.get(name, GRADIENTS["slate"])
        
        # Check for linear-gradient
        if background.startswith("linear-gradient"):
            self._render_gradient(img, background)
        else:
            # Solid color
            color = parse_color(background)
            draw.rectangle([0, 0, img.width, img.height], fill=color[:3])
    
    def _render_gradient(self, img: Any, gradient: str):
        """Render linear gradient background."""
        from PIL import Image
        
        # Parse gradient
        colors = parse_gradient(gradient)
        if len(colors) < 2:
            return
        
        # Parse angle (default 135 degrees)
        angle_match = re.match(r'linear-gradient\s*\(\s*(\d+)deg', gradient)
        angle = int(angle_match.group(1)) if angle_match else 135
        
        # Convert angle to radians and calculate direction
        angle_rad = math.radians(angle)
        
        # For each pixel, calculate gradient position
        width, height = img.size
        
        # Simple top-left to bottom-right gradient for 135deg
        for y in range(height):
            for x in range(width):
                # Calculate position along gradient (0.0 to 1.0)
                if angle == 135:
                    pos = (x + y) / (width + height)
                elif angle == 45:
                    pos = (x + (height - y)) / (width + height)
                elif angle == 90:
                    pos = x / width
                elif angle == 180:
                    pos = y / height
                else:
                    # General case
                    pos = (x * math.cos(angle_rad) + y * math.sin(angle_rad)) / (
                        width * abs(math.cos(angle_rad)) + height * abs(math.sin(angle_rad))
                    )
                
                pos = max(0.0, min(1.0, pos))
                
                # Find color stops
                color1, pos1 = colors[0]
                color2, pos2 = colors[-1]
                
                for i in range(len(colors) - 1):
                    if colors[i][1] <= pos <= colors[i + 1][1]:
                        color1, pos1 = colors[i]
                        color2, pos2 = colors[i + 1]
                        break
                
                # Interpolate
                if pos2 - pos1 > 0:
                    t = (pos - pos1) / (pos2 - pos1)
                else:
                    t = 0
                
                r = int(color1[0] + (color2[0] - color1[0]) * t)
                g = int(color1[1] + (color2[1] - color1[1]) * t)
                b = int(color1[2] + (color2[2] - color1[2]) * t)
                
                img.putpixel((x, y), (r, g, b, 255))
    
    def _render_text(self, img: Any, draw: Any, element: TextElement):
        """Render text element."""
        from PIL import ImageFont
        
        # Get or load font
        font = self._get_font(element.font_family, element.font_size, element.font_weight)
        
        # Parse color
        color = parse_color(element.color)
        
        # Handle text wrapping
        text = element.text
        if element.max_width:
            text = self._wrap_text(text, font, element.max_width)
        
        # Calculate position based on alignment
        x = element.x
        if element.align == "center":
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = element.x - text_width // 2
        elif element.align == "right":
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = element.x - text_width
        
        # Draw text
        draw.text((x, element.y), text, font=font, fill=color[:3])
    
    def _render_rect(self, img: Any, draw: Any, element: RectElement):
        """Render rectangle element."""
        color = parse_color(element.color)
        
        # Apply opacity
        if element.opacity < 1.0:
            color = (color[0], color[1], color[2], int(color[3] * element.opacity))
        
        # Draw rectangle
        if element.border_radius > 0:
            # Rounded rectangle
            self._draw_rounded_rect(
                draw,
                (element.x, element.y, element.x + element.width, element.y + element.height),
                element.border_radius,
                color[:3],
            )
        else:
            draw.rectangle(
                [element.x, element.y, element.x + element.width, element.y + element.height],
                fill=color[:3],
            )
    
    def _render_image(self, img: Any, element: ImageElement):
        """Render image element."""
        from PIL import Image
        
        try:
            # Load image
            if element.src.startswith(("http://", "https://")):
                # URL - skip for now (would need requests)
                return
            else:
                # Local file
                src_path = Path(element.src)
                if not src_path.exists():
                    return
                src_img = Image.open(src_path)
            
            # Resize based on object_fit
            if element.object_fit == "cover":
                src_img = self._cover_resize(src_img, element.width, element.height)
            elif element.object_fit == "contain":
                src_img = self._contain_resize(src_img, element.width, element.height)
            else:
                src_img = src_img.resize((element.width, element.height))
            
            # Apply border radius
            if element.border_radius > 0:
                src_img = self._apply_border_radius(src_img, element.border_radius)
            
            # Paste onto main image
            if src_img.mode == "RGBA":
                img.paste(src_img, (element.x, element.y), src_img)
            else:
                img.paste(src_img, (element.x, element.y))
                
        except Exception:
            # Skip images that can't be loaded
            pass
    
    def _get_font(self, family: str, size: int, weight: str) -> Any:
        """Get or load a font."""
        from PIL import ImageFont
        
        cache_key = f"{family}-{size}-{weight}"
        
        if cache_key not in self._font_cache:
            # Try to load font file
            font = None
            
            if self.fonts_dir:
                # Look for font file
                font_name = f"{family}-{weight.capitalize()}.ttf"
                font_path = self.fonts_dir / font_name
                if font_path.exists():
                    font = ImageFont.truetype(str(font_path), size)
            
            if font is None:
                # Fall back to default font
                try:
                    # Try system font
                    font = ImageFont.truetype("Arial", size)
                except OSError:
                    # Fall back to Pillow's default font
                    font = ImageFont.load_default()
            
            self._font_cache[cache_key] = font
        
        return self._font_cache[cache_key]
    
    def _wrap_text(self, text: str, font: Any, max_width: int) -> str:
        """Wrap text to fit within max_width."""
        from PIL import ImageDraw, Image
        
        # Create temp draw for measuring
        temp_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(temp_img)
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return "\n".join(lines)
    
    def _draw_rounded_rect(self, draw: Any, bounds: Tuple, radius: int, color: Tuple):
        """Draw a rounded rectangle."""
        x1, y1, x2, y2 = bounds
        
        # Draw rectangles
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=color)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=color)
        
        # Draw corners
        draw.ellipse([x1, y1, x1 + radius * 2, y1 + radius * 2], fill=color)
        draw.ellipse([x2 - radius * 2, y1, x2, y1 + radius * 2], fill=color)
        draw.ellipse([x1, y2 - radius * 2, x1 + radius * 2, y2], fill=color)
        draw.ellipse([x2 - radius * 2, y2 - radius * 2, x2, y2], fill=color)
    
    def _cover_resize(self, img: Any, width: int, height: int) -> Any:
        """Resize image to cover area (may crop)."""
        from PIL import Image
        
        src_ratio = img.width / img.height
        dst_ratio = width / height
        
        if src_ratio > dst_ratio:
            # Source is wider - fit height, crop width
            new_height = height
            new_width = int(height * src_ratio)
        else:
            # Source is taller - fit width, crop height
            new_width = width
            new_height = int(width / src_ratio)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to exact size
        left = (new_width - width) // 2
        top = (new_height - height) // 2
        return img.crop((left, top, left + width, top + height))
    
    def _contain_resize(self, img: Any, width: int, height: int) -> Any:
        """Resize image to fit within area (may have letterboxing)."""
        from PIL import Image
        
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        return img
    
    def _apply_border_radius(self, img: Any, radius: int) -> Any:
        """Apply border radius to image."""
        from PIL import Image, ImageDraw
        
        # Create mask
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        
        # Draw rounded rectangle on mask
        self._draw_rounded_rect(draw, (0, 0, img.width, img.height), radius, 255)
        
        # Apply mask
        img = img.convert("RGBA")
        img.putalpha(mask)
        
        return img


# ============================================
# Convenience Functions
# ============================================

def render_canvas(canvas: OGCanvas, format: str = "png") -> bytes:
    """
    Render a canvas to image bytes.
    
    Args:
        canvas: OGCanvas to render
        format: Output format
    
    Returns:
        Image bytes
    """
    renderer = OGRenderer()
    return renderer.render(canvas, format)


def save_canvas(canvas: OGCanvas, path: Path, format: str = "png"):
    """
    Save a canvas to a file.
    
    Args:
        canvas: OGCanvas to render
        path: Output file path
        format: Output format
    """
    image_bytes = render_canvas(canvas, format)
    Path(path).write_bytes(image_bytes)

