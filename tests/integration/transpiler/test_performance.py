"""
Phase 33.1: Performance Benchmark Tests

Compare Python vs JavaScript execution performance for transpiled code.
"""

import pytest
import sys
import time
import statistics
from pathlib import Path
from pynext.transpiler import transpile

# Import executor
sys.path.insert(0, str(Path(__file__).parent))
from test_python_js_equivalence import PythonJSExecutor


@pytest.fixture
def executor():
    """Create a Python-JS executor."""
    exec = PythonJSExecutor()
    yield exec
    import shutil
    shutil.rmtree(exec.temp_dir, ignore_errors=True)


class TestPerformance:
    """Performance benchmarks comparing Python vs JavaScript."""
    
    def test_list_comprehension_performance(self, executor):
        """Benchmark list comprehension performance"""
        python_code = """
result = [x*x for x in range(10000)]
"""
        js_code = transpile(python_code)
        
        # Python timing
        py_times = []
        for _ in range(5):
            start = time.perf_counter()
            executor.execute_python(python_code)
            py_times.append(time.perf_counter() - start)
        
        # JavaScript timing
        js_times = []
        for _ in range(5):
            start = time.perf_counter()
            executor.execute_javascript(js_code)
            js_times.append(time.perf_counter() - start)
        
        py_avg = statistics.mean(py_times)
        js_avg = statistics.mean(js_times)
        
        print(f"\nList Comprehension (10000 items):")
        print(f"  Python: {py_avg*1000:.2f}ms avg")
        print(f"  JavaScript: {js_avg*1000:.2f}ms avg")
        print(f"  Ratio: {js_avg/py_avg:.2f}x")
        
        # Both should complete reasonably fast
        assert py_avg < 1.0  # Python should be < 1 second
        assert js_avg < 1.0  # JS should be < 1 second
    
    def test_function_call_performance(self, executor):
        """Benchmark function call performance"""
        python_code = """
def add(a, b):
    return a + b

total = 0
for i in range(100000):
    total += add(i, i+1)
print(total)
"""
        js_code = transpile(python_code)
        
        # Python timing
        py_times = []
        for _ in range(3):
            start = time.perf_counter()
            executor.execute_python(python_code)
            py_times.append(time.perf_counter() - start)
        
        # JavaScript timing
        js_times = []
        for _ in range(3):
            start = time.perf_counter()
            executor.execute_javascript(js_code)
            js_times.append(time.perf_counter() - start)
        
        py_avg = statistics.mean(py_times)
        js_avg = statistics.mean(js_times)
        
        print(f"\nFunction Calls (100000 iterations):")
        print(f"  Python: {py_avg*1000:.2f}ms avg")
        print(f"  JavaScript: {js_avg*1000:.2f}ms avg")
        print(f"  Ratio: {js_avg/py_avg:.2f}x")
        
        assert py_avg < 2.0
        assert js_avg < 2.0
    
    def test_class_instantiation_performance(self, executor):
        """Benchmark class instantiation performance"""
        python_code = """
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

points = []
for i in range(10000):
    points.append(Point(i, i+1))
print(len(points))
"""
        js_code = transpile(python_code)
        
        # Python timing
        py_times = []
        for _ in range(3):
            start = time.perf_counter()
            executor.execute_python(python_code)
            py_times.append(time.perf_counter() - start)
        
        # JavaScript timing
        js_times = []
        for _ in range(3):
            start = time.perf_counter()
            executor.execute_javascript(js_code)
            js_times.append(time.perf_counter() - start)
        
        py_avg = statistics.mean(py_times)
        js_avg = statistics.mean(js_times)
        
        print(f"\nClass Instantiation (10000 instances):")
        print(f"  Python: {py_avg*1000:.2f}ms avg")
        print(f"  JavaScript: {js_avg*1000:.2f}ms avg")
        print(f"  Ratio: {js_avg/py_avg:.2f}x")
        
        assert py_avg < 2.0
        assert js_avg < 2.0
    
    def test_nested_loops_performance(self, executor):
        """Benchmark nested loops performance"""
        python_code = """
total = 0
for i in range(100):
    for j in range(100):
        total += i * j
print(total)
"""
        js_code = transpile(python_code)
        
        # Python timing
        py_times = []
        for _ in range(3):
            start = time.perf_counter()
            executor.execute_python(python_code)
            py_times.append(time.perf_counter() - start)
        
        # JavaScript timing
        js_times = []
        for _ in range(3):
            start = time.perf_counter()
            executor.execute_javascript(js_code)
            js_times.append(time.perf_counter() - start)
        
        py_avg = statistics.mean(py_times)
        js_avg = statistics.mean(js_times)
        
        print(f"\nNested Loops (100x100):")
        print(f"  Python: {py_avg*1000:.2f}ms avg")
        print(f"  JavaScript: {js_avg*1000:.2f}ms avg")
        print(f"  Ratio: {js_avg/py_avg:.2f}x")
        
        assert py_avg < 1.0
        assert js_avg < 1.0

