# AI Debug Architecture

This document provides a complete technical reference for the PyNext AI DevTools architecture.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PYNEXT DEV SERVER                                   │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         AIDebugger (Orchestrator)                         │  │
│  │                           pynext/devtools/debugger.py                     │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│        │              │              │              │              │            │
│        ▼              ▼              ▼              ▼              ▼            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Chrome   │  │   CDP    │  │  Event   │  │Screenshot│  │  Debug   │          │
│  │ Launcher │  │  Bridge  │  │ Capture  │  │ Capture  │  │  Stream  │          │
│  │          │  │          │  │          │  │          │  │          │          │
│  │launcher  │  │ bridge   │  │ capture  │  │screenshot│  │ stream   │          │
│  │.py       │  │ .py      │  │ .py      │  │ .py      │  │ .py      │          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
│        │              │              │              │              │            │
│        │              │              ▼              ▼              ▼            │
│        │              │       ┌──────────────────────────────────────┐          │
│        │              │       │         .pynext/debug/               │          │
│        │              │       │  ├── events.jsonl                    │          │
│        │              │       │  ├── state.json                      │          │
│        │              │       │  ├── screenshots/                    │          │
│        │              │       │  └── sessions/                       │          │
│        │              │       └──────────────────────────────────────┘          │
│        │              │                                                         │
│        ▼              ▼                                                         │
│  ┌──────────────────────────────────────────┐                                   │
│  │               Chrome Browser              │                                   │
│  │  ┌──────────────────────────────────┐    │                                   │
│  │  │       JSInjector Script          │    │                                   │
│  │  │       (pynext_debug API)         │    │                                   │
│  │  └──────────────────────────────────┘    │                                   │
│  │                    │                      │                                   │
│  │                    ▼                      │                                   │
│  │  ┌──────────────────────────────────┐    │                                   │
│  │  │      __pynext__ Runtime          │    │                                   │
│  │  │      (signals, effects)          │    │                                   │
│  │  └──────────────────────────────────┘    │                                   │
│  └──────────────────────────────────────────┘                                   │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    Session Recording & AI Analysis                        │  │
│  │                                                                           │  │
│  │  ┌──────────────┐          ┌──────────────┐          ┌──────────────┐    │  │
│  │  │   Session    │   ───►   │   Session    │   ───►   │   briefing   │    │  │
│  │  │   Recorder   │          │   Processor  │          │   .md        │    │  │
│  │  │              │          │              │          │              │    │  │
│  │  │ recorder.py  │          │ processor.py │          │ Claude 4.5   │    │  │
│  │  │              │          │              │          │ Opus         │    │  │
│  │  └──────────────┘          └──────────────┘          └──────────────┘    │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. AIDebugger (`debugger.py`)

The main orchestrator that coordinates all debugging components.

**Location:** `pynext/devtools/debugger.py`

**Responsibilities:**
- Initialize and start all sub-components
- Handle session lifecycle (start/end)
- Route events to appropriate handlers
- Manage graceful shutdown with signal handlers

**Key Classes:**

```python
class DebugMode(Enum):
    """Debug mode determines what data is captured."""
    APP = "app"           # For app developers
    CORE = "core"         # For PyNext framework developers
    EVERYTHING = "everything"  # Full diagnostic capture

class DebugConfig:
    """Configuration for AI Debugger."""
    mode: DebugMode = DebugMode.APP
    output_dir: Path = Path(".pynext/debug")
    debug_port: int = 9222
    headless: bool = False
    take_screenshots: bool = True
    screenshot_interval_ms: int = 150
    api_key: Optional[str] = None  # For AI analysis

class AIDebugger:
    """Main orchestrator for PyNext AI DevTools."""
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `start(url)` | Launch Chrome, connect CDP, inject hooks |
| `stop()` | Disconnect, shutdown Chrome, flush files |
| `wait()` | Block until Ctrl+C, handle signals |
| `snapshot(note)` | Take manual screenshot |
| `get_state()` | Get current browser state |
| `get_signal(id)` | Get signal value |
| `set_signal(id, value)` | Set signal for testing |

**Event Routing:**

```
CDP Event (message)
       │
       ▼
 _on_cdp_event()
       │
       ▼
 EventCapture.process_cdp_event()
       │
       ▼
 DebugEvent
       │
       ▼
 _on_event()
       │
       ├──► SESSION_START ──► _start_session()
       ├──► SESSION_END ──► _end_session() ──► AI Analysis
       ├──► USER_NOTE ──► _capture_on_note()
       ├──► CLICK ──► _capture_on_click()
       ├──► SIGNAL_CHANGE ──► _capture_on_signal()
       ├──► JS_EXCEPTION ──► _capture_on_error()
       ├──► ELEMENT_SELECT ──► _capture_on_inspect()
       └──► Other ──► _maybe_screenshot()
```

---

### 2. ChromeLauncher (`launcher.py`)

Finds and launches Chrome/Chromium with debugging enabled.

**Location:** `pynext/devtools/launcher.py`

**Responsibilities:**
- Auto-detect Chrome installation across platforms
- Launch with CDP port enabled
- Create isolated user profile
- Handle Chrome lifecycle

**Platform Detection:**

```python
# macOS
CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]

# Linux
CHROME_PATHS = [
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
]

# Windows
CHROME_PATHS = [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
]
```

**Launch Arguments:**

```bash
--remote-debugging-port=9222    # Enable CDP
--no-first-run                  # Skip setup wizard
--no-default-browser-check      # Skip default browser prompt
--user-data-dir=/tmp/xxx        # Isolated profile
--window-size=1280,800          # Fixed window size
```

**Key Methods:**

| Method | Return | Purpose |
|--------|--------|---------|
| `find_chrome()` | `Path` | Find Chrome executable |
| `launch(url, headless, window_size)` | `str` | Launch and return WebSocket URL |
| `shutdown()` | `None` | Terminate Chrome process |
| `wait_for_ready()` | `str` | Wait for CDP to be available |

---

### 3. CDPBridge (`bridge.py`)

WebSocket connection to Chrome DevTools Protocol.

**Location:** `pynext/devtools/bridge.py`

**Responsibilities:**
- Maintain WebSocket connection to Chrome
- Send commands to CDP
- Receive and dispatch CDP events
- Handle connection lifecycle

**Subscribed Domains:**

| Domain | Purpose | Events |
|--------|---------|--------|
| `Console` | Capture console.log/warn/error | `messageAdded` |
| `Network` | Track fetch/XHR | `requestWillBeSent`, `responseReceived` |
| `Page` | Navigation events | `frameNavigated`, `loadEventFired` |
| `Runtime` | JS execution, exceptions | `exceptionThrown` |
| `DOM` | Get page HTML | (commands only) |

**Key Commands Used:**

| Command | Purpose |
|---------|---------|
| `Page.captureScreenshot` | Take PNG screenshot |
| `DOM.getDocument` | Get document root |
| `DOM.getOuterHTML` | Get full page HTML |
| `Runtime.evaluate` | Execute JavaScript |
| `Page.addScriptToEvaluateOnNewDocument` | Inject persistent script |

**Key Methods:**

```python
class CDPBridge:
    async def connect(ws_url: str) -> None
    async def disconnect() -> None
    async def enable_domains() -> None
    async def send_command(method: str, params: dict) -> dict
    async def execute_script(script: str) -> Any
    def on_event(callback: Callable[[CDPMessage], None]) -> None
```

---

### 4. JSInjector (`injector.py`)

Injects client-side tracking JavaScript into the page.

**Location:** `pynext/devtools/injector.py`

**Responsibilities:**
- Inject tracking script that persists across navigation
- Provide `pynext_debug` API to browser console
- Hook into `__pynext__` runtime for signal tracking
- Report events via console.log with `[PyNext]` prefix

**Injected Global: `pynext_debug`**

```javascript
window.pynext_debug = {
    // Session management
    session_start(intent),    // Begin recording
    session_end(outcome),     // End recording
    note(text),               // Add user note
    snapshot(note),           // Force screenshot
    
    // Element inspection
    inspect(),                // Enable inspect mode
    
    // Drawing annotations
    draw(tool),               // Start drawing mode (not yet implemented)
    
    // State access
    getState(),               // Get current state
    status(),                 // Print status to console
    
    // Internal tracking
    signals: {},              // Tracked signal values
    eventCount: 0,            // Events sent to Python
    lastClick: null,          // Last click info
    _sessionActive: false,    // Recording state
};
```

**Injection Process:**

```
1. Page.addScriptToEvaluateOnNewDocument
   ├── Script persists across navigations
   └── Runs before any page JS
   
2. Runtime.evaluate (for current page)
   └── Immediate injection on current page

3. Verification
   └── Check typeof pynext_debug === "object"
```

**Key Methods:**

```python
class JSInjector:
    async def inject(force: bool = False) -> bool
    async def is_already_injected() -> bool
    async def get_state() -> dict | None
    async def trigger_snapshot(note: str) -> bool
    async def get_signal_value(signal_id: str) -> Any
    async def set_signal_value(signal_id: str, value: Any) -> bool
    async def list_signals() -> list[dict]
```

---

### 5. EventCapture (`capture.py`)

Filters and enriches raw CDP events.

**Location:** `pynext/devtools/capture.py`

**Responsibilities:**
- Parse raw CDP messages
- Identify PyNext-specific events (`[PyNext]` prefix)
- Create structured `DebugEvent` objects
- Emit events to registered callbacks

**EventType Enum:**

```python
class EventType(str, Enum):
    # Console
    CONSOLE_LOG = "console_log"
    CONSOLE_WARN = "console_warn"
    CONSOLE_ERROR = "console_error"
    
    # User interaction
    CLICK = "click"
    INPUT = "input"
    
    # PyNext-specific
    SIGNAL_CHANGE = "signal_change"
    EFFECT_RUN = "effect_run"
    HYDRATION_COMPLETE = "hydration_complete"
    
    # Session
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    USER_NOTE = "user_note"
    ELEMENT_SELECT = "element_select"
    MANUAL_SNAPSHOT = "manual_snapshot"
    
    # Errors
    JS_EXCEPTION = "js_exception"
    
    # Navigation
    NAVIGATION = "navigation"
    
    # Internal
    DEBUG_START = "debug_start"
    DEBUG_END = "debug_end"
```

**Event Flow:**

```
Raw CDP Event
      │
      ▼
Console.messageAdded?
      │
      ├── Yes ──► Check for [PyNext] prefix
      │              │
      │              ├── [PyNext] SIGNAL: ──► EventType.SIGNAL_CHANGE
      │              ├── [PyNext] CLICK: ──► EventType.CLICK  
      │              ├── [PyNext] NOTE: ──► EventType.USER_NOTE
      │              ├── [PyNext] SESSION_START: ──► EventType.SESSION_START
      │              ├── [PyNext] SESSION_END: ──► EventType.SESSION_END
      │              ├── [PyNext] ELEMENT_SELECT: ──► EventType.ELEMENT_SELECT
      │              └── Other ──► EventType.CONSOLE_LOG/WARN/ERROR
      │
      ├── Runtime.exceptionThrown? ──► EventType.JS_EXCEPTION
      │
      ├── Page.frameNavigated? ──► EventType.NAVIGATION
      │
      └── Network.* ? ──► (filtered based on mode)
```

**DebugEvent Structure:**

```python
@dataclass
class DebugEvent:
    seq: int              # Sequential event number
    ts: float             # Unix timestamp
    type: EventType       # Event type
    data: dict            # Event-specific payload
    summary: str          # Human-readable summary
    screenshot: str       # Path to associated screenshot (optional)
```

---

### 6. ScreenshotCapture (`screenshot.py`)

Captures screenshots and DOM snapshots.

**Location:** `pynext/devtools/screenshot.py`

**Responsibilities:**
- Take PNG screenshots via CDP
- Capture DOM HTML snapshots
- Name files descriptively
- Manage frame numbering

**Capture Triggers:**

| Trigger | When | Method |
|---------|------|--------|
| Initial | On debug start | `capture_initial()` |
| Click | After every click | `capture_click()` |
| Signal | After signal.set() | `capture_signal_change()` |
| Error | On JS exception | `capture_error()` |
| Note | When user adds note | (via `capture_action`) |
| Snapshot | Manual Ctrl+Shift+S | `capture_manual()` |
| Frame | Every 150ms during session | `capture_frame()` |
| Action | Before/after actions | `capture_action()` |

**File Naming:**

```
screenshots/
├── 001_initial.png
├── 002_click_new_issue_btn.png
├── 003_signal_view_mode.png
├── 004_error_undefined_is_not.png
└── 005_manual_checking_modal.png

sessions/rec_xxx/
├── all_frames/
│   ├── 0001.png
│   ├── 0002.png
│   └── ...
└── key_frames/
    ├── click_001_before.png
    ├── click_001_after.png
    └── ...
```

---

### 7. DebugStream (`stream.py`)

Writes events and state to files.

**Location:** `pynext/devtools/stream.py`

**Responsibilities:**
- Write events to `events.jsonl` (append-only)
- Update `state.json` (current snapshot)
- Handle file rotation
- Atomic writes to prevent corruption

**Output Format:**

`events.jsonl` (newline-delimited JSON):
```json
{"seq": 1, "ts": 1702345678.123, "type": "debug_start", "data": {}, "summary": "Debug session started"}
{"seq": 2, "ts": 1702345679.456, "type": "click", "data": {"selector": "#btn", "x": 150, "y": 200}, "summary": "Click on #btn"}
{"seq": 3, "ts": 1702345680.789, "type": "signal_change", "data": {"signal_name": "count", "old_value": 0, "new_value": 1}, "summary": "Signal count: 0 → 1"}
```

`state.json` (current state):
```json
{
  "url": "http://localhost:3000/issues",
  "title": "Issues - Linear Clone",
  "signals": {
    "view_mode": {"value": "kanban", "name": "view_mode"},
    "filter_status": {"value": "all", "name": "filter_status"}
  },
  "lastClick": {"element": {"selector": "#new-btn"}, "x": 150, "y": 200},
  "eventCount": 42,
  "running": true
}
```

---

### 8. SessionRecorder (`recorder.py`)

Manages surgical debug recording sessions.

**Location:** `pynext/devtools/recorder.py`

**Responsibilities:**
- Session lifecycle (start/end)
- Record actions with full context
- Build unified timeline
- Save session files

**Session Lifecycle:**

```
pynext_debug.session_start("Testing form")
        │
        ▼
   ┌────────────────────────────────────┐
   │   RECORDING ACTIVE                 │
   │                                    │
   │  • Screenshots every 150ms         │
   │  • Clicks captured with context    │
   │  • Notes added to timeline         │
   │  • Errors captured with stack      │
   │  • Elements can be inspected       │
   │  • Signals tracked before/after    │
   └────────────────────────────────────┘
        │
        ▼
pynext_debug.session_end("Form broken")
        │
        ▼
   Save timeline.json, summary.json
        │
        ▼
   Trigger AI Analysis (if API key set)
```

**Key Classes:**

```python
@dataclass
class TimelineEvent:
    """Single unified event in the timeline."""
    seq: int           # Sequential number
    ts: int            # Milliseconds since session start
    type: str          # Event type
    data: dict         # Event-specific payload
    screenshot: str    # Path to screenshot (optional)

@dataclass
class RecordingSession:
    """Complete recording session with all captured data."""
    session_id: str
    intent: str
    outcome: str
    timeline: List[TimelineEvent]    # Unified timeline
    console_errors: List[dict]       # Console errors
    selected_element: ElementInfo    # From inspect mode
    hydration_map: dict              # Initial state
```

---

### 9. SessionProcessor (`processor.py`)

AI analysis using Claude 4.5 Opus.

**Location:** `pynext/devtools/processor.py`

**Responsibilities:**
- Load session data (timeline.json)
- Send to Claude with screenshots
- Parse AI response
- Generate output files

**Analysis Pipeline:**

```
timeline.json
      │
      ├──► Load session metadata
      │
      ├──► Load key_frames/*.png as base64
      │
      ├──► Build diagnosis prompt
      │         │
      │         ▼
      │    Claude 4.5 Opus API Call
      │    (claude-opus-4-5-20251101)
      │         │
      │         ▼
      │    Parse JSON response
      │
      ├──► Generate briefing.md
      │
      ├──► Generate narration.json
      │
      ├──► Generate instructions.md
      │
      └──► Generate storyboard.png
```

**Generated Files:**

| File | Purpose | Content |
|------|---------|---------|
| `briefing.md` | Primary AI diagnosis | Summary, root cause, actions |
| `narration.json` | Frame-by-frame descriptions | AI narration per screenshot |
| `instructions.md` | Meta-prompt for Cursor | How to read the session |
| `storyboard.png` | Visual timeline | Composite of key frames |

---

## Data Flow Summary

### Event Capture Flow

```
Browser Click
      │
      ▼
pynext_debug.reportClick()
      │
      ▼
console.log("[PyNext] CLICK: #btn at (150,200)")
      │
      ▼
CDP: Console.messageAdded
      │
      ▼
CDPBridge._on_message()
      │
      ▼
EventCapture.process_cdp_event()
      │
      ▼
DebugEvent(type=CLICK, data={selector:"#btn", x:150, y:200})
      │
      ▼
AIDebugger._on_event()
      │
      ├──► DebugStream.write_event() ──► events.jsonl
      │
      └──► ScreenshotCapture.capture_click() ──► screenshots/
```

### Session Recording Flow

```
pynext_debug.session_start("Test form")
      │
      ▼
console.log("[PyNext] SESSION_START: Test form")
      │
      ▼
AIDebugger._on_event(SESSION_START)
      │
      ▼
AIDebugger._start_session()
      │
      ├──► SessionRecorder.start_session()
      │         │
      │         └──► Create sessions/rec_xxx/ directory
      │
      └──► Start screenshot loop (150ms interval)

      ... user interacts ...

pynext_debug.session_end("Form broken")
      │
      ▼
AIDebugger._end_session()
      │
      ├──► Stop screenshot loop
      │
      ├──► SessionRecorder.end_session()
      │         │
      │         └──► Save timeline.json, summary.json
      │
      └──► SessionProcessor.analyze_session()
                │
                ├──► Call Claude 4.5 Opus
                │
                └──► Generate briefing.md, narration.json
```

---

## Configuration Reference

### DebugConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `mode` | `DebugMode` | `APP` | Capture mode |
| `output_dir` | `Path` | `.pynext/debug` | Output directory |
| `debug_port` | `int` | `9222` | Chrome CDP port |
| `headless` | `bool` | `False` | Run without window |
| `window_size` | `tuple` | `(1280, 800)` | Window dimensions |
| `take_screenshots` | `bool` | `True` | Enable screenshots |
| `take_snapshots` | `bool` | `True` | Enable DOM snapshots |
| `screenshot_interval_ms` | `int` | `150` | Time-based interval |
| `max_events` | `int` | `10000` | Event buffer size |
| `api_key` | `str` | `None` | Anthropic API key |
| `enable_ai_analysis` | `bool` | `True` | Run AI on session end |

### DebugMode Options

| Mode | Audience | Captures |
|------|----------|----------|
| `APP` | App developers | Component state, user actions, app errors |
| `CORE` | PyNext maintainers | Hydration, signals, runtime traces |
| `EVERYTHING` | Complex bugs | Both layers + browser internals |

---

## File Structure Reference

```
.pynext/debug/
├── events.jsonl              # All events (append-only)
├── state.json                # Current state snapshot
├── screenshots/              # Event-triggered screenshots
│   ├── 001_initial.png
│   ├── 002_click_xxx.png
│   └── ...
├── snapshots/                # DOM HTML snapshots
│   ├── 001_initial.html
│   └── ...
└── sessions/                 # Recording sessions
    └── rec_1702345678_abc123/
        ├── timeline.json         # Unified event timeline (PRIMARY)
        ├── summary.json          # Session metadata
        ├── user_notes.json       # User notes
        ├── annotations.json      # Drawing coordinates
        ├── actions.jsonl         # Recorded actions
        ├── briefing.md           # AI diagnosis
        ├── narration.json        # AI frame narrations
        ├── instructions.md       # Meta-prompt for Cursor
        ├── storyboard.png        # Key frames composite
        ├── all_frames/           # Every captured frame
        │   ├── 0001.png
        │   └── ...
        ├── key_frames/           # Important screenshots
        │   ├── click_001_after.png
        │   └── ...
        └── annotated_frames/     # Screenshots with drawings
```

---

## See Also

- [Data Pipeline](./DATA_PIPELINE.md) - Event flow details
- [Session Recording](./SESSION_RECORDING.md) - Recording workflow
- [AI Analysis](./AI_ANALYSIS.md) - Briefing generation
- [CLI Commands](./CLI_COMMANDS.md) - Command reference
- [Cursor Integration](./CURSOR_INTEGRATION.md) - Using with Cursor AI

