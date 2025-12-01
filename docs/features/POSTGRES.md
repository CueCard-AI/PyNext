# PostgreSQL Adapter

## Table of Contents

1. [Introduction: Why PostgreSQL?](#introduction-why-postgresql)
2. [Chapter 1: What is PostgreSQL?](#chapter-1-what-is-postgresql)
3. [Chapter 2: Connecting to PostgreSQL](#chapter-2-connecting-to-postgresql)
4. [Chapter 3: Connection URLs Explained](#chapter-3-connection-urls-explained)
5. [Chapter 4: Connection Pooling Basics](#chapter-4-connection-pooling-basics)
6. [Chapter 5: Statement Caching](#chapter-5-statement-caching)
7. [Chapter 6: Type Mapping](#chapter-6-type-mapping)
8. [Chapter 7: Production Configuration](#chapter-7-production-configuration)
9. [Chapter 8: SSL and Security](#chapter-8-ssl-and-security)
10. [Quick Reference](#quick-reference)
11. [Related Documentation](#related-documentation)

---

## Introduction: Why PostgreSQL?

### The Database Landscape

There are many databases. Why does PyNext focus on PostgreSQL?

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DATABASE OPTIONS                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  SQLite         PostgreSQL        MySQL           MongoDB           │
│  ──────         ──────────        ─────           ───────           │
│  • File-based   • Full-featured   • Popular       • Document DB     │
│  • Great for    • Production-     • Good for      • No SQL          │
│    prototyping    ready             web apps                        │
│  • No server    • Advanced        • Simpler       • Flexible        │
│    needed         features          than Postgres   schema          │
│                                                                      │
│  PyNext uses:                                                        │
│  ─────────────                                                       │
│  • SQLite for development/testing (MemoryAdapter)                   │
│  • PostgreSQL for production (PostgresAdapter)                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Why PostgreSQL for Production?

| Feature | Why It Matters |
|---------|----------------|
| **ACID Compliance** | Data consistency - never lose or corrupt data |
| **Advanced Types** | JSON, arrays, UUIDs, time ranges, geo types |
| **Full-Text Search** | Built-in search without external service |
| **Extensions** | PostGIS (geo), pgvector (AI), TimescaleDB (time-series) |
| **Reliability** | Battle-tested for 35+ years |
| **Scalability** | Handles billions of rows, read replicas, sharding |
| **Free & Open** | No licensing costs, strong community |

### PyNext + PostgreSQL

PyNext's PostgreSQL adapter provides:

- **Simple connection** - One line to connect
- **Automatic pooling** - Efficient connection management
- **Statement caching** - Faster repeated queries
- **Type safety** - Python types ↔ PostgreSQL types
- **Production features** - Retries, circuit breakers, replicas

---

## Chapter 1: What is PostgreSQL?

### The Basics

**PostgreSQL** (often called "Postgres") is an open-source relational database. It stores data in tables with rows and columns, and you query it with SQL.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HOW POSTGRESQL WORKS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    Your App                     PostgreSQL Server                    │
│    ────────                     ─────────────────                    │
│                                                                      │
│    Python code     ──────►      Port 5432                           │
│    (PyNext)          SQL        ├── Databases                       │
│                      ↓          │   ├── myapp_dev                   │
│                      │          │   ├── myapp_prod                  │
│    Results        ◄──┘          │   └── myapp_test                  │
│    (Python dicts)               │                                   │
│                                 └── Each database has:               │
│                                     ├── Tables                       │
│                                     ├── Indexes                      │
│                                     ├── Users/Roles                  │
│                                     └── Extensions                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Server** | The PostgreSQL process | Running on localhost:5432 |
| **Database** | A named collection of data | `myapp_production` |
| **Schema** | Namespace within database | `public` (default) |
| **Table** | Collection of rows | `users`, `posts` |
| **Role/User** | Access credentials | `myapp_user` |

### Local vs Cloud PostgreSQL

**Local (Development):**
```bash
# Install on macOS
brew install postgresql@16
brew services start postgresql@16

# Install on Ubuntu
sudo apt install postgresql

# Default connection
postgresql://localhost:5432/postgres
```

**Cloud (Production):**
- **Supabase** - Free tier, generous limits
- **Neon** - Serverless, scales to zero
- **Railway** - Simple deployment
- **AWS RDS** - Enterprise scale
- **Heroku** - Easy setup

---

## Chapter 2: Connecting to PostgreSQL

### The Simplest Connection

```python
from pynext.db import configure_db
from pynext.db.adapters import PostgresAdapter

# One line to connect!
adapter = PostgresAdapter("postgresql://user:password@localhost:5432/mydb")
await adapter.connect()
configure_db(adapter)

# Now use your models
from myapp.models import User
users = await User.all()
```

### Connection Methods

#### Method 1: URL String

```python
# Full URL with all parts
adapter = PostgresAdapter(
    "postgresql://myuser:mypassword@db.example.com:5432/mydb?sslmode=require"
)
```

#### Method 2: Keyword Arguments

```python
# Explicit parameters
adapter = PostgresAdapter(
    host="db.example.com",
    port=5432,
    database="mydb",
    user="myuser",
    password="mypassword",
    ssl=True,
)
```

#### Method 3: Environment Variable

```python
import os

# Common pattern: use DATABASE_URL env var
adapter = PostgresAdapter(os.environ["DATABASE_URL"])

# Or with fallback
adapter = PostgresAdapter(
    os.environ.get("DATABASE_URL", "postgresql://localhost:5432/mydb")
)
```

#### Method 4: Mixed (URL + Overrides)

```python
# Start with URL, override specific parts
adapter = PostgresAdapter(
    url="postgresql://user@localhost:5432/mydb",
    password=os.environ["DB_PASSWORD"],  # Keep password in env
    ssl=True,  # Force SSL
)
```

### Connection Lifecycle

```python
from pynext.db.adapters import PostgresAdapter

# Create adapter (doesn't connect yet)
adapter = PostgresAdapter("postgresql://localhost/mydb")

# Connect (establishes connection pool)
await adapter.connect()

# Use the database...
# (your app runs)

# Disconnect (closes all connections)
await adapter.disconnect()
```

### Context Manager (Recommended)

```python
async with PostgresAdapter("postgresql://localhost/mydb") as adapter:
    configure_db(adapter)
    
    # Use database
    users = await User.all()
    
# Automatically disconnects when block exits
```

### Complete Example

```python
import asyncio
from pynext.db import configure_db, Table
from pynext.db.adapters import PostgresAdapter

# Define your model
class User(Table):
    name: str
    email: str

async def main():
    # Connect
    adapter = PostgresAdapter("postgresql://localhost:5432/myapp")
    await adapter.connect()
    configure_db(adapter)
    
    try:
        # Create a user
        user = await User.insert(name="Alice", email="alice@example.com")
        print(f"Created user: {user.id}")
        
        # Query users
        all_users = await User.all()
        print(f"Total users: {len(all_users)}")
        
    finally:
        # Always disconnect
        await adapter.disconnect()

asyncio.run(main())
```

---

## Chapter 3: Connection URLs Explained

### URL Anatomy

```
postgresql://user:password@host:port/database?options
─────────── ──── ──────── ──── ──── ──────── ───────
     │        │      │      │    │      │       │
     │        │      │      │    │      │       └── Query parameters
     │        │      │      │    │      └── Database name
     │        │      │      │    └── Port (default: 5432)
     │        │      │      └── Server hostname or IP
     │        │      └── Password (URL-encoded if special chars)
     │        └── Username
     └── Scheme (postgresql:// or postgres://)
```

### URL Examples

```python
# Local development (no auth)
"postgresql://localhost/mydb"

# Local with user/password
"postgresql://myuser:mypass@localhost:5432/mydb"

# Cloud database with SSL
"postgresql://user:pass@db.cloud.com:5432/mydb?sslmode=require"

# Unix socket (local, fast)
"postgresql:///mydb?host=/var/run/postgresql"

# Multiple hosts (for failover)
"postgresql://host1,host2,host3/mydb?target_session_attrs=primary"
```

### Special Characters in Passwords

If your password contains special characters, URL-encode them:

```python
import urllib.parse

# Password with special characters: my@pass!word
password = urllib.parse.quote("my@pass!word")
url = f"postgresql://user:{password}@localhost/mydb"
# Result: postgresql://user:my%40pass%21word@localhost/mydb
```

Common encodings:
| Character | Encoded |
|-----------|---------|
| `@` | `%40` |
| `:` | `%3A` |
| `/` | `%2F` |
| `!` | `%21` |
| `#` | `%23` |
| `%` | `%25` |

### URL Query Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `sslmode` | `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full` | SSL mode |
| `connect_timeout` | seconds | Connection timeout |
| `application_name` | string | App name in pg_stat_activity |
| `options` | string | PostgreSQL options |

```python
# With multiple parameters
url = "postgresql://user:pass@host/db?sslmode=require&connect_timeout=10&application_name=myapp"
```

---

## Chapter 4: Connection Pooling Basics

### Why Pool Connections?

Opening a database connection is **expensive** (50-200ms). Pooling keeps connections open and reuses them:

```
Without pooling:              With pooling:
────────────────              ─────────────

Request 1:                    Request 1:
  Open connection (100ms)       Borrow from pool (0ms)
  Query (5ms)                   Query (5ms)
  Close connection              Return to pool

Request 2:                    Request 2:
  Open connection (100ms)       Borrow from pool (0ms)
  Query (5ms)                   Query (5ms)
  Close connection              Return to pool

Total: 210ms                  Total: 10ms (21x faster!)
```

### Default Pool Configuration

PyNext creates a connection pool automatically:

```python
# Default pool settings
adapter = PostgresAdapter(
    "postgresql://localhost/mydb",
    min_connections=5,   # Keep at least 5 connections ready
    max_connections=20,  # Allow up to 20 concurrent connections
)
```

### Pool Sizing Guidelines

| Application Size | Min | Max | Notes |
|------------------|-----|-----|-------|
| Development | 1 | 5 | Low traffic |
| Small app | 5 | 20 | < 100 req/sec |
| Medium app | 10 | 50 | 100-1000 req/sec |
| Large app | 20 | 100+ | > 1000 req/sec |

**Formula for max_connections:**
```
max_connections = (CPU cores × 2) + effective_spindle_count

For a 4-core machine with SSD:
max_connections = (4 × 2) + 1 = 9

But most cloud databases limit to 100-500 total connections.
```

### Pool Statistics

```python
# Get pool stats
stats = await adapter.pool_stats()
print(f"Pool size: {stats['size']}")
print(f"In use: {stats['in_use']}")
print(f"Available: {stats['available']}")
print(f"Waiting: {stats['waiting']}")
```

For detailed pooling documentation, see [POOLING.md](./POOLING.md).

---

## Chapter 5: Statement Caching

### What is Statement Caching?

PostgreSQL can **prepare** SQL statements for reuse. This saves parsing time on repeated queries:

```
First execution:                 Subsequent executions:
────────────────                 ──────────────────────

Query: SELECT * FROM users       Query: SELECT * FROM users
  ↓                               ↓
Parse SQL (1ms)                  Use cached plan (0ms) ← Skip parsing!
  ↓                               ↓
Plan query (1ms)                 Execute (5ms)
  ↓
Execute (5ms)

Total: 7ms                       Total: 5ms (30% faster!)
```

### Automatic Caching

PyNext caches statements automatically:

```python
# This query is cached after first execution
for user_id in range(1000):
    user = await User.get(user_id)
    # First time: parse + plan + execute
    # Subsequent: just execute (cached plan)
```

### Cache Configuration

```python
adapter = PostgresAdapter(
    "postgresql://localhost/mydb",
    statement_cache_size=1000,  # Cache up to 1000 prepared statements
)
```

### When Caching Helps

✅ **Great for:**
- Repeated queries with different parameters
- CRUD operations (insert, select, update, delete)
- Hot paths in your application

❌ **Doesn't help:**
- Dynamic SQL (different structure each time)
- One-off queries
- Very complex queries (planning time > cache benefit)

---

## Chapter 6: Type Mapping

### Python to PostgreSQL

PyNext maps Python types to PostgreSQL types automatically:

| Python | PostgreSQL | Example |
|--------|------------|---------|
| `str` | `TEXT` | `"hello"` |
| `int` | `INTEGER` | `42` |
| `float` | `DOUBLE PRECISION` | `3.14` |
| `bool` | `BOOLEAN` | `True` |
| `datetime` | `TIMESTAMPTZ` | `datetime.now()` |
| `date` | `DATE` | `date.today()` |
| `time` | `TIME` | `time(12, 30)` |
| `timedelta` | `INTERVAL` | `timedelta(days=1)` |
| `Decimal` | `NUMERIC` | `Decimal("99.99")` |
| `bytes` | `BYTEA` | `b"binary"` |
| `UUID` | `UUID` | `uuid.uuid4()` |
| `dict` | `JSONB` | `{"key": "value"}` |
| `list` | `JSONB` | `[1, 2, 3]` |
| `list[int]` | `INTEGER[]` | `[1, 2, 3]` |
| `list[str]` | `TEXT[]` | `["a", "b"]` |
| `Optional[T]` | `T` (nullable) | `None` |

### PostgreSQL-Specific Types

```python
from pynext.db import Table
from pynext.db.types import (
    UUID,
    JSONB,
    Array,
    DateRange,
    TSVector,  # Full-text search
)

class Product(Table):
    # UUID primary key
    id: UUID = Field(default_factory=uuid.uuid4)
    
    # JSON data
    metadata: JSONB = {}
    
    # Array of tags
    tags: Array[str] = []
    
    # Full-text search vector
    search_vector: TSVector
    
    # Date range for availability
    available: DateRange
```

### Custom Type Converters

```python
from pynext.db.adapters import register_type_converter

# Custom Python class
class Money:
    def __init__(self, cents: int):
        self.cents = cents
    
    def __repr__(self):
        return f"${self.cents / 100:.2f}"

# Register converter
@register_type_converter(Money)
def convert_money(value):
    if isinstance(value, Money):
        return value.cents  # Python → PostgreSQL
    else:
        return Money(value)  # PostgreSQL → Python

# Now use in models
class Product(Table):
    price: Money
```

---

## Chapter 7: Production Configuration

### Basic Production Setup

```python
from pynext.db.adapters import PostgresAdapter

adapter = PostgresAdapter(
    # Connection
    url=os.environ["DATABASE_URL"],
    
    # Pool sizing
    min_connections=10,
    max_connections=50,
    
    # Timeouts
    connect_timeout=10,
    command_timeout=30,
    
    # SSL (always in production!)
    ssl=True,
)
```

### With Reliability Features

```python
adapter = PostgresAdapter(
    url=os.environ["DATABASE_URL"],
    
    # Enable all reliability features
    reliability=True,  # Retries, circuit breaker, graceful degradation
    
    # Pool
    min_connections=10,
    max_connections=50,
)
```

### With Read Replicas

```python
from pynext.db.adapters import PostgresAdapter, Replica

adapter = PostgresAdapter(
    # Primary (writes)
    primary=os.environ["PRIMARY_DATABASE_URL"],
    
    # Replicas (reads)
    replicas=[
        os.environ["REPLICA_1_URL"],
        os.environ["REPLICA_2_URL"],
    ],
    
    reliability=True,
)

# Writes automatically go to primary
await User.insert(name="Alice")

# Reads automatically go to replicas
users = await User.all()
```

### Full Production Example

```python
from pynext.db.adapters import PostgresAdapter, Replica, ReplicaConfig

adapter = PostgresAdapter(
    # Primary connection
    host=os.environ["DB_PRIMARY_HOST"],
    port=5432,
    database=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    ssl=True,
    
    # Replicas with weights
    replicas=ReplicaConfig(
        replicas=[
            Replica(
                host=os.environ["DB_REPLICA_1_HOST"],
                weight=2,  # Gets 2x traffic
            ),
            Replica(
                host=os.environ["DB_REPLICA_2_HOST"],
                weight=1,
            ),
        ],
        max_lag_seconds=5,  # Don't use replica if >5s behind
    ),
    
    # Pool configuration
    min_connections=20,
    max_connections=100,
    
    # Reliability
    reliability=True,
    
    # Timeouts
    connect_timeout=10,
    command_timeout=30,
)
```

See [RELIABILITY.md](./RELIABILITY.md) for complete reliability documentation.

---

## Chapter 8: SSL and Security

### Why SSL?

Without SSL, data travels in plain text:

```
Your App ────── Network ────── Database
           ↑
        Attacker can see:
        • Passwords
        • User data
        • Queries
```

With SSL, data is encrypted:

```
Your App ════════════════════ Database
           ↑
        Attacker sees:
        • Gibberish
```

### SSL Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `disable` | No SSL | Never (except local dev) |
| `allow` | Use SSL if available | Legacy systems |
| `prefer` | Try SSL, fall back to plain | Default |
| `require` | Require SSL, don't verify cert | Most production |
| `verify-ca` | Require SSL + verify CA | High security |
| `verify-full` | Require SSL + verify hostname | Maximum security |

### Configuring SSL

```python
# URL parameter
adapter = PostgresAdapter(
    "postgresql://user:pass@host/db?sslmode=require"
)

# Keyword argument
adapter = PostgresAdapter(
    host="db.example.com",
    ssl=True,  # Equivalent to sslmode=require
)

# With certificate verification
adapter = PostgresAdapter(
    host="db.example.com",
    ssl={
        "sslmode": "verify-full",
        "sslrootcert": "/path/to/ca-certificate.crt",
    }
)
```

### Security Best Practices

1. **Always use SSL in production**
   ```python
   ssl=True  # or sslmode=require
   ```

2. **Use environment variables for credentials**
   ```python
   password=os.environ["DB_PASSWORD"]  # Never hardcode!
   ```

3. **Use least-privilege database users**
   ```sql
   -- Create app user with minimal permissions
   CREATE USER myapp_user WITH PASSWORD 'secure_password';
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO myapp_user;
   ```

4. **Use connection limits**
   ```python
   max_connections=50  # Don't exhaust database connections
   ```

5. **Use timeouts**
   ```python
   connect_timeout=10,
   command_timeout=30,
   ```

---

## Quick Reference

### Minimal Connection

```python
from pynext.db import configure_db
from pynext.db.adapters import PostgresAdapter

adapter = PostgresAdapter("postgresql://localhost/mydb")
await adapter.connect()
configure_db(adapter)
```

### Production Connection

```python
adapter = PostgresAdapter(
    url=os.environ["DATABASE_URL"],
    ssl=True,
    min_connections=10,
    max_connections=50,
    reliability=True,
)
await adapter.connect()
configure_db(adapter)
```

### With Read Replicas

```python
adapter = PostgresAdapter(
    primary=os.environ["PRIMARY_URL"],
    replicas=[
        os.environ["REPLICA_1_URL"],
        os.environ["REPLICA_2_URL"],
    ],
    reliability=True,
)
```

### All Options

```python
adapter = PostgresAdapter(
    # Connection (choose one)
    url: str = None,                    # Full connection URL
    host: str = "localhost",            # Or individual parts
    port: int = 5432,
    database: str = None,
    user: str = "postgres",
    password: str = None,
    
    # SSL
    ssl: bool | dict = False,           # True or detailed config
    
    # Pool
    min_connections: int = 5,
    max_connections: int = 20,
    
    # Timeouts
    connect_timeout: float = 10.0,
    command_timeout: float = 30.0,
    
    # Statement cache
    statement_cache_size: int = 1000,
    
    # Reliability
    reliability: bool = False,          # Enable all reliability features
    
    # Replicas
    primary: str = None,                # Primary URL (for read replicas)
    replicas: list | ReplicaConfig = None,
)
```

---

## Related Documentation

| Topic | Document | Description |
|-------|----------|-------------|
| **Core Concepts** | [DATABASE.md](./DATABASE.md) | ORM basics, models, CRUD |
| **Schema Changes** | [MIGRATIONS.md](./MIGRATIONS.md) | Version-controlled migrations |
| **Connection Pool** | [POOLING.md](./POOLING.md) | Advanced pooling configuration |
| **Fault Tolerance** | [RELIABILITY.md](./RELIABILITY.md) | Retries, circuit breakers, replicas |
| **Performance** | [HIGH_LOAD.md](./HIGH_LOAD.md) | Caching, pipelining, scaling |
