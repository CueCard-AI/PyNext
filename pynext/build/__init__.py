"""
PyNext Build System

=============================================================================
WHAT THIS MODULE PROVIDES
=============================================================================

Complete build toolchain for PyNext reactive components:

1. **Compilation** - Python @island → JavaScript
2. **Scanning** - Find @island components in source files
3. **Caching** - Incremental builds (only recompile changed files)
4. **Bundling** - Combine runtime with compiled islands
5. **Minification** - Reduce output size
6. **Tree Shaking** - Remove unused code
7. **Analysis** - Bundle composition reports

=============================================================================
QUICK START
=============================================================================

    from pynext.build import compile_project, BuildConfig
    
    # Compile entire project
    result = compile_project("./my-app")
    print(f"Built {result.island_count} islands in {result.duration_ms}ms")
    
    # With options
    result = compile_project("./my-app", BuildConfig(
        tree_shake=True,
        parallel=True,
        minify=True,
    ))

=============================================================================
"""

from pynext.build.minify import minify_js, minify_runtime
from pynext.build.bundle import bundle_runtime, get_required_modules

# Core build system
from pynext.build.reactive import compile_project, compile_files, BuildConfig, BuildResult
from pynext.build.scanner import scan_directory, scan_file, scan_source, IslandInfo, ScanResult
from pynext.build.cache import BuildCache, CacheEntry, CacheStats, hash_file, hash_content
from pynext.build.manifest import BuildManifest, IslandEntry, RuntimeEntry, BuildStats
from pynext.build.parallel import compile_parallel, ParallelConfig, ParallelResult
from pynext.build.watcher import FileWatcher, WatcherConfig, ChangeEvent, watch_and_compile
from pynext.build.hmr import HMRServer, HMRConfig, HMRUpdate, generate_hmr_client_script
from pynext.build.treeshake import tree_shake, analyze_features, TreeShakeResult, TreeShakeConfig, prune_runtime
from pynext.build.analyze import analyze_bundle, BundleAnalysis, FileAnalysis, print_report, generate_report_json, generate_report_html

__all__ = [
    # Legacy exports
    'minify_js',
    'minify_runtime',
    'bundle_runtime',
    'get_required_modules',
    
    # Core build API
    'compile_project',
    'compile_files',
    'BuildConfig',
    'BuildResult',
    
    # Scanner
    'scan_directory',
    'scan_file',
    'scan_source',
    'IslandInfo',
    'ScanResult',
    
    # Cache
    'BuildCache',
    'CacheEntry',
    'CacheStats',
    'hash_file',
    'hash_content',
    
    # Manifest
    'BuildManifest',
    'IslandEntry',
    'RuntimeEntry',
    'BuildStats',
    
    # Parallel compilation
    'compile_parallel',
    'ParallelConfig',
    'ParallelResult',
    
    # File watcher
    'FileWatcher',
    'WatcherConfig',
    'ChangeEvent',
    'watch_and_compile',
    
    # Hot Module Replacement
    'HMRServer',
    'HMRConfig',
    'HMRUpdate',
    'generate_hmr_client_script',
    
    # Tree shaking
    'tree_shake',
    'analyze_features',
    'TreeShakeResult',
    'TreeShakeConfig',
    'prune_runtime',
    
    # Bundle analysis
    'analyze_bundle',
    'BundleAnalysis',
    'FileAnalysis',
    'print_report',
    'generate_report_json',
    'generate_report_html',
]

