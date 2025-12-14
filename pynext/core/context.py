"""
Render context for tracking signals and component state during rendering.
"""

from __future__ import annotations

import contextvars
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from pynext.reactive import Signal, Effect, Memo, Store


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
class FormBinding:
    """Binding info for a form field to a DOM element."""
    
    element_id: str
    form_id: str
    field_name: str
    bind_type: str  # "value", "checked", etc.


@dataclass
class ReactiveBinding:
    """
    Binding info for a reactive DOM update.
    
    Connects a DOM node to one or more signals. When the signals change,
    the runtime will update the specific DOM node.
    """
    
    node_id: str              # DOM element ID (e.g., "el_abc123_1")
    binding_type: str         # "text", "attr", "class", "style", "show", "for"
    signal_deps: list[str]    # Signal IDs this binding depends on
    update_expr: str          # JavaScript expression to compute new value
    attr_name: str = ""       # For attr bindings, which attribute
    initial_value: Any = None # Server-rendered initial value


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
    # Structure: element_id -> {event_type -> {"code": str, "mods": dict}}
    event_handlers: dict[str, dict[str, dict]] = field(default_factory=dict)
    
    # Stores for complex state
    stores: dict[str, Any] = field(default_factory=dict)
    
    # Forms for form state
    forms: dict[str, Any] = field(default_factory=dict)
    
    # Form bindings (element_id -> FormBinding)
    form_bindings: dict[str, FormBinding] = field(default_factory=dict)
    
    # Reactive bindings for fine-grained DOM updates
    bindings: list[ReactiveBinding] = field(default_factory=list)
    
    # Counter for generating unique IDs
    _id_counter: int = field(default=0)
    
    def generate_id(self, prefix: str = "pn") -> str:
        """Generate a unique ID for an element or signal."""
        self._id_counter += 1
        return f"{prefix}_{self.render_id}_{self._id_counter}"
    
    def register_signal(self, signal: "Signal", element_id: Optional[str] = None) -> str:
        """
        Register a signal for hydration.
        
        Args:
            signal: The Signal instance to register
            element_id: Optional element ID if signal is bound to a specific element.
                       If not provided, uses the signal's own ID.
        
        Returns:
            The signal ID
        """
        signal_id = signal._id
        # Use signal's name as key for better debugging
        signal_name = getattr(signal, '_name', signal_id)
        self.signals[signal_name] = SignalRegistration(
            signal_id=signal_id,
            initial_value=signal._value,
            element_id=element_id or signal_id,
        )
        return signal_id
    
    def register_store(self, store: "Store") -> str:
        """
        Register a store for hydration.
        
        Args:
            store: The Store instance to register
            
        Returns:
            The store ID
        """
        store_id = store._id if hasattr(store, '_id') else str(id(store))
        store_name = getattr(store, '_name', store_id)
        # Serialize store data
        if hasattr(store, 'to_hydration_state'):
            self.stores[store_name] = store.to_hydration_state()
        elif hasattr(store, '_data'):
            self.stores[store_name] = dict(store._data)
        return store_id
    
    def register_memo(self, memo: "Memo") -> str:
        """
        Register a memo for hydration.
        
        Memos are registered as signals since they behave similarly on the client.
        
        Args:
            memo: The Memo instance to register
            
        Returns:
            The memo ID
        """
        memo_id = memo._id if hasattr(memo, '_id') else str(id(memo))
        memo_name = getattr(memo, '_name', memo_id)
        memo_value = memo._value if hasattr(memo, '_value') else None
        self.signals[memo_name] = SignalRegistration(
            signal_id=memo_id,
            initial_value=memo_value,
            element_id=memo_id,
        )
        return memo_id
    
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
    
    def register_event(
        self, 
        element_id: str, 
        event_type: str, 
        handler_code: str,
        modifiers: Optional[dict] = None,
    ) -> None:
        """
        Register an event handler for an element.
        
        Args:
            element_id: The element's unique ID
            event_type: Event type (e.g., "click", "submit")
            handler_code: JavaScript code to execute
            modifiers: Optional event modifiers (stop, prevent, self_only, once, capture)
        """
        if element_id not in self.event_handlers:
            self.event_handlers[element_id] = {}
        self.event_handlers[element_id][event_type] = {
            "code": handler_code,
            "mods": modifiers or {},
        }
    
    def register_form(self, form: "FormState") -> str:
        """
        Register a form for hydration.
        
        Args:
            form: The FormState instance to register
            
        Returns:
            The form ID
        """
        # Use the form's _form_id if available, otherwise fall back to id(form)
        form_id = getattr(form, '_form_id', None) or f"form_{id(form)}"
        if hasattr(form, 'to_hydration_state'):
            self.forms[form_id] = form.to_hydration_state()
        return form_id
    
    def register_form_binding(
        self, 
        element_id: str, 
        form_id: str, 
        field_name: str, 
        bind_type: str = "value"
    ) -> None:
        """
        Register a binding between a form field and a DOM element.
        
        Args:
            element_id: The DOM element ID
            form_id: The form's unique ID
            field_name: The name of the field in the form
            bind_type: Type of binding ("value", "checked", etc.)
        """
        self.form_bindings[element_id] = FormBinding(
            element_id=element_id,
            form_id=form_id,
            field_name=field_name,
            bind_type=bind_type,
        )
    
    def register_binding(
        self,
        node_id: str,
        binding_type: str,
        signal_deps: list[str],
        update_expr: str,
        attr_name: str = "",
        initial_value: Any = None,
    ) -> None:
        """
        Register a reactive binding for fine-grained DOM updates.
        
        This creates a binding that the client-side runtime will use to
        update specific DOM nodes when signals change.
        
        Args:
            node_id: DOM element ID (e.g., "el_abc123_1")
            binding_type: Type of binding ("text", "attr", "class", "style", "show", "for")
            signal_deps: List of signal IDs this binding depends on
            update_expr: JavaScript expression to compute the new value
            attr_name: For attr/class/style bindings, which attribute
            initial_value: Server-rendered initial value (for hydration check)
        """
        self.bindings.append(ReactiveBinding(
            node_id=node_id,
            binding_type=binding_type,
            signal_deps=signal_deps,
            update_expr=update_expr,
            attr_name=attr_name,
            initial_value=initial_value,
        ))
    
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
            "forms": self.forms,
            "formBindings": {
                eid: {
                    "elementId": binding.element_id,
                    "formId": binding.form_id,
                    "fieldName": binding.field_name,
                    "bindType": binding.bind_type,
                }
                for eid, binding in self.form_bindings.items()
            },
            # Reactive bindings for fine-grained DOM updates
            "bindings": [
                {
                    "nodeId": b.node_id,
                    "type": b.binding_type,
                    "signals": b.signal_deps,
                    "update": b.update_expr,
                    "attr": b.attr_name,
                    "initial": b.initial_value,
                }
                for b in self.bindings
            ],
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


def clear_context() -> None:
    """Clear the current render context (set to None)."""
    _render_context.set(None)


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

