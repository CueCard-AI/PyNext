# PyNext Transpiler Debugging

This document describes how to debug Python-to-JavaScript transpilation in PyNext.

## Overview

PyNext provides two separate debugging systems:

1. **`pynext_debug`** - General app debugging (signals, stores, session recording)
2. **`px_transpile_debug`** - Transpiler-specific debugging (Python→JS, runtime usage)

This document covers `px_transpile_debug`, which helps you understand and troubleshoot the transpilation process.

## Browser Console API

When running with `--ai-debug`, the `px_transpile_debug` object is available in the browser console:

### List All Handlers

```javascript
px_transpile_debug.listHandlers()
// → ["handle_add_issue", "handle_toggle", "handle_delete"]
```

### View Handler Source

```javascript
px_transpile_debug.showHandler("handle_add_issue")
// Shows Python source, JavaScript output, and runtime dependencies
```

Output:
```
═══════════════════════════════════════════════════════════════
handle_add_issue
═══════════════════════════════════════════════════════════════

Python Source:
def handle_add_issue():
    title = title_input()
    if title:
        issues.set([*issues(), Issue(title)])

JavaScript Output:
function handle_add_issue() {
    let title = title_input();
    if (__py.bool(title)) {
        issues.set([...issues(), new Issue(title)]);
    }
}

Runtime Dependencies:
__py.bool, __pynext__.getSignal
═══════════════════════════════════════════════════════════════
```

### View Original Python Source

```javascript
px_transpile_debug.showSource("handle_add_issue")
// → "def handle_add_issue():\n    title = title_input()..."
```

### View Runtime Statistics

```javascript
px_transpile_debug.runtimeStats()
// → { bool: 42, at: 15, eq: 7, mod: 3 }
```

Shows how many times each `__py.*` runtime function has been called.

### Test Expression Semantics

```javascript
px_transpile_debug.testExpr("-7 % 3")
// → { expression: "-7 % 3", result: 2, expected: 2, match: true }
```

Verifies that Python semantics are correctly implemented.

## Python Debug API

### Get Transpile Debug Info

```python
from pynext.transpiler.debug import get_transpile_debug_info

info = get_transpile_debug_info('''
def handle_click():
    if items:
        count.set(count() + 1)
''')

print(info.original)      # Original Python source
print(info.javascript)    # Generated JavaScript
print(info.runtime_deps)  # ['__py.bool', '__pynext__.getSignal']
print(info.source_map)    # V3 source map for debugging
```

### Register Handler for Browser Debugging

```python
from pynext.transpiler.debug import register_handler_debug_info

register_handler_debug_info(
    name="handle_add",
    python_source="def handle_add(): ...",
    javascript="function handle_add() { ... }",
    runtime_deps=["__py.bool", "__py.eq"],
)
```

### Generate JS Registration Code

```python
from pynext.transpiler.debug import generate_handler_registry_js

js_code = generate_handler_registry_js()
# Inject this into the page to populate px_transpile_debug
```

## Source Maps

PyNext generates V3 source maps that enable debugging Python in browser DevTools.

### Generating Source Maps

```python
from pynext.transpiler.sourcemap import SourceMapBuilder

builder = SourceMapBuilder("handler.py", "handler.js")
builder.add_mapping(gen_line=1, gen_col=0, src_line=1, src_col=0)
builder.add_mapping(gen_line=2, gen_col=4, src_line=2, src_col=4)

# Get source map JSON
source_map = builder.to_json()

# Get inline data URL (for embedding)
data_url = builder.to_data_url()

# Get inline comment to append to JS
comment = builder.to_inline_comment()
# → "//# sourceMappingURL=data:application/json;base64,..."
```

### Source Map Fields

```json
{
    "version": 3,
    "file": "handler.js",
    "sources": ["handler.py"],
    "sourcesContent": ["def handle_click():\n    ..."],
    "names": ["handle_click", "items"],
    "mappings": "AAAA;AACA,IAAI;..."
}
```

## Common Debugging Scenarios

### Why is my condition always true/false?

Check if Python truthiness differs from JavaScript:

```javascript
// In browser console
px_transpile_debug.testExpr("bool([])")
// → { result: false, expected: false, match: true }

px_transpile_debug.testExpr("bool({})")
// → { result: false, expected: false, match: true }
```

Python considers empty collections falsy; JavaScript doesn't. The transpiler uses `__py.bool()` to handle this.

### Why is my modulo giving wrong results?

```javascript
px_transpile_debug.testExpr("-7 % 3")
// → { result: 2, expected: 2, match: true }

// JavaScript native would give -1, but __py.mod gives Python's 2
```

### What runtime functions is my code using?

```javascript
px_transpile_debug.runtimeStats()
// → { bool: 42, at: 15, eq: 7, slice: 3 }
```

High numbers may indicate optimization opportunities.

### How do I see what JavaScript was generated?

```javascript
px_transpile_debug.showHandler("my_handler")
```

Or in Python:

```python
from pynext.transpiler.debug import get_transpile_debug_info

info = get_transpile_debug_info("def foo(): return items[-1]")
print(info.javascript)
# → "function foo() { return __py.at(items, -1); }"
```

## Troubleshooting Guide

### Handler Not Found

```javascript
px_transpile_debug.showHandler("my_handler")
// → Handler 'my_handler' not found
```

**Causes:**
1. Handler not registered (app not started with `--ai-debug`)
2. Typo in handler name
3. Handler defined but not used on the page

**Solution:**
```javascript
px_transpile_debug.listHandlers()  // See what's available
```

### Unexpected Runtime Behavior

If transpiled code behaves differently than expected:

1. Check the generated JavaScript:
   ```javascript
   px_transpile_debug.showHandler("handler_name")
   ```

2. Verify Python semantics:
   ```javascript
   px_transpile_debug.testExpr("your expression")
   ```

3. Check runtime dependencies:
   ```javascript
   info = px_transpile_debug.getHandler("handler_name")
   console.log(info.runtimeDeps)
   ```

### Source Map Not Working

If breakpoints don't work in Python files:

1. Ensure source content is included:
   ```python
   builder = SourceMapBuilder("file.py", "file.js", source_content=python_code)
   ```

2. Check source map is appended to JS:
   ```javascript
   // JS should end with:
   //# sourceMappingURL=data:application/json;base64,...
   ```

3. Enable source maps in DevTools (Settings → Sources → Enable JavaScript source maps)

## Performance Considerations

### Minimize Runtime Calls

Each `__py.*` call has overhead. The transpiler's optimizer eliminates unnecessary calls:

```python
# Before optimization
x = len(items)  # → __py.len(items)

# After type inference (if items is known to be array)
x = len(items)  # → items.length
```

Check what's being called:

```javascript
px_transpile_debug.runtimeStats()
```

### Debug Mode Only

`px_transpile_debug` is only available in development mode. In production:

- No handler registry overhead
- No runtime tracking
- Minimal bundle size

## Integration with DevTools

### Setting Breakpoints

With source maps, you can:

1. Open DevTools → Sources
2. Navigate to your Python file
3. Click to set breakpoints
4. Debug step-by-step

### Console Workflow

```javascript
// 1. List what's available
px_transpile_debug.listHandlers()

// 2. Inspect a specific handler
px_transpile_debug.showHandler("handle_submit")

// 3. Check runtime usage
px_transpile_debug.runtimeStats()

// 4. Verify an expression
px_transpile_debug.testExpr("-7 % 3")
```

## See Also

- [CLASSES.md](CLASSES.md) - Class transpilation
- [OPTIMIZER.md](OPTIMIZER.md) - Optimization passes
- [../devtools/AI_DEBUG.md](../devtools/AI_DEBUG.md) - General app debugging with `pynext_debug`
