"""
PyNext Database Layer.

A simple, type-safe ORM for PyNext applications.

Usage:
    from pynext.db import Table, configure_db, MemoryAdapter
    
    # Configure database
    adapter = MemoryAdapter()
    await adapter.connect()
    configure_db(adapter)
    
    # Define models
    class User(Table):
        name: str
        email: str
        age: int = 0
    
    # Use them
    user = await User.insert(name="John", email="john@example.com")
    users = await User.select().where(role="admin").order_by("name")
    await user.update(name="Jane")
    await user.delete()
    
    # Batch operations
    users = await User.insert_many([
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
    ])
    
    # Raw SQL
    from pynext.db import db
    users = await db.sql("SELECT * FROM users WHERE role = $1", "admin")
    
    # Transactions
    async with db.transaction():
        await User.insert(name="John")
        await Post.insert(title="Hello")
    
    # Type-safe SQL builder
    from pynext.db import sql
    users = await (
        sql.select("*")
        .from_("users")
        .where("role", "=", "admin")
        .execute()
    )
"""

# Core
from pynext.db.table import (
    Table,
    configure_db,
    get_adapter,
    _model_registry,
)

# Fields
from pynext.db.fields import (
    Field,
    FieldInfo,
    SQLType,
    parse_type_hint,
    create_auto_fields,
    serialize_value,
    deserialize_value,
)

# Query
from pynext.db.query import Query

# Raw SQL
from pynext.db.sql import (
    Database,
    db,
)

# Transactions
from pynext.db.transaction import (
    Transaction,
    Savepoint,
    IsolationLevel,
    transaction,
)

# SQL Builder
from pynext.db.builder import (
    SQLBuilder,
    SelectBuilder,
    InsertBuilder,
    UpdateBuilder,
    DeleteBuilder,
    JoinType,
    OrderDirection,
    sql,
)

# Relationships (core + backref + collections + loading)
from pynext.db.relationships import (
    # Core types
    RelationshipType,
    RelationshipInfo,
    BelongsTo,
    HasMany,
    HasOne,
    ManyToMany,
    belongs_to,
    has_many,
    has_one,
    many_to_many,
    setup_relationships,
    detect_relationships,
    detect_reverse_relationships,
    process_backrefs,
    # Backref
    BackrefConfig,
    BackrefRegistry,
    RelationshipSyncManager,
    get_backref_registry,
    get_sync_manager,
    reset_backref_registry,
    reset_sync_manager,
    # Collections
    SyncedList,
    ManyToManyCollection,
    # Many-to-Many
    JunctionConfig,
    JunctionTableFactory,
    JunctionManager,
    get_junction_factory,
    reset_junction_factory,
    DynamicManyToMany,
    AssociationProxy,
    # Loading strategies
    LoadStrategy,
    LoadOption,
    LazyLoadError,
    RelationshipLoader,
    get_loader,
    reset_loader,
    # Loading option functions
    joinedload,
    selectinload,
    subqueryload,
    raiseload,
    noload,
    lazyload,
    immediateload,
    eagerload,
    Load,
    # Dynamic relationships
    DynamicRelationship,
)

# Validation
from pynext.db.validation import (
    validate_type,
    validate_constraints,
    validate_field,
    validate_data,
    run_validators,
    Validator,
    MinLength,
    MaxLength,
    MinValue,
    MaxValue,
    Regex,
    Email,
    URL,
    OneOf,
    NotEmpty,
    Lowercase,
    Uppercase,
    Strip,
)

# Adapters
from pynext.db.adapters import (
    Adapter,
    MemoryAdapter,
    MockAdapter,
    # PostgreSQL (optional - requires asyncpg)
    PostgresAdapter,
    PostgresConfig,
    PostgresConfigError,
    AutoScalingPool,
    PoolStats,
    StatementCache,
)

# Exceptions
from pynext.db.exceptions import (
    DatabaseError,
    ValidationError,
    NotFoundError,
    QueryError,
    ConnectionError,
    TransactionError,
    RelationshipError,
    ConfigurationError,
)

# Migrations (lazy import to avoid circular dependencies)
def __getattr__(name):
    """Lazy import migrations module."""
    if name == "migrations":
        from pynext.db import migrations
        return migrations
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Core
    "Table",
    "configure_db",
    "get_adapter",
    "_model_registry",
    
    # Fields
    "Field",
    "FieldInfo",
    "SQLType",
    "parse_type_hint",
    "create_auto_fields",
    "serialize_value",
    "deserialize_value",
    
    # Query
    "Query",
    
    # Raw SQL
    "Database",
    "db",
    
    # Transactions
    "Transaction",
    "Savepoint",
    "IsolationLevel",
    "transaction",
    
    # SQL Builder
    "SQLBuilder",
    "SelectBuilder",
    "InsertBuilder",
    "UpdateBuilder",
    "DeleteBuilder",
    "JoinType",
    "OrderDirection",
    "sql",
    
    # Relationships
    "RelationshipType",
    "RelationshipInfo",
    "BelongsTo",
    "HasMany",
    "HasOne",
    "ManyToMany",
    "belongs_to",
    "has_many",
    "has_one",
    "many_to_many",
    "setup_relationships",
    "detect_relationships",
    "detect_reverse_relationships",
    "process_backrefs",
    
    # Backref (bidirectional relationships)
    "BackrefConfig",
    "BackrefRegistry",
    "RelationshipSyncManager",
    "get_backref_registry",
    "get_sync_manager",
    "reset_backref_registry",
    "reset_sync_manager",
    
    # Synced Collections
    "SyncedList",
    "ManyToManyCollection",
    
    # Many-to-Many
    "JunctionConfig",
    "JunctionTableFactory",
    "JunctionManager",
    "get_junction_factory",
    "reset_junction_factory",
    "DynamicManyToMany",
    "AssociationProxy",
    
    # Loading strategies
    "LoadStrategy",
    "LoadOption",
    "LazyLoadError",
    "RelationshipLoader",
    "get_loader",
    "reset_loader",
    
    # Loading option functions
    "joinedload",
    "selectinload",
    "subqueryload",
    "raiseload",
    "noload",
    "lazyload",
    "immediateload",
    "eagerload",
    "Load",
    
    # Dynamic relationships
    "DynamicRelationship",
    
    # Validation
    "validate_type",
    "validate_constraints",
    "validate_field",
    "validate_data",
    "run_validators",
    "Validator",
    "MinLength",
    "MaxLength",
    "MinValue",
    "MaxValue",
    "Regex",
    "Email",
    "URL",
    "OneOf",
    "NotEmpty",
    "Lowercase",
    "Uppercase",
    "Strip",
    
    # Adapters
    "Adapter",
    "MemoryAdapter",
    "MockAdapter",
    # PostgreSQL
    "PostgresAdapter",
    "PostgresConfig",
    "PostgresConfigError",
    "AutoScalingPool",
    "PoolStats",
    "StatementCache",
    
    # Exceptions
    "DatabaseError",
    "ValidationError",
    "NotFoundError",
    "QueryError",
    "ConnectionError",
    "TransactionError",
    "RelationshipError",
    "ConfigurationError",
    
    # Migrations (lazy import)
    "migrations",
]

