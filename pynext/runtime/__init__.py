"""Runtime module containing JS assets for client-side reactivity.

PyNext runtime supports two modes:
- Development: Full, unminified JS with comments and debug features
- Production: Slim, minified JS for maximum performance

Set PYNEXT_ENV=production or DEBUG=false for production mode.
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional

# Runtime directory paths
_RUNTIME_DIR = Path(__file__).parent
_MIN_DIR = _RUNTIME_DIR / "min"


def is_production() -> bool:
    """Check if running in production mode.
    
    Production mode is enabled when:
    - PYNEXT_ENV=production
    - NODE_ENV=production
    - DEBUG=false or DEBUG=0
    """
    pynext_env = os.environ.get("PYNEXT_ENV", "").lower()
    node_env = os.environ.get("NODE_ENV", "").lower()
    debug = os.environ.get("DEBUG", "true").lower()
    
    if pynext_env == "production" or node_env == "production":
        return True
    if debug in ("false", "0", "no"):
        return True
    return False


def _get_runtime_file(name: str, prefer_slim: bool = True) -> Path:
    """Get the path to a runtime file, preferring slim/minified in production.
    
    Resolution order in production:
    1. min/{name}.slim.js (smallest)
    2. {name}.slim.js (small)
    3. {name}.js (full)
    
    In development, always returns {name}.js
    """
    if is_production() and prefer_slim:
        # Try minified slim first
        min_slim = _MIN_DIR / f"{name}.slim.js"
        if min_slim.exists():
            return min_slim
        
        # Try unminified slim
        slim = _RUNTIME_DIR / f"{name}.slim.js"
        if slim.exists():
            return slim
    
    # Fall back to full version
    return _RUNTIME_DIR / f"{name}.js"


@lru_cache(maxsize=32)
def _read_cached(path: Path) -> str:
    """Read file content with caching."""
    return path.read_text()


def get_runtime_js(minified: Optional[bool] = None) -> str:
    """Get the signals.js runtime content.
    
    Args:
        minified: Override production detection. If None, uses is_production().
    """
    use_slim = minified if minified is not None else is_production()
    path = _get_runtime_file("signals", prefer_slim=use_slim)
    return _read_cached(path)


def get_runtime_path() -> Path:
    """Get the path to the signals.js runtime file."""
    return _get_runtime_file("signals")


def get_resource_js() -> str:
    """Get the resource.js runtime content."""
    path = _get_runtime_file("resource", prefer_slim=False)  # No slim version
    return _read_cached(path)


def get_resource_path() -> Path:
    """Get the path to the resource.js runtime file."""
    return _get_runtime_file("resource", prefer_slim=False)


def get_suspense_js() -> str:
    """Get the suspense.js runtime content."""
    path = _get_runtime_file("suspense", prefer_slim=False)  # No slim version
    return _read_cached(path)


def get_suspense_path() -> Path:
    """Get the path to the suspense.js runtime file."""
    return _get_runtime_file("suspense", prefer_slim=False)


def get_islands_js() -> str:
    """Get the islands.js runtime content."""
    path = _get_runtime_file("islands", prefer_slim=False)  # No slim version
    return _read_cached(path)


def get_islands_path() -> Path:
    """Get the path to the islands.js runtime file."""
    return _get_runtime_file("islands", prefer_slim=False)


def get_lazy_js() -> str:
    """Get the lazy.js runtime content."""
    path = _get_runtime_file("lazy", prefer_slim=False)  # No slim version
    return _read_cached(path)


def get_lazy_path() -> Path:
    """Get the path to the lazy.js runtime file."""
    return _get_runtime_file("lazy", prefer_slim=False)


def get_navigation_js() -> str:
    """Get the navigation.js runtime content."""
    path = _get_runtime_file("navigation", prefer_slim=False)  # No slim version
    return _read_cached(path)


def get_navigation_path() -> Path:
    """Get the path to the navigation.js runtime file."""
    return _get_runtime_file("navigation", prefer_slim=False)


def get_i18n_js() -> str:
    """Get the i18n.js runtime content."""
    path = _get_runtime_file("i18n", prefer_slim=False)  # No slim version
    return _read_cached(path)


def get_i18n_path() -> Path:
    """Get the path to the i18n.js runtime file."""
    return _get_runtime_file("i18n", prefer_slim=False)


# Slim file getters for optional features
def get_browser_js() -> str:
    """Get the browser.js runtime content (slim in production)."""
    path = _get_runtime_file("browser")
    return _read_cached(path)


def get_keyboard_js() -> str:
    """Get the keyboard.js runtime content (slim in production)."""
    path = _get_runtime_file("keyboard")
    return _read_cached(path)


def get_focus_js() -> str:
    """Get the focus.js runtime content (slim in production)."""
    path = _get_runtime_file("focus")
    return _read_cached(path)


def get_theme_js() -> str:
    """Get the theme.js runtime content (slim in production)."""
    path = _get_runtime_file("theme")
    return _read_cached(path)


def get_storage_js() -> str:
    """Get the storage.js runtime content (slim in production)."""
    path = _get_runtime_file("storage")
    return _read_cached(path)


def get_sse_js() -> str:
    """Get the sse.js runtime content (slim in production)."""
    path = _get_runtime_file("sse")
    return _read_cached(path)


def get_toast_js() -> str:
    """Get the toast.js runtime content (slim in production)."""
    path = _get_runtime_file("toast")
    return _read_cached(path)


def get_full_runtime_js(minified: Optional[bool] = None) -> str:
    """Get the complete runtime including all core modules.
    
    In production mode, uses slim/minified versions for smaller bundle.
    """
    use_slim = minified if minified is not None else is_production()
    
    # Core runtime (always included)
    parts = [get_runtime_js(minified=use_slim)]
    
    # Optional modules (only include full versions in dev)
    if not use_slim:
        parts.extend([
            get_resource_js(),
            get_suspense_js(),
            get_islands_js(),
            get_lazy_js(),
            get_navigation_js(),
            get_i18n_js(),
        ])
    
    return "\n\n".join(parts)


def get_runtime_size_info() -> dict:
    """Get information about runtime file sizes for debugging."""
    files = ["signals", "browser", "keyboard", "focus", "theme", "storage", "sse", "toast"]
    
    info = {
        "mode": "production" if is_production() else "development",
        "files": {}
    }
    
    for name in files:
        full_path = _RUNTIME_DIR / f"{name}.js"
        slim_path = _RUNTIME_DIR / f"{name}.slim.js"
        min_slim_path = _MIN_DIR / f"{name}.slim.js"
        
        file_info = {}
        
        if full_path.exists():
            file_info["full"] = full_path.stat().st_size
        if slim_path.exists():
            file_info["slim"] = slim_path.stat().st_size
        if min_slim_path.exists():
            file_info["min_slim"] = min_slim_path.stat().st_size
        
        # Which one would be used
        used_path = _get_runtime_file(name)
        file_info["used"] = str(used_path.name)
        file_info["used_size"] = used_path.stat().st_size if used_path.exists() else 0
        
        info["files"][name] = file_info
    
    # Total sizes
    info["total_full"] = sum(
        (f.get("full", 0) for f in info["files"].values())
    )
    info["total_used"] = sum(
        (f.get("used_size", 0) for f in info["files"].values())
    )
    
    return info


__all__ = [
    "is_production",
    "get_runtime_js",
    "get_runtime_path",
    "get_resource_js",
    "get_resource_path",
    "get_suspense_js",
    "get_suspense_path",
    "get_islands_js",
    "get_islands_path",
    "get_lazy_js",
    "get_lazy_path",
    "get_navigation_js",
    "get_navigation_path",
    "get_i18n_js",
    "get_i18n_path",
    "get_browser_js",
    "get_keyboard_js",
    "get_focus_js",
    "get_theme_js",
    "get_storage_js",
    "get_sse_js",
    "get_toast_js",
    "get_full_runtime_js",
    "get_runtime_size_info",
]
