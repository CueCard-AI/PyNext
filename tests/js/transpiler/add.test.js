/**
 * Tests for __py.add() - Python polymorphic addition
 * 
 * CRITICAL DIFFERENCE:
 * Python: [1] + [2] = [1, 2] (list concatenation)
 * JavaScript: [1] + [2] = "1,2" (string coercion!)
 * 
 * This runtime function implements Python addition semantics.
 */

const __py = require('./setup');

describe('__py.add() - Python Polymorphic Addition', () => {
    
    // =========================================================================
    // NUMBER ADDITION
    // =========================================================================
    
    describe('Number addition', () => {
        test('add(1, 2) returns 3', () => {
            expect(__py.add(1, 2)).toBe(3);
        });
        
        test('add(1.5, 2.5) returns 4.0', () => {
            expect(__py.add(1.5, 2.5)).toBe(4.0);
        });
        
        test('add(-1, 1) returns 0', () => {
            expect(__py.add(-1, 1)).toBe(0);
        });
        
        test('add(0, 0) returns 0', () => {
            expect(__py.add(0, 0)).toBe(0);
        });
        
        test('add with negative numbers', () => {
            expect(__py.add(-5, -3)).toBe(-8);
        });
        
        test('add with very large numbers', () => {
            expect(__py.add(1e10, 2e10)).toBe(3e10);
        });
        
        test('add with Infinity', () => {
            expect(__py.add(Infinity, 1)).toBe(Infinity);
            expect(__py.add(-Infinity, -1)).toBe(-Infinity);
        });
    });
    
    // =========================================================================
    // LIST CONCATENATION (CRITICAL DIFFERENCE!)
    // =========================================================================
    
    describe('List concatenation (critical difference!)', () => {
        test('add([1,2], [3,4]) returns [1,2,3,4] (JS: "1,23,4"!)', () => {
            const a = [1, 2];
            const b = [3, 4];
            expect(__py.add(a, b)).toEqual([1, 2, 3, 4]);
            expect(a + b).toBe("1,23,4");  // Verify JS difference!
        });
        
        test('add([1], []) returns [1]', () => {
            expect(__py.add([1], [])).toEqual([1]);
        });
        
        test('add([], [1]) returns [1]', () => {
            expect(__py.add([], [1])).toEqual([1]);
        });
        
        test('add([], []) returns []', () => {
            expect(__py.add([], [])).toEqual([]);
        });
        
        test('add([[1]], [[2]]) returns [[1],[2]]', () => {
            expect(__py.add([[1]], [[2]])).toEqual([[1], [2]]);
        });
        
        test('add with nested arrays', () => {
            expect(__py.add([[1, 2]], [[3, 4]])).toEqual([[1, 2], [3, 4]]);
        });
        
        test('add does not mutate original arrays', () => {
            const a = [1, 2];
            const b = [3, 4];
            const result = __py.add(a, b);
            expect(a).toEqual([1, 2]);
            expect(b).toEqual([3, 4]);
            expect(result).toEqual([1, 2, 3, 4]);
        });
        
        test('add multiple lists', () => {
            const a = [1];
            const b = [2];
            const c = [3];
            expect(__py.add(__py.add(a, b), c)).toEqual([1, 2, 3]);
        });
    });
    
    // =========================================================================
    // STRING CONCATENATION
    // =========================================================================
    
    describe('String concatenation', () => {
        test('add("hello", " world") returns "hello world"', () => {
            expect(__py.add("hello", " world")).toBe("hello world");
        });
        
        test('add("", "x") returns "x"', () => {
            expect(__py.add("", "x")).toBe("x");
        });
        
        test('add("x", "") returns "x"', () => {
            expect(__py.add("x", "")).toBe("x");
        });
        
        test('add("", "") returns ""', () => {
            expect(__py.add("", "")).toBe("");
        });
        
        test('add with unicode strings', () => {
            expect(__py.add("你", "好")).toBe("你好");
        });
        
        test('add with emoji', () => {
            expect(__py.add("Hi ", "👋")).toBe("Hi 👋");
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('add with boolean treated as number', () => {
            // JS behavior: true + true = 2
            expect(__py.add(true, true)).toBe(2);
            expect(__py.add(false, 1)).toBe(1);
        });
        
        test('add array with mixed types', () => {
            expect(__py.add([1, "a"], [true, null])).toEqual([1, "a", true, null]);
        });
        
        test('add long arrays', () => {
            const a = Array.from({length: 1000}, (_, i) => i);
            const b = Array.from({length: 1000}, (_, i) => i + 1000);
            const result = __py.add(a, b);
            expect(result.length).toBe(2000);
            expect(result[0]).toBe(0);
            expect(result[1999]).toBe(1999);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: [1] + [2] == [1, 2]', () => {
            expect(__py.add([1], [2])).toEqual([1, 2]);
        });
        
        test('Python: [1, 2] + [3, 4] == [1, 2, 3, 4]', () => {
            expect(__py.add([1, 2], [3, 4])).toEqual([1, 2, 3, 4]);
        });
        
        test('Python: "a" + "b" == "ab"', () => {
            expect(__py.add("a", "b")).toBe("ab");
        });
        
        test('Python: [] + [] == []', () => {
            expect(__py.add([], [])).toEqual([]);
        });
        
        test('Python: 1 + 2 == 3', () => {
            expect(__py.add(1, 2)).toBe(3);
        });
    });
    
    // =========================================================================
    // COMMON PATTERNS
    // =========================================================================
    
    describe('Common patterns in transpiled code', () => {
        test('items = items + [new_item] pattern', () => {
            let items = [1, 2, 3];
            const new_item = 4;
            items = __py.add(items, [new_item]);
            expect(items).toEqual([1, 2, 3, 4]);
        });
        
        test('[*items, new] pattern (spread)', () => {
            const items = [1, 2];
            // Python: [*items, new] → __py.add(items, [new])
            const result = __py.add(items, [3]);
            expect(result).toEqual([1, 2, 3]);
        });
        
        test('String building pattern', () => {
            let s = "";
            s = __py.add(s, "Hello");
            s = __py.add(s, " ");
            s = __py.add(s, "World");
            expect(s).toBe("Hello World");
        });
    });
});
