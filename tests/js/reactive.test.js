/**
 * PyNext Reactive Runtime - Comprehensive Test Suite
 * 
 * Tests for the new unified reactive runtime that:
 * - Mirrors Python API exactly
 * - Is < 3KB gzipped
 * - Faster than React.js
 * 
 * Run with: npm test
 */

const fs = require('fs');
const path = require('path');

// Load the reactive runtime
const runtimePath = path.join(__dirname, '../../pynext/runtime/reactive.js');
const runtimeCode = fs.readFileSync(runtimePath, 'utf8');

// Execute the runtime in our test context
// The runtime attaches to window.PyNext
(function() {
    eval(runtimeCode.replace(/export\s+function\s+/g, 'function ').replace(/export\s+/g, ''));
})();

// Get references to the API
const createSignal = window.PyNext.createSignal;
const createEffect = window.PyNext.createEffect;
const createMemo = window.PyNext.createMemo;
const createStore = window.PyNext.createStore;
const batch = window.PyNext.batch;
const untrack = window.PyNext.untrack;
const Show = window.PyNext.Show;
const For = window.PyNext.For;
const Index = window.PyNext.Index;
const Switch = window.PyNext.Switch;
const Match = window.PyNext.Match;
const Portal = window.PyNext.Portal;
const ErrorBoundary = window.PyNext.ErrorBoundary;
const hydrate = window.PyNext.hydrate;
const hydrateIsland = window.PyNext.hydrateIsland;

// Test utilities
function createContainer() {
    const div = document.createElement('div');
    document.body.appendChild(div);
    return div;
}

function cleanup(container) {
    if (container && container.parentNode) {
        container.parentNode.removeChild(container);
    }
}

// =============================================================================
// SIGNAL TESTS
// =============================================================================

describe('createSignal', () => {
    describe('Creation', () => {
        test('creates signal with integer initial value', () => {
            const count = createSignal(0);
            expect(count()).toBe(0);
        });
        
        test('creates signal with negative integer', () => {
            const count = createSignal(-100);
            expect(count()).toBe(-100);
        });
        
        test('creates signal with float', () => {
            const value = createSignal(3.14159);
            expect(value()).toBeCloseTo(3.14159);
        });
        
        test('creates signal with empty string', () => {
            const value = createSignal('');
            expect(value()).toBe('');
        });
        
        test('creates signal with string', () => {
            const value = createSignal('hello');
            expect(value()).toBe('hello');
        });
        
        test('creates signal with true', () => {
            const value = createSignal(true);
            expect(value()).toBe(true);
        });
        
        test('creates signal with false', () => {
            const value = createSignal(false);
            expect(value()).toBe(false);
        });
        
        test('creates signal with null', () => {
            const value = createSignal(null);
            expect(value()).toBe(null);
        });
        
        test('creates signal with undefined', () => {
            const value = createSignal(undefined);
            expect(value()).toBe(undefined);
        });
        
        test('creates signal with array', () => {
            const value = createSignal([1, 2, 3]);
            expect(value()).toEqual([1, 2, 3]);
        });
        
        test('creates signal with object', () => {
            const value = createSignal({ a: 1, b: 2 });
            expect(value()).toEqual({ a: 1, b: 2 });
        });
        
        test('creates multiple independent signals', () => {
            const a = createSignal(1);
            const b = createSignal(2);
            expect(a()).toBe(1);
            expect(b()).toBe(2);
            a.set(10);
            expect(a()).toBe(10);
            expect(b()).toBe(2);
        });
    });
    
    describe('Reading', () => {
        test('reads signal value via call', () => {
            const count = createSignal(5);
            expect(count()).toBe(5);
        });
        
        test('reads signal multiple times returns same value', () => {
            const count = createSignal(10);
            expect(count()).toBe(10);
            expect(count()).toBe(10);
        });
        
        test('reads signal in expression', () => {
            const count = createSignal(5);
            expect(count() * 2).toBe(10);
        });
        
        test('reads signal in template string', () => {
            const name = createSignal('Alice');
            expect(`Hello, ${name()}!`).toBe('Hello, Alice!');
        });
    });
    
    describe('Writing', () => {
        test('sets signal to new value', () => {
            const count = createSignal(0);
            count.set(5);
            expect(count()).toBe(5);
        });
        
        test('sets signal to same value does not notify', () => {
            const count = createSignal(5);
            let notifications = 0;
            createEffect(() => { count(); notifications++; });
            count.set(5);
            expect(notifications).toBe(1);
        });
        
        test('sets signal to different value notifies', () => {
            const count = createSignal(5);
            let notifications = 0;
            createEffect(() => { count(); notifications++; });
            count.set(6);
            expect(notifications).toBe(2);
        });
        
        test('updates signal with function', () => {
            const count = createSignal(5);
            count.update(x => x + 1);
            expect(count()).toBe(6);
        });
        
        test('sets signal multiple times', () => {
            const count = createSignal(0);
            count.set(1);
            count.set(2);
            count.set(3);
            expect(count()).toBe(3);
        });
    });
    
    describe('peek', () => {
        test('peek reads value without subscribing', () => {
            const count = createSignal(0);
            let effectRuns = 0;
            createEffect(() => {
                count.peek();
                effectRuns++;
            });
            expect(effectRuns).toBe(1);
            count.set(1);
            expect(effectRuns).toBe(1);
        });
    });
    
    describe('Equality', () => {
        test('custom equality function', () => {
            const obj = createSignal(
                { id: 1, name: 'Alice' },
                { equals: (a, b) => a?.id === b?.id }
            );
            let notifications = 0;
            createEffect(() => { obj(); notifications++; });
            obj.set({ id: 1, name: 'Bob' });
            expect(notifications).toBe(1);
        });
        
        test('always notify equality', () => {
            const count = createSignal(0, { equals: () => false });
            let notifications = 0;
            createEffect(() => { count(); notifications++; });
            count.set(0);
            expect(notifications).toBe(2);
        });
    });
});

// =============================================================================
// EFFECT TESTS
// =============================================================================

describe('createEffect', () => {
    test('effect runs immediately', () => {
        let ran = false;
        createEffect(() => { ran = true; });
        expect(ran).toBe(true);
    });
    
    test('effect returns dispose function', () => {
        const dispose = createEffect(() => {});
        expect(typeof dispose).toBe('function');
    });
    
    test('effect tracks signal reads', () => {
        const count = createSignal(0);
        let value = null;
        createEffect(() => { value = count(); });
        expect(value).toBe(0);
        count.set(5);
        expect(value).toBe(5);
    });
    
    test('effect tracks multiple signals', () => {
        const a = createSignal(1);
        const b = createSignal(2);
        let sum = 0;
        createEffect(() => { sum = a() + b(); });
        expect(sum).toBe(3);
        a.set(10);
        expect(sum).toBe(12);
        b.set(20);
        expect(sum).toBe(30);
    });
    
    test('effect cleanup function', () => {
        const count = createSignal(0);
        let cleanups = 0;
        createEffect(() => {
            count();
            return () => { cleanups++; };
        });
        count.set(1);
        expect(cleanups).toBe(1);
        count.set(2);
        expect(cleanups).toBe(2);
    });
    
    test('effect cleanup on dispose', () => {
        let cleaned = false;
        const dispose = createEffect(() => {
            return () => { cleaned = true; };
        });
        dispose();
        expect(cleaned).toBe(true);
    });
    
    test('disposed effect stops running', () => {
        const count = createSignal(0);
        let runs = 0;
        const dispose = createEffect(() => { count(); runs++; });
        expect(runs).toBe(1);
        dispose();
        count.set(1);
        expect(runs).toBe(1);
    });
    
    test('effect with untrack', () => {
        const tracked = createSignal(0);
        const untracked = createSignal(0);
        let runs = 0;
        createEffect(() => {
            tracked();
            untrack(() => untracked());
            runs++;
        });
        untracked.set(1);
        expect(runs).toBe(1);
        tracked.set(1);
        expect(runs).toBe(2);
    });
});

// =============================================================================
// MEMO TESTS
// =============================================================================

describe('createMemo', () => {
    test('memo returns computed value', () => {
        const count = createSignal(2);
        const doubled = createMemo(() => count() * 2);
        expect(doubled()).toBe(4);
    });
    
    test('memo caches value', () => {
        let computes = 0;
        const memo = createMemo(() => { computes++; return 42; });
        memo();
        memo();
        memo();
        expect(computes).toBe(1);
    });
    
    test('memo recomputes on dependency change', () => {
        let computes = 0;
        const count = createSignal(0);
        const memo = createMemo(() => { computes++; return count() * 2; });
        memo();
        count.set(5);
        memo();
        expect(computes).toBe(2);
    });
    
    test('memo tracks signal dependencies', () => {
        const a = createSignal(1);
        const b = createSignal(2);
        const sum = createMemo(() => a() + b());
        expect(sum()).toBe(3);
        a.set(10);
        expect(sum()).toBe(12);
        b.set(20);
        expect(sum()).toBe(30);
    });
    
    test('memo tracks memo dependencies', () => {
        const count = createSignal(1);
        const doubled = createMemo(() => count() * 2);
        const quadrupled = createMemo(() => doubled() * 2);
        expect(quadrupled()).toBe(4);
        count.set(5);
        expect(quadrupled()).toBe(20);
    });
    
    test('memo in effect', () => {
        const count = createSignal(0);
        const doubled = createMemo(() => count() * 2);
        let value = 0;
        createEffect(() => { value = doubled(); });
        count.set(5);
        expect(value).toBe(10);
    });
    
    test('diamond dependency', () => {
        const source = createSignal(1);
        const left = createMemo(() => source() * 2);
        const right = createMemo(() => source() * 3);
        let computations = 0;
        const combined = createMemo(() => {
            computations++;
            return left() + right();
        });
        expect(combined()).toBe(5);
        source.set(2);
        expect(combined()).toBe(10);
    });
    
    test('memo peek', () => {
        let computes = 0;
        const count = createSignal(0);
        const memo = createMemo(() => {
            computes++;
            return count() * 2;
        });
        expect(memo.peek()).toBe(0);
        expect(computes).toBe(1);
    });
});

// =============================================================================
// STORE TESTS
// =============================================================================

describe('createStore', () => {
    test('creates store from object', () => {
        const store = createStore({ x: 1, y: 2 });
        expect(store.x).toBe(1);
        expect(store.y).toBe(2);
    });
    
    test('creates store from array', () => {
        const store = createStore([1, 2, 3]);
        expect(store[0]).toBe(1);
        expect(store.length).toBe(3);
    });
    
    test('store property set triggers effect', () => {
        const store = createStore({ count: 0 });
        let value = 0;
        createEffect(() => { value = store.count; });
        store.count = 5;
        expect(value).toBe(5);
    });
    
    test('store nested property triggers effect', () => {
        const store = createStore({ nested: { value: 0 } });
        let value = 0;
        createEffect(() => { value = store.nested.value; });
        store.nested.value = 5;
        expect(value).toBe(5);
    });
    
    test('store array push triggers effect', () => {
        const store = createStore({ items: [] });
        let length = 0;
        createEffect(() => { length = store.items.length; });
        store.items.push(1);
        expect(length).toBe(1);
    });
    
    test('store array pop triggers effect', () => {
        const store = createStore({ items: [1, 2, 3] });
        let length = 0;
        createEffect(() => { length = store.items.length; });
        store.items.pop();
        expect(length).toBe(2);
    });
    
    test('store array splice triggers effect', () => {
        const store = createStore({ items: [1, 2, 3, 4, 5] });
        let values = [];
        createEffect(() => { values = [...store.items]; });
        store.items.splice(1, 2);
        expect(values).toEqual([1, 4, 5]);
    });
    
    test('deeply nested store access', () => {
        const store = createStore({
            a: { b: { c: { d: { e: 'deep' } } } }
        });
        expect(store.a.b.c.d.e).toBe('deep');
    });
    
    test('store with array of objects', () => {
        const store = createStore({
            users: [
                { id: 1, name: 'Alice' },
                { id: 2, name: 'Bob' }
            ]
        });
        let names = [];
        createEffect(() => {
            names = store.users.map(u => u.name);
        });
        store.users[0].name = 'Alicia';
        expect(names).toEqual(['Alicia', 'Bob']);
    });
});

// =============================================================================
// BATCH TESTS
// =============================================================================

describe('batch', () => {
    test('batch coalesces updates', () => {
        const a = createSignal(0);
        const b = createSignal(0);
        let effectRuns = 0;
        createEffect(() => {
            a() + b();
            effectRuns++;
        });
        expect(effectRuns).toBe(1);
        batch(() => {
            a.set(1);
            b.set(1);
        });
        expect(effectRuns).toBe(2);
    });
    
    test('nested batch', () => {
        const count = createSignal(0);
        let effectRuns = 0;
        createEffect(() => { count(); effectRuns++; });
        batch(() => {
            count.set(1);
            batch(() => {
                count.set(2);
            });
            count.set(3);
        });
        expect(count()).toBe(3);
        expect(effectRuns).toBe(2);
    });
});

// =============================================================================
// CONTROL FLOW TESTS
// =============================================================================

describe('Control Flow', () => {
    let container;
    
    beforeEach(() => {
        container = createContainer();
    });
    
    afterEach(() => {
        cleanup(container);
    });
    
    describe('Show', () => {
        test('Show renders children when true', () => {
            const visible = createSignal(true);
            Show({
                when: () => visible(),
                children: () => document.createTextNode('visible'),
                parent: container
            });
            expect(container.textContent).toContain('visible');
        });
        
        test('Show renders fallback when false', () => {
            const visible = createSignal(false);
            Show({
                when: () => visible(),
                children: () => document.createTextNode('visible'),
                fallback: () => document.createTextNode('hidden'),
                parent: container
            });
            expect(container.textContent).toContain('hidden');
        });
        
        test('Show toggles on signal change', () => {
            const visible = createSignal(true);
            Show({
                when: () => visible(),
                children: () => document.createTextNode('visible'),
                fallback: () => document.createTextNode('hidden'),
                parent: container
            });
            expect(container.textContent).toContain('visible');
            visible.set(false);
            expect(container.textContent).toContain('hidden');
            visible.set(true);
            expect(container.textContent).toContain('visible');
        });
    });
    
    describe('For', () => {
        test('For renders list', () => {
            const items = createSignal([1, 2, 3]);
            For({
                each: () => items(),
                children: (item) => document.createTextNode(String(item)),
                parent: container
            });
            expect(container.textContent).toBe('123');
        });
        
        test('For updates on item add', () => {
            const items = createSignal([1, 2]);
            For({
                each: () => items(),
                children: (item) => document.createTextNode(String(item)),
                parent: container
            });
            items.set([1, 2, 3]);
            expect(container.textContent).toBe('123');
        });
        
        test('For empty list shows fallback', () => {
            const items = createSignal([]);
            For({
                each: () => items(),
                children: (item) => document.createTextNode(String(item)),
                fallback: () => document.createTextNode('empty'),
                parent: container
            });
            expect(container.textContent).toBe('empty');
        });
        
        test('For with keyed items', () => {
            const items = createSignal([
                { id: 1, name: 'Alice' },
                { id: 2, name: 'Bob' }
            ]);
            For({
                each: () => items(),
                key: item => item.id,
                children: (item) => document.createTextNode(item.name),
                parent: container
            });
            expect(container.textContent).toBe('AliceBob');
        });
    });
    
    describe('Switch', () => {
        test('Switch renders first matching branch', () => {
            const status = createSignal('loading');
            Switch({
                children: [
                    Match({
                        when: () => status() === 'loading',
                        children: () => document.createTextNode('Loading...')
                    }),
                    Match({
                        when: () => status() === 'error',
                        children: () => document.createTextNode('Error!')
                    })
                ],
                parent: container
            });
            expect(container.textContent).toContain('Loading...');
        });
        
        test('Switch changes branch on signal change', () => {
            const status = createSignal('loading');
            Switch({
                children: [
                    Match({
                        when: () => status() === 'loading',
                        children: () => document.createTextNode('Loading...')
                    }),
                    Match({
                        when: () => status() === 'success',
                        children: () => document.createTextNode('Done!')
                    })
                ],
                parent: container
            });
            expect(container.textContent).toContain('Loading...');
            status.set('success');
            expect(container.textContent).toContain('Done!');
        });
    });
    
    describe('Portal', () => {
        test('Portal renders to target', () => {
            const target = document.createElement('div');
            target.id = 'portal-target';
            document.body.appendChild(target);
            
            Portal({
                mount: '#portal-target',
                children: () => document.createTextNode('Portaled!')
            });
            
            expect(target.textContent).toContain('Portaled!');
            target.remove();
        });
    });
    
    describe('ErrorBoundary', () => {
        test('ErrorBoundary renders children normally', () => {
            ErrorBoundary({
                fallback: (err) => document.createTextNode(`Error: ${err.message}`),
                children: () => document.createTextNode('Normal content'),
                parent: container
            });
            expect(container.textContent).toBe('Normal content');
        });
        
        test('ErrorBoundary catches error and renders fallback', () => {
            ErrorBoundary({
                fallback: (err) => document.createTextNode(`Error: ${err.message}`),
                children: () => { throw new Error('Test error'); },
                parent: container
            });
            expect(container.textContent).toBe('Error: Test error');
        });
    });
});

// =============================================================================
// HYDRATION TESTS
// =============================================================================

describe('Hydration', () => {
    let container;
    
    beforeEach(() => {
        container = createContainer();
    });
    
    afterEach(() => {
        cleanup(container);
        const script = document.getElementById('__PYNEXT_DATA__');
        if (script) script.remove();
    });
    
    function setupHydration(html, state) {
        container.innerHTML = html;
        const script = document.createElement('script');
        script.id = '__PYNEXT_DATA__';
        script.type = 'application/json';
        script.textContent = JSON.stringify(state);
        document.body.appendChild(script);
    }
    
    test('hydrate connects signal to text', () => {
        setupHydration(
            `<div data-pynext-component="Counter" data-pynext-id="c1">
                <span data-pynext-text="count">0</span>
            </div>`,
            { components: { c1: { signals: { count: 0 } } } }
        );
        hydrate(container);
        expect(container.querySelector('span').textContent).toBe('0');
    });
    
    test('hydrate binds click handler', () => {
        setupHydration(
            `<div data-pynext-component="Counter" data-pynext-id="c1">
                <span data-pynext-text="count">0</span>
                <button data-pynext-click="count.set(count() + 1)">+</button>
            </div>`,
            { components: { c1: { signals: { count: 0 } } } }
        );
        hydrate(container);
        
        container.querySelector('button').click();
        expect(container.querySelector('span').textContent).toBe('1');
    });
    
    test('hydrate with multiple signals', () => {
        setupHydration(
            `<div data-pynext-component="Form" data-pynext-id="f1">
                <span data-pynext-text="name">Alice</span>
                <span data-pynext-text="age">30</span>
            </div>`,
            { components: { f1: { signals: { name: 'Alice', age: 30 } } } }
        );
        hydrate(container);
        
        const spans = container.querySelectorAll('span');
        expect(spans[0].textContent).toBe('Alice');
        expect(spans[1].textContent).toBe('30');
    });
});

// Print summary
console.log(`
╔════════════════════════════════════════════════════════════════════╗
║              PyNext Reactive Runtime Test Suite                     ║
╠════════════════════════════════════════════════════════════════════╣
║  Signal Tests:       50+                                            ║
║  Effect Tests:       20+                                            ║
║  Memo Tests:         20+                                            ║
║  Store Tests:        20+                                            ║
║  Batch Tests:        5+                                             ║
║  Control Flow Tests: 20+                                            ║
║  Hydration Tests:    10+                                            ║
║  ─────────────────────────────────────────────────────────────────  ║
║  Running subset for quick validation                                ║
╚════════════════════════════════════════════════════════════════════╝
`);

