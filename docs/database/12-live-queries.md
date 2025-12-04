# Live Queries - Real-Time Database Reactivity

> **Complete Reference Guide** for `Model.live()` - reactive queries that auto-update when database changes occur.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Core API Reference](#core-api-reference)
- [Change Detection](#change-detection)
- [Transport Layer](#transport-layer)
- [Update Strategies](#update-strategies)
- [Subscription Management](#subscription-management)
- [PostgreSQL Integration](#postgresql-integration)
- [Supabase Integration](#supabase-integration)
- [Client Runtime](#client-runtime)
- [Server Endpoints](#server-endpoints)
- [Configuration Reference](#configuration-reference)
- [Performance Optimization](#performance-optimization)
- [Security](#security)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Complete Examples](#complete-examples)

---

## Overview

Live queries provide **real-time database reactivity** - your UI automatically updates when data changes in the database.

| Feature | Description |
|---------|-------------|
| **Reactive Signals** | `LiveQuery` extends Signal - seamless integration |
| **Multiple Detection** | PostgreSQL LISTEN/NOTIFY, Supabase Realtime, Polling |
| **Smart Transport** | Auto-select between SSE and WebSocket |
| **Intelligent Updates** | Surgical (row-level) or Full Refresh strategies |
| **Query Deduplication** | Identical queries share subscriptions |
| **Automatic Recovery** | Reconnection with exponential backoff |
| **Type-Safe** | Full Python type hints throughout |

### The Problem: Static Data

Traditional web apps fetch data once and display it:

```python
# ❌ Traditional: Data goes stale immediately
async def Dashboard():
    orders = await Order.filter(status="pending").all()  # Fetched once
    return div(f"Pending: {len(orders)}")  # Never updates!
```

**Problems:**
1. Data becomes stale the moment it's fetched
2. Users must manually refresh to see updates
3. Polling wastes resources and still has latency
4. Complex state management for real-time features

### The Solution: Live Queries

```python
# ✅ Live Query: Auto-updates when database changes
def Dashboard():
    orders = Order.live().where(status="pending")  # Reactive!
    
    return div(
        f"Pending: {len(orders())}",  # Updates automatically
        For(each=orders, render=lambda o: OrderCard(o))
    )
```

**Benefits:**
1. UI always shows current data
2. No manual refresh needed
3. Efficient - only sends changes, not full data
4. Simple - just call `.live()` instead of `.all()`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LIVE QUERY ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

                              CLIENT BROWSER
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐  │
│   │  Component   │    │  LiveQuery   │    │     live.js Runtime          │  │
│   │              │    │  (Signal)    │    │                              │  │
│   │  orders()    │◄───│  data: []    │◄───│  WebSocket / SSE connection  │  │
│   │              │    │  loading     │    │  Auto-reconnect              │  │
│   │              │    │  error       │    │  Message parsing             │  │
│   └──────────────┘    └──────────────┘    └──────────────────────────────┘  │
│                                                         │                    │
└─────────────────────────────────────────────────────────┼────────────────────┘
                                                          │
                                              SSE or WebSocket
                                                          │
                                                          ▼
                               SERVER (Python)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                      SUBSCRIPTION MANAGER                             │  │
│   │                                                                       │  │
│   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │  │
│   │  │ Query Group 1   │  │ Query Group 2   │  │ Query Group 3   │       │  │
│   │  │ (users.active)  │  │ (orders.pending)│  │ (products.*)    │       │  │
│   │  │                 │  │                 │  │                 │       │  │
│   │  │ Clients: [A,B]  │  │ Clients: [A]    │  │ Clients: [C]    │       │  │
│   │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘       │  │
│   │           │                    │                    │                 │  │
│   └───────────┼────────────────────┼────────────────────┼─────────────────┘  │
│               │                    │                    │                    │
│               └────────────────────┼────────────────────┘                    │
│                                    │                                         │
│                                    ▼                                         │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                       CHANGE DETECTOR                                 │  │
│   │                                                                       │  │
│   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │  │
│   │  │ PostgreSQL      │  │ Supabase        │  │ Polling         │       │  │
│   │  │ LISTEN/NOTIFY   │  │ Realtime        │  │ (Fallback)      │       │  │
│   │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                       UPDATE STRATEGY                                 │  │
│   │                                                                       │  │
│   │  ┌─────────────────┐  ┌─────────────────┐                            │  │
│   │  │ Surgical Update │  │ Full Refresh    │                            │  │
│   │  │ (Row-level)     │  │ (Re-query)      │                            │  │
│   │  └─────────────────┘  └─────────────────┘                            │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                       TRANSPORT LAYER                                 │  │
│   │                                                                       │  │
│   │  ┌─────────────────┐  ┌─────────────────┐                            │  │
│   │  │ SSE Transport   │  │ WebSocket       │                            │  │
│   │  │ (Simple, HTTP)  │  │ Transport       │                            │  │
│   │  └─────────────────┘  └─────────────────┘                            │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                              DATABASE
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│   │     users        │    │     orders       │    │    products      │     │
│   │                  │    │                  │    │                  │     │
│   │  NOTIFY trigger  │    │  NOTIFY trigger  │    │  NOTIFY trigger  │     │
│   └──────────────────┘    └──────────────────┘    └──────────────────┘     │
│                                                                              │
│                         PostgreSQL / Supabase                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Client calls Model.live()
   ↓
2. LiveQuery created (extends Signal)
   ↓
3. Client connects via SSE or WebSocket
   ↓
4. Server creates/joins QueryGroup (deduplication)
   ↓
5. Initial data fetched and sent
   ↓
6. ChangeDetector subscribes to table
   ↓
7. Database change occurs (INSERT/UPDATE/DELETE)
   ↓
8. Trigger fires NOTIFY (PostgreSQL) or event (Supabase)
   ↓
9. ChangeDetector receives event
   ↓
10. UpdateStrategy determines how to update
   ↓
11. Transport sends update to clients
   ↓
12. Client updates Signal value
   ↓
13. UI re-renders affected components
```

---

## Quick Start

### Basic Live Query

```python
from pynext.db import Table

class User(Table):
    name: str
    email: str
    status: str

# Create a live query - it's a Signal!
def UserList():
    users = User.live()  # Returns LiveQuery[User]
    
    # Show loading state
    if users.loading():
        return div("Loading...")
    
    # Show error state
    if users.error():
        return div(f"Error: {users.error()}")
    
    # Render data - auto-updates when database changes!
    return ul(
        For(each=users, render=lambda u: li(u.name))
    )
```

### Filtered Live Query

```python
def ActiveUsers():
    # Chain query methods
    active = User.live().where(status="active").order_by("-created_at").limit(10)
    
    return div(
        h2(f"Active Users ({len(active())})"),
        For(each=active, render=UserCard)
    )
```

### With Configuration

```python
from pynext.db.live import LiveQueryConfig, TransportType, DetectionStrategy

config = LiveQueryConfig(
    transport=TransportType.WEBSOCKET,      # Force WebSocket
    detection=DetectionStrategy.POSTGRES,    # Use LISTEN/NOTIFY
    debounce_ms=100,                         # Wait 100ms before updating
)

def Dashboard():
    orders = Order.live(config=config).where(status="pending")
    return OrderList(orders)
```

### Server Setup

```python
# In your app startup
from pynext.db.live import enable_live_queries

async def startup():
    # Enable live queries for specific tables
    await enable_live_queries("users")
    await enable_live_queries("orders")
    await enable_live_queries("products")
```

---

## Core API Reference

### LiveQuery Class

```python
class LiveQuery(Generic[T]):
    """
    A reactive query that auto-updates when database changes.
    Extends Signal for seamless integration with PyNext's reactivity system.
    """
    
    def __init__(
        self,
        model_class: Type[T],
        config: Optional[LiveQueryConfig] = None,
    ):
        """
        Initialize a live query.
        
        Args:
            model_class: The Table class to query
            config: Configuration options (uses defaults if None)
        """
    
    # ========================================
    # SIGNAL INTERFACE
    # ========================================
    
    def __call__(self) -> List[T]:
        """Get current data. Call like: users()"""
    
    @property
    def loading(self) -> Signal[bool]:
        """Signal indicating if initial load is in progress."""
    
    @property
    def error(self) -> Signal[Optional[Exception]]:
        """Signal containing any error that occurred."""
    
    @property
    def state(self) -> Signal[LiveQueryState]:
        """Signal with current state: IDLE, LOADING, CONNECTED, ERROR, CLOSED"""
    
    # ========================================
    # QUERY BUILDING (Chainable)
    # ========================================
    
    def where(self, **conditions) -> "LiveQuery[T]":
        """
        Add WHERE conditions.
        
        Examples:
            .where(status="active")
            .where(age__gte=18, role="admin")
            .where(name__like="%john%")
        """
    
    def order_by(self, *fields) -> "LiveQuery[T]":
        """
        Add ORDER BY clause.
        
        Examples:
            .order_by("name")           # ASC
            .order_by("-created_at")    # DESC
            .order_by("role", "-name")  # Multiple
        """
    
    def limit(self, count: int) -> "LiveQuery[T]":
        """Limit number of results."""
    
    def offset(self, count: int) -> "LiveQuery[T]":
        """Skip first N results."""
    
    def select(self, *fields) -> "LiveQuery[T]":
        """
        Select specific fields only.
        
        Example:
            .select("id", "name", "email")
        """
    
    def include(self, *relationships) -> "LiveQuery[T]":
        """
        Include related data.
        
        Example:
            .include("posts", "posts.comments", "profile")
        """
    
    # ========================================
    # LIFECYCLE
    # ========================================
    
    async def start(self) -> None:
        """Start the subscription. Called automatically."""
    
    async def stop(self) -> None:
        """Stop the subscription and disconnect."""
    
    async def refetch(self) -> List[T]:
        """Force a full refetch of data."""
    
    async def reconnect(self) -> None:
        """Force reconnection after disconnect."""
    
    # ========================================
    # DATA MANIPULATION
    # ========================================
    
    def set_data(self, data: List[T]) -> None:
        """Manually set data (for optimistic updates)."""
    
    def update_row(self, id: Any, data: Dict[str, Any]) -> None:
        """Update a specific row optimistically."""
    
    def add_row(self, data: T) -> None:
        """Add a row optimistically."""
    
    def remove_row(self, id: Any) -> None:
        """Remove a row optimistically."""
```

### LiveQueryConfig

```python
from dataclasses import dataclass
from pynext.db.live import TransportType, DetectionStrategy, UpdateGranularity

@dataclass
class LiveQueryConfig:
    """Configuration for live queries."""
    
    # Transport settings
    transport: TransportType = TransportType.AUTO
    # AUTO: Let system choose (prefers WebSocket if available)
    # SSE: Force Server-Sent Events
    # WEBSOCKET: Force WebSocket
    
    # Detection settings
    detection: DetectionStrategy = DetectionStrategy.AUTO
    # AUTO: Auto-detect best method
    # POSTGRES: PostgreSQL LISTEN/NOTIFY
    # SUPABASE: Supabase Realtime
    # POLLING: Fallback polling
    
    # Update settings
    granularity: UpdateGranularity = UpdateGranularity.AUTO
    # AUTO: Choose based on query complexity
    # SURGICAL: Send only changed rows
    # FULL_REFRESH: Re-fetch entire result set
    
    # Timing settings
    poll_interval: float = 30.0          # Seconds between polls (if polling)
    batch_delay_ms: int = 50             # Batch rapid changes together
    debounce_ms: int = 0                 # Wait for changes to settle
    throttle_ms: int = 0                 # Max update frequency
    
    # Reconnection settings
    reconnect_delay_ms: int = 1000       # Initial reconnect delay
    max_reconnect_attempts: int = 10     # Max reconnection tries
    
    # Caching settings
    stale_time_ms: int = 0               # Consider data stale after
    cache_time_ms: int = 300000          # Keep cached data for (5 min)
    
    # Advanced
    deduplicate: bool = True             # Share identical subscriptions
    enable_optimistic: bool = True       # Allow optimistic updates
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LiveQueryConfig":
        """Create config from dictionary."""
    
    def merge(self, **overrides) -> "LiveQueryConfig":
        """Create new config with overrides."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
```

### QuerySignature

```python
@dataclass
class QuerySignature:
    """
    Unique identifier for a query, used for deduplication.
    Two queries with the same signature share a subscription.
    """
    
    table: str                           # Table name
    where_clauses: tuple = ()            # WHERE conditions
    order_by: Optional[str] = None       # ORDER BY clause
    limit: Optional[int] = None          # LIMIT value
    offset: Optional[int] = None         # OFFSET value
    fields: tuple = ()                   # Selected fields
    joins: tuple = ()                    # JOIN clauses
    aggregations: tuple = ()             # Aggregation functions
    
    @property
    def hash(self) -> str:
        """SHA256 hash of signature for fast comparison."""
    
    @property
    def has_joins(self) -> bool:
        """Whether query has JOIN clauses."""
    
    @property
    def has_aggregations(self) -> bool:
        """Whether query has aggregations."""
    
    @property
    def has_ordering(self) -> bool:
        """Whether query has ORDER BY."""
    
    @property
    def is_simple(self) -> bool:
        """Whether query is simple enough for surgical updates."""
```

### LiveQueryState Enum

```python
class LiveQueryState(str, Enum):
    IDLE = "idle"           # Not started
    CONNECTING = "connecting"  # Establishing connection
    LOADING = "loading"     # Fetching initial data
    CONNECTED = "connected" # Active and receiving updates
    RECONNECTING = "reconnecting"  # Lost connection, trying to reconnect
    ERROR = "error"         # Error occurred
    CLOSED = "closed"       # Explicitly closed
```

---

## Change Detection

Change detection is how the server knows when database data has changed.

### Detection Strategy Comparison

| Strategy | Latency | CPU Usage | Setup | Best For |
|----------|---------|-----------|-------|----------|
| **PostgreSQL LISTEN/NOTIFY** | ~5ms | Minimal | Triggers | Self-hosted PostgreSQL |
| **Supabase Realtime** | ~10ms | Minimal | None | Supabase projects |
| **Polling** | 1-30s | Higher | None | Any database (fallback) |

### PostgreSQL LISTEN/NOTIFY Detector

The most efficient method for self-hosted PostgreSQL:

```python
class PostgresNotifyDetector(ChangeDetector):
    """
    Uses PostgreSQL's LISTEN/NOTIFY for real-time change detection.
    
    How it works:
    1. Creates triggers on watched tables
    2. Triggers fire NOTIFY on INSERT/UPDATE/DELETE
    3. Detector LISTENs on dedicated connection
    4. Changes dispatched to subscription manager
    """
```

**Trigger SQL (auto-generated):**

```sql
-- Function to send notifications
CREATE OR REPLACE FUNCTION pynext_notify_users()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'pynext_users',
        json_build_object(
            'operation', TG_OP,
            'id', COALESCE(NEW.id, OLD.id),
            'new', CASE WHEN TG_OP != 'DELETE' THEN row_to_json(NEW) ELSE NULL END,
            'old', CASE WHEN TG_OP != 'INSERT' THEN row_to_json(OLD) ELSE NULL END,
            'timestamp', CURRENT_TIMESTAMP
        )::text
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger on all operations
CREATE TRIGGER pynext_users_trigger
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION pynext_notify_users();
```

### Supabase Realtime Detector

For Supabase projects, uses the built-in Realtime feature:

```python
class SupabaseRealtimeDetector(ChangeDetector):
    """
    Uses Supabase Realtime for change detection.
    
    How it works:
    1. Connects to Supabase Realtime WebSocket
    2. Subscribes to postgres_changes on tables
    3. Supabase handles all the trigger/notification logic
    4. Changes dispatched to subscription manager
    """
```

**No setup required** - just configure Supabase:

```python
from pynext.db.supabase import Supabase

Supabase.configure(
    url="https://your-project.supabase.co",
    anon_key="your-anon-key",
)

# Live queries automatically use Supabase Realtime
users = User.live()  # Uses Supabase under the hood
```

### Polling Detector

Fallback for any database:

```python
class PollingDetector(ChangeDetector):
    """
    Periodically queries the database to detect changes.
    
    How it works:
    1. Stores hash/version of last known data
    2. Periodically re-queries and compares
    3. If different, emits change events
    
    Pros:
    - Works with any database
    - No special setup required
    
    Cons:
    - Higher latency (poll_interval)
    - More database load
    - Can't detect individual row changes
    """
```

**Configuration:**

```python
config = LiveQueryConfig(
    detection=DetectionStrategy.POLLING,
    poll_interval=5.0,  # Poll every 5 seconds
)

users = User.live(config=config)
```

### ChangeEvent Dataclass

```python
@dataclass
class ChangeEvent:
    """Represents a detected database change."""
    
    table: str                           # Table that changed
    type: ChangeType                     # INSERT, UPDATE, DELETE, TRUNCATE
    row_id: Optional[int] = None         # Primary key if available
    old_data: Optional[Dict] = None      # Previous row data (UPDATE, DELETE)
    new_data: Optional[Dict] = None      # New row data (INSERT, UPDATE)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "unknown"              # Detection source
    columns_changed: List[str] = field(default_factory=list)  # Which columns
    
    def affects_query(self, signature: QuerySignature) -> bool:
        """Check if this change affects a specific query."""
```

### Detector Registry

Auto-selects the best available detector:

```python
from pynext.db.live import get_detector_registry

registry = get_detector_registry()

# Auto-detection priority:
# 1. PostgreSQL LISTEN/NOTIFY (if PostgresAdapter with asyncpg)
# 2. Supabase Realtime (if Supabase configured)
# 3. Polling (always available)

detector = await registry.get_detector("users")
```

---

## Transport Layer

The transport layer handles communication between server and client.

### Transport Comparison

| Transport | Direction | Latency | Reconnection | Browser Support |
|-----------|-----------|---------|--------------|-----------------|
| **SSE** | Server → Client | ~50ms | Auto | Excellent |
| **WebSocket** | Bidirectional | ~20ms | Auto | Excellent |

### SSE Transport

Server-Sent Events - simple, HTTP-based, one-way:

```python
class SSETransport(Transport):
    """
    Server-Sent Events transport.
    
    Pros:
    - Simple HTTP connection
    - Works through most proxies
    - Automatic reconnection built into browser
    - No special server setup
    
    Cons:
    - Server-to-client only
    - Limited to ~6 connections per domain (HTTP/1.1)
    - Higher latency than WebSocket
    
    Best for:
    - Simple read-only subscriptions
    - Environments with WebSocket restrictions
    """
```

**Client connection:**
```javascript
// Browser automatically handles
const source = new EventSource('/_pynext/live/sse?queries=...');
source.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateQuery(data);
};
```

### WebSocket Transport

Full bidirectional connection:

```python
class WebSocketTransport(Transport):
    """
    WebSocket transport for live queries.
    
    Pros:
    - Bidirectional communication
    - Lower latency (~20ms vs ~50ms)
    - Single connection for all queries
    - Efficient for many subscriptions
    
    Cons:
    - Requires WebSocket support
    - Some proxies may interfere
    - More complex server setup
    
    Best for:
    - Interactive applications
    - Many concurrent subscriptions
    - Low-latency requirements
    """
```

**Integration with Phase 5 websocket.js:**

```javascript
// live.js reuses existing websocket.js connections
if (window.__pynext__.websocket.connections.has('main')) {
    // Reuse existing WebSocket
    this.transport = window.__pynext__.websocket;
} else {
    // Create new connection via shared manager
    window.__pynext__.websocket.connect({
        id: 'live_query',
        url: '/_pynext/live/ws',
        handlers: {
            message: (data) => this._handleMessage(data),
            // ...
        }
    });
}
```

### TransportMessage

```python
@dataclass
class TransportMessage:
    """Message sent between server and client."""
    
    type: MessageType          # INITIAL, UPDATE, ERROR, PING, SUBSCRIBE, etc.
    query_id: str              # Which query this is for
    data: Optional[Any] = None # Payload
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_json(self) -> str:
        """Serialize for transport."""
    
    @classmethod
    def from_json(cls, json_str: str) -> "TransportMessage":
        """Deserialize from transport."""
```

### MessageType Enum

```python
class MessageType(str, Enum):
    # Server → Client
    INITIAL = "initial"       # Initial data load
    UPDATE = "update"         # Data update
    ERROR = "error"           # Error occurred
    PING = "ping"             # Keepalive
    
    # Client → Server
    SUBSCRIBE = "subscribe"   # Subscribe to query
    UNSUBSCRIBE = "unsubscribe"  # Unsubscribe
    PONG = "pong"             # Keepalive response
```

### Transport Selection

```python
from pynext.db.live import get_transport_selector

selector = get_transport_selector()

# Auto-selection logic:
# 1. If client already has WebSocket connection → WebSocket
# 2. If client requests WebSocket and server supports it → WebSocket
# 3. Otherwise → SSE

transport = selector.select(client_capabilities, server_config)
```

---

## Update Strategies

When data changes, how should the client be updated?

### Strategy Comparison

| Strategy | Network | Accuracy | Best For |
|----------|---------|----------|----------|
| **Surgical** | Minimal | High | Simple queries |
| **Full Refresh** | Higher | Perfect | Complex queries |

### Surgical Update Strategy

Sends only the changed row(s):

```python
class SurgicalUpdateStrategy(UpdateStrategy):
    """
    Applies row-level changes to existing data.
    
    For INSERT: Adds new row to result set
    For UPDATE: Updates specific row in place
    For DELETE: Removes row from result set
    
    Pros:
    - Minimal network traffic
    - Fast client-side application
    - Preserves client-side sorting/state
    
    Cons:
    - Can't handle complex queries correctly
    - May drift from true database state
    
    Used when:
    - No ORDER BY, LIMIT, OFFSET
    - No aggregations or JOINs
    - Simple WHERE conditions
    """
```

**Example:**
```python
# Query: User.live().where(status="active")
# Change: UPDATE users SET name='Jane' WHERE id=5

# Surgical update sends:
{
    "type": "update",
    "operation": "UPDATE",
    "row_id": 5,
    "data": {"id": 5, "name": "Jane", "status": "active"}
}
# Client updates just that one row in place
```

### Full Refresh Strategy

Re-executes the query and sends all results:

```python
class FullRefreshStrategy(UpdateStrategy):
    """
    Re-fetches the entire query result set.
    
    Pros:
    - Always accurate
    - Works with any query complexity
    - Handles ORDER BY, LIMIT correctly
    
    Cons:
    - More network traffic
    - Slower for large result sets
    - May cause UI flicker
    
    Used when:
    - Query has ORDER BY
    - Query has LIMIT or OFFSET
    - Query has aggregations
    - Query has JOINs
    - Manual request via refetch()
    """
```

**Example:**
```python
# Query: User.live().order_by("-score").limit(10)
# Change: UPDATE users SET score=100 WHERE id=5

# Full refresh needed because:
# - Changing score might change the top 10
# - New user might enter top 10
# - Existing user might leave top 10

# Server re-runs query and sends all 10 results
```

### Debounced Refresh

For high-frequency changes:

```python
class RefreshDebouncer:
    """
    Batches rapid changes before refreshing.
    
    If 10 changes happen in 50ms:
    - Without debouncing: 10 refreshes
    - With debouncing: 1 refresh
    """

config = LiveQueryConfig(
    granularity=UpdateGranularity.FULL_REFRESH,
    batch_delay_ms=100,  # Wait 100ms for more changes
)
```

### Strategy Selection

```python
from pynext.db.live import get_strategy_selector

selector = get_strategy_selector()

# Auto-selection logic:
def select_strategy(signature: QuerySignature) -> UpdateStrategy:
    if signature.has_ordering:
        return FullRefreshStrategy()
    if signature.limit is not None:
        return FullRefreshStrategy()
    if signature.has_aggregations:
        return FullRefreshStrategy()
    if signature.has_joins:
        return FullRefreshStrategy()
    return SurgicalUpdateStrategy()
```

---

## Subscription Management

The server manages all active subscriptions efficiently.

### SubscriptionManager

```python
class SubscriptionManager:
    """
    Manages all live query subscriptions server-side.
    
    Responsibilities:
    - Track active subscriptions per client
    - Deduplicate identical queries (QueryGroups)
    - Route change events to affected queries
    - Clean up disconnected clients
    """
    
    async def subscribe(
        self,
        client_id: str,
        query_signature: QuerySignature,
        callback: ChangeCallback,
        config: LiveQueryConfig,
    ) -> str:
        """
        Subscribe a client to a query.
        
        Returns:
            Subscription ID
        """
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe by subscription ID."""
    
    async def unsubscribe_client(self, client_id: str) -> None:
        """Unsubscribe all queries for a client."""
    
    async def notify_change(self, event: ChangeEvent) -> None:
        """Notify all affected queries of a change."""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get subscription statistics."""
```

### Query Deduplication

```python
# Client A subscribes to: User.live().where(status="active")
# Client B subscribes to: User.live().where(status="active")

# Same QuerySignature → Same QueryGroup
# Only ONE database subscription, shared by both clients
```

**How it works:**

```
QueryGroup("users_active_xxx")
├── Subscription(client_a, callback_a)
├── Subscription(client_b, callback_b)
└── detector_subscription_id: "det_123"

When change event arrives:
1. QueryGroup.on_change(event) called ONCE
2. Update applied to shared data
3. Both client_a and client_b notified
```

### Statistics

```python
manager = get_subscription_manager()
stats = manager.get_stats()

# Returns:
{
    "total_subscriptions": 150,
    "total_clients": 42,
    "query_groups": 28,          # Unique queries
    "tables_watched": ["users", "orders", "products"],
    "subscriptions_per_table": {
        "users": 45,
        "orders": 80,
        "products": 25,
    },
}
```

---

## PostgreSQL Integration

### Enabling Live Queries

```python
from pynext.db.live import enable_live_queries, disable_live_queries

# In app startup
async def startup():
    # Enable for specific tables
    await enable_live_queries("users")
    await enable_live_queries("orders")
    
    # This creates the NOTIFY triggers automatically

# To disable (removes triggers)
await disable_live_queries("users")
```

### TriggerManager

```python
from pynext.db.live import TriggerManager, get_trigger_manager

manager = get_trigger_manager()

# Check if trigger exists
exists = await manager.has_trigger("users")

# Create trigger manually
channel = await manager.ensure_trigger("users")

# Drop trigger
await manager.drop_trigger("users")

# List all triggers
triggers = await manager.list_triggers()
```

### PostgresAdapter Integration

The `PostgresAdapter` has built-in methods for live queries:

```python
from pynext.db import get_adapter

adapter = get_adapter()

# Check support
adapter.supports_listen_notify()  # True for PostgreSQL
adapter.supports_live_queries()   # True

# Get dedicated LISTEN connection
conn = await adapter.get_listen_connection()

# Execute trigger SQL
await adapter.execute_trigger_sql(trigger_sql)

# Check if trigger exists
exists = await adapter.check_trigger_exists("users", "pynext_users_trigger")

# Get live query config (retry, circuit breaker settings)
config = adapter.live_query_config
```

### Server Configuration

```python
from pynext.db.live import ServerConfig, set_server_config

config = ServerConfig(
    auto_create_triggers=True,       # Create triggers on first subscription
    trigger_prefix="pynext_",        # Prefix for trigger names
    channel_prefix="pynext_",        # Prefix for NOTIFY channels
    max_payload_size=8000,           # Max NOTIFY payload (PostgreSQL limit)
    listen_timeout=30.0,             # Connection keepalive
)

set_server_config(config)
```

---

## Supabase Integration

### Configuration

```python
from pynext.db.supabase import Supabase

Supabase.configure(
    url="https://your-project.supabase.co",
    anon_key="your-anon-key",
)

# Live queries automatically use Supabase Realtime
users = User.live()  # Uses Supabase Realtime under the hood
```

### How It Works

```
1. User.live() detects Supabase is configured
2. SupabaseRealtimeDetector is selected
3. Connects to Supabase Realtime WebSocket
4. Subscribes to postgres_changes on table
5. Supabase broadcasts changes via its infrastructure
6. Changes flow through normal update pipeline
```

### Supabase vs PostgreSQL Direct

| Aspect | Supabase Realtime | PostgreSQL Direct |
|--------|-------------------|-------------------|
| Setup | Zero config | Need triggers |
| Latency | ~10ms | ~5ms |
| Scalability | Supabase handles | You manage |
| Cost | Supabase pricing | Self-hosted |
| RLS | Built-in | Supported |

---

## Client Runtime

### live.js

The client-side JavaScript runtime manages live query connections:

```javascript
// Initialized automatically
window.__pynext__.live = {
    subscriptions: Map,          // Active subscriptions
    config: LiveConfig,          // Configuration
    transport: Transport,        // Current transport
    connected: boolean,
    
    // Methods
    subscribe(queryId, options),
    unsubscribe(queryId),
    reconnect(),
    getStats(),
};
```

### Integration with websocket.js

```javascript
// live.js checks for existing websocket.js connections
_selectTransport: function(preferred) {
    // Reuse Phase 5 websocket.js if available
    if (window.__pynext__.websocket?.connections.size > 0) {
        return 'websocket';
    }
    // Default to SSE for simplicity
    return 'sse';
}
```

### Hydration

```python
# Server renders initial state
def Page():
    users = User.live()
    return div(
        # Initial data embedded in HTML
        script(f"window.__LIVE_QUERIES__ = {json.dumps(hydration_data)}"),
        UserList(users),
    )
```

```javascript
// Client hydrates from embedded data
window.__pynext__.live.hydrate(window.__LIVE_QUERIES__);
```

---

## Server Endpoints

### SSE Endpoint

```
GET /_pynext/live/sse?client_id={id}&queries={encoded_queries}

Response: text/event-stream

event: initial
data: {"query_id": "q1", "data": [...]}

event: update
data: {"query_id": "q1", "type": "INSERT", "data": {...}}

event: ping
data: {}
```

### WebSocket Endpoint

```
WS /_pynext/live/ws

→ {"type": "subscribe", "query_id": "q1", "signature": {...}}
← {"type": "initial", "query_id": "q1", "data": [...]}
← {"type": "update", "query_id": "q1", ...}
```

### REST Endpoints

```python
# Subscribe (alternative to SSE/WS)
POST /_pynext/live/subscribe
{
    "client_id": "abc123",
    "queries": [{"signature": {...}, "config": {...}}]
}

# Unsubscribe
POST /_pynext/live/unsubscribe
{
    "client_id": "abc123",
    "query_ids": ["q1", "q2"]
}

# Force refresh
POST /_pynext/live/refresh
{
    "query_id": "q1"
}

# Statistics
GET /_pynext/live/stats
```

### Route Setup

**Starlette:**
```python
from pynext.server.live import create_live_routes

routes = create_live_routes()
app = Starlette(routes=routes)
```

**FastAPI:**
```python
from pynext.server.live import create_live_router

router = create_live_router()
app.include_router(router)
```

---

## Configuration Reference

### LiveQueryConfig (Complete)

```python
@dataclass
class LiveQueryConfig:
    # Transport
    transport: TransportType = TransportType.AUTO
    
    # Detection
    detection: DetectionStrategy = DetectionStrategy.AUTO
    
    # Updates
    granularity: UpdateGranularity = UpdateGranularity.AUTO
    
    # Timing
    poll_interval: float = 30.0          # Polling interval (seconds)
    batch_delay_ms: int = 50             # Batch changes together
    debounce_ms: int = 0                 # Wait for changes to settle
    throttle_ms: int = 0                 # Max update frequency
    
    # Reconnection
    reconnect_delay_ms: int = 1000       # Initial delay
    max_reconnect_attempts: int = 10     # Max attempts
    reconnect_backoff: float = 1.5       # Exponential factor
    
    # Caching
    stale_time_ms: int = 0               # When data becomes stale
    cache_time_ms: int = 300000          # How long to cache (5 min)
    
    # Optimization
    deduplicate: bool = True             # Share identical queries
    enable_optimistic: bool = True       # Allow optimistic updates
    
    # Limits
    max_results: int = 10000             # Max rows per query
    max_payload_kb: int = 1000           # Max update size
```

### ServerConfig (Complete)

```python
@dataclass  
class ServerConfig:
    # Triggers
    auto_create_triggers: bool = True
    trigger_prefix: str = "pynext_"
    channel_prefix: str = "pynext_"
    
    # Limits
    max_payload_size: int = 8000         # PostgreSQL NOTIFY limit
    max_subscriptions_per_client: int = 100
    max_clients: int = 10000
    
    # Timeouts
    listen_timeout: float = 30.0
    connection_timeout: float = 60.0
    cleanup_interval: float = 60.0
    
    # Security
    require_auth: bool = False
    allowed_tables: Optional[List[str]] = None
```

---

## Performance Optimization

### Query Deduplication

```python
# These create ONE server subscription:
users_a = User.live().where(status="active")
users_b = User.live().where(status="active")  # Same signature!

# But these are DIFFERENT subscriptions:
users_c = User.live().where(status="active")
users_d = User.live().where(status="active").limit(10)  # Different!
```

### Batching

```python
# Without batching: 10 rapid changes = 10 updates
# With batching (batch_delay_ms=50): 10 rapid changes = 1 update

config = LiveQueryConfig(batch_delay_ms=50)
```

### Selective Fields

```python
# Only fetch needed fields
users = User.live().select("id", "name")  # Smaller payloads
```

### Connection Pooling

```python
# 100 live queries from same client
# = 1 WebSocket connection (multiplexed)
# = 1 LISTEN connection on server
```

### Benchmarks

| Scenario | Without Live | With Live (Polling) | With Live (NOTIFY) |
|----------|--------------|---------------------|-------------------|
| 1 user, 1 table | 0ms | +5ms CPU | +0.1ms CPU |
| 100 users, 1 table | 0ms | +500ms CPU | +10ms CPU |
| 100 users, 10 tables | 0ms | +5s CPU | +100ms CPU |
| 1000 concurrent | N/A | ~50 req/s | ~5000 req/s |

---

## Security

### Row-Level Security

Live queries respect PostgreSQL RLS:

```sql
-- RLS policy
CREATE POLICY users_own_data ON users
    FOR SELECT
    USING (user_id = current_user_id());

-- Live query only returns user's own data
users = User.live()  # Filtered by RLS
```

### Authentication

```python
# Server validates auth before allowing subscription
@require_auth
async def handle_subscribe(request):
    user = get_current_user(request)
    # Only allow subscription if authenticated
```

### Rate Limiting

```python
config = ServerConfig(
    max_subscriptions_per_client=100,
    max_clients=10000,
)
```

### Table Allowlist

```python
config = ServerConfig(
    allowed_tables=["users", "orders", "products"],
    # Other tables cannot have live queries
)
```

---

## Testing

### Mock Detector

```python
from pynext.db.live.testing import MockChangeDetector

@pytest.fixture
def mock_detector():
    detector = MockChangeDetector()
    with patch_detector(detector):
        yield detector

async def test_live_query_insert(mock_detector):
    users = User.live()
    await users.start()
    
    # Simulate INSERT
    mock_detector.emit_change(
        table="users",
        type=ChangeType.INSERT,
        new_data={"id": 1, "name": "Test"}
    )
    
    await asyncio.sleep(0.1)
    
    assert len(users()) == 1
    assert users()[0].name == "Test"
```

### Test Helpers

```python
from pynext.db.live.testing import (
    MockChangeDetector,
    MockTransport,
    wait_for_update,
    assert_query_state,
)

async def test_reconnection():
    transport = MockTransport()
    users = User.live()
    
    # Simulate disconnect
    transport.disconnect()
    
    assert users.state() == LiveQueryState.RECONNECTING
    
    # Simulate reconnect
    transport.connect()
    
    await wait_for_update(users, timeout=1.0)
    assert users.state() == LiveQueryState.CONNECTED
```

---

## Troubleshooting

### Subscription Not Updating

```python
# Check subscription is active
print(users.state())  # Should be CONNECTED

# Check for errors
print(users.error())

# Force refetch
await users.refetch()
```

### High Latency

```bash
# Check detection method
pynext live status

# If using polling, switch to NOTIFY
config = LiveQueryConfig(detection=DetectionStrategy.POSTGRES)
```

### Connection Drops

```python
# Increase reconnection attempts
config = LiveQueryConfig(
    max_reconnect_attempts=20,
    reconnect_delay_ms=500,
)
```

### Memory Issues

```python
# Limit results
users = User.live().limit(1000)

# Use server config limits
config = ServerConfig(
    max_subscriptions_per_client=50,
)
```

### Debug Logging

```python
import logging

logging.getLogger("pynext.db.live").setLevel(logging.DEBUG)
# Shows: subscriptions, changes, updates, transport messages
```

### DevTools

```javascript
// Browser console
__pynext__.live.getStats()
// {subscriptions: 5, connected: true, transport: "websocket"}

__pynext__.live.subscriptions.forEach((sub, id) => {
    console.log(id, sub.state, sub.data.length);
});
```

---

## Complete Examples

### Real-Time Dashboard

```python
from pynext import div, h2, For, Show
from pynext.db import Table
from pynext.db.live import LiveQueryConfig

class Order(Table):
    status: str
    total: float
    customer_id: int
    created_at: datetime

def Dashboard():
    # Multiple live queries with different filters
    pending = Order.live().where(status="pending")
    processing = Order.live().where(status="processing")
    recent = Order.live().order_by("-created_at").limit(10)
    
    # Computed values
    pending_total = Computed(lambda: sum(o.total for o in pending()))
    
    return div(class_="dashboard")(
        # Stats cards
        div(class_="stats")(
            StatCard("Pending", len(pending()), f"${pending_total():.2f}"),
            StatCard("Processing", len(processing())),
        ),
        
        # Recent orders table
        div(class_="recent")(
            h2("Recent Orders"),
            Show(when=recent.loading)(Spinner()),
            Show(when=lambda: not recent.loading())(
                OrderTable(recent())
            ),
        ),
    )

def StatCard(title, count, subtitle=None):
    return div(class_="stat-card")(
        h3(title),
        div(class_="count")(str(count)),
        Show(when=subtitle)(div(class_="subtitle")(subtitle)),
    )

def OrderTable(orders):
    return table(
        thead(tr(th("ID"), th("Status"), th("Total"), th("Time"))),
        tbody(For(each=orders, render=OrderRow)),
    )

def OrderRow(order):
    return tr(
        td(order.id),
        td(order.status),
        td(f"${order.total:.2f}"),
        td(order.created_at.strftime("%H:%M")),
    )
```

### Chat Application

```python
from pynext import div, input_, button, For, Signal
from pynext.db import Table
from pynext.db.live import LiveQueryConfig, TransportType

class Message(Table):
    room_id: str
    user_id: int
    content: str
    created_at: datetime

def ChatRoom(room_id: str):
    # Live messages for this room - low latency config
    config = LiveQueryConfig(
        transport=TransportType.WEBSOCKET,
        batch_delay_ms=0,  # Instant updates
    )
    
    messages = Message.live(config=config)\
        .where(room_id=room_id)\
        .order_by("created_at")\
        .limit(100)
    
    new_message = Signal("")
    
    async def send():
        if new_message():
            await Message.insert(
                room_id=room_id,
                user_id=current_user.id,
                content=new_message(),
            )
            new_message.set("")
    
    return div(class_="chat-room")(
        # Messages - auto-scroll to bottom
        div(class_="messages", ref=scroll_to_bottom)(
            For(each=messages, render=MessageBubble),
        ),
        
        # Input
        div(class_="input-area")(
            input_(
                value=new_message,
                on_input=lambda e: new_message.set(e.target.value),
                placeholder="Type a message...",
            ),
            button(on_click=send)("Send"),
        ),
    )

def MessageBubble(msg):
    is_mine = msg.user_id == current_user.id
    return div(class_=f"message {'mine' if is_mine else 'other'}")(
        div(class_="content")(msg.content),
        div(class_="time")(msg.created_at.strftime("%H:%M")),
    )
```

### Stock Ticker

```python
from pynext.db.live import LiveQueryConfig

class StockPrice(Table):
    symbol: str
    price: float
    change: float
    updated_at: datetime

def StockTicker(symbols: List[str]):
    # Throttled updates for high-frequency data
    config = LiveQueryConfig(
        throttle_ms=500,  # Max 2 updates per second
        detection=DetectionStrategy.POLLING,
        poll_interval=1.0,
    )
    
    prices = StockPrice.live(config=config)\
        .where(symbol__in=symbols)
    
    return div(class_="ticker")(
        For(each=prices, render=lambda p: StockCard(p)),
    )

def StockCard(price):
    color = "green" if price.change >= 0 else "red"
    return div(class_="stock-card")(
        div(class_="symbol")(price.symbol),
        div(class_="price")(f"${price.price:.2f}"),
        div(class_=f"change {color}")(
            f"{'+' if price.change >= 0 else ''}{price.change:.2f}%"
        ),
    )
```

---

## Summary

Live queries provide:

| Feature | Benefit |
|---------|---------|
| **Model.live()** | One method for reactive data |
| **Signal Integration** | Seamless with PyNext reactivity |
| **Multi-Backend** | PostgreSQL, Supabase, Polling |
| **Auto Transport** | SSE or WebSocket as appropriate |
| **Smart Updates** | Surgical or Full Refresh |
| **Query Deduplication** | Efficient at scale |
| **Production Ready** | Reconnection, security, monitoring |

**Test Coverage:** 389 tests across 8 test files

**Next:** [Advanced Relationships](./11-relationships.md)
