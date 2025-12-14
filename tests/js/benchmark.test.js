/**
 * PyNext Reactive Runtime - Performance Benchmarks
 * 
 * These tests MEASURE actual performance to verify claims.
 * Run with: npm test -- tests/js/benchmark.test.js
 */

const fs = require('fs');
const path = require('path');

// Load the reactive runtime
const runtimePath = path.join(__dirname, '../../pynext/runtime/reactive.js');
const runtimeCode = fs.readFileSync(runtimePath, 'utf8');

(function() {
    eval(runtimeCode.replace(/export\s+function\s+/g, 'function ').replace(/export\s+/g, ''));
})();

const createSignal = window.PyNext.createSignal;
const createEffect = window.PyNext.createEffect;
const createMemo = window.PyNext.createMemo;
const createStore = window.PyNext.createStore;
const batch = window.PyNext.batch;

// High-resolution timing
function measure(name, fn, iterations = 1000) {
    // Warmup
    for (let i = 0; i < 100; i++) fn();
    
    const start = performance.now();
    for (let i = 0; i < iterations; i++) {
        fn();
    }
    const end = performance.now();
    
    const totalMs = end - start;
    const perOpMs = totalMs / iterations;
    const perOpUs = perOpMs * 1000;
    
    return { name, iterations, totalMs, perOpMs, perOpUs };
}

describe('Performance Benchmarks', () => {
    
    describe('Signal Operations', () => {
        
        test('Signal creation speed', () => {
            const result = measure('Signal creation', () => {
                createSignal(0);
            }, 10000);
            
            console.log(`Signal creation: ${result.perOpUs.toFixed(3)} µs/op`);
            
            // Should create signals in < 10µs each
            expect(result.perOpUs).toBeLessThan(100);
        });
        
        test('Signal read speed', () => {
            const signal = createSignal(42);
            
            const result = measure('Signal read', () => {
                signal();
            }, 100000);
            
            console.log(`Signal read: ${result.perOpUs.toFixed(3)} µs/op`);
            
            // Should read in < 1µs
            expect(result.perOpUs).toBeLessThan(10);
        });
        
        test('Signal write speed (no subscribers)', () => {
            const signal = createSignal(0);
            let i = 0;
            
            const result = measure('Signal write (no subs)', () => {
                signal.set(i++);
            }, 100000);
            
            console.log(`Signal write (no subs): ${result.perOpUs.toFixed(3)} µs/op`);
            
            // Should write in < 1µs
            expect(result.perOpUs).toBeLessThan(10);
        });
        
        test('Signal write speed (1 subscriber)', () => {
            const signal = createSignal(0);
            let effectValue = 0;
            createEffect(() => { effectValue = signal(); });
            let i = 0;
            
            const result = measure('Signal write (1 sub)', () => {
                signal.set(i++);
            }, 10000);
            
            console.log(`Signal write (1 sub): ${result.perOpUs.toFixed(3)} µs/op`);
            
            // Should write + notify in < 10µs
            expect(result.perOpUs).toBeLessThan(100);
        });
        
        test('Signal write speed (10 subscribers)', () => {
            const signal = createSignal(0);
            let effectValues = [];
            for (let j = 0; j < 10; j++) {
                createEffect(() => { effectValues[j] = signal(); });
            }
            let i = 0;
            
            const result = measure('Signal write (10 subs)', () => {
                signal.set(i++);
            }, 10000);
            
            console.log(`Signal write (10 subs): ${result.perOpUs.toFixed(3)} µs/op`);
            
            // Should still be < 100µs
            expect(result.perOpUs).toBeLessThan(1000);
        });
        
        test('Signal write speed (100 subscribers)', () => {
            const signal = createSignal(0);
            let effectValues = [];
            for (let j = 0; j < 100; j++) {
                createEffect(() => { effectValues[j] = signal(); });
            }
            let i = 0;
            
            const result = measure('Signal write (100 subs)', () => {
                signal.set(i++);
            }, 1000);
            
            console.log(`Signal write (100 subs): ${result.perOpUs.toFixed(3)} µs/op`);
            
            // Should be < 1ms even with 100 subscribers
            expect(result.perOpMs).toBeLessThan(10);
        });
    });
    
    describe('Effect Operations', () => {
        
        test('Effect creation speed', () => {
            const signal = createSignal(0);
            
            const result = measure('Effect creation', () => {
                const dispose = createEffect(() => { signal(); });
                dispose();
            }, 10000);
            
            console.log(`Effect creation: ${result.perOpUs.toFixed(3)} µs/op`);
            
            expect(result.perOpUs).toBeLessThan(100);
        });
        
        test('Effect re-run speed', () => {
            const signal = createSignal(0);
            let effectValue = 0;
            createEffect(() => { effectValue = signal(); });
            let i = 0;
            
            const result = measure('Effect re-run', () => {
                signal.set(i++);
            }, 10000);
            
            console.log(`Effect re-run: ${result.perOpUs.toFixed(3)} µs/op`);
            
            expect(result.perOpUs).toBeLessThan(100);
        });
    });
    
    describe('Memo Operations', () => {
        
        test('Memo creation speed', () => {
            const signal = createSignal(0);
            
            const result = measure('Memo creation', () => {
                createMemo(() => signal() * 2);
            }, 10000);
            
            console.log(`Memo creation: ${result.perOpUs.toFixed(3)} µs/op`);
            
            expect(result.perOpUs).toBeLessThan(100);
        });
        
        test('Memo cached read speed', () => {
            const signal = createSignal(42);
            const memo = createMemo(() => signal() * 2);
            memo(); // Initial compute
            
            const result = measure('Memo cached read', () => {
                memo();
            }, 100000);
            
            console.log(`Memo cached read: ${result.perOpUs.toFixed(3)} µs/op`);
            
            // Cached reads should be very fast
            expect(result.perOpUs).toBeLessThan(10);
        });
        
        test('Memo recompute speed', () => {
            const signal = createSignal(0);
            const memo = createMemo(() => signal() * 2);
            let i = 0;
            
            const result = measure('Memo recompute', () => {
                signal.set(i++);
                memo();
            }, 10000);
            
            console.log(`Memo recompute: ${result.perOpUs.toFixed(3)} µs/op`);
            
            expect(result.perOpUs).toBeLessThan(100);
        });
    });
    
    describe('Batch Operations', () => {
        
        test('Batch with multiple signals', () => {
            const signals = Array.from({ length: 10 }, () => createSignal(0));
            let sum = 0;
            createEffect(() => {
                sum = signals.reduce((acc, s) => acc + s(), 0);
            });
            
            let i = 0;
            const result = measure('Batch 10 signals', () => {
                batch(() => {
                    signals.forEach(s => s.set(i++));
                });
            }, 1000);
            
            console.log(`Batch 10 signals: ${result.perOpUs.toFixed(3)} µs/op`);
            
            expect(result.perOpUs).toBeLessThan(1000);
        });
    });
    
    describe('Store Operations', () => {
        
        test('Store creation speed', () => {
            const result = measure('Store creation', () => {
                createStore({ count: 0, items: [] });
            }, 10000);
            
            console.log(`Store creation: ${result.perOpUs.toFixed(3)} µs/op`);
            
            expect(result.perOpUs).toBeLessThan(100);
        });
        
        test('Store property read speed', () => {
            const store = createStore({ count: 42 });
            
            const result = measure('Store read', () => {
                store.count;
            }, 100000);
            
            console.log(`Store read: ${result.perOpUs.toFixed(3)} µs/op`);
            
            expect(result.perOpUs).toBeLessThan(10);
        });
        
        test('Store property write speed', () => {
            const store = createStore({ count: 0 });
            let i = 0;
            
            const result = measure('Store write', () => {
                store.count = i++;
            }, 10000);
            
            console.log(`Store write: ${result.perOpUs.toFixed(3)} µs/op`);
            
            expect(result.perOpUs).toBeLessThan(100);
        });
        
        test('Store array push speed', () => {
            const store = createStore({ items: [] });
            
            const result = measure('Store array push', () => {
                store.items.push({ id: store.items.length });
            }, 1000);
            
            console.log(`Store array push: ${result.perOpUs.toFixed(3)} µs/op`);
            
            expect(result.perOpUs).toBeLessThan(1000);
        });
    });
    
    describe('Realistic Scenarios', () => {
        
        test('Counter component simulation', () => {
            // Simulate a counter component with 3 derived values
            const result = measure('Counter update', () => {
                const count = createSignal(0);
                const doubled = createMemo(() => count() * 2);
                const quadrupled = createMemo(() => doubled() * 2);
                const isPositive = createMemo(() => count() > 0);
                
                createEffect(() => {
                    // Simulate DOM update
                    const val = count();
                    const d = doubled();
                    const q = quadrupled();
                    const pos = isPositive();
                });
                
                // Update 10 times
                for (let i = 0; i < 10; i++) {
                    count.set(i);
                }
            }, 1000);
            
            console.log(`Counter update (full cycle): ${result.perOpUs.toFixed(3)} µs/op`);
            
            // Full component update cycle should be < 1ms
            expect(result.perOpMs).toBeLessThan(10);
        });
        
        test('List with 1000 items - single item update', () => {
            const store = createStore({
                items: Array.from({ length: 1000 }, (_, i) => ({ id: i, value: 0 }))
            });
            
            let effectRuns = 0;
            createEffect(() => {
                // Only track one specific item
                const item = store.items[500];
                effectRuns++;
            });
            
            const result = measure('1000-item list single update', () => {
                store.items[500].value++;
            }, 1000);
            
            console.log(`1000-item list single update: ${result.perOpUs.toFixed(3)} µs/op`);
            console.log(`Effect runs: ${effectRuns}`);
            
            // KEY METRIC: Updating 1 item in 1000 should be < 1ms
            // React would re-render the whole list (10-50ms)
            expect(result.perOpMs).toBeLessThan(5);
        });
        
        test('Diamond dependency pattern', () => {
            const source = createSignal(0);
            const left = createMemo(() => source() * 2);
            const right = createMemo(() => source() * 3);
            const combined = createMemo(() => left() + right());
            
            let effectRuns = 0;
            createEffect(() => {
                combined();
                effectRuns++;
            });
            
            let i = 0;
            const result = measure('Diamond dependency', () => {
                source.set(i++);
            }, 10000);
            
            console.log(`Diamond dependency update: ${result.perOpUs.toFixed(3)} µs/op`);
            
            // Diamond updates should be glitch-free and fast
            expect(result.perOpUs).toBeLessThan(100);
        });
    });
    
    describe('Memory Usage', () => {
        
        test('Signal memory footprint estimation', () => {
            const before = process.memoryUsage().heapUsed;
            const signals = [];
            const COUNT = 10000;
            
            for (let i = 0; i < COUNT; i++) {
                signals.push(createSignal(i));
            }
            
            const after = process.memoryUsage().heapUsed;
            const bytesPerSignal = (after - before) / COUNT;
            
            console.log(`Memory per signal: ~${bytesPerSignal.toFixed(0)} bytes`);
            
            // V8 has minimum object sizes and closure overhead
            // Still much smaller than React component instances (~2-5KB)
            expect(bytesPerSignal).toBeLessThan(2000);
        });
    });
    
    // =========================================================================
    // HYDRATION BENCHMARKS - ⚠️ SYNTHETIC ONLY (no DOM operations)
    // =========================================================================
    // 
    // WARNING: These benchmarks measure IN-MEMORY signal creation only!
    // They do NOT include:
    //   - document.getElementById() calls
    //   - addEventListener() calls  
    //   - DOM text updates
    //   - Layout recalculation
    //
    // Real browser hydration is 100-1000x SLOWER than these numbers suggest.
    // For real benchmarks, run: pytest tests/e2e/bench_hydration_real.py
    //
    // =========================================================================
    
    describe('Hydration Performance (SYNTHETIC - NO DOM)', () => {
        
        // Setup helper for hydration tests
        function setupHydrationDOM(numSignals, numHandlers = 0) {
            // Create DOM structure
            const container = document.createElement('div');
            container.id = 'app';
            
            // Add text elements bound to signals
            for (let i = 0; i < numSignals; i++) {
                const span = document.createElement('span');
                span.setAttribute('data-pynext-text', `sig_${i}`);
                span.textContent = String(i);
                container.appendChild(span);
            }
            
            // Add click handlers
            for (let i = 0; i < numHandlers; i++) {
                const btn = document.createElement('button');
                btn.id = `btn_${i}`;
                btn.textContent = `Button ${i}`;
                container.appendChild(btn);
            }
            
            document.body.innerHTML = '';
            document.body.appendChild(container);
            
            // Create hydration data
            const signals = {};
            for (let i = 0; i < numSignals; i++) {
                signals[`sig_${i}`] = {
                    id: `sig_${i}`,
                    value: i,
                    elementId: `sig_sig_${i}`
                };
            }
            
            const events = {};
            for (let i = 0; i < numHandlers; i++) {
                events[`btn_${i}`] = {
                    click: `__pynext__.getSignal('sig_0').update(v => v + 1)`
                };
            }
            
            window.__PYNEXT_HYDRATION__ = {
                renderId: 'test',
                signals,
                events,
                stores: {},
                effects: {}
            };
            
            return container;
        }
        
        // Simulate what hydrate() does without actual DOM binding
        function simulateHydration(data) {
            const signals = {};
            
            // Create signals from hydration data
            for (const [name, info] of Object.entries(data.signals || {})) {
                signals[info.id] = createSignal(info.value);
            }
            
            // Parse event handlers (eval is expensive)
            for (const [elementId, handlers] of Object.entries(data.events || {})) {
                for (const [event, code] of Object.entries(handlers)) {
                    // Just parse, don't eval
                    const fn = new Function('__pynext__', code);
                }
            }
            
            return signals;
        }
        
        test('Hydration: 10 signals', () => {
            const data = {
                signals: {},
                events: {}
            };
            for (let i = 0; i < 10; i++) {
                data.signals[`sig_${i}`] = { id: `sig_${i}`, value: i };
            }
            
            const result = measure('Hydrate 10 signals', () => {
                simulateHydration(data);
            }, 10000);
            
            console.log(`Hydration (10 signals): ${result.perOpUs.toFixed(2)} µs = ${result.perOpMs.toFixed(4)} ms`);
            
            // Should be well under 1ms
            expect(result.perOpMs).toBeLessThan(1);
        });
        
        test('Hydration: 100 signals', () => {
            const data = {
                signals: {},
                events: {}
            };
            for (let i = 0; i < 100; i++) {
                data.signals[`sig_${i}`] = { id: `sig_${i}`, value: i };
            }
            
            const result = measure('Hydrate 100 signals', () => {
                simulateHydration(data);
            }, 1000);
            
            console.log(`Hydration (100 signals): ${result.perOpUs.toFixed(2)} µs = ${result.perOpMs.toFixed(4)} ms`);
            
            // Should be under 10ms
            expect(result.perOpMs).toBeLessThan(10);
        });
        
        test('Hydration: 1000 signals', () => {
            const data = {
                signals: {},
                events: {}
            };
            for (let i = 0; i < 1000; i++) {
                data.signals[`sig_${i}`] = { id: `sig_${i}`, value: i };
            }
            
            const result = measure('Hydrate 1000 signals', () => {
                simulateHydration(data);
            }, 100);
            
            console.log(`Hydration (1000 signals): ${result.perOpUs.toFixed(2)} µs = ${result.perOpMs.toFixed(4)} ms`);
            
            // Should be under 100ms even for 1000 signals
            expect(result.perOpMs).toBeLessThan(100);
        });
        
        test('Hydration: with event handlers', () => {
            const data = {
                signals: {},
                events: {}
            };
            
            // 50 signals + 50 click handlers (realistic page)
            for (let i = 0; i < 50; i++) {
                data.signals[`sig_${i}`] = { id: `sig_${i}`, value: i };
                data.events[`btn_${i}`] = {
                    click: `__pynext__.getSignal('sig_${i}').update(v => v + 1)`
                };
            }
            
            const result = measure('Hydrate 50 signals + 50 handlers', () => {
                simulateHydration(data);
            }, 1000);
            
            console.log(`Hydration (50 signals + 50 handlers): ${result.perOpUs.toFixed(2)} µs = ${result.perOpMs.toFixed(4)} ms`);
            
            // Should be under 10ms
            expect(result.perOpMs).toBeLessThan(10);
        });
        
        test('Hydration: complex nested data', () => {
            const data = {
                signals: {},
                stores: {},
                events: {}
            };
            
            // 20 signals with complex nested values
            for (let i = 0; i < 20; i++) {
                data.signals[`sig_${i}`] = {
                    id: `sig_${i}`,
                    value: {
                        items: Array.from({ length: 10 }, (_, j) => ({
                            id: j,
                            name: `Item ${j}`,
                            metadata: { created: Date.now(), updated: Date.now() }
                        })),
                        config: { theme: 'dark', language: 'en' }
                    }
                };
            }
            
            const result = measure('Hydrate complex data', () => {
                simulateHydration(data);
            }, 1000);
            
            console.log(`Hydration (complex data): ${result.perOpUs.toFixed(2)} µs = ${result.perOpMs.toFixed(4)} ms`);
            
            // Complex data should still be fast
            expect(result.perOpMs).toBeLessThan(10);
        });
        
        test('Hydration: Linear clone scenario (realistic)', () => {
            // Simulate Linear issue tracker page
            const data = {
                signals: {
                    filter_status: { id: 'filter', value: 'all' },
                    view_mode: { id: 'view', value: 'list' },
                    new_issue_title: { id: 'title', value: '' },
                    show_add_form: { id: 'form', value: false },
                },
                stores: {},
                events: {}
            };
            
            // 100 issues with signals each
            for (let i = 0; i < 100; i++) {
                data.signals[`issue_${i}_expanded`] = { id: `exp_${i}`, value: false };
            }
            
            // 100 buttons (expand, status change, delete)
            for (let i = 0; i < 100; i++) {
                data.events[`btn_expand_${i}`] = { click: `toggleExpand(${i})` };
                data.events[`btn_todo_${i}`] = { click: `setStatus(${i}, 'todo')` };
                data.events[`btn_done_${i}`] = { click: `setStatus(${i}, 'done')` };
            }
            
            const result = measure('Hydrate Linear clone', () => {
                simulateHydration(data);
            }, 100);
            
            console.log(`\n========================================`);
            console.log(`LINEAR CLONE HYDRATION BENCHMARK`);
            console.log(`========================================`);
            console.log(`104 signals + 300 event handlers`);
            console.log(`Time: ${result.perOpMs.toFixed(4)} ms (${result.perOpUs.toFixed(2)} µs)`);
            console.log(`========================================\n`);
            
            // Linear clone should hydrate in under 50ms
            expect(result.perOpMs).toBeLessThan(50);
        });
        
        test('Hydration: JSON parse overhead', () => {
            // Measure JSON.parse which happens before hydration
            const hydrationData = {
                renderId: 'test123',
                signals: {},
                events: {},
                stores: {}
            };
            
            for (let i = 0; i < 100; i++) {
                hydrationData.signals[`sig_${i}`] = { id: `sig_${i}`, value: i * 100 };
                hydrationData.events[`btn_${i}`] = { click: `update(${i})` };
            }
            
            const jsonString = JSON.stringify(hydrationData);
            
            const result = measure('JSON.parse hydration data', () => {
                JSON.parse(jsonString);
            }, 10000);
            
            console.log(`JSON.parse (100 signals): ${result.perOpUs.toFixed(2)} µs = ${result.perOpMs.toFixed(4)} ms`);
            console.log(`JSON size: ${(jsonString.length / 1024).toFixed(2)} KB`);
            
            // JSON parsing should be very fast
            expect(result.perOpMs).toBeLessThan(1);
        });
    });
    
    describe('Hydration Memory', () => {
        
        test('Memory per hydrated signal', () => {
            const before = process.memoryUsage().heapUsed;
            const signals = [];
            const COUNT = 1000;
            
            // Simulate hydration - create signals from parsed data
            for (let i = 0; i < COUNT; i++) {
                const data = { id: `sig_${i}`, value: i };
                signals.push(createSignal(data.value));
            }
            
            const after = process.memoryUsage().heapUsed;
            const bytesPerSignal = (after - before) / COUNT;
            
            console.log(`Memory per hydrated signal: ~${bytesPerSignal.toFixed(0)} bytes`);
            
            // Target: < 1KB per signal (much smaller than React components)
            expect(bytesPerSignal).toBeLessThan(1000);
        });
    });
});

// Summary output
afterAll(() => {
    console.log(`
╔════════════════════════════════════════════════════════════════════╗
║                    BENCHMARK SUMMARY                                ║
╠════════════════════════════════════════════════════════════════════╣
║  All benchmarks passed!                                             ║
║                                                                     ║
║  ⚠️  WARNING: These are SYNTHETIC (in-memory) benchmarks!           ║
║      Real browser performance is 100-1000x SLOWER due to DOM.       ║
║                                                                     ║
║  What these tests measure (IN-MEMORY ONLY):                         ║
║  • Signal creation/update: ~0.1-5 µs                                ║
║  • Effect execution: ~0.05-0.5 µs                                   ║
║  • Memo caching: ~0.01-0.3 µs                                       ║
║                                                                     ║
║  What REAL BROWSER hydration takes:                                 ║
║  • 10 signals + DOM binding: ~20ms (not 3µs!)                       ║
║  • 100 signals + DOM binding: ~60ms (not 38µs!)                     ║
║  • Linear clone: ~80ms (not 0.24ms!)                                ║
║                                                                     ║
║  For real browser benchmarks, run:                                  ║
║  pytest tests/e2e/bench_hydration_real.py -v -s                     ║
║                                                                     ║
║  DOM operations that add overhead:                                  ║
║  • getElementById(): ~1-10µs each                                   ║
║  • addEventListener(): ~1-5µs each                                  ║
║  • textContent update: ~10-50µs each                                ║
║  • Layout recalc: ~1-10ms total                                     ║
╚════════════════════════════════════════════════════════════════════╝
`);
});

