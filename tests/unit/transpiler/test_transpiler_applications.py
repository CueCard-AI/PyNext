"""
Phase 33.1: Transpiler Application Unit Tests

Unit tests for mini applications that exercise the transpiler
with realistic code patterns. These tests verify that transpiled
JavaScript produces equivalent results to Python code.

These tests run as part of the unit test suite and appear in GitHub Actions.
"""

import pytest
import shutil
import re
from pathlib import Path

from .harness.executor import MiniAppHarness
from .applications import (
    calculator,
    todo,
    data_processor,
    game,
    math_library,
    event_system,
    string_ops,
    list_ops,
    dict_ops,
    nested_structures,
    control_flow,
    function_composition,
    class_hierarchy,
    multiple_inheritance,
    properties,
    static_class_methods,
    exception_handling,
    generators,
    complex_app,
)


@pytest.fixture
def harness():
    """Create a mini app harness."""
    h = MiniAppHarness()
    yield h
    shutil.rmtree(h.temp_dir, ignore_errors=True)


# =============================================================================
# CALCULATOR APPLICATION TESTS
# =============================================================================

class TestCalculator:
    """Calculator application unit tests."""
    
    def test_calculator_basic(self, harness):
        """Test calculator application produces equivalent results."""
        result = harness.run_mini_app(calculator.CALCULATOR_CODE)
        
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: {result['javascript']['stderr']}"
        
        # Extract numeric values for comparison
        py_nums = re.findall(r'\d+', result["python"]["stdout"])
        js_nums = re.findall(r'\d+', result["javascript"]["stdout"])
        
        assert len(py_nums) > 0, "Python produced no output"
        assert len(js_nums) > 0, f"JS produced no output: {result['javascript']}"
        assert set(py_nums) == set(js_nums), f"Python: {py_nums}, JS: {js_nums}"


# =============================================================================
# TODO APPLICATION TESTS
# =============================================================================

class TestTodo:
    """Todo application unit tests."""
    
    def test_todo_app(self, harness):
        """Test todo application produces equivalent results."""
        result = harness.run_mini_app(todo.TODO_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# DATA PROCESSOR TESTS
# =============================================================================

class TestDataProcessor:
    """Data processor application unit tests."""
    
    def test_data_processor(self, harness):
        """Test data processor produces equivalent results."""
        result = harness.run_mini_app(data_processor.DATA_PROCESSOR_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# GAME APPLICATION TESTS
# =============================================================================

class TestGame:
    """Game application unit tests."""
    
    def test_game_app(self, harness):
        """Test game application produces equivalent results."""
        result = harness.run_mini_app(game.GAME_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# MATH LIBRARY TESTS
# =============================================================================

class TestMathLibrary:
    """Math library application unit tests."""
    
    def test_math_library(self, harness):
        """Test math library produces equivalent results."""
        result = harness.run_mini_app(math_library.MATH_LIBRARY_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# EVENT SYSTEM TESTS
# =============================================================================

class TestEventSystem:
    """Event system application unit tests."""
    
    def test_event_system(self, harness):
        """Test event system produces equivalent results."""
        result = harness.run_mini_app(event_system.EVENT_SYSTEM_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# STRING OPERATIONS TESTS
# =============================================================================

class TestStringOperations:
    """String operations application unit tests."""
    
    def test_string_operations(self, harness):
        """Test string operations produce equivalent results."""
        result = harness.run_mini_app(string_ops.STRING_OPS_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# LIST OPERATIONS TESTS
# =============================================================================

class TestListOperations:
    """List operations application unit tests."""
    
    def test_list_operations(self, harness):
        """Test list operations produce equivalent results."""
        result = harness.run_mini_app(list_ops.LIST_OPS_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# DICTIONARY OPERATIONS TESTS
# =============================================================================

class TestDictionaryOperations:
    """Dictionary operations application unit tests."""
    
    def test_dictionary_operations(self, harness):
        """Test dictionary operations produce equivalent results."""
        result = harness.run_mini_app(dict_ops.DICT_OPS_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# NESTED STRUCTURES TESTS
# =============================================================================

class TestNestedStructures:
    """Nested structures application unit tests."""
    
    def test_nested_structures(self, harness):
        """Test nested structures produce equivalent results."""
        result = harness.run_mini_app(nested_structures.NESTED_STRUCTURES_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# CONTROL FLOW TESTS
# =============================================================================

class TestControlFlow:
    """Control flow application unit tests."""
    
    def test_control_flow(self, harness):
        """Test control flow produces equivalent results."""
        result = harness.run_mini_app(control_flow.CONTROL_FLOW_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# FUNCTION COMPOSITION TESTS
# =============================================================================

class TestFunctionComposition:
    """Function composition application unit tests."""
    
    def test_function_composition(self, harness):
        """Test function composition produces equivalent results."""
        result = harness.run_mini_app(function_composition.FUNCTION_COMPOSITION_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# CLASS HIERARCHY TESTS
# =============================================================================

class TestClassHierarchy:
    """Class hierarchy application unit tests."""
    
    def test_class_hierarchy(self, harness):
        """Test class hierarchy produces equivalent results."""
        result = harness.run_mini_app(class_hierarchy.CLASS_HIERARCHY_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# MULTIPLE INHERITANCE TESTS
# =============================================================================

class TestMultipleInheritance:
    """Multiple inheritance application unit tests."""
    
    def test_multiple_inheritance(self, harness):
        """Test multiple inheritance produces equivalent results."""
        result = harness.run_mini_app(multiple_inheritance.MULTIPLE_INHERITANCE_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# PROPERTIES TESTS
# =============================================================================

class TestProperties:
    """Properties application unit tests."""
    
    def test_properties(self, harness):
        """Test properties produce equivalent results."""
        result = harness.run_mini_app(properties.PROPERTIES_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# STATIC AND CLASS METHODS TESTS
# =============================================================================

class TestStaticClassMethods:
    """Static and class methods application unit tests."""
    
    def test_static_class_methods(self, harness):
        """Test static and class methods produce equivalent results."""
        result = harness.run_mini_app(static_class_methods.STATIC_CLASS_METHODS_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# EXCEPTION HANDLING TESTS
# =============================================================================

class TestExceptionHandling:
    """Exception handling application unit tests."""
    
    def test_exception_handling(self, harness):
        """Test exception handling produces equivalent results."""
        result = harness.run_mini_app(exception_handling.EXCEPTION_HANDLING_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# GENERATORS TESTS
# =============================================================================

class TestGenerators:
    """Generators application unit tests."""
    
    def test_generators(self, harness):
        """Test generators produce equivalent results."""
        result = harness.run_mini_app(generators.GENERATORS_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


# =============================================================================
# COMPLEX APPLICATION TESTS
# =============================================================================

class TestComplexApp:
    """Complex application unit tests."""
    
    def test_complex_app(self, harness):
        """Test complex application produces equivalent results."""
        result = harness.run_mini_app(complex_app.COMPLEX_APP_CODE)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0

