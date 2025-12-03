"""
PyNext Live Query - Transport Manager.

Manages transport connections for all clients.

Responsibilities:
- Creates and tracks transports per client
- Routes messages to correct clients
- Handles connection lifecycle
- Batches messages for efficiency
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Set, TYPE_CHECKING

from pynext.db.live.config import TransportType
from pynext.db.live.transport.base import (
    Transport,
    TransportMessage,
    TransportState,
)
from pynext.db.live.transport.sse import SSETransport
from pynext.db.live.transport.websocket import WebSocketTransport
from pynext.db.live.transport.selector import get_transport_selector

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TransportManager:
    """
    Manages all transport connections.
    
    This is a singleton - use get_transport_manager() to access.
    
    Features:
    - Client -> Transport mapping
    - Message routing
    - Batch sending
    - Connection cleanup
    """
    
    def __init__(self):
        # Client ID -> Transport
        self._transports: Dict[str, Transport] = {}
        
        # Client ID -> Subscribed query IDs
        self._client_subscriptions: Dict[str, Set[str]] = {}
        
        # Query ID -> Subscribed client IDs
        self._query_clients: Dict[str, Set[str]] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Batch settings
        self._batch_delay_ms = 50
        self._pending_batches: Dict[str, List[TransportMessage]] = {}
        self._batch_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(
        self,
        client_id: Optional[str] = None,
        transport_type: TransportType = TransportType.SSE,
        connection: Optional[any] = None,
    ) -> str:
        """
        Create a new transport for a client.
        
        Args:
            client_id: Optional client ID (generated if not provided)
            transport_type: Type of transport to create
            connection: WebSocket or streaming response object
        
        Returns:
            The client ID
        """
        async with self._lock:
            client_id = client_id or f"client_{uuid.uuid4().hex[:12]}"
            
            # Create transport based on type
            if transport_type == TransportType.WEBSOCKET:
                transport = WebSocketTransport(connection)
                get_transport_selector().register_websocket(client_id)
            else:
                transport = SSETransport(connection)
            
            # Connect
            await transport.connect(client_id)
            
            # Store
            self._transports[client_id] = transport
            self._client_subscriptions[client_id] = set()
            
            logger.info(f"Client connected: {client_id} ({transport.name})")
            
            return client_id
    
    async def disconnect(self, client_id: str) -> None:
        """Disconnect a client and clean up."""
        async with self._lock:
            transport = self._transports.pop(client_id, None)
            
            if transport:
                await transport.disconnect()
                
                # Clean up selector
                if isinstance(transport, WebSocketTransport):
                    get_transport_selector().unregister_websocket(client_id)
            
            # Clean up subscriptions
            query_ids = self._client_subscriptions.pop(client_id, set())
            for query_id in query_ids:
                clients = self._query_clients.get(query_id, set())
                clients.discard(client_id)
                if not clients:
                    self._query_clients.pop(query_id, None)
            
            # Cancel batch task
            batch_task = self._batch_tasks.pop(client_id, None)
            if batch_task:
                batch_task.cancel()
            
            logger.info(f"Client disconnected: {client_id}")
    
    async def send(
        self,
        client_id: str,
        message: TransportMessage,
        batch: bool = True,
    ) -> bool:
        """
        Send a message to a client.
        
        Args:
            client_id: Target client
            message: Message to send
            batch: Whether to batch with other messages
        
        Returns:
            True if sent/queued, False if client not found
        """
        transport = self._transports.get(client_id)
        if not transport:
            return False
        
        if batch and self._batch_delay_ms > 0:
            return self._queue_for_batch(client_id, message)
        else:
            return await transport.send(message)
    
    async def broadcast(
        self,
        query_id: str,
        message: TransportMessage,
    ) -> int:
        """
        Broadcast a message to all clients subscribed to a query.
        
        Returns:
            Number of clients message was sent to
        """
        clients = self._query_clients.get(query_id, set())
        sent = 0
        
        for client_id in list(clients):
            if await self.send(client_id, message):
                sent += 1
        
        return sent
    
    def subscribe_query(self, client_id: str, query_id: str) -> None:
        """Subscribe a client to query updates."""
        if client_id not in self._client_subscriptions:
            self._client_subscriptions[client_id] = set()
        self._client_subscriptions[client_id].add(query_id)
        
        if query_id not in self._query_clients:
            self._query_clients[query_id] = set()
        self._query_clients[query_id].add(client_id)
    
    def unsubscribe_query(self, client_id: str, query_id: str) -> None:
        """Unsubscribe a client from query updates."""
        if client_id in self._client_subscriptions:
            self._client_subscriptions[client_id].discard(query_id)
        
        if query_id in self._query_clients:
            self._query_clients[query_id].discard(client_id)
            if not self._query_clients[query_id]:
                del self._query_clients[query_id]
    
    def get_transport(self, client_id: str) -> Optional[Transport]:
        """Get the transport for a client."""
        return self._transports.get(client_id)
    
    def get_connected_clients(self) -> List[str]:
        """Get list of connected client IDs."""
        return list(self._transports.keys())
    
    def get_query_subscribers(self, query_id: str) -> Set[str]:
        """Get client IDs subscribed to a query."""
        return self._query_clients.get(query_id, set()).copy()
    
    def _queue_for_batch(self, client_id: str, message: TransportMessage) -> bool:
        """Queue a message for batched sending."""
        if client_id not in self._pending_batches:
            self._pending_batches[client_id] = []
            
            # Start batch timer
            self._batch_tasks[client_id] = asyncio.create_task(
                self._flush_batch(client_id)
            )
        
        self._pending_batches[client_id].append(message)
        return True
    
    async def _flush_batch(self, client_id: str) -> None:
        """Flush pending messages for a client."""
        await asyncio.sleep(self._batch_delay_ms / 1000)
        
        messages = self._pending_batches.pop(client_id, [])
        self._batch_tasks.pop(client_id, None)
        
        if not messages:
            return
        
        transport = self._transports.get(client_id)
        if transport:
            await transport.send_batch(messages)
    
    async def cleanup_disconnected(self) -> int:
        """Clean up disconnected transports. Returns count cleaned."""
        async with self._lock:
            disconnected = [
                client_id
                for client_id, transport in self._transports.items()
                if transport.state == TransportState.DISCONNECTED
                or transport.state == TransportState.ERROR
            ]
            
            for client_id in disconnected:
                await self.disconnect(client_id)
            
            return len(disconnected)
    
    @property
    def client_count(self) -> int:
        """Number of connected clients."""
        return len(self._transports)
    
    @property
    def subscription_count(self) -> int:
        """Total number of query subscriptions."""
        return sum(len(subs) for subs in self._client_subscriptions.values())


# Global transport manager
_manager: Optional[TransportManager] = None


def get_transport_manager() -> TransportManager:
    """Get the global transport manager."""
    global _manager
    if _manager is None:
        _manager = TransportManager()
    return _manager


async def reset_transport_manager() -> None:
    """Reset the transport manager. Mainly for testing."""
    global _manager
    if _manager:
        for client_id in list(_manager._transports.keys()):
            await _manager.disconnect(client_id)
    _manager = None

