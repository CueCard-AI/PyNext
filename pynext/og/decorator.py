"""
OG Image Decorator.

Mark pages for automatic OG image generation.

Example:
    from pynext import og_image
    
    @og_image()
    def BlogPost(slug: str):
        ...
    
    # With custom template
    @og_image(template=templates.blog_post)
    def BlogPost(slug: str):
        ...
    
    # With custom generator
    @og_image()
    def BlogPost(slug: str):
        ...
    
    @BlogPost.og
    def generate_og(slug: str) -> OGCanvas:
        return OGCanvas(...).add_text(...)

Why This Matters:
    The decorator pattern makes OG image generation opt-in.
    Just add @og_image() and PyNext handles the rest.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Literal, Optional, Union

from pynext.og.templates import OGTemplate


# ============================================
# OG Configuration
# ============================================

@dataclass
class OGConfig:
    """
    Configuration for OG image generation.
    
    Attributes:
        template: OGTemplate to use for generation
        cache: Cache duration (True = 3600s, int = seconds, False = no cache)
        format: Output format (png, jpeg, webp)
        quality: Image quality (1-100, for jpeg/webp)
        enabled: Whether OG generation is enabled
    """
    template: OGTemplate
    cache: Union[bool, int] = True
    format: Literal["png", "jpeg", "webp"] = "png"
    quality: int = 90
    enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if not 1 <= self.quality <= 100:
            raise ValueError("Quality must be between 1 and 100")
        
        if self.format not in ("png", "jpeg", "webp"):
            raise ValueError("Format must be png, jpeg, or webp")
    
    @property
    def cache_seconds(self) -> int:
        """Get cache duration in seconds."""
        if isinstance(self.cache, bool):
            return 3600 if self.cache else 0
        return self.cache
    
    @property
    def media_type(self) -> str:
        """Get MIME type for format."""
        return {
            "png": "image/png",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
        }[self.format]


# ============================================
# OG Image Decorator
# ============================================

def og_image(
    template: Optional[OGTemplate] = None,
    cache: Union[bool, int] = True,
    format: Literal["png", "jpeg", "webp"] = "png",
    quality: int = 90,
) -> Callable:
    """
    Decorator to enable OG image generation for a page.
    
    When applied to a page component, PyNext will:
    1. Generate OG images at /og/{path}.png
    2. Auto-inject og:image meta tags
    3. Cache images with ISR
    
    Args:
        template: OGTemplate to use (default: minimal template)
        cache: Cache duration (True = 3600s, int = seconds, False = no cache)
        format: Output format (png, jpeg, webp)
        quality: Image quality (1-100)
    
    Returns:
        Decorated function with OG config attached
    
    Example:
        # Simple usage
        @og_image()
        def BlogPost(slug: str):
            ...
        
        # With template
        from pynext.og import templates
        
        @og_image(template=templates.blog_post)
        def BlogPost(slug: str):
            ...
        
        # With caching
        @og_image(cache=86400)  # Cache for 24 hours
        def BlogPost(slug: str):
            ...
        
        # As JPEG
        @og_image(format="jpeg", quality=85)
        def BlogPost(slug: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Create OG config
        config = OGConfig(
            template=template or OGTemplate(),
            cache=cache,
            format=format,
            quality=quality,
        )
        
        # Attach config to function
        func._og_config = config
        func._og_handler = None
        
        # Add .og decorator for custom handler
        def og_handler_decorator(handler: Callable) -> Callable:
            """Register custom OG image generator."""
            func._og_handler = handler
            return handler
        
        func.og = og_handler_decorator
        
        return func
    
    return decorator


# ============================================
# Utility Functions
# ============================================

def has_og_config(func: Callable) -> bool:
    """
    Check if a function has OG config attached.
    
    Args:
        func: Function to check
    
    Returns:
        True if function has OG config
    """
    return hasattr(func, "_og_config") and isinstance(func._og_config, OGConfig)


def get_og_config(func: Callable) -> Optional[OGConfig]:
    """
    Get OG config from a function.
    
    Args:
        func: Function with OG config
    
    Returns:
        OGConfig or None
    """
    if has_og_config(func):
        return func._og_config
    return None


def get_og_handler(func: Callable) -> Optional[Callable]:
    """
    Get custom OG handler from a function.
    
    Args:
        func: Function with OG handler
    
    Returns:
        Custom handler function or None
    """
    if hasattr(func, "_og_handler"):
        return func._og_handler
    return None


def generate_og_meta_tags(
    path: str,
    base_url: str,
    width: int = 1200,
    height: int = 630,
) -> str:
    """
    Generate OG image meta tags.
    
    Args:
        path: Page path (e.g., "/blog/my-post")
        base_url: Site base URL (e.g., "https://example.com")
        width: Image width
        height: Image height
    
    Returns:
        HTML meta tags string
    """
    # Normalize path
    path = path.lstrip("/")
    image_url = f"{base_url.rstrip('/')}/og/{path}.png"
    
    tags = [
        f'<meta property="og:image" content="{image_url}">',
        f'<meta property="og:image:width" content="{width}">',
        f'<meta property="og:image:height" content="{height}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:image" content="{image_url}">',
    ]
    
    return "\n".join(tags)

