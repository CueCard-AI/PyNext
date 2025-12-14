"""
Event Capture - Filter and Enrich Browser Events for AI Consumption.

This module processes raw CDP events and transforms them into structured,
AI-friendly debug events with PyNext context.

What Gets Captured:
    - Console messages (log, warn, error, info, debug)
    - Network requests and responses (fetch, XHR, navigation)
    - Click events with element information
    - Signal value changes (via injected tracking)
    - Navigation events (URL changes)
    - JavaScript errors and exceptions
    - Custom PyNext events (component lifecycle, hydration)

Why Filter?
    Raw CDP events are noisy - hundreds per second during page load.
    We filter to keep only actionable events that help debugging.
    AI doesn't need to see every internal browser event.

How It Works:
    1. CDPBridge sends raw CDP events to EventCapture
    2. EventCapture filters based on event type and relevance
    3. Relevant events are enriched with PyNext context
    4. DebugEvent objects are emitted for streaming/storage

Example:
    capture = EventCapture()
    
    def handle_event(event: DebugEvent):
        print(f"[{event.type}] {event.summary}")
    
    capture.on_event(handle_event)
    
    # Connect to CDP bridge
    bridge.on_event(capture.process_cdp_event)
"""

from __future__ import annotations

import time
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
from pathlib import Path


class EventType(str, Enum):
    """Types of debug events we capture."""
    
    # Console
    CONSOLE_LOG = "console_log"
    CONSOLE_WARN = "console_warn"
    CONSOLE_ERROR = "console_error"
    CONSOLE_INFO = "console_info"
    
    # User interaction
    CLICK = "click"
    INPUT = "input"
    SUBMIT = "submit"
    
    # Navigation
    NAVIGATION = "navigation"
    PAGE_LOAD = "page_load"
    
    # Network
    NETWORK_REQUEST = "network_request"
    NETWORK_RESPONSE = "network_response"
    NETWORK_ERROR = "network_error"
    
    # JavaScript
    JS_ERROR = "js_error"
    JS_EXCEPTION = "js_exception"
    
    # PyNext-specific
    SIGNAL_CHANGE = "signal_change"
    SIGNAL_READ = "signal_read"
    EFFECT_RUN = "effect_run"
    COMPONENT_MOUNT = "component_mount"
    COMPONENT_UPDATE = "component_update"
    HYDRATION_START = "hydration_start"
    HYDRATION_COMPLETE = "hydration_complete"
    
    # Manual triggers
    MANUAL_SNAPSHOT = "manual_snapshot"
    
    # Session recording
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    USER_NOTE = "user_note"
    ELEMENT_SELECT = "element_select"
    DRAWING = "drawing"
    
    # System
    DEBUG_START = "debug_start"
    DEBUG_END = "debug_end"


@dataclass
class DebugEvent:
    """
    A structured debug event for AI consumption.
    
    This is the core data structure that gets streamed to events.jsonl.
    It contains all information needed for AI to understand what happened.
    
    Attributes:
        seq: Sequential event number (for ordering)
        ts: Unix timestamp with milliseconds
        type: Event type (from EventType enum)
        data: Event-specific data payload
        summary: Human-readable one-line summary
        screenshot: Path to related screenshot (if any)
        source: Source location (file:line) if applicable
    """
    seq: int
    ts: float
    type: EventType
    data: dict = field(default_factory=dict)
    summary: str = ""
    screenshot: Optional[str] = None
    source: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "seq": self.seq,
            "ts": self.ts,
            "type": self.type.value,
            "data": self.data,
            "summary": self.summary,
        }
        if self.screenshot:
            result["screenshot"] = self.screenshot
        if self.source:
            result["source"] = self.source
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "DebugEvent":
        """Create from dictionary."""
        return cls(
            seq=data["seq"],
            ts=data["ts"],
            type=EventType(data["type"]),
            data=data.get("data", {}),
            summary=data.get("summary", ""),
            screenshot=data.get("screenshot"),
            source=data.get("source"),
        )


class EventCapture:
    """
    Captures and processes browser events for AI debugging.
    
    This class is the central event processor that:
    - Receives raw CDP events from CDPBridge
    - Filters out noise and keeps relevant events
    - Enriches events with PyNext context
    - Emits structured DebugEvent objects
    
    Attributes:
        event_count: Total events captured
        last_event_time: Timestamp of last event
        pynext_context: Tracked PyNext state (signals, components)
    
    Example:
        capture = EventCapture()
        
        # Subscribe to events
        capture.on_event(lambda e: print(e.summary))
        
        # Feed CDP events
        bridge.on_event(capture.process_cdp_event)
    """
    
    # Event types to ignore (too noisy)
    IGNORED_METHODS = {
        "Network.dataReceived",
        "Network.loadingFinished",
        "Network.requestWillBeSentExtraInfo",
        "Network.responseReceivedExtraInfo",
        "DOM.documentUpdated",
        "DOM.childNodeCountUpdated",
        "Page.frameNavigated",
        "Page.frameStartedLoading",
        "Page.frameStoppedLoading",
        "Runtime.consoleAPICalled",  # Duplicate of Console.messageAdded
    }
    
    # Console message sources to ignore
    IGNORED_CONSOLE_SOURCES = {
        "deprecation",
        "intervention",
        "recommendation",
    }
    
    def __init__(self):
        """Initialize the event capture."""
        self._seq = 0
        self._callbacks: list[Callable[[DebugEvent], None]] = []
        self._last_event_time = 0.0
        self._pynext_signals: dict[str, dict] = {}  # signal_id -> info
        self._pynext_components: dict[str, dict] = {}  # component_id -> info
        self._pending_requests: dict[str, dict] = {}  # request_id -> request info
        self._dedup_window = 0.05  # 50ms dedup window
        self._last_events: dict[str, float] = {}  # event_key -> timestamp
    
    @property
    def event_count(self) -> int:
        """Total number of events captured."""
        return self._seq
    
    @property
    def last_event_time(self) -> float:
        """Timestamp of the last event."""
        return self._last_event_time
    
    def on_event(self, callback: Callable[[DebugEvent], None]) -> None:
        """
        Register a callback for captured events.
        
        Args:
            callback: Function that takes a DebugEvent
        """
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[DebugEvent], None]) -> None:
        """Remove a previously registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _emit(self, event: DebugEvent) -> None:
        """Emit an event to all callbacks."""
        self._last_event_time = event.ts
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception:
                pass  # Don't let callback errors break capture
    
    def _next_seq(self) -> int:
        """Get next sequence number."""
        self._seq += 1
        return self._seq
    
    def _should_dedupe(self, key: str) -> bool:
        """Check if event should be deduplicated."""
        now = time.time()
        if key in self._last_events:
            if now - self._last_events[key] < self._dedup_window:
                return True
        self._last_events[key] = now
        return False
    
    def process_cdp_event(self, message: Any) -> Optional[DebugEvent]:
        """
        Process a raw CDP event and emit DebugEvent if relevant.
        
        Args:
            message: CDPMessage from CDPBridge
        
        Returns:
            DebugEvent if event was captured, None if filtered out
        """
        if not hasattr(message, "method") or not message.method:
            return None
        
        method = message.method
        params = message.params or {}
        
        # Skip ignored methods
        if method in self.IGNORED_METHODS:
            return None
        
        # Route to specific handlers
        if method == "Console.messageAdded":
            return self._handle_console(params)
        elif method == "Log.entryAdded":
            return self._handle_log(params)
        elif method == "Network.requestWillBeSent":
            return self._handle_network_request(params)
        elif method == "Network.responseReceived":
            return self._handle_network_response(params)
        elif method == "Network.loadingFailed":
            return self._handle_network_error(params)
        elif method == "Runtime.exceptionThrown":
            return self._handle_exception(params)
        elif method == "Page.loadEventFired":
            return self._handle_page_load(params)
        elif method == "Page.navigatedWithinDocument":
            return self._handle_navigation(params)
        
        return None
    
    def _handle_console(self, params: dict) -> Optional[DebugEvent]:
        """Handle Console.messageAdded event."""
        message = params.get("message", {})
        level = message.get("level", "log")
        text = message.get("text", "")
        source = message.get("source", "")
        url = message.get("url", "")
        line = message.get("line", 0)
        
        # Skip ignored sources
        if source in self.IGNORED_CONSOLE_SOURCES:
            return None
        
        # Skip empty messages
        if not text.strip():
            return None
        
        # Check for PyNext-specific messages
        if text.startswith("[PyNext]"):
            return self._handle_pynext_message(text, url, line)
        
        # Map level to event type
        type_map = {
            "log": EventType.CONSOLE_LOG,
            "warning": EventType.CONSOLE_WARN,
            "error": EventType.CONSOLE_ERROR,
            "info": EventType.CONSOLE_INFO,
            "debug": EventType.CONSOLE_LOG,
        }
        event_type = type_map.get(level, EventType.CONSOLE_LOG)
        
        # Dedupe rapid repeated messages
        dedup_key = f"console:{level}:{text[:100]}"
        if self._should_dedupe(dedup_key):
            return None
        
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=event_type,
            data={
                "level": level,
                "text": text,
                "url": url,
                "line": line,
            },
            summary=f"console.{level}: {text[:100]}",
            source=f"{Path(url).name}:{line}" if url and line else None,
        )
        
        self._emit(event)
        return event
    
    def _handle_log(self, params: dict) -> Optional[DebugEvent]:
        """Handle Log.entryAdded event."""
        entry = params.get("entry", {})
        level = entry.get("level", "info")
        text = entry.get("text", "")
        source = entry.get("source", "")
        url = entry.get("url", "")
        line = entry.get("lineNumber", 0)
        
        # Only capture errors and warnings
        if level not in ("error", "warning"):
            return None
        
        type_map = {
            "warning": EventType.CONSOLE_WARN,
            "error": EventType.CONSOLE_ERROR,
        }
        event_type = type_map.get(level, EventType.CONSOLE_LOG)
        
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=event_type,
            data={
                "level": level,
                "text": text,
                "source": source,
                "url": url,
                "line": line,
            },
            summary=f"{level}: {text[:100]}",
            source=f"{Path(url).name}:{line}" if url and line else None,
        )
        
        self._emit(event)
        return event
    
    def _handle_pynext_message(
        self,
        text: str,
        url: str,
        line: int,
    ) -> Optional[DebugEvent]:
        """Handle PyNext-specific console messages."""
        # Parse PyNext message format: [PyNext] TYPE: DATA
        match = re.match(r"\[PyNext\]\s*(\w+):\s*(.*)", text)
        if not match:
            return None
        
        msg_type = match.group(1).upper()
        msg_data = match.group(2)
        
        if msg_type == "SIGNAL":
            # Signal change: [PyNext] SIGNAL: view_mode = kanban (was: list)
            sig_match = re.match(r"(\w+)\s*=\s*(.+?)\s*\(was:\s*(.+?)\)", msg_data)
            if sig_match:
                return self._emit_signal_change(
                    signal_name=sig_match.group(1),
                    new_value=sig_match.group(2),
                    old_value=sig_match.group(3),
                    source=f"{Path(url).name}:{line}" if url else None,
                )
        
        elif msg_type == "HYDRATION":
            return self._emit_event(
                EventType.HYDRATION_COMPLETE,
                {"message": msg_data},
                f"Hydration: {msg_data}",
            )
        
        elif msg_type == "EFFECT":
            return self._emit_event(
                EventType.EFFECT_RUN,
                {"message": msg_data},
                f"Effect: {msg_data}",
            )
        
        elif msg_type == "SESSION_START":
            # Session started: [PyNext] SESSION_START: {intent}
            return self._emit_event(
                EventType.SESSION_START,
                {"intent": msg_data.strip()},
                f"Session started: {msg_data.strip()}",
            )
        
        elif msg_type == "SESSION_END":
            # Session ended: [PyNext] SESSION_END: {outcome}
            return self._emit_event(
                EventType.SESSION_END,
                {"outcome": msg_data.strip()},
                f"Session ended: {msg_data.strip()}",
            )
        
        elif msg_type == "NOTE":
            # User note: [PyNext] NOTE: {text}
            return self._emit_event(
                EventType.USER_NOTE,
                {"text": msg_data.strip()},
                f"Note: {msg_data.strip()}",
            )
        
        elif msg_type == "SNAPSHOT":
            # Manual snapshot: [PyNext] SNAPSHOT: {note}
            return self._emit_event(
                EventType.MANUAL_SNAPSHOT,
                {"note": msg_data.strip()},
                f"Snapshot: {msg_data.strip()}",
            )
        
        elif msg_type == "CLICK":
            # Click event: [PyNext] CLICK: {selector}
            return self._emit_event(
                EventType.CLICK,
                {"selector": msg_data.strip()},
                f"Click: {msg_data.strip()}",
            )
        
        elif msg_type == "ELEMENT_SELECT":
            # Element selected in inspect mode: [PyNext] ELEMENT_SELECT: {json}
            try:
                import json
                element_data = json.loads(msg_data.strip())
                return self._emit_event(
                    EventType.ELEMENT_SELECT,
                    element_data,
                    f"Element selected: {element_data.get('selector', 'unknown')}",
                )
            except (json.JSONDecodeError, ValueError):
                return self._emit_event(
                    EventType.ELEMENT_SELECT,
                    {"raw": msg_data.strip()},
                    f"Element selected: {msg_data.strip()[:50]}",
                )
        
        elif msg_type == "DRAWING":
            # Drawing annotation: [PyNext] DRAWING: {json}
            try:
                import json
                drawing_data = json.loads(msg_data.strip())
                drawing_type = drawing_data.get("type", "unknown")
                return self._emit_event(
                    EventType.DRAWING,
                    drawing_data,
                    f"Drawing: {drawing_type}",
                )
            except (json.JSONDecodeError, ValueError):
                return self._emit_event(
                    EventType.DRAWING,
                    {"raw": msg_data.strip()},
                    f"Drawing annotation",
                )
        
        return None
    
    def _handle_network_request(self, params: dict) -> Optional[DebugEvent]:
        """Handle Network.requestWillBeSent event."""
        request = params.get("request", {})
        request_id = params.get("requestId", "")
        url = request.get("url", "")
        method = request.get("method", "GET")
        
        # Skip data URLs and extensions
        if url.startswith("data:") or url.startswith("chrome-extension:"):
            return None
        
        # Skip common static assets (images, fonts, etc.)
        if any(url.endswith(ext) for ext in [".png", ".jpg", ".gif", ".woff", ".woff2", ".ico"]):
            return None
        
        # Store for correlation with response
        self._pending_requests[request_id] = {
            "url": url,
            "method": method,
            "start_time": time.time(),
        }
        
        # Only emit for API calls (fetch, XHR to API endpoints)
        if "/api/" in url or "/_next/" not in url:
            event = DebugEvent(
                seq=self._next_seq(),
                ts=time.time(),
                type=EventType.NETWORK_REQUEST,
                data={
                    "request_id": request_id,
                    "url": url,
                    "method": method,
                },
                summary=f"{method} {url}",
            )
            self._emit(event)
            return event
        
        return None
    
    def _handle_network_response(self, params: dict) -> Optional[DebugEvent]:
        """Handle Network.responseReceived event."""
        request_id = params.get("requestId", "")
        response = params.get("response", {})
        url = response.get("url", "")
        status = response.get("status", 0)
        
        # Get original request info
        request_info = self._pending_requests.pop(request_id, {})
        
        # Only emit for API calls
        if "/api/" not in url and "/_next/" in url:
            return None
        
        duration_ms = (time.time() - request_info.get("start_time", time.time())) * 1000
        
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=EventType.NETWORK_RESPONSE,
            data={
                "request_id": request_id,
                "url": url,
                "status": status,
                "duration_ms": round(duration_ms, 2),
            },
            summary=f"{status} {url} ({duration_ms:.0f}ms)",
        )
        
        self._emit(event)
        return event
    
    def _handle_network_error(self, params: dict) -> Optional[DebugEvent]:
        """Handle Network.loadingFailed event."""
        request_id = params.get("requestId", "")
        error_text = params.get("errorText", "Unknown error")
        
        request_info = self._pending_requests.pop(request_id, {})
        url = request_info.get("url", "Unknown URL")
        
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=EventType.NETWORK_ERROR,
            data={
                "request_id": request_id,
                "url": url,
                "error": error_text,
            },
            summary=f"Network error: {url} - {error_text}",
        )
        
        self._emit(event)
        return event
    
    def _handle_exception(self, params: dict) -> Optional[DebugEvent]:
        """Handle Runtime.exceptionThrown event."""
        exception_details = params.get("exceptionDetails", {})
        exception = exception_details.get("exception", {})
        
        text = exception.get("description", "") or exception_details.get("text", "Unknown error")
        url = exception_details.get("url", "")
        line = exception_details.get("lineNumber", 0)
        column = exception_details.get("columnNumber", 0)
        
        # Get stack trace if available
        stack_trace = exception_details.get("stackTrace", {})
        call_frames = stack_trace.get("callFrames", [])
        stack = []
        for frame in call_frames[:5]:  # Limit to 5 frames
            stack.append({
                "function": frame.get("functionName", "(anonymous)"),
                "url": frame.get("url", ""),
                "line": frame.get("lineNumber", 0),
                "column": frame.get("columnNumber", 0),
            })
        
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=EventType.JS_EXCEPTION,
            data={
                "text": text,
                "url": url,
                "line": line,
                "column": column,
                "stack": stack,
            },
            summary=f"Error: {text[:100]}",
            source=f"{Path(url).name}:{line}:{column}" if url else None,
        )
        
        self._emit(event)
        return event
    
    def _handle_page_load(self, params: dict) -> Optional[DebugEvent]:
        """Handle Page.loadEventFired event."""
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=EventType.PAGE_LOAD,
            data={
                "timestamp": params.get("timestamp", 0),
            },
            summary="Page loaded",
        )
        
        self._emit(event)
        return event
    
    def _handle_navigation(self, params: dict) -> Optional[DebugEvent]:
        """Handle Page.navigatedWithinDocument event."""
        url = params.get("url", "")
        
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=EventType.NAVIGATION,
            data={
                "url": url,
            },
            summary=f"Navigated to {url}",
        )
        
        self._emit(event)
        return event
    
    def _emit_signal_change(
        self,
        signal_name: str,
        new_value: Any,
        old_value: Any,
        source: Optional[str] = None,
        signal_id: Optional[str] = None,
    ) -> DebugEvent:
        """Emit a signal change event."""
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=EventType.SIGNAL_CHANGE,
            data={
                "signal_id": signal_id or f"sig_{signal_name}",
                "signal_name": signal_name,
                "old_value": old_value,
                "new_value": new_value,
            },
            summary=f"Signal {signal_name}: {old_value} → {new_value}",
            source=source,
        )
        
        self._emit(event)
        return event
    
    def _emit_event(
        self,
        event_type: EventType,
        data: dict,
        summary: str,
        source: Optional[str] = None,
    ) -> DebugEvent:
        """Emit a generic event."""
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=event_type,
            data=data,
            summary=summary,
            source=source,
        )
        
        self._emit(event)
        return event
    
    def emit_click(
        self,
        element: dict,
        x: int,
        y: int,
    ) -> DebugEvent:
        """
        Emit a click event.
        
        Called by the injected JS when user clicks an element.
        
        Args:
            element: Element info (tagName, id, classes, selector)
            x: Click X coordinate
            y: Click Y coordinate
        """
        selector = element.get("selector", "unknown")
        tag = element.get("tagName", "element")
        
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=EventType.CLICK,
            data={
                "element": element,
                "x": x,
                "y": y,
            },
            summary=f"Click: {selector}",
        )
        
        self._emit(event)
        return event
    
    def emit_manual_snapshot(self, note: str = "") -> DebugEvent:
        """
        Emit a manual snapshot event.
        
        Called when user triggers a manual screenshot.
        
        Args:
            note: Optional user-provided note
        """
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=EventType.MANUAL_SNAPSHOT,
            data={
                "note": note,
            },
            summary=f"Manual snapshot: {note}" if note else "Manual snapshot",
        )
        
        self._emit(event)
        return event
    
    def emit_debug_start(self) -> DebugEvent:
        """Emit debug session start event."""
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=EventType.DEBUG_START,
            data={},
            summary="Debug session started",
        )
        
        self._emit(event)
        return event
    
    def emit_debug_end(self) -> DebugEvent:
        """Emit debug session end event."""
        event = DebugEvent(
            seq=self._next_seq(),
            ts=time.time(),
            type=EventType.DEBUG_END,
            data={
                "total_events": self._seq,
            },
            summary=f"Debug session ended ({self._seq} events)",
        )
        
        self._emit(event)
        return event
    
    def register_signal(
        self,
        signal_id: str,
        signal_name: str,
        component: Optional[str] = None,
        line: Optional[int] = None,
    ) -> None:
        """
        Register a PyNext signal for tracking.
        
        Called during hydration when signals are initialized.
        
        Args:
            signal_id: Unique signal ID (e.g., "sig_124")
            signal_name: Human-readable name (e.g., "view_mode")
            component: Source component file
            line: Line number in source
        """
        self._pynext_signals[signal_id] = {
            "name": signal_name,
            "component": component,
            "line": line,
        }
    
    def get_signal_info(self, signal_id: str) -> Optional[dict]:
        """Get registered signal information."""
        return self._pynext_signals.get(signal_id)

