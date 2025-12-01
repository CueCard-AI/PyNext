# Production Reliability

> **Phase 5.3 Complete**: Retry logic, circuit breakers, read replicas, and graceful degradation.

PyNext's reliability system provides production-grade fault tolerance for your PostgreSQL connections. This document explains the **why**, **what**, and **how** of each component.

---

## Table of Contents

1. [Quick Start: Three Levels of Configuration](#quick-start-three-levels-of-configuration)
2. [Philosophy: Why Reliability Matters](#philosophy-why-reliability-matters)
3. [The Four Pillars](#the-four-pillars)
4. [Retry Logic](#retry-logic)
5. [Circuit Breakers](#circuit-breakers)
6. [Read Replica Routing](#read-replica-routing)
7. [Graceful Degradation](#graceful-degradation)
8. [Integration Patterns](#integration-patterns)
9. [Configuration Reference](#configuration-reference)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## Quick Start: Three Levels of Configuration

PyNext follows the principle: **super simple by default, full power when needed.**

### Level 1: One Line (90% of Users)

Just add `reliability=True`:

```python
from pynext.db.adapters import PostgresAdapter

# Enable all reliability features with sensible defaults
db = PostgresAdapter("postgresql://localhost/mydb", reliability=True)
await db.connect()

# That's it! You now have:
# ✓ Automatic retry with exponential backoff
# ✓ Circuit breaker protection
# ✓ Graceful degradation
```

### Level 2: With Replicas (Production)

Add read replicas for scalability:

```python
from pynext.db.adapters import PostgresAdapter

db = PostgresAdapter(
    primary="postgresql://primary.example.com/mydb",
    replicas=[
        "postgresql://replica1.example.com/mydb",
        "postgresql://replica2.example.com/mydb",
    ],
)
await db.connect()

# Reads automatically go to replicas
users = await db.read("SELECT * FROM users WHERE active = true")

# Writes always go to primary
await db.write("UPDATE users SET active = false WHERE id = $1", (user_id,))
```

### Level 3: Full Control (Enterprise)

Fine-tune every component:

```python
from pynext.db.adapters import (
    PostgresAdapter,
    Replica, ReplicaConfig,
    RetryConfig,
    CircuitBreakerConfig,
    DegradationConfig, DegradationTrigger, DegradationLevel, DegradationMetric,
)

db = PostgresAdapter(
    # Primary with keyword args
    host="primary.example.com",
    port=5432,
    database="mydb",
    user="postgres",
    password="secret",
    ssl=True,
    
    # Replicas with fine-grained control
    replicas=ReplicaConfig(
        replicas=[
            # Style 1: URL string
            Replica("postgresql://replica1.example.com/mydb", weight=3),
            
            # Style 2: Keyword arguments
            Replica(
                host="replica2.example.com",
                port=5432,
                database="mydb",
                user="postgres",
                password="secret",
                ssl=True,
                weight=1,
                max_lag=5.0,  # Max 5 seconds behind primary
                name="us-west-replica",
            ),
        ],
        routing="weighted_random",  # or "round_robin", "least_connections"
        lag_check_interval=5.0,
    ),
    
    # Retry configuration
    retry=RetryConfig(
        max_attempts=5,
        initial_delay=0.1,
        backoff="exponential",
        multiplier=2.0,
        jitter=True,
    ),
    
    # Circuit breaker configuration
    circuit_breaker=CircuitBreakerConfig(
        failure_threshold=5,
        timeout=30.0,
        success_threshold=2,
        scope="query_type",  # Separate breakers for reads vs writes
    ),
    
    # Degradation configuration
    degradation=DegradationConfig(
        triggers=[
            DegradationTrigger(
                metric=DegradationMetric.ERROR_RATE,
                threshold=0.1,
                level=DegradationLevel.DEGRADED,
            ),
            DegradationTrigger(
                metric=DegradationMetric.ERROR_RATE,
                threshold=0.25,
                level=DegradationLevel.CRITICAL,
            ),
        ],
        auto_recovery=True,
        notify_callback=lambda old, new: print(f"Degradation: {old} → {new}"),
    ),
)
await db.connect()
```

---

## Philosophy: Why Reliability Matters

### The Problem with Direct Database Calls

```
Your App                     PostgreSQL
    |                            |
    |-------- query ------------>|
    |                            | ← What if this fails?
    |<------- results -----------|
    |                            |
```

In the happy path, queries succeed. But databases fail for many reasons:

1. **Transient failures**: Network hiccups, brief overloads, connection resets
2. **Sustained failures**: Database down, disk full, crash recovery
3. **Slow degradation**: Increasing latency, connection exhaustion
4. **Cascading failures**: One failure triggers many more

Without reliability patterns, a single failure becomes a user-facing error.

### The PyNext Solution

```
Your App → Retry → Circuit Breaker → Replica Router → PostgreSQL
             ↓           ↓                 ↓
          Backoff    Protection         Failover
             ↓           ↓                 ↓
          Jitter     Recovery          Load Balance
```

Each layer handles specific failure modes:

| Layer | Handles | Example |
|-------|---------|---------|
| **Retry** | Transient failures | Network blip, deadlock |
| **Circuit Breaker** | Sustained failures | Database down |
| **Replica Router** | Primary failures | Automatic failover |
| **Degradation** | Slow failures | Progressive load shedding |

---

## The Four Pillars

### 1. Retry Logic

**Problem**: A network blip kills your query.
**Solution**: Try again with intelligent backoff.

```python
from pynext.db.adapters import RetryConfig, RetryManager

# Simple: just retry
retry = RetryManager()
result = await retry.execute_with_retry(my_operation)

# Configured: customize behavior
retry = RetryManager(RetryConfig(
    max_attempts=5,
    initial_delay=0.5,
    backoff="exponential",
))
```

### 2. Circuit Breakers

**Problem**: Database is down, but you keep hammering it.
**Solution**: Stop trying when failure is certain.

```python
from pynext.db.adapters import CircuitBreaker, CircuitBreakerConfig

breaker = CircuitBreaker("database", CircuitBreakerConfig(
    failure_threshold=5,      # Open after 5 failures
    timeout=30.0,             # Try again after 30s
    success_threshold=2,      # Close after 2 successes
))

result = await breaker.execute(my_operation)
```

### 3. Read Replica Routing

**Problem**: Primary database is overwhelmed with reads.
**Solution**: Route reads to replicas.

```python
from pynext.db.adapters import Replica, ReplicaConfig, ReplicaManager

config = ReplicaConfig(replicas=[
    Replica("postgresql://replica1/db", weight=2),
    Replica("postgresql://replica2/db", weight=1),
])
manager = ReplicaManager(config)

# Automatically routes to replicas
replica_url = await manager.get_replica()
```

### 4. Graceful Degradation

**Problem**: Load is increasing, response times suffering.
**Solution**: Progressively shed load to protect critical operations.

```python
from pynext.db.adapters import DegradationManager, DegradationConfig

manager = DegradationManager(DegradationConfig(
    auto_recovery=True,
))

# Check current health
if manager.current_level == DegradationLevel.NORMAL:
    # Full operations
    pass
elif manager.current_level == DegradationLevel.DEGRADED:
    # Reduce non-essential operations
    pass
```

---

## Retry Logic

### First Principles: Why Retry?

Not all failures are permanent. Consider:

- **Network timeout**: Router was busy for 50ms
- **Connection reset**: TCP connection dropped
- **Deadlock**: Two transactions conflicted

These are **transient** - they succeed on retry. Retrying is the right answer.

But some failures are permanent:

- **Syntax error**: Your SQL is wrong
- **Permission denied**: User can't access table
- **Not found**: Row doesn't exist

Retrying these wastes time. PyNext distinguishes automatically.

### How Backoff Works

Without backoff, retries can cause **thundering herd**:

```
Time 0s: Request fails
Time 0s: Retry 1 (fails)
Time 0s: Retry 2 (fails)
Time 0s: Retry 3 (fails)
← All requests hit at once, overwhelming the server
```

With exponential backoff:

```
Time 0.0s: Request fails
Time 1.0s: Retry 1 (fails)
Time 3.0s: Retry 2 (fails)  ← wait 2s
Time 7.0s: Retry 3 (fails)  ← wait 4s
← Gives server time to recover
```

### Backoff Strategies

```python
from pynext.db.adapters import RetryConfig

# Exponential (default): delay = initial × (multiplier ^ attempt)
# Best for: Most cases
config = RetryConfig(
    backoff="exponential",
    initial_delay=1.0,
    multiplier=2.0,
)
# Delays: 1s, 2s, 4s, 8s, 16s...

# Linear: delay = initial × attempt
# Best for: Predictable timing
config = RetryConfig(
    backoff="linear",
    initial_delay=1.0,
)
# Delays: 1s, 2s, 3s, 4s, 5s...

# Fixed: delay = initial (constant)
# Best for: Polling, real-time
config = RetryConfig(
    backoff="fixed",
    initial_delay=0.5,
)
# Delays: 0.5s, 0.5s, 0.5s, 0.5s...
```

### Jitter: Preventing Synchronized Retries

Without jitter, all failed requests retry at the same time:

```
Client A: retry at 1.0s
Client B: retry at 1.0s
Client C: retry at 1.0s
← All hit server at 1.0s
```

With jitter (±25% randomization):

```
Client A: retry at 0.8s
Client B: retry at 1.1s
Client C: retry at 0.9s
← Spread out, server handles smoothly
```

```python
config = RetryConfig(
    jitter=True,           # Enable jitter
    jitter_factor=0.25,    # ±25% of delay
)
```

### Retryable vs Non-Retryable Errors

PyNext automatically classifies errors:

**Retryable** (worth trying again):
- `ConnectionRefusedError` - Server might be starting up
- `ConnectionResetError` - Network hiccup
- `TimeoutError` - Temporary slowness
- `BrokenPipeError` - Connection dropped
- PostgreSQL deadlock (`40P01`)
- PostgreSQL serialization failure (`40001`)

**Non-Retryable** (don't waste time):
- `ValueError` - Bad input
- `KeyError` - Missing key
- PostgreSQL syntax error (`42601`)
- PostgreSQL permission denied (`42501`)

### Custom Retry Logic

```python
def should_retry(error: Exception, attempt: int) -> bool:
    """Custom retry decision."""
    # Always retry rate limits
    if isinstance(error, RateLimitError):
        return attempt < 10
    
    # Never retry validation errors
    if isinstance(error, ValidationError):
        return False
    
    # Default: retry connection errors up to 3 times
    return attempt < 3

result = await retry.execute_with_retry(
    operation,
    should_retry=should_retry,
)
```

### Retry Statistics

```python
# Track retry behavior
retry = RetryManager()
await retry.execute_with_retry(operation)

stats = retry.stats
print(f"Attempts: {stats.total_attempts}")
print(f"Successes: {stats.total_successes}")
print(f"Retries: {stats.total_retries}")
print(f"Success rate: {stats.success_rate:.1%}")
print(f"Avg retries/success: {stats.avg_retries_per_success:.1f}")
```

### Convenience Configurations

```python
from pynext.db.adapters import quick_retry, standard_retry, aggressive_retry, no_retry

# Real-time operations (fast, few retries)
config = quick_retry()
# max_attempts=3, initial_delay=0.05, max_delay=0.5, linear

# Standard operations (balanced)
config = standard_retry()
# max_attempts=3, initial_delay=1.0, max_delay=30, exponential

# Background jobs (many retries, long delays)
config = aggressive_retry()
# max_attempts=10, initial_delay=0.1, max_delay=60, exponential

# Disable retries
config = no_retry()
# max_attempts=1
```

---

## Circuit Breakers

### First Principles: Why Stop Trying?

Imagine your database is down. Without a circuit breaker:

```
Request 1: Wait 30s, timeout, fail
Request 2: Wait 30s, timeout, fail
Request 3: Wait 30s, timeout, fail
...
← Every request wastes 30s before failing
```

With a circuit breaker:

```
Requests 1-5: Fail quickly (detect problem)
Circuit OPENS
Requests 6-100: Fail immediately (0ms)
After 30s: Circuit HALF-OPENS
Request 101: Try once
If success: Circuit CLOSES (resume)
If failure: Circuit re-OPENS (wait longer)
```

### The Three States

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   ┌─────────┐      failures      ┌────────┐                 │
   │   │ CLOSED  │ ─────────────────> │  OPEN  │                 │
   │   │ (allow) │                    │(reject)│                 │
   │   └────┬────┘                    └───┬────┘                 │
   │        │                             │                       │
   │        │ successes                   │ timeout               │
   │        │                             ▼                       │
   │        │                      ┌───────────┐                 │
   │        │                      │ HALF_OPEN │                 │
   │        │                      │  (probe)  │                 │
   │        │                      └─────┬─────┘                 │
   │        │                            │                        │
   │        │ success ───────────────────┘                        │
   │        │                                                     │
   │   ┌────┴────┐                                               │
   │   │ CLOSED  │ <── success resets state                      │
   │   └─────────┘                                               │
   │                                                              │
   └──────────────────────────────────────────────────────────────┘
```

**CLOSED** (normal operation):
- Requests flow through
- Failures are counted
- When failures reach threshold → OPEN

**OPEN** (failing fast):
- Requests are rejected immediately
- No load on database
- After timeout → HALF_OPEN

**HALF_OPEN** (testing recovery):
- Limited requests allowed (probes)
- If success → CLOSED
- If failure → OPEN

### Configuration Options

```python
from pynext.db.adapters import CircuitBreakerConfig, CircuitBreaker

config = CircuitBreakerConfig(
    # When to trip
    failure_threshold=5,        # Open after 5 consecutive failures
    
    # How to recover
    success_threshold=2,        # Close after 2 successes in half-open
    timeout=30.0,               # Wait 30s before trying half-open
    
    # Advanced
    half_open_max_requests=3,   # Allow 3 probe requests
    failure_rate_threshold=0.5, # Open if 50% failure rate
    sample_window=60.0,         # Failure rate window
    
    # Scope
    scope="global",             # "global", "connection", or "query_type"
    
    # Exclusions
    excluded_errors={ValueError}, # Don't count these as failures
)

breaker = CircuitBreaker("my-service", config)
```

### Circuit Breaker Scopes

**Global** (one breaker for all):
```python
# All database operations share one breaker
breaker = CircuitBreaker("database", CircuitBreakerConfig(scope="global"))
```

**Per-Connection** (isolation):
```python
# Each connection has its own breaker
registry = CircuitBreakerRegistry(
    config=CircuitBreakerConfig(scope="connection")
)
breaker = registry.get_for_connection("conn-123")
```

**Per-Query-Type** (fine-grained):
```python
# Separate breakers for reads vs writes
registry = CircuitBreakerRegistry(
    config=CircuitBreakerConfig(scope="query_type")
)
read_breaker = registry.get_for_query_type("read")
write_breaker = registry.get_for_query_type("write")

# Write breaker can be open while reads still work
```

### Using the Registry

```python
from pynext.db.adapters import CircuitBreakerRegistry

registry = CircuitBreakerRegistry()

# Get breakers by key
primary_breaker = registry.get_breaker("primary")
replica_breaker = registry.get_breaker("replica")

# Check all breaker states
all_stats = registry.get_all_stats()
for name, stats in all_stats.items():
    print(f"{name}: {stats['state']}, failures={stats['total_failures']}")

# Reset all breakers
registry.reset_all()
```

### Manual Control

```python
# Force open (maintenance mode)
breaker.force_open()

# Force close (recovery confirmed)
breaker.force_close()

# Reset to initial state
breaker.reset()

# Check state
if breaker.is_closed:
    print("Normal operation")
elif breaker.is_open:
    print(f"Circuit open, retry in {breaker.get_time_until_half_open():.1f}s")
```

### Convenience Configurations

```python
from pynext.db.adapters import (
    create_global_breaker,
    create_sensitive_breaker,
    create_tolerant_breaker,
)

# Standard: trips after 5 failures, 30s timeout
breaker = create_global_breaker("database")

# Sensitive: trips after 3 failures, 10s timeout (payment processing)
breaker = create_sensitive_breaker("payments")

# Tolerant: trips after 10 failures, 60s timeout (background jobs)
breaker = create_tolerant_breaker("batch-jobs")
```

---

## Read Replica Routing

### First Principles: Why Replicas?

A single PostgreSQL server has limits:
- CPU: ~100K queries/second
- Memory: Caches finite data
- I/O: Disk speed caps reads

With replicas:

```
                     ┌────────────────┐
                     │    Primary     │
                     │    (writes)    │
                     └───────┬────────┘
                             │ replication
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐
        │ Replica 1 │  │ Replica 2 │  │ Replica 3 │
        │  (reads)  │  │  (reads)  │  │  (reads)  │
        └───────────┘  └───────────┘  └───────────┘
```

Benefits:
- **Scale reads**: 3 replicas = 3x read capacity
- **Reduce primary load**: Reads don't touch primary
- **Geographic distribution**: Replicas in different regions
- **Failover**: Promote replica if primary fails

### Configuration

PyNext supports two configuration styles for replicas. Use whichever feels more natural:

#### Style 1: URL String (Simple)

Best for quick setups or when credentials are in the URL:

```python
from pynext.db.adapters import Replica, ReplicaConfig, ReplicaManager

config = ReplicaConfig(
    replicas=[
        Replica("postgresql://user:pass@replica1.example.com/db", weight=2),
        Replica("postgresql://user:pass@replica2.example.com/db", weight=1),
    ],
)
```

#### Style 2: Keyword Arguments (Explicit)

Best for production setups with environment variables:

```python
import os
from pynext.db.adapters import Replica, ReplicaConfig, ReplicaManager

config = ReplicaConfig(
    replicas=[
        Replica(
            host=os.environ["REPLICA1_HOST"],
            port=int(os.environ.get("REPLICA1_PORT", 5432)),
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["REPLICA1_PASSWORD"],  # Different password per replica
            ssl=True,
            name="us-east-replica",
            weight=2,           # 2x traffic of default
            max_lag=5.0,        # Max 5 seconds behind
        ),
        Replica(
            host=os.environ["REPLICA2_HOST"],
            port=int(os.environ.get("REPLICA2_PORT", 5432)),
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["REPLICA2_PASSWORD"],
            ssl=True,
            name="us-west-replica",
            weight=1,
            max_lag=10.0,
        ),
    ],
    
    # Lag detection
    lag_check_interval=5.0,     # Check every 5s
    
    # Failover
    failover_timeout=60.0,      # Remove unhealthy for 60s
    
    # Routing
    routing="weighted_random",  # or "round_robin", "least_connections"
)

manager = ReplicaManager(config)
```

#### Replica Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str | None | PostgreSQL URL (if not using keyword args) |
| `host` | str | None | Database host (if not using URL) |
| `port` | int | 5432 | Database port |
| `database` | str | None | Database name |
| `user` | str | None | Username |
| `password` | str | None | Password (URL-encoded automatically) |
| `ssl` | bool | False | Enable SSL (`?sslmode=require`) |
| `weight` | int | 1 | Traffic weight (higher = more traffic) |
| `max_lag` | float | 10.0 | Max replication lag in seconds |
| `name` | str | auto | Human-readable name for logs |
| `enabled` | bool | True | Whether replica is active |

#### Which Style to Use?

| Scenario | Recommended Style |
|----------|-------------------|
| Development | URL string (simple) |
| Production with secrets | Keyword args (explicit) |
| Different passwords per replica | Keyword args |
| Passwords with special characters | Keyword args (auto-encodes) |
| Quick prototyping | URL string |
| Environment-based config | Keyword args |

**Example: Passwords with special characters**

```python
# URL style - must manually encode special chars
Replica("postgresql://user:p%40ss%21word@host/db")  # Password: p@ss!word

# Keyword style - auto-encodes for you
Replica(
    host="host",
    database="db",
    user="user",
    password="p@ss!word",  # No manual encoding needed!
)
```

### Weighted Routing

Weights control traffic distribution:

```python
replicas=[
    Replica("...", weight=3),  # Gets 3/6 = 50% of traffic
    Replica("...", weight=2),  # Gets 2/6 = 33% of traffic
    Replica("...", weight=1),  # Gets 1/6 = 17% of traffic
]
```

Use cases:
- **Faster hardware**: Higher weight for better servers
- **Geographic locality**: Higher weight for nearby replicas
- **Gradual rollout**: Start new replica at low weight

### Lag Detection

Replicas can fall behind the primary:

```
Primary: transaction 1000
Replica: transaction 997   ← 3 transactions behind
```

PyNext monitors lag and excludes lagging replicas:

```python
config = ReplicaConfig(
    replicas=[
        Replica("...", max_lag_bytes=1024*1024),  # Max 1MB lag
    ],
    check_lag=True,
    lag_check_interval=5.0,
)

# Lagging replicas are automatically excluded
replica_url = await manager.get_replica()  # Only returns non-lagging
```

### Automatic Failover

When a replica fails:

```python
# Replica becomes unavailable
# → Automatically removed from rotation
# → Traffic redistributes to healthy replicas
# → Periodic health checks
# → Replica recovered → back in rotation
```

```python
stats = manager.stats
print(f"Available: {stats.available_count}/{stats.total_count}")
print(f"Unhealthy: {stats.unhealthy_replicas}")
print(f"Failovers: {stats.total_failovers}")
```

### Usage Patterns

```python
# Simple: get any healthy replica
replica_url = await manager.get_replica()
async with db.connect(replica_url) as conn:
    result = await conn.fetch("SELECT * FROM users")

# With lag requirement
replica_url = await manager.get_replica(max_lag_bytes=1024)

# Specific replica (debugging)
replica_url = await manager.get_replica(name="replica-east")

# Check health
health = await manager.check_health()
for replica_name, status in health.items():
    print(f"{replica_name}: {'healthy' if status.healthy else 'unhealthy'}")
```

---

## Graceful Degradation

### First Principles: Why Degrade Gracefully?

Under stress, you have two options:

**Option A: Crash**
```
Load: 100% → 110% → ERROR → ALL REQUESTS FAIL
```

**Option B: Degrade gracefully**
```
Load: 100% → 110%
Level: NORMAL → DEGRADED
Actions: Reject batch operations, prioritize critical
Result: Important requests still succeed
```

### Degradation Levels

```python
from pynext.db.adapters import DegradationLevel

# NORMAL: Everything works
# DEGRADED: Non-essential operations reduced
# CRITICAL: Only essential operations
# EMERGENCY: Minimal operations, maximum load shedding
```

Visual representation:

```
          Load
           ▲
EMERGENCY  │ ████████████████████
CRITICAL   │ ████████████████
DEGRADED   │ ████████████
NORMAL     │ ████████
           └───────────────────────▶ Time
```

### Triggers

Triggers define when to escalate:

```python
from pynext.db.adapters import DegradationConfig, DegradationTrigger, DegradationMetric

config = DegradationConfig(
    triggers=[
        # Queue depth (pending requests)
        DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=100,
            level=DegradationLevel.DEGRADED,
        ),
        DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=500,
            level=DegradationLevel.CRITICAL,
        ),
        
        # Error rate
        DegradationTrigger(
            metric=DegradationMetric.ERROR_RATE,
            threshold=0.10,  # 10%
            level=DegradationLevel.DEGRADED,
        ),
        DegradationTrigger(
            metric=DegradationMetric.ERROR_RATE,
            threshold=0.25,  # 25%
            level=DegradationLevel.CRITICAL,
        ),
        
        # Latency P95
        DegradationTrigger(
            metric=DegradationMetric.LATENCY_P95,
            threshold=1000,  # 1 second
            level=DegradationLevel.DEGRADED,
        ),
    ],
)
```

### Actions

Actions define what to do at each level:

```python
from pynext.db.adapters import DegradationAction

config = DegradationConfig(
    actions={
        DegradationLevel.DEGRADED: [
            DegradationAction.LOG_WARNING,
        ],
        DegradationLevel.CRITICAL: [
            DegradationAction.LOG_WARNING,
            DegradationAction.REJECT_BATCH,     # No batch operations
        ],
        DegradationLevel.EMERGENCY: [
            DegradationAction.LOG_WARNING,
            DegradationAction.REJECT_LOW,       # Reject low-priority
            DegradationAction.NOTIFY,           # Alert operators
        ],
    },
)
```

### Auto-Recovery

When load decreases, automatically recover:

```python
config = DegradationConfig(
    auto_recovery=True,
    recovery_check_interval=10.0,  # Check every 10s
    recovery_delay=30.0,           # Wait 30s of normal before recovering
)
```

Recovery is conservative to avoid thrashing:

```
Level: CRITICAL
Metrics normal for 30s
Level: DEGRADED
Metrics normal for 30s
Level: NORMAL
```

### Notifications

Get notified on level changes:

```python
def notify_ops(old_level: DegradationLevel, new_level: DegradationLevel):
    if new_level > old_level:
        # Escalating - alert!
        send_pagerduty(f"Database degraded: {old_level.name} → {new_level.name}")
    else:
        # Recovering
        send_slack(f"Database recovering: {old_level.name} → {new_level.name}")

config = DegradationConfig(
    notify_callback=notify_ops,
)
```

### Usage in Code

```python
manager = DegradationManager(config)

# Check level before operations
if manager.current_level == DegradationLevel.NORMAL:
    # Full operations
    await process_batch(items)
elif manager.current_level == DegradationLevel.DEGRADED:
    # Reduced batch size
    await process_batch(items[:10])
elif manager.current_level >= DegradationLevel.CRITICAL:
    # Skip batch, only critical ops
    logger.warning("Skipping batch due to degraded state")

# Update metrics (called periodically)
manager.update_metrics({
    "queue_depth": len(pending_queue),
    "error_rate": errors / requests,
    "latency_p95": percentile(latencies, 95),
})
```

### Convenience Configurations

```python
from pynext.db.adapters import (
    default_config,
    strict_config,
    lenient_config,
    disabled_config,
)

# Standard thresholds (recommended)
config = default_config()

# Lower thresholds (production, SLA-sensitive)
config = strict_config()

# Higher thresholds (development, testing)
config = lenient_config()

# Disabled (testing only)
config = disabled_config()
```

---

## Integration Patterns

### Pattern 1: Full Stack Protection

```python
from pynext.db.adapters import (
    RetryManager, RetryConfig,
    CircuitBreaker, CircuitBreakerConfig,
    ReplicaManager, ReplicaConfig, Replica,
    DegradationManager, DegradationConfig,
)

class ResilientDatabase:
    def __init__(self, primary_url: str, replicas: list[str]):
        # Layer 1: Retry
        self.retry = RetryManager(RetryConfig(
            max_attempts=3,
            initial_delay=0.1,
        ))
        
        # Layer 2: Circuit breaker
        self.breaker = CircuitBreaker("database", CircuitBreakerConfig(
            failure_threshold=5,
            timeout=30.0,
        ))
        
        # Layer 3: Replica routing
        self.replicas = ReplicaManager(ReplicaConfig(
            replicas=[Replica(url) for url in replicas],
        ))
        
        # Layer 4: Degradation
        self.degradation = DegradationManager()
    
    async def read(self, query: str) -> list:
        """Read with full protection."""
        if self.degradation.current_level >= DegradationLevel.EMERGENCY:
            raise ServiceUnavailableError("Database in emergency mode")
        
        async def operation():
            replica_url = await self.replicas.get_replica()
            async with connect(replica_url) as conn:
                return await conn.fetch(query)
        
        return await self.retry.execute_with_retry(
            lambda: self.breaker.execute(operation)
        )
    
    async def write(self, query: str, params: tuple) -> None:
        """Write with protection."""
        if self.degradation.current_level >= DegradationLevel.CRITICAL:
            raise ServiceUnavailableError("Writes disabled during critical load")
        
        async def operation():
            async with connect(self.primary_url) as conn:
                await conn.execute(query, *params)
        
        return await self.retry.execute_with_retry(
            lambda: self.breaker.execute(operation)
        )
```

### Pattern 2: Per-Operation Configuration

```python
from pynext.db.adapters import with_retry, RetryConfig

# Critical: aggressive retry
@with_retry(RetryConfig(max_attempts=5, initial_delay=0.5))
async def process_payment(payment_id: str) -> bool:
    async with db.transaction():
        await db.execute("UPDATE payments SET status = 'processing' WHERE id = $1", payment_id)
        result = await payment_gateway.charge(payment_id)
        await db.execute("UPDATE payments SET status = $1 WHERE id = $2", result.status, payment_id)
        return result.success

# Best-effort: minimal retry
@with_retry(RetryConfig(max_attempts=2, initial_delay=0.05))
async def update_analytics(event: dict) -> None:
    await db.execute("INSERT INTO events (...) VALUES (...)", event)
```

### Pattern 3: Health Endpoint

```python
from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health endpoint for load balancers."""
    
    # Check circuit breaker
    if db.breaker.is_open:
        return Response(
            content='{"status": "unhealthy", "reason": "circuit_open"}',
            status_code=503,
        )
    
    # Check degradation level
    if db.degradation.current_level >= DegradationLevel.EMERGENCY:
        return Response(
            content='{"status": "degraded", "level": "emergency"}',
            status_code=503,
        )
    
    # Check replica availability
    if db.replicas.stats.available_count == 0:
        return Response(
            content='{"status": "unhealthy", "reason": "no_replicas"}',
            status_code=503,
        )
    
    return {
        "status": "healthy",
        "degradation_level": db.degradation.current_level.name,
        "circuit_state": db.breaker.state.value,
        "replicas_available": db.replicas.stats.available_count,
    }
```

---

## Configuration Reference

### RetryConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_attempts` | int | 3 | Maximum attempts (including initial) |
| `initial_delay` | float | 1.0 | Initial delay in seconds |
| `max_delay` | float | 30.0 | Maximum delay cap |
| `backoff` | str | "exponential" | "exponential", "linear", "fixed" |
| `multiplier` | float | 2.0 | Exponential backoff multiplier |
| `jitter` | bool | True | Add randomization |
| `jitter_factor` | float | 0.25 | Jitter range (±25%) |
| `retry_on_timeout` | bool | True | Retry timeout errors |
| `log_retries` | bool | True | Log retry attempts |

### CircuitBreakerConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `failure_threshold` | int | 5 | Failures before opening |
| `success_threshold` | int | 2 | Successes to close |
| `timeout` | float | 30.0 | Seconds before half-open |
| `scope` | str | "global" | "global", "connection", "query_type" |
| `half_open_max_requests` | int | 1 | Probe requests allowed |
| `failure_rate_threshold` | float | None | Alternative: rate-based |
| `sample_window` | float | 60.0 | Window for rate calculation |

### ReplicaConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `replicas` | list[Replica] | [] | List of replicas |
| `check_lag` | bool | True | Monitor replication lag |
| `lag_check_interval` | float | 5.0 | Seconds between checks |
| `failover_threshold` | int | 3 | Errors before failover |
| `failover_timeout` | float | 60.0 | Failover duration |
| `routing_strategy` | str | "weighted_random" | Routing algorithm |

### DegradationConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `triggers` | list[Trigger] | defaults | When to escalate |
| `actions` | dict | defaults | What to do at each level |
| `auto_recovery` | bool | True | Auto-recover when normal |
| `recovery_check_interval` | float | 10.0 | Seconds between checks |
| `recovery_delay` | float | 30.0 | Delay before recovering |
| `notify_callback` | Callable | None | Level change callback |

---

## Best Practices

### 1. Layer Your Defenses

```python
# Good: multiple layers
result = await retry.execute_with_retry(
    lambda: breaker.execute(
        lambda: replicas.with_replica(operation)
    )
)

# Bad: single layer
result = await operation()  # No protection
```

### 2. Fail Fast for Non-Retryable Errors

```python
# Good: don't retry validation errors
config = RetryConfig(
    retryable_errors={"ConnectionError", "TimeoutError"},
)

# Bad: retry everything
config = RetryConfig(max_attempts=10)  # Wastes time on syntax errors
```

### 3. Configure Appropriate Timeouts

```python
# Good: timeout matches operation
config = CircuitBreakerConfig(timeout=30.0)  # Database recovery time

# Bad: too short
config = CircuitBreakerConfig(timeout=1.0)  # Will thrash

# Bad: too long
config = CircuitBreakerConfig(timeout=3600.0)  # Hour of downtime
```

### 4. Monitor and Alert

```python
# Good: track and alert
stats = retry.stats
if stats.retry_rate > 0.1:  # 10% retries
    alert("High retry rate: possible database issues")

# Good: degradation notifications
config = DegradationConfig(
    notify_callback=send_pagerduty,
)
```

### 5. Test Failure Scenarios

```python
# Good: test with circuit open
@pytest.mark.asyncio
async def test_circuit_open_handling():
    breaker.force_open()
    with pytest.raises(CircuitOpenError):
        await operation()

# Good: test degraded behavior
async def test_degraded_mode():
    manager.force_level(DegradationLevel.CRITICAL)
    # Verify batch operations are rejected
    with pytest.raises(DegradedServiceError):
        await batch_operation()
```

---

## Troubleshooting

### Issue: Circuit keeps tripping

**Symptoms**: Circuit breaker opens frequently, service flapping

**Causes**:
1. Threshold too low
2. Underlying database issues
3. Legitimate traffic spikes

**Solutions**:
```python
# Increase threshold
config = CircuitBreakerConfig(failure_threshold=10)

# Use failure rate instead of count
config = CircuitBreakerConfig(
    failure_rate_threshold=0.3,  # 30% failure rate
    sample_window=60.0,
)

# Check database health
# Look at slow query logs, connection counts
```

### Issue: Retries taking too long

**Symptoms**: Requests timing out during retry

**Solutions**:
```python
# Reduce max delay
config = RetryConfig(
    max_delay=5.0,  # Cap at 5s, not 30s
)

# Use linear backoff
config = RetryConfig(
    backoff="linear",
    initial_delay=0.5,
)

# Reduce max attempts
config = RetryConfig(max_attempts=2)
```

### Issue: Replicas all unavailable

**Symptoms**: `NoAvailableReplicaError`

**Causes**:
1. All replicas are lagging
2. Network partition
3. Incorrect configuration

**Solutions**:
```python
# Increase lag tolerance
Replica("...", max_lag_bytes=10*1024*1024)  # 10MB

# Add fallback to primary
try:
    url = await manager.get_replica()
except NoAvailableReplicaError:
    url = primary_url  # Fallback

# Check replica health
health = await manager.check_health()
for name, status in health.items():
    print(f"{name}: {status}")
```

### Issue: Degradation not recovering

**Symptoms**: Stuck in CRITICAL or EMERGENCY

**Solutions**:
```python
# Verify auto_recovery is enabled
config = DegradationConfig(auto_recovery=True)

# Reduce recovery delay
config = DegradationConfig(recovery_delay=10.0)

# Manual recovery
manager.reset()

# Check metrics
print(manager.stats.current_metrics)
# Are metrics actually normal?
```

---

## Summary

PyNext's reliability system provides **defense in depth** for your database connections:

| Component | Purpose | Default |
|-----------|---------|---------|
| **Retry** | Handle transient failures | 3 attempts, exponential backoff |
| **Circuit Breaker** | Prevent cascading failures | 5 failures → open |
| **Replica Routing** | Scale reads, enable failover | Weighted random |
| **Graceful Degradation** | Progressive load shedding | Auto-recovery enabled |

Together, these components ensure your application stays responsive even when the database is under stress or experiencing failures.

---

## Production Checklist

### Minimum Production Setup

```python
from pynext.db.adapters import PostgresAdapter

# ✅ This is enough for most production apps
adapter = PostgresAdapter(
    host="primary.example.com",
    port=5432,
    database="mydb",
    user="postgres",
    password=os.environ["DB_PASSWORD"],
    ssl=True,
    reliability=True,  # Enables retry + circuit breaker + degradation
)
```

### Recommended Production Setup

```python
from pynext.db.adapters import (
    PostgresAdapter,
    Replica, ReplicaConfig,
    RetryConfig,
    CircuitBreakerConfig,
    DegradationConfig,
)

adapter = PostgresAdapter(
    # Connection (use environment variables)
    host=os.environ["DB_PRIMARY_HOST"],
    port=int(os.environ.get("DB_PORT", 5432)),
    database=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    ssl=True,
    
    # Pool sizing
    min_connections=5,
    max_connections=50,
    
    # Read replicas
    replicas=ReplicaConfig(
        replicas=[
            Replica(
                host=os.environ["DB_REPLICA1_HOST"],
                port=int(os.environ.get("DB_PORT", 5432)),
                database=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_REPLICA1_PASSWORD"],
                ssl=True,
                weight=2,
            ),
            Replica(
                host=os.environ["DB_REPLICA2_HOST"],
                port=int(os.environ.get("DB_PORT", 5432)),
                database=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_REPLICA2_PASSWORD"],
                ssl=True,
                weight=1,
            ),
        ],
        lag_check_interval=10.0,
    ),
    
    # Reliability
    retry=RetryConfig(
        max_attempts=3,
        backoff="exponential",
    ),
    circuit_breaker=CircuitBreakerConfig(
        failure_threshold=5,
        timeout=30.0,
    ),
    degradation=DegradationConfig(
        auto_recovery=True,
        notify_callback=send_alert_to_ops,
    ),
)
```

### Checklist

| Item | Status | Notes |
|------|--------|-------|
| SSL enabled | ✅ | `ssl=True` |
| Credentials from env | ✅ | Never hardcode passwords |
| Connection pool sized | ✅ | `max_connections` based on DB limits |
| Retry enabled | ✅ | `reliability=True` or `retry=RetryConfig(...)` |
| Circuit breaker enabled | ✅ | `reliability=True` or `circuit_breaker=...` |
| Replicas configured (if available) | ✅ | `replicas=[...]` |
| Degradation notifications | ✅ | `notify_callback=...` |
| Health endpoint | ✅ | See Pattern 3 above |
| Logging configured | ✅ | `log_retries=True` (default) |

---

## Common Patterns

### Pattern: Environment-Based Configuration

```python
import os
from pynext.db.adapters import PostgresAdapter, Replica, ReplicaConfig

def create_adapter():
    """Create adapter from environment variables."""
    
    # Parse replica hosts from comma-separated string
    replica_hosts = os.environ.get("DB_REPLICA_HOSTS", "").split(",")
    replicas = [
        Replica(
            host=host.strip(),
            port=int(os.environ.get("DB_PORT", 5432)),
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            ssl=os.environ.get("DB_SSL", "true").lower() == "true",
        )
        for host in replica_hosts if host.strip()
    ]
    
    return PostgresAdapter(
        host=os.environ["DB_PRIMARY_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        ssl=os.environ.get("DB_SSL", "true").lower() == "true",
        replicas=ReplicaConfig(replicas=replicas) if replicas else None,
        reliability=True,
    )
```

### Pattern: Development vs Production

```python
import os
from pynext.db.adapters import PostgresAdapter

ENV = os.environ.get("ENV", "development")

if ENV == "development":
    # Simple local setup
    adapter = PostgresAdapter("postgresql://postgres:postgres@localhost/mydb")
elif ENV == "production":
    # Full production setup
    adapter = PostgresAdapter(
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        ssl=True,
        reliability=True,
        replicas=[os.environ["DB_REPLICA_URL"]],
    )
```

### Pattern: FastAPI Integration

```python
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from pynext.db.adapters import PostgresAdapter

adapter: PostgresAdapter = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global adapter
    adapter = PostgresAdapter(
        url=os.environ["DATABASE_URL"],
        reliability=True,
    )
    await adapter.connect()
    yield
    await adapter.disconnect()

app = FastAPI(lifespan=lifespan)

def get_db():
    return adapter

@app.get("/users")
async def get_users(db: PostgresAdapter = Depends(get_db)):
    return await db.read("SELECT * FROM users")
```

---

## Related Documentation

- [PostgreSQL Adapter](POSTGRES.md) - Core PostgreSQL features
- [Connection Pooling](POOLING.md) - Connection management
- [Database Overview](DATABASE.md) - Full Data Layer guide

