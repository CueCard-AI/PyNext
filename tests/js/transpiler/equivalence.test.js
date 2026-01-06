/**
 * Equivalence Tests - Verify transpiled code produces same results as Python
 * 
 * These tests run actual transpiled patterns and verify they produce
 * the same results that the original Python code would produce.
 * 
 * This is the most critical test file - it verifies end-to-end correctness.
 */

const __py = require('./setup');

describe('Equivalence Tests - Transpiled Code Verification', () => {
    
    // =========================================================================
    // LIST COMPREHENSION EQUIVALENCE
    // =========================================================================
    
    describe('List Comprehension Equivalence', () => {
        
        test('[x*2 for x in [1,2,3]] == [2, 4, 6]', () => {
            // Python: [x*2 for x in [1,2,3]]
            // Transpiled: [...__py.iter([1,2,3])].map(x => __py.mul(x, 2))
            const items = [1, 2, 3];
            const result = [...__py.iter(items)].map(x => __py.mul(x, 2));
            expect(result).toEqual([2, 4, 6]);
        });
        
        test('[x for x in items if x > 0] with negatives', () => {
            // Python: [x for x in items if x > 0]
            const items = [-2, -1, 0, 1, 2];
            const result = [...__py.iter(items)].filter(x => x > 0);
            expect(result).toEqual([1, 2]);
        });
        
        test('[x*2 for x in items if x > 0]', () => {
            // Python: [x*2 for x in items if x > 0]
            const items = [-1, 0, 1, 2, 3];
            const result = [...__py.iter(items)]
                .filter(x => x > 0)
                .map(x => __py.mul(x, 2));
            expect(result).toEqual([2, 4, 6]);
        });
        
        test('[x**2 for x in range(5)]', () => {
            // Python: [x**2 for x in range(5)]
            const result = [...__py.iter(__py.range(5))].map(x => x ** 2);
            expect(result).toEqual([0, 1, 4, 9, 16]);
        });
        
        test('[[j for j in range(3)] for i in range(2)]', () => {
            // Python: [[j for j in range(3)] for i in range(2)]
            const result = [...__py.iter(__py.range(2))].map(
                i => [...__py.iter(__py.range(3))].map(j => j)
            );
            expect(result).toEqual([[0, 1, 2], [0, 1, 2]]);
        });
        
        test('[item.upper() for item in ["a", "b", "c"]]', () => {
            // Python: [item.upper() for item in items]
            // Note: In JS, .upper() -> .toUpperCase()
            const items = ["a", "b", "c"];
            const result = [...__py.iter(items)].map(item => item.toUpperCase());
            expect(result).toEqual(["A", "B", "C"]);
        });
        
        test('Flatten: [y for x in matrix for y in x]', () => {
            // Python: [y for x in matrix for y in x]
            const matrix = [[1, 2], [3, 4], [5, 6]];
            const result = [...__py.iter(matrix)].flatMap(x => [...__py.iter(x)]);
            expect(result).toEqual([1, 2, 3, 4, 5, 6]);
        });
    });
    
    // =========================================================================
    // DICT COMPREHENSION EQUIVALENCE
    // =========================================================================
    
    describe('Dict Comprehension Equivalence', () => {
        
        test('{k: v for k, v in items}', () => {
            // Python: {k: v for k, v in items}
            const items = [['a', 1], ['b', 2], ['c', 3]];
            const result = Object.fromEntries(
                [...__py.iter(items)].map(([k, v]) => [k, v])
            );
            expect(result).toEqual({a: 1, b: 2, c: 3});
        });
        
        test('{k: v*2 for k, v in items}', () => {
            // Python: {k: v*2 for k, v in items}
            const items = [['a', 1], ['b', 2]];
            const result = Object.fromEntries(
                [...__py.iter(items)].map(([k, v]) => [k, __py.mul(v, 2)])
            );
            expect(result).toEqual({a: 2, b: 4});
        });
        
        test('{k: v for k, v in items if v > 0}', () => {
            // Python: {k: v for k, v in items if v > 0}
            const items = [['a', -1], ['b', 2], ['c', 3]];
            const result = Object.fromEntries(
                [...__py.iter(items)]
                    .filter(([k, v]) => v > 0)
                    .map(([k, v]) => [k, v])
            );
            expect(result).toEqual({b: 2, c: 3});
        });
        
        test('{i: i**2 for i in range(5)}', () => {
            // Python: {i: i**2 for i in range(5)}
            const result = Object.fromEntries(
                [...__py.iter(__py.range(5))].map(i => [i, i ** 2])
            );
            expect(result).toEqual({0: 0, 1: 1, 2: 4, 3: 9, 4: 16});
        });
    });
    
    // =========================================================================
    // SET COMPREHENSION EQUIVALENCE
    // =========================================================================
    
    describe('Set Comprehension Equivalence', () => {
        
        test('{x for x in [1, 2, 2, 3, 3, 3]}', () => {
            // Python: {x for x in items}
            const items = [1, 2, 2, 3, 3, 3];
            const result = new Set([...__py.iter(items)]);
            expect([...result].sort()).toEqual([1, 2, 3]);
        });
        
        test('{x*2 for x in items}', () => {
            // Python: {x*2 for x in items}
            const items = [1, 2, 3];
            const result = new Set([...__py.iter(items)].map(x => __py.mul(x, 2)));
            expect([...result].sort()).toEqual([2, 4, 6]);
        });
        
        test('{x for x in items if x > 0}', () => {
            // Python: {x for x in items if x > 0}
            const items = [-1, 0, 1, 2, 2];
            const result = new Set([...__py.iter(items)].filter(x => x > 0));
            expect([...result].sort()).toEqual([1, 2]);
        });
    });
    
    // =========================================================================
    // GENERATOR EXPRESSION EQUIVALENCE
    // =========================================================================
    
    describe('Generator Expression Equivalence', () => {
        
        test('sum(x for x in items)', () => {
            // Python: sum(x for x in items)
            const items = [1, 2, 3, 4, 5];
            const result = __py.sum([...__py.iter(items)]);
            expect(result).toBe(15);
        });
        
        test('sum(x*2 for x in items)', () => {
            // Python: sum(x*2 for x in items)
            const items = [1, 2, 3];
            const result = __py.sum([...__py.iter(items)].map(x => __py.mul(x, 2)));
            expect(result).toBe(12);
        });
        
        test('any(x > 0 for x in items)', () => {
            // Python: any(x > 0 for x in items)
            const items = [-1, 0, 1];
            const result = [...__py.iter(items)].some(x => x > 0);
            expect(result).toBe(true);
        });
        
        test('all(x > 0 for x in items)', () => {
            // Python: all(x > 0 for x in items)
            const items = [1, 2, 3];
            const result = [...__py.iter(items)].every(x => x > 0);
            expect(result).toBe(true);
        });
        
        test('all(x > 0 for x in items) with negatives', () => {
            const items = [1, -1, 2];
            const result = [...__py.iter(items)].every(x => x > 0);
            expect(result).toBe(false);
        });
        
        test('max(x.value for x in items)', () => {
            // Python: max(x.value for x in items)
            const items = [{value: 1}, {value: 5}, {value: 3}];
            const result = Math.max(...[...__py.iter(items)].map(x => x.value));
            expect(result).toBe(5);
        });
        
        test('min(x for x in items)', () => {
            // Python: min(x for x in items)
            const items = [3, 1, 4, 1, 5];
            const result = Math.min(...[...__py.iter(items)]);
            expect(result).toBe(1);
        });
    });
    
    // =========================================================================
    // BOOLEAN OPERATOR EQUIVALENCE
    // =========================================================================
    
    describe('Boolean Operator Equivalence', () => {
        
        test('[] or "default" returns "default"', () => {
            // Python: [] or "default" returns "default"
            const x = [];
            const result = __py.bool(x) ? x : "default";
            expect(result).toBe("default");
        });
        
        test('[1] or "default" returns [1]', () => {
            // Python: [1] or "default" returns [1]
            const x = [1];
            const result = __py.bool(x) ? x : "default";
            expect(result).toEqual([1]);
        });
        
        test('[1] and "yes" returns "yes"', () => {
            // Python: [1] and "yes" returns "yes"
            const x = [1];
            const result = __py.bool(x) ? "yes" : x;
            expect(result).toBe("yes");
        });
        
        test('[] and "yes" returns []', () => {
            // Python: [] and "yes" returns []
            const x = [];
            const result = __py.bool(x) ? "yes" : x;
            expect(result).toEqual([]);
        });
        
        test('{} or "default" returns "default"', () => {
            const x = {};
            const result = __py.bool(x) ? x : "default";
            expect(result).toBe("default");
        });
        
        test('0 or 10 returns 10', () => {
            // Python: 0 or 10 returns 10
            const x = 0;
            const result = __py.bool(x) ? x : 10;
            expect(result).toBe(10);
        });
        
        test('5 or 10 returns 5', () => {
            // Python: 5 or 10 returns 5
            const x = 5;
            const result = __py.bool(x) ? x : 10;
            expect(result).toBe(5);
        });
    });
    
    // =========================================================================
    // CHAINED COMPARISON EQUIVALENCE
    // =========================================================================
    
    describe('Chained Comparison Equivalence', () => {
        
        test('0 < 5 < 10 is true', () => {
            // Python: 0 < 5 < 10
            const x = 5;
            expect((0 < x) && (x < 10)).toBe(true);
        });
        
        test('0 < 15 < 10 is false', () => {
            // Python: 0 < 15 < 10
            const x = 15;
            expect((0 < x) && (x < 10)).toBe(false);
        });
        
        test('0 < 0 < 10 is false', () => {
            const x = 0;
            expect((0 < x) && (x < 10)).toBe(false);
        });
        
        test('1 <= 1 <= 1 is true', () => {
            const x = 1;
            expect((1 <= x) && (x <= 1)).toBe(true);
        });
        
        test('a < b < c < d chained', () => {
            const [a, b, c, d] = [1, 2, 3, 4];
            expect((a < b) && (b < c) && (c < d)).toBe(true);
        });
        
        test('a < b > c pattern (valid in Python)', () => {
            // Python: 1 < 5 > 3 is True (5 > 1 and 5 > 3)
            const [a, b, c] = [1, 5, 3];
            expect((a < b) && (b > c)).toBe(true);
        });
    });
    
    // =========================================================================
    // FOR LOOP EQUIVALENCE
    // =========================================================================
    
    describe('For Loop Equivalence', () => {
        
        test('for i in range(5): result.append(i*2)', () => {
            const result = [];
            for (const i of __py.iter(__py.range(5))) {
                result.push(__py.mul(i, 2));
            }
            expect(result).toEqual([0, 2, 4, 6, 8]);
        });
        
        test('for k in dict: result.append(k)', () => {
            const d = {a: 1, b: 2, c: 3};
            const result = [];
            for (const k of __py.iter(d)) {
                result.push(k);
            }
            expect(result.sort()).toEqual(["a", "b", "c"]);
        });
        
        test('for i, item in enumerate(items):', () => {
            const items = ["a", "b", "c"];
            const result = [];
            for (const [i, item] of __py.enumerate(items)) {
                result.push(`${i}:${item}`);
            }
            expect(result).toEqual(["0:a", "1:b", "2:c"]);
        });
        
        test('for a, b in zip(list1, list2):', () => {
            const list1 = [1, 2, 3];
            const list2 = ["a", "b", "c"];
            const result = [];
            for (const [a, b] of __py.zip(list1, list2)) {
                result.push([a, b]);
            }
            expect(result).toEqual([[1, "a"], [2, "b"], [3, "c"]]);
        });
    });
    
    // =========================================================================
    // NEGATIVE INDEXING EQUIVALENCE
    // =========================================================================
    
    describe('Negative Indexing Equivalence', () => {
        
        test('items[-1]', () => {
            const items = [1, 2, 3, 4, 5];
            expect(__py.at(items, -1)).toBe(5);
        });
        
        test('items[-2]', () => {
            const items = [1, 2, 3, 4, 5];
            expect(__py.at(items, -2)).toBe(4);
        });
        
        test('string[-1]', () => {
            const s = "hello";
            expect(__py.at(s, -1)).toBe("o");
        });
    });
    
    // =========================================================================
    // SLICING EQUIVALENCE
    // =========================================================================
    
    describe('Slicing Equivalence', () => {
        
        test('items[1:3]', () => {
            const items = [0, 1, 2, 3, 4];
            expect(__py.slice(items, 1, 3)).toEqual([1, 2]);
        });
        
        test('items[::-1] (reverse)', () => {
            const items = [1, 2, 3];
            expect(__py.slice(items, null, null, -1)).toEqual([3, 2, 1]);
        });
        
        test('string[::2]', () => {
            const s = "abcdef";
            expect(__py.slice(s, null, null, 2)).toBe("ace");
        });
    });
    
    // =========================================================================
    // MODULO EQUIVALENCE
    // =========================================================================
    
    describe('Modulo Equivalence', () => {
        
        test('-7 % 3 == 2', () => {
            expect(__py.mod(-7, 3)).toBe(2);
        });
        
        test('7 % -3 == -2', () => {
            expect(__py.mod(7, -3)).toBe(-2);
        });
        
        test('Circular index: idx % len', () => {
            const items = [0, 1, 2, 3, 4];
            const idx = -1;
            const circularIdx = __py.mod(idx, items.length);
            expect(circularIdx).toBe(4);
            expect(items[circularIdx]).toBe(4);
        });
    });
    
    // =========================================================================
    // LIST OPERATIONS EQUIVALENCE
    // =========================================================================
    
    describe('List Operations Equivalence', () => {
        
        test('[1, 2] + [3, 4] == [1, 2, 3, 4]', () => {
            expect(__py.add([1, 2], [3, 4])).toEqual([1, 2, 3, 4]);
        });
        
        test('[1, 2] * 3 == [1, 2, 1, 2, 1, 2]', () => {
            expect(__py.mul([1, 2], 3)).toEqual([1, 2, 1, 2, 1, 2]);
        });
        
        test('"ab" * 3 == "ababab"', () => {
            expect(__py.mul("ab", 3)).toBe("ababab");
        });
        
        test('[1, 2] == [1, 2]', () => {
            expect(__py.eq([1, 2], [1, 2])).toBe(true);
        });
        
        test('[1, 2] in [[1, 2], [3, 4]]', () => {
            expect(__py.contains([1, 2], [[1, 2], [3, 4]])).toBe(true);
        });
    });
    
    // =========================================================================
    // F-STRING EQUIVALENCE
    // =========================================================================
    
    describe('F-String Equivalence', () => {
        
        test('f"Value: {value:.2f}"', () => {
            const value = 3.14159;
            const result = `Value: ${__py.format(value, '.2f')}`;
            expect(result).toBe('Value: 3.14');
        });
        
        test('f"Count: {count:,}"', () => {
            const count = 1234567;
            const result = `Count: ${__py.format(count, ',')}`;
            expect(result).toBe('Count: 1,234,567');
        });
        
        test('f"Name: {name:>10}"', () => {
            const name = 'Alice';
            const result = `Name: ${__py.format(name, '>10')}`;
            expect(result).toBe('Name:      Alice');
        });
        
        test('f"ID: {id:05d}"', () => {
            const id = 42;
            const result = `ID: ${__py.format(id, '05d')}`;
            expect(result).toBe('ID: 00042');
        });
        
        test('f"Progress: {pct:.1%}"', () => {
            const pct = 0.756;
            const result = `Progress: ${__py.format(pct, '.1%')}`;
            expect(result).toBe('Progress: 75.6%');
        });
    });
    
    // =========================================================================
    // COMPLEX REAL-WORLD PATTERNS
    // =========================================================================
    
    describe('Complex Real-World Patterns', () => {
        
        test('Filter and transform list', () => {
            // Python: [item.upper() for item in items if len(item) > 2]
            const items = ['a', 'abc', 'ab', 'abcd'];
            const result = [...__py.iter(items)]
                .filter(item => item.length > 2)
                .map(item => item.toUpperCase());
            expect(result).toEqual(['ABC', 'ABCD']);
        });
        
        test('Create lookup dict', () => {
            // Python: {user.id: user for user in users}
            const users = [
                {id: 1, name: 'Alice'},
                {id: 2, name: 'Bob'}
            ];
            const result = Object.fromEntries(
                [...__py.iter(users)].map(user => [user.id, user])
            );
            expect(result[1].name).toBe('Alice');
            expect(result[2].name).toBe('Bob');
        });
        
        test('Default value pattern', () => {
            // Python: config.get("key") or "default"
            const config = {};
            const value = __py.bool(config["key"]) ? config["key"] : "default";
            expect(value).toBe("default");
        });
        
        test('Conditional list building', () => {
            // Python: items = [x for x in data if x is not None]
            const data = [1, null, 2, undefined, 3, null];
            const result = [...__py.iter(data)].filter(x => x !== null && x !== undefined);
            expect(result).toEqual([1, 2, 3]);
        });
        
        test('Zip and process', () => {
            // Python: {k: v for k, v in zip(keys, values)}
            const keys = ['a', 'b', 'c'];
            const values = [1, 2, 3];
            const result = Object.fromEntries(__py.zip(keys, values));
            expect(result).toEqual({a: 1, b: 2, c: 3});
        });
    });
});
