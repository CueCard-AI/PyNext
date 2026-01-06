# PyNext Integration (Phase 18.6)

## Table of Contents

1. [Who Uses This](#who-uses-this)
2. [What It Does](#what-it-does)
3. [When to Use](#when-to-use)
4. [Where It Lives](#where-it-lives)
5. [Why It Exists](#why-it-exists)
6. [How It Works](#how-it-works)
7. [Code Examples](#code-examples)
8. [Test Coverage](#test-coverage)
9. [Troubleshooting](#troubleshooting)

---

## Who Uses This

### Primary Users

| User | Use Case |
|------|----------|
| **PyNext Framework** | Automatically transpiles event handlers for hydration |
| **Developers** | Debug transpiled handlers with CLI tools |
| **LLMs/AI Assistants** | Understand and extend handler transpilation |

### Developer Personas

1. **Web Developers** building reactive apps with PyNext
2. **Framework Contributors** extending transpilation capabilities
3. **DevOps Engineers** debugging production issues

---

## What It Does

Phase 18.6 integrates the Python-to-JavaScript transpiler (Phase 18.1-18.5) with PyNext's reactive system. It:

### Core Capabilities

1. **Reactive Context Analysis** - Detects signals, stores, forms, and memos from handler closures
2. **IR Transformation** - Transforms IR nodes to use `__pynext__.*` runtime API
3. **Hydration Code Generation** - Generates JavaScript compatible with client-side hydration
4. **html.py Integration** - Replaces regex-based handler extraction with AST-based transpilation
5. **CLI Tools** - Provides `pynext transpile` command for debugging
6. **Dev Server Integration** - Adds `--emit-js` flag for development

### Transformation Table

| Python Pattern | JavaScript Output |
|----------------|-------------------|
| `signal()` | `__pynext__.getSignal('id').read()` |
| `signal.set(v)` | `__pynext__.getSignal('id').set(v)` |
| `signal.update(fn)` | `__pynext__.getSignal('id').update(fn)` |
| `signal.peek()` | `__pynext__.getSignal('id').peek()` |
| `store.prop` | `__pynext__.getStore('id').prop` |
| `store["key"]` | `__pynext__.getStore('id')["key"]` |
| `form.validate()` | `__pynext__.getForm('id').validate()` |
| `form.values` | `__pynext__.getForm('id').values` |
| `form.reset()` | `__pynext__.getForm('id').reset()` |
| `memo()` | `__pynext__.getMemo('id').read()` |

---

## When to Use

### Automatically Used

The transpiler is automatically used whenever you:

```python
# Define an event handler in PyNext
button(onclick=lambda: count.set(count() + 1))["Click Me"]

# Use complex handlers
def handle_add_issue():
    if issue_form.validate():
        all_issues.set([*all_issues(), issue_form.values])
        issue_form.reset()
```

### Manual Use Cases

Use the CLI for:

```bash
# Debug transpilation
pynext transpile pages/issues.py --print --annotate

# Check if handlers can be transpiled
pynext check pages/issues.py

# Show runtime dependencies
pynext deps pages/issues.py
```

---

## Where It Lives

### File Structure

```
pynext/transpiler/
├── reactive.py      # ReactiveContext analyzer
├── pynext.py        # PyNextTransformer
├── hydration.py     # Hydration code generator
├── cli.py           # CLI commands
├── __init__.py      # Public API exports

pynext/core/
├── html.py          # Modified to use AST transpiler

pynext/server/
├── dev.py           # Modified for --emit-js flag

tests/unit/transpiler/
├── test_186_signals.py    # 80 tests
├── test_186_stores.py     # 60 tests
├── test_186_forms.py      # 60 tests
├── test_186_handlers.py   # 100 tests
├── test_186_e2e.py        # 80 tests
```

### Module Dependencies

```
html.py
    │
    ▼
reactive.py ──► pynext.py ──► hydration.py
    │               │              │
    ▼               ▼              ▼
Signal/Store/   PyNextTransformer  transpile_for_hydration()
Form detection  IR transforms      Code generation
```

---

## Why It Exists

### The Problem

The old regex-based approach in `html.py` failed on complex handlers:

```python
# ❌ FAILED with regex - too complex
def handle_add_issue():
    if issue_form.validate():
        values = issue_form.values
        all_issues.set([*all_issues(), values])
        issue_form.reset()
        show_add_form.set(False)
```

Output was: `console.warn('[PyNext] Could not transpile handler')`

### The Solution

Phase 18.6 uses the full AST-based transpiler:

```python
# ✅ NOW WORKS - proper transpilation
def handle_add_issue():
    if issue_form.validate():
        values = issue_form.values
        all_issues.set([*all_issues(), values])
        issue_form.reset()
        show_add_form.set(False)
```

Output is correct JavaScript using `__pynext__.*` API.

### Benefits

1. **Correctness** - Proper AST parsing handles any Python syntax
2. **Maintainability** - No regex patterns to maintain
3. **Extensibility** - Easy to add new patterns
4. **Debuggability** - CLI tools for inspection
5. **AI-Friendly** - Clean architecture for LLM understanding

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PHASE 18.6 INTEGRATION FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Python Handler (in page.py)                                                 │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────┐                                                    │
│  │  html.py            │  → Detects onclick, onsubmit, etc.                 │
│  │  _extract_handler   │                                                    │
│  └──────────┬──────────┘                                                    │
│             │                                                                │
│             ▼                                                                │
│  ┌─────────────────────┐     ┌─────────────────────┐                       │
│  │  reactive.py        │ ──▶ │  pynext.py          │                       │
│  │  (Detect signals,   │     │  (PyNext-specific   │                       │
│  │   forms, stores)    │     │   transforms)       │                       │
│  └─────────────────────┘     └──────────┬──────────┘                       │
│                                          │                                   │
│                                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    EXISTING TRANSPILER (18.1-18.5)                    │   │
│  │  parser.py → nodes.py → emitter.py → JavaScript                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                          │                                   │
│                                          ▼                                   │
│  ┌─────────────────────┐     ┌─────────────────────┐                       │
│  │  hydration.py       │ ──▶ │  Output JavaScript  │                       │
│  │  (Resolve IDs,      │     │  with __pynext__.*  │                       │
│  │   wire to runtime)  │     │  API calls          │                       │
│  └─────────────────────┘     └─────────────────────┘                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Process

#### Step 1: Reactive Context Analysis

```python
from pynext.transpiler.reactive import analyze_handler

def handle_click():
    count.set(count() + 1)

ctx = analyze_handler(handle_click)
# ctx.signals = {"count": ReactiveObjectInfo(name="count", id="sig_1", ...)}
```

The analyzer:
1. Gets `func.__closure__` (captured variables)
2. Gets `func.__code__.co_freevars` (variable names)
3. Checks each for `__pynext_type__` attribute
4. Categorizes as signal/store/form/memo

#### Step 2: IR Transformation

```python
from pynext.transpiler.pynext import PyNextTransformer

transformer = PyNextTransformer(ctx)

# Before: Name("count")
# After: Call(__pynext__.getSignal('sig_1'))
```

The transformer:
1. Walks the IR tree
2. Identifies reactive object references
3. Replaces with `__pynext__.get*()` calls
4. Preserves all other code

#### Step 3: Code Generation

```python
from pynext.transpiler.hydration import transpile_for_hydration

js = transpile_for_hydration(handle_click, ctx)
# → "function handle_click() { __pynext__.getSignal('sig_1').set(...) }"
```

The generator:
1. Parses Python to IR
2. Transforms with PyNextTransformer
3. Emits JavaScript

---

## Code Examples

### Basic Signal Operations

```python
# Python
count = signal(0)

def increment():
    count.set(count() + 1)

def decrement():
    count.update(lambda n: n - 1)
```

```javascript
// Generated JavaScript
function increment() {
    __pynext__.getSignal('sig_1').set(
        __pynext__.getSignal('sig_1').read() + 1
    );
}

function decrement() {
    __pynext__.getSignal('sig_1').update(n => n - 1);
}
```

### Form Validation Pattern

```python
# Python
issue_form = create_form(
    title=Field(required=True),
    description=Field()
)
show_modal = signal(False)
all_issues = signal([])

def handle_add_issue():
    if issue_form.validate():
        values = issue_form.values
        all_issues.set([*all_issues(), values])
        issue_form.reset()
        show_modal.set(False)
```

```javascript
// Generated JavaScript
function handle_add_issue() {
    if (__pynext__.getForm('form_1').validate()) {
        const values = __pynext__.getForm('form_1').values;
        __pynext__.getSignal('sig_1').set([
            ...__pynext__.getSignal('sig_1').read(),
            values
        ]);
        __pynext__.getForm('form_1').reset();
        __pynext__.getSignal('sig_2').set(false);
    }
}
```

### Delete Pattern with Filter

```python
# Python
def handle_delete(issue_id):
    all_issues.set([
        issue for issue in all_issues()
        if issue["id"] != issue_id
    ])
```

```javascript
// Generated JavaScript
function handle_delete(issue_id) {
    __pynext__.getSignal('sig_1').set(
        __pynext__.getSignal('sig_1').read().filter(
            issue => issue["id"] !== issue_id
        )
    );
}
```

### Store Operations

```python
# Python
todos = store({"items": [], "filter": "all"})

def add_todo(text):
    todos.items.append({"text": text, "done": False})

def set_filter(value):
    todos.filter = value
```

```javascript
// Generated JavaScript
function add_todo(text) {
    __pynext__.getStore('store_1').items.push({
        text: text,
        done: false
    });
}

function set_filter(value) {
    __pynext__.getStore('store_1').filter = value;
}
```

---

## Test Coverage

### Summary

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_186_signals.py` | 75 | Signal read/set/update/peek, multiple signals |
| `test_186_stores.py` | 60 | Property access, subscripts, mutations |
| `test_186_forms.py` | 60 | validate(), values, reset(), field access |
| `test_186_handlers.py` | 100 | Complex patterns, async, nested |
| `test_186_e2e.py` | 79 | Linear app patterns, full integration |
| **Total** | **374** | Complete Phase 18.6 coverage |

### Key Test Categories

#### Signal Tests (80)
- Basic read: `count()` → `.read()`
- Set operations: `count.set(5)` → `.set(5)`
- Update operations: `count.update(fn)` → `.update(fn)`
- Peek: `count.peek()` → `.peek()`
- Multiple signals in expressions
- Edge cases (nested lambdas, ternaries)

#### Store Tests (60)
- Property access: `store.items` → `.items`
- Subscript access: `store["key"]` → `["key"]`
- Array mutations: `append`, `pop`, `insert`
- Nested properties
- Multiple stores

#### Form Tests (60)
- Validation: `form.validate()` → `.validate()`
- Values: `form.values` → `.values`
- Reset: `form.reset()` → `.reset()`
- Field access: `form.title`
- Errors: `form.errors.title`

#### Handler Tests (100)
- handle_add_issue pattern
- handle_delete pattern
- handle_status_change pattern
- Toggle patterns
- List manipulation
- Numeric operations
- Async patterns

#### E2E Tests (80)
- Complete Linear app flows
- CRUD operations
- View switching
- Selection handling
- Real-time updates

---

## Troubleshooting

### Handler Not Transpiling

**Symptom:**
```javascript
console.warn('[PyNext] Handler has no reactive state - use @server_action for server-side logic')
```

**Cause:** Handler doesn't capture any reactive objects in its closure.

**Solution:** Ensure reactive objects are defined in the outer scope:

```python
# ❌ Wrong - count not in closure
def page():
    count = signal(0)
    def handler():
        count.set(1)  # count is local, not captured

# ✅ Right - count is captured
count = signal(0)
def handler():
    count.set(1)  # count is in closure
```

### Transpile Error

**Symptom:**
```javascript
console.error('[PyNext] Transpile failed: ...')
```

**Cause:** Unsupported Python syntax or internal error.

**Solution:**
1. Check `PYNEXT_DEBUG=1` for detailed logs
2. Use CLI to inspect: `pynext transpile pages/file.py --print`
3. Simplify the handler and re-add complexity

### Wrong Signal ID

**Symptom:** Handler uses wrong signal ID.

**Cause:** ID changed between renders.

**Solution:** Use `_name` attribute for stable lookup:
```python
count = signal(0, name="count")  # Use name for stability
```

### Legacy Fallback Used

**Symptom:** Simple patterns work but complex ones fail.

**Cause:** AST transpiler failed, fell back to regex.

**Solution:**
1. Check `PYNEXT_DEBUG=1` for fallback messages
2. File an issue with the failing pattern

---

## CLI Reference

### transpile

```bash
pynext transpile [FILE] [OPTIONS]

Options:
  -o, --output FILE     Output file path
  --print               Print to terminal
  --annotate            Include Python source as comments
  --deps                Show runtime dependencies
  --debug               Show detailed debug output
  -h, --handler NAME    Specific handler(s) to transpile
```

### check

```bash
pynext check FILE [OPTIONS]

Options:
  -v, --verbose         Show detailed output
```

### deps

```bash
pynext deps FILE

Shows:
  - __pynext__.getSignal, getStore, getForm, getMemo
  - __py.* runtime helpers used
```

---

## API Reference

### ReactiveContext

```python
from pynext.transpiler.reactive import ReactiveContext, create_context

ctx = create_context(
    signals={"count": "sig_1"},
    stores={"todos": "store_1"},
    forms={"form": "form_1"},
    memos={"total": "memo_1"}
)
```

### analyze_handler

```python
from pynext.transpiler.reactive import analyze_handler

def handler():
    count.set(1)

ctx = analyze_handler(handler)
# ctx.signals["count"] → ReactiveObjectInfo
```

### PyNextTransformer

```python
from pynext.transpiler.pynext import PyNextTransformer

transformer = PyNextTransformer(ctx)
transformed_ir = transformer.transform(ir_node)
```

### transpile_for_hydration

```python
from pynext.transpiler.hydration import transpile_for_hydration, HydrationOptions

options = HydrationOptions(
    wrap_in_function=True,
    include_comments=True
)
js = transpile_for_hydration(handler, ctx, options)
```

---

## Critical Fixes (Phase 18.6.1)

The following critical fixes were implemented to address edge cases:

### 1. Signal Reads Inside Comprehensions ✅

**Problem**: Signals inside dict/set comprehensions were not transformed because `_transform_dictcomp` and `_transform_setcomp` were missing.

**Solution**: Added transforms for `DictComp` and `SetComp` nodes.

```python
# Before (broken): count() not transformed
{x: count() for x in items}
# → Object.fromEntries([...].map(x => [x, count()]))  # BROKEN!

# After (fixed): count() properly transformed
{x: count() for x in items}
# → Object.fromEntries([...].map(x => [x, __pynext__.getSignal('id').read()]))
```

### 2. Nested Function Handlers ✅

**Problem**: Closures only looked at immediate `__closure__`, missing signals in outer scopes.

**Solution**: Added `_extract_nested_closure_vars()` that traverses closure chains.

```python
def outer():
    count = signal(0)
    def inner():  # count is NOW detected
        count.set(1)
```

### 3. Form Field Signals ✅

**Problem**: Form fields (`form.email`, `form.password`) are signals but weren't detected.

**Solution**: Added `_extract_form_field_signals()` to extract field signals from forms.

```python
form = create_form(email=Field(), password=Field())
# form.email() is now recognized as a signal read
```

### 4. Try/Except Support ✅

**Problem**: `try/except` blocks were stubbed out as `/* pass */`.

**Solution**: Added proper `Try` and `ExceptHandler` IR nodes with full transpilation.

```python
try:
    count.set(risky())
except ValueError as e:
    error.set(str(e))
finally:
    loading.set(False)
```

Transpiles to:

```javascript
try {
    __pynext__.getSignal('sig_1').set(risky());
} catch (_e) {
    if (_e instanceof Error && _e.name === 'ValueError') {
        let e = _e;
        __pynext__.getSignal('sig_2').set(String(e));
    }
} finally {
    __pynext__.getSignal('sig_3').set(false);
}
```

### 5. Lambda Source Extraction ✅

**Problem**: `inspect.getsource()` fails for inline lambdas.

**Solution**: Added fallback bytecode analysis for common lambda patterns.

### 6. Async Handler Improvements ✅

**Problem**: Signals inside await expressions weren't transformed.

**Solution**: Added `_transform_await()` to handle signals in async contexts.

```python
async def handler():
    result = await api.fetch(count())  # count() now transformed
```

---

## Test Summary

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_186_signals.py` | 75 | ✅ Pass |
| `test_186_stores.py` | 60 | ✅ Pass |
| `test_186_forms.py` | 60 | ✅ Pass |
| `test_186_handlers.py` | 100 | ✅ Pass |
| `test_186_e2e.py` | 79 | ✅ Pass |
| `test_186_critical_fixes.py` | 68 | ✅ Pass |
| **Total** | **442** | ✅ Pass |

---

## Future Enhancements

1. **Source Maps** - Map JavaScript back to Python lines
2. **Memo Transforms** - Full memo support with dependencies
3. **Effect Transforms** - Effect function transpilation
4. **Watch Mode** - Live transpilation feedback
5. **Type Hints** - TypeScript output with types
