"""
PyNext Hydration - Server-to-Client State Transfer

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Hydration is the process of making server-rendered HTML interactive.

1. Server renders HTML with reactive markers (data-pynext-*)
2. Server serializes state to __PYNEXT_DATA__ JSON
3. Client loads page (instant content - no flash)
4. Client calls hydrate() to connect JS runtime to existing DOM
5. Page becomes interactive

This file provides utilities for:
- Collecting signals/stores from a component
- Rendering with hydration markers
- Serializing state for the client

=============================================================================
WHY THIS EXISTS
=============================================================================

Without hydration, we'd have two bad options:

Option A: Client-side rendering only
    - User sees blank page until JS loads
    - Bad for SEO
    - Slow perceived performance

Option B: Server rendering without hydration
    - User sees content immediately
    - But page isn't interactive
    - Must re-render on client (flicker)

Hydration gives us the best of both:
    - User sees content immediately (SSR)
    - Page becomes interactive seamlessly (hydration)
    - No re-rendering, no flicker

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    Server Side (Python):
    ┌─────────────────────────────────────────────────────────────────┐
    │  def counter_page():                                             │
    │      count = signal(0)                                           │
    │      return div()[                                               │
    │          span()[count()],                                        │
    │          button(onclick=lambda: count.set(count() + 1))["+"]    │
    │      ]                                                           │
    │                                                                  │
    │  Renders to:                                                     │
    │  <div data-pynext-component="counter" data-pynext-id="c1">      │
    │      <span data-pynext-text="count">0</span>                    │
    │      <button data-pynext-click="count.set(count() + 1)">+</button>│
    │  </div>                                                          │
    │  <script id="__PYNEXT_DATA__">                                  │
    │      {"components": {"c1": {"signals": {"count": 0}}}}          │
    │  </script>                                                       │
    └─────────────────────────────────────────────────────────────────┘
    
    Client Side (JavaScript):
    ┌─────────────────────────────────────────────────────────────────┐
    │  import { hydrate } from 'pynext/runtime/reactive.js';          │
    │                                                                  │
    │  hydrate();  // Connects signals to DOM                         │
    │                                                                  │
    │  1. Parse __PYNEXT_DATA__                                       │
    │  2. Create signals with server values                            │
    │  3. Bind data-pynext-text elements to signals                   │
    │  4. Attach data-pynext-click handlers                           │
    │  5. Page is now interactive!                                     │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

1. PyNext SSR engine - calls render_component() for each page
2. Control flow components - output hydration markers
3. The JS runtime - hydrate() reads __PYNEXT_DATA__

=============================================================================
COMPILATION
=============================================================================

This file is Python-side only. It generates HTML + JSON that the
compiled JS runtime (reactive.js) consumes.

=============================================================================
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.reactive.signal import Signal
    from pynext.reactive.store import Store


# =============================================================================
# COMPONENT STATE COLLECTOR
# =============================================================================

@dataclass
class ComponentState:
    """
    Collects reactive state from a component for hydration.
    
    Used during SSR to gather all signals/stores that need to be
    serialized for client-side hydration.
    
    Example:
        state = ComponentState("counter", "c1")
        state.add_signal(count)
        state.add_store(todos)
        
        html = state.to_hydration_script()
    """
    
    name: str
    """Component name (e.g., "Counter")"""
    
    id: str
    """Unique component ID (e.g., "c1")"""
    
    signals: Dict[str, Any] = field(default_factory=dict)
    """Map of signal names to their current values"""
    
    stores: Dict[str, Any] = field(default_factory=dict)
    """Map of store names to their current data"""
    
    def add_signal(self, signal: "Signal") -> None:
        """
        Add a signal to the component state.
        
        Args:
            signal: The signal to add
        """
        self.signals[signal._name] = signal._value
    
    def add_store(self, store: "Store") -> None:
        """
        Add a store to the component state.
        
        Args:
            store: The store to add
        """
        # Unwrap reactive wrappers to plain dicts/lists
        state = store.to_hydration_state()
        self.stores.update(state)
    
    def to_dict(self) -> dict:
        """
        Convert to serializable dict.
        
        Returns:
            Dict suitable for JSON serialization
        """
        result = {}
        if self.signals:
            result["signals"] = self.signals
        if self.stores:
            result["stores"] = self.stores
        return result


# =============================================================================
# HYDRATION STATE MANAGER
# =============================================================================

class HydrationState:
    """
    Manages hydration state for an entire page.
    
    Collects state from multiple components and serializes to JSON.
    
    Example:
        state = HydrationState()
        state.add_component(counter_state)
        state.add_component(todos_state)
        
        script = state.to_script()
        # <script id="__PYNEXT_DATA__">{"components": {...}}</script>
    """
    
    def __init__(self):
        self.components: Dict[str, ComponentState] = {}
    
    def add_component(self, component: ComponentState) -> None:
        """
        Add a component's state to the page state.
        
        Args:
            component: The component state to add
        """
        self.components[component.id] = component
    
    def to_dict(self) -> dict:
        """
        Convert to serializable dict.
        
        Returns:
            Dict with all component states
        """
        return {
            "components": {
                cid: comp.to_dict()
                for cid, comp in self.components.items()
            }
        }
    
    def to_json(self) -> str:
        """
        Serialize to JSON string.
        
        Returns:
            JSON string of all component states
        """
        return json.dumps(self.to_dict())
    
    def to_script(self) -> str:
        """
        Generate the __PYNEXT_DATA__ script tag.
        
        Returns:
            HTML script tag with serialized state
        """
        json_str = self.to_json()
        return f'<script id="__PYNEXT_DATA__" type="application/json">{json_str}</script>'


# =============================================================================
# HYDRATION ATTRIBUTE HELPERS
# =============================================================================

def hydration_attrs(
    component_name: str,
    component_id: str,
) -> dict:
    """
    Generate hydration attributes for a component root.
    
    Args:
        component_name: Name of the component
        component_id: Unique ID for this instance
    
    Returns:
        Dict of data-pynext-* attributes
    
    Example:
        attrs = hydration_attrs("Counter", "c1")
        # {"data-pynext-component": "Counter", "data-pynext-id": "c1"}
    """
    return {
        "data-pynext-component": component_name,
        "data-pynext-id": component_id,
    }


def text_binding(signal_name: str) -> dict:
    """
    Generate text binding attribute.
    
    Args:
        signal_name: Name of the signal to bind
    
    Returns:
        Dict with data-pynext-text attribute
    
    Example:
        attrs = text_binding("count")
        # {"data-pynext-text": "count"}
    """
    return {"data-pynext-text": signal_name}


def click_handler(code: str) -> dict:
    """
    Generate click handler attribute.
    
    Args:
        code: JavaScript code to execute on click
    
    Returns:
        Dict with data-pynext-click attribute
    
    Example:
        attrs = click_handler("count.set(count() + 1)")
        # {"data-pynext-click": "count.set(count() + 1)"}
    """
    return {"data-pynext-click": code}


def event_handler(event: str, code: str) -> dict:
    """
    Generate event handler attribute.
    
    Args:
        event: Event name (click, input, change, etc.)
        code: JavaScript code to execute
    
    Returns:
        Dict with data-pynext-{event} attribute
    
    Example:
        attrs = event_handler("input", "name.set(e.target.value)")
        # {"data-pynext-input": "name.set(e.target.value)"}
    """
    return {f"data-pynext-{event}": code}


# =============================================================================
# COMPONENT ID GENERATOR
# =============================================================================

_component_counter = 0


def next_component_id() -> str:
    """
    Generate a unique component ID.
    
    Returns:
        Unique ID string (e.g., "c1", "c2", ...)
    """
    global _component_counter
    _component_counter += 1
    return f"c{_component_counter}"


def reset_component_ids() -> None:
    """
    Reset the component ID counter.
    
    Called at the start of each SSR request to ensure
    consistent IDs between server and client.
    """
    global _component_counter
    _component_counter = 0


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ComponentState",
    "HydrationState",
    "hydration_attrs",
    "text_binding",
    "click_handler",
    "event_handler",
    "next_component_id",
    "reset_component_ids",
]

