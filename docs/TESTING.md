# PyNext Testing Guide

## Quick Start

```bash
# 1. Start PostgreSQL test database
docker-compose up -d postgres

# 2. Run all tests
./scripts/test-db.sh

# 3. Stop when done
docker-compose down
```

---

## Database Setup

### Prerequisites

- **Docker Desktop** - Install from https://docker.com
- **Go 1.21+** - Install from https://go.dev (for Go bridge tests)
- **Python 3.10+** - With pip

### Start PostgreSQL

```bash
# Start test database (port 5433 to avoid conflicts)
docker-compose up -d postgres

# Verify it's running
docker ps | grep pynext_test_db

# Check logs if issues
docker-compose logs postgres
```

### Connection Details

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `5433` |
| Database | `pynext_test` |
| User | `pynext` |
| Password | `pynext` |
| URL | `postgresql://pynext:pynext@localhost:5433/pynext_test` |

### Stop Database

```bash
# Stop containers (keep data)
docker-compose down

# Stop and delete all data
docker-compose down -v
```

---

## Running Tests

### Test Script

```bash
# All database tests
./scripts/test-db.sh

# Specific test types
./scripts/test-db.sh unit         # Python unit tests
./scripts/test-db.sh go           # Go tests only
./scripts/test-db.sh parallel     # Parallel execution tests
./scripts/test-db.sh integration  # Integration tests

# Rebuild Go library first
./scripts/test-db.sh --rebuild
./scripts/test-db.sh unit --rebuild
```

### Manual pytest

```bash
# Set database URL
export PYNEXT_TEST_DB_URL="postgresql://pynext:pynext@localhost:5433/pynext_test"

# Run specific tests
pytest tests/unit/test_go_bridge_parallel.py -v
pytest tests/unit/test_go_bridge_*.py -v
pytest tests/integration/ -v

# With coverage
pytest tests/unit/test_go_bridge_*.py --cov=pynext_go --cov-report=html
```

### Go Tests

```bash
cd go
go test ./... -v
go test ./pkg/bridge -v -run Parallel  # Specific tests
```

---

## Test Fixtures

### Session-Scoped (Fast)

Shared connection pool across all tests. Use `clean_tables` for isolation:

```python
from tests.fixtures.database import requires_db, db_pool, clean_tables

@requires_db
def test_users(db_pool, clean_tables):
    clean_tables(["users", "orders"])
    
    with db_pool.connection() as conn:
        conn.execute("INSERT INTO users (name) VALUES ('Alice')")
        conn.commit()
        
        result = conn.execute("SELECT * FROM users").fetchall()
        assert len(result) == 1
```

### Per-Test Transaction (Isolated)

Auto-rollback after each test - no cleanup needed:

```python
from tests.fixtures.database import requires_db, db_transaction

@requires_db
def test_insert(db_transaction):
    db_transaction.execute("INSERT INTO users (name) VALUES ('Bob')")
    # Automatically rolled back after test!
```

### Go Bridge

```python
from tests.fixtures.database import requires_db, requires_go, go_bridge

@requires_db
@requires_go
def test_go_query(go_bridge):
    result = go_bridge.execute("SELECT 1 as num", [])
    assert result.scalar() == 1
```

### Seed Data

```python
from tests.fixtures.database import seed_users, seed_orders

def test_with_data(db_pool, clean_tables, seed_users, seed_orders):
    clean_tables(["orders", "users"])
    seed_users(100)           # 100 test users
    seed_orders(500, user_ids=list(range(1, 101)))  # 500 orders
```

---

## Test Data Seeding

### Create Test Tables

```python
# In Python
from tests.fixtures.database import create_test_tables

def test_setup(db_pool, create_test_tables):
    # Tables: users, orders, products, order_items
    pass
```

Or manually:

```sql
-- In psql or any SQL client
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    age INTEGER,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    total DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Bulk Seed Script

```bash
# Default: 1,000 users, 5,000 orders, 100 products
python scripts/seed-test-data.py

# Custom amounts
python scripts/seed-test-data.py --users 10000 --orders 50000 --products 200

# Clean tables first (recommended)
python scripts/seed-test-data.py --users 10000 --orders 50000 --clean

# Use custom database URL
python scripts/seed-test-data.py --url "postgresql://user:pass@host/db"
```

**Expected output:**

```
Connecting to postgresql://pynext:pynext@localhost:5433/pynext_test...
Creating tables...
Tables created.
Cleaning tables...
Tables cleaned.

Seeding data...
Seeding 10,000 users...
  Seeded 10,000 users in 0.06s
Seeding 100 products...
  Seeded 100 products.
Seeding 50,000 orders...
  Seeded 50,000 orders in 0.64s
Seeding ~100,000 order items...
  Seeded 150,042 order items in 2.10s

✅ Total seeding time: 2.84s

=== Database Statistics ===
  users: 10,000 rows
  products: 100 rows
  orders: 50,000 rows
  order_items: 150,042 rows
```

---

## CI/CD

GitHub Actions automatically runs database tests:

```yaml
# .github/workflows/test.yml
db-tests:
  services:
    postgres:
      image: postgres:16-alpine
      env:
        POSTGRES_USER: pynext
        POSTGRES_PASSWORD: pynext
        POSTGRES_DB: pynext_test
      ports:
        - 5433:5432
```

---

## Troubleshooting

### Docker won't start

**Option 1: Restart Docker Desktop (macOS)**

```bash
# Quit Docker Desktop
osascript -e 'quit app "Docker Desktop"'

# Wait a moment
sleep 3

# Start Docker Desktop
open -a Docker

# Wait for it to start (up to 60 seconds)
echo "Waiting for Docker..."
for i in {1..60}; do
    docker info > /dev/null 2>&1 && echo "Docker started!" && break
    sleep 1
done

# Verify
docker ps
```

**Option 2: Kill stuck processes**

```bash
# Kill any stuck Docker processes
killall Docker 2>/dev/null
killall com.docker.hyperkit 2>/dev/null

# Start fresh
open -a Docker
```

**Option 3: Check Docker Desktop status**

```bash
# Check if Docker processes are running
ps aux | grep -i docker | grep -v grep

# Check Docker socket
ls -la ~/.docker/run/docker.sock

# Test Docker API
docker version
```

**Common error: "Internal Server Error"**

This usually means Docker Desktop needs a restart. The daemon is running but not responding properly:

```bash
# Force quit and restart
osascript -e 'quit app "Docker Desktop"'
sleep 5
open -a Docker
sleep 15
docker ps
```

### Can't connect to database

```bash
# Check container is running
docker ps | grep pynext

# Check logs
docker-compose logs postgres

# Test connection
docker exec pynext_test_db pg_isready -U pynext -d pynext_test
```

### Go bridge not loading

```bash
# Rebuild Go library
./scripts/test-db.sh --rebuild

# Or manually
cd go
go build -buildmode=c-shared -o ../pynext_go/_lib/darwin_arm64/libpynext.dylib ./cmd/pynext/main.go
```

### Tests skip with "PostgreSQL not available"

```bash
# Make sure database is running
docker-compose up -d postgres

# Set environment variable
export PYNEXT_TEST_DB_URL="postgresql://pynext:pynext@localhost:5433/pynext_test"
```

---

## Performance Testing

### Parallel Query Benchmark

```python
import time
import pynext_go

pynext_go.init(primary="postgresql://pynext:pynext@localhost:5433/pynext_test")

# Sequential - runs one at a time
start = time.time()
for i in range(5):
    pynext_go.execute("SELECT pg_sleep(0.05)", [])
seq_time = time.time() - start
print(f"Sequential: {seq_time*1000:.0f}ms")  # ~250ms

# Parallel - all run simultaneously in Go goroutines
start = time.time()
pynext_go.execute_parallel([
    ("SELECT pg_sleep(0.05)", []) for _ in range(5)
])
par_time = time.time() - start
print(f"Parallel: {par_time*1000:.0f}ms")  # ~50ms

print(f"Speedup: {seq_time/par_time:.1f}x")  # ~5x faster!
```

### Real-World Performance (10K users, 50K orders)

```python
import pynext_go

pynext_go.init(primary="postgresql://pynext:pynext@localhost:5433/pynext_test")

# Single query performance
result = pynext_go.execute("SELECT COUNT(*) FROM users", [])
# ~3ms

result = pynext_go.execute("SELECT * FROM users LIMIT 1000", [])
# ~2ms for 1000 rows

# Parallel analytics queries
results = pynext_go.execute_parallel([
    ("SELECT COUNT(*) FROM users", []),
    ("SELECT COUNT(*) FROM orders", []),
    ("SELECT status, COUNT(*) FROM orders GROUP BY status", []),
    ("SELECT DATE_TRUNC('day', created_at), COUNT(*) FROM orders GROUP BY 1", []),
])
# ~25ms for all 4 queries (vs ~40ms sequential)
```

### Expected Performance Numbers

| Operation | Time |
|-----------|------|
| Simple COUNT | ~3ms |
| SELECT 1000 rows | ~2ms |
| Complex JOIN | ~15ms |
| 4 parallel queries | ~25ms |
| 5 × 50ms queries (parallel) | ~75ms |
| 5 × 50ms queries (sequential) | ~269ms |

**Speedup: 3-5x faster with parallel queries!**

### Go Bridge vs asyncpg Benchmarks

Run the official comparison benchmarks:

```bash
# Full benchmark suite
pytest tests/benchmarks/test_go_vs_asyncpg.py -v --benchmark-only

# Quick regression test
pytest tests/benchmarks/test_go_vs_asyncpg.py -v -k "Regression"
```

**Performance Targets (must not regress):**

| Metric | Target | Current |
|--------|--------|---------|
| 500 concurrent queries | < 500ms | ~284ms ✅ |
| 200 small queries | < 50ms | ~5ms ✅ |
| Parallel speedup | ≥ 3x | ~7.5x ✅ |

**Go Bridge vs asyncpg Comparison (after optimization):**

| Workload | Go Bridge | asyncpg | Winner |
|----------|-----------|---------|--------|
| Small query (100 rows) | 0.35ms | 0.53ms | **Go JSON 1.5x** 🚀 |
| Medium query (1000 rows) | 1.60ms | 1.72ms | **Go Arrow 1.1x** 🚀 |
| Large query (5000 rows) | 8.37ms | 9.81ms | **Go Arrow 1.2x** 🚀 |
| 5 parallel queries × 100 | 569ms | 1163ms | **Go 2.0x** 🚀 |
| 500 concurrent queries | 284ms | 3121ms | **Go 11x** 🚀 |

**Optimizations:** sonic (Go JSON), orjson (Python JSON), Arrow IPC

**Which Method to Use:**
- < 500 rows: `execute()` (JSON fastest)
- > 500 rows: `execute_arrow()` (Arrow faster)
- Multiple queries: `execute_parallel()` (2-3x faster)

**Go Bridge now beats asyncpg in all scenarios!**

---

## Test Summary

When all tests pass, you should see:

```
======================== 461 passed, 5 skipped in 2.08s ========================
```

### Test Categories

| Test File | Tests | Description |
|-----------|-------|-------------|
| `test_go_bridge_parallel.py` | 31 | Parallel query execution |
| `test_go_bridge_async.py` | 15 | Async API methods |
| `test_go_bridge_robustness.py` | 45 | Edge cases, error handling |
| `test_go_bridge_concurrency.py` | 20 | Thread safety |
| `test_go_bridge_boundary.py` | 25 | JSON serialization |
| `test_go_bridge_module.py` | 30 | Module-level functions |
| `test_go_adapter.py` | 40 | Database adapter |
| `test_go_fallback_simulation.py` | 17 | Fallback when Go unavailable |

### Go Tests

```bash
cd go && go test ./... -v
# Expected: All tests pass
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYNEXT_TEST_DB_URL` | `postgresql://pynext:pynext@localhost:5433/pynext_test` | Test database URL |
| `PYNEXT_SKIP_DB_TESTS` | (unset) | Skip all database tests if set |
| `PYNEXT_REQUIRE_GO` | (unset) | Fail if Go bridge unavailable |
| `PYNEXT_GO_LIB` | (auto-detect) | Path to Go shared library |

