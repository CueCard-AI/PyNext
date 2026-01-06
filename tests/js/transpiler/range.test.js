/**
 * Tests for __py.range() - Python range
 * 
 * Python: range(5) → [0, 1, 2, 3, 4]
 * JavaScript: No direct equivalent
 * 
 * This runtime function provides Python range behavior.
 */

const __py = require('./setup');

describe('__py.range() - Python Range', () => {
    
    // =========================================================================
    // SINGLE ARGUMENT (stop)
    // =========================================================================
    
    describe('Single argument (stop)', () => {
        test('range(5) returns [0,1,2,3,4]', () => {
            expect(__py.range(5)).toEqual([0, 1, 2, 3, 4]);
        });
        
        test('range(0) returns []', () => {
            expect(__py.range(0)).toEqual([]);
        });
        
        test('range(1) returns [0]', () => {
            expect(__py.range(1)).toEqual([0]);
        });
        
        test('range(10) returns [0,1,2,3,4,5,6,7,8,9]', () => {
            expect(__py.range(10)).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
        });
        
        test('range with negative stop returns []', () => {
            expect(__py.range(-5)).toEqual([]);
        });
    });
    
    // =========================================================================
    // TWO ARGUMENTS (start, stop)
    // =========================================================================
    
    describe('Two arguments (start, stop)', () => {
        test('range(2, 5) returns [2,3,4]', () => {
            expect(__py.range(2, 5)).toEqual([2, 3, 4]);
        });
        
        test('range(0, 10) returns [0,1,2,3,4,5,6,7,8,9]', () => {
            expect(__py.range(0, 10)).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
        });
        
        test('range(5, 5) returns []', () => {
            expect(__py.range(5, 5)).toEqual([]);
        });
        
        test('range(5, 2) returns [] (start > stop)', () => {
            expect(__py.range(5, 2)).toEqual([]);
        });
        
        test('range with negative start', () => {
            expect(__py.range(-3, 3)).toEqual([-3, -2, -1, 0, 1, 2]);
        });
        
        test('range with negative stop', () => {
            expect(__py.range(-5, -2)).toEqual([-5, -4, -3]);
        });
        
        test('range both negative', () => {
            expect(__py.range(-10, -5)).toEqual([-10, -9, -8, -7, -6]);
        });
    });
    
    // =========================================================================
    // THREE ARGUMENTS (start, stop, step)
    // =========================================================================
    
    describe('Three arguments (start, stop, step)', () => {
        test('range(0, 10, 2) returns [0,2,4,6,8]', () => {
            expect(__py.range(0, 10, 2)).toEqual([0, 2, 4, 6, 8]);
        });
        
        test('range(1, 10, 2) returns [1,3,5,7,9]', () => {
            expect(__py.range(1, 10, 2)).toEqual([1, 3, 5, 7, 9]);
        });
        
        test('range(0, 10, 3) returns [0,3,6,9]', () => {
            expect(__py.range(0, 10, 3)).toEqual([0, 3, 6, 9]);
        });
        
        test('range(0, 10, 5) returns [0,5]', () => {
            expect(__py.range(0, 10, 5)).toEqual([0, 5]);
        });
        
        test('range(0, 10, 10) returns [0]', () => {
            expect(__py.range(0, 10, 10)).toEqual([0]);
        });
        
        test('range(0, 10, 20) returns [0]', () => {
            expect(__py.range(0, 10, 20)).toEqual([0]);
        });
    });
    
    // =========================================================================
    // NEGATIVE STEP (counting down)
    // =========================================================================
    
    describe('Negative step (counting down)', () => {
        test('range(5, 0, -1) returns [5,4,3,2,1]', () => {
            expect(__py.range(5, 0, -1)).toEqual([5, 4, 3, 2, 1]);
        });
        
        test('range(10, 0, -2) returns [10,8,6,4,2]', () => {
            expect(__py.range(10, 0, -2)).toEqual([10, 8, 6, 4, 2]);
        });
        
        test('range(10, 0, -3) returns [10,7,4,1]', () => {
            expect(__py.range(10, 0, -3)).toEqual([10, 7, 4, 1]);
        });
        
        test('range(0, -5, -1) returns [0,-1,-2,-3,-4]', () => {
            expect(__py.range(0, -5, -1)).toEqual([0, -1, -2, -3, -4]);
        });
        
        test('range(5, 0, -1) vs range(0, 5)', () => {
            expect(__py.range(5, 0, -1)).toEqual([5, 4, 3, 2, 1]);
            expect(__py.range(0, 5)).toEqual([0, 1, 2, 3, 4]);
        });
        
        test('range with negative step but start < stop returns []', () => {
            expect(__py.range(0, 5, -1)).toEqual([]);
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('range(100) length is 100', () => {
            expect(__py.range(100).length).toBe(100);
        });
        
        test('range(1000) is correct', () => {
            const result = __py.range(1000);
            expect(result.length).toBe(1000);
            expect(result[0]).toBe(0);
            expect(result[999]).toBe(999);
        });
        
        test('range step of 1 is default', () => {
            expect(__py.range(0, 5, 1)).toEqual([0, 1, 2, 3, 4]);
            expect(__py.range(0, 5)).toEqual([0, 1, 2, 3, 4]);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: list(range(5))', () => {
            expect(__py.range(5)).toEqual([0, 1, 2, 3, 4]);
        });
        
        test('Python: list(range(2, 5))', () => {
            expect(__py.range(2, 5)).toEqual([2, 3, 4]);
        });
        
        test('Python: list(range(0, 10, 2))', () => {
            expect(__py.range(0, 10, 2)).toEqual([0, 2, 4, 6, 8]);
        });
        
        test('Python: list(range(5, 0, -1))', () => {
            expect(__py.range(5, 0, -1)).toEqual([5, 4, 3, 2, 1]);
        });
        
        test('Python: list(range(-3, 3))', () => {
            expect(__py.range(-3, 3)).toEqual([-3, -2, -1, 0, 1, 2]);
        });
    });
    
    // =========================================================================
    // COMMON PATTERNS
    // =========================================================================
    
    describe('Common patterns in transpiled code', () => {
        test('for i in range(n): pattern', () => {
            const result = [];
            for (const i of __py.range(5)) {
                result.push(i * 2);
            }
            expect(result).toEqual([0, 2, 4, 6, 8]);
        });
        
        test('for i in range(len(items)): pattern', () => {
            const items = ["a", "b", "c"];
            const result = [];
            for (const i of __py.range(items.length)) {
                result.push(`${i}: ${items[i]}`);
            }
            expect(result).toEqual(["0: a", "1: b", "2: c"]);
        });
        
        test('for i in range(start, end): pattern', () => {
            const result = [];
            for (const i of __py.range(3, 7)) {
                result.push(i);
            }
            expect(result).toEqual([3, 4, 5, 6]);
        });
        
        test('for i in range(n, 0, -1): countdown pattern', () => {
            const result = [];
            for (const i of __py.range(5, 0, -1)) {
                result.push(i);
            }
            expect(result).toEqual([5, 4, 3, 2, 1]);
        });
    });
});
