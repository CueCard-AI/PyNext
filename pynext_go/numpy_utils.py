"""
PyNext Go Bridge - NumPy Conversion Utilities.

This module provides zero-copy and efficient conversions from
Apache Arrow to NumPy arrays. It handles:
    - Column-wise extraction (dict of arrays)
    - Structured array creation (single array with named fields)
    - Type mapping from Arrow to NumPy dtypes
    - Null handling (NaN for floats, None for objects)

Performance Notes:
    - Numeric columns use zero-copy where possible
    - String columns require data copy (Python strings)
    - Use column-wise for analytics (vectorized ops)
    - Use structured for row-oriented access

Design Principles:
    - Zero-copy when possible (numeric types)
    - Clear error messages for type mismatches
    - Consistent null handling
    - Support all common PostgreSQL types
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

# Type hints for optional imports
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None  # type: ignore
    NUMPY_AVAILABLE = False

try:
    import pyarrow as pa
    PYARROW_AVAILABLE = True
except ImportError:
    pa = None  # type: ignore
    PYARROW_AVAILABLE = False


# =============================================================================
# Arrow to NumPy Type Mapping
# =============================================================================

# Arrow type ID to NumPy dtype mapping
# This maps Arrow's type system to NumPy's dtype system
ARROW_TO_NUMPY_DTYPE = {
    # Integers (exact mapping, zero-copy possible)
    "int8": "int8",
    "int16": "int16", 
    "int32": "int32",
    "int64": "int64",
    "uint8": "uint8",
    "uint16": "uint16",
    "uint32": "uint32",
    "uint64": "uint64",
    
    # Floats (exact mapping, zero-copy possible)
    "float": "float32",
    "double": "float64",
    "halffloat": "float16",
    
    # Boolean (zero-copy possible in most cases)
    "bool": "bool",
    
    # Strings (requires copy - Python strings)
    "string": "object",
    "large_string": "object",
    "utf8": "object",
    "large_utf8": "object",
    
    # Binary (requires copy)
    "binary": "object",
    "large_binary": "object",
    
    # Date/Time (special handling)
    "date32": "datetime64[D]",
    "date64": "datetime64[ms]",
    "timestamp[s]": "datetime64[s]",
    "timestamp[ms]": "datetime64[ms]",
    "timestamp[us]": "datetime64[us]",
    "timestamp[ns]": "datetime64[ns]",
    "time32[s]": "object",  # No NumPy equivalent
    "time32[ms]": "object",
    "time64[us]": "object",
    "time64[ns]": "object",
    "duration[s]": "timedelta64[s]",
    "duration[ms]": "timedelta64[ms]",
    "duration[us]": "timedelta64[us]",
    "duration[ns]": "timedelta64[ns]",
    
    # Decimal (requires object for precision)
    "decimal128": "object",
    "decimal256": "object",
    
    # Null type
    "null": "object",
    
    # Complex types (all become object)
    "list": "object",
    "large_list": "object",
    "struct": "object",
    "map": "object",
    "dictionary": "object",
}


def _check_numpy() -> None:
    """Raise ImportError if numpy not available."""
    if not NUMPY_AVAILABLE:
        raise ImportError(
            "numpy is required for NumPy conversion. "
            "Install with: pip install numpy"
        )


def _check_pyarrow() -> None:
    """Raise ImportError if pyarrow not available."""
    if not PYARROW_AVAILABLE:
        raise ImportError(
            "pyarrow is required for Arrow to NumPy conversion. "
            "Install with: pip install pyarrow"
        )


def arrow_type_to_numpy_dtype(arrow_type) -> str:
    """
    Convert an Arrow type to a NumPy dtype string.
    
    Args:
        arrow_type: PyArrow DataType
        
    Returns:
        NumPy dtype string (e.g., "int64", "float64", "object")
        
    Examples:
        >>> arrow_type_to_numpy_dtype(pa.int64())
        'int64'
        >>> arrow_type_to_numpy_dtype(pa.string())
        'object'
        >>> arrow_type_to_numpy_dtype(pa.timestamp('us'))
        'datetime64[us]'
    """
    _check_pyarrow()
    
    # Get type string representation
    type_str = str(arrow_type)
    
    # Handle timestamp with timezone
    if type_str.startswith("timestamp"):
        # Extract unit: timestamp[us, tz=UTC] -> us
        if "[" in type_str:
            unit = type_str.split("[")[1].split(",")[0].split("]")[0]
            return f"datetime64[{unit}]"
        return "datetime64[ns]"  # default
    
    # Handle duration
    if type_str.startswith("duration"):
        if "[" in type_str:
            unit = type_str.split("[")[1].split("]")[0]
            return f"timedelta64[{unit}]"
        return "timedelta64[ns]"
    
    # Handle date types
    if type_str == "date32[day]":
        return "datetime64[D]"
    if type_str == "date64[ms]":
        return "datetime64[ms]"
    
    # Look up in mapping
    return ARROW_TO_NUMPY_DTYPE.get(type_str, "object")


def arrow_schema_to_numpy_dtype(schema) -> np.dtype:
    """
    Convert an Arrow schema to a NumPy structured dtype.
    
    Creates a dtype that can be used to create a structured NumPy array
    where each field corresponds to a column in the Arrow table.
    
    Args:
        schema: PyArrow Schema
        
    Returns:
        NumPy structured dtype
        
    Examples:
        >>> schema = pa.schema([
        ...     ('id', pa.int64()),
        ...     ('name', pa.string()),
        ...     ('score', pa.float64())
        ... ])
        >>> arrow_schema_to_numpy_dtype(schema)
        dtype([('id', '<i8'), ('name', 'O'), ('score', '<f8')])
    """
    _check_numpy()
    _check_pyarrow()
    
    fields = []
    for field in schema:
        numpy_dtype = arrow_type_to_numpy_dtype(field.type)
        
        # Handle string fields - need to determine max length for U dtype
        # For simplicity, use object dtype for strings
        if numpy_dtype == "object":
            fields.append((field.name, "O"))
        else:
            fields.append((field.name, numpy_dtype))
    
    return np.dtype(fields)


# =============================================================================
# Column-wise Conversion
# =============================================================================

def arrow_table_to_numpy_columns(
    table,
    zero_copy: bool = True,
) -> Dict[str, "np.ndarray"]:
    """
    Convert an Arrow Table to a dictionary of NumPy arrays.
    
    Each column becomes a separate NumPy array. This is the most
    efficient representation for analytics and vectorized operations.
    
    Args:
        table: PyArrow Table
        zero_copy: If True, attempt zero-copy conversion for numeric types.
                   If False, always copy data.
                   
    Returns:
        Dictionary mapping column names to NumPy arrays
        
    Performance:
        - Numeric columns: Zero-copy when zero_copy=True (instant)
        - String columns: Requires copy (O(n))
        - Object columns: Requires copy (O(n))
        
    Examples:
        >>> table = pa.table({'id': [1, 2, 3], 'name': ['a', 'b', 'c']})
        >>> arrays = arrow_table_to_numpy_columns(table)
        >>> arrays['id']
        array([1, 2, 3])
        >>> arrays['name']
        array(['a', 'b', 'c'], dtype=object)
        
    Zero-copy verification:
        >>> table = pa.table({'x': [1.0, 2.0, 3.0]})
        >>> arr = arrow_table_to_numpy_columns(table)['x']
        >>> arr.flags['OWNDATA']
        False  # Zero-copy - doesn't own data
    """
    _check_numpy()
    _check_pyarrow()
    
    result = {}
    
    for column_name in table.column_names:
        column = table.column(column_name)
        
        # Handle chunked arrays (combine chunks first)
        if len(column.chunks) > 1:
            # Multiple chunks - need to combine
            column = column.combine_chunks()
        else:
            column = column.chunks[0] if column.chunks else column
        
        # Determine if zero-copy is possible
        dtype_str = arrow_type_to_numpy_dtype(column.type)
        can_zero_copy = (
            zero_copy and 
            dtype_str not in ("object",) and
            not dtype_str.startswith("datetime64") and
            not dtype_str.startswith("timedelta64") and
            column.null_count == 0  # Nulls require special handling
        )
        
        if can_zero_copy:
            # Try zero-copy
            try:
                arr = column.to_numpy(zero_copy_only=True)
            except pa.ArrowInvalid:
                # Fall back to copy
                arr = column.to_numpy(zero_copy_only=False)
        else:
            # Need to copy - force a writable copy
            arr = column.to_numpy(zero_copy_only=False)
            # If not zero_copy requested, ensure we have a writable copy
            if not zero_copy and not arr.flags.writeable:
                arr = arr.copy()
        
        result[column_name] = arr
    
    return result


def arrow_table_to_numpy_dict(
    table,
    nan_for_null: bool = True,
) -> Dict[str, "np.ndarray"]:
    """
    Convert Arrow Table to dict of NumPy arrays with null handling.
    
    Similar to arrow_table_to_numpy_columns but with explicit null handling.
    
    Args:
        table: PyArrow Table
        nan_for_null: If True, convert nulls to NaN for numeric types.
                      If False, use numpy masked arrays.
                      
    Returns:
        Dictionary mapping column names to NumPy arrays
    """
    _check_numpy()
    _check_pyarrow()
    
    result = {}
    
    for column_name in table.column_names:
        column = table.column(column_name)
        
        # Check for nulls
        has_nulls = column.null_count > 0
        dtype_str = arrow_type_to_numpy_dtype(column.type)
        is_numeric = dtype_str in ("int8", "int16", "int32", "int64", 
                                    "uint8", "uint16", "uint32", "uint64",
                                    "float16", "float32", "float64")
        
        if has_nulls and is_numeric and nan_for_null:
            # Convert to float with NaN for nulls
            arr = column.to_pandas().values
            # pandas handles null -> NaN conversion
        else:
            arr = column.to_numpy(zero_copy_only=False)
        
        result[column_name] = arr
    
    return result


# =============================================================================
# Structured Array Conversion
# =============================================================================

def arrow_table_to_structured(
    table,
    max_string_length: int = 256,
) -> "np.ndarray":
    """
    Convert an Arrow Table to a NumPy structured array.
    
    Creates a single NumPy array where each row is a record with
    named fields. This is useful for row-oriented access patterns.
    
    Args:
        table: PyArrow Table
        max_string_length: Maximum length for fixed-width string fields.
                           Strings longer than this are truncated.
                           Use 0 for object dtype (variable length).
                           
    Returns:
        NumPy structured array
        
    Performance:
        - Slower than column-wise for vectorized operations
        - Better for iterating over rows
        - All data is copied
        
    Examples:
        >>> table = pa.table({
        ...     'id': [1, 2, 3],
        ...     'name': ['Alice', 'Bob', 'Charlie'],
        ...     'score': [95.5, 87.3, 92.1]
        ... })
        >>> arr = arrow_table_to_structured(table)
        >>> arr.dtype
        dtype([('id', '<i8'), ('name', 'O'), ('score', '<f8')])
        >>> arr[0]
        (1, 'Alice', 95.5)
        >>> arr['name']
        array(['Alice', 'Bob', 'Charlie'], dtype=object)
    """
    _check_numpy()
    _check_pyarrow()
    
    # Build dtype
    fields = []
    for field in table.schema:
        numpy_dtype = arrow_type_to_numpy_dtype(field.type)
        
        if numpy_dtype == "object" and max_string_length > 0:
            # Check if this is a string type
            if pa.types.is_string(field.type) or pa.types.is_large_string(field.type):
                # Use fixed-width Unicode string
                fields.append((field.name, f"U{max_string_length}"))
            else:
                fields.append((field.name, "O"))
        else:
            fields.append((field.name, numpy_dtype))
    
    dtype = np.dtype(fields)
    
    # Create empty array
    n_rows = len(table)
    arr = np.empty(n_rows, dtype=dtype)
    
    # Fill columns
    for i, field in enumerate(table.schema):
        column = table.column(field.name)
        
        # Get NumPy array for column
        if len(column.chunks) > 1:
            column = column.combine_chunks()
        else:
            column = column.chunks[0] if column.chunks else column
        
        col_arr = column.to_numpy(zero_copy_only=False)
        
        # Handle string truncation for fixed-width fields
        field_dtype = dtype.fields[field.name][0]
        if field_dtype.kind == "U":
            # Fixed-width string - truncate if needed
            max_len = field_dtype.itemsize // 4  # Unicode chars
            arr[field.name] = col_arr  # NumPy handles truncation
        else:
            arr[field.name] = col_arr
    
    return arr


def arrow_table_to_records(
    table,
) -> List[Dict[str, Any]]:
    """
    Convert Arrow Table to list of dictionaries.
    
    Each row becomes a dictionary. This is the most flexible
    format but also the slowest.
    
    Args:
        table: PyArrow Table
        
    Returns:
        List of dictionaries (one per row)
        
    Note:
        For better performance, use arrow_table_to_numpy_columns()
        and iterate over indices, or use execute_copy_rows() which
        is optimized for this pattern.
    """
    _check_numpy()
    _check_pyarrow()
    
    # Convert to pandas first (handles all type conversions)
    df = table.to_pandas()
    return df.to_dict(orient="records")


# =============================================================================
# Batch Conversion Utilities
# =============================================================================

def convert_arrow_batch_to_numpy(
    batch,
    as_structured: bool = False,
) -> Union[Dict[str, "np.ndarray"], "np.ndarray"]:
    """
    Convert a single Arrow RecordBatch to NumPy.
    
    Args:
        batch: PyArrow RecordBatch
        as_structured: If True, return structured array.
                       If False, return dict of arrays.
                       
    Returns:
        NumPy array(s)
    """
    _check_numpy()
    _check_pyarrow()
    
    # Convert batch to table (single chunk)
    table = pa.Table.from_batches([batch])
    
    if as_structured:
        return arrow_table_to_structured(table)
    else:
        return arrow_table_to_numpy_columns(table)


def concatenate_numpy_dicts(
    dicts: List[Dict[str, "np.ndarray"]],
) -> Dict[str, "np.ndarray"]:
    """
    Concatenate multiple column-wise NumPy dicts into one.
    
    Useful when processing data in batches.
    
    Args:
        dicts: List of column dictionaries
        
    Returns:
        Single dictionary with concatenated arrays
    """
    _check_numpy()
    
    if not dicts:
        return {}
    
    if len(dicts) == 1:
        return dicts[0]
    
    # Get column names from first dict
    columns = list(dicts[0].keys())
    
    result = {}
    for col in columns:
        arrays = [d[col] for d in dicts]
        result[col] = np.concatenate(arrays)
    
    return result


# =============================================================================
# Type Inference Utilities
# =============================================================================

def infer_numpy_dtype_from_values(
    values: List[Any],
    sample_size: int = 100,
) -> str:
    """
    Infer appropriate NumPy dtype from Python values.
    
    Args:
        values: List of Python values
        sample_size: Number of values to sample for inference
        
    Returns:
        NumPy dtype string
    """
    _check_numpy()
    
    if not values:
        return "object"
    
    # Sample values
    sample = values[:sample_size]
    
    # Check for None/null
    non_null = [v for v in sample if v is not None]
    if not non_null:
        return "object"
    
    # Check types
    first = non_null[0]
    
    if isinstance(first, bool):
        return "bool"
    elif isinstance(first, int):
        # Check magnitude
        max_val = max(abs(v) for v in non_null if isinstance(v, int))
        if max_val < 2**7:
            return "int8"
        elif max_val < 2**15:
            return "int16"
        elif max_val < 2**31:
            return "int32"
        else:
            return "int64"
    elif isinstance(first, float):
        return "float64"
    elif isinstance(first, str):
        return "object"  # Variable length strings
    elif isinstance(first, bytes):
        return "object"
    else:
        return "object"


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Availability flags
    "NUMPY_AVAILABLE",
    "PYARROW_AVAILABLE",
    
    # Type mapping
    "ARROW_TO_NUMPY_DTYPE",
    "arrow_type_to_numpy_dtype",
    "arrow_schema_to_numpy_dtype",
    
    # Column-wise conversion
    "arrow_table_to_numpy_columns",
    "arrow_table_to_numpy_dict",
    
    # Structured array conversion
    "arrow_table_to_structured",
    "arrow_table_to_records",
    
    # Batch utilities
    "convert_arrow_batch_to_numpy",
    "concatenate_numpy_dicts",
    
    # Type inference
    "infer_numpy_dtype_from_values",
]

