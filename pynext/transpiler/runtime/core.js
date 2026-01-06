/**
 * PyNext Transpiler - Python Runtime for JavaScript
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides JavaScript functions that implement Python semantics in the browser.
 * Used by transpiled code to handle cases where Python and JavaScript differ.
 * 
 * =============================================================================
 * WHY THIS EXISTS (Problem It Solves)
 * =============================================================================
 * 
 * Python and JavaScript have subtle differences that break code if ignored:
 * 
 * 1. Truthiness:  Python [] is falsy, JS [] is truthy
 * 2. Modulo:      Python -1 % 3 = 2, JS -1 % 3 = -1
 * 3. Floor div:   Python 7 // 3 = 2, JS has no equivalent
 * 4. Equality:    Python [1,2] == [1,2] is True, JS is false
 * 5. Indexing:    Python items[-1] works, JS returns undefined
 * 6. Slicing:     Python items[1:3] works, JS has no equivalent
 * 
 * This runtime provides helper functions that make JS behave like Python.
 * 
 * =============================================================================
 * SIZE BUDGET
 * =============================================================================
 * 
 * Target: < 500 bytes gzipped
 * 
 * Only essential functions are included. Tree-shaking removes unused code.
 * Each function is designed to be as small as possible.
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * The transpiler emits calls to these functions:
 * 
 *   items[-1]     → __py.at(items, -1)
 *   items[1:3]    → __py.slice(items, 1, 3)
 *   not items     → !__py.bool(items)
 *   a == b        → __py.eq(a, b)
 *   x % y         → __py.mod(x, y)
 *   x // y        → __py.floordiv(x, y)
 */

import {
    ValueError,
    KeyError,
    IndexError,
    ZeroDivisionError,
    PyTypeError as TypeError_,
} from './errors.js';

// =============================================================================
// INDEXING
// =============================================================================

/**
 * Python negative indexing: items[-1] returns last element
 * 
 * @param {Array|string} arr - Array or string to index
 * @param {number} i - Index (can be negative)
 * @returns {*} Element at index
 * 
 * @example
 * at([1, 2, 3], -1)  // → 3
 * at("hello", -2)    // → "l"
 */
export function at(arr, i) {
    if (i < 0) return arr[arr.length + i];
    return arr[i];
}

/**
 * Python slicing: items[start:stop:step]
 * 
 * Handles:
 * - Negative indices
 * - Omitted start/stop (null)
 * - Negative step (reverse)
 * 
 * @param {Array|string} arr - Array or string to slice
 * @param {number|null} start - Start index
 * @param {number|null} stop - Stop index (exclusive)
 * @param {number} step - Step value (default 1)
 * @returns {Array|string} Sliced result
 * 
 * @example
 * slice([0,1,2,3,4], 1, 3)      // → [1, 2]
 * slice([0,1,2,3,4], null, -1)  // → [0, 1, 2, 3]
 * slice([0,1,2,3,4], null, null, -1) // → [4, 3, 2, 1, 0]
 */
export function slice(arr, start, stop, step = 1) {
    const len = arr.length;
    const isString = typeof arr === 'string';
    
    // Normalize indices
    if (step === 0) throw new Error("slice step cannot be zero");
    
    if (step > 0) {
        // Forward slice
        start = start === null ? 0 : (start < 0 ? Math.max(0, len + start) : Math.min(len, start));
        stop = stop === null ? len : (stop < 0 ? Math.max(0, len + stop) : Math.min(len, stop));
        
        const result = [];
        for (let i = start; i < stop; i += step) {
            result.push(arr[i]);
        }
        return isString ? result.join('') : result;
    } else {
        // Reverse slice
        start = start === null ? len - 1 : (start < 0 ? Math.max(-1, len + start) : Math.min(len - 1, start));
        stop = stop === null ? -1 : (stop < 0 ? Math.max(-1, len + stop) : Math.min(len - 1, stop));
        
        const result = [];
        for (let i = start; i > stop; i += step) {
            if (i >= 0 && i < len) result.push(arr[i]);
        }
        return isString ? result.join('') : result;
    }
}

// =============================================================================
// TRUTHINESS
// =============================================================================

/**
 * Python truthiness check
 * 
 * Python falsy: None, False, 0, 0.0, "", [], {}, set()
 * JS falsy:     null, undefined, false, 0, 0n, "", NaN
 * 
 * Key difference: [] and {} are truthy in JS but falsy in Python
 * 
 * @param {*} x - Value to check
 * @returns {boolean} Python truthiness
 * 
 * @example
 * bool([])    // → false (Python: [] is falsy)
 * bool({})    // → false (Python: {} is falsy)
 * bool([1])   // → true
 */
export function bool(x) {
    if (x === null || x === undefined) return false;
    if (x === false || x === 0 || x === '') return false;
    if (Array.isArray(x)) return x.length > 0;
    if (typeof x === 'object') {
        if (x.constructor === Object) return Object.keys(x).length > 0;
        if (x instanceof Set || x instanceof Map) return x.size > 0;
    }
    return true;
}

// =============================================================================
// ARITHMETIC
// =============================================================================

/**
 * Python modulo: always returns result with same sign as divisor
 * 
 * JS: -1 % 3 = -1
 * Py: -1 % 3 = 2
 * 
 * Throws ZeroDivisionError for modulo by zero (Python behavior).
 * 
 * @param {number} a - Dividend
 * @param {number} b - Divisor
 * @returns {number} Python-style modulo
 * @throws {Error} If b is zero
 */
export function mod(a, b) {
    if (b === 0) {
        throw new ZeroDivisionError("integer division or modulo by zero");
    }
    const result = ((a % b) + b) % b;
    // Normalize -0 to 0
    return result === 0 ? 0 : result;
}

/**
 * Python floor division: rounds toward negative infinity
 * 
 * Throws ZeroDivisionError for division by zero (Python behavior).
 * 
 * @param {number} a - Dividend
 * @param {number} b - Divisor
 * @returns {number} Floor division result
 * @throws {Error} If b is zero
 */
export function floordiv(a, b) {
    if (b === 0) {
        throw new ZeroDivisionError("integer division or modulo by zero");
    }
    return Math.floor(a / b);
}

/**
 * Python true division with zero-check
 * 
 * By default, JavaScript returns Infinity for division by zero.
 * This function can optionally throw like Python.
 * 
 * @param {number} a - Dividend
 * @param {number} b - Divisor
 * @param {boolean} strict - If true, throw on zero (default: false for browser compat)
 * @returns {number} Division result
 * @throws {Error} If b is zero and strict is true
 */
export function div(a, b, strict = false) {
    if (b === 0 && strict) {
        throw new ZeroDivisionError("division by zero");
    }
    return a / b;
}

// =============================================================================
// EQUALITY
// =============================================================================

/**
 * Python equality: deep comparison for collections
 * 
 * JS: [1,2] === [1,2] is false (reference equality)
 * Py: [1,2] == [1,2] is True (value equality)
 * 
 * Includes cycle detection to prevent stack overflow on circular references.
 * 
 * @param {*} a - First value
 * @param {*} b - Second value
 * @param {WeakMap} seenA - Tracking map for a's visited objects (internal)
 * @param {WeakMap} seenB - Tracking map for b's visited objects (internal)
 * @returns {boolean} Python equality
 */
export function eq(a, b, seenA = null, seenB = null) {
    // Same reference or primitives
    if (a === b) return true;
    
    // Null/undefined
    if (a === null || b === null) return a === b;
    if (a === undefined || b === undefined) return a === b;
    
    // Different types
    if (typeof a !== typeof b) return false;
    
    // For objects, check for circular references
    if (typeof a === 'object') {
        // Initialize seen maps on first object comparison
        if (seenA === null) {
            seenA = new WeakMap();
            seenB = new WeakMap();
        }
        
        // Check for cycles: if we've seen this pair before with matching partners
        if (seenA.has(a)) {
            // If a was paired with b before, they're equal in this cycle
            return seenA.get(a) === b && seenB.get(b) === a;
        }
        if (seenB.has(b)) {
            return seenB.get(b) === a && seenA.get(a) === b;
        }
        
        // Mark as seen before recursing
        seenA.set(a, b);
        seenB.set(b, a);
    }
    
    // Arrays
    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) return false;
        for (let i = 0; i < a.length; i++) {
            if (!eq(a[i], b[i], seenA, seenB)) return false;
        }
        return true;
    }
    
    // Sets
    if (a instanceof Set && b instanceof Set) {
        if (a.size !== b.size) return false;
        for (const item of a) {
            // For sets, we need to check if an equivalent item exists
            let found = false;
            for (const bItem of b) {
                if (eq(item, bItem, seenA, seenB)) {
                    found = true;
                    break;
                }
            }
            if (!found) return false;
        }
        return true;
    }
    
    // Maps
    if (a instanceof Map && b instanceof Map) {
        if (a.size !== b.size) return false;
        for (const [key, value] of a) {
            if (!b.has(key)) return false;
            if (!eq(value, b.get(key), seenA, seenB)) return false;
        }
        return true;
    }
    
    // Plain objects (dicts)
    if (typeof a === 'object' && a.constructor === Object && b.constructor === Object) {
        const keysA = Object.keys(a);
        const keysB = Object.keys(b);
        if (keysA.length !== keysB.length) return false;
        for (const key of keysA) {
            if (!(key in b)) return false;
            if (!eq(a[key], b[key], seenA, seenB)) return false;
        }
        return true;
    }
    
    return false;
}

// =============================================================================
// MEMBERSHIP
// =============================================================================

/**
 * Python 'in' operator
 * 
 * Works for:
 * - Arrays: x in [1,2,3]
 * - Strings: "a" in "abc"
 * - Objects: "key" in {"key": 1}
 * 
 * @param {*} item - Item to find
 * @param {*} container - Container to search
 * @returns {boolean} Whether item is in container
 */
export function contains(item, container) {
    if (typeof container === 'string') {
        return container.includes(item);
    }
    if (Array.isArray(container)) {
        return container.some(x => eq(x, item));
    }
    if (typeof container === 'object' && container !== null) {
        return item in container;
    }
    return false;
}

// Alias for 'in' keyword
export { contains as in_ };

// =============================================================================
// ITERATION HELPERS
// =============================================================================

/**
 * Python enumerate()
 * 
 * @param {Iterable} iterable - Iterable to enumerate
 * @param {number} start - Starting index (default 0)
 * @returns {Array} Array of [index, value] pairs
 */
export function enumerate(iterable, start = 0) {
    const arr = Array.from(iterable);
    return arr.map((item, i) => [start + i, item]);
}

/**
 * Python zip()
 * 
 * @param {...Iterable} iterables - Iterables to zip
 * @returns {Array} Array of tuples
 */
export function zip(...iterables) {
    const arrays = iterables.map(it => Array.from(it));
    const minLen = Math.min(...arrays.map(a => a.length));
    const result = [];
    for (let i = 0; i < minLen; i++) {
        result.push(arrays.map(a => a[i]));
    }
    return result;
}

/**
 * Python range()
 * 
 * @param {number} start - Start value
 * @param {number} stop - Stop value
 * @param {number} step - Step value
 * @returns {Array} Array of numbers
 */
export function range(start, stop, step = 1) {
    if (stop === undefined) {
        stop = start;
        start = 0;
    }
    const result = [];
    if (step > 0) {
        for (let i = start; i < stop; i += step) result.push(i);
    } else {
        for (let i = start; i > stop; i += step) result.push(i);
    }
    return result;
}

/**
 * Python sum()
 * 
 * @param {Iterable} iterable - Iterable to sum
 * @returns {number} Sum
 */
export function sum(iterable) {
    return Array.from(iterable).reduce((a, b) => a + b, 0);
}

// =============================================================================
// DELETE HELPERS
// =============================================================================

/**
 * Python del for indexable
 * 
 * @param {Array|Object} obj - Object to delete from
 * @param {*} key - Key/index to delete
 */
export function del(obj, key) {
    if (Array.isArray(obj)) {
        // Negative index support
        const idx = key < 0 ? obj.length + key : key;
        obj.splice(idx, 1);
    } else {
        delete obj[key];
    }
}

/**
 * Python del for slice
 * 
 * @param {Array} arr - Array to delete from
 * @param {Array} sliceArgs - [start, stop, step]
 */
export function del_slice(arr, sliceArgs) {
    const [start, stop] = sliceArgs;
    const s = start === null ? 0 : (start < 0 ? arr.length + start : start);
    const e = stop === null ? arr.length : (stop < 0 ? arr.length + stop : stop);
    arr.splice(s, e - s);
}

// =============================================================================
// STRING HELPERS
// =============================================================================

/**
 * Python str.count()
 * 
 * @param {string} str - String to search
 * @param {string} sub - Substring to count
 * @returns {number} Count of occurrences
 */
export function str_count(str, sub) {
    if (sub.length === 0) return str.length + 1;
    let count = 0;
    let pos = 0;
    while ((pos = str.indexOf(sub, pos)) !== -1) {
        count++;
        pos += sub.length;
    }
    return count;
}

/**
 * Python str.format() (basic)
 * 
 * @param {string} template - Format string
 * @param {...*} args - Arguments
 * @returns {string} Formatted string
 */
export function format(value, spec) {
    /**
     * Python-style format specification
     * 
     * Spec syntax: [[fill]align][sign][#][0][width][,][.precision][type]
     * 
     * Examples:
     *   format(3.14159, '.2f')  → "3.14"
     *   format(1234, ',')       → "1,234"
     *   format('hi', '>10')     → "        hi"
     *   format('hi', '<10')     → "hi        "
     *   format(5, '05d')        → "00005"
     *   format(0.25, '.1%')     → "25.0%"
     */
    if (!spec) return String(value);
    
    // Parse the format spec
    // [[fill]align][sign][#][0][width][,][.precision][type]
    const match = spec.match(/^([^<>=^])?([<>=^])?([+\- ])?([#])?(0)?(\d+)?([,])?(?:\.(\d+))?([bcdeEfFgGnosxX%])?$/);
    
    if (!match) {
        // Fallback for simple cases
        if (spec === ',') return Number(value).toLocaleString();
        if (spec.startsWith('.') && spec.endsWith('f')) {
            const precision = parseInt(spec.slice(1, -1));
            return Number(value).toFixed(precision);
        }
        if (spec.startsWith('>')) {
            const width = parseInt(spec.slice(1));
            return String(value).padStart(width);
        }
        if (spec.startsWith('<')) {
            const width = parseInt(spec.slice(1));
            return String(value).padEnd(width);
        }
        return String(value);
    }
    
    let [, fill, align, sign, alt, zero, width, comma, precision, type] = match;
    
    fill = fill || (zero ? '0' : ' ');
    align = align || (zero ? '=' : '>');
    width = width ? parseInt(width) : 0;
    precision = precision !== undefined ? parseInt(precision) : undefined;
    
    let result;
    
    // Handle type
    switch (type) {
        case 'f':
        case 'F':
            result = precision !== undefined ? Number(value).toFixed(precision) : String(value);
            break;
        case 'e':
            result = precision !== undefined ? Number(value).toExponential(precision) : Number(value).toExponential();
            break;
        case 'E':
            result = (precision !== undefined ? Number(value).toExponential(precision) : Number(value).toExponential()).toUpperCase();
            break;
        case '%':
            result = (Number(value) * 100).toFixed(precision !== undefined ? precision : 6) + '%';
            break;
        case 'd':
            result = Math.floor(Number(value)).toString();
            break;
        case 'x':
            result = Math.floor(Number(value)).toString(16);
            break;
        case 'X':
            result = Math.floor(Number(value)).toString(16).toUpperCase();
            break;
        case 'b':
            result = Math.floor(Number(value)).toString(2);
            break;
        case 'o':
            result = Math.floor(Number(value)).toString(8);
            break;
        default:
            result = String(value);
            if (precision !== undefined && typeof value === 'number') {
                result = Number(value).toFixed(precision);
            }
    }
    
    // Add thousands separator
    if (comma && typeof value === 'number') {
        const parts = result.split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        result = parts.join('.');
    }
    
    // Handle sign
    if (sign === '+' && Number(value) >= 0 && !result.startsWith('-')) {
        result = '+' + result;
    } else if (sign === ' ' && Number(value) >= 0 && !result.startsWith('-')) {
        result = ' ' + result;
    }
    
    // Handle width and alignment
    if (result.length < width) {
        const padding = fill.repeat(width - result.length);
        switch (align) {
            case '<':
                result = result + padding;
                break;
            case '>':
                result = padding + result;
                break;
            case '^':
                const left = Math.floor((width - result.length) / 2);
                const right = width - result.length - left;
                result = fill.repeat(left) + result + fill.repeat(right);
                break;
            case '=':
                // Pad after sign
                if (result.startsWith('-') || result.startsWith('+') || result.startsWith(' ')) {
                    result = result[0] + padding + result.slice(1);
                } else {
                    result = padding + result;
                }
                break;
        }
    }
    
    return result;
}

// =============================================================================
// LIST HELPERS
// =============================================================================

/**
 * Python list.remove() - removes first occurrence
 * 
 * @param {Array} arr - Array to modify
 * @param {*} item - Item to remove
 */
export function list_remove(arr, item) {
    const idx = arr.findIndex(x => eq(x, item));
    if (idx !== -1) arr.splice(idx, 1);
    else throw new ValueError("list.remove(x): x not in list");
}

// =============================================================================
// DICT HELPERS
// =============================================================================

/**
 * Python dict.pop()
 * 
 * @param {Object} obj - Dict to pop from
 * @param {string} key - Key to pop
 * @param {*} default_ - Default if key missing
 * @returns {*} Value
 */
export function dict_pop(obj, key, default_ = undefined) {
    if (key in obj) {
        const val = obj[key];
        delete obj[key];
        return val;
    }
    if (default_ !== undefined) return default_;
    throw new KeyError(key);
}

/**
 * Python dict.setdefault()
 * 
 * @param {Object} obj - Dict
 * @param {string} key - Key
 * @param {*} default_ - Default value
 * @returns {*} Value
 */
export function dict_setdefault(obj, key, default_ = null) {
    if (!(key in obj)) obj[key] = default_;
    return obj[key];
}

// =============================================================================
// TYPE HELPERS
// =============================================================================

/**
 * Python isinstance() - basic type checking
 * 
 * @param {*} obj - Object to check
 * @param {*} types - Type or tuple of types
 * @returns {boolean} Whether obj is instance
 */
export function isinstance(obj, types) {
    const typeArray = Array.isArray(types) ? types : [types];
    for (const t of typeArray) {
        if (t === 'str' || t === String) {
            if (typeof obj === 'string') return true;
        } else if (t === 'int' || t === Number) {
            if (typeof obj === 'number' && Number.isInteger(obj)) return true;
        } else if (t === 'float' || t === Number) {
            if (typeof obj === 'number') return true;
        } else if (t === 'bool' || t === Boolean) {
            if (typeof obj === 'boolean') return true;
        } else if (t === 'list' || t === Array) {
            if (Array.isArray(obj)) return true;
        } else if (t === 'dict' || t === Object) {
            if (typeof obj === 'object' && obj !== null && obj.constructor === Object) return true;
        } else if (typeof t === 'function') {
            if (obj instanceof t) return true;
        }
    }
    return false;
}

/**
 * Python type()
 * 
 * @param {*} obj - Object to get type of
 * @returns {string} Type name
 */
export function type(obj) {
    if (obj === null) return 'NoneType';
    if (Array.isArray(obj)) return 'list';
    if (typeof obj === 'string') return 'str';
    if (typeof obj === 'number') return Number.isInteger(obj) ? 'int' : 'float';
    if (typeof obj === 'boolean') return 'bool';
    if (typeof obj === 'object' && obj.constructor === Object) return 'dict';
    return typeof obj;
}

// =============================================================================
// ITERATION HELPERS
// =============================================================================

/**
 * Python-style iteration over any object
 * 
 * Handles:
 * - Arrays: iterate as-is
 * - Strings: iterate characters
 * - Objects/dicts: iterate over keys
 * - Iterables: use Symbol.iterator
 * 
 * @param {*} obj - Object to iterate
 * @returns {Iterable} Iterable for use in for-of
 */
export function iter(obj) {
    if (obj === null || obj === undefined) return [];
    if (Array.isArray(obj)) return obj;
    if (typeof obj === 'string') return obj;
    if (typeof obj[Symbol.iterator] === 'function') return obj;
    // Plain object - iterate keys (Python dict behavior)
    if (typeof obj === 'object' && obj.constructor === Object) {
        return Object.keys(obj);
    }
    return [obj];
}

// =============================================================================
// POLYMORPHIC OPERATORS
// =============================================================================

/**
 * Python-style addition
 * 
 * Handles:
 * - Numbers: regular addition
 * - Strings: concatenation
 * - Lists: concatenation
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result
 */
export function add(a, b) {
    // List concatenation
    if (Array.isArray(a) && Array.isArray(b)) {
        return [...a, ...b];
    }
    // Default to JS addition (works for numbers, strings)
    return a + b;
}

/**
 * Python-style multiplication
 * 
 * Handles:
 * - Numbers: regular multiplication
 * - String * int: repetition
 * - List * int: repetition
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result
 */
export function mul(a, b) {
    // String repetition
    if (typeof a === 'string' && typeof b === 'number') {
        return a.repeat(b);
    }
    if (typeof b === 'string' && typeof a === 'number') {
        return b.repeat(a);
    }
    // List repetition
    if (Array.isArray(a) && typeof b === 'number') {
        const result = [];
        for (let i = 0; i < b; i++) result.push(...a);
        return result;
    }
    if (Array.isArray(b) && typeof a === 'number') {
        const result = [];
        for (let i = 0; i < a; i++) result.push(...b);
        return result;
    }
    // Default to JS multiplication
    return a * b;
}

// =============================================================================
// REPR AND ASCII (for f-string conversions)
// =============================================================================

/**
 * Python repr() - returns a string representation for debugging
 * 
 * @param {*} obj - Object to represent
 * @returns {string} String representation
 * 
 * @example
 * repr("hello")  // → "'hello'"
 * repr([1, 2])   // → "[1, 2]"
 */
export function repr(obj) {
    if (obj === null) return 'None';
    if (obj === undefined) return 'None';
    if (typeof obj === 'string') return `'${obj.replace(/'/g, "\\'")}'`;
    if (typeof obj === 'boolean') return obj ? 'True' : 'False';
    if (Array.isArray(obj)) {
        return '[' + obj.map(repr).join(', ') + ']';
    }
    if (typeof obj === 'object' && obj.constructor === Object) {
        const pairs = Object.entries(obj).map(([k, v]) => `'${k}': ${repr(v)}`);
        return '{' + pairs.join(', ') + '}';
    }
    return String(obj);
}

/**
 * Python ascii() - like repr() but escapes non-ASCII characters
 * 
 * @param {*} obj - Object to represent
 * @returns {string} ASCII-safe string representation
 * 
 * @example
 * ascii("héllo")  // → "'h\\xe9llo'"
 */
export function ascii(obj) {
    const r = repr(obj);
    // Escape non-ASCII characters
    return r.replace(/[^\x00-\x7F]/g, (char) => {
        const code = char.charCodeAt(0);
        if (code < 256) {
            return '\\x' + code.toString(16).padStart(2, '0');
        }
        return '\\u' + code.toString(16).padStart(4, '0');
    });
}

// =============================================================================
// IMPORT SYSTEM (Phase 33.3)
// =============================================================================

/**
 * Copy all enumerable properties from a module object to the current scope.
 * 
 * WHAT: Implements Python's `from module import *` for built-in modules.
 * WHY: Built-in modules are objects in __py.* namespace, not ES6 modules.
 *       Star imports need to copy properties to the current scope.
 * HOW: Iterates over all enumerable properties and adds them to the target scope.
 * WHO: Used by emitter for star imports from built-in modules.
 * WHEN: When transpiling `from json import *` or similar.
 * WHERE: Runtime helper for import system.
 * 
 * Phase 33.3: Star imports from built-in modules.
 * 
 * @param {Object} moduleObj - The module object (e.g., __py.json)
 * @param {Object} scope - The scope object to add properties to (default: globalThis)
 * 
 * @example
 * // Python: from json import *
 * // JavaScript:
 * __py.star_import(__py.json, globalThis);
 * // Now loads, dumps, etc. are available in global scope
 * 
 * // Usage:
 * const data = loads('{"key": "value"}');  // loads is now available
 */
export function star_import(moduleObj, scope = null) {
    if (!moduleObj || typeof moduleObj !== 'object') {
        return;
    }
    
    // Determine target scope
    // In Node.js: use globalThis
    // In browser: use window (if available) or globalThis
    const targetScope = scope || (typeof globalThis !== 'undefined' ? globalThis : 
                                  typeof window !== 'undefined' ? window : 
                                  typeof global !== 'undefined' ? global : {});
    
    // Get all enumerable property names
    const keys = Object.keys(moduleObj);
    
    // Copy each property to the scope
    for (const key of keys) {
        // Skip private properties (starting with _) unless they're special
        // Python's import * typically skips names starting with _
        // But we allow __all__, __name__, __file__, etc.
        if (key.startsWith('_') && 
            key !== '__all__' && 
            key !== '__name__' && 
            key !== '__file__' && 
            key !== '__doc__' &&
            key !== '__version__') {
            continue;
        }
        
        // Skip if property already exists in scope (don't overwrite)
        if (key in targetScope && targetScope[key] !== undefined) {
            continue;
        }
        
        // Define property in scope
        try {
            // Try to use defineProperty for better control
            Object.defineProperty(targetScope, key, {
                value: moduleObj[key],
                writable: true,
                enumerable: true,
                configurable: true
            });
        } catch (e) {
            // If defineProperty fails (e.g., in strict mode), try direct assignment
            try {
                targetScope[key] = moduleObj[key];
            } catch (e2) {
                // Silently skip if we can't add to scope
                // This can happen in strict mode or with non-configurable properties
            }
        }
    }
}

/**
 * Copy properties from ES6 module namespace to current scope.
 * 
 * WHAT: Implements Python's `from module import *` for regular ES6 modules.
 * WHY: ES6 namespace imports create a namespace object, but Python star imports
 *      copy properties to the current scope.
 * HOW: Checks for __all__ in namespace, then copies properties accordingly.
 * WHO: Used by emitter for star imports from regular modules.
 * WHEN: When transpiling `from my_module import *`.
 * WHERE: Runtime helper for import system.
 * 
 * Phase 33.3: Star imports from regular modules.
 * 
 * @param {Object} namespace - The ES6 namespace object (from `import * as _module`)
 * @param {Object} scope - The scope object to add properties to (default: globalThis)
 * @param {Array<string>|null} __all__ - Optional __all__ list from module
 * 
 * @example
 * // Python: from my_module import *
 * // JavaScript:
 * import * as _my_module from './my_module.js';
 * __py.star_import_esm(_my_module, globalThis, _my_module.__all__);
 * // Now x, y are available in global scope (if in __all__)
 */
export function star_import_esm(namespace, scope = null, __all__ = null) {
    if (!namespace || typeof namespace !== 'object') {
        return;
    }
    
    // Determine target scope
    const targetScope = scope || (typeof globalThis !== 'undefined' ? globalThis : 
                                  typeof window !== 'undefined' ? window : 
                                  typeof global !== 'undefined' ? global : {});
    
    // Get __all__ from namespace if not provided
    const allList = __all__ || namespace.__all__;
    
    let keys;
    if (allList && Array.isArray(allList)) {
        // Use __all__ if defined
        keys = allList;
    } else {
        // No __all__: copy all non-private enumerable properties
        keys = Object.keys(namespace);
    }
    
    // Copy each property to the scope
    for (const key of keys) {
        // Skip if not in namespace
        if (!(key in namespace)) {
            continue;
        }
        
        // Skip private properties (starting with _) unless in __all__
        // Python's import * skips names starting with _ unless explicitly in __all__
        if (!allList && key.startsWith('_') && 
            key !== '__all__' && 
            key !== '__name__' && 
            key !== '__file__' && 
            key !== '__doc__' &&
            key !== '__version__') {
            continue;
        }
        
        // Skip if property already exists in scope (don't overwrite)
        if (key in targetScope && targetScope[key] !== undefined) {
            continue;
        }
        
        // Define property in scope
        try {
            Object.defineProperty(targetScope, key, {
                value: namespace[key],
                writable: true,
                enumerable: true,
                configurable: true
            });
        } catch (e) {
            // Fallback to direct assignment
            try {
                targetScope[key] = namespace[key];
            } catch (e2) {
                // Silently skip if we can't add to scope
            }
        }
    }
}

// =============================================================================
// TYPE METHODS (Phase 18.3)
// =============================================================================

import strMethods from './types/string.js';
import listMethods from './types/list.js';
import dictMethods from './types/dict.js';
import setMethods from './types/set.js';

// =============================================================================
// ENHANCED BUILTINS (Phase 18.4)
// =============================================================================

import * as builtins from './builtins.js';

// =============================================================================
// STANDARD LIBRARY (Phase 18.4)
// =============================================================================

import * as json from './stdlib/json.js';
import * as math from './stdlib/math.js';
import * as re from './stdlib/re.js';
import * as random from './stdlib/random.js';

// =============================================================================
// DECORATORS (Phase 18.5)
// =============================================================================

import * as decorators from './decorators.js';

// =============================================================================
// DUNDER METHODS (Phase 33.3: Operator Overloading)
// =============================================================================

import * as dunders from './dunders.js';

// =============================================================================
// EXPORT DEFAULT OBJECT
// =============================================================================

/**
 * Default export as __py namespace
 * 
 * Usage in transpiled code:
 *   import __py from 'pynext/runtime';
 *   __py.at(arr, -1)
 *   __py.str.split(s)
 *   __py.list.remove(items, x)
 *   __py.sorted(items, key, reverse)
 *   __py.json.loads(s)
 */
const __py = {
    at,
    slice,
    bool,
    mod,
    floordiv,
    div,
    eq,
    in: contains,
    iter,
    add,
    mul,
    enumerate,
    zip,
    range,
    sum,
    del,
    del_slice,
    str_count,
    format,
    list_remove,
    dict_pop,
    dict_setdefault,
    isinstance,
    type,
    repr,
    ascii,
    star_import,
    // Type methods (Phase 18.3)
    str: strMethods,
    list: listMethods,
    dict: dictMethods,
    set: setMethods,
    // Enhanced builtins (Phase 18.4)
    sorted: builtins.sorted,
    min: builtins.min,
    max: builtins.max,
    any: builtins.any,
    all: builtins.all,
    divmod: builtins.divmod,
    pow: builtins.pow,
    callable: builtins.callable,
    filter: builtins.filter,
    map: builtins.map,
    reversed: builtins.reversed,
    round: builtins.round,
    abs: builtins.abs,
    len: builtins.len,
    // Standard library (Phase 18.4)
    json,
    math,
    re,
    random,
    // Decorators (Phase 18.5)
    memoize: decorators.memoize,
    debounce: decorators.debounce,
    throttle: decorators.throttle,
    once: decorators.once,
    retry: decorators.retry,
    deprecated: decorators.deprecated,
    log_calls: decorators.log_calls,
    timed: decorators.timed,
    cached_property: decorators.cached_property,
    validate: decorators.validate,
    lock: decorators.lock,
    compose: decorators.compose,
    // Dunder methods (Phase 33.3: Operator Overloading)
    dunders: dunders.dunders,
};

export default __py;
