/**
 * Intensive Tests for Store Proxy Mutation Methods
 * 
 * Tests edge cases in the createStore Proxy implementation.
 * 
 * Critical Risk: Array mutation methods must trigger reactivity.
 * Missing methods can cause UI to not update when store data changes.
 * 
 * Coverage:
 * 1. All array mutation methods (push, pop, shift, unshift, splice, sort, reverse, fill, copyWithin)
 * 2. Object.assign with store data
 * 3. Nested mutations
 * 4. Array of objects mutations
 * 5. Deletions
 */

// Mock implementation of createStore with all required features
function createStore(initial) {
    const subscribers = new Set();
    let currentObserver = null;
    
    function notify() {
        for (const sub of subscribers) {
            if (typeof sub.execute === 'function') {
                sub.execute();
            } else {
                sub();
            }
        }
    }
    
    function makeProxy(obj, path = []) {
        if (obj === null || typeof obj !== 'object') {
            return obj;
        }
        
        return new Proxy(obj, {
            get(target, prop) {
                if (prop === '__isProxy') return true;
                if (prop === '__target') return target;
                if (prop === '__path') return path;
                
                // Track dependency
                if (currentObserver && typeof prop !== 'symbol') {
                    subscribers.add(currentObserver);
                }
                
                const value = target[prop];
                
                // Wrap array mutation methods
                if (Array.isArray(target) && typeof value === 'function') {
                    const mutatingMethods = [
                        'push', 'pop', 'shift', 'unshift', 
                        'splice', 'sort', 'reverse', 'fill', 'copyWithin'
                    ];
                    if (mutatingMethods.includes(prop)) {
                        return function(...args) {
                            const result = Array.prototype[prop].apply(target, args);
                            notify();
                            return result;
                        };
                    }
                }
                
                // Recursively wrap nested objects
                if (value !== null && typeof value === 'object' && !value.__isProxy) {
                    return makeProxy(value, [...path, prop]);
                }
                
                return value;
            },
            
            set(target, prop, value) {
                if (target[prop] !== value) {
                    target[prop] = value;
                    notify();
                }
                return true;
            },
            
            deleteProperty(target, prop) {
                if (prop in target) {
                    delete target[prop];
                    notify();
                }
                return true;
            },
        });
    }
    
    const proxy = makeProxy(initial);
    
    // For testing: expose subscribe method
    proxy.__subscribe = (fn) => {
        subscribers.add(fn);
        return () => subscribers.delete(fn);
    };
    
    proxy.__setObserver = (obs) => {
        currentObserver = obs;
    };
    
    proxy.__clearObserver = () => {
        currentObserver = null;
    };
    
    return proxy;
}


// =============================================================================
// TESTS: Array Mutation Methods
// =============================================================================

describe('Store Array Mutation Methods', () => {
    describe('push()', () => {
        test('triggers reactivity on push', () => {
            const store = createStore({ items: [1, 2, 3] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            store.items.push(4);
            
            expect(store.items).toEqual([1, 2, 3, 4]);
            expect(updateCount).toBe(1);
        });
        
        test('push multiple items', () => {
            const store = createStore({ items: [] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            store.items.push(1, 2, 3);
            
            expect(store.items).toEqual([1, 2, 3]);
            expect(updateCount).toBe(1);
        });
        
        test('push returns new length', () => {
            const store = createStore({ items: [1, 2] });
            const length = store.items.push(3);
            
            expect(length).toBe(3);
        });
    });
    
    describe('pop()', () => {
        test('triggers reactivity on pop', () => {
            const store = createStore({ items: [1, 2, 3] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            const popped = store.items.pop();
            
            expect(popped).toBe(3);
            expect(store.items).toEqual([1, 2]);
            expect(updateCount).toBe(1);
        });
        
        test('pop on empty array', () => {
            const store = createStore({ items: [] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            const popped = store.items.pop();
            
            expect(popped).toBeUndefined();
            expect(updateCount).toBe(1); // Still notifies even on empty
        });
    });
    
    describe('shift()', () => {
        test('triggers reactivity on shift', () => {
            const store = createStore({ items: [1, 2, 3] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            const shifted = store.items.shift();
            
            expect(shifted).toBe(1);
            expect(store.items).toEqual([2, 3]);
            expect(updateCount).toBe(1);
        });
    });
    
    describe('unshift()', () => {
        test('triggers reactivity on unshift', () => {
            const store = createStore({ items: [2, 3] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            const length = store.items.unshift(1);
            
            expect(length).toBe(3);
            expect(store.items).toEqual([1, 2, 3]);
            expect(updateCount).toBe(1);
        });
        
        test('unshift multiple items', () => {
            const store = createStore({ items: [3] });
            
            store.items.unshift(1, 2);
            
            expect(store.items).toEqual([1, 2, 3]);
        });
    });
    
    describe('splice()', () => {
        test('splice remove items triggers reactivity', () => {
            const store = createStore({ items: [1, 2, 3, 4, 5] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            const removed = store.items.splice(1, 2);
            
            expect(removed).toEqual([2, 3]);
            expect(store.items).toEqual([1, 4, 5]);
            expect(updateCount).toBe(1);
        });
        
        test('splice insert items triggers reactivity', () => {
            const store = createStore({ items: [1, 4, 5] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            store.items.splice(1, 0, 2, 3);
            
            expect(store.items).toEqual([1, 2, 3, 4, 5]);
            expect(updateCount).toBe(1);
        });
        
        test('splice replace items', () => {
            const store = createStore({ items: [1, 2, 3] });
            
            store.items.splice(1, 1, 'a', 'b');
            
            expect(store.items).toEqual([1, 'a', 'b', 3]);
        });
    });
    
    describe('sort()', () => {
        test('sort triggers reactivity', () => {
            const store = createStore({ items: [3, 1, 2] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            store.items.sort();
            
            expect(store.items).toEqual([1, 2, 3]);
            expect(updateCount).toBe(1);
        });
        
        test('sort with comparator', () => {
            const store = createStore({ items: [1, 2, 3] });
            
            store.items.sort((a, b) => b - a);
            
            expect(store.items).toEqual([3, 2, 1]);
        });
    });
    
    describe('reverse()', () => {
        test('reverse triggers reactivity', () => {
            const store = createStore({ items: [1, 2, 3] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            store.items.reverse();
            
            expect(store.items).toEqual([3, 2, 1]);
            expect(updateCount).toBe(1);
        });
    });
    
    describe('fill()', () => {
        test('fill triggers reactivity', () => {
            const store = createStore({ items: [1, 2, 3] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            store.items.fill(0);
            
            expect(store.items).toEqual([0, 0, 0]);
            expect(updateCount).toBe(1);
        });
        
        test('fill with start and end', () => {
            const store = createStore({ items: [1, 2, 3, 4, 5] });
            
            store.items.fill(0, 1, 4);
            
            expect(store.items).toEqual([1, 0, 0, 0, 5]);
        });
    });
    
    describe('copyWithin()', () => {
        test('copyWithin triggers reactivity', () => {
            const store = createStore({ items: [1, 2, 3, 4, 5] });
            let updateCount = 0;
            store.__subscribe(() => updateCount++);
            
            store.items.copyWithin(0, 3);
            
            expect(store.items).toEqual([4, 5, 3, 4, 5]);
            expect(updateCount).toBe(1);
        });
    });
});


// =============================================================================
// TESTS: Direct Assignment
// =============================================================================

describe('Store Direct Assignment', () => {
    test('assigning to property triggers reactivity', () => {
        const store = createStore({ count: 0 });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.count = 1;
        
        expect(store.count).toBe(1);
        expect(updateCount).toBe(1);
    });
    
    test('assigning same value does NOT trigger', () => {
        const store = createStore({ count: 0 });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.count = 0;  // Same value
        
        expect(updateCount).toBe(0);
    });
    
    test('assigning array element triggers reactivity', () => {
        const store = createStore({ items: [1, 2, 3] });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.items[1] = 'changed';
        
        expect(store.items).toEqual([1, 'changed', 3]);
        expect(updateCount).toBe(1);
    });
    
    test('assigning new property triggers reactivity', () => {
        const store = createStore({ existing: 1 });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.newProp = 2;
        
        expect(store.newProp).toBe(2);
        expect(updateCount).toBe(1);
    });
});


// =============================================================================
// TESTS: Nested Mutations
// =============================================================================

describe('Store Nested Mutations', () => {
    test('deeply nested assignment triggers reactivity', () => {
        const store = createStore({ 
            user: { 
                profile: { 
                    name: 'Alice' 
                } 
            } 
        });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.user.profile.name = 'Bob';
        
        expect(store.user.profile.name).toBe('Bob');
        expect(updateCount).toBe(1);
    });
    
    test('nested array mutation triggers reactivity', () => {
        const store = createStore({ 
            users: [
                { name: 'Alice' },
                { name: 'Bob' }
            ]
        });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.users[0].name = 'Charlie';
        
        expect(store.users[0].name).toBe('Charlie');
        expect(updateCount).toBe(1);
    });
    
    test('push to nested array triggers reactivity', () => {
        const store = createStore({ 
            categories: [
                { name: 'A', items: [1, 2] }
            ]
        });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.categories[0].items.push(3);
        
        expect(store.categories[0].items).toEqual([1, 2, 3]);
        expect(updateCount).toBe(1);
    });
});


// =============================================================================
// TESTS: Deletion
// =============================================================================

describe('Store Deletion', () => {
    test('delete property triggers reactivity', () => {
        const store = createStore({ a: 1, b: 2 });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        delete store.a;
        
        expect(store.a).toBeUndefined();
        // Check that 'a' is no longer in the target, 'b' remains
        expect('a' in store.__target).toBe(false);
        expect('b' in store.__target).toBe(true);
        expect(updateCount).toBe(1);
    });
    
    test('delete non-existent property does NOT trigger', () => {
        const store = createStore({ a: 1 });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        delete store.nonexistent;
        
        expect(updateCount).toBe(0);
    });
    
    test('delete array element triggers reactivity', () => {
        const store = createStore({ items: [1, 2, 3] });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        delete store.items[1];
        
        // Note: delete on array creates a "hole"
        expect(store.items.length).toBe(3);
        expect(1 in store.items).toBe(false);
        expect(updateCount).toBe(1);
    });
});


// =============================================================================
// TESTS: Object.assign (Critical Risk!)
// =============================================================================

describe('Store Object.assign Behavior', () => {
    test('Object.assign to store property triggers reactivity', () => {
        const store = createStore({ data: { a: 1 } });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        // This should trigger because it sets individual properties
        Object.assign(store.data, { b: 2 });
        
        expect(store.data.b).toBe(2);
        // Note: Object.assign sets properties one by one through proxy
        expect(updateCount).toBeGreaterThanOrEqual(1);
    });
    
    test('Object.assign with multiple sources', () => {
        const store = createStore({ config: {} });
        
        Object.assign(store.config, { a: 1 }, { b: 2 }, { c: 3 });
        
        expect(store.config).toEqual({ a: 1, b: 2, c: 3 });
    });
    
    test('replacing entire object triggers reactivity', () => {
        const store = createStore({ data: { old: 'value' } });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.data = { new: 'value' };
        
        expect(store.data.new).toBe('value');
        expect(store.data.old).toBeUndefined();
        expect(updateCount).toBe(1);
    });
});


// =============================================================================
// TESTS: Array of Objects
// =============================================================================

describe('Store Array of Objects', () => {
    test('modify object in array triggers reactivity', () => {
        const store = createStore({
            todos: [
                { id: 1, text: 'Task 1', done: false },
                { id: 2, text: 'Task 2', done: false },
            ]
        });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.todos[0].done = true;
        
        expect(store.todos[0].done).toBe(true);
        expect(updateCount).toBe(1);
    });
    
    test('push new object to array', () => {
        const store = createStore({ todos: [] });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.todos.push({ id: 1, text: 'New Task', done: false });
        
        expect(store.todos.length).toBe(1);
        expect(store.todos[0].text).toBe('New Task');
        expect(updateCount).toBe(1);
    });
    
    test('modify newly pushed object triggers reactivity', () => {
        const store = createStore({ todos: [] });
        
        store.todos.push({ id: 1, text: 'Task', done: false });
        
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.todos[0].text = 'Modified';
        
        expect(store.todos[0].text).toBe('Modified');
        expect(updateCount).toBe(1);
    });
    
    test('filter-like replacement', () => {
        const store = createStore({
            items: [1, 2, 3, 4, 5]
        });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        // Replace with filtered version
        const filtered = store.items.filter(x => x % 2 === 0);
        store.items = filtered;
        
        expect(store.items).toEqual([2, 4]);
        expect(updateCount).toBe(1);
    });
    
    test('map-like replacement', () => {
        const store = createStore({
            items: [1, 2, 3]
        });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.items = store.items.map(x => x * 2);
        
        expect(store.items).toEqual([2, 4, 6]);
        expect(updateCount).toBe(1);
    });
});


// =============================================================================
// TESTS: Non-Mutating Methods (Should NOT trigger)
// =============================================================================

describe('Store Non-Mutating Methods', () => {
    test('forEach does NOT trigger reactivity', () => {
        const store = createStore({ items: [1, 2, 3] });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        let sum = 0;
        store.items.forEach(x => sum += x);
        
        expect(sum).toBe(6);
        expect(updateCount).toBe(0);
    });
    
    test('map does NOT trigger reactivity', () => {
        const store = createStore({ items: [1, 2, 3] });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        const doubled = store.items.map(x => x * 2);
        
        expect(doubled).toEqual([2, 4, 6]);
        expect(store.items).toEqual([1, 2, 3]); // Original unchanged
        expect(updateCount).toBe(0);
    });
    
    test('filter does NOT trigger reactivity', () => {
        const store = createStore({ items: [1, 2, 3, 4, 5] });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        const evens = store.items.filter(x => x % 2 === 0);
        
        expect(evens).toEqual([2, 4]);
        expect(store.items).toEqual([1, 2, 3, 4, 5]); // Original unchanged
        expect(updateCount).toBe(0);
    });
    
    test('reduce does NOT trigger reactivity', () => {
        const store = createStore({ items: [1, 2, 3] });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        const sum = store.items.reduce((acc, x) => acc + x, 0);
        
        expect(sum).toBe(6);
        expect(updateCount).toBe(0);
    });
    
    test('slice does NOT trigger reactivity', () => {
        const store = createStore({ items: [1, 2, 3, 4, 5] });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        const sliced = store.items.slice(1, 3);
        
        expect(sliced).toEqual([2, 3]);
        expect(store.items).toEqual([1, 2, 3, 4, 5]);
        expect(updateCount).toBe(0);
    });
    
    test('concat does NOT trigger reactivity', () => {
        const store = createStore({ items: [1, 2] });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        const concatenated = store.items.concat([3, 4]);
        
        expect(concatenated).toEqual([1, 2, 3, 4]);
        expect(store.items).toEqual([1, 2]);
        expect(updateCount).toBe(0);
    });
});


// =============================================================================
// TESTS: Edge Cases
// =============================================================================

describe('Store Edge Cases', () => {
    test('null values in store', () => {
        const store = createStore({ value: null });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.value = { a: 1 };
        
        expect(store.value).toEqual({ a: 1 });
        expect(updateCount).toBe(1);
    });
    
    test('setting to null triggers reactivity', () => {
        const store = createStore({ value: { a: 1 } });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.value = null;
        
        expect(store.value).toBeNull();
        expect(updateCount).toBe(1);
    });
    
    test('undefined values', () => {
        const store = createStore({ value: undefined });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.value = 'defined';
        
        expect(store.value).toBe('defined');
        expect(updateCount).toBe(1);
    });
    
    test('empty array operations', () => {
        const store = createStore({ items: [] });
        let updateCount = 0;
        store.__subscribe(() => updateCount++);
        
        store.items.push(1);
        store.items.pop();
        
        expect(store.items).toEqual([]);
        expect(updateCount).toBe(2);
    });
    
    test('multiple subscribers', () => {
        const store = createStore({ count: 0 });
        let updates1 = 0;
        let updates2 = 0;
        
        store.__subscribe(() => updates1++);
        store.__subscribe(() => updates2++);
        
        store.count = 1;
        
        expect(updates1).toBe(1);
        expect(updates2).toBe(1);
    });
    
    test('unsubscribe stops notifications', () => {
        const store = createStore({ count: 0 });
        let updateCount = 0;
        
        const unsub = store.__subscribe(() => updateCount++);
        
        store.count = 1;
        expect(updateCount).toBe(1);
        
        unsub();
        
        store.count = 2;
        expect(updateCount).toBe(1);  // No more updates
    });
});
