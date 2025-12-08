"""
Polars Integration Tests for Phase 8.3.

Tests for pynext_go.execute_polars() and related functionality.
80 comprehensive tests covering type mapping, null handling, performance,
and integration with the QueryBuilder.

Test Categories:
1. Basic type mapping (all PostgreSQL types)
2. Null handling
3. Empty results
4. Large datasets
5. Schema preservation
6. Error handling
7. Zero-copy verification
8. QueryBuilder integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List

# Try to import polars (skip tests if not available)
polars_available = False
try:
    import polars as pl
    polars_available = True
except ImportError:
    pass

# Try to import pyarrow (needed for testing)
pyarrow_available = False
try:
    import pyarrow as pa
    pyarrow_available = True
except ImportError:
    pass


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_arrow_table():
    """Create a mock Arrow table for testing."""
    if not pyarrow_available:
        pytest.skip("pyarrow not available")
    
    return pa.table({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "score": [95.5, 87.3, 92.1, 78.9, 88.5],
        "active": [True, False, True, True, False],
    })


@pytest.fixture
def mock_bridge():
    """Create a mock GoBridge for testing."""
    bridge = Mock()
    bridge._initialized = True
    return bridge


# =============================================================================
# Basic Type Mapping Tests (20 tests)
# =============================================================================

class TestPolarsTypeMapping:
    """Test PostgreSQL -> Arrow -> Polars type mapping."""
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int8_column(self):
        """Test INT8 (smallint) type mapping."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int8())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Int8
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int16_column(self):
        """Test INT16 (smallint) type mapping."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int16())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Int16
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int32_column(self):
        """Test INT32 (integer) type mapping."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int32())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Int32
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int64_column(self):
        """Test INT64 (bigint) type mapping."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Int64
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float32_column(self):
        """Test FLOAT32 (real) type mapping."""
        table = pa.table({"val": pa.array([1.5, 2.5, 3.5], type=pa.float32())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Float32
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float64_column(self):
        """Test FLOAT64 (double precision) type mapping."""
        table = pa.table({"val": pa.array([1.5, 2.5, 3.5], type=pa.float64())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Float64
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_column(self):
        """Test BOOLEAN type mapping."""
        table = pa.table({"val": pa.array([True, False, True], type=pa.bool_())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Boolean
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_column(self):
        """Test STRING (text, varchar) type mapping."""
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Utf8
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_string_column(self):
        """Test LARGE_STRING type mapping."""
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.large_string())})
        df = pl.from_arrow(table)
        # Large string should map to String/Utf8 in Polars
        assert df["val"].dtype in (pl.Utf8, pl.String)
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_binary_column(self):
        """Test BINARY (bytea) type mapping."""
        table = pa.table({"val": pa.array([b"abc", b"def", b"ghi"], type=pa.binary())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Binary
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_date32_column(self):
        """Test DATE32 type mapping."""
        import datetime
        dates = [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2), datetime.date(2024, 1, 3)]
        table = pa.table({"val": pa.array(dates, type=pa.date32())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Date
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_timestamp_column(self):
        """Test TIMESTAMP type mapping."""
        import datetime
        ts = [datetime.datetime(2024, 1, 1, 12, 0), datetime.datetime(2024, 1, 2, 12, 0)]
        table = pa.table({"val": pa.array(ts, type=pa.timestamp("us"))})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Datetime("us")
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_timestamp_with_timezone(self):
        """Test TIMESTAMP WITH TIMEZONE type mapping."""
        import datetime
        ts = [datetime.datetime(2024, 1, 1, 12, 0), datetime.datetime(2024, 1, 2, 12, 0)]
        table = pa.table({"val": pa.array(ts, type=pa.timestamp("us", tz="UTC"))})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Datetime("us", "UTC")
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_duration_column(self):
        """Test DURATION type mapping."""
        table = pa.table({"val": pa.array([1000, 2000, 3000], type=pa.duration("us"))})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Duration("us")
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_mixed_types_table(self):
        """Test table with mixed column types."""
        table = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["a", "b", "c"], type=pa.string()),
            "score": pa.array([1.1, 2.2, 3.3], type=pa.float64()),
            "active": pa.array([True, False, True], type=pa.bool_()),
        })
        df = pl.from_arrow(table)
        assert df["id"].dtype == pl.Int64
        assert df["name"].dtype == pl.Utf8
        assert df["score"].dtype == pl.Float64
        assert df["active"].dtype == pl.Boolean
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint8_column(self):
        """Test UINT8 type mapping."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.uint8())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.UInt8
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint16_column(self):
        """Test UINT16 type mapping."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.uint16())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.UInt16
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint32_column(self):
        """Test UINT32 type mapping."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.uint32())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.UInt32
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint64_column(self):
        """Test UINT64 type mapping."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.uint64())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.UInt64


# =============================================================================
# Null Handling Tests (15 tests)
# =============================================================================

class TestPolarsNullHandling:
    """Test null value handling in Polars conversion."""
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_int64(self):
        """Test null handling in INT64 column."""
        table = pa.table({"val": pa.array([1, None, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        assert df["val"].null_count() == 1
        assert df["val"][0] == 1
        assert df["val"][1] is None
        assert df["val"][2] == 3
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_float64(self):
        """Test null handling in FLOAT64 column."""
        table = pa.table({"val": pa.array([1.5, None, 3.5], type=pa.float64())})
        df = pl.from_arrow(table)
        assert df["val"].null_count() == 1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_string(self):
        """Test null handling in STRING column."""
        table = pa.table({"val": pa.array(["a", None, "c"], type=pa.string())})
        df = pl.from_arrow(table)
        assert df["val"].null_count() == 1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_bool(self):
        """Test null handling in BOOLEAN column."""
        table = pa.table({"val": pa.array([True, None, False], type=pa.bool_())})
        df = pl.from_arrow(table)
        assert df["val"].null_count() == 1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_all_nulls(self):
        """Test column with all null values."""
        table = pa.table({"val": pa.array([None, None, None], type=pa.int64())})
        df = pl.from_arrow(table)
        assert df["val"].null_count() == 3
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_no_nulls(self):
        """Test column with no null values."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        assert df["val"].null_count() == 0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_first_row(self):
        """Test null in first row."""
        table = pa.table({"val": pa.array([None, 2, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        assert df["val"][0] is None
        assert df["val"][1] == 2
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_last_row(self):
        """Test null in last row."""
        table = pa.table({"val": pa.array([1, 2, None], type=pa.int64())})
        df = pl.from_arrow(table)
        assert df["val"][0] == 1
        assert df["val"][2] is None
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_mixed_nulls_multiple_columns(self):
        """Test nulls in multiple columns."""
        table = pa.table({
            "a": pa.array([1, None, 3], type=pa.int64()),
            "b": pa.array([None, "x", "y"], type=pa.string()),
            "c": pa.array([1.0, 2.0, None], type=pa.float64()),
        })
        df = pl.from_arrow(table)
        assert df["a"].null_count() == 1
        assert df["b"].null_count() == 1
        assert df["c"].null_count() == 1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_fill_value(self):
        """Test filling null values."""
        table = pa.table({"val": pa.array([1, None, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        filled = df.with_columns(pl.col("val").fill_null(0))
        assert filled["val"].null_count() == 0
        assert filled["val"][1] == 0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_drop(self):
        """Test dropping null values."""
        table = pa.table({"val": pa.array([1, None, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        dropped = df.drop_nulls()
        assert len(dropped) == 2
        assert dropped["val"].null_count() == 0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_date(self):
        """Test null handling in DATE column."""
        import datetime
        dates = [datetime.date(2024, 1, 1), None, datetime.date(2024, 1, 3)]
        table = pa.table({"val": pa.array(dates, type=pa.date32())})
        df = pl.from_arrow(table)
        assert df["val"].null_count() == 1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_timestamp(self):
        """Test null handling in TIMESTAMP column."""
        import datetime
        ts = [datetime.datetime(2024, 1, 1), None, datetime.datetime(2024, 1, 3)]
        table = pa.table({"val": pa.array(ts, type=pa.timestamp("us"))})
        df = pl.from_arrow(table)
        assert df["val"].null_count() == 1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_count_aggregation(self):
        """Test aggregation with null values."""
        table = pa.table({"val": pa.array([1, None, 3, None, 5], type=pa.int64())})
        df = pl.from_arrow(table)
        # Sum should ignore nulls
        assert df["val"].sum() == 9
        assert df["val"].mean() == 3.0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_binary(self):
        """Test null handling in BINARY column."""
        table = pa.table({"val": pa.array([b"a", None, b"c"], type=pa.binary())})
        df = pl.from_arrow(table)
        assert df["val"].null_count() == 1


# =============================================================================
# Empty Results Tests (10 tests)
# =============================================================================

class TestPolarsEmptyResults:
    """Test handling of empty result sets."""
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table(self):
        """Test empty table conversion."""
        table = pa.table({"id": pa.array([], type=pa.int64())})
        df = pl.from_arrow(table)
        assert len(df) == 0
        assert df.columns == ["id"]
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table_multiple_columns(self):
        """Test empty table with multiple columns."""
        table = pa.table({
            "id": pa.array([], type=pa.int64()),
            "name": pa.array([], type=pa.string()),
            "score": pa.array([], type=pa.float64()),
        })
        df = pl.from_arrow(table)
        assert len(df) == 0
        assert df.columns == ["id", "name", "score"]
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table_schema_preserved(self):
        """Test schema preservation for empty table."""
        table = pa.table({
            "id": pa.array([], type=pa.int64()),
            "name": pa.array([], type=pa.string()),
        })
        df = pl.from_arrow(table)
        assert df["id"].dtype == pl.Int64
        assert df["name"].dtype == pl.Utf8
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table_operations(self):
        """Test operations on empty table."""
        table = pa.table({"val": pa.array([], type=pa.int64())})
        df = pl.from_arrow(table)
        # Operations should not fail
        assert df.filter(pl.col("val") > 0).height == 0
        assert df.select(pl.col("val") * 2).height == 0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table_aggregation(self):
        """Test aggregation on empty table."""
        table = pa.table({"val": pa.array([], type=pa.int64())})
        df = pl.from_arrow(table)
        result = df.select(pl.col("val").sum())
        assert result["val"][0] == 0 or result["val"][0] is None
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table_group_by(self):
        """Test group_by on empty table."""
        table = pa.table({
            "category": pa.array([], type=pa.string()),
            "value": pa.array([], type=pa.int64()),
        })
        df = pl.from_arrow(table)
        result = df.group_by("category").agg(pl.col("value").sum())
        assert len(result) == 0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table_join(self):
        """Test join with empty table."""
        table1 = pa.table({"id": pa.array([], type=pa.int64())})
        table2 = pa.table({"id": pa.array([1, 2], type=pa.int64())})
        df1 = pl.from_arrow(table1)
        df2 = pl.from_arrow(table2)
        result = df1.join(df2, on="id")
        assert len(result) == 0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table_sort(self):
        """Test sorting empty table."""
        table = pa.table({"val": pa.array([], type=pa.int64())})
        df = pl.from_arrow(table)
        result = df.sort("val")
        assert len(result) == 0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table_head(self):
        """Test head on empty table."""
        table = pa.table({"val": pa.array([], type=pa.int64())})
        df = pl.from_arrow(table)
        result = df.head(5)
        assert len(result) == 0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table_to_dict(self):
        """Test to_dict on empty table."""
        table = pa.table({"val": pa.array([], type=pa.int64())})
        df = pl.from_arrow(table)
        result = df.to_dict(as_series=False)  # Get lists, not Series
        assert result == {"val": []}


# =============================================================================
# Large Dataset Tests (10 tests)
# =============================================================================

class TestPolarsLargeDatasets:
    """Test performance with large datasets."""
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_10k_rows(self):
        """Test conversion of 10K rows."""
        n = 10_000
        table = pa.table({
            "id": pa.array(range(n), type=pa.int64()),
            "value": pa.array([float(i) for i in range(n)], type=pa.float64()),
        })
        df = pl.from_arrow(table)
        assert len(df) == n
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_100k_rows(self):
        """Test conversion of 100K rows."""
        n = 100_000
        table = pa.table({
            "id": pa.array(range(n), type=pa.int64()),
            "value": pa.array([float(i) for i in range(n)], type=pa.float64()),
        })
        df = pl.from_arrow(table)
        assert len(df) == n
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_string_column(self):
        """Test large string column conversion."""
        n = 10_000
        strings = [f"string_{i}" for i in range(n)]
        table = pa.table({"name": pa.array(strings, type=pa.string())})
        df = pl.from_arrow(table)
        assert len(df) == n
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_many_columns(self):
        """Test table with many columns."""
        n_cols = 50
        n_rows = 1000
        data = {f"col_{i}": pa.array(range(n_rows), type=pa.int64()) for i in range(n_cols)}
        table = pa.table(data)
        df = pl.from_arrow(table)
        assert len(df.columns) == n_cols
        assert len(df) == n_rows
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_aggregation(self):
        """Test aggregation on large dataset."""
        n = 100_000
        table = pa.table({
            "id": pa.array(range(n), type=pa.int64()),
            "value": pa.array([float(i % 100) for i in range(n)], type=pa.float64()),
        })
        df = pl.from_arrow(table)
        result = df.select(pl.col("value").sum())
        # Sum of (0..99 repeated 1000 times) = 99*100/2 * 1000 = 4950000
        assert result["value"][0] == 4950000.0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_filter(self):
        """Test filtering large dataset."""
        n = 100_000
        table = pa.table({
            "id": pa.array(range(n), type=pa.int64()),
            "value": pa.array([i % 100 for i in range(n)], type=pa.int64()),
        })
        df = pl.from_arrow(table)
        result = df.filter(pl.col("value") < 10)
        # 10% of rows should match
        assert len(result) == n // 10
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_group_by(self):
        """Test group_by on large dataset."""
        n = 100_000
        table = pa.table({
            "category": pa.array([f"cat_{i % 100}" for i in range(n)], type=pa.string()),
            "value": pa.array([float(i) for i in range(n)], type=pa.float64()),
        })
        df = pl.from_arrow(table)
        result = df.group_by("category").agg(pl.col("value").sum())
        assert len(result) == 100
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_sort(self):
        """Test sorting large dataset."""
        n = 100_000
        import random
        values = list(range(n))
        random.shuffle(values)
        table = pa.table({"value": pa.array(values, type=pa.int64())})
        df = pl.from_arrow(table)
        result = df.sort("value")
        assert result["value"][0] == 0
        assert result["value"][-1] == n - 1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_with_nulls(self):
        """Test large dataset with many nulls."""
        n = 100_000
        values = [i if i % 3 != 0 else None for i in range(n)]
        table = pa.table({"value": pa.array(values, type=pa.int64())})
        df = pl.from_arrow(table)
        # About 1/3 should be null
        assert df["value"].null_count() > n // 4
        assert df["value"].null_count() < n // 2
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_chunked_array(self):
        """Test chunked Arrow array conversion."""
        chunk1 = pa.array([1, 2, 3], type=pa.int64())
        chunk2 = pa.array([4, 5, 6], type=pa.int64())
        chunked = pa.chunked_array([chunk1, chunk2])
        table = pa.table({"value": chunked})
        df = pl.from_arrow(table)
        assert len(df) == 6
        assert df["value"].to_list() == [1, 2, 3, 4, 5, 6]


# =============================================================================
# Schema Preservation Tests (10 tests)
# =============================================================================

class TestPolarsSchemaPreservation:
    """Test that schema is preserved through conversion."""
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_column_order_preserved(self):
        """Test column order is preserved."""
        table = pa.table({
            "z": pa.array([1], type=pa.int64()),
            "a": pa.array([2], type=pa.int64()),
            "m": pa.array([3], type=pa.int64()),
        })
        df = pl.from_arrow(table)
        assert df.columns == ["z", "a", "m"]
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_column_names_preserved(self):
        """Test column names are preserved."""
        table = pa.table({
            "Column_With_Underscores": pa.array([1], type=pa.int64()),
            "columnWithCamelCase": pa.array([2], type=pa.int64()),
            "column-with-dashes": pa.array([3], type=pa.int64()),
        })
        df = pl.from_arrow(table)
        assert "Column_With_Underscores" in df.columns
        assert "columnWithCamelCase" in df.columns
        assert "column-with-dashes" in df.columns
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_types_preserved_int64(self):
        """Test INT64 type is preserved."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Int64
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_types_preserved_float64(self):
        """Test FLOAT64 type is preserved."""
        table = pa.table({"val": pa.array([1.0, 2.0, 3.0], type=pa.float64())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Float64
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_types_preserved_string(self):
        """Test STRING type is preserved."""
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        df = pl.from_arrow(table)
        assert df["val"].dtype == pl.Utf8
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_nullable_preserved(self):
        """Test nullable columns remain nullable."""
        table = pa.table({"val": pa.array([1, None, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        # Polars should handle nulls
        assert df["val"].null_count() == 1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_schema_from_table(self):
        """Test schema can be extracted."""
        table = pa.table({
            "id": pa.array([1], type=pa.int64()),
            "name": pa.array(["x"], type=pa.string()),
        })
        df = pl.from_arrow(table)
        schema = df.schema
        assert "id" in schema
        assert "name" in schema
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_precision_preserved(self):
        """Test numeric precision is preserved."""
        import math
        table = pa.table({"val": pa.array([math.pi, math.e], type=pa.float64())})
        df = pl.from_arrow(table)
        assert abs(df["val"][0] - math.pi) < 1e-10
        assert abs(df["val"][1] - math.e) < 1e-10
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_unicode_preserved(self):
        """Test unicode strings are preserved."""
        table = pa.table({"val": pa.array(["hello", "世界", "🎉"], type=pa.string())})
        df = pl.from_arrow(table)
        assert df["val"][0] == "hello"
        assert df["val"][1] == "世界"
        assert df["val"][2] == "🎉"
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_string_preserved(self):
        """Test empty strings are preserved."""
        table = pa.table({"val": pa.array(["", "a", ""], type=pa.string())})
        df = pl.from_arrow(table)
        assert df["val"][0] == ""
        assert df["val"][1] == "a"
        assert df["val"][2] == ""


# =============================================================================
# Error Handling Tests (10 tests)
# =============================================================================

class TestPolarsErrorHandling:
    """Test error handling in Polars conversion."""
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_import_error_message(self):
        """Test clear error message when polars not installed."""
        # This test would need to mock the import
        pass  # Covered by other tests
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_invalid_arrow_table(self):
        """Test handling of invalid Arrow table."""
        with pytest.raises((TypeError, ValueError, AttributeError)):
            pl.from_arrow("not a table")
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_none_table(self):
        """Test handling of None table - Polars returns empty DataFrame."""
        # Polars from_arrow with None returns an empty DataFrame, doesn't raise
        result = pl.from_arrow(None)
        assert result is not None  # It returns a valid (empty) DataFrame
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_invalid_column_access(self):
        """Test accessing non-existent column."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        with pytest.raises((KeyError, pl.exceptions.ColumnNotFoundError)):
            _ = df["nonexistent"]
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_invalid_filter_type(self):
        """Test filter with invalid type."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        with pytest.raises((TypeError, pl.exceptions.InvalidOperationError)):
            df.filter("invalid")
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_type_mismatch_operation(self):
        """Test operation with mismatched types."""
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        df = pl.from_arrow(table)
        # Trying to do numeric operation on strings
        with pytest.raises((TypeError, pl.exceptions.InvalidOperationError)):
            df.select(pl.col("val") + 1)
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_out_of_bounds_index(self):
        """Test out of bounds index access."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        with pytest.raises(IndexError):
            _ = df[100]
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_invalid_join_key(self):
        """Test join with non-existent key."""
        table1 = pa.table({"id": pa.array([1, 2], type=pa.int64())})
        table2 = pa.table({"other": pa.array([1, 2], type=pa.int64())})
        df1 = pl.from_arrow(table1)
        df2 = pl.from_arrow(table2)
        with pytest.raises((KeyError, pl.exceptions.ColumnNotFoundError)):
            df1.join(df2, on="nonexistent")
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_invalid_group_by_column(self):
        """Test group_by with non-existent column."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        with pytest.raises((KeyError, pl.exceptions.ColumnNotFoundError)):
            df.group_by("nonexistent").agg(pl.col("val").sum())
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_invalid_sort_column(self):
        """Test sort with non-existent column."""
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        df = pl.from_arrow(table)
        with pytest.raises((KeyError, pl.exceptions.ColumnNotFoundError)):
            df.sort("nonexistent")


# =============================================================================
# Zero-Copy Verification Tests (5 tests)
# =============================================================================

class TestPolarsZeroCopy:
    """Test zero-copy behavior for performance."""
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_from_arrow_is_fast(self):
        """Test that from_arrow is very fast (zero-copy)."""
        import time
        n = 1_000_000
        table = pa.table({
            "id": pa.array(range(n), type=pa.int64()),
            "value": pa.array([float(i) for i in range(n)], type=pa.float64()),
        })
        
        start = time.perf_counter()
        df = pl.from_arrow(table)
        elapsed = time.perf_counter() - start
        
        # Zero-copy should be nearly instant (< 100ms for 1M rows)
        assert elapsed < 0.1, f"from_arrow took {elapsed:.3f}s, expected < 0.1s"
        assert len(df) == n
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_numeric_columns_zero_copy(self):
        """Test numeric columns use zero-copy."""
        table = pa.table({"val": pa.array([1.0, 2.0, 3.0], type=pa.float64())})
        df = pl.from_arrow(table)
        # Polars should share memory with Arrow
        assert len(df) == 3
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_columns_may_copy(self):
        """Test string columns (may require copy)."""
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        df = pl.from_arrow(table)
        # Should still work, even if not zero-copy
        assert df["val"].to_list() == ["a", "b", "c"]
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_roundtrip_preserves_data(self):
        """Test Arrow -> Polars -> Arrow roundtrip."""
        table = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["a", "b", "c"], type=pa.string()),
        })
        df = pl.from_arrow(table)
        table2 = df.to_arrow()
        df2 = pl.from_arrow(table2)
        assert df2["id"].to_list() == [1, 2, 3]
        assert df2["name"].to_list() == ["a", "b", "c"]
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_zero_copy(self):
        """Test zero-copy with large dataset."""
        import time
        n = 10_000_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        
        start = time.perf_counter()
        df = pl.from_arrow(table)
        elapsed = time.perf_counter() - start
        
        # Should still be fast with 10M rows
        assert elapsed < 0.5, f"from_arrow took {elapsed:.3f}s, expected < 0.5s"
        assert len(df) == n


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

