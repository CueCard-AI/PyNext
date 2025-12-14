"""
PyNext Build - File Watcher

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Watches Python source files for changes and triggers recompilation.
Used by the dev server for instant feedback during development.

    from pynext.build.watcher import FileWatcher
    
    watcher = FileWatcher(["pages/", "components/"])
    
    @watcher.on_change
    def recompile(changed_files):
        for file in changed_files:
            compile_file(file)
    
    watcher.start()

=============================================================================
WHY THIS EXISTS
=============================================================================

Fast feedback loop is essential for developer productivity:

1. Developer saves a file
2. Watcher detects the change (< 10ms)
3. Only changed file is recompiled (< 50ms)
4. Browser is notified via HMR (< 10ms)
5. UI updates without full page reload

Total: < 100ms from save to update!

=============================================================================
IMPLEMENTATION
=============================================================================

We use the `watchdog` library for cross-platform file system events:
- Linux: inotify
- macOS: FSEvents
- Windows: ReadDirectoryChangesW

The watcher:
1. Monitors specified directories
2. Debounces rapid changes (saves can trigger multiple events)
3. Filters for .py files only
4. Checks if file contains @island
5. Calls registered callbacks

=============================================================================
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Set, Dict
from collections import defaultdict


__all__ = [
    "FileWatcher",
    "WatcherConfig",
    "ChangeEvent",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class WatcherConfig:
    """
    Configuration for the file watcher.
    
    Attributes:
        extensions: File extensions to watch (default: [".py"])
        ignore_dirs: Directories to ignore
        debounce_ms: Debounce delay in milliseconds
        recursive: Watch subdirectories
    """
    extensions: List[str] = field(default_factory=lambda: [".py"])
    ignore_dirs: Set[str] = field(default_factory=lambda: {
        "__pycache__", ".git", "node_modules", ".venv", ".pynext", "venv"
    })
    debounce_ms: int = 50
    recursive: bool = True


@dataclass
class ChangeEvent:
    """
    Represents a file change event.
    
    Attributes:
        path: Path to the changed file
        event_type: Type of change ("created", "modified", "deleted")
        timestamp: When the change occurred
    """
    path: str
    event_type: str
    timestamp: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


# =============================================================================
# FILE WATCHER
# =============================================================================

class FileWatcher:
    """
    Watches directories for file changes.
    
    Uses debouncing to handle rapid saves and filters for Python files.
    Callbacks are invoked with lists of changed files.
    
    Example:
        watcher = FileWatcher(["pages/", "components/"])
        
        @watcher.on_change
        def handle_change(events):
            for event in events:
                print(f"{event.event_type}: {event.path}")
                compile_file(event.path)
        
        watcher.start()
        
        # ... later
        watcher.stop()
    """
    
    def __init__(
        self,
        directories: List[str | Path],
        config: Optional[WatcherConfig] = None,
    ):
        """
        Initialize the file watcher.
        
        Args:
            directories: List of directories to watch
            config: Watcher configuration
        """
        self.directories = [Path(d).resolve() for d in directories]
        self.config = config or WatcherConfig()
        
        self._callbacks: List[Callable[[List[ChangeEvent]], None]] = []
        self._running = False
        self._observer = None
        self._pending_events: Dict[str, ChangeEvent] = {}
        self._debounce_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
    
    def on_change(self, callback: Callable[[List[ChangeEvent]], None]) -> Callable:
        """
        Register a callback for file changes.
        
        Can be used as a decorator or called directly.
        
        Args:
            callback: Function to call with list of change events
        
        Returns:
            The callback function (for decorator use)
        
        Example:
            @watcher.on_change
            def handle(events):
                for event in events:
                    print(event.path)
        """
        self._callbacks.append(callback)
        return callback
    
    def start(self) -> None:
        """
        Start watching for file changes.
        
        This is non-blocking. The watcher runs in a background thread.
        
        Example:
            watcher.start()
            # ... do other things
            watcher.stop()
        """
        if self._running:
            return
        
        self._running = True
        
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
            
            class Handler(FileSystemEventHandler):
                def __init__(handler_self, watcher: FileWatcher):
                    handler_self.watcher = watcher
                
                def on_modified(handler_self, event):
                    if not event.is_directory:
                        handler_self.watcher._handle_event(event.src_path, "modified")
                
                def on_created(handler_self, event):
                    if not event.is_directory:
                        handler_self.watcher._handle_event(event.src_path, "created")
                
                def on_deleted(handler_self, event):
                    if not event.is_directory:
                        handler_self.watcher._handle_event(event.src_path, "deleted")
            
            self._observer = Observer()
            handler = Handler(self)
            
            for directory in self.directories:
                if directory.exists():
                    self._observer.schedule(
                        handler,
                        str(directory),
                        recursive=self.config.recursive,
                    )
            
            self._observer.start()
            
        except ImportError:
            # Fallback to polling if watchdog is not available
            self._start_polling()
    
    def _start_polling(self) -> None:
        """Start a polling-based watcher (fallback)."""
        import threading
        
        self._file_mtimes: Dict[str, float] = {}
        
        # Initial scan
        for directory in self.directories:
            for root, dirs, files in os.walk(directory):
                # Filter directories
                dirs[:] = [d for d in dirs if d not in self.config.ignore_dirs]
                
                for file in files:
                    if any(file.endswith(ext) for ext in self.config.extensions):
                        path = os.path.join(root, file)
                        try:
                            self._file_mtimes[path] = os.path.getmtime(path)
                        except OSError:
                            pass
        
        def poll_loop():
            while self._running:
                time.sleep(0.5)  # Poll every 500ms
                
                changed = []
                
                for directory in self.directories:
                    if not directory.exists():
                        continue
                        
                    for root, dirs, files in os.walk(directory):
                        dirs[:] = [d for d in dirs if d not in self.config.ignore_dirs]
                        
                        for file in files:
                            if any(file.endswith(ext) for ext in self.config.extensions):
                                path = os.path.join(root, file)
                                try:
                                    mtime = os.path.getmtime(path)
                                    old_mtime = self._file_mtimes.get(path)
                                    
                                    if old_mtime is None:
                                        self._file_mtimes[path] = mtime
                                        changed.append(ChangeEvent(path, "created"))
                                    elif mtime != old_mtime:
                                        self._file_mtimes[path] = mtime
                                        changed.append(ChangeEvent(path, "modified"))
                                except OSError:
                                    if path in self._file_mtimes:
                                        del self._file_mtimes[path]
                                        changed.append(ChangeEvent(path, "deleted"))
                
                if changed:
                    self._fire_callbacks(changed)
        
        self._poll_thread = threading.Thread(target=poll_loop, daemon=True)
        self._poll_thread.start()
    
    def stop(self) -> None:
        """
        Stop watching for file changes.
        
        Example:
            watcher.stop()
        """
        self._running = False
        
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=1.0)
            self._observer = None
        
        if self._debounce_timer:
            self._debounce_timer.cancel()
            self._debounce_timer = None
    
    def _handle_event(self, path: str, event_type: str) -> None:
        """Handle a file system event with debouncing."""
        # Check extension
        if not any(path.endswith(ext) for ext in self.config.extensions):
            return
        
        # Check for ignored directories
        path_parts = Path(path).parts
        if any(part in self.config.ignore_dirs for part in path_parts):
            return
        
        # Add to pending events
        with self._lock:
            self._pending_events[path] = ChangeEvent(path, event_type)
            
            # Reset debounce timer
            if self._debounce_timer:
                self._debounce_timer.cancel()
            
            self._debounce_timer = threading.Timer(
                self.config.debounce_ms / 1000.0,
                self._flush_events,
            )
            self._debounce_timer.start()
    
    def _flush_events(self) -> None:
        """Flush pending events to callbacks."""
        with self._lock:
            events = list(self._pending_events.values())
            self._pending_events.clear()
        
        if events:
            self._fire_callbacks(events)
    
    def _fire_callbacks(self, events: List[ChangeEvent]) -> None:
        """Call all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(events)
            except Exception as e:
                print(f"[PyNext Watcher] Callback error: {e}")
    
    @property
    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running
    
    def __enter__(self) -> "FileWatcher":
        self.start()
        return self
    
    def __exit__(self, *args) -> None:
        self.stop()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def watch_and_compile(
    directories: List[str | Path],
    output_dir: str | Path,
    on_compile: Optional[Callable[[str], None]] = None,
) -> FileWatcher:
    """
    Watch directories and recompile islands on change.
    
    Args:
        directories: Directories to watch
        output_dir: Where to write compiled files
        on_compile: Optional callback after compilation
    
    Returns:
        FileWatcher instance (already started)
    
    Example:
        watcher = watch_and_compile(
            ["pages/", "components/"],
            ".pynext/build",
            on_compile=lambda f: print(f"Compiled: {f}")
        )
        
        # ... later
        watcher.stop()
    """
    from pynext.build.scanner import is_island_file
    from pynext.compiler import compile_file
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    watcher = FileWatcher(directories)
    
    @watcher.on_change
    def handle_change(events: List[ChangeEvent]):
        for event in events:
            if event.event_type == "deleted":
                continue
            
            if not is_island_file(event.path):
                continue
            
            try:
                result = compile_file(event.path)
                
                if result.errors:
                    print(f"[PyNext] Compile error: {event.path}")
                    for error in result.errors:
                        print(f"  {error}")
                else:
                    # Write output
                    name = Path(event.path).stem
                    output_file = output_path / f"{name}.js"
                    output_file.write_text(result.js)
                    
                    print(f"[PyNext] Compiled: {event.path}")
                    
                    if on_compile:
                        on_compile(event.path)
                        
            except Exception as e:
                print(f"[PyNext] Error: {e}")
    
    watcher.start()
    return watcher

