# AI Analysis Pipeline - Briefing Generation

This document explains how PyNext AI DevTools uses Claude 4.5 Opus to analyze debug sessions and generate diagnosis documents.

## Overview

When a recording session ends, the `SessionProcessor` automatically:

1. Loads session data from `timeline.json`
2. Loads key frame screenshots as base64
3. Builds a diagnosis prompt
4. Calls Claude 4.5 Opus API
5. Parses the AI response
6. Generates output files (briefing.md, narration.json, etc.)

---

## When Analysis Runs

AI analysis is triggered **automatically** when:

1. User calls `pynext_debug.session_end("outcome")`
2. An API key is configured (via environment variable or `--api-key` flag)
3. `enable_ai_analysis` is `True` (default)

```bash
# Via environment variable
export ANTHROPIC_API_KEY=sk-ant-xxx
pynext dev --ai-debug

# Via CLI flag
pynext dev --ai-debug --api-key sk-ant-xxx
```

---

## The Pipeline

```
Session End
     │
     ▼
Load timeline.json ──────────────────────────────────┐
     │                                                │
     ▼                                                │
Load key_frames/*.png ─► Base64 encode ─────────────┐│
     │                                               ││
     ▼                                               ││
Build Diagnosis Prompt ◄─────────────────────────────┘│
     │                                                 │
     ▼                                                 │
Claude 4.5 Opus API Call ◄─────────────────────────────┘
     │                    (claude-opus-4-5-20251101)
     ▼
Parse JSON Response
     │
     ├──► Generate briefing.md
     ├──► Generate narration.json
     ├──► Generate instructions.md
     └──► Generate storyboard.png
```

---

## Step 1: Load Session Data

The processor first loads the session timeline:

```python
def _load_session_data(self, session_path: Path) -> Dict:
    # Prefer timeline.json (new unified format)
    timeline_path = session_path / "timeline.json"
    if timeline_path.exists():
        with open(timeline_path) as f:
            return json.load(f)
    
    # Fallback to summary.json (old format)
    summary_path = session_path / "summary.json"
    if summary_path.exists():
        with open(summary_path) as f:
            return json.load(f)
    
    return {}
```

### Session Data Structure

```json
{
  "session_id": "rec_1702345678_abc123",
  "intent": "Testing create issue form",
  "outcome": "Form inputs don't work",
  "duration_ms": 15000,
  "events": [...],
  "console_errors": [...],
  "final_signals": {...},
  "selected_element": {...}
}
```

---

## Step 2: Load Key Frames

Up to 10 screenshots are loaded and encoded as base64:

```python
def _load_key_frames(self, session_path: Path, session_data: Dict) -> List[Dict]:
    key_frames = []
    
    # Load from key_frames directory
    key_frames_dir = session_path / "key_frames"
    if key_frames_dir.exists():
        for img_path in sorted(key_frames_dir.glob("*.png"))[:10]:
            with open(img_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            key_frames.append({
                "path": img_path.name,
                "data": data,
                "frame_number": int(img_path.stem.split("_")[0])
            })
    
    # If no key frames, sample from all_frames
    if not key_frames:
        all_frames_dir = session_path / "all_frames"
        # Sample first, middle, last frames
        ...
    
    return key_frames
```

### Key Frame Selection

Priority order:
1. Screenshots in `key_frames/` directory (explicitly marked important)
2. First, middle, and last frames from `all_frames/`
3. Maximum 10 frames to stay within API limits

---

## Step 3: Build Diagnosis Prompt

The prompt is constructed with all available context:

```python
def _build_diagnosis_prompt(self, session_data: Dict) -> str:
    intent = session_data.get("intent", "Unknown")
    outcome = session_data.get("outcome", "Unknown")
    duration = session_data.get("duration_ms", 0)
    events = session_data.get("events", [])
    console_errors = session_data.get("console_errors", [])
    selected_element = session_data.get("selected_element")
    
    prompt = f"""You are analyzing a PyNext debug session. PyNext is a Python web framework with SolidJS-style reactivity.

## Session Information
- **Intent**: {intent}
- **Outcome**: {outcome}
- **Duration**: {duration}ms
- **Timeline Events**: {len(events)}
- **Console Errors**: {len(console_errors)}
"""
```

### Prompt Sections

1. **Session Information** - Basic metadata
2. **Selected Element** - If user used inspect mode
3. **Timeline** - Chronological list of all events
4. **Console Errors** - JavaScript errors with stacks
5. **Analysis Required** - JSON schema for response

### Full Prompt Example

```
You are analyzing a PyNext debug session. PyNext is a Python web framework with SolidJS-style reactivity.

## Session Information
- **Intent**: Testing create issue form
- **Outcome**: Form inputs don't work
- **Duration**: 15000ms
- **Timeline Events**: 7
- **Console Errors**: 1

## Selected Element (via Inspect Mode)
- Selector: `#title-input`
- Tag: input
- Source: `issues.py:142`
- Hydrated: false
- Handlers: {"oninput": false, "onclick": false}

## Timeline (Chronological - All Events)
This is a unified timeline of all events during the session:

- [0ms] **SESSION START**: Testing create issue form
- [500ms] **CLICK** on `#new-issue-btn` → signals changed: [show_modal]
- [1200ms] **CLICK** on `#title-input` → signals changed: none
- [2000ms] **USER NOTE**: "Tried to type but nothing appears"
- [3500ms] **INSPECTED**: `#title-input` (source: `issues.py:142`)
- [4000ms] **ERROR**: `Cannot read property 'set' of undefined`
- [15000ms] **SESSION END**: Form inputs don't work

## Console Errors
- [4000ms] Cannot read property 'set' of undefined
  Stack: at HTMLInputElement.oninput (signals.js:42)

## Analysis Required
Please analyze this debug session and provide:

1. **Bug Type**: One of:
   - "framework_bug" (bug in PyNext itself)
   - "app_bug" (bug in user's application code)
   - "config_issue" (configuration problem)
   - "user_error" (user misunderstanding)

2. **Root Cause**: What specifically went wrong

3. **Source Location**: If identifiable, which file/line contains the bug

4. **Severity**: critical/high/medium/low

5. **Recommended Actions**: Steps to fix the issue

Format your response as JSON:
```json
{
    "bug_type": "...",
    "root_cause": "...",
    "source_file": "..." or null,
    "source_line": ... or null,
    "severity": "...",
    "confidence": 0.0-1.0,
    "explanation": "...",
    "recommended_actions": ["...", "..."]
}
```
```

---

## Step 4: Claude API Call

The prompt and images are sent to Claude:

```python
async def _generate_diagnosis(self, session_data: Dict, key_frames: List[Dict]) -> Diagnosis:
    client = self._get_client()
    
    # Build prompt
    prompt = self._build_diagnosis_prompt(session_data)
    
    # Build message with images
    content = [{"type": "text", "text": prompt}]
    
    for frame in key_frames[:5]:  # Limit to 5 images for API
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": frame["data"],
            }
        })
    
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=4000,
        messages=[{"role": "user", "content": content}],
    )
    
    return self._parse_diagnosis_response(response.content[0].text)
```

### API Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `model` | `claude-opus-4-5-20251101` | Latest Claude 4.5 Opus |
| `max_tokens` | `4000` | Enough for detailed analysis |
| `images` | Up to 5 | Key frame screenshots |

---

## Step 5: Parse AI Response

The JSON response is extracted and parsed:

```python
def _parse_diagnosis_response(self, response_text: str) -> Diagnosis:
    # Extract JSON from response
    import re
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    
    if json_match:
        data = json.loads(json_match.group(1))
        return Diagnosis(
            bug_type=data.get("bug_type", "unknown"),
            root_cause=data.get("root_cause", "Unknown"),
            source_file=data.get("source_file"),
            source_line=data.get("source_line"),
            severity=data.get("severity", "medium"),
            confidence=data.get("confidence", 0.5),
            explanation=data.get("explanation", ""),
            recommended_actions=data.get("recommended_actions", []),
        )
    
    # Fallback: treat as plain text
    return Diagnosis(
        bug_type="unknown",
        root_cause=response_text[:500],
        explanation=response_text,
    )
```

### Diagnosis Structure

```python
@dataclass
class Diagnosis:
    bug_type: str           # "framework_bug", "app_bug", etc.
    root_cause: str         # What went wrong
    source_file: str        # File containing bug (optional)
    source_line: int        # Line number (optional)
    severity: str           # "critical", "high", "medium", "low"
    confidence: float       # 0.0-1.0
    explanation: str        # Detailed explanation
    recommended_actions: List[str]  # Steps to fix
```

---

## Step 6: Generate Output Files

### briefing.md

The primary output for Cursor:

```python
def _generate_briefing(self, session_path: Path, session_data: Dict, result: AnalysisResult) -> Path:
    content = f"""# Debug Session Briefing

## For: Cursor AI Assistant
## Session: {result.session_id}
## Generated: {datetime.now().isoformat()}

---

## Quick Summary

**Intent:** {session_data.get('intent', 'Unknown')}
**Outcome:** {session_data.get('outcome', 'Unknown')}
**Duration:** {session_data.get('duration_ms', 0)}ms

## Diagnosis

**Bug Type:** {result.diagnosis.bug_type}
**Root Cause:** {result.diagnosis.root_cause}
**Severity:** {result.diagnosis.severity}
**Confidence:** {result.diagnosis.confidence:.0%}

{result.diagnosis.explanation}

## Recommended Actions

1. {result.diagnosis.recommended_actions[0]}
2. {result.diagnosis.recommended_actions[1]}
...

## User Observations

- [2000ms] Tried to type but nothing appears
- [3500ms] Element inspection showed handlers not attached

## Timeline (Unified)

- [500ms] CLICK on `#new-issue-btn`
- [1200ms] CLICK on `#title-input`
- [4000ms] ERROR: Cannot read property 'set' of undefined

## Console Errors

- [4000ms] `Cannot read property 'set' of undefined`

## Files to Investigate

- `pynext/runtime/signals.js` - Client-side hydration
- `pynext/server/hydration.py` - Server-side state serialization
- `issues.py:142` - Source of problem element
"""
    
    with open(session_path / "briefing.md", "w") as f:
        f.write(content)
```

### narration.json

Frame-by-frame AI descriptions:

```python
async def _generate_narrations(self, session_data: Dict, key_frames: List[Dict]) -> List[FrameNarration]:
    narrations = []
    
    for frame in key_frames[:10]:
        prompt = f"""Describe what you see in this screenshot from a PyNext debug session.
This is frame {frame['frame_number']}.
Context: User intent was "{session_data.get('intent')}"

Provide a brief, factual description (1-2 sentences) of the UI state."""
        
        response = client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image", "source": {"type": "base64", ...}}
                ]
            }]
        )
        
        narrations.append(FrameNarration(
            frame_number=frame["frame_number"],
            narration=response.content[0].text,
        ))
    
    return narrations
```

Output:

```json
{
  "session_id": "rec_xxx",
  "frame_count": 5,
  "frames": [
    {
      "frame_number": 1,
      "timestamp_ms": 0,
      "screenshot": "click_001_after.png",
      "narration": "A modal dialog has appeared with a form for creating a new issue. The title input field is empty and appears to have focus.",
      "is_key_frame": true
    },
    {
      "frame_number": 2,
      "timestamp_ms": 1200,
      "screenshot": "click_002_after.png",
      "narration": "The cursor is now in the title input field, but no text has been entered. The field appears unresponsive.",
      "is_key_frame": true
    }
  ]
}
```

### instructions.md

Meta-prompt for Cursor:

```markdown
# How to Read This Debug Session

You are receiving a PyNext debug session. Here's how to interpret it:

## File Structure

```
session/
├── briefing.md          # START HERE - AI-generated summary
├── timeline.json        # All events chronologically
├── summary.json         # Session metadata
├── narration.json       # AI explanation per frame
├── key_frames/          # Important screenshots
└── all_frames/          # Every captured frame
```

## Reading Order

1. **Read `briefing.md` first** - Contains diagnosis and recommended actions
2. **Look at `storyboard.png`** - Visual timeline of key moments
3. **Check `timeline.json`** - Precise event sequence
4. **Examine `key_frames/`** - Visual evidence

## Key Patterns to Look For

| Pattern | Meaning |
|---------|---------|
| `signals_changed: []` after click | Handler not working |
| `handlers: {oninput: false}` | Event not attached |
| `hydrated: false` | Hydration bug |
| Console error after click | Handler throws exception |
```

### storyboard.png

Composite image of key frames:

```python
def _generate_storyboard(self, session_path: Path, session_data: Dict, key_frames: List[Dict]) -> Path:
    from PIL import Image, ImageDraw, ImageFont
    
    # Settings
    thumb_width = 400
    thumb_height = 300
    padding = 20
    cols = min(len(key_frames), 4)
    rows = (len(key_frames) + cols - 1) // cols
    
    # Create canvas
    canvas = Image.new("RGB", (canvas_width, canvas_height), color="#f8f9fa")
    draw = ImageDraw.Draw(canvas)
    
    # Header
    draw.text((padding, padding), f"Session: {session_id}", fill="#333")
    draw.text((padding, 30), f"Intent: {intent}", fill="#666")
    
    # Draw frames in grid
    for i, frame in enumerate(key_frames):
        row, col = i // cols, i % cols
        x = padding + col * (thumb_width + padding)
        y = 60 + row * (thumb_height + padding + 40)
        
        # Load, resize, paste frame
        img = Image.open(BytesIO(base64.b64decode(frame["data"])))
        img.thumbnail((thumb_width, thumb_height))
        canvas.paste(img, (x, y))
        
        # Add label
        draw.text((x, y + thumb_height + 5), f"Frame {frame['frame_number']}")
    
    canvas.save(session_path / "storyboard.png")
```

---

## Error Handling

If AI analysis fails, a basic briefing is still generated:

```python
def _generate_basic_briefing(self, session_path: Path, session_data: Dict, error: str) -> Path:
    content = f"""# Debug Session Briefing

## Session: {session_data.get('session_id', 'unknown')}

**Note:** AI analysis unavailable: {error}

---

## Session Summary

**Intent:** {session_data.get('intent', 'Unknown')}
**Outcome:** {session_data.get('outcome', 'Unknown')}
**Duration:** {session_data.get('duration_ms', 0)}ms

## User Notes
{format_notes(session_data.get('notes', []))}

## Key Events
{format_events(session_data.get('key_events', []))}
"""
```

---

## Manual Analysis

You can also run analysis manually on existing sessions:

```python
from pynext.devtools import SessionProcessor

processor = SessionProcessor(api_key="sk-ant-xxx")
result = await processor.analyze_session(Path(".pynext/debug/sessions/rec_xxx"))

print(f"Diagnosis: {result.diagnosis.root_cause}")
print(f"Briefing: {result.briefing_path}")
```

Or from the command line (if implemented):

```bash
pynext debug analyze .pynext/debug/sessions/rec_xxx
```

---

## Cost Considerations

| Item | Approximate Cost |
|------|------------------|
| Diagnosis (text + 5 images) | $0.03-0.05 |
| Frame narrations (10 frames) | $0.02-0.03 |
| **Total per session** | **~$0.05-0.10** |

To reduce costs:
- Use fewer key frames
- Skip narration generation for simple bugs
- Use a cheaper model for narration

---

## See Also

- [Session Recording](./SESSION_RECORDING.md) - Recording workflow
- [Cursor Integration](./CURSOR_INTEGRATION.md) - Using with Cursor
- [CLI Commands](./CLI_COMMANDS.md) - Command reference

