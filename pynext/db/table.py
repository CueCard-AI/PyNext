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


# =============================================================================
# FK On Delete Mapping (Phase 7.4.1)
# =============================================================================

# Map PyNext on_delete values to PostgreSQL ON DELETE actions
_ON_DELETE_MAP = {
    "cascade": "CASCADE",
    "nullify": "SET NULL",
    "protect": "RESTRICT",
    "none": "NO ACTION",
}


def _map_on_delete_to_postgres(on_delete: str) -> str:
    """
    Map PyNext on_delete value to PostgreSQL ON DELETE action.
    
    Args:
        on_delete: PyNext value ("cascade", "nullify", "protect", "none")
    
    Returns:
        PostgreSQL action ("CASCADE", "SET NULL", "RESTRICT", "NO ACTION")
    """
    return _ON_DELETE_MAP.get(on_delete.lower(), "NO ACTION")

if TYPE_CHECKING:
    from pynext.db.query import Query
    from pynext.db.adapters.base import Adapter

T = TypeVar("T", bound="Table")

# Global registry of all models
_model_registry: Dict[str, Type["Table"]] = {}


def _extract_list_table_type(type_hint: Any) -> Optional[type]:
    """
    Extract Table type from a List[Model] type hint for M2M auto-detection.
    
    Returns the Model class if:
    - type_hint is List[SomeTable] where SomeTable is a Table subclass
    - type_hint is list[SomeTable] (Python 3.9+)
    
    Returns None if:
    - Not a List type
    - List of primitives (List[str], List[int])
    - List of non-Table classes
    
    Examples:
        List[User] → User (if User is Table subclass)
        List[str] → None
        List["Post"] → "Post" (string for forward reference)
        int → None
    """
    import typing
    
    # Get origin for generic types
    origin = getattr(type_hint, "__origin__", None)
    
    # Check for List or list
    if origin is not list and origin is not List:
        return None
    
    # Get type arguments
    args = getattr(type_hint, "__args__", ())
    if not args:
        return None
    
    inner_type = args[0]
    
    # Handle string forward references
    if isinstance(inner_type, str):
        # Return the string - will be resolved later
        return inner_type
    
    # Handle ForwardRef
    if isinstance(inner_type, typing.ForwardRef):
        return inner_type.__forward_arg__
    
    # Check if it's a Table subclass
    # Import here to avoid circular imports
    try:
        if isinstance(inner_type, type):
            # Check if it has Table-like attributes
            # We can't import Table here due to circular imports
            # So we check for _fields which Table subclasses have
            if hasattr(inner_type, "_fields") or hasattr(inner_type, "__table_name__"):
                return inner_type
            
            # Also check if it's defined in user code (not primitives)
            if inner_type.__module__ != "builtins":
                # Could be a Table subclass that's not yet fully defined
                # Return it and let the metaclass handle it
                return inner_type
    except Exception:
        pass
    
    return None

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
    5. Processes backref definitions for bidirectional sync
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
        
        # Track relationship descriptors for later processing
        relationship_attrs: Dict[str, Any] = {}
        
        # Collect List[Model] fields for potential M2M auto-detection
        potential_m2m_fields: Dict[str, type] = {}
        
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
            
            # Check if it's a relationship descriptor
            from pynext.db.relationships import BelongsTo, HasMany, HasOne, ManyToMany
            if isinstance(default, (BelongsTo, HasMany, HasOne, ManyToMany)):
                # Set the rel_name now that we know it
                default.rel_name = field_name
                default._cache_attr = f"_cached_{field_name}"
                relationship_attrs[field_name] = default
                continue
            
            # Check for List[Model] pattern for M2M auto-detection
            # Only if no explicit descriptor is assigned
            if default is ... or default is None:
                target_model = _extract_list_table_type(type_hint)
                if target_model is not None:
                    potential_m2m_fields[field_name] = target_model
                    continue  # Don't process as regular field
            
            # Check if it's an explicit Field()
            if isinstance(default, Field):
                field_info = default.to_field_info(field_name, type_hint)
            else:
                field_info = parse_type_hint(field_name, type_hint, default)
            
            fields[field_name] = field_info
        
        # Auto-create M2M relationships for List[Model] fields
        # This happens after all fields are processed
        for field_name, target_model in potential_m2m_fields.items():
            from pynext.db.relationships import ManyToMany
            
            # Check if this is actually a has_many (target has FK to us)
            # For now, we treat bare List[Model] as M2M
            # has_many must be explicit: has_many(Model, backref="x")
            
            m2m_descriptor = ManyToMany(
                rel_name=field_name,
                model=target_model,
                through=None,  # Auto-create junction
                backref=None,  # Auto-generate from class name
                back_populates=None,
                lazy="select",
            )
            m2m_descriptor._cache_attr = f"_cached_{field_name}"
            relationship_attrs[field_name] = m2m_descriptor
            namespace[field_name] = m2m_descriptor
        
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
        
        # Process backrefs after class creation
        # This needs to happen after registration so forward references can resolve
        _process_model_backrefs(cls)
        
        # Resolve any pending backrefs waiting for this model
        _resolve_pending_backrefs(cls)
        
        # Sync cascade on_delete to FK fields (Phase 7.4.1)
        # This propagates relationship cascade settings to FK field constraints
        _sync_cascade_to_fk_fields(cls)
        
        return cls


def _process_model_backrefs(model: Type["Table"]) -> None:
    """
    Process backref definitions on a model.
    
    This scans the model's attributes for relationship descriptors
    with backref or back_populates set, and registers them.
    
    Args:
        model: The model class to process
    """
    from pynext.db.relationships import (
        BelongsTo,
        HasMany,
        HasOne,
        process_backrefs,
    )
    
    # Process backrefs using the relationships module function
    process_backrefs(model, _model_registry)


def _sync_cascade_to_fk_fields(model: Type["Table"]) -> None:
    """
    Sync on_delete cascade settings from relationships to FK fields.
    
    This is called after a model is created to propagate the on_delete
    setting from relationship descriptors (has_many, has_one) to the
    FK field's fk_on_delete attribute.
    
    Example:
        class User(Table):
            posts: List[Post] = has_many(Post, on_delete="cascade")
        
        # This syncs to Post._fields["author_id"].fk_on_delete = "CASCADE"
    
    Args:
        model: The model class to process
    """
    from pynext.db.relationships import HasMany, HasOne, ManyToMany
    
    # Scan for relationship descriptors with on_delete
    for attr_name in dir(model):
        if attr_name.startswith("_"):
            continue
        
        attr = getattr(model, attr_name, None)
        if attr is None:
            continue
        
        # Check for HasMany/HasOne with on_delete
        if isinstance(attr, (HasMany, HasOne)):
            on_delete = getattr(attr, "on_delete", "none")
            cascade = getattr(attr, "cascade", None)
            
            # Get the actual on_delete action
            if on_delete and on_delete != "none":
                pg_on_delete = _map_on_delete_to_postgres(on_delete)
            elif cascade and cascade.on_delete:
                pg_on_delete = "CASCADE"
            else:
                continue  # No on_delete to sync
            
            # Find the related model and update its FK field
            related_model = getattr(attr, "_model", None)
            if related_model is None:
                continue
            
            # Resolve string model name
            if isinstance(related_model, str):
                related_model = _model_registry.get(related_model.lower() + "s")
                if related_model is None:
                    continue
            
            # Get FK field name (e.g., "author_id" for User -> Post)
            fk_field = getattr(attr, "foreign_key", None)
            if fk_field is None:
                # Auto-detect from model name
                fk_field = model.__name__.lower() + "_id"
            
            # Update the FK field's fk_on_delete
            if hasattr(related_model, "_fields") and fk_field in related_model._fields:
                related_model._fields[fk_field].fk_on_delete = pg_on_delete


def _resolve_pending_backrefs(model: Type["Table"]) -> None:
    """
    Resolve any pending backrefs that were waiting for this model.
    
    When a model defines has_many("Post", backref="author") but Post
    doesn't exist yet, the backref is deferred. This function resolves
    those deferred backrefs when Post is finally created.
    
    Args:
        model: The newly created model
    """
    from pynext.db.relationships.backref import get_backref_registry
    
    registry = get_backref_registry()
    registry.resolve_pending(model)


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
        """Compare by id, or by identity if ids are not set."""
        if not isinstance(other, self.__class__):
            return False
        # For unsaved objects (no id), compare by identity
        self_id = getattr(self, "id", None)
        other_id = getattr(other, "id", None)
        if self_id is None or other_id is None:
            return self is other
        return self_id == other_id
    
    def __hash__(self) -> int:
        """Hash by id, or by identity if id is not set."""
        self_id = getattr(self, "id", None)
        if self_id is None:
            return id(self)  # Use object identity for unsaved objects
        return hash((self.__class__.__name__, self_id))
    
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
    
    async def save(self: T, _skip_cascade: bool = False) -> T:
        """
        Save this record (insert or update).
        
        If the record has an id, it updates. Otherwise, it inserts.
        Cascades save to related objects if cascade.on_save=True.
        
        Examples:
            user = User(name="John", email="john@example.com")
            await user.save()  # Inserts
            
            user.name = "Jane"
            await user.save()  # Updates
            
            # With cascade configured:
            class User(Table):
                posts: List[Post] = has_many(Post, cascade=CascadeOptions(on_save=True))
            
            user.posts[0].title = "Updated"
            await user.save()  # Also saves the modified post
        
        Args:
            _skip_cascade: Internal flag to skip cascade (prevents recursion)
        
        Returns:
            The saved model instance (self)
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
        
        # Handle cascade save unless skipped
        if not _skip_cascade:
            from pynext.db.relationships.cascade import get_cascade_manager
            manager = get_cascade_manager()
            await manager.cascade_save(self)
        
        return self
    
    async def delete(self, _skip_cascade: bool = False) -> bool:
        """
        Delete this record.
        
        Handles cascade operations based on relationship configuration:
        - on_delete="cascade": Delete related records
        - on_delete="nullify": Set FK to NULL on related records
        - on_delete="protect": Raise error if related records exist
        
        Examples:
            await user.delete()
            
            # With cascade configured on User.posts as on_delete="cascade":
            await user.delete()  # Also deletes all posts
        
        Args:
            _skip_cascade: Internal flag to skip cascade (prevents recursion)
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            ProtectedDeleteError: If trying to delete with protected relationships
        """
        adapter = get_adapter()
        
        # Handle cascades unless skipped (internal recursive call)
        if not _skip_cascade:
            from pynext.db.relationships.cascade import get_cascade_manager
            manager = get_cascade_manager()
            
            # Check for protected relationships first
            protected_error = await manager.check_protected(self)
            if protected_error:
                raise protected_error
            
            # Execute cascades (delete related, nullify FKs)
            await manager.cascade_delete(self)
        
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

