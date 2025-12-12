"""
Session Processor - AI Analysis for Debug Sessions.

This module uses Claude 4.5 Opus to analyze debug sessions and generate:
- Frame-by-frame narration
- Diagnosis summary with root cause
- AI briefing document for Cursor
- Instructions prompt (meta-prompt)
- Storyboard composite images

Usage:
    processor = SessionProcessor(api_key="sk-...")
    
    # Analyze a completed session
    result = await processor.analyze_session(session_path)
    
    # Access generated files
    print(result.briefing_path)
    print(result.narration_path)
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Model configuration
ANALYSIS_MODEL = "claude-opus-4-5-20251101"


@dataclass
class FrameNarration:
    """AI-generated narration for a single frame."""
    frame_number: int
    timestamp_ms: int
    screenshot_path: str
    narration: str
    observations: List[str] = field(default_factory=list)
    is_key_frame: bool = False


@dataclass
class Diagnosis:
    """AI-generated diagnosis of a debug session."""
    bug_type: str  # "framework_bug", "app_bug", "config_issue", "user_error"
    root_cause: str
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    severity: str = "medium"  # "critical", "high", "medium", "low"
    confidence: float = 0.0
    explanation: str = ""
    recommended_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "bug_type": self.bug_type,
            "root_cause": self.root_cause,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "severity": self.severity,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "recommended_actions": self.recommended_actions,
        }


@dataclass
class AnalysisResult:
    """Result of AI analysis on a debug session."""
    session_id: str
    session_path: Path
    
    # Generated files
    briefing_path: Optional[Path] = None
    narration_path: Optional[Path] = None
    instructions_path: Optional[Path] = None
    storyboard_path: Optional[Path] = None
    
    # Analysis data
    diagnosis: Optional[Diagnosis] = None
    frame_narrations: List[FrameNarration] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    
    # Metadata
    analysis_time_ms: int = 0
    model_used: str = ANALYSIS_MODEL
    tokens_used: int = 0


class SessionProcessor:
    """
    Processes debug sessions using Claude 4.5 Opus for AI analysis.
    
    This class:
    1. Reads session data (summary.json, actions.jsonl, screenshots)
    2. Sends to Claude for analysis
    3. Generates briefing.md, narration.json, instructions.md
    4. Creates storyboard composite image
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the session processor.
        
        Args:
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = ANALYSIS_MODEL
        self._client = None
    
    def _get_client(self):
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                if not self.api_key:
                    raise ValueError("Anthropic API key not provided")
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package required for AI analysis.\n"
                    "Install with: pip install anthropic"
                )
        return self._client
    
    async def analyze_session(self, session_path: Path) -> AnalysisResult:
        """
        Analyze a completed debug session.
        
        Args:
            session_path: Path to session directory
        
        Returns:
            AnalysisResult with generated files and diagnosis
        """
        import time
        start_time = time.time()
        
        session_path = Path(session_path)
        
        # Load session data
        session_data = self._load_session_data(session_path)
        
        # Load key frame screenshots
        key_frames = self._load_key_frames(session_path, session_data)
        
        result = AnalysisResult(
            session_id=session_data.get("session_id", "unknown"),
            session_path=session_path,
        )
        
        try:
            # Generate diagnosis
            result.diagnosis = await self._generate_diagnosis(session_data, key_frames)
            
            # Generate frame narrations
            result.frame_narrations = await self._generate_narrations(session_data, key_frames)
            
            # Extract key insights
            result.key_insights = self._extract_key_insights(session_data, result.diagnosis)
            
            # Generate output files
            result.briefing_path = self._generate_briefing(session_path, session_data, result)
            result.narration_path = self._generate_narration_file(session_path, result)
            result.instructions_path = self._generate_instructions(session_path, session_data)
            result.storyboard_path = self._generate_storyboard(session_path, session_data, key_frames)
            
        except Exception as e:
            # Still generate basic files without AI
            result.briefing_path = self._generate_basic_briefing(session_path, session_data, str(e))
        
        result.analysis_time_ms = int((time.time() - start_time) * 1000)
        
        return result
    
    def _load_session_data(self, session_path: Path) -> Dict:
        """Load session data - prefer timeline.json if available."""
        # Try timeline.json first (new unified format)
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
    
    def _load_key_frames(self, session_path: Path, session_data: Dict) -> List[Dict]:
        """Load key frame screenshots as base64."""
        key_frames = []
        
        # Get key frame numbers from session data
        key_frame_numbers = session_data.get("key_frames", [])
        
        # Load from key_frames directory first
        key_frames_dir = session_path / "key_frames"
        if key_frames_dir.exists():
            for img_path in sorted(key_frames_dir.glob("*.png"))[:10]:  # Limit to 10
                try:
                    with open(img_path, "rb") as f:
                        data = base64.b64encode(f.read()).decode()
                    key_frames.append({
                        "path": str(img_path.name),
                        "data": data,
                        "frame_number": int(img_path.stem.split("_")[0]) if img_path.stem[0].isdigit() else 0,
                    })
                except Exception:
                    pass
        
        # If no key frames, sample from all_frames
        if not key_frames:
            all_frames_dir = session_path / "all_frames"
            if all_frames_dir.exists():
                all_frames = sorted(all_frames_dir.glob("*.png"))
                # Sample first, middle, last
                if len(all_frames) >= 3:
                    samples = [all_frames[0], all_frames[len(all_frames)//2], all_frames[-1]]
                else:
                    samples = all_frames[:3]
                
                for img_path in samples:
                    try:
                        with open(img_path, "rb") as f:
                            data = base64.b64encode(f.read()).decode()
                        key_frames.append({
                            "path": str(img_path.name),
                            "data": data,
                            "frame_number": int(img_path.stem) if img_path.stem.isdigit() else 0,
                        })
                    except Exception:
                        pass
        
        return key_frames
    
    async def _generate_diagnosis(self, session_data: Dict, key_frames: List[Dict]) -> Diagnosis:
        """Use Claude to diagnose the session."""
        client = self._get_client()
        
        # Build prompt
        prompt = self._build_diagnosis_prompt(session_data)
        
        # Build message with images
        content = [{"type": "text", "text": prompt}]
        
        for frame in key_frames[:5]:  # Limit to 5 images
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": frame["data"],
                }
            })
        
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": content}],
            )
            
            # Parse response
            return self._parse_diagnosis_response(response.content[0].text)
            
        except Exception as e:
            # Return default diagnosis on error
            return Diagnosis(
                bug_type="unknown",
                root_cause=f"Analysis failed: {str(e)}",
                explanation="Unable to analyze session with AI.",
                recommended_actions=["Review session manually"],
            )
    
    def _build_diagnosis_prompt(self, session_data: Dict) -> str:
        """Build the diagnosis prompt for Claude."""
        intent = session_data.get("intent", "Unknown")
        outcome = session_data.get("outcome", "Unknown")
        duration = session_data.get("duration_ms", 0)
        
        # Get unified timeline events (new format) or fall back to old format
        events = session_data.get("events", [])
        console_errors = session_data.get("console_errors", [])
        final_signals = session_data.get("final_signals", {})
        selected_element = session_data.get("selected_element")
        
        # Fallback to old format if no timeline events
        notes = session_data.get("notes", [])
        key_events = session_data.get("key_events", [])
        
        prompt = f"""You are analyzing a PyNext debug session. PyNext is a Python web framework with SolidJS-style reactivity.

## Session Information
- **Intent**: {intent}
- **Outcome**: {outcome}
- **Duration**: {duration}ms
- **Timeline Events**: {len(events)}
- **Console Errors**: {len(console_errors)}
"""
        
        # Add selected element if available
        if selected_element:
            prompt += f"\n## Selected Element (via Inspect Mode)\n"
            prompt += f"- Selector: `{selected_element.get('selector', 'unknown')}`\n"
            prompt += f"- Tag: {selected_element.get('tagName', 'unknown')}\n"
            if selected_element.get('source'):
                prompt += f"- Source: `{selected_element.get('source')}`\n"
            prompt += f"- Hydrated: {selected_element.get('hydrated', False)}\n"
            prompt += f"- Handlers: {selected_element.get('handlers', {})}\n"
        
        # Use unified timeline if available
        if events:
            prompt += "\n## Timeline (Chronological - All Events)\n"
            prompt += "This is a unified timeline of all events during the session:\n\n"
            
            for event in events[:50]:  # Limit to 50 events
                ts = event.get("ts", 0)
                etype = event.get("type", "unknown")
                data = event.get("data", {})
                screenshot = event.get("screenshot", "")
                
                if etype == "click":
                    signals_changed = data.get("signals_changed", [])
                    signals_str = ", ".join([s.get("name", s.get("id", "?")) for s in signals_changed]) if signals_changed else "none"
                    prompt += f"- [{ts}ms] **CLICK** on `{data.get('selector', 'unknown')}` → signals changed: [{signals_str}]\n"
                elif etype == "note":
                    prompt += f"- [{ts}ms] **USER NOTE**: \"{data.get('text', '')}\"\n"
                elif etype == "error":
                    msg = data.get("message", "")[:100]
                    prompt += f"- [{ts}ms] **ERROR**: `{msg}`\n"
                elif etype == "inspect":
                    source = data.get("source", "unknown")
                    prompt += f"- [{ts}ms] **INSPECTED**: `{data.get('selector', 'unknown')}` (source: `{source}`)\n"
                elif etype == "signal":
                    prompt += f"- [{ts}ms] **SIGNAL CHANGE**: `{data.get('signal_name')}` = {data.get('new_value')}\n"
                elif etype == "snapshot":
                    prompt += f"- [{ts}ms] **SNAPSHOT**: {data.get('note', 'manual')}\n"
                elif etype == "session_start":
                    prompt += f"- [{ts}ms] **SESSION START**: {data.get('intent', intent)}\n"
                elif etype == "session_end":
                    prompt += f"- [{ts}ms] **SESSION END**: {data.get('outcome', outcome)}\n"
                else:
                    prompt += f"- [{ts}ms] {etype}: {str(data)[:80]}\n"
        else:
            # Fallback to old format
            prompt += "\n## User Notes\n"
            for note in notes:
                prompt += f"- [{note.get('ts', 0)}ms] {note.get('text', '')}\n"
            
            prompt += "\n## Key Events\n"
            for event in key_events[:20]:
                prompt += f"- [{event.get('ts', 0)}ms] {event.get('event', '')} "
                if event.get('target'):
                    prompt += f"on {event['target']} "
                if event.get('result'):
                    prompt += f"-> {event['result']}"
                prompt += "\n"
        
        # Add console errors section
        if console_errors:
            prompt += "\n## Console Errors\n"
            for err in console_errors[:10]:
                prompt += f"- [{err.get('ts', 0)}ms] {err.get('message', '')[:150]}\n"
                if err.get('stack'):
                    prompt += f"  Stack: {err.get('stack', '')[:200]}\n"
        
        prompt += """
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
"""
        return prompt
    
    def _parse_diagnosis_response(self, response_text: str) -> Diagnosis:
        """Parse Claude's diagnosis response."""
        # Extract JSON from response
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        
        if json_match:
            try:
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
            except json.JSONDecodeError:
                pass
        
        # Fallback: extract from plain text
        return Diagnosis(
            bug_type="unknown",
            root_cause=response_text[:500],
            explanation=response_text,
            recommended_actions=["Review manually"],
        )
    
    async def _generate_narrations(self, session_data: Dict, key_frames: List[Dict]) -> List[FrameNarration]:
        """Generate AI narrations for each key frame."""
        narrations = []
        
        client = self._get_client()
        
        for i, frame in enumerate(key_frames[:10]):
            prompt = f"""Describe what you see in this screenshot from a PyNext debug session.
This is frame {frame.get('frame_number', i+1)}.
Context: User intent was "{session_data.get('intent', 'unknown')}"

Provide a brief, factual description (1-2 sentences) of the UI state."""
            
            try:
                response = client.messages.create(
                    model=self.model,
                    max_tokens=200,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": frame["data"],
                                }
                            }
                        ]
                    }]
                )
                
                narration_text = response.content[0].text
            except Exception:
                narration_text = f"Frame {frame.get('frame_number', i+1)} - analysis unavailable"
            
            narrations.append(FrameNarration(
                frame_number=frame.get("frame_number", i+1),
                timestamp_ms=0,
                screenshot_path=frame.get("path", ""),
                narration=narration_text,
                is_key_frame=True,
            ))
        
        return narrations
    
    def _extract_key_insights(self, session_data: Dict, diagnosis: Optional[Diagnosis]) -> List[str]:
        """Extract key insights from the session."""
        insights = []
        
        # Check for common patterns
        key_events = session_data.get("key_events", [])
        
        for event in key_events:
            if event.get("result") == "NO_CHANGE":
                insights.append(f"Action at {event.get('ts', 0)}ms had no effect")
            if event.get("event") == "note":
                insights.append(f"User noted: {event.get('text', '')}")
        
        if diagnosis:
            insights.append(f"Root cause: {diagnosis.root_cause}")
        
        return insights[:10]  # Limit to 10
    
    def _generate_briefing(self, session_path: Path, session_data: Dict, result: AnalysisResult) -> Path:
        """Generate the AI briefing markdown file."""
        briefing_path = session_path / "briefing.md"
        
        content = f"""# Debug Session Briefing

## For: Cursor AI Assistant
## Session: {result.session_id}
## Generated: {datetime.now().isoformat()}

---

## Quick Summary

**Intent:** {session_data.get('intent', 'Unknown')}
**Outcome:** {session_data.get('outcome', 'Unknown')}
**Duration:** {session_data.get('duration_ms', 0)}ms

"""
        
        if result.diagnosis:
            d = result.diagnosis
            content += f"""## Diagnosis

**Bug Type:** {d.bug_type}
**Root Cause:** {d.root_cause}
**Severity:** {d.severity}
**Confidence:** {d.confidence:.0%}

{d.explanation}

"""
            if d.source_file:
                content += f"**Source:** `{d.source_file}`"
                if d.source_line:
                    content += f" line {d.source_line}"
                content += "\n\n"
            
            if d.recommended_actions:
                content += "## Recommended Actions\n\n"
                for i, action in enumerate(d.recommended_actions, 1):
                    content += f"{i}. {action}\n"
                content += "\n"
        
        # User observations - extract notes from timeline if available
        events = session_data.get("events", [])
        notes = session_data.get("notes", [])
        
        # Extract notes from timeline events
        if events:
            timeline_notes = [e for e in events if e.get("type") == "note"]
            if timeline_notes:
                content += "## User Observations\n\n"
                for e in timeline_notes:
                    content += f"- [{e.get('ts', 0)}ms] {e.get('data', {}).get('text', '')}\n"
                content += "\n"
        elif notes:
            content += "## User Observations\n\n"
            for note in notes:
                content += f"- [{note.get('ts', 0)}ms] {note.get('text', '')}\n"
            content += "\n"
        
        # Timeline - use unified events if available
        if events:
            content += "## Timeline (Unified)\n\n"
            # Show key event types: click, note, error, inspect
            key_event_types = {"click", "note", "error", "inspect", "signal", "session_start", "session_end"}
            key_timeline = [e for e in events if e.get("type") in key_event_types][:20]
            
            for event in key_timeline:
                ts = event.get("ts", 0)
                etype = event.get("type", "unknown")
                data = event.get("data", {})
                
                if etype == "click":
                    content += f"- [{ts}ms] CLICK on `{data.get('selector', 'unknown')}`\n"
                elif etype == "note":
                    content += f"- [{ts}ms] NOTE: {data.get('text', '')}\n"
                elif etype == "error":
                    content += f"- [{ts}ms] ERROR: {data.get('message', '')[:80]}\n"
                elif etype == "inspect":
                    content += f"- [{ts}ms] INSPECT: `{data.get('selector', 'unknown')}`\n"
                elif etype == "signal":
                    content += f"- [{ts}ms] SIGNAL: `{data.get('signal_name')}` = {data.get('new_value')}\n"
                else:
                    content += f"- [{ts}ms] {etype}\n"
            content += "\n"
        else:
            # Fallback to old format
            key_events = session_data.get("key_events", [])
            if key_events:
                content += "## Timeline\n\n"
                for event in key_events[:15]:
                    content += f"- [{event.get('ts', 0)}ms] {event.get('event', '')} "
                    if event.get('target'):
                        content += f"on `{event['target']}`"
                    if event.get('result'):
                        content += f" → {event['result']}"
                    content += "\n"
                content += "\n"
        
        # Console errors
        console_errors = session_data.get("console_errors", [])
        if console_errors:
            content += "## Console Errors\n\n"
            for err in console_errors[:5]:
                content += f"- [{err.get('ts', 0)}ms] `{err.get('message', '')[:100]}`\n"
            content += "\n"
        
        # Files to investigate
        content += """## Files to Investigate

Based on the diagnosis, check these files:
"""
        if result.diagnosis and result.diagnosis.source_file:
            content += f"- `{result.diagnosis.source_file}` - Primary source of bug\n"
        content += """- `pynext/runtime/signals.js` - Client-side hydration
- `pynext/server/hydration.py` - Server-side state serialization
- `pynext/core/html.py` - HTML rendering

## Related Files

See `storyboard.png` for visual timeline.
Key frames are in `key_frames/` directory.
"""
        
        with open(briefing_path, "w") as f:
            f.write(content)
        
        return briefing_path
    
    def _generate_basic_briefing(self, session_path: Path, session_data: Dict, error: str) -> Path:
        """Generate basic briefing without AI analysis."""
        briefing_path = session_path / "briefing.md"
        
        content = f"""# Debug Session Briefing

## Session: {session_data.get('session_id', 'unknown')}
## Generated: {datetime.now().isoformat()}

**Note:** AI analysis unavailable: {error}

---

## Session Summary

**Intent:** {session_data.get('intent', 'Unknown')}
**Outcome:** {session_data.get('outcome', 'Unknown')}
**Duration:** {session_data.get('duration_ms', 0)}ms
**Actions:** {session_data.get('action_count', 0)}
**Frames:** {session_data.get('frame_count', 0)}

## User Notes
"""
        for note in session_data.get("notes", []):
            content += f"- [{note.get('ts', 0)}ms] {note.get('text', '')}\n"
        
        content += "\n## Key Events\n"
        for event in session_data.get("key_events", [])[:20]:
            content += f"- [{event.get('ts', 0)}ms] {event.get('event', '')}\n"
        
        with open(briefing_path, "w") as f:
            f.write(content)
        
        return briefing_path
    
    def _generate_narration_file(self, session_path: Path, result: AnalysisResult) -> Path:
        """Generate narration.json file."""
        narration_path = session_path / "narration.json"
        
        data = {
            "session_id": result.session_id,
            "frame_count": len(result.frame_narrations),
            "frames": [
                {
                    "frame_number": n.frame_number,
                    "timestamp_ms": n.timestamp_ms,
                    "screenshot": n.screenshot_path,
                    "narration": n.narration,
                    "observations": n.observations,
                    "is_key_frame": n.is_key_frame,
                }
                for n in result.frame_narrations
            ]
        }
        
        with open(narration_path, "w") as f:
            json.dump(data, f, indent=2)
        
        return narration_path
    
    def _generate_instructions(self, session_path: Path, session_data: Dict) -> Path:
        """Generate instructions.md meta-prompt."""
        instructions_path = session_path / "instructions.md"
        
        content = """# How to Read This Debug Session

You are receiving a PyNext debug session. Here's how to interpret it:

## File Structure

```
session/
├── briefing.md          # START HERE - AI-generated summary
├── summary.json         # Raw session data
├── narration.json       # AI explanation per frame
├── instructions.md      # This file
├── user_notes.json      # User commentary
├── annotations.json     # User drawings (coordinates)
├── storyboard.png       # Key frames composite (if generated)
├── key_frames/          # Important screenshots
├── annotated_frames/    # Screenshots with user drawings
└── all_frames/          # Every captured frame
```

## Reading Order

1. **Read `briefing.md` first** - Contains diagnosis and recommended actions
2. **Look at `storyboard.png`** - Visual timeline of key moments
3. **Check `narration.json`** - Frame-by-frame AI descriptions
4. **Review `user_notes.json`** - What the user observed
5. **Examine specific frames** - In `key_frames/` or `all_frames/`

## Key Patterns to Look For

| Pattern | Meaning |
|---------|---------|
| `result: "NO_CHANGE"` | Action had no effect - bug evidence |
| `handlers: {oninput: false}` | Event handler not attached - hydration bug |
| `hydrated: false` | Element not properly hydrated |
| `pixelsDifferent: 0` | Screenshot unchanged - nothing happened |

## Common Issues

### Form inputs not working
- Check `hydrateFormBindings()` in `signals.js`
- Verify `data-pynext-bind` attribute is set
- Check if `oninput` handler is attached

### Show component not toggling
- Check `hydrateBindings()` for show type
- Verify signal ID mapping
- Check initial condition value

### Signal not updating
- Verify signal exists in `__pynext__.signals`
- Check if `set()` method is being called
- Look for errors in console

## PyNext-Specific Context

PyNext uses SolidJS-style fine-grained reactivity:
- Signals: `Signal` class with `read()`, `set()`, `update()`
- Effects: Auto-run when dependencies change
- Hydration: Server renders HTML, client attaches handlers

Files to check for bugs:
- `pynext/runtime/signals.js` - Client-side reactive runtime
- `pynext/server/hydration.py` - Hydration data serialization
- `pynext/core/html.py` - Server-side HTML rendering
"""
        
        with open(instructions_path, "w") as f:
            f.write(content)
        
        return instructions_path
    
    def _generate_storyboard(self, session_path: Path, session_data: Dict, key_frames: List[Dict]) -> Optional[Path]:
        """Generate composite storyboard image."""
        if not key_frames:
            return None
        
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            # PIL not available, skip storyboard
            return None
        
        storyboard_path = session_path / "storyboard.png"
        
        # Settings
        thumb_width = 400
        thumb_height = 300
        padding = 20
        cols = min(len(key_frames), 4)
        rows = (len(key_frames) + cols - 1) // cols
        
        # Create canvas
        canvas_width = (thumb_width + padding) * cols + padding
        canvas_height = (thumb_height + padding + 40) * rows + padding + 60  # +40 for labels, +60 for header
        
        canvas = Image.new("RGB", (canvas_width, canvas_height), color="#f8f9fa")
        draw = ImageDraw.Draw(canvas)
        
        # Header
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        except Exception:
            font = ImageFont.load_default()
            small_font = font
        
        draw.text((padding, padding), f"Session: {session_data.get('session_id', 'unknown')}", fill="#333", font=font)
        draw.text((padding, padding + 30), f"Intent: {session_data.get('intent', '')}", fill="#666", font=small_font)
        
        # Draw frames
        for i, frame in enumerate(key_frames):
            row = i // cols
            col = i % cols
            
            x = padding + col * (thumb_width + padding)
            y = 60 + padding + row * (thumb_height + padding + 40)
            
            # Load and resize image
            try:
                img_data = base64.b64decode(frame["data"])
                from io import BytesIO
                img = Image.open(BytesIO(img_data))
                img.thumbnail((thumb_width, thumb_height))
                
                # Paste onto canvas
                canvas.paste(img, (x, y))
                
                # Add border
                draw.rectangle([x-1, y-1, x+thumb_width+1, y+thumb_height+1], outline="#ddd", width=1)
                
                # Add label
                label = f"Frame {frame.get('frame_number', i+1)}"
                draw.text((x, y + thumb_height + 5), label, fill="#333", font=small_font)
                
            except Exception:
                # Draw placeholder
                draw.rectangle([x, y, x+thumb_width, y+thumb_height], fill="#eee", outline="#ddd")
                draw.text((x+10, y+10), f"Frame {i+1}", fill="#999", font=small_font)
        
        # Save
        canvas.save(storyboard_path)
        
        return storyboard_path


async def process_session(session_path: str, api_key: Optional[str] = None) -> AnalysisResult:
    """
    Convenience function to process a debug session.
    
    Args:
        session_path: Path to session directory
        api_key: Anthropic API key (optional, uses env var)
    
    Returns:
        AnalysisResult with generated files
    """
    processor = SessionProcessor(api_key=api_key)
    return await processor.analyze_session(Path(session_path))

