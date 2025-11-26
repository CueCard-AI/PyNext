/**
 * PyNext JavaScript Test Setup
 * 
 * Uses Jest with jsdom for DOM testing
 */

// Mock browser APIs that jsdom doesn't provide
global.matchMedia = global.matchMedia || function(query) {
    return {
        matches: false,
        media: query,
        onchange: null,
        addListener: function() {},
        removeListener: function() {},
        addEventListener: function() {},
        removeEventListener: function() {},
        dispatchEvent: function() { return true; },
    };
};

// Mock localStorage
const localStorageMock = (function() {
    let store = {};
    return {
        getItem: function(key) {
            return store[key] || null;
        },
        setItem: function(key, value) {
            store[key] = String(value);
        },
        removeItem: function(key) {
            delete store[key];
        },
        clear: function() {
            store = {};
        },
    };
})();
Object.defineProperty(global, 'localStorage', { value: localStorageMock });

// Mock sessionStorage
const sessionStorageMock = (function() {
    let store = {};
    return {
        getItem: function(key) {
            return store[key] || null;
        },
        setItem: function(key, value) {
            store[key] = String(value);
        },
        removeItem: function(key) {
            delete store[key];
        },
        clear: function() {
            store = {};
        },
    };
})();
Object.defineProperty(global, 'sessionStorage', { value: sessionStorageMock });

// Mock navigator
Object.defineProperty(global.navigator, 'platform', {
    value: 'MacIntel',
    writable: true,
});

Object.defineProperty(global.navigator, 'onLine', {
    value: true,
    writable: true,
});

// Mock EventSource
class MockEventSource {
    constructor(url) {
        this.url = url;
        this.readyState = 0;
        this.listeners = {};
        
        setTimeout(() => {
            this.readyState = 1;
            if (this.onopen) this.onopen();
        }, 0);
    }
    
    addEventListener(event, handler) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(handler);
    }
    
    removeEventListener(event, handler) {
        if (!this.listeners[event]) return;
        this.listeners[event] = this.listeners[event].filter(h => h !== handler);
    }
    
    close() {
        this.readyState = 2;
    }
    
    simulateMessage(event, data) {
        const handlers = this.listeners[event] || [];
        handlers.forEach(h => h({ data: JSON.stringify(data) }));
    }
}
global.EventSource = MockEventSource;

// Reset __pynext__ before each test
beforeEach(() => {
    global.__pynext__ = {};
    global.__PYNEXT_DATA__ = null;
    localStorageMock.clear();
    sessionStorageMock.clear();
    document.body.innerHTML = '';
});

// Helper to dispatch keyboard events
global.pressKey = function(key, options = {}) {
    const event = new KeyboardEvent('keydown', {
        key: key,
        metaKey: options.meta || false,
        ctrlKey: options.ctrl || false,
        altKey: options.alt || false,
        shiftKey: options.shift || false,
        bubbles: true,
    });
    (options.target || document).dispatchEvent(event);
    return event;
};

// Helper to wait for async operations
global.tick = function(ms = 0) {
    return new Promise(resolve => setTimeout(resolve, ms));
};

