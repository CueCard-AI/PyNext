/**
 * PyNext Standard Library - json module
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides Python json module equivalents in JavaScript.
 * 
 * =============================================================================
 * WHY THIS EXISTS
 * =============================================================================
 * 
 * Python's json module has slightly different API than JSON object:
 * - json.loads(s) vs JSON.parse(s) - same behavior
 * - json.dumps(obj, indent=2) vs JSON.stringify(obj, null, 2) - different arg order
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * Python:
 *   import json
 *   data = json.loads('{"a": 1}')
 *   s = json.dumps(data, indent=2)
 * 
 * Transpiled:
 *   const data = __py.json.loads('{"a": 1}');
 *   const s = __py.json.dumps(data, null, 2);
 */

/**
 * Parse a JSON string to JavaScript object.
 * 
 * @param {string} s - JSON string to parse
 * @returns {*} Parsed JavaScript value
 * @throws {SyntaxError} If JSON is invalid
 * 
 * @example
 * loads('{"a": 1}')  // → {a: 1}
 * loads('[1, 2, 3]') // → [1, 2, 3]
 */
export function loads(s) {
    return JSON.parse(s);
}

/**
 * Serialize a JavaScript value to JSON string.
 * 
 * @param {*} obj - Value to serialize
 * @param {number|null} indent - Indentation spaces (null for compact)
 * @param {boolean} sort_keys - Sort object keys (Python compat)
 * @returns {string} JSON string
 * 
 * @example
 * dumps({a: 1})           // → '{"a":1}'
 * dumps({a: 1}, 2)        // → '{\n  "a": 1\n}'
 * dumps({b: 1, a: 2}, null, true) // → '{"a":2,"b":1}'
 */
export function dumps(obj, indent = null, sort_keys = false) {
    if (sort_keys && obj !== null && typeof obj === 'object') {
        obj = sortKeys(obj);
    }
    return JSON.stringify(obj, null, indent);
}

/**
 * Recursively sort object keys (for sort_keys=True).
 */
function sortKeys(obj) {
    if (Array.isArray(obj)) {
        return obj.map(sortKeys);
    }
    if (obj !== null && typeof obj === 'object') {
        const sorted = {};
        Object.keys(obj).sort().forEach(key => {
            sorted[key] = sortKeys(obj[key]);
        });
        return sorted;
    }
    return obj;
}

/**
 * Load JSON from a file-like object (browser: not supported).
 * Throws an error as file operations aren't available in browser.
 */
export function load(fp) {
    throw new Error("json.load() is not supported in browser environment");
}

/**
 * Write JSON to a file-like object (browser: not supported).
 * Throws an error as file operations aren't available in browser.
 */
export function dump(obj, fp, indent = null) {
    throw new Error("json.dump() is not supported in browser environment");
}
