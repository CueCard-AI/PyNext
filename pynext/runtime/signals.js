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
    }

    /**
     * Create a reactive effect
     * 
     * Supports two call signatures:
     * 1. createEffect(fn) - for runtime effects (like bindings)
     * 2. createEffect(id, dependencyIds, code) - for hydration effects
     */
    function createEffect(idOrFn, dependencyIds, code) {
        let id;
        let effectFn;
        
        // Handle both signatures
        if (typeof idOrFn === 'function') {
            // createEffect(fn) - runtime signature
            id = 'effect_' + Math.random().toString(36).substr(2, 9);
            effectFn = idOrFn;
        } else {
            // createEffect(id, deps, code) - hydration signature
            id = idOrFn;
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
                    if (effectFn) {
                        const result = effectFn();
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
     */
    function hydrateFormBindings(bindings) {
        for (const [elementId, binding] of Object.entries(bindings)) {
            const element = document.getElementById(elementId);
            if (!element) continue;
            
            const { formId, fieldName, bindType } = binding;
            const form = __pynext__.forms[formId];
            if (!form) continue;
            
            const field = form._fields[fieldName];
            if (!field) continue;
            
            // Set initial value
            if (bindType === 'checked') {
                element.checked = field.get();
            } else {
                element.value = field.get();
            }
            
            // Listen for changes
            element.addEventListener('input', (e) => {
                const value = bindType === 'checked' ? e.target.checked : e.target.value;
                form.set(fieldName, value);
            });
            
            // Update DOM when signal changes (create effect)
            createEffect(`bind_${elementId}`, () => {
                const value = field.get();
                if (bindType === 'checked') {
                    element.checked = value;
                } else if (element.value !== value) {
                    element.value = value;
                }
            });
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

        // Create signals - store by BOTH name and ID for flexible lookup
        for (const [name, signalData] of Object.entries(data.signals || {})) {
            const signalId = signalData.id || name;  // Use actual signal ID
            const signal = createSignal(signalId, signalData.value);
            // Also store by name for stable lookup (IDs change each render, names don't)
            if (name && name !== signalId) {
                __pynext__.signals[name] = signal;
            }
            console.log(`[PyNext] Created signal: ${name} -> ${signalId}`);
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
                            baseHandler(event);
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

        console.log('[PyNext] Hydration complete');

        // Hydrate React components if bridge is available
        hydrateReactComponents();
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
     * Register a For binding for list rendering with array diffing
     * 
     * Implements keyed reconciliation (like SolidJS/React):
     * 1. Track items by unique key
     * 2. Diff new vs old keys
     * 3. Remove deleted items, add new, reorder as needed
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
                        updateNodeWithItem(node, newByKey.get(key).item, newByKey.get(key).index);
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
     */
    function updateNodeWithItem(node, item, index) {
        if (!item || typeof item !== 'object') return;
        
        node.setAttribute('data-for-index', index);
        
        // Update [data-item-field] elements
        node.querySelectorAll('[data-item-field]').forEach(el => {
            const field = el.getAttribute('data-item-field');
            if (field && item[field] !== undefined) {
                el.textContent = String(item[field]);
            }
        });
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

