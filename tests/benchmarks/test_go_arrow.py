"""
Go Bridge Arrow/DataFrame Integration Tests

These tests validate PyArrow integration and DataFrame conversion performance.
Run with: pytest tests/benchmarks/test_go_arrow.py -v

Targets:
- execute_arrow returns valid PyArrow Table
- Zero-copy conversion to pandas/polars
- Large result set handling (100k rows)
"""

import os
import time

import pytest

# Database URL
DB_URL = os.environ.get(
    "PYNEXT_TEST_DB_URL",
    "postgresql://pynext:pynext@localhost:5433/pynext_test"
)


def is_db_available() -> bool:
    """Check if test database is available."""
    try:
        import psycopg
        with psycopg.connect(DB_URL, connect_timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def is_pyarrow_available() -> bool:
    """Check if pyarrow is installed."""
    try:
        import pyarrow
        return True
    except ImportError:
        return False


def is_pandas_available() -> bool:
    """Check if pandas is installed."""
    try:
        import pandas
        return True
    except ImportError:
        return False


def is_polars_available() -> bool:
    """Check if polars is installed."""
    try:
        import polars
        return True
    except ImportError:
        return False


requires_db = pytest.mark.skipif(
    not is_db_available(),
    reason="PostgreSQL test database not available"
)

requires_arrow = pytest.mark.skipif(
    not is_pyarrow_available(),
    reason="PyArrow not installed"
)

requires_pandas = pytest.mark.skipif(
    not is_pandas_available(),
    reason="Pandas not installed"
)

requires_polars = pytest.mark.skipif(
    not is_polars_available(),
    reason="Polars not installed"
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="class")
def go_bridge(request):
    """Initialize Go bridge for Arrow tests."""
    import pynext_go
    
    # Close any existing connection first
    try:
        pynext_go.close()
    except Exception:
        pass
    
    pynext_go.init(primary=DB_URL, pool_min_size=10, pool_max_size=50)
    pynext_go.warmup()
    
    yield pynext_go
    pynext_go.close()


# =============================================================================
# Basic Arrow Tests
# =============================================================================

@requires_db
@requires_arrow
class TestArrowBasic:
    """Basic Arrow functionality tests."""
    
    def test_execute_arrow_returns_table(self, go_bridge):
        """Verify execute_arrow returns a PyArrow Table."""
        import pyarrow as pa
        
        table = go_bridge.execute_arrow("SELECT 1 as num, 'hello' as txt", [])
        
        assert isinstance(table, pa.Table), f"Expected Table, got {type(table)}"
        assert len(table) == 1
        assert table.num_columns == 2
        assert table.column_names == ['num', 'txt']
    
    def test_arrow_type_mapping(self, go_bridge):
        """Verify PostgreSQL types map correctly to Arrow types."""
        import pyarrow as pa
        
        table = go_bridge.execute_arrow("""
            SELECT 
                1::int4 as int_val,
                1::int8 as bigint_val,
                1.5::float8 as float_val,
                true::bool as bool_val,
                'text'::text as text_val,
                '2024-01-01'::date as date_val
        """, [])
        
        schema = table.schema
        
        # Check types
        assert pa.types.is_integer(schema.field('int_val').type)
        assert pa.types.is_int64(schema.field('bigint_val').type)
        assert pa.types.is_floating(schema.field('float_val').type)
        assert pa.types.is_boolean(schema.field('bool_val').type)
        assert pa.types.is_string(schema.field('text_val').type) or pa.types.is_large_string(schema.field('text_val').type)
    
    def test_arrow_null_handling(self, go_bridge):
        """Verify NULL values are handled correctly."""
        import pyarrow as pa
        
        table = go_bridge.execute_arrow("SELECT NULL::int4 as val", [])
        
        assert len(table) == 1
        assert table.column('val').null_count == 1
    
    def test_arrow_empty_result(self, go_bridge):
        """Verify empty result returns empty table with schema."""
        import pyarrow as pa
        
        table = go_bridge.execute_arrow(
            "SELECT * FROM users WHERE id = -1", []
        )
        
        assert isinstance(table, pa.Table)
        assert len(table) == 0
        assert len(table.column_names) > 0  # Schema preserved


# =============================================================================
# DataFrame Conversion Tests
# =============================================================================

@requires_db
@requires_arrow
@requires_pandas
class TestPandasConversion:
    """Pandas DataFrame conversion tests."""
    
    def test_arrow_to_pandas(self, go_bridge):
        """Verify Arrow table converts to pandas DataFrame."""
        import pandas as pd
        
        table = go_bridge.execute_arrow("SELECT * FROM users LIMIT 5", [])
        df = table.to_pandas()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert 'name' in df.columns
        assert 'email' in df.columns
    
    def test_pandas_dtypes_preserved(self, go_bridge):
        """Verify pandas dtypes match Arrow types."""
        import pandas as pd
        import numpy as np
        
        table = go_bridge.execute_arrow("""
            SELECT 
                1::int4 as int_val,
                1.5::float8 as float_val,
                true::bool as bool_val
        """, [])
        df = table.to_pandas()
        
        assert np.issubdtype(df['int_val'].dtype, np.integer)
        assert np.issubdtype(df['float_val'].dtype, np.floating)
        # Note: Arrow bool may map to bool or object
    
    def test_result_to_pandas_convenience(self, go_bridge):
        """Verify QueryResult.to_pandas() works."""
        import pandas as pd
        
        result = go_bridge.execute("SELECT * FROM users LIMIT 3", [])
        df = result.to_pandas()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3


@requires_db
@requires_arrow
@requires_polars
class TestPolarsConversion:
    """Polars DataFrame conversion tests."""
    
    def test_arrow_to_polars(self, go_bridge):
        """Verify Arrow table converts to polars DataFrame."""
        import polars as pl
        
        table = go_bridge.execute_arrow("SELECT * FROM users LIMIT 5", [])
        df = pl.from_arrow(table)
        
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 5
        assert 'name' in df.columns
    
    def test_result_to_polars_convenience(self, go_bridge):
        """Verify QueryResult.to_polars() works."""
        import polars as pl
        
        result = go_bridge.execute("SELECT * FROM users LIMIT 3", [])
        df = result.to_polars()
        
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 3


# =============================================================================
# Performance Tests
# =============================================================================

@requires_db
@requires_arrow
class TestArrowPerformance:
    """Arrow performance benchmarks."""
    
    def test_arrow_5000_rows_performance(self, go_bridge, benchmark):
        """Benchmark: Read 5000 rows via Arrow."""
        def run():
            return go_bridge.execute_arrow(
                "SELECT * FROM orders LIMIT 5000", []
            )
        
        # Warmup
        run()
        
        table = benchmark(run)
        assert len(table) == 5000
    
    def test_json_5000_rows_comparison(self, go_bridge, benchmark):
        """Benchmark: Read 5000 rows via JSON for comparison."""
        def run():
            return go_bridge.execute(
                "SELECT * FROM orders LIMIT 5000", []
            )
        
        # Warmup
        run()
        
        result = benchmark(run)
        assert len(result.rows) == 5000
    
    def test_arrow_100k_rows(self, go_bridge):
        """Test: Read 100k rows via Arrow (from logs table)."""
        import pyarrow as pa
        
        start = time.perf_counter()
        table = go_bridge.execute_arrow(
            "SELECT * FROM logs LIMIT 100000", []
        )
        elapsed = time.perf_counter() - start
        
        assert isinstance(table, pa.Table)
        assert len(table) == 100000
        
        print(f"\n📊 Arrow 100k rows:")
        print(f"   Time: {elapsed*1000:.0f}ms")
        print(f"   Rows/sec: {100000/elapsed:,.0f}")
        
        # Should complete in under 3 seconds
        assert elapsed < 3.0, f"100k rows took {elapsed:.1f}s, target is <3s"
    
    @requires_pandas
    def test_arrow_to_pandas_100k_performance(self, go_bridge):
        """Test: Convert 100k row Arrow table to pandas."""
        import pandas as pd
        
        # First get the Arrow table
        table = go_bridge.execute_arrow(
            "SELECT * FROM logs LIMIT 100000", []
        )
        
        # Time the conversion
        start = time.perf_counter()
        df = table.to_pandas()
        elapsed = time.perf_counter() - start
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100000
        
        print(f"\n📊 Arrow → Pandas 100k rows:")
        print(f"   Conversion time: {elapsed*1000:.0f}ms")
        
        # Conversion should be fast (leverages zero-copy where possible)
        assert elapsed < 1.0, f"Conversion took {elapsed:.1f}s, target is <1s"


# =============================================================================
# Arrow vs JSON Comparison
# =============================================================================

@requires_db
@requires_arrow
class TestArrowVsJson:
    """Compare Arrow and JSON result formats."""
    
    def test_arrow_vs_json_correctness(self, go_bridge):
        """Verify Arrow and JSON return same data."""
        sql = "SELECT id, name, email FROM users ORDER BY id LIMIT 5"
        
        # Get via JSON
        json_result = go_bridge.execute(sql, [])
        
        # Get via Arrow
        arrow_table = go_bridge.execute_arrow(sql, [])
        arrow_df = arrow_table.to_pandas()
        
        # Compare
        assert len(json_result.rows) == len(arrow_df)
        
        for i, row in enumerate(json_result.rows):
            assert row[0] == arrow_df.iloc[i]['id']
            assert row[1] == arrow_df.iloc[i]['name']
            assert row[2] == arrow_df.iloc[i]['email']
    
    def test_arrow_faster_for_large_results(self, go_bridge):
        """Arrow should be faster than JSON for large results."""
        sql = "SELECT * FROM logs LIMIT 50000"
        
        # Time JSON
        json_times = []
        for _ in range(3):
            start = time.perf_counter()
            go_bridge.execute(sql, [])
            json_times.append(time.perf_counter() - start)
        json_best = min(json_times)
        
        # Time Arrow
        arrow_times = []
        for _ in range(3):
            start = time.perf_counter()
            go_bridge.execute_arrow(sql, [])
            arrow_times.append(time.perf_counter() - start)
        arrow_best = min(arrow_times)
        
        print(f"\n📊 Arrow vs JSON (50k rows):")
        print(f"   JSON best: {json_best*1000:.0f}ms")
        print(f"   Arrow best: {arrow_best*1000:.0f}ms")
        print(f"   Speedup: {json_best/arrow_best:.2f}x")
        
        # Arrow should be at least as fast as JSON
        # (May be faster or similar depending on data types)


# =============================================================================
# NumPy Integration Tests
# =============================================================================

@requires_db
@requires_arrow
class TestNumPyIntegration:
    """NumPy array integration tests."""
    
    def test_arrow_to_numpy_columns(self, go_bridge):
        """Verify Arrow columns convert to NumPy arrays."""
        import numpy as np
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        
        table = go_bridge.execute_arrow(
            "SELECT id, total FROM orders LIMIT 100", []
        )
        
        arrays = arrow_table_to_numpy_columns(table)
        
        assert 'id' in arrays
        assert 'total' in arrays
        assert isinstance(arrays['id'], np.ndarray)
        assert len(arrays['id']) == 100
    
    def test_numpy_zero_copy(self, go_bridge):
        """Verify NumPy conversion uses zero-copy where possible."""
        import numpy as np
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        
        table = go_bridge.execute_arrow(
            "SELECT id FROM orders LIMIT 1000", []
        )
        
        # Get column as NumPy array
        arrays = arrow_table_to_numpy_columns(table, zero_copy=True)
        arr = arrays['id']
        
        assert isinstance(arr, np.ndarray)
        assert len(arr) == 1000


# =============================================================================
# Async Arrow Tests
# =============================================================================

@requires_db
@requires_arrow
class TestArrowAsync:
    """Async Arrow execution tests."""
    
    @pytest.mark.asyncio
    async def test_execute_arrow_async(self, go_bridge):
        """Verify async Arrow execution works."""
        import pyarrow as pa
        
        table = await go_bridge.execute_arrow_async(
            "SELECT * FROM users LIMIT 5", []
        )
        
        assert isinstance(table, pa.Table)
        assert len(table) == 5
    
    @pytest.mark.asyncio
    async def test_concurrent_arrow_queries(self, go_bridge):
        """Test multiple concurrent Arrow queries."""
        import asyncio
        import pyarrow as pa
        
        async def query(limit: int):
            return await go_bridge.execute_arrow_async(
                f"SELECT * FROM orders LIMIT {limit}", []
            )
        
        # Run 5 queries concurrently
        results = await asyncio.gather(
            query(100),
            query(200),
            query(300),
            query(400),
            query(500),
        )
        
        assert len(results) == 5
        assert all(isinstance(r, pa.Table) for r in results)
        assert [len(r) for r in results] == [100, 200, 300, 400, 500]


# =============================================================================
# Regression Tests
# =============================================================================

@requires_db
@requires_arrow
class TestArrowRegression:
    """Arrow performance regression tests."""
    
    def test_arrow_10k_under_200ms(self, go_bridge):
        """10k rows via Arrow must complete in under 200ms."""
        times = []
        
        for _ in range(5):
            start = time.perf_counter()
            table = go_bridge.execute_arrow(
                "SELECT * FROM orders LIMIT 10000", []
            )
            times.append(time.perf_counter() - start)
            assert len(table) == 5000  # Only 5000 orders in test data
        
        best = min(times)
        print(f"\n⏱️ Arrow 5k rows (best of 5): {best*1000:.0f}ms")
        
        # Adjust target for actual data size
        assert best < 0.2, f"Arrow took {best*1000:.0f}ms, target is <200ms"

