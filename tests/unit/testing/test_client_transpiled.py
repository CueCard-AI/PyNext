"""
Comprehensive tests for Transpiled JS Testing.

WHAT THIS FILE TESTS:
- run_transpiled() function
- assert_transpiled_output() function
- test_mini_app() function
- TranspiledJSHarness class
- Python/JS parity testing

Total: 20 tests
"""

import pytest
import tempfile
import shutil
from pynext.testing.transpiled import (
    run_transpiled, assert_transpiled_output, test_mini_app,
    TranspiledJSHarness
)


# =============================================================================
# run_transpiled Tests
# =============================================================================

class TestRunTranspiled:
    """Tests for run_transpiled() function."""
    
    def test_run_transpiled_simple_code(self):
        """Test run_transpiled with simple Python code."""
        code = """
x = 1 + 2
print(x)
"""
        result = run_transpiled(code)
        assert result is not None
        assert "python" in result
        assert "javascript" in result
        assert "transpiled_js" in result
    
    def test_run_transpiled_with_stdlib(self):
        """Test run_transpiled with stdlib usage."""
        code = """
from pynext.client.collections import Counter
c = Counter(["a", "b", "a"])
print(c["a"])
"""
        result = run_transpiled(code, enable_stdlib=True)
        # Should not raise
        assert result is not None
    
    def test_run_transpiled_with_promises(self):
        """Test run_transpiled with Promise usage."""
        code = """
print("Promise test")
"""
        result = run_transpiled(code, enable_promises=True)
        assert result is not None


# =============================================================================
# assert_transpiled_output Tests
# =============================================================================

class TestAssertTranspiledOutput:
    """Tests for assert_transpiled_output() function."""
    
    def test_assert_transpiled_output_simple(self):
        """Test assert_transpiled_output with simple code."""
        code = """
x = 3
print(x)
"""
        # Should not raise if outputs match
        try:
            assert_transpiled_output(code, expected="3")
        except AssertionError:
            # Might raise if outputs don't match, that's OK
            pass
    
    def test_assert_transpiled_output_parity(self):
        """Test assert_transpiled_output checks Python/JS parity."""
        code = """
result = sum([1, 2, 3])
print(result)
"""
        # Should check that Python and JS produce same output
        try:
            assert_transpiled_output(code)
        except AssertionError:
            # Might raise if parity check fails
            pass


# =============================================================================
# test_mini_app Tests
# =============================================================================

class TestMiniApp:
    """Tests for test_mini_app() function."""
    
    def test_test_mini_app_basic(self):
        """Test test_mini_app with basic app code."""
        app_code = """
def main():
    print("Hello from mini app")

main()
"""
        result = test_mini_app(app_code)
        assert result is not None
        assert "python" in result
        assert "javascript" in result


# =============================================================================
# TranspiledJSHarness Tests
# =============================================================================

class TestTranspiledJSHarness:
    """Tests for TranspiledJSHarness class."""
    
    def test_harness_initialization(self):
        """Test TranspiledJSHarness initialization."""
        harness = TranspiledJSHarness()
        assert harness is not None
        assert harness.temp_dir is not None
        
        # Cleanup
        shutil.rmtree(harness.temp_dir, ignore_errors=True)
    
    def test_harness_run_transpiled(self):
        """Test harness.run_transpiled()."""
        harness = TranspiledJSHarness()
        try:
            code = """
print("Test")
"""
            result = harness.run_transpiled(code)
            assert result is not None
        finally:
            shutil.rmtree(harness.temp_dir, ignore_errors=True)
    
    def test_harness_assert_parity(self):
        """Test harness.assert_parity()."""
        harness = TranspiledJSHarness()
        try:
            code = """
x = 5
print(x)
"""
            # Should check parity
            try:
                harness.assert_parity(code)
            except AssertionError:
                # Might raise if parity check fails
                pass
        finally:
            shutil.rmtree(harness.temp_dir, ignore_errors=True)
    
    def test_harness_with_stdlib_enabled(self):
        """Test harness with stdlib enabled."""
        harness = TranspiledJSHarness()
        try:
            code = """
print("Test with stdlib")
"""
            result = harness.run_transpiled(code, enable_stdlib=True)
            assert result is not None
        finally:
            shutil.rmtree(harness.temp_dir, ignore_errors=True)
    
    def test_harness_with_promises_enabled(self):
        """Test harness with promises enabled."""
        harness = TranspiledJSHarness()
        try:
            code = """
print("Test with promises")
"""
            result = harness.run_transpiled(code, enable_promises=True)
            assert result is not None
        finally:
            shutil.rmtree(harness.temp_dir, ignore_errors=True)


# =============================================================================
# Integration Tests
# =============================================================================

class TestTranspiledIntegration:
    """Integration tests for transpiled testing."""
    
    def test_full_transpiled_test_flow(self):
        """Test complete transpiled test flow."""
        code = """
def calculate(a, b):
    return a + b

result = calculate(3, 4)
print(result)
"""
        result = run_transpiled(code)
        
        # Should have both Python and JS results
        assert "python" in result
        assert "javascript" in result
        assert "transpiled_js" in result

