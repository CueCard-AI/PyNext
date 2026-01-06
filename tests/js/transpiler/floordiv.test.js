/**
 * Tests for __py.floordiv() - Python floor division
 * 
 * Python: 7 // 3 = 2 (floor toward negative infinity)
 * JavaScript: Math.floor(7 / 3) = 2 (same)
 * 
 * But for negative numbers:
 * Python: -7 // 3 = -3 (floor toward -inf)
 * JavaScript: Math.floor(-7 / 3) = -3 (same) but Math.trunc(-7/3) = -2
 * 
 * This runtime function ensures consistent Python floor division.
 */

const __py = require('./setup');

describe('__py.floordiv() - Python Floor Division', () => {
    
    // =========================================================================
    // BASIC FLOOR DIVISION (positive numbers)
    // =========================================================================
    
    describe('Basic floor division with positive numbers', () => {
        test('floordiv(7, 3) returns 2', () => {
            expect(__py.floordiv(7, 3)).toBe(2);
        });
        
        test('floordiv(10, 3) returns 3', () => {
            expect(__py.floordiv(10, 3)).toBe(3);
        });
        
        test('floordiv(9, 3) returns 3', () => {
            expect(__py.floordiv(9, 3)).toBe(3);
        });
        
        test('floordiv(15, 5) returns 3', () => {
            expect(__py.floordiv(15, 5)).toBe(3);
        });
        
        test('floordiv(100, 10) returns 10', () => {
            expect(__py.floordiv(100, 10)).toBe(10);
        });
        
        test('floordiv(1, 2) returns 0', () => {
            expect(__py.floordiv(1, 2)).toBe(0);
        });
        
        test('floordiv(3, 4) returns 0', () => {
            expect(__py.floordiv(3, 4)).toBe(0);
        });
    });
    
    // =========================================================================
    // NEGATIVE NUMBERS
    // =========================================================================
    
    describe('Negative numbers (floor toward -infinity)', () => {
        test('floordiv(-7, 3) returns -3 (not -2!)', () => {
            // Floor toward -infinity: -7/3 = -2.33... → -3
            expect(__py.floordiv(-7, 3)).toBe(-3);
        });
        
        test('floordiv(7, -3) returns -3 (not -2!)', () => {
            expect(__py.floordiv(7, -3)).toBe(-3);
        });
        
        test('floordiv(-7, -3) returns 2', () => {
            expect(__py.floordiv(-7, -3)).toBe(2);
        });
        
        test('floordiv(-9, 3) returns -3 (exact division)', () => {
            expect(__py.floordiv(-9, 3)).toBe(-3);
        });
        
        test('floordiv(-1, 3) returns -1', () => {
            expect(__py.floordiv(-1, 3)).toBe(-1);
        });
        
        test('floordiv(-2, 3) returns -1', () => {
            expect(__py.floordiv(-2, 3)).toBe(-1);
        });
        
        test('floordiv(-4, 3) returns -2', () => {
            expect(__py.floordiv(-4, 3)).toBe(-2);
        });
        
        test('floordiv(1, -2) returns -1', () => {
            expect(__py.floordiv(1, -2)).toBe(-1);
        });
    });
    
    // =========================================================================
    // FLOATS
    // =========================================================================
    
    describe('Floats', () => {
        test('floordiv(7.5, 2) returns 3', () => {
            expect(__py.floordiv(7.5, 2)).toBe(3);
        });
        
        test('floordiv(-7.5, 2) returns -4 (floor toward -inf)', () => {
            expect(__py.floordiv(-7.5, 2)).toBe(-4);
        });
        
        test('floordiv(10.5, 3) returns 3', () => {
            expect(__py.floordiv(10.5, 3)).toBe(3);
        });
        
        test('floordiv(2.5, 0.5) returns 5', () => {
            expect(__py.floordiv(2.5, 0.5)).toBe(5);
        });
        
        test('floordiv(-2.5, 0.5) returns -5', () => {
            expect(__py.floordiv(-2.5, 0.5)).toBe(-5);
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('floordiv(0, 5) returns 0', () => {
            expect(__py.floordiv(0, 5)).toBe(0);
        });
        
        test('floordiv(5, 5) returns 1', () => {
            expect(__py.floordiv(5, 5)).toBe(1);
        });
        
        test('floordiv(4, 5) returns 0', () => {
            expect(__py.floordiv(4, 5)).toBe(0);
        });
        
        test('floordiv with very large numbers', () => {
            expect(__py.floordiv(1000000000, 7)).toBe(142857142);
        });
        
        test('floordiv with very small divisor', () => {
            expect(__py.floordiv(10, 0.1)).toBe(100);
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: 7 // 3 == 2', () => {
            expect(__py.floordiv(7, 3)).toBe(2);
        });
        
        test('Python: -7 // 3 == -3', () => {
            expect(__py.floordiv(-7, 3)).toBe(-3);
        });
        
        test('Python: 7 // -3 == -3', () => {
            expect(__py.floordiv(7, -3)).toBe(-3);
        });
        
        test('Python: -7 // -3 == 2', () => {
            expect(__py.floordiv(-7, -3)).toBe(2);
        });
        
        test('Python: 5 // 2 == 2', () => {
            expect(__py.floordiv(5, 2)).toBe(2);
        });
        
        test('Python: -5 // 2 == -3', () => {
            expect(__py.floordiv(-5, 2)).toBe(-3);
        });
    });
});
