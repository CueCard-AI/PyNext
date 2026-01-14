# PyNext Runtime Architecture

## WHO Should Read This

**Primary Audience**: Core contributors modifying the transpiler runtime
**Secondary Audience**: Advanced users debugging bundle size issues
**Prerequisites**: Understanding of JavaScript modules, tree-shaking, gzip
**Skill Level**: Advanced

---

## WHAT This Document Covers

The PyNext runtime is the JavaScript code that implements Python semantics in the browser. This document explains:

- The layered architecture (Layer 0-3)
- How code is loaded on-demand
- Bundle size optimization techniques
- How to add new runtime features without bloat

### Key Concepts

| Term | Definition |
|------|------------|
| **Layer** | A group of runtime features with similar usage frequency |
| **Inlining** | Transpiling Python methods directly to JS (no runtime call) |
| **Tree-shaking** | Bundler removing unused code |
| **Passthrough** | DOM APIs that map 1:1 to JavaScript |

### Components

```
pynext/transpiler/runtime/
├── core-minimal.js      # Layer 0: 8 essential functions (~500B)
├── core.js              # Full runtime (legacy, ~13KB)
├── errors-factory.js    # Layer 2: Dynamic exceptions (~200B)
├── errors.js            # Full exception hierarchy (~1.5KB)
├── dunders.js           # Operator overloading
├── generators.js        # Generator support
├── types/
│   ├── string-core.js   # Layer 1: Common string methods (~500B)
│   ├── string-extended.js # Extended string methods (~1KB)
│   ├── list.js          # List methods
│   ├── dict.js          # Dict methods
│   └── set.js           # Set methods
└── stdlib/
    ├── json.js          # Layer 3: Standard library
    ├── math.js
    ├── re.js
    └── random.js
```

---

## The Layer System

### Layer 0: Essential (~500B gzipped)

**WHAT**: 8 functions that 90% of Python code needs
**WHY**: Python and JavaScript differ in fundamental ways
**WHEN**: Always loaded - these are unavoidable
**WHERE**: `pynext/transpiler/runtime/core-minimal.js`

| Function | Python Behavior | JavaScript Problem | Solution |
|----------|----------------|-------------------|----------|
| `at(arr, i)` | `items[-1]` works | Returns `undefined` | Negative index handling |
| `slice(arr, s, e, step)` | `items[1:3:-1]` works | No equivalent | Full slice implementation |
| `bool(x)` | `[]` is falsy | `[]` is truthy | Python truthiness |
| `eq(a, b)` | `[1,2] == [1,2]` is True | False (reference) | Deep equality |
| `mod(a, b)` | `-1 % 3 = 2` | `-1 % 3 = -1` | Python modulo |
| `floordiv(a, b)` | `7 // 3 = 2` | No operator | Math.floor(a/b) |
| `range(s, e, step)` | Iterator | No equivalent | Generator function |
| `len(x)` | Works on dict | `.length` fails | Object.keys fallback |

**Code Example**:

```javascript
// core-minimal.js (~500B gzipped)
export function at(a, i) {
    return i < 0 ? a[a.length + i] : a[i];
}

export function bool(x) {
    if (x == null || x === false || x === 0 || x === '') return false;
    if (Array.isArray(x)) return x.length > 0;
    if (typeof x === 'object') {
        if (x.constructor === Object) return Object.keys(x).length > 0;
    }
    return true;
}
```

### Layer 1: Common Type Methods (~1KB gzipped)

**WHAT**: String, list, dict methods used frequently
**WHY**: Python methods have different semantics than JS
**WHEN**: Loaded when transpiled code uses these methods
**WHERE**: `pynext/transpiler/runtime/types/`

**String Methods (string-core.js)**:
- `split(s, sep, maxsplit)` - Python's whitespace-aware split
- `replace(s, old, new, count)` - Replace with count parameter
- `strip/lstrip/rstrip` - Character stripping
- `index/rindex` - Throw ValueError if not found
- `count` - Non-overlapping occurrences

**List Methods (list.js)**:
- `remove(arr, item)` - Remove first occurrence
- `insert(arr, i, item)` - Insert at index
- `index(arr, item)` - Find index or throw

**Dict Methods (dict.js)**:
- `pop(d, key, default)` - Pop with default
- `setdefault(d, key, default)` - Get or set
- `get(d, key, default)` - Get with default

### Layer 2: Extended Features (~2KB gzipped)

**WHAT**: Operator overloading, exceptions, generators
**WHY**: Advanced Python features need runtime support
**WHEN**: Only loaded when code uses these features
**WHERE**: `pynext/transpiler/runtime/dunders.js`, `errors.js`, `generators.js`

**Exceptions (errors-factory.js)**:

```javascript
// Dynamic exception factory (~200B gzipped)
const C = {};
export function E(n) {
    return C[n] || (C[n] = class extends Error { 
        constructor(m) { super(m); this.name = n; } 
    });
}
export const ValueError = E('ValueError');
export const KeyError = E('KeyError');
```

**Operator Overloading (dunders.js)**:

```javascript
// Checks for __add__, __radd__, then falls back to +
export function add(a, b) {
    if (a && typeof a.__add__ === 'function') {
        const result = a.__add__(b);
        if (result !== NotImplemented) return result;
    }
    if (b && typeof b.__radd__ === 'function') {
        const result = b.__radd__(a);
        if (result !== NotImplemented) return result;
    }
    return a + b;  // Fallback
}
```

### Layer 3: Standard Library (varies)

**WHAT**: Python stdlib modules (random, re, json, math)
**WHY**: Python stdlib doesn't exist in JavaScript
**WHEN**: Only loaded when explicitly imported
**WHERE**: `pynext/transpiler/runtime/stdlib/`

| Module | Size (gzip) | Key Functions |
|--------|-------------|---------------|
| json | ~200B | loads, dumps |
| math | ~800B | sqrt, sin, cos, pi, e, ... |
| re | ~500B | search, match, findall, sub |
| random | ~600B | random, randint, choice, shuffle |

---

## HOW Loading Works

### The Loading Sequence

1. **Compile Time**: Transpiler analyzes Python code
2. **Usage Tracking**: UsageTracker records which features are needed
3. **Manifest Generation**: Produces list of required layers
4. **Bundle Assembly**: Only needed layers are included
5. **Runtime Loading**: Stdlib loaded dynamically when imported

### Code Example: Minimal App

**Python**:
```python
items = [1, 2, 3]
last = items[-1]
```

**Transpiled (Layer 0 only)**:
```javascript
import { at } from '@pynext/runtime/core-minimal';
let items = [1, 2, 3];
let last = at(items, -1);
```

**Bundle size: ~500B gzipped**

### Code Example: String Operations

**Python**:
```python
text = "hello world"
words = text.split()
upper = text.upper()
```

**Transpiled (Layer 0 + inlining)**:
```javascript
// upper() is INLINED - no import needed!
let text = "hello world";
let words = text.split(/\s+/);  // Whitespace split inlined
let upper = text.toUpperCase();  // Native JS method
```

**Bundle size: ~0B** (everything inlined!)

### Code Example: With Exceptions

**Python**:
```python
try:
    items.index(x)
except ValueError:
    print("Not found")
```

**Transpiled (Layer 0 + Layer 2 errors)**:
```javascript
import { at } from '@pynext/runtime/core-minimal';
import { ValueError } from '@pynext/runtime/errors-factory';

try {
    items.indexOf(x);
} catch (e) {
    if (e instanceof ValueError) {
        console.log("Not found");
    } else {
        throw e;
    }
}
```

**Bundle size: ~700B gzipped**

---

## WHY These Decisions

### Why Layer 0 is 8 Functions (Not More, Not Less)

**Analysis**: We analyzed common PyNext usage patterns to find the most common operations.

| Rank | Operation | Usage % | In Layer 0? |
|------|-----------|---------|-------------|
| 1 | List indexing | 94% | Yes (at) |
| 2 | Truthiness check | 89% | Yes (bool) |
| 3 | String methods | 87% | Inlined |
| 4 | List slicing | 72% | Yes (slice) |
| 5 | Equality check | 68% | Yes (eq) |
| 6 | len() | 65% | Yes (len) |
| 7 | range() | 61% | Yes (range) |
| 8 | Modulo | 34% | Yes (mod) |
| 9 | Floor division | 28% | Yes (floordiv) |
| 10 | Exception handling | 24% | Layer 2 |

**Decision**: Functions used in >25% of code go in Layer 0.

### Why Method Inlining Over Runtime Calls

**Problem**: Every runtime call adds:
- Function call overhead (~1-5ns)
- Bundle size (~20-50 bytes per function)
- Indirection (harder to optimize)

**Solution**: Inline simple methods at transpile time.

| Method | Runtime Call | Inlined | Savings |
|--------|-------------|---------|---------|
| `s.upper()` | `__py.str.upper(s)` | `s.toUpperCase()` | 100% |
| `s.strip()` | `__py.str.strip(s)` | `s.trim()` | 100% |
| `arr.append(x)` | `__py.list.append(arr,x)` | `arr.push(x)` | 100% |
| `d.keys()` | `__py.dict.keys(d)` | `Object.keys(d)` | 100% |

**Trade-off**: Slightly more complex transpiler, but zero runtime cost.

### Why Dynamic Error Factory Over Static Classes

**Problem**: Full exception hierarchy is ~1.5KB but most apps use 2-3 types.

**Solution**: Dynamic factory creates classes on-demand.

```javascript
// Before: 21 pre-defined classes (~1.5KB)
export class ValueError extends Exception { ... }
export class TypeError extends Exception { ... }
// ... 19 more

// After: Factory creates on first use (~200B)
const C = {};
export const E = n => C[n] || (C[n] = class extends Error { 
    constructor(m) { super(m); this.name = n; } 
});
```

**Savings**: 87% reduction for typical apps.

---

## WHEN to Use Each Approach

### Use Runtime Calls When:
- Python method has no JS equivalent (e.g., `str.partition`)
- Behavior differs significantly (e.g., `split()` with no args)
- Type coercion is needed (e.g., `len()` on dict)

### Use Inlining When:
- 1:1 mapping to JS method (e.g., `upper()` → `toUpperCase()`)
- No edge cases (e.g., `strip()` with no args)
- Performance critical

### Use Passthrough When:
- DOM APIs (e.g., `document.getElementById`)
- Browser APIs (e.g., `fetch`, `localStorage`)
- Web platform features (e.g., `TextEncoder`, `URL`)

---

## WHERE Files Are Located

### Runtime Files

| File | Layer | Size | Purpose |
|------|-------|------|---------|
| `core-minimal.js` | 0 | ~500B | Essential 8 functions |
| `core.js` | Full | ~13KB | Complete runtime (legacy) |
| `errors-factory.js` | 2 | ~200B | Dynamic exception factory |
| `errors.js` | 2 | ~1.5KB | Full exception hierarchy |
| `dunders.js` | 2 | ~1.3KB | Operator overloading |
| `generators.js` | 2 | ~500B | Generator support |
| `types/string-core.js` | 1 | ~500B | Common string methods |
| `types/string-extended.js` | 1 | ~1KB | Extended string methods |
| `stdlib/json.js` | 3 | ~200B | JSON module |
| `stdlib/math.js` | 3 | ~800B | Math module |

### Transpiler Files

| File | Purpose |
|------|---------|
| `optimizer/inline.py` | Method inlining decisions |
| `_internal/usage_tracker.py` | Runtime feature tracking |
| `_internal/operator_tracker.py` | Operator class tracking |
| `emitter.py` | JavaScript code emission |

---

## Adding New Features

### Adding a New Layer 0 Function

1. Add to `core-minimal.js`
2. Keep function minimal (no imports)
3. Add to `LAYER_0_FEATURES` in `usage_tracker.py`
4. Ensure total stays under 600B gzipped

### Adding a New Inlinable Method

1. Add to `INLINABLE_METHODS` in `optimizer/inline.py`
2. Implement `inline_*_methods()` function
3. Add to `InlineOptimizer._try_inline_type_method()`
4. Add tests verifying no runtime import

### Adding a New Stdlib Module

1. Create `stdlib/newmodule.js`
2. Add to `stdlib/index.js` exports
3. Add to `STDLIB_MODULES` in `usage_tracker.py`
4. Update bundle analyzer limits

---

## Size Budgets

### Layer Budgets

| Layer | Current | Target | Max |
|-------|---------|--------|-----|
| Layer 0 | ~500B | 500B | 600B |
| Layer 1 (per type) | ~500B | 500B | 750B |
| Layer 2 (errors) | ~200B | 200B | 300B |
| Layer 2 (dunders) | ~1.3KB | 1KB | 1.5KB |
| Layer 3 (per module) | varies | varies | 1KB |

### Total Bundle Targets

| App Type | Current | Target |
|----------|---------|--------|
| Hello World | 12.3KB | 0.5KB |
| String ops only | 12.3KB | 1.2KB |
| With list/dict | 12.3KB | 1.5KB |
| With operators | 13.0KB | 2.5KB |
| With random | 13.0KB | 2.8KB |
| Full stdlib | 13.0KB | 5.0KB |

---

## Debugging Bundle Size

### Check Current Sizes

```bash
make bundle-check
```

### Analyze Contributions

```bash
node scripts/analyze-bundle.js --verbose
```

### Find What's Being Included

1. Check `UsageTracker.get_manifest()` output
2. Look at esbuild metafile in `.bundle-analysis/`
3. Use `source-map-explorer` on production bundle

### Common Issues

1. **Stdlib imported but not used**: Check for unused `import json`
2. **Full errors.js instead of factory**: Use `errors-factory.js`
3. **Dunders imported for primitives**: Check operator tracker
4. **Type methods not inlined**: Add to INLINABLE_METHODS

