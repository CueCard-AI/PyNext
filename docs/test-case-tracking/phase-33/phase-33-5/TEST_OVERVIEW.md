# Phase 33.5: Core Transpilation Completion - Test Overview

**Status**: ✅ Complete  
**Tests**: 59 (all passing)  
**Last Updated**: 2026-01-06

## Summary

Phase 33.5 completes the remaining ~2% of Phase 33 features:

1. **`contextlib.contextmanager`** - Decorator transpilation for generator-based context managers
2. **`asyncio.sleep`** - setTimeout wrapper for async timing
3. **Proxy-based Attribute Access** - `__getattr__`, `__setattr__`, `__delattr__` via JavaScript Proxy

## Test Files

### 1. `tests/unit/transpiler/test_335_contextmanager.py` (20 tests)

Tests the transpilation of `@contextmanager` decorated functions to JavaScript context manager objects.

| Test Class | Tests | Description |
|------------|-------|-------------|
| `TestContextmanagerDecorator` | 10 | Core decorator detection and transpilation |
| `TestContextmanagerEmittedCode` | 5 | Emitted code structure verification |
| `TestContextmanagerEdgeCases` | 5 | Edge cases and complex scenarios |

**Key Tests:**
- `test_basic_contextmanager` - Basic @contextmanager transpilation
- `test_contextmanager_with_try_finally` - try/finally cleanup handling
- `test_emitted_has_gen_field` - Verifies generator field in output
- `test_emitted_exit_handles_exceptions` - Exception handling in __exit__

### 2. `tests/unit/transpiler/test_335_asyncio_sleep.py` (17 tests)

Tests the transpilation of `asyncio.sleep()` to `__py.sleep()`.

| Test Class | Tests | Description |
|------------|-------|-------------|
| `TestAsyncioSleepBasic` | 5 | Basic sleep transpilation |
| `TestAsyncioSleepImportPatterns` | 3 | Different import patterns |
| `TestAsyncioSleepInContext` | 4 | Sleep in various code contexts |
| `TestAsyncioSleepWithGather` | 2 | Combined with asyncio.gather |
| `TestAsyncioSleepEdgeCases` | 3 | Edge cases |

**Key Tests:**
- `test_asyncio_sleep_basic` - Basic `asyncio.sleep(1)` transpilation
- `test_asyncio_sleep_with_float` - Fractional seconds support
- `test_from_asyncio_import_sleep` - `from asyncio import sleep` pattern
- `test_asyncio_sleep_with_gather` - Combined with Promise.all

### 3. `tests/unit/transpiler/test_335_attribute_proxy.py` (22 tests)

Tests Proxy-based attribute access for classes with `__getattr__`, `__setattr__`, `__delattr__`.

| Test Class | Tests | Description |
|------------|-------|-------------|
| `TestGetattr` | 5 | `__getattr__` transpilation |
| `TestSetattr` | 3 | `__setattr__` transpilation |
| `TestDelattr` | 2 | `__delattr__` transpilation |
| `TestCombinedDunders` | 2 | Multiple attribute dunders |
| `TestProxyFactory` | 3 | Factory function emission |
| `TestNoProxyNeeded` | 3 | Classes without proxy requirements |
| `TestEdgeCases` | 4 | Edge cases |

**Key Tests:**
- `test_basic_getattr` - Basic `__getattr__` class transpilation
- `test_factory_function_emitted` - Verifies `__py_create_*` factory
- `test_instantiation_uses_factory` - Factory usage in instantiation
- `test_class_without_dunders` - No factory for regular classes

## Implementation Files

### Modified Files

| File | Changes |
|------|---------|
| `pynext/transpiler/functions.py` | Added @contextmanager detection and emission |
| `pynext/transpiler/emitter.py` | Added asyncio.sleep → __py.sleep and Proxy factory usage |
| `pynext/transpiler/classes.py` | Added attribute proxy detection and factory emission |
| `pynext/transpiler/parser.py` | Added `has_attribute_proxy` detection |
| `pynext/transpiler/nodes.py` | Added `has_attribute_proxy` field to ClassDef |
| `pynext/transpiler/_internal/scope.py` | Added asyncio import and attribute proxy tracking |
| `pynext/transpiler/imports.py` | Added asyncio import tracking |
| `pynext/transpiler/runtime/core.js` | Added sleep, contextmanager, proxy exports |

### New Files

| File | Description |
|------|-------------|
| `pynext/transpiler/runtime/async.js` | `sleep()` Promise wrapper for setTimeout |

## Runtime Helpers

### `__py.sleep(seconds)`

```javascript
// Transpiled from: await asyncio.sleep(1.5)
await __py.sleep(1.5);

// Implementation
export function sleep(seconds) {
    const ms = Math.max(0, (Number(seconds) || 0) * 1000);
    return new Promise(resolve => setTimeout(resolve, ms));
}
```

### `__py.contextmanager(genFn)`

```javascript
// Runtime support for @contextmanager decorated functions
export function contextmanager(genFn) {
    return function(...args) {
        return {
            _gen: null,
            __enter__() {
                this._gen = genFn(...args);
                return this._gen.next().value;
            },
            __exit__(excType, excVal, excTb) {
                try {
                    if (excType) this._gen.throw(excVal);
                    else this._gen.next();
                } catch (e) {
                    if (e !== excVal) throw e;
                }
                return false;
            }
        };
    };
}
```

### `__py.proxy.createAttributeProxy(target)`

Already existed in `proxy.js`. Added to `__py` namespace for attribute access interception.

## Success Criteria

- [x] 59 new tests passing
- [x] Python-JS equivalence for all features
- [x] No performance overhead for non-Proxy classes
- [x] Full who/what/when/where/why/how documentation
- [x] No regressions in existing tests (24,276 passing)

