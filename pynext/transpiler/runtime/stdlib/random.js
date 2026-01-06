/**
 * PyNext Standard Library - random module
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides Python random module equivalents in JavaScript with SEEDABLE PRNG.
 * Uses xorshift128+ algorithm for reproducible random numbers.
 * 
 * =============================================================================
 * WHY THIS EXISTS
 * =============================================================================
 * 
 * Python random module differences from JavaScript:
 * - random.randint(a, b) is INCLUSIVE on both ends
 * - random.shuffle() is IN-PLACE and returns None
 * - random.sample() returns k unique elements
 * - random.choice() works on any sequence
 * - random.seed() allows reproducible sequences
 * 
 * =============================================================================
 * SEEDABLE PRNG
 * =============================================================================
 * 
 * Uses xorshift128+ algorithm:
 * - Fast (single function, no external libraries)
 * - Good statistical properties (passes BigCrush)
 * - 128-bit state, 2^128-1 period
 * - Reproducible when seeded
 * 
 * When seed() is called, subsequent random calls use the seeded PRNG.
 * When seed(None) or no seed, falls back to Math.random().
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * Python:
 *   import random
 *   random.seed(42)          # Now reproducible!
 *   x = random.randint(1, 10)
 *   random.shuffle(items)
 * 
 * Transpiled:
 *   __py.random.seed(42);
 *   const x = __py.random.randint(1, 10);
 *   __py.random.shuffle(items);
 */

// =============================================================================
// SEEDABLE PRNG - xorshift128+
// =============================================================================

/**
 * Internal state for xorshift128+ PRNG.
 * When null, uses Math.random() instead.
 */
let _state = null;

/**
 * Initialize internal state from a seed value.
 * Uses splitmix64 to expand seed into 128-bit state.
 * 
 * @param {number} seed - Integer seed value
 */
function _initState(seed) {
    // Ensure seed is a 32-bit integer
    seed = seed >>> 0;
    
    // Use splitmix64-like expansion to get 128-bit state
    // This ensures different seeds produce different states
    function splitmix32(x) {
        x = Math.imul(x ^ (x >>> 16), 0x85ebca6b);
        x = Math.imul(x ^ (x >>> 13), 0xc2b2ae35);
        return (x ^ (x >>> 16)) >>> 0;
    }
    
    // Generate two 64-bit values (stored as pairs of 32-bit)
    const s0_lo = splitmix32(seed);
    const s0_hi = splitmix32(seed + 1);
    const s1_lo = splitmix32(seed + 2);
    const s1_hi = splitmix32(seed + 3);
    
    _state = {
        s0_lo, s0_hi, s1_lo, s1_hi
    };
}

/**
 * xorshift128+ PRNG core.
 * Returns a random 32-bit unsigned integer.
 * 
 * @returns {number} Random integer in [0, 2^32)
 */
function _nextU32() {
    if (_state === null) {
        return (Math.random() * 0x100000000) >>> 0;
    }
    
    let { s0_lo, s0_hi, s1_lo, s1_hi } = _state;
    
    // xorshift128+ algorithm (simplified for 32-bit JS)
    // Based on: https://vigna.di.unimi.it/xorshift/xorshift128plus.c
    
    // Swap s0 and s1
    let t_lo = s0_lo;
    let t_hi = s0_hi;
    s0_lo = s1_lo;
    s0_hi = s1_hi;
    
    // s1 ^= s1 << 23 (simulate 64-bit shift)
    const shift23_hi = (t_lo << 23) | (t_hi >>> 9);
    const shift23_lo = t_lo << 23;
    t_lo ^= shift23_lo;
    t_hi ^= shift23_hi;
    
    // s1 ^= s1 >> 17
    const shift17_lo = (t_hi << 15) | (t_lo >>> 17);
    const shift17_hi = t_hi >>> 17;
    t_lo ^= shift17_lo;
    t_hi ^= shift17_hi;
    
    // s1 ^= s0
    t_lo ^= s0_lo;
    t_hi ^= s0_hi;
    
    // s1 ^= s0 >> 26
    const shift26_lo = (s0_hi << 6) | (s0_lo >>> 26);
    const shift26_hi = s0_hi >>> 26;
    t_lo ^= shift26_lo;
    t_hi ^= shift26_hi;
    
    // Update state
    _state.s0_lo = s0_lo;
    _state.s0_hi = s0_hi;
    _state.s1_lo = t_lo >>> 0;
    _state.s1_hi = t_hi >>> 0;
    
    // Return sum of old s0 and new s1 (just use low 32 bits)
    return ((s0_lo + t_lo) >>> 0);
}

/**
 * Get random float in [0, 1) using our PRNG.
 * @returns {number}
 */
function _randomFloat() {
    if (_state === null) {
        return Math.random();
    }
    // Use 32 bits for mantissa (sufficient precision for most use cases)
    return _nextU32() / 0x100000000;
}

// =============================================================================
// BASIC RANDOM FUNCTIONS
// =============================================================================

/**
 * Return a random float in [0.0, 1.0).
 * 
 * If seeded, uses xorshift128+ PRNG for reproducibility.
 * Otherwise uses Math.random().
 * 
 * @returns {number}
 * 
 * @example
 * random()  // → 0.7234123...
 */
export function random() {
    return _randomFloat();
}

/**
 * Return a random float in [a, b] (or [a, b) depending on rounding).
 * 
 * @param {number} a - Lower bound
 * @param {number} b - Upper bound
 * @returns {number}
 * 
 * @example
 * uniform(1, 10)  // → 5.234...
 */
export function uniform(a, b) {
    return a + _randomFloat() * (b - a);
}

// =============================================================================
// INTEGER RANDOM FUNCTIONS
// =============================================================================

/**
 * Return a random integer N such that a <= N <= b.
 * 
 * CRITICAL: Both endpoints are INCLUSIVE (unlike JS patterns).
 * 
 * @param {number} a - Lower bound (inclusive)
 * @param {number} b - Upper bound (inclusive)
 * @returns {number}
 * 
 * @example
 * randint(1, 6)  // → 1, 2, 3, 4, 5, or 6
 */
export function randint(a, b) {
    a = Math.floor(a);
    b = Math.floor(b);
    return Math.floor(_randomFloat() * (b - a + 1)) + a;
}

/**
 * Return a random integer N such that start <= N < stop.
 * 
 * @param {number} start - Lower bound (inclusive)
 * @param {number} stop - Upper bound (exclusive)
 * @param {number} step - Step value
 * @returns {number}
 * 
 * @example
 * randrange(0, 10)      // → 0-9
 * randrange(0, 10, 2)   // → 0, 2, 4, 6, or 8
 */
export function randrange(start, stop = null, step = 1) {
    if (stop === null) {
        stop = start;
        start = 0;
    }
    const count = Math.ceil((stop - start) / step);
    return start + step * Math.floor(_randomFloat() * count);
}

// =============================================================================
// SEQUENCE FUNCTIONS
// =============================================================================

/**
 * Return a random element from a non-empty sequence.
 * 
 * @param {Array|string} seq - Sequence to choose from
 * @returns {*}
 * @throws {Error} If sequence is empty
 * 
 * @example
 * choice([1, 2, 3])    // → 1, 2, or 3
 * choice('hello')      // → 'h', 'e', 'l', 'l', or 'o'
 */
export function choice(seq) {
    if (seq.length === 0) {
        throw new Error("Cannot choose from an empty sequence");
    }
    return seq[Math.floor(_randomFloat() * seq.length)];
}

/**
 * Return a list of k unique elements chosen from population.
 * 
 * @param {Array} population - Sequence to sample from
 * @param {number} k - Number of elements to select
 * @returns {Array}
 * @throws {Error} If k > population length
 * 
 * @example
 * sample([1, 2, 3, 4, 5], 3)  // → [3, 1, 5] (random)
 */
export function sample(population, k) {
    if (k > population.length) {
        throw new Error("Sample larger than population");
    }
    if (k < 0) {
        throw new Error("Sample size cannot be negative");
    }
    
    // Fisher-Yates partial shuffle
    const copy = [...population];
    const result = [];
    
    for (let i = 0; i < k; i++) {
        const idx = Math.floor(_randomFloat() * copy.length);
        result.push(copy.splice(idx, 1)[0]);
    }
    
    return result;
}

/**
 * Return a k-length list from population with replacement.
 * 
 * @param {Array} population - Sequence to choose from
 * @param {number} k - Number of selections
 * @param {Array|null} weights - Optional weights for each element
 * @returns {Array}
 * 
 * @example
 * choices([1, 2, 3], 5)  // → [2, 1, 3, 1, 2] (with possible repeats)
 */
export function choices(population, k = 1, weights = null) {
    if (population.length === 0) {
        throw new Error("Cannot choose from an empty population");
    }
    
    const result = [];
    
    if (weights === null) {
        // Uniform weights
        for (let i = 0; i < k; i++) {
            result.push(population[Math.floor(_randomFloat() * population.length)]);
        }
    } else {
        // Weighted selection
        const cumWeights = [];
        let sum = 0;
        for (const w of weights) {
            sum += w;
            cumWeights.push(sum);
        }
        
        for (let i = 0; i < k; i++) {
            const r = _randomFloat() * sum;
            for (let j = 0; j < cumWeights.length; j++) {
                if (r < cumWeights[j]) {
                    result.push(population[j]);
                    break;
                }
            }
        }
    }
    
    return result;
}

/**
 * Shuffle list x in place.
 * 
 * CRITICAL: Returns undefined (None in Python), NOT the shuffled list.
 * 
 * @param {Array} x - List to shuffle (MUTATED)
 * @returns {undefined}
 * 
 * @example
 * const items = [1, 2, 3, 4, 5];
 * shuffle(items);  // Returns undefined
 * // items is now [3, 1, 5, 2, 4] (random)
 */
export function shuffle(x) {
    // Fisher-Yates shuffle (in-place)
    for (let i = x.length - 1; i > 0; i--) {
        const j = Math.floor(_randomFloat() * (i + 1));
        [x[i], x[j]] = [x[j], x[i]];
    }
    // Python returns None (undefined in JS)
}

// =============================================================================
// DISTRIBUTION FUNCTIONS
// =============================================================================

/**
 * Return a random number from Gaussian distribution.
 * 
 * @param {number} mu - Mean
 * @param {number} sigma - Standard deviation
 * @returns {number}
 */
export function gauss(mu, sigma) {
    // Box-Muller transform
    let u1, u2;
    do {
        u1 = _randomFloat();
        u2 = _randomFloat();
    } while (u1 === 0);
    
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return mu + z * sigma;
}

/**
 * Alias for gauss() - normal distribution.
 */
export const normalvariate = gauss;

/**
 * Return a random number from exponential distribution.
 * 
 * @param {number} lambd - Rate parameter (1/mean)
 * @returns {number}
 */
export function expovariate(lambd) {
    return -Math.log(1 - _randomFloat()) / lambd;
}

/**
 * Return a random number from triangular distribution.
 * 
 * @param {number} low - Lower limit
 * @param {number} high - Upper limit
 * @param {number} mode - Most likely value
 * @returns {number}
 */
export function triangular(low = 0, high = 1, mode = null) {
    if (mode === null) {
        mode = (low + high) / 2;
    }
    const u = _randomFloat();
    const c = (mode - low) / (high - low);
    
    if (u < c) {
        return low + Math.sqrt(u * (high - low) * (mode - low));
    } else {
        return high - Math.sqrt((1 - u) * (high - low) * (high - mode));
    }
}

/**
 * Return a random number from beta distribution.
 * 
 * @param {number} alpha 
 * @param {number} beta 
 * @returns {number}
 */
export function betavariate(alpha, beta) {
    const y = gammavariate(alpha, 1);
    const z = gammavariate(beta, 1);
    return y / (y + z);
}

/**
 * Return a random number from gamma distribution.
 * 
 * @param {number} alpha - Shape parameter
 * @param {number} beta - Scale parameter
 * @returns {number}
 */
export function gammavariate(alpha, beta) {
    // Marsaglia and Tsang's method
    if (alpha < 1) {
        return gammavariate(alpha + 1, beta) * Math.pow(_randomFloat(), 1 / alpha);
    }
    
    const d = alpha - 1/3;
    const c = 1 / Math.sqrt(9 * d);
    
    while (true) {
        let x, v;
        do {
            x = gauss(0, 1);
            v = 1 + c * x;
        } while (v <= 0);
        
        v = v * v * v;
        const u = _randomFloat();
        
        if (u < 1 - 0.0331 * (x * x) * (x * x)) {
            return d * v * beta;
        }
        
        if (Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v))) {
            return d * v * beta;
        }
    }
}

// =============================================================================
// STATE FUNCTIONS (LIMITED SUPPORT)
// =============================================================================

/**
 * Initialize the random number generator with a seed.
 * 
 * Uses xorshift128+ PRNG for reproducible random sequences.
 * When called with a seed, all subsequent random calls will use
 * the seeded PRNG. Call seed(None) to return to unseeded mode.
 * 
 * @param {number|string|null} a - Seed value. Numbers are used directly,
 *   strings are hashed. null/undefined returns to unseeded mode.
 * 
 * @example
 * seed(42);
 * const a = random();    // Always the same value for seed 42
 * const b = randint(1,10);  // Next seeded value
 * 
 * seed(42);
 * const c = random();    // Same as a!
 */
export function seed(a = null) {
    if (a === null || a === undefined) {
        // Unseed - go back to Math.random()
        _state = null;
    } else {
        // Convert to integer seed
        let seedVal;
        if (typeof a === 'number') {
            seedVal = Math.floor(a) >>> 0;
        } else if (typeof a === 'string') {
            // Hash string to number
            seedVal = 0;
            for (let i = 0; i < a.length; i++) {
                seedVal = ((seedVal << 5) - seedVal + a.charCodeAt(i)) >>> 0;
            }
        } else {
            // Try to convert to number
            seedVal = Number(a) >>> 0;
        }
        _initState(seedVal);
    }
}

/**
 * Get state of random number generator.
 * 
 * Returns the internal state that can be restored with setstate().
 * 
 * @returns {object} State object
 */
export function getstate() {
    if (_state === null) {
        return { type: 'math.random', state: null };
    }
    return {
        type: 'xorshift128+',
        state: { ..._state }
    };
}

/**
 * Set state of random number generator.
 * 
 * @param {object} state - State from getstate()
 */
export function setstate(state) {
    if (state.type === 'math.random' || state.state === null) {
        _state = null;
    } else if (state.type === 'xorshift128+') {
        _state = { ...state.state };
    } else {
        throw new Error("Invalid state object for random.setstate()");
    }
}
