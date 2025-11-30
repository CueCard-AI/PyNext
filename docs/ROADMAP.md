# PyNext Roadmap

This document tracks future enhancements and features for PyNext. Ideas captured here are not currently in development but represent the product vision.

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
**Total Test Suite**: 4,653 tests
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
- [x] Documentation: `docs/features/DATABASE.md`

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

**Documentation:** [MIGRATIONS.md](./features/MIGRATIONS.md)

##### Phase 5: Database Adapters (PostgreSQL & Supabase)

**Status:** Planned (620 tests planned)

**Design Philosophy:**
- PyNext > asyncpg: Simpler API, same performance
- Zero Config: Works out of the box with sensible defaults
- Production Ready: Circuit breakers, retries, health checks built-in
- Supabase Native: First-class citizen, not an afterthought
- Hyper-Efficient: Connection reuse, prepared statements, minimal overhead

**5.1 PostgreSQL Core Adapter:**
- [ ] `pynext/db/adapters/postgres.py` - asyncpg-based adapter
- [ ] Connection URL and individual param configuration
- [ ] Statement caching for performance (LRU cache, configurable size)
- [ ] Binary protocol for maximum throughput
- [ ] Pipelining support for batch operations

**5.2 Connection Pooling (High-Performance):**
- [ ] Built-in asyncpg pool with intelligent sizing
  - Auto-scale: min_size=5, max_size=100 (configurable)
  - Idle connection recycling (prevent stale connections)
  - Connection warmup on startup
- [ ] External pooler support (PgBouncer, pgpool)
  - Transaction pooling mode (recommended for high concurrency)
  - Session pooling mode (for prepared statements)
- [ ] Pool overflow handling with queuing
  - Max wait time before rejection
  - Queue depth monitoring
- [ ] Connection lifetime limits (prevent memory leaks)

**5.3 Production Reliability:**
- [ ] Health checks with configurable intervals
- [ ] Retry with exponential backoff (1s, 2s, 4s, max 30s)
- [ ] Circuit breaker (failure threshold, recovery timeout)
- [ ] Read replica routing with weighted distribution
- [ ] Graceful degradation under load

**5.4 High-Load Scalability:**
- [ ] Request queuing with backpressure
  - Max queue size before rejection
  - Fair queuing (FIFO)
- [ ] Load shedding when overwhelmed
  - Configurable thresholds
  - Graceful rejection with retry-after headers
- [ ] Connection multiplexing
- [ ] Async connection acquisition (non-blocking)
- [ ] Pool statistics and metrics
  - Active/idle/waiting connections
  - Queries per second
  - Average query time

**5.5 Error Logging & Debugging:**
- [ ] Structured logging with context
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
- [ ] Slow query logging (configurable threshold)
- [ ] Query explain on timeout (auto-analyze slow queries)
- [ ] Pool exhaustion warnings (before failure)
- [ ] Connection leak detection
- [ ] Dead connection detection and cleanup
- [ ] Metrics export (Prometheus/OpenTelemetry)
  - `pynext_db_connections_active`
  - `pynext_db_connections_waiting`
  - `pynext_db_query_duration_seconds`
  - `pynext_db_pool_exhausted_total`
  - `pynext_db_errors_total{type="timeout|connection|query"}`

**5.6 Supabase Full Integration:**
- [ ] Supabase adapter with URL/key configuration
- [ ] Auth: sign_up, sign_in, sign_out, session management
- [ ] Storage: upload, download, delete, signed URLs
- [ ] Realtime: table subscriptions with decorators
- [ ] Edge Functions: invoke remote functions
- [ ] RLS helpers: policy decorators

**5.7 Advanced Query Features:**
- [ ] Per-query `.timeout(seconds)` with statement_timeout
- [ ] `.explain()` and `.analyze()` for query plans
- [ ] Cursor-based pagination for large datasets
- [ ] Prepared statement support with auto-invalidation
- [ ] Query cancellation on client disconnect

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

