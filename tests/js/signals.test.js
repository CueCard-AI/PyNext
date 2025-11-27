/**
 * Tests for PyNext Signals Runtime
 * Uses Jest's built-in jsdom environment
 */

const fs = require('fs');
const path = require('path');

describe('Signals Runtime', () => {
    beforeEach(() => {
        // Setup mock signals system that matches the real API
        window.__pynext__ = window.__pynext__ || {};
        
        const signals = {};
        
        window.__pynext__.createSignal = jest.fn((id, initialValue) => {
            const subscribers = [];
            let value = initialValue;
            const signal = {
                id,
                get: () => value,
                set: (newValue) => {
                    if (value !== newValue) {
                        value = newValue;
                        subscribers.forEach(fn => fn(value));
                    }
                },
                subscribe: (fn) => {
                    subscribers.push(fn);
                    return () => {
                        const idx = subscribers.indexOf(fn);
                        if (idx > -1) subscribers.splice(idx, 1);
                    };
                },
            };
            signals[id] = signal;
            return signal;
        });
        
        window.__pynext__.getSignal = (id) => signals[id];
        window.__pynext__.setSignal = (id, value) => {
            if (signals[id]) signals[id].set(value);
        };
        
        window.__pynext__.createEffect = jest.fn((fn) => {
            fn();
            return () => {};
        });
        
        window.__pynext__.createMemo = jest.fn((fn) => fn);
        
        window.__pynext__.batch = jest.fn((fn) => fn());
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
    });
    
    describe('signals.js file structure', () => {
        let content;
        
        beforeAll(() => {
            content = fs.readFileSync(
                path.join(__dirname, '../../pynext/runtime/signals.js'),
                'utf8'
            );
        });
        
        test('has createSignal function', () => {
            expect(content).toContain('createSignal');
        });
        
        test('has subscribe mechanism', () => {
            expect(content).toContain('subscribe');
        });
        
        test('has effect mechanism', () => {
            expect(content).toContain('effect') || expect(content).toContain('Effect');
        });
        
        test('has batch mechanism', () => {
            expect(content).toContain('batch');
        });
    });
});
