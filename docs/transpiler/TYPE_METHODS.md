# Type Methods Reference (Phase 18.3)

## Overview

This document covers the transpilation of Python type methods (string, list, dict, set) to JavaScript equivalents. Phase 18.3 implements 64 methods with exact Python semantics.

---

## WHO Uses This

- **PyNext Transpiler**: Converts Python method calls to JavaScript
- **Developers**: Debugging transpiled JavaScript output
- **LLMs**: Extending the transpiler with new methods
- **Contributors**: Understanding the mapping patterns

---

## WHAT This Does

Maps Python type methods to JavaScript equivalents with three categories:

| Category | Description | Example |
|----------|-------------|---------|
| **Direct Mapping** | Same semantics, different name | `s.lower()` → `s.toLowerCase()` |
| **Simple Transform** | Minor syntax change | `",".join(items)` → `items.join(",")` |
| **Runtime Helper** | Different semantics | `s.split()` → `__py.str.split(s)` |

---

## WHY This Exists

Python and JavaScript have critical semantic differences:

| Python | JavaScript | Problem |
|--------|------------|---------|
| `"a b".split()` → `["a", "b"]` | `"a b".split()` → `["a b"]` | Python splits on whitespace |
| `[1,2].remove([1])` throws | `arr.indexOf([1])` returns -1 | Python uses deep equality |
| `{}.pop("k")` throws KeyError | `obj["k"]` returns undefined | Python throws on missing |
| `[10,2,1].sort()` → `[1,2,10]` | `[10,2,1].sort()` → `[1,10,2]` | Python sorts numerically |

---

## HOW It Works

### Architecture

```
Python Source           Emitter                 JavaScript Output
─────────────           ───────                 ─────────────────
s.lower()          →    STRING_DIRECT["lower"]  → s.toLowerCase()
s.split()          →    STRING_RUNTIME["split"] → __py.str.split(s)
items.remove(x)    →    LIST_RUNTIME["remove"]  → __py.list.remove(items, x)
```

### Runtime Structure

```
pynext/transpiler/runtime/
├── core.js              # Base functions (at, slice, bool, eq, etc.)
└── types/
    ├── index.js         # Export all type helpers
    ├── string.js        # 25 string methods
    ├── list.js          # 15 list methods  
    ├── dict.js          # 12 dict methods
    └── set.js           # 12 set methods
```

---

## String Methods

### Direct Mappings (Same Semantics)

| Python | JavaScript | Notes |
|--------|------------|-------|
| `s.lower()` | `s.toLowerCase()` | |
| `s.upper()` | `s.toUpperCase()` | |
| `s.startswith(x)` | `s.startsWith(x)` | |
| `s.endswith(x)` | `s.endsWith(x)` | |
| `s.find(x)` | `s.indexOf(x)` | |
| `s.rfind(x)` | `s.lastIndexOf(x)` | |

### Runtime Helpers (Different Semantics)

| Python | JavaScript | Difference |
|--------|------------|------------|
| `s.split()` | `__py.str.split(s)` | Python splits on whitespace |
| `s.split(",", 2)` | `__py.str.split(s, ",", 2)` | Maxsplit support |
| `s.index(x)` | `__py.str.index(s, x)` | Throws ValueError if not found |
| `s.count(x)` | `__py.str.count(s, x)` | Non-overlapping count |
| `s.title()` | `__py.str.title(s)` | Titlecase algorithm |
| `s.capitalize()` | `__py.str.capitalize(s)` | First char upper, rest lower |
| `s.center(10)` | `__py.str.center(s, 10)` | With fill character support |

### Special Cases

```python
# Strip with custom characters
s.strip()        → s.trim()                    # No args
s.strip("xy")    → __py.str.strip(s, "xy")     # With chars

# Replace with count
s.replace("a", "b")      → s.replaceAll("a", "b")
s.replace("a", "b", 1)   → __py.str.replace(s, "a", "b", 1)

# Join is reversed
",".join(items)  → items.join(",")
```

---

## List Methods

### Direct Mappings

| Python | JavaScript | Notes |
|--------|------------|-------|
| `items.reverse()` | `items.reverse()` | Same behavior |
| `items.append(x)` | `items.push(x)` | Different name |
| `items.extend(other)` | `items.push(...other)` | Spread syntax |
| `items.copy()` | `[...items]` | Spread copy |
| `items.clear()` | `(items.length = 0)` | Length trick |

### Runtime Helpers

| Python | JavaScript | Difference |
|--------|------------|------------|
| `items.remove(x)` | `__py.list.remove(items, x)` | Deep equality, throws |
| `items.index(x)` | `__py.list.index(items, x)` | Deep equality, throws |
| `items.count(x)` | `__py.list.count(items, x)` | Deep equality |
| `items.sort()` | `__py.list.sort(items)` | Numeric by default |
| `items.pop(i)` | `__py.list.pop(items, i)` | With index support |
| `items.insert(i, x)` | `__py.list.insert(items, i, x)` | Negative index support |

### Sort with Key and Reverse

```python
# Python
items.sort(key=len, reverse=True)

# JavaScript
__py.list.sort(items, len, true)
```

---

## Dict Methods

### Direct Mappings

| Python | JavaScript | Notes |
|--------|------------|-------|
| `d.keys()` | `Object.keys(d)` | |
| `d.values()` | `Object.values(d)` | |
| `d.items()` | `Object.entries(d)` | |
| `d.copy()` | `{...d}` | Spread copy |

### Runtime Helpers

| Python | JavaScript | Difference |
|--------|------------|------------|
| `d.get(k)` | `__py.dict.get(d, k)` | Returns null, not undefined |
| `d.get(k, v)` | `__py.dict.get(d, k, v)` | With default |
| `d.pop(k)` | `__py.dict.pop(d, k)` | Throws KeyError |
| `d.pop(k, v)` | `__py.dict.pop(d, k, v)` | With default |
| `d.setdefault(k, v)` | `__py.dict.setdefault(d, k, v)` | Sets and returns |
| `d.popitem()` | `__py.dict.popitem(d)` | LIFO order, throws |

---

## Set Methods

### Direct Mappings

| Python | JavaScript | Notes |
|--------|------------|-------|
| `s.add(x)` | `s.add(x)` | Same behavior |
| `s.clear()` | `s.clear()` | Same behavior |

### Runtime Helpers

| Python | JavaScript | Difference |
|--------|------------|------------|
| `s.remove(x)` | `__py.set.remove(s, x)` | Throws KeyError |
| `s.discard(x)` | `__py.set.discard(s, x)` | Ignores missing |
| `s.pop()` | `__py.set.pop(s)` | Arbitrary element |
| `s.union(t)` | `__py.set.union(s, t)` | Returns new set |
| `s.intersection(t)` | `__py.set.intersection(s, t)` | |
| `s.difference(t)` | `__py.set.difference(s, t)` | |
| `s.issubset(t)` | `__py.set.issubset(s, t)` | |
| `s.issuperset(t)` | `__py.set.issuperset(s, t)` | |
| `s.isdisjoint(t)` | `__py.set.isdisjoint(s, t)` | |

---

## Usage Examples

### Basic Method Calls

```python
# Python
name = "  HELLO WORLD  "
clean = name.strip().lower()
words = clean.split()

# Transpiled JavaScript
let name = "  HELLO WORLD  ";
let clean = name.trim().toLowerCase();
let words = __py.str.split(clean);
```

### List Operations

```python
# Python
items = [3, 1, 4, 1, 5]
items.sort()
items.remove(1)
i = items.index(4)

# Transpiled JavaScript
let items = [3, 1, 4, 1, 5];
__py.list.sort(items);
__py.list.remove(items, 1);
let i = __py.list.index(items, 4);
```

### Dict Operations

```python
# Python
config = {"debug": True}
port = config.get("port", 8080)
config.setdefault("host", "localhost")

# Transpiled JavaScript
let config = {"debug": true};
let port = __py.dict.get(config, "port", 8080);
__py.dict.setdefault(config, "host", "localhost");
```

---

## Type Disambiguation

The transpiler cannot always determine the type of a variable. When ambiguous:

1. String methods take precedence (`.index()`, `.count()`)
2. List methods are used for `.remove()`
3. Dict methods are used for `.get()`, `.pop()` with string keys

For explicit type handling, use type hints in the future (Phase 18.5+).

---

## Test Coverage

| Type | Python Tests | JS Tests | Methods |
|------|-------------|----------|---------|
| String | 88 | 91 | 25 |
| List | 54 | 91 | 15 |
| Dict | 45 | 91 | 12 |
| Set | 29 | 91 | 12 |
| **Total** | **216** | **91** | **64** |

---

## Adding New Methods

To add a new method:

1. **Add to runtime** (`types/string.js`, etc.)
2. **Update emitter** (`emitter.py` method dispatch)
3. **Add Python tests** (`test_*_methods.py`)
4. **Add JS tests** (`types.test.js`)
5. **Update this doc**

Pattern for runtime helper:

```javascript
// types/string.js
export function newMethod(s, arg) {
    // Implement Python semantics
    return result;
}
```

Pattern for emitter:

```python
# emitter.py
STRING_RUNTIME = {
    # ...
    "new_method": "__py.str.newMethod",
}
```
