/**
 * PyNext Transpiler - Proxy Wrappers for Dunder Methods
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides optimized Proxy wrappers for Python dunder methods that require
 * dynamic property access:
 * - __getitem__ / __setitem__ / __delitem__ (subscript access)
 * - __getattr__ / __setattr__ / __delattr__ (attribute access)
 * 
 * These enable Pythonic syntax like obj[key] and obj.attr to work correctly
 * in JavaScript.
 * 
 * =============================================================================
 * WHY THIS EXISTS (Problem It Solves)
 * =============================================================================
 * 
 * Python allows customizing subscript and attribute access via dunder methods:
 * - obj[key] calls obj.__getitem__(key)
 * - obj.attr calls obj.__getattr__(attr) if attr doesn't exist
 * 
 * JavaScript doesn't have this, so we use Proxy to intercept:
 * - Property access (get trap)
 * - Property assignment (set trap)
 * - Property deletion (deleteProperty trap)
 * 
 * Optimization: We only wrap objects that actually define these methods to
 * minimize Proxy overhead.
 * 
 * =============================================================================
 * SIZE BUDGET
 * =============================================================================
 * 
 * Target: < 600 bytes gzipped
 * 
 * Proxy wrappers are only created when needed (lazy wrapping).
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * The transpiler automatically wraps objects with dunder methods:
 * 
 *   class MyDict:
 *       def __getitem__(self, key):
 *           return self._data[key]
 *   
 *   # Transpiles to:
 *   class MyDict {
 *       __getitem__(key) {
 *           return this._data[key];
 *       }
 *   }
 *   
 *   # Usage automatically uses Proxy:
 *   const d = new Proxy(new MyDict(), createSubscriptProxy());
 *   d["key"]  // → calls __getitem__("key")
 */

import {
    KeyError,
    AttributeError,
} from './errors.js';

// =============================================================================
// SUBSCRIPT ACCESS (__getitem__, __setitem__, __delitem__)
// =============================================================================

/**
 * Create a Proxy handler for subscript access (obj[key]).
 * 
 * Handles:
 * - __getitem__(key) for obj[key]
 * - __setitem__(key, value) for obj[key] = value
 * - __delitem__(key) for del obj[key]
 * 
 * @param {object} target - Object to wrap
 * @returns {Proxy} Proxy object with subscript access
 * 
 * @example
 * const obj = { __getitem__(k) { return this._data[k]; } };
 * const proxied = new Proxy(obj, createSubscriptProxy());
 * proxied["key"]  // → calls obj.__getitem__("key")
 */
export function createSubscriptProxy(target) {
    return {
        get(target, prop, receiver) {
            // If property exists directly, return it
            if (prop in target) {
                return Reflect.get(target, prop, receiver);
            }
            
            // Try __getitem__ for subscript access
            if (typeof target.__getitem__ === 'function') {
                return target.__getitem__(prop);
            }
            
            // Fallback: undefined
            return undefined;
        },
        
        set(target, prop, value, receiver) {
            // If property exists directly, set it
            if (prop in target) {
                return Reflect.set(target, prop, value, receiver);
            }
            
            // Try __setitem__ for subscript assignment
            if (typeof target.__setitem__ === 'function') {
                target.__setitem__(prop, value);
                return true;
            }
            
            // Fallback: direct assignment
            return Reflect.set(target, prop, value, receiver);
        },
        
        deleteProperty(target, prop) {
            // If property exists directly, delete it
            if (prop in target) {
                return Reflect.deleteProperty(target, prop);
            }
            
            // Try __delitem__ for subscript deletion
            if (typeof target.__delitem__ === 'function') {
                target.__delitem__(prop);
                return true;
            }
            
            // Fallback: delete
            return Reflect.deleteProperty(target, prop);
        },
        
        has(target, prop) {
            // Check if property exists
            if (prop in target) {
                return true;
            }
            
            // Try __contains__ if available
            if (typeof target.__contains__ === 'function') {
                return target.__contains__(prop);
            }
            
            // Try __getitem__ to see if key exists (may throw KeyError)
            if (typeof target.__getitem__ === 'function') {
                try {
                    target.__getitem__(prop);
                    return true;
                } catch (e) {
                    if (e instanceof KeyError) {
                        return false;
                    }
                    throw e;
                }
            }
            
            return false;
        },
    };
}

// =============================================================================
// ATTRIBUTE ACCESS (__getattr__, __setattr__, __delattr__)
// =============================================================================

/**
 * Create a Proxy handler for attribute access (obj.attr).
 * 
 * Handles Python's attribute access protocol:
 * - __getattr__(name): Called ONLY when attr doesn't exist (fallback)
 * - __setattr__(name, value): Called for EVERY attribute assignment (Python behavior)
 * - __delattr__(name): Called for EVERY attribute deletion (Python behavior)
 * 
 * IMPORTANT: This matches Python's semantics where:
 * - __getattr__ is only called as a fallback for missing attributes
 * - __setattr__ is ALWAYS called for any attribute assignment
 * - __delattr__ is ALWAYS called for any attribute deletion
 * 
 * @param {object} target - Object to wrap
 * @returns {object} Proxy handler for attribute access
 * 
 * @example
 * const obj = { __getattr__(name) { return this._data[name]; } };
 * const proxied = new Proxy(obj, createAttributeProxy(obj));
 * proxied.attr  // → calls obj.__getattr__("attr") if attr not found
 */
export function createAttributeProxy(target) {
    // Cache whether target defines these methods for performance
    const hasSetattr = typeof target.__setattr__ === 'function';
    const hasDelattr = typeof target.__delattr__ === 'function';
    const hasGetattr = typeof target.__getattr__ === 'function';
    
    return {
        get(target, prop, receiver) {
            // Skip special properties and symbols
            if (typeof prop === 'symbol' || 
                prop === '__proto__' || 
                prop === 'constructor' || 
                prop === 'prototype') {
                return Reflect.get(target, prop, receiver);
            }
            
            // If property exists directly, return it (normal lookup)
            if (prop in target || Object.prototype.hasOwnProperty.call(target, prop)) {
                return Reflect.get(target, prop, receiver);
            }
            
            // __getattr__ is only called for MISSING attributes (Python behavior)
            if (hasGetattr) {
                try {
                    return target.__getattr__(prop);
                } catch (e) {
                    if (e instanceof AttributeError) {
                        return undefined;
                    }
                    throw e;
                }
            }
            
            // Fallback: undefined
            return undefined;
        },
        
        set(target, prop, value, receiver) {
            // Skip special properties and symbols
            if (typeof prop === 'symbol' || 
                prop === '__proto__' || 
                prop === 'constructor' || 
                prop === 'prototype') {
                return Reflect.set(target, prop, value, receiver);
            }
            
            // Python: __setattr__ is ALWAYS called for attribute assignment
            // This is different from __getattr__ which is only for missing attributes
            if (hasSetattr) {
                target.__setattr__(prop, value);
                return true;
            }
            
            // Fallback: direct assignment
            return Reflect.set(target, prop, value, receiver);
        },
        
        deleteProperty(target, prop) {
            // Skip symbols
            if (typeof prop === 'symbol') {
                return Reflect.deleteProperty(target, prop);
            }
            
            // Python: __delattr__ is ALWAYS called for attribute deletion
            if (hasDelattr) {
                try {
                    target.__delattr__(prop);
                    return true;
                } catch (e) {
                    if (e instanceof AttributeError) {
                        return false;
                    }
                    throw e;
                }
            }
            
            // Fallback: delete
            return Reflect.deleteProperty(target, prop);
        },
        
        has(target, prop) {
            // Check if property exists
            if (prop in target || Object.prototype.hasOwnProperty.call(target, prop)) {
                return true;
            }
            
            // Try __getattr__ to see if attribute exists (may throw AttributeError)
            if (hasGetattr) {
                try {
                    target.__getattr__(prop);
                    return true;
                } catch (e) {
                    if (e instanceof AttributeError) {
                        return false;
                    }
                    throw e;
                }
            }
            
            return false;
        },
    };
}

// =============================================================================
// COMBINED PROXY (Both Subscript and Attribute Access)
// =============================================================================

/**
 * Create a Proxy handler that supports both subscript and attribute access.
 * 
 * This is used when an object defines both __getitem__ and __getattr__.
 * 
 * @param {object} target - Object to wrap
 * @returns {Proxy} Proxy object with both access types
 */
export function createCombinedProxy(target) {
    const subscriptHandler = createSubscriptProxy(target);
    const attributeHandler = createAttributeProxy(target);
    
    return {
        get(target, prop, receiver) {
            // Try subscript first (for numeric/string keys)
            const subscriptResult = subscriptHandler.get(target, prop, receiver);
            if (subscriptResult !== undefined) {
                return subscriptResult;
            }
            
            // Then try attribute
            return attributeHandler.get(target, prop, receiver);
        },
        
        set(target, prop, value, receiver) {
            // Try subscript first
            if (typeof target.__setitem__ === 'function') {
                return subscriptHandler.set(target, prop, value, receiver);
            }
            
            // Then try attribute
            return attributeHandler.set(target, prop, value, receiver);
        },
        
        deleteProperty(target, prop) {
            // Try subscript first
            if (typeof target.__delitem__ === 'function') {
                return subscriptHandler.deleteProperty(target, prop);
            }
            
            // Then try attribute
            return attributeHandler.deleteProperty(target, prop);
        },
        
        has(target, prop) {
            return subscriptHandler.has(target, prop) || attributeHandler.has(target, prop);
        },
    };
}

// =============================================================================
// EXPORTS
// =============================================================================

export const proxy = {
    createSubscriptProxy,
    createAttributeProxy,
    createCombinedProxy,
};

