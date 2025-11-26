"""
PyNext Component Registry System.

Provides a three-tier component system:
- Tier 1: Native libraries (pynext.tw, pynext.shadcn)
- Tier 2: Official UI components (pynext ui add)
- Tier 3: Custom registries (pynext registry)
"""

from pynext.registry.manager import RegistryManager, Registry
from pynext.registry.components import (
    list_available_components,
    get_component_source,
    copy_component_to_project,
    AVAILABLE_COMPONENTS,
)

__all__ = [
    "RegistryManager",
    "Registry",
    "list_available_components",
    "get_component_source",
    "copy_component_to_project",
    "AVAILABLE_COMPONENTS",
]

