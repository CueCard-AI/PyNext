"""
PyNext Testing - Performance Benchmarks

Measure and assert component performance.
Catch performance regressions before they ship.

Example:
    from pynext.testing import benchmark, assert_render_time
    
    @benchmark(iterations=100)
    def test_list_performance():
        result = render(ProductList, items=range(1000))
        assert_render_time(result, max_ms=50)

Why Performance Testing:
    - Catch slow renders early
    - Track performance over time
    - Prevent regressions
    - Document performance characteristics
"""

from __future__ import annotations

import gc
import statistics
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar

from pynext.testing.render import RenderResult


T = TypeVar("T")


# =============================================================================
# Benchmark Results
# =============================================================================

@dataclass
class BenchmarkResult:
    """
    Results of a performance benchmark.
    
    Contains timing statistics for detailed analysis.
    """
    name: str
    iterations: int
    
    # Timing in milliseconds
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    std_dev_ms: float
    
    # Individual timings
    timings: List[float]
    
    def __str__(self) -> str:
        return (
            f"Benchmark: {self.name}\n"
            f"  Iterations: {self.iterations}\n"
            f"  Mean:   {self.mean_ms:.2f}ms\n"
            f"  Median: {self.median_ms:.2f}ms\n"
            f"  Min:    {self.min_ms:.2f}ms\n"
            f"  Max:    {self.max_ms:.2f}ms\n"
            f"  StdDev: {self.std_dev_ms:.2f}ms"
        )
    
    def percentile(self, p: float) -> float:
        """Get the p-th percentile timing."""
        sorted_timings = sorted(self.timings)
        index = int(len(sorted_timings) * p / 100)
        return sorted_timings[min(index, len(sorted_timings) - 1)]
    
    @property
    def p95(self) -> float:
        """95th percentile timing."""
        return self.percentile(95)
    
    @property
    def p99(self) -> float:
        """99th percentile timing."""
        return self.percentile(99)


# =============================================================================
# Benchmark Decorator
# =============================================================================

def benchmark(
    iterations: int = 100,
    warmup: int = 10,
    name: Optional[str] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to benchmark a test function.
    
    Runs the test multiple times and collects timing statistics.
    
    Args:
        iterations: Number of timed iterations
        warmup: Number of warmup iterations (not timed)
        name: Name for the benchmark (default: function name)
        
    Example:
        @benchmark(iterations=100)
        def test_render_speed():
            result = render(BigComponent)
            assert result.render_time_ms < 50
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            benchmark_name = name or func.__name__
            timings: List[float] = []
            
            # Warmup runs (not timed)
            for _ in range(warmup):
                func(*args, **kwargs)
            
            # Force garbage collection
            gc.collect()
            
            # Timed runs
            for _ in range(iterations):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                end = time.perf_counter()
                timings.append((end - start) * 1000)  # Convert to ms
            
            # Calculate statistics
            bench_result = BenchmarkResult(
                name=benchmark_name,
                iterations=iterations,
                mean_ms=statistics.mean(timings),
                median_ms=statistics.median(timings),
                min_ms=min(timings),
                max_ms=max(timings),
                std_dev_ms=statistics.stdev(timings) if len(timings) > 1 else 0,
                timings=timings,
            )
            
            # Store result on function for later access
            wrapper._benchmark_result = bench_result
            
            # Print summary
            print(f"\n{bench_result}")
            
            return result
        
        wrapper._benchmark_result = None
        return wrapper
    
    return decorator


# =============================================================================
# Timing Utilities
# =============================================================================

def measure_render_time(
    component: Any,
    iterations: int = 10,
    *args,
    **kwargs,
) -> BenchmarkResult:
    """
    Measure component render time.
    
    Args:
        component: Component to render
        iterations: Number of render iterations
        *args, **kwargs: Arguments for the component
        
    Returns:
        BenchmarkResult with timing statistics
        
    Example:
        result = measure_render_time(
            ProductList,
            iterations=50,
            items=products
        )
        print(f"Median render: {result.median_ms}ms")
    """
    from pynext.testing.render import render
    
    timings: List[float] = []
    
    # Warmup
    for _ in range(3):
        render(component, *args, **kwargs)
    
    gc.collect()
    
    # Timed runs
    for _ in range(iterations):
        result = render(component, *args, **kwargs)
        timings.append(result.render_time_ms)
    
    return BenchmarkResult(
        name=f"render({getattr(component, '__name__', str(component))})",
        iterations=iterations,
        mean_ms=statistics.mean(timings),
        median_ms=statistics.median(timings),
        min_ms=min(timings),
        max_ms=max(timings),
        std_dev_ms=statistics.stdev(timings) if len(timings) > 1 else 0,
        timings=timings,
    )


class Timer:
    """
    Context manager for timing code blocks.
    
    Example:
        with Timer() as t:
            result = render(BigComponent)
        
        print(f"Took {t.ms}ms")
    """
    
    def __init__(self):
        self.start_time: float = 0
        self.end_time: float = 0
    
    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args) -> None:
        self.end_time = time.perf_counter()
    
    @property
    def seconds(self) -> float:
        """Elapsed time in seconds."""
        return self.end_time - self.start_time
    
    @property
    def ms(self) -> float:
        """Elapsed time in milliseconds."""
        return self.seconds * 1000


def time_function(func: Callable[..., T], *args, **kwargs) -> tuple[T, float]:
    """
    Time a single function call.
    
    Args:
        func: Function to time
        *args, **kwargs: Arguments for the function
        
    Returns:
        Tuple of (result, time_in_ms)
        
    Example:
        result, ms = time_function(render, Button, label="Click")
        print(f"Render took {ms}ms")
    """
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    
    return result, (end - start) * 1000


# =============================================================================
# Performance Assertions
# =============================================================================

def assert_performance(
    result: BenchmarkResult,
    max_mean_ms: Optional[float] = None,
    max_median_ms: Optional[float] = None,
    max_p95_ms: Optional[float] = None,
    max_p99_ms: Optional[float] = None,
) -> None:
    """
    Assert benchmark results meet performance requirements.
    
    Args:
        result: BenchmarkResult to check
        max_mean_ms: Maximum allowed mean time
        max_median_ms: Maximum allowed median time
        max_p95_ms: Maximum allowed 95th percentile
        max_p99_ms: Maximum allowed 99th percentile
        
    Example:
        result = measure_render_time(MyComponent, iterations=100)
        assert_performance(
            result,
            max_median_ms=20,
            max_p95_ms=50
        )
    """
    failures = []
    
    if max_mean_ms and result.mean_ms > max_mean_ms:
        failures.append(f"Mean {result.mean_ms:.2f}ms > {max_mean_ms}ms")
    
    if max_median_ms and result.median_ms > max_median_ms:
        failures.append(f"Median {result.median_ms:.2f}ms > {max_median_ms}ms")
    
    if max_p95_ms and result.p95 > max_p95_ms:
        failures.append(f"P95 {result.p95:.2f}ms > {max_p95_ms}ms")
    
    if max_p99_ms and result.p99 > max_p99_ms:
        failures.append(f"P99 {result.p99:.2f}ms > {max_p99_ms}ms")
    
    if failures:
        raise AssertionError(
            f"Performance requirements not met:\n"
            f"  {chr(10).join(failures)}\n\n"
            f"{result}"
        )


def assert_faster_than(
    result: BenchmarkResult,
    baseline: BenchmarkResult,
    tolerance: float = 0.1,
) -> None:
    """
    Assert that benchmark is faster than baseline.
    
    Args:
        result: Current benchmark result
        baseline: Baseline to compare against
        tolerance: Allowed slowdown (0.1 = 10%)
        
    Example:
        baseline = measure_render_time(OldComponent)
        new_result = measure_render_time(NewComponent)
        assert_faster_than(new_result, baseline)
    """
    max_allowed = baseline.median_ms * (1 + tolerance)
    
    if result.median_ms > max_allowed:
        raise AssertionError(
            f"Performance regression detected!\n"
            f"  Baseline median: {baseline.median_ms:.2f}ms\n"
            f"  Current median:  {result.median_ms:.2f}ms\n"
            f"  Max allowed:     {max_allowed:.2f}ms (tolerance: {tolerance:.0%})"
        )


# =============================================================================
# Memory Benchmarks
# =============================================================================

def measure_memory(
    func: Callable[..., T],
    *args,
    **kwargs,
) -> tuple[T, int]:
    """
    Measure memory usage of a function.
    
    Args:
        func: Function to measure
        *args, **kwargs: Arguments for the function
        
    Returns:
        Tuple of (result, memory_bytes)
        
    Example:
        result, memory = measure_memory(render, BigList, items=range(10000))
        assert memory < 10 * 1024 * 1024  # Less than 10MB
    """
    import tracemalloc
    
    tracemalloc.start()
    result = func(*args, **kwargs)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return result, peak


def assert_memory_limit(
    func: Callable[..., T],
    max_bytes: int,
    *args,
    **kwargs,
) -> T:
    """
    Assert function uses less than specified memory.
    
    Args:
        func: Function to test
        max_bytes: Maximum allowed memory in bytes
        *args, **kwargs: Arguments for the function
        
    Returns:
        Result of the function
        
    Example:
        result = assert_memory_limit(
            render, 
            5 * 1024 * 1024,  # 5MB
            BigComponent
        )
    """
    result, memory = measure_memory(func, *args, **kwargs)
    
    if memory > max_bytes:
        raise AssertionError(
            f"Memory limit exceeded\n"
            f"  Used:    {memory / 1024 / 1024:.2f}MB\n"
            f"  Allowed: {max_bytes / 1024 / 1024:.2f}MB"
        )
    
    return result

