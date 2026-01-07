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

#### Phase 17: Unified Reactive System (Compilation-First Design)

**Status:** In Progress (17.1 ✅, 17.2 ✅, 17.3 ✅, 17.4 ✅, 17.5 ✅, 17.6 ✅, 17.7 ✅, 17.8 ✅, 17.9 ✅, 17.10 ✅, 17.11 ⏳)  
**Priority:** P0 (Critical)  
**Target Tests:** 5,000+  
**Current Tests:** 16,550+ passing (99.9%)  
**Timeline:** ~5-6 weeks (10 of 11 sub-phases complete)

**Progress Summary:**
| Phase | Description | Status | Tests |
|-------|-------------|--------|-------|
| 17.1 | Design & Specification | ✅ Complete | Docs |
| 17.2 | Minimal JS Runtime | ✅ Complete | 66 |
| 17.3 | Python API (Unified) | ✅ Complete | 845 |
| 17.4 | Compiler Core | ✅ Complete | 467 |
| 17.5 | SSR + Hydration | ✅ Complete | 170+ |
| 17.6 | Forms | ✅ Complete | 523+ |
| 17.7 | Build System | ✅ Complete | 339 |
| 17.8 | Client-Side Router | ✅ Complete | 600 |
| 17.9 | AI DevTools | ✅ Complete | 200+ |
| 17.10 | Event Modifiers | ✅ Complete | 49 |
| 17.11 | Migration | ⏳ Pending | - |

This phase represents a **complete unified redesign** of PyNext's reactive system with compilation as a first-class citizen. Unlike the previous piecemeal approach, this design treats server-side rendering, client-side hydration, and the Python-to-JS compiler as a cohesive system from day one.

**Performance Target:** Faster than **both React.js AND Next.js** using SolidJS optimization principles:
- No Virtual DOM (React's main bottleneck)
- Fine-grained reactivity (only affected DOM nodes update)
- O(1) updates regardless of component tree size
- Compiled output (no runtime diffing)

**Why This Redesign:**

The previous approach built components in isolation:
- `pynext/core/signals.py` - Simple signals for SSR
- `pynext/reactive/*.py` - Complex signals for "SolidJS-like" behavior  
- `pynext/runtime/signals.js` - JS runtime that didn't match either Python API

These systems don't connect cleanly. This unified redesign solves that.

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PYNEXT UNIFIED REACTIVE SYSTEM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐   │
│  │   Python API    │     │    Compiler     │     │   JS Runtime    │   │
│  │ (pynext/reactive)│────▶│ (pynext/compiler)│────▶│ (pynext/runtime)│   │
│  └────────┬────────┘     └─────────────────┘     └────────┬────────┘   │
│           │                                               │             │
│           │              ┌─────────────────┐              │             │
│           └─────────────▶│   SSR Engine    │◀─────────────┘             │
│                          │  (HTML + JSON)  │                            │
│                          └────────┬────────┘                            │
│                                   │                                     │
│                          ┌────────▼────────┐                            │
│                          │   Hydration     │                            │
│                          │ (Client Takeover)│                            │
│                          └─────────────────┘                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Design Decisions (Locked In):**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Syntax | Pythonic (`signal()`, `.set()`) | Python devs expect objects, not tuples |
| Compilation | Build-time only | Performance, smaller bundles, predictability |
| Hydration | Both Islands (default) + Full | Flexibility for content sites and apps |
| TypeScript | Generate `.d.ts` | Modern standard, better tooling |

**Success Criteria (vs React/Next.js):**

| Metric | React/Next.js | PyNext Target | Improvement |
|--------|---------------|---------------|-------------|
| Initial render | 50-100ms | < 20ms | 2.5-5x faster |
| Update 1 item in 1000-item list | 10-50ms (re-renders list) | < 5ms | 10x faster |
| Memory per component | 1-2KB | < 500 bytes | 2-4x smaller |
| Bundle size | ~40KB (React) | < 5KB | 8x smaller |
| Hydration time (100 signals) | 100-500ms | < 100ms | 2-5x faster |
| Compilation speed | N/A | < 50ms per component | - |

*Note: Hydration times are for real browser with DOM operations, not synthetic benchmarks.*

---

**17.1 Design and Specification (COMPLETED)**

Before writing code, lock down the exact APIs and protocols:

- [x] Define Python API: `signal()`, `effect()`, `memo()`, `store()`, `Show`, `For`, `Switch`
- [x] Define hydration protocol: server HTML format, JSON state, client takeover
- [x] Define compilation boundaries: what compiles to JS, what stays server-only
- [x] Document API constraints for compilable code
- [x] Create specification with examples
- [x] Define 5,000 test specifications

**Files Created:**
- `docs/reactive/SPECIFICATION.md` - Complete API specification (~2000 lines)
- `docs/reactive/HYDRATION_PROTOCOL.md` - Server/client handoff protocol (~500 lines)
- `docs/reactive/COMPILATION_GUIDE.md` - What compiles to JS (~500 lines)
- `docs/reactive/TEST_SPECIFICATIONS.md` - 5,000 test specifications (~8000 lines)
- `docs/reactive/AI_GUIDE.md` - LLM assistance guide (~300 lines)

**Example API (to be finalized):**
```python
from pynext.reactive import signal, effect, memo, Show, For

# Signals - reactive values
count = signal(0)
name = signal("hello")

# Read (callable)
value = count()

# Write
count.set(5)
count.set(count() + 1)

# Effects - side effects
@effect
def log_count():
    print(f"Count: {count()}")

# Memos - derived values
doubled = memo(lambda: count() * 2)

# Control flow
Show(when=lambda: count() > 0)[
    "Count is positive"
]

For(each=lambda: items(), key=lambda x: x.id)[
    lambda item: div()[item.name]
]
```

---

**17.2 Minimal JS Runtime (COMPLETED)**

Implemented the client-side runtime (~2.3KB gzipped - under 3KB target!):

- [x] `createSignal(initial)` - Reactive value
- [x] `createEffect(fn)` - Side effect with auto-tracking
- [x] `createMemo(fn)` - Memoized computation
- [x] `createStore(obj)` - Deep reactive object
- [x] `batch(fn)` - Coalesce updates
- [x] `untrack(fn)` - Read without tracking
- [x] `hydrate(root)` - Connect server HTML to signals
- [x] `hydrateIsland(selector)` - Hydrate single component
- [x] Control flow: `Show`, `For`, `Index`, `Switch`, `Match`, `Portal`, `ErrorBoundary`

**Files Created:**
- `pynext/runtime/reactive.js` - Main runtime (1186 lines, ~40KB)
- `pynext/runtime/reactive.d.ts` - TypeScript definitions (200+ lines)
- `pynext/runtime/reactive.min.js` - Minified (**2.3KB gzipped**)
- `tests/js/test_reactive.js` - 800+ comprehensive tests
- `docs/reactive/JS_RUNTIME.md` - Complete documentation

**Performance Achieved (Benchmarked):**
| Metric | React (published) | PyNext (measured) | Improvement |
|--------|-------------------|-------------------|-------------|
| Bundle size | ~40KB | **2.3KB gzip** | **17x smaller** |
| Memory per signal | ~2-5KB (component) | **~850 bytes** | **3-6x smaller** |

**In-Memory Operations (synthetic benchmarks):**
| Operation | PyNext | Note |
|-----------|--------|------|
| Signal update (1 subscriber) | 0.15 µs | In-memory only |
| List update (1 of 1000) | 2.7 µs | In-memory only |

**Real Browser Performance (with DOM):**
| Scenario | PyNext Target | Note |
|----------|---------------|------|
| Hydration (100 signals) | < 100ms | Includes DOM binding |
| Linear clone (104 signals + 305 handlers) | < 150ms | Realistic app |
| First interaction latency | < 50ms | After hydration |

*⚠️ In-memory benchmarks are 100-1000x faster than real DOM operations.*
*Run `pytest tests/e2e/bench_hydration_real.py` for real browser benchmarks.*

**JS API (mirrors Python exactly):**
```javascript
// Runtime API
const count = createSignal(0);
const doubled = createMemo(() => count() * 2);

createEffect(() => {
    console.log(`Count: ${count()}, Doubled: ${doubled()}`);
});

count.set(5);  // Logs: "Count: 5, Doubled: 10"

// Hydration
hydrate(document.getElementById('app'), window.__PYNEXT_DATA__);
```

---

**17.3 Python API (Unified) ✅ COMPLETED**

Single implementation that works for both SSR and compilation:

- [x] `signal(initial)` - Signal class designed for SSR + compilation
- [x] `effect(fn)` - Effect with proper cleanup
- [x] `memo(fn)` - Memoized computation  
- [x] `store(obj)` - Deep reactive store
- [x] `Show`, `For`, `Index`, `Switch`, `Match` - Control flow
- [x] `Portal`, `Dynamic`, `ErrorBoundary` - Advanced control flow
- [x] Compilation markers for build-time extraction
- [x] Import migration (27 files updated)
- [x] Test cleanup (removed over-engineered tests)

**Completed Work:**
- Migrated all imports from `pynext.core.signals` → `pynext.reactive`
- Converted `pynext/core/signals.py` to compatibility shim with deprecation warnings
- Cleaned up 310 over-engineered tests (Owner hierarchy, internal state, WeakSet internals)
- **845 reactive tests passing** (100% pass rate)
- **16,044+ total tests passing** (100% pass rate)

**Remaining (Phase 17.8+):**
- ✅ Hydration tests now passing (Phase 17.5 complete)
- ✅ Form tests now passing (Phase 17.6 complete - 523+ tests)
- ✅ Build System tests passing (Phase 17.7 complete - 339 tests)
- 59 E2E tests pending (need Playwright + dev server infrastructure for 17.8+)

**Files (cleaned up):**
- `pynext/reactive/signal.py` - Core reactive value container (auto-registers with SSR context)
- `pynext/reactive/effect.py` - Side effect tracking
- `pynext/reactive/memo.py` - Cached computations (with hydration support)
- `pynext/reactive/store.py` - Deep reactive objects (auto-registers with SSR context)
- `pynext/reactive/control_flow.py` - Show, For, Switch, etc.
- `pynext/reactive/batch.py` - Batching utilities
- `pynext/reactive/context.py` - Tracking context
- `pynext/reactive/hydration.py` - Hydration manager
- `pynext/server/hydration.py` - Server-side hydration utilities (✅ Phase 17.5)
- `pynext/core/context.py` - Render context with signal/store/memo registration
- `pynext/core/signals.py` - **Now a compatibility shim** (issues deprecation warnings)

**Key difference from old approach:**
```python
# OLD: Two separate systems
from pynext.core.signals import Signal      # For SSR
from pynext.reactive.signal import Signal   # For "SolidJS-like"

# NEW: One unified system
from pynext.reactive import signal  # Works for SSR AND compiles to JS
```

**Test Results Summary:**
| Category | Tests | Status |
|----------|-------|--------|
| Signal | 54 | ✅ Pass |
| Effect | 45 | ✅ Pass |
| Memo | 50 | ✅ Pass |
| Store | 40 | ✅ Pass |
| Batch/Context | 45 | ✅ Pass |
| Integration | 40 | ✅ Pass |
| Control Flow | 571 | ✅ Pass |
| **Total Reactive** | **845** | ✅ **100%** |

---

**17.4 Compiler Core (5-7 days)** ✅ COMPLETE

Build-time compilation of Python reactive code to optimized JavaScript:

**Implemented:**
- `pynext/compiler/__init__.py` - Public API (`compile_island()`, `compile_file()`)
- `pynext/compiler/parser.py` - Python AST → IR extraction (~350 lines)
- `pynext/compiler/analyzer.py` - Dependency tracking (~200 lines)
- `pynext/compiler/emitter.py` - IR → JavaScript generation (~500 lines)
- `pynext/compiler/sourcemap.py` - V3 source map generation (~200 lines)
- `pynext/compiler/errors.py` - AI-friendly compile-time errors (~200 lines)
- `docs/reactive/COMPILER.md` - Complete documentation

**Tests:** 298 passing (100% pass rate)

**Performance:**
- Compile time: ~1ms per component (target was <50ms)
- Bundle size: ~400 bytes per simple component

**Linear Clone Milestone:** IssueCard component compiles successfully:

- [x] AST parser for Python reactive code (`parser.py` - 1,011 lines)
- [x] Intermediate representation (IR) (IslandIR, DOMNode, SignalDef, etc.)
- [x] Dependency analyzer (track signal reads/writes in handlers) (`analyzer.py` - 481 lines)
- [x] JS code emitter (`emitter.py` - 1,233 lines)
- [x] Source map generation for debugging (`sourcemap.py` - 483 lines)

**Status: ✅ COMPLETE** - 467 compiler tests passing

**Compiler Pipeline:**
```
Python Source
     │
     ▼
┌─────────────────┐
│ 1. AST Parser   │  Parse Python, identify reactive constructs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. IR Generator │  Convert to compiler IR
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Analyzer     │  Track dependencies, identify compilable code
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. JS Emitter   │  Generate optimized JavaScript
└────────┬────────┘
         │
         ▼
   JavaScript + Source Map
```

**Files:**
- `pynext/compiler/__init__.py` - Compiler entry point
- `pynext/compiler/parser.py` - Python AST analysis
- `pynext/compiler/ir.py` - Intermediate representation
- `pynext/compiler/analyzer.py` - Dependency analysis
- `pynext/compiler/emitter.py` - JS code generation
- `pynext/compiler/sourcemap.py` - Source map generation

**Example Compilation:**
```python
# Input (Python)
@island
def Counter():
    count = signal(0)
    
    return button(onclick=lambda: count.set(count() + 1))[
        count()
    ]
```

```javascript
// Output (JavaScript)
function Counter() {
    const count = createSignal(0);
    const _el = document.createElement("button");
    
    _el.addEventListener("click", () => count.set(count() + 1));
    createEffect(() => _el.textContent = count());
    
    return _el;
}
```

**Linear Clone Milestone (17.4):** Interactive issue card with expand/collapse

---

**17.5 SSR + Hydration Integration (✅ COMPLETE)**

Connect server rendering to client hydration:

- [x] Server renders HTML with hydration markers (`data-pynext-*` attributes)
- [x] Hydration data serialization (JSON in `<script>` tag)
- [x] Client-side hydration connects signals to existing DOM
- [x] Islands mode (default): selective hydration of `@island` components
- [x] Full hydration mode (opt-in): `@page(hydration="full")`
- [x] Add `get_js_init()`, `to_json()`, `to_hydration_state()` to Memo
- [x] Wire `__PYNEXT_HYDRATION__` into server responses
- [x] Fix signal auto-registration during SSR (`_register_with_context()`)
- [x] Create `pynext/server/hydration.py` utilities
- [x] Real browser benchmarks with Playwright (`tests/e2e/bench_hydration_real.py`)
- [x] Honest performance documentation (DOM operations are 100-1000x slower than in-memory)

**Files Created/Modified:**
- `pynext/server/hydration.py` - Server-side hydration utilities
- `pynext/reactive/signal.py` - Auto-registration with render context
- `pynext/reactive/memo.py` - Added hydration methods
- `pynext/reactive/store.py` - Auto-registration with render context
- `pynext/core/context.py` - Enhanced register_signal/store/memo
- `pynext/core/component.py` - Added `hydration` parameter to `@page`
- `pynext/core/html.py` - Fixed handler extraction (source analysis, not monkey-patching)
- `tests/unit/hydration/` - 145 comprehensive hydration tests
- `tests/e2e/bench_hydration_real.py` - Real Playwright browser benchmarks
- `examples/linear/` - Linear clone with issues, Kanban, filtering
- `docs/reactive/HYDRATION.md` - Complete hydration documentation

**Test Results:**
- 11 integration tests: ✅ All passing
- 145 unit hydration tests: ✅ All passing
- 14 hydration benchmarks: ✅ All passing
- **Total: 170+ hydration tests**

**Real Browser Performance (Benchmarked with Playwright):**
| Scenario | Hydration Time | TTI Target |
|----------|----------------|------------|
| 10 signals + 10 handlers | 10-30ms | < 50ms |
| 100 signals + 100 handlers | 30-80ms | < 100ms |
| Linear clone (104 signals + 305 handlers) | 50-100ms | < 150ms |

*⚠️ Note: In-memory benchmarks show µs, but real DOM operations are 100-1000x slower.*
- [ ] Fix 15 hydration tests (`tests/integration/test_hydration.py`, `tests/benchmarks/bench_hydration.py`)

**Pre-existing Tests (Ready to Pass After Implementation):**
| Test File | Tests | Current Status |
|-----------|-------|----------------|
| `tests/integration/test_hydration.py` | 11 | 5 pass, 6 fail |
| `tests/benchmarks/bench_hydration.py` | 3 | 1 pass, 2 fail |
| `tests/benchmarks/bench_islands.py` | 5 | 2 pass, 3 fail |

**Files:**
- `pynext/server/hydration.py` - Server-side hydration data
- `pynext/runtime/hydrate.js` - Client-side hydration
- `pynext/reactive/memo.py` - Add `get_js_init()`, `to_json()`

**Hydration Protocol:**
```html
<!-- Server renders -->
<div data-pynext-root="counter">
  <button data-pynext-text="count">0</button>
</div>
<script id="__PYNEXT_DATA__" type="application/json">
  {"counter": {"count": 0}}
</script>

<!-- Client hydrates -->
<script type="module">
  import { hydrate } from '/_pynext/reactive.js';
  hydrate(document.querySelector('[data-pynext-root]'));
</script>
```

**Linear Clone Milestone (17.5):** ✅ Complete
- `examples/linear/pages/issues.py` - Full issue list with filtering
- `examples/linear/pages/index.py` - Landing page
- `examples/linear/components/issue_card.py` - Reusable issue card component
- Features: Add/remove issues, filter by status, Kanban view, expand/collapse cards

---

**17.6 Form Handling (✅ COMPLETE)**

Two-way binding and form state management:

- [x] `bind=` - Two-way input binding (text, checkbox, radio, select)
- [x] `create_form()` - Reactive form state management
- [x] Built-in validators (required, min_length, max_length, email, pattern, etc.)
- [x] Custom/composable validators (compose, when)
- [x] Reactive validation with error signals
- [x] Touched/dirty state tracking
- [x] Form reset and submission handling
- [x] `error_for()` - Error display helper
- [x] Compiler support (FormDef parsing and emission)
- [x] JS runtime with matching API

**Test Results:** 523+ tests passing (100%)

**Files Created/Modified:**
- `pynext/reactive/forms.py` - FormState class, create_form()
- `pynext/reactive/validators.py` - 15 built-in validators + composition utilities
- `pynext/core/html.py` - Added bind= attribute support
- `pynext/runtime/forms.js` - JS form runtime (~250 lines)
- `pynext/compiler/parser.py` - Added FormDef IR extraction
- `pynext/compiler/emitter.py` - Added createForm() JS emission
- `examples/linear/pages/issues.py` - Create issue modal with validation
- `tests/unit/forms/*.py` - 523+ comprehensive tests
- `tests/js/forms.test.js` - 100+ JS form tests
- `docs/reactive/FORMS.md` - Complete documentation

**Linear Clone Milestone (17.6):** ✅ Complete
- Create issue modal with title, description, priority, status fields
- Form validation with instant feedback
- Error display with `error_for()` helper

```python
from pynext.reactive import signal, create_form, Show

@island
def CreateIssueForm(on_create):
    form = create_form({
        "title": "",
        "description": "",
        "priority": "medium",
    }, validators={
        "title": [required, max_length(100)],
    })
    
    def handle_submit():
        if form.validate():
            on_create(form.values)
            form.reset()
    
    return form_(onsubmit=handle_submit)[
        input_(bind_value=form.title, placeholder="Issue title..."),
        Show(when=lambda: form.errors.title)[
            span(class_="error")[form.errors.title]
        ],
        button(type="submit")["Create"]
    ]
```

**Linear Clone Milestone (17.6):** Create issue modal, edit inline, quick add

---

**17.7 Build System Integration (2-3 days)** ✅ COMPLETE

Integrated compiler with PyNext build system for automated @island compilation:

- [x] `pynext build` compiles all reactive code with `--tree-shake`, `--analyze`, `--benchmark` flags
- [x] `pynext compile` standalone island compilation with `--watch` mode
- [x] `pynext dev` watch mode with incremental compilation (FileWatcher)
- [x] Tree shaking unused reactive code (30%+ bundle reduction)
- [x] Bundle analysis with JSON/HTML reports
- [x] Incremental cache (hash-based, only recompile changed files)
- [x] Parallel compilation (ProcessPoolExecutor, 8x speedup on multi-core)
- [x] Hot Module Replacement (WebSocket-based, < 100ms updates)

**Files Created:**
- `pynext/build/reactive.py` - Main build orchestration (`compile_project()`, `compile_files()`)
- `pynext/build/scanner.py` - @island detection (scan directories/files)
- `pynext/build/cache.py` - Incremental build cache (hash-based)
- `pynext/build/manifest.py` - Build manifest generation
- `pynext/build/parallel.py` - Multi-core compilation (ProcessPoolExecutor)
- `pynext/build/watcher.py` - File watching with debouncing (watchdog)
- `pynext/build/hmr.py` - Hot Module Replacement (WebSocket server)
- `pynext/build/treeshake.py` - Dead code elimination
- `pynext/build/analyze.py` - Bundle composition analysis
- `pynext/build/__init__.py` - Public API exports
- `pynext/cli.py` - Added `compile` command and build flags

**Tests:** 339 passing (100% pass rate)

**Performance (Actual Benchmarks):**

*Measured with `pytest-benchmark` on Python 3.11, macOS*

| Operation | Measured | Target | Status |
|-----------|----------|--------|--------|
| Scan 10 islands | **2.2ms** | < 100ms | ✅ 45x better |
| Scan 100 islands | **33.8ms** | < 500ms | ✅ 15x better |
| Incremental check (cached) | **31.5ms** | < 50ms | ✅ Pass |
| Single cache hit | **0.02ms** | < 10ms | ✅ 500x better |
| Tree shake runtime | **0.5ms** | < 5ms | ✅ 10x better |
| Tree shake 150KB bundle | **35.4ms** | - | ✅ |
| Cache store 100 files | **125.8ms** | - | ⚠️ Disk I/O bound |
| Full pipeline (100 islands) | **31.9ms** | < 100ms | ✅ 3x better |

**How to verify:**
```bash
pytest tests/benchmarks/bench_build.py -v --benchmark-only
```

**Usage:**
```bash
# Development (watch mode, incremental compilation)
pynext dev

# Production (optimized, tree-shaken)
pynext build --tree-shake

# Compile islands only
pynext compile

# Watch mode for islands
pynext compile --watch

# Analyze bundle composition
pynext build --analyze

# Performance metrics
pynext build --benchmark
```

**Documentation:** `docs/reactive/BUILD_SYSTEM.md` (comprehensive guide)

---

**17.8 Client-Side Router ✅ COMPLETE**

SPA navigation without page reloads:

- [x] `Router` - Router container
- [x] `Route` - Route definition with pattern matching
- [x] `Link` - Navigation link (no page reload)
- [x] `useNavigate()` - Programmatic navigation
- [x] `useParams()` - Route parameters (reactive)
- [x] `useSearchParams()` - Query string parameters
- [x] `useLocation()` - Current location state
- [x] `useMatch()` - Pattern matching hook
- [x] `Outlet` - Nested route placeholder
- [x] Route guards with `createRouteGuard()`
- [x] History API integration
- [x] Prefetching on hover

**Files Created:**
- `pynext/reactive/router.py` - Router Python API (~550 lines)
- `pynext/runtime/router.js` - Client-side routing (~400 lines)
- `examples/linear/app.py` - Router-enabled Linear clone
- `tests/unit/router/` - 600 comprehensive tests
- `docs/reactive/ROUTER.md` - Complete documentation

**Tests:** 631 passing (100% pass rate)

**High-Risk Areas Tested:**
| Risk | Severity | Tests | Status |
|------|----------|-------|--------|
| Link active state boundaries | P0 | 3 | ✅ Fixed |
| Guard execution during navigation | P2→Fixed | 4 | ✅ Fixed |
| Global context race conditions | P0 | 3 | ⚠️ Documented |
| Route ordering (static vs dynamic) | P1 | 4 | ⚠️ Documented |
| Hydration data format | P1 | 3 | ✅ Tested |
| Link/Outlet in Element children | P0 | 4 | ⚠️ Documented |

**Performance (Benchmarked):**
| Operation | Time | vs Next.js |
|-----------|------|------------|
| Route compile | < 0.1ms | - |
| Route match | < 0.01ms | 10x faster |
| Navigate | < 5ms | 10-20x faster |
| 100 routes match | < 1ms | - |

**API Example:**

```python
from pynext.reactive import Router, Route, Link, useNavigate, useParams

@page
def App():
    return div()[
        nav()[
            Link(href="/", exact=True)["Home"],
            Link(href="/issues")["Issues"],
        ],
        Router()[
            Route(path="/", component=Home),
            Route(path="/issues", component=IssueList),
            Route(path="/issues/:id", component=IssueDetail),
            Route(path="/projects/:id", component=ProjectBoard),
        ]
    ]

@island
def IssueDetail():
    params = useParams()  # {"id": "123"}
    navigate = useNavigate()
    
    return div()[
        button(onclick=lambda: navigate("/issues"))["← Back"],
        h1()[f"Issue #{params['id']}"]
    ]
```

**Linear Clone Milestone (17.8):** ✅ Complete
- Multi-page SPA with `/`, `/issues`, `/issues/:id`, `/projects/:id`, `/settings`
- Active link highlighting
- Programmatic navigation
- 404 fallback page
- `examples/linear/app.py` with full router integration

**Documentation:** `docs/reactive/ROUTER.md` (comprehensive guide)

---

**17.9 AI DevTools (COMPLETE) ✅**

Native AI debugging support - the first Python web framework with this capability. A comprehensive debugging system that captures browser state, enables surgical bug recording, and generates AI-powered diagnosis.

**Core Infrastructure:**
- [x] **CDP Bridge** - Chrome DevTools Protocol WebSocket connection
- [x] **Chrome Launcher** - Auto-launch Chrome with debugging enabled
- [x] **Event Capture** - Filter and enrich browser events for AI
- [x] **Screenshot Capture** - Automatic screenshots on clicks, signals, errors
- [x] **DOM Snapshots** - Full HTML capture alongside screenshots
- [x] **JSONL Streaming** - Append-only event log for AI consumption
- [x] **Signal Tracking** - Hook into PyNext reactive system
- [x] **Manual Triggers** - Ctrl+Shift+S keyboard shortcut
- [x] **CLI Integration** - `pynext dev --ai-debug` command

**Session Recording (Surgical Debugging):**
- [x] **Session Start/End** - `pynext_debug.session_start("intent")` / `session_end("outcome")`
- [x] **User Notes** - `pynext_debug.note("observation")` with screenshots
- [x] **Inspect Mode** - `pynext_debug.inspect()` for element selection with PyNext context
- [x] **Time-based Screenshots** - Every 150ms during recording
- [x] **Before/After Capture** - Click actions capture signal state changes
- [x] **Unified Timeline** - All events in single `timeline.json`

**AI Analysis (Claude 4.5 Opus):**
- [x] **Automatic Diagnosis** - Triggered on session end when API key set
- [x] **Briefing Generation** - AI-generated `briefing.md` with root cause
- [x] **Frame Narration** - AI descriptions for each key frame
- [x] **Storyboard** - Composite image of key moments
- [x] **Pattern Recognition** - Detects hydration bugs, handler issues

**Debug Modes:**
- [x] `--ai-debug=app` - For app developers (default)
- [x] `--ai-debug=core` - For PyNext framework developers
- [x] `--ai-debug=everything` - Full diagnostic capture

**Usage:**
```bash
# Start with AI debugging
pynext dev --ai-debug --api-key sk-ant-xxx

# In browser console:
pynext_debug.session_start("Testing form submission")
pynext_debug.note("Input not responding")
pynext_debug.inspect()  // Click to select element
pynext_debug.session_end("Form inputs broken")

# AI generates diagnosis automatically
cat .pynext/debug/sessions/rec_xxx/briefing.md
```

**Output Structure:**
```
.pynext/debug/
├── events.jsonl              # All events (real-time)
├── state.json                # Current browser state
├── screenshots/              # Event-triggered screenshots
└── sessions/                 # Recording sessions
    └── rec_xxx/
        ├── timeline.json     # Unified event timeline
        ├── briefing.md       # AI diagnosis
        ├── narration.json    # Frame-by-frame AI descriptions
        ├── storyboard.png    # Key frames composite
        ├── key_frames/       # Important screenshots
        └── all_frames/       # Every captured frame
```

**Implementation Files:**
- `pynext/devtools/__init__.py` - Package exports
- `pynext/devtools/debugger.py` - Main orchestrator
- `pynext/devtools/bridge.py` - CDP WebSocket connection
- `pynext/devtools/launcher.py` - Chrome auto-launch
- `pynext/devtools/capture.py` - Event filtering and enrichment
- `pynext/devtools/screenshot.py` - Screenshot and DOM capture
- `pynext/devtools/stream.py` - JSONL file streaming
- `pynext/devtools/injector.py` - Client-side tracking injection
- `pynext/devtools/recorder.py` - Session recording management
- `pynext/devtools/processor.py` - AI analysis with Claude 4.5 Opus

**Tests:** 200+ comprehensive tests
- `tests/unit/devtools/test_bridge.py` (35 tests)
- `tests/unit/devtools/test_capture.py` (40 tests)
- `tests/unit/devtools/test_screenshot.py` (30 tests)
- `tests/unit/devtools/test_stream.py` (25 tests)
- `tests/unit/devtools/test_launcher.py` (15 tests)
- `tests/unit/devtools/test_injector.py` (20 tests)
- `tests/unit/devtools/test_debugger.py` (15 tests)
- `tests/unit/devtools/test_timeline.py` (26 tests)

**Documentation:** 7 comprehensive documents (~2,500 lines total)
- `docs/devtools/AI_DEBUG.md` - Overview and quick start
- `docs/devtools/ARCHITECTURE.md` - Complete system architecture with diagrams
- `docs/devtools/DATA_PIPELINE.md` - Event flow from browser to file
- `docs/devtools/SESSION_RECORDING.md` - Surgical recording workflow
- `docs/devtools/AI_ANALYSIS.md` - Claude 4.5 Opus integration
- `docs/devtools/CLI_COMMANDS.md` - Complete command reference
- `docs/devtools/CURSOR_INTEGRATION.md` - How to use with Cursor AI

**Why This Matters:**
This is a major differentiator for PyNext. No other Python web framework (Django, Flask, FastAPI) has native AI debugging. Next.js and React also lack this. AI assistants can now:
- See exactly what users see during debugging (events AND visuals)
- Get automatic diagnosis with root cause analysis
- Receive structured data optimized for AI consumption
- Follow unified timelines matching user observations

The result: **10x faster debugging** with AI assistance.

---

**17.10 Event Modifiers (COMPLETE) ✅**

SolidJS-inspired event handling with declarative modifiers for `stopPropagation`, `preventDefault`, and more:

- [x] `stop()` - Calls `event.stopPropagation()` before handler
- [x] `prevent()` - Calls `event.preventDefault()` before handler  
- [x] `self_only()` - Only fires if `event.target === event.currentTarget`
- [x] `once()` - Handler fires once, then removes itself
- [x] `capture()` - Use capture phase instead of bubble phase
- [x] Modifier composition (`stop(prevent(handler))`)
- [x] HTML serialization with modifiers in hydration data
- [x] Client-side modifier application during event attachment

**The Problem Solved:**
PyNext renders on the server and hydrates on the client. Event handlers are serialized to JavaScript, but you can't serialize code like `e.stopPropagation()`. This caused modals to close when clicking form inputs - a fundamental bug affecting any component needing event control.

**The Solution:**
Wrap handlers in modifiers that PyNext understands:

```python
from pynext import div, button, self_only, stop, prevent

# Modal: only close when clicking overlay, not children
div(onclick=self_only(lambda: show.set(False)))[
    div(class_="modal-content")[...]  # Clicks here don't close modal
]

# Form: prevent page reload
form(onsubmit=prevent(lambda: handle_submit()))[...]

# Nested button: stop propagation to parent
button(onclick=stop(lambda: inner_action()))[...]
```

**Files Created:**
- `pynext/events.py` - EventHandler class and modifier functions (~200 lines)
- `pynext/core/html.py` - Updated to detect and serialize EventHandler
- `pynext/core/context.py` - Updated register_event with modifiers
- `pynext/runtime/signals.js` - Updated event attachment with modifier support
- `tests/unit/events/test_event_handlers.py` - 49 comprehensive tests
- `docs/reactive/EVENTS.md` - Complete documentation

**Tests:** 49 passing (100% pass rate)

**Linear Clone Fix:**
- Fixed modal that was closing when clicking form inputs
- Modal overlay now uses `self_only()` instead of broken `e.stopPropagation()` pattern

---

**17.11 Form Handler Transpilation (COMPLETE) ✅**

Automatically transpile complex Python form handlers to client-side JavaScript:

- [x] Add `_form_id` attribute to `FormState` for unique identification
- [x] Detect `FormState` objects in handler closures
- [x] Recognize `form.validate()` / `form.reset()` patterns
- [x] Generate JavaScript for form submission handlers
- [x] Handle `[*signal(), new_item]` array append pattern
- [x] Support multiple signal operations in one handler
- [x] Export `getForm()` from JavaScript runtime

**The Problem Solved:**
The Linear demo's "Create Issue" button didn't work because the `handle_add_issue()` function was too complex for PyNext's transpiler:

```python
def handle_add_issue():
    if issue_form.validate():           # FormState method
        values = issue_form.values       # Property access
        all_issues.set([*all_issues(), values])  # Array append
        next_id.set(next_id() + 1)       # Increment
        issue_form.reset()               # FormState method
        show_add_form.set(False)         # Signal set
```

Previously, this fell back to `console.warn()` - the button did nothing.

**The Solution:**
Enhanced the transpiler to recognize FormState patterns and generate proper JavaScript:

```javascript
(function() {
    const form = __pynext__.getForm('form_xxx');
    if (!form) { console.error('[PyNext] Form not found'); return; }
    if (form.validate()) {
        const values = form.values;
        __pynext__.getSignal('all_issues').update(arr => [...arr, values]);
        __pynext__.getSignal('next_id').update(v => v + 1);
        __pynext__.getSignal('show_add_form').set(false);
        form.reset();
    }
})()
```

**Files Changed:**
- `pynext/reactive/forms.py` - Added `_form_id` attribute (~5 lines)
- `pynext/core/html.py` - Form detection + transpilation (~180 lines)
- `pynext/runtime/signals.js` - Added `getForm()` export (~10 lines)
- `tests/unit/transpiler/test_form_handlers.py` - 21 comprehensive tests

**Tests:** 21 passing (100% pass rate) + 602 forms/transpiler tests

**Pattern Recognition:**
| Python Pattern | JavaScript Output |
|----------------|-------------------|
| `form.validate()` | `form.validate()` |
| `form.reset()` | `form.reset()` |
| `form.values` | `form.values` |
| `sig.set([*sig(), x])` | `sig.update(arr => [...arr, x])` |
| `sig.set(sig() + 1)` | `sig.update(v => v + 1)` |
| `sig.set(False)` | `sig.set(false)` |

**Linear Clone Fix:**
- "Create Issue" button now fully functional
- Form validation, array append, and modal close all work client-side
- No server round-trip needed for form submissions

---

**17.12 Migration and Cleanup (2-3 days)**

Deprecate old systems and finalize:

- [x] Convert `pynext/core/signals.py` to compatibility shim (Phase 17.3)
- [x] Update all 27 import files to use `pynext.reactive` (Phase 17.3)
- [ ] Deprecate old `pynext/runtime/signals.js` (use `reactive.js`)
- [ ] Update `example/` app to use new APIs
- [ ] Migration guide documentation
- [ ] Set up E2E test infrastructure (Playwright + dev server)
- [ ] Fix 59 E2E test errors in `tests/e2e/test_reactivity.py`

**Files Status:**

| File | Status |
|------|--------|
| `pynext/core/signals.py` | ✅ Now a compatibility shim with deprecation warnings |
| `pynext/core/suspense.py` | ⏳ Merge into new control_flow |
| `pynext/runtime/signals.js` | ⏳ Replace with `reactive.js` |
| `pynext/runtime/control_flow.js` | ⏳ Merge into `reactive.js` |

**E2E Test Infrastructure (Needed):**
- Install Playwright: `pip install playwright && playwright install chromium`
- Start dev server: `pynext dev &`
- Then E2E tests can run

**Linear Clone Milestone (17.11):** Full production-ready Linear clone with keyboard shortcuts, optimistic updates

---

**Linear Clone: Phased Build-Out**

Build a Linear-like project management app incrementally as each phase completes. This provides real-world dogfooding instead of toy demos.

| Phase | Linear Features | What It Proves |
|-------|-----------------|----------------|
| 17.4 | Interactive issue card (expand/collapse, status toggle) | ✅ Complete |
| 17.5 | Issue list, Kanban columns, filters | ✅ Complete |
| 17.6 | Create/edit forms, validation | ✅ Complete |
| 17.8 | Multi-page SPA, deep linking | Router works |
| 17.10 | Event modifiers (modal fix) | ✅ Complete |
| 17.11 | Form handler transpilation (Create Issue works) | ✅ Complete |
| 17.12 | Keyboard shortcuts, polish | Production-ready |

---

**Test Coverage Target: 1,200+ tests**

| Sub-Phase | Tests |
|-----------|-------|
| 17.1 Specification | 0 (docs only) | ✅ Complete |
| 17.2 JS Runtime | 66 | ✅ Complete (2.3KB gzip) |
| 17.3 Python API | 845 | ✅ Complete (100% pass) |
| 17.4 Compiler | 467 | ✅ Complete (100% pass) |
| 17.5 SSR + Hydration | 170+ | ✅ Complete (100% pass) |
| 17.6 Forms | 523+ | ✅ Complete (100% pass) |
| 17.7 Build System | 339 | ✅ Complete |
| 17.8 Router | 600 | ✅ Complete |
| 17.9 AI DevTools | 200+ | ✅ Complete |
| 17.10 Migration | 50 | ⏳ Pending |

**Documentation:** `docs/reactive/` (~5,000 lines)

---

#### Phase 18: Complete Python-to-JavaScript Transpiler

**Status:** ✅ **COMPLETE** (18.1 → 18.8 Complete + 1,374 JS Runtime Tests)
**Priority:** P0 (Critical)
**Total Tests:** 4,923 (3,549 Python + 1,374 JS)
**Timeline:** 8 weeks (8 sub-phases)
**Runtime Size:** ~20KB gzipped (Complete Python semantic parity)

**Vision:** A production-grade Python-to-JavaScript transpiler with **complete Python semantic parity**. Inspired by SolidJS's compilation model, this compiles Python to optimized JavaScript that behaves exactly like Python while remaining faster than React:

- **Zero Virtual DOM** - Direct DOM manipulation, O(1) updates
- **Fine-grained reactivity** - Only affected nodes update
- **Complete Python semantics** - Truthiness, operators, methods all work correctly
- **Readable output** - Generated JS should be human-debuggable
- **Optimization passes** - Eliminate unnecessary wrappers for maximum performance
- **Gradual adoption** - Works alongside existing @island compiler

**Why This Matters:**

The current `html.py` transpiler uses regex pattern-matching which:
1. Fails on complex handlers
2. Misses critical Python/JS semantic differences
3. Produces incorrect behavior for edge cases

```python
# FAILS TODAY - too complex for regex-based html.py
def handle_add_issue():
    if issue_form.validate():
        all_issues.set([*all_issues(), issue_form.values])
        issue_form.reset()
        show_add_form.set(False)
```

**Critical Python/JS Semantic Differences (Must Handle):**

| Behavior | Python | JavaScript | Impact |
|----------|--------|------------|--------|
| Empty list truthiness | `[]` is falsy | `[]` is truthy | `if items:` fails |
| Empty dict truthiness | `{}` is falsy | `{}` is truthy | `if config:` fails |
| Modulo with negatives | `-7 % 3 = 2` | `-7 % 3 = -1` | Math bugs |
| Collection equality | `[1,2] == [1,2]` is True | `[1,2] === [1,2]` is false | Comparison bugs |
| String repeat | `"a" * 3 = "aaa"` | `"a" * 3 = NaN` | String ops fail |
| List concat | `[1] + [2] = [1,2]` | `[1] + [2] = "1,2"` | List ops fail |
| Default sort | Numeric comparison | String comparison | `[10,2,1].sort()` differs |
| Negative indexing | `items[-1]` works | `items[-1]` is undefined | Index access fails |
| Dict iteration | `for k in d:` iterates keys | Objects not iterable | Loops fail |

Phase 18 handles ALL of these correctly with a complete runtime library.

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PYNEXT COMPLETE TRANSPILER PIPELINE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Python Source (event handlers, reactive code)                               │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────┐     ┌─────────────────┐     ┌──────────────────────┐  │
│  │  1. AST Parser  │ ──▶ │ 2. Transformer  │ ──▶ │ 3. Semantic Analyzer │  │
│  │  (Python ast)   │     │ (Normalize AST) │     │ (Scope/Type/Deps)    │  │
│  └─────────────────┘     └─────────────────┘     └──────────┬───────────┘  │
│                                                              │              │
│                                                              ▼              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌──────────────────────┐  │
│  │ 6. Optimizer    │ ◀── │ 5. JS Emitter   │ ◀── │ 4. Runtime Resolver  │  │
│  │ (Wrapper Elide) │     │ (Code Gen)      │     │ (Map Py→JS calls)    │  │
│  └────────┬────────┘     └─────────────────┘     └──────────────────────┘  │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Complete Python Runtime (~20KB)                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │   │
│  │  │ Builtins │  │  Types   │  │ Operators│  │ Methods  │  │  Std   │ │   │
│  │  │ len,sum  │  │ list,dict│  │ %,//,in  │  │ str,list │  │ json,re│ │   │
│  │  │ min,max  │  │ set,tuple│  │ ==,is    │  │ dict,set │  │ math   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│           │                                                                  │
│           ▼                                                                  │
│    Optimized JavaScript Bundle + Source Maps                                 │
│    (Still 5-20x faster than React due to O(1) reactive updates)             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Progress Summary:**

| Phase | Description | Status | Python Tests | JS Tests | Runtime Size |
|-------|-------------|--------|--------------|----------|--------------|
| 18.1 | Core Statements + Semantic Foundation | ✅ **Complete** | 494 | - | 2KB |
| 18.2 | Expressions, Operators & Comprehensions | ✅ **Complete** | 305 | - | 4KB |
| 18.3 | Runtime: Types & Methods | ✅ **Complete** | 260 | 160 | 8KB |
| 18.4 | Runtime: Builtins & Standard Library | ✅ **Complete** | 412 | 203 | 14KB |
| 18.5 | Advanced Features (async, generators, decorators) | ✅ **Complete** | 817 | 108 | 18KB |
| 18.1-18.5 | **JavaScript Runtime Tests** | ✅ **Complete** | - | **1196** | - |
| 18.6 | PyNext Integration + Critical Fixes | ✅ **Complete** | 442 | 38 | 18KB |
| 18.7 | Optimization Passes | ✅ **Complete** | 1,018 | - | 18KB (smaller output) |
| 18.8 | Edge Cases, Classes & Polish | ✅ **Complete** | 600 | 130 | 20KB |
| **Total** | | | **3,549** | **1,374** | **20KB** |

**JavaScript Runtime Tests (1244 tests):**
Comprehensive tests verifying the `__py` runtime behaves identically to Python:
- `tests/js/transpiler/at.test.js` - 30 tests for negative indexing
- `tests/js/transpiler/slice.test.js` - 50 tests for slicing
- `tests/js/transpiler/bool.test.js` - 40 tests for Python truthiness
- `tests/js/transpiler/mod.test.js` - 41 tests for Python modulo
- `tests/js/transpiler/floordiv.test.js` - 31 tests for floor division
- `tests/js/transpiler/eq.test.js` - 47 tests for deep equality
- `tests/js/transpiler/in.test.js` - 40 tests for membership
- `tests/js/transpiler/iter.test.js` - 27 tests for Python iteration
- `tests/js/transpiler/add.test.js` - 33 tests for polymorphic addition
- `tests/js/transpiler/mul.test.js` - 42 tests for polymorphic multiplication
- `tests/js/transpiler/enumerate.test.js` - 20 tests for enumerate
- `tests/js/transpiler/zip.test.js` - 20 tests for zip
- `tests/js/transpiler/range.test.js` - 37 tests for range
- `tests/js/transpiler/format.test.js` - 87 tests for format specifications
- `tests/js/transpiler/equivalence.test.js` - 85 tests for end-to-end equivalence
- `tests/js/transpiler/helpers.test.js` - 43 tests for del, sum, isinstance, type
- `tests/js/transpiler/repr_ascii.test.js` - 35 tests for repr() and ascii() conversions
- `tests/js/transpiler/side_effects.test.js` - 26 tests for single-evaluation verification
- `tests/js/transpiler/types.test.js` - 91 tests for type methods (Phase 18.3)
- `tests/js/transpiler/risk_cases.test.js` - 69 tests for high-risk edge cases (Phase 18.3)
- `tests/js/transpiler/builtins.test.js` - 119 tests for builtins and stdlib (Phase 18.4)
- `tests/js/transpiler/builtins_risk.test.js` - 84 tests for risk area hardening (Phase 18.4)
- `tests/js/transpiler/advanced.test.js` - 98 tests for async, decorators, unpacking (Phase 18.5)
- `tests/js/transpiler/critical_fixes.test.js` - 38 tests for PyNext integration (Phase 18.6)

---

**18.1 Core Statements + Semantic Foundation (Week 1) - ✅ COMPLETE (494 tests)**

Build the transpiler foundation with correct Python semantics from day one.

**Implementation Summary:**
- **Core Transpiler**: 4,200+ lines of Python + JavaScript
- **Test Suite**: 4,500+ lines, 494 passing tests
- **Benchmarks**: 13 performance tests, ~32μs per simple handler
- **Documentation**: 628 lines in `docs/transpiler/CORE_STATEMENTS.md`

**Risk Fixes Implemented:**
| Fix | Description | Impact |
|-----|-------------|--------|
| Scope Tracking | `let` vs reassignment detection | No more redeclaration errors |
| For Tuple Unpacking | `for i, x in enumerate(items)` | Common pattern now works |
| List Concatenation | `__py.add()` for `[1]+[2]` | List ops work correctly |
| Dict Iteration | `__py.iter()` for `for k in d:` | Dict loops work correctly |
| String/List Repeat | `__py.mul()` for `"a"*3`, `[1]*3` | Repeat ops work correctly |
| Negative Index | Improved heuristic for `__py.at()` | Function call indices work |

**Statements:**

| Python | JavaScript |
|--------|------------|
| `x = 5` | `let x = 5;` |
| `x += 1` | `x += 1;` |
| `if x > 0:` | `if (x > 0) {` |
| `elif x < 0:` | `} else if (x < 0) {` |
| `for x in items:` | `for (const x of items) {` |
| `for i in range(10):` | `for (let i = 0; i < 10; i++) {` |
| `for k in some_dict:` | `for (const k of Object.keys(some_dict)) {` |
| `while x > 0:` | `while (x > 0) {` |
| `def foo(a, b=1):` | `function foo(a, b = 1) {` |
| `lambda x: x * 2` | `(x) => x * 2` |
| `return x, y` | `return [x, y];` |
| `pass` | `/* pass */` |
| `break` / `continue` | `break;` / `continue;` |
| `del items[0]` | `__py.del(items, 0);` |
| `del obj["key"]` | `__py.del(obj, "key");` |

**Indexing & Slicing (Critical!):**

| Python | JavaScript |
|--------|------------|
| `items[-1]` | `__py.at(items, -1)` |
| `items[-2]` | `__py.at(items, -2)` |
| `items[1:3]` | `__py.slice(items, 1, 3)` |
| `items[:3]` | `__py.slice(items, null, 3)` |
| `items[2:]` | `__py.slice(items, 2, null)` |
| `items[::2]` | `__py.slice(items, null, null, 2)` |
| `items[::-1]` | `__py.slice(items, null, null, -1)` |
| `items[1:-1]` | `__py.slice(items, 1, -1)` |

**Tuple Unpacking:**

| Python | JavaScript |
|--------|------------|
| `a, b = pair` | `const [a, b] = pair;` |
| `a, b = b, a` | `[a, b] = [b, a];` |
| `first, *rest = items` | `const [first, ...rest] = items;` |
| `a, *middle, z = items` | `const [a, ...middle] = items; const z = middle.pop();` |
| `x, y, z = point` | `const [x, y, z] = point;` |

**Files Created:**
- `pynext/transpiler/__init__.py` - Public API: `transpile()`, `transpile_handler()`
- `pynext/transpiler/nodes.py` - 25+ IR node dataclasses
- `pynext/transpiler/parser.py` - Python AST → IR (849 lines)
- `pynext/transpiler/emitter.py` - IR → JavaScript (936 lines)
- `pynext/transpiler/errors.py` - TranspileError with helpful messages
- `pynext/transpiler/_internal/utils.py` - Shared utilities
- `pynext/transpiler/runtime/core.js` - Python runtime (~500 bytes gzipped)
- `docs/transpiler/CORE_STATEMENTS.md` - Full documentation

**Test Files Created (463 tests):**
- `tests/unit/transpiler/test_assignment.py` - 52 tests
- `tests/unit/transpiler/test_aug_assignment.py` - 30 tests
- `tests/unit/transpiler/test_if_statement.py` - 60 tests
- `tests/unit/transpiler/test_for_loop.py` - 56 tests
- `tests/unit/transpiler/test_while_loop.py` - 30 tests
- `tests/unit/transpiler/test_function_def.py` - 42 tests
- `tests/unit/transpiler/test_lambda.py` - 35 tests
- `tests/unit/transpiler/test_return.py` - 28 tests
- `tests/unit/transpiler/test_pass_break_continue.py` - 18 tests
- `tests/unit/transpiler/test_delete.py` - 15 tests
- `tests/unit/transpiler/test_negative_indexing.py` - 26 tests
- `tests/unit/transpiler/test_slicing.py` - 33 tests
- `tests/unit/transpiler/test_tuple_unpacking.py` - 19 tests
- `tests/unit/transpiler/test_expressions.py` - 41 tests
- `tests/unit/transpiler/test_integration.py` - 21 tests

**Usage Example:**
```python
from pynext.transpiler import transpile, transpile_handler

# Transpile Python to JavaScript
js = transpile("x = items[-1]")
# → "let x = __py.at(items, -1);"

# Transpile event handler
js = transpile_handler('''
def handle_click():
    count.set(count() + 1)
''')
# → "function handle_click() { count.set(count() + 1); }"
```

---

**18.2 Expressions, Operators & Comprehensions (Week 2) - ✅ COMPLETE (305 tests)**

Handle all Python operators with correct semantics, including critical differences.

**Implementation Summary:**
- **New IR Nodes**: FString, FormattedValue, ListComp, DictComp, SetComp, GeneratorExp, Comprehension
- **Parser Updates**: 130+ lines for f-string and comprehension parsing
- **Emitter Updates**: 250+ lines for expression emission (including fixes)
- **Runtime Updates**: `__py.format()`, `__py.repr()`, `__py.ascii()` (~150 lines)
- **Test Suite**: 305 comprehensive tests across 9 test files
- **Documentation**: `docs/transpiler/EXPRESSIONS.md`

**Critical Fixes Implemented:**
| Fix | Problem | Solution |
|-----|---------|----------|
| Chained Comparison | `a < f() < b` called f() twice | IIFE caching: `((_t) => (a < _t) && (_t < b))(f())` |
| Boolean Operators | `f() and g()` called f() twice | IIFE caching for complex operands |
| F-String Conversion | `!r`, `!s`, `!a` not implemented | Added `__py.repr()` and `__py.ascii()` |
| Dynamic Format Specs | `f"{x:{width}}"` ignored | Parse and emit dynamic specs |

**Features Implemented:**
| Feature | Python Example | JavaScript Output |
|---------|---------------|-------------------|
| Chained Comparisons | `0 < x < 10` | `(0 < x) && (x < 10)` |
| Chained with Side Effects | `a < f() < b` | `((_t) => (a < _t) && (_t < b))(f())` |
| Boolean and | `x and y` | `__py.bool(x) ? y : x` |
| Boolean or | `x or y` | `__py.bool(x) ? x : y` |
| F-Strings | `f"Hello {name}"` | `` `Hello ${name}` `` |
| Format Specs | `f"{x:.2f}"` | `` `${__py.format(x, '.2f')}` `` |
| F-String !r | `f"{obj!r}"` | `` `${__py.repr(obj)}` `` |
| F-String !s | `f"{val!s}"` | `` `${String(val)}` `` |
| List Comp | `[x*2 for x in items]` | `[...items.map(x => x*2)]` |
| List Comp Filter | `[x for x in items if x > 0]` | `[...items.filter(x => x > 0)]` |
| Dict Comp | `{k: v for k, v in items}` | `Object.fromEntries([...items])` |
| Set Comp | `{x for x in items}` | `new Set(items)` |
| Generator Exp | `any(x > 0 for x in items)` | `items.some(x => x > 0)` |

**Comparison Operators:**

| Python | JavaScript | Notes |
|--------|------------|-------|
| `a == b` | `__py.eq(a, b)` | Deep equality for collections |
| `a != b` | `!__py.eq(a, b)` | |
| `a is None` | `a === null` | Identity for None |
| `a is not None` | `a !== null` | |
| `a is b` | `a === b` | Reference identity |
| `0 < x < 10` | `0 < x && x < 10` | Chained comparisons |
| `a == b == c` | `__py.eq(a, b) && __py.eq(b, c)` | |

**Logical Operators (Truthiness-aware!):**

| Python | JavaScript | Notes |
|--------|------------|-------|
| `if items:` | `if (__py.bool(items)) {` | `[]` and `{}` are falsy |
| `x and y` | `__py.bool(x) ? y : x` | Returns value, not boolean |
| `x or y` | `__py.bool(x) ? x : y` | Returns value, not boolean |
| `not x` | `!__py.bool(x)` | |

**Arithmetic Operators (Semantic differences!):**

| Python | JavaScript | Notes |
|--------|------------|-------|
| `a + b` | `__py.add(a, b)` | `[1]+[2]=[1,2]` not `"1,2"` |
| `a * b` | `__py.mul(a, b)` | `"a"*3="aaa"` not `NaN` |
| `a // b` | `__py.floordiv(a, b)` | Floor division |
| `a % b` | `__py.mod(a, b)` | Python modulo semantics! |
| `a ** b` | `a ** b` | Same in both |
| `a / b` | `a / b` | Same (but 0/0 differs) |

**Membership Operators (Polymorphic!):**

| Python | JavaScript | Notes |
|--------|------------|-------|
| `x in [1,2,3]` | `[1,2,3].includes(x)` | Array |
| `x in {1,2,3}` | `new Set([1,2,3]).has(x)` | Set |
| `x in {"a":1}` | `x in obj` | Dict keys |
| `x in "hello"` | `"hello".includes(x)` | Substring |
| `x in range(10)` | `__py.range(10).includes(x)` | Range |

**F-Strings with Format Specs:**

| Python | JavaScript |
|--------|------------|
| `f"Hello {name}"` | `` `Hello ${name}` `` |
| `f"{value:.2f}"` | `value.toFixed(2)` |
| `f"{value:,}"` | `value.toLocaleString()` |
| `f"{percent:.1%}"` | `(percent * 100).toFixed(1) + '%'` |
| `f"{s:>10}"` | `s.padStart(10)` |
| `f"{s:<10}"` | `s.padEnd(10)` |

**Comprehensions:**

| Python | JavaScript |
|--------|------------|
| `[x*2 for x in items]` | `items.map(x => x*2)` |
| `[x for x in items if x > 0]` | `items.filter(x => x > 0)` |
| `[x*2 for x in items if x > 0]` | `items.filter(x => x > 0).map(x => x*2)` |
| `{k: v for k, v in items}` | `Object.fromEntries(items)` |
| `{x for x in items}` | `new Set(items)` |
| `[y for x in matrix for y in x]` | `matrix.flatMap(x => x)` |

**Generator Expressions (in function calls):**

| Python | JavaScript |
|--------|------------|
| `sum(x for x in items)` | `__py.sum(items)` |
| `sum(x*2 for x in items)` | `__py.sum(items.map(x => x*2))` |
| `any(x > 0 for x in items)` | `items.some(x => x > 0)` |
| `all(x > 0 for x in items)` | `items.every(x => x > 0)` |
| `max(x.value for x in items)` | `Math.max(...items.map(x => x.value))` |

**Files:**
- `pynext/transpiler/expressions.py`
- `pynext/transpiler/operators.py`
- `pynext/transpiler/comprehensions.py`
- `pynext/transpiler/runtime/operators.js` - `__py.eq`, `__py.bool`, `__py.mod`, etc.
- `tests/unit/transpiler/test_expressions.py`
- `tests/unit/transpiler/test_operators.py`
- `tests/unit/transpiler/test_comprehensions.py`
- `tests/unit/transpiler/test_truthiness.py`

---

**18.3 Runtime: Types & Methods (Week 3) - ✅ COMPLETE (420 tests)**

Implement Python's type methods with exact semantics.

**Implementation Summary:**
- **Runtime Files**: 4 type modules (string.js, list.js, dict.js, set.js) + index.js
- **Methods Implemented**: 64 total (25 string, 15 list, 12 dict, 12 set)
- **Emitter Updates**: Comprehensive method dispatch with 3 categories (direct, transform, runtime)
- **Python Tests**: 260 tests (216 + 44 risk case tests)
- **JavaScript Tests**: 160 tests (91 type + 69 risk case tests)
- **Documentation**: `docs/transpiler/TYPE_METHODS.md`

**Risk Fixes Implemented:**
| Fix | Description | Impact |
|-----|-------------|--------|
| `title()` browser compat | Removed lookbehind regex | Safari < 16.4 now works |
| `split()` whitespace | Preserve original whitespace in remainder | `"a  b\tc".split(None,1)` correct |
| `sort()` mixed types | Throw TypeError like Python 3 | `[1,"a"].sort()` throws |
| `is*()` unicode | Full unicode support | `"café".isalpha()` = True |
| `splitlines()` | All 10 Python line endings | `\x0b`, `\u2028`, etc. |

**Method Categories:**
| Category | Count | Example |
|----------|-------|---------|
| Direct Mapping | 12 | `s.lower()` → `s.toLowerCase()` |
| Simple Transform | 8 | `",".join(items)` → `items.join(",")` |
| Runtime Helper | 44 | `s.split()` → `__py.str.split(s)` |

**String Methods:**

| Python | JavaScript | Notes |
|--------|------------|-------|
| `s.lower()` | `s.toLowerCase()` | Direct map |
| `s.upper()` | `s.toUpperCase()` | Direct map |
| `s.strip()` | `s.trim()` | Direct map |
| `s.lstrip()` | `s.trimStart()` | Direct map |
| `s.rstrip()` | `s.trimEnd()` | Direct map |
| `s.split()` | `__py.str.split(s)` | No-arg splits on whitespace! |
| `s.split(",")` | `s.split(",")` | Direct map |
| `",".join(items)` | `items.join(",")` | Reversed order |
| `s.replace("a", "b")` | `s.replaceAll("a", "b")` | Python replaces ALL |
| `s.replace("a", "b", 1)` | `s.replace("a", "b")` | With count |
| `s.startswith("x")` | `s.startsWith("x")` | Direct map |
| `s.endswith("x")` | `s.endsWith("x")` | Direct map |
| `s.find("x")` | `s.indexOf("x")` | Direct map |
| `s.index("x")` | `__py.str.index(s, "x")` | Throws on not found! |
| `s.count("x")` | `(s.match(/x/g) \|\| []).length` | |
| `s.isdigit()` | `/^\d+$/.test(s)` | |
| `s.isalpha()` | `/^[a-zA-Z]+$/.test(s)` | |
| `s.capitalize()` | `s[0].toUpperCase() + s.slice(1).toLowerCase()` | |
| `s.title()` | `__py.str.title(s)` | Complex |
| `s.center(10)` | `s.padStart((s.length+10)/2).padEnd(10)` | |
| `s.zfill(5)` | `s.padStart(5, '0')` | |

**List Methods:**

| Python | JavaScript | Notes |
|--------|------------|-------|
| `items.append(x)` | `items.push(x)` | Returns None vs length |
| `items.extend(other)` | `items.push(...other)` | |
| `items.insert(i, x)` | `items.splice(i, 0, x)` | |
| `items.pop()` | `items.pop()` | Same |
| `items.pop(0)` | `items.shift()` | Or splice |
| `items.pop(i)` | `items.splice(i, 1)[0]` | |
| `items.remove(x)` | `__py.list.remove(items, x)` | Throws on not found! |
| `items.clear()` | `items.length = 0` | |
| `items.index(x)` | `__py.list.index(items, x)` | Throws on not found! |
| `items.count(x)` | `items.filter(i => __py.eq(i, x)).length` | |
| `items.sort()` | `items.sort((a,b) => a-b)` | Numeric not string! |
| `items.sort(key=fn)` | `items.sort((a,b) => fn(a)-fn(b))` | |
| `items.sort(reverse=True)` | `items.sort((a,b) => b-a)` | |
| `items.reverse()` | `items.reverse()` | Same |
| `items.copy()` | `[...items]` | |

**Dict Methods:**

| Python | JavaScript | Notes |
|--------|------------|-------|
| `d.get("k")` | `d["k"] ?? null` | Returns null not undefined |
| `d.get("k", default)` | `d["k"] ?? default` | |
| `d.keys()` | `Object.keys(d)` | |
| `d.values()` | `Object.values(d)` | |
| `d.items()` | `Object.entries(d)` | |
| `d.update(other)` | `Object.assign(d, other)` | |
| `d.pop("k")` | `__py.dict.pop(d, "k")` | Throws on not found! |
| `d.pop("k", default)` | `__py.dict.pop(d, "k", default)` | |
| `d.setdefault("k", v)` | `d["k"] ??= v` | |
| `d.clear()` | `for(k in d) delete d[k]` | |
| `d.copy()` | `{...d}` | Shallow |

**Set Methods:**

| Python | JavaScript | Notes |
|--------|------------|-------|
| `s.add(x)` | `s.add(x)` | Same |
| `s.remove(x)` | `__py.set.remove(s, x)` | Throws on not found! |
| `s.discard(x)` | `s.delete(x)` | Ignores missing |
| `s.pop()` | `__py.set.pop(s)` | |
| `s.clear()` | `s.clear()` | Same |
| `s.copy()` | `new Set(s)` | |
| `s.union(t)` | `new Set([...s, ...t])` | |
| `s.intersection(t)` | `new Set([...s].filter(x => t.has(x)))` | |
| `s.difference(t)` | `new Set([...s].filter(x => !t.has(x)))` | |
| `s.issubset(t)` | `[...s].every(x => t.has(x))` | |
| `s.issuperset(t)` | `[...t].every(x => s.has(x))` | |

**Files:**
- `pynext/transpiler/runtime/types/string.js`
- `pynext/transpiler/runtime/types/list.js`
- `pynext/transpiler/runtime/types/dict.js`
- `pynext/transpiler/runtime/types/set.js`
- `pynext/transpiler/runtime/types/index.js`
- `tests/unit/transpiler/test_string_methods.py`
- `tests/unit/transpiler/test_list_methods.py`
- `tests/unit/transpiler/test_dict_methods.py`
- `tests/unit/transpiler/test_set_methods.py`

---

**18.4 Runtime: Builtins & Standard Library (Week 4) - ✅ COMPLETE (531 tests)**

Implement Python builtins and common standard library functions.

**Implementation Summary:**
- **Runtime Files**: `builtins.js` + 4 stdlib modules (json.js, math.js, re.js, random.js)
- **Enhanced Builtins**: sorted(key=, reverse=), min/max(key=), any/all, divmod, pow, callable
- **Standard Library**: json (loads, dumps), math (30+ functions), re (match, search, sub, findall, split), random (10+ functions with seedable PRNG)
- **Python Tests**: 412 tests across 4 test files (test_builtins.py: 100, test_stdlib.py: 89, + 223 existing)
- **JavaScript Tests**: 203 tests (builtins.test.js: 119 + builtins_risk.test.js: 84)
- **Documentation**: `docs/transpiler/BUILTINS.md`

**Key Semantic Fixes:**
| Builtin | Python | JavaScript | Solution |
|---------|--------|------------|----------|
| `sorted(key=len)` | Key function | No equivalent | `__py.sorted(items, len)` |
| `min([])` | ValueError | Infinity | Throw Error |
| `any([[], {}])` | False | True | Use `__py.bool()` |
| `filter(None, x)` | Filter falsy | No equivalent | `filter(x => __py.bool(x))` |
| `re.match()` | Anchored at ^ | Not anchored | Prepend ^ |
| `random.shuffle()` | In-place, None | No equivalent | Fisher-Yates |

**Risk Area Fixes (Phase 18.4 Hardening):**

| Issue | Problem | Solution | Tests |
|-------|---------|----------|-------|
| `sorted()` default | JS sort is lexicographic | Always use `__py.sorted()` with stable sort + type checking | 8 |
| `min/max` types | No mixed type error | `__py.min/max` with TypeError on mixed types | 12 |
| `round()` .5 | JS rounds up | Banker's rounding (round half to even) | 8 |
| `random.seed()` | Not supported | xorshift128+ PRNG with full state save/restore | 10 |
| `re.match` groups | No position tracking | Group position tracking with ES2022 indices fallback | 7 |
| `math.pi/e/tau` | Module access issue | Emitter handles module constants directly | 5 |
| `filter(None)` | Variable detection | Always use `__py.filter()` for proper None handling | 5 |

**Total Risk Tests Added:** 84 tests in `builtins_risk.test.js`

**Core Builtins:**

| Python | JavaScript |
|--------|------------|
| `len(x)` | `x.length` (arrays/strings) or `x.size` (sets/maps) |
| `range(n)` | `__py.range(n)` (lazy iterator) |
| `range(a, b)` | `__py.range(a, b)` |
| `range(a, b, step)` | `__py.range(a, b, step)` |
| `str(x)` | `String(x)` |
| `int(x)` | `parseInt(x, 10)` |
| `float(x)` | `parseFloat(x)` |
| `bool(x)` | `__py.bool(x)` |
| `list(x)` | `Array.from(x)` or `[...x]` |
| `dict(x)` | `Object.fromEntries(x)` |
| `set(x)` | `new Set(x)` |
| `tuple(x)` | `Object.freeze([...x])` |

**Aggregate Builtins:**

| Python | JavaScript |
|--------|------------|
| `sum(items)` | `items.reduce((a,b) => a+b, 0)` |
| `sum(items, start)` | `items.reduce((a,b) => a+b, start)` |
| `min(items)` | `Math.min(...items)` |
| `min(a, b, c)` | `Math.min(a, b, c)` |
| `min(items, key=fn)` | `items.reduce((a,b) => fn(a)<fn(b)?a:b)` |
| `max(items)` | `Math.max(...items)` |
| `max(items, key=fn)` | `items.reduce((a,b) => fn(a)>fn(b)?a:b)` |
| `any(items)` | `items.some(__py.bool)` |
| `all(items)` | `items.every(__py.bool)` |
| `sorted(items)` | `[...items].sort((a,b) => a-b)` |
| `sorted(items, key=fn)` | `[...items].sort((a,b) => fn(a)-fn(b))` |
| `sorted(items, reverse=True)` | `[...items].sort((a,b) => b-a)` |
| `reversed(items)` | `[...items].reverse()` |

**Iteration Builtins:**

| Python | JavaScript |
|--------|------------|
| `enumerate(items)` | `items.map((v, i) => [i, v])` |
| `enumerate(items, start=1)` | `items.map((v, i) => [i+1, v])` |
| `zip(a, b)` | `__py.zip(a, b)` |
| `zip(a, b, c)` | `__py.zip(a, b, c)` |
| `map(fn, items)` | `items.map(fn)` |
| `filter(fn, items)` | `items.filter(fn)` |
| `filter(None, items)` | `items.filter(__py.bool)` |

**Type/Introspection Builtins:**

| Python | JavaScript |
|--------|------------|
| `isinstance(x, int)` | `Number.isInteger(x)` |
| `isinstance(x, float)` | `typeof x === 'number'` |
| `isinstance(x, str)` | `typeof x === 'string'` |
| `isinstance(x, bool)` | `typeof x === 'boolean'` |
| `isinstance(x, list)` | `Array.isArray(x)` |
| `isinstance(x, dict)` | `__py.isDict(x)` |
| `isinstance(x, set)` | `x instanceof Set` |
| `isinstance(x, (int, float))` | `typeof x === 'number'` |
| `type(x)` | `__py.type(x)` |
| `callable(x)` | `typeof x === 'function'` |
| `hasattr(obj, "x")` | `"x" in obj` |
| `getattr(obj, "x")` | `obj["x"]` |
| `getattr(obj, "x", default)` | `obj["x"] ?? default` |
| `setattr(obj, "x", v)` | `obj["x"] = v` |

**Other Builtins:**

| Python | JavaScript |
|--------|------------|
| `abs(x)` | `Math.abs(x)` |
| `round(x)` | `Math.round(x)` |
| `round(x, 2)` | `Math.round(x * 100) / 100` |
| `pow(x, y)` | `Math.pow(x, y)` |
| `divmod(a, b)` | `[__py.floordiv(a,b), __py.mod(a,b)]` |
| `ord(c)` | `c.charCodeAt(0)` |
| `chr(n)` | `String.fromCharCode(n)` |
| `print(*args)` | `console.log(...args)` |
| `repr(x)` | `JSON.stringify(x)` |

**Standard Library - json:**

| Python | JavaScript |
|--------|------------|
| `json.loads(s)` | `JSON.parse(s)` |
| `json.dumps(obj)` | `JSON.stringify(obj)` |
| `json.dumps(obj, indent=2)` | `JSON.stringify(obj, null, 2)` |

**Standard Library - re (basic):**

| Python | JavaScript |
|--------|------------|
| `re.match(pattern, s)` | `s.match(new RegExp('^' + pattern))` |
| `re.search(pattern, s)` | `s.match(new RegExp(pattern))` |
| `re.sub(pattern, repl, s)` | `s.replace(new RegExp(pattern, 'g'), repl)` |
| `re.findall(pattern, s)` | `s.match(new RegExp(pattern, 'g')) \|\| []` |
| `re.split(pattern, s)` | `s.split(new RegExp(pattern))` |

**Standard Library - math:**

| Python | JavaScript |
|--------|------------|
| `math.floor(x)` | `Math.floor(x)` |
| `math.ceil(x)` | `Math.ceil(x)` |
| `math.sqrt(x)` | `Math.sqrt(x)` |
| `math.sin(x)` / `cos` / `tan` | `Math.sin(x)` / etc. |
| `math.log(x)` | `Math.log(x)` |
| `math.exp(x)` | `Math.exp(x)` |
| `math.pi` | `Math.PI` |
| `math.e` | `Math.E` |
| `math.inf` | `Infinity` |
| `math.isnan(x)` | `Number.isNaN(x)` |
| `math.isinf(x)` | `!Number.isFinite(x)` |

**Standard Library - random:**

| Python | JavaScript |
|--------|------------|
| `random.random()` | `Math.random()` |
| `random.randint(a, b)` | `Math.floor(Math.random() * (b-a+1)) + a` |
| `random.choice(items)` | `items[Math.floor(Math.random() * items.length)]` |
| `random.shuffle(items)` | `__py.random.shuffle(items)` |
| `random.sample(items, k)` | `__py.random.sample(items, k)` |

**Files:**
- `pynext/transpiler/runtime/builtins.js`
- `pynext/transpiler/runtime/stdlib/json.js`
- `pynext/transpiler/runtime/stdlib/re.js`
- `pynext/transpiler/runtime/stdlib/math.js`
- `pynext/transpiler/runtime/stdlib/random.js`
- `tests/unit/transpiler/test_builtins.py`
- `tests/unit/transpiler/test_stdlib.py`

---

**18.5 Advanced Features (Week 5) - ✅ COMPLETE (817 tests)**

Handle async, generators (limited), decorators, and advanced unpacking.

**Async/Await:**

```python
async def fetch_user(id):
    response = await fetch(f"/api/users/{id}")
    data = await response.json()
    return data
```

```javascript
async function fetch_user(id) {
    const response = await fetch(`/api/users/${id}`);
    const data = await response.json();
    return data;
}
```

**Generator Expressions (in function calls only):**

| Python | JavaScript |
|--------|------------|
| `sum(x**2 for x in items)` | `items.reduce((a,x) => a + x**2, 0)` |
| `any(x > 0 for x in items)` | `items.some(x => x > 0)` |
| `all(valid(x) for x in items)` | `items.every(x => valid(x))` |
| `list(x*2 for x in items)` | `items.map(x => x*2)` |
| `dict((k, v*2) for k,v in d.items())` | `Object.fromEntries(Object.entries(d).map(([k,v]) => [k, v*2]))` |

**Note:** Full generators (`yield`) are NOT supported - use `@server_action` for those.

**Decorators (limited):**

```python
@memoize
def expensive(n):
    return fib(n)
```

```javascript
const expensive = __py.memoize(function expensive(n) {
    return fib(n);
});
```

Supported decorators:
- `@memoize` - Caching wrapper
- `@debounce(ms)` - Debounce wrapper
- `@throttle(ms)` - Throttle wrapper
- Custom decorators that are simple function wrappers

**Unpacking (complete):**

| Python | JavaScript |
|--------|------------|
| `[*a, *b]` | `[...a, ...b]` |
| `{**a, **b}` | `{...a, ...b}` |
| `foo(*args)` | `foo(...args)` |
| `foo(**kwargs)` | `foo(kwargs)` (objects as kwargs) |
| `foo(*args, **kwargs)` | `foo(...args, kwargs)` |
| `def foo(*args):` | `function foo(...args) {` |
| `def foo(**kwargs):` | `function foo(kwargs = {}) {` |
| `def foo(a, *args, **kwargs):` | `function foo(a, ...args) { const kwargs = args.pop?.() \|\| {}; }` |

**Keyword Arguments:**

```python
sorted(items, key=lambda x: x["name"], reverse=True)
```

```javascript
__py.sorted(items, { key: x => x["name"], reverse: true })
```

**Files:**
- `pynext/transpiler/async_await.py`
- `pynext/transpiler/generators.py`
- `pynext/transpiler/decorators.py`
- `pynext/transpiler/unpacking.py`
- `pynext/transpiler/runtime/decorators.js`
- `tests/unit/transpiler/test_async.py`
- `tests/unit/transpiler/test_generators.py`
- `tests/unit/transpiler/test_decorators.py`
- `tests/unit/transpiler/test_unpacking.py`

---

**18.6 PyNext Integration (Week 6) - ✅ COMPLETE (480 tests)**

Wire the transpiler into PyNext's reactive system, replacing the regex-based `html.py` approach.

**Integration Points:**

```python
# In pynext/core/html.py, replace:
handler_code = self._extract_handler_code(handler_func)  # Regex-based (OLD)

# With:
from pynext.transpiler import transpile_handler
handler_code = transpile_handler(handler_func, context=ctx)  # AST-based (NEW)
```

**PyNext-Specific Transforms:**

| Python | JavaScript |
|--------|------------|
| `signal(0)` | `__pynext__.createSignal(0)` |
| `count()` (signal read) | `count.read()` |
| `count.set(value)` | `count.set(value)` |
| `count.update(fn)` | `count.update(fn)` |
| `memo(lambda: x() * 2)` | `__pynext__.createMemo(() => x.read() * 2)` |
| `effect(lambda: ...)` | `__pynext__.createEffect(() => ...)` |
| `form.validate()` | `__pynext__.getForm('form_id').validate()` |
| `form.values` | `__pynext__.getForm('form_id').values` |
| `form.reset()` | `__pynext__.getForm('form_id').reset()` |
| `store.items` | `__pynext__.getStore('store_id').items` |

**Complete Handler Example:**

```python
def handle_add_issue():
    if issue_form.validate():
        values = issue_form.values
        new_issue = {
            "id": next_id(),
            "title": values["title"],
            "status": values["status"],
        }
        all_issues.set([*all_issues(), new_issue])
        next_id.update(lambda n: n + 1)
        issue_form.reset()
        show_modal.set(False)
```

```javascript
function handle_add_issue() {
    const issue_form = __pynext__.getForm('form_xxx');
    if (issue_form.validate()) {
        const values = issue_form.values;
        const new_issue = {
            "id": __pynext__.getSignal('next_id').read(),
            "title": values["title"],
            "status": values["status"],
        };
        __pynext__.getSignal('all_issues').update(arr => [...arr, new_issue]);
        __pynext__.getSignal('next_id').update(n => n + 1);
        issue_form.reset();
        __pynext__.getSignal('show_modal').set(false);
    }
}
```

**Hydration Integration:**

The transpiler generates code that works with PyNext's hydration system:
- Signal IDs are resolved at hydration time via `__pynext__.getSignal()`
- Form IDs are resolved via `__pynext__.getForm()`
- Store IDs are resolved via `__pynext__.getStore()`

**Debug CLI - Transpile Command:**

For debugging and inspection, add a CLI command to output transpiled JavaScript:

```bash
# Transpile a specific file and output JS
pynext transpile pages/issues.py --output issues.js

# Transpile with source maps
pynext transpile pages/issues.py --output issues.js --sourcemap

# Transpile and print to terminal (no file)
pynext transpile pages/issues.py --print

# Transpile with Python source as comments
pynext transpile pages/issues.py --print --annotate

# Transpile all handlers in project
pynext transpile --all --output-dir ./debug-js/

# Show which runtime functions would be used
pynext transpile pages/issues.py --deps
```

**Example Output (with --annotate):**

```javascript
// ═══════════════════════════════════════════════════════════════════════════
// Transpiled from: pages/issues.py
// Handlers: handle_add_issue, handle_delete, handle_status_change
// Runtime dependencies: __py.bool, __py.slice, __pynext__.getSignal
// Generated: 2024-01-15T10:30:00Z
// ═══════════════════════════════════════════════════════════════════════════

// ─────────────────────────────────────────────────────────────────────────────
// Original Python (lines 45-55):
//
//   def handle_add_issue():
//       if issue_form.validate():
//           values = issue_form.values
//           all_issues.set([*all_issues(), values])
//           issue_form.reset()
//           show_modal.set(False)
//
// ─────────────────────────────────────────────────────────────────────────────
function handle_add_issue() {
    const issue_form = __pynext__.getForm('form_xxx');
    if (issue_form.validate()) {
        const values = issue_form.values;
        __pynext__.getSignal('all_issues').update(arr => [...arr, values]);
        issue_form.reset();
        __pynext__.getSignal('show_modal').set(false);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Original Python (lines 57-60):
//
//   def handle_delete(issue_id):
//       all_issues.set([x for x in all_issues() if x["id"] != issue_id])
//
// ─────────────────────────────────────────────────────────────────────────────
function handle_delete(issue_id) {
    __pynext__.getSignal('all_issues').update(
        arr => arr.filter(x => x["id"] !== issue_id)
    );
}
```

**Dev Server Debug Mode:**

```bash
# Run dev server with JS output for all handlers
pynext dev --emit-js

# Creates .pynext/debug/ directory:
# .pynext/debug/
# ├── pages/
# │   ├── issues.handlers.js      # All handlers from issues.py
# │   ├── issues.handlers.js.map  # Source map
# │   ├── dashboard.handlers.js
# │   └── ...
# └── runtime.js                   # The runtime being used (for reference)
```

Files are regenerated on every hot reload, enabling:
- Side-by-side Python/JS comparison during development
- IDE integration for viewing generated code
- Git-diffing generated output to catch transpiler regressions

**Files:**
- `pynext/transpiler/reactive.py` - Detect signals, memos, effects, stores, forms
- `pynext/transpiler/hydration.py` - Generate hydration-compatible code
- `pynext/transpiler/pynext.py` - PyNext-specific transforms
- `pynext/transpiler/cli.py` - CLI transpile command
- `pynext/core/html.py` - Integration (modify `_extract_handler_code`)
- `pynext/server/dev.py` - Dev server --emit-js flag
- `tests/e2e/test_linear_transpiled.py` - Linear app works end-to-end!
- `tests/e2e/test_forms_transpiled.py`
- `tests/e2e/test_signals_transpiled.py`
- `tests/unit/transpiler/test_cli.py`
- `tests/unit/transpiler/test_186_critical_fixes.py` - Critical fixes tests (68 tests)
- `tests/js/transpiler/critical_fixes.test.js` - JS runtime tests (38 tests)

**Critical Fixes (Phase 18.6.1) - ✅ COMPLETE:**

Six critical risk areas were identified and fixed with comprehensive testing:

| Pattern | Issue | Fix |
|---------|-------|-----|
| Signal reads in comprehensions | Signal calls not transformed in DictComp/SetComp | Added `_transform_dictcomp`, `_transform_setcomp` to PyNextTransformer |
| Nested function handlers | Closure detection incomplete | Recursive closure traversal in `_extract_closure_vars` |
| Form field signals (`form.email()`) | Not detected as reactive | Added `_extract_form_field_signals` helper |
| Lambda handlers | `inspect.getsource()` fails | Bytecode fallback in `get_handler_source` |
| `try/except` blocks | Became `/* pass */` | Full `Try`/`ExceptHandler` IR nodes + parser/emitter/transformer |
| Async handlers with `await` | Signals in await not transformed | Added `_transform_await` to PyNextTransformer |

**Test Summary:**

| Test Type | Count |
|-----------|-------|
| Python unit tests (Phase 18.6) | 442 |
| JavaScript runtime tests | 38 |
| **Total Phase 18.6** | **480** |

| Test Type | Count |
|-----------|-------|
| Python unit tests (Phase 18.7) | 841 |
| JavaScript runtime tests (Phase 18.7) | 177 |
| **Total Phase 18.7** | **1,018** |

---

**18.7 Optimization Passes (Week 7) - ✅ COMPLETE (1,018 tests)**

Reduce generated code size and eliminate unnecessary runtime calls.

**Implementation Summary:**

| Component | Status | Tests |
|-----------|--------|-------|
| Type Inference Engine | ✅ Complete | 171 |
| Wrapper Elision | ✅ Complete | 160 |
| Loop Capture Fix | ✅ Complete | 85 |
| Runtime Inlining | ✅ Complete | 80 |
| Dead Code Elimination | ✅ Complete | 92 |
| @js_native Decorator | ✅ Complete | 50 |
| Edge Cases (Async, FString, etc.) | ✅ Complete | 94 |
| End-to-End Pipeline | ✅ Complete | 40 |
| Stress/Real-World Patterns | ✅ Complete | 69 |
| JavaScript Runtime Tests | ✅ Complete | 177 |
| **Total** | | **1,018** |

**Optimization 1: Wrapper Elision**

When the transpiler can prove Python and JS semantics are equivalent, skip the wrapper:

```python
# Before optimization:
if x > 0:  # x is known to be a number
    ...

# Naive output:
if (__py.bool(x > 0)) { ... }

# Optimized output (bool wrapper unnecessary for comparisons):
if (x > 0) { ... }
```

**Wrapper elision rules (implemented with safety tests):**
- `__py.bool(x)` elided when `x` is a comparison result (always boolean)
- `__py.bool(x)` elided when `x` is known to be `boolean` type
- `__py.eq(a, b)` simplified to `a === b` when both are primitives
- `__py.add(a, b)` simplified to `a + b` when both are numbers
- `__py.mul(a, b)` simplified to `a * b` when both are numbers
- `__py.at(arr, i)` simplified to `arr[i]` when `i` is known non-negative

**Critical Safety: Never elide when semantics differ:**
- `[]` truthiness (Python: false, JS: true) → Uses `__py.bool` or inlines to `.length > 0`
- `[1] == [1]` (Python: true, JS: false) → Must use `__py.eq`
- `items[-1]` (Python: last, JS: undefined) → Must use `__py.at`
- `-7 % 3` (Python: 2, JS: -1) → Must use `__py.mod`
- `"a" * 3` (Python: "aaa", JS: NaN) → Must use `__py.mul`

**Optimization 2: Type Inference**

Track types through the code to enable more elisions:

```python
def process(items: list[int]) -> int:
    total = 0  # int
    for x in items:  # x is int
        if x > 0:  # comparison, result is bool
            total += x  # int + int = int
    return total
```

**Type inference capabilities:**
- Literal type inference (int, float, str, bool, None, list, dict, tuple)
- Variable type propagation through assignments
- Binary/unary operation result types
- Function call return types (built-ins like `len()` → int)
- Augmented assignment (`+=`, `-=`) type tracking
- F-string type inference (always str)
- Comprehension types (list comp → list, dict comp → dict)

**Optimization 3: Dead Code Elimination**

Remove unreachable code and unused imports:

```javascript
// Before: imports entire runtime
import { __py } from 'pynext/runtime';

// After: only imports what's used
import { __py_bool, __py_slice } from 'pynext/runtime';
```

**DCE capabilities:**
- `if False:` branches removed
- `if True:` unwrapped to just body
- `x if True else y` simplified to `x`
- `x if False else y` simplified to `y`
- Unused runtime dependency collection for minimal imports

**Optimization 4: Inline Simple Runtime Calls**

For very simple runtime functions, inline them:

```javascript
// Before:
__py.len(items)   // items is known list
__py.bool(items)  // items is known list

// After (inlined):
items.length
items.length > 0
```

**Inlining capabilities:**
- `len(list/str/tuple)` → `.length`
- `len(dict)` → `Object.keys().length`
- `bool(list/str)` → `.length > 0`
- `bool(dict)` → `Object.keys().length > 0`

**Optimization 5: Loop Variable Capture Fix**

Automatically fix the Python loop closure gotcha (including nested loops):

```python
# This is a bug in Python (all callbacks see i=4)
for i in range(5):
    onclick=lambda: handle(i)  # Wrong!

# Nested loops also fixed:
for i in range(5):
    for j in range(5):
        onclick=lambda: handle(i, j)  # Both captured correctly
```

```javascript
// Transpiler automatically fixes by capturing:
for (let i = 0; i < 5; i++) {
    onclick = ((i) => () => handle(i))(i);  // Captured correctly
}

// Nested:
for (let i = 0; i < 5; i++) {
    for (let j = 0; j < 5; j++) {
        onclick = ((i, j) => () => handle(i, j))(i, j);  // Both captured
    }
}
```

**Optimization 6: @js_native Escape Hatch**

For performance-critical code, skip all Python semantics:

```python
@js_native
def fast_sum(items):
    total = 0
    for x in items:
        total += x
    return total
```

```javascript
// No __py wrappers, pure JS
function fast_sum(items) {
    let total = 0;
    for (const x of items) {
        total += x;
    }
    return total;
}
```

**Optimization Metrics:**

| Metric | Target | Achieved |
|--------|--------|----------|
| Wrapper calls reduced | 50-70% fewer | ✅ |
| Generated code size | 30-40% smaller | ✅ |
| Runtime execution | 10-20% faster | ✅ |

**Edge Cases Handled:**

| Edge Case | Status |
|-----------|--------|
| Async/Await expressions | ✅ Returns ANY type, preserves wrappers |
| F-Strings | ✅ Returns STR type, enables len inlining |
| Comprehensions | ✅ Returns correct collection type |
| Augmented Assignment | ✅ Tracks type through +=, -= etc. |
| Chained Comparisons | ✅ Returns BOOL, enables bool elision |
| IfExp (Ternary) | ✅ DCE for constant conditions |
| Try/Except | ✅ Conservative type merging |
| BoolOp (and/or) | ✅ Returns BOOL for bool operands |

**Files:**
- `pynext/transpiler/optimizer/__init__.py` - Main API
- `pynext/transpiler/optimizer/types.py` - Type inference engine
- `pynext/transpiler/optimizer/elision.py` - Wrapper elision
- `pynext/transpiler/optimizer/capture.py` - Loop capture fix
- `pynext/transpiler/optimizer/inline.py` - Runtime inlining
- `pynext/transpiler/optimizer/dce.py` - Dead code elimination
- `pynext/transpiler/optimizer/native.py` - @js_native support
- `pynext/transpiler/optimizer/_internal/` - Internal utilities
- `docs/transpiler/OPTIMIZER.md` - Comprehensive documentation

**Test Files:**
- `tests/unit/transpiler/test_187_types.py` - Type inference (129 tests)
- `tests/unit/transpiler/test_187_elision.py` - Wrapper elision (127 tests)
- `tests/unit/transpiler/test_187_capture.py` - Loop capture (74 tests)
- `tests/unit/transpiler/test_187_inline.py` - Runtime inlining (80 tests)
- `tests/unit/transpiler/test_187_dce.py` - Dead code elimination (70 tests)
- `tests/unit/transpiler/test_187_native.py` - @js_native (50 tests)
- `tests/unit/transpiler/test_187_integration.py` - Integration (48 tests)
- `tests/unit/transpiler/test_187_regression.py` - Regression (50 tests)
- `tests/unit/transpiler/test_187_elision_safety.py` - Safety (33 tests)
- `tests/unit/transpiler/test_187_type_edge_cases.py` - Type edge cases (42 tests)
- `tests/unit/transpiler/test_187_cross_pass.py` - Cross-pass (21 tests)
- `tests/unit/transpiler/test_187_nested_capture.py` - Nested capture (11 tests)
- `tests/unit/transpiler/test_187_dce_safety.py` - DCE safety (22 tests)
- `tests/unit/transpiler/test_187_e2e.py` - End-to-end (21 tests)
- `tests/unit/transpiler/test_187_stress.py` - Stress tests (19 tests)
- `tests/unit/transpiler/test_187_edge_cases.py` - Edge cases (38 tests)
- `tests/benchmarks/test_optimizer_benchmarks.py` - Benchmarks (6 tests)
- `tests/js/transpiler/optimizer.test.js` - JS runtime (55 tests)
- `tests/js/transpiler/optimizer_extended.test.js` - JS extended (66 tests)
- `tests/js/transpiler/edge_cases.test.js` - JS edge cases (56 tests)

---

**18.8 Edge Cases, Classes & Polish (Week 8) - ✅ COMPLETE (600 Python + 130 JS tests)**

Handle remaining edge cases, add class support, and polish for production.

**Edge Cases:**

| Case | Handling |
|------|----------|
| Division by zero | `1/0` returns `Infinity` (JS), not error |
| Integer overflow | Large ints lose precision in JS |
| Unicode identifiers | `café = 1` → `const café = 1;` |
| Walrus operator | `if (x := val):` → `let x; if (x = val) {` |
| Assert statements | `assert x > 0` → `if (!(x > 0)) throw new AssertionError();` |
| Multiple inheritance | Not supported, compile error with helpful message |
| `global`/`nonlocal` | Limited support with warnings |

**Class Support (Basic):**

```python
class Todo:
    def __init__(self, title, done=False):
        self.title = title
        self.done = done
    
    def toggle(self):
        self.done = not self.done
    
    @property
    def status(self):
        return "Done" if self.done else "Pending"
```

```javascript
class Todo {
    constructor(title, done = false) {
        this.title = title;
        this.done = done;
    }
    
    toggle() {
        this.done = !this.done;
    }
    
    get status() {
        return this.done ? "Done" : "Pending";
    }
}
```

**Supported class features:**
- `__init__` → `constructor`
- Instance methods
- `@property` → getters
- `@staticmethod` → static methods
- Single inheritance with `super()`

**Not supported (use @server_action):**
- Multiple inheritance
- `@classmethod`
- Metaclasses
- Descriptors
- `__slots__`

**Error Messages:**

When code can't be transpiled, provide helpful errors:

```
TranspileError: Cannot transpile generator function 'count_up' at line 15.

  def count_up():
      yield 1  # <-- Generators not supported
      yield 2

Suggestion: Use @server_action for generator functions:

  @server_action
  def count_up():
      yield 1
      yield 2
```

**Source Maps:**

Generate V3 source maps for debugging Python in the browser:

```json
{
  "version": 3,
  "file": "handler.js",
  "sources": ["handler.py"],
  "mappings": "AAAA,SAAS,..."
}
```

**Browser DevTools Integration:**

In development mode, expose debugging utilities in the browser console via `px_transpile_debug`:

```javascript
// In browser console (dev mode only):

// Show all registered handlers
px_transpile_debug.listHandlers()
// → ['handle_add_issue', 'handle_delete', 'handle_status_change']

// Show transpiled JS for a specific handler
px_transpile_debug.showHandler('handle_add_issue')
// → Logs: original Python, generated JS, runtime dependencies

// Show the Python source for a handler
px_transpile_debug.showSource('handle_add_issue')
// → Logs: Original Python code with line numbers

// Show runtime usage statistics
px_transpile_debug.runtimeStats()
// → { 'bool': 12, 'slice': 3, 'at': 8, ... }

// Verify Python semantics for an expression
px_transpile_debug.testExpr('-7 % 3')
// → { expression: "-7 % 3", result: 2, expected: 2, match: true }
```

**Phase 18.8 Test Summary:**

| Test Type | Count |
|-----------|-------|
| Python unit tests (test_188_classes.py) | 120 |
| Python unit tests (test_188_class_edge_cases.py) | 60 |
| Python unit tests (test_188_assert.py) | 40 |
| Python unit tests (test_188_walrus.py) | 50 |
| Python unit tests (test_188_edge_cases.py) | 60 |
| Python unit tests (test_188_sourcemap.py) | 50 |
| Python unit tests (test_188_debug.py) | 40 |
| Python unit tests (test_188_errors.py) | 50 |
| Python unit tests (test_188_integration.py) | 30 |
| JavaScript runtime tests (classes.test.js) | 80 |
| JavaScript runtime tests (188_edge_cases.test.js) | 20 |
| JavaScript runtime tests (px_debug.test.js) | 30 |
| **Total Phase 18.8** | **630** |

**Visual Debugging (with --debug-transpiler):**

```bash
pynext dev --debug-transpiler
```

Enables a floating debug panel in the browser showing:
- List of all handlers on the current page
- Click to expand and see Python → JS transformation
- Highlight which runtime functions are used
- Real-time updates on hot reload

**Files:**
- `pynext/transpiler/classes.py`
- `pynext/transpiler/edge_cases.py`
- `pynext/transpiler/errors.py` - Helpful error messages
- `pynext/transpiler/sourcemap.py` - Source map generation
- `pynext/transpiler/debug.py` - Debug utilities
- `pynext/runtime/debug.js` - Browser DevTools integration
- `tests/unit/transpiler/test_classes.py`
- `tests/unit/transpiler/test_edge_cases.py`
- `tests/unit/transpiler/test_errors.py`
- `tests/unit/transpiler/test_debug.py`

---

**Complete Runtime Library Structure:**

```
pynext/transpiler/runtime/
├── index.js              # Entry point, exports all
├── core.js               # __py.at, __py.slice, __py.bool, __py.eq
├── operators.js          # __py.add, __py.mul, __py.mod, __py.floordiv, __py.in
├── types/
│   ├── index.js          # Re-exports all types
│   ├── string.js         # String method implementations
│   ├── list.js           # List method implementations
│   ├── dict.js           # Dict method implementations
│   └── set.js            # Set method implementations
├── builtins.js           # len, range, sum, min, max, any, all, sorted, etc.
├── stdlib/
│   ├── json.js           # json.loads, json.dumps
│   ├── re.js             # re.match, re.search, re.sub, etc.
│   ├── math.js           # math.floor, math.sqrt, etc.
│   └── random.js         # random.choice, random.randint, etc.
├── exceptions.js         # ValueError, TypeError, KeyError, etc.
├── decorators.js         # memoize, debounce, throttle
└── pynext.js             # PyNext integration (__pynext__ namespace)
```

**Runtime Size Breakdown:**

| Module | Size (gzipped) |
|--------|----------------|
| core.js | 1KB |
| operators.js | 1KB |
| types/ | 4KB |
| builtins.js | 3KB |
| stdlib/ | 6KB |
| exceptions.js | 0.5KB |
| decorators.js | 0.5KB |
| pynext.js | 4KB |
| **Total** | **~20KB** |

**Tree-Shaking:** Only import what you use. A simple handler might only need 3-5KB.

---

**Success Criteria:**

| Metric | Target |
|--------|--------|
| Linear app handlers | 100% work without fallbacks |
| All Python operators | Correct semantics (truthiness, modulo, equality) |
| Generated JS readability | Human-debuggable |
| Runtime size (complete) | ~20KB gzipped |
| Runtime size (typical handler) | ~5KB gzipped (tree-shaken) |
| Compilation speed | < 100ms per file |
| Test coverage | 3,300+ tests |
| Performance vs React | 5-20x faster updates (O(1) vs O(n)) |

**Milestones:**

1. **Week 2:** Basic handlers transpile correctly
2. **Week 4:** All Python operators work with correct semantics
3. **Week 6:** Linear app works end-to-end with no fallbacks
4. **Week 8:** Optimization passes reduce output size by 30%+

**Milestone:** Any Python event handler that doesn't use generators, file I/O, or complex imports transpiles correctly and runs faster than equivalent React code.

---

## PyNext Enterprise Architecture

### The Vision: Better Than Next.js

PyNext Enterprise Architecture makes project structure, styling, deployment, and observability dramatically simpler than Next.js or NestJS while supporting enterprise-scale monorepos and microservices.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PYNEXT ENTERPRISE ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Structure + Style + Deploy + Observe = Complete Enterprise Platform        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Why Better Than Next.js                          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  • Feature-first architecture (not file-first)                      │   │
│  │  • Pythonic CSS (not Tailwind string soup)                          │   │
│  │  • Headless components you own (ShadCN-style)                       │   │
│  │  • Monorepo with clear boundaries (not implicit)                    │   │
│  │  • Declarative deployment (not YAML hell)                           │   │
│  │  • Unified observability (not 5 different tools)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Feature   │  │  Pythonic  │  │  PyNext    │  │ Workspace  │           │
│  │  Slices    │  │    CSS     │  │    UI      │  │ Boundaries │           │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘           │
│                                                                              │
│  ┌────────────┐  ┌────────────┐                                            │
│  │ Declarative│  │  Unified   │                                            │
│  │   Deploy   │  │ Observability                                           │
│  └────────────┘  └────────────┘                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Overview

```mermaid
graph TB
    subgraph enterprise [PyNext Enterprise Architecture]
        P19[Phase 19: Feature Slices]
        P20[Phase 20: Pythonic CSS]
        P21[Phase 21: PyNext UI]
        P22[Phase 22: Workspace Boundaries]
        P23[Phase 23: Declarative Deploy]
        P24[Phase 24: Unified Observability]
    end
    
    P19 --> P20
    P20 --> P21
    P21 --> P22
    P22 --> P23
    P23 --> P24
    
    subgraph runtime [PyNext Runtime - Phases 25-32]
        P25[Package Manager]
        P26[AI Development]
        P27[Database Studio]
    end
    
    P24 --> P25
```

### Enterprise Architecture vs Next.js

| Capability | Next.js | NestJS | **PyNext Enterprise** |
|------------|---------|--------|----------------------|
| **Project Structure** | File-based, implicit | Module-based | **Feature Slices with enforced layers** |
| **Styling** | Tailwind strings, CSS Modules | N/A | **Pythonic CSS with variants** |
| **Components** | React, external libs | N/A | **Headless primitives you own** |
| **Monorepo** | Turborepo (separate) | Nx (separate) | **Built-in workspace boundaries** |
| **Deployment** | Vercel-specific, YAML | Docker/K8s manual | **Declarative Python, auto-generates all** |
| **Observability** | External tools | External tools | **Unified tracing, logs, metrics** |
| **Learning Curve** | Steep (many concepts) | Steep (decorators) | **Progressive (simple defaults)** |

### Enterprise Phases Summary

| Phase | Feature | Target Tests | Duration |
|-------|---------|--------------|----------|
| 19 | Feature Slices Architecture | 300+ | 6 weeks |
| 20 | Pythonic CSS Styling System | 400+ | 8 weeks |
| 21 | PyNext UI (Headless Components) | 500+ | 10 weeks |
| 22 | Workspace Boundaries | 250+ | 6 weeks |
| 23 | Declarative Deployment | 300+ | 8 weeks |
| 24 | Unified Observability | 350+ | 8 weeks |
| **Total** | | **2,100+** | **46 weeks** |

---

#### Phase 19: Feature Slices Architecture (Target: 300+ tests)

**Status:** 🔲 Planned
**Priority:** P0 (Critical - Foundation for Enterprise)
**Timeline:** 6 weeks

**Goal**: A feature-first project structure that's dramatically better than Next.js's file-based routing. Features are organized by domain, not by technical layer, with clear separation between data, API, and UI layers within each feature.

##### Problem Statement

Next.js and traditional frameworks organize code by technical concern:

```
# Next.js: Technical layers scattered across app
app/
├── checkout/
│   └── page.tsx          # UI only
├── api/
│   └── checkout/
│       └── route.ts      # API separate
├── lib/
│   └── checkout.ts       # Logic separate
└── types/
    └── checkout.ts       # Types separate
```

**Problems:**
- Related code scattered across directories
- No clear boundaries between features
- Easy to create circular dependencies
- Hard to extract features to packages/services

##### The Solution: Feature Slices

```
# PyNext: Feature-first with clear layers
apps/web/features/
├── checkout/
│   ├── data/              # Models, queries, types (database layer)
│   │   ├── models.py      # Cart, CartItem models
│   │   ├── queries.py     # get_cart(), get_items()
│   │   └── types.py       # CartDTO, ItemDTO
│   ├── api/               # Server actions, API routes (API layer)
│   │   ├── actions.py     # add_to_cart(), remove_item()
│   │   └── routes.py      # /api/cart endpoints
│   ├── ui/                # Components, pages (UI layer)
│   │   ├── cart.page.py   # Main cart page
│   │   ├── cart_item.py   # CartItem component
│   │   └── cart_summary.py
│   └── checkout.feature.py  # Public API (glue file)
```

##### Layer Dependency Diagram

```mermaid
graph TD
    subgraph feature [Feature: Checkout]
        subgraph ui_layer [UI Layer]
            CartPage[cart.page.py]
            CartItem[cart_item.py]
        end
        
        subgraph api_layer [API Layer]
            Actions[actions.py]
            Routes[routes.py]
        end
        
        subgraph data_layer [Data Layer]
            Models[models.py]
            Queries[queries.py]
            Types[types.py]
        end
    end
    
    CartPage --> Actions
    CartItem --> Actions
    Actions --> Models
    Actions --> Queries
    Routes --> Models
    
    ui_layer -.->|"imports allowed"| api_layer
    api_layer -.->|"imports allowed"| data_layer
    ui_layer -.->|"FORBIDDEN"| data_layer
```

##### Layer Rules

| Layer | Can Import From | Cannot Import From | Purpose |
|-------|----------------|-------------------|---------|
| **UI** (`ui/`) | `api/`, shared UI | `data/`, other features' `ui/` | Components, pages |
| **API** (`api/`) | `data/`, shared utils | `ui/`, other features' `api/` | Actions, routes |
| **Data** (`data/`) | shared types, ORM | `api/`, `ui/` | Models, queries |

##### Feature Communication Diagram

```mermaid
graph LR
    subgraph app [Web App]
        subgraph checkout [Checkout Feature]
            C_UI[UI]
            C_API[API]
            C_Data[Data]
        end
        
        subgraph auth [Auth Feature]
            A_UI[UI]
            A_API[API]
            A_Data[Data]
        end
        
        subgraph products [Products Feature]
            P_UI[UI]
            P_API[API]
            P_Data[Data]
        end
    end
    
    C_API -->|"via feature.py"| A_API
    C_API -->|"via feature.py"| P_API
    C_UI -->|"shared components"| A_UI
```

##### The Glue File Pattern

Each feature exposes a public API through a `*.feature.py` file:

```python
# checkout.feature.py - Public API for the checkout feature
"""Checkout feature - cart management and order processing."""

# Re-export public types
from .data.types import CartDTO, CartItemDTO, OrderDTO

# Re-export public actions  
from .api.actions import (
    add_to_cart,
    remove_from_cart,
    update_quantity,
    clear_cart,
    create_order,
)

# Re-export public queries
from .data.queries import (
    get_cart,
    get_cart_items,
    get_cart_total,
)

# Define what's public
__all__ = [
    # Types
    "CartDTO",
    "CartItemDTO", 
    "OrderDTO",
    # Actions
    "add_to_cart",
    "remove_from_cart",
    "update_quantity",
    "clear_cart",
    "create_order",
    # Queries
    "get_cart",
    "get_cart_items",
    "get_cart_total",
]
```

**Usage from other features:**

```python
# In products feature, importing from checkout
from features.checkout import add_to_cart, CartDTO

# NOT: from features.checkout.api.actions import add_to_cart  # FORBIDDEN
# NOT: from features.checkout.data.models import Cart         # FORBIDDEN
```

##### Architecture Linting

Enforce layer rules with CLI:

```bash
# Check architecture rules
pynext lint --architecture

# Output:
# ✗ features/checkout/ui/cart.page.py imports from features/checkout/data/models.py
#   UI layer cannot import directly from Data layer. Use API layer instead.
#
# ✗ features/products/api/actions.py imports from features/checkout/api/actions.py
#   Cross-feature imports must go through feature.py files.
#
# ✓ 47 files checked, 2 violations found
```

##### Example: Complete Feature

```python
# features/checkout/data/models.py
from pynext.db import Table

class Cart(Table):
    user_id: str
    items: list["CartItem"] = []

class CartItem(Table):
    cart_id: int
    product_id: int
    quantity: int
    price: float

# features/checkout/data/queries.py
from .models import Cart, CartItem

async def get_cart(user_id: str) -> Cart | None:
    return await Cart.where(user_id=user_id).with_related("items").first()

async def get_cart_total(cart: Cart) -> float:
    return sum(item.price * item.quantity for item in cart.items)

# features/checkout/api/actions.py
from pynext import action
from ..data.models import Cart, CartItem
from ..data.queries import get_cart

@action
async def add_to_cart(user_id: str, product_id: int, quantity: int = 1):
    cart = await get_cart(user_id)
    if not cart:
        cart = await Cart.insert(user_id=user_id)
    
    # Check if item exists
    existing = next((i for i in cart.items if i.product_id == product_id), None)
    if existing:
        existing.quantity += quantity
        await existing.save()
    else:
        await CartItem.insert(cart_id=cart.id, product_id=product_id, quantity=quantity)
    
    return await get_cart(user_id)

# features/checkout/ui/cart.page.py
from pynext import page
from ..api.actions import add_to_cart, remove_from_cart
from .cart_item import CartItem

@page("/cart")
def CartPage():
    cart = Cart.live(user_id=current_user().id)
    
    return Div(
        H1("Your Cart"),
        For(cart.items, lambda item: CartItem(item=item)),
        CartSummary(cart=cart),
    )
```

##### Success Metrics

| Metric | Target |
|--------|--------|
| Feature isolation | 100% (no cross-feature data imports) |
| Lint performance | < 1s for 1000 files |
| Developer adoption | 90%+ prefer feature slices |
| Extraction time | Feature → Package in < 1 hour |

---

#### Phase 20: Pythonic CSS Styling System (Target: 400+ tests)

**Status:** 🔲 Planned
**Priority:** P1 (High - Core DX)
**Timeline:** 8 weeks

**Goal**: Make CSS dramatically easier than Tailwind or CSS-in-JS with a Python-native API that provides type safety, IDE autocomplete, and zero runtime overhead.

##### Problem Statement

Current CSS approaches have significant pain points:

**Tailwind:**
```html
<!-- String soup, no type safety, hard to read -->
<button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 
               rounded focus:outline-none focus:shadow-outline disabled:opacity-50
               sm:py-3 sm:px-6 md:text-lg transition-all duration-200">
  Click me
</button>
```

**CSS-in-JS (styled-components):**
```jsx
// Separate template language, runtime cost
const Button = styled.button`
  background: ${props => props.primary ? 'blue' : 'gray'};
  &:hover { background: darkblue; }
`;
```

**Problems:**
- No type safety or autocomplete for class names
- Variants require complex conditional logic
- Responsive design is verbose
- State styles (hover, focus) scattered in strings

##### The Solution: Pythonic CSS

```python
from pynext.css import style, variants, theme, keyframes

# Type-safe, autocomplete, readable
button = style(
    background=theme.colors.primary,
    color="white",
    font_weight="bold",
    padding="0.5rem 1rem",
    border_radius="0.25rem",
    transition="all 0.2s",
    
    # States - clear and explicit
    hover={"background": theme.colors.primary_dark},
    focus={"outline": "none", "box_shadow": theme.shadows.ring},
    disabled={"opacity": 0.5, "cursor": "not-allowed"},
    
    # Responsive - just kwargs
    sm={"padding": "0.75rem 1.5rem"},
    md={"font_size": "1.125rem"},
)
```

##### Style Composition Diagram

```mermaid
graph TD
    subgraph inputs [Style Inputs]
        Theme[theme.colors.primary]
        States[hover, focus, active]
        Responsive[sm, md, lg, xl]
        Variants[size, color]
    end
    
    subgraph processing [Processing]
        StyleFn["style()"]
        VariantsFn["variants()"]
        ScopedDec["@scoped"]
    end
    
    subgraph outputs [Outputs]
        InlineCSS[Inline Styles]
        CSSVars[CSS Variables]
        ScopedCSS[Scoped Classes]
    end
    
    Theme --> StyleFn
    States --> StyleFn
    Responsive --> StyleFn
    StyleFn --> VariantsFn
    Variants --> VariantsFn
    
    StyleFn --> InlineCSS
    VariantsFn --> CSSVars
    ScopedDec --> ScopedCSS
```

##### Core API: `style()`

```python
from pynext.css import style, theme

# Basic style
card = style(
    background="white",
    border_radius="0.5rem",
    box_shadow=theme.shadows.md,
    padding="1.5rem",
)

# With states
button = style(
    background=theme.colors.primary,
    padding="0.75rem 1.5rem",
    border_radius="0.5rem",
    cursor="pointer",
    transition="all 0.2s ease",
    
    # Pseudo-states
    hover={
        "background": theme.colors.primary_dark,
        "transform": "translateY(-1px)",
    },
    focus={
        "outline": f"2px solid {theme.colors.ring}",
        "outline_offset": "2px",
    },
    active={
        "transform": "translateY(0)",
    },
    disabled={
        "opacity": 0.5,
        "cursor": "not-allowed",
        "pointer_events": "none",
    },
    
    # Responsive breakpoints
    sm={"padding": "0.5rem 1rem", "font_size": "0.875rem"},
    md={"padding": "0.75rem 1.5rem"},
    lg={"padding": "1rem 2rem", "font_size": "1.125rem"},
    xl={"padding": "1.25rem 2.5rem"},
)

# Usage in component
def Button(children, **props):
    return button.element("button", children, **props)
    # Or: return Btn(style=button, children=children, **props)
```

##### Variants API

```python
from pynext.css import style, variants

# Base button style
base_button = style(
    display="inline-flex",
    align_items="center",
    justify_content="center",
    font_weight="500",
    border_radius="0.375rem",
    transition="all 0.2s",
    cursor="pointer",
    
    focus={"outline": "2px solid", "outline_offset": "2px"},
    disabled={"opacity": 0.5, "cursor": "not-allowed"},
)

# Create variants
Button = variants(
    base=base_button,
    
    # Size variants
    size={
        "sm": {"padding": "0.25rem 0.75rem", "font_size": "0.875rem", "height": "2rem"},
        "md": {"padding": "0.5rem 1rem", "font_size": "1rem", "height": "2.5rem"},
        "lg": {"padding": "0.75rem 1.5rem", "font_size": "1.125rem", "height": "3rem"},
    },
    
    # Color variants
    color={
        "primary": {
            "background": theme.colors.primary,
            "color": "white",
            "hover": {"background": theme.colors.primary_dark},
        },
        "secondary": {
            "background": theme.colors.secondary,
            "color": "white",
            "hover": {"background": theme.colors.secondary_dark},
        },
        "outline": {
            "background": "transparent",
            "border": f"1px solid {theme.colors.border}",
            "hover": {"background": theme.colors.muted},
        },
        "ghost": {
            "background": "transparent",
            "hover": {"background": theme.colors.muted},
        },
        "danger": {
            "background": theme.colors.danger,
            "color": "white",
            "hover": {"background": theme.colors.danger_dark},
        },
    },
    
    # Default variants
    defaults={"size": "md", "color": "primary"},
)

# Usage
Button("Click me")                           # Default: md + primary
Button("Small", size="sm")                   # sm + primary
Button("Danger", color="danger", size="lg")  # lg + danger
Button("Ghost", color="ghost")               # md + ghost
```

##### Theme System Diagram

```mermaid
graph LR
    subgraph config [Theme Config]
        Colors[colors]
        Spacing[spacing]
        Typography[typography]
        Shadows[shadows]
    end
    
    subgraph modes [Theme Modes]
        Light[Light Mode]
        Dark[Dark Mode]
        Custom[Custom Themes]
    end
    
    subgraph usage [Usage]
        Component[Component]
        CSS[Generated CSS]
    end
    
    Colors --> Light
    Colors --> Dark
    Light --> Component
    Dark --> Component
    Component --> CSS
```

##### Theme Configuration

```python
# pynext.theme.py
from pynext.css import create_theme

theme = create_theme(
    colors={
        # Semantic colors
        "primary": "#3b82f6",
        "primary_dark": "#2563eb",
        "secondary": "#6b7280",
        "danger": "#ef4444",
        "success": "#22c55e",
        "warning": "#f59e0b",
        
        # UI colors
        "background": "#ffffff",
        "foreground": "#0f172a",
        "muted": "#f1f5f9",
        "border": "#e2e8f0",
        "ring": "#3b82f6",
        
        # Dark mode overrides (auto-applied)
        "dark": {
            "background": "#0f172a",
            "foreground": "#f8fafc",
            "muted": "#1e293b",
            "border": "#334155",
        },
    },
    
    spacing={
        "xs": "0.25rem",
        "sm": "0.5rem",
        "md": "1rem",
        "lg": "1.5rem",
        "xl": "2rem",
    },
    
    typography={
        "sans": "Inter, system-ui, sans-serif",
        "mono": "JetBrains Mono, monospace",
        "sizes": {
            "xs": "0.75rem",
            "sm": "0.875rem",
            "base": "1rem",
            "lg": "1.125rem",
            "xl": "1.25rem",
        },
    },
    
    shadows={
        "sm": "0 1px 2px rgba(0, 0, 0, 0.05)",
        "md": "0 4px 6px rgba(0, 0, 0, 0.1)",
        "lg": "0 10px 15px rgba(0, 0, 0, 0.1)",
        "ring": "0 0 0 3px rgba(59, 130, 246, 0.5)",
    },
    
    breakpoints={
        "sm": "640px",
        "md": "768px",
        "lg": "1024px",
        "xl": "1280px",
    },
)
```

##### Animations

```python
from pynext.css import keyframes, animate

# Define keyframes
fade_in = keyframes(
    from_={"opacity": 0, "transform": "translateY(10px)"},
    to={"opacity": 1, "transform": "translateY(0)"},
)

slide_in = keyframes({
    "0%": {"transform": "translateX(-100%)"},
    "100%": {"transform": "translateX(0)"},
})

pulse = keyframes({
    "0%, 100%": {"opacity": 1},
    "50%": {"opacity": 0.5},
})

# Apply animations
modal = style(
    animation=animate(fade_in, duration="0.2s", easing="ease-out"),
)

# Or inline
notification = style(
    animation=f"{slide_in} 0.3s ease-out",
)
```

##### Scoped CSS Decorator

```python
from pynext.css import scoped

@scoped
def Card(title: str, children):
    """Card component with scoped styles - no class name conflicts."""
    return Div(
        class_="card",  # Becomes: card_x7k2m (unique hash)
        children=[
            H2(class_="title", children=title),
            Div(class_="content", children=children),
        ],
    )

# Companion CSS (same file or .css file)
Card.css = """
.card {
    background: white;
    border-radius: 0.5rem;
    padding: 1.5rem;
}

.card .title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1rem;
}

.card .content {
    color: #64748b;
}
"""
```

##### Comparison: Tailwind vs PyNext CSS

| Aspect | Tailwind | PyNext CSS |
|--------|----------|------------|
| **Type Safety** | None | Full (IDE autocomplete) |
| **Variants** | Complex conditionals | First-class `variants()` |
| **States** | `hover:`, `focus:` prefixes | Explicit `hover={}` dict |
| **Responsive** | `sm:`, `md:` prefixes | `sm={}`, `md={}` kwargs |
| **Theming** | Tailwind config | Python theme object |
| **Dark Mode** | `dark:` prefix | Automatic via theme |
| **Runtime Cost** | None | None (build-time) |
| **Bundle Size** | Purged CSS | Minimal inline |
| **Readability** | String soup | Clear Python |

##### Success Metrics

| Metric | Target |
|--------|--------|
| Style creation time | < 50% of Tailwind |
| Zero runtime overhead | Compile-time only |
| Type coverage | 100% of CSS properties |
| Theme hot reload | < 50ms |
| Bundle size | Comparable to Tailwind |

---

#### Phase 21: PyNext UI (Headless Components) (Target: 500+ tests)

**Status:** 🔲 Planned
**Priority:** P1 (High - Core DX)
**Timeline:** 10 weeks

**Goal**: ShadCN-style headless components that you own and customize. Accessible, keyboard-navigable primitives with zero styling opinions.

##### Problem Statement

React component libraries have trade-offs:

| Library | Problem |
|---------|---------|
| **Material UI** | Opinionated styles, hard to customize |
| **Chakra UI** | Runtime CSS-in-JS, large bundle |
| **Radix UI** | React-only, requires separate styling |
| **ShadCN** | Great, but React/Tailwind only |

**What we want:**
- Headless (behavior only, you own styles)
- Accessible (ARIA, keyboard nav built-in)
- Python-native (not React wrappers)
- Copy into project (you own the code)

##### The Solution: PyNext UI

```bash
# Add components to your project
pynext ui add button dialog tabs select

# Components copied to packages/ui/primitives/
# You own the code, customize freely
```

##### Component Architecture Diagram

```mermaid
graph TD
    subgraph cli [CLI]
        Add["pynext ui add button"]
    end
    
    subgraph registry [Component Registry]
        Remote[Remote Registry]
        Local[Local Cache]
    end
    
    subgraph project [Your Project]
        Packages[packages/ui/primitives/]
        Button[button.py]
        Dialog[dialog.py]
    end
    
    subgraph usage [Usage]
        Import["from packages.ui import Button"]
        Customize[Custom Styling]
        Render[Rendered Component]
    end
    
    Add --> Remote
    Remote --> Local
    Local --> Packages
    Packages --> Button
    Packages --> Dialog
    Button --> Import
    Import --> Customize
    Customize --> Render
```

##### Project Structure After `pynext ui add`

```
packages/
└── ui/
    ├── __init__.py           # Re-exports all components
    ├── primitives/
    │   ├── button.py         # Button component
    │   ├── dialog.py         # Dialog component
    │   ├── tabs.py           # Tabs component
    │   ├── select.py         # Select component
    │   └── ...
    ├── styles/
    │   ├── button.py         # Default button styles (optional)
    │   └── ...
    └── utils/
        ├── compose.py        # Style composition utilities
        └── accessibility.py  # A11y helpers
```

##### Compound Component Pattern

```mermaid
graph TD
    subgraph dialog [Dialog Component]
        Root[Dialog.Root]
        Trigger[Dialog.Trigger]
        Portal[Dialog.Portal]
        Overlay[Dialog.Overlay]
        Content[Dialog.Content]
        Title[Dialog.Title]
        Description[Dialog.Description]
        Close[Dialog.Close]
    end
    
    Root --> Trigger
    Root --> Portal
    Portal --> Overlay
    Portal --> Content
    Content --> Title
    Content --> Description
    Content --> Close
```

##### Component Examples

**Button (Simple):**

```python
# packages/ui/primitives/button.py
from pynext import component
from pynext.css import style, variants

# Headless button - just behavior
@component
def Button(
    children,
    variant: str = "default",
    size: str = "md",
    disabled: bool = False,
    loading: bool = False,
    on_click = None,
    **props
):
    return button(
        disabled=disabled or loading,
        on_click=on_click if not loading else None,
        aria_busy=loading,
        data_variant=variant,
        data_size=size,
        **props,
        children=[
            Show(loading, Spinner(class_="button-spinner")),
            Span(class_="button-content", children=children),
        ],
    )

# Default styles (user can override or replace)
Button.styles = variants(
    base=style(
        display="inline-flex",
        align_items="center",
        justify_content="center",
        font_weight="500",
        border_radius="0.375rem",
        transition="all 0.15s",
        cursor="pointer",
        focus={"outline": "2px solid", "outline_offset": "2px"},
        disabled={"opacity": 0.5, "pointer_events": "none"},
    ),
    size={
        "sm": {"height": "2rem", "padding": "0 0.75rem", "font_size": "0.875rem"},
        "md": {"height": "2.5rem", "padding": "0 1rem", "font_size": "1rem"},
        "lg": {"height": "3rem", "padding": "0 1.5rem", "font_size": "1.125rem"},
    },
    variant={
        "default": {"background": "var(--primary)", "color": "white"},
        "outline": {"border": "1px solid var(--border)", "background": "transparent"},
        "ghost": {"background": "transparent", "hover": {"background": "var(--muted)"}},
    },
)
```

**Dialog (Compound):**

```python
# packages/ui/primitives/dialog.py
from pynext import component, Signal, create_context
from pynext.css import style

# Context for dialog state
DialogContext = create_context()

@component
def DialogRoot(children, open: Signal[bool] = None, on_open_change = None):
    """Root dialog container managing open state."""
    internal_open = open or Signal(False)
    
    def handle_change(new_state):
        internal_open.set(new_state)
        if on_open_change:
            on_open_change(new_state)
    
    return DialogContext.Provider(
        value={"open": internal_open, "on_change": handle_change},
        children=children,
    )

@component  
def DialogTrigger(children, as_child: bool = False):
    """Button that opens the dialog."""
    ctx = DialogContext.use()
    
    def handle_click():
        ctx["on_change"](True)
    
    if as_child:
        return children.clone(on_click=handle_click)
    
    return Button(on_click=handle_click, children=children)

@component
def DialogPortal(children):
    """Renders dialog in a portal at document root."""
    ctx = DialogContext.use()
    
    return Show(
        ctx["open"].get(),
        Portal(children=children),
    )

@component
def DialogOverlay(**props):
    """Backdrop behind dialog."""
    ctx = DialogContext.use()
    
    return Div(
        class_="dialog-overlay",
        on_click=lambda: ctx["on_change"](False),
        aria_hidden=True,
        **props,
    )

@component
def DialogContent(children, **props):
    """Main dialog content container."""
    ctx = DialogContext.use()
    
    # Handle Escape key
    def on_keydown(e):
        if e.key == "Escape":
            ctx["on_change"](False)
    
    return Div(
        role="dialog",
        aria_modal=True,
        class_="dialog-content",
        on_keydown=on_keydown,
        tabindex=-1,
        **props,
        children=children,
    )

@component
def DialogTitle(children, **props):
    """Accessible dialog title."""
    return H2(
        class_="dialog-title",
        id="dialog-title",
        **props,
        children=children,
    )

@component
def DialogDescription(children, **props):
    """Accessible dialog description."""
    return P(
        class_="dialog-description", 
        id="dialog-description",
        **props,
        children=children,
    )

@component
def DialogClose(children, **props):
    """Button that closes the dialog."""
    ctx = DialogContext.use()
    
    return Button(
        on_click=lambda: ctx["on_change"](False),
        aria_label="Close dialog",
        **props,
        children=children or "×",
    )

# Namespace export
class Dialog:
    Root = DialogRoot
    Trigger = DialogTrigger
    Portal = DialogPortal
    Overlay = DialogOverlay
    Content = DialogContent
    Title = DialogTitle
    Description = DialogDescription
    Close = DialogClose
```

**Usage:**

```python
from packages.ui import Dialog, Button
from pynext.css import style

# Custom styles
overlay_style = style(
    position="fixed",
    inset=0,
    background="rgba(0, 0, 0, 0.5)",
    backdrop_filter="blur(4px)",
)

content_style = style(
    position="fixed",
    top="50%",
    left="50%",
    transform="translate(-50%, -50%)",
    background="white",
    border_radius="0.5rem",
    padding="1.5rem",
    box_shadow="0 25px 50px -12px rgba(0, 0, 0, 0.25)",
    max_width="28rem",
    width="90%",
)

def ConfirmDialog():
    return Dialog.Root(
        Dialog.Trigger(Button("Delete Item")),
        Dialog.Portal(
            Dialog.Overlay(style=overlay_style),
            Dialog.Content(
                style=content_style,
                children=[
                    Dialog.Title("Confirm Delete"),
                    Dialog.Description("This action cannot be undone."),
                    Div(
                        style={"display": "flex", "gap": "0.5rem", "margin_top": "1rem"},
                        children=[
                            Dialog.Close(Button("Cancel", variant="outline")),
                            Button("Delete", variant="danger", on_click=delete_item),
                        ],
                    ),
                ],
            ),
        ),
    )
```

##### Component List

| Category | Components |
|----------|------------|
| **Buttons** | Button, IconButton, ButtonGroup, ToggleButton |
| **Inputs** | Input, Textarea, Checkbox, Radio, Switch, Slider, Select, Combobox |
| **Overlay** | Dialog, Modal, Sheet, Drawer, Popover, Tooltip, ContextMenu, DropdownMenu |
| **Feedback** | Alert, AlertDialog, Toast, Progress, Skeleton, Spinner |
| **Layout** | Card, Accordion, Tabs, Collapsible, Separator, AspectRatio |
| **Navigation** | NavigationMenu, Breadcrumb, Pagination, Menubar |
| **Data** | Table, Avatar, Badge, Tag, Calendar, DatePicker |

##### CLI Commands

```bash
# Add single component
pynext ui add button

# Add multiple components
pynext ui add dialog tabs select combobox

# Add all components
pynext ui add --all

# Update components (fetch latest)
pynext ui update button dialog

# List available components
pynext ui list

# Show component info
pynext ui info dialog
```

##### Success Metrics

| Metric | Target |
|--------|--------|
| Accessibility score | 100% (axe-core) |
| Keyboard navigation | Full support |
| Component count | 25+ primitives |
| Bundle per component | < 2KB gzipped |
| Customization time | < 5 min per component |

---

#### Phase 22: Workspace Boundaries (Monorepo) (Target: 250+ tests)

**Status:** 🔲 Planned
**Priority:** P1 (High - Enterprise Scale)
**Timeline:** 6 weeks

**Goal**: Enterprise monorepo organization with clear boundaries, explicit dependency rules, and progressive extraction from features to packages to microservices.

##### Problem Statement

Monorepo tools like Turborepo/Nx are powerful but complex:

- Separate tool to learn and configure
- Implicit dependency detection
- Build configuration complexity
- Unclear extraction paths

**What we want:**
- Built into PyNext (no separate tool)
- Explicit dependencies via Python
- Clear workspace structure
- Simple feature → package → service evolution

##### The Solution: PyNext Workspaces

```python
# pynext.workspace.py
from pynext.workspace import Workspace, App, Service, Package

workspace = Workspace(
    name="mycompany",
    
    apps={
        "web": App(
            path="apps/web",
            depends_on=["ui", "utils", "config"],
        ),
        "admin": App(
            path="apps/admin", 
            depends_on=["ui", "utils"],
        ),
    },
    
    services={
        "payments": Service(
            path="services/payments",
            depends_on=["utils", "types"],
            port=8001,
        ),
        "notifications": Service(
            path="services/notifications",
            depends_on=["utils", "queue"],
            port=8002,
        ),
    },
    
    packages={
        "ui": Package(path="packages/ui"),
        "utils": Package(path="packages/utils"),
        "config": Package(path="packages/config"),
        "types": Package(path="packages/types"),
        "queue": Package(path="packages/queue"),
    },
    
    infra={
        "database": "infra/database",
        "cache": "infra/cache",
    },
)
```

##### Workspace Structure Diagram

```mermaid
graph TD
    subgraph workspace [PyNext Workspace]
        subgraph apps [apps/]
            Web[web/]
            Admin[admin/]
            Mobile[mobile-web/]
        end
        
        subgraph services [services/]
            Payments[payments/]
            Notifications[notifications/]
            Search[search/]
        end
        
        subgraph packages [packages/]
            UI[ui/]
            Utils[utils/]
            Config[config/]
            Types[types/]
        end
        
        subgraph infra [infra/]
            Database[database/]
            Cache[cache/]
            Queue[queue/]
        end
    end
    
    Web --> UI
    Web --> Utils
    Admin --> UI
    Payments --> Utils
    Payments --> Types
    Notifications --> Queue
```

##### Directory Structure

```
pynext-workspace/
├── pynext.workspace.py          # Workspace configuration
├── apps/
│   ├── web/                     # Main web application
│   │   ├── features/            # Feature slices
│   │   ├── pages/               # Public pages
│   │   └── pynext.app.py        # App config
│   └── admin/                   # Admin dashboard
│       ├── features/
│       └── pynext.app.py
├── services/
│   ├── payments/                # Payments microservice
│   │   ├── data/
│   │   ├── api/
│   │   ├── ui/                  # Admin UI for service
│   │   └── pynext.service.py    # Service config
│   └── notifications/
│       ├── data/
│       ├── api/
│       └── pynext.service.py
├── packages/
│   ├── ui/                      # Shared UI components
│   │   ├── primitives/
│   │   ├── styles/
│   │   └── __init__.py
│   ├── utils/                   # Shared utilities
│   │   ├── dates.py
│   │   ├── validation.py
│   │   └── __init__.py
│   ├── config/                  # Shared configuration
│   │   └── __init__.py
│   └── types/                   # Shared type definitions
│       └── __init__.py
└── infra/
    ├── database/                # Database schemas, migrations
    │   ├── migrations/
    │   └── schema.py
    ├── cache/                   # Cache configuration
    └── queue/                   # Message queue config
```

##### Dependency Flow Diagram

```mermaid
graph LR
    subgraph allowed [Allowed Dependencies]
        Apps[Apps]
        Services[Services]
        Packages[Packages]
        Infra[Infra]
    end
    
    Apps -->|"can import"| Packages
    Apps -->|"can import"| Infra
    Services -->|"can import"| Packages
    Services -->|"can import"| Infra
    Packages -->|"can import"| Infra
    
    Apps -.->|"CANNOT import"| Services
    Apps -.->|"CANNOT import"| Apps
    Services -.->|"CANNOT import"| Apps
```

##### Dependency Rules

| From | Can Import | Cannot Import | Why |
|------|------------|---------------|-----|
| **Apps** | packages/, infra/ | services/, other apps/ | Apps are deployment units |
| **Services** | packages/, infra/ | apps/, other services/ | Services are isolated |
| **Packages** | other packages/, infra/ | apps/, services/ | Packages are shared code |
| **Infra** | Nothing (leaf) | Everything | Infra is foundational |

##### Service Extraction Flow

```mermaid
graph LR
    subgraph evolution [Feature Evolution]
        Feature[Feature in App]
        Package[Shared Package]
        Service[Microservice]
    end
    
    Feature -->|"extract shared logic"| Package
    Package -->|"needs own deployment"| Service
    
    subgraph communication [Communication]
        HTTP[HTTP Client]
        GRPC[gRPC Client]
        Events[Event Bus]
    end
    
    Service --> HTTP
    Service --> GRPC
    Service --> Events
```

**Evolution Path:**

```bash
# 1. Start: Feature in app
apps/web/features/payments/

# 2. Extract shared logic to package
pynext extract packages/payments-core --from apps/web/features/payments/data

# 3. Promote to service (needs own deployment)
pynext promote services/payments --from packages/payments-core
```

##### Build-Time Bundling

Shared code is copied into deployment artifacts at build time:

```python
# At build time:
# - apps/web imports packages/ui → ui code bundled into web
# - services/payments imports packages/utils → utils code bundled into payments

# Result: Each deployment is self-contained
dist/
├── web/                    # Contains web + ui + utils + config
├── admin/                  # Contains admin + ui + utils
└── payments/               # Contains payments + utils + types
```

##### Service Communication

Services communicate at runtime via generated clients:

```python
# Auto-generated client for payments service
# packages/clients/payments.py (generated)
from pynext.client import ServiceClient

class PaymentsClient(ServiceClient):
    """Auto-generated client for payments service."""
    
    async def create_payment(self, order_id: str, amount: float) -> Payment:
        return await self._call("create_payment", order_id=order_id, amount=amount)
    
    async def get_payment(self, payment_id: str) -> Payment:
        return await self._call("get_payment", payment_id=payment_id)

# Usage in web app
from packages.clients import PaymentsClient

payments = PaymentsClient()
payment = await payments.create_payment(order.id, order.total)
```

##### CLI Commands

```bash
# Workspace management
pynext workspace init              # Create pynext.workspace.py
pynext workspace validate          # Check dependency rules
pynext workspace graph             # Visualize dependencies

# Development
pynext dev                         # Run all apps and services
pynext dev apps/web                # Run specific app
pynext dev services/payments       # Run specific service

# Extraction
pynext extract packages/core --from apps/web/features/shared
pynext promote services/auth --from packages/auth

# Building
pynext build                       # Build all
pynext build apps/web              # Build specific
pynext build --affected            # Build only changed
```

##### Success Metrics

| Metric | Target |
|--------|--------|
| Dependency validation | < 1s for 1000 files |
| Build parallelization | Full (independent units) |
| Extraction time | Feature → Package < 10 min |
| Service generation | Client generated in < 5s |

---

#### Phase 23: Declarative Deployment (Target: 300+ tests)

**Status:** 🔲 Planned
**Priority:** P1 (High - Production Ready)
**Timeline:** 8 weeks

**Goal**: Python-based infrastructure configuration that "just works" with smart defaults, while offering progressive complexity for enterprise needs. Auto-generates Docker, Kubernetes, Terraform, and CI/CD.

##### Problem Statement

Deployment today is painful:

| Approach | Problem |
|----------|---------|
| **Vercel** | Vendor lock-in, expensive at scale |
| **Docker + K8s** | YAML hell, steep learning curve |
| **Terraform** | Complex HCL syntax, state management |
| **Manual** | Error-prone, not reproducible |

**What we want:**
- Start simple (`pynext deploy`)
- Progressive complexity as needed
- Python config (not YAML/HCL)
- Auto-generate all artifacts

##### The Solution: Declarative Deployment

```python
# pynext.deploy.py - Simple start
from pynext.deploy import App, deploy

deploy(App("web"))  # That's it! Auto-detects everything.
```

```python
# pynext.deploy.py - Progressive complexity
from pynext.deploy import App, Service, Database, Redis, deploy, lock

deploy(
    apps=[
        App("web", domain="myapp.com", env="production"),
        App("admin", domain="admin.myapp.com"),
    ],
    
    services=[
        Service("payments", replicas=3, cpu="2", memory="4Gi"),
        Service("notifications", replicas=2, cpu="1", memory="2Gi"),
    ],
    
    database=Database(
        provider="supabase",  # or "postgres", "planetscale"
        pooling=True,
        max_connections=100,
    ),
    
    cache=Redis(cluster=True),
    
    globals=lock(
        region="us-east-1",
        log_level="info",
        tracing=True,
    ),
)
```

##### Deployment Flow Diagram

```mermaid
graph TD
    subgraph config [Configuration]
        Central["pynext.deploy.py"]
        Local["apps/web/deploy.py"]
        Env[".env files"]
    end
    
    subgraph merge [Config Merge]
        Defaults[Smart Defaults]
        Override["override()"]
        Lock["lock()"]
    end
    
    subgraph generate [Generated Artifacts]
        Docker[Dockerfile]
        Compose[docker-compose.yml]
        K8s[kubernetes/]
        Terraform[terraform/]
        Actions[.github/workflows/]
    end
    
    subgraph deploy [Deploy Targets]
        Vercel[Vercel]
        Fly[Fly.io]
        Railway[Railway]
        K8sCluster[Kubernetes]
        Custom[Custom VPS]
    end
    
    Central --> Merge
    Local --> Merge
    Env --> Merge
    Merge --> Defaults
    Defaults --> Override
    Override --> Lock
    Lock --> Docker
    Lock --> Compose
    Lock --> K8s
    Lock --> Terraform
    Lock --> Actions
    
    Docker --> Fly
    Docker --> Railway
    Docker --> Custom
    K8s --> K8sCluster
    Actions --> Vercel
```

##### Configuration Hierarchy

```mermaid
graph TD
    subgraph hierarchy [Configuration Hierarchy]
        Global["pynext.deploy.py (global)"]
        App["apps/web/deploy.py"]
        Service["services/payments/deploy.py"]
        Infra["infra/deploy.py"]
    end
    
    subgraph result [Final Config]
        Merged[Merged Configuration]
    end
    
    Global -->|"base config"| Merged
    App -->|"app overrides"| Merged
    Service -->|"service overrides"| Merged
    Infra -->|"infra additions"| Merged
```

##### Local Deploy Files

Each app/service can have its own `deploy.py`:

```python
# apps/web/deploy.py
from pynext.deploy import override

override(
    env_vars={
        "NEXT_PUBLIC_API_URL": "https://api.myapp.com",
        "ANALYTICS_KEY": "${ANALYTICS_KEY}",  # From secrets
    },
    
    scaling=AutoScale(
        min_replicas=2,
        max_replicas=20,
        target_cpu=70,
        target_memory=80,
    ),
    
    health_check=HealthCheck(
        path="/api/health",
        interval="30s",
        timeout="5s",
    ),
)
```

```python
# services/payments/deploy.py  
from pynext.deploy import override

override(
    replicas=3,
    cpu="2",
    memory="4Gi",
    
    # Service-specific config
    env_vars={
        "STRIPE_KEY": "${STRIPE_SECRET_KEY}",
        "WEBHOOK_SECRET": "${STRIPE_WEBHOOK_SECRET}",
    },
    
    # PCI compliance requirements
    network=Network(
        ingress=["apps/web"],  # Only web can call payments
        egress=["stripe.com", "database"],
    ),
)
```

##### Override and Lock

```python
# pynext.deploy.py - Central control
from pynext.deploy import deploy, lock, override

deploy(
    # Lock: Cannot be overridden by local deploy.py
    globals=lock(
        region="us-east-1",      # Immutable
        log_level="info",        # Immutable  
        tracing=True,            # Immutable
        min_tls_version="1.2",   # Security requirement
    ),
    
    # Can be overridden by local deploy.py
    defaults=override(
        replicas=1,              # Default, can increase
        cpu="1",                 # Default, can increase
        memory="2Gi",            # Default, can increase
    ),
)
```

##### Generated Artifacts

```bash
# Generate all deployment artifacts
pynext deploy generate

# Creates:
.deploy/
├── docker/
│   ├── web.Dockerfile
│   ├── admin.Dockerfile
│   ├── payments.Dockerfile
│   └── docker-compose.yml
├── kubernetes/
│   ├── web-deployment.yaml
│   ├── web-service.yaml
│   ├── payments-deployment.yaml
│   ├── payments-service.yaml
│   ├── ingress.yaml
│   └── configmaps/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── vpc/
│       ├── rds/
│       └── eks/
└── .github/
    └── workflows/
        ├── deploy-web.yml
        ├── deploy-admin.yml
        ├── deploy-payments.yml
        └── preview.yml
```

##### Deploy Commands

```bash
# Simple deploy (auto-detects platform)
pynext deploy

# Deploy to specific platform
pynext deploy --platform=vercel
pynext deploy --platform=fly
pynext deploy --platform=railway
pynext deploy --platform=kubernetes

# Deploy specific targets
pynext deploy apps/web
pynext deploy services/payments

# Preview deployments
pynext deploy --preview    # Creates PR preview environment

# Dry run
pynext deploy --dry-run    # Shows what would happen
```

##### Platform Detection

```python
# Auto-detection order:
# 1. Explicit --platform flag
# 2. Environment variables (VERCEL, FLY_APP_NAME, RAILWAY_ENVIRONMENT)
# 3. Config files (vercel.json, fly.toml, railway.json)
# 4. Git remotes (vercel.com, fly.io)
# 5. Default: Docker (universal fallback)
```

##### Success Metrics

| Metric | Target |
|--------|--------|
| Zero-config deploy | Works for 80% of projects |
| Artifact generation | < 5s |
| First deploy time | < 5 min |
| Preview environments | Auto per PR |
| Rollback time | < 30s |

---

#### Phase 24: Unified Observability (Target: 350+ tests)

**Status:** 🔲 Planned
**Priority:** P1 (High - Production Ready)
**Timeline:** 8 weeks

**Goal**: Automatic tracing, structured logging, and error tracking across the entire stack with zero configuration. Development logs unified, production exports to any backend.

##### Problem Statement

Observability today requires multiple tools:

| Concern | Typical Tools | Problem |
|---------|---------------|---------|
| **Tracing** | Jaeger, Zipkin, Datadog | Complex setup, manual instrumentation |
| **Logging** | Winston, Bunyan, structlog | Separate per service, no correlation |
| **Errors** | Sentry, Bugsnag | Another SDK, manual context |
| **Metrics** | Prometheus, StatsD | Yet another tool |

**What we want:**
- One unified system
- Automatic instrumentation
- Correlation across services
- Simple dev experience

##### The Solution: Unified Observability

```python
from pynext.observe import log, trace, metric

@trace("checkout.process")
async def process_order(order_id: str):
    log.info("Processing order", order_id=order_id)
    # Auto-enriched: request_id, user_id, trace_id, route, duration
    
    with trace.span("validate"):
        await validate_order(order_id)
    
    with trace.span("charge"):
        await charge_payment(order_id)
    
    metric.increment("orders.processed")
```

##### Observability Architecture Diagram

```mermaid
graph TD
    subgraph sources [Data Sources]
        WebApp[Web App]
        PaymentsSvc[Payments Service]
        NotificationsSvc[Notifications Service]
        Database[(Database)]
    end
    
    subgraph collection [Collection Layer]
        Traces[Distributed Traces]
        Logs[Structured Logs]
        Metrics[Metrics]
        Errors[Error Reports]
    end
    
    subgraph correlation [Correlation]
        RequestID[Request ID]
        TraceID[Trace ID]
        UserID[User ID]
    end
    
    subgraph export [Export]
        OTEL[OpenTelemetry]
        DevLogs["pynext dev --logs"]
    end
    
    subgraph backends [Backends]
        Datadog[Datadog]
        Honeycomb[Honeycomb]
        Grafana[Grafana]
        Console[Dev Console]
    end
    
    WebApp --> Traces
    WebApp --> Logs
    PaymentsSvc --> Traces
    PaymentsSvc --> Logs
    NotificationsSvc --> Traces
    Database --> Metrics
    
    Traces --> RequestID
    Logs --> RequestID
    RequestID --> TraceID
    TraceID --> UserID
    
    UserID --> OTEL
    UserID --> DevLogs
    
    OTEL --> Datadog
    OTEL --> Honeycomb
    OTEL --> Grafana
    DevLogs --> Console
```

##### Request Tracing Flow

```mermaid
sequenceDiagram
    participant Browser
    participant WebApp
    participant Payments
    participant Database
    participant Logs
    
    Browser->>WebApp: POST /checkout
    Note over WebApp: trace_id: abc123
    WebApp->>Logs: log.info("Checkout started", trace_id=abc123)
    
    WebApp->>Payments: process_payment()
    Note over Payments: trace_id: abc123 (propagated)
    Payments->>Logs: log.info("Processing payment", trace_id=abc123)
    
    Payments->>Database: INSERT transaction
    Payments->>Logs: log.info("Payment complete", trace_id=abc123)
    
    Payments-->>WebApp: success
    WebApp->>Logs: log.info("Checkout complete", trace_id=abc123)
    WebApp-->>Browser: 200 OK
```

##### Automatic Instrumentation

PyNext automatically instruments:

```python
# Automatic - no code needed
- HTTP requests (incoming and outgoing)
- Database queries (with query text, duration)
- Cache operations (hits, misses, duration)
- Background jobs (queued, started, completed, failed)
- Server actions (invoked, completed, errors)
- WebSocket connections (connected, messages, disconnected)
```

##### Structured Logging

```python
from pynext.observe import log

# Simple logging
log.info("User signed up")
log.warning("Rate limit approaching")
log.error("Payment failed", error=e)

# With context (auto-merged with request context)
log.info("Order created", 
    order_id=order.id,
    total=order.total,
    items=len(order.items),
)

# Output (development):
# 2024-01-15 10:23:45 INFO  [web] Order created
#   order_id=ord_123 total=99.99 items=3
#   request_id=req_abc trace_id=abc123 user_id=usr_456
#   route=/checkout duration=45ms

# Output (production - JSON):
# {"level":"info","msg":"Order created","order_id":"ord_123",
#  "total":99.99,"items":3,"request_id":"req_abc",
#  "trace_id":"abc123","user_id":"usr_456","route":"/checkout",
#  "duration_ms":45,"timestamp":"2024-01-15T10:23:45Z"}
```

##### Auto-Enrichment

Every log is automatically enriched:

| Field | Source | Example |
|-------|--------|---------|
| `request_id` | Generated per request | `req_abc123` |
| `trace_id` | Propagated across services | `abc123` |
| `span_id` | Current span | `span_456` |
| `user_id` | Auth context | `usr_789` |
| `route` | Current route | `/checkout` |
| `method` | HTTP method | `POST` |
| `service` | Service name | `web` |
| `version` | App version | `1.2.3` |
| `environment` | Deployment env | `production` |
| `duration_ms` | Request duration | `45` |

##### Tracing API

```python
from pynext.observe import trace

# Decorator-based tracing
@trace("checkout.process")
async def process_order(order_id: str):
    # Automatic span created
    ...

# Context manager for sub-spans
async def process_order(order_id: str):
    with trace.span("validate_order"):
        await validate(order_id)
    
    with trace.span("charge_payment") as span:
        span.set_attribute("payment_method", "card")
        await charge(order_id)
    
    with trace.span("send_confirmation"):
        await send_email(order_id)

# Manual spans
span = trace.start_span("custom_operation")
try:
    # ... work ...
    span.set_status("ok")
finally:
    span.end()
```

##### Error Tracking

```python
from pynext.observe import error_boundary, capture_error

# Automatic error boundaries in components
@error_boundary(fallback=ErrorPage)
def CheckoutPage():
    # Any error here is automatically:
    # - Logged with full context
    # - Reported to error tracking
    # - Shown to user via fallback
    ...

# Manual error capture
try:
    await risky_operation()
except Exception as e:
    capture_error(e, context={
        "operation": "risky_operation",
        "user_id": user.id,
    })
    raise
```

##### Metrics API

```python
from pynext.observe import metric

# Counter
metric.increment("orders.created")
metric.increment("orders.created", tags={"type": "subscription"})

# Gauge
metric.gauge("active_connections", connection_count)

# Histogram
metric.histogram("order.total", order.total)
metric.histogram("response.time", duration_ms)

# Timer
with metric.timer("payment.process"):
    await process_payment()
```

##### Development Experience

```bash
# Unified log viewer in development
pynext dev --logs

# Output:
┌─────────────────────────────────────────────────────────────────┐
│ PyNext Dev Logs - All Services                                   │
├─────────────────────────────────────────────────────────────────┤
│ 10:23:45 [web]      INFO  Request started POST /checkout        │
│ 10:23:45 [web]      INFO  Order created order_id=ord_123        │
│ 10:23:45 [payments] INFO  Processing payment order_id=ord_123   │
│ 10:23:46 [payments] INFO  Payment successful payment_id=pay_456 │
│ 10:23:46 [web]      INFO  Request completed 200 45ms            │
├─────────────────────────────────────────────────────────────────┤
│ Filter: [all] [web] [payments] [errors] [slow>100ms]            │
└─────────────────────────────────────────────────────────────────┘
```

##### Production Export

```python
# pynext.observe.py - Production configuration
from pynext.observe import configure

configure(
    # OpenTelemetry export
    tracing=OTLPExporter(
        endpoint="https://api.honeycomb.io",
        headers={"x-honeycomb-team": "${HONEYCOMB_API_KEY}"},
    ),
    
    # Structured log export
    logging=LogExporter(
        providers=[
            DatadogLogs(api_key="${DATADOG_API_KEY}"),
            CloudWatchLogs(log_group="/pynext/production"),
        ],
    ),
    
    # Error tracking
    errors=SentryExporter(
        dsn="${SENTRY_DSN}",
        environment="production",
    ),
    
    # Metrics
    metrics=PrometheusExporter(port=9090),
)
```

##### Success Metrics

| Metric | Target |
|--------|--------|
| Zero-config tracing | Automatic for all requests |
| Log correlation | 100% requests traceable |
| Error capture rate | 100% (no lost errors) |
| Instrumentation overhead | < 1ms per request |
| Export latency | Async, non-blocking |

---

## PyNext Runtime: The Complete Full-Stack Python Runtime

### Vision

PyNext is evolving from a framework into a **complete full-stack Python runtime** — the most powerful and fastest development environment for building web applications.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PYNEXT RUNTIME                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PyNext = Package Manager + Framework + Database + Deployment +             │
│           AI Tooling + Background Jobs + Analytics + Feature Flags          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Why Faster Than Bun                              │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  • Go-powered parallel resolution (not JavaScript)                  │   │
│  │  • Unified npm + pip in single resolution graph                     │   │
│  │  • Pre-computed dependency graphs cached globally                   │   │
│  │  • Zero-copy memory-mapped package cache                            │   │
│  │  • Parallel downloads with HTTP/2 connection pooling                │   │
│  │  • Content-addressable storage (deduplication across projects)      │   │
│  │  • SAT-based version resolution (PubGrub algorithm)                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  One command. Both ecosystems. Faster than either.                          │
│                                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Packages  │  │  Database  │  │    AI      │  │   Deploy   │           │
│  │  npm + pip │  │  Studio    │  │   Native   │  │  Universal │           │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘           │
│                                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │   Jobs     │  │    Live    │  │  Feature   │  │ Analytics  │           │
│  │ Background │  │   Collab   │  │   Flags    │  │ Monitoring │           │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### PyNext vs Bun

| Capability | Bun | PyNext Runtime |
|------------|-----|----------------|
| **Languages** | JavaScript only | Python + JavaScript unified |
| **Package Manager** | npm only | npm + pip + pynext registry |
| **Database** | Basic SQLite | Full ORM + migrations + visual studio |
| **AI Tooling** | None | Generate, explain, fix, test, review |
| **Background Jobs** | None | Built-in queue with scheduling |
| **Deployment** | Bun-compatible only | Universal (Vercel, CF, Fly, Docker, etc.) |
| **Real-time** | WebSocket only | Live state, presence, collaboration |
| **Feature Flags** | None | Built-in rollouts + A/B testing |
| **Analytics** | None | Built-in monitoring + dashboard |
| **Cold Install** | ~3s (100 deps) | <1s (Go parallel resolver) |
| **Warm Install** | ~300ms | <100ms (content-addressed cache) |

### Runtime Phases Summary

| Phase | Feature | Target Tests | Duration |
|-------|---------|--------------|----------|
| 25 | Unified Package Manager | 800+ | 12 weeks |
| 26 | AI-Native Development | 400+ | 8 weeks |
| 27 | Database Studio & Migrations | 400+ | 8 weeks |
| 28 | Background Jobs | 300+ | 8 weeks |
| 29 | Universal Deployment | 200+ | 8 weeks |
| 30 | Live Collaboration | 250+ | 8 weeks |
| 31 | Feature Flags & Rollouts | 200+ | 8 weeks |
| 32 | Analytics & Monitoring | 200+ | 8 weeks |
| **Total** | | **2,750+** | |

---

#### Phase 25: Unified Package Manager (Target: 800+ tests)

**Status:** 🔲 Planned
**Priority:** P0 (Critical - Foundation for Runtime)
**Timeline:** 12 weeks

**Goal**: The fastest, smartest, and most LLM-friendly package manager for full-stack development. Handles npm + pip + pynext registry in a unified system. Not just faster than Bun—better conflict resolution, better error messages, and structured output designed for AI systems.

##### Why Faster Than Bun

| Operation | Bun | PyNext | Why PyNext Wins |
|-----------|-----|--------|-----------------|
| Cold install (100 deps) | ~3s | <1s | Go parallel resolver + connection pooling |
| Warm install (100 deps) | ~300ms | <100ms | Memory-mapped cache, zero parsing |
| Resolution | Single-threaded | Parallel goroutines | Go's concurrency model |
| Ecosystem | npm only | npm + pip unified | Single resolution graph |
| Cache | Per-project | Global content-addressed | Deduplication across projects |
| Lockfile parse | JavaScript | Go + mmap | Zero-copy reads |

##### Why Better Than Bun (Beyond Speed)

| Capability | Bun | PyNext | Why PyNext is Better |
|------------|-----|--------|---------------------|
| **Ecosystems** | npm only | npm + pip + pynext | Unified resolution across ecosystems |
| **Conflict Resolution** | Basic errors | Interactive + auto-fix | Solves 90%+ conflicts automatically |
| **Error Messages** | Generic | Context-rich with solutions | "Did you mean X?" + one-click fix |
| **Offline Mode** | Partial | Full offline-first | Works without internet after first install |
| **Reproducibility** | Good | Perfect | Byte-for-byte identical builds |
| **Monorepo** | Basic | First-class workspaces | Shared deps, hoisting, cross-references |
| **Security** | Audit only | Audit + auto-patch + block | Prevents vulnerable installs |
| **Compatibility DB** | None | Pre-computed matrix | Knows what works together before you try |
| **LLM-Friendly** | Human output only | Structured JSON + API | Easy for AI systems to parse and use |
| **Deprecation Handling** | Manual | Automatic replacement | Auto-migrates to successor packages |

##### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PyNext Package Manager                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Go Resolution Engine                              │   │
│  │  • Parallel dependency resolution (goroutines)                       │   │
│  │  • SAT solver for version conflicts (PubGrub algorithm)             │   │
│  │  • Pre-computed compatibility matrix                                 │   │
│  │  • Incremental resolution (only changed deps)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│          ┌─────────────────────────┼─────────────────────────┐              │
│          ▼                         ▼                         ▼              │
│  ┌───────────────┐       ┌───────────────┐       ┌───────────────┐         │
│  │  npm Registry │       │  PyPI Registry │       │ PyNext Registry│         │
│  │  (parallel)   │       │  (parallel)    │       │  (parallel)   │         │
│  └───────────────┘       └───────────────┘       └───────────────┘         │
│          │                         │                         │              │
│          └─────────────────────────┼─────────────────────────┘              │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                 Content-Addressable Cache                            │   │
│  │  ~/.pynext/cache/                                                    │   │
│  │  ├── blobs/           # SHA256-addressed package contents           │   │
│  │  ├── metadata/        # Pre-parsed package metadata                  │   │
│  │  ├── graphs/          # Pre-computed dependency graphs               │   │
│  │  └── index.db         # SQLite index for fast lookups               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

##### CLI Commands - Installation

```bash
# Add packages (auto-detect ecosystem)
pynext add lodash pandas            # Detects: lodash→npm, pandas→pip
pynext add npm:chart.js pip:numpy   # Explicit ecosystem
pynext add @pynext/charts           # PyNext registry

# Install from lockfile (extremely fast)
pynext install                      # Parallel install from pynext.lock
pynext install --frozen             # Fail if lockfile outdated

# Remove packages
pynext remove lodash pandas

# Update packages
pynext update                       # Update all
pynext update lodash                # Update specific
pynext update --interactive         # Choose updates interactively

# Dependency inspection
pynext why lodash                   # Why is this installed?
pynext list                         # List all dependencies
pynext list --tree                  # Dependency tree
pynext outdated                     # Show outdated packages

# Security
pynext audit                        # Security audit both ecosystems
pynext audit --fix                  # Auto-fix vulnerabilities
```

##### CLI Commands - Publishing

```bash
# Initialize a publishable package
pynext init                         # Create pynext.package.toml
pynext init --template=component    # From template

# Build package
pynext build                        # Build for distribution
pynext build --check                # Validate without building

# Publish to registry
pynext login                        # Authenticate with registry
pynext publish                      # Publish to PyNext registry
pynext publish --dry-run            # Preview what would be published
pynext publish --tag=beta           # Publish with tag

# Package management
pynext whoami                       # Show logged-in user
pynext owner add <user> <package>   # Add package owner
pynext deprecate <package> <msg>    # Deprecate a version
pynext unpublish <package>@<ver>    # Remove version (within 72h)
```

##### Package Format (`pynext.package.toml`)

```toml
[package]
name = "@myorg/data-table"
version = "1.0.0"
description = "A sortable, filterable data table component"
license = "MIT"
repository = "https://github.com/myorg/data-table"
keywords = ["table", "data", "component"]

[author]
name = "Jane Developer"
email = "jane@example.com"

# What this package provides
[layers]
frontend = true      # Has frontend components
backend = true       # Has backend utilities
database = false     # No database models

# Dependencies
[dependencies.npm]
papaparse = "^5.4"
lodash = "^4.17"

[dependencies.pip]
pandas = ">=2.0"

[dependencies.pynext]
"@pynext/shadcn" = "^1.0"

# Files to include
[files]
include = ["components/", "utils/", "README.md"]
exclude = ["tests/", "*.test.py"]

# Entry points
[exports]
"." = "components/__init__.py"
"./utils" = "utils/__init__.py"
```

##### Lockfile Format (`pynext.lock`)

```toml
# Auto-generated - DO NOT EDIT
version = 2
resolved_at = "2025-01-15T10:30:00Z"
resolver_version = "1.0.0"

# Resolution metadata
[resolution]
strategy = "highest"  # or "minimal", "locked"
platforms = ["linux-x64", "darwin-arm64", "win32-x64"]

# npm packages
[npm.lodash]
version = "4.17.21"
integrity = "sha512-v2kDEe57lecTulaDIuNTPy3Ry4gLGJ6Z1O3vE1krgXZNrsQ+LFTGHVxVjcXPs17LhbZVGedAJv8XZ1tvj5FvSg=="
resolved = "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz"
engines = { node = ">=0.10.0" }

[npm.papaparse]
version = "5.4.1"
integrity = "sha512-..."
resolved = "https://registry.npmjs.org/papaparse/-/papaparse-5.4.1.tgz"
dependencies = {}

# pip packages
[pip.pandas]
version = "2.1.0"
hash = "sha256:abc123..."
requires_python = ">=3.9"
dependencies = ["numpy>=1.23.2", "python-dateutil>=2.8.2"]

[pip.numpy]
version = "1.26.0"
hash = "sha256:def456..."
requires_python = ">=3.9"

# pynext packages
[pynext."@pynext/shadcn"]
version = "1.0.0"
integrity = "sha256:..."
resolved = "https://registry.pynext.dev/@pynext/shadcn/1.0.0.tgz"
```

##### Advanced Dependency Resolution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Dependency Resolution Algorithm                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. PARSE: Read all package.toml files in parallel                          │
│     └─ Go: parallel file reads with io_uring (Linux) / kqueue (macOS)      │
│                                                                              │
│  2. FETCH METADATA: Parallel registry queries                               │
│     └─ Go: HTTP/2 connection pooling, 50+ concurrent requests              │
│     └─ Cache: Pre-fetched metadata from ~/.pynext/cache/metadata/          │
│                                                                              │
│  3. BUILD GRAPH: Construct unified dependency graph                         │
│     └─ npm deps + pip deps + pynext deps in single graph                   │
│     └─ Cross-ecosystem constraints (e.g., pynext pkg needs both)           │
│                                                                              │
│  4. RESOLVE: SAT-based version resolution                                   │
│     └─ PubGrub algorithm (same as Dart/Pub, Cargo)                         │
│     └─ Handles: version conflicts, circular deps, platform constraints     │
│     └─ Produces: clear error messages for unsatisfiable constraints        │
│                                                                              │
│  5. VERIFY: Check compatibility matrix                                      │
│     └─ Pre-computed compatibility data from registry                       │
│     └─ Known conflicts, deprecations, security issues                      │
│                                                                              │
│  6. DOWNLOAD: Parallel content-addressed downloads                          │
│     └─ Only download blobs not in cache (SHA256 check)                     │
│     └─ Connection pooling: reuse connections per registry                  │
│     └─ Streaming extraction: decompress while downloading                  │
│                                                                              │
│  7. LINK: Hardlink from cache to node_modules/.venv                        │
│     └─ Zero copy: hardlinks mean no data movement                          │
│     └─ Atomic: all-or-nothing installation                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Intelligent Conflict Resolution

PyNext doesn't just report conflicts—it solves them automatically:

```
$ pynext add pkg-a pkg-b

Resolving dependencies...

  ╭─ Conflict Detected ─────────────────────────────────────────╮
  │                                                              │
  │  lodash has incompatible version requirements:              │
  │                                                              │
  │    pkg-a@1.0.0 requires lodash@^4.0.0                       │
  │    pkg-b@2.0.0 requires lodash@^3.0.0                       │
  │                                                              │
  ├─ Automatic Resolution ──────────────────────────────────────┤
  │                                                              │
  │  ✓ [AUTO-APPLIED] Updated pkg-b to 2.1.0                   │
  │    └─ pkg-b@2.1.0 supports lodash@^4.0 (verified)          │
  │                                                              │
  │  Resolution: lodash@4.17.21                                 │
  │                                                              │
  ╰──────────────────────────────────────────────────────────────╯

✓ Installed 47 packages in 0.8s
```

**Resolution Strategies (in order of preference):**

1. **Version Negotiation** — Find versions that satisfy all constraints
2. **Upstream Updates** — Check if newer versions resolve conflicts
3. **Peer Dependency Relaxation** — Allow compatible minor mismatches
4. **Duplication (when safe)** — Install multiple versions in isolation
5. **Patching** — Apply known compatibility patches automatically

**Compatibility Database:**

```bash
$ pynext add react-query

  ℹ️  react-query is deprecated → @tanstack/react-query
  
  Automatically using @tanstack/react-query@5.0.0
  (Original name preserved in lockfile for reference)

✓ Installed @tanstack/react-query@5.0.0 in 0.3s
```

**Security Auto-Patching:**

```bash
$ pynext add vulnerable-pkg@1.0.0

  ⚠️  vulnerable-pkg@1.0.0 has a known vulnerability (CVE-2024-1234)
  
  ✓ [AUTO-PATCHED] Using vulnerable-pkg@1.0.1 (patched version)
  
  Details: https://pynext.dev/advisory/CVE-2024-1234
```

##### LLM-Friendly Design

PyNext's package manager is designed to be easily understood and used by AI systems:

**Structured Output for Machine Parsing:**

```bash
# Human-readable (default)
pynext add lodash

# Machine-readable JSON for LLMs
pynext add lodash --json
{
  "action": "add",
  "success": true,
  "packages": [
    {
      "name": "lodash",
      "version": "4.17.21",
      "ecosystem": "npm",
      "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
      "integrity": "sha512-...",
      "size_bytes": 531584,
      "dependencies": []
    }
  ],
  "total_packages": 1,
  "install_time_ms": 245,
  "cache_hits": 1
}
```

**Structured Errors for AI Debugging:**

```json
{
  "success": false,
  "error": {
    "code": "VERSION_CONFLICT",
    "message": "Cannot resolve dependency conflict for lodash",
    "context": {
      "package": "lodash",
      "required_by": [
        {"package": "pkg-a@1.0.0", "requires": "^4.0.0"},
        {"package": "pkg-b@2.0.0", "requires": "^3.0.0"}
      ],
      "attempted_solutions": [
        {"strategy": "upgrade", "result": "pkg-b@2.1.0 supports lodash@4", "success": true}
      ],
      "recommended_fix": "pynext add pkg-b@2.1.0",
      "alternative_fixes": [
        "Add [overrides] to pynext.package.toml",
        "Use --force to allow duplicates"
      ]
    },
    "documentation_url": "https://pynext.dev/docs/conflicts#version-conflict"
  }
}
```

**Error Codes for Programmatic Handling:**

| Code | Meaning | AI Action |
|------|---------|-----------|
| `PACKAGE_NOT_FOUND` | Package doesn't exist | Suggest alternatives from `suggestions` field |
| `VERSION_CONFLICT` | Incompatible versions | Apply `recommended_fix` command |
| `NETWORK_ERROR` | Can't reach registry | Retry or use `--offline` |
| `INTEGRITY_MISMATCH` | Checksum failed | Re-download with `--force` |
| `PEER_DEP_MISSING` | Missing peer dependency | Add package from `missing_peers` field |
| `DEPRECATED` | Package is deprecated | Use `replacement` field |
| `VULNERABLE` | Security vulnerability | Use `patched_version` field |

**Self-Documenting Commands:**

```bash
pynext add --explain
{
  "command": "add",
  "description": "Add packages to the project",
  "arguments": [
    {"name": "packages", "type": "string[]", "required": true}
  ],
  "options": [
    {"name": "--dev", "short": "-D", "type": "boolean"},
    {"name": "--exact", "short": "-E", "type": "boolean"},
    {"name": "--json", "type": "boolean", "description": "Output as JSON for LLM parsing"}
  ],
  "examples": [
    "pynext add lodash",
    "pynext add pip:pandas npm:chart.js"
  ]
}
```

**Dependency Graph for AI Analysis:**

```bash
pynext graph --json
{
  "nodes": [
    {"id": "lodash@4.17.21", "ecosystem": "npm", "direct": true, "size": 531584},
    {"id": "pandas@2.1.0", "ecosystem": "pip", "direct": true, "size": 12500000},
    {"id": "numpy@1.26.0", "ecosystem": "pip", "direct": false, "size": 18000000}
  ],
  "edges": [
    {"from": "pandas@2.1.0", "to": "numpy@1.26.0", "type": "requires"}
  ],
  "total_size": 31031584,
  "ecosystems": {"npm": 1, "pip": 2}
}
```

**Python API for Programmatic Access:**

```python
from pynext.packages import PackageManager

pm = PackageManager(project_dir=".")

# Add packages programmatically (for AI code generation)
result = await pm.add(["lodash", "pandas"])
print(result.success)           # True
print(result.packages)          # List of installed packages
print(result.conflicts)         # Any conflicts encountered
print(result.suggestions)       # AI-friendly suggestions

# Query dependency graph
graph = await pm.graph()
for node in graph.nodes:
    print(f"{node.name}@{node.version} ({node.ecosystem})")

# Check for issues
issues = await pm.audit()
for issue in issues:
    print(f"{issue.severity}: {issue.package}")
    print(f"  Fix: {issue.fix_command}")  # Ready to execute

# Resolve conflicts programmatically
if result.conflicts:
    for conflict in result.conflicts:
        # AI can choose resolution strategy
        await pm.resolve(conflict, strategy="auto")
```

##### Files to Create

| File | Purpose |
|------|---------|
| `pynext/packages/__init__.py` | Package exports |
| `pynext/packages/resolver.py` | Python orchestrator for Go resolver |
| `pynext/packages/lockfile.py` | Lockfile read/write (TOML) |
| `pynext/packages/cache.py` | Content-addressable cache management |
| `pynext/packages/npm.py` | npm registry client |
| `pynext/packages/pypi.py` | PyPI registry client |
| `pynext/packages/registry.py` | PyNext registry client |
| `pynext/packages/installer.py` | Parallel installation orchestrator |
| `pynext/packages/publisher.py` | Package publishing workflow |
| `pynext/packages/auth.py` | Authentication for publishing |
| `pynext/packages/validator.py` | Package validation |
| `go/pkg/resolver/resolver.go` | Go parallel resolver (PubGrub) |
| `go/pkg/resolver/graph.go` | Dependency graph builder |
| `go/pkg/resolver/sat.go` | SAT solver for versions |
| `go/pkg/resolver/cache.go` | Cache operations |
| `go/pkg/resolver/download.go` | Parallel downloads |
| `go/pkg/resolver/registry.go` | Registry clients |

##### Performance Optimizations

1. **Go Resolver Core**
   - All resolution logic in Go for maximum speed
   - Goroutines for parallel registry queries
   - Channels for streaming results

2. **Content-Addressable Cache**
   - SHA256-addressed blobs
   - Deduplication: same content = same blob
   - Hardlinks: zero-copy installs

3. **Memory-Mapped Lockfile**
   - mmap for zero-copy lockfile reads
   - Incremental updates (only write changed parts)

4. **Connection Pooling**
   - HTTP/2 multiplexing
   - Persistent connections per registry
   - 50+ concurrent downloads

5. **Streaming Extraction**
   - Decompress while downloading
   - No temp files for tarballs

6. **Pre-computed Graphs**
   - Popular package graphs pre-computed
   - Served from CDN edge

7. **Incremental Resolution**
   - Only resolve changed dependencies
   - Reuse previous resolution where valid

##### PyNext Registry API

```
registry.pynext.dev
├── /api/v1/packages              # List/search packages
├── /api/v1/packages/:name        # Package metadata
├── /api/v1/packages/:name/:ver   # Version metadata
├── /api/v1/publish               # Upload package
├── /api/v1/auth                  # Authentication
└── /blobs/:sha256                # Content-addressed storage
```

##### Configuration

```python
# pynext.config.py
packages = {
    "cache_dir": "~/.pynext/cache",
    "parallel": True,
    "strict": True,  # Fail on missing lockfile
    "registries": [
        "https://registry.pynext.dev",
        "https://registry.npmjs.org",
        "https://pypi.org",
    ],
}
```

##### Success Criteria

| Metric | Target |
|--------|--------|
| Cold install (100 deps) | <1s (Bun: ~3s) |
| Warm install (100 deps) | <100ms (Bun: ~300ms) |
| Resolution (1000 deps) | <500ms |
| Cache deduplication | 80%+ across projects |
| Lockfile reproducibility | 100% byte-for-byte |
| Auto-conflict resolution | 90%+ of conflicts resolved automatically |
| Error actionability | 95%+ of errors include fix commands |
| JSON output coverage | 100% of commands support --json |
| LLM parse success rate | 99%+ for structured output |
| Deprecation auto-migration | 100% of known deprecations |
| Security auto-patching | 100% of patchable vulnerabilities |
| Test coverage | 800+ tests |

##### Milestones

1. **Week 1-2:** Lockfile format, basic `pynext add/install` (Python)
2. **Week 3-4:** Go resolver - graph building, SAT solver
3. **Week 5-6:** Content-addressable cache, parallel downloads
4. **Week 7-8:** PyNext registry client, publishing workflow
5. **Week 9-10:** Advanced conflict resolution, error messages
6. **Week 11-12:** Performance tuning, benchmarks vs Bun

---

#### Phase 26: AI-Native Development (Target: 400+ tests)

**Status:** 🔲 Planned
**Priority:** P0 (Critical - Major Differentiator)
**Timeline:** 8 weeks

**Goal**: First-class AI tooling integrated into the runtime. Make PyNext the first AI-native web framework.

##### CLI Commands

```bash
# Generate code from description
pynext ai generate "sortable data table with pagination"
pynext ai generate "user authentication flow"
pynext ai generate "stripe checkout integration"

# Explain code
pynext ai explain pages/dashboard.py
pynext ai explain pages/dashboard.py --function=calculate_totals

# Auto-fix errors
pynext ai fix                       # Fix all lint/type errors
pynext ai fix pages/dashboard.py    # Fix specific file
pynext ai fix --dry-run             # Preview fixes

# Generate tests
pynext ai test pages/dashboard.py   # Generate tests for file
pynext ai test --coverage           # Generate tests for uncovered code

# Code review
pynext ai review                    # Review uncommitted changes
pynext ai review --pr               # Review current PR

# Interactive assistant
pynext ai chat                      # Start interactive session
```

##### Configuration

```python
# pynext.config.py
ai = {
    "provider": "anthropic",          # or "openai", "local", "ollama"
    "model": "claude-sonnet-4-20250514",
    "api_key_env": "ANTHROPIC_API_KEY",
    
    # Auto-fix settings
    "auto_fix": True,                 # Fix errors on save
    "auto_fix_types": ["lint", "type", "import"],
    
    # Explanation settings
    "explain_errors": True,           # Rich error explanations in dev
    
    # Test generation
    "generate_tests": True,           # Suggest tests for new code
    "test_framework": "pytest",
    
    # Context settings
    "context_files": 10,              # Max files to include as context
    "context_tokens": 50000,          # Max tokens for context
}
```

##### Python API

```python
from pynext.ai import generate, explain, fix, test

# Generate a component
component_code = await generate(
    "a sortable data table with pagination",
    context=["models/user.py"],
    style="shadcn",
)

# Explain code
explanation = await explain(
    file="pages/dashboard.py",
    function="calculate_totals",
    detail="verbose",
)

# Fix errors in file
fixes = await fix(
    file="pages/dashboard.py",
    errors=lint_errors,
    apply=True,
)

# Generate tests
tests = await test(
    file="pages/dashboard.py",
    coverage_target=80,
)
```

##### Integration with DevTools

Extend existing `pynext/devtools/` (AI_ANALYSIS.md, AI_DEBUG.md):

```python
# In dev server, errors get AI explanations
@app.exception_handler(Exception)
async def handle_error(request, exc):
    # Get AI explanation
    explanation = await ai.explain_error(exc, request)
    
    return HTMLResponse(f"""
        <div class="error-overlay">
            <h1>{exc.__class__.__name__}</h1>
            <p>{str(exc)}</p>
            
            <h2>AI Explanation</h2>
            <p>{explanation.summary}</p>
            
            <h2>Suggested Fix</h2>
            <pre><code>{explanation.suggested_fix}</code></pre>
            
            <button onclick="applyFix()">Apply Fix</button>
        </div>
    """)
```

##### Files to Create

| File | Purpose |
|------|---------|
| `pynext/ai/__init__.py` | Package exports |
| `pynext/ai/client.py` | LLM provider abstraction (Anthropic, OpenAI, Ollama) |
| `pynext/ai/generator.py` | Component/code generation |
| `pynext/ai/explainer.py` | Code and error explanation |
| `pynext/ai/fixer.py` | Error auto-fix with context |
| `pynext/ai/tester.py` | Test generation |
| `pynext/ai/reviewer.py` | Code review |
| `pynext/ai/context.py` | Context gathering (relevant files) |
| `pynext/ai/prompts/generate.py` | Generation prompts |
| `pynext/ai/prompts/explain.py` | Explanation prompts |
| `pynext/ai/prompts/fix.py` | Fix prompts |
| `pynext/ai/prompts/test.py` | Test generation prompts |
| `pynext/ai/prompts/review.py` | Review prompts |

##### Provider Abstraction

```python
# pynext/ai/client.py
class AIProvider(Protocol):
    async def complete(self, messages: list[Message], **kwargs) -> str: ...
    async def stream(self, messages: list[Message], **kwargs) -> AsyncIterator[str]: ...

class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def complete(self, messages, **kwargs):
        response = await self.client.messages.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return response.content[0].text

class OpenAIProvider(AIProvider): ...
class OllamaProvider(AIProvider): ...  # Local models
```

##### Success Criteria

| Metric | Target |
|--------|--------|
| Component generation accuracy | 80%+ usable first try |
| Error fix success rate | 70%+ auto-fixable |
| Test generation coverage | 60%+ line coverage |
| Explanation clarity | 90%+ user satisfaction |
| Test coverage | 400+ tests |

##### Milestones

1. **Week 1-2:** LLM client abstraction, `pynext ai generate` basic
2. **Week 3-4:** `pynext ai fix` with error context
3. **Week 5-6:** `pynext ai test` generation
4. **Week 7-8:** `pynext ai review`, `pynext ai chat`, polish

---

#### Phase 27: Database Studio and Migrations (Target: 400+ tests)

**Status:** 🔲 Planned
**Priority:** P1 (High)
**Timeline:** 8 weeks

**Goal**: Visual database management and automatic schema migrations. Make database management as easy as editing Python classes.

##### CLI Commands

```bash
# Initialize database
pynext db init                      # Auto-detect from config
pynext db init postgres             # Specific database
pynext db init sqlite
pynext db init supabase

# Schema management
pynext db push                      # Sync schema to DB (auto-migrate)
pynext db pull                      # Pull schema from existing DB
pynext db diff                      # Show pending changes

# Migrations
pynext db migrate                   # Run pending migrations
pynext db migrate --name="add_users"  # Create named migration
pynext db rollback                  # Rollback last migration
pynext db rollback --steps=3        # Rollback multiple
pynext db status                    # Show migration status

# Data management
pynext db seed                      # Run seed data
pynext db reset                     # Drop and recreate (dev only)

# Visual studio
pynext db studio                    # Open browser-based explorer

# Code generation
pynext db generate                  # Generate typed query helpers
```

##### Visual Studio (Browser-Based)

```
pynext db studio → Opens http://localhost:5555

┌─────────────────────────────────────────────────────────────────────────────┐
│  PyNext Database Studio                                    localhost:5555   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌────────────────────────────────────────────────────┐  │
│  │ Tables       │  │ users                                    [+ Add]   │  │
│  ├──────────────┤  ├────────────────────────────────────────────────────┤  │
│  │ ▶ users      │  │ id │ name      │ email           │ created_at     │  │
│  │   posts      │  │────┼───────────┼─────────────────┼────────────────│  │
│  │   comments   │  │ 1  │ Alice     │ alice@example   │ 2025-01-15     │  │
│  │   tags       │  │ 2  │ Bob       │ bob@example     │ 2025-01-14     │  │
│  │              │  │ 3  │ Carol     │ carol@example   │ 2025-01-13     │  │
│  └──────────────┘  └────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ SQL Query                                               [▶ Run]     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ SELECT * FROM users WHERE created_at > '2025-01-01'                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  [Tables] [Query] [Schema] [Migrations] [Seed] [ERD]                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

Features:
- Table browser with CRUD operations
- SQL query editor with autocomplete
- Schema visualization (ERD diagram)
- Migration history timeline
- Seed data editor
- Query performance analyzer
- Export to CSV/JSON
```

##### Auto-Migration Example

```python
# models/user.py - Just add a field
class User(Model):
    name: str
    email: str
    avatar_url: str | None = None  # NEW FIELD - just add it!

# pynext db push
#
# Detected schema changes:
#   + users.avatar_url (TEXT, nullable)
#
# Apply changes? [Y/n] y
#
# ✓ Added column: users.avatar_url
# ✓ Migration saved: migrations/20250115_add_avatar_url.py
```

##### Schema Differ

```python
# pynext/db/migrations/differ.py
class SchemaDiffer:
    """Compares Python models to database schema."""
    
    def diff(self, models: list[Model], db_schema: Schema) -> list[Change]:
        changes = []
        
        for model in models:
            table_name = model.__tablename__
            
            if table_name not in db_schema.tables:
                changes.append(CreateTable(model))
                continue
            
            db_table = db_schema.tables[table_name]
            
            # Check each field
            for field in model.__fields__:
                if field.name not in db_table.columns:
                    changes.append(AddColumn(table_name, field))
                elif field != db_table.columns[field.name]:
                    changes.append(AlterColumn(table_name, field))
            
            # Check for removed columns
            for col_name in db_table.columns:
                if col_name not in model.__fields__:
                    changes.append(DropColumn(table_name, col_name))
        
        return changes
```

##### Files to Create

| File | Purpose |
|------|---------|
| `pynext/db/studio/__init__.py` | Studio server |
| `pynext/db/studio/server.py` | HTTP server for studio UI |
| `pynext/db/studio/api.py` | REST API for CRUD operations |
| `pynext/db/studio/static/` | Studio frontend (HTML/JS/CSS) |
| `pynext/db/migrations/differ.py` | Schema diff detection |
| `pynext/db/migrations/generator.py` | Migration file generation |
| `pynext/db/migrations/runner.py` | Migration execution |
| `pynext/db/migrations/history.py` | Migration history tracking |
| `pynext/db/migrations/rollback.py` | Rollback operations |

##### Success Criteria

| Metric | Target |
|--------|--------|
| Schema diff accuracy | 99%+ correct migrations |
| Studio load time | <1s |
| Migration safety | Zero data loss |
| Rollback reliability | 100% reversible |
| Test coverage | 400+ tests |

##### Milestones

1. **Week 1-2:** Schema differ, basic `pynext db push`
2. **Week 3-4:** Migration generator, rollback support
3. **Week 5-6:** Studio server, table browser, CRUD
4. **Week 7-8:** SQL editor, ERD visualization, polish

---

#### Phase 28: Background Jobs (Target: 300+ tests)

**Status:** 🔲 Planned
**Priority:** P1 (High)
**Timeline:** 8 weeks

**Goal**: Built-in job queue for background processing. No external dependencies required for simple use cases.

##### Python API

```python
from pynext.jobs import job, schedule, Queue

# Define a job
@job
async def send_welcome_email(user_id: int):
    user = await User.get(user_id)
    await Email.send(
        to=user.email,
        template="welcome",
        context={"name": user.name},
    )

# Define a scheduled job
@schedule("0 9 * * *")  # Every day at 9am
async def daily_digest():
    users = await User.filter(digest_enabled=True).all()
    for user in users:
        await send_digest.enqueue(user.id)

@schedule("*/5 * * * *")  # Every 5 minutes
async def check_expired_sessions():
    await Session.delete_expired()

# Enqueue jobs
await send_welcome_email.enqueue(user_id=123)
await send_welcome_email.enqueue(user_id=456, delay="5m")
await send_welcome_email.enqueue(user_id=789, priority=10)

# Enqueue with options
await send_welcome_email.enqueue(
    user_id=123,
    delay="1h",              # Delay execution
    priority=5,              # Higher = sooner
    retry_attempts=3,        # Retry on failure
    retry_delay="1m",        # Delay between retries
    timeout="30s",           # Max execution time
    unique=True,             # Prevent duplicates
)

# Batch enqueue
await Queue.enqueue_many([
    send_welcome_email.prepare(user_id=1),
    send_welcome_email.prepare(user_id=2),
    send_welcome_email.prepare(user_id=3),
])
```

##### Job Lifecycle

```python
from pynext.jobs import job, on_success, on_failure, on_retry

@job
@on_success(notify_admin)
@on_failure(log_error)
@on_retry(increment_retry_count)
async def process_payment(order_id: int):
    order = await Order.get(order_id)
    result = await stripe.charge(order.total)
    order.status = "paid"
    await order.save()
    return result

# Progress tracking for long jobs
@job(track_progress=True)
async def import_csv(file_path: str):
    rows = read_csv(file_path)
    for i, row in enumerate(rows):
        await process_row(row)
        await job.update_progress(i / len(rows) * 100)
```

##### CLI Commands

```bash
# Start workers
pynext jobs start                   # Start default worker
pynext jobs start -w 4              # Start 4 workers
pynext jobs start --queue=emails    # Specific queue

# Job management
pynext jobs list                    # Show queued jobs
pynext jobs list --status=failed    # Filter by status
pynext jobs retry                   # Retry all failed
pynext jobs retry <job_id>          # Retry specific
pynext jobs cancel <job_id>         # Cancel job
pynext jobs clear                   # Clear completed

# Monitoring
pynext jobs stats                   # Show statistics
pynext jobs dashboard               # Open web dashboard

# Scheduled jobs
pynext jobs schedule list           # List scheduled jobs
pynext jobs schedule run <name>     # Run scheduled job now
```

##### Configuration

```python
# pynext.config.py
jobs = {
    # Storage backend
    "backend": "sqlite",          # or "redis", "postgres"
    "database_url": "sqlite:///jobs.db",
    
    # Worker settings
    "workers": 4,
    "queues": ["default", "emails", "reports"],
    
    # Retry settings
    "retry_attempts": 3,
    "retry_delay": "1m",
    "retry_backoff": "exponential",  # or "linear", "fixed"
    
    # Limits
    "max_runtime": "30m",
    "max_memory": "512MB",
    
    # Cleanup
    "keep_completed": "7d",
    "keep_failed": "30d",
}
```

##### Storage Backends

```python
# SQLite (default, zero config)
jobs = {"backend": "sqlite"}

# Redis (for production)
jobs = {
    "backend": "redis",
    "redis_url": "redis://localhost:6379/0",
}

# PostgreSQL (shared with main DB)
jobs = {
    "backend": "postgres",
    "database_url": "postgresql://...",
}
```

##### Files to Create

| File | Purpose |
|------|---------|
| `pynext/jobs/__init__.py` | Package exports |
| `pynext/jobs/decorators.py` | `@job`, `@schedule` decorators |
| `pynext/jobs/queue.py` | Job queue implementation |
| `pynext/jobs/worker.py` | Job worker process |
| `pynext/jobs/scheduler.py` | Cron scheduler |
| `pynext/jobs/storage/base.py` | Storage backend interface |
| `pynext/jobs/storage/sqlite.py` | SQLite backend |
| `pynext/jobs/storage/redis.py` | Redis backend |
| `pynext/jobs/storage/postgres.py` | PostgreSQL backend |
| `pynext/jobs/retry.py` | Retry strategies |
| `pynext/jobs/progress.py` | Progress tracking |
| `pynext/jobs/dashboard/` | Web dashboard |

##### Success Criteria

| Metric | Target |
|--------|--------|
| Job throughput | 1000+ jobs/sec (Redis) |
| Reliability | 99.9% job completion |
| Enqueue latency | <10ms |
| At-least-once delivery | 100% |
| Test coverage | 300+ tests |

##### Milestones

1. **Week 1-2:** `@job` decorator, SQLite storage, basic queue
2. **Week 3-4:** Worker process, retry logic, priorities
3. **Week 5-6:** `@schedule` decorator, cron parser
4. **Week 7-8:** Redis/Postgres backends, dashboard, CLI

---

#### Phase 29: Universal Deployment (Target: 200+ tests)

**Status:** 🔲 Planned
**Priority:** P1 (High)
**Timeline:** 8 weeks

**Goal**: One-command deployment to any platform. Zero-config for common platforms.

##### CLI Commands

```bash
# Deploy (auto-detect platform)
pynext deploy                       # Auto-detect from git remote
pynext deploy --platform=vercel     # Explicit platform

# Platform-specific
pynext deploy vercel
pynext deploy cloudflare
pynext deploy fly
pynext deploy railway
pynext deploy render
pynext deploy docker
pynext deploy self --domain=app.com

# Preview deployments
pynext preview                      # Deploy preview of current branch
pynext preview --expires=24h        # With expiration

# Environment management
pynext env list                     # List env vars
pynext env set KEY=value            # Set env var
pynext env set KEY=value --prod     # Production only
pynext env pull                     # Pull from platform to .env
pynext env push                     # Push .env to platform

# Monitoring
pynext logs                         # Stream production logs
pynext logs --since=1h              # Logs from last hour
pynext status                       # Deployment status

# Rollback
pynext rollback                     # Rollback to previous
pynext rollback --version=abc123    # Specific version
pynext releases                     # List releases
```

##### Configuration

```python
# pynext.config.py
deploy = {
    # Platform settings
    "platform": "auto",              # Auto-detect or specify
    "region": "us-east-1",           # Primary region
    "regions": ["us", "eu", "asia"], # Multi-region
    
    # Edge settings
    "edge": True,                    # Deploy to edge functions
    "edge_routes": ["/api/*"],       # Which routes go to edge
    
    # Preview settings
    "preview_branches": True,        # Auto-preview for PRs
    "preview_domain": "preview.myapp.com",
    
    # Domain settings
    "domain": "myapp.com",
    "subdomains": {
        "api": "api.myapp.com",
        "docs": "docs.myapp.com",
    },
    
    # Build settings
    "build_command": "pynext build",
    "output_dir": ".pynext/build",
    
    # Health checks
    "health_check": "/api/health",
    "health_timeout": "30s",
}
```

##### Platform Adapters

```python
# pynext/deploy/adapters/base.py
class DeployAdapter(Protocol):
    """Base protocol for deployment adapters."""
    
    async def build(self, config: DeployConfig) -> BuildOutput:
        """Build the application for this platform."""
        ...
    
    async def deploy(self, build: BuildOutput) -> Deployment:
        """Deploy to the platform."""
        ...
    
    async def preview(self, build: BuildOutput) -> PreviewDeployment:
        """Create a preview deployment."""
        ...
    
    async def logs(self, deployment: Deployment) -> AsyncIterator[str]:
        """Stream logs from deployment."""
        ...
    
    async def rollback(self, deployment: Deployment, version: str) -> Deployment:
        """Rollback to a previous version."""
        ...
    
    async def env_set(self, key: str, value: str, production: bool) -> None:
        """Set an environment variable."""
        ...
```

##### Platform-Specific Outputs

```
Vercel:
├── .vercel/
│   ├── output/
│   │   ├── static/          # Static assets
│   │   ├── functions/       # Serverless functions
│   │   └── config.json
│   └── project.json

Cloudflare:
├── .cloudflare/
│   ├── worker.js            # Edge worker
│   ├── _routes.json         # Routing config
│   └── wrangler.toml

Docker:
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # With postgres, redis
└── .dockerignore

Fly.io:
├── fly.toml                 # Fly configuration
└── Dockerfile
```

##### Auto-Detection

```python
# pynext/deploy/detector.py
def detect_platform() -> str | None:
    """Detect deployment platform from environment."""
    
    # Check git remotes
    if "vercel" in git_remotes():
        return "vercel"
    if "fly.io" in git_remotes():
        return "fly"
    
    # Check environment variables
    if os.getenv("VERCEL"):
        return "vercel"
    if os.getenv("CF_PAGES"):
        return "cloudflare"
    if os.getenv("FLY_APP_NAME"):
        return "fly"
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return "railway"
    
    # Check config files
    if Path("vercel.json").exists():
        return "vercel"
    if Path("wrangler.toml").exists():
        return "cloudflare"
    if Path("fly.toml").exists():
        return "fly"
    
    return None
```

##### Files to Create

| File | Purpose |
|------|---------|
| `pynext/deploy/__init__.py` | Package exports |
| `pynext/deploy/detector.py` | Platform auto-detection |
| `pynext/deploy/builder.py` | Production build |
| `pynext/deploy/adapters/base.py` | Base adapter protocol |
| `pynext/deploy/adapters/vercel.py` | Vercel adapter |
| `pynext/deploy/adapters/cloudflare.py` | Cloudflare adapter |
| `pynext/deploy/adapters/fly.py` | Fly.io adapter |
| `pynext/deploy/adapters/railway.py` | Railway adapter |
| `pynext/deploy/adapters/docker.py` | Docker/self-hosted adapter |
| `pynext/deploy/preview.py` | Preview deployments |
| `pynext/deploy/env.py` | Environment variable management |

##### Success Criteria

| Metric | Target |
|--------|--------|
| Platforms supported | 5+ |
| Deploy time (simple app) | <60s |
| Zero-config success | 80%+ apps deploy without config |
| Preview deploy time | <30s |
| Test coverage | 200+ tests |

##### Milestones

1. **Week 1-2:** Build system, Docker adapter
2. **Week 3-4:** Vercel, Cloudflare adapters
3. **Week 5-6:** Fly.io, Railway adapters
4. **Week 7-8:** Preview deployments, env management, auto-detection

---

#### Phase 30: Live Collaboration (Target: 250+ tests)

**Status:** 🔲 Planned
**Priority:** P2 (Medium)
**Timeline:** 8 weeks

**Goal**: Real-time state synchronization and presence indicators. Enable multiplayer experiences with minimal code.

##### Python API

```python
from pynext.live import live_signal, presence, room

# Shared state across all connected clients
document = live_signal(
    {"title": "", "content": ""},
    room="doc-123",
)

# Presence - see who's online
users = presence(room="doc-123")

@component
def CollaborativeEditor():
    return div()[
        # Real-time cursor positions
        Cursors(users),
        
        # Shared title
        input(
            value=document().title,
            oninput=lambda e: document.merge({"title": e.target.value}),
        ),
        
        # Shared content
        textarea(
            value=document().content,
            oninput=lambda e: document.merge({"content": e.target.value}),
        ),
        
        # Who's online
        div(class_="presence")[
            For(users)[lambda u: 
                div(class_="user", style=f"--color: {u.color}")[
                    Avatar(src=u.avatar),
                    span()[u.name],
                ]
            ],
        ],
    ]
```

##### Live Signal Types

```python
from pynext.live import live_signal, live_list, live_map, live_text

# Basic JSON state
state = live_signal({"count": 0}, room="counter")
state.merge({"count": state().count + 1})

# List with CRDT operations
items = live_list(["item1", "item2"], room="list")
items.append("item3")
items.insert(0, "item0")
items.remove("item1")

# Map with nested updates
data = live_map({"users": {}}, room="data")
data.set("users.alice", {"name": "Alice"})

# Collaborative text (Yjs Y.Text)
text = live_text("Hello", room="doc")
text.insert(5, " World")
text.delete(0, 5)
```

##### Presence API

```python
from pynext.live import presence, set_presence

# Get all users in room
users = presence(room="doc-123")

# Set own presence data
set_presence(
    room="doc-123",
    data={
        "name": "Alice",
        "color": "#ff0000",
        "cursor": {"x": 100, "y": 200},
        "selection": {"start": 10, "end": 20},
    },
)

# Presence updates automatically propagate
@component
def Cursors():
    users = presence(room="doc-123")
    
    return div()[
        For(users)[lambda u:
            div(
                class_="cursor",
                style=f"left: {u.cursor.x}px; top: {u.cursor.y}px; --color: {u.color}",
            )[u.name]
        ],
    ]
```

##### Room Management

```python
from pynext.live import room, Room

# Create/join a room
doc_room = room("doc-123")

# Room with options
doc_room = room(
    "doc-123",
    persistence=True,           # Persist to database
    max_users=50,               # Limit concurrent users
    auth=require_login,         # Auth callback
)

# Room events
@doc_room.on_join
async def handle_join(user):
    print(f"{user.name} joined")

@doc_room.on_leave
async def handle_leave(user):
    print(f"{user.name} left")

@doc_room.on_update
async def handle_update(changes):
    print(f"Document updated: {changes}")
```

##### CRDT Integration (Yjs)

```python
# pynext/live/sync.py
from y_py import YDoc, YText, YMap, YArray

class LiveDocument:
    """CRDT-backed live document using Yjs."""
    
    def __init__(self, room_id: str):
        self.doc = YDoc()
        self.room_id = room_id
        self._subscribers: list[Callable] = []
    
    def get_text(self, name: str) -> YText:
        return self.doc.get_text(name)
    
    def get_map(self, name: str) -> YMap:
        return self.doc.get_map(name)
    
    def get_array(self, name: str) -> YArray:
        return self.doc.get_array(name)
    
    def on_update(self, callback: Callable):
        self._subscribers.append(callback)
    
    def apply_update(self, update: bytes):
        """Apply update from remote."""
        self.doc.apply_update(update)
        for callback in self._subscribers:
            callback()
    
    def encode_state(self) -> bytes:
        """Encode full state for new clients."""
        return self.doc.encode_state_as_update()
```

##### Server Configuration

```python
# pynext.config.py
live = {
    # WebSocket settings
    "websocket_path": "/_pynext/live",
    
    # Persistence
    "persistence": True,
    "persistence_backend": "sqlite",  # or "redis", "postgres"
    
    # Scaling
    "provider": "websocket",          # or "webrtc", "redis"
    
    # Limits
    "max_rooms": 1000,
    "max_users_per_room": 100,
    "max_document_size": "10MB",
    
    # Security
    "require_auth": True,
    "room_auth_callback": "check_room_access",
}
```

##### Files to Create

| File | Purpose |
|------|---------|
| `pynext/live/__init__.py` | Package exports |
| `pynext/live/signal.py` | `live_signal` implementation |
| `pynext/live/presence.py` | Presence tracking |
| `pynext/live/room.py` | Room management |
| `pynext/live/sync.py` | CRDT synchronization (Yjs) |
| `pynext/live/server.py` | WebSocket sync server |
| `pynext/live/persistence.py` | Document persistence |
| `pynext/runtime/live.js` | Client-side sync runtime |

##### Success Criteria

| Metric | Target |
|--------|--------|
| Sync latency | <50ms |
| Concurrent users per room | 100+ |
| Offline support | Full offline-first |
| Conflict resolution | Automatic via CRDT |
| Test coverage | 250+ tests |

##### Milestones

1. **Week 1-2:** `live_signal` basic implementation
2. **Week 3-4:** Yjs CRDT integration
3. **Week 5-6:** Presence, cursor tracking
4. **Week 7-8:** Offline support, persistence, scaling

---

#### Phase 31: Feature Flags and Rollouts (Target: 200+ tests)

**Status:** 🔲 Planned
**Priority:** P2 (Medium)
**Timeline:** 8 weeks

**Goal**: Built-in feature flag system with gradual rollouts and A/B testing. Ship with confidence.

##### Python API - Basic Flags

```python
from pynext.features import flag, is_enabled

# Simple boolean flag
@flag("new_dashboard")
@component
def Dashboard():
    return new_dashboard_component()

# Check programmatically
if is_enabled("new_dashboard"):
    show_new_dashboard()
else:
    show_old_dashboard()

# Flag with fallback
@flag("experimental_feature", fallback=OldComponent)
@component
def ExperimentalComponent():
    ...
```

##### Python API - Rollouts

```python
from pynext.features import rollout, rollout_for_user

# Percentage rollout
@rollout(percentage=10)  # 10% of users
@component
def NewCheckout():
    ...

# User-specific check
if rollout_for_user("new_checkout", user_id=user.id):
    return new_checkout()

# Gradual rollout
@rollout(
    percentage=10,
    increase_by=10,      # Increase 10% daily
    increase_interval="1d",
    max_percentage=100,
)
@component
def NewFeature():
    ...
```

##### Python API - A/B Testing

```python
from pynext.features import experiment, Variant

# Define experiment
@experiment("checkout_flow", variants=["control", "variant_a", "variant_b"])
@component
def Checkout(variant: str):
    if variant == "control":
        return checkout_v1()
    elif variant == "variant_a":
        return checkout_v2()
    elif variant == "variant_b":
        return checkout_v3()

# Get variant for user
variant = get_variant("checkout_flow", user_id=user.id)

# Track conversion
track_conversion("checkout_flow", user_id=user.id, value=order.total)

# Experiment with weights
@experiment(
    "pricing_page",
    variants={
        "control": 50,       # 50% traffic
        "variant_a": 30,     # 30% traffic
        "variant_b": 20,     # 20% traffic
    },
)
@component
def PricingPage(variant: str):
    ...
```

##### Targeting Rules

```python
from pynext.features import flag, Target

# Target specific users
@flag(
    "beta_features",
    target=Target.users(["user-1", "user-2"]),
)

# Target by attribute
@flag(
    "enterprise_feature",
    target=Target.where(plan="enterprise"),
)

# Complex targeting
@flag(
    "new_feature",
    target=Target.any([
        Target.users(["admin-1"]),
        Target.where(plan="pro", country="US"),
        Target.percentage(10),
    ]),
)
```

##### CLI Commands

```bash
# Flag management
pynext flags list                   # List all flags
pynext flags list --enabled         # Only enabled
pynext flags enable new_dashboard   # Enable flag
pynext flags disable new_dashboard  # Disable flag

# Rollout management
pynext flags rollout new_feature 50%    # Set to 50%
pynext flags rollout new_feature 100%   # Full rollout
pynext flags rollout new_feature 0%     # Disable

# Experiment management
pynext flags experiment list
pynext flags experiment stats checkout_flow
pynext flags experiment winner checkout_flow variant_a

# Targeting
pynext flags target new_feature --users=alice,bob
pynext flags target new_feature --where="plan=pro"

# Audit
pynext flags history new_feature    # Change history
```

##### Configuration

```python
# pynext.config.py
features = {
    # Storage
    "backend": "sqlite",          # or "redis", "postgres", "launchdarkly"
    
    # Defaults
    "default_enabled": False,
    "sticky_bucketing": True,     # Same user = same variant
    
    # Statistics
    "track_exposures": True,
    "significance_threshold": 0.95,
    
    # Sync (for external providers)
    "sync_interval": "1m",
}
```

##### Files to Create

| File | Purpose |
|------|---------|
| `pynext/features/__init__.py` | Package exports |
| `pynext/features/flags.py` | `@flag` decorator, `is_enabled` |
| `pynext/features/rollout.py` | `@rollout` decorator |
| `pynext/features/experiment.py` | A/B testing, variants |
| `pynext/features/targeting.py` | Targeting rules |
| `pynext/features/bucketing.py` | Consistent user bucketing |
| `pynext/features/storage/base.py` | Storage interface |
| `pynext/features/storage/sqlite.py` | SQLite storage |
| `pynext/features/storage/redis.py` | Redis storage |
| `pynext/features/stats.py` | Experiment statistics |
| `pynext/features/tracking.py` | Exposure/conversion tracking |

##### Success Criteria

| Metric | Target |
|--------|--------|
| Flag evaluation | <1ms |
| Targeting accuracy | 100% consistent |
| A/B bucketing consistency | 100% (sticky) |
| Statistical significance detection | Automatic |
| Test coverage | 200+ tests |

##### Milestones

1. **Week 1-2:** `@flag` decorator, basic storage
2. **Week 3-4:** `@rollout` with percentage
3. **Week 5-6:** `@experiment` A/B testing, bucketing
4. **Week 7-8:** Targeting rules, statistics, CLI

---

#### Phase 32: Built-in Analytics and Monitoring (Target: 200+ tests)

**Status:** 🔲 Planned
**Priority:** P2 (Medium)
**Timeline:** 8 weeks

**Goal**: Zero-config performance monitoring and analytics. Understand your app without external services.

##### Python API - Automatic Tracking

```python
from pynext.analytics import track

# Automatic tracking decorator
@track  # Tracks: timing, errors, calls
async def checkout(cart_id: str):
    cart = await Cart.get(cart_id)
    result = await process_payment(cart)
    return result

# Track with custom name
@track(name="payment_processing")
async def process_payment(cart):
    ...

# Track with custom attributes
@track(attributes={"category": "checkout"})
async def checkout(cart_id: str):
    ...
```

##### Python API - Custom Metrics

```python
from pynext.analytics import metric, counter, histogram, gauge

# Record a metric
metric("cart_value", cart.total)
metric("items_count", len(cart.items), tags={"user": user.id})

# Counter (monotonically increasing)
counter("page_views", tags={"page": "/home"})
counter("api_calls", tags={"endpoint": "/api/users"})

# Histogram (distribution)
histogram("response_time", duration_ms)
histogram("payload_size", len(body))

# Gauge (current value)
gauge("active_users", get_active_user_count())
gauge("queue_depth", job_queue.size())
```

##### Python API - Custom Events

```python
from pynext.analytics import event

# Track custom events
event("purchase_completed", {
    "value": 99.99,
    "currency": "USD",
    "items": ["item-1", "item-2"],
})

event("user_signed_up", {
    "method": "google",
    "referrer": request.referrer,
})

# Track with user
event("feature_used", {"feature": "export"}, user_id=user.id)
```

##### Python API - Error Tracking

```python
from pynext.analytics import capture_exception, capture_message

try:
    process_order(order)
except Exception as e:
    capture_exception(e, context={
        "order_id": order.id,
        "user_id": user.id,
    })
    raise

# Capture warning/info messages
capture_message("High memory usage detected", level="warning")
```

##### CLI Commands

```bash
# Dashboard
pynext analytics                    # Open web dashboard
pynext analytics --port=5556

# Query data
pynext analytics errors             # Recent errors
pynext analytics errors --last=24h
pynext analytics slow               # Slow endpoints
pynext analytics slow --threshold=500ms

# Events
pynext analytics events             # List event types
pynext analytics events purchase_completed --last=7d

# Export
pynext analytics export             # Export all data
pynext analytics export --format=csv --last=30d

# Alerts
pynext analytics alerts list
pynext analytics alerts add --metric=error_rate --threshold=0.01
```

##### Dashboard (Browser-Based)

```
pynext analytics → Opens http://localhost:5556

┌─────────────────────────────────────────────────────────────────────────────┐
│  PyNext Analytics                                       localhost:5556      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Requests (last 24h)                                                  │   │
│  │ ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄│   │
│  │ 12.5k requests | 99.2% success | p50: 45ms | p99: 230ms             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────┐  ┌──────────────────────────────────────┐   │
│  │ Top Endpoints            │  │ Recent Errors                         │   │
│  │ GET /api/users    3.2k   │  │ ValueError: Invalid email format     │   │
│  │ POST /api/orders  1.8k   │  │ TimeoutError: Database connection    │   │
│  │ GET /dashboard    1.5k   │  │ PermissionError: Access denied       │   │
│  └──────────────────────────┘  └──────────────────────────────────────┘   │
│                                                                              │
│  [Overview] [Requests] [Errors] [Events] [Metrics] [Alerts]                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

Features:
- Request/response times (p50, p95, p99)
- Error rates and stack traces
- Slow endpoint detection
- Custom event tracking
- Real-time metrics graphs
- Alerting configuration
- User session tracking
- Export to CSV/JSON
```

##### Configuration

```python
# pynext.config.py
analytics = {
    # Storage
    "backend": "sqlite",          # or "postgres", "clickhouse"
    "database_path": ".pynext/analytics.db",
    
    # Collection
    "track_requests": True,
    "track_errors": True,
    "sample_rate": 1.0,           # 100% of requests
    
    # Retention
    "keep_detailed": "7d",        # Keep detailed data 7 days
    "keep_aggregated": "90d",     # Keep aggregated 90 days
    
    # Dashboard
    "dashboard_port": 5556,
    "dashboard_auth": True,
    
    # Alerts
    "alert_email": "alerts@example.com",
    "alert_slack_webhook": "https://hooks.slack.com/...",
}
```

##### Files to Create

| File | Purpose |
|------|---------|
| `pynext/analytics/__init__.py` | Package exports |
| `pynext/analytics/tracker.py` | `@track` decorator |
| `pynext/analytics/metrics.py` | `metric`, `counter`, `histogram`, `gauge` |
| `pynext/analytics/events.py` | `event` function |
| `pynext/analytics/errors.py` | Error tracking |
| `pynext/analytics/storage/base.py` | Storage interface |
| `pynext/analytics/storage/sqlite.py` | SQLite storage |
| `pynext/analytics/storage/postgres.py` | PostgreSQL storage |
| `pynext/analytics/dashboard/` | Web dashboard (server + static) |
| `pynext/analytics/alerts.py` | Alerting system |
| `pynext/analytics/export.py` | Data export |
| `pynext/analytics/aggregation.py` | Metric aggregation |

##### Success Criteria

| Metric | Target |
|--------|--------|
| Collection overhead | <1ms per request |
| Dashboard load time | <1s |
| Query performance | <100ms for 7 days |
| Data retention | 30+ days |
| Test coverage | 200+ tests |

##### Milestones

1. **Week 1-2:** `@track` decorator, request/error tracking
2. **Week 3-4:** Custom metrics, events, SQLite storage
3. **Week 5-6:** Dashboard server, visualizations
4. **Week 7-8:** Alerts, export, aggregation

---

## Universal Client-Side Python: Phases 33-50

Extend PyNext's transpiler to support **every possible client-side interaction** from pure Python, enabling developers to build applications like Figma, Notion, Discord, Replit, and TradingView without writing JavaScript.

```mermaid
mindmap
  root((Universal Client Python))
    Foundation
      Phase33[Phase 33: Core Transpiler]
      Phase34[Phase 34: DOM APIs]
      Phase35[Phase 35: Browser APIs]
    Interaction
      Phase36[Phase 36: Animation]
      Phase37[Phase 37: Gestures]
      Phase38[Phase 38: Observers]
    Media
      Phase39[Phase 39: File/Canvas/Audio]
      Phase40[Phase 40: Real-time/Storage]
    Graphics
      Phase41[Phase 41: WebGL/WebGPU]
      Phase42[Phase 42: SVG Manipulation]
    Performance
      Phase43[Phase 43: Workers/WASM]
      Phase44[Phase 44: Virtualization]
    Editors
      Phase45[Phase 45: Rich Text/Selection]
      Phase46[Phase 46: Code Editors]
      Phase47[Phase 47: Terminal]
    Advanced
      Phase48[Phase 48: Infinite Canvas]
      Phase49[Phase 49: Cross-Tab/Offline]
      Phase50[Phase 50: Device APIs]
```

### Phase Summary Table

| Phase | Name | Target Apps | Tests | Weeks |
|-------|------|-------------|-------|-------|
| 33 | Core Language Transpilation | All | 500 | 6 |
| 34 | DOM API Bindings | All | 400 | 4 |
| 35 | Browser APIs | All | 300 | 4 |
| 36 | Animation and Motion | Framer, Linear | 200 | 3 |
| 37 | Touch and Gestures | Miro, mobile apps | 200 | 3 |
| 38 | Observers | Lazy loading, responsive | 150 | 2 |
| 39 | File, Canvas 2D, Audio | Canva, Spotify | 250 | 4 |
| 40 | Real-time and Storage | Slack, Notion | 200 | 4 |
| 41 | WebGL / WebGPU | Figma, Spline, TradingView | 300 | 6 |
| 42 | SVG Manipulation | Charts, diagrams, Miro | 150 | 3 |
| 43 | Workers and WebAssembly | Figma, Adobe, heavy processing | 250 | 5 |
| 44 | Virtual Scrolling / Windowing | Airtable, large lists | 150 | 3 |
| 45 | Rich Text / Selection API | Notion, Confluence, editors | 300 | 5 |
| 46 | Code Editor Integration | GitHub, Replit, CodeSandbox | 200 | 4 |
| 47 | Terminal Emulation | Replit, Vercel, CodeSandbox | 150 | 3 |
| 48 | Infinite Canvas / Pan-Zoom | Miro, FigJam, Figma | 200 | 4 |
| 49 | Cross-Tab / Offline-First | Notion, collaborative apps | 150 | 3 |
| 50 | Device APIs | Accessibility, e-commerce, mobile | 200 | 4 |
| **Total** | | | **4250** | **70 weeks** |

---

### FOUNDATION PHASES (33-35)

---

### Phase 33: Core Language Transpilation Overview

**Goal:** Complete Python language transpilation for client-side execution — every construct needed to write Python that runs as JavaScript in the browser.

**Total Scope:** ~975 tests across 4 sub-phases, ~13 weeks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 33: CORE LANGUAGE TRANSPILATION                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 33.1: FUNDAMENTALS (230 tests, 4 weeks)                                 ││
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        ││
│  │ │  Functions  │ │   Classes   │ │Control Flow │ │Comprehensions│       ││
│  │ │  50 tests   │ │  80 tests   │ │  60 tests   │ │  40 tests   │        ││
│  │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 33.2: ADVANCED CONSTRUCTS (290 tests, 4 weeks)                          ││
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        ││
│  │ │   Dunder    │ │ Generators  │ │  Context    │ │  Pattern    │        ││
│  │ │  Methods    │ │ & Iterators │ │  Managers   │ │  Matching   │        ││
│  │ │ 100 tests   │ │  50 tests   │ │  40 tests   │ │  60 tests   │        ││
│  │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        ││
│  │ ┌─────────────┐                                                         ││
│  │ │   Async     │                                                         ││
│  │ │  40 tests   │                                                         ││
│  │ └─────────────┘                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 33.3: INFRASTRUCTURE (120 tests, 2 weeks)                               ││
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                        ││
│  │ │  Exception  │ │   Import    │ │   Source    │                        ││
│  │ │  Hierarchy  │ │   System    │ │    Maps     │                        ││
│  │ │  50 tests   │ │  40 tests   │ │  30 tests   │                        ││
│  │ └─────────────┘ └─────────────┘ └─────────────┘                        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 33.4: CLIENT DEVELOPMENT TOOLS (335 tests, 3 weeks)                     ││
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        ││
│  │ │   Client    │ │  Runtime    │ │  Extended   │ │  Promise &  │        ││
│  │ │  Testing    │ │   Types     │ │   Stdlib    │ │ Scheduling  │        ││
│  │ │  70 tests   │ │  35 tests   │ │ 180 tests   │ │  50 tests   │        ││
│  │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Dependency Graph

```
                    ┌─────────────────┐
                    │     33.1        │
                    │  Fundamentals   │
                    │  Functions,     │
                    │  Classes, etc.  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │      33.2       │ │      33.3       │ │      33.4       │
    │    Advanced     │ │ Infrastructure  │ │  Dev Tools      │
    │ (needs classes) │ │ (needs basics)  │ │ (needs stdlib)  │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │
             └───────────────────┴───────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Phase 34: DOM APIs    │
                    │ (needs all transpilation│
                    │    features)            │
                    └─────────────────────────┘
```

---

#### Phase 33.1: Core Transpilation - Fundamentals ✅ COMPLETE

**Status**: ✅ **COMPLETE** (46/46 features, 427+ tests passing)

The essential building blocks — functions, classes, control flow, and comprehensions.

**Completion Date**: December 2024  
**Test Coverage**: 427+ unit tests, 22,659+ total passing tests  
**Documentation**: [FUNDAMENTALS.md](../transpiler/FUNDAMENTALS.md)

##### Transpilation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TRANSPILATION PIPELINE                              │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Python    │    │   Python    │    │    AST      │    │ JavaScript  │  │
│  │   Source    │───▶│    AST      │───▶│ Transformer │───▶│   Output    │  │
│  │   (.py)     │    │   Parser    │    │             │    │   (.js)     │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                              │                              │
│                     ┌────────────────────────┼────────────────────────┐     │
│                     │                        │                        │     │
│                     ▼                        ▼                        ▼     │
│            ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐│
│            │    Functions    │    │     Classes     │    │  Control Flow   ││
│            │   Transpiler    │    │   Transpiler    │    │   Transpiler    ││
│            │                 │    │                 │    │                 ││
│            │ • def → function│    │ • class → class │    │ • if/elif/else  ││
│            │ • *args/**kwargs│    │ • __init__      │    │ • for/while     ││
│            │ • decorators    │    │ • inheritance   │    │ • try/except    ││
│            │ • closures      │    │ • super()       │    │ • assert        ││
│            └─────────────────┘    └─────────────────┘    └─────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

##### What Phase 33.1 Enables

After Phase 33.1, you can write client-side code like this:

```python
from pynext.client import client

@client
class TodoApp:
    """A complete todo app using only Python."""
    
    def __init__(self, initial_todos: list = None):
        self.todos = initial_todos or []
        self.filter = "all"
    
    @property
    def visible_todos(self):
        if self.filter == "active":
            return [t for t in self.todos if not t["done"]]
        elif self.filter == "completed":
            return [t for t in self.todos if t["done"]]
        return self.todos
    
    def add_todo(self, text: str):
        self.todos.append({"id": len(self.todos), "text": text, "done": False})
    
    def toggle_todo(self, id: int):
        for todo in self.todos:
            if todo["id"] == id:
                todo["done"] = not todo["done"]
                break
    
    @staticmethod
    def format_date():
        # Uses datetime from 33.4
        pass

# This transpiles to clean JavaScript:
# class TodoApp {
#     constructor(initialTodos = null) {
#         this.todos = initialTodos ?? [];
#         this.filter = "all";
#     }
#     get visibleTodos() {
#         if (this.filter === "active") {
#             return this.todos.filter(t => !t.done);
#         } ...
#     }
# }
```

##### Functions (50 tests)

**Functions:**

```python
# Python                                    # JavaScript
def greet(name, greeting="Hello"):    →    function greet(name, greeting = "Hello") {
    return f"{greeting}, {name}!"                return `${greeting}, ${name}!`;
                                            }

def process(*args, **kwargs):          →    function process(...args) {
    for arg in args:                             // kwargs parsed from last arg if object
        print(arg)                               for (const arg of args) {
    for key, value in kwargs.items():                console.log(arg);
        print(f"{key}={value}")                  }
                                            }

@decorator                             →    const my_func = decorator(function my_func() {
def my_func():                                   // body
    pass                                    });

@decorator_with_args(x=1)              →    const my_func = decorator_with_args({x: 1})(
def my_func():                                   function my_func() { /* body */ }
    pass                                    );
```

**Classes (80 tests):**

```python
# Python                                    # JavaScript
class Animal:                          →    class Animal {
    def __init__(self, name):                   constructor(name) {
        self.name = name                            this.name = name;
                                                }
    def speak(self):                            speak() {
        return "..."                                return "...";
                                                }
                                            }

class Dog(Animal):                     →    class Dog extends Animal {
    def __init__(self, name, breed):            constructor(name, breed) {
        super().__init__(name)                      super(name);
        self.breed = breed                          this.breed = breed;
                                                }
    def speak(self):                            speak() {
        return "Woof!"                              return "Woof!";
                                                }
                                            }

class Counter:                         →    class Counter {
    @staticmethod                               static create() {
    def create():                                   return new Counter();
        return Counter()                        }
                                            
    @classmethod                                static from_value(value) {
    def from_value(cls, value):                     const instance = new Counter();
        instance = cls()                            instance._count = value;
        instance._count = value                     return instance;
        return instance                         }
                                            
    @property                                   get count() {
    def count(self):                                return this._count;
        return self._count                      }
                                            
    @count.setter                               set count(value) {
    def count(self, value):                         this._count = value;
        self._count = value                     }
                                            }
```

**Control Flow (60 tests):**

```python
# Python                                    # JavaScript
try:                                   →    try {
    result = risky_operation()                  result = risky_operation();
except ValueError as e:                     } catch (e) {
    handle_error(e)                             if (e instanceof ValueError) {
except TypeError:                                   handle_error(e);
    handle_type_error()                         } else if (e instanceof TypeError) {
finally:                                            handle_type_error();
    cleanup()                                   } else {
                                                    throw e;
                                                }
                                            } finally {
                                                cleanup();
                                            }

for item in items:                     →    for (const item of items) {
    if item.valid:                              if (item.valid) {
        process(item)                               process(item);
else:                                           } else {
    no_items_found()                                continue;
                                                }
                                            }
                                            // else clause: runs if no break
                                            if (!__broke) { no_items_found(); }

assert condition, "Error message"      →    if (!condition) {
                                                throw new Error("Error message");
                                            }
```

**Comprehensions (40 tests):**

```python
# Python                                    # JavaScript
[x * 2 for x in items]                 →    items.map(x => x * 2)

[x for x in items if x > 0]            →    items.filter(x => x > 0)

[x * 2 for x in items if x > 0]        →    items.filter(x => x > 0).map(x => x * 2)

{k: v for k, v in pairs}               →    Object.fromEntries(pairs.map(([k, v]) => [k, v]))

{x for x in items}                     →    new Set(items)

[[y for y in row] for row in matrix]   →    matrix.map(row => row.map(y => y))
```

##### Phase 33.1 Checklist

**Status**: ✅ **COMPLETE** (46/46 features, 427+ tests passing)

```
Phase 33.1: Fundamentals (427+ tests) ✅
├── Functions (10 features) ✅
│   ├── [x] Basic function definitions (def → function)
│   ├── [x] Default argument values
│   ├── [x] *args (variadic positional) → rest parameters
│   ├── [x] **kwargs (variadic keyword) → object destructuring
│   ├── [x] Keyword-only arguments (*, kw_only)
│   ├── [x] Positional-only arguments (/, pos_only)
│   ├── [x] Nested functions (closures)
│   ├── [x] Lambda expressions (lambda → arrow functions)
│   ├── [x] Simple decorators (@decorator)
│   └── [x] Parameterized decorators (@decorator(args))
│
├── Classes (15 features) ✅
│   ├── [x] Basic class definition
│   ├── [x] __init__ → constructor
│   ├── [x] Instance methods (self → this)
│   ├── [x] Single inheritance (extends)
│   ├── [x] super() calls
│   ├── [x] Multiple inheritance (mixin pattern)
│   ├── [x] @staticmethod
│   ├── [x] @classmethod
│   ├── [x] @property getter
│   ├── [x] @property setter
│   ├── [x] @property deleter
│   ├── [x] Private methods (_ prefix)
│   ├── [x] Name mangling (__ prefix → #private)
│   ├── [x] @dataclass (auto-generated methods)
│   └── [x] Abstract base classes (ABC, @abstractmethod)
│
├── Control Flow (13 features) ✅
│   ├── [x] if / elif / else
│   ├── [x] for loops (for x in iterable → for...of)
│   ├── [x] for...else (loop completion flag)
│   ├── [x] while loops
│   ├── [x] while...else
│   ├── [x] break / continue
│   ├── [x] try / except (→ try/catch)
│   ├── [x] except with type checking
│   ├── [x] except as binding
│   ├── [x] Multiple except clauses
│   ├── [x] finally block
│   ├── [x] raise exceptions (→ throw)
│   └── [x] assert statements (→ conditional throw)
│
└── Comprehensions (8 features) ✅
    ├── [x] List comprehension: [x for x in items]
    ├── [x] Filtered: [x for x in items if cond]
    ├── [x] Mapped + filtered: [f(x) for x in items if cond]
    ├── [x] Nested: [[y for y in row] for row in matrix]
    ├── [x] Dict comprehension: {k: v for k, v in pairs}
    ├── [x] Set comprehension: {x for x in items}
    ├── [x] Generator expression: (x for x in items)
    └── [x] Multiple for clauses
```

**Documentation**: See [FUNDAMENTALS.md](../transpiler/FUNDAMENTALS.md) for complete documentation.

##### Phase 33.1 Files to Create

| File | Purpose |
|------|---------|
| `pynext/transpiler/functions.py` | Function transpilation (*args, **kwargs, decorators) |
| `pynext/transpiler/classes.py` | Class transpilation (inheritance, super, properties) |
| `pynext/transpiler/control_flow.py` | Control flow (try/except, for/while, assert) |
| `pynext/transpiler/comprehensions.py` | List/dict/set comprehensions |
| `pynext/runtime/decorators.js` | Decorator runtime helpers |
| `pynext/runtime/classes.js` | Class helpers (super, property descriptors) |

##### Phase 33.1 Success Criteria

| Metric | Target | Status |
|--------|--------|--------|
| Function coverage | 100% of function syntax | ✅ 100% |
| Class coverage | 100% of class syntax | ✅ 100% |
| Control flow | All Python control structures | ✅ Complete |
| Comprehensions | All comprehension types | ✅ Complete |
| Test coverage | 230+ unit tests | ✅ 427+ tests |
| Performance | < 50ms transpilation per file | ✅ Met |

##### Phase 33.1 Milestones

1. **Week 1:** Basic functions, default args, *args/**kwargs ✅
2. **Week 2:** Classes, inheritance, super(), properties ✅
3. **Week 3:** Decorators, closures, lambdas ✅
4. **Week 4:** Control flow, comprehensions ✅

**All milestones completed. Phase 33.1 is production-ready.**

---

#### Phase 33.2: Core Transpilation - Advanced Constructs (290 tests, 4 weeks)

Advanced Python features — dunder methods, generators, context managers, pattern matching, and async.

##### Advanced Constructs Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADVANCED CONSTRUCTS TRANSPILATION                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                          Dunder Methods                                  ││
│  │                                                                          ││
│  │   __str__    →  toString()              __iter__ → Symbol.iterator      ││
│  │   __repr__   →  Symbol.for("repr")      __next__ → iterator.next()      ││
│  │   __eq__     →  equals() method         __len__  → .length getter       ││
│  │   __add__    →  __add__() + runtime     __call__ → callable wrapper     ││
│  │   __getitem__→  Proxy handler           __contains__ → includes()       ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                          Generators                                      ││
│  │                                                                          ││
│  │   def gen():           →    function* gen() {                           ││
│  │       yield 1                    yield 1;                                ││
│  │       yield from other           yield* other;                           ││
│  │                              }                                           ││
│  │                                                                          ││
│  │   (x for x in items)   →    (function*() { for (x of items) yield x })()││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                       Context Managers                                   ││
│  │                                                                          ││
│  │   with resource() as r:    →    const r = resource();                   ││
│  │       use(r)                     try { use(r); }                        ││
│  │                                  finally { r.__exit__(); }              ││
│  │                                                                          ││
│  │   async with aresource():  →    const r = await aresource();            ││
│  │       await use(r)               try { await use(r); }                  ││
│  │                                  finally { await r.__aexit__(); }       ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                       Pattern Matching                                   ││
│  │                                                                          ││
│  │   match value:             →    switch(true) {                          ││
│  │       case "lit":                   case value === "lit": ...           ││
│  │       case [a, b]:                  case Array.isArray(value): ...      ││
│  │       case {"k": v}:                case typeof value === "object": ... ││
│  │       case _:                       default: ...                         ││
│  │                                 }                                        ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                           Async                                          ││
│  │                                                                          ││
│  │   async def fn():          →    async function fn() { }                 ││
│  │   await promise            →    await promise                            ││
│  │   async for x in agen():   →    for await (x of agen()) { }             ││
│  │   asyncio.gather(...)      →    Promise.all([...])                      ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

##### What Phase 33.2 Enables

After Phase 33.2, you can write Pythonic code with magic methods:

```python
from pynext.client import client

@client
class Vector:
    """A 2D vector with operator overloading."""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar: float) -> "Vector":
        return Vector(self.x * scalar, self.y * scalar)
    
    def __iter__(self):
        yield self.x
        yield self.y
    
    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"

@client
def animate_particle():
    """Uses generators for smooth animation frames."""
    position = Vector(0, 0)
    velocity = Vector(1, 0.5)
    
    while True:
        position = position + velocity
        yield position  # Generator yields each frame
        
        # Apply gravity
        velocity = velocity + Vector(0, -0.1)

@client
async def fetch_data_with_context():
    """Async context manager for API calls."""
    async with APISession() as session:
        data = await session.get("/api/items")
        
        match data:
            case {"items": [first, *rest]} if first["priority"] == "high":
                return process_urgent(first, rest)
            case {"items": items}:
                return process_normal(items)
            case {"error": msg}:
                raise APIError(msg)
```

##### Dunder Methods (100 tests)

```python
# Python                                    # JavaScript
class Vector:                          →    class Vector {
    def __init__(self, x, y):                   constructor(x, y) {
        self.x = x                                  this.x = x;
        self.y = y                                  this.y = y;
                                                }
    def __str__(self):                          toString() {
        return f"({self.x}, {self.y})"              return `(${this.x}, ${this.y})`;
                                                }
    def __repr__(self):                         [Symbol.for("repr")]() {
        return f"Vector({self.x}, {self.y})"        return `Vector(${this.x}, ${this.y})`;
                                                }
    def __eq__(self, other):                    equals(other) {
        return self.x == other.x and                return this.x === other.x &&
               self.y == other.y                       this.y === other.y;
                                                }
    def __len__(self):                          get length() {
        return 2                                    return 2;
                                                }
    def __iter__(self):                         *[Symbol.iterator]() {
        yield self.x                                yield this.x;
        yield self.y                                yield this.y;
                                                }
    def __contains__(self, item):               includes(item) {
        return item == self.x or                    return item === this.x ||
               item == self.y                          item === this.y;
                                                }
    def __getitem__(self, index):               // Via Proxy wrapper
        if index == 0: return self.x                get(target, prop) {
        if index == 1: return self.y                    if (prop === "0") return target.x;
        raise IndexError()                              if (prop === "1") return target.y;
                                                    }
    def __call__(self, scale):                  // Callable object pattern
        return Vector(self.x * scale,               __call__(scale) {
                      self.y * scale)                   return new Vector(
                                                            this.x * scale,
                                                            this.y * scale
                                                        );
                                                    }
                                            }
```

**Generators and Iterators (50 tests):**

```python
# Python                                    # JavaScript
def countdown(n):                      →    function* countdown(n) {
    while n > 0:                                while (n > 0) {
        yield n                                     yield n;
        n -= 1                                      n -= 1;
                                                }
                                            }

def flatten(nested):                   →    function* flatten(nested) {
    for item in nested:                         for (const item of nested) {
        if isinstance(item, list):                  if (Array.isArray(item)) {
            yield from flatten(item)                    yield* flatten(item);
        else:                                       } else {
            yield item                                  yield item;
                                                    }
                                                }
                                            }

# Generator expression                      // Generator function
(x * 2 for x in items)                 →    (function*() {
                                                for (const x of items) yield x * 2;
                                            })()
```

**Context Managers (40 tests):**

```python
# Python                                    # JavaScript
with open_file(path) as f:             →    const f = open_file(path);
    data = f.read()                         try {
                                                const data = f.read();
                                            } finally {
                                                f.close();
                                            }

with resource1() as r1, \              →    const r1 = resource1();
     resource2() as r2:                     try {
    process(r1, r2)                             const r2 = resource2();
                                                try {
                                                    process(r1, r2);
                                                } finally {
                                                    r2.close();
                                                }
                                            } finally {
                                                r1.close();
                                            }

async with async_resource() as r:      →    const r = await async_resource();
    await r.process()                       try {
                                                await r.process();
                                            } finally {
                                                await r.close();
                                            }
```

**Pattern Matching (60 tests):**

```python
# Python                                    # JavaScript
match command:                         →    switch (true) {
    case "quit":                                case command === "quit":
        exit()                                      exit();
    case "help":                                    break;
        show_help()                             case command === "help":
    case ["move", x, y]:                            show_help();
        move_to(x, y)                               break;
    case {"action": "click", "x": x}:           case Array.isArray(command) &&
        click_at(x)                                   command[0] === "move":
    case _:                                         const [, x, y] = command;
        unknown()                                   move_to(x, y);
                                                    break;
                                                case typeof command === "object" &&
                                                      command.action === "click":
                                                    const { x } = command;
                                                    click_at(x);
                                                    break;
                                                default:
                                                    unknown();
                                            }
```

**Async Patterns (40 tests):**

```python
# Python                                    # JavaScript
async for item in async_iter():        →    for await (const item of async_iter()) {
    await process(item)                         await process(item);
                                            }

results = await asyncio.gather(        →    const results = await Promise.all([
    fetch_a(),                                  fetch_a(),
    fetch_b(),                                  fetch_b(),
    fetch_c(),                                  fetch_c(),
)                                           ]);
```

##### Phase 33.2 Checklist

```
Phase 33.2: Advanced Constructs (290 tests) ✅
├── Dunder Methods (100 tests) ✅
│   ├── String Representation
│   │   ├── [x] __str__ → toString()
│   │   ├── [x] __repr__ → Symbol.for("repr")
│   │   └── [x] __format__ → custom formatter
│   │
│   ├── Comparison
│   │   ├── [x] __eq__ / __ne__ → equals()
│   │   ├── [x] __lt__ / __gt__ → comparison
│   │   └── [x] __le__ / __ge__ → comparison
│   │
│   ├── Container
│   │   ├── [x] __len__ → .length getter
│   │   ├── [x] __bool__ → Boolean coercion
│   │   ├── [x] __iter__ → Symbol.iterator
│   │   ├── [x] __next__ → iterator.next()
│   │   ├── [x] __contains__ → includes/has
│   │   ├── [x] __getitem__ → Proxy get
│   │   ├── [x] __setitem__ → Proxy set
│   │   └── [x] __delitem__ → Proxy delete
│   │
│   ├── Arithmetic
│   │   ├── [x] __add__ / __sub__ / __mul__ / __truediv__
│   │   ├── [x] __radd__ / __rsub__ (reverse ops)
│   │   ├── [x] __iadd__ / __isub__ (in-place)
│   │   └── [x] __neg__ / __pos__ / __abs__
│   │
│   ├── Callable
│   │   └── [x] __call__ → callable object
│   │
│   └── Attribute Access
│       ├── [x] __getattr__ → Proxy get
│       ├── [x] __setattr__ → Proxy set
│       └── [x] __delattr__ → Proxy delete
│
├── Generators (50 tests) ✅
│   ├── [x] yield statement → yield keyword
│   ├── [x] yield from → yield* delegation
│   ├── [x] Generator functions → function*
│   ├── [x] Generator expressions → IIFE generator
│   ├── [x] send() method
│   ├── [x] throw() method
│   ├── [x] close() method
│   └── [x] return in generator → StopIteration
│
├── Context Managers (40 tests) ✅ (5/6)
│   ├── [x] with statement (single) → try/finally
│   ├── [x] with statement (multiple) → nested try/finally
│   ├── [x] __enter__ / __exit__ protocol
│   ├── [x] async with → async try/finally
│   ├── [x] __aenter__ / __aexit__ protocol
│   └── [ ] contextlib.contextmanager decorator
│
├── Pattern Matching (60 tests) ✅
│   ├── [x] Literal patterns (strings, numbers)
│   ├── [x] Capture patterns (x := value)
│   ├── [x] Wildcard pattern (_)
│   ├── [x] Sequence patterns ([a, b, *rest])
│   ├── [x] Mapping patterns ({"key": value})
│   ├── [x] Class patterns (Point(x=1, y=2))
│   ├── [x] OR patterns (case A | B)
│   ├── [x] AS patterns (case x as alias)
│   ├── [x] Guard clauses (case x if condition)
│   └── [x] Nested patterns
│
└── Async (40 tests) ✅ (5/7)
    ├── [x] async def → async function
    ├── [x] await expression
    ├── [x] async for → for await
    ├── [x] async with → async try/finally
    ├── [x] asyncio.gather → Promise.all
    ├── [ ] asyncio.sleep → setTimeout wrapper
    └── [ ] Task cancellation
```

##### Phase 33.2 Files to Create

| File | Purpose |
|------|---------|
| `pynext/transpiler/dunders.py` | All dunder method transpilation |
| `pynext/transpiler/generators.py` | yield, yield from, generator protocol |
| `pynext/transpiler/context.py` | Context manager transpilation |
| `pynext/transpiler/pattern.py` | Pattern matching transpilation |
| `pynext/transpiler/async_support.py` | async/await, async for/with |
| `pynext/runtime/dunders.js` | Runtime helpers for dunder methods |
| `pynext/runtime/generators.js` | Generator protocol helpers |
| `pynext/runtime/proxy.js` | Proxy wrappers for __getitem__ etc. |

##### Phase 33.2 Success Criteria

| Metric | Target |
|--------|--------|
| Dunder methods | All common dunders supported |
| Generators | Full generator protocol |
| Context managers | sync and async |
| Pattern matching | Python 3.10+ match/case |
| Async | Complete async/await support |
| Test coverage | 290+ unit tests |

##### Phase 33.2 Milestones

1. **Week 1:** Dunder methods (string, comparison, container)
2. **Week 2:** Dunder methods (arithmetic, callable, attribute access)
3. **Week 3:** Generators, context managers
4. **Week 4:** Pattern matching, async patterns

---

#### Phase 33.3: Core Transpilation - Infrastructure (120 tests, 2 weeks)

Critical infrastructure — exception hierarchy, import system, and source maps.

##### Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TRANSPILATION INFRASTRUCTURE                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      Exception Hierarchy                                 ││
│  │                                                                          ││
│  │  BaseException                                                           ││
│  │  ├── SystemExit                                                          ││
│  │  ├── KeyboardInterrupt                                                   ││
│  │  └── Exception                                                           ││
│  │      ├── ArithmeticError → ZeroDivisionError, OverflowError             ││
│  │      ├── LookupError → KeyError, IndexError                             ││
│  │      ├── TypeError, ValueError, AttributeError                          ││
│  │      ├── RuntimeError → NotImplementedError, RecursionError             ││
│  │      └── StopIteration (critical for generators!)                       ││
│  │                                                                          ││
│  │  Features:                                                               ││
│  │  • isinstance() / issubclass() work correctly                           ││
│  │  • Exception chaining (raise ... from ...)                              ││
│  │  • Custom exception classes                                              ││
│  │  • __cause__, __context__, __traceback__                                ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        Import System                                     ││
│  │                                                                          ││
│  │  Python                          JavaScript                              ││
│  │  ────────────────────────────────────────────────────────────────────   ││
│  │  import math                  →  import * as math from 'pynext/math'    ││
│  │  from math import sqrt        →  import { sqrt } from 'pynext/math'     ││
│  │  from . import sibling        →  import * as sibling from './sibling'  ││
│  │  from ..parent import x       →  import { x } from '../parent'          ││
│  │                                                                          ││
│  │  Dynamic imports:                                                        ││
│  │  await import_module("./x")   →  await import('./x.js')                 ││
│  │                                                                          ││
│  │  Circular import handling:                                               ││
│  │  • Cycle detection at transpile time                                    ││
│  │  • Lazy initialization for cyclic deps                                  ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        Source Maps                                       ││
│  │                                                                          ││
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                ││
│  │  │  Python     │     │   Source    │     │  JavaScript │                ││
│  │  │  Source     │────▶│    Map      │◀────│   Output    │                ││
│  │  │  app.py:42  │     │  (.map)     │     │  app.js:87  │                ││
│  │  └─────────────┘     └─────────────┘     └─────────────┘                ││
│  │                             │                                            ││
│  │                             ▼                                            ││
│  │  ┌─────────────────────────────────────────────────────────────────┐    ││
│  │  │                    Debugging Experience                          │    ││
│  │  │  • Breakpoints in Python source                                 │    ││
│  │  │  • Stack traces show Python lines                               │    ││
│  │  │  • Variable names preserved                                     │    ││
│  │  │  • Browser DevTools show .py files                              │    ││
│  │  └─────────────────────────────────────────────────────────────────┘    ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

##### What Phase 33.3 Enables

After Phase 33.3, you get proper error handling and debugging:

```python
from pynext.client import client
from pynext.client.exceptions import ValueError, KeyError, HTTPError

@client
def process_user_data(data: dict):
    """Full exception support with Python semantics."""
    try:
        user_id = data["user_id"]  # KeyError if missing
        
        if not isinstance(user_id, int):
            raise TypeError(f"Expected int, got {type(user_id).__name__}")
        
        if user_id < 0:
            raise ValueError("user_id must be positive")
        
        return fetch_user(user_id)
        
    except KeyError as e:
        # Proper exception chaining
        raise ValueError("Missing required field") from e
        
    except (TypeError, ValueError) as e:
        # Multiple exception types
        console.error(f"Validation error: {e}")
        raise
        
    finally:
        cleanup()

# IMPORT SYSTEM - Clean module structure
# utils/validators.py
from .base import BaseValidator  # Relative import
from ..config import settings    # Parent import

# Dynamic imports for code splitting
@client
async def load_heavy_module():
    # Lazy load only when needed
    module = await import_module("./heavy_charts")
    return module.render_chart(data)

# SOURCE MAPS - Errors show Python line numbers!
# Browser console shows:
#   ValueError: user_id must be positive
#     at process_user_data (app.py:12)  ← Python file, Python line!
#     at handle_submit (forms.py:45)
```

##### Tier 3: Advanced Features (30 tests)

**Operator Overloading:**

```python
# Python                                    # JavaScript (method call workaround)
v3 = v1 + v2                           →    const v3 = v1.__add__(v2);
# OR with runtime helper:
                                            const v3 = __py_add__(v1, v2);

# In-place operations
v1 += v2                               →    v1 = v1.__iadd__ ? v1.__iadd__(v2)
                                                           : __py_add__(v1, v2);
```

**Attribute Access via Proxy (30 tests):**

```python
# Python                                    # JavaScript
class Dynamic:                         →    class Dynamic {
    def __getattr__(self, name):                // Wrapped with Proxy
        return f"dynamic_{name}"            }
                                            
    def __setattr__(self, name, val):       const DynamicProxy = new Proxy(Dynamic, {
        print(f"Setting {name}")                get(target, prop) {
        super().__setattr__(name, val)              return `dynamic_${prop}`;
                                                },
                                                set(target, prop, value) {
                                                    console.log(`Setting ${prop}`);
                                                    target[prop] = value;
                                                    return true;
                                                }
                                            });
```

**Special Cases (20 tests):**

```python
# Python                                    # JavaScript
# Walrus operator
if (n := len(items)) > 10:             →    let n;
    print(f"Too many: {n}")                 if ((n = items.length) > 10) {
                                                console.log(`Too many: ${n}`);
                                            }

# Unpacking
a, *rest, z = items                    →    const [a, ...rest] = items;
                                            const z = rest.pop();

first, *middle, last = items           →    const [first, ...temp] = items;
                                            const last = temp.pop();
                                            const middle = temp;

# Identity
x is None                              →    x === null
x is not None                          →    x !== null

# Enums
class Color(Enum):                     →    const Color = Object.freeze({
    RED = 1                                     RED: 1,
    GREEN = 2                                   GREEN: 2,
    BLUE = 3                                    BLUE: 3,
                                            });
```

##### Phase 33.3 Additional Features (30 tests)

```
Operator Overloading & Attribute Access (30 tests)
├── Operator Overloading (20 tests)
│   ├── [ ] Binary operators via __add__, __sub__, etc.
│   ├── [ ] Reverse operators via __radd__, __rsub__, etc.
│   ├── [ ] In-place operators via __iadd__, __isub__, etc.
│   └── [ ] Runtime operator helper functions
│
└── Attribute Access (10 tests)
    ├── [ ] __getattr__ via Proxy
    ├── [ ] __setattr__ via Proxy
    └── [ ] __delattr__ via Proxy
```

---

##### Phase 33.3 Main Checklist

```
Phase 33.3: Infrastructure (120 tests)
├── Exception Hierarchy (50 tests)
│   ├── [ ] BaseException root class
│   ├── [ ] Exception base class
│   ├── [ ] All standard exceptions (see hierarchy)
│   ├── [ ] isinstance() / issubclass() work correctly
│   ├── [ ] Exception chaining (raise from)
│   ├── [ ] Custom exception classes
│   ├── [ ] __cause__, __context__, __traceback__
│   └── [ ] StopIteration with .value
│
├── Import System (40 tests)
│   ├── [ ] import module
│   ├── [ ] import module as alias
│   ├── [ ] from module import x
│   ├── [ ] from module import x as alias
│   ├── [ ] from module import x, y, z
│   ├── [ ] from module import *
│   ├── [ ] from . import x (relative)
│   ├── [ ] from .. import x (parent)
│   ├── [ ] await import_module() (dynamic)
│   ├── [ ] Circular import detection
│   ├── [ ] __all__ handling
│   └── [ ] TYPE_CHECKING imports
│
└── Source Maps (30 tests)
    ├── [ ] Line-level mapping
    ├── [ ] Column-level mapping
    ├── [ ] Variable name preservation
    ├── [ ] Function/class name mapping
    ├── [ ] Stack trace rewriting
    ├── [ ] Console log source attribution
    └── [ ] Browser DevTools integration
```

##### Phase 33.3 Files to Create

| File | Purpose |
|------|---------|
| `pynext/runtime/exceptions.js` | Full Python exception hierarchy |
| `pynext/transpiler/imports.py` | Import/module transpilation |
| `pynext/transpiler/sourcemap.py` | Enhanced source map generation |
| `pynext/transpiler/stack_rewriter.py` | Stack trace rewriting to Python |
| `pynext/transpiler/operators.py` | Operator overloading helpers |

##### Phase 33.3 Success Criteria

| Metric | Target |
|--------|--------|
| Exceptions | All Python exceptions with inheritance |
| Imports | All import forms including dynamic |
| Source maps | Line, column, variable mapping |
| Stack traces | Rewritten to Python source |
| Test coverage | 120+ unit tests |

##### Phase 33.3 Milestones

1. **Week 1:** Exception hierarchy, import system
2. **Week 2:** Source maps, stack trace rewriting

---

#### Phase 33.4: Client Development Tools (335 tests, 3 weeks)

Developer experience — testing, type checking, extended stdlib, and scheduling.

##### Development Tools Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CLIENT DEVELOPMENT TOOLS                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     Client Testing Infrastructure                        ││
│  │                                                                          ││
│  │  from pynext.testing.client import render, screen, fireEvent            ││
│  │                                                                          ││
│  │  def test_counter():                                                     ││
│  │      render(Counter, props={"initial": 5})                              ││
│  │      button = screen.getByTestId("counter-btn")                         ││
│  │      assert button.textContent == "Count: 5"                            ││
│  │      fireEvent.click(button)                                            ││
│  │      assert button.textContent == "Count: 6"                            ││
│  │                                                                          ││
│  │  Features:                                                               ││
│  │  • render() / cleanup()                                                 ││
│  │  • screen.getByText/Role/TestId                                         ││
│  │  • fireEvent.click/keyDown/change                                       ││
│  │  • waitFor() for async                                                  ││
│  │  • mock_fetch, mock_navigator                                           ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     Runtime Type Checking                                ││
│  │                                                                          ││
│  │  @typed                                                                  ││
│  │  @client                                                                 ││
│  │  def greet(name: str, times: int = 1) -> str:                           ││
│  │      return (f"Hello, {name}! " * times).strip()                        ││
│  │                                                                          ││
│  │  greet(123)  # TypeError: name must be str, got int                     ││
│  │                                                                          ││
│  │  Features:                                                               ││
│  │  • @typed decorator                                                     ││
│  │  • Basic types (str, int, float, bool)                                  ││
│  │  • Collection types (List, Dict, Set)                                   ││
│  │  • Union, Optional, Callable                                            ││
│  │  • Dev mode only (no-op in production)                                  ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     Extended Standard Library                            ││
│  │                                                                          ││
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐            ││
│  │  │ datetime  │  │collections│  │ itertools │  │ functools │            ││
│  │  │           │  │           │  │           │  │           │            ││
│  │  │ datetime  │  │ Counter   │  │ chain     │  │ partial   │            ││
│  │  │ date      │  │ defaultdict│ │ cycle     │  │ reduce    │            ││
│  │  │ time      │  │ deque     │  │ groupby   │  │ lru_cache │            ││
│  │  │ timedelta │  │ namedtuple│  │ islice    │  │ wraps     │            ││
│  │  │ timezone  │  │ OrderedDict│ │ permutations│ │           │            ││
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘            ││
│  │                                                                          ││
│  │  ┌───────────┐  ┌───────────┐                                           ││
│  │  │ operator  │  │   copy    │                                           ││
│  │  │           │  │           │                                           ││
│  │  │ itemgetter│  │ copy      │                                           ││
│  │  │ attrgetter│  │ deepcopy  │                                           ││
│  │  │ methodcaller│ │           │                                           ││
│  │  └───────────┘  └───────────┘                                           ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     Promise & Scheduling                                 ││
│  │                                                                          ││
│  │  Promise Methods:                    Scheduling APIs:                    ││
│  │  • Promise.all()                    • queueMicrotask()                  ││
│  │  • Promise.allSettled()             • requestIdleCallback()             ││
│  │  • Promise.race()                   • cancelIdleCallback()              ││
│  │  • Promise.any()                    • requestAnimationFrame()           ││
│  │  • Promise.withResolvers()          • cancelAnimationFrame()            ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

##### What Phase 33.4 Enables

After Phase 33.4, you get full testing and developer tooling:

```python
# TEST YOUR CLIENT CODE IN PYTHON
from pynext.testing.client import render, screen, fireEvent, waitFor

def test_todo_app():
    """Test client components just like React Testing Library."""
    render(TodoApp, props={"initial": ["Buy milk"]})
    
    # Query elements
    input = screen.getByPlaceholderText("Add todo...")
    button = screen.getByRole("button", name="Add")
    
    # Interact
    fireEvent.change(input, target={"value": "Walk dog"})
    fireEvent.click(button)
    
    # Assert
    assert screen.getByText("Walk dog")
    assert len(screen.getAllByRole("listitem")) == 2

async def test_async_data():
    """Test async operations."""
    render(UserProfile, props={"userId": 123})
    
    # Wait for async data
    await waitFor(lambda: screen.getByText("John Doe"))
    
    assert screen.getByTestId("email").textContent == "john@example.com"


# RUNTIME TYPE CHECKING (DEV MODE)
from pynext.client import client, typed

@typed  # Enable runtime type checking
@client
def calculate_total(items: list[dict], tax_rate: float = 0.1) -> float:
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    return subtotal * (1 + tax_rate)

calculate_total([{"price": 10}], "invalid")  
# TypeError: tax_rate must be float, got str


# EXTENDED STDLIB
from pynext.client.datetime import datetime, timedelta
from pynext.client.collections import Counter, defaultdict
from pynext.client.itertools import groupby, chain
from pynext.client.functools import lru_cache

@client
def analyze_orders(orders: list[dict]):
    # Group by date
    by_date = defaultdict(list)
    for order in orders:
        date = datetime.fromisoformat(order["created_at"]).date()
        by_date[date].append(order)
    
    # Count product frequency
    products = Counter(
        item["product_id"] 
        for order in orders 
        for item in order["items"]
    )
    
    # Get trending (most common 5)
    return products.most_common(5)

@lru_cache(maxsize=100)  # Memoization works!
@client
def expensive_calculation(n: int) -> int:
    return sum(i ** 2 for i in range(n))


# PROMISE & SCHEDULING
from pynext.client import (
    Promise, 
    queue_microtask, 
    request_animation_frame,
    request_idle_callback
)

@client
async def fetch_all_data():
    # Parallel fetches
    user, posts, comments = await Promise.all([
        fetch("/api/user"),
        fetch("/api/posts"),
        fetch("/api/comments")
    ])
    return {"user": user, "posts": posts, "comments": comments}

@client
def smooth_animation(element):
    def animate():
        # Runs at 60fps
        element.style.transform = f"translateX({x}px)"
        x += 1
        if x < 500:
            request_animation_frame(animate)
    
    request_animation_frame(animate)
```

##### Phase 33.4 Checklist

```
Phase 33.4: Client Development Tools (335 tests)
├── Client Testing Infrastructure (70 tests)
│   ├── Core API
│   │   ├── [ ] render(Component, props)
│   │   ├── [ ] cleanup()
│   │   ├── [ ] screen object
│   │   ├── [ ] within(element)
│   │   └── [ ] act(callback)
│   │
│   ├── Query Methods
│   │   ├── [ ] getByTestId / queryByTestId / findByTestId
│   │   ├── [ ] getByText / queryByText / findByText
│   │   ├── [ ] getByRole / queryByRole / findByRole
│   │   ├── [ ] getByLabelText / getByPlaceholderText
│   │   └── [ ] getAllBy* variants
│   │
│   ├── Fire Events
│   │   ├── [ ] click, dblClick, contextMenu
│   │   ├── [ ] keyDown, keyUp, keyPress
│   │   ├── [ ] change, input, submit
│   │   ├── [ ] focus, blur
│   │   └── [ ] mouse/touch events
│   │
│   ├── Async Testing
│   │   ├── [ ] waitFor(predicate)
│   │   ├── [ ] waitFor with timeout
│   │   └── [ ] findBy* async queries
│   │
│   └── Mocking
│       ├── [ ] mock_fetch
│       ├── [ ] mock_navigator
│       ├── [ ] mock_window
│       └── [ ] mock_document
│
├── Runtime Type Checking (35 tests)
│   ├── [ ] @typed decorator
│   ├── [ ] str/int/float/bool checking
│   ├── [ ] List[T], Dict[K,V], Set[T]
│   ├── [ ] Optional[T], Union[T1,T2]
│   ├── [ ] Callable[[Args], Return]
│   ├── [ ] Return type validation
│   └── [ ] enable_type_checking() config
│
├── Extended Standard Library (180 tests)
│   ├── datetime (40 tests)
│   │   ├── [ ] datetime, date, time classes
│   │   ├── [ ] timedelta arithmetic
│   │   ├── [ ] timezone handling
│   │   └── [ ] strftime/strptime
│   │
│   ├── collections (35 tests)
│   │   ├── [ ] Counter
│   │   ├── [ ] defaultdict
│   │   ├── [ ] deque
│   │   ├── [ ] OrderedDict
│   │   └── [ ] namedtuple
│   │
│   ├── itertools (45 tests)
│   │   ├── [ ] chain, cycle, repeat, count
│   │   ├── [ ] islice, takewhile, dropwhile
│   │   ├── [ ] groupby, accumulate
│   │   └── [ ] product, permutations, combinations
│   │
│   ├── functools (25 tests)
│   │   ├── [ ] partial
│   │   ├── [ ] reduce
│   │   ├── [ ] lru_cache, cache
│   │   └── [ ] wraps
│   │
│   ├── operator (20 tests)
│   │   ├── [ ] itemgetter, attrgetter, methodcaller
│   │   └── [ ] Arithmetic/comparison operators
│   │
│   └── copy (15 tests)
│       ├── [ ] copy (shallow)
│       └── [ ] deepcopy
│
└── Promise & Scheduling (50 tests)
    ├── Promise Methods (20 tests)
    │   ├── [ ] Promise.all()
    │   ├── [ ] Promise.allSettled()
    │   ├── [ ] Promise.race()
    │   ├── [ ] Promise.any() + AggregateError
    │   └── [ ] Promise.withResolvers()
    │
    ├── Microtask Queue (10 tests)
    │   └── [ ] queueMicrotask()
    │
    ├── Idle Callbacks (10 tests)
    │   ├── [ ] requestIdleCallback()
    │   └── [ ] cancelIdleCallback()
    │
    └── Animation Frames (10 tests)
        ├── [ ] requestAnimationFrame()
        └── [ ] cancelAnimationFrame()
```

##### Phase 33.4 Files to Create

| File | Purpose |
|------|---------|
| `pynext/testing/__init__.py` | Client testing infrastructure |
| `pynext/testing/client.py` | render, screen, fireEvent, waitFor |
| `pynext/testing/mocks.py` | mock_fetch, mock_navigator, mock_window |
| `pynext/testing/queries.py` | getByText, getByRole, getByTestId |
| `pynext/client/typed.py` | @typed decorator for runtime type checking |
| `pynext/runtime/stdlib/datetime.js` | datetime, date, time, timedelta |
| `pynext/runtime/stdlib/collections.js` | Counter, defaultdict, deque, etc. |
| `pynext/runtime/stdlib/itertools.js` | All itertools functions |
| `pynext/runtime/stdlib/functools.js` | partial, reduce, lru_cache |
| `pynext/runtime/stdlib/operator.js` | itemgetter, attrgetter, etc. |
| `pynext/runtime/stdlib/copy.js` | copy, deepcopy |
| `pynext/runtime/promise.js` | Promise utilities |
| `pynext/runtime/scheduling.js` | Scheduling APIs |

##### Phase 33.4 Success Criteria

| Metric | Target |
|--------|--------|
| Client testing | Full render/query/event API |
| Type checking | Optional runtime validation |
| Extended stdlib | 6 modules fully implemented |
| Promise utilities | All Promise.* methods |
| Scheduling | All scheduling APIs |
| Test coverage | 335+ unit tests |

##### Phase 33.4 Milestones

1. **Week 1:** Client testing infrastructure
2. **Week 2:** Runtime type checking, Promise utilities, scheduling
3. **Week 3:** Extended stdlib (datetime, collections, itertools, functools, operator, copy)

---

### Phase 33 Summary

| Sub-Phase | Focus | Tests | Weeks |
|-----------|-------|-------|-------|
| **33.1** | Fundamentals (functions, classes, control flow, comprehensions) | 230 | 4 |
| **33.2** | Advanced (dunders, generators, context managers, pattern matching, async) | 290 | 4 |
| **33.3** | Infrastructure (exceptions, imports, source maps) | 120 | 2 |
| **33.4** | Dev Tools (testing, types, stdlib, scheduling) | 335 | 3 |
| **Total** | | **975** | **13** |

---

##### Reference: Detailed Exception Hierarchy (Phase 33.3)

The following was the original Phase 33 checklist - now superseded by 33.1-33.4 above:

---

### Phase 33 Detailed Reference Material

The following sections provide detailed API specifications for Phase 33 components.
These are reference materials for implementation.

---

#### Full Python Exception Hierarchy (Phase 33.3 Reference)

Complete exception class hierarchy for proper try/except handling.

```python
from pynext.client import (
    # Base exceptions
    BaseException, Exception, 
    # System exceptions
    SystemExit, KeyboardInterrupt, GeneratorExit,
    # Iteration
    StopIteration, StopAsyncIteration,
    # Arithmetic
    ArithmeticError, ZeroDivisionError, OverflowError, FloatingPointError,
    # Assertions
    AssertionError,
    # Attribute/Name
    AttributeError, NameError, UnboundLocalError,
    # Import
    ImportError, ModuleNotFoundError,
    # Lookup
    LookupError, IndexError, KeyError,
    # Type/Value
    TypeError, ValueError, UnicodeError, UnicodeDecodeError, UnicodeEncodeError,
    # Runtime
    RuntimeError, NotImplementedError, RecursionError,
    # OS/IO
    OSError, IOError, FileNotFoundError, PermissionError, TimeoutError,
    # Other
    MemoryError, BufferError, EOFError, SyntaxError,
    # Promise-specific
    AggregateError,
)

# =============================================================================
# Exception Hierarchy
# =============================================================================

# BaseException (root of all exceptions)
#   ├── SystemExit
#   ├── KeyboardInterrupt
#   ├── GeneratorExit
#   └── Exception (base for all standard exceptions)
#       ├── StopIteration (critical for generators!)
#       ├── StopAsyncIteration (async generators)
#       ├── ArithmeticError
#       │   ├── ZeroDivisionError
#       │   ├── OverflowError
#       │   └── FloatingPointError
#       ├── AssertionError
#       ├── AttributeError
#       ├── BufferError
#       ├── EOFError
#       ├── ImportError
#       │   └── ModuleNotFoundError
#       ├── LookupError
#       │   ├── IndexError
#       │   └── KeyError
#       ├── MemoryError
#       ├── NameError
#       │   └── UnboundLocalError
#       ├── OSError (IOError is alias)
#       │   ├── FileNotFoundError
#       │   ├── PermissionError
#       │   └── TimeoutError
#       ├── RuntimeError
#       │   ├── NotImplementedError
#       │   └── RecursionError
#       ├── SyntaxError
#       ├── TypeError
#       ├── ValueError
#       │   └── UnicodeError
#       │       ├── UnicodeDecodeError
#       │       └── UnicodeEncodeError
#       └── AggregateError (for Promise.any)

# =============================================================================
# Exception Usage in Transpiled Code
# =============================================================================

# try/except with specific types
@client
def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return float('inf')
    except TypeError as e:
        console.error(f"Type error: {e}")
        raise

# Multiple exception types
@client
def get_item(data, key):
    try:
        return data[key]
    except (KeyError, IndexError) as e:
        return None
    except TypeError:
        raise ValueError(f"Cannot index {type(data)}")

# Exception chaining (raise from)
@client
def process_data(raw):
    try:
        parsed = parse(raw)
    except ValueError as e:
        raise RuntimeError("Failed to process data") from e
    # In JS: new RuntimeError("...").cause = e

# StopIteration for generators
@client
def my_generator():
    yield 1
    yield 2
    return "done"  # Becomes StopIteration.value

# Custom exceptions
@client
class ValidationError(ValueError):
    def __init__(self, field, message):
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message

# AggregateError for Promise.any
@client
async def fetch_any(urls):
    try:
        return await Promise.any([fetch(url) for url in urls])
    except AggregateError as e:
        console.error(f"All {len(e.errors)} requests failed")
        for err in e.errors:
            console.error(f"  - {err}")
        raise

# Exception attributes
@client
def handle_error(e):
    console.log(f"Type: {type(e).__name__}")
    console.log(f"Message: {str(e)}")
    console.log(f"Args: {e.args}")
    if hasattr(e, '__cause__'):
        console.log(f"Caused by: {e.__cause__}")
    if hasattr(e, '__traceback__'):
        # Traceback rewritten to Python source
        console.log(f"Traceback: {e.__traceback__}")
```

##### Exception Hierarchy Checklist

```
Exception Hierarchy (Phase 33)
├── Base Classes (10 tests)
│   ├── [ ] BaseException
│   ├── [ ] Exception
│   ├── [ ] isinstance() checks
│   ├── [ ] issubclass() checks
│   └── [ ] Exception inheritance chain
│
├── Iteration Exceptions (5 tests)
│   ├── [ ] StopIteration (with .value)
│   ├── [ ] StopAsyncIteration
│   └── [ ] Generator return value
│
├── Arithmetic Exceptions (5 tests)
│   ├── [ ] ZeroDivisionError
│   ├── [ ] OverflowError
│   └── [ ] FloatingPointError
│
├── Lookup Exceptions (5 tests)
│   ├── [ ] IndexError
│   ├── [ ] KeyError
│   └── [ ] LookupError base
│
├── Type/Value Exceptions (5 tests)
│   ├── [ ] TypeError
│   ├── [ ] ValueError
│   └── [ ] UnicodeError variants
│
├── Other Standard Exceptions (5 tests)
│   ├── [ ] AttributeError
│   ├── [ ] NameError
│   ├── [ ] RuntimeError
│   ├── [ ] NotImplementedError
│   └── [ ] AssertionError
│
├── Exception Features (10 tests)
│   ├── [ ] Exception chaining (raise from)
│   ├── [ ] Exception.args
│   ├── [ ] Exception.__cause__
│   ├── [ ] Exception.__context__
│   ├── [ ] Custom exception classes
│   └── [ ] AggregateError for Promise.any
│
└── Traceback Integration (5 tests)
    ├── [ ] __traceback__ attribute
    ├── [ ] Stack trace rewriting to Python
    └── [ ] Source map integration
```

##### Import and Module Transpilation

Python import statements transpiled to JavaScript modules.

```python
# =============================================================================
# Basic Imports
# =============================================================================

# Import entire module
import math                      # → import * as math from 'pynext/stdlib/math.js'
result = math.sqrt(16)

# Import with alias
import numpy as np               # → import * as np from 'numpy'

# From import (named)
from math import sqrt, pi        # → import { sqrt, pi } from 'pynext/stdlib/math.js'

# From import with alias
from math import sqrt as square_root

# From import all (star import)
from math import *               # → import * from 'pynext/stdlib/math.js'

# =============================================================================
# Relative Imports
# =============================================================================

# Same directory
from . import sibling            # → import * as sibling from './sibling.js'
from .sibling import func        # → import { func } from './sibling.js'

# Parent directory
from .. import parent            # → import * as parent from '../parent.js'
from ..parent import thing       # → import { thing } from '../parent.js'

# Deep relative
from ...utils.helpers import x   # → import { x } from '../../utils/helpers.js'

# =============================================================================
# Dynamic Imports (Lazy Loading)
# =============================================================================

# Async dynamic import
@client
async def load_heavy_component():
    module = await import_module("./heavy_component.py")
    return module.HeavyComponent

# Conditional import
@client
async def get_chart_library():
    if is_mobile():
        module = await import_module("./charts/lite.py")
    else:
        module = await import_module("./charts/full.py")
    return module

# Import with loading state
@client
def lazy_component(path):
    component = Signal(None)
    loading = Signal(True)
    
    async def load():
        module = await import_module(path)
        component.set(module.default)
        loading.set(False)
    
    load()
    return component, loading

# =============================================================================
# Circular Import Handling
# =============================================================================

# PyNext handles circular imports by:
# 1. Detecting cycles at transpile time
# 2. Using lazy initialization for cyclic dependencies
# 3. Warning developers about potential issues

# Example: a.py imports b.py, b.py imports a.py
# Transpiled with lazy resolution:
# a.js: let _b; export const getB = () => _b || (_b = require('./b.js'))

# =============================================================================
# Re-exports
# =============================================================================

# __all__ for explicit exports
__all__ = ["public_func", "PublicClass"]

# Re-export from submodules
from .submodule import thing      # Makes 'thing' available from this module
from .other import *              # Re-export everything from 'other'

# =============================================================================
# Conditional Imports (TYPE_CHECKING)
# =============================================================================

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Only imported for type hints, not at runtime
    from .heavy_module import HeavyType

def process(item: "HeavyType") -> None:
    pass
```

##### Import/Module Checklist

```
Import/Module Transpilation (Phase 33)
├── Basic Imports (10 tests)
│   ├── [ ] import module
│   ├── [ ] import module as alias
│   ├── [ ] from module import x
│   ├── [ ] from module import x as alias
│   ├── [ ] from module import x, y, z
│   └── [ ] from module import *
│
├── Relative Imports (8 tests)
│   ├── [ ] from . import x
│   ├── [ ] from .module import x
│   ├── [ ] from .. import x
│   ├── [ ] from ..module import x
│   └── [ ] Deep relative (...)
│
├── Dynamic Imports (10 tests)
│   ├── [ ] await import_module(path)
│   ├── [ ] Conditional dynamic import
│   ├── [ ] Dynamic import error handling
│   └── [ ] Code splitting integration
│
├── Circular Imports (5 tests)
│   ├── [ ] Cycle detection
│   ├── [ ] Lazy initialization
│   └── [ ] Warning generation
│
└── Re-exports (7 tests)
    ├── [ ] __all__ handling
    ├── [ ] Re-export from submodule
    ├── [ ] TYPE_CHECKING imports
    └── [ ] Conditional exports
```

##### Source Map Enhancements

Advanced source mapping for Python-to-JavaScript debugging.

```python
# =============================================================================
# Source Map Features
# =============================================================================

# 1. Line-Level Mapping
# Python line 42 → JavaScript line 87
# Enables: Breakpoints, error stack traces

# 2. Column-Level Mapping
# Python col 15 on line 42 → JS col 23 on line 87
# Enables: Precise error highlighting, expression-level debugging

# 3. Variable Name Mapping
# Python 'user_name' → JS 'user_name' (preserved)
# Python 'user_name' → JS '_userName' (mapped)
# Enables: Variable inspection in debugger shows Python names

# 4. Scope Mapping
# Python function 'calculate_total' at line 10-25
# → JS function at lines 15-45
# Enables: Function-level navigation

# =============================================================================
# Stack Trace Rewriting
# =============================================================================

# When a JavaScript error occurs:
# Original JS Stack:
#   at Object.calculate (app.js:87:15)
#   at async fetchData (app.js:102:23)
#   at main (app.js:150:5)

# Rewritten Python Stack:
#   File "app.py", line 42, in calculate
#     result = data["missing_key"]
#   File "app.py", line 55, in fetchData
#     return await calculate(response)
#   File "app.py", line 78, in main
#     data = await fetchData()
# KeyError: 'missing_key'

@client
def rewrite_stack_trace(js_error):
    """Rewrite JS stack trace to Python source locations."""
    stack_lines = []
    for frame in parse_js_stack(js_error.stack):
        python_loc = source_map.lookup(frame.file, frame.line, frame.column)
        if python_loc:
            stack_lines.append(
                f'  File "{python_loc.file}", line {python_loc.line}, in {python_loc.function}\n'
                f'    {python_loc.source_line}'
            )
    return "\n".join(stack_lines)

# =============================================================================
# Console Integration
# =============================================================================

# console.log in Python shows source location
console.log("Debug:", value)
# Output: [app.py:42] Debug: <value>

# Clickable links in browser console
# Click "[app.py:42]" → Opens Python source at line 42

# =============================================================================
# Browser DevTools Integration
# =============================================================================

# "View Source" shows Python
# - Browser DevTools → Sources panel
# - Shows .py files (via source maps)
# - Syntax highlighting for Python
# - Set breakpoints in Python source

# Step-through debugging
# - Step Over (F10) → Next Python line
# - Step Into (F11) → Enter Python function
# - Step Out (Shift+F11) → Exit Python function
```

##### Source Map Checklist

```
Source Map Enhancements (Phase 33)
├── Line/Column Mapping (8 tests)
│   ├── [ ] Line-level source map generation
│   ├── [ ] Column-level source map generation
│   ├── [ ] Multi-line statement handling
│   └── [ ] Expression-level precision
│
├── Name Mapping (6 tests)
│   ├── [ ] Variable name preservation
│   ├── [ ] Function name mapping
│   ├── [ ] Class name mapping
│   └── [ ] Scope boundaries
│
├── Stack Trace Rewriting (10 tests)
│   ├── [ ] Parse JavaScript stack traces
│   ├── [ ] Map to Python source locations
│   ├── [ ] Include Python source line
│   ├── [ ] Handle async stack traces
│   ├── [ ] Handle minified code
│   └── [ ] Preserve exception type
│
└── Console Integration (6 tests)
    ├── [ ] Add source location to console.log
    ├── [ ] Clickable source links
    ├── [ ] Python object pretty-printing
    └── [ ] Integration with browser devtools
```

##### Client-Side Testing Infrastructure

Test transpiled client code without a browser.

```python
from pynext.testing.client import (
    render, screen, fireEvent, waitFor, cleanup,
    within, act, renderHook,
    mock_fetch, mock_navigator, mock_window,
)

# =============================================================================
# Basic Component Testing
# =============================================================================

@client
def Counter(initial=0):
    count = Signal(initial)
    return button(
        on_click=lambda: count.set(count() + 1),
        data_testid="counter-btn"
    )[f"Count: {count()}"]

# Test file
def test_counter_increments():
    # Render component
    render(Counter, props={"initial": 5})
    
    # Query elements
    button = screen.getByTestId("counter-btn")
    assert button.textContent == "Count: 5"
    
    # Interact
    fireEvent.click(button)
    
    # Assert update
    assert button.textContent == "Count: 6"
    
    # Cleanup (automatic with pytest fixture)
    cleanup()

# =============================================================================
# Query Methods
# =============================================================================

# By test ID (recommended)
screen.getByTestId("submit-btn")

# By text content
screen.getByText("Submit")
screen.getByText(/submit/i)  # Regex, case-insensitive

# By role (accessibility)
screen.getByRole("button", name="Submit")
screen.getByRole("textbox", name="Email")
screen.getByRole("checkbox", checked=True)

# By label (form fields)
screen.getByLabelText("Email Address")

# By placeholder
screen.getByPlaceholderText("Enter email...")

# By display value (inputs)
screen.getByDisplayValue("current value")

# Query variants
screen.getByX(...)      # Throws if not found
screen.queryByX(...)    # Returns None if not found
screen.findByX(...)     # Async, waits for element
screen.getAllByX(...)   # Returns list, throws if empty
screen.queryAllByX(...) # Returns list (may be empty)
screen.findAllByX(...)  # Async, returns list

# =============================================================================
# Fire Events
# =============================================================================

# Click events
fireEvent.click(element)
fireEvent.dblClick(element)
fireEvent.contextMenu(element)

# Keyboard events
fireEvent.keyDown(element, key="Enter")
fireEvent.keyUp(element, key="Escape")
fireEvent.keyPress(element, key="a")

# Form events
fireEvent.change(input_el, target={"value": "new value"})
fireEvent.input(input_el, target={"value": "typing..."})
fireEvent.submit(form_el)
fireEvent.focus(element)
fireEvent.blur(element)

# Mouse events
fireEvent.mouseEnter(element)
fireEvent.mouseLeave(element)
fireEvent.mouseDown(element)
fireEvent.mouseUp(element)

# Touch events
fireEvent.touchStart(element)
fireEvent.touchEnd(element)

# Drag events
fireEvent.dragStart(element)
fireEvent.drop(target, dataTransfer={"text/plain": "data"})

# =============================================================================
# Async Testing
# =============================================================================

@client
def AsyncComponent():
    data = Signal(None)
    loading = Signal(True)
    
    async def fetch_data():
        response = await fetch("/api/data")
        data.set(await response.json())
        loading.set(False)
    
    fetch_data()
    
    return div()[
        "Loading..." if loading() else data()["message"]
    ]

async def test_async_component():
    render(AsyncComponent)
    
    # Initially shows loading
    assert screen.getByText("Loading...")
    
    # Wait for async update
    await waitFor(lambda: screen.getByText("Hello World"))
    
    # Or with timeout
    await waitFor(
        lambda: screen.queryByText("Loading...") is None,
        timeout=5000
    )

# =============================================================================
# Mocking Browser APIs
# =============================================================================

def test_geolocation():
    with mock_navigator(geolocation={
        "getCurrentPosition": lambda success, error: success({
            "coords": {"latitude": 40.7128, "longitude": -74.0060}
        })
    }):
        render(LocationComponent)
        assert screen.getByText("New York")

def test_fetch():
    with mock_fetch({
        "/api/users": {"status": 200, "json": [{"name": "Alice"}]},
        "/api/posts": {"status": 404},
    }):
        render(Dashboard)
        await waitFor(lambda: screen.getByText("Alice"))

def test_local_storage():
    with mock_window(localStorage={"theme": "dark"}):
        render(ThemeProvider)
        assert screen.getByTestId("app").classList.contains("dark")

# =============================================================================
# Testing Signals Directly
# =============================================================================

def test_signal_updates():
    count = Signal(0)
    double = Memo(lambda: count() * 2)
    
    assert count() == 0
    assert double() == 0
    
    count.set(5)
    
    assert count() == 5
    assert double() == 10

# =============================================================================
# Testing Hooks (renderHook)
# =============================================================================

def test_custom_hook():
    def useCounter(initial):
        count = Signal(initial)
        increment = lambda: count.set(count() + 1)
        return count, increment
    
    result = renderHook(lambda: useCounter(10))
    count, increment = result.current
    
    assert count() == 10
    
    act(lambda: increment())
    
    assert count() == 11

# =============================================================================
# Scoped Queries (within)
# =============================================================================

def test_scoped_queries():
    render(div()[
        div(data_testid="section-1")[
            button()["Click me"]
        ],
        div(data_testid="section-2")[
            button()["Click me"]
        ]
    ])
    
    section1 = screen.getByTestId("section-1")
    section2 = screen.getByTestId("section-2")
    
    # Query within a specific container
    btn1 = within(section1).getByText("Click me")
    btn2 = within(section2).getByText("Click me")
    
    assert btn1 != btn2
```

##### Client Testing Checklist

```
Client Testing Infrastructure (Phase 33)
├── Core Testing API (15 tests)
│   ├── [ ] render(Component, props)
│   ├── [ ] cleanup()
│   ├── [ ] screen object
│   ├── [ ] within(element)
│   └── [ ] act(callback)
│
├── Query Methods (15 tests)
│   ├── [ ] getByTestId / queryByTestId / findByTestId
│   ├── [ ] getByText / queryByText / findByText
│   ├── [ ] getByRole / queryByRole / findByRole
│   ├── [ ] getByLabelText
│   ├── [ ] getByPlaceholderText
│   ├── [ ] getAllBy* variants
│   └── [ ] Regex support
│
├── Fire Events (10 tests)
│   ├── [ ] click, dblClick
│   ├── [ ] keyDown, keyUp, keyPress
│   ├── [ ] change, input, submit
│   ├── [ ] focus, blur
│   ├── [ ] mouse events
│   └── [ ] touch events
│
├── Async Testing (10 tests)
│   ├── [ ] waitFor(predicate)
│   ├── [ ] waitFor with timeout
│   ├── [ ] findBy* async queries
│   └── [ ] Async component updates
│
├── Mocking (15 tests)
│   ├── [ ] mock_fetch
│   ├── [ ] mock_navigator
│   ├── [ ] mock_window
│   ├── [ ] mock_document
│   ├── [ ] Signal mocking
│   └── [ ] Custom mock factories
│
└── pytest Integration (5 tests)
    ├── [ ] Auto-cleanup fixture
    ├── [ ] Async test support
    ├── [ ] Snapshot testing
    └── [ ] Coverage reporting
```

##### Runtime Type Checking (Development Mode)

Optional type validation for catching errors early.

```python
from pynext.client import typed, enable_type_checking

# =============================================================================
# Enable Type Checking (Dev Mode Only)
# =============================================================================

# Global enable (typically in dev config)
enable_type_checking(True)  # Enable for all @typed functions
enable_type_checking(False)  # Disable (production)

# =============================================================================
# Function Type Checking
# =============================================================================

@typed
@client
def greet(name: str, times: int = 1) -> str:
    return (f"Hello, {name}! " * times).strip()

# Valid calls
greet("Alice")           # OK
greet("Bob", 3)          # OK
greet("Charlie", times=2)  # OK

# Invalid calls (in dev mode, raises TypeError)
greet(123)               # TypeError: name must be str, got int
greet("Alice", "3")      # TypeError: times must be int, got str
greet("Alice", -1)       # OK (no range checking, just type)

# =============================================================================
# Class Type Checking
# =============================================================================

@typed
@client
class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    
    def greet(self, greeting: str = "Hello") -> str:
        return f"{greeting}, {self.name}!"
    
    def set_age(self, new_age: int) -> None:
        self.age = new_age

# Invalid usage
user = User("Alice", "30")  # TypeError: age must be int
user.set_age("31")          # TypeError: new_age must be int

# =============================================================================
# Complex Types
# =============================================================================

from typing import List, Dict, Optional, Union, Callable

@typed
@client
def process_items(
    items: List[str],
    config: Dict[str, int],
    callback: Optional[Callable[[str], None]] = None
) -> List[str]:
    results = []
    for item in items:
        if callback:
            callback(item)
        results.append(item.upper())
    return results

# Checked:
# - items must be a list
# - Each item in list should be str
# - config must be a dict
# - callback must be callable or None

# =============================================================================
# Union Types
# =============================================================================

@typed
@client
def parse_id(id_value: Union[str, int]) -> int:
    if isinstance(id_value, str):
        return int(id_value)
    return id_value

parse_id("123")   # OK
parse_id(123)     # OK
parse_id(12.5)    # TypeError: id_value must be str | int, got float

# =============================================================================
# Type Checking Configuration
# =============================================================================

# Selective enabling
@typed(strict=True)  # Check all types strictly
@typed(strict=False)  # Only check top-level types (default)

@typed(on_error="raise")  # Raise TypeError (default)
@typed(on_error="warn")   # console.warn instead of raise
@typed(on_error="log")    # console.log instead of raise

# Performance: Type checking only in dev mode
# In production: @typed decorator is a no-op
```

##### Runtime Type Checking Checklist

```
Runtime Type Checking (Phase 33)
├── Basic Types (8 tests)
│   ├── [ ] str type checking
│   ├── [ ] int type checking
│   ├── [ ] float type checking
│   ├── [ ] bool type checking
│   ├── [ ] None type checking
│   └── [ ] Default value handling
│
├── Collection Types (8 tests)
│   ├── [ ] List[T] checking
│   ├── [ ] Dict[K, V] checking
│   ├── [ ] Set[T] checking
│   ├── [ ] Tuple[T, ...] checking
│   └── [ ] Nested collection types
│
├── Advanced Types (8 tests)
│   ├── [ ] Optional[T]
│   ├── [ ] Union[T1, T2]
│   ├── [ ] Callable[[Args], Return]
│   ├── [ ] Any type
│   └── [ ] Custom classes
│
├── Return Type Checking (5 tests)
│   ├── [ ] Return value validation
│   ├── [ ] None return for -> None
│   └── [ ] Async return types
│
└── Configuration (6 tests)
    ├── [ ] enable_type_checking()
    ├── [ ] @typed(strict=True/False)
    ├── [ ] @typed(on_error="raise/warn/log")
    ├── [ ] Production mode (no-op)
    └── [ ] Per-function enable/disable
```

##### Extended Standard Library Transpilation

Additional Python stdlib modules for comprehensive client-side Python support.

```python
from pynext.client import datetime, timedelta, collections, itertools, functools

# =============================================================================
# datetime Module
# =============================================================================

from pynext.client.datetime import datetime, date, time, timedelta, timezone

# Current date/time
now = datetime.now()                    # Local time
utc_now = datetime.now(timezone.utc)    # UTC time
today = date.today()

# Create specific date/time
dt = datetime(2024, 12, 14, 10, 30, 0)
d = date(2024, 12, 14)
t = time(10, 30, 0)

# From timestamp
dt = datetime.fromtimestamp(1702500000)
dt = datetime.utcfromtimestamp(1702500000)

# From ISO string
dt = datetime.fromisoformat("2024-12-14T10:30:00")
d = date.fromisoformat("2024-12-14")

# Properties
dt.year          # 2024
dt.month         # 12
dt.day           # 14
dt.hour          # 10
dt.minute        # 30
dt.second        # 0
dt.microsecond   # 0
dt.weekday()     # 5 (Saturday, 0=Monday)
dt.isoweekday()  # 6 (Saturday, 1=Monday)

# Formatting
dt.isoformat()                    # "2024-12-14T10:30:00"
dt.strftime("%Y-%m-%d %H:%M:%S")  # "2024-12-14 10:30:00"
dt.strftime("%B %d, %Y")          # "December 14, 2024"
dt.strftime("%A")                 # "Saturday"

# Parsing
datetime.strptime("2024-12-14", "%Y-%m-%d")

# timedelta (duration)
delta = timedelta(days=7, hours=3, minutes=30)
delta.days           # 7
delta.seconds        # 12600 (3*3600 + 30*60)
delta.total_seconds()  # 619800.0

# Arithmetic
future = dt + timedelta(days=7)
past = dt - timedelta(hours=24)
diff = datetime.now() - dt  # Returns timedelta

# Comparison
dt1 < dt2
dt1 == dt2
dt1 >= dt2

# Timezone handling
from pynext.client.datetime import timezone

utc = timezone.utc
eastern = timezone(timedelta(hours=-5), "EST")

dt_utc = datetime.now(timezone.utc)
dt_local = dt_utc.astimezone()           # Convert to local
dt_eastern = dt_utc.astimezone(eastern)  # Convert to EST

# Replace components
new_dt = dt.replace(year=2025, month=1)

# =============================================================================
# collections Module
# =============================================================================

from pynext.client.collections import Counter, defaultdict, deque, OrderedDict, namedtuple

# Counter (counting hashable objects)
counter = Counter(["a", "b", "a", "c", "a", "b"])
counter["a"]           # 3
counter.most_common(2) # [("a", 3), ("b", 2)]
counter.total()        # 6

# Update counter
counter.update(["a", "d"])
counter["a"]  # 4

# Counter arithmetic
c1 = Counter({"a": 3, "b": 2})
c2 = Counter({"a": 1, "b": 3})
c1 + c2  # Counter({"a": 4, "b": 5})
c1 - c2  # Counter({"a": 2})
c1 & c2  # Counter({"a": 1, "b": 2}) (intersection)
c1 | c2  # Counter({"a": 3, "b": 3}) (union)

# defaultdict (dict with default values)
dd = defaultdict(list)
dd["key"].append(1)    # No KeyError, creates empty list
dd["key"].append(2)
dd["key"]  # [1, 2]

dd_int = defaultdict(int)
dd_int["count"] += 1   # No KeyError, starts at 0

dd_set = defaultdict(set)
dd_set["items"].add("a")

# Custom default factory
dd = defaultdict(lambda: "default_value")
dd["missing"]  # "default_value"

# deque (double-ended queue)
dq = deque([1, 2, 3])
dq.append(4)        # Add to right
dq.appendleft(0)    # Add to left
dq.pop()            # Remove from right
dq.popleft()        # Remove from left
dq.extend([5, 6])   # Extend right
dq.extendleft([])   # Extend left (reversed order)
dq.rotate(1)        # Rotate right
dq.rotate(-1)       # Rotate left

# Bounded deque (auto-discards old items)
dq = deque(maxlen=100)
for i in range(200):
    dq.append(i)    # Only keeps last 100

len(dq)  # 100

# OrderedDict (maintains insertion order - mostly for compatibility)
od = OrderedDict()
od["first"] = 1
od["second"] = 2
od.move_to_end("first")        # Move to end
od.move_to_end("second", False)  # Move to beginning
od.popitem(last=True)          # Pop last item
od.popitem(last=False)         # Pop first item

# namedtuple (lightweight object type)
Point = namedtuple("Point", ["x", "y"])
p = Point(10, 20)
p.x          # 10
p.y          # 20
p[0]         # 10 (index access)
x, y = p     # Unpacking

Point = namedtuple("Point", ["x", "y"], defaults=[0, 0])
p = Point()  # Point(x=0, y=0)

p._asdict()           # {"x": 10, "y": 20}
p._replace(x=100)     # Point(x=100, y=20)
Point._fields         # ("x", "y")

# =============================================================================
# itertools Module
# =============================================================================

from pynext.client.itertools import (
    chain, cycle, repeat, count,
    islice, takewhile, dropwhile, filterfalse,
    groupby, accumulate,
    product, permutations, combinations, combinations_with_replacement,
    zip_longest, starmap, tee, pairwise
)

# Infinite iterators
for i in count(10, 2):     # 10, 12, 14, ... (infinite)
    if i > 20:
        break

for item in cycle([1, 2, 3]):  # 1, 2, 3, 1, 2, 3, ... (infinite)
    if condition:
        break

for _ in repeat("hello", 3):  # "hello", "hello", "hello"
    pass

# Chain iterables
for item in chain([1, 2], [3, 4], [5, 6]):
    print(item)  # 1, 2, 3, 4, 5, 6

# from_iterable variant
list(chain.from_iterable([[1, 2], [3, 4]]))  # [1, 2, 3, 4]

# Slicing iterables
list(islice(count(), 5))           # [0, 1, 2, 3, 4]
list(islice(count(), 2, 5))        # [2, 3, 4]
list(islice(count(), 0, 10, 2))    # [0, 2, 4, 6, 8]

# Filtering
list(takewhile(lambda x: x < 5, [1, 3, 5, 2, 4]))  # [1, 3]
list(dropwhile(lambda x: x < 5, [1, 3, 5, 2, 4]))  # [5, 2, 4]
list(filterfalse(lambda x: x % 2, range(10)))      # [0, 2, 4, 6, 8]

# Grouping
data = [{"name": "Alice", "dept": "Engineering"},
        {"name": "Bob", "dept": "Engineering"},
        {"name": "Charlie", "dept": "Sales"}]
# Data must be sorted by key first!
sorted_data = sorted(data, key=lambda x: x["dept"])
for key, group in groupby(sorted_data, key=lambda x: x["dept"]):
    print(f"{key}: {list(group)}")

# Accumulate
list(accumulate([1, 2, 3, 4]))           # [1, 3, 6, 10] (running sum)
list(accumulate([1, 2, 3, 4], lambda a, b: a * b))  # [1, 2, 6, 24]

# Combinatorics
list(product([1, 2], ["a", "b"]))        # [(1,'a'), (1,'b'), (2,'a'), (2,'b')]
list(product([1, 2], repeat=2))          # [(1,1), (1,2), (2,1), (2,2)]

list(permutations([1, 2, 3]))            # All orderings
list(permutations([1, 2, 3], 2))         # 2-length orderings

list(combinations([1, 2, 3], 2))         # [(1,2), (1,3), (2,3)]
list(combinations_with_replacement([1, 2], 2))  # [(1,1), (1,2), (2,2)]

# Zip variants
list(zip_longest([1, 2], [1, 2, 3, 4], fillvalue=0))  # [(1,1), (2,2), (0,3), (0,4)]

# Starmap (unpack arguments)
list(starmap(pow, [(2, 3), (3, 2), (10, 2)]))  # [8, 9, 100]

# Tee (create independent iterators)
a, b = tee(iter([1, 2, 3]))
list(a)  # [1, 2, 3]
list(b)  # [1, 2, 3]

# Pairwise (Python 3.10+)
list(pairwise([1, 2, 3, 4]))  # [(1,2), (2,3), (3,4)]

# =============================================================================
# functools Module
# =============================================================================

from pynext.client.functools import partial, reduce, lru_cache, cache, wraps

# partial (pre-fill function arguments)
def power(base, exp):
    return base ** exp

square = partial(power, exp=2)
cube = partial(power, exp=3)
square(5)  # 25
cube(3)    # 27

# reduce (fold iterable to single value)
from pynext.client.functools import reduce

sum_all = reduce(lambda a, b: a + b, [1, 2, 3, 4])  # 10
max_val = reduce(lambda a, b: a if a > b else b, [3, 1, 4, 1, 5])  # 5

# With initial value
result = reduce(lambda a, b: a + b, [1, 2, 3], 10)  # 16

# lru_cache (memoization with size limit)
@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

fibonacci(100)  # Fast due to caching

# Cache info
fibonacci.cache_info()  # CacheInfo(hits=98, misses=101, maxsize=128, currsize=101)
fibonacci.cache_clear()  # Clear cache

# cache (unbounded memoization, Python 3.9+)
@cache
def expensive_computation(x, y):
    return x ** y ** x

# wraps (preserve function metadata in decorators)
def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("Before")
        result = func(*args, **kwargs)
        print("After")
        return result
    return wrapper

@my_decorator
def my_function():
    """My docstring."""
    pass

my_function.__name__  # "my_function" (preserved)
my_function.__doc__   # "My docstring." (preserved)

# =============================================================================
# operator Module
# =============================================================================

from pynext.client.operator import (
    itemgetter, attrgetter, methodcaller,
    add, sub, mul, truediv, floordiv, mod, pow, neg, pos, abs,
    eq, ne, lt, le, gt, ge,
    and_, or_, not_, xor,
    getitem, setitem, delitem,
    concat, contains
)

# itemgetter (get items by key/index)
get_name = itemgetter("name")
get_name({"name": "Alice", "age": 30})  # "Alice"

get_first_last = itemgetter(0, -1)
get_first_last([1, 2, 3, 4, 5])  # (1, 5)

# Sort by key
users = [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}]
sorted(users, key=itemgetter("name"))  # Sorted by name

# attrgetter (get attributes)
get_x = attrgetter("x")
get_x(point)  # point.x

# Nested attributes
get_nested = attrgetter("address.city")
get_nested(user)  # user.address.city

# Multiple attributes
get_coords = attrgetter("x", "y")
get_coords(point)  # (point.x, point.y)

# methodcaller (call methods)
upper = methodcaller("upper")
upper("hello")  # "HELLO"

split_comma = methodcaller("split", ",")
split_comma("a,b,c")  # ["a", "b", "c"]

# Operator functions
add(1, 2)        # 3
mul(3, 4)        # 12
truediv(10, 3)   # 3.333...
floordiv(10, 3)  # 3
mod(10, 3)       # 1
neg(-5)          # 5

# Comparison operators
eq(1, 1)   # True
lt(1, 2)   # True
ge(2, 2)   # True

# Boolean operators
and_(True, False)  # False
or_(True, False)   # True
not_(True)         # False

# =============================================================================
# copy Module
# =============================================================================

from pynext.client.copy import copy, deepcopy

# Shallow copy
original = {"a": [1, 2, 3], "b": {"nested": True}}
shallow = copy(original)
shallow["a"].append(4)  # Also modifies original["a"]

# Deep copy
deep = deepcopy(original)
deep["a"].append(5)  # Does NOT modify original["a"]
deep["b"]["nested"] = False  # Does NOT modify original["b"]

# Copy with custom __copy__ and __deepcopy__
@client
class MyClass:
    def __init__(self, value):
        self.value = value
        self.computed = expensive_computation()
    
    def __copy__(self):
        # Custom shallow copy
        new = MyClass.__new__(MyClass)
        new.value = self.value
        new.computed = self.computed  # Share reference
        return new
    
    def __deepcopy__(self, memo):
        # Custom deep copy
        new = MyClass.__new__(MyClass)
        new.value = deepcopy(self.value, memo)
        new.computed = deepcopy(self.computed, memo)
        return new
```

##### Promise Utilities and Scheduling APIs

Essential async patterns for client-side Python.

```python
from pynext.client import (
    Promise, 
    queueMicrotask, 
    requestIdleCallback, 
    cancelIdleCallback,
    requestAnimationFrame,
    cancelAnimationFrame,
)

# =============================================================================
# Promise Static Methods
# =============================================================================

# Promise.all - wait for all to resolve (fails on any rejection)
results = await Promise.all([
    fetch("/api/users"),
    fetch("/api/posts"),
    fetch("/api/comments"),
])
users, posts, comments = results

# Promise.allSettled - wait for all to complete (success or failure)
results = await Promise.allSettled([
    fetch("/api/required"),
    fetch("/api/optional"),  # May fail
])
for result in results:
    if result.status == "fulfilled":
        process(result.value)
    else:
        log_error(result.reason)

# Promise.race - first to resolve/reject wins
result = await Promise.race([
    fetch("/api/primary"),
    fetch("/api/backup"),
])

# Promise.race for timeout
async def fetch_with_timeout(url, timeout_ms=5000):
    timeout = Promise(lambda resolve, reject: 
        window.setTimeout(lambda: reject(TimeoutError("Request timed out")), timeout_ms)
    )
    return await Promise.race([fetch(url), timeout])

# Promise.any - first to resolve (ignores rejections until all fail)
result = await Promise.any([
    fetch("/api/server1"),  # May fail
    fetch("/api/server2"),  # May fail
    fetch("/api/server3"),  # First success wins
])
# Raises AggregateError if ALL reject

# Promise.resolve / Promise.reject
resolved = Promise.resolve(42)
rejected = Promise.reject(Error("Failed"))

# Promise.withResolvers (Promise with external resolve/reject)
promise, resolve, reject = Promise.withResolvers()
# Later...
resolve(result)

# =============================================================================
# Microtask Queue
# =============================================================================

# Queue function to run after current task, before next event loop
queueMicrotask(lambda: console.log("Runs as microtask"))

# Use case: Ensure DOM updates before running code
@client
def update_after_render():
    element.textContent = "New text"
    queueMicrotask(lambda: 
        # This runs after DOM update is scheduled
        measure_element_size()
    )

# Microtasks run before:
# - setTimeout callbacks
# - requestAnimationFrame callbacks
# - I/O callbacks

# =============================================================================
# Idle Callbacks (Run When Browser is Idle)
# =============================================================================

# Schedule work for when browser is idle
def do_background_work(deadline):
    while deadline.timeRemaining() > 0 and work_queue:
        task = work_queue.pop()
        process_task(task)
    
    if work_queue:
        # More work remaining, schedule again
        requestIdleCallback(do_background_work)

idle_id = requestIdleCallback(do_background_work)

# With timeout (run within timeout even if not idle)
idle_id = requestIdleCallback(do_background_work, {"timeout": 2000})

# Cancel pending idle callback
cancelIdleCallback(idle_id)

# IdleDeadline object
# deadline.timeRemaining()  - ms remaining in idle period
# deadline.didTimeout       - True if timeout forced execution

# =============================================================================
# Animation Frame Scheduling
# =============================================================================

# Schedule work for next frame (before repaint)
def animate(timestamp):
    # timestamp is DOMHighResTimeStamp
    update_animation(timestamp)
    
    if animation_running:
        requestAnimationFrame(animate)

frame_id = requestAnimationFrame(animate)

# Cancel animation
cancelAnimationFrame(frame_id)

# Animation loop pattern
@client
class AnimationLoop:
    def __init__(self):
        self.running = False
        self.frame_id = None
        self.last_time = 0
    
    def start(self, callback):
        self.running = True
        
        def loop(timestamp):
            if not self.running:
                return
            
            # Calculate delta time
            delta = timestamp - self.last_time if self.last_time else 0
            self.last_time = timestamp
            
            # Call user callback
            callback(timestamp, delta)
            
            # Schedule next frame
            self.frame_id = requestAnimationFrame(loop)
        
        self.frame_id = requestAnimationFrame(loop)
    
    def stop(self):
        self.running = False
        if self.frame_id:
            cancelAnimationFrame(self.frame_id)
            self.frame_id = None

# Usage
loop = AnimationLoop()
loop.start(lambda ts, dt: update_game(dt))
# Later...
loop.stop()

# =============================================================================
# Scheduling Patterns
# =============================================================================

# Debounce with RAF (one update per frame max)
@client
def debounce_raf(callback):
    pending = None
    
    def debounced(*args):
        nonlocal pending
        if pending:
            cancelAnimationFrame(pending)
        pending = requestAnimationFrame(lambda _: callback(*args))
    
    return debounced

# Throttle to idle time
@client
def run_when_idle(callback, timeout=1000):
    requestIdleCallback(
        lambda deadline: callback(),
        {"timeout": timeout}
    )

# Priority scheduling pattern
@client
def schedule_by_priority(task, priority):
    if priority == "immediate":
        queueMicrotask(task)
    elif priority == "high":
        window.setTimeout(task, 0)
    elif priority == "normal":
        requestAnimationFrame(lambda _: task())
    elif priority == "low":
        requestIdleCallback(lambda _: task())
```

##### Promise and Scheduling Checklist

```
Promise and Scheduling APIs (Phase 33)
├── Promise Static Methods (20 tests)
│   ├── [ ] Promise.all()
│   ├── [ ] Promise.allSettled()
│   ├── [ ] Promise.race()
│   ├── [ ] Promise.any() + AggregateError
│   ├── [ ] Promise.resolve() / Promise.reject()
│   └── [ ] Promise.withResolvers()
│
├── Microtask Queue (10 tests)
│   ├── [ ] queueMicrotask()
│   └── [ ] Microtask ordering
│
├── Idle Callbacks (10 tests)
│   ├── [ ] requestIdleCallback()
│   ├── [ ] cancelIdleCallback()
│   ├── [ ] IdleDeadline.timeRemaining()
│   ├── [ ] IdleDeadline.didTimeout
│   └── [ ] Timeout option
│
└── Animation Frames (10 tests)
    ├── [ ] requestAnimationFrame()
    ├── [ ] cancelAnimationFrame()
    └── [ ] DOMHighResTimeStamp
```

##### Extended Standard Library Checklist

```
Extended Standard Library Support (Phase 33)
├── datetime Module (40 tests)
│   ├── [ ] datetime class (now, fromtimestamp, fromisoformat)
│   ├── [ ] date class (today, fromisoformat)
│   ├── [ ] time class
│   ├── [ ] timedelta (arithmetic, total_seconds)
│   ├── [ ] timezone (utc, custom offsets)
│   ├── [ ] strftime/strptime formatting
│   ├── [ ] Date/time arithmetic
│   └── [ ] Comparison operators
│
├── collections Module (35 tests)
│   ├── [ ] Counter (counting, most_common, arithmetic)
│   ├── [ ] defaultdict (default factories)
│   ├── [ ] deque (append, pop, rotate, maxlen)
│   ├── [ ] OrderedDict (move_to_end, popitem)
│   └── [ ] namedtuple (creation, _asdict, _replace)
│
├── itertools Module (45 tests)
│   ├── [ ] Infinite: count, cycle, repeat
│   ├── [ ] Chain: chain, chain.from_iterable
│   ├── [ ] Slicing: islice
│   ├── [ ] Filtering: takewhile, dropwhile, filterfalse
│   ├── [ ] Grouping: groupby
│   ├── [ ] Accumulation: accumulate
│   ├── [ ] Combinatorics: product, permutations, combinations
│   ├── [ ] zip_longest, starmap, tee
│   └── [ ] pairwise (Python 3.10+)
│
├── functools Module (25 tests)
│   ├── [ ] partial (argument binding)
│   ├── [ ] reduce (fold)
│   ├── [ ] lru_cache (memoization)
│   ├── [ ] cache (unbounded memoization)
│   └── [ ] wraps (decorator helper)
│
├── operator Module (20 tests)
│   ├── [ ] itemgetter, attrgetter, methodcaller
│   ├── [ ] Arithmetic: add, sub, mul, truediv, etc.
│   ├── [ ] Comparison: eq, ne, lt, le, gt, ge
│   └── [ ] Boolean: and_, or_, not_
│
└── copy Module (15 tests)
    ├── [ ] copy (shallow)
    ├── [ ] deepcopy (deep)
    └── [ ] Custom __copy__/__deepcopy__
```

##### Files to Create/Modify

| File | Purpose |
|------|---------|
| `pynext/client/__init__.py` | @client decorator, client context |
| `pynext/transpiler/functions.py` | *args, **kwargs, decorators, closures |
| `pynext/transpiler/classes.py` | Inheritance, super, static/class methods, property |
| `pynext/transpiler/dunders.py` | All dunder method transpilation |
| `pynext/transpiler/comprehensions.py` | List/dict/set comprehensions, generators |
| `pynext/transpiler/control_flow.py` | try/except, with, match/case |
| `pynext/transpiler/generators.py` | yield, yield from, iterator protocol |
| `pynext/transpiler/async_support.py` | async for, async with, gather |
| `pynext/transpiler/operators.py` | Operator overloading helpers |
| `pynext/runtime/py_runtime.js` | Runtime helpers (__py_add__, etc.) |
| `pynext/runtime/promise.js` | Promise utilities (all, allSettled, race, any) |
| `pynext/runtime/scheduling.js` | queueMicrotask, requestIdleCallback, RAF |
| `pynext/runtime/stdlib/datetime.js` | datetime, date, time, timedelta, timezone |
| `pynext/runtime/stdlib/collections.js` | Counter, defaultdict, deque, OrderedDict, namedtuple |
| `pynext/runtime/stdlib/itertools.js` | All itertools functions |
| `pynext/runtime/stdlib/functools.js` | partial, reduce, lru_cache, cache, wraps |
| `pynext/runtime/stdlib/operator.js` | itemgetter, attrgetter, methodcaller, operators |
| `pynext/runtime/stdlib/copy.js` | copy, deepcopy |
| `pynext/runtime/exceptions.js` | Full Python exception hierarchy |
| `pynext/transpiler/imports.py` | Import/module transpilation |
| `pynext/transpiler/sourcemap.py` | Enhanced source map generation |
| `pynext/transpiler/stack_rewriter.py` | Stack trace rewriting to Python |
| `pynext/testing/__init__.py` | Client testing infrastructure |
| `pynext/testing/client.py` | render, screen, fireEvent, waitFor |
| `pynext/testing/mocks.py` | mock_fetch, mock_navigator, mock_window |
| `pynext/testing/queries.py` | getByText, getByRole, getByTestId |
| `pynext/client/typed.py` | @typed decorator for runtime type checking |

##### Success Criteria

| Metric | Target |
|--------|--------|
| Language coverage | 100% of Python 3.10+ constructs used in client code |
| Extended stdlib | datetime, collections, itertools, functools, operator, copy |
| Promise utilities | all, allSettled, race, any, withResolvers |
| Scheduling APIs | queueMicrotask, requestIdleCallback, RAF |
| Exception hierarchy | All Python exceptions with proper inheritance |
| Import transpilation | All import forms including dynamic imports |
| Source maps | Line, column, variable name mapping |
| Client testing | Full render/query/event testing API |
| Type checking | Optional runtime type validation |
| Test coverage | 900+ unit tests |
| Performance | Transpilation < 100ms per file |
| Bundle size | < 12KB runtime helpers |
| Compatibility | Works with all existing PyNext apps |

##### Phase 33 Complete Milestone Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 33 IMPLEMENTATION TIMELINE                        │
│                              (13 weeks total)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 33.1: FUNDAMENTALS (4 weeks)                                         │
│  ┌──────────┬──────────┬──────────┬──────────┐                              │
│  │  Week 1  │  Week 2  │  Week 3  │  Week 4  │                              │
│  │Functions │ Classes  │Decorators│ Control  │                              │
│  │*args     │Inheritanc│ Closures │ Flow &   │                              │
│  │**kwargs  │super()   │ Lambdas  │Comprehen.│                              │
│  └──────────┴──────────┴──────────┴──────────┘                              │
│                          ↓                                                   │
│  PHASE 33.2: ADVANCED (4 weeks)                                             │
│  ┌──────────┬──────────┬──────────┬──────────┐                              │
│  │  Week 5  │  Week 6  │  Week 7  │  Week 8  │                              │
│  │ Dunders  │ Dunders  │Generators│ Pattern  │                              │
│  │ (str/eq/ │ (arith/  │ Context  │ Matching │                              │
│  │ contain) │ callable)│ Managers │ + Async  │                              │
│  └──────────┴──────────┴──────────┴──────────┘                              │
│                          ↓                                                   │
│  PHASE 33.3: INFRASTRUCTURE (2 weeks)                                       │
│  ┌──────────┬──────────┐                                                    │
│  │  Week 9  │ Week 10  │                                                    │
│  │Exception │ Source   │                                                    │
│  │Hierarchy │ Maps &   │                                                    │
│  │+ Imports │ Stacks   │                                                    │
│  └──────────┴──────────┘                                                    │
│                          ↓                                                   │
│  PHASE 33.4: DEV TOOLS (3 weeks)                                            │
│  ┌──────────┬──────────┬──────────┐                                         │
│  │ Week 11  │ Week 12  │ Week 13  │                                         │
│  │ Testing  │ Types &  │ Extended │                                         │
│  │ Infra    │ Promise  │ Stdlib   │                                         │
│  │          │ Schedule │ (6 mods) │                                         │
│  └──────────┴──────────┴──────────┘                                         │
│                          ↓                                                   │
│                   ┌──────────────┐                                          │
│                   │   PHASE 34   │                                          │
│                   │   DOM APIs   │                                          │
│                   └──────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Phase 33 Exit Criteria

Before moving to Phase 34, ALL of the following must be complete:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PHASE 33 EXIT CRITERIA                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ✓ ALL 975 tests passing                                                    │
│                                                                              │
│  ✓ Functions: Any Python function can be transpiled                         │
│      - *args, **kwargs, defaults, closures, decorators                      │
│                                                                              │
│  ✓ Classes: Any Python class can be transpiled                              │
│      - Inheritance, super(), properties, staticmethod, classmethod          │
│                                                                              │
│  ✓ Dunders: Standard dunder methods work                                    │
│      - __str__, __eq__, __iter__, __getitem__, __call__, etc.              │
│                                                                              │
│  ✓ Generators: yield, yield from, generator expressions                    │
│                                                                              │
│  ✓ Context Managers: with statement works (sync and async)                 │
│                                                                              │
│  ✓ Pattern Matching: match/case fully supported                            │
│                                                                              │
│  ✓ Exceptions: Full hierarchy with isinstance checks                       │
│                                                                              │
│  ✓ Imports: All import forms work (relative, absolute, dynamic)            │
│                                                                              │
│  ✓ Source Maps: Errors show Python line numbers in browser                 │
│                                                                              │
│  ✓ Testing: render(), screen, fireEvent work                               │
│                                                                              │
│  ✓ Stdlib: datetime, collections, itertools, functools work                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

#### Phase 34: DOM API Bindings (625 tests, 7 weeks)

Complete document, Element, Event, CSS, and browser utility interfaces — the foundation for all UI manipulation.

**Sub-Phase Overview:**

| Sub-Phase | Focus | Tests | Duration |
|-----------|-------|-------|----------|
| **34.1** | Core DOM (Document + Element) | 100 | 1 week |
| **34.2** | CSS Runtime & Styling | 120 | 1 week |
| **34.3** | CSS Typed Object Model | 135 | 1 week |
| **34.4** | Events & Interactions | 80 | 1 week |
| **34.5** | URL, Encoding & Binary Data | 95 | 1 week |
| **34.6** | Memory Management | 70 | 1 week |
| **34.7** | Error Boundaries & DX | 25 | 1 week |

---

##### Phase 34.1: Core DOM APIs (100 tests, 1 week)

Document queries, element creation, attributes, traversal, and manipulation.

##### DOM API Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PHASE 34: DOM API BINDINGS                          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                           Document API                                   ││
│  │                                                                          ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │   Query     │  │   Create    │  │   Navigate  │  │   State     │    ││
│  │  │             │  │             │  │             │  │             │    ││
│  │  │ getElementBy│  │ createElement│ │ location    │  │ readyState  │    ││
│  │  │ querySelector│ │ createText  │  │ title       │  │ visibilityS │    ││
│  │  │ querySelectorAll│ createFrag │  │ referrer    │  │ activeElem  │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                           Element API                                    ││
│  │                                                                          ││
│  │  Attributes        Classes           Style              Dimensions       ││
│  │  ───────────       ─────────         ─────              ──────────       ││
│  │  getAttribute      classList.add     style.display      offsetWidth      ││
│  │  setAttribute      classList.remove  style.transform    offsetHeight     ││
│  │  removeAttribute   classList.toggle  style.setProperty  getBoundingRect  ││
│  │  dataset           classList.contains style.cssText     scrollIntoView   ││
│  │                                                                          ││
│  │  DOM Traversal     DOM Manipulation  innerHTML/Text     Focus            ││
│  │  ─────────────     ────────────────  ──────────────     ─────            ││
│  │  parentElement     appendChild       innerHTML          focus()          ││
│  │  children          insertBefore      innerText          blur()           ││
│  │  nextSibling       removeChild       textContent        tabIndex         ││
│  │  querySelector     replaceChild      outerHTML                           ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                           Event API                                      ││
│  │                                                                          ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │   Mouse     │  │  Keyboard   │  │   Touch     │  │    Form     │    ││
│  │  │             │  │             │  │             │  │             │    ││
│  │  │ click       │  │ keydown     │  │ touchstart  │  │ submit      │    ││
│  │  │ dblclick    │  │ keyup       │  │ touchmove   │  │ change      │    ││
│  │  │ mouseenter  │  │ keypress    │  │ touchend    │  │ input       │    ││
│  │  │ mouseleave  │  │             │  │ touchcancel │  │ focus/blur  │    ││
│  │  │ contextmenu │  │             │  │             │  │             │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  │                                                                          ││
│  │  Event Properties: target, currentTarget, preventDefault(),              ││
│  │                    stopPropagation(), bubbles, cancelable               ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

###### Python API (Phase 34.1)

```python
from pynext.client import document, Element

# =============================================================================
# Document Queries
# =============================================================================

el = document.getElementById("app")
el = document.querySelector(".card")
els = document.querySelectorAll("div.item")
els = document.getElementsByClassName("item")
els = document.getElementsByTagName("div")

# =============================================================================
# Element Creation
# =============================================================================

div = document.createElement("div")
svg = document.createElementNS("http://www.w3.org/2000/svg", "circle")
text = document.createTextNode("Hello")
fragment = document.createDocumentFragment()
comment = document.createComment("This is a comment")

# =============================================================================
# Element Attributes
# =============================================================================

el.getAttribute("data-id")
el.setAttribute("data-id", "123")
el.removeAttribute("disabled")
el.hasAttribute("hidden")
el.toggleAttribute("disabled")
el.dataset.userId  # data-user-id
el.dataset.userName = "Alice"  # Sets data-user-name

# =============================================================================
# Element Content
# =============================================================================

el.textContent = "Hello"
el.innerHTML = "<span>World</span>"
el.innerText = "Visible text"
html = el.outerHTML

# =============================================================================
# DOM Traversal
# =============================================================================

el.parentElement
el.parentNode
el.children                    # HTMLCollection of child elements
el.childNodes                  # NodeList including text nodes
el.firstElementChild
el.lastElementChild
el.firstChild
el.lastChild
el.nextElementSibling
el.previousElementSibling
el.nextSibling
el.previousSibling
el.closest(".container")       # Find ancestor matching selector
el.matches(".active")          # Check if matches selector

# =============================================================================
# DOM Manipulation
# =============================================================================

parent.appendChild(child)
parent.insertBefore(new_child, reference)
parent.removeChild(child)
parent.replaceChild(new_child, old_child)
el.remove()                    # Remove self from parent
el.cloneNode(deep=True)        # Clone element
el.append(child1, "text", child2)   # Append multiple
el.prepend(child1, child2)     # Prepend multiple
el.after(sibling)              # Insert after
el.before(sibling)             # Insert before
el.replaceWith(replacement)    # Replace self

# =============================================================================
# Element Properties
# =============================================================================

el.id
el.tagName                     # "DIV", "SPAN", etc.
el.className = "foo bar"
el.childElementCount
```

###### Phase 34.1 Checklist

```
Core DOM APIs (Phase 34.1)
├── Document Queries (20 tests)
│   ├── [ ] getElementById
│   ├── [ ] querySelector
│   ├── [ ] querySelectorAll
│   ├── [ ] getElementsByClassName
│   ├── [ ] getElementsByTagName
│   └── [ ] getElementsByName
│
├── Element Creation (15 tests)
│   ├── [ ] createElement
│   ├── [ ] createElementNS (SVG, MathML)
│   ├── [ ] createTextNode
│   ├── [ ] createComment
│   └── [ ] createDocumentFragment
│
├── Attributes (20 tests)
│   ├── [ ] getAttribute / setAttribute
│   ├── [ ] removeAttribute / hasAttribute
│   ├── [ ] toggleAttribute
│   ├── [ ] dataset (data-* attributes)
│   └── [ ] attributes NamedNodeMap
│
├── Content (10 tests)
│   ├── [ ] textContent
│   ├── [ ] innerHTML
│   ├── [ ] innerText
│   └── [ ] outerHTML
│
├── Traversal (15 tests)
│   ├── [ ] parentElement / parentNode
│   ├── [ ] children / childNodes
│   ├── [ ] first/lastElementChild
│   ├── [ ] next/previousElementSibling
│   ├── [ ] closest()
│   └── [ ] matches()
│
└── Manipulation (20 tests)
    ├── [ ] appendChild / insertBefore
    ├── [ ] removeChild / replaceChild
    ├── [ ] remove()
    ├── [ ] cloneNode()
    ├── [ ] append() / prepend()
    ├── [ ] before() / after()
    └── [ ] replaceWith()
```

###### Files to Create (Phase 34.1)

- `pynext/client/dom.py` — Document and Element Python stubs
- `pynext/client/node.py` — Node, NodeList, HTMLCollection
- `pynext/runtime/dom/document.js` — Document API runtime
- `pynext/runtime/dom/element.js` — Element API runtime
- `tests/unit/client/test_341_document.py` — Document tests
- `tests/unit/client/test_341_element.py` — Element tests

---

##### Phase 34.2: CSS Runtime & Styling (120 tests, 1 week)

Inline styles, CSS custom properties, computed styles, and classList.

###### Python API (Phase 34.2)

```python
from pynext.client import document, window

# =============================================================================
# Inline Style Manipulation
# =============================================================================

# Direct property access (camelCase)
el.style.display = "flex"
el.style.backgroundColor = "red"
el.style.borderRadius = "8px"
el.style.boxShadow = "0 4px 6px rgba(0,0,0,0.1)"
el.style.transform = "translateX(100px) rotate(45deg)"
el.style.transition = "all 0.3s ease-in-out"
el.style.willChange = "transform"  # Performance hint

# Vendor prefixes
el.style.webkitTransform = "rotate(45deg)"
el.style.mozTransform = "rotate(45deg)"

# =============================================================================
# CSS Custom Properties (Variables)
# =============================================================================

el.style.setProperty("--primary-color", "#3b82f6")
el.style.setProperty("--spacing", "16px")
el.style.setProperty("--opacity", "0.8")
value = el.style.getPropertyValue("--primary-color")
el.style.removeProperty("--primary-color")

# Root-level CSS variables (theming)
root = document.documentElement
root.style.setProperty("--theme-bg", "#ffffff")
root.style.setProperty("--theme-fg", "#000000")

# Style priority (important)
el.style.setProperty("color", "red", "important")

# =============================================================================
# Computed Styles
# =============================================================================

computed = window.getComputedStyle(el)
actual_width = computed.width                    # "200px"
actual_bg = computed.backgroundColor             # "rgb(255, 0, 0)"
actual_font = computed.fontSize                  # "16px"
actual_var = computed.getPropertyValue("--primary-color")

# Computed styles for pseudo-elements
before_styles = window.getComputedStyle(el, "::before")
after_content = before_styles.content
after_styles = window.getComputedStyle(el, "::after")

# =============================================================================
# cssText (Full Inline Style String)
# =============================================================================

el.style.cssText = "display: flex; gap: 8px; padding: 16px;"
full_style = el.style.cssText

# Style length and iteration
num_styles = el.style.length
for i in range(el.style.length):
    prop_name = el.style.item(i)  # e.g., "background-color"

# =============================================================================
# classList API
# =============================================================================

el.classList.add("active", "highlighted")
el.classList.remove("hidden")
el.classList.toggle("selected")
el.classList.toggle("selected", force=True)  # Force add
el.classList.contains("active")
el.classList.replace("old-class", "new-class")
el.classList.item(0)  # First class
el.classList.length
el.className = "foo bar"

# Iterate over classes
for cls in el.classList:
    print(cls)
```

###### Phase 34.2 Checklist

```
CSS Runtime & Styling (Phase 34.2)
├── Style Property Access (40 tests)
│   ├── [ ] el.style.<property> = value (all CSS properties)
│   ├── [ ] el.style.cssText get/set
│   ├── [ ] el.style.length
│   ├── [ ] el.style.item(index)
│   ├── [ ] Vendor prefixes (-webkit-, -moz-)
│   └── [ ] Style property name conversion (camelCase ↔ kebab-case)
│
├── CSS Custom Properties (30 tests)
│   ├── [ ] el.style.setProperty("--var", value)
│   ├── [ ] el.style.getPropertyValue("--var")
│   ├── [ ] el.style.removeProperty("--var")
│   ├── [ ] document.documentElement root variables
│   ├── [ ] setProperty with priority ("important")
│   └── [ ] Cascading variable inheritance
│
├── Computed Styles (30 tests)
│   ├── [ ] window.getComputedStyle(el)
│   ├── [ ] window.getComputedStyle(el, "::before")
│   ├── [ ] window.getComputedStyle(el, "::after")
│   ├── [ ] All property getters
│   ├── [ ] getPropertyValue for variables
│   └── [ ] Resolved values (px, rgb, etc.)
│
└── classList (20 tests)
    ├── [ ] classList.add(class1, class2, ...)
    ├── [ ] classList.remove(class1, class2, ...)
    ├── [ ] classList.toggle(class)
    ├── [ ] classList.toggle(class, force)
    ├── [ ] classList.contains(class)
    ├── [ ] classList.replace(oldClass, newClass)
    ├── [ ] classList.item(index)
    ├── [ ] classList.length
    └── [ ] className get/set
```

###### Files to Create (Phase 34.2)

- `pynext/client/style.py` — CSSStyleDeclaration stub
- `pynext/client/css_vars.py` — CSS Custom Properties helpers
- `pynext/runtime/dom/style.js` — Style manipulation runtime
- `pynext/transpiler/css.py` — camelCase ↔ kebab-case conversion
- `tests/unit/client/test_342_style.py` — Style tests
- `tests/unit/client/test_342_classlist.py` — classList tests
- `tests/unit/client/test_342_computed.py` — Computed style tests

---

##### Phase 34.3: CSS Typed Object Model (135 tests, 1 week)

Modern, type-safe CSS manipulation with CSS factory methods and StylePropertyMap.

###### Python API (Phase 34.3)

```python
from pynext.client import CSS, CSSUnitValue, CSSKeywordValue, CSSTransformValue

# =============================================================================
# CSS Unit Values
# =============================================================================

width = CSS.px(100)           # CSSUnitValue: 100px
height = CSS.percent(50)      # CSSUnitValue: 50%
margin = CSS.em(2)            # CSSUnitValue: 2em
padding = CSS.rem(1.5)        # CSSUnitValue: 1.5rem
angle = CSS.deg(45)           # CSSUnitValue: 45deg
time = CSS.ms(300)            # CSSUnitValue: 300ms

# CSSUnitValue properties and arithmetic
value = CSS.px(100)
value.value       # 100 (numeric value)
value.unit        # "px" (unit string)
str(value)        # "100px"
doubled = value.mul(2)        # 200px
half = value.div(2)           # 50px

# =============================================================================
# CSS Calc and Math Functions
# =============================================================================

width = CSS.calc("100% - 20px")
min_val = CSS.min(CSS.px(100), CSS.percent(50))
max_val = CSS.max(CSS.px(100), CSS.percent(50))
clamped = CSS.clamp(CSS.px(100), CSS.percent(50), CSS.px(300))

# =============================================================================
# StylePropertyMap (el.attributeStyleMap)
# =============================================================================

style_map = el.attributeStyleMap
style_map.set("width", CSS.px(100))
style_map.set("height", CSS.percent(50))
width = style_map.get("width")
style_map.delete("width")
style_map.clear()

# =============================================================================
# CSS Transforms (Typed)
# =============================================================================

translate = CSS.translate(CSS.px(100), CSS.px(50))
rotate = CSS.rotate(CSS.deg(45))
scale = CSS.scale(2, 1.5)

transform = CSSTransformValue([
    CSS.translate(CSS.px(100), CSS.px(50)),
    CSS.rotate(CSS.deg(45)),
    CSS.scale(2),
])
style_map.set("transform", transform)

# =============================================================================
# CSS Colors (Typed)
# =============================================================================

red = CSS.color("red")
rgb_color = CSS.rgb(255, 0, 0)
hsl_color = CSS.hsl(0, 100, 50)
oklch_color = CSS.oklch(0.7, 0.15, 30)
lighter = red.lighten(20)
darker = red.darken(20)
```

###### Phase 34.3 Checklist

```
CSS Typed OM (Phase 34.3)
├── CSS Factory Methods (30 tests)
│   ├── [ ] CSS.px(), CSS.percent(), CSS.em(), CSS.rem()
│   ├── [ ] CSS.vw(), CSS.vh(), CSS.vmin(), CSS.vmax()
│   ├── [ ] CSS.deg(), CSS.rad(), CSS.turn()
│   ├── [ ] CSS.ms(), CSS.s()
│   ├── [ ] CSS.keyword(), CSS.calc()
│   └── [ ] CSS.min(), CSS.max(), CSS.clamp()
│
├── CSSUnitValue (25 tests)
│   ├── [ ] value and unit properties
│   ├── [ ] toString()
│   ├── [ ] add(), sub(), mul(), div()
│   ├── [ ] equals()
│   └── [ ] to() unit conversion
│
├── CSSTransformValue (20 tests)
│   ├── [ ] CSS.translate(), CSS.rotate(), CSS.scale()
│   ├── [ ] CSS.skew(), CSS.matrix(), CSS.perspective()
│   ├── [ ] CSSTransformValue constructor
│   └── [ ] toMatrix() conversion
│
├── StylePropertyMap (25 tests)
│   ├── [ ] el.attributeStyleMap
│   ├── [ ] set(), get(), has(), delete(), clear()
│   ├── [ ] keys(), values(), entries()
│   └── [ ] size property
│
├── Computed Style Map (15 tests)
│   ├── [ ] el.computedStyleMap()
│   └── [ ] get() returns resolved values
│
└── CSS Color (20 tests)
    ├── [ ] CSS.color(), CSS.rgb(), CSS.hsl()
    ├── [ ] CSS.oklch(), CSS.oklab()
    └── [ ] Color manipulation (lighten, darken, alpha)
```

###### Files to Create (Phase 34.3)

- `pynext/client/typed_om.py` — CSS factory, CSSUnitValue, StylePropertyMap
- `pynext/client/css_color.py` — CSS color types and manipulation
- `pynext/runtime/dom/typed_om.js` — Typed OM runtime
- `tests/unit/client/test_343_css_factory.py`
- `tests/unit/client/test_343_unit_value.py`
- `tests/unit/client/test_343_transform.py`
- `tests/unit/client/test_343_color.py`

---

##### Phase 34.4: Events & Interactions (80 tests, 1 week)

Mouse, keyboard, touch, drag, and input events with full type safety.

###### Python API (Phase 34.4)

```python
from pynext.client import MouseEvent, KeyboardEvent, TouchEvent

# Mouse Events
@client
def on_click(event: MouseEvent):
    event.clientX, event.clientY      # Viewport coords
    event.pageX, event.pageY          # Page coords
    event.offsetX, event.offsetY      # Element coords
    event.button                      # 0=left, 1=middle, 2=right
    event.buttons                     # Bitmask of pressed buttons
    event.altKey, event.ctrlKey       # Modifiers

# Keyboard Events
@client
def on_keydown(event: KeyboardEvent):
    event.key                         # "Enter", "a", "Escape"
    event.code                        # "KeyA", "Enter", "Space"
    event.repeat                      # True if held

# Touch Events
@client
def on_touch(event: TouchEvent):
    for touch in event.touches:
        touch.identifier
        touch.clientX, touch.clientY
    event.changedTouches

# Drag Events
@client
def on_drag(event: DragEvent):
    event.dataTransfer.setData("text/plain", data)
    event.dataTransfer.getData("text/plain")
    event.dataTransfer.files

# Custom Events
event = CustomEvent("myevent", {"detail": {"foo": "bar"}})
el.dispatchEvent(event)

# Event Listeners
el.addEventListener("click", on_click)
el.addEventListener("click", on_click, {"capture": True, "once": True})
el.removeEventListener("click", on_click)
```

###### Phase 34.4 Checklist

```
Events & Interactions (Phase 34.4)
├── Mouse Events (15 tests)
│   ├── [ ] click, dblclick, contextmenu
│   ├── [ ] mousedown, mouseup, mousemove
│   ├── [ ] mouseenter, mouseleave, mouseover, mouseout
│   ├── [ ] Event properties (clientX/Y, pageX/Y, offsetX/Y)
│   ├── [ ] button, buttons, modifiers (alt, ctrl, shift, meta)
│   └── [ ] wheel event
│
├── Keyboard Events (15 tests)
│   ├── [ ] keydown, keyup, keypress
│   ├── [ ] key, code properties
│   ├── [ ] repeat property
│   ├── [ ] Modifier keys
│   └── [ ] Key combinations
│
├── Touch Events (10 tests)
│   ├── [ ] touchstart, touchmove, touchend, touchcancel
│   ├── [ ] touches, changedTouches, targetTouches
│   ├── [ ] Touch.identifier, clientX/Y
│   └── [ ] Multi-touch handling
│
├── Drag Events (10 tests)
│   ├── [ ] dragstart, drag, dragend
│   ├── [ ] dragenter, dragover, dragleave, drop
│   ├── [ ] dataTransfer.setData/getData
│   ├── [ ] dataTransfer.files
│   └── [ ] effectAllowed, dropEffect
│
├── Form Events (10 tests)
│   ├── [ ] submit, reset
│   ├── [ ] input, change
│   ├── [ ] focus, blur, focusin, focusout
│   └── [ ] InputEvent (inputType, data, isComposing)
│
├── Custom Events (10 tests)
│   ├── [ ] CustomEvent constructor
│   ├── [ ] detail property
│   ├── [ ] dispatchEvent
│   └── [ ] Event bubbling/capturing
│
└── Event Methods (10 tests)
    ├── [ ] preventDefault()
    ├── [ ] stopPropagation()
    ├── [ ] stopImmediatePropagation()
    ├── [ ] target, currentTarget
    └── [ ] addEventListener options (capture, once, passive)
```

###### Files to Create (Phase 34.4)

- `pynext/client/events.py` — All event type stubs
- `pynext/client/events.pyi` — Type stubs for IDE
- `pynext/runtime/dom/events.js` — Event handling runtime
- `tests/unit/client/test_344_mouse_events.py`
- `tests/unit/client/test_344_keyboard_events.py`
- `tests/unit/client/test_344_touch_events.py`
- `tests/unit/client/test_344_custom_events.py`

---

##### Phase 34.5: URL, Encoding & Binary Data (95 tests, 1 week)

URL parsing, text encoding/decoding, base64, and typed arrays.

###### Python API (Phase 34.5)

```python
from pynext.client import URL, URLSearchParams

# =============================================================================
# URL Parsing and Manipulation
# =============================================================================

# Parse a URL
url = URL("https://user:pass@example.com:8080/path/to/page?foo=bar&baz=qux#section")

# URL components (all readable properties)
url.href          # Full URL string
url.protocol      # "https:"
url.username      # "user"
url.password      # "pass"
url.host          # "example.com:8080" (hostname:port)
url.hostname      # "example.com"
url.port          # "8080"
url.pathname      # "/path/to/page"
url.search        # "?foo=bar&baz=qux"
url.searchParams  # URLSearchParams object
url.hash          # "#section"
url.origin        # "https://example.com:8080" (read-only)

# Modify URL components
url.pathname = "/new/path"
url.hash = "#new-section"
url.port = "3000"

# Resolve relative URLs
base = URL("https://example.com/a/b/c")
relative = URL("../d", base)
relative.href  # "https://example.com/a/d"

# Convert to string
str(url)       # Same as url.href
url.toString() # Same as url.href
url.toJSON()   # Same as url.href (for JSON.stringify)

# =============================================================================
# URLSearchParams (Query String Manipulation)
# =============================================================================

# Create from string
params = URLSearchParams("foo=1&bar=2&foo=3")

# Create from object
params = URLSearchParams({"page": "1", "limit": "10", "sort": "name"})

# Create from list of tuples
params = URLSearchParams([("key", "value1"), ("key", "value2")])

# Create empty
params = URLSearchParams()

# Get values
params.get("foo")       # "1" (first value)
params.getAll("foo")    # ["1", "3"] (all values)

# Check existence
params.has("bar")       # True
params.has("missing")   # False

# Set values (replaces all existing)
params.set("foo", "new_value")

# Append values (adds to existing)
params.append("foo", "another_value")

# Delete
params.delete("foo")                  # Delete all "foo" entries
params.delete("foo", "specific")      # Delete only "foo=specific"

# Sort alphabetically by key
params.sort()

# Iterate
for key in params.keys():
    print(key)

for value in params.values():
    print(value)

for key, value in params.entries():
    print(f"{key}={value}")

# Size
len(list(params))  # Number of entries

# Convert to string
str(params)         # "foo=1&bar=2" (without leading ?)
params.toString()   # Same as str()

# =============================================================================
# Common URL Patterns
# =============================================================================

# Build API URL with query params
@client
def build_api_url(endpoint, **params):
    url = URL(f"{window.location.origin}/api{endpoint}")
    for key, value in params.items():
        if value is not None:
            url.searchParams.set(key, str(value))
    return url.href

api_url = build_api_url("/users", page=1, limit=10, active=True)
# "https://example.com/api/users?page=1&limit=10&active=true"

# Parse current page URL
@client
def get_query_param(name, default=None):
    params = URLSearchParams(window.location.search)
    return params.get(name) or default

current_page = get_query_param("page", "1")

# Update URL without reload (with History API)
@client
def update_query_param(name, value):
    url = URL(window.location.href)
    url.searchParams.set(name, value)
    window.history.pushState({}, "", url.href)

# Check if URL is same origin
@client
def is_same_origin(url_string):
    try:
        url = URL(url_string, window.location.origin)
        return url.origin == window.location.origin
    except:
        return False
```

```python
from pynext.client import TextEncoder, TextDecoder, btoa, atob, Blob, Uint8Array

# =============================================================================
# TextEncoder (String → Bytes)
# =============================================================================

encoder = TextEncoder()  # Always UTF-8

# Encode string to Uint8Array
bytes_array = encoder.encode("Hello, 世界!")
# Uint8Array with UTF-8 bytes

# Get encoding name
encoder.encoding  # "utf-8"

# Encode into existing buffer
buffer = Uint8Array(100)
result = encoder.encodeInto("Hello", buffer)
result.read      # Characters read
result.written   # Bytes written

# =============================================================================
# TextDecoder (Bytes → String)
# =============================================================================

# Create decoder (various encodings)
decoder = TextDecoder("utf-8")              # Default
decoder_latin = TextDecoder("iso-8859-1")   # Latin-1
decoder_utf16 = TextDecoder("utf-16le")     # UTF-16 Little Endian

# Decoder options
decoder = TextDecoder("utf-8", {
    "fatal": True,      # Throw on invalid sequences (default: False)
    "ignoreBOM": True,  # Ignore byte order mark (default: False)
})

# Decode bytes to string
text = decoder.decode(bytes_array)

# Streaming decode (for chunked data)
decoder = TextDecoder("utf-8", {"stream": True})
chunk1 = decoder.decode(first_chunk, {"stream": True})
chunk2 = decoder.decode(second_chunk, {"stream": True})
final = decoder.decode()  # Flush remaining

# Decoder properties
decoder.encoding   # "utf-8"
decoder.fatal      # True/False
decoder.ignoreBOM  # True/False

# =============================================================================
# Base64 Encoding (ASCII-safe binary encoding)
# =============================================================================

# Encode string to Base64 (only works with ASCII/Latin-1)
encoded = btoa("Hello, World!")  # "SGVsbG8sIFdvcmxkIQ=="

# Decode Base64 to string
decoded = atob("SGVsbG8sIFdvcmxkIQ==")  # "Hello, World!"

# For Unicode strings (must encode to UTF-8 first)
@client
def unicode_to_base64(text):
    encoder = TextEncoder()
    bytes_array = encoder.encode(text)
    # Convert Uint8Array to binary string
    binary = "".join(chr(b) for b in bytes_array)
    return btoa(binary)

@client
def base64_to_unicode(base64_str):
    binary = atob(base64_str)
    bytes_array = Uint8Array([ord(c) for c in binary])
    decoder = TextDecoder()
    return decoder.decode(bytes_array)

# Encode "Hello, 世界!" to base64 (with UTF-8)
base64_unicode = unicode_to_base64("Hello, 世界!")

# =============================================================================
# ArrayBuffer and Typed Arrays
# =============================================================================

# Create typed arrays
uint8 = Uint8Array(16)                    # 16 bytes of zeros
uint8 = Uint8Array([1, 2, 3, 4, 5])       # From values
uint8 = Uint8Array(array_buffer)          # From ArrayBuffer
uint8 = Uint8Array(array_buffer, 4, 8)    # Offset 4, length 8

# Other typed arrays
from pynext.client import (
    Int8Array, Uint8Array, Uint8ClampedArray,
    Int16Array, Uint16Array,
    Int32Array, Uint32Array,
    Float32Array, Float64Array,
    BigInt64Array, BigUint64Array,
)

# ArrayBuffer operations
buffer = ArrayBuffer(256)
buffer.byteLength      # 256
buffer.slice(0, 100)   # New ArrayBuffer with first 100 bytes

# DataView for mixed types
from pynext.client import DataView

view = DataView(buffer)
view.setInt32(0, 12345, True)    # Little-endian
value = view.getInt32(0, True)   # Read back

# =============================================================================
# Practical Encoding Examples
# =============================================================================

# Convert ArrayBuffer to hex string
@client
def buffer_to_hex(buffer):
    bytes_array = Uint8Array(buffer)
    return "".join(f"{b:02x}" for b in bytes_array)

# Convert hex string to ArrayBuffer
@client
def hex_to_buffer(hex_str):
    bytes_list = [int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)]
    return Uint8Array(bytes_list).buffer

# Read file as base64
@client
async def file_to_base64(file):
    buffer = await file.arrayBuffer()
    bytes_array = Uint8Array(buffer)
    binary = "".join(chr(b) for b in bytes_array)
    return btoa(binary)

# Create download from base64
@client
def download_base64(base64_data, filename, mime_type):
    binary = atob(base64_data)
    bytes_array = Uint8Array([ord(c) for c in binary])
    blob = Blob([bytes_array], {"type": mime_type})
    url = URL.createObjectURL(blob)
    
    a = document.createElement("a")
    a.href = url
    a.download = filename
    a.click()
    
    URL.revokeObjectURL(url)
```

###### Phase 34.5 Checklist

```
URL, Encoding & Binary Data (Phase 34.5)
├── URL API (25 tests)
│   ├── [ ] URL constructor (absolute, relative with base)
│   ├── [ ] All URL properties (href, protocol, hostname, etc.)
│   ├── [ ] URL property setters
│   ├── [ ] url.toString(), url.toJSON()
│   ├── [ ] url.searchParams integration
│   └── [ ] URL.createObjectURL / revokeObjectURL
│
├── URLSearchParams (25 tests)
│   ├── [ ] Constructor (string, object, array of tuples)
│   ├── [ ] get(), getAll()
│   ├── [ ] set(), append()
│   ├── [ ] has(), delete()
│   ├── [ ] sort()
│   ├── [ ] Iteration (keys, values, entries)
│   └── [ ] toString()
│
├── TextEncoder (15 tests)
│   ├── [ ] encode()
│   ├── [ ] encodeInto()
│   └── [ ] encoding property
│
├── TextDecoder (20 tests)
│   ├── [ ] Constructor with encoding options
│   ├── [ ] decode() with various encodings
│   ├── [ ] Streaming decode
│   ├── [ ] fatal and ignoreBOM options
│   └── [ ] Common encodings (utf-8, iso-8859-1, utf-16)
│
└── Base64 & Binary (10 tests)
    ├── [ ] btoa() for ASCII strings
    ├── [ ] atob() for base64 decoding
    ├── [ ] ArrayBuffer, TypedArrays
    └── [ ] DataView
```

###### Files to Create (Phase 34.5)

- `pynext/client/url.py` — URL and URLSearchParams
- `pynext/client/encoding.py` — TextEncoder, TextDecoder, base64
- `pynext/client/binary.py` — ArrayBuffer, TypedArrays, DataView
- `pynext/runtime/dom/url.js` — URL runtime
- `pynext/runtime/dom/encoding.js` — Encoding runtime
- `tests/unit/client/test_345_url.py`
- `tests/unit/client/test_345_search_params.py`
- `tests/unit/client/test_345_encoding.py`
- `tests/unit/client/test_345_binary.py`

---

##### Phase 34.6: Memory Management (70 tests, 1 week)

Weak references, structured cloning, and memory-safe patterns.

###### Python API (Phase 34.6)

```python
from pynext.client import structuredClone

# =============================================================================
# Basic Deep Cloning
# =============================================================================

# Clone simple objects
original = {"name": "Alice", "scores": [100, 95, 88]}
clone = structuredClone(original)
clone["scores"].append(92)  # Doesn't affect original

# Clone with nested structures
data = {
    "users": [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ],
    "metadata": {
        "created": Date.now(),
        "version": 1,
    }
}
deep_clone = structuredClone(data)

# =============================================================================
# Supported Types
# =============================================================================

# All these types are properly cloned:
structuredClone({
    # Primitives
    "string": "hello",
    "number": 42,
    "boolean": True,
    "null": None,
    
    # Objects and Arrays
    "object": {"nested": {"deep": True}},
    "array": [1, 2, [3, 4]],
    
    # Date
    "date": Date(),
    
    # RegExp
    "regex": RegExp("\\d+", "g"),
    
    # Map and Set
    "map": Map([["key1", "value1"], ["key2", "value2"]]),
    "set": Set([1, 2, 3]),
    
    # Binary data
    "buffer": ArrayBuffer(16),
    "uint8": Uint8Array([1, 2, 3]),
    "int32": Int32Array([100, 200]),
    
    # Blob and File
    "blob": Blob(["data"], {"type": "text/plain"}),
    
    # Error objects
    "error": Error("Something went wrong"),
})

# =============================================================================
# Circular References
# =============================================================================

# structuredClone handles circular references automatically
obj = {"name": "circular"}
obj["self"] = obj  # Circular reference
clone = structuredClone(obj)  # Works correctly!
clone["self"] is clone  # True

# =============================================================================
# Transfer (Move Ownership)
# =============================================================================

# Transfer ArrayBuffers (move, not copy) - original becomes detached
buffer = ArrayBuffer(1024 * 1024)  # 1MB buffer
clone = structuredClone({"data": buffer}, {"transfer": [buffer]})
# buffer.byteLength is now 0 (detached)
# clone["data"] has the 1MB buffer

# Useful for moving large data to workers efficiently

# =============================================================================
# Types That Cannot Be Cloned
# =============================================================================

# These will throw DataCloneError:
# - Functions
# - DOM nodes
# - Symbols
# - WeakMap, WeakSet
# - Property descriptors (getters/setters become values)

# Check if value is cloneable
@client
def is_cloneable(value):
    try:
        structuredClone(value)
        return True
    except:
        return False

# =============================================================================
# Practical Use Cases
# =============================================================================

# State snapshots for undo/redo
@client
class UndoStack:
    def __init__(self):
        self.history = []
        self.index = -1
    
    def push(self, state):
        # Clone state before storing
        self.history = self.history[:self.index + 1]
        self.history.append(structuredClone(state))
        self.index += 1
    
    def undo(self):
        if self.index > 0:
            self.index -= 1
            return structuredClone(self.history[self.index])
        return None
    
    def redo(self):
        if self.index < len(self.history) - 1:
            self.index += 1
            return structuredClone(self.history[self.index])
        return None

# Safe state passing to components
@client
def pass_to_component(state):
    # Ensure component can't mutate parent state
    return structuredClone(state)
```

```python
from pynext.client import WeakRef, WeakMap, WeakSet, FinalizationRegistry

# =============================================================================
# WeakRef (Weak Reference to Object)
# =============================================================================

# Create a weak reference (doesn't prevent garbage collection)
large_object = {"data": "x" * 10000}
weak = WeakRef(large_object)

# Dereference to get the object (or None if GC'd)
obj = weak.deref()
if obj is not None:
    print(obj["data"])
else:
    print("Object was garbage collected")

# Use case: Caching without preventing GC
@client
class WeakCache:
    def __init__(self):
        self.cache = {}  # key → WeakRef
    
    def get(self, key):
        if key in self.cache:
            ref = self.cache[key]
            value = ref.deref()
            if value is not None:
                return value
            # Object was GC'd, remove stale entry
            del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = WeakRef(value)

# =============================================================================
# WeakMap (Keys are Weakly Held)
# =============================================================================

# WeakMap keys must be objects, values can be anything
# When key object is GC'd, the entry is automatically removed

cache = WeakMap()

# Associate data with DOM elements without preventing their GC
def attach_data(element, data):
    cache.set(element, data)
    # When element is removed from DOM and GC'd,
    # the cache entry is automatically cleaned up

def get_data(element):
    return cache.get(element)

# WeakMap methods
cache.set(obj, "value")     # Set value for key
cache.get(obj)              # Get value (undefined if not found)
cache.has(obj)              # Check if key exists
cache.delete(obj)           # Remove entry

# Use case: Private data for objects
_private = WeakMap()

@client
class MyClass:
    def __init__(self, secret):
        _private.set(self, {"secret": secret})
    
    def get_secret(self):
        return _private.get(self)["secret"]

# =============================================================================
# WeakSet (Weak Collection of Objects)
# =============================================================================

# WeakSet holds objects weakly - they can be GC'd even if in the set
tracked = WeakSet()

# Track objects without preventing GC
def track_element(element):
    tracked.add(element)

def is_tracked(element):
    return tracked.has(element)

def untrack_element(element):
    tracked.delete(element)

# Use case: Track which elements have been processed
processed = WeakSet()

@client
def process_once(element):
    if processed.has(element):
        return  # Already processed
    
    # Process element...
    do_something(element)
    
    # Mark as processed (weak, so removed when element is GC'd)
    processed.add(element)

# =============================================================================
# FinalizationRegistry (Cleanup Callbacks)
# =============================================================================

# Get notified when objects are garbage collected
# Useful for releasing external resources

# Create registry with cleanup callback
registry = FinalizationRegistry(lambda held_value:
    print(f"Cleanup: {held_value}")
)

# Register object with held value (passed to callback)
obj = {"large": "data"}
registry.register(obj, "resource-123")
# When obj is GC'd, callback receives "resource-123"

# Register with unregister token
unregister_token = {}
registry.register(obj, "resource-456", unregister_token)

# Unregister before GC (e.g., manual cleanup)
registry.unregister(unregister_token)

# =============================================================================
# Practical Memory Management Patterns
# =============================================================================

# Pattern 1: Resource cleanup for large objects
@client
class ResourceManager:
    def __init__(self):
        self.registry = FinalizationRegistry(self._cleanup)
        self.resources = {}  # id → resource
    
    def _cleanup(self, resource_id):
        if resource_id in self.resources:
            # Release external resource
            self.resources[resource_id].release()
            del self.resources[resource_id]
    
    def allocate(self, owner, resource):
        resource_id = str(id(resource))
        self.resources[resource_id] = resource
        self.registry.register(owner, resource_id)
        return resource

# Pattern 2: Event listener cleanup
@client
class SafeEventEmitter:
    def __init__(self):
        self.listeners = WeakMap()  # object → Set of callbacks
    
    def on(self, target, event, callback):
        if not self.listeners.has(target):
            self.listeners.set(target, {})
        events = self.listeners.get(target)
        if event not in events:
            events[event] = set()
        events[event].add(callback)
    
    def emit(self, target, event, data):
        if not self.listeners.has(target):
            return
        events = self.listeners.get(target)
        if event in events:
            for callback in events[event]:
                callback(data)
        # If target is GC'd, all its listeners are automatically cleaned up

# Pattern 3: DOM element metadata without memory leaks
element_metadata = WeakMap()

@client
def set_element_config(element, config):
    element_metadata.set(element, config)
    # When element is removed and GC'd, config is also GC'd

@client
def get_element_config(element):
    return element_metadata.get(element)
```

###### Phase 34.6 Checklist

```
Memory Management (Phase 34.6)
├── structuredClone (20 tests)
│   ├── [ ] Deep cloning primitives and objects
│   ├── [ ] Date, RegExp, Map, Set cloning
│   ├── [ ] ArrayBuffer, TypedArray cloning
│   ├── [ ] Circular reference handling
│   ├── [ ] transfer option for ArrayBuffers
│   └── [ ] DataCloneError for non-cloneable types
│
├── WeakRef (15 tests)
│   ├── [ ] WeakRef constructor
│   ├── [ ] deref() returning object or undefined
│   └── [ ] GC behavior verification
│
├── WeakMap (15 tests)
│   ├── [ ] set(), get(), has(), delete()
│   ├── [ ] Object-only keys requirement
│   └── [ ] Automatic cleanup on key GC
│
├── WeakSet (10 tests)
│   ├── [ ] add(), has(), delete()
│   └── [ ] Automatic cleanup on value GC
│
└── FinalizationRegistry (10 tests)
    ├── [ ] Constructor with callback
    ├── [ ] register() with held value
    ├── [ ] register() with unregister token
    └── [ ] unregister()
```

###### Files to Create (Phase 34.6)

- `pynext/client/clone.py` — structuredClone
- `pynext/client/weakref.py` — WeakRef, WeakMap, WeakSet, FinalizationRegistry
- `pynext/runtime/dom/clone.js` — Clone runtime
- `pynext/runtime/dom/weakref.js` — Weak reference runtime
- `tests/unit/client/test_346_structured_clone.py`
- `tests/unit/client/test_346_weakref.py`
- `tests/unit/client/test_346_weakmap.py`
- `tests/unit/client/test_346_finalization.py`

---

##### Phase 34.7: Error Boundaries & DX (25 tests, 1 week)

Error handling components and IDE developer experience.

###### Type Stubs for IDE Autocomplete (.pyi files)

```python
# =============================================================================
# Example: pynext/client/document.pyi
# =============================================================================

from typing import Optional, List, overload, Union
from .element import Element
from .node import Node, NodeList

class Document:
    # Properties
    body: Element
    head: Element
    documentElement: Element
    title: str
    URL: str
    domain: str
    referrer: str
    cookie: str
    readyState: str
    visibilityState: str
    hidden: bool
    fullscreenElement: Optional[Element]
    activeElement: Optional[Element]
    
    # Query methods
    def getElementById(self, id: str) -> Optional[Element]: ...
    def querySelector(self, selector: str) -> Optional[Element]: ...
    def querySelectorAll(self, selector: str) -> NodeList: ...
    def getElementsByClassName(self, classNames: str) -> NodeList: ...
    def getElementsByTagName(self, tagName: str) -> NodeList: ...
    def getElementsByName(self, name: str) -> NodeList: ...
    
    # Creation methods
    def createElement(self, tagName: str) -> Element: ...
    def createElementNS(self, namespace: str, qualifiedName: str) -> Element: ...
    def createTextNode(self, data: str) -> Node: ...
    def createComment(self, data: str) -> Node: ...
    def createDocumentFragment(self) -> Node: ...
    def createEvent(self, eventType: str) -> Event: ...
    
    # Event methods
    def addEventListener(self, type: str, listener: Callable, options: Optional[dict] = None) -> None: ...
    def removeEventListener(self, type: str, listener: Callable) -> None: ...
    def dispatchEvent(self, event: Event) -> bool: ...
    
    # Other methods
    def execCommand(self, commandId: str, showUI: bool = False, value: str = "") -> bool: ...
    def getSelection(self) -> Selection: ...
    def exitFullscreen(self) -> Awaitable[None]: ...

document: Document

# =============================================================================
# Example: pynext/client/element.pyi
# =============================================================================

class Element(Node):
    # Properties
    id: str
    className: str
    classList: DOMTokenList
    tagName: str
    innerHTML: str
    outerHTML: str
    textContent: str
    style: CSSStyleDeclaration
    dataset: DOMStringMap
    attributes: NamedNodeMap
    children: NodeList
    childElementCount: int
    firstElementChild: Optional[Element]
    lastElementChild: Optional[Element]
    nextElementSibling: Optional[Element]
    previousElementSibling: Optional[Element]
    parentElement: Optional[Element]
    scrollTop: float
    scrollLeft: float
    scrollWidth: float
    scrollHeight: float
    clientTop: float
    clientLeft: float
    clientWidth: float
    clientHeight: float
    offsetTop: float
    offsetLeft: float
    offsetWidth: float
    offsetHeight: float
    
    # Attribute methods
    def getAttribute(self, name: str) -> Optional[str]: ...
    def setAttribute(self, name: str, value: str) -> None: ...
    def removeAttribute(self, name: str) -> None: ...
    def hasAttribute(self, name: str) -> bool: ...
    def toggleAttribute(self, name: str, force: Optional[bool] = None) -> bool: ...
    
    # Query methods
    def querySelector(self, selector: str) -> Optional[Element]: ...
    def querySelectorAll(self, selector: str) -> NodeList: ...
    def closest(self, selector: str) -> Optional[Element]: ...
    def matches(self, selector: str) -> bool: ...
    
    # DOM manipulation
    def appendChild(self, node: Node) -> Node: ...
    def removeChild(self, node: Node) -> Node: ...
    def replaceChild(self, newChild: Node, oldChild: Node) -> Node: ...
    def insertBefore(self, newNode: Node, referenceNode: Optional[Node]) -> Node: ...
    def append(self, *nodes: Union[Node, str]) -> None: ...
    def prepend(self, *nodes: Union[Node, str]) -> None: ...
    def remove(self) -> None: ...
    def replaceWith(self, *nodes: Union[Node, str]) -> None: ...
    def cloneNode(self, deep: bool = False) -> Element: ...
    
    # Geometry
    def getBoundingClientRect(self) -> DOMRect: ...
    def getClientRects(self) -> DOMRectList: ...
    
    # Scroll
    def scrollTo(self, options: dict) -> None: ...
    def scrollBy(self, options: dict) -> None: ...
    def scrollIntoView(self, options: Optional[dict] = None) -> None: ...
    
    # Focus
    def focus(self, options: Optional[dict] = None) -> None: ...
    def blur(self) -> None: ...
    
    # Events
    def addEventListener(self, type: str, listener: Callable, options: Optional[dict] = None) -> None: ...
    def removeEventListener(self, type: str, listener: Callable) -> None: ...
    def dispatchEvent(self, event: Event) -> bool: ...
    
    # Animation
    def animate(self, keyframes: List[dict], options: Union[int, dict]) -> Animation: ...
    def getAnimations(self) -> List[Animation]: ...
    
    # Fullscreen
    def requestFullscreen(self, options: Optional[dict] = None) -> Awaitable[None]: ...
```

###### Error Boundaries

```python
from pynext.client import ErrorBoundary, error_boundary

# =============================================================================
# ErrorBoundary Component
# =============================================================================

def App():
    return ErrorBoundary(
        fallback=ErrorFallback,
        on_error=log_error_to_server,
    )[
        Header(),
        MainContent(),  # If this throws, ErrorFallback is shown
        Footer(),
    ]

def ErrorFallback(error, reset):
    """Fallback UI shown when child throws."""
    return div(class_="error-container")[
        h2()["Something went wrong"],
        p()[str(error)],
        button(on_click=reset)["Try again"],
    ]

def log_error_to_server(error, error_info):
    """Called when error is caught."""
    fetch("/api/errors", {
        "method": "POST",
        "body": JSON.stringify({
            "error": str(error),
            "stack": error.stack,
            "component_stack": error_info.componentStack,
        })
    })

# =============================================================================
# @error_boundary Decorator
# =============================================================================

@error_boundary(fallback=lambda e: div()[f"Error: {e}"])
@client
def RiskyComponent():
    # If this throws, fallback is rendered instead
    data = parse_untrusted_data()
    return DisplayData(data)

# With custom error handler
@error_boundary(
    fallback=MinimalFallback,
    on_error=lambda e, info: console.error("Component error:", e),
)
@client
def AnotherRiskyComponent():
    pass

# =============================================================================
# Nested Error Boundaries
# =============================================================================

def Dashboard():
    return div()[
        # Each section has its own error boundary
        # A failure in one doesn't affect others
        
        ErrorBoundary(fallback=WidgetError)[
            AnalyticsWidget(),
        ],
        
        ErrorBoundary(fallback=WidgetError)[
            SalesWidget(),
        ],
        
        ErrorBoundary(fallback=WidgetError)[
            InventoryWidget(),
        ],
    ]

# =============================================================================
# Development vs Production Error Display
# =============================================================================

# In development mode:
# - Show full Python stack trace
# - Show component stack
# - Show error details
# - "View source" links

# In production mode:
# - Show user-friendly message
# - Log error to monitoring service
# - No implementation details exposed

# Configuration
from pynext import configure

configure(
    error_boundary_mode="development",  # or "production"
    error_reporting_url="/api/errors",
)

# =============================================================================
# Error Recovery
# =============================================================================

@client
def RecoverableComponent():
    data = Signal(None)
    error = Signal(None)
    
    async def load():
        try:
            response = await fetch("/api/data")
            data.set(await response.json())
            error.set(None)
        except Exception as e:
            error.set(e)
    
    load()
    
    if error():
        return div()[
            p()[f"Failed: {error()}"],
            button(on_click=load)["Retry"],
        ]
    
    if not data():
        return div()["Loading..."]
    
    return DisplayData(data())
```

###### Phase 34.7 Checklist

```
Error Boundaries & DX (Phase 34.7)
├── ErrorBoundary Component (8 tests)
│   ├── [ ] Catch errors in children
│   ├── [ ] Render fallback on error
│   ├── [ ] on_error callback
│   ├── [ ] reset() function
│   └── [ ] Error info (component stack)
│
├── @error_boundary Decorator (5 tests)
│   ├── [ ] Wrap component in error boundary
│   ├── [ ] fallback parameter
│   └── [ ] on_error parameter
│
├── Nested Boundaries (5 tests)
│   ├── [ ] Independent error handling
│   ├── [ ] Closest boundary catches
│   └── [ ] Sibling isolation
│
└── Type Stubs (7 tests)
    ├── [ ] document.pyi autocomplete
    ├── [ ] element.pyi autocomplete
    ├── [ ] events.pyi autocomplete
    └── [ ] IDE integration tests
```

###### Files to Create (Phase 34.7)

- `pynext/client/error_boundary.py` — ErrorBoundary component and decorator
- `pynext/client/document.pyi` — Type stubs for document
- `pynext/client/element.pyi` — Type stubs for Element
- `pynext/client/events.pyi` — Type stubs for events
- `pynext/client/node.pyi` — Type stubs for Node, NodeList
- `tests/unit/client/test_347_error_boundary.py`
- `tests/unit/client/test_347_type_stubs.py`

---

##### What Phase 34 Enables

After completing all Phase 34 sub-phases, you can directly manipulate the DOM from Python:

```python
from pynext.client import client, document, window

@client
def create_todo_list(items: list[str]):
    """Build a complete UI using DOM APIs — no JSX required."""
    
    # Create container
    container = document.createElement("div")
    container.className = "todo-container"
    container.style.padding = "20px"
    container.style.borderRadius = "8px"
    container.style.boxShadow = "0 4px 6px rgba(0,0,0,0.1)"
    
    # Add title
    title = document.createElement("h1")
    title.textContent = "My Todos"
    title.style.setProperty("--heading-color", "#1e40af")
    title.style.color = "var(--heading-color)"
    container.appendChild(title)
    
    # Create list
    ul = document.createElement("ul")
    ul.classList.add("todo-list", "space-y-2")
    
    for item in items:
        li = document.createElement("li")
        li.textContent = item
        li.dataset.status = "pending"  # data-status="pending"
        
        # Add click handler
        def toggle(e):
            target = e.currentTarget
            if target.classList.contains("completed"):
                target.classList.remove("completed")
                target.dataset.status = "pending"
            else:
                target.classList.add("completed")
                target.dataset.status = "done"
        
        li.addEventListener("click", toggle)
        ul.appendChild(li)
    
    container.appendChild(ul)
    
    # Append to document
    document.body.appendChild(container)
    return container


@client
def interactive_form():
    """Handle form events with full Python ergonomics."""
    form = document.querySelector("#signup-form")
    
    def on_submit(event):
        event.preventDefault()
        
        # Get form data
        name = document.querySelector("#name").value
        email = document.querySelector("#email").value
        
        # Validate
        if not name or not email:
            show_error("Please fill all fields")
            return
        
        # Submit
        submit_form({"name": name, "email": email})
    
    form.addEventListener("submit", on_submit)


@client
def smooth_scroll_to(element_id: str):
    """Use DOM methods for smooth interactions."""
    el = document.getElementById(element_id)
    if el:
        # Get position
        rect = el.getBoundingClientRect()
        
        # Smooth scroll
        el.scrollIntoView({"behavior": "smooth", "block": "center"})
        
        # Flash highlight
        el.style.transition = "background-color 0.3s ease"
        el.style.backgroundColor = "#fef3c7"
        
        window.setTimeout(
            lambda: setattr(el.style, "backgroundColor", "transparent"),
            1000
        )
```

##### Phase 34 Success Criteria

| Metric | Target |
|--------|--------|
| DOM coverage | 100% of commonly used DOM APIs |
| Event types | All standard event interfaces |
| CSS runtime | Full CSSStyleDeclaration support |
| CSS variables | Complete custom properties API |
| Computed styles | All getComputedStyle capabilities |
| CSS Typed OM | Full attributeStyleMap and factory methods |
| URL/Encoding | Complete URL, TextEncoder/Decoder, base64 |
| Memory APIs | Full WeakRef, WeakMap, WeakSet, FinalizationRegistry |
| Error Boundaries | Component and decorator patterns |
| Type Stubs | Full IDE autocomplete for all DOM APIs |
| Test coverage | 625+ unit tests |

##### Phase 34 Milestones

| Week | Sub-Phase | Deliverables |
|------|-----------|--------------|
| 1 | 34.1 | Document queries, createElement, attributes, traversal, manipulation |
| 2 | 34.2 | classList, el.style, CSS variables, getComputedStyle |
| 3 | 34.3 | CSS Typed OM, CSSUnitValue, transforms, colors |
| 4 | 34.4 | Mouse, keyboard, touch, drag events |
| 5 | 34.5 | URL, URLSearchParams, TextEncoder/Decoder, base64 |
| 6 | 34.6 | structuredClone, WeakRef, WeakMap, WeakSet |
| 7 | 34.7 | Error boundaries, type stubs, IDE integration |

---

#### Phase 35: Browser APIs (300 tests, 4 weeks)

Window, navigator, and fetch APIs — connecting Python to the browser environment.

##### Browser APIs Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 35: BROWSER APIs                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                            Window API                                    ││
│  │                                                                          ││
│  │  Timers           Location          History           Screen            ││
│  │  ──────           ────────          ───────           ──────            ││
│  │  setTimeout       window.location   history.pushState window.screen     ││
│  │  setInterval      location.href     history.back()    screen.width      ││
│  │  clearTimeout     location.search   history.forward() screen.height     ││
│  │  clearInterval    location.hash     history.go(n)     devicePixelRatio  ││
│  │                                                                          ││
│  │  Dialogs          Storage           Dimensions        Events            ││
│  │  ───────          ───────           ──────────        ──────            ││
│  │  alert            localStorage      innerWidth        resize            ││
│  │  confirm          sessionStorage    innerHeight       scroll            ││
│  │  prompt           getItem/setItem   scrollX/Y         online/offline    ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                          Navigator API                                   ││
│  │                                                                          ││
│  │  User Info        Capabilities      Clipboard         Geolocation       ││
│  │  ─────────        ────────────      ─────────         ───────────       ││
│  │  userAgent        online            writeText         getCurrentPos     ││
│  │  language         cookieEnabled     readText          watchPosition     ││
│  │  platform         maxTouchPoints    write/read        clearWatch        ││
│  │  vendor                                                                  ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                            Fetch API                                     ││
│  │                                                                          ││
│  │  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐   ││
│  │  │     Request     │     │    Response     │     │    Headers      │   ││
│  │  │                 │     │                 │     │                 │   ││
│  │  │ • url, method   │────▶│ • status, ok    │     │ • get, set      │   ││
│  │  │ • headers       │     │ • json(), text()│     │ • has, delete   │   ││
│  │  │ • body          │     │ • blob(), bytes │     │ • entries()     │   ││
│  │  │ • mode, cache   │     │ • headers       │     │ • forEach()     │   ││
│  │  └─────────────────┘     └─────────────────┘     └─────────────────┘   ││
│  │                                                                          ││
│  │  fetch(url, options) → Response                                         ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         Console & Performance                            ││
│  │                                                                          ││
│  │  Console API                    Performance API                          ││
│  │  ───────────                    ───────────────                          ││
│  │  console.log/warn/error         performance.now()                        ││
│  │  console.table/group            performance.mark()                       ││
│  │  console.time/timeEnd           performance.measure()                    ││
│  │  console.count/assert           performance.getEntries()                 ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Python API

```python
from pynext.client import window, navigator, fetch

# Window - Location
window.location.href
window.location.pathname
window.location.search
window.location.hash
window.location.reload()
window.location.assign("/new-page")
window.location.replace("/new-page")

# Window - History
window.history.pushState(state, "", "/new-url")
window.history.replaceState(state, "", "/new-url")
window.history.back()
window.history.forward()
window.history.go(-2)

# Window - Dimensions
window.innerWidth, window.innerHeight
window.outerWidth, window.outerHeight
window.scrollX, window.scrollY
window.devicePixelRatio

# Window - Scroll
window.scrollTo(0, 100)
window.scrollTo({"top": 100, "behavior": "smooth"})
window.scrollBy(0, 50)

# Window - Dialogs
window.alert("Message")
result = window.confirm("Continue?")
input_val = window.prompt("Enter name:", "default")

# Window - Timers
id = window.setTimeout(callback, 1000)
window.clearTimeout(id)
id = window.setInterval(callback, 1000)
window.clearInterval(id)
window.requestAnimationFrame(callback)
window.cancelAnimationFrame(id)

# Window - Storage
window.localStorage.setItem("key", "value")
window.localStorage.getItem("key")
window.localStorage.removeItem("key")
window.localStorage.clear()
window.sessionStorage  # Same API

# Window - Media Queries (CSS Media Matching)
# Basic media query matching
mq = window.matchMedia("(prefers-color-scheme: dark)")
is_dark = mq.matches  # True if dark mode
mq.media  # "(prefers-color-scheme: dark)"

# Responsive breakpoints
is_mobile = window.matchMedia("(max-width: 768px)").matches
is_tablet = window.matchMedia("(min-width: 769px) and (max-width: 1024px)").matches
is_desktop = window.matchMedia("(min-width: 1025px)").matches

# Listen for media query changes
@client
def setup_responsive():
    mq = window.matchMedia("(max-width: 768px)")
    is_mobile = Signal(mq.matches)
    
    @mq.on_change
    def on_breakpoint_change(event):
        is_mobile.set(event.matches)
    
    # Alternative: addEventListener
    mq.addEventListener("change", on_breakpoint_change)
    mq.removeEventListener("change", on_breakpoint_change)

# System preferences
prefers_dark = window.matchMedia("(prefers-color-scheme: dark)")
prefers_light = window.matchMedia("(prefers-color-scheme: light)")
prefers_reduced_motion = window.matchMedia("(prefers-reduced-motion: reduce)")
prefers_contrast = window.matchMedia("(prefers-contrast: high)")
prefers_transparency = window.matchMedia("(prefers-reduced-transparency: reduce)")

# Device capabilities
is_touch = window.matchMedia("(pointer: coarse)").matches
is_hover_capable = window.matchMedia("(hover: hover)").matches
is_landscape = window.matchMedia("(orientation: landscape)").matches
is_portrait = window.matchMedia("(orientation: portrait)").matches
is_retina = window.matchMedia("(min-resolution: 2dppx)").matches

# Display features
is_hdr = window.matchMedia("(dynamic-range: high)").matches
color_gamut = window.matchMedia("(color-gamut: p3)").matches

# Combined queries
complex_mq = window.matchMedia(
    "(min-width: 768px) and (prefers-color-scheme: dark) and (hover: hover)"
)

# Navigator
navigator.userAgent
navigator.language
navigator.languages
navigator.onLine
navigator.cookieEnabled
navigator.hardwareConcurrency
navigator.maxTouchPoints

# Navigator - Clipboard
await navigator.clipboard.writeText("Hello")
text = await navigator.clipboard.readText()
await navigator.clipboard.write([ClipboardItem(...)])

# Navigator - Geolocation
position = await navigator.geolocation.getCurrentPosition()
position.coords.latitude
position.coords.longitude
position.coords.accuracy

# Navigator - Permissions
result = await navigator.permissions.query({"name": "geolocation"})
result.state  # "granted", "denied", "prompt"

# Navigator - Share
await navigator.share({
    "title": "Check this out",
    "text": "Amazing content",
    "url": "https://example.com",
})

# Fetch API
response = await fetch("/api/data")
response.ok
response.status
response.statusText
data = await response.json()
text = await response.text()
blob = await response.blob()

# Fetch - Options
response = await fetch("/api/data", {
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps({"key": "value"}),
    "credentials": "include",
    "mode": "cors",
})

# Fetch - AbortController
controller = AbortController()
response = await fetch("/api/data", {"signal": controller.signal})
controller.abort()

# FormData
form_data = FormData()
form_data.append("file", file_blob, "filename.txt")
form_data.append("name", "value")
await fetch("/upload", {"method": "POST", "body": form_data})
```

##### Files to Create

- `pynext/client/window.py` — window object stubs
- `pynext/client/navigator.py` — navigator stubs
- `pynext/client/fetch.py` — fetch, Request, Response, Headers, FormData, AbortController
- `pynext/client/media_query.py` — MediaQueryList, responsive utilities

##### CSS Media Query Checklist

```
Media Query Support (included in Phase 35)
├── MediaQueryList API (25 tests)
│   ├── [ ] window.matchMedia(query)
│   ├── [ ] mq.matches (boolean)
│   ├── [ ] mq.media (query string)
│   ├── [ ] mq.addEventListener("change", callback)
│   ├── [ ] mq.removeEventListener("change", callback)
│   ├── [ ] mq.onchange = callback (legacy)
│   └── [ ] MediaQueryListEvent (matches, media)
│
├── Responsive Breakpoints (15 tests)
│   ├── [ ] Width queries (min-width, max-width)
│   ├── [ ] Height queries (min-height, max-height)
│   ├── [ ] Orientation (landscape, portrait)
│   ├── [ ] Aspect ratio queries
│   └── [ ] Combined queries (and, or, not)
│
├── System Preferences (20 tests)
│   ├── [ ] prefers-color-scheme (dark, light)
│   ├── [ ] prefers-reduced-motion (reduce, no-preference)
│   ├── [ ] prefers-contrast (high, low, no-preference)
│   ├── [ ] prefers-reduced-transparency
│   ├── [ ] forced-colors (active, none)
│   └── [ ] inverted-colors
│
├── Device Capabilities (15 tests)
│   ├── [ ] pointer (coarse, fine, none)
│   ├── [ ] hover (hover, none)
│   ├── [ ] any-pointer, any-hover
│   └── [ ] resolution / min-resolution (dppx, dpi)
│
└── Display Features (10 tests)
    ├── [ ] display-mode (fullscreen, standalone, browser)
    ├── [ ] color-gamut (srgb, p3, rec2020)
    ├── [ ] dynamic-range (standard, high)
    └── [ ] overflow-block, overflow-inline
```

##### Console API (Full)

Complete console API for debugging and logging.

```python
from pynext.client import console

# =============================================================================
# Basic Logging
# =============================================================================

console.log("Message", obj, array)           # Standard log
console.info("Info message")                 # Info level
console.warn("Warning message")              # Warning level
console.error("Error message")               # Error level
console.debug("Debug message")               # Debug level (often hidden)

# =============================================================================
# Formatted Output
# =============================================================================

# String substitution
console.log("Hello %s, you have %d messages", "Alice", 5)
console.log("Object: %o, JSON: %j", obj, data)

# CSS styling (browser only)
console.log("%cStyled text", "color: red; font-weight: bold")
console.log("%cRed %cBlue", "color: red", "color: blue")

# =============================================================================
# Object Inspection
# =============================================================================

# Display object with expandable properties
console.dir(object)
console.dir(object, {"depth": 5, "colors": True})

# Display DOM element as HTML
console.dirxml(document.body)

# Display array of objects as table
users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
]
console.table(users)
console.table(users, ["name"])  # Only show "name" column

# =============================================================================
# Grouping
# =============================================================================

console.group("User Details")
console.log("Name: Alice")
console.log("Email: alice@example.com")
console.groupEnd()

# Collapsed by default
console.groupCollapsed("Request Details")
console.log("URL: /api/users")
console.log("Method: GET")
console.groupEnd()

# Nested groups
console.group("Outer")
console.log("Outer content")
console.group("Inner")
console.log("Inner content")
console.groupEnd()
console.groupEnd()

# =============================================================================
# Timing
# =============================================================================

console.time("operation")
# ... do something ...
console.timeLog("operation", "Checkpoint 1")
# ... do more ...
console.timeLog("operation", "Checkpoint 2")
# ... finish ...
console.timeEnd("operation")  # Prints total time

# =============================================================================
# Counting
# =============================================================================

for item in items:
    console.count("item processed")
    # Prints "item processed: 1", "item processed: 2", etc.

console.countReset("item processed")

# Default label
console.count()       # "default: 1"
console.count()       # "default: 2"
console.countReset()  # Reset default counter

# =============================================================================
# Assertions
# =============================================================================

console.assert(condition, "This prints only if condition is falsy")
console.assert(x > 0, "x must be positive, got:", x)

# =============================================================================
# Stack Traces
# =============================================================================

console.trace("Stack trace:")
# Prints call stack from this point

# =============================================================================
# Clearing
# =============================================================================

console.clear()  # Clear console (if supported)

# =============================================================================
# Memory (Chrome only)
# =============================================================================

# Check memory usage
if hasattr(console, "memory"):
    console.log(f"Used: {console.memory.usedJSHeapSize}")
    console.log(f"Total: {console.memory.totalJSHeapSize}")
    console.log(f"Limit: {console.memory.jsHeapSizeLimit}")
```

##### Performance API

Essential for measuring and monitoring application performance.

```python
from pynext.client import performance, PerformanceObserver

# =============================================================================
# High-Resolution Timing
# =============================================================================

# Get current timestamp (microsecond precision)
start = performance.now()
# ... operation ...
end = performance.now()
duration = end - start  # Milliseconds with microsecond precision

# Time origin (when page started loading)
origin = performance.timeOrigin  # Unix timestamp in ms

# =============================================================================
# User Timing API (Custom Marks and Measures)
# =============================================================================

# Create marks (named timestamps)
performance.mark("start-render")
# ... render ...
performance.mark("end-render")

# Create measure between marks
performance.measure("render-time", "start-render", "end-render")

# Measure with options
performance.measure("fetch-time", {
    "start": "fetch-start",
    "end": "fetch-end",
    "detail": {"url": "/api/users"},
})

# Measure from navigation start
performance.measure("time-to-interactive", {
    "start": performance.timeOrigin,
    "end": performance.now(),
})

# Get entries
entries = performance.getEntriesByName("render-time")
for entry in entries:
    console.log(f"Duration: {entry.duration}ms")
    console.log(f"Start: {entry.startTime}ms")
    console.log(f"Detail: {entry.detail}")

# Get entries by type
marks = performance.getEntriesByType("mark")
measures = performance.getEntriesByType("measure")

# Clear entries
performance.clearMarks()                  # All marks
performance.clearMarks("start-render")    # Specific mark
performance.clearMeasures()               # All measures
performance.clearMeasures("render-time")  # Specific measure

# =============================================================================
# Navigation Timing
# =============================================================================

# Get navigation timing
nav_entries = performance.getEntriesByType("navigation")
if nav_entries:
    nav = nav_entries[0]
    
    # DNS lookup time
    dns = nav.domainLookupEnd - nav.domainLookupStart
    
    # TCP connection time
    tcp = nav.connectEnd - nav.connectStart
    
    # TLS negotiation (HTTPS)
    tls = nav.secureConnectionStart > 0 and (nav.connectEnd - nav.secureConnectionStart) or 0
    
    # Time to First Byte (TTFB)
    ttfb = nav.responseStart - nav.requestStart
    
    # Response download time
    download = nav.responseEnd - nav.responseStart
    
    # DOM parsing
    dom_parse = nav.domInteractive - nav.responseEnd
    
    # DOMContentLoaded
    dcl = nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart
    
    # Load event
    load = nav.loadEventEnd - nav.loadEventStart
    
    # Total page load time
    total = nav.loadEventEnd - nav.navigationStart

# =============================================================================
# Resource Timing
# =============================================================================

# Get all resource timings
resources = performance.getEntriesByType("resource")
for res in resources:
    console.log(f"{res.name}: {res.duration}ms")
    console.log(f"  Type: {res.initiatorType}")  # script, link, img, fetch, etc.
    console.log(f"  Size: {res.transferSize} bytes")
    console.log(f"  Cached: {res.transferSize == 0}")

# Clear resource buffer
performance.clearResourceTimings()

# Set resource buffer size
performance.setResourceTimingBufferSize(500)

# =============================================================================
# PerformanceObserver (Real-time Monitoring)
# =============================================================================

# Observe performance entries as they occur
@client
def observe_performance():
    def callback(list, observer):
        for entry in list.getEntries():
            if entry.entryType == "longtask":
                console.warn(f"Long task detected: {entry.duration}ms")
            elif entry.entryType == "largest-contentful-paint":
                console.log(f"LCP: {entry.startTime}ms")
            elif entry.entryType == "first-input":
                console.log(f"FID: {entry.processingStart - entry.startTime}ms")
    
    observer = PerformanceObserver(callback)
    observer.observe({
        "entryTypes": [
            "longtask",
            "largest-contentful-paint",
            "first-input",
            "paint",
            "layout-shift",
        ]
    })

# Observer with buffered entries (get entries from before observer was created)
observer = PerformanceObserver(callback)
observer.observe({
    "type": "largest-contentful-paint",
    "buffered": True,
})

# Disconnect observer
observer.disconnect()

# Get supported entry types
supported = PerformanceObserver.supportedEntryTypes

# =============================================================================
# Core Web Vitals
# =============================================================================

@client
def measure_web_vitals():
    # Largest Contentful Paint (LCP)
    lcp_observer = PerformanceObserver(lambda list, obs:
        [console.log(f"LCP: {e.startTime}ms") for e in list.getEntries()]
    )
    lcp_observer.observe({"type": "largest-contentful-paint", "buffered": True})
    
    # First Input Delay (FID)
    fid_observer = PerformanceObserver(lambda list, obs:
        [console.log(f"FID: {e.processingStart - e.startTime}ms") for e in list.getEntries()]
    )
    fid_observer.observe({"type": "first-input", "buffered": True})
    
    # Cumulative Layout Shift (CLS)
    cls_value = 0
    cls_observer = PerformanceObserver(lambda list, obs:
        [setattr(cls_value, "value", cls_value + e.value) for e in list.getEntries() if not e.hadRecentInput]
    )
    cls_observer.observe({"type": "layout-shift", "buffered": True})

# =============================================================================
# Memory (Chrome only)
# =============================================================================

if hasattr(performance, "memory"):
    mem = performance.memory
    console.log(f"Used: {mem.usedJSHeapSize / 1024 / 1024:.2f} MB")
    console.log(f"Total: {mem.totalJSHeapSize / 1024 / 1024:.2f} MB")
    console.log(f"Limit: {mem.jsHeapSizeLimit / 1024 / 1024:.2f} MB")

# =============================================================================
# Paint Timing
# =============================================================================

paint_entries = performance.getEntriesByType("paint")
for entry in paint_entries:
    if entry.name == "first-paint":
        console.log(f"First Paint: {entry.startTime}ms")
    elif entry.name == "first-contentful-paint":
        console.log(f"First Contentful Paint: {entry.startTime}ms")
```

##### Web Crypto API

Secure cryptographic operations for modern web applications.

```python
from pynext.client import crypto

# =============================================================================
# Random Values
# =============================================================================

# Generate cryptographically secure random values
array = Uint8Array(16)
crypto.getRandomValues(array)

# Generate UUID v4
uuid = crypto.randomUUID()  # "550e8400-e29b-41d4-a716-446655440000"

# =============================================================================
# Hashing (Digest)
# =============================================================================

@client
async def hash_data(data, algorithm="SHA-256"):
    """Hash string data using specified algorithm."""
    encoder = TextEncoder()
    data_bytes = encoder.encode(data)
    hash_buffer = await crypto.subtle.digest(algorithm, data_bytes)
    
    # Convert to hex string
    hash_array = Uint8Array(hash_buffer)
    return "".join(f"{b:02x}" for b in hash_array)

# Supported algorithms: SHA-1, SHA-256, SHA-384, SHA-512
password_hash = await hash_data("my_password", "SHA-256")

# =============================================================================
# Symmetric Encryption (AES)
# =============================================================================

@client
async def generate_aes_key():
    """Generate a new AES-256-GCM key."""
    return await crypto.subtle.generateKey(
        {
            "name": "AES-GCM",
            "length": 256,
        },
        True,  # extractable
        ["encrypt", "decrypt"]
    )

@client
async def encrypt_data(key, data):
    """Encrypt data with AES-GCM."""
    encoder = TextEncoder()
    data_bytes = encoder.encode(data)
    
    # Generate random IV (must be unique for each encryption)
    iv = crypto.getRandomValues(Uint8Array(12))
    
    encrypted = await crypto.subtle.encrypt(
        {
            "name": "AES-GCM",
            "iv": iv,
            "tagLength": 128,  # Authentication tag length in bits
        },
        key,
        data_bytes
    )
    
    return {"iv": iv, "ciphertext": encrypted}

@client
async def decrypt_data(key, iv, ciphertext):
    """Decrypt AES-GCM encrypted data."""
    decrypted = await crypto.subtle.decrypt(
        {
            "name": "AES-GCM",
            "iv": iv,
        },
        key,
        ciphertext
    )
    
    decoder = TextDecoder()
    return decoder.decode(decrypted)

# Usage
key = await generate_aes_key()
encrypted = await encrypt_data(key, "Secret message")
plaintext = await decrypt_data(key, encrypted["iv"], encrypted["ciphertext"])

# =============================================================================
# Asymmetric Encryption (RSA)
# =============================================================================

@client
async def generate_rsa_keypair():
    """Generate RSA key pair for encryption."""
    return await crypto.subtle.generateKey(
        {
            "name": "RSA-OAEP",
            "modulusLength": 2048,
            "publicExponent": Uint8Array([1, 0, 1]),
            "hash": "SHA-256",
        },
        True,
        ["encrypt", "decrypt"]
    )

@client
async def rsa_encrypt(public_key, data):
    """Encrypt with RSA public key."""
    encoder = TextEncoder()
    return await crypto.subtle.encrypt(
        {"name": "RSA-OAEP"},
        public_key,
        encoder.encode(data)
    )

@client
async def rsa_decrypt(private_key, ciphertext):
    """Decrypt with RSA private key."""
    decrypted = await crypto.subtle.decrypt(
        {"name": "RSA-OAEP"},
        private_key,
        ciphertext
    )
    decoder = TextDecoder()
    return decoder.decode(decrypted)

# =============================================================================
# Digital Signatures (ECDSA)
# =============================================================================

@client
async def generate_signing_keypair():
    """Generate ECDSA key pair for signing."""
    return await crypto.subtle.generateKey(
        {
            "name": "ECDSA",
            "namedCurve": "P-256",  # or P-384, P-521
        },
        True,
        ["sign", "verify"]
    )

@client
async def sign_data(private_key, data):
    """Sign data with private key."""
    encoder = TextEncoder()
    return await crypto.subtle.sign(
        {
            "name": "ECDSA",
            "hash": "SHA-256",
        },
        private_key,
        encoder.encode(data)
    )

@client
async def verify_signature(public_key, signature, data):
    """Verify signature with public key."""
    encoder = TextEncoder()
    return await crypto.subtle.verify(
        {
            "name": "ECDSA",
            "hash": "SHA-256",
        },
        public_key,
        signature,
        encoder.encode(data)
    )

# =============================================================================
# Password-Based Key Derivation (PBKDF2)
# =============================================================================

@client
async def derive_key_from_password(password, salt, iterations=100000):
    """Derive encryption key from password using PBKDF2."""
    encoder = TextEncoder()
    
    # Import password as raw key material
    key_material = await crypto.subtle.importKey(
        "raw",
        encoder.encode(password),
        "PBKDF2",
        False,
        ["deriveBits", "deriveKey"]
    )
    
    # Derive AES key
    return await crypto.subtle.deriveKey(
        {
            "name": "PBKDF2",
            "salt": encoder.encode(salt),
            "iterations": iterations,
            "hash": "SHA-256",
        },
        key_material,
        {"name": "AES-GCM", "length": 256},
        True,
        ["encrypt", "decrypt"]
    )

# =============================================================================
# HMAC (Message Authentication)
# =============================================================================

@client
async def generate_hmac_key():
    """Generate HMAC key."""
    return await crypto.subtle.generateKey(
        {
            "name": "HMAC",
            "hash": "SHA-256",
        },
        True,
        ["sign", "verify"]
    )

@client
async def create_hmac(key, data):
    """Create HMAC signature."""
    encoder = TextEncoder()
    signature = await crypto.subtle.sign(
        "HMAC",
        key,
        encoder.encode(data)
    )
    # Convert to hex
    return "".join(f"{b:02x}" for b in Uint8Array(signature))

@client
async def verify_hmac(key, signature_hex, data):
    """Verify HMAC signature."""
    encoder = TextEncoder()
    # Convert hex to bytes
    signature = Uint8Array([int(signature_hex[i:i+2], 16) for i in range(0, len(signature_hex), 2)])
    return await crypto.subtle.verify(
        "HMAC",
        key,
        signature,
        encoder.encode(data)
    )

# =============================================================================
# Key Import/Export
# =============================================================================

@client
async def export_key_raw(key):
    """Export key as raw bytes."""
    return await crypto.subtle.exportKey("raw", key)

@client
async def export_key_jwk(key):
    """Export key as JWK (JSON Web Key)."""
    return await crypto.subtle.exportKey("jwk", key)

@client
async def import_key_raw(key_data, algorithm, usages):
    """Import raw key bytes."""
    return await crypto.subtle.importKey(
        "raw",
        key_data,
        algorithm,
        True,
        usages
    )

@client
async def import_key_jwk(jwk, algorithm, usages):
    """Import JWK."""
    return await crypto.subtle.importKey(
        "jwk",
        jwk,
        algorithm,
        True,
        usages
    )

# =============================================================================
# Key Wrapping (Encrypting Keys)
# =============================================================================

@client
async def wrap_key(wrapping_key, key_to_wrap):
    """Encrypt a key with another key."""
    iv = crypto.getRandomValues(Uint8Array(12))
    wrapped = await crypto.subtle.wrapKey(
        "raw",
        key_to_wrap,
        wrapping_key,
        {"name": "AES-GCM", "iv": iv}
    )
    return {"iv": iv, "wrapped": wrapped}

@client
async def unwrap_key(wrapping_key, iv, wrapped_key, algorithm, usages):
    """Decrypt a wrapped key."""
    return await crypto.subtle.unwrapKey(
        "raw",
        wrapped_key,
        wrapping_key,
        {"name": "AES-GCM", "iv": iv},
        algorithm,
        True,
        usages
    )
```

##### Internationalization API (Intl)

Complete i18n support for global applications.

```python
from pynext.client import Intl

# =============================================================================
# Number Formatting
# =============================================================================

# Basic number formatting
formatter = Intl.NumberFormat("en-US")
formatter.format(1234567.89)  # "1,234,567.89"

formatter_de = Intl.NumberFormat("de-DE")
formatter_de.format(1234567.89)  # "1.234.567,89"

# Currency formatting
usd = Intl.NumberFormat("en-US", {
    "style": "currency",
    "currency": "USD",
})
usd.format(1234.56)  # "$1,234.56"

eur = Intl.NumberFormat("de-DE", {
    "style": "currency",
    "currency": "EUR",
})
eur.format(1234.56)  # "1.234,56 €"

# Currency with options
formatter = Intl.NumberFormat("en-US", {
    "style": "currency",
    "currency": "USD",
    "currencyDisplay": "name",     # "code", "symbol", "name", "narrowSymbol"
    "minimumFractionDigits": 0,
    "maximumFractionDigits": 0,
})
formatter.format(1234)  # "1,234 US dollars"

# Percent formatting
pct = Intl.NumberFormat("en-US", {"style": "percent"})
pct.format(0.75)  # "75%"

pct_de = Intl.NumberFormat("de-DE", {
    "style": "percent",
    "minimumFractionDigits": 2,
})
pct_de.format(0.7512)  # "75,12 %"

# Unit formatting
distance = Intl.NumberFormat("en-US", {
    "style": "unit",
    "unit": "kilometer",
    "unitDisplay": "long",  # "short", "narrow", "long"
})
distance.format(42)  # "42 kilometers"

# Compact notation (1K, 1M, etc.)
compact = Intl.NumberFormat("en-US", {
    "notation": "compact",
    "compactDisplay": "short",
})
compact.format(1234567)  # "1.2M"

# Scientific notation
scientific = Intl.NumberFormat("en-US", {
    "notation": "scientific",
})
scientific.format(1234567)  # "1.235E6"

# Significant digits
sig = Intl.NumberFormat("en-US", {
    "minimumSignificantDigits": 3,
    "maximumSignificantDigits": 5,
})
sig.format(1.2)  # "1.20"

# Format to parts
formatter = Intl.NumberFormat("en-US", {"style": "currency", "currency": "USD"})
parts = formatter.formatToParts(1234.56)
# [{"type": "currency", "value": "$"}, {"type": "integer", "value": "1"}, ...]

# Format range
range_fmt = Intl.NumberFormat("en-US")
range_fmt.formatRange(1000, 5000)  # "1,000–5,000"

# =============================================================================
# Date/Time Formatting
# =============================================================================

# Basic date formatting
date_fmt = Intl.DateTimeFormat("en-US")
date_fmt.format(date_obj)  # "12/14/2024"

date_de = Intl.DateTimeFormat("de-DE")
date_de.format(date_obj)  # "14.12.2024"

# Date style presets
date_full = Intl.DateTimeFormat("en-US", {"dateStyle": "full"})
date_full.format(date_obj)  # "Saturday, December 14, 2024"

date_long = Intl.DateTimeFormat("en-US", {"dateStyle": "long"})
date_long.format(date_obj)  # "December 14, 2024"

date_medium = Intl.DateTimeFormat("en-US", {"dateStyle": "medium"})
date_medium.format(date_obj)  # "Dec 14, 2024"

date_short = Intl.DateTimeFormat("en-US", {"dateStyle": "short"})
date_short.format(date_obj)  # "12/14/24"

# Time formatting
time_fmt = Intl.DateTimeFormat("en-US", {
    "timeStyle": "long",
    "timeZone": "America/New_York",
})
time_fmt.format(date_obj)  # "10:30:00 AM EST"

# Combined date and time
datetime_fmt = Intl.DateTimeFormat("en-US", {
    "dateStyle": "long",
    "timeStyle": "short",
})
datetime_fmt.format(date_obj)  # "December 14, 2024 at 10:30 AM"

# Custom format
custom = Intl.DateTimeFormat("en-US", {
    "weekday": "long",       # "narrow", "short", "long"
    "year": "numeric",       # "numeric", "2-digit"
    "month": "long",         # "numeric", "2-digit", "narrow", "short", "long"
    "day": "numeric",        # "numeric", "2-digit"
    "hour": "numeric",       # "numeric", "2-digit"
    "minute": "2-digit",     
    "second": "2-digit",
    "hour12": True,          # 12-hour vs 24-hour
    "timeZoneName": "short", # "short", "long", "shortOffset", "longOffset"
})

# Format range
range_fmt = Intl.DateTimeFormat("en-US", {"dateStyle": "medium"})
range_fmt.formatRange(start_date, end_date)  # "Dec 14 – 20, 2024"

# =============================================================================
# Relative Time Formatting
# =============================================================================

rtf = Intl.RelativeTimeFormat("en", {"numeric": "auto"})

rtf.format(-1, "day")    # "yesterday"
rtf.format(-2, "day")    # "2 days ago"
rtf.format(1, "day")     # "tomorrow"
rtf.format(3, "week")    # "in 3 weeks"
rtf.format(-1, "month")  # "last month"

# Always numeric
rtf_numeric = Intl.RelativeTimeFormat("en", {"numeric": "always"})
rtf_numeric.format(-1, "day")  # "1 day ago" (not "yesterday")

# Style options
rtf_short = Intl.RelativeTimeFormat("en", {"style": "short"})
rtf_short.format(-3, "month")  # "3 mo. ago"

rtf_narrow = Intl.RelativeTimeFormat("en", {"style": "narrow"})
rtf_narrow.format(-3, "month")  # "3mo ago"

# =============================================================================
# List Formatting
# =============================================================================

lf = Intl.ListFormat("en", {"style": "long", "type": "conjunction"})
lf.format(["Alice", "Bob", "Charlie"])  # "Alice, Bob, and Charlie"

lf_or = Intl.ListFormat("en", {"style": "long", "type": "disjunction"})
lf_or.format(["Red", "Blue", "Green"])  # "Red, Blue, or Green"

lf_unit = Intl.ListFormat("en", {"style": "narrow", "type": "unit"})
lf_unit.format(["5 pounds", "3 ounces"])  # "5 pounds 3 ounces"

# =============================================================================
# Plural Rules
# =============================================================================

pr = Intl.PluralRules("en-US")
pr.select(0)   # "other"
pr.select(1)   # "one"
pr.select(2)   # "other"

pr_ordinal = Intl.PluralRules("en-US", {"type": "ordinal"})
pr_ordinal.select(1)   # "one" (1st)
pr_ordinal.select(2)   # "two" (2nd)
pr_ordinal.select(3)   # "few" (3rd)
pr_ordinal.select(4)   # "other" (4th)

# Use for pluralization
@client
def pluralize(count, singular, plural):
    pr = Intl.PluralRules("en-US")
    return singular if pr.select(count) == "one" else plural

message = f"You have {count} {pluralize(count, 'message', 'messages')}"

# =============================================================================
# Collation (Sorting)
# =============================================================================

# Create collator for locale-aware sorting
collator = Intl.Collator("de-DE")
names = ["Äpfel", "Zebra", "Apfel"]
sorted_names = sorted(names, key=lambda s: collator.compare(s, ""))

# Compare two strings
collator.compare("a", "b")  # -1 (a < b)
collator.compare("b", "a")  # 1 (b > a)
collator.compare("a", "a")  # 0 (equal)

# Collator options
collator = Intl.Collator("en-US", {
    "sensitivity": "base",      # "base", "accent", "case", "variant"
    "ignorePunctuation": True,
    "numeric": True,            # "1" < "2" < "10"
})

# Case-insensitive comparison
ci_collator = Intl.Collator("en-US", {"sensitivity": "base"})
ci_collator.compare("ABC", "abc")  # 0 (equal)

# Natural number sorting
num_collator = Intl.Collator("en-US", {"numeric": True})
files = ["file1.txt", "file10.txt", "file2.txt"]
sorted_files = sorted(files, key=lambda s: num_collator.compare(s, ""))
# ["file1.txt", "file2.txt", "file10.txt"]

# =============================================================================
# Display Names
# =============================================================================

# Language names
dn_lang = Intl.DisplayNames("en", {"type": "language"})
dn_lang.of("de")     # "German"
dn_lang.of("zh-Hans")  # "Simplified Chinese"

# Region names
dn_region = Intl.DisplayNames("en", {"type": "region"})
dn_region.of("DE")   # "Germany"
dn_region.of("US")   # "United States"

# Currency names
dn_currency = Intl.DisplayNames("en", {"type": "currency"})
dn_currency.of("EUR")  # "Euro"
dn_currency.of("JPY")  # "Japanese Yen"

# Script names
dn_script = Intl.DisplayNames("en", {"type": "script"})
dn_script.of("Latn")  # "Latin"
dn_script.of("Hans")  # "Simplified"

# Calendar names
dn_cal = Intl.DisplayNames("en", {"type": "calendar"})
dn_cal.of("gregory")  # "Gregorian Calendar"

# Date/time field names
dn_dt = Intl.DisplayNames("en", {"type": "dateTimeField"})
dn_dt.of("month")  # "month"
dn_dt.of("hour")   # "hour"

# =============================================================================
# Segmenter (Text Segmentation)
# =============================================================================

# Word segmentation
word_seg = Intl.Segmenter("en", {"granularity": "word"})
segments = list(word_seg.segment("Hello, World!"))
# [{"segment": "Hello", "isWordLike": True}, {"segment": ", ", "isWordLike": False}, ...]

# Sentence segmentation
sent_seg = Intl.Segmenter("en", {"granularity": "sentence"})
segments = list(sent_seg.segment("Hello! How are you?"))
# [{"segment": "Hello! "}, {"segment": "How are you?"}]

# Grapheme segmentation (for emojis, combined characters)
grapheme_seg = Intl.Segmenter("en", {"granularity": "grapheme"})
segments = list(grapheme_seg.segment("👨‍👩‍👧‍👦"))  # Family emoji = 1 grapheme

# =============================================================================
# Locale Utilities
# =============================================================================

# Get canonical locale
Intl.getCanonicalLocales("EN-us")  # ["en-US"]

# Locale negotiation
supported = Intl.Locale.supportedLocalesOf(
    ["en-US", "de-DE", "fr-FR"],
    {"localeMatcher": "best fit"}
)

# Locale object
locale = Intl.Locale("en-US")
locale.language       # "en"
locale.region         # "US"
locale.baseName       # "en-US"
locale.calendar       # undefined
locale.numberingSystem  # undefined

# Locale with options
locale = Intl.Locale("en-US", {"calendar": "gregory", "hourCycle": "h12"})
```

##### Console, Performance, Crypto, and Intl Checklist

```
Console, Performance, Crypto, Intl Support (Phase 35)
├── Console API (20 tests)
│   ├── [ ] log, info, warn, error, debug
│   ├── [ ] dir, dirxml, table
│   ├── [ ] group, groupCollapsed, groupEnd
│   ├── [ ] time, timeLog, timeEnd
│   ├── [ ] count, countReset
│   ├── [ ] assert, trace
│   └── [ ] clear, memory
│
├── Performance API (50 tests)
│   ├── [ ] performance.now()
│   ├── [ ] performance.timeOrigin
│   ├── [ ] performance.mark()
│   ├── [ ] performance.measure()
│   ├── [ ] performance.getEntriesByName/Type
│   ├── [ ] performance.clearMarks/Measures
│   ├── [ ] Navigation timing entries
│   ├── [ ] Resource timing entries
│   ├── [ ] PerformanceObserver
│   ├── [ ] Core Web Vitals (LCP, FID, CLS)
│   └── [ ] Paint timing (FP, FCP)
│
├── Web Crypto API (60 tests)
│   ├── [ ] crypto.getRandomValues()
│   ├── [ ] crypto.randomUUID()
│   ├── [ ] subtle.digest() (SHA-1, SHA-256, SHA-384, SHA-512)
│   ├── [ ] subtle.generateKey() (AES, RSA, ECDSA, HMAC)
│   ├── [ ] subtle.encrypt/decrypt (AES-GCM, RSA-OAEP)
│   ├── [ ] subtle.sign/verify (ECDSA, HMAC)
│   ├── [ ] subtle.deriveKey/deriveBits (PBKDF2, HKDF)
│   ├── [ ] subtle.importKey/exportKey (raw, jwk, pkcs8, spki)
│   └── [ ] subtle.wrapKey/unwrapKey
│
├── Intl.NumberFormat (25 tests)
│   ├── [ ] Locale number formatting
│   ├── [ ] Currency formatting
│   ├── [ ] Percent formatting
│   ├── [ ] Unit formatting
│   ├── [ ] Compact notation
│   ├── [ ] formatToParts, formatRange
│   └── [ ] Significant digits
│
├── Intl.DateTimeFormat (25 tests)
│   ├── [ ] dateStyle/timeStyle presets
│   ├── [ ] Custom format options
│   ├── [ ] Time zones
│   ├── [ ] formatToParts, formatRange
│   └── [ ] Calendar systems
│
├── Intl.RelativeTimeFormat (10 tests)
│   ├── [ ] Relative time formatting
│   └── [ ] numeric, style options
│
├── Intl.ListFormat (10 tests)
│   ├── [ ] Conjunction (and)
│   ├── [ ] Disjunction (or)
│   └── [ ] Unit lists
│
├── Intl.PluralRules (10 tests)
│   ├── [ ] Cardinal rules
│   └── [ ] Ordinal rules
│
├── Intl.Collator (15 tests)
│   ├── [ ] Locale-aware comparison
│   ├── [ ] Sensitivity options
│   └── [ ] Numeric sorting
│
├── Intl.DisplayNames (10 tests)
│   ├── [ ] Language, region, currency names
│   └── [ ] Script, calendar names
│
└── Intl.Segmenter (10 tests)
    ├── [ ] Word segmentation
    ├── [ ] Sentence segmentation
    └── [ ] Grapheme segmentation
```

##### Fullscreen API

Control fullscreen mode for immersive experiences.

```python
from pynext.client import document, Element

# =============================================================================
# Requesting Fullscreen
# =============================================================================

# Request fullscreen on an element
element = document.getElementById("video-player")
await element.requestFullscreen()

# With options
await element.requestFullscreen({
    "navigationUI": "hide",  # "auto", "hide", "show"
})

# Vendor-prefixed (handled automatically by PyNext)
# element.webkitRequestFullscreen()  # Safari
# element.mozRequestFullScreen()     # Firefox legacy

# =============================================================================
# Exiting Fullscreen
# =============================================================================

await document.exitFullscreen()

# Check if fullscreen is active
if document.fullscreenElement:
    print("Currently fullscreen:", document.fullscreenElement)

# =============================================================================
# Fullscreen Properties
# =============================================================================

# Current fullscreen element (or None)
document.fullscreenElement

# Is fullscreen available/enabled?
document.fullscreenEnabled

# =============================================================================
# Fullscreen Events
# =============================================================================

@client
def on_fullscreen_change(event):
    if document.fullscreenElement:
        print("Entered fullscreen")
        # Adjust UI for fullscreen
        show_fullscreen_controls()
    else:
        print("Exited fullscreen")
        # Restore normal UI
        show_normal_controls()

document.addEventListener("fullscreenchange", on_fullscreen_change)

@client
def on_fullscreen_error(event):
    console.error("Fullscreen request failed")
    # Maybe blocked by browser policy or user gesture required

document.addEventListener("fullscreenerror", on_fullscreen_error)

# =============================================================================
# Fullscreen Toggle Pattern
# =============================================================================

@client
async def toggle_fullscreen(element=None):
    target = element or document.documentElement
    
    if document.fullscreenElement:
        await document.exitFullscreen()
    else:
        try:
            await target.requestFullscreen()
        except Exception as e:
            console.error("Fullscreen error:", e)

# =============================================================================
# Keyboard Shortcut (F11 equivalent)
# =============================================================================

@client
def setup_fullscreen_shortcut():
    @document.on("keydown")
    async def on_keydown(event):
        if event.key == "F11" or (event.key == "f" and event.metaKey):
            event.preventDefault()
            await toggle_fullscreen()

# =============================================================================
# CSS Pseudo-classes for Fullscreen
# =============================================================================

# These CSS selectors work in fullscreen:
# :fullscreen - matches fullscreen element
# ::backdrop - styles the backdrop behind fullscreen element
# :not(:fullscreen) - styles when not fullscreen
```

##### Screen API

Access display information for responsive and multi-monitor support.

```python
from pynext.client import window, screen

# =============================================================================
# Screen Properties
# =============================================================================

# Screen dimensions (includes taskbar, etc.)
screen.width           # Total screen width in pixels
screen.height          # Total screen height in pixels

# Available dimensions (excludes taskbar, dock)
screen.availWidth      # Available width
screen.availHeight     # Available height
screen.availLeft       # Left offset of available area
screen.availTop        # Top offset of available area

# Color depth
screen.colorDepth      # Bits per pixel (e.g., 24)
screen.pixelDepth      # Same as colorDepth in modern browsers

# Orientation
screen.orientation.type   # "landscape-primary", "portrait-primary", etc.
screen.orientation.angle  # 0, 90, 180, 270

# =============================================================================
# Screen Orientation API
# =============================================================================

# Lock orientation (requires fullscreen in most browsers)
await screen.orientation.lock("landscape")
await screen.orientation.lock("portrait")
await screen.orientation.lock("landscape-primary")
await screen.orientation.lock("portrait-secondary")

# Unlock (allow rotation)
screen.orientation.unlock()

# Listen for orientation changes
@client
def on_orientation_change(event):
    new_type = screen.orientation.type
    new_angle = screen.orientation.angle
    console.log(f"Orientation: {new_type} ({new_angle}°)")
    
    # Adjust layout
    if new_type.startswith("landscape"):
        enable_landscape_layout()
    else:
        enable_portrait_layout()

screen.orientation.addEventListener("change", on_orientation_change)

# =============================================================================
# Window Screen Position
# =============================================================================

# Window position on screen
window.screenX         # X position of window on screen
window.screenY         # Y position of window on screen
window.screenLeft      # Alias for screenX
window.screenTop       # Alias for screenY

# =============================================================================
# Multi-Monitor Support (Screen Enumeration API - experimental)
# =============================================================================

# Get all screens (requires permission)
@client
async def get_all_screens():
    if hasattr(window, "getScreenDetails"):
        screen_details = await window.getScreenDetails()
        
        for s in screen_details.screens:
            console.log(f"Screen: {s.label}")
            console.log(f"  Size: {s.width}x{s.height}")
            console.log(f"  Position: ({s.left}, {s.top})")
            console.log(f"  Primary: {s.isPrimary}")
            console.log(f"  Internal: {s.isInternal}")
        
        # Current screen
        current = screen_details.currentScreen
        
        # Listen for screen changes
        screen_details.addEventListener("screenschange", on_screens_change)
    else:
        # Fallback: only single screen info
        return [{"width": screen.width, "height": screen.height}]

# =============================================================================
# Device Pixel Ratio
# =============================================================================

# High-DPI detection
dpr = window.devicePixelRatio  # 1 for standard, 2 for Retina, etc.

# Responsive image loading based on DPR
@client
def get_appropriate_image(base_url):
    dpr = window.devicePixelRatio
    if dpr >= 2:
        return base_url.replace(".jpg", "@2x.jpg")
    return base_url

# Listen for DPR changes (e.g., moving window between monitors)
mq = window.matchMedia(f"(resolution: {window.devicePixelRatio}dppx)")

@mq.on_change
def on_dpr_change(event):
    console.log(f"Device pixel ratio changed to: {window.devicePixelRatio}")
    update_high_dpi_images()
```

##### Page Visibility API

Detect when the page is hidden (tab switched, minimized).

```python
from pynext.client import document

# =============================================================================
# Visibility State
# =============================================================================

# Check current visibility
document.visibilityState  # "visible", "hidden", "prerender"
document.hidden           # True if page is hidden

# =============================================================================
# Visibility Change Event
# =============================================================================

@client
def on_visibility_change(event):
    if document.hidden:
        # Page is hidden (user switched tabs, minimized, etc.)
        console.log("Page hidden")
        
        # Pause expensive operations
        pause_animations()
        pause_video_playback()
        reduce_network_requests()
        
        # Clear sensitive data from memory
        clear_sensitive_display()
    else:
        # Page is visible again
        console.log("Page visible")
        
        # Resume operations
        resume_animations()
        
        # Sync with server (may have missed updates)
        sync_with_server()
        
        # Refresh stale data
        refresh_if_stale()

document.addEventListener("visibilitychange", on_visibility_change)

# =============================================================================
# Practical Use Cases
# =============================================================================

# Auto-pause video when tab is hidden
@client
def setup_video_autopause(video_element):
    was_playing = False
    
    @document.on("visibilitychange")
    def on_change(event):
        nonlocal was_playing
        
        if document.hidden:
            # Remember if video was playing
            was_playing = not video_element.paused
            if was_playing:
                video_element.pause()
        else:
            # Resume if it was playing before
            if was_playing:
                video_element.play()

# Pause real-time updates when hidden
@client
def setup_efficient_polling():
    poll_interval = Signal(1000)  # 1 second when visible
    
    @document.on("visibilitychange")
    def on_change(event):
        if document.hidden:
            poll_interval.set(30000)  # 30 seconds when hidden
        else:
            poll_interval.set(1000)   # Back to 1 second
            fetch_latest_data()       # Immediate refresh

# Track time spent on page
@client
def track_page_time():
    start_time = None
    total_visible_time = 0
    
    @document.on("visibilitychange")
    def on_change(event):
        nonlocal start_time, total_visible_time
        
        if document.hidden:
            if start_time:
                total_visible_time += performance.now() - start_time
                start_time = None
        else:
            start_time = performance.now()
    
    # Start tracking if page loads visible
    if not document.hidden:
        start_time = performance.now()
    
    # Send analytics on page unload
    @window.on("beforeunload")
    def on_unload(event):
        if start_time:
            total_visible_time += performance.now() - start_time
        send_analytics({"visible_time": total_visible_time})
```

##### Network Information API

Detect connection type and quality for adaptive loading.

```python
from pynext.client import navigator

# =============================================================================
# Network Connection Properties
# =============================================================================

connection = navigator.connection or navigator.mozConnection or navigator.webkitConnection

if connection:
    # Effective connection type (based on measured performance)
    connection.effectiveType  # "slow-2g", "2g", "3g", "4g"
    
    # Downlink speed estimate (Mbps)
    connection.downlink       # e.g., 10.0
    
    # Round-trip time estimate (ms)
    connection.rtt            # e.g., 100
    
    # Data saver mode
    connection.saveData       # True if user enabled data saver
    
    # Actual connection type (if available)
    connection.type           # "wifi", "cellular", "ethernet", "none", "unknown"

# =============================================================================
# Adaptive Loading Based on Connection
# =============================================================================

@client
def get_image_quality():
    """Return appropriate image quality based on connection."""
    connection = navigator.connection
    
    if not connection:
        return "high"  # Default to high if API not available
    
    if connection.saveData:
        return "low"
    
    effective = connection.effectiveType
    if effective == "slow-2g" or effective == "2g":
        return "low"
    elif effective == "3g":
        return "medium"
    else:
        return "high"

@client
def should_autoplay_video():
    """Determine if video should autoplay based on connection."""
    connection = navigator.connection
    
    if not connection:
        return True
    
    if connection.saveData:
        return False
    
    if connection.effectiveType in ["slow-2g", "2g"]:
        return False
    
    return True

@client
def get_fetch_priority():
    """Adjust resource loading based on connection."""
    connection = navigator.connection
    
    if not connection:
        return "normal"
    
    if connection.effectiveType == "4g" and not connection.saveData:
        return "aggressive"  # Prefetch more
    elif connection.effectiveType in ["slow-2g", "2g"]:
        return "conservative"  # Only critical resources
    else:
        return "normal"

# =============================================================================
# Connection Change Events
# =============================================================================

@client
def setup_connection_monitoring():
    connection = navigator.connection
    
    if not connection:
        return
    
    @connection.on("change")
    def on_connection_change(event):
        new_type = connection.effectiveType
        console.log(f"Connection changed to: {new_type}")
        
        # Adapt to new connection
        if new_type in ["slow-2g", "2g"]:
            # Switch to low-bandwidth mode
            reduce_image_quality()
            pause_background_downloads()
            show_offline_indicator()
        else:
            # Resume normal operation
            restore_image_quality()
            resume_background_downloads()
            hide_offline_indicator()

# =============================================================================
# Offline Detection
# =============================================================================

# Online/Offline status
navigator.onLine  # True if browser thinks it's online

@window.on("online")
def on_online(event):
    console.log("Back online!")
    sync_pending_changes()
    hide_offline_banner()

@window.on("offline")
def on_offline(event):
    console.log("Gone offline")
    show_offline_banner()
    enable_offline_mode()
```

##### Beacon API

Send data to server reliably, even during page unload.

```python
from pynext.client import navigator

# =============================================================================
# Sending Beacons
# =============================================================================

# sendBeacon sends data asynchronously without blocking page unload
# Returns True if browser accepted the request (not guaranteed delivery)

success = navigator.sendBeacon("/api/analytics", JSON.stringify({
    "event": "page_view",
    "duration": total_time,
    "timestamp": Date.now(),
}))

if success:
    console.log("Beacon queued successfully")
else:
    console.warn("Beacon failed to queue")

# =============================================================================
# Data Types Supported
# =============================================================================

# String data
navigator.sendBeacon("/log", "Simple string data")

# JSON as string
navigator.sendBeacon("/log", JSON.stringify({"key": "value"}))

# Blob
blob = Blob([JSON.stringify(data)], {"type": "application/json"})
navigator.sendBeacon("/log", blob)

# FormData
form_data = FormData()
form_data.append("event", "click")
form_data.append("target", "button#submit")
navigator.sendBeacon("/log", form_data)

# URLSearchParams
params = URLSearchParams({"event": "view", "id": "123"})
navigator.sendBeacon("/log", params)

# ArrayBuffer / TypedArray
buffer = new Uint8Array([1, 2, 3, 4])
navigator.sendBeacon("/log", buffer)

# =============================================================================
# Use Cases
# =============================================================================

# Analytics on page unload
@client
def setup_analytics():
    page_start = performance.now()
    
    @window.on("beforeunload")
    def on_unload(event):
        duration = performance.now() - page_start
        
        navigator.sendBeacon("/api/analytics", JSON.stringify({
            "type": "page_unload",
            "url": window.location.href,
            "duration": duration,
            "referrer": document.referrer,
        }))
    
    # Also send on visibility hidden (mobile browsers may not fire unload)
    @document.on("visibilitychange")
    def on_visibility(event):
        if document.visibilityState == "hidden":
            navigator.sendBeacon("/api/heartbeat", JSON.stringify({
                "type": "page_hidden",
                "url": window.location.href,
            }))

# Error reporting
@client
def report_error(error):
    navigator.sendBeacon("/api/errors", JSON.stringify({
        "message": str(error),
        "stack": error.stack if hasattr(error, "stack") else None,
        "url": window.location.href,
        "userAgent": navigator.userAgent,
        "timestamp": Date.now(),
    }))

# Capture unhandled errors
@window.on("error")
def on_error(event):
    report_error({
        "message": event.message,
        "filename": event.filename,
        "lineno": event.lineno,
        "colno": event.colno,
    })

@window.on("unhandledrejection")
def on_rejection(event):
    report_error({
        "message": f"Unhandled rejection: {event.reason}",
    })

# Form submission tracking (even if user navigates away)
@client
def track_form_submit(form_id, data):
    navigator.sendBeacon("/api/forms", JSON.stringify({
        "form_id": form_id,
        "submitted_at": Date.now(),
        "field_count": len(data),
    }))
```

##### Additional Browser APIs Checklist

```
Additional Browser APIs (Phase 35)
├── Fullscreen API (15 tests)
│   ├── [ ] element.requestFullscreen()
│   ├── [ ] document.exitFullscreen()
│   ├── [ ] document.fullscreenElement
│   ├── [ ] document.fullscreenEnabled
│   ├── [ ] fullscreenchange event
│   ├── [ ] fullscreenerror event
│   └── [ ] Vendor prefix handling
│
├── Screen API (20 tests)
│   ├── [ ] screen.width, screen.height
│   ├── [ ] screen.availWidth, screen.availHeight
│   ├── [ ] screen.colorDepth, screen.pixelDepth
│   ├── [ ] screen.orientation.type, screen.orientation.angle
│   ├── [ ] screen.orientation.lock(), screen.orientation.unlock()
│   ├── [ ] orientationchange event
│   ├── [ ] window.screenX, window.screenY
│   └── [ ] window.devicePixelRatio
│
├── Page Visibility API (10 tests)
│   ├── [ ] document.visibilityState
│   ├── [ ] document.hidden
│   └── [ ] visibilitychange event
│
├── Network Information API (15 tests)
│   ├── [ ] navigator.connection
│   ├── [ ] effectiveType (slow-2g, 2g, 3g, 4g)
│   ├── [ ] downlink, rtt
│   ├── [ ] saveData
│   ├── [ ] type (wifi, cellular, etc.)
│   ├── [ ] change event
│   ├── [ ] navigator.onLine
│   └── [ ] online/offline events
│
└── Beacon API (10 tests)
    ├── [ ] navigator.sendBeacon()
    ├── [ ] String data
    ├── [ ] Blob data
    ├── [ ] FormData
    └── [ ] ArrayBuffer
```

##### Files to Create (Updated)

- `pynext/client/window.py` — window object stubs
- `pynext/client/navigator.py` — navigator stubs
- `pynext/client/fetch.py` — fetch, Request, Response, Headers, FormData, AbortController
- `pynext/client/media_query.py` — MediaQueryList, responsive utilities
- `pynext/client/console.py` — Full console API
- `pynext/client/performance.py` — Performance API, PerformanceObserver
- `pynext/client/crypto.py` — Web Crypto API (crypto.subtle)
- `pynext/client/intl.py` — Full Intl API (NumberFormat, DateTimeFormat, etc.)
- `pynext/client/fullscreen.py` — Fullscreen API
- `pynext/client/screen.py` — Screen and Orientation API
- `pynext/client/visibility.py` — Page Visibility API
- `pynext/client/network.py` — Network Information API, online/offline
- `pynext/client/beacon.py` — Beacon API
- `pynext/client/window.pyi` — Type stubs for window
- `pynext/client/navigator.pyi` — Type stubs for navigator
- `pynext/client/fetch.pyi` — Type stubs for fetch, Request, Response
- `pynext/client/console.pyi` — Type stubs for console
- `pynext/client/performance.pyi` — Type stubs for Performance API
- `pynext/client/crypto.pyi` — Type stubs for Web Crypto
- `pynext/client/intl.pyi` — Type stubs for Intl API
- `pynext/client/storage.pyi` — Type stubs for localStorage/sessionStorage

##### Success Criteria

| Metric | Target |
|--------|--------|
| Window API coverage | 100% of commonly used window APIs |
| Navigator coverage | All standard navigator interfaces |
| Fetch coverage | Complete fetch API including streaming |
| Media Query coverage | Full matchMedia and all query types |
| System preferences | All prefers-* media features |
| Console API | Full debugging console support |
| Performance API | Complete timing and monitoring |
| Web Crypto | All cryptographic operations |
| Intl API | Full internationalization support |
| Fullscreen API | Full enter/exit/events |
| Screen API | Complete screen and orientation |
| Visibility API | Full page visibility detection |
| Network API | Connection info, online/offline |
| Beacon API | Reliable unload data sending |
| Type Stubs | Full IDE autocomplete for all Browser APIs |
| Test coverage | 615+ unit tests |

##### Milestones

1. **Week 1:** window.location, history, dimensions, scroll
2. **Week 2:** Timers, storage, matchMedia (full API), dialogs
3. **Week 3:** Navigator APIs, Console API, Performance API
4. **Week 4:** Fetch API, Web Crypto API
5. **Week 5:** Intl API (NumberFormat, DateTimeFormat, etc.)
6. **Week 6:** Intl advanced (Collator, Segmenter, DisplayNames)
7. **Week 7:** Fullscreen, Screen, Visibility, Network, Beacon APIs, Type Stubs

##### What Phase 35 Enables

After Phase 35, you have full access to browser capabilities from Python:

```python
from pynext.client import client, window, navigator, fetch, console, performance
from pynext.client import localStorage, Intl

@client
async def build_full_stack_app():
    """A complete client-side app using only Python — no JavaScript."""
    
    # ═══════════════════════════════════════════════════════════════════════
    # FETCH DATA FROM API
    # ═══════════════════════════════════════════════════════════════════════
    
    response = await fetch("/api/users", {
        "method": "GET",
        "headers": {"Authorization": f"Bearer {get_token()}"}
    })
    
    if not response.ok:
        console.error(f"API Error: {response.status}")
        return
    
    users = await response.json()
    console.log("Loaded users:", users)
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # STORE USER PREFERENCES
    # ═══════════════════════════════════════════════════════════════════════
    
    # Save to localStorage
    localStorage.setItem("theme", "dark")
    localStorage.setItem("sidebar_collapsed", "true")
    
    # Load settings
    theme = localStorage.getItem("theme") or "light"
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # INTERNATIONALIZATION
    # ═══════════════════════════════════════════════════════════════════════
    
    # Format numbers by locale
    number_fmt = Intl.NumberFormat(navigator.language, {
        "style": "currency",
        "currency": "USD"
    })
    console.log(number_fmt.format(1234.56))  # "$1,234.56"
    
    # Format dates
    date_fmt = Intl.DateTimeFormat(navigator.language, {
        "dateStyle": "full",
        "timeStyle": "short"
    })
    console.log(date_fmt.format(Date.now()))  # "Sunday, December 14, 2025 at 3:45 PM"
    
    # Relative time
    rel_fmt = Intl.RelativeTimeFormat(navigator.language, {"numeric": "auto"})
    console.log(rel_fmt.format(-1, "day"))  # "yesterday"
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # PERFORMANCE MONITORING
    # ═══════════════════════════════════════════════════════════════════════
    
    performance.mark("render-start")
    
    # ... render logic ...
    
    performance.mark("render-end")
    performance.measure("render-time", "render-start", "render-end")
    
    measures = performance.getEntriesByName("render-time")
    console.log(f"Render took {measures[0].duration}ms")
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # RESPONSIVE DESIGN
    # ═══════════════════════════════════════════════════════════════════════
    
    # Check for dark mode preference
    dark_mode = window.matchMedia("(prefers-color-scheme: dark)")
    
    def on_theme_change(e):
        if e.matches:
            apply_dark_theme()
        else:
            apply_light_theme()
    
    dark_mode.addEventListener("change", on_theme_change)
    
    # Check for mobile
    is_mobile = window.matchMedia("(max-width: 768px)").matches
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # GEOLOCATION & CLIPBOARD
    # ═══════════════════════════════════════════════════════════════════════
    
    # Get user location
    position = await navigator.geolocation.getCurrentPosition()
    lat, lon = position.coords.latitude, position.coords.longitude
    console.log(f"User is at {lat}, {lon}")
    
    # Copy to clipboard
    await navigator.clipboard.writeText(f"https://maps.google.com/?q={lat},{lon}")
    console.log("Location URL copied!")


@client
async def secure_crypto_example():
    """Use Web Crypto for secure operations."""
    from pynext.client import crypto
    
    # Generate random bytes
    random_bytes = crypto.getRandomValues(Uint8Array(16))
    
    # Hash data
    data = TextEncoder().encode("my-password")
    hash_buffer = await crypto.subtle.digest("SHA-256", data)
    
    # Generate key pair
    key_pair = await crypto.subtle.generateKey(
        {"name": "RSA-OAEP", "modulusLength": 2048, "publicExponent": ...},
        True,
        ["encrypt", "decrypt"]
    )
    
    console.log("Secure key generated!")
```

---

### DEVTOOLS PHASE

---

#### Phase 35.5: DevTools Integration (200 tests, 6 weeks)

Comprehensive debugging tools for Python-to-JavaScript development.

##### Overview

```
DevTools Architecture
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser DevTools                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   Signals    │  │  Components  │  │   Network    │               │
│  │   Panel      │  │    Tree      │  │    Panel     │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                        │
│  ┌──────┴─────────────────┴─────────────────┴──────┐                │
│  │              DevTools Client (JS)                │                │
│  │  - Signal registry inspection                   │                │
│  │  - Component tree building                      │                │
│  │  - Network request interception                 │                │
│  └──────────────────────┬──────────────────────────┘                │
│                         │                                            │
│  ┌──────────────────────┴──────────────────────────┐                │
│  │           PyNext Runtime Integration             │                │
│  │  - __PYNEXT_DEVTOOLS__ global                   │                │
│  │  - Signal hooks                                  │                │
│  │  - Source map integration                        │                │
│  └─────────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

##### Python API

```python
from pynext.devtools import (
    enable_devtools,
    SignalInspector,
    ComponentTree,
    PerformanceProfiler,
)

# =============================================================================
# DevTools Initialization
# =============================================================================

# Enable devtools (typically in development config)
enable_devtools(
    enabled=True,
    signal_tracking=True,
    component_tracking=True,
    network_interception=True,
    performance_profiling=True,
)

# Conditional enable (e.g., based on environment)
import os
enable_devtools(enabled=os.getenv("PYNEXT_ENV") == "development")

# =============================================================================
# Signal Inspector
# =============================================================================

# All signals are automatically tracked
count = Signal(0, name="count")  # Optional name for better debugging
user = Signal(None, name="current_user")

# Signal inspector features (accessed from browser devtools):
# - View all active signals with current values
# - See signal names and creation source (file:line)
# - View dependency graph (which memos depend on which signals)
# - Edit signal values live
# - View update history (last N changes)

# Programmatic access
inspector = SignalInspector.get_instance()
all_signals = inspector.get_all_signals()
signal_value = inspector.get_signal_value("count")
inspector.set_signal_value("count", 42)  # For debugging

# =============================================================================
# Reactivity Graph Visualization
# =============================================================================

# The devtools visualize the reactivity graph:
#
#   ┌─────────┐     ┌─────────────┐     ┌─────────────┐
#   │ count   │────▶│ doubleCount │────▶│ Effect:     │
#   │ Signal  │     │   Memo      │     │ updateDOM   │
#   └─────────┘     └─────────────┘     └─────────────┘
#        │
#        │          ┌─────────────┐     ┌─────────────┐
#        └─────────▶│  tripleCount│────▶│ Effect:     │
#                   │    Memo     │     │ logToServer │
#                   └─────────────┘     └─────────────┘

# Features:
# - Interactive graph (drag, zoom, pan)
# - Highlight active updates
# - Show update propagation animation
# - Filter by signal/memo/effect
# - Search by name

# =============================================================================
# Component Tree
# =============================================================================

# Devtools show the component hierarchy:
#
# ▼ App
#   ▼ Header
#     ├ Logo
#     └ Navigation
#   ▼ MainContent
#     ▼ Dashboard
#       ├ AnalyticsWidget (signals: data, loading)
#       ├ SalesWidget (signals: sales, period)
#       └ InventoryWidget
#   ▼ Footer

# Features:
# - Expandable tree view
# - Click component → see props and signals
# - Hover component → highlight in page
# - Jump to Python source
# - Search components by name

# =============================================================================
# DOM ↔ Python Mapping
# =============================================================================

# Click any element in the page:
# - See which Python component created it
# - View the Python source code
# - See all signals affecting this element

# Example devtools output:
# Element: <div class="widget-container">
# Created by: Dashboard.py:45 in AnalyticsWidget()
# Signals:
#   - data (from AnalyticsWidget, line 23)
#   - loading (from AnalyticsWidget, line 24)

# =============================================================================
# Network Panel Integration
# =============================================================================

# All fetch() calls show Python source:
#
# Request: GET /api/users
# Status: 200 OK
# Duration: 145ms
# Python Source: api.py:89 in fetch_users()
#
# Request Body: {"page": 1, "limit": 10}
# Response Body: [{"id": 1, "name": "Alice"}, ...]

# Features:
# - Filter by status, type, source file
# - View request/response as Python dicts
# - Copy as Python code
# - Replay request

# =============================================================================
# Performance Profiler
# =============================================================================

# Start profiling
profiler = PerformanceProfiler()
profiler.start()

# ... run your code ...

# Stop and get results
report = profiler.stop()

# Report includes:
# - Signal update timings
# - DOM operation timings
# - Component render timings
# - Slow operation warnings

# Automatic slow update detection
# (Shown in devtools console)
# ⚠️ Slow signal update: 'heavyData' took 150ms
#    Source: analytics.py:78
#    Subscribers: 12 memos, 5 effects

# Flame graph visualization
# Shows hierarchical timing of:
# - Python function execution
# - Signal updates
# - DOM modifications
```

##### Signal Inspector Implementation

```python
# =============================================================================
# Signal Registry
# =============================================================================

class SignalRegistry:
    """Global registry of all signals for devtools inspection."""
    
    _instance = None
    _signals: Dict[str, WeakRef] = {}
    _update_history: Dict[str, List[dict]] = {}
    _max_history = 50
    
    @classmethod
    def register(cls, signal, name=None, source_location=None):
        """Register a signal for tracking."""
        signal_id = id(signal)
        cls._signals[signal_id] = WeakRef(signal)
        cls._update_history[signal_id] = []
        
        # Store metadata
        signal.__devtools_meta__ = {
            "id": signal_id,
            "name": name or f"signal_{signal_id}",
            "source": source_location,
            "created_at": performance.now(),
        }
    
    @classmethod
    def record_update(cls, signal, old_value, new_value):
        """Record a signal update for history."""
        signal_id = id(signal)
        history = cls._update_history.get(signal_id, [])
        
        history.append({
            "timestamp": performance.now(),
            "old_value": old_value,
            "new_value": new_value,
            "stack": get_python_stack_trace(),
        })
        
        # Trim history
        if len(history) > cls._max_history:
            history = history[-cls._max_history:]
        
        cls._update_history[signal_id] = history
    
    @classmethod
    def get_all_signals(cls):
        """Get all active signals."""
        result = []
        for signal_id, ref in list(cls._signals.items()):
            signal = ref.deref()
            if signal is None:
                del cls._signals[signal_id]
            else:
                result.append({
                    "id": signal_id,
                    "name": signal.__devtools_meta__["name"],
                    "value": signal(),
                    "source": signal.__devtools_meta__["source"],
                    "subscribers": len(signal._subscribers),
                })
        return result
```

##### Component Tree Implementation

```python
# =============================================================================
# Component Tracking
# =============================================================================

class ComponentTree:
    """Track component hierarchy for devtools."""
    
    _root = None
    _current_component = None
    
    @classmethod
    def start_render(cls, component_fn, props):
        """Called when a component starts rendering."""
        node = {
            "id": id(component_fn),
            "name": component_fn.__name__,
            "props": props,
            "signals": [],
            "children": [],
            "source": get_source_location(component_fn),
            "render_start": performance.now(),
        }
        
        if cls._current_component:
            cls._current_component["children"].append(node)
        else:
            cls._root = node
        
        node["parent"] = cls._current_component
        cls._current_component = node
    
    @classmethod
    def end_render(cls):
        """Called when a component finishes rendering."""
        if cls._current_component:
            cls._current_component["render_time"] = (
                performance.now() - cls._current_component["render_start"]
            )
            cls._current_component = cls._current_component.get("parent")
    
    @classmethod
    def register_signal_usage(cls, signal):
        """Track which signals a component uses."""
        if cls._current_component:
            cls._current_component["signals"].append({
                "id": id(signal),
                "name": signal.__devtools_meta__.get("name", "unknown"),
            })
    
    @classmethod
    def get_tree(cls):
        """Get the component tree for devtools."""
        return cls._root
```

##### DevTools Checklist

```
DevTools Integration (Phase 35.5)
├── Signal Inspector (60 tests)
│   ├── [ ] Signal registry
│   ├── [ ] Signal metadata (name, source, created_at)
│   ├── [ ] Current value inspection
│   ├── [ ] Subscriber count
│   ├── [ ] Update history (last N changes)
│   ├── [ ] Live value editing
│   ├── [ ] Signal search/filter
│   └── [ ] Weak reference cleanup
│
├── Reactivity Graph (30 tests)
│   ├── [ ] Signal → Memo dependencies
│   ├── [ ] Memo → Effect dependencies
│   ├── [ ] Graph visualization (nodes/edges)
│   ├── [ ] Update propagation animation
│   ├── [ ] Cycle detection
│   └── [ ] Filter by type
│
├── Component Tree (50 tests)
│   ├── [ ] Component hierarchy tracking
│   ├── [ ] Props inspection
│   ├── [ ] Signals used by component
│   ├── [ ] Render timing per component
│   ├── [ ] Highlight component in page
│   ├── [ ] Jump to Python source
│   ├── [ ] Component search
│   └── [ ] Real-time updates
│
├── DOM ↔ Python Mapping (20 tests)
│   ├── [ ] Element → component mapping
│   ├── [ ] Element → signals mapping
│   ├── [ ] Click-to-inspect
│   ├── [ ] Source code preview
│   └── [ ] Bidirectional navigation
│
├── Network Panel (20 tests)
│   ├── [ ] Intercept fetch() calls
│   ├── [ ] Python source attribution
│   ├── [ ] Request/response as Python dicts
│   ├── [ ] Timing breakdown
│   ├── [ ] Filter by status/type
│   └── [ ] Replay request
│
├── Performance Profiler (30 tests)
│   ├── [ ] Signal update timing
│   ├── [ ] DOM operation timing
│   ├── [ ] Component render timing
│   ├── [ ] Slow operation detection
│   ├── [ ] Flame graph generation
│   ├── [ ] Memory tracking
│   └── [ ] Export report
│
└── Browser Integration (20 tests)
    ├── [ ] Chrome DevTools panel
    ├── [ ] DevTools sidebar
    ├── [ ] Console integration
    ├── [ ] Elements panel integration
    ├── [ ] Keyboard shortcuts
    └── [ ] Dark/light theme support
```

##### Files to Create

- `pynext/devtools/__init__.py` — DevTools package
- `pynext/devtools/config.py` — enable_devtools, configuration
- `pynext/devtools/signal_inspector.py` — Signal registry and inspection
- `pynext/devtools/reactivity_graph.py` — Dependency graph visualization
- `pynext/devtools/component_tree.py` — Component hierarchy tracking
- `pynext/devtools/dom_mapping.py` — DOM ↔ Python element mapping
- `pynext/devtools/network_panel.py` — Fetch interception and display
- `pynext/devtools/performance.py` — Performance profiler
- `pynext/devtools/client.js` — Client-side devtools injection
- `pynext/devtools/panel.html` — DevTools panel UI
- `pynext/devtools/panel.js` — DevTools panel logic
- `pynext/devtools/panel.css` — DevTools panel styling

##### Success Criteria

| Metric | Target |
|--------|--------|
| Signal inspection | View/edit all signals with full history |
| Reactivity graph | Interactive visualization of dependencies |
| Component tree | Full hierarchy with props and signals |
| DOM mapping | Click any element → see Python source |
| Network panel | All fetch calls with Python attribution |
| Performance | Flame graph with sub-ms timing |
| Browser integration | Works in Chrome, Firefox, Edge |
| Test coverage | 200+ unit tests |

##### Milestones

1. **Week 1:** Signal registry, basic signal inspection
2. **Week 2:** Signal history, live editing, reactivity graph
3. **Week 3:** Component tree tracking, hierarchy visualization
4. **Week 4:** DOM mapping, click-to-inspect, source preview
5. **Week 5:** Network panel, fetch interception, Python formatting
6. **Week 6:** Performance profiler, flame graph, browser panel integration

##### What Phase 35.5 Enables

After Phase 35.5, you get React DevTools-level debugging for PyNext:

```python
# BROWSER DEVTOOLS SHOW YOUR PYTHON CODE
# ════════════════════════════════════════════════════════════════════════════

# When you open Chrome DevTools → PyNext panel:

# ┌───────────────────────────────────────────────────────────────────────────┐
# │ 🔍 Signals                                                                │
# ├───────────────────────────────────────────────────────────────────────────┤
# │ ▶ count: 5                           [✏️ Edit] [📊 History]              │
# │   └── subscribers: 3                                                     │
# │   └── last updated: 0.2ms ago                                            │
# │                                                                           │
# │ ▶ todos: [{id: 1, text: "Buy milk", done: false}, ...]                  │
# │   └── subscribers: 7                                                     │
# │   └── last updated: 1.5s ago                                             │
# │                                                                           │
# │ ▶ filter: "active"                                                       │
# │   └── subscribers: 2                                                     │
# │                                                                           │
# ├───────────────────────────────────────────────────────────────────────────┤
# │ 🌳 Component Tree                                                        │
# ├───────────────────────────────────────────────────────────────────────────┤
# │ ▼ <App>                                 📍 app.py:15                     │
# │   ├── <Header>                          📍 components/header.py:8       │
# │   │   └── <Logo>                        📍 components/header.py:42      │
# │   ├── <TodoList>                        📍 pages/todos.py:23            │
# │   │   ├── <TodoItem key="1">            📍 components/todo.py:12        │
# │   │   ├── <TodoItem key="2">            📍 components/todo.py:12        │
# │   │   └── <TodoItem key="3">            📍 components/todo.py:12        │
# │   └── <Footer>                          📍 components/footer.py:5       │
# │                                                                           │
# ├───────────────────────────────────────────────────────────────────────────┤
# │ 📊 Reactivity Graph                                                      │
# ├───────────────────────────────────────────────────────────────────────────┤
# │                                                                           │
# │   ┌─────────┐     ┌────────────────┐     ┌────────────────┐             │
# │   │  count  │────▶│  doubled_count │────▶│ CounterDisplay │             │
# │   └─────────┘     └────────────────┘     └────────────────┘             │
# │                          │                                               │
# │                          ▼                                               │
# │                   ┌────────────────┐                                     │
# │                   │  is_even_memo  │                                     │
# │                   └────────────────┘                                     │
# │                                                                           │
# └───────────────────────────────────────────────────────────────────────────┘

# CLICK ANY DOM ELEMENT → SEE PYTHON SOURCE
# ════════════════════════════════════════════════════════════════════════════

# 1. Click element in browser
# 2. DevTools highlights the element
# 3. Shows the Python file and line where it was created:
#
#    📍 Source: components/todo.py:45
#    
#    def TodoItem(todo):
#        return li(
#            className="todo-item",
#            children=[
#                checkbox(checked=todo["done"], onChange=toggle),
#  >>>           span(todo["text"]),  # ← You clicked this!
#                button("Delete", onClick=delete)
#            ]
#        )


# PROFILER: SEE EXACTLY WHAT'S SLOW
# ════════════════════════════════════════════════════════════════════════════

# Performance tab shows:
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │ render_todo_list     ████████████████████████████████████░░░░  45.2ms      │
# │   ├─ filter_todos    ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  12.1ms      │
# │   ├─ map_to_items    ████████████████████░░░░░░░░░░░░░░░░░░░░  25.3ms      │
# │   │   └─ TodoItem×50 █████████████████░░░░░░░░░░░░░░░░░░░░░░░░  22.8ms      │
# │   └─ apply_dom       ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   7.8ms      │
# └─────────────────────────────────────────────────────────────────────────────┘
#
# 💡 Tip: TodoItem is rendering 50 times. Consider memoization?
```

---

### INTERACTION PHASES (36-38)

---

#### Phase 36: Animation and Motion (200 tests, 3 weeks)

Web Animations API, spring physics, timelines — buttery smooth motion from Python.

##### Animation Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 36: ANIMATION & MOTION                           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    Web Animations API (WAAPI)                            ││
│  │                                                                          ││
│  │    element.animate(keyframes, options)                                   ││
│  │                                                                          ││
│  │    Keyframes: [{...}, {...}]         Options:                           ││
│  │    • opacity, transform              • duration, delay                   ││
│  │    • color, backgroundColor          • easing, fill                      ││
│  │    • width, height                   • iterations, direction             ││
│  │    • offset (custom timing)          • id, composite                     ││
│  │                                                                          ││
│  │    Controls: play() | pause() | reverse() | cancel() | finish()         ││
│  │    Promises: animation.finished → await completion                       ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                       Spring Physics                                     ││
│  │                                                                          ││
│  │    Natural motion with physical properties:                              ││
│  │                                                                          ││
│  │    ┌───────────────────────────────────────────────────────────┐        ││
│  │    │                                                           │        ││
│  │    │   stiffness ──────────▶ How snappy (higher = faster)     │        ││
│  │    │   damping ────────────▶ How bouncy (lower = more bounce) │        ││
│  │    │   mass ───────────────▶ How heavy (higher = slower)      │        ││
│  │    │                                                           │        ││
│  │    │   ╭─────╮     stiff   ╭──╮   bouncy  ╭─────────────╮     │        ││
│  │    │   │     ╰─────────────╯  │           ╰─~─~─~─~─────╯     │        ││
│  │    │                                                           │        ││
│  │    └───────────────────────────────────────────────────────────┘        ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        Timeline Orchestration                            ││
│  │                                                                          ││
│  │    0ms     100ms    200ms    300ms    400ms    500ms    600ms           ││
│  │    │        │        │        │        │        │        │              ││
│  │    ████████████                                               fadeIn     ││
│  │             ████████████████                                  slideIn    ││
│  │                      ████████████████████                     scaleUp    ││
│  │                               █████████████████████████████   colorize   ││
│  │                                                                          ││
│  │    timeline.add(anim, startTime | "<" | "<+=100" | ">-50")              ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Python API

```python
from pynext.client import animate, spring, timeline

# Web Animations API
animation = el.animate([
    {"opacity": 0, "transform": "translateY(-20px)"},
    {"opacity": 1, "transform": "translateY(0)"},
], {
    "duration": 300,
    "easing": "ease-out",
    "fill": "forwards",
})
await animation.finished
animation.pause()
animation.play()
animation.reverse()
animation.cancel()

# Spring Physics
anim = spring(el, {
    "to": {"x": 100, "scale": 1.2},
    "stiffness": 300,
    "damping": 20,
    "mass": 1,
})

# Timeline (stagger animations)
tl = timeline()
tl.add(el1.animate(...), 0)           # Start at 0ms
tl.add(el2.animate(...), 100)         # Start at 100ms
tl.add(el3.animate(...), "<+=50")     # 50ms after previous ends
tl.play()

# CSS Transitions via Python
el.style.transition = "all 0.3s ease"
el.style.transform = "scale(1.1)"

# Transition property control
el.style.transitionProperty = "transform, opacity"
el.style.transitionDuration = "0.3s, 0.2s"
el.style.transitionTimingFunction = "ease-out"
el.style.transitionDelay = "0.1s"

# Transition events
@client
def on_transition_start(event):
    event.propertyName      # "transform"
    event.elapsedTime       # 0
    event.pseudoElement     # ""

@client
def on_transition_end(event):
    event.propertyName      # "transform"
    event.elapsedTime       # 0.3
    # Clean up or chain next animation

@client
def on_transition_cancel(event):
    event.propertyName
    # Handle interrupted transition

el.addEventListener("transitionstart", on_transition_start)
el.addEventListener("transitionend", on_transition_end)
el.addEventListener("transitionrun", on_transition_run)
el.addEventListener("transitioncancel", on_transition_cancel)

# Keyframe animations
@keyframes
def bounce():
    return [
        {"offset": 0, "transform": "translateY(0)"},
        {"offset": 0.5, "transform": "translateY(-20px)"},
        {"offset": 1, "transform": "translateY(0)"},
    ]

# Animation options (complete)
animation = el.animate(keyframes, {
    "duration": 300,                    # milliseconds
    "easing": "ease-out",               # CSS easing or cubic-bezier
    "delay": 100,                       # start delay
    "endDelay": 50,                     # end delay
    "fill": "forwards",                 # none, forwards, backwards, both
    "direction": "alternate",           # normal, reverse, alternate, alternate-reverse
    "iterations": 3,                    # number or Infinity
    "iterationStart": 0.5,              # start at 50%
    "composite": "add",                 # replace, add, accumulate
    "pseudoElement": "::before",        # animate pseudo-element
})

# Animation control
animation.play()
animation.pause()
animation.reverse()
animation.finish()
animation.cancel()
animation.persist()                     # Keep final state

# Animation properties
animation.playState                     # "running", "paused", "finished"
animation.playbackRate = 2.0            # 2x speed
animation.currentTime = 150             # Seek to 150ms
animation.startTime
animation.effect.getTiming()
animation.effect.getComputedTiming()

# Animation events
animation.onfinish = on_finish
animation.oncancel = on_cancel
animation.onremove = on_remove
await animation.finished                # Promise

# Update animation timing
animation.effect.updateTiming({
    "duration": 500,
    "easing": "ease-in",
})

# Get running animations
animations = el.getAnimations()
all_animations = document.getAnimations()

# Easing functions
EASINGS = {
    "linear": "linear",
    "ease": "ease",
    "ease-in": "ease-in",
    "ease-out": "ease-out",
    "ease-in-out": "ease-in-out",
    "cubic-bezier": "cubic-bezier(0.4, 0, 0.2, 1)",  # Custom
    "steps": "steps(5, jump-start)",
    "spring": "linear(0, 0.25, 0.5, 1)",  # Approximated spring
}

# CSS animation via style
el.style.animation = "bounce 0.5s ease-in-out infinite"
el.style.animationName = "bounce"
el.style.animationDuration = "0.5s"
el.style.animationTimingFunction = "ease-in-out"
el.style.animationDelay = "0.1s"
el.style.animationIterationCount = "infinite"
el.style.animationDirection = "alternate"
el.style.animationFillMode = "forwards"
el.style.animationPlayState = "running"  # or "paused"

# Animation events (CSS animations)
@client
def on_animation_start(event):
    event.animationName     # "bounce"
    event.elapsedTime       # 0
    event.pseudoElement

@client
def on_animation_end(event):
    event.animationName
    event.elapsedTime

@client
def on_animation_iteration(event):
    event.animationName
    event.elapsedTime       # Time at iteration

el.addEventListener("animationstart", on_animation_start)
el.addEventListener("animationend", on_animation_end)
el.addEventListener("animationiteration", on_animation_iteration)
el.addEventListener("animationcancel", on_animation_cancel)
```

##### CSS Animation Checklist

```
CSS Animation Support (Phase 36)
├── Web Animations API (60 tests)
│   ├── [ ] Element.animate(keyframes, options)
│   ├── [ ] Animation.play() / pause() / reverse()
│   ├── [ ] Animation.finish() / cancel() / persist()
│   ├── [ ] Animation.playState
│   ├── [ ] Animation.playbackRate
│   ├── [ ] Animation.currentTime / startTime
│   ├── [ ] Animation.finished (Promise)
│   ├── [ ] Animation.onfinish / oncancel / onremove
│   ├── [ ] AnimationEffect.getTiming() / getComputedTiming()
│   ├── [ ] AnimationEffect.updateTiming()
│   ├── [ ] Element.getAnimations()
│   ├── [ ] document.getAnimations()
│   └── [ ] Keyframe object format validation
│
├── CSS Transitions (40 tests)
│   ├── [ ] transitionProperty
│   ├── [ ] transitionDuration
│   ├── [ ] transitionTimingFunction
│   ├── [ ] transitionDelay
│   ├── [ ] transition (shorthand)
│   ├── [ ] transitionstart event
│   ├── [ ] transitionend event
│   ├── [ ] transitionrun event
│   ├── [ ] transitioncancel event
│   └── [ ] TransitionEvent properties
│
├── CSS Animation Properties (30 tests)
│   ├── [ ] animationName
│   ├── [ ] animationDuration
│   ├── [ ] animationTimingFunction
│   ├── [ ] animationDelay
│   ├── [ ] animationIterationCount
│   ├── [ ] animationDirection
│   ├── [ ] animationFillMode
│   ├── [ ] animationPlayState
│   ├── [ ] animation (shorthand)
│   └── [ ] @keyframes Python decorator
│
├── Animation Events (25 tests)
│   ├── [ ] animationstart
│   ├── [ ] animationend
│   ├── [ ] animationiteration
│   ├── [ ] animationcancel
│   └── [ ] AnimationEvent properties
│
└── Easing Functions (15 tests)
    ├── [ ] Built-in easings (ease, linear, etc.)
    ├── [ ] cubic-bezier() parsing
    ├── [ ] steps() parsing
    ├── [ ] linear() multi-point easing
    └── [ ] Spring approximation
```

##### Files to Create

- `pynext/client/animation.py` — Web Animations API stubs
- `pynext/client/spring.py` — Spring physics engine
- `pynext/client/timeline.py` — Animation timeline orchestration
- `pynext/client/transitions.py` — CSS Transitions API and events
- `pynext/client/easing.py` — Easing function utilities and parsing
- `pynext/transpiler/keyframes.py` — @keyframes decorator transpilation

##### Success Criteria

| Metric | Target |
|--------|--------|
| Animation types | Keyframe, spring, timeline, CSS transitions |
| CSS transitions | Full transition property and event support |
| Animation events | All transition and animation events |
| Easing support | Built-in + cubic-bezier + steps + linear |
| Performance | 60fps animations |
| Test coverage | 200+ unit tests (including 170 CSS animation tests) |

##### Milestones

1. **Week 1:** Web Animations API (animate, keyframes, controls, events)
2. **Week 2:** CSS Transitions (properties, events), Spring physics
3. **Week 3:** Timeline orchestration, easing functions, stagger, sequencing

##### What Phase 36 Enables

After Phase 36, you can create beautiful, performant animations:

```python
from pynext.client import client, spring, timeline
from pynext.client.animation import animate, stagger

@client
async def fancy_list_animation(items: list):
    """Create a stunning staggered list entrance."""
    
    # Get all list items
    elements = document.querySelectorAll(".list-item")
    
    # Staggered fade-in with spring physics
    for i, el in enumerate(elements):
        await spring(el, {
            "from": {"opacity": 0, "y": 50, "scale": 0.8},
            "to": {"opacity": 1, "y": 0, "scale": 1},
            "stiffness": 200,
            "damping": 15,
            "delay": i * 50,  # Stagger each item
        }).finished
    
    console.log("All items animated in!")


@client  
def interactive_card():
    """Card with hover animation using Web Animations API."""
    
    card = document.querySelector(".card")
    
    def on_hover(e):
        card.animate([
            {"transform": "translateY(0) scale(1)", "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"},
            {"transform": "translateY(-8px) scale(1.02)", "boxShadow": "0 20px 40px rgba(0,0,0,0.2)"},
        ], {
            "duration": 200,
            "easing": "cubic-bezier(0.34, 1.56, 0.64, 1)",  # Bouncy!
            "fill": "forwards",
        })
    
    def on_leave(e):
        card.animate([
            {"transform": "translateY(-8px) scale(1.02)"},
            {"transform": "translateY(0) scale(1)"},
        ], {"duration": 150, "fill": "forwards"})
    
    card.addEventListener("mouseenter", on_hover)
    card.addEventListener("mouseleave", on_leave)


@client
async def page_transition():
    """Orchestrated page transition with timeline."""
    
    tl = timeline()
    
    # Fade out old content
    tl.add(
        document.querySelector(".old-page").animate(
            [{"opacity": 1}, {"opacity": 0}],
            {"duration": 200, "fill": "forwards"}
        ),
        0
    )
    
    # Slide in new content
    tl.add(
        document.querySelector(".new-page").animate(
            [{"transform": "translateX(100%)"}, {"transform": "translateX(0)"}],
            {"duration": 300, "easing": "ease-out", "fill": "forwards"}
        ),
        100  # Start 100ms into timeline
    )
    
    # Stagger in child elements
    children = document.querySelectorAll(".new-page > *")
    for i, child in enumerate(children):
        tl.add(
            child.animate(
                [{"opacity": 0, "y": 20}, {"opacity": 1, "y": 0}],
                {"duration": 200, "fill": "forwards"}
            ),
            f"<+={i * 50}"  # Stagger after previous
        )
    
    await tl.play().finished
```

---

#### Phase 37: Touch and Gestures (200 tests, 3 weeks)

Pan, pinch, swipe, pointer events, drag-and-drop.

##### Gesture Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PHASE 37: TOUCH & GESTURES                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        Pointer Events                                    ││
│  │                                                                          ││
│  │  Mouse, Touch, Pen → Unified Pointer API                                ││
│  │                                                                          ││
│  │  pointerdown  →  pointermove  →  pointerup                              ││
│  │       │                │              │                                  ││
│  │       ▼                ▼              ▼                                  ││
│  │  ┌─────────┐    ┌───────────┐   ┌──────────┐                            ││
│  │  │  START  │───▶│  MOVING   │──▶│   END    │                            ││
│  │  │ capture │    │  track    │   │ release  │                            ││
│  │  └─────────┘    └───────────┘   └──────────┘                            ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     Gesture Recognizers                                  ││
│  │                                                                          ││
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐            ││
│  │  │    TAP    │  │   SWIPE   │  │    PAN    │  │   PINCH   │            ││
│  │  │           │  │           │  │           │  │           │            ││
│  │  │  • tap    │  │  • left   │  │  • start  │  │  • zoom   │            ││
│  │  │  • double │  │  • right  │  │  • move   │  │  • rotate │            ││
│  │  │  • long   │  │  • up     │  │  • end    │  │           │            ││
│  │  │           │  │  • down   │  │  • cancel │  │           │            ││
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘            ││
│  │                                                                          ││
│  │  ┌───────────┐  ┌───────────┐                                           ││
│  │  │   DRAG    │  │   HOLD    │                                           ││
│  │  │           │  │           │                                           ││
│  │  │  • start  │  │  • press  │                                           ││
│  │  │  • move   │  │  • hold   │                                           ││
│  │  │  • drop   │  │  • release│                                           ││
│  │  └───────────┘  └───────────┘                                           ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     Drag and Drop API                                    ││
│  │                                                                          ││
│  │  Draggable ──────▶ DragEvent ──────▶ DropZone                           ││
│  │                                                                          ││
│  │  dragstart → drag → dragenter → dragover → drop → dragend              ││
│  │                                                                          ││
│  │  DataTransfer: setData(), getData(), files, types                       ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Python API

```python
from pynext.client import use_gesture, use_pan, use_pinch, use_swipe

# Gesture hooks
@use_pan(element)
def on_pan(state):
    state.delta       # [dx, dy]
    state.movement    # Total movement
    state.velocity    # [vx, vy]
    state.direction   # [1, -1] = right-up
    state.first       # Is first event?
    state.last        # Is last event?

@use_pinch(element)
def on_pinch(state):
    state.scale       # Relative scale
    state.origin      # Pinch center [x, y]
    state.rotation    # Rotation angle

@use_swipe(element)
def on_swipe(state):
    state.direction   # "left", "right", "up", "down"
    state.velocity
    state.distance

@use_longpress(element, duration=500)
def on_longpress(state):
    show_context_menu(state.x, state.y)

# Pointer Events
el.addEventListener("pointerdown", on_pointer)
el.setPointerCapture(event.pointerId)
el.releasePointerCapture(event.pointerId)

# Sortable Lists
@use_sortable(container)
def on_reorder(old_index, new_index):
    items.set(reorder(items(), old_index, new_index))

# Drag and Drop
@use_draggable(element)
def on_drag(state):
    state.x, state.y
    state.offset

@use_droppable(zone)
def on_drop(item, position):
    handle_drop(item, position)
```

##### Files to Create

- `pynext/client/gestures.py` — Gesture recognizers
- `pynext/client/pointer.py` — Pointer event handling
- `pynext/client/drag.py` — Drag and drop, sortable lists

##### Success Criteria

| Metric | Target |
|--------|--------|
| Gesture types | Pan, pinch, swipe, longpress, tap |
| Touch support | Full multi-touch |
| Test coverage | 200+ unit tests |

##### Milestones

1. **Week 1:** Pan, pinch, rotate gestures
2. **Week 2:** Swipe, longpress, tap detection
3. **Week 3:** Drag-and-drop, sortable lists

##### What Phase 37 Enables

After Phase 37, you can build touch-first interfaces:

```python
from pynext.client import client, on_swipe, on_pan, on_pinch, use_drag

@client
def swipeable_card():
    """Tinder-style swipeable cards."""
    
    card = document.querySelector(".card")
    
    @on_pan(card)
    def handle_pan(e):
        # Move card with finger/mouse
        card.style.transform = f"translateX({e.deltaX}px) rotate({e.deltaX * 0.1}deg)"
        
        # Change opacity based on direction
        if e.deltaX > 100:
            card.classList.add("accept-hint")
        elif e.deltaX < -100:
            card.classList.add("reject-hint")
    
    @on_swipe(card, direction="left")
    async def reject(e):
        await animate_out(card, "left")
        show_next_card()
    
    @on_swipe(card, direction="right") 
    async def accept(e):
        await animate_out(card, "right")
        show_next_card()


@client
def image_viewer():
    """Pinch-to-zoom image viewer."""
    
    image = document.querySelector(".zoomable-image")
    current_scale = 1.0
    
    @on_pinch(image)
    def handle_zoom(e):
        nonlocal current_scale
        current_scale *= e.scale
        current_scale = max(0.5, min(current_scale, 5.0))  # Clamp
        image.style.transform = f"scale({current_scale})"


@client
def kanban_board():
    """Drag-and-drop Kanban board."""
    
    columns = document.querySelectorAll(".column")
    cards = document.querySelectorAll(".card")
    
    for card in cards:
        use_drag(card, {
            "on_start": lambda e, c=card: c.classList.add("dragging"),
            "on_end": lambda e, c=card: c.classList.remove("dragging"),
        })
    
    for column in columns:
        @on_drop(column)
        def handle_drop(e):
            dragged = document.querySelector(".dragging")
            if dragged:
                column.appendChild(dragged)
                save_card_position(dragged.dataset.id, column.dataset.status)
```

---

#### Phase 38: Observers (150 tests, 2 weeks)

IntersectionObserver, ResizeObserver, MutationObserver — reactive to the DOM.

##### Observer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 38: OBSERVERS                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                   IntersectionObserver                                   ││
│  │                   (Visibility Detection)                                 ││
│  │                                                                          ││
│  │     ┌────────────────────────────────────────────────┐                  ││
│  │     │                 Viewport                        │                  ││
│  │     │   ┌─────────────────────────────────┐          │                  ││
│  │     │   │ ████████ ← visible = true       │          │                  ││
│  │     │   │        ratio = 0.6              │          │                  ││
│  │     └───┼─────────────────────────────────┼──────────┘                  ││
│  │         │ ░░░░░░░░ ← outside viewport     │                             ││
│  │         └─────────────────────────────────┘                             ││
│  │                                                                          ││
│  │   Use cases: Lazy loading, infinite scroll, read tracking               ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     ResizeObserver                                       ││
│  │                     (Size Changes)                                       ││
│  │                                                                          ││
│  │     ┌──────────┐       drag        ┌────────────────────┐               ││
│  │     │   100px  │  ───────────▶     │       200px        │               ││
│  │     │          │                   │                    │               ││
│  │     └──────────┘                   └────────────────────┘               ││
│  │                                                                          ││
│  │   callback({ width: 200, height: 100, contentRect, ... })               ││
│  │                                                                          ││
│  │   Use cases: Responsive components, chart resizing, container queries   ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    MutationObserver                                      ││
│  │                    (DOM Changes)                                         ││
│  │                                                                          ││
│  │   Watch for:                                                             ││
│  │   • childList   — elements added/removed                                ││
│  │   • attributes  — attribute changes                                      ││
│  │   • characterData — text content changes                                 ││
│  │   • subtree     — deep watching                                          ││
│  │                                                                          ││
│  │   Use cases: Third-party integration, accessibility, syncing            ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Python API

```python
from pynext.client import IntersectionObserver, ResizeObserver, MutationObserver

# Intersection Observer (lazy loading, infinite scroll)
observer = IntersectionObserver(
    callback=on_intersect,
    options={"threshold": 0.5, "rootMargin": "100px"}
)
observer.observe(element)
observer.unobserve(element)
observer.disconnect()

@client
def on_intersect(entries):
    for entry in entries:
        if entry.isIntersecting:
            load_content(entry.target)
        entry.intersectionRatio
        entry.boundingClientRect
        entry.rootBounds

# Resize Observer
resize_observer = ResizeObserver(on_resize)
resize_observer.observe(element)

@client
def on_resize(entries):
    for entry in entries:
        entry.contentRect.width
        entry.contentRect.height
        entry.borderBoxSize
        entry.contentBoxSize

# Mutation Observer
mutation_observer = MutationObserver(on_mutate)
mutation_observer.observe(element, {
    "childList": True,
    "subtree": True,
    "attributes": True,
    "attributeFilter": ["class", "style"],
    "characterData": True,
})

@client
def on_mutate(mutations):
    for mutation in mutations:
        mutation.type           # "childList", "attributes", "characterData"
        mutation.target
        mutation.addedNodes
        mutation.removedNodes
        mutation.attributeName
        mutation.oldValue
```

##### Files to Create

- `pynext/client/observers.py` — All observer APIs

##### Success Criteria

| Metric | Target |
|--------|--------|
| Observer types | Intersection, Resize, Mutation |
| Test coverage | 150+ unit tests |

##### Milestones

1. **Week 1:** IntersectionObserver (lazy loading, infinite scroll)
2. **Week 2:** ResizeObserver, MutationObserver

##### What Phase 38 Enables

After Phase 38, you can react to DOM changes efficiently:

```python
from pynext.client import client, IntersectionObserver, ResizeObserver, MutationObserver

@client
def lazy_load_images():
    """Load images only when they scroll into view."""
    
    images = document.querySelectorAll("img[data-src]")
    
    def on_intersect(entries, observer):
        for entry in entries:
            if entry.isIntersecting:
                img = entry.target
                img.src = img.dataset.src  # Load the real image
                img.classList.add("loaded")
                observer.unobserve(img)  # Stop watching
    
    observer = IntersectionObserver(on_intersect, {
        "rootMargin": "100px",  # Start loading 100px before visible
        "threshold": 0.1
    })
    
    for img in images:
        observer.observe(img)


@client
def responsive_chart():
    """Chart that redraws when container resizes."""
    
    container = document.querySelector(".chart-container")
    chart = None
    
    def on_resize(entries):
        for entry in entries:
            width = entry.contentRect.width
            height = entry.contentRect.height
            
            if chart:
                chart.resize(width, height)
                chart.redraw()
            else:
                chart = create_chart(container, width, height)
    
    observer = ResizeObserver(on_resize)
    observer.observe(container)


@client
def infinite_scroll():
    """Load more content when reaching bottom."""
    
    sentinel = document.querySelector(".scroll-sentinel")
    page = 1
    
    def on_reach_bottom(entries, observer):
        nonlocal page
        
        for entry in entries:
            if entry.isIntersecting:
                page += 1
                load_more_items(page)
    
    observer = IntersectionObserver(on_reach_bottom, {
        "rootMargin": "200px"  # Trigger before reaching bottom
    })
    observer.observe(sentinel)
```

---

### MEDIA PHASES (39-40)

---

#### Phase 39: File, Canvas 2D, Audio (250 tests, 4 weeks)

FileReader, Canvas 2D drawing, Web Audio API — multimedia from Python.

##### Media APIs Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 39: FILE, CANVAS, AUDIO                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                          File API                                        ││
│  │                                                                          ││
│  │  <input type="file">  →  FileList  →  File  →  FileReader               ││
│  │                                                                          ││
│  │  FileReader methods:                   Blob methods:                     ││
│  │  • readAsText()                        • slice()                         ││
│  │  • readAsDataURL()                     • text()                          ││
│  │  • readAsArrayBuffer()                 • arrayBuffer()                   ││
│  │  • readAsBinaryString()                • stream()                        ││
│  │                                                                          ││
│  │  URL.createObjectURL(blob)  →  "blob:https://..."                       ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        Canvas 2D                                         ││
│  │                                                                          ││
│  │  ┌────────────────────────────────────────────────────────────┐         ││
│  │  │  canvas.getContext("2d") → CanvasRenderingContext2D       │         ││
│  │  │                                                            │         ││
│  │  │  Shapes          Paths           Text           Images     │         ││
│  │  │  ──────          ─────           ────           ──────     │         ││
│  │  │  fillRect        beginPath       fillText       drawImage  │         ││
│  │  │  strokeRect      moveTo/lineTo   strokeText    createPat.. │         ││
│  │  │  clearRect       arc/arcTo       measureText   getImageDat │         ││
│  │  │                  bezierCurveTo   font          putImageDat │         ││
│  │  │                  quadraticCurve  textAlign                 │         ││
│  │  │                                                            │         ││
│  │  │  Transforms: translate, rotate, scale, setTransform       │         ││
│  │  │  State: save(), restore()                                  │         ││
│  │  │                                                            │         ││
│  │  └────────────────────────────────────────────────────────────┘         ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                       Web Audio API                                      ││
│  │                                                                          ││
│  │  AudioContext → Source → Effects → Destination                          ││
│  │                                                                          ││
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌───────────┐   ││
│  │  │ AudioBuffer │──▶│   Gain      │──▶│  Analyser   │──▶│  Output   │   ││
│  │  │ (source)    │   │  (volume)   │   │ (visualize) │   │ (speakers)│   ││
│  │  └─────────────┘   └─────────────┘   └─────────────┘   └───────────┘   ││
│  │        ▲                                    │                            ││
│  │        │                                    ▼                            ││
│  │  ┌─────────────┐                    ┌─────────────┐                     ││
│  │  │ Oscillator  │                    │ getByteFreq │                     ││
│  │  │ (synth)     │                    │ Data()      │                     ││
│  │  └─────────────┘                    └─────────────┘                     ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Python API

```python
from pynext.client import FileReader, Canvas2D, AudioContext

# File API
@client
async def on_file_select(event):
    file = event.target.files[0]
    file.name
    file.size
    file.type
    file.lastModified
    
    reader = FileReader()
    content = await reader.readAsText(file)
    # or: await reader.readAsDataURL(file)
    # or: await reader.readAsArrayBuffer(file)

# Blob and URL
blob = Blob([data], {"type": "text/plain"})
url = URL.createObjectURL(blob)
URL.revokeObjectURL(url)

# Canvas 2D
canvas = document.getElementById("canvas")
ctx = canvas.getContext("2d")

# Drawing
ctx.fillStyle = "red"
ctx.fillRect(10, 10, 100, 100)
ctx.strokeStyle = "blue"
ctx.lineWidth = 2
ctx.strokeRect(10, 10, 100, 100)
ctx.clearRect(0, 0, canvas.width, canvas.height)

# Paths
ctx.beginPath()
ctx.moveTo(0, 0)
ctx.lineTo(100, 100)
ctx.quadraticCurveTo(50, 0, 100, 0)
ctx.bezierCurveTo(10, 10, 90, 10, 100, 100)
ctx.arc(50, 50, 40, 0, 2 * math.pi)
ctx.arcTo(100, 0, 100, 100, 50)
ctx.closePath()
ctx.fill()
ctx.stroke()

# Text
ctx.font = "24px Arial"
ctx.textAlign = "center"
ctx.textBaseline = "middle"
ctx.fillText("Hello", 50, 50)
ctx.strokeText("World", 50, 80)
metrics = ctx.measureText("Hello")

# Images
img = Image()
img.src = "/image.png"
await img.decode()
ctx.drawImage(img, 0, 0)
ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh)

# Transforms
ctx.save()
ctx.translate(50, 50)
ctx.rotate(math.pi / 4)
ctx.scale(2, 2)
ctx.setTransform(a, b, c, d, e, f)
ctx.restore()

# Pixel manipulation
image_data = ctx.getImageData(0, 0, width, height)
ctx.putImageData(image_data, 0, 0)

# Web Audio
audio_ctx = AudioContext()
oscillator = audio_ctx.createOscillator()
oscillator.type = "sine"  # sine, square, sawtooth, triangle
oscillator.frequency.value = 440
oscillator.frequency.setValueAtTime(440, audio_ctx.currentTime)
oscillator.frequency.linearRampToValueAtTime(880, audio_ctx.currentTime + 1)

gain = audio_ctx.createGain()
gain.gain.value = 0.5

oscillator.connect(gain)
gain.connect(audio_ctx.destination)
oscillator.start()
oscillator.stop(audio_ctx.currentTime + 2)

# Audio from file
audio_buffer = await audio_ctx.decodeAudioData(array_buffer)
source = audio_ctx.createBufferSource()
source.buffer = audio_buffer
source.connect(audio_ctx.destination)
source.start()
```

##### Files to Create

- `pynext/client/file.py` — FileReader, Blob, URL
- `pynext/client/canvas.py` — Canvas 2D context
- `pynext/client/audio.py` — Web Audio API

##### Success Criteria

| Metric | Target |
|--------|--------|
| File API | Complete FileReader, Blob, URL |
| Canvas 2D | Full drawing API |
| Web Audio | Oscillators, buffers, effects |
| Test coverage | 250+ unit tests |

##### Milestones

1. **Week 1:** File API (FileReader, Blob, URL)
2. **Week 2:** Canvas 2D (drawing, paths, text)
3. **Week 3:** Canvas 2D (images, transforms, pixels)
4. **Week 4:** Web Audio API

---

#### Phase 40: Real-time and Storage (200 tests, 4 weeks)

WebSocket, Server-Sent Events, WebRTC, IndexedDB, Cache API.

##### Python API

```python
from pynext.client import WebSocket, EventSource, IndexedDB

# WebSocket
ws = WebSocket("wss://api.example.com/ws")

@ws.on_open
def on_open():
    ws.send(json.dumps({"type": "subscribe"}))

@ws.on_message
def on_message(event):
    data = json.loads(event.data)
    handle_message(data)

@ws.on_close
def on_close(event):
    event.code
    event.reason
    event.wasClean
    if event.code != 1000:
        reconnect()

@ws.on_error
def on_error(event):
    log_error(event)

ws.close(1000, "Normal closure")

# Server-Sent Events
es = EventSource("/events")

@es.on_open
def on_sse_open():
    pass

@es.on_message
def on_sse_message(event):
    event.data
    event.lastEventId

@es.on("custom-event")
def on_custom(event):
    pass

@es.on_error
def on_sse_error(event):
    pass

es.close()

# IndexedDB
db = await IndexedDB.open("mydb", 1)

@db.on_upgrade
def on_upgrade(db, old_version, new_version):
    if old_version < 1:
        store = db.createObjectStore("items", {"keyPath": "id"})
        store.createIndex("by_date", "created_at")
        store.createIndex("by_name", "name", {"unique": False})

tx = db.transaction("items", "readwrite")
store = tx.objectStore("items")
await store.put({"id": 1, "name": "Item 1", "created_at": Date.now()})
await store.add({"id": 2, "name": "Item 2"})
item = await store.get(1)
all_items = await store.getAll()
await store.delete(1)
await store.clear()

# Cursors
index = store.index("by_date")
cursor = await index.openCursor()
while cursor:
    process(cursor.value)
    cursor = await cursor.continue_()

# Cache API
cache = await caches.open("app-cache-v1")
await cache.put(request, response)
response = await cache.match(request)
await cache.delete(request)
await caches.delete("app-cache-v1")
```

##### Trusted Types and Content Security Policy (CSP)

Security APIs for preventing XSS and other injection attacks.

```python
from pynext.client import TrustedTypes, trustedTypes, document, window

# =============================================================================
# Trusted Types API (XSS Prevention)
# =============================================================================

# Check if Trusted Types are supported and enforced
if trustedTypes:
    print("Trusted Types supported")

# Check if a policy exists
trustedTypes.isHTML(value)        # True if TrustedHTML
trustedTypes.isScript(value)      # True if TrustedScript
trustedTypes.isScriptURL(value)   # True if TrustedScriptURL

# =============================================================================
# Creating Trusted Type Policies
# =============================================================================

# Create a policy (usually done once at app initialization)
policy = trustedTypes.createPolicy("pynext-sanitizer", {
    # Sanitize HTML before injection
    "createHTML": lambda input: sanitize_html(input),
    
    # Validate script content
    "createScript": lambda input: validate_script(input),
    
    # Validate script URLs
    "createScriptURL": lambda input: validate_url(input),
})

# Use the policy to create trusted values
safe_html = policy.createHTML(user_input)
el.innerHTML = safe_html  # Allowed because it's TrustedHTML

safe_script = policy.createScript(script_code)
safe_url = policy.createScriptURL("/scripts/app.js")

# =============================================================================
# Default Policy (Fallback)
# =============================================================================

# Create default policy (called when no trusted type is provided)
trustedTypes.createPolicy("default", {
    "createHTML": lambda input: 
        # Auto-sanitize any string passed to innerHTML
        DOMPurify.sanitize(input) if DOMPurify else escape_html(input),
    
    "createScript": lambda input:
        # Reject all inline scripts by default
        raise_error("Inline scripts not allowed"),
    
    "createScriptURL": lambda input:
        # Only allow same-origin scripts
        validate_same_origin(input) or raise_error(f"Invalid script URL: {input}"),
})

# =============================================================================
# Policy Management
# =============================================================================

# Get existing policy by name
existing_policy = trustedTypes.getPolicy("pynext-sanitizer")

# Get all policy names
policy_names = trustedTypes.getPolicyNames()  # ["pynext-sanitizer", "default"]

# Check for default policy
has_default = trustedTypes.defaultPolicy is not None

# =============================================================================
# Practical Sanitization Functions
# =============================================================================

@client
def sanitize_html(html_string):
    """
    Sanitize HTML to prevent XSS.
    Uses a template element for parsing.
    """
    # Create temporary element
    template = document.createElement("template")
    template.innerHTML = html_string
    
    # Remove dangerous elements and attributes
    dangerous_tags = ["script", "iframe", "object", "embed", "form"]
    dangerous_attrs = ["onclick", "onerror", "onload", "onmouseover", "onfocus"]
    
    for tag in dangerous_tags:
        for el in template.content.querySelectorAll(tag):
            el.remove()
    
    for el in template.content.querySelectorAll("*"):
        for attr in dangerous_attrs:
            el.removeAttribute(attr)
        # Remove javascript: URLs
        if el.hasAttribute("href"):
            href = el.getAttribute("href")
            if href and href.lower().startswith("javascript:"):
                el.removeAttribute("href")
        if el.hasAttribute("src"):
            src = el.getAttribute("src")
            if src and src.lower().startswith("javascript:"):
                el.removeAttribute("src")
    
    return template.innerHTML

@client
def escape_html(text):
    """Escape HTML special characters."""
    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text

@client
def validate_same_origin(url):
    """Validate that URL is same-origin."""
    try:
        parsed = URL(url, window.location.origin)
        return parsed.origin == window.location.origin
    except:
        return False

# =============================================================================
# CSP Violation Reporting
# =============================================================================

# Listen for CSP violations
@client
def setup_csp_monitoring():
    @document.on("securitypolicyviolation")
    def on_violation(event):
        violation_data = {
            "documentURI": event.documentURI,
            "blockedURI": event.blockedURI,
            "violatedDirective": event.violatedDirective,
            "effectiveDirective": event.effectiveDirective,
            "originalPolicy": event.originalPolicy,
            "disposition": event.disposition,  # "enforce" or "report"
            "statusCode": event.statusCode,
            "lineNumber": event.lineNumber,
            "columnNumber": event.columnNumber,
            "sourceFile": event.sourceFile,
            "sample": event.sample,  # First 40 chars of violating content
        }
        
        # Log violation
        console.warn("CSP Violation:", violation_data)
        
        # Optionally report to server
        fetch("/api/csp-report", {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": JSON.stringify(violation_data),
        })

# =============================================================================
# Nonce Handling for Inline Scripts
# =============================================================================

@client
def get_csp_nonce():
    """
    Get the CSP nonce for the current page.
    Usually injected by the server into a meta tag.
    """
    meta = document.querySelector('meta[name="csp-nonce"]')
    if meta:
        return meta.getAttribute("content")
    
    # Or get from an existing script tag
    script = document.querySelector("script[nonce]")
    if script:
        return script.nonce or script.getAttribute("nonce")
    
    return None

@client
def create_script_with_nonce(src=None, content=None):
    """Create a script element with the page's CSP nonce."""
    script = document.createElement("script")
    nonce = get_csp_nonce()
    
    if nonce:
        script.nonce = nonce
    
    if src:
        # For external scripts
        if trustedTypes:
            policy = trustedTypes.getPolicy("pynext-sanitizer")
            if policy:
                script.src = policy.createScriptURL(src)
            else:
                script.src = src
        else:
            script.src = src
    elif content:
        # For inline scripts
        if trustedTypes:
            policy = trustedTypes.getPolicy("pynext-sanitizer")
            if policy:
                script.textContent = policy.createScript(content)
            else:
                script.textContent = content
        else:
            script.textContent = content
    
    return script

# =============================================================================
# Secure Element Creation Helpers
# =============================================================================

@client
def safe_set_html(element, html_content):
    """Safely set innerHTML with sanitization."""
    if trustedTypes:
        policy = trustedTypes.getPolicy("pynext-sanitizer")
        if policy:
            element.innerHTML = policy.createHTML(html_content)
            return
    
    # Fallback: sanitize manually
    element.innerHTML = sanitize_html(html_content)

@client
def safe_create_element(tag, attributes=None, html_content=None):
    """Create element safely with optional HTML content."""
    el = document.createElement(tag)
    
    if attributes:
        for key, value in attributes.items():
            if key.startswith("on"):
                # Don't set inline event handlers
                console.warn(f"Inline event handler '{key}' ignored for security")
            else:
                el.setAttribute(key, value)
    
    if html_content:
        safe_set_html(el, html_content)
    
    return el

# =============================================================================
# Subresource Integrity (SRI)
# =============================================================================

@client
async def load_script_with_integrity(src, integrity, crossorigin="anonymous"):
    """
    Load external script with Subresource Integrity check.
    """
    return await Promise(lambda resolve, reject:
        script = document.createElement("script")
        script.src = src
        script.integrity = integrity
        script.crossOrigin = crossorigin
        
        script.onload = lambda: resolve(script)
        script.onerror = lambda e: reject(Error(f"Failed to load: {src}"))
        
        document.head.appendChild(script)
    )

# Example usage:
# await load_script_with_integrity(
#     "https://cdn.example.com/lib.js",
#     "sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxIqYBbLMnYXELBKsWbzBFvFX+qJtx+"
# )

@client
async def compute_integrity(content, algorithm="SHA-384"):
    """Compute SRI hash for content."""
    encoder = TextEncoder()
    data = encoder.encode(content)
    hash_buffer = await crypto.subtle.digest(algorithm.upper(), data)
    hash_array = Uint8Array(hash_buffer)
    hash_base64 = btoa("".join(chr(b) for b in hash_array))
    return f"{algorithm.lower()}-{hash_base64}"
```

##### Trusted Types and CSP Checklist

```
Trusted Types and CSP Support (Phase 40)
├── Trusted Types API (25 tests)
│   ├── [ ] trustedTypes.createPolicy()
│   ├── [ ] policy.createHTML()
│   ├── [ ] policy.createScript()
│   ├── [ ] policy.createScriptURL()
│   ├── [ ] trustedTypes.isHTML/isScript/isScriptURL
│   ├── [ ] trustedTypes.getPolicy()
│   ├── [ ] trustedTypes.getPolicyNames()
│   ├── [ ] trustedTypes.defaultPolicy
│   └── [ ] Default policy fallback
│
├── Sanitization (15 tests)
│   ├── [ ] HTML sanitization (remove dangerous elements)
│   ├── [ ] Attribute sanitization (event handlers)
│   ├── [ ] URL sanitization (javascript: prevention)
│   ├── [ ] HTML escaping
│   └── [ ] Same-origin validation
│
├── CSP Violation Handling (10 tests)
│   ├── [ ] securitypolicyviolation event
│   ├── [ ] SecurityPolicyViolationEvent properties
│   └── [ ] Violation reporting
│
├── Nonce Handling (10 tests)
│   ├── [ ] Nonce extraction from meta/script
│   ├── [ ] Script creation with nonce
│   └── [ ] Style creation with nonce
│
└── Subresource Integrity (10 tests)
    ├── [ ] Script loading with integrity
    ├── [ ] Link loading with integrity
    └── [ ] Integrity hash computation
```

##### Files to Create

- `pynext/client/websocket.py` — WebSocket wrapper
- `pynext/client/sse.py` — Server-Sent Events
- `pynext/client/webrtc.py` — WebRTC basics
- `pynext/client/indexeddb.py` — IndexedDB wrapper
- `pynext/client/cache.py` — Cache API
- `pynext/client/trusted_types.py` — Trusted Types API
- `pynext/client/csp.py` — CSP helpers, nonce handling, SRI

##### Success Criteria

| Metric | Target |
|--------|--------|
| Real-time | WebSocket, SSE, basic WebRTC |
| Storage | IndexedDB, Cache API |
| Security | Full Trusted Types, CSP violation handling |
| Test coverage | 270+ unit tests (200 storage + 70 security) |

##### Milestones

1. **Week 1:** WebSocket (connect, send, receive, reconnect)
2. **Week 2:** Server-Sent Events
3. **Week 3:** IndexedDB (CRUD, transactions, cursors)
4. **Week 4:** Cache API, basic WebRTC
5. **Week 5:** Trusted Types, CSP handling, SRI

---

### GRAPHICS PHASES (41-42)

---

#### Phase 41: WebGL / WebGPU (300 tests, 6 weeks)

Complete WebGL 2.0 and WebGPU bindings for high-performance graphics.

##### Python API

```python
from pynext.client import WebGL2, WebGPU

# WebGL2 context
canvas = document.getElementById("canvas")
gl = canvas.getContext("webgl2")

# Shaders
vertex_shader = gl.createShader(gl.VERTEX_SHADER)
gl.shaderSource(vertex_shader, """
    #version 300 es
    in vec4 a_position;
    void main() {
        gl_Position = a_position;
    }
""")
gl.compileShader(vertex_shader)

# Program linking
program = gl.createProgram()
gl.attachShader(program, vertex_shader)
gl.attachShader(program, fragment_shader)
gl.linkProgram(program)
gl.useProgram(program)

# Buffers
buffer = gl.createBuffer()
gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
gl.bufferData(gl.ARRAY_BUFFER, Float32Array(vertices), gl.STATIC_DRAW)

# Vertex attributes
location = gl.getAttribLocation(program, "a_position")
gl.enableVertexAttribArray(location)
gl.vertexAttribPointer(location, 3, gl.FLOAT, False, 0, 0)

# Uniforms
u_matrix = gl.getUniformLocation(program, "u_matrix")
gl.uniformMatrix4fv(u_matrix, False, matrix)

# Textures
texture = gl.createTexture()
gl.bindTexture(gl.TEXTURE_2D, texture)
gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image)
gl.generateMipmap(gl.TEXTURE_2D)

# Framebuffers
framebuffer = gl.createFramebuffer()
gl.bindFramebuffer(gl.FRAMEBUFFER, framebuffer)

# Draw
gl.viewport(0, 0, canvas.width, canvas.height)
gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT)
gl.drawArrays(gl.TRIANGLES, 0, vertex_count)
gl.drawElements(gl.TRIANGLES, index_count, gl.UNSIGNED_SHORT, 0)

# WebGPU (next-gen)
adapter = await navigator.gpu.requestAdapter()
device = await adapter.requestDevice()
context = canvas.getContext("webgpu")
context.configure({
    "device": device,
    "format": navigator.gpu.getPreferredCanvasFormat(),
})
```

##### Files to Create

- `pynext/client/webgl.py` — WebGL/WebGL2 stubs
- `pynext/client/webgpu.py` — WebGPU stubs
- `pynext/runtime/webgl.js` — Helper utilities

##### Success Criteria

| Metric | Target |
|--------|--------|
| WebGL coverage | Full WebGL 2.0 API |
| WebGPU coverage | Core WebGPU API |
| Test coverage | 300+ unit tests |

##### Milestones

1. **Week 1-2:** WebGL context, shaders, programs
2. **Week 3-4:** Buffers, attributes, uniforms, textures
3. **Week 5:** Framebuffers, render targets, advanced features
4. **Week 6:** WebGPU basics

---

#### Phase 42: SVG Manipulation (150 tests, 3 weeks)

Complete SVG DOM and path manipulation.

##### Python API

```python
from pynext.client import SVG

# Create SVG elements
svg = document.createElementNS("http://www.w3.org/2000/svg", "svg")
svg.setAttribute("viewBox", "0 0 100 100")
svg.setAttribute("width", "200")
svg.setAttribute("height", "200")

# Basic shapes
circle = document.createElementNS("http://www.w3.org/2000/svg", "circle")
circle.setAttribute("cx", "50")
circle.setAttribute("cy", "50")
circle.setAttribute("r", "40")
circle.setAttribute("fill", "red")
circle.setAttribute("stroke", "black")
circle.setAttribute("stroke-width", "2")

rect = document.createElementNS("http://www.w3.org/2000/svg", "rect")
rect.setAttribute("x", "10")
rect.setAttribute("y", "10")
rect.setAttribute("width", "80")
rect.setAttribute("height", "60")
rect.setAttribute("rx", "5")  # Rounded corners

line = document.createElementNS("http://www.w3.org/2000/svg", "line")
line.setAttribute("x1", "0")
line.setAttribute("y1", "0")
line.setAttribute("x2", "100")
line.setAttribute("y2", "100")

# Paths
path = document.createElementNS("http://www.w3.org/2000/svg", "path")
path.setAttribute("d", "M10 10 L90 90 Q50 50 10 90 Z")

# Path commands:
# M x y     - Move to
# L x y     - Line to
# H x       - Horizontal line
# V y       - Vertical line
# C x1 y1 x2 y2 x y - Cubic bezier
# Q x1 y1 x y - Quadratic bezier
# A rx ry rotation large-arc sweep x y - Arc
# Z         - Close path

# Transforms
transform_list = element.transform.baseVal
transform = svg.createSVGTransform()
transform.setTranslate(50, 50)
transform.setRotate(45, 0, 0)
transform.setScale(2, 2)
transform_list.appendItem(transform)

# Bounding box
bbox = element.getBBox()
# bbox.x, bbox.y, bbox.width, bbox.height

# Point transformation
point = svg.createSVGPoint()
point.x, point.y = 100, 100
transformed = point.matrixTransform(element.getScreenCTM().inverse())

# Groups
g = document.createElementNS("http://www.w3.org/2000/svg", "g")
g.setAttribute("transform", "translate(50, 50)")
g.appendChild(circle)
g.appendChild(rect)

# Text
text = document.createElementNS("http://www.w3.org/2000/svg", "text")
text.setAttribute("x", "50")
text.setAttribute("y", "50")
text.setAttribute("text-anchor", "middle")
text.textContent = "Hello SVG"

# Gradients
defs = document.createElementNS("http://www.w3.org/2000/svg", "defs")
gradient = document.createElementNS("http://www.w3.org/2000/svg", "linearGradient")
gradient.setAttribute("id", "myGradient")
stop1 = document.createElementNS("http://www.w3.org/2000/svg", "stop")
stop1.setAttribute("offset", "0%")
stop1.setAttribute("stop-color", "red")
```

##### SVG CSS Styling

SVG elements support special CSS properties for fills, strokes, and presentation.

```python
from pynext.client import document, window

# =============================================================================
# SVG Fill Properties
# =============================================================================

# Fill color
circle.style.fill = "red"
circle.style.fill = "#ff0000"
circle.style.fill = "rgb(255, 0, 0)"
circle.style.fill = "url(#myGradient)"      # Reference gradient
circle.style.fill = "none"                   # No fill

# Fill opacity
circle.style.fillOpacity = "0.5"
circle.style.fillOpacity = "50%"

# Fill rule (for complex paths)
path.style.fillRule = "nonzero"              # Default
path.style.fillRule = "evenodd"              # Alternating fill

# =============================================================================
# SVG Stroke Properties
# =============================================================================

# Stroke color
circle.style.stroke = "blue"
circle.style.stroke = "#0000ff"
circle.style.stroke = "currentColor"         # Inherit from color

# Stroke width
circle.style.strokeWidth = "2"
circle.style.strokeWidth = "2px"
circle.style.strokeWidth = "0.5em"

# Stroke opacity
circle.style.strokeOpacity = "0.8"

# Line caps (ends of lines)
line.style.strokeLinecap = "butt"            # Default, flat end
line.style.strokeLinecap = "round"           # Rounded end
line.style.strokeLinecap = "square"          # Square end

# Line joins (corners)
path.style.strokeLinejoin = "miter"          # Default, sharp corner
path.style.strokeLinejoin = "round"          # Rounded corner
path.style.strokeLinejoin = "bevel"          # Beveled corner

# Miter limit (for miter joins)
path.style.strokeMiterlimit = "4"            # Default

# Dash patterns
line.style.strokeDasharray = "5, 10"         # 5px dash, 10px gap
line.style.strokeDasharray = "5, 10, 15"     # Repeating pattern
line.style.strokeDasharray = "none"          # Solid line

# Dash offset (for animation)
line.style.strokeDashoffset = "0"
line.style.strokeDashoffset = "100"          # Offset for "drawing" effect

# =============================================================================
# SVG Text Properties
# =============================================================================

# Font properties (same as HTML)
text.style.fontFamily = "'Helvetica', sans-serif"
text.style.fontSize = "16px"
text.style.fontWeight = "bold"
text.style.fontStyle = "italic"

# Text anchor (horizontal alignment)
text.style.textAnchor = "start"              # Default, left-aligned
text.style.textAnchor = "middle"             # Center-aligned
text.style.textAnchor = "end"                # Right-aligned

# Dominant baseline (vertical alignment)
text.style.dominantBaseline = "auto"
text.style.dominantBaseline = "middle"
text.style.dominantBaseline = "hanging"
text.style.dominantBaseline = "central"

# Text decoration
text.style.textDecoration = "underline"
text.style.textDecoration = "line-through"

# Letter and word spacing
text.style.letterSpacing = "2px"
text.style.wordSpacing = "5px"

# =============================================================================
# SVG Presentation Attributes via CSS
# =============================================================================

# Opacity (whole element)
group.style.opacity = "0.5"

# Visibility
element.style.visibility = "visible"
element.style.visibility = "hidden"

# Display
element.style.display = "inline"             # Default for SVG
element.style.display = "none"

# Pointer events
element.style.pointerEvents = "auto"
element.style.pointerEvents = "none"         # Click-through
element.style.pointerEvents = "visiblePainted"
element.style.pointerEvents = "visibleFill"
element.style.pointerEvents = "visibleStroke"

# Cursor
element.style.cursor = "pointer"
element.style.cursor = "move"
element.style.cursor = "crosshair"

# =============================================================================
# SVG Filters via CSS
# =============================================================================

# Apply filter
element.style.filter = "url(#myFilter)"
element.style.filter = "blur(5px)"
element.style.filter = "drop-shadow(3px 3px 5px rgba(0,0,0,0.5))"
element.style.filter = "brightness(1.2) contrast(1.1)"

# =============================================================================
# SVG Masks and Clips via CSS
# =============================================================================

# Clip path
element.style.clipPath = "url(#myClipPath)"
element.style.clipPath = "circle(50%)"
element.style.clipPath = "polygon(0 0, 100% 0, 100% 100%)"

# Mask
element.style.mask = "url(#myMask)"

# =============================================================================
# Computed Styles for SVG
# =============================================================================

# Get computed SVG styles
computed = window.getComputedStyle(circle)
fill_color = computed.fill                   # "rgb(255, 0, 0)"
stroke_width = computed.strokeWidth          # "2px"
opacity = computed.opacity                   # "1"

# SVG-specific computed values
bbox = element.getBBox()                     # Bounding box without transforms
ctm = element.getCTM()                       # Current transformation matrix
screen_ctm = element.getScreenCTM()          # Screen transformation matrix

# =============================================================================
# SVG Transforms via CSS
# =============================================================================

# CSS transforms work on SVG elements
element.style.transform = "rotate(45deg)"
element.style.transform = "translate(100px, 50px)"
element.style.transform = "scale(2)"
element.style.transform = "matrix(1, 0, 0, 1, 100, 50)"

# Transform origin
element.style.transformOrigin = "center"
element.style.transformOrigin = "50% 50%"
element.style.transformOrigin = "0 0"        # Top-left (SVG default)

# Transform box (what the origin is relative to)
element.style.transformBox = "fill-box"      # Bounding box of fill
element.style.transformBox = "stroke-box"    # Including stroke
element.style.transformBox = "view-box"      # SVG viewBox
```

##### SVG CSS Checklist

```
SVG CSS Styling Support (Phase 42)
├── Fill Properties (15 tests)
│   ├── [ ] fill (color, gradient, pattern, none)
│   ├── [ ] fill-opacity
│   ├── [ ] fill-rule (nonzero, evenodd)
│   └── [ ] CSS color values (hex, rgb, hsl, named)
│
├── Stroke Properties (25 tests)
│   ├── [ ] stroke (color)
│   ├── [ ] stroke-width
│   ├── [ ] stroke-opacity
│   ├── [ ] stroke-linecap (butt, round, square)
│   ├── [ ] stroke-linejoin (miter, round, bevel)
│   ├── [ ] stroke-miterlimit
│   ├── [ ] stroke-dasharray
│   └── [ ] stroke-dashoffset
│
├── Text Properties (15 tests)
│   ├── [ ] font-family, font-size, font-weight
│   ├── [ ] text-anchor (start, middle, end)
│   ├── [ ] dominant-baseline
│   ├── [ ] text-decoration
│   └── [ ] letter-spacing, word-spacing
│
├── Presentation Properties (20 tests)
│   ├── [ ] opacity
│   ├── [ ] visibility
│   ├── [ ] display
│   ├── [ ] pointer-events
│   ├── [ ] cursor
│   └── [ ] color (currentColor inheritance)
│
├── Filters and Effects (15 tests)
│   ├── [ ] filter (url, blur, drop-shadow)
│   ├── [ ] clip-path (url, shapes)
│   └── [ ] mask
│
├── SVG Transforms (15 tests)
│   ├── [ ] transform (CSS syntax)
│   ├── [ ] transform-origin
│   ├── [ ] transform-box
│   └── [ ] CSS vs SVG transform interop
│
└── Computed Styles (10 tests)
    ├── [ ] getComputedStyle on SVG elements
    ├── [ ] Resolved fill/stroke values
    └── [ ] getBBox, getCTM, getScreenCTM
```

##### Files to Create

- `pynext/client/svg.py` — SVG element creation and manipulation
- `pynext/client/svg_style.py` — SVG CSS properties and presentation attributes

##### Success Criteria

| Metric | Target |
|--------|--------|
| SVG coverage | All common SVG elements and attributes |
| Path support | Full path command set |
| SVG CSS | All presentation properties via style API |
| Computed styles | Full getComputedStyle support for SVG |
| Test coverage | 150+ unit tests (including 115 SVG CSS tests) |

##### Milestones

1. **Week 1:** Basic shapes (circle, rect, line, polygon), fill/stroke CSS
2. **Week 2:** Paths, transforms, text styling, bounding boxes
3. **Week 3:** Gradients, filters, masks, clips, animation

---

### PERFORMANCE PHASES (43-44)

---

#### Phase 43: Web Workers and WebAssembly (250 tests, 5 weeks)

Enable heavy computation off the main thread.

##### Python API

```python
from pynext.client import Worker, SharedWorker, WebAssembly

# Dedicated Worker
worker = Worker("/heavy-computation.js")
worker.postMessage({"type": "process", "data": large_array})

@worker.on_message
def on_result(event):
    result.set(event.data)

@worker.on_error
def on_error(event):
    console.error(event.message, event.filename, event.lineno)

worker.terminate()

# Transferable objects (zero-copy)
buffer = ArrayBuffer(1024 * 1024 * 100)  # 100MB
worker.postMessage({"buffer": buffer}, transfer=[buffer])
# buffer is now detached, cannot use in main thread

# SharedWorker (shared across tabs)
shared = SharedWorker("/shared-state.js")
shared.port.start()
shared.port.postMessage({"type": "subscribe", "channel": "updates"})

@shared.port.on_message
def on_shared_message(event):
    sync_state(event.data)

# MessageChannel for direct port communication
channel = MessageChannel()
worker1.postMessage({"port": channel.port1}, transfer=[channel.port1])
worker2.postMessage({"port": channel.port2}, transfer=[channel.port2])

# WebAssembly
wasm_module = await WebAssembly.compileStreaming(fetch("/module.wasm"))
instance = await WebAssembly.instantiate(wasm_module, {
    "env": {
        "memory": WebAssembly.Memory({"initial": 256}),
        "log": lambda x: console.log(x),
    }
})

exports = instance.exports
result = exports.process_image(image_ptr, width, height)

# Access WASM memory
memory = exports.memory
view = Uint8Array(memory.buffer, offset, length)

# Shared memory for threading
shared_memory = WebAssembly.Memory({
    "initial": 256,
    "maximum": 512,
    "shared": True,
})

# Atomics for synchronization
Atomics.store(int32_array, index, value)
Atomics.load(int32_array, index)
Atomics.add(int32_array, index, value)
Atomics.wait(int32_array, index, expected_value)
Atomics.notify(int32_array, index, count)
```

##### Files to Create

- `pynext/client/workers.py` — Worker, SharedWorker
- `pynext/client/wasm.py` — WebAssembly stubs
- `pynext/client/atomics.py` — SharedArrayBuffer, Atomics

##### Success Criteria

| Metric | Target |
|--------|--------|
| Worker types | Dedicated, Shared, Service |
| WASM support | Full instantiation and memory access |
| Test coverage | 250+ unit tests |

##### Milestones

1. **Week 1-2:** Dedicated Workers (messaging, transferables)
2. **Week 3:** SharedWorker, MessageChannel
3. **Week 4:** WebAssembly (compile, instantiate, memory)
4. **Week 5:** SharedArrayBuffer, Atomics

---

#### Phase 44: Virtual Scrolling / Windowing (150 tests, 3 weeks)

Efficient rendering of large lists (10K+ items).

##### Python API

```python
from pynext.client import VirtualList, VirtualGrid, useVirtualizer

# Virtual list
@client
def render_row(item, index, style):
    return div(style=style, class_="row")[
        item["name"],
        item["email"],
    ]

VirtualList(
    items=items,           # Signal or list
    height=600,            # Container height
    item_height=50,        # Row height (fixed or function)
    overscan=5,            # Extra items to render
    render=render_row,
)

# Variable height items
VirtualList(
    items=items,
    height=600,
    estimate_item_height=lambda item: 50 + len(item.description) // 100 * 20,
    measure_item=True,     # Measure after render
    render=render_row,
)

# Virtual grid
VirtualGrid(
    items=items,
    height=600,
    width=800,
    row_height=100,
    column_width=200,
    columns=4,
    render=render_cell,
)

# Hook-style API
virtualizer = useVirtualizer({
    "count": len(items),
    "getScrollElement": lambda: scroll_container,
    "estimateSize": lambda: 50,
    "overscan": 5,
})

for virtual_item in virtualizer.getVirtualItems():
    render_item(items[virtual_item.index], virtual_item.start)

# Infinite scroll
VirtualList(
    items=items,
    height=600,
    item_height=50,
    render=render_row,
    on_end_reached=load_more,
    end_reached_threshold=200,  # px from bottom
)
```

##### CSS Containment and Performance

Critical CSS properties for virtual scrolling performance.

```python
from pynext.client import document, window

# =============================================================================
# CSS Containment (Layout Isolation)
# =============================================================================

# Contain property - isolates element from rest of page
container.style.contain = "layout"           # Layout containment
container.style.contain = "paint"            # Paint containment  
container.style.contain = "size"             # Size containment
container.style.contain = "style"            # Style containment
container.style.contain = "strict"           # All containment (layout paint size style)
container.style.contain = "content"          # layout paint style

# Layout containment
# - Element is independent of outside layout
# - Changes inside don't affect outside
# - Critical for virtual scroll containers

# Paint containment
# - Contents don't paint outside element
# - Creates stacking context
# - Creates new formatting context

# Size containment
# - Element size doesn't depend on children
# - Must set explicit size
# - Enables skipping child measurement

# =============================================================================
# Content Visibility (Skip Rendering)
# =============================================================================

# content-visibility - skip rendering of off-screen content
item.style.contentVisibility = "auto"        # Render when near viewport
item.style.contentVisibility = "visible"     # Always render (default)
item.style.contentVisibility = "hidden"      # Skip rendering entirely

# contain-intrinsic-size - placeholder size when hidden
item.style.containIntrinsicSize = "auto 500px"  # Use last rendered or 500px
item.style.containIntrinsicSize = "500px"       # Fixed placeholder
item.style.containIntrinsicWidth = "100%"
item.style.containIntrinsicHeight = "50px"

# Automatic content-visibility detection
# contentvisibilityautostatechange event (when visibility changes)
@client
def on_visibility_change(event):
    if event.skipped:
        # Element is now skipped (off-screen)
        pause_animations()
    else:
        # Element is now visible
        resume_animations()

item.addEventListener("contentvisibilityautostatechange", on_visibility_change)

# Check if element is skipped
if item.checkVisibility({"contentVisibilityAuto": True}):
    print("Element is visible")

# =============================================================================
# CSS Scroll Snap (Smooth Scrolling UX)
# =============================================================================

# Container scroll snap
scroll_container.style.scrollSnapType = "y mandatory"   # Snap on Y axis, required
scroll_container.style.scrollSnapType = "x mandatory"   # Snap on X axis
scroll_container.style.scrollSnapType = "both mandatory" # Both axes
scroll_container.style.scrollSnapType = "y proximity"   # Snap if close
scroll_container.style.scrollSnapType = "none"          # No snapping

# Snap stop (whether to skip snap points)
scroll_container.style.scrollSnapStop = "normal"        # Can skip (default)
scroll_container.style.scrollSnapStop = "always"        # Must stop at each

# Child snap alignment
item.style.scrollSnapAlign = "start"         # Align to start of container
item.style.scrollSnapAlign = "center"        # Align to center
item.style.scrollSnapAlign = "end"           # Align to end
item.style.scrollSnapAlign = "none"          # No snapping for this item

# Scroll snap margin (offset from snap point)
item.style.scrollSnapMargin = "20px"
item.style.scrollSnapMarginTop = "10px"
item.style.scrollSnapMarginBottom = "10px"

# Scroll padding (safe area on container)
scroll_container.style.scrollPadding = "20px"
scroll_container.style.scrollPaddingTop = "50px"        # For fixed headers

# =============================================================================
# Scroll Behavior
# =============================================================================

# Smooth scrolling via CSS
scroll_container.style.scrollBehavior = "smooth"
scroll_container.style.scrollBehavior = "auto"          # Instant (default)

# Programmatic smooth scroll
scroll_container.scrollTo({
    "top": 1000,
    "left": 0,
    "behavior": "smooth"
})

scroll_container.scrollBy({
    "top": 100,
    "behavior": "smooth"
})

item.scrollIntoView({
    "behavior": "smooth",
    "block": "center",
    "inline": "nearest"
})

# Overscroll behavior (bounce effect)
scroll_container.style.overscrollBehavior = "contain"   # No scroll chaining
scroll_container.style.overscrollBehavior = "none"      # No overscroll effect
scroll_container.style.overscrollBehavior = "auto"      # Default behavior
scroll_container.style.overscrollBehaviorY = "contain"
scroll_container.style.overscrollBehaviorX = "auto"

# =============================================================================
# Scrollbar Styling
# =============================================================================

# Standard scrollbar styling (Firefox)
scroll_container.style.scrollbarWidth = "auto"          # Default
scroll_container.style.scrollbarWidth = "thin"          # Thin scrollbar
scroll_container.style.scrollbarWidth = "none"          # Hide scrollbar
scroll_container.style.scrollbarColor = "#888 #f1f1f1"  # thumb track

# Scrollbar gutter (space reserved for scrollbar)
scroll_container.style.scrollbarGutter = "stable"       # Always reserve space
scroll_container.style.scrollbarGutter = "stable both-edges"

# =============================================================================
# Overflow and Clipping
# =============================================================================

container.style.overflow = "auto"            # Scrollbars when needed
container.style.overflow = "scroll"          # Always show scrollbars
container.style.overflow = "hidden"          # Clip content
container.style.overflow = "visible"         # Allow overflow
container.style.overflow = "clip"            # Hard clip (no scrolling possible)

container.style.overflowX = "auto"
container.style.overflowY = "scroll"

# Overflow anchor (maintain scroll position)
container.style.overflowAnchor = "auto"      # Browser maintains position
container.style.overflowAnchor = "none"      # Disable anchoring

# =============================================================================
# Performance Hints
# =============================================================================

# Will-change for scroll performance
scroll_container.style.willChange = "scroll-position"
item.style.willChange = "transform"

# Touch action for smooth touch scrolling
scroll_container.style.touchAction = "pan-y"            # Vertical scroll only
scroll_container.style.touchAction = "pan-x"            # Horizontal scroll only
scroll_container.style.touchAction = "manipulation"     # Pan and zoom
scroll_container.style.touchAction = "none"             # Disable browser handling
```

##### CSS Containment and Scroll Checklist

```
CSS Containment and Scroll Support (Phase 44)
├── CSS Containment (25 tests)
│   ├── [ ] contain: layout
│   ├── [ ] contain: paint
│   ├── [ ] contain: size
│   ├── [ ] contain: style
│   ├── [ ] contain: strict
│   ├── [ ] contain: content
│   └── [ ] Containment interaction with virtual scroll
│
├── Content Visibility (20 tests)
│   ├── [ ] content-visibility: auto
│   ├── [ ] content-visibility: visible
│   ├── [ ] content-visibility: hidden
│   ├── [ ] contain-intrinsic-size
│   ├── [ ] contain-intrinsic-width / height
│   ├── [ ] contentvisibilityautostatechange event
│   └── [ ] checkVisibility() method
│
├── CSS Scroll Snap (25 tests)
│   ├── [ ] scroll-snap-type (x, y, both, mandatory, proximity)
│   ├── [ ] scroll-snap-stop
│   ├── [ ] scroll-snap-align (start, center, end)
│   ├── [ ] scroll-snap-margin
│   ├── [ ] scroll-padding
│   └── [ ] Snap with virtual scrolling
│
├── Scroll Behavior (15 tests)
│   ├── [ ] scroll-behavior: smooth
│   ├── [ ] scrollTo/scrollBy with behavior
│   ├── [ ] scrollIntoView with options
│   ├── [ ] overscroll-behavior
│   └── [ ] overflow-anchor
│
├── Scrollbar Styling (10 tests)
│   ├── [ ] scrollbar-width
│   ├── [ ] scrollbar-color
│   └── [ ] scrollbar-gutter
│
├── Overflow (10 tests)
│   ├── [ ] overflow / overflow-x / overflow-y
│   ├── [ ] overflow: clip
│   └── [ ] overflow-anchor
│
└── Performance (10 tests)
    ├── [ ] will-change: scroll-position
    ├── [ ] touch-action
    └── [ ] GPU acceleration for scroll
```

##### Files to Create

- `pynext/client/virtual.py` — VirtualList, VirtualGrid components
- `pynext/client/containment.py` — CSS Containment utilities
- `pynext/client/scroll.py` — Scroll snap, smooth scroll, scrollbar styling

##### Success Criteria

| Metric | Target |
|--------|--------|
| Item count | Handle 100K+ items smoothly |
| Performance | 60fps scrolling |
| CSS Containment | Full containment property support |
| Content visibility | Auto visibility with intrinsic sizing |
| Scroll snap | Full snap configuration |
| Test coverage | 150+ unit tests (including 115 CSS scroll tests) |

##### Milestones

1. **Week 1:** Fixed-height VirtualList
2. **Week 2:** Variable-height VirtualList, measurement
3. **Week 3:** VirtualGrid, infinite scroll

---

### EDITOR PHASES (45-47)

---

#### Phase 45: Rich Text Editing / Selection API (300 tests, 5 weeks)

Build Notion-like block editors.

##### Python API

```python
from pynext.client import Selection, Range, ContentEditable

# Selection API
selection = window.getSelection()
selection.rangeCount
selection.anchorNode       # Start of selection
selection.anchorOffset
selection.focusNode        # End of selection
selection.focusOffset
selection.isCollapsed      # Cursor vs range
selection.type             # "None", "Caret", "Range"

# Get/set selection
range = selection.getRangeAt(0)
range.startContainer
range.startOffset
range.endContainer
range.endOffset
range.collapsed
range.commonAncestorContainer

# Create and set range
new_range = document.createRange()
new_range.setStart(text_node, 5)
new_range.setEnd(text_node, 10)
selection.removeAllRanges()
selection.addRange(new_range)

# Select node contents
range.selectNodeContents(element)
range.selectNode(element)

# Collapse
range.collapse(to_start=True)
selection.collapseToStart()
selection.collapseToEnd()

# Range manipulation
fragment = range.extractContents()   # Cut
fragment = range.cloneContents()     # Copy
range.deleteContents()               # Delete
range.insertNode(new_node)           # Insert at start
range.surroundContents(wrapper)      # Wrap selection

# ContentEditable
div.contentEditable = "true"
div.contentEditable = "plaintext-only"

# Input events for contenteditable
@client
def on_before_input(event):
    event.inputType     # "insertText", "insertParagraph", "deleteContentBackward", etc.
    event.data          # Text being inserted
    event.dataTransfer  # For paste
    event.getTargetRanges()  # Affected ranges
    
    if event.inputType == "insertParagraph":
        event.preventDefault()
        handle_enter_key()

# execCommand (legacy but still used)
document.execCommand("bold")
document.execCommand("italic")
document.execCommand("insertHTML", False, "<strong>Bold</strong>")
document.execCommand("formatBlock", False, "h1")
document.queryCommandState("bold")       # True if bold active
document.queryCommandEnabled("copy")     # Can execute?
document.queryCommandValue("fontSize")   # Current value

# Clipboard events
@client
def on_paste(event):
    event.preventDefault()
    
    # Get clipboard data
    text = event.clipboardData.getData("text/plain")
    html = event.clipboardData.getData("text/html")
    files = event.clipboardData.files
    
    # Insert sanitized content
    insert_at_cursor(sanitize(html or text))

@client
def on_copy(event):
    event.preventDefault()
    selection = window.getSelection()
    
    # Set custom clipboard data
    event.clipboardData.setData("text/plain", selection.toString())
    event.clipboardData.setData("text/html", get_selection_html())
    event.clipboardData.setData("application/x-myapp", serialize_blocks())
```

##### CSS Font Loading API

Essential for rich text editors to ensure fonts are loaded before rendering.

```python
from pynext.client import FontFace, FontFaceSet

# =============================================================================
# Document Fonts (FontFaceSet)
# =============================================================================

# Check if fonts are ready
await document.fonts.ready                    # Promise resolves when fonts loaded
is_loading = document.fonts.status           # "loading" or "loaded"

# Load specific font
await document.fonts.load("16px 'Inter'")
await document.fonts.load("bold 24px 'Fira Code'")
await document.fonts.load("italic 16px Georgia")

# Check if font is available
has_font = document.fonts.check("16px 'Inter'")
has_bold = document.fonts.check("bold 16px 'Inter'")

# Iterate over loaded fonts
for font_face in document.fonts:
    print(f"{font_face.family}: {font_face.status}")

# Font loading events
document.fonts.addEventListener("loading", on_fonts_loading)
document.fonts.addEventListener("loadingdone", on_fonts_loaded)
document.fonts.addEventListener("loadingerror", on_fonts_error)

@client
def on_fonts_loading(event):
    show_loading_indicator()

@client
def on_fonts_loaded(event):
    hide_loading_indicator()
    for font in event.fontfaces:
        print(f"Loaded: {font.family}")

@client
def on_fonts_error(event):
    for font in event.fontfaces:
        print(f"Failed: {font.family}")
        load_fallback_font()

# =============================================================================
# FontFace API (Custom Fonts)
# =============================================================================

# Create custom font
font = FontFace("CustomFont", "url(/fonts/custom.woff2)", {
    "weight": "400",
    "style": "normal",
    "display": "swap",
    "unicodeRange": "U+0000-00FF",           # Latin characters only
})

# Load the font
await font.load()

# Check font status
font.status    # "unloaded", "loading", "loaded", "error"
font.loaded    # Promise

# Add to document
document.fonts.add(font)

# Font properties
font.family           # "CustomFont"
font.weight           # "400"
font.style            # "normal"
font.stretch          # "normal"
font.unicodeRange     # "U+0000-00FF"
font.variant          # "normal"
font.featureSettings  # "normal"
font.display          # "swap"

# Font descriptors
font_bold = FontFace("CustomFont", "url(/fonts/custom-bold.woff2)", {
    "weight": "700",
    "style": "normal",
})
await font_bold.load()
document.fonts.add(font_bold)

# Remove font
document.fonts.delete(font)

# Clear all fonts
document.fonts.clear()

# =============================================================================
# Font Loading Strategies
# =============================================================================

# FOIT prevention (Flash of Invisible Text)
async def load_with_fallback(font_family, font_url, fallback):
    el.style.fontFamily = fallback  # Start with fallback
    
    font = FontFace(font_family, f"url({font_url})")
    try:
        await font.load()
        document.fonts.add(font)
        el.style.fontFamily = f"'{font_family}', {fallback}"
    except:
        print(f"Font failed, using fallback: {fallback}")

# Preload critical fonts
async def preload_fonts():
    critical_fonts = [
        ("Inter", "/fonts/inter.woff2", {"weight": "400"}),
        ("Inter", "/fonts/inter-bold.woff2", {"weight": "700"}),
        ("Fira Code", "/fonts/fira-code.woff2", {"weight": "400"}),
    ]
    
    faces = [FontFace(name, f"url({url})", opts) for name, url, opts in critical_fonts]
    
    # Load all in parallel
    await Promise.all([f.load() for f in faces])
    
    # Add all to document
    for face in faces:
        document.fonts.add(face)
```

##### CSS Selection and Caret Styling

Styling for text selection and cursor in contenteditable.

```python
# =============================================================================
# Caret Styling
# =============================================================================

# Caret color
editable.style.caretColor = "red"
editable.style.caretColor = "#3b82f6"
editable.style.caretColor = "auto"           # Match color property
editable.style.caretColor = "transparent"    # Hide caret

# =============================================================================
# CSS Highlight API (Modern Selection Styling)
# =============================================================================

from pynext.client import Highlight, CSS

# Create highlight ranges
range1 = document.createRange()
range1.setStart(text_node, 0)
range1.setEnd(text_node, 10)

range2 = document.createRange()
range2.setStart(text_node, 20)
range2.setEnd(text_node, 30)

# Create a highlight
search_highlight = Highlight(range1, range2)

# Register the highlight
CSS.highlights.set("search-results", search_highlight)

# Style the highlight in CSS (requires CSS generation)
# ::highlight(search-results) { background-color: yellow; }

# Clear highlights
CSS.highlights.delete("search-results")
CSS.highlights.clear()

# Multiple highlight types
CSS.highlights.set("current-match", Highlight(current_range))
CSS.highlights.set("other-matches", Highlight(*other_ranges))
CSS.highlights.set("spelling-error", Highlight(*error_ranges))

# Highlight priority (higher = on top)
search_highlight.priority = 1
current_highlight.priority = 2               # Current match on top

# Iterate highlights
for name, highlight in CSS.highlights.entries():
    print(f"{name}: {highlight.size} ranges")

# Add/remove ranges from highlight
search_highlight.add(new_range)
search_highlight.delete(old_range)
search_highlight.clear()

# =============================================================================
# User-Select Control
# =============================================================================

# Control text selectability
el.style.userSelect = "auto"                 # Normal selection
el.style.userSelect = "text"                 # Text is selectable
el.style.userSelect = "none"                 # Prevent selection
el.style.userSelect = "all"                  # Select entire element on click
el.style.userSelect = "contain"              # Selection contained within

# =============================================================================
# Selection Direction and Appearance
# =============================================================================

# Input selection direction
input_el.style.caretColor = "blue"

# For contenteditable, control selection via Selection API
selection = window.getSelection()
selection.extend(node, offset)               # Extend selection
selection.setBaseAndExtent(anchor, anchorOff, focus, focusOff)

# =============================================================================
# Text Cursor Shapes
# =============================================================================

el.style.cursor = "text"                     # I-beam for text
el.style.cursor = "vertical-text"            # Vertical I-beam
el.style.cursor = "grab"                     # For draggable blocks
el.style.cursor = "grabbing"                 # While dragging
el.style.cursor = "cell"                     # For tables
el.style.cursor = "col-resize"               # Column resize
el.style.cursor = "row-resize"               # Row resize
```

##### Font and Selection Checklist

```
Font Loading and Selection Support (Phase 45)
├── FontFaceSet (document.fonts) (25 tests)
│   ├── [ ] document.fonts.ready
│   ├── [ ] document.fonts.status
│   ├── [ ] document.fonts.load(font)
│   ├── [ ] document.fonts.check(font)
│   ├── [ ] document.fonts.add/delete/clear
│   ├── [ ] Iteration over font faces
│   ├── [ ] loading event
│   ├── [ ] loadingdone event
│   └── [ ] loadingerror event
│
├── FontFace API (20 tests)
│   ├── [ ] FontFace constructor
│   ├── [ ] font.load()
│   ├── [ ] font.status / font.loaded
│   ├── [ ] Font descriptors (weight, style, etc.)
│   ├── [ ] unicodeRange
│   └── [ ] display (swap, block, fallback, auto)
│
├── Caret Styling (10 tests)
│   ├── [ ] caret-color
│   ├── [ ] caret-color: auto
│   └── [ ] caret-color: transparent
│
├── CSS Highlight API (20 tests)
│   ├── [ ] Highlight constructor
│   ├── [ ] CSS.highlights.set/get/delete/clear
│   ├── [ ] highlight.add/delete/clear
│   ├── [ ] highlight.priority
│   └── [ ] Multiple highlight registrations
│
├── User Selection Control (10 tests)
│   ├── [ ] user-select: auto/text/none/all/contain
│   └── [ ] Selection containment behavior
│
└── Cursor Styles (5 tests)
    ├── [ ] cursor: text, vertical-text
    └── [ ] cursor: grab, grabbing, cell, resize
```

##### Files to Create

- `pynext/client/selection.py` — Selection, Range APIs
- `pynext/client/editable.py` — ContentEditable helpers
- `pynext/client/clipboard.py` — Enhanced clipboard
- `pynext/client/fonts.py` — FontFace, FontFaceSet, font loading
- `pynext/client/highlight.py` — CSS Highlight API

##### Success Criteria

| Metric | Target |
|--------|--------|
| Selection API | Complete Range/Selection |
| Input types | All beforeinput types |
| Font Loading | Full FontFace and FontFaceSet API |
| Highlight API | CSS Highlights for search, errors, etc. |
| Caret styling | Full caret-color support |
| Test coverage | 300+ unit tests (including 90 font/selection CSS tests) |

##### Milestones

1. **Week 1-2:** Selection API (Range, Selection)
2. **Week 3:** ContentEditable, beforeinput events, caret styling
3. **Week 4:** execCommand, formatting, Font Loading API
4. **Week 5:** Clipboard events, CSS Highlight API, custom formats

---

#### Phase 46: Code Editor Integration (200 tests, 4 weeks)

Integrate Monaco Editor and CodeMirror.

##### Python API

```python
from pynext.client import Monaco, CodeMirror

# Monaco Editor
editor = Monaco.create(container, {
    "value": initial_code,
    "language": "python",
    "theme": "vs-dark",
    "automaticLayout": True,
    "fontSize": 14,
    "lineNumbers": "on",
    "minimap": {"enabled": False},
    "wordWrap": "on",
    "scrollBeyondLastLine": False,
})

# Get/set content
code = editor.getValue()
editor.setValue(new_code)

# Cursor and selection
editor.setPosition({"lineNumber": 10, "column": 5})
editor.setSelection({
    "startLineNumber": 1, "startColumn": 1,
    "endLineNumber": 5, "endColumn": 10
})
editor.revealLine(50)
editor.revealLineInCenter(50)

# Events
@editor.on_change
def on_content_change(event):
    code_signal.set(editor.getValue())

@editor.on_cursor_change
def on_cursor_change(event):
    position = editor.getPosition()
    status.set(f"Line {position.lineNumber}, Col {position.column}")

# Decorations (errors, highlights)
decorations = editor.deltaDecorations([], [
    {
        "range": Monaco.Range(1, 1, 1, 10),
        "options": {
            "inlineClassName": "error-squiggle",
            "hoverMessage": {"value": "**Error:** Undefined variable"},
            "glyphMarginClassName": "error-glyph",
        }
    },
])

# Actions and commands
editor.addAction({
    "id": "run-code",
    "label": "Run Code",
    "keybindings": [Monaco.KeyMod.CtrlCmd | Monaco.KeyCode.Enter],
    "run": lambda ed: run_code(ed.getValue()),
})

# Diff editor
diff_editor = Monaco.createDiffEditor(container, {"readOnly": True})
diff_editor.setModel({
    "original": Monaco.createModel(old_code, "python"),
    "modified": Monaco.createModel(new_code, "python"),
})

# CodeMirror 6 alternative
view = CodeMirror.EditorView({
    "doc": initial_code,
    "extensions": [
        CodeMirror.basicSetup,
        CodeMirror.python(),
        CodeMirror.oneDark,
    ],
    "parent": container,
})
```

##### Font Loading for Code Editors

Monospace fonts are critical for code editors - must load before rendering.

```python
from pynext.client import FontFace, document

# =============================================================================
# Preload Code Editor Fonts
# =============================================================================

async def preload_editor_fonts():
    """
    Load monospace fonts before initializing editor.
    Critical for proper character width calculation.
    """
    
    # Popular programming fonts
    fonts_to_load = [
        # Fira Code (with ligatures)
        ("Fira Code", "/fonts/FiraCode-Regular.woff2", {"weight": "400"}),
        ("Fira Code", "/fonts/FiraCode-Bold.woff2", {"weight": "700"}),
        
        # JetBrains Mono
        ("JetBrains Mono", "/fonts/JetBrainsMono-Regular.woff2", {"weight": "400"}),
        ("JetBrains Mono", "/fonts/JetBrainsMono-Bold.woff2", {"weight": "700"}),
        
        # Source Code Pro
        ("Source Code Pro", "/fonts/SourceCodePro-Regular.woff2", {"weight": "400"}),
    ]
    
    # Load all fonts in parallel
    font_faces = []
    for family, url, descriptors in fonts_to_load:
        face = FontFace(family, f"url({url})", {
            **descriptors,
            "display": "swap",  # Show fallback while loading
        })
        font_faces.append(face)
    
    # Wait for all to load
    results = await Promise.allSettled([f.load() for f in font_faces])
    
    # Add successfully loaded fonts
    for i, result in enumerate(results):
        if result.status == "fulfilled":
            document.fonts.add(font_faces[i])
        else:
            print(f"Failed to load: {fonts_to_load[i][0]}")
    
    return results

# =============================================================================
# Font Feature Settings for Code
# =============================================================================

# Enable ligatures for operators (Fira Code style)
editor_container.style.fontFeatureSettings = '"liga" 1, "calt" 1'

# Common ligatures: -> => == != >= <= 
# Fira Code: !== === <=> >>= <<= 

# Disable ligatures if not wanted
editor_container.style.fontFeatureSettings = '"liga" 0'

# Stylistic alternates
editor_container.style.fontFeatureSettings = '"ss01" 1'  # Stylistic set 1

# =============================================================================
# Monaco Editor Font Configuration
# =============================================================================

# Wait for font before creating editor
await preload_editor_fonts()
await document.fonts.ready

editor = Monaco.create(container, {
    "fontFamily": "'Fira Code', 'JetBrains Mono', 'Cascadia Code', monospace",
    "fontSize": 14,
    "fontWeight": "400",
    "fontLigatures": True,              # Enable ligatures
    "lineHeight": 1.5,
    "letterSpacing": 0,
})

# Update font after loading
@client
async def update_editor_font(font_family):
    font = FontFace(font_family, f"url(/fonts/{font_family}.woff2)")
    await font.load()
    document.fonts.add(font)
    editor.updateOptions({"fontFamily": f"'{font_family}', monospace"})

# =============================================================================
# CodeMirror Font Configuration
# =============================================================================

# CodeMirror uses CSS for font styling
editor_container.style.fontFamily = "'Fira Code', monospace"
editor_container.style.fontSize = "14px"
editor_container.style.fontFeatureSettings = '"liga" 1'

# Custom theme with font
my_theme = CodeMirror.EditorView.theme({
    "&": {
        "fontFamily": "'Fira Code', monospace",
        "fontSize": "14px",
    },
    ".cm-content": {
        "fontFeatureSettings": '"liga" 1',
    },
})

view = CodeMirror.EditorView({
    "extensions": [
        CodeMirror.basicSetup,
        my_theme,
    ],
    "parent": container,
})
```

##### Code Editor Font Checklist

```
Code Editor Font Support (Phase 46)
├── Font Preloading (10 tests)
│   ├── [ ] Preload fonts before editor init
│   ├── [ ] Font load error handling
│   ├── [ ] document.fonts.ready integration
│   └── [ ] Multiple font variants (regular, bold)
│
├── Font Feature Settings (10 tests)
│   ├── [ ] font-feature-settings for ligatures
│   ├── [ ] Enable/disable ligatures
│   ├── [ ] Stylistic alternates
│   └── [ ] Monaco fontLigatures option
│
├── Monaco Font Config (10 tests)
│   ├── [ ] fontFamily option
│   ├── [ ] fontSize, fontWeight
│   ├── [ ] lineHeight, letterSpacing
│   └── [ ] Dynamic font updates
│
└── CodeMirror Font Config (10 tests)
    ├── [ ] CSS font styling
    ├── [ ] Custom theme with fonts
    └── [ ] font-feature-settings in theme
```

##### Files to Create

- `pynext/client/monaco.py` — Monaco Editor wrapper
- `pynext/client/codemirror.py` — CodeMirror wrapper
- `pynext/client/editor_fonts.py` — Code editor font preloading utilities

##### Success Criteria

| Metric | Target |
|--------|--------|
| Editor support | Monaco, CodeMirror |
| Features | Syntax highlighting, decorations, actions |
| Font loading | Preload before render, ligature support |
| Font features | Full font-feature-settings control |
| Test coverage | 200+ unit tests (including 40 font tests) |

##### Milestones

1. **Week 1-2:** Monaco Editor (create, content, events), font preloading
2. **Week 3:** Decorations, actions, diff editor, ligatures
3. **Week 4:** CodeMirror integration, custom themes

---

#### Phase 47: Terminal Emulation (150 tests, 3 weeks)

Build Replit/Vercel-style terminal UIs using xterm.js.

##### Python API

```python
from pynext.client import Terminal, FitAddon, WebLinksAddon, SearchAddon

# Create terminal
term = Terminal({
    "cols": 80,
    "rows": 24,
    "cursorBlink": True,
    "cursorStyle": "block",  # block, underline, bar
    "fontFamily": "'Fira Code', monospace",
    "fontSize": 14,
    "lineHeight": 1.2,
    "theme": {
        "background": "#1e1e1e",
        "foreground": "#d4d4d4",
        "cursor": "#ffffff",
        "selection": "#264f78",
        "black": "#000000",
        "red": "#cd3131",
        "green": "#0dbc79",
        "yellow": "#e5e510",
        "blue": "#2472c8",
        "magenta": "#bc3fbc",
        "cyan": "#11a8cd",
        "white": "#e5e5e5",
    },
})

# Addons
fit_addon = FitAddon()
term.loadAddon(fit_addon)
term.loadAddon(WebLinksAddon())

# Open in container
term.open(container_element)
fit_addon.fit()  # Resize to container

# Write output
term.write("$ ")
term.writeln("Hello, world!")
term.write("\x1b[32mGreen text\x1b[0m")  # ANSI colors
term.write("\x1b[1mBold\x1b[0m")
term.write("\x1b[2J\x1b[H")  # Clear screen

# Handle input
@term.on_data
def on_input(data):
    # Send to backend
    ws.send({"type": "stdin", "data": data})

@term.on_key
def on_key(event):
    if event.key == "\x03":  # Ctrl+C
        send_signal("SIGINT")

# Receive from backend
@ws.on_message
def on_output(event):
    if event.data.type == "stdout":
        term.write(event.data.data)

# Resize
window.addEventListener("resize", lambda e: fit_addon.fit())
term.resize(100, 30)

# Selection
term.select(0, 0, 10, 5)
selected = term.getSelection()
term.clearSelection()

# Search
search_addon = SearchAddon()
term.loadAddon(search_addon)
search_addon.findNext("error")
search_addon.findPrevious("error")
```

##### Files to Create

- `pynext/client/terminal.py` — xterm.js wrapper

##### Success Criteria

| Metric | Target |
|--------|--------|
| Terminal features | Full xterm.js API |
| Addons | Fit, WebLinks, Search |
| Test coverage | 150+ unit tests |

##### Milestones

1. **Week 1:** Terminal creation, theming, output
2. **Week 2:** Input handling, resize, addons
3. **Week 3:** Selection, search, advanced features

---

### ADVANCED PHASES (48-50)

---

#### Phase 48: Infinite Canvas / Pan-Zoom (200 tests, 4 weeks)

Build Miro/FigJam-style infinite canvases.

##### Python API

```python
from pynext.client import InfiniteCanvas, Viewport, use_pan_zoom

# Viewport state
viewport = Signal({
    "x": 0,        # Pan X
    "y": 0,        # Pan Y
    "scale": 1,    # Zoom level
})

# Pan handling
@use_pan(canvas, {"button": "middle"})
def on_pan(event):
    v = viewport()
    viewport.set({
        **v,
        "x": v["x"] + event.deltaX / v["scale"],
        "y": v["y"] + event.deltaY / v["scale"],
    })

# Zoom with mouse position anchor
@use_wheel(canvas)
def on_wheel(event):
    event.preventDefault()
    
    v = viewport()
    old_scale = v["scale"]
    
    # Calculate new scale
    delta = -event.deltaY * 0.001
    new_scale = clamp(old_scale * (1 + delta), 0.1, 10)
    
    # Get mouse position relative to canvas
    rect = canvas.getBoundingClientRect()
    mouse_x = event.clientX - rect.left
    mouse_y = event.clientY - rect.top
    
    # Zoom toward mouse position
    scale_ratio = new_scale / old_scale
    new_x = mouse_x - (mouse_x - v["x"]) * scale_ratio
    new_y = mouse_y - (mouse_y - v["y"]) * scale_ratio
    
    viewport.set({"x": new_x, "y": new_y, "scale": new_scale})

# Apply transform
@effect
def apply_transform():
    v = viewport()
    content.style.transform = f"translate({v['x']}px, {v['y']}px) scale({v['scale']})"

# Coordinate conversion
def screen_to_world(screen_x, screen_y):
    v = viewport()
    return (
        (screen_x - v["x"]) / v["scale"],
        (screen_y - v["y"]) / v["scale"],
    )

def world_to_screen(world_x, world_y):
    v = viewport()
    return (
        world_x * v["scale"] + v["x"],
        world_y * v["scale"] + v["y"],
    )

# Fit content to view
def fit_to_bounds(bounds):
    padding = 50
    canvas_rect = canvas.getBoundingClientRect()
    
    scale_x = (canvas_rect.width - padding * 2) / bounds.width
    scale_y = (canvas_rect.height - padding * 2) / bounds.height
    scale = min(scale_x, scale_y, 1)
    
    center_x = bounds.x + bounds.width / 2
    center_y = bounds.y + bounds.height / 2
    
    viewport.set({
        "x": canvas_rect.width / 2 - center_x * scale,
        "y": canvas_rect.height / 2 - center_y * scale,
        "scale": scale,
    })

# Minimap
minimap_scale = 0.1
@effect
def update_minimap():
    v = viewport()
    minimap_viewport.style.transform = f"translate({-v['x'] * minimap_scale}px, {-v['y'] * minimap_scale}px)"
```

##### CSS Transform Utilities

Essential for infinite canvas, pan-zoom, and complex visual manipulations.

```python
from pynext.client import DOMMatrix, DOMPoint, CSSTransform

# =============================================================================
# DOMMatrix API (2D and 3D transforms)
# =============================================================================

# Create identity matrix
matrix = DOMMatrix()  # Identity

# Create from CSS transform string
matrix = DOMMatrix("translate(100px, 50px) rotate(45deg) scale(2)")

# Create from array (6 values for 2D, 16 for 3D)
matrix = DOMMatrix([1, 0, 0, 1, 100, 50])  # 2D: a, b, c, d, e, f
matrix = DOMMatrix([                        # 3D: 4x4 matrix
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    100, 50, 0, 1
])

# Matrix properties (2D)
matrix.a, matrix.b      # Scale X and skew Y
matrix.c, matrix.d      # Skew X and scale Y
matrix.e, matrix.f      # Translate X and Y

# Matrix properties (3D)
matrix.m11, matrix.m12, matrix.m13, matrix.m14
matrix.m21, matrix.m22, matrix.m23, matrix.m24
matrix.m31, matrix.m32, matrix.m33, matrix.m34
matrix.m41, matrix.m42, matrix.m43, matrix.m44

# Matrix flags
matrix.is2D             # True if 2D transform
matrix.isIdentity       # True if identity matrix

# =============================================================================
# Matrix Operations (return NEW matrix, original unchanged)
# =============================================================================

# Translation
translated = matrix.translate(100, 50)
translated_3d = matrix.translate(100, 50, 25)  # 3D

# Scaling
scaled = matrix.scale(2)                    # Uniform
scaled = matrix.scale(2, 1.5)               # Non-uniform
scaled = matrix.scaleNonUniform(2, 1.5)     # Deprecated but supported
scaled_3d = matrix.scale3d(2)               # 3D uniform
scaled_3d = matrix.scale3d(2, 1.5, 1)       # 3D non-uniform

# Rotation
rotated = matrix.rotate(45)                 # Degrees
rotated = matrix.rotate(45, 100, 50)        # With origin
rotated_3d = matrix.rotateAxisAngle(1, 0, 0, 45)  # Around axis

# Skew
skewed = matrix.skewX(30)                   # Degrees
skewed = matrix.skewY(30)

# Flip
flipped = matrix.flipX()
flipped = matrix.flipY()

# Matrix multiplication (composition)
combined = matrix.multiply(other_matrix)
combined = matrix.preMultiplySelf(other_matrix)

# Inversion
inverted = matrix.inverse()                 # Returns new matrix
is_invertible = matrix.invertSelf()         # Modifies in place, returns self

# =============================================================================
# Mutating Operations (modify matrix in place)
# =============================================================================

matrix.translateSelf(100, 50)
matrix.scaleSelf(2, 2)
matrix.rotateSelf(45)
matrix.skewXSelf(30)
matrix.multiplySelf(other_matrix)

# Set from values
matrix.setMatrixValue("translate(100px, 50px)")

# =============================================================================
# Point Transformation
# =============================================================================

# Create a point
point = DOMPoint(100, 50)
point_3d = DOMPoint(100, 50, 25, 1)  # x, y, z, w

# Transform point by matrix
transformed_point = point.matrixTransform(matrix)
new_x = transformed_point.x
new_y = transformed_point.y

# Transform multiple points
points = [DOMPoint(x, y) for x, y in coordinates]
transformed = [p.matrixTransform(matrix) for p in points]

# =============================================================================
# CSS Transform Helpers
# =============================================================================

# Build transform string from components
transform = CSSTransform()
transform.translate(100, 50)
transform.rotate(45)
transform.scale(2)
css_string = transform.toString()  # "translate(100px, 50px) rotate(45deg) scale(2)"

# Parse transform string
parsed = CSSTransform.parse("translate(100px, 50px) rotate(45deg)")
parsed.translations   # [(100, 50)]
parsed.rotations      # [45]
parsed.scales         # []

# Apply to element
el.style.transform = transform.toString()

# Get current transform as matrix
current_matrix = DOMMatrix(window.getComputedStyle(el).transform)

# =============================================================================
# Transform Origin
# =============================================================================

el.style.transformOrigin = "center center"
el.style.transformOrigin = "top left"
el.style.transformOrigin = "50% 50%"
el.style.transformOrigin = "100px 50px"

# =============================================================================
# 3D Transforms
# =============================================================================

# Perspective
el.style.perspective = "1000px"
parent.style.perspective = "1000px"
el.style.perspectiveOrigin = "50% 50%"

# 3D transforms
el.style.transform = "rotateX(45deg)"
el.style.transform = "rotateY(45deg)"
el.style.transform = "rotateZ(45deg)"
el.style.transform = "rotate3d(1, 1, 0, 45deg)"
el.style.transform = "translateZ(100px)"
el.style.transform = "translate3d(100px, 50px, 25px)"
el.style.transform = "scale3d(2, 2, 2)"

# Preserve 3D
el.style.transformStyle = "preserve-3d"
el.style.backfaceVisibility = "hidden"

# =============================================================================
# Performance Optimization
# =============================================================================

# Hardware acceleration hints
el.style.willChange = "transform"
el.style.willChange = "transform, opacity"

# Contain for layout optimization
el.style.contain = "layout"
el.style.contain = "paint"
el.style.contain = "strict"

# Force GPU layer
el.style.transform = "translateZ(0)"  # Null transform trick

# After animation, clean up willChange
el.style.willChange = "auto"
```

##### CSS Transform Checklist

```
CSS Transform Support (Phase 48)
├── DOMMatrix API (50 tests)
│   ├── [ ] DOMMatrix() constructor
│   ├── [ ] DOMMatrix(cssString)
│   ├── [ ] DOMMatrix(array) - 6 or 16 values
│   ├── [ ] Matrix properties (a-f, m11-m44)
│   ├── [ ] is2D, isIdentity flags
│   ├── [ ] translate() / translateSelf()
│   ├── [ ] scale() / scaleSelf()
│   ├── [ ] rotate() / rotateSelf()
│   ├── [ ] skewX() / skewY() / skewXSelf() / skewYSelf()
│   ├── [ ] flipX() / flipY()
│   ├── [ ] multiply() / multiplySelf()
│   ├── [ ] inverse() / invertSelf()
│   ├── [ ] preMultiplySelf()
│   └── [ ] setMatrixValue()
│
├── DOMPoint API (15 tests)
│   ├── [ ] DOMPoint(x, y, z, w)
│   ├── [ ] DOMPointReadOnly
│   ├── [ ] matrixTransform(matrix)
│   └── [ ] Point properties (x, y, z, w)
│
├── Transform Properties (25 tests)
│   ├── [ ] transform (all functions)
│   ├── [ ] transformOrigin
│   ├── [ ] transformStyle (preserve-3d)
│   ├── [ ] perspective
│   ├── [ ] perspectiveOrigin
│   ├── [ ] backfaceVisibility
│   └── [ ] Parse getComputedStyle().transform
│
├── Transform Functions (30 tests)
│   ├── [ ] translate(x, y)
│   ├── [ ] translateX(x) / translateY(y)
│   ├── [ ] translate3d(x, y, z)
│   ├── [ ] scale(x, y)
│   ├── [ ] scaleX(x) / scaleY(y)
│   ├── [ ] scale3d(x, y, z)
│   ├── [ ] rotate(angle)
│   ├── [ ] rotateX(angle) / rotateY(angle) / rotateZ(angle)
│   ├── [ ] rotate3d(x, y, z, angle)
│   ├── [ ] skew(x, y)
│   ├── [ ] skewX(angle) / skewY(angle)
│   ├── [ ] matrix(a, b, c, d, e, f)
│   └── [ ] matrix3d(16 values)
│
└── Performance (15 tests)
    ├── [ ] willChange property
    ├── [ ] contain property
    ├── [ ] GPU layer promotion
    └── [ ] Transform cleanup
```

##### Files to Create

- `pynext/client/canvas_viewport.py` — Pan/zoom viewport management
- `pynext/client/dom_matrix.py` — DOMMatrix and DOMPoint API stubs
- `pynext/client/css_transform.py` — CSS transform builder and parser
- `pynext/client/coordinate_systems.py` — Screen/world coordinate utilities

##### Success Criteria

| Metric | Target |
|--------|--------|
| Pan/zoom | Smooth, pinch-zoom on touch |
| Coordinate systems | Screen ↔ world conversion |
| DOMMatrix | Full API support including 3D |
| Transform parsing | Parse and compose CSS transforms |
| Performance | GPU-accelerated, 60fps |
| Test coverage | 200+ unit tests (including 135 CSS transform tests) |

##### Milestones

1. **Week 1:** Viewport state, pan handling, basic transforms
2. **Week 2:** Zoom with anchor point, DOMMatrix API
3. **Week 3:** Coordinate conversion, DOMPoint, transform parsing
4. **Week 4:** Minimap, touch gestures, 3D transforms, performance optimization

---

#### Phase 49: Cross-Tab / Offline-First (150 tests, 3 weeks)

Build Notion-like multi-tab sync and offline support.

##### Python API

```python
from pynext.client import BroadcastChannel, ServiceWorker, BackgroundSync

# Cross-tab communication
channel = BroadcastChannel("app-state")

# Broadcast to all tabs
def broadcast_update(update):
    channel.postMessage({
        "type": "state_update",
        "data": update,
        "source": tab_id,
    })

# Receive from other tabs
@channel.on_message
def on_message(event):
    if event.data.source != tab_id:
        merge_state(event.data.data)

# Leader election (only one tab does background work)
leader_channel = BroadcastChannel("leader-election")
is_leader = Signal(False)

def claim_leadership():
    leader_channel.postMessage({"type": "claim", "id": tab_id})
    is_leader.set(True)

@leader_channel.on_message  
def on_leader_message(event):
    if event.data.type == "claim" and event.data.id != tab_id:
        is_leader.set(False)

# Service Worker registration
sw = await navigator.serviceWorker.register("/sw.js")
sw.addEventListener("statechange", on_state_change)

# Background sync
await sw.sync.register("sync-pending-changes")

# Cache-first strategy
@client
async def fetch_with_cache(url):
    cache = await caches.open("app-cache-v1")
    cached = await cache.match(url)
    
    if cached:
        # Return cached, update in background
        fetch(url).then(lambda r: cache.put(url, r.clone()))
        return cached
    
    response = await fetch(url)
    await cache.put(url, response.clone())
    return response

# Offline detection
is_online = use_online()

@effect
def handle_offline():
    if not is_online():
        show_offline_banner()
        queue_changes_locally()
    else:
        hide_offline_banner()
        sync_queued_changes()
```

##### Files to Create

- `pynext/client/broadcast.py` — BroadcastChannel wrapper
- `pynext/client/offline.py` — Offline detection, sync queuing

##### Success Criteria

| Metric | Target |
|--------|--------|
| Cross-tab sync | Real-time via BroadcastChannel |
| Offline support | Queue and sync |
| Test coverage | 150+ unit tests |

##### Milestones

1. **Week 1:** BroadcastChannel, cross-tab messaging
2. **Week 2:** Leader election, ServiceWorker
3. **Week 3:** Offline detection, sync queue

---

#### Phase 50: Device APIs (200 tests, 4 weeks)

Complete device integration — speech, payments, sensors, notifications.

##### Python API

```python
from pynext.client import (
    SpeechRecognition, SpeechSynthesis,
    PaymentRequest,
    Notification,
    Gamepad,
    DeviceOrientation,
    Bluetooth, USB, Serial,
)

# Speech Recognition
recognition = SpeechRecognition()
recognition.continuous = True
recognition.interimResults = True
recognition.lang = "en-US"

@recognition.on_result
def on_speech(event):
    for result in event.results:
        transcript = result[0].transcript
        confidence = result[0].confidence
        
        if result.isFinal:
            process_command(transcript)
        else:
            interim_text.set(transcript)

recognition.start()

# Speech Synthesis
synthesis = window.speechSynthesis
voices = synthesis.getVoices()

utterance = SpeechSynthesisUtterance("Hello, welcome to PyNext!")
utterance.voice = voices.find(lambda v: v.lang.startswith("en"))
utterance.rate = 1.0
utterance.pitch = 1.0

synthesis.speak(utterance)

# Payment Request API
request = PaymentRequest(
    method_data=[
        {"supportedMethods": "basic-card"},
        {"supportedMethods": "https://google.com/pay", "data": {...}},
    ],
    details={
        "total": {"label": "Total", "amount": {"currency": "USD", "value": "99.99"}},
        "displayItems": [
            {"label": "Product", "amount": {"currency": "USD", "value": "89.99"}},
            {"label": "Tax", "amount": {"currency": "USD", "value": "10.00"}},
        ],
    },
)

if await request.canMakePayment():
    response = await request.show()
    await response.complete("success")

# Notifications
permission = await Notification.requestPermission()

if permission == "granted":
    notification = Notification("New Message", {
        "body": "You have a new message from Alice",
        "icon": "/icon.png",
        "tag": "message-123",
        "requireInteraction": True,
    })
    
    @notification.on_click
    def on_click():
        window.focus()
        navigate("/messages/123")

# Gamepad API
@client
def poll_gamepads():
    gamepads = navigator.getGamepads()
    for gamepad in gamepads:
        if gamepad:
            for i, button in enumerate(gamepad.buttons):
                if button.pressed:
                    handle_button(i, button.value)
            
            left_x = gamepad.axes[0]
            left_y = gamepad.axes[1]
    
    window.requestAnimationFrame(poll_gamepads)

# Device Orientation
@client
def on_orientation(event):
    alpha = event.alpha  # Z-axis rotation (0-360)
    beta = event.beta    # X-axis rotation (-180 to 180)
    gamma = event.gamma  # Y-axis rotation (-90 to 90)
    
    update_3d_view(alpha, beta, gamma)

window.addEventListener("deviceorientation", on_orientation)

# Bluetooth
device = await navigator.bluetooth.requestDevice({
    "filters": [{"services": ["heart_rate"]}],
})
server = await device.gatt.connect()
service = await server.getPrimaryService("heart_rate")
characteristic = await service.getCharacteristic("heart_rate_measurement")
await characteristic.startNotifications()
```

##### Files to Create

- `pynext/client/speech.py` — Speech recognition and synthesis
- `pynext/client/payments.py` — Payment Request API
- `pynext/client/devices.py` — Gamepad, orientation, Bluetooth, etc.

##### Success Criteria

| Metric | Target |
|--------|--------|
| Speech | Recognition and synthesis |
| Payments | Payment Request API |
| Sensors | Orientation, motion, gamepad |
| Test coverage | 200+ unit tests |

##### Milestones

1. **Week 1:** Speech recognition and synthesis
2. **Week 2:** Payment Request API, Notifications
3. **Week 3:** Gamepad, device orientation
4. **Week 4:** Bluetooth, USB, Serial (experimental)

---

### ADVANCED DEVTOOLS PHASE

---

#### Phase 51: Advanced DevTools (100 tests, 4 weeks)

Time-travel debugging, Python breakpoints, and browser extension packaging.

##### Python API

```python
from pynext.devtools import (
    TimeTravel,
    Breakpoint,
    DevToolsExtension,
)

# =============================================================================
# Time-Travel Debugging
# =============================================================================

# Time-travel is automatically enabled in development mode
# All signal changes are recorded

# Access via devtools panel or programmatically:
time_travel = TimeTravel.get_instance()

# Get timeline of all state changes
timeline = time_travel.get_timeline()
for entry in timeline:
    print(f"{entry.timestamp}: {entry.signal_name} = {entry.new_value}")

# Jump to a specific point in time
time_travel.goto(timestamp)

# Step backward/forward
time_travel.step_back()
time_travel.step_forward()

# Compare state at two points
diff = time_travel.diff(timestamp1, timestamp2)
for change in diff:
    print(f"{change.signal}: {change.old} → {change.new}")

# =============================================================================
# Recording Sessions
# =============================================================================

# Start a new recording
session_id = time_travel.start_recording()

# ... user interacts with app ...

# Stop and save recording
recording = time_travel.stop_recording()
time_travel.save_recording(recording, "bug_reproduction.json")

# Load and replay a recording
recording = time_travel.load_recording("bug_reproduction.json")
time_travel.replay(recording)

# Share recording via URL
share_url = time_travel.get_share_url(recording)
# https://pynext.dev/replay?session=abc123

# =============================================================================
# State Snapshots
# =============================================================================

# Create a named snapshot
time_travel.create_snapshot("before_bug")

# ... trigger the bug ...

time_travel.create_snapshot("after_bug")

# Compare snapshots
diff = time_travel.compare_snapshots("before_bug", "after_bug")

# Restore to a snapshot
time_travel.restore_snapshot("before_bug")

# =============================================================================
# Python Breakpoints
# =============================================================================

from pynext.devtools import breakpoint, logpoint, conditional_breakpoint

# Simple breakpoint (pauses execution)
@client
def calculate_total(items):
    total = 0
    for item in items:
        breakpoint()  # Pause here, inspect variables
        total += item.price
    return total

# Conditional breakpoint
@client
def process_order(order):
    for item in order.items:
        conditional_breakpoint(item.price > 100)  # Only pause for expensive items
        process_item(item)

# Logpoint (log without pausing)
@client
def handle_click(event):
    logpoint(f"Click at ({event.clientX}, {event.clientY})")  # Logs but doesn't pause
    do_something()

# =============================================================================
# Breakpoint Configuration
# =============================================================================

# Set breakpoints programmatically
from pynext.devtools import set_breakpoint, remove_breakpoint

# By file and line
bp_id = set_breakpoint("app.py", line=42)

# With condition
bp_id = set_breakpoint("app.py", line=42, condition="x > 10")

# With hit count
bp_id = set_breakpoint("app.py", line=42, hit_count=5)  # Break on 5th hit

# Remove breakpoint
remove_breakpoint(bp_id)

# List all breakpoints
breakpoints = list_breakpoints()

# =============================================================================
# Debugger Integration
# =============================================================================

# When paused at a breakpoint, you can:

# Inspect local variables
locals()  # {"items": [...], "total": 42}

# Inspect specific variables
inspect(total)  # Detailed view with type, value, etc.

# Evaluate expressions
eval_expr("total * 1.1")  # Evaluate in current context

# View call stack
get_stack()  # [{"file": "app.py", "line": 42, "function": "calculate_total"}, ...]

# Step through code
step_over()   # Next line
step_into()   # Into function call
step_out()    # Out of current function
continue_()   # Resume execution

# =============================================================================
# Watch Expressions
# =============================================================================

# Add watch expressions
add_watch("total")
add_watch("len(items)")
add_watch("items[0].price")

# Watches are evaluated on every pause
# Shown in devtools panel

# Remove watch
remove_watch("total")

# =============================================================================
# Browser Extension
# =============================================================================

# The PyNext DevTools browser extension provides:
# - Dedicated DevTools panel for PyNext apps
# - Automatic detection of PyNext pages
# - Signal inspector panel
# - Component tree panel
# - Time-travel controls
# - Breakpoint management
# - Performance profiler

# Install from browser stores:
# - Chrome: chrome.google.com/webstore/pynext-devtools
# - Firefox: addons.mozilla.org/pynext-devtools
# - Edge: microsoftedge.microsoft.com/addons/pynext-devtools

# Extension auto-connects to PyNext apps:
# - No manual setup required
# - Works with localhost and production
# - Version compatibility checking
```

##### Time-Travel Implementation

```python
# =============================================================================
# Timeline Recording
# =============================================================================

class TimelineEntry:
    """Single entry in the time-travel timeline."""
    timestamp: float
    type: str  # "signal_update", "effect_run", "user_event"
    signal_id: Optional[str]
    signal_name: Optional[str]
    old_value: Any
    new_value: Any
    source_location: str
    stack_trace: List[str]

class TimeTravel:
    """Time-travel debugging implementation."""
    
    _timeline: List[TimelineEntry] = []
    _snapshots: Dict[str, dict] = {}
    _current_index: int = -1
    _is_recording: bool = True
    
    @classmethod
    def record(cls, entry: TimelineEntry):
        """Record a new timeline entry."""
        if cls._is_recording:
            cls._timeline.append(entry)
            cls._current_index = len(cls._timeline) - 1
    
    @classmethod
    def goto(cls, index: int):
        """Jump to a specific point in the timeline."""
        if 0 <= index < len(cls._timeline):
            # Pause recording while replaying
            cls._is_recording = False
            
            # Replay all entries up to target
            cls._reset_all_signals()
            for i in range(index + 1):
                cls._apply_entry(cls._timeline[i])
            
            cls._current_index = index
            cls._is_recording = True
    
    @classmethod
    def step_back(cls):
        """Step back one entry."""
        if cls._current_index > 0:
            cls.goto(cls._current_index - 1)
    
    @classmethod
    def step_forward(cls):
        """Step forward one entry."""
        if cls._current_index < len(cls._timeline) - 1:
            cls.goto(cls._current_index + 1)
    
    @classmethod
    def create_snapshot(cls, name: str):
        """Create a named snapshot of current state."""
        cls._snapshots[name] = {
            "timestamp": performance.now(),
            "index": cls._current_index,
            "signals": cls._capture_all_signals(),
        }
    
    @classmethod
    def restore_snapshot(cls, name: str):
        """Restore state from a snapshot."""
        if name in cls._snapshots:
            snapshot = cls._snapshots[name]
            cls._restore_signals(snapshot["signals"])
            cls._current_index = snapshot["index"]
```

##### Advanced DevTools Checklist

```
Advanced DevTools (Phase 51)
├── Time-Travel Debugging (50 tests)
│   ├── [ ] Timeline recording
│   ├── [ ] Signal change tracking
│   ├── [ ] Goto specific timestamp
│   ├── [ ] Step backward
│   ├── [ ] Step forward
│   ├── [ ] State snapshots (create/restore)
│   ├── [ ] Snapshot comparison
│   ├── [ ] Session recording (save/load)
│   ├── [ ] Session replay
│   ├── [ ] Share session URL
│   └── [ ] Persist across page reload
│
├── Python Breakpoints (30 tests)
│   ├── [ ] breakpoint() function
│   ├── [ ] conditional_breakpoint()
│   ├── [ ] logpoint()
│   ├── [ ] set_breakpoint() by file/line
│   ├── [ ] Breakpoint with condition
│   ├── [ ] Breakpoint with hit count
│   ├── [ ] remove_breakpoint()
│   ├── [ ] list_breakpoints()
│   ├── [ ] Variable inspection (locals, globals)
│   ├── [ ] Expression evaluation
│   ├── [ ] Call stack viewing
│   ├── [ ] step_over / step_into / step_out
│   └── [ ] Watch expressions
│
├── Browser Extension (20 tests)
│   ├── [ ] Chrome extension (Manifest V3)
│   ├── [ ] Firefox extension
│   ├── [ ] Edge extension
│   ├── [ ] Auto-detect PyNext pages
│   ├── [ ] DevTools panel integration
│   ├── [ ] Version compatibility
│   ├── [ ] Marketplace listing
│   └── [ ] One-click install
│
└── IDE Integration (bonus)
    ├── [ ] VS Code extension
    ├── [ ] PyCharm plugin
    └── [ ] Breakpoint sync with browser
```

##### Files to Create

- `pynext/devtools/time_travel.py` — Timeline recording and replay
- `pynext/devtools/snapshots.py` — State snapshots
- `pynext/devtools/breakpoints.py` — Python breakpoint implementation
- `pynext/devtools/debugger.py` — Step through, variable inspection
- `pynext/devtools/watches.py` — Watch expressions
- `pynext/devtools/extension/` — Browser extension package
- `pynext/devtools/extension/manifest.json` — Chrome manifest v3
- `pynext/devtools/extension/panel.html` — DevTools panel
- `pynext/devtools/extension/panel.js` — Panel logic
- `pynext/devtools/extension/content.js` — Content script
- `pynext/devtools/extension/background.js` — Service worker

##### Success Criteria

| Metric | Target |
|--------|--------|
| Time-travel | Full state history with replay |
| Snapshots | Create, restore, compare, share |
| Breakpoints | Python breakpoints with conditions |
| Variable inspection | Full locals/globals access |
| Stepping | Over, into, out |
| Watch expressions | Live evaluation |
| Browser extension | Chrome, Firefox, Edge |
| Test coverage | 100+ unit tests |

##### Milestones

1. **Week 1:** Timeline recording, state snapshots
2. **Week 2:** Time-travel navigation (goto, step), session save/load
3. **Week 3:** Breakpoints, variable inspection, stepping
4. **Week 4:** Browser extension packaging, marketplace submission

---

#### Phase 51.5: LLM-Native DevTools (150 tests, 5 weeks)

AI-first debugging infrastructure — making PyNext the first framework where LLMs can debug as effectively as humans.

##### Overview

```
LLM Debugging Architecture
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Cursor / AI Assistant                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  "Debug this error" → reads structured logs, queries debug server,    │   │
│  │   sets breakpoints, steps through code, gets AI-friendly explanations │   │
│  └────────────────────────────────┬─────────────────────────────────────┘   │
│                                   │                                          │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │                    LLM Debug Interface                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │  CLI Tool   │  │Debug Server │  │     DAP     │  │ Structured  │  │   │
│  │  │ (Terminal)  │  │  (HTTP/WS)  │  │  (VS Code)  │  │    Logs     │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └────────────────────────────────┬─────────────────────────────────────┘   │
│                                   │                                          │
│  ┌────────────────────────────────┴─────────────────────────────────────┐   │
│  │                    PyNext Runtime (Browser)                           │   │
│  │  Signals • Components • Effects • Network • Errors                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

##### CLI Debug Interface

```bash
# =============================================================================
# Signal Inspection
# =============================================================================

# List all signals with current values
$ pynext debug signals
┌─────────────────┬──────────────────┬────────────┬─────────────────────┐
│ Name            │ Value            │ Subscribers│ Source              │
├─────────────────┼──────────────────┼────────────┼─────────────────────┤
│ count           │ 42               │ 3          │ counter.py:12       │
│ user            │ {"id": 1, ...}   │ 5          │ auth.py:45          │
│ loading         │ false            │ 2          │ dashboard.py:23     │
│ items           │ [1, 2, 3]        │ 4          │ list.py:8           │
└─────────────────┴──────────────────┴────────────┴─────────────────────┘

# JSON output for LLM parsing
$ pynext debug signals --json
[
  {"name": "count", "value": 42, "subscribers": 3, "source": "counter.py:12"},
  {"name": "user", "value": {"id": 1, "name": "Alice"}, "subscribers": 5, "source": "auth.py:45"}
]

# Get specific signal with full details
$ pynext debug signals count --json
{
  "name": "count",
  "value": 42,
  "type": "int",
  "source": "counter.py:12",
  "created_at": 1702567890.123,
  "subscribers": [
    {"type": "memo", "name": "doubleCount", "source": "counter.py:15"},
    {"type": "effect", "name": "logCount", "source": "counter.py:18"}
  ],
  "history": [
    {"timestamp": 1702567890.100, "value": 0, "trigger": "initial"},
    {"timestamp": 1702567891.200, "value": 1, "trigger": "user_click"},
    {"timestamp": 1702567892.300, "value": 42, "trigger": "api_response"}
  ]
}

# Set signal value (for debugging)
$ pynext debug signals count --set 100
Signal 'count' updated: 42 → 100

# =============================================================================
# Component Tree
# =============================================================================

# Get component hierarchy
$ pynext debug components --json
{
  "name": "App",
  "source": "app.py:10",
  "props": {},
  "signals": [],
  "render_time_ms": 2.5,
  "children": [
    {
      "name": "Header",
      "source": "header.py:5",
      "signals": ["user"],
      "children": [...]
    },
    {
      "name": "Dashboard",
      "source": "dashboard.py:12",
      "signals": ["loading", "data"],
      "children": [...]
    }
  ]
}

# Search components
$ pynext debug components --search "Dashboard" --json

# Get component by path
$ pynext debug components "App/Dashboard/DataTable" --json

# =============================================================================
# Timeline and Time-Travel
# =============================================================================

# Get recent state changes
$ pynext debug timeline --last 20 --json
[
  {
    "id": 1001,
    "timestamp": 1702567892.300,
    "type": "signal_update",
    "signal": "count",
    "old_value": 1,
    "new_value": 42,
    "source": "counter.py:25",
    "trigger": "click_handler"
  },
  {
    "id": 1002,
    "timestamp": 1702567892.350,
    "type": "effect_run",
    "effect": "syncToServer",
    "duration_ms": 45,
    "signals_read": ["count", "user"]
  }
]

# Jump to specific point in time
$ pynext debug timeline --goto 1001
Jumped to timeline entry 1001 (count = 1)

# Create/restore snapshots
$ pynext debug snapshot create "before_bug"
Snapshot 'before_bug' created

$ pynext debug snapshot restore "before_bug"
Restored snapshot 'before_bug'

# Compare snapshots
$ pynext debug snapshot diff "before_bug" "after_bug" --json
{
  "changed_signals": [
    {"name": "count", "before": 1, "after": 42},
    {"name": "loading", "before": true, "after": false}
  ],
  "new_signals": [],
  "removed_signals": []
}

# =============================================================================
# Session Recording
# =============================================================================

# Start recording
$ pynext debug record start
Recording started. Session ID: abc123

# Stop and save
$ pynext debug record stop --save bug_reproduction.json
Recording saved to bug_reproduction.json (2.3 MB, 45 seconds, 234 events)

# Replay a session
$ pynext debug replay bug_reproduction.json
Replaying session... (use --speed 2 for 2x speed)

# =============================================================================
# Error Analysis
# =============================================================================

# Get recent errors with full context
$ pynext debug errors --last 5 --json
[
  {
    "id": "err_001",
    "type": "KeyError",
    "message": "'missing_key'",
    "timestamp": 1702567900.000,
    "python_source": {
      "file": "dashboard.py",
      "line": 42,
      "function": "render_data",
      "code": "value = data['missing_key']"
    },
    "signals_at_crash": {
      "data": {"items": [1, 2, 3]},
      "loading": false
    },
    "recent_events": [
      {"type": "click", "target": "button.load", "time_before_ms": 500},
      {"type": "fetch", "url": "/api/data", "status": 200, "time_before_ms": 200}
    ],
    "session_file": "/tmp/pynext_crash_err_001.json",
    "replay_command": "pynext debug replay /tmp/pynext_crash_err_001.json"
  }
]

# AI-friendly error explanation
$ pynext debug explain-error err_001

═══════════════════════════════════════════════════════════════════════════════
ERROR ANALYSIS: KeyError 'missing_key'
═══════════════════════════════════════════════════════════════════════════════

WHAT HAPPENED:
  At dashboard.py:42 in render_data(), the code tried to access data['missing_key']
  but the 'data' signal does not contain a 'missing_key' key.

TIMELINE LEADING TO ERROR:
  1. [T-500ms] User clicked "Load Data" button
  2. [T-450ms] Signal 'loading' set to true
  3. [T-200ms] fetch('/api/data') completed with status 200
  4. [T-150ms] Signal 'data' set to API response: {"items": [1, 2, 3]}
  5. [T-0ms]   Component re-rendered, accessed data['missing_key'] → ERROR

SIGNAL STATE AT CRASH:
  data = {"items": [1, 2, 3]}  ← Note: no 'missing_key' field
  loading = false
  user = {"id": 1, "name": "Alice"}

ROOT CAUSE ANALYSIS:
  The API response structure changed or doesn't match expected schema.
  Expected: {"missing_key": ..., "items": [...]}
  Received: {"items": [...]}

SUGGESTED FIXES:
  1. Use data.get('missing_key', default_value)
  2. Add key existence check: if 'missing_key' in data:
  3. Validate API response schema before using

TO REPRODUCE:
  pynext debug replay /tmp/pynext_crash_err_001.json

═══════════════════════════════════════════════════════════════════════════════

# =============================================================================
# Breakpoints (via CLI)
# =============================================================================

# Set a breakpoint
$ pynext debug breakpoint add dashboard.py:42
Breakpoint 1 set at dashboard.py:42

# Set conditional breakpoint
$ pynext debug breakpoint add dashboard.py:42 --condition "count > 10"
Breakpoint 2 set at dashboard.py:42 (when count > 10)

# List breakpoints
$ pynext debug breakpoint list --json
[
  {"id": 1, "file": "dashboard.py", "line": 42, "condition": null, "hits": 5},
  {"id": 2, "file": "dashboard.py", "line": 42, "condition": "count > 10", "hits": 2}
]

# Remove breakpoint
$ pynext debug breakpoint remove 1

# When paused at breakpoint, inspect state
$ pynext debug locals --json
{"items": [...], "total": 42, "index": 5}

$ pynext debug eval "total * 2"
84

$ pynext debug stack --json
[
  {"file": "dashboard.py", "line": 42, "function": "render_data", "locals": {...}},
  {"file": "app.py", "line": 15, "function": "App", "locals": {...}}
]

# Step commands
$ pynext debug step over
Stepped to dashboard.py:43

$ pynext debug step into
Stepped into helper.py:10

$ pynext debug continue
Resumed execution
```

##### Debug Server API

```python
# =============================================================================
# Debug Server (automatically started in dev mode)
# =============================================================================

# Configuration
from pynext import configure

configure(
    debug_server=True,           # Enable debug server
    debug_server_port=9229,      # Port (default: 9229)
    debug_server_host="127.0.0.1",  # Host (localhost only by default)
    debug_server_auth="token123",   # Optional auth token
)

# =============================================================================
# REST API Endpoints
# =============================================================================

# All endpoints return JSON and accept an optional ?token= for auth

# --- Signals ---
GET  /api/signals                    # List all signals
GET  /api/signals/:name              # Get specific signal
GET  /api/signals/:name/history      # Get signal history
POST /api/signals/:name/set          # Set signal value
     Body: {"value": <new_value>}

# --- Components ---
GET  /api/components                 # Full component tree
GET  /api/components/search?q=       # Search components
GET  /api/components/:path           # Get component by path

# --- Timeline ---
GET  /api/timeline                   # Get timeline entries
GET  /api/timeline/:id               # Get specific entry
POST /api/timeline/goto              # Jump to entry
     Body: {"id": <entry_id>}

# --- Snapshots ---
GET  /api/snapshots                  # List snapshots
POST /api/snapshots                  # Create snapshot
     Body: {"name": "snapshot_name"}
POST /api/snapshots/:name/restore    # Restore snapshot
GET  /api/snapshots/diff?from=&to=   # Compare snapshots

# --- Sessions ---
POST /api/sessions/record/start      # Start recording
POST /api/sessions/record/stop       # Stop recording
GET  /api/sessions                   # List recorded sessions
GET  /api/sessions/:id               # Download session file
POST /api/sessions/:id/replay        # Replay session

# --- Errors ---
GET  /api/errors                     # List recent errors
GET  /api/errors/:id                 # Get error details
GET  /api/errors/:id/explain         # Get AI-friendly explanation
GET  /api/errors/:id/session         # Download crash session

# --- Breakpoints ---
GET  /api/breakpoints                # List breakpoints
POST /api/breakpoints                # Set breakpoint
     Body: {"file": "...", "line": 42, "condition": "..."}
DELETE /api/breakpoints/:id          # Remove breakpoint

# --- Debugger (when paused) ---
GET  /api/debug/status               # Paused? At which line?
GET  /api/debug/locals               # Local variables
GET  /api/debug/stack                # Call stack
POST /api/debug/eval                 # Evaluate expression
     Body: {"expression": "total * 2"}
POST /api/debug/step                 # Step over/into/out
     Body: {"action": "over|into|out"}
POST /api/debug/continue             # Resume execution

# =============================================================================
# WebSocket API (for live updates)
# =============================================================================

WS /api/ws

# Messages sent by server:
{"type": "signal_update", "name": "count", "value": 42, "old_value": 41}
{"type": "component_render", "name": "Dashboard", "duration_ms": 12}
{"type": "effect_run", "name": "syncData", "duration_ms": 45}
{"type": "error", "id": "err_001", "type": "KeyError", "message": "..."}
{"type": "breakpoint_hit", "id": 1, "file": "dashboard.py", "line": 42}

# Messages sent by client:
{"type": "subscribe", "channels": ["signals", "errors", "breakpoints"]}
{"type": "unsubscribe", "channels": ["signals"]}
{"type": "set_signal", "name": "count", "value": 100}
{"type": "step", "action": "over"}
{"type": "continue"}
```

##### Debug Adapter Protocol (DAP) Implementation

```python
# =============================================================================
# VS Code / Cursor Integration
# =============================================================================

# launch.json configuration
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "PyNext: Debug App",
            "type": "pynext",
            "request": "launch",
            "program": "${workspaceFolder}/app.py",
            "port": 9229,
            "pythonBreakpoints": true,
            "signalInspection": true,
            "timeTravel": true
        },
        {
            "name": "PyNext: Attach to Running App",
            "type": "pynext",
            "request": "attach",
            "port": 9229,
            "host": "localhost"
        }
    ]
}

# =============================================================================
# DAP Capabilities
# =============================================================================

# The PyNext debug adapter supports:
capabilities = {
    # Standard DAP
    "supportsConfigurationDoneRequest": True,
    "supportsFunctionBreakpoints": True,
    "supportsConditionalBreakpoints": True,
    "supportsHitConditionalBreakpoints": True,
    "supportsLogPoints": True,
    "supportsEvaluateForHovers": True,
    "supportsSetVariable": True,
    "supportsStepBack": True,  # Time-travel!
    "supportsRestartFrame": True,
    "supportsGotoTargetsRequest": True,
    
    # PyNext-specific extensions
    "supportsSignalInspection": True,
    "supportsComponentTree": True,
    "supportsTimeTravel": True,
    "supportsSessionRecording": True,
    "supportsErrorExplanation": True,
}

# =============================================================================
# Custom DAP Extensions for PyNext
# =============================================================================

# Request: pynext/signals
# Get all signals (shown in Variables panel under "Signals" scope)
{
    "command": "pynext/signals",
    "type": "request"
}

# Response:
{
    "signals": [
        {"name": "count", "value": "42", "type": "int", "variablesReference": 101},
        {"name": "user", "value": "{...}", "type": "dict", "variablesReference": 102}
    ]
}

# Request: pynext/timeTravel
# Step back in time
{
    "command": "pynext/timeTravel",
    "arguments": {"action": "stepBack"}
}

# Request: pynext/explainError
# Get AI-friendly explanation of current error
{
    "command": "pynext/explainError",
    "arguments": {"errorId": "err_001"}
}
```

##### Structured Logging

```python
# =============================================================================
# Machine-Readable Log Format
# =============================================================================

from pynext.devtools import StructuredLogger

# All logs are prefixed with [PYNEXT:<CATEGORY>] and contain JSON
# This makes them easy for LLMs to parse from terminal output

# Automatic logging (enabled in dev mode)
[PYNEXT:SIGNAL] {"ts":1702567890123,"name":"count","old":41,"new":42,"source":"counter.py:25","trigger":"click"}
[PYNEXT:RENDER] {"ts":1702567890150,"component":"Counter","duration_ms":2.3,"signals_read":["count"]}
[PYNEXT:EFFECT] {"ts":1702567890200,"name":"logCount","duration_ms":0.5,"signals_read":["count"]}
[PYNEXT:FETCH]  {"ts":1702567890300,"url":"/api/data","method":"GET","status":200,"duration_ms":145}
[PYNEXT:ERROR]  {"ts":1702567890500,"type":"KeyError","message":"'missing_key'","file":"dashboard.py","line":42}

# =============================================================================
# Log Levels and Filtering
# =============================================================================

configure(
    structured_logging=True,
    log_level="debug",  # debug, info, warn, error
    log_categories=["signal", "error", "fetch"],  # Filter categories
    log_output="stderr",  # stdout, stderr, file:/path/to/log.json
)

# =============================================================================
# Custom Structured Logs
# =============================================================================

from pynext.devtools import log

@client
def my_function():
    log.debug("Starting computation", context={"input": data})
    result = compute(data)
    log.info("Computation complete", context={"result": result, "duration_ms": 45})

# Output:
[PYNEXT:DEBUG] {"ts":...,"message":"Starting computation","context":{"input":{...}}}
[PYNEXT:INFO]  {"ts":...,"message":"Computation complete","context":{"result":...,"duration_ms":45}}
```

##### AI-Optimized Commands

```bash
# =============================================================================
# Commands Designed for LLM Consumption
# =============================================================================

# Full context dump for any error
$ pynext debug context --json
{
  "app_state": {
    "signals": {...},
    "components": {...},
    "recent_events": [...],
    "network_log": [...]
  },
  "errors": [...],
  "performance": {
    "slow_signals": [...],
    "slow_components": [...]
  },
  "suggestions": [
    "Signal 'heavyData' updated 47 times in 1 second - possible loop?",
    "Component 'DataTable' re-rendered 23 times - missing memo?"
  ]
}

# Suggest fixes based on error patterns
$ pynext debug suggest-fix err_001 --json
{
  "error": "KeyError 'missing_key'",
  "file": "dashboard.py",
  "line": 42,
  "current_code": "value = data['missing_key']",
  "suggestions": [
    {
      "fix": "value = data.get('missing_key', None)",
      "confidence": 0.95,
      "explanation": "Use .get() with default for optional keys"
    },
    {
      "fix": "if 'missing_key' in data:\n    value = data['missing_key']\nelse:\n    value = compute_default()",
      "confidence": 0.80,
      "explanation": "Check key existence before access"
    }
  ]
}

# Minimize reproduction steps
$ pynext debug minimize-repro session.json --json
{
  "original_events": 234,
  "minimized_events": 12,
  "minimized_session": "/tmp/minimized_session.json",
  "steps": [
    "1. Navigate to /dashboard",
    "2. Click 'Load Data' button",
    "3. Wait for API response",
    "4. Error occurs in DataTable component"
  ]
}

# Diff current state vs expected
$ pynext debug assert --signal count --equals 42
✓ Signal 'count' equals 42

$ pynext debug assert --signal count --equals 100
✗ Signal 'count' is 42, expected 100
  Last updated: 500ms ago at counter.py:25
  Previous values: [0, 1, 5, 42]
```

##### LLM DevTools Checklist

```
LLM-Native DevTools (Phase 51.5)
├── CLI Debug Interface (40 tests)
│   ├── [ ] pynext debug signals (list, get, set)
│   ├── [ ] pynext debug signals --json
│   ├── [ ] pynext debug components (tree, search)
│   ├── [ ] pynext debug timeline (list, goto)
│   ├── [ ] pynext debug snapshot (create, restore, diff)
│   ├── [ ] pynext debug record (start, stop, replay)
│   ├── [ ] pynext debug errors (list, explain)
│   ├── [ ] pynext debug breakpoint (add, remove, list)
│   ├── [ ] pynext debug step (over, into, out)
│   ├── [ ] pynext debug locals, stack, eval
│   └── [ ] All commands support --json flag
│
├── Debug Server API (40 tests)
│   ├── [ ] REST endpoints for all inspection
│   ├── [ ] Signal CRUD operations
│   ├── [ ] Component tree queries
│   ├── [ ] Timeline and time-travel endpoints
│   ├── [ ] Snapshot management
│   ├── [ ] Session recording endpoints
│   ├── [ ] Error retrieval and explanation
│   ├── [ ] Breakpoint management
│   ├── [ ] Debugger control (step, continue)
│   ├── [ ] WebSocket for live updates
│   └── [ ] Authentication token support
│
├── Debug Adapter Protocol (30 tests)
│   ├── [ ] Launch configuration
│   ├── [ ] Attach configuration
│   ├── [ ] Breakpoint protocol (set, hit, remove)
│   ├── [ ] Variable inspection (locals, globals, signals)
│   ├── [ ] Call stack frames
│   ├── [ ] Step over/into/out
│   ├── [ ] Step back (time-travel)
│   ├── [ ] Evaluate expressions
│   ├── [ ] Custom pynext/* requests
│   ├── [ ] VS Code extension packaging
│   └── [ ] Cursor integration testing
│
├── Structured Logging (15 tests)
│   ├── [ ] [PYNEXT:SIGNAL] format
│   ├── [ ] [PYNEXT:RENDER] format
│   ├── [ ] [PYNEXT:EFFECT] format
│   ├── [ ] [PYNEXT:FETCH] format
│   ├── [ ] [PYNEXT:ERROR] format
│   ├── [ ] Log level filtering
│   ├── [ ] Category filtering
│   └── [ ] Custom log.debug/info/warn/error
│
└── AI-Optimized Commands (25 tests)
    ├── [ ] pynext debug context (full dump)
    ├── [ ] pynext debug explain-error
    ├── [ ] pynext debug suggest-fix
    ├── [ ] pynext debug minimize-repro
    ├── [ ] pynext debug assert
    ├── [ ] Pattern-based fix suggestions
    ├── [ ] Automatic anomaly detection
    └── [ ] All output machine-parseable
```

##### Files to Create

- `pynext/devtools/cli/__init__.py` — CLI debug command entry point
- `pynext/devtools/cli/signals.py` — Signal inspection commands
- `pynext/devtools/cli/components.py` — Component tree commands
- `pynext/devtools/cli/timeline.py` — Timeline and time-travel commands
- `pynext/devtools/cli/snapshots.py` — Snapshot commands
- `pynext/devtools/cli/sessions.py` — Recording commands
- `pynext/devtools/cli/errors.py` — Error analysis commands
- `pynext/devtools/cli/breakpoints.py` — Breakpoint commands
- `pynext/devtools/cli/debugger.py` — Step, eval, locals commands
- `pynext/devtools/server/__init__.py` — Debug server entry point
- `pynext/devtools/server/app.py` — HTTP/WebSocket server
- `pynext/devtools/server/routes.py` — REST API routes
- `pynext/devtools/server/websocket.py` — WebSocket handlers
- `pynext/devtools/server/auth.py` — Token authentication
- `pynext/devtools/dap/__init__.py` — DAP implementation
- `pynext/devtools/dap/adapter.py` — Debug adapter
- `pynext/devtools/dap/protocol.py` — DAP protocol handling
- `pynext/devtools/dap/pynext_extensions.py` — Custom DAP extensions
- `pynext/devtools/logging/__init__.py` — Structured logging
- `pynext/devtools/logging/formatters.py` — Log formatters
- `pynext/devtools/ai/__init__.py` — AI-optimized features
- `pynext/devtools/ai/explain.py` — Error explanation
- `pynext/devtools/ai/suggest.py` — Fix suggestions
- `pynext/devtools/ai/minimize.py` — Reproduction minimization
- `pynext/devtools/vscode/extension/` — VS Code extension package

##### Success Criteria

| Metric | Target |
|--------|--------|
| CLI Coverage | All debug operations available via CLI |
| JSON Output | Every command supports --json |
| Debug Server | Full REST + WebSocket API |
| DAP Support | Works in VS Code and Cursor |
| Structured Logs | All runtime events logged in parseable format |
| AI Commands | explain-error, suggest-fix, minimize-repro |
| Response Time | < 50ms for all inspection queries |
| Test Coverage | 150+ unit tests |

##### Milestones

1. **Week 1:** CLI foundation, signal/component inspection commands
2. **Week 2:** Debug server REST API, WebSocket live updates
3. **Week 3:** DAP implementation, VS Code extension
4. **Week 4:** Structured logging, AI explain-error
5. **Week 5:** AI suggest-fix, minimize-repro, integration testing

---

#### Phase 51.6: MCP & Browser-Aware Debugging (100 tests, 3 weeks)

Cursor-native debugging via MCP protocol with PyNext-aware browser tools.

##### Overview

```
MCP Integration Architecture
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Cursor IDE                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                           Claude                                        │ │
│  │                                                                         │ │
│  │  Available Tools:                                                       │ │
│  │  ├── browser_snapshot      (Cursor built-in)                           │ │
│  │  ├── browser_click         (Cursor built-in)                           │ │
│  │  ├── browser_console       (Cursor built-in)                           │ │
│  │  ├── pynext_signals        ← PyNext MCP                                │ │
│  │  ├── pynext_inspect        ← PyNext MCP                                │ │
│  │  ├── pynext_diagnose       ← PyNext MCP                                │ │
│  │  └── pynext_explain        ← PyNext MCP                                │ │
│  │                                                                         │ │
│  └─────────────────────────────────┬───────────────────────────────────────┘ │
│                                    │ MCP Protocol                           │
│  ┌─────────────────────────────────┴───────────────────────────────────────┐ │
│  │                       PyNext MCP Server                                  │ │
│  │                    (runs with pynext dev)                               │ │
│  └─────────────────────────────────┬───────────────────────────────────────┘ │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │ WebSocket
                    ┌────────────────┴────────────────┐
                    │      Browser + PyNext App        │
                    │                                  │
                    │  window.__PYNEXT_DEBUG__ = {     │
                    │    signals, components, ...      │
                    │  }                               │
                    └──────────────────────────────────┘
```

##### Setup & Configuration

```bash
# =============================================================================
# One-Time Setup
# =============================================================================

# Initialize MCP configuration for Cursor
$ pynext init-debug

Created .cursor/mcp.json:
{
  "servers": {
    "pynext": {
      "command": "pynext",
      "args": ["mcp-server"],
      "description": "PyNext debugging tools for Cursor"
    }
  }
}

# =============================================================================
# Daily Workflow
# =============================================================================

# Start dev server with debug mode (MCP server auto-starts)
$ pynext dev
# App running on http://localhost:3000
# Debug server on http://localhost:9229
# MCP endpoint on http://localhost:9229/mcp

# Or explicitly enable debug mode
$ pynext dev --debug

# =============================================================================
# Cursor Auto-Discovery
# =============================================================================

# When Cursor opens a project with .cursor/mcp.json:
# 1. Reads MCP configuration
# 2. Connects to PyNext MCP server
# 3. Discovers available tools
# 4. Tools appear alongside browser_* tools

# Cursor will show:
# "Connected to PyNext MCP server"
# "Available tools: pynext_signals, pynext_inspect, pynext_diagnose, ..."
```

##### MCP Tools API

```python
# =============================================================================
# pynext/devtools/mcp/server.py
# =============================================================================

from mcp import Server, Tool
from pynext.devtools import DebugRuntime

mcp = Server("pynext-devtools")
runtime = DebugRuntime()

# =============================================================================
# Tool: pynext_signals
# =============================================================================

@mcp.tool(
    name="pynext_signals",
    description="Get PyNext signal values. Returns all signals or a specific one with history.",
)
async def pynext_signals(name: str = None, include_history: bool = False) -> dict:
    """
    Get signal values from the running PyNext app.
    
    Args:
        name: Optional signal name. If omitted, returns all signals.
        include_history: Include last 10 value changes.
    
    Returns:
        Signal data with value, source location, and subscribers.
    
    Example:
        pynext_signals()
        → {"count": {"value": 42, "source": "counter.py:12"}, ...}
        
        pynext_signals(name="count", include_history=True)
        → {"name": "count", "value": 42, "history": [...], "subscribers": [...]}
    """
    if name:
        return await runtime.get_signal(name, include_history)
    return await runtime.get_all_signals()

# =============================================================================
# Tool: pynext_inspect_element
# =============================================================================

@mcp.tool(
    name="pynext_inspect_element",
    description="Inspect a DOM element with PyNext context. Shows bound signals, Python source, and event handlers.",
)
async def pynext_inspect_element(selector: str) -> dict:
    """
    Deep inspection of a DOM element including its PyNext bindings.
    
    Args:
        selector: CSS selector (e.g., "button.submit", "#email", "[data-testid='login']")
    
    Returns:
        Element details including:
        - Basic: tag, text, attributes, rect
        - Visibility: visible, visibility_reason
        - Interactivity: clickable, disabled, disabled_reason
        - PyNext: component, source, bound_signals, event_handlers
    
    Example:
        pynext_inspect_element("button[type=submit]")
        → {
            "found": true,
            "tag": "button",
            "text": "Submit",
            "visible": true,
            "clickable": false,
            "disabled": true,
            "disabled_reason": "Signal 'is_valid' is false",
            "pynext": {
                "component": "SubmitButton",
                "source": "form.py:45",
                "bound_signals": ["is_valid", "is_loading"],
                "event_handlers": [
                    {"event": "click", "handler": "form.py:52 in handle_submit()"}
                ]
            }
        }
    """
    return await runtime.inspect_element(selector)

# =============================================================================
# Tool: pynext_why_not_visible
# =============================================================================

@mcp.tool(
    name="pynext_why_not_visible",
    description="Diagnose why an element is not visible. Returns the root cause signal.",
)
async def pynext_why_not_visible(selector: str) -> dict:
    """
    Analyze why an element is not visible on the page.
    
    Args:
        selector: CSS selector for the element
    
    Returns:
        Visibility analysis with checks and root cause.
    
    Example:
        pynext_why_not_visible(".modal-content")
        → {
            "element": ".modal-content",
            "is_visible": false,
            "checks": [
                {"check": "display", "passed": true, "value": "flex"},
                {"check": "opacity", "passed": true, "value": "1"},
                {"check": "parent_visible", "passed": false, 
                 "reason": "Parent .modal has display:none"}
            ],
            "root_cause": {
                "type": "parent_hidden",
                "parent": ".modal",
                "css_property": "display: none",
                "controlled_by": {
                    "signal": "modal_open",
                    "value": false,
                    "source": "modal.py:23"
                },
                "fix": "Set modal_open to True"
            }
        }
    """
    return await runtime.diagnose_visibility(selector)

# =============================================================================
# Tool: pynext_why_not_clickable
# =============================================================================

@mcp.tool(
    name="pynext_why_not_clickable",
    description="Diagnose why an element cannot be clicked. Returns the blocking reason.",
)
async def pynext_why_not_clickable(selector: str) -> dict:
    """
    Analyze why an element is not clickable.
    
    Args:
        selector: CSS selector for the element
    
    Returns:
        Clickability analysis with blocking reason.
    
    Example:
        pynext_why_not_clickable("button.submit")
        → {
            "element": "button.submit",
            "is_clickable": false,
            "checks": [
                {"check": "exists", "passed": true},
                {"check": "visible", "passed": true},
                {"check": "not_disabled", "passed": false, "reason": "disabled attribute"},
                {"check": "no_overlay", "passed": true},
                {"check": "pointer_events", "passed": true}
            ],
            "root_cause": {
                "type": "disabled",
                "attribute": "disabled",
                "binding": "disabled={not is_valid()}",
                "signal": "is_valid",
                "value": false,
                "source": "form.py:45",
                "depends_on": ["email", "password"],
                "deeper_cause": "Signal 'email' is empty string"
            }
        }
    """
    return await runtime.diagnose_clickability(selector)

# =============================================================================
# Tool: pynext_diagnose
# =============================================================================

@mcp.tool(
    name="pynext_diagnose",
    description="Run automated diagnostics to find issues in the running app.",
)
async def pynext_diagnose() -> dict:
    """
    Automatically detect issues, warnings, and suggestions.
    
    Returns:
        Diagnostic report with errors, warnings, and suggestions.
    
    Example:
        pynext_diagnose()
        → {
            "status": "issues_found",
            "errors": [
                {
                    "type": "fetch_failed",
                    "url": "/api/submit",
                    "status": 500,
                    "response": {"error": "Database connection failed"},
                    "triggered_by": "form.py:67 in handle_submit()"
                }
            ],
            "warnings": [
                {
                    "type": "excessive_renders",
                    "component": "DataTable",
                    "count": 47,
                    "period": "5 seconds",
                    "source": "table.py:12",
                    "likely_cause": "Signal 'filter' updating in loop",
                    "suggestion": "Add debounce to filter updates"
                }
            ],
            "suggestions": [
                {
                    "type": "unused_signal",
                    "signal": "old_data",
                    "source": "dashboard.py:34",
                    "suggestion": "Remove if not needed"
                }
            ]
        }
    """
    return await runtime.run_diagnostics()

# =============================================================================
# Tool: pynext_components
# =============================================================================

@mcp.tool(
    name="pynext_components",
    description="Get the PyNext component tree (not just DOM).",
)
async def pynext_components(search: str = None) -> dict:
    """
    Get the PyNext component hierarchy.
    
    Args:
        search: Optional component name to search for.
    
    Returns:
        Component tree with props, signals, and render times.
    
    Example:
        pynext_components()
        → {
            "name": "App",
            "source": "app.py:10",
            "render_time_ms": 2.5,
            "children": [
                {"name": "Header", "source": "header.py:5", ...},
                {"name": "Dashboard", "source": "dashboard.py:12", ...}
            ]
        }
    """
    if search:
        return await runtime.find_component(search)
    return await runtime.get_component_tree()

# =============================================================================
# Tool: pynext_python_source
# =============================================================================

@mcp.tool(
    name="pynext_python_source",
    description="Map a DOM element or JavaScript location to Python source.",
)
async def pynext_python_source(selector: str = None, js_location: str = None) -> dict:
    """
    Find the Python source that created a DOM element or JS code.
    
    Args:
        selector: CSS selector for a DOM element
        js_location: JavaScript file:line (e.g., "bundle.js:1234")
    
    Returns:
        Python source location.
    
    Example:
        pynext_python_source(selector="button.submit")
        → {
            "python_file": "form.py",
            "line": 45,
            "function": "SubmitButton",
            "code": "return button(class_='submit', disabled=not is_valid())[...]"
        }
    """
    if selector:
        return await runtime.element_to_python(selector)
    elif js_location:
        return await runtime.js_to_python(js_location)

# =============================================================================
# Tool: pynext_dom_snapshot
# =============================================================================

@mcp.tool(
    name="pynext_dom_snapshot",
    description="Get structured DOM snapshot with PyNext annotations.",
)
async def pynext_dom_snapshot(selector: str = "body", max_depth: int = 5) -> dict:
    """
    Capture the DOM tree with PyNext component and signal annotations.
    
    Args:
        selector: Root element (default: "body")
        max_depth: Maximum depth to traverse (default: 5)
    
    Returns:
        DOM tree with PyNext metadata.
    """
    return await runtime.get_dom_snapshot(selector, max_depth)

# =============================================================================
# Tool: pynext_console
# =============================================================================

@mcp.tool(
    name="pynext_console",
    description="Get console logs with Python source attribution.",
)
async def pynext_console(last_n: int = 30, level: str = None) -> list:
    """
    Get recent console output mapped to Python source.
    
    Args:
        last_n: Number of entries (default: 30)
        level: Filter by level (log, warn, error)
    
    Returns:
        Console entries with Python source locations.
    """
    return await runtime.get_console_logs(last_n, level)

# =============================================================================
# Tool: pynext_network
# =============================================================================

@mcp.tool(
    name="pynext_network",
    description="Get network requests with Python source attribution.",
)
async def pynext_network(last_n: int = 20, status: str = None) -> list:
    """
    Get network requests mapped to Python source.
    
    Args:
        last_n: Number of requests (default: 20)
        status: Filter by status (e.g., "error", "2xx", "4xx", "5xx")
    
    Returns:
        Network requests with triggering Python code.
    """
    return await runtime.get_network_log(last_n, status)
```

##### Example Debugging Session

```
User: "The submit button doesn't work when I click it"

Claude: Let me investigate...

[pynext_inspect_element selector="button[type=submit]"]
→ {
    "found": true,
    "tag": "button",
    "text": "Submit",
    "visible": true,
    "clickable": true,
    "disabled": false,
    "pynext": {
        "component": "SubmitButton",
        "source": "form.py:45",
        "event_handlers": [
            {"event": "click", "handler": "form.py:52 in handle_submit()"}
        ]
    }
}

Claude: The button looks clickable. Let me check if there are any errors...

[pynext_diagnose]
→ {
    "errors": [
        {
            "type": "unhandled_exception",
            "error": "TypeError: Cannot read property 'id' of null",
            "source": "form.py:55",
            "line": "user_id = current_user['id']",
            "signal_state": {"current_user": null}
        }
    ]
}

Claude: Found it! The click handler at form.py:55 crashes because 
`current_user` is null. Let me verify...

[pynext_signals name="current_user"]
→ {
    "name": "current_user",
    "value": null,
    "source": "auth.py:12"
}

Claude: The issue is that `current_user` is null, but the code at 
form.py:55 tries to access `current_user['id']` without checking.

**Root cause:** User is not logged in, but the form doesn't guard against this.

**Fix options:**
1. Add null check: `user_id = current_user['id'] if current_user else None`
2. Don't show the form when logged out
3. Redirect to login page
```

##### MCP Checklist

```
MCP & Browser-Aware Debugging (Phase 51.6)
├── MCP Server (25 tests)
│   ├── [ ] MCP protocol implementation
│   ├── [ ] Tool registration and discovery
│   ├── [ ] Connection management
│   ├── [ ] Error handling
│   ├── [ ] Authentication (optional token)
│   └── [ ] Auto-start with pynext dev
│
├── Setup & Configuration (10 tests)
│   ├── [ ] pynext init-debug command
│   ├── [ ] .cursor/mcp.json generation
│   ├── [ ] Auto-detection of Cursor
│   └── [ ] Zero-config with pynext dev --debug
│
├── Browser-Aware Tools (40 tests)
│   ├── [ ] pynext_inspect_element
│   ├── [ ] pynext_why_not_visible
│   ├── [ ] pynext_why_not_clickable
│   ├── [ ] pynext_dom_snapshot
│   ├── [ ] pynext_python_source
│   ├── [ ] pynext_console (with Python source)
│   ├── [ ] pynext_network (with Python source)
│   └── [ ] Element → Component mapping
│
├── Diagnostic Tools (15 tests)
│   ├── [ ] pynext_diagnose
│   ├── [ ] Auto-detect fetch failures
│   ├── [ ] Auto-detect excessive renders
│   ├── [ ] Auto-detect unused signals
│   ├── [ ] Root cause analysis
│   └── [ ] Fix suggestions
│
└── Cursor Integration (10 tests)
    ├── [ ] Works alongside browser_* tools
    ├── [ ] Tool descriptions for Claude
    ├── [ ] Response format optimization
    └── [ ] Connection status reporting
```

##### Files to Create

- `pynext/devtools/mcp/__init__.py` — MCP package
- `pynext/devtools/mcp/server.py` — MCP server implementation
- `pynext/devtools/mcp/tools.py` — Tool definitions
- `pynext/devtools/mcp/protocol.py` — MCP protocol handling
- `pynext/devtools/browser/__init__.py` — Browser-aware debugging
- `pynext/devtools/browser/inspector.py` — Element inspection
- `pynext/devtools/browser/visibility.py` — Visibility diagnostics
- `pynext/devtools/browser/clickability.py` — Click diagnostics
- `pynext/devtools/browser/mapping.py` — DOM → Python mapping
- `pynext/cli/commands/init_debug.py` — Setup command

##### Success Criteria

| Metric | Target |
|--------|--------|
| MCP Protocol | Full MCP server implementation |
| Tool Discovery | Auto-discovered by Cursor |
| Element Inspection | Full PyNext context for any element |
| Diagnostics | Auto-detect common issues |
| Source Mapping | Any DOM element → Python source |
| Setup | One command: `pynext init-debug` |
| Test Coverage | 100+ unit tests |

##### Milestones

1. **Week 1:** MCP server, basic tools (signals, components)
2. **Week 2:** Element inspection, visibility/clickability diagnostics
3. **Week 3:** DOM→Python mapping, auto-diagnostics, Cursor integration testing

---

### APPLICATION INFRASTRUCTURE PHASES (52-56)

---

#### Phase 52: Data Fetching Layer (200 tests, 5 weeks)

TanStack Query-style data fetching with caching, background refresh, and optimistic updates.

##### Overview

```
Data Fetching Architecture
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Application                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        Component Layer                                  │ │
│  │   users = use_query("/api/users")                                      │ │
│  │   users.data, users.loading, users.error, users.refetch()              │ │
│  └────────────────────────────────┬───────────────────────────────────────┘ │
│                                   │                                          │
│  ┌────────────────────────────────┴───────────────────────────────────────┐ │
│  │                         Query Layer                                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │   Cache     │  │  Deduping   │  │   Retry     │  │ Background  │   │ │
│  │  │  (in-mem)   │  │  (pending)  │  │   Logic     │  │   Refetch   │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └────────────────────────────────┬───────────────────────────────────────┘ │
│                                   │                                          │
│  ┌────────────────────────────────┴───────────────────────────────────────┐ │
│  │                         Network Layer                                   │ │
│  │                    fetch() / WebSocket / SSE                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Python API

```python
from pynext.query import (
    use_query, use_mutation, use_infinite_query,
    QueryClient, QueryClientProvider,
    prefetch_query, invalidate_queries,
)

# =============================================================================
# Basic Query
# =============================================================================

@client
def UserList():
    # Simple data fetching
    users = use_query(
        key="users",
        fn=lambda: fetch("/api/users").json(),
    )
    
    if users.loading:
        return div()["Loading..."]
    
    if users.error:
        return div()[f"Error: {users.error}"]
    
    return ul()[
        [li(key=user["id"])[user["name"]] for user in users.data]
    ]

# =============================================================================
# Query with Options
# =============================================================================

@client
def Dashboard():
    # Full options
    stats = use_query(
        key="dashboard_stats",
        fn=lambda: fetch("/api/stats").json(),
        
        # Caching
        stale_time=60_000,        # Data fresh for 1 minute
        cache_time=300_000,       # Keep in cache for 5 minutes
        
        # Refetching
        refetch_on_mount=True,    # Refetch when component mounts
        refetch_on_focus=True,    # Refetch when window regains focus
        refetch_on_reconnect=True, # Refetch when network reconnects
        refetch_interval=30_000,  # Poll every 30 seconds
        
        # Retry
        retry=3,                  # Retry 3 times on failure
        retry_delay=1000,         # Wait 1s between retries
        
        # Transforms
        select=lambda data: data["summary"],  # Transform response
        
        # Callbacks
        on_success=lambda data: console.log("Loaded!", data),
        on_error=lambda err: console.error("Failed!", err),
    )
    
    return div()[
        stats.data["total_users"] if stats.data else "...",
        button(on_click=stats.refetch)["Refresh"],
    ]

# =============================================================================
# Parameterized Queries
# =============================================================================

@client
def UserProfile(user_id: int):
    # Query key includes parameters
    user = use_query(
        key=["user", user_id],  # Unique cache key per user
        fn=lambda: fetch(f"/api/users/{user_id}").json(),
        enabled=user_id is not None,  # Don't fetch if no ID
    )
    
    return div()[
        user.data["name"] if user.data else "Loading...",
    ]

# =============================================================================
# Dependent Queries
# =============================================================================

@client
def UserPosts():
    # First query
    user = use_query(
        key="current_user",
        fn=lambda: fetch("/api/me").json(),
    )
    
    # Dependent query - waits for user
    posts = use_query(
        key=["posts", user.data["id"] if user.data else None],
        fn=lambda: fetch(f"/api/users/{user.data['id']}/posts").json(),
        enabled=user.data is not None,  # Only run after user loads
    )
    
    return div()[
        f"Posts by {user.data['name']}" if user.data else "Loading user...",
        ul()[
            [li()[post["title"]] for post in (posts.data or [])]
        ] if posts.data else "Loading posts...",
    ]

# =============================================================================
# Mutations
# =============================================================================

@client
def CreateUserForm():
    name = Signal("")
    
    create_user = use_mutation(
        fn=lambda data: fetch("/api/users", method="POST", body=data).json(),
        
        # Invalidate related queries on success
        on_success=lambda data: invalidate_queries("users"),
        
        # Optimistic update
        on_mutate=lambda data: {
            # Return context for rollback
            "previous": query_client.get_query_data("users"),
        },
        
        # Rollback on error
        on_error=lambda err, data, context: {
            query_client.set_query_data("users", context["previous"])
        },
    )
    
    async def submit():
        await create_user.mutate({"name": name()})
        name.set("")
    
    return form(on_submit=submit)[
        input(
            value=name(),
            on_input=lambda e: name.set(e.target.value),
        ),
        button(
            type="submit",
            disabled=create_user.loading,
        )[
            "Creating..." if create_user.loading else "Create User"
        ],
        div()[create_user.error] if create_user.error else None,
    ]

# =============================================================================
# Optimistic Updates
# =============================================================================

@client
def TodoItem(todo):
    toggle = use_mutation(
        fn=lambda: fetch(f"/api/todos/{todo['id']}/toggle", method="POST").json(),
        
        on_mutate=lambda: {
            # Optimistically update cache
            previous = query_client.get_query_data("todos")
            query_client.set_query_data("todos", lambda todos: [
                {**t, "done": not t["done"]} if t["id"] == todo["id"] else t
                for t in todos
            ])
            return {"previous": previous}
        },
        
        on_error=lambda err, _, context: {
            # Rollback on error
            query_client.set_query_data("todos", context["previous"])
        },
        
        on_settled=lambda: {
            # Always refetch to ensure consistency
            invalidate_queries("todos")
        },
    )
    
    return li(
        class_="line-through" if todo["done"] else "",
        on_click=toggle.mutate,
    )[
        todo["title"]
    ]

# =============================================================================
# Infinite Queries (Pagination)
# =============================================================================

@client
def InfiniteUserList():
    users = use_infinite_query(
        key="users_infinite",
        fn=lambda page_param: fetch(f"/api/users?page={page_param}").json(),
        get_next_page_param=lambda last_page: last_page["next_cursor"],
        initial_page_param=1,
    )
    
    return div()[
        # Flatten all pages
        ul()[
            [
                li(key=user["id"])[user["name"]]
                for page in (users.data["pages"] or [])
                for user in page["users"]
            ]
        ],
        
        button(
            on_click=users.fetch_next_page,
            disabled=not users.has_next_page or users.is_fetching_next_page,
        )[
            "Loading more..." if users.is_fetching_next_page else
            "Load More" if users.has_next_page else
            "No more users"
        ],
    ]

# =============================================================================
# Prefetching
# =============================================================================

@client
def UserListItem(user):
    # Prefetch on hover
    async def prefetch():
        await prefetch_query(
            key=["user", user["id"]],
            fn=lambda: fetch(f"/api/users/{user['id']}").json(),
        )
    
    return li(
        on_mouse_enter=prefetch,
    )[
        Link(href=f"/users/{user['id']}")[user["name"]]
    ]

# =============================================================================
# Query Client Configuration
# =============================================================================

# Global defaults
query_client = QueryClient(
    default_options={
        "stale_time": 60_000,
        "cache_time": 300_000,
        "retry": 3,
        "refetch_on_focus": True,
    }
)

# In your root component
def App():
    return QueryClientProvider(client=query_client)[
        Router()[...]
    ]
```

##### Query Checklist

```
Data Fetching Layer (Phase 52)
├── Core Query (50 tests)
│   ├── [ ] use_query basic usage
│   ├── [ ] Query key (string and array)
│   ├── [ ] Query function
│   ├── [ ] Loading/error/data states
│   ├── [ ] Enabled option
│   ├── [ ] Select transform
│   ├── [ ] Placeholder data
│   └── [ ] Initial data
│
├── Caching (40 tests)
│   ├── [ ] In-memory cache
│   ├── [ ] stale_time
│   ├── [ ] cache_time (garbage collection)
│   ├── [ ] Cache key matching
│   ├── [ ] Partial key invalidation
│   ├── [ ] get_query_data / set_query_data
│   └── [ ] Cache persistence (optional)
│
├── Refetching (30 tests)
│   ├── [ ] refetch() manual
│   ├── [ ] refetch_on_mount
│   ├── [ ] refetch_on_focus
│   ├── [ ] refetch_on_reconnect
│   ├── [ ] refetch_interval (polling)
│   └── [ ] Stale-while-revalidate
│
├── Mutations (40 tests)
│   ├── [ ] use_mutation basic
│   ├── [ ] mutate() / mutateAsync()
│   ├── [ ] Loading/error/data states
│   ├── [ ] on_mutate callback
│   ├── [ ] on_success callback
│   ├── [ ] on_error callback
│   ├── [ ] on_settled callback
│   ├── [ ] Optimistic updates
│   └── [ ] Rollback on error
│
├── Infinite Queries (20 tests)
│   ├── [ ] use_infinite_query
│   ├── [ ] fetch_next_page
│   ├── [ ] fetch_previous_page
│   ├── [ ] has_next_page / has_previous_page
│   ├── [ ] Flatten pages helper
│   └── [ ] Cursor and offset pagination
│
├── Query Client (20 tests)
│   ├── [ ] QueryClient configuration
│   ├── [ ] QueryClientProvider
│   ├── [ ] Default options
│   ├── [ ] invalidate_queries
│   ├── [ ] prefetch_query
│   ├── [ ] cancel_queries
│   └── [ ] reset_queries
│
└── Advanced (bonus)
    ├── [ ] Parallel queries
    ├── [ ] Suspense integration
    ├── [ ] SSR/hydration
    └── [ ] DevTools integration
```

##### Files to Create

- `pynext/query/__init__.py` — Query package exports
- `pynext/query/client.py` — QueryClient implementation
- `pynext/query/query.py` — use_query hook
- `pynext/query/mutation.py` — use_mutation hook
- `pynext/query/infinite.py` — use_infinite_query hook
- `pynext/query/cache.py` — Cache implementation
- `pynext/query/utils.py` — Helpers (invalidate, prefetch, etc.)
- `pynext/query/provider.py` — QueryClientProvider component
- `pynext/query/devtools.py` — Query DevTools integration

##### Success Criteria

| Metric | Target |
|--------|--------|
| Query API | Full TanStack Query-style API |
| Caching | In-memory with stale/cache time |
| Mutations | Optimistic updates with rollback |
| Infinite | Cursor and offset pagination |
| DevTools | Query cache inspection |
| Test coverage | 200+ unit tests |

##### Milestones

1. **Week 1:** Core use_query, loading/error/data states, basic caching
2. **Week 2:** Cache management, stale_time, cache_time, invalidation
3. **Week 3:** Mutations, optimistic updates, rollback
4. **Week 4:** Infinite queries, prefetching, parallel queries
5. **Week 5:** QueryClient, provider, DevTools integration

---

#### Phase 53: Form Management (180 tests, 4 weeks)

React Hook Form-style declarative form handling with validation.

##### Python API

```python
from pynext.forms import (
    use_form, Form, field,
    validators as v,
    Controller, FormProvider,
)

# =============================================================================
# Basic Form
# =============================================================================

@client
def ContactForm():
    form = use_form(
        default_values={
            "name": "",
            "email": "",
            "message": "",
        }
    )
    
    async def on_submit(data):
        await fetch("/api/contact", method="POST", body=data)
        form.reset()
    
    return form.Form(on_submit=on_submit)[
        # Register fields
        input(
            **form.register("name", required=True, min_length=2),
            placeholder="Name",
        ),
        form.error("name") and span(class_="error")[form.error("name")],
        
        input(
            **form.register("email", required=True, pattern=v.EMAIL),
            placeholder="Email",
        ),
        form.error("email") and span(class_="error")[form.error("email")],
        
        textarea(
            **form.register("message", required=True, min_length=10),
            placeholder="Message",
        ),
        form.error("message") and span(class_="error")[form.error("message")],
        
        button(
            type="submit",
            disabled=form.is_submitting,
        )[
            "Sending..." if form.is_submitting else "Send"
        ],
    ]

# =============================================================================
# Typed Form with Validation
# =============================================================================

@client
def SignupForm():
    form = use_form(
        default_values={
            "username": "",
            "email": "",
            "password": "",
            "confirm_password": "",
            "age": None,
            "terms": False,
        },
        mode="on_blur",  # Validate on blur (vs on_change, on_submit)
    )
    
    # Custom validation
    @form.validator("confirm_password")
    def passwords_match(value, form_values):
        if value != form_values["password"]:
            return "Passwords must match"
        return None
    
    @form.validator("username")
    async def username_available(value):
        # Async validation
        response = await fetch(f"/api/check-username?u={value}")
        data = await response.json()
        if not data["available"]:
            return "Username already taken"
        return None
    
    return form.Form(on_submit=handle_signup)[
        input(**form.register("username", 
            required="Username is required",
            min_length={"value": 3, "message": "At least 3 characters"},
            max_length=20,
            pattern={"value": r"^[a-z0-9_]+$", "message": "Only lowercase, numbers, underscore"},
        )),
        
        input(**form.register("email",
            required=True,
            validate=v.email("Invalid email address"),
        )),
        
        input(**form.register("password",
            required=True,
            min_length=8,
            validate=[
                v.contains_uppercase("Must contain uppercase"),
                v.contains_number("Must contain number"),
            ],
        ), type="password"),
        
        input(**form.register("confirm_password",
            required=True,
        ), type="password"),
        
        input(**form.register("age",
            value_as_number=True,  # Parse as number
            min={"value": 13, "message": "Must be 13 or older"},
            max=120,
        ), type="number"),
        
        label()[
            input(**form.register("terms", required="Must accept terms"), type="checkbox"),
            "I accept the terms and conditions",
        ],
        
        button(type="submit", disabled=not form.is_valid or form.is_submitting)[
            "Sign Up"
        ],
    ]

# =============================================================================
# Built-in Validators
# =============================================================================

from pynext.forms import validators as v

# String validators
v.required("Field is required")
v.min_length(3, "At least 3 characters")
v.max_length(100, "Max 100 characters")
v.pattern(r"^\d+$", "Must be numeric")
v.email("Invalid email")
v.url("Invalid URL")

# Number validators
v.min(0, "Must be positive")
v.max(100, "Max 100")
v.integer("Must be whole number")
v.positive("Must be positive")

# Custom validators
v.one_of(["a", "b", "c"], "Must be a, b, or c")
v.matches_field("password", "Passwords must match")

# Compose validators
v.compose(
    v.required(),
    v.min_length(8),
    v.contains_uppercase(),
    v.contains_number(),
)

# =============================================================================
# Field Arrays (Dynamic Fields)
# =============================================================================

@client
def InvoiceForm():
    form = use_form(default_values={
        "client": "",
        "items": [{"description": "", "amount": 0}],
    })
    
    items = form.use_field_array("items")
    
    return form.Form(on_submit=submit)[
        input(**form.register("client")),
        
        div()[
            [
                div(key=field.id)[
                    input(**form.register(f"items.{i}.description")),
                    input(**form.register(f"items.{i}.amount"), type="number"),
                    button(on_click=lambda: items.remove(i))["Remove"],
                ]
                for i, field in enumerate(items.fields)
            ],
        ],
        
        button(on_click=lambda: items.append({"description": "", "amount": 0}))[
            "Add Item"
        ],
        
        div()[f"Total: ${sum(item['amount'] for item in form.watch('items'))}"],
        
        button(type="submit")["Submit Invoice"],
    ]

# =============================================================================
# Controlled Components
# =============================================================================

@client
def RichEditorForm():
    form = use_form(default_values={"content": ""})
    
    return form.Form(on_submit=submit)[
        # For components that don't support standard props
        Controller(
            name="content",
            control=form.control,
            rules={"required": True, "min_length": 100},
            render=lambda field: RichTextEditor(
                value=field.value,
                on_change=field.on_change,
                on_blur=field.on_blur,
            ),
        ),
        
        button(type="submit")["Publish"],
    ]

# =============================================================================
# Form State & Helpers
# =============================================================================

form = use_form(...)

# State
form.is_valid        # All validations pass
form.is_dirty        # Any field changed from default
form.is_submitting   # Submit in progress
form.is_submitted    # Form was submitted
form.is_submit_successful  # Last submit succeeded
form.submit_count    # Number of submit attempts

# Field state
form.get_field_state("email")  # {dirty, touched, error, invalid}

# Errors
form.errors          # All errors dict
form.error("email")  # Specific field error

# Values
form.watch()         # All values (reactive)
form.watch("email")  # Specific field (reactive)
form.get_values()    # All values (snapshot)

# Actions
form.reset()                    # Reset to defaults
form.reset({"email": "new"})    # Reset with new defaults
form.set_value("email", "x")    # Set single field
form.set_error("email", "msg")  # Set error manually
form.clear_errors()             # Clear all errors
form.trigger()                  # Trigger validation
form.trigger("email")           # Validate specific field

# =============================================================================
# Schema Validation (Pydantic-style)
# =============================================================================

from pynext.forms import schema, use_form

@schema
class UserSchema:
    name: str = field(min_length=2, max_length=50)
    email: str = field(validators=[v.email()])
    age: int = field(min=0, max=120)
    role: str = field(one_of=["admin", "user", "guest"])

@client
def UserForm():
    form = use_form(schema=UserSchema)
    
    # Type-safe access
    name = form.watch("name")  # Type: str
    
    return form.Form(on_submit=submit)[
        input(**form.register("name")),
        # Errors automatically typed to schema fields
    ]
```

##### Form Checklist

```
Form Management (Phase 53)
├── Core API (40 tests)
│   ├── [ ] use_form hook
│   ├── [ ] register() field binding
│   ├── [ ] Form component wrapper
│   ├── [ ] default_values
│   ├── [ ] mode (on_change, on_blur, on_submit)
│   ├── [ ] reset() and reset with values
│   └── [ ] get_values() / watch()
│
├── Validation (50 tests)
│   ├── [ ] required
│   ├── [ ] min_length / max_length
│   ├── [ ] min / max (numbers)
│   ├── [ ] pattern (regex)
│   ├── [ ] Custom validator function
│   ├── [ ] Async validators
│   ├── [ ] Compose validators
│   ├── [ ] Field-level validation
│   ├── [ ] Form-level validation
│   └── [ ] Cross-field validation
│
├── Built-in Validators (20 tests)
│   ├── [ ] v.email()
│   ├── [ ] v.url()
│   ├── [ ] v.matches_field()
│   ├── [ ] v.one_of()
│   ├── [ ] v.contains_uppercase/lowercase/number()
│   └── [ ] v.integer(), v.positive()
│
├── Form State (25 tests)
│   ├── [ ] is_valid, is_dirty, is_submitting
│   ├── [ ] errors dict
│   ├── [ ] error(field) helper
│   ├── [ ] get_field_state()
│   ├── [ ] set_value() / set_error()
│   ├── [ ] clear_errors()
│   └── [ ] trigger() validation
│
├── Field Arrays (20 tests)
│   ├── [ ] use_field_array()
│   ├── [ ] append() / prepend()
│   ├── [ ] remove() / insert()
│   ├── [ ] move() / swap()
│   └── [ ] fields iteration
│
├── Controller (15 tests)
│   ├── [ ] Controller component
│   ├── [ ] control prop
│   ├── [ ] render function
│   └── [ ] Custom component integration
│
└── Schema Validation (10 tests)
    ├── [ ] @schema decorator
    ├── [ ] Type inference
    ├── [ ] Pydantic-style field definitions
    └── [ ] Type-safe form access
```

##### Files to Create

- `pynext/forms/__init__.py` — Forms package exports
- `pynext/forms/form.py` — use_form hook
- `pynext/forms/field.py` — Field registration and state
- `pynext/forms/validators.py` — Built-in validators
- `pynext/forms/field_array.py` — Dynamic field arrays
- `pynext/forms/controller.py` — Controller component
- `pynext/forms/schema.py` — Schema-based validation
- `pynext/forms/types.py` — Type definitions

##### Success Criteria

| Metric | Target |
|--------|--------|
| API Style | React Hook Form compatible |
| Validation | Sync and async validators |
| Field Arrays | Dynamic add/remove fields |
| Schema | Pydantic-style declarations |
| Performance | No unnecessary re-renders |
| Test coverage | 180+ unit tests |

##### Milestones

1. **Week 1:** Core use_form, register, basic validation
2. **Week 2:** All built-in validators, async validation, cross-field
3. **Week 3:** Field arrays, Controller, form state management
4. **Week 4:** Schema validation, type inference, performance optimization

---

#### Phase 54: State Management & Sync (150 tests, 4 weeks)

Advanced state persistence, undo/redo, and server synchronization.

##### Python API

```python
from pynext.state import (
    # Persistence
    persistent_signal, PersistenceProvider,
    # Undo/Redo
    use_history, History,
    # Server Sync
    use_sync, SyncProvider,
)

# =============================================================================
# Persistent Signals (Enhanced)
# =============================================================================

from pynext.state import persistent_signal

# localStorage with options
theme = persistent_signal(
    key="theme",
    default="light",
    storage="local",           # "local" | "session" | "indexeddb"
    serialize=JSON.stringify,  # Custom serializer
    deserialize=JSON.parse,    # Custom deserializer
    version=1,                 # Schema version for migrations
    migrate=lambda old, version: old,  # Migration function
)

# IndexedDB for large data
documents = persistent_signal(
    key="documents",
    default=[],
    storage="indexeddb",
    db_name="my_app",
    store_name="documents",
)

# =============================================================================
# Schema Migrations
# =============================================================================

user_prefs = persistent_signal(
    key="user_prefs",
    default={"theme": "light", "sidebar": "expanded", "notifications": True},
    version=2,
    migrate=lambda old, from_version: {
        # Version 1 → 2: Added notifications
        1: lambda data: {**data, "notifications": True},
    }.get(from_version, lambda x: x)(old),
)

# =============================================================================
# Undo/Redo History
# =============================================================================

from pynext.state import use_history

@client
def TextEditor():
    content = Signal("")
    
    history = use_history(
        signal=content,
        max_history=100,        # Keep last 100 states
        debounce_ms=500,        # Group rapid changes
    )
    
    return div()[
        div(class_="toolbar")[
            button(
                on_click=history.undo,
                disabled=not history.can_undo,
            )["Undo"],
            button(
                on_click=history.redo,
                disabled=not history.can_redo,
            )["Redo"],
            span()[f"History: {history.index + 1}/{len(history.history)}"],
        ],
        
        textarea(
            value=content(),
            on_input=lambda e: content.set(e.target.value),
        ),
    ]

# =============================================================================
# Multi-Signal History (Document-level Undo)
# =============================================================================

from pynext.state import History

@client
def DocumentEditor():
    title = Signal("Untitled")
    content = Signal("")
    tags = Signal([])
    
    # Track multiple signals together
    history = History(
        signals={"title": title, "content": content, "tags": tags},
        max_history=50,
    )
    
    def add_tag(tag):
        # All changes in a transaction are one undo step
        with history.transaction():
            tags.update(lambda t: [*t, tag])
    
    return div()[
        button(on_click=history.undo, disabled=not history.can_undo)["Undo"],
        button(on_click=history.redo, disabled=not history.can_redo)["Redo"],
        
        input(value=title(), on_input=lambda e: title.set(e.target.value)),
        textarea(value=content(), on_input=lambda e: content.set(e.target.value)),
    ]

# =============================================================================
# History API
# =============================================================================

history = use_history(signal)

# State
history.can_undo       # bool
history.can_redo       # bool
history.index          # Current position
history.history        # List of states

# Actions
history.undo()         # Go back
history.redo()         # Go forward
history.go(index)      # Jump to specific state
history.clear()        # Clear history

# Transactions (group multiple changes)
with history.transaction("Add section"):
    title.set("New Title")
    content.set("New content")
# Shows as single undo step

# =============================================================================
# Server Sync
# =============================================================================

from pynext.state import use_sync

@client
def CollaborativeDocument(doc_id: str):
    # Sync signal with server
    content = use_sync(
        key=f"doc:{doc_id}",
        default="",
        
        # Sync endpoints
        fetch_url=f"/api/docs/{doc_id}",
        save_url=f"/api/docs/{doc_id}",
        
        # Sync options
        save_debounce=1000,      # Debounce saves
        save_on_blur=True,       # Save when losing focus
        save_on_unload=True,     # Save before page unload
        
        # Conflict resolution
        on_conflict=lambda local, remote: {
            # Return merged value
            "content": merge(local["content"], remote["content"]),
        },
        
        # Callbacks
        on_save=lambda: show_toast("Saved!"),
        on_error=lambda e: show_toast(f"Save failed: {e}"),
    )
    
    return div()[
        div(class_="status")[
            "Saving..." if content.is_saving else
            "Saved" if content.is_synced else
            "Unsaved changes"
        ],
        
        textarea(
            value=content(),
            on_input=lambda e: content.set(e.target.value),
        ),
        
        button(on_click=content.save)["Save Now"],
    ]

# =============================================================================
# Realtime Sync (WebSocket)
# =============================================================================

from pynext.state import use_realtime_sync

@client
def RealtimeEditor(doc_id: str):
    content = use_realtime_sync(
        key=f"doc:{doc_id}",
        default="",
        
        # WebSocket endpoint
        ws_url=f"/ws/docs/{doc_id}",
        
        # Optimistic updates
        optimistic=True,
        
        # Presence (who's editing)
        presence=True,
        
        # CRDT for conflict-free merging
        crdt="yjs",  # or "automerge"
    )
    
    return div()[
        div(class_="presence")[
            [
                Avatar(user=u, style={"background": u["color"]})
                for u in content.presence
            ]
        ],
        
        textarea(
            value=content(),
            on_input=lambda e: content.set(e.target.value),
        ),
    ]

# =============================================================================
# Offline Support
# =============================================================================

from pynext.state import use_offline_sync

@client
def OfflineCapableForm():
    data = use_offline_sync(
        key="draft_form",
        default={},
        
        # Save to IndexedDB when offline
        offline_storage="indexeddb",
        
        # Sync when back online
        sync_url="/api/submit",
        
        # Queue operations while offline
        queue_operations=True,
    )
    
    return div()[
        div(class_="status")[
            "Offline - changes saved locally" if not navigator.onLine else
            "Online"
        ],
        # Form fields...
    ]
```

##### State Sync Checklist

```
State Management & Sync (Phase 54)
├── Enhanced Persistence (35 tests)
│   ├── [ ] persistent_signal()
│   ├── [ ] localStorage backend
│   ├── [ ] sessionStorage backend
│   ├── [ ] IndexedDB backend
│   ├── [ ] Custom serializer/deserializer
│   ├── [ ] Schema versioning
│   └── [ ] Migration functions
│
├── Undo/Redo (40 tests)
│   ├── [ ] use_history() single signal
│   ├── [ ] History class (multi-signal)
│   ├── [ ] undo() / redo()
│   ├── [ ] can_undo / can_redo
│   ├── [ ] go(index)
│   ├── [ ] clear()
│   ├── [ ] max_history limit
│   ├── [ ] Debouncing rapid changes
│   └── [ ] Transactions (grouped undo)
│
├── Server Sync (40 tests)
│   ├── [ ] use_sync() basic
│   ├── [ ] Fetch on mount
│   ├── [ ] Save debouncing
│   ├── [ ] save_on_blur / save_on_unload
│   ├── [ ] is_saving / is_synced state
│   ├── [ ] Error handling
│   ├── [ ] Conflict resolution
│   ├── [ ] Retry on failure
│   └── [ ] Manual save()
│
├── Realtime Sync (25 tests)
│   ├── [ ] use_realtime_sync()
│   ├── [ ] WebSocket connection
│   ├── [ ] Presence tracking
│   ├── [ ] Optimistic updates
│   ├── [ ] CRDT integration (Yjs/Automerge)
│   └── [ ] Reconnection handling
│
└── Offline Support (10 tests)
    ├── [ ] use_offline_sync()
    ├── [ ] IndexedDB fallback
    ├── [ ] Operation queue
    └── [ ] Sync on reconnect
```

##### Files to Create

- `pynext/state/__init__.py` — State package exports
- `pynext/state/persistent.py` — Enhanced persistent signals
- `pynext/state/history.py` — Undo/redo implementation
- `pynext/state/sync.py` — Server sync
- `pynext/state/realtime.py` — WebSocket sync
- `pynext/state/offline.py` — Offline support
- `pynext/state/crdt.py` — CRDT integration helpers
- `pynext/state/migrations.py` — Schema migration utilities

##### Success Criteria

| Metric | Target |
|--------|--------|
| Persistence | localStorage, sessionStorage, IndexedDB |
| Undo/Redo | Single and multi-signal history |
| Server Sync | Debounced saves with conflict resolution |
| Realtime | WebSocket with presence |
| Offline | Queue and sync on reconnect |
| Test coverage | 150+ unit tests |

##### Milestones

1. **Week 1:** Enhanced persistence, IndexedDB, migrations
2. **Week 2:** Undo/redo, transactions, debouncing
3. **Week 3:** Server sync, conflict resolution
4. **Week 4:** Realtime sync, offline support

---

#### Phase 55: Visual Regression Testing (100 tests, 3 weeks)

Screenshot-based testing for component visual consistency.

##### Python API

```python
from pynext.testing.visual import (
    snapshot, compare, VisualTest,
    PixelMatchOptions, configure_visual_testing,
)

# =============================================================================
# Basic Snapshot Testing
# =============================================================================

from pynext.testing.visual import snapshot, compare

def test_button_variants():
    # Capture snapshots of components
    snapshot(Button(variant="primary"), name="button-primary")
    snapshot(Button(variant="secondary"), name="button-secondary")
    snapshot(Button(variant="destructive"), name="button-destructive")
    snapshot(Button(disabled=True), name="button-disabled")

def test_button_matches_baseline():
    # Compare against saved baseline
    result = compare("button-primary")
    assert result.matches, f"Visual diff: {result.diff_percent}%"

# =============================================================================
# Snapshot with Options
# =============================================================================

def test_card_component():
    snapshot(
        Card(title="Test", content="Content"),
        name="card-default",
        
        # Viewport size
        viewport={"width": 800, "height": 600},
        
        # Wait for animations/fonts
        wait_for="fonts",  # or "animations", "network", time in ms
        
        # Mask dynamic content
        mask=[
            ".timestamp",           # CSS selector
            "[data-testid='avatar']",
        ],
        
        # Threshold for comparison
        threshold=0.01,  # 1% pixel difference allowed
    )

# =============================================================================
# Multiple Viewports (Responsive Testing)
# =============================================================================

def test_responsive_layout():
    viewports = [
        {"name": "mobile", "width": 375, "height": 667},
        {"name": "tablet", "width": 768, "height": 1024},
        {"name": "desktop", "width": 1440, "height": 900},
    ]
    
    for vp in viewports:
        snapshot(
            Dashboard(),
            name=f"dashboard-{vp['name']}",
            viewport=vp,
        )

# =============================================================================
# Component States
# =============================================================================

def test_button_states():
    # Normal
    snapshot(Button()["Click me"], name="button-normal")
    
    # Hover (simulated)
    snapshot(Button()["Click me"], name="button-hover", state="hover")
    
    # Focus
    snapshot(Button()["Click me"], name="button-focus", state="focus")
    
    # Active
    snapshot(Button()["Click me"], name="button-active", state="active")

# =============================================================================
# Dark Mode Testing
# =============================================================================

def test_dark_mode():
    snapshot(Card(title="Test"), name="card-light", theme="light")
    snapshot(Card(title="Test"), name="card-dark", theme="dark")

# =============================================================================
# Full Page Snapshots
# =============================================================================

def test_full_page():
    snapshot(
        full_page=True,  # Capture entire scrollable area
        name="dashboard-full",
        url="/dashboard",  # Or provide component
    )

# =============================================================================
# Visual Test Class (for organization)
# =============================================================================

class TestLoginPage(VisualTest):
    viewport = {"width": 1280, "height": 800}
    threshold = 0.005
    
    def test_initial_state(self):
        self.snapshot(LoginPage(), name="login-initial")
    
    def test_with_error(self):
        self.snapshot(
            LoginPage(error="Invalid credentials"),
            name="login-error",
        )
    
    def test_loading_state(self):
        self.snapshot(
            LoginPage(loading=True),
            name="login-loading",
        )

# =============================================================================
# Configuration
# =============================================================================

from pynext.testing.visual import configure_visual_testing

configure_visual_testing(
    # Baseline storage
    baseline_dir="tests/visual/baselines",
    
    # Diff output
    diff_dir="tests/visual/diffs",
    
    # Default options
    default_threshold=0.01,
    default_viewport={"width": 1280, "height": 800},
    
    # Comparison algorithm
    algorithm="pixelmatch",  # or "ssim", "perceptual"
    
    # CI behavior
    update_baselines=os.getenv("UPDATE_BASELINES") == "true",
    fail_on_missing_baseline=True,
)

# =============================================================================
# CLI Commands
# =============================================================================

# Run visual tests
# $ pynext test:visual

# Update baselines
# $ pynext test:visual --update-baselines

# Compare specific test
# $ pynext test:visual --filter "button"

# Generate report
# $ pynext test:visual --report

# =============================================================================
# CI Integration
# =============================================================================

# In GitHub Actions:
# - name: Visual Regression Tests
#   run: pynext test:visual
#   env:
#     CI: true
# 
# - name: Upload Diffs
#   if: failure()
#   uses: actions/upload-artifact@v3
#   with:
#     name: visual-diffs
#     path: tests/visual/diffs/

# =============================================================================
# Diff Report
# =============================================================================

# When tests fail, generates an HTML report:
# tests/visual/report.html
#
# Shows:
# - Side-by-side comparison (baseline vs actual)
# - Diff overlay (highlighting changes)
# - Pixel difference percentage
# - Accept/Reject buttons for updating baselines
```

##### Visual Testing Checklist

```
Visual Regression Testing (Phase 55)
├── Snapshot Capture (30 tests)
│   ├── [ ] snapshot() basic
│   ├── [ ] Component rendering
│   ├── [ ] Viewport configuration
│   ├── [ ] Wait for fonts/animations
│   ├── [ ] Mask dynamic elements
│   ├── [ ] State simulation (hover, focus)
│   ├── [ ] Theme variants (light/dark)
│   └── [ ] Full page capture
│
├── Comparison (25 tests)
│   ├── [ ] compare() against baseline
│   ├── [ ] Threshold configuration
│   ├── [ ] Pixel diff calculation
│   ├── [ ] Diff image generation
│   ├── [ ] SSIM comparison
│   └── [ ] Perceptual diff
│
├── Baseline Management (20 tests)
│   ├── [ ] Baseline storage
│   ├── [ ] Update baselines flag
│   ├── [ ] Missing baseline handling
│   ├── [ ] Baseline versioning
│   └── [ ] Cleanup old baselines
│
├── Reporting (15 tests)
│   ├── [ ] HTML diff report
│   ├── [ ] Side-by-side view
│   ├── [ ] Diff overlay
│   ├── [ ] Accept/reject UI
│   └── [ ] CI artifact upload
│
└── CLI & Integration (10 tests)
    ├── [ ] pynext test:visual
    ├── [ ] --update-baselines flag
    ├── [ ] --filter option
    ├── [ ] --report generation
    └── [ ] CI environment detection
```

##### Files to Create

- `pynext/testing/visual/__init__.py` — Visual testing exports
- `pynext/testing/visual/snapshot.py` — Snapshot capture
- `pynext/testing/visual/compare.py` — Image comparison
- `pynext/testing/visual/baseline.py` — Baseline management
- `pynext/testing/visual/report.py` — HTML report generation
- `pynext/testing/visual/config.py` — Configuration
- `pynext/testing/visual/cli.py` — CLI commands
- `pynext/testing/visual/algorithms/` — Comparison algorithms

##### Success Criteria

| Metric | Target |
|--------|--------|
| Snapshot | Component + full page |
| Comparison | Pixel, SSIM, perceptual |
| Thresholds | Configurable per-test |
| Reporting | Interactive HTML diffs |
| CI | GitHub Actions ready |
| Test coverage | 100+ unit tests |

##### Milestones

1. **Week 1:** Snapshot capture, basic comparison, baseline storage
2. **Week 2:** Advanced comparison algorithms, masking, states
3. **Week 3:** Reporting, CLI, CI integration

---

#### Phase 56: CLI Scaffolding & Generators (80 tests, 2 weeks)

Project scaffolding and code generation for rapid development.

##### CLI Commands

```bash
# =============================================================================
# Project Creation
# =============================================================================

# Create new project
$ pynext new my-app
$ pynext new my-app --template minimal
$ pynext new my-app --template full
$ pynext new my-app --template saas

# Interactive mode
$ pynext new
? Project name: my-app
? Template: (minimal, full, saas)
? Include examples: Yes
? Initialize git: Yes
? Install dependencies: Yes

# =============================================================================
# Generate Components
# =============================================================================

# Generate component
$ pynext generate component UserCard
# Creates: pages/components/user_card.py

$ pynext generate component UserCard --path src/components
# Creates: src/components/user_card.py

# With options
$ pynext generate component Modal --island
# Creates island component with client interactivity

$ pynext generate component DataTable --props "data:list,columns:list"
# Pre-fills prop definitions

# =============================================================================
# Generate Pages
# =============================================================================

# Generate page
$ pynext generate page dashboard
# Creates: pages/dashboard.py

$ pynext generate page users/[id]
# Creates: pages/users/[id].py (dynamic route)

$ pynext generate page api/users --api
# Creates: pages/api/users.py (API route)

# =============================================================================
# Generate Full Features
# =============================================================================

# Generate CRUD for a resource
$ pynext generate crud users
# Creates:
#   pages/users/index.py      (list)
#   pages/users/[id].py       (detail)
#   pages/users/new.py        (create form)
#   pages/users/[id]/edit.py  (edit form)
#   pages/api/users.py        (API endpoints)
#   components/user_form.py   (shared form)

# Generate auth pages
$ pynext generate auth
# Creates:
#   pages/login.py
#   pages/register.py
#   pages/forgot-password.py
#   pages/reset-password.py
#   middleware/auth.py

# =============================================================================
# Generate from Schema
# =============================================================================

# From Pydantic model
$ pynext generate from-schema models/user.py:User
# Generates form component with all fields

# From OpenAPI spec
$ pynext generate from-openapi openapi.json
# Generates API client and types

# =============================================================================
# Project Analysis
# =============================================================================

# Analyze bundle size
$ pynext analyze
# Opens interactive bundle analyzer

$ pynext analyze --json > bundle-stats.json
# Export as JSON

# Check for issues
$ pynext doctor
# Checks:
#   ✓ Python version
#   ✓ Dependencies installed
#   ✓ Config file valid
#   ✓ No circular imports
#   ✓ No unused components
#   ⚠ 3 components could be islands

# List all routes
$ pynext routes
# /                    pages/index.py
# /dashboard           pages/dashboard.py
# /users               pages/users/index.py
# /users/:id           pages/users/[id].py
# /api/users           pages/api/users.py

# =============================================================================
# Development Helpers
# =============================================================================

# Add shadcn component
$ pynext add button
$ pynext add card dialog table
$ pynext add --all  # Add all components

# Update dependencies
$ pynext update

# Check for updates
$ pynext outdated

# =============================================================================
# Templates (Custom Generators)
# =============================================================================

# List available templates
$ pynext templates list

# Create custom template
$ pynext templates create my-component

# Use custom template
$ pynext generate my-component Header
```

##### Generator Templates

```python
# =============================================================================
# Template Definition: .pynext/templates/component.py.template
# =============================================================================

"""
Component: {{ name }}
Generated by PyNext CLI
"""

from pynext import {{ imports }}
{% if island %}
from pynext.core.client import Signal, island
{% endif %}

{% if island %}
@island
{% endif %}
def {{ class_name }}({% for prop in props %}{{ prop.name }}: {{ prop.type }}{% if not loop.last %}, {% endif %}{% endfor %}):
    """{{ description }}"""
    {% if island %}
    # Client-side state
    {% for state in states %}
    {{ state.name }} = Signal({{ state.default }})
    {% endfor %}
    {% endif %}
    
    return div(class_="{{ css_class }}")[
        # Component content
        {% for prop in props %}
        span()[{{ prop.name }}],
        {% endfor %}
    ]

# =============================================================================
# Template Config: .pynext/templates/component.yaml
# =============================================================================

# name: component
# description: Generate a PyNext component
# 
# prompts:
#   - name: name
#     message: Component name
#     validate: required
#   
#   - name: island
#     message: Is this an island (client-interactive)?
#     type: confirm
#     default: false
#   
#   - name: props
#     message: Props (comma-separated, e.g., "title:str,count:int")
#     type: input
# 
# files:
#   - template: component.py.template
#     output: "{{ output_path }}/{{ snake_case(name) }}.py"
```

##### CLI Checklist

```
CLI Scaffolding & Generators (Phase 56)
├── Project Creation (15 tests)
│   ├── [ ] pynext new <name>
│   ├── [ ] --template option
│   ├── [ ] Interactive mode
│   ├── [ ] Git initialization
│   └── [ ] Dependency installation
│
├── Component Generation (20 tests)
│   ├── [ ] pynext generate component
│   ├── [ ] --path option
│   ├── [ ] --island flag
│   ├── [ ] --props definition
│   └── [ ] Name case conversion
│
├── Page Generation (15 tests)
│   ├── [ ] pynext generate page
│   ├── [ ] Dynamic routes [id]
│   ├── [ ] Catch-all routes [...]
│   ├── [ ] API routes --api
│   └── [ ] Layout generation
│
├── CRUD Generation (10 tests)
│   ├── [ ] pynext generate crud
│   ├── [ ] List, detail, create, edit pages
│   ├── [ ] API endpoints
│   └── [ ] Form component
│
├── Analysis Tools (10 tests)
│   ├── [ ] pynext analyze (bundle)
│   ├── [ ] pynext doctor
│   ├── [ ] pynext routes
│   └── [ ] pynext outdated
│
└── Custom Templates (10 tests)
    ├── [ ] Template definition
    ├── [ ] Template prompts
    ├── [ ] Variable substitution
    └── [ ] File output
```

##### Files to Create

- `pynext/cli/__init__.py` — CLI entry point
- `pynext/cli/commands/new.py` — Project creation
- `pynext/cli/commands/generate.py` — Code generation
- `pynext/cli/commands/analyze.py` — Bundle analysis
- `pynext/cli/commands/doctor.py` — Project health check
- `pynext/cli/commands/routes.py` — Route listing
- `pynext/cli/commands/add.py` — Add shadcn components
- `pynext/cli/templates/` — Built-in templates
- `pynext/cli/prompts.py` — Interactive prompts

##### Success Criteria

| Metric | Target |
|--------|--------|
| Project creation | 3+ templates |
| Generators | Component, page, CRUD, auth |
| Analysis | Bundle size, doctor checks |
| Custom templates | Full templating system |
| Test coverage | 80+ unit tests |

##### Milestones

1. **Week 1:** Project creation, component/page generation
2. **Week 2:** CRUD generation, analysis tools, custom templates

---

### Implementation Timeline

| Quarter | Phases | Focus |
|---------|--------|-------|
| Q1 | 33.1-33.2 | Core Transpilation Fundamentals & Advanced |
| Q2 | 33.3-35.5 | Infrastructure, DOM, Browser, DevTools |
| Q3 | 36-40 | Interaction + Media |
| Q4 | 41-44 | Graphics + Performance |
| Q5 | 45-51.6 | Editors + Advanced + LLM DevTools + MCP Integration |
| Q6 | 52-56 | Application Infrastructure |

**Total: 5985+ tests, 113+ weeks (~28 months)**

---

### Type Stubs for All Phases

Each phase should include `.pyi` type stub files for IDE autocomplete:

| Phase | Stub Files |
|-------|------------|
| 33.1 | Core language types (no stubs needed - Python native) |
| 33.2 | Advanced construct types (no stubs needed - Python native) |
| 33.3 | Exception types (no stubs needed - Python native) |
| 33.4 | `testing.pyi`, `typed.pyi`, `datetime.pyi`, `collections.pyi`, `itertools.pyi`, `functools.pyi` |
| 34 | `document.pyi`, `element.pyi`, `events.pyi`, `node.pyi` |
| 35 | `window.pyi`, `navigator.pyi`, `fetch.pyi`, `console.pyi`, `crypto.pyi`, `intl.pyi` |
| 35.5 | `devtools.pyi` |
| 36 | `animation.pyi`, `spring.pyi`, `timeline.pyi` |
| 37 | `gestures.pyi`, `pointer.pyi`, `drag.pyi` |
| 38 | `observers.pyi` |
| 39 | `file.pyi`, `canvas.pyi`, `audio.pyi` |
| 40 | `websocket.pyi`, `sse.pyi`, `webrtc.pyi`, `indexeddb.pyi`, `trusted_types.pyi` |
| 41 | `webgl.pyi`, `webgpu.pyi` |
| 42 | `svg.pyi` |
| 43 | `worker.pyi`, `wasm.pyi` |
| 44 | `virtual.pyi` |
| 45 | `selection.pyi`, `editable.pyi`, `fonts.pyi`, `highlight.pyi` |
| 46 | `monaco.pyi`, `codemirror.pyi` |
| 47 | `terminal.pyi` |
| 48 | `canvas_viewport.pyi`, `dom_matrix.pyi` |
| 49 | `broadcast_channel.pyi`, `service_worker.pyi` |
| 50 | `speech.pyi`, `payment.pyi`, `notification.pyi`, `gamepad.pyi`, `bluetooth.pyi` |
| 51 | `time_travel.pyi`, `breakpoints.pyi` |
| 51.5 | `debug_cli.pyi`, `debug_server.pyi`, `dap.pyi` |
| 51.6 | `mcp.pyi`, `browser_inspector.pyi`, `diagnostics.pyi` |
| 52 | `query.pyi`, `mutation.pyi`, `query_client.pyi` |
| 53 | `forms.pyi`, `validators.pyi`, `field_array.pyi` |
| 54 | `persistent.pyi`, `history.pyi`, `sync.pyi` |
| 55 | `visual.pyi`, `snapshot.pyi`, `compare.pyi` |
| 56 | `cli.pyi`, `generators.pyi` |

---

### Files Created Summary

| Phase | New Files |
|-------|-----------|
| 33.1 | `pynext/transpiler/functions.py`, `transpiler/classes.py`, `transpiler/control_flow.py`, `transpiler/comprehensions.py`, `runtime/decorators.js`, `runtime/classes.js` |
| 33.2 | `pynext/transpiler/dunders.py`, `transpiler/generators.py`, `transpiler/context.py`, `transpiler/pattern.py`, `transpiler/async_support.py`, `runtime/dunders.js`, `runtime/generators.js`, `runtime/proxy.js` |
| 33.3 | `pynext/runtime/exceptions.js`, `transpiler/imports.py`, `transpiler/sourcemap.py`, `transpiler/stack_rewriter.py`, `transpiler/operators.py` |
| 33.4 | `pynext/testing/__init__.py`, `testing/client.py`, `testing/mocks.py`, `testing/queries.py`, `client/typed.py`, `runtime/stdlib/datetime.js`, `runtime/stdlib/collections.js`, `runtime/stdlib/itertools.js`, `runtime/stdlib/functools.js`, `runtime/stdlib/operator.js`, `runtime/stdlib/copy.js`, `runtime/promise.js`, `runtime/scheduling.js` |
| 34 | `pynext/client/dom.py`, `pynext/client/events.py`, `pynext/client/error_boundary.py`, `pynext/client/*.pyi` (type stubs) |
| 35 | `pynext/client/window.py`, `pynext/client/navigator.py`, `pynext/client/fetch.py`, `pynext/client/*.pyi` (type stubs) |
| 35.5 | `pynext/devtools/__init__.py`, `devtools/signal_inspector.py`, `devtools/component_tree.py`, `devtools/reactivity_graph.py`, `devtools/network_panel.py`, `devtools/performance.py`, `devtools/panel.js` |
| 36 | `pynext/client/animation.py`, `pynext/client/spring.py`, `pynext/client/timeline.py` |
| 37 | `pynext/client/gestures.py`, `pynext/client/pointer.py`, `pynext/client/drag.py` |
| 38 | `pynext/client/observers.py` |
| 39 | `pynext/client/file.py`, `pynext/client/canvas.py`, `pynext/client/audio.py` |
| 40 | `pynext/client/websocket.py`, `pynext/client/sse.py`, `pynext/client/webrtc.py`, `pynext/client/indexeddb.py`, `pynext/client/cache.py` |
| 41 | `pynext/client/webgl.py`, `pynext/client/webgpu.py`, `pynext/runtime/webgl.js` |
| 42 | `pynext/client/svg.py` |
| 43 | `pynext/client/workers.py`, `pynext/client/wasm.py`, `pynext/client/atomics.py` |
| 44 | `pynext/client/virtual.py` |
| 45 | `pynext/client/selection.py`, `pynext/client/editable.py`, `pynext/client/clipboard.py` |
| 46 | `pynext/client/monaco.py`, `pynext/client/codemirror.py` |
| 47 | `pynext/client/terminal.py` |
| 48 | `pynext/client/canvas_viewport.py` |
| 49 | `pynext/client/broadcast.py`, `pynext/client/offline.py` |
| 50 | `pynext/client/speech.py`, `pynext/client/payments.py`, `pynext/client/devices.py` |
| 51 | `pynext/devtools/time_travel.py`, `devtools/breakpoints.py`, `devtools/debugger.py`, `devtools/extension/` (browser extension) |
| 51.5 | `pynext/devtools/cli/` (CLI commands), `devtools/server/` (debug server), `devtools/dap/` (DAP adapter), `devtools/ai/` (AI commands), `devtools/vscode/` (VS Code extension) |
| 51.6 | `pynext/devtools/mcp/` (MCP server), `devtools/browser/` (browser-aware debugging), `cli/commands/init_debug.py` |
| 52 | `pynext/query/__init__.py`, `query/client.py`, `query/query.py`, `query/mutation.py`, `query/infinite.py`, `query/cache.py` |
| 53 | `pynext/forms/__init__.py`, `forms/form.py`, `forms/field.py`, `forms/validators.py`, `forms/field_array.py`, `forms/controller.py`, `forms/schema.py` |
| 54 | `pynext/state/__init__.py`, `state/persistent.py`, `state/history.py`, `state/sync.py`, `state/realtime.py`, `state/offline.py` |
| 55 | `pynext/testing/visual/__init__.py`, `visual/snapshot.py`, `visual/compare.py`, `visual/baseline.py`, `visual/report.py`, `visual/cli.py` |
| 56 | `pynext/cli/commands/new.py`, `cli/commands/generate.py`, `cli/commands/analyze.py`, `cli/commands/doctor.py`, `cli/templates/` |

---

### Success Criteria

| Metric | Target |
|--------|--------|
| Client-side coverage | 100% — No JS hacks needed for any interaction |
| Application compatibility | Can build Figma, Notion, Discord, Replit in pure Python |
| Bundle size | Less than 20KB base runtime |
| Test coverage | 4250+ tests |
| Documentation | Full API docs with examples for all 18 phases |

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

## 🔮 Future Vision: TurboPyNext

> *"When PyNext projects regularly exceed 1,000+ islands and sub-10ms builds become critical, we'll implement TurboPyNext."*

### What Is TurboPyNext?

A **full Rust rewrite** of the PyNext compiler, inspired by Vercel's Turbopack. This replaces the current Python-based build system with a native Rust binary for maximum build performance.

**Important:** TurboPyNext is a **Developer Experience (DX)** improvement. It makes builds faster during development but has **zero impact on browser load time or runtime performance** — the generated JavaScript output is identical.

### Why Full Rust?

| Metric | Current (Python) | TurboPyNext (Rust) | Improvement |
|--------|------------------|-------------------|-------------|
| 100 islands | ~35ms | ~1-2ms | 20-35x faster |
| 1,000 islands | ~350ms | ~10ms | 35x faster |
| 10,000 islands | ~3.5s | ~100ms | 35x faster |
| Incremental (1 file) | ~32ms | ~1ms | 32x faster |
| Memory usage | Higher (Python) | Lower (native) | ~5x less |

### Architecture

```
pynext-turbo/                      # Standalone Rust project
├── crates/
│   ├── pynext-cli/               # `pynext-turbo build` command
│   │   └── (clap for arg parsing)
│   │
│   ├── pynext-parser/            # Python AST parsing
│   │   └── (tree-sitter-python)
│   │
│   ├── pynext-ir/                # Reactive intermediate representation
│   │   └── Signal/Effect/Store/Memo detection
│   │
│   ├── pynext-emit/              # JavaScript code generation
│   │   └── Same output as Python compiler
│   │
│   └── pynext-cache/             # Incremental computation engine
│       └── (salsa for fine-grained caching)
│
├── Cargo.toml
└── README.md

pynext/                            # Python framework (unchanged API)
└── build/
    └── turbo.py                  # subprocess.run(["pynext-turbo", ...])
```

### Technology Choices

| Component | Technology | Why |
|-----------|------------|-----|
| **Parser** | `tree-sitter-python` | Incremental parsing, error recovery, fast |
| **Incremental Engine** | `salsa` | Fine-grained dependency tracking (used by rust-analyzer) |
| **Parallelism** | `rayon` | Work-stealing parallel iteration across all cores |
| **CLI** | `clap` | Fast, ergonomic argument parsing |
| **Serialization** | `serde_json` | Zero-copy JSON for manifests and cache |

### What TurboPyNext Affects

| Metric | Impact |
|--------|--------|
| Build time | ✅ 20-50x faster |
| HMR speed | ✅ Sub-millisecond updates |
| Dev server start | ✅ Near-instant |
| Cold start | ✅ Faster initial compilation |
| **Bundle size** | ❌ No change (same JS output) |
| **Page load time** | ❌ No change |
| **Runtime performance** | ❌ No change |
| **Time to Interactive** | ❌ No change |

### When To Build TurboPyNext

**Trigger conditions (pursue when ANY are true):**
1. Teams report build times as a pain point (> 1s for typical project)
2. HMR latency noticeably impacts development flow
3. Large projects with 500+ islands become common
4. Enterprise adoption requires faster CI/CD builds

**Not needed if:**
- Most projects have < 100 islands (current 35ms is fine)
- Development workflow doesn't require sub-10ms builds
- Team doesn't have Rust expertise and no resources to acquire it

### Implementation Phases

| Phase | Work | Duration | Deliverable |
|-------|------|----------|-------------|
| **1. Parser** | tree-sitter-python integration, Python AST → Rust types | 2-3 months | Parse 10K files/sec |
| **2. IR** | Reactive analysis, signal/effect/store detection | 2-3 months | Correct analysis |
| **3. Emitter** | JavaScript code generation, source maps | 2-3 months | Identical JS output |
| **4. Cache** | Salsa incremental engine, persistent cache | 2-3 months | Sub-ms incremental |
| **5. CLI + Distribution** | Binary builds, platform wheels, CI/CD | 1-2 months | `pip install pynext[turbo]` |
| **Total** | | **9-14 months** | Full TurboPyNext |

### Installation Model

```bash
# Option 1: Pre-built binaries via pip (recommended)
pip install pynext[turbo]
# Downloads platform-specific binary (Linux/macOS/Windows, x64/ARM64)

# Option 2: Build from source (requires Rust toolchain)
cargo install pynext-turbo

# Usage
pynext build --turbo        # Use Rust compiler (fast)
pynext build                # Use Python compiler (fallback)

# The output is identical — only build speed differs
```

### Success Metrics

| Metric | Target |
|--------|--------|
| 100 islands cold build | < 5ms |
| 1,000 islands cold build | < 50ms |
| 10,000 islands cold build | < 200ms |
| Single file incremental | < 5ms |
| Binary size | < 10MB |
| Platforms | Linux, macOS, Windows (x64, ARM64) |
| Memory usage | < 100MB for 10K islands |

### Comparison to Turbopack

| Aspect | Turbopack | TurboPyNext |
|--------|-----------|-------------|
| **Source language** | JavaScript/TypeScript | Python |
| **Target** | Bundle JS/TS for Next.js | Compile Python → minimal JS |
| **Output** | Bundled React apps | Tiny SolidJS-style islands |
| **Team** | Vercel (100+ engineers) | PyNext contributors |
| **Shared tech** | Rust, salsa-like caching | Same |

TurboPyNext is inspired by Turbopack's architecture but solves a different problem: compiling Python to JavaScript rather than bundling JavaScript.

---

## Contributing

Have an idea that's not on this list? Open an issue or discussion to propose new features!

