# PyNext Database Observability

## Table of Contents
1. [Introduction](#introduction)
2. [Why Observability Matters](#why-observability-matters)
3. [The Three Pillars of Observability](#the-three-pillars-of-observability)
4. [Structured Logging](#structured-logging)
5. [Metrics Collection](#metrics-collection)
6. [Query Analysis](#query-analysis)
7. [Pool Monitoring](#pool-monitoring)
8. [Integration Guide](#integration-guide)
9. [Best Practices](#best-practices)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [API Reference](#api-reference)

---

## Introduction

### What is Observability?

Imagine you're driving a car. You have:
- **Dashboard gauges** (speedometer, fuel gauge, temperature) → **Metrics**
- **Warning lights** (check engine, oil pressure) → **Alerts**
- **GPS navigation** showing your route → **Traces**
- **Dashcam recording** what happens → **Logs**

**Observability** is having these "instruments" for your database operations. Without them, when something goes wrong, you're driving blind—no idea why queries are slow, connections are failing, or your database is overloaded.

### The Core Problem

```
❌ WITHOUT OBSERVABILITY:
"The website is slow. Why?"
*Hours of guessing and random fixes*

✅ WITH OBSERVABILITY:
"Query on users table averaging 2.5s, should be 50ms"
"Sequential scan detected, missing index on email column"
"Connection pool at 98% capacity, need to scale"
*Immediate diagnosis, targeted fix*
```

### PyNext's Approach

PyNext provides **complete observability out of the box**:

```python
from pynext.db.adapters import PostgresAdapter, LogConfig, MetricsConfig, AnalyzerConfig, MonitorConfig

# One-line setup with sensible defaults
adapter = PostgresAdapter(
    "postgresql://...",
    observability=True  # Enables everything with defaults
)

# Or fine-tune each component
adapter = PostgresAdapter(
    "postgresql://...",
    logging_config=LogConfig(slow_query_ms=100),
    metrics_config=MetricsConfig(backend="prometheus"),
    analyzer_config=AnalyzerConfig(suggest_indexes=True),
    monitor_config=MonitorConfig(leak_detection_timeout=300),
)
```

---

## Why Observability Matters

### The Kindergarten Explanation

Think of observability like a doctor's checkup for your database:

1. **Logs** = Patient's symptoms journal ("I felt dizzy at 3pm")
2. **Metrics** = Vital signs (heart rate, blood pressure over time)
3. **Traces** = Following the path of a request through your body
4. **Analysis** = The doctor interpreting all this to diagnose problems

### The Real-World Problem

Consider an e-commerce site during Black Friday:

```
WITHOUT OBSERVABILITY:
- 9:00 AM: Site is fine
- 10:30 AM: "Checkout is slow"
- 11:00 AM: "Users can't checkout at all"
- 11:30 AM: Team scrambles to find the cause
- 12:00 PM: Sales lost, customers frustrated
- 2:00 PM: Finally found: database connections exhausted

WITH OBSERVABILITY:
- 9:00 AM: Site is fine
- 10:00 AM: Alert: "Connection pool at 75% capacity"
- 10:05 AM: Dashboard shows increasing query latency
- 10:10 AM: Metrics indicate checkout queries taking 3x normal
- 10:15 AM: Analyzer suggests: "Add index on orders.created_at"
- 10:20 AM: Index added, problem solved before users notice
```

### The Cost of Not Knowing

| Scenario | Without Observability | With Observability |
|----------|----------------------|-------------------|
| Slow query | Hours debugging | Seconds to identify |
| Connection leak | Gradual degradation, hard to trace | Immediate detection |
| Missing index | Discovered after weeks of slowness | Suggested immediately |
| Pool exhaustion | Application crash | Early warning + auto-scale |
| Replica lag | Inconsistent reads | Monitored + auto-failover |

---

## The Three Pillars of Observability

### 1. Logs - The Story

Logs tell **what happened**. They're the narrative of your database operations.

```python
# What a log entry looks like
{
    "timestamp": "2024-01-15T10:30:45.123Z",
    "level": "WARNING",
    "event": "slow_query",
    "query": "SELECT * FROM users WHERE email = $1",
    "duration_ms": 2543.12,
    "query_id": "abc-123",
    "trace_id": "xyz-789",
    "table": "users",
    "status": "success"
}
```

### 2. Metrics - The Numbers

Metrics are **time-series data** about your database:

```python
# Metrics over time
pynext_db_query_duration_seconds{table="users", query_type="SELECT"}
pynext_db_connections_active{pool_name="main"}
pynext_db_errors_total{error_type="connection_timeout"}
pynext_db_slow_queries_total{table="orders"}
```

### 3. Traces - The Journey

Traces follow a request across your system:

```
[Frontend Request: abc-123]
  └─→ [API Handler: 15ms]
       └─→ [Database Query 1: 45ms] ← "SELECT * FROM users..."
       └─→ [Database Query 2: 120ms] ← "SELECT * FROM orders..." ← SLOW!
       └─→ [Cache Lookup: 2ms]
```

---

## Structured Logging

### The Kindergarten Version

Think of logs as a diary. An unstructured diary might say:

```
"Had a slow day, database was weird, something happened at 3pm"
```

A structured diary (log) says:

```json
{
    "date": "2024-01-15",
    "time": "15:00:00",
    "event": "slow_query",
    "duration": "2.5 seconds",
    "query": "SELECT * FROM orders",
    "cause": "missing index"
}
```

The structured version can be **searched, filtered, and analyzed** by computers!

### Basic Logging Setup

```python
from pynext.db.adapters import LogConfig, DBLogger

# Create a logging configuration
config = LogConfig(
    enabled=True,           # Turn logging on
    level="INFO",           # DEBUG, INFO, WARNING, ERROR, CRITICAL
    slow_query_ms=200,      # Log queries slower than 200ms as warnings
    log_params=False,       # Don't log query parameters (security!)
    logger_name="myapp.db"  # Logger name for filtering
)

# Create the logger
logger = DBLogger(config)

# Log a query
logger.log_query(
    query="SELECT * FROM users WHERE id = $1",
    duration_ms=45.3,
    status="success"
)
# Output: 2024-01-15 10:30:45 - myapp.db - INFO - query_executed: {...}
```

### Structured Logging with structlog

For production, use `structlog` for JSON output:

```python
from pynext.db.adapters import LogConfig, DBLogger

# Enable structlog for JSON output
config = LogConfig(
    enabled=True,
    level="INFO",
    slow_query_ms=100,
    structlog_enabled=True  # Outputs JSON instead of plain text
)

logger = DBLogger(config)

# Same log call, but now outputs JSON:
logger.log_query(
    query="SELECT * FROM orders WHERE user_id = $1",
    duration_ms=150.7,
    status="success"
)

# JSON Output (one line, formatted here for readability):
# {
#   "timestamp": "2024-01-15T10:30:45.123456Z",
#   "level": "warning",
#   "event": "slow_query",
#   "query": "SELECT * FROM orders WHERE user_id = $1",
#   "duration_ms": 150.7,
#   "status": "success",
#   "query_id": "abc-123-def-456",
#   "logger": "myapp.db"
# }
```

### Context Propagation

Track requests across your application:

```python
from pynext.db.adapters import DBLogger, LogConfig, query_id_var, trace_id_var, client_ip_var

logger = DBLogger(LogConfig(enabled=True))

# In your request handler
def handle_request(request):
    # Set context for this request
    logger.set_context(
        trace_id=request.headers.get("X-Trace-ID"),
        client_ip=request.client.host
    )
    
    # All subsequent logs will include this context
    result = db.query("SELECT * FROM users WHERE id = $1", user_id)
    
    # Clean up after request
    logger.reset_context()
```

### Log Levels Explained

```python
# DEBUG: Detailed information for developers
logger.debug("connection_acquired", pool_id=1, wait_time_ms=5)

# INFO: Normal operations
logger.info("query_executed", query="SELECT...", duration_ms=45)

# WARNING: Something unexpected but not critical
logger.warning("slow_query", query="SELECT...", duration_ms=2500)

# ERROR: Something failed
logger.error("query_error", query="SELECT...", error="connection refused")

# CRITICAL: System is in trouble
logger.critical("pool_exhausted", active=100, max=100, waiting=50)
```

### When to Log What

| Level | Use For | Example |
|-------|---------|---------|
| DEBUG | Connection acquisition, cache hits | "Got connection from pool in 2ms" |
| INFO | Successful queries, transactions | "Query completed in 45ms" |
| WARNING | Slow queries, pool getting full | "Query took 2.5s (threshold: 200ms)" |
| ERROR | Failed queries, connection errors | "Query failed: connection timeout" |
| CRITICAL | Pool exhaustion, complete failure | "All connections in use, 50 waiting" |

---

## Metrics Collection

### The Kindergarten Version

Imagine a fitness tracker for your database:
- **Steps** → **Queries executed**
- **Heart rate** → **Response time**
- **Sleep quality** → **Connection pool health**
- **Calories burned** → **Resource usage**

These numbers, tracked over time, show patterns and problems.

### Why Metrics Over Logs?

```
LOGS: "Query X took 100ms"
LOGS: "Query X took 110ms"
LOGS: "Query X took 95ms"
... (millions of entries)

METRICS: query_duration_avg{query="X"} = 101.67ms over last hour
```

Metrics **aggregate** data so you can see the forest, not just the trees.

### Basic Metrics Setup

```python
from pynext.db.adapters import MetricsConfig, MetricsCollector

# Configure metrics
config = MetricsConfig(
    enabled=True,
    backend="prometheus",  # or "opentelemetry"
    prefix="myapp_db",     # All metrics start with "myapp_db_"
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],  # Histogram buckets
    extra_labels={"environment": "production"},
)

# Create collector
collector = MetricsCollector(config)

# Record a query
collector.record_query_duration(
    duration_seconds=0.045,
    query_type="SELECT",
    table="users",
    status="success"
)

# Record pool state
collector.record_pool_state(
    pool_name="main",
    active=25,
    idle=5,
    waiting=0
)
```

### Metric Types Explained

#### 1. Gauges - Current State

```python
# "What is the value RIGHT NOW?"
collector.gauge("connections_active", 25, "Active database connections")
collector.gauge("connections_idle", 5, "Idle database connections")

# Gauge goes up and down
# 10:00 → 25 connections
# 10:01 → 30 connections (traffic spike)
# 10:02 → 15 connections (spike over)
```

#### 2. Counters - Cumulative Totals

```python
# "How many TOTAL since start?"
collector.counter("queries_total", 1, "Total queries executed")
collector.counter("errors_total", 1, "Total errors")

# Counter only goes up
# 10:00 → 1000 queries
# 10:01 → 1150 queries
# 10:02 → 1300 queries
```

#### 3. Histograms - Distribution

```python
# "What's the DISTRIBUTION of values?"
collector.histogram("query_duration_seconds", 0.045, "Query duration")

# Histogram tracks percentiles:
# p50 (median) = 0.05s
# p90 = 0.15s
# p99 = 0.8s  ← 1% of queries are slow!
```

### Key Metrics to Track

#### Query Performance

```python
# Duration histogram by query type and table
myapp_db_query_duration_seconds{query_type="SELECT", table="users"}

# Query count by status
myapp_db_queries_total{status="success", query_type="SELECT"}
myapp_db_queries_total{status="error", query_type="UPDATE"}

# Slow query count
myapp_db_slow_queries_total{table="orders"}
```

#### Connection Pool Health

```python
# Current pool state
myapp_db_connections_active{pool_name="main"}
myapp_db_connections_idle{pool_name="main"}
myapp_db_connections_waiting{pool_name="main"}

# Pool exhaustion events
myapp_db_pool_exhausted_total{pool_name="main"}

# Connection lifecycle
myapp_db_connections_created_total
myapp_db_connections_closed_total
```

#### Error Tracking

```python
# Errors by type
myapp_db_errors_total{error_type="connection_timeout"}
myapp_db_errors_total{error_type="query_timeout"}
myapp_db_errors_total{error_type="integrity_violation"}
```

### Prometheus Backend

```python
from pynext.db.adapters import MetricsConfig, PrometheusBackend

config = MetricsConfig(
    enabled=True,
    backend="prometheus",
    prometheus_config={
        "start_http_server": True,  # Expose /metrics endpoint
        "port": 9090,
        "addr": "0.0.0.0",
    }
)

# Your application now exposes metrics at http://localhost:9090/metrics
# Prometheus scrapes this endpoint every 15 seconds (configurable)
```

**Example Prometheus output:**
```
# HELP myapp_db_query_duration_seconds Duration of database queries
# TYPE myapp_db_query_duration_seconds histogram
myapp_db_query_duration_seconds_bucket{table="users",le="0.01"} 150
myapp_db_query_duration_seconds_bucket{table="users",le="0.05"} 890
myapp_db_query_duration_seconds_bucket{table="users",le="0.1"} 950
myapp_db_query_duration_seconds_bucket{table="users",le="+Inf"} 1000
myapp_db_query_duration_seconds_count{table="users"} 1000
myapp_db_query_duration_seconds_sum{table="users"} 45.67

# HELP myapp_db_connections_active Number of active database connections
# TYPE myapp_db_connections_active gauge
myapp_db_connections_active{pool_name="main"} 25
```

### OpenTelemetry Backend

```python
from pynext.db.adapters import MetricsConfig, OpenTelemetryBackend, OTLPConfig

config = MetricsConfig(
    enabled=True,
    backend="opentelemetry",
    opentelemetry_config={
        "endpoint": "http://otel-collector:4317",
        "service_name": "myapp-db",
        "metric_export_interval_ms": 5000,
    }
)

# Metrics are exported to your OpenTelemetry collector
# Works with Jaeger, Zipkin, Honeycomb, Datadog, etc.
```

---

## Query Analysis

### The Kindergarten Version

Imagine a mechanic looking at your car:
- **Slow acceleration** → "Your spark plugs are worn"
- **High fuel consumption** → "Try lower RPMs"
- **Strange noise** → "Brake pads need replacing"

The Query Analyzer is your database mechanic:
- **Slow query** → "Missing index on email column"
- **Full table scan** → "Add WHERE clause"
- **Fetching too much** → "Use SELECT specific columns"

### Why Query Analysis?

```
BEFORE:
"The orders page is slow" → "I have no idea why"

AFTER:
"The orders page is slow" →
  Analysis: "Sequential scan on orders table"
  Suggestion: "CREATE INDEX ON orders (user_id, created_at)"
  Estimated improvement: "From 2.5s to 0.05s (50x faster)"
```

### Basic Setup

```python
from pynext.db.adapters import QueryAnalyzer, AnalyzerConfig

config = AnalyzerConfig(
    enabled=True,
    slow_query_threshold_ms=100,  # Analyze queries slower than 100ms
    auto_explain=True,            # Run EXPLAIN ANALYZE automatically
    explain_format="json",        # JSON for easier parsing
    suggest_indexes=True,         # Suggest missing indexes
    suggest_rewrites=True,        # Suggest query improvements
)

analyzer = QueryAnalyzer(config)
```

### Understanding EXPLAIN Output

When a query is slow, we ask PostgreSQL "how did you execute this?"

```python
# Slow query
query = "SELECT * FROM orders WHERE user_id = 123"

# Ask PostgreSQL for execution plan
result = await analyzer.analyze_query(query, connection=conn)

# Result structure
{
    "explain": {
        "Node Type": "Seq Scan",        # ← BAD! Full table scan
        "Relation Name": "orders",
        "Filter": "(user_id = 123)",
        "Rows Removed by Filter": 999999,  # ← Scanned 1M rows!
        "Actual Rows": 15,                  # ← To find 15!
    },
    "query_time_ms": 2543.12,
    "suggestions": [
        {
            "type": "index_suggestion",
            "table": "orders",
            "columns": ["user_id"],
            "reason": "Sequential scan filtering 999,999 rows",
            "sql_hint": "CREATE INDEX ON orders (user_id);"
        }
    ]
}
```

### What the Analyzer Detects

#### 1. Sequential Scans (Seq Scan)

```python
# BAD: Sequential Scan
SELECT * FROM users WHERE email = 'test@example.com'
# PostgreSQL reads EVERY row to find the match

# SUGGESTION:
CREATE INDEX ON users (email);
# Now PostgreSQL jumps directly to matching rows
```

#### 2. Index-Only vs Index Scan

```python
# GOOD: Index Only Scan (fastest)
SELECT id FROM users WHERE email = 'test@example.com'
# All data is in the index itself

# OK: Index Scan (fast)
SELECT id, name FROM users WHERE email = 'test@example.com'
# Finds via index, fetches additional columns from table

# BAD: Bitmap Heap Scan
# Uses index but still needs lots of table reads
```

#### 3. Missing LIMIT

```python
# BAD: No LIMIT on potentially large result
SELECT * FROM orders WHERE status = 'pending'
# Could return millions of rows!

# SUGGESTION: Add LIMIT
SELECT * FROM orders WHERE status = 'pending' LIMIT 100
```

#### 4. SELECT *

```python
# BAD: Fetching all columns
SELECT * FROM users

# SUGGESTION: Specify columns
SELECT id, name, email FROM users
# Less data transferred, faster query
```

### Index Suggestions

```python
from pynext.db.adapters import IndexSuggestion

# Analyzer automatically generates suggestions
suggestion = IndexSuggestion(
    table="orders",
    columns=["user_id", "created_at"],
    reason="Sequential Scan detected with filter on user_id, sorted by created_at",
    severity="HIGH",
    sql_hint="CREATE INDEX ON orders (user_id, created_at);"
)

# Partial indexes for specific conditions
IndexSuggestion(
    table="orders",
    columns=["status"],
    reason="Frequent queries on status='pending'",
    sql_hint="CREATE INDEX ON orders (status) WHERE status = 'pending';"
)
```

### Query Hints

```python
from pynext.db.adapters import QueryHint

# Analyzer provides rewrite hints
hints = [
    QueryHint(
        hint="Use JOIN instead of subquery",
        reason="Subquery is executed for each row",
        severity="HIGH",
        query_pattern="SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
    ),
    QueryHint(
        hint="Add pagination with LIMIT and OFFSET",
        reason="Unbounded result set",
        severity="MEDIUM"
    ),
    QueryHint(
        hint="Consider using EXISTS instead of COUNT(*) > 0",
        reason="EXISTS stops at first match",
        severity="LOW"
    )
]
```

### Automatic Analysis Integration

```python
from pynext.db.adapters import PostgresAdapter, AnalyzerConfig

adapter = PostgresAdapter(
    "postgresql://...",
    analyzer_config=AnalyzerConfig(
        enabled=True,
        slow_query_threshold_ms=100,
        auto_explain=True,
        suggest_indexes=True,
    )
)

# Any query slower than 100ms is automatically analyzed
# Results logged as warnings with suggestions
```

---

## Pool Monitoring

### The Kindergarten Version

Imagine a parking lot (connection pool):
- **Spaces** = Maximum connections (max_size)
- **Parked cars** = Active connections (in use)
- **Empty spaces** = Idle connections (available)
- **Cars waiting** = Queued requests (waiting for a space)

Pool monitoring watches:
- Is the lot filling up? (**exhaustion warning**)
- Did someone park and never come back? (**connection leak**)
- Are some spaces actually unusable? (**dead connections**)

### Why Pool Monitoring?

```
WITHOUT MONITORING:
- Application crashes under load
- "Connection pool exhausted" error appears
- Spent hours finding the cause: a function that never released its connection

WITH MONITORING:
- Warning: "Pool at 80% capacity"
- Alert: "Connection held for 5 minutes by process_orders()"
- Fixed the leak before any user impact
```

### Basic Setup

```python
from pynext.db.adapters import PoolMonitor, MonitorConfig, DBLogger, LogConfig

# Create a logger for the monitor
logger = DBLogger(LogConfig(enabled=True, level="WARNING"))

# Configure monitoring
config = MonitorConfig(
    enabled=True,
    exhaustion_warning_threshold=0.8,  # Warn at 80% usage
    leak_detection_timeout=300,         # 5 minutes
    health_check_interval=30,           # Check every 30 seconds
    dead_connection_timeout=60,         # Mark dead after 60s unresponsive
)

# Create the monitor (usually done internally by adapter)
monitor = PoolMonitor(
    config=config,
    get_pool_state=lambda: (active, idle, waiting, max_size),
    mark_connection_dead=lambda conn: pool.remove(conn),
    get_idle_connections=lambda: pool.idle_connections,
    logger=logger,
)

# Start monitoring
monitor.start()
```

### Pool Exhaustion Detection

```python
# Configuration
config = MonitorConfig(
    exhaustion_warning_threshold=0.8  # 80%
)

# What happens:
# Pool: 100 max connections
# Currently: 85 active + 5 waiting = 90 in use
# Usage: 90/100 = 90% > 80% threshold
# Result: WARNING logged

# Log output:
# {
#   "event": "pool_exhaustion_warning",
#   "message": "Connection pool usage is high: 90/100 (90%)",
#   "active": 85,
#   "idle": 10,
#   "waiting": 5,
#   "max_size": 100,
#   "usage_ratio": 0.90
# }
```

### Connection Leak Detection

A "leak" is when code acquires a connection but never releases it:

```python
# BAD CODE (leak):
async def get_user(user_id):
    conn = await pool.acquire()
    result = await conn.fetch("SELECT * FROM users WHERE id = $1", user_id)
    # OOPS! Forgot to release the connection!
    return result

# GOOD CODE:
async def get_user(user_id):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM users WHERE id = $1", user_id)
    # Connection automatically released
    return result
```

The `LeakDetector` tracks acquired connections:

```python
from pynext.db.adapters import LeakDetector, MonitorConfig

config = MonitorConfig(
    leak_detection_timeout=300  # 5 minutes
)

detector = LeakDetector(config, on_leak_detected=handle_leak)

# When a connection is acquired
detector.acquire(connection)  # Records time and calling task

# 5 minutes later, if not released:
# {
#   "event": "connection_leak_detected",
#   "message": "Connection 12345 held by task process_orders for 301.5s",
#   "connection_id": 12345,
#   "held_duration_s": 301.5,
#   "acquiring_task": "process_orders"
# }
```

### Dead Connection Detection

Connections can become "dead" due to:
- Network issues
- Database server restart
- Firewall timeout
- PostgreSQL `idle_in_transaction_session_timeout`

The `HealthChecker` periodically tests idle connections:

```python
from pynext.db.adapters import HealthChecker, MonitorConfig

config = MonitorConfig(
    health_check_interval=30,      # Check every 30 seconds
    dead_connection_timeout=60,    # 60s timeout for health check
)

checker = HealthChecker(
    config=config,
    get_idle_connections=lambda: pool.idle,
    mark_connection_dead=lambda conn: pool.remove(conn),
    on_unhealthy=lambda conn, e: log_error(conn, e)
)

# Health check runs:
# SELECT 1;  -- Simple query to test connection
# If timeout or error → connection marked dead and removed
```

### Full Integration Example

```python
from pynext.db.adapters import (
    PostgresAdapter,
    LogConfig,
    MetricsConfig,
    MonitorConfig,
)

# Create fully observable adapter
adapter = PostgresAdapter(
    "postgresql://user:pass@localhost/mydb",
    
    # Logging: Track what's happening
    logging_config=LogConfig(
        enabled=True,
        level="INFO",
        slow_query_ms=200,
        structlog_enabled=True,
    ),
    
    # Metrics: Track numbers over time
    metrics_config=MetricsConfig(
        enabled=True,
        backend="prometheus",
        prefix="myapp_db",
    ),
    
    # Monitoring: Detect pool issues
    monitor_config=MonitorConfig(
        enabled=True,
        exhaustion_warning_threshold=0.8,
        leak_detection_timeout=300,
        health_check_interval=30,
    ),
)

# Connect and start monitoring
await adapter.connect()

# Use normally - all observability happens automatically
users = await adapter.fetch_all("SELECT * FROM users")

# Monitoring runs in background:
# - Warns if pool gets full
# - Detects leaked connections
# - Removes dead connections
```

---

## Integration Guide

### Complete Production Setup

```python
from pynext.db.adapters import (
    PostgresAdapter,
    LogConfig,
    MetricsConfig,
    AnalyzerConfig,
    MonitorConfig,
)

# Production-ready configuration
adapter = PostgresAdapter(
    "postgresql://user:pass@localhost/mydb",
    
    # Connection pool settings
    min_connections=10,
    max_connections=100,
    
    # Logging: Structured, JSON, with context
    logging_config=LogConfig(
        enabled=True,
        level="INFO",
        slow_query_ms=200,
        log_params=False,  # Never log sensitive parameters!
        structlog_enabled=True,
        logger_name="production.database",
    ),
    
    # Metrics: Export to Prometheus
    metrics_config=MetricsConfig(
        enabled=True,
        backend="prometheus",
        prefix="production_db",
        prometheus_config={
            "start_http_server": True,
            "port": 9090,
        },
        extra_labels={
            "environment": "production",
            "service": "api-server",
        }
    ),
    
    # Analysis: Find slow queries
    analyzer_config=AnalyzerConfig(
        enabled=True,
        slow_query_threshold_ms=100,
        auto_explain=True,
        explain_format="json",
        suggest_indexes=True,
        suggest_rewrites=True,
    ),
    
    # Monitoring: Detect pool issues
    monitor_config=MonitorConfig(
        enabled=True,
        exhaustion_warning_threshold=0.75,  # Warn early in production
        leak_detection_timeout=120,         # 2 minutes
        health_check_interval=15,           # More frequent checks
        dead_connection_timeout=30,
    ),
)

await adapter.connect()
```

### Setting Up Dashboards

#### Prometheus + Grafana

1. **Prometheus scrape config** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'pynext-db'
    static_configs:
      - targets: ['your-app:9090']
    scrape_interval: 15s
```

2. **Grafana Dashboard Panels**:

```python
# Query Duration (p50, p90, p99)
histogram_quantile(0.50, rate(production_db_query_duration_seconds_bucket[5m]))
histogram_quantile(0.90, rate(production_db_query_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(production_db_query_duration_seconds_bucket[5m]))

# Connection Pool Usage
production_db_connections_active / production_db_connections_max * 100

# Error Rate
rate(production_db_errors_total[5m])

# Slow Query Rate
rate(production_db_slow_queries_total[5m])
```

### Setting Up Alerts

#### Prometheus Alerting Rules

```yaml
groups:
  - name: database
    rules:
      # Alert if query latency is high
      - alert: HighDatabaseLatency
        expr: histogram_quantile(0.99, rate(production_db_query_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database query latency"
          description: "P99 query latency is {{ $value }}s"

      # Alert if pool is nearly exhausted
      - alert: ConnectionPoolExhaustion
        expr: production_db_connections_active / production_db_connections_max > 0.9
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Pool usage is {{ $value | humanizePercentage }}"

      # Alert if errors are spiking
      - alert: DatabaseErrors
        expr: rate(production_db_errors_total[5m]) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database errors increasing"
          description: "Error rate is {{ $value }} per second"
```

### OpenTelemetry Integration

```python
from pynext.db.adapters import MetricsConfig, OTLPConfig

# Export to OpenTelemetry Collector
config = MetricsConfig(
    enabled=True,
    backend="opentelemetry",
    opentelemetry_config={
        "endpoint": "http://otel-collector:4317",
        "service_name": "my-service",
        "propagator": "w3c_trace_context",  # or "b3"
        "headers": {
            "Authorization": "Bearer token",  # For cloud providers
        }
    }
)
```

---

## Best Practices

### 1. Log Appropriately

```python
# DO: Log meaningful events at appropriate levels
logger.info("query_executed", query_type="SELECT", table="users", duration_ms=45)
logger.warning("slow_query", query=truncated_query, duration_ms=2500)

# DON'T: Log sensitive data
logger.info("query", params={"password": "secret123"})  # NEVER!

# DON'T: Log every query in production (too much noise)
logger.debug("query", query=full_sql)  # OK for development only
```

### 2. Choose Metrics Wisely

```python
# DO: Metrics that matter
collector.histogram("query_duration", duration, labels={"operation": "find_user"})

# DON'T: Too many unique labels (cardinality explosion)
collector.counter("queries", labels={"user_id": user_id})  # BAD! Millions of series

# DO: Aggregate by bounded categories
collector.counter("queries", labels={"user_type": "premium"})  # GOOD
```

### 3. Set Reasonable Thresholds

```python
# Development: Catch early, be aggressive
dev_config = AnalyzerConfig(
    slow_query_threshold_ms=50,   # Strict
    auto_explain=True,             # Explain everything
)

# Production: Balance noise vs insight
prod_config = AnalyzerConfig(
    slow_query_threshold_ms=200,  # Reasonable
    auto_explain=False,            # Only on-demand (EXPLAIN has overhead)
)
```

### 4. Handle High Cardinality

```python
# BAD: User ID as label (millions of unique values)
collector.counter("user_queries", labels={"user_id": str(user_id)})

# GOOD: Use bounded categories
user_type = "premium" if user.is_premium else "free"
collector.counter("user_queries", labels={"user_type": user_type})
```

### 5. Implement Request Tracing

```python
from uuid import uuid4

async def handle_request(request):
    # Generate or extract trace ID
    trace_id = request.headers.get("X-Trace-ID", str(uuid4()))
    
    # Set context for all logs
    logger.set_context(trace_id=trace_id)
    
    try:
        result = await process_request(request)
        return result
    finally:
        logger.reset_context()
```

---

## Troubleshooting Guide

### Problem: "Slow queries but no obvious cause"

**Solution: Enable auto-explain**

```python
config = AnalyzerConfig(
    enabled=True,
    slow_query_threshold_ms=100,
    auto_explain=True,
    explain_format="json"
)

# Check logs for suggestions
# Look for:
# - "Sequential Scan" → Missing index
# - "Rows Removed by Filter" high → Inefficient filter
# - "Sort" → Consider index with ORDER BY columns
```

### Problem: "Connection pool exhaustion"

**Solution: Check for leaks and tune pool size**

```python
# 1. Enable leak detection
config = MonitorConfig(
    enabled=True,
    leak_detection_timeout=60,  # Shorten for debugging
)

# 2. Check logs for leak warnings
# Look for: "connection_leak_detected"

# 3. Common causes:
# - async with not used
# - Exception before release
# - Long-running transactions

# 4. If no leaks, increase pool size
adapter = PostgresAdapter(
    "...",
    max_connections=200,  # Increase from default
)
```

### Problem: "Metrics not appearing in Prometheus"

**Solution: Check endpoint configuration**

```python
# 1. Verify HTTP server is running
config = MetricsConfig(
    enabled=True,
    backend="prometheus",
    prometheus_config={
        "start_http_server": True,
        "port": 9090,  # Confirm port
        "addr": "0.0.0.0",  # Listen on all interfaces
    }
)

# 2. Test endpoint manually
# curl http://localhost:9090/metrics

# 3. Check Prometheus scrape config
# Target should match your app's address
```

### Problem: "Too much log noise"

**Solution: Adjust log levels and thresholds**

```python
# Reduce logging verbosity
config = LogConfig(
    enabled=True,
    level="WARNING",  # Only warnings and errors
    slow_query_ms=500,  # Higher threshold
)

# Or use structured logging with filters
# In production, filter by level in log aggregator
```

### Problem: "Health checks failing"

**Solution: Check network and database**

```python
# 1. Increase timeout
config = MonitorConfig(
    dead_connection_timeout=120,  # 2 minutes
    health_check_interval=60,     # Less frequent
)

# 2. Common causes:
# - Firewall dropping idle connections
# - Database overloaded
# - Network latency spikes

# 3. Enable keepalive at PostgreSQL level
adapter = PostgresAdapter(
    "...",
    server_settings={
        "tcp_keepalives_idle": "60",
        "tcp_keepalives_interval": "10",
        "tcp_keepalives_count": "6",
    }
)
```

---

## API Reference

### LogConfig

```python
@dataclass
class LogConfig:
    """Configuration for database logging."""
    enabled: bool = True              # Enable/disable logging
    level: str = "INFO"               # DEBUG, INFO, WARNING, ERROR, CRITICAL
    slow_query_ms: int = 200          # Threshold for slow query warnings
    log_params: bool = False          # Log query parameters (security risk!)
    structlog_enabled: bool = False   # Use structlog for JSON output
    logger_name: str = "pynext.db"    # Logger name for filtering
    extra_context: Optional[Dict[str, Any]] = None  # Additional context
```

### DBLogger

```python
class DBLogger:
    """Manages structured logging for database operations."""
    
    def __init__(self, config: LogConfig): ...
    
    def debug(self, event_name: str, **kwargs): ...
    def info(self, event_name: str, **kwargs): ...
    def warning(self, event_name: str, **kwargs): ...
    def error(self, event_name: str, **kwargs): ...
    def critical(self, event_name: str, **kwargs): ...
    
    def log_query(
        self,
        query: str,
        duration_ms: float,
        status: str = "success",
        error: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ): ...
    
    def set_context(
        self,
        query_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        **kwargs
    ): ...
    
    def reset_context(self): ...
```

### MetricsConfig

```python
@dataclass
class MetricsConfig:
    """Configuration for database metrics collection."""
    enabled: bool = True
    backend: Literal["prometheus", "opentelemetry", "none"] = "none"
    prefix: str = "pynext_db"
    buckets: List[float] = field(default_factory=lambda: [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0])
    extra_labels: Optional[Dict[str, str]] = None
    prometheus_config: Optional[Dict[str, Any]] = None
    opentelemetry_config: Optional[Dict[str, Any]] = None
```

### MetricsCollector

```python
class MetricsCollector:
    """Collects and aggregates database-related metrics."""
    
    def __init__(self, config: MetricsConfig): ...
    
    def gauge(self, name: str, value: float, description: str, labels: Optional[Dict[str, str]] = None): ...
    def counter(self, name: str, increment: float = 1.0, description: str = "", labels: Optional[Dict[str, str]] = None): ...
    def histogram(self, name: str, value: float, description: str, labels: Optional[Dict[str, str]] = None): ...
    
    def record_query_duration(self, duration_seconds: float, query_type: str, table: Optional[str] = None, status: str = "success"): ...
    def record_error(self, error_type: str, query_type: Optional[str] = None): ...
    def record_pool_state(self, pool_name: str, active: int, idle: int, waiting: int): ...
    def record_pool_exhaustion(self, pool_name: str): ...
    def record_slow_query(self, table: Optional[str] = None, query_type: Optional[str] = None): ...
    
    def shutdown(self): ...
```

### AnalyzerConfig

```python
@dataclass
class AnalyzerConfig:
    """Configuration for the Query Analyzer."""
    enabled: bool = True
    slow_query_threshold_ms: int = 100
    auto_explain: bool = True
    explain_format: Literal["text", "json"] = "json"
    suggest_indexes: bool = True
    suggest_rewrites: bool = True
    ignore_patterns: List[str] = field(default_factory=list)
```

### QueryAnalyzer

```python
class QueryAnalyzer:
    """Analyzes database queries for performance issues."""
    
    def __init__(self, config: AnalyzerConfig): ...
    
    async def analyze_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        connection: Any = None
    ) -> Dict[str, Any]: ...
```

### MonitorConfig

```python
@dataclass
class MonitorConfig:
    """Configuration for the Pool Monitor."""
    enabled: bool = True
    exhaustion_warning_threshold: float = 0.8
    leak_detection_timeout: int = 300  # seconds
    health_check_interval: int = 30    # seconds
    dead_connection_timeout: int = 60  # seconds
    on_warning: Optional[Callable] = None
    on_error: Optional[Callable] = None
```

### PoolMonitor

```python
class PoolMonitor:
    """Monitors connection pool for exhaustion, leaks, and dead connections."""
    
    def __init__(
        self,
        config: MonitorConfig,
        get_pool_state: Callable,
        mark_connection_dead: Callable,
        get_idle_connections: Callable,
        logger: DBLogger
    ): ...
    
    def start(self): ...
    def stop(self): ...
    def record_acquisition(self, connection: Any): ...
    def record_release(self, connection: Any): ...
```

---

## Summary

PyNext's observability features give you complete visibility into your database operations:

| Component | What It Does | Key Benefit |
|-----------|-------------|-------------|
| **Logging** | Records events with context | Debugging and auditing |
| **Metrics** | Tracks numbers over time | Dashboards and alerts |
| **Analysis** | Explains slow queries | Performance optimization |
| **Monitoring** | Watches connection pool | Prevents outages |

**Quick Start**:

```python
from pynext.db.adapters import PostgresAdapter

# Enable everything with sensible defaults
adapter = PostgresAdapter(
    "postgresql://...",
    observability=True
)
```

**Production Setup**:

```python
from pynext.db.adapters import (
    PostgresAdapter,
    LogConfig,
    MetricsConfig,
    AnalyzerConfig,
    MonitorConfig,
)

adapter = PostgresAdapter(
    "postgresql://...",
    logging_config=LogConfig(structlog_enabled=True),
    metrics_config=MetricsConfig(backend="prometheus"),
    analyzer_config=AnalyzerConfig(suggest_indexes=True),
    monitor_config=MonitorConfig(exhaustion_warning_threshold=0.75),
)
```

With PyNext observability, you'll never be flying blind again. You'll know exactly what your database is doing, when it's struggling, and how to fix it—before your users even notice a problem.

