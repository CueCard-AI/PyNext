/**
 * PyNext Runtime - copy Module
 * 
 * WHAT THIS FILE DOES:
 * Provides Python copy module functionality in JavaScript.
 * Implements copy (shallow) and deepcopy.
 * 
 * EXAMPLES:
 *     // In Python:
 *     from pynext.client.copy import copy, deepcopy
 *     shallow = copy(obj)
 *     deep = deepcopy(obj)
 */

/**
 * copy - Shallow copy of object.
 */
export function copy(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }
    
    if (Array.isArray(obj)) {
        return [...obj];
    }
    
    if (obj instanceof Date) {
        return new Date(obj);
    }
    
    if (obj instanceof Map) {
        return new Map(obj);
    }
    
    if (obj instanceof Set) {
        return new Set(obj);
    }
    
    // Plain object
    return { ...obj };
}

/**
 * deepcopy - Deep copy of object.
 */
export function deepcopy(obj, memo = null) {
    if (memo === null) {
        memo = new WeakMap();
    }
    
    // Handle primitives
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }
    
    // Handle circular references
    if (memo.has(obj)) {
        return memo.get(obj);
    }
    
    // Handle arrays
    if (Array.isArray(obj)) {
        const copy = [];
        memo.set(obj, copy);
        for (const item of obj) {
            copy.push(deepcopy(item, memo));
        }
        return copy;
    }
    
    // Handle Date
    if (obj instanceof Date) {
        const copy = new Date(obj);
        memo.set(obj, copy);
        return copy;
    }
    
    // Handle Map
    if (obj instanceof Map) {
        const copy = new Map();
        memo.set(obj, copy);
        for (const [key, value] of obj) {
            copy.set(deepcopy(key, memo), deepcopy(value, memo));
        }
        return copy;
    }
    
    // Handle Set
    if (obj instanceof Set) {
        const copy = new Set();
        memo.set(obj, copy);
        for (const item of obj) {
            copy.add(deepcopy(item, memo));
        }
        return copy;
    }
    
    // Handle plain objects
    const copy = {};
    memo.set(obj, copy);
    for (const [key, value] of Object.entries(obj)) {
        copy[key] = deepcopy(value, memo);
    }
    return copy;
}

// Default export
export default {
    copy,
    deepcopy,
};

