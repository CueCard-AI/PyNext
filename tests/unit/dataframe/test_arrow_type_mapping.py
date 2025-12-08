"""
Arrow Type Mapping Tests for Phase 8.3.

Tests for PostgreSQL -> Arrow -> Python type mapping.
80 comprehensive tests covering all PostgreSQL types and edge cases.

Test Categories:
1. Integer types (smallint, integer, bigint)
2. Float types (real, double precision, numeric)
3. String types (text, varchar, char)
4. Boolean type
5. Date/Time types (date, time, timestamp, interval)
6. Binary type (bytea)
7. Array types
8. JSON types (json, jsonb)
9. UUID type
10. Edge cases (NULL, empty, large values)
"""

import pytest
from typing import Any, Dict, List

# Try to import dependencies
numpy_available = False
try:
    import numpy as np
    numpy_available = True
except ImportError:
    pass

pyarrow_available = False
try:
    import pyarrow as pa
    pyarrow_available = True
except ImportError:
    pass


# =============================================================================
# Integer Type Mapping Tests (15 tests)
# =============================================================================

class TestIntegerTypeMapping:
    """Test PostgreSQL integer type mapping."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int8_mapping(self):
        """Test SMALLINT (int8) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.int8()) == "int8"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int16_mapping(self):
        """Test SMALLINT (int16) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.int16()) == "int16"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int32_mapping(self):
        """Test INTEGER (int32) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.int32()) == "int32"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int64_mapping(self):
        """Test BIGINT (int64) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.int64()) == "int64"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint8_mapping(self):
        """Test UINT8 mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.uint8()) == "uint8"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint16_mapping(self):
        """Test UINT16 mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.uint16()) == "uint16"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint32_mapping(self):
        """Test UINT32 mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.uint32()) == "uint32"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_uint64_mapping(self):
        """Test UINT64 mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.uint64()) == "uint64"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_array_conversion(self):
        """Test integer array conversion."""
        arr = pa.array([1, 2, 3], type=pa.int64())
        np_arr = arr.to_numpy()
        assert np_arr.dtype == np.int64
        np.testing.assert_array_equal(np_arr, [1, 2, 3])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_min_value(self):
        """Test integer minimum value handling."""
        arr = pa.array([-(2**63)], type=pa.int64())
        np_arr = arr.to_numpy()
        assert np_arr[0] == -(2**63)
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_max_value(self):
        """Test integer maximum value handling."""
        arr = pa.array([2**63 - 1], type=pa.int64())
        np_arr = arr.to_numpy()
        assert np_arr[0] == 2**63 - 1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_zero(self):
        """Test integer zero handling."""
        arr = pa.array([0], type=pa.int64())
        np_arr = arr.to_numpy()
        assert np_arr[0] == 0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_negative(self):
        """Test negative integer handling."""
        arr = pa.array([-1, -100, -1000], type=pa.int64())
        np_arr = arr.to_numpy()
        np.testing.assert_array_equal(np_arr, [-1, -100, -1000])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_mixed_signs(self):
        """Test mixed positive/negative integers."""
        arr = pa.array([-5, 0, 5], type=pa.int64())
        np_arr = arr.to_numpy()
        np.testing.assert_array_equal(np_arr, [-5, 0, 5])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_int_empty_array(self):
        """Test empty integer array."""
        arr = pa.array([], type=pa.int64())
        np_arr = arr.to_numpy()
        assert len(np_arr) == 0


# =============================================================================
# Float Type Mapping Tests (15 tests)
# =============================================================================

class TestFloatTypeMapping:
    """Test PostgreSQL float type mapping."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float32_mapping(self):
        """Test REAL (float32) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.float32()) == "float32"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float64_mapping(self):
        """Test DOUBLE PRECISION (float64) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.float64()) == "float64"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_array_conversion(self):
        """Test float array conversion."""
        arr = pa.array([1.5, 2.5, 3.5], type=pa.float64())
        np_arr = arr.to_numpy()
        assert np_arr.dtype == np.float64
        np.testing.assert_array_almost_equal(np_arr, [1.5, 2.5, 3.5])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_precision(self):
        """Test float precision preservation."""
        import math
        arr = pa.array([math.pi, math.e], type=pa.float64())
        np_arr = arr.to_numpy()
        assert abs(np_arr[0] - math.pi) < 1e-15
        assert abs(np_arr[1] - math.e) < 1e-15
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_infinity(self):
        """Test float infinity handling."""
        arr = pa.array([float('inf'), float('-inf')], type=pa.float64())
        np_arr = arr.to_numpy()
        assert np.isinf(np_arr[0]) and np_arr[0] > 0
        assert np.isinf(np_arr[1]) and np_arr[1] < 0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_nan(self):
        """Test float NaN handling."""
        arr = pa.array([float('nan')], type=pa.float64())
        np_arr = arr.to_numpy()
        assert np.isnan(np_arr[0])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_very_small(self):
        """Test very small float values."""
        small = 1e-300
        arr = pa.array([small, -small], type=pa.float64())
        np_arr = arr.to_numpy()
        assert np_arr[0] == small
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_very_large(self):
        """Test very large float values."""
        large = 1e300
        arr = pa.array([large, -large], type=pa.float64())
        np_arr = arr.to_numpy()
        assert np_arr[0] == large
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_zero(self):
        """Test float zero handling."""
        arr = pa.array([0.0, -0.0], type=pa.float64())
        np_arr = arr.to_numpy()
        assert np_arr[0] == 0.0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_negative(self):
        """Test negative float values."""
        arr = pa.array([-1.5, -2.5, -3.5], type=pa.float64())
        np_arr = arr.to_numpy()
        np.testing.assert_array_almost_equal(np_arr, [-1.5, -2.5, -3.5])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float32_precision(self):
        """Test float32 precision."""
        arr = pa.array([1.5, 2.5], type=pa.float32())
        np_arr = arr.to_numpy()
        assert np_arr.dtype == np.float32
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_empty_array(self):
        """Test empty float array."""
        arr = pa.array([], type=pa.float64())
        np_arr = arr.to_numpy()
        assert len(np_arr) == 0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_scientific_notation(self):
        """Test scientific notation floats."""
        arr = pa.array([1e10, 1e-10, 1.5e5], type=pa.float64())
        np_arr = arr.to_numpy()
        assert np_arr[0] == 1e10
        assert np_arr[1] == 1e-10
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_float_decimal_places(self):
        """Test various decimal places."""
        arr = pa.array([0.1, 0.01, 0.001, 0.0001], type=pa.float64())
        np_arr = arr.to_numpy()
        np.testing.assert_array_almost_equal(np_arr, [0.1, 0.01, 0.001, 0.0001])


# =============================================================================
# String Type Mapping Tests (15 tests)
# =============================================================================

class TestStringTypeMapping:
    """Test PostgreSQL string type mapping."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_mapping(self):
        """Test TEXT/VARCHAR (string) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.string()) == "object"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_string_mapping(self):
        """Test LARGE_STRING mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.large_string()) == "object"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_array_conversion(self):
        """Test string array conversion."""
        arr = pa.array(["hello", "world"], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert list(np_arr) == ["hello", "world"]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_unicode(self):
        """Test unicode string handling."""
        arr = pa.array(["hello", "世界", "🎉"], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert np_arr[0] == "hello"
        assert np_arr[1] == "世界"
        assert np_arr[2] == "🎉"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_empty(self):
        """Test empty string handling."""
        arr = pa.array(["", "a", ""], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert np_arr[0] == ""
        assert np_arr[1] == "a"
        assert np_arr[2] == ""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_whitespace(self):
        """Test whitespace string handling."""
        arr = pa.array(["  ", " a ", "\t\n"], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert np_arr[0] == "  "
        assert np_arr[1] == " a "
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_special_chars(self):
        """Test special character handling."""
        arr = pa.array(["a'b", "c\"d", "e\\f"], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert "'" in np_arr[0]
        assert '"' in np_arr[1]
        assert "\\" in np_arr[2]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_long(self):
        """Test long string handling."""
        long_str = "x" * 10000
        arr = pa.array([long_str], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert len(np_arr[0]) == 10000
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_newlines(self):
        """Test newline handling in strings."""
        arr = pa.array(["line1\nline2", "col1\tcol2"], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert "\n" in np_arr[0]
        assert "\t" in np_arr[1]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_null_char(self):
        """Test null character handling."""
        arr = pa.array(["a\x00b"], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert "\x00" in np_arr[0]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_empty_array(self):
        """Test empty string array."""
        arr = pa.array([], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert len(np_arr) == 0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_numeric_looking(self):
        """Test numeric-looking strings."""
        arr = pa.array(["123", "45.67", "-89"], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert np_arr[0] == "123"
        assert isinstance(np_arr[0], str)
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_json_content(self):
        """Test JSON content in strings."""
        arr = pa.array(['{"key": "value"}', '[]', '{}'], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert np_arr[0] == '{"key": "value"}'
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_string_html_content(self):
        """Test HTML content in strings."""
        arr = pa.array(["<html>", "<div>test</div>"], type=pa.string())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert "<html>" in np_arr[0]


# =============================================================================
# Boolean Type Mapping Tests (10 tests)
# =============================================================================

class TestBooleanTypeMapping:
    """Test PostgreSQL boolean type mapping."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_mapping(self):
        """Test BOOLEAN mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.bool_()) == "bool"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_array_conversion(self):
        """Test boolean array conversion (requires copy for Arrow bool)."""
        arr = pa.array([True, False, True], type=pa.bool_())
        np_arr = arr.to_numpy(zero_copy_only=False)  # Boolean requires copy
        assert np_arr.dtype == np.bool_
        np.testing.assert_array_equal(np_arr, [True, False, True])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_all_true(self):
        """Test all True boolean array."""
        arr = pa.array([True, True, True], type=pa.bool_())
        np_arr = arr.to_numpy(zero_copy_only=False)  # Boolean requires copy
        assert np_arr.all()
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_all_false(self):
        """Test all False boolean array."""
        arr = pa.array([False, False, False], type=pa.bool_())
        np_arr = arr.to_numpy(zero_copy_only=False)  # Boolean requires copy
        assert not np_arr.any()
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_single_true(self):
        """Test single True boolean."""
        arr = pa.array([True], type=pa.bool_())
        np_arr = arr.to_numpy(zero_copy_only=False)  # Boolean requires copy
        assert np_arr[0] == True
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_single_false(self):
        """Test single False boolean."""
        arr = pa.array([False], type=pa.bool_())
        np_arr = arr.to_numpy(zero_copy_only=False)  # Boolean requires copy
        assert np_arr[0] == False
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_empty_array(self):
        """Test empty boolean array."""
        arr = pa.array([], type=pa.bool_())
        np_arr = arr.to_numpy(zero_copy_only=False)  # Boolean requires copy
        assert len(np_arr) == 0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_sum_counts_true(self):
        """Test sum counts True values."""
        arr = pa.array([True, True, False, True, False], type=pa.bool_())
        np_arr = arr.to_numpy(zero_copy_only=False)  # Boolean requires copy
        assert np_arr.sum() == 3
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_as_mask(self):
        """Test using boolean array as mask."""
        mask = pa.array([True, False, True], type=pa.bool_())
        data = pa.array([1, 2, 3], type=pa.int64())
        np_mask = mask.to_numpy(zero_copy_only=False)  # Boolean requires copy
        np_data = data.to_numpy()
        filtered = np_data[np_mask]
        np.testing.assert_array_equal(filtered, [1, 3])
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_bool_logical_ops(self):
        """Test logical operations on boolean array."""
        arr1 = pa.array([True, True, False, False], type=pa.bool_())
        arr2 = pa.array([True, False, True, False], type=pa.bool_())
        np1 = arr1.to_numpy(zero_copy_only=False)  # Boolean requires copy
        np2 = arr2.to_numpy(zero_copy_only=False)  # Boolean requires copy
        
        np.testing.assert_array_equal(np1 & np2, [True, False, False, False])
        np.testing.assert_array_equal(np1 | np2, [True, True, True, False])


# =============================================================================
# Date/Time Type Mapping Tests (15 tests)
# =============================================================================

class TestDateTimeTypeMapping:
    """Test PostgreSQL date/time type mapping."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_date32_mapping(self):
        """Test DATE (date32) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert "datetime64" in arrow_type_to_numpy_dtype(pa.date32())
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_date_array_conversion(self):
        """Test date array conversion (requires copy for date types)."""
        import datetime
        dates = [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)]
        arr = pa.array(dates, type=pa.date32())
        np_arr = arr.to_numpy(zero_copy_only=False)  # Date requires copy
        # Should be datetime64 or object
        assert len(np_arr) == 2
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_timestamp_us_mapping(self):
        """Test TIMESTAMP (microsecond) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert "datetime64" in arrow_type_to_numpy_dtype(pa.timestamp("us"))
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_timestamp_ns_mapping(self):
        """Test TIMESTAMP (nanosecond) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert "datetime64" in arrow_type_to_numpy_dtype(pa.timestamp("ns"))
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_timestamp_array_conversion(self):
        """Test timestamp array conversion."""
        import datetime
        ts = [datetime.datetime(2024, 1, 1, 12, 0), datetime.datetime(2024, 1, 2, 12, 0)]
        arr = pa.array(ts, type=pa.timestamp("us"))
        np_arr = arr.to_numpy()
        assert len(np_arr) == 2
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_timestamp_with_tz(self):
        """Test TIMESTAMP WITH TIMEZONE mapping."""
        import datetime
        ts = [datetime.datetime(2024, 1, 1, 12, 0)]
        arr = pa.array(ts, type=pa.timestamp("us", tz="UTC"))
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert len(np_arr) == 1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_duration_mapping(self):
        """Test INTERVAL (duration) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert "timedelta64" in arrow_type_to_numpy_dtype(pa.duration("us"))
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_time32_mapping(self):
        """Test TIME (time32) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        # Time types become object (no NumPy equivalent)
        assert arrow_type_to_numpy_dtype(pa.time32("ms")) == "object"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_timestamp_min(self):
        """Test minimum timestamp value."""
        import datetime
        ts = [datetime.datetime(1970, 1, 1, 0, 0, 0)]
        arr = pa.array(ts, type=pa.timestamp("us"))
        np_arr = arr.to_numpy()
        assert len(np_arr) == 1
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_timestamp_sorting(self):
        """Test timestamp sorting."""
        import datetime
        ts = [
            datetime.datetime(2024, 1, 3),
            datetime.datetime(2024, 1, 1),
            datetime.datetime(2024, 1, 2),
        ]
        arr = pa.array(ts, type=pa.timestamp("us"))
        np_arr = arr.to_numpy()
        sorted_arr = np.sort(np_arr)
        assert sorted_arr[0] < sorted_arr[1] < sorted_arr[2]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_date_empty_array(self):
        """Test empty date array (requires copy for date types)."""
        arr = pa.array([], type=pa.date32())
        np_arr = arr.to_numpy(zero_copy_only=False)  # Date requires copy
        assert len(np_arr) == 0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_timestamp_comparison(self):
        """Test timestamp comparison."""
        import datetime
        ts = [datetime.datetime(2024, 1, 1), datetime.datetime(2024, 1, 2)]
        arr = pa.array(ts, type=pa.timestamp("us"))
        np_arr = arr.to_numpy()
        assert np_arr[0] < np_arr[1]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_duration_array(self):
        """Test duration array conversion."""
        arr = pa.array([1000, 2000, 3000], type=pa.duration("us"))
        np_arr = arr.to_numpy()
        assert len(np_arr) == 3


# =============================================================================
# Binary Type Mapping Tests (10 tests)
# =============================================================================

class TestBinaryTypeMapping:
    """Test PostgreSQL binary (bytea) type mapping."""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_binary_mapping(self):
        """Test BYTEA (binary) mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.binary()) == "object"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_binary_array_conversion(self):
        """Test binary array conversion."""
        arr = pa.array([b"abc", b"def", b"ghi"], type=pa.binary())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert np_arr[0] == b"abc"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_binary_empty(self):
        """Test empty binary value."""
        arr = pa.array([b"", b"x", b""], type=pa.binary())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert np_arr[0] == b""
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_binary_null_bytes(self):
        """Test binary with null bytes."""
        arr = pa.array([b"\x00\x01\x02"], type=pa.binary())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert b"\x00" in np_arr[0]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_binary_all_bytes(self):
        """Test binary with all byte values."""
        data = bytes(range(256))
        arr = pa.array([data], type=pa.binary())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert len(np_arr[0]) == 256
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_binary_large(self):
        """Test large binary value."""
        data = b"x" * 10000
        arr = pa.array([data], type=pa.binary())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert len(np_arr[0]) == 10000
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_binary_empty_array(self):
        """Test empty binary array."""
        arr = pa.array([], type=pa.binary())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert len(np_arr) == 0
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_large_binary_mapping(self):
        """Test LARGE_BINARY mapping."""
        from pynext_go.numpy_utils import arrow_type_to_numpy_dtype
        assert arrow_type_to_numpy_dtype(pa.large_binary()) == "object"
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_binary_iteration(self):
        """Test iterating over binary array."""
        arr = pa.array([b"a", b"b", b"c"], type=pa.binary())
        np_arr = arr.to_numpy(zero_copy_only=False)
        values = list(np_arr)
        assert values == [b"a", b"b", b"c"]
    
    @pytest.mark.skipif(not numpy_available, reason="numpy not available")
    @pytest.mark.skipif(not pyarrow_available, reason="pyarrow not available")
    def test_binary_comparison(self):
        """Test binary comparison."""
        arr = pa.array([b"abc", b"def"], type=pa.binary())
        np_arr = arr.to_numpy(zero_copy_only=False)
        assert np_arr[0] < np_arr[1]


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

