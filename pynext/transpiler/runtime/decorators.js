/**
 * PyNext Decorator Runtime (Phase 18.5)
 * 
 * Provides Python-like decorator functions for JavaScript:
 * - @memoize - Cache function results
 * - @debounce(ms) - Delay execution until calls stop
 * - @throttle(ms) - Limit execution rate
 * - @once - Execute only once
 * - @retry(n) - Retry on failure
 * - @deprecated(msg) - Log deprecation warning
 * - @validate(...validators) - Validate arguments
 * - @log_calls - Log function invocations
 * - @timed - Measure execution time
 * - @cached_property - Cache property result
 */

// =============================================================================
// MEMOIZE - Cache function results
// =============================================================================

/**
 * Memoize a function - cache results based on arguments.
 * 
 * @param {Function} fn - Function to memoize
 * @returns {Function} Memoized function
 * 
 * @example
 * const fib = memoize(function fib(n) {
 *     if (n <= 1) return n;
 *     return fib(n-1) + fib(n-2);
 * });
 */
export function memoize(fn) {
    const cache = new Map();
    
    /**
     * Create a stable cache key from arguments.
     * 
     * Strategy:
     * - Primitives: use directly (number, string, boolean, symbol, bigint)
     * - Single primitive arg: use the value directly
     * - Objects/Arrays: use JSON.stringify for structural equality
     * - Multiple args: prefix with type to avoid collisions
     */
    function makeKey(args) {
        if (args.length === 0) {
            return '__no_args__';
        }
        
        if (args.length === 1) {
            const arg = args[0];
            const type = typeof arg;
            
            // Primitives can be used directly as Map keys
            if (arg === null) return '__null__';
            if (arg === undefined) return '__undefined__';
            if (type === 'number' || type === 'string' || type === 'boolean' || type === 'symbol' || type === 'bigint') {
                return arg;
            }
            
            // Objects/Arrays: use JSON with type prefix to avoid collision
            // e.g., number 1 vs array [1] vs string "1"
            return '__obj__' + JSON.stringify(arg);
        }
        
        // Multiple args: always use JSON with type prefixes
        return '__multi__' + JSON.stringify(args.map(arg => {
            if (arg === null) return { __t: 'null' };
            if (arg === undefined) return { __t: 'undefined' };
            const type = typeof arg;
            if (type === 'symbol') return { __t: 'symbol', v: arg.toString() };
            if (type === 'bigint') return { __t: 'bigint', v: arg.toString() };
            return { __t: type, v: arg };
        }));
    }
    
    function memoized(...args) {
        const key = makeKey(args);
        
        if (!cache.has(key)) {
            cache.set(key, fn.apply(this, args));
        }
        return cache.get(key);
    }
    
    // Preserve function name and add cache access
    Object.defineProperty(memoized, 'name', { value: fn.name });
    memoized.cache = cache;
    memoized.clear = () => cache.clear();
    
    return memoized;
}


// =============================================================================
// DEBOUNCE - Delay execution until calls stop
// =============================================================================

/**
 * Debounce a function - delay execution until calls stop.
 * 
 * @param {number} ms - Milliseconds to wait
 * @returns {Function} Decorator function
 * 
 * @example
 * const search = debounce(300)(function search(query) {
 *     fetchResults(query);
 * });
 */
export function debounce(ms) {
    return function(fn) {
        let timeout = null;
        
        function debounced(...args) {
            if (timeout) {
                clearTimeout(timeout);
            }
            timeout = setTimeout(() => {
                fn.apply(this, args);
                timeout = null;
            }, ms);
        }
        
        // Preserve function name and add control methods
        Object.defineProperty(debounced, 'name', { value: fn.name });
        debounced.cancel = () => {
            if (timeout) {
                clearTimeout(timeout);
                timeout = null;
            }
        };
        debounced.flush = (...args) => {
            if (timeout) {
                clearTimeout(timeout);
                timeout = null;
            }
            return fn.apply(this, args);
        };
        
        return debounced;
    };
}


// =============================================================================
// THROTTLE - Limit execution rate
// =============================================================================

/**
 * Throttle a function - limit execution rate.
 * 
 * @param {number} ms - Minimum milliseconds between calls
 * @returns {Function} Decorator function
 * 
 * @example
 * const scroll = throttle(100)(function onScroll(e) {
 *     updatePosition();
 * });
 */
export function throttle(ms) {
    return function(fn) {
        let lastCall = 0;
        let timeout = null;
        
        function throttled(...args) {
            const now = Date.now();
            const remaining = ms - (now - lastCall);
            
            if (remaining <= 0) {
                // Execute immediately
                lastCall = now;
                return fn.apply(this, args);
            } else if (!timeout) {
                // Schedule for later
                timeout = setTimeout(() => {
                    lastCall = Date.now();
                    timeout = null;
                    fn.apply(this, args);
                }, remaining);
            }
        }
        
        // Preserve function name and add control methods
        Object.defineProperty(throttled, 'name', { value: fn.name });
        throttled.cancel = () => {
            if (timeout) {
                clearTimeout(timeout);
                timeout = null;
            }
        };
        
        return throttled;
    };
}


// =============================================================================
// ONCE - Execute only once
// =============================================================================

/**
 * Execute function only once, return cached result on subsequent calls.
 * 
 * @param {Function} fn - Function to execute once
 * @returns {Function} Function that executes only once
 * 
 * @example
 * const init = once(function init() {
 *     console.log('Initializing...');
 *     return { ready: true };
 * });
 */
export function once(fn) {
    let called = false;
    let result;
    
    function onceFn(...args) {
        if (!called) {
            called = true;
            result = fn.apply(this, args);
        }
        return result;
    }
    
    Object.defineProperty(onceFn, 'name', { value: fn.name });
    onceFn.called = () => called;
    onceFn.reset = () => { called = false; result = undefined; };
    
    return onceFn;
}


// =============================================================================
// RETRY - Retry on failure
// =============================================================================

/**
 * Retry a function on failure.
 * 
 * @param {number} maxRetries - Maximum number of retries (default: 3)
 * @param {number} delay - Delay between retries in ms (default: 0)
 * @returns {Function} Decorator function
 * 
 * @example
 * const fetch = retry(3, 1000)(async function fetchData() {
 *     const response = await fetch('/api/data');
 *     return response.json();
 * });
 */
export function retry(maxRetries = 3, delay = 0) {
    return function(fn) {
        async function retried(...args) {
            let lastError;
            
            for (let attempt = 0; attempt <= maxRetries; attempt++) {
                try {
                    return await fn.apply(this, args);
                } catch (error) {
                    lastError = error;
                    if (attempt < maxRetries && delay > 0) {
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                }
            }
            
            throw lastError;
        }
        
        Object.defineProperty(retried, 'name', { value: fn.name });
        return retried;
    };
}


// =============================================================================
// DEPRECATED - Log deprecation warning
// =============================================================================

/**
 * Mark a function as deprecated.
 * 
 * @param {string} message - Deprecation message
 * @returns {Function} Decorator function
 * 
 * @example
 * const oldMethod = deprecated('Use newMethod instead')(function oldMethod() {
 *     return doOldThing();
 * });
 */
export function deprecated(message = '') {
    return function(fn) {
        let warned = false;
        
        function deprecatedFn(...args) {
            if (!warned) {
                warned = true;
                console.warn(`DEPRECATED: ${fn.name}${message ? `: ${message}` : ''}`);
            }
            return fn.apply(this, args);
        }
        
        Object.defineProperty(deprecatedFn, 'name', { value: fn.name });
        return deprecatedFn;
    };
}


// =============================================================================
// LOG_CALLS - Log function invocations
// =============================================================================

/**
 * Log function calls with arguments and return values.
 * 
 * @param {Function} fn - Function to log
 * @returns {Function} Logged function
 * 
 * @example
 * const add = log_calls(function add(a, b) {
 *     return a + b;
 * });
 */
export function log_calls(fn) {
    function logged(...args) {
        console.log(`CALL: ${fn.name}(${args.map(a => JSON.stringify(a)).join(', ')})`);
        const result = fn.apply(this, args);
        console.log(`RETURN: ${fn.name} => ${JSON.stringify(result)}`);
        return result;
    }
    
    Object.defineProperty(logged, 'name', { value: fn.name });
    return logged;
}


// =============================================================================
// TIMED - Measure execution time
// =============================================================================

/**
 * Measure and log function execution time.
 * 
 * @param {Function} fn - Function to time
 * @returns {Function} Timed function
 * 
 * @example
 * const process = timed(function process(data) {
 *     return heavyComputation(data);
 * });
 */
export function timed(fn) {
    function timedFn(...args) {
        const start = performance.now();
        const result = fn.apply(this, args);
        const end = performance.now();
        console.log(`TIMING: ${fn.name} took ${(end - start).toFixed(2)}ms`);
        return result;
    }
    
    Object.defineProperty(timedFn, 'name', { value: fn.name });
    return timedFn;
}


// =============================================================================
// CACHED_PROPERTY - Cache property result
// =============================================================================

/**
 * Cache a property getter's result (computed once).
 * 
 * @param {Function} getter - Property getter function
 * @returns {Object} Property descriptor
 * 
 * @example
 * class Example {
 *     get expensive() {
 *         return cached_property(() => heavyComputation())();
 *     }
 * }
 */
export function cached_property(getter) {
    const cache = new WeakMap();
    
    return function() {
        if (!cache.has(this)) {
            cache.set(this, getter.call(this));
        }
        return cache.get(this);
    };
}


// =============================================================================
// VALIDATE - Validate arguments
// =============================================================================

/**
 * Validate function arguments.
 * 
 * @param {...Function} validators - Validator functions for each argument
 * @returns {Function} Decorator function
 * 
 * @example
 * const divide = validate(
 *     x => typeof x === 'number',
 *     y => typeof y === 'number' && y !== 0
 * )(function divide(x, y) {
 *     return x / y;
 * });
 */
export function validate(...validators) {
    return function(fn) {
        function validated(...args) {
            for (let i = 0; i < validators.length; i++) {
                if (validators[i] && !validators[i](args[i])) {
                    throw new TypeError(`Invalid argument at position ${i}`);
                }
            }
            return fn.apply(this, args);
        }
        
        Object.defineProperty(validated, 'name', { value: fn.name });
        return validated;
    };
}


// =============================================================================
// LOCK - Prevent concurrent execution
// =============================================================================

/**
 * Prevent concurrent execution of async functions.
 * 
 * @param {Function} fn - Async function to lock
 * @returns {Function} Locked function
 * 
 * @example
 * const save = lock(async function save(data) {
 *     await db.save(data);
 * });
 */
export function lock(fn) {
    let locked = false;
    let queue = [];
    
    async function lockedFn(...args) {
        if (locked) {
            // Wait for current execution to finish
            await new Promise(resolve => queue.push(resolve));
        }
        
        locked = true;
        try {
            return await fn.apply(this, args);
        } finally {
            locked = false;
            if (queue.length > 0) {
                const next = queue.shift();
                next();
            }
        }
    }
    
    Object.defineProperty(lockedFn, 'name', { value: fn.name });
    lockedFn.isLocked = () => locked;
    
    return lockedFn;
}


// =============================================================================
// COMPOSE - Compose multiple decorators
// =============================================================================

/**
 * Compose multiple decorators into one.
 * 
 * @param {...Function} decorators - Decorators to compose
 * @returns {Function} Composed decorator
 * 
 * @example
 * const enhanced = compose(memoize, timed, log_calls);
 * const fn = enhanced(function compute() { ... });
 */
export function compose(...decorators) {
    return function(fn) {
        return decorators.reduceRight((acc, decorator) => decorator(acc), fn);
    };
}
