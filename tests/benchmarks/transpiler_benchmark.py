"""
PyNext Transpiler Benchmarks

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Benchmarks for the Python-to-JavaScript transpiler to track performance.

Run with: pytest tests/benchmarks/transpiler_benchmark.py -v

=============================================================================
METRICS
=============================================================================

- Transpilation speed (ms per handler)
- Throughput (handlers per second)
- Memory usage
"""

import pytest
import time
from pynext.transpiler import transpile, transpile_handler


# =============================================================================
# SAMPLE HANDLERS
# =============================================================================

SIMPLE_HANDLER = '''
def handle_click():
    count.set(count() + 1)
'''

MEDIUM_HANDLER = '''
def handle_submit():
    if not form.validate():
        errors.set(form.errors)
        return
    items.set([*items(), form.values])
    form.reset()
    show_form.set(False)
'''

COMPLEX_HANDLER = '''
def process_data():
    result = []
    for i, item in enumerate(items()):
        if item.active:
            value = item.value * 2
            result = result + [value]
    filtered.set(result)
    
    total = 0
    for x in result:
        total = total + x
    
    if total > 100:
        status.set("high")
    elif total > 50:
        status.set("medium")
    else:
        status.set("low")
'''

MANY_STATEMENTS = '''
def lots_of_work():
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = a + b
    g = c + d
    h = e + f
    i = g + h
    j = i * 2
    k = j - 1
    l = k // 3
    m = l % 7
    n = m ** 2
    result = n
    return result
'''

NESTED_CONTROL_FLOW = '''
def nested_logic():
    for i in range(10):
        for j in range(10):
            if i > 5:
                if j > 5:
                    process(i, j)
                else:
                    skip(i, j)
            else:
                if j < 3:
                    handle_early(i, j)
                else:
                    handle_mid(i, j)
'''


# =============================================================================
# BENCHMARKS
# =============================================================================

class TestTranspilerPerformance:
    """Benchmark transpiler performance."""
    
    def test_simple_handler_speed(self, benchmark):
        """Benchmark simple handler transpilation."""
        result = benchmark(transpile, SIMPLE_HANDLER)
        assert "function handle_click()" in result
    
    def test_medium_handler_speed(self, benchmark):
        """Benchmark medium complexity handler."""
        result = benchmark(transpile, MEDIUM_HANDLER)
        assert "function handle_submit()" in result
    
    def test_complex_handler_speed(self, benchmark):
        """Benchmark complex handler with loops and conditionals."""
        result = benchmark(transpile, COMPLEX_HANDLER)
        assert "function process_data()" in result
    
    def test_many_statements_speed(self, benchmark):
        """Benchmark handler with many statements."""
        result = benchmark(transpile, MANY_STATEMENTS)
        assert "function lots_of_work()" in result
    
    def test_nested_control_flow_speed(self, benchmark):
        """Benchmark deeply nested control flow."""
        result = benchmark(transpile, NESTED_CONTROL_FLOW)
        assert "function nested_logic()" in result


class TestTranspilerThroughput:
    """Measure transpiler throughput."""
    
    def test_throughput_simple(self):
        """Measure simple handlers per second."""
        iterations = 1000
        start = time.perf_counter()
        
        for _ in range(iterations):
            transpile(SIMPLE_HANDLER)
        
        elapsed = time.perf_counter() - start
        handlers_per_second = iterations / elapsed
        ms_per_handler = (elapsed / iterations) * 1000
        
        print(f"\nSimple handler: {handlers_per_second:.0f} handlers/sec, {ms_per_handler:.2f} ms/handler")
        
        # Target: < 10ms per handler
        assert ms_per_handler < 10, f"Simple handler too slow: {ms_per_handler:.2f} ms"
    
    def test_throughput_complex(self):
        """Measure complex handlers per second."""
        iterations = 100
        start = time.perf_counter()
        
        for _ in range(iterations):
            transpile(COMPLEX_HANDLER)
        
        elapsed = time.perf_counter() - start
        handlers_per_second = iterations / elapsed
        ms_per_handler = (elapsed / iterations) * 1000
        
        print(f"\nComplex handler: {handlers_per_second:.0f} handlers/sec, {ms_per_handler:.2f} ms/handler")
        
        # Target: < 20ms per handler
        assert ms_per_handler < 20, f"Complex handler too slow: {ms_per_handler:.2f} ms"


class TestOutputSize:
    """Measure output JavaScript size."""
    
    def test_simple_handler_size(self):
        """Measure simple handler output size."""
        result = transpile(SIMPLE_HANDLER)
        size = len(result)
        print(f"\nSimple handler output: {size} bytes")
        
        # Should be reasonably small
        assert size < 500, f"Simple handler output too large: {size} bytes"
    
    def test_complex_handler_size(self):
        """Measure complex handler output size."""
        result = transpile(COMPLEX_HANDLER)
        size = len(result)
        print(f"\nComplex handler output: {size} bytes")
        
        # Complex handlers should still be reasonable
        assert size < 2000, f"Complex handler output too large: {size} bytes"
    
    def test_output_readability(self):
        """Verify output is readable (has proper indentation)."""
        result = transpile(MEDIUM_HANDLER)
        
        # Should have proper indentation
        lines = result.split('\n')
        indented_lines = [l for l in lines if l.startswith('    ')]
        
        assert len(indented_lines) > 0, "Output should have indented lines"


class TestCorrectness:
    """Verify output correctness across fix scenarios."""
    
    def test_scope_tracking_in_benchmark(self):
        """Verify scope tracking works in complex handler."""
        result = transpile(COMPLEX_HANDLER)
        
        # result should be declared with let once
        assert result.count("let result") == 1
        # total should be declared with let once
        assert result.count("let total") == 1
    
    def test_tuple_unpacking_in_benchmark(self):
        """Verify tuple unpacking works."""
        result = transpile(COMPLEX_HANDLER)
        
        # Should use destructuring for enumerate
        assert "const [i, item]" in result
    
    def test_iteration_in_benchmark(self):
        """Verify iteration uses __py.iter."""
        result = transpile(COMPLEX_HANDLER)
        
        # Should use __py.iter for for-in loops
        assert "__py.iter" in result
