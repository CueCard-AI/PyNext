/**
 * Tests for __py.repr() and __py.ascii() - F-string conversion functions
 * 
 * Python f-string conversions:
 * - !s → str() - String conversion
 * - !r → repr() - Debug representation  
 * - !a → ascii() - ASCII-safe representation
 */

const __py = require('./setup');

describe('__py.repr() - Python repr', () => {
    
    // =========================================================================
    // BASIC TYPES
    // =========================================================================
    
    describe('Basic types', () => {
        test('repr(null) returns "None"', () => {
            expect(__py.repr(null)).toBe('None');
        });
        
        test('repr(undefined) returns "None"', () => {
            expect(__py.repr(undefined)).toBe('None');
        });
        
        test('repr(true) returns "True"', () => {
            expect(__py.repr(true)).toBe('True');
        });
        
        test('repr(false) returns "False"', () => {
            expect(__py.repr(false)).toBe('False');
        });
        
        test('repr(123) returns "123"', () => {
            expect(__py.repr(123)).toBe('123');
        });
        
        test('repr(3.14) returns "3.14"', () => {
            expect(__py.repr(3.14)).toBe('3.14');
        });
    });
    
    // =========================================================================
    // STRINGS - QUOTES
    // =========================================================================
    
    describe('Strings', () => {
        test('repr("hello") wraps in single quotes', () => {
            expect(__py.repr('hello')).toBe("'hello'");
        });
        
        test('repr("") returns empty quoted string', () => {
            expect(__py.repr('')).toBe("''");
        });
        
        test("repr escapes single quotes", () => {
            expect(__py.repr("it's")).toBe("'it\\'s'");
        });
        
        test('repr with newlines', () => {
            const result = __py.repr('hello\nworld');
            expect(result.startsWith("'")).toBe(true);
            expect(result.endsWith("'")).toBe(true);
        });
    });
    
    // =========================================================================
    // ARRAYS
    // =========================================================================
    
    describe('Arrays', () => {
        test('repr([1,2,3]) returns "[1, 2, 3]"', () => {
            expect(__py.repr([1, 2, 3])).toBe('[1, 2, 3]');
        });
        
        test('repr([]) returns "[]"', () => {
            expect(__py.repr([])).toBe('[]');
        });
        
        test('repr with strings in array', () => {
            expect(__py.repr(['a', 'b'])).toBe("['a', 'b']");
        });
        
        test('repr nested arrays', () => {
            expect(__py.repr([[1, 2], [3, 4]])).toBe('[[1, 2], [3, 4]]');
        });
        
        test('repr mixed types', () => {
            expect(__py.repr([1, 'a', true])).toBe("[1, 'a', True]");
        });
    });
    
    // =========================================================================
    // OBJECTS
    // =========================================================================
    
    describe('Objects', () => {
        test('repr({a: 1}) returns dict-like string', () => {
            expect(__py.repr({a: 1})).toBe("{'a': 1}");
        });
        
        test('repr({}) returns "{}"', () => {
            expect(__py.repr({})).toBe('{}');
        });
        
        test('repr with multiple keys', () => {
            const result = __py.repr({a: 1, b: 2});
            expect(result).toContain("'a': 1");
            expect(result).toContain("'b': 2");
        });
        
        test('repr nested objects', () => {
            expect(__py.repr({a: {b: 1}})).toBe("{'a': {'b': 1}}");
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR
    // =========================================================================
    
    describe('Python behavior', () => {
        test('Python: repr("hello") shows quotes', () => {
            expect(__py.repr('hello')).toContain("'");
        });
        
        test('Python: repr(None) == "None"', () => {
            expect(__py.repr(null)).toBe('None');
        });
        
        test('Python: repr(True) == "True"', () => {
            expect(__py.repr(true)).toBe('True');
        });
        
        test('Python: repr([]) == "[]"', () => {
            expect(__py.repr([])).toBe('[]');
        });
    });
});


describe('__py.ascii() - Python ascii', () => {
    
    // =========================================================================
    // ASCII-SAFE OUTPUT
    // =========================================================================
    
    describe('ASCII-safe output', () => {
        test('ascii("hello") is same as repr', () => {
            expect(__py.ascii('hello')).toBe("'hello'");
        });
        
        test('ascii escapes non-ASCII characters', () => {
            const result = __py.ascii('héllo');
            expect(result).not.toContain('é');
            expect(result).toContain('\\x');
        });
        
        test('ascii with unicode', () => {
            const result = __py.ascii('你好');
            expect(result).not.toContain('你');
            expect(result).not.toContain('好');
            expect(result).toContain('\\u');
        });
        
        test('ascii with emoji', () => {
            const result = __py.ascii('Hi 👋');
            expect(result).not.toContain('👋');
        });
    });
    
    // =========================================================================
    // BASIC TYPES (same as repr for ASCII content)
    // =========================================================================
    
    describe('Basic types', () => {
        test('ascii(null) returns "None"', () => {
            expect(__py.ascii(null)).toBe('None');
        });
        
        test('ascii(true) returns "True"', () => {
            expect(__py.ascii(true)).toBe('True');
        });
        
        test('ascii(123) returns "123"', () => {
            expect(__py.ascii(123)).toBe('123');
        });
        
        test('ascii with ASCII array', () => {
            expect(__py.ascii(['a', 'b'])).toBe("['a', 'b']");
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR
    // =========================================================================
    
    describe('Python behavior', () => {
        test('Python: ascii("\\xe9") escapes', () => {
            const result = __py.ascii('é');
            expect(result).toContain('\\x');
        });
        
        test('Python: ascii for normal ASCII is same as repr', () => {
            expect(__py.ascii('abc')).toBe(__py.repr('abc'));
        });
    });
});


describe('F-string conversion patterns', () => {
    
    // =========================================================================
    // COMMON PATTERNS
    // =========================================================================
    
    describe('Common patterns', () => {
        test('f"{obj!r}" pattern', () => {
            const obj = {a: 1};
            const result = __py.repr(obj);
            expect(result).toContain("'a': 1");
        });
        
        test('f"{val!s}" pattern', () => {
            // !s just calls str()/String()
            expect(String(123)).toBe('123');
            expect(String(null)).toBe('null');
        });
        
        test('Debugging with !r shows string quotes', () => {
            const value = 'hello';
            const debug = __py.repr(value);
            expect(debug).toBe("'hello'");
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('repr of function', () => {
            const fn = () => {};
            const result = __py.repr(fn);
            // Should return some string representation
            expect(typeof result).toBe('string');
        });
        
        test('repr of Date', () => {
            const date = new Date('2024-01-01');
            const result = __py.repr(date);
            expect(typeof result).toBe('string');
        });
        
        test('ascii handles mixed content', () => {
            const result = __py.ascii(['hello', '你好']);
            expect(result).toContain('hello');
            expect(result).toContain('\\u');
        });
    });
});
