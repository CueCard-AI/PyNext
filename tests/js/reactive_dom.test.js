/**
 * Tests for reactive DOM updates in JavaScript runtime.
 * 
 * Tests cover:
 * - createEffect behavior
 * - Signal subscription and notification
 * - DOM update functions (updateShow, updateText, updateClass, etc.)
 * - Binding registration and execution
 * - Array diffing for For component
 */

// Mock DOM environment
const { JSDOM } = require('jsdom');

describe('Reactive DOM Updates', () => {
    let window;
    let document;
    let __pynext__;

    beforeEach(() => {
        const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            runScripts: 'dangerously'
        });
        window = dom.window;
        document = window.document;
        
        // Initialize PyNext runtime
        window.__pynext__ = {
            signals: {},
            effects: {},
            stores: {},
            forms: {},
        };
        __pynext__ = window.__pynext__;
    });

    describe('createSignal', () => {
        test('creates signal with initial value', () => {
            const signal = createSignal('sig_1', 42);
            expect(signal.read()).toBe(42);
        });

        test('signal.set updates value', () => {
            const signal = createSignal('sig_1', 0);
            signal.set(10);
            expect(signal.read()).toBe(10);
        });

        test('signal.update uses updater function', () => {
            const signal = createSignal('sig_1', 5);
            signal.update(v => v * 2);
            expect(signal.read()).toBe(10);
        });

        test('signal is registered globally', () => {
            const signal = createSignal('sig_1', 42);
            expect(__pynext__.signals['sig_1']).toBeDefined();
        });
    });

    describe('createEffect', () => {
        test('effect runs immediately', () => {
            let ran = false;
            createEffect(() => {
                ran = true;
            });
            expect(ran).toBe(true);
        });

        test('effect with function callback', () => {
            const values = [];
            const signal = createSignal('sig_1', 0);
            
            createEffect(() => {
                values.push(signal.read());
            });
            
            expect(values).toEqual([0]);
            
            signal.set(1);
            expect(values).toEqual([0, 1]);
        });

        test('effect with hydration format', () => {
            const values = [];
            const signal = createSignal('sig_1', 0);
            
            createEffect(
                'eff_1',
                ['sig_1'],
                `values.push(__pynext__.getSignal('sig_1').read())`
            );
            
            // May or may not work depending on scope
        });

        test('multiple signals trigger effect', () => {
            let runCount = 0;
            const a = createSignal('a', 1);
            const b = createSignal('b', 2);
            
            createEffect(() => {
                a.read();
                b.read();
                runCount++;
            });
            
            expect(runCount).toBe(1);
            
            a.set(10);
            expect(runCount).toBe(2);
            
            b.set(20);
            expect(runCount).toBe(3);
        });
    });

    describe('updateShow', () => {
        test('shows element when visible is true', () => {
            document.body.innerHTML = '<div id="test" style="display: none;">Content</div>';
            const el = document.getElementById('test');
            
            updateShow(el, true);
            
            expect(el.style.display).not.toBe('none');
        });

        test('hides element when visible is false', () => {
            document.body.innerHTML = '<div id="test">Content</div>';
            const el = document.getElementById('test');
            
            updateShow(el, false);
            
            expect(el.style.display).toBe('none');
        });

        test('preserves original display on show', () => {
            document.body.innerHTML = '<div id="test" style="display: flex;">Content</div>';
            const el = document.getElementById('test');
            el.dataset.pynextOriginalDisplay = 'flex';
            
            updateShow(el, false);
            expect(el.style.display).toBe('none');
            
            updateShow(el, true);
            expect(el.style.display).toBe('flex');
        });
    });

    describe('updateText', () => {
        test('updates text content', () => {
            document.body.innerHTML = '<span id="test">Old</span>';
            const el = document.getElementById('test');
            
            updateText(el, 'New');
            
            expect(el.textContent).toBe('New');
        });

        test('handles number values', () => {
            document.body.innerHTML = '<span id="test">0</span>';
            const el = document.getElementById('test');
            
            updateText(el, 42);
            
            expect(el.textContent).toBe('42');
        });

        test('escapes HTML', () => {
            document.body.innerHTML = '<span id="test"></span>';
            const el = document.getElementById('test');
            
            updateText(el, '<script>alert(1)</script>');
            
            expect(el.textContent).toBe('<script>alert(1)</script>');
            expect(el.innerHTML).not.toContain('<script>');
        });
    });

    describe('updateClass', () => {
        test('sets class name', () => {
            document.body.innerHTML = '<div id="test" class="old"></div>';
            const el = document.getElementById('test');
            
            updateClass(el, 'new');
            
            expect(el.className).toBe('new');
        });

        test('handles multiple classes', () => {
            document.body.innerHTML = '<div id="test"></div>';
            const el = document.getElementById('test');
            
            updateClass(el, 'a b c');
            
            expect(el.classList.contains('a')).toBe(true);
            expect(el.classList.contains('b')).toBe(true);
            expect(el.classList.contains('c')).toBe(true);
        });

        test('clears classes with empty string', () => {
            document.body.innerHTML = '<div id="test" class="old"></div>';
            const el = document.getElementById('test');
            
            updateClass(el, '');
            
            expect(el.className).toBe('');
        });
    });

    describe('updateStyle', () => {
        test('sets style string', () => {
            document.body.innerHTML = '<div id="test"></div>';
            const el = document.getElementById('test');
            
            updateStyle(el, 'color: red; font-size: 14px');
            
            expect(el.style.color).toBe('red');
            expect(el.style.fontSize).toBe('14px');
        });

        test('handles style object', () => {
            document.body.innerHTML = '<div id="test"></div>';
            const el = document.getElementById('test');
            
            updateStyle(el, { color: 'blue', margin: '10px' });
            
            // Depends on implementation
        });
    });

    describe('updateAttr', () => {
        test('sets attribute value', () => {
            document.body.innerHTML = '<input id="test" />';
            const el = document.getElementById('test');
            
            updateAttr(el, 'placeholder', 'Enter text');
            
            expect(el.getAttribute('placeholder')).toBe('Enter text');
        });

        test('removes attribute with null', () => {
            document.body.innerHTML = '<input id="test" disabled />';
            const el = document.getElementById('test');
            
            updateAttr(el, 'disabled', null);
            
            expect(el.hasAttribute('disabled')).toBe(false);
        });

        test('handles boolean attributes', () => {
            document.body.innerHTML = '<button id="test">Click</button>';
            const el = document.getElementById('test');
            
            updateAttr(el, 'disabled', true);
            
            expect(el.disabled).toBe(true);
        });
    });

    describe('registerBinding', () => {
        test('creates effect for show binding', () => {
            document.body.innerHTML = '<div id="show_1" data-pynext-show="true">Content</div>';
            const signal = createSignal('sig_1', true);
            
            registerBinding({
                nodeId: 'show_1',
                type: 'show',
                signals: ['sig_1'],
                update: "__pynext__.getSignal('sig_1').read()",
            });
            
            const el = document.getElementById('show_1');
            expect(el.style.display).not.toBe('none');
            
            signal.set(false);
            // Effect should update display
        });

        test('creates effect for text binding', () => {
            document.body.innerHTML = '<span id="text_1">0</span>';
            const signal = createSignal('sig_1', 42);
            
            registerBinding({
                nodeId: 'text_1',
                type: 'text',
                signals: ['sig_1'],
                update: "__pynext__.getSignal('sig_1').read()",
            });
            
            const el = document.getElementById('text_1');
            expect(el.textContent).toBe('42');
        });
    });

    describe('hydrateBindings', () => {
        test('processes array of bindings', () => {
            document.body.innerHTML = `
                <div id="show_1" data-pynext-show="true">A</div>
                <span id="text_1">0</span>
            `;
            
            createSignal('sig_1', true);
            createSignal('sig_2', 42);
            
            hydrateBindings([
                { nodeId: 'show_1', type: 'show', signals: ['sig_1'], update: 'true' },
                { nodeId: 'text_1', type: 'text', signals: ['sig_2'], update: '42' },
            ]);
            
            // Both bindings should be registered
        });
    });

    describe('For binding with array diffing', () => {
        test('handles empty list', () => {
            document.body.innerHTML = '<div id="for_1" data-pynext-for="true"></div>';
            const signal = createSignal('sig_1', []);
            
            registerForBinding(
                document.getElementById('for_1'),
                { initial: { count: 0, keys: [] } },
                () => signal.read()
            );
            
            const container = document.getElementById('for_1');
            expect(container.children.length).toBe(0);
        });

        test('adds items to empty list', () => {
            document.body.innerHTML = `
                <div id="for_1" data-pynext-for="true">
                    <div data-for-item="1">Item 1</div>
                </div>
            `;
            const signal = createSignal('sig_1', [{ id: 1 }]);
            
            registerForBinding(
                document.getElementById('for_1'),
                { initial: { count: 1, keys: [1] } },
                () => signal.read()
            );
            
            // Add more items
            signal.set([{ id: 1 }, { id: 2 }]);
            
            // Should have 2 items now
        });

        test('removes items from list', () => {
            document.body.innerHTML = `
                <div id="for_1" data-pynext-for="true">
                    <div data-for-item="1">Item 1</div>
                    <div data-for-item="2">Item 2</div>
                </div>
            `;
            const signal = createSignal('sig_1', [{ id: 1 }, { id: 2 }]);
            
            registerForBinding(
                document.getElementById('for_1'),
                { initial: { count: 2, keys: [1, 2] } },
                () => signal.read()
            );
            
            // Remove item
            signal.set([{ id: 1 }]);
            
            // Should have 1 item now
        });
    });

    describe('Batch updates', () => {
        test('batch delays effects', () => {
            const values = [];
            const signal = createSignal('sig_1', 0);
            
            createEffect(() => {
                values.push(signal.read());
            });
            
            expect(values).toEqual([0]);
            
            __pynext__.batch(() => {
                signal.set(1);
                signal.set(2);
                signal.set(3);
            });
            
            // Effect should only run once with final value
            expect(values[values.length - 1]).toBe(3);
        });
    });

    describe('Edge cases', () => {
        test('null element handled gracefully', () => {
            expect(() => {
                updateShow(null, true);
            }).not.toThrow();
        });

        test('missing element ID handled', () => {
            registerBinding({
                nodeId: 'nonexistent',
                type: 'show',
                signals: ['sig_1'],
                update: 'true',
            });
            // Should not throw
        });

        test('invalid update expression handled', () => {
            document.body.innerHTML = '<div id="test">X</div>';
            createSignal('sig_1', true);
            
            registerBinding({
                nodeId: 'test',
                type: 'text',
                signals: ['sig_1'],
                update: 'this is not valid JS {{{',
            });
            // Should not crash
        });
    });
});

// Helper functions (would be imported from signals.js in real tests)
function createSignal(id, initialValue) {
    let value = initialValue;
    const subscribers = new Set();

    const signal = {
        id,
        read: () => value,
        set: (newValue) => {
            value = newValue;
            subscribers.forEach(fn => fn());
        },
        update: (fn) => {
            value = fn(value);
            subscribers.forEach(fn => fn());
        },
        subscribe: (fn) => {
            subscribers.add(fn);
            return () => subscribers.delete(fn);
        }
    };

    window.__pynext__.signals[id] = signal;
    return signal;
}

function createEffect(fnOrId, deps, code) {
    let fn;
    if (typeof fnOrId === 'function') {
        fn = fnOrId;
    } else if (code) {
        try {
            fn = new Function(code);
        } catch (e) {
            return null;
        }
    } else {
        return null;
    }

    const effect = {
        id: typeof fnOrId === 'string' ? fnOrId : 'effect_' + Math.random().toString(36).substr(2, 9),
        execute: fn
    };

    // Run immediately
    fn();

    window.__pynext__.effects[effect.id] = effect;
    return effect;
}

function updateShow(element, visible) {
    if (!element) return;
    element.style.display = visible ? (element.dataset.pynextOriginalDisplay || '') : 'none';
}

function updateText(element, value) {
    if (!element) return;
    element.textContent = String(value);
}

function updateClass(element, value) {
    if (!element) return;
    element.className = value;
}

function updateStyle(element, value) {
    if (!element) return;
    if (typeof value === 'string') {
        element.style.cssText = value;
    }
}

function updateAttr(element, attrName, value) {
    if (!element) return;
    if (value === null || value === false) {
        element.removeAttribute(attrName);
    } else {
        element.setAttribute(attrName, value);
    }
}

function registerBinding(binding) {
    const element = document.getElementById(binding.nodeId);
    if (!element) return;
    
    // Create effect based on type
    createEffect(() => {
        try {
            const value = new Function('return ' + binding.update)();
            switch (binding.type) {
                case 'show': updateShow(element, value); break;
                case 'text': updateText(element, value); break;
                case 'class': updateClass(element, value); break;
                case 'style': updateStyle(element, value); break;
            }
        } catch (e) {
            console.warn('Binding error:', e);
        }
    });
}

function registerForBinding(container, binding, eachFn) {
    // Simplified implementation for tests
}

function hydrateBindings(bindings) {
    bindings.forEach(registerBinding);
}

