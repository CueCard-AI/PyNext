/**
 * Tests for __py.iter() - Python iteration
 * 
 * Python: for k in dict iterates over keys
 * JavaScript: for-of on object throws (not iterable)
 * 
 * This runtime function enables Python-style iteration.
 */

const __py = require('./setup');

describe('__py.iter() - Python Iteration', () => {
    
    // =========================================================================
    // ARRAY ITERATION
    // =========================================================================
    
    describe('Array iteration', () => {
        test('iter([1,2,3]) returns [1,2,3]', () => {
            expect([...__py.iter([1, 2, 3])]).toEqual([1, 2, 3]);
        });
        
        test('iter empty array returns empty', () => {
            expect([...__py.iter([])]).toEqual([]);
        });
        
        test('iter with nested arrays', () => {
            expect([...__py.iter([[1, 2], [3, 4]])]).toEqual([[1, 2], [3, 4]]);
        });
        
        test('iter with mixed types', () => {
            expect([...__py.iter([1, "a", null, true])]).toEqual([1, "a", null, true]);
        });
    });
    
    // =========================================================================
    // STRING ITERATION
    // =========================================================================
    
    describe('String iteration', () => {
        test('iter("abc") returns ["a","b","c"]', () => {
            expect([...__py.iter("abc")]).toEqual(["a", "b", "c"]);
        });
        
        test('iter empty string returns empty', () => {
            expect([...__py.iter("")]).toEqual([]);
        });
        
        test('iter single char string', () => {
            expect([...__py.iter("x")]).toEqual(["x"]);
        });
        
        test('iter with unicode', () => {
            expect([...__py.iter("你好")]).toEqual(["你", "好"]);
        });
    });
    
    // =========================================================================
    // DICT ITERATION (iterate keys!)
    // =========================================================================
    
    describe('Dict iteration (iterate keys!)', () => {
        test('iter({a:1,b:2}) returns ["a","b"]', () => {
            const result = [...__py.iter({a: 1, b: 2})];
            expect(result).toContain("a");
            expect(result).toContain("b");
            expect(result.length).toBe(2);
        });
        
        test('iter empty dict returns empty', () => {
            expect([...__py.iter({})]).toEqual([]);
        });
        
        test('iter dict returns only keys, not values', () => {
            const result = [...__py.iter({a: 1, b: 2})];
            expect(result).not.toContain(1);
            expect(result).not.toContain(2);
        });
        
        test('iter with numeric keys', () => {
            const result = [...__py.iter({1: "a", 2: "b"})];
            expect(result).toContain("1");  // Keys are strings in JS
            expect(result).toContain("2");
        });
    });
    
    // =========================================================================
    // NULL/UNDEFINED
    // =========================================================================
    
    describe('Null/Undefined handling', () => {
        test('iter(null) returns empty', () => {
            expect([...__py.iter(null)]).toEqual([]);
        });
        
        test('iter(undefined) returns empty', () => {
            expect([...__py.iter(undefined)]).toEqual([]);
        });
    });
    
    // =========================================================================
    // SET ITERATION
    // =========================================================================
    
    describe('Set iteration', () => {
        test('iter(new Set([1,2,3])) returns [1,2,3]', () => {
            const result = [...__py.iter(new Set([1, 2, 3]))];
            expect(result).toContain(1);
            expect(result).toContain(2);
            expect(result).toContain(3);
            expect(result.length).toBe(3);
        });
        
        test('iter empty set returns empty', () => {
            expect([...__py.iter(new Set())]).toEqual([]);
        });
    });
    
    // =========================================================================
    // MAP ITERATION
    // =========================================================================
    
    describe('Map iteration', () => {
        test('iter(new Map()) iterates entries', () => {
            const m = new Map([["a", 1], ["b", 2]]);
            const result = [...__py.iter(m)];
            expect(result.length).toBe(2);
        });
    });
    
    // =========================================================================
    // FOR LOOP PATTERNS
    // =========================================================================
    
    describe('For loop patterns', () => {
        test('for x in list pattern', () => {
            const items = [1, 2, 3];
            const result = [];
            for (const x of __py.iter(items)) {
                result.push(x * 2);
            }
            expect(result).toEqual([2, 4, 6]);
        });
        
        test('for k in dict pattern', () => {
            const d = {a: 1, b: 2, c: 3};
            const keys = [];
            for (const k of __py.iter(d)) {
                keys.push(k);
            }
            expect(keys.sort()).toEqual(["a", "b", "c"]);
        });
        
        test('for char in string pattern', () => {
            const s = "hello";
            const chars = [];
            for (const c of __py.iter(s)) {
                chars.push(c);
            }
            expect(chars).toEqual(["h", "e", "l", "l", "o"]);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: for x in [1,2,3]', () => {
            expect([...__py.iter([1, 2, 3])]).toEqual([1, 2, 3]);
        });
        
        test('Python: for k in {"a":1,"b":2}', () => {
            const result = [...__py.iter({a: 1, b: 2})];
            expect(result.sort()).toEqual(["a", "b"]);
        });
        
        test('Python: for c in "abc"', () => {
            expect([...__py.iter("abc")]).toEqual(["a", "b", "c"]);
        });
        
        test('Python: list(iter(x)) for various types', () => {
            expect([...__py.iter([])]).toEqual([]);
            expect([...__py.iter({})]).toEqual([]);
            expect([...__py.iter("")]).toEqual([]);
        });
    });
    
    // =========================================================================
    // INTEGRATION WITH OTHER __py FUNCTIONS
    // =========================================================================
    
    describe('Integration with other __py functions', () => {
        test('iter + enumerate pattern', () => {
            const items = ["a", "b", "c"];
            const result = __py.enumerate([...__py.iter(items)]);
            expect(result).toEqual([[0, "a"], [1, "b"], [2, "c"]]);
        });
        
        test('iter + contains pattern', () => {
            const d = {a: 1, b: 2};
            const keys = [...__py.iter(d)];
            expect(__py.contains("a", keys)).toBe(true);
            expect(__py.contains("c", keys)).toBe(false);
        });
    });
});
