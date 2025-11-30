# PostgreSQL Adapter

The PostgreSQL adapter provides production-ready database connectivity with automatic connection pooling, statement caching, and type-safe operations.

## Quick Start (30 Seconds)

```python
from pynext.db import PostgresAdapter, configure_db, Table

# 1. Connect (one line)
adapter = PostgresAdapter("postgresql://user:pass@localhost/mydb")
await adapter.connect()
configure_db(adapter)

# 2. Define models
class User(Table):
    name: str
    email: str
    age: int = 0

# 3. Use them
user = await User.insert(name="John", email="john@example.com")
users = await User.all()
```

## Configuration Options

### Connection URL

The simplest way to configure:

```python
adapter = PostgresAdapter("postgresql://user:pass@localhost:5432/mydb")
```

**URL Format:**
```
postgresql://[user[:password]@][host][:port]/database[?options]
```

**Supported schemes:** `postgresql://` and `postgres://`

### Keyword Arguments

For explicit configuration:

```python
adapter = PostgresAdapter(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="secret",
    ssl=True,
)
```

### Mixed (URL + Overrides)

Override specific parts of the URL:

```python
adapter = PostgresAdapter(
    url="postgresql://user@localhost/mydb",
    password=os.environ["DB_PASSWORD"],  # Override password
)
```

## Auto-Scaling Connection Pool

The adapter automatically manages a connection pool that scales based on demand.

### How It Works

```
                    ┌─────────────────────────────────────┐
                    │         Auto-Scaling Pool            │
                    │                                     │
Requests ──────────►│  min=1 ◄───── Active ─────► max=100│
                    │         Connections                 │
                    │                                     │
                    │  • Grows on demand                  │
                    │  • Shrinks when idle                │
                    │  • Never exceeds max                │
                    └─────────────────────────────────────┘
```

### Pool Configuration

```python
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    
    # Pool sizing
    min_connections=5,      # Keep 5 connections warm
    max_connections=100,    # Scale up to 100 under load
    auto_scale=True,        # Enable auto-scaling (default)
    
    # Connection lifecycle
    idle_timeout=300.0,     # Close idle connections after 5 min
    max_lifetime=3600.0,    # Replace connections after 1 hour
    
    # Timeouts
    connect_timeout=10.0,   # 10s to establish connection
    command_timeout=30.0,   # 30s per query
    acquire_timeout=30.0,   # 30s to get a connection from pool
)
```

### Scaling Behavior

| Scenario | Behavior |
|----------|----------|
| Low traffic | Pool stays at `min_connections` |
| Spike | Pool grows instantly (up to max) |
| Sustained load | Pool stays at current size |
| Traffic drops | Idle connections closed after `idle_timeout` |

## Statement Caching

Prepared statements are cached for 10-30% faster repeated queries.

### How It Works

1. **First execution:** PostgreSQL parses SQL, creates plan
2. **Cache stores:** Prepared statement with SQL as key
3. **Subsequent:** Skip parsing, reuse cached statement
4. **LRU eviction:** When cache is full, oldest statements removed

### Configuration

```python
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    statement_cache_size=1000,  # Cache 1000 statements (default)
)
```

### Memory Usage

- Each statement uses ~1-10KB
- Default 1000 statements ≈ 1-10MB
- Adjust based on unique query count

## Type Conversion

Automatic conversion between Python and PostgreSQL types:

| Python Type | PostgreSQL Type | Notes |
|-------------|-----------------|-------|
| `int` | `INTEGER` | Auto-detects size |
| `float` | `DOUBLE PRECISION` | 64-bit |
| `str` | `TEXT` | Unlimited length |
| `bool` | `BOOLEAN` | True/False |
| `datetime` | `TIMESTAMPTZ` | Always timezone-aware |
| `date` | `DATE` | Date only |
| `time` | `TIME` | Time only |
| `bytes` | `BYTEA` | Binary data |
| `list` | `ARRAY` / `JSONB` | Based on content |
| `dict` | `JSONB` | JSON with indexing |
| `Decimal` | `NUMERIC` | Exact decimal |
| `UUID` | `UUID` | UUID type |

### Timezone Handling

All naive datetimes are automatically converted to UTC:

```python
from datetime import datetime

# Naive datetime (no timezone)
dt = datetime(2024, 1, 15, 12, 30, 0)

# Stored as TIMESTAMPTZ with UTC
await User.insert(name="John", created_at=dt)
# Stored as: 2024-01-15 12:30:00+00:00
```

## Raw SQL

For complex queries, use raw SQL:

```python
# Execute (returns status)
await adapter.execute("UPDATE users SET active = true WHERE id = $1", (1,))

# Fetch all rows
users = await adapter.fetch_all(
    "SELECT * FROM users WHERE age > $1", 
    (18,)
)

# Fetch one row
user = await adapter.fetch_one(
    "SELECT * FROM users WHERE id = $1", 
    (1,)
)
```

**Note:** PostgreSQL uses `$1`, `$2`, etc. for parameters (not `?`).

## Transactions

### Basic Transaction

```python
await adapter.begin_transaction()
try:
    await User.insert(name="John")
    await Post.insert(title="Hello", author_id=1)
    await adapter.commit_transaction()
except Exception:
    await adapter.rollback_transaction()
    raise
```

### With Context Manager (via Table)

```python
from pynext.db import transaction

async with transaction():
    await User.insert(name="John")
    await Post.insert(title="Hello")
    # Auto-commits on success
    # Auto-rollbacks on exception
```

### Savepoints

For partial rollbacks:

```python
await adapter.begin_transaction()

await User.insert(name="John")
await adapter.savepoint("before_post")

try:
    await Post.insert(title="Hello")
except Exception:
    await adapter.rollback_savepoint("before_post")
    # User still inserted

await adapter.commit_transaction()
```

### Isolation Levels

```python
await adapter.begin_transaction(isolation="serializable")
# Options: read_committed, repeatable_read, serializable
```

## Monitoring

### Pool Statistics

```python
stats = adapter.get_pool_stats()

print(f"Connections: {stats.busy}/{stats.size}")
print(f"Idle: {stats.idle}")
print(f"Waiting: {stats.waiting}")
print(f"Utilization: {stats.busy / stats.size * 100:.1f}%")
```

### Available Metrics

| Metric | Description |
|--------|-------------|
| `size` | Current pool size |
| `idle` | Idle connections |
| `busy` | Active connections |
| `waiting` | Requests waiting |
| `total_acquires` | Total connection requests |
| `total_releases` | Total releases |
| `total_timeouts` | Acquire timeouts |

## Error Handling

### Connection Errors

```python
from pynext.db import ConnectionError

try:
    await adapter.connect()
except ConnectionError as e:
    print(f"Failed to connect: {e}")
```

### Pool Exhausted

When all connections are busy and max is reached:

```python
from pynext.db.adapters.postgres_pool import PoolExhaustedError

try:
    async with adapter.acquire() as conn:
        await conn.execute("SELECT 1")
except PoolExhaustedError:
    print("Pool exhausted - consider increasing max_connections")
```

### Query Errors

```python
from pynext.db import QueryError

try:
    await adapter.execute("INVALID SQL")
except QueryError as e:
    print(f"Query failed: {e}")
```

## Best Practices

### 1. Connection Lifecycle

```python
# ✅ Good: Connect once at startup
adapter = PostgresAdapter("postgresql://localhost/mydb")
await adapter.connect()
configure_db(adapter)

# Use throughout application...

# Disconnect on shutdown
await adapter.disconnect()
```

### 2. Pool Sizing

```python
# ✅ Good: Size based on workload
adapter = PostgresAdapter(
    url="...",
    min_connections=5,    # Keep warm connections
    max_connections=50,   # Don't overwhelm DB
)

# ❌ Bad: Oversized pool
adapter = PostgresAdapter(
    url="...",
    max_connections=1000,  # Too many!
)
```

### 3. Use Models Over Raw SQL

```python
# ✅ Preferred: Type-safe, auto-escaping
users = await User.select().where(role="admin").all()

# ⚠️ Use sparingly: Raw SQL
users = await adapter.fetch_all(
    "SELECT * FROM users WHERE role = $1",
    ("admin",)
)
```

### 4. Transactions for Related Operations

```python
# ✅ Good: Atomic operations
async with transaction():
    user = await User.insert(name="John")
    await Profile.insert(user_id=user.id, bio="...")

# ❌ Bad: Non-atomic
user = await User.insert(name="John")
await Profile.insert(user_id=user.id, bio="...")  # Could fail!
```

## Troubleshooting

### "Connection refused"

```
ConnectionError: Failed to connect to PostgreSQL
```

**Solutions:**
1. Check PostgreSQL is running: `pg_isready`
2. Verify host/port are correct
3. Check firewall rules

### "Pool exhausted"

```
PoolExhaustedError: Timeout waiting for connection
```

**Solutions:**
1. Increase `max_connections`
2. Increase `acquire_timeout`
3. Reduce query time
4. Check for connection leaks

### "Authentication failed"

```
ConnectionError: password authentication failed
```

**Solutions:**
1. Verify username/password
2. Check `pg_hba.conf` for auth method
3. Ensure user has access to database

### Slow Queries

**Solutions:**
1. Add indexes on filtered columns
2. Use `EXPLAIN ANALYZE` to debug
3. Check statement cache hit rate:

```python
# Get cache stats per connection
from pynext.db.adapters import StatementCache
# Check stats.hit_rate
```

## API Reference

### PostgresAdapter

```python
class PostgresAdapter:
    def __init__(
        self,
        url: str = None,
        *,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        ssl: bool = None,
        min_connections: int = 1,
        max_connections: int = 10,
        auto_scale: bool = True,
        idle_timeout: float = 300.0,
        max_lifetime: float = 3600.0,
        acquire_timeout: float = 30.0,
        statement_cache_size: int = 1000,
        connect_timeout: float = 10.0,
        command_timeout: float = None,
    ):
        """Create a PostgreSQL adapter."""
    
    async def connect(self) -> None:
        """Connect to PostgreSQL."""
    
    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
    
    async def execute(self, sql: str, params: tuple = None) -> Any:
        """Execute raw SQL."""
    
    async def fetch_all(self, sql: str, params: tuple = None) -> List[Dict]:
        """Fetch all rows."""
    
    async def fetch_one(self, sql: str, params: tuple = None) -> Optional[Dict]:
        """Fetch one row."""
    
    async def begin_transaction(self, isolation: str = None) -> None:
        """Begin a transaction."""
    
    async def commit_transaction(self) -> None:
        """Commit the transaction."""
    
    async def rollback_transaction(self) -> None:
        """Rollback the transaction."""
    
    async def savepoint(self, name: str) -> None:
        """Create a savepoint."""
    
    async def rollback_savepoint(self, name: str) -> None:
        """Rollback to a savepoint."""
    
    def get_pool_stats(self) -> Optional[PoolStats]:
        """Get pool statistics."""
```

### PostgresConfig

```python
@dataclass
class PostgresConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    user: str = "postgres"
    password: Optional[str] = None
    ssl: bool = False
    ssl_mode: str = "prefer"
    application_name: str = "pynext"
    
    @classmethod
    def from_url(cls, url: str, **overrides) -> "PostgresConfig":
        """Create config from URL."""
    
    def to_dsn(self) -> str:
        """Convert to DSN string."""
    
    def to_asyncpg_kwargs(self) -> Dict[str, Any]:
        """Convert to asyncpg kwargs."""
```

### AutoScalingPool

```python
class AutoScalingPool:
    async def start(self) -> None:
        """Start the pool."""
    
    async def close(self) -> None:
        """Close the pool."""
    
    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Connection]:
        """Acquire a connection."""
    
    def get_stats(self) -> PoolStats:
        """Get pool statistics."""
```

### StatementCache

```python
class StatementCache:
    async def get_or_prepare(
        self, 
        connection: Connection, 
        sql: str
    ) -> PreparedStatement:
        """Get cached or prepare new statement."""
    
    async def invalidate(self, sql: str) -> bool:
        """Invalidate a cached statement."""
    
    async def invalidate_all(self) -> int:
        """Invalidate all statements."""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
```

