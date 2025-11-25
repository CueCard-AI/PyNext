"""
Render context for tracking signals and component state during rendering.
"""

from __future__ import annotations

import contextvars
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from pynext.core.signals import Signal, Effect, Memo, Store


# Context variable to store the current render context
_render_context: contextvars.ContextVar[Optional["RenderContext"]] = contextvars.ContextVar(
    "render_context", default=None
)


@dataclass
class SignalRegistration:
    """Registration info for a signal that needs hydration."""
    
    signal_id: str
    initial_value: Any
    element_id: str


@dataclass
class EffectRegistration:
    """Registration info for an effect that needs to run on client."""
    
    effect_id: str
    dependencies: list[str]  # Signal IDs this effect depends on
    code: str  # JavaScript code to execute


@dataclass
class ActionBinding:
    """Binding info for a server action."""
    
    action_name: str
    action_id: str
    args_template: dict[str, Any]


@dataclass
class RenderContext:
    """
    Context for a single render pass.
    
    Tracks all reactive primitives and their bindings for hydration.
    """
    
    # Unique ID for this render
    render_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    
    # Registered signals
    signals: dict[str, SignalRegistration] = field(default_factory=dict)
    
    # Registered effects  
    effects: dict[str, EffectRegistration] = field(default_factory=dict)
    
    # Server action bindings
    actions: dict[str, ActionBinding] = field(default_factory=dict)
    
    # Event handlers that need to be attached
    event_handlers: dict[str, dict[str, str]] = field(default_factory=dict)
    
    # Stores for complex state
    stores: dict[str, Any] = field(default_factory=dict)
    
    # Counter for generating unique IDs
    _id_counter: int = field(default=0)
    
    def generate_id(self, prefix: str = "pn") -> str:
        """Generate a unique ID for an element or signal."""
        self._id_counter += 1
        return f"{prefix}_{self.render_id}_{self._id_counter}"
    
    def register_signal(self, signal: "Signal", element_id: str) -> str:
        """Register a signal for hydration."""
        signal_id = signal._id
        self.signals[signal_id] = SignalRegistration(
            signal_id=signal_id,
            initial_value=signal._value,
            element_id=element_id,
        )
        return signal_id
    
    def register_effect(self, effect: "Effect") -> str:
        """Register an effect for client-side execution."""
        effect_id = effect._id
        self.effects[effect_id] = EffectRegistration(
            effect_id=effect_id,
            dependencies=list(effect._dependencies),
            code=effect._js_code or "",
        )
        return effect_id
    
    def register_action(self, action_name: str, action_id: str, args: dict) -> str:
        """Register a server action binding."""
        self.actions[action_id] = ActionBinding(
            action_name=action_name,
            action_id=action_id,
            args_template=args,
        )
        return action_id
    
    def register_event(self, element_id: str, event_type: str, handler_code: str) -> None:
        """Register an event handler for an element."""
        if element_id not in self.event_handlers:
            self.event_handlers[element_id] = {}
        self.event_handlers[element_id][event_type] = handler_code
    
    def get_hydration_data(self) -> dict:
        """Get all data needed for client-side hydration."""
        return {
            "renderId": self.render_id,
            "signals": {
                sid: {
                    "id": reg.signal_id,
                    "value": reg.initial_value,
                    "elementId": reg.element_id,
                }
                for sid, reg in self.signals.items()
            },
            "effects": {
                eid: {
                    "id": reg.effect_id,
                    "dependencies": reg.dependencies,
                    "code": reg.code,
                }
                for eid, reg in self.effects.items()
            },
            "actions": {
                aid: {
                    "name": binding.action_name,
                    "id": binding.action_id,
                    "args": binding.args_template,
                }
                for aid, binding in self.actions.items()
            },
            "events": self.event_handlers,
            "stores": self.stores,
        }


def get_context() -> Optional[RenderContext]:
    """Get the current render context, if any."""
    return _render_context.get()


def set_context(ctx: Optional[RenderContext]) -> contextvars.Token:
    """Set the current render context."""
    return _render_context.set(ctx)


def reset_context(token: contextvars.Token) -> None:
    """Reset the render context to its previous value."""
    _render_context.reset(token)


class render_context:
    """Context manager for creating a new render context."""
    
    def __init__(self):
        self.ctx = RenderContext()
        self.token = None
    
    def __enter__(self) -> RenderContext:
        self.token = set_context(self.ctx)
        return self.ctx
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token is not None:
            reset_context(self.token)
        return False

