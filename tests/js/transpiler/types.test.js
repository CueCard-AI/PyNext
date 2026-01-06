/**
 * Tests for Python Type Methods Runtime (Phase 18.3)
 * 
 * Tests the __py.str, __py.list, __py.dict, and __py.set runtime helpers.
 * These functions implement Python semantics in JavaScript.
 */

const __py = require('./setup');

// =============================================================================
// STRING METHODS
// =============================================================================

describe('__py.str.split()', () => {
    test('no args splits on whitespace', () => {
        expect(__py.str.split('a  b   c')).toEqual(['a', 'b', 'c']);
    });
    
    test('empty string returns empty array', () => {
        expect(__py.str.split('')).toEqual([]);
    });
    
    test('only whitespace returns empty array', () => {
        expect(__py.str.split('   ')).toEqual([]);
    });
    
    test('removes leading/trailing whitespace', () => {
        expect(__py.str.split('  a  ')).toEqual(['a']);
    });
    
    test('handles tabs and newlines', () => {
        expect(__py.str.split('a\tb\nc')).toEqual(['a', 'b', 'c']);
    });
    
    test('with separator uses JS split', () => {
        expect(__py.str.split('a,b,c', ',')).toEqual(['a', 'b', 'c']);
    });
    
    test('maxsplit limits splits', () => {
        expect(__py.str.split('a b c d', null, 2)).toEqual(['a', 'b', 'c d']);
    });
    
    test('empty string with separator returns [""]', () => {
        expect(__py.str.split('', ',')).toEqual(['']);
    });
    
    test('Python: "  hello  world  ".split()', () => {
        expect(__py.str.split('  hello  world  ')).toEqual(['hello', 'world']);
    });
});

describe('__py.str.rsplit()', () => {
    test('no maxsplit same as split', () => {
        expect(__py.str.rsplit('a,b,c', ',')).toEqual(['a', 'b', 'c']);
    });
    
    test('maxsplit splits from right', () => {
        expect(__py.str.rsplit('a,b,c,d', ',', 2)).toEqual(['a,b', 'c', 'd']);
    });
});

describe('__py.str.index()', () => {
    test('returns index when found', () => {
        expect(__py.str.index('hello', 'l')).toBe(2);
    });
    
    test('throws when not found', () => {
        expect(() => __py.str.index('hello', 'x')).toThrow('substring not found');
    });
    
    test('with start parameter', () => {
        expect(__py.str.index('hello', 'l', 3)).toBe(3);
    });
    
    test('empty substring found at start', () => {
        expect(__py.str.index('hello', '')).toBe(0);
    });
});

describe('__py.str.count()', () => {
    test('counts occurrences', () => {
        expect(__py.str.count('hello', 'l')).toBe(2);
    });
    
    test('empty substring returns length + 1', () => {
        expect(__py.str.count('hello', '')).toBe(6);
    });
    
    test('no matches returns 0', () => {
        expect(__py.str.count('hello', 'x')).toBe(0);
    });
});

describe('__py.str.title()', () => {
    test('basic title case', () => {
        expect(__py.str.title('hello world')).toBe('Hello World');
    });
    
    test('already titled', () => {
        expect(__py.str.title('Hello World')).toBe('Hello World');
    });
});

describe('__py.str.capitalize()', () => {
    test('basic capitalize', () => {
        expect(__py.str.capitalize('hello')).toBe('Hello');
    });
    
    test('lowers rest', () => {
        expect(__py.str.capitalize('HELLO')).toBe('Hello');
    });
    
    test('empty string', () => {
        expect(__py.str.capitalize('')).toBe('');
    });
});

describe('__py.str.swapcase()', () => {
    test('swaps case', () => {
        expect(__py.str.swapcase('Hello')).toBe('hELLO');
    });
});

describe('__py.str.center()', () => {
    test('centers string', () => {
        expect(__py.str.center('a', 5)).toBe('  a  ');
    });
    
    test('with fill character', () => {
        expect(__py.str.center('a', 5, '-')).toBe('--a--');
    });
    
    test('already wider', () => {
        expect(__py.str.center('hello', 3)).toBe('hello');
    });
});

describe('__py.str.ljust()', () => {
    test('left justifies', () => {
        expect(__py.str.ljust('a', 5)).toBe('a    ');
    });
});

describe('__py.str.rjust()', () => {
    test('right justifies', () => {
        expect(__py.str.rjust('a', 5)).toBe('    a');
    });
});

describe('__py.str.zfill()', () => {
    test('pads with zeros', () => {
        expect(__py.str.zfill('42', 5)).toBe('00042');
    });
    
    test('handles sign', () => {
        expect(__py.str.zfill('-42', 5)).toBe('-0042');
    });
});

describe('__py.str.strip()', () => {
    test('strips whitespace', () => {
        expect(__py.str.strip('  hello  ')).toBe('hello');
    });
    
    test('strips custom chars', () => {
        expect(__py.str.strip('xxhelloxx', 'x')).toBe('hello');
    });
});

describe('__py.str.replace()', () => {
    test('replaces all by default', () => {
        expect(__py.str.replace('aaa', 'a', 'b')).toBe('bbb');
    });
    
    test('with count limit', () => {
        expect(__py.str.replace('aaa', 'a', 'b', 2)).toBe('bba');
    });
});

describe('__py.str.partition()', () => {
    test('partitions on separator', () => {
        expect(__py.str.partition('a:b:c', ':')).toEqual(['a', ':', 'b:c']);
    });
    
    test('separator not found', () => {
        expect(__py.str.partition('abc', ':')).toEqual(['abc', '', '']);
    });
});

describe('__py.str.is* methods', () => {
    test('isdigit', () => {
        expect(__py.str.isdigit('123')).toBe(true);
        expect(__py.str.isdigit('12a')).toBe(false);
    });
    
    test('isalpha', () => {
        expect(__py.str.isalpha('abc')).toBe(true);
        expect(__py.str.isalpha('ab1')).toBe(false);
    });
    
    test('isalnum', () => {
        expect(__py.str.isalnum('abc123')).toBe(true);
        expect(__py.str.isalnum('abc!')).toBe(false);
    });
    
    test('isspace', () => {
        expect(__py.str.isspace('   ')).toBe(true);
        expect(__py.str.isspace(' a ')).toBe(false);
    });
    
    test('isupper', () => {
        expect(__py.str.isupper('ABC')).toBe(true);
        expect(__py.str.isupper('Abc')).toBe(false);
    });
    
    test('islower', () => {
        expect(__py.str.islower('abc')).toBe(true);
        expect(__py.str.islower('Abc')).toBe(false);
    });
});

// =============================================================================
// LIST METHODS
// =============================================================================

describe('__py.list.remove()', () => {
    test('removes first occurrence', () => {
        const arr = [1, 2, 3, 2];
        __py.list.remove(arr, 2);
        expect(arr).toEqual([1, 3, 2]);
    });
    
    test('uses deep equality', () => {
        const arr = [[1], [2], [3]];
        __py.list.remove(arr, [2]);
        expect(arr).toEqual([[1], [3]]);
    });
    
    test('throws when not found', () => {
        expect(() => __py.list.remove([1, 2], 3)).toThrow('x not in list');
    });
    
    test('removes null', () => {
        const arr = [1, null, 3];
        __py.list.remove(arr, null);
        expect(arr).toEqual([1, 3]);
    });
});

describe('__py.list.index()', () => {
    test('returns index when found', () => {
        expect(__py.list.index([1, 2, 3], 2)).toBe(1);
    });
    
    test('throws when not found', () => {
        expect(() => __py.list.index([1, 2], 3)).toThrow('x is not in list');
    });
    
    test('uses deep equality', () => {
        expect(__py.list.index([[1], [2]], [2])).toBe(1);
    });
    
    test('with start parameter', () => {
        expect(__py.list.index([1, 2, 1, 2], 2, 2)).toBe(3);
    });
});

describe('__py.list.count()', () => {
    test('counts occurrences', () => {
        expect(__py.list.count([1, 2, 1, 3, 1], 1)).toBe(3);
    });
    
    test('uses deep equality', () => {
        expect(__py.list.count([[1], [1], [2]], [1])).toBe(2);
    });
});

describe('__py.list.sort()', () => {
    test('sorts numerically by default', () => {
        const arr = [10, 2, 1];
        __py.list.sort(arr);
        expect(arr).toEqual([1, 2, 10]);
    });
    
    test('with reverse', () => {
        const arr = [1, 2, 3];
        __py.list.sort(arr, null, true);
        expect(arr).toEqual([3, 2, 1]);
    });
    
    test('with key function', () => {
        const arr = ['bb', 'a', 'ccc'];
        __py.list.sort(arr, s => s.length);
        expect(arr).toEqual(['a', 'bb', 'ccc']);
    });
});

describe('__py.list.pop()', () => {
    test('pops last by default', () => {
        const arr = [1, 2, 3];
        expect(__py.list.pop(arr)).toBe(3);
        expect(arr).toEqual([1, 2]);
    });
    
    test('pops at index', () => {
        const arr = [1, 2, 3];
        expect(__py.list.pop(arr, 0)).toBe(1);
        expect(arr).toEqual([2, 3]);
    });
    
    test('negative index', () => {
        const arr = [1, 2, 3];
        expect(__py.list.pop(arr, -2)).toBe(2);
    });
    
    test('throws on empty list', () => {
        expect(() => __py.list.pop([])).toThrow('pop from empty list');
    });
});

describe('__py.list.insert()', () => {
    test('inserts at index', () => {
        const arr = [1, 2, 3];
        __py.list.insert(arr, 1, 'x');
        expect(arr).toEqual([1, 'x', 2, 3]);
    });
    
    test('negative index', () => {
        const arr = [1, 2, 3];
        __py.list.insert(arr, -1, 'x');
        // Python: list.insert(-1, x) inserts BEFORE the last element
        expect(arr).toEqual([1, 2, 'x', 3]);
    });
});

// =============================================================================
// DICT METHODS
// =============================================================================

describe('__py.dict.get()', () => {
    test('returns value when exists', () => {
        expect(__py.dict.get({a: 1}, 'a')).toBe(1);
    });
    
    test('returns null when missing', () => {
        expect(__py.dict.get({a: 1}, 'b')).toBe(null);
    });
    
    test('returns default when missing', () => {
        expect(__py.dict.get({a: 1}, 'b', 0)).toBe(0);
    });
});

describe('__py.dict.pop()', () => {
    test('removes and returns value', () => {
        const d = {a: 1, b: 2};
        expect(__py.dict.pop(d, 'a')).toBe(1);
        expect(d).toEqual({b: 2});
    });
    
    test('throws when missing without default', () => {
        expect(() => __py.dict.pop({}, 'x')).toThrow("KeyError: 'x'");
    });
    
    test('returns default when missing', () => {
        expect(__py.dict.pop({}, 'x', 0)).toBe(0);
    });
});

describe('__py.dict.setdefault()', () => {
    test('returns existing value', () => {
        const d = {a: 1};
        expect(__py.dict.setdefault(d, 'a', 0)).toBe(1);
    });
    
    test('sets and returns default', () => {
        const d = {};
        expect(__py.dict.setdefault(d, 'a', 0)).toBe(0);
        expect(d).toEqual({a: 0});
    });
});

describe('__py.dict.popitem()', () => {
    test('pops last item', () => {
        const d = {a: 1, b: 2};
        const result = __py.dict.popitem(d);
        expect(result).toEqual(['b', 2]);
        expect(d).toEqual({a: 1});
    });
    
    test('throws on empty dict', () => {
        expect(() => __py.dict.popitem({})).toThrow('dictionary is empty');
    });
});

describe('__py.dict.update()', () => {
    test('updates with object', () => {
        const d = {a: 1};
        __py.dict.update(d, {b: 2});
        expect(d).toEqual({a: 1, b: 2});
    });
});

describe('__py.dict.clear()', () => {
    test('clears dict', () => {
        const d = {a: 1, b: 2};
        __py.dict.clear(d);
        expect(d).toEqual({});
    });
});

describe('__py.dict.copy()', () => {
    test('shallow copy', () => {
        const d = {a: 1, b: 2};
        const copy = __py.dict.copy(d);
        expect(copy).toEqual({a: 1, b: 2});
        expect(copy).not.toBe(d);
    });
});

describe('__py.dict.fromkeys()', () => {
    test('creates dict from keys', () => {
        expect(__py.dict.fromkeys(['a', 'b'], 0)).toEqual({a: 0, b: 0});
    });
});

// =============================================================================
// SET METHODS
// =============================================================================

describe('__py.set.remove()', () => {
    test('removes element', () => {
        const s = new Set([1, 2, 3]);
        __py.set.remove(s, 2);
        expect(s).toEqual(new Set([1, 3]));
    });
    
    test('throws when missing', () => {
        const s = new Set([1]);
        expect(() => __py.set.remove(s, 2)).toThrow('KeyError: 2');
    });
});

describe('__py.set.discard()', () => {
    test('removes if present', () => {
        const s = new Set([1, 2]);
        __py.set.discard(s, 2);
        expect(s).toEqual(new Set([1]));
    });
    
    test('ignores if missing', () => {
        const s = new Set([1]);
        __py.set.discard(s, 2);  // No error
        expect(s).toEqual(new Set([1]));
    });
});

describe('__py.set.pop()', () => {
    test('pops arbitrary element', () => {
        const s = new Set([1]);
        expect(__py.set.pop(s)).toBe(1);
        expect(s.size).toBe(0);
    });
    
    test('throws on empty set', () => {
        expect(() => __py.set.pop(new Set())).toThrow('pop from an empty set');
    });
});

describe('__py.set.union()', () => {
    test('creates union', () => {
        const s = new Set([1, 2]);
        const result = __py.set.union(s, [3, 4]);
        expect(result).toEqual(new Set([1, 2, 3, 4]));
    });
});

describe('__py.set.intersection()', () => {
    test('creates intersection', () => {
        const s = new Set([1, 2, 3]);
        const result = __py.set.intersection(s, [2, 3, 4]);
        expect(result).toEqual(new Set([2, 3]));
    });
});

describe('__py.set.difference()', () => {
    test('creates difference', () => {
        const s = new Set([1, 2, 3]);
        const result = __py.set.difference(s, [2]);
        expect(result).toEqual(new Set([1, 3]));
    });
});

describe('__py.set.symmetric_difference()', () => {
    test('creates symmetric difference', () => {
        const s = new Set([1, 2, 3]);
        const result = __py.set.symmetric_difference(s, [2, 3, 4]);
        expect(result).toEqual(new Set([1, 4]));
    });
});

describe('__py.set.issubset()', () => {
    test('true when subset', () => {
        const s = new Set([1, 2]);
        expect(__py.set.issubset(s, [1, 2, 3])).toBe(true);
    });
    
    test('false when not subset', () => {
        const s = new Set([1, 4]);
        expect(__py.set.issubset(s, [1, 2, 3])).toBe(false);
    });
});

describe('__py.set.issuperset()', () => {
    test('true when superset', () => {
        const s = new Set([1, 2, 3]);
        expect(__py.set.issuperset(s, [1, 2])).toBe(true);
    });
});

describe('__py.set.isdisjoint()', () => {
    test('true when no common elements', () => {
        const s = new Set([1, 2]);
        expect(__py.set.isdisjoint(s, [3, 4])).toBe(true);
    });
    
    test('false when common elements', () => {
        const s = new Set([1, 2]);
        expect(__py.set.isdisjoint(s, [2, 3])).toBe(false);
    });
});
