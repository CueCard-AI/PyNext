# Go Bridge - High Performance Database Layer

The Go Bridge (`pynext_go`) is a Go-powered database execution engine that delivers **2-3x faster** database operations compared to asyncpg for real-world workloads. It achieves this through true parallelism, efficient serialization, and PostgreSQL's COPY protocol.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Why Go Bridge?](#why-go-bridge)
3. [Installation](#installation)
4. [API Reference](#api-reference)
   - [Initialization](#initialization)
   - [execute()](#execute)
   - [batch()](#batch---parallel-query-execution)
   - [execute_parallel()](#execute_parallel)
   - [execute_copy_df()](#execute_copy_df---dataframes)
   - [execute_arrow()](#execute_arrow)
5. [Performance Guide](#performance-guide)
6. [Best Practices](#best-practices)
7. [Error Handling](#error-handling)
8. [Configuration](#configuration)

---

## Quick Start

```python
import pynext_go

# Initialize the bridge
pynext_go.init(primary='postgresql://user:pass@localhost:5432/mydb')

# Single query
result = pynext_go.execute("SELECT * FROM users WHERE id = $1", [user_id])
print(result.rows)

# Multiple queries in parallel (2x faster!)
with pynext_go.batch() as b:
    user = b.query("SELECT * FROM users WHERE id = $1", [user_id])
    orders = b.query("SELECT * FROM orders WHERE user_id = $1", [user_id])
    notifications = b.query("SELECT * FROM notifications WHERE user_id = $1", [user_id])

# Results available after context exits
return {"user": user.rows, "orders": orders.rows, "notifications": notifications.rows}

# Cleanup
pynext_go.close()
```

---

## Why Go Bridge?

### The Problem with Python + PostgreSQL

Python's Global Interpreter Lock (GIL) prevents true parallel execution:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Python with asyncpg                          │
├─────────────────────────────────────────────────────────────────┤
│  Query 1: ────────────────────────▶                             │
│  Query 2:                          ────────────────────────▶    │
│  Query 3:                                                   ────│
│                                                                 │
│  Total time: Query1 + Query2 + Query3 (SEQUENTIAL)              │
└─────────────────────────────────────────────────────────────────┘
```

Even with `asyncio.gather()`, asyncpg cannot execute multiple queries on a single connection concurrently. Each query must wait for the previous one.

### The Go Bridge Solution

Go's goroutines bypass Python's GIL entirely:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Go Bridge (pynext_go)                       │
├─────────────────────────────────────────────────────────────────┤
│                         ┌─────────────────┐                     │
│  Python ───batch()────▶ │  Go Runtime     │                     │
│                         │                 │                     │
│                         │  goroutine 1 ───┼───▶ Query 1         │
│                         │  goroutine 2 ───┼───▶ Query 2         │
│                         │  goroutine 3 ───┼───▶ Query 3         │
│                         │                 │                     │
│                         │  (TRUE PARALLEL)│                     │
│                         └────────┬────────┘                     │
│                                  │                              │
│  Results ◀───────────────────────┘                              │
│                                                                 │
│  Total time: MAX(Query1, Query2, Query3) (PARALLEL!)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

> **Note:** PyNext is not yet published to PyPI. Install from GitHub or source.

```bash
# From GitHub
pip install git+https://github.com/CueCard-AI/PyNext.git

# Or from source
git clone https://github.com/CueCard-AI/PyNext.git
cd PyNext
pip install -e ".[dev]"
```

**Coming Soon (PyPI):**
```bash
pip install pynext-go
```

The package includes pre-built Go binaries for:
- Linux (amd64, arm64)
- macOS (amd64, arm64 / Apple Silicon)
- Windows (amd64)

### Verify Installation

```python
import pynext_go

print(f"Go available: {pynext_go.GO_AVAILABLE}")
print(f"Library path: {pynext_go.GO_LIBRARY_PATH}")
print(f"Version: {pynext_go.GoBridge.version()}")
```

---

## API Reference

### Initialization

```python
pynext_go.init(
    primary: str,                    # Required: Primary database URL
    replicas: list[str] = None,      # Optional: Read replica URLs
    pool_min_size: int = 2,          # Minimum connections in pool
    pool_max_size: int = 10,         # Maximum connections in pool
    query_timeout: int = 30000,      # Default query timeout (ms)
)
```

**Example:**

```python
pynext_go.init(
    primary='postgresql://user:pass@primary.db.com:5432/mydb',
    replicas=[
        'postgresql://user:pass@replica1.db.com:5432/mydb',
        'postgresql://user:pass@replica2.db.com:5432/mydb',
    ],
    pool_min_size=5,
    pool_max_size=20,
    query_timeout=60000,  # 60 seconds
)
```

---

### execute()

Execute a single query and return results.

```python
result = pynext_go.execute(
    sql: str,                        # SQL with $1, $2, ... placeholders
    params: list = None,             # Query parameters
    timeout_ms: int = None,          # Override default timeout
    use_replica: bool = False,       # Route to read replica
)
```

**Returns:** `QueryResult`

```python
result.rows        # List of rows (each row is a list)
result.columns     # List of column names
result.row_count   # Number of rows returned
result.duration    # Query duration in milliseconds
result.success     # Boolean success status
```

**Example:**

```python
# Simple query
result = pynext_go.execute("SELECT * FROM users WHERE active = $1", [True])
for row in result.rows:
    print(row)

# With timeout
result = pynext_go.execute(
    "SELECT * FROM large_table",
    timeout_ms=5000  # 5 second timeout
)

# Route to replica
result = pynext_go.execute(
    "SELECT * FROM analytics",
    use_replica=True
)
```

**Performance:** ~1x asyncpg (same speed for single queries)

---

### batch() - Parallel Query Execution

Execute multiple independent queries in parallel. **This is the key to 2x speedup.**

```python
with pynext_go.batch() as b:
    result1 = b.query(sql, params)
    result2 = b.query(sql, params)
    result3 = b.query(sql, params)
# All queries execute in parallel when context exits!
```

**Returns:** `DeferredResult` objects that are populated after the context exits.

**Example - API Endpoint:**

```python
def get_user_dashboard(user_id: int):
    """
    Typical dashboard endpoint - needs data from multiple tables.
    With asyncpg: 3 sequential queries = 0.45ms
    With batch(): 3 parallel queries = 0.20ms (2.25x faster!)
    """
    with pynext_go.batch() as b:
        user = b.query(
            "SELECT id, name, email, avatar FROM users WHERE id = $1",
            [user_id]
        )
        orders = b.query(
            "SELECT id, total, status, created_at FROM orders WHERE user_id = $1 ORDER BY created_at DESC LIMIT 10",
            [user_id]
        )
        notifications = b.query(
            "SELECT id, message, read, created_at FROM notifications WHERE user_id = $1 AND read = false LIMIT 20",
            [user_id]
        )
    
    # Results available here - all 3 ran in parallel
    return {
        "user": user.rows[0] if user.rows else None,
        "recent_orders": orders.rows,
        "unread_notifications": notifications.rows,
        "notification_count": notifications.row_count,
    }
```

**Example - E-commerce Product Page:**

```python
def get_product_page(product_id: int, user_id: int = None):
    """
    Product page needs: product, reviews, related, inventory, seller.
    5 queries × 0.15ms = 0.75ms with asyncpg
    5 queries parallel = 0.35ms with batch() (2.1x faster!)
    """
    with pynext_go.batch() as b:
        product = b.query(
            "SELECT * FROM products WHERE id = $1",
            [product_id]
        )
        reviews = b.query(
            "SELECT r.*, u.name as author FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.product_id = $1 ORDER BY r.created_at DESC LIMIT 20",
            [product_id]
        )
        related = b.query(
            "SELECT id, name, price, image FROM products WHERE category_id = (SELECT category_id FROM products WHERE id = $1) AND id != $1 LIMIT 8",
            [product_id]
        )
        inventory = b.query(
            "SELECT warehouse, quantity FROM inventory WHERE product_id = $1",
            [product_id]
        )
        seller = b.query(
            "SELECT s.* FROM sellers s JOIN products p ON s.id = p.seller_id WHERE p.id = $1",
            [product_id]
        )
    
    return {
        "product": product.rows[0],
        "reviews": reviews.rows,
        "related_products": related.rows,
        "inventory": inventory.rows,
        "seller": seller.rows[0] if seller.rows else None,
    }
```

**Async Usage:**

```python
async def get_dashboard_async(user_id: int):
    async with pynext_go.batch() as b:
        user = b.query("SELECT * FROM users WHERE id = $1", [user_id])
        orders = b.query("SELECT * FROM orders WHERE user_id = $1", [user_id])
    
    return {"user": user.rows, "orders": orders.rows}
```

**Performance by Query Count:**

| Queries | asyncpg (sequential) | batch() (parallel) | Speedup |
|---------|---------------------|-------------------|---------|
| 3       | 0.48ms              | 0.26ms            | 1.8x    |
| 5       | 0.81ms              | 0.39ms            | 2.1x    |
| 10      | 2.03ms              | 0.98ms            | 2.1x    |

---

### execute_parallel()

Lower-level parallel execution (batch() is built on this).

```python
results = pynext_go.execute_parallel([
    ("SELECT * FROM users WHERE id = $1", [1]),
    ("SELECT * FROM orders WHERE user_id = $1", [1]),
    ("SELECT COUNT(*) FROM products", []),
])

users, orders, product_count = results
```

---

### execute_copy_df() - DataFrames

**Fastest way to get data into a pandas DataFrame.** Uses PostgreSQL's COPY protocol.

```python
df = pynext_go.execute_copy_df(sql: str)
```

**Returns:** `pandas.DataFrame`

**Example:**

```python
# Analytics query - 10,000 rows
# asyncpg → DataFrame: 24.5ms
# execute_copy_df:      8.8ms (2.8x faster!)

df = pynext_go.execute_copy_df("""
    SELECT 
        date_trunc('day', created_at) as day,
        COUNT(*) as orders,
        SUM(total) as revenue
    FROM orders
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY 1
    ORDER BY 1
""")

# Ready for analysis
print(df.describe())
daily_avg = df['revenue'].mean()
```

**Performance by Row Count:**

| Rows   | asyncpg → DataFrame | execute_copy_df() | Speedup |
|--------|---------------------|-------------------|---------|
| 1,000  | 2.7ms               | 2.5ms             | 1.1x    |
| 5,000  | 11.0ms              | 4.8ms             | 2.3x    |
| 10,000 | 24.5ms              | 8.8ms             | 2.8x    |
| 50,000 | 120ms               | 40ms              | 3.0x    |

---

### execute_arrow()

Get results as a PyArrow Table (zero-copy transfer).

```python
table = pynext_go.execute_arrow(sql: str, params: list = None)
```

**Returns:** `pyarrow.Table`

**Example:**

```python
import pyarrow as pa

# Get data as Arrow table
table = pynext_go.execute_arrow("SELECT * FROM events LIMIT 100000")

# Zero-copy conversion to pandas
df = table.to_pandas()

# Or use directly with Arrow-compatible libraries
import polars as pl
df = pl.from_arrow(table)
```

---

## Performance Guide

### Decision Tree: Which Method to Use?

```
                        ┌─────────────────────────┐
                        │   What's your use case? │
                        └───────────┬─────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌──────────────┐    ┌───────────────┐    ┌─────────────────┐
       │  JSON API    │    │   DataFrame   │    │  Bulk Export    │
       │  Response    │    │   Analysis    │    │  / Streaming    │
       └──────┬───────┘    └───────┬───────┘    └────────┬────────┘
              │                    │                     │
              ▼                    ▼                     ▼
    ┌───────────────────┐  ┌──────────────┐    ┌─────────────────┐
    │ Multiple queries? │  │ >1000 rows?  │    │ execute_copy()  │
    └────────┬──────────┘  └──────┬───────┘    │   Raw bytes     │
             │                    │            └─────────────────┘
      ┌──────┴──────┐      ┌──────┴──────┐
      │ Yes   │ No  │      │ Yes   │ No  │
      ▼       ▼     │      ▼       ▼     │
  ┌────────┐ ┌──────┴┐ ┌──────────────┐ ┌┴─────────────┐
  │batch() │ │execute│ │execute_copy_ │ │execute_arrow │
  │ 2x ⚡  │ │  ()   │ │    df()      │ │     ()       │
  └────────┘ └───────┘ │   2-3x ⚡    │ └──────────────┘
                       └──────────────┘
```

### Summary Table

| Use Case | Method | Speedup vs asyncpg |
|----------|--------|-------------------|
| Single query (API) | `execute()` | ~1x (same) |
| Multi-query endpoint | `batch()` | **1.7-2.1x** |
| DataFrame (1k rows) | `execute_copy_df()` | 1.1x |
| DataFrame (5k+ rows) | `execute_copy_df()` | **2-3x** |
| Bulk data export | `execute_copy()` | **2.5-3x** |

---

## Best Practices

### 1. Use batch() for Multi-Query Endpoints

```python
# ❌ BAD: Sequential queries
def get_dashboard(user_id):
    user = pynext_go.execute("SELECT * FROM users WHERE id = $1", [user_id])
    orders = pynext_go.execute("SELECT * FROM orders WHERE user_id = $1", [user_id])
    stats = pynext_go.execute("SELECT COUNT(*) FROM notifications WHERE user_id = $1", [user_id])
    return {"user": user.rows, "orders": orders.rows, "stats": stats.rows}

# ✅ GOOD: Parallel queries
def get_dashboard(user_id):
    with pynext_go.batch() as b:
        user = b.query("SELECT * FROM users WHERE id = $1", [user_id])
        orders = b.query("SELECT * FROM orders WHERE user_id = $1", [user_id])
        stats = b.query("SELECT COUNT(*) FROM notifications WHERE user_id = $1", [user_id])
    return {"user": user.rows, "orders": orders.rows, "stats": stats.rows}
```

### 2. Use execute_copy_df() for Analytics

```python
# ❌ BAD: asyncpg → list → DataFrame (slow for large data)
async def get_analytics():
    result = await conn.fetch("SELECT * FROM events LIMIT 50000")
    df = pd.DataFrame([dict(r) for r in result])  # 120ms!

# ✅ GOOD: COPY → DataFrame (direct, fast)
def get_analytics():
    df = pynext_go.execute_copy_df("SELECT * FROM events LIMIT 50000")  # 40ms!
```

### 3. Warmup on Application Start

```python
# In your app startup
pynext_go.init(primary='postgresql://...')
pynext_go.warmup()  # Pre-establishes connections
```

### 4. Close on Shutdown

```python
# In your app shutdown
pynext_go.close()
```

---

## Error Handling

```python
from pynext_go import (
    BridgeError,           # Base error
    BridgeQueryError,      # Query execution failed
    BridgeTimeoutError,    # Query timed out
    BridgeConnectionError, # Connection failed
    BridgeConfigError,     # Configuration error
)

try:
    result = pynext_go.execute("SELECT * FROM users")
except BridgeTimeoutError:
    logger.error("Query timed out")
except BridgeQueryError as e:
    logger.error(f"Query failed: {e.message}")
except BridgeError as e:
    logger.error(f"Bridge error: {e}")
```

---

## Configuration

### Environment Variables

```bash
# Override library path
export PYNEXT_GO_LIB=/path/to/libpynext.so

# Enable debug logging
export PYNEXT_GO_DEBUG=1
```

### BridgeConfig Object

```python
from pynext_go import BridgeConfig, GoBridge

config = BridgeConfig(
    primary="postgresql://user:pass@localhost/db",
    replicas=["postgresql://user:pass@replica/db"],
    pool_min_size=5,
    pool_max_size=20,
    query_timeout=30000,
    pool_health_interval=10000,
)

bridge = GoBridge()
bridge.init(config)
```

---

## Health Checks

```python
health = pynext_go.health()

print(health.status)           # "healthy", "degraded", or "unhealthy"
print(health.primary.latency)  # Primary connection latency (ms)
print(health.pool.active)      # Active connections
print(health.pool.idle)        # Idle connections
```

---

## Migration from asyncpg

See [24-asyncpg-vs-gobridge.md](./24-asyncpg-vs-gobridge.md) for a complete migration guide.

---

## Technical Deep Dive

See [25-gobridge-internals.md](./25-gobridge-internals.md) for implementation details.
