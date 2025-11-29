"""
Pre-built OG Image Templates.

Use templates for quick, beautiful OG images without custom code.

Example:
    from pynext import og_image
    from pynext.og import templates
    
    @og_image(template=templates.blog_post)
    def BlogPost(slug: str):
        ...

Why This Matters:
    Most OG images follow common patterns (blog, product, profile).
    Templates provide these patterns out of the box.
"""

from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional
import re

from pynext.og.canvas import OGCanvas


# ============================================
# Gradient Definitions
# ============================================

GRADIENTS: Dict[str, str] = {
    "slate": "linear-gradient(135deg, #334155, #1e293b)",
    "gray": "linear-gradient(135deg, #4b5563, #1f2937)",
    "zinc": "linear-gradient(135deg, #52525b, #18181b)",
    "neutral": "linear-gradient(135deg, #525252, #171717)",
    "stone": "linear-gradient(135deg, #57534e, #1c1917)",
    "red": "linear-gradient(135deg, #ef4444, #b91c1c)",
    "orange": "linear-gradient(135deg, #f97316, #ea580c)",
    "amber": "linear-gradient(135deg, #f59e0b, #d97706)",
    "yellow": "linear-gradient(135deg, #eab308, #ca8a04)",
    "lime": "linear-gradient(135deg, #84cc16, #65a30d)",
    "green": "linear-gradient(135deg, #10b981, #059669)",
    "emerald": "linear-gradient(135deg, #10b981, #047857)",
    "teal": "linear-gradient(135deg, #14b8a6, #0d9488)",
    "cyan": "linear-gradient(135deg, #06b6d4, #0891b2)",
    "sky": "linear-gradient(135deg, #0ea5e9, #0284c7)",
    "blue": "linear-gradient(135deg, #3b82f6, #1d4ed8)",
    "indigo": "linear-gradient(135deg, #6366f1, #4f46e5)",
    "violet": "linear-gradient(135deg, #8b5cf6, #7c3aed)",
    "purple": "linear-gradient(135deg, #a855f7, #9333ea)",
    "fuchsia": "linear-gradient(135deg, #d946ef, #c026d3)",
    "pink": "linear-gradient(135deg, #ec4899, #db2777)",
    "rose": "linear-gradient(135deg, #f43f5e, #e11d48)",
    # Multi-color gradients
    "sunset": "linear-gradient(135deg, #f97316, #ec4899)",
    "ocean": "linear-gradient(135deg, #06b6d4, #3b82f6)",
    "forest": "linear-gradient(135deg, #10b981, #14b8a6)",
    "aurora": "linear-gradient(135deg, #8b5cf6, #06b6d4)",
    "candy": "linear-gradient(135deg, #ec4899, #f97316)",
}


# ============================================
# OG Template
# ============================================

@dataclass
class OGTemplate:
    """
    Pre-defined OG image template.
    
    Templates use mustache-style placeholders ({{variable}})
    that are replaced with context values.
    
    Attributes:
        title: Title text with {{placeholders}}
        subtitle: Optional subtitle with {{placeholders}}
        background: Color, gradient name, or gradient CSS
        logo: Optional logo image path
        font_family: Font family for text
        title_size: Title font size
        subtitle_size: Subtitle font size
        title_color: Title text color
        subtitle_color: Subtitle text color
        padding: Edge padding in pixels
    
    Example:
        template = OGTemplate(
            title="{{title}}",
            subtitle="{{date}} · {{category}}",
            background="gradient:blue",
        )
        
        canvas = template.render({
            "title": "My Blog Post",
            "date": "Jan 1, 2025",
            "category": "Tech",
        })
    """
    title: str = "{{title}}"
    subtitle: Optional[str] = None
    background: str = "gradient:slate"
    logo: Optional[str] = None
    font_family: str = "Inter"
    title_size: int = 64
    subtitle_size: int = 32
    title_color: str = "#ffffff"
    subtitle_color: str = "rgba(255,255,255,0.8)"
    padding: int = 60
    
    # Class-level gradient definitions
    GRADIENTS: ClassVar[Dict[str, str]] = GRADIENTS
    
    def _interpolate(self, template: str, context: Dict[str, Any]) -> str:
        """
        Replace {{placeholders}} with context values.
        
        Args:
            template: String with {{placeholders}}
            context: Dictionary of values
        
        Returns:
            Interpolated string
        """
        def replace(match):
            key = match.group(1).strip()
            return str(context.get(key, f"{{{{{key}}}}}"))
        
        return re.sub(r'\{\{(\w+)\}\}', replace, template)
    
    def _resolve_background(self, background: str) -> str:
        """
        Resolve background to actual value.
        
        Args:
            background: Color, gradient:name, or gradient CSS
        
        Returns:
            Resolved background string
        """
        if background.startswith("gradient:"):
            name = background.split(":")[1]
            return self.GRADIENTS.get(name, self.GRADIENTS["slate"])
        return background
    
    def render(self, context: Dict[str, Any]) -> OGCanvas:
        """
        Render template with context values.
        
        Args:
            context: Dictionary of values for placeholders
        
        Returns:
            OGCanvas with rendered content
        
        Example:
            canvas = template.render({
                "title": "My Post",
                "date": "Jan 1, 2025",
            })
        """
        # Interpolate placeholders
        title = self._interpolate(self.title, context)
        subtitle = self._interpolate(self.subtitle, context) if self.subtitle else None
        
        # Resolve background
        background = self._resolve_background(self.background)
        
        # Create canvas
        canvas = OGCanvas(background=background)
        
        # Add logo if present
        if self.logo:
            canvas.add_image(
                self.logo,
                x=self.padding,
                y=self.padding,
                width=120,
                height=40,
            )
        
        # Calculate title position
        title_y = 200 if not self.logo else 180
        
        # Add title
        canvas.add_text(
            title,
            x=self.padding,
            y=title_y,
            font_size=self.title_size,
            font_weight="bold",
            font_family=self.font_family,
            color=self.title_color,
            max_width=1200 - (self.padding * 2),
        )
        
        # Add subtitle if present
        if subtitle:
            subtitle_y = title_y + self.title_size + 20
            canvas.add_text(
                subtitle,
                x=self.padding,
                y=subtitle_y,
                font_size=self.subtitle_size,
                font_weight="normal",
                font_family=self.font_family,
                color=self.subtitle_color,
                max_width=1200 - (self.padding * 2),
            )
        
        return canvas
    
    def with_logo(self, logo: str) -> "OGTemplate":
        """
        Create a copy with a logo.
        
        Args:
            logo: Path to logo image
        
        Returns:
            New template with logo
        """
        return OGTemplate(
            title=self.title,
            subtitle=self.subtitle,
            background=self.background,
            logo=logo,
            font_family=self.font_family,
            title_size=self.title_size,
            subtitle_size=self.subtitle_size,
            title_color=self.title_color,
            subtitle_color=self.subtitle_color,
            padding=self.padding,
        )
    
    def with_background(self, background: str) -> "OGTemplate":
        """
        Create a copy with a different background.
        
        Args:
            background: New background value
        
        Returns:
            New template with background
        """
        return OGTemplate(
            title=self.title,
            subtitle=self.subtitle,
            background=background,
            logo=self.logo,
            font_family=self.font_family,
            title_size=self.title_size,
            subtitle_size=self.subtitle_size,
            title_color=self.title_color,
            subtitle_color=self.subtitle_color,
            padding=self.padding,
        )


# ============================================
# Pre-built Templates
# ============================================

# Blog post template - title with date and category
blog_post = OGTemplate(
    title="{{title}}",
    subtitle="{{date}} · {{category}}",
    background="gradient:slate",
)

# Product template - product name with price
product = OGTemplate(
    title="{{name}}",
    subtitle="{{price}}",
    background="gradient:blue",
    title_size=56,
)

# Profile template - user name with bio
profile = OGTemplate(
    title="{{name}}",
    subtitle="{{bio}}",
    background="gradient:purple",
)

# Minimal template - just title
minimal = OGTemplate(
    title="{{title}}",
    subtitle=None,
    background="gradient:slate",
)

# Documentation template - docs with section
docs = OGTemplate(
    title="{{title}}",
    subtitle="{{section}} · Documentation",
    background="gradient:indigo",
)

# Event template - event with date and location
event = OGTemplate(
    title="{{title}}",
    subtitle="{{date}} · {{location}}",
    background="gradient:orange",
)

# Announcement template - bold announcement
announcement = OGTemplate(
    title="{{title}}",
    subtitle="{{description}}",
    background="gradient:rose",
    title_size=72,
)

# Video template - video title with duration
video = OGTemplate(
    title="{{title}}",
    subtitle="{{duration}} · {{channel}}",
    background="gradient:red",
)


# ============================================
# Template Factory
# ============================================

def create_template(
    title: str = "{{title}}",
    subtitle: Optional[str] = None,
    background: str = "gradient:slate",
    **kwargs,
) -> OGTemplate:
    """
    Create a custom OG template.
    
    Args:
        title: Title with {{placeholders}}
        subtitle: Optional subtitle with {{placeholders}}
        background: Background color or gradient
        **kwargs: Additional template options
    
    Returns:
        New OGTemplate
    
    Example:
        template = create_template(
            title="{{product_name}}",
            subtitle="Only {{price}}!",
            background="gradient:green",
        )
    """
    return OGTemplate(
        title=title,
        subtitle=subtitle,
        background=background,
        **kwargs,
    )


def get_gradient(name: str) -> str:
    """
    Get a gradient CSS by name.
    
    Args:
        name: Gradient name (e.g., "blue", "sunset")
    
    Returns:
        Gradient CSS string
    
    Example:
        gradient = get_gradient("blue")
        # "linear-gradient(135deg, #3b82f6, #1d4ed8)"
    """
    return GRADIENTS.get(name, GRADIENTS["slate"])


def list_gradients() -> List[str]:
    """
    List all available gradient names.
    
    Returns:
        List of gradient names
    """
    return list(GRADIENTS.keys())

