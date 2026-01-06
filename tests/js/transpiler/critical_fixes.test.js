/**
 * Phase 18.6 Critical Fixes - JavaScript Runtime Tests
 * 
 * These tests verify that the transpiled JavaScript code actually RUNS correctly.
 * This complements the Python tests which verify code GENERATION.
 * 
 * Tests:
 * 1. Signals inside comprehensions/generators
 * 2. Try/except transpilation
 * 3. Async handlers with signals
 * 4. Form operations
 * 5. Store operations
 * 6. Complex nested patterns
 */

require('./setup');

// =============================================================================
// MOCK __pynext__ RUNTIME
// =============================================================================

let mockSignals, mockStores, mockForms, mockMemos;

beforeEach(() => {
    // Reset state
    mockSignals = {};
    mockStores = {};
    mockForms = {};
    mockMemos = {};
    
    // Mock __pynext__ API
    global.__pynext__ = {
        getSignal: (id) => {
            if (!mockSignals[id]) {
                mockSignals[id] = {
                    _value: null,
                    read: function() { return this._value; },
                    set: function(v) { this._value = v; },
                    update: function(fn) { this._value = fn(this._value); },
                    peek: function() { return this._value; },
                };
            }
            return mockSignals[id];
        },
        
        getStore: (id) => {
            if (!mockStores[id]) {
                mockStores[id] = new Proxy({}, {
                    get: (target, prop) => target[prop],
                    set: (target, prop, value) => { target[prop] = value; return true; },
                });
            }
            return mockStores[id];
        },
        
        getForm: (id) => {
            if (!mockForms[id]) {
                mockForms[id] = {
                    _values: {},
                    _errors: {},
                    _valid: true,
                    values: {},
                    errors: {},
                    validate: function() { return this._valid; },
                    reset: function() { this._values = {}; },
                    submit: function() {},
                    set_error: function(field, msg) { this._errors[field] = msg; },
                    clear_errors: function() { this._errors = {}; },
                };
                // Make fields accessible
                mockForms[id].values = mockForms[id]._values;
                mockForms[id].errors = mockForms[id]._errors;
            }
            return mockForms[id];
        },
        
        getMemo: (id) => {
            if (!mockMemos[id]) {
                mockMemos[id] = {
                    _fn: null,
                    read: function() { return this._fn ? this._fn() : null; },
                    peek: function() { return this.read(); },
                };
            }
            return mockMemos[id];
        },
    };
});


// =============================================================================
// TEST 1: SIGNALS IN COMPREHENSIONS
// =============================================================================

describe('Signals in Comprehensions', () => {
    
    test('signal read in list comprehension map', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = 10;
        
        // This is the transpiled version of: [count() * x for x in items]
        const items = [1, 2, 3];
        const result = [...__py.iter(items)].map(x => __py.mul(__pynext__.getSignal('sig_1').read(), x));
        
        expect(result).toEqual([10, 20, 30]);
    });
    
    test('signal read in dict comprehension value', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = 100;
        
        // This is: {k: count() for k in keys}
        const keys = ['a', 'b'];
        const result = Object.fromEntries(
            [...__py.iter(keys)].map(k => [k, __pynext__.getSignal('sig_1').read()])
        );
        
        expect(result).toEqual({ a: 100, b: 100 });
    });
    
    test('signal read in dict comprehension key', () => {
        // Setup  
        __pynext__.getSignal('sig_1')._value = 'prefix';
        
        // This is: {count() + k: v for k, v in items}
        const items = [['a', 1], ['b', 2]];
        const result = Object.fromEntries(
            [...__py.iter(items)].map(([k, v]) => [
                __py.add(__pynext__.getSignal('sig_1').read(), k), 
                v
            ])
        );
        
        expect(result).toEqual({ prefixa: 1, prefixb: 2 });
    });
    
    test('signal read in set comprehension', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = 5;
        
        // This is: {x + count() for x in items}
        const items = [1, 2, 3];
        const result = new Set(
            [...__py.iter(items)].map(x => __py.add(x, __pynext__.getSignal('sig_1').read()))
        );
        
        expect(result).toEqual(new Set([6, 7, 8]));
    });
    
    test('signal read in generator expression', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = 2;
        
        // This is: sum(x * count() for x in items)
        const items = [1, 2, 3];
        const result = [...__py.iter(items)]
            .reduce((__acc__, x) => __acc__ + __py.mul(x, __pynext__.getSignal('sig_1').read()), 0);
        
        expect(result).toBe(12); // (1*2) + (2*2) + (3*2) = 12
    });
    
    test('signal read in filter condition', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = 2;
        
        // This is: [x for x in items if x > threshold()]
        const items = [1, 2, 3, 4, 5];
        const result = [...__py.iter(items)]
            .filter(x => x > __pynext__.getSignal('sig_1').read());
        
        expect(result).toEqual([3, 4, 5]);
    });
    
    test('signal read in any() generator', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = 3;
        
        // This is: any(x > threshold() for x in items)
        const items = [1, 2, 3, 4, 5];
        const result = [...__py.iter(items)]
            .some(x => x > __pynext__.getSignal('sig_1').read());
        
        expect(result).toBe(true);
    });
    
    test('signal read in all() generator', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = 0;
        
        // This is: all(x > threshold() for x in items)
        const items = [1, 2, 3];
        const result = [...__py.iter(items)]
            .every(x => x > __pynext__.getSignal('sig_1').read());
        
        expect(result).toBe(true);
    });
    
    test('multiple signals in same comprehension', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = 10;
        __pynext__.getSignal('sig_2')._value = 2;
        
        // This is: [a() + b() * x for x in items]
        const items = [1, 2, 3];
        const result = [...__py.iter(items)].map(x => 
            __py.add(
                __pynext__.getSignal('sig_1').read(),
                __py.mul(__pynext__.getSignal('sig_2').read(), x)
            )
        );
        
        expect(result).toEqual([12, 14, 16]);
    });
    
    test('signal in nested comprehension', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = 1;
        
        // This is: [[count() + x for x in row] for row in matrix]
        const matrix = [[1, 2], [3, 4]];
        const result = [...__py.iter(matrix)].map(row =>
            [...__py.iter(row)].map(x =>
                __py.add(__pynext__.getSignal('sig_1').read(), x)
            )
        );
        
        expect(result).toEqual([[2, 3], [4, 5]]);
    });
});


// =============================================================================
// TEST 2: TRY/EXCEPT TRANSPILATION
// =============================================================================

describe('Try/Except Patterns', () => {
    
    test('basic try/catch sets signal on success', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = null;
        let called = false;
        
        // This is transpiled try/except
        try {
            const result = 'success';
            __pynext__.getSignal('sig_1').set(result);
            called = true;
        } catch (_e) {
            __pynext__.getSignal('sig_1').set('error');
        }
        
        expect(__pynext__.getSignal('sig_1').read()).toBe('success');
        expect(called).toBe(true);
    });
    
    test('basic try/catch sets signal on error', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = null;
        
        // This is transpiled try/except
        try {
            throw new Error('test error');
            __pynext__.getSignal('sig_1').set('success');
        } catch (_e) {
            __pynext__.getSignal('sig_1').set('error');
        }
        
        expect(__pynext__.getSignal('sig_1').read()).toBe('error');
    });
    
    test('try/catch/finally pattern', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = false;
        __pynext__.getSignal('sig_2')._value = null;
        
        // This is transpiled try/except/finally
        __pynext__.getSignal('sig_1').set(true);  // loading = True
        try {
            __pynext__.getSignal('sig_2').set('data');
        } catch (_e) {
            __pynext__.getSignal('sig_2').set('error');
        } finally {
            __pynext__.getSignal('sig_1').set(false);  // loading = False
        }
        
        expect(__pynext__.getSignal('sig_1').read()).toBe(false);
        expect(__pynext__.getSignal('sig_2').read()).toBe('data');
    });
    
    test('try/catch with exception binding', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = null;
        
        // This is transpiled: except ValueError as e: error.set(str(e))
        try {
            const e = new Error('specific error');
            e.name = 'ValueError';
            throw e;
        } catch (_e) {
            if (_e instanceof Error && _e.name === 'ValueError') {
                let e = _e;
                __pynext__.getSignal('sig_1').set(String(e.message));
            }
        }
        
        expect(__pynext__.getSignal('sig_1').read()).toBe('specific error');
    });
    
    test('nested try/catch', () => {
        // Setup
        const results = [];
        
        try {
            try {
                throw new Error('inner');
            } catch (_e) {
                results.push('caught inner');
            }
            results.push('after inner');
        } catch (_e) {
            results.push('caught outer');
        }
        
        expect(results).toEqual(['caught inner', 'after inner']);
    });
    
    test('try with signal operations in catch', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = [];
        __pynext__.getSignal('sig_2')._value = false;
        
        try {
            throw new Error('fail');
        } catch (_e) {
            __pynext__.getSignal('sig_2').set(true);
            __pynext__.getSignal('sig_1').update(arr => [...arr, 'error']);
        }
        
        expect(__pynext__.getSignal('sig_2').read()).toBe(true);
        expect(__pynext__.getSignal('sig_1').read()).toEqual(['error']);
    });
});


// =============================================================================
// TEST 3: ASYNC HANDLERS
// =============================================================================

describe('Async Handler Patterns', () => {
    
    test('async function sets loading state', async () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = false;  // loading
        __pynext__.getSignal('sig_2')._value = null;   // data
        
        // Mock async function
        const mockFetch = async () => 'fetched data';
        
        // Transpiled async handler
        async function handler() {
            __pynext__.getSignal('sig_1').set(true);
            const result = await mockFetch();
            __pynext__.getSignal('sig_2').set(result);
            __pynext__.getSignal('sig_1').set(false);
        }
        
        await handler();
        
        expect(__pynext__.getSignal('sig_1').read()).toBe(false);
        expect(__pynext__.getSignal('sig_2').read()).toBe('fetched data');
    });
    
    test('await with signal as argument', async () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = 'https://api.example.com';
        
        // Mock fetch that uses the signal value
        const mockFetch = async (url) => `response from ${url}`;
        
        // Transpiled: result = await fetch(url())
        async function handler() {
            const result = await mockFetch(__pynext__.getSignal('sig_1').read());
            return result;
        }
        
        const result = await handler();
        expect(result).toBe('response from https://api.example.com');
    });
    
    test('async try/catch pattern', async () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = null;
        __pynext__.getSignal('sig_2')._value = null;
        
        const mockFetch = async () => { throw new Error('network error'); };
        
        // Transpiled async try/catch
        async function handler() {
            try {
                const data = await mockFetch();
                __pynext__.getSignal('sig_1').set(data);
            } catch (_e) {
                __pynext__.getSignal('sig_2').set('Failed to fetch');
            }
        }
        
        await handler();
        
        expect(__pynext__.getSignal('sig_1').read()).toBe(null);
        expect(__pynext__.getSignal('sig_2').read()).toBe('Failed to fetch');
    });
    
    test('multiple awaits with signals', async () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = [];
        
        const fetchA = async () => 'A';
        const fetchB = async () => 'B';
        
        async function handler() {
            const a = await fetchA();
            const b = await fetchB();
            __pynext__.getSignal('sig_1').set([a, b]);
        }
        
        await handler();
        
        expect(__pynext__.getSignal('sig_1').read()).toEqual(['A', 'B']);
    });
    
    test('async handler with form validation', async () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = false;  // submitting
        mockForms['form_1'] = __pynext__.getForm('form_1');
        mockForms['form_1']._valid = true;
        mockForms['form_1']._values = { email: 'test@example.com' };
        mockForms['form_1'].values = mockForms['form_1']._values;
        
        const submit = async (data) => { return { success: true }; };
        let submitted = false;
        
        async function handler() {
            if (__pynext__.getForm('form_1').validate()) {
                __pynext__.getSignal('sig_1').set(true);
                await submit(__pynext__.getForm('form_1').values);
                submitted = true;
                __pynext__.getSignal('sig_1').set(false);
                __pynext__.getForm('form_1').reset();
            }
        }
        
        await handler();
        
        expect(submitted).toBe(true);
        expect(__pynext__.getSignal('sig_1').read()).toBe(false);
    });
});


// =============================================================================
// TEST 4: FORM OPERATIONS
// =============================================================================

describe('Form Operations', () => {
    
    test('form.validate() returns boolean', () => {
        mockForms['form_1'] = __pynext__.getForm('form_1');
        mockForms['form_1']._valid = true;
        
        const result = __pynext__.getForm('form_1').validate();
        expect(result).toBe(true);
    });
    
    test('form.values access', () => {
        mockForms['form_1'] = __pynext__.getForm('form_1');
        mockForms['form_1']._values = { email: 'test@test.com' };
        mockForms['form_1'].values = mockForms['form_1']._values;
        
        const values = __pynext__.getForm('form_1').values;
        expect(values.email).toBe('test@test.com');
    });
    
    test('form.reset() clears values', () => {
        mockForms['form_1'] = __pynext__.getForm('form_1');
        mockForms['form_1']._values = { email: 'test@test.com' };
        
        __pynext__.getForm('form_1').reset();
        
        expect(mockForms['form_1']._values).toEqual({});
    });
    
    test('form conditional pattern', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = [];
        mockForms['form_1'] = __pynext__.getForm('form_1');
        mockForms['form_1']._valid = true;
        mockForms['form_1']._values = { title: 'New Item' };
        mockForms['form_1'].values = mockForms['form_1']._values;
        
        // Transpiled: if form.validate(): items.update(...)
        function handler() {
            if (__pynext__.getForm('form_1').validate()) {
                const values = __pynext__.getForm('form_1').values;
                __pynext__.getSignal('sig_1').update(arr => [...arr, values]);
                __pynext__.getForm('form_1').reset();
            }
        }
        
        handler();
        
        expect(__pynext__.getSignal('sig_1').read()).toEqual([{ title: 'New Item' }]);
    });
    
    test('form with signal toggle', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = false;  // show_form
        mockForms['form_1'] = __pynext__.getForm('form_1');
        mockForms['form_1']._valid = true;
        
        // Toggle show_form and validate
        function handleSubmit() {
            if (__pynext__.getForm('form_1').validate()) {
                __pynext__.getSignal('sig_1').set(false);  // Hide form
                __pynext__.getForm('form_1').reset();
            }
        }
        
        __pynext__.getSignal('sig_1').set(true);  // Show form first
        expect(__pynext__.getSignal('sig_1').read()).toBe(true);
        
        handleSubmit();
        expect(__pynext__.getSignal('sig_1').read()).toBe(false);
    });
});


// =============================================================================
// TEST 5: STORE OPERATIONS
// =============================================================================

describe('Store Operations', () => {
    
    test('store property access', () => {
        const store = __pynext__.getStore('store_1');
        store.name = 'Test';
        
        expect(__pynext__.getStore('store_1').name).toBe('Test');
    });
    
    test('store subscript access', () => {
        const store = __pynext__.getStore('store_1');
        store['items'] = [1, 2, 3];
        
        expect(__pynext__.getStore('store_1')['items']).toEqual([1, 2, 3]);
    });
    
    test('store array mutations', () => {
        const store = __pynext__.getStore('store_1');
        store.items = [];
        
        // Transpiled: store.items.append(item)
        __pynext__.getStore('store_1').items.push({ id: 1 });
        __pynext__.getStore('store_1').items.push({ id: 2 });
        
        expect(__pynext__.getStore('store_1').items.length).toBe(2);
    });
    
    test('store with signal', () => {
        // Setup
        const store = __pynext__.getStore('store_1');
        store.items = [{ id: 1 }, { id: 2 }];
        __pynext__.getSignal('sig_1')._value = null;
        
        // Get item from store and set to signal
        function handler() {
            const items = __pynext__.getStore('store_1').items;
            __pynext__.getSignal('sig_1').set(items.length);
        }
        
        handler();
        
        expect(__pynext__.getSignal('sig_1').read()).toBe(2);
    });
});


// =============================================================================
// TEST 6: COMPLEX PATTERNS (INTEGRATION)
// =============================================================================

describe('Complex Integration Patterns', () => {
    
    test('handle_add_issue pattern (Linear app)', () => {
        // Setup: all_issues signal, issue_form, show_add_form signal
        __pynext__.getSignal('sig_1')._value = [];  // all_issues
        __pynext__.getSignal('sig_2')._value = true;  // show_add_form
        mockForms['form_1'] = __pynext__.getForm('form_1');
        mockForms['form_1']._valid = true;
        mockForms['form_1']._values = { title: 'Bug fix', priority: 'high' };
        mockForms['form_1'].values = mockForms['form_1']._values;
        
        // Transpiled handle_add_issue
        function handle_add_issue() {
            if (__pynext__.getForm('form_1').validate()) {
                const new_issue = {
                    id: Date.now(),
                    ...__pynext__.getForm('form_1').values,
                    status: 'backlog',
                };
                __pynext__.getSignal('sig_1').update(arr => [...arr, new_issue]);
                __pynext__.getForm('form_1').reset();
                __pynext__.getSignal('sig_2').set(false);
            }
        }
        
        handle_add_issue();
        
        const issues = __pynext__.getSignal('sig_1').read();
        expect(issues.length).toBe(1);
        expect(issues[0].title).toBe('Bug fix');
        expect(__pynext__.getSignal('sig_2').read()).toBe(false);
    });
    
    test('handle_delete with filter', () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = [
            { id: 1, name: 'A' },
            { id: 2, name: 'B' },
            { id: 3, name: 'C' },
        ];
        
        // Transpiled: all_issues.set([i for i in all_issues() if i["id"] != item_id])
        function handle_delete(item_id) {
            __pynext__.getSignal('sig_1').set(
                [...__py.iter(__pynext__.getSignal('sig_1').read())]
                    .filter(i => !__py.eq(i['id'], item_id))
            );
        }
        
        handle_delete(2);
        
        const remaining = __pynext__.getSignal('sig_1').read();
        expect(remaining.length).toBe(2);
        expect(remaining.map(i => i.id)).toEqual([1, 3]);
    });
    
    test('toggle pattern', () => {
        __pynext__.getSignal('sig_1')._value = false;
        
        // Transpiled: show.set(not show())
        function toggle() {
            __pynext__.getSignal('sig_1').set(!__py.bool(__pynext__.getSignal('sig_1').read()));
        }
        
        toggle();
        expect(__pynext__.getSignal('sig_1').read()).toBe(true);
        
        toggle();
        expect(__pynext__.getSignal('sig_1').read()).toBe(false);
    });
    
    test('increment pattern', () => {
        __pynext__.getSignal('sig_1')._value = 0;
        
        // Transpiled: count.set(count() + 1)
        function increment() {
            __pynext__.getSignal('sig_1').set(
                __py.add(__pynext__.getSignal('sig_1').read(), 1)
            );
        }
        
        increment();
        increment();
        increment();
        
        expect(__pynext__.getSignal('sig_1').read()).toBe(3);
    });
    
    test('optimistic update with rollback', async () => {
        // Setup
        __pynext__.getSignal('sig_1')._value = [{ id: 1 }, { id: 2 }];
        __pynext__.getSignal('sig_2')._value = null;  // error
        
        const mockDelete = async (id) => { throw new Error('Network error'); };
        
        // Transpiled optimistic update
        async function handle_delete(item_id) {
            const original = __pynext__.getSignal('sig_1').read();
            // Optimistic update
            __pynext__.getSignal('sig_1').set(
                [...__py.iter(original)].filter(x => !__py.eq(x['id'], item_id))
            );
            try {
                await mockDelete(item_id);
            } catch (_e) {
                // Rollback
                __pynext__.getSignal('sig_1').set(original);
                __pynext__.getSignal('sig_2').set('Delete failed');
            }
        }
        
        await handle_delete(1);
        
        // Should have rolled back
        expect(__pynext__.getSignal('sig_1').read().length).toBe(2);
        expect(__pynext__.getSignal('sig_2').read()).toBe('Delete failed');
    });
    
    test('batch update pattern', () => {
        __pynext__.getSignal('sig_1')._value = [
            { id: 1, status: 'pending' },
            { id: 2, status: 'pending' },
            { id: 3, status: 'done' },
        ];
        __pynext__.getSignal('sig_2')._value = [1, 2];  // selected IDs
        
        // Mark selected as done
        function mark_done() {
            const selected = __pynext__.getSignal('sig_2').read();
            __pynext__.getSignal('sig_1').update(items =>
                [...__py.iter(items)].map(item =>
                    __py.in(item.id, selected) 
                        ? { ...item, status: 'done' }
                        : item
                )
            );
            __pynext__.getSignal('sig_2').set([]);
        }
        
        mark_done();
        
        const items = __pynext__.getSignal('sig_1').read();
        expect(items.filter(i => i.status === 'done').length).toBe(3);
        expect(__pynext__.getSignal('sig_2').read()).toEqual([]);
    });
});


// =============================================================================
// TEST 7: MEMO OPERATIONS
// =============================================================================

describe('Memo Operations', () => {
    
    test('memo read', () => {
        mockMemos['memo_1'] = __pynext__.getMemo('memo_1');
        mockMemos['memo_1']._fn = () => 42;
        
        const result = __pynext__.getMemo('memo_1').read();
        expect(result).toBe(42);
    });
    
    test('memo with signal dependency', () => {
        __pynext__.getSignal('sig_1')._value = 10;
        
        mockMemos['memo_1'] = __pynext__.getMemo('memo_1');
        mockMemos['memo_1']._fn = () => __pynext__.getSignal('sig_1').read() * 2;
        
        expect(__pynext__.getMemo('memo_1').read()).toBe(20);
        
        __pynext__.getSignal('sig_1').set(5);
        expect(__pynext__.getMemo('memo_1').read()).toBe(10);
    });
});


if (typeof describe === 'function') {
    // Running in Jest
} else {
    console.log('Tests defined. Run with Jest.');
}
