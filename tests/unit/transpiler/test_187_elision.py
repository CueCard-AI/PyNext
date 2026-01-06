"""
Phase 18.7 Tests - Wrapper Elision

120 comprehensive tests for wrapper elision optimization.

Test Categories:
1. Bool elision (20 tests)
2. Equality elision (20 tests)
3. Arithmetic elision (30 tests)
4. Index/slice elision (20 tests)
5. Membership elision (10 tests)
6. Negative cases - must NOT elide (20 tests)
"""

import pytest
from pynext.transpiler.nodes import (
    Constant, Name, BinOp, Compare, UnaryOp, Call, Attribute,
    List, Dict, Subscript, Slice, Program, Assignment, ExprStmt,
)
from pynext.transpiler.optimizer._internal.type_env import TypeEnv, PyType
from pynext.transpiler.optimizer.elision import (
    elide_wrappers,
    can_elide_bool, can_elide_eq, can_elide_add, can_elide_sub,
    can_elide_mul, can_elide_div, can_elide_mod, can_elide_floordiv,
    can_elide_at, can_elide_slice, can_elide_in,
    ElisionOptimizer, count_py_calls,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def make_py_call(method: str, *args) -> Call:
    """Create a __py.method(*args) call node."""
    return Call(
        func=Attribute(
            value=Name(id="__py"),
            attr=method,
        ),
        args=args,
        keywords={},
    )


def make_program(stmts) -> Program:
    """Create a Program node from statements."""
    return Program(body=tuple(stmts))


# =============================================================================
# 1. BOOL ELISION (20 tests)
# =============================================================================

class TestBoolElision:
    """Tests for __py.bool() elision."""
    
    def test_comparison_is_elidable(self):
        """Comparison results are always bool."""
        cmp = Compare(
            left=Name(id="x"),
            ops=("gt",),
            comparators=(Constant(value=0),),
        )
        env = TypeEnv()
        assert can_elide_bool(cmp, env) is True
    
    def test_less_than_is_elidable(self):
        cmp = Compare(
            left=Name(id="x"),
            ops=("lt",),
            comparators=(Constant(value=10),),
        )
        env = TypeEnv()
        assert can_elide_bool(cmp, env) is True
    
    def test_equal_is_elidable(self):
        cmp = Compare(
            left=Name(id="x"),
            ops=("eq",),
            comparators=(Constant(value=5),),
        )
        env = TypeEnv()
        assert can_elide_bool(cmp, env) is True
    
    def test_not_equal_is_elidable(self):
        cmp = Compare(
            left=Name(id="x"),
            ops=("noteq",),
            comparators=(Constant(value=5),),
        )
        env = TypeEnv()
        assert can_elide_bool(cmp, env) is True
    
    def test_bool_variable_is_elidable(self):
        """Known bool variables can be elided."""
        env = TypeEnv()
        env.set_type("is_valid", PyType.BOOL)
        node = Name(id="is_valid")
        assert can_elide_bool(node, env) is True
    
    def test_true_literal_is_elidable(self):
        env = TypeEnv()
        node = Constant(value=True)
        assert can_elide_bool(node, env) is True
    
    def test_false_literal_is_elidable(self):
        env = TypeEnv()
        node = Constant(value=False)
        assert can_elide_bool(node, env) is True
    
    def test_int_variable_not_elidable(self):
        """Int variables cannot be elided (0 is falsy)."""
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        node = Name(id="x")
        assert can_elide_bool(node, env) is False
    
    def test_str_variable_not_elidable(self):
        """String variables cannot be elided (empty is falsy)."""
        env = TypeEnv()
        env.set_type("s", PyType.STR)
        node = Name(id="s")
        assert can_elide_bool(node, env) is False
    
    def test_list_variable_not_elidable(self):
        """List variables cannot be elided (empty is falsy)."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        node = Name(id="items")
        assert can_elide_bool(node, env) is False
    
    def test_dict_variable_not_elidable(self):
        """Dict variables cannot be elided (empty is falsy)."""
        env = TypeEnv()
        env.set_type("data", PyType.DICT)
        node = Name(id="data")
        assert can_elide_bool(node, env) is False
    
    def test_unknown_variable_not_elidable(self):
        """Unknown type variables cannot be elided."""
        env = TypeEnv()
        node = Name(id="unknown")
        assert can_elide_bool(node, env) is False
    
    def test_list_literal_not_elidable(self):
        """List literals cannot be elided."""
        env = TypeEnv()
        node = List(elts=(Constant(value=1),))
        assert can_elide_bool(node, env) is False
    
    def test_dict_literal_not_elidable(self):
        """Dict literals cannot be elided."""
        env = TypeEnv()
        node = Dict(keys=(Constant(value="a"),), values=(Constant(value=1),))
        assert can_elide_bool(node, env) is False
    
    def test_int_literal_not_elidable(self):
        """Int literals cannot be elided (0 is falsy)."""
        env = TypeEnv()
        node = Constant(value=5)
        assert can_elide_bool(node, env) is False
    
    def test_zero_literal_not_elidable(self):
        """Zero literal cannot be elided."""
        env = TypeEnv()
        node = Constant(value=0)
        assert can_elide_bool(node, env) is False
    
    def test_string_literal_not_elidable(self):
        """String literals cannot be elided (empty is falsy)."""
        env = TypeEnv()
        node = Constant(value="hello")
        assert can_elide_bool(node, env) is False
    
    def test_empty_string_literal_not_elidable(self):
        """Empty string literal cannot be elided."""
        env = TypeEnv()
        node = Constant(value="")
        assert can_elide_bool(node, env) is False
    
    def test_none_literal_not_elidable(self):
        """None literal cannot be elided."""
        env = TypeEnv()
        node = Constant(value=None)
        assert can_elide_bool(node, env) is False
    
    def test_chained_comparison_elidable(self):
        """Chained comparisons are bool."""
        cmp = Compare(
            left=Name(id="x"),
            ops=("lt", "lt"),
            comparators=(Name(id="y"), Name(id="z")),
        )
        env = TypeEnv()
        assert can_elide_bool(cmp, env) is True


# =============================================================================
# 2. EQUALITY ELISION (20 tests)
# =============================================================================

class TestEqualityElision:
    """Tests for __py.eq() elision."""
    
    def test_int_eq_int_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        left = Name(id="x")
        right = Constant(value=5)
        assert can_elide_eq(left, right, env) is True
    
    def test_int_literal_eq_int_literal(self):
        env = TypeEnv()
        left = Constant(value=5)
        right = Constant(value=10)
        assert can_elide_eq(left, right, env) is True
    
    def test_float_eq_float_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.FLOAT)
        env.set_type("y", PyType.FLOAT)
        left = Name(id="x")
        right = Name(id="y")
        assert can_elide_eq(left, right, env) is True
    
    def test_str_eq_str_elidable(self):
        env = TypeEnv()
        env.set_type("s1", PyType.STR)
        env.set_type("s2", PyType.STR)
        left = Name(id="s1")
        right = Name(id="s2")
        assert can_elide_eq(left, right, env) is True
    
    def test_bool_eq_bool_elidable(self):
        env = TypeEnv()
        env.set_type("a", PyType.BOOL)
        env.set_type("b", PyType.BOOL)
        left = Name(id="a")
        right = Name(id="b")
        assert can_elide_eq(left, right, env) is True
    
    def test_none_eq_none_elidable(self):
        env = TypeEnv()
        left = Constant(value=None)
        right = Constant(value=None)
        assert can_elide_eq(left, right, env) is True
    
    def test_int_eq_float_elidable(self):
        """Mixed numeric types are still primitive."""
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("y", PyType.FLOAT)
        left = Name(id="x")
        right = Name(id="y")
        assert can_elide_eq(left, right, env) is True
    
    def test_str_eq_int_elidable(self):
        """Different primitives are still elidable."""
        env = TypeEnv()
        env.set_type("s", PyType.STR)
        left = Name(id="s")
        right = Constant(value=5)
        assert can_elide_eq(left, right, env) is True
    
    def test_list_eq_list_not_elidable(self):
        """List equality needs deep comparison."""
        env = TypeEnv()
        env.set_type("a", PyType.LIST)
        env.set_type("b", PyType.LIST)
        left = Name(id="a")
        right = Name(id="b")
        assert can_elide_eq(left, right, env) is False
    
    def test_dict_eq_dict_not_elidable(self):
        """Dict equality needs deep comparison."""
        env = TypeEnv()
        env.set_type("a", PyType.DICT)
        env.set_type("b", PyType.DICT)
        left = Name(id="a")
        right = Name(id="b")
        assert can_elide_eq(left, right, env) is False
    
    def test_tuple_eq_tuple_not_elidable(self):
        """Tuple equality needs deep comparison."""
        env = TypeEnv()
        env.set_type("a", PyType.TUPLE)
        env.set_type("b", PyType.TUPLE)
        left = Name(id="a")
        right = Name(id="b")
        assert can_elide_eq(left, right, env) is False
    
    def test_set_eq_set_not_elidable(self):
        """Set equality needs deep comparison."""
        env = TypeEnv()
        env.set_type("a", PyType.SET)
        env.set_type("b", PyType.SET)
        left = Name(id="a")
        right = Name(id="b")
        assert can_elide_eq(left, right, env) is False
    
    def test_int_eq_list_not_elidable(self):
        """Mixed primitive and collection not elidable."""
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("arr", PyType.LIST)
        left = Name(id="x")
        right = Name(id="arr")
        assert can_elide_eq(left, right, env) is False
    
    def test_unknown_eq_int_not_elidable(self):
        """Unknown type not elidable."""
        env = TypeEnv()
        left = Name(id="unknown")
        right = Constant(value=5)
        assert can_elide_eq(left, right, env) is False
    
    def test_int_eq_unknown_not_elidable(self):
        """Unknown type not elidable."""
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        left = Name(id="x")
        right = Name(id="unknown")
        assert can_elide_eq(left, right, env) is False
    
    def test_list_literal_eq_list_literal_not_elidable(self):
        """List literals need deep comparison."""
        env = TypeEnv()
        left = List(elts=(Constant(value=1),))
        right = List(elts=(Constant(value=1),))
        assert can_elide_eq(left, right, env) is False
    
    def test_dict_literal_eq_dict_literal_not_elidable(self):
        """Dict literals need deep comparison."""
        env = TypeEnv()
        left = Dict(keys=(Constant(value="a"),), values=(Constant(value=1),))
        right = Dict(keys=(Constant(value="a"),), values=(Constant(value=1),))
        assert can_elide_eq(left, right, env) is False
    
    def test_any_type_not_elidable(self):
        """ANY type is not primitive."""
        env = TypeEnv()
        env.set_type("x", PyType.ANY)
        env.set_type("y", PyType.ANY)
        left = Name(id="x")
        right = Name(id="y")
        assert can_elide_eq(left, right, env) is False
    
    def test_func_type_not_elidable(self):
        """Function type is not primitive."""
        env = TypeEnv()
        env.set_type("f", PyType.FUNC)
        env.set_type("g", PyType.FUNC)
        left = Name(id="f")
        right = Name(id="g")
        assert can_elide_eq(left, right, env) is False
    
    def test_number_type_elidable(self):
        """NUMBER type is primitive."""
        env = TypeEnv()
        env.set_type("x", PyType.NUMBER)
        env.set_type("y", PyType.NUMBER)
        left = Name(id="x")
        right = Name(id="y")
        assert can_elide_eq(left, right, env) is True


# =============================================================================
# 3. ARITHMETIC ELISION (30 tests)
# =============================================================================

class TestArithmeticElision:
    """Tests for __py.add/sub/mul/div elision."""
    
    # ADD tests (8)
    def test_int_add_int_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("y", PyType.INT)
        assert can_elide_add(Name(id="x"), Name(id="y"), env) is True
    
    def test_float_add_float_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.FLOAT)
        env.set_type("y", PyType.FLOAT)
        assert can_elide_add(Name(id="x"), Name(id="y"), env) is True
    
    def test_int_add_float_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("y", PyType.FLOAT)
        assert can_elide_add(Name(id="x"), Name(id="y"), env) is True
    
    def test_number_add_number_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.NUMBER)
        env.set_type("y", PyType.NUMBER)
        assert can_elide_add(Name(id="x"), Name(id="y"), env) is True
    
    def test_str_add_str_not_elidable(self):
        """String concat needs __py.add for type consistency."""
        env = TypeEnv()
        env.set_type("s1", PyType.STR)
        env.set_type("s2", PyType.STR)
        assert can_elide_add(Name(id="s1"), Name(id="s2"), env) is False
    
    def test_list_add_list_not_elidable(self):
        """List concat needs __py.add."""
        env = TypeEnv()
        env.set_type("a", PyType.LIST)
        env.set_type("b", PyType.LIST)
        assert can_elide_add(Name(id="a"), Name(id="b"), env) is False
    
    def test_int_add_str_not_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("s", PyType.STR)
        assert can_elide_add(Name(id="x"), Name(id="s"), env) is False
    
    def test_unknown_add_int_not_elidable(self):
        env = TypeEnv()
        left = Name(id="unknown")
        right = Constant(value=5)
        assert can_elide_add(left, right, env) is False
    
    # SUB tests (6)
    def test_int_sub_int_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("y", PyType.INT)
        assert can_elide_sub(Name(id="x"), Name(id="y"), env) is True
    
    def test_float_sub_float_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.FLOAT)
        env.set_type("y", PyType.FLOAT)
        assert can_elide_sub(Name(id="x"), Name(id="y"), env) is True
    
    def test_int_sub_float_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("y", PyType.FLOAT)
        assert can_elide_sub(Name(id="x"), Name(id="y"), env) is True
    
    def test_str_sub_str_not_elidable(self):
        """Strings don't support subtraction but check anyway."""
        env = TypeEnv()
        env.set_type("s1", PyType.STR)
        env.set_type("s2", PyType.STR)
        assert can_elide_sub(Name(id="s1"), Name(id="s2"), env) is False
    
    def test_unknown_sub_int_not_elidable(self):
        env = TypeEnv()
        left = Name(id="unknown")
        right = Constant(value=5)
        assert can_elide_sub(left, right, env) is False
    
    def test_literal_sub_literal_elidable(self):
        env = TypeEnv()
        left = Constant(value=10)
        right = Constant(value=3)
        assert can_elide_sub(left, right, env) is True
    
    # MUL tests (8)
    def test_int_mul_int_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("y", PyType.INT)
        assert can_elide_mul(Name(id="x"), Name(id="y"), env) is True
    
    def test_float_mul_float_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.FLOAT)
        env.set_type("y", PyType.FLOAT)
        assert can_elide_mul(Name(id="x"), Name(id="y"), env) is True
    
    def test_int_mul_float_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("y", PyType.FLOAT)
        assert can_elide_mul(Name(id="x"), Name(id="y"), env) is True
    
    def test_str_mul_int_not_elidable(self):
        """String repetition needs __py.mul."""
        env = TypeEnv()
        env.set_type("s", PyType.STR)
        env.set_type("n", PyType.INT)
        assert can_elide_mul(Name(id="s"), Name(id="n"), env) is False
    
    def test_int_mul_str_not_elidable(self):
        """String repetition needs __py.mul."""
        env = TypeEnv()
        env.set_type("n", PyType.INT)
        env.set_type("s", PyType.STR)
        assert can_elide_mul(Name(id="n"), Name(id="s"), env) is False
    
    def test_list_mul_int_not_elidable(self):
        """List repetition needs __py.mul."""
        env = TypeEnv()
        env.set_type("arr", PyType.LIST)
        env.set_type("n", PyType.INT)
        assert can_elide_mul(Name(id="arr"), Name(id="n"), env) is False
    
    def test_unknown_mul_int_not_elidable(self):
        env = TypeEnv()
        left = Name(id="unknown")
        right = Constant(value=5)
        assert can_elide_mul(left, right, env) is False
    
    def test_literal_mul_literal_elidable(self):
        env = TypeEnv()
        left = Constant(value=3)
        right = Constant(value=4)
        assert can_elide_mul(left, right, env) is True
    
    # DIV tests (4)
    def test_int_div_int_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("y", PyType.INT)
        assert can_elide_div(Name(id="x"), Name(id="y"), env) is True
    
    def test_float_div_float_elidable(self):
        env = TypeEnv()
        env.set_type("x", PyType.FLOAT)
        env.set_type("y", PyType.FLOAT)
        assert can_elide_div(Name(id="x"), Name(id="y"), env) is True
    
    def test_unknown_div_int_not_elidable(self):
        env = TypeEnv()
        left = Name(id="unknown")
        right = Constant(value=5)
        assert can_elide_div(left, right, env) is False
    
    def test_literal_div_literal_elidable(self):
        env = TypeEnv()
        left = Constant(value=10)
        right = Constant(value=2)
        assert can_elide_div(left, right, env) is True
    
    # FLOORDIV tests (2)
    def test_floordiv_never_elidable(self):
        """Floor division always needs wrapper."""
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("y", PyType.INT)
        assert can_elide_floordiv(Name(id="x"), Name(id="y"), env) is False
    
    def test_floordiv_literal_never_elidable(self):
        env = TypeEnv()
        left = Constant(value=10)
        right = Constant(value=3)
        assert can_elide_floordiv(left, right, env) is False
    
    # MOD tests (4)
    def test_positive_mod_positive_elidable(self):
        """Positive modulo is safe."""
        env = TypeEnv()
        left = Constant(value=10)
        right = Constant(value=3)
        assert can_elide_mod(left, right, env) is True
    
    def test_zero_mod_positive_elidable(self):
        env = TypeEnv()
        left = Constant(value=0)
        right = Constant(value=3)
        assert can_elide_mod(left, right, env) is True
    
    def test_negative_mod_positive_not_elidable(self):
        """Negative modulo differs between Python and JS."""
        env = TypeEnv()
        left = Constant(value=-7)
        right = Constant(value=3)
        assert can_elide_mod(left, right, env) is False
    
    def test_variable_mod_not_elidable(self):
        """Variables could be negative."""
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        left = Name(id="x")
        right = Constant(value=3)
        assert can_elide_mod(left, right, env) is False


# =============================================================================
# 4. INDEX/SLICE ELISION (20 tests)
# =============================================================================

class TestIndexElision:
    """Tests for __py.at() and __py.slice() elision."""
    
    # AT tests (12)
    def test_positive_index_elidable(self):
        env = TypeEnv()
        arr = Name(id="items")
        idx = Constant(value=0)
        assert can_elide_at(arr, idx, env) is True
    
    def test_zero_index_elidable(self):
        env = TypeEnv()
        arr = Name(id="items")
        idx = Constant(value=0)
        assert can_elide_at(arr, idx, env) is True
    
    def test_large_positive_index_elidable(self):
        env = TypeEnv()
        arr = Name(id="items")
        idx = Constant(value=100)
        assert can_elide_at(arr, idx, env) is True
    
    def test_negative_one_index_not_elidable(self):
        """Negative indexing needs __py.at."""
        env = TypeEnv()
        arr = Name(id="items")
        idx = Constant(value=-1)
        assert can_elide_at(arr, idx, env) is False
    
    def test_negative_index_not_elidable(self):
        env = TypeEnv()
        arr = Name(id="items")
        idx = Constant(value=-5)
        assert can_elide_at(arr, idx, env) is False
    
    def test_variable_index_not_elidable(self):
        """Variable index could be negative."""
        env = TypeEnv()
        env.set_type("i", PyType.INT)
        arr = Name(id="items")
        idx = Name(id="i")
        assert can_elide_at(arr, idx, env) is False
    
    def test_expression_index_not_elidable(self):
        env = TypeEnv()
        arr = Name(id="items")
        idx = BinOp(left=Name(id="i"), op="add", right=Constant(value=1))
        assert can_elide_at(arr, idx, env) is False
    
    def test_bool_true_index_not_elidable(self):
        """bool(True) is 1 but we don't handle this edge case."""
        env = TypeEnv()
        arr = Name(id="items")
        idx = Constant(value=True)  # bool is int subclass
        assert can_elide_at(arr, idx, env) is False
    
    def test_float_index_not_elidable(self):
        env = TypeEnv()
        arr = Name(id="items")
        idx = Constant(value=1.0)
        assert can_elide_at(arr, idx, env) is False
    
    def test_string_index_not_elidable(self):
        env = TypeEnv()
        arr = Name(id="items")
        idx = Constant(value="key")
        assert can_elide_at(arr, idx, env) is False
    
    def test_none_index_not_elidable(self):
        env = TypeEnv()
        arr = Name(id="items")
        idx = Constant(value=None)
        assert can_elide_at(arr, idx, env) is False
    
    def test_unknown_type_index_not_elidable(self):
        env = TypeEnv()
        arr = Name(id="items")
        idx = Name(id="unknown")
        assert can_elide_at(arr, idx, env) is False
    
    # SLICE tests (8)
    def test_simple_slice_elidable(self):
        """arr[0:5] is safe."""
        env = TypeEnv()
        arr = Name(id="items")
        start = Constant(value=0)
        stop = Constant(value=5)
        assert can_elide_slice(arr, start, stop, None, env) is True
    
    def test_open_start_slice_elidable(self):
        """arr[:5] is safe."""
        env = TypeEnv()
        arr = Name(id="items")
        stop = Constant(value=5)
        assert can_elide_slice(arr, None, stop, None, env) is True
    
    def test_open_stop_slice_elidable(self):
        """arr[2:] is safe."""
        env = TypeEnv()
        arr = Name(id="items")
        start = Constant(value=2)
        assert can_elide_slice(arr, start, None, None, env) is True
    
    def test_full_slice_elidable(self):
        """arr[:] is safe."""
        env = TypeEnv()
        arr = Name(id="items")
        assert can_elide_slice(arr, None, None, None, env) is True
    
    def test_negative_start_not_elidable(self):
        """arr[-3:] needs __py.slice."""
        env = TypeEnv()
        arr = Name(id="items")
        start = Constant(value=-3)
        assert can_elide_slice(arr, start, None, None, env) is False
    
    def test_negative_stop_not_elidable(self):
        """arr[:-1] needs __py.slice."""
        env = TypeEnv()
        arr = Name(id="items")
        stop = Constant(value=-1)
        assert can_elide_slice(arr, None, stop, None, env) is False
    
    def test_step_not_elidable(self):
        """arr[::2] needs __py.slice."""
        env = TypeEnv()
        arr = Name(id="items")
        step = Constant(value=2)
        assert can_elide_slice(arr, None, None, step, env) is False
    
    def test_reverse_step_not_elidable(self):
        """arr[::-1] needs __py.slice."""
        env = TypeEnv()
        arr = Name(id="items")
        step = Constant(value=-1)
        assert can_elide_slice(arr, None, None, step, env) is False


# =============================================================================
# 5. MEMBERSHIP ELISION (10 tests)
# =============================================================================

class TestMembershipElision:
    """Tests for __py.in() elision."""
    
    def test_string_in_string_elidable(self):
        """Substring check is safe."""
        env = TypeEnv()
        env.set_type("s", PyType.STR)
        item = Constant(value="x")
        container = Name(id="s")
        assert can_elide_in(item, container, env) is True
    
    def test_char_in_string_elidable(self):
        env = TypeEnv()
        env.set_type("text", PyType.STR)
        item = Constant(value="a")
        container = Name(id="text")
        assert can_elide_in(item, container, env) is True
    
    def test_variable_in_string_elidable(self):
        env = TypeEnv()
        env.set_type("needle", PyType.STR)
        env.set_type("haystack", PyType.STR)
        item = Name(id="needle")
        container = Name(id="haystack")
        assert can_elide_in(item, container, env) is True
    
    def test_item_in_list_not_elidable(self):
        """List membership needs deep equality."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        item = Constant(value=5)
        container = Name(id="items")
        assert can_elide_in(item, container, env) is False
    
    def test_key_in_dict_not_elidable(self):
        """Dict membership uses different semantics."""
        env = TypeEnv()
        env.set_type("data", PyType.DICT)
        item = Constant(value="key")
        container = Name(id="data")
        assert can_elide_in(item, container, env) is False
    
    def test_item_in_set_not_elidable(self):
        env = TypeEnv()
        env.set_type("items", PyType.SET)
        item = Constant(value=5)
        container = Name(id="items")
        assert can_elide_in(item, container, env) is False
    
    def test_item_in_tuple_not_elidable(self):
        env = TypeEnv()
        env.set_type("items", PyType.TUPLE)
        item = Constant(value=5)
        container = Name(id="items")
        assert can_elide_in(item, container, env) is False
    
    def test_item_in_unknown_not_elidable(self):
        env = TypeEnv()
        item = Constant(value=5)
        container = Name(id="unknown")
        assert can_elide_in(item, container, env) is False
    
    def test_int_in_string_elidable(self):
        """Even if item is int, if container is string it's safe."""
        env = TypeEnv()
        env.set_type("text", PyType.STR)
        item = Constant(value=5)  # Will be converted to "5"
        container = Name(id="text")
        assert can_elide_in(item, container, env) is True
    
    def test_list_in_list_not_elidable(self):
        """Nested list membership needs deep equality."""
        env = TypeEnv()
        env.set_type("outer", PyType.LIST)
        env.set_type("inner", PyType.LIST)
        item = Name(id="inner")
        container = Name(id="outer")
        assert can_elide_in(item, container, env) is False


# =============================================================================
# 6. NEGATIVE CASES - MUST NOT ELIDE (20 tests)
# =============================================================================

class TestNegativeCases:
    """Tests ensuring we DON'T elide in dangerous cases."""
    
    def test_empty_list_bool_not_elided(self):
        """[] is falsy in Python, truthy in JS."""
        env = TypeEnv()
        node = List(elts=())
        assert can_elide_bool(node, env) is False
    
    def test_empty_dict_bool_not_elided(self):
        """{} is falsy in Python, truthy in JS."""
        env = TypeEnv()
        node = Dict(keys=(), values=())
        assert can_elide_bool(node, env) is False
    
    def test_zero_bool_not_elided(self):
        """0 is falsy in both, but we're conservative with int type."""
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        node = Name(id="x")
        assert can_elide_bool(node, env) is False
    
    def test_empty_string_bool_not_elided(self):
        env = TypeEnv()
        env.set_type("s", PyType.STR)
        node = Name(id="s")
        assert can_elide_bool(node, env) is False
    
    def test_list_eq_list_not_elided(self):
        """[1] == [1] is True in Python, false in JS."""
        env = TypeEnv()
        left = List(elts=(Constant(value=1),))
        right = List(elts=(Constant(value=1),))
        assert can_elide_eq(left, right, env) is False
    
    def test_dict_eq_dict_not_elided(self):
        env = TypeEnv()
        left = Dict(keys=(Constant(value="a"),), values=(Constant(value=1),))
        right = Dict(keys=(Constant(value="a"),), values=(Constant(value=1),))
        assert can_elide_eq(left, right, env) is False
    
    def test_list_add_list_not_elided(self):
        """[1] + [2] = [1,2] in Python, "1,2" in JS."""
        env = TypeEnv()
        env.set_type("a", PyType.LIST)
        env.set_type("b", PyType.LIST)
        assert can_elide_add(Name(id="a"), Name(id="b"), env) is False
    
    def test_str_mul_int_not_elided(self):
        """"a" * 3 = "aaa" in Python, NaN in JS."""
        env = TypeEnv()
        env.set_type("s", PyType.STR)
        assert can_elide_mul(Name(id="s"), Constant(value=3), env) is False
    
    def test_negative_index_not_elided(self):
        """arr[-1] gets last item in Python, undefined in JS."""
        env = TypeEnv()
        arr = Name(id="items")
        idx = Constant(value=-1)
        assert can_elide_at(arr, idx, env) is False
    
    def test_negative_mod_not_elided(self):
        """-7 % 3 = 2 in Python, -1 in JS."""
        env = TypeEnv()
        left = Constant(value=-7)
        right = Constant(value=3)
        assert can_elide_mod(left, right, env) is False
    
    def test_floordiv_not_elided(self):
        """10 // 3 = 3 needs Math.floor in JS."""
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        env.set_type("y", PyType.INT)
        assert can_elide_floordiv(Name(id="x"), Name(id="y"), env) is False
    
    def test_reverse_slice_not_elided(self):
        """arr[::-1] reverses in Python."""
        env = TypeEnv()
        arr = Name(id="items")
        step = Constant(value=-1)
        assert can_elide_slice(arr, None, None, step, env) is False
    
    def test_step_slice_not_elided(self):
        """arr[::2] takes every other in Python."""
        env = TypeEnv()
        arr = Name(id="items")
        step = Constant(value=2)
        assert can_elide_slice(arr, None, None, step, env) is False
    
    def test_negative_slice_start_not_elided(self):
        env = TypeEnv()
        arr = Name(id="items")
        start = Constant(value=-5)
        assert can_elide_slice(arr, start, None, None, env) is False
    
    def test_negative_slice_stop_not_elided(self):
        env = TypeEnv()
        arr = Name(id="items")
        stop = Constant(value=-1)
        assert can_elide_slice(arr, None, stop, None, env) is False
    
    def test_list_in_list_not_elided(self):
        """[1] in [[1]] needs deep equality."""
        env = TypeEnv()
        env.set_type("nested", PyType.LIST)
        item = List(elts=(Constant(value=1),))
        container = Name(id="nested")
        assert can_elide_in(item, container, env) is False
    
    def test_unknown_type_bool_not_elided(self):
        env = TypeEnv()
        node = Name(id="unknown")
        assert can_elide_bool(node, env) is False
    
    def test_unknown_type_eq_not_elided(self):
        env = TypeEnv()
        left = Name(id="unknown")
        right = Name(id="other")
        assert can_elide_eq(left, right, env) is False
    
    def test_unknown_type_add_not_elided(self):
        env = TypeEnv()
        left = Name(id="unknown")
        right = Name(id="other")
        assert can_elide_add(left, right, env) is False
    
    def test_unknown_type_in_not_elided(self):
        env = TypeEnv()
        item = Constant(value=5)
        container = Name(id="unknown")
        assert can_elide_in(item, container, env) is False


# =============================================================================
# OPTIMIZER INTEGRATION TESTS
# =============================================================================

class TestElisionOptimizerIntegration:
    """Integration tests for the ElisionOptimizer class."""
    
    def test_optimizer_creation(self):
        env = TypeEnv()
        opt = ElisionOptimizer(env)
        assert opt.elision_count == 0
    
    def test_optimizer_counts_elisions(self):
        env = TypeEnv()
        opt = ElisionOptimizer(env)
        
        # Create a __py.bool(x > 0) call
        cmp = Compare(
            left=Name(id="x"),
            ops=("gt",),
            comparators=(Constant(value=0),),
        )
        call = make_py_call("bool", cmp)
        
        result = opt.visit_Call(call)
        assert result is cmp  # Should return the comparison directly
        assert opt.elision_count == 1
    
    def test_optimizer_preserves_non_py_calls(self):
        env = TypeEnv()
        opt = ElisionOptimizer(env)
        
        call = Call(
            func=Name(id="print"),
            args=(Constant(value="hello"),),
            keywords={},
        )
        
        result = opt.visit_Call(call)
        assert result is call
        assert opt.elision_count == 0
    
    def test_count_py_calls(self):
        # Create a program with some __py calls
        stmts = [
            ExprStmt(value=make_py_call("bool", Name(id="x"))),
            ExprStmt(value=make_py_call("eq", Name(id="a"), Name(id="b"))),
        ]
        program = make_program(stmts)
        
        count = count_py_calls(program)
        assert count == 2
    
    def test_elide_wrappers_function(self):
        env = TypeEnv()
        cmp = Compare(
            left=Name(id="x"),
            ops=("gt",),
            comparators=(Constant(value=0),),
        )
        call = make_py_call("bool", cmp)
        stmts = [ExprStmt(value=call)]
        program = make_program(stmts)
        
        result = elide_wrappers(program, env)
        
        # Check the call was elided
        assert isinstance(result.body[0].value, Compare)
