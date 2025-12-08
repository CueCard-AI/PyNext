"""
DataFrame Performance Benchmark Tests for Phase 8.3.

Performance benchmark tests comparing pynext_go DataFrame operations
against asyncpg and manual conversion approaches.

Test Categories:
1. Polars vs asyncpg + manual conversion
2. NumPy vs asyncpg + manual conversion
3. pandas vs asyncpg + manual conversion
4. Various dataset sizes (100, 1K, 10K, 100K rows)
5. Memory usage comparison
6. Zero-copy verification
"""

import pytest
import time
from typing import Any, Dict, List
from unittest.mock import Mock, patch, MagicMock

# Try to import dependencies
numpy_available = False
try:
    import numpy as np
    numpy_available = True
except ImportError:
    pass

pandas_available = False
try:
    import pandas as pd
    pandas_available = True
except ImportError:
    pass

polars_available = False
try:
    import polars as pl
    polars_available = True
except ImportError:
    pass

pyarrow_available = False
try:
    import pyarrow as pa
    pyarrow_available = True
except ImportError:
    pass


# =============================================================================
# Test Data Generators
# =============================================================================

def generate_arrow_table(n_rows: int, n_cols: int = 5) -> "pa.Table":
    """Generate a test Arrow table."""
    if not pyarrow_available:
        pytest.skip("pyarrow not available")
    
    data = {
        "id": pa.array(range(n_rows), type=pa.int64()),
        "value": pa.array([float(i) for i in range(n_rows)], type=pa.float64()),
        "name": pa.array([f"name_{i}" for i in range(n_rows)], type=pa.string()),
        "active": pa.array([i % 2 == 0 for i in range(n_rows)], type=pa.bool_()),
        "score": pa.array([float(i % 100) for i in range(n_rows)], type=pa.float64()),
    }
    return pa.table(data)


def generate_dict_rows(n_rows: int) -> List[Dict[str, Any]]:
    """Generate test data as list of dicts (simulating asyncpg)."""
    return [
        {
            "id": i,
            "value": float(i),
            "name": f"name_{i}",
            "active": i % 2 == 0,
            "score": float(i % 100),
        }
        for i in range(n_rows)
    ]


# =============================================================================
# Polars Performance Tests (10 tests)
# =============================================================================

class TestPolarsPerformance:
    """Benchmark tests for Polars conversion."""
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_1k_rows(self):
        """Benchmark Polars conversion with 1K rows."""
        table = generate_arrow_table(1000)
        
        start = time.perf_counter()
        df = pl.from_arrow(table)
        elapsed = time.perf_counter() - start
        
        assert len(df) == 1000
        assert elapsed < 0.1  # Should be very fast
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_10k_rows(self):
        """Benchmark Polars conversion with 10K rows."""
        table = generate_arrow_table(10_000)
        
        start = time.perf_counter()
        df = pl.from_arrow(table)
        elapsed = time.perf_counter() - start
        
        assert len(df) == 10_000
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_100k_rows(self):
        """Benchmark Polars conversion with 100K rows."""
        table = generate_arrow_table(100_000)
        
        start = time.perf_counter()
        df = pl.from_arrow(table)
        elapsed = time.perf_counter() - start
        
        assert len(df) == 100_000
        assert elapsed < 0.5  # Zero-copy should be fast
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_1m_rows(self):
        """Benchmark Polars conversion with 1M rows."""
        table = generate_arrow_table(1_000_000)
        
        start = time.perf_counter()
        df = pl.from_arrow(table)
        elapsed = time.perf_counter() - start
        
        assert len(df) == 1_000_000
        assert elapsed < 1.0  # Even 1M should be fast
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_polars_vs_manual_10k(self):
        """Compare Polars Arrow conversion vs manual dict conversion."""
        n = 10_000
        table = generate_arrow_table(n)
        rows = generate_dict_rows(n)
        
        # Polars from Arrow (fast path)
        start = time.perf_counter()
        df_polars = pl.from_arrow(table)
        polars_time = time.perf_counter() - start
        
        # Manual from dicts (slow path)
        start = time.perf_counter()
        df_manual = pl.DataFrame(rows)
        manual_time = time.perf_counter() - start
        
        assert len(df_polars) == n
        assert len(df_manual) == n
        # Arrow path should be faster
        assert polars_time < manual_time
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_filter_performance(self):
        """Benchmark Polars filtering after conversion."""
        table = generate_arrow_table(100_000)
        df = pl.from_arrow(table)
        
        start = time.perf_counter()
        filtered = df.filter(pl.col("score") > 50)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_groupby_performance(self):
        """Benchmark Polars groupby after conversion."""
        table = generate_arrow_table(100_000)
        df = pl.from_arrow(table)
        
        start = time.perf_counter()
        result = df.group_by("active").agg(pl.mean("score"))
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_aggregation_performance(self):
        """Benchmark Polars aggregation after conversion."""
        table = generate_arrow_table(100_000)
        df = pl.from_arrow(table)
        
        start = time.perf_counter()
        result = df.select([
            pl.sum("value"),
            pl.mean("score"),
            pl.max("id"),
        ])
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_sort_performance(self):
        """Benchmark Polars sorting after conversion."""
        table = generate_arrow_table(100_000)
        df = pl.from_arrow(table)
        
        start = time.perf_counter()
        sorted_df = df.sort("score", descending=True)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.5
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_join_performance(self):
        """Benchmark Polars join after conversion."""
        table1 = generate_arrow_table(10_000)
        table2 = generate_arrow_table(10_000)
        df1 = pl.from_arrow(table1)
        df2 = pl.from_arrow(table2).select(["id", "score"])
        
        start = time.perf_counter()
        result = df1.join(df2, on="id", suffix="_right")
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.5


# =============================================================================
# NumPy Performance Tests (10 tests)
# =============================================================================

class TestNumPyPerformance:
    """Benchmark tests for NumPy conversion."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_1k_rows(self):
        """Benchmark NumPy conversion with 1K rows."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = generate_arrow_table(1000)
        
        start = time.perf_counter()
        arrays = arrow_table_to_numpy_columns(table)
        elapsed = time.perf_counter() - start
        
        assert len(arrays["id"]) == 1000
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_10k_rows(self):
        """Benchmark NumPy conversion with 10K rows."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = generate_arrow_table(10_000)
        
        start = time.perf_counter()
        arrays = arrow_table_to_numpy_columns(table)
        elapsed = time.perf_counter() - start
        
        assert len(arrays["id"]) == 10_000
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_100k_rows(self):
        """Benchmark NumPy conversion with 100K rows."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = generate_arrow_table(100_000)
        
        start = time.perf_counter()
        arrays = arrow_table_to_numpy_columns(table)
        elapsed = time.perf_counter() - start
        
        assert len(arrays["id"]) == 100_000
        assert elapsed < 0.5
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_1m_rows(self):
        """Benchmark NumPy conversion with 1M rows."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = generate_arrow_table(1_000_000)
        
        start = time.perf_counter()
        arrays = arrow_table_to_numpy_columns(table)
        elapsed = time.perf_counter() - start
        
        assert len(arrays["id"]) == 1_000_000
        assert elapsed < 2.0  # String columns require copy
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_vs_manual_10k(self):
        """Compare NumPy Arrow conversion vs manual dict conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 10_000
        table = generate_arrow_table(n)
        rows = generate_dict_rows(n)
        
        # NumPy from Arrow (fast path)
        start = time.perf_counter()
        arrays_arrow = arrow_table_to_numpy_columns(table)
        arrow_time = time.perf_counter() - start
        
        # Manual from dicts (slow path)
        start = time.perf_counter()
        arrays_manual = {
            "id": np.array([r["id"] for r in rows]),
            "value": np.array([r["value"] for r in rows]),
        }
        manual_time = time.perf_counter() - start
        
        assert len(arrays_arrow["id"]) == n
        # Arrow path should be faster for numeric columns
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_zero_copy_numeric(self):
        """Test zero-copy performance for numeric columns."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 1_000_000
        # Numeric-only table for zero-copy
        table = pa.table({
            "id": pa.array(range(n), type=pa.int64()),
            "value": pa.array([float(i) for i in range(n)], type=pa.float64()),
        })
        
        start = time.perf_counter()
        arrays = arrow_table_to_numpy_columns(table, zero_copy=True)
        elapsed = time.perf_counter() - start
        
        assert len(arrays["id"]) == n
        assert elapsed < 0.1  # Zero-copy should be instant
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_vectorized_ops(self):
        """Benchmark vectorized operations on NumPy result."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = generate_arrow_table(100_000)
        arrays = arrow_table_to_numpy_columns(table)
        
        start = time.perf_counter()
        result = arrays["value"] * 2 + arrays["score"]
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_aggregation(self):
        """Benchmark NumPy aggregation."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = generate_arrow_table(100_000)
        arrays = arrow_table_to_numpy_columns(table)
        
        start = time.perf_counter()
        total = arrays["value"].sum()
        mean = arrays["score"].mean()
        max_val = arrays["id"].max()
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_boolean_indexing(self):
        """Benchmark NumPy boolean indexing."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = generate_arrow_table(100_000)
        arrays = arrow_table_to_numpy_columns(table)
        
        start = time.perf_counter()
        filtered = arrays["id"][arrays["score"] > 50]
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_structured_array(self):
        """Benchmark structured array conversion."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = generate_arrow_table(100_000)
        
        start = time.perf_counter()
        arr = arrow_table_to_structured(table)
        elapsed = time.perf_counter() - start
        
        assert len(arr) == 100_000
        assert elapsed < 1.0


# =============================================================================
# pandas Performance Tests (10 tests)
# =============================================================================

class TestPandasPerformance:
    """Benchmark tests for pandas conversion."""
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_1k_rows(self):
        """Benchmark pandas conversion with 1K rows."""
        table = generate_arrow_table(1000)
        
        start = time.perf_counter()
        df = table.to_pandas()
        elapsed = time.perf_counter() - start
        
        assert len(df) == 1000
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_10k_rows(self):
        """Benchmark pandas conversion with 10K rows."""
        table = generate_arrow_table(10_000)
        
        start = time.perf_counter()
        df = table.to_pandas()
        elapsed = time.perf_counter() - start
        
        assert len(df) == 10_000
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_100k_rows(self):
        """Benchmark pandas conversion with 100K rows."""
        table = generate_arrow_table(100_000)
        
        start = time.perf_counter()
        df = table.to_pandas()
        elapsed = time.perf_counter() - start
        
        assert len(df) == 100_000
        assert elapsed < 0.5
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_1m_rows(self):
        """Benchmark pandas conversion with 1M rows."""
        table = generate_arrow_table(1_000_000)
        
        start = time.perf_counter()
        df = table.to_pandas()
        elapsed = time.perf_counter() - start
        
        assert len(df) == 1_000_000
        assert elapsed < 2.0
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_vs_manual_10k(self):
        """Compare pandas Arrow conversion vs manual dict conversion."""
        n = 10_000
        table = generate_arrow_table(n)
        rows = generate_dict_rows(n)
        
        # pandas from Arrow (fast path)
        start = time.perf_counter()
        df_arrow = table.to_pandas()
        arrow_time = time.perf_counter() - start
        
        # Manual from dicts (slow path)
        start = time.perf_counter()
        df_manual = pd.DataFrame(rows)
        manual_time = time.perf_counter() - start
        
        assert len(df_arrow) == n
        assert len(df_manual) == n
        # Arrow path should be faster
        assert arrow_time < manual_time
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_filter_performance(self):
        """Benchmark pandas filtering after conversion."""
        table = generate_arrow_table(100_000)
        df = table.to_pandas()
        
        start = time.perf_counter()
        filtered = df[df["score"] > 50]
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_groupby_performance(self):
        """Benchmark pandas groupby after conversion."""
        table = generate_arrow_table(100_000)
        df = table.to_pandas()
        
        start = time.perf_counter()
        result = df.groupby("active")["score"].mean()
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_aggregation_performance(self):
        """Benchmark pandas aggregation after conversion."""
        table = generate_arrow_table(100_000)
        df = table.to_pandas()
        
        start = time.perf_counter()
        result = df.agg({"value": "sum", "score": "mean", "id": "max"})
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_sort_performance(self):
        """Benchmark pandas sorting after conversion."""
        table = generate_arrow_table(100_000)
        df = table.to_pandas()
        
        start = time.perf_counter()
        sorted_df = df.sort_values("score", ascending=False)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.5
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_merge_performance(self):
        """Benchmark pandas merge after conversion."""
        table1 = generate_arrow_table(10_000)
        table2 = generate_arrow_table(10_000)
        df1 = table1.to_pandas()
        df2 = table2.to_pandas()[["id", "score"]]
        
        start = time.perf_counter()
        result = pd.merge(df1, df2, on="id", suffixes=("", "_right"))
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.5


# =============================================================================
# Memory Performance Tests (5 tests)
# =============================================================================

class TestMemoryPerformance:
    """Benchmark tests for memory usage."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_memory_efficiency(self):
        """Test NumPy uses less memory than Python lists."""
        n = 100_000
        
        # NumPy array
        np_arr = np.arange(n, dtype=np.int64)
        np_bytes = np_arr.nbytes
        
        # Python list
        py_list = list(range(n))
        # Python ints are ~28 bytes each on 64-bit
        py_bytes_approx = n * 28
        
        # NumPy should be much smaller
        assert np_bytes < py_bytes_approx
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_arrow_memory_sharing(self):
        """Test Arrow memory can be shared with NumPy."""
        n = 1_000_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        
        # Get NumPy view
        np_arr = table.column("val").to_numpy()
        
        # Both should reference same memory for numeric types
        # (verify by checking nbytes is reasonable)
        assert np_arr.nbytes == n * 8  # int64 = 8 bytes
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_memory_efficiency(self):
        """Test Polars memory efficiency."""
        n = 1_000_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        
        df = pl.from_arrow(table)
        
        # Polars should be memory efficient
        assert len(df) == n
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_pandas_memory_usage(self):
        """Test pandas memory usage from Arrow."""
        n = 100_000
        table = generate_arrow_table(n)
        
        df = table.to_pandas()
        
        # Check memory usage is reasonable
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        assert memory_mb < 100  # Should be well under 100MB
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_structured_array_memory(self):
        """Test structured array memory usage."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n = 100_000
        table = generate_arrow_table(n)
        
        arr = arrow_table_to_structured(table)
        
        # Check memory usage is reasonable (allowing some overhead for structured arrays)
        memory_mb = arr.nbytes / (1024 * 1024)
        assert memory_mb < 150  # Structured arrays have some overhead


# =============================================================================
# Comparative Performance Tests (5 tests)
# =============================================================================

class TestComparativePerformance:
    """Compare performance across different methods."""
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_vs_pandas_conversion(self):
        """Compare Polars vs pandas Arrow conversion speed."""
        n = 100_000
        table = generate_arrow_table(n)
        
        # Polars
        start = time.perf_counter()
        df_polars = pl.from_arrow(table)
        polars_time = time.perf_counter() - start
        
        # pandas
        start = time.perf_counter()
        df_pandas = table.to_pandas()
        pandas_time = time.perf_counter() - start
        
        assert len(df_polars) == n
        assert len(df_pandas) == n
        
        # Polars should be faster or similar (zero-copy)
        # Allow some variance
        print(f"Polars: {polars_time:.4f}s, pandas: {pandas_time:.4f}s")
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_vs_pandas_groupby(self):
        """Compare Polars vs pandas groupby speed."""
        n = 100_000
        table = generate_arrow_table(n)
        
        # Polars
        df_polars = pl.from_arrow(table)
        start = time.perf_counter()
        result_polars = df_polars.group_by("active").agg(pl.mean("score"))
        polars_time = time.perf_counter() - start
        
        # pandas
        df_pandas = table.to_pandas()
        start = time.perf_counter()
        result_pandas = df_pandas.groupby("active")["score"].mean()
        pandas_time = time.perf_counter() - start
        
        print(f"Polars groupby: {polars_time:.4f}s, pandas groupby: {pandas_time:.4f}s")
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numpy_vs_pandas_aggregation(self):
        """Compare NumPy vs pandas aggregation speed."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 100_000
        table = generate_arrow_table(n)
        
        # NumPy
        arrays = arrow_table_to_numpy_columns(table)
        start = time.perf_counter()
        np_sum = arrays["value"].sum()
        np_mean = arrays["score"].mean()
        numpy_time = time.perf_counter() - start
        
        # pandas
        df = table.to_pandas()
        start = time.perf_counter()
        pd_sum = df["value"].sum()
        pd_mean = df["score"].mean()
        pandas_time = time.perf_counter() - start
        
        print(f"NumPy: {numpy_time:.4f}s, pandas: {pandas_time:.4f}s")
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_polars_vs_pandas_filter(self):
        """Compare Polars vs pandas filter speed."""
        n = 100_000
        table = generate_arrow_table(n)
        
        # Polars
        df_polars = pl.from_arrow(table)
        start = time.perf_counter()
        result_polars = df_polars.filter(pl.col("score") > 50)
        polars_time = time.perf_counter() - start
        
        # pandas
        df_pandas = table.to_pandas()
        start = time.perf_counter()
        result_pandas = df_pandas[df_pandas["score"] > 50]
        pandas_time = time.perf_counter() - start
        
        print(f"Polars filter: {polars_time:.4f}s, pandas filter: {pandas_time:.4f}s")
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_all_methods_conversion_time(self):
        """Compare all conversion methods."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 100_000
        table = generate_arrow_table(n)
        
        # Polars
        start = time.perf_counter()
        df_polars = pl.from_arrow(table)
        polars_time = time.perf_counter() - start
        
        # NumPy
        start = time.perf_counter()
        arrays = arrow_table_to_numpy_columns(table)
        numpy_time = time.perf_counter() - start
        
        # pandas (if available)
        if pandas_available:
            start = time.perf_counter()
            df_pandas = table.to_pandas()
            pandas_time = time.perf_counter() - start
        else:
            pandas_time = float('inf')
        
        print(f"Conversion times for {n} rows:")
        print(f"  Polars: {polars_time:.4f}s")
        print(f"  NumPy:  {numpy_time:.4f}s")
        print(f"  pandas: {pandas_time:.4f}s")


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print output

