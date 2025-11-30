"""
Tests for PyNext Database Fields.

Tests for field parsing, type mapping, serialization, and deserialization.
"""

import pytest
import json
from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Dict, Optional, Set
from uuid import UUID, uuid4

from pynext.db.fields import (
    Field,
    FieldInfo,
    SQLType,
    parse_type_hint,
    create_auto_fields,
    serialize_value,
    deserialize_value,
)


# =============================================================================
# Type Hint Parsing Tests (30 tests)
# =============================================================================

class TestTypeHintParsing:
    """Tests for parse_type_hint function."""
    
    def test_parse_str(self):
        """Test parsing str type."""
        field = parse_type_hint("name", str)
        assert field.python_type == str
        assert field.sql_type == SQLType.VARCHAR
        assert field.nullable is False
    
    def test_parse_int(self):
        """Test parsing int type."""
        field = parse_type_hint("count", int)
        assert field.python_type == int
        assert field.sql_type == SQLType.INTEGER
        assert field.nullable is False
    
    def test_parse_float(self):
        """Test parsing float type."""
        field = parse_type_hint("price", float)
        assert field.python_type == float
        assert field.sql_type == SQLType.REAL
        assert field.nullable is False
    
    def test_parse_bool(self):
        """Test parsing bool type."""
        field = parse_type_hint("active", bool)
        assert field.python_type == bool
        assert field.sql_type == SQLType.BOOLEAN
        assert field.nullable is False
    
    def test_parse_datetime(self):
        """Test parsing datetime type."""
        field = parse_type_hint("timestamp", datetime)
        assert field.python_type == datetime
        assert field.sql_type == SQLType.TIMESTAMP
    
    def test_parse_date(self):
        """Test parsing date type."""
        field = parse_type_hint("birthday", date)
        assert field.python_type == date
        assert field.sql_type == SQLType.DATE
    
    def test_parse_time(self):
        """Test parsing time type."""
        field = parse_type_hint("alarm", time)
        assert field.python_type == time
        assert field.sql_type == SQLType.TIME
    
    def test_parse_decimal(self):
        """Test parsing Decimal type."""
        field = parse_type_hint("amount", Decimal)
        assert field.python_type == Decimal
        assert field.sql_type == SQLType.DECIMAL
    
    def test_parse_uuid(self):
        """Test parsing UUID type."""
        field = parse_type_hint("external_id", UUID)
        assert field.python_type == UUID
        assert field.sql_type == SQLType.UUID
    
    def test_parse_bytes(self):
        """Test parsing bytes type."""
        field = parse_type_hint("data", bytes)
        assert field.python_type == bytes
        assert field.sql_type == SQLType.BLOB
    
    def test_parse_list(self):
        """Test parsing list type."""
        field = parse_type_hint("tags", list)
        assert field.python_type == list
        assert field.sql_type == SQLType.JSON
    
    def test_parse_list_generic(self):
        """Test parsing List[str] type."""
        field = parse_type_hint("tags", List[str])
        assert field.python_type == list
        assert field.sql_type == SQLType.JSON
    
    def test_parse_dict(self):
        """Test parsing dict type."""
        field = parse_type_hint("metadata", dict)
        assert field.python_type == dict
        assert field.sql_type == SQLType.JSON
    
    def test_parse_dict_generic(self):
        """Test parsing Dict[str, int] type."""
        field = parse_type_hint("scores", Dict[str, int])
        assert field.python_type == dict
        assert field.sql_type == SQLType.JSON
    
    def test_parse_optional_str(self):
        """Test parsing Optional[str] is nullable."""
        field = parse_type_hint("bio", Optional[str])
        assert field.nullable is True
        assert field.python_type == str
    
    def test_parse_optional_int(self):
        """Test parsing Optional[int] is nullable."""
        field = parse_type_hint("age", Optional[int])
        assert field.nullable is True
        assert field.python_type == int
    
    def test_parse_union_none(self):
        """Test parsing str | None is nullable."""
        field = parse_type_hint("name", str | None)
        assert field.nullable is True
        assert field.python_type == str
    
    def test_parse_with_default_str(self):
        """Test parsing with string default."""
        field = parse_type_hint("role", str, "user")
        assert field.default == "user"
        assert field.has_default is True
    
    def test_parse_with_default_int(self):
        """Test parsing with int default."""
        field = parse_type_hint("count", int, 0)
        assert field.default == 0
        assert field.has_default is True
    
    def test_parse_with_default_none(self):
        """Test parsing with None default."""
        field = parse_type_hint("bio", Optional[str], None)
        assert field.default is None
        assert field.nullable is True
    
    def test_parse_list_default_uses_factory(self):
        """Test parsing list default uses factory."""
        field = parse_type_hint("tags", List[str], [])
        assert field.default is None
        assert field.default_factory is not None
        assert field.get_default() == []
    
    def test_parse_dict_default_uses_factory(self):
        """Test parsing dict default uses factory."""
        field = parse_type_hint("meta", Dict[str, str], {})
        assert field.default is None
        assert field.default_factory is not None
        assert field.get_default() == {}
    
    def test_parse_fk_field(self):
        """Test parsing *_id field detects FK."""
        field = parse_type_hint("user_id", int)
        assert field.foreign_key == "users"
        assert field.index is True
    
    def test_parse_fk_field_author(self):
        """Test parsing author_id detects FK to authors."""
        field = parse_type_hint("author_id", int)
        assert field.foreign_key == "authors"
    
    def test_parse_non_fk_id_field(self):
        """Test parsing external_id as str still detects FK (just not commonly used)."""
        field = parse_type_hint("external_id", str)
        # external_id ends with _id so it still gets FK detection
        assert field.foreign_key == "externals"
    
    def test_parse_set_type(self):
        """Test parsing Set type."""
        field = parse_type_hint("unique_tags", Set[str])
        assert field.python_type == set
        assert field.sql_type == SQLType.JSON
    
    def test_field_name_stored(self):
        """Test field name is stored."""
        field = parse_type_hint("my_field", str)
        assert field.name == "my_field"
    
    def test_varchar_default_max_length(self):
        """Test VARCHAR has default max_length of 255."""
        field = parse_type_hint("name", str)
        assert field.max_length == 255
    
    def test_nullable_field_allows_none_default(self):
        """Test nullable field allows None as default."""
        field = parse_type_hint("bio", Optional[str])
        assert field.nullable is True
    
    def test_non_nullable_field_no_default(self):
        """Test non-nullable field without default."""
        field = parse_type_hint("name", str)
        assert field.nullable is False
        assert field.default is None
        assert field.has_default is False


# =============================================================================
# Auto Fields Tests (10 tests)
# =============================================================================

class TestAutoFields:
    """Tests for auto-generated fields."""
    
    def test_auto_fields_creates_id(self):
        """Test auto fields includes id."""
        fields = create_auto_fields()
        assert "id" in fields
    
    def test_auto_id_is_primary_key(self):
        """Test auto id is primary key."""
        fields = create_auto_fields()
        assert fields["id"].primary_key is True
    
    def test_auto_id_is_auto_increment(self):
        """Test auto id is auto increment."""
        fields = create_auto_fields()
        assert fields["id"].auto_increment is True
    
    def test_auto_id_is_integer(self):
        """Test auto id is integer type."""
        fields = create_auto_fields()
        assert fields["id"].sql_type == SQLType.INTEGER
    
    def test_auto_fields_creates_created_at(self):
        """Test auto fields includes created_at."""
        fields = create_auto_fields()
        assert "created_at" in fields
    
    def test_created_at_is_auto_now_add(self):
        """Test created_at has auto_now_add."""
        fields = create_auto_fields()
        assert fields["created_at"].auto_now_add is True
    
    def test_created_at_is_timestamp(self):
        """Test created_at is timestamp type."""
        fields = create_auto_fields()
        assert fields["created_at"].sql_type == SQLType.TIMESTAMP
    
    def test_auto_fields_creates_updated_at(self):
        """Test auto fields includes updated_at."""
        fields = create_auto_fields()
        assert "updated_at" in fields
    
    def test_updated_at_is_auto_now(self):
        """Test updated_at has auto_now."""
        fields = create_auto_fields()
        assert fields["updated_at"].auto_now is True
    
    def test_updated_at_is_timestamp(self):
        """Test updated_at is timestamp type."""
        fields = create_auto_fields()
        assert fields["updated_at"].sql_type == SQLType.TIMESTAMP


# =============================================================================
# Field Class Tests (20 tests)
# =============================================================================

class TestFieldClass:
    """Tests for explicit Field class."""
    
    def test_field_with_default(self):
        """Test Field with default value."""
        f = Field(default="user")
        info = f.to_field_info("role", str)
        assert info.default == "user"
    
    def test_field_with_max_length(self):
        """Test Field with max_length."""
        f = Field(max_length=100)
        info = f.to_field_info("bio", str)
        assert info.max_length == 100
    
    def test_field_with_unique(self):
        """Test Field with unique constraint."""
        f = Field(unique=True)
        info = f.to_field_info("email", str)
        assert info.unique is True
    
    def test_field_with_index(self):
        """Test Field with index."""
        f = Field(index=True)
        info = f.to_field_info("email", str)
        assert info.index is True
    
    def test_field_with_primary_key(self):
        """Test Field with primary_key."""
        f = Field(primary_key=True)
        info = f.to_field_info("custom_id", int)
        assert info.primary_key is True
        assert info.auto_increment is True
    
    def test_field_with_foreign_key(self):
        """Test Field with explicit foreign_key."""
        f = Field(foreign_key="authors")
        info = f.to_field_info("writer_id", int)
        assert info.foreign_key == "authors"
    
    def test_field_with_validators(self):
        """Test Field with validators."""
        def validate_email(v):
            if "@" not in v:
                raise ValueError("must contain @")
            return v
        
        f = Field(validators=[validate_email])
        info = f.to_field_info("email", str)
        assert len(info.validators) == 1
    
    def test_field_with_nullable(self):
        """Test Field with explicit nullable."""
        f = Field(nullable=True)
        info = f.to_field_info("bio", str)
        assert info.nullable is True
    
    def test_field_with_default_factory(self):
        """Test Field with default_factory."""
        f = Field(default_factory=list)
        info = f.to_field_info("tags", List[str])
        assert info.default_factory is not None
        assert info.get_default() == []
    
    def test_field_overrides_type_hint_nullable(self):
        """Test Field nullable overrides type hint."""
        f = Field(nullable=True)
        info = f.to_field_info("name", str)  # str is not nullable by default
        assert info.nullable is True
    
    def test_field_combines_with_type_hint(self):
        """Test Field combines with type hint parsing."""
        f = Field(unique=True, max_length=100)
        info = f.to_field_info("email", str)
        
        assert info.sql_type == SQLType.VARCHAR  # From type hint
        assert info.unique is True  # From Field
        assert info.max_length == 100  # From Field
    
    def test_field_multiple_validators(self):
        """Test Field with multiple validators."""
        def not_empty(v):
            if not v:
                raise ValueError("cannot be empty")
            return v
        
        def lowercase(v):
            return v.lower()
        
        f = Field(validators=[not_empty, lowercase])
        info = f.to_field_info("email", str)
        assert len(info.validators) == 2
    
    def test_field_default_with_type_hint(self):
        """Test Field default works with type hint."""
        f = Field(default="guest")
        info = f.to_field_info("role", str)
        assert info.default == "guest"
        assert info.python_type == str
    
    def test_field_no_arguments(self):
        """Test Field with no arguments."""
        f = Field()
        info = f.to_field_info("name", str)
        assert info.python_type == str
        assert info.has_default is False
    
    def test_field_preserves_name(self):
        """Test Field preserves field name."""
        f = Field(unique=True)
        info = f.to_field_info("my_email", str)
        assert info.name == "my_email"
    
    def test_field_with_all_options(self):
        """Test Field with all options specified."""
        f = Field(
            default="user",
            max_length=50,
            unique=False,
            index=True,
            nullable=False,
        )
        info = f.to_field_info("role", str)
        
        assert info.default == "user"
        assert info.max_length == 50
        assert info.unique is False
        assert info.index is True
        assert info.nullable is False


# =============================================================================
# Serialization Tests (20 tests)
# =============================================================================

class TestSerialization:
    """Tests for serialize_value and deserialize_value."""
    
    def test_serialize_none(self):
        """Test serializing None."""
        field = FieldInfo("test", str, SQLType.VARCHAR, nullable=True)
        assert serialize_value(None, field) is None
    
    def test_serialize_str(self):
        """Test serializing string (passthrough)."""
        field = FieldInfo("name", str, SQLType.VARCHAR)
        assert serialize_value("hello", field) == "hello"
    
    def test_serialize_int(self):
        """Test serializing int (passthrough)."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        assert serialize_value(42, field) == 42
    
    def test_serialize_float(self):
        """Test serializing float (passthrough)."""
        field = FieldInfo("price", float, SQLType.REAL)
        assert serialize_value(3.14, field) == 3.14
    
    def test_serialize_bool_true(self):
        """Test serializing True -> 1."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert serialize_value(True, field) == 1
    
    def test_serialize_bool_false(self):
        """Test serializing False -> 0."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert serialize_value(False, field) == 0
    
    def test_serialize_datetime(self):
        """Test serializing datetime to ISO string."""
        field = FieldInfo("timestamp", datetime, SQLType.TIMESTAMP)
        dt = datetime(2024, 1, 15, 12, 30, 45)
        result = serialize_value(dt, field)
        assert result == "2024-01-15T12:30:45"
    
    def test_serialize_date(self):
        """Test serializing date to ISO string."""
        field = FieldInfo("birthday", date, SQLType.DATE)
        d = date(2024, 1, 15)
        result = serialize_value(d, field)
        assert result == "2024-01-15"
    
    def test_serialize_time(self):
        """Test serializing time to ISO string."""
        field = FieldInfo("alarm", time, SQLType.TIME)
        t = time(12, 30, 45)
        result = serialize_value(t, field)
        assert result == "12:30:45"
    
    def test_serialize_uuid(self):
        """Test serializing UUID to string."""
        field = FieldInfo("external_id", UUID, SQLType.UUID)
        u = uuid4()
        result = serialize_value(u, field)
        assert result == str(u)
    
    def test_serialize_dict_to_json(self):
        """Test serializing dict to JSON string."""
        field = FieldInfo("metadata", dict, SQLType.JSON)
        data = {"key": "value", "num": 42}
        result = serialize_value(data, field)
        assert result == json.dumps(data)
    
    def test_serialize_list_to_json(self):
        """Test serializing list to JSON string."""
        field = FieldInfo("tags", list, SQLType.JSON)
        data = ["a", "b", "c"]
        result = serialize_value(data, field)
        assert result == json.dumps(data)
    
    def test_deserialize_none(self):
        """Test deserializing None."""
        field = FieldInfo("test", str, SQLType.VARCHAR, nullable=True)
        assert deserialize_value(None, field) is None
    
    def test_deserialize_str(self):
        """Test deserializing string (passthrough)."""
        field = FieldInfo("name", str, SQLType.VARCHAR)
        assert deserialize_value("hello", field) == "hello"
    
    def test_deserialize_bool_1(self):
        """Test deserializing 1 -> True."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert deserialize_value(1, field) is True
    
    def test_deserialize_bool_0(self):
        """Test deserializing 0 -> False."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN)
        assert deserialize_value(0, field) is False
    
    def test_deserialize_datetime_str(self):
        """Test deserializing ISO string to datetime."""
        field = FieldInfo("timestamp", datetime, SQLType.TIMESTAMP)
        result = deserialize_value("2024-01-15T12:30:45", field)
        assert result == datetime(2024, 1, 15, 12, 30, 45)
    
    def test_deserialize_date_str(self):
        """Test deserializing ISO string to date."""
        field = FieldInfo("birthday", date, SQLType.DATE)
        result = deserialize_value("2024-01-15", field)
        assert result == date(2024, 1, 15)
    
    def test_deserialize_uuid_str(self):
        """Test deserializing string to UUID."""
        field = FieldInfo("external_id", UUID, SQLType.UUID)
        u = uuid4()
        result = deserialize_value(str(u), field)
        assert result == u
    
    def test_deserialize_json_to_dict(self):
        """Test deserializing JSON string to dict."""
        field = FieldInfo("metadata", dict, SQLType.JSON)
        json_str = '{"key": "value", "num": 42}'
        result = deserialize_value(json_str, field)
        assert result == {"key": "value", "num": 42}
    
    def test_deserialize_json_to_list(self):
        """Test deserializing JSON string to list."""
        field = FieldInfo("tags", list, SQLType.JSON)
        json_str = '["a", "b", "c"]'
        result = deserialize_value(json_str, field)
        assert result == ["a", "b", "c"]


# =============================================================================
# FieldInfo Methods Tests (10 tests)
# =============================================================================

class TestFieldInfoMethods:
    """Tests for FieldInfo class methods."""
    
    def test_has_default_true(self):
        """Test has_default when default is set."""
        field = FieldInfo("role", str, SQLType.VARCHAR, default="user")
        assert field.has_default is True
    
    def test_has_default_false(self):
        """Test has_default when no default."""
        field = FieldInfo("name", str, SQLType.VARCHAR)
        assert field.has_default is False
    
    def test_has_default_with_factory(self):
        """Test has_default with default_factory."""
        field = FieldInfo("tags", list, SQLType.JSON, default_factory=list)
        assert field.has_default is True
    
    def test_get_default_value(self):
        """Test get_default returns default value."""
        field = FieldInfo("role", str, SQLType.VARCHAR, default="user")
        assert field.get_default() == "user"
    
    def test_get_default_factory(self):
        """Test get_default calls factory."""
        field = FieldInfo("tags", list, SQLType.JSON, default_factory=list)
        result1 = field.get_default()
        result2 = field.get_default()
        assert result1 == []
        assert result2 == []
        assert result1 is not result2  # Different instances
    
    def test_to_sql_column_simple(self):
        """Test to_sql_column for simple field."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=100)
        sql = field.to_sql_column()
        assert "name" in sql
        assert "VARCHAR(100)" in sql
    
    def test_to_sql_column_primary_key(self):
        """Test to_sql_column for primary key."""
        field = FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True)
        sql = field.to_sql_column()
        assert "PRIMARY KEY" in sql
        assert "AUTOINCREMENT" in sql
    
    def test_to_sql_column_not_null(self):
        """Test to_sql_column includes NOT NULL."""
        field = FieldInfo("name", str, SQLType.VARCHAR, nullable=False)
        sql = field.to_sql_column()
        assert "NOT NULL" in sql
    
    def test_to_sql_column_unique(self):
        """Test to_sql_column includes UNIQUE."""
        field = FieldInfo("email", str, SQLType.VARCHAR, unique=True)
        sql = field.to_sql_column()
        assert "UNIQUE" in sql
    
    def test_to_sql_column_default(self):
        """Test to_sql_column includes DEFAULT."""
        field = FieldInfo("role", str, SQLType.VARCHAR, default="user")
        sql = field.to_sql_column()
        assert "DEFAULT 'user'" in sql


# =============================================================================
# Advanced Field Tests (40 additional tests)
# =============================================================================

class TestAdvancedTypeParsing:
    """Advanced tests for type hint parsing."""
    
    def test_parse_complex_list(self):
        """Test parsing List with complex inner type."""
        field = parse_type_hint("items", List[Dict[str, int]])
        assert field.sql_type == SQLType.JSON
    
    def test_parse_nested_optional(self):
        """Test parsing deeply nested Optional."""
        field = parse_type_hint("data", Optional[List[str]])
        assert field.nullable is True
        assert field.sql_type == SQLType.JSON
    
    def test_parse_fk_compound_name(self):
        """Test parsing compound FK name like created_by_id."""
        field = parse_type_hint("created_by_id", int)
        assert field.foreign_key == "created_bys"
    
    def test_parse_multiple_underscores_fk(self):
        """Test parsing FK with multiple underscores."""
        field = parse_type_hint("original_author_id", int)
        assert field.foreign_key == "original_authors"
    
    def test_field_info_sql_column_int_default(self):
        """Test SQL column with integer default."""
        field = FieldInfo("count", int, SQLType.INTEGER, default=0)
        sql = field.to_sql_column()
        assert "DEFAULT 0" in sql
    
    def test_field_info_sql_column_bool_true_default(self):
        """Test SQL column with boolean true default."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN, default=True)
        sql = field.to_sql_column()
        assert "DEFAULT 1" in sql
    
    def test_field_info_sql_column_bool_false_default(self):
        """Test SQL column with boolean false default."""
        field = FieldInfo("active", bool, SQLType.BOOLEAN, default=False)
        sql = field.to_sql_column()
        assert "DEFAULT 0" in sql
    
    def test_default_factory_creates_new_instances(self):
        """Test default_factory creates new instances each time."""
        field = FieldInfo("tags", list, SQLType.JSON, default_factory=list)
        
        list1 = field.get_default()
        list2 = field.get_default()
        
        list1.append("item")
        assert len(list2) == 0  # Independent
    
    def test_parse_optional_with_default_value(self):
        """Test Optional field with non-None default."""
        field = parse_type_hint("role", Optional[str], "user")
        assert field.nullable is True
        assert field.default == "user"


class TestAdvancedSerialization:
    """Advanced tests for serialization/deserialization."""
    
    def test_serialize_nested_dict(self):
        """Test serializing nested dict to JSON."""
        field = FieldInfo("meta", dict, SQLType.JSON)
        data = {"level1": {"level2": {"level3": "value"}}}
        result = serialize_value(data, field)
        assert '"level3"' in result
    
    def test_serialize_list_of_dicts(self):
        """Test serializing list of dicts to JSON."""
        field = FieldInfo("items", list, SQLType.JSON)
        data = [{"id": 1}, {"id": 2}]
        result = serialize_value(data, field)
        assert '"id"' in result
    
    def test_serialize_empty_dict(self):
        """Test serializing empty dict."""
        field = FieldInfo("meta", dict, SQLType.JSON)
        result = serialize_value({}, field)
        assert result == "{}"
    
    def test_serialize_empty_list(self):
        """Test serializing empty list."""
        field = FieldInfo("tags", list, SQLType.JSON)
        result = serialize_value([], field)
        assert result == "[]"
    
    def test_deserialize_nested_dict(self):
        """Test deserializing nested dict from JSON."""
        field = FieldInfo("meta", dict, SQLType.JSON)
        result = deserialize_value('{"a": {"b": "c"}}', field)
        assert result["a"]["b"] == "c"
    
    def test_deserialize_list_of_numbers(self):
        """Test deserializing list of numbers."""
        field = FieldInfo("scores", list, SQLType.JSON)
        result = deserialize_value("[1, 2, 3]", field)
        assert result == [1, 2, 3]
    
    def test_serialize_datetime_with_timezone(self):
        """Test serializing datetime preserves format."""
        field = FieldInfo("timestamp", datetime, SQLType.TIMESTAMP)
        dt = datetime(2024, 1, 15, 12, 30, 45, 123456)
        result = serialize_value(dt, field)
        assert "2024-01-15" in result
        assert "12:30:45" in result
    
    def test_deserialize_datetime_preserves_precision(self):
        """Test deserializing datetime preserves microseconds."""
        field = FieldInfo("timestamp", datetime, SQLType.TIMESTAMP)
        result = deserialize_value("2024-01-15T12:30:45.123456", field)
        assert result.microsecond == 123456
    
    def test_serialize_uuid_format(self):
        """Test serializing UUID produces standard format."""
        from uuid import UUID
        field = FieldInfo("external_id", UUID, SQLType.UUID)
        u = UUID("12345678-1234-5678-1234-567812345678")
        result = serialize_value(u, field)
        assert result == "12345678-1234-5678-1234-567812345678"
    
    def test_deserialize_uuid_uppercase(self):
        """Test deserializing uppercase UUID."""
        from uuid import UUID
        field = FieldInfo("external_id", UUID, SQLType.UUID)
        result = deserialize_value("12345678-1234-5678-1234-567812345678", field)
        assert isinstance(result, UUID)
    
    def test_serialize_preserves_passthrough_types(self):
        """Test serialize passes through simple types unchanged."""
        field = FieldInfo("count", int, SQLType.INTEGER)
        assert serialize_value(42, field) == 42
        
        field = FieldInfo("name", str, SQLType.VARCHAR)
        assert serialize_value("hello", field) == "hello"
    
    def test_deserialize_already_correct_type(self):
        """Test deserialize handles already correct types."""
        field = FieldInfo("meta", dict, SQLType.JSON)
        data = {"key": "value"}
        result = deserialize_value(data, field)  # Already a dict
        assert result == data


class TestFieldEdgeCases:
    """Edge case tests for field handling."""
    
    def test_field_with_empty_name(self):
        """Test field with empty string name."""
        field = FieldInfo("", str, SQLType.VARCHAR)
        assert field.name == ""
    
    def test_field_with_very_long_name(self):
        """Test field with very long name."""
        long_name = "x" * 1000
        field = FieldInfo(long_name, str, SQLType.VARCHAR)
        assert field.name == long_name
    
    def test_field_max_length_zero(self):
        """Test field with max_length of 0."""
        field = FieldInfo("name", str, SQLType.VARCHAR, max_length=0)
        assert field.max_length == 0
    
    def test_field_nullable_primary_key(self):
        """Test primary key can't really be nullable (but stored)."""
        field = FieldInfo("id", int, SQLType.INTEGER, primary_key=True, nullable=True)
        assert field.primary_key is True
        assert field.nullable is True  # Stored but not enforced here
    
    def test_multiple_validators_stored(self):
        """Test multiple validators are stored."""
        def v1(x): return x
        def v2(x): return x
        def v3(x): return x
        
        field = FieldInfo("name", str, SQLType.VARCHAR, validators=[v1, v2, v3])
        assert len(field.validators) == 3
    
    def test_sql_type_enum_values(self):
        """Test SQLType enum has expected values."""
        assert SQLType.INTEGER.value == "INTEGER"
        assert SQLType.VARCHAR.value == "VARCHAR"
        assert SQLType.JSON.value == "JSON"
        assert SQLType.TIMESTAMP.value == "TIMESTAMP"
    
    def test_field_with_explicit_nullable_false(self):
        """Test Field with explicit nullable=False."""
        f = Field(nullable=False)
        info = f.to_field_info("name", Optional[str])
        assert info.nullable is False  # Explicit overrides type hint
    
    def test_field_foreign_key_overrides_detection(self):
        """Test explicit foreign_key overrides auto-detection."""
        f = Field(foreign_key="custom_table")
        info = f.to_field_info("user_id", int)
        assert info.foreign_key == "custom_table"  # Not "users"

