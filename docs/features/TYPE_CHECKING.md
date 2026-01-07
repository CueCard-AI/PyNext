# PyNext Type Checking Guide

## Overview

PyNext provides both runtime and compile-time type checking for client-side code, giving you the safety of TypeScript with the simplicity of Python.

## Who Should Use This

- **Developers wanting type safety** without TypeScript
- **Teams using type hints** who want validation
- **Anyone building large applications** needing type checking

## What It Provides

### 1. Runtime Type Checking (@typed decorator)

Validate types at runtime during development:

```python
from pynext.client import typed

@typed
@client
def calculate_total(items: list[dict], tax_rate: float = 0.1) -> float:
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    return subtotal * (1 + tax_rate)

# In dev mode: Validates types
calculate_total([{"price": 10, "quantity": 2}], 0.15)  # OK
calculate_total([{"price": 10}], "0.15")  # TypeError: tax_rate must be float
```

### 2. Compile-Time Type Checking

Catch type errors before runtime:

```python
def add(a: int, b: int) -> int:
    return a + b

add("1", "2")  # Type error detected at transpile time
```

### 3. Type Checking Configuration

Enable/disable type checking globally:

```python
from pynext.client import enable_type_checking

enable_type_checking(True)   # Enable
enable_type_checking(False)  # Disable (for production)
```

## When to Use

- **Development**: Enable runtime checking to catch bugs early
- **Production**: Disable for performance (decorator is stripped)
- **Large codebases**: Use compile-time checking for better IDE support

## How It Works

### Runtime Type Checking

1. `@typed` decorator wraps function
2. Validates arguments against type hints
3. Validates return value
4. Raises `TypeError` on mismatch

### Compile-Time Checking

1. Transpiler analyzes type annotations
2. Checks argument types at call sites
3. Warns/errors on mismatches
4. Enables type-based optimizations

## Where to Find More

- `pynext/client/typed.py` - @typed decorator
- `pynext/runtime/type_check.js` - Runtime validation
- `pynext/transpiler/type_checker.py` - Compile-time checking
- `tests/unit/client/test_typed.py` - Tests

