/**
 * Tests for __py.bool() - Python truthiness
 * 
 * CRITICAL DIFFERENCE:
 * Python: [] is falsy, {} is falsy
 * JavaScript: [] is truthy, {} is truthy
 * 
 * This runtime function implements Python truthiness semantics.
 */

const __py = require('./setup');

describe('__py.bool() - Python Truthiness', () => {
    
    // =========================================================================
    // PYTHON-SPECIFIC FALSY VALUES (JS would say truthy!)
    // =========================================================================
    
    describe('Python-specific falsy values (JS truthy!)', () => {
        test('bool([]) returns false (JS: truthy!)', () => {
            expect(__py.bool([])).toBe(false);
        });
        
        test('bool({}) returns false (JS: truthy!)', () => {
            expect(__py.bool({})).toBe(false);
        });
        
        test('bool(new Set()) returns false', () => {
            expect(__py.bool(new Set())).toBe(false);
        });
        
        test('bool(new Map()) returns false', () => {
            expect(__py.bool(new Map())).toBe(false);
        });
    });
    
    // =========================================================================
    // STANDARD FALSY VALUES (same in Python and JS)
    // =========================================================================
    
    describe('Standard falsy values', () => {
        test('bool(null) returns false', () => {
            expect(__py.bool(null)).toBe(false);
        });
        
        test('bool(undefined) returns false', () => {
            expect(__py.bool(undefined)).toBe(false);
        });
        
        test('bool(false) returns false', () => {
            expect(__py.bool(false)).toBe(false);
        });
        
        test('bool(0) returns false', () => {
            expect(__py.bool(0)).toBe(false);
        });
        
        test('bool(0.0) returns false', () => {
            expect(__py.bool(0.0)).toBe(false);
        });
        
        test('bool(-0) returns false', () => {
            expect(__py.bool(-0)).toBe(false);
        });
        
        test('bool("") returns false', () => {
            expect(__py.bool("")).toBe(false);
        });
        
        test('bool(NaN) returns false', () => {
            expect(__py.bool(NaN)).toBe(false);
        });
    });
    
    // =========================================================================
    // TRUTHY VALUES - ARRAYS
    // =========================================================================
    
    describe('Truthy values - Arrays', () => {
        test('bool([1]) returns true', () => {
            expect(__py.bool([1])).toBe(true);
        });
        
        test('bool([0]) returns true (non-empty!)', () => {
            // Note: [0] is truthy because it's non-empty, even though 0 is falsy
            expect(__py.bool([0])).toBe(true);
        });
        
        test('bool([null]) returns true (non-empty!)', () => {
            expect(__py.bool([null])).toBe(true);
        });
        
        test('bool([""]) returns true (non-empty!)', () => {
            expect(__py.bool([""])).toBe(true);
        });
        
        test('bool([[]]) returns true (non-empty!)', () => {
            expect(__py.bool([[]])).toBe(true);
        });
        
        test('bool([1,2,3]) returns true', () => {
            expect(__py.bool([1, 2, 3])).toBe(true);
        });
        
        test('bool([false]) returns true (non-empty!)', () => {
            expect(__py.bool([false])).toBe(true);
        });
    });
    
    // =========================================================================
    // TRUTHY VALUES - OBJECTS
    // =========================================================================
    
    describe('Truthy values - Objects', () => {
        test('bool({a: 1}) returns true', () => {
            expect(__py.bool({a: 1})).toBe(true);
        });
        
        test('bool({a: 0}) returns true (non-empty!)', () => {
            expect(__py.bool({a: 0})).toBe(true);
        });
        
        test('bool({0: 0}) returns true (non-empty!)', () => {
            expect(__py.bool({0: 0})).toBe(true);
        });
        
        test('bool({a: null}) returns true (non-empty!)', () => {
            expect(__py.bool({a: null})).toBe(true);
        });
        
        test('bool({a: 1, b: 2}) returns true', () => {
            expect(__py.bool({a: 1, b: 2})).toBe(true);
        });
    });
    
    // =========================================================================
    // TRUTHY VALUES - STRINGS
    // =========================================================================
    
    describe('Truthy values - Strings', () => {
        test('bool("0") returns true (non-empty string!)', () => {
            expect(__py.bool("0")).toBe(true);
        });
        
        test('bool(" ") returns true (whitespace is truthy)', () => {
            expect(__py.bool(" ")).toBe(true);
        });
        
        test('bool("false") returns true (non-empty string!)', () => {
            expect(__py.bool("false")).toBe(true);
        });
        
        test('bool("null") returns true (non-empty string!)', () => {
            expect(__py.bool("null")).toBe(true);
        });
        
        test('bool("hello") returns true', () => {
            expect(__py.bool("hello")).toBe(true);
        });
        
        test('bool("\\n") returns true (newline is truthy)', () => {
            expect(__py.bool("\n")).toBe(true);
        });
        
        test('bool("\\t") returns true (tab is truthy)', () => {
            expect(__py.bool("\t")).toBe(true);
        });
    });
    
    // =========================================================================
    // TRUTHY VALUES - NUMBERS
    // =========================================================================
    
    describe('Truthy values - Numbers', () => {
        test('bool(1) returns true', () => {
            expect(__py.bool(1)).toBe(true);
        });
        
        test('bool(-1) returns true', () => {
            expect(__py.bool(-1)).toBe(true);
        });
        
        test('bool(0.1) returns true', () => {
            expect(__py.bool(0.1)).toBe(true);
        });
        
        test('bool(-0.1) returns true', () => {
            expect(__py.bool(-0.1)).toBe(true);
        });
        
        test('bool(Infinity) returns true', () => {
            expect(__py.bool(Infinity)).toBe(true);
        });
        
        test('bool(-Infinity) returns true', () => {
            expect(__py.bool(-Infinity)).toBe(true);
        });
        
        test('bool(0.0001) returns true', () => {
            expect(__py.bool(0.0001)).toBe(true);
        });
        
        test('bool(1e-100) returns true', () => {
            expect(__py.bool(1e-100)).toBe(true);
        });
    });
    
    // =========================================================================
    // TRUTHY VALUES - BOOLEANS
    // =========================================================================
    
    describe('Truthy values - Booleans', () => {
        test('bool(true) returns true', () => {
            expect(__py.bool(true)).toBe(true);
        });
    });
    
    // =========================================================================
    // TRUTHY VALUES - SETS AND MAPS
    // =========================================================================
    
    describe('Truthy values - Sets and Maps', () => {
        test('bool(new Set([1])) returns true', () => {
            expect(__py.bool(new Set([1]))).toBe(true);
        });
        
        test('bool(new Set([0])) returns true (non-empty)', () => {
            expect(__py.bool(new Set([0]))).toBe(true);
        });
        
        test('bool(new Map([[1, 1]])) returns true', () => {
            expect(__py.bool(new Map([[1, 1]]))).toBe(true);
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('bool of function returns true', () => {
            expect(__py.bool(() => {})).toBe(true);
        });
        
        test('bool of Date returns true', () => {
            expect(__py.bool(new Date())).toBe(true);
        });
        
        test('bool of class instance returns true', () => {
            class MyClass {}
            expect(__py.bool(new MyClass())).toBe(true);
        });
        
        test('bool of Symbol returns true', () => {
            expect(__py.bool(Symbol())).toBe(true);
        });
        
        test('bool of array with holes returns based on length', () => {
            const arr = new Array(3);  // [undefined, undefined, undefined]
            expect(__py.bool(arr)).toBe(true);  // length > 0
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: bool([]) == False', () => {
            expect(__py.bool([])).toBe(false);
        });
        
        test('Python: bool({}) == False', () => {
            expect(__py.bool({})).toBe(false);
        });
        
        test('Python: bool([0]) == True (non-empty)', () => {
            expect(__py.bool([0])).toBe(true);
        });
        
        test('Python: bool("0") == True (non-empty string)', () => {
            expect(__py.bool("0")).toBe(true);
        });
        
        test('Python: bool(0.0) == False', () => {
            expect(__py.bool(0.0)).toBe(false);
        });
        
        test('Python: bool(None) == False', () => {
            // None maps to null in JS
            expect(__py.bool(null)).toBe(false);
        });
    });
    
    // =========================================================================
    // COMMON PATTERNS IN TRANSPILED CODE
    // =========================================================================
    
    describe('Common patterns in transpiled code', () => {
        test('if items: pattern with empty list', () => {
            const items = [];
            // Python: if items:  → if (__py.bool(items)) {
            if (__py.bool(items)) {
                throw new Error("Should not reach here");
            }
            expect(true).toBe(true);  // Passed if we get here
        });
        
        test('if items: pattern with non-empty list', () => {
            const items = [1, 2, 3];
            let reached = false;
            if (__py.bool(items)) {
                reached = true;
            }
            expect(reached).toBe(true);
        });
        
        test('if config: pattern with empty dict', () => {
            const config = {};
            if (__py.bool(config)) {
                throw new Error("Should not reach here");
            }
            expect(true).toBe(true);
        });
        
        test('if config: pattern with non-empty dict', () => {
            const config = {debug: true};
            let reached = false;
            if (__py.bool(config)) {
                reached = true;
            }
            expect(reached).toBe(true);
        });
    });
});
