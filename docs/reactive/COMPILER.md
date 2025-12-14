# PyNext Compiler - Complete Guide

## Overview

The PyNext Compiler transforms Python `@island` components into optimized JavaScript that runs in the browser. This enables Python developers to write reactive client-side code without learning JavaScript.

## Why It Exists

### The Problem
React requires JavaScript. Python developers want to use Python. Simply running Python in the browser (via Pyodide/Brython) is too slow and bloated.

### The Solution
Compile Python to JavaScript at build time:
- **Zero runtime overhead** - No Python interpreter in browser
- **Smaller bundles** - ~200 bytes per component vs ~40KB for React
- **Faster updates** - Direct DOM manipulation, no Virtual DOM
- **Python debugging** - Source maps let you debug Python in browser devtools

## Architecture

```
Python Source (@island component)
         │
         ▼
┌─────────────────────┐
│  1. PARSER          │  pynext/compiler/parser.py
│  (Python AST → IR)  │  
│  - ast.parse() the component
│  - Extract signals, effects, handlers
│  - Build DOM tree structure
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. ANALYZER        │  pynext/compiler/analyzer.py
│  (Dependency Graph) │
│  - Track signal reads in handlers
│  - Track signal writes
│  - Identify compilable vs server-only
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  3. EMITTER         │  pynext/compiler/emitter.py
│  (IR → JavaScript)  │
│  - Emit createSignal() calls
│  - Emit DOM creation
│  - Emit event handlers
│  - Emit reactive effects
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  4. SOURCE MAP      │  pynext/compiler/sourcemap.py
│  (Debug Support)    │
│  - Map JS lines to Python lines
│  - Enable Python debugging in browser
└─────────────────────┘
```

## Quick Start

### Basic Usage

```python
from pynext.compiler import compile_island

result = compile_island('''
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))[count()]
''', "counter.py")

if result.success:
    print(result.js)  # JavaScript code
    print(result.map) # Source map
else:
    for error in result.errors:
        print(error)
```

### Output JavaScript

```javascript
function Counter() {
    const count = createSignal(0);

    const _el1 = document.createElement("button");
    _el1.addEventListener("click", () => count.set((count() + 1)));
    const _text2 = document.createTextNode("");
    _el1.appendChild(_text2);
    createEffect(() => { _text2.textContent = count(); });
    return _el1;
}

window.__PYNEXT_ISLANDS__ = window.__PYNEXT_ISLANDS__ || {};
window.__PYNEXT_ISLANDS__.Counter = Counter;
```

## API Reference

### `compile_island(source, filename) -> CompileResult`

Compile a single `@island` component.

**Parameters:**
- `source`: Python source code string
- `filename`: Filename for error messages and source maps

**Returns:** `CompileResult` with:
- `.js`: Generated JavaScript string
- `.map`: V3 source map (JSON string)
- `.success`: Boolean indicating success
- `.errors`: List of `CompileError` if failed
- `.warnings`: List of `CompileWarning`
- `.islands`: List of island names compiled
- `.stats`: Compilation statistics dict

### `compile_file(filepath) -> CompileResult`

Compile all `@island` components in a Python file.

## What Can Be Compiled

### ✅ Supported

| Python | JavaScript |
|--------|------------|
| `signal(0)` | `createSignal(0)` |
| `signal.set(x)` | `signal.set(x)` |
| `signal.update(fn)` | `signal.update(fn)` |
| `signal()` | `signal()` |
| `memo(lambda: ...)` | `createMemo(() => ...)` |
| `@effect def ...` | `createEffect(() => ...)` |
| `onclick=lambda: ...` | `addEventListener("click", ...)` |
| `div(class_="x")` | `createElement("div")` + `className` |
| `Show(when=...)` | Runtime Show component |
| `For(each=...)` | Runtime For component |
| `+`, `-`, `*`, `/` | `+`, `-`, `*`, `/` |
| `==`, `!=`, `<`, `>` | `===`, `!==`, `<`, `>` |
| `and`, `or`, `not` | `&&`, `||`, `!` |
| `if x else y` | `x ? y : z` |
| `data["key"]` | `data["key"]` |
| `obj.attr` | `obj.attr` |
| `[1, 2, 3]` | `[1, 2, 3]` |
| `{"a": 1}` | `{"a": 1}` |
| `f"text {x}"` | Template literals |

### ❌ Not Supported (Causes Compile Error)

| Python | Why | Solution |
|--------|-----|----------|
| `class X:` | JS classes are different | Use functions |
| `await fetch()` | Async requires runtime | Use server actions |
| `yield x` | Generators not supported | Use lists |
| `global x` | No global state in islands | Use signals |
| `import x` | No Python imports in client | Import at module level |
| Complex comprehensions | Hard to translate | Use For() |

## Integration with PyNext

### Phase 17.2 (JS Runtime)

The emitter generates code that calls these exact functions from `pynext/runtime/reactive.js`:

| Python | JS Function | Line |
|--------|-------------|------|
| `signal(x)` | `createSignal(x)` | 123 |
| `memo(fn)` | `createMemo(fn)` | 294 |
| `effect(fn)` | `createEffect(fn)` | 217 |
| `store(obj)` | `createStore(obj)` | 393 |
| `batch(fn)` | `batch(fn)` | 494 |
| `Show(...)` | `Show({...})` | 571 |
| `For(...)` | `For({...})` | 643 |

### Phase 17.3 (Python API)

The parser identifies reactive constructs by looking for:

```python
# Parser looks for these patterns:
count = signal(0)      # SignalDef
doubled = memo(...)    # MemoDef
@effect def log(): ... # EffectDef
onclick=lambda: ...    # HandlerDef
return div()[...]      # DOMNode
```

### Phase 17.5 (SSR + Hydration)

The compiler outputs hydration-ready code:

```javascript
// Islands are registered for client-side hydration
window.__PYNEXT_ISLANDS__ = window.__PYNEXT_ISLANDS__ || {};
window.__PYNEXT_ISLANDS__.Counter = Counter;
```

## Error Messages

The compiler produces helpful, AI-friendly error messages:

```
CompileError [E010]: Cannot compile class 'Helper' to JavaScript

  File "counter.py", line 15
    class Helper:
    ^^^^^

SOLUTION:
  Python classes cannot be compiled to JavaScript. Options:
  
  1. Move the class outside the @island component
  2. Convert to a plain function
  3. Use a server action for class-based logic

DOCS: https://pynext.dev/docs/compilation#classes
```

## Performance

| Metric | Target | Typical |
|--------|--------|---------|
| Compile time | < 50ms | ~1ms |
| Bundle size (simple) | < 500B | ~400B |
| Bundle size (complex) | < 2KB | ~1.5KB |

## Testing

The compiler has 298 passing tests covering:

- Parser: Island detection, signals, effects, memos, handlers, DOM tree
- Analyzer: Dependency tracking, unused signal detection
- Emitter: JavaScript generation for all constructs
- Source Map: VLQ encoding, line mapping
- Integration: Real-world component patterns

Run tests:
```bash
pytest tests/unit/compiler/ -v
```

## For AI Assistants

### Understanding the Codebase

1. **Entry point**: `pynext/compiler/__init__.py` - `compile_island()`
2. **Pipeline**: parser → analyzer → emitter → sourcemap
3. **IR**: `IslandIR` dataclass holds parsed component
4. **Output**: JavaScript string + V3 source map JSON

### Common Tasks

**Adding a new Python construct:**
1. Add extraction in `parser.py` (e.g., `_extract_new_construct()`)
2. Add to IR dataclass if needed
3. Add dependency analysis in `analyzer.py`
4. Add emission in `emitter.py` (e.g., `_emit_new_construct()`)
5. Add tests

**Adding a new error type:**
1. Create factory function in `errors.py`
2. Call it from parser/analyzer where error should occur
3. Add test in `test_errors.py`

**Debugging compilation:**
```python
from pynext.compiler.parser import parse_island
from pynext.compiler.analyzer import analyze_dependencies

# Step through pipeline
ir = parse_island(source, "debug.py")
print(ir.signals)   # See parsed signals
print(ir.handlers)  # See parsed handlers

ir = analyze_dependencies(ir)
print(ir.handlers[0].reads)   # See what signals are read
print(ir.handlers[0].writes)  # See what signals are written
```

