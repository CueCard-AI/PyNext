"""
PyNext OG Image Module.

Generate beautiful Open Graph images for social media sharing.

Example:
    from pynext import og_image, OGCanvas, OGTemplate
    
    # Simple usage
    @og_image()
    def BlogPost(slug: str):
        ...
    
    # With template
    @og_image(template=templates.blog_post)
    def BlogPost(slug: str):
        ...
    
    # Full control
    @og_image()
    def BlogPost(slug: str):
        ...
    
    @BlogPost.og
    def generate_og(slug: str) -> OGCanvas:
        return OGCanvas(background="gradient:blue").add_text(...)
"""

from pynext.og.canvas import (
    OGCanvas,
    TextElement,
    ImageElement,
    RectElement,
)

from pynext.og.templates import (
    OGTemplate,
    blog_post,
    product,
    profile,
    minimal,
)

from pynext.og.decorator import (
    og_image,
    OGConfig,
)

from pynext.og.renderer import (
    OGRenderer,
)

# Expose templates as a namespace
from pynext.og import templates

__all__ = [
    # Canvas
    "OGCanvas",
    "TextElement",
    "ImageElement",
    "RectElement",
    # Templates
    "OGTemplate",
    "blog_post",
    "product",
    "profile",
    "minimal",
    "templates",
    # Decorator
    "og_image",
    "OGConfig",
    # Renderer
    "OGRenderer",
]

