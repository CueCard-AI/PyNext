/**
 * PyNext Transpiler Runtime Test Setup
 * 
 * This file provides the __py runtime for testing.
 * Since the runtime is ES modules and Jest uses CommonJS by default,
 * we recreate the functions here for testing.
 */

// =============================================================================
// INDEXING
// =============================================================================

function at(arr, i) {
    if (arr === null || arr === undefined) return undefined;
    // Handle Map-like objects (Counter, defaultdict, OrderedDict)
    if (arr instanceof Map || (arr && typeof arr.get === 'function' && typeof arr.has === 'function')) {
        return arr.get(i);
    }
    if (i < 0) return arr[arr.length + i];
    return arr[i];
}

function slice(arr, start, stop, step = 1) {
    if (arr === null || arr === undefined) return [];
    const len = arr.length;
    const isString = typeof arr === 'string';
    
    if (step === 0) throw new Error("slice step cannot be zero");
    
    if (step > 0) {
        start = start === null ? 0 : (start < 0 ? Math.max(0, len + start) : Math.min(len, start));
        stop = stop === null ? len : (stop < 0 ? Math.max(0, len + stop) : Math.min(len, stop));
        
        const result = [];
        for (let i = start; i < stop; i += step) {
            result.push(arr[i]);
        }
        return isString ? result.join('') : result;
    } else {
        start = start === null ? len - 1 : (start < 0 ? Math.max(-1, len + start) : Math.min(len - 1, start));
        stop = stop === null ? -1 : (stop < 0 ? Math.max(-1, len + stop) : Math.min(len - 1, stop));
        
        const result = [];
        for (let i = start; i > stop; i += step) {
            if (i >= 0 && i < len) result.push(arr[i]);
        }
        return isString ? result.join('') : result;
    }
}

// =============================================================================
// TRUTHINESS
// =============================================================================

/**
 * Pythonic truthiness with __bool__ support.
 * 
 * Phase 33.2: Checks for [Symbol.toPrimitive]("boolean") (from __bool__ dunder).
 * 
 * @param {*} x - Value to check
 * @returns {boolean} Truthiness
 */
function bool(x) {
    // Phase 33.2: Check for __bool__ dunder method (via Symbol.toPrimitive)
    if (typeof x === 'object' && x !== null) {
        const toPrimitive = x[Symbol.toPrimitive];
        if (typeof toPrimitive === 'function') {
            try {
                const result = toPrimitive.call(x, 'boolean');
                if (typeof result === 'boolean') {
                    return result;
                }
            } catch (e) {
                // Fall through to default behavior
            }
        }
    }
    
    // Default truthiness checks
    if (x === null || x === undefined) return false;
    if (x === false || x === 0 || x === '') return false;
    if (Number.isNaN(x)) return false;
    if (Array.isArray(x)) return x.length > 0;
    if (typeof x === 'object') {
        if (x.constructor === Object) return Object.keys(x).length > 0;
        if (x instanceof Set || x instanceof Map) return x.size > 0;
    }
    return true;
}

// =============================================================================
// ARITHMETIC
// =============================================================================

function mod(a, b) {
    const result = ((a % b) + b) % b;
    // Normalize -0 to 0
    return result === 0 ? 0 : result;
}

function floordiv(a, b) {
    return Math.floor(a / b);
}

// =============================================================================
// EQUALITY
// =============================================================================

/**
 * Pythonic equality comparison with __eq__ support.
 * 
 * Phase 33.2: Checks for equals() method (from __eq__ dunder) on objects.
 * 
 * @param {*} a - First value
 * @param {*} b - Second value
 * @returns {boolean} True if equal
 */
function eq(a, b) {
    // Same reference
    if (a === b) return true;
    
    // Handle null/undefined
    if (a == null || b == null) return a === b;
    
    // Phase 33.2: If a has equals() method (from __eq__ dunder), use it
    if (typeof a === 'object' && a !== null && typeof a.equals === 'function') {
        return a.equals(b);
    }
    
    // Phase 33.2: If b has equals() method (reverse), use it
    if (typeof b === 'object' && b !== null && typeof b.equals === 'function') {
        return b.equals(a);
    }
    
    // Arrays: deep equality
    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) return false;
        for (let i = 0; i < a.length; i++) {
            if (!eq(a[i], b[i])) return false;
        }
        return true;
    }
    
    // Objects: shallow equality (key-value pairs)
    if (typeof a === 'object' && typeof b === 'object' && !Array.isArray(a) && !Array.isArray(b)) {
        const keysA = Object.keys(a);
        const keysB = Object.keys(b);
        if (keysA.length !== keysB.length) return false;
        for (const key of keysA) {
            if (!(key in b)) return false;
            if (!eq(a[key], b[key])) return false;
        }
        return true;
    }
    
    // Primitive types: direct comparison
    return a === b;
}

// =============================================================================
// MEMBERSHIP
// =============================================================================

/**
 * Pythonic membership test with __contains__ support.
 * 
 * Phase 33.2: Checks for has() method (from __contains__ dunder).
 * 
 * @param {*} item - Item to check
 * @param {*} container - Container to check in
 * @returns {boolean} True if item is in container
 */
function contains(item, container) {
    // Phase 33.2: Check for __contains__ dunder method (via has() method)
    if (typeof container === 'object' && container !== null && typeof container.has === 'function') {
        return container.has(item);
    }
    
    // Default membership checks
    if (typeof container === 'string') {
        return container.includes(item);
    }
    if (Array.isArray(container)) {
        return container.some(x => eq(x, item));
    }
    if (container instanceof Set) {
        for (const x of container) {
            if (eq(x, item)) return true;
        }
        return false;
    }
    if (typeof container === 'object' && container !== null) {
        return item in container;
    }
    return false;
}

// =============================================================================
// ITERATION HELPERS
// =============================================================================

function enumerate(iterable, start = 0) {
    const arr = Array.from(iterable);
    return arr.map((item, i) => [start + i, item]);
}

function zip(...iterables) {
    if (iterables.length === 0) return [];
    const arrays = iterables.map(it => Array.from(it));
    const minLen = Math.min(...arrays.map(a => a.length));
    const result = [];
    for (let i = 0; i < minLen; i++) {
        result.push(arrays.map(a => a[i]));
    }
    return result;
}

function range(start, stop, step = 1) {
    if (stop === undefined) {
        stop = start;
        start = 0;
    }
    if (step === 0) {
        throw new Error("range() step argument must not be zero");
    }
    const result = [];
    if (step > 0) {
        for (let i = start; i < stop; i += step) result.push(i);
    } else if (step < 0) {
        for (let i = start; i > stop; i += step) result.push(i);
    }
    return result;
}

function sum(iterable, start = 0) {
    return Array.from(iterable).reduce((a, b) => a + b, start);
}

function iter(obj) {
    if (obj === null || obj === undefined) return [];
    if (Array.isArray(obj)) return obj;
    if (typeof obj === 'string') return [...obj];
    if (typeof obj[Symbol.iterator] === 'function') return [...obj];
    if (typeof obj === 'object' && obj.constructor === Object) {
        return Object.keys(obj);
    }
    return [obj];
}

/**
 * Phase 33.2: Python next() builtin implementation
 * 
 * WHO: Used by transpiled Python code when calling next(iterable) or next(iterable, default)
 * 
 * WHAT: Implements Python's next() function semantics for JavaScript iterables
 * 
 * WHEN: Called whenever Python code uses next() on:
 *   - Generator expressions: next(x for x in range(10))
 *   - Generator functions: next(fib_gen)
 *   - Arrays/lists: next([1, 2, 3])
 *   - Any iterable: next(iterable, default_value)
 * 
 * WHERE: Runtime helper in __py.next() - used by transpiler for all next() calls
 * 
 * WHY: Python's next() requires persistent iterator state across multiple calls:
 *   - Problem: Generator expressions are materialized as arrays in JS (no lazy evaluation)
 *   - Problem: Arrays don't have persistent iterator state (each [Symbol.iterator]() creates new iterator)
 *   - Problem: Python's next() must track position across multiple calls: next(gen), next(gen), next(gen)
 *   - Solution: Use WeakMap to associate each array with a persistent iterator object
 * 
 * HOW: 
 *   1. For generators: Use directly (they already have .next() method)
 *   2. For arrays/iterables:
 *      a. Check WeakMap for existing iterator (reuse if found)
 *      b. If not found, create new iterator with position tracking
 *      c. Store iterator in WeakMap (keyed by array reference)
 *      d. Call iterator.next() to get next value
 *   3. Handle StopIteration: Throw error (or return default if provided)
 * 
 * DESIGN DECISIONS:
 *   - WeakMap (not Map): Allows garbage collection when arrays are no longer referenced
 *   - Non-mutating: Doesn't add properties to user arrays (avoids property pollution)
 *   - Persistent state: Same array reference = same iterator position (matches Python semantics)
 *   - Memory-safe: WeakMap entries are GC'd when array is no longer referenced
 * 
 * EXAMPLES:
 *   Python: squares = (x*x for x in range(10))
 *           first = next(squares)  # 0
 *           second = next(squares) # 1
 *   
 *   JS:     squares = [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
 *           first = __py.next(squares)   // 0 (creates iterator, position=0)
 *           second = __py.next(squares)  // 1 (reuses iterator, position=1)
 * 
 * EDGE CASES:
 *   - Empty iterable: Throws StopIteration (or returns default if provided)
 *   - Iterator exhausted: Throws StopIteration (or returns default if provided)
 *   - Multiple arrays with same content: Each has separate iterator state (correct)
 *   - Same array, different references: Same iterator state (WeakMap keyed by reference)
 * 
 * PERFORMANCE:
 *   - WeakMap.get/set: O(1) operations, optimized by JS engines
 *   - No array mutation: Avoids property enumeration overhead
 *   - Lazy iterator creation: Only creates iterator when first next() is called
 */
const _iterators = new WeakMap();

function py_next(iterable, default_value) {
    // If it's already a generator (has .next() method), use it directly
    // This handles Python generator functions and JavaScript generator objects
    if (iterable && typeof iterable.next === 'function') {
        const result = iterable.next();
        if (result.done) {
            if (default_value !== undefined) {
                return default_value;
            }
            throw new Error('StopIteration');
        }
        return result.value;
    }
    
    // For arrays or array-like objects, we need to create a persistent iterator
    // Convert to array if needed (handles other iterables like strings, Sets, etc.)
    const arr = Array.isArray(iterable) ? iterable : __py.iter(iterable);
    
    // Get or create iterator from WeakMap (doesn't mutate the array)
    // WeakMap key is the array reference, value is the iterator object with position state
    let iterator = _iterators.get(arr);
    if (!iterator) {
        // Create new iterator with position tracking
        // This iterator maintains state across multiple next() calls
        let index = 0;
        iterator = {
            next: function() {
                if (index >= arr.length) {
                    return { done: true, value: undefined };
                }
                return { done: false, value: arr[index++] };
            }
        };
        // Store in WeakMap so subsequent next() calls on same array reuse this iterator
        _iterators.set(arr, iterator);
    }
    
    // Call the iterator's next() method to get the next value
    const result = iterator.next();
    if (result.done) {
        // Iterator exhausted - return default or throw StopIteration
        if (default_value !== undefined) {
            return default_value;
        }
        throw new Error('StopIteration');
    }
    return result.value;
}

// =============================================================================
// DELETE HELPERS
// =============================================================================

function del(obj, key) {
    if (Array.isArray(obj)) {
        const idx = key < 0 ? obj.length + key : key;
        obj.splice(idx, 1);
    } else {
        delete obj[key];
    }
}

function del_slice(arr, sliceArgs) {
    const [start, stop] = sliceArgs;
    const s = start === null ? 0 : (start < 0 ? arr.length + start : start);
    const e = stop === null ? arr.length : (stop < 0 ? arr.length + stop : stop);
    arr.splice(s, e - s);
}

// =============================================================================
// POLYMORPHIC OPERATORS
// =============================================================================

function add(a, b) {
    if (Array.isArray(a) && Array.isArray(b)) {
        return [...a, ...b];
    }
    return a + b;
}

function mul(a, b) {
    if (typeof a === 'string' && typeof b === 'number') {
        return b <= 0 ? '' : a.repeat(b);
    }
    if (typeof b === 'string' && typeof a === 'number') {
        return a <= 0 ? '' : b.repeat(a);
    }
    if (Array.isArray(a) && typeof b === 'number') {
        if (b <= 0) return [];
        const result = [];
        for (let i = 0; i < b; i++) result.push(...a);
        return result;
    }
    if (Array.isArray(b) && typeof a === 'number') {
        if (a <= 0) return [];
        const result = [];
        for (let i = 0; i < a; i++) result.push(...b);
        return result;
    }
    return a * b;
}

// =============================================================================
// FORMAT
// =============================================================================

function format(value, spec) {
    if (!spec) return String(value);
    
    // Handle simple type-only specs first
    if (spec === 'x') return Math.floor(Number(value)).toString(16);
    if (spec === 'X') return Math.floor(Number(value)).toString(16).toUpperCase();
    if (spec === 'b') return Math.floor(Number(value)).toString(2);
    if (spec === 'o') return Math.floor(Number(value)).toString(8);
    if (spec === 'd') return Math.floor(Number(value)).toString();
    if (spec === ',') {
        const num = Number(value);
        const parts = num.toString().split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return parts.join('.');
    }
    
    // Handle .Nf pattern
    const floatMatch = spec.match(/^\.(\d+)f$/i);
    if (floatMatch) {
        return Number(value).toFixed(parseInt(floatMatch[1]));
    }
    
    // Handle .N% pattern
    const pctMatch = spec.match(/^\.(\d+)%$/);
    if (pctMatch) {
        return (Number(value) * 100).toFixed(parseInt(pctMatch[1])) + '%';
    }
    
    // Handle alignment patterns like >10, <10, ^10
    const alignMatch = spec.match(/^([*\-_=])?([<>^])(\d+)$/);
    if (alignMatch) {
        const [, fillChar, alignDir, widthStr] = alignMatch;
        const fill = fillChar || ' ';
        const width = parseInt(widthStr);
        const str = String(value);
        if (str.length >= width) return str;
        const padding = fill.repeat(width - str.length);
        if (alignDir === '>') return padding + str;
        if (alignDir === '<') return str + padding;
        if (alignDir === '^') {
            const left = Math.floor((width - str.length) / 2);
            const right = width - str.length - left;
            return fill.repeat(left) + str + fill.repeat(right);
        }
    }
    
    // Handle zero-padded integers like 05d
    const zeroPadMatch = spec.match(/^0?(\d+)d$/);
    if (zeroPadMatch) {
        const width = parseInt(zeroPadMatch[1]);
        const num = Math.floor(Number(value));
        const isNeg = num < 0;
        const absStr = Math.abs(num).toString();
        if (isNeg) {
            const padded = absStr.padStart(width - 1, '0');
            return '-' + padded;
        }
        return absStr.padStart(width, '0');
    }
    
    // Handle zero-padded hex like 04x
    const hexPadMatch = spec.match(/^0?(\d+)([xX])$/);
    if (hexPadMatch) {
        const width = parseInt(hexPadMatch[1]);
        const num = Math.floor(Number(value));
        const hex = num.toString(16);
        const result = hex.padStart(width, '0');
        return hexPadMatch[2] === 'X' ? result.toUpperCase() : result;
    }
    
    // Handle zero-padded binary like 08b
    const binPadMatch = spec.match(/^0?(\d+)b$/);
    if (binPadMatch) {
        const width = parseInt(binPadMatch[1]);
        const num = Math.floor(Number(value));
        return num.toString(2).padStart(width, '0');
    }
    
    // Handle sign specifiers +d and ' d'
    const signMatch = spec.match(/^([+ ])d$/);
    if (signMatch) {
        const num = Math.floor(Number(value));
        const signChar = signMatch[1];
        if (num >= 0) {
            return signChar + num.toString();
        }
        return num.toString();
    }
    
    // Handle comma with precision like ,.2f
    const commaFloatMatch = spec.match(/^,\.(\d+)f$/i);
    if (commaFloatMatch) {
        const precision = parseInt(commaFloatMatch[1]);
        const num = Number(value);
        const fixed = num.toFixed(precision);
        const parts = fixed.split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return parts.join('.');
    }
    
    // Handle scientific notation
    const sciMatch = spec.match(/^\.?(\d*)([eE])$/);
    if (sciMatch) {
        const precision = sciMatch[1] ? parseInt(sciMatch[1]) : undefined;
        const result = precision !== undefined 
            ? Number(value).toExponential(precision) 
            : Number(value).toExponential();
        return sciMatch[2] === 'E' ? result.toUpperCase() : result;
    }
    
    // Fallback: try full format spec parsing
    const match = spec.match(/^([^<>=^])?([<>=^])?([+\- ])?([#])?(0)?(\d+)?([,])?(?:\.(\d+))?([bcdeEfFgGnosxX%])?$/);
    
    if (!match) {
        return String(value);
    }
    
    let [, fill, align, sign, alt, zero, width, comma, precision, type] = match;
    
    fill = fill || (zero ? '0' : ' ');
    align = align || (zero ? '=' : '>');
    width = width ? parseInt(width) : 0;
    precision = precision !== undefined ? parseInt(precision) : undefined;
    
    let result;
    
    switch (type) {
        case 'f':
        case 'F':
            result = precision !== undefined ? Number(value).toFixed(precision) : Number(value).toFixed(6);
            break;
        case 'e':
            result = precision !== undefined ? Number(value).toExponential(precision) : Number(value).toExponential();
            break;
        case 'E':
            result = (precision !== undefined ? Number(value).toExponential(precision) : Number(value).toExponential()).toUpperCase();
            break;
        case '%':
            result = (Number(value) * 100).toFixed(precision !== undefined ? precision : 6) + '%';
            break;
        case 'd':
            result = Math.floor(Number(value)).toString();
            break;
        case 'x':
            result = Math.floor(Number(value)).toString(16);
            break;
        case 'X':
            result = Math.floor(Number(value)).toString(16).toUpperCase();
            break;
        case 'b':
            result = Math.floor(Number(value)).toString(2);
            break;
        case 'o':
            result = Math.floor(Number(value)).toString(8);
            break;
        default:
            result = String(value);
            if (precision !== undefined && typeof value === 'number') {
                result = Number(value).toFixed(precision);
            }
    }
    
    if (comma && typeof value === 'number') {
        const parts = result.split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        result = parts.join('.');
    }
    
    if (sign === '+' && Number(value) >= 0 && !result.startsWith('-')) {
        result = '+' + result;
    } else if (sign === ' ' && Number(value) >= 0 && !result.startsWith('-')) {
        result = ' ' + result;
    }
    
    if (result.length < width) {
        const padding = fill.repeat(width - result.length);
        switch (align) {
            case '<':
                result = result + padding;
                break;
            case '>':
                result = padding + result;
                break;
            case '^':
                const left = Math.floor((width - result.length) / 2);
                const right = width - result.length - left;
                result = fill.repeat(left) + result + fill.repeat(right);
                break;
            case '=':
                if (result.startsWith('-') || result.startsWith('+') || result.startsWith(' ')) {
                    result = result[0] + padding + result.slice(1);
                } else {
                    result = padding + result;
                }
                break;
        }
    }
    
    return result;
}

// =============================================================================
// STRING/LIST HELPERS
// =============================================================================

function str_count(str, sub) {
    if (sub.length === 0) return str.length + 1;
    let count = 0;
    let pos = 0;
    while ((pos = str.indexOf(sub, pos)) !== -1) {
        count++;
        pos += sub.length;
    }
    return count;
}

function list_remove(arr, item) {
    const idx = arr.findIndex(x => eq(x, item));
    if (idx !== -1) arr.splice(idx, 1);
    else throw new Error(`ValueError: list.remove(x): x not in list`);
}

function dict_pop(obj, key, default_ = undefined) {
    if (key in obj) {
        const val = obj[key];
        delete obj[key];
        return val;
    }
    if (default_ !== undefined) return default_;
    throw new Error(`KeyError: ${key}`);
}

function dict_setdefault(obj, key, default_ = null) {
    if (!(key in obj)) obj[key] = default_;
    return obj[key];
}

function dict_items(d) {
    // Preserves key types (unlike Object.entries() which converts to strings).
    // For objects with integer keys, we need to preserve the numeric type.
    const result = [];
    for (const key in d) {
        if (d.hasOwnProperty(key)) {
            // Try to preserve numeric keys as numbers
            const numKey = Number(key);
            const preservedKey = (!isNaN(numKey) && String(numKey) === key && numKey >= 0) ? numKey : key;
            result.push([preservedKey, d[key]]);
        }
    }
    return result;
}

function isinstance(obj, types) {
    const typeArray = Array.isArray(types) ? types : [types];
    for (const t of typeArray) {
        if (t === 'str' || t === String) {
            if (typeof obj === 'string') return true;
        } else if (t === 'int' || t === Number) {
            if (typeof obj === 'number' && Number.isInteger(obj)) return true;
        } else if (t === 'float' || t === Number) {
            if (typeof obj === 'number') return true;
        } else if (t === 'bool' || t === Boolean) {
            if (typeof obj === 'boolean') return true;
        } else if (t === 'list' || t === Array) {
            if (Array.isArray(obj)) return true;
        } else if (t === 'dict' || t === Object) {
            if (typeof obj === 'object' && obj !== null && obj.constructor === Object) return true;
        } else if (typeof t === 'function') {
            if (obj instanceof t) return true;
        }
    }
    return false;
}

function type(obj) {
    if (obj === null) return 'NoneType';
    if (Array.isArray(obj)) return 'list';
    if (typeof obj === 'string') return 'str';
    if (typeof obj === 'number') return Number.isInteger(obj) ? 'int' : 'float';
    if (typeof obj === 'boolean') return 'bool';
    if (typeof obj === 'object' && obj.constructor === Object) return 'dict';
    return typeof obj;
}

// =============================================================================
// REPR AND ASCII (for f-string conversions)
// =============================================================================

function repr(obj) {
    if (obj === null) return 'None';
    if (obj === undefined) return 'None';
    if (typeof obj === 'string') return `'${obj.replace(/'/g, "\\'")}'`;
    if (typeof obj === 'boolean') return obj ? 'True' : 'False';
    if (Array.isArray(obj)) {
        return '[' + obj.map(repr).join(', ') + ']';
    }
    if (typeof obj === 'object' && obj.constructor === Object) {
        const pairs = Object.entries(obj).map(([k, v]) => `'${k}': ${repr(v)}`);
        return '{' + pairs.join(', ') + '}';
    }
    return String(obj);
}

function ascii(obj) {
    const r = repr(obj);
    return r.replace(/[^\x00-\x7F]/g, (char) => {
        const code = char.charCodeAt(0);
        if (code < 256) {
            return '\\x' + code.toString(16).padStart(2, '0');
        }
        return '\\u' + code.toString(16).padStart(4, '0');
    });
}

/**
 * Python str() for f-strings - mimics Python's str() behavior.
 * 
 * In Python f-strings, str() is used (not repr()):
 * - Top-level strings: no quotes (f"{'hello'}" → "hello")
 * - Collections: repr-like with quoted strings inside (f"{['a']}" → "['a']")
 * - Other types: String() conversion
 * 
 * @param {*} obj - Object to convert
 * @param {boolean} inCollection - Whether we're inside a collection (strings get quotes)
 * @returns {string} String representation for f-strings
 */
function fstr(obj, inCollection = false) {
    // For strings: no quotes at top level, but quotes inside collections
    if (typeof obj === 'string') {
        return inCollection ? `'${obj.replace(/'/g, "\\'")}'` : obj;
    }
    
    // For collections, use repr-like behavior (str() for collections is same as repr())
    // Elements inside collections should use repr (with quotes for strings)
    if (Array.isArray(obj)) {
        return '[' + obj.map(item => fstr(item, true)).join(', ') + ']';
    }
    if (typeof obj === 'object' && obj !== null && obj.constructor === Object) {
        const pairs = Object.entries(obj).map(([k, v]) => {
            // Keys: always use repr (with quotes for strings)
            const keyStr = typeof k === 'string' ? `'${k.replace(/'/g, "\\'")}'` : fstr(k, true);
            // Values: use repr (with quotes for strings)
            return `${keyStr}: ${fstr(v, true)}`;
        });
        return '{' + pairs.join(', ') + '}';
    }
    
    // For other types, use String() (Python's str() behavior)
    if (obj === null) return 'None';
    if (obj === undefined) return 'None';
    if (typeof obj === 'boolean') return obj ? 'True' : 'False';
    return String(obj);
}

/**
 * Python str() - converts object to string using __str__ if available.
 * 
 * FUNDAMENTAL FIX: This is the single source of truth for Python string conversion.
 * Both str() and print() use this, ensuring consistency.
 * 
 * Python semantics:
 * 1. If object has __str__() → call it (transpiled as toString())
 * 2. Else if object has __repr__() → call it (transpiled as Symbol.for("repr"))
 * 3. Else → use default string representation
 * 
 * @param {*} obj - Object to convert to string
 * @returns {string} String representation
 */
function py_str(obj) {
    // Handle arrays FIRST (before checking for toString on objects)
    // Arrays should use Python list representation
    if (Array.isArray(obj)) {
        // Phase 33.2: Check if this is an array of pairs (dict items) - format as Python tuples
        // This matches Python's behavior where sorted(dict.items()) outputs tuples
        if (obj.length > 0 && Array.isArray(obj[0]) && obj[0].length === 2) {
            return '[' + obj.map(([k, v]) => '(' + py_str(k) + ', ' + py_str(v) + ')').join(', ') + ']';
        }
        return '[' + obj.map(py_str).join(', ') + ']';
    }
    
    // If object has custom toString() (from __str__), use it
    if (obj !== null && obj !== undefined && typeof obj === 'object') {
        // Check if toString is overridden (not the default Object.prototype.toString)
        const proto = Object.getPrototypeOf(obj);
        if (proto && proto.hasOwnProperty('toString')) {
            const str = obj.toString();
            // Only use it if it's not the default "[object Object]"
            if (str !== '[object Object]') {
                return str;
            }
        }
        // Also check if toString is directly on the object
        if (obj.toString && obj.toString !== Object.prototype.toString) {
            const str = obj.toString();
            if (str !== '[object Object]') {
                return str;
            }
        }
        
        // Check for __repr__ (Symbol.for("repr"))
        const reprSym = Symbol.for('repr');
        if (typeof obj[reprSym] === 'function') {
            return obj[reprSym]();
        }
    }
    
    // Fallback: use Python-compatible string representation
    if (obj === null) return 'None';
    if (obj === undefined) return 'None';
    if (typeof obj === 'string') return obj;
    if (typeof obj === 'boolean') return obj ? 'True' : 'False';
    if (typeof obj === 'object') {
        // Default object representation (for objects without __str__)
        const entries = Object.entries(obj).map(([k, v]) => `${k}: ${py_str(v)}`);
        return '{' + entries.join(', ') + '}';
    }
    return String(obj);
}

/**
 * Python print() - prints values using Python str() semantics.
 * 
 * FUNDAMENTAL FIX: Uses __py.str() for each argument, ensuring print() and str()
 * use the same conversion logic.
 * 
 * @param {...*} args - Values to print
 */
function py_print(...args) {
    // Check for sep/end kwargs at end (if last arg is an object with sep/end properties)
    let sep = ' ';
    let end = '\n';
    let actualArgs = args;
    
    if (args.length > 0 && typeof args[args.length - 1] === 'object' && args[args.length - 1] !== null) {
        const lastArg = args[args.length - 1];
        // Check if it's a kwargs object (has sep or end properties)
        if ('sep' in lastArg || 'end' in lastArg) {
            actualArgs = args.slice(0, -1);
            if ('sep' in lastArg) sep = lastArg.sep;
            if ('end' in lastArg) end = lastArg.end;
        }
    }
    
    // FUNDAMENTAL FIX: Convert each argument using py_str() before joining
    const strArgs = actualArgs.map(py_str);
    console.log(strArgs.join(sep));
}

// =============================================================================
// STRING METHODS (Phase 18.3)
// =============================================================================

const str = {
    split: function(s, sep = null, maxsplit = -1) {
        if (s === '') return sep === null ? [] : [''];
        if (sep === null) {
            const trimmed = s.trim();
            if (trimmed === '') return [];
            if (maxsplit < 0) return trimmed.split(/\s+/);
            // With maxsplit, preserve original whitespace in remainder
            const result = [];
            let remaining = s.trimStart();
            let count = 0;
            while (count < maxsplit && remaining.length > 0) {
                const match = remaining.match(/^\S+/);
                if (!match) break;
                result.push(match[0]);
                remaining = remaining.slice(match[0].length);
                const wsMatch = remaining.match(/^\s+/);
                if (wsMatch) remaining = remaining.slice(wsMatch[0].length);
                count++;
            }
            if (remaining.length > 0) result.push(remaining);
            return result;
        }
        if (maxsplit < 0) return s.split(sep);
        const parts = s.split(sep);
        if (maxsplit >= parts.length - 1) return parts;
        const result = parts.slice(0, maxsplit);
        result.push(parts.slice(maxsplit).join(sep));
        return result;
    },
    rsplit: function(s, sep = null, maxsplit = -1) {
        if (maxsplit < 0) return str.split(s, sep, -1);
        const parts = str.split(s, sep, -1);
        if (maxsplit >= parts.length - 1) return parts;
        const splitPoint = parts.length - maxsplit;
        const result = [parts.slice(0, splitPoint).join(sep || ' ')];
        result.push(...parts.slice(splitPoint));
        return result;
    },
    index: function(s, sub, start = 0, end = null) {
        const searchIn = end === null ? s.slice(start) : s.slice(start, end);
        const idx = searchIn.indexOf(sub);
        if (idx === -1) throw new Error('substring not found');
        return idx + start;
    },
    rindex: function(s, sub, start = 0, end = null) {
        const searchIn = end === null ? s.slice(start) : s.slice(start, end);
        const idx = searchIn.lastIndexOf(sub);
        if (idx === -1) throw new Error('substring not found');
        return idx + start;
    },
    count: function(s, sub, start = 0, end = null) {
        const searchIn = end === null ? s.slice(start) : s.slice(start, end);
        if (sub === '') return searchIn.length + 1;
        let count = 0, pos = 0;
        while ((pos = searchIn.indexOf(sub, pos)) !== -1) { count++; pos += sub.length; }
        return count;
    },
    title: function(s) {
        // Browser-compatible version (no lookbehind)
        let result = '';
        let capitalizeNext = true;
        for (const c of s) {
            if (/[a-zA-Z]/.test(c)) {
                result += capitalizeNext ? c.toUpperCase() : c.toLowerCase();
                capitalizeNext = false;
            } else {
                result += c;
                capitalizeNext = true;
            }
        }
        return result;
    },
    capitalize: function(s) {
        if (s.length === 0) return s;
        return s[0].toUpperCase() + s.slice(1).toLowerCase();
    },
    swapcase: function(s) {
        return s.split('').map(c => c === c.toUpperCase() ? c.toLowerCase() : c.toUpperCase()).join('');
    },
    center: function(s, width, fillchar = ' ') {
        if (s.length >= width) return s;
        const totalPad = width - s.length;
        const leftPad = Math.floor(totalPad / 2);
        return fillchar.repeat(leftPad) + s + fillchar.repeat(totalPad - leftPad);
    },
    ljust: function(s, width, fillchar = ' ') {
        if (s.length >= width) return s;
        return s + fillchar.repeat(width - s.length);
    },
    rjust: function(s, width, fillchar = ' ') {
        if (s.length >= width) return s;
        return fillchar.repeat(width - s.length) + s;
    },
    zfill: function(s, width) {
        if (s.length >= width) return s;
        const sign = (s[0] === '+' || s[0] === '-') ? s[0] : '';
        const rest = sign ? s.slice(1) : s;
        return sign + rest.padStart(width - sign.length, '0');
    },
    strip: function(s, chars = null) {
        if (chars === null) return s.trim();
        const regex = new RegExp(`^[${chars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}]+|[${chars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}]+$`, 'g');
        return s.replace(regex, '');
    },
    lstrip: function(s, chars = null) {
        if (chars === null) return s.trimStart();
        const regex = new RegExp(`^[${chars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}]+`);
        return s.replace(regex, '');
    },
    rstrip: function(s, chars = null) {
        if (chars === null) return s.trimEnd();
        const regex = new RegExp(`[${chars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}]+$`);
        return s.replace(regex, '');
    },
    replace: function(s, old, new_, count = -1) {
        if (count < 0) return s.replaceAll(old, new_);
        let result = s, replaced = 0, pos = 0;
        while (replaced < count && (pos = result.indexOf(old, pos)) !== -1) {
            result = result.slice(0, pos) + new_ + result.slice(pos + old.length);
            pos += new_.length;
            replaced++;
        }
        return result;
    },
    partition: function(s, sep) {
        const idx = s.indexOf(sep);
        if (idx === -1) return [s, '', ''];
        return [s.slice(0, idx), sep, s.slice(idx + sep.length)];
    },
    rpartition: function(s, sep) {
        const idx = s.lastIndexOf(sep);
        if (idx === -1) return ['', '', s];
        return [s.slice(0, idx), sep, s.slice(idx + sep.length)];
    },
    splitlines: function(s, keepends = false) {
        const lineBreaks = /\r\n|\r|\n|\x0b|\x0c|\x1c|\x1d|\x1e|\x85|\u2028|\u2029/g;
        if (keepends) {
            const result = [];
            let lastEnd = 0;
            let match;
            while ((match = lineBreaks.exec(s)) !== null) {
                result.push(s.slice(lastEnd, match.index + match[0].length));
                lastEnd = match.index + match[0].length;
            }
            if (lastEnd < s.length) result.push(s.slice(lastEnd));
            return result;
        }
        return s.split(lineBreaks);
    },
    isdigit: function(s) {
        if (s.length === 0) return false;
        for (const c of s) if (!/\d/.test(c)) return false;
        return true;
    },
    isalpha: function(s) {
        if (s.length === 0) return false;
        for (const c of s) {
            if (c.toLowerCase() === c.toUpperCase() && !/[a-zA-Z]/.test(c)) {
                const code = c.charCodeAt(0);
                if (!((code >= 0x4E00 && code <= 0x9FFF) || (code >= 0x00C0 && code <= 0x024F) ||
                      (code >= 0x0400 && code <= 0x04FF) || (code >= 0x0370 && code <= 0x03FF))) {
                    return false;
                }
            }
        }
        return true;
    },
    isalnum: function(s) {
        if (s.length === 0) return false;
        for (const c of s) if (!this.isalpha(c) && !this.isdigit(c)) return false;
        return true;
    },
    isspace: s => s.length > 0 && /^\s+$/.test(s),
    isupper: function(s) {
        if (s.length === 0) return false;
        let hasCased = false;
        for (const c of s) {
            if (c.toLowerCase() !== c.toUpperCase()) {
                hasCased = true;
                if (c !== c.toUpperCase()) return false;
            }
        }
        return hasCased;
    },
    islower: function(s) {
        if (s.length === 0) return false;
        let hasCased = false;
        for (const c of s) {
            if (c.toLowerCase() !== c.toUpperCase()) {
                hasCased = true;
                if (c !== c.toLowerCase()) return false;
            }
        }
        return hasCased;
    },
    isnumeric: function(s) {
        if (s.length === 0) return false;
        for (const c of s) if (!/\d/.test(c)) return false;
        return true;
    },
    isdecimal: function(s) {
        if (s.length === 0) return false;
        for (const c of s) if (!/[0-9]/.test(c)) return false;
        return true;
    },
    isidentifier: function(s) {
        if (s.length === 0) return false;
        if (/[0-9]/.test(s[0])) return false;
        if (!this.isalpha(s[0]) && s[0] !== '_') return false;
        for (let i = 1; i < s.length; i++) {
            if (!this.isalpha(s[i]) && !this.isdigit(s[i]) && s[i] !== '_') return false;
        }
        return true;
    },
    expandtabs: function(s, tabsize = 8) {
        let result = '', col = 0;
        for (const c of s) {
            if (c === '\t') {
                const spaces = tabsize - (col % tabsize);
                result += ' '.repeat(spaces);
                col += spaces;
            } else if (c === '\n' || c === '\r') {
                result += c;
                col = 0;
            } else {
                result += c;
                col++;
            }
        }
        return result;
    },
};

// =============================================================================
// LIST METHODS (Phase 18.3)
// =============================================================================

const list = {
    remove: function(arr, value) {
        for (let i = 0; i < arr.length; i++) {
            if (eq(arr[i], value)) {
                arr.splice(i, 1);
                return;
            }
        }
        throw new Error('list.remove(x): x not in list');
    },
    index: function(arr, value, start = 0, stop = null) {
        const end = stop === null ? arr.length : stop;
        for (let i = start; i < end && i < arr.length; i++) {
            if (eq(arr[i], value)) return i;
        }
        throw new Error('x is not in list');
    },
    count: function(arr, value) {
        let count = 0;
        for (const item of arr) { if (eq(item, value)) count++; }
        return count;
    },
    sort: function(arr, key = null, reverse = false) {
        arr.sort((a, b) => {
            const keyA = key ? key(a) : a;
            const keyB = key ? key(b) : b;
            const typeA = typeof keyA;
            const typeB = typeof keyB;
            // Python 3: TypeError on mixed types
            if (typeA !== typeB && keyA != null && keyB != null) {
                throw new TypeError(`'<' not supported between instances of '${typeA}' and '${typeB}'`);
            }
            if (typeA === 'number' && typeB === 'number') {
                return reverse ? keyB - keyA : keyA - keyB;
            }
            if (typeA === 'string' && typeB === 'string') {
                if (keyA < keyB) return reverse ? 1 : -1;
                if (keyA > keyB) return reverse ? -1 : 1;
                return 0;
            }
            const strA = String(keyA), strB = String(keyB);
            if (strA < strB) return reverse ? 1 : -1;
            if (strA > strB) return reverse ? -1 : 1;
            return 0;
        });
    },
    pop: function(arr, index = -1) {
        if (arr.length === 0) throw new Error('pop from empty list');
        if (index < 0) index = arr.length + index;
        if (index < 0 || index >= arr.length) throw new Error('pop index out of range');
        return arr.splice(index, 1)[0];
    },
    insert: function(arr, index, value) {
        // Python: insert(-1, x) inserts BEFORE the last element
        if (index < 0) index = Math.max(0, arr.length + index);
        if (index > arr.length) index = arr.length;
        arr.splice(index, 0, value);
    },
    extend: function(arr, iterable) { for (const item of iterable) arr.push(item); },
    clear: function(arr) { arr.length = 0; },
    copy: function(arr) { return [...arr]; },
    reverse: function(arr) { arr.reverse(); },
    append: function(arr, value) { arr.push(value); },
};

// =============================================================================
// DICT METHODS (Phase 18.3)
// =============================================================================

const dict = {
    pop: function(d, key, defaultValue = undefined) {
        if (key in d) {
            const value = d[key];
            delete d[key];
            return value;
        }
        if (defaultValue !== undefined) return defaultValue;
        throw new Error(`KeyError: '${key}'`);
    },
    get: function(d, key, defaultValue = null) {
        if (key in d) return d[key];
        return defaultValue;
    },
    setdefault: function(d, key, defaultValue = null) {
        if (!(key in d)) d[key] = defaultValue;
        return d[key];
    },
    popitem: function(d) {
        const keys = Object.keys(d);
        if (keys.length === 0) throw new Error('dictionary is empty');
        const key = keys[keys.length - 1];
        const value = d[key];
        delete d[key];
        return [key, value];
    },
    update: function(d, other = null, kwargs = {}) {
        if (other !== null) {
            if (typeof other[Symbol.iterator] === 'function' && !Array.isArray(other) && typeof other !== 'string') {
                for (const [k, v] of other) d[k] = v;
            } else if (typeof other === 'object') {
                Object.assign(d, other);
            }
        }
        Object.assign(d, kwargs);
    },
    clear: function(d) {
        for (const key in d) {
            if (Object.prototype.hasOwnProperty.call(d, key)) delete d[key];
        }
    },
    copy: function(d) { return { ...d }; },
    keys: function(d) { return Object.keys(d); },
    values: function(d) { return Object.values(d); },
    items: function(d) { return Object.entries(d); },
    fromkeys: function(keys, value = null) {
        const d = {};
        for (const k of keys) d[k] = value;
        return d;
    },
};

// =============================================================================
// SET METHODS (Phase 18.3)
// =============================================================================

const set = {
    remove: function(s, elem) {
        if (!s.has(elem)) throw new Error(`KeyError: ${elem}`);
        s.delete(elem);
    },
    discard: function(s, elem) { s.delete(elem); },
    pop: function(s) {
        if (s.size === 0) throw new Error('pop from an empty set');
        const elem = s.values().next().value;
        s.delete(elem);
        return elem;
    },
    add: function(s, elem) { s.add(elem); },
    update: function(s, ...iterables) {
        for (const iterable of iterables) {
            for (const elem of iterable) s.add(elem);
        }
    },
    clear: function(s) { s.clear(); },
    copy: function(s) { return new Set(s); },
    union: function(s, ...others) {
        const result = new Set(s);
        for (const other of others) {
            for (const elem of other) result.add(elem);
        }
        return result;
    },
    intersection: function(s, ...others) {
        let result = new Set(s);
        for (const other of others) {
            const otherSet = new Set(other);
            result = new Set([...result].filter(x => otherSet.has(x)));
        }
        return result;
    },
    difference: function(s, ...others) {
        const result = new Set(s);
        for (const other of others) {
            for (const elem of other) result.delete(elem);
        }
        return result;
    },
    symmetric_difference: function(s, other) {
        const otherSet = new Set(other);
        const result = new Set();
        for (const elem of s) { if (!otherSet.has(elem)) result.add(elem); }
        for (const elem of otherSet) { if (!s.has(elem)) result.add(elem); }
        return result;
    },
    issubset: function(s, other) {
        const otherSet = other instanceof Set ? other : new Set(other);
        for (const elem of s) { if (!otherSet.has(elem)) return false; }
        return true;
    },
    issuperset: function(s, other) {
        const otherSet = other instanceof Set ? other : new Set(other);
        for (const elem of otherSet) { if (!s.has(elem)) return false; }
        return true;
    },
    isdisjoint: function(s, other) {
        for (const elem of other) { if (s.has(elem)) return false; }
        return true;
    },
};

// =============================================================================
// ENHANCED BUILTINS (Phase 18.4)
// =============================================================================

function sorted(iterable, key = null, reverse = false) {
    const arr = [...iterable];
    if (arr.length === 0) return arr;
    
    // Pre-compute keys and check types
    const keyed = arr.map((item, idx) => ({
        item,
        key: key ? key(item) : item,
        idx  // For stable sort
    }));
    
    // Check for mixed types (Python 3 throws TypeError)
    const firstType = typeof keyed[0].key;
    for (let i = 1; i < keyed.length; i++) {
        const t = typeof keyed[i].key;
        if (t !== firstType && keyed[i].key != null && keyed[0].key != null) {
            throw new TypeError(`'<' not supported between instances of '${firstType}' and '${t}'`);
        }
    }
    
    keyed.sort((a, b) => {
        const keyA = a.key;
        const keyB = b.key;
        
        // Handle null/undefined
        if (keyA == null && keyB == null) return a.idx - b.idx;  // Stable
        if (keyA == null) return reverse ? -1 : 1;
        if (keyB == null) return reverse ? 1 : -1;
        
        let cmp;
        if (typeof keyA === 'number' && typeof keyB === 'number') {
            cmp = keyA - keyB;
        } else {
            // Lexicographic comparison (works for strings)
            if (keyA < keyB) cmp = -1;
            else if (keyA > keyB) cmp = 1;
            else cmp = 0;
        }
        
        // Apply reverse, then use index for stability
        if (cmp === 0) return a.idx - b.idx;
        return reverse ? -cmp : cmp;
    });
    
    return keyed.map(k => k.item);
}

function min(iterable, key = null) {
    const arr = [...iterable];
    
    if (arr.length === 0) {
        throw new Error("min() arg is an empty sequence");
    }
    
    // Check for mixed types (Python 3 throws TypeError)
    if (key === null) {
        const firstType = typeof arr[0];
        for (let i = 1; i < arr.length; i++) {
            const t = typeof arr[i];
            if (t !== firstType && arr[i] != null && arr[0] != null) {
                throw new TypeError(`'<' not supported between instances of '${firstType}' and '${t}'`);
            }
        }
    }
    
    if (key) {
        return arr.reduce((a, b) => key(a) <= key(b) ? a : b);
    }
    return arr.reduce((a, b) => a <= b ? a : b);
}

function max(iterable, key = null) {
    const arr = [...iterable];
    
    if (arr.length === 0) {
        throw new Error("max() arg is an empty sequence");
    }
    
    // Check for mixed types (Python 3 throws TypeError)
    if (key === null) {
        const firstType = typeof arr[0];
        for (let i = 1; i < arr.length; i++) {
            const t = typeof arr[i];
            if (t !== firstType && arr[i] != null && arr[0] != null) {
                throw new TypeError(`'<' not supported between instances of '${firstType}' and '${t}'`);
            }
        }
    }
    
    if (key) {
        return arr.reduce((a, b) => key(a) >= key(b) ? a : b);
    }
    return arr.reduce((a, b) => a >= b ? a : b);
}

function any(iterable) {
    for (const x of iterable) if (bool(x)) return true;
    return false;
}

function all(iterable) {
    for (const x of iterable) if (!bool(x)) return false;
    return true;
}

function divmod(a, b) {
    return [floordiv(a, b), mod(a, b)];
}

/**
 * Return x**y, optionally modulo z.
 * 
 * Phase 33.2: Supports __pow__ dunder method for custom classes.
 * 
 * @param {*} x - Base (number or object with __pow__ method)
 * @param {number} y - Exponent
 * @param {number|null} z - Optional modulus
 * @returns {number}
 */
function pow(x, y, z = null) {
    // Phase 33.2: Check for __pow__ dunder method (only for 2-arg case)
    if (z === null) {
        if (typeof x === 'object' && x !== null && typeof x.__pow__ === 'function') {
            return x.__pow__(y);
        }
        return Math.pow(x, y);
    }
    
    // 3-arg case: modular exponentiation
    if (Number.isInteger(x) && Number.isInteger(y) && Number.isInteger(z)) {
        let result = 1;
        x = x % z;
        while (y > 0) {
            if (y % 2 === 1) result = (result * x) % z;
            y = Math.floor(y / 2);
            x = (x * x) % z;
        }
        return result;
    }
    return Math.pow(x, y) % z;
}

/**
 * Return absolute value of a number.
 * 
 * Phase 33.2: Supports __abs__ dunder method for custom classes.
 * 
 * @param {*} x - Number or object with __abs__ method
 * @returns {number}
 */
function abs(x) {
    // Phase 33.2: Check for __abs__ dunder method
    if (typeof x === 'object' && x !== null && typeof x.__abs__ === 'function') {
        return x.__abs__();
    }
    // Fallback: Math.abs for numbers
    return Math.abs(x);
}

function callable(obj) {
    return typeof obj === 'function';
}

function filter(func, iterable) {
    const arr = [...iterable];
    // Handle None/null/undefined - use Python truthiness
    if (func == null) {
        return arr.filter(x => bool(x));
    }
    return arr.filter(func);
}

function pyMap(func, ...iterables) {
    if (iterables.length === 1) return [...iterables[0]].map(func);
    const arrays = iterables.map(it => [...it]);
    const minLen = Math.min(...arrays.map(a => a.length));
    const result = [];
    for (let i = 0; i < minLen; i++) result.push(func(...arrays.map(a => a[i])));
    return result;
}

function reversed(iterable) {
    return [...iterable].reverse();
}

function round(x, ndigits = 0) {
    const factor = Math.pow(10, ndigits);
    const scaled = x * factor;
    
    // Check if exactly at .5
    const floor = Math.floor(scaled);
    const decimal = scaled - floor;
    
    // Banker's rounding: round .5 to nearest even
    if (Math.abs(decimal - 0.5) < 1e-9) {
        // Exactly at .5 - round to even
        if (floor % 2 === 0) {
            return floor / factor;
        } else {
            return (floor + 1) / factor;
        }
    }
    
    // Normal rounding for other cases
    return Math.round(scaled) / factor;
}

/**
 * Pythonic length with __len__ support.
 * 
 * Phase 33.2: Checks for length getter (from __len__ dunder).
 * 
 * @param {*} obj - Object to get length of
 * @returns {number} Length
 */
function len(obj) {
    if (obj == null) throw new TypeError("object of type 'NoneType' has no len()");
    
    // Phase 33.2: Check for __len__ dunder method (via length getter)
    if (typeof obj === 'object' && obj !== null) {
        // Check if this is a getter (not a regular property)
        const descriptor = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(obj) || obj, 'length');
        if (descriptor && typeof descriptor.get === 'function') {
            return obj.length;
        }
        // Also check if length is a number (might be a getter on the instance)
        if (typeof obj.length === 'number') {
            return obj.length;
        }
    }
    
    // Default length checks
    if (typeof obj === 'string' || Array.isArray(obj)) return obj.length;
    if (obj instanceof Map || obj instanceof Set) return obj.size;
    if (typeof obj === 'object') return Object.keys(obj).length;
    throw new TypeError(`object of type '${typeof obj}' has no len()`);
}

// =============================================================================
// STANDARD LIBRARY (Phase 18.4)
// =============================================================================

const json = {
    loads: s => JSON.parse(s),
    dumps: function(obj, indent = null, sort_keys = false) {
        if (sort_keys && obj !== null && typeof obj === 'object') {
            obj = this._sortKeys(obj);
        }
        return JSON.stringify(obj, null, indent);
    },
    _sortKeys: function(obj) {
        if (Array.isArray(obj)) return obj.map(x => this._sortKeys(x));
        if (obj !== null && typeof obj === 'object') {
            const sorted = {};
            Object.keys(obj).sort().forEach(key => { sorted[key] = this._sortKeys(obj[key]); });
            return sorted;
        }
        return obj;
    }
};

const math = {
    pi: Math.PI,
    e: Math.E,
    tau: 2 * Math.PI,
    inf: Infinity,
    nan: NaN,
    floor: Math.floor,
    ceil: Math.ceil,
    trunc: Math.trunc,
    sqrt: Math.sqrt,
    pow: Math.pow,
    exp: Math.exp,
    log: (x, base = null) => base === null ? Math.log(x) : Math.log(x) / Math.log(base),
    log10: Math.log10,
    log2: Math.log2,
    sin: Math.sin,
    cos: Math.cos,
    tan: Math.tan,
    asin: Math.asin,
    acos: Math.acos,
    atan: Math.atan,
    atan2: Math.atan2,
    sinh: Math.sinh,
    cosh: Math.cosh,
    tanh: Math.tanh,
    asinh: Math.asinh,
    acosh: Math.acosh,
    atanh: Math.atanh,
    hypot: Math.hypot,
    degrees: x => x * (180 / Math.PI),
    radians: x => x * (Math.PI / 180),
    isnan: x => Number.isNaN(x),
    isinf: x => !Number.isFinite(x) && !Number.isNaN(x),
    isfinite: x => Number.isFinite(x),
    fabs: Math.abs,
    factorial: function(n) {
        if (n < 0 || !Number.isInteger(n)) throw new Error("factorial() not defined for negative values");
        if (n === 0 || n === 1) return 1;
        let result = 1;
        for (let i = 2; i <= n; i++) result *= i;
        return result;
    },
    gcd: function(a, b) {
        a = Math.abs(Math.floor(a));
        b = Math.abs(Math.floor(b));
        while (b) { [a, b] = [b, a % b]; }
        return a;
    },
    lcm: function(a, b) {
        if (a === 0 || b === 0) return 0;
        return Math.abs(Math.floor(a) * Math.floor(b)) / this.gcd(a, b);
    },
    modf: x => [x - Math.trunc(x), Math.trunc(x)],
    copysign: (x, y) => Math.abs(x) * Math.sign(y),
};

const re = {
    match: function(pattern, string, flags = '') {
        let regex, m;
        try {
            regex = new RegExp('^' + pattern, flags + 'd');
            m = regex.exec(string);
        } catch (e) {
            regex = new RegExp('^' + pattern, flags);
            m = regex.exec(string);
        }
        return m ? this._createMatch(m, string) : null;
    },
    search: function(pattern, string, flags = '') {
        let regex, m;
        try {
            regex = new RegExp(pattern, flags + 'd');
            m = regex.exec(string);
        } catch (e) {
            regex = new RegExp(pattern, flags);
            m = regex.exec(string);
        }
        return m ? this._createMatch(m, string) : null;
    },
    findall: (pattern, string, flags = '') => string.match(new RegExp(pattern, flags + 'g')) || [],
    sub: function(pattern, repl, string, count = 0, flags = '') {
        if (count === 0) return string.replace(new RegExp(pattern, flags + 'g'), repl);
        let result = string, n = 0;
        while (n < count) {
            const newResult = result.replace(new RegExp(pattern, flags), repl);
            if (newResult === result) break;
            result = newResult;
            n++;
        }
        return result;
    },
    split: function(pattern, string, maxsplit = 0, flags = '') {
        if (maxsplit === 0) return string.split(new RegExp(pattern, flags));
        const result = [];
        let remaining = string, n = 0;
        while (n < maxsplit) {
            const m = remaining.match(new RegExp(pattern, flags));
            if (!m) break;
            result.push(remaining.slice(0, m.index));
            remaining = remaining.slice(m.index + m[0].length);
            n++;
        }
        result.push(remaining);
        return result;
    },
    escape: string => string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'),
    compile: function(pattern, flags = '') {
        const self = this;
        return {
            pattern, flags,
            match: string => self.match(pattern, string, flags),
            search: string => self.search(pattern, string, flags),
            findall: string => self.findall(pattern, string, flags),
            sub: (repl, string, count = 0) => self.sub(pattern, repl, string, count, flags),
            split: (string, maxsplit = 0) => self.split(pattern, string, maxsplit, flags),
        };
    },
    fullmatch: function(pattern, string, flags = '') {
        let regex, m;
        try {
            regex = new RegExp('^' + pattern + '$', flags + 'd');
            m = regex.exec(string);
        } catch (e) {
            regex = new RegExp('^' + pattern + '$', flags);
            m = regex.exec(string);
        }
        return m ? this._createMatch(m, string) : null;
    },
    _createMatch: function(m, string) {
        const fullMatchStart = m.index;
        const groupPositions = [];
        groupPositions[0] = { start: fullMatchStart, end: fullMatchStart + m[0].length };
        
        // Try to use indices if available (ES2022+)
        if (m.indices) {
            for (let i = 1; i < m.length; i++) {
                if (m.indices[i]) {
                    groupPositions[i] = { start: m.indices[i][0], end: m.indices[i][1] };
                } else {
                    groupPositions[i] = { start: -1, end: -1 };
                }
            }
        } else {
            // Fallback: estimate positions
            let searchStart = fullMatchStart;
            for (let i = 1; i < m.length; i++) {
                if (m[i] === undefined) {
                    groupPositions[i] = { start: -1, end: -1 };
                } else {
                    const groupStart = string.indexOf(m[i], searchStart);
                    if (groupStart >= 0 && groupStart < fullMatchStart + m[0].length) {
                        groupPositions[i] = { start: groupStart, end: groupStart + m[i].length };
                        searchStart = groupStart + m[i].length;
                    } else {
                        groupPositions[i] = { start: fullMatchStart, end: fullMatchStart + m[i].length };
                    }
                }
            }
        }
        
        return {
            group: (i = 0) => m[i],
            groups: () => m.slice(1),
            start: function(g = 0) {
                if (g >= groupPositions.length) throw new Error(`no such group: ${g}`);
                return groupPositions[g].start;
            },
            end: function(g = 0) {
                if (g >= groupPositions.length) throw new Error(`no such group: ${g}`);
                return groupPositions[g].end;
            },
            span: function(g = 0) { return [this.start(g), this.end(g)]; },
            string,
            lastindex: m.length > 1 ? m.length - 1 : null,
        };
    }
};

// Seedable PRNG using xorshift128+
let _randomState = null;

function _initRandomState(seed) {
    seed = seed >>> 0;
    function splitmix32(x) {
        x = Math.imul(x ^ (x >>> 16), 0x85ebca6b);
        x = Math.imul(x ^ (x >>> 13), 0xc2b2ae35);
        return (x ^ (x >>> 16)) >>> 0;
    }
    _randomState = {
        s0_lo: splitmix32(seed),
        s0_hi: splitmix32(seed + 1),
        s1_lo: splitmix32(seed + 2),
        s1_hi: splitmix32(seed + 3)
    };
}

function _nextU32() {
    if (_randomState === null) {
        return (Math.random() * 0x100000000) >>> 0;
    }
    let { s0_lo, s0_hi, s1_lo, s1_hi } = _randomState;
    let t_lo = s0_lo, t_hi = s0_hi;
    s0_lo = s1_lo; s0_hi = s1_hi;
    const shift23_hi = (t_lo << 23) | (t_hi >>> 9);
    const shift23_lo = t_lo << 23;
    t_lo ^= shift23_lo; t_hi ^= shift23_hi;
    const shift17_lo = (t_hi << 15) | (t_lo >>> 17);
    const shift17_hi = t_hi >>> 17;
    t_lo ^= shift17_lo; t_hi ^= shift17_hi;
    t_lo ^= s0_lo; t_hi ^= s0_hi;
    const shift26_lo = (s0_hi << 6) | (s0_lo >>> 26);
    const shift26_hi = s0_hi >>> 26;
    t_lo ^= shift26_lo; t_hi ^= shift26_hi;
    _randomState.s0_lo = s0_lo; _randomState.s0_hi = s0_hi;
    _randomState.s1_lo = t_lo >>> 0; _randomState.s1_hi = t_hi >>> 0;
    return ((s0_lo + t_lo) >>> 0);
}

function _randomFloat() {
    if (_randomState === null) return Math.random();
    return _nextU32() / 0x100000000;
}

const random = {
    random: () => _randomFloat(),
    uniform: (a, b) => a + _randomFloat() * (b - a),
    randint: (a, b) => Math.floor(_randomFloat() * (b - a + 1)) + a,
    randrange: function(start, stop = null, step = 1) {
        if (stop === null) { stop = start; start = 0; }
        const count = Math.ceil((stop - start) / step);
        return start + step * Math.floor(_randomFloat() * count);
    },
    choice: function(seq) {
        if (seq.length === 0) throw new Error("Cannot choose from an empty sequence");
        return seq[Math.floor(_randomFloat() * seq.length)];
    },
    choices: function(population, k = 1, weights = null) {
        if (population.length === 0) throw new Error("Cannot choose from an empty population");
        const result = [];
        if (weights === null) {
            for (let i = 0; i < k; i++) result.push(population[Math.floor(_randomFloat() * population.length)]);
        } else {
            const cumWeights = [];
            let sum = 0;
            for (const w of weights) { sum += w; cumWeights.push(sum); }
            for (let i = 0; i < k; i++) {
                const r = _randomFloat() * sum;
                for (let j = 0; j < cumWeights.length; j++) {
                    if (r < cumWeights[j]) { result.push(population[j]); break; }
                }
            }
        }
        return result;
    },
    sample: function(population, k) {
        if (k > population.length) throw new Error("Sample larger than population");
        if (k < 0) throw new Error("Sample size cannot be negative");
        const copy = [...population];
        const result = [];
        for (let i = 0; i < k; i++) {
            const idx = Math.floor(_randomFloat() * copy.length);
            result.push(copy.splice(idx, 1)[0]);
        }
        return result;
    },
    shuffle: function(x) {
        for (let i = x.length - 1; i > 0; i--) {
            const j = Math.floor(_randomFloat() * (i + 1));
            [x[i], x[j]] = [x[j], x[i]];
        }
    },
    gauss: function(mu, sigma) {
        let u1, u2;
        do { u1 = _randomFloat(); u2 = _randomFloat(); } while (u1 === 0);
        const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
        return mu + z * sigma;
    },
    seed: function(a = null) {
        if (a === null || a === undefined) {
            _randomState = null;
        } else {
            let seedVal;
            if (typeof a === 'number') seedVal = Math.floor(a) >>> 0;
            else if (typeof a === 'string') {
                seedVal = 0;
                for (let i = 0; i < a.length; i++) {
                    seedVal = ((seedVal << 5) - seedVal + a.charCodeAt(i)) >>> 0;
                }
            } else seedVal = Number(a) >>> 0;
            _initRandomState(seedVal);
        }
    },
    getstate: function() {
        if (_randomState === null) return { type: 'math.random', state: null };
        return { type: 'xorshift128+', state: { ..._randomState } };
    },
    setstate: function(state) {
        if (state.type === 'math.random' || state.state === null) _randomState = null;
        else if (state.type === 'xorshift128+') _randomState = { ...state.state };
        else throw new Error("Invalid state object for random.setstate()");
    },
    expovariate: lambd => -Math.log(1 - _randomFloat()) / lambd,
    triangular: function(low = 0, high = 1, mode = null) {
        if (mode === null) mode = (low + high) / 2;
        const u = _randomFloat();
        const c = (mode - low) / (high - low);
        if (u < c) return low + Math.sqrt(u * (high - low) * (mode - low));
        return high - Math.sqrt((1 - u) * (high - low) * (high - mode));
    },
};

// =============================================================================
// DECORATORS (Phase 18.5)
// =============================================================================

function memoize(fn) {
    const cache = new Map();
    
    // Create stable cache key with type prefixes to avoid collisions
    function makeKey(args) {
        if (args.length === 0) return '__no_args__';
        if (args.length === 1) {
            const arg = args[0];
            if (arg === null) return '__null__';
            if (arg === undefined) return '__undefined__';
            const type = typeof arg;
            if (type === 'number' || type === 'string' || type === 'boolean' || type === 'symbol' || type === 'bigint') {
                return arg;
            }
            return '__obj__' + JSON.stringify(arg);
        }
        return '__multi__' + JSON.stringify(args.map(arg => {
            if (arg === null) return { __t: 'null' };
            if (arg === undefined) return { __t: 'undefined' };
            const type = typeof arg;
            if (type === 'symbol') return { __t: 'symbol', v: arg.toString() };
            if (type === 'bigint') return { __t: 'bigint', v: arg.toString() };
            return { __t: type, v: arg };
        }));
    }
    
    function memoized(...args) {
        const key = makeKey(args);
        if (!cache.has(key)) {
            cache.set(key, fn.apply(this, args));
        }
        return cache.get(key);
    }
    memoized.cache = cache;
    memoized.clear = () => cache.clear();
    return memoized;
}

function debounce(ms) {
    return function(fn) {
        let timeout = null;
        function debounced(...args) {
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(() => {
                fn.apply(this, args);
                timeout = null;
            }, ms);
        }
        debounced.cancel = () => {
            if (timeout) {
                clearTimeout(timeout);
                timeout = null;
            }
        };
        return debounced;
    };
}

function throttle(ms) {
    return function(fn) {
        let lastCall = 0;
        let timeout = null;
        function throttled(...args) {
            const now = Date.now();
            const remaining = ms - (now - lastCall);
            if (remaining <= 0) {
                lastCall = now;
                return fn.apply(this, args);
            } else if (!timeout) {
                timeout = setTimeout(() => {
                    lastCall = Date.now();
                    timeout = null;
                    fn.apply(this, args);
                }, remaining);
            }
        }
        throttled.cancel = () => {
            if (timeout) {
                clearTimeout(timeout);
                timeout = null;
            }
        };
        return throttled;
    };
}

function once(fn) {
    let called = false;
    let result;
    function onceFn(...args) {
        if (!called) {
            called = true;
            result = fn.apply(this, args);
        }
        return result;
    }
    onceFn.called = () => called;
    onceFn.reset = () => { called = false; result = undefined; };
    return onceFn;
}

function retry(maxRetries = 3, delay = 0) {
    return function(fn) {
        return async function(...args) {
            let lastError;
            for (let attempt = 0; attempt <= maxRetries; attempt++) {
                try {
                    return await fn.apply(this, args);
                } catch (error) {
                    lastError = error;
                    if (attempt < maxRetries && delay > 0) {
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                }
            }
            throw lastError;
        };
    };
}

function deprecated(message = '') {
    return function(fn) {
        let warned = false;
        function deprecatedFn(...args) {
            if (!warned) {
                warned = true;
                console.warn(`DEPRECATED: ${fn.name}${message ? `: ${message}` : ''}`);
            }
            return fn.apply(this, args);
        }
        return deprecatedFn;
    };
}

function log_calls(fn) {
    function logged(...args) {
        console.log(`CALL: ${fn.name}(${args.map(a => JSON.stringify(a)).join(', ')})`);
        const result = fn.apply(this, args);
        console.log(`RETURN: ${fn.name} => ${JSON.stringify(result)}`);
        return result;
    }
    return logged;
}

function timed(fn) {
    function timedFn(...args) {
        const start = Date.now();
        const result = fn.apply(this, args);
        const end = Date.now();
        console.log(`TIMING: ${fn.name} took ${end - start}ms`);
        return result;
    }
    return timedFn;
}

// =============================================================================
// EXPORT __py OBJECT
// =============================================================================

const __py = {
    at,
    slice,
    bool,
    mod,
    floordiv,
    eq,
    in: contains,
    contains,
    iter,
    next: py_next,
    add,
    mul,
    enumerate,
    zip,
    range,
    sum,
    del,
    del_slice,
    format,
    str_count,
    list_remove,
    dict_pop,
    dict_setdefault,
    dict: Object.assign(dict, {
        items: dict_items,
        pop: dict_pop,
        setdefault: dict_setdefault,
    }),
    isinstance,
    type,
    star_import,
    repr,
    fstr,
    str: Object.assign(py_str, str),  // str() function with string methods as properties
    print: py_print,
    ascii,
    // Type methods (Phase 18.3)
    list,
    set,
    // Enhanced builtins (Phase 18.4)
    sorted,
    min,
    max,
    any,
    all,
    divmod,
    pow,
    abs,
    callable,
    filter,
    map: pyMap,
    reversed,
    round,
    len,
    // Standard library (Phase 18.4)
    json,
    math,
    re,
    random,
    // Phase 33.2: Async support
    asyncio: {
        run: async (coro) => {
            // asyncio.run(coro) - runs async function and returns result
            // If coro is a function, call it; if it's already a Promise, await it
            if (typeof coro === 'function') {
                return await coro();
            }
            return await coro;
        },
        gather: async (...coros) => {
            // asyncio.gather(*coros) - runs multiple async functions concurrently
            // Handle both function references and Promises
            const promises = coros.map(coro => 
                typeof coro === 'function' ? coro() : coro
            );
            return await Promise.all(promises);
        },
    },
    // Decorators (Phase 18.5)
    memoize,
    debounce,
    throttle,
    once,
    retry,
    deprecated,
    log_calls,
    timed,
};

// =============================================================================
// CLASSES (Phase 33.1)
// =============================================================================

function applyMixins(targetClass, mixins) {
    for (const mixin of mixins) {
        // Get all property names from mixin prototype
        const propertyNames = Object.getOwnPropertyNames(mixin.prototype);
        
        for (const name of propertyNames) {
            // Skip constructor
            if (name === 'constructor') {
                continue;
            }
            
            // Copy property descriptor from mixin to target
            const descriptor = Object.getOwnPropertyDescriptor(mixin.prototype, name);
            if (descriptor) {
                Object.defineProperty(targetClass.prototype, name, descriptor);
            }
        }
    }
}

function createProperty({ get, set, delete: deleter }) {
    const descriptor = {};
    
    if (get) {
        descriptor.get = get;
    }
    
    if (set) {
        descriptor.set = set;
    }
    
    // JavaScript doesn't have a native delete descriptor, so we store
    // the deleter function as a custom property that can be called
    if (deleter) {
        descriptor.configurable = true; // Allow deletion
        // Store deleter as a symbol property
        const deleteSymbol = Symbol.for(`__delete_${Math.random()}`);
        descriptor[deleteSymbol] = deleter;
    }
    
    return descriptor;
}

function checkAbstract(abstractClass, instanceClass) {
    if (instanceClass === abstractClass) {
        throw new Error(`TypeError: Cannot instantiate abstract class ${abstractClass.name}`);
    }
}

// Make __py_classes available globally
global.__py_classes = { applyMixins, createProperty, checkAbstract };

// =============================================================================
// PHASE 33.2: DUNDER METHODS (Advanced Constructs)
// =============================================================================

// Dunder equality helpers
function dunders_equals(a, b) {
    // Same reference
    if (a === b) return true;
    
    // Handle null/undefined
    if (a == null || b == null) return a === b;
    
    // If a has __eq__ method (via equals), use it
    if (typeof a === 'object' && a !== null && typeof a.equals === 'function') {
        return a.equals(b);
    }
    
    // Arrays: deep equality
    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) return false;
        for (let i = 0; i < a.length; i++) {
            if (!dunders_equals(a[i], b[i])) return false;
        }
        return true;
    }
    
    // Objects: shallow equality
    if (typeof a === 'object' && typeof b === 'object' && !Array.isArray(a) && !Array.isArray(b)) {
        const keysA = Object.keys(a);
        const keysB = Object.keys(b);
        if (keysA.length !== keysB.length) return false;
        for (const key of keysA) {
            if (!(key in b)) return false;
            if (!dunders_equals(a[key], b[key])) return false;
        }
        return true;
    }
    
    // Primitive types: direct comparison
    return a === b;
}

function dunders_notEquals(a, b) {
    return !dunders_equals(a, b);
}

function dunders_repr(obj) {
    // If object has __repr__ method (via Symbol), use it
    if (typeof obj === 'object' && obj !== null) {
        const reprSym = Symbol.for('repr');
        if (typeof obj[reprSym] === 'function') {
            return obj[reprSym]();
        }
    }
    
    // Fallback to toString()
    if (obj === null) return 'null';
    if (obj === undefined) return 'undefined';
    if (typeof obj === 'string') return `'${obj}'`;
    if (Array.isArray(obj)) {
        return '[' + obj.map(dunders_repr).join(', ') + ']';
    }
    if (typeof obj === 'object') {
        const entries = Object.entries(obj).map(([k, v]) => `${k}: ${dunders_repr(v)}`);
        return '{' + entries.join(', ') + '}';
    }
    return String(obj);
}

function dunders_format(obj, format_spec) {
    // If object has __format__ method (via Symbol), use it
    if (typeof obj === 'object' && obj !== null) {
        const formatSym = Symbol.for('format');
        if (typeof obj[formatSym] === 'function') {
            return obj[formatSym](format_spec);
        }
    }
    
    // Fallback: basic formatting for numbers
    if (typeof obj === 'number') {
        if (format_spec === '.2f') {
            return obj.toFixed(2);
        }
        if (format_spec === ',') {
            return obj.toLocaleString();
        }
    }
    
    // Default: convert to string
    return String(obj);
}

// Proxy helpers for Phase 33.2
function createSubscriptProxy(target) {
    return {
        get(target, prop, receiver) {
            if (prop in target) {
                return Reflect.get(target, prop, receiver);
            }
            if (typeof target.__getitem__ === 'function') {
                return target.__getitem__(prop);
            }
            return undefined;
        },
        set(target, prop, value, receiver) {
            if (prop in target) {
                return Reflect.set(target, prop, value, receiver);
            }
            if (typeof target.__setitem__ === 'function') {
                target.__setitem__(prop, value);
                return true;
            }
            return Reflect.set(target, prop, value, receiver);
        },
        deleteProperty(target, prop) {
            if (prop in target) {
                return Reflect.deleteProperty(target, prop);
            }
            if (typeof target.__delitem__ === 'function') {
                target.__delitem__(prop);
                return true;
            }
            return Reflect.deleteProperty(target, prop);
        },
        has(target, prop) {
            if (prop in target) {
                return true;
            }
            if (typeof target.__contains__ === 'function') {
                return target.__contains__(prop);
            }
            if (typeof target.__getitem__ === 'function') {
                try {
                    target.__getitem__(prop);
                    return true;
                } catch (e) {
                    return false;
                }
            }
            return false;
        },
    };
}

function createAttributeProxy(target) {
    return {
        get(target, prop, receiver) {
            if (prop === '__proto__' || prop === 'constructor' || prop === 'prototype') {
                return Reflect.get(target, prop, receiver);
            }
            if (prop in target || Object.prototype.hasOwnProperty.call(target, prop)) {
                return Reflect.get(target, prop, receiver);
            }
            if (typeof target.__getattr__ === 'function') {
                try {
                    return target.__getattr__(prop);
                } catch (e) {
                    return undefined;
                }
            }
            return undefined;
        },
        set(target, prop, value, receiver) {
            if (prop === '__proto__' || prop === 'constructor' || prop === 'prototype') {
                return Reflect.set(target, prop, value, receiver);
            }
            if (prop in target || Object.prototype.hasOwnProperty.call(target, prop)) {
                return Reflect.set(target, prop, value, receiver);
            }
            if (typeof target.__setattr__ === 'function') {
                target.__setattr__(prop, value);
                return true;
            }
            return Reflect.set(target, prop, value, receiver);
        },
        deleteProperty(target, prop) {
            if (prop in target || Object.prototype.hasOwnProperty.call(target, prop)) {
                return Reflect.deleteProperty(target, prop);
            }
            if (typeof target.__delattr__ === 'function') {
                try {
                    target.__delattr__(prop);
                    return true;
                } catch (e) {
                    return false;
                }
            }
            return Reflect.deleteProperty(target, prop);
        },
    };
}

// Generator helpers for Phase 33.2
function wrapGenerator(gen) {
    let isClosed = false;
    
    return {
        next(value) {
            if (isClosed) {
                return { done: true, value: undefined };
            }
            try {
                // Python next(g) is equivalent to g.send(None)
                // So when value is undefined (no argument), pass null to match Python None
                const result = gen.next(value === undefined ? null : value);
                if (result.done) {
                    isClosed = true;
                }
                return result;
            } catch (e) {
                isClosed = true;
                throw e;
            }
        },
        send(value) {
            // Python send() returns the yielded value, not the result object
            const result = this.next(value);
            return result.value;
        },
        throw(exception) {
            if (isClosed) {
                throw exception;
            }
            try {
                const result = gen.throw(exception);
                if (result.done) {
                    isClosed = true;
                }
                return result;
            } catch (e) {
                isClosed = true;
                throw e;
            }
        },
        close() {
            if (isClosed) {
                return;
            }
            isClosed = true;
            try {
                gen.return();
            } catch (e) {
                // Ignore errors on close
            }
        },
        [Symbol.iterator]() {
            return this;
        },
    };
}

// Phase 33.2: Runtime helpers for subscript access (when Proxy isn't available)
function getitem(obj, key) {
    // Check for __getitem__ dunder method
    if (typeof obj === 'object' && obj !== null && typeof obj.__getitem__ === 'function') {
        return obj.__getitem__(key);
    }
    // Fallback: direct property access
    return obj[key];
}

function setitem(obj, key, value) {
    // Check for __setitem__ dunder method
    if (typeof obj === 'object' && obj !== null && typeof obj.__setitem__ === 'function') {
        obj.__setitem__(key, value);
        return;
    }
    // Fallback: direct property assignment
    obj[key] = value;
}

// Phase 33.2: Runtime helper for callable objects (objects with __call__ method)
function call(obj, ...args) {
    // Handle keyword arguments: if last arg is an object and has __kw__ property, it's kwargs
    let positionalArgs = args;
    let kwargs = null;
    if (args.length > 0 && typeof args[args.length - 1] === 'object' && args[args.length - 1] !== null && args[args.length - 1].__kw__ === true) {
        kwargs = args[args.length - 1];
        positionalArgs = args.slice(0, -1);
        // Remove __kw__ marker
        delete kwargs.__kw__;
    }
    
    // If obj is a function, call it directly
    if (typeof obj === 'function') {
        if (kwargs) {
            return obj(...positionalArgs, kwargs);
        }
        return obj(...positionalArgs);
    }
    // If obj has __call__ method, use it
    if (typeof obj === 'object' && obj !== null && typeof obj.__call__ === 'function') {
        if (kwargs) {
            return obj.__call__(...positionalArgs, kwargs);
        }
        return obj.__call__(...positionalArgs);
    }
    // Fallback: try to call as function (will throw if not callable)
    if (kwargs) {
        return obj(...positionalArgs, kwargs);
    }
    return obj(...positionalArgs);
}

// =============================================================================
// PHASE 33.2: DUNDER ARITHMETIC OPERATIONS
// =============================================================================

function dunders_add(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__add__ === 'function') {
        const result = a.__add__(b);
        if (result !== undefined && result !== null) return result;
    }
    if (typeof b === 'object' && b !== null && typeof b.__radd__ === 'function') {
        const result = b.__radd__(a);
        if (result !== undefined && result !== null) return result;
    }
    if (Array.isArray(a) && Array.isArray(b)) return [...a, ...b];
    return a + b;
}

function dunders_sub(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__sub__ === 'function') {
        const result = a.__sub__(b);
        if (result !== undefined && result !== null) return result;
    }
    if (typeof b === 'object' && b !== null && typeof b.__rsub__ === 'function') {
        const result = b.__rsub__(a);
        if (result !== undefined && result !== null) return result;
    }
    return a - b;
}

function dunders_mul(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__mul__ === 'function') {
        const result = a.__mul__(b);
        if (result !== undefined && result !== null) return result;
    }
    if (typeof b === 'object' && b !== null && typeof b.__rmul__ === 'function') {
        const result = b.__rmul__(a);
        if (result !== undefined && result !== null) return result;
    }
    if (typeof a === 'string' && typeof b === 'number') return a.repeat(b);
    if (typeof b === 'string' && typeof a === 'number') return b.repeat(a);
    if (Array.isArray(a) && typeof b === 'number') {
        const result = [];
        for (let i = 0; i < b; i++) result.push(...a);
        return result;
    }
    return a * b;
}

function dunders_truediv(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__truediv__ === 'function') {
        const result = a.__truediv__(b);
        if (result !== undefined && result !== null) return result;
    }
    if (typeof b === 'object' && b !== null && typeof b.__rtruediv__ === 'function') {
        const result = b.__rtruediv__(a);
        if (result !== undefined && result !== null) return result;
    }
    return a / b;
}

function dunders_floordiv(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__floordiv__ === 'function') {
        const result = a.__floordiv__(b);
        if (result !== undefined && result !== null) return result;
    }
    if (typeof b === 'object' && b !== null && typeof b.__rfloordiv__ === 'function') {
        const result = b.__rfloordiv__(a);
        if (result !== undefined && result !== null) return result;
    }
    return Math.floor(a / b);
}

function dunders_mod(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__mod__ === 'function') {
        const result = a.__mod__(b);
        if (result !== undefined && result !== null) return result;
    }
    if (typeof b === 'object' && b !== null && typeof b.__rmod__ === 'function') {
        const result = b.__rmod__(a);
        if (result !== undefined && result !== null) return result;
    }
    return ((a % b) + b) % b;
}

function dunders_pow(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__pow__ === 'function') {
        const result = a.__pow__(b);
        if (result !== undefined && result !== null) return result;
    }
    if (typeof b === 'object' && b !== null && typeof b.__rpow__ === 'function') {
        const result = b.__rpow__(a);
        if (result !== undefined && result !== null) return result;
    }
    return Math.pow(a, b);
}

function dunders_lshift(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__lshift__ === 'function') {
        const result = a.__lshift__(b);
        if (result !== undefined && result !== null) return result;
    }
    return a << b;
}

function dunders_rshift(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__rshift__ === 'function') {
        const result = a.__rshift__(b);
        if (result !== undefined && result !== null) return result;
    }
    return a >> b;
}

function dunders_bitand(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__and__ === 'function') {
        const result = a.__and__(b);
        if (result !== undefined && result !== null) return result;
    }
    return a & b;
}

function dunders_bitor(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__or__ === 'function') {
        const result = a.__or__(b);
        if (result !== undefined && result !== null) return result;
    }
    return a | b;
}

function dunders_bitxor(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__xor__ === 'function') {
        const result = a.__xor__(b);
        if (result !== undefined && result !== null) return result;
    }
    return a ^ b;
}

function dunders_neg(a) {
    if (typeof a === 'object' && a !== null && typeof a.__neg__ === 'function') {
        return a.__neg__();
    }
    return -a;
}

function dunders_pos(a) {
    if (typeof a === 'object' && a !== null && typeof a.__pos__ === 'function') {
        return a.__pos__();
    }
    return +a;
}

// In-place operators
function dunders_iadd(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__iadd__ === 'function') {
        return a.__iadd__(b);
    }
    return dunders_add(a, b);
}

function dunders_isub(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__isub__ === 'function') {
        return a.__isub__(b);
    }
    return dunders_sub(a, b);
}

function dunders_imul(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__imul__ === 'function') {
        return a.__imul__(b);
    }
    return dunders_mul(a, b);
}

function dunders_itruediv(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__itruediv__ === 'function') {
        return a.__itruediv__(b);
    }
    return dunders_truediv(a, b);
}

function dunders_ifloordiv(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__ifloordiv__ === 'function') {
        return a.__ifloordiv__(b);
    }
    return dunders_floordiv(a, b);
}

function dunders_imod(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__imod__ === 'function') {
        return a.__imod__(b);
    }
    return dunders_mod(a, b);
}

function dunders_ipow(a, b) {
    if (typeof a === 'object' && a !== null && typeof a.__ipow__ === 'function') {
        return a.__ipow__(b);
    }
    return dunders_pow(a, b);
}

// Add Phase 33.2 helpers to __py
__py.dunders = {
    // Equality
    equals: dunders_equals,
    notEquals: dunders_notEquals,
    repr: dunders_repr,
    format: dunders_format,
    // Arithmetic
    add: dunders_add,
    sub: dunders_sub,
    mul: dunders_mul,
    truediv: dunders_truediv,
    floordiv: dunders_floordiv,
    mod: dunders_mod,
    pow: dunders_pow,
    // Bitwise
    lshift: dunders_lshift,
    rshift: dunders_rshift,
    bitand: dunders_bitand,
    bitor: dunders_bitor,
    bitxor: dunders_bitxor,
    // Unary
    neg: dunders_neg,
    pos: dunders_pos,
    // In-place
    iadd: dunders_iadd,
    isub: dunders_isub,
    imul: dunders_imul,
    itruediv: dunders_itruediv,
    ifloordiv: dunders_ifloordiv,
    imod: dunders_imod,
    ipow: dunders_ipow,
};

__py.proxy = {
    createSubscriptProxy,
    createAttributeProxy,
};

// Async generator helpers for Phase 33.2+
/**
 * StopAsyncIteration exception for async generators.
 * 
 * WHAT: Exception raised by async generators when they are exhausted.
 * 
 * WHY: Python distinguishes between regular iterators (StopIteration) and
 *      async iterators (StopAsyncIteration). This enables proper exception
 *      handling in async for loops.
 * 
 * HOW: Raised automatically by async generators when they have no more values
 *      to yield. Caught by async for loops to signal completion.
 */
class StopAsyncIteration extends Error {
    constructor(value = undefined) {
        super('StopAsyncIteration');
        this.name = 'StopAsyncIteration';
        this.value = value;
    }
}

/**
 * Wrap an async JavaScript generator to support Python async generator protocol.
 * 
 * WHAT: Wraps an async generator (async function*) to add Python-style protocol
 *       methods: send(), throw(), close(). All methods return Promise<IteratorResult>.
 * 
 * WHY: JavaScript async generators don't have send(), throw(), close() methods.
 *      Python async generators support these methods for advanced iteration control.
 *      This wrapper provides Python compatibility.
 * 
 * HOW: 
 *     1. Wraps the async generator in an object with protocol methods
 *     2. next(), send(), throw() all return Promise<IteratorResult>
 *     3. Handles StopAsyncIteration (different from StopIteration)
 *     4. Tracks closed state to prevent operations on closed generators
 * 
 * @param {AsyncGenerator} gen - JavaScript async generator (from async function*)
 * @returns {object} Wrapped async generator with send(), throw(), close()
 */
function wrapAsyncGenerator(gen) {
    let isClosed = false;
    
    return {
        async next(value) {
            if (isClosed) {
                return Promise.resolve({ done: true, value: undefined });
            }
            try {
                // Python next(g) is equivalent to g.send(None)
                // So when value is undefined (no argument), pass null to match Python None
                const result = await gen.next(value === undefined ? null : value);
                if (result.done) {
                    isClosed = true;
                }
                return result;
            } catch (e) {
                isClosed = true;
                throw e;
            }
        },
        
        async send(value) {
            const result = await this.next(value);
            if (result.done) {
                // Generator is done - raise StopAsyncIteration
                throw new StopAsyncIteration(result.value);
            }
            return result.value;
        },
        
        async throw(exception) {
            if (isClosed) {
                throw exception;
            }
            try {
                const result = await gen.throw(exception);
                if (result.done) {
                    isClosed = true;
                }
                return result;
            } catch (e) {
                isClosed = true;
                throw e;
            }
        },
        
        async close() {
            if (isClosed) {
                return Promise.resolve();
            }
            isClosed = true;
            try {
                await gen.return();
            } catch (e) {
                // Ignore errors on close - generator may already be done
            }
        },
        
        [Symbol.asyncIterator]() {
            return this;
        },
    };
}

__py.generators = {
    wrapGenerator,
    wrapAsyncGenerator,
    StopAsyncIteration,
};

// =============================================================================
// IMPORT SYSTEM (Phase 33.3)
// =============================================================================

/**
 * Copy all enumerable properties from a module object to the current scope.
 * 
 * WHAT: Implements Python's `from module import *` for built-in modules.
 * WHY: Built-in modules are objects in __py.* namespace, not ES6 modules.
 *       Star imports need to copy properties to the current scope.
 * HOW: Iterates over all enumerable properties and adds them to the target scope.
 * WHO: Used by emitter for star imports from built-in modules.
 * WHEN: When transpiling `from json import *` or similar.
 * WHERE: Runtime helper for import system.
 * 
 * Phase 33.3: Star imports from built-in modules.
 * 
 * @param {Object} moduleObj - The module object (e.g., __py.json)
 * @param {Object} scope - The scope object to add properties to (default: globalThis)
 */
function star_import(moduleObj, scope = null) {
    if (!moduleObj || typeof moduleObj !== 'object') {
        return;
    }
    
    // Determine target scope
    // In Node.js: use globalThis
    // In browser: use window (if available) or globalThis
    const targetScope = scope || (typeof globalThis !== 'undefined' ? globalThis : 
                                  typeof window !== 'undefined' ? window : 
                                  typeof global !== 'undefined' ? global : {});
    
    // Get all enumerable property names
    const keys = Object.keys(moduleObj);
    
    // Copy each property to the scope
    for (const key of keys) {
        // Skip private properties (starting with _) unless they're special
        // Python's import * typically skips names starting with _
        // But we allow __all__, __name__, __file__, etc.
        if (key.startsWith('_') && 
            key !== '__all__' && 
            key !== '__name__' && 
            key !== '__file__' && 
            key !== '__doc__' &&
            key !== '__version__') {
            continue;
        }
        
        // Skip if property already exists in scope (don't overwrite)
        if (key in targetScope && targetScope[key] !== undefined) {
            continue;
        }
        
        // Define property in scope
        try {
            // Try to use defineProperty for better control
            Object.defineProperty(targetScope, key, {
                value: moduleObj[key],
                writable: true,
                enumerable: true,
                configurable: true
            });
        } catch (e) {
            // If defineProperty fails (e.g., in strict mode), try direct assignment
            try {
                targetScope[key] = moduleObj[key];
            } catch (e2) {
                // Silently skip if we can't add to scope
                // This can happen in strict mode or with non-configurable properties
            }
        }
    }
}

/**
 * Copy properties from ES6 module namespace to current scope.
 * 
 * WHAT: Implements Python's `from module import *` for regular ES6 modules.
 * WHY: ES6 namespace imports create a namespace object, but Python star imports
 *      copy properties to the current scope.
 * HOW: Checks for __all__ in namespace, then copies properties accordingly.
 * WHO: Used by emitter for star imports from regular modules.
 * WHEN: When transpiling `from my_module import *`.
 * WHERE: Runtime helper for import system.
 * 
 * Phase 33.3: Star imports from regular modules.
 * 
 * @param {Object} namespace - The ES6 namespace object (from `import * as _module`)
 * @param {Object} scope - The scope object to add properties to (default: globalThis)
 * @param {Array<string>|null} __all__ - Optional __all__ list from module
 */
function star_import_esm(namespace, scope = null, __all__ = null) {
    if (!namespace || typeof namespace !== 'object') {
        return;
    }
    
    // Determine target scope
    const targetScope = scope || (typeof globalThis !== 'undefined' ? globalThis : 
                                  typeof window !== 'undefined' ? window : 
                                  typeof global !== 'undefined' ? global : {});
    
    // Get __all__ from namespace if not provided
    const allList = __all__ || namespace.__all__;
    
    let keys;
    if (allList && Array.isArray(allList)) {
        // Use __all__ if defined
        keys = allList;
    } else {
        // No __all__: copy all non-private enumerable properties
        keys = Object.keys(namespace);
    }
    
    // Copy each property to the scope
    for (const key of keys) {
        // Skip if not in namespace
        if (!(key in namespace)) {
            continue;
        }
        
        // Skip private properties (starting with _) unless in __all__
        // Python's import * skips names starting with _ unless explicitly in __all__
        if (!allList && key.startsWith('_') && 
            key !== '__all__' && 
            key !== '__name__' && 
            key !== '__file__' && 
            key !== '__doc__' &&
            key !== '__version__') {
            continue;
        }
        
        // Skip if property already exists in scope (don't overwrite)
        if (key in targetScope && targetScope[key] !== undefined) {
            continue;
        }
        
        // Define property in scope
        try {
            Object.defineProperty(targetScope, key, {
                value: namespace[key],
                writable: true,
                enumerable: true,
                configurable: true
            });
        } catch (e) {
            // Fallback to direct assignment
            try {
                targetScope[key] = namespace[key];
            } catch (e2) {
                // Silently skip if we can't add to scope
            }
        }
    }
}

__py.getitem = getitem;
__py.star_import_esm = star_import_esm;
__py.setitem = setitem;
__py.call = call;

// Make __py_classes available globally
global.__py_classes = { applyMixins, createProperty, checkAbstract };

// Make available globally for tests
global.__py = __py;

module.exports = __py;
