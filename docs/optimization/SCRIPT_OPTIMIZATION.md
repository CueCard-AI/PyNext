# PyNext Script Optimization

> **Zero Wrapper JavaScript • Native Browser Loading • Build-Time Analysis**

## Overview

PyNext's script optimization eliminates the JavaScript overhead that other frameworks introduce for script management. While Next.js ships ~2KB of runtime JavaScript just to load your scripts, PyNext uses native browser attributes and generates pure HTML.

| Feature | Next.js | PyNext |
|---------|---------|--------|
| **Wrapper JS** | ~2KB runtime | **0 KB** |
| **Loading Strategies** | JS-managed | **Native browser attributes** |
| **Preload Hints** | Runtime injection | **Build-time generation** |
| **Dependency Resolution** | Runtime | **Build-time topological sort** |
| **Async Safety Detection** | None | **Static analysis** |
| **SRI Hashes** | Manual | **Auto-generated at build** |

## SolidJS Principles Applied

### 1. Zero JavaScript for Script Loading
```python
# This generates pure HTML - no wrapper JS shipped
Script(src="/js/app.js", strategy="afterInteractive")

# Output: <script src="/js/app.js" defer></script>
```

### 2. Build-Time Work Over Runtime Processing
```
Build Phase:
  ├─ Analyze script dependencies
  ├─ Detect async-safe scripts
  ├─ Calculate SRI hashes
  ├─ Generate optimal load order
  └─ Create preload hints

Runtime:
  └─ Browser loads native <script> tags
```

### 3. Native Browser Features
- Uses `defer` and `async` attributes natively
- `<link rel="preload">` for critical scripts
- `<link rel="modulepreload">` for ES modules
- Browser handles scheduling automatically

### 4. Minimal JS Only When Necessary
```python
# These need zero wrapper JS:
Script(src="...", strategy="beforeInteractive")  # Native blocking
Script(src="...", strategy="afterInteractive")   # Native defer
Script(src="...", strategy="module")             # Native module

# These need minimal JS (for user interaction triggers):
Script(src="...", strategy="lazyOnload")  # ~300 bytes
Script(src="...", strategy="worker")      # ~100 bytes
```

---

## Quick Start

### Installation

```bash
# From GitHub (PyPI coming soon)
pip install git+https://github.com/CueCard-AI/PyNext.git
```

No additional dependencies required for script optimization.

### Basic Usage

```python
from pynext import Script
from pynext.html import html, head, body, div

def Page():
    # Register scripts - they're collected and rendered optimally
    Script(src="/js/app.js")
    Script(src="/js/analytics.js", strategy="lazyOnload")
    
    return div()["My Page Content"]
```

### Build Command

```bash
pynext build --pages ./pages --static ./public --output ./dist

# Output:
# [PyNext] Building for production...
# [PyNext] Analyzing scripts...
# [PyNext] Analyzed 5 scripts:
# [PyNext]   → Zero wrapper overhead
# [PyNext]   → Native loading strategies
# [PyNext] Build complete: dist
```

---

## Loading Strategies

PyNext provides five loading strategies that map directly to optimal browser behavior:

### Strategy Comparison

| Strategy | When It Loads | Browser API | JS Overhead |
|----------|---------------|-------------|-------------|
| `beforeInteractive` | Immediately, blocking | `<script>` in head | **0 bytes** |
| `afterInteractive` | After DOM ready | `<script defer>` | **0 bytes** |
| `module` | Async, respects imports | `<script type="module">` | **0 bytes** |
| `lazyOnload` | On idle/interaction | `requestIdleCallback` | ~300 bytes |
| `worker` | In Web Worker | `new Worker()` | ~100 bytes |

### Strategy Details

#### 1. `beforeInteractive` - Critical Blocking Scripts

```python
Script(src="/js/polyfills.js", strategy="beforeInteractive")
```

**Generated HTML:**
```html
<head>
  <script src="/js/polyfills.js"></script>
</head>
```

**Use for:**
- Polyfills that must load before any other code
- Critical inline configurations
- Scripts that other scripts depend on synchronously

**Performance Impact:**
- ⚠️ Blocks page rendering until loaded
- Use sparingly and only for truly critical scripts

---

#### 2. `afterInteractive` - Standard Deferred Scripts (Default)

```python
Script(src="/js/app.js", strategy="afterInteractive")
# or simply:
Script(src="/js/app.js")  # afterInteractive is the default
```

**Generated HTML:**
```html
<script src="/js/app.js" defer></script>
```

**Use for:**
- Main application JavaScript
- Feature enhancements
- Interactive components

**Performance Impact:**
- ✅ Doesn't block page rendering
- ✅ Executes after DOM is parsed
- ✅ Maintains execution order

---

#### 3. `module` - ES Module Scripts

```python
Script(src="/js/app.mjs", strategy="module")
```

**Generated HTML:**
```html
<script type="module" src="/js/app.mjs"></script>
```

**Use for:**
- Modern ES module code
- Code with `import`/`export` statements
- Tree-shakeable libraries

**Performance Impact:**
- ✅ Async by default
- ✅ Respects import dependencies
- ✅ Enables modulepreload optimization

---

#### 4. `lazyOnload` - Lazy Loading on Idle/Interaction

```python
Script(src="/js/analytics.js", strategy="lazyOnload")
```

**Generated HTML:**
```html
<script>
(function() {
  var lazyScripts = [{"src": "/js/analytics.js"}];
  var loaded = false;
  
  function loadScripts() {
    if (loaded) return;
    loaded = true;
    
    lazyScripts.forEach(function(script) {
      var el = document.createElement('script');
      el.src = script.src;
      document.body.appendChild(el);
    });
  }
  
  // Load on idle
  if ('requestIdleCallback' in window) {
    requestIdleCallback(loadScripts, { timeout: 3000 });
  } else {
    setTimeout(loadScripts, 2000);
  }
  
  // Also load on first interaction
  ['mouseover', 'touchstart', 'scroll', 'keydown'].forEach(function(event) {
    document.addEventListener(event, loadScripts, { once: true, passive: true });
  });
})();
</script>
```

**Use for:**
- Analytics and tracking
- Chat widgets
- Social media embeds
- Non-critical third-party scripts

**Performance Impact:**
- ✅ Zero impact on initial page load
- ✅ Loads during browser idle time
- ✅ Or loads on first user interaction
- ⚠️ Requires ~300 bytes of inline JS

---

#### 5. `worker` - Web Worker Scripts

```python
Script(src="/js/heavy-computation.js", strategy="worker")
```

**Generated HTML:**
```html
<script>
(function() {
  var workerScripts = ["/js/heavy-computation.js"];
  
  if ('Worker' in window) {
    workerScripts.forEach(function(src) {
      try {
        new Worker(src);
      } catch (e) {
        console.warn('Failed to create worker:', e);
      }
    });
  }
})();
</script>
```

**Use for:**
- CPU-intensive computations
- Data processing
- Background sync
- Crypto operations

**Performance Impact:**
- ✅ Runs on separate thread
- ✅ Doesn't block main thread
- ⚠️ Requires ~100 bytes of inline JS
- ⚠️ Limited DOM access

---

## Strategy Decision Flowchart

```
                    ┌─────────────────────────────┐
                    │   Does the script need to   │
                    │   run before page renders?  │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                   YES                           NO
                    │                             │
                    ▼                             ▼
        ┌───────────────────┐      ┌─────────────────────────┐
        │ beforeInteractive │      │ Is it an ES module with │
        │   (blocking)      │      │   import/export?        │
        └───────────────────┘      └────────────┬────────────┘
                                                │
                                   ┌────────────┴────────────┐
                                   │                         │
                                  YES                       NO
                                   │                         │
                                   ▼                         ▼
                        ┌──────────────────┐    ┌─────────────────────────┐
                        │     module       │    │ Is it CPU-intensive and │
                        │  (async module)  │    │   can run in worker?    │
                        └──────────────────┘    └────────────┬────────────┘
                                                             │
                                                ┌────────────┴────────────┐
                                                │                         │
                                               YES                       NO
                                                │                         │
                                                ▼                         ▼
                                    ┌───────────────────┐    ┌─────────────────────────┐
                                    │      worker       │    │ Is it non-critical      │
                                    │   (Web Worker)    │    │   (analytics, chat)?    │
                                    └───────────────────┘    └────────────┬────────────┘
                                                                          │
                                                             ┌────────────┴────────────┐
                                                             │                         │
                                                            YES                       NO
                                                             │                         │
                                                             ▼                         ▼
                                                 ┌───────────────────┐    ┌───────────────────┐
                                                 │    lazyOnload     │    │  afterInteractive │
                                                 │   (idle/interact) │    │     (defer)       │
                                                 └───────────────────┘    └───────────────────┘
```

---

## Core API

### `Script()` - The Main Component

```python
from pynext import Script

Script(
    src="/js/app.js",                    # External script URL
    strategy="afterInteractive",          # Loading strategy
    inline=None,                          # Inline script content
    type="text/javascript",               # Script type
    id="my-script",                       # Element ID
    async_=False,                         # async attribute
    defer=True,                           # defer attribute
    nomodule=False,                       # nomodule fallback
    crossorigin="anonymous",              # CORS setting
    integrity="sha384-...",               # SRI hash
    nonce="abc123",                       # CSP nonce
    referrerpolicy="no-referrer",         # Referrer policy
    preload=True,                         # Add preload link
    on_load="console.log('loaded')",      # onload handler
    on_error="console.error('failed')",   # onerror handler
)
```

### Helper Functions

#### `InlineScript()` - Inline JavaScript

```python
from pynext.core.script import InlineScript

InlineScript("""
    console.log('Page loaded');
    window.APP_CONFIG = { debug: true };
""")
```

#### `ModuleScript()` - ES Modules

```python
from pynext.core.script import ModuleScript

ModuleScript("/js/app.mjs", preload=True)
```

**Generated HTML:**
```html
<link rel="modulepreload" href="/js/app.mjs" crossorigin="anonymous" />
<script type="module" src="/js/app.mjs" crossorigin="anonymous"></script>
```

#### `AnalyticsScript()` - Analytics (Lazy)

```python
from pynext.core.script import AnalyticsScript

AnalyticsScript("https://www.googletagmanager.com/gtag/js?id=G-XXXXX")
```

#### `WorkerScript()` - Web Workers

```python
from pynext.core.script import WorkerScript

WorkerScript("/workers/image-processor.js")
```

#### `ImportMap()` - ES Module Import Maps

```python
from pynext.core.script import ImportMap

ImportMap({
    "lodash": "https://cdn.skypack.dev/lodash",
    "react": "https://cdn.skypack.dev/react",
    "@/components/": "/js/components/",
})
```

**Generated HTML:**
```html
<script type="importmap">
{
  "imports": {
    "lodash": "https://cdn.skypack.dev/lodash",
    "react": "https://cdn.skypack.dev/react",
    "@/components/": "/js/components/"
  }
}
</script>
```

---

## HTML Integration

### Getting Scripts for Page Rendering

```python
from pynext.core.script import get_head_scripts, get_body_scripts, clear_scripts

def render_page(content):
    return f"""
<!DOCTYPE html>
<html>
<head>
    {get_head_scripts()}  <!-- Preloads + beforeInteractive -->
</head>
<body>
    {content}
    {get_body_scripts()}  <!-- afterInteractive + lazy + worker -->
</body>
</html>
"""
```

### Output Locations

```
<head>
  <!-- Preload hints (generated at build) -->
  <link rel="preload" as="script" href="/js/app.js" />
  <link rel="modulepreload" href="/js/module.mjs" />
  
  <!-- beforeInteractive scripts -->
  <script src="/js/polyfills.js"></script>
</head>
<body>
  <!-- Page content -->
  
  <!-- afterInteractive scripts (at end of body) -->
  <script src="/js/app.js" defer></script>
  
  <!-- module scripts -->
  <script type="module" src="/js/module.mjs"></script>
  
  <!-- lazyOnload scripts (loader code) -->
  <script>
    (function() { /* requestIdleCallback loader */ })();
  </script>
  
  <!-- worker scripts (worker creator) -->
  <script>
    (function() { /* Worker creator */ })();
  </script>
</body>
```

---

## Build-Time Analysis

### ScriptOptimizer

The build-time optimizer analyzes all scripts and generates metadata:

```python
from pynext.bundler.scripts import ScriptOptimizer, ScriptOptimizerConfig

optimizer = ScriptOptimizer(ScriptOptimizerConfig(
    output_dir=Path("dist/_scripts"),
    cache_dir=Path(".pynext/script-cache"),
    calculate_sri=True,
    analyze_dependencies=True,
    bundle_scripts=False,
    minify=True,
    generate_source_maps=True,
    parallel_analysis=4,
))

analyses = optimizer.optimize_scripts(project_root=Path("."))
```

### What Gets Analyzed

For each script, the optimizer extracts:

```python
@dataclass
class ScriptAnalysis:
    src: str              # Script path
    hash: str             # Content hash for caching
    size: int             # Size in bytes
    dependencies: List[str]   # Import dependencies
    exports: List[str]        # Exported symbols
    is_module: bool           # ES module or classic
    is_async_safe: bool       # Can use async/defer
    sri_hash: Optional[str]   # Subresource Integrity hash
    load_time_estimate: float # Estimated load time (ms)
```

### Dependency Detection

The optimizer finds:

```javascript
// ES imports
import { something } from './module.js';
import * as utils from './utils.js';

// Dynamic imports
const module = await import('./lazy.js');

// CommonJS requires
const lib = require('./lib.js');
```

### Async Safety Detection

Scripts are marked as **not** async-safe if they contain:

```javascript
// These patterns require synchronous loading:
document.write('...');           // ❌ Blocks parsing
document.writeln('...');         // ❌ Blocks parsing
document.getElementById('x');     // ❌ May not exist yet
window.onload = function() {};   // ❌ Legacy handler
```

### SRI Hash Generation

```python
# SHA-384 hash for Subresource Integrity
integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
```

---

## Build-Time Workflow

```
                              BUILD TIME
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │   Script()      │──────────────────┐                                     │
│  │   calls in      │                  │                                     │
│  │   components    │                  ▼                                     │
│  └─────────────────┘         ┌─────────────────┐                            │
│                              │ ScriptRegistry  │                            │
│                              │                 │                            │
│                              │ - Deduplication │                            │
│                              │ - Strategy sort │                            │
│                              │ - Order tracking│                            │
│                              └────────┬────────┘                            │
│                                       │                                     │
│                                       ▼                                     │
│                           ┌───────────────────────┐                         │
│                           │   ScriptOptimizer     │                         │
│                           │                       │                         │
│                           │  ┌─────────────────┐  │                         │
│                           │  │ Parallel        │  │                         │
│                           │  │ Analysis        │  │                         │
│                           │  └────────┬────────┘  │                         │
│                           │           │           │                         │
│                           │           ▼           │                         │
│                           │  ┌─────────────────┐  │                         │
│                           │  │ For each script │  │                         │
│                           │  │                 │  │                         │
│                           │  │ 1. Parse imports│  │                         │
│                           │  │ 2. Parse exports│  │                         │
│                           │  │ 3. Check async  │  │                         │
│                           │  │ 4. Calculate SRI│  │                         │
│                           │  │ 5. Estimate time│  │                         │
│                           │  └────────┬────────┘  │                         │
│                           │           │           │                         │
│                           │           ▼           │                         │
│                           │  ┌─────────────────┐  │                         │
│                           │  │ Topological     │  │                         │
│                           │  │ Sort for order  │  │                         │
│                           │  └────────┬────────┘  │                         │
│                           │           │           │                         │
│                           │           ▼           │                         │
│                           │  ┌─────────────────┐  │                         │
│                           │  │ Generate        │  │                         │
│                           │  │ Preload Hints   │  │                         │
│                           │  └─────────────────┘  │                         │
│                           └───────────┬───────────┘                         │
│                                       │                                     │
│                                       ▼                                     │
│                           ┌───────────────────────┐                         │
│                           │   ScriptAnalysis[]    │                         │
│                           │                       │                         │
│                           │ - Optimal load order  │                         │
│                           │ - Preload links       │                         │
│                           │ - SRI hashes          │                         │
│                           │ - Async flags         │                         │
│                           └───────────────────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │
                              RUNTIME  │
┌──────────────────────────────────────┼──────────────────────────────────────┐
│                                      ▼                                      │
│  <head>                                                                     │
│    <link rel="preload" as="script" href="/js/app.js" />                     │
│    <script src="/js/polyfills.js"></script>                                 │
│  </head>                                                                    │
│  <body>                                                                     │
│    <!-- content -->                                                         │
│    <script src="/js/app.js" defer></script>                                 │
│    <script type="module" src="/js/module.mjs"></script>                     │
│  </body>                                                                    │
│                                                                             │
│  (Pure HTML - Zero Wrapper JavaScript)                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Dependency Resolution

### Topological Sort

When scripts have dependencies, the optimizer ensures correct load order:

```python
optimizer.get_optimal_load_order(analyses)

# Input dependencies:
#   app.js imports from utils.js
#   utils.js imports from config.js
#   feature.js imports from app.js

# Output order:
#   1. config.js
#   2. utils.js
#   3. app.js
#   4. feature.js
```

### Circular Dependency Handling

```python
# If A imports B, and B imports A:
# Optimizer detects cycle and breaks it gracefully
# Warning is logged, scripts load in registration order
```

---

## Preload Hint Generation

### Automatic Preload Links

```python
hints = optimizer.generate_preload_hints(analyses, priority_threshold=500.0)

# Generates:
# <link rel="preload" as="script" href="/js/critical.js" integrity="sha384-..." crossorigin="anonymous" />
# <link rel="modulepreload" href="/js/module.mjs" integrity="sha384-..." crossorigin="anonymous" />
```

### Priority Threshold

Scripts are preloaded if their estimated load time is **below** the threshold:
- Small, critical scripts get preloaded
- Large, non-critical scripts don't waste bandwidth

```python
# Script is 10KB → ~200ms estimated load time → PRELOAD
# Script is 100KB → ~2000ms estimated load time → NO PRELOAD
```

---

## Script Bundling (Optional)

For production, scripts can be bundled using esbuild:

```python
optimizer.bundle_scripts(
    scripts=["/js/app.js", "/js/utils.js", "/js/feature.js"],
    output_path=Path("dist/bundle.js"),
    minify=True,
)
```

### When to Bundle

| Scenario | Recommendation |
|----------|----------------|
| Many small scripts | Bundle together |
| HTTP/2 available | Keep separate (multiplexing) |
| Frequent updates to one file | Keep separate (caching) |
| Shared dependencies | Bundle shared code |

---

## CLI Integration

### Build Command

```bash
pynext build --pages ./pages --static ./public --output ./dist
```

### Build Output

```
[PyNext] Building for production...
[PyNext] Bundled 5 npm packages
[PyNext] Processing images...
[PyNext] Processing fonts...
[PyNext] Analyzing scripts...
[PyNext] Analyzed 8 scripts:
[PyNext]   → Zero wrapper overhead
[PyNext]   → Native loading strategies
[PyNext] Build complete: dist
```

### Script Analysis Cache

```
.pynext/
└── script-cache/
    ├── a1b2c3d4e5f6.json   # Cached analysis (by content hash)
    ├── b2c3d4e5f6a1.json
    └── ...
```

Subsequent builds skip analysis for unchanged scripts.

---

## Performance Comparison

### Bundle Size

| Framework | Script Loader JS | Notes |
|-----------|------------------|-------|
| Next.js | ~2KB | `next/script` runtime |
| Nuxt | ~1.5KB | `useScript` composable |
| Gatsby | ~1KB | Script loader |
| **PyNext** | **0 KB** | Native browser attributes |

### Loading Performance

| Metric | JS-Managed Loading | PyNext Native Loading |
|--------|--------------------|-----------------------|
| First Contentful Paint | Delayed by loader | **Immediate** |
| Time to Interactive | Loader overhead | **Direct execution** |
| Main Thread Blocking | Loader execution | **None** |
| Hydration Dependency | Required | **None** |

### Lazy Loading Comparison

| Approach | JS Size | Triggers |
|----------|---------|----------|
| Next.js `lazyOnload` | ~500 bytes | Intersection Observer |
| PyNext `lazyOnload` | **~300 bytes** | `requestIdleCallback` + events |

---

## Best Practices

### 1. Use the Right Strategy

```python
# ❌ Loading analytics in head
Script(src="/analytics.js", strategy="beforeInteractive")

# ✅ Load analytics lazily
Script(src="/analytics.js", strategy="lazyOnload")
```

### 2. Preload Critical Scripts

```python
# ✅ Preload scripts needed for initial interaction
Script(src="/js/app.js", preload=True)
```

### 3. Use Modules for Modern Code

```python
# ❌ Classic script for module code
Script(src="/js/app.mjs")

# ✅ Use module strategy
Script(src="/js/app.mjs", strategy="module")
```

### 4. Add SRI for Third-Party Scripts

```python
# ✅ Include integrity hash
Script(
    src="https://cdn.example.com/lib.js",
    integrity="sha384-oqVuAfXRKap7...",
    crossorigin="anonymous",
)
```

### 5. Offload Heavy Work to Workers

```python
# ❌ Running crypto on main thread
Script(src="/js/crypto-heavy.js")

# ✅ Run in Web Worker
Script(src="/js/crypto-heavy.js", strategy="worker")
```

### 6. Use Import Maps for CDN Modules

```python
# ✅ Clean imports in your code
ImportMap({
    "lodash": "https://cdn.skypack.dev/lodash",
    "react": "https://cdn.skypack.dev/react",
})

# Then in your JS:
# import { debounce } from 'lodash';
```

---

## Troubleshooting

### Scripts Not Loading

1. **Check strategy placement:**
   ```python
   # beforeInteractive goes in <head>
   # afterInteractive goes at end of <body>
   ```

2. **Verify script path:**
   ```python
   # Paths starting with / are relative to static directory
   Script(src="/js/app.js")  # Looks in static/js/app.js
   ```

3. **Check console for errors:**
   - 404 for missing scripts
   - CORS errors for cross-origin scripts

### Lazy Scripts Loading Too Early

```python
# Increase idle timeout
# (Modify the lazyOnload generator in script.py if needed)
```

### Worker Script Failures

```python
# Workers can't access DOM
# Check browser console for Worker errors
# Ensure Worker script doesn't use document/window
```

### SRI Mismatch

```python
# SRI hash must match exact content
# Regenerate hash after any script changes
pynext build  # Recalculates all SRI hashes
```

---

## Architecture

### File Structure

```
pynext/
├── core/
│   └── script.py              # Script component and registry
│       ├── ScriptStrategy     # Loading strategies enum
│       ├── ScriptType         # Script types enum
│       ├── ScriptConfig       # Script configuration
│       ├── ScriptRegistry     # Global script storage
│       ├── Script()           # Main component
│       ├── InlineScript()     # Inline helper
│       ├── ModuleScript()     # Module helper
│       ├── AnalyticsScript()  # Analytics helper
│       ├── WorkerScript()     # Worker helper
│       ├── ImportMap()        # Import map helper
│       ├── get_head_scripts() # Head output
│       └── get_body_scripts() # Body output
│
├── bundler/
│   └── scripts.py             # Build-time optimizer
│       ├── ScriptAnalysis     # Analysis result
│       ├── ScriptOptimizerConfig  # Config options
│       ├── ScriptOptimizer    # Main optimizer
│       │   ├── optimize_scripts()     # Analyze all
│       │   ├── get_optimal_load_order()  # Dependency sort
│       │   ├── generate_preload_hints()  # Preload links
│       │   └── bundle_scripts()       # esbuild bundling
│       └── optimize_scripts_for_build()  # CLI entry
│
└── cli.py                     # Build command integration
```

### Data Flow

```
                    Component Code                    Build Time
                         │                                │
                         ▼                                │
                 ┌───────────────┐                        │
                 │   Script()    │                        │
                 └───────┬───────┘                        │
                         │                                │
                         ▼                                │
                 ┌───────────────┐                        │
                 │ScriptRegistry │◄────────────────────────
                 │               │     analyze_scripts()  │
                 │ _scripts: {}  │                        │
                 │ _load_order[] │                        │
                 └───────┬───────┘                        │
                         │                                │
           ┌─────────────┼─────────────┐                  │
           │             │             │                  │
           ▼             ▼             ▼                  │
    ┌──────────┐  ┌──────────┐  ┌──────────┐              │
    │  HEAD    │  │  BODY    │  │  LAZY    │              │
    │ scripts  │  │ scripts  │  │ scripts  │              │
    └──────────┘  └──────────┘  └──────────┘              │
           │             │             │                  │
           │             │             │                  │
           ▼             ▼             ▼                  │
    ┌─────────────────────────────────────────┐           │
    │              HTML Output                │           │
    │                                         │           │
    │  <head>                                 │           │
    │    <link rel="preload" .../>            │◄──────────┘
    │    <script src="..."></script>          │   preload hints
    │  </head>                                │
    │  <body>                                 │
    │    <script defer ...></script>          │
    │    <script type="module" ...></script>  │
    │    <script>/* lazy loader */</script>   │
    │  </body>                                │
    └─────────────────────────────────────────┘
```

---

## API Reference

### Components

| Function | Purpose | Returns |
|----------|---------|---------|
| `Script(...)` | Register a script | `""` (empty string) |
| `InlineScript(code, strategy)` | Inline JavaScript | `""` |
| `ModuleScript(src, ...)` | ES module script | `""` |
| `AnalyticsScript(src, id)` | Lazy analytics | `""` |
| `WorkerScript(src)` | Web Worker | `""` |
| `ImportMap(imports, scopes)` | Import map | `""` |

### Registry Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `get_script_registry()` | Get global registry | `ScriptRegistry` |
| `get_head_scripts()` | Get head HTML | `str` |
| `get_body_scripts()` | Get body HTML | `str` |
| `clear_scripts()` | Clear registry | `None` |

### Optimizer Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `optimize_scripts_for_build(project_root, config)` | Analyze all scripts | `Dict[str, ScriptAnalysis]` |
| `generate_script_manifest(analyses, output_path)` | Create manifest file | `None` |

### Enums

| Enum | Values |
|------|--------|
| `ScriptStrategy` | `BEFORE_INTERACTIVE`, `AFTER_INTERACTIVE`, `LAZY_ONLOAD`, `WORKER`, `MODULE` |
| `ScriptType` | `JAVASCRIPT`, `MODULE`, `IMPORTMAP`, `JSON` |

### Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `output_dir` | `static/_scripts` | Output directory |
| `cache_dir` | `.pynext/script-cache` | Cache directory |
| `calculate_sri` | `True` | Generate SRI hashes |
| `analyze_dependencies` | `True` | Parse imports |
| `bundle_scripts` | `False` | Bundle with esbuild |
| `minify` | `True` | Minify bundles |
| `generate_source_maps` | `True` | Include source maps |
| `parallel_analysis` | `4` | Concurrent analysis |

---

## Summary

PyNext Script Optimization provides:

✅ **Zero Wrapper JavaScript** - Native `<script>` tags  
✅ **Five Loading Strategies** - beforeInteractive, afterInteractive, module, lazyOnload, worker  
✅ **Build-Time Analysis** - Dependencies, exports, async safety  
✅ **Automatic Preload Hints** - `<link rel="preload">` generation  
✅ **SRI Hash Calculation** - Subresource Integrity at build  
✅ **Dependency Ordering** - Topological sort for correct load order  
✅ **Incremental Builds** - Content-hash based caching  
✅ **Optional Bundling** - esbuild integration  
✅ **Import Map Support** - Modern ES module resolution  

**Result:** Fastest possible script loading with zero framework overhead.

