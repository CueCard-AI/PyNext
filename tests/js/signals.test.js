/**
 * Tests for PyNext Signals Runtime
 */

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

describe('Signals Runtime', () => {
    let dom;
    let window;
    
    beforeEach(() => {
        dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            runScripts: 'dangerously',
        });
        window = dom.window;
        
        // Load the runtime
        const code = fs.readFileSync(
            path.join(__dirname, '../../pynext/runtime/signals.slim.js'),
            'utf8'
        );
        const script = window.document.createElement('script');
        script.textContent = code;
        window.document.body.appendChild(script);
    });
    
    afterEach(() => {
        dom.window.close();
    });
    
    describe('createSignal', () => {
        test('creates signal with initial value', () => {
            const signal = window.__pynext__.createSignal('test', 42);
            
            expect(signal.id).toBe('test');
            expect(signal.get()).toBe(42);
        });
        
        test('set updates value', () => {
            const signal = window.__pynext__.createSignal('test', 0);
            signal.set(100);
            
            expect(signal.get()).toBe(100);
        });
        
        test('does not trigger on same value', () => {
            let calls = 0;
            const signal = window.__pynext__.createSignal('test', 5);
            signal.subscribe(() => calls++);
            
            signal.set(5); // Same value
            expect(calls).toBe(0);
            
            signal.set(10); // Different value
            expect(calls).toBe(1);
        });
    });
    
    describe('getSignal/setSignal', () => {
        test('getSignal retrieves by ID', () => {
            window.__pynext__.createSignal('mySignal', 'hello');
            
            const signal = window.__pynext__.getSignal('mySignal');
            expect(signal.get()).toBe('hello');
        });
        
        test('setSignal updates by ID', () => {
            window.__pynext__.createSignal('mySignal', 'initial');
            window.__pynext__.setSignal('mySignal', 'updated');
            
            expect(window.__pynext__.getSignal('mySignal').get()).toBe('updated');
        });
        
        test('setSignal ignores unknown ID', () => {
            expect(() => {
                window.__pynext__.setSignal('unknown', 'value');
            }).not.toThrow();
        });
    });
    
    describe('createEffect', () => {
        test('runs immediately', () => {
            let ran = false;
            window.__pynext__.createEffect(() => {
                ran = true;
            });
            
            expect(ran).toBe(true);
        });
        
        test('re-runs when signal changes', () => {
            let value = 0;
            const signal = window.__pynext__.createSignal('count', 1);
            
            window.__pynext__.createEffect(() => {
                value = signal.get() * 2;
            });
            
            expect(value).toBe(2);
            
            signal.set(5);
            expect(value).toBe(10);
        });
    });
    
    describe('createMemo', () => {
        test('computes derived value', () => {
            const a = window.__pynext__.createSignal('a', 2);
            const b = window.__pynext__.createSignal('b', 3);
            
            const sum = window.__pynext__.createMemo(() => a.get() + b.get());
            
            expect(sum()).toBe(5);
        });
        
        test('updates when dependencies change', () => {
            const x = window.__pynext__.createSignal('x', 10);
            const doubled = window.__pynext__.createMemo(() => x.get() * 2);
            
            expect(doubled()).toBe(20);
            
            x.set(15);
            expect(doubled()).toBe(30);
        });
    });
    
    describe('batch', () => {
        test('batches multiple updates', () => {
            let updateCount = 0;
            const a = window.__pynext__.createSignal('a', 1);
            const b = window.__pynext__.createSignal('b', 2);
            
            window.__pynext__.createEffect(() => {
                a.get();
                b.get();
                updateCount++;
            });
            
            // Initial run
            expect(updateCount).toBe(1);
            
            // Batched updates
            window.__pynext__.batch(() => {
                a.set(10);
                b.set(20);
            });
            
            // Should have run effect once more (not twice)
            expect(updateCount).toBe(2);
        });
    });
    
    describe('hydrate', () => {
        test('hydrates from __PYNEXT_DATA__', () => {
            window.__PYNEXT_DATA__ = {
                signals: [
                    { id: 'count', value: 42 },
                    { id: 'name', value: 'PyNext' }
                ]
            };
            
            // Re-load runtime
            const code = fs.readFileSync(
                path.join(__dirname, '../../pynext/runtime/signals.slim.js'),
                'utf8'
            );
            eval(code);
            
            expect(window.__pynext__.getSignal('count').get()).toBe(42);
            expect(window.__pynext__.getSignal('name').get()).toBe('PyNext');
        });
    });
    
    describe('DOM binding', () => {
        test('bindText updates element text', () => {
            const div = window.document.createElement('div');
            window.document.body.appendChild(div);
            
            window.__pynext__.createSignal('message', 'Hello');
            window.__pynext__.bindText(div, 'message');
            
            expect(div.textContent).toBe('Hello');
            
            window.__pynext__.setSignal('message', 'World');
            expect(div.textContent).toBe('World');
        });
        
        test('bindClass toggles class', () => {
            const div = window.document.createElement('div');
            window.document.body.appendChild(div);
            
            window.__pynext__.createSignal('active', false);
            window.__pynext__.bindClass(div, 'is-active', 'active');
            
            expect(div.classList.contains('is-active')).toBe(false);
            
            window.__pynext__.setSignal('active', true);
            expect(div.classList.contains('is-active')).toBe(true);
        });
    });
});

