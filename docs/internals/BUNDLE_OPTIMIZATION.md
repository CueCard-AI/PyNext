# PyNext Bundle Optimization Guide

## WHO Should Read This

**Primary Audience**: Developers optimizing PyNext bundle size
**Secondary Audience**: Contributors adding new runtime features
**Prerequisites**: Understanding of JavaScript bundling, gzip compression, tree-shaking
**Skill Level**: Intermediate to Advanced

---

## WHAT This Document Covers

This document explains how to achieve minimal bundle sizes for PyNext applications:

- Optimization techniques and their impact
- Compression strategies (gzip, brotli)
- Tree-shaking requirements
- Measurement methodology
- CI integration for bundle monitoring

### Key Metrics

| Metric | Description |
|--------|-------------|
| **Raw Size** | Uncompressed JavaScript bytes |
| **Gzip Size** | Standard HTTP compression (what browsers download) |
| **Brotli Size** | Modern compression (20% smaller than gzip) |

---

## WHY Bundle Size Matters

### Performance Impact

| Size (gzip) | Parse Time | Download (3G) | Download (4G) |
|-------------|------------|---------------|---------------|
| 1KB | ~1ms | 125ms | 10ms |
| 5KB | ~5ms | 625ms | 50ms |
| 13KB | ~15ms | 1.6s | 130ms |
| 50KB | ~60ms | 6.3s | 500ms |

Every KB adds ~1-2ms of parse time and significant download time on slow connections.

### PyNext Goals

| App Type | Target Size | Current Size | Status |
|----------|-------------|--------------|--------|
| Hello World | 500B | 12.3KB | ⚠️ 25x too large |
| Simple CRUD | 1.5KB | 12.3KB | ⚠️ 8x too large |
| Full App | 5KB | 13KB | ⚠️ 2.6x too large |

---

## HOW Optimization Works

### 1. Layered Architecture

Instead of one monolithic runtime, we split into layers:

```
                    ┌─────────────────────────────────────────────────────┐
                    │ Layer 3: Stdlib (~500B-1KB per module)              │
                    │   json, math, re, random                            │
                    │   Only loaded when imported                         │
                    └─────────────────────────────────────────────────────┘
                    ┌─────────────────────────────────────────────────────┐
                    │ Layer 2: Extended (~2KB)                             │
                    │   errors, dunders, generators                       │
                    │   Only loaded when used                             │
                    └─────────────────────────────────────────────────────┘
                    ┌─────────────────────────────────────────────────────┐
                    │ Layer 1: Type Methods (~1KB)                         │
                    │   str.*, list.*, dict.*, set.*                      │
                    │   Only loaded when methods used                     │
                    └─────────────────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────────────────────┐
│ Layer 0: Essential (~500B)                                                │
│   at, slice, bool, eq, mod, floordiv, range, len                          │
│   Always loaded (unavoidable Python differences)                          │
└───────────────────────────────────────────────────────────────────────────┘
```

### 2. Method Inlining

Simple methods become native JavaScript with zero runtime:

| Python | Before (runtime) | After (inlined) | Savings |
|--------|------------------|-----------------|---------|
| `s.upper()` | `__py.str.upper(s)` | `s.toUpperCase()` | 100% |
| `s.lower()` | `__py.str.lower(s)` | `s.toLowerCase()` | 100% |
| `s.strip()` | `__py.str.strip(s)` | `s.trim()` | 100% |
| `arr.append(x)` | `__py.list.append(arr, x)` | `arr.push(x)` | 100% |
| `arr.pop()` | `__py.list.pop(arr)` | `arr.pop()` | 100% |
| `d.keys()` | `__py.dict.keys(d)` | `Object.keys(d)` | 100% |
| `d.values()` | `__py.dict.values(d)` | `Object.values(d)` | 100% |

**Implementation**: See `pynext/transpiler/optimizer/inline.py`

### 3. Dynamic Error Factory

Replace 21 static exception classes with a tiny factory:

```javascript
// Before: ~1.5KB
export class ValueError extends Exception { ... }
export class TypeError extends Exception { ... }
export class KeyError extends Exception { ... }
// ... 18 more classes

// After: ~200B
const C = {};
export const E = n => C[n] || (C[n] = class extends Error { 
    constructor(m) { super(m); this.name = n; } 
});
```

**Savings**: 87% reduction for error handling

### 4. Operator Overloading On-Demand

Only emit dunder runtime calls when custom classes define operators:

```python
# No custom operators → direct JS
x = 1 + 2  # Emits: let x = 1 + 2;

# Custom operator class → runtime call
class Vector:
    def __add__(self, other): ...

v = v1 + v2  # Emits: let v = __py.dunders.add(v1, v2);
```

**Implementation**: See `pynext/transpiler/_internal/operator_tracker.py`

### 5. Stdlib Code Splitting

Each stdlib module is separate, loaded only when imported:

```javascript
// Before: All stdlib bundled together
import { json, math, re, random } from './stdlib/index.js';

// After: Dynamic imports
const json = await import('./stdlib/json.js');  // Only when needed
```

---

## WHEN to Apply Each Technique

### Always Apply

- Layer 0 for basic operations
- Method inlining for simple cases
- `sideEffects: false` in package.json

### Apply When Detected

- Operator tracking (only if custom operator classes exist)
- Error factory (only if exceptions are used)
- Stdlib splitting (only for imported modules)

### Never Apply

- Inlining complex methods (e.g., `str.split()` with whitespace handling)
- Skipping runtime for DOM APIs (already passthrough)

---

## WHERE Optimization Happens

### Transpile Time (Python → JavaScript)

| File | Optimization |
|------|--------------|
| `optimizer/inline.py` | Method inlining decisions |
| `_internal/operator_tracker.py` | Operator class detection |
| `_internal/usage_tracker.py` | Runtime feature tracking |
| `emitter.py` | Code generation |

### Build Time (Bundling)

| Tool | Optimization |
|------|--------------|
| esbuild | Minification, tree-shaking |
| package.json | `sideEffects: false` enables tree-shaking |
| rollup/webpack | Alternative bundlers |

### Runtime (Browser)

| Technique | Benefit |
|-----------|---------|
| Dynamic imports | Load stdlib on-demand |
| ES modules | Native browser tree-shaking |

---

## Measurement Methodology

### Tools

1. **Bundle Analyzer** (`scripts/analyze-bundle.js`)
   - Measures raw, gzip, brotli sizes
   - Tracks contributions per file
   - Enforces limits in CI

2. **esbuild Metafile**
   - Shows what's included in bundle
   - Identifies unexpected imports

3. **source-map-explorer**
   - Visualizes bundle composition
   - Identifies bloat sources

### Running Analysis

```bash
# Quick check against limits
make bundle-check

# Verbose analysis with breakdown
node scripts/analyze-bundle.js --verbose

# JSON output for CI
node scripts/analyze-bundle.js --json
```

### Output Example

```
📦 PyNext Bundle Size Analysis

══════════════════════════════════════════════════════════════════════
  Commit: local  |  Branch: local
══════════════════════════════════════════════════════════════════════

  Status  Bundle                      Gzip     Limit   Usage
──────────────────────────────────────────────────────────────────────
  ✅     layer0-minimal            799B    1.00KB    78%
  ✅     layer2-errors-factory      955B    1.17KB    80%
  ⚠️     layer2-errors-full      1.23KB    1.50KB    82%
  ⚠️     layer1-string-core      1.28KB    1.56KB    82%
  ✅     layer1-string-extended    1.28KB    3.50KB    37%
  ⚠️     transpiler-core        12.32KB   14.00KB    88%
  ⚠️     transpiler-full        13.17KB   15.00KB    88%
  ⚠️     transpiler-dunders      1.26KB    1.50KB    84%
  ✅     signals                 1.38KB    2.00KB    69%
  ✅     ui-core                   632B    1.00KB    62%
  ✅     ui-full                 5.72KB    8.00KB    71%
──────────────────────────────────────────────────────────────────────
  Total:                           39.97KB  (gzipped)
```

---

## CI Integration

### GitHub Actions Workflow

```yaml
bundle-size:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
    - run: npm ci
    - run: node scripts/analyze-bundle.js
    - name: Check limits
      run: |
        if jq -e '.failed' .bundle-analysis/bundle-report.json; then
          echo "❌ Bundle size limits exceeded!"
          exit 1
        fi
```

### PR Comments

The CI automatically posts bundle size comparisons on PRs:

```
## 📦 Bundle Size Report

| Bundle | Before | After | Diff |
|--------|--------|-------|------|
| layer0-minimal | 512B | 518B | 🟡 +6B |
| string-core | 623B | 623B | ⚪ — |
| transpiler-core | 12.3KB | 12.4KB | 🟡 +100B |
```

---

## Compression Details

### Gzip vs Brotli

| Compression | Compatibility | Size | Speed |
|-------------|---------------|------|-------|
| Gzip | Universal | Baseline | Fast |
| Brotli | Modern browsers | -20% | Slower |

### What Compresses Well

- Repetitive patterns (function boilerplate)
- Common keywords (`function`, `const`, `return`)
- Similar code structures

### What Compresses Poorly

- Random strings
- Already-minified code
- Unique variable names

### Optimization Tips

1. **Consistent naming** - helps compression
2. **Avoid code duplication** - wastes bytes
3. **Smaller functions** - more reusable patterns
4. **Constants instead of literals** - referenced multiple times

---

## Tree-Shaking Requirements

### For Tree-Shaking to Work

1. **ES modules only** - no CommonJS
2. **`sideEffects: false`** - in package.json
3. **No circular dependencies** - breaks analysis
4. **Named exports** - not default objects

### Good (Tree-Shakeable)

```javascript
// Named exports
export function split(s, sep) { ... }
export function join(arr, sep) { ... }
```

### Bad (Not Tree-Shakeable)

```javascript
// Default object export
export default {
    split(s, sep) { ... },
    join(arr, sep) { ... },
};
```

### Circular Dependencies

```javascript
// ❌ BAD: Circular
// core.js
import { ValueError } from './errors.js';

// errors.js
import { format } from './core.js';

// ✅ GOOD: Acyclic
// core.js - no imports from errors
export function format() { ... }

// errors.js
import { format } from './core.js';
```

---

## Size Budgets

### Per-Layer Budgets

| Layer | Target | Max | Action if Exceeded |
|-------|--------|-----|-------------------|
| Layer 0 | 500B | 600B | Split function out |
| Layer 1 (per type) | 500B | 750B | Split core/extended |
| Layer 2 (errors) | 200B | 300B | Use factory |
| Layer 2 (dunders) | 1KB | 1.5KB | Optimize loops |
| Layer 3 (per module) | 500B | 1KB | Split features |

### App Bundle Budgets

| App Type | Target | Layers Used |
|----------|--------|-------------|
| Hello World | 500B | Layer 0 only |
| String processing | 1.2KB | Layer 0 + string-core |
| CRUD app | 1.5KB | Layer 0 + types + errors |
| Complex app | 3KB | Layer 0-2 |
| Full stdlib | 5KB | All layers |

---

## Troubleshooting

### Bundle Too Large

1. Run `node scripts/analyze-bundle.js --verbose`
2. Check top contributors in output
3. Look for unexpected imports
4. Check if methods can be inlined

### Tree-Shaking Not Working

1. Check for `sideEffects: false` in package.json
2. Look for circular dependencies
3. Ensure ES module syntax
4. Check for default object exports

### CI Failing on Size

1. Check which bundle exceeded limit
2. Compare with main branch
3. Consider if increase is justified
4. Either optimize or adjust limit (with justification)

---

## Adding New Features Without Bloat

### Checklist

1. [ ] Can this be inlined at transpile time?
2. [ ] Is this used by >25% of apps? (Layer 0)
3. [ ] Is this a type method? (Layer 1)
4. [ ] Is this stdlib? (Layer 3, lazy-loaded)
5. [ ] Does this add circular dependencies?
6. [ ] Is the new code tree-shakeable?

### Example: Adding New String Method

```python
# Python: str.removeprefix()
def removeprefix(self, prefix):
    if self.startswith(prefix):
        return self[len(prefix):]
    return self
```

**Decision Tree**:

1. Is there a JS equivalent? → No
2. Can it be inlined? → No (complex logic)
3. Used often? → Medium (Layer 1, extended)

**Implementation**:

```javascript
// Add to string-extended.js (not core)
export function removeprefix(s, prefix) {
    return s.startsWith(prefix) ? s.slice(prefix.length) : s;
}
```

**Size Impact**: ~40B raw, ~20B gzip - within budget.

