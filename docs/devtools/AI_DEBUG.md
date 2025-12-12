# PyNext AI DevTools

## What This Is

PyNext AI DevTools is a native debugging feature that captures complete browser state - events AND visuals - streaming them to files that AI assistants can read in real-time. It includes **surgical recording sessions** for precise bug capture and **AI analysis** using Claude 4.5 Opus.

```bash
pynext dev --ai-debug=app     # For app developers (default)
pynext dev --ai-debug=core    # For PyNext framework developers  
pynext dev --ai-debug=everything  # Full diagnostic capture
```

This single command:
1. Launches Chrome with debugging enabled
2. Captures every click, signal change, console message
3. Takes screenshots on key events
4. Streams everything to `.pynext/debug/`
5. Provides in-browser tools for surgical debugging
6. Generates AI-powered diagnosis on session end

**Result:** AI can see exactly what you see, debug issues as effectively as a human.

## Why This Exists

Traditional debugging with AI assistants has a fundamental gap:

| What AI Can See | What AI Cannot See |
|----------------|-------------------|
| Your code | The actual UI |
| Error messages you paste | What happened before the error |
| Console logs you copy | Real-time signal changes |
| Nothing automatically | User interactions |

This creates a frustrating back-and-forth:
- "Can you show me the console?"
- "What does the page look like?"
- "Did you click the button?"
- "What was the signal value before?"

**AI DevTools closes this gap.** Every browser event is captured automatically. Every significant change triggers a screenshot. AI has complete context without asking.

## Quick Start

### 1. Install Dependencies

```bash
pip install websockets>=12.0  # Required
pip install Pillow>=10.0      # Optional: screenshot annotation
```

### 2. Start Debug Mode

```bash
pynext dev --ai-debug
```

Chrome opens automatically. Navigate and interact with your app normally.

### 3. AI Reads Debug Output

In Cursor or your AI assistant:
- Read `.pynext/debug/events.jsonl` for event stream
- Read `.pynext/debug/screenshots/*.png` for visuals
- Read `.pynext/debug/state.json` for current state

## What Gets Captured

### Events

| Type | Description | When |
|------|-------------|------|
| `console_log/warn/error` | Console messages | Any console output |
| `click` | User clicks | Every click with element info |
| `signal_change` | Signal value changes | When signal.set() is called |
| `network_request/response` | API calls | Fetch/XHR to `/api/*` |
| `js_exception` | JavaScript errors | Any uncaught exception |
| `navigation` | URL changes | SPA navigation |
| `manual_snapshot` | User-triggered | Ctrl+Shift+S |

### Screenshots

Screenshots are captured automatically on:
- **Clicks** - See what was clicked
- **Signal changes** - See the UI after state update
- **Errors** - See the page when error occurred
- **Navigation** - See each page
- **Manual trigger** - Ctrl+Shift+S

### DOM Snapshots

Full HTML captured alongside screenshots for inspecting:
- Element structure
- Attribute values
- Hidden elements
- Generated content

## Output Structure

```
.pynext/debug/
├── events.jsonl          # All events (append-only)
├── state.json            # Current state snapshot
├── screenshots/          # Event-triggered screenshots
│   ├── 001_initial.png
│   ├── 002_click_new_issue_btn.png
│   ├── 003_signal_modal_open.png
│   └── ...
├── snapshots/            # DOM HTML snapshots
│   ├── 001_initial.html
│   └── ...
└── sessions/             # Recording sessions
    └── rec_1702345678_abc123/
        ├── summary.json        # Session metadata
        ├── actions.jsonl       # All actions
        ├── user_notes.json     # User notes
        ├── annotations.json    # Drawing annotations
        ├── briefing.md         # AI diagnosis (if API key set)
        ├── narration.json      # AI frame narration
        ├── instructions.md     # Meta-prompt for Cursor
        ├── storyboard.png      # Key frames composite
        ├── all_frames/         # All screenshots
        ├── key_frames/         # Important screenshots
        └── annotated_frames/   # Screenshots with drawings
```

### events.jsonl Format

Each line is a JSON object:

```json
{
  "seq": 42,
  "ts": 1702345678.123,
  "type": "signal_change",
  "data": {
    "signal_id": "sig_124",
    "signal_name": "view_mode",
    "old_value": "list",
    "new_value": "kanban"
  },
  "summary": "Signal view_mode: list → kanban",
  "screenshot": "screenshots/042_signal_view_mode.png"
}
```

### state.json Format

Current page state:

```json
{
  "url": "http://localhost:3000/issues",
  "pathname": "/issues",
  "title": "Issues - Linear Clone",
  "signals": {
    "view_mode": {"value": "kanban", "name": "view_mode"},
    "filter_status": {"value": "all", "name": "filter_status"}
  },
  "lastClick": {
    "element": {"selector": "#new-issue-btn", "tagName": "button"},
    "x": 150,
    "y": 200
  },
  "eventCount": 42,
  "_timestamp": 1702345678.123
}
```

## Manual Snapshot Triggers

### Keyboard Shortcut

Press `Ctrl+Shift+S` in the browser. Optional note prompt appears.

### Console Command

```javascript
__pynext_debug__.snapshot("Checking modal position")
```

### From Python (testing)

```python
await debugger.snapshot("Before form submit")
```

## Debug Modes

| Mode | Flag | Focus | Audience |
|------|------|-------|----------|
| App | `--ai-debug=app` | User's application code, component state | App developers |
| Core | `--ai-debug=core` | PyNext internals, hydration, signals | Framework maintainers |
| Everything | `--ai-debug=everything` | All layers combined | Complex cross-layer bugs |

### Mode Selection

```bash
# Default - for debugging your app
pynext dev --ai-debug

# Explicit app mode (same as default)
pynext dev --ai-debug=app

# For PyNext framework developers
pynext dev --ai-debug=core

# Full diagnostic capture
pynext dev --ai-debug=everything
```

## CLI Options

```bash
pynext dev --ai-debug[=MODE] [OPTIONS]

Options:
  --ai-debug=MODE       Debug mode: app (default), core, everything
  --debug-output DIR    Output directory (default: .pynext/debug)
  --debug-port PORT     Chrome debugging port (default: 9222)
  --headless            Run Chrome without visible window
  --api-key KEY         Anthropic API key for AI analysis
```

## Session Recording API

The most powerful debugging feature is **surgical recording sessions**. Start a session, perform actions, add notes, and get AI-generated diagnosis.

### In-Browser API (pynext_debug)

```javascript
// Start a recording session
pynext_debug.session_start("Testing the form input")

// During session - add commentary
pynext_debug.note("Can't type in this field")

// Select specific element visually
pynext_debug.inspect()  // Hover + click to select

// Draw annotations on screen
pynext_debug.draw()  // Opens toolbar with circle, arrow, text tools

// Force a screenshot
pynext_debug.snapshot("Before clicking submit")

// Check session status
pynext_debug.status()

// End session with outcome
pynext_debug.session_end("Form inputs are broken")
```

### Session Workflow

1. **session_start("intent")** - Begin recording, explain what you're testing
2. **inspect()** - Hover + click to select specific element  
3. **[Perform actions]** - Click, type, interact normally
4. **note("...")** - Add commentary during session
5. **draw()** - Annotate with circles, arrows, text
6. **session_end("outcome")** - End recording, explain what happened

### Element Inspection

When you call `pynext_debug.inspect()`:

1. Move mouse over elements - blue highlight appears
2. Tooltip shows component info, source file, signal bindings
3. Click to SELECT element
4. Console logs full element details

Tooltip example:
```
┌───────────────────────────────────────┐
│  input#title-input                    │
│───────────────────────────────────────│
│  Component: IssueForm                 │
│  Source:    issues.py:142             │
│  Signal:    form_title (sig_6)        │
│  Handler:   oninput -> null (NOT!)    │
│  Hydrated:  No                        │
│                                       │
│  [Click to select]                    │
└───────────────────────────────────────┘
```

### Drawing Annotations

When you call `pynext_debug.draw()`:

1. Canvas overlay appears over entire page
2. Toolbar with tools: Pen, Circle, Arrow, Text
3. Color picker: Red, Green, Blue
4. Draw annotations to highlight issues
5. Press ESC or click Done to exit

All drawings are:
- Captured in screenshots
- Saved as JSON coordinates
- Available for AI analysis

### Session Output

After `session_end()`, files are generated in `.pynext/debug/sessions/rec_xxx/`:

```
sessions/rec_xxx/
├── RAW DATA (preserved)
│   ├── summary.json          # All events with timestamps
│   ├── user_notes.json       # Every note() call
│   ├── annotations.json      # Drawing coordinates
│   ├── all_frames/           # Every captured screenshot
│   └── annotated_frames/     # Screenshots with drawings
│
├── AI-GENERATED (analysis)
│   ├── briefing.md           # AI diagnosis and summary
│   ├── narration.json        # AI explanation per frame
│   └── instructions.md       # How Cursor should read this
│
└── PROCESSED (efficient viewing)
    ├── storyboard.png        # Key frames composite
    └── key_frames/           # Only frames where state changed
```

## AI Analysis

Sessions are analyzed by Claude 4.5 Opus to generate:

### briefing.md

AI-generated diagnosis for Cursor:

```markdown
# Debug Session Briefing

## Quick Summary
User attempted to type in form input but text did not appear.
This is a hydration bug - handlers not attached.

## Diagnosis
**Bug Type:** framework_bug
**Root Cause:** Element has data-pynext-bind="sig_6" but oninput handler is null.
**Severity:** high
**Confidence:** 90%

## User Observations
- [1200ms] "Can't type - cursor appears but nothing shows up"

## Recommended Actions
1. Open signals.js line 450
2. Check addEventListener('input', ...) is called
3. Verify formBindings data from server
```

### API Key Configuration

AI analysis requires an Anthropic API key:

```bash
# Via environment variable
export ANTHROPIC_API_KEY=sk-ant-...
pynext dev --ai-debug

# Via CLI flag
pynext dev --ai-debug --api-key=sk-ant-...
```

## Python API

For programmatic control:

```python
from pynext.devtools import AIDebugger, DebugConfig, DebugMode

# Configure with mode
config = DebugConfig(
    mode=DebugMode.APP,  # or "app", DebugMode.CORE, DebugMode.EVERYTHING
    output_dir=Path(".pynext/debug"),
    debug_port=9222,
    headless=False,
    take_screenshots=True,
    screenshot_interval_ms=150,  # Time-based screenshots
    api_key="sk-ant-...",  # For AI analysis
)

# Start debugging
debugger = AIDebugger(config)
await debugger.start("http://localhost:3000")

# Get current state
state = await debugger.get_state()
print(f"Signals: {state['signals']}")

# Get/set signal values
value = await debugger.get_signal("view_mode")
await debugger.set_signal("view_mode", "kanban")

# List all signals
signals = await debugger.list_signals()

# Take manual snapshot
await debugger.snapshot("Checking layout")

# Read recent events
events = debugger.read_events(limit=50)

# Get session summary
summary = debugger.get_summary()

# Stop
await debugger.stop()
```

### Session Recording (Python)

```python
from pynext.devtools import SessionRecorder, RecordingSession

# Create recorder
recorder = SessionRecorder(output_dir=Path(".pynext/debug"))

# Start session
session = recorder.start_session("Testing form validation")

# Record actions programmatically
from pynext.devtools.recorder import ElementInfo, SignalSnapshot, DOMSnapshot

element = ElementInfo(
    selector="#email-input",
    tag_name="input",
    pynext_source="forms.py:42",
    pynext_bind="sig_email",
)

signals = SignalSnapshot(
    signals_before={"sig_email": ""},
    signals_after={"sig_email": "test@"},
)

recorder.record_keypress(
    key="t",
    element=element,
    value_before="",
    value_after="test@",
    signals=signals,
    dom_changes=DOMSnapshot(),
)

# Add note
recorder.add_note("Email field accepting input")

# End session
session_path = recorder.end_session("Form working correctly")
```

### AI Analysis (Python)

```python
from pynext.devtools import SessionProcessor

# Analyze a session
processor = SessionProcessor(api_key="sk-ant-...")
result = await processor.analyze_session(session_path)

# Access generated files
print(f"Briefing: {result.briefing_path}")
print(f"Diagnosis: {result.diagnosis.root_cause}")
print(f"Actions: {result.diagnosis.recommended_actions}")
```

## Example Debugging Session

### The Problem

User: "The modal won't open when I click the button"

### Without AI DevTools

```
AI: Can you paste the console output?
User: [copies console]
AI: What does the page look like?
User: [takes screenshot, uploads]
AI: What's the signal value?
User: How do I check that?
AI: Open DevTools and type...
```

5 messages, 10 minutes, still debugging.

### With AI DevTools

```
AI: Let me check the debug output...

Looking at events.jsonl:
- Line 42: Click on #new-issue-btn at (150, 200)
- Line 43: signal_change: modal_open = true (was: false)
- No error events after the click

Looking at screenshot 043_signal_modal_open.png:
- Modal container exists but has display:none
- Signal changed but DOM didn't update

The issue is in the Show component - the signal 
updates but the effect isn't re-evaluating.
Let me check control_flow.py...
```

1 message, 30 seconds, root cause identified.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PYNEXT DEV SERVER                           │
│                                                                     │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐         │
│  │ ChromeLauncher│──▶│   CDPBridge   │──▶│  EventCapture │         │
│  │ (auto-launch) │   │  (WebSocket)  │   │   (filter)    │         │
│  └───────────────┘   └───────────────┘   └───────────────┘         │
│                              │                    │                 │
│                              ▼                    ▼                 │
│                      ┌───────────────┐   ┌───────────────┐         │
│                      │ScreenshotCap │   │  DebugStream  │         │
│                      │   (PNG/HTML) │   │   (JSONL)     │         │
│                      └───────────────┘   └───────────────┘         │
│                              │                    │                 │
│                              ▼                    ▼                 │
│                      ┌─────────────────────────────────┐           │
│                      │     .pynext/debug/              │           │
│                      │     ├── events.jsonl            │           │
│                      │     ├── state.json              │           │
│                      │     ├── screenshots/            │           │
│                      │     └── snapshots/              │           │
│                      └─────────────────────────────────┘           │
│                                      ▲                              │
│                                      │                              │
│                              ┌───────────────┐                     │
│                              │   JSInjector  │                     │
│                              │ (signal hooks)│                     │
│                              └───────────────┘                     │
│                                      │                              │
│                                      ▼                              │
│                              ┌───────────────┐                     │
│                              │   Browser     │                     │
│                              │   (Chrome)    │                     │
│                              └───────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### ChromeLauncher

Finds and launches Chrome with CDP enabled:
- Auto-detects Chrome on macOS, Linux, Windows
- Creates temporary profile (no interference with regular Chrome)
- Enables remote debugging port

### CDPBridge

WebSocket connection to Chrome DevTools Protocol:
- Subscribes to Console, Network, Page, Runtime, DOM domains
- Takes screenshots via Page.captureScreenshot
- Gets DOM via DOM.getOuterHTML
- Executes JavaScript via Runtime.evaluate

### EventCapture

Filters and enriches raw CDP events:
- Ignores noise (internal Chrome events)
- Adds PyNext context (signal names, component origins)
- Deduplicates rapid repeated events
- Emits structured DebugEvent objects

### ScreenshotCapture

Captures visuals on triggers:
- Takes PNG screenshots via CDP
- Captures DOM HTML snapshots
- Names files descriptively (042_click_submit_btn.png)
- Optionally highlights clicked elements

### DebugStream

Writes to files for AI consumption:
- JSONL format (append-only, crash-safe)
- State file (current snapshot, overwritten)
- File rotation on size limit
- Atomic writes to prevent corruption

### JSInjector

Injects PyNext-aware tracking:
- Patches __pynext__.signals to report changes
- Sets up click tracking with element info
- Adds manual snapshot shortcut (Ctrl+Shift+S)
- Reports via console.log with [PyNext] prefix

## Troubleshooting

### Chrome Won't Launch

```
RuntimeError: Chrome/Chromium not found
```

**Solution:** Install Chrome or set CHROME_PATH environment variable.

### Port Already in Use

```
TimeoutError: Chrome did not start within 30 seconds
```

**Solution:** Use `--debug-port 9333` or kill process on port 9222.

### Screenshots Not Captured

Check that Pillow is installed for annotation:
```bash
pip install Pillow>=10.0
```

### Events Not Appearing

1. Check `.pynext/debug/` directory exists
2. Ensure browser navigated to your dev server
3. Check console for [PyNext] DEBUG messages

## Performance

| Metric | Value |
|--------|-------|
| Event capture overhead | < 1ms per event |
| Screenshot capture | ~50-100ms per shot |
| Memory usage | ~20MB for 1000 events |
| File rotation | At 10MB or 10,000 events |

## Best Practices

### For Developers

1. **Start fresh:** Use `--ai-debug` from clean session
2. **Reproduce precisely:** Do exact steps to trigger bug
3. **Use manual snapshots:** Ctrl+Shift+S at key moments
4. **Add notes:** Describe what you expect vs. what happens

### For AI Assistants

1. **Read events first:** Get chronological view of what happened
2. **Check screenshots:** Visual context for UI issues
3. **Look for signal changes:** Track state flow
4. **Check errors:** JS exceptions often have stack traces
5. **Compare snapshots:** Before/after DOM changes

## Future Enhancements

- [ ] Video recording mode
- [ ] Network request/response bodies
- [ ] Performance metrics (LCP, FID, CLS)
- [ ] Remote debugging (debug on mobile device)
- [ ] Cursor extension for real-time streaming

## Detailed Documentation

For deeper understanding, see these companion documents:

| Document | Description |
|----------|-------------|
| [Architecture](./ARCHITECTURE.md) | Complete system architecture with component diagrams |
| [Data Pipeline](./DATA_PIPELINE.md) | Event flow from browser action to output file |
| [Session Recording](./SESSION_RECORDING.md) | Surgical recording workflow and timeline format |
| [AI Analysis](./AI_ANALYSIS.md) | Briefing generation pipeline using Claude 4.5 Opus |
| [CLI Commands](./CLI_COMMANDS.md) | Complete command reference with examples |
| [Cursor Integration](./CURSOR_INTEGRATION.md) | How to use debug sessions with Cursor AI |

## Related Documentation

- [Phase 17.9: AI DevTools](/docs/ROADMAP.md#phase-179-ai-devtools)
- [Hydration](/docs/reactive/HYDRATION.md)
- [Reactive DOM Updates](/docs/reactive/DOM_UPDATES.md)
- [Event Modifiers](/docs/reactive/EVENTS.md)

