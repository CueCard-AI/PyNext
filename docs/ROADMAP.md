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
**Total Test Suite**: 10,813+ tests
**Status**: Next.js Feature Parity Achieved 🎉

**Data Layer Status**: Phases 1-6 Complete + Phase 7.1-7.5 Complete (5,625+ tests including live queries, bidirectional relationships, loading strategies, many-to-many relationships, cascade options, and custom join conditions)

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

**Status:** Phases 5.1-5.7 Complete ✅ (3,199 tests), Phase 6 Complete ✅ (389 tests), Phase 7.1 Complete ✅ (182 tests), Phase 7.2 Complete ✅ (437 tests), Phase 7.3 Complete ✅ (329 tests), Phase 7.4 Complete ✅ (601 tests), Phase 7.5 Complete ✅ (488 tests)

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

##### Phase 6: Reactive Frontend Integration ✅ COMPLETE (389 tests)

**Status:** Complete with comprehensive implementation and documentation.

- [x] **Model.live()** — Queries that auto-update when data changes ✅
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

**6.1 Core Live Query API** ✅
- [x] `LiveQuery` class extending `Signal` with `loading` and `error` signals
- [x] Chainable query methods: `.where()`, `.order_by()`, `.limit()`, `.offset()`, `.select()`
- [x] `QuerySignature` for query deduplication
- [x] `LiveQueryConfig` for transport, detection, granularity settings
- [x] Files: `pynext/db/live/query.py`, `pynext/db/live/config.py`

**6.2 Change Detection** ✅
- [x] `ChangeDetector` abstract base with `ChangeEvent` dataclass
- [x] `PostgresNotifyDetector` - PostgreSQL LISTEN/NOTIFY integration
- [x] `SupabaseRealtimeDetector` - Supabase Realtime integration
- [x] `PollingDetector` - Fallback polling strategy
- [x] `DetectorRegistry` with auto-selection based on available infrastructure
- [x] Files: `pynext/db/live/detection/` (base.py, postgres.py, supabase.py, polling.py, registry.py)

**6.3 Transport Layer** ✅
- [x] `Transport` abstract base with message queuing
- [x] `SSETransport` - Server-Sent Events implementation
- [x] `WebSocketTransport` - WebSocket with `websocket.js` integration
- [x] `TransportSelector` with auto-selection (prefer WS if available)
- [x] `TransportManager` for connection lifecycle management
- [x] Files: `pynext/db/live/transport/` (base.py, sse.py, websocket.py, selector.py, manager.py)

**6.4 Update Strategies** ✅
- [x] `UpdateStrategy` abstract base with `UpdateResult`
- [x] `SurgicalUpdateStrategy` - Row-level INSERT/UPDATE/DELETE
- [x] `FullRefreshStrategy` - Complete data refresh with debouncing
- [x] `StrategySelector` with auto-selection based on query complexity
- [x] Files: `pynext/db/live/updates/` (base.py, surgical.py, refresh.py, selector.py)

**6.5 Subscription Manager** ✅
- [x] `SubscriptionManager` for server-side subscription tracking
- [x] Query deduplication via `QuerySignature`
- [x] Client subscription tracking and cleanup
- [x] Files: `pynext/db/live/subscriptions.py`

**6.6 PostgreSQL Integration** ✅
- [x] `TriggerManager` for NOTIFY trigger creation/management
- [x] `PostgresAdapter` methods: `get_listen_connection()`, `supports_listen_notify()`, `execute_trigger_sql()`, `check_trigger_exists()`
- [x] `enable_live_queries()` / `disable_live_queries()` convenience functions
- [x] Files: `pynext/db/live/triggers.py`, `pynext/db/adapters/postgres.py`

**6.7 Supabase Integration** ✅
- [x] Native Supabase Realtime support via `SupabaseRealtimeDetector`
- [x] Automatic channel management and subscription handling

**6.8 Client Runtime** ✅
- [x] `pynext/runtime/live.js` - Client-side live query manager
- [x] Integration with `pynext/runtime/websocket.js` for shared connections
- [x] Auto-reconnection and message queuing

**6.9 Server Integration** ✅
- [x] SSE endpoint: `/_pynext/live/sse`
- [x] WebSocket endpoint: `/_pynext/live/ws`
- [x] Subscription endpoints: `/_pynext/live/subscribe`, `/_pynext/live/unsubscribe`
- [x] Files: `pynext/server/live.py`

**Documentation:** [docs/database/12-live-queries.md](./database/12-live-queries.md) (672 lines)

**Test Coverage:** 389 tests across 8 test files:
- `test_live_query.py`, `test_live_config.py`, `test_live_detection.py`
- `test_live_transport.py`, `test_live_updates.py`, `test_live_subscriptions.py`
- `test_live_server.py`, `test_live_integration.py`

##### Phase 7: Advanced Relationships (1,549+ tests)

A complete relationship system that matches SQLAlchemy's power while keeping PyNext's simple definition advantage.

**7.1 Bidirectional Relationships (backref)** ✅
- [x] `backref` parameter for automatic reverse relationship creation
- [x] `back_populates` for explicit bidirectional linking
- [x] Automatic sync when either side is modified
- [x] Cascade relationship updates through the graph
- [x] `BackrefConfig` dataclass for configuration
- [x] `BackrefRegistry` for tracking bidirectional pairs
- [x] `RelationshipSyncManager` with loop prevention via `ContextVar`
- [x] `SyncedList` collection with automatic sync on `append`, `remove`, `extend`, `clear`, `pop`, `insert`, `__setitem__`, `__delitem__`
- [x] Forward reference resolution for models defined in any order
- [x] Safe handling of unsaved objects (no `id` attribute)

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

**Files Created/Modified:**
- `pynext/db/relationships/__init__.py` - Package exports
- `pynext/db/relationships/backref.py` - BackrefConfig, BackrefRegistry, RelationshipSyncManager
- `pynext/db/relationships/collections.py` - SyncedList implementation
- `pynext/db/relationships/core.py` - Updated with backref/back_populates support
- `pynext/db/table.py` - Updated `__eq__`/`__hash__` for unsaved objects

**Documentation:** [docs/database/11-relationships.md](./database/11-relationships.md) (788 lines)

**Test Coverage:** 182 tests across 4 test files:
- `test_backref_basic.py` - BackrefConfig, BackrefRegistry, descriptor attributes (58 tests)
- `test_backref_sync.py` - Bidirectional sync behavior, loop prevention (44 tests)
- `test_backref_collections.py` - SyncedList operations (40 tests)
- `test_backref_edge_cases.py` - Null values, self-referential, performance (40 tests)

**7.2 Loading Strategies** ✅ (437 tests)
- [x] `lazy="select"` - Default lazy loading (query on access)
- [x] `lazy="joined"` - JOIN in same query (eager)
- [x] `lazy="subquery"` - Separate subquery (good for collections)
- [x] `lazy="selectin"` - SELECT IN (ids) (best for batches)
- [x] `lazy="raise"` - Raise error if accessed (prevent N+1)
- [x] `lazy="dynamic"` - Return query instead of results
- [x] Query-level override with `options()` and chaining
- [x] `LazyLoadError` for N+1 prevention
- [x] Documentation: `docs/database/13-loading-strategies.md`

```python
class User(Table):
    posts: List[Post] = has_many(Post, lazy="selectin")  # Best for batches
    profile: Profile = has_one(Profile, lazy="joined")    # Eager load
    audit_logs: List[Log] = has_many(Log, lazy="dynamic") # Query builder

# Query-level override
users = await User.select().options(
    selectinload("posts").joinedload("author"),
    joinedload("profile"),
    raiseload("audit_logs"),  # Raises if accessed
)
```

**7.3 Many-to-Many Relationships** ✅ COMPLETE (329 tests)
- [x] `through` parameter for junction/association tables
- [x] Support for extra columns on junction table
- [x] Association proxy for direct access through relationship
- [x] Bidirectional many-to-many with backref
- [x] Loading strategies (select, selectin, raise, dynamic)
- [x] DynamicManyToMany query builder for large collections

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

**7.4 Cascade Options** ✅ (601 tests)
- [x] `on_delete="cascade"` - Delete related when parent deleted
- [x] `on_delete="nullify"` - Set FK to NULL when parent deleted
- [x] `on_delete="protect"` - Raise error if related exist
- [x] `on_delete="none"` - Do nothing (default)
- [x] `CascadeOptions` for fine-grained control (on_save, on_delete, on_orphan, on_merge)
- [x] `CascadeOptions.all()`, `.delete_only()`, `.delete_orphan()`, `.save_only()` presets
- [x] `CascadeManager` for executing cascades
- [x] `ProtectedDeleteError` for protected relationships
- [x] Hooked into `Table.delete()` and `Table.save()`
- [x] Orphan handling in `SyncedList` and `ManyToManyCollection`

```python
# PyNext - Simpler than SQLAlchemy!
class User(Table):
    # Simple preset - delete posts when user deleted
    posts: List[Post] = has_many(Post, on_delete="cascade")
    
    # Nullify - set FK to NULL (anonymous content)
    comments: List[Comment] = has_many(Comment, on_delete="nullify")
    
    # Protect - cannot delete if has related
    orders: List[Order] = has_many(Order, on_delete="protect")
    
    # Fine-grained control
    logs: List[Log] = has_many(Log, cascade=CascadeOptions(
        on_save=True,     # Save logs when user saved
        on_delete=True,   # Delete logs when user deleted
        on_orphan=True,   # Delete log when removed from collection
    ))

# Usage - just works!
await user.delete()  # Cascades automatically based on on_delete

# Protect check
try:
    await user.delete()
except ProtectedDeleteError as e:
    print(f"Cannot delete: has {e.related_count} {e.relationship}")
```

**7.4.1 Database-Level Cascade Integration** ✅
- [x] Add `fk_on_delete` attribute to `FieldInfo`
- [x] Sync relationship `on_delete` to FK field in `TableMeta`
- [x] Update `PostgresAdapter.create_table()` to generate FK constraints with `ON DELETE`
- [x] Add error translation for FK violations → `ProtectedDeleteError`
- [x] Add `get_foreign_keys()` and `has_constraint()` introspection methods
- [x] Add `add_fk_constraint()`, `alter_fk_on_delete()`, `drop_fk_constraint()` methods
- [x] Add FK method signatures to base adapter
- [x] Update `CascadeManager` for hybrid execution (DB handles on_delete)
- [x] 123 tests for DB-level cascade integration
- [x] Documentation with FK introspection and migration examples

```python
# Same simple code - now with database-level performance!
class User(Table):
    posts: List[Post] = has_many(Post, on_delete="cascade")

# PyNext auto-generates PostgreSQL FK constraints:
# CREATE TABLE "posts" (
#     "author_id" INTEGER NOT NULL REFERENCES "users"("id") ON DELETE CASCADE
# )

# Delete 10,000 posts in 1 query instead of 10,001!
await user.delete()  # Database handles cascade automatically

# Introspect FK constraints
fks = await adapter.get_foreign_keys("posts")
# [{"constraint_name": "posts_author_id_fkey", "on_delete": "CASCADE", ...}]

# Migrate FK constraints
await adapter.alter_fk_on_delete("posts", "author_id", "SET NULL")
```

**7.5 Custom Join Conditions** ✅ Complete (488 tests)
- [x] Condition functions: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `like`, `ilike`, `is_in`, `not_in`, `is_null`
- [x] Tuple syntax: `("field", ">=", value)` for SQL-like conditions
- [x] `filter` parameter on all relationship types (`has_many`, `has_one`, `belongs_to`, `many_to_many`)
- [x] Date/time helpers: `days_ago`, `hours_ago`, `weeks_ago`, `start_of_today`, etc.
- [x] Full integration with loading strategies
- [x] Comprehensive documentation

**Why This is Better Than SQLAlchemy:**
```python
# SQLAlchemy (string-based, error-prone, no IDE help):
class User(Base):
    active_posts = relationship(
        "Post",
        primaryjoin="and_(User.id == Post.author_id, Post.is_active == true())"
    )

# PyNext (type-safe, IDE autocomplete, two syntaxes):
from pynext.db import eq, gte, days_ago

class User(Table):
    # Function syntax (IDE autocomplete)
    active_posts: List[Post] = has_many(Post, filter=[
        eq("is_active", True)
    ])
    
    # Tuple syntax (SQL-like)
    recent_posts: List[Post] = has_many(Post, filter=[
        ("created_at", ">=", days_ago(30))
    ])
    
    # Mix both + multiple conditions
    trending: List[Post] = has_many(Post, filter=[
        eq("is_active", True),
        ("views", ">=", 100),
        gte("created_at", days_ago(7))
    ])
```

**Files:**
- `pynext/db/relationships/conditions.py` — Condition class and functions
- `pynext/db/relationships/filter.py` — RelationshipFilter class
- `pynext/db/relationships/helpers.py` — Date/time helper functions
- `docs/database/17-custom-join-conditions.md` — Comprehensive documentation

**7.6 Self-Referential Relationships** ✅ COMPLETE (315 tests)
- [x] Parent-child hierarchies (e.g., categories, org charts)
- [x] Adjacency list pattern with auto-detection
- [x] Path enumeration helpers (path, path_ids)
- [x] Recursive query support (CTE for PostgreSQL, app-level fallback)
- [x] TreeMixin with all tree traversal methods
- [x] Move operations with cycle prevention

```python
from pynext.db import Table, TreeMixin

class Category(Table, TreeMixin):
    name: str
    parent_id: Optional[int]  # Auto-detected as self-referential
    
    # All these methods are now available:
    # Sync properties:
    # - is_root: bool
    # - path: str ("Electronics/Computers/Laptops")
    # - path_ids: List[int]
    
    # Async methods:
    # - ancestors() -> List[Category]
    # - descendants() -> List[Category]
    # - root() -> Category
    # - depth() -> int
    # - is_leaf() -> bool
    # - siblings() -> List[Category]
    # - subtree() -> List[Category]
    # - children() -> List[Category]
    # - parent() -> Optional[Category]
    # - move_to(new_parent) -> None
    # - make_root() -> None
```

**Files:**
- `pynext/db/relationships/tree.py` — TreeMixin class with all tree methods
- `pynext/db/relationships/tree_query.py` — CTE query builders for PostgreSQL
- `docs/database/18-self-referential.md` — Comprehensive documentation

**7.7 Polymorphic Relationships** ✅
- [x] Single table inheritance with `@polymorphic("type")` decorator
- [x] Joined table inheritance with `strategy="joined"`
- [x] Concrete table inheritance with `strategy="concrete"`
- [x] Generic foreign keys with `Union[A, B, C] = generic_fk()`
- [x] Automatic type inference from discriminator values
- [x] `without_polymorphism()` for explicit control
- [x] `where_target_type()` for generic FK filtering

```python
from pynext.db.polymorphic import polymorphic, generic_fk
from typing import Union

# Single Table Inheritance (default)
@polymorphic("type")
class Content(Table):
    title: str

@polymorphic.subtype("article")
class Article(Content):
    body: str

@polymorphic.subtype("video")
class Video(Content):
    url: str
    duration: int

# Automatic type inference
contents = await Content.all()  # [Article(...), Video(...), ...]
articles = await Article.all()  # Only articles

# Generic Foreign Keys
class Comment(Table):
    content: str
    target: Union[Article, Video, Photo] = generic_fk()

comment = await Comment.create(content="Great!", target=article)
target = await comment.target  # Returns Article, Video, or Photo
```

**Files Created:**
- `pynext/db/polymorphic/__init__.py` — Package exports
- `pynext/db/polymorphic/base.py` — `@polymorphic` and `@polymorphic.subtype` decorators
- `pynext/db/polymorphic/registry.py` — Type registry for polymorphic models
- `pynext/db/polymorphic/strategies.py` — STI, Joined, Concrete strategies
- `pynext/db/polymorphic/generic_fk.py` — Union-type generic foreign keys
- `pynext/db/polymorphic/query.py` — Query extensions for polymorphic
- `docs/database/19-polymorphic.md` — Comprehensive documentation

**Test Coverage:** 438 tests across 15 test files:
- `test_poly_sti_basic.py`, `test_poly_sti_queries.py`, `test_poly_sti_advanced.py`
- `test_poly_joined_basic.py`, `test_poly_joined_queries.py`
- `test_poly_concrete_basic.py`, `test_poly_concrete_queries.py`
- `test_poly_generic_fk.py`, `test_poly_gfk_advanced.py`
- `test_poly_registry.py`, `test_poly_query.py`, `test_poly_edge_cases.py`
- `test_poly_integration.py`, `test_poly_patterns.py`, `test_poly_sql.py`
- `test_poly_strategy.py`, `test_poly_type_checking.py`
- `test_poly_instantiation.py`, `test_poly_decorator.py`, `test_poly_advanced.py`

**7.8 Relationship Events/Hooks** ✅ COMPLETE
- [x] `@on_append` - When item added to collection
- [x] `@on_remove` - When item removed from collection
- [x] `@on_set` - When scalar relationship set
- [x] `@before_delete` - Before cascade delete

```python
class User(Table):
    posts: List[Post] = has_many(Post)
    profile: Profile = has_one(Profile)
    
    @on_append("posts")
    def on_post_added(self, post: Post):
        """Called when a post is added to user.posts."""
        send_notification(f"New post by {self.name}")
    
    @on_remove("posts")
    def on_post_removed(self, post: Post):
        """Called when a post is removed."""
        log_audit(f"Post {post.id} removed from {self.name}")
    
    @on_set("profile")
    def on_profile_changed(self, old_profile: Profile, new_profile: Profile):
        """Called when profile is set or changed."""
        if old_profile and new_profile:
            log_audit(f"Profile changed")
    
    @before_delete()
    def cleanup(self):
        """Called before cascade delete starts."""
        archive_user_data(self)
```

**Implementation Files:**
- `pynext/db/relationships/hooks.py` - Core decorators and HookRegistry
- `pynext/db/relationships/hook_executor.py` - Synchronous hook execution
- `docs/database/20-relationship-hooks.md` - Comprehensive documentation

**Tests (249 tests):**
- `test_hook_on_append.py` - on_append hook tests
- `test_hook_on_remove.py` - on_remove hook tests  
- `test_hook_on_set.py` - on_set hook tests
- `test_hook_before_delete.py` - before_delete hook tests
- `test_hook_registry.py` - HookRegistry tests
- `test_hook_execution.py` - Execution order and error handling tests
- `test_hook_edge_cases.py` - Edge cases and inheritance tests
- `test_hook_integration.py` - Real-world pattern tests

**7.9 Association Proxy** ✅
- [x] Access attributes through relationships
- [x] Simplify many-to-many access
- [x] Scalar and collection proxies
- [x] Dot-notation path traversal
- [x] Creator functions for mutations
- [x] Auto-detect scalar vs collection
- [x] 323 comprehensive tests

```python
class User(Table):
    enrollments: List[Enrollment] = has_many(Enrollment)
    
    # Access course names directly through enrollments
    course_names: List[str] = association_proxy("enrollments", "course.name")
    
    # Access courses directly
    courses: List[Course] = association_proxy("enrollments", "course")
    
    # With creator for adding
    courses_with_add: List[Course] = association_proxy(
        "enrollments",
        "course",
        creator=lambda c: Enrollment(course=c)
    )

class Post(Table):
    author: User = belongs_to(User, "author_id")
    
    # Scalar proxy - returns single value, not list!
    author_name: str = association_proxy("author", "name")

# Usage
user.course_names  # ["Math", "Physics", "Chemistry"]
user.courses       # [Course(...), Course(...), ...]
post.author_name   # "Alice" (string, not list)
```

**Files Created:**
- `pynext/db/relationships/association_proxy.py` - Core implementation
- `docs/database/21-association-proxy.md` - Comprehensive documentation

**Test Files (323 tests):**
- `test_assoc_proxy_basic.py` - Basic proxy functionality
- `test_assoc_proxy_collection.py` - Collection operations
- `test_assoc_proxy_scalar.py` - Scalar proxy behavior
- `test_assoc_proxy_nested.py` - Nested path traversal
- `test_assoc_proxy_creator.py` - Creator functions
- `test_assoc_proxy_m2m.py` - Many-to-many integration
- `test_assoc_proxy_belongs_to.py` - belongs_to/has_one proxies
- `test_assoc_proxy_caching.py` - Caching behavior
- `test_assoc_proxy_edge_cases.py` - Edge cases
- `test_assoc_proxy_integration.py` - Real-world patterns

**7.10 Relationship Ordering** ✅
- [x] Default ordering on relationships
- [x] Multiple order columns
- [x] Ascending/descending
- [x] NULLS FIRST/LAST support
- [x] Query-time ordering override
- [x] OrderSpec class and OrderingConfig
- [x] Integration with has_many and many_to_many
- [x] SQL generation with table aliases

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
    
    # NULLS handling
    tasks: List[Task] = has_many(
        Task,
        order_by=["priority desc nulls first", "due_date nulls last"]
    )
```

**Test Files (382 tests):**
- `test_order_spec.py` - OrderSpec parsing and validation
- `test_order_has_many.py` - has_many with ordering
- `test_order_m2m.py` - many_to_many ordering
- `test_order_eager_load.py` - Eager loading with ordering
- `test_order_multiple.py` - Multiple order columns
- `test_order_direction.py` - asc/desc handling
- `test_order_nulls.py` - NULLS FIRST/LAST
- `test_order_override.py` - Query-time override
- `test_order_edge_cases.py` - Edge cases
- `test_order_integration.py` - Real-world patterns

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
| 7.4 Cascade | 601 | All cascade types, combinations, patterns ✅ |
| 7.5 Custom joins | 80 | Expressions, filters, complex |
| 7.6 Self-referential | 315 | Hierarchies, recursion, CTE, app-level |
| 7.7 Polymorphic | 438 | STI, Joined, Concrete, Generic FK |
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

##### Phase 8: Query System & Go Bridge (1700+ tests)

A revolutionary database layer: Go-powered query engine with Python's simplicity. True parallelism via embedded Go runtime, zero-copy data transfer via Apache Arrow, and enterprise-grade features.

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                        PYTHON LAYER                         │
│  • Query building (AST)           • Model definitions       │
│  • Result mapping to objects      • Migrations              │
│  • L1 Cache (app-level, Redis)    • Error handling          │
└─────────────────────────┬───────────────────────────────────┘
                          │ Apache Arrow (zero-copy)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         GO LAYER                            │
│  • Query optimization             • Query execution         │
│  • Connection pooling             • L2 Cache (results)      │
│  • Replica routing                • Health monitoring       │
│  • Timeouts & retries             • True parallelism        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       DATABASES                             │
│  Primary │ Replica 1 │ Replica 2 │ Analytics │ Shards      │
└─────────────────────────────────────────────────────────────┘
```

**8.1 Go Bridge Core** ✅ COMPLETE
- [x] Go shared library (.so/.dylib/.dll) for Linux/macOS/Windows
- [x] Apache Arrow data format (zero-copy Python↔Go)
- [x] Connection pool management (Go owns all connections)
- [x] Lazy startup with optional `pynext.warmup()`
- [x] Auto cleanup + explicit `pynext.close()`
- [x] Python fallback when Go unavailable
- [x] Parallel query execution (goroutines)
- [x] Async API wrappers
- [x] **batch()** context manager for parallel queries (2x faster)
- [x] **execute_copy_df()** for DataFrames (2-3x faster)
- [x] **execute_copy_rows()** for JSON APIs
- [x] PostgreSQL COPY protocol (CSV format)
- [x] Prepared statement caching (2048 capacity)
- [x] Fast JSON with sonic (Go) and orjson (Python)

**Implementation Details:**
- Go module: `go/pkg/bridge/`, `go/pkg/arrow/`
- Python wrapper: `pynext_go/` package with ctypes interface
- Adapter: `pynext/db/adapters/go_adapter.py` with auto-fallback
- Build: `scripts/build-go.sh` and `scripts/build-go-all.sh`
- Documentation:
  - `docs/database/23-go-bridge.md` - Complete API reference
  - `docs/database/24-asyncpg-vs-gobridge.md` - Comparison & migration guide
  - `docs/database/25-gobridge-internals.md` - Deep technical implementation
- Tests: 579+ tests (105 Go + 474+ Python)
- Benchmarks: `tests/benchmarks/test_go_vs_asyncpg.py`

**Performance Results (vs asyncpg) - Verified with 500 iterations:**

| Use Case | Method | Speedup | Notes |
|----------|--------|---------|-------|
| Multi-query endpoint (3 queries) | `batch()` | **1.85x** | True parallel via goroutines |
| Multi-query endpoint (5 queries) | `batch()` | **2.08x** | Each query gets own connection |
| Multi-query endpoint (10 queries) | `batch()` | **2.07x** | Scales with query count |
| DataFrame (1,000 rows) | `execute_copy_df()` | **1.11x** | COPY + pyarrow CSV |
| DataFrame (5,000 rows) | `execute_copy_df()` | **2.30x** | Efficient bulk transfer |
| DataFrame (10,000 rows) | `execute_copy_df()` | **2.79x** | Best for analytics |
| Bulk export (50,000 rows) | `execute_copy()` | **3.24x** | Raw COPY protocol |
| Bulk export (100,000 rows) | `execute_copy()` | **2.85x** | Stable at scale |
| Single query (any size) | `execute()` | **~1x** | Network-bound, same as asyncpg |

**Run benchmarks:**
```bash
pytest tests/benchmarks/test_go_vs_asyncpg.py -v --benchmark-only
```

**Usage Examples:**

```python
import pynext_go

# Initialize
pynext_go.init(
    primary="postgresql://user:pass@localhost/mydb",
    replicas=["postgresql://replica1/mydb"],
    pool_min_size=5,
    pool_max_size=20,
)

# ============================================================
# 1. MULTI-QUERY ENDPOINTS - Use batch() (2x faster!)
# ============================================================
# Looks sequential, executes in parallel
def get_dashboard(user_id: int):
    with pynext_go.batch() as b:
        user = b.query("SELECT * FROM users WHERE id = $1", [user_id])
        orders = b.query("SELECT * FROM orders WHERE user_id = $1", [user_id])
        notifications = b.query("SELECT * FROM notifications WHERE user_id = $1", [user_id])
    
    # All 3 queries ran in parallel!
    return {
        "user": user.rows[0] if user.rows else None,
        "orders": orders.rows,
        "notifications": notifications.rows,
    }

# Async version
async def get_dashboard_async(user_id: int):
    async with pynext_go.batch() as b:
        user = b.query("SELECT * FROM users WHERE id = $1", [user_id])
        orders = b.query("SELECT * FROM orders WHERE user_id = $1", [user_id])
    return {"user": user.rows, "orders": orders.rows}

# ============================================================
# 2. DATAFRAMES - Use execute_copy_df() (2-3x faster!)
# ============================================================
def get_analytics():
    # 10,000 rows: asyncpg takes 24.5ms, this takes 8.8ms
    df = pynext_go.execute_copy_df("""
        SELECT date_trunc('day', created_at) as day,
               COUNT(*) as orders,
               SUM(total) as revenue
        FROM orders
        GROUP BY 1
        ORDER BY 1
    """)
    return df.to_dict()

# ============================================================
# 3. SINGLE QUERIES - Use execute() (same as asyncpg)
# ============================================================
result = pynext_go.execute("SELECT * FROM users WHERE id = $1", [user_id])
print(result.rows)

# ============================================================
# 4. BULK EXPORT - Use execute_copy() (3x faster!)
# ============================================================
csv_data = pynext_go.execute_copy("SELECT * FROM orders")
with open("export.csv", "wb") as f:
    f.write(csv_data)

# ============================================================
# 5. PARALLEL QUERIES - Lower-level API
# ============================================================
results = pynext_go.execute_parallel([
    ("SELECT * FROM users", []),
    ("SELECT * FROM orders WHERE status = $1", ["active"]),
    ("SELECT COUNT(*) FROM products", []),
])
users, orders, product_count = results

# Health check
health = pynext_go.health()
print(f"Status: {health.status}")

# Cleanup
pynext_go.close()
```

**Decision Tree: Which Method to Use?**

```
┌─────────────────────────────────────────────────────────────────────┐
│                     What's your use case?                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Multiple queries per request?                                      │
│  ├── YES → Use batch()                          ⚡ 2x faster        │
│  └── NO ↓                                                           │
│                                                                     │
│  Need a DataFrame?                                                  │
│  ├── YES (1000+ rows) → Use execute_copy_df()   ⚡ 2-3x faster      │
│  └── NO ↓                                                           │
│                                                                     │
│  Bulk data export?                                                  │
│  ├── YES → Use execute_copy()                   ⚡ 3x faster        │
│  └── NO ↓                                                           │
│                                                                     │
│  Single query for JSON API?                                         │
│  └── Use execute()                              Same as asyncpg     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**8.2 Query Builder Core** ✅ COMPLETE
- [x] Query AST builder (Python) - `pynext/db/conditions.py`, `pynext/db/ast.py`
- [x] Query optimizer (Go) - `go/pkg/query/optimizer.go`
- [x] SQL generator (Go) - `go/pkg/query/generator.go`
- [x] Query executor (Go) - `go/pkg/query/executor.go`
- [x] Query validator (Go) - `go/pkg/query/validator.go`
- [x] Query complexity limits (configurable)
- [x] SQL injection prevention (strict mode)
- [x] 4 SQL escape hatch levels
- [x] CGO bridge integration (`PynextQueryExecute`, `PynextQueryExplain`, `PynextQueryValidate`)

**Documentation:**
- `docs/database/26-query-builder.md` - Complete API reference (who/what/when/where/why)
- `docs/database/27-query-security.md` - Security model, injection prevention
- `docs/database/28-query-internals.md` - Deep technical: AST, Go optimization
- `docs/database/29-parallel-execution.md` - **NEW**: Parallel execution complete guide (1000+ lines)
  - The problem (GIL, asyncio limitations)
  - The solution (Go goroutines, architecture diagrams)
  - Who/What/When/Where/Why breakdown
  - Implementation guide with patterns
  - Performance benchmarks
  - Debugging and troubleshooting
  - Best practices and FAQ

**Test Coverage: 500+ tests**
- `tests/unit/db/test_conditions.py` - 81 tests (condition functions)
- `tests/unit/db/test_query_builder.py` - 150+ tests (QueryBuilder API)
- `tests/unit/db/test_query_builder_parallel.py` - 50 tests (parallel execution)
- `tests/unit/db/test_query_builder_syntax.py` - 84 tests (syntax parsing)
- `tests/unit/db/test_ast.py` - 50+ tests (AST generation)
- `tests/integration/db/test_query_builder_postgres.py` - 43 tests (PostgreSQL integration)
- `go/pkg/query/ast_test.go` - 25+ tests (Go AST parsing)
- `go/pkg/query/generator_test.go` - 25+ tests (SQL generation)
- `go/pkg/query/optimizer_test.go` - 20+ tests (query optimization)
- `go/pkg/query/validator_test.go` - 20+ tests (validation)
- `go/pkg/query/executor_test.go` - 10+ tests (execution)

```python
# Dead simple API - NO __ pattern!

# Three ways to query (all work together):

# 1. Tuple syntax (explicit operators)
users = await User.q(("age", ">", 18), ("status", "=", "active"))

# 2. SQL string (familiar to SQL users)
users = await User.q("age > $1 AND status = $2", 18, "active")

# 3. Condition functions (type-safe)
from pynext.db import gt, eq, contains, and_, or_
users = await User.q(gt("age", 18), eq("status", "active"))

# Chainable for complex queries
users = await (User.q(gt("age", 18))
         .select("id", "name", "email")
         .include("posts", "comments")
         .order("-created_at")
         .page(1, per_page=20))

# Complex conditions with logical operators
users = await User.q(
    and_(
        gt("age", 18),
        or_(eq("role", "admin"), eq("role", "moderator"))
    )
)

# SQL Escape Hatches (4 levels)
# Level 1: SQL in .q()
users = await User.q("custom_func(data) > $1", 10)

# Level 2: Raw SQL (returns dicts)
rows = await db.sql("SELECT * FROM users WHERE ...")

# Level 3: Raw SQL with model mapping
users = await User.sql("SELECT * FROM users WHERE ...")

# Level 4: Hybrid (builder + raw)
users = await User.q(gt("age", 18)).where_raw("jsonb_col @> $1", ['{"key": "val"}'])
```

**8.3 DataFrame Integration** ✅ COMPLETE
- [x] Arrow table result wrapper (`execute_arrow()`)
- [x] Pandas integration via COPY protocol (`execute_copy_df()`)
- [x] CSV/Dict serialization (`execute_copy_rows()`)
- [x] Polars integration (native Arrow, zero-copy) - `execute_polars()`
- [x] NumPy column-wise arrays (zero-copy for numerics) - `execute_numpy()`
- [x] NumPy structured arrays (row-oriented) - `execute_numpy_structured()`
- [x] pandas via Arrow (optimized) - `execute_pandas()`
- [x] QueryBuilder methods: `.to_polars()`, `.to_pandas()`, `.to_numpy()`, `.to_numpy_structured()`, `.to_dicts()`, `.to_list()`
- [x] Async versions for all methods
- [x] Arrow type mapping utilities (`pynext_go/numpy_utils.py`)
- [x] **600 comprehensive tests** across 8 test files
- [x] **Documentation**: `docs/database/30-dataframe-integration.md`

```python
# Standalone functions (fastest path)
import pynext_go

df = pynext_go.execute_polars("SELECT * FROM users WHERE age > $1", [18])  # Zero-copy!
arrays = pynext_go.execute_numpy("SELECT id, score FROM users")  # Vectorized ops
structured = pynext_go.execute_numpy_structured("SELECT * FROM users")  # Row iteration
df = pynext_go.execute_pandas("SELECT * FROM orders")  # pandas compatibility

# QueryBuilder methods (chainable)
df = await User.q(("age", ">", 18)).to_polars()
df = await User.q().select("id", "name", "score").order("-score").limit(100).to_pandas()
arrays = await Product.q(("active", "=", True)).to_numpy()
rows = await Order.q(("status", "=", "pending")).to_dicts()  # For JSON API

# Async versions
df = await pynext_go.execute_polars_async("SELECT * FROM large_table")
arrays = await pynext_go.execute_numpy_async("SELECT * FROM metrics")
```

**Performance (vs asyncpg + manual conversion) - MEASURED:**

| Rows | Operation | asyncpg | pynext-go | Speedup |
|------|-----------|---------|-----------|---------|
| 100K | to_polars | 213ms | 49ms | **4.33x** |
| 100K | to_pandas | 222ms | 49ms | **4.52x** |
| 100K | to_numpy | 139ms | 50ms | **2.77x** |
| 500K | to_polars | 1,031ms | 225ms | **4.59x** |
| 500K | to_pandas | 1,381ms | 243ms | **5.69x** |
| 1M | to_polars | 1,925ms | 498ms | **3.87x** |
| 2M | to_polars | 4,477ms | 890ms | **5.03x** |

**Average: 4.07x faster than asyncpg**

See `docs/database/31-benchmark-methodology.md` for full methodology.

**8.4 Read Replicas & Smart Routing**
- [ ] Replica configuration (named, tagged, geographic)
- [ ] Smart routing (read/write detection)
- [ ] Round-robin, least-connections, geographic routing
- [ ] Replica health monitoring
- [ ] Automatic failover
- [ ] Replication lag awareness

```python
# Configuration
pynext.config(
    primary="postgres://primary...",
    replicas=[
        {"url": "postgres://replica1...", "name": "us-east-1", "tags": ["fast"]},
        {"url": "postgres://replica2...", "name": "us-west-2", "tags": ["analytics"]},
    ],
    routing="smart"  # or "round_robin", "least_connections"
)

# Automatic routing (default)
User.q().all()  # Reads → replica, writes → primary

# Explicit routing
User.q().replica("us-east-1").all()
User.q().replica(tags=["analytics"]).all()
User.q().replica("nearest").all()  # Geographic
User.q().primary().all()  # Force primary
```

**8.5 Two-Tier Caching**
- [ ] Go-level result cache (L2)
- [ ] Python-level cache interface (L1)
- [ ] Redis backend support
- [ ] In-memory backend
- [ ] TTL management
- [ ] Cache invalidation

```python
# L1: Python/Redis (app-level, shared)
# L2: Go (query results, fast)

User.q(id=1).cache(ttl=60)  # Cache for 60s
User.q("status = 'active'").cache("active_users", ttl=300)

pynext.config(cache_backend="redis://localhost:6379")
```

**8.6 REST/API Response Formatting**
- [ ] Offset pagination
- [ ] Cursor-based pagination
- [ ] Streaming large results
- [ ] JSON serialization
- [ ] Response metadata
- [ ] Framework integrations (FastAPI, Flask)

```python
# Pagination
users = User.q().page(1, per_page=20)
# Returns: {"data": [...], "meta": {"page": 1, "total": 100, "pages": 5}}

# Cursor-based (for large datasets)
users = User.q().cursor(after="abc123", limit=20)

# Streaming (millions of rows)
async for batch in User.q().stream(batch_size=1000):
    process(batch)

# Direct JSON response
return User.q().page(1).to_response()  # FastAPI/Flask ready
```

**8.7 Live Queries & Server Actions**
- [ ] Query subscription (WebSocket)
- [ ] Change detection
- [ ] Server action decorator
- [ ] Frontend SDK generation
- [ ] Optimistic updates

```python
# WebSocket subscription
@app.websocket("/users")
async def user_updates(ws):
    async for change in User.subscribe("status = 'active'"):
        await ws.send(change.to_json())

# Server Actions (callable from frontend)
@server_action
async def get_users(age_min: int):
    return User.q(("age", ">", age_min)).all()

# Frontend calls directly:
# const users = await serverActions.get_users({ age_min: 18 })
```

**8.8 Batch Operations**
- [ ] Bulk insert (COPY protocol)
- [ ] Bulk update
- [ ] Bulk delete
- [ ] Upsert/merge
- [ ] DataFrame input support
- [ ] Batch size configuration

```python
# Bulk insert from DataFrame
User.bulk_insert(df)  # From pandas
User.bulk_insert(records)  # From dicts

# Bulk update
User.q("status = 'old'").update(status="archived")

# Bulk delete
User.q("created_at < '2020-01-01'").delete()

# Upsert
User.bulk_upsert(records, conflict_keys=["email"])
```

**8.9 Transactions**
- [ ] Transaction context manager
- [ ] Transaction decorator
- [ ] Savepoints
- [ ] Isolation levels
- [ ] Deadlock detection
- [ ] Transaction timeout

```python
# Context manager
async with db.transaction() as tx:
    user = User.create(name="John")
    Post.create(author=user, title="Hello")
    # Auto-commit on exit, rollback on exception

# Decorator
@transactional
async def create_user_with_posts(name, posts):
    user = User.create(name=name)
    for p in posts:
        Post.create(author=user, **p)
    return user

# Savepoints
async with db.transaction() as tx:
    User.create(name="A")
    async with tx.savepoint():
        User.create(name="B")
        raise ValueError()  # Only B rolls back
    User.create(name="C")  # A and C commit
```

**Async/Sync Strategy:**
```python
# Auto-detect context - SAME API works everywhere:
user = User.get(1)  # Works in sync AND async contexts!

# Framework detects:
# - In FastAPI route? → async
# - In script? → sync
# - In Celery task? → sync

# Explicit override when needed:
user = User.get(1, mode="sync")   # Force sync
user = User.get(1, mode="async")  # Force async
```

**Error Handling:**
```python
# Default: Exceptions (familiar to Python devs)
user = User.get(1)  # Raises UserNotFoundError if not found

# Safe mode: Result type
result = User.get(1, safe=True)
# Returns: Ok(user) or Err(UserNotFoundError)

match result:
    case Ok(user):
        print(user.name)
    case Err(e):
        print(f"Error: {e}")
```

---

##### Phase 9: Observability & Operations (200+ tests)

Production-ready monitoring, tracing, and health checks.

**9.1 Comprehensive Metrics**
- [ ] Query metrics (count, latency histograms)
- [ ] Connection pool metrics
- [ ] Cache metrics (L1/L2 hit rates)
- [ ] Replica metrics (queries, lag)
- [ ] Error tracking
- [ ] Prometheus exporter
- [ ] Grafana dashboards

```python
metrics = db.metrics()
# Returns:
{
    "queries": {
        "total": 150000,
        "per_second": 250,
        "latency_p50_ms": 2,
        "latency_p95_ms": 15,
        "latency_p99_ms": 45,
        "errors": 12
    },
    "connections": {
        "active": 20,
        "idle": 30,
        "max": 50
    },
    "cache": {
        "l1_hits": 5000,
        "l2_hits": 8000,
        "hit_rate": 0.92
    },
    "replicas": {
        "replica-1": {"queries": 50000, "lag_ms": 10},
        "replica-2": {"queries": 48000, "lag_ms": 15}
    }
}

# Prometheus export
@app.get("/metrics")
def metrics():
    return db.metrics_prometheus()
```

**9.2 Distributed Tracing**
- [ ] OpenTelemetry integration
- [ ] Span creation (Python → Go → DB)
- [ ] Context propagation
- [ ] Jaeger/Zipkin export
- [ ] Query attribution
- [ ] Sampling configuration

```python
# Automatic tracing
pynext.config(tracing=True, service_name="my-app")

# Trace: Python → Go → Database
# Each span shows:
# - Query text (parameterized)
# - Execution time
# - Rows affected
# - Connection used
# - Replica selected

# Custom spans
with db.trace("complex_operation"):
    users = User.q().all()
    posts = Post.q().all()
```

**9.3 Query Logging**
- [ ] Slow query logging (configurable threshold)
- [ ] Query analysis (EXPLAIN)
- [ ] Query pattern detection
- [ ] Index suggestions
- [ ] Custom handlers/alerts

```python
pynext.config(
    slow_query_threshold_ms=100,  # Log queries >100ms
    log_all_queries=False,        # Or log everything (dev)
    query_log_format="json"       # or "text"
)

# Custom slow query handler
@pynext.on_slow_query
def handle_slow(query_info):
    alert_team(query_info)

# Query analysis
analysis = db.analyze_query("SELECT * FROM users WHERE...")
# Returns: execution plan, index usage, suggestions
```

**9.4 Health Checks**
- [ ] Health check API
- [ ] Primary/replica status
- [ ] Connection pool status
- [ ] Go bridge status
- [ ] Kubernetes probe helpers

```python
# Detailed health
health = db.health()
# Returns:
{
    "status": "healthy",  # or "degraded" or "unhealthy"
    "primary": {"status": "ok", "latency_ms": 2},
    "replicas": {
        "replica-1": {"status": "ok", "lag_ms": 50},
        "replica-2": {"status": "degraded", "lag_ms": 2000}
    },
    "go_bridge": {"status": "ok", "goroutines": 12}
}

# Quick checks for load balancers
db.is_healthy()  # bool
db.is_ready()    # bool

# Kubernetes probes
@app.get("/health/live")
def liveness():
    return {"status": "ok"}

@app.get("/health/ready")  
def readiness():
    return db.health()
```

---

##### Phase 10: Multi-Tenancy & Scaling (200+ tests)

Enterprise-ready multi-tenant support with flexible isolation strategies. Perfect for SaaS, CRMs, and white-label platforms.

**10.1 Tenant Strategies**
- [ ] Row-level isolation (WHERE tenant_id = X)
- [ ] Schema-level isolation (separate schemas)
- [ ] Database-level isolation (separate databases)
- [ ] Mixed strategy support (by tier)
- [ ] Tenant context propagation
- [ ] Cross-tenant queries (admin)

```python
# Row-level (shared everything) - for small tenants
pynext.config(
    tenant_strategy="row_level",
    tenant_column="tenant_id"
)
# All queries get: WHERE tenant_id = 'current'

# Schema-level (separate schemas) - for medium tenants
pynext.config(tenant_strategy="schema")
# Queries go to: tenant_schema.users

# Database-level (separate databases) - for enterprise
pynext.config(tenant_strategy="database")
# Connects to: tenant_database

# Mixed strategies by tier
pynext.config(tenant_strategy={
    "free": "row_level",
    "pro": "schema",
    "enterprise": "database"
})

# Tenant context
@app.middleware
def add_tenant(request):
    tenant_id = get_tenant_from_token(request)
    pynext.set_tenant(tenant_id)

# Queries automatically scoped
users = User.q().all()  # Only current tenant's users

# Admin: cross-tenant query
users = User.q().all_tenants()
```

**10.2 Tenant Upgrades**
- [ ] Row → Schema migration
- [ ] Schema → Database migration
- [ ] Background migration worker
- [ ] Zero-downtime cutover
- [ ] Rollback support

```python
# Upgrade tenant from row_level to schema
await tenant.upgrade_to("schema")

# Upgrade to dedicated database
await tenant.upgrade_to("database")

# Migration runs in background, zero downtime
status = await tenant.upgrade_status()
# {"progress": 75, "eta_seconds": 120}
```

**10.3 Sharding Support**
- [ ] Hash-based sharding
- [ ] Range-based sharding
- [ ] Lookup table sharding
- [ ] Shard routing
- [ ] Cross-shard queries (scatter-gather)
- [ ] Shard rebalancing

```python
pynext.config(
    sharding={
        "strategy": "hash",  # or "range", "lookup"
        "key": "user_id",
        "shards": [
            "postgres://shard1...",
            "postgres://shard2...",
            "postgres://shard3...",
        ]
    }
)

# Automatic routing
User.q(user_id=123).all()  # Routes to correct shard

# Cross-shard queries (when needed)
User.q().all_shards().all()  # Scatter-gather
```

**10.4 Rate Limiting & Quotas**
- [ ] Query rate limiting per tenant
- [ ] Connection quotas per tenant
- [ ] Query timeout enforcement
- [ ] Complexity scoring
- [ ] Quota exceeded handling

```python
pynext.config(
    rate_limits={
        "free": {"queries_per_second": 10, "connections": 5},
        "pro": {"queries_per_second": 100, "connections": 20},
        "enterprise": {"queries_per_second": 1000, "connections": 50},
    }
)

# Per-query timeout
User.q().timeout(5000).all()  # 5 second timeout

# Global defaults
pynext.config(
    default_query_timeout_ms=30000,
    max_query_complexity=100
)
```

---

**Phase 8-10 Integration with Phase 7:**

| Phase 7 Feature | Query System Integration |
|-----------------|--------------------------|
| 7.1-7.3 M2M | Query builder supports M2M joins via dot notation |
| 7.4 Cascades | Batch operations respect cascade rules |
| 7.5 Filters | Query builder uses same filter syntax |
| 7.6 Trees | Hierarchical queries via `User.ancestors()` |
| 7.7 Polymorphic | Query across polymorphic types |
| 7.8 Hooks | All operations fire appropriate hooks |
| 7.9 Proxies | Query through association proxies |
| 7.10 Ordering | Query builder uses same `order()` syntax |

**Test Targets:**

| Sub-Phase | Tests |
|-----------|-------|
| 8.1 Go Bridge | 580+ (105 Go + 475 Python + benchmarks) |
| 8.2 Query Builder | 300+ ✅ (81 conditions + 150 builder + 50 AST + 65 Go) |
| 8.3 DataFrame | 600+ ✅ (80 Polars + 100 NumPy colwise + 100 NumPy struct + 120 QueryBuilder + 80 type mapping + 50 error + 40 benchmark + 30 integration) |
| 8.4 Replicas | 150+ |
| 8.5 Caching | 100+ |
| 8.6 REST/API | 100+ |
| 8.7 Live Queries | 150+ |
| 8.8 Batch Ops | 100+ |
| 8.9 Transactions | 100+ |
| 9.x Observability | 200+ |
| 10.x Multi-tenant | 200+ |
| **Total** | **2200+** |

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

#### Phase 11: Core Reactivity (Target: 400+ tests)

**11.1 Signals (React's useState equivalent)**
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

**11.2 Computed/Derived State (React's useMemo)**
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

**11.3 Effects (React's useEffect)**
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

**11.4 Resources (React's data fetching patterns)**
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

#### Phase 12: Component Patterns (Target: 300+ tests)

**12.1 Context (React's useContext)**
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

**12.2 Error Boundaries (React's componentDidCatch)**
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

**12.3 Suspense (React's Suspense)**
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

**12.4 Portals (React's createPortal)**
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

**12.5 Refs (React's useRef)**
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

#### Phase 13: Control Flow (Target: 200+ tests)

**13.1 Conditional Rendering**
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

**13.2 List Rendering**
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

**13.3 Dynamic Components**
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

#### Phase 14: Advanced Patterns (Target: 300+ tests)

**14.1 Stores (Complex State)**
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

**14.2 Transitions (Concurrent UI)**
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

**14.3 Deferred Values**
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

**14.4 Streaming & Progressive Rendering**
- [x] Streaming HTML (ALREADY IMPLEMENTED)
- [ ] Progressive hydration
- [ ] Selective hydration based on visibility
- [ ] `renderToStream()` for SSR

---

#### Phase 15: Developer Experience (Target: 200+ tests)

**15.1 DevTools Integration**
- [ ] Signal inspection in browser devtools
- [ ] Component tree visualization
- [ ] Reactivity graph visualization
- [ ] Time-travel debugging

**15.2 Hot Module Replacement**
- [x] HMR for components (ALREADY IMPLEMENTED)
- [ ] Preserve signal state across HMR
- [ ] Component state persistence

**15.3 TypeScript-style Type Hints**
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

#### Phase 16: Native Authentication (Target: 600+ tests)

**16.1 One-Line Setup**
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

**16.2 Signal-Based Auth State**
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

**16.3 Route Protection**
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

**16.4 Built-In Auth Forms**
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

**16.5 OAuth Providers**
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

**16.6 Magic Links (Passwordless)**
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

**16.7 Session Management**
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

**16.8 Email Verification**
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

**16.9 Password Reset**
- [ ] `Auth.send_reset_email(email)` - Send reset link
- [ ] Auto-generated `/reset-password` route
- [ ] Secure token with expiry
- [ ] Invalidate all sessions on reset

```python
await Auth.send_reset_email(email)
await Auth.reset_password(token, new_password)
```

**16.10 Two-Factor Authentication (2FA/MFA)**
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

**16.11 Account Linking**
- [ ] Same email = same account (automatic)
- [ ] Link additional providers
- [ ] Unlink providers (keep at least one)

```python
await Auth.link_provider(user_id, "github", github_token)
providers = await Auth.get_linked_providers(user_id)
await Auth.unlink_provider(user_id, "github")
```

**16.12 Role & Permission System**
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

**16.13 API Route Protection**
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

**16.14 Data Access Layer Integration**
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

**16.15 Seamless ORM Integration**

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

**16.16 Auto-Generated Migrations**
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

**16.17 Session Storage with Adapters**
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

**16.18 Validation Integration**
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

**16.19 Query Builder Integration**
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

**16.20 Security Built-In**
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

#### Phase 7.5: Custom Join Conditions ✅

- [x] **Condition functions** — `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `like`, `ilike`, `is_in`, `not_in`, `is_null` for type-safe filtering
- [x] **Tuple syntax** — `("field", ">=", value)` for SQL-like conditions
- [x] **`filter` parameter** — Works on all relationship types (`has_many`, `has_one`, `belongs_to`, `many_to_many`)
- [x] **Date/time helpers** — `days_ago`, `hours_ago`, `weeks_ago`, `start_of_today`, `start_of_month`, etc.
- [x] **Loading strategy integration** — Filters work with all loading strategies
- [x] **Mixed syntax support** — Combine function and tuple syntax in same filter list

**Implementation Details:**
- Files: `pynext/db/relationships/` (conditions.py, filter.py, helpers.py)
- Classes: `Condition`, `RelationshipFilter`, date/time helper functions
- Tests: **488 comprehensive tests** across 9 test files
- Documentation: `docs/database/17-custom-join-conditions.md`

**Why This is Better Than SQLAlchemy:**
- Type-safe conditions with IDE autocomplete (vs string-based expressions)
- Two syntaxes: function calls and SQL-like tuples
- Clear validation errors instead of cryptic runtime failures
- Easy for LLMs to understand and generate

---

#### Phase 7.2: Loading Strategies ✅

- [x] **`lazy` parameter** — Control loading behavior: select, joined, subquery, selectin, raise, dynamic
- [x] **Query options** — `options(selectinload(), joinedload(), raiseload())` for query-level control
- [x] **N+1 prevention** — `LazyLoadError` raised when accessing `lazy="raise"` relationships
- [x] **Dynamic relationships** — `DynamicRelationship` returns query builder for large collections
- [x] **Nested loading** — Chain options: `selectinload("posts").joinedload("author")`

**Implementation Details:**
- Files: `pynext/db/relationships/` (loading.py, options.py, dynamic.py)
- Classes: `LoadStrategy`, `LoadOption`, `LazyLoadError`, `RelationshipLoader`, `DynamicRelationship`
- Tests: **300 comprehensive tests** across 6 files
- Documentation: `docs/database/13-loading-strategies.md` (800 lines)

---

#### Phase 7.1: Bidirectional Relationships (backref) ✅

- [x] **`backref` parameter** — Automatic reverse relationship creation
- [x] **`back_populates`** — Explicit bidirectional linking between models
- [x] **Automatic sync** — Modifying either side syncs the other automatically
- [x] **Loop prevention** — ContextVar-based guard prevents infinite recursion
- [x] **`SyncedList` collection** — Auto-syncs on append, remove, extend, clear, pop, insert, etc.
- [x] **Forward references** — Models can be defined in any order with lazy resolution

**Implementation Details:**
- Files: `pynext/db/relationships/` (backref.py, collections.py, core.py, __init__.py)
- Classes: `BackrefConfig`, `BackrefRegistry`, `RelationshipSyncManager`, `SyncedList`
- Tests: **182 comprehensive tests** across 4 test files:
  - `test_backref_basic.py` (58 tests) — Config, registry, descriptor attributes
  - `test_backref_sync.py` (44 tests) — Bidirectional sync, loop prevention
  - `test_backref_collections.py` (40 tests) — SyncedList operations
  - `test_backref_edge_cases.py` (40 tests) — Null values, self-referential, performance
- Docs: [docs/database/11-relationships.md](./database/11-relationships.md) (788 lines)

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

- [x] **AI Agentic Validation System** — Intelligent code generation with thought threads ✅ COMPLETED
  - Files: `pynext/generator/` (config.py, thought.py, reasoning.py, validator.py, search.py, agent.py)
  - **Thought Threads**: Chain-of-thought reasoning instead of blind retry
    - AI reasons about *why* errors occurred, not just *what* failed
    - Progressive understanding: each thought builds on previous
    - Self-critique in deep mode before generating fixes
  - **Configurable Model Selection**: CLI > env > config > default
    - `--model claude-opus-4-20250514` for complex generation
    - `ANTHROPIC_MODEL` environment variable
    - `pynext.ai.toml` config file support
  - **Thought Depth Levels**:
    - `shallow` (1-2 thoughts): Fast, simple fixes
    - `medium` (2-3 thoughts): Balanced analysis
    - `deep` (3-5 thoughts): Full analysis with self-critique
  - **Validation Levels**: syntax, imports, full (with PyNext pattern checking)
  - **Codebase Search**: AI searches PyNext docs/source for correct patterns
  - **CLI Flags**: `--model`, `--max-thoughts`, `--thought-depth`, `--validation`, `--verbose`
  - Tests: **100+ comprehensive tests** for config, thought threads, validator, search, agent
  - Docs: [docs/generators/AI_GENERATION.md](./generators/AI_GENERATION.md)

- [x] **AI App Builder CLI** — Cursor-like AI application builder ✅ COMPLETED
  - Files: `pynext/app/` (generator.py, planner.py, context.py, session.py, progress.py, rollback.py, file_generator.py)
  - **PyNext Knowledge Base (RAG)**: Since no LLM is trained on PyNext, we built a semantic retrieval system
    - `pynext/app/knowledge/indexer.py`: Indexes all docs and source code with smart chunking
    - `pynext/app/knowledge/retriever.py`: Semantic search over indexed content
    - `pynext/app/knowledge/patterns.py`: Library of 16 reusable PyNext patterns
    - `pynext/app/knowledge/embeddings.py`: Local or API-based embeddings
    - `pynext/app/knowledge/context_builder.py`: Builds optimal prompts for AI
  - **Three Generation Modes**:
    - `plan`: Show plan, wait for approval, then generate (default, safest)
    - `agent`: Execute autonomously with minimal prompts
    - `ask`: Ask for approval at each step (most interactive)
  - **Complexity Scaling**: minimal (3-5 files) to enterprise (50+ files)
  - **Project Context**: Analyzes existing projects to enable intelligent feature additions
  - **Progress Tracking**: Visual feedback with progress bars and summaries
  - **Rollback Support**: Checkpoints and rollback for failed generations
  - **App Templates**: Pre-built structures (blog, SaaS, e-commerce, dashboard)
  - **CLI Commands**:
    - `pynext app new "description"` — Create new application
    - `pynext app add "feature"` — Add feature to existing project
    - `pynext app chat` — Interactive chat session
  - Tests: **54 comprehensive tests** for knowledge base, planner, context, generator
  - Docs: [docs/app-builder/README.md](./app-builder/README.md)

- [x] **Session Memory & Configuration System** — Persistent memory and hierarchical config ✅ COMPLETED
  - Files: `pynext/app/memory.py`, `pynext/app/config.py`, `pynext/app/templates/pynext.toml`
  - **Session Memory** (`memory.py`):
    - Persistent conversation history stored in `.pynext/session.mem` (JSON Lines format)
    - Automatic summarization when context gets large (80% of max tokens)
    - Checkpoints for project state snapshots and rollback
    - Preferences storage for learned user settings
    - Semantic search and context retrieval for AI prompts
    - **Configurable sync**: incremental/full/manual modes, customizable triggers
    - CLI: `pynext memory show/stats/clear/flush/compact/export/sync/checkpoint`
  - **Configuration System** (`config.py`):
    - Hierarchical config: `~/.config/pynext/` → `./pynext.toml` → env → CLI
    - Variables with `${var}` syntax and computed values
    - Named modes: `prototype`, `production`, `strict` with inheritance
    - Conditional prompts with Python (`when`) and LLM (`when_llm`) evaluation
    - Reusable patterns with variable substitution
    - Per-file-type prompts (page, island, api, model, action, etc.)
    - Validation rules, style preferences, team standards
    - CLI: `pynext config init/show/get/validate`
  - **Sync Configuration** (in `[memory]` section of `pynext.toml`):
    - `sync_mode`: incremental (append), full (rewrite), manual
    - `sync_on`: triggers like `assistant_response`, `checkpoint`, `exit`
    - `sync_batch_size`, `exclude_roles`, `max_entries_in_memory`
    - File rotation and compression options
  - **Integration**: Session uses memory for persistence, file_generator uses config for prompts
  - Tests: **80+ comprehensive tests** for memory and config systems
  - Docs: [docs/app-builder/CONFIG.md](./app-builder/CONFIG.md), [docs/app-builder/MEMORY.md](./app-builder/MEMORY.md)

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

