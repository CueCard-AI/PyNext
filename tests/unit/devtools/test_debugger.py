"""
Tests for AI Debugger - Main Orchestrator for PyNext AI DevTools.

Tests cover:
- AIDebugger initialization
- Start and stop lifecycle
- Event handling and screenshot capture
- State management
- Signal access
- Manual snapshots
- Summary and event reading
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from pynext.devtools.debugger import AIDebugger, DebugConfig, start_debug_session
from pynext.devtools.capture import DebugEvent, EventType


# ============================================
# DebugConfig Tests
# ============================================

class TestDebugConfig:
    """Tests for DebugConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration."""
        config = DebugConfig()
        
        assert config.output_dir == Path(".pynext/debug")
        assert config.debug_port == 9222
        assert config.headless is False
        assert config.window_size == (1280, 800)
        assert config.take_screenshots is True
    
    def test_custom_values(self):
        """Test custom configuration."""
        config = DebugConfig(
            output_dir=Path("/tmp/debug"),
            debug_port=9333,
            headless=True,
            window_size=(1920, 1080),
        )
        
        assert config.output_dir == Path("/tmp/debug")
        assert config.debug_port == 9333
        assert config.headless is True
    
    def test_output_dir_conversion(self):
        """Test that output_dir is converted to Path."""
        config = DebugConfig(output_dir="/tmp/debug")
        
        assert isinstance(config.output_dir, Path)


# ============================================
# AIDebugger Initialization Tests
# ============================================

class TestAIDebuggerInit:
    """Tests for AIDebugger initialization."""
    
    def test_init_default_config(self):
        """Test initialization with default config."""
        debugger = AIDebugger()
        
        assert debugger.config is not None
        assert debugger.running is False
        assert debugger.event_count == 0
    
    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = DebugConfig(debug_port=9333)
        debugger = AIDebugger(config)
        
        assert debugger.config.debug_port == 9333
    
    def test_running_property(self):
        """Test running property."""
        debugger = AIDebugger()
        
        assert debugger.running is False
        
        debugger._running = True
        assert debugger.running is True


# ============================================
# Start/Stop Lifecycle Tests
# ============================================

class TestAIDebuggerLifecycle:
    """Tests for debugger lifecycle."""
    
    @pytest.mark.asyncio
    async def test_start_creates_output_dir(self):
        """Test that start creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            config = DebugConfig(output_dir=output_dir, take_screenshots=False)
            debugger = AIDebugger(config)
            
            # Mock all components
            with patch('pynext.devtools.debugger.ChromeLauncher') as MockLauncher:
                mock_launcher = Mock()
                mock_launcher.launch = AsyncMock(return_value="ws://localhost:9222/...")
                MockLauncher.return_value = mock_launcher
                
                with patch('pynext.devtools.debugger.CDPBridge') as MockBridge:
                    mock_bridge = AsyncMock()
                    mock_bridge.on_event = Mock()
                    MockBridge.return_value = mock_bridge
                    
                    with patch('pynext.devtools.debugger.JSInjector') as MockInjector:
                        mock_injector = AsyncMock()
                        MockInjector.return_value = mock_injector
                        
                        await debugger.start("http://localhost:3000")
            
            assert output_dir.exists()
            
            await debugger.stop()
    
    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Test that start sets running to True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug", take_screenshots=False)
            debugger = AIDebugger(config)
            
            with patch('pynext.devtools.debugger.ChromeLauncher') as MockLauncher:
                mock_launcher = Mock()
                mock_launcher.launch = AsyncMock(return_value="ws://...")
                MockLauncher.return_value = mock_launcher
                
                with patch('pynext.devtools.debugger.CDPBridge') as MockBridge:
                    mock_bridge = AsyncMock()
                    mock_bridge.on_event = Mock()
                    MockBridge.return_value = mock_bridge
                    
                    with patch('pynext.devtools.debugger.JSInjector') as MockInjector:
                        MockInjector.return_value = AsyncMock()
                        
                        await debugger.start("http://localhost:3000")
            
            assert debugger.running is True
            
            await debugger.stop()
    
    @pytest.mark.asyncio
    async def test_stop_sets_running_false(self):
        """Test that stop sets running to False."""
        debugger = AIDebugger()
        debugger._running = True
        debugger._stop_event = asyncio.Event()
        
        # Set up mock components
        debugger._capture = Mock()
        debugger._capture.emit_debug_end = Mock()
        debugger._stream = Mock()
        debugger._bridge = AsyncMock()
        debugger._launcher = Mock()
        
        await debugger.stop()
        
        assert debugger.running is False
    
    @pytest.mark.asyncio
    async def test_stop_clears_components(self):
        """Test that stop disconnects components."""
        debugger = AIDebugger()
        debugger._running = True
        debugger._stop_event = asyncio.Event()
        
        mock_bridge = AsyncMock()
        debugger._bridge = mock_bridge
        
        mock_launcher = Mock()
        debugger._launcher = mock_launcher
        
        debugger._capture = Mock()
        debugger._capture.emit_debug_end = Mock()
        debugger._stream = Mock()
        
        await debugger.stop()
        
        mock_bridge.disconnect.assert_called()
        mock_launcher.shutdown.assert_called()
    
    @pytest.mark.asyncio
    async def test_start_when_already_running(self):
        """Test that start does nothing if already running."""
        debugger = AIDebugger()
        debugger._running = True
        
        # Should return immediately without error
        await debugger.start("http://localhost:3000")


# ============================================
# State and Signal Tests
# ============================================

class TestAIDebuggerState:
    """Tests for state and signal access."""
    
    @pytest.mark.asyncio
    async def test_get_state(self):
        """Test getting current state."""
        debugger = AIDebugger()
        debugger._running = True
        debugger._url = "http://localhost:3000"
        
        mock_injector = AsyncMock()
        mock_injector.get_state = AsyncMock(return_value={
            "signals": {"count": 5},
        })
        debugger._injector = mock_injector
        
        state = await debugger.get_state()
        
        assert state["url"] == "http://localhost:3000"
        assert state["running"] is True
    
    @pytest.mark.asyncio
    async def test_get_signal(self):
        """Test getting signal value."""
        debugger = AIDebugger()
        
        mock_injector = AsyncMock()
        mock_injector.get_signal_value = AsyncMock(return_value="kanban")
        debugger._injector = mock_injector
        
        value = await debugger.get_signal("view_mode")
        
        assert value == "kanban"
    
    @pytest.mark.asyncio
    async def test_get_signal_no_injector(self):
        """Test get_signal when injector not available."""
        debugger = AIDebugger()
        debugger._injector = None
        
        value = await debugger.get_signal("count")
        
        assert value is None
    
    @pytest.mark.asyncio
    async def test_set_signal(self):
        """Test setting signal value."""
        debugger = AIDebugger()
        
        mock_injector = AsyncMock()
        mock_injector.set_signal_value = AsyncMock(return_value=True)
        debugger._injector = mock_injector
        
        result = await debugger.set_signal("count", 10)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_list_signals(self):
        """Test listing signals."""
        debugger = AIDebugger()
        
        mock_injector = AsyncMock()
        mock_injector.list_signals = AsyncMock(return_value=[
            {"id": "sig_1", "name": "count", "value": 5}
        ])
        debugger._injector = mock_injector
        
        signals = await debugger.list_signals()
        
        assert len(signals) == 1


# ============================================
# Snapshot Tests
# ============================================

class TestAIDebuggerSnapshot:
    """Tests for snapshot functionality."""
    
    @pytest.mark.asyncio
    async def test_snapshot(self):
        """Test taking manual snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug")
            debugger = AIDebugger(config)
            debugger._running = True
            
            mock_capture = Mock()
            mock_capture.emit_manual_snapshot = Mock()
            debugger._capture = mock_capture
            
            mock_screenshots = AsyncMock()
            mock_screenshots.capture_manual = AsyncMock(return_value=Mock(
                screenshot_path=Path(tmpdir) / "debug" / "screenshots" / "001.png"
            ))
            debugger._screenshots = mock_screenshots
            
            result = await debugger.snapshot("Testing")
            
            mock_capture.emit_manual_snapshot.assert_called_with("Testing")
    
    @pytest.mark.asyncio
    async def test_snapshot_not_running(self):
        """Test snapshot when not running."""
        debugger = AIDebugger()
        debugger._running = False
        
        result = await debugger.snapshot("Test")
        
        assert result is None


# ============================================
# Event Reading Tests
# ============================================

class TestAIDebuggerEvents:
    """Tests for event reading."""
    
    def test_read_events(self):
        """Test reading events."""
        debugger = AIDebugger()
        
        mock_stream = Mock()
        mock_stream.read_events = Mock(return_value=[
            DebugEvent(seq=1, ts=1.0, type=EventType.CONSOLE_LOG),
            DebugEvent(seq=2, ts=2.0, type=EventType.CLICK),
        ])
        debugger._stream = mock_stream
        
        events = debugger.read_events(limit=10)
        
        assert len(events) == 2
    
    def test_read_events_no_stream(self):
        """Test read_events when stream not available."""
        debugger = AIDebugger()
        debugger._stream = None
        
        events = debugger.read_events()
        
        assert events == []


# ============================================
# Summary Tests
# ============================================

class TestAIDebuggerSummary:
    """Tests for summary functionality."""
    
    def test_get_summary(self):
        """Test getting summary."""
        debugger = AIDebugger()
        debugger._running = True
        debugger._url = "http://localhost:3000"
        
        mock_capture = Mock()
        mock_capture.event_count = 42
        debugger._capture = mock_capture
        
        mock_stream = Mock()
        mock_stream.get_summary = Mock(return_value={
            "screenshot_count": 10,
            "snapshot_count": 10,
        })
        debugger._stream = mock_stream
        
        summary = debugger.get_summary()
        
        assert summary["running"] is True
        assert summary["url"] == "http://localhost:3000"
        assert summary["event_count"] == 42


# ============================================
# Event Handling Tests
# ============================================

class TestAIDebuggerEventHandling:
    """Tests for event handling."""
    
    @pytest.mark.asyncio
    async def test_on_event_writes_to_stream(self):
        """Test that events are written to stream."""
        debugger = AIDebugger()
        debugger._running = True
        
        mock_stream = Mock()
        debugger._stream = mock_stream
        
        # Disable screenshot capture
        debugger._screenshots = None
        
        event = DebugEvent(seq=1, ts=1.0, type=EventType.CONSOLE_LOG)
        debugger._on_event(event)
        
        mock_stream.write_event.assert_called_with(event)


# ============================================
# Convenience Function Tests
# ============================================

class TestStartDebugSession:
    """Tests for start_debug_session convenience function."""
    
    @pytest.mark.asyncio
    async def test_start_debug_session(self):
        """Test start_debug_session function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('pynext.devtools.debugger.ChromeLauncher') as MockLauncher:
                mock_launcher = Mock()
                mock_launcher.launch = AsyncMock(return_value="ws://...")
                MockLauncher.return_value = mock_launcher
                
                with patch('pynext.devtools.debugger.CDPBridge') as MockBridge:
                    mock_bridge = AsyncMock()
                    mock_bridge.on_event = Mock()
                    MockBridge.return_value = mock_bridge
                    
                    with patch('pynext.devtools.debugger.JSInjector') as MockInjector:
                        MockInjector.return_value = AsyncMock()
                        
                        with patch('pynext.devtools.debugger.ScreenshotCapture') as MockScreenshot:
                            mock_screenshot = AsyncMock()
                            MockScreenshot.return_value = mock_screenshot
                            
                            debugger = await start_debug_session(
                                "http://localhost:3000",
                                output_dir=tmpdir + "/debug",
                            )
                
                assert debugger.running is True
                
                await debugger.stop()


# ============================================
# Session Recording Tests
# ============================================

class TestSessionRecording:
    """Tests for session recording (time-based + event-based screenshots)."""
    
    def test_session_state_initialized(self):
        """Test session state is initialized in AIDebugger."""
        debugger = AIDebugger()
        
        # Recorder is None until start() is called
        assert debugger._recorder is None
        assert debugger._screenshot_task is None
    
    @pytest.mark.asyncio
    async def test_start_session_creates_directory(self):
        """Test _start_session creates session directory via SessionRecorder."""
        from pynext.devtools.recorder import SessionRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug")
            debugger = AIDebugger(config)
            debugger._running = True
            
            # Initialize recorder (normally done in start())
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            
            debugger._start_session("test intent")
            
            # Cancel the screenshot task to prevent warnings
            if debugger._screenshot_task:
                debugger._screenshot_task.cancel()
            
            assert debugger._recorder.is_recording is True
            assert debugger._recorder._session_dir is not None
            assert debugger._recorder._session_dir.exists()
    
    @pytest.mark.asyncio
    async def test_start_session_saves_metadata(self):
        """Test _start_session saves session metadata."""
        from pynext.devtools.recorder import SessionRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug")
            debugger = AIDebugger(config)
            debugger._running = True
            debugger._url = "http://localhost:3000"
            
            # Initialize recorder
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            
            debugger._start_session("debugging modal bug")
            
            # Cancel the screenshot task
            if debugger._screenshot_task:
                debugger._screenshot_task.cancel()
            
            session = debugger._recorder.current_session
            assert session is not None
            assert session.intent == "debugging modal bug"
    
    @pytest.mark.asyncio
    async def test_end_session_updates_metadata(self):
        """Test _end_session saves session summary with outcome."""
        from pynext.devtools.recorder import SessionRecorder
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug")
            debugger = AIDebugger(config)
            debugger._running = True
            
            # Initialize recorder
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            
            # Start session
            debugger._start_session("test")
            session_dir = debugger._recorder._session_dir
            
            # End session (this cancels the screenshot task)
            result_path = debugger._end_session("found the bug!")
            
            assert debugger._recorder.is_recording is False
            assert result_path == session_dir
            
            # Check saved summary (SessionRecorder saves summary.json, not metadata.json)
            summary = json.loads((session_dir / "summary.json").read_text())
            assert summary["outcome"] == "found the bug!"
    
    @pytest.mark.asyncio
    async def test_start_session_prevents_double_start(self):
        """Test that starting session while active does nothing."""
        from pynext.devtools.recorder import SessionRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug")
            debugger = AIDebugger(config)
            debugger._running = True
            
            # Initialize recorder
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            
            debugger._start_session("first")
            original_session_id = debugger._recorder.current_session.session_id
            
            debugger._start_session("second")
            
            # Cancel the screenshot task
            if debugger._screenshot_task:
                debugger._screenshot_task.cancel()
            
            # Should still be the first session
            assert debugger._recorder.current_session.session_id == original_session_id
    
    def test_end_session_without_active_returns_none(self):
        """Test ending session without active returns None."""
        debugger = AIDebugger()
        
        result = debugger._end_session("outcome")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_on_event_starts_session(self):
        """Test SESSION_START event starts session recording."""
        from pynext.devtools.recorder import SessionRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug")
            debugger = AIDebugger(config)
            debugger._running = True
            debugger._stream = Mock()
            debugger._screenshots = None  # Disable screenshots
            
            # Initialize recorder
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            
            event = DebugEvent(
                seq=1,
                ts=1.0,
                type=EventType.SESSION_START,
                data={"intent": "test session"},
            )
            debugger._on_event(event)
            
            # Cancel screenshot task
            if debugger._screenshot_task:
                debugger._screenshot_task.cancel()
            
            assert debugger._recorder.is_recording is True
    
    @pytest.mark.asyncio
    async def test_on_event_ends_session(self):
        """Test SESSION_END event ends session recording."""
        from pynext.devtools.recorder import SessionRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug", enable_ai_analysis=False)
            debugger = AIDebugger(config)
            debugger._running = True
            debugger._stream = Mock()
            debugger._screenshots = None
            
            # Initialize recorder
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            
            # Start first
            debugger._start_session("test")
            
            # Cancel screenshot task before ending
            if debugger._screenshot_task:
                debugger._screenshot_task.cancel()
            
            event = DebugEvent(
                seq=2,
                ts=2.0,
                type=EventType.SESSION_END,
                data={"outcome": "done"},
            )
            debugger._on_event(event)
            
            assert debugger._recorder.is_recording is False
    
    @pytest.mark.asyncio
    async def test_screenshot_loop_captures_frames(self):
        """Test _screenshot_loop captures frames at interval."""
        from pynext.devtools.recorder import SessionRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(
                output_dir=Path(tmpdir) / "debug",
                screenshot_interval_ms=50,  # Fast for testing
            )
            debugger = AIDebugger(config)
            debugger._running = True
            
            # Initialize recorder and start session
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            session = debugger._recorder.start_session("test")
            
            mock_screenshots = AsyncMock()
            debugger._screenshots = mock_screenshots
            
            # Run loop for ~150ms
            task = asyncio.create_task(debugger._screenshot_loop())
            await asyncio.sleep(0.16)
            debugger._recorder.end_session("done")  # Stop recording
            await asyncio.sleep(0.1)
            task.cancel()
            
            # Should have called capture_frame at least 2 times
            assert mock_screenshots.capture_frame.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_capture_on_click(self):
        """Test _capture_on_click takes before/after screenshots."""
        from pynext.devtools.recorder import SessionRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug")
            debugger = AIDebugger(config)
            debugger._running = True
            
            # Initialize recorder and start session
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            debugger._recorder.start_session("test")
            
            mock_screenshots = AsyncMock()
            debugger._screenshots = mock_screenshots
            debugger._injector = AsyncMock()
            debugger._injector.get_state = AsyncMock(return_value={"signals": {}})
            
            await debugger._capture_on_click({"selector": "#submit-btn"})
            
            # Should call capture_action twice (before and after)
            assert mock_screenshots.capture_action.call_count == 2
            
            calls = mock_screenshots.capture_action.call_args_list
            assert calls[0].kwargs["phase"] == "before"
            assert calls[1].kwargs["phase"] == "after"
    
    @pytest.mark.asyncio
    async def test_capture_on_note(self):
        """Test _capture_on_note takes screenshot."""
        from pynext.devtools.recorder import SessionRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug")
            debugger = AIDebugger(config)
            
            # Initialize recorder and start session
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            debugger._recorder.start_session("test")
            
            mock_screenshots = AsyncMock()
            debugger._screenshots = mock_screenshots
            
            await debugger._capture_on_note("checking modal position")
            
            mock_screenshots.capture_action.assert_called_once()
            call_kwargs = mock_screenshots.capture_action.call_args.kwargs
            assert call_kwargs["action_type"] == "note"
            assert call_kwargs["context"] == "checking modal position"
    
    @pytest.mark.asyncio
    async def test_capture_on_signal(self):
        """Test _capture_on_signal takes screenshot."""
        from pynext.devtools.recorder import SessionRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug")
            debugger = AIDebugger(config)
            
            # Initialize recorder and start session
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            debugger._recorder.start_session("test")
            
            mock_screenshots = AsyncMock()
            debugger._screenshots = mock_screenshots
            
            await debugger._capture_on_signal("view_mode", "kanban")
            
            mock_screenshots.capture_action.assert_called_once()
            call_kwargs = mock_screenshots.capture_action.call_args.kwargs
            assert call_kwargs["action_type"] == "signal"
    
    @pytest.mark.asyncio
    async def test_capture_on_error(self):
        """Test _capture_on_error takes screenshot."""
        from pynext.devtools.recorder import SessionRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DebugConfig(output_dir=Path(tmpdir) / "debug")
            debugger = AIDebugger(config)
            
            # Initialize recorder and start session
            debugger._recorder = SessionRecorder(config.output_dir, config.mode.value)
            debugger._recorder.start_session("test")
            
            mock_screenshots = AsyncMock()
            debugger._screenshots = mock_screenshots
            
            await debugger._capture_on_error("TypeError: undefined")
            
            mock_screenshots.capture_action.assert_called_once()
            call_kwargs = mock_screenshots.capture_action.call_args.kwargs
            assert call_kwargs["action_type"] == "error"

