/**
 * PyNext Runtime - Scheduling APIs
 * 
 * WHAT THIS FILE DOES:
 * Provides browser scheduling APIs (queueMicrotask, requestIdleCallback, requestAnimationFrame)
 * with polyfills for environments that don't support them.
 * 
 * WHY THIS EXISTS:
 * These APIs are essential for efficient client-side code but aren't available everywhere.
 * This provides consistent behavior across all environments.
 * 
 * HOW IT WORKS:
 * - Uses native APIs when available
 * - Provides polyfills for older environments
 * - Maintains consistent API across environments
 * 
 * WHO USES THIS:
 * - Transpiled Python code using scheduling APIs
 * - Client-side code needing scheduling
 * 
 * WHEN TO USE:
 * - queueMicrotask: For high-priority microtasks
 * - requestIdleCallback: For low-priority work during idle time
 * - requestAnimationFrame: For smooth animations
 * 
 * EXAMPLES:
 *     // In Python:
 *     from pynext.client import queue_microtask, request_animation_frame
 *     
 *     queue_microtask(lambda: print("Microtask"))
 *     request_animation_frame(animate)
 */

/**
 * queueMicrotask - Schedule a microtask to run after current task.
 */
export function queueMicrotask(callback) {
    if (typeof globalThis.queueMicrotask === 'function') {
        return globalThis.queueMicrotask(callback);
    }
    
    if (typeof Promise !== 'undefined') {
        // Polyfill using Promise
        Promise.resolve().then(callback);
    } else {
        // Fallback to setTimeout(0)
        setTimeout(callback, 0);
    }
}

/**
 * requestIdleCallback - Schedule callback to run during idle time.
 * Returns a handle that can be used to cancel the callback.
 */
export function requestIdleCallback(callback, options = {}) {
    if (typeof globalThis.requestIdleCallback === 'function') {
        return globalThis.requestIdleCallback(callback, options);
    }
    
    // Polyfill using setTimeout
    const timeout = options.timeout || 5000;
    const start = Date.now();
    
    const timeoutId = setTimeout(() => {
        callback({
            didTimeout: true,
            timeRemaining() {
                return Math.max(0, timeout - (Date.now() - start));
            }
        });
    }, timeout);
    
    // Try to run immediately if possible
    if (typeof globalThis.requestAnimationFrame === 'function') {
        globalThis.requestAnimationFrame(() => {
            if (Date.now() - start < timeout) {
                clearTimeout(timeoutId);
                callback({
                    didTimeout: false,
                    timeRemaining() {
                        return Math.max(0, timeout - (Date.now() - start));
                    }
                });
            }
        });
    }
    
    return timeoutId;
}

/**
 * cancelIdleCallback - Cancel a scheduled idle callback.
 */
export function cancelIdleCallback(handle) {
    if (typeof globalThis.cancelIdleCallback === 'function') {
        return globalThis.cancelIdleCallback(handle);
    }
    
    // Polyfill: clearTimeout for our polyfill
    clearTimeout(handle);
}

/**
 * requestAnimationFrame - Schedule callback to run before next repaint.
 * Returns a handle that can be used to cancel the callback.
 */
export function requestAnimationFrame(callback) {
    if (typeof globalThis.requestAnimationFrame === 'function') {
        return globalThis.requestAnimationFrame(callback);
    }
    
    if (typeof globalThis.webkitRequestAnimationFrame === 'function') {
        return globalThis.webkitRequestAnimationFrame(callback);
    }
    
    if (typeof globalThis.mozRequestAnimationFrame === 'function') {
        return globalThis.mozRequestAnimationFrame(callback);
    }
    
    // Polyfill using setTimeout (60fps = ~16ms)
    return setTimeout(() => {
        callback(Date.now());
    }, 16);
}

/**
 * cancelAnimationFrame - Cancel a scheduled animation frame.
 */
export function cancelAnimationFrame(handle) {
    if (typeof globalThis.cancelAnimationFrame === 'function') {
        return globalThis.cancelAnimationFrame(handle);
    }
    
    if (typeof globalThis.webkitCancelAnimationFrame === 'function') {
        return globalThis.webkitCancelAnimationFrame(handle);
    }
    
    if (typeof globalThis.mozCancelAnimationFrame === 'function') {
        return globalThis.mozCancelAnimationFrame(handle);
    }
    
    // Polyfill: clearTimeout for our polyfill
    clearTimeout(handle);
}

/**
 * Default export with all scheduling functions.
 */
export default {
    queueMicrotask,
    requestIdleCallback,
    cancelIdleCallback,
    requestAnimationFrame,
    cancelAnimationFrame,
};

