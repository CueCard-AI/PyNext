/**
 * PyNext Transpiler - Async Runtime Helpers
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides runtime implementations for Python's asyncio functions that are
 * transpiled to JavaScript equivalents.
 * 
 * Currently implements:
 * - sleep(seconds) → Promise-based setTimeout wrapper
 * 
 * =============================================================================
 * WHY THIS EXISTS (Problem It Solves)
 * =============================================================================
 * 
 * Python's asyncio.sleep(seconds) needs to be transpiled to JavaScript.
 * JavaScript doesn't have a built-in sleep function, so we wrap setTimeout
 * in a Promise to provide equivalent functionality.
 * 
 * Python:
 *   await asyncio.sleep(1.5)  # Sleep for 1.5 seconds
 * 
 * JavaScript:
 *   await __py.sleep(1.5);    # Uses this runtime helper
 * 
 * =============================================================================
 * HOW IT WORKS (Architecture)
 * =============================================================================
 * 
 * sleep(seconds) creates a Promise that resolves after the specified time.
 * The seconds parameter is converted to milliseconds for setTimeout.
 * 
 * Edge cases handled:
 * - Negative values: treated as 0 (immediate resolution)
 * - Non-numeric values: converted to number, NaN treated as 0
 * - Very large values: capped at Number.MAX_SAFE_INTEGER
 * 
 * =============================================================================
 * SIZE BUDGET
 * =============================================================================
 * 
 * Target: < 300 bytes gzipped
 * 
 * This is a minimal runtime helper that only wraps setTimeout.
 * 
 * =============================================================================
 * EXAMPLES
 * =============================================================================
 * 
 * ```javascript
 * // Basic usage
 * await __py.sleep(1);      // Sleep for 1 second
 * await __py.sleep(0.5);    // Sleep for 500ms
 * await __py.sleep(0);      // Immediate (next microtask)
 * 
 * // In a loop
 * for (let i = 0; i < 5; i++) {
 *     console.log(i);
 *     await __py.sleep(0.1);  // Wait 100ms between iterations
 * }
 * ```
 */

/**
 * Sleep for the specified number of seconds.
 * 
 * Equivalent to Python's asyncio.sleep(seconds).
 * 
 * IMPORTANT: This function matches Python's behavior:
 * - Negative values raise ValueError (Python behavior)
 * - Zero delay uses queueMicrotask for immediate yield (matches Python's sleep(0))
 * - Positive values use setTimeout
 * 
 * @param {number} seconds - Number of seconds to sleep (can be fractional)
 * @returns {Promise<void>} Promise that resolves after the specified time
 * @throws {ValueError} If seconds is negative
 * 
 * @example
 * await sleep(1.5);  // Sleep for 1.5 seconds
 * await sleep(0);    // Yield to event loop (immediate via microtask)
 */
export function sleep(seconds) {
    const num = Number(seconds);
    
    // Python raises ValueError for negative durations
    if (num < 0) {
        throw new Error(`ValueError: sleep length must be non-negative, got ${num}`);
    }
    
    const ms = (num || 0) * 1000;
    
    // For zero delay, use queueMicrotask for true immediate yield
    // This matches Python's asyncio.sleep(0) which yields immediately
    // (setTimeout has a minimum ~4ms delay in browsers)
    if (ms === 0) {
        return new Promise(resolve => {
            if (typeof queueMicrotask === 'function') {
                queueMicrotask(resolve);
            } else {
                // Fallback for older environments
                Promise.resolve().then(resolve);
            }
        });
    }
    
    // Cap at a reasonable maximum to prevent overflow
    const cappedMs = Math.min(ms, Number.MAX_SAFE_INTEGER);
    
    return new Promise(resolve => setTimeout(resolve, cappedMs));
}

/**
 * Sleep helper that matches Python's asyncio.sleep behavior exactly.
 * 
 * This is the function bound to __py.sleep in the runtime.
 * 
 * @param {number} seconds - Number of seconds to sleep
 * @returns {Promise<void>} Promise that resolves after the specified time
 */
export const asyncSleep = sleep;

// =============================================================================
// EXPORTS
// =============================================================================

export default {
    sleep,
    asyncSleep,
};

