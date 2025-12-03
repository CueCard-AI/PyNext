"""
PyNext Live Query Transport Layer.

Handles communication between server and client for live queries.

Transport Types:
- SSE (Server-Sent Events): Simple, unidirectional, browser-native
- WebSocket: Bidirectional, lower latency, reuses existing connections

The transport layer:
1. Sends updates from server to client
2. Handles reconnection and state sync
3. Batches updates for efficiency

Usage:
    from pynext.db.live.transport import TransportManager, get_transport_manager
    
    manager = get_transport_manager()
    
    # Send update to client
    await manager.send(client_id, message)
"""

from pynext.db.live.transport.base import (
    Transport,
    TransportMessage,
    TransportState,
    MessageType,
)

from pynext.db.live.transport.manager import (
    TransportManager,
    get_transport_manager,
)

__all__ = [
    "Transport",
    "TransportMessage",
    "TransportState",
    "MessageType",
    "TransportManager",
    "get_transport_manager",
]

