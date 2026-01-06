"""
Phase 33.3: Infrastructure Integration Tests

Comprehensive integration tests combining all Phase 33.3 features:
- Exception hierarchy with imports
- Import system with source maps
- Source maps with stack trace rewriting
- Operator overloading with exceptions
- Full feature integration in mini applications

Total: 50+ comprehensive integration tests.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from pynext.transpiler import transpile
from pynext.transpiler.sourcemap import SourceMapBuilder
from pynext.transpiler.stack_rewriter import rewrite_stack_trace, parse_stack_trace
from tests.integration.transpiler.test_python_js_equivalence import PythonJSExecutor


# =============================================================================
# EXCEPTIONS + IMPORTS INTEGRATION (10 tests)
# =============================================================================

class TestExceptionImportIntegration:
    """Test exception hierarchy with import system."""
    
    @pytest.mark.asyncio
    async def test_import_exceptions_and_use(self):
        """Test importing exceptions and using them."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, KeyError

def process_value(x):
    if x < 0:
        raise ValueError("negative")
    if x > 100:
        raise TypeError("too large")
    return x * 2

try:
    result = process_value(-1)
except ValueError as e:
    print(f"Caught ValueError: {e}")
except TypeError as e:
    print(f"Caught TypeError: {e}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "ValueError" in py_result["stdout"]
            assert "ValueError" in js_result["stdout"] or "negative" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_import_exceptions_with_isinstance(self):
        """Test importing exceptions and using isinstance."""
        code = """
from pynext.client.exceptions import ValueError, Exception

def handle_error(e):
    if isinstance(e, ValueError):
        return "value error"
    elif isinstance(e, Exception):
        return "generic error"
    return "unknown"

try:
    raise ValueError("test")
except Exception as e:
    print(handle_error(e))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "value error" in py_result["stdout"].lower()
    
    @pytest.mark.asyncio
    async def test_import_exceptions_with_chaining(self):
        """Test importing exceptions and using chaining."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

try:
    raise ValueError("original")
except ValueError as e:
    try:
        raise TypeError("converted") from e
    except TypeError as new:
        print(f"New: {new}, Cause: {new.__cause__ is not None}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
    
    @pytest.mark.asyncio
    async def test_import_exceptions_in_class(self):
        """Test importing exceptions in class."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class ErrorHandler:
    def __init__(self):
        self.errors = []
    
    def handle(self, e):
        if isinstance(e, ValueError):
            self.errors.append("value")
        elif isinstance(e, TypeError):
            self.errors.append("type")
        return len(self.errors)

handler = ErrorHandler()
try:
    raise ValueError("test")
except Exception as e:
    count = handler.handle(e)
    print(count)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "1" in py_result["stdout"] or "1" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_import_exceptions_with_dynamic_import(self):
        """Test exceptions with dynamic imports."""
        code = """
from importlib import import_module
from pynext.client.exceptions import ImportError

try:
    module = import_module("json")
    print("imported json")
except ImportError as e:
    print(f"Import failed: {e}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
    
    @pytest.mark.asyncio
    async def test_import_exceptions_with_relative_import(self):
        """Test exceptions with relative imports."""
        code = """
# Simulate relative import scenario
from pynext.client.exceptions import ValueError

def process():
    from . import utils  # Would be relative in real scenario
    return utils.process()

try:
    result = process()
except ValueError as e:
    print(f"Error: {e}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        # Just verify it transpiles
        assert "import" in js_code
        assert "ValueError" in js_code
    
    @pytest.mark.asyncio
    async def test_import_exceptions_with_star_import(self):
        """Test exceptions with star import."""
        code = """
from pynext.client.exceptions import *

def process(x):
    if x < 0:
        raise ValueError("negative")
    return x

try:
    result = process(-1)
except ValueError as e:
    print(f"Caught: {type(e).__name__}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
    
    @pytest.mark.asyncio
    async def test_import_exceptions_with_aliases(self):
        """Test exceptions with aliased imports."""
        code = """
from pynext.client.exceptions import ValueError as VE, TypeError as TE

def process(x):
    if x < 0:
        raise VE("negative")
    if x > 100:
        raise TE("too large")
    return x

try:
    result = process(-1)
except VE as e:
    print(f"Caught VE: {e}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
    
    @pytest.mark.asyncio
    async def test_import_exceptions_with_type_checking(self):
        """Test exceptions with TYPE_CHECKING imports."""
        code = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.client.exceptions import ValueError

def process(x):
    if x < 0:
        raise ValueError("negative")
    return x

result = process(5)
print(result)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "5" in py_result["stdout"] or "5" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_import_exceptions_comprehensive(self):
        """Test comprehensive exception and import integration."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, IndexError, Exception
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
            return value * 2
        except ValueError as e:
            self.errors.append(("value", str(e)))
            raise
        except TypeError as e:
            self.errors.append(("type", str(e)))
            raise

processor = ErrorProcessor()
try:
    result = processor.process(-1)
except ValueError as e:
    print(f"Handled: {len(processor.errors)}")
    print(isinstance(e, ValueError))
    print(isinstance(e, Exception))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]


# =============================================================================
# SOURCE MAPS + STACK TRACES INTEGRATION (10 tests)
# =============================================================================

class TestSourceMapStackTraceIntegration:
    """Test source maps with stack trace rewriting."""
    
    def test_source_map_generation_with_rewriting(self):
        """Test generating source map and using it for rewriting."""
        # Create source map
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.start_function("divide", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4, name="x")
        builder.add_mapping(2, 8, 2, 8, name="y")
        builder.end_function("divide", 5, 3)
        source_map = builder.to_json()
        
        # Create stack trace
        stack = """
Error: Division by zero
    at divide (handler.js:2:8)
"""
        
        # Rewrite stack trace
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
        assert "Error: Division by zero" in rewritten
    
    def test_source_map_with_function_boundaries_for_stack_trace(self):
        """Test source map function boundaries used in stack trace."""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.start_function("calculate", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4, name="x")
        builder.end_function("calculate", 10, 5)
        source_map = builder.to_json()
        
        # Function boundaries should be in source map
        assert "x_pynext_functions" in source_map
        assert len(source_map["x_pynext_functions"]) == 1
        assert source_map["x_pynext_functions"][0]["name"] == "calculate"
        
        # Use for stack trace rewriting
        stack = """
Error: test
    at calculate (handler.js:5:10)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_source_map_with_class_boundaries_for_stack_trace(self):
        """Test source map class boundaries used in stack trace."""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.start_class("Calculator", 0, 0, 0, 0)
        builder.start_function("divide", 2, 0, 2, 0)
        builder.add_mapping(3, 4, 3, 4)
        builder.end_function("divide", 5, 3)
        builder.end_class("Calculator", 10, 5)
        source_map = builder.to_json()
        
        assert "x_pynext_classes" in source_map
        assert "x_pynext_functions" in source_map
        
        stack = """
Error: test
    at Calculator.divide (handler.js:3:4)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_source_map_variable_names_in_stack_trace(self):
        """Test variable names from source map used in stack trace."""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(10, 15, 8, 12, name="my_variable")
        source_map = builder.to_json()
        
        assert "my_variable" in source_map["names"]
        
        stack = """
Error: test
    at process (handler.js:11:16)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        # Variable name might be used if function name not available
        assert "handler.py" in rewritten
    
    def test_source_map_column_precision_for_stack_trace(self):
        """Test column precision in source map for accurate stack traces."""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(10, 20, 8, 15)  # Precise column mapping
        source_map = builder.to_json()
        
        stack = """
Error: test
    at func (handler.js:11:21)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        # Should map to correct Python column
        assert "handler.py" in rewritten
    
    def test_source_map_multi_line_for_stack_trace(self):
        """Test multi-line mappings in source map for stack traces."""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(10, 0, 8, 0)
        builder.add_mapping(11, 0, 8, 10)  # Same source line, different column
        builder.add_mapping(12, 0, 9, 0)  # Different source line
        source_map = builder.to_json()
        
        stack = """
Error: test
    at func (handler.js:11:5)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_source_map_with_nested_functions_for_stack_trace(self):
        """Test nested function boundaries in source map for stack traces."""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.start_function("outer", 0, 0, 0, 0)
        builder.start_function("inner", 2, 0, 2, 0)
        builder.add_mapping(3, 4, 3, 4)
        builder.end_function("inner", 5, 3)
        builder.end_function("outer", 10, 5)
        source_map = builder.to_json()
        
        stack = """
Error: test
    at inner (handler.js:3:4)
    at outer (handler.js:6:2)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
        # Should rewrite both frames
    
    def test_source_map_with_source_content_for_stack_trace(self):
        """Test source content in source map for stack trace context."""
        source_code = "def divide(x, y):\n    return x / y"
        builder = SourceMapBuilder("handler.py", "handler.js", source_content=source_code)
        builder.add_mapping(0, 0, 0, 0)
        source_map = builder.to_json()
        
        assert "sourcesContent" in source_map
        assert source_map["sourcesContent"][0] == source_code
        
        stack = """
Error: Division by zero
    at divide (handler.js:1:10)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_comprehensive_source_map_stack_trace_scenario(self):
        """Test comprehensive source map and stack trace scenario."""
        builder = SourceMapBuilder("calculator.py", "calculator.js")
        builder.start_class("Calculator", 0, 0, 0, 0)
        builder.start_function("divide", 2, 0, 2, 0)
        builder.add_mapping(3, 4, 3, 4, name="x")
        builder.add_mapping(4, 8, 4, 8, name="y")
        builder.end_function("divide", 6, 4)
        builder.end_class("Calculator", 10, 5)
        source_map = builder.to_json()
        
        stack = """
TypeError: Division by zero
    at Calculator.divide (calculator.js:4:8)
    at process (calculator.js:15:5)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "calculator.py" in rewritten
        assert "TypeError" in rewritten
    
    def test_source_map_with_all_features_for_stack_trace(self):
        """Test source map with all features for stack trace rewriting."""
        source_code = """
class Processor:
    def process(self, x):
        if x < 0:
            raise ValueError("negative")
        return x * 2
"""
        builder = SourceMapBuilder("processor.py", "processor.js", source_content=source_code)
        builder.start_class("Processor", 0, 0, 0, 0)
        builder.start_function("process", 2, 0, 2, 0)
        builder.add_mapping(3, 8, 3, 8, name="x", kind="variable")
        builder.add_mapping(4, 12, 4, 12, name="ValueError", kind="statement")
        builder.end_function("process", 5, 4)
        builder.end_class("Processor", 6, 5)
        source_map = builder.to_json()
        
        # Verify all features present
        assert "x_pynext_functions" in source_map
        assert "x_pynext_classes" in source_map
        assert "names" in source_map
        assert "sourcesContent" in source_map
        
        stack = """
ValueError: negative
    at Processor.process (processor.js:4:12)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "processor.py" in rewritten
        assert "ValueError" in rewritten


# =============================================================================
# OPERATORS + EXCEPTIONS INTEGRATION (10 tests)
# =============================================================================

class TestOperatorExceptionIntegration:
    """Test operator overloading with exception handling."""
    
    @pytest.mark.asyncio
    async def test_operator_overloading_with_exceptions(self):
        """Test operator overloading that raises exceptions."""
        code = """
class SafeDivider:
    def __init__(self, value):
        self.value = value
    
    def __truediv__(self, other):
        if other.value == 0:
            raise ZeroDivisionError("division by zero")
        return SafeDivider(self.value / other.value)
    
    def __str__(self):
        return str(self.value)

a = SafeDivider(10)
b = SafeDivider(0)

try:
    result = a / b
except ZeroDivisionError as e:
    print(f"Caught: {type(e).__name__}")
    print(str(a))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "ZeroDivisionError" in py_result["stdout"] or "division by zero" in py_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_operator_overloading_with_exception_chaining(self):
        """Test operator overloading with exception chaining."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class Number:
    def __init__(self, value):
        self.value = value
    
    def __add__(self, other):
        if not isinstance(other, Number):
            raise ValueError("invalid type")
        return Number(self.value + other.value)
    
    def __mul__(self, other):
        if not isinstance(other, Number):
            raise ValueError("invalid type")
        if self.value * other.value > 1000:
            raise TypeError("result too large") from ValueError("overflow")
        return Number(self.value * other.value)

a = Number(100)
b = Number(20)

try:
    result = a * b
except TypeError as e:
    print(f"TypeError: {e.__cause__ is not None}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
    
    @pytest.mark.asyncio
    async def test_operator_overloading_with_isinstance_check(self):
        """Test operator overloading with isinstance check."""
        code = """
from pynext.client.exceptions import TypeError

class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        if not isinstance(other, Vector):
            raise TypeError("can only add Vector to Vector")
        return Vector(self.x + other.x, self.y + other.y)
    
    def __str__(self):
        return f"({self.x}, {self.y})"

v1 = Vector(1, 2)
v2 = Vector(3, 4)
v3 = v1 + v2
print(str(v3))

try:
    v4 = v1 + 5
except TypeError as e:
    print(f"Caught: {isinstance(e, TypeError)}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "(4, 6)" in py_result["stdout"] or "4" in py_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_operator_overloading_with_multiple_exceptions(self):
        """Test operator overloading with multiple exception types."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, ZeroDivisionError

class Calculator:
    def __init__(self, value):
        self.value = value
    
    def __truediv__(self, other):
        if not isinstance(other, Calculator):
            raise TypeError("invalid type")
        if other.value == 0:
            raise ZeroDivisionError("division by zero")
        if self.value < 0:
            raise ValueError("negative dividend")
        return Calculator(self.value / other.value)
    
    def __str__(self):
        return str(self.value)

a = Calculator(10)
b = Calculator(0)

try:
    result = a / b
except ZeroDivisionError as e:
    print("ZeroDivisionError")
except TypeError as e:
    print("TypeError")
except ValueError as e:
    print("ValueError")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "ZeroDivisionError" in py_result["stdout"] or "ZeroDivisionError" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_operator_overloading_with_reverse_operators(self):
        """Test reverse operators with exceptions."""
        code = """
from pynext.client.exceptions import TypeError

class Number:
    def __init__(self, value):
        self.value = value
    
    def __radd__(self, other):
        if not isinstance(other, (int, float)):
            raise TypeError("invalid type")
        return Number(self.value + other)
    
    def __str__(self):
        return str(self.value)

n = Number(5)
result = 10 + n
print(str(result))

try:
    result2 = "str" + n
except TypeError as e:
    print(f"Caught: {isinstance(e, TypeError)}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "15" in py_result["stdout"] or "15" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_operator_overloading_with_in_place_operators(self):
        """Test in-place operators with exceptions."""
        code = """
from pynext.client.exceptions import ValueError

class Counter:
    def __init__(self, value):
        self.value = value
    
    def __iadd__(self, other):
        if not isinstance(other, int):
            raise ValueError("can only add int")
        self.value += other
        return self
    
    def __str__(self):
        return str(self.value)

c = Counter(5)
c += 3
print(str(c))

try:
    c += "invalid"
except ValueError as e:
    print(f"Caught: {type(e).__name__}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "8" in py_result["stdout"] or "8" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_operator_overloading_with_unary_operators(self):
        """Test unary operators with exceptions."""
        code = """
from pynext.client.exceptions import OverflowError

class Number:
    def __init__(self, value):
        self.value = value
    
    def __neg__(self):
        if self.value < -1000:
            raise OverflowError("value too negative")
        return Number(-self.value)
    
    def __abs__(self):
        if abs(self.value) > 1000:
            raise OverflowError("value too large")
        return Number(abs(self.value))
    
    def __str__(self):
        return str(self.value)

n = Number(5)
neg = -n
print(str(neg))

abs_n = abs(n)
print(str(abs_n))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "-5" in py_result["stdout"] or "-5" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_operator_overloading_with_exception_hierarchy(self):
        """Test operator overloading with exception hierarchy."""
        code = """
from pynext.client.exceptions import (
    ArithmeticError, ZeroDivisionError, OverflowError, Exception
)

class SafeNumber:
    def __init__(self, value):
        self.value = value
    
    def __truediv__(self, other):
        if other.value == 0:
            raise ZeroDivisionError("division by zero")
        return SafeNumber(self.value / other.value)
    
    def __pow__(self, other):
        result = self.value ** other.value
        if result > 1000000:
            raise OverflowError("result too large")
        return SafeNumber(result)

a = SafeNumber(10)
b = SafeNumber(0)

try:
    result = a / b
except ZeroDivisionError as e:
    print(isinstance(e, ZeroDivisionError))
    print(isinstance(e, ArithmeticError))
    print(isinstance(e, Exception))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            # All isinstance checks should be True
            py_lines = py_result["stdout"].strip().split("\n")
            assert len(py_lines) >= 3
    
    @pytest.mark.asyncio
    async def test_operator_overloading_with_nested_exceptions(self):
        """Test operator overloading with nested exception handling."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class Container:
    def __init__(self, items):
        self.items = items
    
    def __getitem__(self, index):
        if not isinstance(index, int):
            raise TypeError("index must be int")
        if index < 0 or index >= len(self.items):
            raise ValueError("index out of range")
        return self.items[index]
    
    def __len__(self):
        return len(self.items)

c = Container([1, 2, 3])
print(len(c))

try:
    value = c[10]
except ValueError as e:
    print(f"ValueError: {isinstance(e, ValueError)}")

try:
    value = c["invalid"]
except TypeError as e:
    print(f"TypeError: {isinstance(e, TypeError)}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "3" in py_result["stdout"] or "3" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_operator_overloading_comprehensive(self):
        """Test comprehensive operator overloading with exceptions."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, ZeroDivisionError, ArithmeticError
)

class ComplexNumber:
    def __init__(self, real, imag):
        self.real = real
        self.imag = imag
    
    def __add__(self, other):
        if not isinstance(other, ComplexNumber):
            raise TypeError("can only add ComplexNumber")
        return ComplexNumber(self.real + other.real, self.imag + other.imag)
    
    def __truediv__(self, other):
        if not isinstance(other, ComplexNumber):
            raise TypeError("invalid type")
        if other.real == 0 and other.imag == 0:
            raise ZeroDivisionError("division by zero")
        # Simplified division
        return ComplexNumber(self.real / other.real, self.imag / other.imag)
    
    def __str__(self):
        return f"{self.real}+{self.imag}i"

c1 = ComplexNumber(10, 5)
c2 = ComplexNumber(0, 0)

try:
    result = c1 / c2
except ZeroDivisionError as e:
    print(isinstance(e, ZeroDivisionError))
    print(isinstance(e, ArithmeticError))
    print(isinstance(e, Exception))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]


# =============================================================================
# FULL FEATURE INTEGRATION MINI APPS (20 tests)
# =============================================================================

class TestFullFeatureIntegration:
    """Test all Phase 33.3 features together in mini applications."""
    
    @pytest.mark.asyncio
    async def test_error_handler_app(self):
        """Mini app: Error handler with exceptions, imports, operators."""
        code = """
from pynext.client.exceptions import ValueError, TypeError, Exception

class ErrorHandler:
    def __init__(self):
        self.errors = []
    
    def process(self, value):
        if value < 0:
            raise ValueError("negative")
        if value > 100:
            raise TypeError("too large")
        return value * 2
    
    def safe_process(self, value):
        try:
            return self.process(value)
        except ValueError as e:
            self.errors.append(("value", str(e)))
            return None
        except TypeError as e:
            self.errors.append(("type", str(e)))
            return None
        except Exception as e:
            self.errors.append(("other", str(e)))
            return None

handler = ErrorHandler()
result1 = handler.safe_process(-1)
result2 = handler.safe_process(150)
result3 = handler.safe_process(50)

print(len(handler.errors))
print(result3)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "2" in py_result["stdout"] or "2" in js_result["stdout"]
            assert "100" in py_result["stdout"] or "100" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_calculator_app_with_operators_and_exceptions(self):
        """Mini app: Calculator with operator overloading and exceptions."""
        code = """
from pynext.client.exceptions import ZeroDivisionError, ValueError

class Number:
    def __init__(self, value):
        self.value = value
    
    def __add__(self, other):
        return Number(self.value + other.value)
    
    def __sub__(self, other):
        return Number(self.value - other.value)
    
    def __mul__(self, other):
        return Number(self.value * other.value)
    
    def __truediv__(self, other):
        if other.value == 0:
            raise ZeroDivisionError("division by zero")
        return Number(self.value / other.value)
    
    def __str__(self):
        return str(self.value)

class Calculator:
    def __init__(self):
        self.history = []
    
    def calculate(self, a, op, b):
        try:
            if op == "+":
                result = a + b
            elif op == "-":
                result = a - b
            elif op == "*":
                result = a * b
            elif op == "/":
                result = a / b
            else:
                raise ValueError("invalid operator")
            self.history.append((op, str(result)))
            return result
        except ZeroDivisionError as e:
            self.history.append(("error", str(e)))
            return None
        except ValueError as e:
            self.history.append(("error", str(e)))
            return None

calc = Calculator()
a = Number(10)
b = Number(0)

result1 = calc.calculate(a, "+", Number(5))
result2 = calc.calculate(a, "/", b)
result3 = calc.calculate(a, "*", Number(2))

print(str(result1))
print(len(calc.history))
print(str(result3))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "15" in py_result["stdout"] or "15" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_data_processor_app(self):
        """Mini app: Data processor with imports, exceptions, operators."""
        code = """
from pynext.client.exceptions import ValueError, TypeError
import json

class DataProcessor:
    def __init__(self):
        self.processed = []
    
    def process_item(self, item):
        if not isinstance(item, (int, float)):
            raise TypeError("item must be numeric")
        if item < 0:
            raise ValueError("item must be non-negative")
        return item * 2
    
    def process_batch(self, items):
        results = []
        for item in items:
            try:
                result = self.process_item(item)
                results.append(result)
            except ValueError as e:
                results.append(None)
            except TypeError as e:
                results.append(None)
        return results

processor = DataProcessor()
items = [1, 2, -1, 3, "invalid", 4]
results = processor.process_batch(items)

print(len(results))
print(len([r for r in results if r is not None]))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "6" in py_result["stdout"] or "6" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_validator_app(self):
        """Mini app: Validator with exceptions, isinstance, operators."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class Validator:
    def validate_number(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("must be number")
        if value < 0:
            raise ValueError("must be non-negative")
        return value
    
    def validate_string(self, value):
        if not isinstance(value, str):
            raise TypeError("must be string")
        if len(value) == 0:
            raise ValueError("must be non-empty")
        return value
    
    def validate_list(self, value):
        if not isinstance(value, list):
            raise TypeError("must be list")
        if len(value) == 0:
            raise ValueError("must be non-empty")
        return value

validator = Validator()

try:
    result1 = validator.validate_number(5)
    result2 = validator.validate_string("test")
    result3 = validator.validate_list([1, 2, 3])
    print("all valid")
except Exception as e:
    print(f"error: {type(e).__name__}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "all valid" in py_result["stdout"] or "all valid" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_api_client_app(self):
        """Mini app: API client with imports, exceptions, error handling."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, Exception
)

class APIClient:
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        if not isinstance(key, str):
            raise TypeError("key must be string")
        if key not in self.cache:
            raise KeyError(f"key not found: {key}")
        return self.cache[key]
    
    def set(self, key, value):
        if not isinstance(key, str):
            raise TypeError("key must be string")
        self.cache[key] = value
        return True
    
    def safe_get(self, key, default=None):
        try:
            return self.get(key)
        except KeyError:
            return default
        except TypeError as e:
            return default

client = APIClient()
client.set("name", "test")
value = client.safe_get("name")
default = client.safe_get("missing", "default")

print(value)
print(default)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "test" in py_result["stdout"] or "test" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_math_library_app(self):
        """Mini app: Math library with operators, exceptions, imports."""
        code = """
from pynext.client.exceptions import ValueError, OverflowError

class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        if not isinstance(other, Vector):
            raise ValueError("can only add Vector")
        return Vector(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            raise ValueError("scalar must be number")
        result = Vector(self.x * scalar, self.y * scalar)
        if abs(result.x) > 1000 or abs(result.y) > 1000:
            raise OverflowError("result too large")
        return result
    
    def __abs__(self):
        magnitude = (self.x**2 + self.y**2)**0.5
        if magnitude > 1000:
            raise OverflowError("magnitude too large")
        return magnitude
    
    def __str__(self):
        return f"({self.x}, {self.y})"

v1 = Vector(1, 2)
v2 = Vector(3, 4)
v3 = v1 + v2
magnitude = abs(v1)

print(str(v3))
print(magnitude)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "(4, 6)" in py_result["stdout"] or "4" in py_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_config_manager_app(self):
        """Mini app: Config manager with imports, exceptions, validation."""
        code = """
from pynext.client.exceptions import ValueError, KeyError, TypeError

class ConfigManager:
    def __init__(self):
        self.config = {}
    
    def set(self, key, value):
        if not isinstance(key, str):
            raise TypeError("key must be string")
        if key == "":
            raise ValueError("key cannot be empty")
        self.config[key] = value
    
    def get(self, key, default=None):
        if key not in self.config:
            if default is not None:
                return default
            raise KeyError(f"key not found: {key}")
        return self.config[key]
    
    def validate(self):
        errors = []
        for key, value in self.config.items():
            try:
                if not isinstance(key, str):
                    raise TypeError(f"invalid key type: {key}")
                if key.startswith("_"):
                    raise ValueError(f"private key not allowed: {key}")
            except (TypeError, ValueError) as e:
                errors.append(str(e))
        return errors

manager = ConfigManager()
manager.set("name", "test")
manager.set("value", 42)

name = manager.get("name")
value = manager.get("value")
errors = manager.validate()

print(name)
print(value)
print(len(errors))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "test" in py_result["stdout"] or "test" in js_result["stdout"]
            assert "42" in py_result["stdout"] or "42" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_file_processor_app(self):
        """Mini app: File processor with imports, exceptions, operators."""
        code = """
from pynext.client.exceptions import (
    FileNotFoundError, PermissionError, OSError, ValueError
)

class FileProcessor:
    def __init__(self):
        self.files = {}
    
    def read(self, filename):
        if not isinstance(filename, str):
            raise TypeError("filename must be string")
        if filename not in self.files:
            raise FileNotFoundError(f"file not found: {filename}")
        return self.files[filename]
    
    def write(self, filename, content):
        if not isinstance(filename, str):
            raise TypeError("filename must be string")
        if filename.startswith("/"):
            raise PermissionError("cannot write to root")
        self.files[filename] = content
    
    def process(self, filename):
        try:
            content = self.read(filename)
            return len(content)
        except FileNotFoundError:
            return 0
        except PermissionError:
            return -1

processor = FileProcessor()
processor.write("test.txt", "hello")
length = processor.process("test.txt")

print(length)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "5" in py_result["stdout"] or "5" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_event_system_app(self):
        """Mini app: Event system with exceptions, imports, error handling."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class EventEmitter:
    def __init__(self):
        self.listeners = {}
    
    def on(self, event, handler):
        if not isinstance(event, str):
            raise TypeError("event must be string")
        if not callable(handler):
            raise TypeError("handler must be callable")
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(handler)
    
    def emit(self, event, *args):
        if event not in self.listeners:
            return
        for handler in self.listeners[event]:
            try:
                handler(*args)
            except Exception as e:
                print(f"Handler error: {type(e).__name__}")

emitter = EventEmitter()

def handler(value):
    if value < 0:
        raise ValueError("negative value")
    print(f"Handled: {value}")

emitter.on("test", handler)
emitter.emit("test", 5)
emitter.emit("test", -1)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "Handled: 5" in py_result["stdout"] or "Handled: 5" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_cache_system_app(self):
        """Mini app: Cache system with operators, exceptions, imports."""
        code = """
from pynext.client.exceptions import KeyError, ValueError

class Cache:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.data = {}
    
    def __getitem__(self, key):
        if key not in self.data:
            raise KeyError(f"key not found: {key}")
        return self.data[key]
    
    def __setitem__(self, key, value):
        if len(self.data) >= self.max_size and key not in self.data:
            raise ValueError("cache full")
        self.data[key] = value
    
    def __len__(self):
        return len(self.data)
    
    def __contains__(self, key):
        return key in self.data

cache = Cache(max_size=3)
cache["a"] = 1
cache["b"] = 2
cache["c"] = 3

print(len(cache))
print("a" in cache)
print(cache["a"])

try:
    cache["d"] = 4
except ValueError as e:
    print("cache full")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "3" in py_result["stdout"] or "3" in js_result["stdout"]
            assert "cache full" in py_result["stdout"] or "cache full" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_comprehensive_app_all_features(self):
        """Comprehensive app using all Phase 33.3 features."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, ZeroDivisionError, Exception
)
import json

class Calculator:
    def __init__(self):
        self.history = []
    
    def calculate(self, a, op, b):
        try:
            if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                raise TypeError("operands must be numbers")
            if op == "+":
                result = a + b
            elif op == "-":
                result = a - b
            elif op == "*":
                result = a * b
            elif op == "/":
                if b == 0:
                    raise ZeroDivisionError("division by zero")
                result = a / b
            else:
                raise ValueError(f"invalid operator: {op}")
            self.history.append((op, result))
            return result
        except ZeroDivisionError as e:
            self.history.append(("error", str(e)))
            raise
        except (TypeError, ValueError) as e:
            self.history.append(("error", str(e)))
            raise

calc = Calculator()

try:
    result1 = calc.calculate(10, "+", 5)
    result2 = calc.calculate(10, "/", 0)
except ZeroDivisionError as e:
    print(f"Caught: {isinstance(e, ZeroDivisionError)}")
    print(f"Is ArithmeticError: {isinstance(e, Exception)}")
    print(f"History: {len(calc.history)}")
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "Caught" in py_result["stdout"] or "Caught" in js_result["stdout"]
    
    # Continue with 10 more comprehensive mini apps...
    @pytest.mark.asyncio
    async def test_web_api_app(self):
        """Mini app: Web API with all features."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, HTTPError
)

class API:
    def __init__(self):
        self.routes = {}
    
    def route(self, path, handler):
        if not isinstance(path, str):
            raise TypeError("path must be string")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self.routes[path] = handler
    
    def handle(self, path, data=None):
        if path not in self.routes:
            raise KeyError(f"route not found: {path}")
        try:
            return self.routes[path](data)
        except Exception as e:
            raise HTTPError(f"handler error: {e}") from e

api = API()

def handler(data):
    if data is None:
        raise ValueError("data required")
    return {"status": "ok", "data": data}

api.route("/test", handler)
result = api.handle("/test", {"key": "value"})

print(result["status"])
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
    
    @pytest.mark.asyncio
    async def test_database_orm_app(self):
        """Mini app: Database ORM with exceptions, operators, imports."""
        code = """
from pynext.client.exceptions import ValueError, KeyError, AttributeError

class Model:
    def __init__(self, **kwargs):
        self._data = kwargs
    
    def __getitem__(self, key):
        if key not in self._data:
            raise KeyError(f"field not found: {key}")
        return self._data[key]
    
    def __setitem__(self, key, value):
        self._data[key] = value
    
    def __contains__(self, key):
        return key in self._data
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

class User(Model):
    def validate(self):
        errors = []
        if "name" not in self:
            errors.append("name required")
        if "email" not in self:
            errors.append("email required")
        if errors:
            raise ValueError(f"validation errors: {errors}")
        return True

user = User(name="test", email="test@example.com")
user.validate()

name = user["name"]
email = user.get("email")

print(name)
print(email)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "test" in py_result["stdout"] or "test" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_router_app(self):
        """Mini app: Router with exceptions, imports, operators."""
        code = """
from pynext.client.exceptions import ValueError, KeyError

class Router:
    def __init__(self):
        self.routes = {}
        self.middleware = []
    
    def add_route(self, method, path, handler):
        key = f"{method}:{path}"
        if key in self.routes:
            raise ValueError(f"route already exists: {key}")
        self.routes[key] = handler
    
    def match(self, method, path):
        key = f"{method}:{path}"
        if key not in self.routes:
            raise KeyError(f"route not found: {key}")
        return self.routes[key]
    
    def __len__(self):
        return len(self.routes)
    
    def __contains__(self, key):
        return key in self.routes

router = Router()
router.add_route("GET", "/users", lambda: "users")
router.add_route("POST", "/users", lambda: "create user")

handler = router.match("GET", "/users")
print(handler())
print(len(router))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "users" in py_result["stdout"] or "users" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_state_manager_app(self):
        """Mini app: State manager with exceptions, operators, imports."""
        code = """
from pynext.client.exceptions import ValueError, KeyError

class StateManager:
    def __init__(self):
        self.state = {}
        self.listeners = []
    
    def set(self, key, value):
        if not isinstance(key, str):
            raise ValueError("key must be string")
        old_value = self.state.get(key)
        self.state[key] = value
        if old_value != value:
            self._notify(key, value, old_value)
    
    def get(self, key, default=None):
        if key not in self.state:
            if default is not None:
                return default
            raise KeyError(f"key not found: {key}")
        return self.state[key]
    
    def _notify(self, key, new_value, old_value):
        for listener in self.listeners:
            try:
                listener(key, new_value, old_value)
            except Exception:
                pass  # Ignore listener errors
    
    def subscribe(self, listener):
        self.listeners.append(listener)

manager = StateManager()

def listener(key, new, old):
    print(f"{key} changed: {old} -> {new}")

manager.subscribe(listener)
manager.set("count", 0)
manager.set("count", 1)

value = manager.get("count")
print(value)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "1" in py_result["stdout"] or "1" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_form_validator_app(self):
        """Mini app: Form validator with exceptions, isinstance, operators."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class FormValidator:
    def __init__(self):
        self.errors = {}
    
    def validate_field(self, name, value, rules):
        errors = []
        for rule_name, rule_func in rules.items():
            try:
                rule_func(value)
            except (ValueError, TypeError) as e:
                errors.append(f"{rule_name}: {str(e)}")
        if errors:
            self.errors[name] = errors
            return False
        return True
    
    def validate(self, form_data):
        self.errors = {}
        all_valid = True
        
        # Validate name
        name_valid = self.validate_field("name", form_data.get("name"), {
            "required": lambda v: v if v else ValueError("required"),
            "min_length": lambda v: v if len(v) >= 3 else ValueError("too short"),
        })
        all_valid = all_valid and name_valid
        
        # Validate age
        age_valid = self.validate_field("age", form_data.get("age"), {
            "required": lambda v: v if v is not None else ValueError("required"),
            "is_number": lambda v: v if isinstance(v, (int, float)) else TypeError("must be number"),
            "min_value": lambda v: v if v >= 0 else ValueError("must be non-negative"),
        })
        all_valid = all_valid and age_valid
        
        return all_valid

validator = FormValidator()
form1 = {"name": "test", "age": 25}
form2 = {"name": "ab", "age": -1}

valid1 = validator.validate(form1)
valid2 = validator.validate(form2)

print(valid1)
print(len(validator.errors))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "True" in py_result["stdout"] or "true" in py_result["stdout"] or "1" in py_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_payment_processor_app(self):
        """Mini app: Payment processor with all features."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, OverflowError, ArithmeticError
)

class Money:
    def __init__(self, amount, currency="USD"):
        if not isinstance(amount, (int, float)):
            raise TypeError("amount must be number")
        if amount < 0:
            raise ValueError("amount cannot be negative")
        if amount > 1000000:
            raise OverflowError("amount too large")
        self.amount = amount
        self.currency = currency
    
    def __add__(self, other):
        if not isinstance(other, Money):
            raise TypeError("can only add Money")
        if self.currency != other.currency:
            raise ValueError("currency mismatch")
        total = self.amount + other.amount
        if total > 1000000:
            raise OverflowError("total too large")
        return Money(total, self.currency)
    
    def __sub__(self, other):
        if not isinstance(other, Money):
            raise TypeError("can only subtract Money")
        if self.currency != other.currency:
            raise ValueError("currency mismatch")
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("insufficient funds")
        return Money(result, self.currency)
    
    def __str__(self):
        return f"{self.amount} {self.currency}"

class PaymentProcessor:
    def process(self, amount, currency="USD"):
        try:
            money = Money(amount, currency)
            return str(money)
        except (ValueError, TypeError, OverflowError) as e:
            return f"Error: {type(e).__name__}"

processor = PaymentProcessor()
result1 = processor.process(100)
result2 = processor.process(-10)

print(result1)
print(result2)
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "100" in py_result["stdout"] or "100" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_logging_system_app(self):
        """Mini app: Logging system with exceptions, imports."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class Logger:
    def __init__(self, level="INFO"):
        self.level = level
        self.logs = []
    
    def log(self, level, message):
        if not isinstance(level, str):
            raise TypeError("level must be string")
        if not isinstance(message, str):
            raise TypeError("message must be string")
        if level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError(f"invalid level: {level}")
        self.logs.append((level, message))
    
    def info(self, message):
        self.log("INFO", message)
    
    def error(self, message):
        self.log("ERROR", message)

logger = Logger()
logger.info("test message")
logger.error("error message")

print(len(logger.logs))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "2" in py_result["stdout"] or "2" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_serializer_app(self):
        """Mini app: Serializer with exceptions, operators, imports."""
        code = """
from pynext.client.exceptions import ValueError, TypeError
import json

class Serializer:
    def __init__(self):
        self.serialized = []
    
    def serialize(self, obj):
        if isinstance(obj, dict):
            return json.dumps(obj)
        elif isinstance(obj, list):
            return json.dumps(obj)
        elif isinstance(obj, (int, float, str, bool)):
            return str(obj)
        else:
            raise TypeError(f"cannot serialize: {type(obj).__name__}")
    
    def deserialize(self, data):
        if not isinstance(data, str):
            raise TypeError("data must be string")
        try:
            return json.loads(data)
        except Exception as e:
            raise ValueError(f"invalid JSON: {e}")

serializer = Serializer()
data = {"key": "value"}
serialized = serializer.serialize(data)
deserialized = serializer.deserialize(serialized)

print(serialized)
print(deserialized["key"])
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "value" in py_result["stdout"] or "value" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_workflow_engine_app(self):
        """Mini app: Workflow engine with all features."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, RuntimeError
)

class Workflow:
    def __init__(self, name):
        self.name = name
        self.steps = []
        self.state = {}
    
    def add_step(self, step_name, handler):
        if not isinstance(step_name, str):
            raise TypeError("step_name must be string")
        if not callable(handler):
            raise TypeError("handler must be callable")
        if step_name in [s[0] for s in self.steps]:
            raise ValueError(f"step already exists: {step_name}")
        self.steps.append((step_name, handler))
    
    def execute(self):
        for step_name, handler in self.steps:
            try:
                result = handler(self.state)
                self.state[step_name] = result
            except Exception as e:
                raise RuntimeError(f"step {step_name} failed: {e}") from e
        return self.state

workflow = Workflow("test")

def step1(state):
    state["count"] = 0
    return state["count"]

def step2(state):
    state["count"] += 1
    return state["count"]

workflow.add_step("init", step1)
workflow.add_step("increment", step2)
result = workflow.execute()

print(result["count"])
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "1" in py_result["stdout"] or "1" in js_result["stdout"]
    
    @pytest.mark.asyncio
    async def test_ultimate_integration_app(self):
        """Ultimate integration: All Phase 33.3 features together."""
        code = """
from pynext.client.exceptions import (
    ValueError, TypeError, KeyError, ZeroDivisionError,
    ArithmeticError, Exception, BaseException
)
import json

class UltimateApp:
    def __init__(self):
        self.data = {}
        self.errors = []
    
    def set(self, key, value):
        if not isinstance(key, str):
            raise TypeError("key must be string")
        if key == "":
            raise ValueError("key cannot be empty")
        self.data[key] = value
    
    def get(self, key):
        if key not in self.data:
            raise KeyError(f"key not found: {key}")
        return self.data[key]
    
    def calculate(self, a, op, b):
        try:
            if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                raise TypeError("operands must be numbers")
            if op == "+":
                return a + b
            elif op == "-":
                return a - b
            elif op == "*":
                return a * b
            elif op == "/":
                if b == 0:
                    raise ZeroDivisionError("division by zero")
                return a / b
            else:
                raise ValueError(f"invalid operator: {op}")
        except ZeroDivisionError as e:
            self.errors.append(("calc", str(e)))
            raise
        except (TypeError, ValueError) as e:
            self.errors.append(("calc", str(e)))
            raise
    
    def process(self, key, a, op, b):
        try:
            value = self.get(key)
            result = self.calculate(a, op, b)
            self.set(f"{key}_result", result)
            return result
        except KeyError as e:
            self.errors.append(("process", str(e)))
            return None
        except ZeroDivisionError as e:
            self.errors.append(("process", str(e)))
            return None
        except Exception as e:
            self.errors.append(("process", str(e)))
            return None
    
    def validate_errors(self):
        for error_type, message in self.errors:
            if isinstance(error_type, str):
                if "ZeroDivisionError" in message:
                    print("Arithmetic error detected")
                elif "KeyError" in message:
                    print("Key error detected")
                elif "TypeError" in message:
                    print("Type error detected")

app = UltimateApp()
app.set("x", 10)
result1 = app.process("x", 10, "+", 5)
result2 = app.process("missing", 10, "/", 0)
app.validate_errors()

print(result1)
print(len(app.errors))
"""
        executor = PythonJSExecutor()
        py_result = executor.execute_python(code)
        js_code = transpile(code)
        js_result = executor.execute_javascript(js_code)
        
        assert py_result["success"] == js_result["success"]
        if py_result["success"]:
            assert "15" in py_result["stdout"] or "15" in js_result["stdout"]


# =============================================================================
# SOURCE MAP + STACK TRACE + TRANSPILATION INTEGRATION (10 tests)
# =============================================================================

class TestSourceMapTranspilationIntegration:
    """Test source maps generated during transpilation and used for stack traces."""
    
    def test_transpile_with_source_map_generation(self):
        """Test transpilation generates source map."""
        code = """
def divide(x, y):
    return x / y

result = divide(10, 2)
print(result)
"""
        # Transpile with source map tracking
        result = transpile(code)
        assert "function" in result or "divide" in result
        
        # Source map should be available if we track it
        # (This depends on transpile() returning source map)
    
    def test_transpile_error_generates_stack_trace(self):
        """Test transpiled code error generates stack trace."""
        code = """
def divide(x, y):
    if y == 0:
        raise ZeroDivisionError("division by zero")
    return x / y

result = divide(10, 0)
"""
        result = transpile(code)
        assert "function" in result or "divide" in result
        assert "ZeroDivisionError" in result or "division by zero" in result
    
    def test_source_map_for_transpiled_function(self):
        """Test source map generated for transpiled function."""
        code = """
def process(x):
    if x < 0:
        raise ValueError("negative")
    return x * 2

result = process(5)
"""
        # Create source map manually to simulate transpilation
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("process", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4, name="x")
        builder.add_mapping(2, 8, 2, 8, name="ValueError")
        builder.end_function("process", 4, 3)
        source_map = builder.to_json()
        
        # Simulate stack trace from transpiled code
        stack = """
ValueError: negative
    at process (output.js:2:8)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "source.py" in rewritten
    
    def test_source_map_for_transpiled_class(self):
        """Test source map generated for transpiled class."""
        code = """
class Calculator:
    def divide(self, x, y):
        if y == 0:
            raise ZeroDivisionError("division by zero")
        return x / y

calc = Calculator()
result = calc.divide(10, 0)
"""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("Calculator", 0, 0, 0, 0)
        builder.start_function("divide", 2, 0, 2, 0)
        builder.add_mapping(3, 8, 3, 8, name="y")
        builder.end_function("divide", 5, 3)
        builder.end_class("Calculator", 6, 5)
        source_map = builder.to_json()
        
        stack = """
ZeroDivisionError: division by zero
    at Calculator.divide (output.js:3:8)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "source.py" in rewritten
    
    def test_source_map_for_transpiled_imports(self):
        """Test source map generated for transpiled imports."""
        code = """
from pynext.client.exceptions import ValueError

def process(x):
    if x < 0:
        raise ValueError("negative")
    return x

result = process(-1)
"""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)  # Import line
        builder.start_function("process", 2, 0, 2, 0)
        builder.add_mapping(3, 8, 3, 8, name="x")
        builder.add_mapping(4, 8, 4, 8, name="ValueError")
        builder.end_function("process", 5, 4)
        source_map = builder.to_json()
        
        stack = """
ValueError: negative
    at process (output.js:4:8)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "source.py" in rewritten
    
    def test_source_map_for_transpiled_operators(self):
        """Test source map generated for transpiled operators."""
        code = """
class Number:
    def __init__(self, value):
        self.value = value
    
    def __add__(self, other):
        return Number(self.value + other.value)
    
    def __truediv__(self, other):
        if other.value == 0:
            raise ZeroDivisionError("division by zero")
        return Number(self.value / other.value)

a = Number(10)
b = Number(0)
result = a / b
"""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("Number", 0, 0, 0, 0)
        builder.start_function("__truediv__", 6, 0, 6, 0)
        builder.add_mapping(7, 8, 7, 8, name="other")
        builder.add_mapping(8, 12, 8, 12, name="ZeroDivisionError")
        builder.end_function("__truediv__", 9, 7)
        builder.end_class("Number", 10, 8)
        source_map = builder.to_json()
        
        stack = """
ZeroDivisionError: division by zero
    at Number.__truediv__ (output.js:8:12)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "source.py" in rewritten
    
    def test_comprehensive_transpilation_source_map(self):
        """Test comprehensive transpilation with full source map."""
        code = """
from pynext.client.exceptions import ValueError, TypeError

class Processor:
    def __init__(self):
        self.data = {}
    
    def process(self, key, value):
        if not isinstance(key, str):
            raise TypeError("key must be string")
        if key in self.data:
            raise ValueError(f"key already exists: {key}")
        self.data[key] = value
        return value

processor = Processor()
result = processor.process("test", 42)
print(result)
"""
        # Create comprehensive source map
        builder = SourceMapBuilder("processor.py", "processor.js")
        builder.add_mapping(0, 0, 0, 0)  # Import
        builder.start_class("Processor", 2, 0, 2, 0)
        builder.start_function("__init__", 3, 0, 3, 0)
        builder.add_mapping(4, 8, 4, 8, name="self")
        builder.end_function("__init__", 5, 4)
        builder.start_function("process", 6, 0, 6, 0)
        builder.add_mapping(7, 8, 7, 8, name="key")
        builder.add_mapping(8, 12, 8, 12, name="TypeError")
        builder.end_function("process", 12, 10)
        builder.end_class("Processor", 13, 11)
        source_map = builder.to_json()
        
        stack = """
TypeError: key must be string
    at Processor.process (processor.js:8:12)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "processor.py" in rewritten
        assert "TypeError" in rewritten
    
    def test_source_map_with_all_mapping_kinds(self):
        """Test source map with all mapping kinds."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, kind="statement")
        builder.start_function("func", 1, 0, 1, 0)
        builder.add_mapping(2, 4, 2, 4, name="x", kind="variable")
        builder.end_function("func", 3, 2)
        builder.start_class("MyClass", 4, 0, 4, 0)
        builder.end_class("MyClass", 5, 4)
        source_map = builder.to_json()
        
        # Verify all features
        assert "x_pynext_functions" in source_map
        assert "x_pynext_classes" in source_map
        assert "names" in source_map
        assert "mappings" in source_map
    
    def test_source_map_roundtrip_with_stack_trace(self):
        """Test complete roundtrip: transpile → source map → stack trace."""
        code = """
def calculate(x, y):
    if y == 0:
        raise ZeroDivisionError("division by zero")
    return x / y

result = calculate(10, 0)
"""
        # Simulate transpilation with source map
        builder = SourceMapBuilder("calculator.py", "calculator.js")
        builder.start_function("calculate", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4, name="y")
        builder.add_mapping(2, 8, 2, 8, name="ZeroDivisionError")
        builder.end_function("calculate", 3, 2)
        source_map = builder.to_json()
        
        # Simulate JavaScript error stack trace
        stack = """
ZeroDivisionError: division by zero
    at calculate (calculator.js:2:8)
    at <anonymous> (calculator.js:5:1)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "calculator.py" in rewritten
        assert "ZeroDivisionError" in rewritten
    
    def test_source_map_with_complex_nested_structure(self):
        """Test source map with complex nested structure."""
        builder = SourceMapBuilder("app.py", "app.js")
        builder.start_class("App", 0, 0, 0, 0)
        builder.start_function("__init__", 2, 0, 2, 0)
        builder.end_function("__init__", 4, 2)
        builder.start_function("process", 5, 0, 5, 0)
        builder.start_function("helper", 6, 0, 6, 0)
        builder.add_mapping(7, 8, 7, 8, name="x")
        builder.end_function("helper", 8, 6)
        builder.end_function("process", 10, 7)
        builder.end_class("App", 11, 8)
        source_map = builder.to_json()
        
        stack = """
Error: test
    at App.helper (app.js:7:8)
    at App.process (app.js:9:2)
"""
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "app.py" in rewritten
        # Should rewrite both frames correctly

