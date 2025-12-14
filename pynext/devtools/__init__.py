"""
PyNext AI DevTools - Native AI Debugging Support.

This module provides real-time browser state capture for AI-assisted debugging.
When enabled with `pynext dev --ai-debug`, it:

1. Launches Chrome with CDP (Chrome DevTools Protocol) enabled
2. Captures all browser events (console, clicks, network, signals)
3. Takes screenshots on every interaction
4. Streams everything to .pynext/debug/ for AI consumption
5. Provides surgical recording sessions for precise debugging

Why This Matters:
    Traditional debugging requires context switching between code and browser.
    AI assistants can't see what's happening in the browser. This module
    bridges that gap by capturing the complete browser state - both events
    AND visuals - so AI can debug issues as effectively as a human.

Debug Modes:
    --ai-debug=app         For app developers debugging their application
    --ai-debug=core        For PyNext developers debugging the framework
    --ai-debug=everything  Full diagnostic capture for complex bugs

Session API (in browser console):
    pynext_debug.session_start("intent")   Start recording session
    pynext_debug.inspect()                 Select element visually
    pynext_debug.note("text")              Add commentary
    pynext_debug.draw()                    Enable drawing annotations
    pynext_debug.session_end("outcome")    End session with analysis

Output Structure:
    .pynext/debug/
    ├── events.jsonl          # All events, append-only
    ├── state.json            # Current state summary
    ├── screenshots/          # Screenshot captures
    ├── snapshots/            # DOM HTML snapshots
    └── sessions/             # Recording sessions
        └── rec_xxx/
            ├── summary.json
            ├── briefing.md   # AI-generated diagnosis
            ├── narration.json
            ├── storyboard.png
            ├── key_frames/
            └── all_frames/

Architecture:
    CDPBridge      - WebSocket connection to Chrome DevTools Protocol
    ChromeLauncher - Finds and launches Chrome with debugging enabled
    EventCapture   - Filters and enriches browser events
    ScreenshotCapture - Takes screenshots with element annotations
    DebugStream    - Writes events to JSONL files
    JSInjector     - Injects PyNext-aware tracking code
    SessionRecorder - Manages surgical recording sessions
    SessionProcessor - AI analysis with Claude 4.5 Opus
    AIDebugger     - Orchestrates all components
"""

from pynext.devtools.bridge import CDPBridge
from pynext.devtools.launcher import ChromeLauncher
from pynext.devtools.capture import EventCapture, DebugEvent
from pynext.devtools.screenshot import ScreenshotCapture
from pynext.devtools.stream import DebugStream
from pynext.devtools.injector import JSInjector
from pynext.devtools.debugger import AIDebugger, DebugConfig, DebugMode
from pynext.devtools.recorder import SessionRecorder, RecordingSession, RecordedAction
from pynext.devtools.processor import SessionProcessor, AnalysisResult, Diagnosis

__all__ = [
    # Core components
    "CDPBridge",
    "ChromeLauncher",
    "EventCapture",
    "DebugEvent",
    "ScreenshotCapture",
    "DebugStream",
    "JSInjector",
    # Session management
    "SessionRecorder",
    "RecordingSession", 
    "RecordedAction",
    # AI analysis
    "SessionProcessor",
    "AnalysisResult",
    "Diagnosis",
    # Configuration
    "DebugConfig",
    "DebugMode",
    # Main orchestrator
    "AIDebugger",
]

