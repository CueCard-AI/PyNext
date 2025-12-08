# asyncpg vs Go Bridge: Complete Comparison & Migration Guide

This document provides a comprehensive comparison between `asyncpg` (Python's fastest PostgreSQL driver) and `pynext_go` (Go Bridge), including when to use each, performance benchmarks, and migration patterns.

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Comparison](#architecture-comparison)
3. [Performance Benchmarks](#performance-benchmarks)
4. [When to Use What](#when-to-use-what)
5. [Migration Guide](#migration-guide)
6. [Code Comparison Examples](#code-comparison-examples)
7. [Gotchas & Limitations](#gotchas--limitations)

---

## Executive Summary

### Quick Comparison

| Feature | asyncpg | Go Bridge (pynext_go) |
|---------|---------|----------------------|
| **Single query speed** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Excellent (same) |
| **Multi-query speed** | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ 2x faster |
| **DataFrame speed** | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ 2-3x faster |
| **Bulk export speed** | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ 2.5-3x faster |
| **True parallelism** | ❌ GIL-limited | ✅ Via goroutines |
| **Async native** | ✅ Built for async | ⚠️ Async wrapper |
| **Connection per query** | ❌ Shares connection | ✅ Separate connections |
| **Ecosystem maturity** | ⭐⭐⭐⭐⭐ Battle-tested | ⭐⭐⭐ Newer |

### The Bottom Line

- **Use Go Bridge when:**
  - Your endpoints make 2+ database queries
  - You're building data pipelines with DataFrames
  - You need bulk data export
  - You're hitting Python GIL limitations

- **Keep asyncpg when:**
  - Single query per endpoint
  - You need maximum async ecosystem compatibility
  - Your queries are simple and fast

---

## Architecture Comparison

### asyncpg Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Python Process                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    asyncio Event Loop                         │   │
│  │  ┌────────────────────────────────────────────────────────┐   │   │
│  │  │                  asyncpg Connection                     │   │   │
│  │  │                                                         │   │   │
│  │  │   Query 1 ─────▶ wait ─────▶ result ─────▶             │   │   │
│  │  │                                           Query 2 ───▶  │   │   │
│  │  │                                                         │   │   │
│  │  │   ⚠️ Only ONE query can run at a time per connection    │   │   │
│  │  │   ⚠️ Python GIL blocks true parallelism                 │   │   │
│  │  └────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Total time for 3 queries: Q1 + Q2 + Q3 = 0.45ms                   │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Characteristics:**
- Runs entirely in Python
- Uses asyncio for I/O concurrency (not parallelism)
- One connection can only run one query at a time
- GIL prevents true CPU parallelism
- Excellent for I/O-bound single queries

### Go Bridge Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Python Process                             │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │   pynext_go.batch()                                           │  │
│  │         │                                                     │  │
│  │         │  ctypes FFI call                                    │  │
│  │         ▼                                                     │  │
│  │  ┌────────────────────────────────────────────────────────┐   │  │
│  │  │              Go Runtime (libpynext.so)                  │   │  │
│  │  │                                                         │   │  │
│  │  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │  │
│  │  │   │ goroutine 1 │  │ goroutine 2 │  │ goroutine 3 │    │   │  │
│  │  │   │   Query 1   │  │   Query 2   │  │   Query 3   │    │   │  │
│  │  │   │     ↓       │  │     ↓       │  │     ↓       │    │   │  │
│  │  │   │  Connection │  │  Connection │  │  Connection │    │   │  │
│  │  │   │     1       │  │     2       │  │     3       │    │   │  │
│  │  │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │   │  │
│  │  │          │                │                │           │   │  │
│  │  │          └────────────────┼────────────────┘           │   │  │
│  │  │                           │                            │   │  │
│  │  │                 Results collected                      │   │  │
│  │  │                                                         │   │  │
│  │  │   ✅ TRUE PARALLEL EXECUTION                           │   │  │
│  │  │   ✅ Each query has its own connection                 │   │  │
│  │  │   ✅ No GIL limitation                                 │   │  │
│  │  └────────────────────────────────────────────────────────┘   │  │
│  │         │                                                     │  │
│  │         ▼  Return to Python                                   │  │
│  │      Results                                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Total time for 3 queries: MAX(Q1, Q2, Q3) = 0.20ms                │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Characteristics:**
- Python calls into Go via FFI (ctypes)
- Go runtime handles true parallel execution
- Each query gets its own goroutine and connection
- No GIL limitation - real parallelism
- Results serialized back to Python

---

## Performance Benchmarks

All benchmarks run on:
- PostgreSQL 15 (local Docker)
- 100,000 row `orders` table
- 500 iterations for stability
- macOS Apple Silicon

### Single Query Performance

When you execute a single query, both libraries perform nearly identically:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Single Query Performance (SELECT * FROM orders LIMIT n)           │
├──────────────┬─────────────┬─────────────┬──────────────────────────┤
│    Rows      │   asyncpg   │  Go Bridge  │       Speedup            │
├──────────────┼─────────────┼─────────────┼──────────────────────────┤
│    100       │   0.36ms    │   0.36ms    │    1.0x (same)           │
│    500       │   0.81ms    │   0.80ms    │    1.0x (same)           │
│   1000       │   1.44ms    │   1.40ms    │    1.03x                 │
│   5000       │   7.10ms    │   6.81ms    │    1.04x                 │
└──────────────┴─────────────┴─────────────┴──────────────────────────┘
```

**Why?** For a single query, the bottleneck is network round-trip to PostgreSQL (~0.1ms). Both libraries are equally fast at this.

### Multi-Query Performance (The Big Win)

When your API endpoint makes multiple database calls, Go Bridge shines:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Multi-Query Performance (batch() vs sequential)                   │
├──────────────┬─────────────┬─────────────┬──────────────────────────┤
│   Queries    │   asyncpg   │   batch()   │       Speedup            │
├──────────────┼─────────────┼─────────────┼──────────────────────────┤
│     3        │   0.48ms    │   0.26ms    │  ⚡ 1.85x faster         │
│     5        │   0.81ms    │   0.39ms    │  ⚡ 2.08x faster         │
│    10        │   2.03ms    │   0.98ms    │  ⚡ 2.07x faster         │
└──────────────┴─────────────┴─────────────┴──────────────────────────┘
```

**Why?** asyncpg must run queries sequentially (one at a time). Go Bridge runs them all in parallel using goroutines.

### DataFrame Performance

When loading data into pandas DataFrames:

```
┌─────────────────────────────────────────────────────────────────────┐
│  DataFrame Performance (query → pandas DataFrame)                  │
├──────────────┬─────────────┬─────────────┬──────────────────────────┤
│    Rows      │   asyncpg   │ copy_df()   │       Speedup            │
├──────────────┼─────────────┼─────────────┼──────────────────────────┤
│   1,000      │   2.7ms     │   2.5ms     │    1.1x                  │
│   5,000      │  11.0ms     │   4.8ms     │  ⚡ 2.3x faster          │
│  10,000      │  24.5ms     │   8.8ms     │  ⚡ 2.8x faster          │
│  50,000      │  120ms      │   40ms      │  ⚡ 3.0x faster          │
└──────────────┴─────────────┴─────────────┴──────────────────────────┘
```

**Why?** Go Bridge uses PostgreSQL's COPY protocol which streams data efficiently, then pyarrow parses CSV blazingly fast.

### Bulk Export Performance

For raw data streaming/export:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Bulk Export Performance (COPY protocol)                           │
├──────────────┬─────────────┬─────────────┬──────────────────────────┤
│    Rows      │   asyncpg   │   copy()    │       Speedup            │
├──────────────┼─────────────┼─────────────┼──────────────────────────┤
│  10,000      │  12.3ms     │   4.9ms     │  ⚡ 2.5x faster          │
│  50,000      │  50.2ms     │  15.5ms     │  ⚡ 3.2x faster          │
│ 100,000      │  102ms      │  31ms       │  ⚡ 3.3x faster          │
└──────────────┴─────────────┴─────────────┴──────────────────────────┘
```

---

## When to Use What

### Use Go Bridge (pynext_go) When:

#### ✅ Your API endpoints make multiple database queries

Most real-world endpoints need data from multiple tables:

```python
# Dashboard: user + orders + notifications + stats
# Product page: product + reviews + related + inventory + seller
# Checkout: cart + user + shipping + payment methods

# All of these benefit from batch()
with pynext_go.batch() as b:
    # All queries run in parallel - 2x faster
    ...
```

#### ✅ You're building data pipelines with DataFrames

```python
# Analytics, reporting, ML feature engineering
df = pynext_go.execute_copy_df("SELECT * FROM events WHERE date > '2024-01-01'")
```

#### ✅ You need bulk data export

```python
# Data dumps, ETL, backups
csv_data = pynext_go.execute_copy("SELECT * FROM large_table")
```

#### ✅ You're hitting Python GIL limitations

If you're running multiple database-heavy tasks and seeing CPU underutilization, Go Bridge's true parallelism helps.

### Keep asyncpg When:

#### ✅ Single query per endpoint

```python
# Simple CRUD endpoints with one query
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
```

For single queries, asyncpg and Go Bridge are equally fast. Stick with asyncpg for ecosystem familiarity.

#### ✅ You need deep async ecosystem integration

If you're using asyncpg with SQLAlchemy async, encode/databases, or other async ORMs, stick with asyncpg for compatibility.

#### ✅ Transactions with complex logic

asyncpg's transaction context managers are more Pythonic:

```python
async with conn.transaction():
    await conn.execute("UPDATE accounts SET balance = balance - $1 WHERE id = $2", amount, from_id)
    # Python logic here
    await conn.execute("UPDATE accounts SET balance = balance + $1 WHERE id = $2", amount, to_id)
```

#### ✅ You need connection-level features

- Prepared statements with explicit management
- LISTEN/NOTIFY
- Streaming large results row-by-row
- Custom type codecs

---

## Migration Guide

### Step 1: Add Go Bridge alongside asyncpg

```python
# Don't remove asyncpg yet - run them side by side
import asyncpg
import pynext_go

# Initialize both
pool = await asyncpg.create_pool(...)
pynext_go.init(primary='postgresql://...')
```

### Step 2: Identify multi-query endpoints

Find endpoints that make 2+ queries:

```python
# Before: Sequential queries
async def get_dashboard(user_id: int):
    user = await conn.fetch("SELECT * FROM users WHERE id = $1", user_id)
    orders = await conn.fetch("SELECT * FROM orders WHERE user_id = $1", user_id)
    notifications = await conn.fetch("SELECT * FROM notifications WHERE user_id = $1", user_id)
    return {"user": user, "orders": orders, "notifications": notifications}
```

### Step 3: Convert to batch()

```python
# After: Parallel queries
def get_dashboard(user_id: int):
    with pynext_go.batch() as b:
        user = b.query("SELECT * FROM users WHERE id = $1", [user_id])
        orders = b.query("SELECT * FROM orders WHERE user_id = $1", [user_id])
        notifications = b.query("SELECT * FROM notifications WHERE user_id = $1", [user_id])
    
    return {
        "user": user.rows[0] if user.rows else None,
        "orders": orders.rows,
        "notifications": notifications.rows
    }
```

### Step 4: Convert DataFrame operations

```python
# Before: asyncpg → DataFrame
async def get_analytics():
    result = await conn.fetch("SELECT * FROM events LIMIT 50000")
    df = pd.DataFrame([dict(r) for r in result])
    return df

# After: COPY → DataFrame
def get_analytics():
    return pynext_go.execute_copy_df("SELECT * FROM events LIMIT 50000")
```

### Step 5: Benchmark and validate

```python
import time

# Benchmark old endpoint
start = time.perf_counter()
for _ in range(100):
    await old_get_dashboard(user_id)
old_time = time.perf_counter() - start

# Benchmark new endpoint
start = time.perf_counter()
for _ in range(100):
    new_get_dashboard(user_id)
new_time = time.perf_counter() - start

print(f"Old: {old_time*10:.2f}ms per call")
print(f"New: {new_time*10:.2f}ms per call")
print(f"Speedup: {old_time/new_time:.2f}x")
```

---

## Code Comparison Examples

### Example 1: User Dashboard

**asyncpg (sequential):**
```python
async def get_dashboard(user_id: int):
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, name, email FROM users WHERE id = $1", 
            user_id
        )
        orders = await conn.fetch(
            "SELECT id, total, status FROM orders WHERE user_id = $1 LIMIT 10", 
            user_id
        )
        notifications = await conn.fetch(
            "SELECT id, message FROM notifications WHERE user_id = $1 AND read = false", 
            user_id
        )
    
    return {
        "user": dict(user) if user else None,
        "orders": [dict(o) for o in orders],
        "notifications": [dict(n) for n in notifications],
    }
```

**Go Bridge (parallel):**
```python
def get_dashboard(user_id: int):
    with pynext_go.batch() as b:
        user = b.query("SELECT id, name, email FROM users WHERE id = $1", [user_id])
        orders = b.query("SELECT id, total, status FROM orders WHERE user_id = $1 LIMIT 10", [user_id])
        notifications = b.query("SELECT id, message FROM notifications WHERE user_id = $1 AND read = false", [user_id])
    
    return {
        "user": dict(zip(user.columns, user.rows[0])) if user.rows else None,
        "orders": [dict(zip(orders.columns, row)) for row in orders.rows],
        "notifications": [dict(zip(notifications.columns, row)) for row in notifications.rows],
    }
```

**Performance:** Go Bridge is **1.85x faster** (0.26ms vs 0.48ms)

### Example 2: Analytics Report

**asyncpg:**
```python
async def get_sales_report(start_date: str, end_date: str):
    async with pool.acquire() as conn:
        result = await conn.fetch("""
            SELECT 
                date_trunc('day', created_at) as day,
                COUNT(*) as order_count,
                SUM(total) as revenue
            FROM orders
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY 1
            ORDER BY 1
        """, start_date, end_date)
    
    df = pd.DataFrame([dict(r) for r in result])
    return df
```

**Go Bridge:**
```python
def get_sales_report(start_date: str, end_date: str):
    # Note: COPY doesn't support parameters, use string formatting carefully
    # or use execute_arrow() for parameterized queries
    df = pynext_go.execute_copy_df(f"""
        SELECT 
            date_trunc('day', created_at) as day,
            COUNT(*) as order_count,
            SUM(total) as revenue
        FROM orders
        WHERE created_at BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY 1
        ORDER BY 1
    """)
    return df
```

**Performance:** Go Bridge is **2.5x faster** for 10k rows

### Example 3: Bulk Export

**asyncpg:**
```python
async def export_orders(output_file: str):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM orders")
    
    df = pd.DataFrame([dict(r) for r in result])
    df.to_csv(output_file, index=False)
```

**Go Bridge:**
```python
def export_orders(output_file: str):
    csv_data = pynext_go.execute_copy("SELECT * FROM orders")
    with open(output_file, 'wb') as f:
        f.write(csv_data)
```

**Performance:** Go Bridge is **3x faster** for 100k rows

---

## Gotchas & Limitations

### Go Bridge Limitations

1. **No streaming results**
   - Results are fully buffered in memory
   - For very large results, use COPY with chunking

2. **COPY doesn't support parameters**
   ```python
   # ❌ This doesn't work
   pynext_go.execute_copy("SELECT * FROM orders WHERE user_id = $1", [user_id])
   
   # ✅ Use execute() or execute_arrow() for parameterized queries
   pynext_go.execute("SELECT * FROM orders WHERE user_id = $1", [user_id])
   ```

3. **Transactions are simpler**
   - Use execute_batch() for transactional multi-statement operations
   - Complex transaction logic should stay in asyncpg

4. **No LISTEN/NOTIFY**
   - Go Bridge is for queries, not pub/sub
   - Keep asyncpg for real-time features

### asyncpg Limitations

1. **No true parallelism**
   - Even with `asyncio.gather()`, queries run sequentially on one connection
   - Using multiple connections requires pool management

2. **Slow for large DataFrames**
   - Row-by-row conversion to dicts is slow
   - No native COPY protocol support

3. **GIL-bound**
   - CPU-intensive result processing blocks other async tasks

---

## Summary Decision Matrix

| Scenario | Recommendation | Speedup |
|----------|---------------|---------|
| Single query, return JSON | asyncpg or Go execute() | Same |
| Multiple queries, return JSON | **Go Bridge batch()** | **2x** |
| Single query → DataFrame (small) | Either | Same |
| Single query → DataFrame (large) | **Go Bridge copy_df()** | **2-3x** |
| Bulk data export | **Go Bridge copy()** | **3x** |
| Real-time LISTEN/NOTIFY | asyncpg | N/A |
| Complex transactions | asyncpg | N/A |
| Streaming large results | asyncpg | N/A |

---

## Next Steps

- [Go Bridge API Reference](./23-go-bridge.md)
- [Go Bridge Internals](./25-gobridge-internals.md)

