"""
PostgreSQL Type Converters.

This module handles conversion between Python types and PostgreSQL types.
It ensures that data flows correctly between your Python code and PostgreSQL.

Type Mapping Overview:

| Python Type | PostgreSQL Type | Notes |
|-------------|-----------------|-------|
| int | INTEGER/BIGINT | Auto-detects size |
| float | DOUBLE PRECISION | 64-bit float |
| str | TEXT/VARCHAR | Unlimited length |
| bool | BOOLEAN | True/False |
| datetime | TIMESTAMPTZ | Always timezone-aware |
| date | DATE | Date only |
| time | TIME | Time only |
| bytes | BYTEA | Binary data |
| list | ARRAY | PostgreSQL arrays |
| dict | JSONB | JSON with indexing |
| Decimal | NUMERIC | Exact decimal |
| UUID | UUID | UUID type |

AI-Friendly Design:
- Each converter is a simple function
- Clear error messages with examples
- Type hints on all functions
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union


class TypeConversionError(Exception):
    """Error converting between Python and PostgreSQL types.
    
    Raised when:
    - A value cannot be converted to the target type
    - An unsupported type is encountered
    
    The error message includes:
    - What type was expected
    - What value was provided
    - How to fix it
    """
    pass


# =============================================================================
# Python → PostgreSQL Converters
# =============================================================================

def python_to_postgres(value: Any, target_type: Optional[str] = None) -> Any:
    """Convert a Python value to PostgreSQL format.
    
    This is the main conversion function. It automatically detects
    the Python type and converts to the appropriate PostgreSQL format.
    
    Args:
        value: Any Python value
        target_type: Optional PostgreSQL type hint (e.g., "JSONB", "UUID")
    
    Returns:
        Value in PostgreSQL-compatible format
    
    Examples:
        # Automatic conversion
        python_to_postgres(123)           # 123 (INTEGER)
        python_to_postgres("hello")       # "hello" (TEXT)
        python_to_postgres(True)          # True (BOOLEAN)
        python_to_postgres(datetime.now())  # datetime (TIMESTAMPTZ)
        
        # Explicit type
        python_to_postgres({"a": 1}, "JSONB")  # JSON string
    """
    if value is None:
        return None
    
    # Handle explicit target types
    if target_type:
        target_upper = target_type.upper()
        if target_upper == "JSONB" or target_upper == "JSON":
            return convert_to_json(value)
        elif target_upper == "UUID":
            return convert_to_uuid(value)
        elif target_upper == "BYTEA":
            return convert_to_bytes(value)
    
    # Auto-detect type
    if isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return value
    elif isinstance(value, float):
        return value
    elif isinstance(value, str):
        return value
    elif isinstance(value, Decimal):
        return value  # asyncpg handles Decimal natively
    elif isinstance(value, datetime):
        return ensure_timezone_aware(value)
    elif isinstance(value, date):
        return value
    elif isinstance(value, time):
        return value
    elif isinstance(value, timedelta):
        return value
    elif isinstance(value, bytes):
        return value
    elif isinstance(value, uuid.UUID):
        return value
    elif isinstance(value, (list, tuple)):
        return [python_to_postgres(item) for item in value]
    elif isinstance(value, dict):
        return convert_to_json(value)
    elif isinstance(value, Enum):
        return value.value
    else:
        # Try JSON as last resort
        try:
            return convert_to_json(value)
        except (TypeError, ValueError):
            raise TypeConversionError(
                f"Cannot convert {type(value).__name__} to PostgreSQL type.\n"
                f"Value: {value!r}\n"
                "Supported types: int, float, str, bool, datetime, date, "
                "time, bytes, list, dict, Decimal, UUID, Enum"
            )


def ensure_timezone_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware.
    
    PostgreSQL's TIMESTAMPTZ expects timezone-aware datetimes.
    This function adds UTC timezone if the datetime is naive.
    
    Args:
        dt: datetime object
    
    Returns:
        Timezone-aware datetime
    
    Example:
        naive = datetime(2024, 1, 1, 12, 0, 0)
        aware = ensure_timezone_aware(naive)  # Now has UTC timezone
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def convert_to_json(value: Any) -> str:
    """Convert a value to JSON string for JSONB column.
    
    Args:
        value: Any JSON-serializable value
    
    Returns:
        JSON string
    
    Raises:
        TypeConversionError: If value is not JSON-serializable
    """
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError) as e:
        raise TypeConversionError(
            f"Cannot convert to JSON: {e}\n"
            f"Value: {value!r}\n"
            "Make sure all nested values are JSON-serializable."
        )


def convert_to_uuid(value: Any) -> uuid.UUID:
    """Convert a value to UUID.
    
    Args:
        value: UUID, string, or bytes
    
    Returns:
        uuid.UUID object
    
    Raises:
        TypeConversionError: If value cannot be converted to UUID
    """
    if isinstance(value, uuid.UUID):
        return value
    
    try:
        if isinstance(value, str):
            return uuid.UUID(value)
        elif isinstance(value, bytes):
            return uuid.UUID(bytes=value)
        else:
            raise TypeConversionError(
                f"Cannot convert {type(value).__name__} to UUID.\n"
                f"Value: {value!r}\n"
                "Expected: UUID, string, or bytes"
            )
    except ValueError as e:
        raise TypeConversionError(
            f"Invalid UUID format: {e}\n"
            f"Value: {value!r}\n"
            "Example: '550e8400-e29b-41d4-a716-446655440000'"
        )


def convert_to_bytes(value: Any) -> bytes:
    """Convert a value to bytes for BYTEA column.
    
    Args:
        value: bytes, str, or bytearray
    
    Returns:
        bytes object
    
    Raises:
        TypeConversionError: If value cannot be converted to bytes
    """
    if isinstance(value, bytes):
        return value
    elif isinstance(value, bytearray):
        return bytes(value)
    elif isinstance(value, str):
        return value.encode("utf-8")
    else:
        raise TypeConversionError(
            f"Cannot convert {type(value).__name__} to bytes.\n"
            f"Value: {value!r}\n"
            "Expected: bytes, bytearray, or str"
        )


# =============================================================================
# PostgreSQL → Python Converters
# =============================================================================

def postgres_to_python(value: Any, python_type: Type) -> Any:
    """Convert a PostgreSQL value to Python type.
    
    Args:
        value: Value from PostgreSQL
        python_type: Target Python type
    
    Returns:
        Value converted to the target type
    
    Examples:
        postgres_to_python(123, int)        # 123
        postgres_to_python("2024-01-01", date)  # date(2024, 1, 1)
        postgres_to_python('{"a": 1}', dict)    # {"a": 1}
    """
    if value is None:
        return None
    
    # Already the right type
    if isinstance(value, python_type):
        return value
    
    # Handle special conversions
    if python_type == bool:
        return bool(value)
    elif python_type == int:
        return int(value)
    elif python_type == float:
        return float(value)
    elif python_type == str:
        return str(value)
    elif python_type == Decimal:
        return Decimal(str(value))
    elif python_type == datetime:
        return convert_to_datetime(value)
    elif python_type == date:
        return convert_to_date(value)
    elif python_type == time:
        return convert_to_time(value)
    elif python_type == bytes:
        return convert_to_bytes(value)
    elif python_type == uuid.UUID:
        return convert_to_uuid(value)
    elif python_type == dict:
        return convert_from_json(value)
    elif python_type == list:
        if isinstance(value, (list, tuple)):
            return list(value)
        return convert_from_json(value)
    else:
        # Return as-is for complex types
        return value


def convert_to_datetime(value: Any) -> datetime:
    """Convert a value to datetime.
    
    Args:
        value: datetime, str, int (timestamp), or date
    
    Returns:
        datetime object
    """
    if isinstance(value, datetime):
        return value
    elif isinstance(value, date):
        return datetime.combine(value, time())
    elif isinstance(value, str):
        # Try common formats
        for fmt in [
            "%Y-%m-%d %H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
        ]:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise TypeConversionError(
            f"Cannot parse datetime: {value!r}\n"
            "Expected format: YYYY-MM-DD HH:MM:SS"
        )
    elif isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    else:
        raise TypeConversionError(
            f"Cannot convert {type(value).__name__} to datetime.\n"
            f"Value: {value!r}"
        )


def convert_to_date(value: Any) -> date:
    """Convert a value to date.
    
    Args:
        value: date, datetime, or str
    
    Returns:
        date object
    """
    if isinstance(value, datetime):
        return value.date()
    elif isinstance(value, date):
        return value
    elif isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise TypeConversionError(
                f"Cannot parse date: {value!r}\n"
                "Expected format: YYYY-MM-DD"
            )
    else:
        raise TypeConversionError(
            f"Cannot convert {type(value).__name__} to date.\n"
            f"Value: {value!r}"
        )


def convert_to_time(value: Any) -> time:
    """Convert a value to time.
    
    Args:
        value: time, datetime, or str
    
    Returns:
        time object
    """
    if isinstance(value, datetime):
        return value.time()
    elif isinstance(value, time):
        return value
    elif isinstance(value, str):
        for fmt in ["%H:%M:%S.%f", "%H:%M:%S", "%H:%M"]:
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
        raise TypeConversionError(
            f"Cannot parse time: {value!r}\n"
            "Expected format: HH:MM:SS"
        )
    else:
        raise TypeConversionError(
            f"Cannot convert {type(value).__name__} to time.\n"
            f"Value: {value!r}"
        )


def convert_from_json(value: Any) -> Any:
    """Convert a JSON value to Python dict/list.
    
    Args:
        value: JSON string or already parsed value
    
    Returns:
        Parsed JSON value
    """
    if isinstance(value, (dict, list)):
        return value
    elif isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise TypeConversionError(
                f"Invalid JSON: {e}\n"
                f"Value: {value[:100]!r}..."
            )
    else:
        raise TypeConversionError(
            f"Cannot convert {type(value).__name__} from JSON.\n"
            f"Value: {value!r}"
        )


# =============================================================================
# Type Mapping
# =============================================================================

@dataclass
class TypeMapping:
    """Mapping between Python and PostgreSQL types.
    
    Attributes:
        python_type: Python type class
        postgres_type: PostgreSQL type name
        to_postgres: Function to convert Python → PostgreSQL
        from_postgres: Function to convert PostgreSQL → Python
    """
    python_type: Type
    postgres_type: str
    to_postgres: Callable[[Any], Any] = lambda x: x
    from_postgres: Callable[[Any], Any] = lambda x: x


# Default type mappings
DEFAULT_TYPE_MAPPINGS: Dict[Type, TypeMapping] = {
    int: TypeMapping(int, "INTEGER"),
    float: TypeMapping(float, "DOUBLE PRECISION"),
    str: TypeMapping(str, "TEXT"),
    bool: TypeMapping(bool, "BOOLEAN"),
    bytes: TypeMapping(bytes, "BYTEA", convert_to_bytes),
    datetime: TypeMapping(datetime, "TIMESTAMPTZ", ensure_timezone_aware),
    date: TypeMapping(date, "DATE"),
    time: TypeMapping(time, "TIME"),
    timedelta: TypeMapping(timedelta, "INTERVAL"),
    Decimal: TypeMapping(Decimal, "NUMERIC"),
    uuid.UUID: TypeMapping(uuid.UUID, "UUID", convert_to_uuid, convert_to_uuid),
    dict: TypeMapping(dict, "JSONB", convert_to_json, convert_from_json),
    list: TypeMapping(list, "JSONB", convert_to_json, convert_from_json),
}


def get_postgres_type(python_type: Type) -> str:
    """Get the PostgreSQL type for a Python type.
    
    Args:
        python_type: Python type class
    
    Returns:
        PostgreSQL type name
    
    Example:
        get_postgres_type(int)      # "INTEGER"
        get_postgres_type(str)      # "TEXT"
        get_postgres_type(dict)     # "JSONB"
    """
    # Handle Optional types
    origin = getattr(python_type, "__origin__", None)
    if origin is Union:
        args = getattr(python_type, "__args__", ())
        # Filter out NoneType for Optional
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return get_postgres_type(non_none[0])
    
    # Handle List types
    if origin is list:
        args = getattr(python_type, "__args__", ())
        if args:
            inner_type = get_postgres_type(args[0])
            return f"{inner_type}[]"
        return "JSONB"
    
    # Lookup in mappings
    if python_type in DEFAULT_TYPE_MAPPINGS:
        return DEFAULT_TYPE_MAPPINGS[python_type].postgres_type
    
    # Default to TEXT for unknown types
    return "TEXT"


def get_python_type(postgres_type: str) -> Type:
    """Get the Python type for a PostgreSQL type.
    
    Args:
        postgres_type: PostgreSQL type name
    
    Returns:
        Python type class
    
    Example:
        get_python_type("INTEGER")   # int
        get_python_type("TEXT")      # str
        get_python_type("JSONB")     # dict
    """
    postgres_upper = postgres_type.upper()
    
    # Handle arrays
    if postgres_upper.endswith("[]"):
        return list
    
    # Type mapping
    type_map = {
        "INTEGER": int,
        "INT": int,
        "INT4": int,
        "BIGINT": int,
        "INT8": int,
        "SMALLINT": int,
        "INT2": int,
        "SERIAL": int,
        "BIGSERIAL": int,
        "DOUBLE PRECISION": float,
        "FLOAT8": float,
        "REAL": float,
        "FLOAT4": float,
        "NUMERIC": Decimal,
        "DECIMAL": Decimal,
        "TEXT": str,
        "VARCHAR": str,
        "CHAR": str,
        "CHARACTER VARYING": str,
        "BOOLEAN": bool,
        "BOOL": bool,
        "BYTEA": bytes,
        "TIMESTAMP": datetime,
        "TIMESTAMPTZ": datetime,
        "TIMESTAMP WITH TIME ZONE": datetime,
        "TIMESTAMP WITHOUT TIME ZONE": datetime,
        "DATE": date,
        "TIME": time,
        "TIMETZ": time,
        "INTERVAL": timedelta,
        "UUID": uuid.UUID,
        "JSON": dict,
        "JSONB": dict,
    }
    
    return type_map.get(postgres_upper, str)


# =============================================================================
# Array Handling
# =============================================================================

def convert_array_to_postgres(value: List[Any], element_type: Optional[str] = None) -> List[Any]:
    """Convert a Python list to PostgreSQL array format.
    
    Args:
        value: Python list
        element_type: PostgreSQL element type
    
    Returns:
        List ready for PostgreSQL array
    """
    if not value:
        return []
    
    return [python_to_postgres(item, element_type) for item in value]


def convert_array_from_postgres(value: List[Any], element_type: Type) -> List[Any]:
    """Convert a PostgreSQL array to Python list.
    
    Args:
        value: PostgreSQL array
        element_type: Python element type
    
    Returns:
        Python list with converted elements
    """
    if not value:
        return []
    
    return [postgres_to_python(item, element_type) for item in value]

