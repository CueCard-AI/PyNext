# Connection Pooling

High-performance connection pooling for PostgreSQL with intelligent sizing, external pooler support, advanced queuing, and comprehensive monitoring.

## Table of Contents

1. [Why Connection Pooling?](#why-connection-pooling)
2. [First Principles: What is a Connection?](#first-principles-what-is-a-connection)
3. [The Pooling Solution](#the-pooling-solution)
4. [Quick Start](#quick-start)
5. [Architecture Deep Dive](#architecture-deep-dive)
6. [Pool Sizing](#pool-sizing)
7. [Queue Management](#queue-management)
8. [Connection Lifecycle](#connection-lifecycle)
9. [Connection Warmup](#connection-warmup)
10. [External Poolers](#external-poolers)
11. [Monitoring & Metrics](#monitoring--metrics)
12. [Production Configuration](#production-configuration)
13. [Performance Tuning](#performance-tuning)
14. [Troubleshooting](#troubleshooting)
15. [API Reference](#api-reference)

---

## Why Connection Pooling?

### First Principles: What is a Connection?

Before understanding pooling, let's understand what a database connection actually is.

When your Python code talks to PostgreSQL, it doesn't just "send SQL" - it establishes a **connection**. This connection is a network socket with a complex lifecycle:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    What Happens When You Connect                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Your App                                   PostgreSQL Server                 │
│  ────────                                   ─────────────────                 │
│                                                                               │
│  1. Open TCP socket ─────────────────────►  Accept connection                 │
│                     (~1-5ms network RTT)                                      │
│                                                                               │
│  2. TLS handshake   ◄───────────────────►  TLS negotiation                   │
│                     (~10-50ms for TLS)                                        │
│                                                                               │
│  3. Auth request    ─────────────────────►  Verify credentials               │
│                     (password, MD5, SCRAM)                                    │
│                                                                               │
│  4. Auth response   ◄─────────────────────  Grant access                     │
│                                                                               │
│  5. Get parameters  ◄───────────────────►  Session setup                     │
│                     (timezone, encoding)                                      │
│                                                                               │
│  TOTAL: 50-200ms for a new connection!                                       │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

**The Problem**: Each connection costs 50-200ms to establish. If your API handles 1000 requests/second and each opens a new connection:

- 1000 × 100ms = **100 seconds of connection overhead per second**
- That's impossible - your server would collapse

### The Real Cost of Connections

It gets worse. PostgreSQL connections are **expensive** on the server side too:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Per-Connection Overhead                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Resource               Cost Per Connection                                   │
│  ────────               ───────────────────                                   │
│                                                                               │
│  Memory (RAM)           ~5-10 MB for query buffers, temp space               │
│  Backend Process        1 OS process per connection (fork overhead)          │
│  File Descriptors       3-4 FDs per connection (socket, locks, files)        │
│  Shared Memory          Locks, stats, prepared statements                    │
│                                                                               │
│  With 500 connections:                                                        │
│    • 2.5-5 GB RAM just for connections                                       │
│    • 500 OS processes (context switching nightmare)                          │
│    • 1500-2000 file descriptors                                              │
│                                                                               │
│  PostgreSQL default max_connections: 100 (for good reason!)                  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Without Pooling: The Nightmare Scenario

```python
# BAD: What happens without pooling
async def get_user(user_id: int):
    # Every request does this:
    conn = await asyncpg.connect("postgresql://localhost/db")  # 50-200ms!
    try:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return user
    finally:
        await conn.close()

# For 100 concurrent requests:
# - 100 new connections (5-20 seconds of connection time!)
# - 100 PostgreSQL processes spawned
# - 500-1000 MB RAM consumed
# - Response time: 100ms (query) + 100ms (connection) = 200ms minimum
```

---

## The Pooling Solution

### What is Connection Pooling?

Connection pooling is **connection reuse**. Instead of creating a new connection for each request, we maintain a pool of pre-established connections that requests can borrow:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Connection Pooling Concept                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Without Pooling:                                                             │
│  ─────────────────                                                            │
│                                                                               │
│  Request 1 ──► Create Conn ──► Query ──► Close Conn                          │
│  Request 2 ──► Create Conn ──► Query ──► Close Conn                          │
│  Request 3 ──► Create Conn ──► Query ──► Close Conn                          │
│  ...                                                                          │
│  (Each request pays 100ms connection cost)                                    │
│                                                                               │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                               │
│  With Pooling:                                                                │
│  ────────────                                                                 │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────┐                 │
│  │                    CONNECTION POOL                       │                 │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │                 │
│  │  │ Conn 1 │  │ Conn 2 │  │ Conn 3 │  │ Conn 4 │  ...   │                 │
│  │  │ (idle) │  │ (busy) │  │ (idle) │  │ (busy) │        │                 │
│  │  └────────┘  └────────┘  └────────┘  └────────┘        │                 │
│  └─────────────────────────────────────────────────────────┘                 │
│       ▲                                    ▲                                  │
│       │                                    │                                  │
│  Request 1: Borrow Conn 1           Request 3: Borrow Conn 3                 │
│  Request 2: Borrow Conn 2           Request 4: Wait (all busy)               │
│                                                                               │
│  (Each request pays ~0ms for already-open connection)                        │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### The Impact

| Metric | Without Pooling | With Pooling | Improvement |
|--------|-----------------|--------------|-------------|
| Connection time per request | 50-200ms | 0ms | **100x faster** |
| Max connections to DB | Unlimited (bad!) | Controlled | **Predictable** |
| Memory per connection | Wasted | Reused | **10x less RAM** |
| PostgreSQL processes | 1 per request | Fixed pool size | **Stable** |
| Latency at 1000 req/s | 200ms+ | 10ms | **20x faster** |

---

## Quick Start

### Minimal Setup

```python
from pynext.db import PostgresAdapter

# Just connect - pooling is automatic!
db = PostgresAdapter("postgresql://localhost/mydb")
await db.connect()

# Use it - connections are borrowed and returned automatically
user = await User.get(1)  # Borrows connection, returns when done

# Graceful shutdown
await db.disconnect()
```

### Production Setup

```python
from pynext.db import PostgresAdapter

db = PostgresAdapter(
    "postgresql://localhost/mydb",
    min_connections=10,    # Keep 10 warm connections
    max_connections=100,   # Scale up to 100 under load
    warmup=True,           # Pre-warm connections at startup
)
await db.connect()
```

That's it! PyNext handles:
- Creating connections on demand
- Returning connections when queries complete
- Scaling up under load
- Scaling down when idle
- Health checking
- Connection retirement

---

## Architecture Deep Dive

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PostgresAdapter                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                         AutoScalingPool                               │  │
│   │                                                                       │  │
│   │   ┌───────────────────────────────────────────────────────────────┐  │  │
│   │   │                    Connection Storage                          │  │  │
│   │   │                                                                │  │  │
│   │   │   ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐           │  │  │
│   │   │   │Conn 1│  │Conn 2│  │Conn 3│  │Conn 4│  │Conn 5│    ...    │  │  │
│   │   │   │ IDLE │  │ BUSY │  │ BUSY │  │ IDLE │  │ IDLE │           │  │  │
│   │   │   └──────┘  └──────┘  └──────┘  └──────┘  └──────┘           │  │  │
│   │   │                                                                │  │  │
│   │   └───────────────────────────────────────────────────────────────┘  │  │
│   │                                                                       │  │
│   │   ┌───────────────────────────────────────────────────────────────┐  │  │
│   │   │                    ConnectionQueue                             │  │  │
│   │   │                                                                │  │  │
│   │   │   When all connections are busy, requests wait here:          │  │  │
│   │   │   [req 1] → [req 2] → [req 3] → [req 4] → ...                 │  │  │
│   │   │                                                                │  │  │
│   │   │   Features:                                                    │  │  │
│   │   │   • FIFO ordering (fair)                                      │  │  │
│   │   │   • Priority levels (CRITICAL > NORMAL > BATCH)               │  │  │
│   │   │   • Timeout per request                                       │  │  │
│   │   │   • Backpressure signals                                      │  │  │
│   │   │                                                                │  │  │
│   │   └───────────────────────────────────────────────────────────────┘  │  │
│   │                                                                       │  │
│   │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │  │
│   │   │LifecycleManager │  │ConnectionWarmer │  │ ExternalPooler │      │  │
│   │   │                 │  │                 │  │                 │      │  │
│   │   │ • Tracks age    │  │ • Warmup query  │  │ • PgBouncer     │      │  │
│   │   │ • Tracks uses   │  │ • Parallel warm │  │ • pgpool        │      │  │
│   │   │ • Health checks │  │ • Retry logic   │  │ • Mode detect   │      │  │
│   │   │ • Retirement    │  │ • Statement prep│  │ • Feature compat│      │  │
│   │   └─────────────────┘  └─────────────────┘  └─────────────────┘      │  │
│   │                                                                       │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How a Request Flows Through the Pool

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Request Lifecycle                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  1. ACQUIRE REQUEST                                                           │
│     ─────────────────                                                         │
│                                                                               │
│     Your code:   user = await User.get(1)                                    │
│                         │                                                     │
│                         ▼                                                     │
│     Pool:        Check for idle connection                                    │
│                         │                                                     │
│             ┌───────────┴───────────┐                                        │
│             ▼                       ▼                                        │
│       Found idle?              No idle available                             │
│             │                       │                                        │
│             ▼                       ▼                                        │
│       Return it! ◄───────    Below max_connections?                         │
│       (< 1ms)                       │                                        │
│                         ┌───────────┴───────────┐                            │
│                         ▼                       ▼                            │
│                   Create new               At max capacity                   │
│                   connection               Enter queue                       │
│                   (~50-200ms)              (wait for release)                │
│                         │                       │                            │
│                         ▼                       ▼                            │
│                   Return it!               Wait with timeout...              │
│                                                  │                            │
│                                     ┌────────────┴────────────┐              │
│                                     ▼                         ▼              │
│                               Released!                   Timeout!           │
│                               Return it                   Raise error        │
│                                                                               │
│  ════════════════════════════════════════════════════════════════════════    │
│                                                                               │
│  2. USE CONNECTION                                                            │
│     ──────────────                                                            │
│                                                                               │
│     Connection borrowed ───► Execute query ───► Get results                  │
│                               (your SQL)         (< 1ms - 10s)               │
│                                                                               │
│  ════════════════════════════════════════════════════════════════════════    │
│                                                                               │
│  3. RELEASE CONNECTION                                                        │
│     ─────────────────                                                         │
│                                                                               │
│     Query complete ───► Check connection health                               │
│                                   │                                           │
│                      ┌────────────┴────────────┐                             │
│                      ▼                         ▼                             │
│                 Healthy?                   Unhealthy!                        │
│                      │                    Close & discard                    │
│         ┌────────────┴────────────┐                                          │
│         ▼                         ▼                                          │
│   Queue waiting?            Return to idle                                   │
│   Give to waiter            pool for next                                    │
│   (notify future)           request                                          │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Pool Sizing

### The Sizing Problem

Pool sizing is critical. Too small = requests wait. Too large = waste resources.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Pool Sizing Trade-offs                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  TOO SMALL (min=1, max=5)                                                     │
│  ────────────────────────                                                     │
│                                                                               │
│  Requests:  ████████████████████████████████████████  (100/sec)              │
│  Pool:      █████  (5 connections)                                           │
│  Queue:     ████████████████████████████████████████  (95 waiting!)          │
│                                                                               │
│  Result: High latency, timeouts, unhappy users                               │
│                                                                               │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                               │
│  TOO LARGE (min=100, max=500)                                                 │
│  ───────────────────────────                                                  │
│                                                                               │
│  Requests:  ████████████████████████████████████████  (100/sec)              │
│  Pool:      █████████████████████████████████████████████████████ (200 conn) │
│  Queue:     (empty - no waiting)                                              │
│                                                                               │
│  BUT: 1GB RAM wasted, PostgreSQL struggling with 200 processes               │
│                                                                               │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                               │
│  JUST RIGHT (min=10, max=50)                                                  │
│  ──────────────────────────                                                   │
│                                                                               │
│  Requests:  ████████████████████████████████████████  (100/sec)              │
│  Pool:      ██████████████████████████  (30 connections, auto-scaled)        │
│  Queue:     ██  (brief waits during spikes)                                  │
│                                                                               │
│  Result: Low latency, efficient resources, happy users                       │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Sizing Guidelines

| Workload | Requests/sec | min | max | Why |
|----------|-------------|-----|-----|-----|
| Development | < 10 | 1 | 5 | Minimal resources needed |
| Small app | < 100 | 5 | 20 | Low traffic, small DB |
| Medium app | < 1000 | 10 | 50 | Typical production app |
| Large app | < 10000 | 20 | 100 | High traffic, optimized queries |
| High-traffic | > 10000 | 50 | 200 | Enterprise scale |

### The Formula

PostgreSQL has a well-known formula for optimal connections:

```
max_connections = (core_count * 2) + effective_spindle_count
```

For most cloud VMs with SSDs:
- 4 cores → 10-15 connections
- 8 cores → 20-25 connections  
- 16 cores → 35-40 connections

**Why so few?** PostgreSQL is CPU-bound for queries. More connections than cores = context switching overhead. SSDs are fast enough that disk I/O rarely blocks.

### Auto-Scaling

PyNext pools scale automatically:

```python
db = PostgresAdapter(
    "postgresql://localhost/mydb",
    min_connections=5,      # Start with 5
    max_connections=50,     # Scale up to 50
    auto_scale=True,        # Enable auto-scaling (default)
    scale_up_threshold=0.8, # Scale up when 80% busy
    scale_down_timeout=60,  # Scale down after 60s idle
)
```

**How it works:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Auto-Scaling Behavior                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Time 0:00    Pool: █████ (5/5 = 100% busy)                                  │
│               → Scale up! Create 3 more connections                          │
│                                                                               │
│  Time 0:01    Pool: █████████ (5/8 = 62% busy)                               │
│               → Stable, no action                                            │
│                                                                               │
│  Time 0:30    Pool: █████████████████ (14/17 = 82% busy)                     │
│               → Scale up! Create 5 more connections                          │
│                                                                               │
│  Time 1:00    Pool: ██████████████████████ (8/22 = 36% busy)                 │
│               → Traffic dropped, but wait...                                 │
│                                                                               │
│  Time 2:00    Pool: ██████████████████████ (4/22 = 18% busy)                 │
│               → Still low after 60s, scale down to 10                        │
│                                                                               │
│  Time 2:01    Pool: ██████████ (4/10 = 40% busy)                             │
│               → Right-sized for current load                                 │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Queue Management

### Why Queuing?

When all connections are busy, new requests must wait. Without proper queuing:

```python
# Without queue management:
try:
    conn = await pool.acquire(timeout=30)  # Might timeout randomly
except asyncio.TimeoutError:
    # No idea why - no visibility, no fairness
    return "Database busy, try again"
```

### PyNext's Queue System

```python
from pynext.db.adapters import QueueConfig, QueueOverflowAction

db = PostgresAdapter(
    "postgresql://localhost/mydb",
    queue_config=QueueConfig(
        max_size=1000,           # Max 1000 waiting requests
        max_wait_time=30.0,      # Each waits max 30 seconds
        fairness="fifo",         # First-in-first-out (fair)
        overflow_action=QueueOverflowAction.REJECT,
        warn_threshold=100,      # Log warning at 100 waiting
        critical_threshold=500,  # Log error at 500 waiting
    ),
)
```

### Queue Fairness

**FIFO (First-In-First-Out)** - Default, fair:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              FIFO Queue                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Arrived:   09:00:00.000  09:00:00.050  09:00:00.100  09:00:00.150           │
│             ▼             ▼             ▼             ▼                       │
│  Queue:     [Request A] → [Request B] → [Request C] → [Request D]            │
│             (first out)                               (last out)              │
│                                                                               │
│  When connection available: Request A gets it (waited longest)               │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Priority Queue** - For critical paths:

```python
from pynext.db.adapters import QueueConfig, QueuePriority

db = PostgresAdapter(
    queue_config=QueueConfig(fairness="priority"),
)

# In your code:
async def health_check():
    # Critical - skip the line!
    async with db.acquire(priority=QueuePriority.CRITICAL):
        return await db.sql_val("SELECT 1")

async def background_sync():
    # Batch - wait patiently
    async with db.acquire(priority=QueuePriority.BATCH):
        return await sync_all_users()
```

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Priority Queue                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Priority Levels:                                                             │
│                                                                               │
│  0 - CRITICAL   │████████████████████████████│ Served first (health checks)  │
│  1 - HIGH       │██████████████████████│      User-facing APIs               │
│  2 - NORMAL     │████████████████│            Default priority               │
│  3 - LOW        │██████████│                  Background tasks               │
│  4 - BATCH      │████│                        Bulk operations                │
│                                                                               │
│  Queue with priorities:                                                       │
│                                                                               │
│  Position 1: [Request X - CRITICAL]   ← Gets next connection                 │
│  Position 2: [Request A - HIGH]                                               │
│  Position 3: [Request C - HIGH]                                               │
│  Position 4: [Request B - NORMAL]     ← Even though B arrived before C       │
│  Position 5: [Request D - BATCH]                                              │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Overflow Handling

When the queue is full, what happens to new requests?

```python
from pynext.db.adapters import QueueConfig, QueueOverflowAction

# Option 1: REJECT (default) - fail immediately with clear error
QueueConfig(
    max_size=1000,
    overflow_action=QueueOverflowAction.REJECT,
)
# Raises: QueueFullError("Queue is full (1000/1000). Consider scaling.")

# Option 2: DROP_OLDEST - sacrifice oldest waiter for new request
QueueConfig(
    max_size=1000,
    overflow_action=QueueOverflowAction.DROP_OLDEST,
)
# Oldest request in queue gets cancelled, new request enters

# Option 3: TIMEOUT_FASTEST - reduce timeouts for oldest requests
QueueConfig(
    max_size=1000,
    overflow_action=QueueOverflowAction.TIMEOUT_FASTEST,
)
# Oldest requests have their timeouts reduced to make room faster
```

### Backpressure Signals

The queue tells you when you're under pressure:

```python
# In your request handler:
@app.get("/api/users")
async def get_users():
    # Check if we should shed load
    if db.is_under_pressure:
        return Response(
            "System busy, please retry",
            status_code=503,
            headers={"Retry-After": "5"}
        )
    
    # Check specific thresholds
    if db.queue_depth > 100:
        logger.warning(f"Queue backing up: {db.queue_depth} waiting")
    
    return await User.all()
```

---

## Connection Lifecycle

### Why Lifecycle Management?

Connections aren't immortal. They can:
- Leak memory over time
- Accumulate stale session state
- Lose connection to the database
- Hold onto resources too long

### The Lifecycle States

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Connection Lifecycle                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  CREATED                                                                      │
│     │                                                                         │
│     ▼                                                                         │
│  ┌────────────┐                                                              │
│  │            │    ┌──────────────────────────────────────────────────┐     │
│  │   IDLE     │◄───┤  Connection available, waiting for work          │     │
│  │            │    └──────────────────────────────────────────────────┘     │
│  └─────┬──────┘                                                              │
│        │                                                                      │
│        │ acquire()                                                           │
│        ▼                                                                      │
│  ┌────────────┐                                                              │
│  │            │    ┌──────────────────────────────────────────────────┐     │
│  │   BUSY     │◄───┤  Connection in use, executing queries             │     │
│  │            │    └──────────────────────────────────────────────────┘     │
│  └─────┬──────┘                                                              │
│        │                                                                      │
│        │ release()                                                           │
│        ▼                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                        HEALTH CHECK                                  │     │
│  │                                                                      │     │
│  │  • Is connection still open?                                        │     │
│  │  • Did the last query succeed?                                      │     │
│  │  • Has soft lifetime been exceeded?                                 │     │
│  │  • Has use count limit been reached?                                │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│        │                                                                      │
│        ├──── Healthy ────► Return to IDLE                                   │
│        │                                                                      │
│        └──── Unhealthy ──► RETIRED                                          │
│                               │                                               │
│                               ▼                                               │
│                          Connection closed,                                   │
│                          new one created                                      │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Lifecycle Configuration

```python
from pynext.db.adapters import LifecycleConfig, ReplacementStrategy

db = PostgresAdapter(
    "postgresql://localhost/mydb",
    lifecycle_config=LifecycleConfig(
        # Lifetime limits
        max_lifetime=3600,        # HARD: Close after 1 hour (no exceptions)
        soft_lifetime=1800,       # SOFT: Prefer closing after 30min
        
        # Use count limits
        max_uses=10000,           # Close after 10000 queries
        
        # Health checking
        health_check_interval=30, # Check every 30 seconds
        health_check_timeout=5.0, # Health check must complete in 5s
        health_check_query="SELECT 1",  # Query to validate connection
        
        # Replacement behavior
        replacement_strategy=ReplacementStrategy.GRACEFUL,
        grace_period=30.0,        # Wait 30s for busy connection
    ),
)
```

### Soft vs Hard Lifetime

**Hard Lifetime**: Connection is ALWAYS closed after this time, even if healthy.

**Soft Lifetime**: Connection is PREFERRED for closing, but only when convenient.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     Soft vs Hard Lifetime                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Timeline for connection created at 00:00:00:                                │
│                                                                               │
│  00:00:00 ─────────────── CREATED ──────────────────────────────────────     │
│                                                                               │
│  00:30:00 ─────────────── SOFT LIMIT ───────────────────────────────────     │
│            │                                                                  │
│            │  If connection is idle → close it, create new                   │
│            │  If connection is busy → keep using, mark for replacement       │
│            │                                                                  │
│  00:45:00 ─────────────── (still running if was busy) ──────────────────     │
│            │                                                                  │
│            │  Connection marked for retirement                               │
│            │  Will be closed when next released                              │
│            │                                                                  │
│  01:00:00 ─────────────── HARD LIMIT ───────────────────────────────────     │
│            │                                                                  │
│            │  Connection MUST close now                                      │
│            │  If busy: wait grace_period, then force close                   │
│            │                                                                  │
│  01:00:30 ─────────────── GRACE EXPIRED ────────────────────────────────     │
│            │                                                                  │
│            │  Force close (may interrupt query)                              │
│            │  Log warning about forced closure                               │
│            │                                                                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Replacement Strategies

```python
from pynext.db.adapters import ReplacementStrategy

# GRACEFUL (default) - wait for connection to be released
LifecycleConfig(
    replacement_strategy=ReplacementStrategy.GRACEFUL,
    grace_period=30.0,  # Wait up to 30s
)
# Best for: Most applications. No query interruption.

# IMMEDIATE - close connection now (may interrupt queries!)
LifecycleConfig(
    replacement_strategy=ReplacementStrategy.IMMEDIATE,
)
# Best for: When you need strict lifetime enforcement.
# Warning: May cause query failures!

# LAZY - mark for replacement, close on next release
LifecycleConfig(
    replacement_strategy=ReplacementStrategy.LAZY,
)
# Best for: When you don't care exactly when it closes.
```

### Health Checks

Regular health checks detect dead connections before queries fail:

```python
LifecycleConfig(
    health_check_interval=30,     # Check every 30 seconds
    health_check_timeout=5.0,     # Must complete in 5 seconds
    health_check_query="SELECT 1",  # Simple validation query
)
```

**What health checks detect:**

| Issue | Detection | Result |
|-------|-----------|--------|
| Connection dropped | Query fails | Mark unhealthy, replace |
| Network timeout | Query times out | Mark unhealthy, replace |
| PostgreSQL restart | Connection invalid | Mark unhealthy, replace |
| Zombie connection | No response | Mark unhealthy, replace |

---

## Connection Warmup

### The Cold Start Problem

When a pool starts or scales up, connections are "cold" - they haven't been used yet:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Cold Start Impact                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Without Warmup:                                                              │
│  ────────────────                                                             │
│                                                                               │
│  Request 1: Connect (100ms) + Prepare statement (50ms) + Query (5ms) = 155ms │
│  Request 2: Connect (100ms) + Prepare statement (50ms) + Query (5ms) = 155ms │
│  ...                                                                          │
│  (First 10 requests all pay the cold start penalty)                          │
│                                                                               │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                               │
│  With Warmup:                                                                 │
│  ─────────────                                                                │
│                                                                               │
│  Startup: Create 10 connections, warm each with SELECT 1 (50ms total)        │
│                                                                               │
│  Request 1: Query (5ms) = 5ms                                                 │
│  Request 2: Query (5ms) = 5ms                                                 │
│  ...                                                                          │
│  (All requests get fast response immediately!)                               │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Warmup Configuration

```python
from pynext.db.adapters import WarmupConfig

db = PostgresAdapter(
    "postgresql://localhost/mydb",
    warmup_config=WarmupConfig(
        enabled=True,              # Enable warmup
        query="SELECT 1",          # Warmup query
        timeout=5.0,               # Timeout for warmup query
        parallel=True,             # Warm connections in parallel
        max_parallel=10,           # Max parallel warmup operations
        retry_on_failure=True,     # Retry failed warmups
        max_retries=3,             # Max retry attempts
        prepare_statements=[       # Pre-prepare common queries
            "SELECT * FROM users WHERE id = $1",
            "SELECT * FROM posts WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
        ],
    ),
)
```

### Simple Warmup Toggle

```python
# Just enable with defaults
db = PostgresAdapter(
    "postgresql://localhost/mydb",
    warmup=True,  # Uses default warmup query (SELECT 1)
)

# Or customize the query
db = PostgresAdapter(
    "postgresql://localhost/mydb",
    warmup=True,
    warmup_query="SELECT NOW()",  # Custom warmup query
)
```

### Parallel Warmup

For pools with many connections, parallel warmup is essential:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       Sequential vs Parallel Warmup                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Sequential (parallel=False):                                                 │
│  ───────────────────────────                                                  │
│                                                                               │
│  Time:  0ms      100ms     200ms     300ms     400ms     500ms               │
│         │         │         │         │         │         │                  │
│  Conn 1 ████████                                                              │
│  Conn 2          ████████                                                     │
│  Conn 3                   ████████                                            │
│  Conn 4                            ████████                                   │
│  Conn 5                                     ████████                          │
│                                                                               │
│  Total: 500ms to warm 5 connections                                          │
│                                                                               │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                               │
│  Parallel (parallel=True, max_parallel=5):                                   │
│  ─────────────────────────────────────────                                    │
│                                                                               │
│  Time:  0ms      100ms                                                        │
│         │         │                                                           │
│  Conn 1 ████████                                                              │
│  Conn 2 ████████                                                              │
│  Conn 3 ████████                                                              │
│  Conn 4 ████████                                                              │
│  Conn 5 ████████                                                              │
│                                                                               │
│  Total: 100ms to warm 5 connections (5x faster!)                             │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Statement Preparation

For maximum performance, pre-prepare your most common queries:

```python
warmup_config = WarmupConfig(
    prepare_statements=[
        "SELECT * FROM users WHERE id = $1",
        "SELECT * FROM posts WHERE author_id = $1 ORDER BY created_at DESC LIMIT $2",
        "INSERT INTO audit_log (user_id, action, timestamp) VALUES ($1, $2, $3)",
    ],
)
```

**Why prepare statements?**

| Query Type | First Execution | Subsequent Executions |
|------------|-----------------|----------------------|
| Unprepared | Parse (1ms) + Plan (2ms) + Execute (5ms) = 8ms | Parse (1ms) + Plan (2ms) + Execute (5ms) = 8ms |
| Prepared | Prepare (3ms) | Execute (5ms) = 5ms |

For frequently-executed queries, preparation saves 3ms per query!

---

## External Poolers

### What is an External Pooler?

External poolers like PgBouncer sit between your app and PostgreSQL, providing an additional layer of connection management:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       External Pooler Architecture                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  WITHOUT External Pooler:                                                     │
│  ─────────────────────────                                                    │
│                                                                               │
│  Your App ─────────────────────────────────────────────► PostgreSQL          │
│  (1 conn)                                                  (1 backend)       │
│                                                                               │
│  Scale to 10 servers:                                                         │
│  Server 1 (50 conn) ─┐                                                        │
│  Server 2 (50 conn) ─┼─────────────────────────────────► PostgreSQL          │
│  ...                 │                                    (500 backends!)    │
│  Server 10 (50 conn)─┘                                                        │
│                                                                               │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                               │
│  WITH External Pooler (PgBouncer):                                           │
│  ─────────────────────────────────                                            │
│                                                                               │
│  Server 1 (50 conn) ─┐                                                        │
│  Server 2 (50 conn) ─┼─────► PgBouncer ─────────────────► PostgreSQL         │
│  ...                 │      (multiplexes)                 (20 backends)       │
│  Server 10 (50 conn)─┘                                                        │
│                                                                               │
│  500 app connections → 20 PostgreSQL connections (25x reduction!)            │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Why Use External Poolers?

| Scenario | Benefit |
|----------|---------|
| Many app servers | Consolidate connections (500 → 20) |
| PostgreSQL connection limits | Stay under max_connections |
| Short-lived connections | Pool at infrastructure level |
| Serverless (Lambda, etc) | Persistent connections despite ephemeral workers |
| Supabase, Neon, Render | Required for their managed pooling |

### PgBouncer Modes

```python
from pynext.db.adapters import ExternalPoolerConfig, PoolerType, PoolerMode

# Transaction Mode (most common, most scalable)
db = PostgresAdapter(
    "postgresql://localhost:6432/mydb",
    external_pooler=ExternalPoolerConfig(
        enabled=True,
        type=PoolerType.PGBOUNCER,
        mode=PoolerMode.TRANSACTION,
    ),
)
```

| Mode | Connection Reuse | Features Supported | Best For |
|------|-----------------|-------------------|----------|
| **TRANSACTION** | Per transaction | Basic queries only | High throughput, many clients |
| **SESSION** | Per client session | All PostgreSQL features | Features that need session state |
| **STATEMENT** | Per statement | Nothing (legacy) | Ancient apps only |

### Feature Compatibility Matrix

| Feature | Transaction Mode | Session Mode |
|---------|-----------------|--------------|
| Simple queries | ✅ | ✅ |
| Transactions | ✅ | ✅ |
| Prepared statements | ❌ | ✅ |
| Server-side cursors | ❌ | ✅ |
| LISTEN/NOTIFY | ❌ | ✅ |
| SET session variables | ❌ | ✅ |
| Advisory locks | ❌ | ✅ |
| Temp tables | ❌ | ✅ |

### Platform-Specific Helpers

```python
from pynext.db.adapters import (
    create_pooler_config_for_supabase,
    create_pooler_config_for_render,
    create_pooler_config_for_neon,
)

# Supabase - automatically configured for their pooler
db = PostgresAdapter(
    os.environ["SUPABASE_DB_URL"],
    external_pooler=create_pooler_config_for_supabase(),
)

# Render - automatically configured
db = PostgresAdapter(
    os.environ["RENDER_DB_URL"],
    external_pooler=create_pooler_config_for_render(),
)

# Neon - automatically configured
db = PostgresAdapter(
    os.environ["NEON_DB_URL"],
    external_pooler=create_pooler_config_for_neon(),
)
```

### Auto-Detection

PyNext can auto-detect if you're connecting through an external pooler:

```python
db = PostgresAdapter(
    "postgresql://localhost:6432/mydb",
    external_pooler=ExternalPoolerConfig(
        auto_detect=True,  # Detect pooler type automatically
    ),
)

# After connecting:
if db.external_pooler_detected:
    print(f"Detected {db.external_pooler_type} in {db.external_pooler_mode} mode")
```

---

## Monitoring & Metrics

### Pool Statistics

```python
# Get comprehensive pool stats
stats = db.get_pool_stats()

print(f"Pool size: {stats.size}")           # Total connections
print(f"Busy: {stats.busy}")                 # Currently in use
print(f"Idle: {stats.idle}")                 # Available for use
print(f"Waiting: {stats.waiting}")           # Requests in queue
print(f"Utilization: {stats.busy / stats.size:.1%}")  # Capacity used

# Queue metrics
print(f"Queue depth: {stats.queue_depth}")
print(f"Queue wait avg: {stats.queue_wait_avg_ms:.1f}ms")
print(f"Queue wait p50: {stats.queue_wait_p50_ms:.1f}ms")
print(f"Queue wait p99: {stats.queue_wait_p99_ms:.1f}ms")

# Health
print(f"Warmup success rate: {stats.warmup_success_rate:.1%}")
print(f"Under pressure: {stats.is_under_pressure}")
```

### Queue Statistics

```python
queue_stats = db.get_queue_stats()

print(f"Current depth: {queue_stats.depth}")
print(f"Total enqueued: {queue_stats.total_enqueued}")
print(f"Total dequeued: {queue_stats.total_dequeued}")
print(f"Total timeouts: {queue_stats.total_timeouts}")
print(f"Total rejections: {queue_stats.total_rejections}")
print(f"Total cancellations: {queue_stats.total_cancellations}")

# Wait time distribution
print(f"Wait time p50: {queue_stats.wait_time_p50_ms:.1f}ms")
print(f"Wait time p95: {queue_stats.wait_time_p95_ms:.1f}ms")
print(f"Wait time p99: {queue_stats.wait_time_p99_ms:.1f}ms")
```

### Lifecycle Statistics

```python
lifecycle_stats = db.get_lifecycle_stats()

print(f"Connections created: {lifecycle_stats.total_connections_created}")
print(f"Connections retired: {lifecycle_stats.total_connections_retired}")
print(f"Avg lifetime: {lifecycle_stats.avg_connection_lifetime_ms / 1000:.0f}s")
print(f"Avg uses per connection: {lifecycle_stats.avg_connection_uses:.0f}")
print(f"Health checks performed: {lifecycle_stats.health_checks_performed}")
print(f"Health checks failed: {lifecycle_stats.health_checks_failed}")

# Retirement breakdown
print(f"Retirements by reason: {lifecycle_stats.retirements_by_reason}")
# {'soft_lifetime': 45, 'hard_lifetime': 12, 'max_uses': 8, 'health_check_failed': 3}
```

### Warmup Statistics

```python
warmup_stats = db.get_warmup_stats()

print(f"Total warmups: {warmup_stats.total_warmups}")
print(f"Successful: {warmup_stats.successful_warmups}")
print(f"Failed: {warmup_stats.failed_warmups}")
print(f"Success rate: {warmup_stats.success_rate:.1%}")
print(f"Avg duration: {warmup_stats.avg_duration_ms:.1f}ms")
print(f"Max duration: {warmup_stats.max_duration_ms:.1f}ms")
```

### Prometheus Integration

```python
from prometheus_client import Gauge, Counter, Histogram

# Create metrics
pool_size = Gauge('db_pool_size', 'Total connections in pool')
pool_busy = Gauge('db_pool_busy', 'Busy connections')
pool_queue_depth = Gauge('db_pool_queue_depth', 'Requests waiting for connection')
pool_queue_wait = Histogram('db_pool_queue_wait_seconds', 'Queue wait time')

# Update in a background task
async def update_metrics():
    while True:
        stats = db.get_pool_stats()
        pool_size.set(stats.size)
        pool_busy.set(stats.busy)
        pool_queue_depth.set(stats.queue_depth)
        await asyncio.sleep(1)
```

---

## Production Configuration

### Recommended Production Settings

```python
from pynext.db import PostgresAdapter
from pynext.db.adapters import (
    QueueConfig,
    LifecycleConfig,
    WarmupConfig,
    ExternalPoolerConfig,
    PoolerType,
    PoolerMode,
    QueueOverflowAction,
    ReplacementStrategy,
)
import os

db = PostgresAdapter(
    os.environ["DATABASE_URL"],
    
    # Pool sizing
    min_connections=10,         # Warm pool
    max_connections=100,        # Scale under load
    auto_scale=True,            # Adapt to traffic
    
    # Timeouts
    acquire_timeout=30.0,       # Wait for connection
    connect_timeout=10.0,       # Establish connection
    command_timeout=60.0,       # Query timeout
    
    # Queue management
    queue_config=QueueConfig(
        max_size=1000,
        max_wait_time=30.0,
        fairness="fifo",
        overflow_action=QueueOverflowAction.REJECT,
        warn_threshold=100,
        critical_threshold=500,
    ),
    
    # Lifecycle management
    lifecycle_config=LifecycleConfig(
        max_lifetime=3600,          # 1 hour hard limit
        soft_lifetime=1800,         # 30 min soft limit
        max_uses=10000,             # Retire after 10k queries
        health_check_interval=30,   # Check every 30s
        health_check_timeout=5.0,
        replacement_strategy=ReplacementStrategy.GRACEFUL,
        grace_period=30.0,
    ),
    
    # Warmup
    warmup_config=WarmupConfig(
        enabled=True,
        parallel=True,
        max_parallel=10,
        retry_on_failure=True,
        max_retries=3,
    ),
    
    # External pooler (if applicable)
    external_pooler=ExternalPoolerConfig(
        auto_detect=True,
    ),
)

await db.connect()
```

### Environment-Specific Configurations

```python
import os

# Development
if os.environ.get("ENV") == "development":
    db = PostgresAdapter(
        "postgresql://localhost/mydb_dev",
        min_connections=1,
        max_connections=5,
        warmup=False,  # Faster startup
    )

# Staging
elif os.environ.get("ENV") == "staging":
    db = PostgresAdapter(
        os.environ["DATABASE_URL"],
        min_connections=5,
        max_connections=20,
        warmup=True,
    )

# Production
else:
    db = PostgresAdapter(
        os.environ["DATABASE_URL"],
        min_connections=10,
        max_connections=100,
        warmup=True,
        warmup_config=WarmupConfig(
            parallel=True,
            prepare_statements=[
                "SELECT * FROM users WHERE id = $1",
            ],
        ),
    )
```

---

## Performance Tuning

### Connection Acquisition Time

The most important metric. Should be < 5ms for 99% of requests.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Connection Acquisition Targets                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Excellent:    p99 < 1ms    │ Pool has idle connections                      │
│  Good:         p99 < 5ms    │ Occasional scaling                             │
│  Acceptable:   p99 < 20ms   │ Some queuing during peaks                      │
│  Problematic:  p99 < 100ms  │ Frequent queuing, consider scaling             │
│  Critical:     p99 > 100ms  │ Pool undersized or query issues                │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Optimization steps:**

1. Increase `min_connections` to reduce cold starts
2. Increase `max_connections` if pool is often at capacity
3. Enable warmup to reduce first-query latency
4. Check for slow queries holding connections too long

### Queue Wait Time

Should approach zero for healthy systems.

```python
# Healthy queue metrics:
queue_stats = db.get_queue_stats()

if queue_stats.wait_time_p99_ms > 100:
    # 99th percentile > 100ms is concerning
    logger.warning(f"Queue wait time high: {queue_stats.wait_time_p99_ms}ms")
    
if queue_stats.total_timeouts > 0:
    # Any timeouts indicate insufficient capacity
    logger.error(f"Queue timeouts detected: {queue_stats.total_timeouts}")
```

### Connection Utilization

Target 60-80% utilization at peak load.

```python
stats = db.get_pool_stats()
utilization = stats.busy / stats.size

if utilization > 0.9:
    # 90%+ sustained = scale up
    logger.warning(f"Pool utilization high: {utilization:.1%}")
    
if utilization < 0.3:
    # 30% sustained = scale down
    logger.info(f"Pool utilization low: {utilization:.1%}")
```

---

## Troubleshooting

### PoolExhaustedError

```
PoolExhaustedError: Timeout waiting for connection after 30.0s.
Pool stats: {'size': 100, 'busy': 100, 'waiting': 500}
```

**Causes:**
1. `max_connections` too low for traffic
2. Slow queries holding connections
3. Connection leak (not releasing connections)

**Solutions:**
```python
# 1. Increase pool size
db = PostgresAdapter(max_connections=200)

# 2. Increase timeout
db = PostgresAdapter(acquire_timeout=60.0)

# 3. Find slow queries
lifecycle_stats = db.get_lifecycle_stats()
print(f"Avg uses: {lifecycle_stats.avg_connection_uses}")  # Low = queries taking too long

# 4. Check for leaks - use context manager
async with db.acquire() as conn:  # Always releases
    await conn.fetch(...)
# Don't do: conn = await db.acquire()  # Might not release!
```

### QueueFullError

```
QueueFullError: Connection queue is full (1000/1000 requests waiting).
Consider increasing pool size or queue size.
```

**Causes:**
1. Sustained high traffic
2. Pool can't scale fast enough
3. Database overloaded

**Solutions:**
```python
# 1. Increase queue size
db = PostgresAdapter(
    queue_config=QueueConfig(max_size=5000)
)

# 2. Add load shedding
@app.middleware
async def shed_load(request, call_next):
    if db.is_under_pressure:
        return Response(status_code=503, headers={"Retry-After": "5"})
    return await call_next(request)

# 3. Scale horizontally (more app servers)
```

### QueueTimeoutError

```
QueueTimeoutError: Timed out waiting for connection after 30.0s.
Position in queue: 847, queue depth: 1000.
```

**Causes:**
1. Queue too long
2. Connections too slow
3. Not enough connections

**Solutions:**
```python
# 1. Reduce wait time (fail fast)
QueueConfig(max_wait_time=10.0)

# 2. Priority for critical requests
async with db.acquire(priority=QueuePriority.CRITICAL):
    ...

# 3. Increase pool capacity
db = PostgresAdapter(max_connections=200)
```

### Connection Leaks

**Symptoms:**
- `total_connections_created` keeps growing
- `busy` count high even during low traffic
- Pool never scales down

**Detection:**
```python
stats = db.get_lifecycle_stats()
leak_count = stats.total_connections_created - stats.total_connections_retired

if leak_count > 10:
    logger.error(f"Possible connection leak: {leak_count} connections not retired")
```

**Prevention:**
```python
# ALWAYS use context manager
async with db.acquire() as conn:
    result = await conn.fetch("SELECT * FROM users")
    return result  # Connection automatically released

# NOT this:
conn = await db.acquire()
result = await conn.fetch("SELECT * FROM users")
# If exception occurs here, connection is leaked!
await db.release(conn)
```

### Health Check Failures

**Symptoms:**
- `health_checks_failed` increasing
- Connections being retired frequently

**Investigation:**
```python
stats = db.get_lifecycle_stats()
print(f"Health checks: {stats.health_checks_performed}")
print(f"Failures: {stats.health_checks_failed}")
print(f"Failure rate: {stats.health_checks_failed / stats.health_checks_performed:.1%}")

if stats.health_checks_failed > 10:
    # Check database connectivity
    # Check network stability
    # Check PostgreSQL logs
```

**Solutions:**
```python
# More lenient health checks
LifecycleConfig(
    health_check_interval=60,  # Less frequent
    health_check_timeout=10.0,  # Longer timeout
)
```

---

## API Reference

### PostgresAdapter

```python
PostgresAdapter(
    # Connection
    url: str = None,                           # Connection URL
    host: str = "localhost",                   # Database host
    port: int = 5432,                          # Database port
    database: str = None,                      # Database name
    user: str = None,                          # Username
    password: str = None,                      # Password
    
    # Pool sizing
    min_connections: int = 5,                  # Minimum pool size
    max_connections: int = 50,                 # Maximum pool size
    auto_scale: bool = True,                   # Enable auto-scaling
    
    # Timeouts
    acquire_timeout: float = 30.0,             # Wait for connection
    connect_timeout: float = 10.0,             # Establish connection
    command_timeout: float = 60.0,             # Query timeout
    
    # Components
    queue_config: QueueConfig = None,          # Queue configuration
    lifecycle_config: LifecycleConfig = None,  # Lifecycle configuration
    warmup_config: WarmupConfig = None,        # Warmup configuration
    external_pooler: ExternalPoolerConfig = None,  # External pooler
    
    # Shortcuts
    warmup: bool = False,                      # Enable warmup with defaults
    warmup_query: str = "SELECT 1",            # Warmup query
)
```

### QueueConfig

```python
QueueConfig(
    max_size: int = 1000,                      # Max waiting requests
    max_wait_time: float = 30.0,               # Timeout per request
    fairness: str = "fifo",                    # "fifo" or "priority"
    overflow_action: QueueOverflowAction = REJECT,  # When full
    track_wait_times: bool = True,             # Track statistics
    warn_threshold: int = 100,                 # Warning level
    critical_threshold: int = 500,             # Critical level
)
```

### LifecycleConfig

```python
LifecycleConfig(
    max_lifetime: float = 3600,                # Hard lifetime limit (seconds)
    soft_lifetime: float = 1800,               # Soft lifetime limit
    max_uses: int = 10000,                     # Max queries per connection
    health_check_interval: float = 30,         # Seconds between checks
    health_check_timeout: float = 5.0,         # Check timeout
    health_check_query: str = "SELECT 1",      # Validation query
    replacement_strategy: ReplacementStrategy = GRACEFUL,
    grace_period: float = 30.0,                # Wait before force close
)
```

### WarmupConfig

```python
WarmupConfig(
    enabled: bool = True,                      # Enable warmup
    query: str = "SELECT 1",                   # Warmup query
    timeout: float = 5.0,                      # Query timeout
    parallel: bool = True,                     # Parallel warmup
    max_parallel: int = 10,                    # Max concurrent warmups
    retry_on_failure: bool = True,             # Retry failed warmups
    max_retries: int = 3,                      # Max retries
    prepare_statements: List[str] = [],        # Statements to prepare
)
```

### ExternalPoolerConfig

```python
ExternalPoolerConfig(
    enabled: bool = False,                     # Enable external pooler mode
    type: PoolerType = None,                   # PGBOUNCER, PGPOOL, ODYSSEY
    mode: PoolerMode = TRANSACTION,            # TRANSACTION, SESSION, STATEMENT
    auto_detect: bool = True,                  # Detect pooler automatically
    disable_prepared_statements: bool = None,  # Auto-set based on mode
    connection_validation_query: str = None,   # Custom validation
)
```

---

## See Also

- [PostgreSQL Adapter](./02-getting-started.md) - Core PostgreSQL functionality
- [Database Overview](./01-fundamentals.md) - Full Data Layer documentation
- [Migrations](./03-migrations.md) - Schema migration system
