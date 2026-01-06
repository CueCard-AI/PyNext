"""
Phase 33.1: Edge Case Equivalence Tests

Tests for edge cases and corner cases that might cause issues
in Python-to-JavaScript transpilation.
"""

import pytest
import sys
from pathlib import Path
from pynext.transpiler import transpile

# Import executor
sys.path.insert(0, str(Path(__file__).parent))
from test_python_js_equivalence import PythonJSExecutor


@pytest.fixture
def executor():
    """Create a Python-JS executor."""
    exec = PythonJSExecutor()
    yield exec
    import shutil
    shutil.rmtree(exec.temp_dir, ignore_errors=True)


class TestEdgeCases:
    """Test edge cases and corner cases."""
    
    def test_empty_list_comprehension(self, executor):
        """[] - empty list comprehension"""
        python_code = """
result = [x for x in []]
print(result)
"""
        js_code = transpile(python_code)
        
        py_result = executor.execute_python(python_code)
        js_result = executor.execute_javascript(js_code)
        
        assert executor.compare_results(py_result, js_result)
    
    def test_nested_comprehensions(self, executor):
        """[[x*y for y in range(3)] for x in range(2)]"""
        python_code = """
result = [[x*y for y in range(3)] for x in range(2)]
print(result)
"""
        js_code = transpile(python_code)
        
        py_result = executor.execute_python(python_code)
        js_result = executor.execute_javascript(js_code)
        
        assert executor.compare_results(py_result, js_result)
    
    def test_lambda_in_comprehension(self, executor):
        """[lambda x: x*2 for i in range(3)]"""
        python_code = """
funcs = [lambda x: x*2 for i in range(3)]
print([f(5) for f in funcs])
"""
        js_code = transpile(python_code)
        
        py_result = executor.execute_python(python_code)
        js_result = executor.execute_javascript(js_code)
        
        assert executor.compare_results(py_result, js_result)
    
    def test_closure_capture(self, executor):
        """Test closure variable capture"""
        python_code = """
def make_multiplier(n):
    def multiply(x):
        return x * n
    return multiply

mul2 = make_multiplier(2)
mul3 = make_multiplier(3)
print(mul2(5))
print(mul3(5))
"""
        js_code = transpile(python_code)
        
        py_result = executor.execute_python(python_code)
        js_result = executor.execute_javascript(js_code)
        
        assert executor.compare_results(py_result, js_result)
    
    def test_default_arg_mutation(self, executor):
        """Test default argument with mutable default"""
        python_code = """
def append_item(item, lst=[]):
    lst.append(item)
    return lst

print(append_item(1))
print(append_item(2))
"""
        js_code = transpile(python_code)
        
        py_result = executor.execute_python(python_code)
        js_result = executor.execute_javascript(js_code)
        
        # Both should show the same behavior (mutable default)
        assert executor.compare_results(py_result, js_result)
    
    def test_for_else_with_break(self, executor):
        """for...else that doesn't execute else"""
        python_code = """
for i in range(3):
    if i == 1:
        break
else:
    print("else")
print("done")
"""
        js_code = transpile(python_code)
        
        py_result = executor.execute_python(python_code)
        js_result = executor.execute_javascript(js_code)
        
        assert executor.compare_results(py_result, js_result)
    
    def test_for_else_without_break(self, executor):
        """for...else that executes else"""
        python_code = """
for i in range(3):
    if i == 10:
        break
else:
    print("else")
print("done")
"""
        js_code = transpile(python_code)
        
        py_result = executor.execute_python(python_code)
        js_result = executor.execute_javascript(js_code)
        
        assert executor.compare_results(py_result, js_result)
    
    def test_multiple_inheritance(self, executor):
        """Test multiple inheritance with mixins"""
        python_code = """
class A:
    def method_a(self):
        return "A"

class B:
    def method_b(self):
        return "B"

class C(A, B):
    pass

c = C()
print(c.method_a())
print(c.method_b())
"""
        js_code = transpile(python_code)
        
        py_result = executor.execute_python(python_code)
        js_result = executor.execute_javascript(js_code)
        
        assert executor.compare_results(py_result, js_result)
    
    def test_property_getter_setter(self, executor):
        """Test @property with getter and setter"""
        python_code = """
class Temperature:
    def __init__(self):
        self._celsius = 0
    
    @property
    def celsius(self):
        return self._celsius
    
    @celsius.setter
    def celsius(self, value):
        self._celsius = value
    
    @property
    def fahrenheit(self):
        return self._celsius * 9/5 + 32

t = Temperature()
t.celsius = 25
print(int(t.celsius))
print(int(t.fahrenheit))
"""
        js_code = transpile(python_code)
        
        py_result = executor.execute_python(python_code)
        js_result = executor.execute_javascript(js_code)
        
        # Extract numbers from output
        import re
        py_nums = re.findall(r'\d+', py_result["stdout"])
        js_nums = re.findall(r'\d+', js_result["stdout"])
        
        assert py_nums == js_nums

