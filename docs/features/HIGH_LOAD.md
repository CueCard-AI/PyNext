# High-Load Scalability

## Table of Contents

1. [Introduction: What is "High Load"?](#introduction-what-is-high-load)
2. [Chapter 1: The Waiting Room Problem](#chapter-1-the-waiting-room-problem)
3. [Chapter 2: Network Round Trips - The Hidden Cost](#chapter-2-network-round-trips---the-hidden-cost)
4. [Chapter 3: Query Pipelining - Sending Mail in Batches](#chapter-3-query-pipelining---sending-mail-in-batches)
5. [Chapter 4: Caching - The Librarian's Memory](#chapter-4-caching---the-librarians-memory)
6. [Chapter 5: Query Coalescing - The Carpool](#chapter-5-query-coalescing---the-carpool)
7. [Chapter 6: Adaptive Scaling - The Elastic Restaurant](#chapter-6-adaptive-scaling---the-elastic-restaurant)
8. [Chapter 7: Timeouts - The Safety Net](#chapter-7-timeouts---the-safety-net)
9. [Chapter 8: Batch Optimization - The Factory Assembly Line](#chapter-8-batch-optimization---the-factory-assembly-line)
10. [Chapter 9: Putting It All Together](#chapter-9-putting-it-all-together)
11. [Chapter 10: Production Recipes](#chapter-10-production-recipes)
12. [API Reference](#api-reference)

---

## Introduction: What is "High Load"?

### The Simple Definition

Imagine you run a lemonade stand. On a normal day, maybe 10 kids come by per hour. You can easily serve each one, make their lemonade fresh, and chat with them.

Now imagine it's the hottest day of summer, and suddenly 1,000 kids show up in the same hour. That's **high load**.

```
Normal day:     👦 ... 👧 ... 👦 ... (10 per hour - easy!)
High load day:  👦👧👦👧👦👧👦👧👦👧👦👧... (1,000 per hour - chaos!)
```

### What Happens Under High Load?

When your web application experiences high load, several bad things happen:

1. **Requests pile up** - Like a queue at the DMV
2. **Response times increase** - Users wait longer and longer
3. **Resources get exhausted** - Your server runs out of memory, connections, CPU
4. **Failures cascade** - One slow query blocks others, making everything slow
5. **Users leave** - And they don't come back

### The Database Bottleneck

Here's a crucial insight: **the database is almost always the bottleneck**.

```
User Request → Your App → Database ← This is the slow part!
                 ↓
              Response
```

Why? Because databases:
- Store data on disk (slow compared to memory)
- Need to maintain consistency (locks, transactions)
- Have limited connections (typically 100-1000 max)
- Are shared by all your application instances

### What This Chapter Covers

PyNext provides six techniques to handle high database load:

| Technique | What It Does | Analogy |
|-----------|--------------|---------|
| **Pipelining** | Send multiple queries at once | Mailing multiple letters in one trip |
| **Caching** | Remember previous results | A librarian who memorizes popular books |
| **Coalescing** | Combine identical queries | Carpooling to work |
| **Adaptive Scaling** | Adjust resources automatically | A restaurant that adds tables when busy |
| **Timeouts** | Prevent slow queries from blocking | A timer that rings if something takes too long |
| **Batch Optimization** | Group similar operations | A factory assembly line |

Let's learn each one from scratch.

---

## Chapter 1: The Waiting Room Problem

### Understanding Connections

Before we dive into high-load techniques, we need to understand **connections**.

Think of a database connection like a phone call:

```
Your App                          Database
   |                                  |
   |  📞 "Hello, can I connect?"      |
   |--------------------------------->|
   |                                  |
   |  📞 "Sure, you're connected!"    |
   |<---------------------------------|
   |                                  |
   |  📝 "SELECT * FROM users"        |
   |--------------------------------->|
   |                                  |
   |  📋 "Here's the data..."         |
   |<---------------------------------|
   |                                  |
   |  👋 "Goodbye!"                   |
   |--------------------------------->|
```

**Key insight**: Opening a connection is expensive! It involves:
1. TCP handshake (3 network round trips)
2. TLS negotiation (more round trips for security)
3. PostgreSQL authentication
4. Memory allocation on both sides

This takes **50-200 milliseconds** - an eternity in computer time.

### The Naive Approach (Don't Do This!)

```python
# ❌ BAD: Opens a new connection for every query
async def get_user(user_id: int):
    # Connection opened here (50-200ms)
    conn = await asyncpg.connect("postgresql://...")
    
    # Query runs (5ms)
    user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    
    # Connection closed here
    await conn.close()
    
    return user

# If 1000 users request their profiles:
# 1000 connections × 100ms = 100 SECONDS of just connection time!
```

### The Connection Pool Solution

A **connection pool** is like a waiting room of pre-opened connections:

```
┌─────────────────────────────────────────┐
│           Connection Pool               │
│                                         │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐   │
│  │Conn│ │Conn│ │Conn│ │Conn│ │Conn│   │
│  │ 1  │ │ 2  │ │ 3  │ │ 4  │ │ 5  │   │
│  └────┘ └────┘ └────┘ └────┘ └────┘   │
│    ✓      ✓     busy    ✓     busy    │
└─────────────────────────────────────────┘
          ↑
    Your code borrows
    a connection, uses it,
    then returns it
```

```python
# ✅ GOOD: Reuses connections from a pool
pool = await asyncpg.create_pool("postgresql://...")

async def get_user(user_id: int):
    # Borrows existing connection (0ms)
    async with pool.acquire() as conn:
        # Query runs (5ms)
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    # Connection returned to pool (not closed)
    
    return user

# 1000 users: just 5ms each = 5 SECONDS total (20x faster!)
```

### But There's a Limit...

Pools have a maximum size. What happens when all connections are in use?

```
Request 1: "I need a connection" → Gets connection 1 ✓
Request 2: "I need a connection" → Gets connection 2 ✓
Request 3: "I need a connection" → Gets connection 3 ✓
Request 4: "I need a connection" → Gets connection 4 ✓
Request 5: "I need a connection" → Gets connection 5 ✓
Request 6: "I need a connection" → WAITS... ⏳
Request 7: "I need a connection" → WAITS... ⏳
Request 8: "I need a connection" → WAITS... ⏳
```

This is where high-load optimization comes in. We need to:
1. **Use each connection more efficiently** (pipelining, batching)
2. **Avoid using connections when possible** (caching, coalescing)
3. **Adjust pool size dynamically** (adaptive scaling)
4. **Prevent bad queries from hogging connections** (timeouts)

---

## Chapter 2: Network Round Trips - The Hidden Cost

### The Speed of Light is Slow

Here's something that surprises most developers: **network latency dominates database performance**.

Let's do the math:

```
Your Server (San Francisco) ←→ Database (New York)
Distance: ~2,500 miles
Speed of light: 186,000 miles/second
One-way time: 2,500 / 186,000 = 0.013 seconds = 13 milliseconds
Round trip: 26 milliseconds

But wait! Data doesn't travel at light speed through fiber:
Actual round trip: ~40 milliseconds
```

Now consider a typical query:

```
Action                          Time
────────────────────────────────────────
Send query to database          20ms  ↓
Database processes query         2ms  ⚙️
Send results back               20ms  ↑
────────────────────────────────────────
Total                           42ms

The actual work was only 2ms!
The network was 40ms (95% of the time)!
```

### The Multiplication Problem

If you make 10 queries sequentially:

```python
# ❌ BAD: 10 sequential queries
async def load_dashboard(user_id: int):
    user = await db.fetch("SELECT * FROM users WHERE id = $1", user_id)           # 42ms
    posts = await db.fetch("SELECT * FROM posts WHERE user_id = $1", user_id)     # 42ms
    comments = await db.fetch("SELECT * FROM comments WHERE user_id = $1", user_id) # 42ms
    likes = await db.fetch("SELECT * FROM likes WHERE user_id = $1", user_id)     # 42ms
    followers = await db.fetch("SELECT * FROM followers WHERE user_id = $1", user_id) # 42ms
    following = await db.fetch("SELECT * FROM following WHERE user_id = $1", user_id) # 42ms
    notifications = await db.fetch("SELECT * FROM notifications WHERE user_id = $1", user_id) # 42ms
    settings = await db.fetch("SELECT * FROM settings WHERE user_id = $1", user_id) # 42ms
    badges = await db.fetch("SELECT * FROM badges WHERE user_id = $1", user_id)   # 42ms
    stats = await db.fetch("SELECT * FROM stats WHERE user_id = $1", user_id)     # 42ms
    
    # Total: 420ms just for network!
    # (Actual database work: only 20ms)
```

### What We Need

We need ways to reduce network round trips:

| Strategy | How It Helps |
|----------|--------------|
| **Pipelining** | Send 10 queries in 1 round trip instead of 10 |
| **Caching** | Don't make the query at all - use cached result |
| **Coalescing** | 100 identical queries become 1 query |
| **Batching** | Combine 100 INSERTs into 1 bulk INSERT |

Let's learn each one.

---

## Chapter 3: Query Pipelining - Sending Mail in Batches

### The Post Office Analogy

Imagine you need to mail 10 letters:

**Without pipelining (10 trips to post office):**
```
Trip 1: Drive to post office, mail letter 1, drive back
Trip 2: Drive to post office, mail letter 2, drive back
Trip 3: Drive to post office, mail letter 3, drive back
...
Trip 10: Drive to post office, mail letter 10, drive back

Total: 10 trips × 30 minutes = 300 minutes
```

**With pipelining (1 trip with all letters):**
```
Trip 1: Drive to post office, mail ALL 10 letters, drive back

Total: 1 trip × 35 minutes = 35 minutes
```

That's **8.5x faster** with basically the same amount of actual work!

### How Database Pipelining Works

Without pipelining:
```
Your App                              Database
   |                                      |
   |  📝 Query 1 ----------------------->|
   |                              process |
   |<-------------------------- Results 1 |
   |                                      |
   |  📝 Query 2 ----------------------->|
   |                              process |
   |<-------------------------- Results 2 |
   |                                      |
   |  📝 Query 3 ----------------------->|
   |                              process |
   |<-------------------------- Results 3 |

Time: 3 round trips = 120ms
```

With pipelining:
```
Your App                              Database
   |                                      |
   |  📝 Query 1 ----------------------->|
   |  📝 Query 2 ----------------------->| (sent immediately!)
   |  📝 Query 3 ----------------------->| (sent immediately!)
   |                              process |
   |                              process |
   |                              process |
   |<-------------------------- Results 1 |
   |<-------------------------- Results 2 |
   |<-------------------------- Results 3 |

Time: 1 round trip = 40ms (3x faster!)
```

### Basic Pipelining in PyNext

```python
from pynext.db.adapters import QueryPipeline, PipelineConfig

# Create a pipeline
pipeline = QueryPipeline(
    execute_func=db.execute,  # Your database execute function
    config=PipelineConfig(
        max_batch_size=50,    # Send up to 50 queries at once
        flush_interval=0.01,  # Or flush every 10 milliseconds
    )
)

# Add queries to the pipeline
# They don't execute immediately - they wait to be batched!
result1 = await pipeline.add("SELECT * FROM users WHERE id = $1", 1)
result2 = await pipeline.add("SELECT * FROM posts WHERE user_id = $1", 1)
result3 = await pipeline.add("SELECT * FROM comments WHERE post_id = $1", 42)

# The pipeline automatically batches and executes them together
```

### Understanding the Pipeline Configuration

```python
from pynext.db.adapters import PipelineConfig

config = PipelineConfig(
    # Maximum number of queries to batch together
    # Higher = more efficient, but uses more memory
    # Lower = faster response for individual queries
    max_batch_size=50,
    
    # How long to wait before sending a partial batch
    # Lower = faster for low-traffic periods
    # Higher = more efficient batching under load
    flush_interval=0.01,  # 10 milliseconds
    
    # Whether the pipeline is enabled
    enabled=True,
)
```

**How do max_batch_size and flush_interval interact?**

```
Scenario 1: High traffic (100 queries arrive in 5ms)
─────────────────────────────────────────────────────
Queries 1-50 arrive → Batch 1 sent (hit max_batch_size)
Queries 51-100 arrive → Batch 2 sent (hit max_batch_size)

Scenario 2: Low traffic (3 queries arrive over 15ms)
─────────────────────────────────────────────────────
Query 1 arrives at 0ms → Added to batch
Query 2 arrives at 5ms → Added to batch
Query 3 arrives at 8ms → Added to batch
Timer hits 10ms → Batch sent (hit flush_interval)
```

### A Complete Pipelining Example

```python
from pynext.db.adapters import QueryPipeline, PipelineConfig
import asyncio

# Step 1: Create the pipeline
config = PipelineConfig(max_batch_size=100, flush_interval=0.005)

async def run_pipelining_demo():
    # Assume we have a database connection
    async def mock_execute(query, *args):
        """Simulates a database that takes 40ms per query."""
        await asyncio.sleep(0.04)
        return {"query": query, "args": args}
    
    pipeline = QueryPipeline(execute_func=mock_execute, config=config)
    
    # Step 2: Start the pipeline
    await pipeline.start()
    
    try:
        # Step 3: Add many queries - they'll be batched!
        import time
        start = time.time()
        
        # Create 10 concurrent queries
        tasks = [
            pipeline.add("SELECT * FROM users WHERE id = $1", i)
            for i in range(10)
        ]
        
        # Wait for all results
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        print(f"10 queries completed in {elapsed:.3f}s")
        
        # Without pipelining: 10 × 40ms = 400ms
        # With pipelining: ~40-80ms (90% faster!)
        
    finally:
        # Step 4: Clean up
        await pipeline.stop()

asyncio.run(run_pipelining_demo())
```

### When to Use Pipelining

✅ **Great for:**
- Dashboard pages that load many pieces of data
- API endpoints that need multiple related queries
- Background jobs processing multiple records
- Any situation with many independent queries

❌ **Not ideal for:**
- Single queries (no benefit)
- Queries that depend on each other's results
- Transactions (use regular sequential queries)

### Pipeline Statistics

PyNext tracks how effective your pipeline is:

```python
stats = pipeline.get_stats()

print(f"Queries pipelined: {stats['queries_pipelined']}")
print(f"Batches sent: {stats['batches_sent']}")
print(f"Average batch size: {stats['average_batch_size']:.1f}")
print(f"Pipeline efficiency: {stats['efficiency']:.1%}")

# Example output:
# Queries pipelined: 1,234
# Batches sent: 52
# Average batch size: 23.7
# Pipeline efficiency: 95.8%
```

---

## Chapter 4: Caching - The Librarian's Memory

### The Library Analogy

Imagine you're a librarian. Someone asks for "Harry Potter and the Sorcerer's Stone":

**Without memory (no cache):**
```
Person 1: "I need Harry Potter"
Librarian: (walks to shelf, finds book, returns) "Here you go!"  [30 seconds]

Person 2: "I need Harry Potter"
Librarian: (walks to shelf again, finds book, returns) "Here you go!"  [30 seconds]

Person 3: "I need Harry Potter"
Librarian: (walks to shelf AGAIN...) "Here you go!"  [30 seconds]

100 people asking = 3,000 seconds = 50 minutes
```

**With memory (cache):**
```
Person 1: "I need Harry Potter"
Librarian: (walks to shelf, finds book, REMEMBERS location) "Here you go!"  [30 seconds]

Person 2: "I need Harry Potter"
Librarian: "Oh I know where that is!" (grabs from memory) "Here you go!"  [2 seconds]

Person 3: "I need Harry Potter"
Librarian: "Got it!" (from memory) "Here you go!"  [2 seconds]

100 people asking = 30 + 99×2 = 228 seconds = 3.8 minutes (13x faster!)
```

### What is Query Caching?

Query caching stores the results of database queries in memory (RAM), so identical queries can be answered instantly without hitting the database.

```
┌──────────────────────────────────────────────────────────┐
│                        Your App                          │
│                                                          │
│  Request: "Get user 123"                                │
│         ↓                                                │
│  ┌──────────────┐                                       │
│  │    Cache     │  ← Check cache first                  │
│  │  ┌────────┐  │                                       │
│  │  │user_123│  │  Cache hit? → Return immediately!    │
│  │  │  data  │  │                                       │
│  │  └────────┘  │  Cache miss? ↓                        │
│  └──────────────┘                                       │
│         ↓                                                │
│  ┌──────────────┐                                       │
│  │   Database   │  ← Only query if not in cache        │
│  └──────────────┘                                       │
│         ↓                                                │
│  Store result in cache for next time                    │
│         ↓                                                │
│  Return result                                          │
└──────────────────────────────────────────────────────────┘
```

### Basic Caching in PyNext

```python
from pynext.db.adapters import CacheConfig, CachedQueryExecutor

# Create a cache configuration
cache_config = CacheConfig(
    max_size=10000,         # Store up to 10,000 query results
    default_ttl=60.0,       # Results expire after 60 seconds
    enabled=True,
)

# Create the cached executor
cached_db = CachedQueryExecutor(
    execute_func=db.execute,
    config=cache_config,
)

# First call: hits database, stores result in cache
user = await cached_db.execute("SELECT * FROM users WHERE id = $1", 123)
# Took: 42ms (database query)

# Second call: returns cached result instantly!
user = await cached_db.execute("SELECT * FROM users WHERE id = $1", 123)
# Took: 0.1ms (from memory!)

# 420x faster!
```

### Understanding TTL (Time To Live)

TTL is how long a cached result stays valid. It's a trade-off:

```
Short TTL (5 seconds):
├── ✅ Data is always fresh
├── ❌ Less cache benefit (expires quickly)
└── Good for: Frequently changing data (stock prices, live scores)

Long TTL (1 hour):
├── ✅ Maximum cache benefit
├── ❌ Data might be stale
└── Good for: Rarely changing data (user profiles, settings)

No TTL (forever):
├── ✅ Infinite cache benefit
├── ❌ Must manually invalidate
└── Good for: Immutable data (historical records, archived content)
```

### Cache Configuration Explained

```python
from pynext.db.adapters import CacheConfig

config = CacheConfig(
    # Maximum number of query results to cache
    # More = higher memory usage, better hit rate
    max_size=10000,
    
    # Default time before cached results expire (seconds)
    # Shorter = fresher data, lower hit rate
    # Longer = potentially stale data, higher hit rate
    default_ttl=60.0,
    
    # Per-table TTL overrides
    # Some tables change more frequently than others
    table_ttl={
        "users": 300.0,        # User data: cache 5 minutes
        "posts": 60.0,         # Posts: cache 1 minute
        "notifications": 10.0,  # Notifications: cache 10 seconds
        "settings": 3600.0,    # Settings: cache 1 hour
    },
    
    # Whether caching is enabled
    enabled=True,
)
```

### Smart Cache Invalidation

The hardest problem in caching is knowing **when to invalidate** (delete) cached data.

**Problem scenario:**
```
1. User loads their profile → Cached
2. User changes their name
3. User loads their profile → Gets OLD cached name! 😱
```

PyNext provides several invalidation strategies:

#### Strategy 1: TTL-Based (Automatic)

```python
# Data automatically expires after TTL
# Simple but might show stale data for up to TTL seconds
config = CacheConfig(default_ttl=60.0)
```

#### Strategy 2: Tag-Based Invalidation

```python
from pynext.db.adapters import CacheConfig, CachedQueryExecutor

# Mark queries with tags
cached_db = CachedQueryExecutor(execute_func=db.execute, config=config)

# Query with tags
user = await cached_db.execute(
    "SELECT * FROM users WHERE id = $1",
    123,
    cache_tags=["user:123", "users"]  # Tag this result
)

# When user 123 updates their profile:
await cached_db.invalidate_by_tag("user:123")
# This removes ALL cached queries tagged with "user:123"

# Or invalidate all user queries:
await cached_db.invalidate_by_tag("users")
```

#### Strategy 3: Pattern-Based Invalidation

```python
# Invalidate all cached queries matching a pattern
await cached_db.invalidate_by_pattern("SELECT * FROM users%")
# Removes all cached user queries

await cached_db.invalidate_by_pattern("%WHERE user_id = $1%", 123)
# Removes all queries for user 123
```

#### Strategy 4: Smart Invalidation (Automatic)

PyNext can automatically detect which tables a query affects and invalidate related caches:

```python
config = CacheConfig(
    smart_invalidation=True,  # Enable automatic detection
)

cached_db = CachedQueryExecutor(execute_func=db.execute, config=config)

# SELECT query gets cached
user = await cached_db.execute("SELECT * FROM users WHERE id = $1", 123)

# UPDATE automatically invalidates related cache entries!
await cached_db.execute("UPDATE users SET name = $1 WHERE id = $2", "New Name", 123)
# ↑ PyNext detects this modifies 'users' table
# ↑ Automatically invalidates cached queries for user 123
```

### Complete Caching Example

```python
from pynext.db.adapters import CacheConfig, CachedQueryExecutor
import asyncio
import time

async def caching_demo():
    # Simulate a slow database
    async def slow_db_execute(query, *args):
        await asyncio.sleep(0.05)  # 50ms query time
        return {"query": query, "args": args, "data": "result"}
    
    # Configure cache
    config = CacheConfig(
        max_size=1000,
        default_ttl=60.0,
        smart_invalidation=True,
    )
    
    cached_db = CachedQueryExecutor(
        execute_func=slow_db_execute,
        config=config,
    )
    
    # First query - cache miss
    start = time.time()
    result1 = await cached_db.execute("SELECT * FROM users WHERE id = $1", 123)
    time1 = time.time() - start
    print(f"First query: {time1*1000:.1f}ms (cache miss)")
    
    # Second query - cache hit!
    start = time.time()
    result2 = await cached_db.execute("SELECT * FROM users WHERE id = $1", 123)
    time2 = time.time() - start
    print(f"Second query: {time2*1000:.1f}ms (cache hit!)")
    
    # Show improvement
    print(f"Speedup: {time1/time2:.0f}x faster!")
    
    # Check cache statistics
    stats = cached_db.get_stats()
    print(f"\nCache stats:")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.1%}")

asyncio.run(caching_demo())

# Output:
# First query: 51.2ms (cache miss)
# Second query: 0.1ms (cache hit!)
# Speedup: 512x faster!
#
# Cache stats:
#   Hits: 1
#   Misses: 1
#   Hit rate: 50.0%
```

### When to Use Caching

✅ **Great for:**
- Read-heavy workloads (90%+ reads)
- Data that doesn't change frequently
- Expensive queries (JOINs, aggregations)
- Popular content (homepage, trending items)

❌ **Be careful with:**
- Frequently changing data
- User-specific sensitive data (privacy concerns)
- Data requiring absolute consistency
- Queries with many unique parameters

### Cache Statistics

Monitor your cache effectiveness:

```python
stats = cached_db.get_stats()

# Basic metrics
print(f"Total queries: {stats['total_queries']}")
print(f"Cache hits: {stats['hits']}")
print(f"Cache misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate']:.1%}")

# Memory usage
print(f"Cached entries: {stats['entries']}")
print(f"Memory used: {stats['memory_bytes'] / 1024 / 1024:.1f} MB")

# Performance
print(f"Avg cache lookup: {stats['avg_lookup_time_ms']:.2f}ms")
print(f"Avg DB query: {stats['avg_query_time_ms']:.2f}ms")
print(f"Time saved: {stats['time_saved_ms']:.0f}ms")
```

---

## Chapter 5: Query Coalescing - The Carpool

### The Carpool Analogy

Imagine 50 coworkers all need to get to the same office at 9am:

**Without carpooling:**
```
Person 1: Drives alone → 1 car on the road
Person 2: Drives alone → 2 cars on the road
Person 3: Drives alone → 3 cars on the road
...
Person 50: Drives alone → 50 cars on the road

Result: 50 cars, 50 gallons of gas, traffic jam, pollution
```

**With carpooling:**
```
Persons 1-5: Share car 1 → 1 car
Persons 6-10: Share car 2 → 2 cars
...
Persons 46-50: Share car 10 → 10 cars

Result: 10 cars, 10 gallons of gas, less traffic, cleaner air!
```

Same people got to work, but with **80% fewer trips**!

### What is Query Coalescing?

Query coalescing detects when multiple parts of your application request the **exact same data at the same time**, and combines them into a single database query.

```
Without coalescing:
─────────────────────────────────────────────────────
Request A: "Get user 123" → Query 1 → Database
Request B: "Get user 123" → Query 2 → Database  (duplicate!)
Request C: "Get user 123" → Query 3 → Database  (duplicate!)

Database does same work 3 times!

With coalescing:
─────────────────────────────────────────────────────
Request A: "Get user 123" ─┐
Request B: "Get user 123" ─┼→ 1 Query → Database
Request C: "Get user 123" ─┘

Database does work once, result shared with all 3 requests!
```

### When Does This Happen?

More often than you'd think! Consider these scenarios:

**Scenario 1: Popular content**
```
100 users load homepage
All 100 request "SELECT * FROM featured_posts"
Without coalescing: 100 identical queries
With coalescing: 1 query, result shared 100 ways
```

**Scenario 2: Related data in components**
```python
# header.py
user = await db.get_user(current_user_id)  # Gets user

# sidebar.py  
user = await db.get_user(current_user_id)  # Same user again!

# profile_card.py
user = await db.get_user(current_user_id)  # Same user AGAIN!
```

**Scenario 3: N+1 queries**
```python
# Loading 10 posts, each needs author info
for post in posts:
    # If multiple posts have same author, this query is duplicated!
    author = await db.get_user(post.author_id)
```

### Basic Coalescing in PyNext

```python
from pynext.db.adapters import QueryCoalescer, CoalescingConfig

# Configure coalescing
config = CoalescingConfig(
    window_ms=10,      # 10 millisecond window to collect identical queries
    max_waiters=1000,  # Maximum concurrent requests to coalesce
    enabled=True,
)

# Create the coalescer
coalescer = QueryCoalescer(
    execute_func=db.execute,
    config=config,
)

# Start the coalescer
await coalescer.start()

# Now these concurrent queries are automatically coalesced!
async def component_a():
    return await coalescer.execute("SELECT * FROM users WHERE id = $1", 123)

async def component_b():
    return await coalescer.execute("SELECT * FROM users WHERE id = $1", 123)

async def component_c():
    return await coalescer.execute("SELECT * FROM users WHERE id = $1", 123)

# Run all at once
results = await asyncio.gather(component_a(), component_b(), component_c())

# Only ONE database query was made!
# All three components got the same result!
```

### Understanding the Coalescing Window

The "window" is how long the coalescer waits to collect identical queries:

```
Timeline (milliseconds):
──────────────────────────────────────────────────
0ms:  Query A arrives for user 123 → Starts window
3ms:  Query B arrives for user 123 → Joins window  
7ms:  Query C arrives for user 123 → Joins window
10ms: Window closes → Execute 1 query
11ms: Result returned to A, B, and C simultaneously
```

**Trade-off:**

```
Short window (5ms):
├── ✅ Lower latency for first query
├── ❌ Less chance to collect duplicates
└── Good for: Low-latency requirements

Long window (50ms):
├── ✅ More duplicates coalesced
├── ❌ Adds latency to all queries
└── Good for: Very high duplicate rates
```

### Coalescing Configuration Explained

```python
from pynext.db.adapters import CoalescingConfig

config = CoalescingConfig(
    # How long to wait for duplicate queries (milliseconds)
    # Typical: 5-20ms
    window_ms=10,
    
    # Maximum queries to coalesce together
    # Protects memory if you get 10,000 identical requests
    max_waiters=1000,
    
    # Minimum duplicates needed to trigger coalescing
    # Setting to 2 means single queries execute immediately
    min_duplicates=1,
    
    # Whether coalescing is enabled
    enabled=True,
)
```

### A Real-World Coalescing Example

```python
from pynext.db.adapters import QueryCoalescer, CoalescingConfig
import asyncio
import time

async def coalescing_demo():
    # Track actual database calls
    db_call_count = 0
    
    async def db_execute(query, *args):
        nonlocal db_call_count
        db_call_count += 1
        await asyncio.sleep(0.05)  # 50ms query time
        return {"id": args[0], "name": f"User {args[0]}"}
    
    # Configure coalescing
    config = CoalescingConfig(window_ms=20, max_waiters=100)
    coalescer = QueryCoalescer(execute_func=db_execute, config=config)
    await coalescer.start()
    
    try:
        # Simulate 100 components all requesting the same user
        start = time.time()
        
        tasks = [
            coalescer.execute("SELECT * FROM users WHERE id = $1", 123)
            for _ in range(100)
        ]
        
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        print(f"100 requests for same user:")
        print(f"  Database calls made: {db_call_count}")
        print(f"  Time elapsed: {elapsed*1000:.0f}ms")
        print(f"  All results identical: {len(set(str(r) for r in results)) == 1}")
        
        # Without coalescing: 100 calls × 50ms = 5000ms (sequential) or 50ms (parallel but 100x DB load)
        # With coalescing: 1 call × 50ms = 50ms with 1x DB load
        
    finally:
        await coalescer.stop()

asyncio.run(coalescing_demo())

# Output:
# 100 requests for same user:
#   Database calls made: 1
#   Time elapsed: 70ms
#   All results identical: True
```

### Coalescing Statistics

```python
stats = coalescer.get_stats()

print(f"Total queries received: {stats['total_queries']}")
print(f"Queries coalesced: {stats['coalesced_queries']}")
print(f"Actual DB queries: {stats['actual_db_queries']}")
print(f"Coalesce rate: {stats['coalesce_rate']:.1%}")
print(f"Average group size: {stats['avg_group_size']:.1f}")

# Example output:
# Total queries received: 1,000
# Queries coalesced: 920
# Actual DB queries: 80
# Coalesce rate: 92.0%
# Average group size: 12.5
```

### Coalescing vs Caching

These are complementary techniques:

| Aspect | Caching | Coalescing |
|--------|---------|------------|
| **When it helps** | Same query over time | Same query at same time |
| **Memory usage** | Stores results | Only during window |
| **Freshness** | May serve stale data | Always fresh |
| **First query** | Still hits DB | Still hits DB |
| **Repeated query** | Instant (from cache) | Hits DB again |

**Use both together for maximum efficiency!**

```python
# Coalescing handles simultaneous duplicates
# Caching handles duplicates spread over time
# Together they cover all cases!

coalesced_db = QueryCoalescer(execute_func=db.execute, config=coalesce_config)
cached_db = CachedQueryExecutor(execute_func=coalesced_db.execute, config=cache_config)

# Query flow:
# 1. Check cache → If hit, return immediately
# 2. Check coalescer → If identical query pending, wait for it
# 3. Execute query → Store in cache, return result
```

---

## Chapter 6: Adaptive Scaling - The Elastic Restaurant

### The Restaurant Analogy

Imagine you run a restaurant:

**Fixed capacity (no scaling):**
```
Monday 6pm: 20 customers, 10 tables → Everyone seated! 😊
Saturday 7pm: 200 customers, 10 tables → 190 people waiting! 😡
Tuesday 2pm: 2 customers, 10 tables → 8 empty tables wasting money 💸
```

**Adaptive capacity (with scaling):**
```
Monday 6pm: 20 customers → Open 10 tables
Saturday 7pm: 200 customers → Open all 50 tables + outdoor seating!
Tuesday 2pm: 2 customers → Only 3 tables staffed (save money)
```

### What is Adaptive Scaling?

Adaptive scaling automatically adjusts your connection pool size based on actual demand:

```
Low traffic:
┌──────────────────┐
│ Pool: 5 conns    │  ← Minimal resource usage
└──────────────────┘

Medium traffic:
┌────────────────────────────┐
│ Pool: 20 connections       │  ← Scaled up
└────────────────────────────┘

High traffic:
┌────────────────────────────────────────────────┐
│ Pool: 50 connections                           │  ← Maximum capacity
└────────────────────────────────────────────────┘

Traffic spike over:
┌──────────────────┐
│ Pool: 5 conns    │  ← Scaled back down
└──────────────────┘
```

### Why Not Just Use Maximum Connections Always?

Good question! Here's why:

```
Each database connection uses:
├── ~10MB memory on database server
├── ~5MB memory in your application
├── One slot in PostgreSQL's max_connections (typically 100-500)
└── Background keep-alive traffic

50 connections = 750MB memory
If you have 10 app servers = 500 connections = 7.5GB memory!

Plus: Other services might need connections too!
```

Adaptive scaling gives you:
- **Maximum capacity when needed** (during traffic spikes)
- **Minimum resource usage otherwise** (save money, leave room for others)

### Basic Adaptive Scaling in PyNext

```python
from pynext.db.adapters import AdaptiveScaler, AdaptiveScalingConfig

# Configure adaptive scaling
config = AdaptiveScalingConfig(
    min_connections=5,        # Never go below 5
    max_connections=50,       # Never go above 50
    
    scale_up_threshold=0.8,   # Scale up when 80% of connections in use
    scale_down_threshold=0.3, # Scale down when only 30% in use
    
    scale_up_step=5,          # Add 5 connections at a time
    scale_down_step=2,        # Remove 2 at a time (more cautious)
    
    cooldown_seconds=60,      # Wait 60s between scaling actions
)

# Create the scaler
scaler = AdaptiveScaler(pool=connection_pool, config=config)

# Start automatic scaling
await scaler.start()

# That's it! The scaler monitors and adjusts automatically.
```

### Understanding Scaling Thresholds

```
                        Pool Size: 10 connections
                        ┌─────────────────────────────┐
                        │                             │
Scale up threshold 80%  │ - - - - - ⬆️ - - - - - - - │ ← If 8+ connections in use, add more
                        │                             │
                        │       Normal operation      │
                        │                             │
Scale down threshold 30%│ - - - - - ⬇️ - - - - - - - │ ← If only 3 in use, remove some
                        │                             │
                        └─────────────────────────────┘
```

**Example timeline:**

```
Time    In Use   Pool Size   Action
──────────────────────────────────────────────────
0:00    3/10     10          Normal
0:15    5/10     10          Normal
0:30    8/10     10          Scale up! (80% threshold)
0:31    8/15     15          Normal (new size)
0:45    14/15    15          Scale up! (93% > 80%)
0:46    14/20    20          Normal
1:00    6/20     20          Scale down? No, cooldown active
1:30    4/20     20          Scale down! (20% < 30%)
1:31    4/18     18          Normal
2:00    3/18     18          Scale down! (17% < 30%)
2:01    3/16     16          Normal
```

### Predictive Scaling

PyNext can predict traffic patterns and scale **before** you need the capacity:

```python
config = AdaptiveScalingConfig(
    # ... basic settings ...
    
    # Enable prediction
    predictive_scaling=True,
    
    # How much history to analyze
    history_window_hours=24,
    
    # How far ahead to predict
    prediction_window_minutes=15,
)
```

**How prediction works:**

```
Historical data shows:
- 9am: Traffic starts increasing
- 9:30am: Peak traffic
- 10am: Traffic decreases

Without prediction:
─────────────────────────────────────────
9:00  Traffic spikes → "Oh no!" → Scale up → Takes 2 minutes
9:02  New connections ready → Some requests failed during scale-up 😢

With prediction:
─────────────────────────────────────────
8:45  Prediction: "Traffic will spike at 9am" → Scale up proactively
9:00  Traffic spikes → Connections already ready! → Zero failures 🎉
```

### Scaling Configuration Explained

```python
from pynext.db.adapters import AdaptiveScalingConfig

config = AdaptiveScalingConfig(
    # ═══════════════════════════════════════════════════════════
    # CAPACITY LIMITS
    # ═══════════════════════════════════════════════════════════
    
    # Absolute minimum connections (never go below)
    # Should be enough for baseline traffic
    min_connections=5,
    
    # Absolute maximum connections (never exceed)
    # Consider: database limits, memory, other apps sharing DB
    max_connections=50,
    
    # ═══════════════════════════════════════════════════════════
    # SCALING TRIGGERS
    # ═══════════════════════════════════════════════════════════
    
    # Scale up when this % of connections are in use
    # Higher = more efficient, but risk of running out
    # Lower = more headroom, but wastes resources
    scale_up_threshold=0.8,  # 80%
    
    # Scale down when this % of connections are in use
    # Should be well below scale_up_threshold to avoid oscillation
    scale_down_threshold=0.3,  # 30%
    
    # ═══════════════════════════════════════════════════════════
    # SCALING STEPS
    # ═══════════════════════════════════════════════════════════
    
    # How many connections to add when scaling up
    # Larger = faster response to spikes, but might overshoot
    scale_up_step=5,
    
    # How many connections to remove when scaling down
    # Smaller = more cautious (good - don't want to scale down too fast)
    scale_down_step=2,
    
    # ═══════════════════════════════════════════════════════════
    # TIMING
    # ═══════════════════════════════════════════════════════════
    
    # How often to check if scaling is needed
    check_interval_seconds=10,
    
    # Minimum time between scaling actions
    # Prevents rapid scale up/down oscillation
    cooldown_seconds=60,
    
    # ═══════════════════════════════════════════════════════════
    # PREDICTION (OPTIONAL)
    # ═══════════════════════════════════════════════════════════
    
    # Enable predictive scaling based on historical patterns
    predictive_scaling=False,
    
    # How much historical data to consider
    history_window_hours=24,
    
    # How far ahead to predict and pre-scale
    prediction_window_minutes=15,
)
```

### Complete Adaptive Scaling Example

```python
from pynext.db.adapters import AdaptiveScaler, AdaptiveScalingConfig
import asyncio

async def scaling_demo():
    # Create a mock pool for demonstration
    class MockPool:
        def __init__(self):
            self.size = 10
            self.in_use = 0
        
        def get_size(self):
            return self.size
        
        def get_in_use(self):
            return self.in_use
        
        async def resize(self, new_size):
            print(f"  Pool resized: {self.size} → {new_size}")
            self.size = new_size
    
    pool = MockPool()
    
    # Configure scaler
    config = AdaptiveScalingConfig(
        min_connections=5,
        max_connections=50,
        scale_up_threshold=0.8,
        scale_down_threshold=0.3,
        scale_up_step=5,
        scale_down_step=2,
        check_interval_seconds=1,  # Check every second for demo
        cooldown_seconds=2,        # Short cooldown for demo
    )
    
    scaler = AdaptiveScaler(pool=pool, config=config)
    await scaler.start()
    
    try:
        # Simulate traffic patterns
        print("Simulating traffic patterns:\n")
        
        # Low traffic
        print("Phase 1: Low traffic")
        pool.in_use = 2
        await asyncio.sleep(3)
        
        # Increasing traffic
        print("\nPhase 2: Traffic increasing")
        pool.in_use = 8  # 80% of 10
        await asyncio.sleep(3)
        
        # High traffic
        print("\nPhase 3: High traffic")
        pool.in_use = 14  # 93% of 15
        await asyncio.sleep(3)
        
        # Traffic decreasing
        print("\nPhase 4: Traffic decreasing")
        pool.in_use = 4  # 20% of 20
        await asyncio.sleep(5)
        
        print("\n" + "="*50)
        print("Final pool size:", pool.size)
        
    finally:
        await scaler.stop()

asyncio.run(scaling_demo())
```

### Scaling Statistics

```python
stats = scaler.get_stats()

print(f"Current pool size: {stats['current_size']}")
print(f"Current utilization: {stats['utilization']:.1%}")
print(f"Scale up events: {stats['scale_up_count']}")
print(f"Scale down events: {stats['scale_down_count']}")
print(f"Predictions made: {stats['predictions_made']}")
print(f"Prediction accuracy: {stats['prediction_accuracy']:.1%}")
```

---

## Chapter 7: Timeouts - The Safety Net

### The Microwave Analogy

Imagine you put food in the microwave:

**Without a timer:**
```
You: "I'll heat this for a bit..."
(Gets distracted, forgets about microwave)
30 minutes later: Kitchen fills with smoke! 🔥
```

**With a timer:**
```
You: "2 minutes should be enough" (sets timer)
2 minutes later: BEEP! Microwave stops automatically.
Food is heated, kitchen is safe! ✓
```

### What Are Query Timeouts?

Query timeouts automatically cancel database queries that take too long:

```
Without timeout:
─────────────────────────────────────────────────────
Bad query starts → Runs for 5 minutes → Connection blocked
                   ↓
                   All other queries waiting...
                   ↓
                   Website unresponsive 😱

With timeout (10 seconds):
─────────────────────────────────────────────────────
Bad query starts → 10 seconds pass → TIMEOUT! Query cancelled
                   ↓
                   Connection freed
                   ↓
                   Other queries can proceed ✓
```

### Why Queries Get Slow

Queries can become slow for many reasons:

1. **Missing index**: Full table scan instead of index lookup
2. **Lock contention**: Waiting for another transaction
3. **Network issues**: Slow connection to database
4. **Large result set**: Returning millions of rows
5. **Complex joins**: Joining many large tables
6. **Resource exhaustion**: Database server overloaded

### Basic Timeouts in PyNext

```python
from pynext.db.adapters import TimeoutManager, QueryTimeoutConfig

# Configure timeouts
config = QueryTimeoutConfig(
    default_timeout=30.0,  # Default: 30 seconds for any query
)

# Create timeout manager
timeout_mgr = TimeoutManager(config=config)

# Execute with timeout
try:
    result = await timeout_mgr.execute(
        db.execute,
        "SELECT * FROM large_table",
        timeout=10.0,  # Override: 10 seconds for this specific query
    )
except asyncio.TimeoutError:
    print("Query took too long and was cancelled!")
```

### Different Timeouts for Different Queries

Not all queries are equal. A simple lookup should be fast, but a complex report might legitimately take longer:

```python
config = QueryTimeoutConfig(
    # Default for all queries
    default_timeout=30.0,
    
    # Different timeouts by query type
    query_type_timeouts={
        "SELECT": 10.0,   # Reads should be fast
        "INSERT": 5.0,    # Inserts should be very fast
        "UPDATE": 10.0,   # Updates might lock rows
        "DELETE": 10.0,   # Deletes might affect many rows
    },
    
    # Different timeouts by table
    table_timeouts={
        "users": 5.0,          # Users table: fast queries only
        "sessions": 2.0,       # Sessions: very fast
        "analytics": 120.0,    # Analytics: allow slow aggregations
        "reports": 300.0,      # Reports: up to 5 minutes
    },
    
    # Pattern-based timeouts
    pattern_timeouts={
        "%COUNT(%)%": 60.0,          # Aggregations: 1 minute
        "%JOIN%JOIN%JOIN%": 120.0,   # Multiple JOINs: 2 minutes
        "%EXPLAIN%": 10.0,           # EXPLAIN queries: 10 seconds
    },
)
```

### Timeout Resolution Order

When a query runs, PyNext determines its timeout like this:

```
1. Explicit timeout passed to execute()    → Use that
                    ↓ not specified
2. Pattern match (most specific first)     → Use matched timeout
                    ↓ no match
3. Table-specific timeout                  → Use that
                    ↓ not specified
4. Query type timeout (SELECT/INSERT/etc)  → Use that
                    ↓ not specified
5. Default timeout                         → Use that
```

**Example:**

```python
# Query: "SELECT COUNT(*) FROM analytics WHERE date > $1"

# Resolution:
# 1. No explicit timeout passed
# 2. Matches pattern "%COUNT(%)%" → 60 seconds  ← WINNER
# 3. Table "analytics" has 120 second timeout (but pattern was more specific)
# 4. Query type "SELECT" has 10 second timeout (but pattern was more specific)
# 5. Default is 30 seconds (but pattern was more specific)

# Final timeout: 60 seconds
```

### Timeout Configuration Explained

```python
from pynext.db.adapters import QueryTimeoutConfig

config = QueryTimeoutConfig(
    # ═══════════════════════════════════════════════════════════
    # DEFAULT TIMEOUT
    # ═══════════════════════════════════════════════════════════
    
    # Applied when no other timeout matches
    # Should be generous enough for normal queries
    # but short enough to catch runaways
    default_timeout=30.0,  # 30 seconds
    
    # ═══════════════════════════════════════════════════════════
    # QUERY TYPE TIMEOUTS
    # ═══════════════════════════════════════════════════════════
    
    # Different query types have different expected speeds
    query_type_timeouts={
        "SELECT": 10.0,   # Reads: should be fast
        "INSERT": 5.0,    # Inserts: very fast (single row)
        "UPDATE": 10.0,   # Updates: might need to find/lock rows
        "DELETE": 10.0,   # Deletes: might affect many rows
        "CALL": 60.0,     # Stored procedures: might be complex
    },
    
    # ═══════════════════════════════════════════════════════════
    # TABLE-SPECIFIC TIMEOUTS
    # ═══════════════════════════════════════════════════════════
    
    # Some tables are known to be fast or slow
    table_timeouts={
        # Fast tables (small, frequently accessed)
        "users": 5.0,
        "sessions": 2.0,
        "settings": 2.0,
        
        # Medium tables
        "posts": 15.0,
        "comments": 15.0,
        
        # Slow tables (large, complex queries expected)
        "analytics": 120.0,
        "audit_logs": 180.0,
        "reports": 300.0,
    },
    
    # ═══════════════════════════════════════════════════════════
    # PATTERN-BASED TIMEOUTS
    # ═══════════════════════════════════════════════════════════
    
    # Match queries by their SQL content
    # Use % as wildcard
    pattern_timeouts={
        # Aggregations take longer
        "%COUNT(%)%": 60.0,
        "%SUM(%)%": 60.0,
        "%AVG(%)%": 60.0,
        "%GROUP BY%": 60.0,
        
        # Multiple JOINs are expensive
        "%JOIN%JOIN%": 90.0,
        "%JOIN%JOIN%JOIN%": 120.0,
        
        # Full text search can be slow
        "%@@%to_tsquery%": 30.0,
        
        # EXPLAIN should be fast
        "%EXPLAIN%": 10.0,
    },
    
    # ═══════════════════════════════════════════════════════════
    # BEHAVIOR OPTIONS
    # ═══════════════════════════════════════════════════════════
    
    # What to do when timeout occurs
    # "cancel": Cancel the query on the database (recommended)
    # "abandon": Just stop waiting (query continues on DB)
    on_timeout="cancel",
    
    # Whether to log timeout events
    log_timeouts=True,
    
    # Timeout for the cancel command itself
    cancel_timeout=5.0,
)
```

### Complete Timeout Example

```python
from pynext.db.adapters import TimeoutManager, QueryTimeoutConfig
import asyncio

async def timeout_demo():
    # Simulated slow database
    async def slow_db_execute(query, *args, timeout=None):
        if "slow" in query.lower():
            # This query takes 10 seconds
            await asyncio.sleep(10)
        else:
            await asyncio.sleep(0.1)
        return {"success": True}
    
    # Configure timeouts
    config = QueryTimeoutConfig(
        default_timeout=30.0,
        query_type_timeouts={"SELECT": 5.0},
        table_timeouts={"quick_table": 1.0},
    )
    
    timeout_mgr = TimeoutManager(config=config)
    
    # Test 1: Fast query (succeeds)
    print("Test 1: Fast query")
    try:
        result = await timeout_mgr.execute(
            slow_db_execute,
            "SELECT * FROM users WHERE id = $1",
            1
        )
        print("  ✓ Query succeeded\n")
    except asyncio.TimeoutError:
        print("  ✗ Query timed out\n")
    
    # Test 2: Slow query (times out)
    print("Test 2: Slow query (will timeout)")
    try:
        result = await timeout_mgr.execute(
            slow_db_execute,
            "SELECT * FROM slow_table",  # Takes 10 seconds
            timeout=2.0,  # But we only wait 2 seconds
        )
        print("  ✓ Query succeeded\n")
    except asyncio.TimeoutError:
        print("  ✗ Query timed out (as expected!)\n")
    
    # Test 3: Show statistics
    stats = timeout_mgr.get_stats()
    print("Statistics:")
    print(f"  Total queries: {stats['total_queries']}")
    print(f"  Successful: {stats['successful_queries']}")
    print(f"  Timed out: {stats['timed_out_queries']}")
    print(f"  Timeout rate: {stats['timeout_rate']:.1%}")

asyncio.run(timeout_demo())

# Output:
# Test 1: Fast query
#   ✓ Query succeeded
#
# Test 2: Slow query (will timeout)
#   ✗ Query timed out (as expected!)
#
# Statistics:
#   Total queries: 2
#   Successful: 1
#   Timed out: 1
#   Timeout rate: 50.0%
```

### When to Use Timeouts

✅ **Always use timeouts!** They're a safety net that costs nothing when queries are fast.

Specific recommendations:

| Query Type | Recommended Timeout |
|------------|---------------------|
| Simple key lookup | 1-5 seconds |
| Standard SELECT | 5-15 seconds |
| Complex JOIN | 15-60 seconds |
| Aggregation/Report | 60-300 seconds |
| Background job | 300-3600 seconds |

---

## Chapter 8: Batch Optimization - The Factory Assembly Line

### The Assembly Line Analogy

Imagine a factory that makes cars:

**One at a time (no batching):**
```
Car 1: Set up tools → Make car → Clean up → 30 minutes
Car 2: Set up tools → Make car → Clean up → 30 minutes
Car 3: Set up tools → Make car → Clean up → 30 minutes

10 cars = 300 minutes
(Setup and cleanup happen every time!)
```

**Assembly line (batching):**
```
Setup tools once → Make car 1 → Make car 2 → ... → Make car 10 → Clean up once

10 cars = 45 minutes
(Setup and cleanup only once!)
```

### What is Batch Optimization?

Batch optimization automatically groups multiple similar database operations into a single efficient operation:

```
Without batching (10 inserts):
─────────────────────────────────────────────────────
INSERT INTO users (name) VALUES ('Alice')  → Network round trip
INSERT INTO users (name) VALUES ('Bob')    → Network round trip
INSERT INTO users (name) VALUES ('Carol')  → Network round trip
... (7 more)

10 round trips = 400ms network time

With batching (1 bulk insert):
─────────────────────────────────────────────────────
INSERT INTO users (name) VALUES
  ('Alice'),
  ('Bob'),
  ('Carol'),
  ... (7 more)

1 round trip = 40ms network time (10x faster!)
```

### How Batching Works in PyNext

```python
from pynext.db.adapters import BatchOptimizer, BatchConfig

# Configure batching
config = BatchConfig(
    max_batch_size=100,    # Batch up to 100 operations
    flush_interval=0.05,   # Or flush every 50 milliseconds
    enabled=True,
)

# Create batch optimizer
batcher = BatchOptimizer(
    execute_func=db.execute,
    config=config,
)

# Start the batcher
await batcher.start()

# Add operations - they'll be batched automatically!
await batcher.insert("users", {"name": "Alice", "email": "alice@example.com"})
await batcher.insert("users", {"name": "Bob", "email": "bob@example.com"})
await batcher.insert("users", {"name": "Carol", "email": "carol@example.com"})

# These 3 inserts become 1 bulk insert!
```

### Types of Batched Operations

PyNext can batch three types of operations:

#### 1. Bulk INSERT

```python
# Individual inserts → One bulk insert
await batcher.insert("products", {"name": "Widget A", "price": 10})
await batcher.insert("products", {"name": "Widget B", "price": 20})
await batcher.insert("products", {"name": "Widget C", "price": 30})

# Becomes:
# INSERT INTO products (name, price) VALUES
#   ('Widget A', 10),
#   ('Widget B', 20),
#   ('Widget C', 30)
```

#### 2. Bulk UPDATE

```python
# Individual updates → One bulk update
await batcher.update("products", {"id": 1}, {"price": 15})
await batcher.update("products", {"id": 2}, {"price": 25})
await batcher.update("products", {"id": 3}, {"price": 35})

# Becomes:
# UPDATE products SET price = CASE
#   WHEN id = 1 THEN 15
#   WHEN id = 2 THEN 25
#   WHEN id = 3 THEN 35
# END
# WHERE id IN (1, 2, 3)
```

#### 3. Bulk UPSERT (Insert or Update)

```python
# Individual upserts → One bulk upsert
await batcher.upsert("inventory", {"sku": "A001"}, {"quantity": 100})
await batcher.upsert("inventory", {"sku": "A002"}, {"quantity": 200})
await batcher.upsert("inventory", {"sku": "A003"}, {"quantity": 300})

# Becomes:
# INSERT INTO inventory (sku, quantity) VALUES
#   ('A001', 100),
#   ('A002', 200),
#   ('A003', 300)
# ON CONFLICT (sku) DO UPDATE SET quantity = EXCLUDED.quantity
```

### Batch Configuration Explained

```python
from pynext.db.adapters import BatchConfig

config = BatchConfig(
    # ═══════════════════════════════════════════════════════════
    # BATCH SIZE
    # ═══════════════════════════════════════════════════════════
    
    # Maximum operations to batch together
    # Higher = more efficient, but uses more memory
    # PostgreSQL has a limit on query size (~1GB), so don't go too high
    max_batch_size=100,
    
    # Maximum combined size of all values in bytes
    # Prevents creating queries that are too large
    max_batch_bytes=1_000_000,  # 1MB
    
    # ═══════════════════════════════════════════════════════════
    # TIMING
    # ═══════════════════════════════════════════════════════════
    
    # How long to wait for more operations before flushing
    # Lower = faster response for individual operations
    # Higher = more efficient batching under load
    flush_interval=0.05,  # 50 milliseconds
    
    # ═══════════════════════════════════════════════════════════
    # BEHAVIOR
    # ═══════════════════════════════════════════════════════════
    
    # Whether batching is enabled
    enabled=True,
    
    # What to do if one operation in a batch fails
    # "atomic": Rollback entire batch (all or nothing)
    # "continue": Apply successful operations, report failures
    on_error="atomic",
    
    # Whether to return generated IDs for inserts
    return_ids=True,
)
```

### Complete Batching Example

```python
from pynext.db.adapters import BatchOptimizer, BatchConfig
import asyncio
import time

async def batching_demo():
    # Track database operations
    db_operations = []
    
    async def mock_execute(query, *args):
        db_operations.append(query[:50])  # Store first 50 chars
        await asyncio.sleep(0.04)  # 40ms per operation
        return {"success": True}
    
    # Configure batching
    config = BatchConfig(
        max_batch_size=50,
        flush_interval=0.02,  # 20ms
    )
    
    batcher = BatchOptimizer(execute_func=mock_execute, config=config)
    await batcher.start()
    
    try:
        # Insert 100 records
        print("Inserting 100 records...")
        start = time.time()
        
        tasks = [
            batcher.insert("users", {"name": f"User {i}", "email": f"user{i}@example.com"})
            for i in range(100)
        ]
        
        await asyncio.gather(*tasks)
        await batcher.flush()  # Ensure all are sent
        
        elapsed = time.time() - start
        
        print(f"\nResults:")
        print(f"  Records inserted: 100")
        print(f"  Database operations: {len(db_operations)}")
        print(f"  Time elapsed: {elapsed*1000:.0f}ms")
        
        # Without batching: 100 × 40ms = 4000ms
        # With batching (50 per batch): 2 × 40ms = 80ms
        
        print(f"\nOperations sent:")
        for op in db_operations:
            print(f"  {op}...")
        
    finally:
        await batcher.stop()

asyncio.run(batching_demo())

# Output:
# Inserting 100 records...
#
# Results:
#   Records inserted: 100
#   Database operations: 2
#   Time elapsed: 120ms
#
# Operations sent:
#   INSERT INTO users (name, email) VALUES ('Us...
#   INSERT INTO users (name, email) VALUES ('Us...
```

### Batching Statistics

```python
stats = batcher.get_stats()

print(f"Individual operations: {stats['individual_operations']}")
print(f"Batched operations: {stats['batched_operations']}")
print(f"Batches sent: {stats['batches_sent']}")
print(f"Average batch size: {stats['avg_batch_size']:.1f}")
print(f"Reduction ratio: {stats['reduction_ratio']:.1%}")

# Example:
# Individual operations: 1,000
# Batched operations: 20
# Batches sent: 20
# Average batch size: 50.0
# Reduction ratio: 98.0%
```

### When to Use Batching

✅ **Great for:**
- Bulk data imports
- Log/event ingestion
- Sync operations (copying lots of records)
- Background jobs processing many records
- User signups (multiple tables to populate)

❌ **Not ideal for:**
- Single-record operations
- Operations needing immediate ID return
- Transactions requiring specific order
- Operations with different WHERE clauses (hard to batch)

---

## Chapter 9: Putting It All Together

### The Complete Picture

Now you understand all six high-load techniques. Here's how they work together:

```
                            Request arrives
                                  ↓
                    ┌─────────────────────────────┐
                    │         CACHE               │
                    │  "Have I seen this before?" │
                    └─────────────────────────────┘
                         ↓ miss        ↓ hit
                    ┌─────────────┐    └→ Return cached! ✓
                    │  COALESCE   │
                    │  "Is same   │
                    │  query      │
                    │  pending?"  │
                    └─────────────┘
                         ↓ no         ↓ yes
                    ┌─────────────┐    └→ Wait for result ✓
                    │  PIPELINE   │
                    │  "Batch     │
                    │  with other │
                    │  queries?"  │
                    └─────────────┘
                              ↓
                    ┌─────────────────────────────┐
                    │         TIMEOUT             │
                    │  "Start the safety timer"   │
                    └─────────────────────────────┘
                              ↓
                    ┌─────────────────────────────┐
                    │     CONNECTION POOL         │
                    │  (Adaptive scaling adjusts  │
                    │   pool size automatically)  │
                    └─────────────────────────────┘
                              ↓
                    ┌─────────────────────────────┐
                    │       BATCH OPTIMIZER       │
                    │  "Combine with similar      │
                    │   operations?"              │
                    └─────────────────────────────┘
                              ↓
                    ┌─────────────────────────────┐
                    │        DATABASE             │
                    └─────────────────────────────┘
                              ↓
                        Store in cache
                              ↓
                        Return result
```

### A Complete High-Load Configuration

```python
from pynext.db.adapters import (
    # Cache
    CacheConfig, CachedQueryExecutor,
    # Coalesce
    CoalescingConfig, QueryCoalescer,
    # Pipeline
    PipelineConfig, QueryPipeline,
    # Timeout
    QueryTimeoutConfig, TimeoutManager,
    # Batch
    BatchConfig, BatchOptimizer,
    # Scaling
    AdaptiveScalingConfig, AdaptiveScaler,
)

# ═══════════════════════════════════════════════════════════════════
# STEP 1: Create base connection pool
# ═══════════════════════════════════════════════════════════════════

import asyncpg

pool = await asyncpg.create_pool(
    "postgresql://user:pass@localhost/db",
    min_size=5,
    max_size=50,
)

# ═══════════════════════════════════════════════════════════════════
# STEP 2: Wrap with adaptive scaling
# ═══════════════════════════════════════════════════════════════════

scaling_config = AdaptiveScalingConfig(
    min_connections=5,
    max_connections=50,
    scale_up_threshold=0.8,
    scale_down_threshold=0.3,
    cooldown_seconds=60,
)

scaler = AdaptiveScaler(pool=pool, config=scaling_config)
await scaler.start()

# ═══════════════════════════════════════════════════════════════════
# STEP 3: Add timeout protection
# ═══════════════════════════════════════════════════════════════════

timeout_config = QueryTimeoutConfig(
    default_timeout=30.0,
    query_type_timeouts={
        "SELECT": 10.0,
        "INSERT": 5.0,
        "UPDATE": 10.0,
        "DELETE": 10.0,
    },
)

timeout_mgr = TimeoutManager(config=timeout_config)

# Base execute function with timeouts
async def execute_with_timeout(query, *args, timeout=None):
    async with pool.acquire() as conn:
        return await timeout_mgr.execute(
            conn.fetch,
            query,
            *args,
            timeout=timeout,
        )

# ═══════════════════════════════════════════════════════════════════
# STEP 4: Add query pipelining
# ═══════════════════════════════════════════════════════════════════

pipeline_config = PipelineConfig(
    max_batch_size=50,
    flush_interval=0.01,
)

pipeline = QueryPipeline(
    execute_func=execute_with_timeout,
    config=pipeline_config,
)
await pipeline.start()

# ═══════════════════════════════════════════════════════════════════
# STEP 5: Add query coalescing
# ═══════════════════════════════════════════════════════════════════

coalesce_config = CoalescingConfig(
    window_ms=10,
    max_waiters=1000,
)

coalescer = QueryCoalescer(
    execute_func=pipeline.add,  # Routes through pipeline
    config=coalesce_config,
)
await coalescer.start()

# ═══════════════════════════════════════════════════════════════════
# STEP 6: Add caching on top
# ═══════════════════════════════════════════════════════════════════

cache_config = CacheConfig(
    max_size=10000,
    default_ttl=60.0,
    smart_invalidation=True,
)

cached_executor = CachedQueryExecutor(
    execute_func=coalescer.execute,  # Routes through coalescer
    config=cache_config,
)

# ═══════════════════════════════════════════════════════════════════
# STEP 7: Add batch optimization for writes
# ═══════════════════════════════════════════════════════════════════

batch_config = BatchConfig(
    max_batch_size=100,
    flush_interval=0.05,
)

batcher = BatchOptimizer(
    execute_func=execute_with_timeout,  # Bypass cache/coalesce for writes
    config=batch_config,
)
await batcher.start()

# ═══════════════════════════════════════════════════════════════════
# FINAL: Your optimized database interface
# ═══════════════════════════════════════════════════════════════════

class OptimizedDB:
    """Fully optimized database client."""
    
    async def query(self, sql, *args):
        """Execute a read query with full optimization."""
        return await cached_executor.execute(sql, *args)
    
    async def insert(self, table, data):
        """Insert with batching."""
        return await batcher.insert(table, data)
    
    async def update(self, table, where, data):
        """Update with batching."""
        return await batcher.update(table, where, data)
    
    async def execute(self, sql, *args):
        """Execute any query with timeout protection."""
        return await execute_with_timeout(sql, *args)
    
    def stats(self):
        """Get all performance statistics."""
        return {
            "cache": cached_executor.get_stats(),
            "coalesce": coalescer.get_stats(),
            "pipeline": pipeline.get_stats(),
            "batch": batcher.get_stats(),
            "scaling": scaler.get_stats(),
        }
    
    async def close(self):
        """Clean shutdown."""
        await batcher.stop()
        await coalescer.stop()
        await pipeline.stop()
        await scaler.stop()
        await pool.close()

# Use it!
db = OptimizedDB()
users = await db.query("SELECT * FROM users WHERE active = $1", True)
```

### Quick Reference

| Need | Solution | PyNext Component |
|------|----------|-----------------|
| Reduce round trips | Pipeline queries | `QueryPipeline` |
| Avoid repeat queries | Cache results | `CachedQueryExecutor` |
| Handle duplicates | Coalesce queries | `QueryCoalescer` |
| Auto-adjust capacity | Adaptive scaling | `AdaptiveScaler` |
| Prevent slow queries | Timeouts | `TimeoutManager` |
| Bulk operations | Batch optimization | `BatchOptimizer` |

---

## Chapter 10: Production Recipes

### Recipe 1: Small Application (< 100 req/sec)

For small applications, keep it simple:

```python
from pynext.db.adapters import CacheConfig, CachedQueryExecutor, QueryTimeoutConfig

# Simple cache + timeout is usually enough
cache_config = CacheConfig(
    max_size=5000,
    default_ttl=60.0,
)

timeout_config = QueryTimeoutConfig(
    default_timeout=30.0,
)

# That's it! No need for complex optimizations.
```

### Recipe 2: Medium Application (100-1000 req/sec)

Add coalescing and pipelining:

```python
from pynext.db.adapters import (
    CacheConfig, CachedQueryExecutor,
    CoalescingConfig, QueryCoalescer,
    PipelineConfig, QueryPipeline,
    QueryTimeoutConfig,
)

# Cache with smart invalidation
cache_config = CacheConfig(
    max_size=10000,
    default_ttl=60.0,
    smart_invalidation=True,
)

# Coalescing for popular content
coalesce_config = CoalescingConfig(
    window_ms=10,
    max_waiters=500,
)

# Pipelining for dashboard pages
pipeline_config = PipelineConfig(
    max_batch_size=30,
    flush_interval=0.01,
)

# Per-table timeouts
timeout_config = QueryTimeoutConfig(
    default_timeout=30.0,
    table_timeouts={
        "users": 5.0,
        "posts": 10.0,
        "analytics": 60.0,
    },
)
```

### Recipe 3: Large Application (1000+ req/sec)

Full optimization suite:

```python
from pynext.db.adapters import (
    CacheConfig, CachedQueryExecutor,
    CoalescingConfig, QueryCoalescer,
    PipelineConfig, QueryPipeline,
    BatchConfig, BatchOptimizer,
    AdaptiveScalingConfig, AdaptiveScaler,
    QueryTimeoutConfig,
)

# Aggressive caching
cache_config = CacheConfig(
    max_size=50000,
    default_ttl=30.0,
    table_ttl={
        "products": 300.0,    # Products rarely change
        "categories": 3600.0, # Categories almost never change
        "users": 60.0,        # User data changes more often
        "sessions": 10.0,     # Sessions change frequently
    },
    smart_invalidation=True,
)

# Tight coalescing window
coalesce_config = CoalescingConfig(
    window_ms=5,           # Short window for low latency
    max_waiters=2000,      # Handle high concurrency
    min_duplicates=2,
)

# Large batches for efficiency
pipeline_config = PipelineConfig(
    max_batch_size=100,
    flush_interval=0.005,  # 5ms
)

# Aggressive batching for writes
batch_config = BatchConfig(
    max_batch_size=200,
    flush_interval=0.02,  # 20ms
)

# Predictive scaling
scaling_config = AdaptiveScalingConfig(
    min_connections=20,
    max_connections=100,
    scale_up_threshold=0.7,
    scale_down_threshold=0.3,
    predictive_scaling=True,
    history_window_hours=168,  # 1 week
    prediction_window_minutes=30,
)

# Strict timeouts
timeout_config = QueryTimeoutConfig(
    default_timeout=10.0,  # Stricter default
    query_type_timeouts={
        "SELECT": 5.0,
        "INSERT": 2.0,
        "UPDATE": 5.0,
        "DELETE": 5.0,
    },
    pattern_timeouts={
        "%COUNT%": 30.0,
        "%JOIN%JOIN%": 60.0,
    },
)
```

### Recipe 4: High-Write Application (lots of INSERTs)

Focus on batching:

```python
from pynext.db.adapters import BatchConfig, BatchOptimizer

# Maximize batching efficiency
batch_config = BatchConfig(
    max_batch_size=500,        # Large batches
    max_batch_bytes=5_000_000, # 5MB max
    flush_interval=0.1,        # 100ms - prioritize batching over latency
    return_ids=False,          # Skip ID return for speed (if not needed)
)
```

### Recipe 5: Read-Heavy Application (95%+ reads)

Focus on caching:

```python
from pynext.db.adapters import CacheConfig, CachedQueryExecutor

# Maximize cache effectiveness
cache_config = CacheConfig(
    max_size=100000,           # Large cache
    default_ttl=300.0,         # 5 minute default
    table_ttl={
        "static_content": 86400.0,  # 24 hours
        "configuration": 3600.0,    # 1 hour
        "user_profiles": 300.0,     # 5 minutes
    },
    smart_invalidation=True,
)
```

---

## API Reference

### CacheConfig

```python
@dataclass
class CacheConfig:
    max_size: int = 10000           # Maximum cached entries
    default_ttl: float = 60.0       # Default TTL in seconds
    table_ttl: dict = field(...)    # Per-table TTL overrides
    smart_invalidation: bool = False # Auto-invalidate on writes
    enabled: bool = True            # Enable/disable caching
```

### CoalescingConfig

```python
@dataclass
class CoalescingConfig:
    window_ms: int = 10              # Coalescing window in milliseconds
    max_waiters: int = 1000          # Max concurrent waiters
    min_duplicates: int = 1          # Min duplicates to trigger coalescing
    enabled: bool = True             # Enable/disable coalescing
```

### PipelineConfig

```python
@dataclass
class PipelineConfig:
    max_batch_size: int = 50         # Max queries per batch
    flush_interval: float = 0.01     # Flush interval in seconds
    enabled: bool = True             # Enable/disable pipelining
```

### BatchConfig

```python
@dataclass
class BatchConfig:
    max_batch_size: int = 100        # Max operations per batch
    max_batch_bytes: int = 1_000_000 # Max batch size in bytes
    flush_interval: float = 0.05     # Flush interval in seconds
    on_error: str = "atomic"         # "atomic" or "continue"
    return_ids: bool = True          # Return generated IDs
    enabled: bool = True             # Enable/disable batching
```

### AdaptiveScalingConfig

```python
@dataclass
class AdaptiveScalingConfig:
    min_connections: int = 5         # Minimum pool size
    max_connections: int = 50        # Maximum pool size
    scale_up_threshold: float = 0.8  # Scale up at this utilization
    scale_down_threshold: float = 0.3 # Scale down at this utilization
    scale_up_step: int = 5           # Connections to add
    scale_down_step: int = 2         # Connections to remove
    check_interval_seconds: int = 10 # How often to check
    cooldown_seconds: int = 60       # Min time between scaling
    predictive_scaling: bool = False # Enable prediction
    history_window_hours: int = 24   # History for prediction
    prediction_window_minutes: int = 15 # How far ahead to predict
```

### QueryTimeoutConfig

```python
@dataclass
class QueryTimeoutConfig:
    default_timeout: float = 30.0    # Default timeout in seconds
    query_type_timeouts: dict = ...  # Per-query-type timeouts
    table_timeouts: dict = ...       # Per-table timeouts
    pattern_timeouts: dict = ...     # Pattern-based timeouts
    on_timeout: str = "cancel"       # "cancel" or "abandon"
    log_timeouts: bool = True        # Log timeout events
    cancel_timeout: float = 5.0      # Timeout for cancel command
```

---

## Summary

You've learned six powerful techniques for handling high database load:

1. **Pipelining** - Send multiple queries in one network round trip
2. **Caching** - Store results to avoid redundant queries
3. **Coalescing** - Combine identical concurrent queries
4. **Adaptive Scaling** - Automatically adjust pool size
5. **Timeouts** - Prevent slow queries from blocking
6. **Batching** - Group similar operations for efficiency

Each technique addresses a different bottleneck:

| Bottleneck | Solution |
|------------|----------|
| Network latency | Pipelining, Batching |
| Repeated queries | Caching, Coalescing |
| Resource limits | Adaptive Scaling |
| Runaway queries | Timeouts |

Use them together for maximum performance, or pick the ones that match your specific needs.

**Remember**: Start simple, measure, then optimize. Don't add complexity until you need it!
