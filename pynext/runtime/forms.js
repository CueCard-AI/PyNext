/**
 * PyNext Form Runtime
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides reactive form state management with:
 * - Signal per field (fine-grained updates)
 * - Built-in validators
 * - Touched/dirty tracking
 * - Error management
 * 
 * Size target: ~1.5KB minified + gzipped
 * 
 * =============================================================================
 * WHY THIS EXISTS (vs React Forms)
 * =============================================================================
 * 
 * React form libraries have problems:
 * 
 * 1. useState per field: Re-renders entire form on every keystroke
 * 2. Formik: Heavy (~12KB), complex setup
 * 3. react-hook-form: Better, but still has re-render issues
 * 
 * PyNext forms:
 * - Use signals (O(1) updates, no re-renders)
 * - Simple API (no schemas, no setup)
 * - Validation is sync by default (instant feedback)
 * - ~1.5KB bundle size
 * 
 * =============================================================================
 * API OVERVIEW
 * =============================================================================
 * 
 * const form = createForm(
 *     { name: "", email: "" },           // initial values
 *     {                                   // validators (optional)
 *         name: [required()],
 *         email: [required(), email()],
 *     }
 * );
 * 
 * // Field access
 * form.name                   // Signal for name field
 * form.name()                 // Get value
 * form.name.set("Alice")      // Set value
 * 
 * // Errors
 * form.errors.name            // Error for name field (or "")
 * 
 * // State
 * form.isValid()              // True if all validators pass
 * form.isDirty()              // True if any field changed
 * form.isSubmitting()         // True during submission
 * 
 * // Actions
 * form.validate()             // Run all validators
 * form.reset()                // Reset to initial values
 * 
 * =============================================================================
 */

import { createSignal, createMemo, batch } from './reactive.js';


// =============================================================================
// VALIDATORS
// =============================================================================

/**
 * Value must not be empty.
 * 
 * @param {string} message - Error message
 * @returns {Function} Validator function
 * 
 * @example
 * const validate = required("Name is required");
 * validate("");  // "Name is required"
 * validate("a"); // null
 */
export function required(message = "This field is required") {
    return function(value) {
        if (value === null || value === undefined) return message;
        if (typeof value === 'string' && value.trim() === "") return message;
        if (Array.isArray(value) && value.length === 0) return message;
        return null;
    };
}


/**
 * Value must have at least N characters.
 * 
 * @param {number} length - Minimum length
 * @param {string} message - Error message (optional)
 * @returns {Function} Validator function
 */
export function minLength(length, message = null) {
    const msg = message || `Must be at least ${length} characters`;
    return function(value) {
        if (value === null || value === undefined) return msg;
        if (String(value).length < length) return msg;
        return null;
    };
}


/**
 * Value must have at most N characters.
 * 
 * @param {number} length - Maximum length
 * @param {string} message - Error message (optional)
 * @returns {Function} Validator function
 */
export function maxLength(length, message = null) {
    const msg = message || `Must be at most ${length} characters`;
    return function(value) {
        if (value === null || value === undefined) return null;
        if (String(value).length > length) return msg;
        return null;
    };
}


/**
 * Value must be a valid email.
 * 
 * @param {string} message - Error message
 * @returns {Function} Validator function
 */
export function email(message = "Must be a valid email address") {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return function(value) {
        if (!value) return null;  // email() doesn't require a value
        if (!emailRegex.test(value)) return message;
        return null;
    };
}


/**
 * Value must match a regex pattern.
 * 
 * @param {string|RegExp} regex - Pattern to match
 * @param {string} message - Error message
 * @returns {Function} Validator function
 */
export function pattern(regex, message = "Invalid format") {
    const re = typeof regex === 'string' ? new RegExp(regex) : regex;
    return function(value) {
        if (!value) return null;
        if (!re.test(value)) return message;
        return null;
    };
}


/**
 * Numeric value must be at least N.
 * 
 * @param {number} min - Minimum value
 * @param {string} message - Error message (optional)
 * @returns {Function} Validator function
 */
export function minValue(min, message = null) {
    const msg = message || `Must be at least ${min}`;
    return function(value) {
        if (value === null || value === undefined || value === "") return null;
        const num = parseFloat(value);
        if (isNaN(num) || num < min) return msg;
        return null;
    };
}


/**
 * Numeric value must be at most N.
 * 
 * @param {number} max - Maximum value
 * @param {string} message - Error message (optional)
 * @returns {Function} Validator function
 */
export function maxValue(max, message = null) {
    const msg = message || `Must be at most ${max}`;
    return function(value) {
        if (value === null || value === undefined || value === "") return null;
        const num = parseFloat(value);
        if (isNaN(num) || num > max) return msg;
        return null;
    };
}


/**
 * Value must be one of the allowed options.
 * 
 * @param {Array} options - Allowed values
 * @param {string} message - Error message (optional)
 * @returns {Function} Validator function
 */
export function oneOf(options, message = null) {
    const msg = message || `Must be one of: ${options.join(", ")}`;
    return function(value) {
        if (!value) return null;
        if (!options.includes(value)) return msg;
        return null;
    };
}


/**
 * Value must be a valid URL.
 * 
 * @param {string} message - Error message
 * @returns {Function} Validator function
 */
export function url(message = "Must be a valid URL") {
    const urlRegex = /^https?:\/\/(?:[\w-]+\.)+[\w-]+(?:\/[\w-./?%&=]*)?$/i;
    return function(value) {
        if (!value) return null;
        if (!urlRegex.test(value)) return message;
        return null;
    };
}


/**
 * Value must be an integer.
 * 
 * @param {string} message - Error message
 * @returns {Function} Validator function
 */
export function integer(message = "Must be a whole number") {
    return function(value) {
        if (value === null || value === undefined || value === "") return null;
        if (!Number.isInteger(Number(value))) return message;
        return null;
    };
}


/**
 * Value must be a number.
 * 
 * @param {string} message - Error message
 * @returns {Function} Validator function
 */
export function number(message = "Must be a number") {
    return function(value) {
        if (value === null || value === undefined || value === "") return null;
        if (isNaN(Number(value))) return message;
        return null;
    };
}


/**
 * Compose multiple validators into one.
 * 
 * @param {...Function} validators - Validators to compose
 * @returns {Function} Combined validator
 */
export function compose(...validators) {
    return function(value) {
        for (const validator of validators) {
            const error = validator(value);
            if (error) return error;
        }
        return null;
    };
}


/**
 * Run validators only when condition is true.
 * 
 * @param {Function} condition - Condition function
 * @param {...Function} validators - Validators to run
 * @returns {Function} Conditional validator
 */
export function when(condition, ...validators) {
    return function(value) {
        if (!condition()) return null;
        return compose(...validators)(value);
    };
}


// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Run a validator or list of validators on a value.
 * 
 * @param {Function|Array} validators - Validator(s) to run
 * @param {*} value - Value to validate
 * @returns {string|null} First error or null
 */
function runValidators(validators, value) {
    if (!validators) return null;
    
    if (typeof validators === 'function') {
        return validators(value);
    }
    
    for (const validator of validators) {
        const error = validator(value);
        if (error) return error;
    }
    return null;
}


// =============================================================================
// FORM STATE
// =============================================================================

/**
 * Create a reactive form.
 * 
 * @param {Object} initial - Initial field values
 * @param {Object} validators - Field validators (optional)
 * @returns {Object} Form state object
 * 
 * @example
 * const form = createForm(
 *     { email: "", password: "" },
 *     {
 *         email: [required(), email()],
 *         password: [required(), minLength(8)],
 *     }
 * );
 * 
 * form.email()           // Get value
 * form.email.set("a@b")  // Set value
 * form.errors.email      // Get error
 * form.validate()        // Validate all
 * form.reset()           // Reset
 */
export function createForm(initial, validators = {}) {
    // Store initial values for reset
    const initialCopy = { ...initial };
    
    // Create signals for each field
    const fields = {};
    const errors = {};
    const touched = {};
    
    for (const [name, value] of Object.entries(initial)) {
        fields[name] = createSignal(value);
        errors[name] = createSignal("");
        touched[name] = createSignal(false);
    }
    
    // Submitting state
    const isSubmitting = createSignal(false);
    
    // Computed: is form valid?
    const isValid = createMemo(() => {
        for (const [name, fieldValidators] of Object.entries(validators)) {
            if (!fields[name]) continue;
            const value = fields[name]();
            const error = runValidators(fieldValidators, value);
            if (error) return false;
        }
        return true;
    });
    
    // Computed: is form dirty?
    const isDirty = createMemo(() => {
        for (const [name, signal] of Object.entries(fields)) {
            if (signal() !== initialCopy[name]) return true;
        }
        return false;
    });
    
    /**
     * Run all validators and update error signals.
     * 
     * @param {boolean} touch - Whether to mark all fields as touched
     * @returns {boolean} True if valid
     */
    function validate(touch = true) {
        if (touch) {
            for (const t of Object.values(touched)) {
                t.set(true);
            }
        }
        
        let valid = true;
        
        for (const [name, fieldValidators] of Object.entries(validators)) {
            if (!fields[name]) continue;
            
            const value = fields[name]();
            const error = runValidators(fieldValidators, value);
            
            if (error) {
                errors[name].set(error);
                valid = false;
            } else {
                errors[name].set("");
            }
        }
        
        return valid;
    }
    
    /**
     * Validate a single field.
     * 
     * @param {string} name - Field name
     * @returns {boolean} True if valid
     */
    function validateField(name) {
        if (!validators[name]) {
            errors[name]?.set("");
            return true;
        }
        
        const value = fields[name]();
        const error = runValidators(validators[name], value);
        
        if (error) {
            errors[name].set(error);
            return false;
        } else {
            errors[name].set("");
            return true;
        }
    }
    
    /**
     * Reset form to initial values.
     */
    function reset() {
        batch(() => {
            for (const [name, value] of Object.entries(initialCopy)) {
                fields[name].set(value);
                errors[name].set("");
                touched[name].set(false);
            }
            isSubmitting.set(false);
        });
    }
    
    /**
     * Reset a single field.
     * 
     * @param {string} name - Field name
     */
    function resetField(name) {
        if (fields[name]) {
            fields[name].set(initialCopy[name]);
            errors[name].set("");
            touched[name].set(false);
        }
    }
    
    /**
     * Get all current values.
     * 
     * @returns {Object} Field values
     */
    function getValues() {
        const result = {};
        for (const [name, signal] of Object.entries(fields)) {
            result[name] = signal();
        }
        return result;
    }
    
    /**
     * Set multiple values at once.
     * 
     * @param {Object} values - Values to set
     */
    function setValues(values) {
        batch(() => {
            for (const [name, value] of Object.entries(values)) {
                if (fields[name]) {
                    fields[name].set(value);
                    touched[name].set(true);
                }
            }
        });
    }
    
    /**
     * Set error for a field.
     * 
     * @param {string} name - Field name
     * @param {string} message - Error message
     */
    function setError(name, message) {
        if (errors[name]) {
            errors[name].set(message);
        }
    }
    
    /**
     * Clear all errors.
     */
    function clearErrors() {
        for (const error of Object.values(errors)) {
            error.set("");
        }
    }
    
    /**
     * Mark all fields as touched.
     */
    function touchAll() {
        for (const t of Object.values(touched)) {
            t.set(true);
        }
    }
    
    // Build the form object with a Proxy for field access
    const form = {
        // Field access by name
        getField(name) {
            return fields[name];
        },
        
        // All values
        get values() {
            return getValues();
        },
        
        // Errors with proxy access
        errors: new Proxy({}, {
            get(_, name) {
                return errors[name]?.() ?? "";
            }
        }),
        
        // Touched with proxy access
        touched: new Proxy({}, {
            get(_, name) {
                return touched[name]?.() ?? false;
            }
        }),
        
        // State
        isValid,
        isDirty,
        isSubmitting,
        
        // Methods
        validate,
        validateField,
        reset,
        resetField,
        getValues,
        setValues,
        setError,
        clearErrors,
        touchAll,
    };
    
    // Use Proxy to allow form.fieldName access
    return new Proxy(form, {
        get(target, prop) {
            // First check if it's a form method or property
            if (prop in target) {
                return target[prop];
            }
            // Then check if it's a field
            if (fields[prop]) {
                return fields[prop];
            }
            return undefined;
        }
    });
}


// =============================================================================
// TWO-WAY BINDING HELPER
// =============================================================================

/**
 * Create two-way binding for an input element.
 * 
 * This is called by the hydration system to connect form fields
 * to DOM inputs.
 * 
 * @param {HTMLElement} element - Input element
 * @param {Object} signal - Signal to bind
 */
export function bindInput(element, signal) {
    // Set initial value
    if (element.type === 'checkbox') {
        element.checked = signal();
    } else {
        element.value = signal();
    }
    
    // Listen for changes
    const event = element.tagName === 'SELECT' ? 'change' : 'input';
    element.addEventListener(event, (e) => {
        if (element.type === 'checkbox') {
            signal.set(e.target.checked);
        } else {
            signal.set(e.target.value);
        }
    });
    
    // Update element when signal changes
    // This requires access to createEffect, which we import at the top
    // For now, we'll rely on the hydration system to handle reactive updates
}


// =============================================================================
// EXPORTS
// =============================================================================

export default {
    // Form creation
    createForm,
    bindInput,
    
    // Validators
    required,
    minLength,
    maxLength,
    email,
    pattern,
    minValue,
    maxValue,
    oneOf,
    url,
    integer,
    number,
    compose,
    when,
};

