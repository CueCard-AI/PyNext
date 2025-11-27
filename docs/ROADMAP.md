# PyNext Roadmap

This document tracks future enhancements and features for PyNext. Ideas captured here are not currently in development but represent the product vision.

---

## Future Enhancements

### Next.js Feature Parity

Achieving complete feature parity with Next.js while maintaining SolidJS principles (fine-grained reactivity, zero unnecessary JS, build-time optimization).

**Already Implemented**: `loading.py`, `error.py`, `not-found.py`, `layout.py`, `page.py`, `route.py`, dynamic routes, parallel routes, intercepting routes, `@island`, `Link()`, server actions, ISR, streaming, middleware, `Image()`, `Font()`, `Metadata` API, Tailwind utilities


#### Phase 2: Environment & Config (P0)

- [ ] **Environment Variables** — Full `.env` file support
  - Files: `pynext/env.py`, `pynext/build/env.py`
  - Load order: `.env` → `.env.local` → `.env.{mode}` → `.env.{mode}.local`
  - APIs: `env.DATABASE_URL`, `env.get_int()`, `env.get_bool()`, `env.get_list()`
  - Client: `PYNEXT_PUBLIC_*` vars exposed, build-time inlined

- [ ] **Route Segment Config** — Per-route configuration
  - Files: `pynext/core/route_config.py` (new)
  - APIs: `RouteConfig(dynamic="force-dynamic", revalidate=60, runtime="edge")`

#### Phase 3: SEO & Assets (P1)

- [ ] **Sitemap Generation** — Build-time `sitemap.xml`
  - Files: `pynext/seo/sitemap.py`
  - APIs: `@sitemap(changefreq="daily")`, custom `sitemap.py`

- [ ] **Robots.txt** — Configurable robots file
  - Files: `pynext/seo/robots.py`
  - APIs: `RobotsConfig`, `RobotsRule`

- [ ] **App Icons Convention** — Auto-detect favicon, icon.png, apple-icon.png
  - Files: Update `pynext/core/metadata.py`

- [ ] **PWA Manifest** — `manifest.json` generation
  - Files: `pynext/pwa/manifest.py`
  - APIs: `PWAManifest`, `ManifestIcon`

- [ ] **Dynamic OG Images** — Generate OG images at request time
  - Files: `pynext/seo/og_image.py`
  - APIs: `@og_image`, `generate_og_image()`
  - Implementation: Pillow-based, ISR-cached

#### Phase 4: Developer Experience (P1)

- [ ] **Fast File Watching** — <50ms dev reload
  - Files: Update `pynext/server/dev.py`, add `runtime/dev-reload.js`
  - Implementation: `watchfiles` (Rust), WebSocket push

- [ ] **Component Generator CLI** — Scaffold pages/components/APIs
  - Commands: `pynext generate page`, `pynext g component`, `pynext g api`

- [ ] **PyTest Utilities** — Testing helpers
  - Files: `pynext/testing/` module
  - APIs: `render_component()`, `assert_has_class()`, `assert_accessible()`

- [ ] **Linting Integration** — `pynext lint` with ruff
  - Commands: `pynext lint`, `pynext lint --fix`

#### Phase 5: Browser APIs (P1)

All return fine-grained signals (no component re-renders):

- [ ] **`use_websocket(url, on_message)`** → `WebSocketHandle`
- [ ] **`use_media_query("(max-width: 768px)")`** → `Signal[bool]`
- [ ] **`use_geolocation(watch=True)`** → `GeolocationHandle`
- [ ] **`use_clipboard()`** → `ClipboardHandle`
- [ ] **`use_window_size()`** → `Signal[WindowSize]`
- [ ] **`use_scroll_position()`** → `Signal[ScrollPosition]`
- [ ] **`use_intersection(element_id)`** → `Signal[bool]`

#### Phase 6: Advanced Features (P2)

- [ ] **MDX Support** — Markdown with components, `mdx-components.py`
- [ ] **Instrumentation** — `instrumentation.py`, OpenTelemetry
- [ ] **Proxy Configuration** — `proxy.py` for request rewrites
- [ ] **Edge Runtime** — Cloudflare, Vercel Edge, Deno adapters
- [ ] **CSS Modules** — `Component.module.css` with build-time scoping

#### Performance Targets

| Metric | Next.js | PyNext Target |
|--------|---------|---------------|
| JS Bundle (hello world) | ~80KB | <10KB |
| TTI | ~1.5s | <500ms |
| Build time | ~30s | <10s |
| Dev reload | ~300ms | <50ms |

#### Summary

| Phase | Features | New Files | Est. Tests |
|-------|----------|-----------|------------|
| 1 | File conventions | 6 | 80+ |
| 2 | Env & config | 4 | 50+ |
| 3 | SEO & assets | 8 | 60+ |
| 4 | Developer experience | 6 | 70+ |
| 5 | Browser APIs | 2 | 50+ |
| 6 | Advanced | 10 | 80+ |

**Total**: 36 new files, 390+ tests, ~18 days

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
- [ ] **Component generator CLI** — `pynext generate component MyButton`
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

