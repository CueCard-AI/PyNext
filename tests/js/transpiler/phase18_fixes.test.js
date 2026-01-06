/**
 * Comprehensive JavaScript runtime tests for Phase 18 transpiler fixes.
 * 
 * Tests all fundamental fixes to the JavaScript runtime, particularly:
 * 1. Error types matching Python (ValueError, IndexError, KeyError, etc.)
 * 2. Runtime helper correctness
 * 3. Edge cases in arithmetic operators
 * 
 * Author: PyNext Team
 * Phase: 18.8 - Edge Cases, Classes & Polish
 */

const __py = require('./setup');


// =============================================================================
// ERROR HANDLING TESTS
// =============================================================================

describe('Error Handling - Python Exception Semantics', () => {
    describe('list.remove() error', () => {
        test('throws when item not in list', () => {
            const arr = [1, 2, 3];
            expect(() => __py.list.remove(arr, 5)).toThrow();
        });
        
        test('error message mentions ValueError', () => {
            const arr = [1, 2, 3];
            expect(() => __py.list.remove(arr, 5)).toThrow(/list.remove|ValueError/);
        });
        
        test('removes item when found', () => {
            const arr = [1, 2, 3];
            __py.list.remove(arr, 2);
            expect(arr).toEqual([1, 3]);
        });
    });
    
    describe('list.index() error', () => {
        test('throws when item not in list', () => {
            const arr = [1, 2, 3];
            expect(() => __py.list.index(arr, 5)).toThrow();
        });
        
        test('returns index when found', () => {
            const arr = [1, 2, 3];
            expect(__py.list.index(arr, 2)).toBe(1);
        });
    });
    
    describe('list.pop() error', () => {
        test('throws on empty list', () => {
            const arr = [];
            expect(() => __py.list.pop(arr)).toThrow();
        });
        
        test('throws on out of range', () => {
            const arr = [1, 2, 3];
            expect(() => __py.list.pop(arr, 10)).toThrow();
        });
        
        test('pops from end by default', () => {
            const arr = [1, 2, 3];
            expect(__py.list.pop(arr)).toBe(3);
            expect(arr).toEqual([1, 2]);
        });
        
        test('supports negative indices', () => {
            const arr = [1, 2, 3];
            expect(__py.list.pop(arr, -2)).toBe(2);
            expect(arr).toEqual([1, 3]);
        });
    });
    
    describe('list.sort() type error', () => {
        test('throws TypeError on mixed types', () => {
            const arr = [1, 'a'];
            expect(() => __py.list.sort(arr)).toThrow(TypeError);
        });
        
        test('sorts numbers numerically', () => {
            const arr = [3, 1, 4, 1, 5];
            __py.list.sort(arr);
            expect(arr).toEqual([1, 1, 3, 4, 5]);
        });
        
        test('supports key function', () => {
            const arr = ['bb', 'a', 'ccc'];
            __py.list.sort(arr, x => x.length);
            expect(arr).toEqual(['a', 'bb', 'ccc']);
        });
        
        test('supports reverse', () => {
            const arr = [1, 2, 3];
            __py.list.sort(arr, null, true);
            expect(arr).toEqual([3, 2, 1]);
        });
    });
    
    describe('dict.pop() error', () => {
        test('throws KeyError when key not found', () => {
            const d = { a: 1 };
            expect(() => __py.dict.pop(d, 'b')).toThrow(/KeyError/);
        });
        
        test('returns default when provided', () => {
            const d = { a: 1 };
            expect(__py.dict.pop(d, 'b', 'default')).toBe('default');
        });
        
        test('pops and returns value when key exists', () => {
            const d = { a: 1, b: 2 };
            expect(__py.dict.pop(d, 'a')).toBe(1);
            expect(d).toEqual({ b: 2 });
        });
    });
    
    describe('dict.popitem() error', () => {
        test('throws on empty dict', () => {
            const d = {};
            expect(() => __py.dict.popitem(d)).toThrow();
        });
        
        test('pops last inserted item', () => {
            const d = { a: 1, b: 2 };
            const [key, value] = __py.dict.popitem(d);
            expect(key).toBe('b');
            expect(value).toBe(2);
        });
    });
    
    describe('set.remove() error', () => {
        test('throws KeyError when element not in set', () => {
            const s = new Set([1, 2, 3]);
            expect(() => __py.set.remove(s, 4)).toThrow(/KeyError/);
        });
        
        test('removes element when present', () => {
            const s = new Set([1, 2, 3]);
            __py.set.remove(s, 2);
            expect(s.has(2)).toBe(false);
        });
    });
    
    describe('set.pop() error', () => {
        test('throws on empty set', () => {
            const s = new Set();
            expect(() => __py.set.pop(s)).toThrow();
        });
        
        test('pops and returns an element', () => {
            const s = new Set([1, 2, 3]);
            const elem = __py.set.pop(s);
            expect([1, 2, 3]).toContain(elem);
            expect(s.size).toBe(2);
        });
    });
});


// =============================================================================
// BUILTINS ERROR HANDLING
// =============================================================================

describe('Builtins Error Handling', () => {
    describe('sorted() type error', () => {
        test('throws TypeError on mixed types', () => {
            expect(() => __py.sorted([1, 'a'])).toThrow(TypeError);
        });
        
        test('sorts numerically', () => {
            expect(__py.sorted([3, 1, 2])).toEqual([1, 2, 3]);
        });
    });
    
    describe('min() errors', () => {
        test('throws on empty sequence', () => {
            expect(() => __py.min([])).toThrow();
        });
        
        test('throws TypeError on mixed types', () => {
            expect(() => __py.min([1, 'a'])).toThrow(TypeError);
        });
        
        test('returns minimum value', () => {
            expect(__py.min([3, 1, 2])).toBe(1);
        });
    });
    
    describe('max() errors', () => {
        test('throws on empty sequence', () => {
            expect(() => __py.max([])).toThrow();
        });
        
        test('returns maximum value', () => {
            expect(__py.max([3, 1, 2])).toBe(3);
        });
    });
    
    describe('len() type error', () => {
        test('throws TypeError for None/null', () => {
            expect(() => __py.len(null)).toThrow(TypeError);
        });
        
        test('throws TypeError for unsupported types', () => {
            expect(() => __py.len(42)).toThrow(TypeError);
        });
        
        test('returns length for arrays', () => {
            expect(__py.len([1, 2, 3])).toBe(3);
        });
        
        test('returns length for strings', () => {
            expect(__py.len('hello')).toBe(5);
        });
    });
    
    describe('range() error', () => {
        test('throws on zero step', () => {
            expect(() => __py.range(0, 10, 0)).toThrow();
        });
        
        test('generates range correctly', () => {
            expect(__py.range(5)).toEqual([0, 1, 2, 3, 4]);
            expect(__py.range(1, 5)).toEqual([1, 2, 3, 4]);
            expect(__py.range(0, 10, 2)).toEqual([0, 2, 4, 6, 8]);
        });
    });
});


// =============================================================================
// CORE RUNTIME FUNCTIONALITY
// =============================================================================

describe('Core Runtime Functionality', () => {
    describe('at() - negative indexing', () => {
        test('handles negative indices', () => {
            const arr = [1, 2, 3, 4, 5];
            expect(__py.at(arr, -1)).toBe(5);
            expect(__py.at(arr, -2)).toBe(4);
        });
        
        test('handles positive indices', () => {
            const arr = [1, 2, 3];
            expect(__py.at(arr, 0)).toBe(1);
            expect(__py.at(arr, 1)).toBe(2);
        });
        
        test('works with strings', () => {
            expect(__py.at('hello', -1)).toBe('o');
            expect(__py.at('hello', 0)).toBe('h');
        });
    });
    
    describe('slice()', () => {
        test('handles basic slicing', () => {
            const arr = [0, 1, 2, 3, 4];
            expect(__py.slice(arr, 1, 3)).toEqual([1, 2]);
        });
        
        test('handles negative indices', () => {
            const arr = [0, 1, 2, 3, 4];
            expect(__py.slice(arr, null, -1)).toEqual([0, 1, 2, 3]);
        });
        
        test('handles step', () => {
            const arr = [0, 1, 2, 3, 4];
            expect(__py.slice(arr, null, null, 2)).toEqual([0, 2, 4]);
        });
        
        test('handles reverse step', () => {
            const arr = [0, 1, 2, 3, 4];
            expect(__py.slice(arr, null, null, -1)).toEqual([4, 3, 2, 1, 0]);
        });
    });
    
    describe('bool() - Python truthiness', () => {
        test('returns false for empty arrays', () => {
            expect(__py.bool([])).toBe(false);
        });
        
        test('returns false for empty objects', () => {
            expect(__py.bool({})).toBe(false);
        });
        
        test('returns false for zero', () => {
            expect(__py.bool(0)).toBe(false);
        });
        
        test('returns false for empty string', () => {
            expect(__py.bool('')).toBe(false);
        });
        
        test('returns true for non-empty arrays', () => {
            expect(__py.bool([1])).toBe(true);
        });
        
        test('returns true for non-empty objects', () => {
            expect(__py.bool({ a: 1 })).toBe(true);
        });
        
        test('returns true for non-zero numbers', () => {
            expect(__py.bool(1)).toBe(true);
            expect(__py.bool(-1)).toBe(true);
        });
        
        test('returns false for NaN', () => {
            expect(__py.bool(NaN)).toBe(false);
        });
    });
    
    describe('eq() - deep equality', () => {
        test('compares primitives', () => {
            expect(__py.eq(1, 1)).toBe(true);
            expect(__py.eq(1, 2)).toBe(false);
            expect(__py.eq('a', 'a')).toBe(true);
        });
        
        test('compares arrays deeply', () => {
            expect(__py.eq([1, 2], [1, 2])).toBe(true);
            expect(__py.eq([1, 2], [1, 3])).toBe(false);
        });
        
        test('compares nested arrays', () => {
            expect(__py.eq([[1, 2], [3, 4]], [[1, 2], [3, 4]])).toBe(true);
            expect(__py.eq([[1, 2], [3, 4]], [[1, 2], [3, 5]])).toBe(false);
        });
        
        test('compares objects deeply', () => {
            expect(__py.eq({ a: 1 }, { a: 1 })).toBe(true);
            expect(__py.eq({ a: 1 }, { a: 2 })).toBe(false);
        });
        
        test('handles null and undefined', () => {
            expect(__py.eq(null, null)).toBe(true);
            expect(__py.eq(undefined, undefined)).toBe(true);
            expect(__py.eq(null, undefined)).toBe(false);
        });
    });
    
    describe('mod() - Python modulo', () => {
        test('matches Python semantics for negative numbers', () => {
            expect(__py.mod(-7, 3)).toBe(2);  // Python: -7 % 3 = 2
            expect(__py.mod(7, -3)).toBe(-2); // Python: 7 % -3 = -2
        });
        
        test('normalizes -0 to 0', () => {
            expect(__py.mod(0, 5)).toBe(0);
            expect(Object.is(__py.mod(0, 5), 0)).toBe(true);  // Not -0
        });
        
        test('handles positive modulo', () => {
            expect(__py.mod(7, 3)).toBe(1);
            expect(__py.mod(10, 4)).toBe(2);
        });
    });
    
    describe('floordiv() - floor division', () => {
        test('floors toward negative infinity', () => {
            expect(__py.floordiv(7, 3)).toBe(2);
            expect(__py.floordiv(-7, 3)).toBe(-3);  // Floor toward -∞
            expect(__py.floordiv(7, -3)).toBe(-3);
        });
    });
    
    describe('add() - polymorphic addition', () => {
        test('adds numbers', () => {
            expect(__py.add(1, 2)).toBe(3);
        });
        
        test('concatenates strings', () => {
            expect(__py.add('hello', ' world')).toBe('hello world');
        });
        
        test('concatenates arrays', () => {
            expect(__py.add([1, 2], [3, 4])).toEqual([1, 2, 3, 4]);
        });
    });
    
    describe('mul() - polymorphic multiplication', () => {
        test('multiplies numbers', () => {
            expect(__py.mul(3, 4)).toBe(12);
        });
        
        test('repeats strings', () => {
            expect(__py.mul('ab', 3)).toBe('ababab');
            expect(__py.mul(3, 'ab')).toBe('ababab');
        });
        
        test('repeats arrays', () => {
            expect(__py.mul([1, 2], 3)).toEqual([1, 2, 1, 2, 1, 2]);
        });
        
        test('handles zero/negative repetition', () => {
            expect(__py.mul('ab', 0)).toBe('');
            expect(__py.mul('ab', -1)).toBe('');
            expect(__py.mul([1, 2], 0)).toEqual([]);
        });
    });
    
    describe('isinstance()', () => {
        test('checks string type', () => {
            expect(__py.isinstance('hello', 'str')).toBe(true);
            expect(__py.isinstance(123, 'str')).toBe(false);
        });
        
        test('checks number types', () => {
            expect(__py.isinstance(5, 'int')).toBe(true);
            expect(__py.isinstance(5.5, 'float')).toBe(true);
        });
        
        test('checks array type', () => {
            expect(__py.isinstance([1, 2], 'list')).toBe(true);
            expect(__py.isinstance({}, 'list')).toBe(false);
        });
        
        test('checks tuple of types', () => {
            expect(__py.isinstance('hello', ['str', 'int'])).toBe(true);
            expect(__py.isinstance(5, ['str', 'int'])).toBe(true);
            expect(__py.isinstance([], ['str', 'int'])).toBe(false);
        });
    });
    
    describe('type()', () => {
        test('returns correct type names', () => {
            expect(__py.type(null)).toBe('NoneType');
            expect(__py.type([1, 2])).toBe('list');
            expect(__py.type('hello')).toBe('str');
            expect(__py.type(5)).toBe('int');
            expect(__py.type(5.5)).toBe('float');
            expect(__py.type(true)).toBe('bool');
            expect(__py.type({ a: 1 })).toBe('dict');
        });
    });
});


// =============================================================================
// ITERATION HELPERS
// =============================================================================

describe('Iteration Helpers', () => {
    describe('enumerate()', () => {
        test('enumerates from 0 by default', () => {
            expect(__py.enumerate(['a', 'b', 'c'])).toEqual([[0, 'a'], [1, 'b'], [2, 'c']]);
        });
        
        test('supports custom start', () => {
            expect(__py.enumerate(['a', 'b'], 1)).toEqual([[1, 'a'], [2, 'b']]);
        });
    });
    
    describe('zip()', () => {
        test('zips arrays of equal length', () => {
            expect(__py.zip([1, 2], ['a', 'b'])).toEqual([[1, 'a'], [2, 'b']]);
        });
        
        test('stops at shortest array', () => {
            expect(__py.zip([1, 2, 3], ['a', 'b'])).toEqual([[1, 'a'], [2, 'b']]);
        });
        
        test('handles multiple arrays', () => {
            expect(__py.zip([1, 2], ['a', 'b'], [true, false])).toEqual([[1, 'a', true], [2, 'b', false]]);
        });
    });
    
    describe('iter()', () => {
        test('returns array as-is', () => {
            expect(__py.iter([1, 2, 3])).toEqual([1, 2, 3]);
        });
        
        test('converts string to array of chars', () => {
            expect(__py.iter('abc')).toEqual(['a', 'b', 'c']);
        });
        
        test('returns object keys for dicts', () => {
            expect(__py.iter({ a: 1, b: 2 })).toEqual(['a', 'b']);
        });
        
        test('handles null/undefined', () => {
            expect(__py.iter(null)).toEqual([]);
            expect(__py.iter(undefined)).toEqual([]);
        });
    });
    
    describe('sum()', () => {
        test('sums numbers', () => {
            expect(__py.sum([1, 2, 3])).toBe(6);
        });
        
        test('supports start value', () => {
            expect(__py.sum([1, 2, 3], 10)).toBe(16);
        });
    });
});


// =============================================================================
// STRING METHODS
// =============================================================================

describe('String Methods', () => {
    describe('str.split()', () => {
        test('splits by whitespace when no separator', () => {
            expect(__py.str.split('a b c')).toEqual(['a', 'b', 'c']);
        });
        
        test('splits by separator', () => {
            expect(__py.str.split('a,b,c', ',')).toEqual(['a', 'b', 'c']);
        });
        
        test('supports maxsplit', () => {
            expect(__py.str.split('a,b,c,d', ',', 2)).toEqual(['a', 'b', 'c,d']);
        });
        
        test('handles empty string', () => {
            expect(__py.str.split('')).toEqual([]);
        });
    });
    
    describe('str.title()', () => {
        test('titlecases string', () => {
            expect(__py.str.title('hello world')).toBe('Hello World');
        });
    });
    
    describe('str.center()', () => {
        test('centers string', () => {
            expect(__py.str.center('abc', 7)).toBe('  abc  ');
        });
        
        test('supports custom fill char', () => {
            expect(__py.str.center('abc', 7, '-')).toBe('--abc--');
        });
    });
});


// =============================================================================
// REPR AND ASCII
// =============================================================================

describe('repr() and ascii()', () => {
    describe('repr()', () => {
        test('represents None', () => {
            expect(__py.repr(null)).toBe('None');
        });
        
        test('represents strings with quotes', () => {
            expect(__py.repr('hello')).toBe("'hello'");
        });
        
        test('represents booleans', () => {
            expect(__py.repr(true)).toBe('True');
            expect(__py.repr(false)).toBe('False');
        });
        
        test('represents arrays', () => {
            expect(__py.repr([1, 2, 3])).toBe('[1, 2, 3]');
        });
        
        test('represents objects', () => {
            expect(__py.repr({ a: 1 })).toBe("{'a': 1}");
        });
    });
    
    describe('ascii()', () => {
        test('escapes non-ASCII characters', () => {
            expect(__py.ascii('café')).toBe("'caf\\xe9'");
        });
    });
});


// =============================================================================
// FORMAT TESTS
// =============================================================================

describe('format()', () => {
    test('formats floats with precision', () => {
        expect(__py.format(3.14159, '.2f')).toBe('3.14');
        expect(__py.format(3.14159, '.0f')).toBe('3');
    });
    
    test('formats integers', () => {
        expect(__py.format(42, 'd')).toBe('42');
    });
    
    test('formats hex', () => {
        expect(__py.format(255, 'x')).toBe('ff');
        expect(__py.format(255, 'X')).toBe('FF');
    });
    
    test('formats binary', () => {
        expect(__py.format(5, 'b')).toBe('101');
    });
    
    test('formats with alignment', () => {
        expect(__py.format('abc', '>10')).toBe('       abc');
        expect(__py.format('abc', '<10')).toBe('abc       ');
        expect(__py.format('abc', '^10')).toBe('   abc    ');
    });
    
    test('formats percentages', () => {
        expect(__py.format(0.5, '.0%')).toBe('50%');
        expect(__py.format(0.125, '.1%')).toBe('12.5%');
    });
});


// =============================================================================
// INTEGRATION TESTS
// =============================================================================

describe('Integration Tests', () => {
    test('chained operations maintain Python semantics', () => {
        const items = [1, 2, 3];
        
        // Python: items[-1]
        expect(__py.at(items, -1)).toBe(3);
        
        // Python: items[1:3]
        expect(__py.slice(items, 1, 3)).toEqual([2, 3]);
        
        // Python: if items:
        expect(__py.bool(items)).toBe(true);
        expect(__py.bool([])).toBe(false);
    });
    
    test('nested operations work correctly', () => {
        const matrix = [[1, 2], [3, 4], [5, 6]];
        
        // Python: matrix[-1][-1]
        expect(__py.at(__py.at(matrix, -1), -1)).toBe(6);
        
        // Python: matrix[0] + matrix[1]
        expect(__py.add(matrix[0], matrix[1])).toEqual([1, 2, 3, 4]);
    });
    
    test('any() and all() with Python truthiness', () => {
        expect(__py.any([0, '', [], 1])).toBe(true);
        expect(__py.any([0, '', []])).toBe(false);
        
        expect(__py.all([1, 'a', [1]])).toBe(true);
        expect(__py.all([1, '', [1]])).toBe(false);
    });
    
    test('filter with None uses Python truthiness', () => {
        expect(__py.filter(null, [0, 1, '', 'a', [], [1]])).toEqual([1, 'a', [1]]);
    });
});
