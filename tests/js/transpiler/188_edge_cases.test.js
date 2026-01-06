/**
 * Phase 18.8: Edge Cases JavaScript Tests
 *
 * Tests for edge cases: division, unicode, assert behavior, walrus patterns.
 *
 * Tests: 20
 */

const __py = require('./setup');

// =============================================================================
// DIVISION EDGE CASES
// =============================================================================

describe('Division Edge Cases', () => {
    test('division by zero returns Infinity', () => {
        expect(1 / 0).toBe(Infinity);
        expect(-1 / 0).toBe(-Infinity);
    });

    test('zero divided by zero is NaN', () => {
        expect(0 / 0).toBeNaN();
    });

    test('floor division with negative numbers', () => {
        expect(__py.floordiv(7, 3)).toBe(2);
        expect(__py.floordiv(-7, 3)).toBe(-3);  // Python: -3, not -2
        expect(__py.floordiv(7, -3)).toBe(-3);
    });

    test('modulo with negative numbers (Python semantics)', () => {
        expect(__py.mod(-7, 3)).toBe(2);   // Python: 2, JS native: -1
        expect(__py.mod(7, -3)).toBe(-2);  // Python: -2, JS native: 1
        expect(__py.mod(-7, -3)).toBe(-1); // Python: -1, JS native: -1
    });

    test('modulo preserves sign of divisor', () => {
        expect(__py.mod(10, 3)).toBe(1);
        expect(__py.mod(-10, 3)).toBe(2);  // Result is positive like divisor
        expect(__py.mod(10, -3)).toBe(-2); // Result is negative like divisor
    });
});

// =============================================================================
// UNICODE TESTS
// =============================================================================

describe('Unicode Support', () => {
    test('unicode string literals', () => {
        const greeting = "Привет мир";
        expect(greeting).toBe("Привет мир");
    });

    test('unicode in object keys', () => {
        const obj = { 日本語: 'Japanese' };
        expect(obj.日本語).toBe('Japanese');
    });

    test('unicode variable simulation', () => {
        const 变量 = 42;
        expect(变量).toBe(42);
    });

    test('emoji in strings', () => {
        const text = "Hello 👋 World 🌍";
        expect(text).toContain("👋");
        expect(text).toContain("🌍");
    });

    test('unicode string length', () => {
        const café = 'café';
        expect(café.length).toBe(4);
    });
});

// =============================================================================
// ASSERT PATTERN TESTS
// =============================================================================

describe('Assert Pattern', () => {
    test('assert pattern throws on false', () => {
        function assertPattern(condition, message = 'AssertionError') {
            if (!condition) {
                throw new Error('AssertionError: ' + message);
            }
        }
        
        expect(() => assertPattern(false)).toThrow('AssertionError');
        expect(() => assertPattern(true)).not.toThrow();
    });

    test('assert with custom message', () => {
        function assertPattern(condition, message) {
            if (!condition) {
                throw new Error('AssertionError: ' + message);
            }
        }
        
        expect(() => assertPattern(false, 'must be positive'))
            .toThrow('must be positive');
    });

    test('assert with expression', () => {
        function assertPattern(condition) {
            if (!condition) {
                throw new Error('AssertionError');
            }
        }
        
        const x = 5;
        expect(() => assertPattern(x > 0)).not.toThrow();
        expect(() => assertPattern(x < 0)).toThrow('AssertionError');
    });
});

// =============================================================================
// WALRUS PATTERN TESTS
// =============================================================================

describe('Walrus Operator Pattern', () => {
    test('walrus in if pattern', () => {
        // Python: if (x := get_value()): use(x)
        // JS:     let x; if (x = getValue()) { use(x); }
        
        function getValue() { return 42; }
        
        let x;
        if (x = getValue()) {
            expect(x).toBe(42);
        } else {
            fail('Should have entered if block');
        }
    });

    test('walrus with falsy value', () => {
        function getValue() { return 0; }
        
        let x;
        if (x = getValue()) {
            fail('Should not enter if block with falsy value');
        } else {
            expect(x).toBe(0);
        }
    });

    test('walrus in while pattern', () => {
        // Python: while (line := readline()): process(line)
        
        const lines = ['a', 'b', 'c'];
        let index = 0;
        function readline() {
            return index < lines.length ? lines[index++] : null;
        }
        
        const collected = [];
        let line;
        while (line = readline()) {
            collected.push(line);
        }
        
        expect(collected).toEqual(['a', 'b', 'c']);
    });
});

// =============================================================================
// LARGE INTEGER TESTS
// =============================================================================

describe('Large Integer Handling', () => {
    test('safe integer limit', () => {
        expect(Number.isSafeInteger(9007199254740991)).toBe(true);
        expect(Number.isSafeInteger(9007199254740992)).toBe(false);
    });

    test('large integer arithmetic precision loss', () => {
        // Beyond safe integer, precision is lost
        const large = 9007199254740993;
        // This may not equal the exact value due to IEEE 754
        expect(large).toBeGreaterThan(9007199254740990);
    });
});

// =============================================================================
// TRUTHINESS WITH PYTHON SEMANTICS
// =============================================================================

describe('Python Truthiness', () => {
    test('empty collections are falsy', () => {
        expect(__py.bool([])).toBe(false);
        expect(__py.bool({})).toBe(false);
        expect(__py.bool('')).toBe(false);
    });

    test('non-empty collections are truthy', () => {
        expect(__py.bool([1])).toBe(true);
        expect(__py.bool({a: 1})).toBe(true);
        expect(__py.bool('x')).toBe(true);
    });

    test('zero is falsy', () => {
        expect(__py.bool(0)).toBe(false);
        expect(__py.bool(-0)).toBe(false);
    });

    test('NaN is falsy', () => {
        expect(__py.bool(NaN)).toBe(false);
    });
});

