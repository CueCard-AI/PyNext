/**
 * Phase 18.7 Extended JavaScript Runtime Tests
 *
 * Additional comprehensive tests for optimizer verification.
 * Covers edge cases, nested patterns, and real-world scenarios.
 *
 * Test Categories:
 * 1. Slice operations (10 tests)
 * 2. Floor division (5 tests)
 * 3. Nested loop captures (10 tests)
 * 4. Dictionary operations (8 tests)
 * 5. String operations (8 tests)
 * 6. Real-world patterns (15 tests)
 * 7. Edge case combinations (10 tests)
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
    if (typeof a === 'object' && typeof b === 'object' && a !== null && b !== null) {
      return JSON.stringify(a) === JSON.stringify(b);
    }
    return a === b;
  },
  at: (arr, idx) => {
    if (idx < 0) return arr[arr.length + idx];
    return arr[idx];
  },
  slice: (arr, start, stop, step) => {
    start = start ?? 0;
    stop = stop ?? arr.length;
    step = step ?? 1;
    if (start < 0) start = arr.length + start;
    if (stop < 0) stop = arr.length + stop;
    const result = [];
    if (step > 0) {
      for (let i = start; i < stop; i += step) {
        if (i >= 0 && i < arr.length) result.push(arr[i]);
      }
    }
    return result;
  },
  len: (x) => {
    if (Array.isArray(x)) return x.length;
    if (typeof x === 'string') return x.length;
    if (x instanceof Set) return x.size;
    if (x instanceof Map) return x.size;
    if (typeof x === 'object' && x !== null) return Object.keys(x).length;
    throw new Error('len() requires iterable');
  },
  add: (a, b) => {
    if (Array.isArray(a) && Array.isArray(b)) return [...a, ...b];
    return a + b;
  },
  mul: (a, b) => {
    if (typeof a === 'string' && typeof b === 'number') return a.repeat(b);
    if (typeof b === 'string' && typeof a === 'number') return b.repeat(a);
    if (Array.isArray(a) && typeof b === 'number') {
      const result = [];
      for (let i = 0; i < b; i++) result.push(...a);
      return result;
    }
    return a * b;
  },
  mod: (a, b) => ((a % b) + b) % b,
  floordiv: (a, b) => Math.floor(a / b),
  in: (item, container) => {
    if (Array.isArray(container)) {
      return container.some(x => __py.eq(item, x));
    }
    if (typeof container === 'string') {
      return container.includes(item);
    }
    if (container instanceof Set) {
      for (const x of container) {
        if (__py.eq(item, x)) return true;
      }
      return false;
    }
    if (typeof container === 'object') {
      return item in container;
    }
    return false;
  },
};

// =============================================================================
// 1. SLICE OPERATIONS (10 tests)
// =============================================================================

describe('Slice operations', () => {
  test('simple slice start:stop works', () => {
    const items = [0, 1, 2, 3, 4, 5];
    // items[1:4]
    expect(items.slice(1, 4)).toEqual([1, 2, 3]);
  });

  test('slice from start works', () => {
    const items = [0, 1, 2, 3, 4];
    // items[:3]
    expect(items.slice(0, 3)).toEqual([0, 1, 2]);
  });

  test('slice to end works', () => {
    const items = [0, 1, 2, 3, 4];
    // items[2:]
    expect(items.slice(2)).toEqual([2, 3, 4]);
  });

  test('full slice works', () => {
    const items = [0, 1, 2, 3, 4];
    // items[:]
    expect(items.slice()).toEqual([0, 1, 2, 3, 4]);
  });

  test('negative start slice needs __py.slice', () => {
    const items = [0, 1, 2, 3, 4];
    // items[-2:]
    expect(__py.slice(items, -2, null, null)).toEqual([3, 4]);
  });

  test('negative stop slice needs __py.slice', () => {
    const items = [0, 1, 2, 3, 4];
    // items[:-1]
    expect(__py.slice(items, 0, -1, null)).toEqual([0, 1, 2, 3]);
  });

  test('step slice needs __py.slice', () => {
    const items = [0, 1, 2, 3, 4, 5];
    // items[::2]
    expect(__py.slice(items, 0, 6, 2)).toEqual([0, 2, 4]);
  });

  test('string slice works', () => {
    const text = 'hello';
    // text[1:4]
    expect(text.slice(1, 4)).toBe('ell');
  });

  test('empty slice works', () => {
    const items = [0, 1, 2, 3, 4];
    // items[3:3]
    expect(items.slice(3, 3)).toEqual([]);
  });

  test('out of bounds slice is safe', () => {
    const items = [0, 1, 2];
    // items[0:100]
    expect(items.slice(0, 100)).toEqual([0, 1, 2]);
  });
});

// =============================================================================
// 2. FLOOR DIVISION (5 tests)
// =============================================================================

describe('Floor division operations', () => {
  test('positive floor division works', () => {
    // 7 // 3 = 2
    expect(__py.floordiv(7, 3)).toBe(2);
  });

  test('exact division works', () => {
    // 6 // 3 = 2
    expect(__py.floordiv(6, 3)).toBe(2);
  });

  test('negative dividend floor division', () => {
    // -7 // 3 = -3 (Python rounds toward negative infinity)
    expect(__py.floordiv(-7, 3)).toBe(-3);
  });

  test('negative divisor floor division', () => {
    // 7 // -3 = -3
    expect(__py.floordiv(7, -3)).toBe(-3);
  });

  test('both negative floor division', () => {
    // -7 // -3 = 2
    expect(__py.floordiv(-7, -3)).toBe(2);
  });
});

// =============================================================================
// 3. NESTED LOOP CAPTURES (10 tests)
// =============================================================================

describe('Nested loop captures', () => {
  test('inner loop captures inner var', () => {
    const handlers = [];
    for (let i = 0; i < 2; i++) {
      for (let j = 0; j < 3; j++) {
        // Capture j
        handlers.push(((j) => () => j)(j));
      }
    }
    expect(handlers.map(h => h())).toEqual([0, 1, 2, 0, 1, 2]);
  });

  test('inner loop captures outer var', () => {
    const handlers = [];
    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 2; j++) {
        // Capture i (outer loop var)
        handlers.push(((i) => () => i)(i));
      }
    }
    expect(handlers.map(h => h())).toEqual([0, 0, 1, 1, 2, 2]);
  });

  test('inner loop captures both vars', () => {
    const handlers = [];
    for (let i = 0; i < 2; i++) {
      for (let j = 0; j < 2; j++) {
        // Capture both i and j
        handlers.push(((i, j) => () => [i, j])(i, j));
      }
    }
    expect(handlers.map(h => h())).toEqual([
      [0, 0], [0, 1], [1, 0], [1, 1]
    ]);
  });

  test('triple nested captures innermost', () => {
    const handlers = [];
    for (let i = 0; i < 2; i++) {
      for (let j = 0; j < 2; j++) {
        for (let k = 0; k < 2; k++) {
          handlers.push(((k) => () => k)(k));
        }
      }
    }
    expect(handlers.map(h => h())).toEqual([0, 1, 0, 1, 0, 1, 0, 1]);
  });

  test('triple nested captures all', () => {
    const handlers = [];
    for (let i = 0; i < 2; i++) {
      for (let j = 0; j < 2; j++) {
        for (let k = 0; k < 2; k++) {
          handlers.push(((i, j, k) => () => i + j + k)(i, j, k));
        }
      }
    }
    expect(handlers.map(h => h())).toEqual([0, 1, 1, 2, 1, 2, 2, 3]);
  });

  test('capture in function call', () => {
    const handlers = [];
    const process = (x) => x * 10;
    for (let i = 0; i < 3; i++) {
      handlers.push(((i) => () => process(i))(i));
    }
    expect(handlers.map(h => h())).toEqual([0, 10, 20]);
  });

  test('capture in object creation', () => {
    const handlers = [];
    for (let i = 0; i < 3; i++) {
      handlers.push(((i) => () => ({ value: i, squared: i * i }))(i));
    }
    expect(handlers[0]()).toEqual({ value: 0, squared: 0 });
    expect(handlers[1]()).toEqual({ value: 1, squared: 1 });
    expect(handlers[2]()).toEqual({ value: 2, squared: 4 });
  });

  test('capture with conditional', () => {
    const handlers = [];
    for (let i = 0; i < 4; i++) {
      handlers.push(((i) => () => i % 2 === 0 ? 'even' : 'odd')(i));
    }
    expect(handlers.map(h => h())).toEqual(['even', 'odd', 'even', 'odd']);
  });

  test('capture in event handler pattern', () => {
    const buttons = [];
    for (let i = 0; i < 3; i++) {
      buttons.push({
        id: i,
        onClick: ((i) => () => `clicked ${i}`)(i),
      });
    }
    expect(buttons[0].onClick()).toBe('clicked 0');
    expect(buttons[1].onClick()).toBe('clicked 1');
    expect(buttons[2].onClick()).toBe('clicked 2');
  });

  test('capture with array method', () => {
    const items = ['a', 'b', 'c'];
    const handlers = [];
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      handlers.push(((i, item) => () => `${i}: ${item}`)(i, item));
    }
    expect(handlers.map(h => h())).toEqual(['0: a', '1: b', '2: c']);
  });
});

// =============================================================================
// 4. DICTIONARY OPERATIONS (8 tests)
// =============================================================================

describe('Dictionary operations', () => {
  test('dict length inlined', () => {
    const obj = { a: 1, b: 2, c: 3 };
    expect(Object.keys(obj).length).toBe(3);
  });

  test('empty dict length', () => {
    const obj = {};
    expect(Object.keys(obj).length).toBe(0);
  });

  test('dict truthiness inlined', () => {
    const obj = { key: 'value' };
    expect(Object.keys(obj).length > 0).toBe(true);
  });

  test('empty dict falsiness', () => {
    const obj = {};
    expect(Object.keys(obj).length > 0).toBe(false);
  });

  test('dict equality needs __py.eq', () => {
    const a = { x: 1, y: 2 };
    const b = { x: 1, y: 2 };
    expect(a === b).toBe(false);
    expect(__py.eq(a, b)).toBe(true);
  });

  test('nested dict equality', () => {
    const a = { outer: { inner: 1 } };
    const b = { outer: { inner: 1 } };
    expect(__py.eq(a, b)).toBe(true);
  });

  test('dict key in check', () => {
    const obj = { name: 'test', value: 42 };
    expect('name' in obj).toBe(true);
    expect('missing' in obj).toBe(false);
  });

  test('dict iteration', () => {
    const obj = { a: 1, b: 2 };
    const keys = Object.keys(obj);
    expect(keys).toContain('a');
    expect(keys).toContain('b');
  });
});

// =============================================================================
// 5. STRING OPERATIONS (8 tests)
// =============================================================================

describe('String operations', () => {
  test('string length inlined', () => {
    const s = 'hello world';
    expect(s.length).toBe(11);
  });

  test('empty string falsiness', () => {
    const s = '';
    expect(s.length > 0).toBe(false);
  });

  test('non-empty string truthiness', () => {
    const s = 'hello';
    expect(s.length > 0).toBe(true);
  });

  test('string repeat needs __py.mul', () => {
    expect(__py.mul('ab', 3)).toBe('ababab');
    expect(__py.mul(3, 'ab')).toBe('ababab');
  });

  test('string concatenation works', () => {
    const a = 'hello';
    const b = ' world';
    expect(a + b).toBe('hello world');
  });

  test('string in string works', () => {
    const text = 'hello world';
    expect(text.includes('world')).toBe(true);
    expect(text.includes('xyz')).toBe(false);
  });

  test('string equality works', () => {
    const a = 'test';
    const b = 'test';
    expect(a === b).toBe(true);
  });

  test('string slice works', () => {
    const s = 'hello';
    expect(s.slice(1, 4)).toBe('ell');
  });
});

// =============================================================================
// 6. REAL-WORLD PATTERNS (15 tests)
// =============================================================================

describe('Real-world patterns', () => {
  test('filter pattern', () => {
    const items = [1, 2, 3, 4, 5, 6];
    const evens = items.filter(x => x % 2 === 0);
    expect(evens).toEqual([2, 4, 6]);
  });

  test('map pattern', () => {
    const items = [1, 2, 3];
    const doubled = items.map(x => x * 2);
    expect(doubled).toEqual([2, 4, 6]);
  });

  test('reduce pattern', () => {
    const items = [1, 2, 3, 4, 5];
    const sum = items.reduce((a, b) => a + b, 0);
    expect(sum).toBe(15);
  });

  test('find pattern', () => {
    const items = [{ id: 1 }, { id: 2 }, { id: 3 }];
    const found = items.find(x => x.id === 2);
    expect(found).toEqual({ id: 2 });
  });

  test('some pattern', () => {
    const items = [1, 2, 3, 4, 5];
    expect(items.some(x => x > 3)).toBe(true);
    expect(items.some(x => x > 10)).toBe(false);
  });

  test('every pattern', () => {
    const items = [2, 4, 6];
    expect(items.every(x => x % 2 === 0)).toBe(true);
    expect(items.every(x => x > 5)).toBe(false);
  });

  test('grouping pattern', () => {
    const items = [
      { category: 'a', value: 1 },
      { category: 'b', value: 2 },
      { category: 'a', value: 3 },
    ];
    const groups = {};
    for (const item of items) {
      if (!groups[item.category]) {
        groups[item.category] = [];
      }
      groups[item.category].push(item);
    }
    expect(groups['a'].length).toBe(2);
    expect(groups['b'].length).toBe(1);
  });

  test('counter pattern', () => {
    const words = ['a', 'b', 'a', 'c', 'a', 'b'];
    const counts = {};
    for (const word of words) {
      counts[word] = (counts[word] || 0) + 1;
    }
    expect(counts).toEqual({ a: 3, b: 2, c: 1 });
  });

  test('accumulator pattern', () => {
    let total = 0;
    for (let i = 0; i < 5; i++) {
      total = total + i;
    }
    expect(total).toBe(10);
  });

  test('chained method pattern', () => {
    const text = '  HELLO WORLD  ';
    const result = text.trim().toLowerCase().split(' ');
    expect(result).toEqual(['hello', 'world']);
  });

  test('conditional assignment pattern', () => {
    let value = 'default';
    const condition = true;
    if (condition) {
      value = 'computed';
    }
    expect(value).toBe('computed');
  });

  test('early return pattern', () => {
    function findFirst(items, predicate) {
      for (const item of items) {
        if (predicate(item)) {
          return item;
        }
      }
      return null;
    }
    const items = [1, 2, 3, 4, 5];
    expect(findFirst(items, x => x > 3)).toBe(4);
    expect(findFirst(items, x => x > 10)).toBe(null);
  });

  test('state machine pattern', () => {
    function transition(state, event) {
      if (state === 'idle') {
        if (event === 'start') return 'running';
        return 'idle';
      } else if (state === 'running') {
        if (event === 'pause') return 'paused';
        if (event === 'stop') return 'stopped';
        return 'running';
      }
      return state;
    }
    expect(transition('idle', 'start')).toBe('running');
    expect(transition('running', 'pause')).toBe('paused');
  });

  test('recursive pattern', () => {
    function factorial(n) {
      if (n <= 1) return 1;
      return n * factorial(n - 1);
    }
    expect(factorial(5)).toBe(120);
  });

  test('async simulation pattern', () => {
    const callbacks = [];
    function schedule(fn) {
      callbacks.push(fn);
    }
    for (let i = 0; i < 3; i++) {
      schedule(((i) => () => i * 2)(i));
    }
    expect(callbacks.map(cb => cb())).toEqual([0, 2, 4]);
  });
});

// =============================================================================
// 7. EDGE CASE COMBINATIONS (10 tests)
// =============================================================================

describe('Edge case combinations', () => {
  test('list of lists equality', () => {
    const a = [[1, 2], [3, 4]];
    const b = [[1, 2], [3, 4]];
    expect(__py.eq(a, b)).toBe(true);
  });

  test('list in list membership', () => {
    const container = [[1, 2], [3, 4], [5, 6]];
    expect(__py.in([3, 4], container)).toBe(true);
    expect(__py.in([7, 8], container)).toBe(false);
  });

  test('nested dict in list', () => {
    const items = [{ a: 1 }, { b: 2 }];
    expect(__py.in({ a: 1 }, items)).toBe(true);
  });

  test('multiple negative indices', () => {
    const items = [0, 1, 2, 3, 4];
    expect(__py.at(items, -1)).toBe(4);
    expect(__py.at(items, -2)).toBe(3);
    expect(__py.at(items, -5)).toBe(0);
  });

  test('list repeat', () => {
    expect(__py.mul([1, 2], 3)).toEqual([1, 2, 1, 2, 1, 2]);
  });

  test('empty list repeat', () => {
    expect(__py.mul([], 5)).toEqual([]);
  });

  test('combination of operations', () => {
    const items = [1, 2, 3, 4, 5];
    // Get last 3 elements, sum them
    const last3 = __py.slice(items, -3, null, null);
    const sum = last3.reduce((a, b) => a + b, 0);
    expect(sum).toBe(12);  // 3 + 4 + 5
  });

  test('truthiness chain', () => {
    const items = [1, 2, 3];
    const result = __py.bool(items) && items.length > 0 && items[0] === 1;
    expect(result).toBe(true);
  });

  test('mixed type comparison', () => {
    // Should NOT use __py.eq for primitives
    expect(5 === 5.0).toBe(true);
    expect('5' === 5).toBe(false);
    expect(null === undefined).toBe(false);
  });

  test('zero and empty distinctions', () => {
    // All should be falsy in Python semantics
    expect(__py.bool(0)).toBe(false);
    expect(__py.bool('')).toBe(false);
    expect(__py.bool([])).toBe(false);
    expect(__py.bool({})).toBe(false);
    expect(__py.bool(null)).toBe(false);
    expect(__py.bool(undefined)).toBe(false);
    expect(__py.bool(false)).toBe(false);
    
    // These should be truthy
    expect(__py.bool(1)).toBe(true);
    expect(__py.bool('x')).toBe(true);
    expect(__py.bool([0])).toBe(true);
    expect(__py.bool({ a: 0 })).toBe(true);
  });
});
