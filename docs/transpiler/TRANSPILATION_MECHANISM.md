# PyNext Transpilation Mechanism

## Overview

This document explains how PyNext transpiles Python code to optimized JavaScript, focusing on the mechanisms used for Phase 33.4 features.

## Who Should Read This

- **Contributors** extending the transpiler
- **Developers debugging** transpilation issues
- **Anyone interested** in how Python→JS transpilation works

## What Gets Transpiled

### 1. Client Testing Imports

**Python:**
```python
from pynext.testing.client import render, screen
```

**JavaScript:**
```javascript
import { render, screen } from 'pynext/testing/client.js';
```

**Mechanism:**
- `pynext/transpiler/imports.py` handles import parsing
- Maps `pynext.testing.*` to appropriate runtime paths
- Generates ES6 import statements

### 2. Type Checking Decorator

**Python:**
```python
@typed
def add(a: int, b: int) -> int:
    return a + b
```

**JavaScript (Development):**
```javascript
function add(a, b) {
    validate(a, 'int', 'a');
    validate(b, 'int', 'b');
    const result = a + b;
    validateReturn(result, 'int', 'add');
    return result;
}
```

**JavaScript (Production):**
```javascript
function add(a, b) {
    return a + b;  // Type checks stripped
}
```

**Mechanism:**
- `pynext/transpiler/functions.py` recognizes `@typed` decorator
- In dev: Wraps function with validation calls
- In prod: Strips decorator completely
- Uses `pynext/runtime/type_check.js` for validation

### 3. Stdlib Module Imports

**Python:**
```python
from pynext.client.datetime import datetime
from pynext.client.collections import Counter
```

**JavaScript:**
```javascript
import { datetime } from 'pynext/runtime/stdlib/datetime.js';
import { Counter } from 'pynext/runtime/stdlib/collections.js';
```

**Mechanism:**
- `pynext/transpiler/imports.py` maps `pynext.client.*` imports
- Maps to `pynext/runtime/stdlib/*.js` paths
- Handles named imports correctly

## How It Works (Step by Step)

### Step 1: Parsing

```python
# Python AST
ast.FunctionDef(
    name="add",
    args=[arg("a", annotation=ast.Name("int"))],
    returns=ast.Name("int"),
    decorator_list=[ast.Name("typed")]
)
```

### Step 2: IR Generation

```python
# Intermediate Representation
DecoratedFunction(
    decorators=[Decorator(name="typed")],
    function=FunctionDef(
        name="add",
        args=[...],
        returns=TypeInfo("int")
    )
)
```

### Step 3: Transformation

- Check if `@typed` decorator present
- If dev mode: Add validation calls
- If prod mode: Remove decorator
- Handle stdlib imports

### Step 4: Code Generation

```javascript
// Generated JavaScript
function add(a, b) {
    __py.type_check.validate(a, 'int', 'a');
    __py.type_check.validate(b, 'int', 'b');
    const result = a + b;
    __py.type_check.validateReturn(result, 'int', 'add');
    return result;
}
```

## Where to Find the Code

- `pynext/transpiler/imports.py` - Import handling
- `pynext/transpiler/functions.py` - Function/decorator handling
- `pynext/transpiler/emitter.py` - Code generation
- `pynext/transpiler/type_checker.py` - Type analysis
- `pynext/runtime/type_check.js` - Runtime validation

