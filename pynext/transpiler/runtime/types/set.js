/**
 * PyNext Transpiler - Python Set Methods for JavaScript
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides JavaScript functions that implement Python set method semantics.
 * Used when Python set methods differ from JavaScript equivalents.
 * 
 * =============================================================================
 * WHY THIS EXISTS
 * =============================================================================
 * 
 * Python and JavaScript Set methods have critical differences:
 * 
 * 1. remove():     Python throws KeyError if missing
 * 2. discard():    Python ignores missing (like JS delete)
 * 3. pop():        Python pops arbitrary element
 * 4. update():     Python adds multiple items
 * 5. Operators:    Python has |, &, -, ^ for set operations
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * The transpiler emits calls to these functions:
 * 
 *   s.remove(x)        → __py.set.remove(s, x)
 *   s.pop()            → __py.set.pop(s)
 *   s.union(t)         → __py.set.union(s, t)
 */

import { KeyError } from '../errors.js';

// =============================================================================
// REMOVE - Throws KeyError if missing
// =============================================================================

/**
 * Python remove() - remove element, throws if missing
 * 
 * @param {Set} s - Set to modify
 * @param {*} elem - Element to remove
 * @throws {Error} If element not in set
 */
export function remove(s, elem) {
    if (!s.has(elem)) {
        throw new KeyError(elem);
    }
    s.delete(elem);
}

// =============================================================================
// DISCARD - Remove if present, ignore if missing
// =============================================================================

/**
 * Python discard() - remove element if present
 * 
 * @param {Set} s - Set to modify
 * @param {*} elem - Element to remove
 */
export function discard(s, elem) {
    s.delete(elem);
}

// =============================================================================
// POP - Remove and return arbitrary element
// =============================================================================

/**
 * Python pop() - remove and return arbitrary element
 * 
 * @param {Set} s - Set to modify
 * @returns {*} Removed element
 * @throws {Error} If set is empty
 */
export function pop(s) {
    if (s.size === 0) {
        throw new KeyError('pop from an empty set');
    }
    const elem = s.values().next().value;
    s.delete(elem);
    return elem;
}

// =============================================================================
// ADD (for completeness)
// =============================================================================

/**
 * Python add() - add element
 * 
 * @param {Set} s - Set to modify
 * @param {*} elem - Element to add
 */
export function add(s, elem) {
    s.add(elem);
}

// =============================================================================
// UPDATE - Add multiple elements
// =============================================================================

/**
 * Python update() - add elements from iterable
 * 
 * @param {Set} s - Set to modify
 * @param {...Iterable} iterables - Elements to add
 */
export function update(s, ...iterables) {
    for (const iterable of iterables) {
        for (const elem of iterable) {
            s.add(elem);
        }
    }
}

// =============================================================================
// CLEAR
// =============================================================================

/**
 * Python clear() - remove all elements
 * 
 * @param {Set} s - Set to clear
 */
export function clear(s) {
    s.clear();
}

// =============================================================================
// COPY
// =============================================================================

/**
 * Python copy() - shallow copy
 * 
 * @param {Set} s - Set to copy
 * @returns {Set} New set with same elements
 */
export function copy(s) {
    return new Set(s);
}

// =============================================================================
// SET OPERATIONS
// =============================================================================

/**
 * Python union() - return union of sets
 * 
 * @param {Set} s - First set
 * @param {...Iterable} others - Other sets/iterables
 * @returns {Set} Union
 */
export function union(s, ...others) {
    const result = new Set(s);
    for (const other of others) {
        for (const elem of other) {
            result.add(elem);
        }
    }
    return result;
}

/**
 * Python intersection() - return intersection of sets
 * 
 * @param {Set} s - First set
 * @param {...Iterable} others - Other sets/iterables
 * @returns {Set} Intersection
 */
export function intersection(s, ...others) {
    let result = new Set(s);
    for (const other of others) {
        const otherSet = new Set(other);
        result = new Set([...result].filter(x => otherSet.has(x)));
    }
    return result;
}

/**
 * Python difference() - return difference of sets
 * 
 * @param {Set} s - First set
 * @param {...Iterable} others - Sets to subtract
 * @returns {Set} Difference
 */
export function difference(s, ...others) {
    const result = new Set(s);
    for (const other of others) {
        for (const elem of other) {
            result.delete(elem);
        }
    }
    return result;
}

/**
 * Python symmetric_difference() - return symmetric difference
 * 
 * @param {Set} s - First set
 * @param {Iterable} other - Other set
 * @returns {Set} Symmetric difference
 */
export function symmetric_difference(s, other) {
    const otherSet = new Set(other);
    const result = new Set();
    
    for (const elem of s) {
        if (!otherSet.has(elem)) result.add(elem);
    }
    for (const elem of otherSet) {
        if (!s.has(elem)) result.add(elem);
    }
    
    return result;
}

// =============================================================================
// IN-PLACE SET OPERATIONS
// =============================================================================

/**
 * Python intersection_update() - update set with intersection
 */
export function intersection_update(s, ...others) {
    const keep = intersection(s, ...others);
    s.clear();
    for (const elem of keep) {
        s.add(elem);
    }
}

/**
 * Python difference_update() - update set with difference
 */
export function difference_update(s, ...others) {
    for (const other of others) {
        for (const elem of other) {
            s.delete(elem);
        }
    }
}

/**
 * Python symmetric_difference_update() - update with symmetric difference
 */
export function symmetric_difference_update(s, other) {
    const otherSet = new Set(other);
    const toRemove = [];
    const toAdd = [];
    
    for (const elem of s) {
        if (otherSet.has(elem)) toRemove.push(elem);
    }
    for (const elem of otherSet) {
        if (!s.has(elem)) toAdd.push(elem);
    }
    
    for (const elem of toRemove) s.delete(elem);
    for (const elem of toAdd) s.add(elem);
}

// =============================================================================
// COMPARISON METHODS
// =============================================================================

/**
 * Python issubset() - test if s is subset of other
 */
export function issubset(s, other) {
    const otherSet = other instanceof Set ? other : new Set(other);
    for (const elem of s) {
        if (!otherSet.has(elem)) return false;
    }
    return true;
}

/**
 * Python issuperset() - test if s is superset of other
 */
export function issuperset(s, other) {
    const otherSet = other instanceof Set ? other : new Set(other);
    for (const elem of otherSet) {
        if (!s.has(elem)) return false;
    }
    return true;
}

/**
 * Python isdisjoint() - test if sets have no common elements
 */
export function isdisjoint(s, other) {
    for (const elem of other) {
        if (s.has(elem)) return false;
    }
    return true;
}

// =============================================================================
// EXPORT
// =============================================================================

export default {
    remove,
    discard,
    pop,
    add,
    update,
    clear,
    copy,
    union,
    intersection,
    difference,
    symmetric_difference,
    intersection_update,
    difference_update,
    symmetric_difference_update,
    issubset,
    issuperset,
    isdisjoint,
};
