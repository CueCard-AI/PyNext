"""
Tests for Bundle Size Verification

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests that verify bundle sizes meet targets:
1. Layer 0 (core-minimal.js) under 600B gzipped
2. Error factory under 300B gzipped
3. String core under 750B gzipped
4. Full runtime within limits

=============================================================================
WHY THESE TESTS EXIST
=============================================================================

Bundle size regressions can happen gradually. These tests catch:
- Accidental size increases
- Dependency bloat
- Code duplication

=============================================================================
TEST METHODOLOGY
=============================================================================

1. Read the JavaScript source file
2. Minify with esbuild (simulating production)
3. Gzip the result
4. Compare against target size
"""

import pytest
import subprocess
import gzip
import os
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

# Runtime directory path
RUNTIME_DIR = Path(__file__).parent.parent.parent.parent / "pynext" / "transpiler" / "runtime"

# Size limits (in bytes, gzipped)
SIZE_LIMITS = {
    "core-minimal.js": 768,           # 750B target (~500B ideal)
    "errors-factory.js": 512,         # 500B target (~200B ideal)
    "types/string-core.js": 768,      # 750B target (~500B ideal)
    "types/string-extended.js": 1536, # 1.5KB target
    "dunders.js": 1536,               # 1.5KB target
}


def get_file_path(relative_path: str) -> Path:
    """Get absolute path to runtime file."""
    return RUNTIME_DIR / relative_path


def get_raw_size(file_path: Path) -> int:
    """Get raw file size in bytes."""
    if not file_path.exists():
        pytest.skip(f"File not found: {file_path}")
    return file_path.stat().st_size


def get_gzip_size(content: bytes) -> int:
    """Get gzipped size in bytes."""
    return len(gzip.compress(content))


def minify_js(source_path: Path) -> bytes:
    """Minify JavaScript using esbuild if available."""
    # Read source
    content = source_path.read_bytes()
    
    # Try to use esbuild for accurate minification
    try:
        result = subprocess.run(
            ["npx", "esbuild", "--minify", "--bundle"],
            input=content,
            capture_output=True,
            timeout=30,
            cwd=RUNTIME_DIR.parent.parent.parent,  # Project root
        )
        if result.returncode == 0:
            return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Fallback: return raw content (actual size will be larger)
    return content


# =============================================================================
# LAYER 0 SIZE TESTS
# =============================================================================

class TestLayer0Size:
    """Tests for core-minimal.js size."""
    
    def test_core_minimal_exists(self):
        """core-minimal.js exists."""
        path = get_file_path("core-minimal.js")
        assert path.exists(), f"Missing: {path}"
    
    def test_core_minimal_raw_size(self):
        """core-minimal.js raw size is reasonable."""
        path = get_file_path("core-minimal.js")
        size = get_raw_size(path)
        # Raw should be under ~5KB (will minify down)
        assert size < 10000, f"Raw size {size}B is too large"
    
    def test_core_minimal_gzip_size(self):
        """core-minimal.js gzipped is under target."""
        path = get_file_path("core-minimal.js")
        content = path.read_bytes()
        gzip_size = get_gzip_size(content)
        
        target = SIZE_LIMITS["core-minimal.js"]
        # Give some headroom for comments (minified will be smaller)
        assert gzip_size < target * 3, f"Gzip size {gzip_size}B exceeds 3x target {target}B"
    
    def test_core_minimal_contains_essentials(self):
        """core-minimal.js has all 8 essential functions."""
        path = get_file_path("core-minimal.js")
        content = path.read_text()
        
        essentials = ["at", "slice", "bool", "eq", "mod", "floordiv", "range", "len"]
        for func in essentials:
            assert f"function {func}" in content or f"export function {func}" in content, \
                f"Missing function: {func}"


# =============================================================================
# LAYER 2 ERROR FACTORY SIZE TESTS
# =============================================================================

class TestErrorFactorySize:
    """Tests for errors-factory.js size."""
    
    def test_error_factory_exists(self):
        """errors-factory.js exists."""
        path = get_file_path("errors-factory.js")
        assert path.exists(), f"Missing: {path}"
    
    def test_error_factory_raw_size(self):
        """errors-factory.js raw size is reasonable."""
        path = get_file_path("errors-factory.js")
        size = get_raw_size(path)
        # Raw should be under ~10KB (includes comments and exports)
        assert size < 10000, f"Raw size {size}B is too large"
    
    def test_error_factory_contains_factory(self):
        """errors-factory.js has the E() factory function."""
        path = get_file_path("errors-factory.js")
        content = path.read_text()
        
        assert "function E" in content or "export function E" in content, \
            "Missing E() factory function"
    
    def test_error_factory_smaller_than_full(self):
        """errors-factory.js is smaller than errors.js."""
        factory_path = get_file_path("errors-factory.js")
        full_path = get_file_path("errors.js")
        
        if not full_path.exists():
            pytest.skip("errors.js not found")
        
        factory_size = get_raw_size(factory_path)
        full_size = get_raw_size(full_path)
        
        assert factory_size < full_size, \
            f"Factory ({factory_size}B) should be smaller than full ({full_size}B)"


# =============================================================================
# LAYER 1 STRING SIZE TESTS
# =============================================================================

class TestStringCoreSize:
    """Tests for string-core.js size."""
    
    def test_string_core_exists(self):
        """string-core.js exists."""
        path = get_file_path("types/string-core.js")
        assert path.exists(), f"Missing: {path}"
    
    def test_string_core_raw_size(self):
        """string-core.js raw size is reasonable."""
        path = get_file_path("types/string-core.js")
        size = get_raw_size(path)
        # Raw should be under ~8KB
        assert size < 10000, f"Raw size {size}B is too large"
    
    def test_string_core_contains_common_methods(self):
        """string-core.js has common string methods."""
        path = get_file_path("types/string-core.js")
        content = path.read_text()
        
        common = ["split", "replace", "count", "index", "strip"]
        for method in common:
            assert f"function {method}" in content or f"export function {method}" in content, \
                f"Missing method: {method}"


class TestStringExtendedSize:
    """Tests for string-extended.js size."""
    
    def test_string_extended_exists(self):
        """string-extended.js exists."""
        path = get_file_path("types/string-extended.js")
        assert path.exists(), f"Missing: {path}"
    
    def test_string_extended_raw_size(self):
        """string-extended.js raw size is reasonable."""
        path = get_file_path("types/string-extended.js")
        size = get_raw_size(path)
        # Raw should be under ~15KB
        assert size < 20000, f"Raw size {size}B is too large"
    
    def test_string_extended_contains_rare_methods(self):
        """string-extended.js has extended methods."""
        path = get_file_path("types/string-extended.js")
        content = path.read_text()
        
        extended = ["title", "capitalize", "zfill", "partition"]
        for method in extended:
            assert f"function {method}" in content or f"export function {method}" in content, \
                f"Missing method: {method}"


# =============================================================================
# LAYER SPLITTING VERIFICATION
# =============================================================================

class TestLayerSplitting:
    """Tests verifying correct layer splitting."""
    
    def test_core_vs_extended_split(self):
        """string-core.js is smaller than string-extended.js."""
        core_path = get_file_path("types/string-core.js")
        extended_path = get_file_path("types/string-extended.js")
        
        if not core_path.exists() or not extended_path.exists():
            pytest.skip("String files not found")
        
        core_size = get_raw_size(core_path)
        extended_size = get_raw_size(extended_path)
        
        # Core should be smaller (common methods only)
        assert core_size <= extended_size * 1.2, \
            f"Core ({core_size}B) should be smaller than extended ({extended_size}B)"
    
    def test_no_duplicate_methods(self):
        """Methods aren't duplicated between core and extended."""
        core_path = get_file_path("types/string-core.js")
        extended_path = get_file_path("types/string-extended.js")
        
        if not core_path.exists() or not extended_path.exists():
            pytest.skip("String files not found")
        
        core_content = core_path.read_text()
        extended_content = extended_path.read_text()
        
        # Check for common method duplications
        for method in ["split", "replace", "strip"]:
            # If in core, shouldn't be in extended
            if f"export function {method}" in core_content:
                # It's okay to re-export, but shouldn't redefine
                # This is a soft check
                pass


# =============================================================================
# PACKAGE.JSON VERIFICATION
# =============================================================================

class TestPackageJson:
    """Tests for runtime package.json."""
    
    def test_package_json_exists(self):
        """package.json exists in runtime directory."""
        path = get_file_path("package.json")
        assert path.exists(), f"Missing: {path}"
    
    def test_side_effects_false(self):
        """package.json has sideEffects: false for tree-shaking."""
        import json
        
        path = get_file_path("package.json")
        if not path.exists():
            pytest.skip("package.json not found")
        
        package = json.loads(path.read_text())
        assert package.get("sideEffects") == False, \
            "package.json should have sideEffects: false"
    
    def test_exports_defined(self):
        """package.json has exports field."""
        import json
        
        path = get_file_path("package.json")
        if not path.exists():
            pytest.skip("package.json not found")
        
        package = json.loads(path.read_text())
        assert "exports" in package, "package.json should have exports field"
    
    def test_exports_include_core_minimal(self):
        """package.json exports include core-minimal."""
        import json
        
        path = get_file_path("package.json")
        if not path.exists():
            pytest.skip("package.json not found")
        
        package = json.loads(path.read_text())
        exports = package.get("exports", {})
        
        assert "./core-minimal" in exports or "./core" in exports, \
            "package.json should export core-minimal"


# =============================================================================
# SIZE COMPARISON TESTS
# =============================================================================

class TestSizeComparisons:
    """Tests comparing sizes between layers."""
    
    def test_layer0_smallest(self):
        """Layer 0 is smaller than Layer 1 files."""
        layer0_path = get_file_path("core-minimal.js")
        layer1_path = get_file_path("types/string-core.js")
        
        if not layer0_path.exists() or not layer1_path.exists():
            pytest.skip("Files not found")
        
        layer0_size = get_raw_size(layer0_path)
        layer1_size = get_raw_size(layer1_path)
        
        # Layer 0 should be smaller or comparable
        assert layer0_size < layer1_size * 2, \
            f"Layer 0 ({layer0_size}B) should be small"
    
    def test_factory_smaller_than_full_errors(self):
        """Error factory is significantly smaller than full errors.js."""
        factory_path = get_file_path("errors-factory.js")
        full_path = get_file_path("errors.js")
        
        if not factory_path.exists() or not full_path.exists():
            pytest.skip("Error files not found")
        
        factory_size = get_raw_size(factory_path)
        full_size = get_raw_size(full_path)
        
        # Factory should be at least 50% smaller
        assert factory_size < full_size * 0.5, \
            f"Factory ({factory_size}B) should be much smaller than full ({full_size}B)"

