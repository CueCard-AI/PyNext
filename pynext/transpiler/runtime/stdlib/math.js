/**
 * PyNext Standard Library - math module
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides Python math module equivalents in JavaScript.
 * Most map directly to Math.* but some need special handling.
 * 
 * =============================================================================
 * WHY THIS EXISTS
 * =============================================================================
 * 
 * Python math module differences:
 * - math.isnan(x) vs Number.isNaN(x) - same but different name
 * - math.isinf(x) - checks for +/-Infinity specifically
 * - math.log(x, base) - JS Math.log is only natural log
 * - math.factorial(n) - not in JS Math
 * - math.gcd(a, b) - not in JS Math
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * Python:
 *   import math
 *   x = math.sqrt(16)
 *   y = math.log(100, 10)
 * 
 * Transpiled:
 *   const x = __py.math.sqrt(16);  // or Math.sqrt(16)
 *   const y = __py.math.log(100, 10);
 */

// =============================================================================
// CONSTANTS
// =============================================================================

/** π (pi) - ratio of circle's circumference to diameter */
export const pi = Math.PI;

/** e - base of natural logarithm */
export const e = Math.E;

/** τ (tau) - 2π */
export const tau = 2 * Math.PI;

/** Positive infinity */
export const inf = Infinity;

/** Not a Number */
export const nan = NaN;

// =============================================================================
// NUMBER-THEORETIC FUNCTIONS
// =============================================================================

/**
 * Return the ceiling of x.
 * @param {number} x 
 * @returns {number}
 */
export const ceil = Math.ceil;

/**
 * Return the floor of x.
 * @param {number} x 
 * @returns {number}
 */
export const floor = Math.floor;

/**
 * Return the truncated value of x.
 * @param {number} x 
 * @returns {number}
 */
export const trunc = Math.trunc;

/**
 * Return n factorial.
 * @param {number} n - Non-negative integer
 * @returns {number}
 * @throws {Error} If n is negative or not an integer
 */
export function factorial(n) {
    if (n < 0 || !Number.isInteger(n)) {
        throw new Error("factorial() not defined for negative values or non-integers");
    }
    if (n === 0 || n === 1) return 1;
    let result = 1;
    for (let i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

/**
 * Return the greatest common divisor of a and b.
 * @param {number} a 
 * @param {number} b 
 * @returns {number}
 */
export function gcd(a, b) {
    a = Math.abs(Math.floor(a));
    b = Math.abs(Math.floor(b));
    while (b) {
        [a, b] = [b, a % b];
    }
    return a;
}

/**
 * Return the least common multiple of a and b.
 * @param {number} a 
 * @param {number} b 
 * @returns {number}
 */
export function lcm(a, b) {
    if (a === 0 || b === 0) return 0;
    return Math.abs(Math.floor(a) * Math.floor(b)) / gcd(a, b);
}

// =============================================================================
// POWER AND LOGARITHMIC FUNCTIONS
// =============================================================================

/**
 * Return e raised to the power x.
 * @param {number} x 
 * @returns {number}
 */
export const exp = Math.exp;

/**
 * Return the natural logarithm of x, or log base `base` if provided.
 * @param {number} x 
 * @param {number} [base] - Optional base (default: e)
 * @returns {number}
 */
export function log(x, base = null) {
    if (base === null) {
        return Math.log(x);
    }
    return Math.log(x) / Math.log(base);
}

/**
 * Return the base-10 logarithm of x.
 * @param {number} x 
 * @returns {number}
 */
export const log10 = Math.log10;

/**
 * Return the base-2 logarithm of x.
 * @param {number} x 
 * @returns {number}
 */
export const log2 = Math.log2;

/**
 * Return x raised to the power y.
 * @param {number} x 
 * @param {number} y 
 * @returns {number}
 */
export const pow = Math.pow;

/**
 * Return the square root of x.
 * @param {number} x 
 * @returns {number}
 */
export const sqrt = Math.sqrt;

/**
 * Return the square root of the sum of squares of the arguments.
 * @param  {...number} args 
 * @returns {number}
 */
export const hypot = Math.hypot;

// =============================================================================
// TRIGONOMETRIC FUNCTIONS
// =============================================================================

/**
 * Return the sine of x (in radians).
 * @param {number} x 
 * @returns {number}
 */
export const sin = Math.sin;

/**
 * Return the cosine of x (in radians).
 * @param {number} x 
 * @returns {number}
 */
export const cos = Math.cos;

/**
 * Return the tangent of x (in radians).
 * @param {number} x 
 * @returns {number}
 */
export const tan = Math.tan;

/**
 * Return the arc sine of x.
 * @param {number} x 
 * @returns {number}
 */
export const asin = Math.asin;

/**
 * Return the arc cosine of x.
 * @param {number} x 
 * @returns {number}
 */
export const acos = Math.acos;

/**
 * Return the arc tangent of x.
 * @param {number} x 
 * @returns {number}
 */
export const atan = Math.atan;

/**
 * Return the arc tangent of y/x.
 * @param {number} y 
 * @param {number} x 
 * @returns {number}
 */
export const atan2 = Math.atan2;

// =============================================================================
// HYPERBOLIC FUNCTIONS
// =============================================================================

export const sinh = Math.sinh;
export const cosh = Math.cosh;
export const tanh = Math.tanh;
export const asinh = Math.asinh;
export const acosh = Math.acosh;
export const atanh = Math.atanh;

// =============================================================================
// ANGULAR CONVERSION
// =============================================================================

/**
 * Convert angle x from radians to degrees.
 * @param {number} x - Angle in radians
 * @returns {number} Angle in degrees
 */
export function degrees(x) {
    return x * (180 / Math.PI);
}

/**
 * Convert angle x from degrees to radians.
 * @param {number} x - Angle in degrees
 * @returns {number} Angle in radians
 */
export function radians(x) {
    return x * (Math.PI / 180);
}

// =============================================================================
// SPECIAL FUNCTIONS
// =============================================================================

/**
 * Return the absolute value of x.
 * @param {number} x 
 * @returns {number}
 */
export const fabs = Math.abs;

/**
 * Return the sign of x.
 * @param {number} x 
 * @returns {number} -1, 0, or 1
 */
export const copysign = (x, y) => Math.abs(x) * Math.sign(y);

/**
 * Return True if x is a finite number.
 * @param {number} x 
 * @returns {boolean}
 */
export function isfinite(x) {
    return Number.isFinite(x);
}

/**
 * Return True if x is infinity.
 * @param {number} x 
 * @returns {boolean}
 */
export function isinf(x) {
    return !Number.isFinite(x) && !Number.isNaN(x);
}

/**
 * Return True if x is NaN.
 * @param {number} x 
 * @returns {boolean}
 */
export function isnan(x) {
    return Number.isNaN(x);
}

/**
 * Return the fractional and integer parts of x.
 * @param {number} x 
 * @returns {[number, number]} [fractional, integer]
 */
export function modf(x) {
    const int = Math.trunc(x);
    return [x - int, int];
}

/**
 * Return x * (2**i).
 * @param {number} x 
 * @param {number} i 
 * @returns {number}
 */
export function ldexp(x, i) {
    return x * Math.pow(2, i);
}

/**
 * Return (m, e) such that x = m * 2**e.
 * @param {number} x 
 * @returns {[number, number]} [mantissa, exponent]
 */
export function frexp(x) {
    if (x === 0) return [0, 0];
    const exp = Math.floor(Math.log2(Math.abs(x))) + 1;
    return [x / Math.pow(2, exp), exp];
}

/**
 * Sum of iterable of numbers with extended precision.
 * @param {Iterable<number>} iterable 
 * @returns {number}
 */
export function fsum(iterable) {
    // Simple implementation - not as precise as Python's
    let sum = 0;
    for (const x of iterable) {
        sum += x;
    }
    return sum;
}

/**
 * Return the product of all elements in iterable.
 * @param {Iterable<number>} iterable 
 * @param {number} start - Starting value (default 1)
 * @returns {number}
 */
export function prod(iterable, start = 1) {
    let result = start;
    for (const x of iterable) {
        result *= x;
    }
    return result;
}
