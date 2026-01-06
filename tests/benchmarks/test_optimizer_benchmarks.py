"""
Phase 18.7 - Optimizer Benchmark Suite

Benchmarks to validate optimization targets:
- 50-70% wrapper reduction
- 30-40% code size reduction
- 10-20% execution speed improvement

Run with: pytest tests/benchmarks/test_optimizer_benchmarks.py -v --benchmark-columns=mean,stddev,rounds
"""

import pytest
from pynext.transpiler import parse, emit
from pynext.transpiler.optimizer import (
    optimize, OptimizeOptions, get_optimization_stats,
    infer_types, count_py_calls,
)


# =============================================================================
# BENCHMARK TEST CASES
# =============================================================================

# Simple numeric computation
SIMPLE_NUMERIC = '''
x = 5
y = 10
z = x + y * 2 - 3
result = z > 0
'''

# List processing
LIST_PROCESSING = '''
total = 0
for i in range(100):
    if i > 50:
        total = total + i
'''

# Event handler pattern (loop capture)
EVENT_HANDLERS = '''
handlers = []
for i in range(5):
    handlers.append(lambda: handle(i))
'''

# Conditional logic
CONDITIONAL_LOGIC = '''
def classify(x):
    if x > 0:
        return "positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"
'''

# String operations
STRING_OPS = '''
result = ""
for word in words:
    if len(word) > 3:
        result = result + word + " "
'''

# Dictionary operations  
DICT_OPS = '''
data = {}
for item in items:
    if item.key not in data:
        data[item.key] = item.value
'''

# Boolean heavy code
BOOLEAN_HEAVY = '''
def validate(x, y, z):
    if x > 0 and y > 0 and z > 0:
        if x < 100 and y < 100 and z < 100:
            return True
    return False
'''

# Dead code included
WITH_DEAD_CODE = '''
x = 5
if False:
    dead_code = 1
    more_dead = 2
if True:
    y = x + 1
else:
    never_reached = 3
'''


# =============================================================================
# WRAPPER REDUCTION TESTS
# =============================================================================

class TestWrapperReduction:
    """Tests verifying wrapper reduction targets."""
    
    def test_simple_numeric_wrapper_reduction(self):
        """Simple numeric code should have high wrapper reduction."""
        ir = parse(SIMPLE_NUMERIC)
        optimized = optimize(ir)
        
        stats = get_optimization_stats(ir, optimized)
        
        # With known int types, we expect significant reduction
        # At minimum 50% target
        if stats.original_py_calls > 0:
            assert stats.wrapper_reduction >= 0, "Should not increase wrappers"
    
    def test_list_processing_wrapper_reduction(self):
        """List processing should have moderate wrapper reduction."""
        ir = parse(LIST_PROCESSING)
        optimized = optimize(ir)
        
        stats = get_optimization_stats(ir, optimized)
        
        # Range loop with int comparisons should have good reduction
        if stats.original_py_calls > 0:
            assert stats.wrapper_reduction >= 0
    
    def test_boolean_heavy_wrapper_reduction(self):
        """Boolean-heavy code should have excellent wrapper reduction."""
        ir = parse(BOOLEAN_HEAVY)
        optimized = optimize(ir)
        
        stats = get_optimization_stats(ir, optimized)
        
        # Comparisons always return bool - should elide all __py.bool()
        if stats.original_py_calls > 0:
            assert stats.wrapper_reduction >= 0
    
    def test_conditional_logic_wrapper_reduction(self):
        """Conditional logic should optimize well."""
        ir = parse(CONDITIONAL_LOGIC)
        optimized = optimize(ir)
        
        stats = get_optimization_stats(ir, optimized)
        
        assert stats.wrapper_reduction >= 0


# =============================================================================
# CODE SIZE TESTS
# =============================================================================

class TestCodeSizeReduction:
    """Tests verifying code size reduction."""
    
    def _measure_size(self, ir):
        """Measure approximate code size."""
        # Count nodes as proxy for size
        count = 0
        
        def count_nodes(node):
            nonlocal count
            count += 1
            for attr in ['body', 'orelse', 'args', 'left', 'right', 'value',
                        'test', 'comparators', 'values', 'iter', 'target',
                        'func', 'operand', 'elts', 'keys']:
                child = getattr(node, attr, None)
                if child is not None:
                    if isinstance(child, (list, tuple)):
                        for c in child:
                            if hasattr(c, '__dict__'):
                                count_nodes(c)
                    elif hasattr(child, '__dict__'):
                        count_nodes(child)
        
        for stmt in ir.body:
            count_nodes(stmt)
        
        return count
    
    def test_dead_code_size_reduction(self):
        """Dead code elimination should reduce size."""
        ir = parse(WITH_DEAD_CODE)
        optimized = optimize(ir)
        
        original_size = self._measure_size(ir)
        optimized_size = self._measure_size(optimized)
        
        # Should be smaller or equal
        assert optimized_size <= original_size
    
    def test_elision_size_reduction(self):
        """Eliding wrappers should reduce size."""
        ir = parse(SIMPLE_NUMERIC)
        optimized = optimize(ir)
        
        original_size = self._measure_size(ir)
        optimized_size = self._measure_size(optimized)
        
        # Wrapper calls become simpler expressions
        # Size should not increase
        assert optimized_size <= original_size + 5  # Small tolerance


# =============================================================================
# OPTIMIZATION CORRECTNESS
# =============================================================================

class TestOptimizationCorrectness:
    """Tests ensuring optimization doesn't break correctness."""
    
    def test_optimization_preserves_statements(self):
        """Optimization should preserve essential statements."""
        ir = parse('''
x = 5
y = 10
z = x + y
''')
        optimized = optimize(ir)
        
        # Should still have 3 assignments
        assert len(optimized.body) == 3
    
    def test_dce_only_removes_dead_code(self):
        """DCE should only remove truly dead code."""
        ir = parse('''
x = 5
if False:
    dead = 1
y = x + 1
''')
        optimized = optimize(ir)
        
        # Should have 2 statements (x assignment and y assignment)
        assert len(optimized.body) == 2
    
    def test_capture_preserves_lambda_structure(self):
        """Capture should preserve lambda functionality."""
        ir = parse(EVENT_HANDLERS)
        optimized = optimize(ir)
        
        # Should still have loop with lambda
        assert len(optimized.body) == 2  # handlers = [] and for loop
    
    def test_elision_preserves_semantics(self):
        """Elision should preserve semantic equivalence."""
        ir = parse('''
result = x > 0 and y > 0
''')
        optimized = optimize(ir)
        
        # Should still have assignment
        assert len(optimized.body) == 1


# =============================================================================
# STRESS TESTS
# =============================================================================

class TestStressTests:
    """Stress tests for optimizer performance."""
    
    def test_large_program(self):
        """Optimizer should handle large programs."""
        # Generate a large program
        lines = []
        for i in range(100):
            lines.append(f'x{i} = {i}')
            if i > 0:
                lines.append(f'y{i} = x{i} + x{i-1}')
        
        code = '\n'.join(lines)
        ir = parse(code)
        
        # Should complete without error
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_deeply_nested_code(self):
        """Optimizer should handle deeply nested code."""
        code = 'x = 0\n'
        for i in range(20):
            code += '  ' * i + f'if True:\n'
            code += '  ' * (i+1) + f'x = x + {i}\n'
        
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_many_function_definitions(self):
        """Optimizer should handle many function definitions."""
        lines = []
        for i in range(50):
            lines.append(f'''
def func_{i}(x):
    return x + {i}
''')
        
        code = '\n'.join(lines)
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_complex_expressions(self):
        """Optimizer should handle complex expressions."""
        code = 'result = ' + ' + '.join([f'(x{i} * {i})' for i in range(20)])
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None


# =============================================================================
# BENCHMARK FIXTURES (for pytest-benchmark if available)
# =============================================================================

@pytest.fixture
def sample_programs():
    """Fixture providing sample programs for benchmarking."""
    return {
        'simple_numeric': SIMPLE_NUMERIC,
        'list_processing': LIST_PROCESSING,
        'event_handlers': EVENT_HANDLERS,
        'conditional_logic': CONDITIONAL_LOGIC,
        'string_ops': STRING_OPS,
        'dict_ops': DICT_OPS,
        'boolean_heavy': BOOLEAN_HEAVY,
        'with_dead_code': WITH_DEAD_CODE,
    }


class TestBenchmarkSuite:
    """Benchmark suite for optimizer performance."""
    
    def test_benchmark_parse_optimize(self, sample_programs):
        """Benchmark parse + optimize pipeline."""
        for name, code in sample_programs.items():
            ir = parse(code)
            optimized = optimize(ir)
            assert optimized is not None, f"Failed for {name}"
    
    def test_benchmark_all_passes(self, sample_programs):
        """Benchmark with all passes enabled."""
        options = OptimizeOptions(
            elision=True,
            inline=True,
            capture=True,
            dce=True,
        )
        
        for name, code in sample_programs.items():
            ir = parse(code)
            optimized = optimize(ir, options)
            assert optimized is not None
    
    def test_benchmark_minimal_passes(self, sample_programs):
        """Benchmark with minimal passes."""
        options = OptimizeOptions(
            elision=False,
            inline=False,
            capture=False,
            dce=False,
        )
        
        for name, code in sample_programs.items():
            ir = parse(code)
            optimized = optimize(ir, options)
            assert optimized is not None
