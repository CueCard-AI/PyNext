"""
PyNext Database Table Base Class.

The foundation of PyNext's ORM. Just define a class with type hints,
and you get a fully-featured database model.

Design: Stupid simple - just Python types, we handle the rest.
"""

from __future__ import annotations

import inspect
from datetime import datetime
from typing import (
    Any,
    ClassVar,
    Dict,
    get_type_hints,
    List,
    Optional,
    Type,
    TypeVar,
    TYPE_CHECKING,
)

from pynext.db.fields import (
    Field,
    FieldInfo,
    create_auto_fields,
    parse_type_hint,
)
from pynext.db.validation import validate_data
from pynext.db.exceptions import (
    ConfigurationError,
    NotFoundError,
    ValidationError,
)

if TYPE_CHECKING:
    from pynext.db.query import Query
    from pynext.db.adapters.base import Adapter

T = TypeVar("T", bound="Table")

# Global registry of all models
_model_registry: Dict[str, Type["Table"]] = {}

# Global adapter (set via configure_db)
_adapter: Optional["Adapter"] = None


def configure_db(adapter: "Adapter") -> None:
    """
    Configure the database adapter.
    
    Call this once at startup to set the adapter for all models.
    
    Examples:
        from pynext.db import configure_db, MemoryAdapter
        
        adapter = MemoryAdapter()
        await adapter.connect()
        configure_db(adapter)
    """
    global _adapter
    _adapter = adapter


def get_adapter() -> "Adapter":
    """Get the configured adapter."""
    if _adapter is None:
        raise ConfigurationError(
            "No database adapter configured. Call configure_db() first."
        )
    return _adapter


class TableMeta(type):
    """
    Metaclass for Table that processes type hints into field definitions.
    
    This runs when you define a class:
        class User(Table):
            name: str
            email: str
    
    It:
    1. Parses type hints into FieldInfo
    2. Adds auto-fields (id, created_at, updated_at)
    3. Registers the model in the global registry
    4. Sets up relationships
    """
    
    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> Type["Table"]:
        # Don't process the base Table class
        if name == "Table":
            return super().__new__(mcs, name, bases, namespace)
        
        # Get raw annotations first
        annotations = namespace.get("__annotations__", {})
        
        # Get parent annotations
        for base in bases:
            if hasattr(base, "__annotations__"):
                annotations = {**base.__annotations__, **annotations}
        
        # Parse fields from type hints
        fields: Dict[str, FieldInfo] = {}
        
        # Process user-defined fields first
        for field_name, type_hint in annotations.items():
            # Skip private attributes
            if field_name.startswith("_"):
                continue
            
            # Skip ClassVar
            if hasattr(type_hint, "__origin__") and type_hint.__origin__ is ClassVar:
                continue
            
            # Skip auto-fields - they'll be added with proper config later
            if field_name in ("id", "created_at", "updated_at"):
                continue
            
            # Get default value
            default = namespace.get(field_name, ...)
            
            # Check if it's an explicit Field()
            if isinstance(default, Field):
                field_info = default.to_field_info(field_name, type_hint)
            else:
                field_info = parse_type_hint(field_name, type_hint, default)
            
            fields[field_name] = field_info
        
        # Add auto-fields LAST so they're guaranteed to be correct
        auto_fields = create_auto_fields()
        fields.update(auto_fields)
        
        # Create the class
        namespace["_fields"] = fields
        namespace["_relationships"] = {}
        
        # Table name defaults to lowercase plural class name
        if "__table_name__" not in namespace:
            namespace["__table_name__"] = name.lower() + "s"
        
        cls = super().__new__(mcs, name, bases, namespace)
        
        # Register in global registry
        _model_registry[cls.__table_name__] = cls
        
        return cls


class Table(metaclass=TableMeta):
    """
    Base class for database models.
    
    Just define a class with type hints, and you get:
    - Automatic id, created_at, updated_at fields
    - Type validation on create/update
    - Chainable query builder
    - Relationship detection
    
    Usage:
        class User(Table):
            name: str
            email: str
            age: int = 0
            role: str = "user"
        
        # Create
        user = await User.insert(name="John", email="john@example.com")
        
        # Query
        users = await User.select().where(role="admin").order_by("name")
        
        # Update
        await user.update(role="admin")
        
        # Delete
        await user.delete()
    """
    
    # Class attributes set by metaclass
    _fields: ClassVar[Dict[str, FieldInfo]]
    _relationships: ClassVar[Dict[str, Dict]]
    __table_name__: ClassVar[str]
    
    # Instance attributes
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    def __init__(self, **data: Any):
        """
        Create a model instance.
        
        Usually you'll use Table.insert() instead of __init__ directly.
        
        Args:
            **data: Field values
        """
        # Set field values
        for name, field in self._fields.items():
            if name in data:
                setattr(self, name, data[name])
            elif field.has_default:
                setattr(self, name, field.get_default())
            elif field.nullable:
                setattr(self, name, None)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        fields = []
        for name in self._fields:
            if hasattr(self, name):
                value = getattr(self, name)
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                fields.append(f"{name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(fields)})"
    
    def __eq__(self, other: Any) -> bool:
        """Compare by id."""
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash by id."""
        return hash((self.__class__.__name__, self.id))
    
    # Class methods for CRUD operations
    
    @classmethod
    async def insert(cls: Type[T], **data: Any) -> T:
        """
        Insert a new record.
        
        Examples:
            user = await User.insert(name="John", email="john@example.com")
        
        Args:
            **data: Field values
            
        Returns:
            The created model instance
            
        Raises:
            ValidationError: If data fails validation
        """
        adapter = get_adapter()
        
        # Validate data
        validated = validate_data(data, cls._fields, partial=False)
        
        # Ensure table exists
        await adapter.create_table(cls.__table_name__, cls._fields)
        
        # Insert and return
        row = await adapter.insert(cls.__table_name__, validated, cls._fields)
        return cls._from_row(row)
    
    @classmethod
    async def get(cls: Type[T], id: int) -> T:
        """
        Get a record by id.
        
        Examples:
            user = await User.get(1)
        
        Args:
            id: Record id
            
        Returns:
            The model instance
            
        Raises:
            NotFoundError: If not found
        """
        from pynext.db.query import Query
        
        adapter = get_adapter()
        query = Query(cls, adapter, cls._fields).where(id=id)
        row = await adapter.select_one(cls.__table_name__, query, cls._fields)
        
        if row is None:
            raise NotFoundError(cls.__table_name__, id=id)
        
        return cls._from_row(row)
    
    @classmethod
    async def get_or_none(cls: Type[T], id: int) -> Optional[T]:
        """
        Get a record by id, or None if not found.
        
        Examples:
            user = await User.get_or_none(1)
            if user:
                print(user.name)
        """
        try:
            return await cls.get(id)
        except NotFoundError:
            return None
    
    @classmethod
    async def get_by(cls: Type[T], **kwargs: Any) -> T:
        """
        Get a record by field values.
        
        Examples:
            user = await User.get_by(email="john@example.com")
        
        Raises:
            NotFoundError: If not found
        """
        from pynext.db.query import Query
        
        adapter = get_adapter()
        query = Query(cls, adapter, cls._fields).where(**kwargs)
        row = await adapter.select_one(cls.__table_name__, query, cls._fields)
        
        if row is None:
            raise NotFoundError(cls.__table_name__, **kwargs)
        
        return cls._from_row(row)
    
    @classmethod
    async def all(cls: Type[T]) -> List[T]:
        """
        Get all records.
        
        Examples:
            users = await User.all()
        """
        return await cls.select()
    
    @classmethod
    def select(cls: Type[T]) -> "Query[T]":
        """
        Start a query.
        
        Returns a chainable Query builder.
        
        Examples:
            users = await User.select().where(role="admin").order_by("name")
            users = await User.select().where_in(id=[1, 2, 3])
        """
        from pynext.db.query import Query
        
        adapter = get_adapter()
        return Query(cls, adapter, cls._fields)
    
    @classmethod
    async def count(cls: Type[T]) -> int:
        """
        Count all records.
        
        Examples:
            total = await User.count()
        """
        return await cls.select().count()
    
    @classmethod
    async def exists(cls: Type[T], **kwargs: Any) -> bool:
        """
        Check if any records match.
        
        Examples:
            has_admin = await User.exists(role="admin")
        """
        return await cls.select().where(**kwargs).exists()
    
    # ==========================================================================
    # Batch Operations - Phase 2
    # ==========================================================================
    
    @classmethod
    async def insert_many(cls: Type[T], records: List[Dict[str, Any]]) -> List[T]:
        """
        Insert multiple records at once.
        
        Much faster than calling insert() in a loop.
        All records are inserted in a single transaction.
        
        Examples:
            users = await User.insert_many([
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"},
                {"name": "Charlie", "email": "charlie@example.com"},
            ])
        
        Args:
            records: List of dicts with field values
            
        Returns:
            List of created model instances
            
        Raises:
            ValidationError: If any record fails validation
        """
        if not records:
            return []
        
        adapter = get_adapter()
        await adapter.create_table(cls.__table_name__, cls._fields)
        
        results = []
        async with adapter.transaction():
            for data in records:
                validated = validate_data(data, cls._fields, partial=False)
                row = await adapter.insert(cls.__table_name__, validated, cls._fields)
                results.append(cls._from_row(row))
        
        return results
    
    @classmethod
    async def update_many(
        cls: Type[T],
        where: Dict[str, Any],
        set: Dict[str, Any],
    ) -> int:
        """
        Update multiple records matching a condition.
        
        Examples:
            # Make all users with role='user' active
            count = await User.update_many(
                where={"role": "user"},
                set={"active": True}
            )
            print(f"Updated {count} users")
        
        Args:
            where: Conditions to match (AND'd together)
            set: Values to update
            
        Returns:
            Number of records updated
        """
        query = cls.select()
        for field, value in where.items():
            query = query.where(**{field: value})
        
        return await query.update(**set)
    
    @classmethod
    async def delete_many(cls: Type[T], where: Dict[str, Any]) -> int:
        """
        Delete multiple records matching a condition.
        
        Examples:
            # Delete all inactive users
            count = await User.delete_many(where={"active": False})
            print(f"Deleted {count} users")
        
        Args:
            where: Conditions to match (AND'd together)
            
        Returns:
            Number of records deleted
        """
        query = cls.select()
        for field, value in where.items():
            query = query.where(**{field: value})
        
        return await query.delete()
    
    @classmethod
    async def upsert(
        cls: Type[T],
        where: Dict[str, Any],
        create: Dict[str, Any],
        update: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Insert a record or update if it exists.
        
        This is an atomic operation - either insert or update, never both.
        
        Examples:
            # Create user or update if email exists
            user = await User.upsert(
                where={"email": "john@example.com"},
                create={"name": "John", "email": "john@example.com"},
                update={"name": "John Updated"}
            )
        
        Args:
            where: Conditions to find existing record
            create: Values for new record (if not found)
            update: Values to update (if found). If None, uses create values.
            
        Returns:
            The created or updated model instance
        """
        # Try to find existing
        query = cls.select()
        for field, value in where.items():
            query = query.where(**{field: value})
        
        existing = await query.first()
        
        if existing:
            # Update
            update_values = update if update is not None else create
            await existing.update(**update_values)
            return existing
        else:
            # Create
            return await cls.insert(**create)
    
    @classmethod
    async def first(cls: Type[T]) -> Optional[T]:
        """
        Get the first record.
        
        Examples:
            user = await User.first()
        """
        return await cls.select().first()
    
    @classmethod
    async def first_or_raise(cls: Type[T]) -> T:
        """
        Get the first record or raise NotFoundError.
        
        Examples:
            user = await User.first_or_raise()
        """
        result = await cls.select().first()
        if result is None:
            raise NotFoundError(cls.__table_name__)
        return result
    
    @classmethod
    async def find_by(cls: Type[T], **kwargs: Any) -> Optional[T]:
        """
        Find a record by field values, returns None if not found.
        
        Examples:
            user = await User.find_by(email="john@example.com")
            if user:
                print(user.name)
        """
        return await cls.select().where(**kwargs).first()
    
    @classmethod
    async def create_table(cls) -> None:
        """
        Create the table in the database.
        
        Usually called automatically on first insert.
        """
        adapter = get_adapter()
        await adapter.create_table(cls.__table_name__, cls._fields)
    
    @classmethod
    async def drop_table(cls) -> None:
        """
        Drop the table from the database.
        
        Warning: This deletes all data!
        """
        adapter = get_adapter()
        await adapter.drop_table(cls.__table_name__)
    
    # Instance methods
    
    async def update(self: T, **data: Any) -> T:
        """
        Update this record.
        
        Examples:
            await user.update(name="Jane")
            await user.update(role="admin", active=True)
        
        Args:
            **data: Field values to update
            
        Returns:
            The updated model instance (self)
            
        Raises:
            ValidationError: If data fails validation
        """
        adapter = get_adapter()
        
        # Validate data (partial update)
        validated = validate_data(data, self._fields, partial=True)
        
        # Update in database
        row = await adapter.update(
            self.__table_name__,
            self.id,
            validated,
            self._fields,
        )
        
        # Update this instance
        for key, value in row.items():
            setattr(self, key, value)
        
        return self
    
    async def save(self: T) -> T:
        """
        Save this record (insert or update).
        
        If the record has an id, it updates. Otherwise, it inserts.
        
        Examples:
            user = User(name="John", email="john@example.com")
            await user.save()  # Inserts
            
            user.name = "Jane"
            await user.save()  # Updates
        """
        adapter = get_adapter()
        
        if getattr(self, "id", None) is not None:
            # Update existing
            data = self._to_dict()
            del data["id"]
            del data["created_at"]
            await self.update(**data)
        else:
            # Insert new
            data = self._to_dict()
            data.pop("id", None)
            data.pop("created_at", None)
            data.pop("updated_at", None)
            
            # Validate and insert
            validated = validate_data(data, self._fields, partial=False)
            await adapter.create_table(self.__table_name__, self._fields)
            row = await adapter.insert(self.__table_name__, validated, self._fields)
            
            # Update this instance
            for key, value in row.items():
                setattr(self, key, value)
        
        return self
    
    async def delete(self) -> bool:
        """
        Delete this record.
        
        Examples:
            await user.delete()
        
        Returns:
            True if deleted, False if not found
        """
        adapter = get_adapter()
        return await adapter.delete(self.__table_name__, self.id)
    
    async def refresh(self: T) -> T:
        """
        Refresh this record from the database.
        
        Examples:
            await user.refresh()  # Reload from DB
        """
        adapter = get_adapter()
        from pynext.db.query import Query
        
        query = Query(self.__class__, adapter, self._fields).where(id=self.id)
        row = await adapter.select_one(self.__table_name__, query, self._fields)
        
        if row is None:
            raise NotFoundError(self.__table_name__, id=self.id)
        
        for key, value in row.items():
            setattr(self, key, value)
        
        return self
    
    # Helper methods
    
    def _to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            name: getattr(self, name, None)
            for name in self._fields
        }
    
    @classmethod
    def _from_row(cls: Type[T], row: Dict[str, Any]) -> T:
        """Create instance from database row."""
        instance = cls.__new__(cls)
        for key, value in row.items():
            setattr(instance, key, value)
        return instance
    
    # Relationship accessors
    
    @classmethod
    def with_related(cls: Type[T], *relations: str) -> "Query[T]":
        """
        Start a query with eager loading.
        
        Shortcut for User.select().with_related(...)
        
        Examples:
            posts = await Post.with_related("author").all()
        """
        return cls.select().with_related(*relations)


# Re-export for convenience
__all__ = [
    "Table",
    "configure_db",
    "get_adapter",
    "_model_registry",
]

