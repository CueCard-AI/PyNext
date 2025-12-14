"""
Tests for the unified timeline system in PyNext AI DevTools.

This module tests the TimelineEvent dataclass and the timeline functionality
in SessionRecorder that ensures all events are captured in a single 
chronological array.
"""

import json
import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from pynext.devtools.recorder import (
    TimelineEvent,
    RecordingSession,
    SessionRecorder,
    ElementInfo,
    ActionType,
    RecordedAction,
    SignalSnapshot,
    DrawingAnnotation,
)


class TestTimelineEvent:
    """Tests for the TimelineEvent dataclass."""
    
    def test_timeline_event_creation(self):
        """Test creating a basic timeline event."""
        event = TimelineEvent(
            seq=1,
            ts=1000,
            type="click",
            data={"selector": "#button"},
            screenshot="key_frames/0001.png",
        )
        
        assert event.seq == 1
        assert event.ts == 1000
        assert event.type == "click"
        assert event.data == {"selector": "#button"}
        assert event.screenshot == "key_frames/0001.png"
    
    def test_timeline_event_default_values(self):
        """Test default values for optional fields."""
        event = TimelineEvent(seq=1, ts=0, type="frame")
        
        assert event.data == {}
        assert event.screenshot is None
    
    def test_timeline_event_to_dict(self):
        """Test serialization to dictionary."""
        event = TimelineEvent(
            seq=5,
            ts=5000,
            type="note",
            data={"text": "User clicked the button"},
            screenshot="key_frames/0005.png",
        )
        
        result = event.to_dict()
        
        assert result == {
            "seq": 5,
            "ts": 5000,
            "type": "note",
            "data": {"text": "User clicked the button"},
            "screenshot": "key_frames/0005.png",
        }
    
    def test_timeline_event_to_dict_without_screenshot(self):
        """Test serialization when screenshot is None."""
        event = TimelineEvent(seq=1, ts=0, type="session_start", data={"intent": "test"})
        
        result = event.to_dict()
        
        # Should not include screenshot key when None
        assert "screenshot" not in result
        assert result["type"] == "session_start"
    
    def test_timeline_event_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "seq": 10,
            "ts": 10000,
            "type": "error",
            "data": {"message": "Something went wrong"},
            "screenshot": "key_frames/error.png",
        }
        
        event = TimelineEvent.from_dict(data)
        
        assert event.seq == 10
        assert event.ts == 10000
        assert event.type == "error"
        assert event.data["message"] == "Something went wrong"
        assert event.screenshot == "key_frames/error.png"
    
    def test_timeline_event_from_dict_minimal(self):
        """Test creating from minimal dictionary."""
        data = {"seq": 1, "ts": 0, "type": "frame"}
        
        event = TimelineEvent.from_dict(data)
        
        assert event.seq == 1
        assert event.data == {}
        assert event.screenshot is None


class TestRecordingSessionTimeline:
    """Tests for timeline functionality in RecordingSession."""
    
    def test_session_has_timeline(self):
        """Test that sessions have an empty timeline by default."""
        session = RecordingSession(
            session_id="test_123",
            intent="Testing timeline",
            start_time=time.time(),
        )
        
        assert session.timeline == []
        assert session.console_errors == []
    
    def test_append_event_basic(self):
        """Test appending a basic event."""
        session = RecordingSession(
            session_id="test_123",
            intent="Testing timeline",
            start_time=time.time() - 1.0,  # 1 second ago
        )
        
        event = session.append_event(
            event_type="click",
            data={"selector": "#button"},
        )
        
        assert len(session.timeline) == 1
        assert event.seq == 1
        assert event.type == "click"
        assert event.data["selector"] == "#button"
        assert event.ts > 0  # Should have positive timestamp
    
    def test_append_event_with_screenshot(self):
        """Test appending event with screenshot."""
        session = RecordingSession(
            session_id="test_123",
            intent="Testing",
            start_time=time.time(),
        )
        
        event = session.append_event(
            event_type="note",
            data={"text": "This is a note"},
            screenshot="key_frames/0001.png",
        )
        
        assert event.screenshot == "key_frames/0001.png"
    
    def test_append_event_increments_seq(self):
        """Test that sequence numbers increment."""
        session = RecordingSession(
            session_id="test_123",
            intent="Testing",
            start_time=time.time(),
        )
        
        e1 = session.append_event(event_type="frame", data={})
        e2 = session.append_event(event_type="click", data={})
        e3 = session.append_event(event_type="note", data={"text": "test"})
        
        assert e1.seq == 1
        assert e2.seq == 2
        assert e3.seq == 3
        assert len(session.timeline) == 3
    
    def test_timeline_count_property(self):
        """Test timeline_count property."""
        session = RecordingSession(
            session_id="test_123",
            intent="Testing",
            start_time=time.time(),
        )
        
        assert session.timeline_count == 0
        
        session.append_event(event_type="frame", data={})
        assert session.timeline_count == 1
        
        session.append_event(event_type="click", data={})
        assert session.timeline_count == 2
    
    def test_to_dict_includes_timeline_count(self):
        """Test that to_dict includes timeline_count."""
        session = RecordingSession(
            session_id="test_123",
            intent="Testing",
            start_time=time.time(),
        )
        session.append_event(event_type="click", data={})
        session.append_event(event_type="note", data={})
        
        result = session.to_dict()
        
        assert result["timeline_count"] == 2


class TestSessionRecorderTimeline:
    """Tests for timeline functionality in SessionRecorder."""
    
    def test_save_creates_timeline_json(self, tmp_path):
        """Test that ending session creates timeline.json."""
        recorder = SessionRecorder(output_dir=tmp_path, mode="app")
        
        # Start session
        session = recorder.start_session("Testing timeline output")
        session.append_event(event_type="session_start", data={"intent": "Testing"})
        session.append_event(event_type="click", data={"selector": "#btn"})
        session.append_event(event_type="note", data={"text": "Clicked button"})
        
        # End session
        session_dir = recorder.end_session("Test complete")
        
        # Check timeline.json exists
        timeline_path = session_dir / "timeline.json"
        assert timeline_path.exists()
        
        # Check content
        with open(timeline_path) as f:
            data = json.load(f)
        
        assert data["session_id"].startswith("rec_")
        assert data["intent"] == "Testing timeline output"
        assert data["outcome"] == "Test complete"
        assert len(data["events"]) == 3
        assert data["events"][0]["type"] == "session_start"
        assert data["events"][1]["type"] == "click"
        assert data["events"][2]["type"] == "note"
    
    def test_timeline_includes_console_errors(self, tmp_path):
        """Test that console errors are saved."""
        recorder = SessionRecorder(output_dir=tmp_path, mode="app")
        
        session = recorder.start_session("Testing errors")
        session.console_errors.append({
            "message": "TypeError: Cannot read property",
            "stack": "at handleClick (app.js:10)",
            "ts": 1000,
        })
        
        session_dir = recorder.end_session("Error occurred")
        
        with open(session_dir / "timeline.json") as f:
            data = json.load(f)
        
        assert len(data["console_errors"]) == 1
        assert "TypeError" in data["console_errors"][0]["message"]
    
    def test_timeline_includes_final_signals(self, tmp_path):
        """Test that final signals are saved."""
        recorder = SessionRecorder(output_dir=tmp_path, mode="app")
        
        session = recorder.start_session("Testing signals")
        session.hydration_map = {
            "signals": {
                "sig_1": {"value": True},
                "sig_2": {"value": "test"},
            }
        }
        
        session_dir = recorder.end_session("Done")
        
        with open(session_dir / "timeline.json") as f:
            data = json.load(f)
        
        assert data["final_signals"]["sig_1"]["value"] == True
        assert data["final_signals"]["sig_2"]["value"] == "test"
    
    def test_timeline_includes_selected_element(self, tmp_path):
        """Test that selected element is saved."""
        recorder = SessionRecorder(output_dir=tmp_path, mode="app")
        
        session = recorder.start_session("Testing inspect")
        recorder.set_selected_element(ElementInfo(
            selector="#create-btn",
            tag_name="button",
            id="create-btn",
            pynext_source="issues.py:42",
        ))
        
        session_dir = recorder.end_session("Done")
        
        with open(session_dir / "timeline.json") as f:
            data = json.load(f)
        
        assert data["selected_element"]["selector"] == "#create-btn"
        assert data["selected_element"]["pynext_source"] == "issues.py:42"


class TestTimelineEventTypes:
    """Tests for different event types in the timeline."""
    
    def test_click_event(self):
        """Test click event structure."""
        event = TimelineEvent(
            seq=1,
            ts=5000,
            type="click",
            data={
                "selector": "#submit-btn",
                "tagName": "BUTTON",
                "id": "submit-btn",
                "textContent": "Submit",
                "signals_changed": [{"id": "sig_1", "before": False, "after": True}],
            },
            screenshot="key_frames/click_001.png",
        )
        
        d = event.to_dict()
        assert d["type"] == "click"
        assert d["data"]["selector"] == "#submit-btn"
        assert len(d["data"]["signals_changed"]) == 1
    
    def test_note_event(self):
        """Test note event structure."""
        event = TimelineEvent(
            seq=2,
            ts=6000,
            type="note",
            data={"text": "The button didn't work"},
            screenshot="key_frames/note_001.png",
        )
        
        d = event.to_dict()
        assert d["type"] == "note"
        assert d["data"]["text"] == "The button didn't work"
    
    def test_error_event(self):
        """Test error event structure."""
        event = TimelineEvent(
            seq=3,
            ts=7000,
            type="error",
            data={
                "level": "error",
                "message": "Cannot read property 'push' of undefined",
                "stack": "at handleSubmit (app.js:45)",
            },
        )
        
        d = event.to_dict()
        assert d["type"] == "error"
        assert d["data"]["level"] == "error"
        assert "push" in d["data"]["message"]
    
    def test_inspect_event(self):
        """Test inspect event structure."""
        event = TimelineEvent(
            seq=4,
            ts=8000,
            type="inspect",
            data={
                "selector": "#modal",
                "tagName": "DIV",
                "source": "issues.py:120",
                "handlers": {"onclick": True, "oninput": False},
                "hydrated": True,
            },
        )
        
        d = event.to_dict()
        assert d["type"] == "inspect"
        assert d["data"]["source"] == "issues.py:120"
        assert d["data"]["hydrated"] == True
    
    def test_signal_event(self):
        """Test signal change event structure."""
        event = TimelineEvent(
            seq=5,
            ts=9000,
            type="signal",
            data={
                "signal_name": "show_modal",
                "new_value": True,
            },
        )
        
        d = event.to_dict()
        assert d["type"] == "signal"
        assert d["data"]["signal_name"] == "show_modal"
    
    def test_session_start_event(self):
        """Test session start event structure."""
        event = TimelineEvent(
            seq=1,
            ts=0,
            type="session_start",
            data={"intent": "Testing the create issue button"},
        )
        
        d = event.to_dict()
        assert d["type"] == "session_start"
        assert d["ts"] == 0
        assert "create issue" in d["data"]["intent"]
    
    def test_session_end_event(self):
        """Test session end event structure."""
        event = TimelineEvent(
            seq=100,
            ts=30000,
            type="session_end",
            data={"outcome": "Button does not work"},
        )
        
        d = event.to_dict()
        assert d["type"] == "session_end"
        assert "Button does not work" in d["data"]["outcome"]


class TestTimelineChronology:
    """Tests for chronological ordering in timelines."""
    
    def test_events_ordered_by_seq(self):
        """Test that events maintain sequential order."""
        session = RecordingSession(
            session_id="test",
            intent="Test",
            start_time=time.time(),
        )
        
        # Add events with small delays to ensure different timestamps
        session.append_event("session_start", {"intent": "Test"})
        session.append_event("frame", {})
        session.append_event("click", {"selector": "#btn"})
        session.append_event("note", {"text": "note"})
        session.append_event("error", {"message": "err"})
        session.append_event("session_end", {"outcome": "done"})
        
        # Check sequence numbers
        seqs = [e.seq for e in session.timeline]
        assert seqs == [1, 2, 3, 4, 5, 6]
    
    def test_timestamps_are_relative(self):
        """Test that timestamps are relative to session start."""
        start = time.time()
        session = RecordingSession(
            session_id="test",
            intent="Test",
            start_time=start,
        )
        
        # First event should have ~0 timestamp
        e1 = session.append_event("session_start", {})
        assert e1.ts >= 0
        assert e1.ts < 100  # Less than 100ms
        
        # After a delay, timestamp should reflect elapsed time
        time.sleep(0.05)  # 50ms
        e2 = session.append_event("click", {})
        assert e2.ts >= 50  # At least 50ms
        assert e2.ts > e1.ts  # Later than first event


class TestTimelineIntegration:
    """Integration tests for the timeline system."""
    
    def test_full_session_workflow(self, tmp_path):
        """Test a complete session workflow with timeline."""
        recorder = SessionRecorder(output_dir=tmp_path, mode="app")
        
        # Start session
        session = recorder.start_session("Testing create issue flow")
        
        # Simulate session events
        session.append_event("session_start", {"intent": "Testing create issue flow"})
        session.append_event("click", {"selector": "#new-issue-btn"})
        session.append_event("note", {"text": "Modal opened"})
        session.append_event("click", {"selector": "input[name=title]"})
        session.append_event("note", {"text": "Typing in title field"})
        session.append_event("click", {"selector": "#create-btn", "signals_changed": []})
        session.append_event("note", {"text": "Nothing happened!"})
        session.append_event("error", {"message": "TypeError: Cannot read property"})
        session.append_event("inspect", {"selector": "#create-btn", "source": "issues.py:185"})
        
        # Add console error
        session.console_errors.append({
            "message": "TypeError: Cannot read property 'push' of undefined",
            "ts": 5000,
        })
        
        # End session
        session.append_event("session_end", {"outcome": "Button is broken"})
        session_dir = recorder.end_session("Button is broken")
        
        # Verify timeline.json
        with open(session_dir / "timeline.json") as f:
            data = json.load(f)
        
        assert len(data["events"]) == 10
        assert data["events"][0]["type"] == "session_start"
        assert data["events"][-1]["type"] == "session_end"
        
        # Check event types are all recorded
        event_types = [e["type"] for e in data["events"]]
        assert "click" in event_types
        assert "note" in event_types
        assert "error" in event_types
        assert "inspect" in event_types
        
        # Check console errors
        assert len(data["console_errors"]) == 1
        assert "TypeError" in data["console_errors"][0]["message"]

