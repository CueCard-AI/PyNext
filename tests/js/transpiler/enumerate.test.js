/**
 * Tests for __py.enumerate() - Python enumerate
 * 
 * Python: enumerate([a, b, c]) → [(0, a), (1, b), (2, c)]
 * JavaScript: No direct equivalent
 * 
 * This runtime function provides Python enumerate behavior.
 */

const __py = require('./setup');

describe('__py.enumerate() - Python Enumerate', () => {
    
    // =========================================================================
    // BASIC ENUMERATION
    // =========================================================================
    
    describe('Basic enumeration', () => {
        test('enumerate([a,b,c]) returns [[0,a],[1,b],[2,c]]', () => {
            expect(__py.enumerate(["a", "b", "c"])).toEqual([
                [0, "a"],
                [1, "b"],
                [2, "c"]
            ]);
        });
        
        test('enumerate empty array returns []', () => {
            expect(__py.enumerate([])).toEqual([]);
        });
        
        test('enumerate single element', () => {
            expect(__py.enumerate([42])).toEqual([[0, 42]]);
        });
        
        test('enumerate with numbers', () => {
            expect(__py.enumerate([10, 20, 30])).toEqual([
                [0, 10],
                [1, 20],
                [2, 30]
            ]);
        });
        
        test('enumerate with mixed types', () => {
            expect(__py.enumerate([1, "a", null, true])).toEqual([
                [0, 1],
                [1, "a"],
                [2, null],
                [3, true]
            ]);
        });
    });
    
    // =========================================================================
    // WITH START PARAMETER
    // =========================================================================
    
    describe('With start parameter', () => {
        test('enumerate([a,b], 5) returns [[5,a],[6,b]]', () => {
            expect(__py.enumerate(["a", "b"], 5)).toEqual([
                [5, "a"],
                [6, "b"]
            ]);
        });
        
        test('enumerate with start=1 (common pattern)', () => {
            expect(__py.enumerate(["first", "second", "third"], 1)).toEqual([
                [1, "first"],
                [2, "second"],
                [3, "third"]
            ]);
        });
        
        test('enumerate with start=0 (default)', () => {
            expect(__py.enumerate(["a", "b"], 0)).toEqual([
                [0, "a"],
                [1, "b"]
            ]);
        });
        
        test('enumerate with negative start', () => {
            expect(__py.enumerate(["a", "b"], -2)).toEqual([
                [-2, "a"],
                [-1, "b"]
            ]);
        });
        
        test('enumerate with large start', () => {
            expect(__py.enumerate(["a"], 1000)).toEqual([[1000, "a"]]);
        });
    });
    
    // =========================================================================
    // STRING ENUMERATION
    // =========================================================================
    
    describe('String enumeration', () => {
        test('enumerate("ab") returns [[0,"a"],[1,"b"]]', () => {
            expect(__py.enumerate("ab")).toEqual([
                [0, "a"],
                [1, "b"]
            ]);
        });
        
        test('enumerate empty string returns []', () => {
            expect(__py.enumerate("")).toEqual([]);
        });
        
        test('enumerate single char string', () => {
            expect(__py.enumerate("x")).toEqual([[0, "x"]]);
        });
        
        test('enumerate unicode string', () => {
            expect(__py.enumerate("你好")).toEqual([
                [0, "你"],
                [1, "好"]
            ]);
        });
    });
    
    // =========================================================================
    // NESTED ARRAYS
    // =========================================================================
    
    describe('Nested arrays', () => {
        test('enumerate with nested arrays', () => {
            expect(__py.enumerate([[1, 2], [3, 4]])).toEqual([
                [0, [1, 2]],
                [1, [3, 4]]
            ]);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: list(enumerate(["a", "b", "c"]))', () => {
            expect(__py.enumerate(["a", "b", "c"])).toEqual([
                [0, "a"],
                [1, "b"],
                [2, "c"]
            ]);
        });
        
        test('Python: list(enumerate(["a", "b"], start=1))', () => {
            expect(__py.enumerate(["a", "b"], 1)).toEqual([
                [1, "a"],
                [2, "b"]
            ]);
        });
        
        test('Python: list(enumerate("abc"))', () => {
            expect(__py.enumerate("abc")).toEqual([
                [0, "a"],
                [1, "b"],
                [2, "c"]
            ]);
        });
    });
    
    // =========================================================================
    // COMMON PATTERNS
    // =========================================================================
    
    describe('Common patterns in transpiled code', () => {
        test('for i, item in enumerate(items): pattern', () => {
            const items = ["a", "b", "c"];
            const result = [];
            for (const [i, item] of __py.enumerate(items)) {
                result.push(`${i}: ${item}`);
            }
            expect(result).toEqual(["0: a", "1: b", "2: c"]);
        });
        
        test('for i, item in enumerate(items, 1): pattern', () => {
            const items = ["first", "second"];
            const result = [];
            for (const [i, item] of __py.enumerate(items, 1)) {
                result.push(`${i}. ${item}`);
            }
            expect(result).toEqual(["1. first", "2. second"]);
        });
    });
});
