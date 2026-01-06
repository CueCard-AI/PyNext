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
    
    console.log('[PyNext Runtime] Loading...');

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
        // Also check for data-pynext-text bindings
        const textElements = document.querySelectorAll(`[data-pynext-text="${signalId}"]`);
        for (const el of textElements) {
            el.textContent = String(value);
        }
    }

    /**
     * Create a reactive effect
     * 
     * Generalized API supporting multiple call signatures:
     * 
     * 1. createEffect(fn)                    - Anonymous effect with auto-tracking
     * 2. createEffect(id, fn)                - Named effect with auto-tracking  
     * 3. createEffect(id, deps, code)        - Hydration effect with string code
     * 4. createEffect({ id, fn, deps, ... }) - Options object (most flexible)
     * 
     * The options object signature supports:
     * - id: string            - Effect identifier (auto-generated if not provided)
     * - fn: Function          - The effect function to run
     * - code: string          - String code to compile (alternative to fn)
     * - deps: string[]        - Explicit dependency IDs (optional, auto-tracked if not provided)
     * - immediate: boolean    - Run immediately (default: true)
     * - onCleanup: Function   - Cleanup function (also supports returning cleanup from fn)
     */
    function createEffect(idOrFnOrOptions, dependencyIdsOrFn, code) {
        let id;
        let effectFn;
        let immediate = true;
        let explicitCleanup = null;
        
        // Normalize all signatures to a common format
        if (typeof idOrFnOrOptions === 'object' && idOrFnOrOptions !== null && !Array.isArray(idOrFnOrOptions)) {
            // Options object signature: createEffect({ id, fn, ... })
            const opts = idOrFnOrOptions;
            id = opts.id || ('effect_' + Math.random().toString(36).substr(2, 9));
            effectFn = opts.fn;
            immediate = opts.immediate !== false;
            explicitCleanup = opts.onCleanup || null;
            
            // Handle string code
            if (!effectFn && opts.code) {
                try {
                    effectFn = new Function(opts.code);
                } catch (e) {
                    console.error(`[PyNext] Invalid effect code for ${id}:`, e);
                    return null;
                }
            }
        } else if (typeof idOrFnOrOptions === 'function') {
            // createEffect(fn) - anonymous runtime signature
            id = 'effect_' + Math.random().toString(36).substr(2, 9);
            effectFn = idOrFnOrOptions;
        } else if (typeof dependencyIdsOrFn === 'function') {
            // createEffect(id, fn) - named runtime signature
            id = idOrFnOrOptions;
            effectFn = dependencyIdsOrFn;
        } else {
            // createEffect(id, deps, code) - hydration signature with string code
            id = idOrFnOrOptions;
            if (code) {
                try {
                    effectFn = new Function(code);
                } catch (e) {
                    console.error(`[PyNext] Invalid effect code for ${id}:`, e);
                    return null;
                }
            }
        }
        
        const effect = {
            id,
            dependencies: new Set(),
            cleanup: explicitCleanup,
            disposed: false,
            
            execute: () => {
                // Don't run if disposed
                if (effect.disposed) return;
                
                // Clean up previous run
                if (effect.cleanup && typeof effect.cleanup === 'function') {
                    try {
                        effect.cleanup();
                    } catch (e) {
                        console.warn(`[PyNext] Effect cleanup error for ${id}:`, e);
                    }
                    effect.cleanup = explicitCleanup; // Reset to explicit cleanup if any
                }

                // Clear old dependencies for re-tracking
                effect.dependencies.clear();

                // Run effect with tracking
                const prevEffect = currentEffect;
                currentEffect = effect;
                
                try {
                    if (effectFn) {
                        const result = effectFn();
                        // Support returning a cleanup function
                        if (typeof result === 'function') {
                            effect.cleanup = result;
                        }
                    }
                } catch (e) {
                    console.error(`[PyNext] Effect execution error for ${id}:`, e);
                } finally {
                    currentEffect = prevEffect;
                }
            },
            
            // Dispose the effect (remove from tracking, run cleanup)
            dispose: () => {
                effect.disposed = true;
                if (effect.cleanup && typeof effect.cleanup === 'function') {
                    try {
                        effect.cleanup();
                    } catch (e) {
                        console.warn(`[PyNext] Effect dispose cleanup error for ${id}:`, e);
                    }
                }
                effect.cleanup = null;
                effect.dependencies.clear();
                delete __pynext__.effects[id];
            }
        };

        // Register in global store
        __pynext__.effects[id] = effect;

        // Run immediately unless disabled
        if (immediate) {
            effect.execute();
        }

        return effect;
    }
    
    /**
     * Create a two-way binding between a signal and a DOM element
     * 
     * This is a generalized pattern for syncing reactive state with DOM.
     * Works with any element that has a value-like property.
     * 
     * @param {Object} options - Binding configuration
     * @param {string} options.elementId - DOM element ID
     * @param {Object} options.signal - Signal object with get() and set() methods
     * @param {string} options.property - Element property to bind (default: 'value')
     * @param {string} options.event - DOM event to listen for (default: 'input')
     * @param {Function} options.toDOM - Transform value before setting on DOM (optional)
     * @param {Function} options.fromDOM - Transform value from DOM before setting signal (optional)
     * @returns {Object} - Binding object with dispose() method
     */
    function createBinding(options) {
        const {
            elementId,
            signal,
            property = 'value',
            event = 'input',
            toDOM = (v) => v,
            fromDOM = (v) => v,
        } = options;
        
        const element = document.getElementById(elementId);
        if (!element) {
            console.warn(`[PyNext] Binding target not found: #${elementId}`);
            return null;
        }
        
        if (!signal || typeof signal.get !== 'function' || typeof signal.set !== 'function') {
            console.warn(`[PyNext] Invalid signal for binding: #${elementId}`);
            return null;
        }
        
        // Handler for DOM → Signal
        const handleDOMChange = (e) => {
            const rawValue = property === 'checked' ? e.target.checked : e.target[property];
            const value = fromDOM(rawValue);
            signal.set(value);
        };
        
        // Effect for Signal → DOM
        const effect = createEffect(`bind_${elementId}`, () => {
            const value = signal.get();
            const domValue = toDOM(value);
            
            if (property === 'checked') {
                if (element.checked !== domValue) {
                    element.checked = domValue;
                }
            } else {
                if (element[property] !== domValue) {
                    element[property] = domValue;
                }
            }
        });
        
        // Attach DOM listener
        element.addEventListener(event, handleDOMChange);
        
        // Return binding handle with dispose
        return {
            elementId,
            effect,
            dispose: () => {
                element.removeEventListener(event, handleDOMChange);
                effect.dispose();
            }
        };
    }

    /**
     * Create a memoized computation
     * @param {string} id - Internal memo ID (e.g., "memo_5")
     * @param {string[]} dependencyIds - Dependency signal IDs (legacy, not used)
     * @param {Function} computeFn - The computation function
     * @param {string} [name] - Human-readable name for DOM binding (e.g., "total_count")
     */
    function createMemo(id, dependencyIds, computeFn, name) {
        // Use name for DOM lookups, fall back to id
        const domName = name || id;
        let cachedValue;
        let dirty = true;
        const subscribers = new Set();
        
        // FUNDAMENTAL FIX: Create the effect object ONCE, not on every read
        // Previously, a new effect was created on each read, causing infinite subscriber growth
        const memoEffect = {
            dependencies: new Set(),
            execute: () => { 
                dirty = true;
                // Recompute immediately and update DOM
                const newValue = memo.read();
                // Use domName (the human-readable name) for DOM updates
                updateSignalDOM(domName, newValue);
                notifySubscribers(); 
            }
        };

        const memo = {
            id,
            dependencies: memoEffect.dependencies,
            read: () => {
                if (currentEffect) {
                    subscribers.add(currentEffect);
                    currentEffect.dependencies.add(memo.read);
                }
                
                if (dirty) {
                    // Recompute - use the SAME effect object each time
                    const prevEffect = currentEffect;
                    currentEffect = memoEffect;
                    
                    // Clear old dependencies before recompute
                    memoEffect.dependencies.clear();
                    
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
    // Form Hydration
    // ============================================

    /**
     * Built-in validators for form hydration
     */
    const validators = {
        required: (message) => (value) => {
            if (value === null || value === undefined || value === '' || 
                (Array.isArray(value) && value.length === 0)) {
                return message || 'This field is required';
            }
            return null;
        },
        minLength: (length, message) => (value) => {
            if (value === null || value === undefined) return message || `Must be at least ${length} characters`;
            if (String(value).length < length) return message || `Must be at least ${length} characters`;
            return null;
        },
        maxLength: (length, message) => (value) => {
            if (value === null || value === undefined) return null;
            if (String(value).length > length) return message || `Must be at most ${length} characters`;
            return null;
        },
        email: (message) => (value) => {
            if (!value) return null;
            const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            if (!emailPattern.test(value)) return message || 'Must be a valid email address';
            return null;
        },
        pattern: (regex, message) => (value) => {
            if (!value) return null;
            const pattern = new RegExp(regex);
            if (!pattern.test(value)) return message || 'Invalid format';
            return null;
        },
        minValue: (min, message) => (value) => {
            if (value === null || value === undefined || value === '') return null;
            if (Number(value) < min) return message || `Must be at least ${min}`;
            return null;
        },
        maxValue: (max, message) => (value) => {
            if (value === null || value === undefined || value === '') return null;
            if (Number(value) > max) return message || `Must be at most ${max}`;
            return null;
        },
        oneOf: (options, message) => (value) => {
            if (value === null || value === undefined || value === '') return null;
            if (!options.includes(value)) return message || `Must be one of: ${options.join(', ')}`;
            return null;
        },
        url: (message) => (value) => {
            if (!value) return null;
            const urlPattern = /^https?:\/\/(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?(?:\/?|[/?]\S+)$/i;
            if (!urlPattern.test(value)) return message || 'Must be a valid URL';
            return null;
        },
        integer: (message) => (value) => {
            if (value === null || value === undefined || value === '') return null;
            if (!Number.isInteger(Number(value))) return message || 'Must be a whole number';
            return null;
        },
        number: (message) => (value) => {
            if (value === null || value === undefined || value === '') return null;
            if (isNaN(Number(value))) return message || 'Must be a number';
            return null;
        },
        length: (exact, message) => (value) => {
            if (value === null || value === undefined) return message || `Must be exactly ${exact} characters`;
            if (String(value).length !== exact) return message || `Must be exactly ${exact} characters`;
            return null;
        },
    };

    /**
     * Reconstruct validators from serialized format
     */
    function reconstructValidators(serializedValidators) {
        if (!serializedValidators) return {};
        
        const result = {};
        for (const [fieldName, validatorList] of Object.entries(serializedValidators)) {
            result[fieldName] = validatorList.map(v => {
                const factory = validators[v.type];
                if (!factory) {
                    console.warn(`Unknown validator type: ${v.type}`);
                    return () => null;
                }
                // Call factory with args and optional message
                const args = [...(v.args || [])];
                if (v.message) args.push(v.message);
                return factory(...args);
            });
        }
        return result;
    }

    /**
     * Hydrate a single form from serialized data
     */
    function hydrateForm(formData) {
        const initial = formData.initial || {};
        const values = formData.values || {};
        const serializedValidators = formData.validators || {};
        
        // Reconstruct validators
        const formValidators = reconstructValidators(serializedValidators);
        
        // Create form state
        const fields = {};
        const errors = {};
        const touched = {};
        const dirty = {};
        
        for (const [key, value] of Object.entries(initial)) {
            // Create signal for each field with current value (may differ from initial)
            const currentValue = values[key] !== undefined ? values[key] : value;
            const fieldSignal = createSignal(`form_${key}`, currentValue);
            fields[key] = { get: () => fieldSignal.read(), set: (v) => fieldSignal.set(v) };
            
            // Track errors, touched, dirty - createSignal returns an object, not array
            const errorSignal = createSignal(`${key}_error`, formData.errors?.[key] || null);
            errors[key] = [() => errorSignal.read(), (v) => errorSignal.set(v)];
            
            const touchedSignal = createSignal(`${key}_touched`, formData.touched?.[key] || false);
            touched[key] = [() => touchedSignal.read(), (v) => touchedSignal.set(v)];
            
            const dirtySignal = createSignal(`${key}_dirty`, currentValue !== value);
            dirty[key] = [() => dirtySignal.read(), (v) => dirtySignal.set(v)];
        }
        
        // Form API
        const form = {
            _fields: fields,
            _validators: formValidators,
            _initial: initial,
            _errors: errors,
            _touched: touched,
            _dirty: dirty,
            
            // Field access via getter
            get(fieldName) {
                return fields[fieldName]?.get();
            },
            
            set(fieldName, value) {
                if (fields[fieldName]) {
                    fields[fieldName].set(value);
                    dirty[fieldName][1](value !== initial[fieldName]);
                    touched[fieldName][1](true);
                }
            },
            
            // Validate all fields
            validate() {
                let isValid = true;
                for (const [fieldName, fieldValidators] of Object.entries(formValidators)) {
                    const value = fields[fieldName]?.get();
                    for (const validator of fieldValidators) {
                        const error = validator(value);
                        if (error) {
                            errors[fieldName][1](error);
                            isValid = false;
                            break;
                        }
                    }
                    if (isValid) {
                        errors[fieldName][1](null);
                    }
                }
                return isValid;
            },
            
            // Get all values
            get values() {
                const result = {};
                for (const [key, field] of Object.entries(fields)) {
                    result[key] = field.get();
                }
                return result;
            },
            
            // Reset to initial
            reset() {
                for (const [key, value] of Object.entries(initial)) {
                    fields[key].set(value);
                    errors[key][1](null);
                    touched[key][1](false);
                    dirty[key][1](false);
                }
            },
            
            // Computed validity
            get isValid() {
                for (const [fieldName, fieldValidators] of Object.entries(formValidators)) {
                    const value = fields[fieldName]?.get();
                    for (const validator of fieldValidators) {
                        if (validator(value)) return false;
                    }
                }
                return true;
            },
        };
        
        // Add dynamic field access
        return new Proxy(form, {
            get(target, prop) {
                if (prop in target) return target[prop];
                if (target._fields[prop]) {
                    // Return a signal-like object for field access
                    return Object.assign(
                        () => target._fields[prop].get(),
                        { set: (v) => target.set(prop, v) }
                    );
                }
                return undefined;
            }
        });
    }

    /**
     * Bind form fields to DOM elements after hydration
     * 
     * Uses the generalized createBinding() pattern for two-way data binding.
     * Stores bindings for cleanup/disposal when needed.
     */
    function hydrateFormBindings(bindings) {
        // Store bindings for potential cleanup
        const formBindings = [];
        
        for (const [elementId, binding] of Object.entries(bindings)) {
            const { formId, fieldName, bindType } = binding;
            const form = __pynext__.forms[formId];
            if (!form) {
                console.warn(`[PyNext] Form not found for binding: ${formId}`);
                continue;
            }
            
            const field = form._fields[fieldName];
            if (!field) {
                console.warn(`[PyNext] Field not found for binding: ${formId}.${fieldName}`);
                continue;
            }
            
            // Use generalized createBinding for two-way sync
            const bindingHandle = createBinding({
                elementId,
                signal: field,
                property: bindType === 'checked' ? 'checked' : 'value',
                event: 'input',
                // For forms, also notify the form of changes (for validation, dirty tracking)
                fromDOM: (value) => {
                    // Trigger form-level tracking
                    form.set(fieldName, value);
                    return value;
                }
            });
            
            if (bindingHandle) {
                formBindings.push(bindingHandle);
            }
        }
        
        // Store for potential cleanup
        __pynext__._formBindings = formBindings;
        
        return formBindings;
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

        // Inject constants into global scope FIRST
        // These are Python constants (dicts, lists, primitives) that transpiled code needs
        // E.g., STATUS_LABELS = {"backlog": "Backlog", "todo": "Todo", ...}
        if (data.constants) {
            for (const [name, value] of Object.entries(data.constants)) {
                window[name] = value;
                console.log(`[PyNext] Injected constant: ${name}`);
            }
        }

        // Create signals - store by BOTH name and ID for flexible lookup
        // First pass: create signals that are NOT memos
        const memoNames = new Set(Object.keys(data.memos || {}));
        for (const [name, signalData] of Object.entries(data.signals || {})) {
            // Skip memos - they'll be created separately with computation functions
            if (memoNames.has(name)) continue;
            
            const signalId = signalData.id || name;  // Use actual signal ID
            const signal = createSignal(signalId, signalData.value);
            // Also store by name for stable lookup (IDs change each render, names don't)
            if (name && name !== signalId) {
                __pynext__.signals[name] = signal;
            }
            console.log(`[PyNext] Created signal: ${name} -> ${signalId}`);
        }
        
        // Create memos with their computation functions
        for (const [name, memoData] of Object.entries(data.memos || {})) {
            const memoId = memoData.id || name;
            const initialValue = memoData.value;
            const code = memoData.code;
            
            if (code) {
                // Create a real memo with computation function
                try {
                    // The transpiled code is an arrow function like "() => [...]"
                    // new Function('return ' + code) creates a wrapper that returns the arrow fn
                    // We need to call the wrapper to get the actual computation function
                    const wrapper = new Function('return ' + code);
                    const computeFn = wrapper();  // Get the actual arrow function
                    
                    if (typeof computeFn !== 'function') {
                        throw new Error(`Memo code did not return a function: ${typeof computeFn}`);
                    }
                    
                    const memo = createMemo(memoId, [], computeFn, name);
                    // Store by name for lookup
                    __pynext__.signals[name] = memo;
                    // Read the memo once to initialize it and subscribe to dependencies
                    const memoValue = memo.read();
                    console.log(`[PyNext] Created memo: ${name} -> ${memoId} (with computation)`);
                } catch (e) {
                    // Fall back to static signal if computation fails
                    console.warn(`[PyNext] Memo computation failed for ${name}, using static value:`, e);
                    const signal = createSignal(memoId, initialValue);
                    __pynext__.signals[name] = signal;
                    console.log(`[PyNext] Created signal (fallback): ${name} -> ${memoId}`);
                }
            } else {
                // No computation code - create as static signal
                const signal = createSignal(memoId, initialValue);
                __pynext__.signals[name] = signal;
                console.log(`[PyNext] Created signal: ${name} -> ${memoId}`);
            }
        }

        // Create stores
        for (const [id, storeData] of Object.entries(data.stores || {})) {
            createStore(id, storeData);
        }

        // Create effects
        for (const [id, effectData] of Object.entries(data.effects || {})) {
            createEffect(id, effectData.dependencies, effectData.code);
        }

        // Attach event handlers (with modifier support)
        const eventEntries = Object.entries(data.events || {});
        console.log(`[PyNext] Attaching ${eventEntries.length} event handlers...`);
        
        for (const [elementId, handlers] of eventEntries) {
            const element = document.getElementById(elementId);
            if (element) {
                for (const [eventType, handlerData] of Object.entries(handlers)) {
                    try {
                        // Handle both old format (string) and new format ({code, mods})
                        let handlerCode, mods;
                        if (typeof handlerData === 'string') {
                            // Legacy format - just the code
                            handlerCode = handlerData;
                            mods = {};
                        } else {
                            // New format with modifiers
                            handlerCode = handlerData.code;
                            mods = handlerData.mods || {};
                        }
                        
                        console.log(`[PyNext] Attaching ${eventType} to #${elementId}:`, handlerCode.substring(0, 50) + '...', mods);
                        
                        // Create the base handler
                        // Note: The transpiler now adds 'const e = event;' for handlers with 'e' param
                        // No need to add it here - the transpiled code already includes it
                        const baseHandler = new Function('event', handlerCode);
                        
                        // Wrap handler with modifiers
                        const wrappedHandler = (event) => {
                            // self_only: only fire if event.target === event.currentTarget
                            if (mods.self_only && event.target !== event.currentTarget) {
                                return;
                            }
                            // stop: call stopPropagation before handler
                            if (mods.stop) {
                                event.stopPropagation();
                            }
                            // prevent: call preventDefault before handler
                            if (mods.prevent) {
                                event.preventDefault();
                            }
                            // Call the actual handler
                            try {
                                baseHandler(event);
                            } catch (handlerErr) {
                                console.error('[PyNext] Handler error:', handlerErr);
                            }
                        };
                        
                        // Attach with options (once, capture)
                        const options = {};
                        if (mods.once) options.once = true;
                        if (mods.capture) options.capture = true;
                        
                        element.addEventListener(eventType, wrappedHandler, options);
                        console.log(`[PyNext] ✓ Attached ${eventType} to #${elementId}`);
                    } catch (e) {
                        console.error(`[PyNext] ✗ Failed to attach ${eventType} handler to ${elementId}:`, e);
                    }
                }
            } else {
                console.warn(`[PyNext] ✗ Element not found: #${elementId}`);
            }
        }

        // Hydrate forms
        const formEntries = Object.entries(data.forms || {});
        console.log(`[PyNext] Hydrating ${formEntries.length} form(s)...`);
        for (const [formId, formData] of formEntries) {
            try {
                const form = hydrateForm(formData);
                __pynext__.forms[formId] = form;
                console.log(`[PyNext] ✓ Form ${formId} hydrated`);
            } catch (e) {
                console.error(`[PyNext] ✗ Failed to hydrate form ${formId}:`, e);
            }
        }

        // Bind form fields to DOM elements
        hydrateFormBindings(data.formBindings || {});

        // Process reactive bindings
        hydrateBindings(data.bindings || []);

        // FUNDAMENTAL: Initialize toggle-style bindings for buttons
        // This enables reactive highlighting of buttons based on signal values
        initToggleBindings();

        // FUNDAMENTAL: Initialize action bindings for declarative mutations
        // This enables delete, update, toggle operations via data attributes
        initActionBindings();
        
        // FUNDAMENTAL: Attach event handlers from data-pynext-on-* attributes
        // This enables declarative click handlers on buttons (e.g., data-pynext-on-click)
        const pynextRoot = document.getElementById('__pynext') || document.body;
        attachHandlersFromDataAttrs(pynextRoot);

        console.log('[PyNext] Hydration complete');


        // Hydrate React components if bridge is available
        hydrateReactComponents();
    }

    /**
     * FUNDAMENTAL: Initialize toggle-style bindings for buttons/tabs
     * 
     * This is a GENERIC, SCALABLE system for reactive style toggling:
     * - Works with ANY signal name (not hardcoded)
     * - Works with ANY CSS styles (not hardcoded)
     * - Works with dynamically created elements (For loops)
     * - Supports multiple comparison operators (not just equality)
     * - Handles type coercion for numeric comparisons
     * 
     * Elements with data-pynext-toggle-* attributes get reactive style updates:
     * - data-pynext-toggle-signal: Signal name to watch (any signal)
     * - data-pynext-toggle-value: Value to compare against
     * - data-pynext-toggle-op: Comparison operator (default: "eq")
     *     Supported: eq, neq, gt, gte, lt, lte, includes, startsWith, endsWith, truthy, falsy
     * - data-pynext-toggle-active: CSS properties to apply when condition is true
     * - data-pynext-toggle-inactive: CSS properties to apply when condition is false
     * 
     * @param {Element} [root=document] - Root element to scan (for dynamic elements)
     */
    function initToggleBindings(root = document) {
        const toggleElements = root.querySelectorAll('[data-pynext-toggle-signal]');
        
        // Also check if root itself has toggle attributes
        const elementsToProcess = root === document ? 
            toggleElements : 
            (root.hasAttribute?.('data-pynext-toggle-signal') ? 
                [root, ...toggleElements] : toggleElements);
        
        if (elementsToProcess.length === 0) return;
        
        console.log(`[PyNext] Initializing ${elementsToProcess.length} toggle binding(s)...`);
        
        for (const element of elementsToProcess) {
            // Skip if already initialized (prevents duplicate effects)
            if (element.hasAttribute('data-pynext-toggle-initialized')) continue;
            element.setAttribute('data-pynext-toggle-initialized', 'true');
            
            const signalName = element.getAttribute('data-pynext-toggle-signal');
            const targetValue = element.getAttribute('data-pynext-toggle-value');
            const operator = element.getAttribute('data-pynext-toggle-op') || 'eq';
            const activeStyle = element.getAttribute('data-pynext-toggle-active');
            const inactiveStyle = element.getAttribute('data-pynext-toggle-inactive');
            
            if (!signalName) continue;
            // For truthy/falsy operators, value is optional
            if (!targetValue && !['truthy', 'falsy'].includes(operator)) continue;
            
            let signal = __pynext__.signals[signalName];
            if (!signal) {
                // FUNDAMENTAL FIX: Create signal on-the-fly for dynamically added items
                // This handles cases where For loop clones items and creates new signal names
                // that weren't registered during server-side render
                console.log(`[PyNext] Creating signal on-the-fly: ${signalName}`);
                signal = createSignal(signalName, false);
                __pynext__.signals[signalName] = signal;
            }
            
            // Create an effect that updates the element's style when signal changes
            createEffect(() => {
                const currentValue = signal.read();
                const isActive = evaluateToggleCondition(currentValue, targetValue, operator);
                
                // Apply the appropriate styles
                if (isActive && activeStyle) {
                    applyStyleString(element, activeStyle);
                } else if (!isActive && inactiveStyle) {
                    applyStyleString(element, inactiveStyle);
                }
            });
            
            console.log(`[PyNext] ✓ Toggle binding: ${signalName} ${operator} "${targetValue || ''}"`);
        }
    }
    
    /**
     * Evaluate a toggle condition with the specified operator
     * 
     * @param {*} currentValue - Current signal value
     * @param {string} targetValue - Target value from attribute
     * @param {string} operator - Comparison operator
     * @returns {boolean} - Whether the condition is true
     */
    function evaluateToggleCondition(currentValue, targetValue, operator) {
        // Parse target as number if it looks like one (for numeric comparisons)
        const numTarget = targetValue != null && !isNaN(Number(targetValue)) ? Number(targetValue) : null;
        const numCurrent = currentValue != null && !isNaN(Number(currentValue)) ? Number(currentValue) : null;
        
        switch (operator) {
            case 'eq':
            case '==':
            case '===':
                // String comparison (most common for toggles)
                return String(currentValue) === String(targetValue);
                
            case 'neq':
            case '!=':
            case '!==':
                return String(currentValue) !== String(targetValue);
                
            case 'gt':
            case '>':
                return numCurrent !== null && numTarget !== null && numCurrent > numTarget;
                
            case 'gte':
            case '>=':
                return numCurrent !== null && numTarget !== null && numCurrent >= numTarget;
                
            case 'lt':
            case '<':
                return numCurrent !== null && numTarget !== null && numCurrent < numTarget;
                
            case 'lte':
            case '<=':
                return numCurrent !== null && numTarget !== null && numCurrent <= numTarget;
                
            case 'includes':
            case 'contains':
                // Works for both strings and arrays
                if (Array.isArray(currentValue)) {
                    return currentValue.includes(targetValue) || 
                           (numTarget !== null && currentValue.includes(numTarget));
                }
                return String(currentValue).includes(String(targetValue));
                
            case 'startsWith':
                return String(currentValue).startsWith(String(targetValue));
                
            case 'endsWith':
                return String(currentValue).endsWith(String(targetValue));
                
            case 'truthy':
                return Boolean(currentValue);
                
            case 'falsy':
                return !currentValue;
                
            case 'empty':
                // Works for strings, arrays, objects
                if (Array.isArray(currentValue)) return currentValue.length === 0;
                if (typeof currentValue === 'string') return currentValue.length === 0;
                if (typeof currentValue === 'object' && currentValue !== null) {
                    return Object.keys(currentValue).length === 0;
                }
                return !currentValue;
                
            case 'notEmpty':
                if (Array.isArray(currentValue)) return currentValue.length > 0;
                if (typeof currentValue === 'string') return currentValue.length > 0;
                if (typeof currentValue === 'object' && currentValue !== null) {
                    return Object.keys(currentValue).length > 0;
                }
                return Boolean(currentValue);
                
            default:
                console.warn(`[PyNext] Unknown toggle operator: ${operator}`);
                return String(currentValue) === String(targetValue);
        }
    }
    
    /**
     * Apply a CSS style string to an element (merges with existing styles)
     */
    function applyStyleString(element, styleStr) {
        // Parse "property: value; property: value;" format
        const styles = styleStr.split(';').filter(s => s.trim());
        for (const style of styles) {
            const [prop, val] = style.split(':').map(s => s.trim());
            if (prop && val !== undefined) {
                // Convert kebab-case to camelCase for JS style API
                const jsProp = prop.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
                element.style[jsProp] = val;
            }
        }
    }

    /**
     * FUNDAMENTAL: Initialize action bindings for declarative mutations
     * 
     * This handles elements with data-pynext-action-* attributes:
     * - data-pynext-action: Action type (e.g., "delete", "update")
     * - data-pynext-action-signal: Signal name containing the array
     * - data-pynext-action-key: Key to match on (e.g., "id")
     * - data-pynext-action-value: Value to match
     * 
     * @param {Element} [root=document] - Root element to scan
     */
    function initActionBindings(root = document) {
        const actionElements = root.querySelectorAll('[data-pynext-action]');
        
        // Also check if root itself has action attributes
        const elementsToProcess = root === document ? 
            actionElements : 
            (root.hasAttribute?.('data-pynext-action') ? 
                [root, ...actionElements] : actionElements);
        
        if (elementsToProcess.length === 0) return;
        
        console.log(`[PyNext] Initializing ${elementsToProcess.length} action binding(s)...`);
        
        for (const element of elementsToProcess) {
            // Skip if already initialized
            if (element.hasAttribute('data-pynext-action-initialized')) continue;
            element.setAttribute('data-pynext-action-initialized', 'true');
            
            const action = element.getAttribute('data-pynext-action');
            const signalName = element.getAttribute('data-pynext-action-signal');
            const key = element.getAttribute('data-pynext-action-key');
            const value = element.getAttribute('data-pynext-action-value');
            
            if (!action || !signalName) continue;
            
            // Add click handler for the action
            element.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const signal = __pynext__.signals[signalName];
                if (!signal) {
                    console.warn(`[PyNext] Action signal not found: ${signalName}`);
                    return;
                }
                
                const currentValue = signal.read();
                
                switch (action) {
                    case 'delete':
                        // Filter out items where item[key] === value
                        if (Array.isArray(currentValue)) {
                            const numValue = !isNaN(Number(value)) ? Number(value) : value;
                            const newValue = currentValue.filter(item => {
                                const itemVal = item[key];
                                return itemVal !== numValue && String(itemVal) !== String(value);
                            });
                            signal.set(newValue);
                            console.log(`[PyNext] Deleted item with ${key}=${value} from ${signalName}`);
                        }
                        break;
                        
                    case 'toggle':
                        // Toggle a boolean signal
                        signal.set(!currentValue);
                        break;
                        
                    case 'set':
                        // Set to a specific value
                        const numVal = !isNaN(Number(value)) ? Number(value) : value;
                        signal.set(numVal);
                        break;
                        
                    default:
                        console.warn(`[PyNext] Unknown action: ${action}`);
                }
            });
            
            console.log(`[PyNext] ✓ Action binding: ${action} on ${signalName} (${key}=${value})`);
        }
    }

    // ============================================
    // REACTIVE BINDINGS SYSTEM
    // ============================================
    // This is the core of fine-grained DOM updates.
    // Each binding connects a DOM node to one or more signals.
    // When a signal changes, only the affected DOM nodes update.
    // ============================================

    /**
     * Process bindings from hydration data
     */
    function hydrateBindings(bindings) {
        if (!bindings || bindings.length === 0) {
            return;
        }

        console.log(`[PyNext] Processing ${bindings.length} reactive bindings...`);

        for (const binding of bindings) {
            try {
                registerBinding(binding);
            } catch (e) {
                console.error(`[PyNext] Failed to register binding for ${binding.nodeId}:`, e);
            }
        }
    }

    /**
     * Register a reactive binding
     * 
     * Creates an effect that updates the DOM when dependent signals change.
     * 
     * @param {Object} binding - Binding configuration
     * @param {string} binding.nodeId - DOM element ID
     * @param {string} binding.type - Binding type (text, attr, class, style, show, for)
     * @param {string[]} binding.signals - Signal IDs this binding depends on
     * @param {string} binding.update - JavaScript expression to compute new value
     * @param {string} [binding.attr] - Attribute name for attr/class/style bindings
     */
    function registerBinding(binding) {
        const { nodeId, type, signals, update, attr } = binding;
        
        const element = document.getElementById(nodeId);
        if (!element) {
            console.warn(`[PyNext] Binding target not found: #${nodeId}`);
            return;
        }

        // Create an update function from the expression
        let updateFn;
        try {
            updateFn = new Function('return ' + update);
        } catch (e) {
            console.error(`[PyNext] Invalid binding expression for ${nodeId}:`, update, e);
            return;
        }

        // Create effect based on binding type
        switch (type) {
            case 'text':
                createEffect(() => {
                    const value = updateFn();
                    updateText(element, value);
                });
                break;

            case 'attr':
                createEffect(() => {
                    const value = updateFn();
                    updateAttr(element, attr, value);
                });
                break;

            case 'class':
                createEffect(() => {
                    const value = updateFn();
                    updateClass(element, value);
                });
                break;

            case 'style':
                createEffect(() => {
                    const value = updateFn();
                    updateStyle(element, value);
                });
                break;

            case 'show':
                createEffect(() => {
                    const visible = updateFn();
                    updateShow(element, visible);
                });
                break;

            case 'for':
                // For bindings are more complex - handled separately
                registerForBinding(element, binding, updateFn);
                break;

            default:
                console.warn(`[PyNext] Unknown binding type: ${type}`);
        }

        console.log(`[PyNext] ✓ Registered ${type} binding for #${nodeId}`);
    }

    // ============================================
    // DOM UPDATE FUNCTIONS
    // ============================================
    // These functions perform the actual DOM updates.
    // They're designed to be minimal and fast.
    // ============================================

    /**
     * Update text content of an element
     */
    function updateText(element, value) {
        const text = value == null ? '' : String(value);
        if (element.textContent !== text) {
            element.textContent = text;
        }
    }

    /**
     * Update an attribute on an element
     */
    function updateAttr(element, attrName, value) {
        if (value == null || value === false) {
            element.removeAttribute(attrName);
        } else if (value === true) {
            element.setAttribute(attrName, '');
        } else {
            const strValue = String(value);
            if (element.getAttribute(attrName) !== strValue) {
                element.setAttribute(attrName, strValue);
            }
        }
    }

    /**
     * Update class list on an element
     */
    function updateClass(element, value) {
        const className = value == null ? '' : String(value);
        if (element.className !== className) {
            element.className = className;
        }
    }

    /**
     * Update inline styles on an element
     */
    function updateStyle(element, value) {
        if (typeof value === 'string') {
            if (element.style.cssText !== value) {
                element.style.cssText = value;
            }
        } else if (typeof value === 'object' && value !== null) {
            // Object style: { color: 'red', fontSize: '12px' }
            for (const [prop, val] of Object.entries(value)) {
                element.style[prop] = val;
            }
        }
    }

    /**
     * Update visibility of an element (Show component)
     */
    function updateShow(element, visible) {
        const shouldShow = Boolean(visible);
        const currentlyShown = element.style.display !== 'none';
        
        if (shouldShow !== currentlyShown) {
            if (shouldShow) {
                // Restore original display or use block
                const originalDisplay = element.dataset.pynextOriginalDisplay || '';
                element.style.display = originalDisplay;
            } else {
                // Store original display before hiding
                if (element.style.display && element.style.display !== 'none') {
                    element.dataset.pynextOriginalDisplay = element.style.display;
                }
                element.style.display = 'none';
            }
        }
    }

    /**
     * FUNDAMENTAL FIX: Attach event handlers from data-pynext-on-* attributes
     * 
     * This is the core mechanism for making event handlers work in For loops.
     * When elements are cloned from templates, the data attributes travel with them.
     * This function scans for those attributes and attaches the handlers.
     * 
     * Similar to how Alpine.js processes x-on:* directives.
     * 
     * @param {HTMLElement} element - Element to scan (including descendants)
     */
    function attachHandlersFromDataAttrs(element, forItemData = null) {
        // Find all elements with data-pynext-on-* attributes
        const elements = [element, ...element.querySelectorAll('*')];
        
        // If we're inside a For item, get the item data from the closest For wrapper
        // This is used to substitute item-specific values in handlers
        let itemData = forItemData;
        if (!itemData) {
            const forItem = element.closest ? element.closest('[data-for-item]') : null;
            if (forItem) {
                // Try to get item data from the For binding's current state
                const forContainer = forItem.parentElement?.closest('[id^="for_"]');
                const itemKey = forItem.getAttribute('data-for-item');
                // Item data is injected via the forItemData parameter when called from registerForBinding
            }
        }
        
        for (const el of elements) {
            // Get all data attributes
            for (const attr of [...el.attributes]) {
                if (!attr.name.startsWith('data-pynext-on-')) continue;
                
                const eventType = attr.name.replace('data-pynext-on-', '');
                let handlerCode = attr.value
                    .replace(/&quot;/g, '"')
                    .replace(/&#39;/g, "'");
                
                // CRITICAL FIX: If we have For item data, substitute the issue_id in handlers
                // The template uses the first item's id, we need to replace it with the actual item's id
                if (itemData && itemData.id !== undefined) {
                    // Replace hardcoded numeric id in patterns like: __py.at(i, "id"), TEMPLATE_ID)
                    // Look for the pattern and replace the number with the actual item id
                    // This handles: !__py.eq(__py.at(i, "id"), 1) -> !__py.eq(__py.at(i, "id"), 6)
                    handlerCode = handlerCode.replace(
                        /(__py\.at\(i,\s*"id"\),\s*)(\d+)(\))/g,
                        `$1${itemData.id}$3`
                    );
                    // Also update the data attribute so it persists
                    el.setAttribute(attr.name, handlerCode.replace(/"/g, '&quot;'));
                }
                
                // Get modifiers if present
                const modsAttr = el.getAttribute(`data-pynext-mods-${eventType}`);
                let mods = {};
                if (modsAttr) {
                    try {
                        mods = JSON.parse(modsAttr.replace(/&quot;/g, '"'));
                    } catch (e) {}
                }
                
                // Skip if already attached (check for marker)
                const markerAttr = `data-pynext-handler-attached-${eventType}`;
                if (el.hasAttribute(markerAttr)) continue;
                el.setAttribute(markerAttr, 'true');
                
                // Create and attach handler (same logic as hydration)
                try {
                    // Note: The transpiler adds 'const e = event;' for handlers with 'e' param
                    const baseHandler = new Function('event', handlerCode);
                    
                    const handler = (event) => {
                        if (mods.self_only && event.target !== el) return;
                        if (mods.stop) event.stopPropagation();
                        if (mods.prevent) event.preventDefault();
                        
                        try {
                            baseHandler(event);
                        } catch (err) {
                            console.error('[PyNext] Handler error:', err);
                        }
                    };
                    
                    const options = {
                        once: !!mods.once,
                        capture: !!mods.capture,
                    };
                    
                    el.addEventListener(eventType, handler, options);
                } catch (err) {
                    console.error(`[PyNext] Failed to attach ${eventType} handler:`, err);
                }
            }
        }
    }
    
    // Note: attachHandlersFromDataAttrs is exposed later after __pynext__ is defined

    /**
     * Register a For binding for list rendering with array diffing
     * 
     * Implements keyed reconciliation (like SolidJS/React):
     * 1. Track items by unique key
     * 2. Diff new vs old keys
     * 3. Remove deleted items, add new, reorder as needed
     * 
     * FUNDAMENTAL: Uses data-pynext-on-* attributes for event handlers.
     * When items are cloned, handlers are re-attached from these attributes.
     * 
     * @param {HTMLElement} container - The For container element
     * @param {Object} binding - Binding config with initial data
     * @param {Function} eachFn - Function returning current array
     */
    function registerForBinding(container, binding, eachFn) {
        const initialData = binding.initial || {};
        const templateHtml = initialData.template || '';
        
        // Store first item as template for cloning
        let itemTemplate = null;
        const firstItem = container.querySelector('[data-for-item]');
        if (firstItem) {
            itemTemplate = firstItem.cloneNode(true);
        } else if (templateHtml) {
            const temp = document.createElement('div');
            temp.innerHTML = `<div data-for-item="__KEY__">${templateHtml}</div>`;
            itemTemplate = temp.firstElementChild;
        }
        
        // Key extraction: tries id, key, or index
        const getKey = (item, index) => {
            if (item && typeof item === 'object') {
                return item.id ?? item.key ?? index;
            }
            return index;
        };
        
        // Track rendered items: key -> DOM node
        const renderedItems = new Map();
        
        // Initialize with server-rendered items
        container.querySelectorAll('[data-for-item]').forEach(node => {
            const key = node.getAttribute('data-for-item');
            if (key) renderedItems.set(key, node);
        });
        
        createEffect(() => {
            const items = eachFn();
            
            if (!items || !Array.isArray(items)) {
                // Clear all
                for (const [key, node] of renderedItems) {
                    node.remove();
                }
                renderedItems.clear();
                return;
            }
            
            // Build new key -> item map
            const newByKey = new Map();
            const keyOrder = [];
            
            items.forEach((item, index) => {
                const key = String(getKey(item, index));
                newByKey.set(key, { item, index });
                keyOrder.push(key);
            });
            
            // Remove deleted items
            for (const [key, node] of renderedItems) {
                if (!newByKey.has(key)) {
                    node.remove();
                    renderedItems.delete(key);
                }
            }
            
            // Add new / reorder existing
            let prev = null;
            
            for (const key of keyOrder) {
                let node = renderedItems.get(key);
                
                if (!node) {
                    // Create from template
                    if (itemTemplate) {
                        node = itemTemplate.cloneNode(true);
                        node.setAttribute('data-for-item', key);
                        
                        // FUNDAMENTAL FIX: Clear initialization markers so bindings get re-initialized
                        // When cloning, the markers from the template would prevent re-attachment
                        const allElements = [node, ...node.querySelectorAll('*')];
                        for (const el of allElements) {
                            for (const attr of [...el.attributes]) {
                                if (attr.name.startsWith('data-pynext-handler-attached-') ||
                                    attr.name === 'data-pynext-toggle-initialized') {
                                    el.removeAttribute(attr.name);
                                }
                            }
                        }
                        
                        updateNodeWithItem(node, newByKey.get(key).item, newByKey.get(key).index);
                        
                        // FUNDAMENTAL FIX: Attach event handlers from data-pynext-on-* attributes
                        // Pass the item data so handlers can have item-specific values substituted
                        attachHandlersFromDataAttrs(node, newByKey.get(key).item);
                        
                        // FUNDAMENTAL: Initialize toggle bindings for dynamically created elements
                        initToggleBindings(node);
                        
                        // FUNDAMENTAL: Initialize action bindings for dynamically created elements
                        initActionBindings(node);
                    } else {
                        node = document.createElement('div');
                        node.setAttribute('data-for-item', key);
                        node.textContent = JSON.stringify(newByKey.get(key).item);
                    }
                    
                    renderedItems.set(key, node);
                    
                    if (prev) {
                        prev.after(node);
                    } else {
                        container.prepend(node);
                    }
                } else {
                    // Move if needed
                    if (prev && prev.nextElementSibling !== node) {
                        prev.after(node);
                    } else if (!prev && container.firstElementChild !== node) {
                        container.prepend(node);
                    }
                    // Update content
                    updateNodeWithItem(node, newByKey.get(key).item, newByKey.get(key).index);
                }
                
                prev = node;
            }
        });
    }
    
    /**
     * Update a For item node with item data
     * 
     * FUNDAMENTAL DESIGN: Uses data attributes for generic field binding.
     * No application-specific code - everything is driven by data attributes.
     * 
     * Supported patterns:
     * 1. data-pynext-field="fieldName" - Set textContent to item[fieldName]
     * 2. data-pynext-attr-X="fieldName" - Set attribute X to item[fieldName]
     * 3. data-pynext-style-X="fieldName" - Set style.X to item[fieldName]
     * 4. data-X where X matches an item field - Auto-update the data attribute
     * 
     * @param {HTMLElement} node - The item wrapper node
     * @param {Object} item - The item data object
     * @param {number} index - The item's index in the list
     */
    function updateNodeWithItem(node, item, index) {
        if (!item || typeof item !== 'object') return;
        
        node.setAttribute('data-for-index', index);
        
        // Get all elements including node itself
        const allElements = [node, ...node.querySelectorAll('*')];
        
        for (const el of allElements) {
            // Pattern 1: data-pynext-field="fieldName" → textContent
            // FUNDAMENTAL: Uses data-pynext-field-map for value transformation
            // Example: data-pynext-field-map='{"todo":"Todo","done":"Done"}'
            const fieldAttr = el.getAttribute('data-pynext-field');
            if (fieldAttr && item[fieldAttr] !== undefined) {
                let value = item[fieldAttr];
                
                // Check for field value mapping (defined in Python, passed via data attribute)
                const mapAttr = el.getAttribute('data-pynext-field-map');
                if (mapAttr) {
                    try {
                        const fieldMap = JSON.parse(mapAttr.replace(/&quot;/g, '"'));
                        if (fieldMap[value] !== undefined) {
                            value = fieldMap[value];
                        }
                    } catch (e) {
                        console.warn('[PyNext] Invalid field-map JSON:', mapAttr);
                    }
                }
                
                // Check for style mapping (e.g., background color based on value)
                const styleMapAttr = el.getAttribute('data-pynext-style-map');
                if (styleMapAttr) {
                    try {
                        const styleMap = JSON.parse(styleMapAttr.replace(/&quot;/g, '"'));
                        const rawValue = item[fieldAttr];
                        if (styleMap[rawValue]) {
                            for (const [prop, val] of Object.entries(styleMap[rawValue])) {
                                el.style[prop] = val;
                            }
                        }
                    } catch (e) {
                        console.warn('[PyNext] Invalid style-map JSON:', styleMapAttr);
                    }
                }
                
                el.textContent = String(value);
            }
            
            // Pattern 2: data-pynext-attr-X="fieldName" → setAttribute(X, item[fieldName])
            // Pattern 3: data-pynext-style-X="fieldName" → style[X] = item[fieldName]
            for (const attr of [...el.attributes]) {
                if (attr.name.startsWith('data-pynext-attr-')) {
                    const attrName = attr.name.replace('data-pynext-attr-', '');
                    const fieldName = attr.value;
                    if (item[fieldName] !== undefined) {
                        el.setAttribute(attrName, item[fieldName]);
                    }
                } else if (attr.name.startsWith('data-pynext-style-')) {
                    const styleProp = attr.name.replace('data-pynext-style-', '');
                    const fieldName = attr.value;
                    if (item[fieldName] !== undefined) {
                        el.style[styleProp] = item[fieldName];
                    }
                }
            }
            
            // Pattern 4: Auto-update data-* attributes that match item fields
            // e.g., data-issue-id updates from item.id if present
            // Convert data-issue-id to issueId for camelCase lookup
            for (const attr of [...el.attributes]) {
                if (attr.name.startsWith('data-') && 
                    !attr.name.startsWith('data-pynext-') && 
                    !attr.name.startsWith('data-for-')) {
                    
                    // Convert data-issue-id to issueId
                    const dataKey = attr.name.replace('data-', '')
                        .replace(/-([a-z])/g, (_, c) => c.toUpperCase());
                    
                    // Try common mappings: issueId → id, userId → id, itemId → id
                    let value = item[dataKey];
                    if (value === undefined && dataKey.endsWith('Id')) {
                        value = item.id;
                    }
                    
                    if (value !== undefined) {
                        el.setAttribute(attr.name, value);
                    }
                }
            }
        }
        
        // FUNDAMENTAL: Make element IDs unique for each item
        // Use item.id if available, otherwise use index
        const itemKey = item.id ?? item.key ?? index;
        
        const elementsWithId = node.querySelectorAll('[id]');
        elementsWithId.forEach(el => {
            const baseId = el.id.replace(/_item_[\w\d]+$/, ''); // Remove previous suffix
            el.id = `${baseId}_item_${itemKey}`;
        });
        
        if (node.id) {
            const baseId = node.id.replace(/_item_[\w\d]+$/, '');
            node.id = `${baseId}_item_${itemKey}`;
        }
        
        // FUNDAMENTAL FIX: Update data-pynext-toggle-signal and data-pynext-action-value
        // These attributes contain patterns like "issue_1_expanded" that need to be updated
        // to "issue_7_expanded" when the item changes.
        for (const el of allElements) {
            // Update toggle signal names: issue_X_expanded → issue_{item.id}_expanded
            const toggleSignal = el.getAttribute('data-pynext-toggle-signal');
            if (toggleSignal && item.id !== undefined) {
                // Pattern: prefix_NUMBER_suffix → prefix_{newId}_suffix
                const updated = toggleSignal.replace(/_\d+_/, `_${item.id}_`);
                if (updated !== toggleSignal) {
                    el.setAttribute('data-pynext-toggle-signal', updated);
                    // Remove initialized flag so it can be reinitialized with new signal
                    el.removeAttribute('data-pynext-toggle-initialized');
                }
            }
            
            // Update action values: "1" → "{item.id}"
            const actionValue = el.getAttribute('data-pynext-action-value');
            if (actionValue !== null && item.id !== undefined) {
                el.setAttribute('data-pynext-action-value', String(item.id));
                // Remove initialized flag so it can be reinitialized
                el.removeAttribute('data-pynext-action-initialized');
            }
            
            // FUNDAMENTAL FIX: Update onclick handlers that reference signal names
            // Pattern: issue_1_expanded → issue_{item.id}_expanded
            const onclickAttr = el.getAttribute('data-pynext-on-click');
            if (onclickAttr && item.id !== undefined) {
                const updatedOnclick = onclickAttr.replace(/issue_\d+_expanded/g, `issue_${item.id}_expanded`);
                if (updatedOnclick !== onclickAttr) {
                    el.setAttribute('data-pynext-on-click', updatedOnclick);
                    // Re-attach the handler
                    el.removeAttribute('data-pynext-handler-attached-click');
                }
            }
        }
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
     * Get a form by ID
     */
    function getForm(id) {
        return __pynext__.forms[id];
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
        forms: {},  // Form state storage
        resources: new Map(),

        // Core reactivity
        createSignal,
        createEffect,
        createMemo,
        createStore,
        createBinding,
        batch,

        // Utilities
        getSignal,
        getStore,
        getForm,
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
        hydrateForm,
        hydrateFormBindings,
        reconstructValidators,
        
        // Form support
        createForm: (initial, formValidators) => hydrateForm({ initial, values: initial, validators: formValidators }),
        validators,

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
    
    // Expose utility functions defined earlier
    __pynext__.attachHandlersFromDataAttrs = attachHandlersFromDataAttrs;
    __pynext__.initToggleBindings = initToggleBindings;
    __pynext__.initActionBindings = initActionBindings;
    __pynext__.evaluateToggleCondition = evaluateToggleCondition;

    // ==========================================================================
    // PYTHON RUNTIME HELPERS (__py)
    // ==========================================================================
    // These functions provide Python semantics in JavaScript.
    // Used by transpiled code for operations that differ between Python and JS.
    // ==========================================================================

    const __py = {
        // Python negative indexing: arr[-1] -> last element
        at(arr, i) {
            if (arr == null) return undefined;
            if (i < 0) return arr[arr.length + i];
            return arr[i];
        },

        // Python truthiness: [] is falsy, {} is falsy
        bool(val) {
            if (val == null) return false;
            if (val === false || val === 0 || val === '') return false;
            if (Array.isArray(val)) return val.length > 0;
            if (typeof val === 'object') return Object.keys(val).length > 0;
            return true;
        },

        // Python equality: [1,2] == [1,2] is true
        eq(a, b) {
            if (a === b) return true;
            if (a == null || b == null) return a === b;
            if (Array.isArray(a) && Array.isArray(b)) {
                if (a.length !== b.length) return false;
                return a.every((v, i) => __py.eq(v, b[i]));
            }
            if (typeof a === 'object' && typeof b === 'object') {
                const keysA = Object.keys(a);
                const keysB = Object.keys(b);
                if (keysA.length !== keysB.length) return false;
                return keysA.every(k => __py.eq(a[k], b[k]));
            }
            return a === b;
        },

        // Python modulo: always positive result
        mod(a, b) {
            return ((a % b) + b) % b;
        },

        // Python floor division: always floors towards negative infinity
        floordiv(a, b) {
            return Math.floor(a / b);
        },

        // Python 'in' operator: works with strings and arrays
        in(item, container) {
            if (typeof container === 'string') {
                return container.includes(String(item));
            }
            if (Array.isArray(container)) {
                return container.some(x => __py.eq(x, item));
            }
            if (container && typeof container === 'object') {
                return item in container;
            }
            return false;
        },

        // Python addition: handles string concat and list concat
        add(a, b) {
            if (Array.isArray(a) && Array.isArray(b)) {
                return [...a, ...b];
            }
            return a + b;
        },

        // Python multiplication: handles string/list repetition
        mul(a, b) {
            if (typeof a === 'string' && typeof b === 'number') {
                return a.repeat(b);
            }
            if (Array.isArray(a) && typeof b === 'number') {
                const result = [];
                for (let i = 0; i < b; i++) result.push(...a);
                return result;
            }
            return a * b;
        },

        // Python slicing: arr[start:stop:step]
        slice(arr, start, stop, step = 1) {
            if (arr == null) return [];
            const len = arr.length;
            if (start == null) start = step > 0 ? 0 : len - 1;
            if (stop == null) stop = step > 0 ? len : -len - 1;
            if (start < 0) start = Math.max(0, len + start);
            if (stop < 0) stop = Math.max(0, len + stop);

            const result = [];
            if (step > 0) {
                for (let i = start; i < stop && i < len; i += step) {
                    result.push(arr[i]);
                }
            } else {
                for (let i = start; i > stop && i >= 0; i += step) {
                    result.push(arr[i]);
                }
            }
            return typeof arr === 'string' ? result.join('') : result;
        },

        // Python len()
        len(obj) {
            if (obj == null) return 0;
            if (typeof obj.length === 'number') return obj.length;
            if (typeof obj === 'object') return Object.keys(obj).length;
            return 0;
        },

        // Python range()
        range(start, stop, step = 1) {
            if (stop === undefined) { stop = start; start = 0; }
            const result = [];
            if (step > 0) {
                for (let i = start; i < stop; i += step) result.push(i);
            } else {
                for (let i = start; i > stop; i += step) result.push(i);
            }
            return result;
        },

        // Python iter() - ensures iterable is an array for JS methods like .filter()
        iter(obj) {
            if (obj == null) return [];
            if (Array.isArray(obj)) return obj;
            if (typeof obj === 'string') return [...obj];
            if (typeof obj[Symbol.iterator] === 'function') return [...obj];
            if (typeof obj === 'object') return Object.values(obj);
            return [obj];
        },

        // Python contains (for 'x in y')
        contains(item, container) {
            return __py.in(item, container);
        },

        // Python dict operations
        dict: {
            // dict.get(key, default) - returns default if key doesn't exist
            get(obj, key, defaultVal = null) {
                if (obj == null) return defaultVal;
                if (key in obj) return obj[key];
                return defaultVal;
            },
            // dict.keys()
            keys(obj) {
                if (obj == null) return [];
                return Object.keys(obj);
            },
            // dict.values()
            values(obj) {
                if (obj == null) return [];
                return Object.values(obj);
            },
            // dict.items() - returns array of [key, value] pairs
            items(obj) {
                if (obj == null) return [];
                return Object.entries(obj);
            },
            // dict.pop(key, default) - remove and return value
            pop(obj, key, defaultVal = undefined) {
                if (obj == null || !(key in obj)) {
                    if (defaultVal === undefined) {
                        throw new Error(`KeyError: ${key}`);
                    }
                    return defaultVal;
                }
                const val = obj[key];
                delete obj[key];
                return val;
            },
            // dict.update(other) - merge other into obj
            update(obj, other) {
                if (obj == null || other == null) return obj;
                Object.assign(obj, other);
                return obj;
            },
            // dict.setdefault(key, default) - get key or set and return default
            setdefault(obj, key, defaultVal = null) {
                if (obj == null) return defaultVal;
                if (key in obj) return obj[key];
                obj[key] = defaultVal;
                return defaultVal;
            },
        },

        // Python list operations
        list: {
            // list.sort(key=None, reverse=False)
            sort(arr, keyFn = null, reverse = false) {
                if (arr == null) return arr;
                arr.sort((a, b) => {
                    const ka = keyFn ? keyFn(a) : a;
                    const kb = keyFn ? keyFn(b) : b;
                    if (typeof ka === 'string' && typeof kb === 'string') {
                        return reverse ? kb.localeCompare(ka) : ka.localeCompare(kb);
                    }
                    const result = ka < kb ? -1 : (ka > kb ? 1 : 0);
                    return reverse ? -result : result;
                });
                return arr;
            },
        },
    };

    // Expose __py globally for transpiled code
    global.__py = __py;

    // Auto-hydrate when DOM is ready
    console.log('[PyNext Runtime] DOM state:', document.readyState);
    if (document.readyState === 'loading') {
        console.log('[PyNext Runtime] Waiting for DOMContentLoaded...');
        document.addEventListener('DOMContentLoaded', hydrate);
    } else {
        // DOM already loaded, hydrate immediately
        console.log('[PyNext Runtime] DOM ready, hydrating now...');
        setTimeout(hydrate, 0);
    }

})(typeof window !== 'undefined' ? window : global);

