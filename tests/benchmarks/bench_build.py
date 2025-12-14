"""
Real Benchmarks for Phase 17.7 Build System

This file measures ACTUAL performance, not estimates.
Run with: pytest tests/benchmarks/bench_build.py -v --benchmark-only

Results will show:
- Mean time
- Standard deviation
- Min/Max
- Rounds (iterations)
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from pynext.build.scanner import scan_directory, scan_file, scan_source
from pynext.build.cache import BuildCache, hash_file, hash_content
from pynext.build.treeshake import tree_shake, analyze_features
from pynext.build.manifest import BuildManifest


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def island_10(tmp_path):
    """Create 10 island files."""
    for i in range(10):
        (tmp_path / f"island_{i}.py").write_text(f'''
@island
def Island{i}():
    count = signal({i})
    return div()[
        h1()["Counter {i}"],
        button(onclick=lambda: count.update(lambda x: x + 1))[count()],
    ]
''')
    return tmp_path


@pytest.fixture
def island_100(tmp_path):
    """Create 100 island files."""
    for i in range(100):
        (tmp_path / f"island_{i}.py").write_text(f'''
@island
def Island{i}():
    count = signal({i})
    items = store([1, 2, 3])
    double = memo(lambda: count() * 2)
    
    effect(lambda: print(f"Count: {{count()}}"))
    
    return div()[
        h1()["Component {i}"],
        span()[double()],
        For(items, lambda item: li()[item]),
        button(onclick=lambda: count.update(lambda x: x + 1))["Increment"],
    ]
''')
    return tmp_path


@pytest.fixture
def non_island_100(tmp_path):
    """Create 100 non-island files (should be skipped quickly)."""
    for i in range(100):
        (tmp_path / f"utils_{i}.py").write_text(f'''
def helper_{i}():
    """Utility function {i}"""
    return {i} * 2

class Config{i}:
    value = {i}
''')
    return tmp_path


@pytest.fixture
def js_runtime():
    """Sample JavaScript runtime for tree shaking benchmarks."""
    return '''
// PyNext Reactive Runtime
function createSignal(initialValue) {
    let value = initialValue;
    const subscribers = new Set();
    
    const read = () => {
        if (currentObserver) {
            subscribers.add(currentObserver);
        }
        return value;
    };
    
    const write = (newValue) => {
        value = typeof newValue === 'function' ? newValue(value) : newValue;
        subscribers.forEach(fn => fn());
    };
    
    return [read, write];
}

function createStore(initialValue) {
    const signals = {};
    for (const key in initialValue) {
        signals[key] = createSignal(initialValue[key]);
    }
    return signals;
}

function createEffect(fn) {
    const execute = () => {
        currentObserver = execute;
        fn();
        currentObserver = null;
    };
    execute();
}

function createMemo(fn) {
    let cached;
    let dirty = true;
    
    createEffect(() => {
        if (dirty) {
            cached = fn();
            dirty = false;
        }
    });
    
    return () => cached;
}

function Show(props) {
    return props.when ? props.children : null;
}

function For(props) {
    return props.each.map(props.children);
}

function Switch(props) {
    return props.children.find(c => c.when) || null;
}

function Portal(props) {
    return props.children;
}

function ErrorBoundary(props) {
    try {
        return props.children;
    } catch (e) {
        return props.fallback(e);
    }
}

function Suspense(props) {
    return props.children;
}

function batch(fn) {
    fn();
}

function untrack(fn) {
    const prev = currentObserver;
    currentObserver = null;
    const result = fn();
    currentObserver = prev;
    return result;
}

let currentObserver = null;

export {
    createSignal,
    createStore,
    createEffect,
    createMemo,
    Show,
    For,
    Switch,
    Portal,
    ErrorBoundary,
    Suspense,
    batch,
    untrack
};
'''


# =============================================================================
# SCANNER BENCHMARKS
# =============================================================================

class TestScannerBenchmarks:
    """Benchmark scanner performance."""
    
    def test_scan_10_islands(self, island_10, benchmark):
        """Benchmark: Scan 10 island files."""
        result = benchmark(lambda: scan_directory(island_10))
        
        assert result.island_count == 10
        print(f"\n  Found {result.island_count} islands in {result.duration_ms:.2f}ms")
    
    def test_scan_100_islands(self, island_100, benchmark):
        """Benchmark: Scan 100 island files."""
        result = benchmark(lambda: scan_directory(island_100))
        
        assert result.island_count == 100
        print(f"\n  Found {result.island_count} islands in {result.duration_ms:.2f}ms")
    
    def test_scan_100_non_islands(self, non_island_100, benchmark):
        """Benchmark: Skip 100 non-island files (should be fast)."""
        result = benchmark(lambda: scan_directory(non_island_100))
        
        assert result.island_count == 0
        print(f"\n  Scanned {result.files_scanned} files, skipped all in {result.duration_ms:.2f}ms")
    
    def test_scan_single_complex_island(self, tmp_path, benchmark):
        """Benchmark: Scan a complex island file."""
        complex_file = tmp_path / "complex.py"
        complex_file.write_text('''
from pynext import island, signal, store, memo, effect, For, Show

@island
def ComplexDashboard():
    """A complex dashboard component with many reactive features."""
    
    # Multiple signals
    count = signal(0)
    name = signal("")
    active = signal(True)
    
    # Store with nested data
    data = store({
        "users": [],
        "settings": {"theme": "dark", "notifications": True},
        "stats": {"views": 0, "clicks": 0},
    })
    
    # Computed values
    double = memo(lambda: count() * 2)
    triple = memo(lambda: count() * 3)
    summary = memo(lambda: f"{name()} has {count()} items")
    
    # Side effects
    effect(lambda: print(f"Count changed: {count()}"))
    effect(lambda: print(f"Name changed: {name()}"))
    
    return div(class_="dashboard")[
        header()[
            h1()[f"Welcome, {name()}!"],
            span(class_="stats")[f"Count: {count()} | Double: {double()} | Triple: {triple()}"],
        ],
        
        Show(when=lambda: active())[
            main()[
                section()[
                    For(data.users, lambda user: 
                        article(class_="user-card")[
                            h2()[user["name"]],
                            p()[user["email"]],
                        ]
                    ),
                ],
            ],
        ],
        
        footer()[
            button(onclick=lambda: count.update(lambda x: x + 1))["Increment"],
            button(onclick=lambda: active.set(not active()))["Toggle"],
        ],
    ]
''')
        
        result = benchmark(lambda: scan_file(complex_file))
        
        assert result.island_count == 1
        island = result.islands[0]
        assert island.has_signals
        assert island.has_stores
        assert island.has_memos
        assert island.has_effects
        print(f"\n  Scanned complex island in {result.duration_ms:.2f}ms")


# =============================================================================
# CACHE BENCHMARKS
# =============================================================================

class TestCacheBenchmarks:
    """Benchmark cache performance."""
    
    def test_cache_store_100(self, tmp_path, benchmark):
        """Benchmark: Store 100 entries in cache."""
        cache = BuildCache(tmp_path / ".cache")
        
        def store_all():
            for i in range(100):
                cache.store(
                    f"file{i}.py",
                    f"const x{i} = {i};" * 100,  # ~2KB each
                    None,
                    f"hash{i:03d}",
                    [f"Island{i}"],
                )
        
        benchmark(store_all)
        
        stats = cache.get_stats()
        print(f"\n  Stored {stats.total_entries} entries, {stats.cache_size_kb:.1f} KB")
    
    def test_cache_lookup_100(self, tmp_path, benchmark):
        """Benchmark: Lookup 100 entries from cache."""
        cache = BuildCache(tmp_path / ".cache")
        
        # Pre-populate
        for i in range(100):
            cache.store(f"file{i}.py", f"code{i}", None, f"hash{i}", [f"A{i}"])
        
        def lookup_all():
            for i in range(100):
                cache.needs_compile(f"file{i}.py", f"hash{i}")
        
        benchmark(lookup_all)
        
        stats = cache.get_stats()
        print(f"\n  Looked up {stats.total_entries} entries, {stats.hits} hits")
    
    def test_cache_incremental_single(self, tmp_path, benchmark):
        """Benchmark: Single file incremental check (cache hit scenario)."""
        cache = BuildCache(tmp_path / ".cache")
        
        # Store initial
        cache.store("counter.py", "export function Counter() {}", None, "abc123", ["Counter"])
        
        # Benchmark cache hit
        result = benchmark(lambda: cache.needs_compile("counter.py", "abc123"))
        
        assert result is False  # Should be cache hit
        print(f"\n  Cache hit check completed")
    
    def test_hash_file_performance(self, tmp_path, benchmark):
        """Benchmark: File hashing speed."""
        # Create a realistic file
        file = tmp_path / "component.py"
        file.write_text("x = 1\n" * 1000)  # ~6KB file
        
        benchmark(lambda: hash_file(file))
        
        print(f"\n  Hashed {file.stat().st_size} bytes")


# =============================================================================
# TREE SHAKING BENCHMARKS
# =============================================================================

class TestTreeShakeBenchmarks:
    """Benchmark tree shaking performance."""
    
    def test_analyze_features(self, js_runtime, benchmark):
        """Benchmark: Analyze features in runtime."""
        features = benchmark(lambda: analyze_features(js_runtime))
        
        print(f"\n  Found features: {features}")
    
    def test_tree_shake_signals_only(self, js_runtime, benchmark):
        """Benchmark: Tree shake to signals only."""
        result = benchmark(lambda: tree_shake(js_runtime, {"signals"}))
        
        reduction = result.reduction_percent
        print(f"\n  Reduced by {reduction:.1f}% ({result.original_size} -> {result.final_size} bytes)")
    
    def test_tree_shake_full_app(self, js_runtime, benchmark):
        """Benchmark: Tree shake for full app (all features)."""
        result = benchmark(lambda: tree_shake(js_runtime, {"signals", "effects", "stores", "show", "for"}))
        
        reduction = result.reduction_percent
        print(f"\n  Reduced by {reduction:.1f}% (kept: {result.kept_features})")
    
    def test_tree_shake_large_bundle(self, benchmark):
        """Benchmark: Tree shake large bundle (100KB)."""
        # Generate 100KB of JS
        large_bundle = """
function createSignal(x) { return x; }
function createStore(x) { return x; }
function createEffect(x) { return x; }
const data = createSignal(0);
""" * 1000  # ~150KB
        
        result = benchmark(lambda: tree_shake(large_bundle, {"signals"}))
        
        print(f"\n  Processed {result.original_size / 1024:.1f} KB in tree shake")


# =============================================================================
# MANIFEST BENCHMARKS
# =============================================================================

class TestManifestBenchmarks:
    """Benchmark manifest operations."""
    
    def test_manifest_100_islands(self, tmp_path, benchmark):
        """Benchmark: Create manifest with 100 islands."""
        def create_manifest():
            manifest = BuildManifest()
            for i in range(100):
                manifest.add_island(
                    f"Island{i}",
                    f"island_{i}.js",
                    f"components/island_{i}.py",
                    size=500 + i * 10,
                    features=["signals", "effects"],
                )
            manifest.add_runtime("reactive.min.js", 2500)
            return manifest
        
        manifest = benchmark(create_manifest)
        
        print(f"\n  Created manifest with {manifest.stats.total_islands} islands, {manifest.stats.total_size} bytes")
    
    def test_manifest_save_load(self, tmp_path, benchmark):
        """Benchmark: Save and load manifest."""
        manifest = BuildManifest()
        for i in range(50):
            manifest.add_island(f"I{i}", f"i{i}.js", f"i{i}.py", 500)
        
        path = tmp_path / "manifest.json"
        
        def save_and_load():
            manifest.save(path)
            return BuildManifest.load(path)
        
        loaded = benchmark(save_and_load)
        
        print(f"\n  Saved/loaded {loaded.stats.total_islands} islands")


# =============================================================================
# END-TO-END BENCHMARKS
# =============================================================================

class TestEndToEndBenchmarks:
    """End-to-end build benchmarks."""
    
    def test_full_scan_and_cache(self, island_100, benchmark):
        """Benchmark: Full scan + cache check for 100 islands."""
        cache_dir = island_100 / ".cache"
        cache = BuildCache(cache_dir)
        
        def full_pipeline():
            result = scan_directory(island_100)
            for island in result.islands:
                source_hash = hash_file(island.file_path)
                if cache.needs_compile(island.file_path, source_hash):
                    # Would compile here
                    cache.store(
                        island.file_path,
                        f"compiled_{island.name}",
                        None,
                        source_hash,
                        [island.name],
                    )
            return result
        
        result = benchmark(full_pipeline)
        
        print(f"\n  Processed {result.island_count} islands through full pipeline")
    
    def test_incremental_after_cache(self, island_100, benchmark):
        """Benchmark: Incremental build (everything cached)."""
        cache_dir = island_100 / ".cache"
        cache = BuildCache(cache_dir)
        
        # Warm up cache
        result = scan_directory(island_100)
        for island in result.islands:
            source_hash = hash_file(island.file_path)
            cache.store(island.file_path, f"js_{island.name}", None, source_hash, [island.name])
        
        def incremental():
            result = scan_directory(island_100)
            for island in result.islands:
                source_hash = hash_file(island.file_path)
                cache.needs_compile(island.file_path, source_hash)
            return result
        
        result = benchmark(incremental)
        
        stats = cache.get_stats()
        print(f"\n  Incremental check: {stats.hits} cache hits, {stats.misses} misses")


# =============================================================================
# SUMMARY
# =============================================================================

def test_print_summary():
    """Print benchmark summary (run this last)."""
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print("""
Run with: pytest tests/benchmarks/bench_build.py -v --benchmark-only

The benchmark plugin will show actual times for each operation.
Compare results against targets:

| Metric               | Target   | Actual |
|----------------------|----------|--------|
| Scan 10 islands      | < 10ms   | ?      |
| Scan 100 islands     | < 50ms   | ?      |
| Cache 100 stores     | < 50ms   | ?      |
| Cache 100 lookups    | < 10ms   | ?      |
| Incremental (cached) | < 10ms   | ?      |
| Tree shake runtime   | < 5ms    | ?      |
| Full pipeline 100    | < 100ms  | ?      |
""")

