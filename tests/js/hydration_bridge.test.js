/**
 * Hydration Bridge Tests - Phase 18 Transpiler ↔ Runtime Integration
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Tests the critical integration between transpiled JavaScript code and the
 * PyNext runtime. These tests verify that:
 * 
 * 1. __pynext__.getSignal() correctly retrieves signals by ID
 * 2. __pynext__.getStore() correctly retrieves stores by ID
 * 3. __pynext__.getForm() correctly retrieves forms by ID
 * 4. Transpiled handlers execute correctly with the runtime
 * 5. Hydration data is correctly parsed and used
 * 6. Signal/Store/Form registration works correctly
 * 
 * =============================================================================
 * RISK AREAS TESTED
 * =============================================================================
 * 
 * 1. Signal ID mismatch between server and client
 * 2. Form field access patterns
 * 3. Store nested property access
 * 4. Hydration state initialization
 * 5. Handler execution with reactive state
 * 
 * =============================================================================
 */

require('./setup');

// =============================================================================
// MOCK RUNTIME SETUP
// =============================================================================
// 
// Create a mock runtime that matches the real signals.js API but allows us to
// test without loading the full runtime.
// =============================================================================

function createMockRuntime() {
    const signals = {};
    const stores = {};
    const forms = {};
    const memos = {};
    
    return {
        signals,
        stores,
        forms,
        memos,
        
        // Signal API
        createSignal: function(id, initialValue) {
            let value = initialValue;
            const subscribers = new Set();
            
            const signal = {
                id,
                read: function() { return value; },
                set: function(newValue) {
                    if (typeof newValue === 'function') {
                        newValue = newValue(value);
                    }
                    if (value !== newValue) {
                        value = newValue;
                        subscribers.forEach(fn => fn(value));
                    }
                },
                update: function(fn) {
                    this.set(fn(value));
                },
                peek: function() { return value; },
                subscribe: function(fn) {
                    subscribers.add(fn);
                    return () => subscribers.delete(fn);
                },
            };
            
            signals[id] = signal;
            return signal;
        },
        
        getSignal: function(id) {
            return signals[id];
        },
        
        // Store API
        createStore: function(id, initialData) {
            const data = typeof initialData === 'object' ? { ...initialData } : initialData;
            
            // Create a proxy for nested property access
            const proxy = new Proxy(data, {
                get(target, prop) {
                    return target[prop];
                },
                set(target, prop, value) {
                    target[prop] = value;
                    return true;
                },
            });
            
            stores[id] = { data, proxy };
            return proxy;
        },
        
        getStore: function(id) {
            return stores[id]?.proxy;
        },
        
        // Form API
        createForm: function(id, fields) {
            const fieldSignals = {};
            const errors = {};
            
            // Create signals for each field
            for (const [name, value] of Object.entries(fields)) {
                const fieldId = `${id}.${name}`;
                fieldSignals[name] = this.createSignal(fieldId, value);
            }
            
            const form = {
                id,
                fields: fieldSignals,
                errors,
                
                // Access form fields directly: form.email, form.name, etc.
                ...Object.keys(fields).reduce((acc, name) => {
                    acc[name] = fieldSignals[name];
                    return acc;
                }, {}),
                
                validate: function() {
                    // Simple mock validation - always returns true
                    return true;
                },
                
                reset: function() {
                    for (const [name, value] of Object.entries(fields)) {
                        fieldSignals[name].set(value);
                    }
                },
                
                get values() {
                    const result = {};
                    for (const [name, signal] of Object.entries(fieldSignals)) {
                        result[name] = signal.read();
                    }
                    return result;
                },
            };
            
            forms[id] = form;
            return form;
        },
        
        getForm: function(id) {
            return forms[id];
        },
        
        // Memo API
        createMemo: function(id, fn) {
            let cached = fn();
            
            const memo = {
                id,
                read: function() { return cached; },
                peek: function() { return cached; },
                invalidate: function() { cached = fn(); },
            };
            
            memos[id] = memo;
            return memo;
        },
        
        getMemo: function(id) {
            return memos[id];
        },
    };
}

// =============================================================================
// TEST: SIGNAL REGISTRATION & RETRIEVAL
// =============================================================================

describe('Signal Registration and Retrieval', () => {
    let runtime;
    
    beforeEach(() => {
        runtime = createMockRuntime();
        global.__pynext__ = runtime;
    });
    
    test('createSignal registers signal with correct ID', () => {
        runtime.createSignal('sig_1', 0);
        
        expect(runtime.signals['sig_1']).toBeDefined();
        expect(runtime.signals['sig_1'].id).toBe('sig_1');
    });
    
    test('getSignal retrieves signal by ID', () => {
        runtime.createSignal('sig_1', 42);
        
        const signal = runtime.getSignal('sig_1');
        
        expect(signal).toBeDefined();
        expect(signal.read()).toBe(42);
    });
    
    test('getSignal returns undefined for unknown ID', () => {
        const signal = runtime.getSignal('unknown_id');
        
        expect(signal).toBeUndefined();
    });
    
    test('signal.set updates value', () => {
        runtime.createSignal('sig_1', 0);
        const signal = runtime.getSignal('sig_1');
        
        signal.set(100);
        
        expect(signal.read()).toBe(100);
    });
    
    test('signal.update applies function to current value', () => {
        runtime.createSignal('sig_1', 10);
        const signal = runtime.getSignal('sig_1');
        
        signal.update(x => x + 5);
        
        expect(signal.read()).toBe(15);
    });
    
    test('signal.set with function applies it to current value', () => {
        runtime.createSignal('sig_1', 20);
        const signal = runtime.getSignal('sig_1');
        
        signal.set(x => x * 2);
        
        expect(signal.read()).toBe(40);
    });
    
    test('multiple signals have unique IDs', () => {
        runtime.createSignal('sig_1', 'first');
        runtime.createSignal('sig_2', 'second');
        runtime.createSignal('sig_3', 'third');
        
        expect(runtime.getSignal('sig_1').read()).toBe('first');
        expect(runtime.getSignal('sig_2').read()).toBe('second');
        expect(runtime.getSignal('sig_3').read()).toBe('third');
    });
    
    test('signal subscribers are notified on change', () => {
        runtime.createSignal('sig_1', 0);
        const signal = runtime.getSignal('sig_1');
        
        let receivedValue = null;
        signal.subscribe(v => { receivedValue = v; });
        
        signal.set(99);
        
        expect(receivedValue).toBe(99);
    });
});

// =============================================================================
// TEST: STORE REGISTRATION & RETRIEVAL
// =============================================================================

describe('Store Registration and Retrieval', () => {
    let runtime;
    
    beforeEach(() => {
        runtime = createMockRuntime();
        global.__pynext__ = runtime;
    });
    
    test('createStore registers store with correct ID', () => {
        runtime.createStore('store_1', { items: [] });
        
        expect(runtime.stores['store_1']).toBeDefined();
    });
    
    test('getStore retrieves store by ID', () => {
        runtime.createStore('store_1', { items: [1, 2, 3] });
        
        const store = runtime.getStore('store_1');
        
        expect(store).toBeDefined();
        expect(store.items).toEqual([1, 2, 3]);
    });
    
    test('getStore returns undefined for unknown ID', () => {
        const store = runtime.getStore('unknown_id');
        
        expect(store).toBeUndefined();
    });
    
    test('store nested property access works', () => {
        runtime.createStore('store_1', {
            user: {
                profile: {
                    name: 'Alice',
                    age: 30,
                },
            },
        });
        
        const store = runtime.getStore('store_1');
        
        expect(store.user.profile.name).toBe('Alice');
        expect(store.user.profile.age).toBe(30);
    });
    
    test('store property mutation works', () => {
        runtime.createStore('store_1', { count: 0 });
        
        const store = runtime.getStore('store_1');
        store.count = 42;
        
        expect(store.count).toBe(42);
    });
});

// =============================================================================
// TEST: FORM REGISTRATION & RETRIEVAL
// =============================================================================

describe('Form Registration and Retrieval', () => {
    let runtime;
    
    beforeEach(() => {
        runtime = createMockRuntime();
        global.__pynext__ = runtime;
    });
    
    test('createForm registers form with correct ID', () => {
        runtime.createForm('form_1', { email: '', name: '' });
        
        expect(runtime.forms['form_1']).toBeDefined();
        expect(runtime.forms['form_1'].id).toBe('form_1');
    });
    
    test('getForm retrieves form by ID', () => {
        runtime.createForm('form_1', { email: 'test@example.com' });
        
        const form = runtime.getForm('form_1');
        
        expect(form).toBeDefined();
        expect(form.email.read()).toBe('test@example.com');
    });
    
    test('getForm returns undefined for unknown ID', () => {
        const form = runtime.getForm('unknown_id');
        
        expect(form).toBeUndefined();
    });
    
    test('form field access works', () => {
        runtime.createForm('form_1', { email: '', password: '' });
        
        const form = runtime.getForm('form_1');
        
        expect(form.email).toBeDefined();
        expect(form.password).toBeDefined();
    });
    
    test('form field set works', () => {
        runtime.createForm('form_1', { email: '' });
        
        const form = runtime.getForm('form_1');
        form.email.set('new@example.com');
        
        expect(form.email.read()).toBe('new@example.com');
    });
    
    test('form validate returns boolean', () => {
        runtime.createForm('form_1', { email: '' });
        
        const form = runtime.getForm('form_1');
        const result = form.validate();
        
        expect(typeof result).toBe('boolean');
    });
    
    test('form reset restores initial values', () => {
        runtime.createForm('form_1', { email: 'initial@example.com' });
        
        const form = runtime.getForm('form_1');
        form.email.set('changed@example.com');
        expect(form.email.read()).toBe('changed@example.com');
        
        form.reset();
        expect(form.email.read()).toBe('initial@example.com');
    });
    
    test('form values getter returns all field values', () => {
        runtime.createForm('form_1', { email: 'a@b.com', name: 'Alice' });
        
        const form = runtime.getForm('form_1');
        const values = form.values;
        
        expect(values).toEqual({ email: 'a@b.com', name: 'Alice' });
    });
});

// =============================================================================
// TEST: TRANSPILED HANDLER EXECUTION
// =============================================================================

describe('Transpiled Handler Execution', () => {
    let runtime;
    
    beforeEach(() => {
        runtime = createMockRuntime();
        global.__pynext__ = runtime;
    });
    
    test('transpiled signal.set() works', () => {
        runtime.createSignal('sig_1', false);
        
        // This is what the transpiler generates for: show.set(True)
        const handler = () => {
            __pynext__.getSignal('sig_1').set(true);
        };
        
        handler();
        
        expect(runtime.getSignal('sig_1').read()).toBe(true);
    });
    
    test('transpiled signal.update() works', () => {
        runtime.createSignal('sig_1', 0);
        
        // This is what the transpiler generates for: count.update(lambda x: x + 1)
        const handler = () => {
            __pynext__.getSignal('sig_1').update(x => x + 1);
        };
        
        handler();
        handler();
        handler();
        
        expect(runtime.getSignal('sig_1').read()).toBe(3);
    });
    
    test('transpiled signal() read works', () => {
        runtime.createSignal('sig_1', 42);
        
        // This is what the transpiler generates for: x = count()
        let x;
        const handler = () => {
            x = __pynext__.getSignal('sig_1').read();
        };
        
        handler();
        
        expect(x).toBe(42);
    });
    
    test('transpiled store access works', () => {
        runtime.createStore('store_1', { items: ['a', 'b', 'c'] });
        
        // This is what the transpiler generates for: x = todos.items
        let x;
        const handler = () => {
            x = __pynext__.getStore('store_1').items;
        };
        
        handler();
        
        expect(x).toEqual(['a', 'b', 'c']);
    });
    
    test('transpiled form.validate() works', () => {
        runtime.createForm('form_1', { email: 'test@example.com' });
        
        // This is what the transpiler generates for: if form.validate():
        let valid;
        const handler = () => {
            valid = __pynext__.getForm('form_1').validate();
        };
        
        handler();
        
        expect(valid).toBe(true);
    });
    
    test('transpiled form.field.set() works', () => {
        runtime.createForm('form_1', { email: '' });
        
        // This is what the transpiler generates for: form.email.set("new@example.com")
        const handler = () => {
            __pynext__.getForm('form_1').email.set('new@example.com');
        };
        
        handler();
        
        expect(runtime.getForm('form_1').email.read()).toBe('new@example.com');
    });
    
    test('transpiled nested reactive pattern works', () => {
        runtime.createStore('store_1', { items: ['a', 'b', 'c'] });
        runtime.createSignal('sig_1', 1);
        
        // This is what the transpiler generates for: x = store.items[idx()]
        let x;
        const handler = () => {
            x = __pynext__.getStore('store_1').items[__pynext__.getSignal('sig_1').read()];
        };
        
        handler();
        expect(x).toBe('b');
        
        // Change the index
        runtime.getSignal('sig_1').set(2);
        handler();
        expect(x).toBe('c');
    });
    
    test('complex handler with multiple operations works', () => {
        runtime.createSignal('sig_1', false);
        runtime.createForm('form_1', { title: '', priority: '' });
        runtime.createStore('store_1', { items: [] });
        
        // This is what the transpiler generates for a complex handler like:
        // def handle_add():
        //     if form.validate():
        //         store.items.append(form.values)
        //         show_form.set(False)
        //         form.reset()
        const handler = () => {
            const form = __pynext__.getForm('form_1');
            if (form.validate()) {
                const store = __pynext__.getStore('store_1');
                store.items.push(form.values);
                __pynext__.getSignal('sig_1').set(false);
                form.reset();
            }
        };
        
        // Set form values first
        runtime.getForm('form_1').title.set('Test Task');
        runtime.getForm('form_1').priority.set('high');
        runtime.getSignal('sig_1').set(true);
        
        handler();
        
        expect(runtime.getSignal('sig_1').read()).toBe(false);
        expect(runtime.getStore('store_1').items.length).toBe(1);
        expect(runtime.getStore('store_1').items[0].title).toBe('Test Task');
    });
});

// =============================================================================
// TEST: HYDRATION DATA PARSING
// =============================================================================

describe('Hydration Data Parsing', () => {
    let runtime;
    
    beforeEach(() => {
        runtime = createMockRuntime();
        global.__pynext__ = runtime;
    });
    
    test('hydration data initializes signals correctly', () => {
        // Simulate __PYNEXT_DATA__ from server
        const hydrationData = {
            components: {
                c1: {
                    signals: {
                        count: 42,
                        visible: true,
                    },
                },
            },
        };
        
        // Hydration logic
        for (const [compId, compData] of Object.entries(hydrationData.components)) {
            if (compData.signals) {
                for (const [name, value] of Object.entries(compData.signals)) {
                    runtime.createSignal(`${compId}_${name}`, value);
                }
            }
        }
        
        expect(runtime.getSignal('c1_count').read()).toBe(42);
        expect(runtime.getSignal('c1_visible').read()).toBe(true);
    });
    
    test('hydration data initializes stores correctly', () => {
        const hydrationData = {
            components: {
                c1: {
                    stores: {
                        todos: { items: [{ id: 1, text: 'Test' }] },
                    },
                },
            },
        };
        
        // Hydration logic
        for (const [compId, compData] of Object.entries(hydrationData.components)) {
            if (compData.stores) {
                for (const [name, value] of Object.entries(compData.stores)) {
                    runtime.createStore(`${compId}_${name}`, value);
                }
            }
        }
        
        const store = runtime.getStore('c1_todos');
        expect(store.items.length).toBe(1);
        expect(store.items[0].text).toBe('Test');
    });
    
    test('large hydration data is handled', () => {
        // Simulate a large store
        const items = [];
        for (let i = 0; i < 1000; i++) {
            items.push({ id: i, text: `Item ${i}` });
        }
        
        runtime.createStore('store_large', { items });
        
        const store = runtime.getStore('store_large');
        expect(store.items.length).toBe(1000);
        expect(store.items[500].text).toBe('Item 500');
    });
});

// =============================================================================
// TEST: ERROR HANDLING
// =============================================================================

describe('Error Handling', () => {
    let runtime;
    
    beforeEach(() => {
        runtime = createMockRuntime();
        global.__pynext__ = runtime;
    });
    
    test('accessing undefined signal does not throw', () => {
        expect(() => {
            const signal = runtime.getSignal('nonexistent');
            // Using optional chaining like real code would
            const value = signal?.read();
        }).not.toThrow();
    });
    
    test('accessing undefined store does not throw', () => {
        expect(() => {
            const store = runtime.getStore('nonexistent');
            const items = store?.items;
        }).not.toThrow();
    });
    
    test('accessing undefined form does not throw', () => {
        expect(() => {
            const form = runtime.getForm('nonexistent');
            const valid = form?.validate();
        }).not.toThrow();
    });
    
    test('handler with undefined signal is safe with optional chaining', () => {
        // Real transpiled code should use optional chaining for safety
        const handler = () => {
            __pynext__.getSignal('nonexistent')?.set(true);
        };
        
        expect(() => handler()).not.toThrow();
    });
});

// =============================================================================
// TEST: MEMO REGISTRATION & RETRIEVAL
// =============================================================================

describe('Memo Registration and Retrieval', () => {
    let runtime;
    
    beforeEach(() => {
        runtime = createMockRuntime();
        global.__pynext__ = runtime;
    });
    
    test('createMemo registers memo with correct ID', () => {
        runtime.createMemo('memo_1', () => 42);
        
        expect(runtime.memos['memo_1']).toBeDefined();
        expect(runtime.memos['memo_1'].id).toBe('memo_1');
    });
    
    test('getMemo retrieves memo by ID', () => {
        runtime.createMemo('memo_1', () => 'computed');
        
        const memo = runtime.getMemo('memo_1');
        
        expect(memo).toBeDefined();
        expect(memo.read()).toBe('computed');
    });
    
    test('getMemo returns undefined for unknown ID', () => {
        const memo = runtime.getMemo('unknown_id');
        
        expect(memo).toBeUndefined();
    });
    
    test('transpiled memo() read works', () => {
        runtime.createSignal('sig_1', 5);
        runtime.createMemo('memo_1', () => runtime.getSignal('sig_1').read() * 2);
        
        // This is what the transpiler generates for: x = doubled()
        let x;
        const handler = () => {
            x = __pynext__.getMemo('memo_1').read();
        };
        
        handler();
        
        expect(x).toBe(10);
    });
});

// =============================================================================
// TEST: ID STABILITY
// =============================================================================

describe('ID Stability', () => {
    let runtime;
    
    beforeEach(() => {
        runtime = createMockRuntime();
        global.__pynext__ = runtime;
    });
    
    test('signal ID remains stable after updates', () => {
        runtime.createSignal('sig_1', 0);
        
        const signal = runtime.getSignal('sig_1');
        signal.set(1);
        signal.set(2);
        signal.set(3);
        
        // ID should not change
        expect(runtime.getSignal('sig_1').id).toBe('sig_1');
    });
    
    test('multiple components use unique IDs', () => {
        // Component 1
        runtime.createSignal('c1_count', 0);
        runtime.createStore('c1_todos', { items: [] });
        
        // Component 2
        runtime.createSignal('c2_count', 0);
        runtime.createStore('c2_todos', { items: [] });
        
        // Update component 1
        runtime.getSignal('c1_count').set(10);
        runtime.getStore('c1_todos').items.push({ id: 1 });
        
        // Component 2 should be unaffected
        expect(runtime.getSignal('c2_count').read()).toBe(0);
        expect(runtime.getStore('c2_todos').items.length).toBe(0);
    });
});
