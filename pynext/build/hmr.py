"""
PyNext Build - Hot Module Replacement

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Implements Hot Module Replacement (HMR) for instant browser updates during
development. When a file changes, only the updated island is replaced -
no full page reload needed!

    from pynext.build.hmr import HMRServer
    
    hmr = HMRServer(port=3001)
    hmr.start()
    
    # When a file changes:
    hmr.notify_change("counter.js", compiled_js)

=============================================================================
WHY THIS EXISTS
=============================================================================

Traditional development workflow:
1. Edit code
2. Save file
3. Wait for full rebuild (500ms+)
4. Full page reload (500ms+)
5. Lose UI state (scroll position, form data, etc.)

With HMR:
1. Edit code
2. Save file
3. Incremental compile (< 50ms)
4. WebSocket push update (< 10ms)
5. Only changed island re-renders
6. UI state is PRESERVED!

Total: < 100ms, no state loss!

=============================================================================
HOW IT WORKS
=============================================================================

1. HMRServer starts a WebSocket server
2. Browser connects via <script> injected in dev mode
3. When file changes, server sends update message
4. Client-side HMR runtime hot-swaps the module
5. Island re-renders with new code, state preserved

Message format:
{
    "type": "update",
    "module": "counter.js",
    "code": "...",
    "timestamp": 1234567890
}

=============================================================================
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable, Any
from pathlib import Path


__all__ = [
    "HMRServer",
    "HMRClient",
    "HMRConfig",
    "generate_hmr_client_script",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class HMRConfig:
    """
    Configuration for HMR server.
    
    Attributes:
        host: Host to bind to
        port: WebSocket port
        reconnect_interval: Client reconnect interval in ms
    """
    host: str = "localhost"
    port: int = 3001
    reconnect_interval: int = 1000


@dataclass
class HMRUpdate:
    """
    Represents a module update.
    
    Attributes:
        module: Module name (e.g., "counter.js")
        code: New JavaScript code
        source_map: Optional source map
        timestamp: When the update occurred
    """
    module: str
    code: str
    source_map: str = ""
    timestamp: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        """Convert to JSON message."""
        return json.dumps({
            "type": "update",
            "module": self.module,
            "code": self.code,
            "sourceMap": self.source_map,
            "timestamp": self.timestamp,
        })


# =============================================================================
# HMR SERVER
# =============================================================================

class HMRServer:
    """
    WebSocket server for Hot Module Replacement.
    
    Sends module updates to connected browsers when files change.
    
    Example:
        hmr = HMRServer(port=3001)
        hmr.start()
        
        # When a file is compiled:
        hmr.notify_update("counter.js", new_js_code)
        
        # Cleanup
        hmr.stop()
    """
    
    def __init__(self, config: Optional[HMRConfig] = None):
        """
        Initialize HMR server.
        
        Args:
            config: Server configuration
        """
        self.config = config or HMRConfig()
        self._clients: Set[Any] = set()  # WebSocket connections
        self._server = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._pending_updates: List[HMRUpdate] = []
    
    def start(self) -> None:
        """
        Start the HMR server in a background thread.
        
        Example:
            hmr = HMRServer()
            hmr.start()
        """
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        
        # Wait for server to be ready
        for _ in range(50):  # 5 seconds max
            if self._server is not None:
                break
            time.sleep(0.1)
    
    def _run_server(self) -> None:
        """Run the WebSocket server (internal)."""
        try:
            import websockets
        except ImportError:
            print("[PyNext HMR] websockets library not installed. HMR disabled.")
            return
        
        async def handler(websocket, path):
            """Handle a WebSocket connection."""
            self._clients.add(websocket)
            try:
                # Send initial connection message
                await websocket.send(json.dumps({
                    "type": "connected",
                    "timestamp": time.time(),
                }))
                
                # Keep connection alive
                async for message in websocket:
                    # Handle client messages (e.g., acknowledgments)
                    try:
                        data = json.loads(message)
                        if data.get("type") == "ping":
                            await websocket.send(json.dumps({"type": "pong"}))
                    except json.JSONDecodeError:
                        pass
                        
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self._clients.discard(websocket)
        
        async def main():
            self._loop = asyncio.get_event_loop()
            async with websockets.serve(
                handler,
                self.config.host,
                self.config.port,
            ) as server:
                self._server = server
                while self._running:
                    # Process pending updates
                    if self._pending_updates:
                        updates = self._pending_updates[:]
                        self._pending_updates.clear()
                        
                        for update in updates:
                            await self._broadcast(update)
                    
                    await asyncio.sleep(0.01)
        
        asyncio.run(main())
    
    async def _broadcast(self, update: HMRUpdate) -> None:
        """Broadcast update to all connected clients."""
        if not self._clients:
            return
        
        message = update.to_json()
        
        # Send to all clients
        disconnected = set()
        for client in self._clients:
            try:
                await client.send(message)
            except Exception:
                disconnected.add(client)
        
        # Remove disconnected clients
        self._clients -= disconnected
    
    def notify_update(
        self,
        module: str,
        code: str,
        source_map: str = "",
    ) -> None:
        """
        Notify clients of a module update.
        
        Args:
            module: Module name (e.g., "counter.js")
            code: New JavaScript code
            source_map: Optional source map
        
        Example:
            hmr.notify_update("counter.js", "export function Counter() {...}")
        """
        update = HMRUpdate(
            module=module,
            code=code,
            source_map=source_map,
        )
        self._pending_updates.append(update)
    
    def notify_reload(self) -> None:
        """
        Force a full page reload on all clients.
        
        Use this for changes that can't be hot-swapped.
        
        Example:
            hmr.notify_reload()
        """
        self._pending_updates.append(HMRUpdate(
            module="__reload__",
            code="",
        ))
    
    def notify_error(self, error: str) -> None:
        """
        Send a compile error to clients.
        
        Args:
            error: Error message
        
        Example:
            hmr.notify_error("Syntax error at line 42")
        """
        # Use a special "error" module
        self._pending_updates.append(HMRUpdate(
            module="__error__",
            code=error,
        ))
    
    def stop(self) -> None:
        """
        Stop the HMR server.
        
        Example:
            hmr.stop()
        """
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        
        self._server = None
        self._clients.clear()
    
    @property
    def client_count(self) -> int:
        """Number of connected clients."""
        return len(self._clients)
    
    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running and self._server is not None


# =============================================================================
# CLIENT-SIDE SCRIPT
# =============================================================================

def generate_hmr_client_script(config: Optional[HMRConfig] = None) -> str:
    """
    Generate the client-side HMR JavaScript.
    
    This script should be injected into HTML pages during development.
    It connects to the HMR server and handles module updates.
    
    Args:
        config: HMR configuration (for host/port)
    
    Returns:
        JavaScript code as a string
    
    Example:
        script = generate_hmr_client_script()
        html += f"<script>{script}</script>"
    """
    config = config or HMRConfig()
    
    return f'''
(function() {{
    const HMR_HOST = "{config.host}";
    const HMR_PORT = {config.port};
    const RECONNECT_INTERVAL = {config.reconnect_interval};
    
    let socket = null;
    let reconnectTimer = null;
    
    function connect() {{
        try {{
            socket = new WebSocket(`ws://${{HMR_HOST}}:${{HMR_PORT}}`);
            
            socket.onopen = function() {{
                console.log('[PyNext HMR] Connected');
            }};
            
            socket.onmessage = function(event) {{
                try {{
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                }} catch (e) {{
                    console.error('[PyNext HMR] Parse error:', e);
                }}
            }};
            
            socket.onclose = function() {{
                console.log('[PyNext HMR] Disconnected, reconnecting...');
                scheduleReconnect();
            }};
            
            socket.onerror = function(error) {{
                console.error('[PyNext HMR] Error:', error);
            }};
            
        }} catch (e) {{
            console.error('[PyNext HMR] Connection failed:', e);
            scheduleReconnect();
        }}
    }}
    
    function scheduleReconnect() {{
        if (reconnectTimer) return;
        reconnectTimer = setTimeout(function() {{
            reconnectTimer = null;
            connect();
        }}, RECONNECT_INTERVAL);
    }}
    
    function handleMessage(data) {{
        switch (data.type) {{
            case 'connected':
                console.log('[PyNext HMR] Ready');
                break;
                
            case 'update':
                handleUpdate(data);
                break;
                
            case 'pong':
                // Heartbeat response
                break;
        }}
    }}
    
    function handleUpdate(data) {{
        const module = data.module;
        const code = data.code;
        
        if (module === '__reload__') {{
            console.log('[PyNext HMR] Full reload requested');
            location.reload();
            return;
        }}
        
        if (module === '__error__') {{
            console.error('[PyNext HMR] Compile error:', code);
            showErrorOverlay(code);
            return;
        }}
        
        console.log('[PyNext HMR] Updating:', module);
        hideErrorOverlay();
        
        try {{
            // Create a blob URL for the new module
            const blob = new Blob([code], {{ type: 'application/javascript' }});
            const url = URL.createObjectURL(blob);
            
            // Import the new module
            import(url).then(function(newModule) {{
                // Find and update the island
                const islandName = module.replace('.js', '');
                const islands = document.querySelectorAll(`[data-pynext-island="${{islandName}}"]`);
                
                if (islands.length > 0) {{
                    islands.forEach(function(el) {{
                        // Re-render the island with new code
                        if (window.__pynext__ && window.__pynext__.islands) {{
                            const island = window.__pynext__.islands[islandName];
                            if (island && island.update) {{
                                island.update(newModule);
                            }}
                        }}
                    }});
                    console.log('[PyNext HMR] Updated', islands.length, 'instances of', islandName);
                }} else {{
                    // No specific islands, trigger full re-render
                    console.log('[PyNext HMR] No islands found, reloading');
                    location.reload();
                }}
                
                URL.revokeObjectURL(url);
                
            }}).catch(function(error) {{
                console.error('[PyNext HMR] Module load error:', error);
                showErrorOverlay(error.message);
            }});
            
        }} catch (e) {{
            console.error('[PyNext HMR] Update error:', e);
            showErrorOverlay(e.message);
        }}
    }}
    
    function showErrorOverlay(message) {{
        let overlay = document.getElementById('pynext-error-overlay');
        if (!overlay) {{
            overlay = document.createElement('div');
            overlay.id = 'pynext-error-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.85);
                color: #ff5555;
                font-family: monospace;
                font-size: 14px;
                padding: 20px;
                z-index: 999999;
                overflow: auto;
            `;
            document.body.appendChild(overlay);
        }}
        overlay.innerHTML = `
            <h2 style="color: #ff5555; margin: 0 0 20px 0;">PyNext Compile Error</h2>
            <pre style="white-space: pre-wrap;">${{message}}</pre>
            <p style="color: #888; margin-top: 20px;">Fix the error and save to update.</p>
        `;
        overlay.style.display = 'block';
    }}
    
    function hideErrorOverlay() {{
        const overlay = document.getElementById('pynext-error-overlay');
        if (overlay) {{
            overlay.style.display = 'none';
        }}
    }}
    
    // Start heartbeat
    setInterval(function() {{
        if (socket && socket.readyState === WebSocket.OPEN) {{
            socket.send(JSON.stringify({{ type: 'ping' }}));
        }}
    }}, 30000);
    
    // Initial connection
    connect();
}})();
'''


# =============================================================================
# UTILITY CLASS
# =============================================================================

class HMRClient:
    """
    Standalone HMR client for integration with other servers.
    
    Use this when you want to manage the WebSocket connection yourself.
    
    Example:
        client = HMRClient()
        client.on_update(lambda m: print(f"Updated: {m.module}"))
        client.connect()
    """
    
    def __init__(self, config: Optional[HMRConfig] = None):
        self.config = config or HMRConfig()
        self._callbacks: List[Callable[[HMRUpdate], None]] = []
    
    def on_update(self, callback: Callable[[HMRUpdate], None]) -> None:
        """Register a callback for updates."""
        self._callbacks.append(callback)
    
    def send_update(self, update: HMRUpdate) -> None:
        """Send an update to all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(update)
            except Exception as e:
                print(f"[PyNext HMR] Callback error: {e}")

