"""Runtime module containing JS assets for client-side reactivity."""

import importlib.resources as resources
from pathlib import Path


def get_runtime_js() -> str:
    """Get the signals.js runtime content."""
    runtime_path = Path(__file__).parent / "signals.js"
    return runtime_path.read_text()


def get_runtime_path() -> Path:
    """Get the path to the signals.js runtime file."""
    return Path(__file__).parent / "signals.js"


def get_resource_js() -> str:
    """Get the resource.js runtime content."""
    resource_path = Path(__file__).parent / "resource.js"
    return resource_path.read_text()


def get_resource_path() -> Path:
    """Get the path to the resource.js runtime file."""
    return Path(__file__).parent / "resource.js"


def get_suspense_js() -> str:
    """Get the suspense.js runtime content."""
    suspense_path = Path(__file__).parent / "suspense.js"
    return suspense_path.read_text()


def get_suspense_path() -> Path:
    """Get the path to the suspense.js runtime file."""
    return Path(__file__).parent / "suspense.js"


def get_islands_js() -> str:
    """Get the islands.js runtime content."""
    islands_path = Path(__file__).parent / "islands.js"
    return islands_path.read_text()


def get_islands_path() -> Path:
    """Get the path to the islands.js runtime file."""
    return Path(__file__).parent / "islands.js"


def get_lazy_js() -> str:
    """Get the lazy.js runtime content."""
    lazy_path = Path(__file__).parent / "lazy.js"
    return lazy_path.read_text()


def get_lazy_path() -> Path:
    """Get the path to the lazy.js runtime file."""
    return Path(__file__).parent / "lazy.js"


def get_navigation_js() -> str:
    """Get the navigation.js runtime content."""
    nav_path = Path(__file__).parent / "navigation.js"
    return nav_path.read_text()


def get_navigation_path() -> Path:
    """Get the path to the navigation.js runtime file."""
    return Path(__file__).parent / "navigation.js"


def get_i18n_js() -> str:
    """Get the i18n.js runtime content."""
    i18n_path = Path(__file__).parent / "i18n.js"
    return i18n_path.read_text()


def get_i18n_path() -> Path:
    """Get the path to the i18n.js runtime file."""
    return Path(__file__).parent / "i18n.js"


def get_full_runtime_js() -> str:
    """Get the complete runtime including signals, resources, suspense, islands, lazy, navigation, and i18n."""
    return (
        get_runtime_js() + "\n\n" + 
        get_resource_js() + "\n\n" + 
        get_suspense_js() + "\n\n" +
        get_islands_js() + "\n\n" +
        get_lazy_js() + "\n\n" +
        get_navigation_js() + "\n\n" +
        get_i18n_js()
    )


__all__ = [
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
    "get_full_runtime_js",
]

