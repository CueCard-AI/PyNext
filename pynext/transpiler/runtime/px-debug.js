/**
 * PyNext Transpiler Debug Runtime (Phase 18.8)
 * 
 * Exposed as `px_transpile_debug` in dev mode.
 * Separate from `pynext_debug` (general app debugging) - this is specifically
 * for transpiler debugging: viewing Python→JS transformations, runtime usage, etc.
 * 
 * Usage in browser console:
 *   px_transpile_debug.listHandlers()              - List all handlers
 *   px_transpile_debug.showHandler("handle_add")   - Show Python→JS
 *   px_transpile_debug.showSource("handle_add")    - Show original Python
 *   px_transpile_debug.runtimeStats()              - Show __py.* usage
 *   px_transpile_debug.testExpr("-7 % 3")         - Verify semantics
 */

(function() {
    'use strict';
    
    // Prevent double initialization
    if (window.px_transpile_debug) {
        return;
    }
    
    // =================================================================
    // HANDLER REGISTRY
    // =================================================================
    
    // Map of handler name → debug info
    const handlerRegistry = new Map();
    
    // =================================================================
    // RUNTIME STATISTICS
    // =================================================================
    
    // Track __py.* function calls
    const runtimeStats = {};
    
    // Patch __py to track calls (if available)
    function patchPyRuntime() {
        if (!window.__py) {
            return false;
        }
        
        const py = window.__py;
        
        // List of functions to track
        const funcs = [
            'bool', 'at', 'slice', 'eq', 'add', 'mul', 'mod', 'floordiv',
            'in', 'len', 'range', 'enumerate', 'zip', 'sum', 'min', 'max',
            'any', 'all', 'sorted', 'reversed', 'map', 'filter', 'repr',
            'ascii', 'isinstance', 'type', 'format', 'abs', 'round', 'pow',
            'divmod', 'ord', 'chr', 'bin', 'hex', 'oct', 'int', 'float',
            'str', 'list', 'dict', 'set', 'tuple', 'print',
        ];
        
        for (const name of funcs) {
            if (typeof py[name] === 'function' && !py[name]._tracked) {
                const original = py[name];
                py[name] = function(...args) {
                    runtimeStats[name] = (runtimeStats[name] || 0) + 1;
                    return original.apply(this, args);
                };
                py[name]._tracked = true;
                py[name]._original = original;
            }
        }
        
        return true;
    }
    
    // =================================================================
    // PUBLIC API
    // =================================================================
    
    window.px_transpile_debug = {
        /**
         * List all transpiled handlers on the page.
         * @returns {string[]} Array of handler names
         */
        listHandlers() {
            const handlers = Array.from(handlerRegistry.keys());
            if (handlers.length === 0) {
                console.log('[px_transpile_debug] No handlers registered.');
                console.log('Handlers are registered when the page loads with --ai-debug.');
            } else {
                console.log(`[px_transpile_debug] ${handlers.length} handlers:`);
                handlers.forEach((name, i) => {
                    console.log(`  ${i + 1}. ${name}`);
                });
            }
            return handlers;
        },
        
        /**
         * Show transpiled JavaScript for a specific handler.
         * @param {string} name - Handler name
         * @returns {object|null} Handler debug info or null
         */
        showHandler(name) {
            const info = handlerRegistry.get(name);
            if (!info) {
                console.warn(`[px_transpile_debug] Handler '${name}' not found.`);
                console.log('Use px_transpile_debug.listHandlers() to see available handlers.');
                return null;
            }
            
            console.log('%c' + '═'.repeat(60), 'color: #4CAF50');
            console.log(`%c${name}`, 'font-weight: bold; font-size: 14px; color: #4CAF50');
            console.log('%c' + '═'.repeat(60), 'color: #4CAF50');
            
            console.log('\n%cPython Source:', 'font-weight: bold; color: #2196F3');
            console.log('%c' + info.python, 'color: #2196F3; background: #f5f5f5; padding: 4px;');
            
            console.log('\n%cJavaScript Output:', 'font-weight: bold; color: #FF9800');
            console.log('%c' + info.javascript, 'color: #FF9800; background: #f5f5f5; padding: 4px;');
            
            console.log('\n%cRuntime Dependencies:', 'font-weight: bold; color: #9C27B0');
            console.log('%c' + (info.runtimeDeps.join(', ') || 'none'), 'color: #9C27B0');
            
            console.log('%c' + '═'.repeat(60), 'color: #4CAF50');
            
            return info;
        },
        
        /**
         * Show original Python source for a handler.
         * @param {string} name - Handler name
         * @returns {string|null} Python source or null
         */
        showSource(name) {
            const info = handlerRegistry.get(name);
            if (!info) {
                console.warn(`[px_transpile_debug] Handler '${name}' not found.`);
                return null;
            }
            console.log(info.python);
            return info.python;
        },
        
        /**
         * Show usage statistics for __py.* runtime functions.
         * @returns {object} Map of function name → call count
         */
        runtimeStats() {
            const stats = { ...runtimeStats };
            
            if (Object.keys(stats).length === 0) {
                console.log('[px_transpile_debug] No runtime calls tracked yet.');
                console.log('Interact with the page to trigger handlers.');
            } else {
                console.log('[px_transpile_debug] Runtime function usage:');
                const sorted = Object.entries(stats).sort((a, b) => b[1] - a[1]);
                sorted.forEach(([name, count]) => {
                    console.log(`  __py.${name}: ${count} calls`);
                });
            }
            
            return stats;
        },
        
        /**
         * Test an expression to verify Python semantics match.
         * @param {string} expr - Expression to test (e.g., "-7 % 3")
         * @returns {object} Result with expression, result, expected, match
         */
        testExpr(expr) {
            // Known Python results for common tests
            const pythonResults = {
                "-7 % 3": 2,
                "7 % -3": -2,
                "-7 // 3": -3,
                "7 // -3": -3,
                "[] == []": true,
                "[1,2] == [1,2]": true,
                "{} == {}": true,
                "bool([])": false,
                "bool({})": false,
                "bool('')": false,
                "bool([1])": true,
                "bool('x')": true,
            };
            
            let result;
            let error = null;
            
            try {
                // Replace Python operations with __py.* calls
                let jsExpr = expr
                    .replace(/(\S+)\s*%\s*(\S+)/g, '__py.mod($1, $2)')
                    .replace(/(\S+)\s*\/\/\s*(\S+)/g, '__py.floordiv($1, $2)')
                    .replace(/(\[.*?\])\s*==\s*(\[.*?\])/g, '__py.eq($1, $2)')
                    .replace(/(\{.*?\})\s*==\s*(\{.*?\})/g, '__py.eq($1, $2)')
                    .replace(/bool\((.+?)\)/g, '__py.bool($1)');
                
                result = eval(jsExpr);
            } catch (e) {
                error = e.message;
            }
            
            const expected = pythonResults[expr];
            const match = expected !== undefined ? result === expected : 'unknown';
            
            const output = {
                expression: expr,
                result: result,
                expected: expected,
                match: match,
                error: error,
            };
            
            // Pretty print
            const color = match === true ? '#4CAF50' : match === false ? '#f44336' : '#FF9800';
            console.log(`%c${expr}`, 'font-weight: bold');
            console.log(`  Result:   %c${result}`, `color: ${color}`);
            console.log(`  Expected: ${expected !== undefined ? expected : '(not in test suite)'}`);
            console.log(`  Match:    %c${match}`, `color: ${color}`);
            if (error) {
                console.log(`  Error:    %c${error}`, 'color: #f44336');
            }
            
            return output;
        },
        
        /**
         * Get raw debug info for a handler.
         * @param {string} name - Handler name
         * @returns {object|null} Raw debug info
         */
        getHandler(name) {
            return handlerRegistry.get(name) || null;
        },
        
        /**
         * Register a handler's debug info (called by hydration).
         * @internal
         */
        _register(name, info) {
            handlerRegistry.set(name, info);
        },
        
        /**
         * Track a runtime function call (called by instrumented __py).
         * @internal
         */
        _trackCall(fnName) {
            runtimeStats[fnName] = (runtimeStats[fnName] || 0) + 1;
        },
        
        /**
         * Reset all tracking (for testing).
         * @internal
         */
        _reset() {
            handlerRegistry.clear();
            for (const key of Object.keys(runtimeStats)) {
                delete runtimeStats[key];
            }
        },
    };
    
    // =================================================================
    // INITIALIZATION
    // =================================================================
    
    function init() {
        // Try to patch __py for tracking
        if (!patchPyRuntime()) {
            // Wait for __py to load
            let attempts = 0;
            const interval = setInterval(() => {
                if (patchPyRuntime() || attempts++ > 50) {
                    clearInterval(interval);
                }
            }, 100);
        }
        
        console.log('[px_transpile_debug] Transpiler debug tools loaded.');
        console.log('  Use px_transpile_debug.listHandlers() to see registered handlers.');
        console.log('  Use px_transpile_debug.runtimeStats() to see __py.* usage.');
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();

