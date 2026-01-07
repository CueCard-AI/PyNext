/**
 * PyNext Runtime - operator Module
 * 
 * WHAT THIS FILE DOES:
 * Provides Python operator module functionality in JavaScript.
 * Implements itemgetter, attrgetter, methodcaller, and various operators.
 * 
 * EXAMPLES:
 *     // In Python:
 *     from pynext.client.operator import itemgetter, add
 *     get_second = itemgetter(1)
 *     result = add(3, 5)  # 8
 */

/**
 * itemgetter - Create function to get item(s) from object.
 */
export function itemgetter(...items) {
    if (items.length === 1) {
        const item = items[0];
        return function(obj) {
            return obj[item];
        };
    }
    return function(obj) {
        return items.map(item => obj[item]);
    };
}

/**
 * attrgetter - Create function to get attribute(s) from object.
 */
export function attrgetter(...attrs) {
    if (attrs.length === 1) {
        const attr = attrs[0];
        return function(obj) {
            return obj[attr];
        };
    }
    return function(obj) {
        return attrs.map(attr => obj[attr]);
    };
}

/**
 * methodcaller - Create function to call method with arguments.
 */
export function methodcaller(name, ...args) {
    return function(obj) {
        return obj[name](...args);
    };
}

// Arithmetic operators
export function add(a, b) { return a + b; }
export function sub(a, b) { return a - b; }
export function mul(a, b) { return a * b; }
export function truediv(a, b) { return a / b; }
export function floordiv(a, b) { return Math.floor(a / b); }
export function mod(a, b) { return a % b; }
export function pow(a, b) { return a ** b; }

// Comparison operators
export function lt(a, b) { return a < b; }
export function le(a, b) { return a <= b; }
export function eq(a, b) { return a === b; }
export function ne(a, b) { return a !== b; }
export function ge(a, b) { return a >= b; }
export function gt(a, b) { return a > b; }

// Logical operators
export function and_(a, b) { return a && b; }
export function or_(a, b) { return a || b; }
export function not_(a) { return !a; }

// Other operators
export function is_(a, b) { return a === b; }
export function is_not(a, b) { return a !== b; }
export function contains(a, b) {
    if (b === null || b === undefined) {
        return false;
    }
    if (typeof b === 'string' || Array.isArray(b)) {
        return b.includes(a);
    }
    if (typeof b === 'object' && b.has) {
        return b.has(a);
    }
    return a in b;
}

// Default export
export default {
    itemgetter,
    attrgetter,
    methodcaller,
    add,
    sub,
    mul,
    truediv,
    floordiv,
    mod,
    pow,
    lt,
    le,
    eq,
    ne,
    ge,
    gt,
    and_,
    or_,
    not_,
    is_,
    is_not,
    contains,
};

