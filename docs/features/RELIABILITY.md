# Production Reliability

## Table of Contents

1. [Introduction: Why Reliability Matters](#introduction-why-reliability-matters)
2. [Chapter 1: Things That Go Wrong](#chapter-1-things-that-go-wrong)
3. [Chapter 2: The Four Pillars of Reliability](#chapter-2-the-four-pillars-of-reliability)
4. [Chapter 3: Retry Logic - Try Again](#chapter-3-retry-logic---try-again)
5. [Chapter 4: Circuit Breakers - Know When to Stop](#chapter-4-circuit-breakers---know-when-to-stop)
6. [Chapter 5: Read Replicas - Scale Your Reads](#chapter-5-read-replicas---scale-your-reads)
7. [Chapter 6: Graceful Degradation - Fail Gracefully](#chapter-6-graceful-degradation---fail-gracefully)
8. [Chapter 7: Putting It All Together](#chapter-7-putting-it-all-together)
9. [Chapter 8: Monitoring and Alerts](#chapter-8-monitoring-and-alerts)
10. [Configuration Reference](#configuration-reference)
11. [Troubleshooting](#troubleshooting)

---

## Introduction: Why Reliability Matters

### The 3am Problem

It's 3am. Your phone buzzes. The monitoring system says your app is down.

You check: the database server rebooted for routine maintenance. Your app crashed because it couldn't connect. Every request failed. Customers are angry.

**This is preventable.**

### What is Reliability?

**Reliability** means your application keeps working even when things go wrong:

```
Unreliable App:
───────────────
Database reboots → App crashes → Users see errors → Revenue lost

Reliable App:
─────────────
Database reboots → App retries → Users never notice → Business continues
```

### The Reliability Mindset

The key insight: **failures are normal, not exceptional**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    THINGS THAT FAIL                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Networks:    Packets get lost, connections drop, latency spikes    │
│  Databases:   Servers restart, disks fill up, locks contend         │
│  DNS:         Lookups fail, TTL expires, records change             │
│  Cloud:       Instances terminate, regions go down, APIs throttle   │
│  Hardware:    Disks fail, memory corrupts, CPUs overheat            │
│                                                                      │
│  The question isn't IF these will happen, but WHEN.                 │
│  Your code must handle them gracefully.                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Chapter 1: Things That Go Wrong

### Types of Failures

Understanding failure modes helps you handle them:

#### Transient Failures (Temporary)

```
Example: Network hiccup

Request 1: ❌ Connection reset
Request 2: ❌ Connection reset  
Request 3: ✓ Success!          ← Works after a moment

Solution: Retry
```

These failures fix themselves. The database is fine, the network just blipped. Retry and you'll succeed.

#### Intermittent Failures (Recurring)

```
Example: Overloaded database

Request 1: ✓ Success (slow)
Request 2: ❌ Timeout
Request 3: ✓ Success
Request 4: ❌ Timeout
Request 5: ✓ Success

Solution: Add capacity, optimize queries, use read replicas
```

The system works but is stressed. Some requests succeed, some fail.

#### Persistent Failures (Ongoing)

```
Example: Database is down

Request 1: ❌ Connection refused
Request 2: ❌ Connection refused
Request 3: ❌ Connection refused
... (forever)

Solution: Stop trying, use fallback
```

The system is broken. Retrying won't help. You need a different strategy.

### Common Database Failures

| Failure | Symptom | Transient? | Solution |
|---------|---------|------------|----------|
| Connection refused | Can't connect | Maybe | Retry with backoff |
| Connection timeout | Slow to connect | Usually | Retry, check network |
| Query timeout | Query takes too long | Usually | Retry, add index |
| Too many connections | Pool exhausted | Usually | Wait, increase pool |
| Deadlock | Transactions blocking | Yes | Retry immediately |
| Server restart | Connections dropped | Yes | Reconnect |
| Disk full | Writes fail | No | Fix disk, then retry |
| Authentication failed | Wrong credentials | No | Fix credentials |

---

## Chapter 2: The Four Pillars of Reliability

PyNext provides four complementary reliability mechanisms:

```
┌─────────────────────────────────────────────────────────────────────┐
│                   THE FOUR PILLARS                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────┐    ┌───────────────┐                            │
│  │   RETRY       │    │   CIRCUIT     │                            │
│  │   LOGIC       │    │   BREAKER     │                            │
│  │               │    │               │                            │
│  │ "Try again    │    │ "Stop trying  │                            │
│  │  if it fails" │    │  if it keeps  │                            │
│  │               │    │  failing"     │                            │
│  └───────────────┘    └───────────────┘                            │
│         ↓                    ↓                                      │
│  Handles transient      Prevents cascade                            │
│  failures               failures                                    │
│                                                                      │
│  ┌───────────────┐    ┌───────────────┐                            │
│  │   READ        │    │   GRACEFUL    │                            │
│  │   REPLICAS    │    │   DEGRADATION │                            │
│  │               │    │               │                            │
│  │ "Spread the   │    │ "Do less      │                            │
│  │  read load"   │    │  but keep     │                            │
│  │               │    │  working"     │                            │
│  └───────────────┘    └───────────────┘                            │
│         ↓                    ↓                                      │
│  Scales capacity        Maintains partial                           │
│  and adds redundancy    functionality                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Quick Start: Enable Everything

```python
from pynext.db.adapters import PostgresAdapter

# One flag enables all reliability features with sensible defaults
adapter = PostgresAdapter(
    "postgresql://localhost/mydb",
    reliability=True,
)

# You now have:
# ✓ Retry with exponential backoff (3 attempts)
# ✓ Circuit breaker (opens after 5 consecutive failures)
# ✓ Graceful degradation (auto-recovery)
```

---

## Chapter 3: Retry Logic - Try Again

### The Retry Concept

When an operation fails, try again:

```
Without retry:                With retry:
──────────────                ───────────

Request → Fail → Error!       Request → Fail
                                      → Wait
                              Request → Fail
                                      → Wait  
                              Request → Success! ✓
```

### Why Exponential Backoff?

If you retry immediately, you might:
1. Hit the same problem (it hasn't recovered yet)
2. Overwhelm the system (everyone retrying at once)

**Exponential backoff** waits longer between each retry:

```
Attempt 1: Fail → Wait 100ms
Attempt 2: Fail → Wait 200ms  (100ms × 2)
Attempt 3: Fail → Wait 400ms  (200ms × 2)
Attempt 4: Success!

Or with jitter (randomness):
Attempt 1: Fail → Wait 80-120ms   (random within range)
Attempt 2: Fail → Wait 160-240ms
Attempt 3: Fail → Wait 320-480ms

Jitter prevents "thundering herd" (everyone retrying at same moment)
```

### Basic Retry Configuration

```python
from pynext.db.adapters import PostgresAdapter, RetryConfig

adapter = PostgresAdapter(
    "postgresql://localhost/mydb",
    retry=RetryConfig(
        max_attempts=3,        # Try up to 3 times
        initial_delay=0.1,     # First retry after 100ms
        max_delay=10.0,        # Never wait more than 10s
        exponential_base=2,    # Double the delay each time
        jitter=0.1,            # Add ±10% randomness
    ),
)
```

### Understanding Retry Configuration

```python
from pynext.db.adapters import RetryConfig

RetryConfig(
    # ═══════════════════════════════════════════════════════════
    # ATTEMPT LIMITS
    # ═══════════════════════════════════════════════════════════
    
    # Maximum number of attempts (including initial try)
    # 3 = initial + 2 retries
    max_attempts=3,
    
    # ═══════════════════════════════════════════════════════════
    # TIMING
    # ═══════════════════════════════════════════════════════════
    
    # Delay before first retry (seconds)
    initial_delay=0.1,  # 100ms
    
    # Maximum delay between retries (cap)
    max_delay=10.0,  # 10 seconds
    
    # Multiplier for exponential backoff
    # delay = initial_delay * (exponential_base ^ attempt)
    exponential_base=2,
    
    # ═══════════════════════════════════════════════════════════
    # JITTER (Randomness)
    # ═══════════════════════════════════════════════════════════
    
    # Random variation to prevent thundering herd
    # 0.1 = ±10% variation
    # If calculated delay is 1s, actual will be 0.9-1.1s
    jitter=0.1,
    
    # ═══════════════════════════════════════════════════════════
    # ERROR HANDLING
    # ═══════════════════════════════════════════════════════════
    
    # Which errors should trigger a retry?
    # Default: connection errors, timeouts, deadlocks
    retryable_errors=[
        "ConnectionError",
        "TimeoutError", 
        "DeadlockError",
    ],
    
    # Errors that should never retry (fail immediately)
    non_retryable_errors=[
        "AuthenticationError",
        "SyntaxError",
    ],
)
```

### Retry Timeline Visualization

```
With: max_attempts=4, initial_delay=100ms, exponential_base=2

Time     Event
──────────────────────────────────────────────────────────
0ms      Attempt 1 → FAIL
100ms    Wait 100ms...
200ms    Attempt 2 → FAIL  
200ms    Wait 200ms...
400ms    Attempt 3 → FAIL
400ms    Wait 400ms...
800ms    Attempt 4 → SUCCESS! ✓

Total time: 800ms
Without retry: Would have failed at 0ms
```

### When to Retry vs When to Fail

| Error Type | Retry? | Why |
|------------|--------|-----|
| Connection timeout | ✅ Yes | Network issue, may resolve |
| Connection refused | ✅ Yes | Server may be restarting |
| Deadlock | ✅ Yes | Contention, will clear |
| Query timeout | ⚠️ Maybe | Depends on query |
| Authentication failed | ❌ No | Wrong password won't change |
| SQL syntax error | ❌ No | Bug in code |
| Unique constraint violation | ❌ No | Data conflict |

---

## Chapter 4: Circuit Breakers - Know When to Stop

### The Circuit Breaker Concept

Electrical circuit breakers prevent fires by cutting power when there's a problem. Software circuit breakers prevent cascade failures by stopping calls to broken services.

```
Without circuit breaker:          With circuit breaker:
────────────────────────          ────────────────────

Database down!                    Database down!
                                  
Request 1 → Wait... Timeout!     Request 1 → Wait... Timeout!
Request 2 → Wait... Timeout!     Request 2 → Wait... Timeout!
Request 3 → Wait... Timeout!     Request 3 → Wait... Timeout!
Request 4 → Wait... Timeout!     Request 4 → Wait... Timeout!
Request 5 → Wait... Timeout!     Request 5 → Wait... Timeout!
                                  ↓
All requests waiting 30s each,   Circuit OPENS!
backing up, using memory,        ↓
eventually crashing app          Request 6 → FAST FAIL (0ms)
                                  Request 7 → FAST FAIL (0ms)
                                  Request 8 → FAST FAIL (0ms)
                                  ↓
                                  Save resources, fail fast,
                                  try again later
```

### Circuit Breaker States

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER STATES                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────┐    failures     ┌────────────┐                     │
│  │            │    ≥ threshold   │            │                     │
│  │   CLOSED   │ ───────────────► │    OPEN    │                     │
│  │ (normal)   │                  │ (blocking) │                     │
│  │            │                  │            │                     │
│  └────────────┘                  └────────────┘                     │
│       ▲                               │                              │
│       │                               │ timeout expires              │
│       │                               ▼                              │
│       │                         ┌────────────┐                       │
│       │        success          │  HALF-OPEN │                       │
│       └─────────────────────────│  (testing) │                       │
│                                 │            │                       │
│                     failure     └────────────┘                       │
│                        └────────────────┘                            │
│                        (back to OPEN)                                │
│                                                                      │
│  CLOSED: Requests flow through normally                              │
│  OPEN: Requests fail immediately (fast fail)                        │
│  HALF-OPEN: Let one request through to test if service recovered    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Basic Circuit Breaker Configuration

```python
from pynext.db.adapters import PostgresAdapter, CircuitBreakerConfig

adapter = PostgresAdapter(
    "postgresql://localhost/mydb",
    circuit_breaker=CircuitBreakerConfig(
        failure_threshold=5,     # Open after 5 consecutive failures
        recovery_timeout=30.0,   # Try again after 30 seconds
        half_open_requests=3,    # Test with 3 requests before closing
    ),
)
```

### Understanding Circuit Breaker Configuration

```python
from pynext.db.adapters import CircuitBreakerConfig

CircuitBreakerConfig(
    # ═══════════════════════════════════════════════════════════
    # OPENING THRESHOLD
    # ═══════════════════════════════════════════════════════════
    
    # How many consecutive failures before opening the circuit?
    # Lower = more sensitive (opens quickly)
    # Higher = more tolerant (requires more failures)
    failure_threshold=5,
    
    # ═══════════════════════════════════════════════════════════
    # RECOVERY
    # ═══════════════════════════════════════════════════════════
    
    # How long to wait before trying again (seconds)?
    # After this timeout, circuit moves to HALF-OPEN
    recovery_timeout=30.0,
    
    # How many successful requests in HALF-OPEN before closing?
    # More = more confident the service is recovered
    half_open_requests=3,
    
    # ═══════════════════════════════════════════════════════════
    # SCOPE
    # ═══════════════════════════════════════════════════════════
    
    # Circuit breaker scope:
    # "global" - one circuit for all operations
    # "per_connection" - separate circuit per connection
    # "per_query_type" - separate for reads vs writes
    scope="global",
    
    # ═══════════════════════════════════════════════════════════
    # ADVANCED
    # ═══════════════════════════════════════════════════════════
    
    # Sliding window for failure counting (seconds)
    # Failures older than this are forgotten
    failure_window=60.0,
    
    # Only count these as failures
    counted_exceptions=["ConnectionError", "TimeoutError"],
)
```

### Circuit Breaker Scopes

PyNext supports multiple circuit breaker scopes:

```python
# Global: One circuit for all operations
circuit_breaker=CircuitBreakerConfig(scope="global")

# If ANY operation fails 5 times, ALL operations are blocked

# Per-connection: Separate circuit per database connection  
circuit_breaker=CircuitBreakerConfig(scope="per_connection")

# If replica1 fails, only replica1 is blocked
# Primary and replica2 still work

# Per-query-type: Separate for reads vs writes
circuit_breaker=CircuitBreakerConfig(scope="per_query_type")

# If reads fail, reads are blocked but writes work
# Useful when read replicas fail but primary is fine
```

### Timeline Example

```
With: failure_threshold=3, recovery_timeout=30s

Time      Event                          State
─────────────────────────────────────────────────
0:00      Request 1 fails               CLOSED (1 failure)
0:01      Request 2 fails               CLOSED (2 failures)
0:02      Request 3 fails               CLOSED → OPEN!
0:03      Request 4 → FAST FAIL         OPEN (blocked)
0:04      Request 5 → FAST FAIL         OPEN (blocked)
...
0:32      30s passed                    OPEN → HALF-OPEN
0:32      Test request → SUCCESS        HALF-OPEN (1/3)
0:33      Test request → SUCCESS        HALF-OPEN (2/3)
0:34      Test request → SUCCESS        HALF-OPEN → CLOSED!
0:35      Normal traffic resumes        CLOSED (working!)
```

---

## Chapter 5: Read Replicas - Scale Your Reads

### The Scaling Problem

Most applications are read-heavy (90%+ reads). A single database becomes a bottleneck:

```
Without replicas:                With replicas:
─────────────────                ───────────────

All traffic → Primary DB         Writes → Primary DB
             (overloaded!)                    ↓
                                        replication
                                              ↓
                                 Reads → Replica 1
                                         Replica 2
                                         Replica 3
                                 (load distributed!)
```

### How Replication Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATABASE REPLICATION                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    ┌─────────┐     WAL        ┌─────────┐                          │
│    │ PRIMARY │ ─────────────► │ REPLICA │                          │
│    │         │   (changes)    │   1     │                          │
│    └─────────┘                └─────────┘                          │
│         │                                                           │
│         │          WAL        ┌─────────┐                          │
│         └──────────────────►  │ REPLICA │                          │
│                               │   2     │                          │
│                               └─────────┘                          │
│                                                                      │
│    WAL = Write-Ahead Log (stream of all changes)                    │
│                                                                      │
│    Primary:  Handles ALL writes                                     │
│    Replicas: Copy data from primary, handle reads                   │
│                                                                      │
│    Benefit: 3 servers = 3x read capacity                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Basic Replica Configuration

```python
from pynext.db.adapters import PostgresAdapter

adapter = PostgresAdapter(
    # Primary database (handles writes)
    primary="postgresql://primary.example.com/mydb",
    
    # Replicas (handle reads)
    replicas=[
        "postgresql://replica1.example.com/mydb",
        "postgresql://replica2.example.com/mydb",
    ],
)

# Writes automatically go to primary
await User.insert(name="Alice")

# Reads automatically go to replicas
users = await User.all()
```

### Automatic Routing

PyNext automatically routes queries:

```python
# WRITES → Primary
await User.insert(name="Alice")     # → Primary
await user.update(age=26)           # → Primary
await user.delete()                 # → Primary

# READS → Replica (round-robin)
await User.get(1)                   # → Replica 1
await User.all()                    # → Replica 2
await User.where(...).first()       # → Replica 1
```

### Replica Weights

Assign different weights to replicas:

```python
from pynext.db.adapters import PostgresAdapter, Replica

adapter = PostgresAdapter(
    primary="postgresql://primary.example.com/mydb",
    replicas=[
        Replica("postgresql://replica1.example.com/mydb", weight=3),
        Replica("postgresql://replica2.example.com/mydb", weight=1),
    ],
)

# replica1 gets 3x the traffic of replica2
# (75% to replica1, 25% to replica2)
```

Use weights when:
- One replica is more powerful
- One replica is closer (lower latency)
- Testing a new replica

### Lag Detection

Replicas can be behind the primary (replication lag). PyNext can detect and avoid lagging replicas:

```python
from pynext.db.adapters import PostgresAdapter, ReplicaConfig

adapter = PostgresAdapter(
    primary="postgresql://primary.example.com/mydb",
    replicas=ReplicaConfig(
        replicas=[
            "postgresql://replica1.example.com/mydb",
            "postgresql://replica2.example.com/mydb",
        ],
        max_lag_seconds=5,  # Don't use replicas more than 5s behind
    ),
)

# If replica1 is 10s behind:
# - Reads automatically skip replica1
# - Traffic goes to replica2 or primary
```

### Read-After-Write Consistency

When you write then immediately read, you might read from a replica that doesn't have the write yet:

```python
# Problem scenario:
await User.insert(name="Alice")  # → Written to primary
user = await User.where(name="Alice").first()  # → Read from replica
# User might not exist yet! (replication lag)
```

PyNext provides options:

```python
# Option 1: Force read from primary
user = await User.where(name="Alice").first().use_primary()

# Option 2: Wait for replication
await User.insert(name="Alice")
await adapter.wait_for_replication()
user = await User.where(name="Alice").first()

# Option 3: Automatic read-your-writes (per-session)
async with adapter.consistent_reads():
    await User.insert(name="Alice")  # Writes to primary
    user = await User.where(name="Alice").first()  # Also reads from primary
```

### Complete Replica Configuration

```python
from pynext.db.adapters import PostgresAdapter, Replica, ReplicaConfig

adapter = PostgresAdapter(
    # Primary (writes)
    primary="postgresql://primary.example.com/mydb",
    
    # Replicas (reads) with full configuration
    replicas=ReplicaConfig(
        replicas=[
            # High-capacity replica
            Replica(
                host="replica1.example.com",
                database="mydb",
                weight=3,  # Gets 3x traffic
            ),
            
            # Backup replica
            Replica(
                url="postgresql://replica2.example.com/mydb",
                weight=1,
            ),
        ],
        
        # Lag handling
        max_lag_seconds=5,      # Skip replicas more than 5s behind
        lag_check_interval=10,  # Check lag every 10 seconds
        
        # Load balancing
        strategy="round_robin",  # or "least_connections", "random"
        
        # Failover
        fallback_to_primary=True,  # Use primary if all replicas fail
    ),
)
```

---

## Chapter 6: Graceful Degradation - Fail Gracefully

### The Degradation Concept

When the system is stressed, **do less but keep working**:

```
Normal operation:            Degraded operation:
────────────────            ───────────────────

Full features:               Core features only:
✓ Real-time updates         ✓ Basic read/write
✓ Analytics tracking        ✗ Analytics (skip)
✓ Audit logging             ✗ Detailed logging (skip)
✓ Cache warming             ✗ Cache warming (skip)

User sees:                   User sees:
Full functionality          "Running in reduced mode"
                            (but it still works!)
```

### Why Degrade?

When a database is overloaded:

**Without degradation:**
- App tries everything
- Database gets more overloaded
- Everything fails
- Complete outage

**With degradation:**
- App detects stress
- App reduces load (drops non-essential operations)
- Database recovers
- Core functionality works

### Degradation Triggers

```python
from pynext.db.adapters import PostgresAdapter, DegradationConfig, DegradationTrigger

adapter = PostgresAdapter(
    "postgresql://localhost/mydb",
    degradation=DegradationConfig(
        triggers=[
            # Trigger on high connection usage
            DegradationTrigger(
                metric="connection_usage",
                threshold=0.9,  # 90% of connections in use
            ),
            
            # Trigger on slow queries
            DegradationTrigger(
                metric="query_latency",
                threshold=5.0,  # Average latency > 5 seconds
            ),
            
            # Trigger on error rate
            DegradationTrigger(
                metric="error_rate",
                threshold=0.1,  # More than 10% errors
            ),
            
            # Trigger on replica lag
            DegradationTrigger(
                metric="replica_lag",
                threshold=30,  # Any replica > 30s behind
            ),
        ],
    ),
)
```

### Degradation Levels

```python
from pynext.db.adapters import DegradationConfig, DegradationLevel

DegradationConfig(
    levels=[
        # Level 1: Minor stress
        DegradationLevel(
            threshold=0.7,  # Triggered at 70% stress
            actions=[
                "disable_query_cache_warming",
                "reduce_connection_pool",
            ],
        ),
        
        # Level 2: Moderate stress
        DegradationLevel(
            threshold=0.85,
            actions=[
                "skip_audit_logging",
                "disable_analytics",
                "increase_query_timeout",
            ],
        ),
        
        # Level 3: Severe stress
        DegradationLevel(
            threshold=0.95,
            actions=[
                "reject_new_connections",
                "serve_cached_only",
                "enable_read_only_mode",
            ],
        ),
    ],
)
```

### Auto-Recovery

When conditions improve, automatically restore functionality:

```python
DegradationConfig(
    # ... triggers and levels ...
    
    recovery=RecoveryConfig(
        # Wait this long before checking recovery
        check_interval=30,  # Check every 30 seconds
        
        # Recovery thresholds (must be below these to recover)
        thresholds={
            "connection_usage": 0.6,
            "error_rate": 0.05,
        },
        
        # Wait this long of good metrics before recovering
        stable_duration=60,  # 60 seconds of stability
        
        # Recover one level at a time
        gradual=True,
    ),
)
```

### Checking Degradation Status

```python
# Check current status
status = adapter.degradation_status()
print(f"Degradation level: {status.level}")
print(f"Active actions: {status.active_actions}")
print(f"Since: {status.degraded_since}")

# In your code, check and adjust behavior
if adapter.is_degraded():
    # Skip non-essential operations
    pass  # Skip audit logging
else:
    await audit_log.record(action)
```

---

## Chapter 7: Putting It All Together

### The Complete Picture

All four pillars work together:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REQUEST FLOW                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Incoming Request                                                    │
│        ↓                                                             │
│  ┌──────────────────┐                                               │
│  │ Circuit Breaker  │  Is circuit open?                             │
│  │                  │  → Yes: FAST FAIL                             │
│  │                  │  → No: Continue                               │
│  └────────┬─────────┘                                               │
│           ↓                                                          │
│  ┌──────────────────┐                                               │
│  │ Graceful         │  Is system degraded?                          │
│  │ Degradation      │  → Yes: Skip non-essential ops                │
│  │                  │  → No: Full functionality                     │
│  └────────┬─────────┘                                               │
│           ↓                                                          │
│  ┌──────────────────┐                                               │
│  │ Replica Router   │  Is this a read or write?                     │
│  │                  │  → Write: Use primary                         │
│  │                  │  → Read: Use replica                          │
│  └────────┬─────────┘                                               │
│           ↓                                                          │
│  ┌──────────────────┐                                               │
│  │ Retry Logic      │  Did operation fail?                          │
│  │                  │  → Transient: Retry with backoff              │
│  │                  │  → Permanent: Fail                            │
│  └────────┬─────────┘                                               │
│           ↓                                                          │
│     Success or Error                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### One-Line Configuration

For most applications, one flag is enough:

```python
from pynext.db.adapters import PostgresAdapter

adapter = PostgresAdapter(
    "postgresql://localhost/mydb",
    reliability=True,  # Enable everything with sensible defaults
)
```

This enables:
- Retry: 3 attempts, exponential backoff starting at 100ms
- Circuit breaker: Opens after 5 failures, 30s recovery
- Graceful degradation: Auto-detects stress

### Simple Production Configuration

```python
from pynext.db.adapters import PostgresAdapter

adapter = PostgresAdapter(
    # Primary
    primary=os.environ["PRIMARY_DATABASE_URL"],
    
    # Replicas
    replicas=[
        os.environ["REPLICA_1_URL"],
        os.environ["REPLICA_2_URL"],
    ],
    
    # Enable reliability
    reliability=True,
)
```

### Full Production Configuration

```python
from pynext.db.adapters import (
    PostgresAdapter,
    Replica, ReplicaConfig,
    RetryConfig,
    CircuitBreakerConfig,
    DegradationConfig, DegradationTrigger, DegradationLevel,
)

adapter = PostgresAdapter(
    # Primary connection
    primary="postgresql://primary.example.com/mydb",
    
    # Replica configuration
    replicas=ReplicaConfig(
        replicas=[
            Replica("postgresql://replica1.example.com/mydb", weight=2),
            Replica("postgresql://replica2.example.com/mydb", weight=1),
        ],
        max_lag_seconds=10,
        fallback_to_primary=True,
    ),
    
    # Retry configuration
    retry=RetryConfig(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=5.0,
        exponential_base=2,
        jitter=0.1,
    ),
    
    # Circuit breaker
    circuit_breaker=CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30,
        half_open_requests=3,
        scope="per_connection",
    ),
    
    # Graceful degradation
    degradation=DegradationConfig(
        triggers=[
            DegradationTrigger(metric="connection_usage", threshold=0.9),
            DegradationTrigger(metric="error_rate", threshold=0.1),
        ],
        levels=[
            DegradationLevel(threshold=0.8, actions=["reduce_pool"]),
            DegradationLevel(threshold=0.95, actions=["read_only_mode"]),
        ],
    ),
)
```

---

## Chapter 8: Monitoring and Alerts

### Getting Stats

```python
# Overall reliability stats
stats = adapter.reliability_stats()

print(f"Retry Stats:")
print(f"  Total retries: {stats.retry.total_retries}")
print(f"  Successful after retry: {stats.retry.successful_retries}")
print(f"  Failed after all retries: {stats.retry.exhausted_retries}")

print(f"\nCircuit Breaker:")
print(f"  State: {stats.circuit_breaker.state}")
print(f"  Failures: {stats.circuit_breaker.failure_count}")
print(f"  Opens: {stats.circuit_breaker.times_opened}")

print(f"\nReplicas:")
for replica in stats.replicas:
    print(f"  {replica.host}: {replica.lag_seconds}s lag, {replica.request_count} requests")

print(f"\nDegradation:")
print(f"  Level: {stats.degradation.current_level}")
print(f"  Active: {stats.degradation.is_degraded}")
```

### Setting Up Alerts

```python
from pynext.db.adapters import ReliabilityEvent

@adapter.on_event
async def handle_reliability_event(event: ReliabilityEvent):
    if event.type == "circuit_opened":
        await notify_ops(
            f"Circuit breaker opened! Errors: {event.error_count}"
        )
    
    elif event.type == "degradation_started":
        await notify_ops(
            f"Degradation level: {event.level}. Actions: {event.actions}"
        )
    
    elif event.type == "replica_lag":
        await notify_ops(
            f"Replica {event.replica} is {event.lag_seconds}s behind"
        )
```

### Health Check Endpoint

```python
from pynext.server import route

@route("/health")
async def health_check():
    db_health = await adapter.health_check()
    
    return {
        "status": "healthy" if db_health.healthy else "degraded",
        "database": {
            "primary": db_health.primary.status,
            "replicas": [r.status for r in db_health.replicas],
        },
        "reliability": {
            "circuit_breaker": db_health.circuit_breaker.state,
            "degradation_level": db_health.degradation.level,
        },
    }
```

---

## Configuration Reference

### All Configuration Options

```python
from pynext.db.adapters import (
    PostgresAdapter,
    RetryConfig,
    CircuitBreakerConfig,
    ReplicaConfig,
    DegradationConfig,
)

adapter = PostgresAdapter(
    # ═══════════════════════════════════════════════════════════
    # CONNECTION
    # ═══════════════════════════════════════════════════════════
    
    url: str = None,
    host: str = "localhost",
    port: int = 5432,
    database: str = None,
    user: str = "postgres",
    password: str = None,
    ssl: bool = False,
    
    # ═══════════════════════════════════════════════════════════
    # POOLING
    # ═══════════════════════════════════════════════════════════
    
    min_connections: int = 5,
    max_connections: int = 20,
    
    # ═══════════════════════════════════════════════════════════
    # RELIABILITY (simple)
    # ═══════════════════════════════════════════════════════════
    
    reliability: bool = False,  # Enable all with defaults
    
    # ═══════════════════════════════════════════════════════════
    # RELIABILITY (detailed)
    # ═══════════════════════════════════════════════════════════
    
    retry: RetryConfig = None,
    circuit_breaker: CircuitBreakerConfig = None,
    replicas: ReplicaConfig = None,
    degradation: DegradationConfig = None,
)
```

### RetryConfig

```python
RetryConfig(
    max_attempts: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: float = 0.1,
    retryable_errors: list = None,
    non_retryable_errors: list = None,
)
```

### CircuitBreakerConfig

```python
CircuitBreakerConfig(
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    half_open_requests: int = 3,
    scope: str = "global",  # "global", "per_connection", "per_query_type"
    failure_window: float = 60.0,
    counted_exceptions: list = None,
)
```

### ReplicaConfig

```python
ReplicaConfig(
    replicas: list[Replica | str] = [],
    max_lag_seconds: float = None,
    lag_check_interval: float = 10.0,
    strategy: str = "round_robin",  # "round_robin", "least_connections", "random"
    fallback_to_primary: bool = True,
)
```

### DegradationConfig

```python
DegradationConfig(
    triggers: list[DegradationTrigger] = [],
    levels: list[DegradationLevel] = [],
    recovery: RecoveryConfig = None,
)

DegradationTrigger(
    metric: str,  # "connection_usage", "error_rate", "query_latency", "replica_lag"
    threshold: float,
)

DegradationLevel(
    threshold: float,
    actions: list[str],
)
```

---

## Troubleshooting

### Common Issues

**"Circuit breaker is always open"**

The circuit might be opening too aggressively:

```python
# Increase failure threshold
circuit_breaker=CircuitBreakerConfig(
    failure_threshold=10,  # More tolerance
    failure_window=120,    # Count failures over longer period
)
```

Or you might have a persistent issue. Check:
- Is the database actually reachable?
- Are credentials correct?
- Is the network stable?

**"Retries are making things worse"**

If the database is overloaded, retries add more load:

```python
# Increase delay between retries
retry=RetryConfig(
    initial_delay=1.0,    # Start with 1 second
    max_delay=30.0,       # Up to 30 seconds
    max_attempts=2,       # Fewer attempts
)

# Or let circuit breaker handle it
circuit_breaker=CircuitBreakerConfig(
    failure_threshold=3,  # Open quickly
)
```

**"Reads are stale (replication lag)"**

```python
# Lower lag tolerance
replicas=ReplicaConfig(
    max_lag_seconds=2,  # Only use replicas within 2 seconds
)

# Or force reads from primary when needed
user = await User.get(user_id).use_primary()
```

**"Degradation won't recover"**

Check recovery configuration:

```python
degradation=DegradationConfig(
    recovery=RecoveryConfig(
        check_interval=10,    # Check more frequently
        stable_duration=30,   # Shorter stability requirement
        thresholds={
            "connection_usage": 0.5,  # Lower threshold to recover
        },
    ),
)
```

### Debugging

```python
# Enable debug logging
import logging
logging.getLogger("pynext.db.reliability").setLevel(logging.DEBUG)

# Check individual component status
print(f"Retry stats: {adapter.retry_stats()}")
print(f"Circuit state: {adapter.circuit_breaker_state()}")
print(f"Replica status: {adapter.replica_status()}")
print(f"Degradation: {adapter.degradation_status()}")
```

---

## Summary

Production reliability protects your application from failures:

1. **Retry Logic** - Handle transient failures by trying again
2. **Circuit Breakers** - Prevent cascade failures by failing fast
3. **Read Replicas** - Scale reads and add redundancy
4. **Graceful Degradation** - Keep core functionality when stressed

For most applications, one flag enables sensible defaults:

```python
adapter = PostgresAdapter("postgresql://...", reliability=True)
```

For production systems, add read replicas:

```python
adapter = PostgresAdapter(
    primary="postgresql://primary/db",
    replicas=["postgresql://replica1/db", "postgresql://replica2/db"],
    reliability=True,
)
```

**Next steps:**
- [POOLING.md](./POOLING.md) - Connection pool configuration
- [HIGH_LOAD.md](./HIGH_LOAD.md) - Performance optimization
- [POSTGRES.md](./POSTGRES.md) - PostgreSQL setup
