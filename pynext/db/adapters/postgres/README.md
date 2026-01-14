# PostgreSQL Adapter Package

This directory contains a modular, organized PostgreSQL adapter for PyNext.

## Directory Structure

```
postgres/
├── __init__.py          # Re-exports all symbols for convenience
├── README.md            # This file
│
├── core/                # Essential adapter components
│   ├── adapter.py       # Main PostgresAdapter class
│   ├── url.py           # Connection URL parsing (PostgresConfig)
│   ├── types.py         # Python ↔ PostgreSQL type conversion
│   └── cache.py         # Statement caching
│
├── pool/                # Connection pool management (Phase 5.2)
│   ├── pool.py          # Auto-scaling connection pool
│   ├── queue.py         # Fair request queuing with backpressure
│   ├── lifecycle.py     # Connection lifecycle management
│   ├── warmup.py        # Connection warming for cold starts
│   └── external.py      # External pooler support (PgBouncer, pgpool)
│
├── reliability/         # Fault tolerance (Phase 5.3)
│   ├── retry.py         # Automatic retry with exponential backoff
│   ├── circuit.py       # Circuit breaker pattern
│   ├── replica.py       # Read replica routing
│   └── degradation.py   # Graceful degradation under load
│
├── performance/         # Query optimization (Phase 5.4)
│   ├── timeout.py       # Per-query timeout management
│   ├── query_cache.py   # Result caching with smart invalidation
│   ├── coalesce.py      # Query coalescing for identical requests
│   ├── pipeline.py      # Query pipelining for reduced round trips
│   ├── batch.py         # Batch optimization for bulk operations
│   └── scaling.py       # Adaptive pool scaling based on load
│
├── observability/       # Monitoring & logging (Phase 5.5)
│   ├── logging.py       # Structured logging with context
│   ├── metrics.py       # Metrics collection framework
│   ├── prometheus.py    # Prometheus metrics backend
│   ├── opentelemetry.py # OpenTelemetry tracing backend
│   ├── analyzer.py      # Query analysis and optimization hints
│   └── monitor.py       # Pool health monitoring and leak detection
│
└── queries/             # Advanced query features (Phase 5.7)
    ├── query_timeout.py # Chainable query timeout with context manager
    ├── explain.py       # EXPLAIN/ANALYZE parsing and optimization
    ├── pagination.py    # Cursor-based and offset pagination
    ├── prepared.py      # Prepared statement caching
    └── cancel.py        # Query cancellation and tracking
```

## Usage

### Recommended Imports (New Style)

```python
# Core adapter
from pynext.db.adapters.postgres.core import PostgresAdapter, PostgresConfig

# Reliability features
from pynext.db.adapters.postgres.reliability import (
    RetryConfig, CircuitBreaker, ReplicaManager
)

# Performance optimization
from pynext.db.adapters.postgres.performance import (
    QueryCache, BatchOptimizer, AdaptiveScaler
)

# Observability
from pynext.db.adapters.postgres.observability import (
    LogConfig, MetricsConfig, QueryAnalyzer
)
```

### Convenience Import (All-in-One)

```python
# Import everything from the package
from pynext.db.adapters.postgres import (
    PostgresAdapter,
    RetryConfig,
    CircuitBreaker,
    LogConfig,
)
```

### Main Entry Point (Unchanged)

```python
# Import from the main adapters module
from pynext.db.adapters import PostgresAdapter, RetryConfig, LogConfig
```

## Why This Structure?

1. **Discoverability**: Features are grouped by purpose, making it easy to find related functionality.

2. **Reduced Import Overhead**: Import only what you need from specific submodules.

3. **Clear Dependencies**: Each submodule has explicit dependencies, making the codebase easier to understand.

4. **Better IDE Support**: Smaller, focused files provide better autocomplete and navigation.

5. **Maintainability**: Changes to one feature area don't affect unrelated code.

## Migration Note

As of this version, the flat `postgres_*.py` files have been removed. All imports should use one of:

1. **Direct submodule imports** (recommended):
   ```python
   from pynext.db.adapters.postgres.reliability.retry import RetryConfig
   ```

2. **Package-level imports**:
   ```python
   from pynext.db.adapters.postgres import RetryConfig
   ```

3. **Main adapters module**:
   ```python
   from pynext.db.adapters import RetryConfig
   ```

## Related Documentation

- [Database Overview](../../../../docs/database/OVERVIEW.md)
- [Connection Pooling](../../../../docs/database/POOLING.md)
- [Reliability Features](../../../../docs/database/RELIABILITY.md)
- [Performance Tuning](../../../../docs/database/PERFORMANCE.md)

