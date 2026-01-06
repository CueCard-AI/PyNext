# PyNext Transpiler Optimizer

The optimizer reduces generated code size and improves execution speed by applying safe transformations to the IR tree.

## Table of Contents

1. [Who Is This For?](#who-is-this-for)
2. [What Does It Do?](#what-does-it-do)
3. [When Is It Applied?](#when-is-it-applied)
4. [Where Does Optimization Happen?](#where-does-optimization-happen)
5. [Why Each Optimization?](#why-each-optimization)
6. [How To Use It?](#how-to-use-it)
7. [API Reference](#api-reference)
8. [Metrics & Benchmarks](#metrics--benchmarks)

---

## Who Is This For?

### Developers

- **Web developers** using PyNext who want smaller, faster JavaScript output
- **Performance engineers** optimizing bundle sizes and execution time
- **Debugging** when you need to understand why certain wrappers weren't elided

### Contributors

- **Optimizer developers** adding new optimization passes
- **Compiler engineers** understanding the transformation pipeline
- **Testers** verifying optimization correctness

### AI Assistants

- **LLMs** helping debug optimization issues
- **Code generators** that need to understand what's safe to optimize
- **Documentation tools** generating optimization reports

---

## What Does It Do?

The optimizer applies 6 transformation passes:

### 1. Type Inference

Analyzes code to determine variable types:

```python
x = 5           # x: int
y = "hello"     # y: str
z = x + 3       # z: int (int + int)
valid = x > 0   # valid: bool (comparison)
```

### 2. Wrapper Elision

Removes unnecessary `__py.*` wrappers when Python and JS semantics match:

```python
# Before optimization
if __py.bool(x > 0):
    y = __py.add(x, 1)

# After optimization (x is known int)
if (x > 0) {
    y = x + 1;
}
```

### 3. Loop Variable Capture

Fixes the closure-in-loop gotcha automatically:

```python
# Problem: all handlers see i=4
for i in range(5):
    onclick = lambda: handle(i)

# Fixed with IIFE capture
for (let i = 0; i < 5; i++) {
    onclick = ((i) => () => handle(i))(i);
}
```

### 4. Runtime Inlining

Inlines simple runtime calls:

```python
# Before
n = __py.len(items)
valid = __py.bool(items)

# After (items is known list)
n = items.length;
valid = items.length > 0;
```

### 5. Dead Code Elimination

Removes unreachable code:

```python
# Before
if False:
    x = 1  # Unreachable
if True:
    y = 2
else:
    z = 3  # Unreachable

# After
y = 2;
```

### 6. @js_native Support

Detects and handles `@js_native` decorated functions:

```python
@js_native
def fast_sum(items):
    total = 0
    for x in items:
        total += x
    return total

# Emits pure JS without wrappers
function fast_sum(items) {
    let total = 0;
    for (const x of items) {
        total += x;
    }
    return total;
}
```

---

## When Is It Applied?

The optimizer runs in the transpilation pipeline:

```
Python Source
     │
     ▼
┌─────────┐
│  Parse  │
└─────────┘
     │
     ▼
┌─────────────┐
│  IR Nodes   │
└─────────────┘
     │
     ▼
┌─────────────┐     ← Optimizer runs here
│  Optimize   │
└─────────────┘
     │
     ▼
┌─────────────┐
│   Emit      │
└─────────────┘
     │
     ▼
JavaScript
```

### Optimization Order

Passes run in this sequence (order matters!):

1. **Type Inference** - Runs first to provide type info for other passes
2. **Wrapper Elision** - Uses type info to decide safe elisions
3. **Loop Capture** - Fixes closure issues
4. **Inlining** - Uses type info for safe inlining
5. **DCE** - Runs last to clean up any dead code from previous passes

---

## Where Does Optimization Happen?

### File Structure

```
pynext/transpiler/optimizer/
├── __init__.py           # Public API: optimize()
├── types.py              # Type inference engine
├── elision.py            # Wrapper elision rules
├── capture.py            # Loop variable capture fix
├── inline.py             # Runtime call inlining
├── dce.py                # Dead code elimination
├── native.py             # @js_native decorator handling
└── _internal/
    ├── __init__.py
    ├── type_env.py       # Type environment tracking
    └── visitor.py        # IR tree visitor base class
```

### Test Files

```
tests/unit/transpiler/
├── test_187_types.py             # 129 tests - Type inference
├── test_187_elision.py           # 127 tests - Wrapper elision
├── test_187_capture.py           # 74 tests - Loop capture
├── test_187_inline.py            # 80 tests - Runtime inlining
├── test_187_dce.py               # 70 tests - Dead code elimination
├── test_187_native.py            # 50 tests - @js_native
├── test_187_integration.py       # 48 tests - Integration
├── test_187_regression.py        # 50 tests - Regression
├── test_187_elision_safety.py    # 33 tests - Elision safety
├── test_187_type_edge_cases.py   # 42 tests - Type edge cases
├── test_187_cross_pass.py        # 21 tests - Cross-pass
├── test_187_nested_capture.py    # 11 tests - Nested loop capture
├── test_187_dce_safety.py        # 22 tests - DCE safety
├── test_187_e2e.py               # 21 tests - End-to-end
├── test_187_stress.py            # 19 tests - Stress tests
└── test_187_edge_cases.py        # 38 tests - Edge cases (async, fstring)

tests/benchmarks/
└── test_optimizer_benchmarks.py  # 6 tests - Benchmarks

tests/js/transpiler/
├── optimizer.test.js             # 55 tests - Core optimizer
├── optimizer_extended.test.js    # 66 tests - Extended tests
└── edge_cases.test.js            # 56 tests - Edge cases
```

**Total: 1,018 tests (841 Python + 177 JavaScript)**

---

## Why Each Optimization?

### Wrapper Elision

**Problem:** The transpiler conservatively wraps all operations:

```javascript
// Conservative output
y = __py.add(x, __py.mul(a, b));
```

**Why it matters:**
- Each wrapper is a function call (~5-10ns overhead)
- Adds ~15 bytes per wrapper to bundle size
- Makes debugging harder (more stack frames)

**Solution:** When types are known, elide wrappers:

```javascript
// Optimized output (x, a, b are known numbers)
y = x + (a * b);
```

### Loop Capture Fix

**Problem:** Python closures capture by reference:

```python
# All buttons print 4!
for i in range(5):
    btn.onclick = lambda: print(i)
```

**Why it matters:**
- Extremely common bug in UI code
- Hard to debug (works sometimes, fails in loops)
- Python developers expect Python semantics

**Solution:** IIFE wrapping captures current value:

```javascript
for (let i = 0; i < 5; i++) {
    btn.onclick = ((i) => () => console.log(i))(i);
}
```

### Dead Code Elimination

**Problem:** Unreachable code bloats bundles:

```python
if DEBUG:  # False in production
    log_everything()
```

**Why it matters:**
- Dead code increases bundle size
- Import analysis includes unused code
- Confusing for developers reading output

**Solution:** Remove statically unreachable code

---

## How To Use It?

### Basic Usage

```python
from pynext.transpiler import parse, emit
from pynext.transpiler.optimizer import optimize

# Parse Python to IR
ir = parse('''
x = 5
if x > 0:
    y = x + 1
''')

# Optimize
optimized_ir = optimize(ir)

# Emit JavaScript
js_code = emit(optimized_ir)
```

### Custom Options

```python
from pynext.transpiler.optimizer import optimize, OptimizeOptions

# Enable specific passes
options = OptimizeOptions(
    elision=True,      # Wrapper elision
    inline=True,       # Runtime inlining
    capture=True,      # Loop capture fix
    dce=True,          # Dead code elimination
)

optimized = optimize(ir, options)
```

### Disable All Optimization

```python
options = OptimizeOptions(
    elision=False,
    inline=False,
    capture=False,
    dce=False,
)
```

### Get Statistics

```python
from pynext.transpiler.optimizer import get_optimization_stats, format_stats

stats = get_optimization_stats(original_ir, optimized_ir)
print(format_stats(stats))

# Output:
# Optimization Statistics:
#   Original __py.* calls: 15
#   Optimized __py.* calls: 3
#   Wrapper reduction: 80.0%
#   Inlinable calls: 5
#   Loop lambdas: 2
#   Unreachable blocks: 1
#   Runtime deps: ['at', 'eq', 'slice']
```

---

## API Reference

### Main Functions

#### `optimize(ir, options=None) -> Program`

Apply all optimization passes to IR.

```python
from pynext.transpiler.optimizer import optimize

optimized = optimize(ir)
```

#### `OptimizeOptions`

Configuration for optimization passes.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `elision` | bool | True | Enable wrapper elision |
| `inline` | bool | True | Enable runtime inlining |
| `capture` | bool | True | Enable loop capture fix |
| `dce` | bool | True | Enable dead code elimination |

### Type Inference

#### `infer_types(ir) -> TypeEnv`

Infer types for all variables.

```python
from pynext.transpiler.optimizer import infer_types

env = infer_types(ir)
env.get_type("x")  # → PyType.INT
```

#### `PyType` Enum

| Type | Description |
|------|-------------|
| `INT` | Integer |
| `FLOAT` | Float |
| `BOOL` | Boolean |
| `STR` | String |
| `LIST` | List |
| `DICT` | Dictionary |
| `ANY` | Unknown type |

### Elision

#### `elide_wrappers(ir, type_env) -> Program`

Remove unnecessary wrappers.

```python
from pynext.transpiler.optimizer import elide_wrappers, infer_types

env = infer_types(ir)
optimized = elide_wrappers(ir, env)
```

#### `can_elide_*` Functions

Check if specific operations can be elided:

- `can_elide_bool(node, env)` - Check `__py.bool()`
- `can_elide_eq(left, right, env)` - Check `__py.eq()`
- `can_elide_add(left, right, env)` - Check `__py.add()`
- `can_elide_at(arr, idx, env)` - Check `__py.at()`

### Statistics

#### `get_optimization_stats(original, optimized, type_env=None)`

Get statistics about optimization.

```python
stats = get_optimization_stats(original_ir, optimized_ir)
```

Returns `OptimizationStats`:

| Field | Type | Description |
|-------|------|-------------|
| `original_py_calls` | int | __py.* calls before |
| `optimized_py_calls` | int | __py.* calls after |
| `wrapper_reduction` | float | Reduction percentage |
| `runtime_deps` | set | Required runtime functions |

---

## Metrics & Benchmarks

### Target Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Wrapper calls | 50-70% reduction | Count `__py.*` in output |
| Code size | 30-40% smaller | Gzip size comparison |
| Execution time | 10-20% faster | Benchmark suite |
| Test coverage | 100% | All branches covered |

### Running Tests

```bash
# Run all Python optimizer tests
pytest tests/unit/transpiler/test_187_*.py tests/benchmarks/test_optimizer_benchmarks.py -v

# Run JavaScript tests
npm test -- --testPathPattern="optimizer|edge_cases"
```

### Test Summary

| Component | Tests |
|-----------|-------|
| Type Inference (core + edge cases) | 171 |
| Wrapper Elision (core + safety) | 160 |
| Loop Capture (core + nested) | 85 |
| Inlining | 80 |
| DCE (core + safety) | 92 |
| @js_native | 50 |
| Integration + Cross-pass | 69 |
| End-to-End + Stress | 40 |
| Edge Cases (async, fstring, etc.) | 38 |
| Regression + Benchmarks | 56 |
| **Python Subtotal** | **841** |
| JS Runtime (core + extended + edge) | 177 |
| **Grand Total** | **1,018** |

---

## Safe vs Unsafe Elisions

### SAFE to Elide

| Operation | Condition | Example |
|-----------|-----------|---------|
| `__py.bool(x)` | x is comparison | `x > 0` |
| `__py.bool(x)` | x is known bool | `is_valid` |
| `__py.eq(a, b)` | Both primitives | `5 === 5` |
| `__py.add(a, b)` | Both numeric | `5 + 3` |
| `__py.at(arr, i)` | i is positive literal | `items[0]` |

### NEVER Elide (Python/JS differ)

| Operation | Python | JavaScript |
|-----------|--------|------------|
| `__py.bool([])` | False | true |
| `__py.bool({})` | False | true |
| `__py.eq([1], [1])` | True | false |
| `__py.add([1], [2])` | [1, 2] | "1,2" |
| `__py.mul("a", 3)` | "aaa" | NaN |
| `__py.at(arr, -1)` | Last item | undefined |
| `__py.mod(-7, 3)` | 2 | -1 |

---

## Debugging

### Check What Was Optimized

```python
from pynext.transpiler.optimizer import get_optimization_stats

stats = get_optimization_stats(original, optimized)
print(f"Elided {stats.original_py_calls - stats.optimized_py_calls} wrappers")
print(f"Remaining deps: {stats.runtime_deps}")
```

### Disable Specific Pass

```python
# Debug by disabling passes one at a time
options = OptimizeOptions(
    elision=False,  # Disable to see if elision causes issue
    inline=True,
    capture=True,
    dce=True,
)
```

### Check Type Inference

```python
from pynext.transpiler.optimizer import infer_types

env = infer_types(ir)
for var in ["x", "y", "items"]:
    print(f"{var}: {env.get_type(var)}")
```
