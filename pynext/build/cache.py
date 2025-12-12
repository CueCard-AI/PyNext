"""
PyNext Build - Incremental Compilation Cache

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Manages a build cache to enable incremental compilation. Only files that have
changed since the last build are recompiled.

    from pynext.build.cache import BuildCache
    
    cache = BuildCache(".pynext/cache")
    
    # Check if file needs recompilation
    if cache.needs_compile("counter.py", source_hash):
        result = compile_file("counter.py")
        cache.store("counter.py", result.js, result.map, source_hash)
    else:
        js, map = cache.get("counter.py")

=============================================================================
WHY THIS EXISTS
=============================================================================

Without caching, every build recompiles everything:
- 100 islands × 5ms each = 500ms build time
- Change 1 file? Still 500ms!

With caching:
- First build: 500ms (cache miss)
- Change 1 file: 5ms (only recompile that file)
- No changes: 1ms (just check hashes)

This is how we achieve < 50ms incremental builds.

=============================================================================
CACHE STRUCTURE
=============================================================================

.pynext/
├── cache/
│   ├── manifest.json          # Maps file paths to cache entries
│   ├── counter_abc123.js      # Compiled JS (hash in filename)
│   ├── counter_abc123.js.map  # Source map
│   └── ...
└── build/                     # Production output

manifest.json:
{
    "version": "1.0",
    "entries": {
        "pages/dashboard.py": {
            "hash": "abc123...",
            "islands": ["Counter", "Stats"],
            "js_file": "dashboard_abc123.js",
            "compiled_at": "2024-01-01T00:00:00Z"
        }
    }
}

=============================================================================
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


__all__ = [
    "BuildCache",
    "CacheEntry",
    "CacheStats",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class CacheEntry:
    """
    A single cache entry for a compiled file.
    
    Attributes:
        source_hash: SHA256 hash of the source file
        islands: List of island names in the file
        js_file: Filename of the compiled JS
        map_file: Filename of the source map
        compiled_at: When the file was compiled
        compile_time_ms: How long compilation took
        output_size: Size of compiled JS in bytes
    """
    source_hash: str
    islands: List[str]
    js_file: str
    map_file: str = ""
    compiled_at: str = ""
    compile_time_ms: float = 0.0
    output_size: int = 0
    
    def __post_init__(self):
        if not self.compiled_at:
            self.compiled_at = datetime.utcnow().isoformat() + "Z"


@dataclass
class CacheStats:
    """
    Statistics about cache usage.
    
    Attributes:
        hits: Number of cache hits (no recompilation needed)
        misses: Number of cache misses (recompilation needed)
        total_entries: Total entries in cache
        cache_size_kb: Total cache size in KB
        oldest_entry: Timestamp of oldest entry
        newest_entry: Timestamp of newest entry
    """
    hits: int = 0
    misses: int = 0
    total_entries: int = 0
    cache_size_kb: float = 0.0
    oldest_entry: str = ""
    newest_entry: str = ""
    
    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a percentage."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100


# =============================================================================
# BUILD CACHE
# =============================================================================

class BuildCache:
    """
    Manages incremental compilation cache.
    
    The cache stores compiled JavaScript and source maps, keyed by
    source file hash. Only files that have changed need recompilation.
    
    Example:
        cache = BuildCache(".pynext/cache")
        
        # Check if file needs recompilation
        source_hash = hash_file("counter.py")
        if cache.needs_compile("counter.py", source_hash):
            result = compile_file("counter.py")
            cache.store("counter.py", result.js, result.map, source_hash, ["Counter"])
        else:
            js, map = cache.get("counter.py")
    """
    
    MANIFEST_FILE = "manifest.json"
    CACHE_VERSION = "1.0"
    
    def __init__(self, cache_dir: str | Path):
        """
        Initialize the build cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self._manifest: Dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._dirty = False
        
        # Load existing manifest
        self._load_manifest()
    
    def _load_manifest(self) -> None:
        """Load the cache manifest from disk."""
        manifest_path = self.cache_dir / self.MANIFEST_FILE
        
        if not manifest_path.exists():
            return
        
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            
            # Check version
            if data.get("version") != self.CACHE_VERSION:
                # Version mismatch - clear cache
                self.clear()
                return
            
            # Load entries
            for file_path, entry_data in data.get("entries", {}).items():
                self._manifest[file_path] = CacheEntry(**entry_data)
            
            self._stats.total_entries = len(self._manifest)
            
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            # Corrupted manifest - clear cache
            self.clear()
    
    def _save_manifest(self) -> None:
        """Save the cache manifest to disk."""
        if not self._dirty:
            return
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.cache_dir / self.MANIFEST_FILE
        
        data = {
            "version": self.CACHE_VERSION,
            "entries": {
                path: asdict(entry) for path, entry in self._manifest.items()
            },
        }
        
        manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._dirty = False
    
    def needs_compile(self, file_path: str, source_hash: str) -> bool:
        """
        Check if a file needs recompilation.
        
        Args:
            file_path: Path to the source file
            source_hash: Current hash of the source file
        
        Returns:
            True if the file needs recompilation
        
        Example:
            source_hash = hash_file("counter.py")
            if cache.needs_compile("counter.py", source_hash):
                # Recompile needed
                ...
        """
        normalized_path = self._normalize_path(file_path)
        
        if normalized_path not in self._manifest:
            self._stats.misses += 1
            return True
        
        entry = self._manifest[normalized_path]
        
        if entry.source_hash != source_hash:
            self._stats.misses += 1
            return True
        
        # Check if cached files still exist
        js_path = self.cache_dir / entry.js_file
        if not js_path.exists():
            self._stats.misses += 1
            return True
        
        self._stats.hits += 1
        return False
    
    def get(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get cached compilation result.
        
        Args:
            file_path: Path to the source file
        
        Returns:
            Tuple of (js_content, map_content) or (None, None) if not cached
        
        Example:
            js, source_map = cache.get("counter.py")
            if js is not None:
                # Use cached result
                ...
        """
        normalized_path = self._normalize_path(file_path)
        
        if normalized_path not in self._manifest:
            return None, None
        
        entry = self._manifest[normalized_path]
        
        js_path = self.cache_dir / entry.js_file
        map_path = self.cache_dir / entry.map_file if entry.map_file else None
        
        try:
            js_content = js_path.read_text(encoding="utf-8") if js_path.exists() else None
            map_content = map_path.read_text(encoding="utf-8") if map_path and map_path.exists() else None
            return js_content, map_content
        except Exception:
            return None, None
    
    def store(
        self,
        file_path: str,
        js_content: str,
        map_content: Optional[str],
        source_hash: str,
        islands: List[str],
        compile_time_ms: float = 0.0,
    ) -> None:
        """
        Store a compilation result in the cache.
        
        Args:
            file_path: Path to the source file
            js_content: Compiled JavaScript
            map_content: Source map (optional)
            source_hash: Hash of the source file
            islands: List of island names in the file
            compile_time_ms: How long compilation took
        
        Example:
            result = compile_file("counter.py")
            cache.store(
                "counter.py",
                result.js,
                result.map,
                source_hash,
                ["Counter"],
                compile_time_ms=5.2
            )
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        normalized_path = self._normalize_path(file_path)
        
        # Generate unique filenames based on hash
        base_name = Path(file_path).stem
        js_file = f"{base_name}_{source_hash[:8]}.js"
        map_file = f"{base_name}_{source_hash[:8]}.js.map" if map_content else ""
        
        # Remove old cache files if entry exists
        if normalized_path in self._manifest:
            old_entry = self._manifest[normalized_path]
            self._remove_cached_files(old_entry)
        
        # Write new cache files
        js_path = self.cache_dir / js_file
        js_path.write_text(js_content, encoding="utf-8")
        
        if map_content and map_file:
            map_path = self.cache_dir / map_file
            map_path.write_text(map_content, encoding="utf-8")
        
        # Create cache entry
        entry = CacheEntry(
            source_hash=source_hash,
            islands=islands,
            js_file=js_file,
            map_file=map_file,
            compile_time_ms=compile_time_ms,
            output_size=len(js_content),
        )
        
        self._manifest[normalized_path] = entry
        self._stats.total_entries = len(self._manifest)
        self._dirty = True
        self._save_manifest()
    
    def invalidate(self, file_path: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            file_path: Path to the source file
        
        Returns:
            True if entry was invalidated, False if not found
        
        Example:
            cache.invalidate("counter.py")
        """
        normalized_path = self._normalize_path(file_path)
        
        if normalized_path not in self._manifest:
            return False
        
        entry = self._manifest[normalized_path]
        self._remove_cached_files(entry)
        del self._manifest[normalized_path]
        
        self._stats.total_entries = len(self._manifest)
        self._dirty = True
        self._save_manifest()
        
        return True
    
    def clear(self) -> None:
        """
        Clear the entire cache.
        
        Removes all cached files and the manifest.
        
        Example:
            cache.clear()  # Start fresh
        """
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        
        self._manifest = {}
        self._stats = CacheStats()
        self._dirty = False
    
    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.
        
        Returns:
            CacheStats with hit/miss counts and cache size
        
        Example:
            stats = cache.get_stats()
            print(f"Hit rate: {stats.hit_rate:.1f}%")
        """
        # Calculate cache size
        total_size = 0
        oldest = ""
        newest = ""
        
        for entry in self._manifest.values():
            total_size += entry.output_size
            
            if not oldest or entry.compiled_at < oldest:
                oldest = entry.compiled_at
            if not newest or entry.compiled_at > newest:
                newest = entry.compiled_at
        
        self._stats.cache_size_kb = total_size / 1024
        self._stats.total_entries = len(self._manifest)
        self._stats.oldest_entry = oldest
        self._stats.newest_entry = newest
        
        return self._stats
    
    def get_entry(self, file_path: str) -> Optional[CacheEntry]:
        """
        Get cache entry metadata.
        
        Args:
            file_path: Path to the source file
        
        Returns:
            CacheEntry or None if not cached
        """
        normalized_path = self._normalize_path(file_path)
        return self._manifest.get(normalized_path)
    
    def get_all_entries(self) -> Dict[str, CacheEntry]:
        """
        Get all cache entries.
        
        Returns:
            Dict mapping file paths to cache entries
        """
        return dict(self._manifest)
    
    def _normalize_path(self, file_path: str) -> str:
        """Normalize a file path for consistent lookup."""
        return str(Path(file_path).resolve())
    
    def _remove_cached_files(self, entry: CacheEntry) -> None:
        """Remove cached files for an entry."""
        try:
            js_path = self.cache_dir / entry.js_file
            if js_path.exists():
                js_path.unlink()
            
            if entry.map_file:
                map_path = self.cache_dir / entry.map_file
                if map_path.exists():
                    map_path.unlink()
        except Exception:
            pass


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def hash_file(file_path: str | Path) -> str:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hex-encoded hash string
    
    Example:
        hash = hash_file("counter.py")
        # "abc123..."
    """
    path = Path(file_path)
    
    if not path.exists():
        return ""
    
    try:
        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except Exception:
        return ""


def hash_content(content: str) -> str:
    """
    Calculate SHA256 hash of a string.
    
    Args:
        content: String content
    
    Returns:
        Hex-encoded hash string
    
    Example:
        hash = hash_content("def counter(): ...")
        # "abc123..."
    """
    return hashlib.sha256(content.encode()).hexdigest()

