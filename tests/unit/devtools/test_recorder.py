"""
Tests for pynext/devtools/recorder.py - Session Recording.

These tests cover:
- Session lifecycle (start, end)
- Action recording
- Note and drawing capture
- Screenshot management
- Output file generation
"""

import json
import pytest
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from pynext.devtools.recorder import (
    SessionRecorder,
    RecordingSession,
    RecordedAction,
    ElementInfo,
    ElementAncestry,
    SignalSnapshot,
    DOMSnapshot,
    FormState,
    DrawingAnnotation,
    ActionType,
)


class TestSessionRecorderLifecycle:
    """Test session start/end lifecycle."""
    
    def test_start_session_creates_directory(self):
        """Starting a session creates the session directory."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session = recorder.start_session("Testing form")
            
            assert session is not None
            assert session.session_id.startswith("rec_")
            assert session.intent == "Testing form"
            assert (Path(tmpdir) / "sessions" / session.session_id).exists()
    
    def test_start_session_creates_subdirectories(self):
        """Starting a session creates subdirectories for frames."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session = recorder.start_session("Test")
            
            session_dir = Path(tmpdir) / "sessions" / session.session_id
            assert (session_dir / "all_frames").exists()
            assert (session_dir / "key_frames").exists()
            assert (session_dir / "annotated_frames").exists()
    
    def test_is_recording_property(self):
        """is_recording reflects session state."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            
            assert recorder.is_recording is False
            recorder.start_session("Test")
            assert recorder.is_recording is True
            recorder.end_session("Done")
            assert recorder.is_recording is False
    
    def test_end_session_saves_files(self):
        """Ending a session saves all required files."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session = recorder.start_session("Test intent")
            recorder.add_note("A note")
            session_path = recorder.end_session("Test outcome")
            
            assert (session_path / "summary.json").exists()
            assert (session_path / "user_notes.json").exists()
            assert (session_path / "annotations.json").exists()
    
    def test_end_session_summary_content(self):
        """Summary.json contains correct session data."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session = recorder.start_session("My intent")
            time.sleep(0.01)  # Small delay
            session_path = recorder.end_session("My outcome")
            
            with open(session_path / "summary.json") as f:
                summary = json.load(f)
            
            assert summary["intent"] == "My intent"
            assert summary["outcome"] == "My outcome"
            assert summary["duration_ms"] > 0
    
    def test_start_new_session_ends_previous(self):
        """Starting a new session auto-ends the previous one."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session1 = recorder.start_session("First")
            session2 = recorder.start_session("Second")
            
            assert recorder.current_session == session2
            assert session2.intent == "Second"
    
    def test_end_session_when_no_session_returns_none(self):
        """Ending when no session is active returns None."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            result = recorder.end_session("No session")
            assert result is None


class TestRecordedAction:
    """Test action recording."""
    
    def test_record_click_action(self):
        """Recording a click captures all context."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            recorder.start_session("Test")
            
            element = ElementInfo(
                selector="#btn",
                tag_name="button",
                id="btn",
            )
            signals = SignalSnapshot(
                signals_before={"sig_1": "old"},
                signals_after={"sig_1": "new"},
            )
            dom = DOMSnapshot(mutations=[])
            
            action = recorder.record_click(
                element=element,
                position={"x": 100, "y": 200},
                signals=signals,
                dom_changes=dom,
            )
            
            assert action.action_type == ActionType.CLICK
            assert action.target == element
            assert action.position == {"x": 100, "y": 200}
    
    def test_record_keypress_action(self):
        """Recording a keypress captures value change."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            recorder.start_session("Test")
            
            element = ElementInfo(selector="input", tag_name="input")
            signals = SignalSnapshot()
            dom = DOMSnapshot()
            
            action = recorder.record_keypress(
                key="a",
                element=element,
                value_before="",
                value_after="a",
                signals=signals,
                dom_changes=dom,
            )
            
            assert action.action_type == ActionType.KEYPRESS
            assert action.key == "a"
            assert action.value_before == ""
            assert action.value_after == "a"
            assert action.result == "CHANGED"
    
    def test_record_keypress_no_change(self):
        """Keypress with no value change has correct result."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            recorder.start_session("Test")
            
            element = ElementInfo(selector="input", tag_name="input")
            
            action = recorder.record_keypress(
                key="Tab",
                element=element,
                value_before="hello",
                value_after="hello",
                signals=SignalSnapshot(),
                dom_changes=DOMSnapshot(),
            )
            
            assert action.result == "NO_CHANGE"
    
    def test_action_written_to_jsonl(self):
        """Actions are incrementally written to actions.jsonl."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session = recorder.start_session("Test")
            
            element = ElementInfo(selector="#btn", tag_name="button")
            recorder.record_click(
                element=element,
                position={"x": 0, "y": 0},
                signals=SignalSnapshot(),
                dom_changes=DOMSnapshot(),
            )
            
            session_dir = Path(tmpdir) / "sessions" / session.session_id
            actions_file = session_dir / "actions.jsonl"
            
            assert actions_file.exists()
            with open(actions_file) as f:
                lines = f.readlines()
            assert len(lines) == 1


class TestElementInfo:
    """Test element information capture."""
    
    def test_element_info_basic(self):
        """ElementInfo stores basic attributes."""
        el = ElementInfo(
            selector="#myid",
            tag_name="div",
            id="myid",
            class_name="container",
        )
        
        assert el.selector == "#myid"
        assert el.tag_name == "div"
        assert el.id == "myid"
    
    def test_element_info_pynext_attributes(self):
        """ElementInfo stores PyNext attributes."""
        el = ElementInfo(
            selector="input",
            tag_name="input",
            pynext_component="FormInput",
            pynext_source="forms.py:42",
            pynext_bind="sig_5",
        )
        
        assert el.pynext_component == "FormInput"
        assert el.pynext_source == "forms.py:42"
        assert el.pynext_bind == "sig_5"
    
    def test_element_info_handlers(self):
        """ElementInfo tracks handler attachment."""
        el = ElementInfo(
            selector="button",
            tag_name="button",
            handlers={"onclick": True, "oninput": False},
        )
        
        assert el.handlers["onclick"] is True
        assert el.handlers["oninput"] is False
    
    def test_element_info_to_dict(self):
        """ElementInfo serializes to dictionary."""
        el = ElementInfo(
            selector="#test",
            tag_name="div",
            hydrated=True,
        )
        
        data = el.to_dict()
        assert data["selector"] == "#test"
        assert data["hydrated"] is True


class TestSignalSnapshot:
    """Test signal state capture."""
    
    def test_signal_snapshot_changed_detection(self):
        """SignalSnapshot detects changed signals."""
        snap = SignalSnapshot(
            signals_before={"s1": "a", "s2": "b", "s3": "c"},
            signals_after={"s1": "a", "s2": "X", "s3": "c"},
        )
        
        changed = snap.signals_that_changed
        assert "s2" in changed
        assert "s1" not in changed
        assert "s3" not in changed
    
    def test_signal_snapshot_no_changes(self):
        """SignalSnapshot returns empty list when no changes."""
        snap = SignalSnapshot(
            signals_before={"s1": "a"},
            signals_after={"s1": "a"},
        )
        
        assert snap.signals_that_changed == []
    
    def test_signal_snapshot_to_dict(self):
        """SignalSnapshot serializes correctly."""
        snap = SignalSnapshot(
            signals_before={"s1": 1},
            signals_after={"s1": 2},
        )
        
        data = snap.to_dict()
        assert "signalsBefore" in data
        assert "signalsAfter" in data
        assert "signalsThatChanged" in data


class TestNotes:
    """Test user note capture."""
    
    def test_add_note(self):
        """Notes are captured with timestamps."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session = recorder.start_session("Test")
            
            recorder.add_note("First note")
            recorder.add_note("Second note")
            
            assert len(session.notes) == 2
            assert session.notes[0]["text"] == "First note"
    
    def test_notes_saved_to_file(self):
        """Notes are saved to user_notes.json."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session = recorder.start_session("Test")
            recorder.add_note("Test note")
            
            session_dir = Path(tmpdir) / "sessions" / session.session_id
            notes_file = session_dir / "user_notes.json"
            
            assert notes_file.exists()
            with open(notes_file) as f:
                data = json.load(f)
            assert len(data["notes"]) == 1


class TestDrawings:
    """Test drawing annotation capture."""
    
    def test_add_drawing(self):
        """Drawings are captured."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session = recorder.start_session("Test")
            
            drawing = DrawingAnnotation(
                type="circle",
                color="red",
                position={"x": 100, "y": 100},
            )
            recorder.add_drawing(drawing)
            
            assert len(session.drawings) == 1
    
    def test_drawing_types(self):
        """Various drawing types are supported."""
        for draw_type in ["circle", "arrow", "text", "freehand"]:
            drawing = DrawingAnnotation(type=draw_type)
            assert drawing.type == draw_type
    
    def test_arrow_drawing(self):
        """Arrow drawing has from/to positions."""
        drawing = DrawingAnnotation(
            type="arrow",
            from_pos={"x": 0, "y": 0},
            to_pos={"x": 100, "y": 100},
            color="blue",
        )
        
        data = drawing.to_dict()
        assert data["from_pos"] == {"x": 0, "y": 0}
        assert data["to_pos"] == {"x": 100, "y": 100}
    
    def test_text_drawing(self):
        """Text drawing has position and text."""
        drawing = DrawingAnnotation(
            type="text",
            position={"x": 50, "y": 50},
            text="Bug here!",
        )
        
        data = drawing.to_dict()
        assert data["text"] == "Bug here!"
    
    def test_freehand_drawing(self):
        """Freehand drawing has points array."""
        points = [{"x": 0, "y": 0}, {"x": 10, "y": 10}, {"x": 20, "y": 20}]
        drawing = DrawingAnnotation(
            type="freehand",
            points=points,
        )
        
        data = drawing.to_dict()
        assert data["points"] == points


class TestScreenshots:
    """Test screenshot management."""
    
    def test_save_screenshot(self):
        """Screenshots are saved to correct directory."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            recorder.start_session("Test")
            
            # Fake PNG data
            png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
            
            path = recorder.save_screenshot(png_data, frame_type="all", frame_number=1)
            
            assert path == "all_frames/0001.png"
    
    def test_save_key_frame(self):
        """Key frames go to key_frames directory."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            recorder.start_session("Test")
            
            png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
            path = recorder.save_screenshot(png_data, frame_type="key", frame_number=5)
            
            assert path == "key_frames/0005.png"
    
    def test_screenshot_without_session(self):
        """Saving screenshot without session returns None."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            
            png_data = b"\x89PNG\r\n\x1a\n"
            path = recorder.save_screenshot(png_data)
            
            assert path is None


class TestRecordingSession:
    """Test RecordingSession dataclass."""
    
    def test_session_duration(self):
        """Duration is calculated correctly."""
        session = RecordingSession(
            session_id="test",
            intent="Test",
            start_time=1000.0,
        )
        session.end_time = 1005.0
        
        assert session.duration_ms == 5000
    
    def test_session_add_action(self):
        """Actions are added and frame count updated."""
        session = RecordingSession(
            session_id="test",
            intent="Test",
            start_time=time.time(),
        )
        
        action = RecordedAction(
            timestamp_ms=100,
            action_type=ActionType.CLICK,
            frame_number=5,
        )
        session.add_action(action)
        
        assert len(session.actions) == 1
        assert session.frame_count == 5
    
    def test_session_mark_key_frame(self):
        """Key frames are tracked."""
        session = RecordingSession(
            session_id="test",
            intent="Test",
            start_time=time.time(),
        )
        
        session.mark_key_frame(10)
        session.mark_key_frame(20)
        session.mark_key_frame(10)  # Duplicate
        
        assert session.key_frames == [10, 20]
    
    def test_session_to_dict(self):
        """Session serializes to dictionary."""
        session = RecordingSession(
            session_id="test_123",
            intent="Test intent",
            start_time=1000.0,
            mode="app",
        )
        session.end_time = 1002.0
        session.outcome = "Test outcome"
        
        data = session.to_dict()
        
        assert data["session_id"] == "test_123"
        assert data["intent"] == "Test intent"
        assert data["outcome"] == "Test outcome"
        assert data["mode"] == "app"
        assert data["duration_ms"] == 2000


class TestFormState:
    """Test form state capture."""
    
    def test_form_state_basic(self):
        """FormState stores form information."""
        form = FormState(
            form_id="myform",
            is_valid=True,
            is_dirty=True,
            fields={
                "email": {"value": "test@test.com", "touched": True},
            }
        )
        
        assert form.form_id == "myform"
        assert form.is_valid is True
        assert form.fields["email"]["value"] == "test@test.com"
    
    def test_form_state_to_dict(self):
        """FormState serializes to dictionary."""
        form = FormState(form_id="form1")
        data = form.to_dict()
        
        assert data["form_id"] == "form1"
        assert "is_valid" in data


class TestOnActionCallback:
    """Test action callbacks."""
    
    def test_on_action_callback_fired(self):
        """Callbacks are fired when actions are recorded."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            recorder.start_session("Test")
            
            captured = []
            recorder.on_action(lambda a: captured.append(a))
            
            element = ElementInfo(selector="div", tag_name="div")
            recorder.record_click(
                element=element,
                position={"x": 0, "y": 0},
                signals=SignalSnapshot(),
                dom_changes=DOMSnapshot(),
            )
            
            assert len(captured) == 1
            assert captured[0].action_type == ActionType.CLICK
    
    def test_multiple_callbacks(self):
        """Multiple callbacks are all fired."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            recorder.start_session("Test")
            
            count = [0]
            recorder.on_action(lambda a: count.__setitem__(0, count[0] + 1))
            recorder.on_action(lambda a: count.__setitem__(0, count[0] + 1))
            
            element = ElementInfo(selector="div", tag_name="div")
            recorder.record_click(
                element=element,
                position={"x": 0, "y": 0},
                signals=SignalSnapshot(),
                dom_changes=DOMSnapshot(),
            )
            
            assert count[0] == 2


class TestElementAncestry:
    """Test element ancestry tracking."""
    
    def test_ancestry_basic(self):
        """ElementAncestry stores parent chain."""
        ancestry = ElementAncestry(
            ancestors=[
                {"tag": "form", "id": "myform"},
                {"tag": "div", "class": "container"},
            ]
        )
        
        assert len(ancestry.ancestors) == 2
    
    def test_ancestry_nearest_component(self):
        """ElementAncestry tracks nearest PyNext component."""
        ancestry = ElementAncestry(
            ancestors=[{"tag": "div"}],
            nearest_pynext_component={
                "type": "Show",
                "source": "issues.py:234",
            }
        )
        
        assert ancestry.nearest_pynext_component["type"] == "Show"


class TestSelectedElement:
    """Test element selection via inspect mode."""
    
    def test_set_selected_element(self):
        """Selected element is stored in session."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session = recorder.start_session("Test")
            
            element = ElementInfo(
                selector="#target",
                tag_name="input",
                pynext_source="forms.py:100",
            )
            recorder.set_selected_element(element)
            
            assert session.selected_element == element


class TestHydrationMap:
    """Test hydration map capture."""
    
    def test_set_hydration_map(self):
        """Hydration map is stored in session."""
        with TemporaryDirectory() as tmpdir:
            recorder = SessionRecorder(Path(tmpdir))
            session = recorder.start_session("Test")
            
            hydration_map = {
                "total": 10,
                "hydrated": 8,
                "unhydrated": [{"selector": "input", "reason": "handler not attached"}],
            }
            recorder.set_hydration_map(hydration_map)
            
            assert session.hydration_map["total"] == 10
            assert session.hydration_map["hydrated"] == 8

