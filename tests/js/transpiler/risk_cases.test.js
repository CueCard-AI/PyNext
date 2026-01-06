/**
 * Risk Cases Tests for Phase 18.3
 * 
 * Tests for high-risk areas that could cause subtle bugs:
 * 1. split() maxsplit whitespace preservation
 * 2. title() apostrophe handling
 * 3. sort() mixed type errors
 * 4. is*() unicode support
 * 5. splitlines() all line endings
 * 6. strip() with regex special chars
 * 7. insert() negative index edge cases
 */

const __py = require('./setup');

// =============================================================================
// SPLIT() WHITESPACE PRESERVATION
// =============================================================================

describe('split() with maxsplit preserves whitespace', () => {
    test('preserves tab in remainder', () => {
        // Python: "a  b\tc".split(None, 1) → ['a', 'b\tc']
        expect(__py.str.split('a  b\tc', null, 1)).toEqual(['a', 'b\tc']);
    });
    
    test('preserves multiple spaces in remainder', () => {
        // Python: "a   b   c".split(None, 1) → ['a', 'b   c']
        expect(__py.str.split('a   b   c', null, 1)).toEqual(['a', 'b   c']);
    });
    
    test('preserves newline in remainder', () => {
        expect(__py.str.split('a b\nc', null, 1)).toEqual(['a', 'b\nc']);
    });
    
    test('maxsplit=0 returns whole string', () => {
        expect(__py.str.split('a b c', null, 0)).toEqual(['a b c']);
    });
    
    test('leading whitespace trimmed, trailing preserved', () => {
        expect(__py.str.split('  a b c  ', null, 1)).toEqual(['a', 'b c  ']);
    });
});

// =============================================================================
// TITLE() APOSTROPHE HANDLING
// =============================================================================

describe('title() handles apostrophes like Python', () => {
    test("it's a test → It'S A Test", () => {
        expect(__py.str.title("it's a test")).toBe("It'S A Test");
    });
    
    test("they're here → They'Re Here", () => {
        expect(__py.str.title("they're here")).toBe("They'Re Here");
    });
    
    test("don't stop → Don'T Stop", () => {
        expect(__py.str.title("don't stop")).toBe("Don'T Stop");
    });
    
    test('numbers start new word', () => {
        expect(__py.str.title("hello123world")).toBe("Hello123World");
    });
    
    test('mixed punctuation', () => {
        expect(__py.str.title("hello-world")).toBe("Hello-World");
    });
    
    test('underscore starts new word', () => {
        expect(__py.str.title("hello_world")).toBe("Hello_World");
    });
});

// =============================================================================
// SORT() MIXED TYPES
// =============================================================================

describe('sort() throws on mixed types', () => {
    test('throws on [1, "a"]', () => {
        const arr = [1, "a"];
        expect(() => __py.list.sort(arr)).toThrow(TypeError);
    });
    
    test('throws on ["a", 1]', () => {
        const arr = ["a", 1];
        expect(() => __py.list.sort(arr)).toThrow(TypeError);
    });
    
    test('error message matches Python style', () => {
        try {
            __py.list.sort([1, "a"]);
        } catch (e) {
            expect(e.message).toContain("'<' not supported between");
        }
    });
    
    test('same types work fine', () => {
        const nums = [3, 1, 2];
        __py.list.sort(nums);
        expect(nums).toEqual([1, 2, 3]);
        
        const strs = ['c', 'a', 'b'];
        __py.list.sort(strs);
        expect(strs).toEqual(['a', 'b', 'c']);
    });
});

// =============================================================================
// IS*() UNICODE SUPPORT
// =============================================================================

describe('isalpha() unicode support', () => {
    test('café is alphabetic', () => {
        expect(__py.str.isalpha('café')).toBe(true);
    });
    
    test('日本 is alphabetic (CJK)', () => {
        expect(__py.str.isalpha('日本')).toBe(true);
    });
    
    test('Привет is alphabetic (Cyrillic)', () => {
        expect(__py.str.isalpha('Привет')).toBe(true);
    });
    
    test('mixed with numbers is not alphabetic', () => {
        expect(__py.str.isalpha('café123')).toBe(false);
    });
    
    test('mixed with space is not alphabetic', () => {
        expect(__py.str.isalpha('hello world')).toBe(false);
    });
});

describe('isupper/islower unicode support', () => {
    test('CAFÉ is uppercase', () => {
        expect(__py.str.isupper('CAFÉ')).toBe(true);
    });
    
    test('café is lowercase', () => {
        expect(__py.str.islower('café')).toBe(true);
    });
    
    test('mixed case fails', () => {
        expect(__py.str.isupper('CaFé')).toBe(false);
        expect(__py.str.islower('CaFé')).toBe(false);
    });
    
    test('123 has no cased chars - returns false', () => {
        expect(__py.str.isupper('123')).toBe(false);
        expect(__py.str.islower('123')).toBe(false);
    });
    
    test('ABC123 - has cased chars, all upper', () => {
        expect(__py.str.isupper('ABC123')).toBe(true);
    });
});

// =============================================================================
// SPLITLINES() ALL LINE ENDINGS
// =============================================================================

describe('splitlines() handles all Python line endings', () => {
    test('basic \\n', () => {
        expect(__py.str.splitlines('a\nb\nc')).toEqual(['a', 'b', 'c']);
    });
    
    test('basic \\r', () => {
        expect(__py.str.splitlines('a\rb\rc')).toEqual(['a', 'b', 'c']);
    });
    
    test('Windows \\r\\n', () => {
        expect(__py.str.splitlines('a\r\nb\r\nc')).toEqual(['a', 'b', 'c']);
    });
    
    test('vertical tab \\x0b', () => {
        expect(__py.str.splitlines('a\x0bb\x0bc')).toEqual(['a', 'b', 'c']);
    });
    
    test('form feed \\x0c', () => {
        expect(__py.str.splitlines('a\x0cb\x0cc')).toEqual(['a', 'b', 'c']);
    });
    
    test('line separator \\u2028', () => {
        expect(__py.str.splitlines('a\u2028b\u2028c')).toEqual(['a', 'b', 'c']);
    });
    
    test('paragraph separator \\u2029', () => {
        expect(__py.str.splitlines('a\u2029b')).toEqual(['a', 'b']);
    });
    
    test('mixed line endings', () => {
        expect(__py.str.splitlines('a\nb\rc\r\nd')).toEqual(['a', 'b', 'c', 'd']);
    });
    
    test('keepends=true preserves endings', () => {
        const result = __py.str.splitlines('a\nb\r\nc', true);
        expect(result).toEqual(['a\n', 'b\r\n', 'c']);
    });
});

// =============================================================================
// STRIP() WITH REGEX SPECIAL CHARS
// =============================================================================

describe('strip() with regex special characters', () => {
    test('strips ^', () => {
        expect(__py.str.strip('^test^', '^')).toBe('test');
    });
    
    test('strips -', () => {
        expect(__py.str.strip('-test-', '-')).toBe('test');
    });
    
    test('strips ^-', () => {
        expect(__py.str.strip('^-test-^', '^-')).toBe('test');
    });
    
    test('strips []', () => {
        expect(__py.str.strip('[]test[]', '[]')).toBe('test');
    });
    
    test('strips backslash', () => {
        expect(__py.str.strip('\\test\\', '\\')).toBe('test');
    });
    
    test('strips .', () => {
        expect(__py.str.strip('...test...', '.')).toBe('test');
    });
    
    test('strips *', () => {
        expect(__py.str.strip('***test***', '*')).toBe('test');
    });
    
    test('strips $', () => {
        expect(__py.str.strip('$$$test$$$', '$')).toBe('test');
    });
});

// =============================================================================
// INSERT() NEGATIVE INDEX EDGE CASES
// =============================================================================

describe('insert() negative index edge cases', () => {
    test('insert(-1, x) inserts before last', () => {
        const arr = [1, 2, 3];
        __py.list.insert(arr, -1, 'x');
        expect(arr).toEqual([1, 2, 'x', 3]);
    });
    
    test('insert(-100, x) clamps to 0', () => {
        const arr = [1, 2, 3];
        __py.list.insert(arr, -100, 'x');
        expect(arr).toEqual(['x', 1, 2, 3]);
    });
    
    test('insert(100, x) clamps to end', () => {
        const arr = [1, 2, 3];
        __py.list.insert(arr, 100, 'x');
        expect(arr).toEqual([1, 2, 3, 'x']);
    });
    
    test('insert(-2, x) inserts before second-to-last', () => {
        const arr = [1, 2, 3];
        __py.list.insert(arr, -2, 'x');
        expect(arr).toEqual([1, 'x', 2, 3]);
    });
    
    test('insert on empty array', () => {
        const arr = [];
        __py.list.insert(arr, 0, 'x');
        expect(arr).toEqual(['x']);
    });
    
    test('insert at 0', () => {
        const arr = [1, 2, 3];
        __py.list.insert(arr, 0, 'x');
        expect(arr).toEqual(['x', 1, 2, 3]);
    });
});

// =============================================================================
// DEEP EQUALITY IN LIST METHODS
// =============================================================================

describe('list methods use deep equality', () => {
    test('remove() with nested array', () => {
        const arr = [[1, 2], [3, 4], [5, 6]];
        __py.list.remove(arr, [3, 4]);
        expect(arr).toEqual([[1, 2], [5, 6]]);
    });
    
    test('index() with nested array', () => {
        const arr = [[1, 2], [3, 4], [5, 6]];
        expect(__py.list.index(arr, [3, 4])).toBe(1);
    });
    
    test('count() with nested array', () => {
        const arr = [[1, 2], [1, 2], [3, 4]];
        expect(__py.list.count(arr, [1, 2])).toBe(2);
    });
    
    test('remove() with object', () => {
        const arr = [{a: 1}, {a: 2}, {a: 3}];
        __py.list.remove(arr, {a: 2});
        expect(arr).toEqual([{a: 1}, {a: 3}]);
    });
});

// =============================================================================
// DICT METHODS EDGE CASES
// =============================================================================

describe('dict.pop() edge cases', () => {
    test('throws without default', () => {
        expect(() => __py.dict.pop({}, 'missing')).toThrow(/KeyError/);
    });
    
    test('returns default when provided', () => {
        expect(__py.dict.pop({}, 'missing', 'default')).toBe('default');
    });
    
    test('returns value and removes key', () => {
        const d = {a: 1, b: 2};
        expect(__py.dict.pop(d, 'a')).toBe(1);
        expect(d).toEqual({b: 2});
    });
});

describe('dict.setdefault() edge cases', () => {
    test('returns existing value without modifying', () => {
        const d = {a: 1};
        expect(__py.dict.setdefault(d, 'a', 999)).toBe(1);
        expect(d.a).toBe(1);
    });
    
    test('sets and returns default for missing key', () => {
        const d = {};
        expect(__py.dict.setdefault(d, 'a', [])).toEqual([]);
        expect(d.a).toEqual([]);
    });
    
    test('default is null when not provided', () => {
        const d = {};
        expect(__py.dict.setdefault(d, 'a')).toBe(null);
        expect(d.a).toBe(null);
    });
});

// =============================================================================
// SET METHODS EDGE CASES
// =============================================================================

describe('set methods edge cases', () => {
    test('remove() throws on missing', () => {
        const s = new Set([1, 2]);
        expect(() => __py.set.remove(s, 999)).toThrow(/KeyError/);
    });
    
    test('discard() ignores missing', () => {
        const s = new Set([1, 2]);
        __py.set.discard(s, 999);  // No error
        expect(s).toEqual(new Set([1, 2]));
    });
    
    test('pop() throws on empty', () => {
        expect(() => __py.set.pop(new Set())).toThrow(/empty set/);
    });
    
    test('symmetric_difference()', () => {
        const s1 = new Set([1, 2, 3]);
        const s2 = [2, 3, 4];
        expect(__py.set.symmetric_difference(s1, s2)).toEqual(new Set([1, 4]));
    });
});

// =============================================================================
// EDGE CASES FOR EMPTY INPUTS
// =============================================================================

describe('empty input edge cases', () => {
    test('str.split("") with no args', () => {
        expect(__py.str.split('')).toEqual([]);
    });
    
    test('str.split("") with separator', () => {
        expect(__py.str.split('', ',')).toEqual(['']);
    });
    
    test('str.title("")', () => {
        expect(__py.str.title('')).toBe('');
    });
    
    test('str.capitalize("")', () => {
        expect(__py.str.capitalize('')).toBe('');
    });
    
    test('list.sort([])', () => {
        const arr = [];
        __py.list.sort(arr);
        expect(arr).toEqual([]);
    });
    
    test('str.isalpha("")', () => {
        expect(__py.str.isalpha('')).toBe(false);
    });
    
    test('str.splitlines("")', () => {
        expect(__py.str.splitlines('')).toEqual(['']);
    });
});
