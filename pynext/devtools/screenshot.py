"""
Screenshot Capture - Visual Debugging for AI.

This module handles screenshot and DOM snapshot capture for AI debugging.
Screenshots are taken automatically on key events and can be triggered
manually for precise debugging.

What Gets Captured:
    - Screenshot (PNG) of the visible viewport
    - Full DOM HTML snapshot
    - Element highlighting for clicked elements
    - Sequential numbering with descriptive names

Automatic Triggers:
    - Click events
    - Signal value changes
    - JavaScript errors
    - Page navigation
    - Network errors

Manual Triggers:
    - Keyboard: Ctrl+Shift+S
    - Console: __pynext__.snapshot("note")
    - UI button: Click camera icon (optional)

Output:
    .pynext/debug/screenshots/
    ├── 001_initial.png
    ├── 002_click_new_issue_btn.png
    ├── 003_signal_modal_open.png
    ├── 004_manual_checking_layout.png
    └── ...
    
    .pynext/debug/snapshots/
    ├── 001.html
    ├── 002.html
    └── ...

Example:
    capture = ScreenshotCapture(bridge, output_dir)
    
    # Take screenshot on click
    path = await capture.capture("click", element={"id": "submit-btn"})
    print(f"Saved: {path}")
    
    # Manual snapshot with note
    path = await capture.capture("manual", note="Checking modal position")
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pynext.devtools.bridge import CDPBridge


@dataclass
class CaptureResult:
    """Result of a screenshot capture operation."""
    seq: int
    screenshot_path: Optional[Path]
    snapshot_path: Optional[Path]
    trigger: str
    timestamp: float
    
    @property
    def success(self) -> bool:
        """True if at least one capture succeeded."""
        return self.screenshot_path is not None or self.snapshot_path is not None


class ScreenshotCapture:
    """
    Captures screenshots and DOM snapshots for AI debugging.
    
    This class manages:
    - Taking screenshots via CDP
    - Capturing DOM HTML snapshots
    - Sequential file naming
    - Element highlighting
    - Optional image annotation
    
    Attributes:
        output_dir: Base directory for output
        screenshot_count: Number of screenshots taken
        snapshot_count: Number of DOM snapshots taken
    
    Example:
        capture = ScreenshotCapture(bridge, Path(".pynext/debug"))
        
        # Take initial screenshot
        result = await capture.capture("initial")
        
        # Take screenshot with element highlight
        result = await capture.capture(
            "click",
            element={"selector": "#submit-btn"}
        )
    """
    
    def __init__(
        self,
        bridge: "CDPBridge",
        output_dir: Path,
        take_snapshots: bool = True,
    ):
        """
        Initialize screenshot capture.
        
        Args:
            bridge: CDPBridge instance for browser communication
            output_dir: Base directory for output files
            take_snapshots: Also capture DOM HTML snapshots
        """
        self._bridge = bridge
        self._output_dir = Path(output_dir)
        self._take_snapshots = take_snapshots
        self._seq = 0
        self._screenshot_dir = self._output_dir / "screenshots"
        self._snapshot_dir = self._output_dir / "snapshots"
        
        # Create directories
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        if take_snapshots:
            self._snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def screenshot_count(self) -> int:
        """Number of screenshots taken."""
        return self._seq
    
    @property
    def snapshot_count(self) -> int:
        """Number of DOM snapshots taken."""
        return self._seq if self._take_snapshots else 0
    
    def _next_seq(self) -> int:
        """Get next sequence number."""
        self._seq += 1
        return self._seq
    
    def _make_filename(self, seq: int, trigger: str, note: str = "") -> str:
        """
        Create a descriptive filename.
        
        Args:
            seq: Sequence number
            trigger: Event trigger type
            note: Optional note to include
        
        Returns:
            Filename without extension (e.g., "042_click_submit_btn")
        """
        # Sanitize trigger and note for filename
        def sanitize(s: str) -> str:
            return "".join(c if c.isalnum() or c in "_-" else "_" for c in s)[:30]
        
        parts = [f"{seq:03d}", sanitize(trigger)]
        
        if note:
            parts.append(sanitize(note))
        
        return "_".join(parts)
    
    async def capture(
        self,
        trigger: str,
        element: Optional[dict] = None,
        note: str = "",
        highlight: bool = True,
        full_page: bool = False,
    ) -> CaptureResult:
        """
        Capture screenshot and optionally DOM snapshot.
        
        Args:
            trigger: What triggered this capture (click, signal, error, manual)
            element: Element info for highlighting (selector, id, etc.)
            note: Optional note for filename
            highlight: Whether to highlight the element
            full_page: Capture full scrollable page
        
        Returns:
            CaptureResult with paths to saved files
        """
        seq = self._next_seq()
        timestamp = time.time()
        filename = self._make_filename(seq, trigger, note)
        
        screenshot_path: Optional[Path] = None
        snapshot_path: Optional[Path] = None
        
        try:
            # Highlight element if requested
            if highlight and element and element.get("selector"):
                try:
                    await self._bridge.highlight_element(element["selector"])
                    await asyncio.sleep(0.05)  # Brief pause for highlight to render
                except Exception:
                    pass  # Continue even if highlight fails
            
            # Take screenshot
            try:
                screenshot_data = await self._bridge.take_screenshot(
                    format="png",
                    full_page=full_page,
                )
                
                screenshot_path = self._screenshot_dir / f"{filename}.png"
                screenshot_path.write_bytes(screenshot_data)
                
            except Exception as e:
                # Screenshot failed, continue with snapshot
                pass
            
            # Clear highlight
            if highlight and element:
                try:
                    await self._bridge.clear_highlights()
                except Exception:
                    pass
            
            # Take DOM snapshot
            if self._take_snapshots:
                try:
                    html = await self._bridge.get_dom_snapshot()
                    
                    snapshot_path = self._snapshot_dir / f"{filename}.html"
                    snapshot_path.write_text(html, encoding="utf-8")
                    
                except Exception:
                    pass
            
        except Exception:
            pass  # Best effort capture
        
        return CaptureResult(
            seq=seq,
            screenshot_path=screenshot_path,
            snapshot_path=snapshot_path,
            trigger=trigger,
            timestamp=timestamp,
        )
    
    async def capture_initial(self) -> CaptureResult:
        """Capture initial page state after load."""
        return await self.capture("initial", highlight=False)
    
    async def capture_click(
        self,
        element: dict,
        x: int = 0,
        y: int = 0,
    ) -> CaptureResult:
        """
        Capture after a click event.
        
        Args:
            element: Clicked element info
            x: Click X coordinate
            y: Click Y coordinate
        """
        # Create descriptive note from element
        note = ""
        if element.get("id"):
            note = element["id"]
        elif element.get("selector"):
            note = element["selector"].replace(".", "_").replace("#", "")
        
        return await self.capture(
            "click",
            element=element,
            note=note,
            highlight=True,
        )
    
    async def capture_signal_change(
        self,
        signal_name: str,
        new_value: str,
    ) -> CaptureResult:
        """
        Capture after a signal value change.
        
        Args:
            signal_name: Name of the signal
            new_value: New value (stringified)
        """
        note = f"{signal_name}_{new_value}"[:30]
        return await self.capture(
            "signal",
            note=note,
            highlight=False,
        )
    
    async def capture_error(
        self,
        error_message: str,
    ) -> CaptureResult:
        """
        Capture after a JavaScript error.
        
        Args:
            error_message: Error message
        """
        # Truncate error for filename
        note = error_message[:20].replace(" ", "_")
        return await self.capture(
            "error",
            note=note,
            highlight=False,
        )
    
    async def capture_manual(
        self,
        note: str = "",
    ) -> CaptureResult:
        """
        Capture manual snapshot triggered by user.
        
        Args:
            note: User-provided note/label
        """
        return await self.capture(
            "manual",
            note=note or "snapshot",
            highlight=False,
        )
    
    async def capture_navigation(
        self,
        url: str,
    ) -> CaptureResult:
        """
        Capture after navigation.
        
        Args:
            url: New URL
        """
        # Extract path for filename
        from urllib.parse import urlparse
        path = urlparse(url).path.strip("/").replace("/", "_") or "root"
        
        return await self.capture(
            "nav",
            note=path[:30],
            highlight=False,
        )
    
    async def capture_frame(
        self,
        frame_number: int,
        session_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """
        Capture a numbered frame during time-based screenshot loop.
        
        This is used by the 150ms screenshot loop during active sessions.
        Unlike regular captures, frames go to session-specific directory.
        
        Args:
            frame_number: Sequential frame number
            session_dir: Session-specific output directory
        
        Returns:
            Path to saved screenshot, or None if failed
        """
        output_dir = session_dir or self._screenshot_dir
        frames_dir = output_dir / "all_frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            screenshot_data = await self._bridge.take_screenshot(
                format="png",
                full_page=False,  # Viewport only for speed
            )
            
            frame_path = frames_dir / f"{frame_number:04d}.png"
            frame_path.write_bytes(screenshot_data)
            return frame_path
            
        except Exception:
            return None
    
    async def capture_action(
        self,
        action_type: str,
        phase: str,
        context: str,
        session_dir: Optional[Path] = None,
        action_index: int = 0,
    ) -> Optional[Path]:
        """
        Capture before/after screenshot for a user action.
        
        This is used for event-based screenshots on clicks, notes, etc.
        These go to key_frames/ for easy identification.
        
        Args:
            action_type: Type of action (click, note, snapshot, error, signal)
            phase: "before" or "after"
            context: Description of the action (e.g., button selector)
            session_dir: Session-specific output directory
            action_index: Index of this action in the session
        
        Returns:
            Path to saved screenshot, or None if failed
        """
        output_dir = session_dir or self._screenshot_dir
        key_frames_dir = output_dir / "key_frames"
        key_frames_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize context for filename
        safe_context = "".join(
            c if c.isalnum() or c in "_-" else "_" for c in context
        )[:20]
        
        filename = f"{action_type}_{action_index:03d}_{phase}_{safe_context}.png"
        
        try:
            screenshot_data = await self._bridge.take_screenshot(
                format="png",
                full_page=False,
            )
            
            frame_path = key_frames_dir / filename
            frame_path.write_bytes(screenshot_data)
            return frame_path
            
        except Exception:
            return None
    
    async def capture_periodic(self) -> Optional[CaptureResult]:
        """
        Capture periodic screenshot (for time-based loop outside sessions).
        
        This is a simpler version for general monitoring.
        """
        return await self.capture("periodic", highlight=False)
    
    def get_latest_screenshot(self) -> Optional[Path]:
        """Get path to the most recent screenshot."""
        if self._seq == 0:
            return None
        
        # Find most recent PNG
        screenshots = sorted(self._screenshot_dir.glob("*.png"))
        return screenshots[-1] if screenshots else None
    
    def get_latest_snapshot(self) -> Optional[Path]:
        """Get path to the most recent DOM snapshot."""
        if not self._take_snapshots or self._seq == 0:
            return None
        
        snapshots = sorted(self._snapshot_dir.glob("*.html"))
        return snapshots[-1] if snapshots else None
    
    def cleanup_old(self, keep_count: int = 100) -> int:
        """
        Remove old screenshots/snapshots, keeping the most recent.
        
        Args:
            keep_count: Number of recent captures to keep
        
        Returns:
            Number of files removed
        """
        removed = 0
        
        # Cleanup screenshots
        screenshots = sorted(self._screenshot_dir.glob("*.png"))
        for path in screenshots[:-keep_count]:
            try:
                path.unlink()
                removed += 1
            except Exception:
                pass
        
        # Cleanup snapshots
        if self._take_snapshots:
            snapshots = sorted(self._snapshot_dir.glob("*.html"))
            for path in snapshots[:-keep_count]:
                try:
                    path.unlink()
                    removed += 1
                except Exception:
                    pass
        
        return removed


def annotate_screenshot(
    image_data: bytes,
    element_box: dict,
    label: str = "",
) -> bytes:
    """
    Annotate a screenshot with element highlight.
    
    Draws a red box around the specified element and optionally
    adds a label. Requires Pillow.
    
    Args:
        image_data: PNG screenshot bytes
        element_box: Dict with x, y, width, height
        label: Optional label text
    
    Returns:
        Annotated PNG bytes
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Load image
        img = Image.open(io.BytesIO(image_data))
        draw = ImageDraw.Draw(img)
        
        # Draw rectangle
        x = element_box.get("x", 0)
        y = element_box.get("y", 0)
        width = element_box.get("width", 100)
        height = element_box.get("height", 50)
        
        # Red outline
        draw.rectangle(
            [x, y, x + width, y + height],
            outline="red",
            width=3,
        )
        
        # Add label if provided
        if label:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
            except Exception:
                font = ImageFont.load_default()
            
            # Label background
            text_bbox = draw.textbbox((x, y - 20), label, font=font)
            draw.rectangle(text_bbox, fill="red")
            draw.text((x, y - 20), label, fill="white", font=font)
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
        
    except ImportError:
        # Pillow not installed, return original
        return image_data
    except Exception:
        # Any error, return original
        return image_data

