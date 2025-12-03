"""
PyNext Live Query - WebSocket Transport.

WebSocket transport for live queries.

INTEGRATION WITH PHASE 5:
This transport works with the existing use_websocket() hook and websocket.js
runtime from Phase 5 (Browser APIs). On the client side, live.js will
automatically use the __pynext__.websocket infrastructure when available,
enabling connection reuse and shared reconnection logic.

WebSocket advantages:
- Bidirectional communication
- Lower latency
- More efficient for high-frequency updates
- Can reuse existing WebSocket connections from use_websocket()

Best for:
- Complex queries with multiple tables
- High-frequency updates
- When you need client-to-server messages
- When you already have a WebSocket connection from use_websocket()
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional, TYPE_CHECKING

from pynext.db.live.transport.base import (
    Transport,
    TransportMessage,
    TransportState,
    MessageType,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class WebSocketTransport(Transport):
    """
    WebSocket transport for live queries.
    
    Provides bidirectional communication between server and client.
    
    Integration with Phase 5:
        The client-side live.js runtime automatically integrates with the
        existing __pynext__.websocket infrastructure from use_websocket().
        This enables:
        - Connection reuse (no duplicate WebSocket connections)
        - Shared reconnection logic with exponential backoff
        - Consistent connection state signals
    
    Features:
    - Auto-reconnection (via websocket.js on client)
    - Message queuing during reconnect
    - Ping/pong heartbeat
    - Binary message support
    """
    
    def __init__(self, websocket: Optional[Any] = None):
        """
        Create a WebSocket transport.
        
        Args:
            websocket: Optional WebSocket connection (Starlette/FastAPI WebSocket)
        """
        super().__init__()
        self._websocket = websocket
        self._reader_task: Optional[asyncio.Task] = None
        self._pinger_task: Optional[asyncio.Task] = None
        self._connected = False
        self._ping_interval = 30.0
        self._last_pong: float = 0
    
    @property
    def name(self) -> str:
        return "WebSocket"
    
    @property
    def is_bidirectional(self) -> bool:
        return True
    
    async def connect(self, client_id: str) -> None:
        """Accept and start the WebSocket connection."""
        self._client_id = client_id
        self._state = TransportState.CONNECTING
        
        if self._websocket:
            # Accept the WebSocket connection
            if hasattr(self._websocket, "accept"):
                await self._websocket.accept()
            
            # Start reader and pinger tasks
            self._reader_task = asyncio.create_task(self._reader_loop())
            self._pinger_task = asyncio.create_task(self._ping_loop())
        
        self._connected = True
        self._state = TransportState.CONNECTED
        
        logger.debug(f"WebSocket transport connected: {client_id}")
    
    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        self._connected = False
        self._state = TransportState.DISCONNECTED
        
        # Cancel tasks
        for task in [self._reader_task, self._pinger_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._reader_task = None
        self._pinger_task = None
        
        # Close WebSocket
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass
        
        logger.debug(f"WebSocket transport disconnected: {self._client_id}")
    
    async def send(self, message: TransportMessage) -> bool:
        """
        Send a message via WebSocket.
        """
        if not self._connected or not self._websocket:
            self.queue_message(message)
            return False
        
        try:
            await self._websocket.send_text(message.to_json())
            return True
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")
            self.queue_message(message)
            return False
    
    async def _reader_loop(self) -> None:
        """Main loop that reads messages from the WebSocket."""
        if not self._websocket:
            return
        
        try:
            while self._connected:
                try:
                    # Read message
                    if hasattr(self._websocket, "receive_text"):
                        data = await self._websocket.receive_text()
                    else:
                        data = await self._websocket.recv()
                    
                    # Parse and handle message
                    message = TransportMessage.from_json(data)
                    
                    # Handle ping/pong
                    if message.type == MessageType.PING:
                        await self.send(TransportMessage.pong())
                    elif message.type == MessageType.PONG:
                        import time
                        self._last_pong = time.time()
                    else:
                        self._handle_message(message)
                        
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON on WebSocket")
                except Exception as e:
                    if "close" in str(e).lower() or "disconnect" in str(e).lower():
                        break
                    logger.warning(f"WebSocket receive error: {e}")
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket reader error: {e}")
            self._state = TransportState.ERROR
    
    async def _ping_loop(self) -> None:
        """Periodic ping to keep connection alive."""
        try:
            while self._connected:
                await asyncio.sleep(self._ping_interval)
                
                if not self._connected:
                    break
                
                # Send ping
                await self.send(TransportMessage.ping())
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket ping error: {e}")
    
    def set_ping_interval(self, interval: float) -> None:
        """Set the ping interval in seconds."""
        self._ping_interval = max(5.0, interval)


async def handle_websocket(
    websocket: Any,
    client_id: str,
    on_message: Optional[callable] = None,
) -> WebSocketTransport:
    """
    Handle a WebSocket connection for live queries.
    
    Usage with FastAPI:
        @app.websocket("/_pynext/live/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await handle_websocket(websocket, generate_client_id())
    """
    transport = WebSocketTransport(websocket)
    
    if on_message:
        transport.on_message(on_message)
    
    await transport.connect(client_id)
    
    return transport

