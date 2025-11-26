# Tab Visibility Tracking

> **Know when someone is looking at your window.**

## What is Visibility Tracking?

Imagine you're giving a presentation. When the audience looks away, you might pause. When they look back, you continue. That's visibility tracking.

`use_visibility()` tells you when the user is actively viewing your tab vs. when they've switched to another tab or minimized the browser.

## Why Do We Need It?

When users aren't looking at your tab, continuing expensive operations wastes resources:

| Without Visibility Tracking | With Visibility Tracking |
|-----------------------------|--------------------------|
| Polling continues when tab hidden | Polling pauses |
| Animations run invisibly | Animations pause |
| Videos keep playing | Videos pause |
| SSE connections stay active | Can reduce activity |
| Battery drains faster | Battery saved |

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VISIBILITY TRACKING FLOW                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User switches to another tab                                        │
│            │                                                         │
│            ▼                                                         │
│  Browser fires 'visibilitychange' event                             │
│            │                                                         │
│            ▼                                                         │
│  PyNext detects: document.hidden = true                             │
│            │                                                         │
│            ▼                                                         │
│  is_visible signal updates: True → False                            │
│            │                                                         │
│            ▼                                                         │
│  Your code reacts (stop polling, pause animations, etc.)            │
│                                                                      │
│  ════════════════════════════════════════════════════════════       │
│                                                                      │
│  User returns to tab                                                 │
│            │                                                         │
│            ▼                                                         │
│  Browser fires 'visibilitychange' event                             │
│            │                                                         │
│            ▼                                                         │
│  PyNext detects: document.hidden = false                            │
│            │                                                         │
│            ▼                                                         │
│  is_visible signal updates: False → True                            │
│            │                                                         │
│            ▼                                                         │
│  Your code reacts (resume polling, resume animations, etc.)         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Usage

### Step 1: Get the Visibility Signal

```python
from pynext import use_visibility

# Create visibility signal
is_visible = use_visibility()
```

That's it! The signal automatically updates when visibility changes.

### Step 2: Read the Value

```python
# As a property
if is_visible.value:
    print("User is looking at this tab")
else:
    print("User switched to another tab")

# As a callable
visible = is_visible()  # Same as is_visible.value
```

### Step 3: React to Changes

Use with `client_effect` to run code when visibility changes:

```python
from pynext import use_visibility, client_effect

is_visible = use_visibility()

@client_effect
def handle_visibility():
    """React to visibility changes."""
    if is_visible.value:
        # User is back! Resume operations
        start_polling()
        resume_video()
    else:
        # User left. Pause operations
        stop_polling()
        pause_video()
```

---

## Complete Example: Smart Polling

Here's a full example that pauses polling when the tab is hidden:

```python
from pynext import Signal, use_visibility, client_effect, server_action

# Data signal
dashboard_data = Signal(None)
last_updated = Signal(None)

# Get visibility signal
is_visible = use_visibility()

@server_action
async def fetch_dashboard_data():
    """Fetch latest dashboard data from server."""
    data = await db.get_dashboard_stats()
    return data

@client_effect
def smart_polling():
    """
    Poll for updates only when tab is visible.
    
    This saves server resources and battery life when
    the user isn't looking at the page.
    """
    if is_visible.value:
        # Tab is visible — poll every 30 seconds
        result = fetch_dashboard_data()
        dashboard_data.set(result)
        last_updated.set(datetime.now())
        
        # Schedule next poll
        # (In practice, you'd use setInterval)

def Dashboard():
    """Dashboard that updates in real-time."""
    return div()[
        # Show visibility status (for debugging)
        div(class_="text-sm text-muted-foreground mb-4")[
            f"Tab visible: {is_visible.value}",
            f" | Last updated: {last_updated.value}",
        ],
        
        # Dashboard content
        DashboardStats(dashboard_data.value) if dashboard_data.value else
        LoadingSpinner(),
    ]
```

---

## API Reference

### `use_visibility()`

Get a signal that tracks tab visibility.

**Parameters:** None

**Returns:** `VisibilitySignal`

### `VisibilitySignal`

A signal that tracks whether the tab is visible.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Unique signal ID |
| `value` | `bool` | `True` if visible, `False` if hidden |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__call__()` | `bool` | Read current value (same as `.value`) |
| `to_dict()` | `dict` | Serialization for hydration |
| `get_js_init()` | `str` | JS initialization code |

**Usage:**

```python
is_visible = use_visibility()

# Read value
if is_visible.value:
    # Tab is visible
    pass

# Or as callable
if is_visible():
    pass
```

---

## Common Patterns

### Pattern 1: Pause Video When Hidden

```python
is_visible = use_visibility()

def VideoPlayer(video_url):
    video_ref = use_ref("video")
    
    @client_effect
    def handle_visibility():
        video = video_ref.current
        if video:
            if is_visible.value:
                video.play()
            else:
                video.pause()
    
    return video(
        ref=video_ref,
        src=video_url,
        autoplay=True,
    )
```

### Pattern 2: Show "Welcome Back" Message

```python
is_visible = use_visibility()
was_hidden = Signal(False)
show_welcome = Signal(False)

@client_effect
def track_return():
    if not is_visible.value:
        was_hidden.set(True)
    elif was_hidden.value:
        show_welcome.set(True)
        was_hidden.set(False)
        # Hide message after 3 seconds
        # setTimeout(() => show_welcome.set(False), 3000)

def WelcomeBack():
    if show_welcome.value:
        return div(class_="fixed top-4 right-4 bg-green-100 p-4 rounded")[
            "Welcome back! Here's what you missed..."
        ]
    return None
```

### Pattern 3: Reduce SSE Activity When Hidden

```python
is_visible = use_visibility()

# Full activity when visible
sse_active = use_event_source("/api/events", {
    "update": lambda d: handle_update(d) if is_visible.value else None,
})

# Or disconnect entirely when hidden
@client_effect
def manage_sse():
    if is_visible.value:
        sse_active.reconnect()
    else:
        sse_active.close()
```

---

## How It Works Under the Hood

### Browser API

PyNext uses the [Page Visibility API](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API):

```javascript
document.addEventListener('visibilitychange', () => {
    const isVisible = !document.hidden;
    // Update signal
});
```

### Signal Updates

When visibility changes:
1. Browser fires `visibilitychange` event
2. PyNext runtime detects the change
3. Signal value is updated
4. Reactive effects re-run
5. Your UI updates

---

## Troubleshooting

### Signal not updating

**Problem:** `is_visible.value` doesn't change

**Solutions:**
1. Ensure `use_visibility()` is called during render
2. Check that the browser supports Page Visibility API
3. Verify hydration completed (signal is client-side)

### Initial value is wrong

**Problem:** `is_visible.value` is `True` even when tab is hidden

**Note:** The initial value is always `True` (assumed visible). It updates after hydration when the actual state is known.

---

## Related Documentation

- [SSE Connections](./SSE.md) — Pause SSE when hidden
- [Network Status](./ONLINE_STATUS.md) — Detect offline state
- [Client Effects](./CLIENT_RUNTIME.md) — React to changes

