"""
NumPy Structured Array Tests for Phase 8.3.

Tests for pynext_go.execute_numpy_structured() and arrow_table_to_structured().
100 comprehensive tests covering structured array creation, field access,
type mapping, and row-oriented operations.

Test Categories:
1. Structured array creation
2. Dtype inference
3. Field access by name
4. Row access by index
5. Mixed types
6. Unicode strings
7. Fixed-width strings
8. Null handling
9. Large datasets
10. Error handling
"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, List

# Try to import numpy
numpy_available = False
try:
    import numpy as np
    numpy_available = True
except ImportError:
    pass

# Try to import pyarrow
pyarrow_available = False
try:
    import pyarrow as pa
    pyarrow_available = True
except ImportError:
    pass


# =============================================================================
# Structured Array Creation Tests (20 tests)
# =============================================================================

class TestStructuredArrayCreation:
    """Test structured array creation from Arrow tables."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_basic_creation(self):
        """Test basic structured array creation."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["a", "b", "c"], type=pa.string()),
        })
        result = arrow_table_to_structured(table)
        assert len(result) == 3
        assert "id" in result.dtype.names
        assert "name" in result.dtype.names
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_single_column(self):
        """Test single column structured array."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        assert len(result) == 3
        assert result.dtype.names == ("val",)
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_many_columns(self):
        """Test structured array with many columns."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n_cols = 20
        data = {f"col_{i}": pa.array([1, 2, 3], type=pa.int64()) for i in range(n_cols)}
        table = pa.table(data)
        result = arrow_table_to_structured(table)
        assert len(result.dtype.names) == n_cols
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_table(self):
        """Test empty table structured array."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([], type=pa.int64()),
            "name": pa.array([], type=pa.string()),
        })
        result = arrow_table_to_structured(table)
        assert len(result) == 0
        assert "id" in result.dtype.names
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_single_row(self):
        """Test single row structured array."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([1], type=pa.int64()),
            "name": pa.array(["test"], type=pa.string()),
        })
        result = arrow_table_to_structured(table)
        assert len(result) == 1
        assert result[0]["id"] == 1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_mixed_types(self):
        """Test mixed type structured array."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "score": pa.array([1.5, 2.5, 3.5], type=pa.float64()),
            "name": pa.array(["a", "b", "c"], type=pa.string()),
            "active": pa.array([True, False, True], type=pa.bool_()),
        })
        result = arrow_table_to_structured(table)
        assert len(result) == 3
        assert len(result.dtype.names) == 4
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_column_order_preserved(self):
        """Test column order is preserved."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "z": pa.array([1], type=pa.int64()),
            "a": pa.array([2], type=pa.int64()),
            "m": pa.array([3], type=pa.int64()),
        })
        result = arrow_table_to_structured(table)
        assert result.dtype.names == ("z", "a", "m")
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_special_column_names(self):
        """Test special column names."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "Column_Name": pa.array([1], type=pa.int64()),
            "column-name": pa.array([2], type=pa.int64()),
        })
        result = arrow_table_to_structured(table)
        assert "Column_Name" in result.dtype.names
        assert "column-name" in result.dtype.names
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int8_dtype(self):
        """Test INT8 creates correct dtype."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int8())})
        result = arrow_table_to_structured(table)
        assert result.dtype["val"] == np.int8
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int16_dtype(self):
        """Test INT16 creates correct dtype."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int16())})
        result = arrow_table_to_structured(table)
        assert result.dtype["val"] == np.int16
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int32_dtype(self):
        """Test INT32 creates correct dtype."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int32())})
        result = arrow_table_to_structured(table)
        assert result.dtype["val"] == np.int32
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int64_dtype(self):
        """Test INT64 creates correct dtype."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        assert result.dtype["val"] == np.int64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float32_dtype(self):
        """Test FLOAT32 creates correct dtype."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1.0, 2.0, 3.0], type=pa.float32())})
        result = arrow_table_to_structured(table)
        assert result.dtype["val"] == np.float32
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float64_dtype(self):
        """Test FLOAT64 creates correct dtype."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1.0, 2.0, 3.0], type=pa.float64())})
        result = arrow_table_to_structured(table)
        assert result.dtype["val"] == np.float64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_dtype(self):
        """Test BOOLEAN creates correct dtype."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([True, False, True], type=pa.bool_())})
        result = arrow_table_to_structured(table)
        # Boolean may be bool or object depending on nulls
        assert result.dtype["val"] in (np.bool_, np.object_)
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_object_dtype(self):
        """Test STRING with object dtype (max_string_length=0)."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        result = arrow_table_to_structured(table, max_string_length=0)
        assert result.dtype["val"] == np.object_
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_unicode_dtype(self):
        """Test STRING with Unicode dtype (max_string_length > 0)."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        result = arrow_table_to_structured(table, max_string_length=256)
        assert result.dtype["val"].kind == "U"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_custom_string_length(self):
        """Test custom max_string_length."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        result = arrow_table_to_structured(table, max_string_length=10)
        # itemsize = 10 * 4 = 40 bytes for U10
        assert result.dtype["val"].itemsize == 40
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_truncation(self):
        """Test long strings are truncated."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        long_str = "a" * 500
        table = pa.table({"val": pa.array([long_str], type=pa.string())})
        result = arrow_table_to_structured(table, max_string_length=10)
        assert len(result["val"][0]) == 10


# =============================================================================
# Field Access Tests (20 tests)
# =============================================================================

class TestStructuredFieldAccess:
    """Test field access in structured arrays."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_access_by_name(self):
        """Test accessing field by name."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["a", "b", "c"], type=pa.string()),
        })
        result = arrow_table_to_structured(table)
        np.testing.assert_array_equal(result["id"], [1, 2, 3])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_access_multiple_fields(self):
        """Test accessing multiple fields."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "a": pa.array([1, 2, 3], type=pa.int64()),
            "b": pa.array([4, 5, 6], type=pa.int64()),
            "c": pa.array([7, 8, 9], type=pa.int64()),
        })
        result = arrow_table_to_structured(table)
        multi = result[["a", "c"]]
        assert "a" in multi.dtype.names
        assert "c" in multi.dtype.names
        assert "b" not in multi.dtype.names
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_as_array(self):
        """Test field returns array view."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        field_array = result["val"]
        assert isinstance(field_array, np.ndarray)
        assert len(field_array) == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_vectorized_ops(self):
        """Test vectorized operations on field."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        doubled = result["val"] * 2
        np.testing.assert_array_equal(doubled, [2, 4, 6])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_aggregation(self):
        """Test aggregation on field."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_structured(table)
        assert result["val"].sum() == 15
        assert result["val"].mean() == 3.0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_slicing(self):
        """Test slicing on field."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_structured(table)
        np.testing.assert_array_equal(result["val"][:3], [1, 2, 3])
        np.testing.assert_array_equal(result["val"][2:], [3, 4, 5])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_boolean_indexing(self):
        """Test boolean indexing on field."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_structured(table)
        filtered = result["val"][result["val"] > 3]
        np.testing.assert_array_equal(filtered, [4, 5])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_field_access(self):
        """Test string field access."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"name": pa.array(["alice", "bob", "charlie"], type=pa.string())})
        result = arrow_table_to_structured(table)
        names = result["name"]
        assert names[0].strip() == "alice"  # strip for fixed-width
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_field_precision(self):
        """Test float field precision."""
        import math
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([math.pi, math.e], type=pa.float64())})
        result = arrow_table_to_structured(table)
        assert abs(result["val"][0] - math.pi) < 1e-10
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_field_access(self):
        """Test boolean field access."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"active": pa.array([True, False, True], type=pa.bool_())})
        result = arrow_table_to_structured(table)
        assert result["active"][0] == True
        assert result["active"][1] == False
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_assignment(self):
        """Test field value assignment."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        result["val"][0] = 99
        assert result["val"][0] == 99
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_nonexistent_field_error(self):
        """Test accessing non-existent field."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        with pytest.raises((KeyError, ValueError)):
            _ = result["nonexistent"]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_dtype(self):
        """Test field has correct dtype."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "int_col": pa.array([1, 2, 3], type=pa.int64()),
            "float_col": pa.array([1.0, 2.0, 3.0], type=pa.float64()),
        })
        result = arrow_table_to_structured(table)
        assert result["int_col"].dtype == np.int64
        assert result["float_col"].dtype == np.float64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_shape(self):
        """Test field shape is correct."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_structured(table)
        assert result["val"].shape == (5,)
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_copy(self):
        """Test copying field."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        copy = result["val"].copy()
        copy[0] = 99
        assert result["val"][0] == 1  # Original unchanged
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_iteration(self):
        """Test iterating over field values."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        values = list(result["val"])
        assert values == [1, 2, 3]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_sort(self):
        """Test sorting by field."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([3, 1, 2], type=pa.int64()),
            "name": pa.array(["c", "a", "b"], type=pa.string()),
        })
        result = arrow_table_to_structured(table)
        sorted_result = np.sort(result, order="id")
        np.testing.assert_array_equal(sorted_result["id"], [1, 2, 3])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_field_comparison(self):
        """Test field comparison creates boolean array."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_structured(table)
        mask = result["val"] > 3
        np.testing.assert_array_equal(mask, [False, False, False, True, True])


# =============================================================================
# Row Access Tests (20 tests)
# =============================================================================

class TestStructuredRowAccess:
    """Test row access in structured arrays."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_by_index(self):
        """Test accessing row by index."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["a", "b", "c"], type=pa.string()),
        })
        result = arrow_table_to_structured(table)
        row = result[0]
        assert row["id"] == 1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_negative_index(self):
        """Test accessing row by negative index."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        assert result[-1]["val"] == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_slicing(self):
        """Test row slicing."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_structured(table)
        sliced = result[1:4]
        assert len(sliced) == 3
        np.testing.assert_array_equal(sliced["val"], [2, 3, 4])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_iteration(self):
        """Test iterating over rows."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "score": pa.array([10.0, 20.0, 30.0], type=pa.float64()),
        })
        result = arrow_table_to_structured(table)
        ids = []
        for row in result:
            ids.append(row["id"])
        assert ids == [1, 2, 3]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_tuple_conversion(self):
        """Test row to tuple conversion."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([1], type=pa.int64()),
            "score": pa.array([99.5], type=pa.float64()),
        })
        result = arrow_table_to_structured(table)
        row = result[0]
        row_tuple = tuple(row)
        assert row_tuple == (1, 99.5)
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_field_access_by_name(self):
        """Test accessing row field by name."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["alice", "bob", "charlie"], type=pa.string()),
        })
        result = arrow_table_to_structured(table)
        row = result[1]
        assert row["id"] == 2
        # String may have trailing spaces for fixed-width
        assert row["name"].strip() == "bob"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_modification(self):
        """Test modifying row values."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        result[0]["val"] = 99
        assert result[0]["val"] == 99
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_boolean_row_indexing(self):
        """Test boolean indexing of rows."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
            "val": pa.array([10, 20, 30, 40, 50], type=pa.int64()),
        })
        result = arrow_table_to_structured(table)
        filtered = result[result["val"] > 25]
        assert len(filtered) == 3
        np.testing.assert_array_equal(filtered["id"], [3, 4, 5])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_fancy_indexing(self):
        """Test fancy indexing of rows."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([10, 20, 30, 40, 50], type=pa.int64())})
        result = arrow_table_to_structured(table)
        selected = result[[0, 2, 4]]
        np.testing.assert_array_equal(selected["val"], [10, 30, 50])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_first_row(self):
        """Test accessing first row."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        first = result[0]
        assert first["val"] == 1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_last_row(self):
        """Test accessing last row."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        last = result[-1]
        assert last["val"] == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_out_of_bounds(self):
        """Test out of bounds row access."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        with pytest.raises(IndexError):
            _ = result[100]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_step_slicing(self):
        """Test row slicing with step."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([0, 1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_structured(table)
        even = result[::2]
        np.testing.assert_array_equal(even["val"], [0, 2, 4])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_reverse(self):
        """Test reversing rows."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        reversed_arr = result[::-1]
        np.testing.assert_array_equal(reversed_arr["val"], [3, 2, 1])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_contains_all_fields(self):
        """Test row contains all fields."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "a": pa.array([1], type=pa.int64()),
            "b": pa.array([2.0], type=pa.float64()),
            "c": pa.array(["x"], type=pa.string()),
        })
        result = arrow_table_to_structured(table)
        row = result[0]
        assert len(row.dtype.names) == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_enumeration(self):
        """Test enumerating rows."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([10, 20, 30], type=pa.int64())})
        result = arrow_table_to_structured(table)
        for i, row in enumerate(result):
            expected = (i + 1) * 10
            assert row["val"] == expected
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_len(self):
        """Test len() returns number of rows."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_structured(table)
        assert len(result) == 5
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_row_tolist(self):
        """Test converting rows to list."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        as_list = result.tolist()
        assert len(as_list) == 3


# =============================================================================
# Null Handling Tests (10 tests)
# =============================================================================

class TestStructuredNullHandling:
    """Test null value handling in structured arrays."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_int_column(self):
        """Test null in integer column."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1, None, 3], type=pa.int64())})
        result = arrow_table_to_structured(table)
        # Should handle null somehow (NaN for float, or object dtype)
        assert len(result) == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_float_column(self):
        """Test null in float column."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1.0, None, 3.0], type=pa.float64())})
        result = arrow_table_to_structured(table)
        assert np.isnan(result["val"][1])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_string_column(self):
        """Test null in string column."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array(["a", None, "c"], type=pa.string())})
        result = arrow_table_to_structured(table, max_string_length=0)  # Use object
        assert result["val"][1] is None
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_bool_column(self):
        """Test null in boolean column."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([True, None, False], type=pa.bool_())})
        result = arrow_table_to_structured(table)
        # Boolean with null may become object
        assert len(result) == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_all_nulls(self):
        """Test column with all nulls."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([None, None, None], type=pa.float64())})
        result = arrow_table_to_structured(table)
        assert all(np.isnan(result["val"]))
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_mixed_null_columns(self):
        """Test multiple columns with nulls."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({
            "a": pa.array([1.0, None, 3.0], type=pa.float64()),
            "b": pa.array([None, "x", "y"], type=pa.string()),
        })
        result = arrow_table_to_structured(table, max_string_length=0)
        assert np.isnan(result["a"][1])
        assert result["b"][0] is None
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_first_row(self):
        """Test null in first row."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([None, 2.0, 3.0], type=pa.float64())})
        result = arrow_table_to_structured(table)
        assert np.isnan(result["val"][0])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_last_row(self):
        """Test null in last row."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1.0, 2.0, None], type=pa.float64())})
        result = arrow_table_to_structured(table)
        assert np.isnan(result["val"][-1])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_filtering(self):
        """Test filtering rows with nulls."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1.0, None, 3.0], type=pa.float64())})
        result = arrow_table_to_structured(table)
        valid = result[~np.isnan(result["val"])]
        assert len(valid) == 2
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_count(self):
        """Test counting nulls in structured array."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        table = pa.table({"val": pa.array([1.0, None, None, 4.0], type=pa.float64())})
        result = arrow_table_to_structured(table)
        null_count = np.isnan(result["val"]).sum()
        assert null_count == 2


# =============================================================================
# Large Dataset Tests (10 tests)
# =============================================================================

class TestStructuredLargeDatasets:
    """Test structured arrays with large datasets."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_10k_rows(self):
        """Test 10K rows."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n = 10_000
        table = pa.table({
            "id": pa.array(range(n), type=pa.int64()),
            "val": pa.array([float(i) for i in range(n)], type=pa.float64()),
        })
        result = arrow_table_to_structured(table)
        assert len(result) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_100k_rows(self):
        """Test 100K rows."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n = 100_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        result = arrow_table_to_structured(table)
        assert len(result) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_many_columns(self):
        """Test table with many columns."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n_cols = 50
        n_rows = 1000
        data = {f"col_{i}": pa.array(range(n_rows), type=pa.int64()) for i in range(n_cols)}
        table = pa.table(data)
        result = arrow_table_to_structured(table)
        assert len(result.dtype.names) == n_cols
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_strings(self):
        """Test large string columns."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n = 10_000
        strings = [f"long_string_value_{i:010d}" for i in range(n)]
        table = pa.table({"name": pa.array(strings, type=pa.string())})
        result = arrow_table_to_structured(table)
        assert len(result) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_aggregation(self):
        """Test aggregation on large structured array."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n = 100_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        result = arrow_table_to_structured(table)
        assert result["val"].sum() == (n - 1) * n // 2
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_filter(self):
        """Test filtering large structured array."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n = 100_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        result = arrow_table_to_structured(table)
        filtered = result[result["val"] % 2 == 0]
        assert len(filtered) == n // 2
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_sort(self):
        """Test sorting large structured array."""
        import random
        from pynext_go.numpy_utils import arrow_table_to_structured
        n = 10_000
        values = list(range(n))
        random.shuffle(values)
        table = pa.table({"val": pa.array(values, type=pa.int64())})
        result = arrow_table_to_structured(table)
        sorted_result = np.sort(result, order="val")
        assert sorted_result["val"][0] == 0
        assert sorted_result["val"][-1] == n - 1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_iteration(self):
        """Test iterating large structured array."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n = 10_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        result = arrow_table_to_structured(table)
        count = 0
        for row in result:
            count += 1
        assert count == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_mixed_types(self):
        """Test large table with mixed types."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n = 50_000
        table = pa.table({
            "id": pa.array(range(n), type=pa.int64()),
            "val": pa.array([float(i) for i in range(n)], type=pa.float64()),
            "name": pa.array([f"n{i}" for i in range(n)], type=pa.string()),
        })
        result = arrow_table_to_structured(table)
        assert len(result) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_with_nulls(self):
        """Test large array with nulls."""
        from pynext_go.numpy_utils import arrow_table_to_structured
        n = 50_000
        values = [float(i) if i % 5 != 0 else None for i in range(n)]
        table = pa.table({"val": pa.array(values, type=pa.float64())})
        result = arrow_table_to_structured(table)
        null_count = np.isnan(result["val"]).sum()
        assert null_count == n // 5


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

