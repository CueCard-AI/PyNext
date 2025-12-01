# PyNext Database Documentation

Welcome to the PyNext Database Layer documentation. This guide covers everything you need to build data-driven Python web applications - from basic concepts to production-scale deployments.

## 📚 Documentation Overview

```
                    PyNext Database Layer
═══════════════════════════════════════════════════════════════════════════

    BEGINNER                    INTERMEDIATE                   ADVANCED
    ────────                    ────────────                   ────────

    ┌────────────────┐         ┌────────────────┐         ┌────────────────┐
    │ 1. Fundamentals│         │ 3. Migrations  │         │ 6. Reliability │
    │    ORM basics, │         │    Schema      │         │    Retry,      │
    │    CRUD, types │         │    changes     │         │    circuit     │
    └───────┬────────┘         └───────┬────────┘         │    breaker     │
            │                          │                   └───────┬────────┘
            ▼                          ▼                           │
    ┌────────────────┐         ┌────────────────┐                  ▼
    │ 2. Getting     │         │ 4. PostgreSQL  │         ┌────────────────┐
    │    Started     │         │    Adapter     │         │ 7. High-Load   │
    │    Connect to  │         │    Complete    │         │    Scaling,    │
    │    PostgreSQL  │         │    guide       │         │    caching     │
    └───────┬────────┘         └───────┬────────┘         └───────┬────────┘
            │                          │                           │
            └──────────────────────────┼───────────────────────────┘
                                       │
                                       ▼
                              ┌────────────────┐
                              │ 5. Connection  │
                              │    Pooling     │
                              │    Advanced    │
                              │    pool config │
                              └───────┬────────┘
                                      │
                          ┌───────────┴───────────┐
                          ▼                       ▼
                 ┌────────────────┐      ┌────────────────┐
                 │ 8. Observability│      │ 9. Advanced   │
                 │    Metrics,    │      │    Queries    │
                 │    logging     │      │    Timeout,   │
                 └────────────────┘      │    EXPLAIN    │
                                         └───────┬────────┘
                                                 │
                                                 ▼
                                        ┌────────────────┐
                                        │ 10. Supabase  │
                                        │     Auth,     │
                                        │     Storage,  │
                                        │     Realtime  │
                                        └────────────────┘
```

---

## 🚀 Quick Start

### The Fastest Path

```python
from pynext.db import Table, configure
from pynext.db.adapters import PostgresAdapter

# 1. Define your model (that's it - no boilerplate!)
class User(Table):
    name: str
    email: str
    age: int = 0

# 2. Connect to database
adapter = PostgresAdapter("postgresql://localhost/mydb")
await adapter.connect()
configure(adapter)

# 3. Use it!
user = await User.insert(name="Alice", email="alice@example.com", age=25)
users = await User.where(age__gte=18).all()
```

### Choose Your Learning Path

| If you want to... | Start here |
|-------------------|------------|
| Learn database basics from scratch | [01-fundamentals.md](./01-fundamentals.md) |
| Connect to PostgreSQL quickly | [02-getting-started.md](./02-getting-started.md) |
| Manage schema changes | [03-migrations.md](./03-migrations.md) |
| Master PostgreSQL features | [04-postgres-adapter.md](./04-postgres-adapter.md) |
| Handle production load | [05-connection-pooling.md](./05-connection-pooling.md) |
| Build reliable systems | [06-reliability.md](./06-reliability.md) |
| Scale under high load | [07-high-load.md](./07-high-load.md) |
| Monitor and debug | [08-observability.md](./08-observability.md) |
| Optimize queries | [09-advanced-queries.md](./09-advanced-queries.md) |
| Integrate Supabase | [10-supabase.md](./10-supabase.md) |

---

## 📖 Documentation Guide

### [01. Fundamentals](./01-fundamentals.md)
**Start here if you're new to databases or ORMs**

Learn the core concepts from first principles:
- What databases are and why we need them
- How PyNext's ORM works
- Defining tables with Python type hints
- CRUD operations (Create, Read, Update, Delete)
- Query building and filtering
- Relationships between tables
- Validation and data quality
- Transactions

```python
# You'll learn to write this:
class User(Table):
    name: str
    email: str = Field(unique=True)
    posts: List["Post"] = Relationship()

user = await User.insert(name="Alice", email="alice@example.com")
posts = await user.posts.all()
```

---

### [02. Getting Started with PostgreSQL](./02-getting-started.md)
**Connect to a real PostgreSQL database**

Learn how to:
- Set up PostgreSQL (local or cloud)
- Connect using URLs or keyword arguments
- Understand connection URLs
- Configure SSL/TLS for security
- Handle connection lifecycle

```python
# Local development
adapter = PostgresAdapter("postgresql://localhost/mydb")

# Production with SSL
adapter = PostgresAdapter(
    url=os.environ["DATABASE_URL"],
    ssl=True,
)
```

---

### [03. Migrations](./03-migrations.md)
**Manage database schema changes safely**

Learn how to:
- Generate migrations automatically
- Write declarative and Python migrations
- Apply and rollback changes
- Handle complex schema evolution
- Use the migration CLI

```python
# Auto-generate migrations from model changes
pynext db migrate "add user profile fields"

# Apply migrations
pynext db upgrade

# Rollback if needed
pynext db downgrade
```

---

### [04. PostgreSQL Adapter - Complete Guide](./04-postgres-adapter.md)
**~2000 lines of comprehensive documentation**

The definitive guide to PyNext's PostgreSQL adapter:
- First-principles explanations
- Connection configuration
- All Phase 5 features integrated
- Production patterns
- Troubleshooting guide

```python
# Everything you need, with sensible defaults
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    # Auto-enabled: pooling, retries, circuit breaker, 
    # query coalescing, slow query logging
)
```

---

### [05. Connection Pooling](./05-connection-pooling.md)
**Deep dive into connection management**

Learn how to:
- Understand why pooling matters
- Configure pool size for your workload
- Use connection warmup
- Handle queue management
- Integrate with external poolers (PgBouncer)

```python
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    min_connections=5,      # Always ready
    max_connections=50,     # Peak capacity
    warmup=True,            # Pre-warm connections
)
```

---

### [06. Reliability](./06-reliability.md)
**Build fault-tolerant database connections**

Learn how to:
- Configure automatic retries
- Use circuit breakers
- Set up read replicas
- Handle graceful degradation

```python
# Automatic retry with exponential backoff
result = await adapter.with_retry(
    lambda: risky_operation(),
    max_attempts=5,
)

# Circuit breaker protection
if adapter.is_circuit_open:
    return cached_response()
```

---

### [07. High-Load Optimization](./07-high-load.md)
**Scale to handle thousands of requests per second**

Learn how to:
- Use query coalescing (dedupe identical queries)
- Batch operations efficiently
- Implement adaptive pool scaling
- Pipeline queries for throughput

```python
# 1000 users request same data = 1 database query
result = await adapter.coalesce(
    "SELECT * FROM popular_products LIMIT 10"
)

# Insert 10,000 rows efficiently
await adapter.batch_insert("users", rows, batch_size=500)
```

---

### [08. Observability](./08-observability.md)
**Monitor, log, and debug your database layer**

Learn how to:
- Configure structured logging
- Detect slow queries automatically
- Export metrics to Prometheus/OpenTelemetry
- Detect connection leaks

```python
# Get slow query suggestions
for query in adapter.get_slow_queries():
    print(f"{query.duration_ms}ms: {query.sql}")
    for suggestion in query.suggestions:
        print(f"  💡 {suggestion}")
```

---

### [09. Advanced Queries](./09-advanced-queries.md)
**~2000 lines of query optimization techniques**

Learn how to:
- Set per-query timeouts
- Use EXPLAIN/ANALYZE for optimization
- Implement efficient pagination
- Use prepared statements
- Cancel queries on disconnect

```python
# Per-query timeout
async with adapter.timeout(10):
    result = await slow_query()

# Understand why a query is slow
plan = await adapter.explain(query, analyze=True)
print(plan.tree)
print(plan.suggestions)

# Efficient pagination (O(1) at any page)
page = await adapter.paginate(query, cursor=cursor)
```

---

### [10. Supabase Integration](./10-supabase.md)
**Full integration with Supabase services**

Learn how to:
- Authenticate users (email, OAuth, magic links)
- Store and serve files
- Subscribe to real-time changes
- Manage Row Level Security
- Call Edge Functions

```python
from pynext.db.supabase import Supabase

sb = Supabase("https://xxx.supabase.co", "anon-key")

# Auth
user = await sb.auth.sign_in(email="...", password="...")

# Storage
url = await sb.storage.upload("avatars", file)

# Realtime
@sb.realtime.on_insert("messages")
async def handle_message(record):
    print(f"New message: {record['content']}")
```

---

## 🎯 Common Tasks Quick Reference

### CRUD Operations

```python
# Create
user = await User.insert(name="Alice", email="alice@example.com")

# Read
user = await User.get(1)                    # By ID
users = await User.all()                    # All records
users = await User.where(active=True).all() # Filtered

# Update
await user.update(name="Alice Smith")

# Delete
await user.delete()
```

### Querying

```python
# Filter
users = await User.where(age__gte=18, active=True).all()

# Sort
users = await User.order_by("created_at", desc=True).all()

# Limit
top_10 = await User.order_by("score", desc=True).limit(10).all()

# Pagination
page = await User.paginate(page_size=20, cursor=cursor)
```

### Transactions

```python
async with adapter.transaction():
    await Account.update(id=1, balance=balance - 100)
    await Account.update(id=2, balance=balance + 100)
    # Both succeed or both fail
```

### Raw SQL

```python
from pynext.db import sql

results = await sql("SELECT * FROM users WHERE age > $1", 18)
```

---

## 📊 Feature Comparison

### PyNext vs Other ORMs

| Feature | PyNext | SQLAlchemy | Prisma | Django ORM |
|---------|--------|------------|--------|------------|
| **Define with type hints** | ✅ | ❌ | ❌ | ❌ |
| **Async first** | ✅ | ⚠️ | ✅ | ❌ |
| **Auto-generate migrations** | ✅ | ⚠️ | ✅ | ✅ |
| **Connection pooling** | ✅ Built-in | ⚠️ | ✅ | ⚠️ |
| **Circuit breaker** | ✅ | ❌ | ❌ | ❌ |
| **Query coalescing** | ✅ | ❌ | ❌ | ❌ |
| **Per-query timeout** | ✅ | ❌ | ❌ | ❌ |
| **Prepared statements** | ✅ Auto | ⚠️ | ✅ | ❌ |
| **EXPLAIN with suggestions** | ✅ | ❌ | ❌ | ❌ |
| **Prometheus/OTEL metrics** | ✅ | ❌ | ❌ | ❌ |

### When to Use What

| Scenario | Recommended Approach |
|----------|---------------------|
| Simple CRUD | PyNext ORM (`User.insert()`, `User.get()`) |
| Complex queries | Query builder with `.where()`, `.join()` |
| Very complex SQL | Raw SQL with `sql()` |
| High performance | Prepared statements + query coalescing |
| Bulk operations | `batch_insert()`, `update_many()` |
| Real-time updates | Supabase Realtime integration |

---

## 🔗 Related Documentation

- [PyNext Core Documentation](../README.md)
- [API Routes](../data-server/API_ROUTES.md)
- [Server Actions](../data-server/SERVER_ACTIONS.md)
- [State Management](../core-concepts/STATE_MANAGEMENT.md)

---

## 📈 Test Coverage

The PyNext database layer is extensively tested:

| Phase | Tests | Coverage |
|-------|-------|----------|
| Phase 5.1: Core Adapter | 620 | URL, config, CRUD |
| Phase 5.2: Pooling | 500 | Queue, lifecycle, warmup |
| Phase 5.3: Reliability | 580 | Retry, circuit, replicas |
| Phase 5.4: High-Load | 600 | Coalesce, batch, scale |
| Phase 5.5: Observability | 600 | Logging, metrics, analysis |
| Phase 5.6: Supabase | 589 | Auth, storage, realtime |
| Phase 5.7: Advanced | 391 | Timeout, explain, pagination |
| **Total** | **4,275** | **Comprehensive** |

---

## 💡 Getting Help

1. **Check the documentation** - Most answers are in these docs
2. **Search existing issues** - Someone may have asked before
3. **Open an issue** - For bugs or feature requests
4. **Join Discord** - For real-time help

Remember: PyNext is designed to be **Python-first** and **AI-friendly**. When in doubt, write it the Python way!

