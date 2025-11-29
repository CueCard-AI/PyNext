"""
Development server with fast file watching.

Features:
- Sub-50ms reload times
- WebSocket-based hot reload
- Intelligent change detection
- CSS hot swapping
- Automatic reconnection

Example:
    # Start dev server
    server = DevServer(Path("."))
    await server.start()
    
    # Or use CLI
    pynext dev

Why This Matters:
    Fast feedback is essential for developer productivity.
    This server watches for file changes and pushes updates
    to the browser instantly via WebSocket.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import asyncio
import json
import time

from pynext.server.watcher import FileWatcher, FileChange, ChangeType


# ============================================
# Dev Client Script
# ============================================

DEV_CLIENT_SCRIPT = """
/**
 * PyNext Dev Client
 * 
 * Handles hot reloading during development.
 * Automatically injected by dev server.
 */
(function() {
  'use strict';
  
  // Config
  const WS_URL = 'ws://' + location.host + '/__pynext/ws';
  const RECONNECT_DELAY = 1000;
  const MAX_RECONNECT_ATTEMPTS = 10;
  
  let ws = null;
  let reconnectTimer = null;
  let reconnectAttempts = 0;
  
  // Overlay for connection status
  function showOverlay(message) {
    let overlay = document.getElementById('__pynext_overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = '__pynext_overlay';
      overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;padding:8px 16px;background:#1e293b;color:#f1f5f9;font-family:monospace;font-size:13px;z-index:999999;text-align:center;';
      document.body.appendChild(overlay);
    }
    overlay.textContent = message;
    overlay.style.display = 'block';
  }
  
  function hideOverlay() {
    const overlay = document.getElementById('__pynext_overlay');
    if (overlay) overlay.style.display = 'none';
  }
  
  // Connect to dev server
  function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) return;
    
    ws = new WebSocket(WS_URL);
    
    ws.onopen = function() {
      console.log('[PyNext] Dev mode connected');
      reconnectAttempts = 0;
      hideOverlay();
    };
    
    ws.onmessage = function(event) {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (e) {
        console.error('[PyNext] Invalid message:', e);
      }
    };
    
    ws.onclose = function() {
      console.log('[PyNext] Connection lost');
      
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        showOverlay('[PyNext] Reconnecting... (' + reconnectAttempts + '/' + MAX_RECONNECT_ATTEMPTS + ')');
        reconnectTimer = setTimeout(connect, RECONNECT_DELAY);
      } else {
        showOverlay('[PyNext] Connection lost. Refresh to reconnect.');
      }
    };
    
    ws.onerror = function() {
      ws.close();
    };
  }
  
  // Handle reload messages
  function handleMessage(data) {
    if (data.type !== 'reload') return;
    
    console.log('[PyNext] ' + data.reload_type + ' reload: ' + data.path);
    
    const start = performance.now();
    
    switch (data.reload_type) {
      case 'css':
        reloadCSS();
        break;
      case 'hot':
        hotReload();
        break;
      case 'none':
        // API change - no visual reload needed
        console.log('[PyNext] API updated (no reload needed)');
        break;
      case 'full':
      default:
        fullReload();
    }
    
    if (data.reload_type !== 'full') {
      const elapsed = performance.now() - start;
      console.log('[PyNext] Reload completed in ' + elapsed.toFixed(1) + 'ms');
    }
  }
  
  // CSS hot swap - instant, no flash
  function reloadCSS() {
    const links = document.querySelectorAll('link[rel="stylesheet"]');
    links.forEach(function(link) {
      if (!link.href) return;
      const url = new URL(link.href);
      url.searchParams.set('_pynext_t', Date.now());
      link.href = url.toString();
    });
    
    // Also handle inline styles in <style> tags with data-file attribute
    const styles = document.querySelectorAll('style[data-pynext-file]');
    styles.forEach(function(style) {
      const file = style.getAttribute('data-pynext-file');
      fetch(file + '?_t=' + Date.now())
        .then(function(r) { return r.text(); })
        .then(function(css) { style.textContent = css; });
    });
  }
  
  // Hot reload - swap content without full refresh
  function hotReload() {
    fetch(location.href, { 
      cache: 'no-store',
      headers: { 'X-PyNext-Hot-Reload': '1' }
    })
      .then(function(r) { 
        if (!r.ok) throw new Error('Failed to fetch');
        return r.text(); 
      })
      .then(function(html) {
        const parser = new DOMParser();
        const newDoc = parser.parseFromString(html, 'text/html');
        
        // Swap body content
        // Use morphdom if available for minimal DOM changes
        if (window.morphdom) {
          morphdom(document.body, newDoc.body, {
            onBeforeElUpdated: function(fromEl, toEl) {
              // Preserve focus
              if (fromEl === document.activeElement) {
                toEl.focus();
              }
              return true;
            }
          });
        } else {
          // Fallback: simple innerHTML swap
          document.body.innerHTML = newDoc.body.innerHTML;
        }
        
        // Update title if changed
        if (newDoc.title !== document.title) {
          document.title = newDoc.title;
        }
        
        // Re-initialize PyNext runtime
        if (window.__pynext__ && window.__pynext__.init) {
          window.__pynext__.init();
        }
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('pynext:reload', { 
          detail: { type: 'hot' } 
        }));
      })
      .catch(function(err) {
        console.error('[PyNext] Hot reload failed, doing full reload:', err);
        fullReload();
      });
  }
  
  // Full page reload
  function fullReload() {
    location.reload();
  }
  
  // Heartbeat to keep connection alive
  function heartbeat() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
    }
  }
  
  // Start
  connect();
  setInterval(heartbeat, 30000);
  
  // Expose for debugging
  window.__pynext_dev__ = {
    reconnect: connect,
    reload: fullReload,
    hotReload: hotReload,
    reloadCSS: reloadCSS
  };
})();
"""


# ============================================
# Dev Server
# ============================================

class DevServer:
    """
    Development server with hot reloading.
    
    Features:
    - Rust-based file watching (watchfiles)
    - WebSocket push for instant updates
    - Intelligent reload classification
    - CSS hot swapping
    - Automatic reconnection
    
    Attributes:
        root: Project root directory
        port: Server port (default 8000)
        host: Server host (default 0.0.0.0)
    
    Example:
        # Basic usage
        server = DevServer(Path("."))
        await server.start()
        
        # With custom port
        server = DevServer(Path("."), port=3000)
        await server.start()
    """
    
    def __init__(
        self,
        root: Path,
        port: int = 8000,
        host: str = "0.0.0.0",
    ):
        """
        Initialize dev server.
        
        Args:
            root: Project root directory
            port: Server port
            host: Server host
        """
        self.root = Path(root).resolve()
        self.port = port
        self.host = host
        self.watcher = FileWatcher(root)
        self._websockets: Set = set()
        self._reload_count = 0
        self._last_reload_time = 0.0
        self._app = None
    
    async def start(self):
        """
        Start the development server.
        
        Starts both the HTTP server and file watcher.
        """
        try:
            import uvicorn
        except ImportError:
            raise ImportError(
                "uvicorn is required for the dev server.\n"
                "Install with: pip install uvicorn"
            )
        
        # Create app
        self._app = self._create_app()
        
        # Start file watcher in background
        watch_task = asyncio.create_task(self._watch_files())
        
        # Configure and run server
        config = uvicorn.Config(
            self._app,
            host=self.host,
            port=self.port,
            log_level="info",
            reload=False,  # We handle our own reloading
        )
        server = uvicorn.Server(config)
        
        try:
            await server.serve()
        finally:
            self.watcher.stop()
            watch_task.cancel()
    
    def _create_app(self):
        """Create FastAPI app with dev endpoints."""
        try:
            from fastapi import FastAPI, WebSocket, WebSocketDisconnect
            from fastapi.responses import Response
        except ImportError:
            raise ImportError(
                "FastAPI is required for the dev server.\n"
                "Install with: pip install fastapi"
            )
        
        # Import the main app creator
        from pynext.server.app import PyNextApp
        
        # Create main PyNext app
        pynext_app = PyNextApp(
            pages_dir=str(self.root / "pages"),
            static_dir=str(self.root / "public"),
            debug=True,
        )
        app = pynext_app.app
        
        # Store reference
        dev_server = self
        
        # WebSocket endpoint for hot reload
        @app.websocket("/__pynext/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            dev_server._websockets.add(websocket)
            
            try:
                while True:
                    # Receive messages (heartbeat, etc.)
                    data = await websocket.receive_text()
                    try:
                        msg = json.loads(data)
                        if msg.get("type") == "ping":
                            await websocket.send_text(json.dumps({"type": "pong"}))
                    except json.JSONDecodeError:
                        pass
            except WebSocketDisconnect:
                dev_server._websockets.discard(websocket)
            except Exception:
                dev_server._websockets.discard(websocket)
        
        # Dev client script endpoint
        @app.get("/__pynext/dev-client.js")
        async def dev_client_script():
            return Response(
                content=DEV_CLIENT_SCRIPT,
                media_type="application/javascript",
            )
        
        # Dev status endpoint
        @app.get("/__pynext/status")
        async def dev_status():
            return {
                "status": "running",
                "reload_count": dev_server._reload_count,
                "last_reload_ms": dev_server._last_reload_time,
                "connected_clients": len(dev_server._websockets),
            }
        
        return app
    
    async def _watch_files(self):
        """Watch files and broadcast changes."""
        print(f"[PyNext] Watching for changes in {self.root}")
        
        try:
            async for change in self.watcher.watch():
                start_time = time.perf_counter()
                
                # Log change
                print(f"[PyNext] {change.relative_path} → {change.reload_type} reload")
                
                # Broadcast to all connected clients
                await self._broadcast_change(change)
                
                # Track timing
                elapsed = (time.perf_counter() - start_time) * 1000
                self._reload_count += 1
                self._last_reload_time = elapsed
                
                print(f"[PyNext] Reload #{self._reload_count} broadcast in {elapsed:.1f}ms")
                
        except asyncio.CancelledError:
            print("[PyNext] File watcher stopped")
        except Exception as e:
            print(f"[PyNext] Watcher error: {e}")
    
    async def _broadcast_change(self, change: FileChange):
        """
        Broadcast change to all WebSocket clients.
        
        Args:
            change: File change event
        """
        message = {
            "type": "reload",
            "reload_type": change.reload_type,
            "path": change.relative_path,
            "change_type": change.change_type.value,
            "is_delete": change.is_delete,
            "timestamp": time.time(),
        }
        
        json_msg = json.dumps(message)
        
        # Broadcast to all clients
        disconnected = set()
        for ws in self._websockets:
            try:
                await ws.send_text(json_msg)
            except Exception:
                disconnected.add(ws)
        
        # Clean up disconnected clients
        self._websockets -= disconnected
        
        if disconnected:
            print(f"[PyNext] Cleaned up {len(disconnected)} disconnected client(s)")
    
    @property
    def connected_clients(self) -> int:
        """Get number of connected WebSocket clients."""
        return len(self._websockets)


# ============================================
# Convenience Functions
# ============================================

def run_dev_server(
    pages_dir: str = "pages",
    static_dir: str = "public",
    host: str = "0.0.0.0",
    port: int = 8000,
):
    """
    Run development server with hot reloading.
    
    This is the main entry point for the dev server.
    Called by the CLI: `pynext dev`
    
    Args:
        pages_dir: Directory containing pages
        static_dir: Directory containing static files
        host: Server host
        port: Server port
    
    Example:
        # From CLI
        pynext dev
        
        # Programmatically
        run_dev_server(port=3000)
    """
    import asyncio
    
    # Determine project root from pages_dir
    pages_path = Path(pages_dir)
    if pages_path.is_absolute():
        root = pages_path.parent
    else:
        root = Path.cwd()
    
    print(f"\n[PyNext] Starting development server...")
    print(f"  → http://localhost:{port}")
    print(f"  → Hot reload enabled")
    print(f"  → Watching for changes...\n")
    
    server = DevServer(root, port=port, host=host)
    asyncio.run(server.start())


async def run_dev_server_async(
    root: str = ".",
    port: int = 8000,
    host: str = "0.0.0.0",
):
    """
    Async version of run_dev_server.
    
    Args:
        root: Project root directory
        port: Server port
        host: Server host
    
    Example:
        await run_dev_server_async()
    """
    server = DevServer(Path(root), port=port, host=host)
    await server.start()


def get_dev_client_script() -> str:
    """
    Get the dev client JavaScript.
    
    Returns the script that handles hot reloading in the browser.
    
    Returns:
        JavaScript code as string
    """
    return DEV_CLIENT_SCRIPT


def get_dev_script_tag() -> str:
    """
    Get a script tag for the dev client.
    
    Returns:
        HTML script tag
    """
    return '<script src="/__pynext/dev-client.js" defer></script>'
