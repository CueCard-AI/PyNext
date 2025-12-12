"""
PyNext Build - Parallel Compilation

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides multi-core compilation for faster builds. Uses ProcessPoolExecutor
to compile multiple islands in parallel across all CPU cores.

    from pynext.build.parallel import compile_parallel
    
    # Compile islands in parallel
    results = compile_parallel(islands, max_workers=8)

=============================================================================
WHY THIS EXISTS
=============================================================================

Single-threaded compilation:
    100 islands × 5ms = 500ms

Parallel compilation (8 cores):
    100 islands ÷ 8 cores × 5ms = ~62ms

That's an 8x speedup! On modern machines with 16+ cores, the
improvement is even better.

=============================================================================
IMPLEMENTATION NOTES
=============================================================================

We use ProcessPoolExecutor instead of ThreadPoolExecutor because:

1. Python has the GIL (Global Interpreter Lock)
2. Compilation is CPU-bound (parsing, AST manipulation)
3. Processes bypass the GIL and use true parallelism

Each worker process:
1. Receives an island to compile
2. Parses the source file
3. Generates JavaScript
4. Returns the result

The main process:
1. Distributes work to workers
2. Collects results as they complete
3. Handles any errors

=============================================================================
"""

from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Tuple
import os


__all__ = [
    "compile_parallel",
    "ParallelResult",
    "ParallelConfig",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ParallelConfig:
    """
    Configuration for parallel compilation.
    
    Attributes:
        max_workers: Maximum number of worker processes
        use_threads: Use threads instead of processes (faster for small batches)
        timeout: Timeout per file in seconds
        chunk_size: Files to batch per worker (1 = no batching)
    """
    max_workers: int = 0  # 0 = auto (CPU count)
    use_threads: bool = False
    timeout: float = 30.0
    chunk_size: int = 1
    
    def __post_init__(self):
        if self.max_workers <= 0:
            self.max_workers = os.cpu_count() or 4


@dataclass
class ParallelResult:
    """
    Result of parallel compilation.
    
    Attributes:
        success: True if all files compiled successfully
        results: List of (file_path, js, map, error) tuples
        duration_ms: Total time in milliseconds
        files_compiled: Number of files compiled
        errors: Number of files that failed
        workers_used: Number of parallel workers used
    """
    success: bool = True
    results: List[Tuple[str, str, str, Optional[str]]] = None
    duration_ms: float = 0.0
    files_compiled: int = 0
    errors_count: int = 0
    workers_used: int = 0
    
    def __post_init__(self):
        if self.results is None:
            self.results = []


# =============================================================================
# WORKER FUNCTION
# =============================================================================

def _compile_file_worker(file_path: str) -> Tuple[str, str, str, Optional[str]]:
    """
    Worker function to compile a single file.
    
    This runs in a separate process. It must be a module-level function
    (not a method or lambda) for ProcessPoolExecutor to work.
    
    Args:
        file_path: Path to the Python file to compile
    
    Returns:
        Tuple of (file_path, js, source_map, error)
    """
    try:
        from pynext.compiler import compile_file
        
        result = compile_file(file_path)
        
        if result.errors:
            error_msg = "; ".join(str(e) for e in result.errors)
            return (file_path, "", "", error_msg)
        
        return (file_path, result.js, result.map or "", None)
        
    except Exception as e:
        return (file_path, "", "", str(e))


def _compile_files_batch(file_paths: List[str]) -> List[Tuple[str, str, str, Optional[str]]]:
    """
    Worker function to compile a batch of files.
    
    Args:
        file_paths: List of file paths to compile
    
    Returns:
        List of (file_path, js, source_map, error) tuples
    """
    results = []
    for file_path in file_paths:
        results.append(_compile_file_worker(file_path))
    return results


# =============================================================================
# PUBLIC API
# =============================================================================

def compile_parallel(
    file_paths: List[str],
    config: Optional[ParallelConfig] = None,
    on_progress: Optional[Callable[[str, int, int], None]] = None,
) -> ParallelResult:
    """
    Compile multiple files in parallel.
    
    Uses ProcessPoolExecutor to leverage multiple CPU cores for faster
    compilation. Each file is compiled in a separate process.
    
    Args:
        file_paths: List of Python file paths to compile
        config: Parallel compilation configuration
        on_progress: Optional callback (file_path, completed, total)
    
    Returns:
        ParallelResult with all compilation results
    
    Example:
        # Compile 100 files in parallel
        files = ["counter.py", "todo.py", "auth.py", ...]
        result = compile_parallel(files)
        
        if result.success:
            for file_path, js, map, error in result.results:
                print(f"{file_path}: {len(js)} bytes")
        
        # With progress callback
        def on_progress(file, done, total):
            print(f"[{done}/{total}] Compiled {file}")
        
        result = compile_parallel(files, on_progress=on_progress)
    """
    start_time = time.perf_counter()
    
    config = config or ParallelConfig()
    result = ParallelResult()
    
    if not file_paths:
        return result
    
    # For small batches, use single-threaded compilation
    if len(file_paths) <= 2:
        for idx, file_path in enumerate(file_paths):
            compile_result = _compile_file_worker(file_path)
            result.results.append(compile_result)
            
            if on_progress:
                on_progress(file_path, idx + 1, len(file_paths))
            
            if compile_result[3] is not None:  # Has error
                result.errors_count += 1
        
        result.files_compiled = len(file_paths)
        result.workers_used = 1
        result.success = result.errors_count == 0
        result.duration_ms = (time.perf_counter() - start_time) * 1000
        return result
    
    # Choose executor type
    ExecutorClass = ThreadPoolExecutor if config.use_threads else ProcessPoolExecutor
    workers = min(config.max_workers, len(file_paths))
    
    # Submit jobs
    with ExecutorClass(max_workers=workers) as executor:
        if config.chunk_size > 1:
            # Batch files into chunks
            chunks = _chunk_list(file_paths, config.chunk_size)
            futures: Dict[Future, List[str]] = {
                executor.submit(_compile_files_batch, chunk): chunk
                for chunk in chunks
            }
            
            completed = 0
            for future in as_completed(futures.keys(), timeout=config.timeout):
                try:
                    batch_results = future.result()
                    for compile_result in batch_results:
                        result.results.append(compile_result)
                        completed += 1
                        
                        if on_progress:
                            on_progress(compile_result[0], completed, len(file_paths))
                        
                        if compile_result[3] is not None:
                            result.errors_count += 1
                            
                except Exception as e:
                    # Entire batch failed
                    for file_path in futures[future]:
                        result.results.append((file_path, "", "", str(e)))
                        result.errors_count += 1
        else:
            # One file per worker
            futures: Dict[Future, str] = {
                executor.submit(_compile_file_worker, fp): fp
                for fp in file_paths
            }
            
            completed = 0
            for future in as_completed(futures.keys(), timeout=config.timeout):
                file_path = futures[future]
                completed += 1
                
                try:
                    compile_result = future.result()
                    result.results.append(compile_result)
                    
                    if on_progress:
                        on_progress(file_path, completed, len(file_paths))
                    
                    if compile_result[3] is not None:
                        result.errors_count += 1
                        
                except Exception as e:
                    result.results.append((file_path, "", "", str(e)))
                    result.errors_count += 1
    
    result.files_compiled = len(file_paths)
    result.workers_used = workers
    result.success = result.errors_count == 0
    result.duration_ms = (time.perf_counter() - start_time) * 1000
    
    return result


def _chunk_list(items: List[str], chunk_size: int) -> List[List[str]]:
    """Split a list into chunks of the specified size."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_optimal_workers(file_count: int) -> int:
    """
    Calculate optimal number of workers based on file count.
    
    Rules:
    - 1-2 files: 1 worker (overhead not worth it)
    - 3-8 files: min(file_count, 4)
    - 9+ files: min(file_count, CPU count)
    
    Args:
        file_count: Number of files to compile
    
    Returns:
        Optimal number of workers
    """
    cpu_count = os.cpu_count() or 4
    
    if file_count <= 2:
        return 1
    elif file_count <= 8:
        return min(file_count, 4)
    else:
        return min(file_count, cpu_count)


def estimate_compile_time(file_count: int, avg_file_size: int = 1000) -> float:
    """
    Estimate compilation time in milliseconds.
    
    Args:
        file_count: Number of files to compile
        avg_file_size: Average file size in lines
    
    Returns:
        Estimated time in milliseconds
    """
    # Base: ~5ms per file on modern hardware
    base_time = 5.0
    
    # Larger files take longer
    size_factor = avg_file_size / 1000
    
    # Parallel speedup
    workers = get_optimal_workers(file_count)
    parallel_time = (file_count * base_time * size_factor) / workers
    
    # Add overhead for process spawning (~10ms per process)
    overhead = workers * 10 if workers > 1 else 0
    
    return parallel_time + overhead

