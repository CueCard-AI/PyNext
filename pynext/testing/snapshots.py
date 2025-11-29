"""
PyNext Testing - Snapshot Testing

Automatic HTML snapshot comparison.
One function to create, compare, and update snapshots.

Example:
    from pynext.testing import render, assert_snapshot
    
    def test_card():
        result = render(Card, title="Hello")
        assert_snapshot(result, "card_basic")

How It Works:
    1. First run: Creates __snapshots__/card_basic.html
    2. Next runs: Compares rendered HTML to saved snapshot
    3. To update: Run with --update-snapshots flag

Why Snapshots:
    - Catch unintended UI changes
    - Visual regression detection
    - Fast to write, fast to run
    - Easy to review changes
"""

from __future__ import annotations

import difflib
import hashlib
import os
import re
from pathlib import Path
from typing import Optional

from pynext.testing.render import RenderResult


# =============================================================================
# Configuration
# =============================================================================

# Default snapshot directory name
SNAPSHOT_DIR = "__snapshots__"

# File extension for snapshots
SNAPSHOT_EXT = ".html"

# Environment variable to update snapshots
UPDATE_SNAPSHOTS_ENV = "PYNEXT_UPDATE_SNAPSHOTS"


def get_snapshot_dir(test_file: Optional[str] = None) -> Path:
    """
    Get the snapshot directory for a test file.
    
    Snapshots are stored in __snapshots__/ next to the test file.
    
    Args:
        test_file: Path to the test file (auto-detected if None)
        
    Returns:
        Path to snapshot directory
    """
    if test_file is None:
        # Try to detect from call stack
        import inspect
        for frame_info in inspect.stack():
            file_path = frame_info.filename
            if "test_" in os.path.basename(file_path):
                test_file = file_path
                break
        
        if test_file is None:
            # Fallback to current directory
            test_file = "."
    
    test_dir = Path(test_file).parent
    return test_dir / SNAPSHOT_DIR


def should_update_snapshots() -> bool:
    """Check if snapshots should be updated."""
    return os.environ.get(UPDATE_SNAPSHOTS_ENV, "").lower() in ("1", "true", "yes")


# =============================================================================
# HTML Normalization
# =============================================================================

def normalize_html(html: str) -> str:
    """
    Normalize HTML for consistent comparisons.
    
    Removes:
    - Extra whitespace
    - Dynamic IDs
    - Random hashes
    - Timestamps
    
    This ensures snapshots don't fail due to irrelevant differences.
    """
    # Remove extra whitespace
    html = re.sub(r"\s+", " ", html)
    html = re.sub(r"> <", ">\n<", html)
    html = html.strip()
    
    # Normalize self-closing tags
    html = re.sub(r"<(\w+)([^>]*?)\s*/>", r"<\1\2 />", html)
    
    # Remove dynamic IDs (uuid patterns)
    html = re.sub(
        r'id="[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"',
        'id="[dynamic-id]"',
        html
    )
    
    # Remove timestamp-like patterns
    html = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '[timestamp]', html)
    
    # Remove random hashes (common in bundled CSS)
    html = re.sub(r'_[a-f0-9]{6,8}', '_[hash]', html)
    
    return html


def format_html(html: str) -> str:
    """
    Format HTML for readable snapshots.
    
    Adds indentation and line breaks for easier review.
    """
    # Simple formatting - indent nested tags
    lines = []
    indent = 0
    
    for part in re.split(r"(<[^>]+>)", html):
        part = part.strip()
        if not part:
            continue
        
        if part.startswith("</"):
            indent = max(0, indent - 1)
            lines.append("  " * indent + part)
        elif part.startswith("<") and not part.endswith("/>"):
            lines.append("  " * indent + part)
            if not part.startswith("<!") and not part.startswith("<?"):
                # Check if it's a void element
                tag = re.match(r"<(\w+)", part)
                if tag and tag.group(1) not in ("br", "hr", "img", "input", "meta", "link", "area", "base", "col", "embed", "param", "source", "track", "wbr"):
                    indent += 1
        else:
            lines.append("  " * indent + part)
    
    return "\n".join(lines)


# =============================================================================
# Diff Generation
# =============================================================================

def generate_diff(expected: str, actual: str) -> str:
    """
    Generate a human-readable diff between expected and actual.
    
    Shows added/removed lines with context.
    """
    expected_lines = expected.splitlines()
    actual_lines = actual.splitlines()
    
    diff = difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile="snapshot",
        tofile="actual",
        lineterm="",
    )
    
    return "\n".join(diff)


# =============================================================================
# Snapshot Assertions
# =============================================================================

def assert_snapshot(
    result: RenderResult,
    name: str,
    test_file: Optional[str] = None,
) -> None:
    """
    Assert that rendered HTML matches saved snapshot.
    
    On first run, creates the snapshot file.
    On subsequent runs, compares to saved snapshot.
    
    Args:
        result: RenderResult from render()
        name: Name for the snapshot (used as filename)
        test_file: Path to test file (auto-detected if None)
        
    Example:
        def test_button():
            result = render(Button, label="Click")
            assert_snapshot(result, "button_default")
        
        def test_button_disabled():
            result = render(Button, disabled=True)
            assert_snapshot(result, "button_disabled")
    """
    snapshot_dir = get_snapshot_dir(test_file)
    snapshot_path = snapshot_dir / f"{name}{SNAPSHOT_EXT}"
    
    # Normalize and format the actual HTML
    actual = normalize_html(result.html)
    formatted_actual = format_html(actual)
    
    # Check if snapshot exists
    if snapshot_path.exists():
        # Compare to existing snapshot
        expected = snapshot_path.read_text()
        expected_normalized = normalize_html(expected)
        
        if expected_normalized != actual:
            if should_update_snapshots():
                # Update snapshot
                snapshot_path.write_text(formatted_actual)
                print(f"  📸 Updated snapshot: {name}")
            else:
                # Show diff and fail
                diff = generate_diff(expected, formatted_actual)
                raise AssertionError(
                    f"Snapshot mismatch: {name}\n\n"
                    f"Run with PYNEXT_UPDATE_SNAPSHOTS=1 to update.\n\n"
                    f"Diff:\n{diff}"
                )
    else:
        # Create new snapshot
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(formatted_actual)
        print(f"  📸 Created snapshot: {name}")


def assert_snapshot_matches(
    html: str,
    name: str,
    test_file: Optional[str] = None,
) -> None:
    """
    Assert that raw HTML string matches saved snapshot.
    
    Like assert_snapshot but takes HTML string directly.
    Useful for testing HTML generation utilities.
    
    Args:
        html: HTML string to compare
        name: Name for the snapshot
        test_file: Path to test file
        
    Example:
        html = generate_email_template(user)
        assert_snapshot_matches(html, "welcome_email")
    """
    # Create a mock RenderResult
    from pynext.testing.render import RenderResult
    result = RenderResult(html=html)
    assert_snapshot(result, name, test_file)


# =============================================================================
# Snapshot Management
# =============================================================================

def list_snapshots(test_file: Optional[str] = None) -> list[Path]:
    """
    List all snapshots for a test file.
    
    Args:
        test_file: Path to test file
        
    Returns:
        List of snapshot file paths
    """
    snapshot_dir = get_snapshot_dir(test_file)
    if not snapshot_dir.exists():
        return []
    
    return list(snapshot_dir.glob(f"*{SNAPSHOT_EXT}"))


def delete_snapshot(name: str, test_file: Optional[str] = None) -> bool:
    """
    Delete a snapshot.
    
    Args:
        name: Snapshot name
        test_file: Path to test file
        
    Returns:
        True if deleted, False if not found
    """
    snapshot_dir = get_snapshot_dir(test_file)
    snapshot_path = snapshot_dir / f"{name}{SNAPSHOT_EXT}"
    
    if snapshot_path.exists():
        snapshot_path.unlink()
        return True
    return False


def clean_unused_snapshots(
    test_file: str,
    used_names: set[str],
) -> list[str]:
    """
    Remove snapshots that are no longer used.
    
    Args:
        test_file: Path to test file
        used_names: Set of snapshot names that are used
        
    Returns:
        List of deleted snapshot names
    """
    deleted = []
    snapshot_dir = get_snapshot_dir(test_file)
    
    if not snapshot_dir.exists():
        return deleted
    
    for snapshot_path in snapshot_dir.glob(f"*{SNAPSHOT_EXT}"):
        name = snapshot_path.stem
        if name not in used_names:
            snapshot_path.unlink()
            deleted.append(name)
    
    return deleted


def get_snapshot_hash(name: str, test_file: Optional[str] = None) -> Optional[str]:
    """
    Get hash of a snapshot for cache invalidation.
    
    Args:
        name: Snapshot name
        test_file: Path to test file
        
    Returns:
        SHA256 hash of snapshot content, or None if not found
    """
    snapshot_dir = get_snapshot_dir(test_file)
    snapshot_path = snapshot_dir / f"{name}{SNAPSHOT_EXT}"
    
    if not snapshot_path.exists():
        return None
    
    content = snapshot_path.read_bytes()
    return hashlib.sha256(content).hexdigest()

