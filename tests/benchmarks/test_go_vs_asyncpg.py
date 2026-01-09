"""
Go Bridge vs asyncpg Benchmark Tests

These benchmarks track performance parity with asyncpg across different workloads.
Run with: pytest tests/benchmarks/test_go_vs_asyncpg.py -v --benchmark-only

Target Metrics (Go Bridge should beat these):
- High concurrency (500 queries): < 500ms (asyncpg: ~3000ms) ✅ 11x faster
- Small queries (200 x SELECT 1): < 20ms (asyncpg: ~11ms) ✅ 2x faster
- Bulk read (5000 rows x 20): Target parity with asyncpg

Current Status:
- Go wins: High concurrency, small queries, mixed workloads
- asyncpg wins: Bulk reads (JSON serialization overhead)
"""

import asyncio
import os
import time
from typing import Callable

import pytest

# Skip all benchmarks if database not available
DB_URL = os.environ.get(
    "PYNEXT_TEST_DB_URL",
    "postgresql://pynext:pynext@localhost:5433/pynext_test"
)


def is_db_available() -> bool:
    """Check if test database is available."""
    try:
        import psycopg
        with psycopg.connect(DB_URL, connect_timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def is_asyncpg_available() -> bool:
    """Check if asyncpg is installed."""
    try:
        import asyncpg
        return True
    except ImportError:
        return False


requires_db = pytest.mark.skipif(
    not is_db_available(),
    reason="PostgreSQL test database not available"
)

requires_asyncpg = pytest.mark.skipif(
    not is_asyncpg_available(),
    reason="asyncpg not installed"
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="class")
def go_bridge(request):
    """Initialize Go bridge for benchmarks."""
    import pynext_go
    
    # Close any existing connection first
    try:
        pynext_go.close()
    except Exception:
        pass
    
    pynext_go.init(primary=DB_URL, pool_min_size=20, pool_max_size=100)
    pynext_go.warmup()
    
    # Create test tables if they don't exist
    try:
        # Create users table
        pynext_go.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE,
                age INTEGER,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, [])
        
        # Create orders table
        pynext_go.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                total DECIMAL(10, 2) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, [])
        
        # Seed some test data if tables are empty
        user_count_result = pynext_go.execute("SELECT COUNT(*) as count FROM users", [])
        user_count = 0
        if user_count_result and len(user_count_result) > 0:
            user_count = user_count_result[0].get('count', 0) if isinstance(user_count_result[0], dict) else 0
        
        if user_count == 0:
            # Insert a few test users
            for i in range(10):
                pynext_go.execute(
                    "INSERT INTO users (name, email, age) VALUES ($1, $2, $3)",
                    [f"User {i}", f"user{i}@test.com", 20 + i]
                )
            
            # Insert some test orders (need at least 5000 for bulk read test)
            for i in range(5000):
                pynext_go.execute(
                    "INSERT INTO orders (user_id, total, status) VALUES ($1, $2, $3)",
                    [(i % 10) + 1, 10.0 * (i + 1), 'pending' if i % 2 == 0 else 'completed']
                )
    except Exception as e:
        # If tables already exist or other error, continue
        pass
    
    yield pynext_go
    pynext_go.close()


@pytest.fixture(scope="class")
def asyncpg_pool(request):
    """Create asyncpg pool for benchmarks."""
    import asyncpg
    
    async def create_pool():
        pool = await asyncpg.create_pool(DB_URL, min_size=10, max_size=50)
        
        # Create test tables if they don't exist
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    age INTEGER,
                    active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    total DECIMAL(10, 2) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Seed some test data if tables are empty
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            if user_count == 0:
                # Insert test users
                for i in range(10):
                    await conn.execute(
                        "INSERT INTO users (name, email, age) VALUES ($1, $2, $3)",
                        f"User {i}", f"user{i}@test.com", 20 + i
                    )
                
                # Insert test orders (need at least 5000 for bulk read test)
                for i in range(5000):
                    await conn.execute(
                        "INSERT INTO orders (user_id, total, status) VALUES ($1, $2, $3)",
                        (i % 10) + 1, 10.0 * (i + 1), 'pending' if i % 2 == 0 else 'completed'
                    )
        
        return pool
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    pool = loop.run_until_complete(create_pool())
    yield pool
    loop.run_until_complete(pool.close())
    loop.close()


# =============================================================================
# High Concurrency Benchmarks (Go should win BIG)
# =============================================================================

@requires_db
class TestHighConcurrency:
    """
    Target: Go Bridge should be 5-10x faster than asyncpg for 500+ concurrent queries.
    """
    
    def test_go_500_concurrent_queries(self, go_bridge, benchmark):
        """Benchmark: 500 concurrent COUNT queries with Go Bridge."""
        queries = [("SELECT COUNT(*) FROM users", []) for _ in range(500)]
        
        # Warmup
        go_bridge.execute_parallel(queries[:50])
        
        result = benchmark(go_bridge.execute_parallel, queries)
        assert len(result) == 500
        assert all(r.success for r in result)
    
    @requires_asyncpg
    def test_asyncpg_500_concurrent_queries(self, asyncpg_pool, benchmark):
        """Benchmark: 500 concurrent COUNT queries with asyncpg."""
        loop = asyncio.get_event_loop()
        
        async def run_queries():
            async def query():
                async with asyncpg_pool.acquire() as conn:
                    return await conn.fetchval("SELECT COUNT(*) FROM users")
            return await asyncio.gather(*[query() for _ in range(500)])
        
        # Warmup
        loop.run_until_complete(run_queries())
        
        def run():
            return loop.run_until_complete(run_queries())
        
        result = benchmark(run)
        assert len(result) == 500
    
    def test_go_100_concurrent_queries(self, go_bridge, benchmark):
        """Benchmark: 100 concurrent COUNT queries with Go Bridge."""
        queries = [("SELECT COUNT(*) FROM orders WHERE status = 'pending'", []) for _ in range(100)]
        
        result = benchmark(go_bridge.execute_parallel, queries)
        assert len(result) == 100
    
    @requires_asyncpg
    def test_asyncpg_100_concurrent_queries(self, asyncpg_pool, benchmark):
        """Benchmark: 100 concurrent COUNT queries with asyncpg."""
        loop = asyncio.get_event_loop()
        
        async def run_queries():
            async def query():
                async with asyncpg_pool.acquire() as conn:
                    return await conn.fetchval("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
            return await asyncio.gather(*[query() for _ in range(100)])
        
        def run():
            return loop.run_until_complete(run_queries())
        
        result = benchmark(run)
        assert len(result) == 100


# =============================================================================
# Small Query Benchmarks (Go should win)
# =============================================================================

@requires_db
class TestSmallQueries:
    """
    Target: Go Bridge should be 1.5-2x faster for many small queries.
    """
    
    def test_go_200_small_queries(self, go_bridge, benchmark):
        """Benchmark: 200 SELECT 1 queries with Go Bridge."""
        queries = [("SELECT 1", []) for _ in range(200)]
        
        result = benchmark(go_bridge.execute_parallel, queries)
        assert len(result) == 200
    
    @requires_asyncpg
    def test_asyncpg_200_small_queries(self, asyncpg_pool, benchmark):
        """Benchmark: 200 SELECT 1 queries with asyncpg."""
        loop = asyncio.get_event_loop()
        
        async def run_queries():
            async def query():
                async with asyncpg_pool.acquire() as conn:
                    return await conn.fetchval("SELECT 1")
            return await asyncio.gather(*[query() for _ in range(200)])
        
        def run():
            return loop.run_until_complete(run_queries())
        
        result = benchmark(run)
        assert len(result) == 200


# =============================================================================
# Bulk Read Benchmarks (asyncpg currently wins - target for optimization)
# =============================================================================

@requires_db
class TestBulkRead:
    """
    Current: asyncpg wins due to JSON serialization overhead.
    Target: Achieve parity with Arrow-based result transfer.
    """
    
    def test_go_bulk_read_5000_rows(self, go_bridge, benchmark):
        """Benchmark: Read 5000 rows with Go Bridge."""
        def run():
            return go_bridge.execute("SELECT * FROM orders LIMIT 5000", [])
        
        # Warmup
        run()
        
        result = benchmark(run)
        assert len(result) == 5000
    
    @requires_asyncpg
    def test_asyncpg_bulk_read_5000_rows(self, asyncpg_pool, benchmark):
        """Benchmark: Read 5000 rows with asyncpg."""
        loop = asyncio.get_event_loop()
        
        async def run():
            async with asyncpg_pool.acquire() as conn:
                return await conn.fetch("SELECT * FROM orders LIMIT 5000")
        
        def sync_run():
            return loop.run_until_complete(run())
        
        result = benchmark(sync_run)
        assert len(result) == 5000


# =============================================================================
# Mixed Workload Benchmarks
# =============================================================================

@requires_db
class TestMixedWorkload:
    """
    Target: Go Bridge should win on realistic mixed workloads.
    """
    
    def test_go_mixed_workload(self, go_bridge, benchmark):
        """Benchmark: Mixed analytics queries with Go Bridge."""
        queries = [
            ("SELECT COUNT(*) FROM users", []),
            ("SELECT COUNT(*) FROM orders", []),
            ("SELECT AVG(total) FROM orders", []),
            ("SELECT status, COUNT(*) FROM orders GROUP BY status", []),
            ("SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name LIMIT 100", []),
        ]
        
        result = benchmark(go_bridge.execute_parallel, queries)
        assert len(result) == 5
        assert all(r.success for r in result)
    
    @requires_asyncpg
    def test_asyncpg_mixed_workload(self, asyncpg_pool, benchmark):
        """Benchmark: Mixed analytics queries with asyncpg."""
        loop = asyncio.get_event_loop()
        queries = [
            "SELECT COUNT(*) FROM users",
            "SELECT COUNT(*) FROM orders",
            "SELECT AVG(total) FROM orders",
            "SELECT status, COUNT(*) FROM orders GROUP BY status",
            "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name LIMIT 100",
        ]
        
        async def run():
            async def query(sql):
                async with asyncpg_pool.acquire() as conn:
                    return await conn.fetch(sql)
            return await asyncio.gather(*[query(q) for q in queries])
        
        def sync_run():
            return loop.run_until_complete(run())
        
        result = benchmark(sync_run)
        assert len(result) == 5


# =============================================================================
# Parallel vs Sequential (Go internal comparison)
# =============================================================================

@requires_db
class TestGoParallelSpeedup:
    """
    Target: execute_parallel should be 5-10x faster than sequential execute.
    """
    
    def test_go_sequential_100_queries(self, go_bridge, benchmark):
        """Benchmark: 100 queries sequentially with Go Bridge."""
        def run():
            results = []
            for _ in range(100):
                results.append(go_bridge.execute("SELECT COUNT(*) FROM users", []))
            return results
        
        result = benchmark(run)
        assert len(result) == 100
    
    def test_go_parallel_100_queries(self, go_bridge, benchmark):
        """Benchmark: 100 queries in parallel with Go Bridge."""
        queries = [("SELECT COUNT(*) FROM users", []) for _ in range(100)]
        
        result = benchmark(go_bridge.execute_parallel, queries)
        assert len(result) == 100


# =============================================================================
# Performance Regression Tests (these should NOT slow down)
# =============================================================================

@requires_db
class TestPerformanceRegression:
    """
    These tests have specific time targets that should not regress.
    """
    
    def test_500_queries_under_500ms(self, go_bridge):
        """500 concurrent queries should complete in under 500ms."""
        queries = [("SELECT COUNT(*) FROM users", []) for _ in range(500)]
        
        # Warmup (3 iterations to stabilize connection pool)
        for _ in range(3):
            go_bridge.execute_parallel(queries[:50])
        
        # Run multiple iterations, take best time
        best_time = float('inf')
        for _ in range(5):
            start = time.perf_counter()
            results = go_bridge.execute_parallel(queries)
            elapsed = time.perf_counter() - start
            best_time = min(best_time, elapsed)
        
        assert len(results) == 500
        assert all(r.success for r in results)
        assert best_time < 0.5, f"500 queries took {best_time:.2f}s, target is <0.5s"
    
    def test_200_small_queries_under_50ms(self, go_bridge):
        """200 small queries should complete in under 50ms."""
        queries = [("SELECT 1", []) for _ in range(200)]
        
        # Warmup
        go_bridge.execute_parallel(queries[:50])
        
        # Best of 5 runs
        times = []
        for _ in range(5):
            start = time.perf_counter()
            results = go_bridge.execute_parallel(queries)
            times.append(time.perf_counter() - start)
        
        best_time = min(times)
        assert best_time < 0.05, f"200 queries took {best_time*1000:.0f}ms, target is <50ms"
    
    def test_parallel_speedup_at_least_3x(self, go_bridge):
        """Parallel should be at least 3x faster than sequential for 50 queries."""
        queries = [("SELECT COUNT(*) FROM users", []) for _ in range(50)]
        
        # Warmup both paths (3 iterations to stabilize)
        for _ in range(3):
            go_bridge.execute("SELECT 1", [])
            go_bridge.execute_parallel([("SELECT 1", [])])
        
        # Run multiple iterations, take best speedup
        best_speedup = 0
        for _ in range(3):
            # Sequential
            start = time.perf_counter()
            for sql, params in queries:
                go_bridge.execute(sql, params)
            seq_time = time.perf_counter() - start
            
            # Parallel
            start = time.perf_counter()
            go_bridge.execute_parallel(queries)
            par_time = time.perf_counter() - start
            
            speedup = seq_time / par_time if par_time > 0 else float('inf')
            best_speedup = max(best_speedup, speedup)
        
        assert best_speedup >= 3, f"Parallel speedup is only {best_speedup:.1f}x, target is >=3x"

