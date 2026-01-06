/**
 * Tests for __py.slice() - Python slicing
 * 
 * Python: items[start:stop:step]
 * JavaScript: No direct equivalent
 * 
 * This runtime function provides full Python slicing semantics.
 */

const __py = require('./setup');

describe('__py.slice() - Python Slicing', () => {
    
    // =========================================================================
    // BASIC SLICING (positive indices)
    // =========================================================================
    
    describe('Basic slicing with positive indices', () => {
        test('slice([1,2,3,4,5], 1, 3) returns [2,3]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], 1, 3)).toEqual([2, 3]);
        });
        
        test('slice([1,2,3,4,5], 0, 2) returns [1,2]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], 0, 2)).toEqual([1, 2]);
        });
        
        test('slice([1,2,3,4,5], 2, 5) returns [3,4,5]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], 2, 5)).toEqual([3, 4, 5]);
        });
        
        test('slice([1,2,3,4,5], 0, 5) returns entire array', () => {
            expect(__py.slice([1, 2, 3, 4, 5], 0, 5)).toEqual([1, 2, 3, 4, 5]);
        });
        
        test('slice with same start and stop returns empty', () => {
            expect(__py.slice([1, 2, 3], 1, 1)).toEqual([]);
        });
        
        test('slice single element', () => {
            expect(__py.slice([1, 2, 3], 1, 2)).toEqual([2]);
        });
    });
    
    // =========================================================================
    // OMITTED START/STOP (null)
    // =========================================================================
    
    describe('Omitted start/stop (null)', () => {
        test('slice([1,2,3,4,5], null, 3) returns [1,2,3]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], null, 3)).toEqual([1, 2, 3]);
        });
        
        test('slice([1,2,3,4,5], 2, null) returns [3,4,5]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], 2, null)).toEqual([3, 4, 5]);
        });
        
        test('slice([1,2,3,4,5], null, null) returns entire array', () => {
            expect(__py.slice([1, 2, 3, 4, 5], null, null)).toEqual([1, 2, 3, 4, 5]);
        });
        
        test('slice empty array with null bounds returns empty', () => {
            expect(__py.slice([], null, null)).toEqual([]);
        });
    });
    
    // =========================================================================
    // NEGATIVE INDICES
    // =========================================================================
    
    describe('Negative indices', () => {
        test('slice([1,2,3,4,5], -3, null) returns [3,4,5]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], -3, null)).toEqual([3, 4, 5]);
        });
        
        test('slice([1,2,3,4,5], null, -2) returns [1,2,3]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], null, -2)).toEqual([1, 2, 3]);
        });
        
        test('slice([1,2,3,4,5], -3, -1) returns [3,4]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], -3, -1)).toEqual([3, 4]);
        });
        
        test('slice([1,2,3,4,5], -4, -2) returns [2,3]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], -4, -2)).toEqual([2, 3]);
        });
        
        test('slice([1,2,3,4,5], -5, -1) returns [1,2,3,4]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], -5, -1)).toEqual([1, 2, 3, 4]);
        });
        
        test('slice([1,2,3,4,5], -1, null) returns [5]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], -1, null)).toEqual([5]);
        });
    });
    
    // =========================================================================
    // STEP VALUES
    // =========================================================================
    
    describe('Step values', () => {
        test('slice([1,2,3,4,5], null, null, 2) returns [1,3,5]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], null, null, 2)).toEqual([1, 3, 5]);
        });
        
        test('slice([1,2,3,4,5], 1, null, 2) returns [2,4]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], 1, null, 2)).toEqual([2, 4]);
        });
        
        test('slice([1,2,3,4,5], null, null, 3) returns [1,4]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], null, null, 3)).toEqual([1, 4]);
        });
        
        test('slice([0,1,2,3,4,5,6,7,8,9], 0, 10, 2) returns [0,2,4,6,8]', () => {
            expect(__py.slice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 0, 10, 2)).toEqual([0, 2, 4, 6, 8]);
        });
        
        test('slice with step of 1 is default behavior', () => {
            expect(__py.slice([1, 2, 3], 0, 3, 1)).toEqual([1, 2, 3]);
        });
    });
    
    // =========================================================================
    // NEGATIVE STEP (REVERSE)
    // =========================================================================
    
    describe('Negative step (reverse)', () => {
        test('slice([1,2,3,4,5], null, null, -1) reverses array', () => {
            expect(__py.slice([1, 2, 3, 4, 5], null, null, -1)).toEqual([5, 4, 3, 2, 1]);
        });
        
        test('slice([1,2,3,4,5], 3, 0, -1) returns [4,3,2]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], 3, 0, -1)).toEqual([4, 3, 2]);
        });
        
        test('slice([1,2,3,4,5], null, null, -2) returns [5,3,1]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], null, null, -2)).toEqual([5, 3, 1]);
        });
        
        test('slice([1,2,3,4,5], 4, 1, -1) returns [5,4,3]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], 4, 1, -1)).toEqual([5, 4, 3]);
        });
        
        test('slice([1,2,3,4,5], -1, -4, -1) returns [5,4,3]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], -1, -4, -1)).toEqual([5, 4, 3]);
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('slice with start > stop returns empty', () => {
            expect(__py.slice([1, 2, 3], 5, 10)).toEqual([]);
        });
        
        test('slice with negative out of bounds returns empty', () => {
            expect(__py.slice([1, 2, 3], -10, -8)).toEqual([]);
        });
        
        test('slice empty array returns empty', () => {
            expect(__py.slice([], 0, 1)).toEqual([]);
        });
        
        test('slice with step 0 throws error', () => {
            expect(() => __py.slice([1, 2, 3], 0, 3, 0)).toThrow();
        });
        
        test('slice with very large stop index', () => {
            expect(__py.slice([1, 2, 3], 0, 100)).toEqual([1, 2, 3]);
        });
        
        test('slice with very negative start index', () => {
            expect(__py.slice([1, 2, 3], -100, 3)).toEqual([1, 2, 3]);
        });
        
        test('slice null returns empty array', () => {
            expect(__py.slice(null, 0, 1)).toEqual([]);
        });
        
        test('slice undefined returns empty array', () => {
            expect(__py.slice(undefined, 0, 1)).toEqual([]);
        });
    });
    
    // =========================================================================
    // STRINGS
    // =========================================================================
    
    describe('Strings', () => {
        test('slice("hello", 1, 4) returns "ell"', () => {
            expect(__py.slice("hello", 1, 4)).toBe("ell");
        });
        
        test('slice("hello", null, null, -1) reverses string', () => {
            expect(__py.slice("hello", null, null, -1)).toBe("olleh");
        });
        
        test('slice("hello", 0, 2) returns "he"', () => {
            expect(__py.slice("hello", 0, 2)).toBe("he");
        });
        
        test('slice("hello", -2, null) returns "lo"', () => {
            expect(__py.slice("hello", -2, null)).toBe("lo");
        });
        
        test('slice("hello", null, -2) returns "hel"', () => {
            expect(__py.slice("hello", null, -2)).toBe("hel");
        });
        
        test('slice("abcdef", null, null, 2) returns "ace"', () => {
            expect(__py.slice("abcdef", null, null, 2)).toBe("ace");
        });
        
        test('slice empty string returns empty string', () => {
            expect(__py.slice("", 0, 1)).toBe("");
        });
    });
    
    // =========================================================================
    // NESTED ARRAYS
    // =========================================================================
    
    describe('Nested arrays', () => {
        test('slice of nested arrays preserves structure', () => {
            const arr = [[1, 2], [3, 4], [5, 6]];
            expect(__py.slice(arr, 0, 2)).toEqual([[1, 2], [3, 4]]);
        });
        
        test('reverse slice of nested arrays', () => {
            const arr = [[1, 2], [3, 4], [5, 6]];
            expect(__py.slice(arr, null, null, -1)).toEqual([[5, 6], [3, 4], [1, 2]]);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: [1,2,3,4,5][1:3] == [2,3]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], 1, 3)).toEqual([2, 3]);
        });
        
        test('Python: [1,2,3,4,5][::-1] == [5,4,3,2,1]', () => {
            expect(__py.slice([1, 2, 3, 4, 5], null, null, -1)).toEqual([5, 4, 3, 2, 1]);
        });
        
        test('Python: "hello"[::-1] == "olleh"', () => {
            expect(__py.slice("hello", null, null, -1)).toBe("olleh");
        });
        
        test('Python: [1,2,3][::2] == [1,3]', () => {
            expect(__py.slice([1, 2, 3], null, null, 2)).toEqual([1, 3]);
        });
        
        test('Python: [1,2,3][-2:] == [2,3]', () => {
            expect(__py.slice([1, 2, 3], -2, null)).toEqual([2, 3]);
        });
    });
});
