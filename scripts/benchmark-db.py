#!/usr/bin/env python3
"""
Database Performance Benchmark: Go Bridge vs asyncpg

Compares pynext_go (Go bridge) against asyncpg for various workloads.

Usage:
    python scripts/benchmark-db.py                    # Run all benchmarks
    python scripts/benchmark-db.py --queries 1000    # Custom query count
    python scripts/benchmark-db.py --parallel-only   # Only parallel tests
    python scripts/benchmark-db.py --seed            # Seed data first
"""

import argparse
import asyncio
import time
import statistics
from dataclasses import dataclass
from typing import Callable

# Database URL
DB_URL = "postgresql://pynext:pynext@localhost:5433/pynext_test"


@dataclass
class BenchmarkResult:
    name: str
    total_time: float
    queries_per_sec: float
    avg_latency_ms: float
    p50_latency_ms: float
    p99_latency_ms: float
    rows_returned: int


def print_result(result: BenchmarkResult, comparison: BenchmarkResult = None):
    """Print benchmark result with optional comparison."""
    print(f"\n  {result.name}")
    print(f"    Total time:     {result.total_time:.2f}s")
    print(f"    Queries/sec:    {result.queries_per_sec:,.0f}")
    print(f"    Avg latency:    {result.avg_latency_ms:.2f}ms")
    print(f"    P50 latency:    {result.p50_latency_ms:.2f}ms")
    print(f"    P99 latency:    {result.p99_latency_ms:.2f}ms")
    print(f"    Rows returned:  {result.rows_returned:,}")
    
    if comparison:
        speedup = comparison.total_time / result.total_time
        if speedup > 1:
            print(f"    🚀 {speedup:.1f}x FASTER than {comparison.name}")
        else:
            print(f"    ⚠️  {1/speedup:.1f}x slower than {comparison.name}")


def run_benchmark(name: str, func: Callable, iterations: int) -> BenchmarkResult:
    """Run a benchmark and collect statistics."""
    latencies = []
    total_rows = 0
    
    start = time.perf_counter()
    for _ in range(iterations):
        iter_start = time.perf_counter()
        rows = func()
        latencies.append((time.perf_counter() - iter_start) * 1000)
        total_rows += rows
    total_time = time.perf_counter() - start
    
    latencies.sort()
    p50_idx = int(len(latencies) * 0.50)
    p99_idx = int(len(latencies) * 0.99)
    
    return BenchmarkResult(
        name=name,
        total_time=total_time,
        queries_per_sec=iterations / total_time,
        avg_latency_ms=statistics.mean(latencies),
        p50_latency_ms=latencies[p50_idx],
        p99_latency_ms=latencies[p99_idx],
        rows_returned=total_rows,
    )


async def run_async_benchmark(name: str, func: Callable, iterations: int) -> BenchmarkResult:
    """Run an async benchmark."""
    latencies = []
    total_rows = 0
    
    start = time.perf_counter()
    for _ in range(iterations):
        iter_start = time.perf_counter()
        rows = await func()
        latencies.append((time.perf_counter() - iter_start) * 1000)
        total_rows += rows
    total_time = time.perf_counter() - start
    
    latencies.sort()
    p50_idx = int(len(latencies) * 0.50)
    p99_idx = int(len(latencies) * 0.99)
    
    return BenchmarkResult(
        name=name,
        total_time=total_time,
        queries_per_sec=iterations / total_time,
        avg_latency_ms=statistics.mean(latencies),
        p50_latency_ms=latencies[p50_idx],
        p99_latency_ms=latencies[p99_idx],
        rows_returned=total_rows,
    )


# =============================================================================
# Go Bridge Benchmarks
# =============================================================================

def bench_go_simple_select(iterations: int) -> BenchmarkResult:
    """Benchmark simple SELECT with Go bridge."""
    import pynext_go
    
    pynext_go.init(primary=DB_URL)
    pynext_go.warmup()
    
    def query():
        result = pynext_go.execute("SELECT id, name, email FROM users LIMIT 100", [])
        return len(result)
    
    result = run_benchmark("Go Bridge - Simple SELECT", query, iterations)
    pynext_go.close()
    return result


def bench_go_complex_join(iterations: int) -> BenchmarkResult:
    """Benchmark complex JOIN with Go bridge."""
    import pynext_go
    
    pynext_go.init(primary=DB_URL)
    pynext_go.warmup()
    
    sql = """
        SELECT u.id, u.name, COUNT(o.id) as order_count, SUM(o.total) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id, u.name
        ORDER BY total_spent DESC NULLS LAST
        LIMIT 100
    """
    
    def query():
        result = pynext_go.execute(sql, [])
        return len(result)
    
    result = run_benchmark("Go Bridge - Complex JOIN", query, iterations)
    pynext_go.close()
    return result


def bench_go_parallel(parallel_count: int, iterations: int) -> BenchmarkResult:
    """Benchmark parallel queries with Go bridge."""
    import pynext_go
    
    pynext_go.init(primary=DB_URL)
    pynext_go.warmup()
    
    queries = [
        ("SELECT COUNT(*) FROM users", []),
        ("SELECT COUNT(*) FROM orders", []),
        ("SELECT COUNT(*) FROM products", []),
        ("SELECT AVG(total) FROM orders", []),
        ("SELECT status, COUNT(*) FROM orders GROUP BY status", []),
    ][:parallel_count]
    
    def query():
        results = pynext_go.execute_parallel(queries)
        return sum(len(r) for r in results)
    
    result = run_benchmark(f"Go Bridge - {parallel_count} Parallel Queries", query, iterations)
    pynext_go.close()
    return result


def bench_go_bulk_read(iterations: int) -> BenchmarkResult:
    """Benchmark bulk data read with Go bridge."""
    import pynext_go
    
    pynext_go.init(primary=DB_URL)
    pynext_go.warmup()
    
    def query():
        result = pynext_go.execute("SELECT * FROM orders LIMIT 5000", [])
        return len(result)
    
    result = run_benchmark("Go Bridge - Bulk Read (5000 rows)", query, iterations)
    pynext_go.close()
    return result


# =============================================================================
# asyncpg Benchmarks
# =============================================================================

async def bench_asyncpg_simple_select(iterations: int) -> BenchmarkResult:
    """Benchmark simple SELECT with asyncpg."""
    import asyncpg
    
    pool = await asyncpg.create_pool(DB_URL, min_size=5, max_size=20)
    
    async def query():
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, name, email FROM users LIMIT 100")
            return len(rows)
    
    result = await run_async_benchmark("asyncpg - Simple SELECT", query, iterations)
    await pool.close()
    return result


async def bench_asyncpg_complex_join(iterations: int) -> BenchmarkResult:
    """Benchmark complex JOIN with asyncpg."""
    import asyncpg
    
    pool = await asyncpg.create_pool(DB_URL, min_size=5, max_size=20)
    
    sql = """
        SELECT u.id, u.name, COUNT(o.id) as order_count, SUM(o.total) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id, u.name
        ORDER BY total_spent DESC NULLS LAST
        LIMIT 100
    """
    
    async def query():
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql)
            return len(rows)
    
    result = await run_async_benchmark("asyncpg - Complex JOIN", query, iterations)
    await pool.close()
    return result


async def bench_asyncpg_parallel(parallel_count: int, iterations: int) -> BenchmarkResult:
    """Benchmark parallel queries with asyncpg using gather."""
    import asyncpg
    
    pool = await asyncpg.create_pool(DB_URL, min_size=10, max_size=50)
    
    queries = [
        "SELECT COUNT(*) FROM users",
        "SELECT COUNT(*) FROM orders",
        "SELECT COUNT(*) FROM products",
        "SELECT AVG(total) FROM orders",
        "SELECT status, COUNT(*) FROM orders GROUP BY status",
    ][:parallel_count]
    
    async def run_query(sql):
        async with pool.acquire() as conn:
            return await conn.fetch(sql)
    
    async def query():
        results = await asyncio.gather(*[run_query(sql) for sql in queries])
        return sum(len(r) for r in results)
    
    result = await run_async_benchmark(f"asyncpg - {parallel_count} Parallel Queries", query, iterations)
    await pool.close()
    return result


async def bench_asyncpg_bulk_read(iterations: int) -> BenchmarkResult:
    """Benchmark bulk data read with asyncpg."""
    import asyncpg
    
    pool = await asyncpg.create_pool(DB_URL, min_size=5, max_size=20)
    
    async def query():
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM orders LIMIT 5000")
            return len(rows)
    
    result = await run_async_benchmark("asyncpg - Bulk Read (5000 rows)", query, iterations)
    await pool.close()
    return result


# =============================================================================
# Main
# =============================================================================

async def run_all_benchmarks(iterations: int, parallel_count: int):
    """Run all benchmarks and compare."""
    
    print("\n" + "=" * 70)
    print("DATABASE BENCHMARK: Go Bridge vs asyncpg")
    print("=" * 70)
    print(f"\nIterations per test: {iterations}")
    print(f"Parallel query count: {parallel_count}")
    
    # Check data exists
    import pynext_go
    pynext_go.init(primary=DB_URL)
    result = pynext_go.execute("SELECT COUNT(*) FROM users", [])
    user_count = result.scalar()
    result = pynext_go.execute("SELECT COUNT(*) FROM orders", [])
    order_count = result.scalar()
    pynext_go.close()
    
    print(f"\nData: {user_count:,} users, {order_count:,} orders")
    
    if user_count < 1000:
        print("\n⚠️  Low data count. Run: python scripts/seed-test-data.py --users 10000 --orders 50000")
    
    # =========================================================================
    # Simple SELECT
    # =========================================================================
    print("\n" + "-" * 70)
    print("TEST 1: Simple SELECT (100 rows)")
    print("-" * 70)
    
    go_result = bench_go_simple_select(iterations)
    print_result(go_result)
    
    asyncpg_result = await bench_asyncpg_simple_select(iterations)
    print_result(asyncpg_result, go_result)
    
    # =========================================================================
    # Complex JOIN
    # =========================================================================
    print("\n" + "-" * 70)
    print("TEST 2: Complex JOIN with Aggregation")
    print("-" * 70)
    
    go_result = bench_go_complex_join(iterations)
    print_result(go_result)
    
    asyncpg_result = await bench_asyncpg_complex_join(iterations)
    print_result(asyncpg_result, go_result)
    
    # =========================================================================
    # Parallel Queries
    # =========================================================================
    print("\n" + "-" * 70)
    print(f"TEST 3: {parallel_count} Parallel Queries")
    print("-" * 70)
    
    go_result = bench_go_parallel(parallel_count, iterations)
    print_result(go_result)
    
    asyncpg_result = await bench_asyncpg_parallel(parallel_count, iterations)
    print_result(asyncpg_result, go_result)
    
    # =========================================================================
    # Bulk Read
    # =========================================================================
    print("\n" + "-" * 70)
    print("TEST 4: Bulk Read (5000 rows)")
    print("-" * 70)
    
    go_result = bench_go_bulk_read(iterations // 2)  # Fewer iterations for bulk
    print_result(go_result)
    
    asyncpg_result = await bench_asyncpg_bulk_read(iterations // 2)
    print_result(asyncpg_result, go_result)
    
    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)


def seed_data():
    """Seed test data."""
    import subprocess
    subprocess.run([
        "python", "scripts/seed-test-data.py",
        "--users", "50000",
        "--orders", "200000",
        "--products", "500",
        "--clean"
    ], check=True)


def main():
    parser = argparse.ArgumentParser(description="Database benchmark")
    parser.add_argument("--iterations", "-n", type=int, default=500, help="Iterations per test")
    parser.add_argument("--parallel", "-p", type=int, default=5, help="Parallel query count")
    parser.add_argument("--seed", action="store_true", help="Seed data first")
    args = parser.parse_args()
    
    if args.seed:
        print("Seeding test data...")
        seed_data()
    
    try:
        import asyncpg
    except ImportError:
        print("Installing asyncpg...")
        import subprocess
        subprocess.run(["pip", "install", "asyncpg"], check=True)
    
    asyncio.run(run_all_benchmarks(args.iterations, args.parallel))


if __name__ == "__main__":
    main()


