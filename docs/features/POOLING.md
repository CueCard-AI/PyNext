# Connection Pooling (Phase 5.2)

High-performance connection pooling for PostgreSQL with intelligent sizing, external pooler support, advanced queuing, and comprehensive monitoring.

## Quick Start

```python
from pynext.db import PostgresAdapter

# Basic pooling (auto-configured)
db = PostgresAdapter("postgresql://localhost/mydb")

# Production pooling
db = PostgresAdapter(
    "postgresql://localhost/mydb",
    min_connections=10,
    max_connections=100,
    warmup=True,  # Pre-warm connections
)
await db.connect()
```

---

## How Connection Pooling Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PostgresAdapter                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     AutoScalingPool                              │   │
│   │                                                                  │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│   │   │  Conn   │  │  Conn   │  │  Conn   │  │  Conn   │  ...      │   │
│   │   │  (idle) │  │ (busy)  │  │ (busy)  │  │  (idle) │           │   │
│   │   └─────────┘  └─────────┘  └─────────┘  └─────────┘           │   │
│   │                                                                  │   │
│   │   ┌─────────────────────────────────────────────────────────┐   │   │
│   │   │                  ConnectionQueue                         │   │   │
│   │   │   [request] → [request] → [request] → ...              │   │   │
│   │   │   (FIFO order, fair queuing)                            │   │   │
│   │   └─────────────────────────────────────────────────────────┘   │   │
│   │                                                                  │   │
│   │   ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐   │   │
│   │   │LifecycleManager│  │ConnectionWarmer│  │ExternalPooler   │   │   │
│   │   │ (soft/hard     │  │ (pre-warm on   │  │ (PgBouncer,     │   │   │
│   │   │  retirement)   │  │  startup)      │  │  pgpool)        │   │   │
│   │   └────────────────┘  └────────────────┘  └─────────────────┘   │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Flow:**
1. Request arrives → Pool checks for idle connection
2. If available → Return immediately
3. If pool not at max → Create new connection
4. If pool at max → Enter queue (FIFO)
5. When connection released → Notify queue
6. Lifecycle manager retires old connections
7. Warmer keeps connections hot

---

## API Reference

### Basic Configuration

```python
from pynext.db import PostgresAdapter

# Minimal
db = PostgresAdapter("postgresql://localhost/mydb")

# With pool sizing
db = PostgresAdapter(
    "postgresql://localhost/mydb",
    min_connections=5,    # Keep 5 connections warm
    max_connections=50,   # Scale up to 50 under load
    auto_scale=True,      # Enable auto-scaling (default)
)

# With timeouts
db = PostgresAdapter(
    "postgresql://localhost/mydb",
    acquire_timeout=30.0,   # Max time to wait for connection
    connect_timeout=10.0,   # Max time to establish connection
    command_timeout=60.0,   # Max time per query
)
```

### Queue Configuration

```python
from pynext.db.adapters import QueueConfig, QueueOverflowAction

db = PostgresAdapter(
    "postgresql://localhost/mydb",
    queue_config=QueueConfig(
        max_size=1000,           # Max waiting requests
        max_wait_time=30.0,      # Timeout per request
        fairness="fifo",         # FIFO or "priority"
        overflow_action=QueueOverflowAction.REJECT,  # What to do when full
        warn_threshold=100,      # Log warning at this depth
        critical_threshold=500,  # Log error at this depth
    ),
)
```

**Overflow Actions:**
- `REJECT` (default): Immediately raise `QueueFullError`
- `DROP_OLDEST`: Remove oldest waiting request to make room
- `TIMEOUT_FASTEST`: Reduce timeout for oldest requests

### Priority Queue

```python
from pynext.db.adapters import QueueConfig, QueuePriority

db = PostgresAdapter(
    queue_config=QueueConfig(fairness="priority"),
)

# High-priority request
stats = pool.get_stats()  # Critical query

# Background task - can wait
await pool.enqueue(priority=QueuePriority.BATCH)
```

**Priority Levels:**
- `CRITICAL` (0): System-critical queries
- `HIGH` (1): Important user-facing queries
- `NORMAL` (2): Default priority
- `LOW` (3): Background tasks
- `BATCH` (4): Bulk operations

### Lifecycle Configuration

```python
from pynext.db.adapters import LifecycleConfig, ReplacementStrategy

db = PostgresAdapter(
    "postgresql://localhost/mydb",
    lifecycle_config=LifecycleConfig(
        max_lifetime=3600,        # Hard limit: close after 1 hour
        soft_lifetime=1800,       # Soft limit: prefer close after 30min
        max_uses=10000,           # Close after 10000 uses
        health_check_interval=30, # Check connection health every 30s
        health_check_timeout=5.0, # Timeout for health check query
        health_check_query="SELECT 1",  # Query to validate connection
        replacement_strategy=ReplacementStrategy.GRACEFUL,
        grace_period=30.0,        # Wait 30s before force-closing
    ),
)
```

**Replacement Strategies:**
- `GRACEFUL` (default): Wait for connection to be released before closing
- `IMMEDIATE`: Close immediately (may interrupt queries)
- `LAZY`: Mark for replacement, close on next release

### Warmup Configuration

```python
from pynext.db.adapters import WarmupConfig

db = PostgresAdapter(
    "postgresql://localhost/mydb",
    warmup_config=WarmupConfig(
        enabled=True,              # Enable warmup
        query="SELECT 1",          # Query to run
        timeout=5.0,               # Timeout for warmup query
        parallel=True,             # Warm connections in parallel
        max_parallel=10,           # Max parallel warmup operations
        retry_on_failure=True,     # Retry failed warmups
        max_retries=3,             # Max retry attempts
        prepare_statements=[       # Statements to prepare
            "SELECT * FROM users WHERE id = $1",
            "SELECT * FROM posts WHERE user_id = $1",
        ],
    ),
)

# Simple warmup toggle
db = PostgresAdapter(
    "postgresql://localhost/mydb",
    warmup=True,           # Enable with defaults
    warmup_query="SELECT NOW()",  # Custom query
)
```

### External Pooler Configuration

```python
from pynext.db.adapters import (
    ExternalPoolerConfig,
    PoolerType,
    PoolerMode,
    create_pooler_config_for_supabase,
)

# PgBouncer transaction mode
db = PostgresAdapter(
    "postgresql://localhost:6432/mydb",
    external_pooler=ExternalPoolerConfig(
        enabled=True,
        type=PoolerType.PGBOUNCER,
        mode=PoolerMode.TRANSACTION,
        auto_detect=False,  # We know it's PgBouncer
    ),
)

# Supabase (pre-configured)
db = PostgresAdapter(
    "postgresql://...",
    external_pooler=create_pooler_config_for_supabase(),
)
```

**Pooler Types:**
- `PGBOUNCER`: PgBouncer - lightweight, high-performance
- `PGPOOL`: pgpool-II - feature-rich, supports replication
- `ODYSSEY`: Odyssey - modern, multi-threaded

**Pooler Modes:**
- `TRANSACTION`: New DB connection per transaction (most scalable)
- `SESSION`: Dedicated DB connection per client (full features)
- `STATEMENT`: New DB connection per statement (legacy)

---

## Monitoring

### Pool Statistics

```python
stats = db.get_pool_stats()

print(f"Size: {stats.size}")
print(f"Busy: {stats.busy}")
print(f"Idle: {stats.idle}")
print(f"Waiting: {stats.waiting}")
print(f"Utilization: {stats.busy / stats.size:.1%}")

# Phase 5.2 additions
print(f"Queue depth: {stats.queue_depth}")
print(f"Queue wait avg: {stats.queue_wait_avg_ms:.1f}ms")
print(f"Queue wait p99: {stats.queue_wait_p99_ms:.1f}ms")
print(f"Warmup success rate: {stats.warmup_success_rate:.1%}")
print(f"Under pressure: {stats.is_under_pressure}")
```

### Queue Statistics

```python
queue_stats = db.get_queue_stats()

print(f"Depth: {queue_stats.depth}")
print(f"Total enqueued: {queue_stats.total_enqueued}")
print(f"Total dequeued: {queue_stats.total_dequeued}")
print(f"Total timeouts: {queue_stats.total_timeouts}")
print(f"Total rejections: {queue_stats.total_rejections}")
print(f"Wait time p50: {queue_stats.wait_time_p50_ms:.1f}ms")
print(f"Wait time p99: {queue_stats.wait_time_p99_ms:.1f}ms")
```

### Lifecycle Statistics

```python
lifecycle_stats = db.get_lifecycle_stats()

print(f"Created: {lifecycle_stats.total_connections_created}")
print(f"Retired: {lifecycle_stats.total_connections_retired}")
print(f"Avg lifetime: {lifecycle_stats.avg_connection_lifetime_ms:.0f}ms")
print(f"Avg uses: {lifecycle_stats.avg_connection_uses:.0f}")
print(f"Health checks failed: {lifecycle_stats.health_checks_failed}")
print(f"Retirements by reason: {lifecycle_stats.retirements_by_reason}")
```

### Warmup Statistics

```python
warmup_stats = db.get_warmup_stats()

print(f"Total warmups: {warmup_stats.total_warmups}")
print(f"Successful: {warmup_stats.successful_warmups}")
print(f"Failed: {warmup_stats.failed_warmups}")
print(f"Success rate: {warmup_stats.success_rate:.1%}")
print(f"Avg duration: {warmup_stats.avg_duration_ms:.1f}ms")
```

### Backpressure Detection

```python
# Check if system is under pressure
if db.is_under_pressure:
    return Response("System busy, try again", status=503)

# Check queue depth
if db.queue_depth > 100:
    logger.warning(f"Queue backing up: {db.queue_depth}")
```

---

## External Poolers

### PgBouncer Setup

```
# pgbouncer.ini
[databases]
mydb = host=localhost port=5432 dbname=mydb

[pgbouncer]
listen_port = 6432
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

```python
# PyNext configuration
db = PostgresAdapter(
    "postgresql://localhost:6432/mydb",
    external_pooler=ExternalPoolerConfig(
        enabled=True,
        type=PoolerType.PGBOUNCER,
        mode=PoolerMode.TRANSACTION,
    ),
)
```

### Feature Compatibility

| Feature | Transaction Mode | Session Mode |
|---------|-----------------|--------------|
| Prepared statements | ❌ | ✅ |
| Server-side cursors | ❌ | ✅ |
| LISTEN/NOTIFY | ❌ | ✅ |
| SET session variables | ❌ | ✅ |
| Query throughput | High | Medium |

### Platform Helpers

```python
from pynext.db.adapters import (
    create_pooler_config_for_supabase,
    create_pooler_config_for_render,
    create_pooler_config_for_neon,
)

# Supabase
db = PostgresAdapter(
    os.environ["SUPABASE_DB_URL"],
    external_pooler=create_pooler_config_for_supabase(),
)

# Render
db = PostgresAdapter(
    os.environ["RENDER_DB_URL"],
    external_pooler=create_pooler_config_for_render(),
)

# Neon
db = PostgresAdapter(
    os.environ["NEON_DB_URL"],
    external_pooler=create_pooler_config_for_neon(),
)
```

---

## Performance Tuning

### Pool Sizing Guidelines

| Workload | min_connections | max_connections |
|----------|-----------------|-----------------|
| Development | 1 | 5 |
| Small app (< 100 req/s) | 5 | 20 |
| Medium app (< 1000 req/s) | 10 | 50 |
| Large app (< 10000 req/s) | 20 | 100 |
| High-traffic (> 10000 req/s) | 50 | 200 |

**Formula:** `max_connections = (cores * 2) + effective_spindle_count`

### Queue Sizing

```python
# For API endpoints
queue_config = QueueConfig(
    max_size=1000,        # Allow 1000 waiting requests
    max_wait_time=30.0,   # 30s timeout
    warn_threshold=100,   # Warn at 100 waiting
)

# For background jobs (can wait longer)
queue_config = QueueConfig(
    max_size=10000,
    max_wait_time=300.0,  # 5 min timeout
    warn_threshold=1000,
)
```

### Warmup for Cold Starts

```python
# Lambda/serverless: aggressive warmup
warmup_config = WarmupConfig(
    enabled=True,
    timeout=2.0,           # Fast timeout
    parallel=True,
    prepare_statements=[   # Pre-warm hot paths
        "SELECT * FROM users WHERE id = $1",
    ],
)

# Long-running server: optional warmup
warmup_config = WarmupConfig(
    enabled=False,  # Let connections warm naturally
)
```

---

## Troubleshooting

### Common Errors

**PoolExhaustedError**
```
Timeout waiting for connection after 30.0s.
Pool stats: {'size': 100, 'busy': 100, 'waiting': 500}
```

**Fixes:**
1. Increase `max_connections`
2. Increase `acquire_timeout`
3. Optimize slow queries
4. Add backpressure at application level

**QueueFullError**
```
Connection queue is full (1000/1000 requests waiting)
```

**Fixes:**
1. Increase `queue_config.max_size`
2. Add load shedding (return 503)
3. Scale horizontally

**QueueTimeoutError**
```
Timed out waiting for connection after 30.0s
```

**Fixes:**
1. Increase `queue_config.max_wait_time`
2. Add more connections
3. Check for connection leaks

### Connection Leaks

```python
# Enable lifecycle tracking
db = PostgresAdapter(
    "postgresql://localhost/mydb",
    lifecycle_config=LifecycleConfig(
        max_lifetime=300,  # Short lifetime for debugging
        max_uses=100,      # Low use count
    ),
)

# Monitor for leaks
stats = db.get_lifecycle_stats()
if stats.total_connections_created - stats.total_connections_retired > 100:
    logger.warning("Possible connection leak!")
```

### Health Check Failures

```python
# Aggressive health checking
lifecycle_config = LifecycleConfig(
    health_check_interval=10,  # Check every 10s
    health_check_timeout=2.0,  # Fast timeout
)

# Monitor failures
stats = db.get_lifecycle_stats()
if stats.health_checks_failed > 10:
    logger.error("Many health check failures - check database")
```

---

## Complete Example

```python
from pynext.db import PostgresAdapter
from pynext.db.adapters import (
    QueueConfig,
    LifecycleConfig,
    WarmupConfig,
    ExternalPoolerConfig,
    PoolerType,
    PoolerMode,
)

# Production configuration
db = PostgresAdapter(
    os.environ["DATABASE_URL"],
    
    # Pool sizing
    min_connections=10,
    max_connections=100,
    auto_scale=True,
    
    # Timeouts
    acquire_timeout=30.0,
    connect_timeout=10.0,
    command_timeout=60.0,
    
    # Queue management
    queue_config=QueueConfig(
        max_size=1000,
        max_wait_time=30.0,
        warn_threshold=100,
        critical_threshold=500,
    ),
    
    # Lifecycle management
    lifecycle_config=LifecycleConfig(
        max_lifetime=3600,
        soft_lifetime=1800,
        max_uses=10000,
        health_check_interval=30,
    ),
    
    # Connection warmup
    warmup_config=WarmupConfig(
        enabled=True,
        parallel=True,
        max_parallel=10,
    ),
    
    # External pooler (if using)
    external_pooler=ExternalPoolerConfig(
        enabled=True,
        type=PoolerType.PGBOUNCER,
        mode=PoolerMode.TRANSACTION,
    ),
)

await db.connect()

# Use normally
users = await User.all()

# Monitor
stats = db.get_pool_stats()
print(f"Pool: {stats.busy}/{stats.size}, Queue: {stats.queue_depth}")

# Graceful shutdown
await db.disconnect()
```

---

## See Also

- [PostgreSQL Adapter](./POSTGRES.md) - Core PostgreSQL functionality
- [Database Overview](./DATABASE.md) - Full Data Layer documentation
- [Migrations](./MIGRATIONS.md) - Schema migration system

