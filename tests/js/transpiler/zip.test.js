/**
 * Tests for __py.zip() - Python zip
 * 
 * Python: zip([1,2], [a,b]) → [(1, a), (2, b)]
 * JavaScript: No direct equivalent
 * 
 * This runtime function provides Python zip behavior.
 */

const __py = require('./setup');

describe('__py.zip() - Python Zip', () => {
    
    // =========================================================================
    // BASIC ZIP
    // =========================================================================
    
    describe('Basic zip', () => {
        test('zip([1,2], [a,b]) returns [[1,a],[2,b]]', () => {
            expect(__py.zip([1, 2], ["a", "b"])).toEqual([
                [1, "a"],
                [2, "b"]
            ]);
        });
        
        test('zip single element arrays', () => {
            expect(__py.zip([1], ["a"])).toEqual([[1, "a"]]);
        });
        
        test('zip empty arrays returns []', () => {
            expect(__py.zip([], [])).toEqual([]);
        });
        
        test('zip with three arrays', () => {
            expect(__py.zip([1, 2], ["a", "b"], [true, false])).toEqual([
                [1, "a", true],
                [2, "b", false]
            ]);
        });
        
        test('zip with four arrays', () => {
            expect(__py.zip([1], [2], [3], [4])).toEqual([[1, 2, 3, 4]]);
        });
    });
    
    // =========================================================================
    // DIFFERENT LENGTH ARRAYS (shortest wins)
    // =========================================================================
    
    describe('Different length arrays (shortest wins)', () => {
        test('zip([1,2,3], [a,b]) returns [[1,a],[2,b]]', () => {
            // Python zip stops at shortest
            expect(__py.zip([1, 2, 3], ["a", "b"])).toEqual([
                [1, "a"],
                [2, "b"]
            ]);
        });
        
        test('zip with first shorter', () => {
            expect(__py.zip([1], ["a", "b", "c"])).toEqual([[1, "a"]]);
        });
        
        test('zip with one empty', () => {
            expect(__py.zip([], [1, 2, 3])).toEqual([]);
        });
        
        test('zip three arrays different lengths', () => {
            expect(__py.zip([1, 2, 3, 4], ["a", "b"], [true])).toEqual([
                [1, "a", true]
            ]);
        });
    });
    
    // =========================================================================
    // STRING ZIPPING
    // =========================================================================
    
    describe('String zipping', () => {
        test('zip with strings', () => {
            expect(__py.zip("ab", "xy")).toEqual([
                ["a", "x"],
                ["b", "y"]
            ]);
        });
        
        test('zip array with string', () => {
            expect(__py.zip([1, 2], "ab")).toEqual([
                [1, "a"],
                [2, "b"]
            ]);
        });
    });
    
    // =========================================================================
    // NESTED ARRAYS
    // =========================================================================
    
    describe('Nested arrays', () => {
        test('zip with nested arrays', () => {
            expect(__py.zip([[1, 2]], [[3, 4]])).toEqual([
                [[1, 2], [3, 4]]
            ]);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: list(zip([1, 2], ["a", "b"]))', () => {
            expect(__py.zip([1, 2], ["a", "b"])).toEqual([
                [1, "a"],
                [2, "b"]
            ]);
        });
        
        test('Python: list(zip([1, 2, 3], ["a", "b"]))', () => {
            expect(__py.zip([1, 2, 3], ["a", "b"])).toEqual([
                [1, "a"],
                [2, "b"]
            ]);
        });
        
        test('Python: list(zip("abc", [1, 2, 3]))', () => {
            expect(__py.zip("abc", [1, 2, 3])).toEqual([
                ["a", 1],
                ["b", 2],
                ["c", 3]
            ]);
        });
        
        test('Python: list(zip([], []))', () => {
            expect(__py.zip([], [])).toEqual([]);
        });
    });
    
    // =========================================================================
    // COMMON PATTERNS
    // =========================================================================
    
    describe('Common patterns in transpiled code', () => {
        test('for a, b in zip(list1, list2): pattern', () => {
            const names = ["Alice", "Bob"];
            const ages = [30, 25];
            const result = [];
            for (const [name, age] of __py.zip(names, ages)) {
                result.push(`${name} is ${age}`);
            }
            expect(result).toEqual(["Alice is 30", "Bob is 25"]);
        });
        
        test('dict(zip(keys, values)) pattern', () => {
            const keys = ["a", "b", "c"];
            const values = [1, 2, 3];
            const result = Object.fromEntries(__py.zip(keys, values));
            expect(result).toEqual({a: 1, b: 2, c: 3});
        });
        
        test('Parallel iteration', () => {
            const xs = [1, 2, 3];
            const ys = [4, 5, 6];
            const sums = __py.zip(xs, ys).map(([x, y]) => x + y);
            expect(sums).toEqual([5, 7, 9]);
        });
    });
});
