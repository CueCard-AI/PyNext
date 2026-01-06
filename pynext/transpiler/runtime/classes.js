/**
 * PyNext Class Runtime Helpers - Phase 33.1
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides runtime helpers for Python class features that don't have direct
 * JavaScript equivalents:
 * - Multiple inheritance (mixin pattern)
 * - Property descriptors
 * - Abstract base class validation
 * 
 * =============================================================================
 * WHY THIS EXISTS (Problem It Solves)
 * =============================================================================
 * 
 * JavaScript only supports single inheritance. Python supports multiple
 * inheritance. We use a mixin pattern to copy methods from additional base
 * classes to the derived class prototype.
 * 
 * =============================================================================
 * HOW IT WORKS (Architecture)
 * =============================================================================
 * 
 * Multiple Inheritance:
 *   class C(A, B): pass
 *   → class C extends A { constructor() { super(); applyMixins(C, [B]); } }
 * 
 * Property Descriptors:
 *   @property with @setter and @deleter
 *   → Uses Object.defineProperty with get/set/delete descriptors
 * 
 * =============================================================================
 * WHO USES THIS
 * =============================================================================
 * 
 * - Transpiled class code (emitted by pynext/transpiler/emitter.py)
 * - Runtime when classes are instantiated
 * 
 * =============================================================================
 * EXAMPLES
 * =============================================================================
 * 
 * ```javascript
 * // Multiple inheritance
 * class A { methodA() { return "A"; } }
 * class B { methodB() { return "B"; } }
 * class C extends A {
 *     constructor() {
 *         super();
 *         applyMixins(C, [B]);
 *     }
 * }
 * const c = new C();
 * c.methodA(); // "A"
 * c.methodB(); // "B"
 * 
 * // Property with deleter
 * class Foo {
 *     get value() { return this._value; }
 *     set value(v) { this._value = v; }
 *     delete value() { delete this._value; }
 * }
 * ```
 */

/**
 * Apply mixins to a class for multiple inheritance support.
 * 
 * Copies all methods (except constructor) from mixin prototypes to the
 * target class prototype.
 * 
 * @param {Function} targetClass - The class to apply mixins to
 * @param {Array<Function>} mixins - Array of mixin classes
 * 
 * @example
 * class A { methodA() { } }
 * class B { methodB() { } }
 * class C extends A {
 *     constructor() {
 *         super();
 *         applyMixins(C, [B]);
 *     }
 * }
 */
export function applyMixins(targetClass, mixins) {
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

/**
 * Create a property descriptor with getter, setter, and deleter.
 * 
 * Phase 33.1: Support for @property with @setter and @deleter.
 * 
 * @param {Object} options - Property descriptor options
 * @param {Function} options.get - Getter function
 * @param {Function} options.set - Setter function
 * @param {Function} options.delete - Deleter function
 * @returns {Object} Property descriptor
 * 
 * @example
 * Object.defineProperty(obj, 'value', createProperty({
 *     get: () => this._value,
 *     set: (v) => { this._value = v; },
 *     delete: () => { delete this._value; }
 * }));
 */
export function createProperty({ get, set, delete: deleter }) {
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

/**
 * Check if an abstract class is being instantiated directly.
 * 
 * Phase 33.1: Abstract base class validation.
 * 
 * @param {Function} abstractClass - The abstract class
 * @param {Function} instanceClass - The class being instantiated
 * @throws {Error} If abstract class is instantiated directly
 * 
 * @example
 * class AbstractBase {
 *     constructor() {
 *         checkAbstract(AbstractBase, new.target);
 *     }
 * }
 */
export function checkAbstract(abstractClass, instanceClass) {
    if (instanceClass === abstractClass) {
        throw new Error(`TypeError: Cannot instantiate abstract class ${abstractClass.name}`);
    }
}

