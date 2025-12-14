"""
Tests for Debug Stream - JSONL File Streaming for AI Consumption.

Tests cover:
- DebugStream initialization and configuration
- Event writing and buffering
- State file management
- File rotation
- Event reading and iteration
- Atomic writes
- Cleanup and clearing
"""

import pytest
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from pynext.devtools.stream import DebugStream, StreamConfig, format_event_for_display
from pynext.devtools.capture import DebugEvent, EventType


# ============================================
# StreamConfig Tests
# ============================================

class TestStreamConfig:
    """Tests for StreamConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = StreamConfig()
        
        assert config.max_file_size_mb == 10.0
        assert config.max_events == 10000
        assert config.flush_interval == 0.5
        assert config.rotate_count == 3
    
    def test_custom_values(self):
        """Test custom configuration."""
        config = StreamConfig(
            max_file_size_mb=5.0,
            max_events=5000,
            flush_interval=1.0,
            rotate_count=5,
        )
        
        assert config.max_file_size_mb == 5.0
        assert config.max_events == 5000


# ============================================
# DebugStream Initialization Tests
# ============================================

class TestDebugStreamInit:
    """Tests for DebugStream initialization."""
    
    def test_init_creates_directory(self):
        """Test that init creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug" / "nested"
            
            stream = DebugStream(output_dir)
            
            assert output_dir.exists()
    
    def test_events_file_path(self):
        """Test events file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            
            stream = DebugStream(output_dir)
            
            assert stream.events_file == output_dir / "events.jsonl"
    
    def test_state_file_path(self):
        """Test state file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            
            stream = DebugStream(output_dir)
            
            assert stream.state_file == output_dir / "state.json"
    
    def test_init_with_existing_file(self):
        """Test init with existing events file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            output_dir.mkdir()
            
            # Create existing file with some events
            events_file = output_dir / "events.jsonl"
            events_file.write_text('{"seq":1}\n{"seq":2}\n{"seq":3}\n')
            
            stream = DebugStream(output_dir)
            
            assert stream.event_count == 3


# ============================================
# Event Writing Tests
# ============================================

class TestDebugStreamWrite:
    """Tests for event writing."""
    
    def test_write_event(self):
        """Test writing a single event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            event = DebugEvent(
                seq=1,
                ts=time.time(),
                type=EventType.CONSOLE_LOG,
                data={"text": "Hello"},
                summary="console.log: Hello",
            )
            
            stream.write_event(event)
            stream.flush()
            
            assert stream.event_count == 1
            assert stream.events_file.exists()
    
    def test_write_multiple_events(self):
        """Test writing multiple events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            events = [
                DebugEvent(seq=i, ts=time.time(), type=EventType.CONSOLE_LOG)
                for i in range(5)
            ]
            
            stream.write_events(events)
            stream.flush()
            
            assert stream.event_count == 5
    
    def test_write_event_buffering(self):
        """Test that events are buffered and flushed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            event = DebugEvent(seq=1, ts=time.time(), type=EventType.CONSOLE_LOG)
            stream.write_event(event)
            
            # Force flush
            stream.flush()
            
            # File should exist after flush
            assert stream.events_file.exists()
            assert stream.event_count == 1
    
    def test_flush_writes_to_file(self):
        """Test that flush writes buffered events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            config = StreamConfig(flush_interval=10.0)
            stream = DebugStream(output_dir, config)
            
            event = DebugEvent(seq=1, ts=time.time(), type=EventType.CONSOLE_LOG)
            stream.write_event(event)
            stream.flush()
            
            assert len(stream._buffer) == 0
            assert stream.events_file.exists()
    
    def test_event_json_format(self):
        """Test that events are written as valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            event = DebugEvent(
                seq=42,
                ts=1702345678.123,
                type=EventType.SIGNAL_CHANGE,
                data={"signal_name": "count", "old_value": 0, "new_value": 1},
                summary="Signal count: 0 → 1",
            )
            
            stream.write_event(event)
            stream.flush()
            
            # Read and parse
            content = stream.events_file.read_text().strip()
            parsed = json.loads(content)
            
            assert parsed["seq"] == 42
            assert parsed["type"] == "signal_change"


# ============================================
# State Writing Tests
# ============================================

class TestDebugStreamState:
    """Tests for state file management."""
    
    def test_write_state(self):
        """Test writing state file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            state = {
                "url": "http://localhost:3000",
                "signals": {"count": 5},
            }
            
            stream.write_state(state)
            
            assert stream.state_file.exists()
    
    def test_write_state_adds_metadata(self):
        """Test that write_state adds timestamp and event count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            stream.write_state({"key": "value"})
            
            content = json.loads(stream.state_file.read_text())
            
            assert "_timestamp" in content
            assert "_event_count" in content
    
    def test_read_state(self):
        """Test reading state file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            state = {"url": "http://localhost:3000", "count": 42}
            stream.write_state(state)
            
            read_state = stream.read_state()
            
            assert read_state["url"] == "http://localhost:3000"
            assert read_state["count"] == 42
    
    def test_read_state_missing(self):
        """Test reading when state file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            result = stream.read_state()
            
            assert result is None
    
    def test_state_overwrites_previous(self):
        """Test that state overwrites previous state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            stream.write_state({"version": 1})
            stream.write_state({"version": 2})
            
            result = stream.read_state()
            
            assert result["version"] == 2


# ============================================
# Event Reading Tests
# ============================================

class TestDebugStreamRead:
    """Tests for event reading."""
    
    def test_read_events(self):
        """Test reading events from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            # Write events
            for i in range(5):
                event = DebugEvent(
                    seq=i + 1,
                    ts=time.time(),
                    type=EventType.CONSOLE_LOG,
                    summary=f"Event {i + 1}",
                )
                stream.write_event(event)
            stream.flush()
            
            # Read events
            events = stream.read_events()
            
            assert len(events) == 5
    
    def test_read_events_limit(self):
        """Test reading with limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            for i in range(10):
                event = DebugEvent(seq=i, ts=time.time(), type=EventType.CONSOLE_LOG)
                stream.write_event(event)
            stream.flush()
            
            events = stream.read_events(limit=3)
            
            assert len(events) == 3
    
    def test_read_events_reverse(self):
        """Test reading events in reverse order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            for i in range(5):
                event = DebugEvent(seq=i + 1, ts=time.time(), type=EventType.CONSOLE_LOG)
                stream.write_event(event)
            stream.flush()
            
            events = stream.read_events(reverse=True)
            
            assert events[0].seq == 5  # Most recent first
    
    def test_read_events_offset(self):
        """Test reading with offset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            for i in range(5):
                event = DebugEvent(seq=i + 1, ts=time.time(), type=EventType.CONSOLE_LOG)
                stream.write_event(event)
            stream.flush()
            
            events = stream.read_events(offset=2, reverse=False)
            
            assert len(events) == 3
            assert events[0].seq == 3
    
    def test_tail_events(self):
        """Test getting last N events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            for i in range(10):
                event = DebugEvent(seq=i + 1, ts=time.time(), type=EventType.CONSOLE_LOG)
                stream.write_event(event)
            stream.flush()
            
            events = stream.tail_events(count=3)
            
            assert len(events) == 3
            assert events[0].seq == 8  # Oldest of last 3
            assert events[2].seq == 10  # Newest
    
    def test_iter_events(self):
        """Test iterating over events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            for i in range(5):
                event = DebugEvent(seq=i + 1, ts=time.time(), type=EventType.CONSOLE_LOG)
                stream.write_event(event)
            stream.flush()
            
            events = list(stream.iter_events())
            
            assert len(events) == 5
            assert events[0].seq == 1


# ============================================
# Clear and Cleanup Tests
# ============================================

class TestDebugStreamClear:
    """Tests for clearing and cleanup."""
    
    def test_clear(self):
        """Test clearing all debug files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            # Write some data
            stream.write_event(DebugEvent(seq=1, ts=time.time(), type=EventType.CONSOLE_LOG))
            stream.flush()
            stream.write_state({"url": "http://localhost:3000"})
            
            # Clear
            stream.clear()
            
            assert stream.event_count == 0
            assert not stream.events_file.exists()
            assert not stream.state_file.exists()
    
    def test_clear_with_screenshots(self):
        """Test clear removes screenshot directory contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            # Create screenshot dir and file
            screenshots_dir = output_dir / "screenshots"
            screenshots_dir.mkdir()
            (screenshots_dir / "001.png").write_bytes(b"PNG")
            
            stream.clear()
            
            # Dir should exist but be empty
            assert screenshots_dir.exists()
            assert len(list(screenshots_dir.glob("*"))) == 0


# ============================================
# File Rotation Tests
# ============================================

class TestDebugStreamRotation:
    """Tests for file rotation."""
    
    def test_should_rotate_by_size(self):
        """Test rotation trigger by file size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            config = StreamConfig(max_file_size_mb=0.0001)  # Very small
            stream = DebugStream(output_dir, config)
            
            # Write enough to trigger rotation
            for i in range(100):
                event = DebugEvent(
                    seq=i,
                    ts=time.time(),
                    type=EventType.CONSOLE_LOG,
                    data={"text": "A" * 1000},
                )
                stream.write_event(event)
            stream.flush()
            
            # Should have rotated
            assert (output_dir / "events.1.jsonl").exists()
    
    def test_should_rotate_by_count(self):
        """Test rotation trigger by event count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            config = StreamConfig(max_events=10)
            stream = DebugStream(output_dir, config)
            
            # Write more than max
            for i in range(15):
                event = DebugEvent(seq=i, ts=time.time(), type=EventType.CONSOLE_LOG)
                stream.write_event(event)
            stream.flush()
            
            # Should have rotated
            assert (output_dir / "events.1.jsonl").exists()


# ============================================
# Summary Tests
# ============================================

class TestDebugStreamSummary:
    """Tests for stream summary."""
    
    def test_get_summary(self):
        """Test getting stream summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            # Write some events
            for i in range(5):
                event = DebugEvent(seq=i, ts=time.time(), type=EventType.CONSOLE_LOG)
                stream.write_event(event)
            stream.flush()
            
            summary = stream.get_summary()
            
            assert summary["event_count"] == 5
            assert summary["events_file_size"] > 0
    
    def test_summary_with_screenshots(self):
        """Test summary includes screenshot count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            stream = DebugStream(output_dir)
            
            # Create screenshot files
            screenshots_dir = output_dir / "screenshots"
            screenshots_dir.mkdir()
            for i in range(3):
                (screenshots_dir / f"{i:03d}.png").write_bytes(b"PNG")
            
            summary = stream.get_summary()
            
            assert summary["screenshot_count"] == 3


# ============================================
# Format Event Tests
# ============================================

class TestFormatEventForDisplay:
    """Tests for event display formatting."""
    
    def test_format_console_log(self):
        """Test formatting console log event."""
        event = DebugEvent(
            seq=1,
            ts=time.time(),
            type=EventType.CONSOLE_LOG,
            summary="console.log: Hello",
        )
        
        result = format_event_for_display(event)
        
        assert "[0001]" in result
        assert "[console_log]" in result
        assert "Hello" in result
    
    def test_format_error_with_color(self):
        """Test formatting error event with color."""
        event = DebugEvent(
            seq=1,
            ts=time.time(),
            type=EventType.CONSOLE_ERROR,
            summary="Error: Something failed",
        )
        
        result = format_event_for_display(event)
        
        # Should contain ANSI color codes
        assert "\033[" in result
    
    def test_format_with_source(self):
        """Test formatting with source location."""
        event = DebugEvent(
            seq=1,
            ts=time.time(),
            type=EventType.JS_EXCEPTION,
            summary="TypeError",
            source="app.js:42",
        )
        
        result = format_event_for_display(event)
        
        assert "(app.js:42)" in result
    
    def test_format_with_screenshot(self):
        """Test formatting with screenshot path."""
        event = DebugEvent(
            seq=1,
            ts=time.time(),
            type=EventType.CLICK,
            summary="Click: #button",
            screenshot="screenshots/001.png",
        )
        
        result = format_event_for_display(event)
        
        assert "📷" in result or "screenshots/001.png" in result

