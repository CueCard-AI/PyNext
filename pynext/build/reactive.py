"""
PyNext Build - Reactive Compilation

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Main entry point for compiling @island components to JavaScript. Orchestrates
the entire build pipeline: scan → cache check → compile → bundle → output.

    from pynext.build import compile_project, BuildConfig
    
    # Simple usage
    result = compile_project("./my-app")
    
    # With configuration
    result = compile_project("./my-app", BuildConfig(
        tree_shake=True,
        parallel=True,
        minify=True,
    ))
    
    print(f"Compiled {result.island_count} islands in {result.duration_ms}ms")

=============================================================================
WHY THIS EXISTS
=============================================================================

This is the "one command does everything" module. It:

1. Scans directories for @island components
2. Checks cache to skip unchanged files
3. Compiles Python → JavaScript (using pynext.compiler)
4. Bundles with runtime
5. Generates build manifest
6. Reports performance metrics

=============================================================================
PERFORMANCE TARGETS
=============================================================================

| Scenario | Target |
|----------|--------|
| 10 islands (cold) | < 100ms |
| 100 islands (cold) | < 500ms |
| 1 file changed | < 50ms |
| No changes | < 10ms |

=============================================================================
"""

from __future__ import annotations

import os
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Callable

from .scanner import scan_directory, scan_file, IslandInfo, ScanResult
from .cache import BuildCache, hash_file
from .manifest import BuildManifest, IslandEntry


__all__ = [
    "compile_project",
    "compile_files",
    "BuildConfig",
    "BuildResult",
]


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class BuildConfig:
    """
    Build configuration options.
    
    Attributes:
        source_dirs: Directories to scan for islands (default: ["pages/", "components/"])
        output_dir: Where to write compiled files (default: ".pynext/build")
        cache_dir: Where to store build cache (default: ".pynext/cache")
        tree_shake: Enable dead code elimination (default: True)
        minify: Minify JavaScript output (default: True in production)
        sourcemap: Generate source maps (default: True)
        parallel: Use parallel compilation (default: True)
        max_workers: Max parallel workers (default: CPU count)
        use_cache: Enable incremental compilation (default: True)
        clean: Clean output before building (default: False)
        verbose: Print detailed progress (default: False)
    
    Example:
        config = BuildConfig(
            tree_shake=True,
            parallel=True,
            verbose=True,
        )
        result = compile_project("./my-app", config)
    """
    source_dirs: List[str] = field(default_factory=lambda: ["pages/", "components/"])
    output_dir: str = ".pynext/build"
    cache_dir: str = ".pynext/cache"
    tree_shake: bool = True
    minify: bool = True
    sourcemap: bool = True
    parallel: bool = True
    max_workers: Optional[int] = None
    use_cache: bool = True
    clean: bool = False
    verbose: bool = False
    
    def __post_init__(self):
        if self.max_workers is None:
            self.max_workers = os.cpu_count() or 4


# =============================================================================
# BUILD RESULT
# =============================================================================

@dataclass
class BuildResult:
    """
    Result of a build operation.
    
    Attributes:
        success: True if build completed without errors
        islands: List of compiled islands
        errors: List of (file, error) tuples
        warnings: List of (file, warning) tuples
        manifest: Build manifest
        duration_ms: Total build time in milliseconds
        files_scanned: Number of source files scanned
        cache_hits: Number of files served from cache
        cache_misses: Number of files that needed compilation
        output_size_kb: Total output size in KB
    """
    success: bool = True
    islands: List[IslandInfo] = field(default_factory=list)
    errors: List[tuple] = field(default_factory=list)
    warnings: List[tuple] = field(default_factory=list)
    manifest: Optional[BuildManifest] = None
    duration_ms: float = 0.0
    files_scanned: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    output_size_kb: float = 0.0
    
    @property
    def island_count(self) -> int:
        """Number of islands compiled."""
        return len(self.islands)
    
    @property
    def error_count(self) -> int:
        """Number of errors."""
        return len(self.errors)
    
    def __bool__(self) -> bool:
        return self.success


# =============================================================================
# MAIN API
# =============================================================================

def compile_project(
    project_dir: str | Path,
    config: Optional[BuildConfig] = None,
    on_progress: Optional[Callable[[str, int, int], None]] = None,
) -> BuildResult:
    """
    Compile all @island components in a project.
    
    This is the main entry point for production builds. It scans the project
    for @island decorated functions, compiles them to JavaScript, and outputs
    a build manifest.
    
    Args:
        project_dir: Path to the project root
        config: Build configuration options
        on_progress: Optional callback for progress updates (file, current, total)
    
    Returns:
        BuildResult with compiled islands, stats, and any errors
    
    Example:
        # Simple usage
        result = compile_project("./my-app")
        if result.success:
            print(f"Built {result.island_count} islands")
        
        # With configuration
        result = compile_project("./my-app", BuildConfig(
            tree_shake=True,
            parallel=True,
        ))
        
        # With progress callback
        def on_progress(file, current, total):
            print(f"[{current}/{total}] {file}")
        
        result = compile_project("./my-app", on_progress=on_progress)
    """
    start_time = time.perf_counter()
    
    project_path = Path(project_dir).resolve()
    config = config or BuildConfig()
    
    result = BuildResult()
    
    # Validate project directory
    if not project_path.exists():
        result.success = False
        result.errors.append((str(project_path), "Project directory not found"))
        return result
    
    # Initialize paths
    output_path = project_path / config.output_dir
    cache_path = project_path / config.cache_dir
    
    # Clean output if requested
    if config.clean and output_path.exists():
        shutil.rmtree(output_path)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize cache
    cache = BuildCache(cache_path) if config.use_cache else None
    
    # Initialize manifest
    manifest = BuildManifest()
    
    # Step 1: Scan for islands
    if config.verbose:
        print("[PyNext] Scanning for islands...")
    
    all_islands: List[IslandInfo] = []
    
    for source_dir in config.source_dirs:
        dir_path = project_path / source_dir
        if dir_path.exists():
            scan_result = scan_directory(dir_path)
            all_islands.extend(scan_result.islands)
            result.files_scanned += scan_result.files_scanned
            result.errors.extend(scan_result.errors)
    
    if config.verbose:
        print(f"[PyNext] Found {len(all_islands)} islands in {result.files_scanned} files")
    
    if not all_islands:
        result.duration_ms = (time.perf_counter() - start_time) * 1000
        result.manifest = manifest
        return result
    
    # Step 2: Check cache and compile
    to_compile: List[IslandInfo] = []
    
    for island in all_islands:
        source_hash = hash_file(island.file_path)
        
        if cache and not cache.needs_compile(island.file_path, source_hash):
            result.cache_hits += 1
            # Get cached result
            js, source_map = cache.get(island.file_path)
            if js:
                # Write to output
                output_file = output_path / f"{island.name}.js"
                output_file.write_text(js, encoding="utf-8")
                result.output_size_kb += len(js) / 1024
                
                if source_map:
                    map_file = output_path / f"{island.name}.js.map"
                    map_file.write_text(source_map, encoding="utf-8")
                
                # Add to manifest
                manifest.add_island(
                    name=island.name,
                    file=f"{island.name}.js",
                    source_file=island.file_path,
                    size=len(js),
                    features=_get_features(island),
                )
                result.islands.append(island)
        else:
            to_compile.append(island)
            result.cache_misses += 1
    
    if config.verbose:
        print(f"[PyNext] Cache: {result.cache_hits} hits, {result.cache_misses} misses")
    
    # Step 3: Compile islands that need it
    if to_compile:
        if config.verbose:
            print(f"[PyNext] Compiling {len(to_compile)} islands...")
        
        compiled = _compile_islands(
            to_compile,
            output_path,
            config,
            cache,
            on_progress,
        )
        
        for island, js, source_map, error in compiled:
            if error:
                result.errors.append((island.file_path, error))
            else:
                result.islands.append(island)
                result.output_size_kb += len(js) / 1024
                
                # Add to manifest
                manifest.add_island(
                    name=island.name,
                    file=f"{island.name}.js",
                    source_file=island.file_path,
                    size=len(js),
                    features=_get_features(island),
                )
    
    # Step 4: Copy runtime
    runtime_size = _copy_runtime(output_path, config)
    manifest.add_runtime("reactive.min.js", runtime_size, ["signals", "effects", "memo", "store"])
    result.output_size_kb += runtime_size / 1024
    
    # Step 5: Tree shake (if enabled)
    if config.tree_shake:
        # TODO: Implement tree shaking in Phase 17.7.4
        pass
    
    # Step 6: Save manifest
    manifest.stats.compile_time_ms = (time.perf_counter() - start_time) * 1000
    manifest.stats.files_scanned = result.files_scanned
    manifest.stats.cache_hits = result.cache_hits
    manifest.stats.cache_misses = result.cache_misses
    manifest.save(output_path / "manifest.json")
    
    result.manifest = manifest
    result.success = len(result.errors) == 0
    result.duration_ms = (time.perf_counter() - start_time) * 1000
    
    if config.verbose:
        print(f"[PyNext] Build complete: {result.island_count} islands in {result.duration_ms:.1f}ms")
    
    return result


def compile_files(
    files: List[str | Path],
    output_dir: str | Path,
    config: Optional[BuildConfig] = None,
) -> BuildResult:
    """
    Compile specific files.
    
    Useful for incremental builds or testing.
    
    Args:
        files: List of Python files to compile
        output_dir: Where to write compiled files
        config: Build configuration options
    
    Returns:
        BuildResult with compiled islands
    
    Example:
        result = compile_files(
            ["components/counter.py", "components/todo.py"],
            ".pynext/build"
        )
    """
    start_time = time.perf_counter()
    
    config = config or BuildConfig()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    result = BuildResult()
    islands: List[IslandInfo] = []
    
    # Scan specified files
    for file in files:
        file_path = Path(file)
        if file_path.exists():
            scan_result = scan_file(file_path)
            islands.extend(scan_result.islands)
            result.files_scanned += 1
            result.errors.extend(scan_result.errors)
    
    if not islands:
        result.duration_ms = (time.perf_counter() - start_time) * 1000
        return result
    
    # Compile all
    compiled = _compile_islands(islands, output_path, config, None, None)
    
    for island, js, source_map, error in compiled:
        if error:
            result.errors.append((island.file_path, error))
        else:
            result.islands.append(island)
            result.output_size_kb += len(js) / 1024
    
    result.success = len(result.errors) == 0
    result.duration_ms = (time.perf_counter() - start_time) * 1000
    
    return result


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _compile_islands(
    islands: List[IslandInfo],
    output_path: Path,
    config: BuildConfig,
    cache: Optional[BuildCache],
    on_progress: Optional[Callable[[str, int, int], None]],
) -> List[tuple]:
    """
    Compile a list of islands.
    
    Returns list of (island, js, source_map, error) tuples.
    """
    from pynext.compiler import compile_file
    
    results = []
    total = len(islands)
    
    # Group by file (multiple islands can be in one file)
    files_to_compile: Dict[str, List[IslandInfo]] = {}
    for island in islands:
        if island.file_path not in files_to_compile:
            files_to_compile[island.file_path] = []
        files_to_compile[island.file_path].append(island)
    
    # Compile each file
    for idx, (file_path, file_islands) in enumerate(files_to_compile.items()):
        if on_progress:
            on_progress(file_path, idx + 1, len(files_to_compile))
        
        try:
            compile_result = compile_file(file_path)
            
            if compile_result.errors:
                for island in file_islands:
                    error_msg = "; ".join(str(e) for e in compile_result.errors)
                    results.append((island, "", "", error_msg))
            else:
                # Write output
                for island in file_islands:
                    output_file = output_path / f"{island.name}.js"
                    output_file.write_text(compile_result.js, encoding="utf-8")
                    
                    source_map = compile_result.map
                    if config.sourcemap and source_map:
                        map_file = output_path / f"{island.name}.js.map"
                        map_file.write_text(source_map, encoding="utf-8")
                    
                    # Update cache
                    if cache:
                        cache.store(
                            island.file_path,
                            compile_result.js,
                            source_map,
                            island.source_hash,
                            [island.name],
                        )
                    
                    results.append((island, compile_result.js, source_map, None))
                    
        except Exception as e:
            for island in file_islands:
                results.append((island, "", "", str(e)))
    
    return results


def _copy_runtime(output_path: Path, config: BuildConfig) -> int:
    """
    Copy the reactive runtime to the output directory.
    
    Returns the size in bytes.
    """
    from pathlib import Path as P
    
    # Find runtime file
    runtime_dir = P(__file__).parent.parent / "runtime"
    
    if config.minify:
        runtime_file = runtime_dir / "reactive.min.js"
    else:
        runtime_file = runtime_dir / "reactive.js"
    
    if not runtime_file.exists():
        # Fall back to non-minified
        runtime_file = runtime_dir / "reactive.js"
    
    if not runtime_file.exists():
        return 0
    
    # Copy to output
    output_file = output_path / "reactive.min.js"
    content = runtime_file.read_text(encoding="utf-8")
    output_file.write_text(content, encoding="utf-8")
    
    return len(content)


def _get_features(island: IslandInfo) -> List[str]:
    """Extract feature list from island info."""
    features = []
    if island.has_signals:
        features.append("signals")
    if island.has_stores:
        features.append("stores")
    if island.has_effects:
        features.append("effects")
    if island.has_memos:
        features.append("memos")
    if island.has_forms:
        features.append("forms")
    return features

