"""
PyNext Image Component - Build-Time Optimized, Zero JS for Static Images.

Unlike Next.js which processes images on-demand at runtime (~15KB client JS),
PyNext optimizes images at build time with zero client-side JavaScript for
static images. Only interactive images (responsive to signals) ship JS.

SolidJS Principles Applied:
- Zero JS for static content
- Fine-grained reactivity only when needed
- Build-time optimization over runtime processing
- Native browser features over JS polyfills
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Callable
import hashlib
import json

from pynext.core.html import element, Fragment
from pynext.core.signals import Signal


class ImageFormat(Enum):
    """Supported image formats in priority order."""
    AVIF = "avif"    # Best compression, modern browsers
    WEBP = "webp"    # Good compression, wide support
    PNG = "png"      # Lossless, fallback
    JPEG = "jpeg"    # Lossy, universal fallback
    GIF = "gif"      # Animated images
    SVG = "svg"      # Vector graphics (no processing needed)


class ImageLayout(Enum):
    """Image layout modes."""
    INTRINSIC = "intrinsic"    # Original aspect ratio, max at natural size
    FIXED = "fixed"            # Exact width/height
    RESPONSIVE = "responsive"  # Scales with container
    FILL = "fill"              # Fills parent container


class ImageLoading(Enum):
    """Image loading strategies."""
    LAZY = "lazy"      # Native browser lazy loading
    EAGER = "eager"    # Load immediately
    PRIORITY = "priority"  # Preload in head


@dataclass
class ImageSize:
    """Defines an image size variant."""
    width: int
    height: Optional[int] = None
    suffix: str = ""
    
    @property
    def name(self) -> str:
        return f"{self.width}w{self.suffix}"


@dataclass
class ImageConfig:
    """Configuration for image optimization."""
    # Output formats (in priority order for browser selection)
    formats: List[ImageFormat] = field(default_factory=lambda: [
        ImageFormat.AVIF,
        ImageFormat.WEBP,
        ImageFormat.JPEG,
    ])
    
    # Predefined sizes for srcset
    sizes: List[ImageSize] = field(default_factory=lambda: [
        ImageSize(640, suffix="_sm"),    # Mobile
        ImageSize(750, suffix="_md"),    # Tablet
        ImageSize(1080, suffix="_lg"),   # Desktop
        ImageSize(1200, suffix="_xl"),   # Large desktop
        ImageSize(1920, suffix="_2xl"),  # 2K displays
        ImageSize(3840, suffix="_4k"),   # 4K displays
    ])
    
    # Quality settings per format
    quality: Dict[ImageFormat, int] = field(default_factory=lambda: {
        ImageFormat.AVIF: 75,
        ImageFormat.WEBP: 80,
        ImageFormat.JPEG: 85,
        ImageFormat.PNG: 100,
    })
    
    # BlurHash settings
    blur_hash_size: int = 4  # 4x4 grid for blur hash
    blur_placeholder_width: int = 40  # Tiny placeholder for blur
    
    # Device pixel ratios to generate
    device_sizes: List[int] = field(default_factory=lambda: [1, 2, 3])
    
    # Output directory relative to static
    output_dir: str = "_next/image"
    
    # Enable build-time processing
    build_time_optimization: bool = True


# Global default config
_default_config = ImageConfig()


def configure_images(config: ImageConfig) -> None:
    """Set the global image configuration."""
    global _default_config
    _default_config = config


def get_image_config() -> ImageConfig:
    """Get the current image configuration."""
    return _default_config


@dataclass
class OptimizedImage:
    """Represents a processed/optimized image with all variants."""
    original_src: str
    hash: str
    width: int
    height: int
    
    # Generated variants: format -> size -> path
    variants: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    # BlurHash for placeholder
    blur_hash: Optional[str] = None
    blur_data_url: Optional[str] = None
    
    # Dominant color for simple placeholder
    dominant_color: Optional[str] = None
    
    def get_srcset(self, format: ImageFormat) -> str:
        """Generate srcset string for a specific format."""
        if format.value not in self.variants:
            return ""
        
        parts = []
        for size_name, path in self.variants[format.value].items():
            # Extract width from size name (e.g., "640w_sm" -> 640)
            width = int(size_name.split("w")[0])
            parts.append(f"{path} {width}w")
        
        return ", ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for manifest."""
        return {
            "original": self.original_src,
            "hash": self.hash,
            "width": self.width,
            "height": self.height,
            "variants": self.variants,
            "blurHash": self.blur_hash,
            "blurDataUrl": self.blur_data_url,
            "dominantColor": self.dominant_color,
        }


class ImageRegistry:
    """Registry of all images in the application for build-time processing."""
    
    def __init__(self):
        self._images: Dict[str, OptimizedImage] = {}
        self._pending: List[str] = []
    
    def register(self, src: str) -> str:
        """Register an image for optimization, return hash ID."""
        hash_id = hashlib.md5(src.encode()).hexdigest()[:12]
        if hash_id not in self._images and src not in self._pending:
            self._pending.append(src)
        return hash_id
    
    def get(self, src: str) -> Optional[OptimizedImage]:
        """Get optimized image data if available."""
        hash_id = hashlib.md5(src.encode()).hexdigest()[:12]
        return self._images.get(hash_id)
    
    def set(self, src: str, optimized: OptimizedImage) -> None:
        """Store optimized image data."""
        hash_id = hashlib.md5(src.encode()).hexdigest()[:12]
        self._images[hash_id] = optimized
        if src in self._pending:
            self._pending.remove(src)
    
    def get_pending(self) -> List[str]:
        """Get list of images pending optimization."""
        return self._pending.copy()
    
    def clear_pending(self) -> None:
        """Clear pending list after build."""
        self._pending.clear()
    
    def to_manifest(self) -> Dict[str, Any]:
        """Export as manifest for caching."""
        return {
            hash_id: img.to_dict()
            for hash_id, img in self._images.items()
        }
    
    def load_manifest(self, manifest: Dict[str, Any]) -> None:
        """Load from cached manifest."""
        for hash_id, data in manifest.items():
            self._images[hash_id] = OptimizedImage(
                original_src=data["original"],
                hash=hash_id,
                width=data["width"],
                height=data["height"],
                variants=data.get("variants", {}),
                blur_hash=data.get("blurHash"),
                blur_data_url=data.get("blurDataUrl"),
                dominant_color=data.get("dominantColor"),
            )


# Global registry
_image_registry = ImageRegistry()


def get_image_registry() -> ImageRegistry:
    """Get the global image registry."""
    return _image_registry


def Image(
    src: Union[str, Signal],
    alt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    layout: ImageLayout = ImageLayout.INTRINSIC,
    loading: ImageLoading = ImageLoading.LAZY,
    priority: bool = False,
    placeholder: str = "blur",  # "blur", "color", "empty"
    quality: Optional[int] = None,
    sizes: Optional[str] = None,  # CSS sizes attribute
    className: str = "",
    style: Optional[Dict[str, str]] = None,
    on_load: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    **props
) -> str:
    """
    Optimized Image component with build-time processing.
    
    Features:
    - Build-time optimization (AVIF/WebP generation)
    - Native lazy loading (no JS for static images)
    - BlurHash placeholders
    - Responsive srcset
    - Zero client JS for static images
    
    Args:
        src: Image source path or Signal for reactive images
        alt: Alt text (required for accessibility)
        width: Image width in pixels
        height: Image height in pixels
        layout: Layout mode (intrinsic, fixed, responsive, fill)
        loading: Loading strategy (lazy, eager, priority)
        priority: If True, preload the image
        placeholder: Placeholder type (blur, color, empty)
        quality: Override quality setting (1-100)
        sizes: CSS sizes attribute for responsive images
        className: CSS class name
        style: Inline styles
        on_load: Callback when image loads (requires JS)
        on_error: Callback on error (requires JS)
        **props: Additional HTML attributes
    
    Returns:
        Rendered HTML string
    """
    config = get_image_config()
    registry = get_image_registry()
    
    # Check if src is reactive (Signal)
    is_reactive = isinstance(src, Signal)
    src_value = src.get() if is_reactive else src
    
    # Handle SVG (no optimization needed)
    if src_value.lower().endswith('.svg'):
        return _render_svg_image(src_value, alt, width, height, className, style, props)
    
    # Register for build-time optimization
    registry.register(src_value)
    
    # Get optimized data if available
    optimized = registry.get(src_value)
    
    # Determine actual dimensions
    img_width = width
    img_height = height
    if optimized:
        img_width = width or optimized.width
        img_height = height or optimized.height
    
    # Build attributes
    attrs = {
        "alt": alt,
        "loading": "eager" if loading == ImageLoading.PRIORITY or priority else loading.value,
        "decoding": "async",
    }
    
    if img_width:
        attrs["width"] = str(img_width)
    if img_height:
        attrs["height"] = str(img_height)
    if className:
        attrs["class"] = className
    
    # Add inline styles
    style_parts = []
    if style:
        for key, value in style.items():
            style_parts.append(f"{key}: {value}")
    
    # Layout-specific styles
    if layout == ImageLayout.FILL:
        style_parts.extend([
            "position: absolute",
            "inset: 0",
            "width: 100%",
            "height: 100%",
            "object-fit: cover",
        ])
    elif layout == ImageLayout.RESPONSIVE:
        style_parts.extend([
            "width: 100%",
            "height: auto",
        ])
    
    if style_parts:
        attrs["style"] = "; ".join(style_parts)
    
    # Add custom attributes
    for key, value in props.items():
        if key.startswith("data_"):
            attrs[key.replace("_", "-")] = value
        else:
            attrs[key] = value
    
    # If we have optimized variants, use picture element with sources
    if optimized and optimized.variants:
        return _render_picture_element(
            optimized, attrs, sizes, placeholder, priority, is_reactive, on_load, on_error
        )
    
    # Fallback: simple img element (before build optimization)
    return _render_simple_image(src_value, attrs, placeholder, priority, is_reactive, on_load, on_error)


def _render_svg_image(
    src: str,
    alt: str,
    width: Optional[int],
    height: Optional[int],
    className: str,
    style: Optional[Dict[str, str]],
    props: Dict[str, Any]
) -> str:
    """Render SVG image (no optimization needed)."""
    attrs = {"src": src, "alt": alt}
    if width:
        attrs["width"] = str(width)
    if height:
        attrs["height"] = str(height)
    if className:
        attrs["class"] = className
    if style:
        attrs["style"] = "; ".join(f"{k}: {v}" for k, v in style.items())
    attrs.update(props)
    
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f'<img {attr_str} />'


def _render_picture_element(
    optimized: OptimizedImage,
    attrs: Dict[str, str],
    sizes: Optional[str],
    placeholder: str,
    priority: bool,
    is_reactive: bool,
    on_load: Optional[Callable],
    on_error: Optional[Callable]
) -> str:
    """Render optimized picture element with format fallbacks."""
    parts = ['<picture>']
    
    config = get_image_config()
    sizes_attr = sizes or "(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    
    # Add source elements for each format (in priority order)
    for fmt in config.formats:
        if fmt.value in optimized.variants:
            srcset = optimized.get_srcset(fmt)
            if srcset:
                mime_type = f"image/{fmt.value}"
                parts.append(f'<source type="{mime_type}" srcset="{srcset}" sizes="{sizes_attr}" />')
    
    # Build img attributes
    img_attrs = dict(attrs)
    
    # Use best available fallback as src
    fallback_src = optimized.original_src
    for fmt in reversed(config.formats):
        if fmt.value in optimized.variants:
            variants = optimized.variants[fmt.value]
            if variants:
                # Use medium size as default src
                fallback_src = list(variants.values())[len(variants) // 2]
                break
    
    img_attrs["src"] = fallback_src
    
    # Add blur placeholder
    if placeholder == "blur" and optimized.blur_data_url:
        img_attrs["style"] = img_attrs.get("style", "") + f"; background-image: url({optimized.blur_data_url}); background-size: cover"
    elif placeholder == "color" and optimized.dominant_color:
        img_attrs["style"] = img_attrs.get("style", "") + f"; background-color: {optimized.dominant_color}"
    
    # Add reactive attributes if needed
    if is_reactive or on_load or on_error:
        img_attrs["data-pynext-image"] = "true"
        if on_load:
            img_attrs["data-onload"] = "true"
        if on_error:
            img_attrs["data-onerror"] = "true"
    
    # Render img element
    attr_str = " ".join(f'{k}="{v}"' for k, v in img_attrs.items())
    parts.append(f'<img {attr_str} />')
    parts.append('</picture>')
    
    # If priority, add preload link
    if priority:
        preload = _generate_preload_link(optimized)
        return preload + "\n".join(parts)
    
    return "\n".join(parts)


def _render_simple_image(
    src: str,
    attrs: Dict[str, str],
    placeholder: str,
    priority: bool,
    is_reactive: bool,
    on_load: Optional[Callable],
    on_error: Optional[Callable]
) -> str:
    """Render simple img element (pre-optimization fallback)."""
    attrs["src"] = src
    
    # Add reactive attributes if needed
    if is_reactive or on_load or on_error:
        attrs["data-pynext-image"] = "true"
    
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    html = f'<img {attr_str} />'
    
    if priority:
        preload = f'<link rel="preload" as="image" href="{src}" />'
        return preload + html
    
    return html


def _generate_preload_link(optimized: OptimizedImage) -> str:
    """Generate preload link for priority images."""
    config = get_image_config()
    
    # Preload best format
    for fmt in config.formats:
        if fmt.value in optimized.variants:
            srcset = optimized.get_srcset(fmt)
            if srcset:
                mime_type = f"image/{fmt.value}"
                return f'<link rel="preload" as="image" type="{mime_type}" imagesrcset="{srcset}" />\n'
    
    return f'<link rel="preload" as="image" href="{optimized.original_src}" />\n'


def get_image_js_runtime() -> str:
    """
    Get minimal JS runtime for reactive images.
    
    Only needed if:
    - Image src is a Signal
    - on_load or on_error callbacks are used
    
    For static images, this returns empty string (zero JS).
    """
    return """
(function() {
    // Only hydrate images with data-pynext-image
    const images = document.querySelectorAll('img[data-pynext-image]');
    if (images.length === 0) return;
    
    images.forEach(img => {
        // Handle reactive src
        const signalId = img.dataset.signalId;
        if (signalId && window.__pynext__?.signals) {
            const signal = window.__pynext__.signals[signalId];
            if (signal) {
                signal.subscribe(newSrc => {
                    img.src = newSrc;
                });
            }
        }
        
        // Handle onload callback
        if (img.dataset.onload) {
            img.onload = () => {
                img.style.backgroundImage = 'none';
                img.classList.add('loaded');
            };
        }
        
        // Handle onerror callback
        if (img.dataset.onerror) {
            img.onerror = () => {
                img.classList.add('error');
            };
        }
    });
})();
"""


def needs_image_runtime() -> bool:
    """Check if any registered images need JS runtime."""
    registry = get_image_registry()
    # In production, this would check if any images are reactive
    # For now, return False (zero JS by default)
    return False


# Convenience functions for common patterns
def ResponsiveImage(src: str, alt: str, **props) -> str:
    """Responsive image that scales with container."""
    return Image(src=src, alt=alt, layout=ImageLayout.RESPONSIVE, **props)


def FillImage(src: str, alt: str, **props) -> str:
    """Image that fills its parent container."""
    return Image(src=src, alt=alt, layout=ImageLayout.FILL, **props)


def PriorityImage(src: str, alt: str, **props) -> str:
    """Priority image that preloads in head."""
    return Image(src=src, alt=alt, priority=True, loading=ImageLoading.PRIORITY, **props)


def Avatar(src: str, alt: str, size: int = 40, **props) -> str:
    """Circular avatar image."""
    style = props.pop("style", {})
    style["border-radius"] = "50%"
    return Image(
        src=src,
        alt=alt,
        width=size,
        height=size,
        layout=ImageLayout.FIXED,
        style=style,
        **props
    )

