"""
PyNext Client-Side Primitives

Provides Python APIs for client-side interactivity that compile to efficient JavaScript.
These primitives eliminate the need for raw JavaScript in application code.

Key APIs:
- on_keydown, on_key_sequence: Keyboard shortcut handling
- use_storage: localStorage/sessionStorage with signal sync
- use_ref: DOM element references
- client_effect: Client-side effects
- use_theme: Theme/dark mode management
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps

from pynext.core.context import get_context


T = TypeVar("T")


# =============================================================================
# Keyboard Shortcuts
# =============================================================================

@dataclass
class KeyboardShortcut:
    """Represents a registered keyboard shortcut."""
    id: str
    key: str
    modifiers: List[str]
    handler_id: str
    context: str = "global"  # "global", "input", "dialog"
    prevent_default: bool = True
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "modifiers": self.modifiers,
            "handlerId": self.handler_id,
            "context": self.context,
            "preventDefault": self.prevent_default,
        }


@dataclass
class KeySequence:
    """Represents a multi-key sequence (e.g., g → d)."""
    id: str
    keys: List[str]
    handler_id: str
    timeout: int = 1000  # ms
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "keys": self.keys,
            "handlerId": self.handler_id,
            "timeout": self.timeout,
        }


# Global registries
_shortcuts: Dict[str, KeyboardShortcut] = {}
_sequences: Dict[str, KeySequence] = {}
_handlers: Dict[str, Callable] = {}


def _parse_key_combo(combo: str) -> tuple[str, List[str]]:
    """
    Parse a key combination string into key and modifiers.
    
    Examples:
        "cmd+k" -> ("k", ["cmd"])
        "ctrl+shift+s" -> ("s", ["ctrl", "shift"])
        "escape" -> ("escape", [])
    """
    parts = combo.lower().split("+")
    modifiers = []
    key = parts[-1]
    
    for part in parts[:-1]:
        if part in ("cmd", "meta", "command"):
            modifiers.append("meta")
        elif part in ("ctrl", "control"):
            modifiers.append("ctrl")
        elif part in ("alt", "option"):
            modifiers.append("alt")
        elif part in ("shift",):
            modifiers.append("shift")
    
    return key, modifiers


def on_keydown(
    key_combo: str,
    *,
    context: str = "global",
    prevent_default: bool = True,
):
    """
    Decorator to register a keyboard shortcut handler.
    
    Usage:
        @on_keydown("cmd+k")
        def open_search():
            search_open.set(True)
        
        @on_keydown("escape", context="dialog")
        def close_dialog():
            dialog_open.set(False)
    
    Args:
        key_combo: Key combination (e.g., "cmd+k", "ctrl+shift+s", "escape")
        context: When to trigger ("global", "input", "dialog")
        prevent_default: Whether to prevent browser default behavior
    """
    def decorator(fn: Callable) -> Callable:
        shortcut_id = f"shortcut_{uuid.uuid4().hex[:8]}"
        handler_id = f"handler_{uuid.uuid4().hex[:8]}"
        
        key, modifiers = _parse_key_combo(key_combo)
        
        shortcut = KeyboardShortcut(
            id=shortcut_id,
            key=key,
            modifiers=modifiers,
            handler_id=handler_id,
            context=context,
            prevent_default=prevent_default,
        )
        
        _shortcuts[shortcut_id] = shortcut
        _handlers[handler_id] = fn
        
        # Register with render context if available
        ctx = get_context()
        if ctx:
            if not hasattr(ctx, 'keyboard_shortcuts'):
                ctx.keyboard_shortcuts = []
            ctx.keyboard_shortcuts.append(shortcut)
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        
        wrapper._shortcut_id = shortcut_id
        wrapper._handler_id = handler_id
        
        return wrapper
    
    return decorator


def on_key_sequence(
    sequence: str,
    *,
    timeout: int = 1000,
):
    """
    Decorator to register a multi-key sequence handler.
    
    Usage:
        @on_key_sequence("g d")
        def go_to_dashboard():
            navigate("/")
        
        @on_key_sequence("g b")
        def go_to_board():
            navigate("/board")
    
    Args:
        sequence: Space-separated keys (e.g., "g d", "g s")
        timeout: Max time between keys in milliseconds
    """
    def decorator(fn: Callable) -> Callable:
        sequence_id = f"seq_{uuid.uuid4().hex[:8]}"
        handler_id = f"handler_{uuid.uuid4().hex[:8]}"
        
        keys = sequence.lower().split()
        
        seq = KeySequence(
            id=sequence_id,
            keys=keys,
            handler_id=handler_id,
            timeout=timeout,
        )
        
        _sequences[sequence_id] = seq
        _handlers[handler_id] = fn
        
        # Register with render context
        ctx = get_context()
        if ctx:
            if not hasattr(ctx, 'key_sequences'):
                ctx.key_sequences = []
            ctx.key_sequences.append(seq)
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        
        wrapper._sequence_id = sequence_id
        wrapper._handler_id = handler_id
        
        return wrapper
    
    return decorator


def register_shortcut(
    key_combo: str,
    handler: Callable,
    *,
    context: str = "global",
    prevent_default: bool = True,
) -> str:
    """
    Programmatically register a keyboard shortcut.
    
    Returns the shortcut ID for later removal.
    """
    shortcut_id = f"shortcut_{uuid.uuid4().hex[:8]}"
    handler_id = f"handler_{uuid.uuid4().hex[:8]}"
    
    key, modifiers = _parse_key_combo(key_combo)
    
    shortcut = KeyboardShortcut(
        id=shortcut_id,
        key=key,
        modifiers=modifiers,
        handler_id=handler_id,
        context=context,
        prevent_default=prevent_default,
    )
    
    _shortcuts[shortcut_id] = shortcut
    _handlers[handler_id] = handler
    
    return shortcut_id


def unregister_shortcut(shortcut_id: str) -> bool:
    """Remove a registered shortcut."""
    if shortcut_id in _shortcuts:
        shortcut = _shortcuts.pop(shortcut_id)
        _handlers.pop(shortcut.handler_id, None)
        return True
    return False


# =============================================================================
# Storage
# =============================================================================

@dataclass
class StorageSignal:
    """A signal that syncs with localStorage/sessionStorage."""
    id: str
    key: str
    default: Any
    storage_type: str  # "local" or "session"
    _value: Any = field(default=None, repr=False)
    
    def __post_init__(self):
        self._value = self.default
        self._subscribers: List[Callable] = []
    
    def __call__(self) -> Any:
        """Read the current value."""
        return self._value
    
    def set(self, value: Any) -> None:
        """Set a new value and sync to storage."""
        if self._value != value:
            self._value = value
            self._notify()
    
    def _notify(self) -> None:
        for subscriber in self._subscribers:
            subscriber(self._value)
    
    def subscribe(self, fn: Callable) -> Callable[[], None]:
        self._subscribers.append(fn)
        return lambda: self._subscribers.remove(fn)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "default": self.default,
            "storageType": self.storage_type,
        }
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        return f"__pynext__.useStorage('{self.id}', '{self.key}', {json.dumps(self.default)}, '{self.storage_type}')"


_storage_signals: Dict[str, StorageSignal] = {}


def use_storage(
    key: str,
    default: T = None,
    *,
    storage: str = "local",
) -> StorageSignal:
    """
    Create a signal that persists to localStorage or sessionStorage.
    
    Usage:
        theme = use_storage("theme", default="light")
        
        # Read
        current_theme = theme()
        
        # Write (automatically persists)
        theme.set("dark")
    
    Args:
        key: Storage key name
        default: Default value if key doesn't exist
        storage: "local" for localStorage, "session" for sessionStorage
    """
    signal_id = f"storage_{uuid.uuid4().hex[:8]}"
    
    signal = StorageSignal(
        id=signal_id,
        key=key,
        default=default,
        storage_type=storage,
    )
    
    _storage_signals[signal_id] = signal
    
    # Register with render context
    ctx = get_context()
    if ctx:
        if not hasattr(ctx, 'storage_signals'):
            ctx.storage_signals = []
        ctx.storage_signals.append(signal)
    
    return signal


# =============================================================================
# Refs (DOM Element References)
# =============================================================================

@dataclass
class Ref:
    """A reference to a DOM element."""
    id: str
    _element: Any = field(default=None, repr=False)
    
    @property
    def current(self) -> Any:
        """Get the current DOM element (available after hydration)."""
        return self._element
    
    def to_dict(self) -> dict:
        return {"id": self.id}
    
    def get_js_init(self) -> str:
        return f"__pynext__.createRef('{self.id}')"


_refs: Dict[str, Ref] = {}


def use_ref(name: Optional[str] = None) -> Ref:
    """
    Create a reference to a DOM element.
    
    Usage:
        input_ref = use_ref()
        
        # In component
        Input(ref=input_ref, placeholder="Type here")
        
        # Later (after hydration)
        input_ref.current.focus()
    
    Args:
        name: Optional name for debugging
    """
    ref_id = f"ref_{uuid.uuid4().hex[:8]}"
    if name:
        ref_id = f"ref_{name}_{uuid.uuid4().hex[:4]}"
    
    ref = Ref(id=ref_id)
    _refs[ref_id] = ref
    
    return ref


# =============================================================================
# Client Effects
# =============================================================================

@dataclass
class ClientEffect:
    """An effect that runs on the client after hydration."""
    id: str
    handler_id: str
    dependencies: List[str] = field(default_factory=list)
    js_code: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "handlerId": self.handler_id,
            "dependencies": self.dependencies,
        }


_client_effects: Dict[str, ClientEffect] = {}


def client_effect(
    fn: Optional[Callable] = None,
    *,
    dependencies: Optional[List[str]] = None,
):
    """
    Decorator for effects that run on the client.
    
    Unlike regular Effect (which tracks dependencies), client_effect
    runs JavaScript code after hydration.
    
    Usage:
        @client_effect
        def setup_scroll_handler():
            # This code runs in the browser
            window.addEventListener("scroll", on_scroll)
            return lambda: window.removeEventListener("scroll", on_scroll)
        
        @client_effect(dependencies=["theme"])
        def apply_theme():
            document.documentElement.classList.toggle("dark", theme() == "dark")
    """
    def decorator(fn: Callable) -> Callable:
        effect_id = f"ceffect_{uuid.uuid4().hex[:8]}"
        handler_id = f"handler_{uuid.uuid4().hex[:8]}"
        
        effect = ClientEffect(
            id=effect_id,
            handler_id=handler_id,
            dependencies=dependencies or [],
        )
        
        _client_effects[effect_id] = effect
        _handlers[handler_id] = fn
        
        # Register with render context
        ctx = get_context()
        if ctx:
            if not hasattr(ctx, 'client_effects'):
                ctx.client_effects = []
            ctx.client_effects.append(effect)
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        
        wrapper._effect_id = effect_id
        wrapper._handler_id = handler_id
        
        return wrapper
    
    if fn is not None:
        return decorator(fn)
    return decorator


# =============================================================================
# Theme Management
# =============================================================================

@dataclass
class ThemeState:
    """Theme state with dark mode support."""
    id: str
    mode: str  # "light", "dark", "system"
    storage_key: str
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "mode": self.mode,
            "storageKey": self.storage_key,
        }


_theme_state: Optional[ThemeState] = None


def use_theme(
    default: str = "system",
    storage_key: str = "theme",
) -> StorageSignal:
    """
    Create a theme signal with dark mode support.
    
    Automatically handles:
    - System preference detection
    - localStorage persistence
    - Flash prevention
    
    Usage:
        theme = use_theme()
        
        # Read current mode
        mode = theme()  # "light", "dark", or "system"
        
        # Set mode
        theme.set("dark")
        
        # Toggle
        def toggle():
            theme.set("dark" if theme() == "light" else "light")
    
    Returns:
        StorageSignal that can be "light", "dark", or "system"
    """
    global _theme_state
    
    signal = use_storage(storage_key, default=default)
    
    _theme_state = ThemeState(
        id=signal.id,
        mode=default,
        storage_key=storage_key,
    )
    
    # Register with render context for special theme handling
    ctx = get_context()
    if ctx:
        ctx.theme_state = _theme_state
    
    return signal


# =============================================================================
# Server-Sent Events (SSE)
# =============================================================================

@dataclass
class SSEHandle:
    """
    Handle for controlling an SSE connection.
    
    The handle provides methods to control the connection from Python,
    which generate JavaScript that executes in the browser.
    """
    id: str
    url: str
    handlers: Dict[str, Callable]
    options: Dict[str, Any] = field(default_factory=dict)
    
    def close(self) -> str:
        """
        Close the SSE connection.
        
        Returns JavaScript code that closes the connection.
        """
        return f"__pynext__.sse.close('{self.id}')"
    
    def reconnect(self) -> str:
        """
        Manually reconnect to the SSE endpoint.
        
        Returns JavaScript code that reconnects.
        """
        return f"__pynext__.sse.reconnect('{self.id}')"
    
    @property
    def is_connected(self) -> str:
        """JavaScript expression that returns connection status."""
        return f"__pynext__.sse.isConnected('{self.id}')"
    
    def to_dict(self) -> dict:
        # Convert handler lambdas to JS
        js_handlers = {}
        for event_name, handler in self.handlers.items():
            if callable(handler):
                # Transpile the lambda to JS
                js_handlers[event_name] = _transpile_sse_handler(handler)
            else:
                js_handlers[event_name] = handler
        
        return {
            "id": self.id,
            "url": self.url,
            "handlers": js_handlers,
            "options": {
                "reconnect": self.options.get("reconnect", True),
                "reconnectDelay": self.options.get("reconnect_delay", 1000),
            },
        }
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        config = json.dumps(self.to_dict())
        return f"__pynext__.sse.connect({config})"


def _transpile_sse_handler(handler: Callable) -> str:
    """
    Transpile a Python handler to JavaScript.
    
    For SSE handlers, we generate JS that updates signals.
    """
    import inspect
    import ast
    
    try:
        source = inspect.getsource(handler)
        # Clean up lambda source
        if 'lambda' in source:
            # Extract the lambda body
            match = source.split('lambda')[1] if 'lambda' in source else source
            # Extract after the colon
            if ':' in match:
                body = match.split(':', 1)[1].strip()
                # Remove trailing comma, paren, etc.
                body = body.rstrip(',)}').strip()
                return _convert_python_expr_to_js(body)
    except (OSError, TypeError):
        pass
    
    # Fallback: return a no-op
    return "function(data) { console.log('SSE event:', data); }"


def _convert_python_expr_to_js(expr: str) -> str:
    """Convert a Python expression to JavaScript for SSE handlers."""
    # Handle Signal.update() pattern
    if '.update(' in expr:
        # notifications.update(lambda n: [data, *n][:50])
        parts = expr.split('.update(', 1)
        signal_name = parts[0].strip()
        
        # Extract the lambda inside update
        inner = parts[1].rstrip(')')
        if inner.startswith('lambda'):
            # Parse lambda: lambda n: [data, *n][:50]
            lambda_parts = inner.split(':', 1)
            if len(lambda_parts) == 2:
                param = lambda_parts[0].replace('lambda', '').strip()
                body = lambda_parts[1].strip()
                
                # Convert Python list operations to JS
                js_body = body
                # [data, *n] -> [data, ...n]
                js_body = js_body.replace('*', '...')
                # [:50] -> .slice(0, 50)
                if '[:' in js_body:
                    js_body = js_body.replace('[:', '.slice(0,').replace(']', ')')
                
                return f"function(data) {{ __pynext__.getSignal('{signal_name}')?.update(({param}) => {js_body}); }}"
    
    # Handle Signal.set() pattern
    if '.set(' in expr:
        parts = expr.split('.set(', 1)
        signal_name = parts[0].strip()
        value = parts[1].rstrip(')')
        return f"function(data) {{ __pynext__.setSignal('{signal_name}', {value}); }}"
    
    # Default: wrap in function
    return f"function(data) {{ {expr}; }}"


_sse_connections: Dict[str, SSEHandle] = {}


def use_event_source(
    url: str,
    handlers: Dict[str, Callable],
    options: Optional[Dict[str, Any]] = None,
) -> SSEHandle:
    """
    Connect to a Server-Sent Events (SSE) endpoint.
    
    SSE allows the server to push real-time updates to the client.
    This hook creates a connection and maps event types to handlers.
    
    Usage:
        # Simple connection
        sse = use_event_source("/api/events", {
            "notification": lambda data: notifications.update(lambda n: [data, *n]),
            "task_update": lambda data: tasks.set(data),
        })
        
        # With reconnection options
        sse = use_event_source("/api/events", handlers, {
            "reconnect": True,
            "reconnect_delay": 2000,  # 2 seconds
        })
        
        # Close connection
        Button(onclick=lambda: sse.close())["Disconnect"]
    
    Args:
        url: The SSE endpoint URL (must be created on your server)
        handlers: Dict mapping event names to handler functions
        options: Connection options:
            - reconnect: Auto-reconnect on error (default: True)
            - reconnect_delay: Delay before reconnect in ms (default: 1000)
    
    Returns:
        SSEHandle with close(), reconnect(), and is_connected
    
    Note:
        The server endpoint must be created separately using @api_route
        and EventStream. See docs/features/SSE.md for full setup.
    """
    connection_id = f"sse_{uuid.uuid4().hex[:8]}"
    
    handle = SSEHandle(
        id=connection_id,
        url=url,
        handlers=handlers,
        options=options or {},
    )
    
    _sse_connections[connection_id] = handle
    
    # Register with render context
    ctx = get_context()
    if ctx:
        if not hasattr(ctx, 'sse_connections'):
            ctx.sse_connections = []
        ctx.sse_connections.append(handle)
    
    return handle


# =============================================================================
# Tab Visibility
# =============================================================================

@dataclass
class VisibilitySignal:
    """
    A signal that tracks tab visibility.
    
    Value is True when the tab is visible, False when hidden.
    """
    id: str
    _value: bool = field(default=True, repr=False)
    
    def __call__(self) -> bool:
        """Read the current visibility state."""
        return self._value
    
    @property
    def value(self) -> bool:
        """Read the current visibility state."""
        return self._value
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": "visibility",
        }
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        return f"__pynext__.browser.initVisibility('{self.id}')"


_visibility_signal: Optional[VisibilitySignal] = None


def use_visibility() -> VisibilitySignal:
    """
    Track whether the browser tab is visible.
    
    Use this to pause expensive operations when the user
    switches to another tab, saving resources.
    
    Usage:
        is_visible = use_visibility()
        
        # Check visibility
        if is_visible.value:
            poll_for_updates()
        
        # Use with client_effect
        @client_effect
        def smart_polling():
            if is_visible():
                start_polling()
            else:
                stop_polling()
    
    Returns:
        VisibilitySignal that is True when tab is active
    
    How it works:
        Browser fires 'visibilitychange' event when user switches tabs.
        This signal automatically updates, triggering reactive updates.
    """
    global _visibility_signal
    
    # Return existing signal if already created (singleton per page)
    if _visibility_signal is not None:
        return _visibility_signal
    
    signal_id = f"visibility_{uuid.uuid4().hex[:8]}"
    
    _visibility_signal = VisibilitySignal(id=signal_id)
    
    # Register with render context
    ctx = get_context()
    if ctx:
        ctx.visibility_signal = _visibility_signal
    
    return _visibility_signal


# =============================================================================
# Network Status
# =============================================================================

@dataclass
class OnlineSignal:
    """
    A signal that tracks network connectivity.
    
    Value is True when online, False when offline.
    """
    id: str
    _value: bool = field(default=True, repr=False)
    
    def __call__(self) -> bool:
        """Read the current online state."""
        return self._value
    
    @property
    def value(self) -> bool:
        """Read the current online state."""
        return self._value
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": "online",
        }
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        return f"__pynext__.browser.initOnline('{self.id}')"


_online_signal: Optional[OnlineSignal] = None


def use_online() -> OnlineSignal:
    """
    Track whether the browser has network connectivity.
    
    Use this to show offline indicators, queue actions for later,
    or disable features that require internet.
    
    Usage:
        is_online = use_online()
        
        # Show offline banner
        if not is_online.value:
            show_offline_indicator()
        
        # Disable submit when offline
        Button(
            disabled=not is_online.value,
            onclick=submit_form
        )["Submit"]
    
    Returns:
        OnlineSignal that is True when connected to network
    
    How it works:
        Browser fires 'online' and 'offline' events when connectivity changes.
        This signal automatically updates, triggering reactive updates.
    """
    global _online_signal
    
    # Return existing signal if already created (singleton per page)
    if _online_signal is not None:
        return _online_signal
    
    signal_id = f"online_{uuid.uuid4().hex[:8]}"
    
    _online_signal = OnlineSignal(id=signal_id)
    
    # Register with render context
    ctx = get_context()
    if ctx:
        ctx.online_signal = _online_signal
    
    return _online_signal


# =============================================================================
# Hydration Data Generation
# =============================================================================

def get_client_hydration_data() -> dict:
    """
    Get all client-side hydration data.
    
    Called during SSR to generate the __PYNEXT_CLIENT__ data.
    """
    return {
        "shortcuts": [s.to_dict() for s in _shortcuts.values()],
        "sequences": [s.to_dict() for s in _sequences.values()],
        "storage": [s.to_dict() for s in _storage_signals.values()],
        "refs": [r.to_dict() for r in _refs.values()],
        "effects": [e.to_dict() for e in _client_effects.values()],
        "theme": _theme_state.to_dict() if _theme_state else None,
        "sse": [c.to_dict() for c in _sse_connections.values()],
        "visibility": _visibility_signal.to_dict() if _visibility_signal else None,
        "online": _online_signal.to_dict() if _online_signal else None,
    }


def reset_client_state() -> None:
    """Reset all client state (useful for testing)."""
    global _theme_state, _visibility_signal, _online_signal
    _shortcuts.clear()
    _sequences.clear()
    _handlers.clear()
    _storage_signals.clear()
    _refs.clear()
    _client_effects.clear()
    _sse_connections.clear()
    _theme_state = None
    _visibility_signal = None
    _online_signal = None


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Keyboard
    "on_keydown",
    "on_key_sequence",
    "register_shortcut",
    "unregister_shortcut",
    "KeyboardShortcut",
    "KeySequence",
    # Storage
    "use_storage",
    "StorageSignal",
    # Refs
    "use_ref",
    "Ref",
    # Effects
    "client_effect",
    "ClientEffect",
    # Theme
    "use_theme",
    "ThemeState",
    # SSE (Server-Sent Events)
    "use_event_source",
    "SSEHandle",
    # Browser APIs
    "use_visibility",
    "VisibilitySignal",
    "use_online",
    "OnlineSignal",
    # Utilities
    "get_client_hydration_data",
    "reset_client_state",
]

