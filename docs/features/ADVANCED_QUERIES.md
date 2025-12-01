# Advanced Query Features - Complete Guide

PyNext provides advanced query features that give you fine-grained control over database operations. This guide explains everything from first principles, so you understand not just HOW to use these features, but WHY they work the way they do.

## Table of Contents

1. [Understanding Query Execution: First Principles](#understanding-query-execution-first-principles)
2. [Per-Query Timeouts](#per-query-timeouts)
3. [Query Analysis (EXPLAIN/ANALYZE)](#query-analysis-explainanalyze)
4. [Cursor-Based Pagination](#cursor-based-pagination)
5. [Prepared Statements](#prepared-statements)
6. [Query Cancellation](#query-cancellation)
7. [Integration Patterns](#integration-patterns)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)

---

## Understanding Query Execution: First Principles

Before diving into advanced features, let's understand what happens when you run a database query.

### The Journey of a SQL Query

When your Python code runs `await User.all()`, here's what actually happens:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     THE LIFE OF A DATABASE QUERY                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. YOUR PYTHON CODE                                                    │
│     users = await User.all()                                            │
│                    │                                                    │
│                    ▼                                                    │
│  2. PYNEXT QUERY BUILDER                                               │
│     Converts to: "SELECT * FROM users"                                  │
│                    │                                                    │
│                    ▼                                                    │
│  3. CONNECTION POOL                                                     │
│     Gets an available connection (or waits)                             │
│                    │                                                    │
│                    ▼                                                    │
│  ══════════════ NETWORK ══════════════                                  │
│                    │                                                    │
│                    ▼                                                    │
│  4. POSTGRESQL PARSER                                                   │
│     Checks SQL syntax, tokenizes query                                  │
│                    │                                                    │
│                    ▼                                                    │
│  5. POSTGRESQL PLANNER                                                  │
│     Creates execution plan (which indexes to use, join order, etc.)     │
│                    │                                                    │
│                    ▼                                                    │
│  6. POSTGRESQL EXECUTOR                                                 │
│     Runs the plan, reads data from disk/cache                           │
│                    │                                                    │
│                    ▼                                                    │
│  ══════════════ NETWORK ══════════════                                  │
│                    │                                                    │
│                    ▼                                                    │
│  7. PYNEXT TYPE CONVERTER                                               │
│     Converts PostgreSQL types to Python objects                         │
│                    │                                                    │
│                    ▼                                                    │
│  8. YOUR PYTHON CODE                                                    │
│     users = [User(id=1, name="Alice"), User(id=2, name="Bob"), ...]    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Where Time Gets Spent

Understanding WHERE time is spent helps you understand WHY each advanced feature exists:

```
Query Execution Time Breakdown:
═══════════════════════════════════════════════════════════════════════════

Component                Time        What Happens                 Feature
─────────────────────────────────────────────────────────────────────────────
Network round-trip       1-5ms       Data travels to/from DB      (inherent)
                                     
SQL parsing              0.1ms       Parse "SELECT * FROM..."     Prepared
                                                                  Statements
                                                                  
Query planning           0.5-5ms     Decide HOW to execute        Prepared
                                     (index scan? seq scan?)      Statements
                                     
Execution - small        1-10ms      Read data from disk/cache    EXPLAIN
                                                                  helps here
                                                                  
Execution - large        100ms-10s+  Scan millions of rows        Pagination
                                                                  
Waiting for connection   0-1000ms    Pool exhausted, must wait    Timeouts
                                                                  
Result transfer          1-100ms     Send data over network       Pagination
                                                                  
Type conversion          0.1-10ms    PostgreSQL → Python types    (optimized)
─────────────────────────────────────────────────────────────────────────────

TOTAL                    5ms - 10s+  Depends on query complexity
```

### Why Advanced Query Features Exist

| Problem | Symptom | Solution |
|---------|---------|----------|
| Query takes forever | Page hangs, connections exhausted | **Timeouts** |
| Query is slow, don't know why | Users complain about speed | **EXPLAIN/ANALYZE** |
| Too many results to load | Memory errors, slow pages | **Pagination** |
| Same query runs repeatedly | Wasted parsing/planning time | **Prepared Statements** |
| User leaves but query continues | Wasted resources | **Query Cancellation** |

---

## Per-Query Timeouts

### The Problem: Runaway Queries

Imagine this scenario:

```
User clicks "Search" → Your app starts query → Query joins 5 tables → 
Takes 30 seconds → User gives up and leaves → 
But the query KEEPS RUNNING → 
More users click search → More queries pile up → 
All connections exhausted → 
YOUR ENTIRE APP CRASHES
```

This is called a "runaway query" and it's one of the most common causes of production outages.

### What is a Query Timeout?

A timeout says "if this query takes longer than X seconds, STOP IT":

```
                    Query Timeout Timeline
═══════════════════════════════════════════════════════════════════

Timeline:  0s         5s         10s        15s        20s
           │          │          │          │          │
           ▼          ▼          ▼          ▼          ▼
           ├──────────┼──────────┼──────────┼──────────┤
           │                                           │
Query:     [Started]──────────────────────────────────►[Still running]
           │                                           │
           │     ┌─────────────────┐                   │
Timeout:   │     │ 10 second limit │                   │
           │     └────────┬────────┘                   │
           │              │                            │
           │              ▼                            │
           │         [TIMEOUT!]                        │
           │              │                            │
           │              ▼                            │
           │    QueryTimeoutError raised               │
           │    Query cancelled in PostgreSQL          │
           │    Connection returned to pool            │
```

### Three Ways to Set Timeouts

PyNext gives you three ways to set timeouts, each for different use cases:

#### Method 1: Chain Method (For Individual Queries)

Use this when you want to timeout a single specific query:

```python
# ═══════════════════════════════════════════════════════════════════════
# THE CHAIN METHOD
# ═══════════════════════════════════════════════════════════════════════

# Basic usage - 5 second timeout
users = await User.select().where(active=True).timeout(5).all()

# What happens:
# 1. Query starts executing
# 2. If 5 seconds pass and query is still running → QueryTimeoutError
# 3. Query is cancelled in PostgreSQL (doesn't keep running!)
# 4. Connection is returned to pool (not leaked)


# With custom error message (helpful for debugging)
users = await User.select().timeout(
    5, 
    message="User search exceeded time limit - try narrower filters"
).all()

# When timeout occurs, error message will say:
# "User search exceeded time limit - try narrower filters"
# Instead of generic: "Query timed out after 5 seconds"
```

**When to use chain method:**
- ✅ Specific queries you know might be slow
- ✅ Search endpoints (user input = unpredictable)
- ✅ Report generation
- ❌ Not for multiple related queries

#### Method 2: Context Manager (For Multiple Queries)

Use this when multiple queries share a time budget:

```python
# ═══════════════════════════════════════════════════════════════════════
# THE CONTEXT MANAGER
# ═══════════════════════════════════════════════════════════════════════

async with db.timeout(10):
    # ALL queries in this block share the 10 second budget
    users = await User.select().all()          # Takes 2s
    orders = await Order.select().all()         # Takes 3s
    stats = await compute_dashboard_stats()     # Takes 4s
    # Total: 9 seconds - OK, under 10s limit

# If total exceeds 10 seconds → QueryTimeoutError


# Real-world example: API endpoint with time budget
async def get_dashboard(request):
    async with db.timeout(15):  # Dashboard must load in 15s
        
        # Get user data
        user = await User.get(id=request.user_id)
        
        # Get their orders
        orders = await Order.select().where(user_id=user.id).limit(50).all()
        
        # Get recommendations
        recommendations = await get_recommendations(user)
        
        # All three must complete within 15 seconds total
        return Dashboard(user=user, orders=orders, recommendations=recommendations)
```

**When to use context manager:**
- ✅ Dashboard endpoints (multiple data sources)
- ✅ Batch operations (many queries, shared budget)
- ✅ Any operation where total time matters more than individual queries

#### Method 3: Nested Timeouts (For Complex Workflows)

Sometimes you need different timeouts for different parts:

```python
# ═══════════════════════════════════════════════════════════════════════
# NESTED TIMEOUTS
# ═══════════════════════════════════════════════════════════════════════

async def generate_report(request):
    # Overall report has 60 second budget
    async with db.timeout(60):
        
        # But initial data fetch should be quick
        async with db.timeout(5):
            user = await User.get(id=request.user_id)
            settings = await Settings.get(user_id=user.id)
        # Inner timeout is 5s, outer is still 60s
        
        # Heavy computation can take longer
        # (Uses remaining time from 60s budget)
        report_data = await fetch_report_data(user, settings)
        
        # Quick final save
        async with db.timeout(3):
            await Report.insert(user_id=user.id, data=report_data)


# How nested timeouts work:
# ─────────────────────────────────────────────────────────────────────
# 
# Outer: 60 seconds  ├────────────────────────────────────────────────┤
#                    │                                                │
# Inner 1: 5 sec     ├────┤                                           │
#                    │    │                                           │
# Inner 2: 3 sec     │                                           ├──┤ │
#                    │                                           │  │ │
# Time:              0s   5s   10s  15s  20s  25s  30s  35s  40s 45s 50s
```

### How Timeouts Work Under the Hood

Here's what actually happens when you set a timeout:

```
                        Timeout Implementation
═══════════════════════════════════════════════════════════════════════════

1. YOU SET A TIMEOUT
   async with db.timeout(10):
       result = await slow_query()

2. PYNEXT DOES THREE THINGS:

   a) Sets PostgreSQL statement_timeout
      ─────────────────────────────────
      Before query: SET statement_timeout = '10000'  (10 seconds in ms)
      After query:  SET statement_timeout = '0'       (reset to no limit)
      
      Why: PostgreSQL will automatically kill the query after 10 seconds
      
   b) Uses asyncio timeout
      ─────────────────────────────────
      async with asyncio.timeout(10):
          result = await execute_query()
      
      Why: Python side will also give up after 10 seconds
           (handles case where network is slow, not just query)
      
   c) Sends pg_cancel_backend() if needed
      ─────────────────────────────────
      If Python times out before PostgreSQL:
          SELECT pg_cancel_backend(<process_id>)
      
      Why: Ensures query actually stops, not just client giving up
```

### Handling Timeout Errors

When a timeout occurs, you need to handle it gracefully:

```python
from pynext.db import QueryTimeoutError

async def search_products(query: str):
    try:
        # Attempt the search with timeout
        results = await Product.select()\
            .where(name__ilike=f"%{query}%")\
            .timeout(5)\
            .all()
        return {"products": results, "source": "live"}
        
    except QueryTimeoutError as e:
        # Log for debugging
        logger.warning(
            f"Product search timed out: "
            f"query='{query}', "
            f"duration={e.duration_ms}ms, "
            f"limit={e.timeout_seconds}s"
        )
        
        # Return cached/simplified results
        cached = await get_cached_products(query)
        if cached:
            return {"products": cached, "source": "cache"}
        
        # Or return helpful error
        return {
            "error": "Search is taking too long. Try a more specific query.",
            "suggestions": ["Use fewer words", "Add category filter"]
        }
```

### Timeout Statistics

Track timeout patterns to identify problem queries:

```python
from pynext.db import get_timeout_stats, reset_timeout_stats

# Get current statistics
stats = get_timeout_stats()

print(f"Total queries with timeout: {stats.total_queries}")
print(f"Timeouts that occurred: {stats.timeout_count}")
print(f"Timeout rate: {stats.timeout_rate:.1%}")
print(f"Average query duration: {stats.avg_duration_ms:.1f}ms")

# See which query types timeout most
print("\nTimeouts by query type:")
for query_type, count in stats.by_query_type.items():
    print(f"  {query_type}: {count}")

# Output:
# Total queries with timeout: 15432
# Timeouts that occurred: 23
# Timeout rate: 0.1%
# Average query duration: 45.3ms
#
# Timeouts by query type:
#   SELECT: 18
#   UPDATE: 3
#   DELETE: 2


# Reset stats (e.g., after deployment)
reset_timeout_stats()
```

---

## Query Analysis (EXPLAIN/ANALYZE)

### The Problem: Slow Queries

You notice a page is loading slowly. The query looks simple:

```python
users = await User.select().where(email="test@example.com").all()
```

Why is this taking 3 seconds? Without visibility into HOW PostgreSQL executes your query, you're debugging blind.

### What is EXPLAIN?

EXPLAIN asks PostgreSQL: "How WOULD you execute this query?" without actually running it:

```
                    EXPLAIN vs ANALYZE
═══════════════════════════════════════════════════════════════════════════

EXPLAIN (without ANALYZE)
─────────────────────────
What it does:   Shows the PLAN PostgreSQL WOULD use
Runs query:     NO (just plans)
Speed:          Instant
Use when:       You want to see the plan without side effects

Example output:
  Seq Scan on users  (cost=0.00..1234.00 rows=1 width=100)
    Filter: (email = 'test@example.com')


EXPLAIN ANALYZE (with ANALYZE)  
───────────────────────────────
What it does:   Shows plan AND ACTUALLY RUNS the query
Runs query:     YES (executes it!)
Speed:          Takes as long as the query
Use when:       You want real timing data

Example output:
  Seq Scan on users  (cost=0.00..1234.00 rows=1 width=100)
                     (actual time=0.015..2845.123 rows=1 loops=1)
    Filter: (email = 'test@example.com')
    Rows Removed by Filter: 500000
  Planning Time: 0.123 ms
  Execution Time: 2845.456 ms
```

### Understanding Execution Plans

Let's decode what PostgreSQL is telling you:

```
                    Anatomy of an Execution Plan
═══════════════════════════════════════════════════════════════════════════

Seq Scan on users  (cost=0.00..1234.00 rows=1 width=100)
    │        │           │         │       │      │
    │        │           │         │       │      └── Average row size (bytes)
    │        │           │         │       │
    │        │           │         │       └── Estimated rows returned
    │        │           │         │
    │        │           │         └── End cost (total work)
    │        │           │
    │        │           └── Start cost (work before first row)
    │        │
    │        └── Table being scanned
    │
    └── Scan type (see table below)


SCAN TYPES (What PostgreSQL Does):
──────────────────────────────────────────────────────────────────────────

Seq Scan (Sequential Scan)
├── Reads EVERY row in the table
├── Used when: No suitable index, or table is small
├── Speed: SLOW for large tables (O(n))
└── Example: Scanning 1 million rows to find 1 match

Index Scan
├── Uses an index to find rows directly
├── Used when: Indexed column in WHERE clause
├── Speed: FAST (O(log n))
└── Example: Jump directly to matching rows

Index Only Scan
├── Gets all needed data from index alone
├── Used when: All SELECTed columns are in the index
├── Speed: FASTEST (no table access needed)
└── Example: SELECT id FROM users WHERE email = 'x'

Bitmap Index Scan
├── Builds a bitmap of matching rows, then fetches
├── Used when: Multiple index conditions
├── Speed: Good for medium selectivity
└── Example: WHERE status = 'active' AND created > '2024-01-01'
```

### Using EXPLAIN in PyNext

```python
# ═══════════════════════════════════════════════════════════════════════
# BASIC EXPLAIN (Shows plan without running)
# ═══════════════════════════════════════════════════════════════════════

plan = await adapter.explain(
    "SELECT * FROM users WHERE email = 'test@example.com'"
)

print(f"Scan type: {plan.node_type}")       # "Seq Scan" or "Index Scan"
print(f"Estimated cost: {plan.cost}")        # e.g., 1234.00
print(f"Estimated rows: {plan.rows}")        # e.g., 1
print(f"Table: {plan.relation}")             # "users"


# ═══════════════════════════════════════════════════════════════════════
# EXPLAIN ANALYZE (Actually runs the query)
# ═══════════════════════════════════════════════════════════════════════

plan = await adapter.explain(
    "SELECT * FROM users WHERE email = 'test@example.com'",
    analyze=True,   # Actually execute the query!
)

# Now we have ACTUAL timing data
print(f"Planning time: {plan.planning_time}ms")
print(f"Execution time: {plan.execution_time}ms")
print(f"Actual rows: {plan.actual_rows}")

# Compare estimated vs actual
print(f"Estimated rows: {plan.rows}")
print(f"Actual rows: {plan.actual_rows}")
# If these are very different, run ANALYZE on the table!


# ═══════════════════════════════════════════════════════════════════════
# WITH BUFFER STATISTICS (I/O details)
# ═══════════════════════════════════════════════════════════════════════

plan = await adapter.explain(
    "SELECT * FROM users WHERE email = 'test@example.com'",
    analyze=True,
    buffers=True,   # Include I/O statistics
)

print(f"Shared blocks hit (cache): {plan.buffers.shared_hit}")
print(f"Shared blocks read (disk): {plan.buffers.shared_read}")

# If shared_read is high, the data isn't in cache
# Consider: more RAM, or query less data
```

### The ASCII Tree Visualization

PyNext generates a visual tree of the execution plan:

```python
plan = await adapter.explain(
    """
    SELECT users.name, orders.total
    FROM users
    JOIN orders ON orders.user_id = users.id
    WHERE users.active = true
    ORDER BY orders.created_at DESC
    LIMIT 100
    """,
    analyze=True,
)

print(plan.tree)
```

Output:
```
└── Limit
    (cost=1234.00..1234.50 rows=100)
    (actual time=5.123..5.456 rows=100 loops=1)
    │
    └── Sort
        (cost=1234.00..1250.00 rows=5000)
        (actual time=5.100..5.200 rows=100 loops=1)
        Sort Key: orders.created_at DESC
        Sort Method: top-N heapsort  Memory: 50kB
        │
        └── Hash Join
            (cost=100.00..1000.00 rows=5000)
            (actual time=1.000..4.500 rows=5000 loops=1)
            Hash Cond: (orders.user_id = users.id)
            │
            ├── Seq Scan on orders                    ← Reading ALL orders!
            │   (cost=0.00..500.00 rows=10000)
            │   (actual time=0.010..2.000 rows=10000 loops=1)
            │
            └── Hash
                (cost=50.00..50.00 rows=1000)
                (actual time=0.500..0.500 rows=1000 loops=1)
                │
                └── Seq Scan on users                 ← Reading ALL users!
                    (cost=0.00..50.00 rows=1000)
                    (actual time=0.005..0.300 rows=1000 loops=1)
                    Filter: (active = true)
                    Rows Removed by Filter: 200
```

### Automatic Optimization Suggestions

PyNext analyzes the plan and suggests improvements:

```python
plan = await adapter.explain(slow_query, analyze=True)

print("Optimization suggestions:")
for suggestion in plan.suggestions:
    severity_icon = {
        "CRITICAL": "🚨",
        "WARNING": "⚠️",
        "INFO": "ℹ️"
    }[suggestion.severity]
    
    print(f"\n{severity_icon} [{suggestion.severity}] {suggestion.title}")
    print(f"   {suggestion.description}")
    if suggestion.sql:
        print(f"   Fix: {suggestion.sql}")
```

Output:
```
🚨 [CRITICAL] Sequential scan on large table
   Table 'orders' has 1,000,000 rows but no index was used.
   Query scanned all rows to find 5,000 matches.
   Fix: CREATE INDEX idx_orders_user_id ON orders(user_id)

⚠️ [WARNING] Row estimate mismatch
   PostgreSQL estimated 100 rows but found 5,000.
   This can cause poor plan choices.
   Fix: ANALYZE orders

ℹ️ [INFO] Sort uses memory
   Sort operation used 50kB of memory.
   This is fine, but large sorts may spill to disk.
```

### Common Problems and Solutions

```
Problem                          What You'll See              Solution
─────────────────────────────────────────────────────────────────────────────────

SEQUENTIAL SCAN                  Seq Scan on large_table      Add index on WHERE
ON LARGE TABLE                   rows=1000000                 columns

HIGH ROW ESTIMATE                estimated rows=100           Run ANALYZE on
MISMATCH                         actual rows=50000            the table

SORT SPILLS TO DISK              Sort Method: external        Add index on ORDER
                                 merge  Disk: 100MB           BY columns

NESTED LOOP WITH                 Nested Loop                  Ensure join columns
MANY ITERATIONS                  loops=100000                 are indexed

HASH JOIN USES                   Hash  Memory: 500MB          Increase work_mem
TOO MUCH MEMORY                                               or filter earlier

INDEX NOT USED                   Filter: (col = 'value')      Check column types
                                 instead of Index Cond        match exactly
```

---

## Cursor-Based Pagination

### The Problem: Loading 1 Million Rows

You have a table with 1 million users. A naive approach:

```python
# ❌ DON'T DO THIS - loads 1 million rows into memory!
all_users = await User.select().all()

# Then in your template:
for user in all_users:
    render(user)
```

This will:
1. Transfer 1 million rows over the network (slow)
2. Load 1 million User objects into Python memory (crashes)
3. Render 1 million items on a web page (unusable)

### Understanding Pagination Methods

There are two ways to paginate, and they have VERY different performance:

```
                    OFFSET vs KEYSET Pagination
═══════════════════════════════════════════════════════════════════════════

OFFSET PAGINATION (The Traditional Way)
───────────────────────────────────────

How it works:
  Page 1:  SELECT * FROM users ORDER BY id LIMIT 20 OFFSET 0
  Page 2:  SELECT * FROM users ORDER BY id LIMIT 20 OFFSET 20
  Page 50: SELECT * FROM users ORDER BY id LIMIT 20 OFFSET 980
  ...
  Page 5000: SELECT * FROM users ORDER BY id LIMIT 20 OFFSET 99980

The problem with page 5000:
  PostgreSQL must:
    1. Find all users
    2. Sort them by id
    3. Skip the first 99,980 rows (SLOW!)
    4. Return rows 99,981 to 100,000

Performance:
  Page 1:    5ms
  Page 100:  50ms
  Page 1000: 500ms
  Page 5000: 2500ms  ← Gets slower and slower!

Why: OFFSET is O(n) - PostgreSQL scans ALL skipped rows


KEYSET PAGINATION (The Smart Way)
─────────────────────────────────

How it works:
  Page 1:  SELECT * FROM users ORDER BY id LIMIT 20
           Last ID on page: 20
           
  Page 2:  SELECT * FROM users WHERE id > 20 ORDER BY id LIMIT 20
           Last ID on page: 40
           
  Page 50: SELECT * FROM users WHERE id > 980 ORDER BY id LIMIT 20
           Last ID on page: 1000

The magic of page 5000:
  SELECT * FROM users WHERE id > 99980 ORDER BY id LIMIT 20
  
  PostgreSQL:
    1. Jump directly to id > 99980 using index (instant!)
    2. Read next 20 rows
    3. Return them

Performance:
  Page 1:    5ms
  Page 100:  5ms
  Page 1000: 5ms
  Page 5000: 5ms  ← ALWAYS FAST!

Why: WHERE id > X is O(log n) - uses index to jump directly
```

Visual comparison:

```
                    Performance Comparison
═══════════════════════════════════════════════════════════════════════════

Response Time (ms)
     │
2500 │                                                    ╭─ OFFSET
     │                                               ╭────╯
2000 │                                          ╭────╯
     │                                     ╭────╯
1500 │                                ╭────╯
     │                           ╭────╯
1000 │                      ╭────╯
     │                 ╭────╯
 500 │            ╭────╯
     │       ╭────╯
   0 │───────┴────────────────────────────────────────── KEYSET
     └────────────────────────────────────────────────────────────
     Page:  1    100   500   1000  2000  3000  4000  5000
```

### Smart Pagination in PyNext

PyNext automatically chooses the best method:

```python
# ═══════════════════════════════════════════════════════════════════════
# BASIC USAGE (Smart mode - auto-selects best method)
# ═══════════════════════════════════════════════════════════════════════

# First page
page = await adapter.paginate(
    "SELECT * FROM products ORDER BY id",
    page_size=20,
)

print(f"Got {len(page.items)} items")
print(f"Has more pages: {page.has_more}")
print(f"Cursor for next page: {page.next_cursor}")

# Returns:
# {
#   "items": [Product(...), Product(...), ...],  # 20 items
#   "has_more": True,
#   "next_cursor": "eyJpZCI6MjB9...",  # Encoded cursor
#   "page_size": 20
# }


# Next page (pass the cursor)
next_page = await adapter.paginate(
    "SELECT * FROM products ORDER BY id",
    page_size=20,
    cursor=page.next_cursor,  # From previous response
)


# ═══════════════════════════════════════════════════════════════════════
# HOW SMART MODE DECIDES
# ═══════════════════════════════════════════════════════════════════════

# PyNext analyzes your query and chooses:

# Uses KEYSET when:
# ✓ Table has > 10,000 rows
# ✓ ORDER BY column is indexed
# ✓ Simple ordering (single column or compound index)

# Uses OFFSET when:
# ✓ Table has < 10,000 rows (fast enough)
# ✓ You need total count / page numbers
# ✓ Complex ordering not suitable for keyset
```

### The Cursor: How It Works

The cursor encodes "where we left off":

```python
# ═══════════════════════════════════════════════════════════════════════
# WHAT'S INSIDE A CURSOR
# ═══════════════════════════════════════════════════════════════════════

# When you paginate by id:
# Page 1 returns items with id 1-20
# Cursor encodes: {"id": 20}  (the last id)

# Encoded as base64:
# "eyJpZCI6IDIwfQ=="

# Page 2 query becomes:
# SELECT * FROM products WHERE id > 20 ORDER BY id LIMIT 20


# For compound ordering (id + created_at):
# Cursor encodes: {"id": 20, "created_at": "2024-01-15T10:30:00"}

# Page 2 query becomes:
# SELECT * FROM products 
# WHERE (created_at, id) > ('2024-01-15T10:30:00', 20)
# ORDER BY created_at, id 
# LIMIT 20
```

### Explicit Pagination Modes

Sometimes you want to force a specific method:

```python
from pynext.db.adapters import PaginationMethod

# ═══════════════════════════════════════════════════════════════════════
# FORCE KEYSET (Maximum performance)
# ═══════════════════════════════════════════════════════════════════════

page = await adapter.paginate(
    "SELECT * FROM huge_table ORDER BY id",
    page_size=50,
    mode=PaginationMethod.KEYSET,
)

# Always O(1) performance, even on page 1,000,000


# ═══════════════════════════════════════════════════════════════════════
# FORCE OFFSET (When you need page numbers)
# ═══════════════════════════════════════════════════════════════════════

page = await adapter.paginate(
    "SELECT * FROM small_table ORDER BY name",
    page_size=20,
    mode=PaginationMethod.OFFSET,
)

# Includes total count for "Page X of Y" display
print(f"Page {page.current_page} of {page.total_pages}")
print(f"Showing {page.start_index}-{page.end_index} of {page.total_count}")
```

### Streaming Large Datasets

For processing millions of rows without loading into memory:

```python
# ═══════════════════════════════════════════════════════════════════════
# STREAMING (Process without memory issues)
# ═══════════════════════════════════════════════════════════════════════

# Process 10 million rows using only ~100 rows of memory at a time
async for batch in adapter.stream(
    "SELECT * FROM huge_table ORDER BY id",
    batch_size=100,
):
    for row in batch:
        await process_row(row)
    
    # Each batch is 100 rows
    # Previous batch is garbage collected before next loads

# Memory usage: O(batch_size), NOT O(total_rows)
```

### API Response Pattern

Here's how to use pagination in a REST API:

```python
# ═══════════════════════════════════════════════════════════════════════
# API ENDPOINT EXAMPLE
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/products")
async def list_products(
    cursor: str = None,
    page_size: int = 20,
    category: str = None,
):
    # Build query
    query = "SELECT * FROM products"
    params = []
    
    if category:
        query += " WHERE category = $1"
        params.append(category)
    
    query += " ORDER BY id"
    
    # Paginate
    page = await adapter.paginate(
        query,
        *params,
        page_size=min(page_size, 100),  # Cap at 100
        cursor=cursor,
    )
    
    return {
        "data": [p.to_dict() for p in page.items],
        "pagination": {
            "has_more": page.has_more,
            "next_cursor": page.next_cursor,
            "page_size": page.page_size,
        }
    }


# Client usage:
# GET /api/products                           → First page
# GET /api/products?cursor=eyJpZCI6MjB9       → Second page
# GET /api/products?cursor=eyJpZCI6NDB9       → Third page
```

---

## Prepared Statements

### The Problem: Parsing the Same Query 1000 Times

Every time you run a query, PostgreSQL must:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Query Processing Steps                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. PARSE (Lexical Analysis)                          ~0.1ms           │
│     "SELECT * FROM users WHERE id = 123"                                │
│     → [SELECT] [*] [FROM] [users] [WHERE] [id] [=] [123]               │
│                                                                         │
│  2. ANALYZE (Semantic Analysis)                       ~0.2ms           │
│     → Check table exists                                                │
│     → Check column exists                                               │
│     → Check types match                                                 │
│     → Resolve ambiguities                                               │
│                                                                         │
│  3. REWRITE (Query Transformation)                    ~0.1ms           │
│     → Apply views                                                       │
│     → Apply rules                                                       │
│                                                                         │
│  4. PLAN (Optimization)                               ~0.5-5ms         │
│     → Consider all possible execution strategies                        │
│     → Estimate costs                                                    │
│     → Choose best plan                                                  │
│                                                                         │
│  5. EXECUTE (Actually get data)                       varies           │
│     → Run the chosen plan                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

For a query that takes 5ms to execute:
  - Parsing + Planning: 1-5ms (20-50% overhead!)
  - Execution: 5ms
  - Total: 6-10ms

If you run this query 10,000 times/second:
  - Wasted on parsing/planning: 10,000-50,000 ms = 10-50 seconds!
```

### What is a Prepared Statement?

A prepared statement separates "what to do" from "with what values":

```
                    Regular Query vs Prepared Statement
═══════════════════════════════════════════════════════════════════════════

REGULAR QUERY (Every time):
──────────────────────────────

Call 1: SELECT * FROM users WHERE id = 1
        → Parse → Analyze → Plan → Execute → Return
        
Call 2: SELECT * FROM users WHERE id = 2
        → Parse → Analyze → Plan → Execute → Return
        
Call 3: SELECT * FROM users WHERE id = 3
        → Parse → Analyze → Plan → Execute → Return

Time per call: 10ms (5ms overhead + 5ms execution)


PREPARED STATEMENT:
──────────────────

Prepare: SELECT * FROM users WHERE id = $1
         → Parse → Analyze → Plan → STORE THE PLAN
         (One-time cost: 5ms)

Call 1: Execute with $1 = 1
        → Get stored plan → Execute → Return
        
Call 2: Execute with $1 = 2
        → Get stored plan → Execute → Return
        
Call 3: Execute with $1 = 3
        → Get stored plan → Execute → Return

Time per call: 5ms (0ms overhead + 5ms execution)

SAVINGS: 50% faster for repeated queries!
```

### Using Prepared Statements in PyNext

```python
# ═══════════════════════════════════════════════════════════════════════
# PREPARE A STATEMENT
# ═══════════════════════════════════════════════════════════════════════

# Prepare once (at app startup or first use)
stmt = await adapter.prepare(
    "get_user_by_id",                          # Unique name
    "SELECT * FROM users WHERE id = $1",        # SQL with $N placeholders
    types=[int],                                # Parameter types (optional but recommended)
)

# What happens:
# 1. PyNext sends: PREPARE get_user_by_id AS SELECT * FROM users WHERE id = $1
# 2. PostgreSQL parses, analyzes, and plans the query
# 3. PostgreSQL stores the plan in memory
# 4. PyNext stores reference to the prepared statement


# ═══════════════════════════════════════════════════════════════════════
# EXECUTE THE PREPARED STATEMENT
# ═══════════════════════════════════════════════════════════════════════

# Execute many times (20-30% faster after first call!)
user_1 = await stmt.fetchone(1)    # Bind $1 = 1, execute
user_2 = await stmt.fetchone(2)    # Bind $1 = 2, execute
user_3 = await stmt.fetchone(3)    # Bind $1 = 3, execute

# What happens each time:
# 1. PyNext sends: EXECUTE get_user_by_id(1)
# 2. PostgreSQL retrieves stored plan (instant)
# 3. PostgreSQL executes with the value
# 4. Result returned

# Fetch multiple rows
users = await stmt.fetchall(1, 2, 3)  # Returns list of users
```

### Prepared Statement Lifecycle

```
                    Prepared Statement Lifecycle
═══════════════════════════════════════════════════════════════════════════

                        ┌─────────┐
                        │ CREATED │
                        └────┬────┘
                             │
                     prepare("name", sql)
                             │
                             ▼
                    ┌────────────────┐
        ┌──────────│    PREPARED    │──────────┐
        │          └────────┬───────┘          │
        │                   │                  │
   fetchone()          fetchall()         (schema change
        │                   │              detected)
        │                   │                  │
        └────────┬──────────┘                  │
                 │                             │
                 ▼                             ▼
          ┌────────────┐              ┌────────────────┐
          │  EXECUTED  │              │   INVALIDATED  │
          │ (returns   │              │                │
          │  results)  │              │  (auto re-     │
          └────────────┘              │   prepared on  │
                                      │   next use)    │
                                      └────────────────┘
                                             │
                                      unprepare("name")
                                             │
                                             ▼
                                      ┌────────────┐
                                      │  REMOVED   │
                                      └────────────┘
```

### Statement Statistics

Track performance of your prepared statements:

```python
# Get stats for all prepared statements
all_stats = adapter.get_prepared_stats()

for name, stats in all_stats.items():
    print(f"\n{name}:")
    print(f"  SQL: {stats.sql[:50]}...")
    print(f"  Call count: {stats.call_count}")
    print(f"  Total time: {stats.total_time_ms:.1f}ms")
    print(f"  Avg time: {stats.avg_time_ms:.2f}ms")
    print(f"  Errors: {stats.error_count}")
    
    # Calculate time saved
    estimated_without_prepared = stats.call_count * (stats.avg_time_ms + 2)  # +2ms for parsing
    time_saved = estimated_without_prepared - stats.total_time_ms
    print(f"  Time saved: ~{time_saved:.0f}ms")

# Output:
# get_user_by_id:
#   SQL: SELECT * FROM users WHERE id = $1...
#   Call count: 15432
#   Total time: 77160.0ms
#   Avg time: 5.00ms
#   Errors: 0
#   Time saved: ~30864ms
```

### When Schema Changes

If a table's schema changes, prepared statements might become invalid:

```python
# ═══════════════════════════════════════════════════════════════════════
# AUTOMATIC INVALIDATION
# ═══════════════════════════════════════════════════════════════════════

# Scenario: You add a column to users table
# ALTER TABLE users ADD COLUMN nickname VARCHAR(50);

# Next prepared statement execution:
# 1. PostgreSQL detects schema changed
# 2. Returns error: "cached plan must not change result type"
# 3. PyNext catches this error
# 4. PyNext automatically re-prepares the statement
# 5. PyNext re-executes with new plan
# 6. You get your result (slight delay first time)


# ═══════════════════════════════════════════════════════════════════════
# MANUAL CLEANUP
# ═══════════════════════════════════════════════════════════════════════

# Remove a specific prepared statement
await adapter.unprepare("get_user_by_id")

# Remove all prepared statements
count = await adapter.unprepare_all()
print(f"Removed {count} prepared statements")

# Useful before migrations:
async def run_migration():
    # Clear all prepared statements (they'll be re-prepared after migration)
    await adapter.unprepare_all()
    
    # Run migration
    await run_schema_changes()
    
    # First queries after migration will auto-re-prepare
```

---

## Query Cancellation

### The Problem: Wasted Work

Consider this scenario:

```
Timeline:

0.0s  User clicks "Generate Report"
0.1s  Your server starts a complex query
0.2s  Query is running in PostgreSQL...
      ...
      ...
3.0s  User gets impatient, clicks "Cancel" or navigates away
3.1s  Client connection closes
      
      Meanwhile, in PostgreSQL:
      ...
      ...
      ...
8.0s  Query finally finishes!
8.1s  PostgreSQL tries to send result...
8.2s  Connection is closed - result thrown away

WASTED: 5 seconds of database CPU, memory, and I/O
```

Now multiply this by 100 users doing the same thing:

```
Without cancellation:
  100 users × 8 seconds = 800 seconds of query time
  Database is overloaded, ALL users experience slow responses

With cancellation:
  100 users × 3 seconds = 300 seconds of query time (37% reduction!)
  Cancelled queries free resources for active users
```

### How Query Cancellation Works

```
                    Query Cancellation Flow
═══════════════════════════════════════════════════════════════════════════

                   PyNext                          PostgreSQL
                     │                                  │
1. Track query       │                                  │
   ──────────────────┼──────────────────────────────────┼───────────
                     │  "Remember this query           │
                     │   for request req_123"           │
                     │                                  │
2. Execute query     │                                  │
   ──────────────────┼──────────────────────────────────┼───────────
                     │──── SELECT * FROM big_table ────►│
                     │                                  │[processing]
                     │                                  │[processing]
                     │                                  │[processing]
3. Client disconnects│                                  │[processing]
   ──────────────────┼──────────────────────────────────┼───────────
                     │  "Cancel all queries for        │[processing]
                     │   request req_123"               │[processing]
                     │                                  │[processing]
4. Cancel in DB      │                                  │
   ──────────────────┼──────────────────────────────────┼───────────
                     │───pg_cancel_backend(pid)────────►│
                     │                                  │[CANCELLED]
                     │                                  │
5. Resources freed   │                                  │
   ──────────────────┼──────────────────────────────────┼───────────
                     │  Connection returned to pool     │
                     │  Memory freed                    │
                     │                                  │
```

### Using Query Tracking

```python
# ═══════════════════════════════════════════════════════════════════════
# TRACK QUERIES FOR A REQUEST
# ═══════════════════════════════════════════════════════════════════════

async def handle_request(request):
    # Track all queries made during this request
    async with adapter.track_query(request_id=request.id) as tracker:
        
        # All queries here are associated with request.id
        user = await User.get(id=request.user_id)
        orders = await Order.select().where(user_id=user.id).all()
        recommendations = await get_recommendations(user)
        
        return Response(data)

# If client disconnects while queries are running,
# we can cancel them using request.id


# ═══════════════════════════════════════════════════════════════════════
# CANCEL ON DISCONNECT (In your framework's handler)
# ═══════════════════════════════════════════════════════════════════════

@app.on_disconnect
async def handle_disconnect(request):
    # Cancel all queries that were tracked for this request
    count = await adapter.cancel_queries(request.id)
    
    if count > 0:
        logger.info(f"Cancelled {count} queries for disconnected client {request.id}")

# What happens:
# 1. PyNext looks up all queries tagged with request.id
# 2. For each running query, calls pg_cancel_backend(pid)
# 3. PostgreSQL stops executing those queries
# 4. Connections are returned to pool
```

### Viewing Running Queries

```python
# ═══════════════════════════════════════════════════════════════════════
# SEE WHAT'S RUNNING RIGHT NOW
# ═══════════════════════════════════════════════════════════════════════

running = adapter.get_running_queries()

for query in running:
    print(f"Query ID: {query.id}")
    print(f"Request: {query.request_id}")
    print(f"Running for: {query.duration_ms}ms")
    print(f"SQL: {query.query[:100]}...")
    print(f"State: {query.state}")  # PENDING, RUNNING, etc.
    print()

# Output:
# Query ID: q_abc123
# Request: req_user_42
# Running for: 5234ms
# SQL: SELECT * FROM orders JOIN products ON ... WHERE ...
# State: RUNNING


# ═══════════════════════════════════════════════════════════════════════
# CANCEL A SPECIFIC LONG-RUNNING QUERY
# ═══════════════════════════════════════════════════════════════════════

# Find queries running longer than 10 seconds
for query in running:
    if query.duration_ms > 10000:
        logger.warning(f"Cancelling long query: {query.id}")
        await adapter.cancel(query.id)
```

### Cancellation Tokens (For Cooperative Cancellation)

For complex operations that can be cancelled at safe points:

```python
from pynext.db.adapters import CancellationToken, CancelReason

# ═══════════════════════════════════════════════════════════════════════
# CREATE A CANCELLATION TOKEN
# ═══════════════════════════════════════════════════════════════════════

async def process_large_dataset(items, token: CancellationToken):
    """Process items, checking for cancellation periodically."""
    
    results = []
    for i, item in enumerate(items):
        # Check if we should stop (every 100 items)
        if i % 100 == 0:
            token.throw_if_cancelled()  # Raises QueryCancelledError if cancelled
        
        # Do the work
        result = await process_item(item)
        results.append(result)
    
    return results


# ═══════════════════════════════════════════════════════════════════════
# USE THE TOKEN
# ═══════════════════════════════════════════════════════════════════════

async def handle_export_request(request):
    # Create a token for this operation
    token = CancellationToken()
    
    # Store it so we can cancel later
    active_exports[request.id] = token
    
    try:
        items = await fetch_items()
        results = await process_large_dataset(items, token)
        return results
    except QueryCancelledError:
        return Response("Export cancelled", status=499)
    finally:
        del active_exports[request.id]


@app.route("/cancel-export")
async def cancel_export(request):
    token = active_exports.get(request.id)
    if token:
        token.cancel(reason=CancelReason.USER_REQUEST)
        return {"message": "Cancellation requested"}
    return {"message": "No active export found"}
```

---

## Integration Patterns

### Pattern 1: Timeout + Fallback

```python
async def get_user_data(user_id: int):
    """Get user data with timeout and fallback to cache."""
    
    try:
        async with adapter.timeout(5):
            # Try to get fresh data
            user = await User.get(id=user_id)
            orders = await Order.select().where(user_id=user_id).limit(10).all()
            
            # Update cache
            await cache.set(f"user:{user_id}", {"user": user, "orders": orders})
            
            return {"user": user, "orders": orders, "source": "live"}
            
    except QueryTimeoutError:
        # Fall back to cached data
        cached = await cache.get(f"user:{user_id}")
        if cached:
            return {**cached, "source": "cache", "warning": "Using cached data"}
        
        raise HTTPException(503, "Service temporarily unavailable")
```

### Pattern 2: EXPLAIN for Slow Query Detection

```python
async def search_with_analysis(query: str):
    """Search with automatic slow query analysis."""
    
    start = time.time()
    results = await Product.select().where(name__ilike=f"%{query}%").all()
    duration_ms = (time.time() - start) * 1000
    
    # If query was slow, analyze it
    if duration_ms > 500:
        plan = await adapter.explain(
            f"SELECT * FROM products WHERE name ILIKE '%{query}%'",
            analyze=True,
        )
        
        # Log the analysis
        logger.warning(
            f"Slow search query: {duration_ms:.0f}ms\n"
            f"Query: {query}\n"
            f"Plan:\n{plan.tree}\n"
            f"Suggestions: {[s.title for s in plan.suggestions]}"
        )
        
        # Maybe send to monitoring
        await metrics.record_slow_query(
            query=query,
            duration_ms=duration_ms,
            suggestions=plan.suggestions,
        )
    
    return results
```

### Pattern 3: Pagination with Cancellation

```python
@app.get("/api/products")
async def list_products(request, cursor: str = None, page_size: int = 20):
    """Paginated products endpoint with cancellation support."""
    
    async with adapter.track_query(request_id=request.id):
        async with adapter.timeout(10):
            page = await adapter.paginate(
                "SELECT * FROM products ORDER BY created_at DESC",
                page_size=min(page_size, 100),
                cursor=cursor,
            )
            
            return {
                "data": [p.to_dict() for p in page.items],
                "pagination": {
                    "next_cursor": page.next_cursor,
                    "has_more": page.has_more,
                }
            }
```

### Pattern 4: Prepared Statements for Hot Paths

```python
class UserRepository:
    """Repository with prepared statements for common queries."""
    
    def __init__(self, adapter):
        self.adapter = adapter
        self._prepared = False
    
    async def _ensure_prepared(self):
        """Prepare statements on first use."""
        if self._prepared:
            return
        
        self.get_by_id_stmt = await self.adapter.prepare(
            "user_get_by_id",
            "SELECT * FROM users WHERE id = $1",
            types=[int],
        )
        
        self.get_by_email_stmt = await self.adapter.prepare(
            "user_get_by_email",
            "SELECT * FROM users WHERE email = $1",
            types=[str],
        )
        
        self.list_active_stmt = await self.adapter.prepare(
            "user_list_active",
            "SELECT * FROM users WHERE active = true ORDER BY created_at DESC LIMIT $1",
            types=[int],
        )
        
        self._prepared = True
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        await self._ensure_prepared()
        return await self.get_by_id_stmt.fetchone(user_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        await self._ensure_prepared()
        return await self.get_by_email_stmt.fetchone(email)
    
    async def list_active(self, limit: int = 100) -> List[User]:
        await self._ensure_prepared()
        return await self.list_active_stmt.fetchall(limit)
```

---

## API Reference

### Per-Query Timeout

```python
# Classes and Types
class QueryTimeout:
    seconds: float              # Timeout duration
    message: Optional[str]      # Custom error message

class TimeoutConfig:
    default_timeout: Optional[float]  # Default for all queries
    max_timeout: float               # Maximum allowed (default 3600)

class TimeoutStats:
    total_queries: int          # Queries with timeout set
    timeout_count: int          # Number that timed out
    timeout_rate: float         # Percentage that timed out
    avg_duration_ms: float      # Average query duration
    by_query_type: Dict         # Timeouts by SELECT/INSERT/etc.

# Context Manager
TimeoutContext(seconds: float, message: str = None)

# Exception
class QueryTimeoutError(Exception):
    query: str                  # The SQL that timed out
    timeout_seconds: float      # The timeout that was set
    duration_ms: float          # How long query ran before timeout

# Functions
get_timeout_stats() -> TimeoutStats
reset_timeout_stats() -> None
```

### EXPLAIN/ANALYZE

```python
# Main Classes
class QueryPlan:
    raw: str                    # Raw PostgreSQL output
    format: ExplainFormat       # TEXT, JSON, etc.
    query: str                  # Original query
    cost: float                 # Estimated total cost
    rows: int                   # Estimated rows
    node_type: str              # Root node type
    planning_time: Optional[float]   # Time to plan (with ANALYZE)
    execution_time: Optional[float]  # Time to execute (with ANALYZE)
    actual_rows: Optional[int]       # Actual rows (with ANALYZE)
    buffers: Optional[BufferStats]   # I/O stats (with BUFFERS)
    suggestions: List[Suggestion]    # Optimization suggestions
    tree: str                        # ASCII tree visualization
    
    @classmethod
    def from_text(cls, text: str, query: str = None) -> "QueryPlan"
    @classmethod
    def from_json(cls, json_str: str, query: str = None) -> "QueryPlan"
    
    def compare(self, other: "QueryPlan") -> PlanComparison

class PlanNode:
    node_type: str              # "Seq Scan", "Index Scan", etc.
    relation: Optional[str]     # Table name
    cost: float                 # Cost for this node
    rows: int                   # Estimated rows
    actual_time: Optional[float]
    actual_rows: Optional[int]
    children: List[PlanNode]

class BufferStats:
    shared_hit: int             # Blocks found in cache
    shared_read: int            # Blocks read from disk
    shared_written: int         # Blocks written
    local_hit: int
    local_read: int
    local_written: int
    temp_read: int
    temp_written: int

class Suggestion:
    severity: str               # CRITICAL, WARNING, INFO
    title: str                  # Short description
    description: str            # Detailed explanation
    sql: Optional[str]          # Suggested fix (e.g., CREATE INDEX)

# Enums
class ExplainFormat(Enum):
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
```

### Pagination

```python
# Main Classes
class Page(Generic[T]):
    items: List[T]              # Page of results
    page_size: int              # Requested page size
    has_more: bool              # More pages available?
    next_cursor: Optional[str]  # Cursor for next page
    prev_cursor: Optional[str]  # Cursor for previous page
    
    def to_dict(self) -> Dict   # Serialize for API response

class Cursor:
    values: Dict[str, Any]      # Encoded position
    direction: CursorDirection  # FORWARD or BACKWARD
    
    @classmethod
    def encode(cls, values: Dict) -> str    # Dict to base64 string
    @classmethod  
    def decode(cls, cursor: str) -> "Cursor"  # Base64 string to Cursor

class PaginationConfig:
    default_page_size: int = 20
    max_page_size: int = 100
    cursor_secret: Optional[str]  # For signing cursors

# Enums
class PaginationMethod(Enum):
    KEYSET = "keyset"           # WHERE id > last_id
    OFFSET = "offset"           # OFFSET n
    AUTO = "auto"               # PyNext chooses

class CursorDirection(Enum):
    FORWARD = "forward"
    BACKWARD = "backward"
```

### Prepared Statements

```python
# Main Classes
class PreparedStatement:
    name: str                   # Unique identifier
    sql: str                    # SQL with $1, $2, etc.
    param_types: List[type]     # Parameter types
    
    async def fetchone(self, *args) -> Optional[Any]
    async def fetchall(self, *args) -> List[Any]
    async def execute(self, *args) -> int  # Returns row count

class PreparedStats:
    name: str
    sql: str
    call_count: int
    total_time_ms: float
    avg_time_ms: float
    error_count: int

class PreparedCache:
    max_size: int               # LRU eviction threshold
    
    def get(self, name: str) -> Optional[PreparedStatement]
    def put(self, stmt: PreparedStatement) -> None
    def remove(self, name: str) -> bool
    def clear(self) -> int
    def get_all_stats(self) -> Dict[str, PreparedStats]
```

### Query Cancellation

```python
# Main Classes
class RunningQuery:
    id: str                     # Unique query ID
    request_id: Optional[str]   # Associated request
    query: str                  # SQL being executed
    state: QueryState           # PENDING, RUNNING, etc.
    started_at: datetime
    duration_ms: float          # Time since start
    backend_pid: Optional[int]  # PostgreSQL process ID

class QueryTracker:
    request_id: str
    
    def track_query(self, sql: str) -> RunningQuery
    async def cancel_all(self, reason: CancelReason = None) -> int

class CancellationToken:
    is_cancelled: bool
    reason: Optional[CancelReason]
    
    def cancel(self, reason: CancelReason = None) -> None
    def throw_if_cancelled(self) -> None  # Raises QueryCancelledError
    def on_cancel(self, callback: Callable) -> None

class CancellationConfig:
    cancel_on_disconnect: bool = True
    cancel_timeout: float = 5.0     # Seconds to wait for cancel

# Enums
class QueryState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

class CancelReason(Enum):
    CLIENT_DISCONNECT = "client_disconnect"
    TIMEOUT = "timeout"
    USER_REQUEST = "user_request"
    SHUTDOWN = "shutdown"

# Exception
class QueryCancelledError(Exception):
    query_id: str
    reason: CancelReason
    duration_ms: float
```

---

## Troubleshooting

### Timeout Issues

**Problem: Query times out even though it's fast in psql**

```python
# Cause: Network latency or connection acquisition time
# The timeout includes waiting for a connection!

# Solution 1: Increase timeout
async with adapter.timeout(15):  # Was 5
    result = await query()

# Solution 2: Set statement_timeout directly for query-only timing
await adapter.execute("SET statement_timeout = '5000'")  # 5 seconds
result = await query()
await adapter.execute("SET statement_timeout = '0'")
```

**Problem: Nested timeout doesn't work as expected**

```python
# The inner timeout is ADDITIVE to outer, not a separate limit

# WRONG mental model:
async with adapter.timeout(30):
    async with adapter.timeout(5):  # Think: 5 second limit
        await slow_query()  # Takes 6s → times out? NO!

# CORRECT mental model:
# Inner timeout uses the SMALLER of inner vs remaining outer
# If 25s left on outer, inner 5s wins
# If 3s left on outer, outer 3s wins
```

### EXPLAIN Issues

**Problem: EXPLAIN shows different plan than actual query**

```python
# Cause: PostgreSQL statistics are outdated

# Solution: Update table statistics
await adapter.execute("ANALYZE users")
await adapter.execute("ANALYZE orders")

# For all tables:
await adapter.execute("ANALYZE")
```

**Problem: Plan looks good but query is still slow**

```python
# Cause: Plan is based on estimates, actual data may differ

# Solution: Use EXPLAIN ANALYZE to see actual behavior
plan = await adapter.explain(query, analyze=True)

# Compare estimated vs actual rows
print(f"Estimated: {plan.rows}, Actual: {plan.actual_rows}")

# If very different, run ANALYZE on the tables
```

### Pagination Issues

**Problem: "Invalid cursor" errors**

```python
# Causes:
# 1. Cursor from different query
# 2. Cursor was tampered with
# 3. Cursor expired (if using signed cursors)

# Solution: Handle gracefully
try:
    page = await adapter.paginate(query, cursor=cursor)
except ValueError:
    # Start from beginning
    page = await adapter.paginate(query, cursor=None)
```

**Problem: Keyset pagination returns duplicates**

```python
# Cause: ORDER BY column has duplicate values

# Solution: Add unique column to ORDER BY
# WRONG:
"SELECT * FROM orders ORDER BY created_at"  # Multiple orders same time

# CORRECT:
"SELECT * FROM orders ORDER BY created_at, id"  # id breaks ties
```

### Prepared Statement Issues

**Problem: "Prepared statement does not exist"**

```python
# Cause: Statement was invalidated (schema change, connection loss)

# Solution: PyNext auto-re-prepares, but if you see this:
# 1. The connection might have reconnected
# 2. Schema might have changed

# Force re-prepare:
await adapter.unprepare("statement_name")
stmt = await adapter.prepare("statement_name", sql)
```

**Problem: Prepared statement returns wrong results after schema change**

```python
# Cause: Cached plan is stale

# Solution: Clear prepared statements before/after migrations
async def run_migration():
    await adapter.unprepare_all()
    await run_schema_changes()
    # Statements will auto-re-prepare on next use
```

### Cancellation Issues

**Problem: cancel_queries returns 0 but queries are running**

```python
# Causes:
# 1. Queries not tracked with track_query()
# 2. Wrong request_id
# 3. Queries already completed

# Solution: Ensure tracking
async with adapter.track_query(request_id=request.id):  # Required!
    result = await slow_query()

# Verify tracking
running = adapter.get_running_queries()
for q in running:
    print(f"{q.id}: request={q.request_id}")
```

**Problem: Cancelled query still appears to run**

```python
# Cause: pg_cancel_backend sends SIGINT, query may not stop instantly

# Solution: Use terminate for stubborn queries
await adapter._cancel_executor.terminate_by_pid(query.backend_pid)

# Note: This is more forceful and kills the connection
```

---

## Summary

PyNext's advanced query features give you fine-grained control over database operations:

| Feature | Problem It Solves | Key Benefit |
|---------|------------------|-------------|
| **Timeouts** | Runaway queries crash your app | Prevent cascading failures |
| **EXPLAIN** | Don't know why query is slow | Visibility into execution |
| **Pagination** | Can't load 1M rows | O(1) performance at any page |
| **Prepared** | Wasted parsing/planning | 20-30% faster repeated queries |
| **Cancellation** | Wasted work after disconnect | Free resources immediately |

All features follow PyNext's design principles:
- **Simple by default**: Just works with sensible defaults
- **Powerful when needed**: Full control available
- **Observable**: Statistics and logging built in
- **Safe**: Proper error handling and cleanup
