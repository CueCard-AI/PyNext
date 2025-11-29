"""
PWA Manifest Generation.

Generate manifest.json for Progressive Web Apps.

Example:
    from pynext import PWAManifest
    
    manifest = PWAManifest(
        name="My App",
        short_name="App",
        theme_color="#3b82f6",
    )
    
    # Generate manifest.json content
    json_content = manifest.to_json()

Why This Matters:
    The manifest.json file tells browsers how to display your app
    when installed as a PWA:
    - App name and icons
    - Theme colors
    - Start URL
    - Display mode (fullscreen, standalone, etc.)
    - Shortcuts for quick actions
    
    PyNext generates this automatically from your config.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


# ============================================
# Manifest Icon
# ============================================

@dataclass
class ManifestIcon:
    """
    Icon entry for manifest.json.
    
    Attributes:
        src: Icon source path
        sizes: Size string like "192x192" or "any"
        type: MIME type
        purpose: Icon purpose (any/maskable/monochrome)
    
    Example:
        icon = ManifestIcon("icon-192.png", sizes="192x192")
        icon = ManifestIcon("icon-512.png", sizes="512x512", purpose="maskable")
    """
    src: str
    sizes: str = "any"
    type: str = "image/png"
    purpose: str = "any"
    
    def __post_init__(self):
        """Validate and normalize values."""
        # Ensure src starts with /
        if not self.src.startswith("/"):
            self.src = "/" + self.src
        
        # Validate purpose
        valid_purposes = ["any", "maskable", "monochrome"]
        if self.purpose not in valid_purposes:
            raise ValueError(f"purpose must be one of {valid_purposes}, got: {self.purpose}")
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert to manifest icon dict.
        
        Returns:
            Dict for manifest icons array
        """
        result = {
            "src": self.src,
            "sizes": self.sizes,
            "type": self.type,
        }
        
        if self.purpose != "any":
            result["purpose"] = self.purpose
        
        return result


# ============================================
# Shortcut
# ============================================

@dataclass
class Shortcut:
    """
    App shortcut for manifest.
    
    Shortcuts appear in the app's context menu when installed.
    
    Attributes:
        name: Shortcut display name
        url: URL to navigate to
        description: Optional description
        icon: Optional icon path
    
    Example:
        shortcut = Shortcut("New Task", "/tasks/new")
        shortcut = Shortcut("Search", "/search", icon="icon-search.png")
    """
    name: str
    url: str
    description: Optional[str] = None
    icon: Optional[str] = None
    
    def __post_init__(self):
        """Validate shortcut."""
        if not self.name:
            raise ValueError("Shortcut name is required")
        
        if not self.url:
            raise ValueError("Shortcut url is required")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to manifest shortcut dict.
        
        Returns:
            Dict for manifest shortcuts array
        """
        result = {
            "name": self.name,
            "url": self.url,
        }
        
        if self.description:
            result["description"] = self.description
        
        if self.icon:
            icon_src = self.icon if self.icon.startswith("/") else "/" + self.icon
            result["icons"] = [{"src": icon_src, "sizes": "96x96"}]
        
        return result


# ============================================
# PWA Manifest
# ============================================

@dataclass
class PWAManifest:
    """
    Complete PWA manifest configuration.
    
    Generates a valid manifest.json for Progressive Web Apps.
    
    Attributes:
        name: Full app name
        short_name: Short name (max 12 chars, auto-generated if not provided)
        description: App description
        start_url: URL to open when app launches
        scope: Navigation scope
        display: Display mode (fullscreen/standalone/minimal-ui/browser)
        orientation: Screen orientation (any/portrait/landscape)
        theme_color: Browser chrome color
        background_color: Splash screen background
        icons: List of ManifestIcon
        shortcuts: List of Shortcut
        categories: App store categories
        lang: Language code
        dir: Text direction (ltr/rtl)
    
    Example:
        manifest = PWAManifest(
            name="My Awesome App",
            theme_color="#3b82f6",
            shortcuts=[
                Shortcut("New", "/new"),
            ],
        )
    """
    name: str
    short_name: Optional[str] = None
    description: Optional[str] = None
    start_url: str = "/"
    scope: str = "/"
    display: str = "standalone"
    orientation: str = "any"
    theme_color: Optional[str] = None
    background_color: str = "#ffffff"
    icons: List[ManifestIcon] = field(default_factory=list)
    shortcuts: List[Shortcut] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    lang: str = "en"
    dir: str = "ltr"
    
    # Additional optional fields
    id: Optional[str] = None
    prefer_related_applications: bool = False
    related_applications: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and set defaults."""
        if not self.name:
            raise ValueError("PWAManifest name is required")
        
        # Auto-generate short_name if not provided
        if not self.short_name:
            self.short_name = self.name[:12]
        
        # Validate display mode
        valid_displays = ["fullscreen", "standalone", "minimal-ui", "browser"]
        if self.display not in valid_displays:
            raise ValueError(f"display must be one of {valid_displays}, got: {self.display}")
        
        # Validate orientation
        valid_orientations = ["any", "natural", "portrait", "portrait-primary", 
                             "portrait-secondary", "landscape", "landscape-primary",
                             "landscape-secondary"]
        if self.orientation not in valid_orientations:
            raise ValueError(f"orientation must be one of {valid_orientations}, got: {self.orientation}")
        
        # Validate text direction
        if self.dir not in ["ltr", "rtl", "auto"]:
            raise ValueError(f"dir must be ltr, rtl, or auto, got: {self.dir}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to manifest.json dict.
        
        Returns:
            Dict ready for JSON serialization
        """
        manifest = {
            "name": self.name,
            "short_name": self.short_name,
            "start_url": self.start_url,
            "scope": self.scope,
            "display": self.display,
            "background_color": self.background_color,
            "lang": self.lang,
            "dir": self.dir,
        }
        
        # Optional fields
        if self.description:
            manifest["description"] = self.description
        
        if self.theme_color:
            manifest["theme_color"] = self.theme_color
        
        if self.orientation != "any":
            manifest["orientation"] = self.orientation
        
        if self.icons:
            manifest["icons"] = [icon.to_dict() for icon in self.icons]
        
        if self.shortcuts:
            manifest["shortcuts"] = [s.to_dict() for s in self.shortcuts]
        
        if self.categories:
            manifest["categories"] = self.categories
        
        if self.id:
            manifest["id"] = self.id
        
        if self.prefer_related_applications:
            manifest["prefer_related_applications"] = True
            if self.related_applications:
                manifest["related_applications"] = self.related_applications
        
        return manifest
    
    def to_json(self, indent: int = 2) -> str:
        """
        Generate manifest.json content.
        
        Args:
            indent: JSON indentation level
        
        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    def to_link_tag(self) -> str:
        """
        Generate <link rel="manifest"> tag.
        
        Returns:
            HTML link tag
        """
        return '<link rel="manifest" href="/manifest.json">'
    
    def to_meta_tags(self) -> str:
        """
        Generate related meta tags for HTML head.
        
        Returns:
            HTML meta tags string
        """
        tags = []
        
        # Theme color
        if self.theme_color:
            tags.append(f'<meta name="theme-color" content="{self.theme_color}">')
        
        # Apple-specific meta tags
        tags.append('<meta name="apple-mobile-web-app-capable" content="yes">')
        
        if self.display == "fullscreen":
            tags.append('<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">')
        else:
            tags.append('<meta name="apple-mobile-web-app-status-bar-style" content="default">')
        
        if self.short_name:
            tags.append(f'<meta name="apple-mobile-web-app-title" content="{self.short_name}">')
        
        # Microsoft tiles
        if self.theme_color:
            tags.append(f'<meta name="msapplication-TileColor" content="{self.theme_color}">')
        
        return "\n".join(tags)
    
    def write_to_file(self, path: Path) -> Path:
        """
        Write manifest.json to file.
        
        Args:
            path: Output path
        
        Returns:
            Path to written file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        return path


# ============================================
# Manifest Generator
# ============================================

class ManifestGenerator:
    """
    Generate manifest from config and auto-detected icons.
    
    Merges explicit configuration with icons detected from public/.
    
    Example:
        from pynext.pwa import ManifestGenerator, PWAManifest
        from pynext.pwa.icons import IconDetector
        
        config = PWAManifest(name="My App")
        icons = IconDetector(Path("public")).detect()
        
        generator = ManifestGenerator(config, icons)
        manifest_json = generator.generate()
    """
    
    def __init__(self, config: PWAManifest, icons: "AppIcons"):
        """
        Initialize generator.
        
        Args:
            config: PWAManifest configuration
            icons: AppIcons from detection or config
        """
        self.config = config
        self.icons = icons
    
    def generate(self) -> str:
        """
        Generate complete manifest.json.
        
        Merges config icons with detected icons.
        
        Returns:
            JSON string
        """
        # Build manifest dict from config
        manifest = self.config.to_dict()
        
        # Merge icons if config has none
        if not self.config.icons and self.icons.icons:
            manifest["icons"] = self.icons.get_manifest_icons()
        
        return json.dumps(manifest, indent=2)
    
    def get_all_head_tags(self) -> str:
        """
        Get all head tags for PWA.
        
        Combines icon tags, manifest link, and meta tags.
        
        Returns:
            Complete HTML head tags
        """
        tags = []
        
        # Icon tags
        tags.append(self.icons.to_head_tags())
        
        # Manifest link
        tags.append(self.config.to_link_tag())
        
        # Meta tags
        tags.append(self.config.to_meta_tags())
        
        return "\n".join(filter(None, tags))


# ============================================
# Convenience Functions
# ============================================

def pwa_minimal(
    name: str,
    theme_color: Optional[str] = None,
) -> PWAManifest:
    """
    Create minimal PWA manifest with sensible defaults.
    
    Args:
        name: App name
        theme_color: Optional theme color
    
    Returns:
        PWAManifest with minimal config
    
    Example:
        manifest = pwa_minimal("My App")
        manifest = pwa_minimal("My App", theme_color="#3b82f6")
    """
    return PWAManifest(
        name=name,
        theme_color=theme_color,
    )


def pwa_full(
    name: str,
    short_name: Optional[str] = None,
    description: Optional[str] = None,
    theme_color: str = "#3b82f6",
    background_color: str = "#ffffff",
    display: str = "standalone",
    icons: Optional[List[ManifestIcon]] = None,
    shortcuts: Optional[List[Shortcut]] = None,
    categories: Optional[List[str]] = None,
) -> PWAManifest:
    """
    Create full-featured PWA manifest.
    
    Args:
        name: Full app name
        short_name: Short name for home screen
        description: App description
        theme_color: Browser chrome color
        background_color: Splash screen background
        display: Display mode
        icons: List of ManifestIcon
        shortcuts: List of Shortcut
        categories: App categories
    
    Returns:
        PWAManifest with full config
    
    Example:
        manifest = pwa_full(
            name="Task Manager",
            short_name="Tasks",
            theme_color="#10b981",
            shortcuts=[
                Shortcut("New Task", "/new"),
            ],
        )
    """
    return PWAManifest(
        name=name,
        short_name=short_name,
        description=description,
        theme_color=theme_color,
        background_color=background_color,
        display=display,
        icons=icons or [],
        shortcuts=shortcuts or [],
        categories=categories or [],
    )


def generate_default_icons() -> List[ManifestIcon]:
    """
    Generate default icon list for PWA.
    
    Returns:
        List of ManifestIcon with common sizes
    """
    return [
        ManifestIcon("icon-192.png", sizes="192x192"),
        ManifestIcon("icon-512.png", sizes="512x512"),
        ManifestIcon("icon-512.png", sizes="512x512", purpose="maskable"),
    ]


# Import AppIcons for type hints
from pynext.pwa.icons import AppIcons

