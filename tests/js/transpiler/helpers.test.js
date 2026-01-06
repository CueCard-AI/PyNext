/**
 * Tests for additional __py helper functions
 * 
 * del, del_slice, str_count, list_remove, dict_pop, dict_setdefault,
 * isinstance, type, sum
 */

const __py = require('./setup');

describe('__py Helper Functions', () => {
    
    // =========================================================================
    // DEL
    // =========================================================================
    
    describe('del() - Delete by index/key', () => {
        test('del from array by positive index', () => {
            const arr = [1, 2, 3, 4, 5];
            __py.del(arr, 2);
            expect(arr).toEqual([1, 2, 4, 5]);
        });
        
        test('del from array by negative index', () => {
            const arr = [1, 2, 3, 4, 5];
            __py.del(arr, -1);
            expect(arr).toEqual([1, 2, 3, 4]);
        });
        
        test('del from array index 0', () => {
            const arr = [1, 2, 3];
            __py.del(arr, 0);
            expect(arr).toEqual([2, 3]);
        });
        
        test('del from object by key', () => {
            const obj = {a: 1, b: 2, c: 3};
            __py.del(obj, 'b');
            expect(obj).toEqual({a: 1, c: 3});
        });
        
        test('del non-existent key', () => {
            const obj = {a: 1};
            __py.del(obj, 'z');
            expect(obj).toEqual({a: 1});
        });
    });
    
    // =========================================================================
    // DEL_SLICE
    // =========================================================================
    
    describe('del_slice() - Delete slice from array', () => {
        test('del_slice basic range', () => {
            const arr = [1, 2, 3, 4, 5];
            __py.del_slice(arr, [1, 3]);
            expect(arr).toEqual([1, 4, 5]);
        });
        
        test('del_slice from start', () => {
            const arr = [1, 2, 3, 4, 5];
            __py.del_slice(arr, [null, 2]);
            expect(arr).toEqual([3, 4, 5]);
        });
        
        test('del_slice to end', () => {
            const arr = [1, 2, 3, 4, 5];
            __py.del_slice(arr, [3, null]);
            expect(arr).toEqual([1, 2, 3]);
        });
        
        test('del_slice with negative indices', () => {
            const arr = [1, 2, 3, 4, 5];
            __py.del_slice(arr, [-2, null]);
            expect(arr).toEqual([1, 2, 3]);
        });
    });
    
    // =========================================================================
    // SUM
    // =========================================================================
    
    describe('sum() - Sum of iterable', () => {
        test('sum of array', () => {
            expect(__py.sum([1, 2, 3, 4, 5])).toBe(15);
        });
        
        test('sum of empty array', () => {
            expect(__py.sum([])).toBe(0);
        });
        
        test('sum of single element', () => {
            expect(__py.sum([42])).toBe(42);
        });
        
        test('sum with negative numbers', () => {
            expect(__py.sum([-1, 1, -2, 2])).toBe(0);
        });
        
        test('sum with floats', () => {
            expect(__py.sum([0.1, 0.2, 0.3])).toBeCloseTo(0.6);
        });
    });
    
    // =========================================================================
    // STR_COUNT
    // =========================================================================
    
    describe('str_count() - Count substring occurrences', () => {
        test('count occurrences', () => {
            expect(__py.str_count('hello hello hello', 'hello')).toBe(3);
        });
        
        test('count single char', () => {
            expect(__py.str_count('mississippi', 'i')).toBe(4);
        });
        
        test('count not found', () => {
            expect(__py.str_count('hello', 'x')).toBe(0);
        });
        
        test('count empty substring', () => {
            expect(__py.str_count('abc', '')).toBe(4);  // Python behavior
        });
        
        test('count overlapping', () => {
            // Python doesn't count overlapping occurrences
            expect(__py.str_count('aaa', 'aa')).toBe(1);
        });
    });
    
    // =========================================================================
    // LIST_REMOVE
    // =========================================================================
    
    describe('list_remove() - Remove first occurrence', () => {
        test('remove existing element', () => {
            const arr = [1, 2, 3, 2, 4];
            __py.list_remove(arr, 2);
            expect(arr).toEqual([1, 3, 2, 4]);  // Removes first 2 only
        });
        
        test('remove string element', () => {
            const arr = ['a', 'b', 'c'];
            __py.list_remove(arr, 'b');
            expect(arr).toEqual(['a', 'c']);
        });
        
        test('remove throws on not found', () => {
            const arr = [1, 2, 3];
            expect(() => __py.list_remove(arr, 5)).toThrow();
        });
        
        test('remove with deep equality', () => {
            const arr = [[1, 2], [3, 4]];
            __py.list_remove(arr, [1, 2]);
            expect(arr).toEqual([[3, 4]]);
        });
    });
    
    // =========================================================================
    // DICT_POP
    // =========================================================================
    
    describe('dict_pop() - Pop key from dict', () => {
        test('pop existing key', () => {
            const obj = {a: 1, b: 2, c: 3};
            const val = __py.dict_pop(obj, 'b');
            expect(val).toBe(2);
            expect(obj).toEqual({a: 1, c: 3});
        });
        
        test('pop with default', () => {
            const obj = {a: 1};
            const val = __py.dict_pop(obj, 'z', 99);
            expect(val).toBe(99);
            expect(obj).toEqual({a: 1});
        });
        
        test('pop missing without default throws', () => {
            const obj = {a: 1};
            expect(() => __py.dict_pop(obj, 'z')).toThrow();
        });
    });
    
    // =========================================================================
    // DICT_SETDEFAULT
    // =========================================================================
    
    describe('dict_setdefault() - Set default value', () => {
        test('setdefault on missing key', () => {
            const obj = {a: 1};
            const val = __py.dict_setdefault(obj, 'b', 2);
            expect(val).toBe(2);
            expect(obj).toEqual({a: 1, b: 2});
        });
        
        test('setdefault on existing key', () => {
            const obj = {a: 1, b: 5};
            const val = __py.dict_setdefault(obj, 'b', 2);
            expect(val).toBe(5);  // Returns existing value
            expect(obj).toEqual({a: 1, b: 5});  // Unchanged
        });
        
        test('setdefault with null default', () => {
            const obj = {};
            const val = __py.dict_setdefault(obj, 'x');
            expect(val).toBeNull();
            expect(obj).toEqual({x: null});
        });
    });
    
    // =========================================================================
    // ISINSTANCE
    // =========================================================================
    
    describe('isinstance() - Type checking', () => {
        test('isinstance string', () => {
            expect(__py.isinstance('hello', 'str')).toBe(true);
            expect(__py.isinstance(123, 'str')).toBe(false);
        });
        
        test('isinstance int', () => {
            expect(__py.isinstance(42, 'int')).toBe(true);
            expect(__py.isinstance(3.14, 'int')).toBe(false);
        });
        
        test('isinstance float', () => {
            expect(__py.isinstance(3.14, 'float')).toBe(true);
            expect(__py.isinstance(42, 'float')).toBe(true);  // int is also float
        });
        
        test('isinstance bool', () => {
            expect(__py.isinstance(true, 'bool')).toBe(true);
            expect(__py.isinstance(false, 'bool')).toBe(true);
            expect(__py.isinstance(1, 'bool')).toBe(false);
        });
        
        test('isinstance list', () => {
            expect(__py.isinstance([1, 2], 'list')).toBe(true);
            expect(__py.isinstance({}, 'list')).toBe(false);
        });
        
        test('isinstance dict', () => {
            expect(__py.isinstance({a: 1}, 'dict')).toBe(true);
            expect(__py.isinstance([], 'dict')).toBe(false);
        });
        
        test('isinstance with tuple of types', () => {
            expect(__py.isinstance('hello', ['str', 'int'])).toBe(true);
            expect(__py.isinstance(42, ['str', 'int'])).toBe(true);
            expect(__py.isinstance(true, ['str', 'int'])).toBe(false);
        });
    });
    
    // =========================================================================
    // TYPE
    // =========================================================================
    
    describe('type() - Get type name', () => {
        test('type of null', () => {
            expect(__py.type(null)).toBe('NoneType');
        });
        
        test('type of array', () => {
            expect(__py.type([1, 2])).toBe('list');
        });
        
        test('type of string', () => {
            expect(__py.type('hello')).toBe('str');
        });
        
        test('type of int', () => {
            expect(__py.type(42)).toBe('int');
        });
        
        test('type of float', () => {
            expect(__py.type(3.14)).toBe('float');
        });
        
        test('type of bool', () => {
            expect(__py.type(true)).toBe('bool');
        });
        
        test('type of dict', () => {
            expect(__py.type({a: 1})).toBe('dict');
        });
    });
});
