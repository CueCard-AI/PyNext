"""
Unit tests for Go Bridge result types.

Tests QueryResult and BatchResult classes.
"""

import pytest
from typing import Any

from pynext_go.result import QueryResult, BatchResult


class TestQueryResultBasic:
    """Basic QueryResult tests."""
    
    def test_empty_success_result(self):
        """Empty successful result."""
        result = QueryResult(success=True)
        assert result.success is True
        assert result.error == ""
        assert result.rows == []
        assert result.columns == []
        assert len(result) == 0
        assert bool(result) is True
    
    def test_failed_result(self):
        """Failed result with error."""
        result = QueryResult(success=False, error="syntax error")
        assert result.success is False
        assert result.error == "syntax error"
        assert bool(result) is False
    
    def test_result_with_data(self):
        """Result with rows and columns."""
        result = QueryResult(
            success=True,
            rows=[[1, "Alice"], [2, "Bob"]],
            columns=["id", "name"],
            rows_affected=2,
            duration_ms=5.5,
        )
        assert len(result) == 2
        assert result.columns == ["id", "name"]
        assert result.rows_affected == 2
        assert result.duration_ms == 5.5


class TestQueryResultIteration:
    """QueryResult iteration tests."""
    
    def test_iterate_rows(self):
        """Iterate over rows as lists."""
        result = QueryResult(
            success=True,
            rows=[[1, "a"], [2, "b"], [3, "c"]],
            columns=["id", "val"],
        )
        
        collected = list(result)
        assert len(collected) == 3
        assert collected[0] == [1, "a"]
        assert collected[2] == [3, "c"]
    
    def test_getitem(self):
        """Access rows by index."""
        result = QueryResult(
            success=True,
            rows=[[1], [2], [3]],
            columns=["id"],
        )
        
        assert result[0] == [1]
        assert result[1] == [2]
        assert result[-1] == [3]
    
    def test_iter_dicts(self):
        """Iterate over rows as dicts."""
        result = QueryResult(
            success=True,
            rows=[[1, "Alice"], [2, "Bob"]],
            columns=["id", "name"],
        )
        
        dicts = list(result.iter_dicts())
        assert len(dicts) == 2
        assert dicts[0] == {"id": 1, "name": "Alice"}
        assert dicts[1] == {"id": 2, "name": "Bob"}


class TestQueryResultProperties:
    """QueryResult property tests."""
    
    def test_column_count(self):
        """column_count should return number of columns."""
        result = QueryResult(success=True, columns=["a", "b", "c"])
        assert result.column_count == 3
        
        empty = QueryResult(success=True)
        assert empty.column_count == 0
    
    def test_row_count(self):
        """row_count should return number of rows."""
        result = QueryResult(success=True, rows=[[1], [2], [3]])
        assert result.row_count == 3
        
        empty = QueryResult(success=True)
        assert empty.row_count == 0
    
    def test_is_empty(self):
        """is_empty should be True when no rows."""
        empty = QueryResult(success=True, rows=[])
        assert empty.is_empty is True
        
        with_data = QueryResult(success=True, rows=[[1]])
        assert with_data.is_empty is False


class TestQueryResultAccessMethods:
    """QueryResult data access method tests."""
    
    def test_first(self):
        """first should return first row or None."""
        result = QueryResult(success=True, rows=[[1, "a"], [2, "b"]], columns=["id", "val"])
        assert result.first() == [1, "a"]
        
        empty = QueryResult(success=True)
        assert empty.first() is None
    
    def test_first_dict(self):
        """first_dict should return first row as dict."""
        result = QueryResult(success=True, rows=[[1, "a"]], columns=["id", "val"])
        assert result.first_dict() == {"id": 1, "val": "a"}
        
        empty = QueryResult(success=True)
        assert empty.first_dict() is None
    
    def test_one(self):
        """one should return single row or raise."""
        single = QueryResult(success=True, rows=[[42]], columns=["num"])
        assert single.one() == [42]
    
    def test_one_empty_raises(self):
        """one should raise on empty result."""
        empty = QueryResult(success=True)
        with pytest.raises(ValueError, match="Expected one row, got none"):
            empty.one()
    
    def test_one_multiple_raises(self):
        """one should raise on multiple rows."""
        multiple = QueryResult(success=True, rows=[[1], [2]])
        with pytest.raises(ValueError, match="Expected one row, got 2"):
            multiple.one()
    
    def test_one_dict(self):
        """one_dict should return single row as dict."""
        single = QueryResult(success=True, rows=[[42, "x"]], columns=["id", "val"])
        assert single.one_dict() == {"id": 42, "val": "x"}
    
    def test_scalar(self):
        """scalar should return single value."""
        result = QueryResult(success=True, rows=[[42]], columns=["count"])
        assert result.scalar() == 42
    
    def test_scalar_empty_raises(self):
        """scalar should raise on empty result."""
        empty = QueryResult(success=True)
        with pytest.raises(ValueError, match="No rows"):
            empty.scalar()
    
    def test_scalar_no_columns_raises(self):
        """scalar should raise when row has no columns."""
        result = QueryResult(success=True, rows=[[]])
        with pytest.raises(ValueError, match="No columns"):
            result.scalar()
    
    def test_column(self):
        """column should return all values for a column."""
        result = QueryResult(
            success=True,
            rows=[[1, "a"], [2, "b"], [3, "c"]],
            columns=["id", "val"],
        )
        
        assert result.column("id") == [1, 2, 3]
        assert result.column("val") == ["a", "b", "c"]
    
    def test_column_not_found_raises(self):
        """column should raise KeyError for unknown column."""
        result = QueryResult(success=True, columns=["id", "name"])
        with pytest.raises(KeyError, match="Column not found: unknown"):
            result.column("unknown")


class TestQueryResultConversion:
    """QueryResult conversion method tests."""
    
    def test_to_dicts(self):
        """to_dicts should convert all rows to list of dicts."""
        result = QueryResult(
            success=True,
            rows=[[1, "a"], [2, "b"]],
            columns=["id", "val"],
        )
        
        dicts = result.to_dicts()
        assert len(dicts) == 2
        assert dicts[0] == {"id": 1, "val": "a"}
        assert dicts[1] == {"id": 2, "val": "b"}
    
    def test_to_dicts_empty(self):
        """to_dicts on empty result should return empty list."""
        result = QueryResult(success=True)
        assert result.to_dicts() == []
    
    def test_to_pandas_not_installed(self):
        """to_pandas should raise ImportError if pandas not available."""
        # This test may pass or fail depending on environment
        result = QueryResult(success=True, rows=[[1]], columns=["id"])
        try:
            result.to_pandas()
            # If pandas is installed, verify it works
            import pandas as pd
            df = result.to_pandas()
            assert isinstance(df, pd.DataFrame)
        except ImportError:
            pass  # Expected when pandas not installed
    
    def test_to_polars_not_installed(self):
        """to_polars should raise ImportError if polars not available."""
        result = QueryResult(success=True, rows=[[1]], columns=["id"])
        try:
            result.to_polars()
            # If polars is installed, verify it works
            import polars as pl
            df = result.to_polars()
            assert isinstance(df, pl.DataFrame)
        except ImportError:
            pass  # Expected when polars not installed


class TestQueryResultFromDict:
    """QueryResult.from_dict tests."""
    
    def test_from_dict_minimal(self):
        """from_dict with minimal data."""
        d = {"success": True}
        result = QueryResult.from_dict(d)
        assert result.success is True
        assert result.rows == []
    
    def test_from_dict_full(self):
        """from_dict with all fields."""
        d = {
            "success": True,
            "error": "",
            "rows": [[1, "test"]],
            "columns": ["id", "name"],
            "rows_affected": 1,
            "duration_ms": 2.5,
            "cached": True,
        }
        result = QueryResult.from_dict(d)
        
        assert result.success is True
        assert result.rows == [[1, "test"]]
        assert result.columns == ["id", "name"]
        assert result.duration_ms == 2.5
        assert result.cached is True
    
    def test_from_dict_failed(self):
        """from_dict with error."""
        d = {"success": False, "error": "connection lost"}
        result = QueryResult.from_dict(d)
        
        assert result.success is False
        assert result.error == "connection lost"


class TestBatchResultBasic:
    """Basic BatchResult tests."""
    
    def test_empty_success_batch(self):
        """Empty successful batch."""
        batch = BatchResult(success=True)
        assert batch.success is True
        assert batch.results == []
        assert len(batch) == 0
        assert bool(batch) is True
    
    def test_failed_batch(self):
        """Failed batch with error."""
        batch = BatchResult(success=False, error="transaction failed")
        assert batch.success is False
        assert batch.error == "transaction failed"
        assert bool(batch) is False
    
    def test_batch_with_results(self):
        """Batch with individual results."""
        results = [
            QueryResult(success=True, rows_affected=1),
            QueryResult(success=True, rows_affected=2),
            QueryResult(success=True, rows_affected=3),
        ]
        batch = BatchResult(success=True, results=results, duration_ms=10.0)
        
        assert len(batch) == 3
        assert batch.duration_ms == 10.0


class TestBatchResultIteration:
    """BatchResult iteration tests."""
    
    def test_iterate_results(self):
        """Iterate over individual results."""
        results = [
            QueryResult(success=True, rows_affected=1),
            QueryResult(success=True, rows_affected=2),
        ]
        batch = BatchResult(success=True, results=results)
        
        collected = list(batch)
        assert len(collected) == 2
        assert collected[0].rows_affected == 1
    
    def test_getitem(self):
        """Access results by index."""
        results = [
            QueryResult(success=True, rows_affected=1),
            QueryResult(success=True, rows_affected=2),
        ]
        batch = BatchResult(success=True, results=results)
        
        assert batch[0].rows_affected == 1
        assert batch[1].rows_affected == 2
        assert batch[-1].rows_affected == 2


class TestBatchResultProperties:
    """BatchResult property tests."""
    
    def test_total_rows_affected(self):
        """total_rows_affected should sum all results."""
        results = [
            QueryResult(success=True, rows_affected=5),
            QueryResult(success=True, rows_affected=10),
            QueryResult(success=True, rows_affected=3),
        ]
        batch = BatchResult(success=True, results=results)
        
        assert batch.total_rows_affected == 18
    
    def test_total_rows_affected_empty(self):
        """total_rows_affected on empty batch should be 0."""
        batch = BatchResult(success=True)
        assert batch.total_rows_affected == 0
    
    def test_failed_count(self):
        """failed_count should count failed results."""
        results = [
            QueryResult(success=True),
            QueryResult(success=False, error="err1"),
            QueryResult(success=True),
            QueryResult(success=False, error="err2"),
        ]
        batch = BatchResult(success=False, results=results)
        
        assert batch.failed_count == 2
    
    def test_succeeded_count(self):
        """succeeded_count should count successful results."""
        results = [
            QueryResult(success=True),
            QueryResult(success=False),
            QueryResult(success=True),
        ]
        batch = BatchResult(success=False, results=results)
        
        assert batch.succeeded_count == 2
    
    def test_failed_queries(self):
        """failed_queries should return failed results with indices."""
        results = [
            QueryResult(success=True),
            QueryResult(success=False, error="err1"),
            QueryResult(success=True),
            QueryResult(success=False, error="err2"),
        ]
        batch = BatchResult(success=False, results=results)
        
        failed = batch.failed_queries()
        assert len(failed) == 2
        assert failed[0] == (1, results[1])
        assert failed[1] == (3, results[3])


class TestBatchResultFromDict:
    """BatchResult.from_dict tests."""
    
    def test_from_dict_minimal(self):
        """from_dict with minimal data."""
        d = {"success": True}
        batch = BatchResult.from_dict(d)
        assert batch.success is True
        assert batch.results == []
    
    def test_from_dict_full(self):
        """from_dict with all fields."""
        d = {
            "success": True,
            "error": "",
            "results": [
                {"success": True, "rows_affected": 1},
                {"success": True, "rows_affected": 2},
            ],
            "duration_ms": 5.0,
        }
        batch = BatchResult.from_dict(d)
        
        assert batch.success is True
        assert len(batch.results) == 2
        assert batch.results[0].rows_affected == 1
        assert batch.duration_ms == 5.0
    
    def test_from_dict_mixed_success(self):
        """from_dict with mixed success/failure."""
        d = {
            "success": False,
            "error": "query 2 failed",
            "results": [
                {"success": True, "rows_affected": 1},
                {"success": False, "error": "syntax error"},
            ],
        }
        batch = BatchResult.from_dict(d)
        
        assert batch.success is False
        assert batch.error == "query 2 failed"
        assert batch.results[1].error == "syntax error"


class TestQueryResultEdgeCases:
    """Edge case tests."""
    
    def test_large_result(self):
        """Result with many rows."""
        rows = [[i, f"value_{i}"] for i in range(10000)]
        result = QueryResult(success=True, rows=rows, columns=["id", "val"])
        
        assert len(result) == 10000
        assert result.scalar() == 0
        assert result.column("id")[-1] == 9999
    
    def test_wide_result(self):
        """Result with many columns."""
        columns = [f"col_{i}" for i in range(100)]
        rows = [[i for i in range(100)]]
        result = QueryResult(success=True, rows=rows, columns=columns)
        
        assert result.column_count == 100
        d = result.first_dict()
        assert len(d) == 100
    
    def test_null_values(self):
        """Result with None/null values."""
        result = QueryResult(
            success=True,
            rows=[[1, None], [None, "b"]],
            columns=["id", "val"],
        )
        
        assert result.first() == [1, None]
        assert result[1] == [None, "b"]
        
        dicts = result.to_dicts()
        assert dicts[0]["val"] is None
        assert dicts[1]["id"] is None
    
    def test_mixed_types(self):
        """Result with mixed types in same column."""
        result = QueryResult(
            success=True,
            rows=[[1], ["string"], [3.14], [None]],
            columns=["mixed"],
        )
        
        col = result.column("mixed")
        assert col == [1, "string", 3.14, None]
    
    def test_unicode_values(self):
        """Result with unicode values."""
        result = QueryResult(
            success=True,
            rows=[["日本語"], ["emoji 🎉"]],
            columns=["text"],
        )
        
        assert result.column("text") == ["日本語", "emoji 🎉"]
    
    def test_empty_strings(self):
        """Result with empty string values."""
        result = QueryResult(
            success=True,
            rows=[[""], ["not empty"], [""]], 
            columns=["val"],
        )
        
        assert result.column("val")[0] == ""
        assert result.column("val")[1] == "not empty"

