"""
PyNext Build System

Provides build-time optimizations:
- JS minification
- Console statement removal
- Dead code elimination
"""

from pynext.build.minify import minify_js, minify_runtime
from pynext.build.bundle import bundle_runtime, get_required_modules

__all__ = [
    'minify_js',
    'minify_runtime',
    'bundle_runtime',
    'get_required_modules',
]

