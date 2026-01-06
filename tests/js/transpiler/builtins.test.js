/**
 * Phase 18.4: JavaScript Runtime Tests for Builtins
 * 
 * Tests verify the __py.* functions behave identically to Python.
 */

const __py = require('./setup');

// =============================================================================
// SORTED() TESTS
// =============================================================================

describe('__py.sorted()', () => {
    test('basic numeric sort', () => {
        expect(__py.sorted([3, 1, 2])).toEqual([1, 2, 3]);
    });
    
    test('string sort', () => {
        expect(__py.sorted(['c', 'a', 'b'])).toEqual(['a', 'b', 'c']);
    });
    
    test('with key function', () => {
        const items = ['bb', 'a', 'ccc'];
        expect(__py.sorted(items, x => x.length)).toEqual(['a', 'bb', 'ccc']);
    });
    
    test('with reverse', () => {
        expect(__py.sorted([1, 2, 3], null, true)).toEqual([3, 2, 1]);
    });
    
    test('with key and reverse', () => {
        const items = ['a', 'bb', 'ccc'];
        expect(__py.sorted(items, x => x.length, true)).toEqual(['ccc', 'bb', 'a']);
    });
    
    test('empty array', () => {
        expect(__py.sorted([])).toEqual([]);
    });
    
    test('single element', () => {
        expect(__py.sorted([42])).toEqual([42]);
    });
    
    test('does not mutate original', () => {
        const original = [3, 1, 2];
        __py.sorted(original);
        expect(original).toEqual([3, 1, 2]);
    });
});

// =============================================================================
// MIN() / MAX() TESTS
// =============================================================================

describe('__py.min()', () => {
    test('basic iterable', () => {
        expect(__py.min([3, 1, 2])).toBe(1);
    });
    
    test('with key function', () => {
        const items = [{x: 3}, {x: 1}, {x: 2}];
        expect(__py.min(items, o => o.x)).toEqual({x: 1});
    });
    
    test('strings', () => {
        expect(__py.min(['c', 'a', 'b'])).toBe('a');
    });
    
    test('with string key', () => {
        const items = ['ccc', 'a', 'bb'];
        expect(__py.min(items, s => s.length)).toBe('a');
    });
    
    test('throws on empty', () => {
        expect(() => __py.min([])).toThrow('empty sequence');
    });
    
    test('single element', () => {
        expect(__py.min([42])).toBe(42);
    });
});

describe('__py.max()', () => {
    test('basic iterable', () => {
        expect(__py.max([3, 1, 2])).toBe(3);
    });
    
    test('with key function', () => {
        const items = [{x: 3}, {x: 1}, {x: 2}];
        expect(__py.max(items, o => o.x)).toEqual({x: 3});
    });
    
    test('strings', () => {
        expect(__py.max(['c', 'a', 'b'])).toBe('c');
    });
    
    test('throws on empty', () => {
        expect(() => __py.max([])).toThrow('empty sequence');
    });
});

// =============================================================================
// ANY() / ALL() TESTS
// =============================================================================

describe('__py.any()', () => {
    test('returns true if any truthy', () => {
        expect(__py.any([0, '', 1])).toBe(true);
    });
    
    test('returns false if all falsy', () => {
        expect(__py.any([0, '', null, [], {}])).toBe(false);
    });
    
    test('empty array returns false', () => {
        expect(__py.any([])).toBe(false);
    });
    
    test('uses Python truthiness - empty list falsy', () => {
        expect(__py.any([[], {}, 1])).toBe(true);
    });
    
    test('uses Python truthiness - all empty', () => {
        expect(__py.any([[], {}])).toBe(false);
    });
});

describe('__py.all()', () => {
    test('returns true if all truthy', () => {
        expect(__py.all([1, 'a', [1], {a: 1}])).toBe(true);
    });
    
    test('returns false if any falsy', () => {
        expect(__py.all([1, 0, 1])).toBe(false);
    });
    
    test('empty array returns true (vacuous truth)', () => {
        expect(__py.all([])).toBe(true);
    });
    
    test('uses Python truthiness - empty list falsy', () => {
        expect(__py.all([1, []])).toBe(false);
    });
});

// =============================================================================
// DIVMOD() TESTS
// =============================================================================

describe('__py.divmod()', () => {
    test('basic positive', () => {
        expect(__py.divmod(7, 3)).toEqual([2, 1]);
    });
    
    test('negative dividend (Python semantics)', () => {
        // Python: divmod(-7, 3) = (-3, 2)
        expect(__py.divmod(-7, 3)).toEqual([-3, 2]);
    });
    
    test('negative divisor', () => {
        // Python: divmod(7, -3) = (-3, -2)
        expect(__py.divmod(7, -3)).toEqual([-3, -2]);
    });
    
    test('both negative', () => {
        expect(__py.divmod(-7, -3)).toEqual([2, -1]);
    });
    
    test('exact division', () => {
        expect(__py.divmod(9, 3)).toEqual([3, 0]);
    });
    
    test('floats', () => {
        const [q, r] = __py.divmod(7.5, 2.5);
        expect(q).toBe(3);
        expect(r).toBeCloseTo(0, 10);
    });
});

// =============================================================================
// POW() TESTS
// =============================================================================

describe('__py.pow()', () => {
    test('basic power', () => {
        expect(__py.pow(2, 10)).toBe(1024);
    });
    
    test('with modulus', () => {
        expect(__py.pow(2, 10, 1000)).toBe(24);
    });
    
    test('zero exponent', () => {
        expect(__py.pow(5, 0)).toBe(1);
    });
    
    test('negative exponent', () => {
        expect(__py.pow(2, -1)).toBe(0.5);
    });
    
    test('modular exponentiation', () => {
        expect(__py.pow(3, 5, 7)).toBe(5);  // 243 % 7 = 5
    });
});

// =============================================================================
// CALLABLE() TESTS
// =============================================================================

describe('__py.callable()', () => {
    test('function is callable', () => {
        expect(__py.callable(() => {})).toBe(true);
    });
    
    test('number is not callable', () => {
        expect(__py.callable(42)).toBe(false);
    });
    
    test('string is not callable', () => {
        expect(__py.callable('hello')).toBe(false);
    });
    
    test('object is not callable', () => {
        expect(__py.callable({})).toBe(false);
    });
    
    test('array is not callable', () => {
        expect(__py.callable([])).toBe(false);
    });
});

// =============================================================================
// FILTER() TESTS
// =============================================================================

describe('__py.filter()', () => {
    test('with function', () => {
        expect(__py.filter(x => x > 0, [-1, 0, 1, 2])).toEqual([1, 2]);
    });
    
    test('with null uses Python truthiness', () => {
        expect(__py.filter(null, [0, 1, '', 'a', [], [1]])).toEqual([1, 'a', [1]]);
    });
    
    test('empty array', () => {
        expect(__py.filter(x => x, [])).toEqual([]);
    });
    
    test('all filtered out', () => {
        expect(__py.filter(x => x > 10, [1, 2, 3])).toEqual([]);
    });
});

// =============================================================================
// MAP() TESTS
// =============================================================================

describe('__py.map()', () => {
    test('basic map', () => {
        expect(__py.map(x => x * 2, [1, 2, 3])).toEqual([2, 4, 6]);
    });
    
    test('with multiple iterables', () => {
        expect(__py.map((a, b) => a + b, [1, 2, 3], [10, 20, 30])).toEqual([11, 22, 33]);
    });
    
    test('uneven lengths', () => {
        expect(__py.map((a, b) => a + b, [1, 2, 3], [10, 20])).toEqual([11, 22]);
    });
});

// =============================================================================
// REVERSED() TESTS
// =============================================================================

describe('__py.reversed()', () => {
    test('basic reverse', () => {
        expect(__py.reversed([1, 2, 3])).toEqual([3, 2, 1]);
    });
    
    test('string', () => {
        expect(__py.reversed('abc')).toEqual(['c', 'b', 'a']);
    });
    
    test('does not mutate original', () => {
        const original = [1, 2, 3];
        __py.reversed(original);
        expect(original).toEqual([1, 2, 3]);
    });
});

// =============================================================================
// ROUND() TESTS
// =============================================================================

describe('__py.round()', () => {
    test('basic round', () => {
        expect(__py.round(3.7)).toBe(4);
    });
    
    test('with digits', () => {
        expect(__py.round(3.14159, 2)).toBeCloseTo(3.14, 2);
    });
    
    test('negative digits', () => {
        expect(__py.round(1234, -2)).toBe(1200);
    });
    
    test('round half - banker\'s rounding', () => {
        // Python uses banker's rounding (round half to even)
        expect(__py.round(2.5)).toBe(2);  // 2.5 → 2 (even)
        expect(__py.round(3.5)).toBe(4);  // 3.5 → 4 (even)
    });
});

// =============================================================================
// LEN() TESTS
// =============================================================================

describe('__py.len()', () => {
    test('array', () => {
        expect(__py.len([1, 2, 3])).toBe(3);
    });
    
    test('string', () => {
        expect(__py.len('hello')).toBe(5);
    });
    
    test('object (dict)', () => {
        expect(__py.len({a: 1, b: 2})).toBe(2);
    });
    
    test('Set', () => {
        expect(__py.len(new Set([1, 2, 3]))).toBe(3);
    });
    
    test('Map', () => {
        expect(__py.len(new Map([['a', 1], ['b', 2]]))).toBe(2);
    });
    
    test('empty', () => {
        expect(__py.len([])).toBe(0);
    });
    
    test('throws on null', () => {
        expect(() => __py.len(null)).toThrow();
    });
});

// =============================================================================
// SUM() TESTS
// =============================================================================

describe('__py.sum()', () => {
    test('basic sum', () => {
        expect(__py.sum([1, 2, 3])).toBe(6);
    });
    
    test('with start', () => {
        expect(__py.sum([1, 2, 3], 10)).toBe(16);
    });
    
    test('empty array', () => {
        expect(__py.sum([])).toBe(0);
    });
    
    test('empty with start', () => {
        expect(__py.sum([], 100)).toBe(100);
    });
    
    test('negative numbers', () => {
        expect(__py.sum([-1, -2, -3])).toBe(-6);
    });
});

// =============================================================================
// ZIP() TESTS
// =============================================================================

describe('__py.zip()', () => {
    test('two arrays', () => {
        expect(__py.zip([1, 2], ['a', 'b'])).toEqual([[1, 'a'], [2, 'b']]);
    });
    
    test('three arrays', () => {
        expect(__py.zip([1], ['a'], [true])).toEqual([[1, 'a', true]]);
    });
    
    test('uneven lengths', () => {
        expect(__py.zip([1, 2, 3], ['a', 'b'])).toEqual([[1, 'a'], [2, 'b']]);
    });
    
    test('empty', () => {
        expect(__py.zip()).toEqual([]);
    });
});

// =============================================================================
// ENUMERATE() TESTS
// =============================================================================

describe('__py.enumerate()', () => {
    test('basic', () => {
        expect(__py.enumerate(['a', 'b', 'c'])).toEqual([[0, 'a'], [1, 'b'], [2, 'c']]);
    });
    
    test('with start', () => {
        expect(__py.enumerate(['a', 'b'], 1)).toEqual([[1, 'a'], [2, 'b']]);
    });
    
    test('empty', () => {
        expect(__py.enumerate([])).toEqual([]);
    });
});

// =============================================================================
// RANGE() TESTS
// =============================================================================

describe('__py.range()', () => {
    test('single arg', () => {
        expect(__py.range(5)).toEqual([0, 1, 2, 3, 4]);
    });
    
    test('two args', () => {
        expect(__py.range(1, 5)).toEqual([1, 2, 3, 4]);
    });
    
    test('with step', () => {
        expect(__py.range(0, 10, 2)).toEqual([0, 2, 4, 6, 8]);
    });
    
    test('negative step', () => {
        expect(__py.range(5, 0, -1)).toEqual([5, 4, 3, 2, 1]);
    });
    
    test('empty range', () => {
        expect(__py.range(5, 5)).toEqual([]);
    });
    
    test('zero step throws', () => {
        expect(() => __py.range(1, 10, 0)).toThrow();
    });
});

// =============================================================================
// STDLIB: JSON TESTS
// =============================================================================

describe('__py.json', () => {
    test('loads basic', () => {
        expect(__py.json.loads('{"a": 1}')).toEqual({a: 1});
    });
    
    test('loads array', () => {
        expect(__py.json.loads('[1, 2, 3]')).toEqual([1, 2, 3]);
    });
    
    test('dumps basic', () => {
        expect(__py.json.dumps({a: 1})).toBe('{"a":1}');
    });
    
    test('dumps with indent', () => {
        const result = __py.json.dumps({a: 1}, 2);
        expect(result).toContain('\n');
    });
    
    test('dumps with sort_keys', () => {
        const result = __py.json.dumps({b: 1, a: 2}, null, true);
        expect(result.indexOf('a')).toBeLessThan(result.indexOf('b'));
    });
});

// =============================================================================
// STDLIB: MATH TESTS
// =============================================================================

describe('__py.math', () => {
    test('pi constant', () => {
        expect(__py.math.pi).toBeCloseTo(3.14159, 4);
    });
    
    test('e constant', () => {
        expect(__py.math.e).toBeCloseTo(2.71828, 4);
    });
    
    test('sqrt', () => {
        expect(__py.math.sqrt(16)).toBe(4);
    });
    
    test('floor', () => {
        expect(__py.math.floor(3.7)).toBe(3);
    });
    
    test('ceil', () => {
        expect(__py.math.ceil(3.2)).toBe(4);
    });
    
    test('log natural', () => {
        expect(__py.math.log(__py.math.e)).toBeCloseTo(1, 10);
    });
    
    test('log with base', () => {
        expect(__py.math.log(100, 10)).toBeCloseTo(2, 10);
    });
    
    test('factorial', () => {
        expect(__py.math.factorial(5)).toBe(120);
    });
    
    test('gcd', () => {
        expect(__py.math.gcd(12, 8)).toBe(4);
    });
    
    test('lcm', () => {
        expect(__py.math.lcm(4, 6)).toBe(12);
    });
    
    test('isnan', () => {
        expect(__py.math.isnan(NaN)).toBe(true);
        expect(__py.math.isnan(42)).toBe(false);
    });
    
    test('isinf', () => {
        expect(__py.math.isinf(Infinity)).toBe(true);
        expect(__py.math.isinf(-Infinity)).toBe(true);
        expect(__py.math.isinf(42)).toBe(false);
    });
    
    test('degrees', () => {
        expect(__py.math.degrees(Math.PI)).toBeCloseTo(180, 10);
    });
    
    test('radians', () => {
        expect(__py.math.radians(180)).toBeCloseTo(Math.PI, 10);
    });
});

// =============================================================================
// STDLIB: RE TESTS
// =============================================================================

describe('__py.re', () => {
    test('match at start', () => {
        const m = __py.re.match('\\d+', '123abc');
        expect(m).not.toBeNull();
        expect(m.group()).toBe('123');
    });
    
    test('match fails if not at start', () => {
        const m = __py.re.match('\\d+', 'abc123');
        expect(m).toBeNull();
    });
    
    test('search anywhere', () => {
        const m = __py.re.search('\\d+', 'abc123def');
        expect(m).not.toBeNull();
        expect(m.group()).toBe('123');
    });
    
    test('findall', () => {
        expect(__py.re.findall('\\d+', 'a1b2c3')).toEqual(['1', '2', '3']);
    });
    
    test('sub all', () => {
        expect(__py.re.sub('\\d', 'X', 'a1b2c3')).toBe('aXbXcX');
    });
    
    test('sub with count', () => {
        expect(__py.re.sub('\\d', 'X', 'a1b2c3', 2)).toBe('aXbXc3');
    });
    
    test('split', () => {
        expect(__py.re.split('\\s+', 'a b  c')).toEqual(['a', 'b', 'c']);
    });
    
    test('escape', () => {
        expect(__py.re.escape('$100')).toBe('\\$100');
    });
    
    test('groups', () => {
        const m = __py.re.match('(\\d+)-(\\d+)', '123-456');
        expect(m.groups()).toEqual(['123', '456']);
    });
});

// =============================================================================
// STDLIB: RANDOM TESTS
// =============================================================================

describe('__py.random', () => {
    test('random returns 0-1', () => {
        const r = __py.random.random();
        expect(r).toBeGreaterThanOrEqual(0);
        expect(r).toBeLessThan(1);
    });
    
    test('randint inclusive', () => {
        for (let i = 0; i < 100; i++) {
            const r = __py.random.randint(1, 3);
            expect(r).toBeGreaterThanOrEqual(1);
            expect(r).toBeLessThanOrEqual(3);
            expect(Number.isInteger(r)).toBe(true);
        }
    });
    
    test('choice', () => {
        const items = [1, 2, 3];
        const r = __py.random.choice(items);
        expect(items).toContain(r);
    });
    
    test('choice empty throws', () => {
        expect(() => __py.random.choice([])).toThrow();
    });
    
    test('sample', () => {
        const items = [1, 2, 3, 4, 5];
        const s = __py.random.sample(items, 3);
        expect(s.length).toBe(3);
        expect(new Set(s).size).toBe(3);  // All unique
        s.forEach(x => expect(items).toContain(x));
    });
    
    test('sample too large throws', () => {
        expect(() => __py.random.sample([1, 2], 5)).toThrow();
    });
    
    test('shuffle in-place', () => {
        const arr = [1, 2, 3, 4, 5];
        const result = __py.random.shuffle(arr);
        expect(result).toBeUndefined();  // Returns None
        expect(arr.sort()).toEqual([1, 2, 3, 4, 5]);  // Same elements
    });
    
    test('uniform', () => {
        const r = __py.random.uniform(10, 20);
        expect(r).toBeGreaterThanOrEqual(10);
        expect(r).toBeLessThanOrEqual(20);
    });
    
    test('gauss returns number', () => {
        const r = __py.random.gauss(0, 1);
        expect(typeof r).toBe('number');
        expect(isNaN(r)).toBe(false);
    });
});
