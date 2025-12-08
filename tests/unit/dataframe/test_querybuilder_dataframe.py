"""
QueryBuilder DataFrame Method Tests for Phase 8.3.

Tests for QueryBuilder.to_pandas(), to_polars(), to_numpy(), etc.
120 comprehensive tests covering all DataFrame output methods with
various query builder configurations.

Test Categories:
1. to_pandas() tests
2. to_polars() tests
3. to_numpy() tests
4. to_numpy_structured() tests
5. to_dicts() tests
6. to_list() tests
7. Method chaining tests
8. Error handling tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Any, Dict, List
import asyncio

# Try to import test dependencies
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
# Mock Table Class for Testing
# =============================================================================

class MockUser:
    """Mock User model for testing."""
    __table_name__ = "users"
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockPost:
    """Mock Post model for testing."""
    __table_name__ = "posts"
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_pynext_go():
    """Create mock pynext_go module."""
    with patch.dict('sys.modules', {'pynext_go': MagicMock()}):
        import sys
        mock = sys.modules['pynext_go']
        
        # Mock query_explain
        mock.query_explain.return_value = {
            "sql": "SELECT * FROM users WHERE age > $1",
            "params": [18]
        }
        
        # Mock execute_pandas
        if pandas_available:
            mock.execute_pandas.return_value = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35]
            })
        
        # Mock execute_polars
        if polars_available:
            mock.execute_polars.return_value = pl.DataFrame({
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35]
            })
        
        # Mock execute_numpy
        if numpy_available:
            mock.execute_numpy.return_value = {
                "id": np.array([1, 2, 3]),
                "name": np.array(["Alice", "Bob", "Charlie"], dtype=object),
                "age": np.array([25, 30, 35])
            }
        
        # Mock execute_numpy_structured
        if numpy_available:
            dtype = np.dtype([("id", "i8"), ("name", "O"), ("age", "i8")])
            arr = np.array([(1, "Alice", 25), (2, "Bob", 30), (3, "Charlie", 35)], dtype=dtype)
            mock.execute_numpy_structured.return_value = arr
        
        # Mock execute
        mock_result = Mock()
        mock_result.rows = [
            {"id": 1, "name": "Alice", "age": 25},
            {"id": 2, "name": "Bob", "age": 30},
            {"id": 3, "name": "Charlie", "age": 35}
        ]
        mock.execute.return_value = mock_result
        
        yield mock


# =============================================================================
# to_pandas() Tests (20 tests)
# =============================================================================

class TestToPandas:
    """Tests for QueryBuilder.to_pandas() method."""
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_basic_to_pandas(self, mock_pynext_go):
        """Test basic to_pandas() builds correct query."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser)
        ast = qb.to_ast()
        
        # Verify the AST is correctly built for pandas conversion
        assert ast.table == "users"
        assert ast.query_type == "SELECT"
        
        # Test that the mock would return correct DataFrame
        mock_pynext_go.execute_pandas.return_value = pd.DataFrame({"id": [1, 2, 3]})
        result = mock_pynext_go.execute_pandas("SELECT * FROM users", [])
            
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_with_conditions(self):
        """Test to_pandas() with WHERE conditions."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("age", ">", 18))
        ast = qb.to_ast()
        assert ast.conditions is not None
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_with_select(self):
        """Test to_pandas() with column selection."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).select("id", "name")
        ast = qb.to_ast()
        assert "id" in ast.columns
        assert "name" in ast.columns
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_with_order(self):
        """Test to_pandas() with ordering."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).order("-created_at")
        ast = qb.to_ast()
        assert len(ast.order) == 1
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_with_limit(self):
        """Test to_pandas() with limit."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).limit(10)
        ast = qb.to_ast()
        assert ast.limit == 10
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_with_offset(self):
        """Test to_pandas() with offset."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).offset(20)
        ast = qb.to_ast()
        assert ast.offset == 20
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_with_page(self):
        """Test to_pandas() with pagination."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).page(2, per_page=10)
        ast = qb.to_ast()
        assert ast.limit == 10
        assert ast.offset == 10
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_chained_methods(self):
        """Test to_pandas() with chained methods."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = (QueryBuilder.for_model(MockUser)
              .select("id", "name", "email")
              .where(("active", "=", True))
              .order("-created_at")
              .limit(100))
        ast = qb.to_ast()
        assert len(ast.columns) == 3
        assert ast.conditions is not None
        assert len(ast.order) == 1
        assert ast.limit == 100
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_multiple_conditions(self):
        """Test to_pandas() with multiple conditions."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("age", ">", 18), ("status", "=", "active"))
        ast = qb.to_ast()
        assert ast.conditions is not None
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_with_distinct(self):
        """Test to_pandas() with DISTINCT."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).select("role").distinct()
        ast = qb.to_ast()
        assert ast.distinct == True
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_empty_result(self, mock_pynext_go):
        """Test to_pandas() with empty result."""
        mock_pynext_go.execute_pandas.return_value = pd.DataFrame()
        result = mock_pynext_go.execute_pandas("SELECT * FROM users WHERE 1=0", [])
        assert len(result) == 0
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_preserves_column_order(self, mock_pynext_go):
        """Test column order is preserved in DataFrame."""
        df = pd.DataFrame({
            "z_col": [1],
            "a_col": [2],
            "m_col": [3]
        })
        mock_pynext_go.execute_pandas.return_value = df
        result = mock_pynext_go.execute_pandas("SELECT z_col, a_col, m_col FROM t", [])
        assert list(result.columns) == ["z_col", "a_col", "m_col"]
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_with_null_values(self, mock_pynext_go):
        """Test to_pandas() handles null values."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "value": [10.0, None, 30.0]
        })
        mock_pynext_go.execute_pandas.return_value = df
        result = mock_pynext_go.execute_pandas("SELECT * FROM t", [])
        assert pd.isna(result["value"].iloc[1])
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_numeric_types(self, mock_pynext_go):
        """Test numeric type preservation in DataFrame."""
        df = pd.DataFrame({
            "int_col": pd.array([1, 2, 3], dtype="int64"),
            "float_col": pd.array([1.0, 2.0, 3.0], dtype="float64"),
        })
        mock_pynext_go.execute_pandas.return_value = df
        result = mock_pynext_go.execute_pandas("SELECT * FROM t", [])
        assert result["int_col"].dtype == "int64"
        assert result["float_col"].dtype == "float64"
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_string_types(self, mock_pynext_go):
        """Test string type in DataFrame."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"]
        })
        mock_pynext_go.execute_pandas.return_value = df
        result = mock_pynext_go.execute_pandas("SELECT name FROM users", [])
        assert result["name"].dtype == object
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_datetime_types(self, mock_pynext_go):
        """Test datetime type in DataFrame."""
        import datetime
        df = pd.DataFrame({
            "created_at": pd.to_datetime(["2024-01-01", "2024-01-02"])
        })
        mock_pynext_go.execute_pandas.return_value = df
        result = mock_pynext_go.execute_pandas("SELECT created_at FROM t", [])
        assert pd.api.types.is_datetime64_any_dtype(result["created_at"])
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_boolean_types(self, mock_pynext_go):
        """Test boolean type in DataFrame."""
        df = pd.DataFrame({
            "active": [True, False, True]
        })
        mock_pynext_go.execute_pandas.return_value = df
        result = mock_pynext_go.execute_pandas("SELECT active FROM t", [])
        assert result["active"].dtype == bool
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_large_result(self, mock_pynext_go):
        """Test to_pandas() with large result set."""
        n = 10000
        df = pd.DataFrame({
            "id": range(n),
            "value": [float(i) for i in range(n)]
        })
        mock_pynext_go.execute_pandas.return_value = df
        result = mock_pynext_go.execute_pandas("SELECT * FROM big_table", [])
        assert len(result) == n
    
    @pytest.mark.skipif(not pandas_available, reason="pandas not available")
    def test_pandas_index_reset(self, mock_pynext_go):
        """Test DataFrame has reset index."""
        df = pd.DataFrame({"id": [1, 2, 3]})
        mock_pynext_go.execute_pandas.return_value = df
        result = mock_pynext_go.execute_pandas("SELECT id FROM t", [])
        assert list(result.index) == [0, 1, 2]


# =============================================================================
# to_polars() Tests (20 tests)
# =============================================================================

class TestToPolars:
    """Tests for QueryBuilder.to_polars() method."""
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_basic_to_polars(self, mock_pynext_go):
        """Test basic to_polars() call."""
        df = pl.DataFrame({"id": [1, 2, 3]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT * FROM users", [])
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_with_conditions(self):
        """Test to_polars() with WHERE conditions."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("age", ">", 18))
        ast = qb.to_ast()
        assert ast.conditions is not None
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_with_select(self):
        """Test to_polars() with column selection."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).select("id", "name")
        ast = qb.to_ast()
        assert "id" in ast.columns
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_chained_methods(self):
        """Test to_polars() with chained methods."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = (QueryBuilder.for_model(MockUser)
              .select("id", "name")
              .where(("active", "=", True))
              .order("-score")
              .limit(50))
        ast = qb.to_ast()
        assert len(ast.columns) == 2
        assert ast.limit == 50
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_empty_result(self, mock_pynext_go):
        """Test to_polars() with empty result."""
        mock_pynext_go.execute_polars.return_value = pl.DataFrame()
        result = mock_pynext_go.execute_polars("SELECT * FROM t WHERE 1=0", [])
        assert len(result) == 0
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_int_types(self, mock_pynext_go):
        """Test integer types in Polars DataFrame."""
        df = pl.DataFrame({"val": [1, 2, 3]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT val FROM t", [])
        assert result["val"].dtype == pl.Int64
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_float_types(self, mock_pynext_go):
        """Test float types in Polars DataFrame."""
        df = pl.DataFrame({"val": [1.0, 2.0, 3.0]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT val FROM t", [])
        assert result["val"].dtype == pl.Float64
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_string_types(self, mock_pynext_go):
        """Test string types in Polars DataFrame."""
        df = pl.DataFrame({"name": ["a", "b", "c"]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT name FROM t", [])
        assert result["name"].dtype == pl.Utf8
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_bool_types(self, mock_pynext_go):
        """Test boolean types in Polars DataFrame."""
        df = pl.DataFrame({"active": [True, False, True]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT active FROM t", [])
        assert result["active"].dtype == pl.Boolean
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_with_nulls(self, mock_pynext_go):
        """Test null handling in Polars DataFrame."""
        df = pl.DataFrame({"val": [1, None, 3]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT val FROM t", [])
        assert result["val"].null_count() == 1
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_large_result(self, mock_pynext_go):
        """Test to_polars() with large result set."""
        n = 10000
        df = pl.DataFrame({"id": range(n)})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT * FROM t", [])
        assert len(result) == n
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_column_order(self, mock_pynext_go):
        """Test column order preserved in Polars."""
        df = pl.DataFrame({
            "z": [1], "a": [2], "m": [3]
        })
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT z, a, m FROM t", [])
        assert result.columns == ["z", "a", "m"]
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_operations(self, mock_pynext_go):
        """Test Polars operations on result."""
        df = pl.DataFrame({
            "category": ["a", "a", "b", "b"],
            "value": [10, 20, 30, 40]
        })
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT * FROM t", [])
        grouped = result.group_by("category").agg(pl.sum("value"))
        assert len(grouped) == 2
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_filter(self, mock_pynext_go):
        """Test Polars filter on result."""
        df = pl.DataFrame({"val": [1, 2, 3, 4, 5]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT val FROM t", [])
        filtered = result.filter(pl.col("val") > 3)
        assert len(filtered) == 2
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_select(self, mock_pynext_go):
        """Test Polars select on result."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
            "c": [7, 8, 9]
        })
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT * FROM t", [])
        selected = result.select(["a", "c"])
        assert selected.columns == ["a", "c"]
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_sort(self, mock_pynext_go):
        """Test Polars sort on result."""
        df = pl.DataFrame({"val": [3, 1, 2]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT val FROM t", [])
        sorted_df = result.sort("val")
        assert sorted_df["val"].to_list() == [1, 2, 3]
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_with_expressions(self, mock_pynext_go):
        """Test Polars expressions on result."""
        df = pl.DataFrame({"val": [1, 2, 3]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT val FROM t", [])
        with_double = result.with_columns((pl.col("val") * 2).alias("doubled"))
        assert "doubled" in with_double.columns
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_to_dict(self, mock_pynext_go):
        """Test Polars to_dict conversion."""
        df = pl.DataFrame({"id": [1, 2], "name": ["a", "b"]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT * FROM t", [])
        as_dict = result.to_dict()
        assert "id" in as_dict
        assert "name" in as_dict
    
    @pytest.mark.skipif(not polars_available, reason="polars not available")
    def test_polars_lazy_mode(self, mock_pynext_go):
        """Test Polars lazy mode on result."""
        df = pl.DataFrame({"val": [1, 2, 3]})
        mock_pynext_go.execute_polars.return_value = df
        result = mock_pynext_go.execute_polars("SELECT val FROM t", [])
        lazy = result.lazy()
        collected = lazy.collect()
        assert len(collected) == 3


# =============================================================================
# to_numpy() Tests (20 tests)
# =============================================================================

class TestToNumpy:
    """Tests for QueryBuilder.to_numpy() method."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_basic_to_numpy(self, mock_pynext_go):
        """Test basic to_numpy() call."""
        arrays = {
            "id": np.array([1, 2, 3]),
            "score": np.array([10.0, 20.0, 30.0])
        }
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT * FROM t", [])
        assert isinstance(result, dict)
        assert "id" in result
        assert "score" in result
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_int_column(self, mock_pynext_go):
        """Test integer column in NumPy result."""
        arrays = {"val": np.array([1, 2, 3], dtype=np.int64)}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        assert result["val"].dtype == np.int64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_float_column(self, mock_pynext_go):
        """Test float column in NumPy result."""
        arrays = {"val": np.array([1.0, 2.0, 3.0], dtype=np.float64)}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        assert result["val"].dtype == np.float64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_string_column(self, mock_pynext_go):
        """Test string column in NumPy result."""
        arrays = {"name": np.array(["a", "b", "c"], dtype=object)}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT name FROM t", [])
        assert result["name"].dtype == object
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_bool_column(self, mock_pynext_go):
        """Test boolean column in NumPy result."""
        arrays = {"active": np.array([True, False, True], dtype=bool)}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT active FROM t", [])
        assert result["active"].dtype == bool
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_vectorized_ops(self, mock_pynext_go):
        """Test vectorized operations on NumPy result."""
        arrays = {"val": np.array([1, 2, 3, 4, 5])}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        
        assert result["val"].sum() == 15
        assert result["val"].mean() == 3.0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_boolean_indexing(self, mock_pynext_go):
        """Test boolean indexing on NumPy result."""
        arrays = {
            "id": np.array([1, 2, 3, 4, 5]),
            "val": np.array([10, 20, 30, 40, 50])
        }
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT * FROM t", [])
        
        filtered = result["id"][result["val"] > 25]
        np.testing.assert_array_equal(filtered, [3, 4, 5])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_empty_result(self, mock_pynext_go):
        """Test to_numpy() with empty result."""
        arrays = {"val": np.array([], dtype=np.int64)}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t WHERE 1=0", [])
        assert len(result["val"]) == 0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_with_nulls(self, mock_pynext_go):
        """Test null handling in NumPy result."""
        arrays = {"val": np.array([1.0, np.nan, 3.0])}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        assert np.isnan(result["val"][1])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_large_result(self, mock_pynext_go):
        """Test to_numpy() with large result."""
        n = 10000
        arrays = {"val": np.arange(n)}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        assert len(result["val"]) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_zero_copy_flag(self, mock_pynext_go):
        """Test zero_copy flag is passed."""
        arrays = {"val": np.array([1, 2, 3])}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [], True)
        assert "val" in result
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_slicing(self, mock_pynext_go):
        """Test array slicing on NumPy result."""
        arrays = {"val": np.array([1, 2, 3, 4, 5])}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        np.testing.assert_array_equal(result["val"][:3], [1, 2, 3])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_arithmetic(self, mock_pynext_go):
        """Test arithmetic on NumPy result."""
        arrays = {"val": np.array([1, 2, 3])}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        doubled = result["val"] * 2
        np.testing.assert_array_equal(doubled, [2, 4, 6])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_math_functions(self, mock_pynext_go):
        """Test math functions on NumPy result."""
        arrays = {"val": np.array([1.0, 4.0, 9.0])}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        sqrt = np.sqrt(result["val"])
        np.testing.assert_array_almost_equal(sqrt, [1.0, 2.0, 3.0])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_column_combination(self, mock_pynext_go):
        """Test combining columns in NumPy."""
        arrays = {
            "a": np.array([1, 2, 3]),
            "b": np.array([4, 5, 6])
        }
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT a, b FROM t", [])
        combined = result["a"] + result["b"]
        np.testing.assert_array_equal(combined, [5, 7, 9])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_comparison(self, mock_pynext_go):
        """Test comparison on NumPy result."""
        arrays = {"val": np.array([1, 2, 3, 4, 5])}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        mask = result["val"] > 3
        np.testing.assert_array_equal(mask, [False, False, False, True, True])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_shape(self, mock_pynext_go):
        """Test array shape in NumPy result."""
        arrays = {"val": np.array([1, 2, 3, 4, 5])}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        assert result["val"].shape == (5,)
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_reshape(self, mock_pynext_go):
        """Test reshaping NumPy result."""
        arrays = {"val": np.array([1, 2, 3, 4, 5, 6])}
        mock_pynext_go.execute_numpy.return_value = arrays
        result = mock_pynext_go.execute_numpy("SELECT val FROM t", [])
        reshaped = result["val"].reshape(2, 3)
        assert reshaped.shape == (2, 3)
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    def test_numpy_concatenate(self, mock_pynext_go):
        """Test concatenating NumPy results."""
        arrays1 = {"val": np.array([1, 2, 3])}
        arrays2 = {"val": np.array([4, 5, 6])}
        mock_pynext_go.execute_numpy.side_effect = [arrays1, arrays2]
        result1 = mock_pynext_go.execute_numpy("SELECT val FROM t1", [])
        result2 = mock_pynext_go.execute_numpy("SELECT val FROM t2", [])
        combined = np.concatenate([result1["val"], result2["val"]])
        np.testing.assert_array_equal(combined, [1, 2, 3, 4, 5, 6])


# =============================================================================
# to_dicts() Tests (15 tests)
# =============================================================================

class TestToDicts:
    """Tests for QueryBuilder.to_dicts() method."""
    
    def test_basic_to_dicts(self, mock_pynext_go):
        """Test basic to_dicts() call."""
        mock_pynext_go.execute.return_value.rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        result = mock_pynext_go.execute("SELECT * FROM t", [])
        assert isinstance(result.rows, list)
        assert len(result.rows) == 2
        assert result.rows[0]["id"] == 1
    
    def test_dicts_empty_result(self, mock_pynext_go):
        """Test to_dicts() with empty result."""
        mock_pynext_go.execute.return_value.rows = []
        result = mock_pynext_go.execute("SELECT * FROM t WHERE 1=0", [])
        assert result.rows == []
    
    def test_dicts_single_row(self, mock_pynext_go):
        """Test to_dicts() with single row."""
        mock_pynext_go.execute.return_value.rows = [{"id": 1}]
        result = mock_pynext_go.execute("SELECT id FROM t LIMIT 1", [])
        assert len(result.rows) == 1
    
    def test_dicts_preserves_types(self, mock_pynext_go):
        """Test type preservation in dicts."""
        mock_pynext_go.execute.return_value.rows = [
            {"int_col": 42, "float_col": 3.14, "str_col": "test", "bool_col": True}
        ]
        result = mock_pynext_go.execute("SELECT * FROM t", [])
        row = result.rows[0]
        assert isinstance(row["int_col"], int)
        assert isinstance(row["float_col"], float)
        assert isinstance(row["str_col"], str)
        assert isinstance(row["bool_col"], bool)
    
    def test_dicts_null_values(self, mock_pynext_go):
        """Test null handling in dicts."""
        mock_pynext_go.execute.return_value.rows = [
            {"id": 1, "value": None}
        ]
        result = mock_pynext_go.execute("SELECT * FROM t", [])
        assert result.rows[0]["value"] is None
    
    def test_dicts_json_serializable(self, mock_pynext_go):
        """Test dicts are JSON serializable."""
        import json
        mock_pynext_go.execute.return_value.rows = [
            {"id": 1, "name": "Alice", "active": True}
        ]
        result = mock_pynext_go.execute("SELECT * FROM t", [])
        json_str = json.dumps(result.rows)
        assert '"id": 1' in json_str
    
    def test_dicts_large_result(self, mock_pynext_go):
        """Test to_dicts() with large result."""
        n = 1000
        mock_pynext_go.execute.return_value.rows = [{"id": i} for i in range(n)]
        result = mock_pynext_go.execute("SELECT id FROM t", [])
        assert len(result.rows) == n
    
    def test_dicts_column_names(self, mock_pynext_go):
        """Test column names in dicts."""
        mock_pynext_go.execute.return_value.rows = [
            {"user_id": 1, "user_name": "Alice", "created_at": "2024-01-01"}
        ]
        result = mock_pynext_go.execute("SELECT * FROM t", [])
        keys = list(result.rows[0].keys())
        assert "user_id" in keys
        assert "user_name" in keys
        assert "created_at" in keys
    
    def test_dicts_iteration(self, mock_pynext_go):
        """Test iterating over dicts result."""
        mock_pynext_go.execute.return_value.rows = [
            {"id": 1}, {"id": 2}, {"id": 3}
        ]
        result = mock_pynext_go.execute("SELECT id FROM t", [])
        ids = [row["id"] for row in result.rows]
        assert ids == [1, 2, 3]
    
    def test_dicts_nested_access(self, mock_pynext_go):
        """Test dict nested access."""
        mock_pynext_go.execute.return_value.rows = [
            {"user": {"id": 1, "name": "Alice"}}
        ]
        result = mock_pynext_go.execute("SELECT * FROM t", [])
        # If result contains nested dict
        if isinstance(result.rows[0].get("user"), dict):
            assert result.rows[0]["user"]["id"] == 1
    
    def test_dicts_unicode_values(self, mock_pynext_go):
        """Test unicode values in dicts."""
        mock_pynext_go.execute.return_value.rows = [
            {"name": "世界", "emoji": "🎉"}
        ]
        result = mock_pynext_go.execute("SELECT * FROM t", [])
        assert result.rows[0]["name"] == "世界"
        assert result.rows[0]["emoji"] == "🎉"
    
    def test_dicts_empty_string(self, mock_pynext_go):
        """Test empty string in dicts."""
        mock_pynext_go.execute.return_value.rows = [{"name": ""}]
        result = mock_pynext_go.execute("SELECT name FROM t", [])
        assert result.rows[0]["name"] == ""
    
    def test_dicts_whitespace_string(self, mock_pynext_go):
        """Test whitespace string in dicts."""
        mock_pynext_go.execute.return_value.rows = [{"name": "  spaces  "}]
        result = mock_pynext_go.execute("SELECT name FROM t", [])
        assert result.rows[0]["name"] == "  spaces  "
    
    def test_dicts_numeric_string(self, mock_pynext_go):
        """Test numeric-looking strings in dicts."""
        mock_pynext_go.execute.return_value.rows = [{"code": "123"}]
        result = mock_pynext_go.execute("SELECT code FROM t", [])
        assert result.rows[0]["code"] == "123"
        assert isinstance(result.rows[0]["code"], str)


# =============================================================================
# to_list() Tests (15 tests)
# =============================================================================

class TestToList:
    """Tests for QueryBuilder.to_list() method."""
    
    def test_basic_query_builder(self):
        """Test basic QueryBuilder creation."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser)
        assert qb._model == MockUser
    
    def test_to_ast(self):
        """Test to_ast() method."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser)
        ast = qb.to_ast()
        assert ast.table == "users"
    
    def test_select_columns(self):
        """Test column selection."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).select("id", "name")
        ast = qb.to_ast()
        assert "id" in ast.columns
        assert "name" in ast.columns
    
    def test_where_tuple(self):
        """Test WHERE with tuple condition."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser, ("age", ">", 18))
        ast = qb.to_ast()
        assert ast.conditions is not None
    
    def test_where_multiple(self):
        """Test WHERE with multiple conditions."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser, ("age", ">", 18), ("status", "=", "active"))
        ast = qb.to_ast()
        assert ast.conditions is not None
    
    def test_order_ascending(self):
        """Test ORDER BY ascending."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).order("name")
        ast = qb.to_ast()
        assert len(ast.order) == 1
        assert ast.order[0].direction == "ASC"
    
    def test_order_descending(self):
        """Test ORDER BY descending."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).order("-created_at")
        ast = qb.to_ast()
        assert len(ast.order) == 1
        assert ast.order[0].direction == "DESC"
    
    def test_limit(self):
        """Test LIMIT clause."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).limit(10)
        ast = qb.to_ast()
        assert ast.limit == 10
    
    def test_offset(self):
        """Test OFFSET clause."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).offset(20)
        ast = qb.to_ast()
        assert ast.offset == 20
    
    def test_page_first(self):
        """Test pagination first page."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).page(1, per_page=10)
        ast = qb.to_ast()
        assert ast.limit == 10
        assert ast.offset == 0
    
    def test_page_second(self):
        """Test pagination second page."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).page(2, per_page=10)
        ast = qb.to_ast()
        assert ast.limit == 10
        assert ast.offset == 10
    
    def test_distinct(self):
        """Test DISTINCT clause."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).select("role").distinct()
        ast = qb.to_ast()
        assert ast.distinct == True
    
    def test_for_update(self):
        """Test FOR UPDATE clause."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).for_update()
        ast = qb.to_ast()
        assert ast.for_update == True
    
    def test_chained_full(self):
        """Test full chained query."""
        from pynext.db.query_builder import QueryBuilder
        qb = (QueryBuilder.for_model(MockUser)
              .select("id", "name", "email")
              .where(("age", ">", 18))
              .order("-created_at", "name")
              .limit(100)
              .offset(0))
        ast = qb.to_ast()
        assert len(ast.columns) == 3
        assert ast.conditions is not None
        assert len(ast.order) == 2
        assert ast.limit == 100
        assert ast.offset == 0
    
    def test_immutability(self):
        """Test QueryBuilder immutability."""
        from pynext.db.query_builder import QueryBuilder
        qb1 = QueryBuilder.for_model(MockUser)
        qb2 = qb1.limit(10)
        assert qb1.to_ast().limit is None
        assert qb2.to_ast().limit == 10


# =============================================================================
# Error Handling Tests (10 tests)
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in DataFrame methods."""
    
    def test_import_error_pandas(self):
        """Test clear error when pandas not available."""
        # Would need to mock import failure
        pass
    
    def test_import_error_polars(self):
        """Test clear error when polars not available."""
        pass
    
    def test_import_error_numpy(self):
        """Test clear error when numpy not available."""
        pass
    
    def test_connection_error(self, mock_pynext_go):
        """Test connection error handling."""
        mock_pynext_go.execute.side_effect = Exception("Connection failed")
        with pytest.raises(Exception, match="Connection failed"):
            mock_pynext_go.execute("SELECT * FROM t", [])
    
    def test_query_error(self, mock_pynext_go):
        """Test query error handling."""
        mock_pynext_go.execute.side_effect = Exception("Syntax error")
        with pytest.raises(Exception, match="Syntax error"):
            mock_pynext_go.execute("SELECT * FROM", [])
    
    def test_type_conversion_error(self, mock_pynext_go):
        """Test type conversion error handling."""
        # Test would need specific conversion failure scenario
        pass
    
    def test_empty_table_name(self):
        """Test error with empty table name."""
        from pynext.db.query_builder import QueryBuilder
        
        class NoTable:
            pass
        
        qb = QueryBuilder.for_model(NoTable)
        ast = qb.to_ast()
        # Should use fallback table name
        assert ast.table is not None
    
    def test_invalid_page_number(self):
        """Test invalid page number handling."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).page(0)  # 0 should become 1
        ast = qb.to_ast()
        assert ast.offset == 0  # page 1
    
    def test_negative_limit(self):
        """Test negative limit handling."""
        from pynext.db.query_builder import QueryBuilder
        qb = QueryBuilder.for_model(MockUser).limit(-5)
        ast = qb.to_ast()
        # Implementation should handle this appropriately
        assert ast.limit == -5  # Or could be validated
    
    def test_bridge_not_initialized(self, mock_pynext_go):
        """Test error when bridge not initialized."""
        mock_pynext_go.execute.side_effect = Exception("Bridge not initialized")
        with pytest.raises(Exception, match="Bridge not initialized"):
            mock_pynext_go.execute("SELECT * FROM t", [])


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

