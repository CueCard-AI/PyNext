"""
Debug Stream - JSONL File Streaming for AI Consumption.

This module handles writing debug events to files in a format that's
easy for AI assistants to read and process.

Format:
    - events.jsonl: Append-only JSON Lines format
    - state.json: Current state summary (overwritten)

Why JSONL?
    - Append-only: New events added without rewriting entire file
    - Streaming: AI can tail the file for real-time updates
    - Simple: One JSON object per line, easy to parse
    - Recoverable: If file corrupts, only one line is lost

Atomic Writes:
    To prevent corruption during writes, we use atomic operations:
    1. Write to temporary file
    2. Flush and sync to disk
    3. Rename to target file (atomic on most filesystems)

Example:
    stream = DebugStream(Path(".pynext/debug"))
    
    # Write events
    stream.write_event(event)
    
    # Update current state
    stream.write_state({
        "url": "http://localhost:3000/issues",
        "signals": {...},
        "last_event": event.to_dict(),
    })
    
    # Read events for analysis
    events = stream.read_events(limit=100)
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional
import tempfile
import shutil

from pynext.devtools.capture import DebugEvent


@dataclass
class StreamConfig:
    """Configuration for debug stream."""
    max_file_size_mb: float = 10.0  # Max size before rotation
    max_events: int = 10000  # Max events before rotation
    flush_interval: float = 0.5  # Seconds between flushes
    rotate_count: int = 3  # Number of rotated files to keep


class DebugStream:
    """
    Writes debug events to JSONL files for AI consumption.
    
    This class handles:
    - Append-only event logging to events.jsonl
    - State snapshot to state.json
    - File rotation when size limit reached
    - Atomic writes for crash safety
    
    Attributes:
        output_dir: Directory for output files
        events_file: Path to events.jsonl
        state_file: Path to state.json
        event_count: Number of events written
    
    Example:
        stream = DebugStream(Path(".pynext/debug"))
        
        stream.write_event(DebugEvent(...))
        stream.write_state({"url": "...", "signals": {...}})
        
        # Read last 50 events
        for event in stream.read_events(limit=50):
            print(event.summary)
    """
    
    def __init__(
        self,
        output_dir: Path,
        config: Optional[StreamConfig] = None,
    ):
        """
        Initialize the debug stream.
        
        Args:
            output_dir: Directory for output files
            config: Optional configuration
        """
        self._output_dir = Path(output_dir)
        self._config = config or StreamConfig()
        
        # Create output directory
        self._output_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self._events_file = self._output_dir / "events.jsonl"
        self._state_file = self._output_dir / "state.json"
        
        # State
        self._event_count = 0
        self._file_size = 0
        self._last_flush = 0.0
        self._buffer: list[str] = []
        
        # Initialize/check existing file
        if self._events_file.exists():
            self._file_size = self._events_file.stat().st_size
            self._event_count = sum(1 for _ in open(self._events_file))
    
    @property
    def events_file(self) -> Path:
        """Path to events.jsonl file."""
        return self._events_file
    
    @property
    def state_file(self) -> Path:
        """Path to state.json file."""
        return self._state_file
    
    @property
    def event_count(self) -> int:
        """Number of events written."""
        return self._event_count
    
    def clear(self) -> None:
        """Clear all debug files and reset state."""
        if self._events_file.exists():
            self._events_file.unlink()
        if self._state_file.exists():
            self._state_file.unlink()
        
        # Clear screenshot and snapshot directories
        for subdir in ["screenshots", "snapshots"]:
            dir_path = self._output_dir / subdir
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
                dir_path.mkdir()
        
        self._event_count = 0
        self._file_size = 0
        self._buffer.clear()
    
    def write_event(self, event: DebugEvent) -> None:
        """
        Write a debug event to the events file.
        
        Args:
            event: DebugEvent to write
        """
        line = json.dumps(event.to_dict(), separators=(",", ":")) + "\n"
        self._buffer.append(line)
        self._event_count += 1
        self._file_size += len(line.encode("utf-8"))
        
        # Check if we should flush
        now = time.time()
        should_flush = (
            now - self._last_flush >= self._config.flush_interval
            or len(self._buffer) >= 10
        )
        
        if should_flush:
            self.flush()
        
        # Check if we should rotate
        if self._should_rotate():
            self._rotate()
    
    def write_events(self, events: list[DebugEvent]) -> None:
        """
        Write multiple events at once.
        
        Args:
            events: List of DebugEvents to write
        """
        for event in events:
            self.write_event(event)
    
    def flush(self) -> None:
        """Flush buffered events to disk."""
        if not self._buffer:
            return
        
        try:
            with open(self._events_file, "a", encoding="utf-8") as f:
                f.writelines(self._buffer)
                f.flush()
                os.fsync(f.fileno())
            
            self._buffer.clear()
            self._last_flush = time.time()
            
        except Exception as e:
            # On error, keep buffer for retry
            pass
    
    def write_state(self, state: dict) -> None:
        """
        Write current state snapshot.
        
        This overwrites the previous state file atomically.
        
        Args:
            state: Current state dictionary
        """
        state["_timestamp"] = time.time()
        state["_event_count"] = self._event_count
        
        # Atomic write using temp file + rename
        try:
            fd, temp_path = tempfile.mkstemp(
                dir=self._output_dir,
                suffix=".json.tmp",
            )
            
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic rename
                os.replace(temp_path, self._state_file)
                
            except Exception:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
                raise
                
        except Exception:
            pass  # Best effort write
    
    def read_events(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        reverse: bool = True,
    ) -> list[DebugEvent]:
        """
        Read events from the events file.
        
        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            reverse: If True, return most recent first
        
        Returns:
            List of DebugEvent objects
        """
        # Flush any buffered events first
        self.flush()
        
        if not self._events_file.exists():
            return []
        
        events = []
        try:
            with open(self._events_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if reverse:
                lines = lines[::-1]
            
            for i, line in enumerate(lines):
                if i < offset:
                    continue
                if limit and len(events) >= limit:
                    break
                
                try:
                    data = json.loads(line.strip())
                    events.append(DebugEvent.from_dict(data))
                except (json.JSONDecodeError, KeyError):
                    continue
                    
        except Exception:
            pass
        
        return events
    
    def read_state(self) -> Optional[dict]:
        """
        Read the current state snapshot.
        
        Returns:
            State dictionary or None if not available
        """
        if not self._state_file.exists():
            return None
        
        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    
    def tail_events(self, count: int = 10) -> list[DebugEvent]:
        """
        Get the last N events.
        
        Args:
            count: Number of events to return
        
        Returns:
            List of most recent events (newest last)
        """
        events = self.read_events(limit=count, reverse=True)
        return events[::-1]  # Reverse to get oldest first
    
    def iter_events(self) -> Iterator[DebugEvent]:
        """
        Iterate over all events.
        
        Yields:
            DebugEvent objects in chronological order
        """
        self.flush()
        
        if not self._events_file.exists():
            return
        
        try:
            with open(self._events_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        yield DebugEvent.from_dict(data)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception:
            pass
    
    def _should_rotate(self) -> bool:
        """Check if file should be rotated."""
        max_size_bytes = self._config.max_file_size_mb * 1024 * 1024
        return (
            self._file_size >= max_size_bytes
            or self._event_count >= self._config.max_events
        )
    
    def _rotate(self) -> None:
        """Rotate the events file."""
        self.flush()
        
        if not self._events_file.exists():
            return
        
        try:
            # Rotate existing files
            for i in range(self._config.rotate_count - 1, 0, -1):
                old_file = self._output_dir / f"events.{i}.jsonl"
                new_file = self._output_dir / f"events.{i + 1}.jsonl"
                if old_file.exists():
                    if i + 1 >= self._config.rotate_count:
                        old_file.unlink()  # Delete oldest
                    else:
                        old_file.rename(new_file)
            
            # Rotate current file
            rotated = self._output_dir / "events.1.jsonl"
            self._events_file.rename(rotated)
            
            # Reset counters
            self._file_size = 0
            # Note: event_count continues to increment
            
        except Exception:
            pass  # Best effort rotation
    
    def get_summary(self) -> dict:
        """
        Get a summary of the debug stream.
        
        Returns:
            Dict with file sizes, event counts, etc.
        """
        self.flush()
        
        summary = {
            "event_count": self._event_count,
            "events_file_size": 0,
            "screenshot_count": 0,
            "snapshot_count": 0,
        }
        
        if self._events_file.exists():
            summary["events_file_size"] = self._events_file.stat().st_size
        
        screenshots_dir = self._output_dir / "screenshots"
        if screenshots_dir.exists():
            summary["screenshot_count"] = len(list(screenshots_dir.glob("*.png")))
        
        snapshots_dir = self._output_dir / "snapshots"
        if snapshots_dir.exists():
            summary["snapshot_count"] = len(list(snapshots_dir.glob("*.html")))
        
        return summary


def format_event_for_display(event: DebugEvent) -> str:
    """
    Format a debug event for terminal display.
    
    Args:
        event: Event to format
    
    Returns:
        Formatted string with colors and layout
    """
    from datetime import datetime
    
    # Format timestamp
    dt = datetime.fromtimestamp(event.ts)
    time_str = dt.strftime("%H:%M:%S.%f")[:-3]
    
    # Color codes
    colors = {
        "console_error": "\033[91m",  # Red
        "js_exception": "\033[91m",
        "network_error": "\033[91m",
        "console_warn": "\033[93m",  # Yellow
        "signal_change": "\033[94m",  # Blue
        "click": "\033[92m",  # Green
        "manual_snapshot": "\033[95m",  # Magenta
    }
    reset = "\033[0m"
    
    color = colors.get(event.type.value, "")
    
    # Format output
    parts = [
        f"[{time_str}]",
        f"[{event.seq:04d}]",
        f"{color}[{event.type.value}]{reset}",
        event.summary,
    ]
    
    if event.source:
        parts.append(f"({event.source})")
    
    if event.screenshot:
        parts.append(f"📷 {event.screenshot}")
    
    return " ".join(parts)

