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
# WebSocket
# =============================================================================

@dataclass
class WebSocketHandle:
    """
    Handle for a WebSocket connection.
    
    Provides signals for connection state, messages, and errors,
    plus methods to send messages and control the connection.
    
    This is the SolidJS-style approach: signals update, not components.
    """
    id: str
    url: str
    _connected: bool = field(default=False, repr=False)
    _last_message: Any = field(default=None, repr=False)
    _error: Optional[str] = field(default=None, repr=False)
    _subscribers: List[Callable] = field(default_factory=list, repr=False)
    
    # Configuration
    reconnect: bool = True
    reconnect_interval: int = 3000
    on_open: Optional[Callable] = field(default=None, repr=False)
    on_close: Optional[Callable] = field(default=None, repr=False)
    on_message: Optional[Callable] = field(default=None, repr=False)
    on_error: Optional[Callable] = field(default=None, repr=False)
    
    def connected(self) -> bool:
        """Check if WebSocket is currently connected."""
        return self._connected
    
    def last_message(self) -> Any:
        """Get the most recent message received."""
        return self._last_message
    
    def error(self) -> Optional[str]:
        """Get the last error message, if any."""
        return self._error
    
    def send(self, data: Union[dict, str, bytes]) -> str:
        """
        Send data through the WebSocket.
        
        Returns JavaScript code that sends the message.
        """
        if isinstance(data, dict):
            payload = json.dumps(data)
        else:
            payload = json.dumps(str(data))
        return f"__pynext__.websocket.send('{self.id}', {payload})"
    
    def close(self) -> str:
        """Close the WebSocket connection."""
        return f"__pynext__.websocket.close('{self.id}')"
    
    def reconnect_now(self) -> str:
        """Manually trigger a reconnection."""
        return f"__pynext__.websocket.reconnect('{self.id}')"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "reconnect": self.reconnect,
            "reconnectInterval": self.reconnect_interval,
            "hasOnOpen": self.on_open is not None,
            "hasOnClose": self.on_close is not None,
            "hasOnMessage": self.on_message is not None,
            "hasOnError": self.on_error is not None,
        }
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        config = json.dumps(self.to_dict())
        return f"__pynext__.websocket.connect({config})"


_websocket_connections: Dict[str, WebSocketHandle] = {}


def use_websocket(
    url: str,
    *,
    on_message: Optional[Callable[[Any], None]] = None,
    on_open: Optional[Callable[[], None]] = None,
    on_close: Optional[Callable[[], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    reconnect: bool = True,
    reconnect_interval: int = 3000,
) -> WebSocketHandle:
    """
    Connect to a WebSocket server.
    
    This is THE simplest way to use WebSockets in Python:
    
    Usage:
        # Basic - just URL and message handler
        ws = use_websocket("/api/chat", on_message=handle_message)
        
        # Send messages
        Button(onclick=lambda: ws.send({"text": "Hello!"}))["Send"]
        
        # Check connection state
        if ws.connected():
            show_connected_indicator()
        
        # Full options
        ws = use_websocket(
            url="/api/chat",
            on_message=lambda data: messages.update(lambda m: [*m, data]),
            on_open=lambda: print("Connected!"),
            on_close=lambda: print("Disconnected"),
            on_error=lambda e: print(f"Error: {e}"),
            reconnect=True,
            reconnect_interval=3000,
        )
    
    Args:
        url: WebSocket URL ("/api/ws" becomes "ws://host/api/ws")
        on_message: Called when a message is received
        on_open: Called when connection opens
        on_close: Called when connection closes
        on_error: Called on connection error
        reconnect: Auto-reconnect on disconnect (default: True)
        reconnect_interval: Time between reconnect attempts in ms
    
    Returns:
        WebSocketHandle with send(), close(), connected(), etc.
    
    Why this is better than React:
        - No useEffect/useState boilerplate
        - Signals update, components don't re-render
        - Auto-reconnect built-in
        - Type-safe with full IDE support
    """
    connection_id = f"ws_{uuid.uuid4().hex[:8]}"
    
    handle = WebSocketHandle(
        id=connection_id,
        url=url,
        reconnect=reconnect,
        reconnect_interval=reconnect_interval,
        on_message=on_message,
        on_open=on_open,
        on_close=on_close,
        on_error=on_error,
    )
    
    _websocket_connections[connection_id] = handle
    
    # Register with render context
    ctx = get_context()
    if ctx:
        if not hasattr(ctx, 'websocket_connections'):
            ctx.websocket_connections = []
        ctx.websocket_connections.append(handle)
    
    return handle


# =============================================================================
# Media Query
# =============================================================================

@dataclass
class MediaQuerySignal:
    """
    A signal that tracks a CSS media query match.
    
    Value is True when the query matches, False otherwise.
    Updates automatically when the match state changes.
    """
    id: str
    query: str
    _value: bool = field(default=False, repr=False)
    _subscribers: List[Callable] = field(default_factory=list, repr=False)
    
    def __call__(self) -> bool:
        """Check if the media query currently matches."""
        return self._value
    
    @property
    def matches(self) -> bool:
        """Check if the media query currently matches."""
        return self._value
    
    def subscribe(self, fn: Callable[[bool], None]) -> Callable[[], None]:
        """Subscribe to match state changes."""
        self._subscribers.append(fn)
        return lambda: self._subscribers.remove(fn)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "query": self.query,
            "type": "mediaQuery",
        }
    
    def get_js_init(self) -> str:
        return f"__pynext__.browser.initMediaQuery('{self.id}', '{self.query}')"


_media_queries: Dict[str, MediaQuerySignal] = {}


def use_media_query(query: str) -> MediaQuerySignal:
    """
    Track whether a CSS media query matches.
    
    This is responsive design made stupid simple:
    
    Usage:
        # Check screen size
        is_mobile = use_media_query("(max-width: 768px)")
        
        if is_mobile():
            return MobileNav()
        else:
            return DesktopNav()
        
        # Check user preferences
        prefers_dark = use_media_query("(prefers-color-scheme: dark)")
        reduced_motion = use_media_query("(prefers-reduced-motion: reduce)")
        
        # Common patterns
        is_tablet = use_media_query("(min-width: 768px) and (max-width: 1024px)")
        is_landscape = use_media_query("(orientation: landscape)")
        is_retina = use_media_query("(min-resolution: 2dppx)")
    
    Args:
        query: CSS media query string
    
    Returns:
        MediaQuerySignal that is True when query matches
    
    Why this is better than React:
        - One line, no useEffect/useState
        - Signal updates, no component re-render
        - Built-in memoization (same query = same signal)
    """
    # Check if we already have this query
    for signal in _media_queries.values():
        if signal.query == query:
            return signal
    
    signal_id = f"mq_{uuid.uuid4().hex[:8]}"
    
    signal = MediaQuerySignal(id=signal_id, query=query)
    _media_queries[signal_id] = signal
    
    # Register with render context
    ctx = get_context()
    if ctx:
        if not hasattr(ctx, 'media_queries'):
            ctx.media_queries = []
        ctx.media_queries.append(signal)
    
    return signal


# =============================================================================
# Geolocation
# =============================================================================

@dataclass
class GeolocationHandle:
    """
    Handle for tracking user's geographic location.
    
    All values are signals that update when location changes.
    """
    id: str
    watch: bool = False
    high_accuracy: bool = False
    timeout: int = 10000
    max_age: int = 0
    
    # Location signals (all Optional because location may not be available)
    _latitude: Optional[float] = field(default=None, repr=False)
    _longitude: Optional[float] = field(default=None, repr=False)
    _accuracy: Optional[float] = field(default=None, repr=False)
    _altitude: Optional[float] = field(default=None, repr=False)
    _altitude_accuracy: Optional[float] = field(default=None, repr=False)
    _heading: Optional[float] = field(default=None, repr=False)
    _speed: Optional[float] = field(default=None, repr=False)
    
    # State signals
    _loading: bool = field(default=True, repr=False)
    _error: Optional[str] = field(default=None, repr=False)
    _permission: str = field(default="prompt", repr=False)  # "granted", "denied", "prompt"
    
    def latitude(self) -> Optional[float]:
        """Get current latitude (or None if unavailable)."""
        return self._latitude
    
    def longitude(self) -> Optional[float]:
        """Get current longitude (or None if unavailable)."""
        return self._longitude
    
    def accuracy(self) -> Optional[float]:
        """Get accuracy in meters."""
        return self._accuracy
    
    def altitude(self) -> Optional[float]:
        """Get altitude in meters (if available)."""
        return self._altitude
    
    def heading(self) -> Optional[float]:
        """Get heading in degrees (if moving)."""
        return self._heading
    
    def speed(self) -> Optional[float]:
        """Get speed in meters/second (if moving)."""
        return self._speed
    
    def loading(self) -> bool:
        """Check if location is currently being fetched."""
        return self._loading
    
    def error(self) -> Optional[str]:
        """Get the last error message, if any."""
        return self._error
    
    def permission(self) -> str:
        """Get permission state: 'granted', 'denied', or 'prompt'."""
        return self._permission
    
    def refresh(self) -> str:
        """Manually request a location update."""
        return f"__pynext__.browser.refreshGeolocation('{self.id}')"
    
    def stop(self) -> str:
        """Stop watching location (only for watch mode)."""
        return f"__pynext__.browser.stopGeolocation('{self.id}')"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "watch": self.watch,
            "type": "geolocation",
            "options": {
                "enableHighAccuracy": self.high_accuracy,
                "timeout": self.timeout,
                "maximumAge": self.max_age,
            },
        }
    
    def get_js_init(self) -> str:
        config = json.dumps(self.to_dict())
        return f"__pynext__.browser.initGeolocation({config})"


_geolocation: Optional[GeolocationHandle] = None


def use_geolocation(
    *,
    watch: bool = False,
    high_accuracy: bool = False,
    timeout: int = 10000,
    max_age: int = 0,
) -> GeolocationHandle:
    """
    Track the user's geographic location.
    
    Usage:
        # One-time location fetch
        geo = use_geolocation()
        
        # Continuous tracking
        geo = use_geolocation(watch=True, high_accuracy=True)
        
        # Access location
        if geo.loading():
            return "Getting location..."
        
        if geo.error():
            return f"Error: {geo.error()}"
        
        lat, lon = geo.latitude(), geo.longitude()
        return f"You are at {lat}, {lon}"
    
    Args:
        watch: Continuously track location (default: False)
        high_accuracy: Use GPS for higher accuracy (uses more battery)
        timeout: Max time to wait for location in ms
        max_age: Accept cached location up to this age in ms
    
    Returns:
        GeolocationHandle with signals for all location data
    
    Why this is better than React:
        - All values are reactive signals
        - No effect cleanup needed
        - Permission state included
    """
    global _geolocation
    
    # If watch settings match, return existing
    if _geolocation is not None:
        if _geolocation.watch == watch and _geolocation.high_accuracy == high_accuracy:
            return _geolocation
    
    geo_id = f"geo_{uuid.uuid4().hex[:8]}"
    
    _geolocation = GeolocationHandle(
        id=geo_id,
        watch=watch,
        high_accuracy=high_accuracy,
        timeout=timeout,
        max_age=max_age,
    )
    
    # Register with render context
    ctx = get_context()
    if ctx:
        ctx.geolocation = _geolocation
    
    return _geolocation


# =============================================================================
# Clipboard
# =============================================================================

@dataclass
class ClipboardHandle:
    """
    Handle for clipboard operations.
    
    Provides signals for clipboard state and methods to read/write.
    """
    id: str
    _text: Optional[str] = field(default=None, repr=False)
    _copied: bool = field(default=False, repr=False)
    _supported: bool = field(default=True, repr=False)
    _subscribers: List[Callable] = field(default_factory=list, repr=False)
    
    def text(self) -> Optional[str]:
        """Get the last read clipboard text."""
        return self._text
    
    def copied(self) -> bool:
        """Returns True briefly after a successful copy."""
        return self._copied
    
    def supported(self) -> bool:
        """Check if clipboard API is supported."""
        return self._supported
    
    def copy(self, text: str) -> str:
        """
        Copy text to clipboard.
        
        Returns JavaScript code that performs the copy.
        """
        escaped = json.dumps(text)
        return f"__pynext__.browser.clipboardCopy('{self.id}', {escaped})"
    
    def read(self) -> str:
        """
        Read text from clipboard.
        
        Returns JavaScript code that reads and updates the text signal.
        """
        return f"__pynext__.browser.clipboardRead('{self.id}')"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": "clipboard",
        }
    
    def get_js_init(self) -> str:
        return f"__pynext__.browser.initClipboard('{self.id}')"


_clipboard: Optional[ClipboardHandle] = None


def use_clipboard() -> ClipboardHandle:
    """
    Access the system clipboard.
    
    Usage:
        clipboard = use_clipboard()
        
        # Copy text
        Button(onclick=lambda: clipboard.copy("Hello!"))["Copy"]
        
        # Show feedback
        if clipboard.copied():
            show_toast("Copied!")
        
        # Read clipboard (requires user gesture)
        Button(onclick=lambda: clipboard.read())["Paste"]
        
        if clipboard.text():
            print(f"Clipboard contains: {clipboard.text()}")
    
    Returns:
        ClipboardHandle with copy(), read(), and state signals
    
    Note:
        - copy() works without permissions in most browsers
        - read() requires user permission and a user gesture
    """
    global _clipboard
    
    if _clipboard is not None:
        return _clipboard
    
    clip_id = f"clip_{uuid.uuid4().hex[:8]}"
    
    _clipboard = ClipboardHandle(id=clip_id)
    
    # Register with render context
    ctx = get_context()
    if ctx:
        ctx.clipboard = _clipboard
    
    return _clipboard


# =============================================================================
# Window Size
# =============================================================================

@dataclass
class WindowSize:
    """
    Tracks browser window dimensions.
    
    Both width and height are reactive signals.
    """
    id: str
    _width: int = field(default=0, repr=False)
    _height: int = field(default=0, repr=False)
    _subscribers: List[Callable] = field(default_factory=list, repr=False)
    
    def width(self) -> int:
        """Get current window width in pixels."""
        return self._width
    
    def height(self) -> int:
        """Get current window height in pixels."""
        return self._height
    
    def __call__(self) -> tuple:
        """Get (width, height) tuple."""
        return (self._width, self._height)
    
    def subscribe(self, fn: Callable[[int, int], None]) -> Callable[[], None]:
        """Subscribe to size changes."""
        self._subscribers.append(fn)
        return lambda: self._subscribers.remove(fn)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": "windowSize",
        }
    
    def get_js_init(self) -> str:
        return f"__pynext__.browser.initWindowSize('{self.id}')"


_window_size: Optional[WindowSize] = None


def use_window_size() -> WindowSize:
    """
    Track browser window dimensions.
    
    Usage:
        size = use_window_size()
        
        # Access individual dimensions
        width = size.width()
        height = size.height()
        
        # Or as tuple
        w, h = size()
        
        # Responsive logic
        if size.width() < 768:
            return MobileLayout()
        elif size.width() < 1024:
            return TabletLayout()
        else:
            return DesktopLayout()
        
        # Aspect ratio
        is_portrait = size.height() > size.width()
    
    Returns:
        WindowSize with width() and height() signals
    
    Why this is better than React:
        - No useEffect needed
        - Debounced automatically (RAF)
        - Values update, component doesn't re-render
    """
    global _window_size
    
    if _window_size is not None:
        return _window_size
    
    size_id = f"size_{uuid.uuid4().hex[:8]}"
    
    _window_size = WindowSize(id=size_id)
    
    # Register with render context
    ctx = get_context()
    if ctx:
        ctx.window_size = _window_size
    
    return _window_size


# =============================================================================
# Scroll Position
# =============================================================================

@dataclass
class ScrollPosition:
    """
    Tracks and controls scroll position.
    
    Provides reactive signals for position and methods for scrolling.
    """
    id: str
    _x: int = field(default=0, repr=False)
    _y: int = field(default=0, repr=False)
    _progress: float = field(default=0.0, repr=False)
    _subscribers: List[Callable] = field(default_factory=list, repr=False)
    
    def x(self) -> int:
        """Get horizontal scroll position in pixels."""
        return self._x
    
    def y(self) -> int:
        """Get vertical scroll position in pixels."""
        return self._y
    
    def progress(self) -> float:
        """Get scroll progress from 0.0 (top) to 1.0 (bottom)."""
        return self._progress
    
    def __call__(self) -> tuple:
        """Get (x, y) scroll position tuple."""
        return (self._x, self._y)
    
    def to(self, x: int, y: int, smooth: bool = True) -> str:
        """
        Scroll to a specific position.
        
        Args:
            x: Horizontal scroll position
            y: Vertical scroll position
            smooth: Use smooth scrolling animation
        """
        behavior = "smooth" if smooth else "instant"
        return f"window.scrollTo({{left: {x}, top: {y}, behavior: '{behavior}'}})"
    
    def to_top(self, smooth: bool = True) -> str:
        """Scroll to the top of the page."""
        return self.to(0, 0, smooth)
    
    def to_bottom(self, smooth: bool = True) -> str:
        """Scroll to the bottom of the page."""
        behavior = "smooth" if smooth else "instant"
        return f"window.scrollTo({{top: document.body.scrollHeight, behavior: '{behavior}'}})"
    
    def to_element(self, element_id: str, smooth: bool = True) -> str:
        """Scroll an element into view."""
        behavior = "smooth" if smooth else "instant"
        return f"document.getElementById('{element_id}')?.scrollIntoView({{behavior: '{behavior}'}})"
    
    def subscribe(self, fn: Callable[[int, int], None]) -> Callable[[], None]:
        """Subscribe to scroll position changes."""
        self._subscribers.append(fn)
        return lambda: self._subscribers.remove(fn)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": "scrollPosition",
        }
    
    def get_js_init(self) -> str:
        return f"__pynext__.browser.initScrollPosition('{self.id}')"


_scroll_position: Optional[ScrollPosition] = None


def use_scroll_position() -> ScrollPosition:
    """
    Track and control page scroll position.
    
    Usage:
        scroll = use_scroll_position()
        
        # Read scroll position
        x, y = scroll()
        # or
        y = scroll.y()
        
        # Check scroll progress (0.0 to 1.0)
        if scroll.progress() > 0.5:
            show_back_to_top_button()
        
        # Scroll to position
        Button(onclick=lambda: scroll.to_top())["Back to Top"]
        
        # Scroll to element
        Button(onclick=lambda: scroll.to_element("section-2"))["Go to Section 2"]
        
        # Parallax effects
        header_opacity = 1 - scroll.progress()
    
    Returns:
        ScrollPosition with x(), y(), progress(), and scroll methods
    
    Why this is better than React:
        - RAF-throttled automatically (60fps max)
        - Progress calculated for you
        - Simple scroll methods built-in
    """
    global _scroll_position
    
    if _scroll_position is not None:
        return _scroll_position
    
    scroll_id = f"scroll_{uuid.uuid4().hex[:8]}"
    
    _scroll_position = ScrollPosition(id=scroll_id)
    
    # Register with render context
    ctx = get_context()
    if ctx:
        ctx.scroll_position = _scroll_position
    
    return _scroll_position


# =============================================================================
# Intersection Observer
# =============================================================================

@dataclass
class IntersectionSignal:
    """
    A signal that tracks when an element enters/exits the viewport.
    
    Value is True when the element is visible, False otherwise.
    """
    id: str
    element_id: str
    threshold: float = 0.0
    root_margin: str = "0px"
    _visible: bool = field(default=False, repr=False)
    _ratio: float = field(default=0.0, repr=False)
    _subscribers: List[Callable] = field(default_factory=list, repr=False)
    
    def __call__(self) -> bool:
        """Check if element is visible."""
        return self._visible
    
    @property
    def is_visible(self) -> bool:
        """Check if element is visible."""
        return self._visible
    
    def ratio(self) -> float:
        """Get intersection ratio (0.0 to 1.0)."""
        return self._ratio
    
    def subscribe(self, fn: Callable[[bool], None]) -> Callable[[], None]:
        """Subscribe to visibility changes."""
        self._subscribers.append(fn)
        return lambda: self._subscribers.remove(fn)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "elementId": self.element_id,
            "type": "intersection",
            "options": {
                "threshold": self.threshold,
                "rootMargin": self.root_margin,
            },
        }
    
    def get_js_init(self) -> str:
        config = json.dumps(self.to_dict())
        return f"__pynext__.browser.initIntersection({config})"


_intersections: Dict[str, IntersectionSignal] = {}


def use_intersection(
    element_id: str,
    *,
    threshold: float = 0.0,
    root_margin: str = "0px",
) -> IntersectionSignal:
    """
    Track when an element enters or exits the viewport.
    
    Perfect for lazy loading, animations, and infinite scroll.
    
    Usage:
        # Basic: track when element becomes visible
        is_visible = use_intersection("hero-section")
        
        if is_visible():
            start_animation()
        
        # Lazy loading with threshold
        is_visible = use_intersection(
            "image-container",
            threshold=0.5,      # 50% visible
        )
        
        if is_visible():
            return RealImage()
        else:
            return Placeholder()
        
        # Infinite scroll
        bottom_visible = use_intersection(
            "load-more-trigger",
            root_margin="100px"  # Trigger 100px before visible
        )
        
        if bottom_visible():
            load_more_items()
    
    Args:
        element_id: ID of the DOM element to observe
        threshold: How much of element must be visible (0.0 to 1.0)
        root_margin: Margin around the viewport (CSS-style)
    
    Returns:
        IntersectionSignal that is True when element is visible
    
    Why this is better than React:
        - No ref needed (just use element ID)
        - Automatic cleanup
        - Signal-based, no re-renders
    """
    # Check if we already observe this element
    for signal in _intersections.values():
        if signal.element_id == element_id:
            return signal
    
    signal_id = f"int_{uuid.uuid4().hex[:8]}"
    
    signal = IntersectionSignal(
        id=signal_id,
        element_id=element_id,
        threshold=threshold,
        root_margin=root_margin,
    )
    
    _intersections[signal_id] = signal
    
    # Register with render context
    ctx = get_context()
    if ctx:
        if not hasattr(ctx, 'intersections'):
            ctx.intersections = []
        ctx.intersections.append(signal)
    
    return signal


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
        # New browser APIs
        "websocket": [c.to_dict() for c in _websocket_connections.values()],
        "mediaQueries": [q.to_dict() for q in _media_queries.values()],
        "geolocation": _geolocation.to_dict() if _geolocation else None,
        "clipboard": _clipboard.to_dict() if _clipboard else None,
        "windowSize": _window_size.to_dict() if _window_size else None,
        "scrollPosition": _scroll_position.to_dict() if _scroll_position else None,
        "intersections": [i.to_dict() for i in _intersections.values()],
    }


def reset_client_state() -> None:
    """Reset all client state (useful for testing)."""
    global _theme_state, _visibility_signal, _online_signal
    global _geolocation, _clipboard, _window_size, _scroll_position
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
    # New browser APIs
    _websocket_connections.clear()
    _media_queries.clear()
    _geolocation = None
    _clipboard = None
    _window_size = None
    _scroll_position = None
    _intersections.clear()


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
    # Browser APIs - Basic
    "use_visibility",
    "VisibilitySignal",
    "use_online",
    "OnlineSignal",
    # Browser APIs - WebSocket
    "use_websocket",
    "WebSocketHandle",
    # Browser APIs - Media Query
    "use_media_query",
    "MediaQuerySignal",
    # Browser APIs - Geolocation
    "use_geolocation",
    "GeolocationHandle",
    # Browser APIs - Clipboard
    "use_clipboard",
    "ClipboardHandle",
    # Browser APIs - Window Size
    "use_window_size",
    "WindowSize",
    # Browser APIs - Scroll Position
    "use_scroll_position",
    "ScrollPosition",
    # Browser APIs - Intersection Observer
    "use_intersection",
    "IntersectionSignal",
    # Utilities
    "get_client_hydration_data",
    "reset_client_state",
]

