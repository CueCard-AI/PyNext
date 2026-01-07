/**
 * PyNext Runtime - Type Checking
 * 
 * WHAT THIS FILE DOES:
 * Provides runtime type validation for transpiled JavaScript code.
 * Used by @typed decorator to validate function arguments and return values.
 * 
 * WHY THIS EXISTS:
 * Runtime type checking catches type errors that compile-time checking might miss,
 * especially when dealing with dynamic data from external sources.
 * 
 * HOW IT WORKS:
 * - validate() function checks if a value matches an expected type
 * - Supports JavaScript primitives and object types
 * - Validates arrays, objects, and nested structures
 * - Used by transpiled @typed decorator
 * 
 * WHO USES THIS:
 * - Transpiled @typed decorator
 * - Runtime validation in development mode
 * 
 * WHEN TO USE:
 * - In development mode for @typed functions
 * - When you need runtime type safety
 * 
 * EXAMPLES:
 *     // In transpiled code:
 *     import { validate } from 'pynext/runtime/type_check.js';
 *     
 *     function greet(name, times = 1) {
 *         validate(name, 'string');
 *         validate(times, 'number');
 *         // ... function body
 *     }
 */

/**
 * Validate that a value matches an expected type.
 * 
 * @param {any} value - Value to validate
 * @param {string|Function|Object} expectedType - Expected type
 * @param {string} paramName - Parameter name (for error messages)
 * @throws {TypeError} If value doesn't match expected type
 */
export function validate(value, expectedType, paramName = 'value') {
    if (expectedType === undefined || expectedType === null) {
        return; // No type specified, skip validation
    }
    
    // Handle type names as strings
    if (typeof expectedType === 'string') {
        validateByTypeName(value, expectedType, paramName);
        return;
    }
    
    // Handle constructor functions
    if (typeof expectedType === 'function') {
        if (!(value instanceof expectedType)) {
            throw new TypeError(
                `${paramName} must be instance of ${expectedType.name}, got ${typeof value}`
            );
        }
        return;
    }
    
    // Handle type objects (for complex types)
    if (typeof expectedType === 'object') {
        validateComplexType(value, expectedType, paramName);
        return;
    }
}

/**
 * Validate by type name string.
 */
function validateByTypeName(value, typeName, paramName) {
    switch (typeName) {
        case 'str':
        case 'string':
            if (typeof value !== 'string') {
                throw new TypeError(`${paramName} must be string, got ${typeof value}`);
            }
            break;
        
        case 'int':
        case 'number':
            if (typeof value !== 'number' || !Number.isFinite(value)) {
                throw new TypeError(`${paramName} must be number, got ${typeof value}`);
            }
            break;
        
        case 'float':
            if (typeof value !== 'number' || !Number.isFinite(value)) {
                throw new TypeError(`${paramName} must be float, got ${typeof value}`);
            }
            break;
        
        case 'bool':
        case 'boolean':
            if (typeof value !== 'boolean') {
                throw new TypeError(`${paramName} must be boolean, got ${typeof value}`);
            }
            break;
        
        case 'list':
        case 'array':
            if (!Array.isArray(value)) {
                throw new TypeError(`${paramName} must be array, got ${typeof value}`);
            }
            break;
        
        case 'dict':
        case 'object':
            if (typeof value !== 'object' || value === null || Array.isArray(value)) {
                throw new TypeError(`${paramName} must be object, got ${typeof value}`);
            }
            break;
        
        case 'None':
        case 'null':
            if (value !== null && value !== undefined) {
                throw new TypeError(`${paramName} must be null/undefined, got ${typeof value}`);
            }
            break;
        
        default:
            // Unknown type name, skip validation
            break;
    }
}

/**
 * Validate complex types (List[T], Dict[K, V], etc.).
 */
function validateComplexType(value, typeObj, paramName) {
    if (typeObj.type === 'List' || typeObj.type === 'Array') {
        if (!Array.isArray(value)) {
            throw new TypeError(`${paramName} must be array, got ${typeof value}`);
        }
        
        if (typeObj.itemType) {
            value.forEach((item, index) => {
                try {
                    validate(item, typeObj.itemType, `${paramName}[${index}]`);
                } catch (e) {
                    throw new TypeError(
                        `${paramName}[${index}] has wrong type: ${e.message}`
                    );
                }
            });
        }
        return;
    }
    
    if (typeObj.type === 'Dict' || typeObj.type === 'Object') {
        if (typeof value !== 'object' || value === null || Array.isArray(value)) {
            throw new TypeError(`${paramName} must be object, got ${typeof value}`);
        }
        
        if (typeObj.keyType || typeObj.valueType) {
            for (const [key, val] of Object.entries(value)) {
                if (typeObj.keyType) {
                    try {
                        validate(key, typeObj.keyType, `${paramName} key`);
                    } catch (e) {
                        throw new TypeError(`Key has wrong type: ${e.message}`);
                    }
                }
                if (typeObj.valueType) {
                    try {
                        validate(val, typeObj.valueType, `${paramName}['${key}']`);
                    } catch (e) {
                        throw new TypeError(
                            `${paramName}['${key}'] has wrong type: ${e.message}`
                        );
                    }
                }
            }
        }
        return;
    }
    
    if (typeObj.type === 'Union') {
        // Try each type in union
        let matched = false;
        for (const unionType of typeObj.types) {
            try {
                validate(value, unionType, paramName);
                matched = true;
                break;
            } catch (e) {
                // Try next type
            }
        }
        
        if (!matched) {
            throw new TypeError(
                `${paramName} must be one of ${typeObj.types.map(t => 
                    typeof t === 'string' ? t : t.name || 'unknown'
                ).join(', ')}, got ${typeof value}`
            );
        }
        return;
    }
}

/**
 * Check if type checking is enabled (for production builds).
 */
export function isTypeCheckingEnabled() {
    // In production, this could check an environment variable
    return typeof process === 'undefined' || process.env.NODE_ENV !== 'production';
}

/**
 * Create a type validator function.
 */
export function createValidator(expectedType) {
    return function(value, paramName) {
        validate(value, expectedType, paramName);
    };
}

/**
 * Validate function arguments against type hints.
 */
export function validateArguments(args, typeHints, paramNames) {
    if (!isTypeCheckingEnabled()) {
        return;
    }
    
    for (let i = 0; i < args.length; i++) {
        const paramName = paramNames[i] || `arg${i}`;
        const expectedType = typeHints[paramName];
        
        if (expectedType !== undefined) {
            try {
                validate(args[i], expectedType, paramName);
            } catch (e) {
                throw new TypeError(`Argument ${paramName}: ${e.message}`);
            }
        }
    }
}

/**
 * Validate function return value.
 */
export function validateReturn(value, returnType, functionName = 'function') {
    if (!isTypeCheckingEnabled()) {
        return;
    }
    
    if (returnType !== undefined) {
        try {
            validate(value, returnType, 'return value');
        } catch (e) {
            throw new TypeError(`${functionName} return value: ${e.message}`);
        }
    }
}

