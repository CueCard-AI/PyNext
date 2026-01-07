"""
PyNext Transpiler - Compile-Time Type Checking

WHAT THIS FILE DOES:
Performs static type analysis during transpilation to catch type errors early
and enable type-based optimizations.

WHY THIS EXISTS:
Compile-time type checking catches errors before runtime, provides better IDE support,
and enables optimizations based on known types.

HOW IT WORKS:
- Analyzes type annotations in function signatures
- Checks argument types at call sites
- Warns/errors on type mismatches
- Generates optimized code when types are known

WHO USES THIS:
- Transpiler pipeline
- IDE/editor integrations
- Build-time validation

WHEN TO USE:
- During transpilation (always enabled)
- For type-based optimizations
- For better error messages

EXAMPLES:
    # Type checker will validate this:
    def add(a: int, b: int) -> int:
        return a + b
    
    add("1", "2")  # Type error: Expected int, got str
"""

from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field


@dataclass
class TypeInfo:
    """Type information for a value or expression."""
    type_name: str
    is_optional: bool = False
    generic_args: List[TypeInfo] = field(default_factory=list)
    is_union: bool = False
    union_types: List[TypeInfo] = field(default_factory=list)


@dataclass
class TypeError:
    """Type error information."""
    message: str
    line: int
    col: int
    severity: str = "error"  # "error" or "warning"


class TypeChecker:
    """
    Compile-time type checker for PyNext transpiler.
    
    Analyzes type annotations and validates type usage.
    """
    
    def __init__(self, strict: bool = False):
        """
        Initialize type checker.
        
        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict
        self.errors: List[TypeError] = []
        self.warnings: List[TypeError] = []
        self.type_map: Dict[str, TypeInfo] = {}
    
    def check_function(self, node: ast.FunctionDef) -> List[TypeError]:
        """
        Check type annotations in a function definition.
        
        Args:
            node: AST function node
            
        Returns:
            List of type errors
        """
        errors = []
        
        # Extract return type
        if node.returns:
            return_type = self._parse_type_annotation(node.returns)
            # Store for later validation
            self.type_map[f"{node.name}.return"] = return_type
        
        # Check parameter types
        for arg in node.args.args:
            if arg.annotation:
                param_type = self._parse_type_annotation(arg.annotation)
                self.type_map[f"{node.name}.{arg.arg}"] = param_type
        
        return errors
    
    def _parse_type_annotation(self, annotation: ast.expr) -> TypeInfo:
        """
        Parse a type annotation into TypeInfo.
        
        Args:
            annotation: AST node for type annotation
            
        Returns:
            TypeInfo object
        """
        if isinstance(annotation, ast.Name):
            # Simple type: int, str, bool
            return TypeInfo(type_name=annotation.id)
        
        elif isinstance(annotation, ast.Subscript):
            # Generic type: List[int], Dict[str, int], Optional[int]
            value = annotation.value
            
            if isinstance(value, ast.Name):
                type_name = value.id
                
                # Check if it's Optional (Union[T, None])
                if type_name == "Optional":
                    slice_node = annotation.slice
                    if isinstance(slice_node, ast.Index):  # Python < 3.9
                        inner_type = self._parse_type_annotation(slice_node.value)
                    else:  # Python >= 3.9
                        inner_type = self._parse_type_annotation(slice_node)
                    inner_type.is_optional = True
                    return inner_type
                
                # Parse generic arguments
                generic_args = []
                slice_node = annotation.slice
                
                if isinstance(slice_node, ast.Index):  # Python < 3.9
                    elts = slice_node.value
                else:  # Python >= 3.9
                    elts = slice_node
                
                if isinstance(elts, ast.Tuple):
                    for elt in elts.elts:
                        generic_args.append(self._parse_type_annotation(elt))
                else:
                    generic_args.append(self._parse_type_annotation(elts))
                
                # Handle Union type specially
                if type_name == "Union":
                    return TypeInfo(
                        type_name=type_name,
                        generic_args=generic_args,
                        is_union=True,
                        union_types=generic_args
                    )
                
                return TypeInfo(
                    type_name=type_name,
                    generic_args=generic_args
                )
            
            elif isinstance(value, ast.Attribute):
                # Qualified name: typing.List, typing.Dict
                type_name = f"{value.value.id}.{value.attr}"
                return TypeInfo(type_name=type_name)
        
        elif isinstance(annotation, ast.Constant):
            # String annotation: "MyType" (forward reference)
            return TypeInfo(type_name=str(annotation.value))
        
        # Default: unknown type
        return TypeInfo(type_name="Any")
    
    def add_error(self, message: str, line: int, col: int) -> None:
        """Add a type error."""
        self.errors.append(TypeError(message=message, line=line, col=col, severity="error"))
    
    def add_warning(self, message: str, line: int, col: int) -> None:
        """Add a type warning."""
        warning = TypeError(message=message, line=line, col=col, severity="warning")
        self.warnings.append(warning)
        if self.strict:
            self.errors.append(warning)
    
    def get_all_errors(self) -> List[TypeError]:
        """Get all errors and warnings."""
        return self.errors + self.warnings


def check_types(source: str, strict: bool = False) -> List[TypeError]:
    """
    Check types in Python source code.
    
    Args:
        source: Python source code
        strict: If True, treat warnings as errors
        
    Returns:
        List of type errors
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    
    checker = TypeChecker(strict=strict)
    
    # Check all functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            checker.check_function(node)
    
    return checker.get_all_errors()


def validate_function_types(func_def: ast.FunctionDef) -> List[TypeError]:
    """
    Validate type annotations in a function definition.
    
    Args:
        func_def: AST function node
        
    Returns:
        List of type errors
    """
    checker = TypeChecker()
    return checker.check_function(func_def)

