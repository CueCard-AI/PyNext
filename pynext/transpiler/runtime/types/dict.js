/**
 * PyNext Transpiler - Python Dict Methods for JavaScript
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides JavaScript functions that implement Python dict method semantics.
 * Used when Python dict methods differ from JavaScript equivalents.
 * 
 * =============================================================================
 * WHY THIS EXISTS
 * =============================================================================
 * 
 * Python and JavaScript dict/object methods have critical differences:
 * 
 * 1. pop():        Python throws KeyError without default
 * 2. get():        Python returns None (not undefined) by default
 * 3. setdefault(): Python returns value and modifies dict
 * 4. popitem():    Python pops last inserted (LIFO in 3.7+)
 * 5. update():     Python accepts dict or iterable of pairs
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * The transpiler emits calls to these functions:
 * 
 *   d.pop("key")           → __py.dict.pop(d, "key")
 *   d.get("key")           → __py.dict.get(d, "key")
 *   d.setdefault("k", v)   → __py.dict.setdefault(d, "k", v)
 */

import { KeyError } from '../errors.js';

// =============================================================================
// POP - Throws KeyError without default
// =============================================================================

/**
 * Python pop() - remove key and return value, throws if missing
 * 
 * @param {Object} d - Dict to modify
 * @param {string} key - Key to pop
 * @param {*} defaultValue - Default if key missing (undefined = throw)
 * @returns {*} Value at key
 * @throws {Error} If key not found and no default
 */
export function pop(d, key, defaultValue = undefined) {
    if (key in d) {
        const value = d[key];
        delete d[key];
        return value;
    }
    if (defaultValue !== undefined) {
        return defaultValue;
    }
    throw new KeyError(key);
}

// =============================================================================
// GET - Returns null (not undefined) by default
// =============================================================================

/**
 * Python get() - get value with default
 * 
 * @param {Object} d - Dict to access
 * @param {string} key - Key to get
 * @param {*} defaultValue - Default if key missing (null like Python None)
 * @returns {*} Value at key or default
 */
export function get(d, key, defaultValue = null) {
    if (key in d) {
        return d[key];
    }
    return defaultValue;
}

// =============================================================================
// SETDEFAULT - Set and return default if missing
// =============================================================================

/**
 * Python setdefault() - get value, set default if missing
 * 
 * @param {Object} d - Dict to modify
 * @param {string} key - Key to get/set
 * @param {*} defaultValue - Value to set if missing
 * @returns {*} Value at key (existing or new)
 */
export function setdefault(d, key, defaultValue = null) {
    if (!(key in d)) {
        d[key] = defaultValue;
    }
    return d[key];
}

// =============================================================================
// POPITEM - Pop last inserted item
// =============================================================================

/**
 * Python popitem() - remove and return last inserted (key, value) pair
 * 
 * @param {Object} d - Dict to modify
 * @returns {[string, *]} [key, value] pair
 * @throws {Error} If dict is empty
 */
export function popitem(d) {
    const keys = Object.keys(d);
    if (keys.length === 0) {
        throw new KeyError('popitem(): dictionary is empty');
    }
    const key = keys[keys.length - 1];
    const value = d[key];
    delete d[key];
    return [key, value];
}

// =============================================================================
// UPDATE - Update with dict or iterable of pairs
// =============================================================================

/**
 * Python update() - update dict with another dict or pairs
 * 
 * @param {Object} d - Dict to update
 * @param {Object|Iterable} other - Source of updates
 * @param {Object} kwargs - Additional key=value pairs
 */
export function update(d, other = null, kwargs = {}) {
    if (other !== null) {
        if (typeof other[Symbol.iterator] === 'function' && !Array.isArray(other) && typeof other !== 'string') {
            // Iterable of pairs
            for (const [k, v] of other) {
                d[k] = v;
            }
        } else if (typeof other === 'object') {
            // Dict-like object
            Object.assign(d, other);
        }
    }
    Object.assign(d, kwargs);
}

// =============================================================================
// CLEAR
// =============================================================================

/**
 * Python clear() - remove all items
 * 
 * @param {Object} d - Dict to clear
 */
export function clear(d) {
    for (const key in d) {
        if (Object.prototype.hasOwnProperty.call(d, key)) {
            delete d[key];
        }
    }
}

// =============================================================================
// COPY
// =============================================================================

/**
 * Python copy() - shallow copy
 * 
 * @param {Object} d - Dict to copy
 * @returns {Object} Shallow copy
 */
export function copy(d) {
    return { ...d };
}

// =============================================================================
// KEYS / VALUES / ITEMS
// =============================================================================

/**
 * Python keys() - return keys
 */
export function keys(d) {
    return Object.keys(d);
}

/**
 * Python values() - return values
 */
export function values(d) {
    return Object.values(d);
}

/**
 * Python items() - return [key, value] pairs
 * 
 * Preserves key types (unlike Object.entries() which converts to strings).
 * For objects with integer keys, we need to preserve the numeric type.
 */
export function items(d) {
    // Object.entries() converts all keys to strings, which breaks Python semantics
    // We need to preserve the original key types
    const result = [];
    for (const key in d) {
        if (d.hasOwnProperty(key)) {
            // Try to preserve numeric keys as numbers
            const numKey = Number(key);
            const preservedKey = (!isNaN(numKey) && String(numKey) === key && numKey >= 0) ? numKey : key;
            result.push([preservedKey, d[key]]);
        }
    }
    return result;
}

// =============================================================================
// FROMKEYS
// =============================================================================

/**
 * Python dict.fromkeys() - create dict from keys with value
 * 
 * @param {Iterable} keys - Keys for new dict
 * @param {*} value - Value for all keys
 * @returns {Object} New dict
 */
export function fromkeys(keys, value = null) {
    const d = {};
    for (const k of keys) {
        d[k] = value;
    }
    return d;
}

// =============================================================================
// EXPORT
// =============================================================================

export default {
    pop,
    get,
    setdefault,
    popitem,
    update,
    clear,
    copy,
    keys,
    values,
    items,
    fromkeys,
};
