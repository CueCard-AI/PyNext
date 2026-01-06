/**
 * PyNext Transpiler - Python Exception Types for JavaScript
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides JavaScript error classes that match Python's complete exception
 * hierarchy. This enables proper exception handling with try/except patterns,
 * isinstance()/issubclass() checks, and exception chaining.
 * 
 * =============================================================================
 * WHY THIS EXISTS (Problem It Solves)
 * =============================================================================
 * 
 * Python has a rich exception hierarchy:
 * 
 *   BaseException (root)
 *   ├── SystemExit
 *   ├── KeyboardInterrupt
 *   └── Exception
 *       ├── StopIteration
 *       ├── StopAsyncIteration
 *       ├── ArithmeticError
 *       │   ├── ZeroDivisionError
 *       │   ├── OverflowError
 *       │   └── FloatingPointError
 *       ├── LookupError
 *       │   ├── KeyError
 *       │   └── IndexError
 *       ├── OSError
 *       ├── RuntimeError
 *       │   └── RecursionError
 *       ├── ValueError
 *       ├── TypeError
 *       ├── AttributeError
 *       ├── AssertionError
 *       └── NotImplementedError
 * 
 * JavaScript only has Error. By creating specific error classes with proper
 * inheritance, transpiled code can do proper exception type checking:
 * 
 *   try:
 *       items.index(x)
 *   except ValueError:
 *       print("Not found")
 *   
 *   try:
 *       process()
 *   except (ValueError, TypeError) as e:
 *       print(f"Error: {e}")
 *   
 *   raise ValueError("msg") from original_error
 * 
 * =============================================================================
 * WHO USES THIS
 * =============================================================================
 * 
 * - Transpiled Python code that raises/catches exceptions
 * - isinstance() and issubclass() runtime helpers
 * - Exception chaining (raise ... from ...)
 * - Custom exception classes
 * 
 * =============================================================================
 * WHEN THIS IS USED
 * =============================================================================
 * 
 * - At runtime when exceptions are raised
 * - When checking exception types with isinstance()
 * - When checking class hierarchies with issubclass()
 * - When chaining exceptions with raise ... from ...
 * 
 * =============================================================================
 * WHERE THIS FITS
 * =============================================================================
 * 
 * Part of the runtime helpers (pynext/transpiler/runtime/errors.js).
 * Imported by transpiled JavaScript code and used for exception handling.
 * 
 * =============================================================================
 * HOW IT WORKS
 * =============================================================================
 * 
 * 1. BaseException is the root class (extends Error)
 * 2. All exceptions extend BaseException or Exception
 * 3. Inheritance is tracked via prototype chain
 * 4. isinstance() checks prototype chain for type matching
 * 5. issubclass() checks prototype chain for class relationships
 * 6. Exception chaining uses __cause__ and __context__ attributes
 * 
 * =============================================================================
 * EXAMPLES
 * =============================================================================
 * 
 * Basic exception:
 *   throw new ValueError("list.index(x): x not in list");
 * 
 * Exception chaining:
 *   try:
 *       process()
 *   except Exception as e:
 *       raise ValueError("failed") from e
 *   # ValueError.__cause__ = e
 * 
 * isinstance() check:
 *   try:
 *       items.index(x)
 *   except Exception as e:
 *       if isinstance(e, ValueError):
 *           print("Value error")
 *       elif isinstance(e, (KeyError, IndexError)):
 *           print("Lookup error")
 * 
 * issubclass() check:
 *   if issubclass(ZeroDivisionError, ArithmeticError):
 *       print("ZeroDivisionError is an ArithmeticError")
 * 
 * =============================================================================
 * EDGE CASES
 * =============================================================================
 * 
 * - isinstance(None, Exception) → false (None is not an exception)
 * - isinstance(Error, Exception) → false (JavaScript Error is not Python Exception)
 * - issubclass(ValueError, ValueError) → true (class is subclass of itself)
 * - issubclass(BaseException, Exception) → false (BaseException is parent of Exception)
 * 
 * =============================================================================
 * RELATED FILES
 * =============================================================================
 * 
 * - emitter.py: Emits isinstance()/issubclass() calls
 * - parser.py: Parses raise ... from ... syntax
 * - core.js: Basic isinstance() for non-exception types
 */

// =============================================================================
// BASE EXCEPTION CLASSES
// =============================================================================

/**
 * BaseException - Root class for all Python exceptions.
 * 
 * WHAT: The ultimate base class for all exceptions in Python.
 * WHY: Provides common functionality and allows catching all exceptions.
 * HOW: Extends JavaScript's Error class for compatibility.
 * WHO: All Python exceptions inherit from this.
 * WHEN: Used as the base for all exception types.
 * WHERE: Root of the exception hierarchy.
 * 
 * Examples:
 *   class CustomError(BaseException): ...
 *   except BaseException:  # Catches everything
 */
export class BaseException extends Error {
    constructor(message = '') {
        super(message);
        this.name = 'BaseException';
        // Exception chaining attributes (Phase 33.3)
        this.__cause__ = null;      // Explicit cause (raise ... from ...)
        this.__context__ = null;    // Implicit context (exception during handling)
        this.__traceback__ = null;  // Traceback object (for future use)
        // Maintain proper stack trace in V8
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, this.constructor);
        }
    }
}

/**
 * PyException - Alias for BaseException (backward compatibility).
 * 
 * WHAT: Legacy name for BaseException, kept for backward compatibility.
 * WHY: Existing code may reference PyException.
 * HOW: Simply exports BaseException with an alias.
 */
export const PyException = BaseException;

// =============================================================================
// SYSTEM EXCEPTIONS (extend BaseException directly)
// =============================================================================

/**
 * SystemExit - Raised when sys.exit() is called.
 * 
 * WHAT: Exception raised to exit the program.
 * WHY: Allows cleanup code in finally blocks to run.
 * HOW: Extends BaseException (not Exception) so it's not caught by except Exception.
 * WHO: Raised by sys.exit().
 * WHEN: When program should exit.
 * WHERE: System-level exception.
 * 
 * Examples:
 *   sys.exit(0)  # Raises SystemExit(0)
 *   try:
 *       sys.exit(1)
 *   except SystemExit as e:
 *       print(f"Exiting with code {e.code}")
 */
export class SystemExit extends BaseException {
    constructor(code = 0) {
        super(`SystemExit: ${code}`);
        this.name = 'SystemExit';
        this.code = code;
    }
}

/**
 * KeyboardInterrupt - Raised when user presses Ctrl+C.
 * 
 * WHAT: Exception raised when user interrupts the program.
 * WHY: Allows graceful handling of user interruption.
 * HOW: Extends BaseException (not Exception) so it's not caught by except Exception.
 * WHO: Raised by keyboard interrupt signal.
 * WHEN: When user presses interrupt key (Ctrl+C).
 * WHERE: System-level exception.
 * 
 * Examples:
 *   try:
 *       long_running_task()
 *   except KeyboardInterrupt:
 *       print("Interrupted by user")
 */
export class KeyboardInterrupt extends BaseException {
    constructor(message = 'KeyboardInterrupt') {
        super(message);
        this.name = 'KeyboardInterrupt';
    }
}

// =============================================================================
// EXCEPTION CLASS (base for all user exceptions)
// =============================================================================

/**
 * Exception - Base class for all user exceptions.
 * 
 * WHAT: Base class for all exceptions that should be caught by except Exception.
 * WHY: Separates system exceptions (BaseException) from user exceptions (Exception).
 * HOW: Extends BaseException.
 * WHO: All user-defined exceptions should extend this.
 * WHEN: Used as base class for custom exceptions.
 * WHERE: Parent of all standard exceptions except SystemExit and KeyboardInterrupt.
 * 
 * Examples:
 *   class CustomError(Exception): ...
 *   except Exception:  # Catches all user exceptions, not SystemExit/KeyboardInterrupt
 */
export class Exception extends BaseException {
    constructor(message = '') {
        super(message);
        this.name = 'Exception';
    }
}

// =============================================================================
// STANDARD PYTHON EXCEPTIONS (extend Exception)
// =============================================================================

/**
 * ValueError - Raised when an operation receives an argument with the right
 * type but an inappropriate value.
 * 
 * WHAT: Exception for invalid values (wrong value, right type).
 * WHY: Distinguishes value errors from type errors.
 * HOW: Extends Exception.
 * WHO: Raised by operations like list.index(), int(), math.sqrt().
 * WHEN: When value is wrong but type is correct.
 * WHERE: Common exception for validation errors.
 * 
 * Examples:
 *   - list.index(x) when x is not in list
 *   - int("abc")
 *   - math.sqrt(-1)
 */
export class ValueError extends Exception {
    constructor(message = '') {
        super(message);
        this.name = 'ValueError';
    }
}

/**
 * TypeError - Raised when an operation is applied to an object of 
 * inappropriate type.
 * 
 * WHAT: Exception for type mismatches (wrong type).
 * WHY: Distinguishes type errors from value errors.
 * HOW: Extends Exception.
 * WHO: Raised by operations like len(5), "str" + 5.
 * WHEN: When type is wrong.
 * WHERE: Common exception for type checking.
 * 
 * Examples:
 *   - len(5)
 *   - "str" + 5
 *   - sorted([1, "a"])
 */
export class TypeError_ extends Exception {
    constructor(message = '') {
        super(message);
        this.name = 'TypeError';
    }
}
// Export as TypeError (avoiding conflict with global TypeError)
export { TypeError_ as PyTypeError };

// =============================================================================
// ARITHMETIC ERROR HIERARCHY
// =============================================================================

/**
 * ArithmeticError - Base class for arithmetic errors.
 * 
 * WHAT: Base class for arithmetic-related exceptions.
 * WHY: Groups arithmetic errors together for exception handling.
 * HOW: Extends Exception.
 * WHO: Parent of ZeroDivisionError, OverflowError, FloatingPointError.
 * WHEN: Used as base class for arithmetic exceptions.
 * WHERE: Part of exception hierarchy.
 * 
 * Examples:
 *   except ArithmeticError:  # Catches all arithmetic errors
 */
export class ArithmeticError extends Exception {
    constructor(message = '') {
        super(message);
        this.name = 'ArithmeticError';
    }
}

/**
 * ZeroDivisionError - Raised when division by zero occurs.
 * 
 * WHAT: Exception for division/modulo by zero.
 * WHY: Specific error for a common arithmetic mistake.
 * HOW: Extends ArithmeticError.
 * WHO: Raised by division and modulo operations.
 * WHEN: When dividing by zero.
 * WHERE: Arithmetic error hierarchy.
 * 
 * Examples:
 *   1 / 0  # Raises ZeroDivisionError
 *   1 % 0   # Raises ZeroDivisionError
 */
export class ZeroDivisionError extends ArithmeticError {
    constructor(message = 'division by zero') {
        super(message);
        this.name = 'ZeroDivisionError';
    }
}

/**
 * OverflowError - Raised when arithmetic operation exceeds limits.
 * 
 * WHAT: Exception for arithmetic overflow.
 * WHY: Signals when result exceeds representable range.
 * HOW: Extends ArithmeticError.
 * WHO: Raised by arithmetic operations that overflow.
 * WHEN: When result is too large to represent.
 * WHERE: Arithmetic error hierarchy.
 * 
 * Examples:
 *   # In Python, this is rare due to arbitrary precision integers
 *   # In JavaScript, this would be Infinity, not OverflowError
 */
export class OverflowError extends ArithmeticError {
    constructor(message = '') {
        super(message);
        this.name = 'OverflowError';
    }
}

/**
 * FloatingPointError - Raised when floating point operation fails.
 * 
 * WHAT: Exception for floating point errors.
 * WHY: Signals floating point calculation issues.
 * HOW: Extends ArithmeticError.
 * WHO: Raised by floating point operations (rare in practice).
 * WHEN: When floating point calculation fails.
 * WHERE: Arithmetic error hierarchy.
 */
export class FloatingPointError extends ArithmeticError {
    constructor(message = '') {
        super(message);
        this.name = 'FloatingPointError';
    }
}

// =============================================================================
// LOOKUP ERROR HIERARCHY
// =============================================================================

/**
 * LookupError - Base class for lookup errors.
 * 
 * WHAT: Base class for key/index lookup exceptions.
 * WHY: Groups lookup errors together for exception handling.
 * HOW: Extends Exception.
 * WHO: Parent of KeyError and IndexError.
 * WHEN: Used as base class for lookup exceptions.
 * WHERE: Part of exception hierarchy.
 * 
 * Examples:
 *   except LookupError:  # Catches KeyError and IndexError
 */
export class LookupError extends Exception {
    constructor(message = '') {
        super(message);
        this.name = 'LookupError';
    }
}

/**
 * KeyError - Raised when a dict key is not found.
 * 
 * WHAT: Exception for missing dictionary keys.
 * WHY: Specific error for dictionary key lookups.
 * HOW: Extends LookupError.
 * WHO: Raised by dict[key] and dict.pop() without default.
 * WHEN: When key is not in dictionary.
 * WHERE: Lookup error hierarchy.
 * 
 * Examples:
 *   - d["missing"]
 *   - d.pop("missing") without default
 */
export class KeyError extends LookupError {
    constructor(key) {
        super(`KeyError: ${JSON.stringify(key)}`);
        this.name = 'KeyError';
        this.key = key;
    }
}

/**
 * IndexError - Raised when a sequence index is out of range.
 * 
 * WHAT: Exception for out-of-range sequence indices.
 * WHY: Specific error for sequence indexing.
 * HOW: Extends LookupError.
 * WHO: Raised by list[index] and list.pop() on empty list.
 * WHEN: When index is out of range.
 * WHERE: Lookup error hierarchy.
 * 
 * Examples:
 *   - items[100] on a small list
 *   - items.pop() on empty list
 */
export class IndexError extends LookupError {
    constructor(message = 'list index out of range') {
        super(message);
        this.name = 'IndexError';
    }
}

/**
 * AttributeError - Raised when attribute reference or assignment fails.
 * 
 * Examples:
 *   - obj.nonexistent_attr
 *   - None.something
 */
export class AttributeError extends PyException {
    constructor(message) {
        super(message);
        this.name = 'AttributeError';
    }
}

/**
 * RuntimeError - Raised when an error is detected that doesn't fall into
 * any other category.
 * 
 * WHAT: Generic runtime exception for errors that don't fit other categories.
 * WHY: Catch-all for runtime errors.
 * HOW: Extends Exception.
 * WHO: Raised by runtime errors that don't fit other categories.
 * WHEN: When error doesn't fit other exception types.
 * WHERE: Common exception for runtime errors.
 */
export class RuntimeError extends Exception {
    constructor(message = '') {
        super(message);
        this.name = 'RuntimeError';
    }
}

/**
 * RecursionError - Raised when maximum recursion depth is exceeded.
 * 
 * WHAT: Exception for recursion depth exceeded.
 * WHY: Specific error for recursion limits.
 * HOW: Extends RuntimeError.
 * WHO: Raised when recursion depth is exceeded.
 * WHEN: When function calls itself too many times.
 * WHERE: Runtime error hierarchy.
 * 
 * Examples:
 *   def recurse():
 *       recurse()  # Raises RecursionError
 */
export class RecursionError extends RuntimeError {
    constructor(message = 'maximum recursion depth exceeded') {
        super(message);
        this.name = 'RecursionError';
    }
}

/**
 * OSError - Base class for OS-related errors.
 * 
 * WHAT: Base class for operating system errors.
 * WHY: Groups OS-related errors together.
 * HOW: Extends Exception.
 * WHO: Parent of FileNotFoundError, PermissionError, etc.
 * WHEN: Used as base class for OS exceptions.
 * WHERE: Part of exception hierarchy.
 * 
 * Examples:
 *   except OSError:  # Catches all OS errors
 */
export class OSError extends Exception {
    constructor(message = '', errno = null, filename = null) {
        super(message);
        this.name = 'OSError';
        this.errno = errno;
        this.filename = filename;
    }
}

/**
 * StopIteration - Raised to signal the end of an iterator.
 * 
 * WHAT: Exception raised by iterators when exhausted.
 * WHY: Signals end of iteration for regular iterators.
 * HOW: Extends Exception.
 * WHO: Raised by regular generators (def with yield).
 * WHEN: When iterator has no more values.
 * WHERE: Part of iteration protocol.
 * 
 * Examples:
 *   def gen():
 *       yield 1
 *       yield 2
 *   # Raises StopIteration when exhausted
 */
export class StopIteration extends Exception {
    constructor(value = undefined) {
        super('StopIteration');
        this.name = 'StopIteration';
        this.value = value;
    }
}

/**
 * StopAsyncIteration - Raised to signal the end of an async iterator.
 * 
 * WHAT: Exception raised by async generators (async def with yield) when
 *       they are exhausted. Similar to StopIteration but for async iterators.
 * 
 * WHY: Python distinguishes between regular iterators (StopIteration) and
 *      async iterators (StopAsyncIteration). This enables proper exception
 *      handling in async for loops.
 * 
 * HOW: Raised automatically by async generators when they have no more values
 *      to yield. Caught by async for loops to signal completion.
 * 
 * WHO: Used by async generators and async for loops.
 * 
 * WHEN: Raised when an async generator's next() method is called after it
 *       has finished yielding all values.
 * 
 * WHERE: Part of the async iteration protocol, used in async for loops.
 * 
 * Examples:
 *   Python:                          JavaScript:
 *   async def gen():                 async function* gen() {
 *       yield 1                          yield 1;
 *       yield 2                          yield 2;
 *   # Raises StopAsyncIteration      // Raises StopAsyncIteration
 *                                     }
 *   
 *   async for item in gen():         for await (const item of gen()) {
 *       print(item)                      console.log(item);
 *   # Catches StopAsyncIteration     // Catches StopAsyncIteration
 * 
 * Difference from StopIteration:
 *   - StopIteration: Regular generators (def with yield)
 *   - StopAsyncIteration: Async generators (async def with yield)
 *   - Both signal end of iteration, but async version is for async iterators
 * 
 * Related:
 *   - generators.js: wrapAsyncGenerator() - handles StopAsyncIteration
 *   - async_support.py: _emit_async_for() - catches StopAsyncIteration
 */
export class StopAsyncIteration extends Exception {
    constructor(value = undefined) {
        super('StopAsyncIteration');
        this.name = 'StopAsyncIteration';
        this.value = value;
    }
}

/**
 * AssertionError - Raised when an assert statement fails.
 * 
 * WHAT: Exception raised by assert statements.
 * WHY: Signals assertion failures in code.
 * HOW: Extends Exception.
 * WHO: Raised by assert statements.
 * WHEN: When assert condition is false.
 * WHERE: Common exception for assertions.
 */
export class AssertionError extends Exception {
    constructor(message = '') {
        super(message);
        this.name = 'AssertionError';
    }
}

/**
 * NotImplementedError - Raised when an abstract method is not implemented.
 * 
 * WHAT: Exception for unimplemented methods.
 * WHY: Signals that a method should be implemented by a subclass.
 * HOW: Extends Exception.
 * WHO: Raised by abstract methods that aren't implemented.
 * WHEN: When calling an unimplemented abstract method.
 * WHERE: Common exception for abstract classes.
 */
export class NotImplementedError extends Exception {
    constructor(message = '') {
        super(message);
        this.name = 'NotImplementedError';
    }
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * isinstance() - Check if an error is an instance of a type (with inheritance).
 * 
 * WHAT: Checks if an error is an instance of a type, following the exception hierarchy.
 * WHY: Python's isinstance() checks inheritance, not just exact type match.
 * HOW: Traverses prototype chain to check if error is instance of type.
 * WHO: Used by transpiled code for exception type checking.
 * WHEN: When checking exception types in except clauses or isinstance() calls.
 * WHERE: Runtime helper for exception type checking.
 * 
 * Examples:
 *   isinstance(ValueError("msg"), ValueError) → true
 *   isinstance(ValueError("msg"), Exception) → true (ValueError extends Exception)
 *   isinstance(ValueError("msg"), BaseException) → true (Exception extends BaseException)
 *   isinstance(ValueError("msg"), KeyError) → false
 *   isinstance(ZeroDivisionError("msg"), ArithmeticError) → true
 *   isinstance(KeyError("k"), LookupError) → true
 * 
 * Edge Cases:
 *   - isinstance(null, Exception) → false (null is not an exception)
 *   - isinstance(Error("msg"), Exception) → false (JS Error is not Python Exception)
 *   - isinstance(ValueError("msg"), ValueError) → true (class is instance of itself)
 * 
 * @param {Error|*} error - The error to check (can be any value)
 * @param {string|Function|Array} type - The type name, constructor, or tuple of types
 * @returns {boolean} Whether the error is an instance of the type
 */
export function isInstance(error, type) {
    // Handle null/undefined
    if (error === null || error === undefined) {
        return false;
    }
    
    // Handle non-Error objects (not exceptions)
    if (!(error instanceof Error)) {
        return false;
    }
    
    // Handle tuple of types (isinstance(obj, (Type1, Type2)))
    if (Array.isArray(type)) {
        return type.some(t => isInstance(error, t));
    }
    
    // Handle string type name (e.g., 'ValueError', 'Exception')
    if (typeof type === 'string') {
        // Check exact match first
        if (error.name === type) {
            return true;
        }
        
        // Check inheritance by traversing prototype chain
        let proto = Object.getPrototypeOf(error);
        while (proto !== null && proto !== Error.prototype) {
            if (proto.name === type) {
                return true;
            }
            proto = Object.getPrototypeOf(proto);
        }
        
        // Check if it's a BaseException/Exception hierarchy match
        // All Python exceptions extend BaseException
        if (type === 'BaseException' || type === 'Exception') {
            // Check if error is a Python exception (has name matching known types)
            const pythonExceptionNames = [
                'BaseException', 'Exception', 'SystemExit', 'KeyboardInterrupt',
                'StopIteration', 'StopAsyncIteration',
                'ArithmeticError', 'ZeroDivisionError', 'OverflowError', 'FloatingPointError',
                'LookupError', 'KeyError', 'IndexError',
                'OSError', 'RuntimeError', 'RecursionError',
                'ValueError', 'TypeError', 'AttributeError',
                'AssertionError', 'NotImplementedError'
            ];
            if (pythonExceptionNames.includes(error.name)) {
                // Check hierarchy
                if (type === 'BaseException') {
                    return true; // All Python exceptions extend BaseException
                } else if (type === 'Exception') {
                    // Exception extends BaseException, so check if error extends Exception
                    // SystemExit and KeyboardInterrupt extend BaseException but not Exception
                    return error.name !== 'SystemExit' && error.name !== 'KeyboardInterrupt';
                }
            }
        }
        
        return false;
    }
    
    // Handle constructor function (e.g., ValueError, Exception)
    if (typeof type === 'function') {
        // Check instanceof (works for class constructors)
        if (error instanceof type) {
            return true;
        }
        
        // Also check by name (for cases where instanceof doesn't work)
        if (type.name && error.name === type.name) {
            return true;
        }
        
        // Check prototype chain
        let proto = Object.getPrototypeOf(error);
        while (proto !== null && proto !== Error.prototype) {
            if (proto.constructor === type) {
                return true;
            }
            proto = Object.getPrototypeOf(proto);
        }
        
        return false;
    }
    
    return false;
}

/**
 * issubclass() - Check if a class is a subclass of another (with inheritance).
 * 
 * WHAT: Checks if a class is a subclass of another, following the exception hierarchy.
 * WHY: Python's issubclass() checks inheritance relationships between classes.
 * HOW: Traverses prototype chain to check if class extends another.
 * WHO: Used by transpiled code for class hierarchy checking.
 * WHEN: When checking class relationships in issubclass() calls.
 * WHERE: Runtime helper for class hierarchy checking.
 * 
 * Examples:
 *   issubclass(ValueError, ValueError) → true (class is subclass of itself)
 *   issubclass(ValueError, Exception) → true (ValueError extends Exception)
 *   issubclass(ValueError, BaseException) → true (Exception extends BaseException)
 *   issubclass(ZeroDivisionError, ArithmeticError) → true
 *   issubclass(KeyError, LookupError) → true
 *   issubclass(ValueError, KeyError) → false
 * 
 * Edge Cases:
 *   - issubclass(BaseException, Exception) → false (BaseException is parent of Exception)
 *   - issubclass(Exception, BaseException) → true (Exception extends BaseException)
 * 
 * @param {Function|string} cls - The class to check (constructor or class name)
 * @param {Function|string|Array} base - The base class, class name, or tuple of classes
 * @returns {boolean} Whether cls is a subclass of base
 */
export function isSubclass(cls, base) {
    // Handle tuple of bases (issubclass(cls, (Base1, Base2)))
    if (Array.isArray(base)) {
        return base.some(b => isSubclass(cls, b));
    }
    
    // Convert class name to constructor if needed
    let clsConstructor = cls;
    if (typeof cls === 'string') {
        clsConstructor = getExceptionConstructor(cls);
        if (!clsConstructor) {
            return false; // Unknown class name
        }
    }
    
    // Convert base name to constructor if needed
    let baseConstructor = base;
    if (typeof base === 'string') {
        baseConstructor = getExceptionConstructor(base);
        if (!baseConstructor) {
            return false; // Unknown class name
        }
    }
    
    // A class is a subclass of itself
    if (clsConstructor === baseConstructor) {
        return true;
    }
    
    // Check if cls extends base by traversing prototype chain
    let proto = clsConstructor.prototype;
    while (proto !== null && proto !== Error.prototype) {
        if (proto.constructor === baseConstructor) {
            return true;
        }
        proto = Object.getPrototypeOf(proto);
    }
    
    return false;
}

/**
 * Get exception constructor by name.
 * 
 * WHAT: Maps exception class names to their constructors.
 * WHY: Needed for issubclass() and dynamic exception creation.
 * HOW: Returns constructor function for given name.
 * WHO: Used by isSubclass() and createError().
 * WHEN: When converting string names to constructors.
 * WHERE: Internal helper function.
 * 
 * @param {string} name - Exception class name
 * @returns {Function|null} Constructor function or null if not found
 */
function getExceptionConstructor(name) {
    const constructors = {
        'BaseException': BaseException,
        'Exception': Exception,
        'SystemExit': SystemExit,
        'KeyboardInterrupt': KeyboardInterrupt,
        'StopIteration': StopIteration,
        'StopAsyncIteration': StopAsyncIteration,
        'ArithmeticError': ArithmeticError,
        'ZeroDivisionError': ZeroDivisionError,
        'OverflowError': OverflowError,
        'FloatingPointError': FloatingPointError,
        'LookupError': LookupError,
        'KeyError': KeyError,
        'IndexError': IndexError,
        'OSError': OSError,
        'RuntimeError': RuntimeError,
        'RecursionError': RecursionError,
        'ValueError': ValueError,
        'TypeError': TypeError_,
        'AttributeError': AttributeError,
        'AssertionError': AssertionError,
        'NotImplementedError': NotImplementedError,
        // Aliases
        'PyException': BaseException,
        'PyTypeError': TypeError_,
    };
    return constructors[name] || null;
}

/**
 * Create an error from a type name (for dynamic exception creation).
 * 
 * WHAT: Creates an exception instance from a type name string.
 * WHY: Enables dynamic exception creation from string names.
 * HOW: Maps type names to constructors and instantiates them.
 * WHO: Used by transpiled code for dynamic exception creation.
 * WHEN: When exception type is determined at runtime.
 * WHERE: Runtime helper for exception creation.
 * 
 * Examples:
 *   createError('ValueError', 'message') → new ValueError('message')
 *   createError('KeyError', 'key') → new KeyError('key')
 * 
 * @param {string} typeName - Exception type name
 * @param {string|*} message - Error message or value (for KeyError, etc.)
 * @returns {Error} The error instance
 */
export function createError(typeName, message) {
    const constructor = getExceptionConstructor(typeName);
    if (constructor) {
        // Special handling for KeyError (takes key as first arg)
        if (typeName === 'KeyError') {
            return new KeyError(message);
        }
        // Special handling for SystemExit (takes code as first arg)
        if (typeName === 'SystemExit') {
            return new SystemExit(message);
        }
        // Default: pass message to constructor
        return new constructor(message);
    }
    // Fallback to BaseException for unknown types
    return new BaseException(message);
}

// =============================================================================
// EXPORTS
// =============================================================================

export default {
    // Base classes
    BaseException,
    PyException,  // Alias for BaseException (backward compatibility)
    Exception,
    
    // System exceptions
    SystemExit,
    KeyboardInterrupt,
    
    // Iteration exceptions
    StopIteration,
    StopAsyncIteration,
    
    // Arithmetic exceptions
    ArithmeticError,
    ZeroDivisionError,
    OverflowError,
    FloatingPointError,
    
    // Lookup exceptions
    LookupError,
    KeyError,
    IndexError,
    
    // OS exceptions
    OSError,
    
    // Runtime exceptions
    RuntimeError,
    RecursionError,
    
    // Standard exceptions
    ValueError,
    TypeError: TypeError_,
    PyTypeError: TypeError_,  // Alias (avoiding conflict with global TypeError)
    AttributeError,
    AssertionError,
    NotImplementedError,
    
    // Helper functions
    isInstance,
    isSubclass,
    createError,
};
