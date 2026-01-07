/**
 * PyNext Runtime - collections Module
 * 
 * WHAT THIS FILE DOES:
 * Provides Python collections module functionality in JavaScript.
 * Implements Counter, defaultdict, deque, OrderedDict, and namedtuple.
 * 
 * WHY THIS EXISTS:
 * Python developers rely on these data structures. This module provides
 * Python-compatible collections for client-side code.
 * 
 * HOW IT WORKS:
 * - Counter: Map-based with most_common() optimization
 * - defaultdict: Proxy-based with factory function
 * - deque: Array-based with O(1) append/popleft
 * - OrderedDict: Map + linked list for order
 * - namedtuple: Class factory with property access
 * 
 * WHO USES THIS:
 * - Transpiled Python code using collections
 * - Client-side code needing Python collections
 * 
 * WHEN TO USE:
 * - Counting items: Counter
 * - Default values: defaultdict
 * - Queue/stack: deque
 * - Ordered mapping: OrderedDict
 * - Structured data: namedtuple
 * 
 * EXAMPLES:
 *     // In Python:
 *     from pynext.client.collections import Counter, defaultdict
 *     c = Counter(['a', 'b', 'a'])
 *     print(c['a'])  # 2
 */

/**
 * Counter - Count hashable objects.
 */
export class Counter extends Map {
    constructor(iterable = null) {
        super();
        if (iterable !== null && iterable !== undefined) {
            if (iterable instanceof Map || iterable instanceof Counter) {
                for (const [key, value] of iterable) {
                    this.set(key, value);
                }
            } else if (typeof iterable === 'object' && !Array.isArray(iterable)) {
                for (const [key, value] of Object.entries(iterable)) {
                    this.set(key, value);
                }
            } else {
                for (const item of iterable) {
                    this.set(item, (this.get(item) || 0) + 1);
                }
            }
        }
    }
    
    get(key) {
        return super.get(key) || 0;
    }
    
    set(key, value) {
        if (value < 0) {
            throw new ValueError('Counts cannot be negative');
        }
        if (value === 0) {
            super.delete(key);
        } else {
            super.set(key, value);
        }
    }
    
    update(iterable) {
        if (iterable instanceof Map || iterable instanceof Counter) {
            for (const [key, value] of iterable) {
                this.set(key, this.get(key) + value);
            }
        } else if (typeof iterable === 'object' && !Array.isArray(iterable)) {
            for (const [key, value] of Object.entries(iterable)) {
                this.set(key, this.get(key) + value);
            }
        } else {
            for (const item of iterable) {
                this.set(item, this.get(item) + 1);
            }
        }
    }
    
    subtract(iterable) {
        if (iterable instanceof Map || iterable instanceof Counter) {
            for (const [key, value] of iterable) {
                this.set(key, this.get(key) - value);
            }
        } else if (typeof iterable === 'object' && !Array.isArray(iterable)) {
            for (const [key, value] of Object.entries(iterable)) {
                this.set(key, this.get(key) - value);
            }
        } else {
            for (const item of iterable) {
                this.set(item, this.get(item) - 1);
            }
        }
    }
    
    most_common(n = null) {
        const entries = Array.from(this.entries());
        entries.sort((a, b) => b[1] - a[1]);
        if (n === null) {
            return entries;
        }
        return entries.slice(0, n);
    }
    
    elements() {
        // Generator-like: return items repeated according to count
        const result = [];
        for (const [item, count] of this) {
            for (let i = 0; i < count; i++) {
                result.push(item);
            }
        }
        return result;
    }
    
    total() {
        let sum = 0;
        for (const count of this.values()) {
            sum += count;
        }
        return sum;
    }
    
    _add(other) {
        const result = new Counter(this);
        if (other instanceof Counter) {
            for (const [key, value] of other) {
                result.set(key, result.get(key) + value);
            }
        }
        return result;
    }
    
    _sub(other) {
        const result = new Counter(this);
        if (other instanceof Counter) {
            for (const [key, value] of other) {
                result.set(key, result.get(key) - value);
            }
        }
        return result;
    }
    
    _and(other) {
        const result = new Counter();
        if (other instanceof Counter) {
            for (const [key, value] of this) {
                if (other.has(key)) {
                    result.set(key, Math.min(value, other.get(key)));
                }
            }
        }
        return result;
    }
    
    _or(other) {
        const result = new Counter(this);
        if (other instanceof Counter) {
            for (const [key, value] of other) {
                result.set(key, Math.max(result.get(key), value));
            }
        }
        return result;
    }
    
    toString() {
        return `Counter(${JSON.stringify(Object.fromEntries(this))})`;
    }
}

/**
 * defaultdict - Dict with default factory function.
 */
export class defaultdict extends Map {
    constructor(default_factory, ...args) {
        super(...args);
        if (typeof default_factory === 'function') {
            this._default_factory = default_factory;
        } else {
            // If not callable, treat as initial value
            const initial = default_factory;
            this._default_factory = () => initial;
        }
    }
    
    get(key) {
        if (!this.has(key)) {
            this.set(key, this._default_factory());
        }
        return super.get(key);
    }
    
    _getitem(key) {
        return this.get(key);
    }
    
    _setitem(key, value) {
        this.set(key, value);
    }
    
    copy() {
        return new defaultdict(this._default_factory, this);
    }
    
    toString() {
        return `defaultdict(${this._default_factory.name || 'factory'}, ${JSON.stringify(Object.fromEntries(this))})`;
    }
}

/**
 * deque - Double-ended queue.
 */
export class deque {
    constructor(iterable = null, maxlen = null) {
        this._items = [];
        this._maxlen = maxlen;
        if (iterable !== null && iterable !== undefined) {
            for (const item of iterable) {
                this.append(item);
            }
        }
    }
    
    append(x) {
        this._items.push(x);
        if (this._maxlen !== null && this._items.length > this._maxlen) {
            this._items.shift();
        }
    }
    
    appendleft(x) {
        this._items.unshift(x);
        if (this._maxlen !== null && this._items.length > this._maxlen) {
            this._items.pop();
        }
    }
    
    pop() {
        if (this._items.length === 0) {
            throw new IndexError('pop from an empty deque');
        }
        return this._items.pop();
    }
    
    popleft() {
        if (this._items.length === 0) {
            throw new IndexError('pop from an empty deque');
        }
        return this._items.shift();
    }
    
    extend(iterable) {
        for (const item of iterable) {
            this.append(item);
        }
    }
    
    extendleft(iterable) {
        for (const item of iterable) {
            this.appendleft(item);
        }
    }
    
    rotate(n = 1) {
        if (this._items.length === 0) {
            return;
        }
        n = n % this._items.length;
        if (n > 0) {
            const moved = this._items.splice(-n);
            this._items.unshift(...moved);
        } else if (n < 0) {
            const moved = this._items.splice(0, -n);
            this._items.push(...moved);
        }
    }
    
    clear() {
        this._items = [];
    }
    
    count(x) {
        return this._items.filter(item => item === x).length;
    }
    
    remove(value) {
        const index = this._items.indexOf(value);
        if (index === -1) {
            throw new ValueError('deque.remove(value): value not found');
        }
        this._items.splice(index, 1);
    }
    
    reverse() {
        this._items.reverse();
    }
    
    get maxlen() {
        return this._maxlen;
    }
    
    get length() {
        return this._items.length;
    }
    
    _getitem(index) {
        if (index < 0) {
            index = this._items.length + index;
        }
        if (index < 0 || index >= this._items.length) {
            throw new IndexError('deque index out of range');
        }
        return this._items[index];
    }
    
    _setitem(index, value) {
        if (index < 0) {
            index = this._items.length + index;
        }
        if (index < 0 || index >= this._items.length) {
            throw new IndexError('deque index out of range');
        }
        this._items[index] = value;
    }
    
    *[Symbol.iterator]() {
        for (const item of this._items) {
            yield item;
        }
    }
    
    toString() {
        return `deque(${JSON.stringify(this._items)}${this._maxlen !== null ? `, maxlen=${this._maxlen}` : ''})`;
    }
}

/**
 * OrderedDict - Dict that remembers insertion order.
 */
export class OrderedDict extends Map {
    constructor(iterable = null) {
        super();
        this._order = [];
        if (iterable !== null && iterable !== undefined) {
            if (iterable instanceof Map || iterable instanceof OrderedDict) {
                for (const [key, value] of iterable) {
                    this.set(key, value);
                }
            } else if (typeof iterable === 'object' && !Array.isArray(iterable)) {
                for (const [key, value] of Object.entries(iterable)) {
                    this.set(key, value);
                }
            } else {
                for (const [key, value] of iterable) {
                    this.set(key, value);
                }
            }
        }
    }
    
    set(key, value) {
        if (!this.has(key)) {
            this._order.push(key);
        }
        super.set(key, value);
        return this;
    }
    
    delete(key) {
        const deleted = super.delete(key);
        if (deleted) {
            const index = this._order.indexOf(key);
            if (index !== -1) {
                this._order.splice(index, 1);
            }
        }
        return deleted;
    }
    
    clear() {
        super.clear();
        this._order = [];
    }
    
    move_to_end(key, last = true) {
        if (!this.has(key)) {
            throw new KeyError(key);
        }
        const index = this._order.indexOf(key);
        this._order.splice(index, 1);
        if (last) {
            this._order.push(key);
        } else {
            this._order.unshift(key);
        }
    }
    
    popitem(last = true) {
        if (this._order.length === 0) {
            throw new KeyError('dictionary is empty');
        }
        const key = last ? this._order[this._order.length - 1] : this._order[0];
        const value = this.get(key);
        this.delete(key);
        return [key, value];
    }
    
    *keys() {
        for (const key of this._order) {
            yield key;
        }
    }
    
    *values() {
        for (const key of this._order) {
            yield this.get(key);
        }
    }
    
    *entries() {
        for (const key of this._order) {
            yield [key, this.get(key)];
        }
    }
    
    *[Symbol.iterator]() {
        yield* this.keys();
    }
    
    toString() {
        const items = Array.from(this.entries()).map(([k, v]) => `${k}: ${v}`);
        return `OrderedDict({${items.join(', ')}})`;
    }
}

/**
 * namedtuple - Factory function for creating tuple subclasses with named fields.
 */
export function namedtuple(typename, field_names, rename = false, defaults = null, module = null) {
    // Parse field_names
    let fields;
    if (typeof field_names === 'string') {
        fields = field_names.split(/[\s,]+/).filter(f => f);
    } else {
        fields = Array.from(field_names);
    }
    
    // Check for invalid field names
    const invalid = fields.filter(f => !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(f) || ['class', 'def', 'import'].includes(f));
    if (invalid.length > 0 && !rename) {
        throw new ValueError(`Invalid field names: ${invalid.join(', ')}`);
    }
    
    // Rename invalid fields
    if (rename) {
        const used = new Set();
        fields = fields.map((f, i) => {
            if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(f) || ['class', 'def', 'import'].includes(f) || used.has(f)) {
                let newName = `_${i}`;
                while (used.has(newName)) {
                    i++;
                    newName = `_${i}`;
                }
                used.add(newName);
                return newName;
            }
            used.add(f);
            return f;
        });
    }
    
    // Create class
    class NamedTuple {
        constructor(...args) {
            if (args.length === 1 && (args[0] instanceof Array || (typeof args[0] === 'object' && args[0] !== null))) {
                // Single iterable argument
                const iterable = args[0];
                if (iterable instanceof Array) {
                    if (iterable.length !== fields.length) {
                        throw new TypeError(`Expected ${fields.length} arguments, got ${iterable.length}`);
                    }
                    for (let i = 0; i < fields.length; i++) {
                        this[fields[i]] = iterable[i];
                    }
                } else {
                    // Object
                    for (const field of fields) {
                        if (!(field in iterable)) {
                            throw new TypeError(`Missing required field: ${field}`);
                        }
                        this[field] = iterable[field];
                    }
                }
            } else {
                // Positional arguments
                if (args.length !== fields.length) {
                    throw new TypeError(`Expected ${fields.length} arguments, got ${args.length}`);
                }
                for (let i = 0; i < fields.length; i++) {
                    this[fields[i]] = args[i];
                }
            }
        }
        
        _asdict() {
            const result = {};
            for (const field of fields) {
                result[field] = this[field];
            }
            return result;
        }
        
        _replace(**kwargs) {
            const values = fields.map(f => kwargs.hasOwnProperty(f) ? kwargs[f] : this[f]);
            return new NamedTuple(...values);
        }
        
        _fields() {
            return fields.slice();
        }
        
        _make(iterable) {
            return new NamedTuple(iterable);
        }
        
        toString() {
            const items = fields.map(f => `${f}=${this[f]}`);
            return `${typename}(${items.join(', ')})`;
        }
    }
    
    NamedTuple._fields = fields;
    NamedTuple.__name__ = typename;
    
    return NamedTuple;
}

// Error classes
class ValueError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValueError';
    }
}

class TypeError extends Error {
    constructor(message) {
        super(message);
        this.name = 'TypeError';
    }
}

class IndexError extends Error {
    constructor(message) {
        super(message);
        this.name = 'IndexError';
    }
}

class KeyError extends Error {
    constructor(key) {
        super(`'${key}'`);
        this.name = 'KeyError';
        this.key = key;
    }
}

// Default exports
export default {
    Counter,
    defaultdict,
    deque,
    OrderedDict,
    namedtuple,
};

