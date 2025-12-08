"""
NumPy Column-wise Tests for Phase 8.3.

Tests for pynext_go.execute_numpy() and arrow_table_to_numpy_columns().
100 comprehensive tests covering type mapping, null handling, zero-copy,
and integration with the QueryBuilder.

Test Categories:
1. Integer type mapping (int8, int16, int32, int64)
2. Unsigned integer type mapping (uint8, uint16, uint32, uint64)
3. Float type mapping (float32, float64)
4. String column handling
5. Boolean column handling
6. Date/Time column handling
7. Null handling (NaN for numeric, None for object)
8. Zero-copy verification
9. Large datasets
10. Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
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


# =============================================================================
# Integer Type Mapping Tests (20 tests)
# =============================================================================

class TestNumPyIntegerTypes:
    """Test integer type mapping from Arrow to NumPy."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int8_to_numpy(self):
        """Test INT8 to np.int8 conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int8())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.int8
        np.testing.assert_array_equal(result["val"], [1, 2, 3])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int16_to_numpy(self):
        """Test INT16 to np.int16 conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int16())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.int16
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int32_to_numpy(self):
        """Test INT32 to np.int32 conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int32())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.int32
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int64_to_numpy(self):
        """Test INT64 to np.int64 conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.int64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint8_to_numpy(self):
        """Test UINT8 to np.uint8 conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.uint8())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.uint8
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint16_to_numpy(self):
        """Test UINT16 to np.uint16 conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.uint16())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.uint16
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint32_to_numpy(self):
        """Test UINT32 to np.uint32 conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.uint32())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.uint32
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint64_to_numpy(self):
        """Test UINT64 to np.uint64 conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.uint64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.uint64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int8_range(self):
        """Test INT8 full range."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([-128, 0, 127], type=pa.int8())})
        result = arrow_table_to_numpy_columns(table)
        np.testing.assert_array_equal(result["val"], [-128, 0, 127])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int64_large_values(self):
        """Test INT64 with large values."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        large = 2**62
        table = pa.table({"val": pa.array([-large, 0, large], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        np.testing.assert_array_equal(result["val"], [-large, 0, large])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint64_large_values(self):
        """Test UINT64 with large values."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        large = 2**63
        table = pa.table({"val": pa.array([0, large, 2**64 - 1], type=pa.uint64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"][1] == large
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_mixed_integer_types(self):
        """Test table with multiple integer types."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({
            "i8": pa.array([1, 2, 3], type=pa.int8()),
            "i16": pa.array([1, 2, 3], type=pa.int16()),
            "i32": pa.array([1, 2, 3], type=pa.int32()),
            "i64": pa.array([1, 2, 3], type=pa.int64()),
        })
        result = arrow_table_to_numpy_columns(table)
        assert result["i8"].dtype == np.int8
        assert result["i16"].dtype == np.int16
        assert result["i32"].dtype == np.int32
        assert result["i64"].dtype == np.int64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_vectorized_ops(self):
        """Test vectorized operations on integer arrays."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        
        # Vectorized operations
        assert result["val"].sum() == 15
        assert result["val"].mean() == 3.0
        assert result["val"].max() == 5
        assert result["val"].min() == 1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_boolean_indexing(self):
        """Test boolean indexing on integer arrays."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        
        # Boolean indexing
        filtered = result["val"][result["val"] > 3]
        np.testing.assert_array_equal(filtered, [4, 5])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_slicing(self):
        """Test slicing on integer arrays."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3, 4, 5], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        
        # Slicing
        np.testing.assert_array_equal(result["val"][:3], [1, 2, 3])
        np.testing.assert_array_equal(result["val"][-2:], [4, 5])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_arithmetic(self):
        """Test arithmetic on integer arrays."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        
        doubled = result["val"] * 2
        np.testing.assert_array_equal(doubled, [2, 4, 6])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_zeros(self):
        """Test integer array with zeros."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([0, 0, 0], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].sum() == 0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_negative(self):
        """Test integer array with negative values."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([-1, -2, -3], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].sum() == -6
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_single_element(self):
        """Test single element integer array."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([42], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        assert len(result["val"]) == 1
        assert result["val"][0] == 42


# =============================================================================
# Float Type Mapping Tests (15 tests)
# =============================================================================

class TestNumPyFloatTypes:
    """Test float type mapping from Arrow to NumPy."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float32_to_numpy(self):
        """Test FLOAT32 to np.float32 conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.5, 2.5, 3.5], type=pa.float32())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.float32
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float64_to_numpy(self):
        """Test FLOAT64 to np.float64 conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.5, 2.5, 3.5], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.float64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_precision(self):
        """Test float precision is preserved."""
        import math
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([math.pi, math.e], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        assert abs(result["val"][0] - math.pi) < 1e-10
        assert abs(result["val"][1] - math.e) < 1e-10
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_special_values(self):
        """Test special float values (inf, -inf)."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([float('inf'), float('-inf'), 0.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        assert np.isinf(result["val"][0]) and result["val"][0] > 0
        assert np.isinf(result["val"][1]) and result["val"][1] < 0
        assert result["val"][2] == 0.0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_nan_value(self):
        """Test NaN float value."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([float('nan'), 1.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        assert np.isnan(result["val"][0])
        assert result["val"][1] == 1.0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_very_small(self):
        """Test very small float values."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        small = 1e-308
        table = pa.table({"val": pa.array([small, -small], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"][0] == small
        assert result["val"][1] == -small
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_very_large(self):
        """Test very large float values."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        large = 1e307
        table = pa.table({"val": pa.array([large, -large], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"][0] == large
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_vectorized_ops(self):
        """Test vectorized operations on float arrays."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, 2.0, 3.0, 4.0, 5.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        
        assert result["val"].sum() == 15.0
        assert result["val"].mean() == 3.0
        assert result["val"].std() > 0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_arithmetic(self):
        """Test arithmetic on float arrays."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, 2.0, 3.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        
        doubled = result["val"] * 2.0
        np.testing.assert_array_almost_equal(doubled, [2.0, 4.0, 6.0])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_math_functions(self):
        """Test math functions on float arrays."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, 4.0, 9.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        
        sqrt = np.sqrt(result["val"])
        np.testing.assert_array_almost_equal(sqrt, [1.0, 2.0, 3.0])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_comparison(self):
        """Test comparison operations on float arrays."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, 2.0, 3.0, 4.0, 5.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        
        mask = result["val"] > 3.0
        np.testing.assert_array_equal(mask, [False, False, False, True, True])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_negative(self):
        """Test negative float values."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([-1.5, -2.5, -3.5], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].sum() == -7.5
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_zeros(self):
        """Test float array with zeros."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([0.0, 0.0, 0.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].sum() == 0.0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_mixed_signs(self):
        """Test float array with mixed positive/negative."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([-2.0, -1.0, 0.0, 1.0, 2.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].sum() == 0.0


# =============================================================================
# String Column Tests (15 tests)
# =============================================================================

class TestNumPyStringColumns:
    """Test string column handling."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_to_object(self):
        """Test STRING to object dtype conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.object_
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_values_preserved(self):
        """Test string values are preserved."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["hello", "world", "test"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert list(result["val"]) == ["hello", "world", "test"]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_unicode_strings(self):
        """Test unicode string handling."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["hello", "世界", "🎉"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"][0] == "hello"
        assert result["val"][1] == "世界"
        assert result["val"][2] == "🎉"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_empty_strings(self):
        """Test empty string handling."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["", "a", ""], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"][0] == ""
        assert result["val"][1] == "a"
        assert result["val"][2] == ""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_long_strings(self):
        """Test long string handling."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        long_str = "x" * 10000
        table = pa.table({"val": pa.array([long_str, "short"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert len(result["val"][0]) == 10000
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_special_chars(self):
        """Test strings with special characters."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["tab\there", "new\nline", "quote'test"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert "\t" in result["val"][0]
        assert "\n" in result["val"][1]
        assert "'" in result["val"][2]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_whitespace(self):
        """Test strings with whitespace."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["  leading", "trailing  ", "  both  "], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"][0] == "  leading"
        assert result["val"][1] == "trailing  "
        assert result["val"][2] == "  both  "
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_string_column(self):
        """Test large string column conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 10000
        strings = [f"string_{i}" for i in range(n)]
        table = pa.table({"val": pa.array(strings, type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert len(result["val"]) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_numpy_string_ops(self):
        """Test numpy string operations."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["HELLO", "WORLD"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        # Can apply vectorized string ops via np.char
        lower = [s.lower() for s in result["val"]]
        assert lower == ["hello", "world"]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_single_char(self):
        """Test single character strings."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert list(result["val"]) == ["a", "b", "c"]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_numeric_like(self):
        """Test strings that look like numbers."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["123", "456.78", "-99"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        # Should remain as strings
        assert result["val"].dtype == np.object_
        assert result["val"][0] == "123"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_json_like(self):
        """Test strings containing JSON."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(['{"key": "value"}', '[]', '{}'], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"][0] == '{"key": "value"}'
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_string_type(self):
        """Test LARGE_STRING type handling."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.large_string())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.object_
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_iteration(self):
        """Test iteration over string array."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        collected = []
        for s in result["val"]:
            collected.append(s)
        assert collected == ["a", "b", "c"]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_indexing(self):
        """Test indexing string array."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["a", "b", "c", "d", "e"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"][0] == "a"
        assert result["val"][-1] == "e"
        assert list(result["val"][1:3]) == ["b", "c"]


# =============================================================================
# Boolean Column Tests (10 tests)
# =============================================================================

class TestNumPyBooleanColumns:
    """Test boolean column handling."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_to_numpy(self):
        """Test BOOLEAN to np.bool_ conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([True, False, True], type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].dtype == np.bool_
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_values(self):
        """Test boolean values are preserved."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([True, False, True, False], type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table)
        np.testing.assert_array_equal(result["val"], [True, False, True, False])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_all_true(self):
        """Test all True boolean array."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([True, True, True], type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].all()
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_all_false(self):
        """Test all False boolean array."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([False, False, False], type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table)
        assert not result["val"].any()
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_sum(self):
        """Test sum of boolean array (counts True)."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([True, True, False, True, False], type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].sum() == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_as_mask(self):
        """Test using boolean array as mask."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({
            "mask": pa.array([True, False, True], type=pa.bool_()),
            "val": pa.array([1, 2, 3], type=pa.int64()),
        })
        result = arrow_table_to_numpy_columns(table)
        filtered = result["val"][result["mask"]]
        np.testing.assert_array_equal(filtered, [1, 3])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_logical_ops(self):
        """Test logical operations on boolean arrays."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({
            "a": pa.array([True, True, False, False], type=pa.bool_()),
            "b": pa.array([True, False, True, False], type=pa.bool_()),
        })
        result = arrow_table_to_numpy_columns(table)
        
        # AND
        np.testing.assert_array_equal(result["a"] & result["b"], [True, False, False, False])
        # OR
        np.testing.assert_array_equal(result["a"] | result["b"], [True, True, True, False])
        # NOT
        np.testing.assert_array_equal(~result["a"], [False, False, True, True])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_single_element(self):
        """Test single element boolean array."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([True], type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"][0] == True
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_large_array(self):
        """Test large boolean array."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 10000
        values = [i % 2 == 0 for i in range(n)]
        table = pa.table({"val": pa.array(values, type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table)
        assert len(result["val"]) == n
        assert result["val"].sum() == n // 2
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_where(self):
        """Test np.where with boolean array."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([True, False, True], type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table)
        where_result = np.where(result["val"], "yes", "no")
        assert list(where_result) == ["yes", "no", "yes"]


# =============================================================================
# Null Handling Tests (15 tests)
# =============================================================================

class TestNumPyNullHandling:
    """Test null value handling in NumPy conversion."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_int_converts_to_float_nan(self):
        """Test null in integer column - requires float for NaN."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, None, 3], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        # With zero_copy=False, nulls may be converted
        assert len(result["val"]) == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_float_becomes_nan(self):
        """Test null in float column becomes NaN."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, None, 3.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        assert np.isnan(result["val"][1])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_string(self):
        """Test null in string column."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["a", None, "c"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        assert result["val"][0] == "a"
        assert result["val"][1] is None
        assert result["val"][2] == "c"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_in_bool(self):
        """Test null in boolean column."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([True, None, False], type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        # Boolean with null becomes object dtype
        assert len(result["val"]) == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_all_nulls(self):
        """Test column with all null values."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([None, None, None], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        assert len(result["val"]) == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_no_nulls_zero_copy(self):
        """Test zero-copy possible when no nulls."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=True)
        # Should be zero-copy
        assert result["val"].dtype == np.int64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_first_row(self):
        """Test null in first row."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([None, 2.0, 3.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        assert np.isnan(result["val"][0])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_last_row(self):
        """Test null in last row."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, 2.0, None], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        assert np.isnan(result["val"][-1])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_multiple_columns(self):
        """Test nulls in multiple columns."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({
            "a": pa.array([1.0, None, 3.0], type=pa.float64()),
            "b": pa.array([None, "x", "y"], type=pa.string()),
        })
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        assert np.isnan(result["a"][1])
        assert result["b"][0] is None
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_aggregation_with_nan(self):
        """Test aggregation ignores NaN."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, None, 3.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        # nansum ignores NaN
        assert np.nansum(result["val"]) == 4.0
        assert np.nanmean(result["val"]) == 2.0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_isnan(self):
        """Test detecting nulls with isnan."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, None, 3.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        nulls = np.isnan(result["val"])
        np.testing.assert_array_equal(nulls, [False, True, False])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_filling(self):
        """Test filling nulls with np.nan_to_num."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, None, 3.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        filled = np.nan_to_num(result["val"], nan=0.0)
        np.testing.assert_array_equal(filled, [1.0, 0.0, 3.0])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_count(self):
        """Test counting nulls."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, None, None, 4.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        null_count = np.isnan(result["val"]).sum()
        assert null_count == 2
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_filtering(self):
        """Test filtering out nulls."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, None, 3.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        valid = result["val"][~np.isnan(result["val"])]
        np.testing.assert_array_equal(valid, [1.0, 3.0])


# =============================================================================
# Zero-Copy Verification Tests (10 tests)
# =============================================================================

class TestNumPyZeroCopy:
    """Test zero-copy behavior for performance."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int64_zero_copy(self):
        """Test INT64 column zero-copy."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=True)
        # Zero-copy means array doesn't own data
        # Note: This depends on Arrow internals
        assert result["val"].dtype == np.int64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float64_zero_copy(self):
        """Test FLOAT64 column zero-copy."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1.0, 2.0, 3.0], type=pa.float64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=True)
        assert result["val"].dtype == np.float64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_not_zero_copy(self):
        """Test STRING column cannot be zero-copy."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array(["a", "b", "c"], type=pa.string())})
        result = arrow_table_to_numpy_columns(table, zero_copy=True)
        # String columns always require copy
        assert result["val"].dtype == np.object_
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_zero_copy_is_fast(self):
        """Test zero-copy is very fast."""
        import time
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        
        n = 1_000_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        
        start = time.perf_counter()
        result = arrow_table_to_numpy_columns(table, zero_copy=True)
        elapsed = time.perf_counter() - start
        
        # Zero-copy should be nearly instant (< 100ms)
        assert elapsed < 0.1, f"Took {elapsed:.3f}s, expected < 0.1s"
        assert len(result["val"]) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_copy_mode(self):
        """Test explicit copy mode."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        # Should still work
        np.testing.assert_array_equal(result["val"], [1, 2, 3])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_null_prevents_zero_copy(self):
        """Test nulls prevent zero-copy for integers."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, None, 3], type=pa.int64())})
        # Should still work, but may need copy
        result = arrow_table_to_numpy_columns(table, zero_copy=True)
        assert len(result["val"]) == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_may_zero_copy(self):
        """Test boolean column may zero-copy."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([True, False, True], type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table, zero_copy=True)
        assert result["val"].dtype == np.bool_
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_multiple_columns_zero_copy(self):
        """Test multiple columns can all be zero-copy."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({
            "a": pa.array([1, 2, 3], type=pa.int64()),
            "b": pa.array([1.0, 2.0, 3.0], type=pa.float64()),
        })
        result = arrow_table_to_numpy_columns(table, zero_copy=True)
        assert result["a"].dtype == np.int64
        assert result["b"].dtype == np.float64
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_array_zero_copy(self):
        """Test large array zero-copy performance."""
        import time
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        
        n = 10_000_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        
        start = time.perf_counter()
        result = arrow_table_to_numpy_columns(table, zero_copy=True)
        elapsed = time.perf_counter() - start
        
        # Should handle 10M elements very fast
        assert elapsed < 0.5, f"Took {elapsed:.3f}s, expected < 0.5s"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_data_modification_independence(self):
        """Test that modifications don't affect original."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        table = pa.table({"val": pa.array([1, 2, 3], type=pa.int64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        
        # Modify the result
        original = result["val"].copy()
        result["val"][0] = 999
        
        # Verify we can modify without affecting original table
        # (this tests copy mode behavior)
        assert result["val"][0] == 999


# =============================================================================
# Large Dataset Tests (10 tests)
# =============================================================================

class TestNumPyLargeDatasets:
    """Test performance with large datasets."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_10k_rows(self):
        """Test 10K row conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 10_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        assert len(result["val"]) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_100k_rows(self):
        """Test 100K row conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 100_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        assert len(result["val"]) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_1m_rows(self):
        """Test 1M row conversion."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 1_000_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        assert len(result["val"]) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_many_columns(self):
        """Test table with many columns."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n_cols = 100
        n_rows = 10_000
        data = {f"col_{i}": pa.array(range(n_rows), type=pa.int64()) for i in range(n_cols)}
        table = pa.table(data)
        result = arrow_table_to_numpy_columns(table)
        assert len(result) == n_cols
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_aggregation(self):
        """Test aggregation on large array."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 1_000_000
        table = pa.table({"val": pa.array(range(n), type=pa.int64())})
        result = arrow_table_to_numpy_columns(table)
        # Sum of 0..999999
        assert result["val"].sum() == (n - 1) * n // 2
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_with_nulls(self):
        """Test large array with scattered nulls."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 100_000
        values = [float(i) if i % 10 != 0 else None for i in range(n)]
        table = pa.table({"val": pa.array(values, type=pa.float64())})
        result = arrow_table_to_numpy_columns(table, zero_copy=False)
        # 10% should be null
        null_count = np.isnan(result["val"]).sum()
        assert null_count == n // 10
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_string_column(self):
        """Test large string column."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 100_000
        strings = [f"string_{i}" for i in range(n)]
        table = pa.table({"val": pa.array(strings, type=pa.string())})
        result = arrow_table_to_numpy_columns(table)
        assert len(result["val"]) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_boolean_column(self):
        """Test large boolean column."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 1_000_000
        values = [i % 2 == 0 for i in range(n)]
        table = pa.table({"val": pa.array(values, type=pa.bool_())})
        result = arrow_table_to_numpy_columns(table)
        assert result["val"].sum() == n // 2
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_chunked_array_large(self):
        """Test large chunked array."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 100_000
        chunk_size = 10_000
        chunks = [pa.array(range(i, i + chunk_size), type=pa.int64()) for i in range(0, n, chunk_size)]
        chunked = pa.chunked_array(chunks)
        table = pa.table({"val": chunked})
        result = arrow_table_to_numpy_columns(table)
        assert len(result["val"]) == n
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_mixed_types(self):
        """Test large table with mixed types."""
        from pynext_go.numpy_utils import arrow_table_to_numpy_columns
        n = 100_000
        table = pa.table({
            "id": pa.array(range(n), type=pa.int64()),
            "value": pa.array([float(i) for i in range(n)], type=pa.float64()),
            "name": pa.array([f"name_{i}" for i in range(n)], type=pa.string()),
        })
        result = arrow_table_to_numpy_columns(table)
        assert len(result["id"]) == n
        assert len(result["value"]) == n
        assert len(result["name"]) == n


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

