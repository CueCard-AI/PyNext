"""
PyNext Live Query Transport - Base Classes.

Abstract base class for transport implementations.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.live.detection.base import ChangeEvent


class TransportState(str, Enum):
    """
    State of a transport connection.
    
    - disconnected: No connection
    - connecting: Connection in progress
    - connected: Active connection
    - reconnecting: Lost connection, trying to reconnect
    - error: Connection failed
    """
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class MessageType(str, Enum):
    """
    Types of messages sent over the transport.
    
    - data: Query results or updates
    - subscribe: Subscribe to a query
    - unsubscribe: Unsubscribe from a query
    - ping: Keep-alive
    - pong: Keep-alive response
    - error: Error notification
    - sync: State synchronization
    """
    DATA = "data"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    SYNC = "sync"


@dataclass
class TransportMessage:
    """
    A message sent over the transport.
    
    All messages have:
    - type: What kind of message
    - query_id: Which query it relates to (optional)
    - data: The payload
    - timestamp: When it was created
    """
    type: MessageType
    query_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "type": self.type.value,
            "query_id": self.query_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "TransportMessage":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(
            type=MessageType(data["type"]),
            query_id=data.get("query_id"),
            data=data.get("data"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
        )
    
    @classmethod
    def data_message(
        cls,
        query_id: str,
        event: "ChangeEvent",
    ) -> "TransportMessage":
        """Create a data message from a change event."""
        return cls(
            type=MessageType.DATA,
            query_id=query_id,
            data=event.to_dict(),
        )
    
    @classmethod
    def error_message(
        cls,
        query_id: Optional[str],
        error: str,
    ) -> "TransportMessage":
        """Create an error message."""
        return cls(
            type=MessageType.ERROR,
            query_id=query_id,
            data={"error": error},
        )
    
    @classmethod
    def sync_message(
        cls,
        query_id: str,
        full_data: List[Dict[str, Any]],
    ) -> "TransportMessage":
        """Create a sync message with full data."""
        return cls(
            type=MessageType.SYNC,
            query_id=query_id,
            data={"rows": full_data},
        )
    
    @classmethod
    def ping(cls) -> "TransportMessage":
        """Create a ping message."""
        return cls(type=MessageType.PING)
    
    @classmethod
    def pong(cls) -> "TransportMessage":
        """Create a pong message."""
        return cls(type=MessageType.PONG)


# Type for message handlers
MessageHandler = Callable[[TransportMessage], None]


class Transport(ABC):
    """
    Abstract base class for transport implementations.
    
    Transports handle:
    - Sending messages to clients
    - Receiving messages from clients
    - Connection lifecycle
    - Reconnection
    
    Implementations:
    - SSETransport: Server-Sent Events
    - WebSocketTransport: WebSocket
    """
    
    def __init__(self):
        self._state = TransportState.DISCONNECTED
        self._client_id: Optional[str] = None
        self._message_handlers: List[MessageHandler] = []
        self._pending_messages: List[TransportMessage] = []
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this transport."""
        pass
    
    @property
    @abstractmethod
    def is_bidirectional(self) -> bool:
        """Whether this transport supports client-to-server messages."""
        pass
    
    @property
    def state(self) -> TransportState:
        """Current connection state."""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """Whether currently connected."""
        return self._state == TransportState.CONNECTED
    
    @property
    def client_id(self) -> Optional[str]:
        """The client ID for this transport."""
        return self._client_id
    
    @abstractmethod
    async def connect(self, client_id: str) -> None:
        """
        Establish connection to client.
        
        Args:
            client_id: Unique client identifier
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection."""
        pass
    
    @abstractmethod
    async def send(self, message: TransportMessage) -> bool:
        """
        Send a message to the client.
        
        Args:
            message: Message to send
            
        Returns:
            True if sent, False if failed
        """
        pass
    
    async def send_batch(self, messages: List[TransportMessage]) -> int:
        """
        Send multiple messages.
        
        Default implementation sends one-by-one.
        
        Returns:
            Number of messages sent successfully
        """
        sent = 0
        for message in messages:
            if await self.send(message):
                sent += 1
        return sent
    
    def on_message(self, handler: MessageHandler) -> Callable[[], None]:
        """
        Register a message handler.
        
        Returns an unsubscribe function.
        """
        self._message_handlers.append(handler)
        return lambda: self._message_handlers.remove(handler) if handler in self._message_handlers else None
    
    def _handle_message(self, message: TransportMessage) -> None:
        """Dispatch a received message to handlers."""
        for handler in self._message_handlers:
            try:
                handler(message)
            except Exception:
                pass  # Don't let handler errors affect others
    
    def queue_message(self, message: TransportMessage) -> None:
        """Queue a message for later sending (when reconnected)."""
        self._pending_messages.append(message)
    
    async def flush_pending(self) -> int:
        """Send all pending messages. Returns count sent."""
        if not self._pending_messages:
            return 0
        
        messages = self._pending_messages[:]
        self._pending_messages.clear()
        return await self.send_batch(messages)

