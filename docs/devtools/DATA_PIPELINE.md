# Data Pipeline - Event Flow from Browser to File

This document traces the complete journey of events from browser actions to output files that AI can read.

## Overview

The data pipeline follows this path:

```
Browser Action ──► Client JS ──► Console.log ──► CDP ──► Python ──► Files
```

Each step transforms and enriches the data until it's in a format optimized for AI consumption.

---

## Step 1: Browser Event Occurs

When a user interacts with the page, browser events fire.

### Click Example

```javascript
// User clicks a button
document.querySelector('#new-issue-btn').click()
```

The injected `pynext_debug` script captures this:

```javascript
// In TRACKING_SCRIPT (injector.py)
document.addEventListener('click', function(e) {
    const target = e.target;
    window.__pynext_debug__.reportClick(target, e.clientX, e.clientY);
}, true);  // Capture phase to get ALL clicks
```

### Signal Change Example

```javascript
// User action triggers signal update
view_mode.set("kanban");
```

The patched signal intercepts this:

```javascript
// In TRACKING_SCRIPT (injector.py)
signal.set = function(newValue) {
    const oldValue = signal._value;
    const result = signal._set_original(newValue);
    window.__pynext_debug__.reportSignal(
        signal._name || id,
        newValue,
        oldValue
    );
    return result;
};
```

---

## Step 2: Client Reports to Console

All events are reported via `console.log` with a `[PyNext]` prefix:

```javascript
// Click
console.log('[PyNext] CLICK: #new-issue-btn at (150,200)');

// Signal change
console.log('[PyNext] SIGNAL: view_mode = "kanban" (was: "list")');

// User note
console.log('[PyNext] NOTE: Form is not responding');

// Session start
console.log('[PyNext] SESSION_START: Testing create issue');

// Session end
console.log('[PyNext] SESSION_END: {"id":"rec_xxx","outcome":"Form broken"}');

// Element select (from inspect mode)
console.log('[PyNext] ELEMENT_SELECT: ' + JSON.stringify(elementInfo));
```

### Why Console.log?

1. **CDP Visibility**: Console messages are automatically captured by CDP
2. **No Special Transport**: No need for custom WebSocket or HTTP endpoints
3. **Debugging Friendly**: Messages visible in DevTools console
4. **Reliable**: Works even if page scripts error out

---

## Step 3: CDP Captures the Message

Chrome DevTools Protocol delivers the console message to our WebSocket listener.

### CDP Message Format

```json
{
  "method": "Console.messageAdded",
  "params": {
    "message": {
      "level": "log",
      "text": "[PyNext] SIGNAL: view_mode = \"kanban\" (was: \"list\")",
      "source": "console-api",
      "timestamp": 1702345678.123,
      "url": "http://localhost:3000/issues",
      "line": 42
    }
  }
}
```

### CDP Bridge Processing

```python
# In bridge.py
async def _on_message(self, message: str):
    data = json.loads(message)
    method = data.get("method")
    
    if method:  # It's an event
        self._dispatch_event(CDPMessage(method=method, params=data.get("params", {})))
```

---

## Step 4: EventCapture Filters and Enriches

The `EventCapture` class transforms raw CDP messages into structured `DebugEvent` objects.

### Parsing Logic

```python
# In capture.py
def process_cdp_event(self, message: CDPMessage) -> Optional[DebugEvent]:
    if message.method == "Console.messageAdded":
        return self._process_console_message(message.params)
    elif message.method == "Runtime.exceptionThrown":
        return self._process_exception(message.params)
    elif message.method == "Page.frameNavigated":
        return self._process_navigation(message.params)
    # ...
```

### PyNext Message Parsing

```python
def _process_console_message(self, params: dict) -> Optional[DebugEvent]:
    text = params.get("message", {}).get("text", "")
    
    if not text.startswith("[PyNext]"):
        return self._create_console_event(params)
    
    # Parse PyNext-specific messages
    content = text[8:].strip()  # Remove "[PyNext] " prefix
    
    if content.startswith("SIGNAL:"):
        return self._parse_signal_event(content[7:].strip())
    elif content.startswith("CLICK:"):
        return self._parse_click_event(content[6:].strip())
    elif content.startswith("SESSION_START:"):
        return self._create_event(EventType.SESSION_START, 
                                  {"intent": content[14:].strip()})
    elif content.startswith("SESSION_END:"):
        return self._parse_session_end(content[12:].strip())
    elif content.startswith("NOTE:"):
        return self._create_event(EventType.USER_NOTE,
                                  {"text": content[5:].strip()})
    # ...
```

### DebugEvent Creation

```python
@dataclass
class DebugEvent:
    seq: int              # Sequential number (auto-incremented)
    ts: float             # Unix timestamp
    type: EventType       # Parsed event type
    data: dict            # Event-specific payload
    summary: str          # Human-readable summary
    screenshot: str       # Associated screenshot path (optional)
```

Example output:

```python
DebugEvent(
    seq=42,
    ts=1702345678.123,
    type=EventType.SIGNAL_CHANGE,
    data={
        "signal_name": "view_mode",
        "old_value": "list",
        "new_value": "kanban",
    },
    summary="Signal view_mode: list → kanban",
    screenshot="",  # Filled in by ScreenshotCapture
)
```

---

## Step 5: DebugStream Writes to Files

The `DebugStream` persists events to disk for AI consumption.

### events.jsonl (Append-Only Log)

```python
# In stream.py
def write_event(self, event: DebugEvent) -> None:
    line = json.dumps({
        "seq": event.seq,
        "ts": event.ts,
        "type": event.type.value,
        "data": event.data,
        "summary": event.summary,
        "screenshot": event.screenshot,
    })
    
    with open(self.events_path, "a") as f:
        f.write(line + "\n")
```

Output in `events.jsonl`:

```json
{"seq": 40, "ts": 1702345676.0, "type": "click", "data": {"selector": "#view-toggle", "x": 150, "y": 100}, "summary": "Click on #view-toggle"}
{"seq": 41, "ts": 1702345676.5, "type": "signal_change", "data": {"signal_name": "view_mode", "old_value": "list", "new_value": "kanban"}, "summary": "Signal view_mode: list → kanban"}
{"seq": 42, "ts": 1702345677.0, "type": "user_note", "data": {"text": "View changed but items didn't update"}, "summary": "User note: View changed but items didn't update"}
```

### state.json (Current Snapshot)

```python
# Updated after each significant event
def write_state(self, state: dict) -> None:
    state["_timestamp"] = time.time()
    
    # Atomic write to prevent corruption
    temp_path = self.state_path.with_suffix(".tmp")
    with open(temp_path, "w") as f:
        json.dump(state, f, indent=2)
    temp_path.replace(self.state_path)
```

Output in `state.json`:

```json
{
  "url": "http://localhost:3000/issues",
  "title": "Issues - Linear Clone",
  "signals": {
    "view_mode": {"value": "kanban", "name": "view_mode"},
    "filter_status": {"value": "all", "name": "filter_status"}
  },
  "lastClick": {
    "element": {"selector": "#view-toggle", "tagName": "button"},
    "x": 150,
    "y": 100
  },
  "eventCount": 42,
  "running": true,
  "_timestamp": 1702345677.123
}
```

---

## Step 6: ScreenshotCapture Takes Visuals

For certain events, screenshots are captured automatically.

### Screenshot Triggers

| Event Type | Screenshot Taken | File Name Pattern |
|------------|------------------|-------------------|
| Click | After click | `042_click_view_toggle.png` |
| Signal Change | After update | `043_signal_view_mode.png` |
| Error | On exception | `044_error_undefined_is.png` |
| Manual Snapshot | On Ctrl+Shift+S | `045_manual_checking.png` |
| Navigation | After load | `046_navigation_issues.png` |

### CDP Screenshot Command

```python
# In screenshot.py
async def _take_screenshot(self) -> bytes:
    result = await self._bridge.send_command(
        "Page.captureScreenshot",
        {
            "format": "png",
            "quality": 100,
            "fromSurface": True,
        }
    )
    return base64.b64decode(result["data"])
```

### File Saving

```python
async def capture_click(self, element: dict, x: int, y: int) -> CaptureResult:
    screenshot_data = await self._take_screenshot()
    
    # Generate descriptive filename
    selector = element.get("selector", "element")[:20]
    safe_selector = re.sub(r'[^\w-]', '_', selector)
    filename = f"{self._count:03d}_click_{safe_selector}.png"
    
    path = self.screenshots_dir / filename
    with open(path, "wb") as f:
        f.write(screenshot_data)
    
    return CaptureResult(screenshot_path=path)
```

---

## Complete Trace: Button Click

Let's trace a complete button click through the entire pipeline:

### Timeline

| Time (ms) | Stage | Action |
|-----------|-------|--------|
| 0 | Browser | User clicks `#new-issue-btn` |
| 1 | Client JS | `reportClick()` called |
| 2 | Client JS | `console.log("[PyNext] CLICK: ...")` |
| 5 | CDP | WebSocket message received |
| 6 | CDPBridge | `_on_message()` parses JSON |
| 7 | EventCapture | `process_cdp_event()` creates DebugEvent |
| 8 | AIDebugger | `_on_event()` receives event |
| 9 | DebugStream | `write_event()` appends to events.jsonl |
| 10 | ScreenshotCapture | `capture_click()` starts |
| 60 | CDP | Screenshot data received |
| 65 | ScreenshotCapture | PNG saved to screenshots/ |
| 70 | DebugStream | Event updated with screenshot path |
| 75 | AIDebugger | `_update_state()` refreshes state.json |

### Data Transformation

**Stage 1: Browser Event**
```javascript
{
  type: "click",
  target: HTMLButtonElement,
  clientX: 150,
  clientY: 200
}
```

**Stage 2: Console Message**
```
[PyNext] CLICK: #new-issue-btn at (150,200)
```

**Stage 3: CDP Message**
```json
{
  "method": "Console.messageAdded",
  "params": {
    "message": {
      "text": "[PyNext] CLICK: #new-issue-btn at (150,200)",
      "level": "log"
    }
  }
}
```

**Stage 4: DebugEvent**
```python
DebugEvent(
    seq=42,
    ts=1702345678.123,
    type=EventType.CLICK,
    data={
        "selector": "#new-issue-btn",
        "x": 150,
        "y": 200,
        "tagName": "button"
    },
    summary="Click on #new-issue-btn",
    screenshot="screenshots/042_click_new_issue_btn.png"
)
```

**Stage 5: JSONL Line**
```json
{"seq": 42, "ts": 1702345678.123, "type": "click", "data": {"selector": "#new-issue-btn", "x": 150, "y": 200, "tagName": "button"}, "summary": "Click on #new-issue-btn", "screenshot": "screenshots/042_click_new_issue_btn.png"}
```

---

## Session Recording Pipeline

During a recording session, the data pipeline adds additional context:

### Timeline Building

```python
# In debugger.py
async def _capture_on_click(self, click_data: dict) -> None:
    session = self._recorder.current_session
    
    # Capture signal state BEFORE
    signals_before = await self._get_signal_snapshot()
    
    # BEFORE screenshot
    before_path = await self._screenshots.capture_action(
        action_type="click", phase="before", ...
    )
    
    await asyncio.sleep(0.1)  # Wait for DOM update
    
    # Capture signal state AFTER
    signals_after = await self._get_signal_snapshot()
    
    # AFTER screenshot
    after_path = await self._screenshots.capture_action(
        action_type="click", phase="after", ...
    )
    
    # Append to unified timeline
    session.append_event(
        event_type="click",
        data={
            "selector": selector,
            "signals_changed": self._get_changed_signals(signals_before, signals_after),
            "signals_before": signals_before,
            "signals_after": signals_after,
        },
        screenshot=str(after_path),
    )
```

### Timeline Event Structure

```python
@dataclass
class TimelineEvent:
    seq: int           # 1, 2, 3, ...
    ts: int            # Milliseconds since session start
    type: str          # "click", "note", "error", "inspect", "signal"
    data: dict         # Event-specific payload
    screenshot: str    # Relative path to screenshot
```

Example timeline:

```json
{
  "events": [
    {"seq": 1, "ts": 0, "type": "session_start", "data": {"intent": "Test form"}},
    {"seq": 2, "ts": 500, "type": "click", "data": {"selector": "#title-input"}, "screenshot": "key_frames/click_001_after.png"},
    {"seq": 3, "ts": 1200, "type": "note", "data": {"text": "Can't type in field"}},
    {"seq": 4, "ts": 2000, "type": "error", "data": {"message": "oninput is null"}},
    {"seq": 5, "ts": 3500, "type": "inspect", "data": {"selector": "#title-input", "hydrated": false}},
    {"seq": 6, "ts": 5000, "type": "session_end", "data": {"outcome": "Form broken"}}
  ]
}
```

---

## Reading Data for AI

AI assistants can read the output files directly:

### Quick State Check

```python
# Read current state
import json
with open(".pynext/debug/state.json") as f:
    state = json.load(f)
print(f"URL: {state['url']}")
print(f"Signals: {state['signals']}")
```

### Event History

```python
# Read last 10 events
events = []
with open(".pynext/debug/events.jsonl") as f:
    for line in f:
        events.append(json.loads(line))
for event in events[-10:]:
    print(f"[{event['ts']}] {event['summary']}")
```

### Session Analysis

```python
# Read session timeline
with open(".pynext/debug/sessions/rec_xxx/timeline.json") as f:
    session = json.load(f)
    
print(f"Intent: {session['intent']}")
print(f"Outcome: {session['outcome']}")
for event in session['events']:
    print(f"  [{event['ts']}ms] {event['type']}: {event['data']}")
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Event capture latency | < 5ms | Console to DebugEvent |
| Screenshot latency | 50-100ms | CDP round-trip |
| File write latency | < 1ms | Append to JSONL |
| Memory per event | ~1KB | In-memory before write |
| Disk per event | ~200 bytes | Compressed JSON |
| Screenshot size | 50-200KB | PNG, depends on content |

---

## See Also

- [Architecture](./ARCHITECTURE.md) - Component overview
- [Session Recording](./SESSION_RECORDING.md) - Recording workflow
- [AI Analysis](./AI_ANALYSIS.md) - Briefing generation

