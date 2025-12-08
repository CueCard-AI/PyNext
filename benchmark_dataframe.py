#!/usr/bin/env python3
"""
Comprehensive Benchmark: pynext-go vs asyncpg

This script benchmarks:
1. DataFrame operations (Arrow-based)
2. Small query performance (execute_fast)
3. Multi-query parallel execution (batch/execute_parallel)
4. API endpoint scenarios

Run with: python benchmark_dataframe.py
"""

import asyncio
import time
import statistics
import gc
import sys
from typing import List, Dict, Any
from dataclasses import dataclass

# Check dependencies
try:
    import asyncpg
    import pandas as pd
    import polars as pl
    import numpy as np
    import pyarrow as pa
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install asyncpg pandas polars numpy pyarrow")
    sys.exit(1)

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "user": "pynext",
    "password": "pynext",
    "database": "pynext_test",
}

DSN = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""
    name: str
    method: str
    rows: int
    times: List[float]
    
    @property
    def mean_ms(self) -> float:
        return statistics.mean(self.times) * 1000
    
    @property
    def std_ms(self) -> float:
        return statistics.stdev(self.times) * 1000 if len(self.times) > 1 else 0
    
    @property
    def min_ms(self) -> float:
        return min(self.times) * 1000
    
    @property
    def max_ms(self) -> float:
        return max(self.times) * 1000


class BenchmarkRunner:
    """Run DataFrame benchmarks."""
    
    def __init__(self, iterations: int = 5, warmup: int = 2):
        self.iterations = iterations
        self.warmup = warmup
        self.results: List[BenchmarkResult] = []
        self.asyncpg_pool = None
        self.pynext_bridge = None
    
    async def setup(self):
        """Set up database connections."""
        print("Setting up connections...")
        
        # asyncpg pool
        self.asyncpg_pool = await asyncpg.create_pool(
            **DB_CONFIG,
            min_size=5,
            max_size=20,
        )
        
        # pynext-go bridge
        try:
            import pynext_go
            pynext_go.init(DSN)
            self.pynext_bridge = pynext_go
            print("✓ pynext-go initialized")
        except Exception as e:
            print(f"✗ pynext-go failed to initialize: {e}")
            self.pynext_bridge = None
        
        print("✓ asyncpg pool created")
    
    async def teardown(self):
        """Clean up connections."""
        if self.asyncpg_pool:
            await self.asyncpg_pool.close()
        if self.pynext_bridge:
            self.pynext_bridge.close()
    
    async def seed_data(self, table_name: str, num_rows: int):
        """Seed test data into database."""
        print(f"Seeding {num_rows:,} rows into {table_name}...")
        
        async with self.asyncpg_pool.acquire() as conn:
            # Drop and recreate table
            await conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            await conn.execute(f"""
                CREATE TABLE {table_name} (
                    id SERIAL PRIMARY KEY,
                    int_col INTEGER,
                    bigint_col BIGINT,
                    float_col DOUBLE PRECISION,
                    text_col TEXT,
                    bool_col BOOLEAN,
                    timestamp_col TIMESTAMP
                )
            """)
            
            # Insert data in batches
            import datetime
            batch_size = 10000
            base_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
            
            for start in range(0, num_rows, batch_size):
                end = min(start + batch_size, num_rows)
                
                # Generate batch data
                records = []
                for i in range(start, end):
                    records.append((
                        i,  # int_col
                        i * 1000,  # bigint_col
                        float(i) * 1.5,  # float_col
                        f"text_{i % 1000}",  # text_col
                        i % 2 == 0,  # bool_col
                        base_time + datetime.timedelta(seconds=i),  # timestamp_col
                    ))
                
                await conn.executemany(f"""
                    INSERT INTO {table_name} (int_col, bigint_col, float_col, text_col, bool_col, timestamp_col)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, records)
        
        print(f"✓ Seeded {num_rows:,} rows")
    
    async def benchmark_asyncpg_to_pandas(self, query: str, num_rows: int) -> BenchmarkResult:
        """Benchmark asyncpg + manual pandas conversion."""
        times = []
        
        # Warmup
        for _ in range(self.warmup):
            async with self.asyncpg_pool.acquire() as conn:
                rows = await conn.fetch(query)
                df = pd.DataFrame([dict(r) for r in rows])
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            
            async with self.asyncpg_pool.acquire() as conn:
                rows = await conn.fetch(query)
                df = pd.DataFrame([dict(r) for r in rows])
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult("to_pandas", "asyncpg", num_rows, times)
    
    async def benchmark_asyncpg_to_polars(self, query: str, num_rows: int) -> BenchmarkResult:
        """Benchmark asyncpg + manual polars conversion."""
        times = []
        
        # Warmup
        for _ in range(self.warmup):
            async with self.asyncpg_pool.acquire() as conn:
                rows = await conn.fetch(query)
                df = pl.DataFrame([dict(r) for r in rows])
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            
            async with self.asyncpg_pool.acquire() as conn:
                rows = await conn.fetch(query)
                df = pl.DataFrame([dict(r) for r in rows])
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult("to_polars", "asyncpg", num_rows, times)
    
    async def benchmark_asyncpg_to_numpy(self, query: str, num_rows: int) -> BenchmarkResult:
        """Benchmark asyncpg + manual numpy conversion."""
        times = []
        
        # Warmup
        for _ in range(self.warmup):
            async with self.asyncpg_pool.acquire() as conn:
                rows = await conn.fetch(query)
                columns = {}
                if rows:
                    keys = rows[0].keys()
                    for key in keys:
                        columns[key] = np.array([r[key] for r in rows])
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            
            async with self.asyncpg_pool.acquire() as conn:
                rows = await conn.fetch(query)
                columns = {}
                if rows:
                    keys = rows[0].keys()
                    for key in keys:
                        columns[key] = np.array([r[key] for r in rows])
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult("to_numpy", "asyncpg", num_rows, times)
    
    async def benchmark_pynext_arrow(self, query: str, num_rows: int) -> BenchmarkResult:
        """Benchmark pynext-go execute_arrow."""
        if not self.pynext_bridge:
            return BenchmarkResult("execute_arrow", "pynext-go", num_rows, [float('inf')])
        
        times = []
        
        # Warmup
        for _ in range(self.warmup):
            table = await self.pynext_bridge.execute_arrow_async(query)
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            table = await self.pynext_bridge.execute_arrow_async(query)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult("execute_arrow", "pynext-go", num_rows, times)
    
    async def benchmark_pynext_polars(self, query: str, num_rows: int) -> BenchmarkResult:
        """Benchmark pynext-go execute_polars."""
        if not self.pynext_bridge:
            return BenchmarkResult("execute_polars", "pynext-go", num_rows, [float('inf')])
        
        times = []
        
        # Warmup
        for _ in range(self.warmup):
            df = await self.pynext_bridge.execute_polars_async(query)
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            df = await self.pynext_bridge.execute_polars_async(query)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult("execute_polars", "pynext-go", num_rows, times)
    
    async def benchmark_pynext_pandas(self, query: str, num_rows: int) -> BenchmarkResult:
        """Benchmark pynext-go execute_pandas (via Arrow)."""
        if not self.pynext_bridge:
            return BenchmarkResult("execute_pandas", "pynext-go", num_rows, [float('inf')])
        
        times = []
        
        # Warmup
        for _ in range(self.warmup):
            df = await self.pynext_bridge.execute_pandas_async(query)
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            df = await self.pynext_bridge.execute_pandas_async(query)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult("execute_pandas", "pynext-go", num_rows, times)
    
    async def benchmark_pynext_numpy(self, query: str, num_rows: int) -> BenchmarkResult:
        """Benchmark pynext-go execute_numpy."""
        if not self.pynext_bridge:
            return BenchmarkResult("execute_numpy", "pynext-go", num_rows, [float('inf')])
        
        times = []
        
        # Warmup
        for _ in range(self.warmup):
            arrays = await self.pynext_bridge.execute_numpy_async(query)
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            arrays = await self.pynext_bridge.execute_numpy_async(query)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult("execute_numpy", "pynext-go", num_rows, times)
    
    async def benchmark_pynext_copy_df(self, query: str, num_rows: int) -> BenchmarkResult:
        """Benchmark pynext-go execute_copy_df (COPY protocol)."""
        if not self.pynext_bridge:
            return BenchmarkResult("execute_copy_df", "pynext-go", num_rows, [float('inf')])
        
        times = []
        
        # Warmup (sync function, run in executor)
        loop = asyncio.get_event_loop()
        for _ in range(self.warmup):
            df = await loop.run_in_executor(None, self.pynext_bridge.execute_copy_df, query)
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            df = await loop.run_in_executor(None, self.pynext_bridge.execute_copy_df, query)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult("execute_copy_df", "pynext-go", num_rows, times)
    
    # =========================================================================
    # Small Query Benchmarks (execute_fast)
    # =========================================================================
    
    async def benchmark_asyncpg_small_query(self, table_name: str, iterations: int = 100) -> BenchmarkResult:
        """Benchmark asyncpg for small single-row queries."""
        times = []
        
        # Warmup
        for _ in range(10):
            async with self.asyncpg_pool.acquire() as conn:
                await conn.fetchrow(f"SELECT * FROM {table_name} WHERE id = $1", 1)
        
        # Benchmark: measure total time for N queries
        gc.collect()
        start = time.perf_counter()
        
        for i in range(iterations):
            async with self.asyncpg_pool.acquire() as conn:
                await conn.fetchrow(f"SELECT * FROM {table_name} WHERE id = $1", (i % 100) + 1)
        
        total_elapsed = time.perf_counter() - start
        avg_per_query = total_elapsed / iterations
        
        return BenchmarkResult("small_query", "asyncpg", iterations, [avg_per_query] * 5)
    
    async def benchmark_pynext_execute(self, table_name: str, iterations: int = 100) -> BenchmarkResult:
        """Benchmark pynext-go execute() for small queries."""
        if not self.pynext_bridge:
            return BenchmarkResult("execute", "pynext-go", iterations, [float('inf')])
        
        # Warmup
        for _ in range(10):
            self.pynext_bridge.execute(f"SELECT * FROM {table_name} WHERE id = $1", [1])
        
        # Benchmark
        gc.collect()
        start = time.perf_counter()
        
        for i in range(iterations):
            self.pynext_bridge.execute(f"SELECT * FROM {table_name} WHERE id = $1", [(i % 100) + 1])
        
        total_elapsed = time.perf_counter() - start
        avg_per_query = total_elapsed / iterations
        
        return BenchmarkResult("execute", "pynext-go", iterations, [avg_per_query] * 5)
    
    async def benchmark_pynext_execute_fast(self, table_name: str, iterations: int = 100) -> BenchmarkResult:
        """Benchmark pynext-go execute_fast() for small queries."""
        if not self.pynext_bridge:
            return BenchmarkResult("execute_fast", "pynext-go", iterations, [float('inf')])
        
        # Warmup
        for _ in range(10):
            self.pynext_bridge.execute_fast(f"SELECT * FROM {table_name} WHERE id = $1", [1])
        
        # Benchmark
        gc.collect()
        start = time.perf_counter()
        
        for i in range(iterations):
            self.pynext_bridge.execute_fast(f"SELECT * FROM {table_name} WHERE id = $1", [(i % 100) + 1])
        
        total_elapsed = time.perf_counter() - start
        avg_per_query = total_elapsed / iterations
        
        return BenchmarkResult("execute_fast", "pynext-go", iterations, [avg_per_query] * 5)
    
    # =========================================================================
    # Multi-Query Parallel Benchmarks
    # =========================================================================
    
    async def benchmark_asyncpg_multi_query(self, table_name: str, num_queries: int = 5) -> BenchmarkResult:
        """Benchmark asyncpg for multiple sequential queries (simulates API endpoint)."""
        times = []
        
        queries = [
            f"SELECT * FROM {table_name} WHERE id = $1",
            f"SELECT COUNT(*) FROM {table_name}",
            f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 10",
            f"SELECT AVG(int_col) FROM {table_name}",
            f"SELECT * FROM {table_name} WHERE int_col > $1 LIMIT 5",
        ][:num_queries]
        
        # Warmup
        for _ in range(self.warmup):
            async with self.asyncpg_pool.acquire() as conn:
                for i, q in enumerate(queries):
                    if "$1" in q:
                        await conn.fetch(q, 50)
                    else:
                        await conn.fetch(q)
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            
            async with self.asyncpg_pool.acquire() as conn:
                results = []
                for i, q in enumerate(queries):
                    if "$1" in q:
                        results.append(await conn.fetch(q, 50))
                    else:
                        results.append(await conn.fetch(q))
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult(f"multi_query_{num_queries}", "asyncpg", num_queries, times)
    
    async def benchmark_asyncpg_multi_query_gather(self, table_name: str, num_queries: int = 5) -> BenchmarkResult:
        """Benchmark asyncpg with asyncio.gather (best async approach)."""
        times = []
        
        queries = [
            (f"SELECT * FROM {table_name} WHERE id = $1", [50]),
            (f"SELECT COUNT(*) FROM {table_name}", []),
            (f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 10", []),
            (f"SELECT AVG(int_col) FROM {table_name}", []),
            (f"SELECT * FROM {table_name} WHERE int_col > $1 LIMIT 5", [50]),
        ][:num_queries]
        
        async def run_query(q, params):
            async with self.asyncpg_pool.acquire() as conn:
                if params:
                    return await conn.fetch(q, *params)
                return await conn.fetch(q)
        
        # Warmup
        for _ in range(self.warmup):
            await asyncio.gather(*[run_query(q, p) for q, p in queries])
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            
            results = await asyncio.gather(*[run_query(q, p) for q, p in queries])
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult(f"multi_query_gather_{num_queries}", "asyncpg", num_queries, times)
    
    async def benchmark_pynext_execute_parallel(self, table_name: str, num_queries: int = 5) -> BenchmarkResult:
        """Benchmark pynext-go execute_parallel() for multi-query."""
        if not self.pynext_bridge:
            return BenchmarkResult(f"execute_parallel_{num_queries}", "pynext-go", num_queries, [float('inf')])
        
        times = []
        
        queries = [
            (f"SELECT * FROM {table_name} WHERE id = $1", [50]),
            (f"SELECT COUNT(*) FROM {table_name}", []),
            (f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 10", []),
            (f"SELECT AVG(int_col) FROM {table_name}", []),
            (f"SELECT * FROM {table_name} WHERE int_col > $1 LIMIT 5", [50]),
        ][:num_queries]
        
        # Warmup
        for _ in range(self.warmup):
            self.pynext_bridge.execute_parallel(queries)
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            
            results = self.pynext_bridge.execute_parallel(queries)
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult(f"execute_parallel_{num_queries}", "pynext-go", num_queries, times)
    
    async def benchmark_pynext_batch(self, table_name: str, num_queries: int = 5) -> BenchmarkResult:
        """Benchmark pynext-go batch() context manager."""
        if not self.pynext_bridge:
            return BenchmarkResult(f"batch_{num_queries}", "pynext-go", num_queries, [float('inf')])
        
        times = []
        
        # Warmup
        for _ in range(self.warmup):
            with self.pynext_bridge.batch() as b:
                b.query(f"SELECT * FROM {table_name} WHERE id = $1", [50])
                b.query(f"SELECT COUNT(*) FROM {table_name}")
                if num_queries >= 3:
                    b.query(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 10")
                if num_queries >= 4:
                    b.query(f"SELECT AVG(int_col) FROM {table_name}")
                if num_queries >= 5:
                    b.query(f"SELECT * FROM {table_name} WHERE int_col > $1 LIMIT 5", [50])
            gc.collect()
        
        # Benchmark
        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()
            
            with self.pynext_bridge.batch() as b:
                r1 = b.query(f"SELECT * FROM {table_name} WHERE id = $1", [50])
                r2 = b.query(f"SELECT COUNT(*) FROM {table_name}")
                if num_queries >= 3:
                    r3 = b.query(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 10")
                if num_queries >= 4:
                    r4 = b.query(f"SELECT AVG(int_col) FROM {table_name}")
                if num_queries >= 5:
                    r5 = b.query(f"SELECT * FROM {table_name} WHERE int_col > $1 LIMIT 5", [50])
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return BenchmarkResult(f"batch_{num_queries}", "pynext-go", num_queries, times)
    
    # =========================================================================
    # Run Multi-Query Suite
    # =========================================================================
    
    async def run_small_query_benchmark(self, table_name: str):
        """Run small query benchmarks."""
        results = []
        
        print("\n" + "=" * 80)
        print("  Small Query Benchmarks (single row lookups)")
        print("=" * 80)
        
        print("  Running asyncpg small queries (100 iterations)...")
        results.append(await self.benchmark_asyncpg_small_query(table_name, 100))
        
        if self.pynext_bridge:
            print("  Running pynext-go execute()...")
            results.append(await self.benchmark_pynext_execute(table_name, 100))
            
            print("  Running pynext-go execute_fast()...")
            results.append(await self.benchmark_pynext_execute_fast(table_name, 100))
        
        # Print results
        print(f"\n{'Operation':<20} {'Time/query (ms)':<20} {'Speedup vs asyncpg':<20}")
        print("-" * 60)
        
        asyncpg_time = results[0].mean_ms
        print(f"{'asyncpg':<20} {asyncpg_time:>15.3f}")
        
        if len(results) > 1:
            execute_time = results[1].mean_ms
            speedup = asyncpg_time / execute_time
            print(f"{'pynext execute':<20} {execute_time:>15.3f}      {speedup:>10.2f}x")
        
        if len(results) > 2:
            fast_time = results[2].mean_ms
            speedup = asyncpg_time / fast_time
            print(f"{'pynext execute_fast':<20} {fast_time:>15.3f}      {speedup:>10.2f}x")
        
        return results
    
    async def run_multi_query_benchmark(self, table_name: str):
        """Run multi-query parallel benchmarks."""
        results = []
        
        print("\n" + "=" * 80)
        print("  Multi-Query Parallel Benchmarks (API endpoint simulation)")
        print("=" * 80)
        
        for num_queries in [3, 5, 10]:
            print(f"\n  --- {num_queries} queries ---")
            
            print(f"  Running asyncpg sequential...")
            r_seq = await self.benchmark_asyncpg_multi_query(table_name, num_queries)
            results.append(r_seq)
            
            print(f"  Running asyncpg gather...")
            r_gather = await self.benchmark_asyncpg_multi_query_gather(table_name, num_queries)
            results.append(r_gather)
            
            if self.pynext_bridge:
                print(f"  Running pynext-go execute_parallel...")
                r_parallel = await self.benchmark_pynext_execute_parallel(table_name, num_queries)
                results.append(r_parallel)
                
                print(f"  Running pynext-go batch()...")
                r_batch = await self.benchmark_pynext_batch(table_name, num_queries)
                results.append(r_batch)
            
            # Print results for this query count
            print(f"\n  {'Method':<25} {'Time (ms)':<15} {'vs sequential':<15}")
            print("  " + "-" * 55)
            
            seq_time = r_seq.mean_ms
            print(f"  {'asyncpg sequential':<25} {seq_time:>12.2f}")
            
            gather_time = r_gather.mean_ms
            speedup = seq_time / gather_time
            print(f"  {'asyncpg gather':<25} {gather_time:>12.2f}   {speedup:>10.2f}x")
            
            if self.pynext_bridge:
                parallel_time = r_parallel.mean_ms
                speedup = seq_time / parallel_time
                print(f"  {'pynext execute_parallel':<25} {parallel_time:>12.2f}   {speedup:>10.2f}x")
                
                batch_time = r_batch.mean_ms
                speedup = seq_time / batch_time
                print(f"  {'pynext batch()':<25} {batch_time:>12.2f}   {speedup:>10.2f}x")
        
        return results
    
    def print_results(self, results: List[BenchmarkResult], title: str):
        """Print benchmark results in a nice table."""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}")
        
        # Group by operation
        asyncpg_results = {r.name: r for r in results if r.method == "asyncpg"}
        pynext_results = {r.name: r for r in results if r.method == "pynext-go"}
        
        print(f"\n{'Operation':<20} {'asyncpg (ms)':<15} {'pynext-go (ms)':<15} {'Speedup':<10}")
        print("-" * 60)
        
        for name in asyncpg_results.keys():
            asyncpg_r = asyncpg_results.get(name)
            pynext_r = pynext_results.get(name.replace("to_", "execute_"))
            
            if asyncpg_r and pynext_r:
                asyncpg_time = asyncpg_r.mean_ms
                pynext_time = pynext_r.mean_ms
                speedup = asyncpg_time / pynext_time if pynext_time > 0 else float('inf')
                
                print(f"{name:<20} {asyncpg_time:>12.2f}   {pynext_time:>12.2f}   {speedup:>6.2f}x")
        
        # Print copy_df if available
        copy_df = pynext_results.get("execute_copy_df")
        if copy_df:
            asyncpg_pandas = asyncpg_results.get("to_pandas")
            if asyncpg_pandas:
                speedup = asyncpg_pandas.mean_ms / copy_df.mean_ms
                print(f"{'copy_df':<20} {'N/A':>12}   {copy_df.mean_ms:>12.2f}   {speedup:>6.2f}x vs pandas")
    
    async def run_benchmark_suite(self, num_rows: int):
        """Run complete benchmark suite for a given row count."""
        table_name = f"benchmark_{num_rows}"
        await self.seed_data(table_name, num_rows)
        
        query = f"SELECT * FROM {table_name}"
        results = []
        
        print(f"\nRunning benchmarks for {num_rows:,} rows...")
        
        # asyncpg benchmarks
        print("  Running asyncpg → pandas...")
        results.append(await self.benchmark_asyncpg_to_pandas(query, num_rows))
        
        print("  Running asyncpg → polars...")
        results.append(await self.benchmark_asyncpg_to_polars(query, num_rows))
        
        print("  Running asyncpg → numpy...")
        results.append(await self.benchmark_asyncpg_to_numpy(query, num_rows))
        
        # pynext-go benchmarks
        if self.pynext_bridge:
            print("  Running pynext-go execute_arrow...")
            results.append(await self.benchmark_pynext_arrow(query, num_rows))
            
            print("  Running pynext-go execute_polars...")
            results.append(await self.benchmark_pynext_polars(query, num_rows))
            
            print("  Running pynext-go execute_pandas...")
            results.append(await self.benchmark_pynext_pandas(query, num_rows))
            
            print("  Running pynext-go execute_numpy...")
            results.append(await self.benchmark_pynext_numpy(query, num_rows))
            
            print("  Running pynext-go execute_copy_df...")
            results.append(await self.benchmark_pynext_copy_df(query, num_rows))
        
        self.print_results(results, f"Results for {num_rows:,} rows")
        self.results.extend(results)
        
        return results


async def main():
    print("=" * 80)
    print("  COMPREHENSIVE BENCHMARK: pynext-go vs asyncpg")
    print("=" * 80)
    
    runner = BenchmarkRunner(iterations=5, warmup=2)
    
    try:
        await runner.setup()
        
        # Seed a table for small query and multi-query benchmarks
        await runner.seed_data("benchmark_10000", 10000)
        
        # =================================================================
        # PART 1: Small Query Performance (execute_fast)
        # =================================================================
        await runner.run_small_query_benchmark("benchmark_10000")
        
        # =================================================================
        # PART 2: Multi-Query Parallel Performance (batch, execute_parallel)
        # =================================================================
        await runner.run_multi_query_benchmark("benchmark_10000")
        
        # =================================================================
        # PART 3: DataFrame Performance (Arrow-based methods)
        # =================================================================
        print("\n" + "=" * 80)
        print("  DataFrame Benchmarks (large data)")
        print("=" * 80)
        
        # Run benchmarks for different data sizes
        sizes = [100_000, 500_000, 1_000_000]
        
        for size in sizes:
            await runner.run_benchmark_suite(size)
        
        # =================================================================
        # FINAL SUMMARY
        # =================================================================
        print("\n" + "=" * 80)
        print("  FINAL SUMMARY")
        print("=" * 80)
        
        print("\n  DataFrame operations (100K-1M rows):")
        df_asyncpg = sum(r.mean_ms for r in runner.results if r.method == "asyncpg" and "to_" in r.name)
        df_pynext = sum(r.mean_ms for r in runner.results if r.method == "pynext-go" and "execute_p" in r.name)
        if df_pynext > 0:
            print(f"    pynext-go is {df_asyncpg / df_pynext:.2f}x faster for DataFrames")
        
        print("\n  Recommendations:")
        print("    - Small queries: Use execute_fast() for best latency")
        print("    - Multi-query API endpoints: Use batch() or execute_parallel()")
        print("    - DataFrames: Use execute_polars() or execute_pandas()")
        
    finally:
        await runner.teardown()


if __name__ == "__main__":
    asyncio.run(main())

