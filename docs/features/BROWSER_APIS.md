# Browser APIs

> **One-liner Python hooks for browser APIs. No JavaScript required. Signals update, components don't re-render.**

## The Problem

Web applications need access to browser APIs for:
- **Real-time communication** (WebSockets)
- **Responsive design** (media queries)
- **Location services** (geolocation)
- **User convenience** (clipboard)
- **UI adaptation** (window size, scroll position)
- **Performance optimization** (lazy loading with intersection observer)

In React, each of these requires:
1. `useState` for the value
2. `useEffect` for setup/cleanup
3. Event listeners that cause re-renders
4. Careful dependency arrays to avoid bugs

**Result: Boilerplate-heavy, error-prone code.**

## The Solution: Signal-Based Browser Hooks

PyNext provides browser API hooks that:

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser API Hooks                         │
├─────────────────────────────────────────────────────────────┤
│  Python Hook              →  Returns Signal                 │
│  ───────────────────────────────────────────────────────── │
│  use_websocket("/api/ws") →  WebSocketHandle                │
│  use_media_query("...")   →  Signal[bool]                   │
│  use_geolocation()        →  GeolocationHandle              │
│  use_clipboard()          →  ClipboardHandle                │
│  use_window_size()        →  WindowSize                     │
│  use_scroll_position()    →  ScrollPosition                 │
│  use_intersection("id")   →  Signal[bool]                   │
├─────────────────────────────────────────────────────────────┤
│  ✅ One line of Python    ✅ No useEffect                   │
│  ✅ No re-renders         ✅ Automatic cleanup              │
│  ✅ Type-safe             ✅ AI-friendly                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

```python
from pynext import (
    use_websocket,    # Real-time communication
    use_media_query,  # Responsive breakpoints
    use_geolocation,  # User location
    use_clipboard,    # Copy/paste
    use_window_size,  # Viewport dimensions
    use_scroll_position,  # Scroll tracking
    use_intersection, # Visibility detection
)
```

---

## 1. WebSocket (`use_websocket`)

### What It Does

Establishes a WebSocket connection to your server for real-time, bidirectional communication.

### Mental Model

```
┌─────────┐  WebSocket  ┌─────────┐
│ Browser │◄───────────►│ Server  │
└─────────┘             └─────────┘
     ▲                       │
     │    messages.update()  │
     └───────────────────────┘
```

### Basic Usage

```python
from pynext import use_websocket

# Create connection
ws = use_websocket("/api/chat")

# Send messages
Button(onclick=lambda: ws.send({"type": "message", "text": "Hello!"}))[
    "Send Message"
]

# Check connection
if ws.connected():
    show_connected_indicator()
```

### Full API

```python
ws = use_websocket(
    url="/api/chat",
    on_message=lambda data: messages.update(lambda m: [*m, data]),
    on_open=lambda: print("Connected!"),
    on_close=lambda: print("Disconnected"),
    on_error=lambda e: print(f"Error: {e}"),
    reconnect=True,           # Auto-reconnect on disconnect
    reconnect_interval=3000,  # 3 seconds between attempts
)

# Handle type
class WebSocketHandle:
    connected() -> bool          # Is connected?
    last_message() -> Any        # Most recent message
    error() -> str | None        # Last error
    
    send(data: dict) -> None     # Send message
    close() -> None              # Close connection
    reconnect_now() -> None      # Manual reconnect
```

### Real-World Example: Chat Application

```python
from pynext import use_websocket, Signal, div, p, input_, button

# State
messages = Signal([])
input_text = Signal("")

# WebSocket with message handler
ws = use_websocket(
    "/api/chat",
    on_message=lambda msg: messages.update(lambda m: [*m, msg][:100])  # Keep last 100
)

def ChatRoom():
    return div(class_="flex flex-col h-screen")[
        # Message list
        div(class_="flex-1 overflow-y-auto p-4")[
            For(messages(), lambda msg: p[msg["text"]])
        ],
        
        # Input
        div(class_="p-4 border-t flex gap-2")[
            input_(
                value=input_text(),
                onchange=lambda e: input_text.set(e.target.value),
                class_="flex-1 px-4 py-2 border rounded"
            ),
            button(
                onclick=lambda: (
                    ws.send({"text": input_text()}),
                    input_text.set("")
                ),
                disabled=not ws.connected(),
                class_="px-4 py-2 bg-blue-500 text-white rounded"
            )["Send"],
        ],
        
        # Connection status
        div(class_="px-4 py-2 text-sm")[
            "🟢 Connected" if ws.connected() else "🔴 Disconnected"
        ]
    ]
```

### Server-Side (FastAPI Example)

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/api/chat")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        data = await websocket.receive_json()
        # Broadcast to all clients
        await websocket.send_json(data)
```

---

## 2. Media Query (`use_media_query`)

### What It Does

Tracks whether a CSS media query matches. Perfect for responsive design.

### Mental Model

```
┌──────────────────────────────────────────────┐
│             Viewport                          │
│  ┌─────────────────────────────────────────┐ │
│  │ width: 1200px                           │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  use_media_query("(max-width: 768px)")       │
│  → Signal[False]  (1200 > 768)               │
│                                              │
│  use_media_query("(min-width: 1024px)")      │
│  → Signal[True]   (1200 >= 1024)             │
└──────────────────────────────────────────────┘
```

### Basic Usage

```python
from pynext import use_media_query

# Track screen size
is_mobile = use_media_query("(max-width: 768px)")

if is_mobile():
    return MobileNav()
else:
    return DesktopNav()
```

### Common Patterns

```python
# Responsive breakpoints
is_mobile = use_media_query("(max-width: 639px)")
is_tablet = use_media_query("(min-width: 640px) and (max-width: 1023px)")
is_desktop = use_media_query("(min-width: 1024px)")

# User preferences
prefers_dark = use_media_query("(prefers-color-scheme: dark)")
reduced_motion = use_media_query("(prefers-reduced-motion: reduce)")
high_contrast = use_media_query("(prefers-contrast: high)")

# Device capabilities
is_touch = use_media_query("(pointer: coarse)")
is_retina = use_media_query("(min-resolution: 2dppx)")
is_landscape = use_media_query("(orientation: landscape)")
```

### Real-World Example: Responsive Layout

```python
from pynext import use_media_query, div

def Dashboard():
    is_mobile = use_media_query("(max-width: 768px)")
    
    if is_mobile():
        # Stack vertically on mobile
        return div(class_="flex flex-col")[
            Sidebar(),
            MainContent(),
        ]
    else:
        # Side by side on desktop
        return div(class_="flex")[
            div(class_="w-64")[Sidebar()],
            div(class_="flex-1")[MainContent()],
        ]
```

---

## 3. Geolocation (`use_geolocation`)

### What It Does

Tracks the user's geographic location using the browser's Geolocation API.

### Mental Model

```
┌─────────────────────────────────────────────────┐
│  📍 Geolocation                                 │
│  ────────────────────────────────────────────── │
│                                                 │
│  Permission: ⏳ prompt → ✅ granted / ❌ denied │
│                                                 │
│  If granted:                                    │
│    latitude()  → 37.7749                        │
│    longitude() → -122.4194                      │
│    accuracy()  → 10 (meters)                    │
│                                                 │
│  watch=True:                                    │
│    Updates as user moves                        │
│                                                 │
│  high_accuracy=True:                            │
│    Uses GPS (more battery)                      │
└─────────────────────────────────────────────────┘
```

### Basic Usage

```python
from pynext import use_geolocation

# One-time location fetch
geo = use_geolocation()

if geo.loading():
    return "Getting your location..."

if geo.error():
    return f"Error: {geo.error()}"

return f"You're at {geo.latitude()}, {geo.longitude()}"
```

### Continuous Tracking

```python
# Watch mode - updates as user moves
geo = use_geolocation(watch=True, high_accuracy=True)

def LocationTracker():
    return div[
        p[f"Latitude: {geo.latitude()}"],
        p[f"Longitude: {geo.longitude()}"],
        p[f"Accuracy: {geo.accuracy()} meters"],
        p[f"Speed: {geo.speed() or 'Stationary'}"],
        
        button(onclick=lambda: geo.stop())["Stop Tracking"]
    ]
```

### Full API

```python
geo = use_geolocation(
    watch=False,           # Continuous tracking
    high_accuracy=False,   # Use GPS
    timeout=10000,         # Max wait time (ms)
    max_age=0,             # Accept cached location age (ms)
)

# Signals
geo.latitude()   # float | None
geo.longitude()  # float | None
geo.accuracy()   # float | None (meters)
geo.altitude()   # float | None (meters)
geo.heading()    # float | None (degrees)
geo.speed()      # float | None (m/s)
geo.loading()    # bool
geo.error()      # str | None
geo.permission() # "prompt" | "granted" | "denied"

# Methods
geo.refresh()    # Request new position
geo.stop()       # Stop watching
```

---

## 4. Clipboard (`use_clipboard`)

### What It Does

Read from and write to the system clipboard.

### Mental Model

```
┌─────────────────────────────────────────────────┐
│  📋 Clipboard                                   │
│  ────────────────────────────────────────────── │
│                                                 │
│  copy("Hello!")                                 │
│    → copies to system clipboard                 │
│    → copied() = True for 2 seconds              │
│                                                 │
│  read()                                         │
│    → requests permission                        │
│    → text() = clipboard contents                │
└─────────────────────────────────────────────────┘
```

### Basic Usage

```python
from pynext import use_clipboard

clipboard = use_clipboard()

# Copy button with feedback
button(onclick=lambda: clipboard.copy(share_url))[
    "✓ Copied!" if clipboard.copied() else "Copy Link"
]
```

### Copy with Toast

```python
from pynext import use_clipboard, Signal

show_toast = Signal(False)

clipboard = use_clipboard()

def CopyButton(text: str):
    return button(
        onclick=lambda: (
            clipboard.copy(text),
            show_toast.set(True),
        )
    )[
        "Copy"
    ]
```

### Read from Clipboard

```python
from pynext import use_clipboard

clipboard = use_clipboard()

def PasteInput():
    return div[
        button(onclick=lambda: clipboard.read())["Paste"],
        
        Show(
            clipboard.text() is not None,
            lambda: p[f"Pasted: {clipboard.text()}"]
        )
    ]
```

---

## 5. Window Size (`use_window_size`)

### What It Does

Tracks browser window dimensions in real-time.

### Mental Model

```
┌─────────────────────────────────────────────────┐
│  🖥️ Window                                      │
│  ────────────────────────────────────────────── │
│                                                 │
│  ┌───────────────────────────────────────┐      │
│  │                              width()  │      │
│  │                              = 1920   │      │
│  │                                       │      │
│  │  height()                             │      │
│  │  = 1080                               │      │
│  │                                       │      │
│  └───────────────────────────────────────┘      │
│                                                 │
│  Resize event → signals update (RAF throttled)  │
└─────────────────────────────────────────────────┘
```

### Basic Usage

```python
from pynext import use_window_size

size = use_window_size()

# Access dimensions
width = size.width()
height = size.height()

# Or as tuple
w, h = size()
```

### Responsive Layout

```python
from pynext import use_window_size

def ResponsiveColumns():
    size = use_window_size()
    
    # Calculate columns based on width
    columns = 1
    if size.width() >= 640:
        columns = 2
    if size.width() >= 1024:
        columns = 3
    if size.width() >= 1280:
        columns = 4
    
    return div(
        style=f"display: grid; grid-template-columns: repeat({columns}, 1fr);"
    )[
        For(items, lambda item: Card(item))
    ]
```

### Aspect Ratio

```python
from pynext import use_window_size

def VideoPlayer():
    size = use_window_size()
    
    is_portrait = size.height() > size.width()
    
    if is_portrait:
        return VerticalVideoLayout()
    else:
        return HorizontalVideoLayout()
```

---

## 6. Scroll Position (`use_scroll_position`)

### What It Does

Tracks and controls page scroll position.

### Mental Model

```
┌─────────────────────────────────────────────────┐
│  📜 Scroll                                      │
│  ────────────────────────────────────────────── │
│                                                 │
│  ┌─────────────────────────────────────┐        │
│  │ ▲ x() = 0                          │        │
│  │ │                                  │ ←── Viewport
│  │ │                                  │        │
│  └─────────────────────────────────────┘        │
│    │                                            │
│    │ y() = 500px                                │
│    │                                            │
│    │ progress() = 0.25 (25% scrolled)           │
│    ▼                                            │
│  ════════════════════════════════════════       │
│              Document End                        │
└─────────────────────────────────────────────────┘
```

### Basic Usage

```python
from pynext import use_scroll_position

scroll = use_scroll_position()

# Read position
x, y = scroll()
progress = scroll.progress()  # 0.0 to 1.0
```

### Back to Top Button

```python
from pynext import use_scroll_position, div, button

def BackToTop():
    scroll = use_scroll_position()
    
    # Show button when scrolled down
    if scroll.progress() < 0.1:
        return None
    
    return button(
        onclick=lambda: scroll.to_top(),
        class_="fixed bottom-4 right-4 p-4 bg-blue-500 rounded-full"
    )["↑"]
```

### Reading Progress Indicator

```python
from pynext import use_scroll_position

def ReadingProgress():
    scroll = use_scroll_position()
    
    return div(
        class_="fixed top-0 left-0 h-1 bg-blue-500 transition-all",
        style=f"width: {scroll.progress() * 100}%"
    )
```

### Scroll Methods

```python
scroll = use_scroll_position()

# Scroll to position
scroll.to(0, 500)              # Smooth scroll to y=500
scroll.to(0, 500, smooth=False) # Instant jump

# Convenience methods
scroll.to_top()                # Scroll to top
scroll.to_bottom()             # Scroll to bottom
scroll.to_element("section-2") # Scroll element into view
```

---

## 7. Intersection Observer (`use_intersection`)

### What It Does

Tracks when an element enters or exits the viewport. Perfect for lazy loading and animations.

### Mental Model

```
┌─────────────────────────────────────────────────┐
│  👁️ Intersection Observer                       │
│  ────────────────────────────────────────────── │
│                                                 │
│  ┌─────────────────────────────┐                │
│  │      Viewport              │                │
│  │                            │                │
│  │  ┌──────────────────────┐  │ is_visible()   │
│  │  │  #hero-section       │  │ = True         │
│  │  └──────────────────────┘  │ ratio() = 0.8  │
│  │                            │                │
│  └─────────────────────────────┘                │
│                                                 │
│  threshold=0.5 → True when 50% visible          │
│  root_margin="100px" → Trigger 100px early      │
└─────────────────────────────────────────────────┘
```

### Basic Usage

```python
from pynext import use_intersection

# Track when element is visible
is_visible = use_intersection("hero-section")

if is_visible():
    start_animation()
```

### Lazy Loading Images

```python
from pynext import use_intersection, div, img

def LazyImage(src: str, alt: str):
    container_id = f"img-{hash(src)}"
    is_visible = use_intersection(container_id)
    
    return div(id=container_id)[
        img(src=src, alt=alt) if is_visible() else Placeholder()
    ]
```

### Animate on Scroll

```python
from pynext import use_intersection

def AnimatedSection(section_id: str, children):
    is_visible = use_intersection(
        section_id,
        threshold=0.2  # Trigger when 20% visible
    )
    
    return div(
        id=section_id,
        class_=f"transition-all duration-700 {
            'opacity-100 translate-y-0' if is_visible() 
            else 'opacity-0 translate-y-8'
        }"
    )[children]
```

### Infinite Scroll

```python
from pynext import use_intersection, Signal

items = Signal([])
page = Signal(1)

def InfiniteList():
    # Watch the trigger element
    bottom_visible = use_intersection(
        "load-trigger",
        root_margin="200px"  # Trigger 200px before visible
    )
    
    # Load more when trigger is visible
    if bottom_visible():
        load_more_items()
    
    return div[
        For(items(), lambda item: ItemCard(item)),
        
        # Invisible trigger at bottom
        div(id="load-trigger", class_="h-1")
    ]
```

---

## Comparison with React

### React (Verbose)

```jsx
function useWebSocket(url) {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      setMessages(prev => [...prev, JSON.parse(e.data)]);
    };
    
    setSocket(ws);
    
    return () => ws.close();
  }, [url]);
  
  return { socket, connected, messages };
}
```

### PyNext (Simple)

```python
ws = use_websocket(
    "/api/chat",
    on_message=lambda msg: messages.update(lambda m: [*m, msg])
)
```

---

## Performance

| Hook | React (useEffect) | PyNext |
|------|-------------------|--------|
| WebSocket | Re-renders on message | Signal update only |
| Media Query | Re-renders component | Signal update only |
| Window Size | Debounced re-render | RAF-throttled signal |
| Scroll | Throttled re-render | RAF-throttled signal |
| Intersection | Re-renders on visibility | Signal update only |

### Why Signals Are Faster

```
React: Event → setState → Re-render → Diff → DOM update
PyNext: Event → Signal update → Surgical DOM update

No Virtual DOM, no diffing, no component tree traversal.
```

---

## Bundle Size

| Runtime | Size (minified) |
|---------|-----------------|
| browser.js | ~3KB |
| websocket.js | ~2KB |
| **Total** | **~5KB** |

Compare to React hooks implementations that add 10-20KB+ of library code.

---

## Testing

All hooks come with **328 comprehensive unit tests** covering:

| Category | Tests |
|----------|-------|
| WebSocket | 54 tests (base + edge cases) |
| Media Query | 40 tests (base + edge cases) |
| Geolocation | 45 tests (base + edge cases) |
| Clipboard | 40 tests (base + edge cases) |
| Window Size | 30 tests (base + edge cases) |
| Scroll Position | 40 tests (base + edge cases) |
| Intersection Observer | 40 tests (base + edge cases) |
| Integration | 30 tests (multiple hooks) |
| Error Handling | 20 tests |
| JS Runtime | 4 tests |

Test coverage includes:
- Creation and initialization
- Signal values and updates
- JavaScript code generation
- Hydration data serialization
- Singleton/memoization behavior
- Edge cases and error handling
- Integration scenarios
- Stress tests

Run tests:

```bash
pytest tests/unit/test_browser_apis.py -v
```

---

## First Principles Summary

1. **One Hook = One API** — Each browser feature has exactly one hook
2. **Signal-Based** — No re-renders, just surgical DOM updates
3. **Automatic Cleanup** — No need for cleanup effects
4. **Type-Safe** — Full IDE support and autocompletion
5. **Server-Safe** — All hooks return sensible defaults during SSR
6. **RAF Throttled** — Scroll and resize are automatically optimized

---

## Related Documentation

- [SSE (Server-Sent Events)](./SSE.md) — One-way server push
- [Client Runtime](../contributing/RUNTIME_ARCHITECTURE.md) — How signals work
- [Real-Time Updates](../tutorials/concepts/real-time-updates.md) — Tutorial

