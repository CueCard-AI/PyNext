"""
Phase 34.3: CSS Typed OM Performance Benchmarks

Performance tests to ensure CSS Typed OM transpilation is efficient:
- Factory method creation speed
- Arithmetic operation efficiency  
- StylePropertyMap operations
- Large batch operations

Total: 10 tests
"""

import pytest
import time
from pynext.transpiler import transpile


# =============================================================================
# Factory Creation Benchmarks (3 tests)
# =============================================================================

class TestFactoryPerformance:
    """Tests for CSS factory method transpilation performance."""
    
    def test_px_factory_transpilation_speed(self):
        """CSS.px() should transpile quickly."""
        code = 'value = CSS.px(100)'
        
        start = time.perf_counter()
        for _ in range(100):
            transpile(code)
        elapsed = time.perf_counter() - start
        
        # Should transpile 100 times in under 1 second
        assert elapsed < 1.0, f"CSS.px() too slow: {elapsed:.3f}s for 100 iterations"
    
    def test_multiple_factories_transpilation(self):
        """Multiple factory calls should transpile efficiently."""
        code = '''
a = CSS.px(100)
b = CSS.percent(50)
c = CSS.rem(2)
d = CSS.em(1.5)
e = CSS.deg(45)
'''
        
        start = time.perf_counter()
        for _ in range(100):
            transpile(code)
        elapsed = time.perf_counter() - start
        
        # Should transpile 100 times in under 2 seconds
        assert elapsed < 2.0, f"Multiple factories too slow: {elapsed:.3f}s"
    
    def test_factory_output_is_minimal(self):
        """Factory output should not have bloat."""
        code = 'value = CSS.px(100)'
        result = transpile(code)
        
        # Output should be concise, not bloated with wrappers
        lines = [l for l in result.strip().split('\n') if l.strip()]
        assert len(lines) <= 3, f"Too many lines for simple factory: {len(lines)}"


# =============================================================================
# Arithmetic Operation Benchmarks (3 tests)
# =============================================================================

class TestArithmeticPerformance:
    """Tests for arithmetic operation transpilation performance."""
    
    def test_chained_arithmetic_transpilation(self):
        """Chained arithmetic should transpile efficiently."""
        code = '''
result = CSS.px(100).mul(2).div(2).add(CSS.px(50)).sub(CSS.px(25))
'''
        
        start = time.perf_counter()
        for _ in range(100):
            transpile(code)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 2.0, f"Chained arithmetic too slow: {elapsed:.3f}s"
    
    def test_arithmetic_output_is_clean(self):
        """Arithmetic output should be direct method calls."""
        code = 'result = CSS.px(100).add(CSS.px(50))'
        result = transpile(code)
        
        # Should directly use .add(), not wrapped
        assert '.add(' in result
        assert 'CSS.px(100)' in result
    
    def test_complex_expression_transpilation(self):
        """Complex expressions should transpile correctly."""
        code = '''
width = CSS.clamp(CSS.px(100), CSS.percent(50), CSS.px(500))
'''
        
        start = time.perf_counter()
        for _ in range(100):
            transpile(code)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 2.0, f"Complex expression too slow: {elapsed:.3f}s"


# =============================================================================
# StylePropertyMap Benchmarks (2 tests)
# =============================================================================

class TestStyleMapPerformance:
    """Tests for StylePropertyMap operation performance."""
    
    def test_set_operations_transpilation(self):
        """set() operations should transpile efficiently."""
        code = '''
el.attributeStyleMap.set("width", CSS.px(100))
el.attributeStyleMap.set("height", CSS.px(200))
el.attributeStyleMap.set("margin", CSS.px(10))
el.attributeStyleMap.set("padding", CSS.rem(1))
'''
        
        start = time.perf_counter()
        for _ in range(100):
            transpile(code)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 2.0, f"StylePropertyMap.set too slow: {elapsed:.3f}s"
    
    def test_get_operations_transpilation(self):
        """get() operations should transpile efficiently."""
        code = '''
width = el.attributeStyleMap.get("width")
height = el.attributeStyleMap.get("height")
margin = el.attributeStyleMap.get("margin")
'''
        
        start = time.perf_counter()
        for _ in range(100):
            transpile(code)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 2.0, f"StylePropertyMap.get too slow: {elapsed:.3f}s"


# =============================================================================
# Batch Operation Benchmarks (2 tests)
# =============================================================================

class TestBatchPerformance:
    """Tests for large batch transpilation performance."""
    
    def test_many_declarations_transpilation(self):
        """Many CSS declarations should transpile efficiently."""
        # Generate 50 CSS declarations
        lines = [f'v{i} = CSS.px({i * 10})' for i in range(50)]
        code = '\n'.join(lines)
        
        start = time.perf_counter()
        for _ in range(10):
            transpile(code)
        elapsed = time.perf_counter() - start
        
        # 10 iterations of 50 declarations should complete in under 5 seconds
        assert elapsed < 5.0, f"Batch declarations too slow: {elapsed:.3f}s"
    
    def test_output_size_scales_linearly(self):
        """Output size should scale linearly with input."""
        code_10 = '\n'.join([f'v{i} = CSS.px({i})' for i in range(10)])
        code_50 = '\n'.join([f'v{i} = CSS.px({i})' for i in range(50)])
        
        result_10 = transpile(code_10)
        result_50 = transpile(code_50)
        
        # 50 lines should be roughly 5x the size of 10 lines (within 2x margin)
        ratio = len(result_50) / len(result_10)
        assert 3.0 <= ratio <= 7.0, f"Output doesn't scale linearly: ratio={ratio:.2f}"

