# PyNext Roadmap

This document tracks future enhancements and features for PyNext, and articulates the comprehensive vision for what we're building.

---

## The Vision: What We're Building

### The Problem

Modern web development is **unnecessarily complex**. To build a production web app today, developers must:

1. **Learn JavaScript/TypeScript** - Even for simple apps
2. **Master React's mental model** - Hooks, re-renders, stale closures, dependency arrays
3. **Choose from 100+ packages** - State management, routing, forms, auth, ORM, testing...
4. **Configure build tools** - Webpack, Babel, ESLint, TypeScript, Tailwind...
5. **Understand web concepts** - CSR, SSR, SSG, ISR, RSC, hydration, streaming...
6. **Fight the framework** - Workarounds for simple things (why can't I just call a Python function?)

**The result**: A "simple" blog requires 50+ npm packages, 10+ config files, and 1000+ lines of boilerplate.

### The Solution: PyNext

**PyNext is a full-stack Python framework that makes web development as simple as writing Python.**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PYNEXT VISION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Write Python → Get a Fast, Modern Web App → Deploy Anywhere                │
│                                                                              │
│  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐  │
│  │    Your Code     │      │   PyNext Magic    │      │    Production    │  │
│  │                  │      │                  │      │                  │  │
│  │  • Pure Python   │  →   │  • Compiles to   │  →   │  • <10KB JS      │  │
│  │  • Type hints    │      │    optimized JS  │      │  • <500ms TTI    │  │
│  │  • No React      │      │  • Auto-hydrates │      │  • SEO perfect   │  │
│  │  • No npm        │      │  • Smart caching │      │  • Works offline │  │
│  └──────────────────┘      └──────────────────┘      └──────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Core Principles

| Principle | What It Means | Why It Matters |
|-----------|---------------|----------------|
| **Python-First** | Write Python, not JavaScript | Backend devs don't need to learn new languages |
| **SolidJS Reactivity** | Fine-grained updates, not virtual DOM | 10x smaller bundles, 3x faster updates |
| **Zero Config** | Works out of the box | Ship features, not webpack configs |
| **Full-Stack** | UI + API + Database + Auth in one | No glue code between 5 frameworks |
| **AI-Friendly** | Simple, explicit code | LLMs can understand and extend your app |
| **Production-Ready** | Battle-tested patterns built-in | Security, caching, scaling by default |

---

## PyNext vs The Competition

### Framework Comparison

| Capability | Next.js | Django | FastAPI | Flask | **PyNext** |
|------------|---------|--------|---------|-------|------------|
| Language | JS/TS | Python | Python | Python | **Python** |
| Reactivity | Virtual DOM | None | None | None | **Fine-grained (SolidJS)** |
| Bundle Size | ~80KB | N/A | N/A | N/A | **<10KB** |
| TTI | ~1.5s | N/A | N/A | N/A | **<500ms** |
| Server Actions | ✅ | ❌ | ❌ | ❌ | **✅** |
| Built-in ORM | ❌ (Prisma) | ✅ | ❌ | ❌ | **✅** |
| Built-in Auth | ❌ (NextAuth) | ✅ | ❌ | ❌ | **✅** |
| Type Safety | TS required | Optional | ✅ | ❌ | **✅** |
| Hot Reload | ~300ms | ~2s | ~1s | ~1s | **<50ms** |
| Learning Curve | Steep | Moderate | Easy | Easy | **Easy** |

### Lines of Code Comparison

| Task | Next.js + React | Django | **PyNext** |
|------|-----------------|--------|------------|
| Hello World | 15 | 20 | **5** |
| Todo App | 150 | 200 | **50** |
| Blog with Auth | 500 | 400 | **150** |
| E-commerce (basic) | 2000+ | 1500+ | **500** |
| Full SaaS | 10000+ | 8000+ | **3000** |

### Why We're Faster Than Next.js

```
Next.js Request Flow (Complex):
┌──────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│Client│ →  │ Webpack │ →  │  React   │ →  │ Virtual │ →  │   DOM    │
│      │    │ Bundle  │    │ Runtime  │    │   DOM   │    │ Updates  │
└──────┘    └─────────┘    └──────────┘    └─────────┘    └──────────┘
            (80KB+)        (40KB+)         (Diffing)      (Batch)

PyNext Request Flow (Simple):
┌──────┐    ┌─────────┐    ┌──────────┐
│Client│ →  │ Minimal │ →  │  Direct  │
│      │    │ Runtime │    │   DOM    │
└──────┘    └─────────┘    └──────────┘
            (<10KB)        (No diffing)
```

**Why PyNext is faster:**

1. **No Virtual DOM** - SolidJS compiles to direct DOM updates
2. **Fine-grained reactivity** - Only changed nodes update, not entire component trees
3. **Smaller bundles** - No React, no reconciler, no scheduler
4. **Server-first** - Most code runs on server, minimal client JS
5. **Smart hydration** - Only hydrate interactive parts (Islands)

---

## Performance Benchmarks (Targets)

### JavaScript Bundle Size

| App Type | Next.js | PyNext | Reduction |
|----------|---------|--------|-----------|
| Hello World | 80KB | **8KB** | **90%** |
| Blog | 150KB | **15KB** | **90%** |
| Dashboard | 300KB | **30KB** | **90%** |
| E-commerce | 500KB | **50KB** | **90%** |

### Time to Interactive (TTI)

| Network | Next.js | PyNext | Improvement |
|---------|---------|--------|-------------|
| Fast 3G | 2.5s | **0.8s** | **3x faster** |
| 4G | 1.5s | **0.5s** | **3x faster** |
| WiFi | 0.8s | **0.3s** | **2.5x faster** |

### Server Response Time

| Operation | Next.js | PyNext | Improvement |
|-----------|---------|--------|-------------|
| Static page | 50ms | **20ms** | **2.5x faster** |
| SSR page | 200ms | **80ms** | **2.5x faster** |
| API route | 100ms | **40ms** | **2.5x faster** |
| Database query | 150ms | **60ms** | **2.5x faster** |

### Developer Experience

| Metric | Next.js | PyNext | Improvement |
|--------|---------|--------|-------------|
| Hot reload | 300ms | **<50ms** | **6x faster** |
| Build time | 30s | **<10s** | **3x faster** |
| Cold start | 5s | **<2s** | **2.5x faster** |
| Config files | 10+ | **1** | **10x simpler** |

---

## What Makes PyNext Special

### 1. Python All The Way Down

```python
# Next.js: Learn JSX, hooks, TypeScript, npm, webpack...
# PyNext: Just write Python

def HomePage():
    count = Signal(0)
    return div(
        h1(f"Count: {count()}"),
        button("+", on_click=lambda: count.set(count() + 1))
    )
```

### 2. SolidJS Reactivity (Not React)

```python
# React: Re-renders entire component tree
# SolidJS/PyNext: Only updates the exact DOM node that changed

name = Signal("Alice")
# When name changes, ONLY the text node updates
# Not the div, not the parent, not siblings
h1(f"Hello, {name()}")  
```

### 3. Built-in Everything

```python
# Next.js: Install NextAuth + Prisma + TanStack Query + Zod + ...
# PyNext: It's all included

from pynext.auth import Auth, login_required
from pynext.db import Table, db

Auth.setup(secret="...")  # Auth done
db.configure("postgres://...")  # Database done

class User(Table):
    name: str
    email: str  # Validation done
```

### 4. AI-Friendly Code

PyNext is designed for the AI era. Simple, explicit code that LLMs can:
- **Understand** - No magic, no hidden state
- **Generate** - Consistent patterns, clear APIs
- **Debug** - Explicit error messages, stack traces
- **Extend** - Modular design, composable pieces

---

## Future Enhancements

### Next.js Feature Parity

Achieving complete feature parity with Next.js while maintaining SolidJS principles (fine-grained reactivity, zero unnecessary JS, build-time optimization).

**Already Implemented**: `loading.py`, `error.py`, `not-found.py`, `layout.py`, `page.py`, `route.py`, dynamic routes, parallel routes, intercepting routes, `@island`, `Link()`, server actions, ISR, streaming, middleware, `Image()`, `Font()`, `Metadata` API, Tailwind utilities


#### Performance Targets

| Metric | Next.js | PyNext Target |
|--------|---------|---------------|
| JS Bundle (hello world) | ~80KB | <10KB |
| TTI | ~1.5s | <500ms |
| Build time | ~30s | <10s |
| Dev reload | ~300ms | <50ms |

#### Summary

| Phase | Features | Status | Tests |
|-------|----------|--------|-------|
| 1 | File conventions (Route Groups, Template, Error Pages, src/) | ✅ Complete | 192 |
| 2 | Environment Variables + Route Segment Config | ✅ Complete | 187 |
| 3 | SEO & assets (Sitemap, Robots, PWA, OG Images) | ✅ Complete | 220 |
| 4 | Developer experience (Dev Server, Generator, Testing, Linting) | ✅ Complete | 480 |
| 5 | Browser APIs (WebSocket, Geolocation, Visibility, etc.) | ✅ Complete | 328 |
| 6 | Advanced (CSS Modules, MDX, Proxy, Instrumentation, Edge) | ✅ Complete | 541 |

**Completed**: All 6 Phases with 1,948+ tests
**Total Test Suite**: 6,319 tests
**Status**: Next.js Feature Parity Achieved 🎉

---

### Data Layer (Full-Stack ORM)

A complete database integration that makes PyNext a true full-stack framework with the simplest possible API.

#### Problem Statement

Currently, PyNext handles UI beautifully but has no built-in database story. Developers must:
- Manually set up SQLAlchemy/Alembic
- Write boilerplate for connections, sessions, migrations
- Manually sync frontend state when data changes
- Handle loading/error states for every query
- Manage cache invalidation themselves

**Goal**: Make database work as simple as the rest of PyNext - just Python, no ceremony.

#### Design Philosophy

| Principle | Why | How |
|-----------|-----|-----|
| **Pure Python** | Python devs shouldn't learn web concepts | No hooks, no reducers, just method calls |
| **Type-first** | Modern Python uses type hints | Classes with annotations, that's it |
| **Simple by default** | 80% of queries are simple CRUD | One-liners: `User.get(1)`, `user.save()` |
| **Powerful when needed** | Complex queries happen | Chainable: `.where().order_by().limit()` |
| **Reactive automatically** | UI should stay in sync | `.live()` queries auto-update the frontend |
| **Escape hatches** | ORMs can't do everything | Raw SQL always available |

#### Why This Approach (vs Alternatives)

| Alternative | Problem | Our Solution |
|-------------|---------|--------------|
| **SQLAlchemy** | Verbose, Django-era API | Pure type hints, no `Column()` |
| **Django ORM** | Requires Django, not async | Async-first, standalone |
| **Prisma** | TypeScript-only | Native Python with same DX |
| **React Query** | Complex hooks, JS concepts | `.live()` - just works |
| **Apollo Client** | GraphQL overhead, complex | Direct model methods |

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ User.live() │    │ Signal("")  │    │ Computed(lambda: )  │  │
│  │ (server)    │    │ (UI state)  │    │ (derived)           │  │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘  │
│         │                  │                      │              │
│         └──────────────────┼──────────────────────┘              │
│                            │                                     │
│                    ┌───────▼───────┐                            │
│                    │   Component   │                            │
│                    └───────┬───────┘                            │
└────────────────────────────┼────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Server Action  │  ← User.insert(), user.update()
                    └────────┬────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                         BACKEND                                  │
│                    ┌───────▼───────┐                            │
│                    │  pynext.db    │                            │
│                    │  ┌─────────┐  │                            │
│                    │  │  Table  │  │  ← Model base class        │
│                    │  └────┬────┘  │                            │
│                    │       │       │                            │
│                    │  ┌────▼────┐  │                            │
│                    │  │ Query   │  │  ← Chainable builder       │
│                    │  └────┬────┘  │                            │
│                    │       │       │                            │
│                    │  ┌────▼────┐  │                            │
│                    │  │Adapter  │  │  ← PostgreSQL/Supabase     │
│                    │  └────┬────┘  │                            │
│                    └───────┼───────┘                            │
└────────────────────────────┼────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │    Database     │  ← PostgreSQL / Supabase
                    └─────────────────┘
```

#### State Management Strategy

PyNext separates state into two types that compose naturally:

| State Type | What | How | Example |
|------------|------|-----|---------|
| **Server State** | Database data | `.live()` - automatic | `users = User.live()` |
| **UI State** | Local interactions | `Signal()` - explicit | `search = Signal("")` |
| **Derived State** | Computed from both | `Computed()` | `filtered = Computed(...)` |

This eliminates the need for:
- Redux/Zustand for server data
- React Query/SWR hooks
- Manual cache invalidation
- Loading/error state boilerplate

---

#### Implementation Phases

##### Phase 1: Core Model System ✅ Complete (634 tests)
- [x] `Table` base class with type hint parsing
- [x] Auto-generate `id`, `created_at`, `updated_at` fields
- [x] Foreign key detection from `*_id` naming
- [x] Full relationship inference with eager loading (`.with_related()`)
- [x] Full Pydantic-style validation with error messages
- [x] MockAdapter (dict-based) for instant testing
- [x] MemoryAdapter (SQLite) for SQL testing
- [x] Chainable query builder with all filter types
- [x] Documentation: `docs/database/01-fundamentals.md`

##### Phase 2: CRUD Operations ✅ Complete (483 tests)
- [x] **Simple Methods** — One-liners for common operations
  ```python
  user = await User.insert(name="John", email="j@example.com")
  user = await User.get(1)
  users = await User.select()
  await user.update(name="Jane")
  await user.delete()
  ```

- [x] **Batch Operations** — Efficient multi-record operations
  ```python
  users = await User.insert_many([{"name": "A"}, {"name": "B"}])
  count = await User.update_many(where={"role": "user"}, set={"active": True})
  count = await User.delete_many(where={"active": False})
  user = await User.upsert(where={"email": "..."}, create={...}, update={...})
  ```

- [x] **Query Execution Methods** — Aggregation and values
  ```python
  user = await User.select().first()
  user = await User.select().one()  # Raises if not found
  total = await User.select().sum("balance")
  avg = await User.select().avg("age")
  roles = await User.select().distinct("role")
  ```

##### Phase 3: Raw SQL Escape Hatch ✅ Complete (517 tests)
- [x] **Direct SQL** — When ORM isn't enough
  ```python
  from pynext.db import db
  
  # Simple query
  users = await db.sql("SELECT * FROM users WHERE role = $1", "admin")
  
  # With model mapping
  users = await db.sql("SELECT * FROM users WHERE role = $1", "admin", model=User)
  
  # Single row/value
  user = await db.sql_one("SELECT * FROM users WHERE id = $1", 1)
  count = await db.sql_val("SELECT COUNT(*) FROM users")
  
  # Execute (insert/update/delete)
  await db.execute("UPDATE users SET active = true WHERE last_login > $1", date)
  ```

- [x] **Transactions** — ACID-compliant with savepoints
  ```python
  async with db.transaction():
      await User.insert(name="John")
      await Post.insert(title="Hello")
  # Both succeed or both fail
  
  # With savepoints for partial rollback
  async with db.transaction() as tx:
      await User.insert(name="Safe")
      async with tx.savepoint():
          await Post.insert(title="Risky")  # Can rollback just this
  ```

- [x] **Type-Safe SQL Builder** — Build complex SQL safely
  ```python
  from pynext.db import sql
  
  users = await (
      sql.select("users.name", "posts.title")
      .from_("users")
      .join("posts", "users.id", "=", "posts.author_id")
      .where("role", "=", "admin")
      .order_by("created_at", "DESC")
      .limit(10)
      .execute()
  )
  ```

##### Phase 4: Migrations (Alembic Integration) ✅

**Status:** Complete (500 tests, 500 passing, comprehensive docs complete)

- [x] `pynext db init` — Initialize migrations folder
- [x] `pynext db migrate -m "message"` — Auto-generate from model changes
- [x] `pynext db upgrade` — Apply pending migrations
- [x] `pynext db downgrade` — Rollback last migration
- [x] `pynext db history` — Show migration history

**Features Implemented:**
- **Smart Change Detection**: Auto-detect new tables, columns, types, indexes
- **Interactive Prompts**: "Did you rename 'name' to 'full_name'?" for ambiguous changes
- **Declarative Format**: Simple dict-based migrations for 90% of use cases
- **Python Format**: Full async Python for complex data migrations
- **Preview Mode**: `--sql` flag to see exact SQL before applying
- **Rollback Support**: Single, multiple, or to-version rollback

**Documentation:** [03-migrations.md](./database/03-migrations.md)

##### Phase 5: Database Adapters (PostgreSQL & Supabase)

**Status:** Phases 5.1-5.6 Complete ✅ (2,808 tests), Phase 5.7 Planned

**Design Philosophy:**
- PyNext > asyncpg: Simpler API, same performance
- Zero Config: Works out of the box with sensible defaults
- Production Ready: Circuit breakers, retries, health checks built-in
- Supabase Native: First-class citizen, not an afterthought
- Hyper-Efficient: Connection reuse, prepared statements, minimal overhead

**5.1 PostgreSQL Core Adapter:** ✅ Complete (233 tests)
- [x] `pynext/db/adapters/postgres.py` - asyncpg-based adapter
- [x] `pynext/db/adapters/postgres_url.py` - URL parsing with keyword overrides
- [x] `pynext/db/adapters/postgres_pool.py` - Auto-scaling connection pool
- [x] `pynext/db/adapters/postgres_cache.py` - LRU statement cache
- [x] `pynext/db/adapters/postgres_types.py` - Python ↔ PostgreSQL type conversion
- [x] Connection URL and individual param configuration
- [x] Statement caching for performance (LRU cache, configurable size)
- [x] Binary protocol for maximum throughput
- [x] Full transaction support with savepoints
- [x] Documentation: [02-getting-started.md](./database/02-getting-started.md)

**5.2 Connection Pooling (High-Performance):** ✅ Complete (500 tests)
- [x] Built-in asyncpg pool with intelligent sizing
  - Auto-scale: min_size=5, max_size=100 (configurable)
  - Idle connection recycling (prevent stale connections)
  - Connection warmup on startup
- [x] External pooler support (PgBouncer, pgpool)
  - Transaction pooling mode (recommended for high concurrency)
  - Session pooling mode (for prepared statements)
  - Auto-detection of external poolers
- [x] Pool overflow handling with queuing
  - Max wait time before rejection
  - Queue depth monitoring with backpressure
  - Priority queue support (CRITICAL → BATCH)
- [x] Connection lifecycle management
  - Soft/hard lifetime limits
  - Use-count based retirement
  - Graceful replacement strategy
  - Health check validation
- [x] Documentation: [05-connection-pooling.md](./database/05-connection-pooling.md)

**5.3 Production Reliability: ✅ Complete (502 tests)**
- [x] Retry with exponential backoff (configurable delays, max 30s)
  - Exponential, linear, and fixed backoff strategies
  - Jitter for thundering herd prevention
  - Automatic retryable error detection
  - Custom retry logic support
  - Convenience configs: `quick_retry()`, `standard_retry()`, `aggressive_retry()`
- [x] Circuit breaker (failure threshold, recovery timeout)
  - Three states: CLOSED, OPEN, HALF_OPEN
  - Global, per-connection, and per-query-type scopes
  - Rate-based and count-based thresholds
  - Automatic recovery probing
  - Excluded errors support
- [x] Read replica routing with weighted distribution
  - Multiple replicas with custom weights
  - Replication lag detection and automatic exclusion
  - Automatic failover and recovery
  - Health check validation
  - Multiple routing strategies
- [x] Graceful degradation under load
  - Four levels: NORMAL, DEGRADED, CRITICAL, EMERGENCY
  - Configurable triggers (queue depth, error rate, latency, pool utilization)
  - Configurable actions (logging, load shedding, notifications)
  - Auto-recovery with debouncing
- [x] Documentation: [06-reliability.md](./database/06-reliability.md)

**5.4 High-Load Scalability: ✅ Complete (373 tests)**
- [x] Per-query timeouts with intelligent routing
  - Per-type timeouts (SELECT, INSERT, UPDATE, DELETE)
  - Per-table timeouts for specific tables
  - Pattern-based timeouts with regex matching
  - Priority ordering: pattern → table → type → default
- [x] Query caching with smart invalidation
  - TTL-based expiration with configurable TTL
  - Smart (tag-based) invalidation for tables
  - Pattern-based invalidation with glob matching
  - LRU eviction with configurable max size
  - Cache warming support
- [x] Query coalescing (deduplication)
  - Identical query deduplication within window
  - Configurable coalescing window (default 5ms)
  - Result broadcasting to all waiters
  - Error broadcasting on failures
  - Max waiters limit to prevent memory exhaustion
- [x] Query pipelining for batch throughput
  - Automatic batching by size and time
  - Configurable max batch size and wait time
  - Manual flush support
  - Batch execution statistics
- [x] Batch optimization for INSERT/UPDATE/UPSERT
  - Efficient multi-row INSERT with parameter batching
  - UPSERT with ON CONFLICT support
  - Automatic chunking respecting PostgreSQL limits
  - Partial failure handling
- [x] Adaptive scaling with predictive load management
  - Load recording and trend analysis
  - Predictive pool size recommendations
  - Auto-scaling with configurable cooldown
  - Scale event tracking and statistics
- [x] Documentation: [07-high-load.md](./database/07-high-load.md)

**5.5 Error Logging & Debugging:** ✅ COMPLETE (600 tests)
- [x] Structured logging with context
  ```python
  {
    "level": "ERROR",
    "query_id": "abc123",
    "query": "SELECT * FROM users WHERE...",
    "duration_ms": 5234,
    "pool_stats": {"active": 95, "idle": 5, "waiting": 150},
    "error": "connection_timeout",
    "client_ip": "10.0.0.1",
    "trace_id": "xyz789"
  }
  ```
- [x] Slow query logging (configurable threshold)
- [x] Query explain on timeout (auto-analyze slow queries)
- [x] Pool exhaustion warnings (before failure)
- [x] Connection leak detection
- [x] Dead connection detection and cleanup
- [x] Metrics export (Prometheus/OpenTelemetry)
  - `pynext_db_connections_active`
  - `pynext_db_connections_waiting`
  - `pynext_db_query_duration_seconds`
  - `pynext_db_pool_exhausted_total`
  - `pynext_db_errors_total{type="timeout|connection|query"}`
- [x] Documentation: [08-observability.md](./database/08-observability.md)

**5.6 Supabase Full Integration:** ✅ Complete (600 tests)
- [x] `pynext/db/supabase/adapter.py` - SupabaseConfig, Supabase main class
- [x] `pynext/db/supabase/auth.py` - sign_up, sign_in, sign_out, OAuth, sessions
- [x] `pynext/db/supabase/storage.py` - upload, download, delete, signed URLs, buckets
- [x] `pynext/db/supabase/realtime.py` - decorators (@on_insert, @on_update, etc.) + signals
- [x] `pynext/db/supabase/functions.py` - invoke edge functions with retry
- [x] `pynext/db/supabase/rls.py` - @policy decorator, migration gen, sync
- [x] `pynext/db/supabase/exceptions.py` - SupabaseError hierarchy
- [x] Documentation: [10-supabase.md](./database/10-supabase.md)

**5.7 Advanced Query Features:** ✅ (391 tests)
- [x] Per-query `.timeout(seconds)` with statement_timeout (chain + context manager)
- [x] `.explain()` and `.analyze()` for query plans with ASCII tree + suggestions
- [x] Cursor-based pagination (keyset, offset, smart auto-select)
- [x] Prepared statement support with LRU cache + auto-invalidation
- [x] Query cancellation with tracking and disconnect handling
- [x] `pynext/db/adapters/postgres_query_timeout.py` - Chain + context manager APIs
- [x] `pynext/db/adapters/postgres_explain.py` - Parsed output, tree, suggestions
- [x] `pynext/db/adapters/postgres_pagination.py` - Keyset, offset, smart mode
- [x] `pynext/db/adapters/postgres_prepared.py` - Cache + auto-invalidation
- [x] `pynext/db/adapters/postgres_cancel.py` - Tracking + disconnect handling
- [x] Documentation: [09-advanced-queries.md](./database/09-advanced-queries.md)

**PostgreSQL Adapter Integration:** ✅ All Phases Unified
- [x] All Phase 5.1-5.7 features integrated into single `PostgresAdapter` class
- [x] Python-first API with sensible defaults (just works out of the box)
- [x] Progressive disclosure: simple toggles for common needs, full config for power users
- [x] Comprehensive documentation: [04-postgres-adapter.md](./database/04-postgres-adapter.md)

**Configuration Example:**
```python
from pynext.db import configure, PostgresAdapter
from pynext.db.pool import Pool
from pynext.db.reliability import CircuitBreaker, RetryPolicy

configure(
    adapter=PostgresAdapter(
        url="postgresql://user:pass@localhost/db",
        
        # High-performance pooling
        pool=Pool(
            min_size=10,
            max_size=100,
            max_idle_time=300,
            max_queries=50000,
            max_lifetime=3600,
            overflow_max_wait=30,
        ),
        
        # Statement caching
        statement_cache_size=1000,
        
        # Reliability
        retry=RetryPolicy(max_attempts=3, backoff="exponential"),
        circuit_breaker=CircuitBreaker(failure_threshold=10),
        
        # Logging & debugging
        log_queries=True,
        slow_query_threshold=1.0,  # seconds
        log_pool_stats_interval=60,
        
        # Metrics
        metrics_enabled=True,
        metrics_prefix="myapp",
    )
)
```

**Files to Create:**
```
pynext/db/
├── adapters/
│   ├── postgres.py         # PostgreSQL adapter (~400 lines)
│   └── supabase.py         # Supabase adapter (~300 lines)
├── pool/
│   ├── __init__.py         # Pool manager
│   ├── asyncpg_pool.py     # Built-in pool (~150 lines)
│   └── external.py         # PgBouncer support (~100 lines)
├── reliability/
│   ├── health.py           # Health checks (~100 lines)
│   ├── retry.py            # Retry logic (~150 lines)
│   ├── circuit.py          # Circuit breaker (~200 lines)
│   └── replicas.py         # Read replicas (~150 lines)
└── supabase/
    ├── __init__.py         # Supabase exports
    ├── auth.py             # Auth integration (~250 lines)
    ├── storage.py          # Storage API (~200 lines)
    ├── realtime.py         # Realtime subs (~250 lines)
    ├── edge.py             # Edge Functions (~100 lines)
    └── rls.py              # RLS helpers (~150 lines)
```

**Dependencies:**
| Package | Purpose | Why This One |
|---------|---------|--------------|
| `asyncpg>=0.29.0` | PostgreSQL driver | Fastest async driver, binary protocol |
| `supabase>=2.0.0` | Supabase client | Official SDK |
| `gotrue>=2.0.0` | Auth client | Supabase Auth |
| `storage3>=0.7.0` | Storage client | Supabase Storage |
| `realtime>=2.0.0` | Realtime client | Supabase Realtime |

##### Phase 6: Reactive Frontend Integration
- [ ] **Model.live()** — Queries that auto-update when data changes
  ```python
  def Dashboard():
      # Server state (reactive) - auto-updates when DB changes
      users = User.live()
      pending = Order.live().where(status="pending")
      
      # UI state (signals)
      search = Signal("")
      
      # Derived
      filtered = Computed(lambda: [u for u in users if search() in u.name])
      
      return div(
          For(filtered, lambda u: div(u.name)),
          button("Add", on_click=lambda: User.insert(name="New"))
      )
  ```

##### Phase 7: Advanced Relationships (Target: 800+ tests)

A complete relationship system that matches SQLAlchemy's power while keeping PyNext's simple definition advantage.

**7.1 Bidirectional Relationships (backref)**
- [ ] `backref` parameter for automatic reverse relationship creation
- [ ] `back_populates` for explicit bidirectional linking
- [ ] Automatic sync when either side is modified
- [ ] Cascade relationship updates through the graph

```python
class User(Table):
    posts: List["Post"] = has_many("Post", backref="author")

class Post(Table):
    author_id: int
    # author: User automatically created via backref

# Now both sides stay in sync
user.posts.append(post)  # Also sets post.author = user
post.author = user       # Also adds to user.posts
```

**7.2 Loading Strategies**
- [ ] `lazy="select"` - Default lazy loading (query on access)
- [ ] `lazy="joined"` - JOIN in same query (eager)
- [ ] `lazy="subquery"` - Separate subquery (good for collections)
- [ ] `lazy="selectin"` - SELECT IN (ids) (best for batches)
- [ ] `lazy="raise"` - Raise error if accessed (prevent N+1)
- [ ] `lazy="dynamic"` - Return query instead of results

```python
class User(Table):
    posts: List[Post] = has_many(Post, lazy="selectin")  # Best for batches
    profile: Profile = has_one(Profile, lazy="joined")    # Eager load
    audit_logs: List[Log] = has_many(Log, lazy="dynamic") # Query builder

# Query-level override
users = await User.all().options(
    joinedload(User.posts),
    selectinload(User.posts.comments),
)
```

**7.3 Many-to-Many Relationships**
- [ ] `through` parameter for junction/association tables
- [ ] Support for extra columns on junction table
- [ ] Association proxy for direct access through relationship
- [ ] Bidirectional many-to-many with backref

```python
class Student(Table):
    courses: List["Course"] = many_to_many(
        "Course",
        through="enrollments",
        backref="students"
    )

class Course(Table):
    students: List["Student"]  # Auto-created via backref

class Enrollment(Table):  # Junction table with extra data
    student_id: int = ForeignKey(Student)
    course_id: int = ForeignKey(Course)
    enrolled_at: datetime
    grade: Optional[str]

# Usage
student.courses.append(course, grade="A")  # With extra data
course.students  # Access from either side
```

**7.4 Cascade Options**
- [ ] `cascade="save-update"` - Cascade saves to related
- [ ] `cascade="delete"` - Delete related when parent deleted
- [ ] `cascade="delete-orphan"` - Delete when removed from collection
- [ ] `cascade="merge"` - Cascade merge operations
- [ ] `cascade="all"` - All of the above

```python
class User(Table):
    posts: List[Post] = has_many(
        Post, 
        cascade="all, delete-orphan"  # Delete posts when user deleted
    )
    profile: Profile = has_one(
        Profile,
        cascade="all, delete-orphan"  # Delete profile too
    )

# Now deletion cascades automatically
await user.delete()  # Also deletes all posts and profile
```

**7.5 Custom Join Conditions**
- [ ] `primaryjoin` for custom join expressions
- [ ] `secondaryjoin` for many-to-many custom joins
- [ ] Support for non-foreign-key relationships
- [ ] Filtered relationships (e.g., only active posts)

```python
class User(Table):
    # Only load active posts
    active_posts: List[Post] = has_many(
        Post,
        primaryjoin="and_(User.id == Post.author_id, Post.is_active == True)"
    )
    
    # Load posts from last 30 days
    recent_posts: List[Post] = has_many(
        Post,
        primaryjoin="and_(User.id == Post.author_id, Post.created_at > now() - interval '30 days')"
    )

class Comment(Table):
    # Self-referential for replies
    parent_id: Optional[int] = ForeignKey("Comment")
    parent: Optional["Comment"] = belongs_to("Comment", foreign_key="parent_id")
    replies: List["Comment"] = has_many("Comment", foreign_key="parent_id")
```

**7.6 Self-Referential Relationships**
- [ ] Parent-child hierarchies (e.g., categories, org charts)
- [ ] Adjacency list pattern
- [ ] Path enumeration helpers
- [ ] Recursive query support

```python
class Category(Table):
    name: str
    parent_id: Optional[int] = ForeignKey("Category")
    
    parent: Optional["Category"] = belongs_to("Category")
    children: List["Category"] = has_many("Category", foreign_key="parent_id")
    
    # Helper methods
    async def ancestors(self) -> List["Category"]:
        """Get all parent categories up to root."""
        ...
    
    async def descendants(self) -> List["Category"]:
        """Get all child categories recursively."""
        ...
    
    @property
    def path(self) -> str:
        """Get path like 'Electronics/Computers/Laptops'."""
        ...
```

**7.7 Polymorphic Relationships**
- [ ] Single table inheritance
- [ ] Joined table inheritance
- [ ] Concrete table inheritance
- [ ] Generic foreign keys

```python
class Content(Table):
    __polymorphic_on__ = "type"
    type: str
    title: str

class Article(Content):
    __polymorphic_identity__ = "article"
    body: str

class Video(Content):
    __polymorphic_identity__ = "video"
    url: str
    duration: int

# Query returns mixed types
contents = await Content.all()  # [Article(...), Video(...), ...]

# Type-specific queries
articles = await Article.all()  # Only articles
```

**7.8 Relationship Events/Hooks**
- [ ] `@on_append` - When item added to collection
- [ ] `@on_remove` - When item removed from collection
- [ ] `@on_set` - When scalar relationship set
- [ ] `@before_delete` - Before cascade delete

```python
class User(Table):
    posts: List[Post] = has_many(Post)
    
    @posts.on_append
    def on_post_added(self, post: Post):
        """Called when a post is added to user.posts."""
        send_notification(f"New post by {self.name}")
    
    @posts.on_remove
    def on_post_removed(self, post: Post):
        """Called when a post is removed."""
        log_audit(f"Post {post.id} removed from {self.name}")
```

**7.9 Association Proxy**
- [ ] Access attributes through relationships
- [ ] Simplify many-to-many access
- [ ] Scalar and collection proxies

```python
class User(Table):
    enrollments: List[Enrollment] = has_many(Enrollment)
    
    # Access course names directly through enrollments
    course_names: List[str] = association_proxy("enrollments", "course.name")
    
    # Access courses directly
    courses: List[Course] = association_proxy("enrollments", "course")

# Usage
user.course_names  # ["Math", "Physics", "Chemistry"]
user.courses       # [Course(...), Course(...), ...]
```

**7.10 Relationship Ordering**
- [ ] Default ordering on relationships
- [ ] Multiple order columns
- [ ] Ascending/descending

```python
class User(Table):
    # Posts ordered by created_at desc by default
    posts: List[Post] = has_many(
        Post, 
        order_by="created_at desc"
    )
    
    # Multiple order columns
    comments: List[Comment] = has_many(
        Comment,
        order_by=["pinned desc", "created_at desc"]
    )
```

**Files to Create/Modify:**
```
pynext/db/
├── relationships.py          # Enhance existing (~800 lines total)
│   ├── backref support
│   ├── loading strategies
│   ├── cascade options
│   ├── custom joins
│   └── relationship events
├── relationships/
│   ├── __init__.py
│   ├── loading.py           # Loading strategy implementations (~300 lines)
│   ├── cascade.py           # Cascade logic (~200 lines)
│   ├── many_to_many.py      # M2M implementation (~250 lines)
│   ├── polymorphic.py       # Inheritance patterns (~300 lines)
│   ├── self_referential.py  # Hierarchies (~200 lines)
│   ├── proxy.py             # Association proxy (~150 lines)
│   └── events.py            # Relationship hooks (~150 lines)
├── query.py                 # Add joinedload, selectinload, etc.
└── table.py                 # Integrate new relationship features
```

**Test Coverage Target: 800+ tests**

| Feature | Tests | Coverage |
|---------|-------|----------|
| 7.1 Backref | 80 | Sync, cycles, deletion |
| 7.2 Loading strategies | 120 | All 6 strategies, nested |
| 7.3 Many-to-many | 100 | Through, extra cols, proxy |
| 7.4 Cascade | 80 | All cascade types, combinations |
| 7.5 Custom joins | 80 | Expressions, filters, complex |
| 7.6 Self-referential | 80 | Hierarchies, recursion |
| 7.7 Polymorphic | 100 | All 3 inheritance patterns |
| 7.8 Events | 60 | All event types |
| 7.9 Association proxy | 50 | Scalar, collection |
| 7.10 Ordering | 50 | Single, multiple, desc |

**Documentation:** [11-relationships.md](./database/11-relationships.md) (~2500 lines)

**PyNext vs SQLAlchemy Comparison (After Phase 7):**

| Feature | PyNext | SQLAlchemy |
|---------|--------|------------|
| Definition | Simple (type hints) | Verbose (Column, relationship) |
| Backref | Full support | Full support |
| Loading strategies | 6 strategies | 6 strategies |
| Many-to-many | With through table | Full support |
| Cascade | Full support | Full support |
| Custom joins | Full support | Full support |
| Self-referential | With helpers | Manual |
| Polymorphic | All 3 patterns | All 3 patterns |
| Events | Decorators | Event system |
| Association proxy | Full support | Full support |
| N+1 protection | Built-in | Manual |
| Async native | Yes | Bolt-on |

---

#### Success Criteria

| Metric | Target |
|--------|--------|
| Lines to define a model | 3-5 (just class + fields) |
| Lines for basic CRUD | 1 per operation |
| Time to set up database | < 5 minutes |
| Learning curve | 0 for Python devs |
| Frontend state sync | Automatic |
| Connection pool efficiency | < 5ms acquisition |
| Query timeout precision | Per-query control |
| Relationship definition | 1 line with backref |
| N+1 query protection | Automatic detection |
| Loading strategy selection | Per-query control |
| Many-to-many with extra data | Through tables |
| Cascade delete | Configurable per-relationship |

---

### React Feature Parity (SolidJS Principles)

Achieve everything React can do, but faster, simpler, and more Pythonic - using SolidJS's fine-grained reactivity instead of React's virtual DOM and hooks.

**Why SolidJS Over React?**

| Aspect | React | SolidJS/PyNext |
|--------|-------|----------------|
| Re-renders | Entire component tree | Only changed DOM nodes |
| Bundle size | ~40KB min | ~7KB min |
| Mental model | "When does this re-render?" | "When does this value change?" |
| Hooks rules | Must follow rules of hooks | No rules, just variables |
| Memoization | Manual (useMemo, useCallback) | Automatic |
| Closures | Stale closure bugs | Always fresh values |

---

#### Phase 8: Core Reactivity (Target: 400+ tests)

**8.1 Signals (React's useState equivalent)**
- [x] `Signal(initial)` - Reactive primitive (ALREADY IMPLEMENTED)
- [ ] `signal()` - Shorthand factory function
- [ ] Batch updates with `batch()`
- [ ] Untrack reads with `untrack()`
- [ ] Signal debugging with `on_change()` callback

```python
from pynext import Signal, batch

# Simple - just a variable that triggers updates
count = Signal(0)
name = Signal("Alice")

def Counter():
    return div(
        f"Count: {count()}",  # Read with ()
        button("+", on_click=lambda: count.set(count() + 1))
    )

# Batch multiple updates (one DOM update)
def reset():
    batch(lambda: [
        count.set(0),
        name.set("Alice")
    ])
```

**8.2 Computed/Derived State (React's useMemo)**
- [x] `Computed(fn)` - Auto-tracking derived values (ALREADY IMPLEMENTED)
- [ ] `memo(fn)` - Shorthand alias
- [ ] Lazy evaluation option
- [ ] Equality functions for custom comparison

```python
from pynext import Signal, Computed

first = Signal("John")
last = Signal("Doe")

# Automatically recomputes when first or last changes
# No dependency array needed - it just works
full_name = Computed(lambda: f"{first()} {last()}")

def Profile():
    return div(f"Hello, {full_name()}")  # Updates automatically
```

**8.3 Effects (React's useEffect)**
- [x] `Effect(fn)` - Run side effects when dependencies change (ALREADY IMPLEMENTED)
- [ ] `on_mount(fn)` - Run once on mount (like useEffect(fn, []))
- [ ] `on_cleanup(fn)` - Cleanup when component unmounts
- [ ] `on(signal, fn)` - Explicit dependency (like useEffect with deps)

```python
from pynext import Signal, Effect, on_mount, on_cleanup

search = Signal("")

def SearchResults():
    results = Signal([])
    
    # Runs whenever search() changes - no dependency array!
    Effect(lambda: fetch_results(search()).then(results.set))
    
    # Run once on mount
    on_mount(lambda: print("Component mounted"))
    
    # Cleanup on unmount
    on_cleanup(lambda: cancel_pending_requests())
    
    return ul(For(results, lambda r: li(r.title)))
```

**8.4 Resources (React's data fetching patterns)**
- [ ] `Resource(fetcher)` - Async data with loading/error states
- [ ] `resource.loading` - Boolean loading state
- [ ] `resource.error` - Error if failed
- [ ] `resource()` - The data (or None while loading)
- [ ] `resource.refetch()` - Manual refetch
- [ ] `resource.mutate(data)` - Optimistic updates

```python
from pynext import Resource, Signal

user_id = Signal(1)

# Fetcher re-runs when user_id changes
user = Resource(lambda: fetch(f"/api/users/{user_id()}"))

def UserProfile():
    return div(
        Show(user.loading, lambda: "Loading..."),
        Show(user.error, lambda: f"Error: {user.error}"),
        Show(user(), lambda u: div(
            h1(u.name),
            p(u.email)
        ))
    )
```

---

#### Phase 9: Component Patterns (Target: 300+ tests)

**9.1 Context (React's useContext)**
- [ ] `create_context(default)` - Create a context
- [ ] `Provider(value=...)` - Provide value to descendants
- [ ] `use_context(ctx)` - Read context value (reactive!)
- [ ] Nested providers with override

```python
from pynext import create_context, Provider

# Create context with default
ThemeContext = create_context("light")
UserContext = create_context(None)

def App():
    theme = Signal("dark")
    user = Signal({"name": "Alice"})
    
    return Provider(ThemeContext, theme,
        Provider(UserContext, user,
            Dashboard()
        )
    )

def Dashboard():
    # Just use it - reactive automatically
    theme = use_context(ThemeContext)
    user = use_context(UserContext)
    
    return div(
        class_=f"theme-{theme()}",
        f"Welcome, {user().name}"
    )
```

**9.2 Error Boundaries (React's componentDidCatch)**
- [ ] `ErrorBoundary(fallback=...)` - Catch errors in children
- [ ] `fallback` receives error and reset function
- [ ] Nested error boundaries
- [ ] `reset_error_boundary()` to recover

```python
from pynext import ErrorBoundary

def App():
    return ErrorBoundary(
        fallback=lambda err, reset: div(
            h1("Something went wrong"),
            p(str(err)),
            button("Try again", on_click=reset)
        ),
        children=RiskyComponent()
    )
```

**9.3 Suspense (React's Suspense)**
- [x] `Suspense(fallback=...)` - Show fallback while loading (PARTIALLY IMPLEMENTED)
- [ ] Nested suspense boundaries
- [ ] `SuspenseList` for coordinated loading
- [ ] Integration with `Resource()`

```python
from pynext import Suspense, lazy

# Lazy load component
HeavyChart = lazy(lambda: import_component("./HeavyChart"))

def Dashboard():
    return Suspense(
        fallback=Spinner(),
        children=[
            HeavyChart(),
            lazy(lambda: import_component("./DataTable"))()
        ]
    )
```

**9.4 Portals (React's createPortal)**
- [ ] `Portal(mount=selector)` - Render children elsewhere in DOM
- [ ] Default mount to document.body
- [ ] Event bubbling through portal

```python
from pynext import Portal

def Modal():
    show = Signal(False)
    
    return div(
        button("Open", on_click=lambda: show.set(True)),
        Show(show, lambda: 
            Portal(
                mount="body",  # or "#modal-root"
                children=div(
                    class_="modal-overlay",
                    div(
                        class_="modal",
                        h2("Modal Title"),
                        button("Close", on_click=lambda: show.set(False))
                    )
                )
            )
        )
    )
```

**9.5 Refs (React's useRef)**
- [ ] `ref=` attribute for DOM element access
- [ ] `Ref()` for mutable values that don't trigger updates
- [ ] Forward refs through components

```python
from pynext import Ref

def Form():
    input_ref = Ref()  # Mutable container
    
    def focus_input():
        input_ref.current.focus()
    
    return div(
        input(ref=input_ref, type="text"),
        button("Focus", on_click=focus_input)
    )

# Forward ref to child
def FancyInput(ref=None):
    return input(ref=ref, class_="fancy")
```

---

#### Phase 10: Control Flow (Target: 200+ tests)

**10.1 Conditional Rendering**
- [x] `Show(when, children)` - Conditional render (ALREADY IMPLEMENTED)
- [ ] `Show(when, children, fallback=...)` - With else branch
- [ ] `Switch/Match` - Multiple conditions

```python
from pynext import Show, Switch, Match

status = Signal("loading")

def StatusDisplay():
    return Switch(
        Match(status() == "loading", Spinner()),
        Match(status() == "error", ErrorMessage()),
        Match(status() == "success", SuccessMessage()),
        fallback=UnknownStatus()
    )
```

**10.2 List Rendering**
- [x] `For(items, render)` - Efficient list rendering (ALREADY IMPLEMENTED)
- [ ] `Index(items, render)` - When index matters more than identity
- [ ] Keyed vs non-keyed rendering
- [ ] `For` with `fallback` for empty lists

```python
from pynext import For, Index, Signal

items = Signal([
    {"id": 1, "name": "Apple"},
    {"id": 2, "name": "Banana"}
])

def ItemList():
    return ul(
        For(
            items,
            lambda item, idx: li(f"{idx}: {item['name']}"),
            fallback=li("No items")
        )
    )
```

**10.3 Dynamic Components**
- [ ] `Dynamic(component=...)` - Render component dynamically
- [ ] Props spreading

```python
from pynext import Dynamic, Signal

component = Signal(HomePage)

def App():
    return div(
        nav(
            button("Home", on_click=lambda: component.set(HomePage)),
            button("About", on_click=lambda: component.set(AboutPage))
        ),
        Dynamic(component=component)
    )
```

---

#### Phase 11: Advanced Patterns (Target: 300+ tests)

**11.1 Stores (Complex State)**
- [ ] `Store(initial)` - Nested reactive objects
- [ ] `store.path.to.value` - Deep reactivity
- [ ] `produce(store, fn)` - Immer-style updates
- [ ] `reconcile(store, new_data)` - Diff and patch

```python
from pynext import Store, produce

# Deeply reactive - any nested change triggers precise updates
state = Store({
    "user": {"name": "Alice", "settings": {"theme": "dark"}},
    "items": [{"id": 1, "done": False}]
})

def Settings():
    return div(
        f"Theme: {state.user.settings.theme}",  # Reactive path
        button("Toggle", on_click=lambda: 
            produce(state, lambda s: 
                s.user.settings.update(theme="light" if s.user.settings.theme == "dark" else "dark")
            )
        )
    )
```

**11.2 Transitions (Concurrent UI)**
- [ ] `start_transition(fn)` - Mark updates as non-urgent
- [ ] `use_transition()` - Get pending state
- [ ] Keep old UI while new one loads

```python
from pynext import Signal, start_transition, use_transition

tab = Signal("home")
is_pending, start = use_transition()

def TabContainer():
    return div(
        class_="pending" if is_pending() else "",
        nav(
            button("Home", on_click=lambda: start(lambda: tab.set("home"))),
            button("Profile", on_click=lambda: start(lambda: tab.set("profile")))
        ),
        # Old tab stays visible until new one is ready
        TabContent(tab())
    )
```

**11.3 Deferred Values**
- [ ] `deferred(signal)` - Lag behind for expensive renders
- [ ] `deferred(signal, timeout_ms=)` - With timeout

```python
from pynext import Signal, deferred

search = Signal("")
deferred_search = deferred(search, timeout_ms=300)

def Search():
    return div(
        input(value=search, on_input=lambda e: search.set(e.target.value)),
        # Expensive list uses deferred value
        ExpensiveList(query=deferred_search)
    )
```

**11.4 Streaming & Progressive Rendering**
- [x] Streaming HTML (ALREADY IMPLEMENTED)
- [ ] Progressive hydration
- [ ] Selective hydration based on visibility
- [ ] `renderToStream()` for SSR

---

#### Phase 12: Developer Experience (Target: 200+ tests)

**12.1 DevTools Integration**
- [ ] Signal inspection in browser devtools
- [ ] Component tree visualization
- [ ] Reactivity graph visualization
- [ ] Time-travel debugging

**12.2 Hot Module Replacement**
- [x] HMR for components (ALREADY IMPLEMENTED)
- [ ] Preserve signal state across HMR
- [ ] Component state persistence

**12.3 TypeScript-style Type Hints**
- [ ] Full type inference for signals
- [ ] Generic Signal[T]
- [ ] Typed props with dataclass

```python
from pynext import Signal, component
from dataclasses import dataclass

@dataclass
class ButtonProps:
    label: str
    on_click: Callable[[], None]
    disabled: bool = False

@component
def Button(props: ButtonProps):
    return button(
        props.label,
        on_click=props.on_click,
        disabled=props.disabled
    )
```

---

#### Files to Create/Modify

```
pynext/
├── reactivity/
│   ├── __init__.py          # Public exports
│   ├── signal.py            # Enhance Signal with batch, untrack
│   ├── computed.py          # Enhance Computed with lazy, equality
│   ├── effect.py            # Add on_mount, on_cleanup, on()
│   ├── resource.py          # NEW: Async data primitive
│   ├── store.py             # NEW: Deep reactivity
│   ├── context.py           # NEW: Context API
│   └── transitions.py       # NEW: Concurrent UI
├── components/
│   ├── error_boundary.py    # NEW: Error catching
│   ├── suspense.py          # Enhance existing
│   ├── portal.py            # NEW: DOM portals
│   ├── dynamic.py           # NEW: Dynamic component
│   └── control_flow.py      # Enhance Show, For, add Switch
└── runtime/
    ├── reactivity.js        # Client-side reactivity
    └── hydration.js         # Progressive hydration
```

#### React Parity Test Coverage Target: 1200+ tests

| Phase | Feature | Tests |
|-------|---------|-------|
| 8.1 | Signals | 100 |
| 8.2 | Computed | 80 |
| 8.3 | Effects | 100 |
| 8.4 | Resources | 120 |
| 9.1 | Context | 80 |
| 9.2 | Error Boundaries | 60 |
| 9.3 | Suspense | 80 |
| 9.4 | Portals | 40 |
| 9.5 | Refs | 40 |
| 10.x | Control Flow | 200 |
| 11.x | Advanced | 300 |

#### Documentation

Create `docs/features/REACTIVITY.md` (~3000 lines):
- First principles: Why fine-grained reactivity
- Migration guide from React hooks
- Visual diagrams of reactivity flow
- Performance comparisons
- Complete API reference

#### PyNext vs React Comparison

| Feature | React | PyNext |
|---------|-------|--------|
| State | useState + rules | Signal() - just works |
| Derived | useMemo + deps array | Computed() - auto-tracks |
| Effects | useEffect + deps array | Effect() - auto-tracks |
| Context | Provider + useContext | Provider + use_context (reactive!) |
| Suspense | Yes | Yes |
| Error Boundaries | Class components only | Simple component |
| Portals | createPortal | Portal component |
| Concurrent | startTransition | start_transition |
| SSR | Next.js required | Built-in |
| Bundle | ~40KB | ~7KB |
| Re-renders | Component tree | Only changed nodes |
| Mental model | "When re-render?" | "When value change?" |

---

### Native Authentication (SolidJS Principles)

Dead-simple authentication that consolidates the entire Next.js auth complexity into a few Python primitives. No more juggling 15+ concepts just to protect a route!

---

#### Why Authentication is Hard (And Shouldn't Be)

Authentication is a **solved problem**. Every app needs login, logout, sessions, and protected routes. Yet the current state of the art requires:

```
Next.js Auth Flow (From Their Official Docs):

┌─────────────────────────────────────────────────────────────────────────────┐
│                                 CLIENT                                       │
│  ┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐   │
│  │   <form>     │    │ useFormState()   │    │   useFormStatus()      │   │
│  │ (with attrs) │    │ (React hook)     │    │   (another hook)       │   │
│  └──────┬───────┘    └────────┬─────────┘    └───────────┬─────────────┘   │
│         │                     │                          │                  │
│         └─────────────────────┼──────────────────────────┘                  │
│                               ▼                                             │
│                    ┌──────────────────┐                                    │
│                    │  Server Action   │                                    │
│                    └────────┬─────────┘                                    │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────────────┐
│                           SERVER                                             │
│                              ▼                                              │
│   ┌──────────────┐    ┌─────────────────┐    ┌────────────────────────┐    │
│   │  Middleware  │    │  cookies() API  │    │  Session encryption   │    │
│   │  + matcher   │    │  + serialize    │    │  functions            │    │
│   └──────┬───────┘    └────────┬────────┘    └───────────┬────────────┘    │
│          │                     │                         │                  │
│   ┌──────▼───────┐    ┌────────▼────────┐    ┌───────────▼────────────┐    │
│   │    DAL       │    │     DTO         │    │    getSession()       │    │
│   │ (Data Access)│    │(Transfer Object)│    │    helper             │    │
│   └──────────────┘    └─────────────────┘    └────────────────────────┘    │
│                                                                              │
│   External Dependencies: NextAuth, Auth0, Clerk, iron-session, jose...     │
└──────────────────────────────────────────────────────────────────────────────┘

That's 15+ concepts just for "is this user logged in?" 🤯
```

**PyNext Auth Flow:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PYNEXT                                          │
│                                                                              │
│   Auth.setup(secret="...")  ──────────────►  Done.                          │
│                                                                              │
│   @login_required           ──────────────►  Route protected.               │
│                                                                              │
│   current_user()            ──────────────►  User data (reactive).          │
│                                                                              │
│   Auth.login_form()         ──────────────►  Full login UI.                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

4 concepts. That's it. 🎉
```

---

#### The Next.js Auth Problem (In Detail)

From the [Next.js authentication docs](https://nextjs.org/docs/pages/guides/authentication), here's what you actually need:

| Concept | What It Does | Lines of Code | Files |
|---------|--------------|---------------|-------|
| `<form>` with handlers | Capture user input | ~20 | 1 |
| `useFormState()` | Manage form state | ~15 | 1 |
| `useFormStatus()` | Show loading states | ~10 | 1 |
| Server Action | Handle form submission | ~30 | 1 |
| API Route `/api/auth/login` | Process login | ~50 | 1 |
| `cookies()` API | Set/get cookies | ~20 | 1 |
| `serialize` package | Encode cookies | ~10 | 1 |
| Session encryption | Encrypt session data | ~40 | 1 |
| Database session table | Store sessions | ~30 | 1 |
| Middleware | Check auth on routes | ~50 | 1 |
| `matcher` config | Define protected routes | ~20 | 1 |
| Data Access Layer | Centralize DB queries | ~100 | 3+ |
| Data Transfer Objects | Shape API responses | ~50 | 2+ |
| `getSession()` helper | Get user from session | ~30 | 1 |
| Error handling | Auth errors | ~40 | 1 |
| **TOTAL** | **Basic auth** | **~500+ lines** | **15+ files** |

And this doesn't include:
- OAuth providers (add ~200 lines each)
- Email verification (~100 lines)
- Password reset (~100 lines)
- 2FA (~150 lines)
- Rate limiting (external package)
- CSRF protection (external package)

---

#### PyNext Auth Solution (Comparison)

| Task | Next.js Approach | Lines | PyNext Approach | Lines | Reduction |
|------|------------------|-------|-----------------|-------|-----------|
| **Setup** | Config file + env + init | ~100 | `Auth.setup(secret=...)` | **3** | **97%** |
| **Protected route** | Middleware + matcher + hook | ~80 | `@login_required` | **1** | **99%** |
| **Get current user** | Hook + context + types | ~40 | `current_user()` | **1** | **98%** |
| **Login form** | Form + state + action + API | ~100 | `Auth.login_form()` | **1** | **99%** |
| **OAuth (Google)** | Provider + callback + config | ~150 | `providers=["google"]` | **1** | **99%** |
| **Session mgmt** | iron-session + encrypt + cookies | ~80 | `session="jwt"` | **1** | **99%** |
| **Email verification** | Custom routes + tokens + email | ~100 | `require_verified=True` | **1** | **99%** |
| **Password reset** | Custom flow + tokens + email | ~100 | `Auth.send_reset_email()` | **1** | **99%** |
| **2FA/MFA** | External package + UI + storage | ~200 | `mfa_enabled=True` | **1** | **99%** |
| **Role-based access** | Custom middleware | ~60 | `@role_required("admin")` | **1** | **98%** |
| **CSRF protection** | Manual tokens + validation | ~50 | Automatic | **0** | **100%** |
| **Rate limiting** | External package + config | ~40 | Built-in | **0** | **100%** |
| **TOTAL** | Complex multi-file setup | **~1000+** | Simple Python | **~30** | **97%** |

---

#### Performance Benchmarks (Auth-Specific)

| Metric | Next.js + NextAuth | PyNext Auth | Improvement |
|--------|-------------------|-------------|-------------|
| **Auth check latency** | ~50ms (JWT verify + hooks) | **~5ms** | **10x faster** |
| **Session lookup (DB)** | ~100ms (Prisma + hooks) | **~20ms** | **5x faster** |
| **Login form render** | ~200ms (React + form libs) | **~20ms** | **10x faster** |
| **Bundle size (auth)** | ~30KB (NextAuth client) | **<3KB** | **90% smaller** |
| **OAuth flow** | 3 round-trips | **2 round-trips** | **33% faster** |
| **Time to implement** | 1-2 days | **10 minutes** | **100x faster** |

---

#### Why Our Approach is Better

| Principle | Next.js Problem | PyNext Solution |
|-----------|-----------------|-----------------|
| **Simplicity** | 15+ concepts to learn | 4 concepts total |
| **Reactivity** | Hooks + context + re-renders | Signals - just works |
| **Integration** | Separate auth library | Built into framework |
| **Database** | Separate ORM (Prisma) | Uses your existing `db` |
| **Type Safety** | TypeScript required | Python type hints |
| **Security** | Manual CSRF, rate limiting | Automatic, built-in |
| **Extensibility** | Override adapter methods | Extend `Auth.User` class |
| **Testing** | Mock providers manually | MockAdapter included |

---

#### Complete Example: Next.js vs PyNext

**Next.js (Minimal Auth) - 12+ files, ~500 lines:**

```
app/
├── api/
│   └── auth/
│       ├── [...nextauth]/route.ts    # 50 lines
│       └── login/route.ts            # 40 lines
├── lib/
│   ├── auth.ts                       # 60 lines (config)
│   ├── session.ts                    # 40 lines
│   └── dal.ts                        # 80 lines
├── middleware.ts                     # 50 lines
├── login/
│   ├── page.tsx                      # 60 lines
│   └── actions.ts                    # 40 lines
├── dashboard/
│   └── page.tsx                      # 30 lines
└── types/
    └── auth.ts                       # 30 lines
```

**PyNext (Same Features) - 2 files, ~30 lines:**

```python
# config.py (10 lines)
from pynext.auth import Auth

Auth.setup(
    secret=env("AUTH_SECRET"),
    providers=["email", "google"],
    session="jwt",
)

# pages/login.py (10 lines)
from pynext.auth import Auth

def LoginPage():
    return div(
        h1("Sign In"),
        Auth.oauth_button("google"),
        Auth.login_form()
    )

# pages/dashboard.py (10 lines)
from pynext.auth import login_required, current_user

@login_required
def Dashboard():
    user = current_user()
    return div(f"Welcome, {user().name}!")
```

**Same result. 97% less code. Zero config files.**

---

#### Architecture: How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PYNEXT AUTH ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     ┌──────────────────────────────────────────────────┐  │
│  │   Browser   │     │                    PyNext Server                  │  │
│  │             │     │                                                   │  │
│  │  ┌───────┐  │     │   ┌─────────────────────────────────────────┐   │  │
│  │  │Signal │◄─┼─────┼───│            Auth Middleware               │   │  │
│  │  │current│  │     │   │  • Check session cookie                  │   │  │
│  │  │_user()│  │     │   │  • Decode JWT / lookup DB session        │   │  │
│  │  └───────┘  │     │   │  • Set current_user Signal               │   │  │
│  │             │     │   │  • Apply @login_required                 │   │  │
│  │  ┌───────┐  │     │   └─────────────────────────────────────────┘   │  │
│  │  │ Forms │──┼─────┼───►  Auth.login_form()                          │  │
│  │  │       │  │     │      • CSRF token (automatic)                   │  │
│  │  │       │  │     │      • Validation (automatic)                   │  │
│  │  │       │  │     │      • Rate limiting (automatic)                │  │
│  │  └───────┘  │     │                                                   │  │
│  │             │     │   ┌─────────────────────────────────────────┐   │  │
│  │  ┌───────┐  │     │   │            Session Storage               │   │  │
│  │  │Cookie │◄─┼─────┼───│                                         │   │  │
│  │  │(JWT)  │  │     │   │  JWT ───► Stateless (default)           │   │  │
│  │  └───────┘  │     │   │  DB  ───► PostgresAdapter (revocable)   │   │  │
│  │             │     │   │  Redis──► Fast + revocable              │   │  │
│  └─────────────┘     │   └─────────────────────────────────────────┘   │  │
│                      │                                                   │  │
│                      │   ┌─────────────────────────────────────────┐   │  │
│                      │   │            ORM Integration               │   │  │
│                      │   │                                         │   │  │
│                      │   │  Auth.User ──► extends Table            │   │  │
│                      │   │  user.posts ──► relationships work      │   │  │
│                      │   │  migrations ──► auto-generated          │   │  │
│                      │   └─────────────────────────────────────────┘   │  │
│                      └───────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

#### Security: Built-in, Not Bolted-on

| Security Feature | Next.js | PyNext |
|------------------|---------|--------|
| **Password Hashing** | Manual (bcrypt package) | **Argon2 (default)** |
| **CSRF Protection** | Manual tokens | **Automatic** |
| **Rate Limiting** | External package | **Built-in** |
| **Brute Force Protection** | Manual implementation | **Built-in lockout** |
| **Secure Cookies** | Manual config | **httpOnly, secure, sameSite by default** |
| **Session Encryption** | Manual implementation | **Automatic** |
| **XSS in Forms** | Manual sanitization | **Automatic escaping** |
| **SQL Injection** | Depends on ORM | **Parameterized queries** |

---

#### The PyNext Solution (Code)

```python
from pynext.auth import Auth, login_required, current_user

# 1. Configure once (3 lines)
Auth.setup(
    secret="your-secret-key",
    providers=["email", "google", "github"],
    session="jwt",
)

# 2. Protect routes (1 decorator)
@login_required
def Dashboard():
    user = current_user()  # Signal - reactive!
    return div(f"Welcome, {user().name}")

# 3. Login form (1 line)
def LoginPage():
    return Auth.login_form()
```

**~30 lines of PyNext replaces ~500+ lines of Next.js**

---

#### Phase 13: Native Authentication (Target: 600+ tests)

**13.1 One-Line Setup**
- [ ] `Auth.setup(secret=, providers=, session=)` - Configure everything
- [ ] Auto-generate routes: `/login`, `/logout`, `/register`, `/forgot-password`, `/verify-email`, `/reset-password`
- [ ] Auto-create database tables if needed
- [ ] Environment variable fallbacks (`PYNEXT_AUTH_SECRET`, etc.)

```python
from pynext.auth import Auth
from datetime import timedelta

# Minimal setup - just a secret
Auth.setup(secret="my-secret-key")

# Full setup
Auth.setup(
    secret="my-secret-key",
    session="jwt",                       # or "database" or "redis"
    session_lifetime=timedelta(days=7),
    providers=["email", "google", "github", "magic_link"],
    password_min_length=8,
    require_verified=True,               # Email verification required
    rate_limit="10/minute",
    csrf=True,
    mfa_enabled=False,                   # 2FA support
)
```

**13.2 Signal-Based Auth State**
- [ ] `current_user()` - Reactive Signal with user data
- [ ] `is_authenticated()` - Reactive boolean Signal
- [ ] `auth_loading()` - Loading state Signal
- [ ] `auth_error()` - Error state Signal
- [ ] Auto-refresh on token expiry
- [ ] Automatic state sync across tabs

```python
from pynext.auth import current_user, is_authenticated

def Header():
    user = current_user()  # Signal - updates automatically!
    
    return header(
        Show(is_authenticated(),
            lambda: div(
                f"Hello, {user().name}",
                button("Logout", on_click=Auth.logout)
            ),
            fallback=a("Login", href="/login")
        )
    )
```

**13.3 Route Protection**
- [ ] `@login_required` - Protect any route
- [ ] `@login_required(redirect="/login")` - Custom redirect
- [ ] `@role_required("admin")` - Role-based access
- [ ] `@permission_required("posts:write")` - Permission-based
- [ ] Automatic redirect after login to original destination
- [ ] Protected route patterns in config

```python
from pynext.auth import login_required, role_required, permission_required

# Simple protection
@login_required
def Dashboard():
    return div("Secret dashboard")

# Role-based
@role_required("admin")
def AdminPanel():
    return div("Admin only")

# Fine-grained permissions
@permission_required("posts:delete")
def DeletePost(post_id: int):
    return div("Delete confirmation")

# Or configure globally
Auth.setup(
    protected_routes=["/dashboard/*", "/admin/*", "/api/private/*"],
    public_routes=["/", "/login", "/register", "/api/public/*"],
)
```

**13.4 Built-In Auth Forms**
- [ ] `Auth.login_form()` - Complete login form with validation
- [ ] `Auth.register_form()` - Registration with password strength
- [ ] `Auth.forgot_password_form()` - Password reset request
- [ ] `Auth.reset_password_form(token)` - Set new password
- [ ] `Auth.change_password_form()` - Change current password
- [ ] `Auth.verify_email_form()` - Email verification
- [ ] All forms customizable but work out-of-box
- [ ] Built-in CSRF protection

```python
# Default forms - just work!
def LoginPage():
    return div(
        h1("Sign In"),
        Auth.login_form()
    )

# Customized
def CustomLogin():
    return Auth.login_form(
        class_="my-form",
        show_remember_me=True,
        show_forgot_password=True,
        on_success=lambda: navigate("/dashboard"),
    )
```

**13.5 OAuth Providers**
- [ ] Google, GitHub, Apple, Microsoft, Discord, Twitter, Facebook
- [ ] `Auth.oauth_button("google")` - Styled button
- [ ] Automatic callback handling
- [ ] Account linking (same email = same account)
- [ ] Scope configuration

```python
Auth.setup(
    providers={
        "google": {
            "client_id": env("GOOGLE_CLIENT_ID"),
            "client_secret": env("GOOGLE_CLIENT_SECRET"),
            "scopes": ["email", "profile"],
        },
        "github": {
            "client_id": env("GITHUB_CLIENT_ID"),
            "client_secret": env("GITHUB_CLIENT_SECRET"),
        }
    }
)

def LoginPage():
    return div(
        Auth.oauth_button("google"),
        Auth.oauth_button("github"),
        p("or"),
        Auth.login_form()
    )
```

**13.6 Magic Links (Passwordless)**
- [ ] `Auth.send_magic_link(email)` - Send login link
- [ ] Automatic token generation and validation
- [ ] Configurable expiry
- [ ] Rate limiting built-in

```python
Auth.setup(
    providers=["magic_link"],
    magic_link_expiry=timedelta(minutes=15),
)

async def send_link():
    await Auth.send_magic_link(email())
```

**13.7 Session Management**
- [ ] JWT sessions (stateless, scalable) - default
- [ ] Database sessions (revocable, audit trail)
- [ ] Redis sessions (fast + revocable)
- [ ] Cookie encryption automatic
- [ ] Secure cookie settings (httpOnly, secure, sameSite)
- [ ] "Remember me" with extended lifetime
- [ ] Multi-device session management
- [ ] Session invalidation on password change

```python
# Stateless JWT (default)
Auth.setup(session="jwt", session_lifetime=timedelta(days=7))

# Database sessions (revocable)
Auth.setup(session="database")

# Redis (fast + revocable)
Auth.setup(session="redis", redis_url="redis://localhost")

# Session management
sessions = await Auth.get_sessions(user_id)
await Auth.revoke_session(session_id)
await Auth.revoke_all_sessions(user_id)
```

**13.8 Email Verification**
- [ ] `Auth.send_verification_email(email)` - Send verification
- [ ] Auto-generated `/verify-email` route
- [ ] Configurable expiry
- [ ] Resend with rate limiting

```python
Auth.setup(
    require_verified=True,
    verification_expiry=timedelta(hours=24),
)

# Check status
if not current_user().email_verified:
    return redirect("/verify-email")
```

**13.9 Password Reset**
- [ ] `Auth.send_reset_email(email)` - Send reset link
- [ ] Auto-generated `/reset-password` route
- [ ] Secure token with expiry
- [ ] Invalidate all sessions on reset

```python
await Auth.send_reset_email(email)
await Auth.reset_password(token, new_password)
```

**13.10 Two-Factor Authentication (2FA/MFA)**
- [ ] TOTP support (Google Authenticator, Authy)
- [ ] SMS codes (optional)
- [ ] Backup codes generation
- [ ] Remember device option

```python
Auth.setup(mfa_enabled=True, mfa_methods=["totp"])

# Enable for user
qr_code, backup_codes = await Auth.enable_2fa(user_id)

# Verify
is_valid = await Auth.verify_2fa(user_id, code)

# Require 2FA for route
@login_required(require_2fa=True)
def SecureDashboard(): ...
```

**13.11 Account Linking**
- [ ] Same email = same account (automatic)
- [ ] Link additional providers
- [ ] Unlink providers (keep at least one)

```python
await Auth.link_provider(user_id, "github", github_token)
providers = await Auth.get_linked_providers(user_id)
await Auth.unlink_provider(user_id, "github")
```

**13.12 Role & Permission System**
- [ ] Built-in Role model
- [ ] Permission strings (e.g., "posts:write")
- [ ] Role inheritance
- [ ] Easy assignment

```python
from pynext.auth import Role

admin = Role("admin", permissions=["*"])
editor = Role("editor", permissions=["posts:*", "comments:*"])

await Auth.assign_role(user_id, "editor")

if await Auth.has_permission(user_id, "posts:write"):
    # Can write posts
```

**13.13 API Route Protection**
- [ ] `@api_auth_required` for API endpoints
- [ ] API key authentication option
- [ ] Scoped access tokens
- [ ] Rate limiting per endpoint

```python
from pynext.auth import api_auth_required

@api_auth_required
async def api_get_profile(request):
    user = current_user()
    return {"id": user().id, "name": user().name}

@api_auth_required(scopes=["write:posts"])
async def api_create_post(request): ...
```

**13.14 Data Access Layer Integration**
- [ ] Automatic user context in queries
- [ ] Row-level security helpers
- [ ] Audit logging

```python
from pynext.auth import with_user_context

@with_user_context
async def get_my_posts():
    # Automatically filtered by current user
    return await Post.all()
```

**13.15 Seamless ORM Integration**

Auth uses PyNext's existing database layer - no separate config needed!

- [ ] `AuthUser` extends `Table` - full ORM capabilities
- [ ] Auto-create auth tables via migrations
- [ ] Use existing `PostgresAdapter` for sessions
- [ ] Relationships work out-of-box (`user.posts`, `user.roles`)
- [ ] Validation uses PyNext's validation system
- [ ] Works with all adapters (Postgres, SQLite, Mock)

```python
from pynext.db import Table, db
from pynext.auth import Auth

# Auth automatically uses your configured database
db.configure("postgresql://localhost/myapp")

Auth.setup(
    secret="...",
    session="database",  # Uses your PostgresAdapter!
)

# AuthUser is a regular Table - extend it!
class User(Auth.User):
    """Your custom user with all ORM features."""
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Relationships work!
    posts: List["Post"] = has_many("Post", backref="author")
    profile: "Profile" = has_one("Profile")

class Post(Table):
    title: str
    content: str
    author_id: int  # FK to User - auto-detected!

# All ORM features available
user = await User.get(1)
user.posts  # Eager loading works
await user.with_related("posts", "profile")  # Load relationships

# Queries with auth context
@login_required
async def my_dashboard():
    user = current_user()
    
    # Use ORM normally
    my_posts = await Post.where(author_id=user().id).all()
    recent = await Post.where(author_id=user().id).order_by("-created_at").limit(5)
    
    return {"posts": my_posts, "recent": recent}
```

**13.16 Auto-Generated Migrations**
- [ ] `pynext db migrate` creates auth tables automatically
- [ ] Version-tracked with your app migrations
- [ ] Customizable table names

```python
# Auth tables are auto-detected and migrated
# Just run: pynext db migrate

# Generated migration creates:
# - users (id, email, password_hash, email_verified, created_at, updated_at)
# - sessions (id, user_id, token, expires_at, created_at)
# - roles (id, name, permissions)
# - user_roles (user_id, role_id)

# Customize table names if needed
Auth.setup(
    table_prefix="auth_",  # auth_users, auth_sessions, etc.
)
```

**13.17 Session Storage with Adapters**
- [ ] JWT (stateless) - no database needed
- [ ] Database sessions use your `PostgresAdapter`
- [ ] Redis sessions via optional adapter
- [ ] All benefit from connection pooling, retry, etc.

```python
# Database sessions use your existing adapter
db.configure("postgresql://localhost/myapp")

Auth.setup(
    session="database",
    # Automatically uses your PostgresAdapter with:
    # - Connection pooling
    # - Statement caching
    # - Retry logic
    # - Circuit breaker
)

# Or explicit adapter
from pynext.db.adapters import PostgresAdapter

adapter = PostgresAdapter(
    url="postgresql://localhost/myapp",
    min_connections=5,
    max_connections=20,
)

Auth.setup(
    session="database",
    adapter=adapter,  # Use specific adapter
)
```

**13.18 Validation Integration**
- [ ] Uses PyNext's validation system
- [ ] Custom validators for auth fields
- [ ] Clear error messages

```python
from pynext.db import Table, EmailField, StringField
from pynext.auth import Auth

class User(Auth.User):
    # PyNext validation works!
    email: str = EmailField(unique=True)
    username: str = StringField(min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$")
    
    @validator("username")
    def username_not_reserved(cls, v):
        if v in ["admin", "root", "system"]:
            raise ValueError("Username is reserved")
        return v

# Validation errors are user-friendly
try:
    await Auth.register(email="bad", password="123")
except ValidationError as e:
    # {"email": "Invalid email format", "password": "Must be at least 8 characters"}
```

**13.19 Query Builder Integration**
- [ ] Auth queries use PyNext's query builder
- [ ] Chainable, type-safe queries
- [ ] Raw SQL escape hatch

```python
# Auth uses the same query patterns you know
from pynext.auth import AuthUser

# Standard queries
admins = await AuthUser.where(role="admin").all()
recent_users = await AuthUser.order_by("-created_at").limit(10)
verified = await AuthUser.where(email_verified=True).count()

# Complex queries
active_admins = await (
    AuthUser
    .where(role="admin")
    .where(last_login__gte=datetime.now() - timedelta(days=30))
    .with_related("sessions")
    .all()
)

# Raw SQL when needed
result = await db.sql("""
    SELECT u.*, COUNT(s.id) as session_count
    FROM users u
    LEFT JOIN sessions s ON s.user_id = u.id
    GROUP BY u.id
    HAVING COUNT(s.id) > 5
""")
```

**13.20 Security Built-In**
- [ ] Password hashing (argon2 default, bcrypt option)
- [ ] CSRF protection automatic
- [ ] Rate limiting built-in
- [ ] Brute force protection (lockout)
- [ ] Secure cookies (httpOnly, secure, sameSite)
- [ ] Session encryption
- [ ] XSS protection in forms

```python
Auth.setup(
    password_hasher="argon2",
    csrf=True,
    rate_limit={
        "login": "5/minute",
        "register": "3/minute",
        "forgot_password": "3/hour",
    },
    lockout_threshold=5,  # Lock after 5 failed attempts
    lockout_duration=timedelta(minutes=15),
)
```

---

**Files to Create:**
```
pynext/auth/
├── __init__.py          # Public API
├── config.py            # Auth.setup()
├── signals.py           # current_user(), is_authenticated()
├── decorators.py        # @login_required, @role_required
├── forms.py             # Auth.login_form(), etc.
├── providers/
│   ├── email.py         # Email/password
│   ├── oauth.py         # OAuth base + Google, GitHub, etc.
│   └── magic_link.py    # Passwordless
├── session/
│   ├── jwt.py           # JWT sessions
│   ├── database.py      # DB sessions (uses PostgresAdapter)
│   └── redis.py         # Redis sessions
├── security/
│   ├── password.py      # Hashing
│   ├── csrf.py          # CSRF protection
│   ├── rate_limit.py    # Rate limiting
│   ├── tokens.py        # Token generation
│   └── mfa.py           # 2FA/TOTP
├── verification.py      # Email verification
├── reset.py             # Password reset
├── roles.py             # Roles & permissions
├── linking.py           # Account linking
├── models.py            # User, Session, Role (extends Table)
└── middleware.py        # Auth middleware
```

**Test Coverage Target: 600+ tests**

| Feature | Tests |
|---------|-------|
| Setup & Config | 40 |
| Auth Signals | 50 |
| Route Protection | 60 |
| Built-in Forms | 60 |
| OAuth Providers | 80 |
| Magic Links | 40 |
| Sessions | 70 |
| Email Verification | 40 |
| Password Reset | 40 |
| 2FA/MFA | 50 |
| Account Linking | 30 |
| Roles & Permissions | 50 |
| API Protection | 40 |
| ORM Integration | 60 |
| Security | 80 |

**Documentation:** [AUTHENTICATION.md](./features/AUTHENTICATION.md) (~2500 lines)

**PyNext Auth vs Next.js Auth:**

| Task | Next.js | PyNext |
|------|---------|--------|
| Basic setup | ~100 lines + config | 3 lines |
| Protected route | Middleware + matcher + hooks | 1 decorator |
| Get current user | Hook + context + types | `current_user()` |
| Login form | Form + handler + API route + fetch | `Auth.login_form()` |
| OAuth | Provider config + callbacks + routes | `providers=["google"]` |
| Sessions | iron-session/jose + encrypt + cookies | `session="jwt"` |
| Database sessions | Manual table + encrypt + cookies | `session="database"` |
| ORM integration | Separate setup | Uses existing `db` |
| Email verification | Custom implementation | `require_verified=True` |
| Password reset | Custom implementation | `Auth.send_reset_email()` |
| 2FA/MFA | External package | `mfa_enabled=True` |
| Role-based access | Custom middleware | `@role_required("admin")` |
| CSRF | Manual setup | Automatic |
| Rate limiting | External package | Built-in |

**Total: ~500+ lines of Next.js code → ~30 lines of PyNext**

---

### Figma Integration

Connecting Figma to the component registry would streamline designer-developer collaboration:

- [ ] **Design tokens sync** — Extract colors, typography, spacing from Figma → auto-generate Tailwind config and CSS variables
- [ ] **Component scaffolding** — Generate PyNext component skeletons from Figma component designs
- [ ] **Figma plugin** — Allow designers to mark components as "export to PyNext" with defined props/variants
- [ ] **Bi-directional linking** — Track implementation status, detect when designs drift from code

---

- [ ] **Collaborative Editing** — Real-time collaboration via Yjs
  
  **Core Concept**: Multiple users editing the same document simultaneously, with changes merging automatically using CRDTs (Conflict-free Replicated Data Types).
  
  **Architecture**:
  ```
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │  Client A   │     │  Client B   │     │  Client C   │
  │  (Y.Doc)    │     │  (Y.Doc)    │     │  (Y.Doc)    │
  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                     ┌───────┴───────┐
                     │   Provider    │
                     │  (WebSocket)  │
                     └───────┬───────┘
                             │
                     ┌───────┴───────┐
                     │    Server     │
                     │  (y-websocket)│
                     └───────────────┘
  ```
  
  **Proposed Python API**:
  ```python
  Editor(
      id="shared-doc",
      collaborative=CollaborativeConfig(
          room="document-123",
          provider="websocket",
          websocket_url="wss://sync.example.com",
          user={"name": "Alice", "color": "#ff0000"},
          awareness=True,
          persist=True,
      )
  )
  ```
  
  **Required Dependencies**:
  - Client: `yjs`, `y-websocket`, `@tiptap/extension-collaboration`
  - Server: `y-py`, `websockets`
  
  **Implementation Phases**:
  1. Basic WebSocket sync (2 users, same document)
  2. Cursor awareness and presence indicators
  3. Multiple provider support (WebSocket, WebRTC)
  4. Offline-first with IndexedDB persistence
  5. Advanced features (comments, suggestions, history)
  
  **Considerations**:
  - Scalability: 2-10 users → y-websocket; 10-50 → Redis; 50+ → custom sharding
  - Security: Room authorization, operation validation, rate limiting
  - Offline: IndexedDB for local persistence, sync on reconnect
  
  See: [docs/editor/COLLABORATIVE.md](./editor/COLLABORATIVE.md) for full architecture

---

### Component System Enhancements

Improving the component development and usage experience:

- [ ] **Visual component playground** — Storybook-like environment for testing components in isolation
- [ ] **Component versioning** — Track versions in registries, handle breaking changes
- [ ] **Automatic accessibility auditing** — Built-in a11y checks for components
- [ ] **Dark mode / theming system** — More robust theme switching and customization
- [ ] **Animation presets library** — Common animations (fade, slide, scale) ready to use
- [ ] **Responsive variant helpers** — Easier responsive props (e.g., `size={"sm": "sm", "md": "lg"}`)

---

### Developer Experience

Making PyNext easier and more enjoyable to use:

- [ ] **VS Code extension** — Component autocomplete, prop suggestions, documentation hover
- [ ] **Hot module replacement** — Update components without full page reload
- [ ] **Visual diff** — Show changes when registry components update
- [ ] **Error boundaries** — Graceful error handling in components
- [ ] **DevTools integration** — Browser extension for inspecting PyNext state

---

### Ecosystem

Building the PyNext community and ecosystem:

- [ ] **Official component marketplace** — Directory of community components
- [ ] **Community contribution process** — Guidelines for submitting components
- [ ] **Component quality badges** — Verified, accessible, tested indicators
- [ ] **Integration with Python frameworks** — First-class support for FastAPI, Django, Flask
- [ ] **Templates and starters** — Pre-built application templates

---

### Real-Time & Browser APIs

- [ ] **`use_websocket()`** — WebSocket connections with message handling
- [ ] **`use_media_query()`** — Responsive media query matching
- [ ] **`use_geolocation()`** — Browser geolocation API
- [ ] **`use_clipboard()`** — Copy/paste functionality
- [ ] **`use_window_size()`** — Viewport dimensions tracking
- [ ] **`use_scroll_position()`** — Scroll position tracking
- [ ] **`use_intersection()`** — Intersection Observer for lazy loading

---

### Performance

Optimizing for production:

- [ ] **Component-level code splitting** — Only load component JS when needed
- [ ] **Server-side streaming** — Progressive rendering for faster TTFB
- [ ] **Partial hydration improvements** — More granular island hydration
- [ ] **Static extraction** — Extract static components to pure HTML
- [ ] **Bundle analysis** — Tools to identify and reduce bundle size

---

### Testing

Making components easier to test:

- [ ] **Testing utilities** — Helpers for testing PyNext components
- [ ] **Visual regression testing** — Automated screenshot comparison
- [ ] **Accessibility testing integration** — Axe, Pa11y integration
- [ ] **Component snapshot testing** — Track HTML output changes

---

## Recently Completed

#### Phase 6: Advanced Features (P2) ✅

- [x] **CSS Modules** — Build-time scoping with unique hash prefixes (docs: [CSS_MODULES.md](features/CSS_MODULES.md))
- [x] **MDX Support** — Markdown with Python components, frontmatter, TOC extraction (docs: [MDX.md](features/MDX.md))
- [x] **Proxy Configuration** — Decorator-based API with path rewriting, WebSocket support (docs: [PROXY.md](features/PROXY.md))
- [x] **Instrumentation** — OpenTelemetry traces, Prometheus metrics, structured logging (docs: [INSTRUMENTATION.md](features/INSTRUMENTATION.md))
- [x] **Edge Runtime** — Adapters for Cloudflare, Vercel, Deno, Bun (docs: [EDGE.md](features/EDGE.md))

#### Phase 5: Browser APIs (P1) ✅ COMPLETED

All return fine-grained signals (no component re-renders):

- [x] **`use_websocket(url, on_message)`** → `WebSocketHandle` ✅
- [x] **`use_media_query("(max-width: 768px)")`** → `Signal[bool]` ✅
- [x] **`use_geolocation(watch=True)`** → `GeolocationHandle` ✅
- [x] **`use_clipboard()`** → `ClipboardHandle` ✅
- [x] **`use_window_size()`** → `Signal[WindowSize]` ✅
- [x] **`use_scroll_position()`** → `Signal[ScrollPosition]` ✅
- [x] **`use_intersection(element_id)`** → `Signal[bool]` ✅

**Implementation Details:**
- Files: `pynext/core/client.py`, `pynext/runtime/browser.js`, `pynext/runtime/websocket.js`
- Features: Auto-reconnect WebSocket, RAF-throttled scroll/resize, memoized media queries, permission-aware geolocation
- Tests: **328 comprehensive unit tests** (`tests/unit/test_browser_apis.py`)
  - 24 WebSocket base tests + 30 edge cases
  - 15 Media Query base tests + 25 edge cases
  - 20 Geolocation base tests + 25 edge cases
  - 15 Clipboard base tests + 25 edge cases
  - 10 Window Size base tests + 20 edge cases
  - 15 Scroll Position base tests + 25 edge cases
  - 15 Intersection Observer base tests + 25 edge cases
  - 30 Integration tests (multiple hooks together)
  - 20 Error handling tests
  - 4 JavaScript runtime file tests
- Docs: [docs/features/BROWSER_APIS.md](./features/BROWSER_APIS.md)

#### Phase 4: Developer Experience (P1)

- [x] **Fast File Watching** — <50ms dev reload ✅ COMPLETED
  - Files: `pynext/server/watcher.py`, `pynext/server/dev.py`, `pynext/runtime/dev-reload.js`
  - APIs: `FileWatcher`, `FileChange`, `ChangeType`, `DevServer`, `create_watcher()`, `watch_once()`
  - Features: Rust-based watching (watchfiles), WebSocket push, intelligent reload classification (hot/css/full/none), auto-reconnect with overlay, heartbeat keep-alive
  - Performance: <5ms file detection, <50ms total reload
  - Tests: **146 comprehensive unit tests** (ChangeType, FileChange, FileWatcher, DevServer, edge cases, performance benchmarks, async behavior, JS client validation)
  - Docs: [docs/features/DEV_SERVER.md](./features/DEV_SERVER.md)

- [x] **Component Generator CLI** — Scaffold pages/components/APIs ✅ COMPLETED
  - Files: `pynext/generator/` (core.py, templates.py, prompts.py, ai.py, validators.py)
  - Commands: `pynext generate page`, `pynext g component`, `pynext g api`, etc.
  - All 11 types: page, component, island, api, layout, template, loading, error, middleware, action, hook
  - Modes: Interactive (default), Non-interactive (--yes), AI-assisted (--ai)
  - Templates: Minimal (--minimal) and Full (--full)
  - AI Features: Leading questions, completeness evaluation, follow-up questions
  - Tests: **106 comprehensive tests** including:
    - Unit tests: validators, templates, core logic, prompts, CLI
    - **19 real API integration tests** with Anthropic Claude:
      - Page, component, island, API, action, hook generation
      - Completeness evaluation (sufficient/needs-more scenarios)
      - Code quality checks (Tailwind, docstrings, syntax validation)
  - Docs: [docs/features/GENERATOR.md](./features/GENERATOR.md)

  - [x] **PyTest Utilities** — Testing helpers ✅ COMPLETED
  - Files: `pynext/testing/` module (render.py, assertions.py, accessibility.py, snapshots.py, async_utils.py, visual.py, benchmarks.py, coverage.py)
  - APIs: `render()`, `assert_text()`, `assert_has_class()`, `assert_accessible()`, `assert_snapshot()`, `assert_visual_match()`, `@benchmark`, `wait_for()`
  - Features: 20+ assertion functions, WCAG 2.1 AA accessibility testing, snapshot testing, visual regression, async testing, performance benchmarks, signal/component/branch coverage
  - Tests: **128 comprehensive unit tests**
  - Docs: [docs/features/TESTING.md](./features/TESTING.md)

- [x] **Linting Integration** — `pynext lint` with ruff ✅ COMPLETED
  - Files: `pynext/lint/` module (runner.py, config.py, lsp.py, rules/)
  - Commands: `pynext lint`, `pynext lint --fix`, `pynext lint init`, `pynext lint vscode`, `pynext lint rules`, `pynext lint explain`, `pynext lint lsp`
  - Rules: **10 PyNext-specific rules (PNX001-010)** — Unused Signal, Signal in loop, Missing component return, Invalid prop type, Server import in island, Invalid route name, Missing page export, Untracked effect, Direct signal mutation, Missing metadata
  - Features: Zero-config defaults, ruff integration (Rust-powered), auto-fix, LSP server for any editor, VS Code integration
  - Tests: **70+ comprehensive unit tests**
  - Docs: [docs/features/LINTING.md](./features/LINTING.md)


#### Phase 3: SEO & Assets (P1)

- [x] **Sitemap Generation** — Build-time `sitemap.xml` ✅ COMPLETED
  - Files: `pynext/seo/sitemap.py`, `pynext/seo/__init__.py`
  - APIs: `@sitemap(priority, changefreq, lastmod, include)`, `SitemapGenerator`, `SitemapEntry`
  - Features: Auto-discovery from router, dynamic route support via `get_sitemap_params()`, automatic sitemap index at 50k URLs
  - CLI: `pynext sitemap generate/validate/preview`
  - Performance: 10x faster than Next.js (router integration, streaming XML)
  - Tests: 82 unit tests
  - Docs: [docs/features/SITEMAP.md](./features/SITEMAP.md)

- [x] **Robots.txt** — Configurable robots file ✅ COMPLETED
  - Files: `pynext/seo/robots.py`
  - APIs: `RobotsConfig`, `RobotsRule`, `robots_allow_all()`, `robots_disallow_all()`
  - CLI: `pynext robots generate/preview/validate`
  - Features: Auto sitemap URL, host directive, crawl-delay support

- [x] **App Icons Convention** — Auto-detect favicon, icon.png, apple-icon.png ✅ COMPLETED
  - Files: `pynext/pwa/icons.py`
  - APIs: `Icon`, `AppIcons`, `IconDetector`, `detect_icons()`, `create_icons()`
  - Features: Auto-detect from public/, size from filename, MIME type detection
  - CLI: `pynext icons detect/validate`
  - Tests: 74 unit tests
  - Docs: [docs/features/PWA.md](./features/PWA.md)

- [x] **PWA Manifest** — `manifest.json` generation ✅ COMPLETED
  - Files: `pynext/pwa/manifest.py`
  - APIs: `PWAManifest`, `ManifestIcon`, `Shortcut`, `pwa_minimal()`, `pwa_full()`
  - Features: Auto-merge with detected icons, shortcuts, categories
  - CLI: `pynext manifest generate/preview`, `pynext pwa validate`
  - Server: `/manifest.json` endpoint

- [x] **Dynamic OG Images** — Generate OG images at request time ✅ COMPLETED
  - Files: `pynext/og/canvas.py`, `pynext/og/templates.py`, `pynext/og/decorator.py`, `pynext/og/renderer.py`
  - APIs: `@og_image`, `OGCanvas`, `OGTemplate`, `OGRenderer`
  - Features: Chainable canvas API, 25+ gradient presets, 8 pre-built templates, ISR caching
  - CLI: `pynext og preview/generate/validate`
  - Server: `/og/{path}.png` endpoint with auto-caching
  - Tests: 64 unit tests
  - Docs: [docs/features/OG_IMAGES.md](./features/OG_IMAGES.md)

#### Phase 2: Environment & Config (P0) ✅ COMPLETED

- [x] **Route Segment Config** — Per-route configuration ✅ COMPLETED
  - Files: `pynext/core/route_config.py`
  - APIs: `@route_config(dynamic, revalidate, cache, tags, runtime, max_duration)`
  - Enums: `Dynamic`, `Cache`, `Runtime` for type-safe IDE autocomplete
  - Shortcuts: `@static_route`, `@dynamic_route`, `@edge_route`, `@cached_route`, `@no_cache_route`
  - Performance: Config parsed at import (0ms runtime), O(1) lookup
  - Tests: 84 unit tests
  - Docs: [docs/features/ROUTE_CONFIG.md](./features/ROUTE_CONFIG.md)

- [x] **Environment Variables** — Full `.env` file support ✅
  - Files: `pynext/env_module.py`, `pynext/env/loader.py`, `pynext/env/schema.py`, `pynext/env/client.py`, `pynext/build/env.py`
  - Load order: `.env` → `.env.local` → `.env.{mode}` → `.env.{mode}.local` → OS
  - APIs: `env.DATABASE_URL`, `env.get_int()`, `env.get_bool()`, `env.get_list()`, `env.get_json()`
  - Client: `PYNEXT_PUBLIC_*` vars exposed via build-time inlining OR runtime fetch
  - Schema: `EnvSchema`, `Var(type, required, default, secret, validator, choices)`
  - CLI: `pynext env list`, `pynext env check`, `pynext env validate`, `pynext env init`
  - Performance: 16x faster than Next.js (3ms vs 50ms), 0ms client access
  - Tests: 103 unit tests
  - Docs: [docs/features/ENVIRONMENT.md](./features/ENVIRONMENT.md)

#### Phase 1: File Conventions (P0) ✅ COMPLETED

- [x] **Route Groups `(folder)`** — Organize routes without affecting URLs ✅
  - Files: `pynext/router/groups.py`
  - APIs: `is_route_group()`, `strip_groups()`, `RouteGroup`, `GroupRegistry`
  - Behavior: `pages/(marketing)/about/page.py` → `/about`
  - Performance: O(1) lookup (78ns)
  - Docs: [docs/features/ROUTE_GROUPS.md](./features/ROUTE_GROUPS.md)

- [x] **Template `template.py`** — Layouts that remount on navigation ✅
  - Files: `pynext/core/template.py`, `pynext/runtime/template.js`
  - APIs: `@template(animate=True, duration=200)`, `TransitionType`
  - Performance: <1ms render (0.8μs)
  - Docs: [docs/features/TEMPLATE.md](./features/TEMPLATE.md)

- [x] **Error Pages `forbidden.py`, `unauthorized.py`** — Custom 403/401 pages ✅
  - Files: `pynext/core/errors.py`
  - APIs: `ForbiddenError`, `UnauthorizedError`, `@forbidden_page`, `@unauthorized_page`
  - Performance: Zero JS (4μs render)
  - Docs: [docs/features/ERROR_PAGES.md](./features/ERROR_PAGES.md)

- [x] **`src/` Folder Support** — Auto-detect `src/pages/` structure ✅
  - Files: `pynext/core/paths.py`
  - APIs: `resolve_paths()`, `ProjectPaths`, `ensure_structure()`
  - Performance: Auto-detect (40μs)
  - Docs: [docs/features/PROJECT_STRUCTURE.md](./features/PROJECT_STRUCTURE.md)


#### Phase 1: File Conventions (P0) ✅ COMPLETED

All Phase 1 features implemented with 192 unit tests + 46 benchmark tests.

**Performance Results** (measured):
| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Route lookup | O(1) | 78ns (O(1) confirmed) | ✅ |
| Template render | <5ms | 0.8μs (6000x faster) | ✅ |
| Error page render | <10ms | 4μs (2500x faster) | ✅ |
| Path resolution | <1ms | 40μs (25x faster) | ✅ |

- [x] **Route Groups `(folder)`** — Organize routes without affecting URLs ✅
  - Files: `pynext/router/groups.py`
  - APIs: `is_route_group()`, `strip_groups()`, `get_group_name()`, `scan_groups()`, `GroupRegistry`
  - Docs: [Route Groups](./features/ROUTE_GROUPS.md)

- [x] **Template `template.py`** — Layouts that remount on navigation ✅
  - Files: `pynext/core/template.py`, `pynext/runtime/template.js`
  - APIs: `@template(animate=True, duration=200, transition="fade")`, `TransitionType`
  - Docs: [Template](./features/TEMPLATE.md)

- [x] **Error Pages `forbidden.py`, `unauthorized.py`** — Custom 403/401/404 pages ✅
  - Files: `pynext/core/errors.py`
  - APIs: `UnauthorizedError`, `ForbiddenError`, `NotFoundError`, `@unauthorized_page`, `@forbidden_page`
  - Docs: [Error Pages](./features/ERROR_PAGES.md)

- [x] **`src/` Folder Support** — Auto-detect `src/pages/` structure ✅
  - Files: `pynext/core/paths.py`
  - APIs: `resolve_paths()`, `detect_structure()`, `ensure_structure()`, `find_project_root()`
  - Docs: [Project Structure](./features/PROJECT_STRUCTURE.md)

### Real-Time & Browser APIs

Native Python APIs for browser-specific features:

- [x] **`use_event_source()`** — Server-Sent Events (SSE) with automatic reconnection ✅ COMPLETED
  - Connect to SSE endpoints from Python
  - Event handlers via dict mapping
  - Auto-reconnect on error
  - See: [docs/features/SSE.md](./features/SSE.md)

- [x] **`use_visibility()`** — Track document visibility (for smart polling) ✅ COMPLETED
  - Returns signal that updates on tab switch
  - Pause expensive operations when hidden
  - See: [docs/features/VISIBILITY.md](./features/VISIBILITY.md)

- [x] **`use_online()`** — Network status detection ✅ COMPLETED
  - Returns signal for online/offline state
  - Disable features when offline
  - See: [docs/features/ONLINE_STATUS.md](./features/ONLINE_STATUS.md)

### Editor Enhancements

Extend the Rich Text Editor (`pynext.editor`) with advanced features:

- [x] **useEditor() Python API** — Programmatic editor control from Python ✅ COMPLETED
  - `get_content()`, `set_content()`, `focus()`, `clear()`
  - `insert_text()`, `toggle_bold()`, `toggle_italic()`, etc.
  - `get_markdown()`, `set_markdown()` (when markdown extension enabled)
  - See: [docs/editor/USE_EDITOR.md](./editor/USE_EDITOR.md)

- [x] **Markdown Extension** — Full markdown support via Tiptap ✅ COMPLETED
  - Parse markdown input, export to markdown
  - `MarkdownEditor` convenience component
  - `TiptapLoader(markdown=True)` for library support
  - See: [docs/editor/MARKDOWN.md](./editor/MARKDOWN.md)

- [x] **Mentions Extension** — @mention support ✅ COMPLETED
  - Customizable suggestion list with `MentionConfig`
  - Server action integration for user search
  - Configurable trigger character (@, #, etc.)
  - See: [docs/editor/MENTIONS.md](./editor/MENTIONS.md)

- [x] **Slash Commands** — / command palette ✅ COMPLETED
  - Quick formatting commands (/h1, /bold, /code)
  - Custom command registration with `SlashCommand`
  - `DEFAULT_SLASH_COMMANDS` for common actions
  - See: [docs/editor/SLASH_COMMANDS.md](./editor/SLASH_COMMANDS.md)


### Advanced Components (Phase 2+) — COMPLETED ✓

All 12 advanced components have been implemented:

- [x] **Skeleton** — Loading placeholder animations
- [x] **Tooltip** — Contextual hover information
- [x] **Popover** — Floating content panels
- [x] **Toast / Sonner** — Non-blocking notifications
- [x] **Sheet / Drawer** — Slide-out panels
- [x] **Combobox / Autocomplete** — Searchable select with filtering
- [x] **Command palette** — cmdk-style command menu (⌘K)
- [x] **Calendar / DatePicker** — Date selection with range support
- [x] **Data Table** — Sortable, filterable, paginated tables
- [x] **File upload** — Drag-and-drop with preview
- [x] **Charts** — Integration with Chart.js (`pynext.charts`)
- [x] **Rich text editor** — Tiptap integration (`pynext.editor`)

### Phase 2: Client Runtime ✓

- [x] Keyboard shortcuts (`@on_keydown`, `@on_key_sequence`)
- [x] Theme management (`ThemeProvider`, `ThemeToggle`, `use_theme`)
- [x] Focus management (`FocusTrap`, `RovingFocus`, `SkipLinks`)
- [x] Storage signals (`use_storage` for localStorage/sessionStorage)
- [x] Client effects (`@client_effect` for browser-side logic)
- [x] Lambda transpilation (Python → JavaScript for event handlers)

### Phase 1: Core UI System ✓

- [x] Tailwind utilities (`tw`, `cn`)
- [x] ShadCN component port (Button, Card, Dialog, etc.)
- [x] React wrapper for escape hatch
- [x] Component registry system
- [x] Client-side interactivity runtime

---

## Contributing

Have an idea that's not on this list? Open an issue or discussion to propose new features!

