# PyNext Go Bridge - Complete Quickstart Guide

> **From Zero to 4x Faster Database Operations in 10 Minutes**
>
> This guide covers everything you need to know to use pynext-go effectively.

---

## Table of Contents

1. [Installation](#1-installation)
2. [Basic Setup](#2-basic-setup)
3. [Single Queries](#3-single-queries)
4. [Small Query Optimization](#4-small-query-optimization-execute_fast)
5. [Multi-Query Parallel Execution](#5-multi-query-parallel-execution)
6. [DataFrame Operations](#6-dataframe-operations)
7. [QueryBuilder API](#7-querybuilder-api)
8. [Async Support](#8-async-support)
9. [Performance Summary](#9-performance-summary)
10. [Decision Guide](#10-decision-guide-what-to-use-when)
11. [Complete Example](#11-complete-example-real-world-api)

---

## 1. Installation

### Prerequisites

```bash
# PostgreSQL 14+ running (via Docker or native)
docker run -d --name postgres -p 5432:5432 \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypass \
  -e POSTGRES_DB=mydb \
  postgres:16-alpine
```

### Install pynext-go

> **Note:** PyNext is not yet published to PyPI. Install from GitHub or source.

**Option A: Install from GitHub**
```bash
pip install git+https://github.com/CueCard-AI/PyNext.git

# Optional: DataFrame libraries
pip install pandas polars numpy pyarrow
```

**Option B: Install from source**
```bash
git clone https://github.com/CueCard-AI/PyNext.git
cd PyNext
pip install -e ".[dev]"

# Optional: DataFrame libraries
pip install pandas polars numpy pyarrow
```

**Coming Soon (PyPI):**
```bash
pip install pynext-go
```

### Verify Installation

```python
import pynext_go
print(pynext_go.__version__)  # Should print version
```

---

## 2. Basic Setup

### Initialize the Bridge

```python
import pynext_go

# Basic initialization
pynext_go.init("postgresql://myuser:mypass@localhost:5432/mydb")

# Your database operations here...

# Clean up when done (e.g., on app shutdown)
pynext_go.close()
```

### With Configuration Options

```python
pynext_go.init(
    "postgresql://user:pass@localhost:5432/mydb",
    # Optional settings (defaults shown):
    # pool_min=5,           # Minimum connections
    # pool_max=20,          # Maximum connections
    # query_timeout=30,     # Query timeout in seconds
)
```

### In a Web Framework (FastAPI)

```python
from fastapi import FastAPI
import pynext_go

app = FastAPI()

@app.on_event("startup")
async def startup():
    pynext_go.init("postgresql://user:pass@localhost:5432/mydb")

@app.on_event("shutdown")
async def shutdown():
    pynext_go.close()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    result = pynext_go.execute("SELECT * FROM users WHERE id = $1", [user_id])
    return result.rows[0] if result.rows else None
```

---

## 3. Single Queries

### Basic Execute

```python
import pynext_go

# SELECT with parameters
result = pynext_go.execute(
    "SELECT * FROM users WHERE status = $1 AND age > $2",
    ["active", 18]
)

# Access results
print(result.rows)        # List of dicts: [{"id": 1, "name": "Alice"}, ...]
print(result.row_count)   # Number of rows returned
print(result.columns)     # Column names: ["id", "name", "status", "age"]

# Get first row
if result.rows:
    user = result.rows[0]
    print(f"First user: {user['name']}")

# INSERT
result = pynext_go.execute(
    "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id",
    ["Alice", "alice@example.com"]
)
new_id = result.rows[0]["id"]

# UPDATE
result = pynext_go.execute(
    "UPDATE users SET status = $1 WHERE id = $2",
    ["inactive", 123]
)
print(f"Updated {result.row_count} rows")

# DELETE
result = pynext_go.execute(
    "DELETE FROM users WHERE last_login < $1",
    [datetime.now() - timedelta(days=365)]
)
```

### Parameter Types

```python
# Integers
pynext_go.execute("SELECT * FROM users WHERE id = $1", [42])

# Strings
pynext_go.execute("SELECT * FROM users WHERE name = $1", ["Alice"])

# Booleans
pynext_go.execute("SELECT * FROM users WHERE active = $1", [True])

# Dates/Timestamps
from datetime import datetime, date
pynext_go.execute("SELECT * FROM events WHERE date = $1", [date.today()])
pynext_go.execute("SELECT * FROM logs WHERE created_at > $1", [datetime.now()])

# Lists (for IN queries)
pynext_go.execute("SELECT * FROM users WHERE id = ANY($1)", [[1, 2, 3]])

# JSON
pynext_go.execute("SELECT * FROM users WHERE metadata @> $1", ['{"role": "admin"}'])

# NULL
pynext_go.execute("SELECT * FROM users WHERE deleted_at IS NULL")
```

---

## 4. Small Query Optimization (execute_fast)

For repeated small queries (like API endpoint lookups), use `execute_fast()` for **3.14x faster** performance:

```python
# Regular execute: ~0.95ms per query
result = pynext_go.execute("SELECT * FROM users WHERE id = $1", [user_id])

# execute_fast: ~0.30ms per query (3.14x faster!)
result = pynext_go.execute_fast("SELECT * FROM users WHERE id = $1", [user_id])
```

### When to Use execute_fast

✅ **Use execute_fast for:**
- Single-row lookups by ID
- Repeated small queries in hot paths
- API endpoint handlers

❌ **Don't use execute_fast for:**
- Large result sets (use execute_polars instead)
- One-off queries (overhead not worth it)
- Queries that return many rows

### Example: User Lookup API

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # execute_fast is perfect for single-row lookups
    result = pynext_go.execute_fast(
        "SELECT id, name, email FROM users WHERE id = $1",
        [user_id]
    )
    if not result.rows:
        raise HTTPException(404, "User not found")
    return result.rows[0]
```

---

## 5. Multi-Query Parallel Execution

When your endpoint needs multiple queries, use `batch()` or `execute_parallel()` for **~2x faster** execution:

### Using batch() (Recommended)

```python
# WITHOUT batch: ~5ms (sequential)
user = pynext_go.execute("SELECT * FROM users WHERE id = $1", [user_id])
orders = pynext_go.execute("SELECT * FROM orders WHERE user_id = $1", [user_id])
prefs = pynext_go.execute("SELECT * FROM preferences WHERE user_id = $1", [user_id])

# WITH batch: ~2.5ms (parallel) - 2x faster!
with pynext_go.batch() as b:
    user = b.query("SELECT * FROM users WHERE id = $1", [user_id])
    orders = b.query("SELECT * FROM orders WHERE user_id = $1", [user_id])
    prefs = b.query("SELECT * FROM preferences WHERE user_id = $1", [user_id])

# Results available after the 'with' block
return {
    "user": user.rows[0],
    "orders": orders.rows,
    "preferences": prefs.rows[0] if prefs.rows else {}
}
```

### Using execute_parallel()

For dynamic query lists:

```python
# Build query list dynamically
queries = [
    ("SELECT * FROM users WHERE id = $1", [user_id]),
    ("SELECT COUNT(*) FROM orders WHERE user_id = $1", [user_id]),
]

if include_notifications:
    queries.append(("SELECT * FROM notifications WHERE user_id = $1 LIMIT 5", [user_id]))

# Execute all in parallel
results = pynext_go.execute_parallel(queries)

user = results[0].rows[0]
order_count = results[1].rows[0]["count"]
notifications = results[2].rows if len(results) > 2 else []
```

### Real-World Example: Dashboard API

```python
@app.get("/dashboard/{user_id}")
async def get_dashboard(user_id: int):
    with pynext_go.batch() as b:
        # All these execute in parallel!
        user = b.query("SELECT * FROM users WHERE id = $1", [user_id])
        stats = b.query("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(total) as total_spent,
                AVG(total) as avg_order
            FROM orders WHERE user_id = $1
        """, [user_id])
        recent_orders = b.query("""
            SELECT * FROM orders 
            WHERE user_id = $1 
            ORDER BY created_at DESC LIMIT 5
        """, [user_id])
        notifications = b.query("""
            SELECT * FROM notifications 
            WHERE user_id = $1 AND read = false
            LIMIT 10
        """, [user_id])
    
    return {
        "user": user.rows[0],
        "stats": stats.rows[0],
        "recent_orders": recent_orders.rows,
        "unread_notifications": notifications.rows
    }
```

---

## 6. DataFrame Operations

For analytics and data processing, pynext-go is **4x faster** than asyncpg:

### Polars DataFrames (Fastest)

```python
import polars as pl

# Get data as Polars DataFrame (4x faster than asyncpg!)
df = pynext_go.execute_polars(
    "SELECT * FROM events WHERE timestamp > $1",
    [last_week]
)

# Now use Polars for fast analytics
result = (
    df
    .filter(pl.col("status") == "completed")
    .group_by("event_type")
    .agg([
        pl.count().alias("count"),
        pl.col("duration").mean().alias("avg_duration")
    ])
    .sort("count", descending=True)
)

print(result)
```

### pandas DataFrames

```python
import pandas as pd

# Get data as pandas DataFrame
df = pynext_go.execute_pandas(
    "SELECT * FROM sales WHERE date >= $1",
    [start_date]
)

# pandas operations
print(df.describe())
print(df.groupby("product_id")["amount"].sum())
```

### NumPy Arrays (Column-wise)

```python
import numpy as np

# Get data as dict of NumPy arrays
arrays = pynext_go.execute_numpy(
    "SELECT id, score, value FROM metrics WHERE active = true"
)

# Vectorized operations (fast!)
mean_score = np.mean(arrays["score"])
high_scorers = arrays["id"][arrays["score"] > 90]
normalized = (arrays["value"] - np.mean(arrays["value"])) / np.std(arrays["value"])
```

### NumPy Structured Arrays (Row-wise)

```python
# Get data as structured NumPy array
arr = pynext_go.execute_numpy_structured(
    "SELECT id, name, score FROM users ORDER BY score DESC LIMIT 100"
)

# Access by field name
print(arr["name"])  # All names
print(arr["score"])  # All scores

# Access by row
print(arr[0])  # First row: (1, 'Alice', 98.5)

# Iterate over rows
for row in arr:
    print(f"{row['name']}: {row['score']}")
```

### Async DataFrame Operations

```python
# All DataFrame methods have async versions
df = await pynext_go.execute_polars_async("SELECT * FROM large_table")
df = await pynext_go.execute_pandas_async("SELECT * FROM events")
arrays = await pynext_go.execute_numpy_async("SELECT * FROM metrics")
```

---

## 7. QueryBuilder API

For type-safe queries without writing SQL:

### Basic Usage

```python
from pynext.db import Table

class User(Table):
    __table_name__ = "users"

# Simple queries
users = await User.q().all()                    # SELECT * FROM users
user = await User.q().first()                   # SELECT * FROM users LIMIT 1
count = await User.q().count()                  # SELECT COUNT(*) FROM users
exists = await User.q().exists()                # SELECT EXISTS(...)
```

### Filtering with Conditions

```python
# Tuple syntax (most readable)
users = await User.q(("status", "=", "active")).all()
users = await User.q(("age", ">", 18)).all()
users = await User.q(("role", "IN", ["admin", "moderator"])).all()

# Multiple conditions (implicit AND)
users = await User.q(
    ("status", "=", "active"),
    ("age", ">", 18)
).all()

# Function syntax
from pynext.db.conditions import eq, gt, in_, and_, or_

users = await User.q(gt("age", 18)).all()
users = await User.q(in_("role", ["admin", "mod"])).all()

# Complex conditions
users = await User.q(
    and_(
        gt("age", 18),
        or_(eq("role", "admin"), eq("role", "moderator"))
    )
).all()
```

### Chaining Methods

```python
# Build complex queries with chaining
users = await (
    User.q(("status", "=", "active"))
    .select("id", "name", "email")
    .where(("created_at", ">", last_month))
    .order("-created_at")  # Descending
    .limit(10)
    .offset(20)
    .all()
)

# Pagination helper
page1 = await User.q().page(1, per_page=20)
page2 = await User.q().page(2, per_page=20)
```

### DataFrame Output

```python
# Get results directly as DataFrames
df = await User.q(("age", ">", 18)).to_polars()
df = await User.q(("status", "=", "active")).to_pandas()
arrays = await User.q().select("id", "score").to_numpy()

# Chain with aggregation
df = await User.q(("status", "=", "active")).to_polars()
summary = df.group_by("plan").agg(pl.count())
```

### Raw SQL Escape Hatches

```python
# When you need custom SQL
users = await User.q().where_raw("age > $1 AND score < $2", [18, 100]).all()

# Full raw query
result = pynext_go.execute("SELECT * FROM users WHERE custom_function(col) = $1", [value])
```

---

## 8. Async Support

All methods have async versions for use with FastAPI, asyncio, etc:

```python
import asyncio
import pynext_go

async def main():
    pynext_go.init("postgresql://...")
    
    # Async single query
    result = await pynext_go.execute_async("SELECT * FROM users")
    
    # Async execute_fast
    result = await pynext_go.execute_fast_async("SELECT * FROM users WHERE id = $1", [1])
    
    # Async parallel
    results = await pynext_go.execute_parallel_async([
        ("SELECT * FROM users", []),
        ("SELECT * FROM orders", []),
    ])
    
    # Async DataFrames
    df = await pynext_go.execute_polars_async("SELECT * FROM events")
    df = await pynext_go.execute_pandas_async("SELECT * FROM events")
    
    pynext_go.close()

asyncio.run(main())
```

### With FastAPI

```python
from fastapi import FastAPI
import pynext_go

app = FastAPI()

@app.get("/users")
async def get_users():
    result = await pynext_go.execute_async("SELECT * FROM users LIMIT 100")
    return result.rows

@app.get("/analytics")
async def get_analytics():
    df = await pynext_go.execute_polars_async("SELECT * FROM events")
    summary = df.group_by("type").agg(pl.count()).to_dicts()
    return {"summary": summary}
```

---

## 9. Performance Summary

### Measured Benchmarks

| Operation | asyncpg | pynext-go | Speedup |
|-----------|---------|-----------|---------|
| **Small query (single row)** | 0.95ms | 0.30ms | **3.14x faster** |
| **3 queries (API endpoint)** | 1.38ms | 0.70ms | **1.96x faster** |
| **10 queries (complex API)** | 5.05ms | 2.57ms | **1.97x faster** |
| **DataFrame 100K rows** | 219ms | 50ms | **4.4x faster** |
| **DataFrame 500K rows** | 1156ms | 269ms | **4.3x faster** |
| **DataFrame 1M rows** | 2191ms | 500ms | **4.4x faster** |

### Why pynext-go is Faster

1. **No GIL**: Go executes queries truly in parallel
2. **Zero-copy Arrow**: Data transfer without Python iteration
3. **Connection pinning**: Reuse connections for repeated queries
4. **Native serialization**: Go handles all data conversion

---

## 10. Decision Guide: What to Use When

```
What are you doing?
│
├── Single small query (1 row)?
│   └── Use execute_fast() → 3.14x faster
│
├── Multiple independent queries?
│   ├── 2-5 queries? → Use batch() → ~2x faster
│   └── 5+ queries? → Use execute_parallel() → ~2x faster
│
├── Loading data for analysis?
│   ├── Using Polars? → Use execute_polars() → 4x faster
│   ├── Using pandas? → Use execute_pandas() → 4x faster
│   └── Using NumPy? → Use execute_numpy() → 3x faster
│
├── Building dynamic queries?
│   └── Use QueryBuilder: User.q(conditions).all()
│
└── Just need raw SQL?
    └── Use execute() or execute_async()
```

### Quick Reference Table

| Use Case | Method | Example |
|----------|--------|---------|
| Single row by ID | `execute_fast()` | `execute_fast("SELECT * FROM users WHERE id = $1", [id])` |
| API with 3+ queries | `batch()` | `with batch() as b: ...` |
| Dynamic query list | `execute_parallel()` | `execute_parallel(queries)` |
| Analytics (Polars) | `execute_polars()` | `execute_polars("SELECT * FROM events")` |
| Analytics (pandas) | `execute_pandas()` | `execute_pandas("SELECT * FROM events")` |
| Vectorized ops | `execute_numpy()` | `execute_numpy("SELECT x, y FROM data")` |
| Type-safe queries | `QueryBuilder` | `User.q(("age", ">", 18)).all()` |

---

## 11. Complete Example: Real-World API

Here's a complete FastAPI application showcasing all features:

```python
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import pynext_go
import polars as pl

app = FastAPI(title="User Dashboard API")

# =============================================================================
# Startup/Shutdown
# =============================================================================

@app.on_event("startup")
async def startup():
    pynext_go.init("postgresql://user:pass@localhost:5432/mydb")

@app.on_event("shutdown") 
async def shutdown():
    pynext_go.close()

# =============================================================================
# Single Query Endpoints (use execute_fast)
# =============================================================================

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get single user - uses execute_fast for 3x speed."""
    result = pynext_go.execute_fast(
        "SELECT id, name, email, created_at FROM users WHERE id = $1",
        [user_id]
    )
    if not result.rows:
        raise HTTPException(404, "User not found")
    return result.rows[0]

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    """Get single order - uses execute_fast for 3x speed."""
    result = pynext_go.execute_fast(
        "SELECT * FROM orders WHERE id = $1",
        [order_id]
    )
    if not result.rows:
        raise HTTPException(404, "Order not found")
    return result.rows[0]

# =============================================================================
# Multi-Query Endpoints (use batch)
# =============================================================================

@app.get("/users/{user_id}/dashboard")
async def get_user_dashboard(user_id: int):
    """User dashboard - uses batch() for 2x speed with parallel queries."""
    
    with pynext_go.batch() as b:
        user = b.query(
            "SELECT id, name, email FROM users WHERE id = $1",
            [user_id]
        )
        stats = b.query("""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total), 0) as total_spent,
                COALESCE(AVG(total), 0) as avg_order
            FROM orders 
            WHERE user_id = $1
        """, [user_id])
        recent_orders = b.query("""
            SELECT id, total, status, created_at 
            FROM orders 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT 5
        """, [user_id])
        notifications = b.query("""
            SELECT id, message, created_at 
            FROM notifications 
            WHERE user_id = $1 AND read = false 
            ORDER BY created_at DESC 
            LIMIT 10
        """, [user_id])
    
    if not user.rows:
        raise HTTPException(404, "User not found")
    
    return {
        "user": user.rows[0],
        "stats": stats.rows[0],
        "recent_orders": recent_orders.rows,
        "unread_notifications": notifications.rows
    }

# =============================================================================
# Analytics Endpoints (use DataFrames)
# =============================================================================

@app.get("/analytics/sales")
async def get_sales_analytics(days: int = 30):
    """Sales analytics - uses Polars for 4x faster data processing."""
    
    since = datetime.now() - timedelta(days=days)
    
    # Load data as Polars DataFrame (4x faster than asyncpg!)
    df = await pynext_go.execute_polars_async(
        "SELECT product_id, quantity, total, created_at FROM orders WHERE created_at > $1",
        [since]
    )
    
    # Fast Polars aggregations
    by_product = (
        df
        .group_by("product_id")
        .agg([
            pl.count().alias("order_count"),
            pl.sum("quantity").alias("total_quantity"),
            pl.sum("total").alias("total_revenue"),
            pl.mean("total").alias("avg_order_value")
        ])
        .sort("total_revenue", descending=True)
        .head(10)
    )
    
    daily_revenue = (
        df
        .with_columns(pl.col("created_at").dt.date().alias("date"))
        .group_by("date")
        .agg(pl.sum("total").alias("revenue"))
        .sort("date")
    )
    
    return {
        "top_products": by_product.to_dicts(),
        "daily_revenue": daily_revenue.to_dicts(),
        "summary": {
            "total_orders": len(df),
            "total_revenue": df["total"].sum(),
            "avg_order_value": df["total"].mean()
        }
    }

@app.get("/analytics/users/activity")
async def get_user_activity(days: int = 7):
    """User activity analytics - uses NumPy for vectorized calculations."""
    
    since = datetime.now() - timedelta(days=days)
    
    # Load as NumPy arrays for fast vectorized ops
    arrays = await pynext_go.execute_numpy_async(
        "SELECT user_id, action_count, session_duration FROM user_activity WHERE date > $1",
        [since]
    )
    
    import numpy as np
    
    return {
        "total_users": len(np.unique(arrays["user_id"])),
        "avg_actions_per_user": float(np.mean(arrays["action_count"])),
        "avg_session_duration": float(np.mean(arrays["session_duration"])),
        "most_active_users": arrays["user_id"][np.argsort(arrays["action_count"])[-10:]].tolist()
    }

# =============================================================================
# QueryBuilder Examples
# =============================================================================

from pynext.db import Table
from pynext.db.conditions import gt, eq, in_

class User(Table):
    __table_name__ = "users"

class Order(Table):
    __table_name__ = "orders"

@app.get("/users/active")
async def get_active_users(min_orders: int = 5):
    """Get active users using QueryBuilder."""
    
    users = await User.q(
        ("status", "=", "active"),
        ("order_count", ">=", min_orders)
    ).select("id", "name", "email", "order_count").order("-order_count").limit(100).all()
    
    return users

@app.get("/orders/pending")
async def get_pending_orders():
    """Get pending orders as DataFrame for processing."""
    
    df = await Order.q(
        ("status", "=", "pending"),
        ("created_at", ">", datetime.now() - timedelta(days=7))
    ).to_polars()
    
    return {
        "count": len(df),
        "total_value": df["total"].sum(),
        "orders": df.to_dicts()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Next Steps

- **Deep Dive**: [Go Bridge Internals](./25-gobridge-internals.md) - How it works under the hood
- **Benchmarks**: [Benchmark Methodology](./31-benchmark-methodology.md) - Detailed performance data
- **DataFrames**: [DataFrame Integration](./30-dataframe-integration.md) - Complete DataFrame guide
- **QueryBuilder**: [Query Builder Guide](./26-query-builder.md) - Type-safe queries
- **Parallel Execution**: [Parallel Execution](./29-parallel-execution.md) - batch() deep dive

---

## Troubleshooting

### "Go bridge not initialized"

```python
# Always call init() before using any pynext_go function
pynext_go.init("postgresql://...")
```

### Connection errors

```python
# Check your connection string
pynext_go.init("postgresql://USER:PASSWORD@HOST:PORT/DATABASE")

# Common issues:
# - Wrong port (PostgreSQL default is 5432)
# - Password with special characters (URL encode them)
# - Database doesn't exist
```

### Slow performance

```python
# Are you using the right method?
# Small queries → execute_fast()
# Multiple queries → batch()
# DataFrames → execute_polars()

# Not this:
for id in ids:
    result = pynext_go.execute("SELECT * FROM users WHERE id = $1", [id])

# Do this:
for id in ids:
    result = pynext_go.execute_fast("SELECT * FROM users WHERE id = $1", [id])

# Or even better:
queries = [("SELECT * FROM users WHERE id = $1", [id]) for id in ids]
results = pynext_go.execute_parallel(queries)
```

