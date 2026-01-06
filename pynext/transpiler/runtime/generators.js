/**
 * PyNext Transpiler - Generator Protocol Runtime Helpers
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides JavaScript helpers for Python generator protocol compatibility.
 * Handles send(), throw(), close(), StopIteration, and async generator support.
 * 
 * Supports:
 * - Regular generators (def with yield) → wrapGenerator()
 * - Async generators (async def with yield) → wrapAsyncGenerator()
 * 
 * =============================================================================
 * WHY THIS EXISTS (Problem It Solves)
 * =============================================================================
 * 
 * Python generators support send(), throw(), and close() methods that
 * JavaScript generators don't have directly. This runtime provides:
 * 1. send() - Send value to generator
 * 2. throw() - Throw exception into generator
 * 3. close() - Close generator
 * 4. StopIteration handling (regular generators)
 * 5. StopAsyncIteration handling (async generators)
 * 
 * Async generators additionally return Promise<IteratorResult> instead of
 * IteratorResult, requiring separate wrapper implementation.
 * 
 * =============================================================================
 * SIZE BUDGET
 * =============================================================================
 * 
 * Target: < 800 bytes gzipped (includes both regular and async generators)
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * Regular generators:
 *   def gen():           →    function* gen() {
 *       yield 1              yield 1;
 *                           }
 *   
 *   g = gen()            →    const g = wrapGenerator(gen());
 *   g.send(2)            →    g.send(2);  // Via wrapper
 * 
 * Async generators:
 *   async def gen():     →    async function* gen() {
 *       yield 1              yield 1;
 *                           }
 *   
 *   g = gen()            →    const g = wrapAsyncGenerator(gen());
 *   await g.send(2)      →    await g.send(2);  // Returns Promise
 */

import {
    StopIteration,
    StopAsyncIteration,
} from './errors.js';

/**
 * Wrap a JavaScript generator to support Python generator protocol.
 * 
 * @param {Generator} gen - JavaScript generator
 * @returns {object} Wrapped generator with send(), throw(), close()
 */
export function wrapGenerator(gen) {
    let isClosed = false;
    let lastValue = undefined;
    
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

/**
 * StopIteration exception for generator protocol.
 */
export class StopIterationError extends Error {
    constructor(value = undefined) {
        super('StopIteration');
        this.name = 'StopIteration';
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
 * WHO: Called automatically by the transpiler when emitting async generator calls.
 *      Users don't call this directly - it's injected by emitter.py.
 * 
 * WHEN: During runtime, when an async generator function is called. The transpiler
 *       wraps the call: `gen()` → `wrapAsyncGenerator(gen())`.
 * 
 * WHERE: Part of the runtime helpers, loaded before transpiled code executes.
 * 
 * @param {AsyncGenerator} gen - JavaScript async generator (from async function*)
 * @returns {object} Wrapped async generator with send(), throw(), close()
 * 
 * @example
 * // Python:
 * async def gen():
 *     yield 1
 *     yield 2
 * 
 * g = gen()
 * value = await g.send(None)  # Returns 1
 * 
 * // JavaScript (transpiled):
 * async function* gen() {
 *     yield 1;
 *     yield 2;
 * }
 * 
 * const g = wrapAsyncGenerator(gen());
 * const value = await g.send(null);  // Returns Promise resolving to 1
 * 
 * Protocol Methods:
 * - next(value): Promise<IteratorResult> - Advance generator, return Promise
 * - send(value): Promise<any> - Send value, return Promise of yielded value
 * - throw(exception): Promise<IteratorResult> - Throw exception, return Promise
 * - close(): Promise<void> - Close generator, return Promise
 * 
 * Differences from wrapGenerator():
 * - All methods return Promises (async generators are async)
 * - Uses StopAsyncIteration instead of StopIteration
 * - next() returns Promise<IteratorResult> instead of IteratorResult
 * - send() returns Promise<any> instead of any
 * 
 * Edge Cases:
 * - Closed generators: Methods throw immediately if generator is closed
 * - StopAsyncIteration: Caught and handled properly (different from StopIteration)
 * - Error handling: Errors in generator propagate through Promise rejection
 * 
 * Related:
 * - wrapGenerator() - Regular generator wrapper (synchronous)
 * - errors.js: StopAsyncIteration - Exception for async generator completion
 * - async_support.py: _emit_async_function_def() - Emits async function*
 * - emitter.py: _emit_call() - Wraps async generator calls
 */
export function wrapAsyncGenerator(gen) {
    let isClosed = false;
    
    return {
        async next(value) {
            /**
             * Advance the async generator by one step.
             * 
             * WHAT: Calls the underlying async generator's next() method and
             *       returns a Promise that resolves to IteratorResult.
             * 
             * WHY: JavaScript async generators return Promise<IteratorResult>.
             *      This method preserves that behavior while adding closed state
             *      tracking.
             * 
             * HOW: 
             *     1. Check if generator is closed (return done immediately)
             *     2. Call gen.next(value) which returns a Promise
             *     3. Await the Promise to get IteratorResult
             *     4. Mark as closed if done
             *     5. Return the result
             * 
             * Args:
             *     value: Value to send to the generator (optional)
             * 
             * Returns:
             *     Promise<IteratorResult> - {done: boolean, value: any}
             */
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
            /**
             * Send a value to the async generator and get the yielded value.
             * 
             * WHAT: Sends a value to the generator and returns a Promise that
             *       resolves to the yielded value (not the IteratorResult).
             * 
             * WHY: Python's send() returns the yielded value directly, not the
             *      IteratorResult object. This method provides that behavior.
             * 
             * HOW:
             *     1. Call next(value) which returns Promise<IteratorResult>
             *     2. Await the Promise
             *     3. Extract and return the value (not the result object)
             * 
             * Args:
             *     value: Value to send to the generator
             * 
             * Returns:
             *     Promise<any> - The yielded value (resolves when generator yields)
             * 
             * @example
             * const g = wrapAsyncGenerator(gen());
             * const value = await g.send(42);  // Returns Promise resolving to yielded value
             */
            const result = await this.next(value);
            if (result.done) {
                // Generator is done - raise StopAsyncIteration
                throw new StopAsyncIteration(result.value);
            }
            return result.value;
        },
        
        async throw(exception) {
            /**
             * Throw an exception into the async generator.
             * 
             * WHAT: Throws an exception into the generator at the current yield
             *       point and returns a Promise<IteratorResult>.
             * 
             * WHY: Enables error handling and generator control flow from outside
             *      the generator function.
             * 
             * HOW:
             *     1. Check if generator is closed (throw immediately)
             *     2. Call gen.throw(exception) which returns a Promise
             *     3. Await the Promise to get IteratorResult
             *     4. Mark as closed if done
             *     5. Return the result
             * 
             * Args:
             *     exception: Exception to throw into the generator
             * 
             * Returns:
             *     Promise<IteratorResult> - Result after exception handling
             * 
             * @example
             * const g = wrapAsyncGenerator(gen());
             * try {
             *     await g.throw(new Error("Something went wrong"));
             * } catch (e) {
             *     // Exception was thrown into generator
             * }
             */
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
            /**
             * Close the async generator.
             * 
             * WHAT: Closes the generator, preventing further iteration. Returns
             *       a Promise that resolves when closing is complete.
             * 
             * WHY: Python generators support explicit closing. This provides that
             *      functionality for async generators.
             * 
             * HOW:
             *     1. Check if already closed (return immediately)
             *     2. Mark as closed
             *     3. Call gen.return() which returns a Promise
             *     4. Ignore errors during close (generator may already be done)
             * 
             * Returns:
             *     Promise<void> - Resolves when generator is closed
             * 
             * @example
             * const g = wrapAsyncGenerator(gen());
             * await g.close();  // Generator is now closed
             * await g.next();   // Returns {done: true, value: undefined}
             */
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
            /**
             * Make the wrapped generator an async iterable.
             * 
             * WHAT: Returns the generator itself, making it usable in for await loops.
             * 
             * WHY: Enables async generators to be used in async for loops:
             *      `async for item in gen(): ...`
             * 
             * HOW: Returns `this` so the wrapper can be iterated directly.
             * 
             * Returns:
             *     The wrapped generator (this)
             * 
             * @example
             * const g = wrapAsyncGenerator(gen());
             * for await (const item of g) {
             *     console.log(item);
             * }
             */
            return this;
        },
    };
}

// =============================================================================
// EXPORTS
// =============================================================================

export const generators = {
    wrapGenerator,
    wrapAsyncGenerator,
    StopIterationError,
};

