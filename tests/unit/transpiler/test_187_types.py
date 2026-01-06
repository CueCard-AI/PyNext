"""
Phase 18.7 Tests - Type Inference Engine

100 comprehensive tests for the type inference system.

Test Categories:
1. Literal types (20 tests)
2. Variable types from assignment (15 tests)
3. Binary operation types (20 tests)
4. Unary operation types (10 tests)
5. Comparison and boolean types (10 tests)
6. Function call return types (15 tests)
7. Scope and environment (10 tests)
"""

import pytest
from pynext.transpiler import parse
from pynext.transpiler.optimizer.types import (
    infer_types, infer_expr_type,
    is_comparison, is_bool_literal, is_int_literal,
    is_positive_int_literal, is_str_literal, get_literal_value,
)
from pynext.transpiler.optimizer._internal.type_env import TypeEnv, PyType
from pynext.transpiler.nodes import (
    Constant, Name, BinOp, Compare, UnaryOp, Call, Attribute,
    List, Dict, Tuple, Lambda, ListComp, DictComp, SetComp,
)


# =============================================================================
# 1. LITERAL TYPES (20 tests)
# =============================================================================

class TestLiteralTypes:
    """Tests for inferring types from literals."""
    
    def test_int_literal(self):
        ir = parse("x = 5")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_negative_int_literal(self):
        # Note: -42 is parsed as UnaryOp(usub, 42), not as a single literal
        ir = parse("x = -42")
        env = infer_types(ir)
        # Unary minus on int returns int
        assert env.get_type("x") == PyType.INT
    
    def test_zero_literal(self):
        ir = parse("x = 0")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_float_literal(self):
        ir = parse("x = 3.14")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.FLOAT
    
    def test_negative_float_literal(self):
        # Note: -2.5 is parsed as UnaryOp(usub, 2.5), not as a single literal
        ir = parse("x = -2.5")
        env = infer_types(ir)
        # Unary minus on float returns float
        assert env.get_type("x") == PyType.FLOAT
    
    def test_zero_float_literal(self):
        ir = parse("x = 0.0")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.FLOAT
    
    def test_string_literal(self):
        ir = parse('x = "hello"')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR
    
    def test_empty_string_literal(self):
        ir = parse('x = ""')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR
    
    def test_true_literal(self):
        ir = parse("x = True")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_false_literal(self):
        ir = parse("x = False")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_none_literal(self):
        ir = parse("x = None")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.NONE
    
    def test_list_literal(self):
        ir = parse("x = [1, 2, 3]")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_empty_list_literal(self):
        ir = parse("x = []")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_dict_literal(self):
        ir = parse('x = {"a": 1}')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.DICT
    
    def test_empty_dict_literal(self):
        ir = parse("x = {}")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.DICT
    
    def test_tuple_literal(self):
        ir = parse("x = (1, 2)")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.TUPLE
    
    def test_nested_list_literal(self):
        ir = parse("x = [[1, 2], [3, 4]]")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_mixed_list_literal(self):
        ir = parse('x = [1, "a", True]')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_lambda_literal(self):
        ir = parse("x = lambda y: y + 1")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LAMBDA
    
    def test_multiline_string(self):
        ir = parse('x = "line1\\nline2"')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR


# =============================================================================
# 2. VARIABLE TYPES FROM ASSIGNMENT (15 tests)
# =============================================================================

class TestAssignmentTypes:
    """Tests for type propagation through assignments."""
    
    def test_simple_propagation(self):
        ir = parse("x = 5\ny = x")
        env = infer_types(ir)
        assert env.get_type("y") == PyType.INT
    
    def test_chain_propagation(self):
        ir = parse("x = 5\ny = x\nz = y")
        env = infer_types(ir)
        assert env.get_type("z") == PyType.INT
    
    def test_reassignment_same_type(self):
        ir = parse("x = 5\nx = 10")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_reassignment_different_type(self):
        ir = parse('x = 5\nx = "hello"')
        env = infer_types(ir)
        # Last assignment wins
        assert env.get_type("x") == PyType.STR
    
    def test_multiple_assignments(self):
        ir = parse("x = 1\ny = 2.0\nz = True")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
        assert env.get_type("y") == PyType.FLOAT
        assert env.get_type("z") == PyType.BOOL
    
    def test_unknown_variable(self):
        env = TypeEnv()
        assert env.get_type("unknown") == PyType.ANY
    
    def test_augmented_assignment_int(self):
        ir = parse("x = 5\nx += 1")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_augmented_assignment_float(self):
        ir = parse("x = 5.0\nx += 1")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.FLOAT
    
    def test_augmented_assignment_str(self):
        ir = parse('x = "hello"\nx += " world"')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR
    
    def test_computed_assignment(self):
        ir = parse("x = 5 + 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_list_comprehension_result(self):
        ir = parse("x = [i for i in range(10)]")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_dict_comprehension_result(self):
        ir = parse("x = {k: v for k, v in items}")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.DICT
    
    def test_set_comprehension_result(self):
        ir = parse("x = {i for i in items}")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.SET
    
    def test_conditional_expression(self):
        ir = parse("x = 5 if True else 10")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_conditional_expression_mixed(self):
        ir = parse('x = 5 if True else "hello"')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.ANY


# =============================================================================
# 3. BINARY OPERATION TYPES (20 tests)
# =============================================================================

class TestBinaryOpTypes:
    """Tests for binary operation result types."""
    
    def test_int_add_int(self):
        ir = parse("x = 5 + 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_int_sub_int(self):
        ir = parse("x = 5 - 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_int_mul_int(self):
        ir = parse("x = 5 * 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_int_div_int(self):
        # Division always returns float in Python 3
        ir = parse("x = 10 / 2")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.FLOAT
    
    def test_int_floordiv_int(self):
        ir = parse("x = 10 // 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_int_mod_int(self):
        ir = parse("x = 10 % 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_int_pow_int(self):
        ir = parse("x = 2 ** 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_float_add_float(self):
        ir = parse("x = 3.14 + 2.0")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.FLOAT
    
    def test_int_add_float(self):
        ir = parse("x = 5 + 2.0")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.FLOAT
    
    def test_float_add_int(self):
        ir = parse("x = 2.0 + 5")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.FLOAT
    
    def test_str_add_str(self):
        ir = parse('x = "hello" + " world"')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR
    
    def test_str_mul_int(self):
        ir = parse('x = "ab" * 3')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR
    
    def test_int_mul_str(self):
        ir = parse('x = 3 * "ab"')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR
    
    def test_list_add_list(self):
        ir = parse("x = [1, 2] + [3, 4]")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_list_mul_int(self):
        ir = parse("x = [1, 2] * 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_bitwise_or(self):
        ir = parse("x = 5 | 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_bitwise_and(self):
        ir = parse("x = 5 & 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_bitwise_xor(self):
        ir = parse("x = 5 ^ 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_left_shift(self):
        ir = parse("x = 5 << 2")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_right_shift(self):
        ir = parse("x = 20 >> 2")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT


# =============================================================================
# 4. UNARY OPERATION TYPES (10 tests)
# =============================================================================

class TestUnaryOpTypes:
    """Tests for unary operation result types."""
    
    def test_not_bool(self):
        ir = parse("x = not True")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_not_int(self):
        ir = parse("x = not 5")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_not_list(self):
        ir = parse("x = not []")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_negate_int(self):
        # Use a variable to ensure we get UnaryOp
        ir = parse("y = 5\nx = -y")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_negate_float(self):
        ir = parse("y = 3.14\nx = -y")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.FLOAT
    
    def test_positive_int(self):
        ir = parse("y = 5\nx = +y")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_positive_float(self):
        ir = parse("y = 3.14\nx = +y")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.FLOAT
    
    def test_invert_int(self):
        ir = parse("x = ~5")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_double_not(self):
        ir = parse("x = not not True")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_double_negate(self):
        ir = parse("y = 5\nx = --y")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT


# =============================================================================
# 5. COMPARISON AND BOOLEAN TYPES (10 tests)
# =============================================================================

class TestComparisonTypes:
    """Tests for comparison and boolean operation result types."""
    
    def test_less_than(self):
        ir = parse("x = 5 < 10")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_greater_than(self):
        ir = parse("x = 10 > 5")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_equal(self):
        ir = parse("x = 5 == 5")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_not_equal(self):
        ir = parse("x = 5 != 3")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_less_equal(self):
        ir = parse("x = 5 <= 10")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_greater_equal(self):
        ir = parse("x = 10 >= 5")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_and_op(self):
        ir = parse("x = True and False")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_or_op(self):
        ir = parse("x = True or False")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_in_op(self):
        ir = parse("x = 5 in [1, 2, 3]")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_not_in_op(self):
        ir = parse("x = 5 not in [1, 2, 3]")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL


# =============================================================================
# 6. FUNCTION CALL RETURN TYPES (15 tests)
# =============================================================================

class TestCallTypes:
    """Tests for function call return types."""
    
    def test_len_returns_int(self):
        ir = parse("x = len(items)")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_int_returns_int(self):
        ir = parse('x = int("5")')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_float_returns_float(self):
        ir = parse('x = float("3.14")')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.FLOAT
    
    def test_str_returns_str(self):
        ir = parse("x = str(5)")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR
    
    def test_bool_returns_bool(self):
        ir = parse("x = bool(1)")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_list_returns_list(self):
        ir = parse("x = list(items)")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_dict_returns_dict(self):
        ir = parse("x = dict(items)")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.DICT
    
    def test_sorted_returns_list(self):
        ir = parse("x = sorted(items)")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_abs_returns_int(self):
        ir = parse("x = abs(-5)")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_any_returns_bool(self):
        ir = parse("x = any(items)")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_all_returns_bool(self):
        ir = parse("x = all(items)")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_str_upper_returns_str(self):
        ir = parse('x = "hello".upper()')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.STR
    
    def test_str_split_returns_list(self):
        ir = parse('x = "a,b,c".split(",")')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.LIST
    
    def test_str_count_returns_int(self):
        ir = parse('x = "hello".count("l")')
        env = infer_types(ir)
        assert env.get_type("x") == PyType.INT
    
    def test_unknown_function_returns_any(self):
        ir = parse("x = unknown_func()")
        env = infer_types(ir)
        assert env.get_type("x") == PyType.ANY


# =============================================================================
# 7. SCOPE AND ENVIRONMENT (10 tests)
# =============================================================================

class TestScopeTypes:
    """Tests for type environment scoping."""
    
    def test_type_env_creation(self):
        env = TypeEnv()
        assert env.get_type("x") == PyType.ANY
    
    def test_type_env_set_get(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        assert env.get_type("x") == PyType.INT
    
    def test_type_env_child_scope(self):
        parent = TypeEnv()
        parent.set_type("x", PyType.INT)
        child = parent.child_scope("block")
        assert child.get_type("x") == PyType.INT
    
    def test_type_env_child_shadow(self):
        parent = TypeEnv()
        parent.set_type("x", PyType.INT)
        child = parent.child_scope("block")
        child.set_type("x", PyType.STR)
        assert child.get_type("x") == PyType.STR
        assert parent.get_type("x") == PyType.INT
    
    def test_function_scope(self):
        ir = parse("""
def foo():
    x = 5
y = 10
""")
        env = infer_types(ir)
        assert env.get_type("foo") == PyType.FUNC
        assert env.get_type("y") == PyType.INT
    
    def test_for_loop_variable(self):
        ir = parse("for i in range(10): pass")
        env = infer_types(ir)
        assert env.get_type("i") == PyType.INT
    
    def test_for_loop_string_iteration(self):
        ir = parse('for c in "hello": pass')
        env = infer_types(ir)
        assert env.get_type("c") == PyType.STR
    
    def test_type_env_merge(self):
        env = TypeEnv()
        branch1 = TypeEnv()
        branch1.set_type("x", PyType.INT)
        branch2 = TypeEnv()
        branch2.set_type("x", PyType.INT)
        env.merge_types(branch1)
        env.merge_types(branch2)
        assert env.get_type("x") == PyType.INT
    
    def test_type_env_merge_numeric(self):
        env = TypeEnv()
        branch1 = TypeEnv()
        branch1.set_type("x", PyType.INT)
        branch2 = TypeEnv()
        branch2.set_type("x", PyType.FLOAT)
        env.merge_types(branch1)
        env.merge_types(branch2)
        assert env.get_type("x") == PyType.NUMBER
    
    def test_type_env_merge_incompatible(self):
        env = TypeEnv()
        branch1 = TypeEnv()
        branch1.set_type("x", PyType.INT)
        branch2 = TypeEnv()
        branch2.set_type("x", PyType.STR)
        env.merge_types(branch1)
        env.merge_types(branch2)
        assert env.get_type("x") == PyType.ANY


# =============================================================================
# PYTYPE METHODS (bonus tests)
# =============================================================================

class TestPyTypeMethods:
    """Tests for PyType enum methods."""
    
    def test_is_numeric_int(self):
        assert PyType.INT.is_numeric()
    
    def test_is_numeric_float(self):
        assert PyType.FLOAT.is_numeric()
    
    def test_is_numeric_number(self):
        assert PyType.NUMBER.is_numeric()
    
    def test_is_numeric_str(self):
        assert not PyType.STR.is_numeric()
    
    def test_is_primitive_int(self):
        assert PyType.INT.is_primitive()
    
    def test_is_primitive_str(self):
        assert PyType.STR.is_primitive()
    
    def test_is_primitive_list(self):
        assert not PyType.LIST.is_primitive()
    
    def test_is_collection_list(self):
        assert PyType.LIST.is_collection()
    
    def test_is_collection_dict(self):
        assert PyType.DICT.is_collection()
    
    def test_is_collection_int(self):
        assert not PyType.INT.is_collection()
    
    def test_is_known_int(self):
        assert PyType.INT.is_known()
    
    def test_is_known_any(self):
        assert not PyType.ANY.is_known()


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_is_comparison_compare(self):
        node = Compare(left=Constant(value=5), ops=("lt",), comparators=(Constant(value=10),))
        assert is_comparison(node)
    
    def test_is_comparison_not_compare(self):
        node = Constant(value=5)
        assert not is_comparison(node)
    
    def test_is_bool_literal_true(self):
        node = Constant(value=True)
        assert is_bool_literal(node)
    
    def test_is_bool_literal_false(self):
        node = Constant(value=False)
        assert is_bool_literal(node)
    
    def test_is_bool_literal_int(self):
        node = Constant(value=1)
        assert not is_bool_literal(node)
    
    def test_is_int_literal_positive(self):
        node = Constant(value=5)
        assert is_int_literal(node)
    
    def test_is_int_literal_zero(self):
        node = Constant(value=0)
        assert is_int_literal(node)
    
    def test_is_int_literal_negative(self):
        node = Constant(value=-5)
        assert is_int_literal(node)
    
    def test_is_int_literal_bool(self):
        # bool is subclass of int but should not count
        node = Constant(value=True)
        assert not is_int_literal(node)
    
    def test_is_positive_int_literal_positive(self):
        node = Constant(value=5)
        assert is_positive_int_literal(node)
    
    def test_is_positive_int_literal_zero(self):
        node = Constant(value=0)
        assert is_positive_int_literal(node)
    
    def test_is_positive_int_literal_negative(self):
        node = Constant(value=-5)
        assert not is_positive_int_literal(node)
    
    def test_is_str_literal_string(self):
        node = Constant(value="hello")
        assert is_str_literal(node)
    
    def test_is_str_literal_int(self):
        node = Constant(value=5)
        assert not is_str_literal(node)
    
    def test_get_literal_value_int(self):
        node = Constant(value=5)
        assert get_literal_value(node) == 5
    
    def test_get_literal_value_str(self):
        node = Constant(value="hello")
        assert get_literal_value(node) == "hello"
    
    def test_get_literal_value_not_constant(self):
        node = Name(id="x")
        assert get_literal_value(node) is None
