/**
 * Tests for __py.mod() - Python modulo semantics
 * 
 * CRITICAL DIFFERENCE:
 * Python: -7 % 3 = 2  (result has same sign as divisor)
 * JavaScript: -7 % 3 = -1 (result has same sign as dividend)
 * 
 * This runtime function implements Python modulo semantics.
 */

const __py = require('./setup');

describe('__py.mod() - Python Modulo', () => {
    
    // =========================================================================
    // BASIC MODULO (positive numbers)
    // =========================================================================
    
    describe('Basic modulo with positive numbers', () => {
        test('mod(7, 3) returns 1', () => {
            expect(__py.mod(7, 3)).toBe(1);
        });
        
        test('mod(10, 5) returns 0', () => {
            expect(__py.mod(10, 5)).toBe(0);
        });
        
        test('mod(10, 3) returns 1', () => {
            expect(__py.mod(10, 3)).toBe(1);
        });
        
        test('mod(15, 7) returns 1', () => {
            expect(__py.mod(15, 7)).toBe(1);
        });
        
        test('mod(100, 10) returns 0', () => {
            expect(__py.mod(100, 10)).toBe(0);
        });
        
        test('mod(5, 5) returns 0', () => {
            expect(__py.mod(5, 5)).toBe(0);
        });
        
        test('mod(3, 7) returns 3', () => {
            expect(__py.mod(3, 7)).toBe(3);
        });
    });
    
    // =========================================================================
    // NEGATIVE DIVIDEND (CRITICAL DIFFERENCE!)
    // =========================================================================
    
    describe('Negative dividend (critical difference!)', () => {
        test('mod(-7, 3) returns 2 (JS: -1!)', () => {
            // Python: -7 % 3 = 2
            // JS:     -7 % 3 = -1
            expect(__py.mod(-7, 3)).toBe(2);
            expect(-7 % 3).toBe(-1);  // Verify JS difference
        });
        
        test('mod(-1, 3) returns 2 (JS: -1!)', () => {
            expect(__py.mod(-1, 3)).toBe(2);
            expect(-1 % 3).toBe(-1);  // Verify JS difference
        });
        
        test('mod(-10, 3) returns 2 (JS: -1!)', () => {
            expect(__py.mod(-10, 3)).toBe(2);
            expect(-10 % 3).toBe(-1);  // Verify JS difference
        });
        
        test('mod(-4, 3) returns 2 (JS: -1!)', () => {
            expect(__py.mod(-4, 3)).toBe(2);
            expect(-4 % 3).toBe(-1);  // Verify JS difference
        });
        
        test('mod(-6, 4) returns 2 (JS: -2!)', () => {
            expect(__py.mod(-6, 4)).toBe(2);
            expect(-6 % 4).toBe(-2);  // Verify JS difference
        });
        
        test('mod(-5, 3) returns 1 (JS: -2!)', () => {
            expect(__py.mod(-5, 3)).toBe(1);
            expect(-5 % 3).toBe(-2);  // Verify JS difference
        });
        
        test('mod(-9, 3) returns 0', () => {
            // Divisible case - same in both
            expect(__py.mod(-9, 3)).toBe(0);
        });
    });
    
    // =========================================================================
    // NEGATIVE DIVISOR
    // =========================================================================
    
    describe('Negative divisor', () => {
        test('mod(7, -3) returns -2 (JS: 1!)', () => {
            expect(__py.mod(7, -3)).toBe(-2);
            expect(7 % -3).toBe(1);  // Verify JS difference
        });
        
        test('mod(1, -3) returns -2 (JS: 1!)', () => {
            expect(__py.mod(1, -3)).toBe(-2);
            expect(1 % -3).toBe(1);  // Verify JS difference
        });
        
        test('mod(5, -3) returns -1 (JS: 2!)', () => {
            expect(__py.mod(5, -3)).toBe(-1);
            expect(5 % -3).toBe(2);  // Verify JS difference
        });
        
        test('mod(10, -4) returns -2 (JS: 2!)', () => {
            expect(__py.mod(10, -4)).toBe(-2);
            expect(10 % -4).toBe(2);  // Verify JS difference
        });
    });
    
    // =========================================================================
    // BOTH NEGATIVE
    // =========================================================================
    
    describe('Both negative', () => {
        test('mod(-7, -3) returns -1', () => {
            expect(__py.mod(-7, -3)).toBe(-1);
        });
        
        test('mod(-1, -3) returns -1', () => {
            expect(__py.mod(-1, -3)).toBe(-1);
        });
        
        test('mod(-10, -3) returns -1', () => {
            expect(__py.mod(-10, -3)).toBe(-1);
        });
        
        test('mod(-9, -3) returns 0', () => {
            expect(__py.mod(-9, -3)).toBe(0);
        });
        
        test('mod(-5, -2) returns -1', () => {
            expect(__py.mod(-5, -2)).toBe(-1);
        });
    });
    
    // =========================================================================
    // FLOATS
    // =========================================================================
    
    describe('Floats', () => {
        test('mod(7.5, 2) returns 1.5', () => {
            expect(__py.mod(7.5, 2)).toBeCloseTo(1.5);
        });
        
        test('mod(-7.5, 2) returns 0.5 (JS: -1.5!)', () => {
            expect(__py.mod(-7.5, 2)).toBeCloseTo(0.5);
            expect(-7.5 % 2).toBeCloseTo(-1.5);  // Verify JS difference
        });
        
        test('mod(7.5, 2.5) returns 0', () => {
            expect(__py.mod(7.5, 2.5)).toBeCloseTo(0);
        });
        
        test('mod(10.5, 3) returns 1.5', () => {
            expect(__py.mod(10.5, 3)).toBeCloseTo(1.5);
        });
        
        test('mod(-10.5, 3) returns 1.5 (JS: -1.5!)', () => {
            expect(__py.mod(-10.5, 3)).toBeCloseTo(1.5);
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('mod(0, 5) returns 0', () => {
            expect(__py.mod(0, 5)).toBe(0);
        });
        
        test('mod(5, 1) returns 0', () => {
            expect(__py.mod(5, 1)).toBe(0);
        });
        
        test('mod(0, -5) returns 0', () => {
            expect(__py.mod(0, -5)).toBe(0);
        });
        
        test('mod with very large numbers', () => {
            expect(__py.mod(1000000007, 1000000)).toBe(7);
        });
        
        test('mod with very small floats', () => {
            expect(__py.mod(0.1, 0.03)).toBeCloseTo(0.01);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: -7 % 3 == 2', () => {
            expect(__py.mod(-7, 3)).toBe(2);
        });
        
        test('Python: -1 % 3 == 2', () => {
            expect(__py.mod(-1, 3)).toBe(2);
        });
        
        test('Python: 7 % -3 == -2', () => {
            expect(__py.mod(7, -3)).toBe(-2);
        });
        
        test('Python: -7 % -3 == -1', () => {
            expect(__py.mod(-7, -3)).toBe(-1);
        });
        
        test('Python: 0 % 5 == 0', () => {
            expect(__py.mod(0, 5)).toBe(0);
        });
    });
    
    // =========================================================================
    // COMMON USE CASES
    // =========================================================================
    
    describe('Common use cases', () => {
        test('Circular array indexing with negative', () => {
            const arr = [0, 1, 2, 3, 4];
            const idx = -1;
            // Python: arr[idx % len(arr)]
            expect(__py.mod(idx, arr.length)).toBe(4);
        });
        
        test('Wrap around calculation', () => {
            // Position on a 360-degree circle
            const angle = -30;
            expect(__py.mod(angle, 360)).toBe(330);
        });
        
        test('Day of week calculation', () => {
            // What day is 5 days before Monday (0)?
            const monday = 0;
            expect(__py.mod(monday - 5, 7)).toBe(2);  // Wednesday
        });
    });
});
