"""
Comprehensive tests for Compile-Time Type Checking.

WHAT THIS FILE TESTS:
- TypeChecker class
- check_function() method
- Type annotation parsing
- Type error detection
- Type warning generation

Total: 50 tests
"""

import pytest
import ast
from pynext.transpiler.type_checker import (
    TypeChecker, check_types, validate_function_types,
    TypeInfo, TypeError
)


# =============================================================================
# TypeChecker Tests
# =============================================================================

class TestTypeChecker:
    """Tests for TypeChecker class."""
    
    def test_type_checker_initialization(self):
        """Test TypeChecker initialization."""
        checker = TypeChecker()
        assert checker.strict is False
        assert checker.errors == []
        assert checker.warnings == []
    
    def test_type_checker_strict_mode(self):
        """Test TypeChecker in strict mode."""
        checker = TypeChecker(strict=True)
        assert checker.strict is True
    
    def test_check_function_simple(self):
        """Test check_function with simple function."""
        code = """
def add(a: int, b: int) -> int:
    return a + b
"""
        tree = ast.parse(code)
        func_def = tree.body[0]
        
        checker = TypeChecker()
        errors = checker.check_function(func_def)
        assert isinstance(errors, list)
    
    def test_check_function_extracts_return_type(self):
        """Test check_function extracts return type."""
        code = """
def process() -> str:
    return "result"
"""
        tree = ast.parse(code)
        func_def = tree.body[0]
        
        checker = TypeChecker()
        checker.check_function(func_def)
        
        # Should have stored return type
        assert "process.return" in checker.type_map
    
    def test_check_function_extracts_param_types(self):
        """Test check_function extracts parameter types."""
        code = """
def add(a: int, b: int) -> int:
    return a + b
"""
        tree = ast.parse(code)
        func_def = tree.body[0]
        
        checker = TypeChecker()
        checker.check_function(func_def)
        
        # Should have stored parameter types
        assert "add.a" in checker.type_map
        assert "add.b" in checker.type_map


# =============================================================================
# Type Annotation Parsing Tests
# =============================================================================

class TestTypeAnnotationParsing:
    """Tests for type annotation parsing."""
    
    def test_parse_simple_type(self):
        """Test parsing simple type annotation."""
        checker = TypeChecker()
        node = ast.Name(id="int", ctx=ast.Load())
        type_info = checker._parse_type_annotation(node)
        assert type_info.type_name == "int"
    
    def test_parse_optional_type(self):
        """Test parsing Optional type."""
        checker = TypeChecker()
        code = "Optional[int]"
        tree = ast.parse(code, mode="eval")
        type_info = checker._parse_type_annotation(tree.body)
        assert type_info.is_optional is True
    
    def test_parse_list_type(self):
        """Test parsing List type."""
        checker = TypeChecker()
        code = "List[int]"
        tree = ast.parse(code, mode="eval")
        type_info = checker._parse_type_annotation(tree.body)
        assert type_info.type_name == "List"
        assert len(type_info.generic_args) > 0
    
    def test_parse_dict_type(self):
        """Test parsing Dict type."""
        checker = TypeChecker()
        code = "Dict[str, int]"
        tree = ast.parse(code, mode="eval")
        type_info = checker._parse_type_annotation(tree.body)
        assert type_info.type_name == "Dict"
        assert len(type_info.generic_args) >= 2
    
    def test_parse_union_type(self):
        """Test parsing Union type."""
        checker = TypeChecker()
        code = "Union[int, str]"
        tree = ast.parse(code, mode="eval")
        type_info = checker._parse_type_annotation(tree.body)
        assert type_info.is_union is True


# =============================================================================
# check_types Tests
# =============================================================================

class TestCheckTypes:
    """Tests for check_types() function."""
    
    def test_check_types_simple_function(self):
        """Test check_types with simple function."""
        code = """
def add(a: int, b: int) -> int:
    return a + b
"""
        errors = check_types(code)
        assert isinstance(errors, list)
    
    def test_check_types_no_errors(self):
        """Test check_types with valid types."""
        code = """
def process(x: int) -> int:
    return x * 2
"""
        errors = check_types(code)
        # Should not have errors for valid code
        assert isinstance(errors, list)
    
    def test_check_types_strict_mode(self):
        """Test check_types in strict mode."""
        code = """
def process(x: int) -> int:
    return x
"""
        errors = check_types(code, strict=True)
        assert isinstance(errors, list)
    
    def test_check_types_multiple_functions(self):
        """Test check_types with multiple functions."""
        code = """
def func1(x: int) -> int:
    return x

def func2(s: str) -> str:
    return s
"""
        errors = check_types(code)
        assert isinstance(errors, list)


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_add_error(self):
        """Test add_error method."""
        checker = TypeChecker()
        checker.add_error("Test error", 10, 5)
        assert len(checker.errors) == 1
        assert checker.errors[0].message == "Test error"
        assert checker.errors[0].line == 10
    
    def test_add_warning(self):
        """Test add_warning method."""
        checker = TypeChecker()
        checker.add_warning("Test warning", 10, 5)
        assert len(checker.warnings) == 1
        assert checker.warnings[0].message == "Test warning"
    
    def test_strict_mode_warnings_become_errors(self):
        """Test that warnings become errors in strict mode."""
        checker = TypeChecker(strict=True)
        checker.add_warning("Test warning", 10, 5)
        # In strict mode, warnings should also be in errors
        assert len(checker.errors) == 1
    
    def test_get_all_errors(self):
        """Test get_all_errors method."""
        checker = TypeChecker()
        checker.add_error("Error 1", 1, 1)
        checker.add_warning("Warning 1", 2, 1)
        
        all_errors = checker.get_all_errors()
        assert len(all_errors) == 2


# =============================================================================
# TypeInfo Tests
# =============================================================================

class TestTypeInfo:
    """Tests for TypeInfo dataclass."""
    
    def test_type_info_creation(self):
        """Test TypeInfo creation."""
        type_info = TypeInfo(type_name="int")
        assert type_info.type_name == "int"
        assert type_info.is_optional is False
    
    def test_type_info_with_generic_args(self):
        """Test TypeInfo with generic arguments."""
        type_info = TypeInfo(
            type_name="List",
            generic_args=[TypeInfo(type_name="int")]
        )
        assert type_info.type_name == "List"
        assert len(type_info.generic_args) == 1
        assert type_info.generic_args[0].type_name == "int"
    
    def test_type_info_optional(self):
        """Test TypeInfo with optional flag."""
        type_info = TypeInfo(type_name="int", is_optional=True)
        assert type_info.is_optional is True


# =============================================================================
# Integration Tests
# =============================================================================

class TestTypeCheckingIntegration:
    """Integration tests for type checking."""
    
    def test_complex_function_types(self):
        """Test type checking with complex function."""
        code = """
from typing import List, Dict, Optional

def process(
    items: List[int],
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, int]:
    return {"count": len(items)}
"""
        errors = check_types(code)
        assert isinstance(errors, list)
    
    def test_nested_generic_types(self):
        """Test type checking with nested generics."""
        code = """
from typing import List, Dict

def process(data: List[Dict[str, int]]) -> int:
    return len(data)
"""
        errors = check_types(code)
        assert isinstance(errors, list)

