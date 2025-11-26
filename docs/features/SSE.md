# Server-Sent Events (SSE)

> **Like a radio broadcast — the server talks, clients listen.**

## What is SSE?

Imagine a news ticker at the bottom of your TV screen. The station broadcasts updates, and your TV displays them — you don't have to keep asking "any news?". That's SSE.

**Server-Sent Events** is a web standard for servers to push real-time updates to browsers. Unlike WebSockets (which are bidirectional), SSE is one-way: server → client.

**Use cases:**
- Live notifications
- Real-time dashboards
- Activity feeds
- Live scores/updates
- Stock prices
- Chat message delivery

## Why Do We Need It?

Without real-time updates, you have two options:

| Approach | How It Works | Problems |
|----------|--------------|----------|
| **Polling** | Client asks "any updates?" every N seconds | Wastes resources, delayed updates |
| **Refresh** | User manually reloads the page | Terrible UX |

SSE solves this:
- **Instant updates** — Server pushes immediately
- **Efficient** — One persistent connection, no repeated requests
- **Simple** — Built into browsers, no library needed
- **Resilient** — Auto-reconnects on disconnect

## Architecture: Server + Client

SSE has **two parts** — you need both:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SSE ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   YOUR SERVER (You create this)           BROWSER (PyNext handles this)     │
│   ═════════════════════════════           ═════════════════════════════     │
│                                                                              │
│   ┌───────────────────────────┐           ┌───────────────────────────┐     │
│   │                           │           │                           │     │
│   │  @api_route("/api/events")│           │  use_event_source(        │     │
│   │  async def events():      │           │      "/api/events",       │     │
│   │      while True:          │           │      handlers={...}       │     │
│   │          event = await... │           │  )                        │     │
│   │          yield {          │ ────────► │                           │     │
│   │              "event": ... │ SSE Stream│  Handlers called with     │     │
│   │              "data": ...  │ (one-way) │  parsed data              │     │
│   │          }                │           │                           │     │
│   │                           │           │  Signals updated          │     │
│   └───────────────────────────┘           └───────────────────────────┘     │
│                                                                              │
│   FILE: pages/api/events.py               ANYWHERE: your component           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Step 1: Create Your Server Endpoint

First, create an SSE endpoint on your server. This is where events originate.

### File: `pages/api/events.py`

```python
from pynext import api_route
from pynext.streaming import EventStream
import json
import asyncio

@api_route("/api/events")
async def events_endpoint(request):
    """
    SSE endpoint that streams events to connected clients.
    
    This runs on your SERVER. Clients connect to this endpoint,
    and we push events to them over a persistent HTTP connection.
    """
    
    async def generate():
        """
        Generator that yields events.
        
        This function runs in an infinite loop, checking for new
        events and yielding them to connected clients.
        """
        while True:
            # Get the latest event from your data source
            # (database, queue, external API, etc.)
            event = await get_latest_event()
            
            if event:
                # Yield the event in SSE format
                yield {
                    "event": event["type"],   # Event name (e.g., "notification")
                    "data": json.dumps(event["data"]),  # JSON payload
                }
            
            # Wait before checking again
            # (adjust based on your needs)
            await asyncio.sleep(1)
    
    # Return an EventStream response
    # This sets the correct headers and keeps the connection open
    return EventStream(generate())


async def get_latest_event():
    """
    Your logic to get the latest event.
    
    This could query a database, check a message queue,
    or monitor for changes.
    """
    # Example: Check for new notifications
    notification = await db.get_undelivered_notification()
    
    if notification:
        await db.mark_as_delivered(notification.id)
        return {
            "type": "notification",
            "data": {
                "id": notification.id,
                "message": notification.message,
                "created_at": notification.created_at.isoformat(),
            }
        }
    
    return None
```

### Understanding the Server Code

Let's break down each part:

```python
@api_route("/api/events")
```
- Creates an endpoint at `/api/events`
- Clients will connect to this URL

```python
async def generate():
    while True:
        ...
```
- An async generator that runs forever
- Each `yield` sends an event to clients

```python
yield {
    "event": event["type"],
    "data": json.dumps(event["data"]),
}
```
- `event` — The event name (clients listen for this)
- `data` — The payload (must be a string, usually JSON)

```python
return EventStream(generate())
```
- Wraps your generator in an SSE response
- Sets headers: `Content-Type: text/event-stream`
- Keeps the HTTP connection open

---

## Step 2: Connect from Client

Now, connect to your endpoint from the browser using `use_event_source()`:

```python
from pynext import Signal, use_event_source

# Signals to hold your data
notifications = Signal([])
users_online = Signal(0)

# ═══════════════════════════════════════════════════════════════
# Connect to SSE endpoint
# ═══════════════════════════════════════════════════════════════

sse = use_event_source(
    # The URL of your SSE endpoint (created in Step 1)
    "/api/events",
    
    # Handlers: event name → function to call
    {
        # When server yields: {"event": "notification", "data": "..."}
        "notification": lambda data: notifications.update(
            lambda current: [data, *current][:100]  # Prepend, keep 100
        ),
        
        # When server yields: {"event": "user_count", "data": "42"}
        "user_count": lambda data: users_online.set(data["count"]),
    },
    
    # Options (all optional)
    {
        "reconnect": True,        # Auto-reconnect on error
        "reconnect_delay": 1000,  # Milliseconds before retry
    }
)
```

### Understanding the Client Code

```python
use_event_source("/api/events", handlers, options)
```

| Argument | Type | Description |
|----------|------|-------------|
| `url` | `str` | Your SSE endpoint URL |
| `handlers` | `dict` | Event name → handler function |
| `options` | `dict` | Connection options (optional) |

**Handlers:**

```python
{
    "notification": lambda data: ...,
    "task_update": lambda data: ...,
}
```

- Keys match the `event` field from your server
- Values are functions that receive parsed JSON data
- Use lambdas or regular functions

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `reconnect` | `bool` | `True` | Auto-reconnect on error |
| `reconnect_delay` | `int` | `1000` | Ms before reconnect |

---

## Step 3: Use the Data

Once connected, your Signals update automatically. Use them in components:

```python
from pynext.shadcn import Card, CardHeader, CardTitle, CardContent, Badge

def NotificationPanel():
    """Display live notifications."""
    return Card()[
        CardHeader()[
            CardTitle()["Notifications"],
            Badge()[f"{len(notifications.value)} new"],
        ],
        CardContent()[
            # Notifications update in real-time!
            [NotificationItem(n) for n in notifications.value]
        ],
    ]

def NotificationItem(notification):
    return div(class_="p-2 border-b")[
        p(class_="font-medium")[notification["message"]],
        span(class_="text-sm text-muted-foreground")[
            notification["created_at"]
        ],
    ]
```

---

## Complete Example: Live Activity Feed

Here's a full working example:

### Server: `pages/api/activity.py`

```python
from pynext import api_route
from pynext.streaming import EventStream
import json
import asyncio

# In-memory activity log (use Redis/DB in production)
activities = []

@api_route("/api/activity")
async def activity_stream(request):
    """Stream activity events to clients."""
    last_seen = len(activities)
    
    async def generate():
        nonlocal last_seen
        
        while True:
            # Check for new activities
            if len(activities) > last_seen:
                for activity in activities[last_seen:]:
                    yield {
                        "event": "activity",
                        "data": json.dumps(activity),
                    }
                last_seen = len(activities)
            
            await asyncio.sleep(0.5)
    
    return EventStream(generate())

@api_route("/api/activity", methods=["POST"])
async def add_activity(request):
    """Add a new activity (called by other parts of your app)."""
    data = await request.json()
    activities.append({
        "id": len(activities) + 1,
        "user": data["user"],
        "action": data["action"],
        "timestamp": datetime.now().isoformat(),
    })
    return {"status": "ok"}
```

### Client: Component

```python
from pynext import Signal, use_event_source
from pynext.shadcn import Card, CardContent, Avatar, AvatarFallback

# Activity feed signal
activities = Signal([])

# Connect to activity stream
sse = use_event_source("/api/activity", {
    "activity": lambda data: activities.update(
        lambda current: [data, *current][:50]
    ),
})

def ActivityFeed():
    """Live activity feed component."""
    return Card()[
        CardContent()[
            h3(class_="font-semibold mb-4")["Activity"],
            
            div(class_="space-y-3")[
                [ActivityItem(a) for a in activities.value]
            ] if activities.value else
            
            p(class_="text-muted-foreground text-center py-8")[
                "No activity yet..."
            ],
        ],
    ]

def ActivityItem(activity):
    return div(class_="flex items-center gap-3")[
        Avatar()[
            AvatarFallback()[activity["user"][0].upper()]
        ],
        div()[
            p(class_="text-sm")[
                strong()[activity["user"]], 
                f" {activity['action']}"
            ],
            span(class_="text-xs text-muted-foreground")[
                activity["timestamp"]
            ],
        ],
    ]
```

---

## API Reference

### `use_event_source(url, handlers, options)`

Connect to an SSE endpoint.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `str` | Yes | SSE endpoint URL |
| `handlers` | `Dict[str, Callable]` | Yes | Event handlers |
| `options` | `Dict` | No | Connection options |

**Returns:** `SSEHandle`

**Options:**

```python
{
    "reconnect": True,        # Auto-reconnect (default: True)
    "reconnect_delay": 1000,  # Delay in ms (default: 1000)
}
```

### `SSEHandle`

The object returned by `use_event_source()`.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Unique connection ID |
| `url` | `str` | Endpoint URL |
| `is_connected` | `str` (JS) | JS expression for connection status |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `close()` | `str` (JS) | Close the connection |
| `reconnect()` | `str` (JS) | Manually reconnect |

**Usage:**

```python
sse = use_event_source("/api/events", handlers)

# In event handlers
Button(onclick=lambda: sse.close())["Disconnect"]
Button(onclick=lambda: sse.reconnect())["Reconnect"]
```

---

## Common Patterns

### Pattern 1: Multiple Event Types

```python
sse = use_event_source("/api/events", {
    "notification": lambda d: notifications.update(lambda n: [d, *n]),
    "task_created": lambda d: tasks.update(lambda t: [d, *t]),
    "task_updated": lambda d: tasks.update(
        lambda t: [d if x["id"] == d["id"] else x for x in t]
    ),
    "task_deleted": lambda d: tasks.update(
        lambda t: [x for x in t if x["id"] != d["id"]]
    ),
    "user_online": lambda d: online_users.update(lambda s: s | {d["id"]}),
    "user_offline": lambda d: online_users.update(lambda s: s - {d["id"]}),
})
```

### Pattern 2: With Error Handling

```python
connection_error = Signal(False)

sse = use_event_source("/api/events", {
    "message": lambda d: messages.update(lambda m: [d, *m]),
}, {
    "reconnect": True,
    "reconnect_delay": 2000,
})

# Show error state in UI
def StatusBanner():
    return div(class_="bg-red-100 p-2 text-center") if connection_error.value else None
```

### Pattern 3: Authenticated SSE

```python
# Include auth token in URL
token = get_auth_token()
sse = use_event_source(f"/api/events?token={token}", handlers)
```

---

## Troubleshooting

### Connection not establishing

**Problem:** `use_event_source` doesn't connect

**Solutions:**
1. Check that your server endpoint exists and returns `EventStream`
2. Verify the URL is correct (check for typos)
3. Check browser console for CORS errors
4. Ensure your server is running

### Events not firing

**Problem:** Server sends events but handlers not called

**Solutions:**
1. Verify event names match exactly (case-sensitive)
2. Check that server `yield` includes both `event` and `data`
3. Ensure `data` is valid JSON string

### Connection keeps dropping

**Problem:** SSE disconnects frequently

**Solutions:**
1. Check server timeout settings (increase if needed)
2. Verify network stability
3. Enable reconnect: `{"reconnect": True}`

### Memory leak warning

**Problem:** Too many connections

**Solution:** SSE connections persist. Don't create multiple connections to the same endpoint. `use_event_source` handles this automatically.

---

## Best Practices

1. **One connection per endpoint** — Don't create multiple connections to the same URL
2. **Keep payloads small** — SSE isn't for large data transfers
3. **Use reconnection** — Networks are unreliable, always enable reconnect
4. **Handle offline gracefully** — Combine with `use_online()` for offline detection
5. **Server-side filtering** — Filter events on server, not client

---

## Related Documentation

- [Visibility Tracking](./VISIBILITY.md) — Pause SSE when tab is hidden
- [Network Status](./ONLINE_STATUS.md) — Detect offline state
- [Real-Time Updates Tutorial](../tutorials/concepts/real-time-updates.md) — Complete tutorial

