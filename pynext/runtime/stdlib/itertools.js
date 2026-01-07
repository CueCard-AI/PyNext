/**
 * PyNext Runtime - itertools Module
 * 
 * WHAT THIS FILE DOES:
 * Provides Python itertools module functionality in JavaScript.
 * Implements all itertools functions: chain, cycle, repeat, count, islice,
 * takewhile, dropwhile, filterfalse, groupby, accumulate, product, permutations,
 * combinations, combinations_with_replacement, zip_longest, starmap, tee, pairwise.
 * 
 * WHY THIS EXISTS:
 * itertools provides powerful iterator tools. This module makes them
 * available in client-side JavaScript code.
 * 
 * HOW IT WORKS:
 * - Generator-based for memory efficiency
 * - Optimized for common patterns
 * - Supports infinite iterators
 * 
 * EXAMPLES:
 *     // In Python:
 *     from pynext.client.itertools import chain, cycle, groupby
 *     result = list(chain([1, 2], [3, 4]))
 */

/**
 * chain - Chain iterables together.
 */
export function* chain(...iterables) {
    for (const iterable of iterables) {
        yield* iterable;
    }
}

/**
 * chain.from_iterable - Chain from iterable of iterables.
 */
chain.from_iterable = function*(iterable) {
    for (const it of iterable) {
        yield* it;
    }
};

/**
 * cycle - Cycle through iterable infinitely.
 */
export function* cycle(iterable) {
    const saved = [];
    for (const element of iterable) {
        yield element;
        saved.push(element);
    }
    if (saved.length === 0) {
        return;
    }
    while (true) {
        yield* saved;
    }
}

/**
 * repeat - Repeat value n times or infinitely.
 */
export function* repeat(value, times = null) {
    if (times === null) {
        while (true) {
            yield value;
        }
    } else {
        for (let i = 0; i < times; i++) {
            yield value;
        }
    }
}

/**
 * count - Count from start with step.
 */
export function* count(start = 0, step = 1) {
    let n = start;
    while (true) {
        yield n;
        n += step;
    }
}

/**
 * islice - Slice an iterable.
 */
export function* islice(iterable, start, stop = null, step = 1) {
    if (stop === null) {
        stop = start;
        start = 0;
    }
    
    let index = 0;
    for (const item of iterable) {
        if (index >= stop) {
            break;
        }
        if (index >= start && (index - start) % step === 0) {
            yield item;
        }
        index++;
    }
}

/**
 * takewhile - Take elements while predicate is true.
 */
export function* takewhile(predicate, iterable) {
    for (const item of iterable) {
        if (!predicate(item)) {
            break;
        }
        yield item;
    }
}

/**
 * dropwhile - Drop elements while predicate is true.
 */
export function* dropwhile(predicate, iterable) {
    let dropping = true;
    for (const item of iterable) {
        if (dropping && predicate(item)) {
            continue;
        }
        dropping = false;
        yield item;
    }
}

/**
 * filterfalse - Filter elements where predicate is false.
 */
export function* filterfalse(predicate, iterable) {
    if (predicate === null || predicate === undefined) {
        predicate = (x) => !x;
    }
    for (const item of iterable) {
        if (!predicate(item)) {
            yield item;
        }
    }
}

/**
 * groupby - Group consecutive elements by key function.
 */
export function* groupby(iterable, key = null) {
    if (key === null) {
        key = (x) => x;
    }
    
    let currentKey = null;
    let currentGroup = [];
    
    for (const item of iterable) {
        const itemKey = key(item);
        
        if (currentKey === null) {
            currentKey = itemKey;
            currentGroup = [item];
        } else if (itemKey === currentKey) {
            currentGroup.push(item);
        } else {
            yield [currentKey, currentGroup];
            currentKey = itemKey;
            currentGroup = [item];
        }
    }
    
    if (currentKey !== null) {
        yield [currentKey, currentGroup];
    }
}

/**
 * accumulate - Accumulate values with binary function.
 */
export function* accumulate(iterable, func = null) {
    if (func === null) {
        func = (a, b) => a + b;
    }
    
    let total = null;
    for (const item of iterable) {
        if (total === null) {
            total = item;
        } else {
            total = func(total, item);
        }
        yield total;
    }
}

/**
 * product - Cartesian product of iterables.
 */
export function* product(...iterables) {
    if (iterables.length === 0) {
        yield [];
        return;
    }
    
    // Handle repeat parameter
    let repeat = 1;
    if (iterables.length > 0 && typeof iterables[iterables.length - 1] === 'object' && iterables[iterables.length - 1].repeat) {
        repeat = iterables.pop().repeat;
    }
    
    if (iterables.length === 0) {
        yield [];
        return;
    }
    
    const pools = [];
    for (let i = 0; i < repeat; i++) {
        for (const pool of iterables) {
            pools.push(Array.from(pool));
        }
    }
    
    function* _product(pools, result = []) {
        if (pools.length === 0) {
            yield result;
            return;
        }
        
        for (const item of pools[0]) {
            yield* _product(pools.slice(1), [...result, item]);
        }
    }
    
    yield* _product(pools);
}

/**
 * permutations - Permutations of iterable.
 */
export function* permutations(iterable, r = null) {
    const pool = Array.from(iterable);
    const n = pool.length;
    r = r === null ? n : r;
    
    if (r > n) {
        return;
    }
    
    function* _permutations(pool, r, prefix = []) {
        if (r === 0) {
            yield prefix;
            return;
        }
        
        for (let i = 0; i < pool.length; i++) {
            const newPrefix = [...prefix, pool[i]];
            const newPool = pool.filter((_, j) => j !== i);
            yield* _permutations(newPool, r - 1, newPrefix);
        }
    }
    
    yield* _permutations(pool, r);
}

/**
 * combinations - Combinations of iterable.
 */
export function* combinations(iterable, r) {
    const pool = Array.from(iterable);
    const n = pool.length;
    
    if (r > n) {
        return;
    }
    
    function* _combinations(pool, r, start = 0, prefix = []) {
        if (r === 0) {
            yield prefix;
            return;
        }
        
        for (let i = start; i <= pool.length - r; i++) {
            yield* _combinations(pool, r - 1, i + 1, [...prefix, pool[i]]);
        }
    }
    
    yield* _combinations(pool, r);
}

/**
 * combinations_with_replacement - Combinations with replacement.
 */
export function* combinations_with_replacement(iterable, r) {
    const pool = Array.from(iterable);
    const n = pool.length;
    
    if (n === 0 && r > 0) {
        return;
    }
    
    function* _combinations_with_replacement(pool, r, start = 0, prefix = []) {
        if (r === 0) {
            yield prefix;
            return;
        }
        
        for (let i = start; i < pool.length; i++) {
            yield* _combinations_with_replacement(pool, r - 1, i, [...prefix, pool[i]]);
        }
    }
    
    yield* _combinations_with_replacement(pool, r);
}

/**
 * zip_longest - Zip longest iterable, fill with fillvalue.
 */
export function* zip_longest(...iterables) {
    const fillvalue = arguments[arguments.length - 1];
    const hasFillvalue = typeof fillvalue === 'object' && fillvalue !== null && 'fillvalue' in fillvalue;
    const actualFillvalue = hasFillvalue ? fillvalue.fillvalue : null;
    const actualIterables = hasFillvalue ? Array.from(arguments).slice(0, -1) : Array.from(arguments);
    
    if (actualIterables.length === 0) {
        return;
    }
    
    const iterators = actualIterables.map(it => it[Symbol.iterator]());
    const active = new Set(iterators.map((_, i) => i));
    
    while (active.size > 0) {
        const values = [];
        for (let i = 0; i < iterators.length; i++) {
            if (!active.has(i)) {
                values.push(actualFillvalue);
            } else {
                const result = iterators[i].next();
                if (result.done) {
                    active.delete(i);
                    values.push(actualFillvalue);
                } else {
                    values.push(result.value);
                }
            }
        }
        yield values;
    }
}

/**
 * starmap - Map function with unpacked arguments.
 */
export function* starmap(function_, iterable) {
    for (const args of iterable) {
        yield function_(...args);
    }
}

/**
 * tee - Split iterator into n independent iterators.
 */
export function tee(iterable, n = 2) {
    const values = Array.from(iterable);
    const iterators = [];
    
    for (let i = 0; i < n; i++) {
        let index = 0;
        iterators.push({
            next() {
                if (index >= values.length) {
                    return { done: true, value: undefined };
                }
                return { done: false, value: values[index++] };
            },
            [Symbol.iterator]() {
                return this;
            }
        });
    }
    
    return iterators;
}

/**
 * pairwise - Pair adjacent elements.
 */
export function* pairwise(iterable) {
    const iterator = iterable[Symbol.iterator]();
    let prev = iterator.next();
    if (prev.done) {
        return;
    }
    
    let curr = iterator.next();
    while (!curr.done) {
        yield [prev.value, curr.value];
        prev = curr;
        curr = iterator.next();
    }
}

// Default export
export default {
    chain,
    cycle,
    repeat,
    count,
    islice,
    takewhile,
    dropwhile,
    filterfalse,
    groupby,
    accumulate,
    product,
    permutations,
    combinations,
    combinations_with_replacement,
    zip_longest,
    starmap,
    tee,
    pairwise,
};

