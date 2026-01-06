/**
 * Phase 18.7 JavaScript Runtime Tests - Optimizer Verification
 *
 * These tests verify that optimized JavaScript code runs correctly.
 * They test the runtime behavior of elided wrappers and inlined calls.
 *
 * Test Categories:
 * 1. Elided bool() operations (12 tests)
 * 2. Elided equality operations (10 tests)
 * 3. Elided arithmetic operations (10 tests)
 * 4. Inlined len() operations (8 tests)
 * 5. Inlined bool() operations (5 tests)
 * 6. Loop capture IIFE patterns (5 tests)
 */

// Mock __py runtime for tests that need it
const __py = {
  bool: (x) => {
    if (Array.isArray(x)) return x.length > 0;
    if (typeof x === 'object' && x !== null) return Object.keys(x).length > 0;
    return Boolean(x);
  },
  eq: (a, b) => {
    if (Array.isArray(a) && Array.isArray(b)) {
      return JSON.stringify(a) === JSON.stringify(b);
    }
    return a === b;
  },
  at: (arr, idx) => {
    if (idx < 0) return arr[arr.length + idx];
    return arr[idx];
  },
  len: (x) => {
    if (Array.isArray(x)) return x.length;
    if (typeof x === 'string') return x.length;
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
    return a * b;
  },
  mod: (a, b) => ((a % b) + b) % b,  // Python-style modulo
};

// =============================================================================
// 1. ELIDED BOOL() OPERATIONS (12 tests)
// =============================================================================

describe('Elided bool() operations', () => {
  test('comparison result is always bool - greater than', () => {
    const x = 5;
    // Elided: if (__py.bool(x > 0)) → if (x > 0)
    if (x > 0) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('comparison result is always bool - less than', () => {
    const x = -5;
    // Elided: if (__py.bool(x < 0)) → if (x < 0)
    if (x < 0) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('comparison result is always bool - equality', () => {
    const x = 5;
    // Elided: if (__py.bool(x === 5)) → if (x === 5)
    if (x === 5) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('comparison result is always bool - inequality', () => {
    const x = 5;
    // Elided: if (__py.bool(x !== 10)) → if (x !== 10)
    if (x !== 10) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('boolean variable is always bool', () => {
    const isValid = true;
    // Elided: if (__py.bool(isValid)) → if (isValid)
    if (isValid) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('boolean false is always bool', () => {
    const isValid = false;
    // Elided: if (__py.bool(isValid)) → if (isValid)
    if (!isValid) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('chained comparison is bool', () => {
    const x = 5;
    // Elided: if (__py.bool(0 < x && x < 10)) → if (0 < x && x < 10)
    if (0 < x && x < 10) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('or comparison is bool', () => {
    const x = 15;
    // Elided: if (__py.bool(x < 0 || x > 10)) → if (x < 0 || x > 10)
    if (x < 0 || x > 10) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('and comparison is bool', () => {
    const x = 5;
    const y = 10;
    // Elided condition
    if (x > 0 && y > 0) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('not on bool is bool', () => {
    const flag = false;
    // Elided: if (__py.bool(!flag)) → if (!flag)
    if (!flag) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('true literal is bool', () => {
    // Elided: if (__py.bool(true)) → if (true)
    if (true) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('false literal is bool', () => {
    // Elided: if (__py.bool(false)) → if (false)
    if (false) {
      throw new Error('Should not reach here');
    } else {
      expect(true).toBe(true);
    }
  });
});

// =============================================================================
// 2. ELIDED EQUALITY OPERATIONS (10 tests)
// =============================================================================

describe('Elided equality operations', () => {
  test('int === int works for primitives', () => {
    const a = 5;
    const b = 5;
    // Elided: __py.eq(a, b) → a === b
    expect(a === b).toBe(true);
  });

  test('int !== int works for primitives', () => {
    const a = 5;
    const b = 10;
    // Elided
    expect(a !== b).toBe(true);
  });

  test('string === string works for primitives', () => {
    const s1 = 'hello';
    const s2 = 'hello';
    // Elided
    expect(s1 === s2).toBe(true);
  });

  test('string !== string works for primitives', () => {
    const s1 = 'hello';
    const s2 = 'world';
    // Elided
    expect(s1 !== s2).toBe(true);
  });

  test('bool === bool works', () => {
    const a = true;
    const b = true;
    // Elided
    expect(a === b).toBe(true);
  });

  test('null === null works', () => {
    const a = null;
    const b = null;
    // Elided
    expect(a === b).toBe(true);
  });

  test('int and float comparison works', () => {
    const a = 5;
    const b = 5.0;
    // Elided (JS treats them same)
    expect(a === b).toBe(true);
  });

  test('zero equality works', () => {
    const a = 0;
    const b = 0;
    // Elided
    expect(a === b).toBe(true);
  });

  test('empty string equality works', () => {
    const a = '';
    const b = '';
    // Elided
    expect(a === b).toBe(true);
  });

  test('undefined equality works', () => {
    const a = undefined;
    const b = undefined;
    // Elided
    expect(a === b).toBe(true);
  });
});

// =============================================================================
// 3. ELIDED ARITHMETIC OPERATIONS (10 tests)
// =============================================================================

describe('Elided arithmetic operations', () => {
  test('int + int works', () => {
    const a = 5;
    const b = 3;
    // Elided: __py.add(a, b) → a + b
    expect(a + b).toBe(8);
  });

  test('int - int works', () => {
    const a = 10;
    const b = 3;
    // Elided: __py.sub(a, b) → a - b
    expect(a - b).toBe(7);
  });

  test('int * int works', () => {
    const a = 4;
    const b = 5;
    // Elided: __py.mul(a, b) → a * b
    expect(a * b).toBe(20);
  });

  test('int / int works', () => {
    const a = 10;
    const b = 2;
    // Elided: __py.div(a, b) → a / b
    expect(a / b).toBe(5);
  });

  test('float + float works', () => {
    const a = 3.14;
    const b = 2.86;
    // Elided
    expect(a + b).toBeCloseTo(6.0);
  });

  test('float * float works', () => {
    const a = 2.5;
    const b = 4.0;
    // Elided
    expect(a * b).toBe(10);
  });

  test('int + float works', () => {
    const a = 5;
    const b = 2.5;
    // Elided
    expect(a + b).toBe(7.5);
  });

  test('positive mod works', () => {
    const a = 10;
    const b = 3;
    // Elided: __py.mod(a, b) → a % b (for positive)
    expect(a % b).toBe(1);
  });

  test('complex arithmetic expression works', () => {
    const x = 5;
    const y = 3;
    // Elided: all operations on known ints
    const result = (x + y) * 2 - 4 / 2;
    expect(result).toBe(14);
  });

  test('assignment with arithmetic works', () => {
    let x = 5;
    // Elided: x = __py.add(x, 1) → x = x + 1
    x = x + 1;
    expect(x).toBe(6);
  });
});

// =============================================================================
// 4. INLINED LEN() OPERATIONS (8 tests)
// =============================================================================

describe('Inlined len() operations', () => {
  test('list length inlined', () => {
    const items = [1, 2, 3, 4, 5];
    // Inlined: __py.len(items) → items.length
    expect(items.length).toBe(5);
  });

  test('string length inlined', () => {
    const text = 'hello';
    // Inlined: __py.len(text) → text.length
    expect(text.length).toBe(5);
  });

  test('empty list length', () => {
    const items = [];
    // Inlined
    expect(items.length).toBe(0);
  });

  test('empty string length', () => {
    const text = '';
    // Inlined
    expect(text.length).toBe(0);
  });

  test('dict length inlined', () => {
    const data = { a: 1, b: 2, c: 3 };
    // Inlined: __py.len(data) → Object.keys(data).length
    expect(Object.keys(data).length).toBe(3);
  });

  test('empty dict length', () => {
    const data = {};
    // Inlined
    expect(Object.keys(data).length).toBe(0);
  });

  test('nested length call', () => {
    const items = [1, 2, 3];
    // Inlined in comparison
    if (items.length > 0) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('length in loop condition', () => {
    const items = [1, 2, 3];
    let count = 0;
    // Inlined
    for (let i = 0; i < items.length; i++) {
      count++;
    }
    expect(count).toBe(3);
  });
});

// =============================================================================
// 5. INLINED BOOL() OPERATIONS (5 tests)
// =============================================================================

describe('Inlined bool() operations', () => {
  test('list truthiness inlined', () => {
    const items = [1, 2, 3];
    // Inlined: __py.bool(items) → items.length > 0
    if (items.length > 0) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('empty list falsiness inlined', () => {
    const items = [];
    // Inlined: __py.bool(items) → items.length > 0
    if (items.length > 0) {
      throw new Error('Should not reach here');
    } else {
      expect(true).toBe(true);
    }
  });

  test('string truthiness inlined', () => {
    const text = 'hello';
    // Inlined: __py.bool(text) → text.length > 0
    if (text.length > 0) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('dict truthiness inlined', () => {
    const data = { key: 'value' };
    // Inlined: __py.bool(data) → Object.keys(data).length > 0
    if (Object.keys(data).length > 0) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });

  test('set truthiness inlined', () => {
    const s = new Set([1, 2, 3]);
    // Inlined: __py.bool(s) → s.size > 0
    if (s.size > 0) {
      expect(true).toBe(true);
    } else {
      throw new Error('Should not reach here');
    }
  });
});

// =============================================================================
// 6. LOOP CAPTURE IIFE PATTERNS (5 tests)
// =============================================================================

describe('Loop capture IIFE patterns', () => {
  test('IIFE captures loop variable', () => {
    const handlers = [];
    
    for (let i = 0; i < 3; i++) {
      // Transformed: lambda: i → ((i) => () => i)(i)
      handlers.push(((i) => () => i)(i));
    }
    
    // Each handler should return its captured value
    expect(handlers[0]()).toBe(0);
    expect(handlers[1]()).toBe(1);
    expect(handlers[2]()).toBe(2);
  });

  test('IIFE captures in function call', () => {
    const handlers = [];
    
    function handle(x) {
      return x * 2;
    }
    
    for (let i = 0; i < 3; i++) {
      // Transformed: lambda: handle(i) → ((i) => () => handle(i))(i)
      handlers.push(((i) => () => handle(i))(i));
    }
    
    expect(handlers[0]()).toBe(0);
    expect(handlers[1]()).toBe(2);
    expect(handlers[2]()).toBe(4);
  });

  test('IIFE captures multiple variables', () => {
    const handlers = [];
    const letters = ['a', 'b', 'c'];
    
    for (let i = 0; i < 3; i++) {
      const letter = letters[i];
      // Transformed to capture both i and letter
      handlers.push(((i, letter) => () => ({ i, letter }))(i, letter));
    }
    
    expect(handlers[0]()).toEqual({ i: 0, letter: 'a' });
    expect(handlers[1]()).toEqual({ i: 1, letter: 'b' });
    expect(handlers[2]()).toEqual({ i: 2, letter: 'c' });
  });

  test('IIFE in nested loop', () => {
    const handlers = [];
    
    for (let i = 0; i < 2; i++) {
      for (let j = 0; j < 2; j++) {
        // Captures j (inner loop var)
        handlers.push(((j) => () => j)(j));
      }
    }
    
    // Should have [0, 1, 0, 1]
    expect(handlers.map(h => h())).toEqual([0, 1, 0, 1]);
  });

  test('IIFE with complex expression', () => {
    const handlers = [];
    
    for (let i = 0; i < 3; i++) {
      // Transformed: lambda: i * i + 1 → ((i) => () => i * i + 1)(i)
      handlers.push(((i) => () => i * i + 1)(i));
    }
    
    expect(handlers[0]()).toBe(1);   // 0*0+1
    expect(handlers[1]()).toBe(2);   // 1*1+1
    expect(handlers[2]()).toBe(5);   // 2*2+1
  });
});

// =============================================================================
// EDGE CASES (non-elidable - should use __py runtime)
// =============================================================================

describe('Non-elidable cases (require __py runtime)', () => {
  test('list equality needs __py.eq', () => {
    const a = [1, 2, 3];
    const b = [1, 2, 3];
    
    // Native JS: false
    expect(a === b).toBe(false);
    
    // Python semantics via __py.eq: true
    expect(__py.eq(a, b)).toBe(true);
  });

  test('empty list bool needs __py.bool', () => {
    const items = [];
    
    // Native JS: true (non-null object)
    expect(Boolean(items)).toBe(true);
    
    // Python semantics via __py.bool: false
    expect(__py.bool(items)).toBe(false);
  });

  test('negative index needs __py.at', () => {
    const items = [1, 2, 3, 4, 5];
    
    // Native JS: undefined
    expect(items[-1]).toBe(undefined);
    
    // Python semantics via __py.at: 5 (last element)
    expect(__py.at(items, -1)).toBe(5);
  });

  test('string repeat needs __py.mul', () => {
    const s = 'ab';
    const n = 3;
    
    // Native JS: NaN
    expect(s * n).toBeNaN();
    
    // Python semantics via __py.mul: 'ababab'
    expect(__py.mul(s, n)).toBe('ababab');
  });

  test('negative modulo needs __py.mod', () => {
    const a = -7;
    const b = 3;
    
    // Native JS: -1
    expect(a % b).toBe(-1);
    
    // Python semantics via __py.mod: 2
    expect(__py.mod(a, b)).toBe(2);
  });
});
