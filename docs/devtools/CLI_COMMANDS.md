# CLI Commands - Complete Reference

This document provides a complete reference for all PyNext AI DevTools commands.

---

## Starting AI Debug

### Basic Usage

```bash
# Start dev server with AI debugging (default: app mode)
pynext dev --ai-debug

# Explicit app mode (same as above)
pynext dev --ai-debug=app

# For debugging PyNext framework internals
pynext dev --ai-debug=core

# Full diagnostic capture (app + framework + browser)
pynext dev --ai-debug=everything
```

### With Custom Port

```bash
# Run on different dev server port
pynext dev --ai-debug --port 3012

# Different Chrome debugging port
pynext dev --ai-debug --debug-port 9333
```

### With API Key for AI Analysis

```bash
# Via CLI flag (one-time)
pynext dev --ai-debug --api-key sk-ant-api03-xxx

# Via environment variable (recommended)
export ANTHROPIC_API_KEY=sk-ant-api03-xxx
pynext dev --ai-debug
```

### Headless Mode

```bash
# Run Chrome without visible window
pynext dev --ai-debug --headless
```

### Custom Output Directory

```bash
# Save debug files to custom location
pynext dev --ai-debug --debug-output ./my-debug-output
```

---

## Complete Flag Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--ai-debug[=MODE]` | `app` | Enable AI debugging. Modes: `app`, `core`, `everything` |
| `--port PORT` | `3000` | Dev server port |
| `--debug-port PORT` | `9222` | Chrome remote debugging port |
| `--debug-output DIR` | `.pynext/debug` | Output directory for debug files |
| `--api-key KEY` | env `ANTHROPIC_API_KEY` | Anthropic API key for AI analysis |
| `--headless` | `false` | Run Chrome without visible window |

### Debug Modes

| Mode | Flag | Audience | Captures |
|------|------|----------|----------|
| App | `--ai-debug=app` | App developers | Component state, user actions, app errors |
| Core | `--ai-debug=core` | PyNext maintainers | Hydration, signals, runtime traces |
| Everything | `--ai-debug=everything` | Complex bugs | Both layers + browser internals |

---

## In-Browser Commands (`pynext_debug`)

Once AI debug is running, these commands are available in the browser console:

### Session Recording

```javascript
// Start a recording session
pynext_debug.session_start("What you're testing")

// Add commentary during session
pynext_debug.note("Describe what happened")

// Force a screenshot
pynext_debug.snapshot("Optional label")

// Check session status
pynext_debug.status()

// End session with outcome
pynext_debug.session_end("What went wrong/right")
```

### Element Inspection

```javascript
// Enter inspect mode (hover to highlight, click to select)
pynext_debug.inspect()

// After clicking an element, its info is logged and saved
```

### Drawing Annotations

```javascript
// Start drawing mode (not yet fully implemented)
pynext_debug.draw()

// Press ESC to exit drawing mode
```

### Signal Access

```javascript
// Get current state (URL, signals, last click)
pynext_debug.getState()

// View all tracked signals
console.log(pynext_debug.signals)

// Check event count
console.log(pynext_debug.eventCount)
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+S` | Take manual snapshot (with optional note prompt) |

---

## Example Workflows

### Workflow 1: Quick Debug Session

```bash
# 1. Start debugging
pynext dev --ai-debug --port 3012

# 2. Navigate to your app in the Chrome window that opens
# 3. In browser console:
pynext_debug.session_start("Testing create issue form")

# 4. Interact with your app...
# 5. Add notes when you see issues:
pynext_debug.note("Clicked submit but nothing happened")

# 6. Use inspect mode if needed:
pynext_debug.inspect()
# (hover + click to select an element)

# 7. End the session:
pynext_debug.session_end("Create Issue form is broken")

# 8. Ctrl+C to stop server

# 9. Read results:
cat .pynext/debug/sessions/rec_*/briefing.md
```

### Workflow 2: Debug with AI Analysis

```bash
# 1. Set API key once (add to .bashrc/.zshrc for permanent)
export ANTHROPIC_API_KEY=sk-ant-api03-xxx

# 2. Start debugging
pynext dev --ai-debug

# 3. Record the bug...
# (see Workflow 1 steps 2-7)

# 4. After session ends, AI automatically generates:
# - briefing.md (diagnosis)
# - narration.json (frame descriptions)
# - storyboard.png (visual timeline)

# 5. Read the AI diagnosis:
cat .pynext/debug/sessions/rec_*/briefing.md
```

### Workflow 3: Share Session with Cursor

```bash
# 1. Start debug session
pynext dev --ai-debug

# 2. Record the bug, end session

# 3. In Cursor, reference the files:
```

In Cursor chat:
```
Here's my debug session:
@.pynext/debug/sessions/rec_xxx/briefing.md
@.pynext/debug/sessions/rec_xxx/timeline.json

Can you help me fix this bug?
```

### Workflow 4: Framework Developer Debug

```bash
# 1. Debug PyNext internals
pynext dev --ai-debug=core

# 2. This captures:
# - Hydration steps
# - Signal implementation details
# - Effect execution traces
# - Internal runtime state

# 3. Record session as usual...
```

### Workflow 5: Multiple Debug Sessions

```bash
# 1. Start debugging
pynext dev --ai-debug

# 2. Session 1: Test feature A
pynext_debug.session_start("Testing feature A")
# ... interact ...
pynext_debug.session_end("Feature A works")

# 3. Session 2: Test feature B
pynext_debug.session_start("Testing feature B")
# ... interact ...
pynext_debug.session_end("Feature B broken")

# 4. Each session creates its own directory:
# .pynext/debug/sessions/rec_1702345678_aaa/
# .pynext/debug/sessions/rec_1702345688_bbb/
```

---

## Output Files Quick Reference

After running a session, find files in `.pynext/debug/sessions/rec_xxx/`:

| File | Purpose | When to Read |
|------|---------|--------------|
| `briefing.md` | AI diagnosis and recommendations | **Start here** |
| `timeline.json` | All events chronologically | Need precise timestamps |
| `summary.json` | Session metadata | Quick overview |
| `user_notes.json` | Your observations | Review your notes |
| `narration.json` | AI frame descriptions | Understand each frame |
| `instructions.md` | How to read this session | Share with AI |
| `storyboard.png` | Visual timeline | Quick visual overview |
| `key_frames/` | Important screenshots | Visual evidence |
| `all_frames/` | Every captured frame | Frame-by-frame analysis |

### Real-time Files (During Debug)

| File | Purpose |
|------|---------|
| `.pynext/debug/events.jsonl` | Live event stream |
| `.pynext/debug/state.json` | Current browser state |
| `.pynext/debug/screenshots/` | Event-triggered screenshots |

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | API key for AI analysis (Claude 4.5 Opus) |
| `CHROME_PATH` | Custom Chrome/Chromium executable path |
| `PYNEXT_DEBUG_PORT` | Default Chrome debugging port |

---

## Troubleshooting

### Chrome Won't Launch

```
RuntimeError: Chrome/Chromium not found
```

**Solutions:**
1. Install Chrome: https://www.google.com/chrome/
2. Set custom path: `export CHROME_PATH=/path/to/chrome`

### Port Already in Use

```
TimeoutError: Chrome did not start within 30 seconds
```

**Solutions:**
1. Use different port: `--debug-port 9333`
2. Kill existing Chrome: `pkill -f "remote-debugging-port"`
3. Check port: `lsof -i :9222`

### AI Analysis Not Running

```
[PyNext AI Debug] No API key - skipping AI analysis
```

**Solutions:**
1. Set environment variable: `export ANTHROPIC_API_KEY=sk-ant-xxx`
2. Use CLI flag: `--api-key sk-ant-xxx`
3. Check key format: Should start with `sk-ant-`

### No Screenshots Captured

**Check:**
1. Chrome window is visible (not minimized)
2. Page is fully loaded before starting session
3. Console for error messages

### pynext_debug Not Available

```javascript
typeof pynext_debug
// Returns "undefined"
```

**Solutions:**
1. Wait for page to fully load
2. Refresh the page
3. Check console for injection errors

---

## API Key Security

**Do not commit API keys to git!**

Add to `.gitignore`:
```
.env
.pynext/
```

Use environment variables:
```bash
# .bashrc or .zshrc
export ANTHROPIC_API_KEY=sk-ant-xxx
```

Or use a `.env` file (add to .gitignore):
```
ANTHROPIC_API_KEY=sk-ant-xxx
```

---

## See Also

- [Architecture](./ARCHITECTURE.md) - System overview
- [Session Recording](./SESSION_RECORDING.md) - Recording workflow
- [AI Analysis](./AI_ANALYSIS.md) - Briefing generation
- [Cursor Integration](./CURSOR_INTEGRATION.md) - Using with Cursor

