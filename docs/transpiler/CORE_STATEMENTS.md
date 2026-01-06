# PyNext Transpiler: Core Statements Documentation

## Overview

The PyNext transpiler converts Python source code to JavaScript, enabling Python-written event handlers and reactive computations to run in the browser.

---

## Table of Contents

1. [Who Uses This](#who-uses-this)
2. [What It Does](#what-it-does)
3. [When To Use](#when-to-use)
4. [Where It Fits](#where-it-fits)
5. [Why It Exists](#why-it-exists)
6. [How It Works](#how-it-works)
7. [Core Transformations](#core-transformations)
8. [Runtime Library](#runtime-library)
9. [Examples](#examples)
10. [Testing](#testing)
11. [Extending the Transpiler](#extending-the-transpiler)

---

## Who Uses This

### Primary Users

- **PyNext Framework**: Transpiles event handlers (onclick, onsubmit) and reactive computations
- **Application Developers**: Write Python that runs in browsers
- **AI Assistants**: Generate and modify PyNext applications

### How to Access

```python
from pynext.transpiler import transpile, transpile_handler, TranspileError

# Transpile Python code to JavaScript
js = transpile("x = items[-1]")
# → "let x = __py.at(items, -1);"

# Transpile an event handler
js = transpile_handler('''
def handle_click():
    count.set(count() + 1)
''')
# → "function handle_click() { count.set(count() + 1); }"
```

---

## What It Does

The transpiler converts Python code to semantically equivalent JavaScript:

### Input (Python)

```python
def handle_add():
    if form.validate():
        items.set([*items(), form.value])
        form.reset()
        show_form.set(False)
```

### Output (JavaScript)

```javascript
function handle_add() {
    if (form.validate()) {
        items.set([...items(), form.value]);
        form.reset();
        show_form.set(false);
    }
}
```

### Key Features

1. **Full Statement Support**: if/elif/else, for, while, functions, lambdas
2. **Python Semantics**: Negative indexing, slicing, truthiness, modulo
3. **Readable Output**: Generated JS looks hand-written
4. **Error Messages**: Clear errors with line numbers and suggestions

---

## When To Use

### Use the Transpiler For

- Event handlers (onclick, onsubmit, onchange)
- Reactive computations
- Client-side validation
- State manipulation

### Do NOT Use For

- Server-side logic (use `@server_action`)
- Database operations (use PyNext DB layer)
- File I/O (not supported in browser)
- Complex class hierarchies (use server-side Python)

---

## Where It Fits

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PYNEXT APPLICATION                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐    ┌────────────────┐    ┌───────────────────┐   │
│  │  Python Source   │    │   Transpiler   │    │   JavaScript      │   │
│  │                  │ ──▶│                │ ──▶│   (Browser)       │   │
│  │  - Components    │    │  - Parser      │    │                   │   │
│  │  - Handlers      │    │  - IR Nodes    │    │  - Event handlers │   │
│  │  - Reactivity    │    │  - Emitter     │    │  - Reactive code  │   │
│  └──────────────────┘    └────────────────┘    └───────────────────┘   │
│                                  │                                       │
│                                  ▼                                       │
│                          ┌────────────────┐                             │
│                          │   Runtime      │                             │
│                          │   (core.js)    │                             │
│                          │                │                             │
│                          │  - __py.at()   │                             │
│                          │  - __py.slice()│                             │
│                          │  - __py.bool() │                             │
│                          └────────────────┘                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Why It Exists

### The Problem

Python and JavaScript have subtle but critical differences:

| Feature | Python | JavaScript |
|---------|--------|------------|
| Truthiness | `[]` is falsy | `[]` is truthy |
| Modulo | `-1 % 3 = 2` | `-1 % 3 = -1` |
| Equality | `[1,2] == [1,2]` is True | `[1,2] === [1,2]` is false |
| Indexing | `items[-1]` = last element | `items[-1]` = undefined |
| Slicing | `items[1:3]` works | No equivalent |

### The Solution

The transpiler:

1. **Parses** Python code into an Abstract Syntax Tree (AST)
2. **Converts** the AST to an Intermediate Representation (IR)
3. **Emits** JavaScript with runtime calls for Python semantics

---

## How It Works

### Architecture

```
Python Source
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  TRANSPILER PIPELINE                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PARSE                 2. IR                 3. EMIT         │
│  ┌─────────────┐         ┌─────────────┐       ┌─────────────┐ │
│  │ Python AST  │   ──▶   │  IR Nodes   │  ──▶  │ JavaScript  │ │
│  │ (ast.parse) │         │ (nodes.py)  │       │ (emitter.py)│ │
│  └─────────────┘         └─────────────┘       └─────────────┘ │
│                                                                  │
│  parser.py               Assignment, If,       emit_assignment, │
│  _parse_statement()      For, While, etc.      emit_if, etc.    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
JavaScript Output
```

### Files

| File | Purpose |
|------|---------|
| `pynext/transpiler/__init__.py` | Public API: `transpile()`, `transpile_handler()` |
| `pynext/transpiler/nodes.py` | IR node dataclasses |
| `pynext/transpiler/parser.py` | Python AST → IR |
| `pynext/transpiler/emitter.py` | IR → JavaScript |
| `pynext/transpiler/errors.py` | Error types with helpful messages |
| `pynext/transpiler/runtime/core.js` | Python semantics runtime |

---

## Core Transformations

### Statements

| Python | JavaScript |
|--------|------------|
| `x = 5` | `let x = 5;` |
| `x += 1` | `x += 1;` |
| `if x > 0:` | `if (x > 0) {` |
| `elif x < 0:` | `} else if (x < 0) {` |
| `else:` | `} else {` |
| `for x in items:` | `for (const x of items) {` |
| `for i in range(10):` | `for (let i = 0; i < 10; i++) {` |
| `while x > 0:` | `while (x > 0) {` |
| `def foo(a, b):` | `function foo(a, b) {` |
| `async def foo():` | `async function foo() {` |
| `lambda x: x * 2` | `(x) => x * 2` |
| `return x` | `return x;` |
| `pass` | `/* pass */` |
| `break` | `break;` |
| `continue` | `continue;` |

### Expressions

| Python | JavaScript |
|--------|------------|
| `a + b` | `(a + b)` |
| `a // b` | `__py.floordiv(a, b)` |
| `a % b` | `__py.mod(a, b)` |
| `a ** b` | `(a ** b)` |
| `not x` | `!__py.bool(x)` |
| `a == b` | `__py.eq(a, b)` |
| `a is None` | `(a === null)` |
| `x in items` | `__py.in(x, items)` |
| `a and b` | `(__py.bool(a) ? b : a)` |
| `a or b` | `(__py.bool(a) ? a : b)` |
| `a if cond else b` | `(cond ? a : b)` |

### Indexing and Slicing

| Python | JavaScript |
|--------|------------|
| `items[0]` | `items[0]` |
| `items[-1]` | `__py.at(items, -1)` |
| `items[i]` | `__py.at(items, i)` |
| `items[1:3]` | `__py.slice(items, 1, 3)` |
| `items[::-1]` | `__py.slice(items, null, null, -1)` |

### Builtins

| Python | JavaScript |
|--------|------------|
| `len(items)` | `items.length` |
| `str(x)` | `String(x)` |
| `int(x)` | `parseInt(x)` |
| `print(x)` | `console.log(x)` |
| `abs(x)` | `Math.abs(x)` |
| `min(a, b)` | `Math.min(a, b)` |
| `max(a, b)` | `Math.max(a, b)` |

### Methods

| Python | JavaScript |
|--------|------------|
| `s.lower()` | `s.toLowerCase()` |
| `s.upper()` | `s.toUpperCase()` |
| `s.strip()` | `s.trim()` |
| `items.append(x)` | `items.push(x)` |
| `d.keys()` | `Object.keys(d)` |
| `d.values()` | `Object.values(d)` |
| `d.items()` | `Object.entries(d)` |

---

## Runtime Library

The runtime library (`pynext/transpiler/runtime/core.js`) provides functions for Python semantics:

### Core Functions

```javascript
// Negative indexing
__py.at(arr, -1)  // Last element

// Slicing with step
__py.slice(arr, 1, 5, 2)  // [1:5:2]

// Python truthiness
__py.bool([])  // false (unlike JS)

// Python modulo
__py.mod(-1, 3)  // 2 (unlike JS -1)

// Floor division
__py.floordiv(7, 3)  // 2

// Deep equality
__py.eq([1,2], [1,2])  // true

// Membership test
__py.in(x, items)  // true if x in items
```

### Size Budget

Target: < 500 bytes gzipped

The runtime is tree-shakeable - only used functions are included in the bundle.

---

## Examples

### Example 1: Click Counter

**Python:**
```python
def handle_click():
    count.set(count() + 1)
```

**JavaScript:**
```javascript
function handle_click() {
    count.set(count() + 1);
}
```

### Example 2: Form Validation

**Python:**
```python
def handle_submit():
    if not form.validate():
        errors.set(form.errors)
        return
    
    items.set([*items(), form.values])
    form.reset()
    show_form.set(False)
```

**JavaScript:**
```javascript
function handle_submit() {
    if (!__py.bool(form.validate())) {
        errors.set(form.errors);
        return;
    }
    
    items.set([...items(), form.values]);
    form.reset();
    show_form.set(false);
}
```

### Example 3: List Processing

**Python:**
```python
def filter_items():
    query = search().lower()
    result = []
    for item in all_items():
        if query in item.name.lower():
            result.append(item)
    filtered.set(result)
```

**JavaScript:**
```javascript
function filter_items() {
    let query = search().toLowerCase();
    let result = [];
    for (const item of all_items()) {
        if (__py.in(query, item.name.toLowerCase())) {
            result.push(item);
        }
    }
    filtered.set(result);
}
```

### Example 4: Negative Indexing

**Python:**
```python
def get_last_n(items, n):
    return items[-n:]
```

**JavaScript:**
```javascript
function get_last_n(items, n) {
    return __py.slice(items, -n, null);
}
```

---

## Testing

### Running Tests

```bash
# Run all transpiler tests
pytest tests/unit/transpiler/ -v

# Run specific test file
pytest tests/unit/transpiler/test_assignment.py -v

# Run with coverage
pytest tests/unit/transpiler/ --cov=pynext/transpiler
```

### Test Structure

```
tests/unit/transpiler/
├── __init__.py
├── test_assignment.py         # 50 tests
├── test_aug_assignment.py     # 30 tests
├── test_if_statement.py       # 60 tests
├── test_for_loop.py           # 80 tests
├── test_while_loop.py         # 30 tests
├── test_function_def.py       # 60 tests
├── test_lambda.py             # 40 tests
├── test_return.py             # 30 tests
├── test_pass_break_continue.py # 20 tests
├── test_delete.py             # 30 tests
├── test_negative_indexing.py  # 40 tests
├── test_slicing.py            # 60 tests
├── test_tuple_unpacking.py    # 50 tests
├── test_expressions.py        # 50 tests
└── test_integration.py        # 30 tests

Total: 600+ tests
```

### Writing Tests

```python
from pynext.transpiler import transpile, TranspileError

def test_assign_integer():
    """x = 5 → let x = 5;"""
    assert transpile("x = 5") == "let x = 5;"

def test_negative_indexing():
    """items[-1] → __py.at(items, -1)"""
    result = transpile("x = items[-1]")
    assert "__py.at(items, -1)" in result

def test_unsupported_syntax():
    """yield raises UnsupportedSyntax."""
    with pytest.raises(TranspileError):
        transpile("def gen(): yield 1")
```

---

## Extending the Transpiler

### Adding a New Statement Type

1. **Add IR Node** (`nodes.py`):
```python
@dataclass(frozen=True)
class NewStatement(JSNode):
    """Description of new statement."""
    field1: str
    field2: JSNode
```

2. **Add Parser** (`parser.py`):
```python
def _parse_new_statement(node: ast.NewAST, source: Optional[str] = None) -> NewStatement:
    """Parse new statement type."""
    return NewStatement(
        field1=...,
        field2=_parse_expression(node.value, source),
        line=node.lineno,
        col=node.col_offset,
    )

# Add to dispatch table
parsers = {
    ast.NewAST: _parse_new_statement,
    ...
}
```

3. **Add Emitter** (`emitter.py`):
```python
def _emit_new_statement(node: NewStatement, indent: int) -> str:
    """Emit new statement as JavaScript."""
    prefix = make_indent(indent)
    return f"{prefix}// JavaScript for new statement"

# Add to dispatch table
_EMITTERS[NewStatement] = _emit_new_statement
```

4. **Add Tests** (`test_new_statement.py`):
```python
class TestNewStatement:
    def test_basic_case(self):
        result = transpile("new_statement_syntax")
        assert "expected_js" in result
```

### Adding a New Builtin

Add to `_emit_builtin_call()` in `emitter.py`:

```python
builtins = {
    "new_builtin": lambda a: f"jsEquivalent({a[0]})",
    ...
}
```

### Adding a New Method Mapping

Add to `_emit_method_call()` in `emitter.py`:

```python
string_methods = {
    "new_method": "jsMethod",
    ...
}
```

---

## Error Handling

### Error Types

- **TranspileError**: Base class for all transpiler errors
- **UnsupportedSyntax**: Python syntax that can't be transpiled
- **SemanticError**: Valid Python but can't map to JS
- **InternalError**: Bug in the transpiler

### Error Messages Include

1. **Location**: Line and column number
2. **Source Context**: The offending code
3. **Message**: Clear description of the problem
4. **Suggestion**: How to fix or work around the issue

### Example Error

```
TranspileError at line 5:

  def count_up():
      yield 1
      ^^^^^

Generator functions are not supported for client-side transpilation.

Suggestion: Use @server_action for generator functions
```

---

## Best Practices

### Do

- Keep handlers simple and focused
- Use signals for state management
- Test transpiled output matches expectations
- Use `transpile_handler()` for event handlers

### Don't

- Use generators (`yield`)
- Use context managers (`with`)
- Use pattern matching (`match/case`)
- Use `global` or `nonlocal`
- Rely on Python-specific libraries

---

## Troubleshooting

### Common Issues

**Issue: "UnsupportedSyntax: Generator functions"**
- **Cause**: Using `yield` in a function
- **Fix**: Move to `@server_action` or restructure

**Issue: "Transpilation takes too long"**
- **Cause**: Very large functions
- **Fix**: Break into smaller functions

**Issue: "Runtime error in browser"**
- **Cause**: Python/JS semantic difference not handled
- **Fix**: Report as bug, use explicit conversion

---

## Version History

### Phase 18.1 (Current)

- Core statements: if, for, while, def, lambda
- Expressions: arithmetic, comparison, boolean
- Indexing: negative indexing, slicing
- Tuple unpacking
- 600+ tests

### Future Phases

- **18.2**: Comprehensions, f-strings
- **18.3**: Classes
- **18.4**: Exception handling
- **18.5**: Advanced features
- **18.6**: PyNext integration

---

## References

- [PyNext Documentation](../README.md)
- [ROADMAP - Phase 18](../ROADMAP.md)
- [SolidJS Compilation](https://www.solidjs.com/guides/rendering)
- [Python AST Module](https://docs.python.org/3/library/ast.html)
