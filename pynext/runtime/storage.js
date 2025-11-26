/**
 * PyNext Storage Runtime
 * 
 * Provides localStorage/sessionStorage abstraction with:
 * - Signal synchronization
 * - Cross-tab sync (for localStorage)
 * - Automatic JSON serialization
 * - Default values
 * 
 * Size: ~1KB minified
 */

(function(global) {
    'use strict';

    // ==========================================================================
    // State
    // ==========================================================================

    /** @type {Map<string, Object>} Storage signals */
    const storageSignals = new Map();

    // ==========================================================================
    // Storage Signal
    // ==========================================================================

    /**
     * Create a storage-backed signal.
     * 
     * @param {string} id - Signal ID
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value
     * @param {string} storageType - "local" or "session"
     * @returns {Object} Signal-like object
     */
    function useStorage(id, key, defaultValue, storageType = 'local') {
        // Get storage backend
        const storage = storageType === 'session' ? sessionStorage : localStorage;
        
        // Initialize value from storage or default
        let value;
        try {
            const stored = storage.getItem(key);
            value = stored !== null ? JSON.parse(stored) : defaultValue;
        } catch (e) {
            value = defaultValue;
        }
        
        // Subscribers
        const subscribers = new Set();
        
        // Signal object
        const signal = {
            id,
            key,
            storageType,
            
            read: () => value,
            
            write: (newValue) => {
                if (value !== newValue) {
                    value = newValue;
                    
                    // Persist to storage
                    try {
                        storage.setItem(key, JSON.stringify(newValue));
                    } catch (e) {
                        console.warn(`Failed to persist ${key}:`, e);
                    }
                    
                    // Notify subscribers
                    subscribers.forEach(fn => fn(newValue));
                    
                    // Update DOM bindings
                    updateStorageDOM(id, newValue);
                }
            },
            
            update: (fn) => {
                signal.write(fn(value));
            },
            
            subscribe: (fn) => {
                subscribers.add(fn);
                return () => subscribers.delete(fn);
            },
        };
        
        // Store in registry
        storageSignals.set(id, signal);
        
        // Register with main signals system
        if (window.__pynext__?.signals) {
            window.__pynext__.signals[id] = signal;
        }
        
        log(`Created storage signal: ${key} (${storageType})`);
        
        return signal;
    }

    /**
     * Update DOM elements bound to a storage signal.
     * 
     * @param {string} signalId
     * @param {*} value
     */
    function updateStorageDOM(signalId, value) {
        const elements = document.querySelectorAll(`[data-storage-signal="${signalId}"]`);
        elements.forEach(el => {
            const bindType = el.dataset.storageBind || 'text';
            switch (bindType) {
                case 'text':
                    el.textContent = String(value);
                    break;
                case 'value':
                    el.value = value;
                    break;
                case 'class':
                    el.className = String(value);
                    break;
            }
        });
    }

    /**
     * Get a storage signal by ID.
     * 
     * @param {string} id
     * @returns {Object|null}
     */
    function getStorageSignal(id) {
        return storageSignals.get(id) || null;
    }

    // ==========================================================================
    // Cross-Tab Sync (localStorage only)
    // ==========================================================================

    function setupCrossTabSync() {
        window.addEventListener('storage', (event) => {
            // Find signal with this key
            for (const [id, signal] of storageSignals) {
                if (signal.key === event.key && signal.storageType === 'local') {
                    try {
                        const newValue = JSON.parse(event.newValue);
                        // Update without re-persisting (would cause loop)
                        signal._value = newValue;
                        // Notify subscribers
                        if (signal._subscribers) {
                            signal._subscribers.forEach(fn => fn(newValue));
                        }
                        updateStorageDOM(id, newValue);
                        log(`Cross-tab sync: ${signal.key} = ${newValue}`);
                    } catch (e) {
                        console.warn(`Failed to sync ${signal.key}:`, e);
                    }
                    break;
                }
            }
        });
    }

    // ==========================================================================
    // Direct Storage Access
    // ==========================================================================

    /**
     * Get a value from storage directly.
     * 
     * @param {string} key
     * @param {*} defaultValue
     * @param {string} storageType
     * @returns {*}
     */
    function get(key, defaultValue = null, storageType = 'local') {
        const storage = storageType === 'session' ? sessionStorage : localStorage;
        try {
            const stored = storage.getItem(key);
            return stored !== null ? JSON.parse(stored) : defaultValue;
        } catch (e) {
            return defaultValue;
        }
    }

    /**
     * Set a value in storage directly.
     * 
     * @param {string} key
     * @param {*} value
     * @param {string} storageType
     */
    function set(key, value, storageType = 'local') {
        const storage = storageType === 'session' ? sessionStorage : localStorage;
        try {
            storage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.warn(`Failed to set ${key}:`, e);
        }
    }

    /**
     * Remove a value from storage.
     * 
     * @param {string} key
     * @param {string} storageType
     */
    function remove(key, storageType = 'local') {
        const storage = storageType === 'session' ? sessionStorage : localStorage;
        storage.removeItem(key);
    }

    // ==========================================================================
    // Logging
    // ==========================================================================

    const DEBUG = typeof window !== 'undefined' && window.__PYNEXT_DEBUG__;

    function log(...args) {
        if (DEBUG) {
            console.log('[PyNext Storage]', ...args);
        }
    }

    // ==========================================================================
    // Initialization
    // ==========================================================================

    function init() {
        setupCrossTabSync();
        log('Storage runtime initialized');
    }

    /**
     * Initialize from hydration data.
     * 
     * @param {Object[]} storageConfigs
     */
    function hydrate(storageConfigs) {
        if (!storageConfigs) return;
        
        storageConfigs.forEach(config => {
            useStorage(config.id, config.key, config.default, config.storageType);
        });
        
        log(`Hydrated ${storageConfigs.length} storage signals`);
    }

    // ==========================================================================
    // Export
    // ==========================================================================

    if (typeof window !== 'undefined') {
        window.__pynext__ = window.__pynext__ || {};
        
        // API
        window.__pynext__.storage = {
            useStorage,
            getStorageSignal,
            get,
            set,
            remove,
            hydrate,
        };
        
        // Also expose useStorage at top level for convenience
        window.__pynext__.useStorage = useStorage;

        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
    }

    // Module exports
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            useStorage,
            getStorageSignal,
            get,
            set,
            remove,
            hydrate,
        };
    }

})(typeof window !== 'undefined' ? window : global);

