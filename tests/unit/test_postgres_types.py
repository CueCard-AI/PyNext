"""
PostgreSQL Type Conversion Tests.

70 comprehensive tests for type converters.
"""

import json
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum

import pytest

from pynext.db.adapters.postgres_types import (
    python_to_postgres,
    postgres_to_python,
    ensure_timezone_aware,
    convert_to_json,
    convert_to_uuid,
    convert_to_bytes,
    convert_to_datetime,
    convert_to_date,
    convert_to_time,
    convert_from_json,
    get_postgres_type,
    get_python_type,
    convert_array_to_postgres,
    convert_array_from_postgres,
    TypeConversionError,
)


# =============================================================================
# Python to PostgreSQL Conversion Tests
# =============================================================================

class TestPythonToPostgres:
    """Tests for Python → PostgreSQL conversion."""
    
    def test_convert_none(self):
        """Test converting None."""
        assert python_to_postgres(None) is None
    
    def test_convert_int(self):
        """Test converting integers."""
        assert python_to_postgres(42) == 42
        assert python_to_postgres(-100) == -100
        assert python_to_postgres(0) == 0
    
    def test_convert_float(self):
        """Test converting floats."""
        assert python_to_postgres(3.14) == 3.14
        assert python_to_postgres(-2.5) == -2.5
    
    def test_convert_str(self):
        """Test converting strings."""
        assert python_to_postgres("hello") == "hello"
        assert python_to_postgres("") == ""
    
    def test_convert_bool(self):
        """Test converting booleans."""
        assert python_to_postgres(True) is True
        assert python_to_postgres(False) is False
    
    def test_convert_decimal(self):
        """Test converting Decimal."""
        assert python_to_postgres(Decimal("123.45")) == Decimal("123.45")
    
    def test_convert_bytes(self):
        """Test converting bytes."""
        assert python_to_postgres(b"hello") == b"hello"
    
    def test_convert_uuid(self):
        """Test converting UUID."""
        test_uuid = uuid.uuid4()
        assert python_to_postgres(test_uuid) == test_uuid
    
    def test_convert_datetime_naive(self):
        """Test converting naive datetime adds UTC."""
        dt = datetime(2024, 1, 15, 12, 30, 0)
        result = python_to_postgres(dt)
        assert result.tzinfo is not None
    
    def test_convert_datetime_aware(self):
        """Test converting aware datetime."""
        dt = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
        result = python_to_postgres(dt)
        assert result == dt
    
    def test_convert_date(self):
        """Test converting date."""
        d = date(2024, 1, 15)
        assert python_to_postgres(d) == d
    
    def test_convert_time(self):
        """Test converting time."""
        t = time(12, 30, 0)
        assert python_to_postgres(t) == t
    
    def test_convert_list(self):
        """Test converting list."""
        result = python_to_postgres([1, 2, 3])
        assert result == [1, 2, 3]
    
    def test_convert_nested_list(self):
        """Test converting nested list."""
        result = python_to_postgres([[1, 2], [3, 4]])
        assert result == [[1, 2], [3, 4]]
    
    def test_convert_dict(self):
        """Test converting dict to JSON."""
        result = python_to_postgres({"key": "value"})
        assert json.loads(result) == {"key": "value"}
    
    def test_convert_with_target_type_json(self):
        """Test converting with explicit JSONB type."""
        result = python_to_postgres([1, 2, 3], "JSONB")
        assert json.loads(result) == [1, 2, 3]
    
    def test_convert_with_target_type_uuid(self):
        """Test converting string to UUID with explicit type."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result = python_to_postgres(uuid_str, "UUID")
        assert isinstance(result, uuid.UUID)


class TestEnumConversion:
    """Tests for Enum conversion."""
    
    def test_convert_string_enum(self):
        """Test converting string Enum."""
        class Status(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"
        
        assert python_to_postgres(Status.ACTIVE) == "active"
    
    def test_convert_int_enum(self):
        """Test converting int Enum."""
        class Priority(Enum):
            LOW = 1
            HIGH = 2
        
        assert python_to_postgres(Priority.HIGH) == 2


# =============================================================================
# PostgreSQL to Python Conversion Tests
# =============================================================================

class TestPostgresToPython:
    """Tests for PostgreSQL → Python conversion."""
    
    def test_convert_none(self):
        """Test converting None."""
        assert postgres_to_python(None, str) is None
    
    def test_convert_to_int(self):
        """Test converting to int."""
        assert postgres_to_python(42, int) == 42
        assert postgres_to_python("42", int) == 42
    
    def test_convert_to_float(self):
        """Test converting to float."""
        assert postgres_to_python(3.14, float) == 3.14
        assert postgres_to_python("3.14", float) == 3.14
    
    def test_convert_to_str(self):
        """Test converting to string."""
        assert postgres_to_python("hello", str) == "hello"
        assert postgres_to_python(42, str) == "42"
    
    def test_convert_to_bool(self):
        """Test converting to bool."""
        assert postgres_to_python(True, bool) is True
        assert postgres_to_python(1, bool) is True
        assert postgres_to_python(0, bool) is False
    
    def test_convert_to_decimal(self):
        """Test converting to Decimal."""
        result = postgres_to_python("123.45", Decimal)
        assert result == Decimal("123.45")
    
    def test_convert_to_datetime(self):
        """Test converting to datetime."""
        dt_str = "2024-01-15 12:30:00"
        result = postgres_to_python(dt_str, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_convert_to_date(self):
        """Test converting to date."""
        d_str = "2024-01-15"
        result = postgres_to_python(d_str, date)
        assert result == date(2024, 1, 15)
    
    def test_convert_to_time(self):
        """Test converting to time."""
        t_str = "12:30:00"
        result = postgres_to_python(t_str, time)
        assert result == time(12, 30, 0)
    
    def test_convert_to_uuid(self):
        """Test converting to UUID."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result = postgres_to_python(uuid_str, uuid.UUID)
        assert str(result) == uuid_str
    
    def test_convert_to_dict(self):
        """Test converting JSON to dict."""
        json_str = '{"key": "value"}'
        result = postgres_to_python(json_str, dict)
        assert result == {"key": "value"}
    
    def test_convert_to_list(self):
        """Test converting to list."""
        result = postgres_to_python([1, 2, 3], list)
        assert result == [1, 2, 3]


# =============================================================================
# Timezone Tests
# =============================================================================

class TestTimezoneHandling:
    """Tests for timezone handling."""
    
    def test_ensure_timezone_naive(self):
        """Test adding timezone to naive datetime."""
        dt = datetime(2024, 1, 15, 12, 30, 0)
        result = ensure_timezone_aware(dt)
        assert result.tzinfo == timezone.utc
    
    def test_ensure_timezone_already_aware(self):
        """Test preserving existing timezone."""
        dt = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
        result = ensure_timezone_aware(dt)
        assert result.tzinfo == timezone.utc


# =============================================================================
# JSON Conversion Tests
# =============================================================================

class TestJSONConversion:
    """Tests for JSON conversion."""
    
    def test_convert_dict_to_json(self):
        """Test converting dict to JSON."""
        result = convert_to_json({"a": 1, "b": 2})
        assert json.loads(result) == {"a": 1, "b": 2}
    
    def test_convert_list_to_json(self):
        """Test converting list to JSON."""
        result = convert_to_json([1, 2, 3])
        assert json.loads(result) == [1, 2, 3]
    
    def test_convert_nested_to_json(self):
        """Test converting nested structure to JSON."""
        data = {"users": [{"name": "John"}, {"name": "Jane"}]}
        result = convert_to_json(data)
        assert json.loads(result) == data
    
    def test_convert_from_json_dict(self):
        """Test converting JSON string to dict."""
        result = convert_from_json('{"a": 1}')
        assert result == {"a": 1}
    
    def test_convert_from_json_list(self):
        """Test converting JSON string to list."""
        result = convert_from_json('[1, 2, 3]')
        assert result == [1, 2, 3]
    
    def test_convert_from_json_already_parsed(self):
        """Test handling already parsed JSON."""
        result = convert_from_json({"a": 1})
        assert result == {"a": 1}
    
    def test_invalid_json_raises(self):
        """Test invalid JSON raises error."""
        with pytest.raises(TypeConversionError):
            convert_from_json("not valid json")


# =============================================================================
# UUID Conversion Tests
# =============================================================================

class TestUUIDConversion:
    """Tests for UUID conversion."""
    
    def test_convert_uuid_object(self):
        """Test converting UUID object."""
        test_uuid = uuid.uuid4()
        result = convert_to_uuid(test_uuid)
        assert result == test_uuid
    
    def test_convert_uuid_string(self):
        """Test converting UUID string."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result = convert_to_uuid(uuid_str)
        assert str(result) == uuid_str
    
    def test_convert_uuid_bytes(self):
        """Test converting UUID bytes."""
        test_uuid = uuid.uuid4()
        result = convert_to_uuid(test_uuid.bytes)
        assert result == test_uuid
    
    def test_invalid_uuid_raises(self):
        """Test invalid UUID string raises error."""
        with pytest.raises(TypeConversionError):
            convert_to_uuid("not-a-uuid")
    
    def test_invalid_uuid_type_raises(self):
        """Test invalid UUID type raises error."""
        with pytest.raises(TypeConversionError):
            convert_to_uuid(12345)


# =============================================================================
# Bytes Conversion Tests
# =============================================================================

class TestBytesConversion:
    """Tests for bytes conversion."""
    
    def test_convert_bytes(self):
        """Test converting bytes."""
        result = convert_to_bytes(b"hello")
        assert result == b"hello"
    
    def test_convert_bytearray(self):
        """Test converting bytearray."""
        result = convert_to_bytes(bytearray(b"hello"))
        assert result == b"hello"
    
    def test_convert_string_to_bytes(self):
        """Test converting string to bytes."""
        result = convert_to_bytes("hello")
        assert result == b"hello"
    
    def test_invalid_bytes_type_raises(self):
        """Test invalid type raises error."""
        with pytest.raises(TypeConversionError):
            convert_to_bytes(12345)


# =============================================================================
# DateTime Conversion Tests
# =============================================================================

class TestDateTimeConversion:
    """Tests for datetime conversion."""
    
    def test_convert_datetime_object(self):
        """Test converting datetime object."""
        dt = datetime(2024, 1, 15, 12, 30, 0)
        result = convert_to_datetime(dt)
        assert result == dt
    
    def test_convert_date_to_datetime(self):
        """Test converting date to datetime."""
        d = date(2024, 1, 15)
        result = convert_to_datetime(d)
        assert result.date() == d
        assert result.time() == time(0, 0, 0)
    
    def test_convert_string_to_datetime(self):
        """Test converting string to datetime."""
        result = convert_to_datetime("2024-01-15 12:30:00")
        assert result.year == 2024
        assert result.hour == 12
    
    def test_convert_iso_string_to_datetime(self):
        """Test converting ISO format string."""
        result = convert_to_datetime("2024-01-15T12:30:00")
        assert result.year == 2024
    
    def test_convert_timestamp_to_datetime(self):
        """Test converting timestamp to datetime."""
        ts = 1705329000  # 2024-01-15 12:30:00 UTC
        result = convert_to_datetime(ts)
        assert isinstance(result, datetime)
    
    def test_invalid_datetime_raises(self):
        """Test invalid datetime string raises error."""
        with pytest.raises(TypeConversionError):
            convert_to_datetime("not a date")


# =============================================================================
# Type Mapping Tests
# =============================================================================

class TestTypeMapping:
    """Tests for type mapping functions."""
    
    def test_get_postgres_type_int(self):
        """Test getting PostgreSQL type for int."""
        assert get_postgres_type(int) == "INTEGER"
    
    def test_get_postgres_type_str(self):
        """Test getting PostgreSQL type for str."""
        assert get_postgres_type(str) == "TEXT"
    
    def test_get_postgres_type_bool(self):
        """Test getting PostgreSQL type for bool."""
        assert get_postgres_type(bool) == "BOOLEAN"
    
    def test_get_postgres_type_float(self):
        """Test getting PostgreSQL type for float."""
        assert get_postgres_type(float) == "DOUBLE PRECISION"
    
    def test_get_postgres_type_datetime(self):
        """Test getting PostgreSQL type for datetime."""
        assert get_postgres_type(datetime) == "TIMESTAMPTZ"
    
    def test_get_postgres_type_date(self):
        """Test getting PostgreSQL type for date."""
        assert get_postgres_type(date) == "DATE"
    
    def test_get_postgres_type_bytes(self):
        """Test getting PostgreSQL type for bytes."""
        assert get_postgres_type(bytes) == "BYTEA"
    
    def test_get_postgres_type_uuid(self):
        """Test getting PostgreSQL type for UUID."""
        assert get_postgres_type(uuid.UUID) == "UUID"
    
    def test_get_postgres_type_dict(self):
        """Test getting PostgreSQL type for dict."""
        assert get_postgres_type(dict) == "JSONB"
    
    def test_get_python_type_integer(self):
        """Test getting Python type for INTEGER."""
        assert get_python_type("INTEGER") == int
    
    def test_get_python_type_text(self):
        """Test getting Python type for TEXT."""
        assert get_python_type("TEXT") == str
    
    def test_get_python_type_boolean(self):
        """Test getting Python type for BOOLEAN."""
        assert get_python_type("BOOLEAN") == bool
    
    def test_get_python_type_jsonb(self):
        """Test getting Python type for JSONB."""
        assert get_python_type("JSONB") == dict
    
    def test_get_python_type_array(self):
        """Test getting Python type for array."""
        assert get_python_type("INTEGER[]") == list


# =============================================================================
# Array Conversion Tests
# =============================================================================

class TestArrayConversion:
    """Tests for array conversion."""
    
    def test_convert_empty_array(self):
        """Test converting empty array."""
        result = convert_array_to_postgres([])
        assert result == []
    
    def test_convert_int_array(self):
        """Test converting int array."""
        result = convert_array_to_postgres([1, 2, 3])
        assert result == [1, 2, 3]
    
    def test_convert_array_from_postgres(self):
        """Test converting array from PostgreSQL."""
        result = convert_array_from_postgres([1, 2, 3], int)
        assert result == [1, 2, 3]
    
    def test_convert_empty_array_from_postgres(self):
        """Test converting empty array from PostgreSQL."""
        result = convert_array_from_postgres([], int)
        assert result == []

