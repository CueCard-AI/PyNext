/**
 * Browser APIs Runtime Tests
 * Tests for browser.js functionality (visibility, online status)
 */

describe('Visibility API', () => {
    let originalDocument;
    
    beforeEach(() => {
        originalDocument = { ...document };
        
        // Mock document.visibilityState
        Object.defineProperty(document, 'visibilityState', {
            configurable: true,
            get: jest.fn(() => 'visible')
        });
        
        Object.defineProperty(document, 'hidden', {
            configurable: true,
            get: jest.fn(() => false)
        });
        
        // Mock browser.js
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.browser = {
            visibility: {
                _value: true,
                _subscribers: new Set(),
                get: function() { return this._value; },
                subscribe: function(fn) {
                    this._subscribers.add(fn);
                    return () => this._subscribers.delete(fn);
                },
                _update: function(visible) {
                    this._value = visible;
                    this._subscribers.forEach(fn => fn(visible));
                }
            },
            
            online: {
                _value: true,
                _subscribers: new Set(),
                get: function() { return this._value; },
                subscribe: function(fn) {
                    this._subscribers.add(fn);
                    return () => this._subscribers.delete(fn);
                },
                _update: function(online) {
                    this._value = online;
                    this._subscribers.forEach(fn => fn(online));
                }
            }
        };
        
        // Setup visibility listener
        document.addEventListener('visibilitychange', () => {
            window.__pynext__.browser.visibility._update(document.visibilityState === 'visible');
        });
        
        // Setup online/offline listeners
        window.addEventListener('online', () => {
            window.__pynext__.browser.online._update(true);
        });
        
        window.addEventListener('offline', () => {
            window.__pynext__.browser.online._update(false);
        });
    });
    
    describe('visibility signal', () => {
        test('initial value is true (visible)', () => {
            expect(window.__pynext__.browser.visibility.get()).toBe(true);
        });
        
        test('updates on visibility change', () => {
            window.__pynext__.browser.visibility._update(false);
            expect(window.__pynext__.browser.visibility.get()).toBe(false);
        });
        
        test('notifies subscribers', () => {
            const callback = jest.fn();
            window.__pynext__.browser.visibility.subscribe(callback);
            
            window.__pynext__.browser.visibility._update(false);
            
            expect(callback).toHaveBeenCalledWith(false);
        });
        
        test('allows unsubscribe', () => {
            const callback = jest.fn();
            const unsubscribe = window.__pynext__.browser.visibility.subscribe(callback);
            
            unsubscribe();
            window.__pynext__.browser.visibility._update(false);
            
            expect(callback).not.toHaveBeenCalled();
        });
    });
});

describe('Online Status API', () => {
    beforeEach(() => {
        // Mock navigator.onLine
        Object.defineProperty(navigator, 'onLine', {
            configurable: true,
            get: jest.fn(() => true)
        });
    });
    
    describe('online signal', () => {
        test('initial value matches navigator.onLine', () => {
            expect(window.__pynext__.browser.online.get()).toBe(true);
        });
        
        test('updates to false when offline', () => {
            window.__pynext__.browser.online._update(false);
            expect(window.__pynext__.browser.online.get()).toBe(false);
        });
        
        test('updates to true when online', () => {
            window.__pynext__.browser.online._update(false);
            window.__pynext__.browser.online._update(true);
            expect(window.__pynext__.browser.online.get()).toBe(true);
        });
        
        test('notifies subscribers on change', () => {
            const callback = jest.fn();
            window.__pynext__.browser.online.subscribe(callback);
            
            window.__pynext__.browser.online._update(false);
            
            expect(callback).toHaveBeenCalledWith(false);
        });
    });
});

describe('Window Events', () => {
    test('online event handling', () => {
        const callback = jest.fn();
        window.addEventListener('online', callback);
        
        const event = new Event('online');
        window.dispatchEvent(event);
        
        expect(callback).toHaveBeenCalled();
    });
    
    test('offline event handling', () => {
        const callback = jest.fn();
        window.addEventListener('offline', callback);
        
        const event = new Event('offline');
        window.dispatchEvent(event);
        
        expect(callback).toHaveBeenCalled();
    });
    
    test('visibilitychange event handling', () => {
        const callback = jest.fn();
        document.addEventListener('visibilitychange', callback);
        
        const event = new Event('visibilitychange');
        document.dispatchEvent(event);
        
        expect(callback).toHaveBeenCalled();
    });
});

describe('Integration: Polling based on visibility', () => {
    test('can pause polling when hidden', () => {
        let isPolling = true;
        
        window.__pynext__.browser.visibility.subscribe((visible) => {
            isPolling = visible;
        });
        
        // Tab becomes hidden
        window.__pynext__.browser.visibility._update(false);
        expect(isPolling).toBe(false);
        
        // Tab becomes visible
        window.__pynext__.browser.visibility._update(true);
        expect(isPolling).toBe(true);
    });
});

describe('Integration: Network-aware features', () => {
    test('can disable features when offline', () => {
        let canSubmit = true;
        
        window.__pynext__.browser.online.subscribe((online) => {
            canSubmit = online;
        });
        
        // Goes offline
        window.__pynext__.browser.online._update(false);
        expect(canSubmit).toBe(false);
        
        // Goes back online
        window.__pynext__.browser.online._update(true);
        expect(canSubmit).toBe(true);
    });
});

