# PostgreSQL Adapter - Complete Guide

The PyNext PostgreSQL Adapter is a production-ready database client that's both powerful and dead simple to use. This guide explains everything from first principles, so you understand not just HOW to use it, but WHY it works the way it does.

## Table of Contents

1. [Understanding Databases: First Principles](#understanding-databases-first-principles)
2. [Quick Start](#quick-start)
3. [Connection Configuration](#connection-configuration)
4. [Phase 5.1: Core Operations](#phase-51-core-operations)
5. [Phase 5.2: Connection Pooling](#phase-52-connection-pooling)
6. [Phase 5.3: Reliability](#phase-53-reliability)
7. [Phase 5.4: High-Load Optimization](#phase-54-high-load-optimization)
8. [Phase 5.5: Observability](#phase-55-observability)
9. [Phase 5.7: Advanced Queries](#phase-57-advanced-queries)
10. [Configuration Reference](#configuration-reference)
11. [Troubleshooting](#troubleshooting)

---

## Understanding Databases: First Principles

Before diving into the adapter, let's understand what's actually happening when your Python code talks to a database.

### What is a Database Connection?

A database connection is like a phone call between your Python app and PostgreSQL:

```
Your Python App                              PostgreSQL Server
     │                                              │
     │  1. "Hello, I want to connect"              │
     │  ─────────────────────────────────────────► │
     │                                              │
     │  2. "Who are you? Password?"                │
     │  ◄───────────────────────────────────────── │
     │                                              │
     │  3. "I'm user 'myapp', password 'secret'"   │
     │  ─────────────────────────────────────────► │
     │                                              │
     │  4. "OK, you're authenticated. Connection   │
     │      established. Here's your session."     │
     │  ◄───────────────────────────────────────── │
     │                                              │
     │  5. Now you can send SQL queries back       │
     │     and forth on this connection            │
     └──────────────────────────────────────────────┘
```

**Why connections matter:**
- Each connection uses memory on both your app AND the database server
- Creating a connection is SLOW (50-100ms for network handshake + auth)
- PostgreSQL has a limit on how many connections it can handle (typically 100-500)

### The Problem: Web Apps Make Many Requests

Imagine 1000 users hitting your web app simultaneously:

```
❌ WITHOUT Connection Pooling:

User 1 request  ──► Create connection ──► Query ──► Close connection
User 2 request  ──► Create connection ──► Query ──► Close connection
User 3 request  ──► Create connection ──► Query ──► Close connection
...
User 1000       ──► Create connection ──► Query ──► Close connection

Problem:
- 1000 connections = PostgreSQL dies
- 1000 × 100ms = 100 seconds just for connecting!
```

```
✅ WITH Connection Pooling:

                    ┌─── Connection 1 (reused 250 times)
                    │
Pool of 10 ─────────┼─── Connection 2 (reused 250 times)
connections         │
                    ├─── Connection 3 (reused 250 times)
                    │
                    └─── ... (etc)

Result:
- Only 10 connections to PostgreSQL
- Zero time wasted creating connections
- 1000 users served with 10 connections!
```

### Why Async Matters

Python normally waits for each database query to complete:

```python
# Synchronous (blocking) - BAD for web apps
def get_dashboard():
    users = db.query("SELECT * FROM users")      # Wait 50ms
    orders = db.query("SELECT * FROM orders")    # Wait 50ms  
    stats = db.query("SELECT * FROM stats")      # Wait 50ms
    return users, orders, stats                   # Total: 150ms
```

With async, your Python code can do other things while waiting:

```python
# Asynchronous (non-blocking) - GOOD for web apps
async def get_dashboard():
    # Start all three queries simultaneously
    users_task = db.query("SELECT * FROM users")
    orders_task = db.query("SELECT * FROM orders")
    stats_task = db.query("SELECT * FROM stats")
    
    # Wait for all to complete
    users, orders, stats = await asyncio.gather(
        users_task, orders_task, stats_task
    )
    return users, orders, stats  # Total: ~50ms (parallel!)
```

**PyNext uses asyncpg**, the fastest async PostgreSQL driver for Python, which:
- Uses PostgreSQL's binary protocol (faster than text)
- Supports true async/await
- Handles connection pooling automatically

---

## Quick Start

### The Simplest Setup (One Line)

```python
from pynext.db import PostgresAdapter, configure

# This one line sets up EVERYTHING:
# - Connection pool (1-10 connections, auto-scales)
# - Statement caching (1000 statements, 10-30% faster)
# - Auto-retry on transient failures (3 attempts)
# - Circuit breaker (prevents cascading failures)
# - Query coalescing (deduplicates identical queries)
# - Slow query logging (warns you about problems)
adapter = PostgresAdapter("postgresql://user:pass@localhost/mydb")
configure(adapter)

# Now use your models - the adapter handles everything
users = await User.all()
```

### What "Just Works" Means

When you create a `PostgresAdapter` with just a URL, you get these features enabled automatically:

| Feature | Default Setting | What It Does | Why It Matters |
|---------|-----------------|--------------|----------------|
| **Connection Pool** | 1-10 connections | Reuses connections across requests | 100x faster than connecting each time |
| **Statement Cache** | 1000 statements | Remembers parsed SQL | 10-30% faster for repeated queries |
| **Auto-Retry** | 3 attempts | Retries on network errors | Handles Wi-Fi blips, server restarts |
| **Circuit Breaker** | Opens after 5 failures | Stops hammering a dead database | Prevents your app from making things worse |
| **Query Coalescing** | Enabled | Same query from 100 users = 1 database call | Massive savings on hot queries |
| **Slow Query Logging** | 1 second threshold | Logs queries taking > 1s | You'll know when something's wrong |

### Connecting to Your Database

```python
# Step 1: Create the adapter
adapter = PostgresAdapter("postgresql://user:pass@localhost/mydb")

# Step 2: Connect (call once at app startup)
await adapter.connect()

# Step 3: Use your models
users = await User.all()
products = await Product.where(active=True).all()

# Step 4: Disconnect (call at app shutdown)
await adapter.disconnect()
```

### Using as a Context Manager

For scripts or testing, use the context manager pattern:

```python
async with PostgresAdapter("postgresql://localhost/mydb") as adapter:
    # Connection is established
    users = await User.all()
# Connection is automatically closed here
```

---

## Connection Configuration

### Understanding the Connection URL

A PostgreSQL connection URL has this format:

```
postgresql://[user][:password]@[host][:port]/[database][?options]
          │       │            │      │       │          │
          │       │            │      │       │          └─ Query parameters
          │       │            │      │       └─ Database name
          │       │            │      └─ Port (default: 5432)
          │       │            └─ Server hostname or IP
          │       └─ Password (optional)
          └─ Username
```

**Examples:**

```python
# Local development (no password)
adapter = PostgresAdapter("postgresql://postgres@localhost/mydb")

# Production with password
adapter = PostgresAdapter("postgresql://myapp:secretpass@db.example.com/production")

# Custom port
adapter = PostgresAdapter("postgresql://user:pass@localhost:5433/mydb")

# With SSL (required by most cloud providers)
adapter = PostgresAdapter("postgresql://user:pass@db.example.com/mydb?sslmode=require")
```

### Method 1: URL (Recommended for Simplicity)

```python
# Everything in one string
adapter = PostgresAdapter("postgresql://user:pass@localhost:5432/mydb")
```

**Pros:**
- Single configuration value
- Easy to store in environment variables
- Standard format (works with any tool)

**Cons:**
- Password visible in logs if you print the URL
- Less flexibility for complex setups

### Method 2: Keyword Arguments (Recommended for Security)

```python
import os

adapter = PostgresAdapter(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password=os.environ["DB_PASSWORD"],  # Never hardcode passwords!
)
```

**Pros:**
- Password separate from other config
- Explicit about every setting
- Easy to use environment variables

**Cons:**
- More verbose

### Method 3: Mixed (Best of Both Worlds)

```python
import os

# URL for most settings, environment variable for password
adapter = PostgresAdapter(
    url="postgresql://myapp@db.example.com/production",
    password=os.environ["DB_PASSWORD"],  # Override password from env
)
```

This pattern is ideal because:
1. The URL can be in your config/code (no secrets)
2. The password comes from environment (secure)
3. You can easily switch databases by changing the URL

### SSL/TLS Configuration

Modern cloud databases (AWS RDS, Google Cloud SQL, Supabase) require SSL:

```python
# Simple SSL (trust server certificate)
adapter = PostgresAdapter(
    url="postgresql://user:pass@cloud-db.example.com/mydb",
    ssl=True,
)

# Strict SSL (verify server certificate)
adapter = PostgresAdapter(
    url="postgresql://user:pass@cloud-db.example.com/mydb?sslmode=verify-full&sslrootcert=/path/to/ca.crt",
)
```

**SSL Modes Explained:**

| Mode | Security | Use Case |
|------|----------|----------|
| `disable` | None | Local development only |
| `allow` | Optional | Not recommended |
| `prefer` | Optional | Tries SSL, falls back to plain |
| `require` | Encrypted | **Production minimum** |
| `verify-ca` | Encrypted + CA check | High security |
| `verify-full` | Encrypted + hostname check | **Maximum security** |

---

## Phase 5.1: Core Operations

### Understanding CRUD

CRUD stands for Create, Read, Update, Delete - the four basic database operations:

```
┌─────────────────────────────────────────────────────────────────┐
│                        CRUD Operations                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CREATE (INSERT)      Read a new record into the database      │
│  ────────────────                                               │
│  INSERT INTO users (name, email) VALUES ('Alice', 'a@b.com')   │
│                                                                 │
│  READ (SELECT)        Retrieve records from the database       │
│  ─────────────                                                  │
│  SELECT * FROM users WHERE active = true                        │
│                                                                 │
│  UPDATE               Modify existing records                   │
│  ──────                                                         │
│  UPDATE users SET active = false WHERE id = 123                 │
│                                                                 │
│  DELETE               Remove records from the database          │
│  ──────                                                         │
│  DELETE FROM users WHERE created_at < '2020-01-01'              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Connecting and Disconnecting

```python
# ═══════════════════════════════════════════════════════════════
# CONNECTING
# ═══════════════════════════════════════════════════════════════

# Create the adapter (doesn't connect yet)
adapter = PostgresAdapter("postgresql://localhost/mydb")

# Now actually connect (establishes pool, validates connection)
await adapter.connect()

# What happens during connect():
# 1. Creates the connection pool
# 2. Opens min_connections connections to PostgreSQL
# 3. Runs warmup queries (if enabled)
# 4. Validates by running "SELECT 1"
# 5. If anything fails, raises an error with details


# ═══════════════════════════════════════════════════════════════
# DISCONNECTING
# ═══════════════════════════════════════════════════════════════

# When your app shuts down, disconnect cleanly
await adapter.disconnect()

# What happens during disconnect():
# 1. Waits for active queries to complete (with timeout)
# 2. Closes all connections in the pool
# 3. Releases any cached resources
# 4. Logs that the connection was closed
```

### Insert Operations

```python
# ═══════════════════════════════════════════════════════════════
# INSERT ONE RECORD
# ═══════════════════════════════════════════════════════════════

# Insert and get the created record back (with auto-generated ID)
user = await adapter.insert(
    "users",                              # Table name
    {"name": "Alice", "email": "a@b.com"},  # Data to insert
    fields                                # Field definitions (from your model)
)
print(user)  # {"id": 1, "name": "Alice", "email": "a@b.com", "created_at": ...}

# Under the hood, this runs:
# INSERT INTO "users" ("name", "email") VALUES ($1, $2) RETURNING *


# ═══════════════════════════════════════════════════════════════
# INSERT MANY RECORDS
# ═══════════════════════════════════════════════════════════════

# Insert multiple records at once
users = await adapter.insert_many(
    "users",
    [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
        {"name": "Charlie", "email": "charlie@example.com"},
    ],
    fields
)
print(len(users))  # 3

# For LARGE batches (1000+ rows), use batch_insert instead:
count = await adapter.batch_insert(
    "users",
    [{"name": f"User {i}"} for i in range(10000)],
    batch_size=500,  # Insert 500 at a time
)
```

### Select Operations

```python
# ═══════════════════════════════════════════════════════════════
# BASIC SELECT
# ═══════════════════════════════════════════════════════════════

# Using the Query builder
from pynext.db import Query

query = Query().where(active=True).order_by("created_at", "desc").limit(10)
users = await adapter.select("users", query, fields)

# This runs:
# SELECT * FROM "users" WHERE "active" = $1 ORDER BY "created_at" DESC LIMIT 10


# ═══════════════════════════════════════════════════════════════
# COMMON QUERY PATTERNS
# ═══════════════════════════════════════════════════════════════

# Find by ID
query = Query().where(id=123)
user = await adapter.select_one("users", query, fields)

# Find with multiple conditions (AND)
query = Query().where(active=True, role="admin")
# WHERE active = true AND role = 'admin'

# Find with OR conditions
query = Query().where_any(role="admin", role="moderator")
# WHERE role = 'admin' OR role = 'moderator'

# Find with comparison operators
query = Query().where(age__gte=18)  # Greater than or equal
# WHERE age >= 18

# Available operators:
# __eq    = Equal (default)
# __ne    = Not equal
# __gt    = Greater than
# __gte   = Greater than or equal
# __lt    = Less than
# __lte   = Less than or equal
# __in    = In list
# __like  = LIKE pattern
# __ilike = Case-insensitive LIKE
```

### Update Operations

```python
# ═══════════════════════════════════════════════════════════════
# UPDATE RECORDS
# ═══════════════════════════════════════════════════════════════

# Update matching records
query = Query().where(role="user", last_login__lt="2023-01-01")
count = await adapter.update(
    "users",
    query,
    {"active": False},  # New values
    fields
)
print(f"Deactivated {count} inactive users")

# This runs:
# UPDATE "users" SET "active" = $1 
# WHERE "role" = $2 AND "last_login" < $3


# ═══════════════════════════════════════════════════════════════
# UPDATE ONE RECORD
# ═══════════════════════════════════════════════════════════════

# Update a specific record by ID
await adapter.update_one(
    "users",
    Query().where(id=123),
    {"email": "newemail@example.com"},
    fields
)
```

### Delete Operations

```python
# ═══════════════════════════════════════════════════════════════
# DELETE RECORDS
# ═══════════════════════════════════════════════════════════════

# Delete matching records
query = Query().where(active=False, created_at__lt="2020-01-01")
count = await adapter.delete("users", query)
print(f"Deleted {count} old inactive users")

# This runs:
# DELETE FROM "users" WHERE "active" = $1 AND "created_at" < $2


# ═══════════════════════════════════════════════════════════════
# SOFT DELETE (Recommended)
# ═══════════════════════════════════════════════════════════════

# Instead of actually deleting, mark as deleted:
await adapter.update(
    "users",
    Query().where(id=123),
    {"deleted_at": datetime.now()},
    fields
)

# Then in your queries, exclude deleted records:
query = Query().where(deleted_at=None)
active_users = await adapter.select("users", query, fields)
```

### Transactions

A transaction groups multiple operations so they ALL succeed or ALL fail:

```python
# ═══════════════════════════════════════════════════════════════
# WHY TRANSACTIONS MATTER
# ═══════════════════════════════════════════════════════════════

# Imagine transferring money between accounts:

# ❌ WITHOUT transaction - DANGEROUS!
await adapter.update("accounts", Query().where(id=1), {"balance": balance_1 - 100})
# ⚡ CRASH HERE = Money disappeared!
await adapter.update("accounts", Query().where(id=2), {"balance": balance_2 + 100})


# ✅ WITH transaction - SAFE
async with adapter.transaction():
    await adapter.update("accounts", Query().where(id=1), {"balance": balance_1 - 100})
    # If crash happens here, BOTH updates are rolled back
    await adapter.update("accounts", Query().where(id=2), {"balance": balance_2 + 100})
# Only if BOTH succeed, changes are committed


# ═══════════════════════════════════════════════════════════════
# TRANSACTION EXAMPLE
# ═══════════════════════════════════════════════════════════════

async def create_order(user_id: int, items: list):
    async with adapter.transaction():
        # Create the order
        order = await Order.insert(user_id=user_id, status="pending")
        
        # Add order items
        for item in items:
            await OrderItem.insert(
                order_id=order.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
            )
        
        # Reduce inventory
        for item in items:
            await Product.update(
                Query().where(id=item["product_id"]),
                {"stock": Product.stock - item["quantity"]}
            )
        
        # If ANY of these fail, ALL are rolled back
        return order


# ═══════════════════════════════════════════════════════════════
# NESTED TRANSACTIONS (SAVEPOINTS)
# ═══════════════════════════════════════════════════════════════

async with adapter.transaction():
    await User.insert(name="Alice")
    
    try:
        async with adapter.transaction():  # Creates a savepoint
            await Account.insert(user_id=1, type="checking")
            raise ValueError("Oops!")  # This fails
    except ValueError:
        # Inner transaction rolled back, outer continues
        pass
    
    await User.insert(name="Bob")  # This still works
# Alice and Bob are saved, Account is not
```

---

## Phase 5.2: Connection Pooling

### What is Connection Pooling?

Connection pooling is like a car rental service for database connections:

```
Without Pooling (Buy a car for each trip):
───────────────────────────────────────────────────────────────────
Request 1: Buy car → Drive → Scrap car           Cost: $30,000
Request 2: Buy car → Drive → Scrap car           Cost: $30,000
Request 3: Buy car → Drive → Scrap car           Cost: $30,000
                                          Total: $90,000 + slow!

With Pooling (Rent from a fleet):
───────────────────────────────────────────────────────────────────
                   ┌─ Car A ─┐
Request 1 ────────►│         │◄──────── Request 4
                   │  Pool   │
Request 2 ────────►│   of    │◄──────── Request 5
                   │  Cars   │
Request 3 ────────►│         │◄──────── Request 6
                   └─────────┘
                        Total: $500/month + instant!
```

### How PyNext Pooling Works

```
                        PyNext PostgresAdapter
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   Incoming         Connection Pool                PostgreSQL     │
│   Requests         ┌──────────────┐                             │
│                    │              │                              │
│   Request 1 ──────►│  Conn 1 ════╪════► [Connected]             │
│                    │  (busy)     │                              │
│   Request 2 ──────►│  Conn 2 ════╪════► [Connected]             │
│       ▼            │  (busy)     │                              │
│   [Queue]          │  Conn 3 ════╪════► [Connected]             │
│   Request 3        │  (idle)     │                              │
│   Request 4        │  Conn 4 ════╪════► [Connected]             │
│   Request 5        │  (idle)     │                              │
│                    │             │                              │
│                    │  ┌─────────┐│                              │
│                    │  │ Scaler  ││  "Load increasing,           │
│                    │  │         ││   adding more connections"   │
│                    │  └─────────┘│                              │
│                    │             │                              │
│                    └──────────────┘                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Basic Pool Configuration

```python
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    
    # ═══════════════════════════════════════════════════════════
    # POOL SIZE
    # ═══════════════════════════════════════════════════════════
    
    min_connections=5,    # Always keep 5 connections ready
                          # Why: Avoids cold-start latency
                          # Tradeoff: Uses memory even when idle
    
    max_connections=50,   # Never exceed 50 connections
                          # Why: PostgreSQL has limits (default ~100)
                          # Tradeoff: Too high = OOM, too low = queuing
    
    # Rule of thumb: max_connections = 2-3x your expected concurrent requests
    # For a server handling 20 concurrent requests: min=5, max=50
    
    
    # ═══════════════════════════════════════════════════════════
    # TIMEOUTS
    # ═══════════════════════════════════════════════════════════
    
    acquire_timeout=30.0,  # Wait up to 30s for a connection
                           # If pool is exhausted and queue is full
                           # After 30s, raise an error
    
    idle_timeout=300.0,    # Close connections idle for 5 minutes
                           # Why: Release resources during low traffic
                           # Will scale back up when traffic increases
    
    max_lifetime=3600.0,   # Replace connections after 1 hour
                           # Why: Prevents stale connections
                           # Some proxies/firewalls kill old connections
)
```

### Understanding Pool Sizing

```
How to choose pool size:
═══════════════════════════════════════════════════════════════════

Step 1: Know your PostgreSQL limit
───────────────────────────────────
Check your PostgreSQL configuration:
  SHOW max_connections;  -- Usually 100-200

Your app should use LESS than this, leaving room for:
  - Admin connections
  - Other applications
  - Replication
  - Background workers

Rule: Use at most 50-80% of max_connections


Step 2: Know your traffic pattern
─────────────────────────────────
Peak concurrent requests:
  - Small app: 10-20
  - Medium app: 50-100
  - Large app: 100-500

Each concurrent request typically needs 1 connection


Step 3: Calculate
─────────────────
PostgreSQL limit: 200
Safety margin (70%): 140
Other services use: 40
Available for your app: 100

Peak concurrent requests: 50
Set max_connections: 50-75

Minimum connections (for fast response):
  If traffic is consistent: min = max * 0.5
  If traffic is bursty: min = max * 0.2


Example configurations:
───────────────────────

# Small app (10 concurrent users)
min_connections=2, max_connections=10

# Medium app (50 concurrent users)
min_connections=10, max_connections=50

# Large app (200 concurrent users)
min_connections=25, max_connections=100

# High-traffic API (1000+ concurrent)
min_connections=50, max_connections=200
# Plus: Use read replicas and caching!
```

### Connection Warmup

Cold connections are slow. Warmup makes them fast:

```python
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    
    warmup=True,               # Enable warmup
    warmup_query="SELECT 1",   # Query to run on new connections
)
```

**What warmup does:**
1. When a new connection is created
2. Before returning it to the pool
3. Runs the warmup query
4. This triggers PostgreSQL to cache query plans and connection state

**Why it matters:**
```
Without warmup:
  First query on new connection: 50ms
  Second query: 5ms
  
With warmup:
  First query on new connection: 5ms (warmup already ran)
  Second query: 5ms
```

### Pool Statistics

Monitor your pool health:

```python
# ═══════════════════════════════════════════════════════════════
# BASIC POOL STATS
# ═══════════════════════════════════════════════════════════════

stats = adapter.get_pool_stats()

print(f"Pool size: {stats.size}")           # Current total connections
print(f"Busy: {stats.busy}")                 # Connections running queries
print(f"Idle: {stats.idle}")                 # Connections waiting for work
print(f"Queue depth: {stats.queue_depth}")   # Requests waiting for connections


# ═══════════════════════════════════════════════════════════════
# QUEUE STATS (When pool is exhausted)
# ═══════════════════════════════════════════════════════════════

queue_stats = adapter.get_queue_stats()

print(f"Waiting requests: {queue_stats.depth}")
print(f"Average wait time: {queue_stats.wait_time_avg_ms}ms")
print(f"Max wait time: {queue_stats.wait_time_max_ms}ms")


# ═══════════════════════════════════════════════════════════════
# HEALTH INDICATORS
# ═══════════════════════════════════════════════════════════════

# Is the pool struggling?
if adapter.is_under_pressure:
    # Queue is building up - maybe return 503?
    return Response("System busy, please retry", status=503)

# How deep is the queue?
if adapter.queue_depth > 100:
    logger.warning(f"High queue depth: {adapter.queue_depth}")
```

### Using External Poolers (PgBouncer)

For very high traffic, use an external connection pooler:

```
Without PgBouncer:
══════════════════

Web Server 1 (50 connections) ─┐
Web Server 2 (50 connections) ─┼──► PostgreSQL (150 connections)
Web Server 3 (50 connections) ─┘

Problem: 3 servers × 50 = 150 connections to PostgreSQL


With PgBouncer:
══════════════════

Web Server 1 (50 connections) ─┐
Web Server 2 (50 connections) ─┼──► PgBouncer (20 connections) ──► PostgreSQL
Web Server 3 (50 connections) ─┘

Benefit: 150 app connections share 20 database connections!
```

```python
from pynext.db.adapters import ExternalPoolerConfig, PoolerMode

adapter = PostgresAdapter(
    # Connect to PgBouncer, not PostgreSQL directly
    url="postgresql://localhost:6432/mydb",  # PgBouncer's port
    
    external_pooler=ExternalPoolerConfig(
        enabled=True,
        mode=PoolerMode.TRANSACTION,  # Recommended for web apps
    ),
)
```

**Pooler Modes:**

| Mode | How It Works | Best For |
|------|--------------|----------|
| `SESSION` | Connection held for entire session | Long-running apps |
| `TRANSACTION` | Connection held per transaction | **Web apps** (recommended) |
| `STATEMENT` | Connection held per statement | Simple queries only |

---

## Phase 5.3: Reliability

### Why Reliability Matters

Databases fail. Networks fail. Your app shouldn't:

```
Reality of Production:
═══════════════════════════════════════════════════════════════════

[Your App] ─────────────────────────────────────────► [PostgreSQL]
              │                                              │
              │  Things that can go wrong:                   │
              │  • Network blip (WiFi, router restart)       │
              │  • PostgreSQL restart (updates, crashes)     │
              │  • Deadlocks (concurrent transactions)       │
              │  • Overload (too many queries)               │
              │  • Cloud issues (AWS/GCP hiccups)            │
              │                                              │
              └──────────────────────────────────────────────┘

Without reliability features: App crashes, users see errors
With reliability features: App retries, users don't notice
```

### Auto-Retry

Transient failures are temporary - just try again:

```python
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    
    retry=True,          # Enable auto-retry (default: True)
    retry_attempts=3,    # Try up to 3 times (default: 3)
)
```

**How retry works:**

```
Attempt 1: Query fails with "connection reset"
           ↓
           Wait 100ms (exponential backoff)
           ↓
Attempt 2: Query fails with "connection reset"
           ↓
           Wait 200ms
           ↓
Attempt 3: Query succeeds! ✓
           ↓
           Return result to your code
```

**What gets retried (automatically detected):**

| Error | Retried? | Why |
|-------|----------|-----|
| Connection reset | ✅ Yes | Network blip |
| Connection refused | ✅ Yes | Server restarting |
| Deadlock detected | ✅ Yes | Concurrent modification |
| Serialization failure | ✅ Yes | Transaction conflict |
| Syntax error | ❌ No | Your bug, not transient |
| Constraint violation | ❌ No | Data issue |
| Permission denied | ❌ No | Auth issue |

**Manual retry control:**

```python
# For operations that need custom retry logic
result = await adapter.with_retry(
    lambda: some_risky_operation(),
    max_attempts=5,
)

# Check retry statistics
stats = adapter.get_retry_stats()
print(f"Total retries: {stats.total_retries}")
print(f"Success rate: {stats.success_rate:.1%}")
```

### Circuit Breaker

When the database is DOWN, stop hammering it:

```python
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    
    circuit_breaker=True,         # Enable (default: True)
    circuit_breaker_threshold=5,  # Open after 5 failures
)
```

**How circuit breaker works:**

```
                 Circuit Breaker States
═══════════════════════════════════════════════════════════════════

    CLOSED                  OPEN                   HALF_OPEN
   ┌───────┐              ┌───────┐               ┌───────┐
   │       │   5 failures │       │    30 sec     │       │
   │ Allow ├─────────────►│ Block ├──────────────►│ Test  │
   │  all  │              │  all  │               │ one   │
   │       │              │       │               │       │
   └───┬───┘              └───┬───┘               └───┬───┘
       │                      │                       │
       │                      │                       │
       ▼                      ▼                       ▼
   Normal                  Fail fast              If success: → CLOSED
   operation               (no DB call)           If failure: → OPEN


Example timeline:
─────────────────
10:00:00  Query 1: Success (CLOSED)
10:00:01  Query 2: Success (CLOSED)
10:00:02  Query 3: FAIL - DB down (1 failure)
10:00:03  Query 4: FAIL (2 failures)
10:00:04  Query 5: FAIL (3 failures)
10:00:05  Query 6: FAIL (4 failures)
10:00:06  Query 7: FAIL (5 failures) → CIRCUIT OPENS
10:00:07  Query 8: Instant fail, no DB call (OPEN)
10:00:08  Query 9: Instant fail, no DB call (OPEN)
...
10:00:36  30 seconds passed → HALF_OPEN
10:00:37  Query 10: Try one query... Success! → CLOSED
10:00:38  Query 11: Normal operation (CLOSED)
```

**Using the circuit breaker:**

```python
# Check circuit state before expensive operations
if adapter.is_circuit_open:
    # Database is having problems, use fallback
    return get_cached_response()

# Or check the specific state
from pynext.db.adapters import CircuitState

match adapter.circuit_state:
    case CircuitState.CLOSED:
        # Normal operation
        return await fetch_from_db()
    case CircuitState.OPEN:
        # Database is down
        return get_fallback_response()
    case CircuitState.HALF_OPEN:
        # Testing if database recovered
        return await fetch_from_db()

# After you fix the database, reset manually
adapter.reset_circuit()
```

### Read Replicas

Distribute read load across multiple servers:

```
                        Read Replica Architecture
═══════════════════════════════════════════════════════════════════

                    ┌─────────────────────┐
   WRITES ─────────►│   Primary (Master)  │
                    │   - Handles writes  │
                    │   - Always up-to-date│
                    └─────────┬───────────┘
                              │
                              │ Replication (async)
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ Replica 1│    │ Replica 2│    │ Replica 3│
        │ (weight 1)│    │ (weight 2)│    │ (weight 1)│
        └──────────┘    └──────────┘    └──────────┘
              ▲               ▲               ▲
              │               │               │
              └───────────────┼───────────────┘
                              │
   READS ─────────────────────┘  (load balanced)
```

```python
# Add replicas dynamically
await adapter.add_replica("postgresql://replica1/mydb")
await adapter.add_replica("postgresql://replica2/mydb", weight=2)  # 2x traffic

# Check replica stats
stats = adapter.get_replica_stats()
print(f"Replicas: {stats.replica_count}")
print(f"Reads on replicas: {stats.reads_routed}")
print(f"Reads on primary: {stats.reads_on_primary}")

# Remove a problematic replica
await adapter.remove_replica("postgresql://replica1/mydb")
```

**Routing logic:**
- **All writes** → Primary (required for consistency)
- **Normal reads** → Random replica (weighted)
- **Reads after write** → Primary (to see your own changes)
- **Reads in transaction** → Primary (consistency)

### Graceful Degradation

When the database struggles, degrade gracefully instead of failing:

```python
from pynext.db.adapters import DegradationLevel

# Check current level
match adapter.degradation_level:
    case DegradationLevel.NORMAL:
        # Everything fine, full functionality
        pass
        
    case DegradationLevel.DEGRADED:
        # Some issues detected
        # Disable non-essential features
        disable_analytics()
        disable_recommendations()
        
    case DegradationLevel.CRITICAL:
        # Serious issues
        # Serve cached content only
        return cached_response()
        
    case DegradationLevel.EMERGENCY:
        # Database is unreachable
        # Return maintenance page
        return maintenance_page()

# Quick check
if adapter.is_degraded:
    logger.warning("Database is degraded, limiting features")
```

**What triggers each level:**

| Level | Trigger | Response |
|-------|---------|----------|
| NORMAL | All healthy | Full functionality |
| DEGRADED | Queue > 50% or error rate > 5% | Disable non-essential |
| CRITICAL | Queue > 80% or error rate > 20% | Cache only |
| EMERGENCY | Circuit open or unreachable | Maintenance mode |

---

## Phase 5.4: High-Load Optimization

### Query Coalescing

When 100 users request the same data, only hit the database once:

```
                    Without Coalescing
═══════════════════════════════════════════════════════════════════

User 1 ──► Query: "SELECT * FROM products LIMIT 10" ──► DB ──► Result
User 2 ──► Query: "SELECT * FROM products LIMIT 10" ──► DB ──► Result
User 3 ──► Query: "SELECT * FROM products LIMIT 10" ──► DB ──► Result
...
User 100 ► Query: "SELECT * FROM products LIMIT 10" ──► DB ──► Result

Database executes: 100 queries
Total time: 100 × 10ms = 1 second


                    With Coalescing
═══════════════════════════════════════════════════════════════════

User 1 ──► Query ──┐
User 2 ──► Query ──┼──► Coalescer ──► 1 Query ──► DB ──► Result
User 3 ──► Query ──┤                                       │
...                │                                       │
User 100 ► Query ──┘                                       │
    ▲                                                      │
    └──────────── All 100 users get the same result ◄──────┘

Database executes: 1 query
Total time: 10ms + broadcast = ~15ms
```

```python
# Use coalescing for hot queries
result = await adapter.coalesce(
    "SELECT * FROM popular_products LIMIT 10"
)

# Check how much you're saving
stats = adapter.get_coalesce_stats()
print(f"Queries executed: {stats.queries_executed}")
print(f"Queries coalesced: {stats.queries_coalesced}")
print(f"Queries saved: {stats.queries_saved}")
print(f"Hit rate: {stats.hit_rate:.1%}")  # e.g., "92.3%"
```

**When to use coalescing:**
- ✅ Homepage data
- ✅ Navigation menus
- ✅ Popular products
- ✅ Public content
- ❌ User-specific data
- ❌ Writes/updates

### Batch Operations

Insert thousands of rows efficiently:

```python
# ═══════════════════════════════════════════════════════════════
# THE SLOW WAY (Don't do this!)
# ═══════════════════════════════════════════════════════════════

for user in 10000_users:
    await adapter.insert("users", user, fields)
# Time: 10,000 × 5ms = 50 seconds!


# ═══════════════════════════════════════════════════════════════
# THE FAST WAY (Use batch_insert)
# ═══════════════════════════════════════════════════════════════

count = await adapter.batch_insert(
    "users",
    [{"name": f"User {i}", "email": f"user{i}@example.com"} 
     for i in range(10000)],
    batch_size=500,  # 500 rows per INSERT
)
# Time: 20 batches × 50ms = 1 second!

print(f"Inserted {count} users")
```

**How batch_insert works:**

```sql
-- Instead of 500 individual INSERTs:
INSERT INTO users (name, email) VALUES ('User 1', 'user1@example.com');
INSERT INTO users (name, email) VALUES ('User 2', 'user2@example.com');
...

-- We do ONE INSERT with 500 rows:
INSERT INTO users (name, email) VALUES 
  ('User 1', 'user1@example.com'),
  ('User 2', 'user2@example.com'),
  ... (498 more rows) ...
;
```

### Adaptive Pool Scaling

The pool automatically adjusts to your traffic:

```
                    Adaptive Scaling Timeline
═══════════════════════════════════════════════════════════════════

Traffic:     Low ─────────► Peak ─────────► Low ─────────► Peak
             │               │               │               │
Pool size:   ▼               ▼               ▼               ▼
             5 → 5 → 5 → 10 → 25 → 50 → 50 → 30 → 10 → 5 → 10 → 40
                         ↑              ↑         ↑
                    Scale UP       Scale DOWN   Scale UP
                    (more requests) (idle timeout) (more requests)
```

```python
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    min_connections=5,
    max_connections=50,
    adaptive_scaling=True,  # Enable (default)
)

# Check scaling stats
stats = adapter.get_scaling_stats()
print(f"Current pool size: {stats.current_size}")
print(f"Recommended size: {stats.recommended_size}")
print(f"Scale events today: {stats.scale_event_count}")
```

---

## Phase 5.5: Observability

### Why Observability Matters

You can't fix what you can't see:

```
                    The Three Pillars of Observability
═══════════════════════════════════════════════════════════════════

1. LOGS           2. METRICS           3. TRACES
"What happened"   "How much/many"      "The journey"

Query X failed    Queries/sec: 1500    Request → Query 1
at 10:30:45       Avg latency: 12ms        → Query 2
Connection        Error rate: 0.1%          → Query 3
refused to        Pool usage: 75%           → Response
replica-2         Queue depth: 5
```

### Query Logging

```python
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    
    # Log ALL queries (very verbose, use for debugging only)
    log_queries=False,
    
    # Log slow queries (recommended for production)
    log_slow_queries=True,
    slow_query_threshold=1.0,  # Queries taking > 1 second
)
```

**Example log output:**

```
2024-01-15 10:30:45 INFO pynext.db: Query executed in 5ms: SELECT * FROM users LIMIT 10
2024-01-15 10:30:46 WARNING pynext.db: SLOW QUERY (1523ms): SELECT * FROM orders WHERE...
2024-01-15 10:30:47 ERROR pynext.db: Query failed: Connection refused
```

### Slow Query Detection

Find and fix slow queries before users complain:

```python
# Get recent slow queries
slow_queries = adapter.get_slow_queries(limit=10)

for query in slow_queries:
    print(f"═══════════════════════════════════════")
    print(f"Duration: {query.duration_ms}ms")
    print(f"SQL: {query.sql}")
    print(f"Executed at: {query.timestamp}")
    print(f"")
    
    # Get optimization suggestions
    for suggestion in query.suggestions:
        print(f"  💡 {suggestion}")
```

**Example output:**

```
═══════════════════════════════════════
Duration: 2345ms
SQL: SELECT * FROM orders WHERE user_id = 123 ORDER BY created_at
Executed at: 2024-01-15 10:30:45

  💡 Consider adding index: CREATE INDEX idx_orders_user_id ON orders(user_id)
  💡 Query scanned 1,234,567 rows, returned 50 rows
  💡 Consider adding WHERE clause to filter by date range
```

### Query Analysis

Analyze any query for optimization opportunities:

```python
# Analyze a specific query
suggestions = await adapter.analyze_query(
    "SELECT * FROM orders WHERE user_id = 123 AND status = 'pending'"
)

for s in suggestions:
    print(f"Type: {s.type}")           # e.g., "missing_index"
    print(f"Description: {s.description}")
    print(f"Suggested fix: {s.suggested_fix}")
    print(f"Estimated improvement: {s.estimated_improvement}")
    print()
```

### Metrics Collection

Track database performance over time:

```python
adapter = PostgresAdapter(
    url="postgresql://localhost/mydb",
    metrics=True,  # Enable metrics collection
)

# Get current metrics
metrics = adapter.get_metrics()

print(f"Queries per second: {metrics['queries_per_second']}")
print(f"Average latency: {metrics['avg_latency_ms']}ms")
print(f"P99 latency: {metrics['p99_latency_ms']}ms")
print(f"Error rate: {metrics['error_rate']:.2%}")
print(f"Pool utilization: {metrics['pool_utilization']:.1%}")
```

### Health Checks

Check if your database is healthy:

```python
# Perform health check
health = await adapter.health_check()

if health["is_healthy"]:
    print(f"✅ Database healthy")
    print(f"   Latency: {health['latency_ms']}ms")
    print(f"   Pool: {health['pool_status']}")
else:
    print(f"❌ Database unhealthy")
    print(f"   Reason: {health['reason']}")
    print(f"   Last error: {health['last_error']}")
```

**Use in your app's health endpoint:**

```python
@app.get("/health")
async def health_check():
    db_health = await adapter.health_check()
    
    if db_health["is_healthy"]:
        return {"status": "healthy", "database": db_health}
    else:
        return Response(
            {"status": "unhealthy", "database": db_health},
            status_code=503
        )
```

### Leak Detection

Find connections that are never returned to the pool:

```python
# Detect connection leaks
leaks = await adapter.detect_leaks()

if leaks:
    logger.error(f"⚠️ Connection leak detected!")
    for leak in leaks:
        logger.error(f"  Connection held for {leak.held_duration_ms}ms")
        logger.error(f"  Acquired at: {leak.acquired_at}")
        logger.error(f"  Stack trace: {leak.stack_trace}")
```

**Common causes of leaks:**
- Not using `await` on queries
- Not closing transactions
- Exceptions that skip cleanup code
- Missing `async with` blocks

---

## Phase 5.7: Advanced Queries

### Per-Query Timeouts

Prevent runaway queries from blocking your app:

```python
# ═══════════════════════════════════════════════════════════════
# CONTEXT MANAGER (Multiple queries share timeout)
# ═══════════════════════════════════════════════════════════════

async with adapter.timeout(10):  # 10 second timeout
    # All queries in this block share the 10s timeout
    users = await User.all()
    orders = await Order.all()
    stats = await Stats.get()

# If total time exceeds 10 seconds → QueryTimeoutError


# ═══════════════════════════════════════════════════════════════
# CHAIN METHOD (Single query)
# ═══════════════════════════════════════════════════════════════

# For Query builder objects
users = await User.select().timeout(5).all()


# ═══════════════════════════════════════════════════════════════
# HANDLING TIMEOUT ERRORS
# ═══════════════════════════════════════════════════════════════

from pynext.db import QueryTimeoutError

try:
    result = await slow_query()
except QueryTimeoutError as e:
    logger.warning(f"Query timed out after {e.duration_ms}ms")
    return cached_fallback_data()
```

### Query Explanation

Understand WHY a query is slow:

```python
# ═══════════════════════════════════════════════════════════════
# BASIC EXPLAIN (Shows plan, doesn't execute)
# ═══════════════════════════════════════════════════════════════

plan = await adapter.explain(
    "SELECT * FROM users WHERE email = 'test@example.com'"
)

print(f"Estimated cost: {plan.cost}")
print(f"Estimated rows: {plan.rows}")


# ═══════════════════════════════════════════════════════════════
# ANALYZE (Actually executes, shows real timing)
# ═══════════════════════════════════════════════════════════════

plan = await adapter.explain(
    "SELECT * FROM users WHERE email = 'test@example.com'",
    analyze=True,   # Actually run the query
    buffers=True,   # Include I/O statistics
)

print(f"Planning time: {plan.planning_time}ms")
print(f"Execution time: {plan.execution_time}ms")
print(f"Rows returned: {plan.actual_rows}")


# ═══════════════════════════════════════════════════════════════
# VISUAL TREE (ASCII representation)
# ═══════════════════════════════════════════════════════════════

print(plan.tree)

# Output:
# └── Seq Scan on users
#     (cost=0.00..1234.00 rows=1 width=100)
#     (actual time=0.015..45.123 rows=1 loops=1)
#     Filter: (email = 'test@example.com')
#     Rows Removed by Filter: 50000


# ═══════════════════════════════════════════════════════════════
# GET SUGGESTIONS
# ═══════════════════════════════════════════════════════════════

for suggestion in plan.suggestions:
    print(f"[{suggestion.severity}] {suggestion.title}")
    print(f"  {suggestion.description}")
    if suggestion.sql:
        print(f"  Fix: {suggestion.sql}")

# Output:
# [WARNING] Sequential scan on large table
#   Table 'users' has 50,000 rows but no index was used
#   Fix: CREATE INDEX idx_users_email ON users(email)
```

### Pagination

Handle large result sets efficiently:

```python
# ═══════════════════════════════════════════════════════════════
# SMART PAGINATION (Auto-selects best method)
# ═══════════════════════════════════════════════════════════════

# First page
page = await adapter.paginate(
    "SELECT * FROM products ORDER BY id",
    page_size=20,
)

print(f"Items: {len(page.items)}")      # 20
print(f"Has more: {page.has_more}")      # True
print(f"Next cursor: {page.next_cursor}")  # "eyJpZCI6MjB9..."

# Next page (pass the cursor from previous page)
page2 = await adapter.paginate(
    "SELECT * FROM products ORDER BY id",
    page_size=20,
    cursor=page.next_cursor,
)


# ═══════════════════════════════════════════════════════════════
# UNDERSTANDING PAGINATION METHODS
# ═══════════════════════════════════════════════════════════════

# OFFSET PAGINATION (Traditional)
# SQL: SELECT * FROM products LIMIT 20 OFFSET 1000
# Problem: Database must scan 1020 rows to return 20
# Performance: O(n) - gets slower as you go deeper

# KEYSET PAGINATION (Cursor-based)
# SQL: SELECT * FROM products WHERE id > 1000 LIMIT 20
# Benefit: Database jumps directly to id > 1000
# Performance: O(1) - always fast, even on page 50,000

# SMART PAGINATION (PyNext default)
# Automatically uses:
# - Keyset for: Large tables, indexed ORDER BY columns
# - Offset for: Small tables (<10k rows), need page numbers
```

### Prepared Statements

Speed up repeated queries:

```python
# ═══════════════════════════════════════════════════════════════
# HOW PREPARED STATEMENTS WORK
# ═══════════════════════════════════════════════════════════════

# Regular query (every time):
# 1. Parse SQL → 2. Plan query → 3. Execute → 4. Return
# Time: 1ms + 2ms + 5ms = 8ms

# Prepared statement:
# First call: 1. Parse SQL → 2. Plan query → 3. Save plan
# Future calls: 1. Get saved plan → 2. Execute → 3. Return
# Time: 0ms + 0ms + 5ms = 5ms (37% faster!)


# ═══════════════════════════════════════════════════════════════
# USING PREPARED STATEMENTS
# ═══════════════════════════════════════════════════════════════

# Prepare once (at app startup or first use)
stmt = await adapter.prepare(
    "get_user_by_id",                          # Name
    "SELECT * FROM users WHERE id = $1",        # SQL with placeholders
    types=[int],                                # Parameter types
)

# Execute many times (much faster after first call)
user1 = await stmt.fetchone(1)
user2 = await stmt.fetchone(2)
user3 = await stmt.fetchone(3)

# Check performance
stats = adapter.get_prepared_stats()
for name, stat in stats.items():
    print(f"{name}:")
    print(f"  Calls: {stat.call_count}")
    print(f"  Avg time: {stat.avg_time_ms:.2f}ms")
    print(f"  Total time saved: {stat.time_saved_ms:.0f}ms")


# ═══════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════

# Remove a specific prepared statement
await adapter.unprepare("get_user_by_id")

# Remove all (e.g., before schema migration)
await adapter.unprepare_all()
```

### Query Cancellation

Cancel queries when users navigate away:

```python
# ═══════════════════════════════════════════════════════════════
# THE PROBLEM
# ═══════════════════════════════════════════════════════════════

# User clicks "Load Report" (starts 10-second query)
# User immediately clicks "Cancel" or navigates away
# 
# WITHOUT cancellation:
#   - Query runs for 10 seconds anyway
#   - Database resources wasted
#   - Result thrown away
#
# WITH cancellation:
#   - Query cancelled immediately
#   - Database resources freed
#   - Server handles next request faster


# ═══════════════════════════════════════════════════════════════
# USING QUERY TRACKING
# ═══════════════════════════════════════════════════════════════

# In your request handler, track queries
async with adapter.track_query(request_id="req_12345") as tracker:
    # All queries here are associated with this request
    users = await User.all()
    orders = await Order.all()

# When user disconnects (in your framework's disconnect handler)
@app.on_disconnect
async def handle_disconnect(request):
    count = await adapter.cancel_queries(request.id)
    logger.info(f"Cancelled {count} queries for disconnected client")


# ═══════════════════════════════════════════════════════════════
# VIEWING AND CANCELLING QUERIES
# ═══════════════════════════════════════════════════════════════

# See what's running right now
for query in adapter.get_running_queries():
    print(f"ID: {query.id}")
    print(f"Running for: {query.duration_ms}ms")
    print(f"SQL: {query.query[:100]}...")
    print(f"Request: {query.request_id}")
    print()

# Cancel a specific long-running query
await adapter.cancel("query_id_here")
```

---

## Configuration Reference

### Complete Configuration Example

```python
from pynext.db import PostgresAdapter
from pynext.db.adapters import (
    QueueConfig,
    LifecycleConfig,
    ExternalPoolerConfig,
    PoolerMode,
)

adapter = PostgresAdapter(
    # ═══════════════════════════════════════════════════════════
    # CONNECTION (pick URL or individual params)
    # ═══════════════════════════════════════════════════════════
    url="postgresql://user:pass@localhost:5432/mydb",
    # OR:
    # host="localhost",
    # port=5432,
    # database="mydb",
    # user="postgres",
    # password="secret",
    # ssl=True,
    
    
    # ═══════════════════════════════════════════════════════════
    # POOL (Phase 5.1 & 5.2)
    # ═══════════════════════════════════════════════════════════
    min_connections=5,         # Minimum pool size
    max_connections=50,        # Maximum pool size
    auto_scale=True,           # Auto-adjust pool size
    
    idle_timeout=300.0,        # Close idle connections after 5 min
    max_lifetime=3600.0,       # Replace connections after 1 hour
    acquire_timeout=30.0,      # Wait for connection timeout
    connect_timeout=10.0,      # Connection establishment timeout
    command_timeout=None,      # Query timeout (None = no limit)
    
    statement_cache_size=1000, # Prepared statement cache size
    
    warmup=True,               # Warmup new connections
    warmup_query="SELECT 1",   # Warmup query
    
    
    # ═══════════════════════════════════════════════════════════
    # RELIABILITY (Phase 5.3)
    # ═══════════════════════════════════════════════════════════
    retry=True,                     # Auto-retry failed queries
    retry_attempts=3,               # Max retry attempts
    
    circuit_breaker=True,           # Enable circuit breaker
    circuit_breaker_threshold=5,    # Failures before opening
    
    replicas=[                      # Read replica URLs
        "postgresql://replica1/mydb",
        "postgresql://replica2/mydb",
    ],
    
    
    # ═══════════════════════════════════════════════════════════
    # HIGH-LOAD OPTIMIZATION (Phase 5.4)
    # ═══════════════════════════════════════════════════════════
    query_coalescing=True,     # Dedupe identical queries
    query_batching=True,       # Auto-batch operations
    adaptive_scaling=True,     # Auto-scale pool size
    
    
    # ═══════════════════════════════════════════════════════════
    # OBSERVABILITY (Phase 5.5)
    # ═══════════════════════════════════════════════════════════
    log_queries=False,         # Log all queries (verbose!)
    log_slow_queries=True,     # Log slow queries
    slow_query_threshold=1.0,  # Slow query threshold (seconds)
    metrics=True,              # Enable metrics collection
    
    
    # ═══════════════════════════════════════════════════════════
    # ADVANCED QUERIES (Phase 5.7)
    # ═══════════════════════════════════════════════════════════
    prepared_cache_size=1000,  # Prepared statement cache
    cancel_on_disconnect=True, # Cancel queries on disconnect
)
```

### Environment Variables

```bash
# Connection
DATABASE_URL=postgresql://user:pass@localhost/mydb

# Pool
PYNEXT_DB_MIN_CONNECTIONS=5
PYNEXT_DB_MAX_CONNECTIONS=50
PYNEXT_DB_ACQUIRE_TIMEOUT=30

# Reliability
PYNEXT_DB_RETRY_ATTEMPTS=3
PYNEXT_DB_CIRCUIT_BREAKER_THRESHOLD=5

# Observability
PYNEXT_DB_LOG_QUERIES=false
PYNEXT_DB_LOG_SLOW_QUERIES=true
PYNEXT_DB_SLOW_QUERY_THRESHOLD=1.0
PYNEXT_DB_METRICS=true
```

---

## Troubleshooting

### Connection Errors

**Problem: `ConnectionRefusedError`**

```python
# Causes:
# 1. PostgreSQL not running
# 2. Wrong host/port
# 3. Firewall blocking

# Solutions:
# 1. Check PostgreSQL is running:
#    pg_isready -h localhost -p 5432

# 2. Verify connection details:
adapter = PostgresAdapter(
    host="localhost",  # Is this correct?
    port=5432,         # Is PostgreSQL on this port?
    database="mydb",   # Does this database exist?
)
```

**Problem: `TimeoutError` on connect**

```python
# Cause: Network latency or slow server

# Solution: Increase timeout
adapter = PostgresAdapter(
    url="postgresql://remote-server/mydb",
    connect_timeout=30.0,  # Default is 10s
)
```

**Problem: `AuthenticationError`**

```python
# Causes:
# 1. Wrong username/password
# 2. User doesn't have access to database
# 3. pg_hba.conf blocking connection

# Solutions:
# 1. Verify credentials
# 2. Check PostgreSQL logs for details
# 3. Check pg_hba.conf allows your connection method
```

### Pool Exhaustion

**Problem: "Cannot acquire connection within timeout"**

```python
# Causes:
# 1. Too many concurrent requests
# 2. Slow queries holding connections
# 3. Connection leaks

# Solutions:

# 1. Increase pool size
adapter = PostgresAdapter(
    url="...",
    max_connections=100,  # Increase from default 10
)

# 2. Check for slow queries
for q in adapter.get_slow_queries():
    print(f"{q.duration_ms}ms: {q.sql}")

# 3. Check for leaks
leaks = await adapter.detect_leaks()
if leaks:
    for leak in leaks:
        print(f"Leak: {leak.stack_trace}")

# 4. Add timeout to prevent infinite waits
adapter = PostgresAdapter(
    url="...",
    command_timeout=30.0,  # Kill queries after 30s
)
```

### Slow Queries

**Problem: Queries taking too long**

```python
# Step 1: Find slow queries
for q in adapter.get_slow_queries(limit=5):
    print(f"{q.duration_ms}ms: {q.sql[:100]}")

# Step 2: Analyze the problematic query
suggestions = await adapter.analyze_query(slow_sql)
for s in suggestions:
    print(s.description)

# Step 3: Get execution plan
plan = await adapter.explain(slow_sql, analyze=True)
print(plan.tree)

# Common fixes:
# - Add missing indexes
# - Reduce result set with LIMIT
# - Add WHERE clauses
# - Denormalize frequently-joined tables
```

### Circuit Breaker Issues

**Problem: Circuit breaker keeps opening**

```python
# Check why it's opening
stats = adapter.get_retry_stats()
print(f"Recent errors: {stats.recent_errors}")

# Check what's failing
for error in stats.recent_errors:
    print(f"  {error.type}: {error.message}")

# After fixing the underlying issue, reset
adapter.reset_circuit()

# If it's too sensitive, increase threshold
adapter = PostgresAdapter(
    url="...",
    circuit_breaker_threshold=10,  # Default is 5
)
```

---

## Summary

The PyNext PostgreSQL Adapter is designed around these principles:

1. **Just Works** - One line gets you a production-ready setup
2. **Progressive Disclosure** - Simple defaults, advanced options when needed
3. **Observable** - Know what's happening inside
4. **Resilient** - Handles failures gracefully
5. **Fast** - Optimized for high throughput

| What You Need | What To Do |
|---------------|------------|
| Quick start | `PostgresAdapter(url)` |
| More connections | Add `max_connections=50` |
| Handle failures | Already enabled (retry, circuit breaker) |
| Speed up reads | Add `replicas=[...]` |
| Monitor performance | Add `metrics=True` |
| Debug slow queries | Check `get_slow_queries()` |
| Scale for traffic | Already enabled (coalescing, scaling) |

Everything is designed so you can start simple and add complexity only when needed.
