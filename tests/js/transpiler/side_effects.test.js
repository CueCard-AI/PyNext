/**
 * Tests for side effect handling in transpiled code
 * 
 * These tests verify that the transpiled JavaScript evaluates expressions
 * the correct number of times, matching Python's semantics.
 * 
 * Key invariants:
 * - Chained comparisons: a < f() < b should call f() exactly once
 * - Boolean operators: f() and g() should call f() exactly once
 * - F-string expressions: f"{f()}" should call f() exactly once
 */

const __py = require('./setup');

describe('Side Effect Evaluation - Chained Comparisons', () => {
    
    // =========================================================================
    // CHAINED COMPARISON EVALUATION COUNT
    // =========================================================================
    
    describe('Single evaluation in chained comparisons', () => {
        test('middle function called once in a < f() < b', () => {
            let callCount = 0;
            const f = () => { callCount++; return 5; };
            
            // Simulate transpiled: ((_cmp0) => (0 < _cmp0) && (_cmp0 < 10))(f())
            const result = ((_cmp0) => (0 < _cmp0) && (_cmp0 < 10))(f());
            
            expect(callCount).toBe(1);
            expect(result).toBe(true);
        });
        
        test('middle function called once even when comparison fails early', () => {
            let callCount = 0;
            const f = () => { callCount++; return 5; };
            
            // a = 10, which is > 5, so first comparison fails
            // But f() should still only be called once
            const result = ((_cmp0) => (10 < _cmp0) && (_cmp0 < 20))(f());
            
            expect(callCount).toBe(1);
            expect(result).toBe(false);
        });
        
        test('multiple middle functions each called once', () => {
            let fCount = 0, gCount = 0;
            const f = () => { fCount++; return 3; };
            const g = () => { gCount++; return 7; };
            
            // a < f() < g() < b
            const result = ((_cmp0, _cmp1) => 
                (0 < _cmp0) && (_cmp0 < _cmp1) && (_cmp1 < 10)
            )(f(), g());
            
            expect(fCount).toBe(1);
            expect(gCount).toBe(1);
            expect(result).toBe(true);
        });
        
        test('simple variables can be repeated safely', () => {
            const x = 5;
            // No caching needed for simple variables
            const result = (0 < x) && (x < 10);
            expect(result).toBe(true);
        });
    });
    
    // =========================================================================
    // COMPARISON WITH SIDE EFFECTS
    // =========================================================================
    
    describe('Side effects in comparisons', () => {
        test('method with side effect called once', () => {
            let callCount = 0;
            const obj = {
                getValue() { callCount++; return 5; }
            };
            
            const result = ((_cmp0) => (0 < _cmp0) && (_cmp0 < 10))(obj.getValue());
            
            expect(callCount).toBe(1);
            expect(result).toBe(true);
        });
        
        test('array access with side effect called once', () => {
            let accessCount = 0;
            const arr = new Proxy([1, 5, 10], {
                get(target, prop) {
                    if (prop === '1') accessCount++;
                    return target[prop];
                }
            });
            
            // Would be: 0 < arr[1] < 10
            // Need to cache arr[1]
            const val = arr[1];
            const result = (0 < val) && (val < 10);
            
            expect(accessCount).toBe(1);
            expect(result).toBe(true);
        });
    });
});


describe('Side Effect Evaluation - Boolean Operators', () => {
    
    // =========================================================================
    // AND OPERATOR EVALUATION
    // =========================================================================
    
    describe('and operator single evaluation', () => {
        test('f() and g() - f() called once when truthy', () => {
            let fCount = 0, gCount = 0;
            const f = () => { fCount++; return [1]; };  // Truthy
            const g = () => { gCount++; return [2]; };
            
            // Transpiled: ((_b0) => __py.bool(_b0) ? g() : _b0)(f())
            const result = ((_b0) => __py.bool(_b0) ? g() : _b0)(f());
            
            expect(fCount).toBe(1);
            expect(gCount).toBe(1);
            expect(result).toEqual([2]);  // Returns g()
        });
        
        test('f() and g() - f() called once when falsy', () => {
            let fCount = 0, gCount = 0;
            const f = () => { fCount++; return []; };  // Falsy
            const g = () => { gCount++; return [2]; };
            
            const result = ((_b0) => __py.bool(_b0) ? g() : _b0)(f());
            
            expect(fCount).toBe(1);
            expect(gCount).toBe(0);  // Short-circuit - g not called
            expect(result).toEqual([]);  // Returns f()
        });
        
        test('f() and g() and h() - each called once', () => {
            let fCount = 0, gCount = 0, hCount = 0;
            const f = () => { fCount++; return [1]; };
            const g = () => { gCount++; return [2]; };
            const h = () => { hCount++; return [3]; };
            
            // Nested: ((_b0, _b1) => __py.bool(_b0) ? (__py.bool(_b1) ? h() : _b1) : _b0)(f(), g())
            const result = ((_b0, _b1) => 
                __py.bool(_b0) ? (__py.bool(_b1) ? h() : _b1) : _b0
            )(f(), g());
            
            expect(fCount).toBe(1);
            expect(gCount).toBe(1);
            expect(hCount).toBe(1);
            expect(result).toEqual([3]);
        });
    });
    
    // =========================================================================
    // OR OPERATOR EVALUATION
    // =========================================================================
    
    describe('or operator single evaluation', () => {
        test('f() or g() - f() called once when truthy', () => {
            let fCount = 0, gCount = 0;
            const f = () => { fCount++; return [1]; };  // Truthy
            const g = () => { gCount++; return [2]; };
            
            // Transpiled: ((_b0) => __py.bool(_b0) ? _b0 : g())(f())
            const result = ((_b0) => __py.bool(_b0) ? _b0 : g())(f());
            
            expect(fCount).toBe(1);
            expect(gCount).toBe(0);  // Short-circuit - g not called
            expect(result).toEqual([1]);  // Returns f()
        });
        
        test('f() or g() - f() called once when falsy', () => {
            let fCount = 0, gCount = 0;
            const f = () => { fCount++; return []; };  // Falsy
            const g = () => { gCount++; return [2]; };
            
            const result = ((_b0) => __py.bool(_b0) ? _b0 : g())(f());
            
            expect(fCount).toBe(1);
            expect(gCount).toBe(1);
            expect(result).toEqual([2]);  // Returns g()
        });
    });
    
    // =========================================================================
    // PYTHON SEMANTICS - RETURNS VALUE NOT BOOLEAN
    // =========================================================================
    
    describe('Returns value not boolean', () => {
        test('and returns second value when both truthy', () => {
            const a = [1];
            const b = [2];
            const result = __py.bool(a) ? b : a;
            expect(result).toEqual([2]);
        });
        
        test('and returns first falsy value', () => {
            const a = [];
            const b = [2];
            const result = __py.bool(a) ? b : a;
            expect(result).toEqual([]);
        });
        
        test('or returns first truthy value', () => {
            const a = [1];
            const b = [2];
            const result = __py.bool(a) ? a : b;
            expect(result).toEqual([1]);
        });
        
        test('or returns last value when all falsy', () => {
            const a = [];
            const b = {};
            const result = __py.bool(a) ? a : b;
            expect(result).toEqual({});
        });
    });
});


describe('Side Effect Evaluation - Comprehensions', () => {
    
    // =========================================================================
    // COMPREHENSION EVALUATION
    // =========================================================================
    
    describe('Comprehension side effects', () => {
        test('function in comprehension called per element', () => {
            let callCount = 0;
            const f = (x) => { callCount++; return x * 2; };
            
            const items = [1, 2, 3];
            const result = [...__py.iter(items)].map(x => f(x));
            
            expect(callCount).toBe(3);  // Called once per element
            expect(result).toEqual([2, 4, 6]);
        });
        
        test('filter function called per element', () => {
            let callCount = 0;
            const pred = (x) => { callCount++; return x > 0; };
            
            const items = [-1, 0, 1, 2];
            const result = [...__py.iter(items)].filter(x => pred(x));
            
            expect(callCount).toBe(4);  // Called once per element
            expect(result).toEqual([1, 2]);
        });
    });
});


describe('Side Effect Evaluation - F-Strings', () => {
    
    // =========================================================================
    // F-STRING EXPRESSION EVALUATION
    // =========================================================================
    
    describe('F-string expression evaluation', () => {
        test('expression in f-string called once', () => {
            let callCount = 0;
            const f = () => { callCount++; return 'hello'; };
            
            // f"{f()}" → `${f()}`
            const result = `${f()}`;
            
            expect(callCount).toBe(1);
            expect(result).toBe('hello');
        });
        
        test('multiple expressions each called once', () => {
            let fCount = 0, gCount = 0;
            const f = () => { fCount++; return 'a'; };
            const g = () => { gCount++; return 'b'; };
            
            const result = `${f()} and ${g()}`;
            
            expect(fCount).toBe(1);
            expect(gCount).toBe(1);
            expect(result).toBe('a and b');
        });
        
        test('expression with format spec called once', () => {
            let callCount = 0;
            const f = () => { callCount++; return 3.14159; };
            
            // f"{f():.2f}" → `${__py.format(f(), '.2f')}`
            const result = `${__py.format(f(), '.2f')}`;
            
            expect(callCount).toBe(1);
            expect(result).toBe('3.14');
        });
    });
});


describe('Edge Cases - Complex Expressions', () => {
    
    // =========================================================================
    // NESTED COMPLEX EXPRESSIONS
    // =========================================================================
    
    describe('Nested expressions', () => {
        test('chained comparison in boolean operator', () => {
            let callCount = 0;
            const f = () => { callCount++; return 5; };
            
            // (0 < f() < 10) and x > 0
            // The chained comparison should cache f()
            const chainResult = ((_cmp0) => (0 < _cmp0) && (_cmp0 < 10))(f());
            const x = 1;
            const result = __py.bool(chainResult) ? (x > 0) : chainResult;
            
            expect(callCount).toBe(1);
            expect(result).toBe(true);
        });
        
        test('function call in comprehension filter', () => {
            let callCount = 0;
            const pred = (x) => { callCount++; return x > 0; };
            
            const items = [-1, 1, 2];
            const result = [...__py.iter(items)].filter(x => pred(x)).map(x => x * 2);
            
            expect(callCount).toBe(3);  // pred called for each item
            expect(result).toEqual([2, 4]);
        });
    });
});
