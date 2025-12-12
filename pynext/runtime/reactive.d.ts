/**
 * PyNext Unified Reactive Runtime - TypeScript Definitions
 * 
 * This file provides TypeScript type definitions for the PyNext reactive
 * runtime. These definitions mirror the Python API exactly.
 * 
 * @module pynext/runtime/reactive
 */

// =============================================================================
// Signal Types
// =============================================================================

/**
 * Options for creating a signal.
 */
export interface SignalOptions<T> {
    /**
     * Custom equality function. If provided, the signal only notifies
     * subscribers when equals(oldValue, newValue) returns false.
     * 
     * @default (a, b) => a === b
     */
    equals?: (a: T, b: T) => boolean;
}

/**
 * A reactive signal - a container for a value that notifies subscribers
 * when the value changes.
 * 
 * @template T The type of the value
 * 
 * @example
 * const count: Signal<number> = createSignal(0);
 * count();           // Read: returns 0
 * count.set(5);      // Write: sets to 5
 * count.update(x => x + 1);  // Increment
 */
export interface Signal<T> {
    /**
     * Read the current value. If called inside an effect or memo,
     * creates a subscription that will re-run when this signal changes.
     */
    (): T;
    
    /**
     * Set a new value and notify subscribers.
     * Subscribers are only notified if the new value differs from
     * the current value (according to the equals function).
     */
    set(value: T): void;
    
    /**
     * Update the value using a function.
     * This is safer than set(signal() + 1) in async contexts.
     */
    update(fn: (prev: T) => T): void;
    
    /**
     * Read the current value WITHOUT subscribing.
     * Use when you need the value but don't want the enclosing
     * effect/memo to re-run when this signal changes.
     */
    peek(): T;
}

/**
 * Create a reactive signal.
 * 
 * @template T The type of the value
 * @param initialValue The initial value
 * @param options Signal options
 * @returns A signal object
 * 
 * @example
 * const count = createSignal(0);
 * const name = createSignal<string | null>(null);
 * const items = createSignal<Item[]>([]);
 */
export function createSignal<T>(initialValue: T, options?: SignalOptions<T>): Signal<T>;

// =============================================================================
// Effect Types
// =============================================================================

/**
 * A cleanup function returned by an effect.
 * Called before the effect re-runs or when disposed.
 */
export type CleanupFunction = () => void;

/**
 * An effect function that may return a cleanup function.
 */
export type EffectFunction = () => void | CleanupFunction;

/**
 * A dispose function to stop an effect from running.
 */
export type DisposeFunction = () => void;

/**
 * Create a reactive effect that re-runs when dependencies change.
 * 
 * Dependencies are automatically tracked - any signal read inside
 * the effect body becomes a dependency.
 * 
 * @param fn The effect function. Can return a cleanup function.
 * @returns A dispose function to stop the effect.
 * 
 * @example
 * // Basic effect
 * const dispose = createEffect(() => {
 *     console.log(`Count: ${count()}`);
 * });
 * 
 * // Effect with cleanup
 * createEffect(() => {
 *     const timer = setInterval(tick, 1000);
 *     return () => clearInterval(timer);
 * });
 */
export function createEffect(fn: EffectFunction): DisposeFunction;

// =============================================================================
// Memo Types
// =============================================================================

/**
 * A memoized computation that caches its result.
 * 
 * @template T The type of the computed value
 */
export interface Memo<T> {
    /**
     * Read the memoized value. Recomputes only if dependencies changed.
     */
    (): T;
    
    /**
     * Read the value without subscribing.
     */
    peek(): T;
}

/**
 * Create a memoized computation that caches its result.
 * 
 * The computation is lazy - it only runs when the value is read.
 * It caches the result and only recomputes when dependencies change.
 * 
 * @template T The type of the computed value
 * @param fn The computation function
 * @param options Memo options
 * @returns A memo accessor function
 * 
 * @example
 * const doubled = createMemo(() => count() * 2);
 * console.log(doubled());  // Computes and caches
 * console.log(doubled());  // Returns cached value
 */
export function createMemo<T>(fn: () => T, options?: SignalOptions<T>): Memo<T>;

// =============================================================================
// Store Types
// =============================================================================

/**
 * A deep reactive store. Any property access or mutation at any
 * nesting level is tracked and triggers updates.
 * 
 * @template T The type of the store object
 */
export type Store<T> = T;

/**
 * Create a deeply reactive store from an object.
 * 
 * @template T The type of the object (must be an object type)
 * @param initialValue The initial object or array
 * @returns A reactive proxy of the object
 * 
 * @example
 * const store = createStore({
 *     count: 0,
 *     items: [] as Item[],
 *     user: { name: 'Alice', age: 30 }
 * });
 * 
 * store.count = 5;  // Triggers reactivity
 * store.items.push({ id: 1 });  // Also triggers
 * store.user.name = 'Bob';  // Deep reactivity
 */
export function createStore<T extends object>(initialValue: T): Store<T>;

// =============================================================================
// Batching and Untracking
// =============================================================================

/**
 * Batch multiple updates into a single notification cycle.
 * 
 * Effects only run once after all updates in the batch complete.
 * This prevents intermediate states and improves performance.
 * 
 * @param fn The function containing updates
 * 
 * @example
 * batch(() => {
 *     firstName.set('John');
 *     lastName.set('Doe');
 * });
 * // Effects run once, not twice
 */
export function batch(fn: () => void): void;

/**
 * Execute a function without tracking dependencies.
 * 
 * Signals read inside the function will not cause the enclosing
 * effect/memo to re-run when they change.
 * 
 * @template T The return type
 * @param fn The function to execute
 * @returns The return value of fn
 * 
 * @example
 * createEffect(() => {
 *     const tracked = count();  // Tracked
 *     const untracked = untrack(() => other());  // NOT tracked
 * });
 */
export function untrack<T>(fn: () => T): T;

// =============================================================================
// Control Flow Components
// =============================================================================

/**
 * Props for the Show component.
 */
export interface ShowProps<T> {
    /**
     * Accessor returning a truthy/falsy value.
     */
    when: () => T;
    
    /**
     * Render function for when condition is truthy.
     */
    children: () => Node | Node[] | string | null;
    
    /**
     * Render function for when condition is falsy.
     */
    fallback?: () => Node | Node[] | string | null;
    
    /**
     * Parent element to render into.
     */
    parent: Element;
}

/**
 * Conditional rendering component.
 * 
 * @example
 * Show({
 *     when: () => count() > 0,
 *     children: () => document.createTextNode('Positive'),
 *     fallback: () => document.createTextNode('Zero or negative'),
 *     parent: container
 * });
 */
export function Show<T>(props: ShowProps<T>): { dispose: DisposeFunction };

/**
 * Props for the For component.
 */
export interface ForProps<T> {
    /**
     * Accessor returning an array of items.
     */
    each: () => T[];
    
    /**
     * Function to get unique key from item.
     */
    key?: (item: T) => string | number;
    
    /**
     * Render function for each item.
     * @param item The current item
     * @param index Accessor returning current index
     */
    children: (item: T, index: () => number) => Node | Node[] | string | null;
    
    /**
     * Render function for empty list.
     */
    fallback?: () => Node | Node[] | string | null;
    
    /**
     * Parent element to render into.
     */
    parent: Element;
}

/**
 * Keyed list rendering with efficient reconciliation.
 * 
 * @example
 * For({
 *     each: () => items,
 *     key: item => item.id,
 *     children: (item) => {
 *         const li = document.createElement('li');
 *         li.textContent = item.name;
 *         return li;
 *     },
 *     parent: container
 * });
 */
export function For<T>(props: ForProps<T>): { dispose: DisposeFunction };

/**
 * Props for the Index component.
 */
export interface IndexProps<T> {
    /**
     * Accessor returning an array of items.
     */
    each: () => T[];
    
    /**
     * Render function for each item.
     */
    children: (item: T, index: () => number) => Node | Node[] | string | null;
    
    /**
     * Render function for empty list.
     */
    fallback?: () => Node | Node[] | string | null;
    
    /**
     * Parent element to render into.
     */
    parent: Element;
}

/**
 * Index-based list rendering.
 */
export function Index<T>(props: IndexProps<T>): { dispose: DisposeFunction };

/**
 * Props for a Match branch in Switch.
 */
export interface MatchProps {
    /**
     * Condition accessor or boolean.
     */
    when: (() => boolean) | boolean;
    
    /**
     * Render function for this branch.
     */
    children: () => Node | Node[] | string | null;
}

/**
 * Create a Match branch for Switch.
 */
export function Match(props: MatchProps): MatchProps;

/**
 * Props for the Switch component.
 */
export interface SwitchProps {
    /**
     * Array of Match branches.
     */
    children: MatchProps[];
    
    /**
     * Parent element to render into.
     */
    parent: Element;
}

/**
 * Multi-branch conditional rendering.
 * First matching condition wins.
 * 
 * @example
 * Switch({
 *     children: [
 *         Match({ when: () => status() === 'loading', children: () => Spinner() }),
 *         Match({ when: () => status() === 'error', children: () => Error() }),
 *         Match({ when: true, children: () => Content() })
 *     ],
 *     parent: container
 * });
 */
export function Switch(props: SwitchProps): { dispose: DisposeFunction };

/**
 * Props for the Portal component.
 */
export interface PortalProps {
    /**
     * Target selector or element.
     */
    mount: string | Element;
    
    /**
     * Content render function.
     */
    children: () => Node | Node[] | string | null;
}

/**
 * Render content into a different DOM location.
 * 
 * @example
 * Portal({
 *     mount: 'body',
 *     children: () => modalContent
 * });
 */
export function Portal(props: PortalProps): { dispose: DisposeFunction };

/**
 * Props for the ErrorBoundary component.
 */
export interface ErrorBoundaryProps {
    /**
     * Render function for error state.
     */
    fallback: (error: Error) => Node | Node[] | string | null;
    
    /**
     * Content render function.
     */
    children: () => Node | Node[] | string | null;
    
    /**
     * Parent element to render into.
     */
    parent: Element;
}

/**
 * Catch errors in children and render fallback.
 * 
 * @example
 * ErrorBoundary({
 *     fallback: (error) => document.createTextNode(`Error: ${error.message}`),
 *     children: () => riskyContent,
 *     parent: container
 * });
 */
export function ErrorBoundary(props: ErrorBoundaryProps): { dispose: DisposeFunction };

// =============================================================================
// Hydration
// =============================================================================

/**
 * Hydrate the entire page with server-rendered state.
 * 
 * Parses state from <script id="__PYNEXT_DATA__"> and connects
 * signals to DOM elements with data-pynext-* attributes.
 * 
 * @param root Root element (default: document.body)
 * 
 * @example
 * // After page load
 * hydrate();
 * 
 * // Or with specific root
 * hydrate(document.getElementById('app'));
 */
export function hydrate(root?: Element): void;

/**
 * Hydrate a single island component.
 * 
 * @param selector CSS selector or element
 * 
 * @example
 * hydrateIsland('[data-pynext-component="Counter"]');
 */
export function hydrateIsland(selector: string | Element): void;

// =============================================================================
// Global PyNext Object
// =============================================================================

declare global {
    interface Window {
        PyNext: {
            createSignal: typeof createSignal;
            createEffect: typeof createEffect;
            createMemo: typeof createMemo;
            createStore: typeof createStore;
            batch: typeof batch;
            untrack: typeof untrack;
            Show: typeof Show;
            For: typeof For;
            Index: typeof Index;
            Switch: typeof Switch;
            Match: typeof Match;
            Portal: typeof Portal;
            ErrorBoundary: typeof ErrorBoundary;
            hydrate: typeof hydrate;
            hydrateIsland: typeof hydrateIsland;
        };
    }
}

