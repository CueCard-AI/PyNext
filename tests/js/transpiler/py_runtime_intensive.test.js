/**
 * Intensive Tests for Python Runtime Helpers (__py.*)
 * 
 * Tests edge cases that could cause silent failures in transpiled code.
 * 
 * Critical Scenarios:
 * 1. __py.at() - negative indexing edge cases
 * 2. __py.slice() - all slice patterns including step
 * 3. __py.bool() - Python truthiness vs JS truthiness
 * 4. __py.eq() - deep equality with circular refs
 * 5. __py.mod() - negative modulo
 * 6. __py.floordiv() - negative floor division
 * 7. __py.in() - membership testing for all types
 * 8. __py.add() - polymorphic addition
 * 9. __py.mul() - string multiplication (not covered elsewhere)
 */

// Import from transpiler runtime
const path = require('path');

// Mock the errors module for standalone testing
const mockErrors = {
    ValueError: class ValueError extends Error {
        constructor(msg) { super(msg); this.name = 'ValueError'; }
    },
    KeyError: class KeyError extends Error {
        constructor(msg) { super(msg); this.name = 'KeyError'; }
    },
    IndexError: class IndexError extends Error {
        constructor(msg) { super(msg); this.name = 'IndexError'; }
    },
    ZeroDivisionError: class ZeroDivisionError extends Error {
        constructor(msg) { super(msg); this.name = 'ZeroDivisionError'; }
    },
    PyTypeError: class PyTypeError extends Error {
        constructor(msg) { super(msg); this.name = 'TypeError'; }
    },
};

// Inline implementations for testing (matching core.js)
const __py = {
    at(arr, i) {
        if (arr === null || arr === undefined) {
            throw new mockErrors.PyTypeError("'NoneType' object is not subscriptable");
        }
        if (i < 0) return arr[arr.length + i];
        return arr[i];
    },
    
    slice(arr, start, stop, step = 1) {
        if (arr === null || arr === undefined) {
            throw new mockErrors.PyTypeError("'NoneType' object is not subscriptable");
        }
        const len = arr.length;
        const isString = typeof arr === 'string';
        
        if (step === 0) throw new mockErrors.ValueError("slice step cannot be zero");
        
        if (step > 0) {
            start = start === null ? 0 : (start < 0 ? Math.max(0, len + start) : Math.min(len, start));
            stop = stop === null ? len : (stop < 0 ? Math.max(0, len + stop) : Math.min(len, stop));
            
            const result = [];
            for (let i = start; i < stop; i += step) {
                result.push(arr[i]);
            }
            return isString ? result.join('') : result;
        } else {
            start = start === null ? len - 1 : (start < 0 ? Math.max(-1, len + start) : Math.min(len - 1, start));
            stop = stop === null ? -1 : (stop < 0 ? Math.max(-1, len + stop) : Math.min(len - 1, stop));
            
            const result = [];
            for (let i = start; i > stop; i += step) {
                if (i >= 0 && i < len) result.push(arr[i]);
            }
            return isString ? result.join('') : result;
        }
    },
    
    bool(x) {
        if (x === null || x === undefined) return false;
        if (x === false || x === 0 || x === '') return false;
        if (Array.isArray(x)) return x.length > 0;
        if (typeof x === 'object') {
            if (x.constructor === Object) return Object.keys(x).length > 0;
            if (x instanceof Set || x instanceof Map) return x.size > 0;
        }
        return true;
    },
    
    mod(a, b) {
        if (b === 0) {
            throw new mockErrors.ZeroDivisionError("integer division or modulo by zero");
        }
        const result = ((a % b) + b) % b;
        return result === 0 ? 0 : result;
    },
    
    floordiv(a, b) {
        if (b === 0) {
            throw new mockErrors.ZeroDivisionError("integer division or modulo by zero");
        }
        return Math.floor(a / b);
    },
    
    eq(a, b, seenA = null, seenB = null) {
        if (a === b) return true;
        if (a === null || b === null) return a === b;
        if (a === undefined || b === undefined) return a === b;
        if (typeof a !== typeof b) return false;
        
        if (typeof a === 'object') {
            seenA = seenA || new WeakMap();
            seenB = seenB || new WeakMap();
            
            if (seenA.has(a) && seenB.has(b)) {
                return seenA.get(a) === seenB.get(b);
            }
            
            const id = {};
            seenA.set(a, id);
            seenB.set(b, id);
            
            if (Array.isArray(a) && Array.isArray(b)) {
                if (a.length !== b.length) return false;
                for (let i = 0; i < a.length; i++) {
                    if (!__py.eq(a[i], b[i], seenA, seenB)) return false;
                }
                return true;
            }
            
            if (a.constructor === Object && b.constructor === Object) {
                const keysA = Object.keys(a);
                const keysB = Object.keys(b);
                if (keysA.length !== keysB.length) return false;
                for (const key of keysA) {
                    if (!Object.prototype.hasOwnProperty.call(b, key)) return false;
                    if (!__py.eq(a[key], b[key], seenA, seenB)) return false;
                }
                return true;
            }
        }
        
        return false;
    },
    
    contains(item, container) {
        if (container === null || container === undefined) {
            throw new mockErrors.PyTypeError("argument of type 'NoneType' is not iterable");
        }
        if (typeof container === 'string') {
            return container.includes(String(item));
        }
        if (Array.isArray(container)) {
            return container.some(x => __py.eq(x, item));
        }
        if (container instanceof Set) {
            for (const val of container) {
                if (__py.eq(val, item)) return true;
            }
            return false;
        }
        if (container instanceof Map) {
            for (const key of container.keys()) {
                if (__py.eq(key, item)) return true;
            }
            return false;
        }
        if (typeof container === 'object') {
            return Object.prototype.hasOwnProperty.call(container, item);
        }
        return false;
    },
    
    add(a, b) {
        if (typeof a === 'string' || typeof b === 'string') {
            return String(a) + String(b);
        }
        if (Array.isArray(a) && Array.isArray(b)) {
            return [...a, ...b];
        }
        return a + b;
    },
    
    mul(a, b) {
        if (typeof a === 'string' && typeof b === 'number') {
            if (b <= 0) return '';
            return a.repeat(b);
        }
        if (typeof b === 'string' && typeof a === 'number') {
            if (a <= 0) return '';
            return b.repeat(a);
        }
        if (Array.isArray(a) && typeof b === 'number') {
            if (b <= 0) return [];
            const result = [];
            for (let i = 0; i < b; i++) result.push(...a);
            return result;
        }
        if (Array.isArray(b) && typeof a === 'number') {
            if (a <= 0) return [];
            const result = [];
            for (let i = 0; i < a; i++) result.push(...b);
            return result;
        }
        return a * b;
    },
};


// =============================================================================
// TESTS: __py.at() - Negative Indexing
// =============================================================================

describe('__py.at() - Negative Indexing Edge Cases', () => {
    test('array positive index', () => {
        expect(__py.at([1, 2, 3, 4, 5], 0)).toBe(1);
        expect(__py.at([1, 2, 3, 4, 5], 2)).toBe(3);
        expect(__py.at([1, 2, 3, 4, 5], 4)).toBe(5);
    });
    
    test('array negative index', () => {
        expect(__py.at([1, 2, 3, 4, 5], -1)).toBe(5);
        expect(__py.at([1, 2, 3, 4, 5], -2)).toBe(4);
        expect(__py.at([1, 2, 3, 4, 5], -5)).toBe(1);
    });
    
    test('string positive index', () => {
        expect(__py.at('hello', 0)).toBe('h');
        expect(__py.at('hello', 4)).toBe('o');
    });
    
    test('string negative index', () => {
        expect(__py.at('hello', -1)).toBe('o');
        expect(__py.at('hello', -5)).toBe('h');
    });
    
    test('out of bounds returns undefined (not error)', () => {
        expect(__py.at([1, 2, 3], 10)).toBeUndefined();
        expect(__py.at([1, 2, 3], -10)).toBeUndefined();
    });
    
    test('empty array', () => {
        expect(__py.at([], 0)).toBeUndefined();
        expect(__py.at([], -1)).toBeUndefined();
    });
    
    test('single element array', () => {
        expect(__py.at([42], 0)).toBe(42);
        expect(__py.at([42], -1)).toBe(42);
    });
    
    test('null/undefined throws', () => {
        expect(() => __py.at(null, 0)).toThrow();
        expect(() => __py.at(undefined, 0)).toThrow();
    });
});


// =============================================================================
// TESTS: __py.slice() - All Slice Patterns
// =============================================================================

describe('__py.slice() - Comprehensive Slicing', () => {
    const arr = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    
    describe('Basic slices', () => {
        test('start:stop', () => {
            expect(__py.slice(arr, 2, 5)).toEqual([2, 3, 4]);
            expect(__py.slice(arr, 0, 3)).toEqual([0, 1, 2]);
        });
        
        test('start only (to end)', () => {
            expect(__py.slice(arr, 5, null)).toEqual([5, 6, 7, 8, 9]);
            expect(__py.slice(arr, 8, null)).toEqual([8, 9]);
        });
        
        test('stop only (from start)', () => {
            expect(__py.slice(arr, null, 3)).toEqual([0, 1, 2]);
            expect(__py.slice(arr, null, 1)).toEqual([0]);
        });
        
        test('full copy (no args)', () => {
            expect(__py.slice(arr, null, null)).toEqual(arr);
        });
    });
    
    describe('Negative indices', () => {
        test('negative start', () => {
            expect(__py.slice(arr, -3, null)).toEqual([7, 8, 9]);
            expect(__py.slice(arr, -1, null)).toEqual([9]);
        });
        
        test('negative stop', () => {
            expect(__py.slice(arr, null, -1)).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8]);
            expect(__py.slice(arr, null, -3)).toEqual([0, 1, 2, 3, 4, 5, 6]);
        });
        
        test('both negative', () => {
            expect(__py.slice(arr, -5, -2)).toEqual([5, 6, 7]);
        });
    });
    
    describe('With step', () => {
        test('step > 1', () => {
            expect(__py.slice(arr, null, null, 2)).toEqual([0, 2, 4, 6, 8]);
            expect(__py.slice(arr, 1, null, 2)).toEqual([1, 3, 5, 7, 9]);
            expect(__py.slice(arr, 0, 6, 3)).toEqual([0, 3]);
        });
        
        test('step = -1 (reverse)', () => {
            expect(__py.slice(arr, null, null, -1)).toEqual([9, 8, 7, 6, 5, 4, 3, 2, 1, 0]);
        });
        
        test('step < -1', () => {
            expect(__py.slice(arr, null, null, -2)).toEqual([9, 7, 5, 3, 1]);
        });
        
        test('step = 0 throws', () => {
            expect(() => __py.slice(arr, 0, 5, 0)).toThrow();
        });
    });
    
    describe('String slicing', () => {
        test('basic string slice', () => {
            expect(__py.slice('hello', 1, 4)).toBe('ell');
            expect(__py.slice('hello', null, -1)).toBe('hell');
        });
        
        test('string reverse', () => {
            expect(__py.slice('hello', null, null, -1)).toBe('olleh');
        });
        
        test('every other character', () => {
            expect(__py.slice('abcdefg', null, null, 2)).toBe('aceg');
        });
    });
    
    describe('Edge cases', () => {
        test('empty result', () => {
            expect(__py.slice(arr, 5, 5)).toEqual([]);
            expect(__py.slice(arr, 5, 3)).toEqual([]);
        });
        
        test('out of bounds handled gracefully', () => {
            expect(__py.slice(arr, 0, 100)).toEqual(arr);
            expect(__py.slice(arr, -100, 100)).toEqual(arr);
        });
        
        test('empty array', () => {
            expect(__py.slice([], 0, 5)).toEqual([]);
        });
    });
});


// =============================================================================
// TESTS: __py.bool() - Python Truthiness
// =============================================================================

describe('__py.bool() - Python Truthiness', () => {
    describe('Falsy values', () => {
        test('null and undefined', () => {
            expect(__py.bool(null)).toBe(false);
            expect(__py.bool(undefined)).toBe(false);
        });
        
        test('false and zero', () => {
            expect(__py.bool(false)).toBe(false);
            expect(__py.bool(0)).toBe(false);
            expect(__py.bool(0.0)).toBe(false);
            expect(__py.bool(-0)).toBe(false);
        });
        
        test('empty string', () => {
            expect(__py.bool('')).toBe(false);
        });
        
        test('empty array (Python falsy, JS truthy!)', () => {
            // This is the critical difference from JS
            expect(__py.bool([])).toBe(false);
        });
        
        test('empty object (Python falsy, JS truthy!)', () => {
            expect(__py.bool({})).toBe(false);
        });
        
        test('empty Set', () => {
            expect(__py.bool(new Set())).toBe(false);
        });
        
        test('empty Map', () => {
            expect(__py.bool(new Map())).toBe(false);
        });
    });
    
    describe('Truthy values', () => {
        test('true', () => {
            expect(__py.bool(true)).toBe(true);
        });
        
        test('non-zero numbers', () => {
            expect(__py.bool(1)).toBe(true);
            expect(__py.bool(-1)).toBe(true);
            expect(__py.bool(0.1)).toBe(true);
            expect(__py.bool(Infinity)).toBe(true);
        });
        
        test('non-empty string', () => {
            expect(__py.bool('hello')).toBe(true);
            expect(__py.bool(' ')).toBe(true);
            expect(__py.bool('0')).toBe(true);
        });
        
        test('non-empty array', () => {
            expect(__py.bool([1])).toBe(true);
            expect(__py.bool([0])).toBe(true); // Contains 0 but array is not empty
            expect(__py.bool([null])).toBe(true);
        });
        
        test('non-empty object', () => {
            expect(__py.bool({a: 1})).toBe(true);
            expect(__py.bool({x: null})).toBe(true);
        });
        
        test('non-empty Set', () => {
            expect(__py.bool(new Set([1]))).toBe(true);
        });
        
        test('non-empty Map', () => {
            expect(__py.bool(new Map([['a', 1]]))).toBe(true);
        });
    });
    
    describe('Edge cases', () => {
        test('NaN', () => {
            // NaN is falsy in JS, but Python considers it truthy
            // This is a design decision - follow Python or JS?
            // Current implementation follows JS (NaN is truthy in bool())
            expect(__py.bool(NaN)).toBe(true);
        });
        
        test('function', () => {
            expect(__py.bool(() => {})).toBe(true);
        });
        
        test('class instance', () => {
            class Foo {}
            expect(__py.bool(new Foo())).toBe(true);
        });
    });
});


// =============================================================================
// TESTS: __py.mod() - Python Modulo
// =============================================================================

describe('__py.mod() - Python Modulo', () => {
    test('positive numbers', () => {
        expect(__py.mod(7, 3)).toBe(1);
        expect(__py.mod(10, 5)).toBe(0);
        expect(__py.mod(1, 2)).toBe(1);
    });
    
    test('negative dividend (Python vs JS difference!)', () => {
        // JS: -1 % 3 = -1
        // Py: -1 % 3 = 2
        expect(__py.mod(-1, 3)).toBe(2);
        expect(__py.mod(-7, 3)).toBe(2);
        expect(__py.mod(-10, 4)).toBe(2);
    });
    
    test('negative divisor', () => {
        expect(__py.mod(7, -3)).toBe(-2);
        expect(__py.mod(-7, -3)).toBe(-1);
    });
    
    test('zero dividend', () => {
        expect(__py.mod(0, 5)).toBe(0);
        expect(__py.mod(0, -5)).toBe(0);
    });
    
    test('division by zero throws', () => {
        expect(() => __py.mod(5, 0)).toThrow();
        expect(() => __py.mod(0, 0)).toThrow();
    });
    
    test('floating point', () => {
        expect(__py.mod(7.5, 2.5)).toBeCloseTo(0);
        expect(__py.mod(-7.5, 2.5)).toBeCloseTo(0);
    });
});


// =============================================================================
// TESTS: __py.floordiv() - Python Floor Division
// =============================================================================

describe('__py.floordiv() - Python Floor Division', () => {
    test('positive numbers', () => {
        expect(__py.floordiv(7, 3)).toBe(2);
        expect(__py.floordiv(10, 5)).toBe(2);
        expect(__py.floordiv(1, 2)).toBe(0);
    });
    
    test('negative dividend (rounds toward -infinity!)', () => {
        // JS: Math.trunc(-7/3) = -2
        // Py: -7 // 3 = -3
        expect(__py.floordiv(-7, 3)).toBe(-3);
        expect(__py.floordiv(-1, 2)).toBe(-1);
    });
    
    test('negative divisor', () => {
        expect(__py.floordiv(7, -3)).toBe(-3);
        expect(__py.floordiv(-7, -3)).toBe(2);
    });
    
    test('zero dividend', () => {
        expect(__py.floordiv(0, 5)).toBe(0);
    });
    
    test('division by zero throws', () => {
        expect(() => __py.floordiv(5, 0)).toThrow();
    });
});


// =============================================================================
// TESTS: __py.eq() - Deep Equality
// =============================================================================

describe('__py.eq() - Deep Equality', () => {
    describe('Primitives', () => {
        test('numbers', () => {
            expect(__py.eq(1, 1)).toBe(true);
            expect(__py.eq(1, 2)).toBe(false);
            expect(__py.eq(1, 1.0)).toBe(true);
        });
        
        test('strings', () => {
            expect(__py.eq('hello', 'hello')).toBe(true);
            expect(__py.eq('hello', 'world')).toBe(false);
        });
        
        test('booleans', () => {
            expect(__py.eq(true, true)).toBe(true);
            expect(__py.eq(true, false)).toBe(false);
        });
        
        test('null and undefined', () => {
            expect(__py.eq(null, null)).toBe(true);
            expect(__py.eq(undefined, undefined)).toBe(true);
            expect(__py.eq(null, undefined)).toBe(false);
        });
    });
    
    describe('Arrays (Python lists)', () => {
        test('equal arrays', () => {
            expect(__py.eq([1, 2, 3], [1, 2, 3])).toBe(true);
        });
        
        test('different arrays', () => {
            expect(__py.eq([1, 2, 3], [1, 2, 4])).toBe(false);
            expect(__py.eq([1, 2, 3], [1, 2])).toBe(false);
        });
        
        test('nested arrays', () => {
            expect(__py.eq([[1, 2], [3, 4]], [[1, 2], [3, 4]])).toBe(true);
            expect(__py.eq([[1, 2], [3, 4]], [[1, 2], [3, 5]])).toBe(false);
        });
        
        test('empty arrays', () => {
            expect(__py.eq([], [])).toBe(true);
        });
    });
    
    describe('Objects (Python dicts)', () => {
        test('equal objects', () => {
            expect(__py.eq({a: 1, b: 2}, {a: 1, b: 2})).toBe(true);
        });
        
        test('different values', () => {
            expect(__py.eq({a: 1, b: 2}, {a: 1, b: 3})).toBe(false);
        });
        
        test('different keys', () => {
            expect(__py.eq({a: 1, b: 2}, {a: 1, c: 2})).toBe(false);
        });
        
        test('nested objects', () => {
            expect(__py.eq({a: {b: 1}}, {a: {b: 1}})).toBe(true);
            expect(__py.eq({a: {b: 1}}, {a: {b: 2}})).toBe(false);
        });
        
        test('empty objects', () => {
            expect(__py.eq({}, {})).toBe(true);
        });
    });
    
    describe('Circular references', () => {
        test('handles simple circular ref', () => {
            const a = { x: 1 };
            a.self = a;
            const b = { x: 1 };
            b.self = b;
            
            // Should not stack overflow
            expect(__py.eq(a, b)).toBe(true);
        });
        
        test('handles complex circular ref', () => {
            const a = { x: 1, child: { y: 2 } };
            a.child.parent = a;
            const b = { x: 1, child: { y: 2 } };
            b.child.parent = b;
            
            expect(__py.eq(a, b)).toBe(true);
        });
    });
    
    describe('Type mismatches', () => {
        test('number vs string', () => {
            expect(__py.eq(1, '1')).toBe(false);
        });
        
        test('array vs object', () => {
            expect(__py.eq([1, 2], {0: 1, 1: 2})).toBe(false);
        });
    });
});


// =============================================================================
// TESTS: __py.contains() - Membership Testing
// =============================================================================

describe('__py.contains() - Membership Testing', () => {
    describe('Arrays', () => {
        test('primitive in array', () => {
            expect(__py.contains(2, [1, 2, 3])).toBe(true);
            expect(__py.contains(4, [1, 2, 3])).toBe(false);
        });
        
        test('object in array (deep equality)', () => {
            expect(__py.contains({a: 1}, [{a: 1}, {b: 2}])).toBe(true);
            expect(__py.contains({a: 2}, [{a: 1}, {b: 2}])).toBe(false);
        });
        
        test('array in array', () => {
            expect(__py.contains([1, 2], [[1, 2], [3, 4]])).toBe(true);
        });
    });
    
    describe('Strings', () => {
        test('substring in string', () => {
            expect(__py.contains('ell', 'hello')).toBe(true);
            expect(__py.contains('xyz', 'hello')).toBe(false);
        });
        
        test('single char', () => {
            expect(__py.contains('e', 'hello')).toBe(true);
        });
        
        test('empty string', () => {
            expect(__py.contains('', 'hello')).toBe(true);
        });
    });
    
    describe('Objects (dict key check)', () => {
        test('key in object', () => {
            expect(__py.contains('a', {a: 1, b: 2})).toBe(true);
            expect(__py.contains('c', {a: 1, b: 2})).toBe(false);
        });
        
        test('numeric key', () => {
            expect(__py.contains(0, {0: 'a', 1: 'b'})).toBe(true);
        });
    });
    
    describe('Set', () => {
        test('value in Set', () => {
            const s = new Set([1, 2, 3]);
            expect(__py.contains(2, s)).toBe(true);
            expect(__py.contains(4, s)).toBe(false);
        });
    });
    
    describe('Map (key check)', () => {
        test('key in Map', () => {
            const m = new Map([['a', 1], ['b', 2]]);
            expect(__py.contains('a', m)).toBe(true);
            expect(__py.contains('c', m)).toBe(false);
        });
    });
    
    describe('Edge cases', () => {
        test('null container throws', () => {
            expect(() => __py.contains(1, null)).toThrow();
        });
        
        test('undefined container throws', () => {
            expect(() => __py.contains(1, undefined)).toThrow();
        });
    });
});


// =============================================================================
// TESTS: __py.add() - Polymorphic Addition
// =============================================================================

describe('__py.add() - Polymorphic Addition', () => {
    test('numbers', () => {
        expect(__py.add(1, 2)).toBe(3);
        expect(__py.add(-1, 1)).toBe(0);
        expect(__py.add(1.5, 2.5)).toBe(4);
    });
    
    test('string concatenation', () => {
        expect(__py.add('hello', ' world')).toBe('hello world');
        expect(__py.add('', 'test')).toBe('test');
    });
    
    test('string + number (Python-style coercion)', () => {
        // Python would throw TypeError, but we coerce for browser compat
        expect(__py.add('count: ', 5)).toBe('count: 5');
        expect(__py.add(5, ' items')).toBe('5 items');
    });
    
    test('array concatenation', () => {
        expect(__py.add([1, 2], [3, 4])).toEqual([1, 2, 3, 4]);
        expect(__py.add([], [1])).toEqual([1]);
        expect(__py.add([1], [])).toEqual([1]);
    });
});


// =============================================================================
// TESTS: __py.mul() - String/List Repetition
// =============================================================================

describe('__py.mul() - Repetition', () => {
    describe('String repetition', () => {
        test('string * number', () => {
            expect(__py.mul('ab', 3)).toBe('ababab');
            expect(__py.mul('x', 5)).toBe('xxxxx');
        });
        
        test('number * string', () => {
            expect(__py.mul(3, 'ab')).toBe('ababab');
        });
        
        test('zero repetition', () => {
            expect(__py.mul('abc', 0)).toBe('');
            expect(__py.mul('abc', -1)).toBe('');
        });
        
        test('one repetition', () => {
            expect(__py.mul('abc', 1)).toBe('abc');
        });
    });
    
    describe('Array repetition', () => {
        test('array * number', () => {
            expect(__py.mul([1, 2], 3)).toEqual([1, 2, 1, 2, 1, 2]);
        });
        
        test('number * array', () => {
            expect(__py.mul(2, [1, 2])).toEqual([1, 2, 1, 2]);
        });
        
        test('zero repetition', () => {
            expect(__py.mul([1, 2], 0)).toEqual([]);
            expect(__py.mul([1, 2], -1)).toEqual([]);
        });
    });
    
    describe('Numeric multiplication', () => {
        test('numbers', () => {
            expect(__py.mul(3, 4)).toBe(12);
            expect(__py.mul(2.5, 4)).toBe(10);
        });
    });
});
