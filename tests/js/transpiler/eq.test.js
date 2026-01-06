/**
 * Tests for __py.eq() - Python deep equality
 * 
 * CRITICAL DIFFERENCE:
 * Python: [1, 2] == [1, 2] is True (value equality)
 * JavaScript: [1, 2] === [1, 2] is false (reference equality)
 * 
 * This runtime function implements Python value equality.
 */

const __py = require('./setup');

describe('__py.eq() - Python Deep Equality', () => {
    
    // =========================================================================
    // PRIMITIVES
    // =========================================================================
    
    describe('Primitives', () => {
        test('eq(1, 1) returns true', () => {
            expect(__py.eq(1, 1)).toBe(true);
        });
        
        test('eq(1, 2) returns false', () => {
            expect(__py.eq(1, 2)).toBe(false);
        });
        
        test('eq("a", "a") returns true', () => {
            expect(__py.eq("a", "a")).toBe(true);
        });
        
        test('eq("a", "b") returns false', () => {
            expect(__py.eq("a", "b")).toBe(false);
        });
        
        test('eq(true, true) returns true', () => {
            expect(__py.eq(true, true)).toBe(true);
        });
        
        test('eq(true, false) returns false', () => {
            expect(__py.eq(true, false)).toBe(false);
        });
        
        test('eq(null, null) returns true', () => {
            expect(__py.eq(null, null)).toBe(true);
        });
        
        test('eq(undefined, undefined) returns true', () => {
            expect(__py.eq(undefined, undefined)).toBe(true);
        });
        
        test('eq(null, undefined) returns false', () => {
            expect(__py.eq(null, undefined)).toBe(false);
        });
        
        test('eq(0, 0.0) returns true', () => {
            expect(__py.eq(0, 0.0)).toBe(true);
        });
        
        test('eq(0, -0) returns true', () => {
            expect(__py.eq(0, -0)).toBe(true);
        });
    });
    
    // =========================================================================
    // LISTS (CRITICAL DIFFERENCE!)
    // =========================================================================
    
    describe('Lists (critical difference!)', () => {
        test('eq([1,2,3], [1,2,3]) returns true (JS: false!)', () => {
            const a = [1, 2, 3];
            const b = [1, 2, 3];
            expect(__py.eq(a, b)).toBe(true);
            expect(a === b).toBe(false);  // Verify JS difference
        });
        
        test('eq([1,2], [1,2,3]) returns false', () => {
            expect(__py.eq([1, 2], [1, 2, 3])).toBe(false);
        });
        
        test('eq([1,2,3], [1,2]) returns false', () => {
            expect(__py.eq([1, 2, 3], [1, 2])).toBe(false);
        });
        
        test('eq([], []) returns true', () => {
            expect(__py.eq([], [])).toBe(true);
        });
        
        test('eq([1], [2]) returns false', () => {
            expect(__py.eq([1], [2])).toBe(false);
        });
        
        test('eq with same reference returns true', () => {
            const arr = [1, 2, 3];
            expect(__py.eq(arr, arr)).toBe(true);
        });
    });
    
    // =========================================================================
    // NESTED LISTS
    // =========================================================================
    
    describe('Nested lists (deep comparison)', () => {
        test('eq([[1,2],[3,4]], [[1,2],[3,4]]) returns true', () => {
            expect(__py.eq([[1, 2], [3, 4]], [[1, 2], [3, 4]])).toBe(true);
        });
        
        test('eq([[1,2],[3,4]], [[1,2],[3,5]]) returns false', () => {
            expect(__py.eq([[1, 2], [3, 4]], [[1, 2], [3, 5]])).toBe(false);
        });
        
        test('eq([1,[2,3]], [1,[2,3]]) returns true', () => {
            expect(__py.eq([1, [2, 3]], [1, [2, 3]])).toBe(true);
        });
        
        test('eq deeply nested arrays', () => {
            const a = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]];
            const b = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]];
            expect(__py.eq(a, b)).toBe(true);
        });
        
        test('eq with nested empty arrays', () => {
            expect(__py.eq([[], []], [[], []])).toBe(true);
        });
    });
    
    // =========================================================================
    // DICTS (CRITICAL DIFFERENCE!)
    // =========================================================================
    
    describe('Dicts (critical difference!)', () => {
        test('eq({a:1}, {a:1}) returns true (JS: false!)', () => {
            const a = {a: 1};
            const b = {a: 1};
            expect(__py.eq(a, b)).toBe(true);
            expect(a === b).toBe(false);  // Verify JS difference
        });
        
        test('eq({a:1,b:2}, {b:2,a:1}) returns true (order independent)', () => {
            expect(__py.eq({a: 1, b: 2}, {b: 2, a: 1})).toBe(true);
        });
        
        test('eq({a:1}, {a:2}) returns false', () => {
            expect(__py.eq({a: 1}, {a: 2})).toBe(false);
        });
        
        test('eq({a:1}, {b:1}) returns false', () => {
            expect(__py.eq({a: 1}, {b: 1})).toBe(false);
        });
        
        test('eq({}, {}) returns true', () => {
            expect(__py.eq({}, {})).toBe(true);
        });
        
        test('eq({a:1}, {a:1, b:2}) returns false', () => {
            expect(__py.eq({a: 1}, {a: 1, b: 2})).toBe(false);
        });
    });
    
    // =========================================================================
    // NESTED DICTS
    // =========================================================================
    
    describe('Nested dicts (deep comparison)', () => {
        test('eq({a:{b:1}}, {a:{b:1}}) returns true', () => {
            expect(__py.eq({a: {b: 1}}, {a: {b: 1}})).toBe(true);
        });
        
        test('eq({a:{b:1}}, {a:{b:2}}) returns false', () => {
            expect(__py.eq({a: {b: 1}}, {a: {b: 2}})).toBe(false);
        });
        
        test('eq with deeply nested dicts', () => {
            const a = {x: {y: {z: 1}}};
            const b = {x: {y: {z: 1}}};
            expect(__py.eq(a, b)).toBe(true);
        });
    });
    
    // =========================================================================
    // MIXED LISTS AND DICTS
    // =========================================================================
    
    describe('Mixed lists and dicts', () => {
        test('eq([{a:1}], [{a:1}]) returns true', () => {
            expect(__py.eq([{a: 1}], [{a: 1}])).toBe(true);
        });
        
        test('eq({a:[1,2]}, {a:[1,2]}) returns true', () => {
            expect(__py.eq({a: [1, 2]}, {a: [1, 2]})).toBe(true);
        });
        
        test('eq([{a:[1,2]},{b:3}], [{a:[1,2]},{b:3}]) returns true', () => {
            expect(__py.eq([{a: [1, 2]}, {b: 3}], [{a: [1, 2]}, {b: 3}])).toBe(true);
        });
        
        test('eq complex nested structure', () => {
            const a = {users: [{name: "Alice", scores: [1, 2, 3]}, {name: "Bob", scores: [4, 5]}]};
            const b = {users: [{name: "Alice", scores: [1, 2, 3]}, {name: "Bob", scores: [4, 5]}]};
            expect(__py.eq(a, b)).toBe(true);
        });
    });
    
    // =========================================================================
    // TYPE COERCION (Python is strict)
    // =========================================================================
    
    describe('Type coercion (Python is strict)', () => {
        test('eq(1, "1") returns false (different types)', () => {
            expect(__py.eq(1, "1")).toBe(false);
        });
        
        test('eq(1, true) returns false (different types)', () => {
            expect(__py.eq(1, true)).toBe(false);
        });
        
        test('eq(0, false) returns false (different types)', () => {
            expect(__py.eq(0, false)).toBe(false);
        });
        
        test('eq(0, null) returns false (different types)', () => {
            expect(__py.eq(0, null)).toBe(false);
        });
        
        test('eq([], "") returns false (different types)', () => {
            expect(__py.eq([], "")).toBe(false);
        });
        
        test('eq({}, []) returns false (different types)', () => {
            expect(__py.eq({}, [])).toBe(false);
        });
        
        test('eq("0", 0) returns false (different types)', () => {
            expect(__py.eq("0", 0)).toBe(false);
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('eq with NaN values', () => {
            // In Python, float('nan') != float('nan')
            // This is consistent with IEEE 754
            expect(__py.eq(NaN, NaN)).toBe(false);
        });
        
        test('eq with Infinity', () => {
            expect(__py.eq(Infinity, Infinity)).toBe(true);
            expect(__py.eq(-Infinity, -Infinity)).toBe(true);
            expect(__py.eq(Infinity, -Infinity)).toBe(false);
        });
        
        test('eq with arrays containing null', () => {
            expect(__py.eq([null, null], [null, null])).toBe(true);
        });
        
        test('eq with arrays containing undefined', () => {
            expect(__py.eq([undefined], [undefined])).toBe(true);
        });
        
        test('eq with very long arrays', () => {
            const a = Array.from({length: 1000}, (_, i) => i);
            const b = Array.from({length: 1000}, (_, i) => i);
            expect(__py.eq(a, b)).toBe(true);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: [1,2,3] == [1,2,3]', () => {
            expect(__py.eq([1, 2, 3], [1, 2, 3])).toBe(true);
        });
        
        test('Python: {"a": 1} == {"a": 1}', () => {
            expect(__py.eq({a: 1}, {a: 1})).toBe(true);
        });
        
        test('Python: [] == []', () => {
            expect(__py.eq([], [])).toBe(true);
        });
        
        test('Python: {} == {}', () => {
            expect(__py.eq({}, {})).toBe(true);
        });
        
        test('Python: 1 == 1.0', () => {
            expect(__py.eq(1, 1.0)).toBe(true);
        });
        
        test('Python: [1] != 1', () => {
            expect(__py.eq([1], 1)).toBe(false);
        });
    });
});
