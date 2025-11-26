# Build System Internals

> **How PyNext optimizes JavaScript for production — minification, tree-shaking, and lazy loading**

This document explains how PyNext's build system transforms development code into optimized production bundles.

---

## Overview

### What Problem Does This Solve?

Development code is verbose and readable. Production code needs to be small and fast.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT vs PRODUCTION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DEVELOPMENT:                      PRODUCTION:                               │
│  ────────────                      ───────────                               │
│                                                                              │
│  // Initialize the dialog          d=e=>{const t=e.querySelector(           │
│  // component with focus           '[data-pynext-dialog]');if(t)            │
│  // trap and accessibility         {i(t);a(t)}}                             │
│  function initDialog(el) {                                                   │
│    const dialog = el.querySelector(                                          │
│      '[data-pynext-dialog]'        Size: 71 KB → 3 KB (96% smaller)         │
│    );                                                                        │
│    if (dialog) {                                                             │
│      trapFocus(dialog);                                                      │
│      setupA11y(dialog);                                                      │
│    }                                                                         │
│  }                                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Build Modes

### Development Mode (`pynext dev`)

- Full source code (readable)
- Source maps enabled
- `console.debug` statements included
- No minification
- Fast rebuilds

### Production Mode (`pynext build`)

- Minified code
- No source maps (by default)
- `console.debug` stripped
- Tree-shaken
- Optimized bundles

```bash
# Development
pynext dev      # Fast, readable, debug-friendly

# Production
pynext build    # Optimized, minimal, fast
```

---

## Minification

### How It Works

PyNext uses Terser for JavaScript minification:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MINIFICATION PROCESS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INPUT (development):                                                        │
│  ────────────────────                                                       │
│  /**                                                                         │
│   * Opens the dialog and traps focus                                         │
│   * @param {HTMLElement} element - The dialog element                        │
│   */                                                                         │
│  function openDialog(element) {                                              │
│    const content = element.querySelector('[data-pynext-dialog-content]');   │
│    const previouslyFocused = document.activeElement;                         │
│                                                                              │
│    content.style.display = 'block';                                          │
│    content.setAttribute('aria-hidden', 'false');                             │
│                                                                              │
│    console.debug('[PyNext Dialog] Opening:', element.id);                    │
│                                                                              │
│    const focusable = getFocusableElements(content);                          │
│    if (focusable.length > 0) {                                               │
│      focusable[0].focus();                                                   │
│    }                                                                         │
│  }                                                                           │
│                                                                              │
│  OUTPUT (production):                                                        │
│  ────────────────────                                                       │
│  function o(e){const t=e.querySelector('[data-pynext-dialog-content]'),     │
│  n=document.activeElement;t.style.display='block';t.setAttribute(           │
│  'aria-hidden','false');const a=f(t);a.length>0&&a[0].focus()}              │
│                                                                              │
│  Transformations:                                                            │
│  ────────────────                                                           │
│  ✓ Comments removed                                                          │
│  ✓ Variable names shortened (element → e, content → t)                       │
│  ✓ Whitespace removed                                                        │
│  ✓ console.debug removed                                                     │
│  ✓ Unused code eliminated                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Python Implementation

```python
# pynext/build/minify.py

import subprocess
import json

def minify_js(source: str, strip_debug: bool = True) -> str:
    """
    Minify JavaScript source code using Terser.
    
    Args:
        source: JavaScript source code
        strip_debug: Whether to remove console.debug calls
    
    Returns:
        Minified JavaScript
    """
    options = {
        "compress": {
            "dead_code": True,
            "drop_console": ["debug"] if strip_debug else False,
            "drop_debugger": True,
            "unused": True,
        },
        "mangle": {
            "toplevel": False,  # Keep global names
        },
        "format": {
            "comments": False,
        }
    }
    
    result = subprocess.run(
        ["npx", "terser", "--config-file", "-"],
        input=json.dumps(options) + "\n" + source,
        capture_output=True,
        text=True
    )
    
    return result.stdout
```

---

## Tree Shaking

### What Is Tree Shaking?

Tree shaking removes unused code from the final bundle:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TREE SHAKING                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Your Code:                        Runtime Modules:                          │
│  ──────────                        ────────────────                          │
│                                                                              │
│  from pynext import (              ┌─────────────────┐                      │
│    on_keydown,  ───────────────→   │  keyboard.js ✓  │ INCLUDED             │
│    use_theme    ───────────────→   │  theme.js    ✓  │ INCLUDED             │
│  )                                 │  storage.js  ✗  │ EXCLUDED             │
│                                    │  focus.js    ✗  │ EXCLUDED             │
│                                    │  sse.js      ✗  │ EXCLUDED             │
│                                    │  browser.js  ✗  │ EXCLUDED             │
│                                    └─────────────────┘                      │
│                                                                              │
│  Result: Only include keyboard.js and theme.js                               │
│  Savings: 4 modules × ~10KB = ~40KB saved                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# pynext/build/bundle.py

import ast
from pathlib import Path

# Map Python imports to JS runtime modules
IMPORT_TO_RUNTIME = {
    "on_keydown": "keyboard.js",
    "on_key_sequence": "keyboard.js",
    "ShortcutProvider": "keyboard.js",
    "use_theme": "theme.js",
    "ThemeProvider": "theme.js",
    "use_storage": "storage.js",
    "use_event_source": "sse.js",
    "use_visibility": "browser.js",
    "use_online": "browser.js",
}

def analyze_imports(python_source: str) -> set[str]:
    """
    Analyze Python source to find which runtime modules are needed.
    """
    tree = ast.parse(python_source)
    needed_runtimes = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("pynext"):
                for alias in node.names:
                    name = alias.name
                    if name in IMPORT_TO_RUNTIME:
                        needed_runtimes.add(IMPORT_TO_RUNTIME[name])
    
    return needed_runtimes

def create_bundle(project_dir: Path) -> str:
    """
    Create an optimized bundle with only needed runtimes.
    """
    needed = set()
    
    # Analyze all Python files
    for py_file in project_dir.glob("**/*.py"):
        source = py_file.read_text()
        needed.update(analyze_imports(source))
    
    # Always include core signal system
    needed.add("signals.js")
    
    # Concatenate needed modules
    bundle = []
    for runtime in needed:
        runtime_path = Path(__file__).parent.parent / "runtime" / runtime
        if runtime_path.exists():
            bundle.append(runtime_path.read_text())
    
    return "\n".join(bundle)
```

---

## Lazy Loading

### How It Works

UI components are loaded only when needed:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAZY LOADING FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Page with Button only:                                                      │
│  ──────────────────────                                                     │
│  <button>Click me</button>                                                   │
│                                                                              │
│  JavaScript loaded: 0 KB (Button needs no JS!)                               │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  Page with Dialog:                                                           │
│  ─────────────────                                                          │
│  <div data-pynext-dialog>...</div>                                           │
│                                                                              │
│  1. Page loads with static HTML                                              │
│  2. Loader scans for data-pynext-* attributes                                │
│  3. Finds data-pynext-dialog                                                 │
│  4. Dynamically imports dialog.js                                            │
│  5. Dialog becomes interactive                                               │
│                                                                              │
│  JavaScript loaded: core.js (1.5KB) + dialog.js (1KB) = 2.5 KB              │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  Page with Dialog AND DataTable:                                             │
│  ───────────────────────────────                                            │
│  core.js (1.5KB) + dialog.js (1KB) + datatable.js (2KB) = 4.5 KB            │
│                                                                              │
│  Only load what you use!                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```javascript
// runtime/ui/loader.js

// Component registry - lazy loaded
const COMPONENTS = {
  dialog:     () => import('./dialog.js'),
  dropdown:   () => import('./dropdown.js'),
  tabs:       () => import('./tabs.js'),
  accordion:  () => import('./accordion.js'),
  tooltip:    () => import('./tooltip.js'),
  popover:    () => import('./popover.js'),
  sheet:      () => import('./sheet.js'),
  combobox:   () => import('./combobox.js'),
  command:    () => import('./command.js'),
  calendar:   () => import('./calendar.js'),
  datatable:  () => import('./datatable.js'),
  fileupload: () => import('./fileupload.js'),
};

// Track loaded modules
const loaded = new Set();

async function loadComponent(name) {
  if (loaded.has(name)) return;
  
  const loader = COMPONENTS[name];
  if (!loader) return;
  
  console.debug(`[PyNext] Loading ${name}.js`);
  
  const module = await loader();
  loaded.add(name);
  
  return module;
}

async function initializeAll(root = document) {
  // Find all component types on the page
  const componentTypes = new Set();
  
  for (const name of Object.keys(COMPONENTS)) {
    if (root.querySelector(`[data-pynext-${name}]`)) {
      componentTypes.add(name);
    }
  }
  
  // Load and initialize each type
  for (const name of componentTypes) {
    const module = await loadComponent(name);
    
    const elements = root.querySelectorAll(`[data-pynext-${name}]`);
    for (const el of elements) {
      if (!el._pynextInit) {
        module.init(el);
        el._pynextInit = true;
      }
    }
  }
}
```

---

## Debug vs Production

### Debug Statements

Development includes helpful logging:

```javascript
// Development
console.debug('[PyNext Dialog] Opening dialog:', element.id);
console.debug('[PyNext Dialog] Focus trapped');
console.debug('[PyNext Signal] Value changed:', oldValue, '→', newValue);

// Production: ALL REMOVED
```

### Debug Stripping

```python
# pynext/build/minify.py

def strip_debug(source: str) -> str:
    """Remove console.debug statements from source."""
    import re
    
    # Remove console.debug(...) statements
    pattern = r'console\.debug\([^)]*\);?\s*'
    return re.sub(pattern, '', source)
```

---

## Build Pipeline

### Full Build Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BUILD PIPELINE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. ANALYZE                                                                  │
│     - Scan Python files for imports                                          │
│     - Determine needed runtime modules                                       │
│     - Check which UI components are used                                     │
│          ↓                                                                   │
│  2. TREE SHAKE                                                               │
│     - Exclude unused runtime modules                                         │
│     - Exclude unused UI components                                           │
│          ↓                                                                   │
│  3. MINIFY                                                                   │
│     - Run Terser on each module                                              │
│     - Strip console.debug                                                    │
│     - Mangle variable names                                                  │
│          ↓                                                                   │
│  4. BUNDLE                                                                   │
│     - Create core bundle (always loaded)                                     │
│     - Create component chunks (lazy loaded)                                  │
│          ↓                                                                   │
│  5. OUTPUT                                                                   │
│     static/                                                                  │
│     ├── pynext.min.js      (core: signals + loader)                         │
│     └── ui/                                                                  │
│         ├── dialog.min.js                                                    │
│         ├── dropdown.min.js                                                  │
│         └── ...                                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Python Implementation

```python
# pynext/build/__init__.py

from pathlib import Path
from .minify import minify_js, strip_debug
from .bundle import analyze_imports, create_bundle

def build(project_dir: Path, output_dir: Path, mode: str = "production"):
    """
    Build optimized JavaScript bundles.
    
    Args:
        project_dir: Path to user's project
        output_dir: Where to write output
        mode: "development" or "production"
    """
    is_prod = mode == "production"
    
    # Analyze which runtimes are needed
    needed_runtimes = analyze_imports(project_dir)
    
    # Build core bundle
    core_bundle = create_core_bundle(needed_runtimes)
    if is_prod:
        core_bundle = strip_debug(core_bundle)
        core_bundle = minify_js(core_bundle)
    
    (output_dir / "pynext.min.js").write_text(core_bundle)
    
    # Build UI component chunks
    ui_dir = output_dir / "ui"
    ui_dir.mkdir(exist_ok=True)
    
    for component_file in (RUNTIME_DIR / "ui").glob("*.js"):
        if component_file.name in ["core.js", "loader.js"]:
            continue  # These are in the core bundle
        
        source = component_file.read_text()
        if is_prod:
            source = strip_debug(source)
            source = minify_js(source)
        
        output_name = component_file.stem + ".min.js"
        (ui_dir / output_name).write_text(source)
    
    print(f"Build complete: {output_dir}")
```

---

## Size Tracking

### Measuring Bundle Size

```python
# scripts/check-bundle-size.py

from pathlib import Path

MAX_CORE_SIZE = 5 * 1024  # 5 KB
MAX_COMPONENT_SIZE = 3 * 1024  # 3 KB

def check_sizes(build_dir: Path):
    core = build_dir / "pynext.min.js"
    core_size = core.stat().st_size
    
    if core_size > MAX_CORE_SIZE:
        print(f"❌ Core bundle too large: {core_size} bytes (max {MAX_CORE_SIZE})")
        return False
    
    print(f"✓ Core bundle: {core_size} bytes")
    
    for component in (build_dir / "ui").glob("*.min.js"):
        size = component.stat().st_size
        if size > MAX_COMPONENT_SIZE:
            print(f"❌ {component.name} too large: {size} bytes")
            return False
        print(f"✓ {component.name}: {size} bytes")
    
    return True
```

---

## Key Files

| File | Purpose |
|------|---------|
| `pynext/build/__init__.py` | Build orchestration |
| `pynext/build/minify.py` | Terser wrapper |
| `pynext/build/bundle.py` | Tree-shaking and bundling |
| `pynext/cli.py` | `pynext build` command |
| `scripts/check-bundle-size.py` | CI size checks |

---

## Debugging the Build

### Inspect Output

```bash
# See what was generated
ls -la static/

# Check sizes
du -h static/*.js static/ui/*.js

# Verify minification worked
head -c 200 static/pynext.min.js
```

### Skip Minification

```bash
# For debugging, skip minification
pynext build --no-minify
```

### Source Maps

```bash
# Generate source maps for debugging
pynext build --source-maps
```

