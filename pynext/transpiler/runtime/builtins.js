/**
 * PyNext Transpiler - Enhanced Python Builtins
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides enhanced Python builtin functions that require special handling.
 * These builtins have complex semantics that can't be directly mapped to JS.
 * 
 * =============================================================================
 * WHY THIS EXISTS
 * =============================================================================
 * 
 * Basic builtins like len(), str() map directly to JS. But these need runtime:
 * 
 * - sorted(key=, reverse=) - No JS equivalent with key function
 * - min/max(key=) - No JS equivalent with key function
 * - any/all() - Need Python truthiness semantics
 * - divmod() - Returns tuple, uses Python modulo
 * - filter(None, x) - Python filters falsy values
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * Python:
 *   sorted(items, key=len, reverse=True)
 *   min(items, key=lambda x: x.value)
 * 
 * Transpiled:
 *   __py.sorted(items, len, true)
 *   __py.min(items, x => x.value)
 */

import { bool, mod, floordiv, eq } from './core.js';
import { ValueError, PyTypeError as TypeError_ } from './errors.js';

// =============================================================================
// SORTED
// =============================================================================

/**
 * Return a new sorted list from iterable.
 * 
 * Python semantics:
 * - Strings sort lexicographically
 * - Numbers sort numerically
 * - Mixed types throw TypeError
 * - Sort is stable
 * 
 * @param {Iterable} iterable - Items to sort
 * @param {Function|null} key - Key function (applied to each element)
 * @param {boolean} reverse - Reverse order
 * @returns {Array} New sorted array
 * 
 * @example
 * sorted([3, 1, 2])                    // → [1, 2, 3]
 * sorted(['b', 'a', 'c'])              // → ['a', 'b', 'c']
 * sorted(['bb', 'a', 'ccc'], len)      // → ['a', 'bb', 'ccc']
 * sorted([3, 1, 2], null, true)        // → [3, 2, 1]
 */
export function sorted(iterable, key = null, reverse = false) {
    const arr = [...iterable];
    if (arr.length === 0) return arr;
    
    // Pre-compute keys and check types
    const keyed = arr.map((item, idx) => ({
        item,
        key: key ? key(item) : item,
        idx  // For stable sort
    }));
    
    // Check for mixed types (Python 3 throws TypeError)
    const firstType = typeof keyed[0].key;
    for (let i = 1; i < keyed.length; i++) {
        const t = typeof keyed[i].key;
        if (t !== firstType && keyed[i].key != null && keyed[0].key != null) {
            throw new TypeError_(`'<' not supported between instances of '${firstType}' and '${t}'`);
        }
    }
    
    keyed.sort((a, b) => {
        const keyA = a.key;
        const keyB = b.key;
        
        // Handle null/undefined
        if (keyA == null && keyB == null) return a.idx - b.idx;  // Stable
        if (keyA == null) return reverse ? -1 : 1;
        if (keyB == null) return reverse ? 1 : -1;
        
        let cmp;
        if (typeof keyA === 'number' && typeof keyB === 'number') {
            cmp = keyA - keyB;
        } else {
            // Lexicographic comparison (works for strings)
            if (keyA < keyB) cmp = -1;
            else if (keyA > keyB) cmp = 1;
            else cmp = 0;
        }
        
        // Apply reverse, then use index for stability
        if (cmp === 0) return a.idx - b.idx;
        return reverse ? -cmp : cmp;
    });
    
    return keyed.map(k => k.item);
}

// =============================================================================
// MIN / MAX
// =============================================================================

/**
 * Return the smallest item.
 * 
 * Called by emitter as:
 * - __py.min(iterable, key) - key can be null
 * - __py.min([a, b, c], key) - multiple args wrapped in array
 * 
 * @param {Iterable} iterable - Items to compare
 * @param {Function|null} key - Optional key function
 * @returns {*} Smallest item
 * @throws {Error} If empty sequence
 * @throws {TypeError} If mixed types without key
 * 
 * @example
 * min([3, 1, 2], null)               // → 1
 * min(['bb', 'a', 'ccc'], len)       // → 'a'
 * min([5, 2, 8], null)               // → 2
 */
export function min(iterable, key = null) {
    const arr = [...iterable];
    
    if (arr.length === 0) {
        throw new ValueError("min() arg is an empty sequence");
    }
    
    // Check for mixed types (Python 3 throws TypeError)
    if (key === null) {
        const firstType = typeof arr[0];
        for (let i = 1; i < arr.length; i++) {
            const t = typeof arr[i];
            if (t !== firstType && arr[i] != null && arr[0] != null) {
                throw new TypeError(`'<' not supported between instances of '${firstType}' and '${t}'`);
            }
        }
    }
    
    if (key) {
        return arr.reduce((a, b) => key(a) <= key(b) ? a : b);
    }
    return arr.reduce((a, b) => a <= b ? a : b);
}

/**
 * Return the largest item.
 * 
 * @param {Iterable} iterable - Items to compare
 * @param {Function|null} key - Optional key function
 * @returns {*} Largest item
 * @throws {Error} If empty sequence
 * @throws {TypeError} If mixed types without key
 * 
 * @example
 * max([3, 1, 2], null)               // → 3
 * max(['bb', 'a', 'ccc'], len)       // → 'ccc'
 * max([5, 2, 8], null)               // → 8
 */
export function max(iterable, key = null) {
    const arr = [...iterable];
    
    if (arr.length === 0) {
        throw new ValueError("max() arg is an empty sequence");
    }
    
    // Check for mixed types (Python 3 throws TypeError)
    if (key === null) {
        const firstType = typeof arr[0];
        for (let i = 1; i < arr.length; i++) {
            const t = typeof arr[i];
            if (t !== firstType && arr[i] != null && arr[0] != null) {
                throw new TypeError(`'<' not supported between instances of '${firstType}' and '${t}'`);
            }
        }
    }
    
    if (key) {
        return arr.reduce((a, b) => key(a) >= key(b) ? a : b);
    }
    return arr.reduce((a, b) => a >= b ? a : b);
}

// =============================================================================
// ANY / ALL
// =============================================================================

/**
 * Return True if any element of iterable is truthy.
 * 
 * Uses Python truthiness semantics ([], {}, 0, '', None are falsy).
 * 
 * @param {Iterable} iterable - Items to check
 * @returns {boolean}
 * 
 * @example
 * any([0, '', None])    // → false
 * any([0, 1, ''])       // → true
 * any([])               // → false
 */
export function any(iterable) {
    for (const x of iterable) {
        if (bool(x)) return true;
    }
    return false;
}

/**
 * Return True if all elements of iterable are truthy.
 * 
 * Uses Python truthiness semantics.
 * 
 * @param {Iterable} iterable - Items to check
 * @returns {boolean}
 * 
 * @example
 * all([1, 2, 3])        // → true
 * all([1, 0, 3])        // → false
 * all([])               // → true (vacuous truth)
 */
export function all(iterable) {
    for (const x of iterable) {
        if (!bool(x)) return false;
    }
    return true;
}

// =============================================================================
// DIVMOD / POW
// =============================================================================

/**
 * Return (a // b, a % b) with Python semantics.
 * 
 * @param {number} a - Dividend
 * @param {number} b - Divisor
 * @returns {[number, number]} [quotient, remainder]
 * 
 * @example
 * divmod(7, 3)      // → [2, 1]
 * divmod(-7, 3)     // → [-3, 2]  (Python semantics!)
 */
export function divmod(a, b) {
    return [floordiv(a, b), mod(a, b)];
}

/**
 * Return x**y, optionally modulo z.
 * 
 * Phase 33.2: Supports __pow__ dunder method for custom classes.
 * 
 * Three-argument pow(x, y, z) computes (x**y) % z efficiently.
 * 
 * @param {*} x - Base (number or object with __pow__ method)
 * @param {*} y - Exponent
 * @param {number|null} z - Optional modulus
 * @returns {number}
 * 
 * @example
 * pow(2, 10)        // → 1024
 * pow(2, 10, 1000)  // → 24
 * pow(MyVector(3, 4), 2)  // → calls MyVector.__pow__(2) if defined
 */
export function pow(x, y, z = null) {
    // Phase 33.2: Check for __pow__ dunder method (only for 2-arg case)
    if (z === null && typeof x === 'object' && x !== null && typeof x.__pow__ === 'function') {
        return x.__pow__(y);
    }
    
    if (z === null) {
        return Math.pow(x, y);
    }
    // Modular exponentiation
    // For large numbers, use binary exponentiation
    if (Number.isInteger(x) && Number.isInteger(y) && Number.isInteger(z)) {
        let result = 1;
        x = x % z;
        while (y > 0) {
            if (y % 2 === 1) {
                result = (result * x) % z;
            }
            y = Math.floor(y / 2);
            x = (x * x) % z;
        }
        return result;
    }
    return Math.pow(x, y) % z;
}

// =============================================================================
// CALLABLE / TYPE CHECKING
// =============================================================================

/**
 * Return True if object appears callable.
 * 
 * @param {*} obj - Object to check
 * @returns {boolean}
 * 
 * @example
 * callable(print)      // → true
 * callable(42)         // → false
 * callable([].append)  // → true
 */
export function callable(obj) {
    return typeof obj === 'function';
}

// =============================================================================
// FILTER (ENHANCED)
// =============================================================================

/**
 * Filter items from iterable.
 * 
 * If function is None/null/undefined, return items that are truthy.
 * Uses Python truthiness semantics ([], {}, 0, '' are falsy).
 * 
 * @param {Function|null} func - Filter function or None
 * @param {Iterable} iterable - Items to filter
 * @returns {Array} Filtered items
 * 
 * @example
 * filter(x => x > 0, [-1, 0, 1, 2])   // → [1, 2]
 * filter(null, [0, 1, '', 'a', []])   // → [1, 'a']
 */
export function filter(func, iterable) {
    const arr = [...iterable];
    // Handle None/null/undefined - use Python truthiness
    if (func == null) {
        return arr.filter(x => bool(x));
    }
    return arr.filter(func);
}

// =============================================================================
// MAP (ENHANCED)
// =============================================================================

/**
 * Apply function to every item of iterable(s).
 * 
 * With multiple iterables, function gets one arg from each.
 * Stops when shortest iterable is exhausted.
 * 
 * @param {Function} func - Function to apply
 * @param {...Iterable} iterables - One or more iterables
 * @returns {Array} Mapped items
 * 
 * @example
 * map(x => x * 2, [1, 2, 3])           // → [2, 4, 6]
 * map((a, b) => a + b, [1, 2], [10, 20]) // → [11, 22]
 */
export function map(func, ...iterables) {
    if (iterables.length === 1) {
        return [...iterables[0]].map(func);
    }
    
    // Multiple iterables - zip them
    const arrays = iterables.map(it => [...it]);
    const minLen = Math.min(...arrays.map(a => a.length));
    const result = [];
    
    for (let i = 0; i < minLen; i++) {
        result.push(func(...arrays.map(a => a[i])));
    }
    
    return result;
}

// =============================================================================
// REVERSED
// =============================================================================

/**
 * Return reversed iterator (as array).
 * 
 * @param {Iterable} iterable - Items to reverse
 * @returns {Array} Reversed array
 * 
 * @example
 * reversed([1, 2, 3])    // → [3, 2, 1]
 * reversed('abc')        // → ['c', 'b', 'a']
 */
export function reversed(iterable) {
    return [...iterable].reverse();
}

// =============================================================================
// ROUND (ENHANCED)
// =============================================================================

/**
 * Round a number to given precision using banker's rounding.
 * 
 * Python uses "round half to even" (banker's rounding):
 * - round(2.5) = 2 (not 3)
 * - round(3.5) = 4 (rounds to even)
 * 
 * This implementation handles floating point precision issues by:
 * 1. Using a relative epsilon based on the magnitude of the number
 * 2. Handling negative numbers correctly
 * 3. Properly detecting .5 cases even with floating point errors
 * 
 * @param {number} x - Number to round
 * @param {number} ndigits - Decimal places (default 0)
 * @returns {number}
 * 
 * @example
 * round(2.5)           // → 2 (banker's rounding)
 * round(3.5)           // → 4 (banker's rounding)
 * round(3.14159, 2)    // → 3.14
 * round(1234, -2)      // → 1200
 * round(-2.5)          // → -2 (banker's rounding)
 * round(-3.5)          // → -4 (banker's rounding)
 */
export function round(x, ndigits = 0) {
    if (!Number.isFinite(x)) return x;  // Handle Infinity, -Infinity, NaN
    
    const factor = Math.pow(10, ndigits);
    const scaled = x * factor;
    
    // For proper banker's rounding, we need to handle the .5 case carefully
    // Use a relative epsilon based on the scaled value's magnitude
    const epsilon = Math.max(1e-9, Math.abs(scaled) * 1e-14);
    
    // Get the integer part and fractional part
    const isNegative = scaled < 0;
    const absScaled = Math.abs(scaled);
    const floor = Math.floor(absScaled);
    const decimal = absScaled - floor;
    
    let result;
    
    // Check if we're at .5 (within floating point tolerance)
    if (Math.abs(decimal - 0.5) < epsilon) {
        // Banker's rounding: round .5 to nearest even
        if (floor % 2 === 0) {
            result = floor;
        } else {
            result = floor + 1;
        }
    } else if (decimal < 0.5) {
        result = floor;
    } else {
        result = floor + 1;
    }
    
    // Restore sign and scale back
    if (isNegative) result = -result;
    
    // Clean up floating point errors in the final result
    const finalResult = result / factor;
    
    // For integer results, ensure we return an integer
    if (ndigits <= 0) {
        return Math.round(finalResult);
    }
    
    return finalResult;
}

// =============================================================================
// ABS
// =============================================================================

/**
 * Return absolute value of a number.
 * 
 * Phase 33.2: Supports __abs__ dunder method for custom classes.
 * 
 * @param {*} x - Number or object with __abs__ method
 * @returns {number}
 * 
 * @example
 * abs(-5)              // → 5
 * abs(MyVector(3, 4))   // → calls MyVector.__abs__() if defined
 */
export function abs(x) {
    // Phase 33.2: Check for __abs__ dunder method
    if (typeof x === 'object' && x !== null && typeof x.__abs__ === 'function') {
        return x.__abs__();
    }
    // Fallback: Math.abs for numbers
    return Math.abs(x);
}

// =============================================================================
// LEN (ENHANCED - handles Map/Set)
// =============================================================================

/**
 * Return length of object.
 * 
 * @param {*} obj - Array, string, Map, Set, or object with length/size
 * @returns {number}
 * 
 * @example
 * len([1, 2, 3])       // → 3
 * len('hello')         // → 5
 * len(new Set([1,2]))  // → 2
 * len({a: 1, b: 2})    // → 2
 */
export function len(obj) {
    if (obj == null) {
        throw new TypeError_("object of type 'NoneType' has no len()");
    }
    // Phase 33.2: Check for __len__ dunder method (get length() getter)
    if (typeof obj === 'object' && typeof obj.length === 'number') {
        // Check if this is a getter (not a regular property)
        // If object has a get length() getter, use it
        const descriptor = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(obj) || obj, 'length');
        if (descriptor && typeof descriptor.get === 'function') {
            return obj.length;
        }
    }
    if (typeof obj === 'string' || Array.isArray(obj)) {
        return obj.length;
    }
    if (obj instanceof Map || obj instanceof Set) {
        return obj.size;
    }
    // Phase 33.2: Check for length getter (from __len__ dunder)
    if (typeof obj === 'object' && 'length' in obj && typeof obj.length === 'number') {
        return obj.length;
    }
    if (typeof obj === 'object') {
        return Object.keys(obj).length;
    }
    throw new TypeError_(`object of type '${typeof obj}' has no len()`);
}

// =============================================================================
// SUM (ENHANCED)
// =============================================================================

/**
 * Sum items in iterable with optional start value.
 * 
 * @param {Iterable} iterable - Items to sum
 * @param {number} start - Starting value (default 0)
 * @returns {number}
 * 
 * @example
 * sum([1, 2, 3])          // → 6
 * sum([1, 2, 3], 10)      // → 16
 */
export function sum(iterable, start = 0) {
    let total = start;
    for (const x of iterable) {
        total += x;
    }
    return total;
}

// =============================================================================
// INPUT
// =============================================================================

/**
 * Read a line of input (uses prompt() in browser).
 * 
 * @param {string} prompt - Prompt message
 * @returns {string|null}
 */
export function input(prompt = '') {
    return globalThis.prompt?.(prompt) ?? null;
}

// =============================================================================
// PRINT
// =============================================================================

/**
 * Print values to console.
 * 
 * @param {...*} args - Values to print
 * @param {string} sep - Separator (default ' ')
 * @param {string} end - End string (default '\n', ignored in console.log)
 */
export function print(...args) {
    // Check for sep/end kwargs at end
    let sep = ' ';
    let end = '\n';
    
    if (args.length > 0 && typeof args[args.length - 1] === 'object' && args[args.length - 1] !== null) {
        const kwargs = args[args.length - 1];
        if ('sep' in kwargs || 'end' in kwargs) {
            args.pop();
            if ('sep' in kwargs) sep = kwargs.sep;
            if ('end' in kwargs) end = kwargs.end;
        }
    }
    
    console.log(args.join(sep));
}

// =============================================================================
// ZIP (ENHANCED)
// =============================================================================

/**
 * Zip iterables together.
 * 
 * @param {...Iterable} iterables - Iterables to zip
 * @returns {Array<Array>} Array of tuples
 * 
 * @example
 * zip([1, 2], ['a', 'b'])  // → [[1, 'a'], [2, 'b']]
 */
export function zip(...iterables) {
    if (iterables.length === 0) return [];
    
    const arrays = iterables.map(it => [...it]);
    const minLen = Math.min(...arrays.map(a => a.length));
    const result = [];
    
    for (let i = 0; i < minLen; i++) {
        result.push(arrays.map(a => a[i]));
    }
    
    return result;
}

// =============================================================================
// ENUMERATE (ENHANCED)
// =============================================================================

/**
 * Enumerate iterable with index.
 * 
 * @param {Iterable} iterable - Items to enumerate
 * @param {number} start - Starting index (default 0)
 * @returns {Array<[number, *]>} Array of [index, value] pairs
 * 
 * @example
 * enumerate(['a', 'b', 'c'])     // → [[0, 'a'], [1, 'b'], [2, 'c']]
 * enumerate(['a', 'b'], 1)       // → [[1, 'a'], [2, 'b']]
 */
export function enumerate(iterable, start = 0) {
    return [...iterable].map((v, i) => [i + start, v]);
}

// =============================================================================
// RANGE (ENHANCED)
// =============================================================================

/**
 * Generate a range of numbers.
 * 
 * @param {number} start - Start (or stop if only arg)
 * @param {number|null} stop - Stop value
 * @param {number} step - Step value
 * @returns {Array<number>}
 * 
 * @example
 * range(5)          // → [0, 1, 2, 3, 4]
 * range(1, 5)       // → [1, 2, 3, 4]
 * range(0, 10, 2)   // → [0, 2, 4, 6, 8]
 */
export function range(start, stop = null, step = 1) {
    if (stop === null) {
        stop = start;
        start = 0;
    }
    
    if (step === 0) {
        throw new ValueError("range() step argument must not be zero");
    }
    
    const result = [];
    if (step > 0) {
        for (let i = start; i < stop; i += step) {
            result.push(i);
        }
    } else {
        for (let i = start; i > stop; i += step) {
            result.push(i);
        }
    }
    
    return result;
}

// =============================================================================
// EXPORTS
// =============================================================================

export default {
    sorted,
    min,
    max,
    any,
    all,
    divmod,
    pow,
    callable,
    filter,
    map,
    reversed,
    round,
    abs,
    len,
    sum,
    input,
    print,
    zip,
    enumerate,
    range
};
