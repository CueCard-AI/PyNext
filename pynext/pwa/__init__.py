"""
PyNext PWA Module.

Provides app icons auto-detection and PWA manifest generation.

Example:
    from pynext import AppIcons, PWAManifest
    
    # Zero config - just drop files in public/
    # Or explicit config:
    manifest = PWAManifest(
        name="My App",
        theme_color="#3b82f6",
    )
"""

from pynext.pwa.icons import (
    Icon,
    AppIcons,
    IconDetector,
)

from pynext.pwa.manifest import (
    ManifestIcon,
    Shortcut,
    PWAManifest,
    ManifestGenerator,
    pwa_minimal,
    pwa_full,
)

__all__ = [
    # Icons
    "Icon",
    "AppIcons",
    "IconDetector",
    # Manifest
    "ManifestIcon",
    "Shortcut",
    "PWAManifest",
    "ManifestGenerator",
    "pwa_minimal",
    "pwa_full",
]

