"""
App Icons Detection and Configuration.

Auto-detect icons from public/ or configure explicitly.

Example:
    # Zero config - just drop files in public/
    public/
    ├── favicon.ico
    ├── icon-192.png
    ├── icon-512.png
    └── apple-icon.png
    
    # Or explicit config:
    from pynext import AppIcons, Icon
    
    icons = AppIcons(
        favicon="favicon.ico",
        icons=[
            Icon("icon-192.png", size=192),
            Icon("icon-512.png", size=512, purpose="maskable"),
        ],
        apple_icon="apple-icon.png",
    )

Why This Matters:
    Modern web apps need multiple icon sizes for different contexts:
    - Favicon for browser tabs
    - App icons for PWA install
    - Apple touch icons for iOS
    - Open Graph images for social sharing
    
    PyNext auto-detects these from your public/ folder.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import re
import mimetypes


# ============================================
# Icon Dataclass
# ============================================

@dataclass
class Icon:
    """
    A single icon definition.
    
    Attributes:
        path: Path to icon file (relative to public/)
        size: Icon size in pixels (auto-detected from filename if None)
        type: MIME type (auto-detected from extension if None)
        purpose: Icon purpose for manifest (any/maskable/monochrome)
    
    Example:
        icon = Icon("icon-192.png", size=192)
        icon = Icon("icon-512.png", size=512, purpose="maskable")
    """
    path: str
    size: Optional[int] = None
    type: Optional[str] = None
    purpose: str = "any"
    
    def __post_init__(self):
        """Auto-detect size and type if not provided."""
        # Auto-detect size from filename (e.g., icon-192.png -> 192)
        if self.size is None:
            self.size = self._detect_size_from_filename()
        
        # Auto-detect MIME type from extension
        if self.type is None:
            self.type = self._detect_mime_type()
        
        # Validate purpose
        valid_purposes = ["any", "maskable", "monochrome"]
        if self.purpose not in valid_purposes:
            raise ValueError(f"purpose must be one of {valid_purposes}, got: {self.purpose}")
    
    def _detect_size_from_filename(self) -> Optional[int]:
        """Extract size from filename like icon-192.png."""
        filename = Path(self.path).stem
        
        # Pattern: icon-192, icon_512, apple-icon-180
        match = re.search(r'[-_](\d+)(?:x\d+)?$', filename)
        if match:
            return int(match.group(1))
        
        return None
    
    def _detect_mime_type(self) -> str:
        """Detect MIME type from file extension."""
        ext = Path(self.path).suffix.lower()
        
        type_map = {
            ".ico": "image/x-icon",
            ".png": "image/png",
            ".svg": "image/svg+xml",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        
        return type_map.get(ext, "image/png")
    
    def to_link_tag(self, base_path: str = "") -> str:
        """
        Generate <link> tag for HTML head.
        
        Args:
            base_path: Base path prefix for href
        
        Returns:
            HTML link tag string
        """
        href = f"{base_path}/{self.path}".replace("//", "/")
        if not href.startswith("/"):
            href = "/" + href
        
        attrs = [f'rel="icon"']
        
        if self.type:
            attrs.append(f'type="{self.type}"')
        
        if self.size:
            attrs.append(f'sizes="{self.size}x{self.size}"')
        
        attrs.append(f'href="{href}"')
        
        return f'<link {" ".join(attrs)}>'
    
    def to_manifest_icon(self) -> Dict:
        """
        Convert to manifest.json icon entry.
        
        Returns:
            Dict for manifest icons array
        """
        entry = {
            "src": f"/{self.path}".replace("//", "/"),
            "type": self.type or "image/png",
        }
        
        if self.size:
            entry["sizes"] = f"{self.size}x{self.size}"
        else:
            entry["sizes"] = "any"
        
        if self.purpose != "any":
            entry["purpose"] = self.purpose
        
        return entry


# ============================================
# AppIcons Configuration
# ============================================

@dataclass
class AppIcons:
    """
    Complete app icon configuration.
    
    Attributes:
        favicon: Path to favicon file
        icons: List of app icons (different sizes)
        apple_icon: Path to Apple touch icon
        og_image: Path to Open Graph image
    
    Example:
        icons = AppIcons(
            favicon="favicon.ico",
            icons=[
                Icon("icon-192.png", size=192),
                Icon("icon-512.png", size=512),
            ],
            apple_icon="apple-icon.png",
            og_image="og-image.png",
        )
    """
    favicon: Optional[str] = None
    icons: List[Icon] = field(default_factory=list)
    apple_icon: Optional[str] = None
    og_image: Optional[str] = None
    
    # Internal tracking
    _base_url: str = field(default="", repr=False)
    
    def to_head_tags(self, base_url: str = "") -> str:
        """
        Generate all icon-related HTML head tags.
        
        Args:
            base_url: Base URL for absolute URLs (for og:image)
        
        Returns:
            Complete HTML string with all icon tags
        """
        tags = []
        
        # Favicon
        if self.favicon:
            favicon_path = f"/{self.favicon}".replace("//", "/")
            mime_type = Icon(self.favicon).type
            
            if self.favicon.endswith(".ico"):
                tags.append(f'<link rel="icon" href="{favicon_path}">')
            else:
                tags.append(f'<link rel="icon" type="{mime_type}" href="{favicon_path}">')
        
        # App icons
        for icon in self.icons:
            tags.append(icon.to_link_tag())
        
        # Apple touch icon
        if self.apple_icon:
            apple_path = f"/{self.apple_icon}".replace("//", "/")
            tags.append(f'<link rel="apple-touch-icon" href="{apple_path}">')
        
        # Open Graph image
        if self.og_image:
            og_url = f"{base_url}/{self.og_image}".replace("//", "/")
            if base_url:
                og_url = f"{base_url.rstrip('/')}/{self.og_image}"
            tags.append(f'<meta property="og:image" content="{og_url}">')
        
        return "\n".join(tags)
    
    def get_manifest_icons(self) -> List[Dict]:
        """
        Get icons formatted for manifest.json.
        
        Returns:
            List of icon dicts for manifest
        """
        return [icon.to_manifest_icon() for icon in self.icons]
    
    def merge_with(self, other: "AppIcons") -> "AppIcons":
        """
        Merge with another AppIcons config (other takes precedence).
        
        Args:
            other: AppIcons to merge with
        
        Returns:
            New merged AppIcons
        """
        return AppIcons(
            favicon=other.favicon or self.favicon,
            icons=other.icons if other.icons else self.icons,
            apple_icon=other.apple_icon or self.apple_icon,
            og_image=other.og_image or self.og_image,
        )


# ============================================
# Icon Detector
# ============================================

class IconDetector:
    """
    Auto-detect icons from public/ directory.
    
    Scans the public folder for common icon file patterns
    and creates an AppIcons configuration.
    
    Example:
        detector = IconDetector(Path("public"))
        icons = detector.detect()
        print(icons.to_head_tags())
    
    Detected patterns:
        - favicon.ico, favicon.png, favicon.svg
        - icon.png, icon-192.png, icon-512.png
        - apple-icon.png, apple-touch-icon.png
        - og-image.png, og.png, opengraph.png
    """
    
    # File patterns to detect
    FAVICON_PATTERNS = ["favicon.ico", "favicon.png", "favicon.svg"]
    ICON_PATTERNS = ["icon.png", "icon.svg"]
    ICON_SIZE_PATTERN = re.compile(r'^icon[-_](\d+)(?:x\d+)?\.(?:png|svg|webp)$', re.IGNORECASE)
    APPLE_PATTERNS = ["apple-icon.png", "apple-touch-icon.png", "apple-icon-180.png"]
    OG_PATTERNS = ["og-image.png", "og.png", "opengraph.png", "og-image.jpg"]
    
    def __init__(self, public_dir: Path):
        """
        Initialize detector.
        
        Args:
            public_dir: Path to public/ directory
        """
        self.public_dir = Path(public_dir)
    
    def detect(self) -> AppIcons:
        """
        Scan public/ and detect all icons.
        
        Returns:
            AppIcons configuration with detected icons
        """
        if not self.public_dir.exists():
            return AppIcons()
        
        # Get all files in public/
        files = {f.name: f for f in self.public_dir.iterdir() if f.is_file()}
        
        # Detect favicon
        favicon = self._detect_first_match(files, self.FAVICON_PATTERNS)
        
        # Detect app icons
        icons = self._detect_icons(files)
        
        # Detect Apple icon
        apple_icon = self._detect_first_match(files, self.APPLE_PATTERNS)
        
        # Detect OG image
        og_image = self._detect_first_match(files, self.OG_PATTERNS)
        
        return AppIcons(
            favicon=favicon,
            icons=icons,
            apple_icon=apple_icon,
            og_image=og_image,
        )
    
    def _detect_first_match(self, files: Dict[str, Path], patterns: List[str]) -> Optional[str]:
        """Find first matching file from patterns."""
        for pattern in patterns:
            if pattern in files:
                return pattern
        return None
    
    def _detect_icons(self, files: Dict[str, Path]) -> List[Icon]:
        """Detect all app icons with sizes."""
        icons = []
        
        # Check for base icon (no size)
        for pattern in self.ICON_PATTERNS:
            if pattern in files:
                icons.append(Icon(pattern))
        
        # Check for sized icons (icon-192.png, icon-512.png, etc.)
        for filename in files:
            match = self.ICON_SIZE_PATTERN.match(filename)
            if match:
                size = int(match.group(1))
                icons.append(Icon(filename, size=size))
        
        # Sort by size
        icons.sort(key=lambda i: i.size or 0)
        
        return icons
    
    def get_missing_icons(self) -> List[str]:
        """
        Get list of recommended icons that are missing.
        
        Returns:
            List of missing icon descriptions
        """
        icons = self.detect()
        missing = []
        
        if not icons.favicon:
            missing.append("favicon.ico - Browser tab icon")
        
        sizes = {i.size for i in icons.icons if i.size}
        
        if 192 not in sizes:
            missing.append("icon-192.png - PWA icon (required)")
        
        if 512 not in sizes:
            missing.append("icon-512.png - PWA splash screen (required)")
        
        if not icons.apple_icon:
            missing.append("apple-icon.png - iOS home screen icon")
        
        if not icons.og_image:
            missing.append("og-image.png - Social media preview")
        
        return missing
    
    def validate(self) -> List[str]:
        """
        Validate detected icons and return warnings.
        
        Returns:
            List of warning messages
        """
        warnings = []
        icons = self.detect()
        
        # Check for PWA requirements
        sizes = {i.size for i in icons.icons if i.size}
        
        if 192 not in sizes and 512 not in sizes:
            warnings.append("No PWA icons found. Add icon-192.png and icon-512.png for installability.")
        elif 192 not in sizes:
            warnings.append("Missing 192x192 icon. Add icon-192.png for PWA.")
        elif 512 not in sizes:
            warnings.append("Missing 512x512 icon. Add icon-512.png for PWA splash screen.")
        
        # Check for maskable icon
        has_maskable = any(i.purpose == "maskable" for i in icons.icons)
        if not has_maskable and sizes:
            warnings.append("No maskable icon found. Consider adding purpose='maskable' for adaptive icons.")
        
        # Check favicon
        if not icons.favicon:
            warnings.append("No favicon found. Add favicon.ico for browser tabs.")
        
        return warnings


# ============================================
# Convenience Functions
# ============================================

def detect_icons(public_dir: str = "public") -> AppIcons:
    """
    Convenience function to detect icons.
    
    Args:
        public_dir: Path to public directory
    
    Returns:
        Detected AppIcons configuration
    
    Example:
        icons = detect_icons()
        print(icons.to_head_tags())
    """
    return IconDetector(Path(public_dir)).detect()


def create_icons(
    favicon: Optional[str] = None,
    icon_192: Optional[str] = None,
    icon_512: Optional[str] = None,
    apple_icon: Optional[str] = None,
    og_image: Optional[str] = None,
    maskable_512: bool = False,
) -> AppIcons:
    """
    Create AppIcons with common configuration.
    
    Args:
        favicon: Favicon path
        icon_192: 192x192 icon path
        icon_512: 512x512 icon path
        apple_icon: Apple touch icon path
        og_image: Open Graph image path
        maskable_512: Make 512 icon maskable
    
    Returns:
        AppIcons configuration
    
    Example:
        icons = create_icons(
            favicon="favicon.ico",
            icon_192="icon-192.png",
            icon_512="icon-512.png",
            maskable_512=True,
        )
    """
    icons = []
    
    if icon_192:
        icons.append(Icon(icon_192, size=192))
    
    if icon_512:
        purpose = "maskable" if maskable_512 else "any"
        icons.append(Icon(icon_512, size=512, purpose=purpose))
    
    return AppIcons(
        favicon=favicon,
        icons=icons,
        apple_icon=apple_icon,
        og_image=og_image,
    )

