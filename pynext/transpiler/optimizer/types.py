"""
PyNext Transpiler Optimizer - Type Inference Engine

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Infers types for variables and expressions in the IR tree.
This information is used by other optimization passes to make safe decisions.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

To safely elide Python runtime wrappers, we need to know the types:

    x = 5        # Infer: x is int
    y = 3        # Infer: y is int
    z = x + y    # Both int → safe to use native +

Without type inference, we must keep all __py.* wrappers.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    IR Tree
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  TypeInferrer.infer(ir)                                          │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  1. Create root TypeEnv                                          │
    │  2. Walk IR tree, inferring types:                               │
    │     - Literals → direct type                                     │
    │     - Assignments → propagate from RHS                           │
    │     - Operators → compute result type                            │
    │     - Calls → known function return types                        │
    │  3. Return annotated TypeEnv                                     │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

- optimizer/__init__.py: First pass in optimization pipeline
- elision.py: Query types to decide if wrappers can be elided
- inline.py: Query types to select inline strategy

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler import parse
from pynext.transpiler.optimizer.types import infer_types

# Parse some code
ir = parse('''
x = 5
y = "hello"
z = x + 10
valid = z > 0
''')

# Infer types
type_env = infer_types(ir)

type_env.get_type("x")      # → PyType.INT
type_env.get_type("y")      # → PyType.STR
type_env.get_type("z")      # → PyType.INT (int + int)
type_env.get_type("valid")  # → PyType.BOOL (comparison)
```
"""

from __future__ import annotations
from dataclasses import replace
from typing import Optional, Dict, Set

from pynext.transpiler.nodes import (
    JSNode, Program,
    # Statements
    Assignment, AugAssign, If, For, ForUnpack, While, FunctionDef,
    Return, Pass, Break, Continue, Delete, ExprStmt,
    TupleUnpack,
    # Expressions
    Name, Constant, BinOp, UnaryOp, Compare, BoolOp, IfExp,
    Call, Attribute, Subscript, Slice, List, Dict, Tuple,
    Lambda, Await, Starred,
    # Comprehensions
    ListComp, DictComp, SetComp, GeneratorExp,
    # F-Strings
    FString, FormattedValue,
)
from ._internal.type_env import TypeEnv, PyType
from ._internal.visitor import IRVisitor


# =============================================================================
# PUBLIC API
# =============================================================================

def infer_types(ir: Program) -> TypeEnv:
    """
    Infer types for all variables in the IR.
    
    Returns a TypeEnv with inferred types for all variables.
    Unknown types default to PyType.ANY (conservative).
    
    Example:
        ir = parse("x = 5; y = x + 1")
        env = infer_types(ir)
        env.get_type("x")  # → PyType.INT
        env.get_type("y")  # → PyType.INT
    """
    inferrer = TypeInferrer()
    inferrer.infer_program(ir)
    return inferrer.env


def infer_expr_type(expr: JSNode, env: TypeEnv) -> PyType:
    """
    Infer the type of an expression given a type environment.
    
    Example:
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        
        expr = BinOp(left=Name(id="x"), op="add", right=Constant(value=5))
        infer_expr_type(expr, env)  # → PyType.INT
    """
    inferrer = TypeInferrer(env)
    return inferrer._infer_expr(expr)


# =============================================================================
# KNOWN FUNCTION RETURN TYPES
# =============================================================================

# Built-in functions with known return types
BUILTIN_RETURN_TYPES: Dict[str, PyType] = {
    # Integer-returning functions
    "len": PyType.INT,
    "int": PyType.INT,
    "abs": PyType.INT,  # abs(int) → int (conservative)
    "ord": PyType.INT,
    "hash": PyType.INT,
    "id": PyType.INT,
    
    # Float-returning functions
    "float": PyType.FLOAT,
    "round": PyType.FLOAT,
    
    # String-returning functions
    "str": PyType.STR,
    "chr": PyType.STR,
    "repr": PyType.STR,
    "ascii": PyType.STR,
    "format": PyType.STR,
    "hex": PyType.STR,
    "oct": PyType.STR,
    "bin": PyType.STR,
    
    # Boolean-returning functions
    "bool": PyType.BOOL,
    "isinstance": PyType.BOOL,
    "issubclass": PyType.BOOL,
    "callable": PyType.BOOL,
    "hasattr": PyType.BOOL,
    "any": PyType.BOOL,
    "all": PyType.BOOL,
    
    # Collection-returning functions
    "list": PyType.LIST,
    "dict": PyType.DICT,
    "set": PyType.SET,
    "tuple": PyType.TUPLE,
    "sorted": PyType.LIST,
    "reversed": PyType.LIST,
    "enumerate": PyType.LIST,
    "zip": PyType.LIST,
    "range": PyType.LIST,
    "filter": PyType.LIST,
    "map": PyType.LIST,
}

# String method return types
STRING_METHOD_TYPES: Dict[str, PyType] = {
    # String-returning methods
    "upper": PyType.STR,
    "lower": PyType.STR,
    "capitalize": PyType.STR,
    "title": PyType.STR,
    "strip": PyType.STR,
    "lstrip": PyType.STR,
    "rstrip": PyType.STR,
    "replace": PyType.STR,
    "format": PyType.STR,
    "join": PyType.STR,
    "center": PyType.STR,
    "ljust": PyType.STR,
    "rjust": PyType.STR,
    "zfill": PyType.STR,
    "swapcase": PyType.STR,
    "expandtabs": PyType.STR,
    
    # Integer-returning methods
    "count": PyType.INT,
    "find": PyType.INT,
    "rfind": PyType.INT,
    "index": PyType.INT,
    "rindex": PyType.INT,
    
    # Boolean-returning methods
    "startswith": PyType.BOOL,
    "endswith": PyType.BOOL,
    "isalpha": PyType.BOOL,
    "isdigit": PyType.BOOL,
    "isalnum": PyType.BOOL,
    "isspace": PyType.BOOL,
    "isupper": PyType.BOOL,
    "islower": PyType.BOOL,
    "isnumeric": PyType.BOOL,
    "isdecimal": PyType.BOOL,
    "isidentifier": PyType.BOOL,
    
    # List-returning methods
    "split": PyType.LIST,
    "rsplit": PyType.LIST,
    "splitlines": PyType.LIST,
    "partition": PyType.TUPLE,
    "rpartition": PyType.TUPLE,
}

# List method return types
LIST_METHOD_TYPES: Dict[str, PyType] = {
    "copy": PyType.LIST,
    "count": PyType.INT,
    "index": PyType.INT,
    "pop": PyType.ANY,  # Element type unknown
}

# Dict method return types
DICT_METHOD_TYPES: Dict[str, PyType] = {
    "keys": PyType.LIST,
    "values": PyType.LIST,
    "items": PyType.LIST,
    "get": PyType.ANY,
    "pop": PyType.ANY,
    "setdefault": PyType.ANY,
    "copy": PyType.DICT,
}


# =============================================================================
# TYPE INFERRER
# =============================================================================

class TypeInferrer(IRVisitor):
    """
    Infers types for variables and expressions.
    
    Walks the IR tree, tracking variable assignments and inferring types.
    """
    
    def __init__(self, env: Optional[TypeEnv] = None):
        self.env = env or TypeEnv()
        self._current_scope = self.env
        # COMPREHENSIVE FIX: Track variables that were assigned from class instantiations
        # These should NOT have their types inferred from PyType.ANY in augmented assignments
        # This preserves operator overloading for custom classes
        self._class_instances: Set[str] = set()
    
    def infer_program(self, program: Program) -> None:
        """Infer types for all statements in a program."""
        for stmt in program.body:
            self._infer_stmt(stmt)
    
    def _infer_stmt(self, stmt: JSNode) -> None:
        """Infer types from a statement."""
        if isinstance(stmt, Assignment):
            self._infer_assignment(stmt)
        elif isinstance(stmt, AugAssign):
            self._infer_aug_assign(stmt)
        elif isinstance(stmt, TupleUnpack):
            self._infer_tuple_unpack(stmt)
        elif isinstance(stmt, If):
            self._infer_if(stmt)
        elif isinstance(stmt, For):
            self._infer_for(stmt)
        elif isinstance(stmt, ForUnpack):
            self._infer_for_unpack(stmt)
        elif isinstance(stmt, While):
            self._infer_while(stmt)
        elif isinstance(stmt, FunctionDef):
            self._infer_function(stmt)
        elif isinstance(stmt, ExprStmt):
            # Just evaluate expression type (for side effects)
            self._infer_expr(stmt.value)
        # Other statements don't introduce types
    
    def _infer_assignment(self, node: Assignment) -> None:
        """Infer type from assignment: x = value."""
        value_type = self._infer_expr(node.value)
        
        # COMPREHENSIVE FIX: Track if this assignment is from a class instantiation
        # If the value is a Call that returns PyType.ANY, it's likely a class instantiation
        # We need to track this so we don't incorrectly infer types later in augmented assignments
        if isinstance(node.value, Call) and value_type == PyType.ANY:
            # Check if it's NOT a builtin function (builtins return known types)
            # If it's a Call to a Name (like Counter(5)), it's a class instantiation
            if isinstance(node.value.func, Name):
                # This is likely a class instantiation, not a builtin
                # Mark this variable so we don't infer from PyType.ANY later
                self._class_instances.add(node.target)
        
        self._current_scope.set_type(node.target, value_type)
    
    def _infer_aug_assign(self, node: AugAssign) -> None:
        """Infer type from augmented assignment: x += value."""
        # Get current type of target
        target_type = self._current_scope.get_type(node.target)
        value_type = self._infer_expr(node.value)
        
        # COMPREHENSIVE FIX: Don't infer from PyType.ANY if this variable came from a class instantiation
        # This prevents incorrectly inferring custom class instances as primitives
        # Example: c = Counter(5)  # c is PyType.ANY (class instance)
        #          c += 10          # Should NOT infer c as PyType.INT (preserves operator overloading)
        is_class_instance = node.target in self._class_instances
        
        # Phase 33.3: Enhanced type inference for isolated statements
        # If target type is unknown (ANY), infer from RHS for numeric/string operations
        # BUT: Only if it's NOT a class instance (preserve operator overloading for custom classes)
        # This allows the emitter to use native JS operators for common cases
        # while still preserving operator overloading for custom classes
        if target_type == PyType.ANY and not is_class_instance:
            # For arithmetic operations with numeric RHS, infer numeric type
            # This is safe for variables that are truly unknown (not class instances)
            if node.op in ("add", "sub", "mul", "div", "floordiv", "mod", "pow"):
                if value_type.is_numeric():
                    # Use the RHS type as the target type for inference
                    target_type = value_type
                elif value_type == PyType.STR and node.op == "add":
                    # String concatenation
                    target_type = PyType.STR
                elif value_type == PyType.LIST and node.op == "add":
                    # List concatenation
                    target_type = PyType.LIST
            # For bitwise operations, infer INT type
            elif node.op in ("lshift", "rshift", "bitor", "bitxor", "bitand"):
                if value_type.is_numeric():
                    target_type = PyType.INT
        
        # Result type depends on operation
        # NOTE: If target_type is still PyType.ANY (class instance), the result might also be ANY
        # This is correct - we don't know what __iadd__ returns, so we stay conservative
        result_type = self._infer_binop_type(node.op, target_type, value_type)
        self._current_scope.set_type(node.target, result_type)
    
    def _infer_tuple_unpack(self, node: TupleUnpack) -> None:
        """Infer types from tuple unpacking: a, b = value."""
        # We can't know individual element types without more info
        # Mark all targets as ANY
        for target in node.targets:
            self._current_scope.set_type(target, PyType.ANY)
    
    def _infer_if(self, node: If) -> None:
        """Infer types in if/elif/else branches."""
        # Infer test expression (for side effects)
        self._infer_expr(node.test)
        
        # Create copies for branch analysis
        then_env = self._current_scope.copy()
        else_env = self._current_scope.copy()
        
        # Analyze then branch
        old_scope = self._current_scope
        self._current_scope = then_env
        for stmt in node.body:
            self._infer_stmt(stmt)
        
        # Analyze else branch
        self._current_scope = else_env
        for stmt in node.orelse:
            self._infer_stmt(stmt)
        
        # Merge results back
        self._current_scope = old_scope
        self._current_scope.merge_types(then_env)
        self._current_scope.merge_types(else_env)
    
    def _infer_for(self, node: For) -> None:
        """Infer types in for loop."""
        # Infer iterator type
        iter_type = self._infer_expr(node.iter)
        
        # Loop variable type depends on what we're iterating
        if iter_type == PyType.STR:
            elem_type = PyType.STR  # Iterating string → single chars (strings)
        elif iter_type == PyType.LIST:
            elem_type = PyType.ANY  # Can't know element type
        elif iter_type == PyType.DICT:
            elem_type = PyType.ANY  # Dict keys
        else:
            elem_type = PyType.ANY
        
        # For range() loops, we know it's int
        if isinstance(node.iter, Call):
            if isinstance(node.iter.func, Name) and node.iter.func.id == "range":
                elem_type = PyType.INT
        
        self._current_scope.set_type(node.target, elem_type)
        
        # Infer body
        for stmt in node.body:
            self._infer_stmt(stmt)
    
    def _infer_for_unpack(self, node: ForUnpack) -> None:
        """Infer types in for loop with unpacking."""
        # Mark all targets as ANY
        for target in node.targets:
            self._current_scope.set_type(target, PyType.ANY)
        
        # Infer body
        for stmt in node.body:
            self._infer_stmt(stmt)
    
    def _infer_while(self, node: While) -> None:
        """Infer types in while loop."""
        self._infer_expr(node.test)
        for stmt in node.body:
            self._infer_stmt(stmt)
    
    def _infer_function(self, node: FunctionDef) -> None:
        """Infer types in function definition."""
        # Create child scope for function
        func_scope = self._current_scope.child_scope(node.name)
        
        # Parameters are ANY by default (no type hints support yet)
        for arg in node.args:
            if isinstance(arg, tuple):
                # (name, default) tuple
                func_scope.set_type(arg[0], PyType.ANY)
            else:
                func_scope.set_type(arg, PyType.ANY)
        
        # Infer body in function scope
        old_scope = self._current_scope
        self._current_scope = func_scope
        for stmt in node.body:
            self._infer_stmt(stmt)
        self._current_scope = old_scope
        
        # Function itself has FUNC type
        self._current_scope.set_type(node.name, PyType.FUNC)
    
    def _infer_expr(self, expr: JSNode) -> PyType:
        """Infer the type of an expression."""
        if expr is None:
            return PyType.NONE
        
        if isinstance(expr, Constant):
            return self._infer_constant(expr)
        elif isinstance(expr, Name):
            return self._current_scope.get_type(expr.id)
        elif isinstance(expr, BinOp):
            return self._infer_binop(expr)
        elif isinstance(expr, UnaryOp):
            return self._infer_unaryop(expr)
        elif isinstance(expr, Compare):
            return PyType.BOOL  # Comparisons always return bool
        elif isinstance(expr, BoolOp):
            return self._infer_boolop(expr)
        elif isinstance(expr, IfExp):
            return self._infer_ifexp(expr)
        elif isinstance(expr, Call):
            return self._infer_call(expr)
        elif isinstance(expr, Attribute):
            return self._infer_attribute(expr)
        elif isinstance(expr, Subscript):
            return self._infer_subscript(expr)
        elif isinstance(expr, List):
            return PyType.LIST
        elif isinstance(expr, Dict):
            return PyType.DICT
        elif isinstance(expr, Tuple):
            return PyType.TUPLE
        elif isinstance(expr, Lambda):
            return PyType.LAMBDA
        elif isinstance(expr, ListComp):
            return PyType.LIST
        elif isinstance(expr, DictComp):
            return PyType.DICT
        elif isinstance(expr, SetComp):
            return PyType.SET
        elif isinstance(expr, GeneratorExp):
            return PyType.LIST  # Generators are consumed as lists
        elif isinstance(expr, Await):
            return PyType.ANY  # Can't know async result type
        elif isinstance(expr, FString):
            return PyType.STR  # F-strings are always strings
        else:
            return PyType.ANY
    
    def _infer_constant(self, node: Constant) -> PyType:
        """Infer type from a constant value."""
        value = node.value
        if value is None:
            return PyType.NONE
        elif isinstance(value, bool):
            return PyType.BOOL
        elif isinstance(value, int):
            return PyType.INT
        elif isinstance(value, float):
            return PyType.FLOAT
        elif isinstance(value, str):
            return PyType.STR
        else:
            return PyType.ANY
    
    def _infer_binop(self, node: BinOp) -> PyType:
        """Infer type from binary operation."""
        left_type = self._infer_expr(node.left)
        right_type = self._infer_expr(node.right)
        return self._infer_binop_type(node.op, left_type, right_type)
    
    def _infer_binop_type(self, op: str, left: PyType, right: PyType) -> PyType:
        """Infer result type of binary operation."""
        # Arithmetic operations
        if op in ("add", "sub", "mul", "div", "floordiv", "mod", "pow"):
            # String concatenation/repetition
            if op == "add" and left == PyType.STR and right == PyType.STR:
                return PyType.STR
            if op == "mul":
                if left == PyType.STR and right.is_numeric():
                    return PyType.STR
                if right == PyType.STR and left.is_numeric():
                    return PyType.STR
                # List repetition
                if left == PyType.LIST and right.is_numeric():
                    return PyType.LIST
            
            # List concatenation
            if op == "add" and left == PyType.LIST and right == PyType.LIST:
                return PyType.LIST
            
            # Numeric operations
            if left.is_numeric() and right.is_numeric():
                if op == "div":
                    return PyType.FLOAT  # Division always returns float
                if left == PyType.FLOAT or right == PyType.FLOAT:
                    return PyType.FLOAT
                return PyType.INT
            
            return PyType.ANY
        
        # Bitwise operations (always int)
        if op in ("lshift", "rshift", "bitor", "bitxor", "bitand"):
            return PyType.INT
        
        return PyType.ANY
    
    def _infer_unaryop(self, node: UnaryOp) -> PyType:
        """Infer type from unary operation."""
        operand_type = self._infer_expr(node.operand)
        
        if node.op == "not":
            return PyType.BOOL
        elif node.op == "invert":
            return PyType.INT
        elif node.op in ("pos", "neg"):
            # Unary +/- on numeric returns numeric
            return operand_type if operand_type.is_numeric() else PyType.ANY
        
        return PyType.ANY
    
    def _infer_boolop(self, node: BoolOp) -> PyType:
        """Infer type from boolean operation (and/or)."""
        # and/or return one of their operands, but we treat as bool for simplicity
        # This is conservative but safe for optimization purposes
        return PyType.BOOL
    
    def _infer_ifexp(self, node: IfExp) -> PyType:
        """Infer type from conditional expression: a if cond else b."""
        then_type = self._infer_expr(node.body)
        else_type = self._infer_expr(node.orelse)
        
        if then_type == else_type:
            return then_type
        elif then_type.is_numeric() and else_type.is_numeric():
            return PyType.NUMBER
        else:
            return PyType.ANY
    
    def _infer_call(self, node: Call) -> PyType:
        """Infer type from function call."""
        # Check for built-in function calls
        if isinstance(node.func, Name):
            func_name = node.func.id
            if func_name in BUILTIN_RETURN_TYPES:
                return BUILTIN_RETURN_TYPES[func_name]
        
        # Check for method calls
        if isinstance(node.func, Attribute):
            method_name = node.func.attr
            obj_type = self._infer_expr(node.func.value)
            
            # String methods
            if obj_type == PyType.STR and method_name in STRING_METHOD_TYPES:
                return STRING_METHOD_TYPES[method_name]
            
            # List methods
            if obj_type == PyType.LIST and method_name in LIST_METHOD_TYPES:
                return LIST_METHOD_TYPES[method_name]
            
            # Dict methods
            if obj_type == PyType.DICT and method_name in DICT_METHOD_TYPES:
                return DICT_METHOD_TYPES[method_name]
        
        return PyType.ANY
    
    def _infer_attribute(self, node: Attribute) -> PyType:
        """Infer type from attribute access."""
        # Most attribute access results in unknown type
        # Could be extended with known object types
        return PyType.ANY
    
    def _infer_subscript(self, node: Subscript) -> PyType:
        """Infer type from subscript access: items[0]."""
        obj_type = self._infer_expr(node.value)
        
        # String subscript returns string
        if obj_type == PyType.STR:
            if isinstance(node.slice, Slice):
                return PyType.STR  # Slice of string is string
            return PyType.STR  # Single char is string
        
        # List/Tuple subscript - unknown element type
        if obj_type == PyType.LIST:
            if isinstance(node.slice, Slice):
                return PyType.LIST
            return PyType.ANY
        
        if obj_type == PyType.TUPLE:
            if isinstance(node.slice, Slice):
                return PyType.TUPLE
            return PyType.ANY
        
        # Dict subscript - unknown value type
        if obj_type == PyType.DICT:
            return PyType.ANY
        
        return PyType.ANY


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_comparison(node: JSNode) -> bool:
    """Check if a node is a comparison expression (always bool)."""
    return isinstance(node, Compare)


def is_bool_literal(node: JSNode) -> bool:
    """Check if a node is a boolean literal."""
    return isinstance(node, Constant) and isinstance(node.value, bool)


def is_int_literal(node: JSNode) -> bool:
    """Check if a node is an integer literal."""
    return isinstance(node, Constant) and isinstance(node.value, int) and not isinstance(node.value, bool)


def is_positive_int_literal(node: JSNode) -> bool:
    """Check if a node is a non-negative integer literal."""
    return is_int_literal(node) and node.value >= 0


def is_str_literal(node: JSNode) -> bool:
    """Check if a node is a string literal."""
    return isinstance(node, Constant) and isinstance(node.value, str)


def get_literal_value(node: JSNode) -> any:
    """Get the value of a literal, or None if not a literal."""
    if isinstance(node, Constant):
        return node.value
    return None
