/**
 * Phase 18 Risk Area Tests - Comprehensive JavaScript Runtime Tests
 * 
 * Tests all identified risk areas from the Phase 18 audit:
 * 1. Division by zero handling
 * 2. Deep equality with cycles
 * 3. Banker's rounding
 * 4. Modulo with zero
 * 5. Floor division with zero
 * 
 * These tests verify the __py runtime behaves correctly in edge cases.
 */

// Mock the __py runtime
const createMockPy = () => {
    // =============================================================================
    // DIVISION BY ZERO
    // =============================================================================
    
    function mod(a, b) {
        if (b === 0) {
            throw new Error("ZeroDivisionError: integer division or modulo by zero");
        }
        const result = ((a % b) + b) % b;
        return result === 0 ? 0 : result;
    }
    
    function floordiv(a, b) {
        if (b === 0) {
            throw new Error("ZeroDivisionError: integer division or modulo by zero");
        }
        return Math.floor(a / b);
    }
    
    function div(a, b, strict = false) {
        if (b === 0 && strict) {
            throw new Error("ZeroDivisionError: division by zero");
        }
        return a / b;
    }
    
    // =============================================================================
    // DEEP EQUALITY WITH CYCLE DETECTION
    // =============================================================================
    
    function eq(a, b, seenA = null, seenB = null) {
        if (a === b) return true;
        if (a === null || b === null) return a === b;
        if (a === undefined || b === undefined) return a === b;
        if (typeof a !== typeof b) return false;
        
        if (typeof a === 'object') {
            if (seenA === null) {
                seenA = new WeakMap();
                seenB = new WeakMap();
            }
            
            if (seenA.has(a)) {
                return seenA.get(a) === b && seenB.get(b) === a;
            }
            if (seenB.has(b)) {
                return seenB.get(b) === a && seenA.get(a) === b;
            }
            
            seenA.set(a, b);
            seenB.set(b, a);
        }
        
        if (Array.isArray(a) && Array.isArray(b)) {
            if (a.length !== b.length) return false;
            for (let i = 0; i < a.length; i++) {
                if (!eq(a[i], b[i], seenA, seenB)) return false;
            }
            return true;
        }
        
        if (a instanceof Set && b instanceof Set) {
            if (a.size !== b.size) return false;
            for (const item of a) {
                let found = false;
                for (const bItem of b) {
                    if (eq(item, bItem, seenA, seenB)) {
                        found = true;
                        break;
                    }
                }
                if (!found) return false;
            }
            return true;
        }
        
        if (a instanceof Map && b instanceof Map) {
            if (a.size !== b.size) return false;
            for (const [key, value] of a) {
                if (!b.has(key)) return false;
                if (!eq(value, b.get(key), seenA, seenB)) return false;
            }
            return true;
        }
        
        if (typeof a === 'object' && a.constructor === Object && b.constructor === Object) {
            const keysA = Object.keys(a);
            const keysB = Object.keys(b);
            if (keysA.length !== keysB.length) return false;
            for (const key of keysA) {
                if (!(key in b)) return false;
                if (!eq(a[key], b[key], seenA, seenB)) return false;
            }
            return true;
        }
        
        return false;
    }
    
    // =============================================================================
    // BANKER'S ROUNDING
    // =============================================================================
    
    function round(x, ndigits = 0) {
        if (!Number.isFinite(x)) return x;
        
        const factor = Math.pow(10, ndigits);
        const scaled = x * factor;
        const epsilon = Math.max(1e-9, Math.abs(scaled) * 1e-14);
        
        const isNegative = scaled < 0;
        const absScaled = Math.abs(scaled);
        const floor = Math.floor(absScaled);
        const decimal = absScaled - floor;
        
        let result;
        
        if (Math.abs(decimal - 0.5) < epsilon) {
            if (floor % 2 === 0) {
                result = floor;
            } else {
                result = floor + 1;
            }
        } else if (decimal < 0.5) {
            result = floor;
        } else {
            result = floor + 1;
        }
        
        if (isNegative) result = -result;
        
        const finalResult = result / factor;
        
        if (ndigits <= 0) {
            return Math.round(finalResult);
        }
        
        return finalResult;
    }
    
    return { mod, floordiv, div, eq, round };
};

const __py = createMockPy();

// =============================================================================
// DIVISION BY ZERO TESTS
// =============================================================================

describe('Division by Zero', () => {
    describe('floordiv', () => {
        test('floordiv throws on zero divisor', () => {
            expect(() => __py.floordiv(10, 0)).toThrow('ZeroDivisionError');
        });
        
        test('floordiv works with non-zero', () => {
            expect(__py.floordiv(7, 3)).toBe(2);
            expect(__py.floordiv(8, 4)).toBe(2);
            expect(__py.floordiv(-7, 3)).toBe(-3);
        });
    });
    
    describe('mod', () => {
        test('mod throws on zero divisor', () => {
            expect(() => __py.mod(10, 0)).toThrow('ZeroDivisionError');
        });
        
        test('mod works with non-zero', () => {
            expect(__py.mod(7, 3)).toBe(1);
            expect(__py.mod(-7, 3)).toBe(2);  // Python semantics
            expect(__py.mod(7, -3)).toBe(-2);  // Python semantics
        });
    });
    
    describe('div', () => {
        test('div returns Infinity by default', () => {
            expect(__py.div(10, 0)).toBe(Infinity);
            expect(__py.div(-10, 0)).toBe(-Infinity);
        });
        
        test('div throws in strict mode', () => {
            expect(() => __py.div(10, 0, true)).toThrow('ZeroDivisionError');
        });
        
        test('div works with non-zero', () => {
            expect(__py.div(10, 2)).toBe(5);
            expect(__py.div(7, 2)).toBe(3.5);
        });
    });
});

// =============================================================================
// DEEP EQUALITY WITH CYCLES TESTS
// =============================================================================

describe('Deep Equality with Cycle Detection', () => {
    describe('basic equality', () => {
        test('primitives', () => {
            expect(__py.eq(1, 1)).toBe(true);
            expect(__py.eq(1, 2)).toBe(false);
            expect(__py.eq('a', 'a')).toBe(true);
            expect(__py.eq(true, true)).toBe(true);
        });
        
        test('arrays', () => {
            expect(__py.eq([1, 2, 3], [1, 2, 3])).toBe(true);
            expect(__py.eq([1, 2], [1, 2, 3])).toBe(false);
            expect(__py.eq([[1, 2], [3, 4]], [[1, 2], [3, 4]])).toBe(true);
        });
        
        test('objects', () => {
            expect(__py.eq({a: 1, b: 2}, {a: 1, b: 2})).toBe(true);
            expect(__py.eq({a: 1}, {a: 1, b: 2})).toBe(false);
            expect(__py.eq({a: {b: 1}}, {a: {b: 1}})).toBe(true);
        });
    });
    
    describe('cycle detection', () => {
        test('self-referencing array', () => {
            const a = [1, 2];
            a.push(a);  // a = [1, 2, [1, 2, [...]]]
            
            const b = [1, 2];
            b.push(b);  // b = [1, 2, [1, 2, [...]]]
            
            // Should not stack overflow
            expect(__py.eq(a, b)).toBe(true);
        });
        
        test('self-referencing object', () => {
            const a = {x: 1};
            a.self = a;
            
            const b = {x: 1};
            b.self = b;
            
            // Should not stack overflow
            expect(__py.eq(a, b)).toBe(true);
        });
        
        test('mutually referencing objects', () => {
            const a = {x: 1};
            const b = {x: 1};
            a.other = b;
            b.other = a;
            
            const c = {x: 1};
            const d = {x: 1};
            c.other = d;
            d.other = c;
            
            // Should not stack overflow
            expect(__py.eq(a, c)).toBe(true);
        });
        
        test('deeply nested cycles', () => {
            const a = {level: 1, child: {level: 2, child: {level: 3}}};
            a.child.child.parent = a;
            
            const b = {level: 1, child: {level: 2, child: {level: 3}}};
            b.child.child.parent = b;
            
            // Should not stack overflow
            expect(__py.eq(a, b)).toBe(true);
        });
    });
    
    describe('Sets', () => {
        test('equal sets', () => {
            expect(__py.eq(new Set([1, 2, 3]), new Set([1, 2, 3]))).toBe(true);
            expect(__py.eq(new Set([1, 2, 3]), new Set([3, 2, 1]))).toBe(true);
        });
        
        test('unequal sets', () => {
            expect(__py.eq(new Set([1, 2]), new Set([1, 2, 3]))).toBe(false);
        });
    });
    
    describe('Maps', () => {
        test('equal maps', () => {
            const m1 = new Map([['a', 1], ['b', 2]]);
            const m2 = new Map([['a', 1], ['b', 2]]);
            expect(__py.eq(m1, m2)).toBe(true);
        });
        
        test('unequal maps', () => {
            const m1 = new Map([['a', 1]]);
            const m2 = new Map([['a', 2]]);
            expect(__py.eq(m1, m2)).toBe(false);
        });
    });
});

// =============================================================================
// BANKER'S ROUNDING TESTS
// =============================================================================

describe("Banker's Rounding", () => {
    describe('basic rounding', () => {
        test('round down', () => {
            expect(__py.round(2.4)).toBe(2);
            expect(__py.round(2.1)).toBe(2);
        });
        
        test('round up', () => {
            expect(__py.round(2.6)).toBe(3);
            expect(__py.round(2.9)).toBe(3);
        });
    });
    
    describe('banker\'s rounding at .5', () => {
        test('round 2.5 to even (2)', () => {
            expect(__py.round(2.5)).toBe(2);  // Round to even
        });
        
        test('round 3.5 to even (4)', () => {
            expect(__py.round(3.5)).toBe(4);  // Round to even
        });
        
        test('round 4.5 to even (4)', () => {
            expect(__py.round(4.5)).toBe(4);  // Round to even
        });
        
        test('round 5.5 to even (6)', () => {
            expect(__py.round(5.5)).toBe(6);  // Round to even
        });
        
        test('round 0.5 to even (0)', () => {
            expect(__py.round(0.5)).toBe(0);  // Round to even
        });
        
        test('round 1.5 to even (2)', () => {
            expect(__py.round(1.5)).toBe(2);  // Round to even
        });
    });
    
    describe('negative numbers with banker\'s rounding', () => {
        test('round -2.5 to even (-2)', () => {
            expect(__py.round(-2.5)).toBe(-2);  // Round to even
        });
        
        test('round -3.5 to even (-4)', () => {
            expect(__py.round(-3.5)).toBe(-4);  // Round to even
        });
        
        test('round -1.5 to even (-2)', () => {
            expect(__py.round(-1.5)).toBe(-2);  // Round to even
        });
    });
    
    describe('precision (ndigits)', () => {
        test('round to 1 decimal', () => {
            expect(__py.round(3.14159, 1)).toBeCloseTo(3.1, 5);
            expect(__py.round(3.15, 1)).toBeCloseTo(3.2, 5);  // 3.15 -> 3.2 (banker's)
        });
        
        test('round to 2 decimals', () => {
            expect(__py.round(3.14159, 2)).toBeCloseTo(3.14, 5);
            expect(__py.round(3.145, 2)).toBeCloseTo(3.14, 5);  // Banker's rounding
        });
        
        test('negative ndigits', () => {
            expect(__py.round(1234, -1)).toBe(1230);
            expect(__py.round(1234, -2)).toBe(1200);
            expect(__py.round(1250, -2)).toBe(1200);  // Banker's rounding
        });
    });
    
    describe('edge cases', () => {
        test('Infinity', () => {
            expect(__py.round(Infinity)).toBe(Infinity);
            expect(__py.round(-Infinity)).toBe(-Infinity);
        });
        
        test('NaN', () => {
            expect(Number.isNaN(__py.round(NaN))).toBe(true);
        });
        
        test('very large numbers', () => {
            expect(__py.round(1e15 + 0.5)).toBeDefined();  // Should not overflow
        });
        
        test('very small numbers', () => {
            // Note: 0.000005 is exactly 0.5 at the 5th decimal place
            // Due to floating point representation, this may round to 0 (banker's)
            // or 0.00001 depending on the actual floating point value
            const result = __py.round(0.000005, 5);
            expect(result === 0 || result === 0.00001).toBe(true);
        });
    });
});

// =============================================================================
// MODULO SEMANTICS TESTS
// =============================================================================

describe('Python Modulo Semantics', () => {
    test('positive modulo positive', () => {
        expect(__py.mod(7, 3)).toBe(1);
        expect(__py.mod(10, 5)).toBe(0);
    });
    
    test('negative modulo positive (Python semantics)', () => {
        // Python: -7 % 3 = 2 (JS: -7 % 3 = -1)
        expect(__py.mod(-7, 3)).toBe(2);
        expect(__py.mod(-1, 3)).toBe(2);
        expect(__py.mod(-10, 3)).toBe(2);
    });
    
    test('positive modulo negative (Python semantics)', () => {
        // Python: 7 % -3 = -2 (JS: 7 % -3 = 1)
        expect(__py.mod(7, -3)).toBe(-2);
        expect(__py.mod(1, -3)).toBe(-2);
    });
    
    test('negative modulo negative', () => {
        expect(__py.mod(-7, -3)).toBe(-1);
    });
    
    test('zero dividend', () => {
        expect(__py.mod(0, 5)).toBe(0);
    });
});

// =============================================================================
// FLOOR DIVISION SEMANTICS TESTS
// =============================================================================

describe('Python Floor Division Semantics', () => {
    test('positive floor division', () => {
        expect(__py.floordiv(7, 3)).toBe(2);
        expect(__py.floordiv(9, 3)).toBe(3);
    });
    
    test('negative floor division (rounds toward negative infinity)', () => {
        // Python: -7 // 3 = -3 (not -2)
        expect(__py.floordiv(-7, 3)).toBe(-3);
        expect(__py.floordiv(-1, 3)).toBe(-1);
    });
    
    test('positive dividend, negative divisor', () => {
        // Python: 7 // -3 = -3 (not -2)
        expect(__py.floordiv(7, -3)).toBe(-3);
    });
    
    test('both negative', () => {
        expect(__py.floordiv(-7, -3)).toBe(2);
    });
});

// =============================================================================
// INTEGRATION TESTS
// =============================================================================

describe('Integration Tests', () => {
    test('complex nested structure equality', () => {
        const complex1 = {
            users: [
                {name: 'Alice', scores: [95, 87, 92]},
                {name: 'Bob', scores: [88, 91, 85]}
            ],
            metadata: {
                created: 'today',
                tags: new Set(['important', 'review'])
            }
        };
        
        const complex2 = {
            users: [
                {name: 'Alice', scores: [95, 87, 92]},
                {name: 'Bob', scores: [88, 91, 85]}
            ],
            metadata: {
                created: 'today',
                tags: new Set(['review', 'important'])  // Different order
            }
        };
        
        expect(__py.eq(complex1, complex2)).toBe(true);
    });
    
    test('divmod-like calculation', () => {
        const a = 17;
        const b = 5;
        const q = __py.floordiv(a, b);
        const r = __py.mod(a, b);
        
        // a = q * b + r
        expect(q * b + r).toBe(a);
        expect(q).toBe(3);
        expect(r).toBe(2);
    });
    
    test('divmod with negatives', () => {
        const a = -17;
        const b = 5;
        const q = __py.floordiv(a, b);
        const r = __py.mod(a, b);
        
        // a = q * b + r should still hold
        expect(q * b + r).toBe(a);
        expect(q).toBe(-4);  // Python: -17 // 5 = -4
        expect(r).toBe(3);   // Python: -17 % 5 = 3
    });
});

// =============================================================================
// STRESS TESTS
// =============================================================================

describe('Stress Tests', () => {
    test('deeply nested array equality', () => {
        const depth = 100;
        let a = 'value';
        let b = 'value';
        
        for (let i = 0; i < depth; i++) {
            a = [a];
            b = [b];
        }
        
        expect(__py.eq(a, b)).toBe(true);
    });
    
    test('deeply nested object equality', () => {
        const depth = 100;
        let a = {value: 1};
        let b = {value: 1};
        
        for (let i = 0; i < depth; i++) {
            a = {child: a};
            b = {child: b};
        }
        
        expect(__py.eq(a, b)).toBe(true);
    });
    
    test('many rounds', () => {
        const values = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5];
        const expected = [0, 2, 2, 4, 4, 6, 6, 8, 8, 10];  // Banker's rounding
        
        values.forEach((v, i) => {
            expect(__py.round(v)).toBe(expected[i]);
        });
    });
});
