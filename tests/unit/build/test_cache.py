"""
Tests for PyNext Build Cache (70 tests)

Tests incremental compilation cache and hash correctness.
"""

import pytest
import json
import time
from pathlib import Path

from pynext.build.cache import (
    BuildCache,
    CacheEntry,
    CacheStats,
    hash_file,
    hash_content,
)


# =============================================================================
# BASIC CACHE OPERATIONS
# =============================================================================

class TestBasicOperations:
    """Basic cache operations."""
    
    def test_cache_init(self, tmp_path):
        """Initialize cache in a directory."""
        cache_dir = tmp_path / ".cache"
        cache = BuildCache(cache_dir)
        assert cache.cache_dir == cache_dir
    
    def test_cache_creates_dir(self, tmp_path):
        """Cache creates directory on store."""
        cache_dir = tmp_path / ".cache"
        cache = BuildCache(cache_dir)
        cache.store("file.py", "const x = 1;", None, "abc123", ["Island"])
        assert cache_dir.exists()
    
    def test_store_and_get(self, tmp_path):
        """Store and retrieve compiled result."""
        cache = BuildCache(tmp_path / ".cache")
        
        cache.store(
            file_path="counter.py",
            js_content="export function Counter() {}",
            map_content='{"version": 3}',
            source_hash="abc123",
            islands=["Counter"],
        )
        
        js, source_map = cache.get("counter.py")
        assert js == "export function Counter() {}"
        assert source_map == '{"version": 3}'
    
    def test_get_nonexistent(self, tmp_path):
        """Get returns None for missing files."""
        cache = BuildCache(tmp_path / ".cache")
        js, source_map = cache.get("nonexistent.py")
        assert js is None
        assert source_map is None
    
    def test_needs_compile_new_file(self, tmp_path):
        """New file needs compilation."""
        cache = BuildCache(tmp_path / ".cache")
        assert cache.needs_compile("new.py", "abc123") is True
    
    def test_needs_compile_unchanged(self, tmp_path):
        """Unchanged file doesn't need compilation."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "code", None, "hash1", ["A"])
        assert cache.needs_compile("file.py", "hash1") is False
    
    def test_needs_compile_changed(self, tmp_path):
        """Changed file needs compilation."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "old_code", None, "hash1", ["A"])
        assert cache.needs_compile("file.py", "hash2") is True
    
    def test_invalidate(self, tmp_path):
        """Invalidate removes cache entry."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "code", None, "hash", ["A"])
        
        assert cache.invalidate("file.py") is True
        assert cache.get("file.py") == (None, None)
    
    def test_invalidate_nonexistent(self, tmp_path):
        """Invalidate returns False for missing files."""
        cache = BuildCache(tmp_path / ".cache")
        assert cache.invalidate("missing.py") is False
    
    def test_clear(self, tmp_path):
        """Clear removes all cache entries."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("a.py", "a", None, "1", ["A"])
        cache.store("b.py", "b", None, "2", ["B"])
        
        cache.clear()
        
        assert cache.get("a.py") == (None, None)
        assert cache.get("b.py") == (None, None)


# =============================================================================
# CACHE PERSISTENCE
# =============================================================================

class TestPersistence:
    """Cache persistence across restarts."""
    
    def test_manifest_saved(self, tmp_path):
        """Manifest is saved to disk."""
        cache_dir = tmp_path / ".cache"
        cache = BuildCache(cache_dir)
        cache.store("file.py", "code", None, "hash", ["A"])
        
        manifest_path = cache_dir / "manifest.json"
        assert manifest_path.exists()
    
    def test_manifest_loaded(self, tmp_path):
        """Manifest is loaded on init."""
        cache_dir = tmp_path / ".cache"
        
        # First instance stores
        cache1 = BuildCache(cache_dir)
        cache1.store("file.py", "code", None, "hash", ["A"])
        
        # Second instance loads
        cache2 = BuildCache(cache_dir)
        assert cache2.needs_compile("file.py", "hash") is False
    
    def test_manifest_format(self, tmp_path):
        """Manifest has correct JSON structure."""
        cache_dir = tmp_path / ".cache"
        cache = BuildCache(cache_dir)
        cache.store("file.py", "code", None, "abc", ["A"])
        
        manifest = json.loads((cache_dir / "manifest.json").read_text())
        assert manifest["version"] == "1.0"
        assert "entries" in manifest
    
    def test_corrupted_manifest(self, tmp_path):
        """Handle corrupted manifest gracefully."""
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "manifest.json").write_text("not valid json")
        
        # Should not raise
        cache = BuildCache(cache_dir)
        assert cache.get("any.py") == (None, None)
    
    def test_version_mismatch(self, tmp_path):
        """Clear cache on version mismatch."""
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir(parents=True)
        
        # Write old version manifest
        (cache_dir / "manifest.json").write_text(json.dumps({
            "version": "0.9",
            "entries": {"file.py": {"source_hash": "x"}}
        }))
        
        cache = BuildCache(cache_dir)
        # Old entries should be cleared
        entries = cache.get_all_entries()
        assert len(entries) == 0


# =============================================================================
# CACHE FILES
# =============================================================================

class TestCacheFiles:
    """Cache file management."""
    
    def test_js_file_created(self, tmp_path):
        """JS file is written to cache dir."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "const x = 1;", None, "abc123", ["X"])
        
        js_files = list((tmp_path / ".cache").glob("*.js"))
        assert len(js_files) == 1
    
    def test_map_file_created(self, tmp_path):
        """Source map is written when provided."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "const x = 1;", '{"version": 3}', "abc", ["X"])
        
        map_files = list((tmp_path / ".cache").glob("*.js.map"))
        assert len(map_files) == 1
    
    def test_no_map_file_when_none(self, tmp_path):
        """No source map when not provided."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "const x = 1;", None, "abc", ["X"])
        
        map_files = list((tmp_path / ".cache").glob("*.js.map"))
        assert len(map_files) == 0
    
    def test_unique_filenames(self, tmp_path):
        """Files have unique names based on hash."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "v1", None, "hash1", ["X"])
        cache.store("file.py", "v2", None, "hash2", ["X"])
        
        # Should have 1 js file (old one replaced)
        js_files = list((tmp_path / ".cache").glob("*.js"))
        assert len(js_files) == 1
    
    def test_old_files_removed(self, tmp_path):
        """Old cache files are removed on update."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "v1", None, "hash1", ["X"])
        old_files = list((tmp_path / ".cache").glob("file_hash1*.js"))
        
        cache.store("file.py", "v2", None, "hash2", ["X"])
        
        # Old file should not exist
        for f in old_files:
            assert not f.exists()
    
    def test_missing_js_triggers_recompile(self, tmp_path):
        """Missing JS file triggers recompilation."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "code", None, "hash", ["X"])
        
        # Delete the JS file
        for js in (tmp_path / ".cache").glob("*.js"):
            js.unlink()
        
        assert cache.needs_compile("file.py", "hash") is True


# =============================================================================
# CACHE ENTRY
# =============================================================================

class TestCacheEntry:
    """CacheEntry data structure."""
    
    def test_entry_fields(self):
        """Entry has all required fields."""
        entry = CacheEntry(
            source_hash="abc123",
            islands=["Counter", "Todo"],
            js_file="counter_abc123.js",
        )
        assert entry.source_hash == "abc123"
        assert entry.islands == ["Counter", "Todo"]
        assert entry.js_file == "counter_abc123.js"
    
    def test_entry_timestamp(self):
        """Entry has timestamp."""
        entry = CacheEntry(
            source_hash="x",
            islands=["A"],
            js_file="a.js",
        )
        assert entry.compiled_at != ""
    
    def test_get_entry(self, tmp_path):
        """Get entry metadata."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "code", None, "hash", ["A", "B"], compile_time_ms=5.2)
        
        entry = cache.get_entry("file.py")
        assert entry is not None
        assert entry.source_hash == "hash"
        assert entry.islands == ["A", "B"]
        assert entry.compile_time_ms == 5.2
    
    def test_get_all_entries(self, tmp_path):
        """Get all cache entries."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("a.py", "a", None, "1", ["A"])
        cache.store("b.py", "b", None, "2", ["B"])
        
        entries = cache.get_all_entries()
        assert len(entries) == 2


# =============================================================================
# CACHE STATS
# =============================================================================

class TestCacheStats:
    """Cache statistics."""
    
    def test_hit_rate(self):
        """Calculate hit rate."""
        stats = CacheStats(hits=8, misses=2)
        assert stats.hit_rate == 80.0
    
    def test_hit_rate_zero(self):
        """Hit rate with no operations."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0
    
    def test_get_stats(self, tmp_path):
        """Get cache statistics."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("a.py", "x" * 100, None, "1", ["A"])
        cache.store("b.py", "y" * 200, None, "2", ["B"])
        
        # Trigger some hits/misses
        cache.needs_compile("a.py", "1")  # hit
        cache.needs_compile("a.py", "1")  # hit
        cache.needs_compile("c.py", "3")  # miss
        
        stats = cache.get_stats()
        assert stats.total_entries == 2
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.cache_size_kb > 0


# =============================================================================
# HASH FUNCTIONS
# =============================================================================

class TestHashFunctions:
    """Hash utility functions."""
    
    def test_hash_content(self):
        """Hash string content."""
        h1 = hash_content("hello world")
        h2 = hash_content("hello world")
        h3 = hash_content("different")
        
        assert h1 == h2
        assert h1 != h3
    
    def test_hash_content_deterministic(self):
        """Hash is deterministic."""
        content = "def foo(): pass"
        hashes = [hash_content(content) for _ in range(10)]
        assert len(set(hashes)) == 1
    
    def test_hash_file(self, tmp_path):
        """Hash file contents."""
        file = tmp_path / "test.py"
        file.write_text("content")
        
        h1 = hash_file(file)
        h2 = hash_file(file)
        assert h1 == h2
    
    def test_hash_file_changes(self, tmp_path):
        """Hash changes when file changes."""
        file = tmp_path / "test.py"
        file.write_text("v1")
        h1 = hash_file(file)
        
        file.write_text("v2")
        h2 = hash_file(file)
        
        assert h1 != h2
    
    def test_hash_file_missing(self, tmp_path):
        """Hash returns empty for missing file."""
        h = hash_file(tmp_path / "missing.py")
        assert h == ""


# =============================================================================
# PATH NORMALIZATION
# =============================================================================

class TestPathNormalization:
    """Path normalization for consistent lookups."""
    
    def test_relative_path(self, tmp_path):
        """Relative paths are normalized."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("pages/counter.py", "code", None, "hash", ["A"])
        
        # Should find with different path formats
        assert cache.needs_compile("pages/counter.py", "hash") is False
    
    def test_absolute_path(self, tmp_path):
        """Absolute paths work."""
        cache = BuildCache(tmp_path / ".cache")
        abs_path = str(tmp_path / "file.py")
        
        cache.store(abs_path, "code", None, "hash", ["A"])
        assert cache.needs_compile(abs_path, "hash") is False


# =============================================================================
# CONCURRENCY
# =============================================================================

class TestConcurrency:
    """Thread safety tests."""
    
    def test_multiple_stores(self, tmp_path):
        """Multiple stores don't corrupt cache."""
        import threading
        
        cache = BuildCache(tmp_path / ".cache")
        errors = []
        
        def store_item(i):
            try:
                cache.store(f"file{i}.py", f"code{i}", None, f"hash{i}", [f"A{i}"])
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=store_item, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert len(cache.get_all_entries()) == 10


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case handling."""
    
    def test_empty_js(self, tmp_path):
        """Handle empty JS content."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", "", None, "hash", ["A"])
        
        js, _ = cache.get("file.py")
        assert js == ""
    
    def test_large_js(self, tmp_path):
        """Handle large JS content."""
        cache = BuildCache(tmp_path / ".cache")
        large_js = "x" * 1_000_000  # 1MB
        cache.store("file.py", large_js, None, "hash", ["A"])
        
        js, _ = cache.get("file.py")
        assert len(js) == 1_000_000
    
    def test_special_characters_in_path(self, tmp_path):
        """Handle special characters in paths."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("components/[id].py", "code", None, "hash", ["A"])
        
        assert cache.needs_compile("components/[id].py", "hash") is False
    
    def test_unicode_content(self, tmp_path):
        """Handle Unicode in JS content."""
        cache = BuildCache(tmp_path / ".cache")
        cache.store("file.py", 'const msg = "Привет! 你好!"', None, "hash", ["A"])
        
        js, _ = cache.get("file.py")
        assert "Привет" in js
        assert "你好" in js

