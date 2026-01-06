/**
 * Tests for __py.in() / contains() - Python 'in' operator
 * 
 * Python: x in [1,2,3] checks membership with deep equality
 * JavaScript: [1,2,3].includes(x) only works for primitives
 * 
 * This runtime function implements Python 'in' semantics.
 */

const __py = require('./setup');

describe('__py.contains() / in - Python Membership', () => {
    
    // =========================================================================
    // LIST MEMBERSHIP
    // =========================================================================
    
    describe('List membership', () => {
        test('contains(1, [1,2,3]) returns true', () => {
            expect(__py.contains(1, [1, 2, 3])).toBe(true);
        });
        
        test('contains(4, [1,2,3]) returns false', () => {
            expect(__py.contains(4, [1, 2, 3])).toBe(false);
        });
        
        test('contains("a", ["a","b","c"]) returns true', () => {
            expect(__py.contains("a", ["a", "b", "c"])).toBe(true);
        });
        
        test('contains("d", ["a","b","c"]) returns false', () => {
            expect(__py.contains("d", ["a", "b", "c"])).toBe(false);
        });
        
        test('contains(null, [null, 1, 2]) returns true', () => {
            expect(__py.contains(null, [null, 1, 2])).toBe(true);
        });
        
        test('contains(undefined, [undefined]) returns true', () => {
            expect(__py.contains(undefined, [undefined])).toBe(true);
        });
        
        test('contains in empty list returns false', () => {
            expect(__py.contains(1, [])).toBe(false);
        });
    });
    
    // =========================================================================
    // LIST MEMBERSHIP WITH DEEP EQUALITY
    // =========================================================================
    
    describe('List membership with deep equality', () => {
        test('contains([1,2], [[1,2],[3,4]]) returns true (deep check!)', () => {
            // This is different from JS!
            expect(__py.contains([1, 2], [[1, 2], [3, 4]])).toBe(true);
        });
        
        test('contains([1,3], [[1,2],[3,4]]) returns false', () => {
            expect(__py.contains([1, 3], [[1, 2], [3, 4]])).toBe(false);
        });
        
        test('contains({a:1}, [{a:1},{b:2}]) returns true (deep check!)', () => {
            expect(__py.contains({a: 1}, [{a: 1}, {b: 2}])).toBe(true);
        });
        
        test('contains({a:2}, [{a:1},{b:2}]) returns false', () => {
            expect(__py.contains({a: 2}, [{a: 1}, {b: 2}])).toBe(false);
        });
    });
    
    // =========================================================================
    // DICT MEMBERSHIP (keys only)
    // =========================================================================
    
    describe('Dict membership (keys only)', () => {
        test('contains("a", {a:1,b:2}) returns true', () => {
            expect(__py.contains("a", {a: 1, b: 2})).toBe(true);
        });
        
        test('contains("c", {a:1,b:2}) returns false', () => {
            expect(__py.contains("c", {a: 1, b: 2})).toBe(false);
        });
        
        test('contains("1", {"1":"a"}) returns true', () => {
            expect(__py.contains("1", {"1": "a"})).toBe(true);
        });
        
        test('contains in empty dict returns false', () => {
            expect(__py.contains("a", {})).toBe(false);
        });
        
        test('contains value (not key) returns false', () => {
            // Python: 1 in {"a": 1} is False (1 is a value, not a key)
            expect(__py.contains(1, {a: 1})).toBe(false);
        });
    });
    
    // =========================================================================
    // STRING MEMBERSHIP (substring)
    // =========================================================================
    
    describe('String membership (substring)', () => {
        test('contains("ell", "hello") returns true', () => {
            expect(__py.contains("ell", "hello")).toBe(true);
        });
        
        test('contains("x", "hello") returns false', () => {
            expect(__py.contains("x", "hello")).toBe(false);
        });
        
        test('contains("", "hello") returns true (empty string)', () => {
            expect(__py.contains("", "hello")).toBe(true);
        });
        
        test('contains("hello", "hello") returns true', () => {
            expect(__py.contains("hello", "hello")).toBe(true);
        });
        
        test('contains("Hello", "hello") returns false (case sensitive)', () => {
            expect(__py.contains("Hello", "hello")).toBe(false);
        });
        
        test('contains single char', () => {
            expect(__py.contains("h", "hello")).toBe(true);
            expect(__py.contains("o", "hello")).toBe(true);
            expect(__py.contains("z", "hello")).toBe(false);
        });
        
        test('contains in empty string', () => {
            expect(__py.contains("a", "")).toBe(false);
            expect(__py.contains("", "")).toBe(true);
        });
    });
    
    // =========================================================================
    // SET MEMBERSHIP
    // =========================================================================
    
    describe('Set membership', () => {
        test('contains(1, new Set([1,2,3])) returns true', () => {
            expect(__py.contains(1, new Set([1, 2, 3]))).toBe(true);
        });
        
        test('contains(4, new Set([1,2,3])) returns false', () => {
            expect(__py.contains(4, new Set([1, 2, 3]))).toBe(false);
        });
        
        test('contains in empty set returns false', () => {
            expect(__py.contains(1, new Set())).toBe(false);
        });
        
        test('contains with string in set', () => {
            expect(__py.contains("a", new Set(["a", "b"]))).toBe(true);
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('contains with 0', () => {
            expect(__py.contains(0, [0, 1, 2])).toBe(true);
            expect(__py.contains(0, [1, 2, 3])).toBe(false);
        });
        
        test('contains with false', () => {
            expect(__py.contains(false, [false, true])).toBe(true);
            expect(__py.contains(false, [0, 1])).toBe(false);  // 0 !== false
        });
        
        test('contains with NaN', () => {
            // NaN !== NaN in JS, but our eq handles it
            expect(__py.contains(NaN, [NaN])).toBe(false);  // Consistent with Python
        });
        
        test('contains with mixed types', () => {
            expect(__py.contains(1, [1, "1", true])).toBe(true);
            expect(__py.contains("1", [1, "1", true])).toBe(true);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: 1 in [1, 2, 3]', () => {
            expect(__py.contains(1, [1, 2, 3])).toBe(true);
        });
        
        test('Python: [1, 2] in [[1, 2], [3, 4]]', () => {
            expect(__py.contains([1, 2], [[1, 2], [3, 4]])).toBe(true);
        });
        
        test('Python: "a" in {"a": 1}', () => {
            expect(__py.contains("a", {a: 1})).toBe(true);
        });
        
        test('Python: 1 in {"a": 1} is False (1 is value, not key)', () => {
            expect(__py.contains(1, {a: 1})).toBe(false);
        });
        
        test('Python: "ell" in "hello"', () => {
            expect(__py.contains("ell", "hello")).toBe(true);
        });
        
        test('Python: "" in "hello"', () => {
            expect(__py.contains("", "hello")).toBe(true);
        });
    });
    
    // =========================================================================
    // COMMON PATTERNS
    // =========================================================================
    
    describe('Common patterns in transpiled code', () => {
        test('if x in items: pattern', () => {
            const items = [1, 2, 3];
            const x = 2;
            if (__py.contains(x, items)) {
                expect(true).toBe(true);
            } else {
                throw new Error("Should have found item");
            }
        });
        
        test('if key in dict: pattern', () => {
            const config = {debug: true, verbose: false};
            if (__py.contains("debug", config)) {
                expect(true).toBe(true);
            } else {
                throw new Error("Should have found key");
            }
        });
        
        test('if substr in string: pattern', () => {
            const message = "Hello, World!";
            if (__py.contains("World", message)) {
                expect(true).toBe(true);
            } else {
                throw new Error("Should have found substring");
            }
        });
    });
});
