/**
 * PyNext Runtime - functools Module
 * 
 * WHAT THIS FILE DOES:
 * Provides Python functools module functionality in JavaScript.
 * Implements partial, reduce, lru_cache, cache, and wraps.
 * 
 * EXAMPLES:
 *     // In Python:
 *     from pynext.client.functools import partial, lru_cache
 *     
 *     @lru_cache(maxsize=128)
 *     def expensive_function(n):
 *         ...
 */

/**
 * partial - Partial function application.
 */
export function partial(func, ...args) {
    return function(...moreArgs) {
        return func(...args, ...moreArgs);
    };
}

/**
 * reduce - Reduce iterable with function.
 */
export function reduce(function_, iterable, initializer = undefined) {
    const iterator = iterable[Symbol.iterator]();
    let accumulator = initializer;
    
    if (accumulator === undefined) {
        const first = iterator.next();
        if (first.done) {
            throw new TypeError('reduce() of empty sequence with no initial value');
        }
        accumulator = first.value;
    }
    
    for (const item of iterator) {
        accumulator = function_(accumulator, item);
    }
    
    return accumulator;
}

/**
 * LRU Cache implementation.
 */
class LRUCache {
    constructor(maxsize = 128) {
        this.maxsize = maxsize;
        this.cache = new Map();
    }
    
    get(key) {
        if (this.cache.has(key)) {
            // Move to end (most recently used)
            const value = this.cache.get(key);
            this.cache.delete(key);
            this.cache.set(key, value);
            return value;
        }
        return undefined;
    }
    
    set(key, value) {
        if (this.cache.has(key)) {
            // Update existing
            this.cache.delete(key);
        } else if (this.cache.size >= this.maxsize) {
            // Remove least recently used (first item)
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        this.cache.set(key, value);
    }
    
    clear() {
        this.cache.clear();
    }
    
    get size() {
        return this.cache.size;
    }
}

/**
 * lru_cache - LRU cache decorator.
 */
export function lru_cache(maxsize = 128) {
    return function(func) {
        const cache = new LRUCache(maxsize);
        
        const cachedFunc = function(...args) {
            // Create cache key from arguments
            const key = JSON.stringify(args);
            
            // Check cache
            const cached = cache.get(key);
            if (cached !== undefined) {
                return cached;
            }
            
            // Compute and cache
            const result = func(...args);
            cache.set(key, result);
            return result;
        };
        
        // Add cache methods
        cachedFunc.cache_clear = () => cache.clear();
        cachedFunc.cache_info = () => ({
            hits: 0,  // Would need to track this
            misses: 0,  // Would need to track this
            maxsize: maxsize,
            currsize: cache.size,
        });
        
        return cachedFunc;
    };
}

/**
 * cache - Simple cache decorator (unlimited cache).
 */
export function cache(func) {
    return lru_cache(null)(func);
}

/**
 * wraps - Copy function metadata.
 */
export function wraps(wrapped) {
    return function decorator(wrapper) {
        wrapper.__name__ = wrapped.__name__ || wrapped.name;
        wrapper.__doc__ = wrapped.__doc__;
        wrapper.__module__ = wrapped.__module__;
        wrapper.__qualname__ = wrapped.__qualname__ || wrapped.name;
        return wrapper;
    };
}

// Default export
export default {
    partial,
    reduce,
    lru_cache,
    cache,
    wraps,
};

