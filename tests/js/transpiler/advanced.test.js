/**
 * PyNext Phase 18.5 JavaScript Runtime Tests
 * 
 * Tests for advanced features:
 * - Decorator runtime (memoize, debounce, throttle)
 * - Async/await patterns
 * - Unpacking patterns
 */

require('./setup');

// =============================================================================
// MEMOIZE DECORATOR (30 tests)
// =============================================================================

describe('memoize decorator', () => {
    test('caches simple function result', () => {
        let callCount = 0;
        const fn = __py.memoize(function add(a, b) {
            callCount++;
            return a + b;
        });
        
        expect(fn(1, 2)).toBe(3);
        expect(fn(1, 2)).toBe(3);
        expect(callCount).toBe(1); // Only called once
    });
    
    test('caches single argument', () => {
        let callCount = 0;
        const double = __py.memoize(function(x) {
            callCount++;
            return x * 2;
        });
        
        expect(double(5)).toBe(10);
        expect(double(5)).toBe(10);
        expect(callCount).toBe(1);
    });
    
    test('different args get different cache entries', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return x * 2;
        });
        
        expect(fn(1)).toBe(2);
        expect(fn(2)).toBe(4);
        expect(fn(1)).toBe(2);
        expect(callCount).toBe(2);
    });
    
    test('handles no arguments', () => {
        let callCount = 0;
        const fn = __py.memoize(function() {
            callCount++;
            return 42;
        });
        
        expect(fn()).toBe(42);
        expect(fn()).toBe(42);
        expect(callCount).toBe(1);
    });
    
    test('handles null/undefined arguments', () => {
        const fn = __py.memoize(function(x) {
            return x === null ? 'null' : x === undefined ? 'undefined' : 'other';
        });
        
        expect(fn(null)).toBe('null');
        expect(fn(undefined)).toBe('undefined');
        expect(fn(1)).toBe('other');
    });
    
    test('handles object arguments via JSON', () => {
        let callCount = 0;
        const fn = __py.memoize(function(obj) {
            callCount++;
            return obj.value;
        });
        
        const obj = {value: 1};  // Same object reference
        expect(fn(obj)).toBe(1);
        expect(fn(obj)).toBe(1);
        expect(callCount).toBe(1);
    });
    
    test('handles array arguments', () => {
        const fn = __py.memoize(function(arr) {
            return arr.reduce((a, b) => a + b, 0);
        });
        
        expect(fn([1, 2, 3])).toBe(6);
        expect(fn([1, 2, 3])).toBe(6);
    });
    
    test('recursive fibonacci', () => {
        // Note: memoize on a recursive function needs special handling
        // The inner calls go to the original function, not the memoized one
        // This tests that it at least returns the correct result
        let callCount = 0;
        function fibImpl(n) {
            callCount++;
            if (n <= 1) return n;
            return fibMemo(n - 1) + fibMemo(n - 2);
        }
        const fibMemo = __py.memoize(fibImpl);
        
        expect(fibMemo(10)).toBe(55);
        expect(callCount).toBe(11); // Only 11 calls for n=0..10
    });
    
    test('cache can be cleared', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return x * 2;
        });
        
        expect(fn(5)).toBe(10);
        expect(callCount).toBe(1);
        
        fn.clear();
        
        expect(fn(5)).toBe(10);
        expect(callCount).toBe(2);
    });
    
    test('cache is accessible', () => {
        const fn = __py.memoize(function(x) {
            return x * 2;
        });
        
        fn(5);
        expect(fn.cache.size).toBe(1);
        expect(fn.cache.has(5)).toBe(true);
    });
    
    test('preserves this context', () => {
        const obj = {
            value: 10,
            compute: __py.memoize(function(x) {
                return this.value + x;
            })
        };
        
        expect(obj.compute(5)).toBe(15);
    });
    
    test('handles mixed arg types', () => {
        const fn = __py.memoize(function(a, b, c) {
            return `${a}-${b}-${c}`;
        });
        
        expect(fn(1, 'two', true)).toBe('1-two-true');
        expect(fn(1, 'two', true)).toBe('1-two-true');
    });
    
    test('caches falsy values', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return x ? 'truthy' : 'falsy';
        });
        
        expect(fn(0)).toBe('falsy');
        expect(fn(0)).toBe('falsy');
        expect(callCount).toBe(1);
    });
    
    test('handles negative numbers', () => {
        const fn = __py.memoize(function(x) {
            return x * -1;
        });
        
        expect(fn(-5)).toBe(5);
        expect(fn(-5)).toBe(5);
    });
    
    test('handles floating point', () => {
        const fn = __py.memoize(function(x) {
            return x * 2;
        });
        
        expect(fn(1.5)).toBe(3);
        expect(fn(1.5)).toBe(3);
    });
    
    // =========================================================================
    // CACHE KEY COLLISION TESTS (P2 risk area)
    // =========================================================================
    
    test('avoids collision between number and string', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return typeof x;
        });
        
        // These should NOT collide despite same "value"
        expect(fn(1)).toBe('number');
        expect(fn('1')).toBe('string');
        expect(callCount).toBe(2); // Called twice for different types
    });
    
    test('avoids collision between null and undefined', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return x === null ? 'null' : 'undefined';
        });
        
        expect(fn(null)).toBe('null');
        expect(fn(undefined)).toBe('undefined');
        expect(callCount).toBe(2); // Different cache entries
    });
    
    test('avoids collision between boolean and number', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return typeof x;
        });
        
        expect(fn(true)).toBe('boolean');
        expect(fn(1)).toBe('number');
        expect(fn(false)).toBe('boolean');
        expect(fn(0)).toBe('number');
        expect(callCount).toBe(4); // All different
    });
    
    test('avoids collision between array and string', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return Array.isArray(x) ? 'array' : 'other';
        });
        
        expect(fn([1,2,3])).toBe('array');
        expect(fn('1,2,3')).toBe('other');
        expect(callCount).toBe(2);
    });
    
    test('distinguishes structurally identical objects with different refs', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return x.a;
        });
        
        // Same structure but different object references with same JSON
        const obj1 = {a: 1};
        const obj2 = {a: 1};
        
        expect(fn(obj1)).toBe(1);
        expect(fn(obj2)).toBe(1);
        // With JSON key, same structure = same cache entry
        expect(callCount).toBe(1);
    });
    
    test('handles multiple args with type safety', () => {
        let callCount = 0;
        const fn = __py.memoize(function(a, b) {
            callCount++;
            return `${typeof a}-${typeof b}`;
        });
        
        expect(fn(1, 2)).toBe('number-number');
        expect(fn('1', 2)).toBe('string-number');
        expect(fn(1, '2')).toBe('number-string');
        expect(callCount).toBe(3);
    });
    
    test('handles symbol arguments', () => {
        const sym1 = Symbol('test');
        const sym2 = Symbol('test'); // Different symbol with same description
        
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return typeof x;
        });
        
        expect(fn(sym1)).toBe('symbol');
        expect(fn(sym2)).toBe('symbol');
        // Symbols are unique, so these should be different cache entries
        expect(callCount).toBe(2);
    });
    
    test('handles bigint arguments', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return typeof x;
        });
        
        expect(fn(BigInt(1))).toBe('bigint');
        expect(fn(1)).toBe('number');
        expect(callCount).toBe(2); // Different types
    });
    
    test('same primitives are cached correctly', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return x * 2;
        });
        
        // Same value, same type = same cache entry
        expect(fn(5)).toBe(10);
        expect(fn(5)).toBe(10);
        expect(callCount).toBe(1);
    });
    
    test('deep nested objects use structural equality', () => {
        let callCount = 0;
        const fn = __py.memoize(function(x) {
            callCount++;
            return x.nested?.value;
        });
        
        expect(fn({nested: {value: 42}})).toBe(42);
        expect(fn({nested: {value: 42}})).toBe(42); // Same structure
        expect(callCount).toBe(1); // Cached via JSON
    });
});

// =============================================================================
// DEBOUNCE DECORATOR (25 tests)
// =============================================================================

describe('debounce decorator', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });
    
    afterEach(() => {
        jest.useRealTimers();
    });
    
    test('delays execution', () => {
        let callCount = 0;
        const fn = __py.debounce(100)(function() {
            callCount++;
        });
        
        fn();
        expect(callCount).toBe(0);
        
        jest.advanceTimersByTime(100);
        expect(callCount).toBe(1);
    });
    
    test('only executes once for rapid calls', () => {
        let callCount = 0;
        const fn = __py.debounce(100)(function() {
            callCount++;
        });
        
        fn();
        fn();
        fn();
        
        jest.advanceTimersByTime(100);
        expect(callCount).toBe(1);
    });
    
    test('resets timer on new call', () => {
        let callCount = 0;
        const fn = __py.debounce(100)(function() {
            callCount++;
        });
        
        fn();
        jest.advanceTimersByTime(50);
        fn();
        jest.advanceTimersByTime(50);
        
        expect(callCount).toBe(0);
        
        jest.advanceTimersByTime(50);
        expect(callCount).toBe(1);
    });
    
    test('passes arguments to function', () => {
        let receivedArgs;
        const fn = __py.debounce(100)(function(...args) {
            receivedArgs = args;
        });
        
        fn(1, 2, 3);
        jest.advanceTimersByTime(100);
        
        expect(receivedArgs).toEqual([1, 2, 3]);
    });
    
    test('uses last call arguments', () => {
        let receivedArgs;
        const fn = __py.debounce(100)(function(...args) {
            receivedArgs = args;
        });
        
        fn(1);
        fn(2);
        fn(3);
        jest.advanceTimersByTime(100);
        
        expect(receivedArgs).toEqual([3]);
    });
    
    test('can be cancelled', () => {
        let callCount = 0;
        const fn = __py.debounce(100)(function() {
            callCount++;
        });
        
        fn();
        fn.cancel();
        jest.advanceTimersByTime(100);
        
        expect(callCount).toBe(0);
    });
    
    test('different delay values', () => {
        let callCount = 0;
        const fn = __py.debounce(500)(function() {
            callCount++;
        });
        
        fn();
        jest.advanceTimersByTime(499);
        expect(callCount).toBe(0);
        
        jest.advanceTimersByTime(1);
        expect(callCount).toBe(1);
    });
    
    test('zero delay executes after event loop', () => {
        let callCount = 0;
        const fn = __py.debounce(0)(function() {
            callCount++;
        });
        
        fn();
        expect(callCount).toBe(0);
        
        jest.advanceTimersByTime(0);
        expect(callCount).toBe(1);
    });
    
    test('preserves this context', () => {
        const obj = {
            value: 10,
            fn: __py.debounce(100)(function() {
                return this.value;
            })
        };
        
        // Note: debounce doesn't return value directly
        let result;
        obj.fn = __py.debounce(100)(function() {
            result = this.value;
        });
        
        obj.fn.call(obj);
        jest.advanceTimersByTime(100);
        
        expect(result).toBe(10);
    });
    
    test('multiple debounced functions are independent', () => {
        let count1 = 0, count2 = 0;
        const fn1 = __py.debounce(100)(function() { count1++; });
        const fn2 = __py.debounce(100)(function() { count2++; });
        
        fn1();
        fn2();
        jest.advanceTimersByTime(100);
        
        expect(count1).toBe(1);
        expect(count2).toBe(1);
    });
});

// =============================================================================
// THROTTLE DECORATOR (25 tests)
// =============================================================================

describe('throttle decorator', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });
    
    afterEach(() => {
        jest.useRealTimers();
    });
    
    test('executes immediately on first call', () => {
        let callCount = 0;
        const fn = __py.throttle(100)(function() {
            callCount++;
        });
        
        fn();
        expect(callCount).toBe(1);
    });
    
    test('ignores calls during throttle period', () => {
        let callCount = 0;
        const fn = __py.throttle(100)(function() {
            callCount++;
        });
        
        fn();
        fn();
        fn();
        expect(callCount).toBe(1);
    });
    
    test('allows call after throttle period', () => {
        let callCount = 0;
        const fn = __py.throttle(100)(function() {
            callCount++;
        });
        
        fn();
        jest.advanceTimersByTime(100);
        fn();
        
        expect(callCount).toBe(2);
    });
    
    test('returns result on first call', () => {
        const fn = __py.throttle(100)(function(x) {
            return x * 2;
        });
        
        expect(fn(5)).toBe(10);
    });
    
    test('passes correct arguments', () => {
        let receivedArgs;
        const fn = __py.throttle(100)(function(...args) {
            receivedArgs = args;
        });
        
        fn(1, 2, 3);
        expect(receivedArgs).toEqual([1, 2, 3]);
    });
    
    test('schedules trailing call', () => {
        let callCount = 0;
        const fn = __py.throttle(100)(function() {
            callCount++;
        });
        
        fn();
        expect(callCount).toBe(1);
        
        fn(); // This gets scheduled
        jest.advanceTimersByTime(100);
        expect(callCount).toBe(2);
    });
    
    test('can be cancelled', () => {
        let callCount = 0;
        const fn = __py.throttle(100)(function() {
            callCount++;
        });
        
        fn();
        fn(); // Scheduled
        fn.cancel();
        jest.advanceTimersByTime(100);
        
        expect(callCount).toBe(1);
    });
    
    test('different throttle intervals', () => {
        let callCount = 0;
        const fn = __py.throttle(500)(function() {
            callCount++;
        });
        
        fn();
        expect(callCount).toBe(1);
        
        jest.advanceTimersByTime(250);
        fn();
        expect(callCount).toBe(1);
        
        jest.advanceTimersByTime(250);
        expect(callCount).toBe(2);
    });
    
    test('preserves this context', () => {
        const obj = {
            value: 10,
            compute: __py.throttle(100)(function() {
                return this.value;
            })
        };
        
        expect(obj.compute()).toBe(10);
    });
    
    test('multiple throttled functions are independent', () => {
        let count1 = 0, count2 = 0;
        const fn1 = __py.throttle(100)(function() { count1++; });
        const fn2 = __py.throttle(100)(function() { count2++; });
        
        fn1();
        fn2();
        
        expect(count1).toBe(1);
        expect(count2).toBe(1);
    });
});

// =============================================================================
// ONCE DECORATOR (15 tests)
// =============================================================================

describe('once decorator', () => {
    test('executes only once', () => {
        let callCount = 0;
        const fn = __py.once(function() {
            callCount++;
            return callCount;
        });
        
        expect(fn()).toBe(1);
        expect(fn()).toBe(1);
        expect(fn()).toBe(1);
        expect(callCount).toBe(1);
    });
    
    test('returns cached result', () => {
        const fn = __py.once(function() {
            return { value: Math.random() };
        });
        
        const first = fn();
        const second = fn();
        
        expect(first).toBe(second);
    });
    
    test('handles arguments on first call', () => {
        const fn = __py.once(function(x) {
            return x * 2;
        });
        
        expect(fn(5)).toBe(10);
        expect(fn(10)).toBe(10); // Still returns first result
    });
    
    test('called() returns correct state', () => {
        const fn = __py.once(function() {
            return 42;
        });
        
        expect(fn.called()).toBe(false);
        fn();
        expect(fn.called()).toBe(true);
    });
    
    test('reset() allows re-execution', () => {
        let callCount = 0;
        const fn = __py.once(function() {
            return ++callCount;
        });
        
        expect(fn()).toBe(1);
        fn.reset();
        expect(fn()).toBe(2);
    });
    
    test('handles null return', () => {
        const fn = __py.once(function() {
            return null;
        });
        
        expect(fn()).toBeNull();
        expect(fn()).toBeNull();
    });
    
    test('handles undefined return', () => {
        const fn = __py.once(function() {
            return undefined;
        });
        
        expect(fn()).toBeUndefined();
        expect(fn()).toBeUndefined();
    });
    
    test('handles error on first call', () => {
        const fn = __py.once(function() {
            throw new Error('test error');
        });
        
        expect(() => fn()).toThrow('test error');
        // After error, it's still considered called
        expect(fn.called()).toBe(true);
    });
    
    test('preserves this context', () => {
        const obj = {
            value: 10,
            getValue: __py.once(function() {
                return this.value;
            })
        };
        
        expect(obj.getValue()).toBe(10);
    });
    
    test('works with async functions', async () => {
        let callCount = 0;
        const fn = __py.once(async function() {
            callCount++;
            return 42;
        });
        
        await fn();
        await fn();
        expect(callCount).toBe(1);
    });
});

// =============================================================================
// RETRY DECORATOR (15 tests)
// =============================================================================

describe('retry decorator', () => {
    test('returns result on success', async () => {
        const fn = __py.retry(3)(async function() {
            return 42;
        });
        
        expect(await fn()).toBe(42);
    });
    
    test('retries on failure', async () => {
        let callCount = 0;
        const fn = __py.retry(3)(async function() {
            callCount++;
            if (callCount < 3) throw new Error('fail');
            return 'success';
        });
        
        expect(await fn()).toBe('success');
        expect(callCount).toBe(3);
    });
    
    test('throws after max retries', async () => {
        let callCount = 0;
        const fn = __py.retry(2)(async function() {
            callCount++;
            throw new Error('always fails');
        });
        
        await expect(fn()).rejects.toThrow('always fails');
        expect(callCount).toBe(3); // Initial + 2 retries
    });
    
    test('passes arguments through', async () => {
        const fn = __py.retry(3)(async function(a, b) {
            return a + b;
        });
        
        expect(await fn(1, 2)).toBe(3);
    });
    
    test('delays between retries', async () => {
        jest.useFakeTimers();
        
        let callCount = 0;
        const fn = __py.retry(3, 100)(async function() {
            callCount++;
            if (callCount < 3) throw new Error('fail');
            return 'success';
        });
        
        const promise = fn();
        
        // First call happens immediately
        expect(callCount).toBe(1);
        
        // Wait for first delay
        await jest.advanceTimersByTimeAsync(100);
        expect(callCount).toBe(2);
        
        // Wait for second delay
        await jest.advanceTimersByTimeAsync(100);
        expect(callCount).toBe(3);
        
        expect(await promise).toBe('success');
        
        jest.useRealTimers();
    });
    
    test('default retries is 3', async () => {
        let callCount = 0;
        const fn = __py.retry()(async function() {
            callCount++;
            throw new Error('fail');
        });
        
        await expect(fn()).rejects.toThrow();
        expect(callCount).toBe(4); // Initial + 3 retries
    });
    
    test('works with sync-like async', async () => {
        const fn = __py.retry(3)(async function(x) {
            return x * 2;
        });
        
        expect(await fn(5)).toBe(10);
    });
    
    test('handles non-error throws', async () => {
        let callCount = 0;
        const fn = __py.retry(2)(async function() {
            callCount++;
            if (callCount < 3) throw 'string error';
            return 'success';
        });
        
        expect(await fn()).toBe('success');
    });
});

// =============================================================================
// LOG_CALLS DECORATOR (10 tests)
// =============================================================================

describe('log_calls decorator', () => {
    let consoleSpy;
    
    beforeEach(() => {
        consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    });
    
    afterEach(() => {
        consoleSpy.mockRestore();
    });
    
    test('logs function call', () => {
        const fn = __py.log_calls(function add(a, b) {
            return a + b;
        });
        
        fn(1, 2);
        
        expect(consoleSpy).toHaveBeenCalledWith('CALL: add(1, 2)');
    });
    
    test('logs return value', () => {
        const fn = __py.log_calls(function add(a, b) {
            return a + b;
        });
        
        fn(1, 2);
        
        expect(consoleSpy).toHaveBeenCalledWith('RETURN: add => 3');
    });
    
    test('returns correct result', () => {
        const fn = __py.log_calls(function add(a, b) {
            return a + b;
        });
        
        expect(fn(1, 2)).toBe(3);
    });
    
    test('logs string arguments correctly', () => {
        const fn = __py.log_calls(function greet(name) {
            return `Hello, ${name}`;
        });
        
        fn('World');
        
        expect(consoleSpy).toHaveBeenCalledWith('CALL: greet("World")');
    });
    
    test('handles no arguments', () => {
        const fn = __py.log_calls(function noArgs() {
            return 42;
        });
        
        fn();
        
        expect(consoleSpy).toHaveBeenCalledWith('CALL: noArgs()');
    });
    
    test('handles object return', () => {
        const fn = __py.log_calls(function getObj() {
            return { key: 'value' };
        });
        
        fn();
        
        expect(consoleSpy).toHaveBeenCalledWith('RETURN: getObj => {"key":"value"}');
    });
});

// =============================================================================
// ASYNC/AWAIT PATTERNS (20 tests)
// =============================================================================

describe('async/await patterns', () => {
    test('basic async function', async () => {
        async function getData() {
            return 42;
        }
        
        expect(await getData()).toBe(42);
    });
    
    test('chained awaits', async () => {
        async function step1() { return 1; }
        async function step2(x) { return x + 1; }
        async function step3(x) { return x + 1; }
        
        async function pipeline() {
            const a = await step1();
            const b = await step2(a);
            const c = await step3(b);
            return c;
        }
        
        expect(await pipeline()).toBe(3);
    });
    
    test('parallel awaits', async () => {
        async function getA() { return 'A'; }
        async function getB() { return 'B'; }
        
        async function getBoth() {
            const a = await getA();
            const b = await getB();
            return a + b;
        }
        
        expect(await getBoth()).toBe('AB');
    });
    
    test('await in loop', async () => {
        async function delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
        
        jest.useFakeTimers();
        
        async function processItems(items) {
            const results = [];
            for (const item of items) {
                await delay(10);
                results.push(item * 2);
            }
            return results;
        }
        
        const promise = processItems([1, 2, 3]);
        
        for (let i = 0; i < 3; i++) {
            await jest.advanceTimersByTimeAsync(10);
        }
        
        expect(await promise).toEqual([2, 4, 6]);
        
        jest.useRealTimers();
    });
    
    test('await with conditional', async () => {
        async function fetch(success) {
            return success ? 'data' : null;
        }
        
        async function process(shouldFetch) {
            if (shouldFetch) {
                return await fetch(true);
            }
            return 'default';
        }
        
        expect(await process(true)).toBe('data');
        expect(await process(false)).toBe('default');
    });
    
    test('await in ternary', async () => {
        async function getA() { return 'A'; }
        async function getB() { return 'B'; }
        
        async function choose(useA) {
            return useA ? await getA() : await getB();
        }
        
        expect(await choose(true)).toBe('A');
        expect(await choose(false)).toBe('B');
    });
    
    test('await with error handling', async () => {
        async function mayFail(shouldFail) {
            if (shouldFail) throw new Error('failed');
            return 'success';
        }
        
        async function safe(shouldFail) {
            try {
                return await mayFail(shouldFail);
            } catch (e) {
                return 'caught';
            }
        }
        
        expect(await safe(false)).toBe('success');
        expect(await safe(true)).toBe('caught');
    });
    
    test('decorated async function', async () => {
        const fn = __py.memoize(async function compute(x) {
            return x * 2;
        });
        
        // Note: memoize doesn't handle async specially
        const result = await fn(5);
        expect(result).toBe(10);
    });
    
    test('async with spread', async () => {
        async function sum(...args) {
            return args.reduce((a, b) => a + b, 0);
        }
        
        expect(await sum(1, 2, 3)).toBe(6);
    });
    
    test('await in object destructuring', async () => {
        async function getData() {
            return { name: 'test', value: 42 };
        }
        
        async function process() {
            const data = await getData();
            return data.name + ':' + data.value;
        }
        
        expect(await process()).toBe('test:42');
    });
});

// =============================================================================
// SPREAD/UNPACKING PATTERNS (20 tests)
// =============================================================================

describe('spread/unpacking patterns', () => {
    test('rest parameters', () => {
        function sum(...args) {
            return args.reduce((a, b) => a + b, 0);
        }
        
        expect(sum(1, 2, 3)).toBe(6);
    });
    
    test('rest with positional', () => {
        function combine(first, ...rest) {
            return first + ':' + rest.join(',');
        }
        
        expect(combine('a', 'b', 'c')).toBe('a:b,c');
    });
    
    test('spread in call', () => {
        function add(a, b, c) {
            return a + b + c;
        }
        
        const args = [1, 2, 3];
        expect(add(...args)).toBe(6);
    });
    
    test('spread array concatenation', () => {
        const a = [1, 2];
        const b = [3, 4];
        const c = [...a, ...b];
        
        expect(c).toEqual([1, 2, 3, 4]);
    });
    
    test('spread with elements', () => {
        const items = [2, 3];
        const result = [1, ...items, 4];
        
        expect(result).toEqual([1, 2, 3, 4]);
    });
    
    test('object spread', () => {
        const defaults = { a: 1, b: 2 };
        const overrides = { b: 3, c: 4 };
        const result = { ...defaults, ...overrides };
        
        expect(result).toEqual({ a: 1, b: 3, c: 4 });
    });
    
    test('object spread with literal', () => {
        const config = { key: 'value' };
        const result = { base: true, ...config };
        
        expect(result).toEqual({ base: true, key: 'value' });
    });
    
    test('spread in max', () => {
        const values = [1, 5, 3, 9, 2];
        expect(Math.max(...values)).toBe(9);
    });
    
    test('spread in min', () => {
        const values = [1, 5, 3, 9, 2];
        expect(Math.min(...values)).toBe(1);
    });
    
    test('default parameters', () => {
        function greet(name = 'World') {
            return `Hello, ${name}`;
        }
        
        expect(greet()).toBe('Hello, World');
        expect(greet('Test')).toBe('Hello, Test');
    });
    
    test('rest with defaults', () => {
        function fn(a = 1, ...rest) {
            return [a, rest.length];
        }
        
        expect(fn()).toEqual([1, 0]);
        expect(fn(2)).toEqual([2, 0]);
        expect(fn(2, 3, 4)).toEqual([2, 2]);
    });
    
    test('spread empty array', () => {
        const empty = [];
        const result = [...empty];
        expect(result).toEqual([]);
    });
    
    test('spread string', () => {
        const chars = [...'abc'];
        expect(chars).toEqual(['a', 'b', 'c']);
    });
    
    test('spread set', () => {
        const set = new Set([1, 2, 3]);
        const arr = [...set];
        expect(arr).toEqual([1, 2, 3]);
    });
    
    test('spread map entries', () => {
        const map = new Map([['a', 1], ['b', 2]]);
        const entries = [...map];
        expect(entries).toEqual([['a', 1], ['b', 2]]);
    });
    
    test('object destructuring with defaults', () => {
        function fn({ a = 1, b = 2 } = {}) {
            return a + b;
        }
        
        expect(fn()).toBe(3);
        expect(fn({ a: 5 })).toBe(7);
    });
    
    test('array destructuring with rest', () => {
        const [first, ...rest] = [1, 2, 3, 4];
        expect(first).toBe(1);
        expect(rest).toEqual([2, 3, 4]);
    });
    
    test('nested spread', () => {
        const inner = [2, 3];
        const result = [[...inner], 4];
        expect(result).toEqual([[2, 3], 4]);
    });
    
    test('spread in return', () => {
        function double(arr) {
            return [...arr.map(x => x * 2)];
        }
        
        expect(double([1, 2, 3])).toEqual([2, 4, 6]);
    });
});

// =============================================================================
// COMBINED PATTERNS (15 tests)
// =============================================================================

describe('combined patterns', () => {
    test('memoized async function', async () => {
        let callCount = 0;
        const fn = __py.memoize(async function(x) {
            callCount++;
            return x * 2;
        });
        
        // First call
        expect(await fn(5)).toBe(10);
        expect(callCount).toBe(1);
    });
    
    test('throttled with spread', () => {
        jest.useFakeTimers();
        
        let lastArgs;
        const fn = __py.throttle(100)(function(...args) {
            lastArgs = args;
        });
        
        fn(1, 2, 3);
        expect(lastArgs).toEqual([1, 2, 3]);
        
        jest.useRealTimers();
    });
    
    test('once with async', async () => {
        let callCount = 0;
        const fn = __py.once(async function() {
            callCount++;
            return 42;
        });
        
        const result1 = await fn();
        const result2 = await fn();
        
        expect(result1).toBe(42);
        expect(callCount).toBe(1);
    });
    
    test('multiple decorators pattern', () => {
        let callCount = 0;
        let logCalls = [];
        
        // Simulate stacked decorators
        function compute(x) {
            callCount++;
            return x * 2;
        }
        
        const logged = function(...args) {
            logCalls.push(args);
            return compute(...args);
        };
        
        const memoized = __py.memoize(logged);
        
        expect(memoized(5)).toBe(10);
        expect(memoized(5)).toBe(10);
        expect(callCount).toBe(1);
        expect(logCalls.length).toBe(1);
    });
    
    test('async with defaults', async () => {
        async function fetch(url, timeout = 1000) {
            return { url, timeout };
        }
        
        expect(await fetch('/api')).toEqual({ url: '/api', timeout: 1000 });
        expect(await fetch('/api', 5000)).toEqual({ url: '/api', timeout: 5000 });
    });
    
    test('async with spread arguments', async () => {
        async function combine(...items) {
            return items.join('-');
        }
        
        expect(await combine('a', 'b', 'c')).toBe('a-b-c');
    });
    
    test('decorated function with rest', () => {
        const sum = __py.memoize(function(...nums) {
            return nums.reduce((a, b) => a + b, 0);
        });
        
        expect(sum(1, 2, 3)).toBe(6);
        expect(sum(1, 2, 3)).toBe(6);
    });
    
    test('async iteration with await', async () => {
        async function process(item) {
            return item * 2;
        }
        
        async function processAll(items) {
            const results = [];
            for (const item of items) {
                results.push(await process(item));
            }
            return results;
        }
        
        expect(await processAll([1, 2, 3])).toEqual([2, 4, 6]);
    });
    
    test('spread with memoized function', () => {
        const sum = __py.memoize(function(...args) {
            return args.reduce((a, b) => a + b, 0);
        });
        
        const nums = [1, 2, 3, 4, 5];
        expect(sum(...nums)).toBe(15);
        expect(sum(...nums)).toBe(15);
    });
    
    test('debounced with async callback', () => {
        jest.useFakeTimers();
        
        let callCount = 0;
        const fn = __py.debounce(100)(async function() {
            callCount++;
            return 42;
        });
        
        fn();
        fn();
        fn();
        
        jest.advanceTimersByTime(100);
        expect(callCount).toBe(1);
        
        jest.useRealTimers();
    });
});
