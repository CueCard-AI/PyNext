# Phase 18.5: Advanced Features

## Overview

Phase 18.5 implements advanced Python features for the PyNext transpiler:
- **Async/Await** - Full async function and await expression support
- **Generator Optimization** - Optimized generator expression transpilation
- **Decorators** - Python decorator syntax with runtime helpers
- **Unpacking** - Complete `*args`, `**kwargs`, and spread operator support

---

## WHO Should Use This

- **Frontend developers** using async APIs (fetch, WebSocket)
- **Application developers** needing caching (@memoize)
- **UI developers** handling events (@debounce, @throttle)
- **Library authors** creating flexible APIs (*args, **kwargs)
- **Performance optimizers** using generator expressions

---

## WHAT This Implements

### 1. Async/Await

Full Python async/await syntax transpilation:

```python
# Python
async def fetch_user(id):
    response = await fetch(f'/api/users/{id}')
    return await response.json()

# JavaScript
async function fetch_user(id) {
    let response = await fetch(`/api/users/${id}`);
    return await response.json();
}
```

**Features:**
- `async def` → `async function`
- `await expr` → `await expr`
- Nested awaits
- Await in loops, conditions, expressions
- Chained awaits
- Decorated async functions

### 2. Generator Expression Optimization

Instead of materializing generators to arrays, we emit optimized JavaScript:

| Python | Optimized JavaScript |
|--------|---------------------|
| `sum(x for x in items)` | `items.reduce((a,x) => a + x, 0)` |
| `any(x > 0 for x in items)` | `items.some(x => x > 0)` |
| `all(x > 0 for x in items)` | `items.every(x => x > 0)` |
| `list(x*2 for x in items)` | `items.map(x => x*2)` |
| `set(x for x in items)` | `new Set(items)` |

**With filters:**
```python
# Python
sum(x for x in items if x > 0)

# JavaScript
[...items].filter(x => x > 0).reduce((a, x) => a + x, 0)
```

### 3. Decorators

Python-style decorators with runtime helpers:

```python
# Python
@memoize
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

# JavaScript
const fib = __py.memoize(function fib(n) {
    if (n <= 1) {
        return n;
    }
    return __py.add(fib(n - 1), fib(n - 2));
});
```

**Available Decorators:**

| Decorator | Purpose | Example |
|-----------|---------|---------|
| `@memoize` | Cache function results | `@memoize def fib(n): ...` |
| `@debounce(ms)` | Delay until calls stop | `@debounce(300) def search(q): ...` |
| `@throttle(ms)` | Limit execution rate | `@throttle(100) def scroll(e): ...` |
| `@once` | Execute only once | `@once def init(): ...` |
| `@retry(n, delay)` | Retry on failure | `@retry(3, 100) async def fetch(): ...` |
| `@deprecated(msg)` | Log deprecation | `@deprecated("Use v2") def old(): ...` |
| `@log_calls` | Log invocations | `@log_calls def debug(): ...` |
| `@timed` | Measure execution | `@timed def process(): ...` |

**Stacked Decorators:**
```python
@log_calls
@memoize
def compute(x):
    return x * 2

# → const compute = __py.log_calls(__py.memoize(function compute(x) {...}));
```

### 4. Complete Unpacking

**Function Definitions:**

```python
# *args
def varargs(*args):
    return sum(args)

# → function varargs(...args) {
#       return __py.sum(args);
#   }

# **kwargs
def kwargs(**kw):
    return kw

# → function kwargs(kw = {}) {
#       return kw;
#   }

# Mixed with defaults
def mixed(a, b=1, *args):
    pass

# → function mixed(a, b = 1, ...args) { ... }

# *args + **kwargs together (FIXED!)
def wrapper(*args, **kwargs):
    return original(*args, **kwargs)

# → function wrapper(...args) {
#       const kwargs = (args.length > 0 && args[args.length - 1]?.__kw__) 
#           ? args.pop() : {};
#       return original(...args, {...kwargs, __kw__: true});
#   }

# Keyword-only args after *args (FIXED!)
def func(a, *args, key, value=None):
    return key

# → function func(a, ...args) {
#       const __kwargs__ = (args.length > 0 && args[args.length - 1]?.__kw__)
#           ? args.pop() : {};
#       const key = __kwargs__.key;
#       const value = __kwargs__.value ?? null;
#       return key;
#   }
```

**Function Calls:**

```python
# Spread
foo(*items)           # → foo(...items)

# Dict spread
foo(**config)         # → foo(config)

# Mixed
foo(*args, **kwargs)  # → foo(...args, kwargs)
```

**List/Dict Spread:**

```python
[*a, *b]              # → [...a, ...b]
{**a, **b}            # → {...a, ...b}
```

---

## WHEN To Use Each Feature

### Async/Await

Use for:
- API requests (fetch, axios)
- Database queries
- File operations
- Any I/O-bound operations
- WebSocket communication

```python
async def load_dashboard(user_id):
    # Parallel fetches
    profile = await fetch_profile(user_id)
    posts = await fetch_posts(user_id)
    return {'profile': profile, 'posts': posts}
```

### Generator Optimization

Use for:
- Data aggregation (`sum`, `any`, `all`)
- Transformations (`list`, `set`)
- Finding min/max
- Filtering collections

```python
# Instead of
total = 0
for x in items:
    if x > 0:
        total += x

# Write
total = sum(x for x in items if x > 0)
```

### Decorators

| Use Case | Decorator |
|----------|-----------|
| Expensive calculations | `@memoize` |
| Search input | `@debounce(300)` |
| Scroll handlers | `@throttle(16)` |
| Initialization | `@once` |
| Network requests | `@retry(3)` |
| Debugging | `@log_calls`, `@timed` |
| Migration notices | `@deprecated` |

### Unpacking

Use for:
- Flexible function signatures
- Forwarding arguments
- Merging configurations
- Collection concatenation

```python
def wrapper(*args, **kwargs):
    return original(*args, **kwargs)

config = {**defaults, **user_config, **overrides}
```

---

## WHERE These Features Apply

### In Event Handlers

```python
@debounce(300)
def on_search_input(event):
    query = event.target.value
    await search(query)

@throttle(16)
def on_scroll(event):
    update_position()
```

### In API Routes

```python
@memoize
async def get_user(user_id):
    return await db.users.find(user_id)

@retry(3)
async def external_api_call():
    return await fetch(external_url)
```

### In Utility Functions

```python
def merge(*dicts):
    result = {}
    for d in dicts:
        result = {**result, **d}
    return result

def validate(**rules):
    def decorator(fn):
        def wrapped(**kwargs):
            # Validate kwargs against rules
            return fn(**kwargs)
        return wrapped
    return decorator
```

---

## WHY These Features Matter

### Async/Await: Clean Asynchronous Code

**Without async/await:**
```python
fetch(url).then(lambda r: r.json()).then(lambda d: process(d))
```

**With async/await:**
```python
response = await fetch(url)
data = await response.json()
process(data)
```

Benefits:
- Linear, readable code
- Easy error handling with try/except
- Natural control flow

### Generator Optimization: Performance

**Naive implementation:**
```javascript
// Creates intermediate array
[...__py.iter(items).map(x => x * 2)]
```

**Optimized:**
```javascript
// Direct reduce, no intermediate array
items.reduce((a, x) => a + x * 2, 0)
```

Benefits:
- Less memory allocation
- Fewer iterations
- Faster execution

### Decorators: Code Reuse

Without decorators, you'd repeat:
```python
def fib(n):
    if n in _cache:
        return _cache[n]
    result = ...
    _cache[n] = result
    return result
```

With decorators:
```python
@memoize
def fib(n):
    return ...  # Just the logic
```

### Unpacking: Flexibility

Without unpacking:
```python
def wrapper(a, b, c, d, e):
    return original(a, b, c, d, e)
```

With unpacking:
```python
def wrapper(*args, **kwargs):
    return original(*args, **kwargs)
```

---

## HOW It Works

### Async/Await Transpilation

1. **Parser** detects `ast.AsyncFunctionDef` and `ast.Await`
2. Creates `FunctionDef(is_async=True)` and `Await` nodes
3. **Emitter** outputs `async function` and `await` keywords

```python
# IR nodes
FunctionDef(name="fetch", is_async=True, body=[
    Assignment(target="response", value=Await(
        value=Call(func="fetch", args=["url"])
    ))
])
```

### Generator Optimization

1. **Emitter** detects builtin call with `GeneratorExp` argument
2. `_try_optimize_generator_call()` matches patterns
3. Returns optimized JavaScript instead of materialized array

```python
# Detection
if isinstance(args[0], GeneratorExp):
    optimized = _try_optimize_generator_call(name, gen)
    if optimized:
        return optimized
```

### Decorator Transpilation

1. **Parser** creates `Decorator` nodes from `decorator_list`
2. Wraps function in `DecoratedFunction` node
3. **Emitter** applies decorators in reverse order

```python
# Python
@a
@b
def foo(): pass

# IR
DecoratedFunction(
    decorators=[Decorator("a"), Decorator("b")],
    function=FunctionDef("foo", ...)
)

# Output: const foo = a(b(function foo() {...}));
```

### Unpacking Transpilation

1. **Parser** extracts `vararg` and `kwarg` from `ast.arguments`
2. Stores in `FunctionDef` node
3. **Emitter** uses `_build_params_full()` for parameters

```python
# Python
def foo(a, *args, **kwargs): pass

# IR
FunctionDef(
    args=("a",),
    vararg="args",
    kwarg="kwargs"
)

# Output: function foo(a, ...args) { ... }
```

---

## Code Examples

### Complete Async Example

```python
async def fetch_dashboard(user_id):
    """Fetch all dashboard data for a user."""
    # Sequential fetches (dependent data)
    user = await fetch_user(user_id)
    
    if not user:
        return None
    
    # Independent fetches
    profile = await fetch_profile(user.profile_id)
    settings = await fetch_settings(user_id)
    
    # Process
    return {
        'user': user,
        'profile': profile,
        'settings': settings
    }
```

### Complete Decorator Example

```python
@log_calls
@memoize
@retry(3)
async def fetch_with_cache(url):
    """Cached, logged, retrying fetch."""
    response = await fetch(url)
    if not response.ok:
        raise FetchError(response.status)
    return await response.json()
```

### Complete Unpacking Example

```python
def create_element(tag, *children, **props):
    """Create a virtual DOM element."""
    return {
        'tag': tag,
        'children': list(children),
        'props': props
    }

# Usage
div = create_element('div',
    create_element('h1', 'Title'),
    create_element('p', 'Content'),
    className='container',
    id='main'
)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Python Source                          │
│  async def foo(*args, **kwargs):                           │
│      result = await bar(*args, **kwargs)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Parser (parser.py)                     │
│  - Detects async, await, decorators, *args, **kwargs       │
│  - Creates IR nodes: Await, Decorator, DecoratedFunction   │
│  - Updates FunctionDef with vararg, kwarg fields           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      IR Nodes (nodes.py)                    │
│  - Await(value)                                             │
│  - Decorator(name, args, kwargs)                            │
│  - DecoratedFunction(decorators, function)                  │
│  - FunctionDef(vararg, kwarg, kwonly_args, kwonly_defaults)│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Emitter (emitter.py)                   │
│  - _emit_await(): await expr                                │
│  - _emit_decorated_function(): decorator wrapping           │
│  - _build_params_full(): ...args, kwargs = {}              │
│  - _try_optimize_generator_call(): reduce/some/every/map   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Runtime (decorators.js)                │
│  - memoize(fn)                                              │
│  - debounce(ms)(fn)                                         │
│  - throttle(ms)(fn)                                         │
│  - once, retry, deprecated, log_calls, timed               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      JavaScript Output                      │
│  const foo = __py.memoize(async function foo(...args) {    │
│      let result = await bar(...args);                       │
│  });                                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Test Coverage

| Component | Python Tests | JavaScript Tests | Total |
|-----------|-------------|------------------|-------|
| Async/Await | 156 | 20 | 176 |
| Generator Optimization | 170 | - | 170 |
| Decorators | 90 | 60 | 150 |
| Unpacking | 178 | 20 | 198 |
| Risk Cases | 48 | - | 48 |
| Risk Hardening | 95 | - | 95 |
| P1/P2 Risk Areas | 80 | 10 | 90 |
| **Total** | **817** | **108** | **925** |

## Risk Areas Fixed (Phase 18.5.1)

The following high-risk areas have been addressed:

### ✅ P0: `*args` + `**kwargs` Together
**Problem:** kwargs was silently dropped when used with `*args`

**Solution:** Mark kwargs with `__kw__: true` and extract in function body

```python
def wrapper(*args, **kwargs):
    return original(*args, **kwargs)

# → function wrapper(...args) {
#       const kwargs = (args.length > 0 && args[args.length - 1]?.__kw__) 
#           ? args.pop() : {};
#       return original(...args, {...kwargs, __kw__: true});
#   }
```

### ✅ P0: Keyword-only Args After `*`
**Problem:** Keyword-only args became positional, breaking semantics

**Solution:** Extract from kwargs object in function body

```python
def func(a, *args, key, value=None):
    return key

# → function func(a, ...args) {
#       const __kwargs__ = (args.length > 0 && args[args.length - 1]?.__kw__)
#           ? args.pop() : {};
#       const key = __kwargs__.key;
#       const value = __kwargs__.value ?? null;
#       return key;
#   }
```

### ✅ P1: Boolean Short-Circuit Side Effects
**Problem:** Both sides of `and`/`or` were evaluated before short-circuit logic

**Solution:** Lazy evaluation - only evaluate subsequent operands when needed

```python
get_a() and get_b()  # get_b() only called if get_a() is truthy

# → ((_b0) => __py.bool(_b0) ? get_b() : _b0)(get_a())
```

### ✅ P1: Generator Tuple Unpacking
**Problem:** Invalid JS syntax `[a, b] => ...`

**Solution:** Wrap destructuring in parens: `([a, b]) => ...`

```python
sum(a*b for a, b in pairs)

# → [...pairs].reduce((__acc__, [a, b]) => __acc__ + (a * b), 0)
```

### ✅ P2: Decorator Spreads
**Problem:** `@decorator(**spread)` was ignored

**Solution:** Parse and emit starred/double-starred in decorators

```python
@config(**settings)
def setup(): pass

# → const setup = config({...settings})(function setup() { ... })
```

### ✅ P2: Memoize Cache Key Collisions
**Problem:** Different types with same value could collide (e.g., `1` vs `"1"`)

**Solution:** Type-prefixed cache keys

```javascript
// Before: key = JSON.stringify(args)
// After: key = makeKey(args) with type prefixes
```

### Test Files

**Python Tests:**
- `tests/unit/transpiler/test_185_async.py` - 156 tests
- `tests/unit/transpiler/test_185_generators.py` - 170 tests
- `tests/unit/transpiler/test_185_decorators.py` - 90 tests
- `tests/unit/transpiler/test_185_unpacking.py` - 178 tests
- `tests/unit/transpiler/test_185_risk_cases.py` - 48 tests
- `tests/unit/transpiler/test_185_risk_hardening.py` - 95 tests
- `tests/unit/transpiler/test_185_p1_p2_risks.py` - 80 tests

**JavaScript Tests:**
- `tests/js/transpiler/advanced.test.js` - 108 tests (includes cache key collision tests)

---

## Runtime Size

| Component | Size (minified) | Size (gzipped) |
|-----------|----------------|----------------|
| decorators.js | ~4KB | ~1.5KB |
| Existing runtime | ~14KB | ~5KB |
| **Total** | ~18KB | ~6.5KB |

---

## Version History

### Phase 18.5 (Current)

- Added `Await` IR node and parser support
- Implemented generator expression optimization
- Added `Decorator` and `DecoratedFunction` nodes
- Created `decorators.js` runtime
- Extended `FunctionDef` with vararg/kwarg
- Added `*args`, `**kwargs` parsing and emission
- 694 comprehensive tests
