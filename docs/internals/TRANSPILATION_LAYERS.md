# PyNext Transpilation Layers

## WHO Should Read This

**Primary Audience**: Transpiler developers implementing layered bundling
**Secondary Audience**: Advanced users understanding bundle composition
**Prerequisites**: Understanding of PyNext transpiler architecture
**Skill Level**: Advanced

---

## WHAT This Document Covers

This document explains how the transpiler tracks runtime feature usage and generates optimal imports:

- Layer classification system
- Usage tracking during transpilation
- Manifest generation
- Import optimization strategies
- Dynamic loading patterns

---

## The Layer Classification System

### Overview

Features are classified into layers based on usage frequency:

| Layer | Contents | Size | Loading |
|-------|----------|------|---------|
| 0 | Essential functions | ~500B | Always |
| 1 | Type methods | ~1KB | On method use |
| 2 | Extended (errors, dunders) | ~2KB | On feature use |
| 3 | Standard library | varies | On import |

### Layer 0: Essential

**Always required** - These functions address fundamental Python/JavaScript differences.

```python
# Layer 0 features
LAYER_0_FEATURES = frozenset({
    "at",       # items[-1] - negative indexing
    "slice",    # items[1:3:-1] - Python slicing
    "bool",     # if items: - Python truthiness
    "eq",       # a == b - deep equality
    "mod",      # -1 % 3 - Python modulo
    "floordiv", # 7 // 3 - floor division
    "range",    # range(10) - iterator
    "len",      # len(d) - works on dict
})
```

### Layer 1: Type Methods

**Loaded per-type** - String, list, dict, set methods.

```python
# Layer 1 features (organized by type)
LAYER_1_STR_FEATURES = frozenset({
    "str.split", "str.replace", "str.count", "str.index",
    "str.strip", "str.lstrip", "str.rstrip",
    "str.startswith", "str.endswith",
    # ... and more
})

LAYER_1_LIST_FEATURES = frozenset({
    "list.remove", "list.insert", "list.index",
    "list.sort", "list.copy",
    # ... and more
})

LAYER_1_DICT_FEATURES = frozenset({
    "dict.get", "dict.pop", "dict.setdefault",
    "dict.update", "dict.keys", "dict.values",
    # ... and more
})
```

### Layer 2: Extended

**Loaded on feature use** - Errors, operator overloading, generators.

```python
# Layer 2 features
LAYER_2_ERROR_FEATURES = frozenset({
    "ValueError", "TypeError", "KeyError", "IndexError",
    "ZeroDivisionError", "RuntimeError", "AttributeError",
    # ... and more
})

LAYER_2_DUNDER_FEATURES = frozenset({
    "dunders.add", "dunders.sub", "dunders.mul",
    "dunders.eq", "dunders.lt", "dunders.gt",
    # ... and more
})

LAYER_2_GENERATOR_FEATURES = frozenset({
    "wrapGenerator", "wrapAsyncGenerator", "GeneratorExit",
})
```

### Layer 3: Standard Library

**Loaded on import** - Each stdlib module is separate.

```python
STDLIB_MODULES = frozenset({
    "json",    # ~200B - loads, dumps
    "math",    # ~800B - sqrt, sin, cos, pi
    "re",      # ~500B - search, match, sub
    "random",  # ~600B - randint, choice
    "asyncio", # ~300B - sleep, gather
})
```

---

## HOW Usage Tracking Works

### The UsageTracker Class

Located in `pynext/transpiler/_internal/usage_tracker.py`:

```python
class UsageTracker:
    """Tracks runtime feature usage during transpilation."""
    
    def __init__(self):
        self._features: Set[str] = set()
    
    def record(self, feature: str) -> None:
        """Record that a runtime feature was used."""
        self._features.add(feature)
    
    def get_manifest(self) -> UsageManifest:
        """Get categorized manifest of all used features."""
        manifest = UsageManifest()
        
        for feature in self._features:
            if feature in LAYER_0_FEATURES:
                manifest.layer0.append(feature)
            elif feature in LAYER_1_FEATURES:
                manifest.layer1.append(feature)
            # ... etc
        
        return manifest
```

### Recording Usage During Transpilation

The emitter calls `record_usage()` when emitting runtime calls:

```python
# In emitter.py
def _emit_subscript(node):
    """Emit array/dict subscript."""
    index = _emit_expr(node.slice)
    
    # Check for negative index
    if isinstance(node.slice, Constant) and node.slice.value < 0:
        # Record Layer 0 usage
        record_usage("at")
        return f"at({target}, {index})"
    
    return f"{target}[{index}]"
```

### Usage Recording Points

| Operation | Feature Recorded | Layer |
|-----------|-----------------|-------|
| `items[-1]` | `at` | 0 |
| `items[1:3]` | `slice` | 0 |
| `if items:` | `bool` | 0 |
| `a == b` | `eq` | 0 |
| `s.split()` | `str.split` | 1 |
| `arr.append(x)` | `list.append` | 1 (or inlined) |
| `raise ValueError` | `ValueError` | 2 |
| `a + b` (custom class) | `dunders.add` | 2 |
| `import json` | `json` | 3 |

---

## WHEN Manifests Are Generated

### Transpilation Flow

```
Python Source
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│ Parser (AST Analysis)                                         │
│   - Detect class definitions                                  │
│   - Detect operator methods                                   │
│   - Detect stdlib imports                                     │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│ Emitter (Code Generation)                                     │
│   - Record runtime feature usage                              │
│   - UsageTracker.record("at"), record("str.split"), etc.      │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│ Manifest Generation                                           │
│   - UsageTracker.get_manifest()                              │
│   - Categorize features by layer                             │
│   - Output: { layer0: [...], layer1: [...], ... }            │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│ Import Generation                                             │
│   - Generate minimal imports for used features               │
│   - import { at, bool } from '@pynext/runtime/core-minimal'  │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
JavaScript Output
```

### Manifest Structure

```python
@dataclass
class UsageManifest:
    """Manifest of runtime features used."""
    layer0: List[str] = []   # ["at", "bool"]
    layer1: List[str] = []   # ["str.split", "list.append"]
    layer2: List[str] = []   # ["ValueError", "dunders.add"]
    stdlib: List[str] = []   # ["json", "random"]
    
    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "layer0": self.layer0,
            "layer1": self.layer1,
            "layer2": self.layer2,
            "stdlib": self.stdlib,
        }
```

### Example Manifest

**Python Input**:
```python
items = [1, 2, 3]
last = items[-1]
text = "hello world"
words = text.split()

if not items:
    raise ValueError("Empty list")
```

**Generated Manifest**:
```json
{
    "layer0": ["at", "bool"],
    "layer1": ["str.split"],
    "layer2": ["ValueError"],
    "stdlib": []
}
```

---

## WHERE Import Optimization Happens

### Current Import Generation

In `emitter.py`, imports are generated at the top of the output:

```python
def _generate_imports(manifest: UsageManifest) -> str:
    """Generate optimal import statements from manifest."""
    imports = []
    
    # Layer 0
    if manifest.layer0:
        features = ", ".join(manifest.layer0)
        imports.append(f"import {{ {features} }} from '@pynext/runtime/core-minimal';")
    
    # Layer 1 - grouped by type
    str_features = [f for f in manifest.layer1 if f.startswith("str.")]
    if str_features:
        methods = ", ".join(f.split(".")[1] for f in str_features)
        imports.append(f"import {{ {methods} }} from '@pynext/runtime/types/string-core';")
    
    # Layer 2 - errors
    errors = [f for f in manifest.layer2 if f in LAYER_2_ERROR_FEATURES]
    if errors:
        imports.append(f"import {{ E }} from '@pynext/runtime/errors-factory';")
    
    # Layer 3 - stdlib (dynamic imports)
    for mod in manifest.stdlib:
        # Dynamic import in function body
        pass
    
    return "\n".join(imports)
```

### Import Patterns by Layer

| Layer | Import Pattern | Example |
|-------|----------------|---------|
| 0 | Static named | `import { at, bool } from './core-minimal';` |
| 1 | Static named | `import { split } from './types/string-core';` |
| 2 | Static factory | `import { E } from './errors-factory';` |
| 3 | Dynamic | `const json = await import('./stdlib/json');` |

---

## WHY Layer Boundaries

### Layer 0 Criteria

**Include if**:
- Used by >25% of Python code
- Addresses fundamental Python/JS difference
- Cannot be inlined

**Exclude if**:
- Can be inlined (e.g., `s.upper()`)
- Used by <25% of code
- Type-specific (belongs in Layer 1)

### Layer 1 Criteria

**Include if**:
- Type-specific method (str, list, dict, set)
- Has different semantics in Python vs JS
- Cannot be inlined

**Split core/extended if**:
- Core: Used by >50% of apps using that type
- Extended: Used by <50% of apps using that type

### Layer 2 Criteria

**Include if**:
- Advanced feature (errors, operators, generators)
- Only needed by apps using those features
- Not type-specific

### Layer 3 Criteria

**Include if**:
- Part of Python stdlib
- Has no JS equivalent
- Should be lazy-loaded

---

## Dynamic Loading Strategies

### Strategy 1: Static Analysis

Analyze code at transpile time, generate static imports:

```python
# Transpiler output
import { at, bool } from '@pynext/runtime/core-minimal';
import { split } from '@pynext/runtime/types/string-core';
```

**Pros**: Simple, works everywhere
**Cons**: All features loaded upfront

### Strategy 2: Dynamic Import for Stdlib

Use dynamic imports for stdlib modules:

```python
# Python
import json
data = json.loads(text)

# Transpiled
const json = await import('@pynext/runtime/stdlib/json');
const data = json.loads(text);
```

**Pros**: Stdlib only loaded when used
**Cons**: Requires async context or top-level await

### Strategy 3: Lazy Loading All Layers

Use dynamic imports for everything:

```javascript
// Lazy loader
const runtime = {
    _at: null,
    async at(arr, i) {
        if (!this._at) {
            const { at } = await import('./core-minimal.js');
            this._at = at;
        }
        return this._at(arr, i);
    }
};
```

**Pros**: Absolute minimum initial load
**Cons**: Overhead per call, complexity

---

## Example: Full Transpilation Flow

### Input Python

```python
def process_items(items):
    """Process a list of items."""
    if not items:
        raise ValueError("Empty list")
    
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item.upper())
        else:
            result.append(str(item))
    
    return result[-1]
```

### Usage Tracking

```
Recording: bool       (Layer 0) - "if not items:"
Recording: ValueError (Layer 2) - "raise ValueError"
Recording: at         (Layer 0) - "return result[-1]"
```

Note: `item.upper()` is **inlined** to `item.toUpperCase()` - no recording.

### Generated Manifest

```json
{
    "layer0": ["at", "bool"],
    "layer1": [],
    "layer2": ["ValueError"],
    "stdlib": []
}
```

### Output JavaScript

```javascript
import { at, bool } from '@pynext/runtime/core-minimal';
import { E } from '@pynext/runtime/errors-factory';
const ValueError = E('ValueError');

function process_items(items) {
    if (!bool(items)) {
        throw new ValueError("Empty list");
    }
    
    let result = [];
    for (const item of items) {
        if (typeof item === 'string') {
            result.push(item.toUpperCase());  // Inlined!
        } else {
            result.push(String(item));
        }
    }
    
    return at(result, -1);
}
```

### Bundle Size

- Layer 0 features used: `at`, `bool` → ~300B
- Layer 2 features used: `ValueError` → ~100B (factory)
- **Total**: ~400B gzipped

Compare to full runtime: 13KB → **97% savings**

---

## Adding New Layer Features

### Step 1: Classify the Feature

Ask:
1. Is it used by >25% of apps? → Layer 0
2. Is it type-specific? → Layer 1
3. Is it advanced (errors/operators)? → Layer 2
4. Is it stdlib? → Layer 3

### Step 2: Add to Layer Definition

```python
# In usage_tracker.py
LAYER_X_FEATURES = frozenset({
    # ... existing features
    "new_feature",  # Add here
})
```

### Step 3: Record Usage in Emitter

```python
# In emitter.py
def _emit_new_feature(node):
    record_usage("new_feature")
    return f"__py.new_feature({args})"
```

### Step 4: Implement in Runtime

```javascript
// In appropriate layer file
export function new_feature(args) {
    // Implementation
}
```

### Step 5: Update Bundle Analyzer

```javascript
// In scripts/analyze-bundle.js
const BUNDLES = {
    // ... existing bundles
    'layer-x-new': join(ROOT, 'path/to/new.js'),
};
```

---

## Debugging Layer Issues

### Feature Not Recorded

1. Check emitter calls `record_usage()`
2. Verify feature name matches layer definition
3. Check manifest output

### Wrong Layer Classification

1. Verify feature in correct `LAYER_X_FEATURES` set
2. Check for typos in feature name
3. Run tests for layer classification

### Import Not Generated

1. Check manifest includes the feature
2. Verify import generator handles that layer
3. Check for import deduplication issues

