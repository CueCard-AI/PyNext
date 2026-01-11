# PyNext Events API

Complete guide to DOM event handling in PyNext. Type-safe, zero-runtime event APIs that transpile perfectly to JavaScript.

## Overview

### What

PyNext provides full type stubs for all DOM event interfaces:
- **Mouse Events**: click, mousedown, mousemove, wheel, etc.
- **Keyboard Events**: keydown, keyup with key/code properties
- **Touch Events**: touchstart, touchmove with multi-touch support
- **Drag Events**: dragstart, drop with DataTransfer API
- **Form Events**: submit, input, change, focus, blur
- **Custom Events**: User-defined events with detail data

### Why

- **Type Safety**: Full IDE autocompletion for all event properties
- **Zero Runtime**: Pure passthrough transpilation - no overhead
- **AI-Friendly**: Clear, explicit types for LLM assistance
- **Developer Experience**: Python syntax for familiar JavaScript APIs

### When

Use PyNext events whenever you need to:
- Handle user interactions (clicks, keyboard, touch)
- Implement drag-and-drop interfaces
- Build forms with validation
- Create component communication via custom events

### Where

Event handling code lives in `@client` decorated functions that transpile to JavaScript and run in the browser.

### Who

- Frontend developers using Python for web development
- Teams migrating from JavaScript to Python
- Developers who want type safety without TypeScript

---

## Quick Start

```python
from pynext.client import document, MouseEvent, KeyboardEvent

# Mouse click handler
def on_click(event: MouseEvent):
    x = event.clientX
    y = event.clientY
    if event.ctrlKey:
        event.preventDefault()
        handle_ctrl_click()

# Keyboard handler  
def on_keydown(event: KeyboardEvent):
    if event.key == "Escape":
        close_modal()
    elif event.ctrlKey and event.key == "s":
        event.preventDefault()
        save_document()

# Attach listeners
button = document.getElementById("my-button")
button.addEventListener("click", on_click)
document.addEventListener("keydown", on_keydown)
```

---

## Event Types Reference

### Event (Base Class)

All events inherit from this base class.

```python
def handler(event: Event):
    # Read-only properties
    event.type           # "click", "keydown", etc.
    event.target         # Element that triggered event
    event.currentTarget  # Element with listener attached
    event.bubbles        # Does event bubble?
    event.cancelable     # Can be cancelled?
    event.timeStamp      # When event occurred
    event.isTrusted      # User-initiated vs programmatic
    event.defaultPrevented  # Was preventDefault() called?
    
    # Methods
    event.preventDefault()           # Cancel default action
    event.stopPropagation()          # Stop bubbling
    event.stopImmediatePropagation() # Stop all handlers
    event.composedPath()             # Get element path
```

### MouseEvent

For click, mousedown, mouseup, mousemove, mouseenter, mouseleave, contextmenu.

```python
def on_click(event: MouseEvent):
    # Position (viewport)
    x = event.clientX
    y = event.clientY
    
    # Position (document, includes scroll)
    px = event.pageX
    py = event.pageY
    
    # Position (element-relative)
    ox = event.offsetX
    oy = event.offsetY
    
    # Position (screen)
    sx = event.screenX
    sy = event.screenY
    
    # Movement delta (for mousemove)
    dx = event.movementX
    dy = event.movementY
    
    # Button: 0=left, 1=middle, 2=right
    if event.button == 0:
        handle_left_click()
    
    # Buttons bitmask (multiple buttons)
    if event.buttons & 1:  # Primary pressed
        handle_drag()
    
    # Modifier keys
    if event.altKey:
        handle_alt_click()
    if event.ctrlKey:
        handle_ctrl_click()
    if event.shiftKey:
        handle_shift_click()
    if event.metaKey:
        handle_cmd_click()
    
    # Related element (for enter/leave)
    from_el = event.relatedTarget
```

### WheelEvent

For mouse wheel scrolling.

```python
def on_wheel(event: WheelEvent):
    # Scroll amounts
    horizontal = event.deltaX
    vertical = event.deltaY
    depth = event.deltaZ  # Rare
    
    # Delta mode: 0=pixels, 1=lines, 2=pages
    mode = event.deltaMode
    
    # Zoom example
    if event.deltaY > 0:
        zoom_out()
    else:
        zoom_in()
```

### KeyboardEvent

For keydown, keyup events.

```python
def on_keydown(event: KeyboardEvent):
    # Key value (what it represents)
    if event.key == "Enter":
        submit()
    if event.key == "Escape":
        cancel()
    if event.key == "ArrowUp":
        move_up()
    
    # Physical key code (layout-independent)
    if event.code == "KeyW":  # W key position
        move_forward()
    
    # Key state
    if event.repeat:
        return  # Ignore held keys
    
    # IME composition
    if event.isComposing:
        return  # Don't interfere with IME
    
    # Location: 0=standard, 1=left, 2=right, 3=numpad
    if event.location == 3:
        handle_numpad()
    
    # Modifier check
    if event.getModifierState("CapsLock"):
        warn_caps_on()
```

### TouchEvent

For touchstart, touchmove, touchend, touchcancel.

```python
def on_touch_start(event: TouchEvent):
    # All active touches
    for touch in event.touches:
        print(touch.identifier)  # Unique ID
        print(touch.clientX, touch.clientY)
    
    # Touches that changed in this event
    for touch in event.changedTouches:
        track_touch(touch.identifier)
    
    # Touches on target element only
    count = event.targetTouches.length
    
    # Single touch
    if event.touches.length == 1:
        touch = event.touches[0]
        start_drag(touch.pageX, touch.pageY)
    
    # Multi-touch (pinch)
    if event.touches.length == 2:
        t1 = event.touches[0]
        t2 = event.touches[1]
        start_pinch(t1, t2)
```

### Touch

Individual touch point in TouchEvent.

```python
touch = event.touches[0]

touch.identifier     # Unique ID for this touch
touch.target         # Element where touch started
touch.clientX        # Viewport X
touch.clientY        # Viewport Y
touch.pageX          # Document X (with scroll)
touch.pageY          # Document Y (with scroll)
touch.screenX        # Screen X
touch.screenY        # Screen Y
touch.radiusX        # Touch area X radius
touch.radiusY        # Touch area Y radius
touch.rotationAngle  # Rotation 0-90
touch.force          # Pressure 0.0-1.0
```

### DragEvent

For dragstart, drag, dragend, dragenter, dragover, dragleave, drop.

```python
def on_drag_start(event: DragEvent):
    # Set drag data
    event.dataTransfer.setData("text/plain", "hello")
    event.dataTransfer.setData("text/html", "<b>Hello</b>")
    
    # Set allowed effects
    event.dataTransfer.effectAllowed = "copyMove"

def on_drag_over(event: DragEvent):
    event.preventDefault()  # Required to allow drop
    event.dataTransfer.dropEffect = "move"

def on_drop(event: DragEvent):
    event.preventDefault()
    
    # Get drag data
    text = event.dataTransfer.getData("text/plain")
    
    # Check available types
    if "text/html" in event.dataTransfer.types:
        html = event.dataTransfer.getData("text/html")
    
    # Handle dropped files
    for file in event.dataTransfer.files:
        upload(file)
```

### DataTransfer

Data container for drag operations.

```python
dt = event.dataTransfer

# Properties
dt.dropEffect      # "none", "copy", "move", "link"
dt.effectAllowed   # Allowed effects
dt.files           # FileList of dropped files
dt.items           # DataTransferItemList
dt.types           # List of MIME types

# Methods
dt.setData("text/plain", "data")
dt.getData("text/plain")
dt.clearData()
dt.clearData("text/plain")  # Clear specific type
dt.setDragImage(img, 0, 0)  # Custom drag image
```

### FocusEvent

For focus, blur, focusin, focusout.

```python
def on_focus(event: FocusEvent):
    event.target.classList.add("focused")
    
    # Element that lost focus (if any)
    from_element = event.relatedTarget

def on_blur(event: FocusEvent):
    validate(event.target)
    
    # Element gaining focus (if any)
    to_element = event.relatedTarget
```

### InputEvent

For input, beforeinput.

```python
def on_input(event: InputEvent):
    # Data being inserted
    char = event.data  # None for deletions
    
    # Type of input
    if event.inputType == "insertText":
        handle_typing()
    elif event.inputType == "deleteContentBackward":
        handle_backspace()
    elif event.inputType == "insertFromPaste":
        handle_paste()
    
    # IME composition state
    if event.isComposing:
        return  # Wait for composition end
```

### CustomEvent

For user-defined events with arbitrary data.

```python
# Create and dispatch
event = CustomEvent("user-login", {
    "detail": {"userId": 123, "name": "John"},
    "bubbles": True,
    "cancelable": True
})
element.dispatchEvent(event)

# Handle
def on_user_login(event: CustomEvent):
    user_id = event.detail["userId"]
    name = event.detail["name"]
    update_ui(user_id, name)

element.addEventListener("user-login", on_user_login)
```

### PointerEvent

Unified mouse, pen, and touch events.

```python
def on_pointer_down(event: PointerEvent):
    # Pointer type
    if event.pointerType == "touch":
        handle_touch()
    elif event.pointerType == "pen":
        handle_pen(event.pressure)
    elif event.pointerType == "mouse":
        handle_mouse()
    
    # Unique pointer ID
    track_pointer(event.pointerId)
    
    # Pressure (0.0-1.0)
    force = event.pressure
    
    # Pen tilt
    tilt_x = event.tiltX
    tilt_y = event.tiltY
    
    # Is this the primary pointer?
    if event.isPrimary:
        handle_primary()
```

### AnimationEvent & TransitionEvent

For CSS animation and transition events.

```python
def on_animation_end(event: AnimationEvent):
    name = event.animationName
    duration = event.elapsedTime
    pseudo = event.pseudoElement  # "::before", etc.

def on_transition_end(event: TransitionEvent):
    prop = event.propertyName  # "opacity", "transform", etc.
    duration = event.elapsedTime
```

---

## Event Listener Options

### Basic Usage

```python
# Simple listener
el.addEventListener("click", handler)

# Remove listener
el.removeEventListener("click", handler)
```

### Options Object

```python
# Capture phase (runs before bubble)
el.addEventListener("click", handler, {"capture": True})

# Fire only once
el.addEventListener("click", handler, {"once": True})

# Passive (can't call preventDefault)
el.addEventListener("scroll", handler, {"passive": True})

# Combine options
el.addEventListener("touchstart", handler, {
    "capture": True,
    "once": True,
    "passive": True
})
```

### AbortController

```python
controller = AbortController()

el.addEventListener("click", handler, {"signal": controller.signal})

# Later: remove all listeners with this signal
controller.abort()
```

---

## Common Patterns

### Event Delegation

Handle events on a parent for all children:

```python
def on_list_click(event: MouseEvent):
    item = event.target.closest("li")
    if item:
        select_item(item.dataset.id)

list_el.addEventListener("click", on_list_click)
```

### Keyboard Shortcuts

```python
def on_keydown(event: KeyboardEvent):
    if event.ctrlKey or event.metaKey:
        if event.key == "s":
            event.preventDefault()
            save()
        elif event.key == "z":
            event.preventDefault()
            if event.shiftKey:
                redo()
            else:
                undo()

document.addEventListener("keydown", on_keydown)
```

### Drag and Drop

```python
def on_drag_start(event: DragEvent):
    event.dataTransfer.setData("text/plain", event.target.id)
    event.dataTransfer.effectAllowed = "move"

def on_drag_over(event: DragEvent):
    event.preventDefault()

def on_drop(event: DragEvent):
    event.preventDefault()
    id = event.dataTransfer.getData("text/plain")
    item = document.getElementById(id)
    event.target.appendChild(item)
```

### Touch Gestures

```python
start_x = 0

def on_touch_start(event: TouchEvent):
    global start_x
    start_x = event.touches[0].clientX

def on_touch_end(event: TouchEvent):
    dx = event.changedTouches[0].clientX - start_x
    if dx > 50:
        swipe_right()
    elif dx < -50:
        swipe_left()
```

### Custom Events for Components

```python
# Child component emits
def notify_parent(data):
    event = CustomEvent("child-updated", {
        "bubbles": True,
        "detail": data
    })
    el.dispatchEvent(event)

# Parent component listens
parent.addEventListener("child-updated", lambda e: update(e.detail))
```

---

## Composition Events (IME Input)

Handle international text input with Input Method Editors (Chinese, Japanese, Korean).

```python
from pynext.client import document, CompositionEvent

def create_search_input(input_id: str, on_search):
    input_el = document.getElementById(input_id)
    is_composing = False
    
    def on_composition_start(event: CompositionEvent):
        nonlocal is_composing
        is_composing = True
    
    def on_composition_end(event: CompositionEvent):
        nonlocal is_composing
        is_composing = False
        on_search(input_el.value)
    
    def on_input(event):
        if not is_composing:
            on_search(input_el.value)
    
    input_el.addEventListener("compositionstart", on_composition_start)
    input_el.addEventListener("compositionend", on_composition_end)
    input_el.addEventListener("input", on_input)
```

### CompositionEvent Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `str` | Characters being composed or committed |

### Composition Event Types

| Event | When |
|-------|------|
| `compositionstart` | User begins composing (e.g., typing pinyin) |
| `compositionupdate` | Composition text changes as user types |
| `compositionend` | User confirms final characters |

---

## Storage Events (Cross-Tab Sync)

Listen for localStorage/sessionStorage changes from other tabs.

```python
from pynext.client import window, StorageEvent

def sync_state_across_tabs(key: str, on_change):
    def on_storage(event: StorageEvent):
        if event.key == key:
            if event.newValue:
                data = JSON.parse(event.newValue)
                on_change(data)
    
    window.addEventListener("storage", on_storage)

# When you set localStorage in one tab:
# localStorage.setItem("user", JSON.stringify(user))
# The storage event fires in ALL OTHER tabs (not the one that set it)
```

### StorageEvent Properties

| Property | Type | Description |
|----------|------|-------------|
| `key` | `str?` | Changed key (None if storage cleared) |
| `oldValue` | `str?` | Previous value (None if newly added) |
| `newValue` | `str?` | New value (None if removed) |
| `url` | `str` | URL of document that made the change |
| `storageArea` | `Storage` | localStorage or sessionStorage |

---

## AbortController Cleanup

Clean up multiple event listeners with a single call.

```python
class Component:
    def __init__(self, element):
        self.element = element
        self.controller = AbortController()
    
    def mount(self):
        signal = self.controller.signal
        self.element.addEventListener("click", self.on_click, {"signal": signal})
        document.addEventListener("keydown", self.on_keydown, {"signal": signal})
        window.addEventListener("resize", self.on_resize, {"signal": signal})
    
    def unmount(self):
        # All listeners removed with one call!
        self.controller.abort()
```

---

## Message Events

Events for cross-origin messaging, WebSocket, and worker communication.

### MessageEvent

```python
from pynext.client import window, MessageEvent

def on_message(event: MessageEvent):
    # IMPORTANT: Always verify origin for security!
    if event.origin != "https://trusted.com":
        return
    
    data = event.data        # Any serializable data
    origin = event.origin    # Sender's origin
    source = event.source    # Sender's window/worker
    ports = event.ports      # MessagePort array

window.addEventListener("message", on_message)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `Any` | Message payload (string, object, ArrayBuffer, etc.) |
| `origin` | `str` | Origin of the sender (e.g., "https://example.com") |
| `source` | `WindowProxy | None` | Window/Worker that sent the message |
| `ports` | `List[MessagePort]` | Transferred MessagePorts for channel messaging |
| `lastEventId` | `str` | Last event ID (for Server-Sent Events) |

### Use Cases

- `window.addEventListener("message", ...)` - Cross-origin iframe/popup communication
- `ws.addEventListener("message", ...)` - WebSocket messages
- `channel.addEventListener("message", ...)` - BroadcastChannel messages
- `worker.addEventListener("message", ...)` - Web Worker communication

---

## Error Events

Events for runtime script errors and unhandled promise rejections.

### ErrorEvent

```python
from pynext.client import window, ErrorEvent

def on_error(event: ErrorEvent):
    message = event.message     # Error message string
    filename = event.filename   # Script URL
    line = event.lineno         # Line number (1-indexed)
    col = event.colno           # Column number (1-indexed)
    error = event.error         # The Error object (has .stack)

window.addEventListener("error", on_error)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `message` | `str` | Human-readable error message |
| `filename` | `str` | URL of the script where error occurred |
| `lineno` | `int` | Line number (1-indexed) |
| `colno` | `int` | Column number (1-indexed) |
| `error` | `Error | None` | The Error object (access `.stack` for stack trace) |

### Unhandled Promise Rejections

```python
def on_rejection(event):
    reason = event.reason  # The rejection reason/error
    if event.reason:
        console.error(event.reason.stack)

window.addEventListener("unhandledrejection", on_rejection)
```

---

## History Events

Events for browser history and navigation.

### HashChangeEvent

```python
from pynext.client import window, HashChangeEvent

def on_hashchange(event: HashChangeEvent):
    old_url = event.oldURL   # Previous URL with hash
    new_url = event.newURL   # New URL with hash
    new_hash = window.location.hash

window.addEventListener("hashchange", on_hashchange)
```

### PopStateEvent

```python
from pynext.client import window, PopStateEvent

def on_popstate(event: PopStateEvent):
    state = event.state  # State object from pushState/replaceState
    if state:
        route = state["route"]
        render_route(route)

window.addEventListener("popstate", on_popstate)

# Navigate with state
history.pushState({"route": "/about"}, "", "/about")
```

### BeforeUnloadEvent

```python
from pynext.client import window, BeforeUnloadEvent

has_unsaved_changes = False

def on_beforeunload(event: BeforeUnloadEvent):
    if has_unsaved_changes:
        event.preventDefault()
        event.returnValue = ""  # Triggers browser's "Leave site?" dialog

window.addEventListener("beforeunload", on_beforeunload)
```

**Note:** Modern browsers ignore custom `returnValue` messages and show a generic prompt.

---

## Promise Rejection Events

Handle unhandled promise rejections for error monitoring.

### PromiseRejectionEvent

```python
from pynext.client import window, PromiseRejectionEvent

def on_rejection(event: PromiseRejectionEvent):
    promise = event.promise   # The rejected Promise
    reason = event.reason     # Rejection reason (usually an Error)
    
    if reason:
        console.error("Unhandled rejection:", reason.message)
        report_error(reason.stack)
    
    # Optionally prevent browser error logging
    event.preventDefault()

window.addEventListener("unhandledrejection", on_rejection)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `promise` | `Promise` | The Promise that was rejected |
| `reason` | `Any` | The rejection reason (typically an Error object) |

---

## Security Events

Monitor Content Security Policy (CSP) violations.

### SecurityPolicyViolationEvent

```python
from pynext.client import document, SecurityPolicyViolationEvent

def on_csp_violation(event: SecurityPolicyViolationEvent):
    report = {
        "directive": event.violatedDirective,  # e.g., "script-src"
        "blocked": event.blockedURI,
        "document": event.documentURI,
        "source": event.sourceFile,
        "line": event.lineNumber
    }
    send_to_monitoring(report)

document.addEventListener("securitypolicyviolation", on_csp_violation)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `violatedDirective` | `str` | The CSP directive that was violated |
| `effectiveDirective` | `str` | The effective directive |
| `blockedURI` | `str` | URI of the blocked resource |
| `documentURI` | `str` | Document where violation occurred |
| `originalPolicy` | `str` | The full CSP policy string |
| `sourceFile` | `str` | Source file of the violation |
| `lineNumber` | `int` | Line number in source |
| `columnNumber` | `int` | Column number in source |

---

## Page Transition Events

Handle back/forward cache (bfcache) restoration.

### PageTransitionEvent

```python
from pynext.client import window, PageTransitionEvent

def on_pageshow(event: PageTransitionEvent):
    if event.persisted:
        # Page was restored from bfcache
        refresh_stale_data()
        reconnect_websockets()
        update_timestamps()

window.addEventListener("pageshow", on_pageshow)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `persisted` | `bool` | True if page was restored from bfcache |

**Note:** When `persisted` is true, JavaScript didn't re-execute. Timers, WebSockets, and data may be stale.

---

## Progress Events

Track upload/download progress for files and data.

### ProgressEvent

```python
from pynext.client import ProgressEvent

def on_progress(event: ProgressEvent):
    if event.lengthComputable:
        percent = (event.loaded / event.total) * 100
        update_progress_bar(percent)
    else:
        # Total unknown, show indeterminate progress
        show_spinner()

# On XMLHttpRequest
xhr.upload.addEventListener("progress", on_progress)  # Upload
xhr.addEventListener("progress", on_progress)         # Download
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `lengthComputable` | `bool` | True if total size is known |
| `loaded` | `int` | Bytes transferred so far |
| `total` | `int` | Total bytes (only meaningful if lengthComputable) |

---

## Device Motion Events

Access mobile device accelerometer and gyroscope data.

### DeviceMotionEvent

```python
from pynext.client import window, DeviceMotionEvent

def on_motion(event: DeviceMotionEvent):
    accel = event.acceleration
    if accel:
        x, y, z = accel.x, accel.y, accel.z
        detect_shake(x, y, z)
    
    rotation = event.rotationRate
    if rotation:
        console.log(f"Rotating: {rotation.alpha}")

window.addEventListener("devicemotion", on_motion)
```

### DeviceOrientationEvent

```python
from pynext.client import window, DeviceOrientationEvent

def on_orientation(event: DeviceOrientationEvent):
    heading = event.alpha   # 0-360 (compass)
    tilt_fb = event.beta    # -180 to 180 (front/back)
    tilt_lr = event.gamma   # -90 to 90 (left/right)
    
    rotate_compass(heading)

window.addEventListener("deviceorientation", on_orientation)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `acceleration` | `Object` | Acceleration excluding gravity (x, y, z in m/s²) |
| `accelerationIncludingGravity` | `Object` | Acceleration with gravity |
| `rotationRate` | `Object` | Rotation rate (alpha, beta, gamma in deg/s) |
| `interval` | `float` | Interval between events in ms |
| `alpha` | `float` | Compass heading (0-360) |
| `beta` | `float` | Front/back tilt (-180 to 180) |
| `gamma` | `float` | Left/right tilt (-90 to 90) |
| `absolute` | `bool` | True if orientation is absolute (vs device-relative) |

**Note:** iOS 13+ requires user permission. Call `DeviceMotionEvent.requestPermission()` first.

---

## TypeScript Comparison

PyNext event handling is almost identical to TypeScript:

| TypeScript | PyNext |
|------------|--------|
| `(e: MouseEvent) => {}` | `def handler(e: MouseEvent):` |
| `e.preventDefault()` | `e.preventDefault()` |
| `e.target as HTMLElement` | `e.target` (Element type) |
| `e.currentTarget` | `e.currentTarget` |
| `new CustomEvent('x', {detail: y})` | `CustomEvent('x', {"detail": y})` |

---

## Browser Compatibility

All event APIs are native browser features with excellent support:

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| MouseEvent | ✅ | ✅ | ✅ | ✅ |
| KeyboardEvent | ✅ | ✅ | ✅ | ✅ |
| TouchEvent | ✅ | ✅ | ✅ | ✅ |
| DragEvent | ✅ | ✅ | ✅ | ✅ |
| PointerEvent | ✅ | ✅ | ✅ | ✅ |
| CustomEvent | ✅ | ✅ | ✅ | ✅ |
| Event.composedPath | ✅ | ✅ | ✅ | ✅ |
| once/passive options | ✅ | ✅ | ✅ | ✅ |

---

## See Also

- [Events Cookbook](../examples/EVENTS_COOKBOOK.md) - 17 complete mini-application examples
- [DOM API](./DOM_API.md) - Element and document manipulation
- [CSS Styling](./CSS_STYLING.md) - Style manipulation
- [Transpilation Mechanism](../internals/TRANSPILATION_EVENTS.md) - How events transpile

