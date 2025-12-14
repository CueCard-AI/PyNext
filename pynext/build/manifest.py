"""
PyNext Build - Build Manifest

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Generates and manages the build manifest - a JSON file that describes
all compiled islands, their dependencies, and build metadata.

    from pynext.build.manifest import BuildManifest
    
    manifest = BuildManifest()
    manifest.add_island("Counter", "counter.js", {"signals": True})
    manifest.add_runtime("reactive.min.js", 2300)
    manifest.save(".pynext/build/manifest.json")

=============================================================================
WHY THIS EXISTS
=============================================================================

The build manifest is used by:

1. **Server** - Knows which JS files to include in HTML
2. **Dev server** - Tracks what needs to be recompiled
3. **Bundle analyzer** - Understands composition
4. **CI/CD** - Verifies build completeness

=============================================================================
MANIFEST STRUCTURE
=============================================================================

{
    "version": "1.0",
    "buildId": "abc123",
    "buildTime": "2024-01-01T00:00:00Z",
    "islands": {
        "Counter": {
            "file": "counter.js",
            "sourceFile": "components/counter.py",
            "size": 342,
            "features": ["signals", "effects"]
        }
    },
    "runtime": {
        "file": "reactive.min.js",
        "size": 2300
    },
    "stats": {
        "totalIslands": 5,
        "totalSize": 4200,
        "compileTime": 234
    }
}

=============================================================================
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set


__all__ = [
    "BuildManifest",
    "IslandEntry",
    "RuntimeEntry",
    "BuildStats",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class IslandEntry:
    """
    Manifest entry for a compiled island.
    
    Attributes:
        name: Island function name
        file: Output JS filename
        source_file: Original Python source file
        size: Size of compiled JS in bytes
        features: List of reactive features used
        dependencies: Other islands this depends on
    """
    name: str
    file: str
    source_file: str
    size: int = 0
    features: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class RuntimeEntry:
    """
    Manifest entry for the runtime bundle.
    
    Attributes:
        file: Runtime JS filename
        size: Size in bytes
        modules: List of included modules
    """
    file: str
    size: int = 0
    modules: List[str] = field(default_factory=list)


@dataclass
class BuildStats:
    """
    Build statistics.
    
    Attributes:
        total_islands: Number of islands compiled
        total_size: Total output size in bytes
        runtime_size: Size of runtime in bytes
        compile_time_ms: Total compilation time
        files_scanned: Number of source files scanned
        cache_hits: Number of cache hits
        cache_misses: Number of cache misses
    """
    total_islands: int = 0
    total_size: int = 0
    runtime_size: int = 0
    compile_time_ms: float = 0.0
    files_scanned: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def islands_size(self) -> int:
        """Size of islands only (excluding runtime)."""
        return self.total_size - self.runtime_size


# =============================================================================
# BUILD MANIFEST
# =============================================================================

class BuildManifest:
    """
    Build manifest for tracking compiled islands and build metadata.
    
    The manifest is saved as JSON and used by the server to know
    which JavaScript files to include in HTML responses.
    
    Example:
        manifest = BuildManifest()
        
        # Add compiled islands
        manifest.add_island(
            name="Counter",
            file="counter.js",
            source_file="components/counter.py",
            size=342,
            features=["signals", "effects"]
        )
        
        # Add runtime
        manifest.add_runtime("reactive.min.js", 2300, ["signals", "effects", "show"])
        
        # Save
        manifest.save(".pynext/build/manifest.json")
    """
    
    VERSION = "1.0"
    
    def __init__(self, build_id: Optional[str] = None):
        """
        Initialize a new build manifest.
        
        Args:
            build_id: Unique build identifier (auto-generated if not provided)
        """
        self.build_id = build_id or uuid.uuid4().hex[:12]
        self.build_time = datetime.utcnow().isoformat() + "Z"
        self.islands: Dict[str, IslandEntry] = {}
        self.runtime: Optional[RuntimeEntry] = None
        self.stats = BuildStats()
        self._features_used: Set[str] = set()
    
    def add_island(
        self,
        name: str,
        file: str,
        source_file: str,
        size: int = 0,
        features: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> None:
        """
        Add a compiled island to the manifest.
        
        Args:
            name: Island function name
            file: Output JS filename
            source_file: Original Python source file
            size: Size of compiled JS in bytes
            features: List of reactive features used
            dependencies: Other islands this depends on
        
        Example:
            manifest.add_island(
                name="Counter",
                file="counter.js",
                source_file="components/counter.py",
                size=342,
                features=["signals", "effects"]
            )
        """
        features = features or []
        dependencies = dependencies or []
        
        entry = IslandEntry(
            name=name,
            file=file,
            source_file=source_file,
            size=size,
            features=features,
            dependencies=dependencies,
        )
        
        self.islands[name] = entry
        self._features_used.update(features)
        
        # Update stats
        self.stats.total_islands = len(self.islands)
        self.stats.total_size = sum(i.size for i in self.islands.values())
        if self.runtime:
            self.stats.total_size += self.runtime.size
    
    def add_runtime(
        self,
        file: str,
        size: int,
        modules: Optional[List[str]] = None,
    ) -> None:
        """
        Set the runtime bundle information.
        
        Args:
            file: Runtime JS filename
            size: Size in bytes
            modules: List of included modules
        
        Example:
            manifest.add_runtime(
                "reactive.min.js",
                2300,
                ["signals", "effects", "show", "for"]
            )
        """
        modules = modules or []
        
        self.runtime = RuntimeEntry(
            file=file,
            size=size,
            modules=modules,
        )
        
        self.stats.runtime_size = size
        self.stats.total_size = sum(i.size for i in self.islands.values()) + size
    
    def get_island(self, name: str) -> Optional[IslandEntry]:
        """
        Get an island entry by name.
        
        Args:
            name: Island function name
        
        Returns:
            IslandEntry or None if not found
        """
        return self.islands.get(name)
    
    def get_islands_by_file(self) -> Dict[str, List[IslandEntry]]:
        """
        Group islands by their source file.
        
        Returns:
            Dict mapping source file paths to island entries
        """
        result: Dict[str, List[IslandEntry]] = {}
        for island in self.islands.values():
            if island.source_file not in result:
                result[island.source_file] = []
            result[island.source_file].append(island)
        return result
    
    def get_features_used(self) -> Set[str]:
        """
        Get all reactive features used across all islands.
        
        Returns:
            Set of feature names
        """
        return self._features_used.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert manifest to dictionary for JSON serialization.
        
        Returns:
            Dict representation of the manifest
        """
        return {
            "version": self.VERSION,
            "buildId": self.build_id,
            "buildTime": self.build_time,
            "islands": {
                name: asdict(entry) for name, entry in self.islands.items()
            },
            "runtime": asdict(self.runtime) if self.runtime else None,
            "stats": asdict(self.stats),
            "features": list(self._features_used),
        }
    
    def save(self, path: str | Path) -> None:
        """
        Save manifest to a JSON file.
        
        Args:
            path: Path to save the manifest
        
        Example:
            manifest.save(".pynext/build/manifest.json")
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.to_dict()
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    @classmethod
    def load(cls, path: str | Path) -> "BuildManifest":
        """
        Load manifest from a JSON file.
        
        Args:
            path: Path to the manifest file
        
        Returns:
            BuildManifest instance
        
        Example:
            manifest = BuildManifest.load(".pynext/build/manifest.json")
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")
        
        data = json.loads(path.read_text(encoding="utf-8"))
        
        manifest = cls(build_id=data.get("buildId"))
        manifest.build_time = data.get("buildTime", manifest.build_time)
        
        # Load islands
        for name, entry_data in data.get("islands", {}).items():
            manifest.islands[name] = IslandEntry(**entry_data)
        
        # Load runtime
        if data.get("runtime"):
            manifest.runtime = RuntimeEntry(**data["runtime"])
        
        # Load stats
        if data.get("stats"):
            manifest.stats = BuildStats(**data["stats"])
        
        # Load features
        manifest._features_used = set(data.get("features", []))
        
        return manifest
    
    def __repr__(self) -> str:
        return f"BuildManifest(id={self.build_id}, islands={len(self.islands)})"

