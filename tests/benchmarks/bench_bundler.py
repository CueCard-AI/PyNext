"""
Benchmarks for PyNext Bundler (Route Chunks & NPM).

Measures:
1. Package usage analysis (tree-shaking)
2. Route chunk generation
3. Manifest generation
4. Chunk URL computation

Run with:
    python -m pytest tests/benchmarks/bench_bundler.py -v --benchmark-only
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from pynext.bundler.npm import NPMBundler
from pynext.bundler.route_chunks import (
    RouteChunkGenerator,
    RouteChunkInfo,
    ChunkDependency,
)


# =============================================================================
# Package Analysis Benchmarks
# =============================================================================

class TestPackageAnalysisBenchmarks:
    """Benchmarks for package usage analysis."""
    
    def test_analyze_simple_imports(self, benchmark):
        """Analyze simple import statements."""
        bundler = NPMBundler()
        
        source = '''
        import { debounce, throttle } from "lodash";
        const fn = debounce(() => {}, 100);
        '''
        
        def analyze():
            return bundler.analyze_package_usage(source, "lodash")
        
        result = benchmark(analyze)
        assert "debounce" in result
    
    def test_analyze_complex_source(self, benchmark):
        """Analyze complex source with many imports."""
        bundler = NPMBundler()
        
        source = '''
        import { debounce, throttle, map, filter, reduce } from "lodash";
        import { Chart, LineController, BarController } from "chart.js";
        
        const data = map([1,2,3], x => x * 2);
        const filtered = filter(data, x => x > 2);
        const sum = reduce(filtered, (a, b) => a + b, 0);
        
        lodash.debounce(() => {
            lodash.throttle(() => {}, 50);
        }, 100);
        ''' * 10  # Repeat for larger source
        
        def analyze():
            return bundler.analyze_package_usage(source, "lodash")
        
        result = benchmark(analyze)
        assert len(result) > 0
    
    def test_analyze_no_matches(self, benchmark):
        """Analyze source with no package usage."""
        bundler = NPMBundler()
        
        source = '''
        function hello() {
            console.log("Hello, World!");
            return 42;
        }
        ''' * 100
        
        def analyze():
            return bundler.analyze_package_usage(source, "lodash")
        
        result = benchmark(analyze)
        assert result == []


# =============================================================================
# Route Chunk Generation Benchmarks
# =============================================================================

class TestChunkGenerationBenchmarks:
    """Benchmarks for chunk generation."""
    
    def test_route_to_chunk_name(self, benchmark):
        """Convert routes to chunk names."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        routes = [
            "/",
            "/dashboard",
            "/users/[id]",
            "/posts/[...slug]",
            "/admin/settings/profile",
        ] * 20
        
        def convert():
            return [generator._route_to_chunk_name(r) for r in routes]
        
        result = benchmark(convert)
        assert len(result) == 100
    
    def test_chunk_info_creation(self, benchmark):
        """Create RouteChunkInfo objects."""
        def create():
            return RouteChunkInfo(
                route="/dashboard",
                chunk_name="dashboard",
                needs_signals=True,
                needs_resource=True,
                needs_suspense=True,
                islands=["widget1", "widget2"],
                lazy_components=["heavy1"],
            )
        
        result = benchmark(create)
        assert result.route == "/dashboard"
    
    def test_generate_chunk_file(self, benchmark):
        """Generate actual chunk file."""
        mock_router = MagicMock()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = RouteChunkGenerator(
                router=mock_router,
                output_dir=tmpdir,
            )
            
            chunk_info = RouteChunkInfo(
                route="/test",
                chunk_name="test",
                needs_signals=True,
                islands=["widget"],
            )
            
            def generate():
                # Reset for each iteration
                chunk_info.chunk_path = None
                chunk_info.hash = None
                return generator._generate_chunk(chunk_info)
            
            result = benchmark(generate)
            assert result.exists()


# =============================================================================
# Manifest Generation Benchmarks
# =============================================================================

class TestManifestBenchmarks:
    """Benchmarks for manifest operations."""
    
    def test_get_manifest_small(self, benchmark):
        """Generate manifest for small app."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        for i in range(5):
            generator.routes[f"/page-{i}"] = RouteChunkInfo(
                route=f"/page-{i}",
                chunk_name=f"page-{i}",
                size=1000 + i * 100,
                hash=f"abc{i}",
                needs_signals=i % 2 == 0,
            )
        
        def get_manifest():
            return generator.get_manifest()
        
        result = benchmark(get_manifest)
        assert len(result["chunks"]) == 5
    
    def test_get_manifest_large(self, benchmark):
        """Generate manifest for large app (100 routes)."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        for i in range(100):
            generator.routes[f"/page-{i}"] = RouteChunkInfo(
                route=f"/page-{i}",
                chunk_name=f"page-{i}",
                size=1000 + i * 100,
                hash=f"hash{i:04d}",
                needs_signals=i % 2 == 0,
                needs_resource=i % 3 == 0,
            )
        
        def get_manifest():
            return generator.get_manifest()
        
        result = benchmark(get_manifest)
        assert len(result["chunks"]) == 100
    
    def test_manifest_to_json(self, benchmark):
        """Serialize manifest to JSON."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        for i in range(50):
            generator.routes[f"/page-{i}"] = RouteChunkInfo(
                route=f"/page-{i}",
                chunk_name=f"page-{i}",
                size=1000,
                hash=f"hash{i:04d}",
            )
        
        manifest = generator.get_manifest()
        
        def serialize():
            return json.dumps(manifest)
        
        result = benchmark(serialize)
        assert "chunks" in result


# =============================================================================
# URL & Tag Generation Benchmarks
# =============================================================================

class TestURLBenchmarks:
    """Benchmarks for URL and tag generation."""
    
    def test_get_chunk_url(self, benchmark):
        """Get chunk URL."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        generator.routes["/dashboard"] = RouteChunkInfo(
            route="/dashboard",
            chunk_name="dashboard",
            hash="abc12345",
        )
        
        def get_url():
            return generator.get_chunk_url("/dashboard")
        
        result = benchmark(get_url)
        assert "dashboard.js" in result
    
    def test_get_preload_tags(self, benchmark):
        """Generate preload tags."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        generator.routes["/dashboard"] = RouteChunkInfo(
            route="/dashboard",
            chunk_name="dashboard",
            chunk_path=Path("/tmp/dashboard.js"),
            hash="abc123",
            prefetch_routes=["/settings", "/users"],
        )
        generator.routes["/settings"] = RouteChunkInfo(
            route="/settings",
            chunk_name="settings",
            chunk_path=Path("/tmp/settings.js"),
            hash="def456",
        )
        generator.routes["/users"] = RouteChunkInfo(
            route="/users",
            chunk_name="users",
            chunk_path=Path("/tmp/users.js"),
            hash="ghi789",
        )
        
        def get_tags():
            return generator.get_preload_tags("/dashboard")
        
        result = benchmark(get_tags)
        assert len(result) > 0
    
    def test_get_script_tags(self, benchmark):
        """Generate script tags."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        generator.routes["/dashboard"] = RouteChunkInfo(
            route="/dashboard",
            chunk_name="dashboard",
            chunk_path=Path("/tmp/dashboard.js"),
            hash="abc123",
        )
        
        def get_tags():
            return generator.get_script_tags("/dashboard")
        
        result = benchmark(get_tags)
        assert len(result) > 0


# =============================================================================
# Statistics Benchmarks
# =============================================================================

class TestStatsBenchmarks:
    """Benchmarks for statistics computation."""
    
    def test_get_stats(self, benchmark):
        """Compute chunk statistics."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        for i in range(50):
            generator.routes[f"/page-{i}"] = RouteChunkInfo(
                route=f"/page-{i}",
                chunk_name=f"page-{i}",
                size=1000 + i * 100,
                needs_signals=i % 2 == 0,
                needs_resource=i % 3 == 0,
                needs_suspense=i % 5 == 0,
                islands=["widget"] if i % 4 == 0 else [],
                lazy_components=["heavy"] if i % 7 == 0 else [],
            )
        
        def get_stats():
            return generator.get_stats()
        
        result = benchmark(get_stats)
        assert result["totalRoutes"] == 50
    
    def test_get_total_size(self, benchmark):
        """Compute total chunk size."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        for i in range(100):
            generator.routes[f"/page-{i}"] = RouteChunkInfo(
                route=f"/page-{i}",
                chunk_name=f"page-{i}",
                size=1000 + i * 50,
            )
        
        def get_size():
            return generator.get_total_size()
        
        result = benchmark(get_size)
        assert result > 100000


# =============================================================================
# Shared Chunk Detection Benchmarks
# =============================================================================

class TestSharedChunkBenchmarks:
    """Benchmarks for shared chunk computation."""
    
    def test_compute_shared_small(self, benchmark):
        """Compute shared chunk for small app."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        for i in range(10):
            generator.routes[f"/page-{i}"] = RouteChunkInfo(
                route=f"/page-{i}",
                chunk_name=f"page-{i}",
                needs_signals=True,
                needs_resource=i % 2 == 0,
            )
        
        def compute():
            generator.runtime_modules.clear()
            generator.shared_chunk = None
            generator._compute_shared_chunk()
            return generator.runtime_modules
        
        result = benchmark(compute)
        assert "__signals__" in result
    
    def test_compute_shared_large(self, benchmark):
        """Compute shared chunk for large app."""
        mock_router = MagicMock()
        generator = RouteChunkGenerator(router=mock_router)
        
        for i in range(100):
            deps = {}
            if i % 2 == 0:
                deps["lodash"] = ChunkDependency(module="lodash", is_npm=True)
            if i % 3 == 0:
                deps["chart.js"] = ChunkDependency(module="chart.js", is_npm=True)
            
            generator.routes[f"/page-{i}"] = RouteChunkInfo(
                route=f"/page-{i}",
                chunk_name=f"page-{i}",
                needs_signals=i % 2 == 0,
                needs_resource=i % 3 == 0,
                dependencies=deps,
            )
        
        def compute():
            generator.runtime_modules.clear()
            generator.shared_chunk = None
            generator._compute_shared_chunk()
            return generator.shared_chunk
        
        result = benchmark(compute)
        # lodash used by 50 routes, chart.js by 34 routes


# =============================================================================
# NPM Bundler Benchmarks
# =============================================================================

class TestNPMBundlerBenchmarks:
    """Benchmarks for NPM bundler operations."""
    
    def test_is_react_package(self, benchmark):
        """Check if package is React-related."""
        bundler = NPMBundler()
        
        packages = [
            "react", "react-dom", "@mui/material", "@radix-ui/react-dialog",
            "lodash", "chart.js", "d3", "axios", "framer-motion",
            "@emotion/react", "styled-components",
        ] * 10
        
        def check():
            return [bundler._is_react_package(p) for p in packages]
        
        result = benchmark(check)
        assert len(result) == 110
    
    def test_get_import_map(self, benchmark):
        """Generate import map."""
        bundler = NPMBundler()
        
        for i in range(20):
            bundler._bundled[f"package-{i}"] = Path(f"/tmp/pkg{i}.bundle.js")
        
        def get_map():
            return bundler.get_import_map()
        
        result = benchmark(get_map)
        assert len(result) == 20
    
    def test_get_esbuild_aliases(self, benchmark):
        """Get React → Preact aliases."""
        bundler = NPMBundler(react_compat=True)
        
        def get_aliases():
            return bundler._get_esbuild_aliases()
        
        result = benchmark(get_aliases)
        assert len(result) == 5


# =============================================================================
# Summary Stats
# =============================================================================

def test_print_bundler_summary():
    """Print bundler performance summary."""
    import time
    
    print("\n" + "=" * 70)
    print("BUNDLER PERFORMANCE SUMMARY")
    print("=" * 70)
    
    bundler = NPMBundler()
    mock_router = MagicMock()
    generator = RouteChunkGenerator(router=mock_router)
    
    # Package analysis
    source = 'import { debounce, throttle } from "lodash";' * 100
    
    start = time.perf_counter()
    for _ in range(1000):
        bundler.analyze_package_usage(source, "lodash")
    analysis_time = (time.perf_counter() - start) * 1000
    
    print(f"\n1000 package analyses: {analysis_time:.2f}ms")
    
    # Route to chunk name
    routes = ["/dashboard", "/users/[id]", "/posts/[...slug]"] * 100
    
    start = time.perf_counter()
    for _ in range(1000):
        [generator._route_to_chunk_name(r) for r in routes]
    convert_time = (time.perf_counter() - start) * 1000
    
    print(f"1000 route conversions (300 routes each): {convert_time:.2f}ms")
    
    # Manifest generation
    for i in range(100):
        generator.routes[f"/page-{i}"] = RouteChunkInfo(
            route=f"/page-{i}", chunk_name=f"page-{i}", size=1000
        )
    
    start = time.perf_counter()
    for _ in range(1000):
        generator.get_manifest()
    manifest_time = (time.perf_counter() - start) * 1000
    
    print(f"1000 manifest generations (100 routes): {manifest_time:.2f}ms")
    
    print("\n" + "=" * 70)

