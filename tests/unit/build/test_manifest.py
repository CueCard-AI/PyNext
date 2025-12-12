"""
Tests for PyNext Build Manifest (20 tests)

Tests manifest generation and JSON structure.
"""

import pytest
import json
from pathlib import Path

from pynext.build.manifest import (
    BuildManifest,
    IslandEntry,
    RuntimeEntry,
    BuildStats,
)


# =============================================================================
# MANIFEST CREATION
# =============================================================================

class TestManifestCreation:
    """Tests for creating build manifests."""
    
    def test_create_empty_manifest(self):
        """Create empty manifest."""
        manifest = BuildManifest()
        assert manifest.build_id != ""
        assert manifest.build_time != ""
        assert len(manifest.islands) == 0
    
    def test_create_with_build_id(self):
        """Create manifest with custom build ID."""
        manifest = BuildManifest(build_id="custom123")
        assert manifest.build_id == "custom123"
    
    def test_add_island(self):
        """Add island to manifest."""
        manifest = BuildManifest()
        manifest.add_island(
            name="Counter",
            file="counter.js",
            source_file="counter.py",
            size=342,
            features=["signals", "effects"],
        )
        assert len(manifest.islands) == 1
        assert manifest.islands["Counter"].name == "Counter"
    
    def test_add_multiple_islands(self):
        """Add multiple islands."""
        manifest = BuildManifest()
        manifest.add_island("A", "a.js", "a.py", 100)
        manifest.add_island("B", "b.js", "b.py", 200)
        manifest.add_island("C", "c.js", "c.py", 300)
        assert len(manifest.islands) == 3


# =============================================================================
# RUNTIME
# =============================================================================

class TestRuntime:
    """Tests for runtime entry."""
    
    def test_add_runtime(self):
        """Add runtime to manifest."""
        manifest = BuildManifest()
        manifest.add_runtime("reactive.min.js", 2300, ["signals", "effects"])
        
        assert manifest.runtime is not None
        assert manifest.runtime.file == "reactive.min.js"
        assert manifest.runtime.size == 2300
    
    def test_runtime_modules(self):
        """Runtime has module list."""
        manifest = BuildManifest()
        manifest.add_runtime("runtime.js", 1000, ["signals", "stores", "show"])
        assert manifest.runtime.modules == ["signals", "stores", "show"]


# =============================================================================
# STATS
# =============================================================================

class TestStats:
    """Tests for build statistics."""
    
    def test_stats_total_islands(self):
        """Stats tracks total islands."""
        manifest = BuildManifest()
        manifest.add_island("A", "a.js", "a.py", 100)
        manifest.add_island("B", "b.js", "b.py", 200)
        assert manifest.stats.total_islands == 2
    
    def test_stats_total_size(self):
        """Stats tracks total size."""
        manifest = BuildManifest()
        manifest.add_island("A", "a.js", "a.py", 100)
        manifest.add_island("B", "b.js", "b.py", 200)
        manifest.add_runtime("runtime.js", 500)
        assert manifest.stats.total_size == 800
    
    def test_stats_islands_size(self):
        """Stats tracks islands-only size."""
        manifest = BuildManifest()
        manifest.add_island("A", "a.js", "a.py", 100)
        manifest.add_runtime("runtime.js", 500)
        assert manifest.stats.islands_size == 100


# =============================================================================
# FEATURES
# =============================================================================

class TestFeatures:
    """Tests for feature tracking."""
    
    def test_track_features(self):
        """Track features used across islands."""
        manifest = BuildManifest()
        manifest.add_island("A", "a.js", "a.py", features=["signals"])
        manifest.add_island("B", "b.js", "b.py", features=["signals", "effects"])
        manifest.add_island("C", "c.js", "c.py", features=["stores"])
        
        features = manifest.get_features_used()
        assert "signals" in features
        assert "effects" in features
        assert "stores" in features


# =============================================================================
# SERIALIZATION
# =============================================================================

class TestSerialization:
    """Tests for manifest serialization."""
    
    def test_to_dict(self):
        """Convert manifest to dictionary."""
        manifest = BuildManifest(build_id="test123")
        manifest.add_island("Counter", "counter.js", "counter.py", 100)
        
        data = manifest.to_dict()
        assert data["version"] == "1.0"
        assert data["buildId"] == "test123"
        assert "Counter" in data["islands"]
    
    def test_save_to_file(self, tmp_path):
        """Save manifest to JSON file."""
        manifest = BuildManifest()
        manifest.add_island("A", "a.js", "a.py", 100)
        
        path = tmp_path / "manifest.json"
        manifest.save(path)
        
        assert path.exists()
        data = json.loads(path.read_text())
        assert "A" in data["islands"]
    
    def test_load_from_file(self, tmp_path):
        """Load manifest from JSON file."""
        # Create and save
        original = BuildManifest(build_id="abc")
        original.add_island("Counter", "counter.js", "counter.py", 100, ["signals"])
        original.add_runtime("runtime.js", 500)
        
        path = tmp_path / "manifest.json"
        original.save(path)
        
        # Load
        loaded = BuildManifest.load(path)
        assert loaded.build_id == "abc"
        assert "Counter" in loaded.islands
        assert loaded.runtime is not None


# =============================================================================
# QUERIES
# =============================================================================

class TestQueries:
    """Tests for manifest queries."""
    
    def test_get_island(self):
        """Get island by name."""
        manifest = BuildManifest()
        manifest.add_island("Counter", "counter.js", "counter.py", 100)
        
        island = manifest.get_island("Counter")
        assert island is not None
        assert island.name == "Counter"
    
    def test_get_island_missing(self):
        """Get missing island returns None."""
        manifest = BuildManifest()
        assert manifest.get_island("Missing") is None
    
    def test_get_islands_by_file(self):
        """Group islands by source file."""
        manifest = BuildManifest()
        manifest.add_island("A", "a.js", "components.py")
        manifest.add_island("B", "b.js", "components.py")
        manifest.add_island("C", "c.js", "page.py")
        
        by_file = manifest.get_islands_by_file()
        assert len(by_file["components.py"]) == 2
        assert len(by_file["page.py"]) == 1


# =============================================================================
# DATA CLASSES
# =============================================================================

class TestDataClasses:
    """Tests for data class structures."""
    
    def test_island_entry(self):
        """IslandEntry fields."""
        entry = IslandEntry(
            name="Counter",
            file="counter.js",
            source_file="counter.py",
            size=342,
            features=["signals"],
        )
        assert entry.name == "Counter"
        assert entry.size == 342
    
    def test_runtime_entry(self):
        """RuntimeEntry fields."""
        entry = RuntimeEntry(
            file="runtime.js",
            size=2300,
            modules=["signals", "effects"],
        )
        assert entry.file == "runtime.js"
        assert entry.size == 2300
    
    def test_build_stats(self):
        """BuildStats fields."""
        stats = BuildStats(
            total_islands=5,
            total_size=4200,
            runtime_size=2000,
            compile_time_ms=234,
        )
        assert stats.total_islands == 5
        assert stats.islands_size == 2200

