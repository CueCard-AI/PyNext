"""
Build-Time Parallel Routes Compiler for PyNext.

Handles slot compilation at build time:
- Pre-resolves slot hierarchies
- Generates slot manifests
- Analyzes hydration requirements per slot
- Configures slot-level caching

Zero runtime resolution overhead - all slot hierarchies
are pre-computed during build.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Set, Any, Tuple
import hashlib
import json
import ast
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from pynext.router.parallel import (
    CompiledSlotHierarchy,
    ParallelRoute,
    SlotConfig,
    ParallelRouteScanner,
    get_parallel_scanner,
)


@dataclass
class SlotAnalysis:
    """Analysis result for a slot."""
    name: str
    layout_path: str
    routes_count: int
    has_default: bool
    has_loading: bool
    has_error: bool
    is_interactive: bool  # Needs hydration
    estimated_size: int   # Estimated HTML size
    cache_config: Optional[Dict[str, Any]] = None


@dataclass
class SlotManifestEntry:
    """Entry in the slot manifest."""
    name: str
    layout_path: str
    routes: List[Dict[str, str]]  # path_pattern -> module_path
    default_module: Optional[str]
    loading_module: Optional[str]
    error_module: Optional[str]
    config: Dict[str, Any]
    requires_hydration: bool
    bundle_id: Optional[str]


@dataclass
class ParallelRoutesManifest:
    """Complete manifest of all parallel routes."""
    hierarchies: Dict[str, Dict[str, SlotManifestEntry]]  # layout_path -> slot_name -> entry
    slot_bundles: Dict[str, str]  # slot_id -> bundle_path
    total_slots: int
    interactive_slots: int
    static_slots: int


@dataclass
class ParallelBuildConfig:
    """Configuration for parallel routes build."""
    pages_dir: Path = Path("pages")
    output_dir: Path = Path("dist/_parallel")
    cache_dir: Path = Path(".pynext/parallel-cache")
    analyze_hydration: bool = True
    generate_bundles: bool = True
    parallel_analysis: int = 4


class ParallelRoutesCompiler:
    """
    Build-time compiler for parallel routes.
    
    Pre-computes slot hierarchies and generates manifests
    for zero-runtime-cost slot resolution.
    """
    
    def __init__(self, config: Optional[ParallelBuildConfig] = None):
        self.config = config or ParallelBuildConfig()
        self._scanner = get_parallel_scanner()
        self._analyses: Dict[str, SlotAnalysis] = {}
    
    def compile(
        self,
        project_root: Optional[Path] = None,
    ) -> ParallelRoutesManifest:
        """
        Compile all parallel routes.
        
        Returns a complete manifest of all slot hierarchies.
        """
        project_root = project_root or Path.cwd()
        pages_dir = project_root / self.config.pages_dir
        output_dir = project_root / self.config.output_dir
        cache_dir = project_root / self.config.cache_dir
        
        # Ensure directories exist
        output_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Scan for parallel routes
        hierarchies = self._scanner.scan(pages_dir)
        
        if not hierarchies:
            return ParallelRoutesManifest(
                hierarchies={},
                slot_bundles={},
                total_slots=0,
                interactive_slots=0,
                static_slots=0,
            )
        
        # Analyze and compile each hierarchy
        manifest_hierarchies: Dict[str, Dict[str, SlotManifestEntry]] = {}
        slot_bundles: Dict[str, str] = {}
        
        total_slots = 0
        interactive_slots = 0
        static_slots = 0
        
        for layout_path, hierarchy in hierarchies.items():
            manifest_hierarchies[layout_path] = {}
            
            for slot_name, routes in hierarchy.slots.items():
                # Analyze the slot
                analysis = self._analyze_slot(
                    slot_name,
                    layout_path,
                    routes,
                    hierarchy,
                    pages_dir,
                )
                
                slot_id = f"{layout_path}/@{slot_name}" if layout_path else f"@{slot_name}"
                self._analyses[slot_id] = analysis
                
                total_slots += 1
                if analysis.is_interactive:
                    interactive_slots += 1
                else:
                    static_slots += 1
                
                # Generate bundle for interactive slots
                bundle_id = None
                if analysis.is_interactive and self.config.generate_bundles:
                    bundle_id = self._generate_slot_bundle(
                        slot_name,
                        layout_path,
                        routes,
                        output_dir,
                    )
                    if bundle_id:
                        slot_bundles[slot_id] = bundle_id
                
                # Create manifest entry
                manifest_hierarchies[layout_path][slot_name] = SlotManifestEntry(
                    name=slot_name,
                    layout_path=layout_path,
                    routes=[
                        {"pattern": r.path_pattern, "module": r.module_path}
                        for r in routes
                    ],
                    default_module=self._find_module(pages_dir, layout_path, slot_name, "default"),
                    loading_module=self._find_module(pages_dir, layout_path, slot_name, "loading"),
                    error_module=self._find_module(pages_dir, layout_path, slot_name, "error"),
                    config={
                        "cache_ttl": hierarchy.slot_configs.get(slot_name, SlotConfig(name=slot_name)).cache_ttl,
                        "stream_independent": hierarchy.slot_configs.get(slot_name, SlotConfig(name=slot_name)).stream_independent,
                    },
                    requires_hydration=analysis.is_interactive,
                    bundle_id=bundle_id,
                )
        
        manifest = ParallelRoutesManifest(
            hierarchies=manifest_hierarchies,
            slot_bundles=slot_bundles,
            total_slots=total_slots,
            interactive_slots=interactive_slots,
            static_slots=static_slots,
        )
        
        # Write manifest to disk
        self._write_manifest(manifest, output_dir)
        
        return manifest
    
    def _analyze_slot(
        self,
        slot_name: str,
        layout_path: str,
        routes: List[ParallelRoute],
        hierarchy: CompiledSlotHierarchy,
        pages_dir: Path,
    ) -> SlotAnalysis:
        """Analyze a slot for hydration requirements."""
        slot_dir = pages_dir / layout_path / f"@{slot_name}" if layout_path else pages_dir / f"@{slot_name}"
        
        has_default = (slot_dir / "default.py").exists() if slot_dir.exists() else False
        has_loading = (slot_dir / "loading.py").exists() if slot_dir.exists() else False
        has_error = (slot_dir / "error.py").exists() if slot_dir.exists() else False
        
        # Check if any route is interactive
        is_interactive = False
        estimated_size = 0
        
        for route in routes:
            route_interactive, route_size = self._analyze_route_file(
                Path(route.module_path)
            )
            if route_interactive:
                is_interactive = True
            estimated_size += route_size
        
        # Get cache config
        slot_config = hierarchy.slot_configs.get(slot_name, SlotConfig(name=slot_name))
        cache_config = None
        if slot_config.cache_ttl > 0:
            cache_config = {
                "ttl": slot_config.cache_ttl,
                "scope": "slot",
            }
        
        return SlotAnalysis(
            name=slot_name,
            layout_path=layout_path,
            routes_count=len(routes),
            has_default=has_default,
            has_loading=has_loading,
            has_error=has_error,
            is_interactive=is_interactive,
            estimated_size=estimated_size,
            cache_config=cache_config,
        )
    
    def _analyze_route_file(self, file_path: Path) -> Tuple[bool, int]:
        """
        Analyze a route file for interactivity.
        
        Returns (is_interactive, estimated_size).
        """
        if not file_path.exists():
            return False, 0
        
        try:
            content = file_path.read_text()
            
            # Parse AST to detect interactivity markers
            tree = ast.parse(content)
            
            is_interactive = False
            
            for node in ast.walk(tree):
                # Check for Signal, Store, Effect usage
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['Signal', 'Store', 'Effect', 'createResource']:
                            is_interactive = True
                            break
                
                # Check for @island decorator
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == 'island':
                            is_interactive = True
                            break
                        if isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name) and decorator.func.id == 'island':
                                is_interactive = True
                                break
            
            # Estimate size based on content length
            estimated_size = len(content.encode('utf-8'))
            
            return is_interactive, estimated_size
            
        except Exception:
            return False, 0
    
    def _find_module(
        self,
        pages_dir: Path,
        layout_path: str,
        slot_name: str,
        module_name: str,
    ) -> Optional[str]:
        """Find a module file in a slot directory."""
        if layout_path:
            slot_dir = pages_dir / layout_path / f"@{slot_name}"
        else:
            slot_dir = pages_dir / f"@{slot_name}"
        
        module_file = slot_dir / f"{module_name}.py"
        
        if module_file.exists():
            return str(module_file)
        
        return None
    
    def _generate_slot_bundle(
        self,
        slot_name: str,
        layout_path: str,
        routes: List[ParallelRoute],
        output_dir: Path,
    ) -> Optional[str]:
        """
        Generate a JavaScript bundle for an interactive slot.
        
        Returns the bundle ID.
        """
        # Create bundle ID
        bundle_content = f"{layout_path}/@{slot_name}:" + "|".join(
            r.module_path for r in routes
        )
        bundle_id = hashlib.md5(bundle_content.encode()).hexdigest()[:12]
        
        # For now, return the bundle ID (actual bundling would use esbuild)
        # In production, this would generate actual JS bundle
        
        return bundle_id
    
    def _write_manifest(
        self,
        manifest: ParallelRoutesManifest,
        output_dir: Path,
    ) -> None:
        """Write manifest to disk."""
        manifest_data = {
            "hierarchies": {},
            "slotBundles": manifest.slot_bundles,
            "stats": {
                "totalSlots": manifest.total_slots,
                "interactiveSlots": manifest.interactive_slots,
                "staticSlots": manifest.static_slots,
            },
        }
        
        for layout_path, slots in manifest.hierarchies.items():
            manifest_data["hierarchies"][layout_path] = {}
            
            for slot_name, entry in slots.items():
                manifest_data["hierarchies"][layout_path][slot_name] = {
                    "name": entry.name,
                    "routes": entry.routes,
                    "default": entry.default_module,
                    "loading": entry.loading_module,
                    "error": entry.error_module,
                    "config": entry.config,
                    "requiresHydration": entry.requires_hydration,
                    "bundleId": entry.bundle_id,
                }
        
        manifest_path = output_dir / "parallel-manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
    
    def get_analysis(self, slot_id: str) -> Optional[SlotAnalysis]:
        """Get analysis for a specific slot."""
        return self._analyses.get(slot_id)
    
    def get_all_analyses(self) -> Dict[str, SlotAnalysis]:
        """Get all slot analyses."""
        return self._analyses.copy()


def compile_parallel_routes(
    project_root: Optional[Path] = None,
    config: Optional[ParallelBuildConfig] = None,
) -> ParallelRoutesManifest:
    """
    Compile all parallel routes for production build.
    
    Called by CLI build command.
    """
    compiler = ParallelRoutesCompiler(config)
    return compiler.compile(project_root=project_root)


def build_parallel_routes_map(
    pages_dir: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """
    Build parallel routes map for the application.
    
    Returns summary of compiled routes.
    """
    config = ParallelBuildConfig(
        pages_dir=pages_dir,
        output_dir=output_dir / "_parallel",
    )
    
    manifest = compile_parallel_routes(config=config)
    
    return {
        "total_slots": manifest.total_slots,
        "interactive_slots": manifest.interactive_slots,
        "static_slots": manifest.static_slots,
        "hierarchies": len(manifest.hierarchies),
        "bundles": len(manifest.slot_bundles),
    }


# =============================================================================
# Slot-Level ISR Integration
# =============================================================================

@dataclass
class SlotCacheEntry:
    """Cache entry for a slot."""
    slot_id: str
    content: str
    etag: str
    expires_at: float
    dependencies: List[str]  # Tags this slot depends on


class SlotCacheManager:
    """
    Manages slot-level caching for ISR.
    
    Enables fine-grained caching per slot rather than per page,
    allowing different slots to have different TTLs.
    """
    
    def __init__(self):
        self._cache: Dict[str, SlotCacheEntry] = {}
    
    def get(self, slot_id: str, path: str) -> Optional[SlotCacheEntry]:
        """Get cached slot content."""
        cache_key = f"{slot_id}:{path}"
        
        entry = self._cache.get(cache_key)
        if entry:
            import time
            if entry.expires_at > time.time():
                return entry
            else:
                del self._cache[cache_key]
        
        return None
    
    def set(
        self,
        slot_id: str,
        path: str,
        content: str,
        ttl: int,
        dependencies: Optional[List[str]] = None,
    ) -> SlotCacheEntry:
        """Set cached slot content."""
        import time
        
        cache_key = f"{slot_id}:{path}"
        
        # Calculate ETag
        etag = hashlib.md5(content.encode()).hexdigest()
        
        entry = SlotCacheEntry(
            slot_id=slot_id,
            content=content,
            etag=etag,
            expires_at=time.time() + ttl,
            dependencies=dependencies or [],
        )
        
        self._cache[cache_key] = entry
        return entry
    
    def invalidate(self, slot_id: str) -> int:
        """Invalidate all entries for a slot."""
        prefix = f"{slot_id}:"
        
        to_delete = [key for key in self._cache if key.startswith(prefix)]
        
        for key in to_delete:
            del self._cache[key]
        
        return len(to_delete)
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all entries with a dependency tag."""
        to_delete = [
            key for key, entry in self._cache.items()
            if tag in entry.dependencies
        ]
        
        for key in to_delete:
            del self._cache[key]
        
        return len(to_delete)
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        import time
        
        now = time.time()
        valid_entries = sum(1 for e in self._cache.values() if e.expires_at > now)
        expired_entries = len(self._cache) - valid_entries
        
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
        }


# Global slot cache instance
_slot_cache = SlotCacheManager()


def get_slot_cache() -> SlotCacheManager:
    """Get the global slot cache manager."""
    return _slot_cache


def invalidate_slot(slot_id: str) -> int:
    """Invalidate cache for a specific slot."""
    return _slot_cache.invalidate(slot_id)


def invalidate_slot_tag(tag: str) -> int:
    """Invalidate all slots with a dependency tag."""
    return _slot_cache.invalidate_by_tag(tag)

