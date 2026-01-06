# Phase 33.1: Integration Tests

Comprehensive integration tests for Python-to-JavaScript transpilation.

## Test Files

### `test_python_js_equivalence.py`
**Purpose**: Verify that transpiled JavaScript produces the same results as Python code.

**Features**:
- Executes Python code
- Transpiles to JavaScript
- Executes JavaScript with Node.js
- Compares outputs line-by-line
- Normalizes whitespace differences

**Test Coverage**:
- Functions (basic, args, defaults, lambda, nested)
- Classes (basic, inheritance, properties)
- Control flow (if/else, for/while, try/except)
- Comprehensions (list, dict, set)

### `test_edge_cases.py`
**Purpose**: Test edge cases and corner cases.

**Coverage**:
- Empty comprehensions
- Nested comprehensions
- Lambda in comprehensions
- Closure variable capture
- Default argument mutation
- for...else and while...else
- Multiple inheritance
- Property getters/setters

### `test_mini_applications.py`
**Purpose**: Test harness for realistic mini applications.

**Applications**:
- Calculator (classes, methods, history)
- Todo list (classes, state management)
- Data processor (comprehensions, functions)
- Game app (classes, control flow, game loop)
- Math library (static methods, recursion)
- Event system (callbacks, closures)

### `test_more_mini_apps.py`
**Purpose**: Additional mini applications.

**Applications**:
- Shopping cart (items, quantities, totals)
- Bank account (deposits, withdrawals, balance)
- Library system (books, borrowing)
- Sorting algorithms (bubble sort, quick sort)
- Cache system (LRU cache)

### `test_performance.py`
**Purpose**: Performance benchmarks comparing Python vs JavaScript.

**Benchmarks**:
- List comprehension performance
- Function call performance
- Class instantiation performance
- Nested loops performance

## Running Tests

```bash
# Run all integration tests
pytest tests/integration/transpiler/

# Run specific test file
pytest tests/integration/transpiler/test_python_js_equivalence.py

# Run with verbose output
pytest tests/integration/transpiler/ -v

# Run performance tests
pytest tests/integration/transpiler/test_performance.py -v -s
```

## Requirements

- Python 3.10+
- Node.js (for JavaScript execution)
- pytest

## How It Works

1. **Python Execution**: Code is written to a temporary file and executed with `python3`
2. **Transpilation**: Python code is transpiled to JavaScript using `pynext.transpiler.transpile()`
3. **JavaScript Execution**: Transpiled code is wrapped with runtime helpers and executed with `node`
4. **Comparison**: Outputs are normalized (whitespace, formatting) and compared

## Known Issues

- Class instantiation requires `new` keyword fix (handled in test wrapper)
- Template literal escaping for f-strings (handled in test wrapper)
- Output formatting differences (normalized in comparison)

## Future Improvements

- Add more edge cases
- Expand mini applications
- Add more performance benchmarks
- Test async/await patterns
- Test decorators more thoroughly

