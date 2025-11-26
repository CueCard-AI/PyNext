# Network Status Detection

> **Know when the internet goes out.**

## What is Network Status Detection?

Imagine driving through a tunnel — your phone loses signal. Apps that handle this gracefully show "You're offline" instead of cryptic error messages. That's network status detection.

`use_online()` tells you when the user's browser has network connectivity, so you can adapt your UI accordingly.

## Why Do We Need It?

Without network detection, your app fails ungracefully:

| Without Detection | With Detection |
|-------------------|----------------|
| Forms submit and fail silently | "You're offline" message |
| Buttons appear clickable but don't work | Buttons disabled with explanation |
| Users get confused error messages | Clear offline indicator |
| Data might be lost | Actions queued for later |

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                   NETWORK STATUS DETECTION                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Network disconnects (WiFi off, cable unplugged, etc.)              │
│            │                                                         │
│            ▼                                                         │
│  Browser fires 'offline' event                                       │
│            │                                                         │
│            ▼                                                         │
│  PyNext detects: navigator.onLine = false                           │
│            │                                                         │
│            ▼                                                         │
│  is_online signal updates: True → False                             │
│            │                                                         │
│            ▼                                                         │
│  Your code reacts (show banner, disable buttons, queue actions)     │
│                                                                      │
│  ════════════════════════════════════════════════════════════       │
│                                                                      │
│  Network reconnects                                                  │
│            │                                                         │
│            ▼                                                         │
│  Browser fires 'online' event                                        │
│            │                                                         │
│            ▼                                                         │
│  PyNext detects: navigator.onLine = true                            │
│            │                                                         │
│            ▼                                                         │
│  is_online signal updates: False → True                             │
│            │                                                         │
│            ▼                                                         │
│  Your code reacts (hide banner, enable buttons, sync queued data)   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Usage

### Step 1: Get the Online Signal

```python
from pynext import use_online

# Create online status signal
is_online = use_online()
```

That's it! The signal automatically updates when connectivity changes.

### Step 2: Read the Value

```python
# As a property
if is_online.value:
    print("Connected to internet")
else:
    print("No internet connection")

# As a callable
online = is_online()  # Same as is_online.value
```

### Step 3: React in Your UI

```python
from pynext import use_online
from pynext.shadcn import Button, Alert, AlertTitle, AlertDescription

is_online = use_online()

def SubmitButton():
    """Button that's disabled when offline."""
    return Button(
        disabled=not is_online.value,
        onclick=submit_form,
    )[
        "Submit" if is_online.value else "Offline - Cannot Submit"
    ]

def OfflineBanner():
    """Banner that appears when offline."""
    if not is_online.value:
        return Alert(variant="destructive", class_="fixed bottom-4 left-4 right-4")[
            AlertTitle()["You're offline"],
            AlertDescription()[
                "Check your internet connection. Changes will sync when you're back online."
            ],
        ]
    return None
```

---

## Complete Example: Offline-Aware Form

Here's a full example of a form that handles offline gracefully:

```python
from pynext import Signal, use_online, server_action
from pynext.shadcn import (
    Card, CardHeader, CardTitle, CardContent, CardFooter,
    Input, Label, Button, Alert, AlertDescription,
)

# Online status
is_online = use_online()

# Form state
form_data = Signal({"name": "", "email": ""})
pending_submit = Signal(None)  # Queued data when offline
submit_error = Signal(None)

@server_action
async def submit_form(data):
    """Submit form to server."""
    await db.create_user(data)
    return {"success": True}

def handle_submit():
    """Handle form submission with offline support."""
    data = form_data.value
    
    if is_online.value:
        # Online: submit immediately
        try:
            submit_form(data)
            form_data.set({"name": "", "email": ""})
        except Exception as e:
            submit_error.set(str(e))
    else:
        # Offline: queue for later
        pending_submit.set(data)

def ContactForm():
    return Card()[
        CardHeader()[
            CardTitle()["Contact Us"],
        ],
        
        CardContent(class_="space-y-4")[
            # Offline warning
            OfflineWarning() if not is_online.value else None,
            
            # Pending submission notice
            PendingNotice() if pending_submit.value else None,
            
            # Form fields
            div()[
                Label()["Name"],
                Input(
                    value=form_data.value["name"],
                    oninput=lambda e: form_data.set({
                        **form_data.value, 
                        "name": e.target.value
                    }),
                ),
            ],
            
            div()[
                Label()["Email"],
                Input(
                    type_="email",
                    value=form_data.value["email"],
                    oninput=lambda e: form_data.set({
                        **form_data.value, 
                        "email": e.target.value
                    }),
                ),
            ],
        ],
        
        CardFooter()[
            Button(
                onclick=handle_submit,
                disabled=not is_online.value and pending_submit.value,
            )[
                "Submit" if is_online.value else "Queue for Later"
            ],
        ],
    ]

def OfflineWarning():
    return Alert(variant="warning", class_="mb-4")[
        AlertDescription()[
            "You're offline. Your submission will be saved and sent when you reconnect."
        ],
    ]

def PendingNotice():
    return Alert(class_="mb-4")[
        AlertDescription()[
            "You have a pending submission. It will be sent when you're back online."
        ],
    ]
```

---

## API Reference

### `use_online()`

Get a signal that tracks network connectivity.

**Parameters:** None

**Returns:** `OnlineSignal`

### `OnlineSignal`

A signal that tracks whether the browser is online.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Unique signal ID |
| `value` | `bool` | `True` if online, `False` if offline |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__call__()` | `bool` | Read current value (same as `.value`) |
| `to_dict()` | `dict` | Serialization for hydration |
| `get_js_init()` | `str` | JS initialization code |

**Usage:**

```python
is_online = use_online()

# Read value
if is_online.value:
    # Browser has network connection
    pass

# Or as callable
if is_online():
    pass
```

---

## Common Patterns

### Pattern 1: Offline Indicator Badge

```python
is_online = use_online()

def NetworkStatus():
    """Show network status in header."""
    if is_online.value:
        return span(class_="text-green-500 flex items-center gap-1")[
            "●", "Online"
        ]
    else:
        return span(class_="text-red-500 flex items-center gap-1")[
            "●", "Offline"
        ]
```

### Pattern 2: Disable Interactive Features

```python
is_online = use_online()

def ActionButtons():
    return div(class_="flex gap-2")[
        Button(
            disabled=not is_online.value,
            onclick=send_message,
        )["Send Message"],
        
        Button(
            disabled=not is_online.value,
            onclick=upload_file,
        )["Upload File"],
        
        # Read-only features still work
        Button(onclick=view_history)["View History"],
    ]
```

### Pattern 3: Queue Actions for Later

```python
is_online = use_online()
action_queue = Signal([])

def queue_action(action):
    """Queue action if offline, execute if online."""
    if is_online.value:
        execute_action(action)
    else:
        action_queue.update(lambda q: [*q, action])

@client_effect
def process_queue():
    """Process queued actions when back online."""
    if is_online.value and action_queue.value:
        for action in action_queue.value:
            execute_action(action)
        action_queue.set([])
```

### Pattern 4: Combined with SSE

```python
is_online = use_online()
is_visible = use_visibility()

# Only connect to SSE when online and visible
should_connect = is_online.value and is_visible.value

@client_effect
def manage_connection():
    if should_connect:
        sse.reconnect()
    else:
        sse.close()
```

---

## How It Works Under the Hood

### Browser API

PyNext uses the [Navigator.onLine](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/onLine) API:

```javascript
// Initial state
const isOnline = navigator.onLine;

// Listen for changes
window.addEventListener('online', () => {
    // Update signal to true
});

window.addEventListener('offline', () => {
    // Update signal to false
});
```

### Important Limitation

`navigator.onLine` only tells you if the browser **thinks** it's connected. It doesn't guarantee:
- The server is reachable
- The internet actually works
- Specific endpoints are available

For critical operations, consider also pinging your server.

---

## Troubleshooting

### Signal not updating

**Problem:** `is_online.value` doesn't change when toggling WiFi

**Solutions:**
1. Ensure `use_online()` is called during render
2. Some browsers have quirks — test in multiple browsers
3. Verify hydration completed (signal is client-side)

### False positives

**Problem:** `is_online.value` is `True` but requests fail

**Explanation:** The browser reports "online" if it has a network interface, even if that network can't reach the internet (e.g., connected to WiFi with no internet).

**Solution:** For critical operations, also check server reachability:

```python
@server_action
async def check_server():
    """Ping server to verify connectivity."""
    return {"status": "ok"}

# Use both signals
can_submit = is_online.value and server_reachable.value
```

---

## Related Documentation

- [SSE Connections](./SSE.md) — Handle offline for real-time features
- [Visibility Tracking](./VISIBILITY.md) — Pause when tab hidden
- [Real-Time Updates](../tutorials/concepts/real-time-updates.md) — Complete guide

