"""
PyNext Live Query - SSE Transport.

Server-Sent Events transport for live queries.

SSE is simpler than WebSocket:
- One-way (server to client only)
- Browser-native (no library needed)
- Works through proxies and load balancers
- Auto-reconnects on disconnect

Best for:
- Simple live queries
- Low-frequency updates
- When you don't need client-to-server messages
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional, TYPE_CHECKING

from pynext.db.live.transport.base import (
    Transport,
    TransportMessage,
    TransportState,
)

if TYPE_CHECKING:
    from starlette.responses import Response

logger = logging.getLogger(__name__)


class SSETransport(Transport):
    """
    Server-Sent Events transport.
    
    Uses HTTP streaming to send updates to clients.
    The client uses EventSource API to receive.
    
    SSE format:
        event: data
        data: {"type": "data", "query_id": "xxx", "data": {...}}
        
    """
    
    def __init__(self, response: Optional[Any] = None):
        """
        Create an SSE transport.
        
        Args:
            response: Optional Starlette/FastAPI streaming response
        """
        super().__init__()
        self._response = response
        self._queue: asyncio.Queue[TransportMessage] = asyncio.Queue()
        self._writer_task: Optional[asyncio.Task] = None
        self._connected = False
    
    @property
    def name(self) -> str:
        return "SSE"
    
    @property
    def is_bidirectional(self) -> bool:
        return False  # SSE is one-way
    
    async def connect(self, client_id: str) -> None:
        """Start the SSE connection."""
        self._client_id = client_id
        self._state = TransportState.CONNECTING
        
        # Start the writer task
        self._writer_task = asyncio.create_task(self._writer_loop())
        
        self._state = TransportState.CONNECTED
        self._connected = True
        
        logger.debug(f"SSE transport connected: {client_id}")
    
    async def disconnect(self) -> None:
        """Close the SSE connection."""
        self._connected = False
        self._state = TransportState.DISCONNECTED
        
        if self._writer_task:
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass
            self._writer_task = None
        
        logger.debug(f"SSE transport disconnected: {self._client_id}")
    
    async def send(self, message: TransportMessage) -> bool:
        """
        Send a message via SSE.
        
        Messages are queued and sent by the writer task.
        """
        if not self._connected:
            self.queue_message(message)
            return False
        
        await self._queue.put(message)
        return True
    
    async def _writer_loop(self) -> None:
        """Main loop that writes messages to the SSE stream."""
        try:
            while self._connected:
                try:
                    # Wait for a message with timeout for heartbeat
                    message = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=30.0  # Heartbeat every 30s
                    )
                    await self._write_message(message)
                    
                except asyncio.TimeoutError:
                    # Send heartbeat comment to keep connection alive
                    await self._write_heartbeat()
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"SSE writer error: {e}")
            self._state = TransportState.ERROR
    
    async def _write_message(self, message: TransportMessage) -> None:
        """Write a single message to the SSE stream."""
        if self._response is None:
            return
        
        sse_data = self._format_sse(message)
        
        try:
            # Write to the streaming response
            if hasattr(self._response, "write"):
                await self._response.write(sse_data.encode())
            elif hasattr(self._response, "body_iterator"):
                # For async generators
                pass
        except Exception as e:
            logger.warning(f"Failed to write SSE message: {e}")
            self._state = TransportState.ERROR
    
    async def _write_heartbeat(self) -> None:
        """Send a heartbeat comment to keep connection alive."""
        if self._response is None:
            return
        
        try:
            # SSE comment (starts with :)
            heartbeat = ": heartbeat\n\n"
            if hasattr(self._response, "write"):
                await self._response.write(heartbeat.encode())
        except Exception:
            pass
    
    def _format_sse(self, message: TransportMessage) -> str:
        """Format a message as SSE."""
        event_type = message.type.value
        data = message.to_json()
        
        # SSE format
        lines = [
            f"event: {event_type}",
            f"data: {data}",
            "",  # Empty line ends the event
            "",
        ]
        return "\n".join(lines)
    
    def create_response_generator(self):
        """
        Create an async generator for streaming responses.
        
        Usage with FastAPI:
            from fastapi.responses import StreamingResponse
            
            transport = SSETransport()
            return StreamingResponse(
                transport.create_response_generator(),
                media_type="text/event-stream"
            )
        """
        async def generator():
            # Initial connection event
            yield ": connected\n\n"
            
            while self._connected:
                try:
                    message = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=30.0
                    )
                    yield self._format_sse(message)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                except asyncio.CancelledError:
                    break
        
        return generator()


def create_sse_response(transport: SSETransport):
    """
    Create a streaming response for SSE.
    
    Usage:
        @app.get("/_pynext/live/sse")
        async def sse_endpoint():
            transport = SSETransport()
            await transport.connect(client_id)
            return create_sse_response(transport)
    """
    try:
        from starlette.responses import StreamingResponse
        
        return StreamingResponse(
            transport.create_response_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
    except ImportError:
        raise RuntimeError("starlette required for SSE responses")

