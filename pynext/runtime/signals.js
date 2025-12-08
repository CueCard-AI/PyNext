/**
 * PyNext Runtime - SolidJS-inspired reactive runtime
 * 
 * This minimal runtime (~5KB minified) provides:
 * - createSignal: Reactive primitives
 * - createEffect: Auto-tracking side effects
 * - createMemo: Cached derived values
 * - createStore: Nested reactive objects
 * - Hydration: Connect server-rendered HTML to reactivity
 */

(function(global) {
    'use strict';

    // ============================================
    // Core Reactive System
    // ============================================

    let currentEffect = null;
    let batchDepth = 0;
    const batchQueue = new Set();

    /**
     * Create a reactive signal
     */
    function createSignal(id, initialValue) {
        let value = initialValue;
        const subscribers = new Set();
        const attributeBindings = [];

        const read = () => {
            // Track dependency if we're in an effect
            if (currentEffect) {
                subscribers.add(currentEffect);
                currentEffect.dependencies.add(read);
            }
            return value;
        };

        const write = (newValue) => {
            if (typeof newValue === 'function') {
                newValue = newValue(value);
            }
            if (value !== newValue) {
                value = newValue;
                notify();
            }
        };

        const update = (fn) => {
            write(fn(value));
        };

        const notify = () => {
            // Update DOM bindings
            updateSignalDOM(id, value);
            
            // Update attribute bindings
            for (const binding of attributeBindings) {
                const el = document.getElementById(binding.elementId);
                if (el) {
                    el.setAttribute(binding.attrName, value);
                }
            }

            // Notify subscribers
            for (const effect of subscribers) {
                if (batchDepth > 0) {
                    batchQueue.add(effect);
                } else {
                    effect.execute();
                }
            }
        };

        const signal = {
            id,
            read,
            write,
            set: write,  // Alias for write - matches Python Signal.set()
            update,
            subscribe: (fn) => {
                subscribers.add({ execute: fn, dependencies: new Set() });
                return () => subscribers.delete(fn);
            },
            bindAttribute: (elementId, attrName) => {
                attributeBindings.push({ elementId, attrName });
            }
        };

        // Register in global store
        __pynext__.signals[id] = signal;

        return signal;
    }

    /**
     * Update DOM elements bound to a signal
     */
    function updateSignalDOM(signalId, value) {
        const elements = document.querySelectorAll(`[data-signal="${signalId}"]`);
        for (const el of elements) {
            el.textContent = String(value);
        }
    }

    /**
     * Create a reactive effect
     */
    function createEffect(id, dependencyIds, code) {
        const effect = {
            id,
            dependencies: new Set(),
            cleanup: null,
            execute: () => {
                // Clean up previous run
                if (effect.cleanup) {
                    effect.cleanup();
                    effect.cleanup = null;
                }

                // Clear old dependencies
                effect.dependencies.clear();

                // Run effect with tracking
                const prevEffect = currentEffect;
                currentEffect = effect;
                
                try {
                    if (code) {
                        // Execute provided code
                        const fn = new Function(code);
                        const result = fn();
                        if (typeof result === 'function') {
                            effect.cleanup = result;
                        }
                    }
                } finally {
                    currentEffect = prevEffect;
                }
            }
        };

        // Register in global store
        __pynext__.effects[id] = effect;

        // Run immediately
        effect.execute();

        return effect;
    }

    /**
     * Create a memoized computation
     */
    function createMemo(id, dependencyIds, computeFn) {
        let cachedValue;
        let dirty = true;
        const subscribers = new Set();

        const memo = {
            id,
            dependencies: new Set(),
            read: () => {
                if (currentEffect) {
                    subscribers.add(currentEffect);
                    currentEffect.dependencies.add(memo.read);
                }
                
                if (dirty) {
                    // Recompute
                    const prevEffect = currentEffect;
                    currentEffect = {
                        dependencies: memo.dependencies,
                        execute: () => { dirty = true; notifySubscribers(); }
                    };
                    
                    try {
                        if (typeof computeFn === 'function') {
                            cachedValue = computeFn();
                        }
                    } finally {
                        currentEffect = prevEffect;
                    }
                    dirty = false;
                }
                
                return cachedValue;
            },
            invalidate: () => {
                dirty = true;
            }
        };

        const notifySubscribers = () => {
            for (const effect of subscribers) {
                if (batchDepth > 0) {
                    batchQueue.add(effect);
                } else {
                    effect.execute();
                }
            }
        };

        // Register in global store
        __pynext__.memos[id] = memo;

        return memo;
    }

    /**
     * Create a reactive store for complex nested state
     */
    function createStore(id, initialValue) {
        const subscribers = new Set();
        const listRenderers = new Map();  // path -> {element, renderFn}
        
        const notifyAll = () => {
            // Notify effects
            for (const effect of subscribers) {
                if (batchDepth > 0) {
                    batchQueue.add(effect);
                } else {
                    effect.execute();
                }
            }
            // Re-render any registered lists
            for (const [path, renderer] of listRenderers) {
                const array = getNestedValue(store, path);
                if (Array.isArray(array)) {
                    renderList(renderer.element, array, renderer.renderFn, renderer.keyFn);
                }
            }
        };
        
        const createProxy = (target, path = []) => {
            return new Proxy(target, {
                get(obj, prop) {
                    if (prop === '__isProxy') return true;
                    if (prop === '__path') return path;
                    if (prop === '__store') return store;
                    
                    const value = obj[prop];
                    
                    // Track dependency
                    if (currentEffect && typeof prop !== 'symbol') {
                        subscribers.add(currentEffect);
                        currentEffect.dependencies.add(() => obj[prop]);
                    }
                    
                    // For arrays, wrap mutating methods
                    if (Array.isArray(obj) && typeof value === 'function') {
                        const mutatingMethods = ['push', 'pop', 'shift', 'unshift', 'splice', 'sort', 'reverse'];
                        if (mutatingMethods.includes(prop)) {
                            return function(...args) {
                                const result = Array.prototype[prop].apply(obj, args);
                                notifyAll();
                                return result;
                            };
                        }
                    }
                    
                    // Wrap nested objects
                    if (value && typeof value === 'object' && !value.__isProxy) {
                        return createProxy(value, [...path, prop]);
                    }
                    
                    return value;
                },
                set(obj, prop, value) {
                    if (obj[prop] !== value) {
                        obj[prop] = value;
                        notifyAll();
                    }
                    return true;
                }
            });
        };

        const store = createProxy(initialValue);
        
        // Register in global store
        __pynext__.stores[id] = {
            proxy: store,
            raw: initialValue,
            subscribe: (fn) => {
                const effect = { execute: fn, dependencies: new Set() };
                subscribers.add(effect);
                return () => subscribers.delete(effect);
            },
            // Register a list renderer for reactive list updates
            registerList: (path, element, renderFn, keyFn) => {
                listRenderers.set(path, { element, renderFn, keyFn: keyFn || (item => item.id || JSON.stringify(item)) });
            }
        };

        return store;
    }
    
    /**
     * Get a nested value from an object using a path array
     */
    function getNestedValue(obj, path) {
        let current = obj;
        for (const key of path) {
            if (current == null) return undefined;
            current = current[key];
        }
        return current;
    }
    
    /**
     * Render a list of items to a container element
     */
    function renderList(container, items, renderFn, keyFn) {
        if (!container || !items) return;
        
        const fragment = document.createDocumentFragment();
        
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            const key = keyFn(item);
            const html = renderFn(item, i);
            
            const wrapper = document.createElement('div');
            wrapper.innerHTML = html;
            wrapper.firstElementChild?.setAttribute('data-key', key);
            
            while (wrapper.firstChild) {
                fragment.appendChild(wrapper.firstChild);
            }
        }
        
        container.innerHTML = '';
        container.appendChild(fragment);
    }
    
    /**
     * Register a reactive list that updates when store changes
     */
    function reactiveList(storeId, path, containerId, renderFn, keyFn) {
        const storeData = __pynext__.stores[storeId];
        if (!storeData) {
            console.warn(`[PyNext] Store ${storeId} not found`);
            return;
        }
        
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`[PyNext] Container ${containerId} not found`);
            return;
        }
        
        storeData.registerList(path, container, renderFn, keyFn);
        
        // Initial render
        const items = getNestedValue(storeData.proxy, path);
        if (Array.isArray(items)) {
            renderList(container, items, renderFn, keyFn);
        }
    }

    /**
     * Batch multiple updates
     */
    function batch(fn) {
        batchDepth++;
        try {
            fn();
        } finally {
            batchDepth--;
            if (batchDepth === 0) {
                const effects = [...batchQueue];
                batchQueue.clear();
                for (const effect of effects) {
                    effect.execute();
                }
            }
        }
    }

    // ============================================
    // Server Actions
    // ============================================

    /**
     * Call a server action via RPC
     */
    async function callAction(actionId, event, args = {}) {
        if (event) {
            event.preventDefault();
        }

        try {
            const response = await fetch('/_pynext/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    actionId,
                    args
                })
            });

            if (!response.ok) {
                throw new Error(`Action failed: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            return result.data;
        } catch (error) {
            console.error('Server action error:', error);
            throw error;
        }
    }

    // ============================================
    // Hydration
    // ============================================

    /**
     * Hydrate the page with server-rendered state
     */
    function hydrate() {
        const data = window.__PYNEXT_HYDRATION__;
        if (!data) {
            console.warn('No hydration data found');
            return;
        }

        console.log('[PyNext] Hydrating with data:', data);

        // Create signals
        for (const [id, signalData] of Object.entries(data.signals || {})) {
            createSignal(id, signalData.value);
        }

        // Create stores
        for (const [id, storeData] of Object.entries(data.stores || {})) {
            createStore(id, storeData);
        }

        // Create effects
        for (const [id, effectData] of Object.entries(data.effects || {})) {
            createEffect(id, effectData.dependencies, effectData.code);
        }

        // Attach event handlers
        for (const [elementId, handlers] of Object.entries(data.events || {})) {
            const element = document.getElementById(elementId);
            if (element) {
                for (const [eventType, handlerCode] of Object.entries(handlers)) {
                    try {
                        const handler = new Function('event', handlerCode);
                        element.addEventListener(eventType, handler);
                    } catch (e) {
                        console.error(`Failed to attach ${eventType} handler to ${elementId}:`, e);
                    }
                }
            }
        }

        console.log('[PyNext] Hydration complete');

        // Hydrate React components if bridge is available
        hydrateReactComponents();
    }

    /**
     * Hydrate React components after main hydration
     */
    async function hydrateReactComponents() {
        // Check if React bridge is loaded
        if (global.__pynext_react_bridge__) {
            // Merge React bridge into __pynext__
            __pynext__.react = global.__pynext_react_bridge__;
            delete global.__pynext_react_bridge__;
        }

        // Check for React components on the page
        const reactComponents = document.querySelectorAll('[data-react-component]');
        if (reactComponents.length === 0) {
            return;
        }

        console.log(`[PyNext] Found ${reactComponents.length} React components`);

        // Load React bridge dynamically if needed
        if (!__pynext__.react) {
            try {
                await loadScript('/_pynext/react-bridge.js');
                // Wait a tick for the script to execute
                await new Promise(resolve => setTimeout(resolve, 10));
                
                if (global.__pynext_react_bridge__) {
                    __pynext__.react = global.__pynext_react_bridge__;
                    delete global.__pynext_react_bridge__;
                }
            } catch (e) {
                console.warn('[PyNext] Could not load React bridge:', e);
                return;
            }
        }

        // Hydrate React components
        if (__pynext__.react && __pynext__.react.hydrate) {
            await __pynext__.react.hydrate();
        }
    }

    /**
     * Load a script dynamically
     */
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // ============================================
    // Utilities
    // ============================================

    /**
     * Get a signal by ID
     */
    function getSignal(id) {
        return __pynext__.signals[id];
    }

    /**
     * Get a store by ID
     */
    function getStore(id) {
        return __pynext__.stores[id]?.proxy;
    }

    /**
     * Untrack reads within a function (don't create dependencies)
     */
    function untrack(fn) {
        const prevEffect = currentEffect;
        currentEffect = null;
        try {
            return fn();
        } finally {
            currentEffect = prevEffect;
        }
    }

    /**
     * Run a function on mount (after hydration)
     */
    function onMount(fn) {
        if (document.readyState === 'complete') {
            fn();
        } else {
            window.addEventListener('DOMContentLoaded', fn);
        }
    }

    /**
     * Run a cleanup function on unmount
     */
    function onCleanup(fn) {
        if (currentEffect) {
            const effect = currentEffect;
            const originalCleanup = effect.cleanup;
            effect.cleanup = () => {
                if (originalCleanup) originalCleanup();
                fn();
            };
        }
    }

    // ============================================
    // Global API
    // ============================================

    const __pynext__ = {
        // State storage
        signals: {},
        effects: {},
        memos: {},
        stores: {},
        actions: {},
        resources: new Map(),

        // Core reactivity
        createSignal,
        createEffect,
        createMemo,
        createStore,
        batch,

        // Utilities
        getSignal,
        getStore,
        untrack,
        onMount,
        onCleanup,
        reactiveList,
        renderList,

        // Server communication
        callAction,

        // Hydration
        hydrate,
        hydrateReactComponents,

        // React bridge (populated when loaded)
        react: null,
        
        // Resource support (populated by resource.js)
        ResourceState: null,
        createResource: null,
        hydrateResource: null,
        getResource: null,
        waitForResources: null,
        hasPendingResources: null,
    };

    // Expose globally
    global.__pynext__ = __pynext__;

    // Auto-hydrate when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', hydrate);
    } else {
        // DOM already loaded, hydrate immediately
        setTimeout(hydrate, 0);
    }

})(typeof window !== 'undefined' ? window : global);

