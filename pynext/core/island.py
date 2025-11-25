"""
Islands Architecture for PyNext.

Islands enable selective/partial hydration - only interactive parts of the page
get JavaScript, while static content remains as pure HTML.

This dramatically reduces JavaScript bundle sizes and improves performance:
- Static content: 0 bytes JS
- Interactive islands: Only the JS needed for that island

Inspired by Astro Islands and Fresh (Deno).

Example:
    @island
    def Counter():
        count = Signal(0)
        return button(onclick=lambda: count.set(count() + 1))[
            "Count: ", count
        ]
    
    @page
    def HomePage():
        return div()[
            h1()["Welcome"],  # Static - no JS
            p()["This is static content"],  # Static - no JS
            Counter(),  # Interactive island - gets hydrated
        ]
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from pynext.core.signals import Signal, Store, Computed, Effect
    from pynext.core.html import Element


class HydrationStrategy(Enum):
    """When to hydrate an island."""
    
    # Hydrate immediately when page loads
    LOAD = "load"
    
    # Hydrate when island becomes visible (IntersectionObserver)
    VISIBLE = "visible"
    
    # Hydrate when user interacts (click, focus, hover)
    IDLE = "idle"
    
    # Hydrate on specific media query
    MEDIA = "media"
    
    # Never hydrate on client (SSR only)
    NONE = "none"


class InteractivityType(Enum):
    """Types of interactivity in a component."""
    
    NONE = "none"           # Pure static content
    SIGNAL = "signal"       # Has reactive signals
    EVENT = "event"         # Has event handlers
    EFFECT = "effect"       # Has side effects
    RESOURCE = "resource"   # Has async resources
    STORE = "store"         # Has reactive stores


@dataclass
class IslandMetadata:
    """Metadata for an island component."""
    
    # Unique island ID
    id: str
    
    # Component name
    name: str
    
    # Hydration strategy
    strategy: HydrationStrategy = HydrationStrategy.LOAD
    
    # Media query for MEDIA strategy
    media_query: Optional[str] = None
    
    # Types of interactivity detected
    interactivity: Set[InteractivityType] = field(default_factory=set)
    
    # Props passed to the island
    props: Dict[str, Any] = field(default_factory=dict)
    
    # Signals used by this island
    signals: List[str] = field(default_factory=list)
    
    # Whether island is currently rendered
    rendered: bool = False
    
    # Hash for deduplication
    content_hash: Optional[str] = None


@dataclass
class IslandBoundary:
    """
    Represents an island boundary in the component tree.
    
    Islands are hydration boundaries - everything inside gets hydrated together,
    but the island itself is isolated from other islands and static content.
    """
    
    id: str
    metadata: IslandMetadata
    children: List[Any] = field(default_factory=list)
    parent: Optional["IslandBoundary"] = None
    
    def render(self) -> str:
        """Render island with hydration markers."""
        from pynext.core.html import div
        
        # Render children
        children_html = []
        for child in self.children:
            if hasattr(child, 'render'):
                children_html.append(child.render())
            elif callable(child):
                result = child()
                if hasattr(result, 'render'):
                    children_html.append(result.render())
                else:
                    children_html.append(str(result))
            else:
                children_html.append(str(child))
        
        content = "".join(children_html)
        
        # Wrap in island boundary
        return f'''<div data-island="{self.id}" data-hydrate="{self.metadata.strategy.value}" data-component="{self.metadata.name}">{content}</div>'''
    
    def get_hydration_script(self) -> str:
        """Get the JavaScript to hydrate this island."""
        props_json = json.dumps(self.metadata.props)
        signals_json = json.dumps(self.metadata.signals)
        
        return f'''
__pynext__.registerIsland("{self.id}", {{
  component: "{self.metadata.name}",
  strategy: "{self.metadata.strategy.value}",
  props: {props_json},
  signals: {signals_json},
  mediaQuery: {json.dumps(self.metadata.media_query)}
}});
'''


# Global registry of islands
_island_registry: Dict[str, IslandMetadata] = {}
_island_components: Dict[str, Callable] = {}


def island(
    func: Optional[Callable] = None,
    *,
    strategy: HydrationStrategy = HydrationStrategy.LOAD,
    media: Optional[str] = None,
) -> Callable:
    """
    Decorator to mark a component as an interactive island.
    
    Islands are hydration boundaries - only the island's JavaScript is sent
    to the client, not the entire page.
    
    Args:
        strategy: When to hydrate the island
            - LOAD: Immediately on page load
            - VISIBLE: When scrolled into view
            - IDLE: When browser is idle or user interacts
            - MEDIA: When media query matches
            - NONE: Never hydrate (SSR only)
        media: Media query for MEDIA strategy
    
    Example:
        @island
        def Counter():
            count = Signal(0)
            return button(onclick=lambda: count.set(count() + 1))[count]
        
        @island(strategy=HydrationStrategy.VISIBLE)
        def LazyChart():
            # Only hydrated when scrolled into view
            return ChartComponent()
        
        @island(strategy=HydrationStrategy.MEDIA, media="(min-width: 768px)")
        def DesktopOnlyWidget():
            # Only hydrated on desktop
            return ComplexWidget()
    """
    def decorator(fn: Callable) -> Callable:
        component_name = fn.__name__
        
        @wraps(fn)
        def wrapper(*args, **kwargs) -> IslandBoundary:
            # Generate unique ID for this island instance
            island_id = f"island-{component_name}-{uuid.uuid4().hex[:8]}"
            
            # Create metadata
            metadata = IslandMetadata(
                id=island_id,
                name=component_name,
                strategy=strategy,
                media_query=media,
                props=kwargs.copy(),
            )
            
            # Detect interactivity by analyzing the function
            metadata.interactivity = _detect_interactivity(fn)
            
            # Register the island
            _island_registry[island_id] = metadata
            _island_components[component_name] = fn
            
            # Call the actual component
            result = fn(*args, **kwargs)
            
            # Wrap in island boundary
            boundary = IslandBoundary(
                id=island_id,
                metadata=metadata,
                children=[result] if not isinstance(result, list) else result,
            )
            
            return boundary
        
        # Mark as island
        wrapper._is_island = True
        wrapper._island_strategy = strategy
        wrapper._island_media = media
        wrapper._component_name = component_name
        
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


def static(func: Callable) -> Callable:
    """
    Decorator to explicitly mark a component as static (no hydration).
    
    This is useful when you want to ensure a component never gets JavaScript,
    even if it contains elements that might look interactive.
    
    Example:
        @static
        def Footer():
            # Even though this has links, it won't be hydrated
            return footer()[
                a(href="/about")["About"],
                a(href="/contact")["Contact"],
            ]
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Mark as explicitly static
        if hasattr(result, '_metadata'):
            result._metadata['static'] = True
        
        return result
    
    wrapper._is_static = True
    wrapper._is_island = False
    
    return wrapper


def _detect_interactivity(func: Callable) -> Set[InteractivityType]:
    """
    Analyze a function to detect what types of interactivity it uses.
    
    This is used to determine if hydration is needed and what features
    to include in the island's JavaScript bundle.
    """
    interactivity = set()
    
    # Get function source and analyze it
    # In practice, we detect this at render time by tracking what's used
    
    # For now, check common patterns in the function's closure
    if hasattr(func, '__code__'):
        code = func.__code__
        freevars = code.co_freevars
        
        # Check for signal-related names
        signal_indicators = {'Signal', 'signal', 'createSignal', 'set', 'update'}
        store_indicators = {'Store', 'store', 'createStore'}
        effect_indicators = {'Effect', 'effect', 'createEffect'}
        resource_indicators = {'Resource', 'resource', 'createResource', 'fetch'}
        event_indicators = {'onclick', 'onchange', 'oninput', 'onsubmit', 'onkeydown'}
        
        for name in code.co_names:
            if name in signal_indicators:
                interactivity.add(InteractivityType.SIGNAL)
            if name in store_indicators:
                interactivity.add(InteractivityType.STORE)
            if name in effect_indicators:
                interactivity.add(InteractivityType.EFFECT)
            if name in resource_indicators:
                interactivity.add(InteractivityType.RESOURCE)
            if name in event_indicators:
                interactivity.add(InteractivityType.EVENT)
    
    if not interactivity:
        interactivity.add(InteractivityType.NONE)
    
    return interactivity


def is_interactive(component: Any) -> bool:
    """
    Check if a component needs hydration.
    
    Returns True if the component:
    - Is marked as @island
    - Contains signals, stores, or effects
    - Has event handlers
    - Contains interactive children
    """
    # Explicitly marked as static
    if hasattr(component, '_is_static') and component._is_static:
        return False
    
    # Explicitly marked as island
    if hasattr(component, '_is_island') and component._is_island:
        return True
    
    # Check if it's an IslandBoundary
    if isinstance(component, IslandBoundary):
        return True
    
    # Check for signals/stores in the component
    if hasattr(component, '_signals') and component._signals:
        return True
    
    # Check for event handlers
    if hasattr(component, '_attrs'):
        for attr in component._attrs:
            if attr.startswith('on'):
                return True
    
    # Check children recursively
    if hasattr(component, 'children'):
        for child in component.children:
            if is_interactive(child):
                return True
    
    return False


def collect_islands(component: Any) -> List[IslandBoundary]:
    """
    Recursively collect all islands from a component tree.
    
    Used by the server to generate island-specific hydration data.
    """
    islands = []
    
    if isinstance(component, IslandBoundary):
        islands.append(component)
    
    # Check children
    if hasattr(component, 'children'):
        for child in component.children:
            islands.extend(collect_islands(child))
    
    # Check if it's a list of components
    if isinstance(component, list):
        for item in component:
            islands.extend(collect_islands(item))
    
    return islands


def get_island_hydration_data(islands: List[IslandBoundary]) -> Dict[str, Any]:
    """
    Generate hydration data for a list of islands.
    
    This is embedded in the page and used by the client to hydrate islands.
    """
    return {
        "islands": [
            {
                "id": island.id,
                "component": island.metadata.name,
                "strategy": island.metadata.strategy.value,
                "props": island.metadata.props,
                "signals": island.metadata.signals,
                "mediaQuery": island.metadata.media_query,
            }
            for island in islands
        ]
    }


def generate_island_script(islands: List[IslandBoundary]) -> str:
    """
    Generate the JavaScript to hydrate all islands on the page.
    """
    if not islands:
        return ""
    
    scripts = []
    for island in islands:
        scripts.append(island.get_hydration_script())
    
    return f'''<script>
(function() {{
  {"".join(scripts)}
  __pynext__.hydrateIslands();
}})();
</script>'''


# =============================================================================
# Island Analysis Utilities
# =============================================================================

class ComponentAnalyzer:
    """
    Analyzes components to determine hydration requirements.
    
    This is used during build time to:
    1. Identify which components need hydration
    2. Calculate optimal hydration strategies
    3. Generate per-island bundles
    """
    
    def __init__(self):
        self.analyzed: Dict[str, Dict[str, Any]] = {}
    
    def analyze(self, component: Any) -> Dict[str, Any]:
        """Analyze a component for interactivity."""
        component_id = id(component)
        
        if component_id in self.analyzed:
            return self.analyzed[component_id]
        
        result = {
            "id": component_id,
            "is_interactive": False,
            "is_island": False,
            "interactivity_types": set(),
            "signals": [],
            "events": [],
            "resources": [],
            "children_interactive": False,
            "recommended_strategy": HydrationStrategy.NONE,
        }
        
        # Check if it's an island
        if isinstance(component, IslandBoundary):
            result["is_island"] = True
            result["is_interactive"] = True
            result["interactivity_types"] = component.metadata.interactivity
            result["recommended_strategy"] = component.metadata.strategy
        
        # Check for explicit island decorator
        elif hasattr(component, '_is_island') and component._is_island:
            result["is_island"] = True
            result["is_interactive"] = True
        
        # Analyze for signals
        if hasattr(component, '_signals'):
            result["signals"] = list(component._signals.keys())
            result["is_interactive"] = True
            result["interactivity_types"].add(InteractivityType.SIGNAL)
        
        # Analyze for events
        if hasattr(component, '_attrs'):
            for attr, value in component._attrs.items():
                if attr.startswith('on') and callable(value):
                    result["events"].append(attr)
                    result["is_interactive"] = True
                    result["interactivity_types"].add(InteractivityType.EVENT)
        
        # Analyze children
        if hasattr(component, 'children'):
            for child in component.children:
                child_analysis = self.analyze(child)
                if child_analysis["is_interactive"]:
                    result["children_interactive"] = True
        
        # Determine recommended strategy
        if result["is_interactive"]:
            if InteractivityType.EVENT in result["interactivity_types"]:
                # Interactive from the start
                result["recommended_strategy"] = HydrationStrategy.LOAD
            elif InteractivityType.SIGNAL in result["interactivity_types"]:
                # Can wait until visible
                result["recommended_strategy"] = HydrationStrategy.VISIBLE
            else:
                # Can wait until idle
                result["recommended_strategy"] = HydrationStrategy.IDLE
        
        self.analyzed[component_id] = result
        return result


# =============================================================================
# Bundle Generation
# =============================================================================

def get_island_bundle_requirements(islands: List[IslandBoundary]) -> Dict[str, Set[str]]:
    """
    Determine what JavaScript features each island needs.
    
    Returns a dict mapping island IDs to sets of required features.
    """
    requirements: Dict[str, Set[str]] = {}
    
    for island in islands:
        island_reqs = set()
        
        for itype in island.metadata.interactivity:
            if itype == InteractivityType.SIGNAL:
                island_reqs.add("signals")
            elif itype == InteractivityType.STORE:
                island_reqs.add("signals")
                island_reqs.add("store")
            elif itype == InteractivityType.EFFECT:
                island_reqs.add("signals")
                island_reqs.add("effect")
            elif itype == InteractivityType.RESOURCE:
                island_reqs.add("signals")
                island_reqs.add("resource")
            elif itype == InteractivityType.EVENT:
                island_reqs.add("events")
        
        requirements[island.id] = island_reqs
    
    return requirements


def get_minimal_runtime_for_island(island: IslandBoundary) -> List[str]:
    """
    Get the minimal runtime modules needed for an island.
    
    Returns a list of runtime module names to include.
    """
    modules = ["core"]  # Always need core
    
    for itype in island.metadata.interactivity:
        if itype == InteractivityType.SIGNAL:
            modules.append("signals")
        if itype == InteractivityType.STORE:
            modules.append("store")
        if itype == InteractivityType.EFFECT:
            modules.append("effects")
        if itype == InteractivityType.RESOURCE:
            modules.append("resource")
    
    return list(set(modules))

