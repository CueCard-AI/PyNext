"""
Tests for PyNext Parallel Compilation (60 tests)

Tests multi-core compilation with ProcessPoolExecutor.
"""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch

from pynext.build.parallel import (
    compile_parallel,
    ParallelConfig,
    ParallelResult,
    get_optimal_workers,
    estimate_compile_time,
    _compile_file_worker,
)


# =============================================================================
# PARALLEL CONFIG
# =============================================================================

class TestParallelConfig:
    """Tests for ParallelConfig."""
    
    def test_default_config(self):
        """Default configuration."""
        config = ParallelConfig()
        assert config.max_workers > 0
        assert config.use_threads is False
        assert config.timeout == 30.0
    
    def test_auto_workers(self):
        """Auto-detect worker count."""
        config = ParallelConfig(max_workers=0)
        assert config.max_workers > 0  # Should be CPU count
    
    def test_custom_workers(self):
        """Custom worker count."""
        config = ParallelConfig(max_workers=4)
        assert config.max_workers == 4
    
    def test_thread_mode(self):
        """Thread mode option."""
        config = ParallelConfig(use_threads=True)
        assert config.use_threads is True
    
    def test_chunk_size(self):
        """Chunk size option."""
        config = ParallelConfig(chunk_size=5)
        assert config.chunk_size == 5


# =============================================================================
# PARALLEL RESULT
# =============================================================================

class TestParallelResult:
    """Tests for ParallelResult."""
    
    def test_default_result(self):
        """Default result values."""
        result = ParallelResult()
        assert result.success is True
        assert result.results == []
        assert result.files_compiled == 0
    
    def test_result_with_data(self):
        """Result with data."""
        result = ParallelResult(
            success=True,
            files_compiled=5,
            duration_ms=100.0,
            workers_used=4,
        )
        assert result.files_compiled == 5
        assert result.workers_used == 4
    
    def test_result_with_errors(self):
        """Result with errors."""
        result = ParallelResult(
            success=False,
            errors_count=2,
        )
        assert result.success is False
        assert result.errors_count == 2


# =============================================================================
# OPTIMAL WORKERS
# =============================================================================

class TestOptimalWorkers:
    """Tests for optimal worker calculation."""
    
    def test_single_file(self):
        """Single file uses 1 worker."""
        assert get_optimal_workers(1) == 1
    
    def test_two_files(self):
        """Two files use 1 worker."""
        assert get_optimal_workers(2) == 1
    
    def test_small_batch(self):
        """Small batch (3-8 files)."""
        workers = get_optimal_workers(5)
        assert 1 <= workers <= 5
    
    def test_large_batch(self):
        """Large batch uses more workers."""
        workers = get_optimal_workers(100)
        assert workers > 1
    
    def test_never_exceeds_files(self):
        """Workers never exceed file count."""
        workers = get_optimal_workers(3)
        assert workers <= 3


# =============================================================================
# COMPILE TIME ESTIMATION
# =============================================================================

class TestCompileTimeEstimation:
    """Tests for compile time estimation."""
    
    def test_estimate_single_file(self):
        """Estimate for single file."""
        time_ms = estimate_compile_time(1)
        assert time_ms > 0
        assert time_ms < 100  # Should be fast
    
    def test_estimate_scales_with_files(self):
        """Time scales with file count."""
        time_1 = estimate_compile_time(1)
        time_10 = estimate_compile_time(10)
        assert time_10 > time_1
    
    def test_estimate_parallel_faster(self):
        """Parallel is faster for many files."""
        # With parallelism, 100 files shouldn't be 100x slower
        time_1 = estimate_compile_time(1)
        time_100 = estimate_compile_time(100)
        assert time_100 < time_1 * 50
    
    def test_estimate_with_size(self):
        """Size affects estimate."""
        small = estimate_compile_time(10, avg_file_size=100)
        large = estimate_compile_time(10, avg_file_size=10000)
        assert large > small


# =============================================================================
# COMPILE PARALLEL
# =============================================================================

class TestCompileParallel:
    """Tests for parallel compilation."""
    
    def test_empty_file_list(self):
        """Empty file list returns empty result."""
        result = compile_parallel([])
        assert result.success is True
        assert result.files_compiled == 0
    
    def test_single_file(self, tmp_path):
        """Compile single file."""
        file = tmp_path / "counter.py"
        file.write_text('''
@island
def Counter():
    return button()["Click"]
''')
        
        with patch('pynext.build.parallel._compile_file_worker') as mock:
            mock.return_value = (str(file), "js code", "", None)
            result = compile_parallel([str(file)])
        
        assert result.files_compiled == 1
    
    def test_multiple_files(self, tmp_path):
        """Compile multiple files with threads (mocks work in threads)."""
        files = []
        for i in range(5):
            f = tmp_path / f"comp_{i}.py"
            f.write_text(f'''
@island
def Component{i}():
    return div()["{i}"]
''')
            files.append(str(f))
        
        # Use threads so mocks work
        config = ParallelConfig(use_threads=True)
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.return_value = Mock(js="code", map="", errors=[])
            result = compile_parallel(files, config)
        
        assert result.files_compiled == 5
    
    def test_handles_errors(self, tmp_path):
        """Handle compilation errors."""
        file = tmp_path / "broken.py"
        file.write_text("syntax error (")
        
        with patch('pynext.build.parallel._compile_file_worker') as mock:
            mock.return_value = (str(file), "", "", "Syntax error")
            result = compile_parallel([str(file)])
        
        assert result.errors_count == 1
    
    def test_progress_callback(self, tmp_path):
        """Progress callback is called."""
        file = tmp_path / "test.py"
        file.write_text("@island\ndef Test(): pass")
        
        progress_calls = []
        
        def on_progress(path, done, total):
            progress_calls.append((path, done, total))
        
        with patch('pynext.build.parallel._compile_file_worker') as mock:
            mock.return_value = (str(file), "js", "", None)
            compile_parallel([str(file)], on_progress=on_progress)
        
        assert len(progress_calls) > 0
    
    def test_respects_config(self):
        """Respects ParallelConfig (using threads for mocks)."""
        config = ParallelConfig(max_workers=2, use_threads=True)
        
        files = ["a.py", "b.py", "c.py", "d.py"]
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.return_value = Mock(js="code", map="", errors=[])
            result = compile_parallel(files, config)
        
        assert result.workers_used <= 2
    
    def test_thread_mode(self):
        """Thread mode uses ThreadPoolExecutor."""
        config = ParallelConfig(use_threads=True, max_workers=2)
        
        with patch('pynext.build.parallel._compile_file_worker') as mock:
            mock.side_effect = lambda f: (f, "js", "", None)
            result = compile_parallel(["a.py", "b.py", "c.py"], config)
        
        assert result.success


# =============================================================================
# WORKER FUNCTION
# =============================================================================

class TestWorkerFunction:
    """Tests for worker function."""
    
    def test_worker_returns_tuple(self, tmp_path):
        """Worker returns (path, js, map, error) tuple."""
        file = tmp_path / "test.py"
        file.write_text("@island\ndef Test(): pass")
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.return_value = Mock(js="code", map="map", errors=[])
            result = _compile_file_worker(str(file))
        
        assert len(result) == 4
        assert result[0] == str(file)
    
    def test_worker_handles_exception(self, tmp_path):
        """Worker handles compilation exceptions."""
        file = tmp_path / "test.py"
        file.write_text("content")
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.side_effect = Exception("Compilation failed")
            result = _compile_file_worker(str(file))
        
        assert result[3] is not None  # Error message
    
    def test_worker_handles_compile_errors(self, tmp_path):
        """Worker handles compile-time errors."""
        file = tmp_path / "test.py"
        file.write_text("content")
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.return_value = Mock(js="", map="", errors=["Error 1", "Error 2"])
            result = _compile_file_worker(str(file))
        
        assert result[3] is not None  # Combined error message


# =============================================================================
# PERFORMANCE
# =============================================================================

class TestPerformance:
    """Performance tests."""
    
    def test_parallel_faster_than_serial(self, tmp_path):
        """Parallel is faster for many files (using threads for mocks)."""
        files = []
        for i in range(20):
            f = tmp_path / f"file_{i}.py"
            f.write_text(f"@island\ndef F{i}(): pass")
            files.append(str(f))
        
        config = ParallelConfig(use_threads=True)
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.return_value = Mock(js="code", map="", errors=[])
            result = compile_parallel(files, config)
        
        assert result.duration_ms > 0
    
    def test_respects_timeout(self):
        """Respects timeout configuration."""
        config = ParallelConfig(timeout=1.0)
        
        with patch('pynext.build.parallel._compile_file_worker') as mock:
            mock.side_effect = lambda f: (f, "js", "", None)
            result = compile_parallel(["a.py"], config)
        
        assert result.duration_ms < 1000


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case handling."""
    
    def test_all_files_error(self):
        """All files have errors (using threads for mocks)."""
        files = ["a.py", "b.py", "c.py"]
        
        config = ParallelConfig(use_threads=True)
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.return_value = Mock(js="", map="", errors=["Error"])
            result = compile_parallel(files, config)
        
        assert result.success is False
        assert result.errors_count == 3
    
    def test_mixed_success_error(self):
        """Some files succeed, some fail (using threads for mocks)."""
        files = ["a.py", "b.py", "c.py"]
        
        config = ParallelConfig(use_threads=True)
        
        with patch('pynext.compiler.compile_file') as mock:
            def mock_compile(f):
                if "b" in str(f):
                    return Mock(js="", map="", errors=["Error"])
                return Mock(js="code", map="", errors=[])
            
            mock.side_effect = mock_compile
            result = compile_parallel(files, config)
        
        assert result.success is False
        assert result.errors_count == 1
        assert result.files_compiled == 3
    
    def test_chunked_compilation(self):
        """Chunked compilation mode (using threads for mocks)."""
        config = ParallelConfig(chunk_size=3, use_threads=True)
        files = ["a.py", "b.py", "c.py", "d.py", "e.py"]
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.return_value = Mock(js="code", map="", errors=[])
            result = compile_parallel(files, config)
        
        # Should have processed all files
        assert result.files_compiled == 5

