# PyNext Events Cookbook

Complete, copy-paste-ready examples for common event handling patterns in PyNext applications.

---

## 1. Infinite Scroll

Load more content as user scrolls near the bottom of the page.

```python
from pynext.client import document, window

loading = False
page = 1

def on_scroll(event):
    global loading, page
    
    # Check if near bottom
    scroll_top = document.documentElement.scrollTop
    scroll_height = document.documentElement.scrollHeight
    client_height = document.documentElement.clientHeight
    
    if scroll_top + client_height >= scroll_height - 100:
        if not loading:
            loading = True
            page += 1
            fetch_more_items(page)

def fetch_more_items(page_num):
    global loading
    # Fetch items from API
    fetch(f"/api/items?page={page_num}").then(on_response)

def on_response(response):
    global loading
    response.json().then(lambda data: append_items(data))
    loading = False

def append_items(items):
    container = document.getElementById("items")
    for item in items:
        el = document.createElement("div")
        el.className = "item"
        el.textContent = item["title"]
        container.appendChild(el)

# Initialize
window.addEventListener("scroll", on_scroll, {"passive": True})
```

**Key Points:**
- Use `{"passive": True}` for scroll listeners (better performance)
- Check `scrollTop + clientHeight >= scrollHeight - 100` for near-bottom detection
- Use a loading flag to prevent duplicate requests

---

## 2. Keyboard Shortcuts Manager

Register and handle global keyboard shortcuts.

```python
from pynext.client import document, KeyboardEvent

shortcuts = {}

def register_shortcut(keys: str, action):
    """
    Register a keyboard shortcut.
    
    Args:
        keys: Shortcut string like 'ctrl+s', 'meta+shift+p', 'escape'
        action: Callback function to execute
    
    Example:
        register_shortcut("ctrl+s", save_document)
        register_shortcut("escape", close_modal)
    """
    shortcuts[keys] = action

def on_keydown(event: KeyboardEvent):
    # Skip if typing in an input
    if event.target.tagName in ["INPUT", "TEXTAREA"]:
        if event.key != "Escape":  # Allow Escape in inputs
            return
    
    # Build key combo string
    parts = []
    if event.ctrlKey:
        parts.append("ctrl")
    if event.metaKey:
        parts.append("meta")
    if event.shiftKey:
        parts.append("shift")
    if event.altKey:
        parts.append("alt")
    parts.append(event.key.lower())
    
    combo = "+".join(parts)
    
    if combo in shortcuts:
        event.preventDefault()
        shortcuts[combo]()

# Register shortcuts
register_shortcut("ctrl+s", save_document)
register_shortcut("meta+s", save_document)  # Mac
register_shortcut("ctrl+z", undo)
register_shortcut("ctrl+shift+z", redo)
register_shortcut("meta+shift+p", open_command_palette)
register_shortcut("escape", close_modal)

# Start listening
document.addEventListener("keydown", on_keydown)
```

**Key Points:**
- Check both `ctrlKey` and `metaKey` for cross-platform support
- Skip shortcuts when typing in inputs (except Escape)
- Use `event.key.lower()` for case-insensitive matching

---

## 3. Drag-and-Drop File Upload

Create a file drop zone with visual feedback.

```python
from pynext.client import document, DragEvent

def create_dropzone(element_id: str, on_files):
    """
    Create a file drop zone.
    
    Args:
        element_id: ID of the drop zone element
        on_files: Callback receiving list of dropped files
    """
    dropzone = document.getElementById(element_id)
    
    def on_drag_enter(event: DragEvent):
        event.preventDefault()
        dropzone.classList.add("drag-over")
    
    def on_drag_over(event: DragEvent):
        event.preventDefault()
        event.dataTransfer.dropEffect = "copy"
    
    def on_drag_leave(event: DragEvent):
        # Only remove class if leaving the dropzone entirely
        if not dropzone.contains(event.relatedTarget):
            dropzone.classList.remove("drag-over")
    
    def on_drop(event: DragEvent):
        event.preventDefault()
        dropzone.classList.remove("drag-over")
        
        files = []
        for file in event.dataTransfer.files:
            files.append(file)
        
        if files:
            on_files(files)
    
    dropzone.addEventListener("dragenter", on_drag_enter)
    dropzone.addEventListener("dragover", on_drag_over)
    dropzone.addEventListener("dragleave", on_drag_leave)
    dropzone.addEventListener("drop", on_drop)

# Usage
def handle_upload(files):
    for file in files:
        print(f"Uploading {file.name} ({file.size} bytes)")
        upload_to_server(file)

create_dropzone("upload-area", handle_upload)
```

**Key Points:**
- Always call `event.preventDefault()` in dragover/drop handlers
- Set `dropEffect` to show the correct cursor
- Check `relatedTarget` in dragleave to avoid flicker

---

## 4. Touch Gesture Recognizer

Detect swipes and taps on touch devices.

```python
from pynext.client import document, TouchEvent

class GestureRecognizer:
    """
    Recognize touch gestures on an element.
    
    Override on_swipe_left(), on_swipe_right(), on_tap() in subclass.
    """
    
    def __init__(self, element):
        self.element = element
        self.start_x = 0
        self.start_y = 0
        self.start_time = 0
        
        element.addEventListener("touchstart", self.on_touch_start)
        element.addEventListener("touchend", self.on_touch_end)
        element.addEventListener("touchmove", self.on_touch_move, {"passive": False})
    
    def on_touch_start(self, event: TouchEvent):
        if event.touches.length == 1:
            touch = event.touches[0]
            self.start_x = touch.clientX
            self.start_y = touch.clientY
            self.start_time = event.timeStamp
    
    def on_touch_end(self, event: TouchEvent):
        if event.changedTouches.length == 1:
            touch = event.changedTouches[0]
            dx = touch.clientX - self.start_x
            dy = touch.clientY - self.start_y
            duration = event.timeStamp - self.start_time
            
            # Detect swipe (fast horizontal movement)
            if abs(dx) > 50 and abs(dy) < 100 and duration < 300:
                if dx > 0:
                    self.on_swipe_right()
                else:
                    self.on_swipe_left()
            
            # Detect tap (small movement, quick)
            elif abs(dx) < 10 and abs(dy) < 10 and duration < 200:
                self.on_tap()
    
    def on_touch_move(self, event: TouchEvent):
        # Prevent scroll while detecting gesture
        event.preventDefault()
    
    def on_swipe_left(self):
        """Override in subclass."""
        pass
    
    def on_swipe_right(self):
        """Override in subclass."""
        pass
    
    def on_tap(self):
        """Override in subclass."""
        pass


# Usage
class CardGestures(GestureRecognizer):
    def on_swipe_left(self):
        show_next_card()
    
    def on_swipe_right(self):
        show_previous_card()
    
    def on_tap(self):
        flip_card()

card = document.getElementById("card")
gestures = CardGestures(card)
```

**Key Points:**
- Use `{"passive": False}` to allow `preventDefault()` on touchmove
- Check `event.changedTouches` in touchend (not `touches`)
- Use `timeStamp` to measure gesture duration

---

## 5. Cross-Tab State Sync

Synchronize state across browser tabs using localStorage events.

```python
from pynext.client import window, localStorage

def sync_state_across_tabs(key: str, on_change):
    """
    Listen for storage changes from other tabs.
    
    Note: The storage event only fires in OTHER tabs,
    not the one that made the change.
    
    Args:
        key: Storage key to watch
        on_change: Callback receiving the new data
    """
    def on_storage(event):
        if event.key == key:
            if event.newValue:
                data = JSON.parse(event.newValue)
                on_change(data)
            else:
                on_change(None)  # Key was removed
    
    window.addEventListener("storage", on_storage)

def broadcast_state(key: str, data):
    """
    Broadcast state to all other tabs.
    
    Args:
        key: Storage key
        data: Data to broadcast (will be JSON-serialized)
    """
    localStorage.setItem(key, JSON.stringify(data))

# Usage
def on_user_change(user):
    if user:
        update_header(user)
    else:
        show_login_prompt()

# Start listening for changes from other tabs
sync_state_across_tabs("current-user", on_user_change)

# When user logs in (broadcasts to other tabs):
def on_login_success(user):
    broadcast_state("current-user", {
        "id": user.id,
        "name": user.name,
        "avatar": user.avatar_url
    })

# When user logs out:
def on_logout():
    localStorage.removeItem("current-user")
```

**Key Points:**
- StorageEvent only fires in OTHER tabs, not the one making changes
- Check `event.key` to filter for specific keys
- Handle `newValue` being None (key was removed)

---

## 6. Media Player Controls

Build custom video player controls.

```python
from pynext.client import document

def create_media_player(video_id: str):
    """
    Attach custom controls to a video element.
    
    Expected HTML structure:
    <div class="player">
        <video id="video"></video>
        <div class="controls">
            <button id="play-btn">Play</button>
            <div id="progress"></div>
            <span id="time">0:00</span>
            <input id="volume" type="range" min="0" max="1" step="0.1">
        </div>
    </div>
    """
    video = document.getElementById(video_id)
    play_btn = document.getElementById("play-btn")
    progress = document.getElementById("progress")
    time_display = document.getElementById("time")
    volume_slider = document.getElementById("volume")
    
    def on_play(event):
        play_btn.textContent = "Pause"
        play_btn.classList.add("playing")
    
    def on_pause(event):
        play_btn.textContent = "Play"
        play_btn.classList.remove("playing")
    
    def on_timeupdate(event):
        current = video.currentTime
        duration = video.duration
        
        if duration > 0:
            # Update progress bar
            percent = (current / duration) * 100
            progress.style.width = f"{percent}%"
            
            # Update time display
            mins = int(current // 60)
            secs = int(current % 60)
            time_display.textContent = f"{mins}:{secs:02d}"
    
    def on_ended(event):
        play_btn.textContent = "Replay"
        video.currentTime = 0
    
    def toggle_play(event):
        if video.paused:
            video.play()
        else:
            video.pause()
    
    def on_volume_change(event):
        video.volume = float(volume_slider.value)
    
    # Video events
    video.addEventListener("play", on_play)
    video.addEventListener("pause", on_pause)
    video.addEventListener("timeupdate", on_timeupdate)
    video.addEventListener("ended", on_ended)
    
    # Control events
    play_btn.addEventListener("click", toggle_play)
    volume_slider.addEventListener("input", on_volume_change)

# Initialize
create_media_player("video")
```

**Key Points:**
- Use `timeupdate` for progress tracking (fires frequently)
- Check `duration > 0` before calculating progress
- Use `video.paused` to check current state

---

## 7. Event Cleanup with AbortController

Clean up all event listeners with a single call.

```python
from pynext.client import document, window

class Component:
    """
    Base component with automatic event cleanup.
    
    Usage:
        class MyComponent(Component):
            def mount(self):
                super().mount()
                self.on("click", self.element, self.on_click)
                self.on("keydown", document, self.on_keydown)
            
            def on_click(self, event):
                pass
    """
    
    def __init__(self, element):
        self.element = element
        self.controller = AbortController()
    
    def on(self, event_type, target, handler, options=None):
        """
        Add event listener with automatic cleanup.
        
        Args:
            event_type: Event type (e.g., "click")
            target: Target element
            handler: Event handler function
            options: Additional listener options
        """
        opts = {"signal": self.controller.signal}
        if options:
            opts.update(options)
        target.addEventListener(event_type, handler, opts)
    
    def mount(self):
        """
        Setup component. Override in subclass.
        Call super().mount() first.
        """
        pass
    
    def unmount(self):
        """
        Clean up all event listeners.
        Call this when removing the component.
        """
        self.controller.abort()


# Example usage
class Modal(Component):
    def mount(self):
        super().mount()
        
        # All these listeners are cleaned up with one unmount() call
        self.on("click", self.element.querySelector(".close"), self.close)
        self.on("click", self.element.querySelector(".backdrop"), self.close)
        self.on("keydown", document, self.on_keydown)
        self.on("resize", window, self.on_resize)
    
    def on_keydown(self, event):
        if event.key == "Escape":
            self.close()
    
    def on_resize(self, event):
        self.reposition()
    
    def close(self, event=None):
        if event:
            event.preventDefault()
        self.unmount()
        self.element.remove()
    
    def reposition(self):
        # Center the modal
        pass

# Usage
modal_el = document.getElementById("modal")
modal = Modal(modal_el)
modal.mount()

# Later, when closing:
modal.unmount()  # All listeners removed!
```

**Key Points:**
- Create one `AbortController` per component
- Pass `signal` to all `addEventListener` calls
- Call `controller.abort()` to remove all listeners at once

---

## 8. IME-Aware Search Input

Handle international text input correctly.

```python
from pynext.client import document

def create_search_input(input_id: str, on_search, debounce_ms=300):
    """
    Create a search input that handles IME input correctly.
    
    IME (Input Method Editor) is used for Chinese, Japanese, Korean,
    and other languages. During composition, we should NOT trigger
    searches until the user commits their input.
    
    Args:
        input_id: ID of the input element
        on_search: Callback receiving search query
        debounce_ms: Debounce delay in milliseconds
    """
    input_el = document.getElementById(input_id)
    is_composing = False
    timeout_id = None
    
    def on_composition_start(event):
        nonlocal is_composing
        is_composing = True
    
    def on_composition_end(event):
        nonlocal is_composing
        is_composing = False
        # Trigger search with final composed text
        trigger_search()
    
    def on_input(event):
        if not is_composing:
            # Only search when not composing
            debounced_search()
    
    def debounced_search():
        nonlocal timeout_id
        if timeout_id:
            clearTimeout(timeout_id)
        timeout_id = setTimeout(trigger_search, debounce_ms)
    
    def trigger_search():
        nonlocal timeout_id
        timeout_id = None
        on_search(input_el.value)
    
    def on_keydown(event):
        # Allow Enter to submit even during composition
        if event.key == "Enter" and not event.isComposing:
            if timeout_id:
                clearTimeout(timeout_id)
            trigger_search()
    
    input_el.addEventListener("compositionstart", on_composition_start)
    input_el.addEventListener("compositionend", on_composition_end)
    input_el.addEventListener("input", on_input)
    input_el.addEventListener("keydown", on_keydown)

# Usage
def do_search(query):
    print(f"Searching for: {query}")
    fetch(f"/api/search?q={encodeURIComponent(query)}").then(show_results)

search_input = create_search_input("search", do_search)
```

**Key Points:**
- Track `is_composing` state with composition events
- Check `event.isComposing` on keydown for Enter handling
- Combine with debouncing for better UX

---

## 9. WebSocket Real-Time Chat (Production-Ready)

A complete, production-ready WebSocket chat client with all the features you'd expect
in a real application: reconnection, typing indicators, message status, presence,
offline queuing, and health monitoring.

### Why This Pattern Works

WebSocket connections are inherently fragile - networks fail, servers restart, users
switch between WiFi and cellular. A production chat needs to handle all of this
gracefully while providing a seamless user experience.

**The key principles:**
1. **Never lose messages** - Queue messages when offline, send when reconnected
2. **Always reconnect** - Use exponential backoff to avoid overwhelming the server
3. **Show status** - Users need to know if they're connected or not
4. **Optimistic UI** - Show the message immediately, confirm later
5. **Health checks** - Detect stale connections before the user notices

### The Complete Implementation

```python
from pynext.client import document, window, navigator

# =============================================================================
# PRODUCTION-READY WEBSOCKET CHAT CLIENT
# =============================================================================
#
# This is a complete, copy-paste-ready chat client that handles:
#
# ✅ Automatic reconnection with exponential backoff
# ✅ Typing indicators ("John is typing...")
# ✅ Message status (sending → sent → delivered → read)
# ✅ User presence (online/offline/away)
# ✅ Offline message queue (never lose a message)
# ✅ Connection health monitoring (ping/pong heartbeat)
# ✅ Room/channel management
# ✅ Message history with infinite scroll
#
# =============================================================================


class ChatClient:
    """
    A full-featured WebSocket chat client.
    
    WHY USE A CLASS?
    ----------------
    We use a class here because we have lots of state to manage:
    - The WebSocket connection itself
    - Reconnection timers and attempt counts
    - Current room, typing users, pending messages
    - Callback functions for different event types
    
    A class keeps all this organized and makes the code easier to test.
    
    HOW IT WORKS
    ------------
    1. Call ChatClient(...) with your server URL and auth token
    2. Set callback functions (on_message, on_typing, etc.)
    3. Call .connect() to establish the WebSocket
    4. Call .join_room("room-id") to join a chat room
    5. Call .send_message("Hello!") to send messages
    6. The client handles reconnection, queuing, etc. automatically
    
    TRANSPILATION NOTE
    ------------------
    This class transpiles directly to a JavaScript class. The syntax is
    identical - Python classes become JS classes with zero runtime overhead.
    """
    
    def __init__(self, ws_url: str, user_id: str, auth_token: str):
        """
        Initialize the chat client.
        
        Args:
            ws_url: WebSocket server URL (e.g., "wss://chat.example.com/ws")
            user_id: Current user's ID for identifying own messages
            auth_token: JWT or session token for authentication
        
        WHY PASS AUTH TOKEN?
        --------------------
        WebSocket connections can't use HTTP headers for authentication
        (unlike fetch requests). We pass the token in the URL query string
        or send it as the first message after connecting.
        """
        # Connection settings
        self.ws_url = ws_url
        self.user_id = user_id
        self.auth_token = auth_token
        self.ws = None  # Will hold the WebSocket instance
        
        # =====================================================================
        # RECONNECTION SETTINGS
        # =====================================================================
        # These control how we handle disconnections.
        #
        # WHY EXPONENTIAL BACKOFF?
        # ------------------------
        # If the server goes down, we don't want 10,000 clients all trying
        # to reconnect at exactly the same time. By doubling the delay each
        # attempt (1s → 2s → 4s → 8s...), we spread out the load.
        #
        # The max_delay caps this at 30 seconds so users don't wait forever.
        # The max_attempts prevents infinite loops if the server is truly dead.
        
        self.reconnect_delay = 1000    # Start at 1 second
        self.max_delay = 30000         # Cap at 30 seconds
        self.reconnect_attempts = 0    # Track how many times we've tried
        self.max_attempts = 10         # Give up after 10 failed attempts
        
        # =====================================================================
        # CONNECTION STATE
        # =====================================================================
        # We track various pieces of state to provide a great UX.
        
        self.is_connected = False      # Are we currently connected?
        self.current_room = None       # Which chat room are we in?
        self.typing_users = {}         # Dict of user_id → username for typing
        self.typing_timeout = None     # Timer to auto-clear typing status
        
        # =====================================================================
        # OFFLINE MESSAGE QUEUE
        # =====================================================================
        # When the user sends a message while offline, we queue it here.
        # Once reconnected, we flush the queue and send all pending messages.
        # This ensures the user never loses a message!
        
        self.message_queue = []
        
        # =====================================================================
        # PENDING MESSAGE ACKNOWLEDGMENTS
        # =====================================================================
        # When we send a message, we don't know if the server received it
        # until we get an "ack" (acknowledgment) back. We store callbacks
        # here so we can update the UI when the server confirms.
        #
        # Format: { message_id: callback_function }
        
        self.pending_messages = {}
        
        # =====================================================================
        # CALLBACK FUNCTIONS
        # =====================================================================
        # The app using this client sets these to handle different events.
        # This is the "observer pattern" - the client notifies the app
        # when things happen, without knowing the details of the app's UI.
        
        self.on_message = None       # Called when a message is received
        self.on_typing = None        # Called when typing status changes
        self.on_presence = None      # Called when user goes online/offline
        self.on_status_change = None # Called when connection status changes
        
        # =====================================================================
        # HEALTH MONITORING
        # =====================================================================
        # WebSocket connections can become "zombie" connections - the TCP
        # socket is still open but no data can flow through. We use ping/pong
        # heartbeats to detect this and trigger a reconnect.
        
        self.ping_interval = None    # Timer ID for periodic pings
        self.last_pong = Date.now()  # Timestamp of last pong received
    
    # =========================================================================
    # CONNECTION MANAGEMENT
    # =========================================================================
    
    def connect(self):
        """
        Establish the WebSocket connection.
        
        HOW WEBSOCKET AUTHENTICATION WORKS
        ----------------------------------
        Unlike HTTP requests where you can set Authorization headers,
        WebSocket handshakes happen before you can send any data.
        
        Common approaches:
        1. Token in URL query string (what we do here)
        2. Token in a cookie (if same-origin)
        3. Send token as first message after connect
        
        We use the URL approach because it's simplest and works cross-origin.
        The server reads the token from the URL and validates it.
        
        TRANSPILATION NOTE
        ------------------
        `WebSocket(url)` transpiles directly to `new WebSocket(url)` in JS.
        The browser's native WebSocket API is used - no polyfills needed.
        """
        # Build URL with auth token
        # The server will validate this token and identify the user
        url = f"{self.ws_url}?token={self.auth_token}"
        
        # Create the WebSocket connection
        # This is a NATIVE browser API - it connects to the server immediately
        self.ws = WebSocket(url)
        
        # Attach event listeners for the WebSocket lifecycle
        # These events are fired by the browser when things happen
        self.ws.addEventListener("open", self._on_open)
        self.ws.addEventListener("message", self._on_message)
        self.ws.addEventListener("close", self._on_close)
        self.ws.addEventListener("error", self._on_error)
    
    def _on_open(self, event):
        """
        Handle successful WebSocket connection.
        
        This fires when the WebSocket handshake completes successfully.
        At this point we can send and receive messages.
        
        WHAT WE DO HERE
        ---------------
        1. Update our state to "connected"
        2. Reset reconnection delay (since we succeeded)
        3. Start the ping/pong heartbeat
        4. Send any queued messages from when we were offline
        5. Rejoin our chat room (if we were in one before disconnect)
        """
        self.is_connected = True
        
        # Reset reconnection backoff since we connected successfully
        # Next time we disconnect, we'll start at 1 second again
        self.reconnect_delay = 1000
        self.reconnect_attempts = 0
        
        console.log("✅ Connected to chat server")
        
        # Notify the app that we're online
        # The app might show a green dot in the UI
        self._update_status("online")
        
        # Start heartbeat to detect stale connections
        # See _start_ping() for why this is important
        self._start_ping()
        
        # If we had messages queued while offline, send them now
        # This ensures the user never loses a message!
        self._flush_queue()
        
        # If we were in a room before disconnecting, rejoin it
        # This provides a seamless experience - the user doesn't
        # have to manually rejoin after a network blip
        if self.current_room:
            self.join_room(self.current_room)
    
    def _on_close(self, event: CloseEvent):
        """
        Handle WebSocket disconnection.
        
        WHY CLOSE EVENTS MATTER
        -----------------------
        The close event tells us WHY the connection closed:
        
        - event.code: Numeric code (1000 = normal, 1006 = abnormal, etc.)
        - event.reason: Human-readable reason string
        - event.wasClean: True if we received a proper close frame
        
        COMMON CLOSE CODES
        ------------------
        1000: Normal closure (intentional disconnect)
        1001: Going away (page is navigating away)
        1006: Abnormal closure (connection dropped without close frame)
        1011: Server error
        4001: Custom code for authentication failure (we define this)
        
        RECONNECTION STRATEGY
        ---------------------
        We don't always want to reconnect:
        - 1000: User intentionally disconnected, don't reconnect
        - 4001: Auth failed, reconnecting won't help
        - Other codes: Something went wrong, try to reconnect
        
        We use exponential backoff to avoid thundering herd problems.
        """
        self.is_connected = False
        
        # Stop the ping/pong heartbeat since we're disconnected
        self._stop_ping()
        
        # Log what happened (helpful for debugging)
        if event.wasClean:
            console.log(f"Connection closed cleanly: {event.code} - {event.reason}")
        else:
            console.warn(f"Connection lost unexpectedly! Code: {event.code}")
        
        # Notify the app that we're offline
        self._update_status("offline")
        
        # Check if we should reconnect
        # Don't reconnect on intentional close (1000) or auth failure (4001)
        if event.code == 1000:
            console.log("User disconnected intentionally, not reconnecting")
            return
        
        if event.code == 4001:
            console.error("Authentication failed, not reconnecting")
            self._update_status("auth_failed")
            return
        
        # Try to reconnect with exponential backoff
        if self.reconnect_attempts < self.max_attempts:
            self.reconnect_attempts += 1
            
            console.log(
                f"Reconnecting in {self.reconnect_delay}ms... "
                f"(attempt {self.reconnect_attempts}/{self.max_attempts})"
            )
            
            # Schedule reconnection
            setTimeout(self.connect, self.reconnect_delay)
            
            # Double the delay for next time (exponential backoff)
            # But cap at max_delay to avoid waiting forever
            self.reconnect_delay = Math.min(
                self.reconnect_delay * 2,
                self.max_delay
            )
        else:
            console.error("Max reconnection attempts reached, giving up")
            self._update_status("disconnected")
    
    def _on_error(self, event):
        """
        Handle WebSocket errors.
        
        NOTE: WebSocket errors are frustratingly opaque for security reasons.
        The browser doesn't tell us what went wrong - just that something did.
        The actual error details are in the close event that follows.
        
        We just log here; the close handler does the actual recovery.
        """
        console.error("WebSocket error occurred (see close event for details)")
    
    def disconnect(self):
        """
        Gracefully close the WebSocket connection.
        
        WHY USE 1000?
        -------------
        Code 1000 means "normal closure". When the server sees this,
        it knows the client disconnected intentionally.
        
        Our _on_close handler checks for 1000 and skips reconnection.
        """
        if self.ws:
            self.ws.close(1000, "User disconnected")
    
    # =========================================================================
    # HEALTH MONITORING (PING/PONG HEARTBEAT)
    # =========================================================================
    
    def _start_ping(self):
        """
        Start sending periodic pings to detect stale connections.
        
        WHY WE NEED THIS
        ----------------
        TCP connections can become "zombie" connections where:
        - The socket is still technically open
        - But no data can actually flow through
        - The browser doesn't know the connection is dead
        
        This happens when:
        - Network switches (WiFi to cellular)
        - NAT timeout (router forgot about the connection)
        - Firewall issues
        
        By sending pings every 30 seconds, we can detect when the
        server stops responding and trigger a reconnect.
        
        HOW IT WORKS
        ------------
        1. Every 30 seconds, send a ping with a timestamp
        2. Server responds with a pong
        3. If we haven't received a pong in 35 seconds, assume dead connection
        4. Close and reconnect
        """
        def ping():
            if self.is_connected:
                # Send ping with timestamp (server will echo it back)
                self._send({
                    "type": "ping",
                    "timestamp": Date.now()
                })
                
                # Check if we received a pong recently
                # If not, the connection is probably dead
                time_since_pong = Date.now() - self.last_pong
                
                if time_since_pong > 35000:  # 35 seconds
                    console.warn(
                        f"No pong received in {time_since_pong}ms, "
                        "connection might be dead. Reconnecting..."
                    )
                    # Force close to trigger reconnection
                    self.ws.close()
        
        # Run ping every 30 seconds
        self.ping_interval = setInterval(ping, 30000)
    
    def _stop_ping(self):
        """Stop the ping/pong heartbeat."""
        if self.ping_interval:
            clearInterval(self.ping_interval)
            self.ping_interval = None
    
    # =========================================================================
    # MESSAGE HANDLING
    # =========================================================================
    
    def _on_message(self, event: MessageEvent):
        """
        Handle incoming WebSocket messages.
        
        HOW MESSAGE ROUTING WORKS
        -------------------------
        All messages from the server come through this one handler.
        We use a "type" field to route them to the right handler.
        
        This is a common pattern - you could also use separate
        WebSocket connections for different message types, but
        that's wasteful and harder to manage.
        
        MESSAGE TYPES WE HANDLE
        -----------------------
        - pong: Response to our ping (health check)
        - message: A chat message from another user
        - typing: Someone started/stopped typing
        - presence: Someone went online/offline
        - ack: Server acknowledged our message
        - read: Someone read a message
        - history: Response to history request
        - error: Server-side error
        """
        # event.data contains the raw string from the server
        # We expect JSON, so parse it
        data = JSON.parse(event.data)
        
        # Route based on message type
        msg_type = data["type"]
        
        if msg_type == "pong":
            # Update our last pong time for health monitoring
            self.last_pong = Date.now()
        
        elif msg_type == "message":
            self._handle_chat_message(data)
        
        elif msg_type == "typing":
            self._handle_typing(data)
        
        elif msg_type == "presence":
            self._handle_presence(data)
        
        elif msg_type == "ack":
            self._handle_ack(data)
        
        elif msg_type == "read":
            self._handle_read_receipt(data)
        
        elif msg_type == "history":
            self._handle_history(data)
        
        elif msg_type == "error":
            console.error(f"Server error: {data['message']}")
    
    def _handle_chat_message(self, data):
        """
        Process an incoming chat message.
        
        WHAT WE DO
        ----------
        1. Build a message object with all the info the UI needs
        2. Send a "delivered" receipt back to the server
        3. Call the on_message callback so the app can show the message
        
        WHY SEND DELIVERY RECEIPTS?
        ---------------------------
        This lets the sender know their message was received.
        They'll see ✓✓ instead of ✓ in their UI.
        """
        message = {
            "id": data["id"],
            "user_id": data["user_id"],
            "username": data["username"],
            "text": data["text"],
            "timestamp": data["timestamp"],
            "attachments": data.get("attachments", []),
            "status": "received"
        }
        
        # Tell the server we received this message
        # The sender's client will update from "sent" to "delivered"
        self._send({
            "type": "delivered",
            "message_id": data["id"]
        })
        
        # Notify the app to render this message
        if self.on_message:
            self.on_message(message)
    
    def _handle_typing(self, data):
        """
        Handle typing indicator updates.
        
        HOW TYPING INDICATORS WORK
        --------------------------
        1. When user starts typing, client sends {type: "typing", is_typing: true}
        2. Server broadcasts to all room members
        3. We update our typing_users dict
        4. We call on_typing with the list of usernames
        5. The app shows "John is typing..." or "3 people are typing..."
        
        The typing status auto-clears after 3 seconds if we don't get
        another typing message (in case the stop message is lost).
        """
        user_id = data["user_id"]
        username = data["username"]
        is_typing = data["is_typing"]
        
        if is_typing:
            # Add to typing users
            self.typing_users[user_id] = username
        elif user_id in self.typing_users:
            # Remove from typing users
            del self.typing_users[user_id]
        
        # Notify the app with updated list
        if self.on_typing:
            typing_list = list(self.typing_users.values())
            self.on_typing(typing_list)
    
    def _handle_presence(self, data):
        """
        Handle user online/offline status updates.
        
        PRESENCE STATES
        ---------------
        - online: User is actively using the app
        - away: User hasn't interacted recently
        - offline: User disconnected
        
        The server typically broadcasts presence changes to all room members.
        """
        if self.on_presence:
            self.on_presence({
                "user_id": data["user_id"],
                "status": data["status"],
                "last_seen": data.get("last_seen")
            })
    
    def _handle_ack(self, data):
        """
        Handle message acknowledgment from server.
        
        WHAT IS AN ACK?
        ---------------
        When we send a message, we don't know if the server got it.
        The server sends an "ack" to confirm receipt.
        
        This lets us update the UI:
        - Before ack: Show "sending..." or a spinner
        - After ack: Show ✓ (sent)
        
        Later, when the recipient's client sends "delivered":
        - We get a delivery notification
        - Show ✓✓ (delivered)
        """
        msg_id = data["message_id"]
        
        # Look up the callback we stored when sending
        if msg_id in self.pending_messages:
            callback = self.pending_messages[msg_id]
            del self.pending_messages[msg_id]
            
            # Call the callback with the new status
            if callback:
                callback("sent")
    
    def _handle_read_receipt(self, data):
        """Handle notification that someone read a message."""
        # The app can use this to show blue checkmarks
        # Implementation depends on your UI needs
        pass
    
    def _handle_history(self, data):
        """
        Handle message history response.
        
        WHEN THIS IS USED
        -----------------
        When the user scrolls to the top of the chat to load older messages,
        we request history from the server. This handler processes the response.
        """
        messages = data["messages"]
        
        # Pass each message to the app
        if self.on_message:
            for msg in messages:
                self.on_message(msg)
    
    # =========================================================================
    # SENDING MESSAGES
    # =========================================================================
    
    def _send(self, data):
        """
        Send data to the server, with offline queuing.
        
        WHY QUEUE MESSAGES?
        -------------------
        If the user sends a message while offline (or during reconnection),
        we don't want to lose it! We queue it and send when reconnected.
        
        This is critical for user experience - nobody wants their message
        to disappear into the void.
        """
        if self.is_connected and self.ws.readyState == WebSocket.OPEN:
            # We're connected, send immediately
            self.ws.send(JSON.stringify(data))
        else:
            # We're offline, queue for later
            self.message_queue.append(data)
            console.log(f"Queued message for later (queue size: {len(self.message_queue)})")
    
    def _flush_queue(self):
        """
        Send all queued messages after reconnection.
        
        This is called from _on_open() when we successfully reconnect.
        Messages are sent in order (FIFO - first in, first out).
        """
        queue_size = len(self.message_queue)
        if queue_size > 0:
            console.log(f"Flushing {queue_size} queued messages...")
        
        while len(self.message_queue) > 0:
            data = self.message_queue.pop(0)  # Remove from front
            self._send(data)
    
    def send_message(self, text: str, attachments=None, on_status=None):
        """
        Send a chat message.
        
        Args:
            text: The message text
            attachments: Optional list of attachment objects
            on_status: Optional callback for status updates
        
        Returns:
            The message ID (useful for tracking/updating UI)
        
        HOW MESSAGE SENDING WORKS
        -------------------------
        1. Generate a unique message ID
        2. Build the message object
        3. Store the status callback for later (when we get ack)
        4. Send via WebSocket (or queue if offline)
        5. Return the ID so the app can track this message
        
        OPTIMISTIC UI
        -------------
        The app should show the message immediately with "sending" status,
        then update to "sent" when we call the on_status callback.
        This makes the app feel fast and responsive.
        """
        # Generate unique ID: user_id + timestamp + random string
        msg_id = self._generate_id()
        
        message = {
            "type": "message",
            "id": msg_id,
            "room": self.current_room,
            "text": text,
            "attachments": attachments or []
        }
        
        # Store callback to call when we get ack
        if on_status:
            self.pending_messages[msg_id] = on_status
        
        # Send (or queue if offline)
        self._send(message)
        
        return msg_id
    
    def send_typing(self, is_typing: bool):
        """
        Send typing indicator.
        
        DEBOUNCING
        ----------
        We don't want to spam the server with typing events.
        We set a 3-second timeout that auto-sends is_typing=False.
        
        This handles the case where the user stops typing but doesn't
        explicitly trigger a "stop typing" event.
        """
        # Clear any existing timeout
        if self.typing_timeout:
            clearTimeout(self.typing_timeout)
        
        # Send typing status
        self._send({
            "type": "typing",
            "room": self.current_room,
            "is_typing": is_typing
        })
        
        # If starting to type, set timeout to auto-stop
        if is_typing:
            self.typing_timeout = setTimeout(
                lambda: self.send_typing(False),
                3000  # Auto-stop after 3 seconds of no activity
            )
    
    def mark_as_read(self, message_id: str):
        """
        Mark a message as read.
        
        This sends a read receipt to the server, which broadcasts
        to the sender so they can show blue checkmarks.
        """
        self._send({
            "type": "read",
            "message_id": message_id
        })
    
    # =========================================================================
    # ROOM MANAGEMENT
    # =========================================================================
    
    def join_room(self, room_id: str):
        """
        Join a chat room.
        
        After joining, you'll receive:
        - Messages sent to this room
        - Typing indicators from room members
        - Presence updates for room members
        """
        self.current_room = room_id
        
        self._send({
            "type": "join",
            "room": room_id
        })
        
        console.log(f"Joined room: {room_id}")
    
    def leave_room(self):
        """Leave the current room."""
        if self.current_room:
            self._send({
                "type": "leave",
                "room": self.current_room
            })
            
            console.log(f"Left room: {self.current_room}")
            self.current_room = None
    
    def load_history(self, before_id=None, limit=50):
        """
        Load message history.
        
        Args:
            before_id: Load messages older than this ID (for pagination)
            limit: Maximum number of messages to load
        
        INFINITE SCROLL
        ---------------
        Call this when the user scrolls to the top of the message list.
        Pass the ID of the oldest visible message as before_id.
        """
        self._send({
            "type": "get_history",
            "room": self.current_room,
            "before_id": before_id,
            "limit": limit
        })
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def _generate_id(self):
        """
        Generate a unique message ID.
        
        Format: {user_id}_{timestamp}_{random}
        
        This ensures uniqueness even if two users send at the same millisecond.
        """
        random_part = Math.random().toString(36)[2:9]
        return f"{self.user_id}_{Date.now()}_{random_part}"
    
    def _update_status(self, status):
        """Notify the app of connection status change."""
        if self.on_status_change:
            self.on_status_change(status)


# =============================================================================
# COMPLETE USAGE EXAMPLE
# =============================================================================
# This shows how to wire up the ChatClient to a real UI.
# =============================================================================

def init_chat_app():
    """
    Initialize a complete chat application.
    
    This function:
    1. Creates the ChatClient
    2. Wires up all the callbacks to update the UI
    3. Sets up event listeners for user interactions
    4. Handles infinite scroll for message history
    5. Cleans up on page unload
    """
    
    # =========================================================================
    # CREATE THE CLIENT
    # =========================================================================
    
    chat = ChatClient(
        ws_url="wss://chat.example.com/ws",
        user_id=get_current_user_id(),    # Your auth system
        auth_token=get_auth_token()        # Your auth system
    )
    
    # =========================================================================
    # GET UI ELEMENTS
    # =========================================================================
    
    messages_el = document.getElementById("messages")
    input_el = document.getElementById("message-input")
    send_btn = document.getElementById("send-btn")
    status_el = document.getElementById("connection-status")
    typing_el = document.getElementById("typing-indicator")
    
    # =========================================================================
    # HANDLE INCOMING MESSAGES
    # =========================================================================
    
    def on_message(message):
        """
        Render a chat message in the UI.
        
        This creates the DOM structure for a message bubble:
        
        <div class="message own">
          <img class="avatar" src="..." />
          <div class="content">
            <span class="username">John</span>
            <p>Hello world!</p>
            <span class="timestamp">2:34 PM</span>
            <span class="status sent">✓</span>
          </div>
        </div>
        """
        # Create message container
        msg_el = document.createElement("div")
        
        # Add 'own' class if this is our message (for styling)
        is_own = message["user_id"] == chat.user_id
        msg_el.className = f"message {'own' if is_own else ''}"
        msg_el.id = f"msg-{message['id']}"
        
        # Avatar
        avatar = document.createElement("img")
        avatar.className = "avatar"
        avatar.src = f"/api/users/{message['user_id']}/avatar"
        avatar.alt = message["username"]
        
        # Content container
        content = document.createElement("div")
        content.className = "content"
        
        # Username
        username = document.createElement("span")
        username.className = "username"
        username.textContent = message["username"]
        
        # Message text
        text = document.createElement("p")
        text.textContent = message["text"]
        
        # Timestamp
        time_span = document.createElement("span")
        time_span.className = "timestamp"
        time_span.textContent = format_time(message["timestamp"])
        
        # Status indicator (for own messages)
        status = document.createElement("span")
        status.className = f"status {message.get('status', '')}"
        status.id = f"status-{message['id']}"
        
        # Status symbols:
        # sending: ○ (empty circle)
        # sent: ✓
        # delivered: ✓✓
        # read: ✓✓ (blue)
        
        # Assemble the message
        content.appendChild(username)
        content.appendChild(text)
        content.appendChild(time_span)
        if is_own:
            content.appendChild(status)
        
        msg_el.appendChild(avatar)
        msg_el.appendChild(content)
        
        # Add to messages container
        messages_el.appendChild(msg_el)
        
        # Scroll to bottom to show new message
        messages_el.scrollTop = messages_el.scrollHeight
        
        # Mark as read if it's not our own message
        if not is_own:
            chat.mark_as_read(message["id"])
    
    # =========================================================================
    # HANDLE TYPING INDICATORS
    # =========================================================================
    
    def on_typing(typing_users):
        """
        Update the typing indicator.
        
        Shows:
        - Nothing if nobody is typing
        - "John is typing..." for one person
        - "John and Jane are typing..." for two people
        - "3 people are typing..." for more
        """
        count = len(typing_users)
        
        if count == 0:
            typing_el.style.display = "none"
        elif count == 1:
            typing_el.textContent = f"{typing_users[0]} is typing..."
            typing_el.style.display = "block"
        elif count == 2:
            typing_el.textContent = f"{typing_users[0]} and {typing_users[1]} are typing..."
            typing_el.style.display = "block"
        else:
            typing_el.textContent = f"{count} people are typing..."
            typing_el.style.display = "block"
    
    # =========================================================================
    # HANDLE CONNECTION STATUS
    # =========================================================================
    
    def on_status_change(status):
        """
        Update the connection status indicator.
        
        This should update a visual indicator so users know
        if they're connected or not.
        """
        status_el.className = f"status-indicator {status}"
        
        status_text = {
            "online": "Connected",
            "offline": "Connecting...",
            "disconnected": "Disconnected",
            "auth_failed": "Authentication Failed"
        }
        
        status_el.textContent = status_text.get(status, status)
    
    # =========================================================================
    # HANDLE USER PRESENCE
    # =========================================================================
    
    def on_presence(data):
        """
        Update presence indicator for a user.
        
        This finds the user in the member list and updates
        their online/offline indicator.
        """
        user_el = document.querySelector(f"[data-user-id='{data['user_id']}']")
        
        if user_el:
            indicator = user_el.querySelector(".presence")
            indicator.className = f"presence {data['status']}"
            
            # If offline, show last seen time
            if data["status"] == "offline" and data.get("last_seen"):
                indicator.title = f"Last seen: {format_time(data['last_seen'])}"
    
    # =========================================================================
    # SET UP CALLBACKS
    # =========================================================================
    
    chat.on_message = on_message
    chat.on_typing = on_typing
    chat.on_status_change = on_status_change
    chat.on_presence = on_presence
    
    # =========================================================================
    # SEND MESSAGE HANDLER
    # =========================================================================
    
    def on_send(event):
        """
        Handle send button click or form submit.
        """
        event.preventDefault()
        
        text = input_el.value.strip()
        if not text:
            return
        
        # Send the message and get its ID
        # We pass a callback to update the status when ack'd
        msg_id = chat.send_message(
            text,
            on_status=lambda status: update_message_status(msg_id, status)
        )
        
        # OPTIMISTIC UI: Show message immediately with "sending" status
        # This makes the app feel instant, even on slow connections
        on_message({
            "id": msg_id,
            "user_id": chat.user_id,
            "username": "You",
            "text": text,
            "timestamp": Date.now(),
            "status": "sending"
        })
        
        # Clear input
        input_el.value = ""
        
        # Stop typing indicator
        chat.send_typing(False)
    
    def update_message_status(msg_id, status):
        """Update the status indicator for a message."""
        status_el = document.getElementById(f"status-{msg_id}")
        if status_el:
            status_el.className = f"status {status}"
    
    # =========================================================================
    # TYPING INDICATOR ON INPUT
    # =========================================================================
    
    def on_input(event):
        """Send typing indicator when user types."""
        chat.send_typing(True)
    
    # =========================================================================
    # INFINITE SCROLL FOR HISTORY
    # =========================================================================
    
    def on_scroll(event):
        """Load more history when scrolled to top."""
        if messages_el.scrollTop == 0:
            # Get the ID of the first (oldest) visible message
            first_msg = messages_el.querySelector(".message")
            
            if first_msg:
                msg_id = first_msg.id.replace("msg-", "")
                chat.load_history(before_id=msg_id)
    
    # =========================================================================
    # ATTACH EVENT LISTENERS
    # =========================================================================
    
    send_btn.addEventListener("click", on_send)
    document.getElementById("chat-form").addEventListener("submit", on_send)
    input_el.addEventListener("input", on_input)
    messages_el.addEventListener("scroll", on_scroll)
    
    # =========================================================================
    # CONNECT AND JOIN ROOM
    # =========================================================================
    
    chat.connect()
    chat.join_room("general")
    
    # =========================================================================
    # CLEANUP ON PAGE UNLOAD
    # =========================================================================
    
    def on_unload(event):
        """Gracefully disconnect when leaving the page."""
        chat.disconnect()
    
    window.addEventListener("beforeunload", on_unload)
    
    return chat


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_time(timestamp):
    """Format a timestamp for display."""
    date = Date(timestamp)
    return date.toLocaleTimeString()

def get_current_user_id():
    """Get the current user's ID from your auth system."""
    # This would come from your app's auth system
    return window.currentUserId

def get_auth_token():
    """Get the auth token from your auth system."""
    # This would come from localStorage, cookies, or your auth system
    return localStorage.getItem("auth_token")
```

### Key Points

**Connection Lifecycle:**
- `WebSocket(url)` creates the connection immediately
- `addEventListener("open", ...)` fires when handshake completes
- `addEventListener("close", ...)` fires when connection ends
- `event.code` and `event.wasClean` tell you why it closed

**Exponential Backoff:**
- Start at 1 second, double each failure
- Cap at 30 seconds to avoid waiting forever
- Reset to 1 second on successful reconnect

**Offline Queue:**
- Store messages in an array when offline
- Flush the queue on reconnect
- User never loses a message!

**Health Monitoring:**
- Ping every 30 seconds
- If no pong in 35 seconds, assume connection is dead
- Force close to trigger reconnection

**Optimistic UI:**
- Show message immediately with "sending" status
- Update to "sent" when server acknowledges
- Update to "delivered" when recipient confirms

---

## 10. Cross-Window Messaging (iframe/popup)

Secure communication between windows using postMessage.

```python
from pynext.client import window, document

# === Parent Window ===
def setup_iframe_communication(iframe_id: str, allowed_origin: str):
    """
    Set up secure communication with an iframe.
    
    Args:
        iframe_id: The iframe element ID
        allowed_origin: Only accept messages from this origin
    """
    iframe = document.getElementById(iframe_id)
    
    def on_message(event):
        # SECURITY: Always verify origin!
        if event.origin != allowed_origin:
            console.warn(f"Blocked message from {event.origin}")
            return
        
        # Handle the message
        data = event.data
        if data["type"] == "ready":
            console.log("iframe is ready")
            # Send initial data
            send_to_iframe({"type": "init", "user": current_user})
        elif data["type"] == "action":
            handle_iframe_action(data["action"])
    
    def send_to_iframe(message):
        iframe.contentWindow.postMessage(message, allowed_origin)
    
    window.addEventListener("message", on_message)
    
    return {"send": send_to_iframe}

# === Child Window (inside iframe) ===
def setup_parent_communication(parent_origin: str):
    """
    Set up communication with the parent window.
    
    Args:
        parent_origin: Only accept messages from parent origin
    """
    def on_message(event):
        if event.origin != parent_origin:
            return
        
        data = event.data
        if data["type"] == "init":
            initialize_with_user(data["user"])
    
    def send_to_parent(message):
        window.parent.postMessage(message, parent_origin)
    
    window.addEventListener("message", on_message)
    
    # Notify parent we're ready
    send_to_parent({"type": "ready"})
    
    return {"send": send_to_parent}

# Usage in parent
comm = setup_iframe_communication("payment-iframe", "https://payment.example.com")
comm["send"]({"type": "process", "amount": 99.99})
```

**Key Points:**
- **Always verify `event.origin`** for security
- Use `event.source.postMessage()` to reply to sender
- Specify target origin in `postMessage(data, origin)` - never use `"*"` in production
- Access the source window via `event.source`

---

## 11. Global Error Boundary

Centralized error handling with error reporting service integration.

```python
from pynext.client import window, document

def setup_error_boundary(report_endpoint: str = None, on_error_callback = None):
    """
    Set up global error handling and reporting.
    
    Args:
        report_endpoint: URL to send error reports (optional)
        on_error_callback: Custom error handler (optional)
    """
    error_count = 0
    max_errors = 10  # Rate limit error reports
    
    def format_error(event):
        """Format ErrorEvent for reporting."""
        return {
            "type": "runtime_error",
            "message": event.message,
            "source": event.filename,
            "line": event.lineno,
            "column": event.colno,
            "stack": event.error.stack if event.error else None,
            "url": window.location.href,
            "userAgent": navigator.userAgent,
            "timestamp": Date.now()
        }
    
    def format_rejection(event):
        """Format PromiseRejectionEvent for reporting."""
        reason = event.reason
        return {
            "type": "unhandled_rejection",
            "message": str(reason) if reason else "Unknown rejection",
            "stack": reason.stack if reason and hasattr(reason, 'stack') else None,
            "url": window.location.href,
            "timestamp": Date.now()
        }
    
    def send_report(error_data):
        """Send error report to server."""
        nonlocal error_count
        if report_endpoint and error_count < max_errors:
            error_count += 1
            fetch(report_endpoint, {
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": JSON.stringify(error_data)
            }).catch(lambda e: console.error("Failed to send error report"))
    
    def on_error(event):
        """Handle runtime errors."""
        error_data = format_error(event)
        
        # Log to console
        console.error("Runtime Error:", error_data["message"])
        
        # Call custom handler if provided
        if on_error_callback:
            on_error_callback(error_data)
        
        # Send to reporting service
        send_report(error_data)
        
        # Show user-friendly error UI (optional)
        show_error_toast("Something went wrong. We've been notified.")
    
    def on_rejection(event):
        """Handle unhandled promise rejections."""
        error_data = format_rejection(event)
        
        console.error("Unhandled Rejection:", error_data["message"])
        
        if on_error_callback:
            on_error_callback(error_data)
        
        send_report(error_data)
    
    window.addEventListener("error", on_error)
    window.addEventListener("unhandledrejection", on_rejection)
    
    # Return cleanup function
    def cleanup():
        window.removeEventListener("error", on_error)
        window.removeEventListener("unhandledrejection", on_rejection)
    
    return cleanup

# Usage
cleanup = setup_error_boundary(
    report_endpoint="https://errors.example.com/report",
    on_error_callback=lambda e: analytics.track("error", e)
)

# For testing (triggers error)
def trigger_test_error():
    undefined_variable  # This will be caught!
```

**Key Points:**
- Use `window.addEventListener("error", handler)` for script errors
- Use `window.addEventListener("unhandledrejection", handler)` for promise rejections
- Access `event.message`, `event.filename`, `event.lineno`, `event.colno`
- Get the actual Error object via `event.error`
- Get rejection reason via `event.reason`
- Rate limit error reports to prevent flooding

---

## 12. Form Validation with Real-Time Feedback

A complete form validation system with live feedback as the user types.
This is one of the most common patterns in web development.

### Why Real-Time Validation?

Users hate submitting a form only to see a list of errors. Real-time validation:
- Shows errors immediately as the user types
- Provides positive feedback (green checkmarks) for valid fields
- Reduces form abandonment
- Improves accessibility (screen readers announce errors)

### The Complete Implementation

```python
from pynext.client import document

# =============================================================================
# REAL-TIME FORM VALIDATION
# =============================================================================
#
# This pattern validates form fields as the user types, providing:
# - Immediate error feedback
# - Success indicators for valid fields
# - Debounced validation (doesn't validate on every keystroke)
# - Accessible error messages
#
# =============================================================================


def create_validated_form(form_id: str, on_submit):
    """
    Create a form with real-time validation.
    
    Args:
        form_id: The ID of the form element
        on_submit: Callback when form is valid and submitted
    
    HOW IT WORKS
    ------------
    1. Attach 'input' event listeners to each field
    2. When user types, validate after a short delay (debounce)
    3. Show error or success indicator
    4. On submit, validate all fields and only proceed if all valid
    
    TRANSPILATION NOTE
    ------------------
    All of this code transpiles to equivalent JavaScript.
    - document.getElementById → document.getElementById
    - classList.add → classList.add
    - addEventListener → addEventListener
    """
    form = document.getElementById(form_id)
    
    # Track validation state for each field
    # Format: { field_name: True/False }
    validation_state = {}
    
    # Debounce timers for each field
    # We wait 300ms after typing stops before validating
    debounce_timers = {}
    
    # =========================================================================
    # VALIDATION RULES
    # =========================================================================
    # Define validation rules for each field type.
    # Each rule returns (is_valid, error_message).
    
    def validate_email(value):
        """
        Validate email address.
        
        WHY NOT JUST USE type="email"?
        ------------------------------
        The browser's built-in email validation is very lenient.
        It accepts "foo@bar" which isn't a valid email.
        We add additional checks for a better user experience.
        """
        if not value:
            return (False, "Email is required")
        
        # Check for @ and . (basic validation)
        if "@" not in value:
            return (False, "Please include an @ symbol")
        
        parts = value.split("@")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return (False, "Invalid email format")
        
        if "." not in parts[1]:
            return (False, "Please include a domain (e.g., .com)")
        
        return (True, "")
    
    def validate_password(value):
        """
        Validate password strength.
        
        Returns both validity and a strength indicator.
        """
        if not value:
            return (False, "Password is required")
        
        if len(value) < 8:
            return (False, f"Password must be at least 8 characters ({len(value)}/8)")
        
        # Check for mixed case
        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        has_number = any(c.isdigit() for c in value)
        
        if not (has_upper and has_lower):
            return (False, "Include both uppercase and lowercase letters")
        
        if not has_number:
            return (False, "Include at least one number")
        
        return (True, "")
    
    def validate_confirm_password(value):
        """Check that password confirmation matches."""
        password_input = document.getElementById("password")
        password = password_input.value
        
        if not value:
            return (False, "Please confirm your password")
        
        if value != password:
            return (False, "Passwords do not match")
        
        return (True, "")
    
    def validate_username(value):
        """
        Validate username.
        
        This could also include an async check for availability,
        but we keep it simple here.
        """
        if not value:
            return (False, "Username is required")
        
        if len(value) < 3:
            return (False, "Username must be at least 3 characters")
        
        if len(value) > 20:
            return (False, "Username must be 20 characters or less")
        
        # Only allow letters, numbers, underscores
        for char in value:
            if not (char.isalnum() or char == "_"):
                return (False, "Only letters, numbers, and underscores allowed")
        
        return (True, "")
    
    # Map field names to validation functions
    validators = {
        "email": validate_email,
        "password": validate_password,
        "confirm-password": validate_confirm_password,
        "username": validate_username
    }
    
    # =========================================================================
    # UI FEEDBACK FUNCTIONS
    # =========================================================================
    
    def show_error(field_name, message):
        """
        Show an error message for a field.
        
        ACCESSIBILITY
        -------------
        We use aria-describedby to connect the input to its error.
        Screen readers will announce the error when the field is focused.
        
        We also use role="alert" so the error is announced immediately
        when it appears.
        """
        input_el = document.getElementById(field_name)
        error_el = document.getElementById(f"{field_name}-error")
        
        # Update input styling
        input_el.classList.remove("valid")
        input_el.classList.add("invalid")
        input_el.setAttribute("aria-invalid", "true")
        
        # Show error message
        error_el.textContent = message
        error_el.style.display = "block"
        error_el.setAttribute("role", "alert")
        
        # Update validation state
        validation_state[field_name] = False
    
    def show_success(field_name):
        """
        Show success state for a field.
        
        We show a green checkmark to give positive feedback.
        Users like knowing they did something right!
        """
        input_el = document.getElementById(field_name)
        error_el = document.getElementById(f"{field_name}-error")
        success_el = document.getElementById(f"{field_name}-success")
        
        # Update input styling
        input_el.classList.remove("invalid")
        input_el.classList.add("valid")
        input_el.removeAttribute("aria-invalid")
        
        # Hide error, show success
        error_el.style.display = "none"
        if success_el:
            success_el.style.display = "block"
        
        # Update validation state
        validation_state[field_name] = True
    
    def clear_feedback(field_name):
        """Clear all feedback (when field is empty)."""
        input_el = document.getElementById(field_name)
        error_el = document.getElementById(f"{field_name}-error")
        success_el = document.getElementById(f"{field_name}-success")
        
        input_el.classList.remove("valid", "invalid")
        input_el.removeAttribute("aria-invalid")
        error_el.style.display = "none"
        if success_el:
            success_el.style.display = "none"
        
        validation_state[field_name] = False
    
    # =========================================================================
    # PASSWORD STRENGTH METER
    # =========================================================================
    
    def update_password_strength(value):
        """
        Update the visual password strength meter.
        
        Shows a bar that fills up based on password strength:
        - Red (25%): Too short
        - Orange (50%): Weak
        - Yellow (75%): Medium
        - Green (100%): Strong
        """
        strength_bar = document.getElementById("password-strength-bar")
        strength_text = document.getElementById("password-strength-text")
        
        if not value:
            strength_bar.style.width = "0%"
            strength_text.textContent = ""
            return
        
        # Calculate strength score
        score = 0
        
        if len(value) >= 8:
            score += 25
        if len(value) >= 12:
            score += 25
        if any(c.isupper() for c in value) and any(c.islower() for c in value):
            score += 25
        if any(c.isdigit() for c in value):
            score += 15
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value):
            score += 10
        
        # Update UI
        strength_bar.style.width = f"{min(score, 100)}%"
        
        if score < 25:
            strength_bar.style.backgroundColor = "#ef4444"  # red
            strength_text.textContent = "Too weak"
        elif score < 50:
            strength_bar.style.backgroundColor = "#f97316"  # orange
            strength_text.textContent = "Weak"
        elif score < 75:
            strength_bar.style.backgroundColor = "#eab308"  # yellow
            strength_text.textContent = "Medium"
        else:
            strength_bar.style.backgroundColor = "#22c55e"  # green
            strength_text.textContent = "Strong"
    
    # =========================================================================
    # INPUT EVENT HANDLER
    # =========================================================================
    
    def create_input_handler(field_name):
        """
        Create an input handler for a specific field.
        
        WHY DEBOUNCE?
        -------------
        We don't want to validate on every single keystroke.
        That would be annoying ("Your password is too short" after typing 'p').
        
        Instead, we wait 300ms after the user stops typing.
        This gives them time to finish before we show feedback.
        
        CLOSURES
        --------
        This function returns another function. The inner function
        "closes over" field_name, remembering it for later.
        This is how we create unique handlers for each field.
        """
        def on_input(event):
            value = event.target.value
            
            # Special handling for password strength
            if field_name == "password":
                update_password_strength(value)
            
            # Clear any pending debounce timer
            if field_name in debounce_timers:
                clearTimeout(debounce_timers[field_name])
            
            # If empty, clear feedback immediately
            if not value.strip():
                clear_feedback(field_name)
                return
            
            # Debounce: wait 300ms before validating
            debounce_timers[field_name] = setTimeout(
                lambda: validate_field(field_name),
                300
            )
        
        return on_input
    
    def validate_field(field_name):
        """Validate a single field and update UI."""
        input_el = document.getElementById(field_name)
        value = input_el.value
        
        # Get the validator for this field
        validator = validators.get(field_name)
        if not validator:
            return True
        
        # Run validation
        is_valid, error_message = validator(value)
        
        if is_valid:
            show_success(field_name)
        else:
            show_error(field_name, error_message)
        
        return is_valid
    
    # =========================================================================
    # FORM SUBMIT HANDLER
    # =========================================================================
    
    def on_form_submit(event):
        """
        Handle form submission.
        
        WHAT WE DO
        ----------
        1. Prevent the default form submission (page reload)
        2. Validate all fields
        3. If all valid, call the on_submit callback
        4. If any invalid, focus the first invalid field
        """
        event.preventDefault()
        
        # Validate all fields
        all_valid = True
        first_invalid = None
        
        for field_name in validators.keys():
            is_valid = validate_field(field_name)
            if not is_valid and all_valid:
                first_invalid = field_name
                all_valid = False
        
        if all_valid:
            # Collect form data
            form_data = {}
            for field_name in validators.keys():
                input_el = document.getElementById(field_name)
                form_data[field_name] = input_el.value
            
            # Call success callback
            on_submit(form_data)
        else:
            # Focus the first invalid field
            if first_invalid:
                document.getElementById(first_invalid).focus()
    
    # =========================================================================
    # ATTACH EVENT LISTENERS
    # =========================================================================
    
    # Attach input handlers to each field
    for field_name in validators.keys():
        input_el = document.getElementById(field_name)
        if input_el:
            input_el.addEventListener("input", create_input_handler(field_name))
            
            # Also validate on blur (when leaving field)
            input_el.addEventListener("blur", lambda e: validate_field(field_name))
    
    # Attach submit handler
    form.addEventListener("submit", on_form_submit)
    
    return {
        "validate_all": lambda: all(validate_field(f) for f in validators.keys()),
        "get_state": lambda: validation_state
    }


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

def init_registration_form():
    """Initialize the registration form."""
    
    def on_submit(data):
        console.log("Form submitted!", data)
        
        # Send to server
        fetch("/api/register", {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": JSON.stringify(data)
        }).then(handle_response)
    
    form = create_validated_form("registration-form", on_submit)
    return form
```

### HTML Structure for This Example

```html
<form id="registration-form">
  <div class="field">
    <label for="username">Username</label>
    <input type="text" id="username" name="username" 
           aria-describedby="username-error">
    <span id="username-error" class="error" style="display: none;"></span>
    <span id="username-success" class="success" style="display: none;">✓</span>
  </div>
  
  <div class="field">
    <label for="email">Email</label>
    <input type="email" id="email" name="email"
           aria-describedby="email-error">
    <span id="email-error" class="error" style="display: none;"></span>
    <span id="email-success" class="success" style="display: none;">✓</span>
  </div>
  
  <div class="field">
    <label for="password">Password</label>
    <input type="password" id="password" name="password"
           aria-describedby="password-error">
    <div class="strength-meter">
      <div id="password-strength-bar"></div>
    </div>
    <span id="password-strength-text"></span>
    <span id="password-error" class="error" style="display: none;"></span>
  </div>
  
  <div class="field">
    <label for="confirm-password">Confirm Password</label>
    <input type="password" id="confirm-password" name="confirm-password"
           aria-describedby="confirm-password-error">
    <span id="confirm-password-error" class="error" style="display: none;"></span>
  </div>
  
  <button type="submit">Create Account</button>
</form>
```

### Key Points

- **Debounce input events** to avoid validating on every keystroke
- **Use aria-invalid and aria-describedby** for accessibility
- **Validate on blur** (focus leaving field) for better UX
- **Focus first invalid field** on submit attempt
- **Show positive feedback** (checkmarks) for valid fields

---

## 13. Autocomplete / Typeahead Search

A complete autocomplete implementation with keyboard navigation, debouncing,
and accessibility support.

```python
from pynext.client import document, window

# =============================================================================
# AUTOCOMPLETE / TYPEAHEAD SEARCH
# =============================================================================
#
# This provides a searchable dropdown as the user types:
# - Debounced API calls (don't hit server on every keystroke)
# - Keyboard navigation (↑/↓ arrows, Enter to select, Escape to close)
# - Click outside to close
# - Accessible with ARIA attributes
#
# =============================================================================


def create_autocomplete(input_id: str, search_endpoint: str, on_select):
    """
    Create an autocomplete/typeahead input.
    
    Args:
        input_id: ID of the input element
        search_endpoint: API endpoint for search (e.g., "/api/search")
        on_select: Callback when item is selected, receives the item
    
    HOW IT WORKS
    ------------
    1. User types in the input
    2. After 300ms of no typing, we fetch suggestions from the API
    3. Display suggestions in a dropdown
    4. User can navigate with keyboard or click
    5. Selection triggers on_select callback
    
    ACCESSIBILITY (ARIA)
    --------------------
    We use ARIA to make this accessible to screen readers:
    - role="combobox" on the input
    - role="listbox" on the dropdown
    - role="option" on each item
    - aria-activedescendant to indicate current selection
    """
    input_el = document.getElementById(input_id)
    dropdown = document.getElementById(f"{input_id}-dropdown")
    
    # State
    results = []           # Current search results
    selected_index = -1    # Currently highlighted item (-1 = none)
    is_open = False        # Is dropdown visible?
    timeout_id = None      # Debounce timer
    
    # =========================================================================
    # SEARCH FUNCTION
    # =========================================================================
    
    def search(query):
        """
        Fetch search results from the API.
        
        WHY ENCODE THE QUERY?
        ---------------------
        encodeURIComponent handles special characters in the search term.
        Without it, a search for "C++" would break the URL.
        """
        url = f"{search_endpoint}?q={encodeURIComponent(query)}"
        
        fetch(url) \
            .then(lambda response: response.json()) \
            .then(show_results) \
            .catch(lambda error: console.error("Search failed:", error))
    
    # =========================================================================
    # DISPLAY RESULTS
    # =========================================================================
    
    def show_results(data):
        """
        Display search results in the dropdown.
        
        We rebuild the dropdown HTML each time because:
        1. It's simpler than diffing/updating
        2. The list is usually small (<50 items)
        3. Modern browsers handle this quickly
        """
        nonlocal results, selected_index, is_open
        
        results = data
        selected_index = -1
        
        # Clear existing items
        dropdown.innerHTML = ""
        
        if len(results) == 0:
            # Show "no results" message
            no_results = document.createElement("div")
            no_results.className = "autocomplete-no-results"
            no_results.textContent = "No results found"
            dropdown.appendChild(no_results)
        else:
            # Create option for each result
            for i, item in enumerate(results):
                option = document.createElement("div")
                option.className = "autocomplete-option"
                option.id = f"{input_id}-option-{i}"
                option.setAttribute("role", "option")
                option.setAttribute("data-index", str(i))
                
                # Display text (adjust based on your data structure)
                option.textContent = item.get("label", item.get("name", str(item)))
                
                # Click handler
                option.addEventListener("click", lambda e, idx=i: select_item(idx))
                
                # Hover handler (for visual highlighting)
                option.addEventListener("mouseenter", lambda e, idx=i: highlight_item(idx))
                
                dropdown.appendChild(option)
        
        # Show dropdown
        dropdown.style.display = "block"
        is_open = True
        
        # Update ARIA
        input_el.setAttribute("aria-expanded", "true")
    
    # =========================================================================
    # KEYBOARD NAVIGATION
    # =========================================================================
    
    def on_keydown(event):
        """
        Handle keyboard navigation.
        
        KEYBOARD CONTROLS
        -----------------
        - ↓ (ArrowDown): Move to next option
        - ↑ (ArrowUp): Move to previous option
        - Enter: Select current option
        - Escape: Close dropdown
        
        WHY preventDefault()?
        ---------------------
        Without it, ArrowDown would move the cursor in the input.
        We want the arrows to navigate the dropdown instead.
        """
        nonlocal selected_index
        
        if not is_open:
            return
        
        if event.key == "ArrowDown":
            event.preventDefault()  # Don't move cursor
            selected_index = min(selected_index + 1, len(results) - 1)
            highlight_item(selected_index)
        
        elif event.key == "ArrowUp":
            event.preventDefault()
            selected_index = max(selected_index - 1, 0)
            highlight_item(selected_index)
        
        elif event.key == "Enter":
            event.preventDefault()  # Don't submit form
            if selected_index >= 0:
                select_item(selected_index)
        
        elif event.key == "Escape":
            close_dropdown()
            input_el.blur()  # Remove focus
    
    def highlight_item(index):
        """
        Highlight an item in the dropdown.
        
        ARIA-ACTIVEDESCENDANT
        ---------------------
        This tells screen readers which item is currently selected.
        When the user presses ↓, the screen reader announces the new item.
        """
        nonlocal selected_index
        selected_index = index
        
        # Remove highlight from all items
        options = dropdown.querySelectorAll(".autocomplete-option")
        for opt in options:
            opt.classList.remove("highlighted")
        
        # Add highlight to current item
        if index >= 0 and index < len(results):
            current = document.getElementById(f"{input_id}-option-{index}")
            if current:
                current.classList.add("highlighted")
                
                # Update ARIA
                input_el.setAttribute("aria-activedescendant", current.id)
                
                # Scroll into view if needed
                current.scrollIntoView({"block": "nearest"})
    
    def select_item(index):
        """
        Select an item and close the dropdown.
        """
        if index >= 0 and index < len(results):
            item = results[index]
            
            # Update input with selected value
            input_el.value = item.get("label", item.get("name", str(item)))
            
            # Close dropdown
            close_dropdown()
            
            # Notify callback
            on_select(item)
    
    # =========================================================================
    # INPUT HANDLER (DEBOUNCED)
    # =========================================================================
    
    def on_input(event):
        """
        Handle input changes with debouncing.
        
        DEBOUNCE EXPLAINED
        ------------------
        If the user types "hello" quickly, we don't want to search for:
        "h", "he", "hel", "hell", "hello"
        
        That's 5 API calls for one word! Instead, we wait 300ms after
        the user stops typing before searching. This reduces server load
        and provides a smoother experience.
        """
        nonlocal timeout_id
        
        query = event.target.value.strip()
        
        # Cancel any pending search
        if timeout_id:
            clearTimeout(timeout_id)
        
        # Don't search for very short queries
        if len(query) < 2:
            close_dropdown()
            return
        
        # Debounce: wait 300ms after typing stops
        timeout_id = setTimeout(lambda: search(query), 300)
    
    # =========================================================================
    # CLOSE DROPDOWN
    # =========================================================================
    
    def close_dropdown():
        """Close the dropdown and clean up."""
        nonlocal is_open, selected_index, results
        
        dropdown.style.display = "none"
        is_open = False
        selected_index = -1
        results = []
        
        # Update ARIA
        input_el.setAttribute("aria-expanded", "false")
        input_el.removeAttribute("aria-activedescendant")
    
    def on_click_outside(event):
        """Close dropdown when clicking outside."""
        # Check if click was outside input and dropdown
        if event.target != input_el and not dropdown.contains(event.target):
            close_dropdown()
    
    def on_focus(event):
        """Re-open dropdown if we have results and input has value."""
        if input_el.value.strip() and len(results) > 0:
            dropdown.style.display = "block"
    
    # =========================================================================
    # SETUP ARIA ATTRIBUTES
    # =========================================================================
    
    # Set up ARIA for accessibility
    input_el.setAttribute("role", "combobox")
    input_el.setAttribute("aria-autocomplete", "list")
    input_el.setAttribute("aria-expanded", "false")
    input_el.setAttribute("aria-controls", f"{input_id}-dropdown")
    
    dropdown.setAttribute("role", "listbox")
    dropdown.setAttribute("aria-label", "Search suggestions")
    
    # =========================================================================
    # ATTACH EVENT LISTENERS
    # =========================================================================
    
    input_el.addEventListener("input", on_input)
    input_el.addEventListener("keydown", on_keydown)
    input_el.addEventListener("focus", on_focus)
    document.addEventListener("click", on_click_outside)
    
    # Return cleanup function
    def cleanup():
        document.removeEventListener("click", on_click_outside)
    
    return {"close": close_dropdown, "cleanup": cleanup}


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

def init_user_search():
    """Initialize user search autocomplete."""
    
    def on_select(user):
        console.log("Selected user:", user)
        navigate_to_profile(user["id"])
    
    autocomplete = create_autocomplete(
        input_id="user-search",
        search_endpoint="/api/users/search",
        on_select=on_select
    )
    
    return autocomplete
```

### Key Points

- **Debounce API calls** - Wait 300ms after typing stops
- **Keyboard navigation** - ↑/↓/Enter/Escape support
- **ARIA attributes** - role="combobox", aria-activedescendant, etc.
- **Click outside to close** - Document click listener
- **Cancel pending requests** - clearTimeout on new input

---

## 14. Accessible Modal with Focus Trap

A fully accessible modal dialog that traps keyboard focus inside it.
This is essential for users who navigate with keyboards or screen readers.

```python
from pynext.client import document, window

# =============================================================================
# ACCESSIBLE MODAL WITH FOCUS TRAP
# =============================================================================
#
# A proper modal must:
# 1. Trap focus inside (Tab should cycle within the modal)
# 2. Close on Escape key
# 3. Return focus to the trigger element when closed
# 4. Prevent background scrolling
# 5. Announce itself to screen readers
#
# =============================================================================


def create_modal(modal_id: str):
    """
    Create an accessible modal dialog.
    
    Args:
        modal_id: ID of the modal container element
    
    Returns:
        Object with open() and close() methods
    
    ACCESSIBILITY REQUIREMENTS (WCAG)
    ---------------------------------
    1. Focus must be trapped inside the modal
    2. Escape key must close the modal
    3. Focus returns to trigger when closed
    4. Screen readers must announce the modal
    5. Background content must be inert
    """
    modal = document.getElementById(modal_id)
    trigger_element = None  # Element that opened the modal
    
    # =========================================================================
    # FIND FOCUSABLE ELEMENTS
    # =========================================================================
    
    def get_focusable_elements():
        """
        Get all focusable elements inside the modal.
        
        FOCUSABLE ELEMENTS
        ------------------
        - Buttons
        - Links with href
        - Form inputs
        - Textareas
        - Select dropdowns
        - Elements with tabindex (not -1)
        
        We use a CSS selector that matches all of these.
        """
        selector = ', '.join([
            'button:not([disabled])',
            '[href]',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
        ])
        
        return modal.querySelectorAll(selector)
    
    # =========================================================================
    # FOCUS TRAP
    # =========================================================================
    
    def trap_focus(event):
        """
        Trap focus inside the modal.
        
        HOW IT WORKS
        ------------
        When the user presses Tab:
        1. If on the last focusable element, wrap to first
        2. If on the first element and Shift+Tab, wrap to last
        
        This creates a "focus loop" - Tab never leaves the modal.
        
        WHY IS THIS IMPORTANT?
        ----------------------
        Without focus trapping, keyboard users can Tab out of the modal
        into the (hidden) background content. This is confusing and
        breaks the user's mental model of a "modal" (blocking) dialog.
        """
        if event.key != "Tab":
            return
        
        focusable = get_focusable_elements()
        
        # If no focusable elements, do nothing
        if focusable.length == 0:
            event.preventDefault()
            return
        
        first_element = focusable[0]
        last_element = focusable[focusable.length - 1]
        
        if event.shiftKey:
            # Shift+Tab: going backwards
            if document.activeElement == first_element:
                event.preventDefault()
                last_element.focus()
        else:
            # Tab: going forwards
            if document.activeElement == last_element:
                event.preventDefault()
                first_element.focus()
    
    # =========================================================================
    # ESCAPE KEY HANDLER
    # =========================================================================
    
    def on_escape(event):
        """Close modal on Escape key."""
        if event.key == "Escape":
            close_modal()
    
    # =========================================================================
    # BACKDROP CLICK HANDLER
    # =========================================================================
    
    def on_backdrop_click(event):
        """
        Close modal when clicking the backdrop (overlay).
        
        WHY event.target == modal?
        --------------------------
        The modal element is the backdrop. The actual content is a
        child element. If the user clicks on the content, event.target
        will be the content (or a child), not the modal.
        
        If event.target IS the modal, they clicked the dark overlay.
        """
        if event.target == modal:
            close_modal()
    
    # =========================================================================
    # OPEN MODAL
    # =========================================================================
    
    def open_modal(trigger=None):
        """
        Open the modal dialog.
        
        Args:
            trigger: The element that triggered the open (for focus return)
        
        WHAT WE DO
        ----------
        1. Store the trigger element (to return focus later)
        2. Show the modal
        3. Prevent background scrolling
        4. Announce to screen readers
        5. Move focus to first focusable element
        6. Add keyboard event listeners
        """
        nonlocal trigger_element
        trigger_element = trigger
        
        # Show modal
        modal.style.display = "flex"  # or "block", depending on your CSS
        modal.setAttribute("aria-hidden", "false")
        
        # Prevent background scrolling
        # This stops the page from scrolling while modal is open
        document.body.style.overflow = "hidden"
        
        # Add inert to background content (if supported)
        # This prevents screen readers from reading background content
        main_content = document.getElementById("main-content")
        if main_content:
            main_content.setAttribute("aria-hidden", "true")
        
        # Focus the first focusable element
        # (or the close button, or the modal itself)
        focusable = get_focusable_elements()
        if focusable.length > 0:
            focusable[0].focus()
        else:
            # If no focusable elements, focus the modal itself
            modal.focus()
        
        # Add event listeners
        modal.addEventListener("keydown", trap_focus)
        document.addEventListener("keydown", on_escape)
        modal.addEventListener("click", on_backdrop_click)
    
    # =========================================================================
    # CLOSE MODAL
    # =========================================================================
    
    def close_modal():
        """
        Close the modal dialog.
        
        WHAT WE DO
        ----------
        1. Hide the modal
        2. Restore background scrolling
        3. Remove inert from background
        4. Return focus to the trigger element
        5. Remove event listeners
        """
        # Hide modal
        modal.style.display = "none"
        modal.setAttribute("aria-hidden", "true")
        
        # Restore background scrolling
        document.body.style.overflow = ""
        
        # Remove inert from background
        main_content = document.getElementById("main-content")
        if main_content:
            main_content.removeAttribute("aria-hidden")
        
        # Return focus to trigger element
        # This is crucial for keyboard users!
        if trigger_element:
            trigger_element.focus()
        
        # Remove event listeners
        modal.removeEventListener("keydown", trap_focus)
        document.removeEventListener("keydown", on_escape)
        modal.removeEventListener("click", on_backdrop_click)
    
    # =========================================================================
    # INITIAL SETUP
    # =========================================================================
    
    # Set up ARIA attributes
    modal.setAttribute("role", "dialog")
    modal.setAttribute("aria-modal", "true")
    modal.setAttribute("aria-hidden", "true")
    modal.setAttribute("tabindex", "-1")  # Make modal focusable
    
    # Return public API
    return {
        "open": open_modal,
        "close": close_modal
    }


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

def init_confirm_dialog():
    """Initialize a confirmation dialog modal."""
    
    modal = create_modal("confirm-modal")
    
    # Open button
    def on_open_click(event):
        modal["open"](event.target)
    
    document.getElementById("open-modal-btn").addEventListener("click", on_open_click)
    
    # Close button inside modal
    document.getElementById("modal-close-btn").addEventListener("click", 
        lambda e: modal["close"]())
    
    # Confirm button inside modal
    def on_confirm(event):
        do_confirmed_action()
        modal["close"]()
    
    document.getElementById("modal-confirm-btn").addEventListener("click", on_confirm)
    
    return modal
```

### Key Points

- **Focus trap** - Tab cycles within modal, never escapes
- **Escape to close** - Universal convention
- **Return focus** - Focus goes back to trigger element
- **Prevent background scroll** - body overflow:hidden
- **ARIA attributes** - role="dialog", aria-modal="true"
- **Hide background** - aria-hidden="true" on main content

---

## 15. Copy to Clipboard Button

A simple but polished "copy to clipboard" feature with visual feedback.

```python
from pynext.client import document, navigator

# =============================================================================
# COPY TO CLIPBOARD
# =============================================================================
#
# This pattern:
# 1. Uses the modern Clipboard API (async, secure)
# 2. Falls back to execCommand for older browsers
# 3. Shows visual feedback ("Copied!")
#
# =============================================================================


def create_copy_button(button_id: str, get_text):
    """
    Create a copy button with visual feedback.
    
    Args:
        button_id: ID of the button element
        get_text: Function that returns the text to copy
                  (or a static string)
    
    WHY USE A FUNCTION FOR get_text?
    ---------------------------------
    Sometimes the text to copy is dynamic (e.g., an input value).
    By passing a function, we get the current value at click time.
    
    Example: lambda: document.getElementById("code").textContent
    """
    button = document.getElementById(button_id)
    original_text = button.textContent
    original_class = button.className
    
    async def on_click(event):
        """
        Handle copy button click.
        
        CLIPBOARD API
        -------------
        The modern way to copy text is:
        
            await navigator.clipboard.writeText("text")
        
        This is async and may be rejected if the user denies permission.
        It only works in secure contexts (HTTPS) and requires user gesture.
        
        FALLBACK
        --------
        For older browsers, we use the execCommand approach:
        1. Create a hidden textarea
        2. Put the text in it
        3. Select all
        4. Execute "copy" command
        5. Remove the textarea
        """
        # Get the text to copy
        text = get_text() if callable(get_text) else get_text
        
        try:
            # Try modern Clipboard API
            await navigator.clipboard.writeText(text)
            show_success()
        except:
            # Fall back to execCommand
            fallback_copy(text)
    
    def fallback_copy(text):
        """
        Fallback copy using execCommand.
        
        WHY THE WEIRD APPROACH?
        -----------------------
        execCommand("copy") only works on selected text.
        We can't select arbitrary text, only text in form fields.
        So we create a hidden textarea, put the text there,
        select it, copy it, then remove the textarea.
        
        This is a hack, but it works everywhere.
        """
        # Create hidden textarea
        textarea = document.createElement("textarea")
        textarea.value = text
        
        # Make it invisible but still present
        textarea.style.position = "fixed"
        textarea.style.left = "-9999px"
        textarea.style.top = "0"
        textarea.style.opacity = "0"
        
        # Add to DOM (required for selection to work)
        document.body.appendChild(textarea)
        
        # Select and copy
        textarea.select()
        textarea.setSelectionRange(0, 99999)  # For mobile
        document.execCommand("copy")
        
        # Clean up
        document.body.removeChild(textarea)
        
        show_success()
    
    def show_success():
        """
        Show visual feedback that copy succeeded.
        
        UX BEST PRACTICE
        ----------------
        Always give feedback when an action succeeds.
        The user clicked a button - they want to know it worked!
        
        We briefly change the button text and style, then reset.
        """
        # Update button appearance
        button.textContent = "Copied!"
        button.classList.add("copied")
        button.classList.remove("copy-btn")
        
        # Disable button temporarily (prevent rapid clicking)
        button.disabled = True
        
        # Reset after 2 seconds
        setTimeout(reset_button, 2000)
    
    def reset_button():
        """Reset button to original state."""
        button.textContent = original_text
        button.className = original_class
        button.disabled = False
    
    # Attach click handler
    button.addEventListener("click", on_click)
    
    return {"copy": on_click, "reset": reset_button}


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def setup_code_block_copy():
    """
    Add copy buttons to all code blocks.
    
    This is common on documentation sites.
    """
    code_blocks = document.querySelectorAll("pre code")
    
    for block in code_blocks:
        # Create copy button
        btn = document.createElement("button")
        btn.className = "copy-btn"
        btn.textContent = "Copy"
        btn.id = f"copy-{Math.random().toString(36)[2:9]}"
        
        # Position button in corner of code block
        parent = block.parentElement
        parent.style.position = "relative"
        btn.style.position = "absolute"
        btn.style.top = "8px"
        btn.style.right = "8px"
        
        parent.appendChild(btn)
        
        # Create copy handler for this block
        create_copy_button(btn.id, lambda b=block: b.textContent)


def setup_share_link_copy():
    """Copy the current page URL."""
    
    def get_share_url():
        return window.location.href
    
    create_copy_button("share-btn", get_share_url)
```

### Key Points

- **Clipboard API first** - Modern, clean, async
- **Fallback for old browsers** - execCommand with hidden textarea
- **Visual feedback** - Button changes to "Copied!"
- **Debounce clicks** - Disable button temporarily
- **Works with dynamic content** - Pass a function to get text

---

## 16. Lazy Load Images with IntersectionObserver

Load images only when they're about to enter the viewport.
This dramatically improves page load time for image-heavy pages.

```python
from pynext.client import document, IntersectionObserver

# =============================================================================
# LAZY LOADING IMAGES
# =============================================================================
#
# Images are often the largest resources on a page. Loading them all
# at once slows down initial page load. Lazy loading defers image
# loading until the image is about to become visible.
#
# We use IntersectionObserver - a modern, efficient API for detecting
# when elements enter the viewport.
#
# =============================================================================


def setup_lazy_images():
    """
    Set up lazy loading for all images with data-src attribute.
    
    HTML STRUCTURE
    --------------
    Use data-src instead of src for the actual image URL:
    
        <img data-src="large-photo.jpg" 
             src="tiny-placeholder.jpg" 
             alt="Description">
    
    The placeholder can be:
    - A tiny blurred version (LQIP - Low Quality Image Placeholder)
    - A solid color
    - A loading spinner
    - A transparent pixel
    
    INTERSECTION OBSERVER
    ---------------------
    This API tells us when elements enter the viewport.
    It's much more efficient than scroll event listeners.
    
    The browser optimizes it internally - we don't need to
    debounce or do any manual optimization.
    """
    
    def on_intersect(entries, observer):
        """
        Called when observed elements enter or leave viewport.
        
        entries: List of IntersectionObserverEntry objects
        observer: The IntersectionObserver instance
        
        WHAT IS AN ENTRY?
        -----------------
        Each entry contains:
        - target: The DOM element
        - isIntersecting: True if element is in viewport
        - intersectionRatio: How much of element is visible (0-1)
        - boundingClientRect: Element's position
        """
        for entry in entries:
            # Only care about elements entering viewport
            if entry.isIntersecting:
                img = entry.target
                
                # Get the real image URL
                src = img.getAttribute("data-src")
                
                if src:
                    # Start loading the real image
                    img.src = src
                    
                    # Remove data-src so we don't process again
                    img.removeAttribute("data-src")
                    
                    # Optional: Add class for CSS transitions
                    img.classList.add("loaded")
                    
                    # Stop observing this image (it's loaded)
                    observer.unobserve(img)
    
    # =========================================================================
    # CREATE OBSERVER
    # =========================================================================
    
    observer = IntersectionObserver(on_intersect, {
        # root: null means viewport (default)
        "root": None,
        
        # rootMargin: Start loading images 100px before they enter viewport
        # This gives images a head start, reducing visible loading
        "rootMargin": "100px",
        
        # threshold: How much of element must be visible to trigger
        # 0.1 = 10% visible triggers the callback
        "threshold": 0.1
    })
    
    # =========================================================================
    # OBSERVE ALL LAZY IMAGES
    # =========================================================================
    
    lazy_images = document.querySelectorAll("img[data-src]")
    
    for img in lazy_images:
        observer.observe(img)
    
    console.log(f"Lazy loading {lazy_images.length} images")
    
    # Return observer for cleanup
    return observer


# =============================================================================
# PROGRESSIVE IMAGE LOADING (LQIP)
# =============================================================================
#
# For an even better experience, use Low Quality Image Placeholders.
# Show a tiny, blurred image while the full image loads.
#
# =============================================================================


def setup_progressive_images():
    """
    Set up progressive image loading with blur-up effect.
    
    HTML STRUCTURE
    --------------
        <div class="progressive-image">
          <img class="placeholder" 
               src="photo-20px.jpg" 
               alt="Description">
          <img class="full" 
               data-src="photo-1920px.jpg"
               alt="Description">
        </div>
    
    CSS
    ---
        .progressive-image .placeholder {
          filter: blur(20px);
          transform: scale(1.1);
          transition: opacity 0.3s;
        }
        
        .progressive-image .full {
          position: absolute;
          top: 0;
          left: 0;
          opacity: 0;
          transition: opacity 0.3s;
        }
        
        .progressive-image .full.loaded {
          opacity: 1;
        }
    """
    
    def on_intersect(entries, observer):
        for entry in entries:
            if entry.isIntersecting:
                container = entry.target
                full_img = container.querySelector(".full")
                placeholder = container.querySelector(".placeholder")
                
                src = full_img.getAttribute("data-src")
                if src:
                    # When full image loads, show it
                    def on_load(event):
                        full_img.classList.add("loaded")
                        # Optional: hide placeholder after transition
                        setTimeout(lambda: placeholder.remove(), 300)
                    
                    full_img.addEventListener("load", on_load)
                    full_img.src = src
                    full_img.removeAttribute("data-src")
                    
                    observer.unobserve(container)
    
    observer = IntersectionObserver(on_intersect, {
        "rootMargin": "100px",
        "threshold": 0.1
    })
    
    containers = document.querySelectorAll(".progressive-image")
    for container in containers:
        observer.observe(container)
    
    return observer
```

### Key Points

- **IntersectionObserver** - Modern, efficient viewport detection
- **rootMargin** - Load images before they're visible
- **Unobserve after load** - Stop watching loaded images
- **data-src pattern** - Defer loading until observed
- **Progressive loading** - Blur-up effect for better UX

---

## 17. Context Menu (Right-Click)

A custom right-click context menu with keyboard support.

```python
from pynext.client import document, window

# =============================================================================
# CUSTOM CONTEXT MENU
# =============================================================================
#
# Replace the browser's default right-click menu with a custom one.
# Useful for:
# - File managers (copy, paste, rename)
# - Rich text editors (formatting options)
# - Image galleries (save, share, edit)
# - Any app with contextual actions
#
# =============================================================================


def create_context_menu(menu_id: str, actions: dict):
    """
    Create a custom right-click context menu.
    
    Args:
        menu_id: ID of the menu element
        actions: Dict of action names to handler functions
    
    Example:
        create_context_menu("file-menu", {
            "copy": lambda el: copy_file(el),
            "delete": lambda el: delete_file(el),
            "rename": lambda el: rename_file(el)
        })
    
    CONTEXTMENU EVENT
    -----------------
    The 'contextmenu' event fires when the user:
    - Right-clicks
    - Long-presses on mobile
    - Presses the Menu key on keyboard
    
    We call preventDefault() to stop the browser's default menu.
    """
    menu = document.getElementById(menu_id)
    current_target = None  # Element that was right-clicked
    
    # =========================================================================
    # SHOW MENU
    # =========================================================================
    
    def on_contextmenu(event):
        """
        Handle right-click to show context menu.
        
        We only show our menu for elements with data-context-menu attribute.
        This lets you selectively enable context menus.
        """
        nonlocal current_target
        
        # Find the closest element with data-context-menu
        # This lets you right-click on any child element
        target = event.target.closest("[data-context-menu]")
        
        if not target:
            # Not a context menu target, use browser default
            return
        
        # Prevent browser's default context menu
        event.preventDefault()
        
        current_target = target
        
        # Position menu at cursor
        menu.style.left = f"{event.clientX}px"
        menu.style.top = f"{event.clientY}px"
        
        # Show menu
        menu.style.display = "block"
        
        # Ensure menu stays in viewport
        keep_in_viewport()
        
        # Focus menu for keyboard navigation
        first_item = menu.querySelector("[data-action]")
        if first_item:
            first_item.focus()
    
    def keep_in_viewport():
        """
        Adjust menu position to stay in viewport.
        
        If the menu would go off-screen, flip it to the other side.
        """
        rect = menu.getBoundingClientRect()
        
        # Check right edge
        if rect.right > window.innerWidth:
            new_left = rect.left - rect.width
            menu.style.left = f"{max(0, new_left)}px"
        
        # Check bottom edge
        if rect.bottom > window.innerHeight:
            new_top = rect.top - rect.height
            menu.style.top = f"{max(0, new_top)}px"
    
    # =========================================================================
    # MENU ITEM CLICK
    # =========================================================================
    
    def on_menu_click(event):
        """
        Handle click on menu item.
        
        Each menu item has a data-action attribute that maps
        to a function in our actions dict.
        """
        action_name = event.target.getAttribute("data-action")
        
        if action_name and action_name in actions:
            # Call the action handler with the right-clicked element
            actions[action_name](current_target)
        
        hide_menu()
    
    # =========================================================================
    # KEYBOARD NAVIGATION
    # =========================================================================
    
    def on_menu_keydown(event):
        """
        Handle keyboard navigation in the menu.
        
        - ↑/↓: Navigate between items
        - Enter/Space: Activate item
        - Escape: Close menu
        """
        items = menu.querySelectorAll("[data-action]")
        current_index = -1
        
        # Find currently focused item
        for i, item in enumerate(items):
            if item == document.activeElement:
                current_index = i
                break
        
        if event.key == "ArrowDown":
            event.preventDefault()
            next_index = (current_index + 1) % items.length
            items[next_index].focus()
        
        elif event.key == "ArrowUp":
            event.preventDefault()
            prev_index = (current_index - 1) % items.length
            items[prev_index].focus()
        
        elif event.key == "Enter" or event.key == " ":
            event.preventDefault()
            if document.activeElement.hasAttribute("data-action"):
                document.activeElement.click()
        
        elif event.key == "Escape":
            hide_menu()
    
    # =========================================================================
    # HIDE MENU
    # =========================================================================
    
    def hide_menu():
        """Hide the context menu."""
        menu.style.display = "none"
        current_target = None
    
    def on_click_outside(event):
        """Hide menu when clicking anywhere else."""
        if event.target != menu and not menu.contains(event.target):
            hide_menu()
    
    def on_scroll(event):
        """Hide menu on scroll."""
        hide_menu()
    
    # =========================================================================
    # SETUP
    # =========================================================================
    
    # Set up accessibility
    menu.setAttribute("role", "menu")
    
    items = menu.querySelectorAll("[data-action]")
    for item in items:
        item.setAttribute("role", "menuitem")
        item.setAttribute("tabindex", "-1")  # Focusable but not in tab order
    
    # Attach event listeners
    document.addEventListener("contextmenu", on_contextmenu)
    menu.addEventListener("click", on_menu_click)
    menu.addEventListener("keydown", on_menu_keydown)
    document.addEventListener("click", on_click_outside)
    window.addEventListener("scroll", hide_menu, {"passive": True})
    document.addEventListener("keydown", lambda e: hide_menu() if e.key == "Escape" else None)
    
    # Return cleanup function
    def cleanup():
        document.removeEventListener("contextmenu", on_contextmenu)
        document.removeEventListener("click", on_click_outside)
        window.removeEventListener("scroll", hide_menu)
    
    return {"hide": hide_menu, "cleanup": cleanup}


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

def init_file_context_menu():
    """Initialize context menu for file items."""
    
    context_menu = create_context_menu("file-context-menu", {
        "open": lambda el: open_file(el.getAttribute("data-file-id")),
        "copy": lambda el: copy_file(el.getAttribute("data-file-id")),
        "rename": lambda el: start_rename(el),
        "delete": lambda el: confirm_delete(el),
        "share": lambda el: open_share_dialog(el)
    })
    
    return context_menu
```

### HTML Structure

```html
<!-- Menu items have data-context-menu to enable right-click -->
<div class="file-item" data-context-menu data-file-id="123">
  <span class="icon">📄</span>
  <span class="name">document.pdf</span>
</div>

<!-- The context menu (hidden by default) -->
<div id="file-context-menu" class="context-menu" style="display: none;">
  <button data-action="open">Open</button>
  <button data-action="copy">Copy</button>
  <button data-action="rename">Rename</button>
  <hr>
  <button data-action="delete" class="danger">Delete</button>
</div>
```

### Key Points

- **preventDefault()** on contextmenu event - Stops browser menu
- **Position at cursor** - event.clientX, event.clientY
- **Stay in viewport** - Check boundaries and flip if needed
- **Keyboard navigation** - ↑/↓/Enter/Escape
- **Click outside to close** - Document click listener
- **data-action pattern** - Clean action mapping

---

## See Also

- [Events API Reference](../features/EVENTS.md) - Complete API documentation
- [Transpilation Mechanism](../internals/TRANSPILATION_EVENTS.md) - How events transpile
- [DOM API](../features/DOM_API.md) - Element manipulation

