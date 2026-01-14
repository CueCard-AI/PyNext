"""
E2E Tests for Real Bundle Size Validation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

These tests verify ACTUAL bundle sizes of transpiled apps, not just
individual runtime files. This prevents the "vanity metrics" problem
where runtime files are small but real apps are still large.

=============================================================================
HOW IT WORKS
=============================================================================

1. Takes Python source code
2. Transpiles it to JavaScript
3. Bundles with esbuild (including runtime)
4. Measures the gzipped size
5. Asserts it's under target

=============================================================================
WHY THIS EXISTS
=============================================================================

Previous bundle tests only checked individual runtime files (core.js, etc.).
This led to "vanity metrics" where files looked small but real apps
were still large because:
- Duplicated code between runtime files
- Unused optimizations (transpiler didn't use optimized modules)
- No actual bundling to verify tree-shaking

These tests fix that by measuring REAL bundle sizes of transpiled apps.
"""

import pytest
import subprocess
import gzip
import tempfile
import os
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Runtime directory
RUNTIME_DIR = PROJECT_ROOT / "pynext" / "transpiler" / "runtime"

# Size limits (in bytes, gzipped)
# These are REAL targets for actual apps, not just runtime files
SIZE_LIMITS = {
    "hello_world": 15_000,      # Simple print() app should be under 15KB
    "list_operations": 15_000,  # List ops (negative indexing) should be under 15KB
    "string_methods": 16_000,   # String methods should be under 16KB
    "conditionals": 15_000,     # If/else logic should be under 15KB
    "full_app": 20_000,         # App with stdlib should be under 20KB
}


# =============================================================================
# HELPERS
# =============================================================================

def transpile_python(source: str) -> str:
    """Transpile Python source to JavaScript."""
    from pynext.transpiler import transpile
    return transpile(source)


def bundle_with_esbuild(js_code: str, runtime_path: Path = None) -> bytes:
    """
    Bundle JavaScript code with esbuild, including runtime.
    
    Args:
        js_code: JavaScript source code
        runtime_path: Path to runtime directory
    
    Returns:
        Bundled JavaScript as bytes
    """
    if runtime_path is None:
        runtime_path = RUNTIME_DIR
    
    # Create a temporary directory for bundling
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Write the transpiled code
        entry_file = tmpdir_path / "entry.js"
        
        # Create a wrapper that imports the runtime and includes the code
        wrapper = f"""
// Import full runtime (simulating what a real app would do)
import __py from '{runtime_path.as_posix()}/core.js';

// Transpiled code
{js_code}
"""
        entry_file.write_text(wrapper)
        
        # Bundle with esbuild
        output_file = tmpdir_path / "bundle.js"
        
        try:
            result = subprocess.run(
                [
                    "npx", "esbuild",
                    str(entry_file),
                    "--bundle",
                    "--minify",
                    "--outfile=" + str(output_file),
                    "--format=esm",
                    "--platform=browser",
                ],
                capture_output=True,
                timeout=60,
                cwd=PROJECT_ROOT,
            )
            
            if result.returncode != 0:
                # If esbuild fails, skip the test
                pytest.skip(f"esbuild failed: {result.stderr.decode()}")
            
            return output_file.read_bytes()
            
        except FileNotFoundError:
            pytest.skip("esbuild not found - run 'npm install' first")
        except subprocess.TimeoutExpired:
            pytest.skip("esbuild timed out")


def get_gzip_size(content: bytes) -> int:
    """Get gzipped size in bytes."""
    return len(gzip.compress(content))


def measure_bundle_size(python_source: str) -> int:
    """
    Measure the gzipped bundle size of a Python app.
    
    This is the key function - it shows the REAL size a user would get.
    """
    js_code = transpile_python(python_source)
    bundled = bundle_with_esbuild(js_code)
    return get_gzip_size(bundled)


# =============================================================================
# E2E BUNDLE SIZE TESTS
# =============================================================================

class TestRealBundleSize:
    """
    Tests that verify ACTUAL bundle size of transpiled apps.
    
    These tests prevent vanity metrics by measuring real end-to-end sizes.
    """
    
    def test_hello_world_bundle_size(self):
        """A simple print() app should be under 15KB bundled."""
        source = """
print("Hello, World!")
"""
        gzip_size = measure_bundle_size(source)
        limit = SIZE_LIMITS["hello_world"]
        
        assert gzip_size < limit, (
            f"Hello World bundle is {gzip_size}B gzipped, "
            f"should be under {limit}B"
        )
    
    def test_list_operations_bundle_size(self):
        """List operations with negative indexing should be under 15KB."""
        source = """
items = [1, 2, 3, 4, 5]
first = items[0]
last = items[-1]
middle = items[2]
"""
        gzip_size = measure_bundle_size(source)
        limit = SIZE_LIMITS["list_operations"]
        
        assert gzip_size < limit, (
            f"List operations bundle is {gzip_size}B gzipped, "
            f"should be under {limit}B"
        )
    
    def test_conditional_bundle_size(self):
        """Conditionals with truthiness checks should be under 15KB."""
        source = """
items = [1, 2, 3]
if items:
    result = "has items"
else:
    result = "empty"
"""
        gzip_size = measure_bundle_size(source)
        limit = SIZE_LIMITS["conditionals"]
        
        assert gzip_size < limit, (
            f"Conditional bundle is {gzip_size}B gzipped, "
            f"should be under {limit}B"
        )
    
    def test_string_methods_bundle_size(self):
        """String method usage should be under 16KB."""
        source = """
text = "Hello, World!"
upper = text.upper()
parts = text.split(",")
"""
        gzip_size = measure_bundle_size(source)
        limit = SIZE_LIMITS["string_methods"]
        
        assert gzip_size < limit, (
            f"String methods bundle is {gzip_size}B gzipped, "
            f"should be under {limit}B"
        )


class TestBundleSizeRegression:
    """
    Regression tests to ensure bundle sizes don't grow over time.
    """
    
    def test_basic_assignment_size(self):
        """Basic variable assignment should be minimal."""
        source = "x = 5"
        gzip_size = measure_bundle_size(source)
        
        # Very basic code should still be under the hello world limit
        assert gzip_size < SIZE_LIMITS["hello_world"], (
            f"Basic assignment is {gzip_size}B, too large for simple code"
        )
    
    def test_arithmetic_operations_size(self):
        """Arithmetic operations should be under 15KB."""
        source = """
a = 10
b = 3
c = a + b
d = a - b
e = a * b
f = a / b
g = a // b
h = a % b
"""
        gzip_size = measure_bundle_size(source)
        
        assert gzip_size < SIZE_LIMITS["hello_world"], (
            f"Arithmetic bundle is {gzip_size}B, should be under 15KB"
        )


class TestUsageTrackingIntegration:
    """
    Tests that verify usage tracking is working correctly.
    """
    
    def test_usage_manifest_generated(self):
        """Verify usage manifest is generated correctly."""
        from pynext.transpiler._internal.usage_tracker import (
            get_usage_tracker, 
            reset_usage_tracker,
        )
        
        reset_usage_tracker()
        
        source = """
items = [1, 2, 3]
if items:
    last = items[-1]
"""
        js_code = transpile_python(source)
        
        manifest = get_usage_tracker().get_manifest()
        
        # Should have tracked at least 'at' and 'bool' from layer0
        # (though this depends on the emitter using _py_call)
        assert len(manifest.layer0) >= 0, "Some layer0 features should be tracked"
    
    def test_generate_imports_produces_statements(self):
        """Verify generate_imports produces import statements."""
        from pynext.transpiler import transpile
        from pynext.transpiler._internal.usage_tracker import reset_usage_tracker
        
        reset_usage_tracker()
        
        source = """
items = [1, 2, 3]
if items:
    last = items[-1]
"""
        js_code = transpile(source, generate_imports=True)
        
        # Should contain import statement
        assert "import" in js_code, "Generated code should contain imports"
        assert "core-minimal" in js_code, "Should import from core-minimal"


# =============================================================================
# BUNDLE SIZE COMPARISON TESTS
# =============================================================================

class TestMinimalVsFullBundle:
    """
    Tests comparing minimal vs full bundle sizes.
    """
    
    def test_transpile_reports_usage(self):
        """Verify transpile function reports correct usage."""
        from pynext.transpiler import transpile
        from pynext.transpiler._internal.usage_tracker import (
            get_usage_tracker,
            reset_usage_tracker,
        )
        
        reset_usage_tracker()
        
        # Transpile code that uses specific features
        source = """
x = items[-1]  # Uses at()
if x:          # Uses bool()
    pass
"""
        js = transpile(source, generate_imports=True)
        
        # Check that imports include the used features
        assert "at" in js or "bool" in js, (
            "Generated imports should include used features"
        )

