"""
PyNext Testing - Visual Regression

Screenshot-based visual comparison testing.
Catch visual bugs before they reach production.

Example:
    from pynext.testing import render, assert_visual_match
    
    def test_button_visual():
        result = render(Button, variant="primary")
        assert_visual_match(result, "button_primary")

How It Works:
    1. Renders component to HTML
    2. Converts HTML to image using Pillow
    3. Compares to baseline image
    4. Shows diff if mismatch

Requirements:
    - Pillow for image generation
    - wkhtmltopdf or Playwright for HTML-to-image (optional)

Why Visual Testing:
    - Catch CSS regressions
    - Verify responsive layouts
    - Test across themes
    - Document visual appearance
"""

from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
from typing import Optional, Tuple

from pynext.testing.render import RenderResult


# =============================================================================
# Configuration
# =============================================================================

VISUAL_SNAPSHOT_DIR = "__visual_snapshots__"
UPDATE_VISUAL_ENV = "PYNEXT_UPDATE_VISUAL"
DIFF_THRESHOLD = 0.01  # 1% pixel difference allowed


def get_visual_dir(test_file: Optional[str] = None) -> Path:
    """Get the visual snapshot directory."""
    if test_file is None:
        import inspect
        for frame_info in inspect.stack():
            file_path = frame_info.filename
            if "test_" in os.path.basename(file_path):
                test_file = file_path
                break
        if test_file is None:
            test_file = "."
    
    test_dir = Path(test_file).parent
    return test_dir / VISUAL_SNAPSHOT_DIR


def should_update_visual() -> bool:
    """Check if visual snapshots should be updated."""
    return os.environ.get(UPDATE_VISUAL_ENV, "").lower() in ("1", "true", "yes")


# =============================================================================
# HTML to Image Conversion
# =============================================================================

def html_to_image(
    html: str,
    width: int = 800,
    height: int = 600,
    scale: float = 1.0,
) -> bytes:
    """
    Convert HTML to PNG image.
    
    Uses simple CSS rendering for basic components.
    For full rendering, requires Playwright or wkhtmltopdf.
    
    Args:
        html: HTML content to render
        width: Viewport width
        height: Viewport height
        scale: Scale factor for high DPI
        
    Returns:
        PNG image as bytes
    """
    try:
        # Try Playwright first (best quality)
        return _render_with_playwright(html, width, height, scale)
    except ImportError:
        pass
    
    try:
        # Fall back to simple Pillow rendering
        return _render_with_pillow(html, width, height)
    except ImportError:
        raise ImportError(
            "Visual testing requires Pillow. Install with: pip install Pillow\n"
            "For better quality, also install: pip install playwright && playwright install chromium"
        )


def _render_with_playwright(
    html: str,
    width: int,
    height: int,
    scale: float,
) -> bytes:
    """Render HTML using Playwright (browser-based, high quality)."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        
        # Wrap in basic HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ margin: 0; padding: 16px; font-family: system-ui; }}
            </style>
        </head>
        <body>{html}</body>
        </html>
        """
        
        page.set_content(full_html)
        screenshot = page.screenshot(full_page=False)
        browser.close()
        
        return screenshot


def _render_with_pillow(html: str, width: int, height: int) -> bytes:
    """Simple text-based rendering using Pillow."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create white background
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    
    # Simple text extraction from HTML
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    
    # Draw text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Word wrap
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] < width - 32:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(" ".join(current_line))
    
    # Draw lines
    y = 16
    for line in lines[:20]:  # Limit lines
        draw.text((16, y), line, fill="black", font=font)
        y += 20
    
    # Convert to PNG bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# =============================================================================
# Image Comparison
# =============================================================================

def compare_images(
    expected: bytes,
    actual: bytes,
    threshold: float = DIFF_THRESHOLD,
) -> Tuple[bool, float, Optional[bytes]]:
    """
    Compare two images and return diff.
    
    Args:
        expected: Expected image bytes
        actual: Actual image bytes
        threshold: Maximum allowed difference (0-1)
        
    Returns:
        Tuple of (matches, diff_percentage, diff_image_bytes)
    """
    from PIL import Image, ImageChops
    
    # Load images
    img1 = Image.open(io.BytesIO(expected)).convert("RGB")
    img2 = Image.open(io.BytesIO(actual)).convert("RGB")
    
    # Resize if dimensions differ
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
    
    # Calculate difference
    diff = ImageChops.difference(img1, img2)
    
    # Count different pixels
    diff_data = diff.getdata()
    total_pixels = len(diff_data)
    diff_pixels = sum(1 for pixel in diff_data if any(c > 10 for c in pixel))
    diff_percentage = diff_pixels / total_pixels
    
    matches = diff_percentage <= threshold
    
    # Generate diff image if mismatch
    diff_image = None
    if not matches:
        # Highlight differences in red
        diff_highlight = Image.new("RGB", img1.size, "white")
        
        for x in range(img1.size[0]):
            for y in range(img1.size[1]):
                p1 = img1.getpixel((x, y))
                p2 = img2.getpixel((x, y))
                
                if any(abs(a - b) > 10 for a, b in zip(p1, p2)):
                    diff_highlight.putpixel((x, y), (255, 0, 0))
                else:
                    diff_highlight.putpixel((x, y), p1)
        
        buffer = io.BytesIO()
        diff_highlight.save(buffer, format="PNG")
        diff_image = buffer.getvalue()
    
    return matches, diff_percentage, diff_image


# =============================================================================
# Visual Assertions
# =============================================================================

def assert_visual_match(
    result: RenderResult,
    name: str,
    width: int = 800,
    height: int = 600,
    threshold: float = DIFF_THRESHOLD,
    test_file: Optional[str] = None,
) -> None:
    """
    Assert that component visually matches baseline.
    
    Args:
        result: RenderResult from render()
        name: Name for the visual snapshot
        width: Viewport width
        height: Viewport height
        threshold: Maximum allowed difference (0-1)
        test_file: Path to test file
        
    Example:
        result = render(Button, variant="primary")
        assert_visual_match(result, "button_primary")
        
        # Different viewport
        assert_visual_match(result, "button_mobile", width=375)
    """
    visual_dir = get_visual_dir(test_file)
    baseline_path = visual_dir / f"{name}.png"
    diff_path = visual_dir / f"{name}.diff.png"
    actual_path = visual_dir / f"{name}.actual.png"
    
    # Render to image
    actual = html_to_image(result.html, width, height)
    
    if baseline_path.exists():
        # Compare to baseline
        expected = baseline_path.read_bytes()
        matches, diff_pct, diff_img = compare_images(expected, actual, threshold)
        
        if not matches:
            if should_update_visual():
                # Update baseline
                baseline_path.write_bytes(actual)
                if diff_path.exists():
                    diff_path.unlink()
                print(f"  🖼️ Updated visual: {name}")
            else:
                # Save actual and diff for debugging
                actual_path.write_bytes(actual)
                if diff_img:
                    diff_path.write_bytes(diff_img)
                
                raise AssertionError(
                    f"Visual mismatch: {name}\n"
                    f"Difference: {diff_pct:.2%}\n"
                    f"Threshold: {threshold:.2%}\n"
                    f"Actual saved to: {actual_path}\n"
                    f"Diff saved to: {diff_path}\n\n"
                    f"Run with PYNEXT_UPDATE_VISUAL=1 to update baseline."
                )
    else:
        # Create baseline
        visual_dir.mkdir(parents=True, exist_ok=True)
        baseline_path.write_bytes(actual)
        print(f"  🖼️ Created visual: {name}")


def assert_no_visual_regression(
    result: RenderResult,
    name: str,
    variants: dict[str, dict] = None,
    test_file: Optional[str] = None,
) -> None:
    """
    Test component across multiple visual variants.
    
    Useful for testing responsive layouts, themes, etc.
    
    Args:
        result: RenderResult from render()
        name: Base name for snapshots
        variants: Dict of variant name -> settings
        test_file: Path to test file
        
    Example:
        result = render(Card, title="Hello")
        assert_no_visual_regression(result, "card", {
            "desktop": {"width": 1200},
            "tablet": {"width": 768},
            "mobile": {"width": 375},
        })
    """
    variants = variants or {
        "default": {"width": 800, "height": 600}
    }
    
    for variant_name, settings in variants.items():
        snapshot_name = f"{name}_{variant_name}"
        assert_visual_match(
            result,
            snapshot_name,
            width=settings.get("width", 800),
            height=settings.get("height", 600),
            threshold=settings.get("threshold", DIFF_THRESHOLD),
            test_file=test_file,
        )


# =============================================================================
# Visual Snapshot Management
# =============================================================================

def list_visual_snapshots(test_file: Optional[str] = None) -> list[Path]:
    """List all visual snapshots."""
    visual_dir = get_visual_dir(test_file)
    if not visual_dir.exists():
        return []
    
    return [p for p in visual_dir.glob("*.png") if not p.name.endswith((".diff.png", ".actual.png"))]


def clean_visual_artifacts(test_file: Optional[str] = None) -> int:
    """Remove .diff.png and .actual.png files."""
    visual_dir = get_visual_dir(test_file)
    if not visual_dir.exists():
        return 0
    
    count = 0
    for path in visual_dir.glob("*.diff.png"):
        path.unlink()
        count += 1
    
    for path in visual_dir.glob("*.actual.png"):
        path.unlink()
        count += 1
    
    return count


def get_visual_hash(name: str, test_file: Optional[str] = None) -> Optional[str]:
    """Get hash of visual snapshot for caching."""
    visual_dir = get_visual_dir(test_file)
    path = visual_dir / f"{name}.png"
    
    if not path.exists():
        return None
    
    return hashlib.sha256(path.read_bytes()).hexdigest()

