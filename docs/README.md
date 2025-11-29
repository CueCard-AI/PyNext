# PyNext Documentation

> **The complete guide to building modern web applications with PyNext.**

Welcome to the PyNext documentation! This index will help you find exactly what you need, whether you're just getting started or diving into advanced topics.

---

## 📍 Quick Navigation

| I want to... | Go to |
|--------------|-------|
| Get started quickly | [Getting Started](getting-started/GETTING_STARTED.md) |
| Understand how routing works | [Routing](routing/ROUTING.md) |
| Learn about state management | [State Management](core-concepts/STATE_MANAGEMENT.md) |
| Build forms and handle data | [State Patterns](data-server/STATE_PATTERNS.md) |
| Call Python from the browser | [Server Actions](data-server/SERVER_ACTIONS.md) |
| Deploy to production | [Deployment](production/DEPLOYMENT.md) |

---

## 🗺️ Documentation Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PYNEXT DOCUMENTATION MAP                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                           ┌─────────────────┐                               │
│                           │ GETTING STARTED │ ← Start here!                 │
│                           └────────┬────────┘                               │
│                                    │                                         │
│              ┌─────────────────────┼─────────────────────┐                  │
│              ▼                     ▼                     ▼                  │
│    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐         │
│    │  CORE CONCEPTS  │   │     ROUTING     │   │   DATA & STATE  │         │
│    │                 │   │                 │   │                 │         │
│    │ • HTML API      │   │ • Routes        │   │ • State Mgmt    │         │
│    │ • State Mgmt    │   │ • Layouts       │   │ • Server Actions│         │
│    │ • Hydration     │   │ • Navigation    │   │ • API Routes    │         │
│    └────────┬────────┘   └────────┬────────┘   └────────┬────────┘         │
│             │                     │                     │                   │
│             └─────────────────────┼─────────────────────┘                   │
│                                   ▼                                         │
│              ┌─────────────────────────────────────────────┐                │
│              │            RENDERING STRATEGIES             │                │
│              │                                             │                │
│              │  Streaming • Islands • ISR • Static Gen    │                │
│              └─────────────────────┬───────────────────────┘                │
│                                    │                                         │
│              ┌─────────────────────┼─────────────────────┐                  │
│              ▼                     ▼                     ▼                  │
│    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐         │
│    │   OPTIMIZATION  │   │    ADVANCED     │   │   PRODUCTION    │         │
│    │                 │   │                 │   │                 │         │
│    │ • Images        │   │ • Middleware    │   │ • Deployment    │         │
│    │ • Fonts         │   │ • i18n          │   │ • Testing       │         │
│    │ • Code Split    │   │ • Draft Mode    │   │ • Config        │         │
│    └─────────────────┘   └─────────────────┘   └─────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Folder Structure

```
docs/
├── README.md                    ← You are here
│
├── getting-started/             🚀 Start here
│   ├── GETTING_STARTED.md       Installation & first app
│   ├── CLI.md                   Command-line tools
│   └── CONFIGURATION.md         Config options
│
├── core-concepts/               🧱 Fundamentals
│   ├── HTML_API.md              Building UI with Python
│   ├── STATE_MANAGEMENT.md      Signals, Stores, Effects
│   └── HYDRATION.md             Server → Client
│
├── routing/                     🛤️ Navigation
│   ├── ROUTING.md               File-based routes
│   ├── LAYOUTS.md               Shared UI wrappers
│   ├── TRANSITIONS.md           Page animations
│   ├── PARALLEL_ROUTES.md       Multi-slot layouts
│   └── INTERCEPTING_ROUTES.md   Modal patterns
│
├── data-server/                 📊 Data & Forms
│   ├── SERVER_ACTIONS.md        RPC to Python
│   ├── API_ROUTES.md            REST endpoints
│   ├── STATE_PATTERNS.md        Forms & async
│   └── STATE_DATA_INTEGRATION.md Full data flow
│
├── rendering/                   ⚡ Rendering Strategies
│   ├── STREAMING_SUSPENSE.md    Progressive loading
│   ├── ISLANDS.md               Selective hydration
│   ├── STATIC_GENERATION.md     Build-time HTML
│   ├── ISR.md                   Incremental regen
│   └── PARTIAL_PRERENDERING.md  Static + dynamic
│
├── advanced/                    🔧 Power Features
│   ├── MIDDLEWARE.md            Request interception
│   ├── DRAFT_MODE.md            CMS preview
│   └── I18N.md                  Multi-language
│
├── optimization/                📦 Performance
│   ├── IMAGE_OPTIMIZATION.md    Fast images
│   ├── FONT_OPTIMIZATION.md     Zero layout shift
│   ├── SCRIPT_OPTIMIZATION.md   Third-party scripts
│   └── CODE_SPLITTING.md        Smaller bundles
│
├── features/                    ✨ Client Runtime & File Conventions
│   ├── CLIENT_RUNTIME.md        Complete overview
│   ├── KEYBOARD.md              Shortcuts & sequences
│   ├── THEME.md                 Dark mode & theming
│   ├── FOCUS.md                 Accessibility & traps
│   ├── STORAGE.md               Persistent state
│   ├── SSE.md                   Server-Sent Events
│   ├── VISIBILITY.md            Tab visibility tracking
│   ├── ONLINE_STATUS.md         Network detection
│   ├── ROUTE_GROUPS.md          (folder) URL organization
│   ├── TEMPLATE.md              Remounting layouts
│   ├── ERROR_PAGES.md           Custom 401/403/404
│   ├── PROJECT_STRUCTURE.md     src/ folder support
│   ├── ENVIRONMENT.md           Environment variables
│   ├── ROUTE_CONFIG.md          Route segment configuration
│   ├── SITEMAP.md               SEO: Sitemap & robots.txt
│   ├── PWA.md                   PWA: Icons & manifest
│   └── OG_IMAGES.md             Dynamic OG images (NEW)
│
├── integrations/                🔌 External Tools
│   ├── NPM_PACKAGES.md          Using npm
│   └── REACT_INTEGRATION.md     React components
│
├── production/                  🚢 Ship It
│   ├── DEPLOYMENT.md            Docker & cloud
│   └── TESTING.md               Unit, E2E tests
│
└── reference/                   📋 Reference
    └── PHASE2_FEATURES.md       Roadmap
```

---

## 📚 Documentation by Category

### 🚀 Getting Started

Start here if you're new to PyNext.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [Getting Started](getting-started/GETTING_STARTED.md) | Installation, project setup, first app | 🟢 Beginner |
| [CLI Reference](getting-started/CLI.md) | Command-line tools (`pynext dev`, `build`, etc.) | 🟢 Beginner |
| [Configuration](getting-started/CONFIGURATION.md) | `pynext.config.py` options | 🟢 Beginner |

---

### 🧱 Core Concepts

The fundamental building blocks of PyNext.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [HTML API](core-concepts/HTML_API.md) | Building UI with Python (`div`, `span`, `button`, etc.) | 🟢 Beginner |
| [State Management](core-concepts/STATE_MANAGEMENT.md) | Signals, Stores, Computed, Effects | 🟡 Intermediate |
| [Hydration](core-concepts/HYDRATION.md) | How server HTML becomes interactive | 🟡 Intermediate |

---

### 🛤️ Routing & Navigation

How URLs map to pages and how users navigate.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [Routing](routing/ROUTING.md) | File-based routing, dynamic routes, catch-all | 🟢 Beginner |
| [Layouts](routing/LAYOUTS.md) | Shared UI wrappers, nesting, special files | 🟢 Beginner |
| [Transitions](routing/TRANSITIONS.md) | Page transitions, View Transitions API | 🟡 Intermediate |
| [Parallel Routes](routing/PARALLEL_ROUTES.md) | Multiple pages in one layout (slots) | 🔴 Advanced |
| [Intercepting Routes](routing/INTERCEPTING_ROUTES.md) | Modal patterns, route interception | 🔴 Advanced |

---

### 📊 Data & Server

Fetching data, handling forms, and server communication.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [Server Actions](data-server/SERVER_ACTIONS.md) | Call Python from browser events | 🟡 Intermediate |
| [API Routes](data-server/API_ROUTES.md) | REST endpoints alongside pages | 🟡 Intermediate |
| [State Patterns](data-server/STATE_PATTERNS.md) | Forms, async state, optimistic updates | 🟡 Intermediate |
| [State & Data Integration](data-server/STATE_DATA_INTEGRATION.md) | Full data flow patterns | 🔴 Advanced |

---

### ⚡ Rendering Strategies

Different ways to render your pages for different use cases.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [Streaming & Suspense](rendering/STREAMING_SUSPENSE.md) | Progressive rendering, loading states | 🟡 Intermediate |
| [Islands Architecture](rendering/ISLANDS.md) | Selective hydration, minimal JS | 🟡 Intermediate |
| [Static Generation (SSG)](rendering/STATIC_GENERATION.md) | Build-time rendering, zero JS | 🟡 Intermediate |
| [ISR (Incremental Static Regen)](rendering/ISR.md) | Static with automatic updates | 🟡 Intermediate |
| [Partial Prerendering](rendering/PARTIAL_PRERENDERING.md) | Mix static shell with dynamic content | 🔴 Advanced |

---

### 🔧 Advanced Features

Powerful features for complex applications.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [Middleware](advanced/MIDDLEWARE.md) | Request interception, auth, redirects | 🟡 Intermediate |
| [Draft Mode](advanced/DRAFT_MODE.md) | CMS preview, unpublished content | 🟡 Intermediate |
| [Internationalization (i18n)](advanced/I18N.md) | Multi-language support | 🟡 Intermediate |

---

### 📦 Optimization

Making your app fast and efficient.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [Image Optimization](optimization/IMAGE_OPTIMIZATION.md) | AVIF/WebP, lazy loading, BlurHash | 🟢 Beginner |
| [Font Optimization](optimization/FONT_OPTIMIZATION.md) | Font loading, subsetting, display | 🟢 Beginner |
| [Script Optimization](optimization/SCRIPT_OPTIMIZATION.md) | Third-party scripts, loading strategies | 🟡 Intermediate |
| [Code Splitting](optimization/CODE_SPLITTING.md) | Bundle optimization, lazy loading | 🟡 Intermediate |

---

### ✨ Client Runtime Features

Browser interactivity with Python — no JavaScript required!

| Document | Description | Difficulty |
|----------|-------------|------------|
| [Client Runtime Overview](features/CLIENT_RUNTIME.md) | Complete guide to browser APIs from Python | 🟡 Intermediate |
| [Keyboard Shortcuts](features/KEYBOARD.md) | `@on_keydown`, sequences, platform detection | 🟡 Intermediate |
| [Theme Management](features/THEME.md) | Dark mode, system preferences, flash prevention | 🟡 Intermediate |
| [Focus Management](features/FOCUS.md) | Focus traps, roving focus, skip links | 🟡 Intermediate |
| [Storage](features/STORAGE.md) | `use_storage` for localStorage/sessionStorage | 🟡 Intermediate |
| [Server-Sent Events](features/SSE.md) | `use_event_source` for real-time updates | 🟡 Intermediate |
| [Visibility Tracking](features/VISIBILITY.md) | `use_visibility` for smart polling | 🟡 Intermediate |
| [Network Status](features/ONLINE_STATUS.md) | `use_online` for offline detection | 🟡 Intermediate |

---

### 🗂️ File Conventions

Next.js-style file conventions for organizing your project.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [Route Groups](features/ROUTE_GROUPS.md) | Organize routes with `(folder)` without affecting URLs | 🟢 Beginner |
| [Template](features/TEMPLATE.md) | Layouts that remount on navigation (page transitions) | 🟡 Intermediate |
| [Error Pages](features/ERROR_PAGES.md) | Custom 401/403/404/500 pages with zero JS | 🟢 Beginner |
| [Project Structure](features/PROJECT_STRUCTURE.md) | Auto-detect `src/` folder, path resolution | 🟢 Beginner |

---

### ⚙️ Configuration

Environment and route configuration management.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [Environment Variables](features/ENVIRONMENT.md) | Type-safe `.env` files with schema validation | 🟢 Beginner |
| [Route Config](features/ROUTE_CONFIG.md) | Per-route rendering, caching, and runtime | 🟡 Intermediate |
| [Sitemap & Robots.txt](features/SITEMAP.md) | SEO: sitemap generation and robots.txt | 🟢 Beginner |
| [PWA: Icons & Manifest](features/PWA.md) | Make your app installable | 🟢 Beginner |
| [Dynamic OG Images](features/OG_IMAGES.md) | Generate social preview images | 🟡 Intermediate |

---

### 🔌 Integrations

Using external tools and libraries with PyNext.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [NPM Packages](integrations/NPM_PACKAGES.md) | Using npm packages in PyNext | 🟢 Beginner |
| [React Integration](integrations/REACT_INTEGRATION.md) | Using React components in PyNext | 🔴 Advanced |

---

### 🚢 Production

Deploying and maintaining your application.

| Document | Description | Difficulty |
|----------|-------------|------------|
| [Deployment](production/DEPLOYMENT.md) | Docker, cloud platforms, production setup | 🟡 Intermediate |
| [Testing](production/TESTING.md) | Unit tests, integration tests, E2E | 🟡 Intermediate |

---

### 📋 Reference

Additional reference materials.

| Document | Description |
|----------|-------------|
| [Phase 2 Features](reference/PHASE2_FEATURES.md) | Roadmap and upcoming features |

---

## 🎓 Learning Paths

### Path 1: "I'm New to PyNext" (2-3 hours)

```
1. Getting Started ──► 2. HTML API ──► 3. Routing ──► 4. State Management
                                              │
                                              ▼
                       5. Server Actions ◄── 4. Layouts
```

**Read in order:**
1. [Getting Started](getting-started/GETTING_STARTED.md) - Setup and basics
2. [HTML API](core-concepts/HTML_API.md) - Building UI
3. [Routing](routing/ROUTING.md) - Pages and navigation
4. [Layouts](routing/LAYOUTS.md) - Shared UI
5. [State Management](core-concepts/STATE_MANAGEMENT.md) - Reactivity
6. [Server Actions](data-server/SERVER_ACTIONS.md) - Server communication

---

### Path 2: "I Want to Build a Full App" (4-6 hours)

After completing Path 1, continue with:

```
State Patterns ──► API Routes ──► Streaming ──► Middleware ──► Deployment
```

**Read in order:**
1. [State Patterns](data-server/STATE_PATTERNS.md) - Forms, async, optimistic updates
2. [API Routes](data-server/API_ROUTES.md) - REST endpoints
3. [Streaming & Suspense](rendering/STREAMING_SUSPENSE.md) - Loading states
4. [Middleware](advanced/MIDDLEWARE.md) - Auth, redirects
5. [Deployment](production/DEPLOYMENT.md) - Going to production

---

### Path 3: "I Want Maximum Performance" (2-3 hours)

Focus on rendering strategies and optimization:

```
Islands ──► Static Gen ──► ISR ──► Partial Prerendering
                │
                ▼
        Image/Font/Code Optimization
```

**Read in order:**
1. [Islands Architecture](rendering/ISLANDS.md) - Minimal JavaScript
2. [Static Generation](rendering/STATIC_GENERATION.md) - Build-time rendering
3. [ISR](rendering/ISR.md) - Static with freshness
4. [Image Optimization](optimization/IMAGE_OPTIMIZATION.md) - Fast images
5. [Code Splitting](optimization/CODE_SPLITTING.md) - Smaller bundles

---

### Path 4: "I'm Building a Content Site/CMS" (2 hours)

For blogs, documentation, marketing sites:

```
Static Gen ──► ISR ──► Draft Mode ──► i18n
```

**Read in order:**
1. [Static Generation](rendering/STATIC_GENERATION.md) - Pre-build pages
2. [ISR](rendering/ISR.md) - Update without rebuilding
3. [Draft Mode](advanced/DRAFT_MODE.md) - Preview unpublished content
4. [I18N](advanced/I18N.md) - Multi-language

---

## 🔍 Quick Reference

### Common Tasks

| Task | Document | Key Section |
|------|----------|-------------|
| Create a new page | [Routing](routing/ROUTING.md) | Basic Routes |
| Add a dynamic route like `/users/[id]` | [Routing](routing/ROUTING.md) | Dynamic Routes |
| Create a shared header/footer | [Layouts](routing/LAYOUTS.md) | Creating Layouts |
| Manage form state | [State Patterns](data-server/STATE_PATTERNS.md) | Form State |
| Fetch data from database | [Server Actions](data-server/SERVER_ACTIONS.md) | Quick Start |
| Create a REST API | [API Routes](data-server/API_ROUTES.md) | HTTP Methods |
| Add authentication | [Middleware](advanced/MIDDLEWARE.md) | Auth Pattern |
| Show loading spinners | [Streaming & Suspense](rendering/STREAMING_SUSPENSE.md) | Suspense |
| Optimize images | [Image Optimization](optimization/IMAGE_OPTIMIZATION.md) | Quick Start |
| Deploy to production | [Deployment](production/DEPLOYMENT.md) | Docker/Cloud |
| Add keyboard shortcuts | [Keyboard](features/KEYBOARD.md) | Basic Usage |
| Implement dark mode | [Theme](features/THEME.md) | Setup Step-by-Step |
| Persist user preferences | [Storage](features/STORAGE.md) | use_storage API |
| Trap focus in modals | [Focus](features/FOCUS.md) | Focus Trap |
| Organize routes without affecting URLs | [Route Groups](features/ROUTE_GROUPS.md) | Quick Start |
| Add page transitions | [Template](features/TEMPLATE.md) | Animation Config |
| Create custom error pages | [Error Pages](features/ERROR_PAGES.md) | Error Decorators |
| Use `src/` folder structure | [Project Structure](features/PROJECT_STRUCTURE.md) | Auto-Detection |
| Configure environment variables | [Environment](features/ENVIRONMENT.md) | Quick Start |
| Validate env in production | [Environment](features/ENVIRONMENT.md) | Schema Validation |
| Configure route caching | [Route Config](features/ROUTE_CONFIG.md) | Quick Start |
| Use ISR with tags | [Route Config](features/ROUTE_CONFIG.md) | Cache Tags |
| Run on edge runtime | [Route Config](features/ROUTE_CONFIG.md) | Edge Runtime |

### Key Concepts Glossary

| Term | Meaning | Learn More |
|------|---------|------------|
| **Signal** | Reactive value container | [State Management](core-concepts/STATE_MANAGEMENT.md) |
| **Store** | Nested reactive object | [State Management](core-concepts/STATE_MANAGEMENT.md) |
| **Computed** | Derived value (auto-updates) | [State Management](core-concepts/STATE_MANAGEMENT.md) |
| **Effect** | Side effect on state change | [State Management](core-concepts/STATE_MANAGEMENT.md) |
| **Hydration** | Making HTML interactive | [Hydration](core-concepts/HYDRATION.md) |
| **Island** | Isolated interactive component | [Islands](rendering/ISLANDS.md) |
| **Suspense** | Loading boundary | [Streaming](rendering/STREAMING_SUSPENSE.md) |
| **ISR** | Incremental Static Regeneration | [ISR](rendering/ISR.md) |
| **Server Action** | Server function callable from client | [Server Actions](data-server/SERVER_ACTIONS.md) |
| **Middleware** | Request interceptor | [Middleware](advanced/MIDDLEWARE.md) |
| **@on_keydown** | Keyboard shortcut decorator | [Keyboard](features/KEYBOARD.md) |
| **use_storage** | Persistent localStorage signal | [Storage](features/STORAGE.md) |
| **FocusTrap** | Keep focus inside a container | [Focus](features/FOCUS.md) |
| **ThemeProvider** | Dark mode context provider | [Theme](features/THEME.md) |
| **Route Group** | Folder wrapped in `()` for URL organization | [Route Groups](features/ROUTE_GROUPS.md) |
| **Template** | Layout that remounts on navigation | [Template](features/TEMPLATE.md) |
| **UnauthorizedError** | 401 error for unauthenticated users | [Error Pages](features/ERROR_PAGES.md) |
| **ForbiddenError** | 403 error for unauthorized users | [Error Pages](features/ERROR_PAGES.md) |
| **ProjectPaths** | Resolved paths for pages/components/lib | [Project Structure](features/PROJECT_STRUCTURE.md) |
| **env** | Singleton for environment variable access | [Environment](features/ENVIRONMENT.md) |
| **EnvSchema** | Schema validator for environment vars | [Environment](features/ENVIRONMENT.md) |
| **PYNEXT_PUBLIC_*** | Prefix for client-exposed env vars | [Environment](features/ENVIRONMENT.md) |
| **RouteConfig** | Per-route rendering and caching config | [Route Config](features/ROUTE_CONFIG.md) |
| **@route_config** | Decorator for route configuration | [Route Config](features/ROUTE_CONFIG.md) |
| **Dynamic** | Enum for rendering mode (auto/force/static) | [Route Config](features/ROUTE_CONFIG.md) |
| **revalidate** | ISR timing in seconds | [Route Config](features/ROUTE_CONFIG.md) |
| **@sitemap** | Decorator to include page in sitemap | [Sitemap](features/SITEMAP.md) |
| **SitemapGenerator** | Class to generate sitemap XML | [Sitemap](features/SITEMAP.md) |
| **RobotsConfig** | Configuration for robots.txt | [Sitemap](features/SITEMAP.md) |
| **get_sitemap_params** | Function to provide dynamic route params | [Sitemap](features/SITEMAP.md) |
| **PWAManifest** | Configuration for manifest.json | [PWA](features/PWA.md) |
| **Icon** | App icon configuration | [PWA](features/PWA.md) |
| **IconDetector** | Auto-detect icons from public/ | [PWA](features/PWA.md) |
| **Shortcut** | PWA app shortcuts | [PWA](features/PWA.md) |
| **OGCanvas** | Canvas for building OG images | [OG Images](features/OG_IMAGES.md) |
| **OGTemplate** | Pre-defined OG image template | [OG Images](features/OG_IMAGES.md) |
| **@og_image** | Decorator for OG image generation | [OG Images](features/OG_IMAGES.md) |
| **OGRenderer** | Pillow-based image renderer | [OG Images](features/OG_IMAGES.md) |

---

## 💡 Tips for Reading the Docs

1. **Start with analogies** - Each doc begins with first-principle explanations
2. **Look for diagrams** - ASCII diagrams visualize complex concepts
3. **Copy-paste examples** - All code examples are ready to use
4. **Follow learning paths** - Don't try to read everything at once
5. **Use the glossary** - If you see an unfamiliar term, check above

---

## 🤝 Contributing to Docs

Found an error or want to improve the docs?

1. Each doc follows a consistent structure:
   - Overview with analogy
   - Mental model / first principles
   - Code examples with detailed comments
   - Best practices
   - API reference

2. When adding examples, include:
   - What the code does
   - Why it works that way
   - Common gotchas

---

## 📊 Documentation Stats

| Category | Documents | Folder |
|----------|-----------|--------|
| Getting Started | 3 | `getting-started/` |
| Core Concepts | 3 | `core-concepts/` |
| Routing & Navigation | 5 | `routing/` |
| Data & Server | 4 | `data-server/` |
| Rendering Strategies | 5 | `rendering/` |
| Advanced Features | 3 | `advanced/` |
| Optimization | 4 | `optimization/` |
| Client Runtime & File Conventions | 17 | `features/` |
| Integrations | 2 | `integrations/` |
| Production | 2 | `production/` |
| Reference | 1 | `reference/` |
| **Total** | **44 documents** | **11 folders** |

---

*Happy building with PyNext! 🚀*
