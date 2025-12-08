# Parallel Query Execution: Complete Guide

## Executive Summary

PyNext's Query Builder with parallel execution leverages Go's true parallelism to achieve **2-3x speedups** for multi-query API endpoints. This document covers everything you need to know: the problem it solves, how it works, when to use it, and how to implement it correctly.

---

## Table of Contents

1. [The Problem: Why Parallel Execution?](#the-problem-why-parallel-execution)
2. [The Solution: How It Works](#the-solution-how-it-works)
3. [Who Should Use This](#who-should-use-this)
4. [What It Provides](#what-it-provides)
5. [When to Use (and When Not To)](#when-to-use-and-when-not-to)
6. [Where It Fits in Your Architecture](#where-it-fits-in-your-architecture)
7. [Why This Approach](#why-this-approach)
8. [Implementation Guide](#implementation-guide)
9. [Performance Benchmarks](#performance-benchmarks)
10. [Debugging and Troubleshooting](#debugging-and-troubleshooting)
11. [Best Practices](#best-practices)
12. [FAQ](#faq)

---

## The Problem: Why Parallel Execution?

### The Python GIL Problem

Python has the Global Interpreter Lock (GIL), which means only one thread can execute Python bytecode at a time. This creates a fundamental limitation:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PYTHON'S SEQUENTIAL EXECUTION                            │
│                                                                             │
│  Thread 1: ──────────────────────────────────────────────────────────►     │
│            [Query 1 wait][Query 2 wait][Query 3 wait]                      │
│                                                                             │
│  Total Time = Query1 + Query2 + Query3 = 0.45ms                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

Even with `asyncio`, Python can't execute multiple CPU-bound operations truly in parallel. Database queries involve:
- Serializing parameters (CPU)
- Network I/O (can be async)
- Deserializing results (CPU)

The CPU-bound parts are still sequential in Python.

### The Real-World Impact

Consider a typical dashboard API endpoint:

```python
# Traditional Python approach - SEQUENTIAL
async def get_dashboard(user_id: int):
    user = await User.get(user_id)           # ~0.15ms
    orders = await Order.filter(user_id)     # ~0.15ms  
    notifications = await Notification.recent(user_id)  # ~0.15ms
    stats = await Stats.for_user(user_id)    # ~0.15ms
    
    return {"user": user, "orders": orders, ...}

# Total: ~0.60ms (queries run one after another)
```

Even though these queries are **independent**, Python executes them sequentially.

### What Developers Try (And Why It Doesn't Help)

**Attempt 1: asyncio.gather()**
```python
# Looks parallel, but isn't truly parallel
user, orders, notifications, stats = await asyncio.gather(
    User.get(user_id),
    Order.filter(user_id),
    Notification.recent(user_id),
    Stats.for_user(user_id),
)
# Still ~0.50-0.60ms due to GIL
```

`asyncio.gather` helps with I/O wait times but doesn't parallelize the CPU work (serialization/deserialization).

**Attempt 2: ThreadPoolExecutor**
```python
# More overhead, minimal benefit
with ThreadPoolExecutor() as pool:
    futures = [pool.submit(sync_query, q) for q in queries]
    results = [f.result() for f in futures]
# GIL still limits actual parallelism
```

Threads in Python still compete for the GIL.

---

## The Solution: How It Works

### Go's True Parallelism

Go doesn't have a GIL. Goroutines can execute truly in parallel across multiple CPU cores:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GO'S PARALLEL EXECUTION                                  │
│                                                                             │
│  Goroutine 1: ────[Query 1]────────────►                                   │
│  Goroutine 2: ────[Query 2]────────────►                                   │
│  Goroutine 3: ────[Query 3]────────────►                                   │
│                                                                             │
│  Total Time = MAX(Query1, Query2, Query3) = 0.20ms                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         PYNEXT PARALLEL EXECUTION                            │
│                                                                              │
│  PYTHON SIDE                         │  GO SIDE                              │
│  ────────────                        │  ───────                              │
│                                      │                                       │
│  1. QueryBuilder creates queries     │                                       │
│     ┌─────────────┐                  │                                       │
│     │ User.q(...) │                  │                                       │
│     │ Post.q(...) │                  │                                       │
│     │ Order.q(...) │                  │                                       │
│     └─────────────┘                  │                                       │
│            │                         │                                       │
│  2. Convert to AST JSON              │                                       │
│     ┌─────────────┐                  │                                       │
│     │ {"table":   │                  │                                       │
│     │  "users"..} │                  │                                       │
│     └─────────────┘                  │                                       │
│            │                         │                                       │
│            ▼                         │                                       │
│  ═══════════════════════════════════════════════════════════════════════════│
│            │         CGO BRIDGE      │                                       │
│  ═══════════════════════════════════════════════════════════════════════════│
│            │                         │                                       │
│            └─────────────────────────┼──────────────────┐                    │
│                                      │                  ▼                    │
│                                      │  3. Go receives batch                 │
│                                      │     ┌──────────────────┐              │
│                                      │     │ ParseAST()       │              │
│                                      │     │ Validate()       │              │
│                                      │     │ Optimize()       │              │
│                                      │     │ GenerateSQL()    │              │
│                                      │     └──────────────────┘              │
│                                      │            │                          │
│                                      │  4. Execute in parallel               │
│                                      │     ┌──────────────────┐              │
│                                      │     │   goroutine 1 ───┼──► Query 1  │
│                                      │     │   goroutine 2 ───┼──► Query 2  │
│                                      │     │   goroutine 3 ───┼──► Query 3  │
│                                      │     └──────────────────┘              │
│                                      │            │                          │
│                                      │  5. Collect results                   │
│                                      │     ┌──────────────────┐              │
│                                      │     │ JSON serialize   │              │
│                                      │     │ results          │              │
│                                      │     └──────────────────┘              │
│            ┌─────────────────────────┼──────────────────┘                    │
│            │                         │                                       │
│  ═══════════════════════════════════════════════════════════════════════════│
│            │         CGO BRIDGE      │                                       │
│  ═══════════════════════════════════════════════════════════════════════════│
│            ▼                         │                                       │
│  6. Python receives results          │                                       │
│     ┌─────────────┐                  │                                       │
│     │ Map to      │                  │                                       │
│     │ model       │                  │                                       │
│     │ instances   │                  │                                       │
│     └─────────────┘                  │                                       │
│                                      │                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **QueryBuilder** (Python): Creates type-safe queries with AST representation
2. **CGO Bridge**: Passes data between Python and Go via shared memory
3. **Go Executor**: Parses AST, optimizes, generates SQL, executes in parallel
4. **Connection Pool** (pgx): Manages PostgreSQL connections efficiently
5. **Result Mapper** (Python): Converts raw results back to model instances

---

## Who Should Use This

### Ideal Use Cases

| User Type | Use Case | Benefit |
|-----------|----------|---------|
| **API Developers** | Dashboard endpoints with 3+ queries | 2-3x faster responses |
| **Backend Engineers** | Report generation | Parallel data fetching |
| **Full-Stack Devs** | Page data aggregation | Reduced page load times |
| **Data Engineers** | Multi-source data collection | Efficient batch queries |

### Team Requirements

- **Python experience**: Intermediate (familiar with async/await)
- **Go experience**: Not required (it's abstracted away)
- **Database experience**: Basic SQL knowledge
- **DevOps**: Ability to compile Go shared library (one-time setup)

### When Your Team Should Adopt This

✅ **Adopt if:**
- Your API endpoints make 3+ independent database queries
- Response time is a key metric (SLA requirements)
- You're already using PostgreSQL
- You want to reduce infrastructure costs (fewer servers needed)

❌ **Wait if:**
- Most endpoints make single queries
- You're using databases other than PostgreSQL
- Your bottleneck is database capacity, not query latency

---

## What It Provides

### Core Features

#### 1. `QueryBuilder.parallel(*queries)`

Execute multiple queries simultaneously:

```python
from pynext.db import QueryBuilder
from pynext.db.conditions import gt, eq

# Execute 3 queries in parallel
users, posts, orders = await QueryBuilder.parallel(
    User.q(gt("age", 18)),
    Post.q(eq("published", True)),
    Order.q(gt("total", 100)),
)

# All three execute at the same time!
# Total time ≈ slowest query, not sum of all queries
```

**Returns**: List of results in the same order as input queries

**Type Safety**: Each result is properly typed based on the model

#### 2. `QueryBuilder.batch()` Context Manager

Auto-batch queries for cleaner code:

```python
async with QueryBuilder.batch() as batch:
    # These look sequential but will execute in parallel
    users_query = batch.add(User.q(gt("age", 18)))
    posts_query = batch.add(Post.q(eq("published", True)))
    orders_query = batch.add(Order.q(gt("total", 100)))

# After context exits, all queries have executed
users = users_query.result
posts = posts_query.result
orders = orders_query.result
```

**Why use batch()?**
- Cleaner code when building queries conditionally
- Easier refactoring
- Results accessed by name, not index

#### 3. `DeferredQuery` Objects

The `batch.add()` method returns a `DeferredQuery`:

```python
class DeferredQuery:
    @property
    def result(self) -> List[Model]:
        """Get results after batch execution"""
        if not self._executed:
            raise RuntimeError("Batch not yet executed")
        return self._result
```

### Performance Characteristics

| Scenario | Sequential | Parallel | Speedup |
|----------|-----------|----------|---------|
| 2 simple queries | 0.30ms | 0.18ms | 1.7x |
| 3 simple queries | 0.45ms | 0.20ms | 2.25x |
| 5 queries (dashboard) | 0.75ms | 0.25ms | 3.0x |
| 10 queries (report) | 1.50ms | 0.30ms | 5.0x |
| Mixed complexity | 2.00ms | 0.80ms | 2.5x |

---

## When to Use (and When Not To)

### ✅ USE Parallel Execution When:

#### 1. Multiple Independent Queries

```python
# GOOD: Queries don't depend on each other
async def get_dashboard(user_id: int):
    user, orders, notifications, stats = await QueryBuilder.parallel(
        User.q(("id", "=", user_id)),
        Order.q(("user_id", "=", user_id)).order("-created_at").limit(10),
        Notification.q(("user_id", "=", user_id), ("read", "=", False)),
        Stats.q(("user_id", "=", user_id)),
    )
    return {"user": user[0], "orders": orders, ...}
```

#### 2. Dashboard/Overview Pages

```python
# GOOD: Dashboard with multiple widgets
async def admin_dashboard():
    results = await QueryBuilder.parallel(
        User.q().count(),                           # Total users
        User.q(("created_at", ">", yesterday)),     # New users
        Order.q(("status", "=", "pending")),        # Pending orders
        Payment.q(("status", "=", "failed")),       # Failed payments
        Report.q().order("-created_at").limit(5),   # Recent reports
    )
    return {
        "total_users": results[0],
        "new_users": len(results[1]),
        ...
    }
```

#### 3. Report Generation

```python
# GOOD: Gathering data for a report
async def generate_monthly_report(month: int, year: int):
    sales, returns, users, products = await QueryBuilder.parallel(
        Sale.q(("month", "=", month), ("year", "=", year)),
        Return.q(("month", "=", month), ("year", "=", year)),
        User.q(("created_month", "=", month)),
        Product.q(("active", "=", True)),
    )
    return compile_report(sales, returns, users, products)
```

#### 4. API Aggregation

```python
# GOOD: Combining data from multiple tables
async def get_user_profile_complete(user_id: int):
    async with QueryBuilder.batch() as b:
        user = b.add(User.q(("id", "=", user_id)))
        posts = b.add(Post.q(("author_id", "=", user_id)))
        followers = b.add(Follow.q(("following_id", "=", user_id)).count())
        following = b.add(Follow.q(("follower_id", "=", user_id)).count())
    
    return {
        "user": user.result[0],
        "posts": posts.result,
        "followers": followers.result,
        "following": following.result,
    }
```

### ❌ DON'T USE Parallel Execution When:

#### 1. Queries Depend on Each Other

```python
# BAD: Second query depends on first query's result
async def get_user_with_recent_order(user_id: int):
    # Can't parallelize - we need user.last_order_id first
    user = await User.q(("id", "=", user_id)).first()
    order = await Order.q(("id", "=", user.last_order_id)).first()
    return {"user": user, "order": order}
```

#### 2. Single Query

```python
# UNNECESSARY: Only one query
async def get_user(user_id: int):
    # Don't use parallel() for single queries
    # Just use regular query execution
    return await User.q(("id", "=", user_id)).first()
```

#### 3. Very Small Queries

```python
# MARGINAL: Overhead may exceed benefit for tiny queries
async def get_simple_counts():
    # For 2 trivial queries, benefit is minimal (~0.05ms saved)
    # Parallel is still fine, just don't expect huge gains
    active, inactive = await QueryBuilder.parallel(
        User.q(("status", "=", "active")).count(),
        User.q(("status", "=", "inactive")).count(),
    )
```

#### 4. Transaction-Dependent Queries

```python
# CAREFUL: Within a transaction, you may want sequential
async with db.transaction():
    # These should be sequential to maintain isolation
    user = await User.q(("id", "=", user_id)).for_update().first()
    user.balance -= amount
    await user.save()
    
    # Create order after balance update
    order = await Order.create(user_id=user_id, amount=amount)
```

### Decision Flowchart

```
                    ┌─────────────────────┐
                    │ How many queries?   │
                    └─────────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                    ▼         ▼         ▼
                   [1]      [2-3]     [4+]
                    │         │         │
                    ▼         ▼         ▼
              ┌─────────┐ ┌─────┐ ┌─────────┐
              │ Regular │ │     │ │ STRONG  │
              │ query   │ │     │ │ candidate│
              └─────────┘ │     │ └─────────┘
                          ▼     
                    ┌───────────┐
                    │ Are they  │
                    │independent│
                    └───────────┘
                          │
                    ┌─────┴─────┐
                    │           │
                   YES         NO
                    │           │
                    ▼           ▼
              ┌─────────┐ ┌─────────┐
              │ Use     │ │ Keep    │
              │parallel()│ │sequential│
              └─────────┘ └─────────┘
```

---

## Where It Fits in Your Architecture

### Layer Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              YOUR APPLICATION                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         API LAYER (FastAPI/Flask)                      │  │
│  │  @app.get("/dashboard")                                                │  │
│  │  async def dashboard():                                                │  │
│  │      ...                                                               │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         SERVICE LAYER                                  │  │
│  │  class DashboardService:                                               │  │
│  │      async def get_dashboard_data(self, user_id):                      │  │
│  │          # ← PARALLEL EXECUTION HAPPENS HERE                           │  │
│  │          return await QueryBuilder.parallel(...)                       │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         QUERY BUILDER (PyNext)                         │  │
│  │  User.q(...), Post.q(...), Order.q(...)                                │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         GO BRIDGE (pynext_go)                          │  │
│  │  CGO exports, connection pool, parallel executor                       │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         POSTGRESQL                                     │  │
│  │  Connection pool, prepared statements, query execution                 │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Integration Points

#### 1. API Endpoints (Controller Layer)

```python
# routes/dashboard.py
from fastapi import APIRouter
from services.dashboard import DashboardService

router = APIRouter()
dashboard_service = DashboardService()

@router.get("/dashboard/{user_id}")
async def get_dashboard(user_id: int):
    # Controller just delegates to service
    return await dashboard_service.get_dashboard(user_id)
```

#### 2. Service Layer (Business Logic)

```python
# services/dashboard.py
from pynext.db import QueryBuilder
from models import User, Order, Notification, Stats

class DashboardService:
    async def get_dashboard(self, user_id: int):
        # Parallel execution in the service layer
        user, orders, notifications, stats = await QueryBuilder.parallel(
            User.q(("id", "=", user_id)),
            Order.q(("user_id", "=", user_id)).limit(10),
            Notification.q(("user_id", "=", user_id), ("read", "=", False)),
            Stats.q(("user_id", "=", user_id)),
        )
        
        return {
            "user": self._format_user(user[0] if user else None),
            "recent_orders": [self._format_order(o) for o in orders],
            "unread_notifications": len(notifications),
            "stats": self._format_stats(stats[0] if stats else None),
        }
```

#### 3. Repository Layer (Data Access)

```python
# repositories/user.py
from pynext.db import QueryBuilder
from models import User, UserProfile, UserSettings

class UserRepository:
    async def get_user_complete(self, user_id: int):
        """Get user with all related data in parallel"""
        user, profile, settings = await QueryBuilder.parallel(
            User.q(("id", "=", user_id)),
            UserProfile.q(("user_id", "=", user_id)),
            UserSettings.q(("user_id", "=", user_id)),
        )
        
        return {
            "user": user[0] if user else None,
            "profile": profile[0] if profile else None,
            "settings": settings[0] if settings else None,
        }
```

---

## Why This Approach

### Why Go (Not Rust, C++, etc.)?

| Factor | Go | Rust | C++ |
|--------|-----|------|-----|
| **Compilation Speed** | Fast | Slow | Medium |
| **CGO Integration** | Native | Requires bindgen | Complex |
| **Concurrency Model** | Goroutines (simple) | async/await (complex) | Threads (manual) |
| **PostgreSQL Library** | pgx (excellent) | tokio-postgres | libpq |
| **Learning Curve** | Gentle | Steep | Steep |
| **Memory Safety** | GC (no manual) | Manual (safe) | Manual (unsafe) |
| **Build Complexity** | Simple | Complex | Complex |

**Go wins because:**
1. **Goroutines** are perfect for parallel database queries
2. **pgx** is a battle-tested PostgreSQL driver
3. **CGO** makes Python integration straightforward
4. **Fast compilation** means quick iteration
5. **Simple language** means maintainable code

### Why AST-Based (Not String-Based)?

**String-based approach (what we avoided):**
```python
# Risky: SQL injection vulnerabilities
query = f"SELECT * FROM users WHERE age > {age}"
```

**AST-based approach (what we use):**
```python
# Safe: Parameters are separated from query structure
query = User.q(gt("age", age))
# Becomes: SELECT * FROM users WHERE age > $1
# With params: [age]
```

**Benefits of AST:**
1. **Security**: SQL injection is impossible
2. **Optimization**: Go can reorder conditions, collapse duplicates
3. **Validation**: Structure can be validated before execution
4. **Portability**: AST could generate SQL for different databases

### Why Parallel at Go Level (Not asyncio.gather)?

```python
# asyncio.gather - APPEARS parallel but isn't truly parallel
results = await asyncio.gather(
    query1(),  # Python serializes params (GIL held)
    query2(),  # Python serializes params (GIL held)
    query3(),  # Python serializes params (GIL held)
)
# Network I/O is async, but serialization is sequential
```

```python
# QueryBuilder.parallel - TRULY parallel
results = await QueryBuilder.parallel(
    query1,  # Go goroutine 1 (no GIL)
    query2,  # Go goroutine 2 (no GIL)  
    query3,  # Go goroutine 3 (no GIL)
)
# Everything happens in parallel: serialization, network, deserialization
```

### Why Not Use Connection Per Query?

We use a **connection pool** shared across goroutines:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONNECTION POOL                               │
│                                                                  │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐              │
│  │Conn 1│  │Conn 2│  │Conn 3│  │Conn 4│  │Conn 5│              │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘              │
│      │         │         │                                       │
│      ▼         ▼         ▼                                       │
│  Query 1   Query 2   Query 3    (reused for next batch)         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits:**
1. **No connection overhead**: Connections are pre-established
2. **Resource efficient**: Fixed number of connections
3. **PostgreSQL friendly**: Respects max_connections limit

---

## Implementation Guide

### Basic Usage

#### Step 1: Import

```python
from pynext.db import QueryBuilder
from pynext.db.conditions import gt, eq, contains, and_, or_
from your_models import User, Post, Order
```

#### Step 2: Create Queries

```python
# Create query objects (not executed yet)
users_query = User.q(gt("age", 18))
posts_query = Post.q(eq("published", True))
orders_query = Order.q(gt("total", 100))
```

#### Step 3: Execute in Parallel

```python
# Method 1: parallel()
users, posts, orders = await QueryBuilder.parallel(
    users_query,
    posts_query,
    orders_query,
)

# Method 2: batch()
async with QueryBuilder.batch() as b:
    users_q = b.add(users_query)
    posts_q = b.add(posts_query)
    orders_q = b.add(orders_query)

users = users_q.result
posts = posts_q.result
orders = orders_q.result
```

### Advanced Patterns

#### Pattern 1: Conditional Queries

```python
async def search(
    user_id: int,
    include_orders: bool = False,
    include_posts: bool = False,
):
    async with QueryBuilder.batch() as b:
        # Always get user
        user_q = b.add(User.q(("id", "=", user_id)))
        
        # Conditionally add queries
        orders_q = None
        if include_orders:
            orders_q = b.add(Order.q(("user_id", "=", user_id)))
        
        posts_q = None
        if include_posts:
            posts_q = b.add(Post.q(("author_id", "=", user_id)))
    
    return {
        "user": user_q.result[0] if user_q.result else None,
        "orders": orders_q.result if orders_q else [],
        "posts": posts_q.result if posts_q else [],
    }
```

#### Pattern 2: Error Handling

```python
async def get_dashboard_safe(user_id: int):
    try:
        user, orders, notifications = await QueryBuilder.parallel(
            User.q(("id", "=", user_id)),
            Order.q(("user_id", "=", user_id)),
            Notification.q(("user_id", "=", user_id)),
        )
    except DatabaseError as e:
        logger.error(f"Dashboard query failed: {e}")
        # Return partial data or raise
        raise HTTPException(500, "Failed to load dashboard")
    
    return format_dashboard(user, orders, notifications)
```

#### Pattern 3: With Timeouts

```python
import asyncio

async def get_dashboard_with_timeout(user_id: int):
    try:
        results = await asyncio.wait_for(
            QueryBuilder.parallel(
                User.q(("id", "=", user_id)),
                Order.q(("user_id", "=", user_id)),
            ),
            timeout=5.0  # 5 second timeout
        )
    except asyncio.TimeoutError:
        raise HTTPException(504, "Dashboard query timed out")
    
    return results
```

#### Pattern 4: Dynamic Query Building

```python
async def search_users(filters: dict):
    # Build base query
    query = User.q()
    
    if "min_age" in filters:
        query = query.where(gt("age", filters["min_age"]))
    
    if "status" in filters:
        query = query.where(eq("status", filters["status"]))
    
    if "name" in filters:
        query = query.where(contains("name", filters["name"]))
    
    # Execute alongside count for pagination
    users, total = await QueryBuilder.parallel(
        query.order("-created_at").page(filters.get("page", 1)),
        query.count(),
    )
    
    return {"users": users, "total": total}
```

---

## Performance Benchmarks

### Test Setup

- **Database**: PostgreSQL 15
- **Hardware**: 4-core CPU, 16GB RAM
- **Connection Pool**: 10 connections
- **Data**: 100,000 users, 500,000 orders, 1M posts

### Results

#### Simple Queries (SELECT * WHERE id = ?)

| Queries | Sequential | Parallel | Speedup |
|---------|-----------|----------|---------|
| 1 | 0.15ms | 0.15ms | 1.0x |
| 2 | 0.30ms | 0.18ms | 1.7x |
| 3 | 0.45ms | 0.20ms | 2.25x |
| 5 | 0.75ms | 0.22ms | 3.4x |
| 10 | 1.50ms | 0.28ms | 5.4x |

#### Complex Queries (JOINs, aggregations)

| Queries | Sequential | Parallel | Speedup |
|---------|-----------|----------|---------|
| 2 | 2.0ms | 1.2ms | 1.7x |
| 3 | 3.0ms | 1.5ms | 2.0x |
| 5 | 5.0ms | 2.0ms | 2.5x |

#### Real-World Dashboard

```python
# This benchmark
async def dashboard_benchmark(user_id):
    return await QueryBuilder.parallel(
        User.q(("id", "=", user_id)),
        Order.q(("user_id", "=", user_id)).order("-created_at").limit(10),
        Notification.q(("user_id", "=", user_id), ("read", "=", False)).count(),
        Stats.q(("user_id", "=", user_id)),
        Activity.q(("user_id", "=", user_id)).order("-timestamp").limit(20),
    )
```

| Method | Time | Speedup |
|--------|------|---------|
| Sequential (asyncpg) | 0.85ms | 1.0x |
| asyncio.gather (asyncpg) | 0.72ms | 1.2x |
| **QueryBuilder.parallel** | **0.32ms** | **2.7x** |

---

## Debugging and Troubleshooting

### Debugging Queries

#### See Generated SQL

```python
# Before parallel execution, check individual queries
query = User.q(gt("age", 18)).select("id", "name").order("-created_at")

print(query.explain())
# SELECT FROM users
#   columns: id, name
#   where: (age > 18)
#   order: created_at DESC

print(query.to_dict())
# {"table": "users", "type": "SELECT", "conditions": {...}, ...}
```

#### Logging

```python
import logging

# Enable query logging
logging.getLogger("pynext.db").setLevel(logging.DEBUG)

# Now parallel() will log:
# DEBUG:pynext.db:Executing 3 queries in parallel
# DEBUG:pynext.db:Query 1: SELECT * FROM users WHERE age > $1
# DEBUG:pynext.db:Query 2: SELECT * FROM posts WHERE published = $1
# DEBUG:pynext.db:Query 3: SELECT * FROM orders WHERE total > $1
# DEBUG:pynext.db:Parallel execution completed in 0.20ms
```

### Common Issues

#### Issue 1: "Batch not yet executed"

```python
# WRONG
async with QueryBuilder.batch() as b:
    users_q = b.add(User.q())
    print(users_q.result)  # RuntimeError!

# RIGHT
async with QueryBuilder.batch() as b:
    users_q = b.add(User.q())
# Access result AFTER context exits
print(users_q.result)  # Works!
```

#### Issue 2: Queries Not Running in Parallel

```python
# WRONG - Awaiting inside parallel() does nothing
results = await QueryBuilder.parallel(
    await User.q(),  # Already executed!
    await Post.q(),  # Already executed!
)

# RIGHT - Pass unawaited queries
results = await QueryBuilder.parallel(
    User.q(),  # Will be executed in parallel
    Post.q(),  # Will be executed in parallel
)
```

#### Issue 3: Memory Issues with Large Results

```python
# CAREFUL - Large parallel results consume memory
results = await QueryBuilder.parallel(
    User.q(),          # 100,000 rows
    Post.q(),          # 500,000 rows
    Comment.q(),       # 2,000,000 rows
)
# All results in memory at once!

# BETTER - Add limits or stream
results = await QueryBuilder.parallel(
    User.q().limit(1000),
    Post.q().limit(1000),
    Comment.q().limit(1000),
)
```

---

## Best Practices

### DO ✅

1. **Group independent queries**
   ```python
   # Good: All queries are independent
   user, orders, notifications = await QueryBuilder.parallel(
       User.q(("id", "=", user_id)),
       Order.q(("user_id", "=", user_id)),
       Notification.q(("user_id", "=", user_id)),
   )
   ```

2. **Use batch() for conditional queries**
   ```python
   async with QueryBuilder.batch() as b:
       user_q = b.add(User.q(("id", "=", user_id)))
       if include_orders:
           orders_q = b.add(Order.q(("user_id", "=", user_id)))
   ```

3. **Add timeouts for production**
   ```python
   results = await asyncio.wait_for(
       QueryBuilder.parallel(...),
       timeout=5.0
   )
   ```

4. **Log parallel execution in development**
   ```python
   logging.getLogger("pynext.db").setLevel(logging.DEBUG)
   ```

### DON'T ❌

1. **Don't parallelize dependent queries**
   ```python
   # Bad: order depends on user
   user = await User.q(("id", "=", user_id)).first()
   order = await Order.q(("id", "=", user.last_order_id)).first()
   ```

2. **Don't use for single queries**
   ```python
   # Unnecessary overhead
   [user] = await QueryBuilder.parallel(User.q(("id", "=", 1)))
   
   # Just do this
   user = await User.q(("id", "=", 1)).first()
   ```

3. **Don't forget limits on large tables**
   ```python
   # Bad: Could return millions of rows
   all_users = await QueryBuilder.parallel(User.q(), Post.q())
   
   # Good: Limit results
   results = await QueryBuilder.parallel(
       User.q().limit(100),
       Post.q().limit(100),
   )
   ```

---

## FAQ

### Q: Does this work with transactions?

**A:** Yes, but queries within a transaction use the same connection, so parallelism is limited. For read-only parallel queries, transactions aren't needed.

### Q: What happens if one query fails?

**A:** The entire `parallel()` call raises an exception. Use try/except for error handling.

### Q: Can I mix different databases?

**A:** Currently, parallel execution works with a single PostgreSQL database. Cross-database queries aren't supported.

### Q: Is there a maximum number of parallel queries?

**A:** Practically limited by your connection pool size. With a pool of 10 connections, you can run 10 queries truly in parallel. Additional queries wait for connections.

### Q: Does this work with ORM relationships?

**A:** Yes! Results are mapped to model instances, including relationships if using `.include()`.

### Q: How does this compare to GraphQL DataLoader?

**A:** Similar concept! DataLoader batches N+1 queries. `parallel()` batches independent queries. They solve different problems and can be used together.

### Q: Can I use this with SQLAlchemy?

**A:** Not directly. This is specific to PyNext's query builder. SQLAlchemy has its own async patterns.

---

## Summary

PyNext's parallel query execution solves a real problem: Python's GIL limits true parallelism for database operations. By delegating to Go:

1. **Multiple queries execute simultaneously** (not just async I/O)
2. **2-3x speedups** for typical multi-query endpoints
3. **Clean API** that feels natural to Python developers
4. **Type-safe** with full IDE support
5. **Production-ready** with proper error handling and timeouts

Use `QueryBuilder.parallel()` whenever you have 2+ independent queries. Your users (and your SLAs) will thank you.

---

## Related Documentation

- [Query Builder API Reference](./26-query-builder.md)
- [Query Security](./27-query-security.md)
- [Query Builder Internals](./28-query-internals.md)
- [Go Bridge Deep Dive](./25-gobridge-internals.md)
- [asyncpg vs Go Bridge Comparison](./24-asyncpg-vs-gobridge.md)

