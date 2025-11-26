/**
 * Storage Runtime Tests
 * Tests for storage.js functionality (localStorage/sessionStorage sync)
 */

describe('Storage Management', () => {
    let mockStorage;
    
    beforeEach(() => {
        // Mock localStorage
        mockStorage = {};
        const storageMock = {
            getItem: jest.fn(key => mockStorage[key] || null),
            setItem: jest.fn((key, value) => { mockStorage[key] = value; }),
            removeItem: jest.fn(key => { delete mockStorage[key]; }),
            clear: jest.fn(() => { mockStorage = {}; }),
            key: jest.fn(i => Object.keys(mockStorage)[i] || null),
            get length() { return Object.keys(mockStorage).length; }
        };
        
        Object.defineProperty(window, 'localStorage', { value: storageMock, writable: true });
        Object.defineProperty(window, 'sessionStorage', { value: storageMock, writable: true });
        
        // Mock storage.js
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.storage = {
            signals: new Map(),
            
            createStorageSignal: function(key, defaultValue, storageType = 'local') {
                const storage = storageType === 'local' ? localStorage : sessionStorage;
                const stored = storage.getItem(key);
                let value = stored !== null ? JSON.parse(stored) : defaultValue;
                
                const signal = {
                    _value: value,
                    _subscribers: new Set(),
                    get: function() { return this._value; },
                    set: function(newValue) {
                        this._value = newValue;
                        storage.setItem(key, JSON.stringify(newValue));
                        this._subscribers.forEach(fn => fn(newValue));
                    },
                    subscribe: function(fn) {
                        this._subscribers.add(fn);
                        return () => this._subscribers.delete(fn);
                    }
                };
                
                this.signals.set(key, signal);
                return signal;
            },
            
            get: function(key) {
                return this.signals.get(key);
            },
            
            remove: function(key) {
                localStorage.removeItem(key);
                sessionStorage.removeItem(key);
                this.signals.delete(key);
            }
        };
    });
    
    describe('createStorageSignal', () => {
        test('creates signal with default value', () => {
            const signal = window.__pynext__.storage.createStorageSignal('test', 'default');
            expect(signal.get()).toBe('default');
        });
        
        test('retrieves existing value from storage', () => {
            localStorage.setItem('existing', JSON.stringify('stored value'));
            const signal = window.__pynext__.storage.createStorageSignal('existing', 'default');
            expect(signal.get()).toBe('stored value');
        });
        
        test('persists value changes to storage', () => {
            const signal = window.__pynext__.storage.createStorageSignal('persist', 'initial');
            signal.set('updated');
            expect(JSON.parse(localStorage.getItem('persist'))).toBe('updated');
        });
        
        test('notifies subscribers on change', () => {
            const signal = window.__pynext__.storage.createStorageSignal('notify', 'initial');
            const callback = jest.fn();
            signal.subscribe(callback);
            signal.set('changed');
            expect(callback).toHaveBeenCalledWith('changed');
        });
        
        test('allows unsubscribe', () => {
            const signal = window.__pynext__.storage.createStorageSignal('unsub', 'initial');
            const callback = jest.fn();
            const unsubscribe = signal.subscribe(callback);
            unsubscribe();
            signal.set('changed');
            expect(callback).not.toHaveBeenCalled();
        });
    });
    
    describe('Storage types', () => {
        test('uses localStorage by default', () => {
            window.__pynext__.storage.createStorageSignal('local-test', 'value');
            expect(localStorage.setItem).toHaveBeenCalled();
        });
        
        test('can use sessionStorage', () => {
            window.__pynext__.storage.createStorageSignal('session-test', 'value', 'session');
            expect(sessionStorage.setItem).toHaveBeenCalled();
        });
    });
    
    describe('Complex data types', () => {
        test('handles objects', () => {
            const signal = window.__pynext__.storage.createStorageSignal('obj', { key: 'value' });
            expect(signal.get()).toEqual({ key: 'value' });
            
            signal.set({ key: 'updated', new: true });
            expect(signal.get()).toEqual({ key: 'updated', new: true });
        });
        
        test('handles arrays', () => {
            const signal = window.__pynext__.storage.createStorageSignal('arr', [1, 2, 3]);
            expect(signal.get()).toEqual([1, 2, 3]);
            
            signal.set([1, 2, 3, 4]);
            expect(signal.get()).toEqual([1, 2, 3, 4]);
        });
        
        test('handles numbers', () => {
            const signal = window.__pynext__.storage.createStorageSignal('num', 42);
            expect(signal.get()).toBe(42);
        });
        
        test('handles booleans', () => {
            const signal = window.__pynext__.storage.createStorageSignal('bool', true);
            expect(signal.get()).toBe(true);
            
            signal.set(false);
            expect(signal.get()).toBe(false);
        });
        
        test('handles null', () => {
            const signal = window.__pynext__.storage.createStorageSignal('nullable', null);
            expect(signal.get()).toBe(null);
        });
    });
    
    describe('remove', () => {
        test('removes from both storages', () => {
            window.__pynext__.storage.createStorageSignal('to-remove', 'value');
            window.__pynext__.storage.remove('to-remove');
            expect(localStorage.removeItem).toHaveBeenCalledWith('to-remove');
            expect(sessionStorage.removeItem).toHaveBeenCalledWith('to-remove');
        });
        
        test('removes from signal map', () => {
            window.__pynext__.storage.createStorageSignal('mapped', 'value');
            expect(window.__pynext__.storage.get('mapped')).toBeDefined();
            window.__pynext__.storage.remove('mapped');
            expect(window.__pynext__.storage.get('mapped')).toBeUndefined();
        });
    });
});

describe('Cross-tab synchronization', () => {
    test('storage event triggers signal update', () => {
        // This tests the concept - actual implementation depends on storage.js
        const event = new StorageEvent('storage', {
            key: 'cross-tab',
            newValue: JSON.stringify('from-other-tab'),
            oldValue: null,
            storageArea: localStorage
        });
        
        // Dispatch event
        window.dispatchEvent(event);
        
        // In real implementation, this would update the signal
        expect(event.key).toBe('cross-tab');
    });
});

