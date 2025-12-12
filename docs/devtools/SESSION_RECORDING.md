# Session Recording - Surgical Debug Workflow

This document explains how to use surgical recording sessions to capture precise bug reports for AI analysis.

## Overview

Session recording is the most powerful debugging feature in PyNext AI DevTools. It captures:

- Time-based screenshots (every 150ms)
- User actions with before/after state
- User notes and commentary
- Element inspection data
- Console errors with stack traces
- All events in a unified timeline

When the session ends, AI automatically analyzes the data and generates a diagnosis.

---

## Quick Start

```bash
# Start dev server with AI debug
pynext dev --ai-debug --api-key sk-ant-xxx

# In browser console:
pynext_debug.session_start("Testing the create issue form")

# ... interact with your app ...
# ... add notes when you see issues ...

pynext_debug.note("Clicked submit but nothing happened")

# ... use inspect mode to select elements ...

pynext_debug.inspect()  // Hover + click to select

# When done:
pynext_debug.session_end("Form submission is broken")

# AI generates briefing.md automatically
```

---

## Session Lifecycle

### Starting a Session

```javascript
pynext_debug.session_start("What you're testing")
```

**What happens internally:**

1. **SessionRecorder creates session directory**:
   ```
   .pynext/debug/sessions/rec_1702345678_abc123/
   ├── all_frames/      # Created empty
   ├── key_frames/      # Created empty
   └── annotated_frames/  # Created empty
   ```

2. **Session object initialized**:
   ```python
   RecordingSession(
       session_id="rec_1702345678_abc123",
       intent="What you're testing",
       start_time=time.time(),
       timeline=[],
       console_errors=[],
   )
   ```

3. **Hydration map captured**:
   ```python
   session.hydration_map = {
       "url": "http://localhost:3000/issues",
       "signals": {"view_mode": {"value": "list"}, ...},
       "title": "Issues - Linear Clone",
   }
   ```

4. **Screenshot loop started**:
   ```python
   asyncio.create_task(self._screenshot_loop())
   # Takes screenshot every 150ms to all_frames/
   ```

### During Recording

Every 150ms, a frame is captured:
```
all_frames/0001.png
all_frames/0002.png
all_frames/0003.png
...
```

All events are appended to the timeline:
- Clicks (with before/after signal snapshots)
- User notes
- Console errors
- Element selections
- Signal changes
- Manual snapshots

### Ending a Session

```javascript
pynext_debug.session_end("What happened")
```

**What happens internally:**

1. **Screenshot loop stopped**

2. **Session finalized**:
   ```python
   session.outcome = "What happened"
   session.end_time = time.time()
   ```

3. **Files saved**:
   - `timeline.json` (primary - unified timeline)
   - `summary.json` (backwards compatibility)
   - `user_notes.json`
   - `annotations.json`

4. **AI analysis triggered** (if API key set)

---

## Timeline: The Single Source of Truth

All session events go into one unified `timeline.json`:

```json
{
  "session_id": "rec_1702345678_abc123",
  "intent": "Testing create issue form",
  "outcome": "Form submission is broken",
  "mode": "app",
  "duration_ms": 15000,
  "frame_count": 100,
  "events": [
    {
      "seq": 1,
      "ts": 0,
      "type": "session_start",
      "data": {"intent": "Testing create issue form"}
    },
    {
      "seq": 2,
      "ts": 500,
      "type": "click",
      "data": {
        "selector": "#new-issue-btn",
        "tagName": "button",
        "signals_changed": [],
        "signals_before": {"show_modal": {"value": false}},
        "signals_after": {"show_modal": {"value": true}}
      },
      "screenshot": "key_frames/click_001_after.png"
    },
    {
      "seq": 3,
      "ts": 1200,
      "type": "click",
      "data": {
        "selector": "#title-input",
        "tagName": "input"
      },
      "screenshot": "key_frames/click_002_after.png"
    },
    {
      "seq": 4,
      "ts": 2000,
      "type": "note",
      "data": {"text": "Tried to type but nothing appears"},
      "screenshot": "key_frames/note_003.png"
    },
    {
      "seq": 5,
      "ts": 3500,
      "type": "inspect",
      "data": {
        "selector": "#title-input",
        "tagName": "input",
        "handlers": {"oninput": false, "onclick": false},
        "hydrated": false,
        "source": "issues.py:142"
      },
      "screenshot": "key_frames/inspect_004.png"
    },
    {
      "seq": 6,
      "ts": 4000,
      "type": "error",
      "data": {
        "level": "error",
        "message": "Cannot read property 'set' of undefined",
        "stack": "at HTMLInputElement.oninput (signals.js:42)"
      },
      "screenshot": "key_frames/error_005.png"
    },
    {
      "seq": 7,
      "ts": 15000,
      "type": "session_end",
      "data": {"outcome": "Form submission is broken"}
    }
  ],
  "console_errors": [
    {
      "message": "Cannot read property 'set' of undefined",
      "stack": "at HTMLInputElement.oninput (signals.js:42)",
      "ts": 4000
    }
  ],
  "final_signals": {
    "show_modal": {"value": true},
    "form_title": {"value": ""}
  },
  "selected_element": {
    "selector": "#title-input",
    "tagName": "input",
    "hydrated": false,
    "handlers": {"oninput": false}
  }
}
```

---

## Event Types

### Click Events

Captured when user clicks any element.

```json
{
  "seq": 2,
  "ts": 500,
  "type": "click",
  "data": {
    "selector": "#new-issue-btn",
    "tagName": "button",
    "id": "new-issue-btn",
    "textContent": "New Issue",
    "signals_changed": [
      {"id": "show_modal", "name": "show_modal", "before": false, "after": true}
    ],
    "signals_before": {...},
    "signals_after": {...}
  },
  "screenshot": "key_frames/click_001_after.png"
}
```

**Before/After Screenshots:**
- `click_001_before.png` - State before click
- `click_001_after.png` - State after click (100ms delay)

### Note Events

Added when user calls `pynext_debug.note()`.

```json
{
  "seq": 4,
  "ts": 2000,
  "type": "note",
  "data": {
    "text": "Tried to type but nothing appears"
  },
  "screenshot": "key_frames/note_003.png"
}
```

### Error Events

Captured from console errors and JS exceptions.

```json
{
  "seq": 6,
  "ts": 4000,
  "type": "error",
  "data": {
    "level": "error",
    "message": "Cannot read property 'set' of undefined",
    "stack": "at HTMLInputElement.oninput (signals.js:42)\n    at ...",
    "source": "signals.js",
    "line": 42
  },
  "screenshot": "key_frames/error_005.png"
}
```

### Inspect Events

Captured when user selects an element via `pynext_debug.inspect()`.

```json
{
  "seq": 5,
  "ts": 3500,
  "type": "inspect",
  "data": {
    "selector": "#title-input",
    "tagName": "input",
    "id": "title-input",
    "classes": ["form-input"],
    "textContent": "",
    "source": "issues.py:142",
    "handlers": {
      "oninput": false,
      "onclick": false
    },
    "hydrated": false
  },
  "screenshot": "key_frames/inspect_004.png"
}
```

### Signal Events

Captured when signals change.

```json
{
  "seq": 8,
  "ts": 5500,
  "type": "signal",
  "data": {
    "signal_name": "view_mode",
    "new_value": "kanban"
  },
  "screenshot": "key_frames/signal_006.png"
}
```

### Snapshot Events

Captured on manual `pynext_debug.snapshot()` or Ctrl+Shift+S.

```json
{
  "seq": 9,
  "ts": 6000,
  "type": "snapshot",
  "data": {
    "note": "Checking modal position"
  },
  "screenshot": "key_frames/snapshot_007.png"
}
```

---

## In-Browser API Reference

### `pynext_debug.session_start(intent)`

Begin a recording session.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `intent` | string | Yes | What you're testing |

```javascript
pynext_debug.session_start("Testing the login flow")
```

Returns: `true` if started, `false` if already active.

---

### `pynext_debug.session_end(outcome)`

End the recording session.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `outcome` | string | Yes | What happened |

```javascript
pynext_debug.session_end("Login button unresponsive")
```

Returns: Session info object or `null` if no active session.

---

### `pynext_debug.note(text)`

Add a note during the session.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Your observation |

```javascript
pynext_debug.note("Input field not accepting keystrokes")
pynext_debug.note("Modal closes when clicking inside")
pynext_debug.note("Expected: form should submit")
```

Returns: `true` if added, `false` if no active session.

---

### `pynext_debug.inspect()`

Enter element inspection mode.

```javascript
pynext_debug.inspect()
```

**How it works:**
1. Move mouse over elements - blue highlight appears
2. Tooltip shows component info, source file, handler status
3. Click to SELECT element
4. Element info logged to console and added to session

---

### `pynext_debug.snapshot(note)`

Force a screenshot capture.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `note` | string | No | Label for the snapshot |

```javascript
pynext_debug.snapshot("Before clicking submit")
pynext_debug.snapshot()  // No label
```

Also available via keyboard: **Ctrl+Shift+S**

---

### `pynext_debug.status()`

Check current session status.

```javascript
pynext_debug.status()
// Returns: {active: true, id: "rec_xxx", intent: "...", elapsed: 5000, notes: 3}
```

---

### `pynext_debug.draw()`

Enable drawing mode for annotations.

**Note:** Drawing mode is not yet fully implemented in the injected script. Full drawing support requires the ai-debug.js runtime.

---

## Output Files

After a session ends, these files are created:

```
sessions/rec_1702345678_abc123/
├── timeline.json         # PRIMARY - Unified timeline (see above)
├── summary.json          # Session metadata + legacy format
├── user_notes.json       # Just the notes array
├── annotations.json      # Drawing coordinates (if any)
├── actions.jsonl         # Actions in JSONL format
├── briefing.md           # AI-generated diagnosis
├── narration.json        # AI frame descriptions
├── instructions.md       # How to read this session
├── storyboard.png        # Composite of key frames
├── all_frames/           # Every captured frame (150ms interval)
│   ├── 0001.png
│   ├── 0002.png
│   └── ...
├── key_frames/           # Important screenshots
│   ├── click_001_before.png
│   ├── click_001_after.png
│   ├── note_003.png
│   └── ...
└── annotated_frames/     # Screenshots with drawings (if any)
```

### File Descriptions

| File | Purpose | When to Read |
|------|---------|--------------|
| `timeline.json` | All events chronologically | Understanding what happened |
| `briefing.md` | AI diagnosis and recommendations | **Start here** |
| `summary.json` | Session metadata | Quick overview |
| `user_notes.json` | User observations | Understanding user intent |
| `narration.json` | AI frame-by-frame description | Detailed visual analysis |
| `instructions.md` | How Cursor should read session | Share with AI |
| `storyboard.png` | Visual overview | Quick visual scan |
| `key_frames/` | Important screenshots | Visual evidence |
| `all_frames/` | Complete visual timeline | Frame-by-frame analysis |

---

## Best Practices

### 1. Be Specific with Intent

```javascript
// Good
pynext_debug.session_start("Testing if form validation shows errors on empty submit")

// Bad
pynext_debug.session_start("testing stuff")
```

### 2. Add Notes at Key Moments

```javascript
pynext_debug.session_start("Testing create issue form")

// Note when you observe something
pynext_debug.note("Clicked title input but cursor didn't appear")

// Note expected vs actual behavior
pynext_debug.note("Expected: input should accept keystrokes. Actual: nothing happens")

// Note any visual issues
pynext_debug.note("Modal appears but background is not dimmed")
```

### 3. Use Inspect Mode for Problem Elements

```javascript
// After noticing an element doesn't work
pynext_debug.inspect()
// Hover over the element, click to select
// Check if handlers: {oninput: false} - that's the problem!
```

### 4. Be Descriptive with Outcome

```javascript
// Good - describes what's broken and any patterns noticed
pynext_debug.session_end("Form inputs don't accept text. Inspect showed handlers not attached. Likely hydration bug.")

// Bad
pynext_debug.session_end("broken")
```

### 5. Keep Sessions Focused

```javascript
// One session per bug/feature
pynext_debug.session_start("Testing form validation")
// ... test only form validation ...
pynext_debug.session_end("Validation works correctly")

pynext_debug.session_start("Testing form submission")
// ... test only submission ...
pynext_debug.session_end("Submit button doesn't respond")
```

---

## AI Analysis

When a session ends and an API key is configured, AI analysis runs automatically.

### Generated Files

1. **`briefing.md`** - Primary diagnosis document
   - Quick summary
   - Bug type classification
   - Root cause analysis
   - Recommended actions
   - Files to investigate

2. **`narration.json`** - Frame-by-frame descriptions
   - AI narration for each key frame
   - Observations about UI state
   - Key frame markers

3. **`instructions.md`** - Meta-prompt for Cursor
   - How to read the session
   - Pattern recognition guide
   - PyNext-specific context

4. **`storyboard.png`** - Visual composite
   - Key frames arranged in grid
   - Session ID and intent in header
   - Quick visual overview

### Sharing with Cursor

```
User: Here's my debug session:
@.pynext/debug/sessions/rec_xxx/briefing.md
@.pynext/debug/sessions/rec_xxx/timeline.json

Cursor: I've analyzed your debug session. Here's what I found:
...
```

---

## Troubleshooting

### Session Not Starting

```javascript
pynext_debug.session_start("test")
// Returns false
```

**Solution:** Check if a session is already active:
```javascript
pynext_debug.status()
// If active: true, end it first
pynext_debug.session_end("cancelled")
```

### No Screenshots Captured

Check console for errors:
```
[PyNext AI Debug] Screenshot error: ...
```

**Common causes:**
- Chrome running in background
- Window minimized
- Permissions issue

### AI Analysis Not Running

Check console output:
```
[PyNext AI Debug] No API key - skipping AI analysis
```

**Solution:** Set API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-xxx
# or
pynext dev --ai-debug --api-key sk-ant-xxx
```

### Timeline Empty

Check that events are being captured:
```javascript
pynext_debug.eventCount
// Should increase as you interact
```

**If 0:** The injection script may not be loaded. Check:
```javascript
typeof pynext_debug
// Should be "object"
```

---

## See Also

- [CLI Commands](./CLI_COMMANDS.md) - Full command reference
- [AI Analysis](./AI_ANALYSIS.md) - Briefing generation details
- [Cursor Integration](./CURSOR_INTEGRATION.md) - Using sessions with Cursor

