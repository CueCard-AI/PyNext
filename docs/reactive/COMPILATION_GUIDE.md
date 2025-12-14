# PyNext Compilation Guide

> **Version:** 1.0.0  
> **Status:** Draft  
> **Last Updated:** December 2024

---

## Table of Contents

1. [Overview](#1-overview)
2. [Compilable Constructs](#2-compilable-constructs)
3. [Non-Compilable Constructs](#3-non-compilable-constructs)
4. [Compilation Markers](#4-compilation-markers)
5. [Compiler Architecture](#5-compiler-architecture)
6. [Source Maps](#6-source-maps)
7. [Optimization](#7-optimization)
8. [Error Messages](#8-error-messages)

---

## 1. Overview

### 1.1 What is Compilation?

PyNext compiles Python code to JavaScript at **build time**. This enables:

- **Python-first development** - Write Python, run in browser
- **Optimal performance** - No runtime interpretation
- **Small bundles** - Only compiled code, no Python runtime
- **Type safety** - Compile-time checks catch errors early

### 1.2 Compilation Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        COMPILATION PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Python Source          AST              IR            JavaScript       │
│   ─────────────         ─────            ────          ──────────       │
│                                                                          │
│   @island               Python           PyNext         Optimized       │
│   def Counter():   ───▶ AST         ───▶ IR        ───▶ JS              │
│     count = signal(0)   (parse)         (analyze)       (emit)          │
│     ...                                                                  │
│                                                                          │
│                              ┌────────────────────┐                      │
│                              │  Source Map (.map) │                      │
│                              │  Python ↔ JS lines │                      │
│                              └────────────────────┘                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Why Build-Time Only?

| Approach | Pros | Cons |
|----------|------|------|
| **Build-time** (PyNext) | Smallest bundle, fastest execution | Requires build step |
| Runtime interpretation | No build step | Large runtime (~100KB+), slow |
| Hybrid | Flexible | Complex, larger bundles |

PyNext uses **build-time only** for maximum performance.

---

## 2. Compilable Constructs

### 2.1 Signal Operations

All signal operations compile to JavaScript:

```python
# Python                          # JavaScript
count = signal(0)                 # const count = createSignal(0)
value = count()                   # const value = count()
count.set(5)                      # count.set(5)
count.update(lambda x: x + 1)    # count.update(x => x + 1)
count.peek()                      # count.peek()
```

### 2.2 Arithmetic and Comparison

```python
# Python                          # JavaScript
a + b                             # a + b
a - b                             # a - b
a * b                             # a * b
a / b                             # a / b
a // b                            # Math.floor(a / b)
a % b                             # a % b
a ** b                            # a ** b

a == b                            # a === b
a != b                            # a !== b
a < b                             # a < b
a <= b                            # a <= b
a > b                             # a > b
a >= b                            # a >= b

a and b                           # a && b
a or b                            # a || b
not a                             # !a
```

### 2.3 String Operations

```python
# Python                          # JavaScript
f"Count: {count()}"               # `Count: ${count()}`
"hello" + "world"                 # "hello" + "world"
s.upper()                         # s.toUpperCase()
s.lower()                         # s.toLowerCase()
s.strip()                         # s.trim()
s.split(",")                      # s.split(",")
s.replace("a", "b")               # s.replace("a", "b")
len(s)                            # s.length
s[0]                              # s[0]
s[1:3]                            # s.slice(1, 3)
"x" in s                          # s.includes("x")
```

### 2.4 List/Array Operations

```python
# Python                          # JavaScript
items = [1, 2, 3]                 # const items = [1, 2, 3]
items[0]                          # items[0]
items[-1]                         # items[items.length - 1]
items[1:3]                        # items.slice(1, 3)
items.append(4)                   # items.push(4)
items.pop()                       # items.pop()
items.insert(0, x)                # items.unshift(x)
len(items)                        # items.length
x in items                        # items.includes(x)

# Comprehensions
[x * 2 for x in items]            # items.map(x => x * 2)
[x for x in items if x > 0]       # items.filter(x => x > 0)
```

### 2.5 Dictionary/Object Operations

```python
# Python                          # JavaScript
obj = {"a": 1, "b": 2}            # const obj = {a: 1, b: 2}
obj["a"]                          # obj["a"]
obj.get("a", 0)                   # obj.a ?? 0
obj.keys()                        # Object.keys(obj)
obj.values()                      # Object.values(obj)
obj.items()                       # Object.entries(obj)
"a" in obj                        # "a" in obj
```

### 2.6 Control Structures

```python
# Python                          # JavaScript
if x > 0:                         # if (x > 0) {
    y = 1                         #     y = 1
elif x < 0:                       # } else if (x < 0) {
    y = -1                        #     y = -1
else:                             # } else {
    y = 0                         #     y = 0
                                  # }

for item in items:                # for (const item of items) {
    print(item)                   #     console.log(item)
                                  # }

for i, item in enumerate(items):  # items.forEach((item, i) => {
    print(i, item)                #     console.log(i, item)
                                  # })

while x > 0:                      # while (x > 0) {
    x -= 1                        #     x -= 1
                                  # }
```

### 2.7 Functions

```python
# Lambda functions
lambda: count.set(0)              # () => count.set(0)
lambda x: x * 2                   # x => x * 2
lambda x, y: x + y                # (x, y) => x + y

# Function definitions (in @island scope)
def add(a, b):                    # function add(a, b) {
    return a + b                  #     return a + b
                                  # }

# Default arguments
def greet(name="World"):          # function greet(name = "World") {
    return f"Hello, {name}!"      #     return `Hello, ${name}!`
                                  # }
```

### 2.8 Event Handlers

```python
# Python                          # JavaScript
onclick=lambda: count.set(0)      # onclick: () => count.set(0)

oninput=lambda e: (               # oninput: (e) => 
    text.set(e.target.value)      #     text.set(e.target.value)
)

onsubmit=lambda e: (              # onsubmit: (e) => {
    e.preventDefault(),           #     e.preventDefault()
    save()                        #     save()
)                                 # }
```

### 2.9 Store Operations

```python
# Python                          # JavaScript
todos = store({"items": []})      # const todos = createStore({items: []})
todos.items                       # todos.items
todos.items[0]                    # todos.items[0]
todos.items.append(x)             # todos.items.push(x)
todos.filter = "active"           # todos.filter = "active"
```

---

## 3. Non-Compilable Constructs

### 3.1 Server-Only Operations

These operations require server access and cannot run in the browser:

```python
# DATABASE QUERIES - Server only
users = db.query(User).all()
user = await db.get(User, id=1)
await db.insert(User, name="Alice")

# FILE I/O - Server only
with open("data.txt") as f:
    content = f.read()

# NETWORK REQUESTS (from server) - Server only
response = requests.get("https://api.example.com")
```

### 3.2 Disallowed Imports

```python
# These imports are NOT allowed in @island code:
import os              # System access
import sys             # System access
import subprocess      # Process spawning
import socket          # Low-level networking
import asyncio         # Server-side async
import pathlib         # Filesystem access
import pickle          # Binary serialization
import ctypes          # Native code
```

### 3.3 Disallowed Constructs

```python
# Classes - Use functions and stores instead
class Counter:  # NOT ALLOWED in @island
    def __init__(self):
        self.count = 0

# Generators - Use list comprehensions instead
def generate():  # NOT ALLOWED in @island
    for i in range(10):
        yield i

# Decorators (except @island) - NOT ALLOWED
@custom_decorator  # NOT ALLOWED in @island
def my_func():
    pass

# Global mutable state - Use signals instead
counter = 0  # NOT ALLOWED - use signal(0)

# Try/except (limited support)
try:  # Some patterns NOT ALLOWED
    complex_operation()
except SomeException as e:
    handle(e)

# With statements - NOT ALLOWED
with resource:  # NOT ALLOWED in @island
    use(resource)
```

### 3.4 Why These Restrictions?

| Construct | Why Not Compilable |
|-----------|-------------------|
| Classes | No clear JS mapping, use stores |
| Generators | Lazy evaluation, complex state |
| File I/O | No filesystem in browser |
| Database | Requires server connection |
| Imports | Most Python modules have no JS equivalent |
| Global mutation | Breaks reactivity model |

---

## 4. Compilation Markers

### 4.1 @island - Client-Side Component

```python
from pynext.reactive import island, signal

@island
def Counter():
    """
    This entire function compiles to JavaScript.
    It runs in the browser, not on the server.
    """
    count = signal(0)
    
    return div()[
        button(onclick=lambda: count.set(count() - 1))["-"],
        span()[count()],
        button(onclick=lambda: count.set(count() + 1))["+"],
    ]
```

### 4.2 @server - Server-Only Code

```python
from pynext.reactive import server

@server
def get_user(user_id: int):
    """
    This function runs ONLY on the server.
    It can access the database, filesystem, etc.
    """
    return db.query(User).get(user_id)

@server
async def save_todo(todo: dict):
    """Async server function."""
    await db.insert(Todo, **todo)
    return {"success": True}
```

### 4.3 Automatic Detection

When neither `@island` nor `@server` is specified, PyNext auto-detects:

```python
def render_header():
    """
    AUTO-DETECTED AS SERVER:
    - No signals/effects used
    - Just returns HTML
    - Safe to pre-render
    """
    return header()[nav()["Home | About"]]

def Counter():
    """
    AUTO-DETECTED AS ISLAND:
    - Uses signal()
    - Has reactive behavior
    - Needs client-side JS
    """
    count = signal(0)
    return button()[count()]
```

### 4.4 Island Options

```python
@island(
    hydrate="visible",  # When to hydrate: "immediate" | "visible" | "idle" | "interaction"
    prerender=True,     # Server-render initial HTML (default: True)
    ssr=True,           # Enable SSR for this island (default: True)
)
def LazyCounter():
    count = signal(0)
    return button()[count()]
```

---

## 5. Compiler Architecture

### 5.1 Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      COMPILER PIPELINE STAGES                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Stage 1: PARSE                                                         │
│   ─────────────────                                                      │
│   Python source → Python AST (using ast module)                          │
│   - Validates syntax                                                     │
│   - Extracts @island marked functions                                    │
│                                                                          │
│   Stage 2: ANALYZE                                                       │
│   ─────────────────                                                      │
│   Python AST → PyNext IR (Intermediate Representation)                   │
│   - Identifies signals, effects, memos                                   │
│   - Builds dependency graph                                              │
│   - Checks for non-compilable constructs                                 │
│   - Reports errors with Python line numbers                              │
│                                                                          │
│   Stage 3: OPTIMIZE                                                      │
│   ─────────────────                                                      │
│   PyNext IR → Optimized IR                                               │
│   - Dead code elimination                                                │
│   - Constant folding                                                     │
│   - Signal access optimization                                           │
│                                                                          │
│   Stage 4: EMIT                                                          │
│   ─────────────────                                                      │
│   Optimized IR → JavaScript                                              │
│   - Generates JS code                                                    │
│   - Creates source maps                                                  │
│   - Bundles with runtime                                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Intermediate Representation (IR)

```python
# Example IR node types
@dataclass
class IRSignal:
    name: str
    initial_value: IRExpr
    
@dataclass
class IREffect:
    body: list[IRStatement]
    dependencies: set[str]  # Signal names
    
@dataclass  
class IRMemo:
    name: str
    computation: IRExpr
    dependencies: set[str]

@dataclass
class IREventHandler:
    event_type: str  # "click", "input", etc.
    body: list[IRStatement]
    signals_written: set[str]
    
@dataclass
class IRComponent:
    name: str
    signals: list[IRSignal]
    effects: list[IREffect]
    memos: list[IRMemo]
    handlers: list[IREventHandler]
    template: IRElement
```

### 5.3 Dependency Analysis

```python
def analyze_dependencies(node: ast.AST) -> set[str]:
    """
    Find all signals read within an expression.
    
    Example:
        count() + doubled()
        → {"count", "doubled"}
    """
    deps = set()
    
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                # signal() call - reading a signal
                deps.add(child.func.id)
    
    return deps
```

---

## 6. Source Maps

### 6.1 What Are Source Maps?

Source maps connect JavaScript line numbers back to Python source, enabling:

- **Debugging** - Set breakpoints in Python code
- **Error messages** - See Python line numbers in stack traces
- **DevTools** - Step through Python code in browser

### 6.2 Source Map Format

```json
{
    "version": 3,
    "file": "Counter.js",
    "sources": ["Counter.py"],
    "sourcesContent": ["@island\ndef Counter():\n    count = signal(0)\n    ..."],
    "names": ["count", "signal", "set"],
    "mappings": "AAAA,SAAS,QAAQ,GAAG;AACpB,MAAM,KAAK,GAAG,MAAM,CAAC,CAAC,CAAC,CAAC"
}
```

### 6.3 Line Mapping Example

```python
# Counter.py (Python source)
1:  @island
2:  def Counter():
3:      count = signal(0)
4:      return button(onclick=lambda: count.set(count() + 1))[
5:          count()
6:      ]
```

```javascript
// Counter.js (Compiled output)
1:  // @island
2:  function Counter() {
3:      const count = createSignal(0);
4:      return h("button", {onclick: () => count.set(count() + 1)},
5:          count()
6:      );
7:  }
```

```
Mapping:
Python L3 → JS L3 (signal creation)
Python L4 → JS L4 (onclick handler)
Python L5 → JS L5 (count display)
```

---

## 7. Optimization

### 7.1 Dead Code Elimination

```python
# Before optimization
@island
def Example():
    count = signal(0)
    unused = signal(10)  # Never read
    return div()[count()]
```

```javascript
// After optimization - unused signal removed
function Example() {
    const count = createSignal(0);
    // unused signal eliminated
    return h("div", null, count());
}
```

### 7.2 Constant Folding

```python
# Before optimization
width = signal(100)
doubled = 100 * 2  # Constant expression
```

```javascript
// After optimization - computed at build time
const width = createSignal(100);
const doubled = 200;  // Folded
```

### 7.3 Signal Access Optimization

```python
# Before optimization
def render():
    a = count()
    b = count()  # Redundant read
    return a + b
```

```javascript
// After optimization - single read
function render() {
    const _count = count();
    return _count + _count;
}
```

### 7.4 Event Handler Inlining

```python
# Before optimization
def increment():
    count.set(count() + 1)

button(onclick=increment)
```

```javascript
// After optimization - inlined
h("button", {onclick: () => count.set(count() + 1)})
```

### 7.5 Bundle Size Targets

| Component | Size (gzipped) | Contents |
|-----------|---------------|----------|
| Runtime core | ~1.5KB | createSignal, createEffect, createMemo |
| Control flow | ~0.8KB | Show, For, Switch |
| Hydration | ~0.7KB | hydrate, bind |
| **Total** | **< 3KB** | Core reactive system |

---

## 8. Error Messages

### 8.1 Compile-Time Errors

All errors show Python file and line numbers:

```
CompilationError: Cannot use 'import os' in @island component

  File "components/counter.py", line 5
    import os
    ^^^^^^^^^

  Reason: The 'os' module requires system access not available in browsers.
  
  Suggestion: Move this code to a @server function.
```

### 8.2 Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot import X` | Importing non-JS module | Use `@server` for server code |
| `Cannot define class` | Class definition in island | Use functions and stores |
| `Cannot use generator` | Generator function | Use list comprehension |
| `Unknown signal X` | Typo in signal name | Check signal definition |
| `Circular dependency` | A depends on B depends on A | Restructure computation |

### 8.3 Runtime Errors

Even compiled code can have runtime errors:

```javascript
// Runtime error with source map
Uncaught TypeError: Cannot read property 'items' of undefined
    at Counter.py:15:8  // Maps back to Python
    at todos.items.map(...)
```

### 8.4 Development Mode Checks

```python
# In development, additional checks are enabled:

@island
def Counter():
    count = signal(0)
    
    # DEV CHECK: Warns about reading signal outside reactive context
    print(count())  # ⚠️ Warning: Reading signal outside effect/memo
    
    # DEV CHECK: Warns about mutation in render
    if True:
        count.set(1)  # ⚠️ Warning: Signal mutation during render
```

---

## Appendix: Complete Compilation Example

### Input (Python)

```python
# components/todo.py
from pynext.reactive import island, signal, store, memo, Show, For
from pynext.core.html import div, input_, button, ul, li, span

@island
def TodoApp():
    todos = store({"items": []})
    new_text = signal("")
    filter_type = signal("all")
    
    def add_todo():
        if new_text():
            todos.items.append({
                "id": len(todos.items) + 1,
                "text": new_text(),
                "done": False
            })
            new_text.set("")
    
    def toggle_todo(id: int):
        for item in todos.items:
            if item["id"] == id:
                item["done"] = not item["done"]
    
    filtered = memo(lambda: [
        t for t in todos.items
        if filter_type() == "all" or
           (filter_type() == "active" and not t["done"]) or
           (filter_type() == "done" and t["done"])
    ])
    
    remaining = memo(lambda: sum(1 for t in todos.items if not t["done"]))
    
    return div(class_="todo-app")[
        div(class_="input-row")[
            input_(
                type="text",
                value=new_text(),
                oninput=lambda e: new_text.set(e.target.value),
                onkeypress=lambda e: add_todo() if e.key == "Enter" else None,
                placeholder="What needs to be done?"
            ),
            button(onclick=add_todo)["Add"],
        ],
        
        Show(when=lambda: len(todos.items) > 0)[
            ul(class_="todo-list")[
                For(each=filtered, key=lambda t: t["id"])[
                    lambda todo: li(
                        class_="done" if todo["done"] else "",
                        onclick=lambda: toggle_todo(todo["id"])
                    )[
                        span()[todo["text"]]
                    ]
                ]
            ],
            div(class_="footer")[
                span()[f"{remaining()} items left"],
                div(class_="filters")[
                    button(
                        class_="active" if filter_type() == "all" else "",
                        onclick=lambda: filter_type.set("all")
                    )["All"],
                    button(
                        class_="active" if filter_type() == "active" else "",
                        onclick=lambda: filter_type.set("active")
                    )["Active"],
                    button(
                        class_="active" if filter_type() == "done" else "",
                        onclick=lambda: filter_type.set("done")
                    )["Done"],
                ],
            ],
        ],
    ]
```

### Output (JavaScript)

```javascript
// _pynext/islands/TodoApp.js
import { createSignal, createStore, createMemo, createEffect, h, Show, For } from '/_pynext/reactive.js';

export function TodoApp() {
    const todos = createStore({ items: [] });
    const new_text = createSignal("");
    const filter_type = createSignal("all");
    
    function add_todo() {
        if (new_text()) {
            todos.items.push({
                id: todos.items.length + 1,
                text: new_text(),
                done: false
            });
            new_text.set("");
        }
    }
    
    function toggle_todo(id) {
        for (const item of todos.items) {
            if (item.id === id) {
                item.done = !item.done;
            }
        }
    }
    
    const filtered = createMemo(() => 
        todos.items.filter(t =>
            filter_type() === "all" ||
            (filter_type() === "active" && !t.done) ||
            (filter_type() === "done" && t.done)
        )
    );
    
    const remaining = createMemo(() => 
        todos.items.filter(t => !t.done).length
    );
    
    return h("div", { class: "todo-app" },
        h("div", { class: "input-row" },
            h("input", {
                type: "text",
                value: new_text(),
                oninput: (e) => new_text.set(e.target.value),
                onkeypress: (e) => e.key === "Enter" ? add_todo() : null,
                placeholder: "What needs to be done?"
            }),
            h("button", { onclick: add_todo }, "Add")
        ),
        
        Show({ when: () => todos.items.length > 0 },
            h("ul", { class: "todo-list" },
                For({ each: filtered, key: t => t.id },
                    (todo) => h("li", {
                        class: todo.done ? "done" : "",
                        onclick: () => toggle_todo(todo.id)
                    },
                        h("span", null, todo.text)
                    )
                )
            ),
            h("div", { class: "footer" },
                h("span", null, `${remaining()} items left`),
                h("div", { class: "filters" },
                    h("button", {
                        class: filter_type() === "all" ? "active" : "",
                        onclick: () => filter_type.set("all")
                    }, "All"),
                    h("button", {
                        class: filter_type() === "active" ? "active" : "",
                        onclick: () => filter_type.set("active")
                    }, "Active"),
                    h("button", {
                        class: filter_type() === "done" ? "active" : "",
                        onclick: () => filter_type.set("done")
                    }, "Done")
                )
            )
        )
    );
}

//# sourceMappingURL=TodoApp.js.map
```

---

*End of Compilation Guide*

