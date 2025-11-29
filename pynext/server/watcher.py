"""
Fast file watching with watchfiles (Rust-based).

Why watchfiles?
- Written in Rust, uses notify-rs
- Kernel-level events (inotify/FSEvents/ReadDirectoryChanges)
- ~1ms detection latency
- Automatic debouncing

Example:
    watcher = FileWatcher(project_root)
    
    async for change in watcher.watch():
        print(f"Changed: {change.path}")
        print(f"Type: {change.change_type}")
        print(f"Reload: {change.reload_type}")

Why This Matters:
    Fast file watching is the foundation of a good dev experience.
    Slow feedback kills productivity and flow state.
    Sub-50ms reload times keep developers in the zone.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import AsyncIterator, Callable, List, Optional, Set
import asyncio


# ============================================
# Change Types
# ============================================

class ChangeType(Enum):
    """
    Type of file change.
    
    Used to determine the optimal reload strategy.
    """
    PAGE = "page"           # pages/*.py changed
    COMPONENT = "component" # components/*.py changed
    LAYOUT = "layout"       # layout.py changed
    TEMPLATE = "template"   # template.py changed
    STATIC = "static"       # static/* or public/* changed
    CONFIG = "config"       # pynext.config.py changed
    API = "api"             # pages/api/* changed
    UNKNOWN = "unknown"     # Other files


# ============================================
# File Change Event
# ============================================

@dataclass
class FileChange:
    """
    A file change event.
    
    Attributes:
        path: Absolute path to changed file
        change_type: Classification of the change
        is_delete: True if file was deleted
        project_root: Root directory of the project
    
    Example:
        change = FileChange(
            path=Path("/project/pages/index.py"),
            change_type=ChangeType.PAGE,
            is_delete=False,
            project_root=Path("/project"),
        )
        
        print(change.reload_type)  # "hot"
    """
    path: Path
    change_type: ChangeType
    is_delete: bool = False
    project_root: Optional[Path] = None
    
    @property
    def relative_path(self) -> str:
        """
        Get path relative to project root.
        
        Returns:
            Relative path string
        """
        if self.project_root:
            try:
                return str(self.path.relative_to(self.project_root))
            except ValueError:
                pass
        return str(self.path)
    
    @property
    def reload_type(self) -> str:
        """
        Determine reload strategy based on change type.
        
        Returns:
            "hot" - Hot reload (swap content without full refresh)
            "css" - CSS hot swap (instant, no flash)
            "full" - Full page reload (for config changes, etc.)
        """
        # Static files
        if self.change_type == ChangeType.STATIC:
            suffix = self.path.suffix.lower()
            if suffix == ".css":
                return "css"
            if suffix in (".js", ".ts"):
                return "full"  # Scripts need full reload
            # Images, fonts, etc. - full reload for simplicity
            return "full"
        
        # Config changes always need full reload
        if self.change_type == ChangeType.CONFIG:
            return "full"
        
        # Layout changes affect all pages
        if self.change_type == ChangeType.LAYOUT:
            return "full"
        
        # Template changes affect navigation
        if self.change_type == ChangeType.TEMPLATE:
            return "full"
        
        # API changes don't need visual reload
        if self.change_type == ChangeType.API:
            return "none"
        
        # Pages and components can hot reload
        if self.change_type in (ChangeType.PAGE, ChangeType.COMPONENT):
            return "hot"
        
        # Unknown - be safe with full reload
        return "full"
    
    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return self.path.suffix.lower()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": self.relative_path,
            "change_type": self.change_type.value,
            "reload_type": self.reload_type,
            "is_delete": self.is_delete,
            "extension": self.file_extension,
        }


# ============================================
# File Watcher
# ============================================

class FileWatcher:
    """
    Watch files for changes using watchfiles (Rust-based).
    
    Uses kernel-level file system events for maximum performance:
    - Linux: inotify
    - macOS: FSEvents
    - Windows: ReadDirectoryChangesW
    
    Attributes:
        root: Project root directory
        ignore_patterns: Patterns to ignore
        debounce_ms: Debounce window in milliseconds
    
    Example:
        watcher = FileWatcher(Path("/my/project"))
        
        async for change in watcher.watch():
            print(f"File changed: {change.relative_path}")
            
            if change.reload_type == "hot":
                await hot_reload(change)
            elif change.reload_type == "css":
                await css_swap(change)
            else:
                await full_reload()
    """
    
    # Default patterns to ignore
    DEFAULT_IGNORE = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".git",
        ".pynext",
        ".next",
        "node_modules",
        ".env",
        ".env.*",
        "*.log",
        ".DS_Store",
        "Thumbs.db",
        "*.swp",
        "*.swo",
        "*~",
        ".idea",
        ".vscode",
    ]
    
    def __init__(
        self,
        root: Path,
        ignore_patterns: Optional[List[str]] = None,
        debounce_ms: int = 10,
    ):
        """
        Initialize file watcher.
        
        Args:
            root: Project root directory to watch
            ignore_patterns: Additional glob patterns to ignore
            debounce_ms: Debounce rapid changes (default 10ms)
        
        Example:
            # Basic usage
            watcher = FileWatcher(Path("."))
            
            # With custom ignore patterns
            watcher = FileWatcher(
                Path("."),
                ignore_patterns=["*.tmp", "build/*"],
                debounce_ms=20,
            )
        """
        self.root = Path(root).resolve()
        self.ignore_patterns = self.DEFAULT_IGNORE + (ignore_patterns or [])
        self.debounce_ms = debounce_ms
        self._running = False
        self._callbacks: List[Callable[[FileChange], None]] = []
    
    def _classify_change(self, path: Path) -> ChangeType:
        """
        Classify a file change based on its location.
        
        Args:
            path: Path to the changed file (absolute or relative)
        
        Returns:
            ChangeType classification
        """
        # Try to get relative path
        try:
            if path.is_absolute():
                rel_path = path.relative_to(self.root)
            else:
                # Already relative or can't be made relative to root
                # Try to see if it starts with root parts
                try:
                    rel_path = path.relative_to(self.root)
                except ValueError:
                    rel_path = path
        except ValueError:
            rel_path = path
        
        parts = rel_path.parts
        if not parts:
            return ChangeType.UNKNOWN
        
        # Handle src/ folder structure
        adjusted_parts = parts
        if parts[0] == "src" and len(parts) > 1:
            adjusted_parts = parts[1:]
        
        first_part = adjusted_parts[0] if adjusted_parts else ""
        filename = path.name
        
        # Config file (check before directory checks)
        if filename == "pynext.config.py":
            return ChangeType.CONFIG
        
        # Pages directory
        if first_part == "pages":
            # API routes
            if len(adjusted_parts) > 1 and adjusted_parts[1] == "api":
                return ChangeType.API
            
            # Layout file
            if filename == "layout.py":
                return ChangeType.LAYOUT
            
            # Template file
            if filename == "template.py":
                return ChangeType.TEMPLATE
            
            # Regular page
            return ChangeType.PAGE
        
        # Components directory
        if first_part == "components":
            return ChangeType.COMPONENT
        
        # Static/public directories
        if first_part in ("public", "static"):
            return ChangeType.STATIC
        
        # Unknown
        return ChangeType.UNKNOWN
    
    def _should_ignore(self, path: Path) -> bool:
        """
        Check if a path should be ignored.
        
        Args:
            path: Path to check
        
        Returns:
            True if path should be ignored
        """
        path_str = str(path)
        
        for pattern in self.ignore_patterns:
            # Exact match
            if pattern in path_str:
                return True
            
            # Wildcard suffix (*.pyc)
            if pattern.startswith("*") and path_str.endswith(pattern[1:]):
                return True
            
            # Wildcard prefix (*~)
            if pattern.endswith("*") and pattern[:-1] in path_str:
                return True
        
        return False
    
    async def watch(self) -> AsyncIterator[FileChange]:
        """
        Watch for file changes.
        
        Yields FileChange events when files are modified, created, or deleted.
        Uses watchfiles (Rust) for kernel-level performance.
        
        Yields:
            FileChange events
        
        Raises:
            ImportError: If watchfiles is not installed
        
        Example:
            async for change in watcher.watch():
                print(f"Changed: {change.relative_path}")
                print(f"Type: {change.change_type.value}")
        """
        try:
            import watchfiles
        except ImportError:
            raise ImportError(
                "watchfiles is required for the dev server.\n"
                "Install with: pip install watchfiles\n"
                "Or add 'watchfiles' to pynext.requirements.txt"
            )
        
        self._running = True
        
        # Configure watch
        async for changes in watchfiles.awatch(
            self.root,
            debounce=self.debounce_ms,
            recursive=True,
            step=50,  # Check for stop every 50ms
        ):
            if not self._running:
                break
            
            for change_enum, path_str in changes:
                path = Path(path_str)
                
                # Skip ignored paths
                if self._should_ignore(path):
                    continue
                
                # Determine if delete
                is_delete = change_enum == watchfiles.Change.deleted
                
                # Classify and yield
                file_change = FileChange(
                    path=path,
                    change_type=self._classify_change(path),
                    is_delete=is_delete,
                    project_root=self.root,
                )
                
                yield file_change
    
    def stop(self):
        """
        Stop watching for changes.
        
        Call this to gracefully stop the watcher.
        """
        self._running = False
    
    def add_callback(self, callback: Callable[[FileChange], None]):
        """
        Add a callback to be called on file changes.
        
        Args:
            callback: Function to call with FileChange
        """
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[FileChange], None]):
        """
        Remove a callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)


# ============================================
# Convenience Functions
# ============================================

def create_watcher(
    root: str = ".",
    ignore: Optional[List[str]] = None,
) -> FileWatcher:
    """
    Create a file watcher with sensible defaults.
    
    Args:
        root: Project root directory
        ignore: Additional patterns to ignore
    
    Returns:
        Configured FileWatcher
    
    Example:
        watcher = create_watcher()
        
        async for change in watcher.watch():
            print(change)
    """
    return FileWatcher(
        root=Path(root),
        ignore_patterns=ignore,
    )


async def watch_once(root: str = ".") -> FileChange:
    """
    Watch for a single file change.
    
    Useful for testing or simple scripts.
    
    Args:
        root: Project root directory
    
    Returns:
        First FileChange event
    
    Example:
        change = await watch_once()
        print(f"First change: {change.relative_path}")
    """
    watcher = create_watcher(root)
    
    async for change in watcher.watch():
        watcher.stop()
        return change
    
    raise RuntimeError("Watcher stopped without changes")

