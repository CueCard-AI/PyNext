/**
 * Tests for __py.mul() - Python polymorphic multiplication
 * 
 * CRITICAL DIFFERENCE:
 * Python: "a" * 3 = "aaa" (string repetition)
 * JavaScript: "a" * 3 = NaN (string to number coercion fails)
 * 
 * Python: [1, 2] * 3 = [1, 2, 1, 2, 1, 2] (list repetition)
 * JavaScript: [1, 2] * 3 = NaN
 * 
 * This runtime function implements Python multiplication semantics.
 */

const __py = require('./setup');

describe('__py.mul() - Python Polymorphic Multiplication', () => {
    
    // =========================================================================
    // NUMBER MULTIPLICATION
    // =========================================================================
    
    describe('Number multiplication', () => {
        test('mul(3, 4) returns 12', () => {
            expect(__py.mul(3, 4)).toBe(12);
        });
        
        test('mul(2.5, 2) returns 5.0', () => {
            expect(__py.mul(2.5, 2)).toBe(5.0);
        });
        
        test('mul(-3, 4) returns -12', () => {
            expect(__py.mul(-3, 4)).toBe(-12);
        });
        
        test('mul(0, 100) returns 0', () => {
            expect(__py.mul(0, 100)).toBe(0);
        });
        
        test('mul with negative numbers', () => {
            expect(__py.mul(-3, -4)).toBe(12);
        });
        
        test('mul with Infinity', () => {
            expect(__py.mul(Infinity, 2)).toBe(Infinity);
            expect(__py.mul(-Infinity, 2)).toBe(-Infinity);
        });
    });
    
    // =========================================================================
    // STRING REPETITION (CRITICAL DIFFERENCE!)
    // =========================================================================
    
    describe('String repetition (critical difference!)', () => {
        test('mul("a", 3) returns "aaa" (JS: NaN!)', () => {
            expect(__py.mul("a", 3)).toBe("aaa");
            expect("a" * 3).toBeNaN();  // Verify JS difference!
        });
        
        test('mul(3, "a") returns "aaa" (both directions!)', () => {
            expect(__py.mul(3, "a")).toBe("aaa");
        });
        
        test('mul("ab", 2) returns "abab"', () => {
            expect(__py.mul("ab", 2)).toBe("abab");
        });
        
        test('mul("x", 0) returns ""', () => {
            expect(__py.mul("x", 0)).toBe("");
        });
        
        test('mul("x", -1) returns ""', () => {
            // Python: "x" * -1 = ""
            expect(__py.mul("x", -1)).toBe("");
        });
        
        test('mul("hello ", 3) returns "hello hello hello "', () => {
            expect(__py.mul("hello ", 3)).toBe("hello hello hello ");
        });
        
        test('mul with unicode string', () => {
            expect(__py.mul("你好", 2)).toBe("你好你好");
        });
        
        test('mul with emoji', () => {
            expect(__py.mul("👋", 3)).toBe("👋👋👋");
        });
        
        test('mul empty string', () => {
            expect(__py.mul("", 100)).toBe("");
        });
        
        test('mul string by 1', () => {
            expect(__py.mul("hello", 1)).toBe("hello");
        });
    });
    
    // =========================================================================
    // LIST REPETITION (CRITICAL DIFFERENCE!)
    // =========================================================================
    
    describe('List repetition (critical difference!)', () => {
        test('mul([1,2], 3) returns [1,2,1,2,1,2] (JS: NaN!)', () => {
            expect(__py.mul([1, 2], 3)).toEqual([1, 2, 1, 2, 1, 2]);
            expect([1, 2] * 3).toBeNaN();  // Verify JS difference!
        });
        
        test('mul(2, [1,2]) returns [1,2,1,2] (both directions!)', () => {
            expect(__py.mul(2, [1, 2])).toEqual([1, 2, 1, 2]);
        });
        
        test('mul([1], 0) returns []', () => {
            expect(__py.mul([1], 0)).toEqual([]);
        });
        
        test('mul([1], -1) returns []', () => {
            // Python: [1] * -1 = []
            expect(__py.mul([1], -1)).toEqual([]);
        });
        
        test('mul([[1]], 2) returns [[1],[1]]', () => {
            expect(__py.mul([[1]], 2)).toEqual([[1], [1]]);
        });
        
        test('mul([1, 2, 3], 1) returns [1, 2, 3]', () => {
            expect(__py.mul([1, 2, 3], 1)).toEqual([1, 2, 3]);
        });
        
        test('mul empty list', () => {
            expect(__py.mul([], 100)).toEqual([]);
        });
        
        test('mul does not mutate original array', () => {
            const arr = [1, 2];
            const result = __py.mul(arr, 3);
            expect(arr).toEqual([1, 2]);
            expect(result).toEqual([1, 2, 1, 2, 1, 2]);
        });
        
        test('mul with nested arrays', () => {
            expect(__py.mul([[1, 2]], 2)).toEqual([[1, 2], [1, 2]]);
        });
        
        test('mul with mixed types in list', () => {
            expect(__py.mul([1, "a", null], 2)).toEqual([1, "a", null, 1, "a", null]);
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('mul with boolean', () => {
            expect(__py.mul(5, true)).toBe(5);
            expect(__py.mul(5, false)).toBe(0);
        });
        
        test('mul very long repetition', () => {
            const result = __py.mul("x", 10000);
            expect(result.length).toBe(10000);
            expect(result[0]).toBe("x");
            expect(result[9999]).toBe("x");
        });
        
        test('mul list many times', () => {
            const result = __py.mul([1], 100);
            expect(result.length).toBe(100);
            expect(result.every(x => x === 1)).toBe(true);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: "a" * 3 == "aaa"', () => {
            expect(__py.mul("a", 3)).toBe("aaa");
        });
        
        test('Python: 3 * "a" == "aaa"', () => {
            expect(__py.mul(3, "a")).toBe("aaa");
        });
        
        test('Python: [1, 2] * 3 == [1, 2, 1, 2, 1, 2]', () => {
            expect(__py.mul([1, 2], 3)).toEqual([1, 2, 1, 2, 1, 2]);
        });
        
        test('Python: 3 * [1, 2] == [1, 2, 1, 2, 1, 2]', () => {
            expect(__py.mul(3, [1, 2])).toEqual([1, 2, 1, 2, 1, 2]);
        });
        
        test('Python: "x" * 0 == ""', () => {
            expect(__py.mul("x", 0)).toBe("");
        });
        
        test('Python: [1] * 0 == []', () => {
            expect(__py.mul([1], 0)).toEqual([]);
        });
        
        test('Python: "x" * -5 == ""', () => {
            expect(__py.mul("x", -5)).toBe("");
        });
        
        test('Python: [1] * -5 == []', () => {
            expect(__py.mul([1], -5)).toEqual([]);
        });
    });
    
    // =========================================================================
    // COMMON PATTERNS
    // =========================================================================
    
    describe('Common patterns in transpiled code', () => {
        test('Separator pattern: "-" * 20', () => {
            expect(__py.mul("-", 20)).toBe("--------------------");
        });
        
        test('Initialize list pattern: [0] * 10', () => {
            expect(__py.mul([0], 10)).toEqual([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
        });
        
        test('Initialize 2D grid: [[0] * 3] * 2', () => {
            // Note: This creates references in Python, but our impl creates copies
            const row = __py.mul([0], 3);
            expect(row).toEqual([0, 0, 0]);
        });
        
        test('Padding pattern', () => {
            const width = 10;
            const s = "hi";
            const padding = __py.mul(" ", width - s.length);
            expect(padding + s).toBe("        hi");
        });
    });
});
