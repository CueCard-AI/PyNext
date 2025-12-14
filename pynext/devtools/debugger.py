"""
AI Debugger - Main Orchestrator for PyNext AI DevTools.

This is the main entry point that coordinates all devtools components:
- ChromeLauncher: Finds and launches Chrome with CDP
- CDPBridge: WebSocket connection to Chrome
- EventCapture: Filters and enriches browser events
- ScreenshotCapture: Takes screenshots on events
- DebugStream: Writes events to files
- JSInjector: Injects PyNext tracking code

Usage:
    # In pynext dev command
    if args.ai_debug:
        debugger = AIDebugger()
        await debugger.start(url="http://localhost:3000")
        
        # Runs until interrupted
        await debugger.wait()
        
        # Cleanup
        await debugger.stop()

Files Created:
    .pynext/debug/
    ├── events.jsonl    # All debug events
    ├── state.json      # Current state snapshot
    ├── screenshots/    # Screenshots on events
    └── snapshots/      # DOM HTML snapshots
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any

from pynext.devtools.bridge import CDPBridge, CDPMessage
from pynext.devtools.launcher import ChromeLauncher
from pynext.devtools.capture import EventCapture, DebugEvent, EventType
from pynext.devtools.screenshot import ScreenshotCapture
from pynext.devtools.stream import DebugStream, StreamConfig
from pynext.devtools.injector import JSInjector
from pynext.devtools.recorder import SessionRecorder, RecordedAction, ActionType, ElementInfo, SignalSnapshot


class DebugMode(Enum):
    """
    Debug mode determines what data is captured and analyzed.
    
    Modes:
        APP: For app developers debugging their application code.
             Captures component state, user actions, app-level errors.
             Hides PyNext internals.
        
        CORE: For PyNext framework developers debugging the framework.
              Captures hydration steps, signal implementation, runtime traces.
              Shows PyNext internals.
        
        EVERYTHING: Full diagnostic capture for complex cross-layer bugs.
                    Captures both app and framework layers plus browser internals.
    """
    APP = "app"
    CORE = "core"
    EVERYTHING = "everything"
    
    @classmethod
    def from_string(cls, value: str) -> "DebugMode":
        """Parse mode from string, defaulting to APP."""
        value = value.lower().strip() if value else "app"
        try:
            return cls(value)
        except ValueError:
            return cls.APP
    
    @property
    def capture_app_context(self) -> bool:
        """Whether to capture app-level context."""
        return self in (DebugMode.APP, DebugMode.EVERYTHING)
    
    @property
    def capture_framework_internals(self) -> bool:
        """Whether to capture PyNext framework internals."""
        return self in (DebugMode.CORE, DebugMode.EVERYTHING)
    
    @property
    def capture_browser_internals(self) -> bool:
        """Whether to capture browser-level internals."""
        return self == DebugMode.EVERYTHING


@dataclass
class DebugConfig:
    """
    Configuration for AI Debugger.
    
    Attributes:
        mode: Debug mode (app/core/everything)
        output_dir: Directory for debug output files
        debug_port: Chrome DevTools Protocol port
        headless: Run Chrome in headless mode
        window_size: Browser window dimensions
        take_screenshots: Enable screenshot capture
        take_snapshots: Enable DOM snapshot capture
        screenshot_on_click: Capture on click events
        screenshot_on_signal: Capture on signal changes
        screenshot_on_error: Capture on errors
        screenshot_interval_ms: Time-based screenshot interval (0 to disable)
        max_events: Maximum events to store
        api_key: Anthropic API key for AI analysis (optional)
        enable_ai_analysis: Whether to run AI analysis on session end
    """
    mode: DebugMode = DebugMode.APP
    output_dir: Path = field(default_factory=lambda: Path(".pynext/debug"))
    debug_port: int = 9222
    headless: bool = False
    window_size: tuple[int, int] = (1280, 800)
    take_screenshots: bool = True
    take_snapshots: bool = True
    screenshot_on_click: bool = True
    screenshot_on_signal: bool = True
    screenshot_on_error: bool = True
    screenshot_interval_ms: int = 150  # Time-based screenshots every 150ms
    max_events: int = 10000
    api_key: Optional[str] = None  # Anthropic API key for Stage 1 AI
    enable_ai_analysis: bool = True
    
    def __post_init__(self):
        self.output_dir = Path(self.output_dir)
        if isinstance(self.mode, str):
            self.mode = DebugMode.from_string(self.mode)
    
    @property
    def sessions_dir(self) -> Path:
        """Directory for recording sessions."""
        return self.output_dir / "sessions"
    
    def get_mode_description(self) -> str:
        """Get human-readable mode description."""
        descriptions = {
            DebugMode.APP: "App Mode - Debugging your application code",
            DebugMode.CORE: "Core Mode - Debugging PyNext framework internals",
            DebugMode.EVERYTHING: "Everything Mode - Full diagnostic capture",
        }
        return descriptions.get(self.mode, "Unknown mode")


class AIDebugger:
    """
    Main orchestrator for PyNext AI DevTools.
    
    This class coordinates all debugging components to provide:
    - Automatic Chrome launch with CDP
    - Event capture and enrichment
    - Screenshot/snapshot capture
    - File streaming for AI consumption
    
    Attributes:
        config: Debug configuration
        running: Whether debugging is active
        event_count: Total events captured
    
    Example:
        debugger = AIDebugger()
        
        # Start debugging
        await debugger.start("http://localhost:3000")
        
        # Get current state
        state = await debugger.get_state()
        print(f"Signals: {state['signals']}")
        
        # Take manual snapshot
        await debugger.snapshot("Checking modal")
        
        # Stop
        await debugger.stop()
    """
    
    def __init__(self, config: Optional[DebugConfig] = None):
        """
        Initialize the AI Debugger.
        
        Args:
            config: Optional configuration
        """
        self.config = config or DebugConfig()
        
        # Components (initialized on start)
        self._launcher: Optional[ChromeLauncher] = None
        self._bridge: Optional[CDPBridge] = None
        self._capture: Optional[EventCapture] = None
        self._screenshots: Optional[ScreenshotCapture] = None
        self._stream: Optional[DebugStream] = None
        self._injector: Optional[JSInjector] = None
        self._recorder: Optional[SessionRecorder] = None
        
        # State
        self._running = False
        self._stop_event: Optional[asyncio.Event] = None
        self._url: str = ""
        
        # Session recording state
        self._screenshot_task: Optional[asyncio.Task] = None
    
    @property
    def _session_active(self) -> bool:
        """Check if a recording session is active."""
        return self._recorder is not None and self._recorder.is_recording
    
    @property
    def running(self) -> bool:
        """Check if debugging is active."""
        return self._running
    
    @property
    def event_count(self) -> int:
        """Total number of events captured."""
        return self._capture.event_count if self._capture else 0
    
    async def start(
        self,
        url: str = "http://localhost:3000",
        clear_previous: bool = True,
    ) -> None:
        """
        Start the AI debugger.
        
        This will:
        1. Create output directory
        2. Launch Chrome with CDP
        3. Connect to Chrome
        4. Set up event capture
        5. Inject tracking script
        6. Take initial screenshot
        
        Args:
            url: URL to open in Chrome
            clear_previous: Clear previous debug files
        """
        if self._running:
            return
        
        self._url = url
        self._stop_event = asyncio.Event()
        
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize stream
        stream_config = StreamConfig(max_events=self.config.max_events)
        self._stream = DebugStream(self.config.output_dir, stream_config)
        
        if clear_previous:
            self._stream.clear()
        
        # Initialize capture
        self._capture = EventCapture()
        self._capture.on_event(self._on_event)
        
        # Launch Chrome
        print(f"[PyNext AI Debug] Launching Chrome...")
        self._launcher = ChromeLauncher(debug_port=self.config.debug_port)
        ws_url = await self._launcher.launch(
            url=url,
            headless=self.config.headless,
            window_size=self.config.window_size,
        )
        
        # Connect to Chrome
        print(f"[PyNext AI Debug] Connecting to Chrome...")
        self._bridge = CDPBridge()
        await self._bridge.connect(ws_url)
        await self._bridge.enable_domains()
        
        # Set up CDP event handler
        self._bridge.on_event(self._on_cdp_event)
        
        # Initialize screenshot capture
        if self.config.take_screenshots:
            self._screenshots = ScreenshotCapture(
                self._bridge,
                self.config.output_dir,
                take_snapshots=self.config.take_snapshots,
            )
        
        # Initialize injector
        self._injector = JSInjector(self._bridge)
        
        # Wait a moment for page to load
        await asyncio.sleep(1.0)
        
        # Inject tracking script
        print(f"[PyNext AI Debug] Injecting tracking hooks...")
        await self._injector.inject()
        
        # Initialize session recorder
        self._recorder = SessionRecorder(
            output_dir=self.config.output_dir,
            mode=self.config.mode.value,
        )
        
        # Take initial screenshot
        if self._screenshots:
            await self._screenshots.capture_initial()
        
        # Emit start event
        self._capture.emit_debug_start()
        
        self._running = True
        
        print(f"[PyNext AI Debug] Ready!")
        print(f"[PyNext AI Debug] Events: {self.config.output_dir}/events.jsonl")
        print(f"[PyNext AI Debug] Screenshots: {self.config.output_dir}/screenshots/")
        print(f"[PyNext AI Debug] Manual snapshot: Ctrl+Shift+S in browser")
    
    async def stop(self) -> None:
        """
        Stop the AI debugger.
        
        This will:
        1. Emit end event
        2. Flush stream
        3. Disconnect from Chrome
        4. Shut down Chrome
        5. Signal the stop event
        """
        if not self._running:
            return
        
        self._running = False
        
        # Emit end event
        if self._capture:
            self._capture.emit_debug_end()
        
        # Flush stream
        if self._stream:
            self._stream.flush()
        
        # Disconnect from Chrome
        if self._bridge:
            await self._bridge.disconnect()
        
        # Shut down Chrome
        if self._launcher:
            self._launcher.shutdown()
        
        # Signal stop event to unblock wait()
        if self._stop_event:
            self._stop_event.set()
        
        print(f"[PyNext AI Debug] Stopped. {self.event_count} events captured.")
        
        # Signal stop
        if self._stop_event:
            self._stop_event.set()
        
        print(f"[PyNext AI Debug] Stopped. {self.event_count} events captured.")
    
    async def wait(self) -> None:
        """
        Wait until stop() is called or interrupted.
        
        This blocks until debugging is stopped via:
        - Calling stop()
        - Ctrl+C interrupt
        """
        if not self._stop_event:
            return
        
        loop = asyncio.get_running_loop()
        shutdown_requested = False
        
        # Set up signal handler for graceful shutdown
        def handle_signal(sig, frame):
            nonlocal shutdown_requested
            if shutdown_requested:
                # Second interrupt - force exit
                print("\n[PyNext AI Debug] Forced exit.")
                sys.exit(1)
            
            shutdown_requested = True
            print("\n[PyNext AI Debug] Shutting down... (press Ctrl+C again to force)")
            # Use call_soon_threadsafe to schedule stop() from signal handler
            loop.call_soon_threadsafe(lambda: asyncio.create_task(self.stop()))
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        
        await self._stop_event.wait()
    
    def _on_cdp_event(self, message: CDPMessage) -> None:
        """Handle raw CDP event."""
        if self._capture:
            event = self._capture.process_cdp_event(message)
            # Screenshots for certain events are handled in _on_event
    
    def _on_event(self, event: DebugEvent) -> None:
        """Handle captured debug event."""
        # Write to stream
        if self._stream:
            self._stream.write_event(event)
        
        # Handle session lifecycle events
        if event.type == EventType.SESSION_START:
            intent = event.data.get("intent", "")
            self._start_session(intent)
        
        elif event.type == EventType.SESSION_END:
            outcome = event.data.get("outcome", "")
            session_path = self._end_session(outcome)
            if session_path:
                asyncio.create_task(self._run_ai_analysis(session_path))
        
        elif event.type == EventType.USER_NOTE and self._session_active:
            # Take screenshot on note during session
            asyncio.create_task(self._capture_on_note(event.data.get("text", "")))
        
        elif event.type == EventType.MANUAL_SNAPSHOT and self._session_active:
            # Take screenshot on manual snapshot during session
            asyncio.create_task(self._capture_on_snapshot(event.data.get("note", "")))
        
        elif event.type == EventType.CLICK and self._session_active:
            # Take before/after screenshots on click during session
            asyncio.create_task(self._capture_on_click(event.data))
        
        elif event.type == EventType.SIGNAL_CHANGE and self._session_active:
            # Take screenshot on signal change during session
            signal_name = event.data.get("signal_name", "signal")
            new_value = str(event.data.get("new_value", ""))
            asyncio.create_task(self._capture_on_signal(signal_name, new_value))
        
        elif event.type in (EventType.JS_EXCEPTION, EventType.CONSOLE_ERROR) and self._session_active:
            # Take screenshot on error during session and add to timeline
            error_msg = event.data.get("text", "error")
            asyncio.create_task(self._capture_on_error(error_msg, event.data))
        
        elif event.type == EventType.ELEMENT_SELECT and self._session_active:
            # Element selected in inspect mode - add to timeline
            asyncio.create_task(self._capture_on_inspect(event.data))
        
        elif event.type == EventType.DRAWING and self._session_active:
            # Drawing annotation - add to timeline
            asyncio.create_task(self._capture_on_drawing(event.data))
        
        # Take screenshot for certain events (outside of session handling)
        elif self._screenshots and not self._session_active:
            asyncio.create_task(self._maybe_screenshot(event))
        
        # Update state file
        if self._stream:
            asyncio.create_task(self._update_state())
    
    async def _maybe_screenshot(self, event: DebugEvent) -> None:
        """Take screenshot if appropriate for this event."""
        if not self._screenshots:
            return
        
        result = None
        
        if event.type == EventType.CLICK and self.config.screenshot_on_click:
            result = await self._screenshots.capture_click(
                event.data.get("element", {}),
                event.data.get("x", 0),
                event.data.get("y", 0),
            )
        
        elif event.type == EventType.SIGNAL_CHANGE and self.config.screenshot_on_signal:
            result = await self._screenshots.capture_signal_change(
                event.data.get("signal_name", "signal"),
                str(event.data.get("new_value", "")),
            )
        
        elif event.type in (EventType.JS_EXCEPTION, EventType.CONSOLE_ERROR) and self.config.screenshot_on_error:
            result = await self._screenshots.capture_error(
                event.data.get("text", "error")[:50],
            )
        
        elif event.type == EventType.MANUAL_SNAPSHOT:
            result = await self._screenshots.capture_manual(
                event.data.get("note", ""),
            )
        
        elif event.type == EventType.NAVIGATION:
            result = await self._screenshots.capture_navigation(
                event.data.get("url", ""),
            )
        
        # Update event with screenshot path
        if result and result.screenshot_path:
            event.screenshot = str(result.screenshot_path.relative_to(self.config.output_dir))
    
    async def _update_state(self) -> None:
        """Update the state.json file."""
        if not self._stream or not self._injector:
            return
        
        try:
            # Get state from browser
            browser_state = await self._injector.get_state()
            
            state = {
                "url": self._url,
                "event_count": self.event_count,
                "running": self._running,
            }
            
            if browser_state:
                state.update(browser_state)
            
            self._stream.write_state(state)
            
        except Exception:
            pass  # Best effort
    
    async def snapshot(self, note: str = "") -> Optional[Path]:
        """
        Take a manual snapshot.
        
        Args:
            note: Optional note/label for the snapshot
        
        Returns:
            Path to screenshot file
        """
        if not self._running or not self._screenshots:
            return None
        
        # Emit event
        self._capture.emit_manual_snapshot(note)
        
        # Take screenshot
        result = await self._screenshots.capture_manual(note)
        
        return result.screenshot_path if result else None
    
    async def get_state(self) -> dict:
        """
        Get current debug state.
        
        Returns:
            Dict with url, signals, lastClick, eventCount, etc.
        """
        state = {
            "url": self._url,
            "event_count": self.event_count,
            "running": self._running,
        }
        
        if self._injector:
            browser_state = await self._injector.get_state()
            if browser_state:
                state.update(browser_state)
        
        return state
    
    async def get_signal(self, signal_id: str) -> any:
        """
        Get current value of a signal.
        
        Args:
            signal_id: Signal ID
        
        Returns:
            Current signal value
        """
        if self._injector:
            return await self._injector.get_signal_value(signal_id)
        return None
    
    async def set_signal(self, signal_id: str, value: any) -> bool:
        """
        Set a signal value for testing.
        
        Args:
            signal_id: Signal ID
            value: New value
        
        Returns:
            True if set successfully
        """
        if self._injector:
            return await self._injector.set_signal_value(signal_id, value)
        return False
    
    async def list_signals(self) -> list[dict]:
        """
        List all signals in the page.
        
        Returns:
            List of signal info dicts
        """
        if self._injector:
            return await self._injector.list_signals()
        return []
    
    def read_events(self, limit: int = 50) -> list[DebugEvent]:
        """
        Read recent events.
        
        Args:
            limit: Maximum number of events
        
        Returns:
            List of recent events (newest first)
        """
        if self._stream:
            return self._stream.read_events(limit=limit)
        return []
    
    def get_summary(self) -> dict:
        """
        Get a summary of the debug session.
        
        Returns:
            Dict with event counts, file sizes, etc.
        """
        summary = {
            "running": self._running,
            "url": self._url,
            "event_count": self.event_count,
        }
        
        if self._stream:
            summary.update(self._stream.get_summary())
        
        return summary
    
    # =========================================================================
    # Session Recording (Time-based + Event-based screenshots)
    # =========================================================================
    
    def _start_session(self, intent: str) -> None:
        """
        Start a recording session with time-based screenshots.
        
        Called when SESSION_START event is detected from browser.
        Uses SessionRecorder for rich data capture.
        """
        if not self._recorder:
            print(f"[PyNext AI Debug] Recorder not initialized")
            return
        
        if self._recorder.is_recording:
            print(f"[PyNext AI Debug] Session already active, ignoring start")
            return
        
        # Start session via recorder
        session = self._recorder.start_session(intent)
        
        # Capture initial hydration map
        asyncio.create_task(self._capture_hydration_map())
        
        # Start time-based screenshot loop
        self._screenshot_task = asyncio.create_task(self._screenshot_loop())
        
        print(f"[PyNext AI Debug] Session started: {intent}")
        print(f"[PyNext AI Debug] Session dir: {self._recorder._session_dir}")
    
    def _end_session(self, outcome: str) -> Optional[Path]:
        """
        End the recording session.
        
        Called when SESSION_END event is detected from browser.
        Returns the session directory for AI analysis.
        """
        if not self._recorder or not self._recorder.is_recording:
            print(f"[PyNext AI Debug] No active session to end")
            return None
        
        # Stop screenshot loop
        if self._screenshot_task:
            self._screenshot_task.cancel()
            self._screenshot_task = None
        
        # Get session info before ending
        session = self._recorder.current_session
        frame_count = session.frame_count if session else 0
        action_count = session.action_count if session else 0
        
        # End session via recorder (saves all files)
        session_dir = self._recorder.end_session(outcome)
        
        print(f"[PyNext AI Debug] Session ended: {outcome}")
        print(f"[PyNext AI Debug] {frame_count} frames, {action_count} actions")
        
        return session_dir
    
    async def _screenshot_loop(self) -> None:
        """
        Time-based screenshot capture loop (every 150ms).
        
        Runs continuously while session is active.
        Creates complete visual timeline in all_frames/ directory.
        """
        interval = self.config.screenshot_interval_ms / 1000.0  # Convert to seconds
        
        print(f"[PyNext AI Debug] Screenshot loop started (every {self.config.screenshot_interval_ms}ms)")
        
        frame_count = 0
        while self._running and self._recorder and self._recorder.is_recording:
            try:
                frame_count += 1
                session = self._recorder.current_session
                if session:
                    session.frame_count = frame_count
                
                if self._screenshots and self._recorder._session_dir:
                    await self._screenshots.capture_frame(
                        frame_number=frame_count,
                        session_dir=self._recorder._session_dir,
                    )
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log but continue
                print(f"[PyNext AI Debug] Screenshot error: {e}")
                await asyncio.sleep(interval)
        
        print(f"[PyNext AI Debug] Screenshot loop stopped after {frame_count} frames")
    
    async def _capture_hydration_map(self) -> None:
        """Capture initial hydration map for the session."""
        if not self._recorder or not self._recorder.current_session:
            return
        
        try:
            if self._injector:
                state = await self._injector.get_state()
                if state and self._recorder.current_session:
                    self._recorder.current_session.hydration_map = {
                        "url": state.get("url"),
                        "signals": state.get("signals", {}),
                        "title": state.get("title"),
                    }
        except Exception as e:
            print(f"[PyNext AI Debug] Failed to capture hydration map: {e}")
    
    async def _capture_on_click(self, click_data: dict) -> None:
        """Capture before/after screenshots on click during session."""
        if not self._recorder or not self._recorder.is_recording:
            return
        
        session = self._recorder.current_session
        session_dir = self._recorder._session_dir
        if not session or not session_dir:
            return
        
        action_index = session.action_count + 1
        selector = click_data.get("selector", "unknown")
        
        # Capture signal state BEFORE
        signals_before = await self._get_signal_snapshot()
        
        # BEFORE screenshot
        before_path = None
        if self._screenshots:
            before_path = await self._screenshots.capture_action(
                action_type="click",
                phase="before",
                context=selector,
                session_dir=session_dir,
                action_index=action_index,
            )
        
        # Wait for DOM to update
        await asyncio.sleep(0.1)
        
        # Capture signal state AFTER
        signals_after = await self._get_signal_snapshot()
        
        # AFTER screenshot
        after_path = None
        if self._screenshots:
            after_path = await self._screenshots.capture_action(
                action_type="click",
                phase="after",
                context=selector,
                session_dir=session_dir,
                action_index=action_index,
            )
        
        # Calculate changed signals
        signals_changed = self._get_changed_signals(signals_before, signals_after)
        
        # Record the action with full context
        action = RecordedAction(
            action_type=ActionType.CLICK,
            timestamp_ms=int((time.time() - session.start_time) * 1000),
            frame_number=session.frame_count,
            target=ElementInfo(
                selector=selector,
                tag_name=click_data.get("tagName", "unknown"),
                id=click_data.get("id"),
                text_content=click_data.get("textContent"),
            ),
            signals=SignalSnapshot(
                signals_before=signals_before,  # Fixed: was 'before'
                signals_after=signals_after,    # Fixed: was 'after'
            ) if signals_before or signals_after else None,
            screenshot_before=str(before_path) if before_path else None,
            screenshot_after=str(after_path) if after_path else None,
        )
        self._recorder.record_action(action)
        
        # ALSO: Append to unified timeline
        session.append_event(
            event_type="click",
            data={
                "selector": selector,
                "tagName": click_data.get("tagName"),
                "id": click_data.get("id"),
                "textContent": click_data.get("textContent"),
                "signals_changed": signals_changed,
                "signals_before": signals_before,
                "signals_after": signals_after,
            },
            screenshot=str(after_path) if after_path else None,
        )
    
    async def _capture_on_note(self, note_text: str) -> None:
        """Capture screenshot on user note during session."""
        if not self._recorder or not self._recorder.is_recording:
            return
        
        session = self._recorder.current_session
        session_dir = self._recorder._session_dir
        if not session or not session_dir:
            return
        
        # Add note to session (old mechanism)
        session.add_note(note_text)
        
        # Take screenshot
        screenshot_path = None
        if self._screenshots:
            screenshot_path = await self._screenshots.capture_action(
                action_type="note",
                phase="at",
                context=note_text,
                session_dir=session_dir,
                action_index=session.action_count + 1,
            )
        
        # Append to unified timeline
        session.append_event(
            event_type="note",
            data={"text": note_text},
            screenshot=str(screenshot_path) if screenshot_path else None,
        )
    
    async def _capture_on_snapshot(self, note: str) -> None:
        """Capture screenshot on manual snapshot during session."""
        if not self._recorder or not self._recorder.is_recording:
            return
        
        session = self._recorder.current_session
        session_dir = self._recorder._session_dir
        if not session or not session_dir:
            return
        
        # Take screenshot
        screenshot_path = None
        if self._screenshots:
            screenshot_path = await self._screenshots.capture_action(
                action_type="snapshot",
                phase="at",
                context=note,
                session_dir=session_dir,
                action_index=session.action_count + 1,
            )
        
        # Append to unified timeline
        session.append_event(
            event_type="snapshot",
            data={"note": note},
            screenshot=str(screenshot_path) if screenshot_path else None,
        )
    
    async def _capture_on_signal(self, signal_name: str, new_value: str) -> None:
        """Capture screenshot on signal change during session."""
        if not self._recorder or not self._recorder.is_recording:
            return
        
        session = self._recorder.current_session
        session_dir = self._recorder._session_dir
        if not session or not session_dir:
            return
        
        context = f"{signal_name}_{new_value}"[:30]
        
        screenshot_path = None
        if self._screenshots:
            screenshot_path = await self._screenshots.capture_action(
                action_type="signal",
                phase="at",
                context=context,
                session_dir=session_dir,
                action_index=session.action_count + 1,
            )
        
        # Append to unified timeline
        session.append_event(
            event_type="signal",
            data={
                "signal_name": signal_name,
                "new_value": new_value,
            },
            screenshot=str(screenshot_path) if screenshot_path else None,
        )
    
    async def _capture_on_error(self, error_msg: str, error_data: Optional[dict] = None) -> None:
        """Capture screenshot on error during session."""
        if not self._recorder or not self._recorder.is_recording:
            return
        
        session = self._recorder.current_session
        session_dir = self._recorder._session_dir
        if not session or not session_dir:
            return
        
        screenshot_path = None
        if self._screenshots:
            screenshot_path = await self._screenshots.capture_action(
                action_type="error",
                phase="at",
                context=error_msg[:50],
                session_dir=session_dir,
                action_index=session.action_count + 1,
            )
        
        # Build error data
        error_info = error_data or {}
        
        # Append to console_errors list
        session.console_errors.append({
            "message": error_msg,
            "stack": error_info.get("stack"),
            "source": error_info.get("source"),
            "line": error_info.get("line"),
            "ts": int((time.time() - session.start_time) * 1000),
        })
        
        # Append to unified timeline
        session.append_event(
            event_type="error",
            data={
                "level": "error",
                "message": error_msg,
                "stack": error_info.get("stack"),
                "source": error_info.get("source"),
                "line": error_info.get("line"),
            },
            screenshot=str(screenshot_path) if screenshot_path else None,
        )
    
    async def _capture_on_inspect(self, element_data: dict) -> None:
        """Capture element selection from inspect mode during session."""
        if not self._recorder or not self._recorder.is_recording:
            return
        
        session = self._recorder.current_session
        session_dir = self._recorder._session_dir
        if not session or not session_dir:
            return
        
        # Set selected element on the session
        self._recorder.set_selected_element(ElementInfo(
            selector=element_data.get("selector", ""),
            tag_name=element_data.get("tagName", "unknown"),
            id=element_data.get("id"),
            class_name=element_data.get("classes"),
            text_content=element_data.get("textContent"),
            pynext_source=element_data.get("source"),
            handlers=element_data.get("handlers", {}),
            hydrated=element_data.get("hydrated", False),
        ))
        
        # Take screenshot
        screenshot_path = None
        if self._screenshots:
            screenshot_path = await self._screenshots.capture_action(
                action_type="inspect",
                phase="at",
                context=element_data.get("selector", "element")[:30],
                session_dir=session_dir,
                action_index=session.action_count + 1,
            )
        
        # Append to unified timeline
        session.append_event(
            event_type="inspect",
            data={
                "selector": element_data.get("selector"),
                "tagName": element_data.get("tagName"),
                "id": element_data.get("id"),
                "classes": element_data.get("classes"),
                "textContent": element_data.get("textContent"),
                "source": element_data.get("source"),
                "handlers": element_data.get("handlers", {}),
                "hydrated": element_data.get("hydrated", False),
            },
            screenshot=str(screenshot_path) if screenshot_path else None,
        )
    
    async def _capture_on_drawing(self, drawing_data: dict) -> None:
        """Capture drawing annotation during session."""
        if not self._recorder or not self._recorder.is_recording:
            return
        
        session = self._recorder.current_session
        session_dir = self._recorder._session_dir
        if not session or not session_dir:
            return
        
        from pynext.devtools.recorder import DrawingAnnotation
        
        drawing_type = drawing_data.get("type", "unknown")
        drawing_color = drawing_data.get("color", "#ff0000")
        data = drawing_data.get("data", {})
        
        # Create DrawingAnnotation object
        annotation = DrawingAnnotation(
            type=drawing_type,
            color=drawing_color,
            position=data.get("position") or data.get("center"),
            from_pos=data.get("from"),
            to_pos=data.get("to"),
            text=data.get("text"),
            points=data.get("points"),
        )
        
        # Add to session drawings
        self._recorder.add_drawing(annotation)
        
        # Take screenshot showing the drawing
        screenshot_path = None
        if self._screenshots:
            screenshot_path = await self._screenshots.capture_action(
                action_type="drawing",
                phase="at",
                context=drawing_type[:20],
                session_dir=session_dir,
                action_index=session.action_count + 1,
            )
        
        # Append to unified timeline
        session.append_event(
            event_type="drawing",
            data={
                "type": drawing_type,
                "color": drawing_color,
                **data,
            },
            screenshot=str(screenshot_path) if screenshot_path else None,
        )
    
    async def _get_signal_snapshot(self) -> dict:
        """Get current signal values from browser."""
        if not self._injector:
            return {}
        try:
            state = await self._injector.get_state()
            return state.get("signals", {}) if state else {}
        except Exception:
            return {}
    
    def _get_changed_signals(self, before: dict, after: dict) -> list:
        """Get list of signals that changed between before and after."""
        changed = []
        for key in set(list(before.keys()) + list(after.keys())):
            before_val = before.get(key, {}).get("value")
            after_val = after.get(key, {}).get("value")
            if before_val != after_val:
                changed.append({
                    "id": key,
                    "name": before.get(key, after.get(key, {})).get("name", key),
                    "before": before_val,
                    "after": after_val,
                })
        return changed
    
    async def _run_ai_analysis(self, session_path: Path) -> None:
        """
        Run AI analysis on completed session using Claude 4.5 Opus.
        
        This is called automatically when a session ends.
        Generates briefing.md, narration.json, and analysis files.
        """
        if not self.config.enable_ai_analysis:
            print(f"[PyNext AI Debug] AI analysis disabled")
            return
        
        if not self.config.api_key:
            print(f"[PyNext AI Debug] No API key - skipping AI analysis")
            print(f"[PyNext AI Debug] Set ANTHROPIC_API_KEY or use --api-key flag")
            return
        
        print(f"[PyNext AI Debug] Running AI analysis with Claude 4.5 Opus...")
        
        try:
            from pynext.devtools.processor import SessionProcessor
            
            processor = SessionProcessor(
                api_key=self.config.api_key,
            )
            result = await processor.analyze_session(session_path)
            
            print(f"[PyNext AI Debug] ✓ Generated: {result.briefing_path}")
            if result.storyboard_path:
                print(f"[PyNext AI Debug] ✓ Storyboard: {result.storyboard_path}")
            
        except Exception as e:
            print(f"[PyNext AI Debug] Analysis failed: {e}")
            import traceback
            traceback.print_exc()


async def start_debug_session(
    url: str,
    output_dir: str = ".pynext/debug",
    headless: bool = False,
) -> AIDebugger:
    """
    Convenience function to start a debug session.
    
    Args:
        url: URL to debug
        output_dir: Output directory
        headless: Run Chrome in headless mode
    
    Returns:
        Running AIDebugger instance
    """
    config = DebugConfig(
        output_dir=Path(output_dir),
        headless=headless,
    )
    
    debugger = AIDebugger(config)
    await debugger.start(url)
    
    return debugger

