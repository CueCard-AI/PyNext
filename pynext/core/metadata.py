"""
Metadata API for PyNext pages.

Provides a structured way to define page metadata for SEO,
Open Graph, Twitter cards, and more.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union
import json


@dataclass
class OpenGraph:
    """Open Graph metadata for social sharing."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    site_name: Optional[str] = None
    type: str = "website"  # website, article, profile, etc.
    image: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    image_alt: Optional[str] = None
    locale: Optional[str] = None
    
    def to_meta_tags(self) -> list[dict[str, str]]:
        """Convert to list of meta tag dicts."""
        tags = []
        
        if self.title:
            tags.append({"property": "og:title", "content": self.title})
        if self.description:
            tags.append({"property": "og:description", "content": self.description})
        if self.url:
            tags.append({"property": "og:url", "content": self.url})
        if self.site_name:
            tags.append({"property": "og:site_name", "content": self.site_name})
        if self.type:
            tags.append({"property": "og:type", "content": self.type})
        if self.image:
            tags.append({"property": "og:image", "content": self.image})
            if self.image_width:
                tags.append({"property": "og:image:width", "content": str(self.image_width)})
            if self.image_height:
                tags.append({"property": "og:image:height", "content": str(self.image_height)})
            if self.image_alt:
                tags.append({"property": "og:image:alt", "content": self.image_alt})
        if self.locale:
            tags.append({"property": "og:locale", "content": self.locale})
        
        return tags


@dataclass
class Twitter:
    """Twitter Card metadata."""
    
    card: str = "summary_large_image"  # summary, summary_large_image, app, player
    site: Optional[str] = None  # @username
    creator: Optional[str] = None  # @username
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    image_alt: Optional[str] = None
    
    def to_meta_tags(self) -> list[dict[str, str]]:
        """Convert to list of meta tag dicts."""
        tags = [{"name": "twitter:card", "content": self.card}]
        
        if self.site:
            tags.append({"name": "twitter:site", "content": self.site})
        if self.creator:
            tags.append({"name": "twitter:creator", "content": self.creator})
        if self.title:
            tags.append({"name": "twitter:title", "content": self.title})
        if self.description:
            tags.append({"name": "twitter:description", "content": self.description})
        if self.image:
            tags.append({"name": "twitter:image", "content": self.image})
        if self.image_alt:
            tags.append({"name": "twitter:image:alt", "content": self.image_alt})
        
        return tags


@dataclass
class Icons:
    """Favicon and icon metadata."""
    
    icon: Optional[str] = None  # /favicon.ico
    shortcut: Optional[str] = None
    apple: Optional[str] = None  # Apple touch icon
    other: list[dict[str, str]] = field(default_factory=list)
    
    def to_link_tags(self) -> list[dict[str, str]]:
        """Convert to list of link tag dicts."""
        tags = []
        
        if self.icon:
            tags.append({"rel": "icon", "href": self.icon})
        if self.shortcut:
            tags.append({"rel": "shortcut icon", "href": self.shortcut})
        if self.apple:
            tags.append({"rel": "apple-touch-icon", "href": self.apple})
        
        tags.extend(self.other)
        
        return tags


@dataclass
class Alternates:
    """Alternate versions of the page (canonical, languages)."""
    
    canonical: Optional[str] = None
    languages: dict[str, str] = field(default_factory=dict)  # {"en": "/en/page", "fr": "/fr/page"}
    
    def to_link_tags(self) -> list[dict[str, str]]:
        """Convert to list of link tag dicts."""
        tags = []
        
        if self.canonical:
            tags.append({"rel": "canonical", "href": self.canonical})
        
        for lang, href in self.languages.items():
            tags.append({"rel": "alternate", "hreflang": lang, "href": href})
        
        return tags


@dataclass
class Metadata:
    """
    Complete page metadata.
    
    Usage:
        @page(
            metadata=Metadata(
                title="Dashboard | MyApp",
                description="View your dashboard",
                openGraph=OpenGraph(
                    title="Dashboard",
                    image="/og-dashboard.png"
                ),
                robots="noindex, nofollow"
            )
        )
        def dashboard():
            return div()[...]
    
    Or with a dict for openGraph/twitter:
        @page(
            metadata=Metadata(
                title="Dashboard",
                openGraph={"title": "Dashboard", "image": "/og.png"}
            )
        )
    """
    
    # Basic metadata
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[list[str]] = None
    authors: Optional[list[str]] = None
    
    # Robots directives
    robots: Optional[str] = None  # "index, follow", "noindex", etc.
    
    # Open Graph
    openGraph: Optional[Union[OpenGraph, dict]] = None
    
    # Twitter Cards
    twitter: Optional[Union[Twitter, dict]] = None
    
    # Icons
    icons: Optional[Union[Icons, dict]] = None
    
    # Alternates (canonical, languages)
    alternates: Optional[Union[Alternates, dict]] = None
    
    # Manifest
    manifest: Optional[str] = None
    
    # Theme color
    themeColor: Optional[str] = None
    
    # Viewport (usually set globally)
    viewport: Optional[str] = None
    
    # Additional custom meta tags
    other: dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Convert dicts to dataclass instances."""
        if isinstance(self.openGraph, dict):
            self.openGraph = OpenGraph(**self.openGraph)
        if isinstance(self.twitter, dict):
            self.twitter = Twitter(**self.twitter)
        if isinstance(self.icons, dict):
            self.icons = Icons(**self.icons)
        if isinstance(self.alternates, dict):
            self.alternates = Alternates(**self.alternates)
    
    def to_meta_tags(self) -> list[dict[str, str]]:
        """Convert all metadata to list of meta tag dicts."""
        tags = []
        
        # Basic meta tags
        if self.description:
            tags.append({"name": "description", "content": self.description})
        if self.keywords:
            tags.append({"name": "keywords", "content": ", ".join(self.keywords)})
        if self.authors:
            for author in self.authors:
                tags.append({"name": "author", "content": author})
        if self.robots:
            tags.append({"name": "robots", "content": self.robots})
        if self.themeColor:
            tags.append({"name": "theme-color", "content": self.themeColor})
        if self.viewport:
            tags.append({"name": "viewport", "content": self.viewport})
        
        # Open Graph
        if self.openGraph:
            tags.extend(self.openGraph.to_meta_tags())
        
        # Twitter
        if self.twitter:
            tags.extend(self.twitter.to_meta_tags())
        
        # Other custom tags
        for name, content in self.other.items():
            tags.append({"name": name, "content": content})
        
        return tags
    
    def to_link_tags(self) -> list[dict[str, str]]:
        """Convert to list of link tag dicts."""
        tags = []
        
        if self.icons:
            tags.extend(self.icons.to_link_tags())
        if self.alternates:
            tags.extend(self.alternates.to_link_tags())
        if self.manifest:
            tags.append({"rel": "manifest", "href": self.manifest})
        
        return tags
    
    def render_head(self) -> str:
        """Render all metadata as HTML for the <head> section."""
        parts = []
        
        # Meta tags
        for tag in self.to_meta_tags():
            attrs = " ".join(f'{k}="{v}"' for k, v in tag.items())
            parts.append(f"<meta {attrs} />")
        
        # Link tags
        for tag in self.to_link_tags():
            attrs = " ".join(f'{k}="{v}"' for k, v in tag.items())
            parts.append(f"<link {attrs} />")
        
        return "\n    ".join(parts)
    
    def merge(self, other: "Metadata") -> "Metadata":
        """
        Merge another Metadata instance, with 'other' taking precedence.
        
        Useful for combining layout metadata with page metadata.
        """
        merged_data = {}
        
        # Simple fields - other takes precedence if set
        for field_name in ["title", "description", "robots", "manifest", "themeColor", "viewport"]:
            other_val = getattr(other, field_name)
            self_val = getattr(self, field_name)
            merged_data[field_name] = other_val if other_val is not None else self_val
        
        # List fields - concatenate
        if other.keywords or self.keywords:
            merged_data["keywords"] = list(set((self.keywords or []) + (other.keywords or [])))
        if other.authors or self.authors:
            merged_data["authors"] = list(set((self.authors or []) + (other.authors or [])))
        
        # Complex fields - other takes precedence if set
        merged_data["openGraph"] = other.openGraph if other.openGraph else self.openGraph
        merged_data["twitter"] = other.twitter if other.twitter else self.twitter
        merged_data["icons"] = other.icons if other.icons else self.icons
        merged_data["alternates"] = other.alternates if other.alternates else self.alternates
        
        # Other dict - merge
        merged_other = {**self.other, **other.other}
        merged_data["other"] = merged_other
        
        return Metadata(**merged_data)


# Type alias for dynamic metadata generator
MetadataGenerator = Callable[[dict], Metadata]


async def resolve_metadata(
    metadata: Optional[Union[Metadata, MetadataGenerator, dict]],
    params: dict
) -> Optional[Metadata]:
    """
    Resolve metadata, handling static, dynamic, and dict forms.
    
    Args:
        metadata: Static Metadata, async generator function, or dict
        params: Route parameters for dynamic metadata
    
    Returns:
        Resolved Metadata instance or None
    """
    if metadata is None:
        return None
    
    if isinstance(metadata, Metadata):
        return metadata
    
    if isinstance(metadata, dict):
        return Metadata(**metadata)
    
    if callable(metadata):
        # Dynamic metadata generator
        import asyncio
        import inspect
        
        result = metadata(params)
        
        if inspect.isawaitable(result):
            result = await result
        
        if isinstance(result, Metadata):
            return result
        if isinstance(result, dict):
            return Metadata(**result)
    
    return None


def generate_metadata(fn: Callable[[dict], Union[Metadata, dict]]) -> MetadataGenerator:
    """
    Decorator to mark a function as a metadata generator.
    
    Usage:
        @generate_metadata
        async def get_metadata(params):
            user = await db.get_user(params["id"])
            return Metadata(
                title=f"{user.name} | Profile",
                description=user.bio
            )
        
        @page(metadata=get_metadata)
        def user_profile():
            ...
    """
    return fn

