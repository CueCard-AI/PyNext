/**
 * PyNext Runtime - Core Minimal
 * 
 * =============================================================================
 * WHO: Core contributors, bundle size debuggers
 * =============================================================================
 * 
 * =============================================================================
 * WHAT: 8 essential functions for Python-JavaScript interop
 * =============================================================================
 * 
 * This file contains ONLY the functions that 90%+ of Python code needs.
 * Everything else is in separate layers loaded on-demand.
 * 
 * Functions included:
 * - at(arr, i): Negative indexing (items[-1])
 * - slice(arr, s, e, step): Python slicing (items[1:3:-1])
 * - bool(x): Python truthiness ([] is falsy)
 * - eq(a, b): Deep equality ([1,2] == [1,2])
 * - mod(a, b): Python modulo (-1 % 3 = 2)
 * - floordiv(a, b): Floor division (7 // 3 = 2)
 * - range(s, e, step): Range iterator
 * - len(x): Length (works on dict too)
 * 
 * =============================================================================
 * WHEN: Always loaded - these are the unavoidable minimum
 * =============================================================================
 * 
 * =============================================================================
 * WHERE: Imported by transpiled code as '@pynext/runtime/core'
 * =============================================================================
 * 
 * =============================================================================
 * WHY: Python and JavaScript differ in fundamental ways
 * =============================================================================
 * 
 * Without these functions:
 * - items[-1] returns undefined (should return last element)
 * - [] is truthy in JS (should be falsy like Python)
 * - -1 % 3 = -1 in JS (should be 2 like Python)
 * 
 * =============================================================================
 * HOW: The transpiler emits calls to these functions
 * =============================================================================
 * 
 * Python:          JavaScript:
 * items[-1]     →  at(items, -1)
 * not items     →  !bool(items)
 * a == b        →  eq(a, b)
 * 
 * =============================================================================
 * SIZE BUDGET: < 600 bytes gzipped
 * =============================================================================
 */

// NO IMPORTS - This file must be completely self-contained for tree-shaking

/**
 * Python negative indexing: items[-1] returns last element
 * @param {Array|string} a - Array or string to index
 * @param {number} i - Index (can be negative)
 * @returns {*} Element at index
 */
export function at(a, i) {
    return i < 0 ? a[a.length + i] : a[i];
}

/**
 * Python slicing: items[start:stop:step]
 * @param {Array|string} a - Array or string to slice
 * @param {number|null} s - Start index
 * @param {number|null} e - Stop index (exclusive)
 * @param {number} p - Step value (default 1)
 * @returns {Array|string} Sliced result
 */
export function slice(a, s, e, p = 1) {
    const n = a.length;
    const str = typeof a === 'string';
    
    if (p === 0) throw new Error("slice step cannot be zero");
    
    if (p > 0) {
        s = s === null ? 0 : (s < 0 ? Math.max(0, n + s) : Math.min(n, s));
        e = e === null ? n : (e < 0 ? Math.max(0, n + e) : Math.min(n, e));
        const r = [];
        for (let i = s; i < e; i += p) r.push(a[i]);
        return str ? r.join('') : r;
    } else {
        s = s === null ? n - 1 : (s < 0 ? Math.max(-1, n + s) : Math.min(n - 1, s));
        e = e === null ? -1 : (e < 0 ? Math.max(-1, n + e) : Math.min(n - 1, e));
        const r = [];
        for (let i = s; i > e; i += p) if (i >= 0 && i < n) r.push(a[i]);
        return str ? r.join('') : r;
    }
}

/**
 * Python truthiness check
 * Python falsy: None, False, 0, 0.0, "", [], {}, set()
 * @param {*} x - Value to check
 * @returns {boolean} Python truthiness
 */
export function bool(x) {
    if (x == null || x === false || x === 0 || x === '') return false;
    if (Array.isArray(x)) return x.length > 0;
    if (typeof x === 'object') {
        if (x.constructor === Object) return Object.keys(x).length > 0;
        if (x instanceof Set || x instanceof Map) return x.size > 0;
    }
    return true;
}

/**
 * Python equality: deep comparison for collections
 * @param {*} a - First value
 * @param {*} b - Second value
 * @returns {boolean} Python equality
 */
export function eq(a, b) {
    if (a === b) return true;
    if (a == null || b == null) return a === b;
    if (typeof a !== typeof b) return false;
    
    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) return false;
        for (let i = 0; i < a.length; i++) if (!eq(a[i], b[i])) return false;
        return true;
    }
    
    if (typeof a === 'object' && a.constructor === Object && b.constructor === Object) {
        const ka = Object.keys(a), kb = Object.keys(b);
        if (ka.length !== kb.length) return false;
        for (const k of ka) if (!(k in b) || !eq(a[k], b[k])) return false;
        return true;
    }
    
    return false;
}

/**
 * Python modulo: always returns result with same sign as divisor
 * @param {number} a - Dividend
 * @param {number} b - Divisor
 * @returns {number} Python-style modulo
 */
export function mod(a, b) {
    if (b === 0) throw new Error("integer division or modulo by zero");
    const r = ((a % b) + b) % b;
    return r === 0 ? 0 : r;
}

/**
 * Python floor division: rounds toward negative infinity
 * @param {number} a - Dividend
 * @param {number} b - Divisor
 * @returns {number} Floor division result
 */
export function floordiv(a, b) {
    if (b === 0) throw new Error("integer division or modulo by zero");
    return Math.floor(a / b);
}

/**
 * Python range(): generates array of numbers
 * @param {number} start - Start value (or stop if only arg)
 * @param {number} [stop] - Stop value
 * @param {number} [step=1] - Step value
 * @returns {number[]} Array of numbers
 */
export function range(start, stop, step = 1) {
    if (stop === undefined) { stop = start; start = 0; }
    const r = [];
    if (step > 0) for (let i = start; i < stop; i += step) r.push(i);
    else for (let i = start; i > stop; i += step) r.push(i);
    return r;
}

/**
 * Python len(): works on arrays, strings, objects (dicts)
 * @param {*} x - Value to get length of
 * @returns {number} Length
 */
export function len(x) {
    if (x == null) throw new Error("object of type 'NoneType' has no len()");
    if (typeof x === 'string' || Array.isArray(x)) return x.length;
    if (x instanceof Set || x instanceof Map) return x.size;
    if (typeof x === 'object') return Object.keys(x).length;
    throw new Error(`object of type '${typeof x}' has no len()`);
}

// =============================================================================
// Default export for compatibility with existing code
// =============================================================================
export default { at, slice, bool, eq, mod, floordiv, range, len };

