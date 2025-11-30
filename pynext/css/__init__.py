"""
PyNext CSS Modules - Build-Time Scoped CSS

Zero-JS CSS scoping with build-time class name hashing.
Eliminates style conflicts without runtime overhead.

Usage:
    # Inline CSS (scoped automatically)
    from pynext import css
    
    styles = css('''
    .button { padding: 8px 16px; }
    .primary { background: blue; }
    ''')
    
    button(class_=styles.button)["Click"]
    
    # External CSS Module
    from pynext import css_module
    
    styles = css_module("./Button.module.css")
    button(class_=styles.button)["Click"]

Features:
- Build-time scoping (zero runtime JS)
- Unique hash per component
- CSS extraction and bundling
- Works with Tailwind
"""

from .module import css, css_module, CSSModule
from .scoper import CSSScoper, generate_hash
from .extractor import CSSExtractor, extract_all_css
from .bundler import CSSBundler, bundle_css

__all__ = [
    # Main API
    "css",
    "css_module",
    "CSSModule",
    # Scoping
    "CSSScoper",
    "generate_hash",
    # Extraction
    "CSSExtractor",
    "extract_all_css",
    # Bundling
    "CSSBundler",
    "bundle_css",
]

