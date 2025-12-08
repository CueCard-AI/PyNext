# Phase 8.3: DataFrame Integration

> **Complete Guide to PyNext DataFrame Operations**
>
> This document explains how to efficiently retrieve database results as DataFrames using PyNext's Go bridge. Covers Polars, NumPy, and pandas integration with zero-copy optimization.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Who Is This For?](#who-is-this-for)
3. [What Problem Does This Solve?](#what-problem-does-this-solve)
4. [When to Use Each Method](#when-to-use-each-method)
5. [Quick Start](#quick-start)
6. [API Reference](#api-reference)
7. [Performance Benchmarks](#performance-benchmarks)
8. [Type Mapping](#type-mapping)
9. [Architecture](#architecture)
10. [Common Patterns](#common-patterns)
11. [Error Handling](#error-handling)
12. [FAQ](#faq)

---

## Executive Summary

PyNext Phase 8.3 adds DataFrame output methods that are **4x faster than asyncpg** for analytical workloads (up to **5.69x faster** at scale). This is achieved through:

1. **Zero-copy Arrow transfer** from Go to Python
2. **Native Polars integration** (instant conversion from Arrow)
3. **Optimized NumPy arrays** (zero-copy for numeric columns)
4. **Direct pandas support** via Arrow's optimized conversion

### Key Features

| Feature | Speedup vs asyncpg | Best For |
|---------|-------------------|----------|
| `execute_polars()` | **2.7-5.0x** | Analytics, ML pipelines |
| `execute_pandas()` | **2.8-5.7x** | Data exploration, legacy code |
| `execute_numpy()` | **2.4-3.3x** | Vectorized operations |
| `User.q().to_polars()` | **2.7-5.0x** | QueryBuilder + analytics |

---

## Who Is This For?

### Data Scientists / ML Engineers

You work with large datasets and need fast data transfer from PostgreSQL to your analysis environment.

```python
# Before: Slow asyncpg + manual conversion
rows = await conn.fetch("SELECT * FROM training_data LIMIT 100000")
df = pd.DataFrame([dict(r) for r in rows])  # Slow!

# After: 2-3x faster with PyNext
df = await pynext_go.execute_polars_async("SELECT * FROM training_data LIMIT 100000")
```

### Backend Developers with Analytics Endpoints

You build API endpoints that aggregate or analyze data before returning JSON.

```python
# Aggregate large dataset, return summary
df = await User.q(("created_at", ">", last_week)).to_polars()
summary = df.group_by("plan").agg(pl.count()).to_dicts()
return {"user_counts_by_plan": summary}
```

### Anyone Replacing asyncpg

If you're migrating from asyncpg and want DataFrame support, this is your guide.

---

## What Problem Does This Solve?

### The Problem

Traditional Python database drivers (asyncpg, psycopg2) return rows as:
- Lists of Record objects
- Lists of tuples
- Lists of dictionaries

Converting these to DataFrames is slow because:
1. Python iteration is slow (GIL-bound)
2. Type conversion happens row-by-row
3. Memory is copied multiple times

```python
# Traditional approach: O(n) Python loop, multiple copies
rows = await conn.fetch("SELECT * FROM big_table")
df = pd.DataFrame([dict(r) for r in rows])  # 100K rows = ~500ms
```

### The Solution

PyNext uses Apache Arrow as an intermediate format:
1. **Go** queries PostgreSQL and builds Arrow RecordBatch
2. **Arrow IPC** transfers data to Python (zero-copy for numeric types)
3. **Polars/NumPy/pandas** consume Arrow directly (zero-copy)

```python
# PyNext approach: Zero-copy, 2-3x faster
df = pynext_go.execute_polars("SELECT * FROM big_table")  # 100K rows = ~150ms
```

---

## When to Use Each Method

### Decision Tree

```
Do you need a DataFrame?
├── YES
│   ├── Using Polars? → execute_polars() or .to_polars()
│   ├── Using pandas? → execute_pandas() or .to_pandas()
│   ├── Using NumPy?
│   │   ├── Column-wise operations? → execute_numpy() or .to_numpy()
│   │   └── Row iteration? → execute_numpy_structured() or .to_numpy_structured()
│   └── Need raw dicts for JSON? → .to_dicts()
│
└── NO
    ├── Single row? → .first()
    ├── List of models? → .all()
    └── Just count? → .count()
```

### Quick Reference

| Use Case | Method | Why |
|----------|--------|-----|
| ML training data | `execute_polars()` | Fastest, best for large data |
| Data exploration | `execute_pandas()` | Familiar API, Jupyter integration |
| Numerical analysis | `execute_numpy()` | Vectorized ops, zero-copy for floats |
| Row-by-row processing | `execute_numpy_structured()` | Named fields, row iteration |
| API response (small) | `.all()` → JSON | Model instances, validation |
| API response (large) | `.to_dicts()` | Direct dict conversion |
| Aggregation | `execute_polars()` → `.to_dicts()` | Fast aggregation, then JSON |

---

## Quick Start

### Installation

```bash
pip install pynext-go polars numpy pandas pyarrow
```

### Basic Usage

```python
import pynext_go

# Initialize the bridge
pynext_go.init("postgresql://user:pass@localhost/mydb")

# Option 1: Direct function calls
df_polars = pynext_go.execute_polars("SELECT * FROM users WHERE age > $1", [18])
df_pandas = pynext_go.execute_pandas("SELECT * FROM orders")
arrays = pynext_go.execute_numpy("SELECT id, score FROM users")

# Option 2: QueryBuilder methods
df = await User.q(("age", ">", 18)).to_polars()
df = await Order.q().select("id", "total").to_pandas()
arrays = await Product.q().to_numpy()
```

### Async Usage

```python
import asyncio
import pynext_go

async def get_analytics():
    # Async versions available for all methods
    df = await pynext_go.execute_polars_async(
        "SELECT * FROM events WHERE timestamp > $1",
        [last_hour]
    )
    return df.group_by("event_type").agg(pl.count())

asyncio.run(get_analytics())
```

---

## API Reference

### Standalone Functions

#### `pynext_go.execute_polars(sql, params=None)`

Execute query and return Polars DataFrame.

**Arguments:**
- `sql` (str): SQL query with `$1`, `$2`, ... placeholders
- `params` (list, optional): Query parameters

**Returns:** `polars.DataFrame`

**Example:**
```python
import polars as pl

df = pynext_go.execute_polars(
    "SELECT id, name, score FROM users WHERE active = $1",
    [True]
)

# Polars operations
high_scorers = df.filter(pl.col("score") > 90).sort("score", descending=True)
```

---

#### `pynext_go.execute_numpy(sql, params=None, zero_copy=True)`

Execute query and return column-wise NumPy arrays.

**Arguments:**
- `sql` (str): SQL query
- `params` (list, optional): Query parameters
- `zero_copy` (bool): Attempt zero-copy for numeric columns (default: True)

**Returns:** `dict[str, numpy.ndarray]`

**Example:**
```python
import numpy as np

arrays = pynext_go.execute_numpy("SELECT id, score FROM users")

# Vectorized operations (fast!)
mean_score = np.mean(arrays["score"])
high_scorers = arrays["id"][arrays["score"] > 90]
normalized = (arrays["score"] - mean_score) / np.std(arrays["score"])
```

---

#### `pynext_go.execute_numpy_structured(sql, params=None, max_string_length=256)`

Execute query and return NumPy structured array.

**Arguments:**
- `sql` (str): SQL query
- `params` (list, optional): Query parameters
- `max_string_length` (int): Max length for fixed-width string fields (default: 256)

**Returns:** `numpy.ndarray` (structured)

**Example:**
```python
arr = pynext_go.execute_numpy_structured("SELECT id, name, score FROM users")

# Access by field name
print(arr["name"])  # ['Alice', 'Bob', 'Charlie']

# Access by row
print(arr[0])  # (1, 'Alice', 95.5)

# Iterate over rows
for row in arr:
    print(f"{row['name']}: {row['score']}")

# Filter rows
high_scorers = arr[arr["score"] > 90]
```

---

#### `pynext_go.execute_pandas(sql, params=None)`

Execute query and return pandas DataFrame.

**Arguments:**
- `sql` (str): SQL query
- `params` (list, optional): Query parameters

**Returns:** `pandas.DataFrame`

**Example:**
```python
import pandas as pd

df = pynext_go.execute_pandas("SELECT * FROM orders WHERE status = $1", ["pending"])

# pandas operations
print(df.describe())
print(df.groupby("customer_id")["total"].sum())
```

---

### QueryBuilder Methods

All DataFrame methods are available on `QueryBuilder`:

```python
# After building your query
query = User.q(("age", ">", 18)).select("id", "name", "score").order("-score")

# Choose output format
df_polars = await query.to_polars()      # Polars DataFrame
df_pandas = await query.to_pandas()      # pandas DataFrame  
arrays = await query.to_numpy()          # dict[str, ndarray]
structured = await query.to_numpy_structured()  # structured array
dicts = await query.to_dicts()           # list[dict]
tuples = await query.to_list()           # list[tuple]
```

---

## Performance Benchmarks

> **pynext-go is 4.07x faster than asyncpg** on average across all DataFrame operations.
>
> See [Benchmark Methodology](./31-benchmark-methodology.md) for full details.

### Measured Results (Real Benchmarks)

| Rows | Operation | asyncpg (ms) | pynext-go (ms) | **Speedup** |
|------|-----------|--------------|----------------|-------------|
| **10K** | to_polars | 21.77 | 8.01 | 2.72x |
| | to_pandas | 20.31 | 7.16 | 2.83x |
| | to_numpy | 14.67 | 6.19 | 2.37x |
| **100K** | to_polars | 212.67 | 49.17 | **4.33x** |
| | to_pandas | 221.70 | 49.08 | **4.52x** |
| | to_numpy | 138.65 | 50.05 | 2.77x |
| **500K** | to_polars | 1,031.35 | 224.64 | **4.59x** |
| | to_pandas | 1,381.05 | 242.66 | **5.69x** |
| | to_numpy | 737.79 | 249.76 | 2.95x |
| **1M** | to_polars | 1,925.09 | 497.72 | 3.87x |
| | to_pandas | 2,333.45 | 530.88 | 4.40x |
| | to_numpy | 1,397.76 | 532.81 | 2.62x |
| **2M** | to_polars | 4,477.15 | 890.25 | **5.03x** |
| | to_pandas | 4,807.55 | 1,069.86 | **4.49x** |
| | to_numpy | 3,067.54 | 940.00 | **3.26x** |

### Key Takeaways

- **Polars: up to 5.03x faster** (best at 2M rows)
- **pandas: up to 5.69x faster** (best at 500K rows)  
- **NumPy: up to 3.26x faster** (best at 2M rows)
- **Speedup increases with data size** - bigger data = bigger advantage

### Zero-Copy Verification

```python
import time

# 1 million rows, numeric columns only
table = pynext_go.execute_polars("SELECT id, value FROM big_table")

start = time.perf_counter()
df = pl.from_arrow(table)  # Zero-copy!
elapsed = time.perf_counter() - start

print(f"1M rows converted in {elapsed:.3f}s")  # ~0.05s (instant)
```

### Memory Usage

| Method | Memory for 1M rows |
|--------|-------------------|
| Python list of dicts | ~280 MB |
| NumPy arrays | ~16 MB |
| Polars DataFrame | ~16 MB |
| pandas DataFrame | ~24 MB |

---

## Type Mapping

### PostgreSQL to Arrow to Python

| PostgreSQL Type | Arrow Type | NumPy Type | Polars Type | pandas Type |
|-----------------|------------|------------|-------------|-------------|
| SMALLINT | int16 | int16 | Int16 | int16 |
| INTEGER | int32 | int32 | Int32 | int32 |
| BIGINT | int64 | int64 | Int64 | int64 |
| REAL | float32 | float32 | Float32 | float32 |
| DOUBLE PRECISION | float64 | float64 | Float64 | float64 |
| BOOLEAN | bool | bool | Boolean | bool |
| TEXT/VARCHAR | string | object | Utf8 | object |
| BYTEA | binary | object | Binary | object |
| DATE | date32 | datetime64[D] | Date | datetime64 |
| TIMESTAMP | timestamp | datetime64[us] | Datetime | datetime64 |
| TIMESTAMPTZ | timestamp(tz) | datetime64[us] | Datetime(tz) | datetime64 |
| INTERVAL | duration | timedelta64 | Duration | timedelta64 |
| NUMERIC | decimal128 | object | Decimal | object |
| UUID | string | object | Utf8 | object |
| JSON/JSONB | string | object | Utf8 | object |

### Zero-Copy Types

These types support zero-copy conversion (instant):
- All integer types (int8, int16, int32, int64, uint8, uint16, uint32, uint64)
- All float types (float32, float64)
- Boolean (in most cases)

These types require data copy:
- Strings (Python strings are different from Arrow strings)
- Binary data
- Timestamps with timezone
- Decimal/Numeric
- Nested types (arrays, structs)

---

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              PostgreSQL                                  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Query results
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Go Bridge (pynext-go)                          │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │ pgx driver  │ -> │ Arrow RecordBatch │ -> │ Arrow IPC Serialization │  │
│  └─────────────┘    └─────────────────┘    └─────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Arrow IPC bytes (zero-copy for numerics)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              Python                                      │
│  ┌─────────────────┐                                                    │
│  │ PyArrow Table   │ ────────────────────────────────────┐              │
│  └─────────────────┘                                     │              │
│          │                                               │              │
│          ▼                                               ▼              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────────┐   │
│  │ Polars (zero- │  │ NumPy (zero-  │  │ pandas (optimized         │   │
│  │ copy)         │  │ copy numeric) │  │ to_pandas())              │   │
│  └───────────────┘  └───────────────┘  └───────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Why This Is Fast

1. **Go builds Arrow directly**: No Python-side iteration
2. **Arrow IPC is efficient**: Binary format, schema included
3. **Zero-copy where possible**: Numeric arrays share memory
4. **Polars native Arrow support**: Instant conversion
5. **NumPy direct buffer**: Arrow buffers become NumPy arrays

---

## Common Patterns

### Pattern 1: Analytics Dashboard

```python
async def dashboard_stats(user_id: int):
    """Fetch dashboard data using parallel queries and Polars."""
    
    async with QueryBuilder.batch() as b:
        orders = b.add(Order.q(("user_id", "=", user_id)).to_polars())
        events = b.add(Event.q(("user_id", "=", user_id)).to_polars())
    
    # Aggregate with Polars (fast!)
    order_stats = orders.result.select([
        pl.sum("total").alias("total_spent"),
        pl.count().alias("order_count"),
        pl.mean("total").alias("avg_order")
    ]).to_dicts()[0]
    
    event_counts = events.result.group_by("type").agg(
        pl.count()
    ).to_dicts()
    
    return {
        "order_stats": order_stats,
        "event_counts": event_counts
    }
```

### Pattern 2: ML Feature Engineering

```python
def prepare_training_data():
    """Prepare ML training data with NumPy."""
    
    arrays = pynext_go.execute_numpy("""
        SELECT 
            age, income, credit_score, 
            loan_amount, loan_term, approved
        FROM loan_applications
        WHERE application_date > $1
    """, [cutoff_date])
    
    # Feature matrix (zero-copy for numeric columns)
    X = np.column_stack([
        arrays["age"],
        arrays["income"],
        arrays["credit_score"],
        arrays["loan_amount"],
        arrays["loan_term"]
    ])
    
    # Labels
    y = arrays["approved"].astype(int)
    
    return X, y
```

### Pattern 3: Large Export

```python
async def export_to_parquet(query: str, output_path: str):
    """Export large dataset to Parquet file."""
    
    # Get as Polars (efficient for large data)
    df = await pynext_go.execute_polars_async(query)
    
    # Write directly to Parquet (Polars native)
    df.write_parquet(output_path)
```

### Pattern 4: Time Series Analysis

```python
def analyze_metrics(start_time, end_time):
    """Analyze time series metrics with pandas."""
    
    df = pynext_go.execute_pandas("""
        SELECT timestamp, metric_name, value
        FROM metrics
        WHERE timestamp BETWEEN $1 AND $2
        ORDER BY timestamp
    """, [start_time, end_time])
    
    # pandas time series operations
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    
    # Resample to hourly
    hourly = df.groupby('metric_name').resample('1H')['value'].mean()
    
    return hourly
```

### Pattern 5: Vectorized Calculations

```python
def calculate_scores():
    """Perform vectorized calculations with NumPy."""
    
    arrays = pynext_go.execute_numpy(
        "SELECT id, metric_a, metric_b, metric_c FROM items"
    )
    
    # Vectorized calculation (10-100x faster than Python loop)
    scores = (
        0.4 * arrays["metric_a"] +
        0.35 * arrays["metric_b"] +
        0.25 * arrays["metric_c"]
    )
    
    # Find top items
    top_indices = np.argsort(scores)[-10:][::-1]
    top_ids = arrays["id"][top_indices]
    
    return list(top_ids)
```

---

## Error Handling

### Import Errors

```python
try:
    df = pynext_go.execute_polars("SELECT * FROM users")
except ImportError as e:
    # Polars not installed
    print("Install polars: pip install polars")
    # Fallback to pandas
    df = pynext_go.execute_pandas("SELECT * FROM users")
```

### Query Errors

```python
from pynext_go import BridgeQueryError

try:
    df = pynext_go.execute_pandas("SELECT * FROM nonexistent")
except BridgeQueryError as e:
    print(f"Query failed: {e}")
```

### Connection Errors

```python
from pynext_go import BridgeConnectionError

try:
    pynext_go.init("postgresql://bad:connection@string")
except BridgeConnectionError as e:
    print(f"Connection failed: {e}")
```

### Null Value Handling

```python
# NumPy: Nulls become NaN for floats
arrays = pynext_go.execute_numpy("SELECT value FROM data")
valid = arrays["value"][~np.isnan(arrays["value"])]

# Polars: Nulls are native
df = pynext_go.execute_polars("SELECT value FROM data")
valid = df.filter(pl.col("value").is_not_null())

# pandas: Nulls become NaN/NaT/None
df = pynext_go.execute_pandas("SELECT value FROM data")
valid = df.dropna()
```

---

## FAQ

### Q: When should I use Polars vs pandas?

**Polars** for:
- Large datasets (>10K rows)
- Performance-critical code
- Modern codebases
- ML pipelines

**pandas** for:
- Legacy code compatibility
- Jupyter notebooks (better display)
- Specific pandas-only features
- Smaller datasets

### Q: What's the difference between `execute_numpy()` and `execute_numpy_structured()`?

**`execute_numpy()`** returns `dict[str, ndarray]`:
- Best for column-wise operations
- Zero-copy for numeric columns
- Use when: vectorized math, aggregations

**`execute_numpy_structured()`** returns single structured array:
- Best for row-by-row iteration
- Named field access
- Use when: iterating rows, exporting

### Q: How do I verify zero-copy is working?

```python
import numpy as np

arrays = pynext_go.execute_numpy("SELECT id FROM big_table")

# Check if array owns its data
print(arrays["id"].flags["OWNDATA"])  # False = zero-copy
```

### Q: Can I use these with async/await?

Yes! All methods have async versions:

```python
df = await pynext_go.execute_polars_async("SELECT * FROM users")
arrays = await pynext_go.execute_numpy_async("SELECT * FROM data")
df = await User.q().to_polars()  # QueryBuilder methods are already async
```

### Q: What about memory for very large results?

For extremely large results (millions of rows), consider:

1. **Streaming with COPY**: Use `execute_copy()` for raw CSV bytes
2. **Chunked processing**: Add `LIMIT` and process in batches
3. **Server-side aggregation**: Do grouping/filtering in SQL

```python
# Stream large results
csv_bytes = pynext_go.execute_copy("SELECT * FROM huge_table")
# Process in chunks with pandas
for chunk in pd.read_csv(io.BytesIO(csv_bytes), chunksize=10000):
    process(chunk)
```

### Q: How do I handle complex types (JSONB, arrays)?

Complex types are converted to Python objects:

```python
# JSONB becomes dict
arrays = pynext_go.execute_numpy("SELECT jsonb_col FROM table")
for json_obj in arrays["jsonb_col"]:
    print(json_obj["nested"]["key"])

# Arrays become Python lists
arrays = pynext_go.execute_numpy("SELECT int_array FROM table")
for arr in arrays["int_array"]:
    print(sum(arr))
```

---

## Summary

Phase 8.3 DataFrame Integration provides:

1. **`execute_polars()`** - Up to **5.03x faster** than asyncpg, zero-copy
2. **`execute_pandas()`** - Up to **5.69x faster** than asyncpg
3. **`execute_numpy()`** - Up to **3.26x faster**, zero-copy for numerics
4. **`execute_numpy_structured()`** - Row-oriented access with named fields
5. **QueryBuilder methods** - `.to_polars()`, `.to_pandas()`, `.to_numpy()`, etc.

All methods are:
- **Stupid simple** - One function call to get your DataFrame
- **Blazing fast** - **4x faster** than asyncpg on average (measured)
- **Type-safe** - PostgreSQL types map correctly to Python types
- **Memory-efficient** - Zero-copy where possible

For more details, see:
- [Benchmark Methodology](./31-benchmark-methodology.md) - How we test, detailed results
- [Query Builder Guide](./26-query-builder.md)
- [Go Bridge Internals](./25-gobridge-internals.md)
- [Performance Comparison](./24-asyncpg-vs-gobridge.md)

