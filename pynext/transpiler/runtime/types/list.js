/**
 * PyNext Transpiler - Python List Methods for JavaScript
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides JavaScript functions that implement Python list method semantics.
 * Used when Python list methods differ from JavaScript equivalents.
 * 
 * =============================================================================
 * WHY THIS EXISTS
 * =============================================================================
 * 
 * Python and JavaScript list/array methods have critical differences:
 * 
 * 1. remove():   Python uses deep equality and throws if not found
 * 2. index():    Python throws ValueError, JS indexOf returns -1
 * 3. sort():     Python sorts numerically by default, JS sorts as strings
 * 4. pop(i):     Python allows index, JS only pops from end
 * 5. insert():   Python returns None, JS splice returns removed items
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * The transpiler emits calls to these functions:
 * 
 *   items.remove(x)        → __py.list.remove(items, x)
 *   items.index(x)         → __py.list.index(items, x)
 *   items.sort(key=fn)     → __py.list.sort(items, fn)
 */

import { eq } from '../core.js';
import { ValueError, IndexError, PyTypeError as TypeError_ } from '../errors.js';

// =============================================================================
// REMOVE - Uses deep equality, throws if not found
// =============================================================================

/**
 * Python remove() - remove first occurrence using deep equality
 * 
 * @param {Array} arr - Array to modify
 * @param {*} value - Value to remove
 * @throws {Error} If value not in list
 * 
 * @example
 * remove([1, 2, 3], 2)       // → [1, 3]
 * remove([[1], [2]], [1])    // → [[2]] (deep equality!)
 */
export function remove(arr, value) {
    for (let i = 0; i < arr.length; i++) {
        if (eq(arr[i], value)) {
            arr.splice(i, 1);
            return;
        }
    }
    throw new ValueError('list.remove(x): x not in list');
}

// =============================================================================
// INDEX - Throws if not found
// =============================================================================

/**
 * Python index() - find index using deep equality, throws if not found
 * 
 * @param {Array} arr - Array to search
 * @param {*} value - Value to find
 * @param {number} start - Start index
 * @param {number|null} stop - Stop index
 * @returns {number} Index of value
 * @throws {Error} If value not in list
 */
export function index(arr, value, start = 0, stop = null) {
    const end = stop === null ? arr.length : stop;
    for (let i = start; i < end && i < arr.length; i++) {
        if (eq(arr[i], value)) {
            return i;
        }
    }
    throw new ValueError('x is not in list');
}

// =============================================================================
// COUNT - Count occurrences with deep equality
// =============================================================================

/**
 * Python count() - count occurrences using deep equality
 * 
 * @param {Array} arr - Array to search
 * @param {*} value - Value to count
 * @returns {number} Count of occurrences
 */
export function count(arr, value) {
    let count = 0;
    for (const item of arr) {
        if (eq(item, value)) count++;
    }
    return count;
}

// =============================================================================
// SORT - Numeric default, key function, reverse
// =============================================================================

/**
 * Python sort() - sort in place with key function and reverse
 * 
 * @param {Array} arr - Array to sort
 * @param {Function|null} key - Key function
 * @param {boolean} reverse - Reverse order
 * 
 * @example
 * sort([3, 1, 2])                    // → [1, 2, 3] (numeric!)
 * sort(["b", "a", "c"])              // → ["a", "b", "c"]
 * sort([{x: 2}, {x: 1}], o => o.x)   // → [{x: 1}, {x: 2}]
 * 
 * Note: Python 3 throws TypeError on mixed types ([1, "a"].sort())
 */
export function sort(arr, key = null, reverse = false) {
    const cmp = (a, b) => {
        const keyA = key ? key(a) : a;
        const keyB = key ? key(b) : b;
        
        const typeA = typeof keyA;
        const typeB = typeof keyB;
        
        // Python 3: TypeError on mixed types
        if (typeA !== typeB) {
            // Allow null/undefined to compare (they'll be at the end)
            if (keyA != null && keyB != null) {
                throw new TypeError_(`'<' not supported between instances of '${typeA}' and '${typeB}'`);
            }
        }
        
        // Numeric comparison if both are numbers
        if (typeA === 'number' && typeB === 'number') {
            return reverse ? keyB - keyA : keyA - keyB;
        }
        
        // String comparison
        if (typeA === 'string' && typeB === 'string') {
            if (keyA < keyB) return reverse ? 1 : -1;
            if (keyA > keyB) return reverse ? -1 : 1;
            return 0;
        }
        
        // For other types, use default comparison
        const strA = String(keyA);
        const strB = String(keyB);
        if (strA < strB) return reverse ? 1 : -1;
        if (strA > strB) return reverse ? -1 : 1;
        return 0;
    };
    
    arr.sort(cmp);
}

// =============================================================================
// POP - With index support
// =============================================================================

/**
 * Python pop() - pop at index (default -1)
 * 
 * @param {Array} arr - Array to modify
 * @param {number} index - Index to pop (default -1 = last)
 * @returns {*} Removed element
 * @throws {Error} If index out of range
 */
export function pop(arr, index = -1) {
    if (arr.length === 0) {
        throw new IndexError('pop from empty list');
    }
    
    // Normalize negative index
    if (index < 0) index = arr.length + index;
    
    if (index < 0 || index >= arr.length) {
        throw new IndexError('pop index out of range');
    }
    
    return arr.splice(index, 1)[0];
}

// =============================================================================
// INSERT
// =============================================================================

/**
 * Python insert() - insert at index
 * 
 * @param {Array} arr - Array to modify
 * @param {number} index - Index to insert at
 * @param {*} value - Value to insert
 */
export function insert(arr, index, value) {
    // Python allows negative indices and clamps out-of-range
    // Python: insert(-1, x) inserts BEFORE the last element
    if (index < 0) index = Math.max(0, arr.length + index);
    if (index > arr.length) index = arr.length;
    arr.splice(index, 0, value);
}

// =============================================================================
// EXTEND
// =============================================================================

/**
 * Python extend() - extend list with iterable
 * 
 * @param {Array} arr - Array to extend
 * @param {Iterable} iterable - Items to add
 */
export function extend(arr, iterable) {
    for (const item of iterable) {
        arr.push(item);
    }
}

// =============================================================================
// CLEAR
// =============================================================================

/**
 * Python clear() - remove all items
 * 
 * @param {Array} arr - Array to clear
 */
export function clear(arr) {
    arr.length = 0;
}

// =============================================================================
// COPY
// =============================================================================

/**
 * Python copy() - shallow copy
 * 
 * @param {Array} arr - Array to copy
 * @returns {Array} Shallow copy
 */
export function copy(arr) {
    return [...arr];
}

// =============================================================================
// REVERSE
// =============================================================================

/**
 * Python reverse() - reverse in place
 * 
 * @param {Array} arr - Array to reverse
 */
export function reverse(arr) {
    arr.reverse();
}

// =============================================================================
// APPEND (for completeness - same as push but returns None)
// =============================================================================

/**
 * Python append() - add item to end (returns None in Python)
 * 
 * @param {Array} arr - Array to modify
 * @param {*} value - Value to append
 */
export function append(arr, value) {
    arr.push(value);
}

// =============================================================================
// EXPORT
// =============================================================================

export default {
    remove,
    index,
    count,
    sort,
    pop,
    insert,
    extend,
    clear,
    copy,
    reverse,
    append,
};
