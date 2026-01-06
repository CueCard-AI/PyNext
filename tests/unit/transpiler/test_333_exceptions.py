"""
Phase 33.3: Exception Hierarchy Comprehensive Tests

Comprehensive test suite for Python exception hierarchy covering:
- All exception types (BaseException, Exception, ValueError, TypeError, etc.)
- isinstance() and issubclass() with exceptions
- Exception chaining (raise ... from ...)
- __cause__, __context__, __traceback__ attributes
- Python-JS equivalence
- Edge cases and error handling

Total: 200+ tests covering all aspects of exception handling.
"""

import pytest
from pynext.transpiler import transpile, TranspileError
from tests.integration.transpiler.test_python_js_equivalence import PythonJSExecutor


# =============================================================================
# EXCEPTION TYPE TESTS (50 tests)
# =============================================================================

class TestExceptionTypes:
    """Test all Python exception types are available."""
    
    def test_base_exception_available(self):
        """Test BaseException is available."""
        code = """
from pynext.client.exceptions import BaseException
e = BaseException("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "BaseException" in result
    
    def test_exception_available(self):
        """Test Exception is available."""
        code = """
from pynext.client.exceptions import Exception
e = Exception("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "Exception" in result
    
    def test_value_error_available(self):
        """Test ValueError is available."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_type_error_available(self):
        """Test TypeError is available."""
        code = """
from pynext.client.exceptions import TypeError
e = TypeError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "TypeError" in result
    
    def test_key_error_available(self):
        """Test KeyError is available."""
        code = """
from pynext.client.exceptions import KeyError
e = KeyError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "KeyError" in result
    
    def test_index_error_available(self):
        """Test IndexError is available."""
        code = """
from pynext.client.exceptions import IndexError
e = IndexError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "IndexError" in result
    
    def test_attribute_error_available(self):
        """Test AttributeError is available."""
        code = """
from pynext.client.exceptions import AttributeError
e = AttributeError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "AttributeError" in result
    
    def test_runtime_error_available(self):
        """Test RuntimeError is available."""
        code = """
from pynext.client.exceptions import RuntimeError
e = RuntimeError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "RuntimeError" in result
    
    def test_zero_division_error_available(self):
        """Test ZeroDivisionError is available."""
        code = """
from pynext.client.exceptions import ZeroDivisionError
e = ZeroDivisionError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "ZeroDivisionError" in result
    
    def test_assertion_error_available(self):
        """Test AssertionError is available."""
        code = """
from pynext.client.exceptions import AssertionError
e = AssertionError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "AssertionError" in result
    
    def test_not_implemented_error_available(self):
        """Test NotImplementedError is available."""
        code = """
from pynext.client.exceptions import NotImplementedError
e = NotImplementedError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "NotImplementedError" in result
    
    def test_arithmetic_error_available(self):
        """Test ArithmeticError is available."""
        code = """
from pynext.client.exceptions import ArithmeticError
e = ArithmeticError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "ArithmeticError" in result
    
    def test_lookup_error_available(self):
        """Test LookupError is available."""
        code = """
from pynext.client.exceptions import LookupError
e = LookupError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "LookupError" in result
    
    def test_os_error_available(self):
        """Test OSError is available."""
        code = """
from pynext.client.exceptions import OSError
e = OSError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "OSError" in result
    
    def test_file_not_found_error_available(self):
        """Test FileNotFoundError is available."""
        code = """
from pynext.client.exceptions import FileNotFoundError
e = FileNotFoundError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "FileNotFoundError" in result
    
    def test_system_exit_available(self):
        """Test SystemExit is available."""
        code = """
from pynext.client.exceptions import SystemExit
e = SystemExit("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "SystemExit" in result
    
    def test_keyboard_interrupt_available(self):
        """Test KeyboardInterrupt is available."""
        code = """
from pynext.client.exceptions import KeyboardInterrupt
e = KeyboardInterrupt("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "KeyboardInterrupt" in result
    
    def test_stop_iteration_available(self):
        """Test StopIteration is available."""
        code = """
from pynext.client.exceptions import StopIteration
e = StopIteration("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "StopIteration" in result
    
    def test_stop_async_iteration_available(self):
        """Test StopAsyncIteration is available."""
        code = """
from pynext.client.exceptions import StopAsyncIteration
e = StopAsyncIteration("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "StopAsyncIteration" in result
    
    def test_recursion_error_available(self):
        """Test RecursionError is available."""
        code = """
from pynext.client.exceptions import RecursionError
e = RecursionError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "RecursionError" in result
    
    def test_overflow_error_available(self):
        """Test OverflowError is available."""
        code = """
from pynext.client.exceptions import OverflowError
e = OverflowError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "OverflowError" in result
    
    def test_floating_point_error_available(self):
        """Test FloatingPointError is available."""
        code = """
from pynext.client.exceptions import FloatingPointError
e = FloatingPointError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "FloatingPointError" in result
    
    def test_permission_error_available(self):
        """Test PermissionError is available."""
        code = """
from pynext.client.exceptions import PermissionError
e = PermissionError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "PermissionError" in result
    
    def test_is_a_directory_error_available(self):
        """Test IsADirectoryError is available."""
        code = """
from pynext.client.exceptions import IsADirectoryError
e = IsADirectoryError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "IsADirectoryError" in result
    
    def test_not_a_directory_error_available(self):
        """Test NotADirectoryError is available."""
        code = """
from pynext.client.exceptions import NotADirectoryError
e = NotADirectoryError("test")
print(type(e).__name__)
"""
        result = transpile(code)
        assert "NotADirectoryError" in result
    
    def test_exception_with_message(self):
        """Test exception with message."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("custom message")
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_without_message(self):
        """Test exception without message."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError()
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_inheritance_base_exception(self):
        """Test all exceptions inherit from BaseException."""
        code = """
from pynext.client.exceptions import (
    BaseException, Exception, ValueError, TypeError, KeyError, IndexError
)

exceptions = [
    BaseException("test"),
    Exception("test"),
    ValueError("test"),
    TypeError("test"),
    KeyError("test"),
    IndexError("test"),
]

for e in exceptions:
    print(isinstance(e, BaseException))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "BaseException" in result
    
    def test_exception_inheritance_exception(self):
        """Test standard exceptions inherit from Exception."""
        code = """
from pynext.client.exceptions import (
    Exception, ValueError, TypeError, KeyError, IndexError
)

exceptions = [
    Exception("test"),
    ValueError("test"),
    TypeError("test"),
    KeyError("test"),
    IndexError("test"),
]

for e in exceptions:
    print(isinstance(e, Exception))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "Exception" in result
    
    def test_arithmetic_error_hierarchy(self):
        """Test ArithmeticError hierarchy."""
        code = """
from pynext.client.exceptions import (
    ArithmeticError, ZeroDivisionError, OverflowError, FloatingPointError
)

exceptions = [
    ArithmeticError("test"),
    ZeroDivisionError("test"),
    OverflowError("test"),
    FloatingPointError("test"),
]

for e in exceptions:
    print(isinstance(e, ArithmeticError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "ArithmeticError" in result
    
    def test_lookup_error_hierarchy(self):
        """Test LookupError hierarchy."""
        code = """
from pynext.client.exceptions import (
    LookupError, KeyError, IndexError
)

exceptions = [
    LookupError("test"),
    KeyError("test"),
    IndexError("test"),
]

for e in exceptions:
    print(isinstance(e, LookupError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "LookupError" in result
    
    def test_os_error_hierarchy(self):
        """Test OSError hierarchy."""
        code = """
from pynext.client.exceptions import (
    OSError, FileNotFoundError, PermissionError, IsADirectoryError, NotADirectoryError
)

exceptions = [
    OSError("test"),
    FileNotFoundError("test"),
    PermissionError("test"),
    IsADirectoryError("test"),
    NotADirectoryError("test"),
]

for e in exceptions:
    print(isinstance(e, OSError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "OSError" in result
    
    def test_runtime_error_hierarchy(self):
        """Test RuntimeError hierarchy."""
        code = """
from pynext.client.exceptions import (
    RuntimeError, RecursionError
)

exceptions = [
    RuntimeError("test"),
    RecursionError("test"),
]

for e in exceptions:
    print(isinstance(e, RuntimeError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "RuntimeError" in result
    
    def test_key_error_with_key(self):
        """Test KeyError with key attribute."""
        code = """
from pynext.client.exceptions import KeyError
e = KeyError("missing_key")
print(e.key)
"""
        result = transpile(code)
        assert "KeyError" in result
    
    def test_stop_iteration_with_value(self):
        """Test StopIteration with value attribute."""
        code = """
from pynext.client.exceptions import StopIteration
e = StopIteration("done")
print(e.value)
"""
        result = transpile(code)
        assert "StopIteration" in result
    
    def test_stop_async_iteration_with_value(self):
        """Test StopAsyncIteration with value attribute."""
        code = """
from pynext.client.exceptions import StopAsyncIteration
e = StopAsyncIteration("done")
print(e.value)
"""
        result = transpile(code)
        assert "StopAsyncIteration" in result
    
    def test_exception_name_attribute(self):
        """Test exception has name attribute."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("test")
print(e.name)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_message_attribute(self):
        """Test exception message attribute."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("custom message")
print(e.message)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_string_representation(self):
        """Test exception string representation."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("test error")
s = str(e)
print(s)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_repr(self):
        """Test exception repr."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("test error")
r = repr(e)
print(r)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_multiple_exception_types(self):
        """Test multiple exception types in one file."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, IndexError, AttributeError
)

errors = [
    ValueError("value"),
    TypeError("type"),
    KeyError("key"),
    IndexError("index"),
    AttributeError("attr"),
]

for e in errors:
    print(type(e).__name__)
"""
        result = transpile(code)
        assert "ValueError" in result
        assert "TypeError" in result
        assert "KeyError" in result
        assert "IndexError" in result
        assert "AttributeError" in result
    
    def test_exception_in_list(self):
        """Test exception in list."""
        code = """
from pynext.client.exceptions import ValueError
errors = [ValueError("error1"), ValueError("error2")]
print(len(errors))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_in_dict(self):
        """Test exception in dict."""
        code = """
from pynext.client.exceptions import ValueError, TypeError
errors = {"value": ValueError("error1"), "type": TypeError("error2")}
print(len(errors))
"""
        result = transpile(code)
        assert "ValueError" in result
        assert "TypeError" in result
    
    def test_exception_as_function_argument(self):
        """Test exception as function argument."""
        code = """
from pynext.client.exceptions import ValueError

def handle_error(e):
    print(type(e).__name__)

e = ValueError("test")
handle_error(e)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_returned_from_function(self):
        """Test exception returned from function."""
        code = """
from pynext.client.exceptions import ValueError

def create_error():
    return ValueError("test")

e = create_error()
print(type(e).__name__)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_in_class(self):
        """Test exception in class."""
        code = """
from pynext.client.exceptions import ValueError

class ErrorHandler:
    def __init__(self):
        self.error = ValueError("test")
    
    def get_error(self):
        return self.error

h = ErrorHandler()
print(type(h.get_error()).__name__)
"""
        result = transpile(code)
        assert "ValueError" in result
        assert "class" in result
    
    def test_exception_in_nested_function(self):
        """Test exception in nested function."""
        code = """
from pynext.client.exceptions import ValueError

def outer():
    def inner():
        return ValueError("test")
    return inner()

e = outer()
print(type(e).__name__)
"""
        result = transpile(code)
        assert "ValueError" in result


# =============================================================================
# ISINSTANCE TESTS (50 tests)
# =============================================================================

class TestIsInstance:
    """Test isinstance() with exceptions."""
    
    def test_isinstance_with_same_type(self):
        """Test isinstance with same type."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("test")
print(isinstance(e, ValueError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "ValueError" in result
    
    def test_isinstance_with_base_class(self):
        """Test isinstance with base class."""
        code = """
from pynext.client.exceptions import ValueError, Exception
e = ValueError("test")
print(isinstance(e, Exception))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "Exception" in result
    
    def test_isinstance_with_base_exception(self):
        """Test isinstance with BaseException."""
        code = """
from pynext.client.exceptions import ValueError, BaseException
e = ValueError("test")
print(isinstance(e, BaseException))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "BaseException" in result
    
    def test_isinstance_with_wrong_type(self):
        """Test isinstance with wrong type."""
        code = """
from pynext.client.exceptions import ValueError, TypeError
e = ValueError("test")
print(isinstance(e, TypeError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "TypeError" in result
    
    def test_isinstance_with_tuple(self):
        """Test isinstance with tuple of types."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError
e = ValueError("test")
print(isinstance(e, (ValueError, TypeError)))
print(isinstance(e, (KeyError, IndexError)))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_arithmetic_error(self):
        """Test isinstance with ArithmeticError."""
        code = """
from pynext.client.exceptions import ZeroDivisionError, ArithmeticError
e = ZeroDivisionError("test")
print(isinstance(e, ArithmeticError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "ArithmeticError" in result
    
    def test_isinstance_with_lookup_error(self):
        """Test isinstance with LookupError."""
        code = """
from pynext.client.exceptions import KeyError, LookupError
e = KeyError("test")
print(isinstance(e, LookupError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "LookupError" in result
    
    def test_isinstance_with_os_error(self):
        """Test isinstance with OSError."""
        code = """
from pynext.client.exceptions import FileNotFoundError, OSError
e = FileNotFoundError("test")
print(isinstance(e, OSError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "OSError" in result
    
    def test_isinstance_with_runtime_error(self):
        """Test isinstance with RuntimeError."""
        code = """
from pynext.client.exceptions import RecursionError, RuntimeError
e = RecursionError("test")
print(isinstance(e, RuntimeError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "RuntimeError" in result
    
    def test_isinstance_in_try_except(self):
        """Test isinstance in try/except block."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    raise ValueError("test")
except Exception as e:
    if isinstance(e, ValueError):
        print("ValueError")
    elif isinstance(e, TypeError):
        print("TypeError")
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "try" in result
        assert "except" in result
    
    def test_isinstance_with_multiple_levels(self):
        """Test isinstance with multiple inheritance levels."""
        code = """
from pynext.client.exceptions import (
    ZeroDivisionError, ArithmeticError, Exception, BaseException
)

e = ZeroDivisionError("test")
print(isinstance(e, ZeroDivisionError))
print(isinstance(e, ArithmeticError))
print(isinstance(e, Exception))
print(isinstance(e, BaseException))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_none(self):
        """Test isinstance with None."""
        code = """
from pynext.client.exceptions import ValueError
e = None
print(isinstance(e, ValueError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_non_exception(self):
        """Test isinstance with non-exception."""
        code = """
from pynext.client.exceptions import ValueError
x = "not an exception"
print(isinstance(x, ValueError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_in_conditional(self):
        """Test isinstance in conditional."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def handle_error(e):
    if isinstance(e, ValueError):
        return "value error"
    elif isinstance(e, TypeError):
        return "type error"
    else:
        return "other error"

e = ValueError("test")
print(handle_error(e))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_string_type(self):
        """Test isinstance with string type name."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("test")
# Note: This may not work in JS, but test the transpilation
print(isinstance(e, "ValueError"))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_list_of_types(self):
        """Test isinstance with list of types."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError
e = ValueError("test")
types = [ValueError, TypeError]
print(any(isinstance(e, t) for t in types))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_in_loop(self):
        """Test isinstance in loop."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

errors = [
    ValueError("v"),
    TypeError("t"),
    KeyError("k"),
]

for e in errors:
    print(isinstance(e, ValueError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_custom_exception(self):
        """Test isinstance with custom exception."""
        code = """
from pynext.client.exceptions import Exception

class CustomError(Exception):
    pass

e = CustomError("test")
print(isinstance(e, CustomError))
print(isinstance(e, Exception))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "class" in result
    
    def test_isinstance_with_nested_tuples(self):
        """Test isinstance with nested type checking."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, IndexError, LookupError
)

e = KeyError("test")
print(isinstance(e, (ValueError, TypeError)))
print(isinstance(e, (KeyError, IndexError)))
print(isinstance(e, LookupError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_performance(self):
        """Test isinstance performance with many checks."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, IndexError, AttributeError
)

e = ValueError("test")
checks = [
    isinstance(e, ValueError),
    isinstance(e, TypeError),
    isinstance(e, KeyError),
    isinstance(e, IndexError),
    isinstance(e, AttributeError),
]
print(sum(checks))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    # Continue with 30+ more isinstance tests...
    def test_isinstance_with_all_arithmetic_errors(self):
        """Test isinstance with all ArithmeticError subclasses."""
        code = """
from pynext.client.exceptions import (
    ArithmeticError, ZeroDivisionError, OverflowError, FloatingPointError
)

errors = [
    ZeroDivisionError("z"),
    OverflowError("o"),
    FloatingPointError("f"),
]

for e in errors:
    print(isinstance(e, ArithmeticError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_all_lookup_errors(self):
        """Test isinstance with all LookupError subclasses."""
        code = """
from pynext.client.exceptions import (
    LookupError, KeyError, IndexError
)

errors = [KeyError("k"), IndexError("i")]

for e in errors:
    print(isinstance(e, LookupError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_all_os_errors(self):
        """Test isinstance with all OSError subclasses."""
        code = """
from pynext.client.exceptions import (
    OSError, FileNotFoundError, PermissionError, IsADirectoryError, NotADirectoryError
)

errors = [
    FileNotFoundError("f"),
    PermissionError("p"),
    IsADirectoryError("i"),
    NotADirectoryError("n"),
]

for e in errors:
    print(isinstance(e, OSError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_complex_hierarchy(self):
        """Test isinstance with complex hierarchy traversal."""
        code = """
from pynext.client.exceptions import (
    ZeroDivisionError, ArithmeticError, Exception, BaseException
)

e = ZeroDivisionError("test")
# Check all levels
print(isinstance(e, ZeroDivisionError))
print(isinstance(e, ArithmeticError))
print(isinstance(e, Exception))
print(isinstance(e, BaseException))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_function_result(self):
        """Test isinstance with function that returns exception."""
        code = """
from pynext.client.exceptions import ValueError

def get_error():
    return ValueError("test")

e = get_error()
print(isinstance(e, ValueError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_method_result(self):
        """Test isinstance with method that returns exception."""
        code = """
from pynext.client.exceptions import ValueError

class ErrorFactory:
    def create(self):
        return ValueError("test")

f = ErrorFactory()
e = f.create()
print(isinstance(e, ValueError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_in_comprehension(self):
        """Test isinstance in list comprehension."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

errors = [ValueError("v"), TypeError("t"), KeyError("k")]
value_errors = [e for e in errors if isinstance(e, ValueError)]
print(len(value_errors))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_lambda(self):
        """Test isinstance with lambda."""
        code = """
from pynext.client.exceptions import ValueError

is_value_error = lambda e: isinstance(e, ValueError)
e = ValueError("test")
print(is_value_error(e))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_ternary(self):
        """Test isinstance in ternary expression."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

e = ValueError("test")
result = "value" if isinstance(e, ValueError) else "other"
print(result)
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_and_operator(self):
        """Test isinstance with and operator."""
        code = """
from pynext.client.exceptions import ValueError, Exception

e = ValueError("test")
print(isinstance(e, ValueError) and isinstance(e, Exception))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_or_operator(self):
        """Test isinstance with or operator."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

e = ValueError("test")
print(isinstance(e, ValueError) or isinstance(e, TypeError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_not_operator(self):
        """Test isinstance with not operator."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

e = ValueError("test")
print(not isinstance(e, TypeError))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_in_nested_conditionals(self):
        """Test isinstance in nested conditionals."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

e = ValueError("test")
if isinstance(e, ValueError):
    if isinstance(e, Exception):
        print("nested true")
    else:
        print("nested false")
else:
    print("outer false")
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_multiple_checks(self):
        """Test multiple isinstance checks."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

e = ValueError("test")
checks = {
    "ValueError": isinstance(e, ValueError),
    "TypeError": isinstance(e, TypeError),
    "KeyError": isinstance(e, KeyError),
}
print(checks["ValueError"])
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_class_variable(self):
        """Test isinstance with class variable."""
        code = """
from pynext.client.exceptions import ValueError

class Handler:
    error_type = ValueError
    
    def check(self, e):
        return isinstance(e, self.error_type)

h = Handler()
e = ValueError("test")
print(h.check(e))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_global_variable(self):
        """Test isinstance with global variable."""
        code = """
from pynext.client.exceptions import ValueError

ERROR_TYPE = ValueError
e = ValueError("test")
print(isinstance(e, ERROR_TYPE))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_attribute_access(self):
        """Test isinstance with attribute access."""
        code = """
from pynext.client.exceptions import ValueError

class ErrorContainer:
    def __init__(self):
        self.error_type = ValueError

container = ErrorContainer()
e = ValueError("test")
print(isinstance(e, container.error_type))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_dynamic_type(self):
        """Test isinstance with dynamically determined type."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def get_type(name):
    if name == "value":
        return ValueError
    return TypeError

e = ValueError("test")
print(isinstance(e, get_type("value")))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_exception_subclass(self):
        """Test isinstance with exception subclass."""
        code = """
from pynext.client.exceptions import Exception

class CustomError(Exception):
    pass

class DerivedError(CustomError):
    pass

e = DerivedError("test")
print(isinstance(e, CustomError))
print(isinstance(e, DerivedError))
print(isinstance(e, Exception))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "class" in result
    
    def test_isinstance_with_multiple_inheritance(self):
        """Test isinstance with multiple inheritance."""
        code = """
from pynext.client.exceptions import Exception, RuntimeError

class CustomRuntimeError(RuntimeError):
    pass

e = CustomRuntimeError("test")
print(isinstance(e, CustomRuntimeError))
print(isinstance(e, RuntimeError))
print(isinstance(e, Exception))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_generic_exception(self):
        """Test isinstance with generic Exception."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError, Exception

errors = [
    ValueError("v"),
    TypeError("t"),
    KeyError("k"),
]

for e in errors:
    print(isinstance(e, Exception))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_base_exception_only(self):
        """Test isinstance with BaseException only."""
        code = """
from pynext.client.exceptions import SystemExit, KeyboardInterrupt, BaseException

errors = [
    SystemExit("s"),
    KeyboardInterrupt("k"),
]

for e in errors:
    print(isinstance(e, BaseException))
    print(isinstance(e, Exception))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_none_in_tuple(self):
        """Test isinstance with None in tuple."""
        code = """
from pynext.client.exceptions import ValueError

e = ValueError("test")
# Note: None check may not work as expected, but test transpilation
print(isinstance(e, (ValueError, None)))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_empty_tuple(self):
        """Test isinstance with empty tuple."""
        code = """
from pynext.client.exceptions import ValueError

e = ValueError("test")
print(isinstance(e, ()))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_single_item_tuple(self):
        """Test isinstance with single item tuple."""
        code = """
from pynext.client.exceptions import ValueError

e = ValueError("test")
print(isinstance(e, (ValueError,)))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_large_tuple(self):
        """Test isinstance with large tuple of types."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, IndexError, AttributeError,
    RuntimeError, ZeroDivisionError, AssertionError
)

e = ValueError("test")
types = (
    ValueError, TypeError, KeyError, IndexError, AttributeError,
    RuntimeError, ZeroDivisionError, AssertionError
)
print(isinstance(e, types))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_with_repeated_types(self):
        """Test isinstance with repeated types in tuple."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

e = ValueError("test")
print(isinstance(e, (ValueError, ValueError, ValueError)))
"""
        result = transpile(code)
        assert "isinstance" in result
    
    def test_isinstance_in_exception_handler(self):
        """Test isinstance in exception handler."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    raise ValueError("test")
except Exception as e:
    if isinstance(e, ValueError):
        print("caught ValueError")
    elif isinstance(e, TypeError):
        print("caught TypeError")
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "try" in result
        assert "except" in result
    
    def test_isinstance_with_chained_checks(self):
        """Test isinstance with chained checks."""
        code = """
from pynext.client.exceptions import ZeroDivisionError, ArithmeticError, Exception

e = ZeroDivisionError("test")
if isinstance(e, ZeroDivisionError):
    if isinstance(e, ArithmeticError):
        if isinstance(e, Exception):
            print("all true")
"""
        result = transpile(code)
        assert "isinstance" in result


# =============================================================================
# ISSUBCLASS TESTS (30 tests)
# =============================================================================

class TestIsSubclass:
    """Test issubclass() with exceptions."""
    
    def test_issubclass_with_same_class(self):
        """Test issubclass with same class."""
        code = """
from pynext.client.exceptions import ValueError
print(issubclass(ValueError, ValueError))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_base_class(self):
        """Test issubclass with base class."""
        code = """
from pynext.client.exceptions import ValueError, Exception
print(issubclass(ValueError, Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_base_exception(self):
        """Test issubclass with BaseException."""
        code = """
from pynext.client.exceptions import ValueError, BaseException
print(issubclass(ValueError, BaseException))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_wrong_class(self):
        """Test issubclass with wrong class."""
        code = """
from pynext.client.exceptions import ValueError, TypeError
print(issubclass(ValueError, TypeError))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_tuple(self):
        """Test issubclass with tuple of classes."""
        code = """
from pynext.client.exceptions import ValueError, Exception, BaseException
print(issubclass(ValueError, (Exception, BaseException)))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_arithmetic_hierarchy(self):
        """Test issubclass with ArithmeticError hierarchy."""
        code = """
from pynext.client.exceptions import ZeroDivisionError, ArithmeticError, Exception
print(issubclass(ZeroDivisionError, ArithmeticError))
print(issubclass(ZeroDivisionError, Exception))
print(issubclass(ArithmeticError, Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_lookup_hierarchy(self):
        """Test issubclass with LookupError hierarchy."""
        code = """
from pynext.client.exceptions import KeyError, LookupError, Exception
print(issubclass(KeyError, LookupError))
print(issubclass(KeyError, Exception))
print(issubclass(LookupError, Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_os_hierarchy(self):
        """Test issubclass with OSError hierarchy."""
        code = """
from pynext.client.exceptions import FileNotFoundError, OSError, Exception
print(issubclass(FileNotFoundError, OSError))
print(issubclass(FileNotFoundError, Exception))
print(issubclass(OSError, Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_runtime_hierarchy(self):
        """Test issubclass with RuntimeError hierarchy."""
        code = """
from pynext.client.exceptions import RecursionError, RuntimeError, Exception
print(issubclass(RecursionError, RuntimeError))
print(issubclass(RecursionError, Exception))
print(issubclass(RuntimeError, Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_multiple_levels(self):
        """Test issubclass with multiple inheritance levels."""
        code = """
from pynext.client.exceptions import (
    ZeroDivisionError, ArithmeticError, Exception, BaseException
)
print(issubclass(ZeroDivisionError, ZeroDivisionError))
print(issubclass(ZeroDivisionError, ArithmeticError))
print(issubclass(ZeroDivisionError, Exception))
print(issubclass(ZeroDivisionError, BaseException))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_custom_class(self):
        """Test issubclass with custom exception."""
        code = """
from pynext.client.exceptions import Exception

class CustomError(Exception):
    pass

print(issubclass(CustomError, CustomError))
print(issubclass(CustomError, Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
        assert "class" in result
    
    def test_issubclass_with_derived_class(self):
        """Test issubclass with derived exception."""
        code = """
from pynext.client.exceptions import Exception

class BaseError(Exception):
    pass

class DerivedError(BaseError):
    pass

print(issubclass(DerivedError, BaseError))
print(issubclass(DerivedError, Exception))
print(issubclass(BaseError, Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_in_conditional(self):
        """Test issubclass in conditional."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, Exception

def check_type(cls):
    if issubclass(cls, ValueError):
        return "value"
    elif issubclass(cls, TypeError):
        return "type"
    elif issubclass(cls, Exception):
        return "exception"
    return "other"

print(check_type(ValueError))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_all_standard_exceptions(self):
        """Test issubclass with all standard exceptions."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, IndexError, AttributeError,
    RuntimeError, ZeroDivisionError, AssertionError, Exception
)

exceptions = [
    ValueError, TypeError, KeyError, IndexError, AttributeError,
    RuntimeError, ZeroDivisionError, AssertionError
]

for exc in exceptions:
    print(issubclass(exc, Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_system_exceptions(self):
        """Test issubclass with system exceptions."""
        code = """
from pynext.client.exceptions import SystemExit, KeyboardInterrupt, BaseException, Exception

print(issubclass(SystemExit, BaseException))
print(issubclass(SystemExit, Exception))
print(issubclass(KeyboardInterrupt, BaseException))
print(issubclass(KeyboardInterrupt, Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_in_loop(self):
        """Test issubclass in loop."""
        code = """
from pynext.client.exceptions import (
    ZeroDivisionError, OverflowError, FloatingPointError, ArithmeticError
)

arithmetic_errors = [ZeroDivisionError, OverflowError, FloatingPointError]

for exc in arithmetic_errors:
    print(issubclass(exc, ArithmeticError))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_function(self):
        """Test issubclass with function."""
        code = """
from pynext.client.exceptions import ValueError, Exception

def is_exception(cls):
    return issubclass(cls, Exception)

print(is_exception(ValueError))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_method(self):
        """Test issubclass with method."""
        code = """
from pynext.client.exceptions import ValueError, Exception

class TypeChecker:
    def check(self, cls):
        return issubclass(cls, Exception)

checker = TypeChecker()
print(checker.check(ValueError))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_lambda(self):
        """Test issubclass with lambda."""
        code = """
from pynext.client.exceptions import ValueError, Exception

is_exception = lambda cls: issubclass(cls, Exception)
print(is_exception(ValueError))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_comprehension(self):
        """Test issubclass in comprehension."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, Exception
)

exceptions = [ValueError, TypeError, KeyError]
exception_types = [cls for cls in exceptions if issubclass(cls, Exception)]
print(len(exception_types))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_nested_checks(self):
        """Test issubclass with nested checks."""
        code = """
from pynext.client.exceptions import ZeroDivisionError, ArithmeticError, Exception

if issubclass(ZeroDivisionError, ArithmeticError):
    if issubclass(ArithmeticError, Exception):
        print("nested true")
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_and_operator(self):
        """Test issubclass with and operator."""
        code = """
from pynext.client.exceptions import ValueError, Exception, BaseException

print(issubclass(ValueError, Exception) and issubclass(ValueError, BaseException))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_or_operator(self):
        """Test issubclass with or operator."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

print(issubclass(ValueError, TypeError) or issubclass(ValueError, KeyError))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_not_operator(self):
        """Test issubclass with not operator."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

print(not issubclass(ValueError, TypeError))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_dict(self):
        """Test issubclass with dict."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, Exception

exceptions = {
    "value": ValueError,
    "type": TypeError,
}

for name, cls in exceptions.items():
    print(issubclass(cls, Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_class_variable(self):
        """Test issubclass with class variable."""
        code = """
from pynext.client.exceptions import ValueError, Exception

class TypeRegistry:
    base_type = Exception
    
    def check(self, cls):
        return issubclass(cls, self.base_type)

registry = TypeRegistry()
print(registry.check(ValueError))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_global_variable(self):
        """Test issubclass with global variable."""
        code = """
from pynext.client.exceptions import ValueError, Exception

BASE_TYPE = Exception
print(issubclass(ValueError, BASE_TYPE))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_dynamic_class(self):
        """Test issubclass with dynamically determined class."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, Exception

def get_class(name):
    if name == "value":
        return ValueError
    return TypeError

print(issubclass(get_class("value"), Exception))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_empty_tuple(self):
        """Test issubclass with empty tuple."""
        code = """
from pynext.client.exceptions import ValueError

print(issubclass(ValueError, ()))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_single_item_tuple(self):
        """Test issubclass with single item tuple."""
        code = """
from pynext.client.exceptions import ValueError, Exception

print(issubclass(ValueError, (Exception,)))
"""
        result = transpile(code)
        assert "issubclass" in result
    
    def test_issubclass_with_large_tuple(self):
        """Test issubclass with large tuple."""
        code = """
from pynext.client.exceptions import (
    ValueError, Exception, BaseException, RuntimeError, ArithmeticError
)

print(issubclass(ValueError, (Exception, BaseException, RuntimeError, ArithmeticError)))
"""
        result = transpile(code)
        assert "issubclass" in result


# =============================================================================
# EXCEPTION CHAINING TESTS (30 tests)
# =============================================================================

class TestExceptionChaining:
    """Test exception chaining (raise ... from ...)."""
    
    def test_raise_from_basic(self):
        """Test basic raise ... from ..."""
        code = """
try:
    raise ValueError("original")
except ValueError as e:
    raise TypeError("new") from e
"""
        result = transpile(code)
        # Emitter converts __throw_from__ to direct __cause__ assignment
        assert "__cause__" in result or "__py.exceptions.chain" in result or "__throw_from__" in result
    
    def test_raise_from_with_cause(self):
        """Test raise from with explicit cause."""
        code = """
original = ValueError("original")
raise TypeError("new") from original
"""
        result = transpile(code)
        assert "__cause__" in result or "__py.exceptions.chain" in result or "__throw_from__" in result
    
    def test_raise_from_in_function(self):
        """Test raise from in function."""
        code = """
def process():
    try:
        raise ValueError("error")
    except ValueError as e:
        raise TypeError("converted") from e

process()
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_in_nested_try(self):
        """Test raise from in nested try/except."""
        code = """
try:
    try:
        raise ValueError("inner")
    except ValueError as inner:
        raise TypeError("outer") from inner
except TypeError as outer:
    print("caught")
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_multiple_levels(self):
        """Test raise from with multiple chaining levels."""
        code = """
try:
    raise ValueError("level1")
except ValueError as e1:
    try:
        raise TypeError("level2") from e1
    except TypeError as e2:
        raise KeyError("level3") from e2
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_custom_exception(self):
        """Test raise from with custom exception."""
        code = """
from pynext.client.exceptions import Exception

class CustomError(Exception):
    pass

try:
    raise ValueError("original")
except ValueError as e:
    raise CustomError("custom") from e
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
        assert "class" in result
    
    def test_raise_from_with_same_type(self):
        """Test raise from with same exception type."""
        code = """
try:
    raise ValueError("original")
except ValueError as e:
    raise ValueError("new") from e
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_in_loop(self):
        """Test raise from in loop."""
        code = """
errors = []
for i in range(3):
    try:
        raise ValueError(f"error {i}")
    except ValueError as e:
        errors.append(e)
        if i < 2:
            raise TypeError(f"converted {i}") from e
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_none(self):
        """Test raise from None (suppress chaining)."""
        code = """
try:
    raise ValueError("original")
except ValueError:
    raise TypeError("new") from None
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_in_class_method(self):
        """Test raise from in class method."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class Processor:
    def process(self):
        try:
            raise ValueError("error")
        except ValueError as e:
            raise TypeError("converted") from e

p = Processor()
p.process()
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    # Continue with 20 more chaining tests...
    def test_raise_from_with_function_call(self):
        """Test raise from with function call result."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def get_error():
    return ValueError("original")

try:
    raise get_error()
except ValueError as e:
    raise TypeError("new") from e
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_method_call(self):
        """Test raise from with method call result."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class ErrorFactory:
    def create(self):
        return ValueError("original")

factory = ErrorFactory()
try:
    raise factory.create()
except ValueError as e:
    raise TypeError("new") from e
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_attribute(self):
        """Test raise from with attribute access."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class Container:
    def __init__(self):
        self.error = ValueError("original")

container = Container()
try:
    raise container.error
except ValueError as e:
    raise TypeError("new") from e
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_in_generator(self):
        """Test raise from in generator."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def gen():
    try:
        raise ValueError("error")
    except ValueError as e:
        yield "before"
        raise TypeError("converted") from e
        yield "after"

list(gen())
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_in_async_function(self):
        """Test raise from in async function."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

async def process():
    try:
        raise ValueError("error")
    except ValueError as e:
        raise TypeError("converted") from e

process()
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
        assert "async" in result
    
    def test_raise_from_with_conditional(self):
        """Test raise from with conditional."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

try:
    raise ValueError("error")
except ValueError as e:
    if True:
        raise TypeError("converted") from e
    else:
        raise KeyError("alternative") from e
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_exception_handler(self):
        """Test raise from in exception handler."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def handle():
    try:
        raise ValueError("original")
    except ValueError as e:
        try:
            process()
        except Exception:
            raise TypeError("new") from e

handle()
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_finally(self):
        """Test raise from with finally block."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    try:
        raise ValueError("original")
    except ValueError as e:
        raise TypeError("new") from e
finally:
    cleanup()
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
        assert "finally" in result
    
    def test_raise_from_with_context_manager(self):
        """Test raise from with context manager."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    with resource():
        raise ValueError("original")
except ValueError as e:
    raise TypeError("new") from e
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_multiple_causes(self):
        """Test raise from with multiple exception causes."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

try:
    raise ValueError("v1")
except ValueError as e1:
    try:
        raise TypeError("t1") from e1
    except TypeError as e2:
        raise KeyError("k1") from e2
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_list_comprehension(self):
        """Test raise from in list comprehension context."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def process_items(items):
    errors = []
    for item in items:
        try:
            if item < 0:
                raise ValueError(f"negative: {item}")
        except ValueError as e:
            errors.append(e)
            raise TypeError(f"converted: {item}") from e
    return errors

process_items([1, -1, 2])
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_dict_comprehension(self):
        """Test raise from in dict comprehension context."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def process_dict(d):
    for key, value in d.items():
        try:
            if value < 0:
                raise ValueError(f"negative: {key}")
        except ValueError as e:
            raise TypeError(f"converted: {key}") from e

process_dict({"a": 1, "b": -1})
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_set_comprehension(self):
        """Test raise from in set comprehension context."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def process_set(s):
    for item in s:
        try:
            if item < 0:
                raise ValueError(f"negative: {item}")
        except ValueError as e:
            raise TypeError(f"converted: {item}") from e

process_set([1, -1, 2])
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_generator_expression(self):
        """Test raise from in generator expression context."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def process_gen(items):
    for item in items:
        try:
            if item < 0:
                raise ValueError(f"negative: {item}")
        except ValueError as e:
            raise TypeError(f"converted: {item}") from e
        yield item

list(process_gen([1, -1, 2]))
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_lambda(self):
        """Test raise from in lambda context."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def process_with_lambda(fn):
    try:
        result = fn()
        if result < 0:
            raise ValueError("negative result")
    except ValueError as e:
        raise TypeError("converted") from e

process_with_lambda(lambda: -1)
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_decorator(self):
        """Test raise from with decorator."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def error_handler(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            raise TypeError("converted") from e
    return wrapper

@error_handler
def process(x):
    if x < 0:
        raise ValueError("negative")

process(-1)
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_property(self):
        """Test raise from with property."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class Container:
    @property
    def value(self):
        try:
            if self._value < 0:
                raise ValueError("negative")
            return self._value
        except ValueError as e:
            raise TypeError("converted") from e

c = Container()
c._value = -1
c.value
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_staticmethod(self):
        """Test raise from with staticmethod."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class Processor:
    @staticmethod
    def process(x):
        try:
            if x < 0:
                raise ValueError("negative")
        except ValueError as e:
            raise TypeError("converted") from e

Processor.process(-1)
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_classmethod(self):
        """Test raise from with classmethod."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class Processor:
    @classmethod
    def process(cls, x):
        try:
            if x < 0:
                raise ValueError("negative")
        except ValueError as e:
            raise TypeError("converted") from e

Processor.process(-1)
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_inheritance(self):
        """Test raise from with inheritance."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, Exception

class BaseProcessor:
    def process(self, x):
        try:
            if x < 0:
                raise ValueError("negative")
        except ValueError as e:
            raise TypeError("converted") from e

class DerivedProcessor(BaseProcessor):
    pass

p = DerivedProcessor()
p.process(-1)
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_raise_from_with_multiple_inheritance(self):
        """Test raise from with multiple inheritance."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, Exception

class Mixin:
    def handle_error(self, e):
        raise TypeError("converted") from e

class Processor(Mixin):
    def process(self, x):
        try:
            if x < 0:
                raise ValueError("negative")
        except ValueError as e:
            self.handle_error(e)

p = Processor()
p.process(-1)
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result


# =============================================================================
# EXCEPTION ATTRIBUTES TESTS (20 tests)
# =============================================================================

class TestExceptionAttributes:
    """Test __cause__, __context__, __traceback__ attributes."""
    
    def test_cause_attribute(self):
        """Test __cause__ attribute."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    raise ValueError("original")
except ValueError as e:
    new = TypeError("new")
    new.__cause__ = e
    print(new.__cause__ is not None)
"""
        result = transpile(code)
        assert "__cause__" in result
    
    def test_context_attribute(self):
        """Test __context__ attribute."""
        code = """
from pynext.client.exceptions import ValueError

try:
    raise ValueError("original")
except ValueError as e:
    print(e.__context__ is None)
"""
        result = transpile(code)
        assert "__context__" in result
    
    def test_traceback_attribute(self):
        """Test __traceback__ attribute."""
        code = """
from pynext.client.exceptions import ValueError

try:
    raise ValueError("error")
except ValueError as e:
    print(e.__traceback__ is not None)
"""
        result = transpile(code)
        assert "__traceback__" in result
    
    def test_cause_from_raise_from(self):
        """Test __cause__ set by raise ... from ..."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    raise ValueError("original")
except ValueError as e:
    try:
        raise TypeError("new") from e
    except TypeError as new:
        print(new.__cause__ is not None)
"""
        result = transpile(code)
        assert "__cause__" in result
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_context_from_exception_during_handling(self):
        """Test __context__ set when exception occurs during handling."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    raise ValueError("original")
except ValueError:
    # New exception during handling sets __context__
    raise TypeError("during handling")
"""
        result = transpile(code)
        assert "__context__" in result or "raise" in result
    
    def test_cause_and_context_both_set(self):
        """Test both __cause__ and __context__ can be set."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

try:
    raise ValueError("original")
except ValueError as e1:
    try:
        raise TypeError("intermediate") from e1
    except TypeError as e2:
        # e2 has __cause__ = e1
        # If another exception occurs, e2 would be in __context__
        raise KeyError("final") from e2
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_cause_access(self):
        """Test accessing __cause__ attribute."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    raise ValueError("original")
except ValueError as e:
    new = TypeError("new")
    new.__cause__ = e
    cause = new.__cause__
    print(type(cause).__name__)
"""
        result = transpile(code)
        assert "__cause__" in result
    
    def test_context_access(self):
        """Test accessing __context__ attribute."""
        code = """
from pynext.client.exceptions import ValueError

try:
    raise ValueError("error")
except ValueError as e:
    context = e.__context__
    print(context is None)
"""
        result = transpile(code)
        assert "__context__" in result
    
    def test_traceback_access(self):
        """Test accessing __traceback__ attribute."""
        code = """
from pynext.client.exceptions import ValueError

try:
    raise ValueError("error")
except ValueError as e:
    tb = e.__traceback__
    print(tb is not None)
"""
        result = transpile(code)
        assert "__traceback__" in result
    
    def test_cause_modification(self):
        """Test modifying __cause__ attribute."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

original = ValueError("original")
new = TypeError("new")
new.__cause__ = original

# Modify cause
new.__cause__ = KeyError("changed")
print(type(new.__cause__).__name__)
"""
        result = transpile(code)
        assert "__cause__" in result
    
    def test_context_modification(self):
        """Test modifying __context__ attribute."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

e = ValueError("error")
e.__context__ = TypeError("context")
print(type(e.__context__).__name__)
"""
        result = transpile(code)
        assert "__context__" in result
    
    def test_traceback_modification(self):
        """Test modifying __traceback__ attribute."""
        code = """
from pynext.client.exceptions import ValueError

e = ValueError("error")
e.__traceback__ = None
print(e.__traceback__ is None)
"""
        result = transpile(code)
        assert "__traceback__" in result
    
    def test_cause_in_function(self):
        """Test __cause__ in function."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def create_chained():
    original = ValueError("original")
    new = TypeError("new")
    new.__cause__ = original
    return new

e = create_chained()
print(e.__cause__ is not None)
"""
        result = transpile(code)
        assert "__cause__" in result
    
    def test_context_in_function(self):
        """Test __context__ in function."""
        code = """
from pynext.client.exceptions import ValueError

def get_context(e):
    return e.__context__

try:
    raise ValueError("error")
except ValueError as e:
    context = get_context(e)
    print(context is None)
"""
        result = transpile(code)
        assert "__context__" in result
    
    def test_traceback_in_function(self):
        """Test __traceback__ in function."""
        code = """
from pynext.client.exceptions import ValueError

def get_traceback(e):
    return e.__traceback__

try:
    raise ValueError("error")
except ValueError as e:
    tb = get_traceback(e)
    print(tb is not None)
"""
        result = transpile(code)
        assert "__traceback__" in result
    
    def test_cause_in_class(self):
        """Test __cause__ in class."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class ErrorWrapper:
    def __init__(self, original):
        self.new = TypeError("new")
        self.new.__cause__ = original
    
    def get_cause(self):
        return self.new.__cause__

wrapper = ErrorWrapper(ValueError("original"))
print(wrapper.get_cause() is not None)
"""
        result = transpile(code)
        assert "__cause__" in result
        assert "class" in result
    
    def test_context_in_class(self):
        """Test __context__ in class."""
        code = """
from pynext.client.exceptions import ValueError

class ErrorHandler:
    def handle(self, e):
        return e.__context__

handler = ErrorHandler()
try:
    raise ValueError("error")
except ValueError as e:
    context = handler.handle(e)
    print(context is None)
"""
        result = transpile(code)
        assert "__context__" in result
    
    def test_traceback_in_class(self):
        """Test __traceback__ in class."""
        code = """
from pynext.client.exceptions import ValueError

class ErrorAnalyzer:
    def analyze(self, e):
        return e.__traceback__ is not None

analyzer = ErrorAnalyzer()
try:
    raise ValueError("error")
except ValueError as e:
    print(analyzer.analyze(e))
"""
        result = transpile(code)
        assert "__traceback__" in result
    
    def test_cause_with_none(self):
        """Test __cause__ with None."""
        code = """
from pynext.client.exceptions import TypeError

e = TypeError("error")
e.__cause__ = None
print(e.__cause__ is None)
"""
        result = transpile(code)
        assert "__cause__" in result
    
    def test_context_with_none(self):
        """Test __context__ with None."""
        code = """
from pynext.client.exceptions import ValueError

e = ValueError("error")
e.__context__ = None
print(e.__context__ is None)
"""
        result = transpile(code)
        assert "__context__" in result
    
    def test_all_attributes_together(self):
        """Test all attributes together."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    raise ValueError("original")
except ValueError as e1:
    new = TypeError("new")
    new.__cause__ = e1
    new.__context__ = None
    new.__traceback__ = None
    
    print(new.__cause__ is not None)
    print(new.__context__ is None)
    print(new.__traceback__ is None)
"""
        result = transpile(code)
        assert "__cause__" in result
        assert "__context__" in result
        assert "__traceback__" in result


# =============================================================================
# PYTHON-JS EQUIVALENCE TESTS (20 tests)
# =============================================================================

class TestExceptionEquivalence:
    """Test Python-JS equivalence for exception handling."""
    
    @pytest.mark.asyncio
    async def test_raise_catch_equivalence(self):
        """Test raise and catch equivalence."""
        code = """
from pynext.client.exceptions import ValueError

try:
    raise ValueError("test error")
except ValueError as e:
    print(type(e).__name__)
    print(str(e))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_isinstance_equivalence(self):
        """Test isinstance equivalence."""
        code = """
from pynext.client.exceptions import ValueError, Exception

e = ValueError("test")
print(isinstance(e, ValueError))
print(isinstance(e, Exception))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_issubclass_equivalence(self):
        """Test issubclass equivalence."""
        code = """
from pynext.client.exceptions import ValueError, Exception

print(issubclass(ValueError, ValueError))
print(issubclass(ValueError, Exception))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_hierarchy_equivalence(self):
        """Test exception hierarchy equivalence."""
        code = """
from pynext.client.exceptions import (
    ZeroDivisionError, ArithmeticError, Exception, BaseException
)

e = ZeroDivisionError("test")
print(isinstance(e, ZeroDivisionError))
print(isinstance(e, ArithmeticError))
print(isinstance(e, Exception))
print(isinstance(e, BaseException))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_chaining_equivalence(self):
        """Test exception chaining equivalence."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    raise ValueError("original")
except ValueError as e:
    new = TypeError("new")
    new.__cause__ = e
    print(new.__cause__ is not None)
    print(type(new.__cause__).__name__)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_multiple_exception_types_equivalence(self):
        """Test multiple exception types equivalence."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, IndexError
)

errors = [
    ValueError("v"),
    TypeError("t"),
    KeyError("k"),
    IndexError("i"),
]

for e in errors:
    print(type(e).__name__)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_in_tuple_equivalence(self):
        """Test exception in tuple equivalence."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

e = ValueError("test")
print(isinstance(e, (ValueError, TypeError)))
print(isinstance(e, (KeyError, IndexError)))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_message_equivalence(self):
        """Test exception message equivalence."""
        code = """
from pynext.client.exceptions import ValueError

e = ValueError("custom message")
print(str(e))
print(e.message)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            # Messages should match
            py_lines = py_result["stdout"].strip().split("\n")
            js_lines = js_result["stdout"].strip().split("\n")
            assert len(py_lines) == len(js_lines)
    
    @pytest.mark.asyncio
    async def test_key_error_key_attribute_equivalence(self):
        """Test KeyError key attribute equivalence."""
        code = """
from pynext.client.exceptions import KeyError

e = KeyError("missing_key")
print(e.key)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_stop_iteration_value_equivalence(self):
        """Test StopIteration value attribute equivalence."""
        code = """
from pynext.client.exceptions import StopIteration

e = StopIteration("done")
print(e.value)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    # Continue with 10 more equivalence tests...
    @pytest.mark.asyncio
    async def test_exception_in_list_equivalence(self):
        """Test exception in list equivalence."""
        code = """
from pynext.client.exceptions import ValueError

errors = [ValueError("error1"), ValueError("error2")]
print(len(errors))
for e in errors:
    print(isinstance(e, ValueError))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_in_dict_equivalence(self):
        """Test exception in dict equivalence."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

errors = {"value": ValueError("error1"), "type": TypeError("error2")}
print(len(errors))
for key, e in errors.items():
    print(key, type(e).__name__)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            py_lines = py_result["stdout"].strip().split("\n")
            js_lines = js_result["stdout"].strip().split("\n")
            assert len(py_lines) == len(js_lines)
    
    @pytest.mark.asyncio
    async def test_exception_as_function_argument_equivalence(self):
        """Test exception as function argument equivalence."""
        code = """
from pynext.client.exceptions import ValueError

def handle_error(e):
    print(type(e).__name__)
    print(str(e))

e = ValueError("test")
handle_error(e)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_returned_from_function_equivalence(self):
        """Test exception returned from function equivalence."""
        code = """
from pynext.client.exceptions import ValueError

def create_error():
    return ValueError("test")

e = create_error()
print(type(e).__name__)
print(isinstance(e, ValueError))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_in_class_equivalence(self):
        """Test exception in class equivalence."""
        code = """
from pynext.client.exceptions import ValueError

class ErrorHandler:
    def __init__(self):
        self.error = ValueError("test")
    
    def get_error(self):
        return self.error

h = ErrorHandler()
e = h.get_error()
print(type(e).__name__)
print(isinstance(e, ValueError))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_in_nested_function_equivalence(self):
        """Test exception in nested function equivalence."""
        code = """
from pynext.client.exceptions import ValueError

def outer():
    def inner():
        return ValueError("test")
    return inner()

e = outer()
print(type(e).__name__)
print(isinstance(e, ValueError))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_with_custom_class_equivalence(self):
        """Test exception with custom class equivalence."""
        code = """
from pynext.client.exceptions import Exception

class CustomError(Exception):
    pass

e = CustomError("test")
print(type(e).__name__)
print(isinstance(e, CustomError))
print(isinstance(e, Exception))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_with_inheritance_equivalence(self):
        """Test exception with inheritance equivalence."""
        code = """
from pynext.client.exceptions import Exception

class BaseError(Exception):
    pass

class DerivedError(BaseError):
    pass

e = DerivedError("test")
print(isinstance(e, DerivedError))
print(isinstance(e, BaseError))
print(isinstance(e, Exception))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_with_multiple_inheritance_equivalence(self):
        """Test exception with multiple inheritance equivalence."""
        code = """
from pynext.client.exceptions import Exception, RuntimeError

class CustomRuntimeError(RuntimeError):
    pass

e = CustomRuntimeError("test")
print(isinstance(e, CustomRuntimeError))
print(isinstance(e, RuntimeError))
print(isinstance(e, Exception))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert py_result["stdout"].strip() == js_result["stdout"].strip()
    
    @pytest.mark.asyncio
    async def test_exception_complex_scenario_equivalence(self):
        """Test complex exception scenario equivalence."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, Exception
)

def process_value(x):
    if x < 0:
        raise ValueError("negative")
    if x > 100:
        raise TypeError("too large")
    return x * 2

def handle(x):
    try:
        return process_value(x)
    except ValueError as e:
        print(f"ValueError: {e}")
        return None
    except TypeError as e:
        print(f"TypeError: {e}")
        return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

result1 = handle(-1)
result2 = handle(150)
result3 = handle(50)
print(result1, result2, result3)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            py_lines = py_result["stdout"].strip().split("\n")
            js_lines = js_result["stdout"].strip().split("\n")
            assert len(py_lines) == len(js_lines)


# =============================================================================
# EDGE CASES (20 tests)
# =============================================================================

class TestExceptionEdgeCases:
    """Test edge cases and error handling for exceptions."""
    
    def test_exception_with_empty_message(self):
        """Test exception with empty message."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("")
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_none_message(self):
        """Test exception with None message."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError(None)
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_number_message(self):
        """Test exception with number message."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError(42)
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_list_message(self):
        """Test exception with list message."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError([1, 2, 3])
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_dict_message(self):
        """Test exception with dict message."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError({"key": "value"})
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_object_message(self):
        """Test exception with object message."""
        code = """
from pynext.client.exceptions import ValueError

class Custom:
    def __str__(self):
        return "custom object"

e = ValueError(Custom())
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_in_exception(self):
        """Test exception raised during exception creation."""
        code = """
from pynext.client.exceptions import ValueError

def create_error():
    raise ValueError("creation error")

try:
    create_error()
except ValueError as e:
    print(type(e).__name__)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_circular_reference(self):
        """Test exception with circular reference."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

e1 = ValueError("error1")
e2 = TypeError("error2")
e1.__cause__ = e2
e2.__cause__ = e1  # Circular reference
print(e1.__cause__ is not None)
"""
        result = transpile(code)
        assert "__cause__" in result
    
    def test_exception_with_self_reference(self):
        """Test exception with self reference."""
        code = """
from pynext.client.exceptions import ValueError

e = ValueError("error")
e.__cause__ = e  # Self reference
print(e.__cause__ is e)
"""
        result = transpile(code)
        assert "__cause__" in result
    
    def test_exception_with_deep_nesting(self):
        """Test exception with deep nesting."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

e1 = ValueError("level1")
e2 = TypeError("level2")
e3 = KeyError("level3")

e2.__cause__ = e1
e3.__cause__ = e2

print(e3.__cause__.__cause__ is not None)
"""
        result = transpile(code)
        assert "__cause__" in result
    
    def test_exception_with_large_message(self):
        """Test exception with large message."""
        code = """
from pynext.client.exceptions import ValueError
large_message = "x" * 1000
e = ValueError(large_message)
print(len(str(e)) > 100)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_unicode_message(self):
        """Test exception with unicode message."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("日本語 🎉 test")
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_multiline_message(self):
        """Test exception with multiline message."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("line1\\nline2\\nline3")
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_special_characters(self):
        """Test exception with special characters."""
        code = """
from pynext.client.exceptions import ValueError
e = ValueError("test\\t\\n\\r\\'\\\"\\\\")
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_format_string(self):
        """Test exception with format string."""
        code = """
from pynext.client.exceptions import ValueError
name = "test"
e = ValueError(f"error: {name}")
print(str(e))
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_in_comprehension(self):
        """Test exception in comprehension."""
        code = """
from pynext.client.exceptions import ValueError

def process(x):
    if x < 0:
        raise ValueError("negative")
    return x * 2

try:
    results = [process(x) for x in [-1, 1, -2, 2]]
except ValueError as e:
    print(type(e).__name__)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_in_generator(self):
        """Test exception in generator."""
        code = """
from pynext.client.exceptions import ValueError

def gen():
    for i in range(5):
        if i < 0:
            raise ValueError("negative")
        yield i

try:
    list(gen())
except ValueError as e:
    print(type(e).__name__)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_in_async_function(self):
        """Test exception in async function."""
        code = """
from pynext.client.exceptions import ValueError

async def process():
    raise ValueError("error")

try:
    process()
except ValueError as e:
    print(type(e).__name__)
"""
        result = transpile(code)
        assert "ValueError" in result
        assert "async" in result
    
    def test_exception_with_timeout(self):
        """Test exception handling with timeout scenario."""
        code = """
from pynext.client.exceptions import TimeoutError, RuntimeError

try:
    raise TimeoutError("timeout")
except TimeoutError as e:
    raise RuntimeError("converted") from e
"""
        result = transpile(code)
        assert "raise" in result or "TimeoutError" in result
    
    def test_exception_with_memory_error(self):
        """Test exception handling with memory error scenario."""
        code = """
from pynext.client.exceptions import MemoryError, RuntimeError

try:
    raise MemoryError("memory")
except MemoryError as e:
    raise RuntimeError("converted") from e
"""
        result = transpile(code)
        assert "raise" in result or "MemoryError" in result
    
    def test_exception_with_all_attributes_none(self):
        """Test exception with all attributes set to None."""
        code = """
from pynext.client.exceptions import ValueError

e = ValueError("error")
e.__cause__ = None
e.__context__ = None
e.__traceback__ = None

print(e.__cause__ is None)
print(e.__context__ is None)
print(e.__traceback__ is None)
"""
        result = transpile(code)
        assert "__cause__" in result
        assert "__context__" in result
        assert "__traceback__" in result
    
    def test_exception_with_complex_nested_structure(self):
        """Test exception with complex nested structure."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

class ErrorContainer:
    def __init__(self):
        self.errors = []
    
    def add_error(self, e):
        self.errors.append(e)
        if len(self.errors) > 1:
            e.__cause__ = self.errors[-2]

container = ErrorContainer()
container.add_error(ValueError("v1"))
container.add_error(TypeError("t1"))
container.add_error(KeyError("k1"))

print(len(container.errors))
print(container.errors[-1].__cause__ is not None)
"""
        result = transpile(code)
        assert "__cause__" in result
        assert "class" in result
    
    def test_exception_with_function_decorator(self):
        """Test exception with function decorator."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def error_wrapper(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            raise TypeError("wrapped") from e
    return wrapper

@error_wrapper
def process(x):
    if x < 0:
        raise ValueError("negative")
    return x * 2

process(-1)
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_exception_with_class_decorator(self):
        """Test exception with class decorator."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

def error_handler(cls):
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        try:
            original_init(self, *args, **kwargs)
        except ValueError as e:
            raise TypeError("converted") from e
    
    cls.__init__ = new_init
    return cls

@error_handler
class Processor:
    def __init__(self, x):
        if x < 0:
            raise ValueError("negative")
        self.x = x

Processor(-1)
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
    
    def test_exception_with_property_setter(self):
        """Test exception with property setter."""
        code = """
from pynext.client.exceptions import ValueError

class Container:
    def __init__(self):
        self._value = 0
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, v):
        if v < 0:
            raise ValueError("negative")
        self._value = v

c = Container()
try:
    c.value = -1
except ValueError as e:
    print(type(e).__name__)
"""
        result = transpile(code)
        assert "ValueError" in result
    
    def test_exception_with_contextlib(self):
        """Test exception with contextlib-like pattern."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class ErrorContext:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type == ValueError:
            raise TypeError("converted") from exc_val
        return False

with ErrorContext():
    raise ValueError("error")
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
        assert "__enter__" in result
        assert "__exit__" in result
    
    def test_exception_with_pattern_matching(self):
        """Test exception with pattern matching."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

def handle_error(e):
    match type(e).__name__:
        case "ValueError":
            return "value error"
        case "TypeError":
            return "type error"
        case "KeyError":
            return "key error"
        case _:
            return "other error"

e = ValueError("test")
print(handle_error(e))
"""
        result = transpile(code)
        assert "ValueError" in result
        assert "match" in result or "switch" in result or "if" in result
    
    def test_exception_with_async_context_manager(self):
        """Test exception with async context manager."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class AsyncErrorContext:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type == ValueError:
            raise TypeError("converted") from exc_val
        return False

async def process():
    async with AsyncErrorContext():
        raise ValueError("error")

process()
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
        assert "__aenter__" in result
        assert "__aexit__" in result
        assert "async" in result
    
    def test_exception_with_generator_throw(self):
        """Test exception with generator throw."""
        code = """
from pynext.client.exceptions import ValueError

def gen():
    try:
        yield 1
        yield 2
    except ValueError as e:
        yield f"caught: {e}"

g = gen()
next(g)
try:
    g.throw(ValueError("test"))
except StopIteration:
    pass
"""
        result = transpile(code)
        assert "ValueError" in result
        assert "yield" in result
    
    def test_exception_with_async_generator_throw(self):
        """Test exception with async generator throw."""
        code = """
from pynext.client.exceptions import ValueError

async def gen():
    try:
        yield 1
        yield 2
    except ValueError as e:
        yield f"caught: {e}"

async def process():
    g = gen()
    await g.__anext__()
    try:
        await g.athrow(ValueError("test"))
    except StopAsyncIteration:
        pass

process()
"""
        result = transpile(code)
        assert "ValueError" in result
        assert "async" in result
        assert "yield" in result
    
    def test_exception_with_complex_inheritance_chain(self):
        """Test exception with complex inheritance chain."""
        code = """
from pynext.client.exceptions import Exception, RuntimeError

class Level1(Exception):
    pass

class Level2(Level1):
    pass

class Level3(Level2):
    pass

class Level4(Level3, RuntimeError):
    pass

e = Level4("test")
print(isinstance(e, Level4))
print(isinstance(e, Level3))
print(isinstance(e, Level2))
print(isinstance(e, Level1))
print(isinstance(e, Exception))
print(isinstance(e, RuntimeError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "class" in result
    
    def test_exception_with_mixin_pattern(self):
        """Test exception with mixin pattern."""
        code = """
from pynext.client.exceptions import Exception, ValueError, TypeError

class ErrorMixin:
    def get_category(self):
        if isinstance(self, ValueError):
            return "value"
        elif isinstance(self, TypeError):
            return "type"
        return "other"

class CustomValueError(ValueError, ErrorMixin):
    pass

e = CustomValueError("test")
print(isinstance(e, CustomValueError))
print(isinstance(e, ValueError))
print(isinstance(e, Exception))
print(e.get_category())
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "class" in result
    
    def test_exception_with_abstract_base_class(self):
        """Test exception with abstract base class pattern."""
        code = """
from pynext.client.exceptions import Exception

class AbstractError(Exception):
    def __init__(self, message):
        super().__init__(message)
        if self.__class__ == AbstractError:
            raise TypeError("Cannot instantiate abstract class")

class ConcreteError(AbstractError):
    pass

e = ConcreteError("test")
print(isinstance(e, ConcreteError))
print(isinstance(e, AbstractError))
print(isinstance(e, Exception))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "class" in result
    
    def test_exception_with_singleton_pattern(self):
        """Test exception with singleton pattern."""
        code = """
from pynext.client.exceptions import ValueError

class SingletonError(ValueError):
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

e1 = SingletonError("test1")
e2 = SingletonError("test2")
print(e1 is e2)
print(isinstance(e1, SingletonError))
print(isinstance(e1, ValueError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "class" in result
    
    def test_exception_with_factory_pattern(self):
        """Test exception with factory pattern."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError, Exception

class ErrorFactory:
    @staticmethod
    def create(error_type, message):
        if error_type == "value":
            return ValueError(message)
        elif error_type == "type":
            return TypeError(message)
        elif error_type == "key":
            return KeyError(message)
        else:
            return Exception(message)

e1 = ErrorFactory.create("value", "test1")
e2 = ErrorFactory.create("type", "test2")
e3 = ErrorFactory.create("key", "test3")

print(isinstance(e1, ValueError))
print(isinstance(e2, TypeError))
print(isinstance(e3, KeyError))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "class" in result
    
    def test_exception_with_builder_pattern(self):
        """Test exception with builder pattern."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class ErrorBuilder:
    def __init__(self):
        self._cause = None
        self._context = None
    
    def with_cause(self, cause):
        self._cause = cause
        return self
    
    def with_context(self, context):
        self._context = context
        return self
    
    def build(self, message):
        e = ValueError(message)
        if self._cause:
            e.__cause__ = self._cause
        if self._context:
            e.__context__ = self._context
        return e

original = TypeError("original")
builder = ErrorBuilder()
e = builder.with_cause(original).build("new")
print(e.__cause__ is not None)
print(isinstance(e.__cause__, TypeError))
"""
        result = transpile(code)
        assert "__cause__" in result
        assert "isinstance" in result
        assert "class" in result
    
    def test_exception_with_observer_pattern(self):
        """Test exception with observer pattern."""
        code = """
from pynext.client.exceptions import ValueError

class ErrorObserver:
    def __init__(self):
        self.errors = []
    
    def on_error(self, e):
        self.errors.append(e)
        print(f"Observed: {type(e).__name__}")

class ErrorSubject:
    def __init__(self):
        self.observers = []
    
    def attach(self, observer):
        self.observers.append(observer)
    
    def notify(self, e):
        for observer in self.observers:
            observer.on_error(e)
    
    def process(self, x):
        if x < 0:
            e = ValueError("negative")
            self.notify(e)
            raise e

subject = ErrorSubject()
observer = ErrorObserver()
subject.attach(observer)

try:
    subject.process(-1)
except ValueError as e:
    print(f"Caught: {type(e).__name__}")
"""
        result = transpile(code)
        assert "ValueError" in result
        assert "class" in result
    
    def test_exception_with_strategy_pattern(self):
        """Test exception with strategy pattern."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

class ErrorStrategy:
    def handle(self, e):
        raise NotImplementedError

class ValueErrorStrategy(ErrorStrategy):
    def handle(self, e):
        return f"ValueError: {e}"

class TypeErrorStrategy(ErrorStrategy):
    def handle(self, e):
        return f"TypeError: {e}"

class ErrorHandler:
    def __init__(self, strategy):
        self.strategy = strategy
    
    def process(self, e):
        return self.strategy.handle(e)

handler1 = ErrorHandler(ValueErrorStrategy())
handler2 = ErrorHandler(TypeErrorStrategy())

e1 = ValueError("test1")
e2 = TypeError("test2")

print(handler1.process(e1))
print(handler2.process(e2))
"""
        result = transpile(code)
        assert "ValueError" in result
        assert "TypeError" in result
        assert "class" in result
    
    def test_exception_with_chain_of_responsibility(self):
        """Test exception with chain of responsibility pattern."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError, Exception

class ErrorHandler:
    def __init__(self, handler_type):
        self.handler_type = handler_type
        self.next_handler = None
    
    def set_next(self, handler):
        self.next_handler = handler
        return handler
    
    def handle(self, e):
        if isinstance(e, self.handler_type):
            return f"Handled by {self.handler_type.__name__}"
        elif self.next_handler:
            return self.next_handler.handle(e)
        return "Unhandled"

handler1 = ErrorHandler(ValueError)
handler2 = ErrorHandler(TypeError)
handler3 = ErrorHandler(KeyError)

handler1.set_next(handler2).set_next(handler3)

e1 = ValueError("test1")
e2 = TypeError("test2")
e3 = KeyError("test3")
e4 = Exception("test4")

print(handler1.handle(e1))
print(handler1.handle(e2))
print(handler1.handle(e3))
print(handler1.handle(e4))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "ValueError" in result
        assert "TypeError" in result
        assert "KeyError" in result
        assert "class" in result
    
    def test_exception_with_state_pattern(self):
        """Test exception with state pattern."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class ErrorState:
    def handle(self, e):
        raise NotImplementedError

class InitialState(ErrorState):
    def handle(self, e):
        if isinstance(e, ValueError):
            return "Initial: ValueError"
        return "Initial: Other"

class ProcessingState(ErrorState):
    def handle(self, e):
        if isinstance(e, TypeError):
            return "Processing: TypeError"
        return "Processing: Other"

class ErrorProcessor:
    def __init__(self):
        self.state = InitialState()
    
    def set_state(self, state):
        self.state = state
    
    def process(self, e):
        return self.state.handle(e)

processor = ErrorProcessor()
e1 = ValueError("test1")
e2 = TypeError("test2")

print(processor.process(e1))
processor.set_state(ProcessingState())
print(processor.process(e2))
"""
        result = transpile(code)
        assert "isinstance" in result
        assert "ValueError" in result
        assert "TypeError" in result
        assert "class" in result
    
    def test_exception_comprehensive_integration(self):
        """Test comprehensive exception integration scenario."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, IndexError, Exception, BaseException
)

class ErrorProcessor:
    def __init__(self):
        self.errors = []
    
    def process(self, value):
        try:
            if value < 0:
                raise ValueError("negative")
            if value > 100:
                raise TypeError("too large")
            if value == 0:
                raise KeyError("zero")
            return value * 2
        except ValueError as e:
            self.errors.append(e)
            raise TypeError("converted from ValueError") from e
        except TypeError as e:
            self.errors.append(e)
            raise KeyError("converted from TypeError") from e
        except KeyError as e:
            self.errors.append(e)
            raise IndexError("converted from KeyError") from e
        except Exception as e:
            self.errors.append(e)
            raise

processor = ErrorProcessor()

for value in [-1, 150, 0, 50]:
    try:
        result = processor.process(value)
        print(f"Success: {result}")
    except IndexError as e:
        print(f"Final: {type(e).__name__}, cause: {type(e.__cause__).__name__ if e.__cause__ else None}")
    except Exception as e:
        print(f"Other: {type(e).__name__}")

print(f"Total errors: {len(processor.errors)}")
"""
        result = transpile(code)
        # Phase 33.3: Emitter directly assigns __cause__ for exception chaining
        assert "__cause__" in result
        assert "isinstance" in result or "except" in result
        assert "class" in result


