# Python Builtins & Standard Library Reference

## WHO Uses This

- **PyNext Transpiler**: Converts Python builtin calls to JavaScript equivalents
- **Developers**: Debugging transpiled code, understanding the mapping
- **LLMs**: Extending the runtime, helping developers build applications

## WHAT This Does

Maps Python builtin functions and standard library modules to JavaScript equivalents with **exact semantic parity**.

## WHY This Exists

Python builtins and stdlib have subtle differences from JavaScript:

| Python | JavaScript | Difference | Solution |
|--------|------------|------------|----------|
| `sorted(['b', 'a'])` | `[...x].sort()` → `['a', 'b']` but `[10, 2].sort()` → `[10, 2]`! | JS sort is lexicographic | Always use `__py.sorted()` |
| `sorted([1, 'a'])` | No error | Python throws TypeError | Type checking in runtime |
| `round(2.5)` | `Math.round(2.5)` → 3 | Python → 2 (banker's rounding) | `__py.round()` |
| `min([])` | `Math.min(...[])` → Infinity | Python throws ValueError | `__py.min()` |
| `min([1, 'a'])` | No error | Python throws TypeError | Type checking in runtime |
| `any([[], {}])` | `[[], {}].some(Boolean)` → true | Python → false | `__py.any()` with truthiness |
| `filter(None, items)` | `items.filter(Boolean)` | Truthy differs | `__py.filter()` |
| `re.match(pattern, s)` | `s.match(regex)` | Python anchors at start | Prepend `^` |
| `random.seed(42)` | `Math.random()` not seedable | No reproducibility | xorshift128+ PRNG |
| `random.shuffle(items)` | N/A | Must be in-place, return None | Fisher-Yates |

## Critical Semantic Fixes

### 1. sorted() - Always Use Runtime

**Problem**: JavaScript's `.sort()` is lexicographic by default:
```javascript
[10, 2, 3].sort()  // → [10, 2, 3] WRONG!
['b', 'a'].sort()  // → ['a', 'b'] OK
```

**Solution**: Always emit `__py.sorted()`:
```python
sorted([3, 1, 2])           # → __py.sorted([3, 1, 2], null, false)
sorted(items)               # → __py.sorted(items, null, false)
sorted(items, reverse=True) # → __py.sorted(items, null, true)
sorted(items, key=len)      # → __py.sorted(items, len, false)
```

**Runtime Features**:
- Stable sort (preserves order of equal elements)
- Type checking (throws TypeError on mixed types)
- Proper string lexicographic sorting
- Proper numeric sorting

### 2. min/max() - Type Checking

**Problem**: JavaScript doesn't throw on mixed types:
```javascript
Math.min(1, 'a')  // → NaN (silent failure)
```

**Solution**: Always emit `__py.min()` / `__py.max()`:
```python
min(items)        # → __py.min(items, null)
max(a, b, c)      # → __py.max([a, b, c], null)
min(items, key=f) # → __py.min(items, f)
```

**Runtime Features**:
- Throws Error on empty sequence
- Throws TypeError on mixed types (like Python 3)
- Supports key function

### 3. round() - Banker's Rounding

**Problem**: Python uses "round half to even" (banker's rounding):
```python
round(2.5)  # → 2 (not 3!)
round(3.5)  # → 4
round(4.5)  # → 4 (not 5!)
```

**Solution**: `__py.round()` implements banker's rounding:
```python
round(x)      # → __py.round(x, 0)  # With banker's rounding
round(x, 2)   # → __py.round(x, 2)
```

### 4. filter(None) - Always Use Runtime

**Problem**: Variable named `None` vs literal `None`:
```python
f = None
filter(f, items)   # Should filter falsy values
filter(None, items) # Same behavior
```

**Solution**: Always emit `__py.filter()`:
```python
filter(None, items)  # → __py.filter(null, items)
filter(f, items)     # → __py.filter(f, items)
```

**Runtime** checks if first arg is `null`/`undefined` and filters by truthiness.

## HOW It Works

### Architecture

```
pynext/transpiler/
├── emitter.py          # _emit_builtin_call(), stdlib handling
└── runtime/
    ├── builtins.js     # Enhanced builtins (sorted, min, max, any, all, etc.)
    └── stdlib/
        ├── json.js     # JSON parsing/serialization
        ├── math.js     # Math functions and constants
        ├── re.js       # Regular expressions
        └── random.js   # Random number generation
```

### Builtin Categories

#### 1. Type Conversion Builtins

| Python | JavaScript | Notes |
|--------|------------|-------|
| `str(x)` | `String(x)` | Direct mapping |
| `int(x)` | `parseInt(x)` | |
| `float(x)` | `parseFloat(x)` | |
| `bool(x)` | `__py.bool(x)` | Python truthiness! |
| `list(x)` | `[...x]` | |
| `dict(x)` | `Object.fromEntries(x)` | |
| `set(x)` | `new Set(x)` | |
| `tuple(x)` | `Object.freeze([...x])` | Immutable |

#### 2. Aggregate Builtins

| Python | JavaScript | Notes |
|--------|------------|-------|
| `len(x)` | `__py.len(x)` | Handles dict, set, Map sizes |
| `sum(items)` | `__py.sum(items)` | |
| `sum(items, start)` | `__py.sum(items, start)` | |
| `abs(x)` | `Math.abs(x)` | |
| `round(x)` | `__py.round(x, 0)` | **Banker's rounding!** |
| `round(x, n)` | `__py.round(x, n)` | |
| `min(items)` | `__py.min(items, null)` | Type checking, empty error |
| `min(a, b, c)` | `__py.min([a, b, c], null)` | |
| `max(items)` | `__py.max(items, null)` | Type checking, empty error |
| `sorted(items)` | `__py.sorted(items, null, false)` | Stable, type-safe |

#### 3. Enhanced Builtins (with `key=` support)

```python
# sorted with key and reverse
sorted(items, key=len, reverse=True)
# → __py.sorted(items, len, true)

# min/max with key
min(items, key=lambda x: x.score)
# → __py.min(items, (x) => x.score)
```

#### 4. Boolean Aggregates

```python
# any/all use Python truthiness
any([[], {}, 0])  # False (all falsy in Python)
# → __py.any([[], {}, 0])

all([1, "a", [1]])  # True
# → __py.all([1, "a", [1]])
```

#### 5. Iteration Builtins

| Python | JavaScript | Notes |
|--------|------------|-------|
| `enumerate(items)` | `__py.enumerate(items)` | |
| `enumerate(items, 1)` | `__py.enumerate(items, 1)` | Start index |
| `zip(a, b)` | `__py.zip(a, b)` | |
| `range(n)` | `__py.range(0, n)` | |
| `range(a, b, step)` | `__py.range(a, b, step)` | |
| `reversed(items)` | `[...items].reverse()` | |

#### 6. Filter and Map

```python
# filter ALWAYS uses __py.filter for proper None handling
filter(fn, items)        # → __py.filter(fn, items)
filter(None, items)      # → __py.filter(null, items)
filter(lambda x: x, l)   # → __py.filter((x) => x, l)

# Why? Because a variable could be None:
f = None
filter(f, items)  # Must use Python truthiness!
```

```python
# map with single iterable
map(fn, items)
# → [...items].map(fn)

# map with multiple iterables
map(add, iter1, iter2)
# → __py.map(add, iter1, iter2)
```

#### 7. New Builtins

| Python | JavaScript | Notes |
|--------|------------|-------|
| `divmod(a, b)` | `__py.divmod(a, b)` | Returns [q, r] |
| `pow(x, y)` | `Math.pow(x, y)` | |
| `pow(x, y, z)` | `__py.pow(x, y, z)` | Modular exponentiation |
| `callable(x)` | `typeof x === 'function'` | |
| `repr(x)` | `__py.repr(x)` | Python representation |

---

## Standard Library

### json Module

```python
# Parsing JSON
data = json.loads('{"key": "value"}')
# → data = JSON.parse('{"key": "value"}')

# Serializing with indentation
s = json.dumps(obj, indent=2)
# → s = JSON.stringify(obj, null, 2)

# With sort_keys
s = json.dumps(obj, sort_keys=True)
# → s = __py.json.dumps(obj, null, true)
```

### math Module

**Constants (direct emitter handling):**

The emitter handles math module constants directly for optimal output:
```python
math.pi    # → Math.PI
math.e     # → Math.E
math.tau   # → (2 * Math.PI)
math.inf   # → Infinity
math.nan   # → NaN
```

This is handled at transpile time in the emitter's `_emit_attribute()` function, not at runtime.

**Basic Functions:**
```python
math.floor(x)    # → Math.floor(x)
math.ceil(x)     # → Math.ceil(x)
math.sqrt(x)     # → Math.sqrt(x)
math.pow(x, y)   # → Math.pow(x, y)
math.exp(x)      # → Math.exp(x)
```

**Logarithms:**
```python
math.log(x)      # → Math.log(x)
math.log(x, 10)  # → Math.log(x) / Math.log(10)
math.log10(x)    # → Math.log10(x)
math.log2(x)     # → Math.log2(x)
```

**Trigonometry:**
```python
math.sin(x)      # → Math.sin(x)
math.cos(x)      # → Math.cos(x)
math.tan(x)      # → Math.tan(x)
math.atan2(y, x) # → Math.atan2(y, x)
```

**Special Functions:**
```python
math.isnan(x)    # → Number.isNaN(x)
math.isinf(x)    # → !Number.isFinite(x) && !Number.isNaN(x)
math.factorial(n) # → __py.math.factorial(n)
math.gcd(a, b)   # → __py.math.gcd(a, b)
```

### re Module

```python
# Match at start (Python anchors at ^)
m = re.match(r'\d+', text)
# → m = __py.re.match('\\d+', text)

# Search anywhere
m = re.search(r'\d+', text)
# → m = __py.re.search('\\d+', text)

# Find all matches
matches = re.findall(r'\d+', text)
# → matches = __py.re.findall('\\d+', text)

# Substitute
result = re.sub(r'\s+', ' ', text)
# → result = __py.re.sub('\\s+', ' ', text)

# Split
parts = re.split(r'\s+', text)
# → parts = __py.re.split('\\s+', text)
```

**Match Object (with group position tracking):**
```python
m = re.search(r'(\w+)@(\w+)', 'user@host')

# Group access
m.group()     # → 'user@host' (full match)
m.group(0)    # → 'user@host' (same)
m.group(1)    # → 'user'
m.group(2)    # → 'host'
m.groups()    # → ['user', 'host']

# Position tracking (NEW: works for groups!)
m.start()     # → 0 (start of full match)
m.end()       # → 9 (end of full match)
m.start(1)    # → 0 (start of group 1)
m.end(1)      # → 4 (end of group 1)
m.span(1)     # → [0, 4]

# Other properties
m.string      # → 'user@host' (original string)
m.lastindex   # → 2 (last matched group index)
```

**Implementation Details:**
- Uses ES2022 regex indices (`d` flag) when available
- Falls back to position estimation for older browsers
- Properly handles unmatched optional groups (returns -1)

### random Module

**🎉 NEW: Seedable PRNG!**

The random module now supports **reproducible random sequences** using the xorshift128+ algorithm:

```python
# Seed for reproducibility
random.seed(42)              # → __py.random.seed(42)
random.seed("hello")         # → __py.random.seed("hello")  # String seeds work!
random.seed(None)            # → __py.random.seed(null)     # Return to unseeded

# Same seed = same sequence!
random.seed(42)
a = random.random()          # Always the same value
b = random.randint(1, 100)   # Always the same value

random.seed(42)
c = random.random()          # c == a !
d = random.randint(1, 100)   # d == b !
```

**State Management:**
```python
# Save and restore state
state = random.getstate()    # → __py.random.getstate()
# ... do random stuff ...
random.setstate(state)       # → __py.random.setstate(state)
# Back to saved position!
```

**Basic Functions:**
```python
random.random()              # → __py.random.random()
random.uniform(a, b)         # → __py.random.uniform(a, b)
random.randint(a, b)         # → __py.random.randint(a, b)  # INCLUSIVE both ends!
random.randrange(0, 10, 2)   # → __py.random.randrange(0, 10, 2)
```

**Selection:**
```python
random.choice(items)         # → __py.random.choice(items)
random.choices(items, k=3)   # → __py.random.choices(items, 3)
random.sample(items, k)      # → __py.random.sample(items, k)  # Unique elements!
```

**Shuffle (IN-PLACE, returns None!):**
```python
random.shuffle(items)        # → __py.random.shuffle(items)
# items is modified, return value is undefined
```

**Distributions:**
```python
random.gauss(mu, sigma)      # → __py.random.gauss(mu, sigma)
random.normalvariate(mu, s)  # → __py.random.gauss(mu, s)  # Alias
random.expovariate(lambd)    # → __py.random.expovariate(lambd)
random.triangular(lo, hi)    # → __py.random.triangular(lo, hi)
```

**Implementation Details:**
- Uses **xorshift128+** algorithm (same family as V8's Math.random)
- 128-bit state, 2^128-1 period
- Passes BigCrush statistical tests
- All random functions use the seeded PRNG when seeded

---

## Adding New Builtins

### Step 1: Add to Emitter

In `pynext/transpiler/emitter.py`:

```python
def _emit_builtin_call(name: str, args: tuple, keywords: tuple) -> Optional[str]:
    # For simple builtins
    if name == "mybuiltin":
        return f"__py.mybuiltin({args_js[0]})"
    
    # For builtins with keyword args
    if name == "sorted":
        key = kwargs.get("key", "null")
        reverse = kwargs.get("reverse", "false")
        return f"__py.sorted({args_js[0]}, {key}, {reverse})"
```

### Step 2: Add to Runtime

In `pynext/transpiler/runtime/builtins.js`:

```javascript
export function mybuiltin(x) {
    // Implementation with Python semantics
}
```

### Step 3: Add Tests

Python test in `tests/unit/transpiler/test_builtins.py`:
```python
def test_mybuiltin_basic(self):
    result = transpile_expression('mybuiltin(x)')
    assert '__py.mybuiltin(x)' in result
```

JavaScript test in `tests/js/transpiler/builtins.test.js`:
```javascript
test('mybuiltin basic', () => {
    expect(__py.mybuiltin(x)).toBe(expected);
});
```

---

## Test Coverage

| Category | Python Tests | JS Tests |
|----------|--------------|----------|
| Type conversion | 20 | 10 |
| Aggregates | 15 | 10 |
| sorted/min/max | 20 | 20 |
| any/all | 10 | 10 |
| filter/map | 15 | 10 |
| Iteration | 15 | 10 |
| Introspection | 15 | 10 |
| Other builtins | 15 | 10 |
| json | 20 | 15 |
| math | 40 | 20 |
| re | 25 | 20 |
| random (with seed!) | 25 | 25 |
| **Risk Area Hardening** | - | **84** |
| **Total** | **235** | **254** |

### Risk Area Tests (`builtins_risk.test.js`)

| Risk Area | Tests | What's Verified |
|-----------|-------|-----------------|
| `sorted()` | 8 | Stable sort, string sorting, type errors |
| `min/max` | 12 | Empty errors, type errors, key functions |
| `filter(None)` | 5 | Python truthiness, null/undefined |
| `round()` | 8 | Banker's rounding (2.5→2, 3.5→4) |
| `any/all` | 7 | Empty containers are falsy |
| `random.seed()` | 10 | Reproducibility, getstate/setstate |
| `re.match()` | 7 | Group positions, start/end |
| `math` | 10 | Constants, special functions |
| `json` | 3 | sort_keys, indent |
| `len/pow/divmod` | 14 | Edge cases |

---

## Runtime Size

| Module | Size (minified) |
|--------|-----------------|
| builtins.js | ~3KB |
| json.js | ~0.5KB |
| math.js | ~1.5KB |
| re.js | ~2KB |
| random.js | ~2.5KB |
| **Total** | ~9.5KB |

All modules are tree-shakeable - only used functions are included in the final bundle.

---

## Version History

### Phase 18.4 Hardening

Added comprehensive fixes for high-risk semantic differences:

1. **sorted()**: Always uses `__py.sorted()` for stable sort + type checking
2. **min/max()**: Type checking, proper empty sequence errors
3. **round()**: Banker's rounding (round half to even)
4. **random.seed()**: Full seedable PRNG with xorshift128+
5. **re.match()**: Group position tracking with ES2022 indices
6. **filter()**: Always uses `__py.filter()` for proper None handling
7. **math constants**: Direct emitter handling for optimal output

Total new tests: 84 JavaScript + updated Python tests
