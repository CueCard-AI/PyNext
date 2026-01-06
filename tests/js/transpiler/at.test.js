/**
 * Tests for __py.at() - Python negative indexing
 * 
 * Python: items[-1] returns last element
 * JavaScript: items[-1] returns undefined
 * 
 * This runtime function makes JS behave like Python.
 */

const __py = require('./setup');

describe('__py.at() - Negative Indexing', () => {
    
    // =========================================================================
    // POSITIVE INDICES
    // =========================================================================
    
    describe('Positive indices', () => {
        test('at([1,2,3], 0) returns first element', () => {
            expect(__py.at([1, 2, 3], 0)).toBe(1);
        });
        
        test('at([1,2,3], 1) returns second element', () => {
            expect(__py.at([1, 2, 3], 1)).toBe(2);
        });
        
        test('at([1,2,3], 2) returns third element', () => {
            expect(__py.at([1, 2, 3], 2)).toBe(3);
        });
        
        test('at with single element array', () => {
            expect(__py.at([42], 0)).toBe(42);
        });
        
        test('at with nested arrays', () => {
            expect(__py.at([[1, 2], [3, 4]], 0)).toEqual([1, 2]);
            expect(__py.at([[1, 2], [3, 4]], 1)).toEqual([3, 4]);
        });
        
        test('at with objects in array', () => {
            const arr = [{a: 1}, {b: 2}];
            expect(__py.at(arr, 0)).toEqual({a: 1});
            expect(__py.at(arr, 1)).toEqual({b: 2});
        });
    });
    
    // =========================================================================
    // NEGATIVE INDICES
    // =========================================================================
    
    describe('Negative indices', () => {
        test('at([1,2,3], -1) returns last element', () => {
            expect(__py.at([1, 2, 3], -1)).toBe(3);
        });
        
        test('at([1,2,3], -2) returns second-to-last element', () => {
            expect(__py.at([1, 2, 3], -2)).toBe(2);
        });
        
        test('at([1,2,3], -3) returns first element', () => {
            expect(__py.at([1, 2, 3], -3)).toBe(1);
        });
        
        test('at with single element array and -1', () => {
            expect(__py.at([42], -1)).toBe(42);
        });
        
        test('at with nested arrays and negative index', () => {
            expect(__py.at([[1, 2], [3, 4]], -1)).toEqual([3, 4]);
            expect(__py.at([[1, 2], [3, 4]], -2)).toEqual([1, 2]);
        });
        
        test('at nested access with negative indices', () => {
            const arr = [[1, 2], [3, 4]];
            expect(__py.at(__py.at(arr, -1), -1)).toBe(4);
            expect(__py.at(__py.at(arr, -1), -2)).toBe(3);
        });
    });
    
    // =========================================================================
    // OUT OF BOUNDS
    // =========================================================================
    
    describe('Out of bounds', () => {
        test('at([1,2,3], 3) returns undefined', () => {
            expect(__py.at([1, 2, 3], 3)).toBeUndefined();
        });
        
        test('at([1,2,3], 100) returns undefined', () => {
            expect(__py.at([1, 2, 3], 100)).toBeUndefined();
        });
        
        test('at([1,2,3], -4) returns undefined', () => {
            expect(__py.at([1, 2, 3], -4)).toBeUndefined();
        });
        
        test('at([1,2,3], -100) returns undefined', () => {
            expect(__py.at([1, 2, 3], -100)).toBeUndefined();
        });
        
        test('at empty array returns undefined', () => {
            expect(__py.at([], 0)).toBeUndefined();
            expect(__py.at([], -1)).toBeUndefined();
        });
    });
    
    // =========================================================================
    // STRINGS
    // =========================================================================
    
    describe('Strings', () => {
        test('at("hello", 0) returns "h"', () => {
            expect(__py.at("hello", 0)).toBe("h");
        });
        
        test('at("hello", -1) returns "o"', () => {
            expect(__py.at("hello", -1)).toBe("o");
        });
        
        test('at("hello", -2) returns "l"', () => {
            expect(__py.at("hello", -2)).toBe("l");
        });
        
        test('at("hello", 4) returns "o"', () => {
            expect(__py.at("hello", 4)).toBe("o");
        });
        
        test('at empty string returns undefined', () => {
            expect(__py.at("", 0)).toBeUndefined();
            expect(__py.at("", -1)).toBeUndefined();
        });
        
        test('at single char string', () => {
            expect(__py.at("x", 0)).toBe("x");
            expect(__py.at("x", -1)).toBe("x");
        });
    });
    
    // =========================================================================
    // UNICODE STRINGS
    // =========================================================================
    
    describe('Unicode strings', () => {
        test('at with accented characters', () => {
            expect(__py.at("héllo", 0)).toBe("h");
            expect(__py.at("héllo", 1)).toBe("é");
            expect(__py.at("héllo", -1)).toBe("o");
        });
        
        test('at with emoji at start', () => {
            // Note: JS treats emoji as 2 chars, this tests basic handling
            const str = "abc";
            expect(__py.at(str, 0)).toBe("a");
            expect(__py.at(str, -1)).toBe("c");
        });
        
        test('at with Chinese characters', () => {
            expect(__py.at("你好", 0)).toBe("你");
            expect(__py.at("你好", -1)).toBe("好");
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('at with null returns undefined', () => {
            expect(__py.at(null, 0)).toBeUndefined();
        });
        
        test('at with undefined returns undefined', () => {
            expect(__py.at(undefined, 0)).toBeUndefined();
        });
        
        test('at with array containing null/undefined', () => {
            expect(__py.at([null, undefined, 0], 0)).toBeNull();
            expect(__py.at([null, undefined, 0], 1)).toBeUndefined();
            expect(__py.at([null, undefined, 0], -1)).toBe(0);
        });
        
        test('at with index 0.0 (float)', () => {
            expect(__py.at([1, 2, 3], 0.0)).toBe(1);
        });
        
        test('at with very large array', () => {
            const arr = Array.from({length: 10000}, (_, i) => i);
            expect(__py.at(arr, -1)).toBe(9999);
            expect(__py.at(arr, -10000)).toBe(0);
        });
    });
    
    // =========================================================================
    // COMPARISON WITH PYTHON BEHAVIOR
    // =========================================================================
    
    describe('Python behavior verification', () => {
        // These tests verify the exact behavior matches Python
        
        test('Python: [1,2,3][-1] == 3', () => {
            expect(__py.at([1, 2, 3], -1)).toBe(3);
        });
        
        test('Python: "abc"[-1] == "c"', () => {
            expect(__py.at("abc", -1)).toBe("c");
        });
        
        test('Python: [][-1] raises IndexError (JS: undefined)', () => {
            // Python raises IndexError, JS returns undefined
            expect(__py.at([], -1)).toBeUndefined();
        });
        
        test('Python: "x"[0] == "x"', () => {
            expect(__py.at("x", 0)).toBe("x");
        });
        
        test('Consistency: at(arr, 0) == arr[0]', () => {
            const arr = [1, 2, 3];
            expect(__py.at(arr, 0)).toBe(arr[0]);
        });
    });
});
