# Phase 18.2: Expressions, Operators & Comprehensions

## Overview

Phase 18.2 adds complete support for Python expressions, operators, and comprehensions to the PyNext transpiler.

---

## Who Uses This

- **PyNext developers**: Write Python comprehensions and f-strings that work in the browser
- **Event handlers**: Use list/dict comprehensions in onclick handlers
- **Data processing**: Filter, map, and transform data with Python syntax
- **AI assistants**: Extend and debug the transpiler

---

## What It Does

Transpiles Python expressions to equivalent JavaScript:

| Python | JavaScript |
|--------|------------|
| `0 < x < 10` | `(0 < x) && (x < 10)` |
| `x and y` | `__py.bool(x) ? y : x` |
| `f"Hello {name}"` | `` `Hello ${name}` `` |
| `f"{x:.2f}"` | `` `${__py.format(x, '.2f')}` `` |
| `[x*2 for x in items]` | `[...items.map(x => x*2)]` |
| `{k: v for k, v in items}` | `Object.fromEntries(items.map(([k,v]) => [k,v]))` |
| `{x for x in items}` | `new Set(items)` |
| `any(x > 0 for x in items)` | `items.some(x => x > 0)` |

---

## Why It Exists

Python and JavaScript have different semantics that break code if not handled correctly:

### Boolean Operators Return Values

```python
# Python: returns actual value, not boolean
x = [] or "default"  # → "default"
x = [1] and "yes"    # → "yes"
```

```javascript
// JavaScript: returns boolean
x = [] || "default"  // → [] (truthy!)
x = [1] && "yes"     // → "yes"
```

The transpiler uses `__py.bool()` to handle Python truthiness.

### F-Strings with Format Specs

Python format specs don't exist in JavaScript:

```python
f"{3.14159:.2f}"    # → "3.14"
f"{1234:,}"         # → "1,234"
f"{text:>10}"       # → "      text"
```

The transpiler uses `__py.format()` runtime helper.

### Comprehensions

Python's concise comprehension syntax maps to JS methods:

```python
[x*2 for x in items if x > 0]
```

→

```javascript
[...items.filter(x => x > 0).map(x => x*2)]
```

---

## How It Works

### Architecture

```
Python Source
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                      Parser                              │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │ _parse_fstring│  │_parse_list_   │  │_parse_      │ │
│  │               │  │comp           │  │generator_exp│ │
│  └───────────────┘  └───────────────┘  └─────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
                    IR Nodes
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                      Emitter                             │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │ _emit_fstring │  │_emit_list_comp│  │_emit_set_   │ │
│  │               │  │               │  │comp         │ │
│  └───────────────┘  └───────────────┘  └─────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
                  JavaScript Output
```

### IR Nodes

```python
@dataclass(frozen=True)
class FString(JSNode):
    """f"Hello {name}" → template literal"""
    parts: tuple           # Alternating str and JSNode
    format_specs: tuple    # Format spec per expression

@dataclass(frozen=True)
class ListComp(JSNode):
    """[x*2 for x in items if x > 0]"""
    element: JSNode
    generators: tuple[Comprehension, ...]

@dataclass(frozen=True)
class Comprehension(JSNode):
    """for x in items if cond"""
    target: str
    targets: tuple[str, ...]  # For tuple unpacking
    iter: JSNode
    ifs: tuple[JSNode, ...]
```

---

## When to Use

### Use Comprehensions

```python
# Good: Concise and readable
active = [item for item in items if item.active]
by_id = {item.id: item for item in items}
unique_tags = {tag for item in items for tag in item.tags}
```

### Use F-Strings

```python
# Good: Clear and formatted
message = f"Hello {user.name}!"
price = f"${amount:.2f}"
status = f"Progress: {percent:.1%}"
```

### Use Chained Comparisons

```python
# Good: Mathematical notation
if 0 <= index < len(items):
    process(items[index])
```

---

## Examples

### List Comprehension

```python
# Python
squares = [x**2 for x in range(10) if x % 2 == 0]
```

```javascript
// Generated JavaScript
let squares = [...__py.iter(__py.range(0, 10)).filter(x => __py.mod(x, 2) === 0).map(x => x ** 2)];
```

### Dict Comprehension

```python
# Python
word_lengths = {word: len(word) for word in words}
```

```javascript
// Generated JavaScript
let word_lengths = Object.fromEntries([...__py.iter(words)].map(word => [word, word.length]));
```

### F-String with Formatting

```python
# Python
display = f"Total: ${total:,.2f} ({percent:.1%})"
```

```javascript
// Generated JavaScript
let display = `Total: $${__py.format(total, ',.2f')} (${__py.format(percent, '.1%')})`;
```

### Boolean Short-Circuit

```python
# Python
name = user.name or "Anonymous"
valid = user and user.active
```

```javascript
// Generated JavaScript
let name = (__py.bool(user.name) ? user.name : "Anonymous");
let valid = (__py.bool(user) ? user.active : user);
```

---

## Where (File Locations)

| File | Purpose |
|------|---------|
| `pynext/transpiler/nodes.py` | IR node definitions |
| `pynext/transpiler/parser.py` | Python AST → IR |
| `pynext/transpiler/emitter.py` | IR → JavaScript |
| `pynext/transpiler/runtime/core.js` | Runtime helpers |
| `tests/unit/transpiler/test_*.py` | Comprehensive tests |

---

## Runtime Helpers

### `__py.format(value, spec)`

Implements Python format specifications:

```javascript
__py.format(3.14159, '.2f')   // → "3.14"
__py.format(1234567, ',')     // → "1,234,567"
__py.format('hi', '>10')      // → "        hi"
__py.format(5, '05d')         // → "00005"
__py.format(0.25, '.1%')      // → "25.0%"
```

Supported format spec syntax:
```
[[fill]align][sign][#][0][width][,][.precision][type]
```

Types: `d`, `f`, `e`, `%`, `x`, `b`, `o`

### `__py.bool(value)`

Python truthiness:

```javascript
__py.bool([])       // → false (Python: [] is falsy)
__py.bool({})       // → false (Python: {} is falsy)
__py.bool(0)        // → false
__py.bool("")       // → false
__py.bool([1])      // → true
__py.bool({"a": 1}) // → true
```

---

## Test Coverage

| Test File | Tests | Focus |
|-----------|-------|-------|
| `test_chained_compare.py` | 36 | Chained comparisons |
| `test_boolean_ops.py` | 44 | and/or/not semantics |
| `test_fstrings.py` | 52 | Template literals, format specs |
| `test_list_comprehensions.py` | 50 | map/filter/flatMap |
| `test_dict_comprehensions.py` | 32 | Object.fromEntries |
| `test_set_comprehensions.py` | 28 | new Set() |
| `test_generator_expressions.py` | 32 | some/every/reduce |
| `test_182_integration.py` | 25 | Combined patterns |
| **Total** | **249** | |

---

## Troubleshooting

### F-String Format Spec Not Working

**Problem**: `f"{x:.2f}"` produces wrong output

**Solution**: Check that the format spec string is correctly parsed. The parser extracts specs from `ast.FormattedValue.format_spec`.

### List Comprehension Incorrect Order

**Problem**: Filter and map in wrong order

**Solution**: Verify `.filter()` appears before `.map()` in generated code. The comprehension's `if` clauses become filters, and the element expression becomes the map.

### Boolean Operator Returns Wrong Value

**Problem**: `x or y` returns `true` instead of actual value

**Solution**: Ensure using `__py.bool(x) ? x : y` pattern, not JS native `||`.

---

## Performance Notes

- **Comprehensions**: Compile to native JS array methods (map/filter) which are well-optimized
- **F-Strings**: Compile to template literals, no runtime overhead for simple cases
- **Format Specs**: Use `__py.format()` only when needed, simple interpolations use native `${}`

---

## Future Enhancements

Phase 18.3+ will add:
- Nested comprehensions with multiple generators
- More complex format specifications
- Generator expressions that produce true iterators
