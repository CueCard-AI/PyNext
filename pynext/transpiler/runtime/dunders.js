/**
 * PyNext Transpiler - Dunder Method Runtime Helpers
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides JavaScript functions that implement Python dunder method semantics.
 * Used by transpiled code to handle operator overloading and special behaviors
 * that don't have direct JavaScript equivalents.
 * 
 * =============================================================================
 * WHY THIS EXISTS (Problem It Solves)
 * =============================================================================
 * 
 * Python's dunder methods enable rich operator overloading:
 * - obj1 == obj2 calls obj1.__eq__(obj2) if defined
 * - len(obj) calls obj.__len__()
 * - obj[key] calls obj.__getitem__(key)
 * 
 * JavaScript doesn't have this, so we need runtime helpers:
 * 1. equals() - Pythonic equality with __eq__ support
 * 2. repr() - Object representation with __repr__ support
 * 3. format() - Format strings with __format__ support
 * 4. Arithmetic helpers - Handle type coercion for __add__, __sub__, etc.
 * 
 * =============================================================================
 * SIZE BUDGET
 * =============================================================================
 * 
 * Target: < 800 bytes gzipped
 * 
 * Functions are tree-shakeable - only used helpers are included.
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * The transpiler emits calls to these functions:
 * 
 *   obj1 == obj2     → __py.dunders.equals(obj1, obj2)
 *   repr(obj)        → __py.dunders.repr(obj)
 *   format(obj, spec) → __py.dunders.format(obj, spec)
 */

import {
    ValueError,
    TypeError as PyTypeError,
    AttributeError,
} from './errors.js';

// =============================================================================
// EQUALITY (__eq__, __ne__)
// =============================================================================

/**
 * Pythonic equality comparison with __eq__ support.
 * 
 * Handles:
 * - Objects with __eq__ method → calls obj.__eq__(other)
 * - Primitive types → direct === comparison
 * - None/null → special handling
 * - Arrays → deep equality
 * 
 * @param {*} a - First value
 * @param {*} b - Second value
 * @returns {boolean} True if equal
 * 
 * @example
 * equals({x: 1}, {x: 1})  // → true (shallow comparison)
 * equals([1, 2], [1, 2])  // → true (deep comparison)
 * equals(null, null)      // → true
 */
export function equals(a, b) {
    // Same reference
    if (a === b) return true;
    
    // Handle null/undefined
    if (a == null || b == null) return a === b;
    
    // If a has __eq__ method, use it
    if (typeof a === 'object' && a !== null && typeof a.equals === 'function') {
        return a.equals(b);
    }
    
    // If b has __eq__ method (reverse), use it
    if (typeof b === 'object' && b !== null && typeof b.equals === 'function') {
        // For reverse, we'd need b.__eq__ to handle a, but that's less common
        // For now, just do direct comparison
    }
    
    // Arrays: deep equality
    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) return false;
        for (let i = 0; i < a.length; i++) {
            if (!equals(a[i], b[i])) return false;
        }
        return true;
    }
    
    // Objects: shallow equality (key-value pairs)
    if (typeof a === 'object' && typeof b === 'object' && !Array.isArray(a) && !Array.isArray(b)) {
        const keysA = Object.keys(a);
        const keysB = Object.keys(b);
        if (keysA.length !== keysB.length) return false;
        for (const key of keysA) {
            if (!(key in b)) return false;
            if (!equals(a[key], b[key])) return false;
        }
        return true;
    }
    
    // Primitive types: direct comparison
    return a === b;
}

/**
 * Pythonic inequality comparison (not equals).
 * 
 * @param {*} a - First value
 * @param {*} b - Second value
 * @returns {boolean} True if not equal
 */
export function notEquals(a, b) {
    return !equals(a, b);
}

// =============================================================================
// REPRESENTATION (__repr__, __str__)
// =============================================================================

/**
 * Get object representation using __repr__ if available.
 * 
 * @param {*} obj - Object to represent
 * @returns {string} String representation
 * 
 * @example
 * repr({x: 1, y: 2})  // → "{x: 1, y: 2}"
 * repr([1, 2, 3])     // → "[1, 2, 3]"
 */
export function repr(obj) {
    // If object has __repr__ method (via Symbol), use it
    if (typeof obj === 'object' && obj !== null) {
        const reprSym = Symbol.for('repr');
        if (typeof obj[reprSym] === 'function') {
            return obj[reprSym]();
        }
    }
    
    // Fallback to toString()
    if (obj === null) return 'null';
    if (obj === undefined) return 'undefined';
    if (typeof obj === 'string') return `'${obj}'`;
    if (Array.isArray(obj)) {
        return '[' + obj.map(repr).join(', ') + ']';
    }
    if (typeof obj === 'object') {
        const entries = Object.entries(obj).map(([k, v]) => `${k}: ${repr(v)}`);
        return '{' + entries.join(', ') + '}';
    }
    return String(obj);
}

// =============================================================================
// FORMAT (__format__)
// =============================================================================

/**
 * Format object using __format__ if available.
 * 
 * @param {*} obj - Object to format
 * @param {string} format_spec - Format specification (e.g., ".2f", ",", ">10")
 * @returns {string} Formatted string
 * 
 * @example
 * format(3.14159, ".2f")  // → "3.14"
 * format(1234, ",")       // → "1,234"
 */
export function format(obj, format_spec) {
    // If object has __format__ method (via Symbol), use it
    if (typeof obj === 'object' && obj !== null) {
        const formatSym = Symbol.for('format');
        if (typeof obj[formatSym] === 'function') {
            return obj[formatSym](format_spec);
        }
    }
    
    // Fallback: basic formatting for numbers
    if (typeof obj === 'number') {
        if (format_spec === '.2f') {
            return obj.toFixed(2);
        }
        if (format_spec === ',') {
            return obj.toLocaleString();
        }
        // Add more format specs as needed
    }
    
    // Default: convert to string
    return String(obj);
}

// =============================================================================
// ARITHMETIC OPERATIONS (Phase 33.3: Complete Operator Overloading)
// =============================================================================

/**
 * WHAT: Comprehensive operator overloading runtime for Python dunder methods.
 * WHY: Python supports operator overloading via __add__, __radd__, __iadd__, etc.
 *      JavaScript doesn't, so we need runtime helpers.
 * HOW: Checks for dunder methods in order: __add__ → __radd__ → fallback.
 * WHO: Used by transpiled code when operators are used.
 * WHEN: At runtime when operators are evaluated.
 * WHERE: Part of runtime helpers (pynext/transpiler/runtime/dunders.js).
 * 
 * Operator Resolution Order:
 * 1. Check left operand's __add__ (or __sub__, __mul__, etc.)
 * 2. Check right operand's __radd__ (reverse operator)
 * 3. Fallback to JavaScript native operator
 * 
 * In-place operators (__iadd__, __isub__, etc.) are handled separately
 * by the emitter for augmented assignments (x += y).
 */

/**
 * Pythonic addition with __add__ and __radd__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's addition operator with operator overloading.
 * WHY: Python allows classes to override + via __add__ and __radd__.
 * HOW: Checks for __add__ on left, __radd__ on right, then falls back.
 * WHO: Called by transpiled code for a + b expressions.
 * WHEN: At runtime when addition is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * Examples:
 *   Point(1, 2) + Point(3, 4)  → p1.__add__(p2)
 *   5 + Point(1, 2)            → p.__radd__(5)
 *   1 + 2                      → 3 (native JS)
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result of addition
 */
export function add(a, b) {
    // Step 1: Check left operand's __add__ method
    if (typeof a === 'object' && a !== null && typeof a.__add__ === 'function') {
        const result = a.__add__(b);
        // Python returns NotImplemented to signal fallback to reverse operator
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Step 2: Check right operand's __radd__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__radd__ === 'function') {
        const result = b.__radd__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Step 3: Fallback to JavaScript addition
    // Handles: numbers, strings, arrays (list concatenation)
    if (Array.isArray(a) && Array.isArray(b)) {
        return [...a, ...b];
    }
    return a + b;
}

/**
 * Pythonic subtraction with __sub__ and __rsub__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's subtraction operator with operator overloading.
 * WHY: Python allows classes to override - via __sub__ and __rsub__.
 * HOW: Checks for __sub__ on left, __rsub__ on right, then falls back.
 * WHO: Called by transpiled code for a - b expressions.
 * WHEN: At runtime when subtraction is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result of subtraction
 */
export function sub(a, b) {
    // Check left operand's __sub__ method
    if (typeof a === 'object' && a !== null && typeof a.__sub__ === 'function') {
        const result = a.__sub__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __rsub__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__rsub__ === 'function') {
        const result = b.__rsub__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript subtraction
    return a - b;
}

/**
 * Pythonic multiplication with __mul__ and __rmul__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's multiplication operator with operator overloading.
 * WHY: Python allows classes to override * via __mul__ and __rmul__.
 * HOW: Checks for __mul__ on left, __rmul__ on right, then falls back.
 * WHO: Called by transpiled code for a * b expressions.
 * WHEN: At runtime when multiplication is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * Also handles string/list repetition:
 *   "abc" * 3  → "abcabcabc"
 *   [1, 2] * 3 → [1, 2, 1, 2, 1, 2]
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result of multiplication
 */
export function mul(a, b) {
    // Check left operand's __mul__ method
    if (typeof a === 'object' && a !== null && typeof a.__mul__ === 'function') {
        const result = a.__mul__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __rmul__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__rmul__ === 'function') {
        const result = b.__rmul__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback: Handle string/list repetition
    if (typeof a === 'string' && typeof b === 'number') {
        return a.repeat(b);
    }
    if (typeof b === 'string' && typeof a === 'number') {
        return b.repeat(a);
    }
    if (Array.isArray(a) && typeof b === 'number') {
        const result = [];
        for (let i = 0; i < b; i++) {
            result.push(...a);
        }
        return result;
    }
    if (Array.isArray(b) && typeof a === 'number') {
        const result = [];
        for (let i = 0; i < a; i++) {
            result.push(...b);
        }
        return result;
    }
    
    // Fallback to JavaScript multiplication
    return a * b;
}

/**
 * Pythonic true division with __truediv__ and __rtruediv__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's division operator (/) with operator overloading.
 * WHY: Python allows classes to override / via __truediv__ and __rtruediv__.
 * HOW: Checks for __truediv__ on left, __rtruediv__ on right, then falls back.
 * WHO: Called by transpiled code for a / b expressions.
 * WHEN: At runtime when division is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result of division
 */
export function truediv(a, b) {
    // Check left operand's __truediv__ method
    if (typeof a === 'object' && a !== null && typeof a.__truediv__ === 'function') {
        const result = a.__truediv__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __rtruediv__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__rtruediv__ === 'function') {
        const result = b.__rtruediv__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript division
    return a / b;
}

/**
 * Pythonic floor division with __floordiv__ and __rfloordiv__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's floor division operator (//) with operator overloading.
 * WHY: Python allows classes to override // via __floordiv__ and __rfloordiv__.
 * HOW: Checks for __floordiv__ on left, __rfloordiv__ on right, then falls back.
 * WHO: Called by transpiled code for a // b expressions.
 * WHEN: At runtime when floor division is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result of floor division
 */
export function floordiv(a, b) {
    // Check left operand's __floordiv__ method
    if (typeof a === 'object' && a !== null && typeof a.__floordiv__ === 'function') {
        const result = a.__floordiv__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __rfloordiv__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__rfloordiv__ === 'function') {
        const result = b.__rfloordiv__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback: JavaScript floor division (Math.floor)
    return Math.floor(a / b);
}

/**
 * Pythonic modulo with __mod__ and __rmod__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's modulo operator (%) with operator overloading.
 * WHY: Python allows classes to override % via __mod__ and __rmod__.
 * HOW: Checks for __mod__ on left, __rmod__ on right, then falls back.
 * WHO: Called by transpiled code for a % b expressions.
 * WHEN: At runtime when modulo is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result of modulo
 */
export function mod(a, b) {
    // Check left operand's __mod__ method
    if (typeof a === 'object' && a !== null && typeof a.__mod__ === 'function') {
        const result = a.__mod__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __rmod__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__rmod__ === 'function') {
        const result = b.__rmod__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript modulo
    return a % b;
}

/**
 * Pythonic power with __pow__ and __rpow__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's power operator (**) with operator overloading.
 * WHY: Python allows classes to override ** via __pow__ and __rpow__.
 * HOW: Checks for __pow__ on left, __rpow__ on right, then falls back.
 * WHO: Called by transpiled code for a ** b expressions.
 * WHEN: At runtime when power is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Base
 * @param {*} b - Exponent
 * @returns {*} Result of power operation
 */
export function pow(a, b) {
    // Check left operand's __pow__ method
    if (typeof a === 'object' && a !== null && typeof a.__pow__ === 'function') {
        const result = a.__pow__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __rpow__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__rpow__ === 'function') {
        const result = b.__rpow__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript power operator
    return a ** b;
}

/**
 * Pythonic left shift with __lshift__ and __rlshift__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's left shift operator (<<) with operator overloading.
 * WHY: Python allows classes to override << via __lshift__ and __rlshift__.
 * HOW: Checks for __lshift__ on left, __rlshift__ on right, then falls back.
 * WHO: Called by transpiled code for a << b expressions.
 * WHEN: At runtime when left shift is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand (shift amount)
 * @returns {*} Result of left shift
 */
export function lshift(a, b) {
    // Check left operand's __lshift__ method
    if (typeof a === 'object' && a !== null && typeof a.__lshift__ === 'function') {
        const result = a.__lshift__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __rlshift__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__rlshift__ === 'function') {
        const result = b.__rlshift__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript left shift
    return a << b;
}

/**
 * Pythonic right shift with __rshift__ and __rrshift__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's right shift operator (>>) with operator overloading.
 * WHY: Python allows classes to override >> via __rshift__ and __rrshift__.
 * HOW: Checks for __rshift__ on left, __rrshift__ on right, then falls back.
 * WHO: Called by transpiled code for a >> b expressions.
 * WHEN: At runtime when right shift is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand (shift amount)
 * @returns {*} Result of right shift
 */
export function rshift(a, b) {
    // Check left operand's __rshift__ method
    if (typeof a === 'object' && a !== null && typeof a.__rshift__ === 'function') {
        const result = a.__rshift__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __rrshift__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__rrshift__ === 'function') {
        const result = b.__rrshift__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript right shift
    return a >> b;
}

/**
 * Pythonic bitwise AND with __and__ and __rand__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's bitwise AND operator (&) with operator overloading.
 * WHY: Python allows classes to override & via __and__ and __rand__.
 * HOW: Checks for __and__ on left, __rand__ on right, then falls back.
 * WHO: Called by transpiled code for a & b expressions.
 * WHEN: At runtime when bitwise AND is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result of bitwise AND
 */
export function bitand(a, b) {
    // Check left operand's __and__ method
    if (typeof a === 'object' && a !== null && typeof a.__and__ === 'function') {
        const result = a.__and__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __rand__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__rand__ === 'function') {
        const result = b.__rand__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript bitwise AND
    return a & b;
}

/**
 * Pythonic bitwise OR with __or__ and __ror__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's bitwise OR operator (|) with operator overloading.
 * WHY: Python allows classes to override | via __or__ and __ror__.
 * HOW: Checks for __or__ on left, __ror__ on right, then falls back.
 * WHO: Called by transpiled code for a | b expressions.
 * WHEN: At runtime when bitwise OR is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result of bitwise OR
 */
export function bitor(a, b) {
    // Check left operand's __or__ method
    if (typeof a === 'object' && a !== null && typeof a.__or__ === 'function') {
        const result = a.__or__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __ror__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__ror__ === 'function') {
        const result = b.__ror__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript bitwise OR
    return a | b;
}

/**
 * Pythonic bitwise XOR with __xor__ and __rxor__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's bitwise XOR operator (^) with operator overloading.
 * WHY: Python allows classes to override ^ via __xor__ and __rxor__.
 * HOW: Checks for __xor__ on left, __rxor__ on right, then falls back.
 * WHO: Called by transpiled code for a ^ b expressions.
 * WHEN: At runtime when bitwise XOR is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand
 * @param {*} b - Right operand
 * @returns {*} Result of bitwise XOR
 */
export function bitxor(a, b) {
    // Check left operand's __xor__ method
    if (typeof a === 'object' && a !== null && typeof a.__xor__ === 'function') {
        const result = a.__xor__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Check right operand's __rxor__ method (reverse)
    if (typeof b === 'object' && b !== null && typeof b.__rxor__ === 'function') {
        const result = b.__rxor__(a);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript bitwise XOR
    return a ^ b;
}

// =============================================================================
// UNARY OPERATORS (Phase 33.3)
// =============================================================================

/**
 * Pythonic negation with __neg__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's unary negation operator (-) with operator overloading.
 * WHY: Python allows classes to override - via __neg__.
 * HOW: Checks for __neg__ method, then falls back.
 * WHO: Called by transpiled code for -a expressions.
 * WHEN: At runtime when negation is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Operand
 * @returns {*} Result of negation
 */
export function neg(a) {
    // Check operand's __neg__ method
    if (typeof a === 'object' && a !== null && typeof a.__neg__ === 'function') {
        const result = a.__neg__();
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript negation
    return -a;
}

/**
 * Pythonic positive with __pos__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's unary positive operator (+) with operator overloading.
 * WHY: Python allows classes to override + via __pos__.
 * HOW: Checks for __pos__ method, then falls back.
 * WHO: Called by transpiled code for +a expressions.
 * WHEN: At runtime when positive is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Operand
 * @returns {*} Result of positive
 */
export function pos(a) {
    // Check operand's __pos__ method
    if (typeof a === 'object' && a !== null && typeof a.__pos__ === 'function') {
        const result = a.__pos__();
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript positive (usually no-op)
    return +a;
}

/**
 * Pythonic absolute value with __abs__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's abs() function with operator overloading.
 * WHY: Python allows classes to override abs() via __abs__.
 * HOW: Checks for __abs__ method, then falls back.
 * WHO: Called by transpiled code for abs(a) expressions.
 * WHEN: At runtime when absolute value is computed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Operand
 * @returns {*} Result of absolute value
 */
export function abs(a) {
    // Check operand's __abs__ method
    if (typeof a === 'object' && a !== null && typeof a.__abs__ === 'function') {
        const result = a.__abs__();
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to JavaScript Math.abs
    return Math.abs(a);
}

// =============================================================================
// IN-PLACE OPERATORS (Phase 33.3)
// =============================================================================

/**
 * Pythonic in-place addition with __iadd__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's in-place addition operator (+=) with operator overloading.
 * WHY: Python allows classes to override += via __iadd__.
 * HOW: Checks for __iadd__ method, then falls back to regular addition.
 * WHO: Called by transpiled code for a += b expressions.
 * WHEN: At runtime when in-place addition is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * Note: In-place operators should modify the object in place and return it.
 * If __iadd__ is not defined, Python falls back to __add__ and assignment.
 * 
 * @param {*} a - Left operand (will be modified)
 * @param {*} b - Right operand
 * @returns {*} Result (usually a, modified in place)
 */
export function iadd(a, b) {
    // Check left operand's __iadd__ method
    if (typeof a === 'object' && a !== null && typeof a.__iadd__ === 'function') {
        const result = a.__iadd__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to regular addition (Python behavior)
    return add(a, b);
}

/**
 * Pythonic in-place subtraction with __isub__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's in-place subtraction operator (-=) with operator overloading.
 * WHY: Python allows classes to override -= via __isub__.
 * HOW: Checks for __isub__ method, then falls back to regular subtraction.
 * WHO: Called by transpiled code for a -= b expressions.
 * WHEN: At runtime when in-place subtraction is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand (will be modified)
 * @param {*} b - Right operand
 * @returns {*} Result (usually a, modified in place)
 */
export function isub(a, b) {
    // Check left operand's __isub__ method
    if (typeof a === 'object' && a !== null && typeof a.__isub__ === 'function') {
        const result = a.__isub__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to regular subtraction
    return sub(a, b);
}

/**
 * Pythonic in-place multiplication with __imul__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's in-place multiplication operator (*=) with operator overloading.
 * WHY: Python allows classes to override *= via __imul__.
 * HOW: Checks for __imul__ method, then falls back to regular multiplication.
 * WHO: Called by transpiled code for a *= b expressions.
 * WHEN: At runtime when in-place multiplication is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand (will be modified)
 * @param {*} b - Right operand
 * @returns {*} Result (usually a, modified in place)
 */
export function imul(a, b) {
    // Check left operand's __imul__ method
    if (typeof a === 'object' && a !== null && typeof a.__imul__ === 'function') {
        const result = a.__imul__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to regular multiplication
    return mul(a, b);
}

/**
 * Pythonic in-place true division with __itruediv__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's in-place division operator (/=) with operator overloading.
 * WHY: Python allows classes to override /= via __itruediv__.
 * HOW: Checks for __itruediv__ method, then falls back to regular division.
 * WHO: Called by transpiled code for a /= b expressions.
 * WHEN: At runtime when in-place division is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand (will be modified)
 * @param {*} b - Right operand
 * @returns {*} Result (usually a, modified in place)
 */
export function itruediv(a, b) {
    // Check left operand's __itruediv__ method
    if (typeof a === 'object' && a !== null && typeof a.__itruediv__ === 'function') {
        const result = a.__itruediv__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to regular division
    return truediv(a, b);
}

/**
 * Pythonic in-place floor division with __ifloordiv__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's in-place floor division operator (//=) with operator overloading.
 * WHY: Python allows classes to override //= via __ifloordiv__.
 * HOW: Checks for __ifloordiv__ method, then falls back to regular floor division.
 * WHO: Called by transpiled code for a //= b expressions.
 * WHEN: At runtime when in-place floor division is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand (will be modified)
 * @param {*} b - Right operand
 * @returns {*} Result (usually a, modified in place)
 */
export function ifloordiv(a, b) {
    // Check left operand's __ifloordiv__ method
    if (typeof a === 'object' && a !== null && typeof a.__ifloordiv__ === 'function') {
        const result = a.__ifloordiv__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to regular floor division
    return floordiv(a, b);
}

/**
 * Pythonic in-place modulo with __imod__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's in-place modulo operator (%=) with operator overloading.
 * WHY: Python allows classes to override %= via __imod__.
 * HOW: Checks for __imod__ method, then falls back to regular modulo.
 * WHO: Called by transpiled code for a %= b expressions.
 * WHEN: At runtime when in-place modulo is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand (will be modified)
 * @param {*} b - Right operand
 * @returns {*} Result (usually a, modified in place)
 */
export function imod(a, b) {
    // Check left operand's __imod__ method
    if (typeof a === 'object' && a !== null && typeof a.__imod__ === 'function') {
        const result = a.__imod__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to regular modulo
    return mod(a, b);
}

/**
 * Pythonic in-place power with __ipow__ support (Phase 33.3).
 * 
 * WHAT: Handles Python's in-place power operator (**=) with operator overloading.
 * WHY: Python allows classes to override **= via __ipow__.
 * HOW: Checks for __ipow__ method, then falls back to regular power.
 * WHO: Called by transpiled code for a **= b expressions.
 * WHEN: At runtime when in-place power is performed.
 * WHERE: Part of operator overloading runtime.
 * 
 * @param {*} a - Left operand (will be modified)
 * @param {*} b - Right operand
 * @returns {*} Result (usually a, modified in place)
 */
export function ipow(a, b) {
    // Check left operand's __ipow__ method
    if (typeof a === 'object' && a !== null && typeof a.__ipow__ === 'function') {
        const result = a.__ipow__(b);
        if (result !== undefined && result !== null) {
            return result;
        }
    }
    
    // Fallback to regular power
    return pow(a, b);
}

// =============================================================================
// EXPORTS (Phase 33.3: Complete Operator Overloading)
// =============================================================================

/**
 * Complete dunder method runtime helpers.
 * 
 * WHAT: Exports all operator overloading helpers.
 * WHY: Provides single import point for all dunder method support.
 * HOW: Groups all helpers into a single object.
 * WHO: Used by transpiled code and runtime.
 * WHEN: At runtime when operators are used.
 * WHERE: Part of runtime helpers.
 */
export const dunders = {
    // Comparison
    equals,
    notEquals,
    
    // Representation
    repr,
    format,
    
    // Binary arithmetic operators
    add,
    sub,
    mul,
    truediv,
    floordiv,
    mod,
    pow,
    
    // Bitwise operators
    lshift,
    rshift,
    bitand,
    bitor,
    bitxor,
    
    // Unary operators
    neg,
    pos,
    abs,
    
    // In-place operators
    iadd,
    isub,
    imul,
    itruediv,
    ifloordiv,
    imod,
    ipow,
};

