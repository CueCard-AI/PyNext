"""
Phase 18.7 - Type Inference Edge Cases

Tests for edge cases and complex scenarios in type inference.
"""

import pytest
from pynext.transpiler import parse
from pynext.transpiler.nodes import (
    Program, Assignment, If, For, ForUnpack, While, FunctionDef,
    Return, ExprStmt, Try, ExceptHandler,
    Name, Constant, Call, Attribute, Compare, BinOp, UnaryOp,
    List as ListNode, Dict as DictNode, Lambda,
)
from pynext.transpiler.optimizer import infer_types
from pynext.transpiler.optimizer._internal.type_env import TypeEnv, PyType


# =============================================================================
# 1. CONDITIONAL TYPE NARROWING
# =============================================================================

class TestConditionalTypeNarrowing:
    """Test type changes across conditional branches."""
    
    def test_type_after_if_branch_merge(self):
        """Types should merge after if/else branches."""
        ir = parse('''
if condition:
    x = 5
else:
    x = "hello"
''')
        env = infer_types(ir)
        # After merge, x could be int or str - should be ANY
        assert env.get_type("x") == PyType.ANY
    
    def test_type_defined_only_in_if(self):
        """Variable defined only in one branch."""
        ir = parse('''
if condition:
    x = 5
''')
        env = infer_types(ir)
        # x might not be defined - should be in env but could be ANY
        # Actually, the parser adds it unconditionally
        x_type = env.get_type("x")
        # Could be INT (if defined) or ANY (if uncertain)
        assert x_type in (PyType.INT, PyType.ANY)
    
    def test_type_both_branches_same(self):
        """Same type in both branches preserves type."""
        ir = parse('''
if condition:
    x = 5
else:
    x = 10
''')
        env = infer_types(ir)
        # Both branches assign int
        assert env.get_type("x") == PyType.INT
    
    def test_nested_conditionals(self):
        """Nested if statements."""
        ir = parse('''
if a:
    if b:
        x = 5
    else:
        x = 10
else:
    x = 15
''')
        env = infer_types(ir)
        # All branches assign int
        assert env.get_type("x") == PyType.INT
    
    def test_elif_chain_types(self):
        """Type inference through elif chain."""
        ir = parse('''
if a > 0:
    x = 1
elif a < 0:
    x = -1
else:
    x = 0
''')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT


# =============================================================================
# 2. LOOP TYPE INFERENCE
# =============================================================================

class TestLoopTypeInference:
    """Test type inference in loops."""
    
    def test_for_loop_variable(self):
        """Loop variable type from iterable."""
        ir = parse('''
for i in range(10):
    x = i
''')
        env = infer_types(ir)
        # range produces ints
        assert env.get_type("i") == PyType.INT
    
    def test_for_loop_body_type(self):
        """Variables defined in loop body."""
        ir = parse('''
for i in range(10):
    x = i * 2
''')
        env = infer_types(ir)
        # x = int * int = int
        assert env.get_type("x") == PyType.INT
    
    def test_accumulator_pattern(self):
        """Accumulator pattern keeps type."""
        ir = parse('''
total = 0
for i in range(10):
    total = total + i
''')
        env = infer_types(ir)
        # total stays int
        assert env.get_type("total") == PyType.INT
    
    def test_while_loop_body(self):
        """Type in while loop body."""
        ir = parse('''
x = 0
while x < 10:
    x = x + 1
''')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_for_unpack(self):
        """Tuple unpacking in for loop."""
        ir = parse('''
for i, x in enumerate(items):
    y = i
''')
        env = infer_types(ir)
        # NOTE: Current implementation doesn't track enumerate tuple types
        # This is a known limitation - unpacked variables are ANY
        assert env.get_type("i") == PyType.ANY


# =============================================================================
# 3. FUNCTION SCOPE
# =============================================================================

class TestFunctionScope:
    """Test type inference in function scopes."""
    
    def test_function_params_are_any(self):
        """Function parameters without annotation are ANY."""
        ir = parse('''
def foo(x, y):
    z = x + y
''')
        env = infer_types(ir)
        # Parameters without hints are ANY
        # z = ANY + ANY = ANY
        assert env.get_type("z") == PyType.ANY
    
    def test_function_local_scope(self):
        """Local variables in function."""
        ir = parse('''
x = 5
def foo():
    y = 10
    return y
''')
        env = infer_types(ir)
        # x is in global scope
        assert env.get_type("x") == PyType.INT
    
    def test_function_return_type(self):
        """Function return type inference."""
        ir = parse('''
def get_count():
    return 5
''')
        env = infer_types(ir)
        # Function itself is FUNC type
        assert env.get_type("get_count") == PyType.FUNC
    
    def test_nested_function(self):
        """Nested function definitions."""
        ir = parse('''
def outer():
    x = 5
    def inner():
        y = 10
        return y
    return inner()
''')
        env = infer_types(ir)
        assert env.get_type("outer") == PyType.FUNC
    
    def test_lambda_type(self):
        """Lambda expression type."""
        ir = parse('f = lambda x: x + 1')
        env = infer_types(ir)
        assert env.get_type("f") == PyType.LAMBDA


# =============================================================================
# 4. COLLECTION OPERATIONS
# =============================================================================

class TestCollectionOperations:
    """Test type inference for collection operations."""
    
    def test_list_literal_type(self):
        """List literal type."""
        ir = parse('items = [1, 2, 3]')
        env = infer_types(ir)
        assert env.get_type("items") == PyType.LIST
    
    def test_dict_literal_type(self):
        """Dict literal type."""
        ir = parse('data = {"a": 1, "b": 2}')
        env = infer_types(ir)
        assert env.get_type("data") == PyType.DICT
    
    def test_set_from_constructor(self):
        """Set from constructor type."""
        # Set literals not supported in parser, use constructor
        ir = parse('unique = set([1, 2, 3])')
        env = infer_types(ir)
        # set() call returns SET type
        assert env.get_type("unique") == PyType.SET
    
    def test_tuple_literal_type(self):
        """Tuple literal type."""
        ir = parse('coords = (1, 2)')
        env = infer_types(ir)
        assert env.get_type("coords") == PyType.TUPLE
    
    def test_list_append_preserves_type(self):
        """List after append is still LIST."""
        ir = parse('''
items = []
items.append(1)
''')
        env = infer_types(ir)
        assert env.get_type("items") == PyType.LIST
    
    def test_len_returns_int(self):
        """len() always returns int."""
        ir = parse('n = len(items)')
        env = infer_types(ir)
        assert env.get_type("n") == PyType.INT


# =============================================================================
# 5. BINARY OPERATION TYPES
# =============================================================================

class TestBinaryOperationTypes:
    """Test type inference for binary operations."""
    
    def test_int_plus_int(self):
        """int + int = int."""
        ir = parse('x = 5 + 3')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_int_plus_float(self):
        """int + float = float."""
        ir = parse('x = 5 + 3.0')
        env = infer_types(ir)
        # Could be FLOAT or NUMBER
        assert env.get_type("x") in (PyType.FLOAT, PyType.NUMBER)
    
    def test_str_plus_str(self):
        """str + str = str."""
        ir = parse('x = "hello" + " world"')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR
    
    def test_int_mul_int(self):
        """int * int = int."""
        ir = parse('x = 5 * 3')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_comparison_is_bool(self):
        """Comparisons always produce bool."""
        ir = parse('x = 5 > 3')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_and_or_types(self):
        """and/or preserve types or become bool."""
        ir = parse('x = True and False')
        env = infer_types(ir)
        # Python and/or can return operand, but type is still bool-ish
        assert env.get_type("x") == PyType.BOOL


# =============================================================================
# 6. EXCEPTION HANDLING
# =============================================================================

class TestExceptionHandling:
    """Test type inference in try/except blocks."""
    
    def test_try_block_types(self):
        """Types defined in try block."""
        ir = parse('''
try:
    x = 5
except:
    pass
''')
        env = infer_types(ir)
        # x might be defined (if no exception)
        x_type = env.get_type("x")
        assert x_type in (PyType.INT, PyType.ANY)
    
    def test_except_defines_variable(self):
        """Variable defined in except block."""
        ir = parse('''
try:
    risky()
except:
    x = 0
''')
        env = infer_types(ir)
        # x defined in except
        x_type = env.get_type("x")
        assert x_type in (PyType.INT, PyType.ANY)
    
    def test_try_and_except_same_type(self):
        """Same type in both try and except."""
        ir = parse('''
try:
    x = 5
except:
    x = 0
''')
        env = infer_types(ir)
        # NOTE: Current implementation doesn't merge try/except types
        # This is a known limitation - could be improved
        # Variables in try/except are ANY for safety
        assert env.get_type("x") == PyType.ANY


# =============================================================================
# 7. METHOD RETURN TYPES
# =============================================================================

class TestMethodReturnTypes:
    """Test type inference for method calls."""
    
    def test_str_upper(self):
        """str.upper() returns str."""
        ir = parse('x = "hello".upper()')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR
    
    def test_str_split(self):
        """str.split() returns list."""
        ir = parse('x = "a,b,c".split(",")')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_list_copy(self):
        """list.copy() returns list."""
        ir = parse('''
items = [1, 2, 3]
copy = items.copy()
''')
        env = infer_types(ir)
        assert env.get_type("copy") == PyType.LIST
    
    def test_dict_keys(self):
        """dict.keys() returns iterable (ANY for now)."""
        ir = parse('''
data = {"a": 1}
keys = data.keys()
''')
        env = infer_types(ir)
        # Could be LIST or ANY
        keys_type = env.get_type("keys")
        assert keys_type in (PyType.LIST, PyType.ANY)


# =============================================================================
# 8. SPECIAL CASES
# =============================================================================

class TestSpecialCases:
    """Test special and edge cases."""
    
    def test_reassignment_changes_type(self):
        """Reassignment can change type."""
        ir = parse('''
x = 5
x = "hello"
''')
        env = infer_types(ir)
        # Last assignment wins
        assert env.get_type("x") == PyType.STR
    
    def test_none_type(self):
        """None literal type."""
        ir = parse('x = None')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.NONE
    
    def test_bool_literals(self):
        """Boolean literal types."""
        ir = parse('''
a = True
b = False
''')
        env = infer_types(ir)
        assert env.get_type("a") == PyType.BOOL
        assert env.get_type("b") == PyType.BOOL
    
    def test_not_produces_bool(self):
        """not x always produces bool."""
        ir = parse('x = not something')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_negative_int(self):
        """Negative integer is still int."""
        ir = parse('x = -5')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_chained_assignment(self):
        """Chained operations preserve type."""
        ir = parse('''
x = 5
y = x + 1
z = y * 2
''')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
        assert env.get_type("y") == PyType.INT
        assert env.get_type("z") == PyType.INT
    
    def test_unknown_function_call(self):
        """Unknown function call returns ANY."""
        ir = parse('x = unknown_func()')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.ANY
    
    def test_subscript_unknown(self):
        """Subscript access returns ANY."""
        ir = parse('x = items[0]')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.ANY
