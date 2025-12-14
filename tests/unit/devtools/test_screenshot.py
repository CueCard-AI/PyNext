"""
Tests for Screenshot Capture - Visual Debugging for AI.

Tests cover:
- ScreenshotCapture initialization
- Screenshot capture on various triggers
- DOM snapshot capture
- File naming and sequencing
- Element highlighting
- Cleanup of old files
- Error handling
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from pynext.devtools.screenshot import ScreenshotCapture, CaptureResult, annotate_screenshot


# ============================================
# CaptureResult Tests
# ============================================

class TestCaptureResult:
    """Tests for CaptureResult dataclass."""
    
    def test_success_with_screenshot(self):
        """Test success property with screenshot."""
        result = CaptureResult(
            seq=1,
            screenshot_path=Path("/tmp/001.png"),
            snapshot_path=None,
            trigger="click",
            timestamp=1.0,
        )
        
        assert result.success is True
    
    def test_success_with_snapshot(self):
        """Test success property with snapshot only."""
        result = CaptureResult(
            seq=1,
            screenshot_path=None,
            snapshot_path=Path("/tmp/001.html"),
            trigger="click",
            timestamp=1.0,
        )
        
        assert result.success is True
    
    def test_failure_no_captures(self):
        """Test success property when nothing captured."""
        result = CaptureResult(
            seq=1,
            screenshot_path=None,
            snapshot_path=None,
            trigger="error",
            timestamp=1.0,
        )
        
        assert result.success is False


# ============================================
# ScreenshotCapture Tests
# ============================================

class TestScreenshotCapture:
    """Tests for ScreenshotCapture initialization and properties."""
    
    def test_init_creates_directories(self):
        """Test that init creates output directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = Mock()
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            assert (output_dir / "screenshots").exists()
            assert (output_dir / "snapshots").exists()
    
    def test_init_no_snapshots(self):
        """Test init with snapshots disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = Mock()
            
            capture = ScreenshotCapture(bridge, output_dir, take_snapshots=False)
            
            assert (output_dir / "screenshots").exists()
            # Snapshots dir should not exist
            assert not (output_dir / "snapshots").exists()
    
    def test_screenshot_count(self):
        """Test screenshot count tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = Mock()
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            assert capture.screenshot_count == 0
            
            capture._seq = 5
            assert capture.screenshot_count == 5
    
    def test_snapshot_count_when_enabled(self):
        """Test snapshot count when enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = Mock()
            
            capture = ScreenshotCapture(bridge, output_dir, take_snapshots=True)
            capture._seq = 3
            
            assert capture.snapshot_count == 3
    
    def test_snapshot_count_when_disabled(self):
        """Test snapshot count when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = Mock()
            
            capture = ScreenshotCapture(bridge, output_dir, take_snapshots=False)
            capture._seq = 3
            
            assert capture.snapshot_count == 0


class TestScreenshotCaptureFilenames:
    """Tests for filename generation."""
    
    def test_filename_basic(self):
        """Test basic filename generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bridge = Mock()
            capture = ScreenshotCapture(bridge, Path(tmpdir))
            
            filename = capture._make_filename(42, "click", "")
            
            assert filename == "042_click"
    
    def test_filename_with_note(self):
        """Test filename with note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bridge = Mock()
            capture = ScreenshotCapture(bridge, Path(tmpdir))
            
            filename = capture._make_filename(1, "manual", "checking modal")
            
            assert filename == "001_manual_checking_modal"
    
    def test_filename_sanitizes_special_chars(self):
        """Test that special characters are sanitized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bridge = Mock()
            capture = ScreenshotCapture(bridge, Path(tmpdir))
            
            filename = capture._make_filename(1, "click", "btn.submit#form")
            
            assert "/" not in filename
            assert "#" not in filename
            assert "." not in filename
    
    def test_filename_truncates_long_notes(self):
        """Test that long notes are truncated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bridge = Mock()
            capture = ScreenshotCapture(bridge, Path(tmpdir))
            
            long_note = "a" * 100
            filename = capture._make_filename(1, "manual", long_note)
            
            # Note should be truncated to 30 chars
            assert len(filename) < 50


class TestScreenshotCaptureCapture:
    """Tests for capture operations."""
    
    @pytest.mark.asyncio
    async def test_capture_screenshot(self):
        """Test basic screenshot capture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            bridge.highlight_element = AsyncMock()
            bridge.clear_highlights = AsyncMock()
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            result = await capture.capture("test")
            
            assert result.success is True
            assert result.screenshot_path.exists()
            assert result.screenshot_path.read_bytes() == b"PNG_DATA"
    
    @pytest.mark.asyncio
    async def test_capture_with_snapshot(self):
        """Test capture with DOM snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html><body>Test</body></html>")
            bridge.highlight_element = AsyncMock()
            bridge.clear_highlights = AsyncMock()
            
            capture = ScreenshotCapture(bridge, output_dir, take_snapshots=True)
            
            result = await capture.capture("test")
            
            assert result.snapshot_path is not None
            assert result.snapshot_path.exists()
            assert "Test" in result.snapshot_path.read_text()
    
    @pytest.mark.asyncio
    async def test_capture_with_element_highlight(self):
        """Test capture with element highlighting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            bridge.highlight_element = AsyncMock()
            bridge.clear_highlights = AsyncMock()
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            await capture.capture(
                "click",
                element={"selector": "#my-button"},
                highlight=True,
            )
            
            bridge.highlight_element.assert_called_with("#my-button")
            bridge.clear_highlights.assert_called()
    
    @pytest.mark.asyncio
    async def test_capture_no_highlight(self):
        """Test capture without highlighting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            await capture.capture("initial", highlight=False)
            
            bridge.highlight_element.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_capture_handles_screenshot_failure(self):
        """Test that capture continues if screenshot fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(side_effect=Exception("Screenshot failed"))
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            result = await capture.capture("test")
            
            # Should still succeed with snapshot
            assert result.screenshot_path is None
            assert result.snapshot_path is not None


class TestScreenshotCaptureHelpers:
    """Tests for capture helper methods."""
    
    @pytest.mark.asyncio
    async def test_capture_initial(self):
        """Test initial capture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            result = await capture.capture_initial()
            
            assert "initial" in str(result.screenshot_path)
    
    @pytest.mark.asyncio
    async def test_capture_click(self):
        """Test click capture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            bridge.highlight_element = AsyncMock()
            bridge.clear_highlights = AsyncMock()
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            result = await capture.capture_click(
                element={"id": "submit-btn", "selector": "#submit-btn"},
                x=100,
                y=200,
            )
            
            assert "click" in str(result.screenshot_path)
            assert "submit" in str(result.screenshot_path)
    
    @pytest.mark.asyncio
    async def test_capture_signal_change(self):
        """Test signal change capture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            result = await capture.capture_signal_change("view_mode", "kanban")
            
            assert "signal" in str(result.screenshot_path)
    
    @pytest.mark.asyncio
    async def test_capture_error(self):
        """Test error capture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            result = await capture.capture_error("TypeError: Cannot read property")
            
            assert "error" in str(result.screenshot_path)
    
    @pytest.mark.asyncio
    async def test_capture_manual(self):
        """Test manual snapshot capture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            result = await capture.capture_manual("Checking modal position")
            
            assert "manual" in str(result.screenshot_path)
    
    @pytest.mark.asyncio
    async def test_capture_navigation(self):
        """Test navigation capture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            result = await capture.capture_navigation("http://localhost:3000/issues")
            
            assert "nav" in str(result.screenshot_path)


class TestScreenshotCaptureLatest:
    """Tests for getting latest captures."""
    
    @pytest.mark.asyncio
    async def test_get_latest_screenshot(self):
        """Test getting latest screenshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            await capture.capture("first")
            await capture.capture("second")
            
            latest = capture.get_latest_screenshot()
            
            assert latest is not None
            assert "002" in latest.name
    
    @pytest.mark.asyncio
    async def test_get_latest_screenshot_empty(self):
        """Test getting latest screenshot when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = Mock()
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            latest = capture.get_latest_screenshot()
            
            assert latest is None
    
    @pytest.mark.asyncio
    async def test_get_latest_snapshot(self):
        """Test getting latest DOM snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            
            capture = ScreenshotCapture(bridge, output_dir, take_snapshots=True)
            
            await capture.capture("test")
            
            latest = capture.get_latest_snapshot()
            
            assert latest is not None
            assert latest.suffix == ".html"


class TestScreenshotCaptureCleanup:
    """Tests for cleanup functionality."""
    
    @pytest.mark.asyncio
    async def test_cleanup_old_files(self):
        """Test cleanup of old screenshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "debug"
            bridge = AsyncMock()
            bridge.take_screenshot = AsyncMock(return_value=b"PNG_DATA")
            bridge.get_dom_snapshot = AsyncMock(return_value="<html></html>")
            
            capture = ScreenshotCapture(bridge, output_dir)
            
            # Take many screenshots
            for i in range(15):
                await capture.capture(f"test_{i}")
            
            # Keep only 10
            removed = capture.cleanup_old(keep_count=10)
            
            assert removed > 0
            remaining = list((output_dir / "screenshots").glob("*.png"))
            assert len(remaining) == 10


# ============================================
# Annotation Tests
# ============================================

class TestAnnotateScreenshot:
    """Tests for screenshot annotation."""
    
    def test_annotate_without_pillow(self):
        """Test annotation gracefully handles missing Pillow."""
        # When Pillow is not available, should return original
        with patch.dict('sys.modules', {'PIL': None}):
            result = annotate_screenshot(
                b"PNG_DATA",
                {"x": 10, "y": 20, "width": 100, "height": 50},
                "Label",
            )
            
            # Should return original on error
            assert result == b"PNG_DATA"
    
    def test_annotate_with_error(self):
        """Test annotation handles errors gracefully."""
        # Invalid image data should not raise
        result = annotate_screenshot(
            b"NOT_A_VALID_IMAGE",
            {"x": 10, "y": 20, "width": 100, "height": 50},
            "Label",
        )
        
        assert result == b"NOT_A_VALID_IMAGE"

