# Cursor Integration Guide

How to use PyNext AI DevTools debug sessions with Cursor AI.

## Quick Start

After recording a session, share these files with Cursor:

```
@.pynext/debug/sessions/rec_xxx/briefing.md
@.pynext/debug/sessions/rec_xxx/timeline.json
```

## Reading Order

1. **`briefing.md`** - AI-generated diagnosis (start here)
2. **`timeline.json`** - Chronological event data
3. **`storyboard.png`** - Visual overview
4. **`key_frames/`** - Important screenshots

## File Reference

| File | Contains | Use For |
|------|----------|---------|
| `briefing.md` | AI diagnosis, root cause, recommendations | Understanding what's wrong |
| `timeline.json` | All events with timestamps | Precise sequence of events |
| `summary.json` | Session metadata | Quick facts |
| `user_notes.json` | User observations | User's perspective |
| `key_frames/*.png` | Important screenshots | Visual context |

## Example Conversation

```
User: Here's my debug session for the form bug:
@.pynext/debug/sessions/rec_1702345678_abc/briefing.md
@.pynext/debug/sessions/rec_1702345678_abc/timeline.json

Cursor: I've analyzed your debug session. Here's what happened:

At [1200ms], you clicked the title input (#title-input).
At [2000ms], you noted "Can't type in field".
At [3500ms], you inspected the element - hydrated: false.

The root cause is that the form bindings aren't being hydrated.
The input element at issues.py:142 has data-pynext-bind but
no oninput handler attached.

Let me fix the hydration in signals.js...
```

## Pattern Recognition

When analyzing sessions, look for:

| Pattern | Location | Meaning |
|---------|----------|---------|
| `signals_changed: []` after click | timeline events | Handler didn't update state |
| `hydrated: false` | inspect events | Hydration bug |
| `handlers: {oninput: false}` | inspect events | Event not attached |
| Error after click | console_errors | Handler throws exception |

## Useful Queries

**"What happened at timestamp X?"**
→ Filter `timeline.json` events by `ts`

**"Which signals changed?"**
→ Look for `signals_changed` in click events

**"Was the element hydrated?"**
→ Check inspect event `hydrated` field

**"What errors occurred?"**
→ Check `console_errors` array in timeline.json

## PyNext Context for Cursor

When working with PyNext debug sessions:

- **Signals**: Reactive primitives with `read()`, `set()`, `update()`
- **Hydration**: Server renders HTML, client attaches handlers
- **`data-pynext-bind`**: Attribute marking form bindings
- **`__pynext__.signals`**: Client-side signal registry

**Key files to investigate:**
- `pynext/runtime/signals.js` - Client-side hydration
- `pynext/server/hydration.py` - Hydration data serialization
- `pynext/core/html.py` - Server-side HTML rendering

## Timeline Event Types

| Type | Description | Key Data |
|------|-------------|----------|
| `click` | User clicked element | `selector`, `signals_changed` |
| `note` | User added note | `text` |
| `error` | Console error | `message`, `stack` |
| `inspect` | Element selected | `selector`, `hydrated`, `handlers` |
| `signal` | Signal changed | `signal_name`, `new_value` |
| `snapshot` | Manual screenshot | `note` |

## See Also

- [Session Recording](./SESSION_RECORDING.md) - Recording workflow
- [AI Analysis](./AI_ANALYSIS.md) - Briefing generation
- [CLI Commands](./CLI_COMMANDS.md) - Command reference

