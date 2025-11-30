# PyNext Database Layer

A simple, type-safe ORM for PyNext applications. Just Python types, no magic.

## Table of Contents

1. [Why This API?](#why-this-api)
2. [Quick Start](#quick-start)
3. [Defining Models](#defining-models)
4. [CRUD Operations](#crud-operations)
5. [Batch Operations](#batch-operations)
6. [Raw SQL](#raw-sql)
7. [Transactions](#transactions)
8. [Type-Safe SQL Builder](#type-safe-sql-builder)
9. [Query Builder](#query-builder)
10. [Relationships](#relationships)
11. [Validation](#validation)
12. [Adapters](#adapters)
13. [Testing](#testing)
14. [Architecture](#architecture)
15. [Troubleshooting](#troubleshooting)

---

## Why This API?

### First Principles: What is an ORM?

An ORM (Object-Relational Mapper) bridges the gap between Python objects and database tables:

```
┌─────────────────┐         ┌─────────────────┐
│  Python Object  │  <--->  │  Database Row   │
│                 │   ORM   │                 │
│  user.name      │         │  name VARCHAR   │
│  user.age       │         │  age INTEGER    │
└─────────────────┘         └─────────────────┘
```

**Without an ORM**, you write raw SQL:
```python
# Tedious, error-prone, not type-safe
cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
user_id = cursor.lastrowid
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
row = cursor.fetchone()
user = {"id": row[0], "name": row[1], "email": row[2]}
```

**With PyNext's ORM**, you write Python:
```python
# Simple, type-safe, readable
user = await User.insert(name="John", email="john@example.com")
```

### Why Not SQLAlchemy/Django?

| Feature | SQLAlchemy | Django ORM | PyNext |
|---------|------------|------------|--------|
| Define a model | 10+ lines with Column() | 10+ lines with Field() | 3 lines with type hints |
| Async support | Requires extra setup | No | Yes (native) |
| Type safety | Limited | Limited | Full (type hints) |
| Learning curve | Steep | Moderate | Minimal |
| AI-friendly | Complex patterns | Framework-specific | Just Python types |

---

## Quick Start

### 1. Configure the Database

```python
from pynext.db import configure_db, MemoryAdapter

# For testing/development
adapter = MemoryAdapter()
await adapter.connect()
configure_db(adapter)
```

### 2. Define a Model

```python
from pynext.db import Table

class User(Table):
    name: str
    email: str
    age: int = 0
```

That's it. You get:
- `id: int` field (auto-increment primary key)
- `created_at: datetime` field (set on insert)
- `updated_at: datetime` field (set on insert/update)
- Type validation on create/update
- Full query builder

### 3. Use It

```python
# Create
user = await User.insert(name="John", email="john@example.com")

# Read
user = await User.get(1)
users = await User.all()

# Update
await user.update(name="Jane")

# Delete
await user.delete()
```

---

## Defining Models

### Basic Model

```python
class User(Table):
    name: str           # Required string
    email: str          # Required string
    age: int = 0        # Optional with default
    role: str = "user"  # Optional with default
```

### All Supported Types

| Python Type | SQL Type | Example |
|-------------|----------|---------|
| `str` | VARCHAR(255) | `name: str` |
| `int` | INTEGER | `age: int` |
| `float` | REAL | `price: float` |
| `bool` | BOOLEAN | `active: bool` |
| `datetime` | TIMESTAMP | `created: datetime` |
| `date` | DATE | `birthday: date` |
| `time` | TIME | `alarm: time` |
| `Decimal` | DECIMAL | `amount: Decimal` |
| `UUID` | UUID | `external_id: UUID` |
| `bytes` | BLOB | `data: bytes` |
| `list` | JSON | `tags: list[str]` |
| `dict` | JSON | `metadata: dict` |

### Optional Fields

Use `Optional[T]` or `T | None` for nullable fields:

```python
class User(Table):
    name: str                    # Required
    bio: Optional[str] = None    # Optional, nullable
    nickname: str | None = None  # Same as Optional[str]
```

### Custom Table Name

```python
class UserAccount(Table):
    __table_name__ = "users"  # Use "users" table instead of "useraccounts"
    name: str
```

### Explicit Field Configuration

Use `Field()` for advanced options:

```python
from pynext.db import Table, Field

class User(Table):
    name: str
    email: str = Field(unique=True, max_length=100)
    bio: str = Field(max_length=1000, nullable=True)
    role: str = Field(default="user")
```

Field options:
- `default` - Default value
- `max_length` - Maximum string length
- `unique` - Unique constraint
- `index` - Create database index
- `nullable` - Allow NULL values
- `validators` - List of validator functions

---

## CRUD Operations

### Create

```python
# Insert a new record
user = await User.insert(name="John", email="john@example.com")
print(user.id)  # 1
print(user.created_at)  # 2024-01-15 12:30:00

# Or create instance and save
user = User(name="Jane", email="jane@example.com")
await user.save()  # Inserts since no id
```

### Read

```python
# Get by id
user = await User.get(1)

# Get by id (returns None if not found)
user = await User.get_or_none(1)

# Get by field
user = await User.get_by(email="john@example.com")

# Get all
users = await User.all()

# Count
total = await User.count()

# Check existence
exists = await User.exists(role="admin")
```

### Update

```python
# Update specific fields
await user.update(name="Jane", role="admin")

# Or modify and save
user.name = "Jane"
user.role = "admin"
await user.save()  # Updates since has id
```

### Delete

```python
# Delete a record
await user.delete()
```

---

## Batch Operations

For better performance when dealing with multiple records:

### Insert Many

```python
# Insert multiple records at once (10x faster than loop)
users = await User.insert_many([
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
    {"name": "Charlie", "email": "charlie@example.com"},
])
# Returns list of created User instances
```

### Update Many

```python
# Update all matching records
count = await User.update_many(
    where={"role": "user"},      # Filter
    set={"active": True}         # New values
)
print(f"Updated {count} users")
```

### Delete Many

```python
# Delete all matching records
count = await User.delete_many(where={"active": False})
print(f"Deleted {count} inactive users")
```

### Upsert

```python
# Insert or update (atomic operation)
user = await User.upsert(
    where={"email": "john@example.com"},     # Find by this
    create={"name": "John", "email": "john@example.com"},  # Create if not found
    update={"name": "John Updated"}          # Update if found
)
```

---

## Raw SQL

When the ORM isn't enough, raw SQL is always available:

### Basic Queries

```python
from pynext.db import db

# Simple SELECT
rows = await db.sql("SELECT * FROM users WHERE role = $1", "admin")
# Returns: [{"id": 1, "name": "Alice", ...}, ...]

# With model mapping (returns User instances)
users = await db.sql(
    "SELECT * FROM users WHERE role = $1",
    "admin",
    model=User
)
# Returns: [User(id=1, name="Alice", ...), ...]
```

### Single Row / Value

```python
# Fetch single row
row = await db.sql_one("SELECT * FROM users WHERE id = $1", 1)

# Fetch single value (perfect for COUNT, SUM, etc.)
count = await db.sql_val("SELECT COUNT(*) FROM users")
total = await db.sql_val("SELECT SUM(balance) FROM accounts")
```

### Execute (INSERT/UPDATE/DELETE)

```python
# Execute non-SELECT queries
count = await db.execute(
    "UPDATE users SET active = true WHERE last_login > $1",
    datetime(2024, 1, 1)
)
print(f"Updated {count} rows")
```

### Parameterized Queries

Always use parameters to prevent SQL injection:

```python
# GOOD: Parameters are escaped automatically
rows = await db.sql("SELECT * FROM users WHERE role = $1", user_input)

# BAD: Never interpolate user input directly!
# rows = await db.sql(f"SELECT * FROM users WHERE role = '{user_input}'")
```

---

## Transactions

Ensure data consistency with transactions:

### Simple Transaction

```python
from pynext.db import db

# Auto-commit on success, auto-rollback on error
async with db.transaction():
    await User.insert(name="John")
    await Post.insert(title="Hello", author_id=1)
# Both succeed or both fail
```

### With Savepoints

```python
# Partial rollbacks with savepoints
async with db.transaction() as tx:
    await User.insert(name="John")
    
    try:
        async with tx.savepoint():
            await Post.insert(title="Risky")
            # If this fails, only savepoint rolls back
    except Exception:
        pass  # Post insert rolled back, but User insert preserved
    
    await Comment.insert(text="Safe")
```

### Manual Control

```python
async with db.transaction(auto_commit=False) as tx:
    await User.insert(name="John")
    
    if some_condition:
        await tx.commit()
    else:
        await tx.rollback()
```

### Isolation Levels

```python
# Strongest isolation (for critical operations)
async with db.transaction(isolation="serializable"):
    balance = await db.sql_val("SELECT balance FROM accounts WHERE id = $1", 1)
    await db.execute("UPDATE accounts SET balance = $1 WHERE id = $2", balance - 100, 1)
```

---

## Type-Safe SQL Builder

When you need complex SQL with type safety:

```python
from pynext.db import sql

# SELECT with joins, filters, ordering
users = await (
    sql.select("users.name", "posts.title")
    .from_("users")
    .join("posts", "users.id", "=", "posts.author_id")
    .where("users.role", "=", "admin")
    .where("posts.published", "=", True)
    .order_by("posts.created_at", "DESC")
    .limit(10)
    .execute()
)

# INSERT
await (
    sql.insert("users")
    .values(name="John", email="john@example.com")
    .on_conflict_do_nothing("email")  # Handle duplicates
    .execute()
)

# UPDATE
await (
    sql.update("users")
    .set(active=True, role="member")
    .where("last_login", ">", datetime(2024, 1, 1))
    .execute()
)

# DELETE
await (
    sql.delete("users")
    .where("active", "=", False)
    .execute()
)
```

---

## Query Builder

The query builder is **chainable** and **lazy** - nothing executes until you await:

```python
# Build the query (nothing executed yet)
query = User.select().where(role="admin").order_by("-created_at").limit(10)

# Execute when awaited
users = await query
```

### Filter Methods

```python
# Equality
.where(role="admin")
.where(role="admin", active=True)  # AND

# Not equal
.where_not(role="admin")

# IN
.where_in(id=[1, 2, 3])

# LIKE
.where_like(name="%john%")

# Comparisons
.where_gt(age=18)    # > 18
.where_gte(age=18)   # >= 18
.where_lt(age=65)    # < 65
.where_lte(age=65)   # <= 65

# NULL checks
.where_null("deleted_at")
.where_not_null("email")
```

### Ordering

```python
# Ascending
.order_by("name")

# Descending
.order_by("-created_at")

# Multiple
.order_by("role", "-name")
```

### Pagination

```python
# Limit and offset
.limit(10).offset(20)

# Page helper (page 3, 20 per page)
.page(3, 20)
```

### Execution Methods

```python
# Get all matching
users = await User.select().where(role="admin").all()

# Get first (or None)
user = await User.select().where(email="test@example.com").first()

# Get exactly one (raises NotFoundError if not found)
user = await User.select().where(id=1).one()

# Count
count = await User.select().where(active=True).count()

# Check existence
exists = await User.select().where(role="admin").exists()

# Delete matching
deleted = await User.select().where(active=False).delete()

# Update matching
updated = await User.select().where(role="user").update(role="member")
```

### Chaining Example

```python
# Get the 10 most recent active admin users
admins = await (
    User.select()
    .where(role="admin")
    .where(active=True)
    .order_by("-created_at")
    .limit(10)
)
```

---

## Relationships

### Automatic Detection

Foreign keys are detected from `*_id` naming:

```python
class Post(Table):
    title: str
    author_id: int  # Auto-detects FK to "authors" table
```

### Eager Loading

Load related models in a single query:

```python
# Load posts with their authors
posts = await Post.select().with_related("author")

for post in posts:
    print(post.title, post.author.name)  # No extra query!
```

Multiple relations:
```python
posts = await Post.select().with_related("author", "comments")
```

Nested relations:
```python
posts = await Post.select().with_related("author__profile")
```

### Explicit Relationships

For complex cases, define relationships explicitly:

```python
from pynext.db import Table, belongs_to, has_many, has_one

class User(Table):
    name: str

class Profile(Table):
    bio: str
    user_id: int

class Post(Table):
    title: str
    author_id: int

# User has many posts
# Post belongs to author (User)
# User has one profile
```

---

## Validation

### Automatic Type Validation

```python
# This raises ValidationError
await User.insert(name=123)  # "name: expected str, got int"
await User.insert()          # "name: required field missing"
await User.insert(name="")   # "name: cannot be empty"
```

### Type Coercion

Some types are automatically coerced:

```python
# String "5" -> int 5
await User.insert(name="John", age="25")  # Works!

# "true"/"false" -> bool
await User.insert(name="John", active="true")  # Works!

# ISO string -> datetime
await Event.insert(name="Party", start="2024-01-15T20:00:00")  # Works!
```

### Built-in Validators

```python
from pynext.db import (
    Field, MinLength, MaxLength, MinValue, MaxValue,
    Email, URL, Regex, OneOf, NotEmpty
)

class User(Table):
    name: str = Field(validators=[MinLength(2), MaxLength(50)])
    email: str = Field(validators=[Email()])
    role: str = Field(validators=[OneOf(["admin", "user", "guest"])])
    age: int = Field(validators=[MinValue(0), MaxValue(150)])
    website: str = Field(validators=[URL()], nullable=True)
```

### Custom Validators

```python
def validate_username(value: str) -> str:
    if not value.isalnum():
        raise ValueError("must be alphanumeric")
    return value.lower()

class User(Table):
    username: str = Field(validators=[validate_username])
```

### Transformer Validators

Some validators also transform the value:

```python
from pynext.db import Lowercase, Uppercase, Strip

class User(Table):
    email: str = Field(validators=[Strip(), Lowercase()])  # "  JOHN@Example.COM  " -> "john@example.com"
```

---

## Adapters

### MockAdapter (Dict-based)

Pure Python, no dependencies. Perfect for unit tests:

```python
from pynext.db import MockAdapter, configure_db

adapter = MockAdapter()
await adapter.connect()
configure_db(adapter)

# Use it
user = await User.insert(name="Test")

# Reset for next test
adapter.reset()
```

### MemoryAdapter (SQLite)

Real SQL execution for integration tests:

```python
from pynext.db import MemoryAdapter, configure_db

adapter = MemoryAdapter()
await adapter.connect()
configure_db(adapter)

# Uses real SQL
user = await User.insert(name="Test")

# Reset for next test
adapter.reset()
```

### Raw SQL

When ORM isn't enough:

```python
# Execute raw SQL
await adapter.execute("UPDATE users SET role = 'admin' WHERE id = $1", (1,))

# Fetch rows
rows = await adapter.fetch_all("SELECT * FROM users WHERE age > $1", (18,))

# Fetch one row
row = await adapter.fetch_one("SELECT * FROM users WHERE id = $1", (1,))
```

### Transactions

```python
async with adapter.transaction():
    await User.insert(name="John")
    await Account.insert(user_id=1, balance=100)
    # If any operation fails, all are rolled back
```

---

## Testing

### Pytest Fixtures

```python
import pytest
from pynext.db import MockAdapter, configure_db

@pytest.fixture
async def db():
    """Fresh database for each test."""
    adapter = MockAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    adapter.reset()
    await adapter.disconnect()

async def test_create_user(db):
    user = await User.insert(name="John", email="john@test.com")
    assert user.id == 1
    assert user.name == "John"
```

### Using MemoryAdapter for SQL Tests

```python
@pytest.fixture
async def sql_db():
    """SQLite for testing real SQL."""
    adapter = MemoryAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    adapter.reset()
    await adapter.disconnect()
```

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                       Your Code                            │
│                                                            │
│   user = await User.insert(name="John")                    │
│   users = await User.select().where(role="admin")          │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                         Table                               │
│                                                            │
│   - Parses type hints → FieldInfo                          │
│   - Provides CRUD class methods                            │
│   - Auto-generates id, created_at, updated_at             │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                     Query Builder                           │
│                                                            │
│   - Chainable filters: .where(), .order_by(), .limit()     │
│   - Lazy evaluation (executes on await)                    │
│   - Relationship loading: .with_related()                  │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                       Validation                            │
│                                                            │
│   - Type validation and coercion                           │
│   - Constraint checking (max_length, etc.)                 │
│   - Custom validators                                      │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                        Adapter                              │
│                                                            │
│   MockAdapter ──→ Pure Python (dict storage)               │
│   MemoryAdapter ──→ SQLite (in-memory)                     │
│   PostgresAdapter ──→ PostgreSQL (Phase 5 - see ROADMAP)   │
│   SupabaseAdapter ──→ Supabase (Phase 5 - see ROADMAP)     │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
                     [ Database ]
```

---

## Coming Soon: Phase 5 Database Adapters

The next phase of the database layer includes production-ready PostgreSQL and Supabase adapters with:

- **High-Performance Pooling**: asyncpg pool with auto-scaling, idle recycling, and connection warmup
- **Production Reliability**: Circuit breakers, retries with exponential backoff, health checks
- **High-Load Scalability**: Request queuing, load shedding, connection multiplexing
- **Error Logging**: Structured logs, slow query detection, pool exhaustion warnings
- **Supabase Integration**: Auth, Storage, Realtime subscriptions, Edge Functions, RLS helpers

See [ROADMAP.md](../ROADMAP.md#phase-5-database-adapters-postgresql--supabase) for the full implementation plan.

---

## Troubleshooting

### "No database adapter configured"

You need to call `configure_db()` before using models:

```python
from pynext.db import configure_db, MockAdapter

adapter = MockAdapter()
await adapter.connect()
configure_db(adapter)  # <- Don't forget this!
```

### "ValidationError: name: required field missing"

The field has no default and you didn't provide a value:

```python
class User(Table):
    name: str  # Required!
    role: str = "user"  # Has default

# This fails:
await User.insert(role="admin")  # Missing name!

# This works:
await User.insert(name="John", role="admin")
```

### "ValidationError: email: expected str, got int"

Type mismatch. Pass the correct type:

```python
# Wrong:
await User.insert(name="John", email=12345)

# Right:
await User.insert(name="John", email="john@example.com")
```

### "NotFoundError: User not found: id=999"

The record doesn't exist:

```python
# Use get_or_none to avoid exception:
user = await User.get_or_none(999)
if user:
    print(user.name)
```

### Query returns empty list

Check your filters:

```python
# Debug by removing filters one by one
users = await User.select()  # All users
users = await User.select().where(role="admin")  # Only admins
users = await User.select().where(role="admin").where(active=True)  # Active admins
```

### Relationship not loading

Make sure to use `with_related()`:

```python
# Wrong - author is None
posts = await Post.select()
print(posts[0].author)  # None!

# Right - author is loaded
posts = await Post.select().with_related("author")
print(posts[0].author.name)  # "John"
```

