"""
PyNext Database Field System.

Parses Python type hints into database field definitions.
Handles auto-fields (id, created_at, updated_at) automatically.

Design: Stupid simple - just use Python types, we handle the rest.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)
from uuid import UUID

T = TypeVar("T")


class SQLType(Enum):
    """SQL column types."""
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    REAL = "REAL"
    DOUBLE = "DOUBLE PRECISION"
    DECIMAL = "DECIMAL"
    VARCHAR = "VARCHAR"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP"
    DATE = "DATE"
    TIME = "TIME"
    JSON = "JSON"
    JSONB = "JSONB"
    UUID = "UUID"
    BLOB = "BLOB"


@dataclass
class FieldInfo:
    """
    Information about a model field.
    
    Attributes:
        name: Field name
        python_type: Original Python type hint
        sql_type: Corresponding SQL type
        nullable: Whether NULL is allowed
        default: Default value (or None)
        default_factory: Callable to generate default (for mutable types)
        primary_key: Whether this is the primary key
        auto_increment: Whether to auto-increment (for primary keys)
        auto_now: Set to current time on every save
        auto_now_add: Set to current time on first save only
        max_length: Maximum length for VARCHAR
        foreign_key: Target table for FK (e.g., "users")
        unique: Whether value must be unique
        index: Whether to create an index
        validators: List of validator functions
    """
    name: str
    python_type: Type
    sql_type: SQLType
    nullable: bool = False
    default: Any = None
    default_factory: Optional[Callable[[], Any]] = None
    primary_key: bool = False
    auto_increment: bool = False
    auto_now: bool = False
    auto_now_add: bool = False
    max_length: Optional[int] = None
    foreign_key: Optional[str] = None
    unique: bool = False
    index: bool = False
    validators: List[Callable[[Any], Any]] = dataclass_field(default_factory=list)
    
    def __post_init__(self):
        # Auto-detect foreign key from name pattern
        if self.name.endswith("_id") and not self.foreign_key:
            # author_id -> authors
            table_name = self.name[:-3] + "s"
            self.foreign_key = table_name
            self.index = True  # FKs should be indexed
    
    @property
    def has_default(self) -> bool:
        """Check if field has a default value."""
        return self.default is not None or self.default_factory is not None
    
    def get_default(self) -> Any:
        """Get the default value (or call factory)."""
        if self.default_factory:
            return self.default_factory()
        return self.default
    
    def to_sql_column(self) -> str:
        """Generate SQL column definition."""
        parts = [self.name]
        
        # Type
        if self.sql_type == SQLType.VARCHAR:
            length = self.max_length or 255
            parts.append(f"VARCHAR({length})")
        else:
            parts.append(self.sql_type.value)
        
        # Constraints
        if self.primary_key:
            parts.append("PRIMARY KEY")
            if self.auto_increment:
                parts.append("AUTOINCREMENT")
        
        if not self.nullable and not self.primary_key:
            parts.append("NOT NULL")
        
        if self.unique and not self.primary_key:
            parts.append("UNIQUE")
        
        if self.default is not None and not callable(self.default):
            if isinstance(self.default, str):
                parts.append(f"DEFAULT '{self.default}'")
            elif isinstance(self.default, bool):
                parts.append(f"DEFAULT {1 if self.default else 0}")
            else:
                parts.append(f"DEFAULT {self.default}")
        
        return " ".join(parts)


# Type mapping: Python type -> (SQLType, nullable, max_length)
TYPE_MAP: Dict[Type, Tuple[SQLType, bool, Optional[int]]] = {
    str: (SQLType.VARCHAR, False, 255),
    int: (SQLType.INTEGER, False, None),
    float: (SQLType.REAL, False, None),
    bool: (SQLType.BOOLEAN, False, None),
    datetime: (SQLType.TIMESTAMP, False, None),
    date: (SQLType.DATE, False, None),
    time: (SQLType.TIME, False, None),
    Decimal: (SQLType.DECIMAL, False, None),
    UUID: (SQLType.UUID, False, None),
    bytes: (SQLType.BLOB, False, None),
    dict: (SQLType.JSON, False, None),
    list: (SQLType.JSON, False, None),
}


def parse_type_hint(name: str, type_hint: Any, default: Any = ...) -> FieldInfo:
    """
    Parse a Python type hint into a FieldInfo.
    
    Examples:
        parse_type_hint("name", str) -> FieldInfo(name="name", python_type=str, sql_type=VARCHAR, nullable=False)
        parse_type_hint("age", int, 0) -> FieldInfo(..., default=0)
        parse_type_hint("bio", str | None) -> FieldInfo(..., nullable=True)
        parse_type_hint("tags", list[str]) -> FieldInfo(..., sql_type=JSON)
    """
    import types
    
    origin = get_origin(type_hint)
    args = get_args(type_hint)
    
    nullable = False
    inner_type = type_hint
    
    # Handle Optional[X] and X | None (UnionType in Python 3.10+)
    if origin is Union or isinstance(type_hint, types.UnionType):
        if not args:
            args = get_args(type_hint)
        # Filter out NoneType
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1 and type(None) in args:
            nullable = True
            inner_type = non_none_args[0]
            origin = get_origin(inner_type)
            args = get_args(inner_type)
    
    # Handle list[X], dict[X, Y], etc.
    if origin is list or origin is List:
        sql_type = SQLType.JSON
        python_type = list
    elif origin is dict or origin is Dict:
        sql_type = SQLType.JSON
        python_type = dict
    elif origin is set or origin is Set:
        sql_type = SQLType.JSON
        python_type = set
    elif inner_type in TYPE_MAP:
        sql_type, _, max_length = TYPE_MAP[inner_type]
        python_type = inner_type
    else:
        # Default to JSON for complex types
        sql_type = SQLType.JSON
        python_type = inner_type
        max_length = None
    
    # Handle default value
    has_default = default is not ...
    default_value = default if has_default else None
    default_factory = None
    
    # Mutable defaults need factories
    if has_default and isinstance(default, (list, dict, set)):
        default_factory = lambda d=default: type(d)(d)
        default_value = None
    
    # Infer max_length for strings
    max_length = None
    if sql_type == SQLType.VARCHAR:
        max_length = 255  # Default
    
    return FieldInfo(
        name=name,
        python_type=python_type,
        sql_type=sql_type,
        nullable=nullable,
        default=default_value,
        default_factory=default_factory,
        max_length=max_length,
    )


def create_auto_fields() -> Dict[str, FieldInfo]:
    """
    Create the automatic fields every model gets.
    
    Returns:
        id: Primary key, auto-increment
        created_at: Timestamp, set on insert
        updated_at: Timestamp, set on insert and update
    """
    return {
        "id": FieldInfo(
            name="id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            nullable=False,
            primary_key=True,
            auto_increment=True,
        ),
        "created_at": FieldInfo(
            name="created_at",
            python_type=datetime,
            sql_type=SQLType.TIMESTAMP,
            nullable=True,  # Allow None before insert
            auto_now_add=True,
        ),
        "updated_at": FieldInfo(
            name="updated_at",
            python_type=datetime,
            sql_type=SQLType.TIMESTAMP,
            nullable=True,  # Allow None before insert
            auto_now=True,
        ),
    }


class Field(Generic[T]):
    """
    Explicit field definition for advanced use cases.
    
    Most of the time, just use type hints. Use Field() when you need:
    - Custom max_length
    - Unique constraint
    - Custom validators
    - Explicit foreign key
    
    Examples:
        class User(Table):
            # Simple - just use type hint
            name: str
            
            # Advanced - use Field
            email: str = Field(unique=True, max_length=100)
            bio: str = Field(max_length=1000)
            role: str = Field(default="user", validators=[validate_role])
    """
    
    def __init__(
        self,
        default: Any = ...,
        *,
        default_factory: Optional[Callable[[], Any]] = None,
        max_length: Optional[int] = None,
        unique: bool = False,
        index: bool = False,
        primary_key: bool = False,
        foreign_key: Optional[str] = None,
        validators: Optional[List[Callable[[Any], Any]]] = None,
        nullable: Optional[bool] = None,
    ):
        self.default = default
        self.default_factory = default_factory
        self.max_length = max_length
        self.unique = unique
        self.index = index
        self.primary_key = primary_key
        self.foreign_key = foreign_key
        self.validators = validators or []
        self._nullable = nullable
    
    def to_field_info(self, name: str, type_hint: Any) -> FieldInfo:
        """Convert to FieldInfo, combining type hint with Field options."""
        # Start with type hint parsing
        info = parse_type_hint(name, type_hint, self.default)
        
        # Override with explicit Field options
        if self.max_length is not None:
            info.max_length = self.max_length
        if self.unique:
            info.unique = True
        if self.index:
            info.index = True
        if self.primary_key:
            info.primary_key = True
            info.auto_increment = True
        if self.foreign_key:
            info.foreign_key = self.foreign_key
        if self.validators:
            info.validators = self.validators
        if self._nullable is not None:
            info.nullable = self._nullable
        if self.default_factory:
            info.default_factory = self.default_factory
            info.default = None
        
        return info


def serialize_value(value: Any, field: FieldInfo) -> Any:
    """
    Serialize a Python value for database storage.
    
    Examples:
        serialize_value({"a": 1}, json_field) -> '{"a": 1}'
        serialize_value(datetime.now(), timestamp_field) -> "2024-01-01T12:00:00"
    """
    if value is None:
        return None
    
    if field.sql_type == SQLType.JSON or field.sql_type == SQLType.JSONB:
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value
    
    if field.sql_type == SQLType.TIMESTAMP:
        if isinstance(value, datetime):
            return value.isoformat()
        return value
    
    if field.sql_type == SQLType.DATE:
        if isinstance(value, date):
            return value.isoformat()
        return value
    
    if field.sql_type == SQLType.TIME:
        if isinstance(value, time):
            return value.isoformat()
        return value
    
    if field.sql_type == SQLType.UUID:
        if isinstance(value, UUID):
            return str(value)
        return value
    
    if field.sql_type == SQLType.BOOLEAN:
        return 1 if value else 0
    
    return value


def deserialize_value(value: Any, field: FieldInfo) -> Any:
    """
    Deserialize a database value to Python type.
    
    Examples:
        deserialize_value('{"a": 1}', json_field) -> {"a": 1}
        deserialize_value("2024-01-01T12:00:00", timestamp_field) -> datetime(...)
    """
    if value is None:
        return None
    
    if field.sql_type == SQLType.JSON or field.sql_type == SQLType.JSONB:
        if isinstance(value, str):
            return json.loads(value)
        return value
    
    if field.sql_type == SQLType.TIMESTAMP:
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value
    
    if field.sql_type == SQLType.DATE:
        if isinstance(value, str):
            return date.fromisoformat(value)
        return value
    
    if field.sql_type == SQLType.TIME:
        if isinstance(value, str):
            return time.fromisoformat(value)
        return value
    
    if field.sql_type == SQLType.UUID:
        if isinstance(value, str):
            return UUID(value)
        return value
    
    if field.sql_type == SQLType.BOOLEAN:
        return bool(value)
    
    return value

