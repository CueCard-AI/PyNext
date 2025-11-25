"""
Slot Component for Parallel Routes.

Provides a declarative way to define slot placeholders in layouts
that will be filled with parallel route content.

SolidJS Principles Applied:
- Zero JS for static slots
- Independent streaming per slot
- Fine-grained updates (only slot content changes)
- Selective hydration (interactive slots only)

Example:
    @layout
    def dashboard_layout():
        return div(class_="dashboard")[
            Slot("sidebar", loading=SidebarSkeleton),
            Slot("main", loading=ContentSkeleton),
        ]
"""

from dataclasses import dataclass
from typing import Optional, Callable, Any, List, Dict
import uuid
import asyncio
import contextvars

from pynext.core.html import div


# Context for tracking active slots
_slot_context: contextvars.ContextVar[Optional["SlotContext"]] = contextvars.ContextVar(
    "slot_context", default=None
)


@dataclass
class SlotContext:
    """Context for slot rendering."""
    active_slots: Dict[str, str] = None  # slot_name -> rendered content
    pending_slots: List[str] = None
    
    def __post_init__(self):
        if self.active_slots is None:
            self.active_slots = {}
        if self.pending_slots is None:
            self.pending_slots = []


def get_slot_context() -> Optional[SlotContext]:
    """Get current slot context."""
    return _slot_context.get()


def create_slot_context() -> SlotContext:
    """Create a new slot context."""
    ctx = SlotContext()
    _slot_context.set(ctx)
    return ctx


def set_slot_content(name: str, content: str) -> None:
    """Set content for a slot."""
    ctx = get_slot_context()
    if ctx:
        ctx.active_slots[name] = content
        if name in ctx.pending_slots:
            ctx.pending_slots.remove(name)


class Slot:
    """
    Slot component for parallel route content.
    
    Defines a placeholder in a layout where parallel route content
    will be rendered. Each slot can have its own loading and error states.
    
    Args:
        name: Unique slot name (matches @name folder)
        loading: Loading component shown while slot content loads
        error: Error component shown on slot error
        default: Default content if no route matches
        className: CSS class for slot container
        stream: Whether to stream this slot independently
    
    Example:
        # In layout.py
        Slot("sidebar", loading=SidebarSkeleton)
        
        # In pages/@sidebar/page.py
        def sidebar_content():
            return nav()[...navigation items...]
    """
    
    def __init__(
        self,
        name: str,
        loading: Optional[Callable[[], Any]] = None,
        error: Optional[Callable[[Exception], Any]] = None,
        default: Optional[Callable[[], Any]] = None,
        className: str = "",
        stream: bool = True,
    ):
        self.name = name
        self.loading = loading
        self.error = error
        self.default = default
        self.className = className
        self.stream = stream
        self.id = f"slot-{name}-{uuid.uuid4().hex[:6]}"
    
    def render(self) -> str:
        """
        Render the slot.
        
        If content is available in context, render it.
        Otherwise, render loading state or placeholder.
        """
        ctx = get_slot_context()
        
        # Check if we have content for this slot
        if ctx and self.name in ctx.active_slots:
            content = ctx.active_slots[self.name]
            return self._wrap_content(content, "ready")
        
        # Register as pending
        if ctx:
            ctx.pending_slots.append(self.name)
        
        # Render loading or default
        if self.loading:
            loading_content = self._render_component(self.loading)
            return self._wrap_content(loading_content, "loading")
        
        if self.default:
            default_content = self._render_component(self.default)
            return self._wrap_content(default_content, "default")
        
        # Empty placeholder
        return self._wrap_content("", "pending")
    
    def _wrap_content(self, content: str, state: str) -> str:
        """Wrap content in slot container."""
        classes = f"pynext-slot {self.className}".strip()
        
        return f'''<div 
  id="{self.id}"
  class="{classes}"
  data-slot="{self.name}"
  data-slot-state="{state}"
>{content}</div>'''
    
    def _render_component(self, component: Callable) -> str:
        """Render a component function."""
        result = component()
        if hasattr(result, 'render'):
            return result.render()
        return str(result) if result else ""
    
    def render_error(self, error: Exception) -> str:
        """Render error state for this slot."""
        if self.error:
            result = self.error(error)
            if hasattr(result, 'render'):
                content = result.render()
            else:
                content = str(result)
        else:
            content = f'<div class="slot-error">Error loading {self.name}</div>'
        
        return self._wrap_content(content, "error")
    
    def get_streaming_placeholder(self) -> str:
        """Get placeholder HTML for streaming updates."""
        loading_content = ""
        if self.loading:
            loading_content = self._render_component(self.loading)
        
        return self._wrap_content(loading_content, "streaming")


class SlotGroup:
    """
    Group multiple slots for coordinated rendering.
    
    Useful when you want multiple slots to show loading
    states together or stream as a batch.
    
    Example:
        SlotGroup(loading=PageSkeleton)[
            Slot("header"),
            Slot("sidebar"),
            Slot("main"),
            Slot("footer"),
        ]
    """
    
    def __init__(
        self,
        loading: Optional[Callable[[], Any]] = None,
        error: Optional[Callable[[Exception], Any]] = None,
    ):
        self.loading = loading
        self.error = error
        self.slots: List[Slot] = []
        self.id = f"slot-group-{uuid.uuid4().hex[:6]}"
    
    def __getitem__(self, slots: Any) -> "SlotGroup":
        """Add slots using bracket syntax."""
        if isinstance(slots, tuple):
            self.slots = list(slots)
        elif isinstance(slots, list):
            self.slots = slots
        else:
            self.slots = [slots]
        return self
    
    def render(self) -> str:
        """Render the slot group."""
        ctx = get_slot_context()
        
        # Check if all slots have content
        all_ready = True
        if ctx:
            for slot in self.slots:
                if slot.name not in ctx.active_slots:
                    all_ready = False
                    break
        else:
            all_ready = False
        
        if all_ready:
            # Render all slots with their content
            parts = [slot.render() for slot in self.slots]
            return f'<div id="{self.id}" class="slot-group" data-state="ready">{"".join(parts)}</div>'
        
        # Show group loading state
        if self.loading:
            loading_content = ""
            result = self.loading()
            if hasattr(result, 'render'):
                loading_content = result.render()
            else:
                loading_content = str(result)
            
            return f'<div id="{self.id}" class="slot-group" data-state="loading">{loading_content}</div>'
        
        # Render individual slot placeholders
        parts = [slot.render() for slot in self.slots]
        return f'<div id="{self.id}" class="slot-group" data-state="pending">{"".join(parts)}</div>'


# =============================================================================
# Slot Streaming Runtime
# =============================================================================

def get_slot_streaming_js() -> str:
    """
    Get JavaScript runtime for slot streaming updates.
    
    This minimal runtime handles:
    - Updating slot content from stream
    - Managing slot states
    - Optional animations between states
    """
    return """
(function() {
  window.__pynext__ = window.__pynext__ || {};
  window.__pynext__.slots = {
    // Update slot content
    update: function(name, content) {
      var slot = document.querySelector('[data-slot="' + name + '"]');
      if (slot) {
        slot.innerHTML = content;
        slot.setAttribute('data-slot-state', 'ready');
        slot.classList.remove('slot-loading', 'slot-pending');
        slot.classList.add('slot-ready');
      }
    },
    
    // Set slot loading state
    setLoading: function(name) {
      var slot = document.querySelector('[data-slot="' + name + '"]');
      if (slot) {
        slot.setAttribute('data-slot-state', 'loading');
        slot.classList.add('slot-loading');
      }
    },
    
    // Set slot error state
    setError: function(name, message) {
      var slot = document.querySelector('[data-slot="' + name + '"]');
      if (slot) {
        slot.innerHTML = '<div class="slot-error">' + message + '</div>';
        slot.setAttribute('data-slot-state', 'error');
        slot.classList.add('slot-error');
      }
    },
    
    // Update slot group
    updateGroup: function(groupId, slots) {
      var group = document.getElementById(groupId);
      if (group) {
        group.setAttribute('data-state', 'ready');
        Object.keys(slots).forEach(function(name) {
          window.__pynext__.slots.update(name, slots[name]);
        });
      }
    }
  };
})();
"""


def needs_slot_runtime() -> bool:
    """Check if current page needs slot runtime."""
    ctx = get_slot_context()
    return ctx is not None and len(ctx.pending_slots) > 0


# =============================================================================
# Slot CSS
# =============================================================================

def get_slot_css() -> str:
    """Get CSS for slot transitions and states."""
    return """
.pynext-slot {
  position: relative;
}

.pynext-slot[data-slot-state="loading"]::after {
  content: "";
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pynext-slot[data-slot-state="pending"] {
  min-height: 100px;
}

.slot-loading {
  animation: slot-pulse 1.5s ease-in-out infinite;
}

@keyframes slot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.slot-error {
  color: #dc2626;
  padding: 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.25rem;
}

/* Transition when content updates */
.pynext-slot[data-slot-state="ready"] {
  animation: slot-fade-in 0.2s ease-out;
}

@keyframes slot-fade-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
"""


# =============================================================================
# Slot Helpers
# =============================================================================

def define_slot(
    name: str,
    loading: Optional[Callable[[], Any]] = None,
    error: Optional[Callable[[Exception], Any]] = None,
    default: Optional[Callable[[], Any]] = None,
) -> Slot:
    """
    Define a slot with configuration.
    
    Convenience function for creating slots with common patterns.
    """
    return Slot(
        name=name,
        loading=loading,
        error=error,
        default=default,
    )


def sidebar_slot(loading: Optional[Callable] = None) -> Slot:
    """Pre-configured sidebar slot."""
    return Slot("sidebar", loading=loading, className="sidebar-slot")


def main_slot(loading: Optional[Callable] = None) -> Slot:
    """Pre-configured main content slot."""
    return Slot("main", loading=loading, className="main-slot")


def modal_slot(loading: Optional[Callable] = None) -> Slot:
    """Pre-configured modal slot (for intercepting routes)."""
    return Slot("modal", loading=loading, className="modal-slot")

