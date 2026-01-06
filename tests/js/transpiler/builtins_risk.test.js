/**
 * Phase 18.4 Risk Area Tests
 * 
 * Tests all the high-risk semantic differences identified in Phase 18.4.
 * These tests verify that the Python-to-JavaScript transpilation produces
 * correct results for edge cases.
 */

const __py = require('./setup');

// =============================================================================
// SORTED() TESTS - Stable, String, Mixed Types
// =============================================================================

describe('sorted() risk areas', () => {
    test('sorts strings lexicographically', () => {
        expect(__py.sorted(['banana', 'Apple', 'cherry'], null, false)).toEqual(['Apple', 'banana', 'cherry']);
    });
    
    test('sorts numbers numerically', () => {
        expect(__py.sorted([10, 2, 30, 1], null, false)).toEqual([1, 2, 10, 30]);
    });
    
    test('stable sort preserves order of equal elements', () => {
        const items = [
            { name: 'b', val: 1 },
            { name: 'a', val: 2 },
            { name: 'c', val: 1 },
        ];
        const result = __py.sorted(items, x => x.val, false);
        // Items with val=1 should preserve original order: 'b' before 'c'
        expect(result[0].name).toBe('b');
        expect(result[1].name).toBe('c');
        expect(result[2].name).toBe('a');
    });
    
    test('throws TypeError on mixed types', () => {
        expect(() => __py.sorted([1, 'a', 2])).toThrow(TypeError);
    });
    
    test('reverse=true works correctly', () => {
        expect(__py.sorted([1, 3, 2], null, true)).toEqual([3, 2, 1]);
    });
    
    test('key function works with strings', () => {
        expect(__py.sorted(['bb', 'aaa', 'c'], x => x.length, false)).toEqual(['c', 'bb', 'aaa']);
    });
    
    test('empty array returns empty', () => {
        expect(__py.sorted([], null, false)).toEqual([]);
    });
    
    test('single element returns copy', () => {
        const arr = [42];
        const result = __py.sorted(arr, null, false);
        expect(result).toEqual([42]);
        expect(result).not.toBe(arr);  // Should be a copy
    });
});

// =============================================================================
// MIN/MAX() TESTS - Type Checking, Empty, Key
// =============================================================================

describe('min() risk areas', () => {
    test('throws on empty sequence', () => {
        expect(() => __py.min([])).toThrow(/empty sequence/);
    });
    
    test('throws TypeError on mixed types', () => {
        expect(() => __py.min([1, 'a'])).toThrow(TypeError);
    });
    
    test('works with key function', () => {
        expect(__py.min(['bb', 'aaa', 'c'], x => x.length)).toBe('c');
    });
    
    test('works with strings', () => {
        expect(__py.min(['b', 'a', 'c'], null)).toBe('a');
    });
    
    test('works with numbers', () => {
        expect(__py.min([3, 1, 2], null)).toBe(1);
    });
    
    test('single element returns that element', () => {
        expect(__py.min([42], null)).toBe(42);
    });
    
    test('handles negative numbers', () => {
        expect(__py.min([-5, 0, 5], null)).toBe(-5);
    });
});

describe('max() risk areas', () => {
    test('throws on empty sequence', () => {
        expect(() => __py.max([])).toThrow(/empty sequence/);
    });
    
    test('throws TypeError on mixed types', () => {
        expect(() => __py.max([1, 'a'])).toThrow(TypeError);
    });
    
    test('works with key function', () => {
        expect(__py.max(['bb', 'aaa', 'c'], x => x.length)).toBe('aaa');
    });
    
    test('works with strings', () => {
        expect(__py.max(['b', 'a', 'c'], null)).toBe('c');
    });
    
    test('works with numbers', () => {
        expect(__py.max([3, 1, 2], null)).toBe(3);
    });
});

// =============================================================================
// FILTER() TESTS - None Handling, Truthiness
// =============================================================================

describe('filter() risk areas', () => {
    test('filter(None) filters falsy values with Python semantics', () => {
        expect(__py.filter(null, [0, 1, '', 'a', [], [1]])).toEqual([1, 'a', [1]]);
    });
    
    test('filter(None) handles empty list as falsy', () => {
        const result = __py.filter(null, [[], [1], [2]]);
        expect(result).toEqual([[1], [2]]);
    });
    
    test('filter(None) handles empty dict as falsy', () => {
        const result = __py.filter(null, [{}, {a: 1}]);
        expect(result).toEqual([{a: 1}]);
    });
    
    test('filter with function works normally', () => {
        expect(__py.filter(x => x > 0, [-1, 0, 1, 2])).toEqual([1, 2]);
    });
    
    test('filter(undefined) acts like filter(None)', () => {
        expect(__py.filter(undefined, [0, 1, '', 'a'])).toEqual([1, 'a']);
    });
});

// =============================================================================
// ROUND() TESTS - Banker's Rounding
// =============================================================================

describe('round() risk areas - banker\'s rounding', () => {
    test('round(2.5) rounds to 2 (nearest even)', () => {
        expect(__py.round(2.5, 0)).toBe(2);
    });
    
    test('round(3.5) rounds to 4 (nearest even)', () => {
        expect(__py.round(3.5, 0)).toBe(4);
    });
    
    test('round(4.5) rounds to 4 (nearest even)', () => {
        expect(__py.round(4.5, 0)).toBe(4);
    });
    
    test('round(5.5) rounds to 6 (nearest even)', () => {
        expect(__py.round(5.5, 0)).toBe(6);
    });
    
    test('round(1.5) rounds to 2 (nearest even)', () => {
        expect(__py.round(1.5, 0)).toBe(2);
    });
    
    test('round(0.5) rounds to 0 (nearest even)', () => {
        expect(__py.round(0.5, 0)).toBe(0);
    });
    
    test('round with digits works', () => {
        expect(__py.round(3.145, 2)).toBeCloseTo(3.14, 10);
    });
    
    test('round normal cases work', () => {
        expect(__py.round(2.4, 0)).toBe(2);
        expect(__py.round(2.6, 0)).toBe(3);
    });
});

// =============================================================================
// ANY/ALL() TESTS - Python Truthiness
// =============================================================================

describe('any()/all() risk areas - Python truthiness', () => {
    test('any([]) returns false', () => {
        expect(__py.any([])).toBe(false);
    });
    
    test('all([]) returns true (vacuous truth)', () => {
        expect(__py.all([])).toBe(true);
    });
    
    test('any([[], {}]) returns false (empty containers are falsy)', () => {
        expect(__py.any([[], {}])).toBe(false);
    });
    
    test('all([1, 2, 3]) returns true', () => {
        expect(__py.all([1, 2, 3])).toBe(true);
    });
    
    test('all([1, 0, 2]) returns false', () => {
        expect(__py.all([1, 0, 2])).toBe(false);
    });
    
    test('any([0, "", [], 1]) returns true', () => {
        expect(__py.any([0, '', [], 1])).toBe(true);
    });
    
    test('any handles Set correctly', () => {
        expect(__py.any([new Set()])).toBe(false);  // Empty set is falsy
        expect(__py.any([new Set([1])])).toBe(true);  // Non-empty set is truthy
    });
});

// =============================================================================
// RANDOM.SEED() TESTS - Reproducibility
// =============================================================================

describe('random.seed() risk areas - reproducibility', () => {
    test('same seed produces same random sequence', () => {
        __py.random.seed(12345);
        const first = [
            __py.random.random(),
            __py.random.random(),
            __py.random.random(),
        ];
        
        __py.random.seed(12345);
        const second = [
            __py.random.random(),
            __py.random.random(),
            __py.random.random(),
        ];
        
        expect(first).toEqual(second);
    });
    
    test('different seeds produce different sequences', () => {
        __py.random.seed(12345);
        const first = __py.random.random();
        
        __py.random.seed(54321);
        const second = __py.random.random();
        
        expect(first).not.toBe(second);
    });
    
    test('seed with string produces consistent results', () => {
        __py.random.seed('hello');
        const first = __py.random.random();
        
        __py.random.seed('hello');
        const second = __py.random.random();
        
        expect(first).toBe(second);
    });
    
    test('seed(null) returns to unseeded mode', () => {
        __py.random.seed(42);
        const seeded1 = __py.random.random();
        
        __py.random.seed(null);  // Unseed
        // Now it uses Math.random() which is not reproducible
        
        __py.random.seed(42);
        const seeded2 = __py.random.random();
        
        expect(seeded1).toBe(seeded2);  // Same seed, same result
    });
    
    test('randint is reproducible with seed', () => {
        __py.random.seed(42);
        const first = [
            __py.random.randint(1, 100),
            __py.random.randint(1, 100),
            __py.random.randint(1, 100),
        ];
        
        __py.random.seed(42);
        const second = [
            __py.random.randint(1, 100),
            __py.random.randint(1, 100),
            __py.random.randint(1, 100),
        ];
        
        expect(first).toEqual(second);
    });
    
    test('shuffle is reproducible with seed', () => {
        __py.random.seed(42);
        const arr1 = [1, 2, 3, 4, 5];
        __py.random.shuffle(arr1);
        
        __py.random.seed(42);
        const arr2 = [1, 2, 3, 4, 5];
        __py.random.shuffle(arr2);
        
        expect(arr1).toEqual(arr2);
    });
    
    test('choice is reproducible with seed', () => {
        __py.random.seed(42);
        const items = ['a', 'b', 'c', 'd', 'e'];
        const first = [
            __py.random.choice(items),
            __py.random.choice(items),
            __py.random.choice(items),
        ];
        
        __py.random.seed(42);
        const second = [
            __py.random.choice(items),
            __py.random.choice(items),
            __py.random.choice(items),
        ];
        
        expect(first).toEqual(second);
    });
    
    test('sample is reproducible with seed', () => {
        __py.random.seed(42);
        const items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
        const first = __py.random.sample(items, 5);
        
        __py.random.seed(42);
        const second = __py.random.sample(items, 5);
        
        expect(first).toEqual(second);
    });
    
    test('getstate/setstate preserves sequence', () => {
        __py.random.seed(42);
        __py.random.random();  // Advance state
        __py.random.random();
        
        const state = __py.random.getstate();
        const next1 = __py.random.random();
        const next2 = __py.random.random();
        
        __py.random.setstate(state);
        expect(__py.random.random()).toBe(next1);
        expect(__py.random.random()).toBe(next2);
    });
});

// =============================================================================
// RE.MATCH() TESTS - Group Positions
// =============================================================================

describe('re.match() risk areas - group positions', () => {
    test('start() returns correct position', () => {
        const m = __py.re.match('(\\d+)', '123abc');
        expect(m.start()).toBe(0);
        expect(m.start(0)).toBe(0);
    });
    
    test('end() returns correct position', () => {
        const m = __py.re.match('(\\d+)', '123abc');
        expect(m.end()).toBe(3);
        expect(m.end(0)).toBe(3);
    });
    
    test('span() returns [start, end]', () => {
        const m = __py.re.match('(\\d+)', '123abc');
        expect(m.span()).toEqual([0, 3]);
    });
    
    test('group(1) returns first capture', () => {
        const m = __py.re.match('(\\d+)(\\w+)', '123abc');
        expect(m.group(1)).toBe('123');
        expect(m.group(2)).toBe('abc');
    });
    
    test('groups() returns all captures', () => {
        const m = __py.re.match('(\\d+)(\\w+)', '123abc');
        expect(m.groups()).toEqual(['123', 'abc']);
    });
    
    test('search finds match anywhere', () => {
        const m = __py.re.search('(\\d+)', 'abc123def');
        expect(m.group()).toBe('123');
        expect(m.start()).toBe(3);
        expect(m.end()).toBe(6);
    });
    
    test('match anchors at start', () => {
        expect(__py.re.match('\\d+', 'abc123')).toBeNull();
        expect(__py.re.match('\\d+', '123abc')).not.toBeNull();
    });
});

// =============================================================================
// MATH MODULE TESTS - Constants and Functions
// =============================================================================

describe('math module risk areas', () => {
    test('math.pi is correct', () => {
        expect(__py.math.pi).toBeCloseTo(3.14159265, 5);
    });
    
    test('math.e is correct', () => {
        expect(__py.math.e).toBeCloseTo(2.71828182, 5);
    });
    
    test('math.tau is 2*pi', () => {
        expect(__py.math.tau).toBeCloseTo(6.28318530, 5);
    });
    
    test('math.inf is Infinity', () => {
        expect(__py.math.inf).toBe(Infinity);
    });
    
    test('math.nan is NaN', () => {
        expect(Number.isNaN(__py.math.nan)).toBe(true);
    });
    
    test('math.log with base', () => {
        expect(__py.math.log(8, 2)).toBeCloseTo(3, 10);
        expect(__py.math.log(100, 10)).toBeCloseTo(2, 10);
    });
    
    test('math.factorial', () => {
        expect(__py.math.factorial(5)).toBe(120);
        expect(__py.math.factorial(0)).toBe(1);
    });
    
    test('math.gcd', () => {
        expect(__py.math.gcd(48, 18)).toBe(6);
    });
    
    test('math.isnan', () => {
        expect(__py.math.isnan(NaN)).toBe(true);
        expect(__py.math.isnan(1)).toBe(false);
    });
    
    test('math.isinf', () => {
        expect(__py.math.isinf(Infinity)).toBe(true);
        expect(__py.math.isinf(-Infinity)).toBe(true);
        expect(__py.math.isinf(1)).toBe(false);
    });
});

// =============================================================================
// JSON MODULE TESTS - sort_keys
// =============================================================================

describe('json module risk areas', () => {
    test('json.dumps with sort_keys', () => {
        const obj = { b: 2, a: 1, c: 3 };
        const result = __py.json.dumps(obj, null, true);
        expect(result).toBe('{"a":1,"b":2,"c":3}');
    });
    
    test('json.dumps with indent', () => {
        const obj = { a: 1 };
        const result = __py.json.dumps(obj, 2, false);
        expect(result).toContain('\n');
    });
    
    test('json.loads parses correctly', () => {
        const result = __py.json.loads('{"a": 1, "b": [1, 2, 3]}');
        expect(result).toEqual({ a: 1, b: [1, 2, 3] });
    });
});

// =============================================================================
// LEN() TESTS - Various types
// =============================================================================

describe('len() risk areas', () => {
    test('len(dict) returns key count', () => {
        expect(__py.len({ a: 1, b: 2, c: 3 })).toBe(3);
    });
    
    test('len(Set) returns size', () => {
        expect(__py.len(new Set([1, 2, 3]))).toBe(3);
    });
    
    test('len(Map) returns size', () => {
        const m = new Map([['a', 1], ['b', 2]]);
        expect(__py.len(m)).toBe(2);
    });
    
    test('len(null) throws TypeError', () => {
        expect(() => __py.len(null)).toThrow(TypeError);
    });
    
    test('len(string) returns character count', () => {
        expect(__py.len('hello')).toBe(5);
    });
    
    test('len(array) returns element count', () => {
        expect(__py.len([1, 2, 3])).toBe(3);
    });
});

// =============================================================================
// POW() TESTS - 3-argument modular exponentiation
// =============================================================================

describe('pow() risk areas', () => {
    test('pow(2, 10) = 1024', () => {
        expect(__py.pow(2, 10)).toBe(1024);
    });
    
    test('pow(2, 10, 100) = 24 (modular)', () => {
        expect(__py.pow(2, 10, 100)).toBe(24);
    });
    
    test('pow(7, 13, 5) = 2', () => {
        expect(__py.pow(7, 13, 5)).toBe(2);
    });
    
    test('pow handles large modular exponentiation', () => {
        // 2^1000 mod 17 = 1 (by Fermat's little theorem, 2^16 ≡ 1 mod 17)
        expect(__py.pow(2, 1000, 17)).toBe(1);
    });
});

// =============================================================================
// DIVMOD() TESTS
// =============================================================================

describe('divmod() risk areas', () => {
    test('divmod(7, 3) = [2, 1]', () => {
        expect(__py.divmod(7, 3)).toEqual([2, 1]);
    });
    
    test('divmod(-7, 3) = [-3, 2] (Python semantics)', () => {
        expect(__py.divmod(-7, 3)).toEqual([-3, 2]);
    });
    
    test('divmod(7, -3) = [-3, -2]', () => {
        expect(__py.divmod(7, -3)).toEqual([-3, -2]);
    });
});

// =============================================================================
// MAP() TESTS - Multiple iterables
// =============================================================================

describe('map() risk areas', () => {
    test('map with single iterable', () => {
        expect(__py.map(x => x * 2, [1, 2, 3])).toEqual([2, 4, 6]);
    });
    
    test('map with multiple iterables', () => {
        expect(__py.map((a, b) => a + b, [1, 2, 3], [10, 20, 30])).toEqual([11, 22, 33]);
    });
    
    test('map stops at shortest iterable', () => {
        expect(__py.map((a, b) => a + b, [1, 2, 3], [10, 20])).toEqual([11, 22]);
    });
});

// Reset random state after all tests
afterAll(() => {
    __py.random.seed(null);
});
