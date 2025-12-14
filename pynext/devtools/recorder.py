"""
Session Recorder - Manages surgical debug recording sessions.

This module handles user-initiated recording sessions that capture:
- Element selection via inspect mode
- User intent and notes
- Drawing annotations
- Screenshots (time-based and action-based)
- DOM mutations
- Signal state snapshots

Usage:
    recorder = SessionRecorder(output_dir)
    
    # Start a session
    session = recorder.start_session("Testing form input")
    
    # Record actions
    session.record_click(element_info, before_screenshot, after_screenshot)
    session.record_keypress(key, target_info, value_changed)
    session.add_note("Input not responding")
    session.add_drawing(annotation_data)
    
    # End session
    result = recorder.end_session("Form inputs broken")
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ActionType(Enum):
    """Types of user actions captured during recording."""
    CLICK = "click"
    KEYPRESS = "keypress"
    FOCUS = "focus"
    BLUR = "blur"
    INPUT = "input"
    SCROLL = "scroll"
    MOUSE_MOVE = "mouse_move"
    NOTE = "note"
    DRAWING = "drawing"
    SNAPSHOT = "snapshot"
    ELEMENT_SELECT = "element_select"


@dataclass
class TimelineEvent:
    """
    Single unified event in the timeline.
    
    This is the core data structure for the unified timeline. Every event
    (screenshot, click, note, error, signal change, inspect) goes into
    one chronological array using this structure.
    
    Attributes:
        seq: Sequential number (1-indexed)
        ts: Timestamp in milliseconds relative to session start
        type: Event type string (frame, click, note, error, inspect, signal, etc.)
        data: Event-specific payload dictionary
        screenshot: Associated screenshot path (relative to session dir)
    """
    seq: int
    ts: int
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    screenshot: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "seq": self.seq,
            "ts": self.ts,
            "type": self.type,
            "data": self.data,
        }
        if self.screenshot:
            result["screenshot"] = self.screenshot
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TimelineEvent":
        """Create from dictionary."""
        return cls(
            seq=data["seq"],
            ts=data["ts"],
            type=data["type"],
            data=data.get("data", {}),
            screenshot=data.get("screenshot"),
        )


@dataclass
class ElementInfo:
    """Information about a DOM element."""
    selector: str
    tag_name: str
    id: Optional[str] = None
    class_name: Optional[str] = None
    text_content: Optional[str] = None
    value: Optional[str] = None
    
    # PyNext-specific attributes
    pynext_component: Optional[str] = None
    pynext_source: Optional[str] = None
    pynext_bind: Optional[str] = None
    
    # Handler attachment status
    handlers: Dict[str, bool] = field(default_factory=dict)
    
    # Computed styles (relevant ones)
    computed: Dict[str, str] = field(default_factory=dict)
    
    # Hydration status
    hydrated: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ElementAncestry:
    """Element's parent chain with PyNext component info."""
    ancestors: List[Dict[str, Any]] = field(default_factory=list)
    nearest_pynext_component: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SignalSnapshot:
    """Snapshot of signal state before/after an action."""
    signals_before: Dict[str, Any] = field(default_factory=dict)
    signals_after: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def signals_that_changed(self) -> List[str]:
        """Get list of signal IDs that changed."""
        changed = []
        for sig_id in self.signals_before:
            if sig_id in self.signals_after:
                if self.signals_before[sig_id] != self.signals_after[sig_id]:
                    changed.append(sig_id)
        return changed
    
    def to_dict(self) -> Dict:
        return {
            "signalsBefore": self.signals_before,
            "signalsAfter": self.signals_after,
            "signalsThatChanged": self.signals_that_changed,
        }


@dataclass
class DOMSnapshot:
    """DOM mutations captured during an action."""
    mutations: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def mutation_count(self) -> int:
        return len(self.mutations)
    
    def to_dict(self) -> Dict:
        return {"mutations": self.mutations, "count": self.mutation_count}


@dataclass 
class FormState:
    """State of a form at a point in time."""
    form_id: str
    is_valid: bool = False
    is_dirty: bool = False
    is_submitting: bool = False
    fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DrawingAnnotation:
    """A user drawing annotation."""
    type: str  # circle, arrow, text, freehand
    color: str = "red"
    position: Optional[Dict[str, int]] = None
    target: Optional[Dict[str, Any]] = None
    from_pos: Optional[Dict[str, int]] = None
    to_pos: Optional[Dict[str, int]] = None
    text: Optional[str] = None
    points: Optional[List[Dict[str, int]]] = None
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class RecordedAction:
    """A single recorded user action with full context."""
    timestamp_ms: int
    action_type: ActionType
    frame_number: int
    
    # Element context
    target: Optional[ElementInfo] = None
    ancestry: Optional[ElementAncestry] = None
    
    # Action-specific data
    key: Optional[str] = None  # For keypress
    position: Optional[Dict[str, int]] = None  # For click/mouse
    text: Optional[str] = None  # For note
    
    # State snapshots
    signals: Optional[SignalSnapshot] = None
    dom_changes: Optional[DOMSnapshot] = None
    form_state: Optional[FormState] = None
    
    # Screenshots
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    
    # Results
    value_before: Optional[str] = None
    value_after: Optional[str] = None
    result: Optional[str] = None  # "CHANGED", "NO_CHANGE", "ERROR"
    
    # Error if any
    error: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict:
        data = {
            "ts": self.timestamp_ms,
            "type": self.action_type.value,
            "frame": self.frame_number,
        }
        
        if self.target:
            data["target"] = self.target.to_dict()
        if self.ancestry:
            data["ancestry"] = self.ancestry.to_dict()
        if self.key:
            data["key"] = self.key
        if self.position:
            data["position"] = self.position
        if self.text:
            data["text"] = self.text
        if self.signals:
            data["signals"] = self.signals.to_dict()
        if self.dom_changes:
            data["domChanges"] = self.dom_changes.to_dict()
        if self.form_state:
            data["formState"] = self.form_state.to_dict()
        if self.screenshot_before:
            data["screenshotBefore"] = self.screenshot_before
        if self.screenshot_after:
            data["screenshotAfter"] = self.screenshot_after
        if self.value_before is not None:
            data["valueBefore"] = self.value_before
        if self.value_after is not None:
            data["valueAfter"] = self.value_after
        if self.result:
            data["result"] = self.result
        if self.error:
            data["error"] = self.error
            
        return data


@dataclass
class RecordingSession:
    """A complete recording session with all captured data."""
    session_id: str
    intent: str
    start_time: float
    mode: str = "app"
    
    # Session state
    outcome: Optional[str] = None
    end_time: Optional[float] = None
    
    # Selected element (from inspect mode)
    selected_element: Optional[ElementInfo] = None
    
    # Recorded data
    actions: List[RecordedAction] = field(default_factory=list)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    drawings: List[DrawingAnnotation] = field(default_factory=list)
    
    # UNIFIED TIMELINE - Single source of truth for all events
    timeline: List[TimelineEvent] = field(default_factory=list)
    console_errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Frame tracking
    frame_count: int = 0
    key_frames: List[int] = field(default_factory=list)
    
    # Hydration map (captured at start)
    hydration_map: Optional[Dict[str, Any]] = None
    
    @property
    def duration_ms(self) -> int:
        """Duration in milliseconds."""
        if self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return int((time.time() - self.start_time) * 1000)
    
    @property
    def action_count(self) -> int:
        return len(self.actions)
    
    @property
    def timeline_count(self) -> int:
        """Number of events in the timeline."""
        return len(self.timeline)
    
    def append_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        screenshot: Optional[str] = None,
    ) -> TimelineEvent:
        """
        Append any event to the unified timeline.
        
        This is the primary method for recording events. All event types
        (frames, clicks, notes, errors, inspects, signal changes) should
        use this method to ensure they appear in the chronological timeline.
        
        Args:
            event_type: Type of event (frame, click, note, error, inspect, signal, etc.)
            data: Event-specific payload
            screenshot: Path to associated screenshot (relative to session dir)
        
        Returns:
            The created TimelineEvent
        """
        event = TimelineEvent(
            seq=len(self.timeline) + 1,
            ts=int((time.time() - self.start_time) * 1000),
            type=event_type,
            data=data,
            screenshot=screenshot,
        )
        self.timeline.append(event)
        return event
    
    def add_action(self, action: RecordedAction) -> None:
        """Add a recorded action."""
        self.actions.append(action)
        self.frame_count = max(self.frame_count, action.frame_number)
    
    def add_note(self, text: str, timestamp_ms: Optional[int] = None) -> None:
        """Add a user note."""
        ts = timestamp_ms or int((time.time() - self.start_time) * 1000)
        self.notes.append({
            "ts": ts,
            "text": text,
            "frame": self.frame_count,
            "source": "user",
        })
    
    def add_drawing(self, drawing: DrawingAnnotation, timestamp_ms: Optional[int] = None) -> None:
        """Add a user drawing."""
        ts = timestamp_ms or int((time.time() - self.start_time) * 1000)
        drawing_dict = drawing.to_dict()
        drawing_dict["ts"] = ts
        drawing_dict["frame"] = self.frame_count
        self.drawings.append(drawing)
    
    def mark_key_frame(self, frame_number: int) -> None:
        """Mark a frame as a key frame (visual change occurred)."""
        if frame_number not in self.key_frames:
            self.key_frames.append(frame_number)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "intent": self.intent,
            "outcome": self.outcome,
            "mode": self.mode,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "frame_count": self.frame_count,
            "action_count": self.action_count,
            "timeline_count": self.timeline_count,
            "key_frames": self.key_frames,
            "selected_element": self.selected_element.to_dict() if self.selected_element else None,
            "hydration_map": self.hydration_map,
        }
    
    def to_summary(self) -> Dict:
        """Get a summary for the AI briefing."""
        return {
            "session_id": self.session_id,
            "intent": self.intent,
            "outcome": self.outcome,
            "duration_ms": self.duration_ms,
            "action_count": self.action_count,
            "note_count": len(self.notes),
            "drawing_count": len(self.drawings),
            "key_frame_count": len(self.key_frames),
        }


class SessionRecorder:
    """
    Manages recording sessions for surgical debugging.
    
    This class handles:
    - Session lifecycle (start, end)
    - Action recording with full context
    - Screenshot management
    - Output file generation
    """
    
    def __init__(self, output_dir: Path, mode: str = "app"):
        """
        Initialize the session recorder.
        
        Args:
            output_dir: Base output directory
            mode: Debug mode (app/core/everything)
        """
        self.output_dir = Path(output_dir)
        self.mode = mode
        self._current_session: Optional[RecordingSession] = None
        self._session_dir: Optional[Path] = None
        self._on_action_callbacks: List[Callable] = []
    
    @property
    def is_recording(self) -> bool:
        """Check if a session is currently active."""
        return self._current_session is not None
    
    @property
    def current_session(self) -> Optional[RecordingSession]:
        """Get the current recording session."""
        return self._current_session
    
    def on_action(self, callback: Callable[[RecordedAction], None]) -> None:
        """Register a callback for new actions."""
        self._on_action_callbacks.append(callback)
    
    def start_session(self, intent: str) -> RecordingSession:
        """
        Start a new recording session.
        
        Args:
            intent: User's stated intent for this session
        
        Returns:
            The new RecordingSession
        """
        if self._current_session:
            # Auto-end previous session
            self.end_session("Ended by new session")
        
        # Generate session ID
        session_id = f"rec_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Create session directory
        sessions_dir = self.output_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self._session_dir = sessions_dir / session_id
        self._session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self._session_dir / "all_frames").mkdir(exist_ok=True)
        (self._session_dir / "key_frames").mkdir(exist_ok=True)
        (self._session_dir / "annotated_frames").mkdir(exist_ok=True)
        
        # Create session
        self._current_session = RecordingSession(
            session_id=session_id,
            intent=intent,
            start_time=time.time(),
            mode=self.mode,
        )
        
        return self._current_session
    
    def end_session(self, outcome: str) -> Optional[Path]:
        """
        End the current recording session.
        
        Args:
            outcome: User's description of what happened
        
        Returns:
            Path to the session directory
        """
        if not self._current_session:
            return None
        
        self._current_session.outcome = outcome
        self._current_session.end_time = time.time()
        
        # Save session files
        self._save_session_files()
        
        session_dir = self._session_dir
        self._current_session = None
        self._session_dir = None
        
        return session_dir
    
    def record_action(self, action: RecordedAction) -> None:
        """
        Record a user action.
        
        Args:
            action: The action to record
        """
        if not self._current_session:
            return
        
        self._current_session.add_action(action)
        
        # Notify callbacks
        for callback in self._on_action_callbacks:
            try:
                callback(action)
            except Exception:
                pass
        
        # Write to actions.jsonl incrementally
        if self._session_dir:
            actions_file = self._session_dir / "actions.jsonl"
            with open(actions_file, "a") as f:
                f.write(json.dumps(action.to_dict()) + "\n")
    
    def record_click(
        self,
        element: ElementInfo,
        position: Dict[str, int],
        signals: SignalSnapshot,
        dom_changes: DOMSnapshot,
        screenshot_before: Optional[str] = None,
        screenshot_after: Optional[str] = None,
        frame_number: int = 0,
    ) -> RecordedAction:
        """Record a click action with full context."""
        action = RecordedAction(
            timestamp_ms=self._get_timestamp_ms(),
            action_type=ActionType.CLICK,
            frame_number=frame_number,
            target=element,
            position=position,
            signals=signals,
            dom_changes=dom_changes,
            screenshot_before=screenshot_before,
            screenshot_after=screenshot_after,
        )
        self.record_action(action)
        return action
    
    def record_keypress(
        self,
        key: str,
        element: ElementInfo,
        value_before: str,
        value_after: str,
        signals: SignalSnapshot,
        dom_changes: DOMSnapshot,
        frame_number: int = 0,
    ) -> RecordedAction:
        """Record a keypress action."""
        result = "CHANGED" if value_before != value_after else "NO_CHANGE"
        
        action = RecordedAction(
            timestamp_ms=self._get_timestamp_ms(),
            action_type=ActionType.KEYPRESS,
            frame_number=frame_number,
            target=element,
            key=key,
            signals=signals,
            dom_changes=dom_changes,
            value_before=value_before,
            value_after=value_after,
            result=result,
        )
        self.record_action(action)
        return action
    
    def add_note(self, text: str) -> None:
        """Add a user note to the session."""
        if self._current_session:
            self._current_session.add_note(text)
            
            # Save to user_notes.json
            if self._session_dir:
                notes_file = self._session_dir / "user_notes.json"
                notes_data = {"notes": self._current_session.notes}
                with open(notes_file, "w") as f:
                    json.dump(notes_data, f, indent=2)
    
    def add_drawing(self, drawing: DrawingAnnotation) -> None:
        """Add a user drawing to the session."""
        if self._current_session:
            self._current_session.add_drawing(drawing)
            
            # Save to annotations.json
            if self._session_dir:
                annotations_file = self._session_dir / "annotations.json"
                annotations_data = {
                    "drawings": [d.to_dict() for d in self._current_session.drawings]
                }
                with open(annotations_file, "w") as f:
                    json.dump(annotations_data, f, indent=2)
    
    def set_selected_element(self, element: ElementInfo) -> None:
        """Set the element selected via inspect mode."""
        if self._current_session:
            self._current_session.selected_element = element
    
    def set_hydration_map(self, hydration_map: Dict[str, Any]) -> None:
        """Set the hydration status map."""
        if self._current_session:
            self._current_session.hydration_map = hydration_map
    
    def save_screenshot(
        self,
        data: bytes,
        frame_type: str = "all",
        frame_number: Optional[int] = None,
    ) -> Optional[str]:
        """
        Save a screenshot to the session.
        
        Args:
            data: PNG image data
            frame_type: "all", "key", or "annotated"
            frame_number: Frame number (auto-incremented if not provided)
        
        Returns:
            Relative path to the saved file
        """
        if not self._session_dir:
            return None
        
        if frame_number is None and self._current_session:
            self._current_session.frame_count += 1
            frame_number = self._current_session.frame_count
        
        subdir = {
            "all": "all_frames",
            "key": "key_frames",
            "annotated": "annotated_frames",
        }.get(frame_type, "all_frames")
        
        filename = f"{frame_number:04d}.png"
        filepath = self._session_dir / subdir / filename
        
        with open(filepath, "wb") as f:
            f.write(data)
        
        return f"{subdir}/{filename}"
    
    def _get_timestamp_ms(self) -> int:
        """Get timestamp relative to session start."""
        if self._current_session:
            return int((time.time() - self._current_session.start_time) * 1000)
        return 0
    
    def _save_session_files(self) -> None:
        """Save all session files on end."""
        if not self._current_session or not self._session_dir:
            return
        
        session = self._current_session
        
        # Save timeline.json (PRIMARY OUTPUT - Single source of truth)
        timeline_data = {
            "session_id": session.session_id,
            "intent": session.intent,
            "outcome": session.outcome,
            "mode": session.mode,
            "duration_ms": session.duration_ms,
            "frame_count": session.frame_count,
            "events": [e.to_dict() for e in session.timeline],
            "console_errors": session.console_errors,
            "final_signals": session.hydration_map.get("signals", {}) if session.hydration_map else {},
            "selected_element": session.selected_element.to_dict() if session.selected_element else None,
        }
        with open(self._session_dir / "timeline.json", "w") as f:
            json.dump(timeline_data, f, indent=2)
        
        # Save summary.json (for backwards compatibility)
        summary = {
            **session.to_dict(),
            "notes": session.notes,
            "key_events": self._extract_key_events(),
        }
        with open(self._session_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        # Save user_notes.json
        with open(self._session_dir / "user_notes.json", "w") as f:
            json.dump({"notes": session.notes}, f, indent=2)
        
        # Save annotations.json
        with open(self._session_dir / "annotations.json", "w") as f:
            json.dump({
                "drawings": [d.to_dict() for d in session.drawings]
            }, f, indent=2)
    
    def _extract_key_events(self) -> List[Dict]:
        """Extract key events for the summary."""
        if not self._current_session:
            return []
        
        key_events = [
            {"ts": 0, "frame": 1, "event": "session_start", "intent": self._current_session.intent}
        ]
        
        for action in self._current_session.actions:
            if action.action_type in (ActionType.CLICK, ActionType.KEYPRESS, ActionType.NOTE):
                event = {
                    "ts": action.timestamp_ms,
                    "frame": action.frame_number,
                    "event": action.action_type.value,
                }
                if action.target:
                    event["target"] = action.target.selector
                if action.key:
                    event["key"] = action.key
                if action.result:
                    event["result"] = action.result
                if action.text:
                    event["text"] = action.text
                key_events.append(event)
        
        for note in self._current_session.notes:
            key_events.append({
                "ts": note["ts"],
                "frame": note["frame"],
                "event": "note",
                "text": note["text"],
            })
        
        if self._current_session.outcome:
            key_events.append({
                "ts": self._current_session.duration_ms,
                "frame": self._current_session.frame_count,
                "event": "session_end",
                "outcome": self._current_session.outcome,
            })
        
        return sorted(key_events, key=lambda e: e["ts"])

