/**
 * PyNext Runtime - Promise Utilities
 * 
 * WHAT THIS FILE DOES:
 * Provides Promise utility methods (all, allSettled, race, any, withResolvers)
 * that work in both Node.js and browser environments.
 * 
 * WHY THIS EXISTS:
 * Some Promise methods aren't available in all environments (e.g., Promise.any in older browsers).
 * This provides polyfills and consistent behavior across environments.
 * 
 * HOW IT WORKS:
 * - Uses native Promise methods when available
 * - Provides polyfills for older environments
 * - Handles AggregateError for Promise.any()
 * 
 * WHO USES THIS:
 * - Transpiled Python async code
 * - Client-side code using Promise utilities
 * 
 * WHEN TO USE:
 * - When you need Promise.all, Promise.allSettled, etc.
 * - When you need Promise.any with AggregateError support
 * 
 * EXAMPLES:
 *     // In Python:
 *     from pynext.client import Promise
 *     results = await Promise.all([fetch(url1), fetch(url2)])
 *     
 *     // Transpiles to:
 *     import { Promise } from 'pynext/runtime/promise.js';
 *     const results = await Promise.all([fetch(url1), fetch(url2)]);
 */

/**
 * AggregateError for Promise.any() when all promises reject.
 */
export class AggregateError extends Error {
    constructor(errors, message = 'All promises were rejected') {
        super(message);
        this.name = 'AggregateError';
        this.errors = errors;
    }
}

/**
 * Promise.all - Wait for all promises to resolve, or reject if any reject.
 */
export function Promise_all(promises) {
    if (typeof Promise.all === 'function') {
        return Promise.all(promises);
    }
    
    // Polyfill for environments without Promise.all
    if (!Array.isArray(promises)) {
        promises = Array.from(promises);
    }
    
    return new Promise((resolve, reject) => {
        if (promises.length === 0) {
            resolve([]);
            return;
        }
        
        const results = new Array(promises.length);
        let resolvedCount = 0;
        
        promises.forEach((promise, index) => {
            Promise.resolve(promise).then(
                value => {
                    results[index] = value;
                    resolvedCount++;
                    if (resolvedCount === promises.length) {
                        resolve(results);
                    }
                },
                reject
            );
        });
    });
}

/**
 * Promise.allSettled - Wait for all promises to settle (resolve or reject).
 */
export function Promise_allSettled(promises) {
    if (typeof Promise.allSettled === 'function') {
        return Promise.allSettled(promises);
    }
    
    // Polyfill for environments without Promise.allSettled
    if (!Array.isArray(promises)) {
        promises = Array.from(promises);
    }
    
    return Promise.all(
        promises.map(promise =>
            Promise.resolve(promise).then(
                value => ({ status: 'fulfilled', value }),
                reason => ({ status: 'rejected', reason })
            )
        )
    );
}

/**
 * Promise.race - Resolve or reject with the first promise that settles.
 */
export function Promise_race(promises) {
    if (typeof Promise.race === 'function') {
        return Promise.race(promises);
    }
    
    // Polyfill for environments without Promise.race
    return new Promise((resolve, reject) => {
        if (!Array.isArray(promises)) {
            promises = Array.from(promises);
        }
        
        promises.forEach(promise => {
            Promise.resolve(promise).then(resolve, reject);
        });
    });
}

/**
 * Promise.any - Resolve with the first promise that resolves, reject if all reject.
 * Throws AggregateError when all promises reject.
 */
export function Promise_any(promises) {
    if (typeof Promise.any === 'function') {
        return Promise.any(promises);
    }
    
    // Polyfill for environments without Promise.any
    if (!Array.isArray(promises)) {
        promises = Array.from(promises);
    }
    
    if (promises.length === 0) {
        return Promise.reject(new AggregateError([], 'No promises provided'));
    }
    
    const errors = [];
    let rejectedCount = 0;
    
    return new Promise((resolve, reject) => {
        promises.forEach((promise, index) => {
            Promise.resolve(promise).then(
                resolve,
                error => {
                    errors[index] = error;
                    rejectedCount++;
                    if (rejectedCount === promises.length) {
                        reject(new AggregateError(errors));
                    }
                }
            );
        });
    });
}

/**
 * Promise.withResolvers - Create a promise with separate resolve/reject functions.
 */
export function Promise_withResolvers() {
    if (typeof Promise.withResolvers === 'function') {
        return Promise.withResolvers();
    }
    
    // Polyfill for environments without Promise.withResolvers
    let resolve, reject;
    const promise = new Promise((res, rej) => {
        resolve = res;
        reject = rej;
    });
    
    return { promise, resolve, reject };
}

/**
 * Export Promise utilities as a namespace.
 */
export const Promise = {
    all: Promise_all,
    allSettled: Promise_allSettled,
    race: Promise_race,
    any: Promise_any,
    withResolvers: Promise_withResolvers,
};

/**
 * Default export for convenience.
 */
export default Promise;

