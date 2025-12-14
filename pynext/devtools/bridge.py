"""
CDP Bridge - Chrome DevTools Protocol WebSocket Connection.

This module provides a WebSocket bridge to Chrome's DevTools Protocol (CDP).
CDP allows programmatic control of Chrome, including:

- Capturing console output
- Monitoring network requests
- Taking screenshots
- Inspecting the DOM
- Executing JavaScript

Why CDP?
    CDP is the same protocol that Chrome DevTools uses. It provides
    complete visibility into browser behavior without requiring
    browser extensions or page modifications.

How It Works:
    1. Chrome launches with --remote-debugging-port=9222
    2. We connect to ws://localhost:9222/devtools/page/{pageId}
    3. We send CDP commands and receive events via WebSocket
    4. Events are parsed and forwarded to our capture system

Example:
    bridge = CDPBridge()
    await bridge.connect("ws://localhost:9222/devtools/page/ABC123")
    await bridge.enable_domains()
    
    # Listen for console messages
    async for event in bridge.events():
        if event["method"] == "Console.messageAdded":
            print(event["params"]["message"]["text"])

CDP Documentation:
    https://chromedevtools.github.io/devtools-protocol/
"""

from __future__ import annotations

import asyncio
import json
import base64
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, AsyncIterator
from pathlib import Path


@dataclass
class CDPMessage:
    """
    A message from Chrome DevTools Protocol.
    
    CDP messages come in two forms:
    1. Responses to commands we send (have "id" field)
    2. Events from subscribed domains (have "method" field)
    
    Attributes:
        id: Command ID for responses (None for events)
        method: Event type like "Console.messageAdded"
        params: Event data or command result
        error: Error info if command failed
    """
    id: Optional[int] = None
    method: Optional[str] = None
    params: dict = field(default_factory=dict)
    error: Optional[dict] = None
    
    @classmethod
    def from_json(cls, data: dict) -> "CDPMessage":
        """Parse a CDP message from JSON."""
        # CDP uses "result" for command responses and "params" for events
        params = data.get("result") or data.get("params", {})
        return cls(
            id=data.get("id"),
            method=data.get("method"),
            params=params,
            error=data.get("error"),
        )
    
    @property
    def is_event(self) -> bool:
        """True if this is an event (not a command response)."""
        return self.method is not None
    
    @property
    def is_response(self) -> bool:
        """True if this is a command response."""
        return self.id is not None
    
    @property
    def is_error(self) -> bool:
        """True if this is an error response."""
        return self.error is not None


class CDPBridge:
    """
    WebSocket bridge to Chrome DevTools Protocol.
    
    This class manages the WebSocket connection to Chrome and provides
    methods to send commands and receive events.
    
    The bridge handles:
    - Connection establishment and reconnection
    - Command/response correlation via message IDs
    - Event subscription for multiple CDP domains
    - Screenshot and DOM snapshot capture
    
    Attributes:
        ws_url: WebSocket URL to Chrome debugging endpoint
        connected: Whether currently connected
        domains_enabled: Set of enabled CDP domains
    
    Example:
        async with CDPBridge() as bridge:
            await bridge.connect("ws://localhost:9222/devtools/page/ABC")
            await bridge.enable_domains()
            
            screenshot = await bridge.take_screenshot()
            with open("screen.png", "wb") as f:
                f.write(screenshot)
    """
    
    def __init__(self):
        """Initialize the CDP bridge."""
        self._ws = None
        self._ws_url: Optional[str] = None
        self._connected = False
        self._command_id = 0
        self._pending_commands: dict[int, asyncio.Future] = {}
        self._event_callbacks: list[Callable[[CDPMessage], None]] = []
        self._domains_enabled: set[str] = set()
        self._receive_task: Optional[asyncio.Task] = None
    
    @property
    def connected(self) -> bool:
        """Check if connected to Chrome."""
        return self._connected and self._ws is not None
    
    @property
    def domains_enabled(self) -> set[str]:
        """Get set of enabled CDP domains."""
        return self._domains_enabled.copy()
    
    async def connect(self, ws_url: str) -> None:
        """
        Connect to Chrome via WebSocket.
        
        Args:
            ws_url: WebSocket URL from Chrome's /json/version endpoint
                    e.g., "ws://localhost:9222/devtools/page/ABC123"
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets package required for AI DevTools.\n"
                "Install with: pip install websockets>=12.0"
            )
        
        self._ws_url = ws_url
        try:
            self._ws = await websockets.connect(
                ws_url,
                max_size=50 * 1024 * 1024,  # 50MB for large screenshots
                ping_interval=30,
                ping_timeout=10,
            )
            self._connected = True
            
            # Start receiving messages in background
            self._receive_task = asyncio.create_task(self._receive_loop())
            
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to Chrome: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Chrome."""
        self._connected = False
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        self._domains_enabled.clear()
        self._pending_commands.clear()
    
    async def __aenter__(self) -> "CDPBridge":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
    
    async def send_command(
        self,
        method: str,
        params: Optional[dict] = None,
        timeout: float = 30.0,
    ) -> dict:
        """
        Send a CDP command and wait for response.
        
        Args:
            method: CDP method like "Page.captureScreenshot"
            params: Method parameters
            timeout: Max seconds to wait for response
        
        Returns:
            Response result dict
        
        Raises:
            ConnectionError: If not connected
            TimeoutError: If response not received in time
            RuntimeError: If CDP returns an error
        
        Example:
            # Take a screenshot
            result = await bridge.send_command(
                "Page.captureScreenshot",
                {"format": "png", "quality": 80}
            )
            image_data = base64.b64decode(result["data"])
        """
        if not self.connected:
            raise ConnectionError("Not connected to Chrome")
        
        self._command_id += 1
        command_id = self._command_id
        
        message = {
            "id": command_id,
            "method": method,
            "params": params or {},
        }
        
        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_commands[command_id] = future
        
        try:
            await self._ws.send(json.dumps(message))
            result = await asyncio.wait_for(future, timeout=timeout)
            
            if isinstance(result, dict) and "error" in result:
                raise RuntimeError(f"CDP error: {result['error']}")
            
            return result
            
        except asyncio.TimeoutError:
            self._pending_commands.pop(command_id, None)
            raise TimeoutError(f"CDP command {method} timed out")
        
        finally:
            self._pending_commands.pop(command_id, None)
    
    async def _receive_loop(self) -> None:
        """Background task to receive WebSocket messages."""
        try:
            async for raw_message in self._ws:
                try:
                    data = json.loads(raw_message)
                    message = CDPMessage.from_json(data)
                    
                    if message.is_response:
                        # Match to pending command
                        future = self._pending_commands.get(message.id)
                        if future and not future.done():
                            if message.is_error:
                                future.set_result({"error": message.error})
                            else:
                                future.set_result(message.params)
                    
                    if message.is_event:
                        # Notify event callbacks
                        for callback in self._event_callbacks:
                            try:
                                callback(message)
                            except Exception:
                                pass  # Don't let callback errors break the loop
                
                except json.JSONDecodeError:
                    pass  # Ignore malformed messages
                    
        except asyncio.CancelledError:
            raise
        except Exception:
            self._connected = False
    
    def on_event(self, callback: Callable[[CDPMessage], None]) -> None:
        """
        Register a callback for CDP events.
        
        The callback will be called for every CDP event (not responses).
        Multiple callbacks can be registered.
        
        Args:
            callback: Function that takes a CDPMessage
        
        Example:
            def handle_console(msg: CDPMessage):
                if msg.method == "Console.messageAdded":
                    print(msg.params["message"]["text"])
            
            bridge.on_event(handle_console)
        """
        self._event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[CDPMessage], None]) -> None:
        """Remove a previously registered event callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)
    
    async def enable_domains(self) -> None:
        """
        Enable CDP domains for event capture.
        
        Enables the following domains:
        - Console: Console messages and errors
        - Network: HTTP requests and responses
        - Page: Navigation and lifecycle events
        - Runtime: JavaScript execution and exceptions
        - DOM: Document structure changes
        - Input: Mouse and keyboard events
        
        This must be called after connect() to start receiving events.
        """
        domains = [
            "Console",
            "Network",
            "Page",
            "Runtime",
            "DOM",
            "Log",
        ]
        
        for domain in domains:
            try:
                await self.send_command(f"{domain}.enable", timeout=5.0)
                self._domains_enabled.add(domain)
            except Exception:
                pass  # Some domains may not be available
    
    async def take_screenshot(
        self,
        format: str = "png",
        quality: int = 80,
        full_page: bool = False,
    ) -> bytes:
        """
        Take a screenshot of the current page.
        
        Args:
            format: Image format ("png" or "jpeg")
            quality: JPEG quality (1-100, ignored for PNG)
            full_page: Capture full scrollable page vs viewport
        
        Returns:
            Screenshot as bytes
        
        Example:
            screenshot = await bridge.take_screenshot()
            Path("screenshot.png").write_bytes(screenshot)
        """
        params = {"format": format}
        
        if format == "jpeg":
            params["quality"] = quality
        
        if full_page:
            params["captureBeyondViewport"] = True
        
        result = await self.send_command("Page.captureScreenshot", params)
        return base64.b64decode(result.get("data", ""))
    
    async def get_dom_snapshot(self) -> str:
        """
        Get the full HTML of the current page.
        
        Returns:
            HTML string of the document
        
        Example:
            html = await bridge.get_dom_snapshot()
            Path("snapshot.html").write_text(html)
        """
        # Get the document root
        result = await self.send_command("DOM.getDocument", {"depth": -1})
        root_id = result.get("root", {}).get("nodeId")
        
        if not root_id:
            return "<html></html>"
        
        # Get outer HTML
        result = await self.send_command(
            "DOM.getOuterHTML",
            {"nodeId": root_id}
        )
        
        return result.get("outerHTML", "<html></html>")
    
    async def execute_script(self, script: str) -> Any:
        """
        Execute JavaScript in the page context.
        
        Args:
            script: JavaScript code to execute
        
        Returns:
            Return value of the script (JSON-serializable values only)
        
        Example:
            title = await bridge.execute_script("document.title")
            signals = await bridge.execute_script("Object.keys(__pynext__.signals)")
        """
        result = await self.send_command(
            "Runtime.evaluate",
            {
                "expression": script,
                "returnByValue": True,
                "awaitPromise": True,
            }
        )
        
        if "exceptionDetails" in result:
            raise RuntimeError(f"Script error: {result['exceptionDetails']}")
        
        return result.get("result", {}).get("value")
    
    async def get_element_at_position(self, x: int, y: int) -> Optional[dict]:
        """
        Get element information at screen coordinates.
        
        Args:
            x: X coordinate (pixels from left)
            y: Y coordinate (pixels from top)
        
        Returns:
            Dict with element info (tagName, id, classes, selector) or None
        """
        try:
            result = await self.send_command(
                "DOM.getNodeForLocation",
                {"x": x, "y": y}
            )
            
            node_id = result.get("nodeId") or result.get("backendNodeId")
            if not node_id:
                return None
            
            # Get node details
            if "nodeId" in result:
                node_result = await self.send_command(
                    "DOM.describeNode",
                    {"nodeId": node_id}
                )
            else:
                node_result = await self.send_command(
                    "DOM.describeNode",
                    {"backendNodeId": node_id}
                )
            
            node = node_result.get("node", {})
            
            # Build a CSS selector
            attrs = {}
            raw_attrs = node.get("attributes", [])
            for i in range(0, len(raw_attrs), 2):
                attrs[raw_attrs[i]] = raw_attrs[i + 1]
            
            tag = node.get("localName", "div")
            selector = tag
            if attrs.get("id"):
                selector = f"#{attrs['id']}"
            elif attrs.get("class"):
                selector = f"{tag}.{attrs['class'].split()[0]}"
            
            return {
                "tagName": tag,
                "id": attrs.get("id", ""),
                "classes": attrs.get("class", "").split(),
                "selector": selector,
                "nodeId": node_id,
                "attributes": attrs,
            }
            
        except Exception:
            return None
    
    async def highlight_element(
        self,
        selector: str,
        color: str = "rgba(255, 0, 0, 0.3)",
    ) -> None:
        """
        Highlight an element on the page (for screenshots).
        
        Args:
            selector: CSS selector of element to highlight
            color: Highlight color (CSS color value)
        """
        script = f"""
        (function() {{
            const el = document.querySelector({json.dumps(selector)});
            if (el) {{
                el.style.outline = "3px solid red";
                el.style.outlineOffset = "2px";
            }}
        }})();
        """
        await self.execute_script(script)
    
    async def clear_highlights(self) -> None:
        """Remove all element highlights."""
        script = """
        document.querySelectorAll('*').forEach(el => {
            el.style.outline = '';
            el.style.outlineOffset = '';
        });
        """
        await self.execute_script(script)

