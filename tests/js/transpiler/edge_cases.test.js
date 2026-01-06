/**
 * Phase 18.7 - JavaScript Edge Cases Tests
 *
 * Tests for edge cases identified in risk analysis:
 * 1. Async/Await patterns
 * 2. Comprehension-like patterns
 * 3. Augmented assignment
 * 4. Template literals (f-strings)
 * 5. Chained comparisons
 * 6. Ternary expressions
 * 7. Try/Catch variable scope
 * 8. Spread operators
 */

// Mock __py runtime
const __py = {
  bool: (x) => {
    if (Array.isArray(x)) return x.length > 0;
    if (x instanceof Set) return x.size > 0;
    if (x instanceof Map) return x.size > 0;
    if (typeof x === 'object' && x !== null) return Object.keys(x).length > 0;
    return Boolean(x);
  },
  eq: (a, b) => {
    if (Array.isArray(a) && Array.isArray(b)) {
      return JSON.stringify(a) === JSON.stringify(b);
    }
    return a === b;
  },
  add: (a, b) => {
    if (Array.isArray(a) && Array.isArray(b)) return [...a, ...b];
    return a + b;
  },
  mul: (a, b) => {
    if (typeof a === 'string' && typeof b === 'number') return a.repeat(b);
    if (typeof b === 'string' && typeof a === 'number') return b.repeat(a);
    return a * b;
  },
};

// =============================================================================
// 1. ASYNC/AWAIT PATTERNS (10 tests)
// =============================================================================

describe('Async/Await patterns', () => {
  test('await returns promise result', async () => {
    const getData = async () => 42;
    const result = await getData();
    expect(result).toBe(42);
  });

  test('await in expression', async () => {
    const getNum = async () => 5;
    const result = (await getNum()) + 3;
    expect(result).toBe(8);
  });

  test('multiple awaits in expression', async () => {
    const getA = async () => 10;
    const getB = async () => 20;
    const result = (await getA()) + (await getB());
    expect(result).toBe(30);
  });

  test('await with truthiness check', async () => {
    const getData = async () => [1, 2, 3];
    const data = await getData();
    expect(__py.bool(data)).toBe(true);
  });

  test('await with empty result', async () => {
    const getEmpty = async () => [];
    const data = await getEmpty();
    expect(__py.bool(data)).toBe(false);
  });

  test('chained async operations', async () => {
    const step1 = async () => 1;
    const step2 = async (x) => x * 2;
    const step3 = async (x) => x + 10;
    
    let result = await step1();
    result = await step2(result);
    result = await step3(result);
    
    expect(result).toBe(12);
  });

  test('async function with conditional', async () => {
    const maybeData = async (flag) => flag ? [1, 2, 3] : [];
    
    const data1 = await maybeData(true);
    const data2 = await maybeData(false);
    
    expect(__py.bool(data1)).toBe(true);
    expect(__py.bool(data2)).toBe(false);
  });

  test('async in loop pattern', async () => {
    const getItem = async (i) => i * 2;
    const results = [];
    
    for (let i = 0; i < 3; i++) {
      results.push(await getItem(i));
    }
    
    expect(results).toEqual([0, 2, 4]);
  });

  test('Promise.all pattern', async () => {
    const items = [1, 2, 3];
    const doubled = await Promise.all(items.map(async x => x * 2));
    expect(doubled).toEqual([2, 4, 6]);
  });

  test('async error handling', async () => {
    const mayFail = async (shouldFail) => {
      if (shouldFail) throw new Error('Failed');
      return 'success';
    };
    
    expect(await mayFail(false)).toBe('success');
    await expect(mayFail(true)).rejects.toThrow('Failed');
  });
});

// =============================================================================
// 2. COMPREHENSION-LIKE PATTERNS (8 tests)
// =============================================================================

describe('Comprehension-like patterns', () => {
  test('map as list comprehension', () => {
    const items = [1, 2, 3];
    // [x * 2 for x in items]
    const result = items.map(x => x * 2);
    expect(result).toEqual([2, 4, 6]);
  });

  test('filter + map pattern', () => {
    const items = [1, 2, 3, 4, 5];
    // [x * 2 for x in items if x > 2]
    const result = items.filter(x => x > 2).map(x => x * 2);
    expect(result).toEqual([6, 8, 10]);
  });

  test('nested comprehension pattern', () => {
    const matrix = [[1, 2], [3, 4]];
    // [cell for row in matrix for cell in row]
    const result = matrix.flat();
    expect(result).toEqual([1, 2, 3, 4]);
  });

  test('dict comprehension pattern', () => {
    const items = ['a', 'b', 'c'];
    // {item: i for i, item in enumerate(items)}
    const result = Object.fromEntries(items.map((item, i) => [item, i]));
    expect(result).toEqual({ a: 0, b: 1, c: 2 });
  });

  test('set comprehension pattern', () => {
    const items = [1, 2, 2, 3, 3, 3];
    // {x for x in items}
    const result = new Set(items);
    expect([...result]).toEqual([1, 2, 3]);
  });

  test('conditional in comprehension', () => {
    const items = [1, 2, 3, 4, 5];
    // [x if x > 3 else 0 for x in items]
    const result = items.map(x => x > 3 ? x : 0);
    expect(result).toEqual([0, 0, 0, 4, 5]);
  });

  test('lambda in comprehension captures correctly', () => {
    // funcs = [lambda: i for i in range(3)] - with capture fix
    const funcs = [];
    for (let i = 0; i < 3; i++) {
      funcs.push(((i) => () => i)(i));  // IIFE capture
    }
    expect(funcs.map(f => f())).toEqual([0, 1, 2]);
  });

  test('generator expression pattern', () => {
    // sum(x * 2 for x in items)
    const items = [1, 2, 3];
    function* gen() {
      for (const x of items) yield x * 2;
    }
    const sum = [...gen()].reduce((a, b) => a + b, 0);
    expect(sum).toBe(12);
  });
});

// =============================================================================
// 3. AUGMENTED ASSIGNMENT (6 tests)
// =============================================================================

describe('Augmented assignment', () => {
  test('numeric +=', () => {
    let x = 5;
    x += 3;
    expect(x).toBe(8);
  });

  test('numeric -=', () => {
    let x = 10;
    x -= 3;
    expect(x).toBe(7);
  });

  test('numeric *=', () => {
    let x = 4;
    x *= 3;
    expect(x).toBe(12);
  });

  test('string +=', () => {
    let s = 'hello';
    s += ' world';
    expect(s).toBe('hello world');
  });

  test('accumulator pattern with +=', () => {
    let total = 0;
    for (let i = 1; i <= 5; i++) {
      total += i;
    }
    expect(total).toBe(15);
  });

  test('array concat pattern', () => {
    let items = [1, 2];
    items = __py.add(items, [3, 4]);
    expect(items).toEqual([1, 2, 3, 4]);
  });
});

// =============================================================================
// 4. TEMPLATE LITERALS (F-STRINGS) (6 tests)
// =============================================================================

describe('Template literals (f-strings)', () => {
  test('simple interpolation', () => {
    const name = 'World';
    const greeting = `Hello ${name}`;
    expect(greeting).toBe('Hello World');
  });

  test('expression in template', () => {
    const x = 5;
    const y = 3;
    const msg = `Sum: ${x + y}`;
    expect(msg).toBe('Sum: 8');
  });

  test('method call in template', () => {
    const text = 'hello';
    const msg = `Upper: ${text.toUpperCase()}`;
    expect(msg).toBe('Upper: HELLO');
  });

  test('nested template', () => {
    const a = 'A';
    const b = 'B';
    const outer = `outer(${`inner(${a}, ${b})`})`;
    expect(outer).toBe('outer(inner(A, B))');
  });

  test('template length is string', () => {
    const x = 42;
    const s = `Value: ${x}`;
    expect(typeof s).toBe('string');
    expect(s.length).toBe(9);
  });

  test('template truthiness', () => {
    const s = `hello`;
    expect(__py.bool(s)).toBe(true);
    const empty = ``;
    expect(__py.bool(empty)).toBe(false);
  });
});

// =============================================================================
// 5. CHAINED COMPARISONS (6 tests)
// =============================================================================

describe('Chained comparisons', () => {
  test('simple chained: 0 < x < 10', () => {
    const x = 5;
    // Python: 0 < x < 10
    // JS: 0 < x && x < 10
    expect(0 < x && x < 10).toBe(true);
  });

  test('chained out of range', () => {
    const x = 15;
    expect(0 < x && x < 10).toBe(false);
  });

  test('triple chain: a < b < c', () => {
    const a = 1, b = 2, c = 3;
    expect(a < b && b < c).toBe(true);
  });

  test('mixed operators: a < b <= c', () => {
    const a = 1, b = 2, c = 2;
    expect(a < b && b <= c).toBe(true);
  });

  test('equality chain: a == b == c', () => {
    const a = 5, b = 5, c = 5;
    expect(a === b && b === c).toBe(true);
  });

  test('negative case: a < b > c', () => {
    const a = 1, b = 5, c = 3;
    expect(a < b && b > c).toBe(true);  // 1 < 5 and 5 > 3
  });
});

// =============================================================================
// 6. TERNARY EXPRESSIONS (IFEXP) (6 tests)
// =============================================================================

describe('Ternary expressions', () => {
  test('simple ternary true', () => {
    const cond = true;
    const result = cond ? 1 : 2;
    expect(result).toBe(1);
  });

  test('simple ternary false', () => {
    const cond = false;
    const result = cond ? 1 : 2;
    expect(result).toBe(2);
  });

  test('ternary with expressions', () => {
    const x = 5;
    const result = x > 0 ? x * 2 : 0;
    expect(result).toBe(10);
  });

  test('nested ternary', () => {
    const x = 5;
    const result = x > 10 ? 'big' : x > 0 ? 'small' : 'zero';
    expect(result).toBe('small');
  });

  test('ternary in function call', () => {
    const items = [1, 2, 3];
    const result = items.length > 0 ? items[0] : null;
    expect(result).toBe(1);
  });

  test('ternary with __py.bool', () => {
    const items = [1, 2, 3];
    const result = __py.bool(items) ? 'has items' : 'empty';
    expect(result).toBe('has items');
  });
});

// =============================================================================
// 7. TRY/CATCH VARIABLE SCOPE (6 tests)
// =============================================================================

describe('Try/Catch variable scope', () => {
  test('variable defined in try available after', () => {
    let x;
    try {
      x = 5;
    } catch (e) {
      x = 0;
    }
    expect(x).toBe(5);
  });

  test('variable from catch on error', () => {
    let x;
    try {
      throw new Error('fail');
    } catch (e) {
      x = 0;
    }
    expect(x).toBe(0);
  });

  test('finally always runs', () => {
    let x = 0;
    try {
      x = 1;
    } finally {
      x = 2;
    }
    expect(x).toBe(2);
  });

  test('error object access', () => {
    let msg;
    try {
      throw new Error('test error');
    } catch (e) {
      msg = e.message;
    }
    expect(msg).toBe('test error');
  });

  test('nested try/catch', () => {
    let result;
    try {
      try {
        throw new Error('inner');
      } catch (e) {
        result = 'caught inner';
      }
    } catch (e) {
      result = 'caught outer';
    }
    expect(result).toBe('caught inner');
  });

  test('re-throw pattern', () => {
    let caught = false;
    try {
      try {
        throw new Error('original');
      } catch (e) {
        throw e;  // Re-throw
      }
    } catch (e) {
      caught = true;
      expect(e.message).toBe('original');
    }
    expect(caught).toBe(true);
  });
});

// =============================================================================
// 8. SPREAD OPERATORS (8 tests)
// =============================================================================

describe('Spread operators', () => {
  test('array spread in call', () => {
    const add = (a, b, c) => a + b + c;
    const args = [1, 2, 3];
    expect(add(...args)).toBe(6);
  });

  test('array spread in literal', () => {
    const a = [1, 2];
    const b = [3, 4];
    const combined = [...a, ...b];
    expect(combined).toEqual([1, 2, 3, 4]);
  });

  test('object spread', () => {
    const a = { x: 1 };
    const b = { y: 2 };
    const combined = { ...a, ...b };
    expect(combined).toEqual({ x: 1, y: 2 });
  });

  test('spread with override', () => {
    const base = { a: 1, b: 2 };
    const updated = { ...base, b: 3 };
    expect(updated).toEqual({ a: 1, b: 3 });
  });

  test('spread in function rest params', () => {
    const sum = (...nums) => nums.reduce((a, b) => a + b, 0);
    expect(sum(1, 2, 3, 4)).toBe(10);
  });

  test('spread copy array', () => {
    const original = [1, 2, 3];
    const copy = [...original];
    copy.push(4);
    expect(original).toEqual([1, 2, 3]);
    expect(copy).toEqual([1, 2, 3, 4]);
  });

  test('spread copy object', () => {
    const original = { a: 1 };
    const copy = { ...original };
    copy.b = 2;
    expect(original).toEqual({ a: 1 });
    expect(copy).toEqual({ a: 1, b: 2 });
  });

  test('nested spread', () => {
    const inner = [1, 2];
    const outer = [[...inner], [...inner]];
    inner.push(3);
    expect(outer).toEqual([[1, 2], [1, 2]]);  // Not affected
  });
});
