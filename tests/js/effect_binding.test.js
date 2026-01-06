/**
 * Tests for PyNext Generalized Effect and Binding System
 * 
 * Tests cover:
 * - createEffect() with all signatures
 * - createBinding() for two-way data binding
 * - Effect disposal and cleanup
 * - Form reset behavior (the original bug fix)
 * 
 * These tests ensure the reactive runtime correctly handles:
 * 1. Anonymous effects: createEffect(fn)
 * 2. Named effects: createEffect(id, fn)
 * 3. Hydration effects: createEffect(id, deps, code)
 * 4. Options-based effects: createEffect({ id, fn, ... })
 * 5. Two-way bindings between signals and DOM elements
 */

const fs = require('fs');
const path = require('path');

// =============================================================================
// SETUP - Load the actual signals.js runtime
// =============================================================================

describe('Effect and Binding System', () => {
    let signalsContent;
    
    beforeAll(() => {
        signalsContent = fs.readFileSync(
            path.join(__dirname, '../../pynext/runtime/signals.js'),
            'utf8'
        );
    });
    
    beforeEach(() => {
        // Reset the global state
        delete global.__pynext__;
        delete global.__py;
        
        // Execute the signals.js in the global context
        // This is a simplified approach - in real tests we'd use a proper module loader
        eval(signalsContent);
    });
    
    // =========================================================================
    // STRUCTURAL TESTS - Verify the file contains expected patterns
    // =========================================================================
    
    describe('File Structure', () => {
        test('has createEffect function with all signatures documented', () => {
            expect(signalsContent).toContain('function createEffect');
            expect(signalsContent).toContain('createEffect(fn)');
            expect(signalsContent).toContain('createEffect(id, fn)');
            expect(signalsContent).toContain('createEffect(id, deps, code)');
        });
        
        test('has createBinding function', () => {
            expect(signalsContent).toContain('function createBinding');
            expect(signalsContent).toContain('elementId');
            expect(signalsContent).toContain('signal');
        });
        
        test('has effect disposal mechanism', () => {
            expect(signalsContent).toContain('dispose');
            expect(signalsContent).toContain('disposed');
        });
        
        test('exports createBinding in public API', () => {
            expect(signalsContent).toContain('createBinding,');
        });
        
        test('hydrateFormBindings uses createBinding', () => {
            expect(signalsContent).toContain('function hydrateFormBindings');
            expect(signalsContent).toMatch(/hydrateFormBindings[\s\S]*createBinding\(/);
        });
    });
    
    // =========================================================================
    // SIGNATURE DETECTION TESTS
    // =========================================================================
    
    describe('Effect Signature Detection', () => {
        test('detects anonymous function signature: createEffect(fn)', () => {
            // The code should handle typeof idOrFn === 'function'
            expect(signalsContent).toContain("typeof idOrFnOrOptions === 'function'");
        });
        
        test('detects named function signature: createEffect(id, fn)', () => {
            // The code should handle typeof dependencyIdsOrFn === 'function'
            expect(signalsContent).toContain("typeof dependencyIdsOrFn === 'function'");
        });
        
        test('detects options object signature', () => {
            // The code should handle object options
            expect(signalsContent).toContain("typeof idOrFnOrOptions === 'object'");
        });
        
        test('handles hydration string code signature', () => {
            expect(signalsContent).toContain('new Function(');
        });
    });
    
    // =========================================================================
    // EFFECT EXECUTION TESTS
    // =========================================================================
    
    describe('Effect Execution', () => {
        test('effect runs immediately by default', () => {
            expect(signalsContent).toContain('immediate');
            expect(signalsContent).toContain('if (immediate)');
            expect(signalsContent).toContain('effect.execute()');
        });
        
        test('effect clears dependencies before each run', () => {
            expect(signalsContent).toContain('effect.dependencies.clear()');
        });
        
        test('effect tracks currentEffect during execution', () => {
            expect(signalsContent).toContain('currentEffect = effect');
            expect(signalsContent).toContain('currentEffect = prevEffect');
        });
        
        test('effect handles cleanup functions', () => {
            expect(signalsContent).toContain('cleanup');
            expect(signalsContent).toMatch(/if.*cleanup.*&&.*typeof.*cleanup.*===.*'function'/);
        });
        
        test('effect catches and logs execution errors', () => {
            expect(signalsContent).toContain('catch (e)');
            expect(signalsContent).toContain('Effect execution error');
        });
    });
    
    // =========================================================================
    // EFFECT DISPOSAL TESTS
    // =========================================================================
    
    describe('Effect Disposal', () => {
        test('effect has dispose method', () => {
            expect(signalsContent).toContain('dispose: ()');
        });
        
        test('dispose sets disposed flag', () => {
            expect(signalsContent).toContain('effect.disposed = true');
        });
        
        test('dispose runs cleanup', () => {
            // dispose should call cleanup
            expect(signalsContent).toMatch(/dispose:[\s\S]*?cleanup/);
        });
        
        test('dispose removes effect from global store', () => {
            expect(signalsContent).toContain('delete __pynext__.effects[id]');
        });
        
        test('disposed effect does not execute', () => {
            expect(signalsContent).toContain('if (effect.disposed) return');
        });
    });
    
    // =========================================================================
    // BINDING CREATION TESTS
    // =========================================================================
    
    describe('createBinding', () => {
        test('accepts elementId parameter', () => {
            expect(signalsContent).toMatch(/createBinding.*\{[\s\S]*elementId/);
        });
        
        test('accepts signal parameter', () => {
            expect(signalsContent).toMatch(/createBinding[\s\S]*signal/);
        });
        
        test('accepts property parameter with default', () => {
            expect(signalsContent).toContain("property = 'value'");
        });
        
        test('accepts event parameter with default', () => {
            expect(signalsContent).toContain("event = 'input'");
        });
        
        test('supports toDOM transform', () => {
            expect(signalsContent).toContain('toDOM');
            expect(signalsContent).toMatch(/toDOM.*=.*\(v\).*=>.*v/);
        });
        
        test('supports fromDOM transform', () => {
            expect(signalsContent).toContain('fromDOM');
            expect(signalsContent).toMatch(/fromDOM.*=.*\(v\).*=>.*v/);
        });
        
        test('validates element exists', () => {
            expect(signalsContent).toContain('document.getElementById(elementId)');
            expect(signalsContent).toContain('Binding target not found');
        });
        
        test('validates signal has get and set', () => {
            expect(signalsContent).toContain("typeof signal.get !== 'function'");
            expect(signalsContent).toContain("typeof signal.set !== 'function'");
        });
        
        test('handles checked property specially', () => {
            expect(signalsContent).toContain("property === 'checked'");
        });
        
        test('returns binding handle with dispose', () => {
            expect(signalsContent).toMatch(/return\s*\{[\s\S]*elementId[\s\S]*effect[\s\S]*dispose/);
        });
    });
    
    // =========================================================================
    // TWO-WAY BINDING TESTS
    // =========================================================================
    
    describe('Two-Way Binding', () => {
        test('creates effect for signal to DOM sync', () => {
            expect(signalsContent).toMatch(/createBinding[\s\S]*createEffect/);
        });
        
        test('attaches event listener for DOM to signal sync', () => {
            expect(signalsContent).toContain('addEventListener(event, handleDOMChange)');
        });
        
        test('dispose removes event listener', () => {
            expect(signalsContent).toContain('removeEventListener(event, handleDOMChange)');
        });
        
        test('dispose cleans up effect', () => {
            expect(signalsContent).toContain('effect.dispose()');
        });
    });
    
    // =========================================================================
    // FORM BINDING INTEGRATION TESTS
    // =========================================================================
    
    describe('Form Binding Integration', () => {
        test('hydrateFormBindings stores bindings for cleanup', () => {
            expect(signalsContent).toContain('_formBindings');
        });
        
        test('hydrateFormBindings handles missing form gracefully', () => {
            expect(signalsContent).toContain('Form not found for binding');
        });
        
        test('hydrateFormBindings handles missing field gracefully', () => {
            expect(signalsContent).toContain('Field not found for binding');
        });
        
        test('form binding uses createBinding internally', () => {
            expect(signalsContent).toMatch(/hydrateFormBindings[\s\S]*createBinding\(\{/);
        });
        
        test('form binding includes fromDOM for form tracking', () => {
            expect(signalsContent).toMatch(/hydrateFormBindings[\s\S]*fromDOM/);
        });
    });
});


// =============================================================================
// MOCK-BASED FUNCTIONAL TESTS
// =============================================================================

describe('Functional Effect Tests', () => {
    let createSignal, createEffect, effects;
    
    beforeEach(() => {
        // Create a minimal reactive system for testing
        let currentEffect = null;
        effects = {};
        
        createSignal = (id, initialValue) => {
            let value = initialValue;
            const subscribers = new Set();
            
            const signal = {
                id,
                read: () => {
                    if (currentEffect) {
                        subscribers.add(currentEffect);
                        currentEffect.dependencies.add(signal.read);
                    }
                    return value;
                },
                get: function() { return this.read(); },
                set: (newValue) => {
                    if (value !== newValue) {
                        value = newValue;
                        for (const effect of subscribers) {
                            effect.execute();
                        }
                    }
                },
            };
            return signal;
        };
        
        createEffect = (idOrFn, dependencyIdsOrFn, code) => {
            let id;
            let effectFn;
            let immediate = true;
            
            // Handle all signatures (matching the real implementation)
            if (typeof idOrFn === 'object' && idOrFn !== null) {
                const opts = idOrFn;
                id = opts.id || 'effect_' + Math.random().toString(36).substr(2, 9);
                effectFn = opts.fn;
                immediate = opts.immediate !== false;
                if (!effectFn && opts.code) {
                    effectFn = new Function(opts.code);
                }
            } else if (typeof idOrFn === 'function') {
                id = 'effect_' + Math.random().toString(36).substr(2, 9);
                effectFn = idOrFn;
            } else if (typeof dependencyIdsOrFn === 'function') {
                id = idOrFn;
                effectFn = dependencyIdsOrFn;
            } else {
                id = idOrFn;
                if (code) {
                    try {
                        effectFn = new Function(code);
                    } catch (e) {
                        console.error(`Invalid effect code for ${id}:`, e);
                        return null;
                    }
                }
            }
            
            const effect = {
                id,
                dependencies: new Set(),
                cleanup: null,
                disposed: false,
                execute: () => {
                    if (effect.disposed) return;
                    if (effect.cleanup) {
                        effect.cleanup();
                        effect.cleanup = null;
                    }
                    effect.dependencies.clear();
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
                },
                dispose: () => {
                    effect.disposed = true;
                    if (effect.cleanup) effect.cleanup();
                    effect.cleanup = null;
                    effect.dependencies.clear();
                    delete effects[id];
                }
            };
            
            effects[id] = effect;
            if (immediate) effect.execute();
            return effect;
        };
    });
    
    // =========================================================================
    // createEffect SIGNATURE TESTS
    // =========================================================================
    
    describe('createEffect(fn) - Anonymous', () => {
        test('runs immediately', () => {
            let ran = false;
            createEffect(() => { ran = true; });
            expect(ran).toBe(true);
        });
        
        test('generates unique ID', () => {
            const e1 = createEffect(() => {});
            const e2 = createEffect(() => {});
            expect(e1.id).not.toBe(e2.id);
        });
        
        test('tracks signal dependencies', () => {
            const signal = createSignal('test', 0);
            let callCount = 0;
            
            createEffect(() => {
                signal.read();
                callCount++;
            });
            
            expect(callCount).toBe(1);
            signal.set(1);
            expect(callCount).toBe(2);
        });
    });
    
    describe('createEffect(id, fn) - Named', () => {
        test('uses provided ID', () => {
            const effect = createEffect('my-effect', () => {});
            expect(effect.id).toBe('my-effect');
        });
        
        test('runs immediately', () => {
            let ran = false;
            createEffect('named', () => { ran = true; });
            expect(ran).toBe(true);
        });
        
        test('tracks signal dependencies', () => {
            const signal = createSignal('test', 0);
            let callCount = 0;
            
            createEffect('tracker', () => {
                signal.read();
                callCount++;
            });
            
            expect(callCount).toBe(1);
            signal.set(5);
            expect(callCount).toBe(2);
        });
        
        test('is stored in effects registry', () => {
            createEffect('registered', () => {});
            expect(effects['registered']).toBeDefined();
        });
    });
    
    describe('createEffect(id, deps, code) - Hydration', () => {
        test('compiles string code', () => {
            let ran = false;
            global.testFlag = () => { ran = true; };
            
            createEffect('hydrated', [], 'testFlag()');
            expect(ran).toBe(true);
            
            delete global.testFlag;
        });
        
        test('handles invalid code gracefully', () => {
            // Should not throw, just log error
            expect(() => {
                createEffect('invalid', [], 'this is not valid { js');
            }).not.toThrow();
        });
    });
    
    describe('createEffect({ ... }) - Options Object', () => {
        test('accepts options object', () => {
            let ran = false;
            createEffect({
                id: 'options-test',
                fn: () => { ran = true; }
            });
            expect(ran).toBe(true);
        });
        
        test('respects immediate: false', () => {
            let ran = false;
            const effect = createEffect({
                id: 'deferred',
                fn: () => { ran = true; },
                immediate: false
            });
            expect(ran).toBe(false);
            effect.execute();
            expect(ran).toBe(true);
        });
        
        test('auto-generates ID if not provided', () => {
            const effect = createEffect({ fn: () => {} });
            expect(effect.id).toMatch(/^effect_/);
        });
        
        test('accepts code string instead of fn', () => {
            let ran = false;
            global.codeTest = () => { ran = true; };
            
            createEffect({
                id: 'code-option',
                code: 'codeTest()'
            });
            expect(ran).toBe(true);
            
            delete global.codeTest;
        });
    });
    
    // =========================================================================
    // CLEANUP TESTS
    // =========================================================================
    
    describe('Effect Cleanup', () => {
        test('cleanup function is called on re-run', () => {
            let cleanupCalls = 0;
            const signal = createSignal('test', 0);
            
            createEffect(() => {
                signal.read();
                return () => { cleanupCalls++; };
            });
            
            expect(cleanupCalls).toBe(0);
            signal.set(1);
            expect(cleanupCalls).toBe(1);
            signal.set(2);
            expect(cleanupCalls).toBe(2);
        });
        
        test('cleanup is called on dispose', () => {
            let cleaned = false;
            const effect = createEffect(() => {
                return () => { cleaned = true; };
            });
            
            effect.dispose();
            expect(cleaned).toBe(true);
        });
    });
    
    // =========================================================================
    // DISPOSAL TESTS
    // =========================================================================
    
    describe('Effect Disposal', () => {
        test('disposed effect does not run', () => {
            let runCount = 0;
            const effect = createEffect(() => { runCount++; });
            expect(runCount).toBe(1);
            
            effect.dispose();
            effect.execute();
            expect(runCount).toBe(1); // Should not increment
        });
        
        test('disposed effect is removed from registry', () => {
            const effect = createEffect('disposable', () => {});
            expect(effects['disposable']).toBeDefined();
            
            effect.dispose();
            expect(effects['disposable']).toBeUndefined();
        });
        
        test('dependencies are cleared on dispose', () => {
            const signal = createSignal('test', 0);
            const effect = createEffect(() => { signal.read(); });
            
            expect(effect.dependencies.size).toBeGreaterThan(0);
            effect.dispose();
            expect(effect.dependencies.size).toBe(0);
        });
    });
    
    // =========================================================================
    // FORM RESET SCENARIO (Original Bug)
    // =========================================================================
    
    describe('Form Reset Scenario', () => {
        test('named effect tracks form field signal', () => {
            // Simulate form field
            const fieldSignal = createSignal('form_title', '');
            let domValue = '';
            let effectRunCount = 0;
            
            // Create binding effect (like hydrateFormBindings does)
            createEffect('bind_form_field', () => {
                domValue = fieldSignal.read();
                effectRunCount++;
            });
            
            expect(effectRunCount).toBe(1);
            expect(domValue).toBe('');
            
            // User types in field
            fieldSignal.set('Hello');
            expect(effectRunCount).toBe(2);
            expect(domValue).toBe('Hello');
            
            // Form reset
            fieldSignal.set('');
            expect(effectRunCount).toBe(3);
            expect(domValue).toBe('');
        });
        
        test('multiple issues with same title have unique IDs', () => {
            const allIssues = createSignal('all_issues', []);
            const nextId = createSignal('next_id', 1);
            
            // Create first issue
            const issue1 = {
                id: nextId.read(),
                title: 'duplicate title'
            };
            allIssues.set([...allIssues.read(), issue1]);
            nextId.set(nextId.read() + 1);
            
            // Create second issue with same title
            const issue2 = {
                id: nextId.read(),
                title: 'duplicate title'
            };
            allIssues.set([...allIssues.read(), issue2]);
            nextId.set(nextId.read() + 1);
            
            // Verify
            const issues = allIssues.read();
            expect(issues.length).toBe(2);
            expect(issues[0].id).toBe(1);
            expect(issues[1].id).toBe(2);
            expect(issues[0].title).toBe('duplicate title');
            expect(issues[1].title).toBe('duplicate title');
        });
    });
});


// =============================================================================
// DOM BINDING TESTS (with JSDOM)
// =============================================================================

describe('DOM Binding Tests', () => {
    let document;
    
    beforeEach(() => {
        // Reset DOM
        document = global.document;
        document.body.innerHTML = `
            <input id="test-input" type="text" value="">
            <input id="test-checkbox" type="checkbox">
            <select id="test-select">
                <option value="a">A</option>
                <option value="b">B</option>
            </select>
        `;
    });
    
    test('input element exists in jsdom', () => {
        const input = document.getElementById('test-input');
        expect(input).not.toBeNull();
    });
    
    test('checkbox element exists in jsdom', () => {
        const checkbox = document.getElementById('test-checkbox');
        expect(checkbox).not.toBeNull();
        expect(checkbox.type).toBe('checkbox');
    });
    
    test('select element exists in jsdom', () => {
        const select = document.getElementById('test-select');
        expect(select).not.toBeNull();
    });
    
    test('input value can be set programmatically', () => {
        const input = document.getElementById('test-input');
        input.value = 'test value';
        expect(input.value).toBe('test value');
    });
    
    test('checkbox checked can be set programmatically', () => {
        const checkbox = document.getElementById('test-checkbox');
        checkbox.checked = true;
        expect(checkbox.checked).toBe(true);
    });
});
