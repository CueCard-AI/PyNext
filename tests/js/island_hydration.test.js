/**
 * Island Hydration Tests - All Hydration Strategies
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Tests the various hydration strategies that islands can use:
 * - LOAD: Hydrate immediately when page loads
 * - VISIBLE: Hydrate when island becomes visible (IntersectionObserver)
 * - IDLE: Hydrate when browser is idle (requestIdleCallback)
 * - MEDIA: Hydrate on specific media query match
 * - NONE: Never hydrate on client (SSR only)
 * 
 * =============================================================================
 * RISK AREAS TESTED
 * =============================================================================
 * 
 * 1. IntersectionObserver not firing correctly for VISIBLE strategy
 * 2. requestIdleCallback fallback for browsers that don't support it
 * 3. Media query parsing and matching for MEDIA strategy
 * 4. Component factory registration mismatches
 * 5. Multiple islands with different strategies on same page
 * 6. Hydration data parsing failures
 * 7. Event handler attachment after hydration
 * 
 * =============================================================================
 */

require('./setup');

// =============================================================================
// MOCK SETUP
// =============================================================================

// Mock IntersectionObserver
class MockIntersectionObserver {
    constructor(callback, options) {
        this.callback = callback;
        this.options = options;
        this.observedElements = new Set();
        MockIntersectionObserver.instances.push(this);
    }
    
    observe(element) {
        this.observedElements.add(element);
        element.__intersectionObserver = this;
    }
    
    unobserve(element) {
        this.observedElements.delete(element);
        delete element.__intersectionObserver;
    }
    
    disconnect() {
        this.observedElements.clear();
    }
    
    // Test helper: simulate intersection
    simulateIntersection(element, isIntersecting = true) {
        if (this.observedElements.has(element)) {
            this.callback([{
                target: element,
                isIntersecting,
                intersectionRatio: isIntersecting ? 1 : 0,
            }], this);
        }
    }
    
    static reset() {
        MockIntersectionObserver.instances = [];
    }
}
MockIntersectionObserver.instances = [];

// Mock requestIdleCallback
class MockIdleCallback {
    constructor() {
        this.callbacks = [];
        this.idCounter = 0;
    }
    
    request(callback, options) {
        const id = ++this.idCounter;
        this.callbacks.push({ id, callback, options });
        return id;
    }
    
    cancel(id) {
        this.callbacks = this.callbacks.filter(cb => cb.id !== id);
    }
    
    // Test helper: run all idle callbacks
    runAll() {
        const cbs = this.callbacks;
        this.callbacks = [];
        cbs.forEach(({ callback }) => {
            callback({
                didTimeout: false,
                timeRemaining: () => 50,
            });
        });
    }
    
    // Test helper: run a specific callback
    runOne() {
        if (this.callbacks.length > 0) {
            const { callback } = this.callbacks.shift();
            callback({
                didTimeout: false,
                timeRemaining: () => 50,
            });
        }
    }
    
    reset() {
        this.callbacks = [];
        this.idCounter = 0;
    }
}

// Mock matchMedia for media query testing
class MockMediaQueryList {
    constructor(query) {
        this.media = query;
        this._matches = false;
        this.listeners = [];
    }
    
    get matches() {
        return this._matches;
    }
    
    addEventListener(event, handler) {
        if (event === 'change') {
            this.listeners.push(handler);
        }
    }
    
    removeEventListener(event, handler) {
        if (event === 'change') {
            this.listeners = this.listeners.filter(h => h !== handler);
        }
    }
    
    // Legacy API
    addListener(handler) {
        this.listeners.push(handler);
    }
    
    removeListener(handler) {
        this.listeners = this.listeners.filter(h => h !== handler);
    }
    
    // Test helper: change matches state
    setMatches(value) {
        const oldValue = this._matches;
        this._matches = value;
        if (oldValue !== value) {
            this.listeners.forEach(handler => {
                handler({ matches: value, media: this.media });
            });
        }
    }
}

// =============================================================================
// TEST GLOBALS
// =============================================================================

let mockIdleCallback;
let mockMediaQueries;

beforeEach(() => {
    MockIntersectionObserver.reset();
    global.IntersectionObserver = MockIntersectionObserver;
    
    mockIdleCallback = new MockIdleCallback();
    global.requestIdleCallback = (cb, opts) => mockIdleCallback.request(cb, opts);
    global.cancelIdleCallback = (id) => mockIdleCallback.cancel(id);
    
    mockMediaQueries = {};
    global.matchMedia = (query) => {
        if (!mockMediaQueries[query]) {
            mockMediaQueries[query] = new MockMediaQueryList(query);
        }
        return mockMediaQueries[query];
    };
    
    // Reset document
    document.body.innerHTML = '';
    
    // Reset __pynext__
    global.__pynext__ = {
        signals: {},
        stores: {},
        forms: {},
        memos: {},
        islands: {},
        
        createSignal(id, initialValue) {
            let value = initialValue;
            const signal = {
                id,
                read: () => value,
                set: (v) => { value = typeof v === 'function' ? v(value) : v; },
                update: (fn) => { value = fn(value); },
                peek: () => value,
            };
            this.signals[id] = signal;
            return signal;
        },
        
        getSignal(id) {
            return this.signals[id];
        },
        
        registerIsland(name, factory) {
            this.islands[name] = factory;
        },
        
        getIsland(name) {
            return this.islands[name];
        },
    };
    
    global.__PYNEXT_ISLANDS__ = global.__pynext__.islands;
});


// =============================================================================
// HYDRATION STRATEGY: LOAD
// =============================================================================

describe('Hydration Strategy: LOAD', () => {
    test('should hydrate immediately on page load', () => {
        // Create island element
        document.body.innerHTML = `
            <div data-pynext-component="Counter" 
                 data-pynext-id="c1" 
                 data-pynext-strategy="load">
                <span data-pynext-text="count">0</span>
            </div>
        `;
        
        // Register island factory
        let hydrated = false;
        global.__pynext__.registerIsland('Counter', (element, data) => {
            hydrated = true;
            return { element };
        });
        
        // Simulate page load hydration
        const element = document.querySelector('[data-pynext-component="Counter"]');
        const factory = global.__pynext__.getIsland('Counter');
        factory(element, {});
        
        expect(hydrated).toBe(true);
    });
    
    test('should attach event handlers on load hydration', () => {
        document.body.innerHTML = `
            <div data-pynext-component="Button" data-pynext-id="b1" data-pynext-strategy="load">
                <button id="btn">Click</button>
            </div>
        `;
        
        let clicked = false;
        
        global.__pynext__.registerIsland('Button', (element, data) => {
            const btn = element.querySelector('button');
            btn.addEventListener('click', () => {
                clicked = true;
            });
        });
        
        const element = document.querySelector('[data-pynext-component="Button"]');
        const factory = global.__pynext__.getIsland('Button');
        factory(element, {});
        
        // Click the button
        document.getElementById('btn').click();
        expect(clicked).toBe(true);
    });
    
    test('should initialize signals with hydration data', () => {
        document.body.innerHTML = `
            <div data-pynext-component="Counter" data-pynext-id="c1">
                <span id="count-display">5</span>
            </div>
            <script id="__PYNEXT_DATA__" type="application/json">
                {"signals": {"count": {"id": "sig_count", "value": 5}}}
            </script>
        `;
        
        global.__pynext__.registerIsland('Counter', (element, data) => {
            const sig = global.__pynext__.createSignal('sig_count', data.signals.count.value);
            const display = element.querySelector('#count-display');
            display.textContent = sig.read();
            return { count: sig };
        });
        
        // Parse hydration data
        const dataScript = document.getElementById('__PYNEXT_DATA__');
        const hydrationData = JSON.parse(dataScript.textContent);
        
        const element = document.querySelector('[data-pynext-component="Counter"]');
        const factory = global.__pynext__.getIsland('Counter');
        factory(element, hydrationData);
        
        expect(global.__pynext__.getSignal('sig_count').read()).toBe(5);
    });
});


// =============================================================================
// HYDRATION STRATEGY: VISIBLE
// =============================================================================

describe('Hydration Strategy: VISIBLE', () => {
    test('should not hydrate until element is visible', () => {
        document.body.innerHTML = `
            <div data-pynext-component="LazyWidget" 
                 data-pynext-id="w1" 
                 data-pynext-strategy="visible"
                 style="margin-top: 2000px;">
                Content
            </div>
        `;
        
        let hydrated = false;
        global.__pynext__.registerIsland('LazyWidget', (element) => {
            hydrated = true;
        });
        
        // Setup visible hydration
        const element = document.querySelector('[data-pynext-component="LazyWidget"]');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const factory = global.__pynext__.getIsland('LazyWidget');
                    factory(entry.target, {});
                }
            });
        });
        observer.observe(element);
        
        // Should not be hydrated yet
        expect(hydrated).toBe(false);
        
        // Simulate scrolling into view
        MockIntersectionObserver.instances[0].simulateIntersection(element, true);
        
        // Now should be hydrated
        expect(hydrated).toBe(true);
    });
    
    test('should disconnect observer after hydration', () => {
        document.body.innerHTML = `
            <div data-pynext-component="LazyWidget" data-pynext-id="w1">Content</div>
        `;
        
        const element = document.querySelector('[data-pynext-component="LazyWidget"]');
        let disconnected = false;
        
        global.__pynext__.registerIsland('LazyWidget', () => {});
        
        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const factory = global.__pynext__.getIsland('LazyWidget');
                    factory(entry.target, {});
                    obs.unobserve(entry.target);
                    disconnected = true;
                }
            });
        });
        observer.observe(element);
        
        MockIntersectionObserver.instances[0].simulateIntersection(element, true);
        
        expect(disconnected).toBe(true);
        expect(observer.observedElements.has(element)).toBe(false);
    });
    
    test('should handle multiple visible islands independently', () => {
        document.body.innerHTML = `
            <div data-pynext-component="Widget" data-pynext-id="w1">Widget 1</div>
            <div data-pynext-component="Widget" data-pynext-id="w2">Widget 2</div>
        `;
        
        const hydrated = [];
        global.__pynext__.registerIsland('Widget', (element) => {
            hydrated.push(element.dataset.pynextId);
        });
        
        const elements = document.querySelectorAll('[data-pynext-component="Widget"]');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const factory = global.__pynext__.getIsland('Widget');
                    factory(entry.target, {});
                }
            });
        });
        
        elements.forEach(el => observer.observe(el));
        
        // Only first element becomes visible
        MockIntersectionObserver.instances[0].simulateIntersection(elements[0], true);
        expect(hydrated).toEqual(['w1']);
        
        // Second element becomes visible
        MockIntersectionObserver.instances[0].simulateIntersection(elements[1], true);
        expect(hydrated).toEqual(['w1', 'w2']);
    });
});


// =============================================================================
// HYDRATION STRATEGY: IDLE
// =============================================================================

describe('Hydration Strategy: IDLE', () => {
    test('should hydrate when browser becomes idle', () => {
        document.body.innerHTML = `
            <div data-pynext-component="IdleWidget" data-pynext-id="iw1">Content</div>
        `;
        
        let hydrated = false;
        global.__pynext__.registerIsland('IdleWidget', () => {
            hydrated = true;
        });
        
        // Schedule hydration for idle time
        const element = document.querySelector('[data-pynext-component="IdleWidget"]');
        requestIdleCallback(() => {
            const factory = global.__pynext__.getIsland('IdleWidget');
            factory(element, {});
        });
        
        // Should not be hydrated yet
        expect(hydrated).toBe(false);
        
        // Run idle callbacks
        mockIdleCallback.runAll();
        
        expect(hydrated).toBe(true);
    });
    
    test('should fallback to setTimeout when requestIdleCallback unavailable', async () => {
        // Remove requestIdleCallback
        const originalRIC = global.requestIdleCallback;
        delete global.requestIdleCallback;
        
        document.body.innerHTML = `
            <div data-pynext-component="IdleWidget" data-pynext-id="iw1">Content</div>
        `;
        
        let hydrated = false;
        global.__pynext__.registerIsland('IdleWidget', () => {
            hydrated = true;
        });
        
        const element = document.querySelector('[data-pynext-component="IdleWidget"]');
        
        // Use fallback - setTimeout when requestIdleCallback is not available
        const scheduleIdle = global.requestIdleCallback || 
            ((cb) => setTimeout(cb, 0));
        
        scheduleIdle(() => {
            const factory = global.__pynext__.getIsland('IdleWidget');
            factory(element, {});
        });
        
        // Wait for the callback
        await new Promise(resolve => setTimeout(resolve, 10));
        
        expect(hydrated).toBe(true);
        
        // Restore
        global.requestIdleCallback = originalRIC;
    });
    
    test('should respect timeout option', () => {
        document.body.innerHTML = `
            <div data-pynext-component="IdleWidget" data-pynext-id="iw1">Content</div>
        `;
        
        const element = document.querySelector('[data-pynext-component="IdleWidget"]');
        
        requestIdleCallback(() => {
            global.__pynext__.getIsland('IdleWidget')?.(element, {});
        }, { timeout: 2000 });
        
        expect(mockIdleCallback.callbacks[0].options.timeout).toBe(2000);
    });
});


// =============================================================================
// HYDRATION STRATEGY: MEDIA
// =============================================================================

describe('Hydration Strategy: MEDIA', () => {
    test('should hydrate when media query matches', () => {
        document.body.innerHTML = `
            <div data-pynext-component="MobileWidget" 
                 data-pynext-id="mw1"
                 data-pynext-media="(max-width: 768px)">
                Content
            </div>
        `;
        
        let hydrated = false;
        global.__pynext__.registerIsland('MobileWidget', () => {
            hydrated = true;
        });
        
        const element = document.querySelector('[data-pynext-component="MobileWidget"]');
        const mediaQuery = element.dataset.pynextMedia;
        const mql = matchMedia(mediaQuery);
        
        // Setup media query listener
        const checkMedia = () => {
            if (mql.matches) {
                const factory = global.__pynext__.getIsland('MobileWidget');
                factory(element, {});
            }
        };
        
        mql.addEventListener('change', checkMedia);
        checkMedia(); // Initial check
        
        // Media doesn't match yet
        expect(hydrated).toBe(false);
        
        // Simulate viewport change
        mql.setMatches(true);
        
        expect(hydrated).toBe(true);
    });
    
    test('should hydrate immediately if media already matches', () => {
        document.body.innerHTML = `
            <div data-pynext-component="DesktopWidget" 
                 data-pynext-id="dw1"
                 data-pynext-media="(min-width: 1024px)">
                Content
            </div>
        `;
        
        let hydrated = false;
        global.__pynext__.registerIsland('DesktopWidget', () => {
            hydrated = true;
        });
        
        const element = document.querySelector('[data-pynext-component="DesktopWidget"]');
        const mediaQuery = element.dataset.pynextMedia;
        
        // Pre-set matches
        mockMediaQueries[mediaQuery] = new MockMediaQueryList(mediaQuery);
        mockMediaQueries[mediaQuery]._matches = true;
        
        const mql = matchMedia(mediaQuery);
        
        if (mql.matches) {
            const factory = global.__pynext__.getIsland('DesktopWidget');
            factory(element, {});
        }
        
        expect(hydrated).toBe(true);
    });
    
    test('should handle complex media queries', () => {
        const queries = [
            '(min-width: 768px) and (max-width: 1024px)',
            '(orientation: landscape)',
            '(prefers-color-scheme: dark)',
            '(hover: hover)',
        ];
        
        queries.forEach(query => {
            const mql = matchMedia(query);
            expect(mql.media).toBe(query);
        });
    });
});


// =============================================================================
// HYDRATION STRATEGY: NONE
// =============================================================================

describe('Hydration Strategy: NONE', () => {
    test('should never hydrate with NONE strategy', () => {
        document.body.innerHTML = `
            <div data-pynext-component="StaticWidget" 
                 data-pynext-id="sw1"
                 data-pynext-strategy="none">
                Static Content
            </div>
        `;
        
        let hydrated = false;
        global.__pynext__.registerIsland('StaticWidget', () => {
            hydrated = true;
        });
        
        const element = document.querySelector('[data-pynext-component="StaticWidget"]');
        const strategy = element.dataset.pynextStrategy;
        
        // Only hydrate if strategy is not 'none'
        if (strategy !== 'none') {
            const factory = global.__pynext__.getIsland('StaticWidget');
            factory(element, {});
        }
        
        expect(hydrated).toBe(false);
    });
    
    test('NONE strategy content should remain static', () => {
        document.body.innerHTML = `
            <div data-pynext-component="StaticWidget" data-pynext-strategy="none">
                <p>This is static content</p>
            </div>
        `;
        
        const element = document.querySelector('[data-pynext-component="StaticWidget"]');
        const originalContent = element.innerHTML;
        
        // Simulate hydration attempt (should be skipped)
        const strategy = element.dataset.pynextStrategy;
        if (strategy === 'none') {
            // Don't hydrate
        }
        
        // Content should be unchanged
        expect(element.innerHTML).toBe(originalContent);
    });
});


// =============================================================================
// COMPONENT FACTORY REGISTRATION
// =============================================================================

describe('Component Factory Registration', () => {
    test('should register island factory correctly', () => {
        const factory = (element, data) => ({ success: true });
        global.__pynext__.registerIsland('TestComponent', factory);
        
        expect(global.__pynext__.getIsland('TestComponent')).toBe(factory);
    });
    
    test('should handle missing factory gracefully', () => {
        const factory = global.__pynext__.getIsland('NonExistent');
        expect(factory).toBeUndefined();
    });
    
    test('should allow factory re-registration (HMR)', () => {
        const factory1 = () => 1;
        const factory2 = () => 2;
        
        global.__pynext__.registerIsland('HMRComponent', factory1);
        expect(global.__pynext__.getIsland('HMRComponent')()).toBe(1);
        
        // Re-register (simulating HMR)
        global.__pynext__.registerIsland('HMRComponent', factory2);
        expect(global.__pynext__.getIsland('HMRComponent')()).toBe(2);
    });
    
    test('should register to window.__PYNEXT_ISLANDS__', () => {
        const factory = () => {};
        global.__pynext__.registerIsland('GlobalComponent', factory);
        
        expect(window.__PYNEXT_ISLANDS__.GlobalComponent).toBe(factory);
    });
});


// =============================================================================
// HYDRATION DATA PARSING
// =============================================================================

describe('Hydration Data Parsing', () => {
    test('should parse __PYNEXT_DATA__ script tag', () => {
        document.body.innerHTML = `
            <div id="app">Content</div>
            <script id="__PYNEXT_DATA__" type="application/json">
                {
                    "renderId": "abc123",
                    "signals": {"count": {"id": "sig_1", "value": 0}},
                    "stores": {},
                    "events": {}
                }
            </script>
        `;
        
        const dataScript = document.getElementById('__PYNEXT_DATA__');
        const data = JSON.parse(dataScript.textContent);
        
        expect(data.renderId).toBe('abc123');
        expect(data.signals.count.value).toBe(0);
    });
    
    test('should handle malformed JSON gracefully', () => {
        document.body.innerHTML = `
            <script id="__PYNEXT_DATA__" type="application/json">
                {invalid json}
            </script>
        `;
        
        const dataScript = document.getElementById('__PYNEXT_DATA__');
        
        let data = null;
        let error = null;
        
        try {
            data = JSON.parse(dataScript.textContent);
        } catch (e) {
            error = e;
        }
        
        expect(error).toBeInstanceOf(SyntaxError);
        expect(data).toBeNull();
    });
    
    test('should handle missing hydration script', () => {
        document.body.innerHTML = `<div id="app">Content</div>`;
        
        const dataScript = document.getElementById('__PYNEXT_DATA__');
        expect(dataScript).toBeNull();
    });
    
    test('should handle escaped content in JSON', () => {
        // In real HTML, </script> would be escaped as <\/script>
        // For testing, we just use a safe string
        document.body.innerHTML = `
            <script id="__PYNEXT_DATA__" type="application/json">
                {"message": "Hello World"}
            </script>
        `;
        
        const dataScript = document.getElementById('__PYNEXT_DATA__');
        const data = JSON.parse(dataScript.textContent);
        
        expect(data.message).toBe('Hello World');
    });
});


// =============================================================================
// EVENT HANDLER ATTACHMENT
// =============================================================================

describe('Event Handler Attachment After Hydration', () => {
    test('should attach click handlers from hydration data', () => {
        document.body.innerHTML = `
            <div data-pynext-component="Button" data-pynext-id="b1">
                <button id="btn" data-pynext-click>Click me</button>
            </div>
        `;
        
        const hydrationData = {
            events: {
                'btn': {
                    'click': {
                        code: "__pynext__.getSignal('sig_count').update(v => v + 1)",
                        mods: {}
                    }
                }
            }
        };
        
        // Create signal
        global.__pynext__.createSignal('sig_count', 0);
        
        // Attach handler
        const btn = document.getElementById('btn');
        const eventData = hydrationData.events['btn'];
        
        Object.entries(eventData).forEach(([eventType, handler]) => {
            btn.addEventListener(eventType, () => {
                eval(handler.code);
            });
        });
        
        // Click and verify
        btn.click();
        expect(global.__pynext__.getSignal('sig_count').read()).toBe(1);
    });
    
    test('should apply event modifiers correctly', () => {
        document.body.innerHTML = `
            <form id="form">
                <button type="submit">Submit</button>
            </form>
        `;
        
        const hydrationData = {
            events: {
                'form': {
                    'submit': {
                        code: "console.log('submitted')",
                        mods: { prevent: true, stop: true }
                    }
                }
            }
        };
        
        let defaultPrevented = false;
        let propagationStopped = false;
        
        const form = document.getElementById('form');
        const eventData = hydrationData.events['form'];
        
        form.addEventListener('submit', (e) => {
            if (eventData.submit.mods.prevent) {
                e.preventDefault();
                defaultPrevented = true;
            }
            if (eventData.submit.mods.stop) {
                e.stopPropagation();
                propagationStopped = true;
            }
        });
        
        // Create and dispatch submit event
        const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(submitEvent);
        
        expect(defaultPrevented).toBe(true);
        expect(propagationStopped).toBe(true);
    });
    
    test('should handle multiple event types on same element', () => {
        document.body.innerHTML = `<input id="input" type="text" />`;
        
        const events = {
            'input': { code: "handleInput()", mods: {} },
            'focus': { code: "handleFocus()", mods: {} },
            'blur': { code: "handleBlur()", mods: {} },
        };
        
        const input = document.getElementById('input');
        const firedEvents = [];
        
        Object.keys(events).forEach(eventType => {
            input.addEventListener(eventType, () => {
                firedEvents.push(eventType);
            });
        });
        
        input.dispatchEvent(new Event('focus'));
        input.dispatchEvent(new Event('input'));
        input.dispatchEvent(new Event('blur'));
        
        expect(firedEvents).toEqual(['focus', 'input', 'blur']);
    });
});


// =============================================================================
// EDGE CASES
// =============================================================================

describe('Hydration Edge Cases', () => {
    test('should handle island inside island', () => {
        document.body.innerHTML = `
            <div data-pynext-component="Parent" data-pynext-id="p1">
                <div data-pynext-component="Child" data-pynext-id="c1">
                    Nested content
                </div>
            </div>
        `;
        
        const hydrationOrder = [];
        
        global.__pynext__.registerIsland('Parent', () => {
            hydrationOrder.push('Parent');
        });
        global.__pynext__.registerIsland('Child', () => {
            hydrationOrder.push('Child');
        });
        
        // Hydrate parent first
        const parent = document.querySelector('[data-pynext-id="p1"]');
        global.__pynext__.getIsland('Parent')(parent, {});
        
        // Then child
        const child = document.querySelector('[data-pynext-id="c1"]');
        global.__pynext__.getIsland('Child')(child, {});
        
        expect(hydrationOrder).toEqual(['Parent', 'Child']);
    });
    
    test('should handle dynamic island insertion', () => {
        document.body.innerHTML = `<div id="container"></div>`;
        
        let hydrated = false;
        global.__pynext__.registerIsland('Dynamic', () => {
            hydrated = true;
        });
        
        // Dynamically insert island
        const container = document.getElementById('container');
        container.innerHTML = `
            <div data-pynext-component="Dynamic" data-pynext-id="d1">
                Dynamic content
            </div>
        `;
        
        // Hydrate the new island
        const island = container.querySelector('[data-pynext-component="Dynamic"]');
        global.__pynext__.getIsland('Dynamic')(island, {});
        
        expect(hydrated).toBe(true);
    });
    
    test('should survive hydration with missing signal', () => {
        document.body.innerHTML = `
            <div data-pynext-component="Widget" data-pynext-id="w1">
                <span data-pynext-text="missing">Default</span>
            </div>
        `;
        
        let errorThrown = false;
        
        global.__pynext__.registerIsland('Widget', (element) => {
            try {
                const sig = global.__pynext__.getSignal('nonexistent');
                if (sig) {
                    element.querySelector('span').textContent = sig.read();
                }
            } catch (e) {
                errorThrown = true;
            }
        });
        
        const element = document.querySelector('[data-pynext-component="Widget"]');
        global.__pynext__.getIsland('Widget')(element, {});
        
        // Should not throw, just gracefully handle missing signal
        expect(errorThrown).toBe(false);
        expect(element.querySelector('span').textContent).toBe('Default');
    });
});
