# Real-Time Updates

> **Keep your UI in sync with the server**

Learn different strategies for real-time updates: polling, Server-Sent Events (SSE), and optimistic updates.

---

## What You'll Learn

- Polling for simple updates
- Server-Sent Events for push notifications
- Optimistic updates for instant feedback
- Choosing the right strategy

---

## Strategy Comparison

| Strategy | Latency | Complexity | Best For |
|----------|---------|------------|----------|
| Polling | Medium | Low | Dashboards, non-critical data |
| SSE | Low | Medium | Notifications, live feeds |
| WebSocket | Lowest | High | Chat, collaboration |
| Optimistic | Instant | Medium | User actions |

---

## 1. Polling

Periodically fetch fresh data from the server.

```python
from pynext import Signal, Effect
import asyncio

data = Signal(None)
is_polling = Signal(True)

async def fetch_data():
    """Fetch latest data from server."""
    response = await fetch("/api/data")
    return await response.json()

@Effect
async def poll_loop():
    """Poll for updates every 5 seconds."""
    while is_polling.value:
        try:
            result = await fetch_data()
            data.set(result)
        except Exception as e:
            print(f"Polling error: {e}")
        
        await asyncio.sleep(5)

# Stop polling when component unmounts
def cleanup():
    is_polling.set(False)
```

### Smart Polling

Only poll when the tab is visible:

```python
from pynext import Signal
from pynext.core.client import client_effect, use_storage

# Track visibility state
is_visible = Signal(True)


@client_effect
def track_visibility():
    """
    Track browser tab visibility.
    
    This client_effect runs in the browser and listens for
    visibility changes. Polling stops when tab is hidden.
    """
    # Effect cleanup function is called when the effect re-runs
    pass


# Server action for polling
@server_action
async def poll_for_updates():
    """Fetch latest data from server."""
    # Only runs when called
    data = await get_latest_data()
    return data


def PollingComponent():
    """
    Component that polls for updates.
    
    Uses server action for the actual data fetching,
    with visibility-aware polling on the client.
    """
    return div()[
        # Server action handles the polling interval
        # and respects is_visible signal
    ]
```

> **Note:** For advanced visibility tracking, you can use the `script()` escape hatch for the `visibilitychange` event, or wait for a future `use_visibility()` hook.

---

## 2. Server-Sent Events (SSE)

Server pushes updates to the client.

### Server Side

```python
# pages/api/events.py
from pynext import api_route
from pynext.streaming import EventStream

@api_route("/api/events")
async def events_endpoint(request):
    """SSE endpoint for real-time updates."""
    async def generate():
        while True:
            # Get latest data
            event = await get_latest_event()
            
            if event:
                yield {
                    "event": event["type"],
                    "data": json.dumps(event["data"]),
                }
            
            await asyncio.sleep(1)
    
    return EventStream(generate())
```

### Client Side

For SSE connections, we use PyNext's `client_effect` for browser-specific APIs:

```python
from pynext import Signal
from pynext.core.client import client_effect

notifications = Signal([])
tasks = Signal([])


@client_effect
def setup_sse():
    """
    Connect to SSE endpoint.
    
    This uses client_effect because EventSource is a browser-specific API
    that requires JavaScript. The effect runs after hydration.
    """
    # This will be transpiled to JavaScript
    pass


# The actual SSE connection (using script() as an escape hatch)
# In future versions, PyNext will provide a use_event_source() hook
def SSEConnection():
    """
    Set up Server-Sent Events connection.
    
    Note: SSE is a browser API that requires JavaScript.
    We use script() as an escape hatch for browser-specific APIs.
    """
    return script()["""
        const events = new EventSource('/api/events');
        
        events.addEventListener('notification', (e) => {
            const data = JSON.parse(e.data);
            // Update Signal via PyNext bridge
            __pynext__.getSignal('notifications')?.update((current) => 
                [...current, data].slice(-50)
            );
        });
        
        events.addEventListener('task_update', (e) => {
            const data = JSON.parse(e.data);
            __pynext__.getSignal('tasks')?.update((current) =>
                current.map(t => t.id === data.id ? data : t)
            );
        });
        
        events.onerror = () => {
            // Reconnect on error
            setTimeout(() => events.close(), 1000);
        };
    """]
```

> **Note:** SSE and WebSocket are browser-specific APIs that currently require the `script()` escape hatch. A future PyNext version will provide `use_event_source()` and `use_websocket()` hooks.

---

## 3. Optimistic Updates

Update the UI immediately, then sync with server.

```python
from pynext import Signal, server_action

tasks = Signal([])

@server_action
async def toggle_task_done(task_id: int):
    """Toggle task completion status."""
    # 1. Optimistically update UI
    tasks.set([
        {**t, "done": not t["done"]} if t["id"] == task_id else t
        for t in tasks.value
    ])
    
    # 2. Send to server
    try:
        response = await fetch(f"/api/tasks/{task_id}/toggle", method="POST")
        if not response.ok:
            raise Exception("Server error")
        
        # 3. Server response (optional: update with server state)
        server_task = await response.json()
        tasks.set([
            server_task if t["id"] == task_id else t
            for t in tasks.value
        ])
        
    except Exception as e:
        # 4. Rollback on error
        tasks.set([
            {**t, "done": not t["done"]} if t["id"] == task_id else t
            for t in tasks.value
        ])
        show_error("Failed to update task")
```

### With Rollback State

```python
def create_optimistic_update():
    """Create an optimistic update helper."""
    pending = Signal({})  # Track pending updates
    
    async def optimistic(
        key: str,
        update_fn,
        server_fn,
        rollback_fn=None,
    ):
        # Store original state
        original = pending.value.get(key)
        if original is None:
            pending.set({**pending.value, key: update_fn.__self__.value})
        
        # Apply optimistic update
        update_fn()
        
        try:
            # Call server
            result = await server_fn()
            # Clear pending
            p = pending.value.copy()
            p.pop(key, None)
            pending.set(p)
            return result
        except Exception as e:
            # Rollback
            if rollback_fn:
                rollback_fn()
            elif original is not None:
                update_fn.__self__.set(original)
            raise
    
    return optimistic
```

---

## 4. Real-Time Patterns

### Live Activity Feed

```python
activities = Signal([])

@Effect
def subscribe_to_activities():
    """Subscribe to live activity updates."""
    es = EventSource("/api/activities/stream")
    
    def on_message(event):
        activity = json.loads(event.data)
        activities.update(lambda current: [activity, *current[:49]])
    
    es.addEventListener("activity", on_message)
    
    return lambda: es.close()

def ActivityFeed():
    return div(class_="space-y-2")[
        [ActivityItem(a) for a in activities.value]
    ]
```

### Live Counter

```python
from pynext import Signal

counter = Signal(0)

def LiveCounter():
    return div()[
        # Counter updates in real-time from SSE
        span(class_="text-4xl font-bold")[counter],
        span(class_="text-muted-foreground")[ " active users"],
    ]

# Server pushes updates
# { "event": "counter", "data": "42" }
```

### Presence Indicators

```python
online_users = Signal(set())

@Effect
def track_presence():
    """Track who's online."""
    es = EventSource("/api/presence")
    
    es.addEventListener("join", lambda e: 
        online_users.update(lambda s: s | {json.loads(e.data)["user_id"]})
    )
    
    es.addEventListener("leave", lambda e:
        online_users.update(lambda s: s - {json.loads(e.data)["user_id"]})
    )
    
    return lambda: es.close()

def UserAvatar(user):
    is_online = user.id in online_users.value
    
    return div(class_="relative")[
        Avatar()[...],
        is_online and div(class_=cn(
            "absolute bottom-0 right-0 w-3 h-3 rounded-full",
            "bg-green-500 border-2 border-background",
        )),
    ]
```

---

## 5. Handling Conflicts

When multiple users edit the same data:

```python
from pynext import Signal

last_updated = Signal(None)

@server_action
async def save_changes(data: dict):
    """Save with conflict detection."""
    # Include last known timestamp
    response = await fetch("/api/save", {
        "method": "POST",
        "body": json.dumps({
            **data,
            "last_updated": last_updated.value,
        }),
    })
    
    result = await response.json()
    
    if result.get("conflict"):
        # Server detected a conflict
        return {
            "success": False,
            "conflict": True,
            "server_data": result["current"],
            "message": "Someone else modified this. Review changes.",
        }
    
    # Update our timestamp
    last_updated.set(result["updated_at"])
    return {"success": True}
```

### Merge UI

```python
def ConflictResolver(local_data, server_data, on_resolve):
    return Dialog(open=True)[
        DialogContent()[
            DialogTitle()["Conflict Detected"],
            DialogDescription()[
                "Someone else modified this data. Choose which version to keep."
            ],
            
            div(class_="grid grid-cols-2 gap-4 my-4")[
                div()[
                    h4()["Your Changes"],
                    pre()[json.dumps(local_data, indent=2)],
                ],
                div()[
                    h4()["Server Version"],
                    pre()[json.dumps(server_data, indent=2)],
                ],
            ],
            
            DialogFooter()[
                Button(onclick=lambda: on_resolve("local"))["Keep Mine"],
                Button(onclick=lambda: on_resolve("server"))["Use Server"],
                Button(onclick=lambda: on_resolve("merge"), variant="default")[
                    "Merge"
                ],
            ],
        ],
    ]
```

---

## Choosing a Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Decision Tree                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Need instant feedback for user actions?                    │
│  └─ YES → Use Optimistic Updates                            │
│                                                             │
│  Need server push for notifications/events?                 │
│  └─ YES → Use SSE                                           │
│                                                             │
│  Need bidirectional real-time (chat, collab)?              │
│  └─ YES → Use WebSocket                                     │
│                                                             │
│  Just need periodic refresh of dashboard data?              │
│  └─ YES → Use Polling (simple, good enough)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Polling is fine** — For many use cases, it's the simplest solution
2. **SSE for push** — One-way server-to-client updates
3. **Optimistic for UX** — Instant feedback, rollback on error
4. **Handle conflicts** — Multiple users editing same data
5. **Clean up connections** — Close SSE/WebSocket on unmount

---

## Related Tutorials

- [State Management](./state-management.md) - Managing real-time state
- [Data Tables](./data-tables.md) - Live-updating tables

