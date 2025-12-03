# Live Queries - Real-Time Database Reactivity

## What You'll Learn

By the end of this guide, you'll understand:
- What live queries are and why they matter
- How to create reactive database subscriptions
- The technology behind real-time updates
- How to configure for different use cases
- Performance optimization strategies

---

## Part 1: Understanding Live Queries

### The Problem: Static Data in a Dynamic World

Imagine you're building a dashboard. Users want to see:
- Real-time inventory counts
- Live order updates
- Instant notification when data changes

Traditional approach:
```python
# ❌ Polling - wasteful and slow
while True:
    data = await User.all()
    update_ui(data)
    await asyncio.sleep(5)  # Check every 5 seconds
```

Problems:
1. **Wasteful**: Makes requests even when nothing changed
2. **Slow**: Up to 5 second delay before seeing updates
3. **Resource intensive**: Constant database queries
4. **Scalability nightmare**: 1000 users = 1000 queries per 5 seconds

### The Solution: Live Queries

Live queries flip the model:

```python
# ✅ Live Query - reactive and efficient
users = User.live()  # Subscribe once

# Automatically updates when database changes!
```

How it works:
1. **Subscribe once**: Client connects and declares interest
2. **Server watches**: Database notifies of changes
3. **Push updates**: Only changed data sent to client
4. **Instant reactivity**: Updates appear in milliseconds

---

## Part 2: Your First Live Query

### Basic Usage

```python
from pynext.db import Table

class User(Table):
    name: str
    email: str
    status: str

# Create a live query - returns a Signal
users = User.live()

# In a component, this auto-updates!
def UserList():
    return Ul(*[
        Li(user.name) for user in users()
    ])
```

### What Happens Behind the Scenes

```
1. User.live() called
   ↓
2. Server creates subscription
   ↓
3. Initial data fetched and sent
   ↓
4. Database trigger watches for changes
   ↓
5. Change detected → Server notified
   ↓
6. Update strategy applied
   ↓
7. Changes pushed to client via SSE/WebSocket
   ↓
8. Signal updates → UI re-renders
```

---

## Part 3: Filtering Live Queries

### WHERE Clauses

```python
# Only active users
active_users = User.live().where(status="active")

# Multiple conditions
premium_active = User.live().where(
    status="active",
    subscription="premium"
)

# Comparison operators
recent = User.live().where(created_at__gte=yesterday)
```

### Ordering and Limiting

```python
# Top 10 users by score
top_users = User.live().order_by("-score").limit(10)

# Latest posts
recent_posts = Post.live().order_by("-created_at").limit(20)
```

### Relationships

```python
# Include related data
users_with_posts = User.live().include("posts")

# Deep nesting
full_data = User.live().include(
    "posts",
    "posts.comments",
    "profile"
)
```

---

## Part 4: Configuration Options

### Transport Mode

Choose how updates are delivered:

```python
from pynext.db.live import LiveQueryConfig, TransportType

# Auto-select (recommended)
config = LiveQueryConfig(transport=TransportType.AUTO)

# Force SSE (simple, one-way)
config = LiveQueryConfig(transport=TransportType.SSE)

# Force WebSocket (bidirectional, lower latency)
config = LiveQueryConfig(transport=TransportType.WEBSOCKET)
```

**When to use each:**

| Transport | Best For | Latency | Browser Support |
|-----------|----------|---------|-----------------|
| SSE | Simple read-only updates | ~50ms | Excellent |
| WebSocket | Interactive apps, chat | ~20ms | Excellent |
| Auto | Most cases | Varies | Excellent |

### Detection Strategy

How the server detects database changes:

```python
from pynext.db.live import DetectionStrategy

# Auto-detect best method
config = LiveQueryConfig(detection=DetectionStrategy.AUTO)

# PostgreSQL LISTEN/NOTIFY (fastest)
config = LiveQueryConfig(detection=DetectionStrategy.LISTEN_NOTIFY)

# Supabase Realtime (if using Supabase)
config = LiveQueryConfig(detection=DetectionStrategy.SUPABASE)

# Polling (fallback, works everywhere)
config = LiveQueryConfig(detection=DetectionStrategy.POLLING)
```

**Detection comparison:**

| Method | Latency | CPU Usage | Setup Required |
|--------|---------|-----------|----------------|
| LISTEN/NOTIFY | ~5ms | Minimal | Triggers |
| Supabase | ~10ms | Minimal | Supabase config |
| Polling | 1-5s | Higher | None |

### Update Granularity

How updates are applied:

```python
from pynext.db.live import UpdateGranularity

# Auto-select based on query
config = LiveQueryConfig(update_granularity=UpdateGranularity.AUTO)

# Surgical - only send changed rows
config = LiveQueryConfig(update_granularity=UpdateGranularity.SURGICAL)

# Full refresh - re-fetch entire result set
config = LiveQueryConfig(update_granularity=UpdateGranularity.FULL_REFRESH)
```

**When each is used:**

- **Surgical**: Simple queries without ORDER BY or LIMIT
- **Full Refresh**: Complex queries with sorting, limiting, or aggregations

---

## Part 5: The Signal Pattern

### Live Queries are Signals

Live queries return PyNext Signals, providing reactive state:

```python
# Live query returns a Signal
users = User.live()

# Reading current value
current_users = users()  # Call the signal

# In templates - auto-tracks dependencies
def Template():
    return Div(
        f"Count: {len(users())}",  # Re-renders on change
        *[UserCard(u) for u in users()]
    )
```

### Built-in State Signals

Every live query includes helper signals:

```python
users = User.live()

# Loading state
if users.loading():
    return Spinner()

# Error state
if users.error():
    return Error(users.error())

# Data state
return UserList(users())
```

### Computed Values

Derive computed values from live queries:

```python
users = User.live()

# Computed signal - updates when users change
active_count = computed(lambda: len([u for u in users() if u.status == "active"]))

# Use in templates
def Stats():
    return Div(f"Active: {active_count()}")
```

---

## Part 6: Debouncing and Throttling

### Debouncing

Wait for rapid changes to settle:

```python
# Wait 100ms after last change before updating
config = LiveQueryConfig(debounce_ms=100)

users = User.live(config=config)
```

**Use case**: Text search - wait for user to stop typing

### Throttling

Limit update frequency:

```python
# At most one update every 500ms
config = LiveQueryConfig(throttle_ms=500)

prices = StockPrice.live(config=config)
```

**Use case**: High-frequency data - don't overwhelm the UI

---

## Part 7: Error Handling and Recovery

### Automatic Reconnection

PyNext handles connection drops automatically:

```python
config = LiveQueryConfig(
    max_retries=5,          # Try 5 times
    retry_delay_ms=1000,    # Start with 1 second delay
)

users = User.live(config=config)
```

Retry behavior:
1. First retry: 1 second
2. Second retry: 2 seconds (exponential backoff)
3. Third retry: 4 seconds
4. ...and so on

### Error Callbacks

Handle errors explicitly:

```python
def on_error(error):
    log_error(error)
    show_toast("Connection lost, retrying...")

users = User.live(on_error=on_error)
```

### Manual Reconnection

Force reconnection:

```python
users = User.live()

# On network recovery
users.reconnect()
```

---

## Part 8: Server-Side Setup

### PostgreSQL Triggers

For LISTEN/NOTIFY detection, PyNext creates triggers automatically:

```python
# During app startup
from pynext.db.live import setup_live_queries

await setup_live_queries()  # Creates necessary triggers
```

The generated trigger looks like:
```sql
CREATE OR REPLACE FUNCTION pynext_notify_users()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'pynext_users',
        json_build_object(
            'operation', TG_OP,
            'id', COALESCE(NEW.id, OLD.id),
            'new', row_to_json(NEW),
            'old', row_to_json(OLD)
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Supabase Integration

If using Supabase, live queries work out of the box:

```python
from pynext.db.supabase import Supabase

# Configure Supabase
Supabase.configure(
    url="your-project.supabase.co",
    anon_key="your-anon-key"
)

# Live queries automatically use Supabase Realtime
users = User.live()  # Uses Supabase channels
```

---

## Part 9: Performance Optimization

### Query Deduplication

Multiple components subscribing to the same query share a single subscription:

```python
# Component A
users_a = User.live().where(status="active")

# Component B (same query)
users_b = User.live().where(status="active")

# Server: Only ONE subscription, shared by both
```

### Batching Updates

Multiple rapid changes are batched:

```python
# 10 inserts in quick succession
for i in range(10):
    await User.create(name=f"User {i}")

# Client receives ONE batched update, not 10
```

### Connection Pooling

Live query connections are pooled and reused:

```python
# 100 live queries from same client
# = 1 SSE/WebSocket connection, multiplexed
```

### Selective Column Updates

Only fetch changed columns:

```python
# Only name and email in live updates
users = User.live().select("id", "name", "email")
```

---

## Part 10: Security Considerations

### Row-Level Security

Live queries respect PostgreSQL RLS policies:

```python
# RLS policy ensures users only see their data
users = User.live()  # Only returns user's own records
```

### Authentication

Live query connections are authenticated:

```python
# Connection includes auth token
# Server validates before allowing subscription
```

### Rate Limiting

Protect against subscription abuse:

```python
from pynext.db.live import LiveQueryConfig

config = LiveQueryConfig(
    max_subscriptions_per_client=100,  # Limit per client
)
```

---

## Part 11: Debugging Live Queries

### Logging

Enable verbose logging:

```python
import logging

logging.getLogger("pynext.db.live").setLevel(logging.DEBUG)
```

Output:
```
DEBUG: Creating subscription for users (client_1)
DEBUG: Change detected: INSERT users id=5
DEBUG: Applying surgical update: +1 row
DEBUG: Broadcasting to 3 subscribers
```

### DevTools Integration

In development mode, PyNext provides a live query inspector:

```python
# In browser console
__pynext__.liveQueries.list()  // Show all subscriptions
__pynext__.liveQueries.stats() // Connection stats
```

### Testing Live Queries

```python
import pytest
from pynext.db.live.testing import MockChangeDetector

@pytest.fixture
def mock_detector():
    """Replace real detector with mock."""
    detector = MockChangeDetector()
    with patch_detector(detector):
        yield detector

async def test_live_query_updates(mock_detector):
    users = User.live()
    
    # Simulate database change
    mock_detector.emit_change(
        table="users",
        type=ChangeType.INSERT,
        data={"id": 1, "name": "Test"}
    )
    
    await asyncio.sleep(0.1)  # Let update propagate
    
    assert len(users()) == 1
    assert users()[0].name == "Test"
```

---

## Part 12: Complete Example

### Real-Time Dashboard

```python
from pynext import Component
from pynext.db import Table
from pynext.db.live import LiveQueryConfig, TransportType

class Order(Table):
    status: str
    total: float
    customer_id: int
    created_at: datetime

class Dashboard(Component):
    def __init__(self):
        # Live queries with different configs
        self.pending_orders = Order.live().where(status="pending")
        self.recent_orders = Order.live().order_by("-created_at").limit(10)
        
        # Computed stats
        self.pending_total = computed(
            lambda: sum(o.total for o in self.pending_orders())
        )
    
    def render(self):
        if self.pending_orders.loading():
            return Loading()
        
        return Div(class_="dashboard")(
            # Stats card
            Card(
                H2("Pending Orders"),
                P(f"Count: {len(self.pending_orders())}"),
                P(f"Total: ${self.pending_total():.2f}"),
            ),
            
            # Order list - auto-updates!
            Card(
                H2("Recent Orders"),
                Table(
                    *[OrderRow(order) for order in self.recent_orders()]
                ),
            ),
        )

def OrderRow(order):
    return Tr(
        Td(order.id),
        Td(order.status),
        Td(f"${order.total:.2f}"),
        Td(order.created_at.strftime("%H:%M")),
    )
```

---

## Quick Reference

### Creating Live Queries

```python
# Basic
users = User.live()

# With filter
active = User.live().where(status="active")

# With config
users = User.live(config=LiveQueryConfig(debounce_ms=100))
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `transport` | TransportType | AUTO | SSE, WEBSOCKET, or AUTO |
| `detection` | DetectionStrategy | AUTO | How to detect changes |
| `update_granularity` | UpdateGranularity | AUTO | Surgical or full refresh |
| `debounce_ms` | int | 0 | Debounce delay |
| `throttle_ms` | int | 0 | Throttle interval |
| `max_retries` | int | 3 | Reconnection attempts |
| `retry_delay_ms` | int | 1000 | Initial retry delay |

### Signal Properties

```python
lq = User.live()

lq()           # Current data
lq.loading()   # Is loading
lq.error()     # Error if any
lq.connected() # Connection status
```

### Lifecycle Methods

```python
lq = User.live()

await lq.start()       # Start subscription
await lq.stop()        # Stop subscription
await lq.reconnect()   # Force reconnection
lq.set_data(data)      # Manual data update
```

---

## Summary

Live queries provide:

1. **Real-time reactivity** - Instant UI updates on database changes
2. **Efficient transport** - SSE/WebSocket with automatic selection
3. **Smart detection** - LISTEN/NOTIFY, Supabase, or polling
4. **Signal integration** - Seamless with PyNext's reactive system
5. **Production-ready** - Error recovery, debouncing, security

Next: [Database Migrations](./04-migrations.md)

