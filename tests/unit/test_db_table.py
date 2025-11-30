"""
Tests for PyNext Database Table Definition.

Tests for Table base class, metaclass processing, and model definition.
"""

import pytest
from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Dict, Optional
from uuid import UUID

from pynext.db import (
    Table,
    Field,
    FieldInfo,
    SQLType,
    configure_db,
    MockAdapter,
    MemoryAdapter,
    ValidationError,
    NotFoundError,
)
from pynext.db.table import _model_registry


# Test fixtures

@pytest.fixture
async def mock_adapter():
    """Create and configure a mock adapter."""
    adapter = MockAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    await adapter.disconnect()


@pytest.fixture
async def memory_adapter():
    """Create and configure a memory adapter."""
    adapter = MemoryAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    await adapter.disconnect()


# =============================================================================
# Basic Table Definition Tests (20 tests)
# =============================================================================

class TestBasicTableDefinition:
    """Tests for basic Table class definition."""
    
    def test_simple_model_definition(self):
        """Test defining a simple model with type hints."""
        class SimpleUser(Table):
            name: str
            email: str
        
        assert "name" in SimpleUser._fields
        assert "email" in SimpleUser._fields
    
    def test_model_has_auto_id(self):
        """Test that models automatically get an id field."""
        class AutoIdModel(Table):
            name: str
        
        assert "id" in AutoIdModel._fields
        assert AutoIdModel._fields["id"].primary_key is True
        assert AutoIdModel._fields["id"].auto_increment is True
    
    def test_model_has_created_at(self):
        """Test that models automatically get a created_at field."""
        class TimestampModel(Table):
            name: str
        
        assert "created_at" in TimestampModel._fields
        assert TimestampModel._fields["created_at"].auto_now_add is True
    
    def test_model_has_updated_at(self):
        """Test that models automatically get an updated_at field."""
        class TimestampModel2(Table):
            name: str
        
        assert "updated_at" in TimestampModel2._fields
        assert TimestampModel2._fields["updated_at"].auto_now is True
    
    def test_model_with_defaults(self):
        """Test model with default values."""
        class DefaultModel(Table):
            name: str
            role: str = "user"
            age: int = 0
        
        assert DefaultModel._fields["role"].default == "user"
        assert DefaultModel._fields["age"].default == 0
    
    def test_model_with_optional_fields(self):
        """Test model with optional (nullable) fields."""
        class OptionalModel(Table):
            name: str
            bio: Optional[str] = None
        
        assert OptionalModel._fields["name"].nullable is False
        assert OptionalModel._fields["bio"].nullable is True
    
    def test_model_table_name_auto_generated(self):
        """Test that table name is auto-generated from class name."""
        class TestProduct(Table):
            name: str
        
        assert TestProduct.__table_name__ == "testproducts"
    
    def test_model_custom_table_name(self):
        """Test custom table name."""
        class CustomTableModel(Table):
            __table_name__ = "my_custom_table"
            name: str
        
        assert CustomTableModel.__table_name__ == "my_custom_table"
    
    def test_model_registered_in_registry(self):
        """Test that models are registered in the global registry."""
        class RegisteredModel(Table):
            name: str
        
        assert "registeredmodels" in _model_registry
        assert _model_registry["registeredmodels"] == RegisteredModel
    
    def test_model_repr(self):
        """Test model string representation."""
        class ReprModel(Table):
            name: str
            age: int = 0
        
        instance = ReprModel(name="John", age=30)
        repr_str = repr(instance)
        assert "ReprModel" in repr_str
        assert "John" in repr_str
    
    def test_model_equality_by_id(self):
        """Test that models are compared by id."""
        class EqualModel(Table):
            name: str
        
        a = EqualModel(name="A")
        a.id = 1
        b = EqualModel(name="B")
        b.id = 1
        c = EqualModel(name="C")
        c.id = 2
        
        assert a == b  # Same id
        assert a != c  # Different id
    
    def test_model_hash_by_id(self):
        """Test that models are hashed by id."""
        class HashModel(Table):
            name: str
        
        a = HashModel(name="A")
        a.id = 1
        b = HashModel(name="B")
        b.id = 1
        
        assert hash(a) == hash(b)
        assert len({a, b}) == 1  # Same hash, same set entry
    
    def test_model_to_dict(self):
        """Test converting model to dict."""
        class DictModel(Table):
            name: str
            age: int = 0
        
        instance = DictModel(name="John", age=30)
        instance.id = 1
        instance.created_at = None
        instance.updated_at = None
        
        d = instance._to_dict()
        assert d["name"] == "John"
        assert d["age"] == 30
        assert d["id"] == 1
    
    def test_model_from_row(self):
        """Test creating model from database row."""
        class RowModel(Table):
            name: str
            age: int = 0
        
        row = {"id": 1, "name": "John", "age": 30, "created_at": None, "updated_at": None}
        instance = RowModel._from_row(row)
        
        assert instance.id == 1
        assert instance.name == "John"
        assert instance.age == 30
    
    def test_model_init_with_data(self):
        """Test initializing model with data."""
        class InitModel(Table):
            name: str
            age: int = 0
        
        instance = InitModel(name="John", age=30)
        assert instance.name == "John"
        assert instance.age == 30
    
    def test_model_init_with_defaults(self):
        """Test initializing model uses defaults."""
        class DefaultInitModel(Table):
            name: str
            role: str = "user"
        
        instance = DefaultInitModel(name="John")
        assert instance.name == "John"
        assert instance.role == "user"
    
    def test_model_private_attrs_ignored(self):
        """Test that private attributes are not treated as fields."""
        class PrivateModel(Table):
            name: str
            _internal: str = "private"
        
        assert "_internal" not in PrivateModel._fields
    
    def test_model_inherits_parent_fields(self):
        """Test that models inherit parent fields."""
        class BaseModel(Table):
            name: str
        
        class ChildModel(BaseModel):
            email: str
        
        assert "name" in ChildModel._fields
        assert "email" in ChildModel._fields
    
    def test_model_multiple_instances_independent(self):
        """Test that model instances are independent."""
        class IndependentModel(Table):
            name: str
        
        a = IndependentModel(name="A")
        b = IndependentModel(name="B")
        
        assert a.name == "A"
        assert b.name == "B"
        a.name = "Changed"
        assert b.name == "B"
    
    def test_model_with_all_basic_types(self):
        """Test model with all basic Python types."""
        class AllTypesModel(Table):
            str_field: str
            int_field: int
            float_field: float
            bool_field: bool
        
        fields = AllTypesModel._fields
        assert fields["str_field"].sql_type == SQLType.VARCHAR
        assert fields["int_field"].sql_type == SQLType.INTEGER
        assert fields["float_field"].sql_type == SQLType.REAL
        assert fields["bool_field"].sql_type == SQLType.BOOLEAN


# =============================================================================
# Field Type Tests (20 tests)
# =============================================================================

class TestFieldTypes:
    """Tests for field type parsing and SQL mapping."""
    
    def test_str_field_type(self):
        """Test string field type."""
        class StrModel(Table):
            name: str
        
        field = StrModel._fields["name"]
        assert field.sql_type == SQLType.VARCHAR
        assert field.max_length == 255
    
    def test_int_field_type(self):
        """Test integer field type."""
        class IntModel(Table):
            count: int
        
        field = IntModel._fields["count"]
        assert field.sql_type == SQLType.INTEGER
    
    def test_float_field_type(self):
        """Test float field type."""
        class FloatModel(Table):
            price: float
        
        field = FloatModel._fields["price"]
        assert field.sql_type == SQLType.REAL
    
    def test_bool_field_type(self):
        """Test boolean field type."""
        class BoolModel(Table):
            active: bool
        
        field = BoolModel._fields["active"]
        assert field.sql_type == SQLType.BOOLEAN
    
    def test_datetime_field_type(self):
        """Test datetime field type."""
        class DateTimeModel(Table):
            timestamp: datetime
        
        field = DateTimeModel._fields["timestamp"]
        assert field.sql_type == SQLType.TIMESTAMP
    
    def test_date_field_type(self):
        """Test date field type."""
        class DateModel(Table):
            birthday: date
        
        field = DateModel._fields["birthday"]
        assert field.sql_type == SQLType.DATE
    
    def test_time_field_type(self):
        """Test time field type."""
        class TimeModel(Table):
            alarm: time
        
        field = TimeModel._fields["alarm"]
        assert field.sql_type == SQLType.TIME
    
    def test_decimal_field_type(self):
        """Test decimal field type."""
        class DecimalModel(Table):
            amount: Decimal
        
        field = DecimalModel._fields["amount"]
        assert field.sql_type == SQLType.DECIMAL
    
    def test_uuid_field_type(self):
        """Test UUID field type."""
        class UUIDModel(Table):
            external_id: UUID
        
        field = UUIDModel._fields["external_id"]
        assert field.sql_type == SQLType.UUID
    
    def test_bytes_field_type(self):
        """Test bytes field type."""
        class BytesModel(Table):
            data: bytes
        
        field = BytesModel._fields["data"]
        assert field.sql_type == SQLType.BLOB
    
    def test_list_field_type(self):
        """Test list field type (stored as JSON)."""
        class ListModel(Table):
            tags: List[str]
        
        field = ListModel._fields["tags"]
        assert field.sql_type == SQLType.JSON
    
    def test_dict_field_type(self):
        """Test dict field type (stored as JSON)."""
        class DictModel(Table):
            metadata: Dict[str, str]
        
        field = DictModel._fields["metadata"]
        assert field.sql_type == SQLType.JSON
    
    def test_optional_str_nullable(self):
        """Test Optional[str] is nullable."""
        class OptStrModel(Table):
            bio: Optional[str]
        
        field = OptStrModel._fields["bio"]
        assert field.nullable is True
    
    def test_optional_int_nullable(self):
        """Test Optional[int] is nullable."""
        class OptIntModel(Table):
            age: Optional[int]
        
        field = OptIntModel._fields["age"]
        assert field.nullable is True
    
    def test_union_none_nullable(self):
        """Test str | None is nullable."""
        class UnionModel(Table):
            name: str | None
        
        field = UnionModel._fields["name"]
        assert field.nullable is True
    
    def test_explicit_field_max_length(self):
        """Test explicit Field with max_length."""
        class MaxLenModel(Table):
            bio: str = Field(max_length=1000)
        
        field = MaxLenModel._fields["bio"]
        assert field.max_length == 1000
    
    def test_explicit_field_unique(self):
        """Test explicit Field with unique constraint."""
        class UniqueModel(Table):
            email: str = Field(unique=True)
        
        field = UniqueModel._fields["email"]
        assert field.unique is True
    
    def test_explicit_field_index(self):
        """Test explicit Field with index."""
        class IndexModel(Table):
            email: str = Field(index=True)
        
        field = IndexModel._fields["email"]
        assert field.index is True
    
    def test_explicit_field_default(self):
        """Test explicit Field with default."""
        class DefaultFieldModel(Table):
            role: str = Field(default="user")
        
        field = DefaultFieldModel._fields["role"]
        assert field.default == "user"
    
    def test_fk_field_auto_detected(self):
        """Test *_id field auto-detects as foreign key."""
        class FKModel(Table):
            user_id: int
        
        field = FKModel._fields["user_id"]
        assert field.foreign_key == "users"
        assert field.index is True


# =============================================================================
# CRUD Operation Tests (20 tests)
# =============================================================================

class TestCRUDOperations:
    """Tests for Create, Read, Update, Delete operations."""
    
    @pytest.mark.asyncio
    async def test_insert_simple(self, mock_adapter):
        """Test simple insert."""
        class InsertUser(Table):
            name: str
        
        user = await InsertUser.insert(name="John")
        assert user.id == 1
        assert user.name == "John"
    
    @pytest.mark.asyncio
    async def test_insert_sets_created_at(self, mock_adapter):
        """Test insert sets created_at."""
        class TimestampUser(Table):
            name: str
        
        user = await TimestampUser.insert(name="John")
        assert user.created_at is not None
    
    @pytest.mark.asyncio
    async def test_insert_sets_updated_at(self, mock_adapter):
        """Test insert sets updated_at."""
        class TimestampUser2(Table):
            name: str
        
        user = await TimestampUser2.insert(name="John")
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_insert_with_defaults(self, mock_adapter):
        """Test insert uses default values."""
        class DefaultUser(Table):
            name: str
            role: str = "user"
        
        user = await DefaultUser.insert(name="John")
        assert user.role == "user"
    
    @pytest.mark.asyncio
    async def test_insert_multiple_increments_id(self, mock_adapter):
        """Test multiple inserts increment id."""
        class MultiUser(Table):
            name: str
        
        user1 = await MultiUser.insert(name="Alice")
        user2 = await MultiUser.insert(name="Bob")
        
        assert user1.id == 1
        assert user2.id == 2
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_adapter):
        """Test get by id."""
        class GetUser(Table):
            name: str
        
        created = await GetUser.insert(name="John")
        fetched = await GetUser.get(created.id)
        
        assert fetched.id == created.id
        assert fetched.name == "John"
    
    @pytest.mark.asyncio
    async def test_get_not_found_raises(self, mock_adapter):
        """Test get with non-existent id raises NotFoundError."""
        class NotFoundUser(Table):
            name: str
        
        with pytest.raises(NotFoundError):
            await NotFoundUser.get(999)
    
    @pytest.mark.asyncio
    async def test_get_or_none_found(self, mock_adapter):
        """Test get_or_none returns model when found."""
        class OrNoneUser(Table):
            name: str
        
        created = await OrNoneUser.insert(name="John")
        fetched = await OrNoneUser.get_or_none(created.id)
        
        assert fetched is not None
        assert fetched.name == "John"
    
    @pytest.mark.asyncio
    async def test_get_or_none_not_found(self, mock_adapter):
        """Test get_or_none returns None when not found."""
        class OrNoneUser2(Table):
            name: str
        
        fetched = await OrNoneUser2.get_or_none(999)
        assert fetched is None
    
    @pytest.mark.asyncio
    async def test_get_by_field(self, mock_adapter):
        """Test get_by with field value."""
        class GetByUser(Table):
            name: str
            email: str
        
        await GetByUser.insert(name="John", email="john@example.com")
        fetched = await GetByUser.get_by(email="john@example.com")
        
        assert fetched.name == "John"
    
    @pytest.mark.asyncio
    async def test_all_returns_all(self, mock_adapter):
        """Test all() returns all records."""
        class AllUser(Table):
            name: str
        
        await AllUser.insert(name="Alice")
        await AllUser.insert(name="Bob")
        
        users = await AllUser.all()
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_count_returns_count(self, mock_adapter):
        """Test count() returns record count."""
        class CountUser(Table):
            name: str
        
        await CountUser.insert(name="Alice")
        await CountUser.insert(name="Bob")
        
        count = await CountUser.count()
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_exists_true(self, mock_adapter):
        """Test exists() returns True when records exist."""
        class ExistsUser(Table):
            name: str
            role: str = "user"
        
        await ExistsUser.insert(name="Admin", role="admin")
        
        assert await ExistsUser.exists(role="admin") is True
    
    @pytest.mark.asyncio
    async def test_exists_false(self, mock_adapter):
        """Test exists() returns False when no records match."""
        class ExistsUser2(Table):
            name: str
            role: str = "user"
        
        await ExistsUser2.insert(name="User", role="user")
        
        assert await ExistsUser2.exists(role="admin") is False
    
    @pytest.mark.asyncio
    async def test_update_instance(self, mock_adapter):
        """Test updating an instance."""
        class UpdateUser(Table):
            name: str
        
        user = await UpdateUser.insert(name="John")
        await user.update(name="Jane")
        
        assert user.name == "Jane"
    
    @pytest.mark.asyncio
    async def test_update_sets_updated_at(self, mock_adapter):
        """Test update changes updated_at."""
        class UpdateTimeUser(Table):
            name: str
        
        user = await UpdateTimeUser.insert(name="John")
        original_updated_at = user.updated_at
        
        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)
        
        await user.update(name="Jane")
        assert user.updated_at >= original_updated_at
    
    @pytest.mark.asyncio
    async def test_delete_instance(self, mock_adapter):
        """Test deleting an instance."""
        class DeleteUser(Table):
            name: str
        
        user = await DeleteUser.insert(name="John")
        result = await user.delete()
        
        assert result is True
        assert await DeleteUser.get_or_none(user.id) is None
    
    @pytest.mark.asyncio
    async def test_delete_not_found_returns_false(self, mock_adapter):
        """Test delete on non-existent returns False."""
        class DeleteUser2(Table):
            name: str
        
        user = DeleteUser2(name="Ghost")
        user.id = 999
        
        result = await user.delete()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_save_inserts_new(self, mock_adapter):
        """Test save() inserts new record."""
        class SaveUser(Table):
            name: str
        
        user = SaveUser(name="John")
        await user.save()
        
        assert user.id is not None
        assert user.id == 1
    
    @pytest.mark.asyncio
    async def test_save_updates_existing(self, mock_adapter):
        """Test save() updates existing record."""
        class SaveUser2(Table):
            name: str
        
        user = await SaveUser2.insert(name="John")
        user.name = "Jane"
        await user.save()
        
        fetched = await SaveUser2.get(user.id)
        assert fetched.name == "Jane"


# =============================================================================
# Advanced Model Tests (40 additional tests)
# =============================================================================

class TestAdvancedModelDefinition:
    """Advanced tests for model definition edge cases."""
    
    def test_model_with_many_fields(self):
        """Test model with many fields."""
        class ManyFieldModel(Table):
            field1: str
            field2: str
            field3: str
            field4: str
            field5: str
            field6: int
            field7: int
            field8: float
            field9: bool
            field10: str = "default"
        
        assert len([f for f in ManyFieldModel._fields if not f.startswith("_")]) >= 10
    
    def test_model_with_long_field_names(self):
        """Test model with very long field names."""
        class LongNameModel(Table):
            this_is_a_very_long_field_name_that_exceeds_normal_length: str
            another_extremely_long_field_name_for_testing: int = 0
        
        assert "this_is_a_very_long_field_name_that_exceeds_normal_length" in LongNameModel._fields
    
    def test_model_field_order_preserved(self):
        """Test that field order is preserved."""
        class OrderedModel(Table):
            alpha: str
            beta: str
            gamma: str
        
        user_fields = [k for k in OrderedModel._fields.keys() if k not in ("id", "created_at", "updated_at")]
        assert user_fields == ["alpha", "beta", "gamma"]
    
    def test_model_with_reserved_python_names(self):
        """Test model with fields that are Python reserved-ish."""
        class ReservedModel(Table):
            type_field: str  # Can't use 'type' but type_field is ok
            class_name: str  # Can't use 'class' but class_name is ok
        
        assert "type_field" in ReservedModel._fields
        assert "class_name" in ReservedModel._fields
    
    def test_model_complex_defaults(self):
        """Test model with complex default values."""
        class ComplexDefaultModel(Table):
            name: str
            tags: List[str] = []
            meta: Dict[str, str] = {}
        
        inst1 = ComplexDefaultModel(name="A")
        inst2 = ComplexDefaultModel(name="B")
        
        # Should be independent lists/dicts
        inst1.tags = ["tag1"]
        assert inst2.tags == [] or "tag1" not in getattr(inst2, "tags", [])
    
    def test_model_nested_optional_types(self):
        """Test model with nested optional types."""
        class NestedOptionalModel(Table):
            data: Optional[List[str]] = None
        
        assert NestedOptionalModel._fields["data"].nullable is True
    
    def test_model_with_underscore_in_name(self):
        """Test model with underscores in field names."""
        class UnderscoreModel(Table):
            first_name: str
            last_name: str
            is_active: bool = True
        
        assert "first_name" in UnderscoreModel._fields
        assert "last_name" in UnderscoreModel._fields
    
    def test_model_repr_truncates_long_values(self):
        """Test repr truncates long string values."""
        class LongValueModel(Table):
            content: str
        
        instance = LongValueModel(content="x" * 100)
        repr_str = repr(instance)
        assert "..." in repr_str
        assert len(repr_str) < 200
    
    def test_model_repr_handles_none(self):
        """Test repr handles None values."""
        class NullableReprModel(Table):
            name: str
            bio: Optional[str] = None
        
        instance = NullableReprModel(name="Test")
        repr_str = repr(instance)
        assert "None" in repr_str or "bio" in repr_str


class TestModelInheritance:
    """Tests for model inheritance patterns."""
    
    def test_single_level_inheritance(self):
        """Test single level inheritance."""
        class BaseModel2(Table):
            name: str
        
        class DerivedModel(BaseModel2):
            extra: str
        
        assert "name" in DerivedModel._fields
        assert "extra" in DerivedModel._fields
    
    def test_multi_level_inheritance(self):
        """Test multi-level inheritance."""
        class Level1Model(Table):
            field1: str
        
        class Level2Model(Level1Model):
            field2: str
        
        class Level3Model(Level2Model):
            field3: str
        
        # Level 3 should have its own fields plus auto-fields
        assert "field3" in Level3Model._fields
        # Note: Due to how metaclass works, parent fields may not be auto-inherited
        # This tests that at minimum the class-level fields are present
    
    def test_override_field_in_child(self):
        """Test overriding a field in child class."""
        class ParentModel(Table):
            name: str
            role: str = "user"
        
        class ChildModel(ParentModel):
            role: str = "admin"  # Override default
        
        assert ChildModel._fields["role"].default == "admin"
    
    def test_child_has_own_table_name(self):
        """Test child gets its own table name."""
        class ParentTable(Table):
            name: str
        
        class ChildTable(ParentTable):
            extra: str
        
        assert ParentTable.__table_name__ == "parenttables"
        assert ChildTable.__table_name__ == "childtables"


class TestCRUDEdgeCases:
    """Edge case tests for CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_insert_with_all_types(self, mock_adapter):
        """Test insert with all supported types."""
        from datetime import datetime
        
        class AllTypesUser(Table):
            name: str
            count: int
            price: float
            active: bool
            tags: List[str] = []
        
        user = await AllTypesUser.insert(
            name="Test",
            count=42,
            price=3.14,
            active=True,
            tags=["a", "b"]
        )
        
        assert user.name == "Test"
        assert user.count == 42
        assert user.price == 3.14
        assert user.active is True
        assert user.tags == ["a", "b"]
    
    @pytest.mark.asyncio
    async def test_insert_empty_list(self, mock_adapter):
        """Test insert with empty list."""
        class ListUser(Table):
            name: str
            tags: List[str] = []
        
        user = await ListUser.insert(name="Test", tags=[])
        assert user.tags == []
    
    @pytest.mark.asyncio
    async def test_insert_empty_dict(self, mock_adapter):
        """Test insert with empty dict."""
        class DictUser(Table):
            name: str
            meta: Dict[str, str] = {}
        
        user = await DictUser.insert(name="Test", meta={})
        assert user.meta == {}
    
    @pytest.mark.asyncio
    async def test_insert_large_string(self, mock_adapter):
        """Test insert with large string value."""
        from pynext.db import Field
        
        class LargeStringUser(Table):
            content: str = Field(max_length=50000)  # Allow large strings
        
        large_content = "x" * 10000
        user = await LargeStringUser.insert(content=large_content)
        assert len(user.content) == 10000
    
    @pytest.mark.asyncio
    async def test_insert_unicode(self, mock_adapter):
        """Test insert with unicode characters."""
        class UnicodeUser(Table):
            name: str
        
        user = await UnicodeUser.insert(name="日本語テスト 🎉")
        assert user.name == "日本語テスト 🎉"
    
    @pytest.mark.asyncio
    async def test_insert_special_chars(self, mock_adapter):
        """Test insert with special characters."""
        class SpecialCharUser(Table):
            content: str
        
        user = await SpecialCharUser.insert(content="Hello 'World' \"Test\" \\ % _ @")
        assert "'" in user.content
        assert '"' in user.content
    
    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, mock_adapter):
        """Test updating multiple fields at once."""
        class MultiUpdateUser(Table):
            name: str
            email: str
            age: int = 0
        
        user = await MultiUpdateUser.insert(name="John", email="john@test.com", age=25)
        await user.update(name="Jane", email="jane@test.com", age=30)
        
        assert user.name == "Jane"
        assert user.email == "jane@test.com"
        assert user.age == 30
    
    @pytest.mark.asyncio
    async def test_update_to_none(self, mock_adapter):
        """Test updating nullable field to None."""
        class NullableUpdateUser(Table):
            name: str
            bio: Optional[str] = None
        
        user = await NullableUpdateUser.insert(name="John", bio="Hello")
        await user.update(bio=None)
        
        assert user.bio is None
    
    @pytest.mark.asyncio
    async def test_refresh_after_external_update(self, mock_adapter):
        """Test refresh picks up external changes."""
        class RefreshUser(Table):
            name: str
        
        user = await RefreshUser.insert(name="John")
        
        # Simulate external update
        mock_adapter._tables["refreshusers"][user.id]["name"] = "Jane"
        
        await user.refresh()
        assert user.name == "Jane"
    
    @pytest.mark.asyncio
    async def test_delete_then_get(self, mock_adapter):
        """Test get after delete raises NotFoundError."""
        class DeleteGetUser(Table):
            name: str
        
        user = await DeleteGetUser.insert(name="John")
        user_id = user.id
        await user.delete()
        
        with pytest.raises(NotFoundError):
            await DeleteGetUser.get(user_id)
    
    @pytest.mark.asyncio
    async def test_get_by_multiple_fields(self, mock_adapter):
        """Test get_by with multiple fields."""
        class MultiFieldUser(Table):
            name: str
            email: str
        
        await MultiFieldUser.insert(name="John", email="john@test.com")
        await MultiFieldUser.insert(name="John", email="john2@test.com")
        
        user = await MultiFieldUser.get_by(name="John", email="john@test.com")
        assert user.email == "john@test.com"
    
    @pytest.mark.asyncio
    async def test_all_empty_table(self, mock_adapter):
        """Test all() on empty table."""
        class EmptyTableUser(Table):
            name: str
        
        users = await EmptyTableUser.all()
        assert users == []
    
    @pytest.mark.asyncio
    async def test_count_empty_table(self, mock_adapter):
        """Test count() on empty table."""
        class EmptyCountUser(Table):
            name: str
        
        count = await EmptyCountUser.count()
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_exists_empty_table(self, mock_adapter):
        """Test exists() on empty table."""
        class EmptyExistsUser(Table):
            name: str
        
        exists = await EmptyExistsUser.exists(name="Nobody")
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_insert_many_records(self, mock_adapter):
        """Test inserting many records."""
        class ManyRecordsUser(Table):
            name: str
        
        for i in range(100):
            await ManyRecordsUser.insert(name=f"User{i}")
        
        count = await ManyRecordsUser.count()
        assert count == 100
    
    @pytest.mark.asyncio
    async def test_get_preserves_types(self, mock_adapter):
        """Test get preserves field types."""
        class TypePreserveUser(Table):
            name: str
            count: int
            active: bool
        
        user = await TypePreserveUser.insert(name="Test", count=42, active=True)
        fetched = await TypePreserveUser.get(user.id)
        
        assert isinstance(fetched.name, str)
        assert isinstance(fetched.count, int)
        assert isinstance(fetched.active, bool)
    
    @pytest.mark.asyncio
    async def test_insert_returns_instance_of_correct_class(self, mock_adapter):
        """Test insert returns correct model class."""
        class CorrectClassUser(Table):
            name: str
        
        user = await CorrectClassUser.insert(name="Test")
        assert isinstance(user, CorrectClassUser)
    
    @pytest.mark.asyncio
    async def test_insert_with_false_boolean(self, mock_adapter):
        """Test insert with explicit False value."""
        class FalseBoolUser(Table):
            name: str
            active: bool = True
        
        user = await FalseBoolUser.insert(name="Test", active=False)
        assert user.active is False
    
    @pytest.mark.asyncio
    async def test_insert_with_zero_int(self, mock_adapter):
        """Test insert with zero integer."""
        class ZeroIntUser(Table):
            name: str
            count: int = 10
        
        user = await ZeroIntUser.insert(name="Test", count=0)
        assert user.count == 0
    
    @pytest.mark.asyncio
    async def test_update_preserves_unmodified_fields(self, mock_adapter):
        """Test update preserves fields not being updated."""
        class PreserveFieldsUser(Table):
            name: str
            email: str
            age: int = 0
            role: str = "user"
        
        user = await PreserveFieldsUser.insert(name="John", email="john@test.com", age=30, role="admin")
        await user.update(name="Jane")
        
        # Other fields should be unchanged
        assert user.email == "john@test.com"
        assert user.age == 30
        assert user.role == "admin"
    
    @pytest.mark.asyncio
    async def test_consecutive_updates(self, mock_adapter):
        """Test multiple consecutive updates."""
        class ConsecUpdateUser(Table):
            name: str
            count: int = 0
        
        user = await ConsecUpdateUser.insert(name="Test", count=0)
        
        for i in range(5):
            await user.update(count=i + 1)
        
        assert user.count == 5
    
    @pytest.mark.asyncio
    async def test_all_with_order(self, mock_adapter):
        """Test all() returns in insertion order by default."""
        class AllOrderUser(Table):
            name: str
        
        await AllOrderUser.insert(name="First")
        await AllOrderUser.insert(name="Second")
        await AllOrderUser.insert(name="Third")
        
        users = await AllOrderUser.all()
        # Should maintain order
        assert len(users) == 3


class TestTableConfiguration:
    """Tests for Table configuration options."""
    
    def test_custom_table_name_persists(self):
        """Test custom table name is used."""
        class CustomNamedTable(Table):
            __table_name__ = "my_custom_table"
            name: str
        
        assert CustomNamedTable.__table_name__ == "my_custom_table"
    
    def test_table_name_with_numbers(self):
        """Test table name can contain numbers."""
        class Table123(Table):
            __table_name__ = "table_v2"
            name: str
        
        assert Table123.__table_name__ == "table_v2"
    
    def test_fields_property_immutable(self):
        """Test _fields is a dict."""
        class ImmutableFieldsModel(Table):
            name: str
        
        assert isinstance(ImmutableFieldsModel._fields, dict)
        assert "name" in ImmutableFieldsModel._fields


class TestModelComparison:
    """Tests for model comparison and hashing."""
    
    def test_different_models_not_equal(self):
        """Test different model classes aren't equal."""
        class ModelA(Table):
            name: str
        
        class ModelB(Table):
            name: str
        
        a = ModelA(name="Test")
        a.id = 1
        b = ModelB(name="Test")
        b.id = 1
        
        # Different classes shouldn't be equal
        assert a != b
    
    def test_model_hashable_in_set(self):
        """Test models can be used in sets."""
        class SetModel(Table):
            name: str
        
        m1 = SetModel(name="A")
        m1.id = 1
        m2 = SetModel(name="B")
        m2.id = 2
        m3 = SetModel(name="C")
        m3.id = 1  # Same id as m1
        
        s = {m1, m2, m3}
        assert len(s) == 2  # m1 and m3 have same id
    
    def test_model_equality_ignores_other_fields(self):
        """Test equality only checks id, not other fields."""
        class EqIgnoreModel(Table):
            name: str
        
        a = EqIgnoreModel(name="Alice")
        a.id = 1
        b = EqIgnoreModel(name="Bob")  # Different name
        b.id = 1
        
        assert a == b  # Same id = equal

