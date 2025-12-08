# Query Builder: Complete Guide

## Executive Summary

The PyNext Query Builder is a **stupid-simple, AI-friendly** API for database queries. It provides three syntax styles, chainable methods, SQL escape hatches, and Go-powered parallel execution for 2-3x speedups.

**Key Value Proposition**: Write clean Python code → Get optimized, secure SQL → Execute with true parallelism.

---

## Table of Contents

1. [The Problem We Solve](#the-problem-we-solve)
2. [Who Should Use This](#who-should-use-this)
3. [What It Provides](#what-it-provides)
4. [When to Use What](#when-to-use-what)
5. [Where It Fits](#where-it-fits)
6. [Why This Design](#why-this-design)
7. [Quick Start](#quick-start)
8. [Three Syntax Styles](#three-syntax-styles)
9. [Chainable Methods](#chainable-methods)
10. [Execution Methods](#execution-methods)
11. [SQL Escape Hatches](#sql-escape-hatches)
12. [Parallel Execution](#parallel-execution)
13. [Debugging](#debugging)
14. [Common Patterns](#common-patterns)
15. [Performance Tips](#performance-tips)

---

## The Problem We Solve

### Traditional ORM Pain Points

**Problem 1: Complex, Unreadable Query APIs**
```python
# Django ORM - WTF does this mean?
User.objects.filter(
    Q(age__gt=18) & (Q(role__in=['admin', 'mod']) | Q(is_superuser=True))
).exclude(status='deleted').select_related('profile').order_by('-created_at')[:10]

# SQLAlchemy - Even worse
session.query(User).filter(
    and_(
        User.age > 18,
        or_(User.role.in_(['admin', 'mod']), User.is_superuser == True)
    )
).filter(User.status != 'deleted').options(joinedload(User.profile)).order_by(User.created_at.desc()).limit(10)
```

**Problem 2: Magic Strings and Hidden Complexity**
```python
# Django's double-underscore magic
User.objects.filter(profile__address__city__name__icontains='york')
# What SQL does this generate? How many JOINs?
```

**Problem 3: Hard for AI/LLMs to Understand**
```python
# LLM prompt: "Add a filter for users over 25"
# Django: User.objects.filter(age__gt=25)  ← LLM might write age__gte or age_gt
# SQLAlchemy: session.query(User).filter(User.age > 25)  ← Needs to know session context
```

**Problem 4: No True Parallelism**
```python
# Python's GIL prevents true parallel query execution
# Even asyncio.gather doesn't help with CPU-bound serialization
```

### The PyNext Solution

```python
# PyNext - Crystal clear, AI-friendly
users = await User.q(
    ("age", ">", 18),
    ("role", "in", ["admin", "mod"]),
).select("id", "name").order("-created_at").limit(10)

# Explicit operators, no magic strings, obvious intent
# LLM prompt: "Add filter for age > 25"
# LLM response: .where(("age", ">", 25))  ← Obvious!
```

---

## Who Should Use This

### Primary Audience

| Who | Why PyNext Query Builder |
|-----|--------------------------|
| **Python Backend Developers** | Clean, intuitive API without ORM complexity |
| **Full-Stack Developers** | Fast iteration with clear query syntax |
| **AI/LLM-Assisted Development** | Predictable patterns LLMs can generate correctly |
| **Junior Developers** | Gentle learning curve, explicit syntax |
| **Performance-Focused Teams** | Go-powered parallel execution |

### Prerequisites

- **Python**: 3.10+ (async/await support)
- **PostgreSQL**: 12+ (primary supported database)
- **Experience Level**: Beginner to Advanced

### Team Fit

✅ **Great fit if you:**
- Value code readability over "cleverness"
- Want LLMs to help write database code
- Need parallel query execution
- Prefer explicit over implicit

❌ **May not fit if you:**
- Heavily invested in Django/SQLAlchemy ecosystem
- Need multi-database support (MySQL, SQLite, etc.)
- Require complex ORM features (identity map, unit of work)

---

## What It Provides

### Core Features

| Feature | Description | Example |
|---------|-------------|---------|
| **Three Syntax Styles** | Tuple, SQL string, or functions | `("age", ">", 18)` or `gt("age", 18)` |
| **Chainable Methods** | Build queries fluently | `.select().where().order().limit()` |
| **Type Safety** | IDE autocomplete, type hints | `User.q() -> QueryBuilder[User]` |
| **SQL Escape Hatches** | Four levels of raw SQL | `where_raw()`, `db.sql()`, etc. |
| **Parallel Execution** | 2-3x speedup | `QueryBuilder.parallel()` |
| **Go-Powered** | Optimization, SQL generation | Bypasses Python's GIL |
| **Security** | SQL injection prevention | Parameterized queries, validation |

### Feature Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        QUERY BUILDER FEATURES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  QUERY BUILDING                     EXECUTION                                │
│  ──────────────                     ─────────                                │
│  ✓ Tuple syntax                     ✓ .all() - Get all rows                 │
│  ✓ SQL string syntax                ✓ .first() - Get first row              │
│  ✓ Function syntax                  ✓ .one() - Get exactly one              │
│  ✓ Logical operators (AND/OR/NOT)   ✓ .count() - Count rows                 │
│  ✓ All comparison operators         ✓ .exists() - Check existence           │
│  ✓ NULL handling                    ✓ .delete() - Delete rows               │
│  ✓ Pattern matching (LIKE/ILIKE)    ✓ .update() - Update rows               │
│  ✓ Range queries (BETWEEN)          ✓ .parallel() - Parallel execution      │
│  ✓ Array/JSON operators             ✓ .batch() - Auto-batch queries         │
│                                                                              │
│  QUERY MODIFIERS                    DEBUGGING                                │
│  ───────────────                    ─────────                                │
│  ✓ .select() - Column selection     ✓ .explain() - Human-readable query     │
│  ✓ .where() - Add conditions        ✓ .to_dict() - AST as dictionary        │
│  ✓ .order() - Sorting               ✓ Logging support                       │
│  ✓ .limit() / .offset()             ✓ Query timing                          │
│  ✓ .page() - Pagination                                                      │
│  ✓ .include() - Eager loading                                                │
│  ✓ .distinct() - Unique rows                                                 │
│  ✓ .for_update() - Row locking                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## When to Use What

### Syntax Style Decision Tree

```
                         ┌─────────────────────────────┐
                         │ What's your situation?      │
                         └─────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │ Quick & simple  │    │ IDE autocomplete│    │ Raw SQL needed  │
    │ No imports      │    │ Type safety     │    │ Complex queries │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
              │                       │                       │
              ▼                       ▼                       ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │ TUPLE SYNTAX    │    │ FUNCTION SYNTAX │    │ SQL STRING      │
    │ ("age", ">", 18)│    │ gt("age", 18)   │    │ "age > $1", 18  │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Method Selection Guide

| I want to... | Use this method | Example |
|--------------|-----------------|---------|
| Get all matching rows | `.all()` or `await query` | `users = await User.q()` |
| Get first row or None | `.first()` | `user = await User.q(id=1).first()` |
| Get exactly one row | `.one()` | `user = await User.q(id=1).one()` |
| Count rows | `.count()` | `total = await User.q().count()` |
| Check if rows exist | `.exists()` | `if await User.q(email=email).exists():` |
| Delete rows | `.delete()` | `await User.q(status="deleted").delete()` |
| Update rows | `.update()` | `await User.q(id=1).update(name="New")` |
| Execute in parallel | `.parallel()` | `await QueryBuilder.parallel(q1, q2)` |

---

## Where It Fits

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           YOUR APPLICATION                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│    │   FastAPI   │    │    Flask    │    │   Django    │                     │
│    │   Endpoint  │    │    View     │    │    View     │                     │
│    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│           │                  │                  │                            │
│           └──────────────────┼──────────────────┘                            │
│                              │                                               │
│                              ▼                                               │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │                      SERVICE / REPOSITORY LAYER                      │   │
│    │                                                                      │   │
│    │   class UserService:                                                 │   │
│    │       async def get_dashboard(self, user_id):                        │   │
│    │           return await QueryBuilder.parallel(                        │   │
│    │               User.q(("id", "=", user_id)),                          │   │
│    │               Order.q(("user_id", "=", user_id)),                    │   │
│    │           )                                                          │   │
│    │                                                                      │   │
│    └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │                      PYNEXT QUERY BUILDER                            │   │
│    │                                                                      │   │
│    │   User.q(("age", ">", 18))     # Create query                        │   │
│    │       .select("id", "name")    # Chain methods                       │   │
│    │       .order("-created_at")    # More chaining                       │   │
│    │       .limit(10)               # Build complete                      │   │
│    │                                                                      │   │
│    └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │                      GO BRIDGE (pynext_go)                           │   │
│    │                                                                      │   │
│    │   • Parse AST from Python                                            │   │
│    │   • Validate for security                                            │   │
│    │   • Optimize conditions                                              │   │
│    │   • Generate SQL                                                     │   │
│    │   • Execute with pgx                                                 │   │
│    │   • Parallel goroutine execution                                     │   │
│    │                                                                      │   │
│    └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │                         POSTGRESQL                                   │   │
│    └─────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### File Organization

```
your_project/
├── models/
│   ├── __init__.py
│   ├── user.py          # class User(Table): ...
│   └── order.py         # class Order(Table): ...
│
├── services/
│   ├── __init__.py
│   └── user_service.py  # Uses QueryBuilder here
│
├── routes/
│   ├── __init__.py
│   └── users.py         # FastAPI routes
│
└── main.py              # App entry point
```

---

## Why This Design

### Design Principles

#### 1. Explicit Over Implicit

```python
# BAD: Django magic (what does __gt mean?)
User.objects.filter(age__gt=18)

# GOOD: PyNext explicit
User.q(("age", ">", 18))  # Crystal clear!
User.q(gt("age", 18))     # Also clear!
```

**Why?** 
- New developers understand immediately
- LLMs generate correct code
- Code reviews are faster
- Debugging is easier

#### 2. One Query, Multiple Syntaxes

```python
# All three produce the same result:
User.q(("age", ">", 18))           # Tuple: Quick, no imports
User.q(gt("age", 18))              # Function: Type-safe, autocomplete
User.q("age > $1", 18)             # SQL: For SQL lovers

# Why three syntaxes?
# - Different developers have different preferences
# - Different situations call for different approaches
# - Gradual adoption from SQL to builder
```

#### 3. Chainable, Immutable Methods

```python
# Each method returns a new QueryBuilder
query = User.q()
query = query.where(gt("age", 18))  # New query
query = query.order("-created_at")  # New query
query = query.limit(10)             # New query

# Why immutable?
# - No side effects
# - Safe to pass queries around
# - Can branch queries
base = User.q(("active", "=", True))
admins = base.where(("role", "=", "admin"))
users = base.where(("role", "=", "user"))
```

#### 4. Escape Hatches for Complex SQL

```python
# When the builder can't express your query:
# Level 1: SQL in condition
User.q("jsonb_col @> $1", '{"key": "value"}')

# Level 2: Raw SQL (returns dicts)
db.sql("SELECT * FROM users WHERE complex_func()")

# Level 3: Raw SQL with model mapping
User.sql("SELECT * FROM users WHERE ...")

# Level 4: Mix builder with raw
User.q(gt("age", 18)).where_raw("custom_func($1)", [value])

# Why escape hatches?
# - No builder covers 100% of SQL
# - Don't fight the tool
# - Gradual migration path
```

#### 5. Go for Performance

```python
# Python's GIL limits parallelism
# Go has no GIL - true parallel execution

# 3 queries sequential: ~0.45ms
# 3 queries parallel:   ~0.20ms (2.25x faster!)

await QueryBuilder.parallel(
    User.q(...),
    Order.q(...),
    Stats.q(...),
)
```

**Why Go specifically?**
- Goroutines: Lightweight, true parallelism
- pgx: Excellent PostgreSQL driver
- CGO: Clean Python integration
- Fast compilation: Quick iteration

---

## Quick Start

### Installation

```bash
# From GitHub (PyPI coming soon)
pip install git+https://github.com/CueCard-AI/PyNext.git

# Or from source
git clone https://github.com/CueCard-AI/PyNext.git
cd PyNext && pip install -e ".[dev]"
```

### Define Models

```python
# models/user.py
from pynext.db import Table

class User(Table):
    name: str
    email: str
    age: int
    status: str = "active"
```

### Write Queries

```python
# Basic query
users = await User.q(("age", ">", 18))

# With chaining
users = await (User.q(("age", ">", 18))
    .select("id", "name", "email")
    .order("-created_at")
    .limit(10))

# Parallel execution
users, orders = await QueryBuilder.parallel(
    User.q(("status", "=", "active")),
    Order.q(("total", ">", 100)),
)
```

---

## Three Syntax Styles

### Style 1: Tuple Syntax

**Best for**: Quick queries, no imports needed, maximum readability.

```python
# Basic comparisons
users = await User.q(("age", ">", 18))
users = await User.q(("status", "=", "active"))
users = await User.q(("score", ">=", 80))

# Multiple conditions (implicit AND)
users = await User.q(
    ("age", ">", 18),
    ("status", "=", "active"),
    ("email", "is not null"),
)

# All supported operators
("field", "=", value)         # Equal
("field", "!=", value)        # Not equal  
("field", "<>", value)        # Not equal (SQL style)
("field", ">", value)         # Greater than
("field", ">=", value)        # Greater than or equal
("field", "<", value)         # Less than
("field", "<=", value)        # Less than or equal
("field", "like", "%pat%")    # Pattern (case-sensitive)
("field", "ilike", "%pat%")   # Pattern (case-insensitive)
("field", "in", [a, b, c])    # In list
("field", "not in", [a, b])   # Not in list
("field", "is null")          # Is NULL (2 elements!)
("field", "is not null")      # Is NOT NULL (2 elements!)
("field", "between", a, b)    # Between (4 elements!)
```

### Style 2: Condition Functions

**Best for**: Type safety, IDE autocomplete, complex conditions.

```python
from pynext.db.conditions import (
    # Comparison
    eq, ne, gt, gte, lt, lte,
    # Pattern matching
    like, ilike, contains, startswith, endswith,
    # List operations
    in_, not_in,
    # Null checks
    is_null, not_null,
    # Range
    between,
    # Logical
    and_, or_, not_,
    # Raw SQL
    raw,
)

# Basic
users = await User.q(gt("age", 18))
users = await User.q(eq("status", "active"))

# Pattern matching
users = await User.q(contains("name", "john"))      # ILIKE '%john%'
users = await User.q(startswith("email", "admin"))  # LIKE 'admin%'

# Logical combinations
users = await User.q(
    and_(
        gt("age", 18),
        or_(eq("role", "admin"), eq("role", "moderator"))
    )
)
```

### Style 3: SQL String

**Best for**: SQL experts, complex expressions, PostgreSQL-specific features.

```python
# Parameterized (safe!)
users = await User.q("age > $1 AND status = $2", 18, "active")

# PostgreSQL operators
users = await User.q("jsonb_col @> $1", '{"key": "value"}')
users = await User.q("array_col && $1", ["a", "b"])

# Complex expressions
users = await User.q(
    "EXTRACT(YEAR FROM created_at) = $1 AND score > $2",
    2024, 80
)
```

---

## Chainable Methods

### `.select(*columns)`

Choose which columns to fetch:

```python
# Select specific columns
users = await User.q().select("id", "name", "email")

# With table prefix (for joins)
data = await User.q().select("users.id", "posts.title")
```

### `.where(*conditions)`

Add conditions to an existing query:

```python
query = User.q(gt("age", 18))
query = query.where(eq("status", "active"))
query = query.where(not_null("email"))
users = await query
```

### `.where_raw(sql, params)`

Add raw SQL condition:

```python
users = await (User.q(gt("age", 18))
    .where_raw("jsonb_col @> $1", ['{"premium": true}'])
    .where_raw("created_at > NOW() - INTERVAL $1", ["30 days"]))
```

### `.order(*fields)`

Sort results. Prefix with `-` for descending:

```python
users = await User.q().order("name")                  # ASC
users = await User.q().order("-created_at")           # DESC
users = await User.q().order("-created_at", "name")   # Multi-column
```

### `.limit(n)` / `.offset(n)`

Limit and skip rows:

```python
users = await User.q().limit(10)
users = await User.q().limit(10).offset(20)  # Rows 21-30
```

### `.page(page, per_page=20)`

Convenient pagination:

```python
users = await User.q().page(1)              # First 20
users = await User.q().page(2)              # Rows 21-40
users = await User.q().page(1, per_page=50) # First 50
```

### `.include(*relationships)`

Eager load relationships:

```python
users = await User.q().include("posts")
users = await User.q().include("posts", "comments")
users = await User.q().include("posts.author")  # Nested
```

### `.distinct()`

Select unique rows:

```python
roles = await User.q().select("role").distinct()
```

### `.for_update()`

Lock rows (in transaction):

```python
async with db.transaction():
    user = await User.q(("id", "=", 1)).for_update().first()
    user.balance -= 100
    await user.save()
```

---

## Execution Methods

### `.all()` or `await query`

Get all matching rows:

```python
users = await User.q(gt("age", 18))       # Returns List[User]
users = await User.q(gt("age", 18)).all() # Same thing
```

### `.first()`

Get first row or `None`:

```python
user = await User.q(("id", "=", 1)).first()
if user:
    print(user.name)
```

### `.one()`

Get exactly one row (raises if 0 or 2+):

```python
try:
    user = await User.q(("email", "=", email)).one()
except NotFoundError:
    print("User not found")
except MultipleResultsError:
    print("Multiple users with same email!")
```

### `.count()`

Count matching rows:

```python
active_count = await User.q(eq("status", "active")).count()
```

### `.exists()`

Check if any rows match:

```python
if await User.q(("email", "=", email)).exists():
    raise ValueError("Email already taken")
```

### `.delete()`

Delete matching rows:

```python
deleted = await User.q(("status", "=", "deleted")).delete()
print(f"Deleted {deleted} users")
```

### `.update(**fields)`

Update matching rows:

```python
updated = await User.q(("status", "=", "pending")).update(status="active")
print(f"Activated {updated} users")
```

---

## SQL Escape Hatches

Four levels for when the builder isn't enough:

### Level 1: SQL String in `.q()`

```python
# Simple SQL conditions
users = await User.q("custom_func(data) > $1", 10)
users = await User.q("jsonb_col @> $1::jsonb", '{"key": "value"}')
```

### Level 2: Raw SQL (Returns Dicts)

```python
from pynext.db import db

rows = await db.sql('''
    SELECT u.*, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
    GROUP BY u.id
    HAVING COUNT(o.id) > $1
''', 10)

for row in rows:
    print(row["name"], row["order_count"])
```

### Level 3: Raw SQL with Model Mapping

```python
users = await User.sql('''
    SELECT * FROM users
    WHERE id IN (
        SELECT user_id FROM orders
        WHERE total > $1
    )
''', 1000)  # Returns List[User]!
```

### Level 4: Hybrid (Builder + Raw)

```python
users = await (User.q(gt("age", 18))
    .where_raw("jsonb_col @> $1", ['{"premium": true}'])
    .where(eq("status", "active"))
    .order("-created_at"))
```

---

## Parallel Execution

### Why Parallel?

```python
# Sequential: ~0.45ms (queries run one after another)
user = await User.q(("id", "=", user_id)).first()
orders = await Order.q(("user_id", "=", user_id))
notifications = await Notification.q(("user_id", "=", user_id))

# Parallel: ~0.20ms (2.25x faster!)
user, orders, notifications = await QueryBuilder.parallel(
    User.q(("id", "=", user_id)),
    Order.q(("user_id", "=", user_id)),
    Notification.q(("user_id", "=", user_id)),
)
```

### Method 1: `QueryBuilder.parallel()`

```python
from pynext.db import QueryBuilder

users, posts, orders = await QueryBuilder.parallel(
    User.q(gt("age", 18)),
    Post.q(eq("published", True)),
    Order.q(gt("total", 100)),
)
```

### Method 2: `QueryBuilder.batch()`

```python
async with QueryBuilder.batch() as b:
    users_q = b.add(User.q(gt("age", 18)))
    posts_q = b.add(Post.q(eq("published", True)))

# Access results after context exits
users = users_q.result
posts = posts_q.result
```

### When to Use Parallel

| Scenario | Use Parallel? | Why |
|----------|---------------|-----|
| Dashboard with 5 widgets | ✅ Yes | Independent queries |
| User + orders + notifications | ✅ Yes | Independent queries |
| Get user, then their posts | ❌ No | Posts depend on user.id |
| Single API with 1 query | ❌ No | No benefit |

**See [Parallel Execution Guide](./29-parallel-execution.md) for complete documentation.**

---

## Debugging

### `.explain()`

Get human-readable query explanation:

```python
query = User.q(gt("age", 18)).select("id", "name").order("-created_at")
print(query.explain())
# SELECT FROM users
#   columns: id, name
#   where: (age > 18)
#   order: created_at DESC
```

### `.to_dict()`

Get AST as dictionary:

```python
ast = User.q(gt("age", 18)).to_dict()
# {"table": "users", "type": "SELECT", "conditions": {...}}
```

### Logging

```python
import logging
logging.getLogger("pynext.db").setLevel(logging.DEBUG)

# Now see all queries:
# DEBUG:pynext.db:Executing: SELECT * FROM users WHERE age > $1
# DEBUG:pynext.db:Params: [18]
# DEBUG:pynext.db:Duration: 0.15ms
```

---

## Common Patterns

### Pagination with Total

```python
async def get_users_paginated(page: int, per_page: int = 20):
    base = User.q(eq("status", "active"))
    
    total, users = await QueryBuilder.parallel(
        base.count(),
        base.order("-created_at").page(page, per_page),
    )
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page
    }
```

### Search Across Multiple Fields

```python
async def search_users(query: str):
    return await User.q(
        or_(
            contains("name", query),
            contains("email", query),
            contains("bio", query),
        )
    ).order("-created_at").limit(50)
```

### Complex Filters

```python
async def find_premium_admins():
    return await User.q(
        and_(
            eq("role", "admin"),
            or_(
                eq("plan", "premium"),
                gt("credits", 1000)
            ),
            not_null("verified_at")
        )
    ).include("permissions")
```

### Conditional Query Building

```python
async def search(filters: dict):
    query = User.q()
    
    if "min_age" in filters:
        query = query.where(gte("age", filters["min_age"]))
    
    if "status" in filters:
        query = query.where(eq("status", filters["status"]))
    
    if "search" in filters:
        query = query.where(contains("name", filters["search"]))
    
    return await query.order("-created_at").page(filters.get("page", 1))
```

---

## DataFrame Output Methods

The QueryBuilder supports direct conversion to DataFrames and arrays for analytics.

### Available Methods

| Method | Returns | Best For |
|--------|---------|----------|
| `.to_polars()` | `polars.DataFrame` | Analytics, ML (zero-copy) |
| `.to_pandas()` | `pandas.DataFrame` | Data exploration |
| `.to_numpy()` | `dict[str, ndarray]` | Vectorized operations |
| `.to_numpy_structured()` | `numpy.ndarray` (structured) | Row iteration |
| `.to_dicts()` | `list[dict]` | JSON APIs |
| `.to_list()` | `list[tuple]` | Simple iteration |

### Examples

```python
# Polars DataFrame (zero-copy, 2-3x faster than asyncpg)
df = await User.q(("age", ">", 18)).to_polars()
result = df.filter(pl.col("status") == "active").group_by("role").count()

# pandas DataFrame
df = await User.q().select("id", "name", "score").order("-score").to_pandas()
print(df.describe())

# NumPy column-wise (zero-copy for numeric columns)
arrays = await User.q(("active", "=", True)).to_numpy()
mean_score = np.mean(arrays["score"])
high_scorers = arrays["id"][arrays["score"] > 90]

# NumPy structured (row iteration)
arr = await User.q().to_numpy_structured()
for row in arr:
    print(f"{row['name']}: {row['score']}")

# List of dicts (for JSON API responses)
rows = await User.q(("status", "=", "active")).to_dicts()
return {"users": rows}
```

### Performance Comparison

| Method | 100K rows | vs asyncpg |
|--------|-----------|------------|
| `.to_polars()` | ~150ms | **3x faster** |
| `.to_pandas()` | ~200ms | **2.25x faster** |
| `.to_numpy()` | ~180ms | **2.5x faster** |
| `.to_dicts()` | ~300ms | **1.5x faster** |

**Full documentation**: [DataFrame Integration](./30-dataframe-integration.md)

---

## Performance Tips

1. **Use `.select()`** - Only fetch columns you need
2. **Use `.page()`** - Don't fetch all rows
3. **Use `parallel()`** - For 2+ independent queries
4. **Use indexed columns in `.order()`** - Faster sorting
5. **Put selective conditions first** - Go optimizer helps
6. **Avoid `SELECT *`** - Specify columns
7. **Use `.exists()` not `.count() > 0`** - Faster existence check
8. **Use `.first()` not `[0]`** - Adds LIMIT 1
9. **Use `.to_polars()` for analytics** - Zero-copy, 2-3x faster
10. **Use `.to_dicts()` for JSON APIs** - Direct serialization

---

## Related Documentation

- [DataFrame Integration](./30-dataframe-integration.md) - Polars, NumPy, pandas output
- [Parallel Execution Complete Guide](./29-parallel-execution.md)
- [Query Security](./27-query-security.md)
- [Query Builder Internals](./28-query-internals.md)
- [Go Bridge Deep Dive](./25-gobridge-internals.md)
