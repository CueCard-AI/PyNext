/**
 * Phase 18.8: px_transpile_debug API Tests
 *
 * Tests for the browser debug runtime.
 * These tests simulate the px_transpile_debug API behavior.
 *
 * Tests: 30
 */

const __py = require('./setup');

// =============================================================================
// MOCK px_transpile_debug API
// =============================================================================

// Simulated px_transpile_debug for Node.js testing
function createPxTranspileDebug() {
    const handlerRegistry = new Map();
    const runtimeStats = {};

    return {
        listHandlers() {
            return Array.from(handlerRegistry.keys());
        },

        showHandler(name) {
            const info = handlerRegistry.get(name);
            if (!info) return null;
            return info;
        },

        showSource(name) {
            const info = handlerRegistry.get(name);
            if (!info) return null;
            return info.python;
        },

        runtimeStats() {
            return { ...runtimeStats };
        },

        testExpr(expr) {
            const pythonResults = {
                "-7 % 3": 2,
                "7 % -3": -2,
                "[] == []": true,
                "[1,2] == [1,2]": true,
                "bool([])": false,
                "bool([1])": true,
            };

            let result;
            try {
                let jsExpr = expr
                    .replace(/(\S+)\s*%\s*(\S+)/g, '__py.mod($1, $2)')
                    .replace(/(\[.*?\])\s*==\s*(\[.*?\])/g, '__py.eq($1, $2)')
                    .replace(/bool\((.+?)\)/g, '__py.bool($1)');
                result = eval(jsExpr);
            } catch (e) {
                return { expression: expr, result: null, error: e.message };
            }

            const expected = pythonResults[expr];
            return {
                expression: expr,
                result: result,
                expected: expected,
                match: expected !== undefined ? result === expected : 'unknown',
            };
        },

        getHandler(name) {
            return handlerRegistry.get(name) || null;
        },

        _register(name, info) {
            handlerRegistry.set(name, info);
        },

        _trackCall(fnName) {
            runtimeStats[fnName] = (runtimeStats[fnName] || 0) + 1;
        },

        _reset() {
            handlerRegistry.clear();
            for (const key of Object.keys(runtimeStats)) {
                delete runtimeStats[key];
            }
        },
    };
}

// Create test instance
const px_transpile_debug = createPxTranspileDebug();

// =============================================================================
// HANDLER REGISTRATION TESTS
// =============================================================================

describe('Handler Registration', () => {
    beforeEach(() => {
        px_transpile_debug._reset();
    });

    test('register handler', () => {
        px_transpile_debug._register('handle_click', {
            python: 'def handle_click(): pass',
            javascript: 'function handle_click() {}',
            runtimeDeps: [],
        });

        expect(px_transpile_debug.listHandlers()).toContain('handle_click');
    });

    test('register multiple handlers', () => {
        px_transpile_debug._register('handler_a', { python: 'a', javascript: 'a', runtimeDeps: [] });
        px_transpile_debug._register('handler_b', { python: 'b', javascript: 'b', runtimeDeps: [] });
        px_transpile_debug._register('handler_c', { python: 'c', javascript: 'c', runtimeDeps: [] });

        const handlers = px_transpile_debug.listHandlers();
        expect(handlers).toHaveLength(3);
        expect(handlers).toContain('handler_a');
        expect(handlers).toContain('handler_b');
        expect(handlers).toContain('handler_c');
    });

    test('list handlers returns empty initially', () => {
        expect(px_transpile_debug.listHandlers()).toEqual([]);
    });
});

// =============================================================================
// HANDLER RETRIEVAL TESTS
// =============================================================================

describe('Handler Retrieval', () => {
    beforeEach(() => {
        px_transpile_debug._reset();
        px_transpile_debug._register('my_handler', {
            python: 'def my_handler(x):\n    return x + 1',
            javascript: 'function my_handler(x) { return x + 1; }',
            runtimeDeps: ['__py.add'],
        });
    });

    test('showHandler returns info', () => {
        const info = px_transpile_debug.showHandler('my_handler');
        expect(info).not.toBeNull();
        expect(info.python).toContain('my_handler');
        expect(info.javascript).toContain('my_handler');
    });

    test('showHandler returns null for unknown', () => {
        const info = px_transpile_debug.showHandler('unknown');
        expect(info).toBeNull();
    });

    test('showSource returns Python code', () => {
        const source = px_transpile_debug.showSource('my_handler');
        expect(source).toContain('def my_handler');
    });

    test('showSource returns null for unknown', () => {
        const source = px_transpile_debug.showSource('unknown');
        expect(source).toBeNull();
    });

    test('getHandler returns raw info', () => {
        const info = px_transpile_debug.getHandler('my_handler');
        expect(info.runtimeDeps).toContain('__py.add');
    });
});

// =============================================================================
// RUNTIME STATS TESTS
// =============================================================================

describe('Runtime Statistics', () => {
    beforeEach(() => {
        px_transpile_debug._reset();
    });

    test('track function calls', () => {
        px_transpile_debug._trackCall('bool');
        px_transpile_debug._trackCall('bool');
        px_transpile_debug._trackCall('eq');

        const stats = px_transpile_debug.runtimeStats();
        expect(stats.bool).toBe(2);
        expect(stats.eq).toBe(1);
    });

    test('stats empty initially', () => {
        const stats = px_transpile_debug.runtimeStats();
        expect(Object.keys(stats)).toHaveLength(0);
    });

    test('stats are independent', () => {
        px_transpile_debug._trackCall('at');
        const stats = px_transpile_debug.runtimeStats();
        
        // Modify returned object shouldn't affect internal state
        stats.at = 999;
        
        const stats2 = px_transpile_debug.runtimeStats();
        expect(stats2.at).toBe(1);
    });
});

// =============================================================================
// EXPRESSION TESTING TESTS
// =============================================================================

describe('Expression Testing', () => {
    test('test modulo expression', () => {
        const result = px_transpile_debug.testExpr('-7 % 3');
        expect(result.expression).toBe('-7 % 3');
        expect(result.result).toBe(2);
        expect(result.expected).toBe(2);
        expect(result.match).toBe(true);
    });

    test('test positive modulo', () => {
        const result = px_transpile_debug.testExpr('7 % -3');
        expect(result.result).toBe(-2);
        expect(result.expected).toBe(-2);
        expect(result.match).toBe(true);
    });

    test('test bool on empty list', () => {
        const result = px_transpile_debug.testExpr('bool([])');
        expect(result.result).toBe(false);
        expect(result.expected).toBe(false);
        expect(result.match).toBe(true);
    });

    test('test bool on non-empty list', () => {
        const result = px_transpile_debug.testExpr('bool([1])');
        expect(result.result).toBe(true);
        expect(result.expected).toBe(true);
        expect(result.match).toBe(true);
    });

    test('test unknown expression returns unknown match', () => {
        // Use a valid expression that's not in the known results
        const result = px_transpile_debug.testExpr('5 + 5');
        expect(result.result).toBe(10);
        expect(result.match).toBe('unknown');  // Not in pythonResults lookup
    });
});

// =============================================================================
// RESET TESTS
// =============================================================================

describe('Reset Functionality', () => {
    test('reset clears handlers', () => {
        px_transpile_debug._register('test', { python: '', javascript: '', runtimeDeps: [] });
        expect(px_transpile_debug.listHandlers()).toHaveLength(1);
        
        px_transpile_debug._reset();
        expect(px_transpile_debug.listHandlers()).toHaveLength(0);
    });

    test('reset clears stats', () => {
        px_transpile_debug._trackCall('bool');
        expect(px_transpile_debug.runtimeStats().bool).toBe(1);
        
        px_transpile_debug._reset();
        expect(px_transpile_debug.runtimeStats().bool).toBeUndefined();
    });
});

// =============================================================================
// HANDLER INFO STRUCTURE TESTS
// =============================================================================

describe('Handler Info Structure', () => {
    beforeEach(() => {
        px_transpile_debug._reset();
    });

    test('handler has python field', () => {
        px_transpile_debug._register('test', {
            python: 'def test(): pass',
            javascript: '',
            runtimeDeps: [],
        });
        
        const info = px_transpile_debug.getHandler('test');
        expect(info).toHaveProperty('python');
    });

    test('handler has javascript field', () => {
        px_transpile_debug._register('test', {
            python: '',
            javascript: 'function test() {}',
            runtimeDeps: [],
        });
        
        const info = px_transpile_debug.getHandler('test');
        expect(info).toHaveProperty('javascript');
    });

    test('handler has runtimeDeps field', () => {
        px_transpile_debug._register('test', {
            python: '',
            javascript: '',
            runtimeDeps: ['__py.bool', '__py.eq'],
        });
        
        const info = px_transpile_debug.getHandler('test');
        expect(info.runtimeDeps).toContain('__py.bool');
        expect(info.runtimeDeps).toContain('__py.eq');
    });
});

