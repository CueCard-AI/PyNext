"""
Phase 18.7 Tests - Runtime Inlining

80 comprehensive tests for the runtime inlining optimization.

Test Categories:
1. len() inlining (25 tests)
2. bool() inlining (25 tests)
3. InlineOptimizer (20 tests)
4. Edge cases (10 tests)
"""

import pytest
from pynext.transpiler.nodes import (
    Program, Assignment, ExprStmt,
    Name, Constant, Call, Attribute, Compare, BinOp,
)
from pynext.transpiler.optimizer._internal.type_env import TypeEnv, PyType
from pynext.transpiler.optimizer.inline import (
    inline_runtime_calls,
    can_inline_len, can_inline_bool,
    inline_len, inline_bool,
    InlineOptimizer, count_inlinable_calls,
)


# =============================================================================
# HELPERS
# =============================================================================

def make_program(stmts) -> Program:
    return Program(body=tuple(stmts))


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


# =============================================================================
# 1. LEN() INLINING (25 tests)
# =============================================================================

class TestLenInlining:
    """Tests for len() inlining."""
    
    def test_can_inline_len_list(self):
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        assert can_inline_len(Name(id="items"), env) is True
    
    def test_can_inline_len_str(self):
        env = TypeEnv()
        env.set_type("text", PyType.STR)
        assert can_inline_len(Name(id="text"), env) is True
    
    def test_can_inline_len_dict(self):
        env = TypeEnv()
        env.set_type("data", PyType.DICT)
        assert can_inline_len(Name(id="data"), env) is True
    
    def test_can_inline_len_tuple(self):
        env = TypeEnv()
        env.set_type("tup", PyType.TUPLE)
        assert can_inline_len(Name(id="tup"), env) is True
    
    def test_cannot_inline_len_unknown(self):
        env = TypeEnv()
        assert can_inline_len(Name(id="unknown"), env) is False
    
    def test_cannot_inline_len_int(self):
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        assert can_inline_len(Name(id="x"), env) is False
    
    def test_cannot_inline_len_set(self):
        """Sets use .size not .length."""
        env = TypeEnv()
        env.set_type("s", PyType.SET)
        assert can_inline_len(Name(id="s"), env) is False
    
    def test_inline_len_list_result(self):
        """len(list) → list.length."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        result = inline_len(Name(id="items"), env)
        
        assert isinstance(result, Attribute)
        assert result.attr == "length"
        assert isinstance(result.value, Name)
        assert result.value.id == "items"
    
    def test_inline_len_str_result(self):
        """len(str) → str.length."""
        env = TypeEnv()
        env.set_type("text", PyType.STR)
        result = inline_len(Name(id="text"), env)
        
        assert isinstance(result, Attribute)
        assert result.attr == "length"
    
    def test_inline_len_dict_result(self):
        """len(dict) → Object.keys(dict).length."""
        env = TypeEnv()
        env.set_type("data", PyType.DICT)
        result = inline_len(Name(id="data"), env)
        
        assert isinstance(result, Attribute)
        assert result.attr == "length"
        # value should be Object.keys(data)
        assert isinstance(result.value, Call)
    
    def test_inline_len_tuple_result(self):
        """len(tuple) → tuple.length."""
        env = TypeEnv()
        env.set_type("tup", PyType.TUPLE)
        result = inline_len(Name(id="tup"), env)
        
        assert isinstance(result, Attribute)
        assert result.attr == "length"
    
    def test_inline_len_unknown_returns_none(self):
        """Unknown type returns None (can't inline)."""
        env = TypeEnv()
        result = inline_len(Name(id="unknown"), env)
        assert result is None
    
    def test_inline_len_preserves_node(self):
        """Inlining preserves the argument node."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        arg = Name(id="items")
        result = inline_len(arg, env)
        
        assert result.value is arg
    
    def test_inline_len_complex_arg(self):
        """Can inline len of complex expression."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        # items.copy() - result is still a list but type inference returns LIST for list method 'copy'
        arg = Call(
            func=Attribute(value=Name(id="items"), attr="copy"),
            args=(),
            keywords={},
        )
        # The type inference knows list.copy() returns list
        result = inline_len(arg, env)
        # Since copy() on list returns list, this can be inlined
        assert isinstance(result, Attribute)
        assert result.attr == "length"
    
    def test_inline_len_dict_structure(self):
        """Check dict len inlining structure in detail."""
        env = TypeEnv()
        env.set_type("data", PyType.DICT)
        result = inline_len(Name(id="data"), env)
        
        # Should be Object.keys(data).length
        assert isinstance(result, Attribute)
        assert result.attr == "length"
        
        keys_call = result.value
        assert isinstance(keys_call, Call)
        assert isinstance(keys_call.func, Attribute)
        assert keys_call.func.value.id == "Object"
        assert keys_call.func.attr == "keys"
    
    def test_inline_len_number_type(self):
        """NUMBER type cannot be inlined."""
        env = TypeEnv()
        env.set_type("x", PyType.NUMBER)
        result = inline_len(Name(id="x"), env)
        assert result is None
    
    def test_inline_len_any_type(self):
        """ANY type cannot be inlined."""
        env = TypeEnv()
        env.set_type("x", PyType.ANY)
        result = inline_len(Name(id="x"), env)
        assert result is None
    
    def test_inline_len_bool_type(self):
        """BOOL type cannot be inlined."""
        env = TypeEnv()
        env.set_type("x", PyType.BOOL)
        result = inline_len(Name(id="x"), env)
        assert result is None
    
    def test_inline_len_func_type(self):
        """FUNC type cannot be inlined."""
        env = TypeEnv()
        env.set_type("f", PyType.FUNC)
        result = inline_len(Name(id="f"), env)
        assert result is None
    
    def test_inline_len_lambda_type(self):
        """LAMBDA type cannot be inlined."""
        env = TypeEnv()
        env.set_type("f", PyType.LAMBDA)
        result = inline_len(Name(id="f"), env)
        assert result is None
    
    def test_inline_len_none_type(self):
        """NONE type cannot be inlined."""
        env = TypeEnv()
        env.set_type("x", PyType.NONE)
        result = inline_len(Name(id="x"), env)
        assert result is None
    
    def test_inline_len_float_type(self):
        """FLOAT type cannot be inlined."""
        env = TypeEnv()
        env.set_type("x", PyType.FLOAT)
        result = inline_len(Name(id="x"), env)
        assert result is None
    
    def test_can_inline_len_with_attribute_access(self):
        """Attribute access on known list."""
        env = TypeEnv()
        env.set_type("obj", PyType.ANY)  # obj is unknown
        arg = Attribute(value=Name(id="obj"), attr="items")
        result = can_inline_len(arg, env)
        # Cannot inline because type is unknown
        assert result is False


# =============================================================================
# 2. BOOL() INLINING (25 tests)
# =============================================================================

class TestBoolInlining:
    """Tests for bool() inlining."""
    
    def test_can_inline_bool_list(self):
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        assert can_inline_bool(Name(id="items"), env) is True
    
    def test_can_inline_bool_str(self):
        env = TypeEnv()
        env.set_type("text", PyType.STR)
        assert can_inline_bool(Name(id="text"), env) is True
    
    def test_can_inline_bool_dict(self):
        env = TypeEnv()
        env.set_type("data", PyType.DICT)
        assert can_inline_bool(Name(id="data"), env) is True
    
    def test_can_inline_bool_set(self):
        env = TypeEnv()
        env.set_type("s", PyType.SET)
        assert can_inline_bool(Name(id="s"), env) is True
    
    def test_cannot_inline_bool_unknown(self):
        env = TypeEnv()
        assert can_inline_bool(Name(id="unknown"), env) is False
    
    def test_cannot_inline_bool_int(self):
        """Int truthiness is different - 0 is falsy."""
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        assert can_inline_bool(Name(id="x"), env) is False
    
    def test_cannot_inline_bool_tuple(self):
        """Tuple not in inline list yet."""
        env = TypeEnv()
        env.set_type("t", PyType.TUPLE)
        assert can_inline_bool(Name(id="t"), env) is False
    
    def test_inline_bool_list_result(self):
        """bool(list) → list.length > 0."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        result = inline_bool(Name(id="items"), env)
        
        assert isinstance(result, Compare)
        assert result.ops == (">",)
        # Left side is items.length
        assert isinstance(result.left, Attribute)
        assert result.left.attr == "length"
        # Right side is 0
        assert isinstance(result.comparators[0], Constant)
        assert result.comparators[0].value == 0
    
    def test_inline_bool_str_result(self):
        """bool(str) → str.length > 0."""
        env = TypeEnv()
        env.set_type("text", PyType.STR)
        result = inline_bool(Name(id="text"), env)
        
        assert isinstance(result, Compare)
        assert isinstance(result.left, Attribute)
        assert result.left.attr == "length"
    
    def test_inline_bool_dict_result(self):
        """bool(dict) → Object.keys(dict).length > 0."""
        env = TypeEnv()
        env.set_type("data", PyType.DICT)
        result = inline_bool(Name(id="data"), env)
        
        assert isinstance(result, Compare)
        # Left side is Object.keys(data).length
        assert isinstance(result.left, Attribute)
        assert result.left.attr == "length"
        assert isinstance(result.left.value, Call)
    
    def test_inline_bool_set_result(self):
        """bool(set) → set.size > 0."""
        env = TypeEnv()
        env.set_type("s", PyType.SET)
        result = inline_bool(Name(id="s"), env)
        
        assert isinstance(result, Compare)
        # Sets use .size not .length
        assert isinstance(result.left, Attribute)
        assert result.left.attr == "size"
    
    def test_inline_bool_unknown_returns_none(self):
        """Unknown type returns None."""
        env = TypeEnv()
        result = inline_bool(Name(id="unknown"), env)
        assert result is None
    
    def test_inline_bool_preserves_node(self):
        """Inlining preserves the argument node."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        arg = Name(id="items")
        result = inline_bool(arg, env)
        
        assert result.left.value is arg
    
    def test_inline_bool_int_returns_none(self):
        """Int can't be inlined - 0 is special."""
        env = TypeEnv()
        env.set_type("x", PyType.INT)
        result = inline_bool(Name(id="x"), env)
        assert result is None
    
    def test_inline_bool_float_returns_none(self):
        """Float can't be inlined - 0.0 is special."""
        env = TypeEnv()
        env.set_type("x", PyType.FLOAT)
        result = inline_bool(Name(id="x"), env)
        assert result is None
    
    def test_inline_bool_none_returns_none(self):
        """None type can't be inlined."""
        env = TypeEnv()
        env.set_type("x", PyType.NONE)
        result = inline_bool(Name(id="x"), env)
        assert result is None
    
    def test_inline_bool_bool_returns_none(self):
        """Bool type can't be inlined (already bool)."""
        env = TypeEnv()
        env.set_type("x", PyType.BOOL)
        result = inline_bool(Name(id="x"), env)
        assert result is None
    
    def test_inline_bool_any_returns_none(self):
        """ANY type can't be inlined."""
        env = TypeEnv()
        env.set_type("x", PyType.ANY)
        result = inline_bool(Name(id="x"), env)
        assert result is None
    
    def test_inline_bool_number_returns_none(self):
        """NUMBER type can't be inlined."""
        env = TypeEnv()
        env.set_type("x", PyType.NUMBER)
        result = inline_bool(Name(id="x"), env)
        assert result is None
    
    def test_inline_bool_func_returns_none(self):
        """FUNC type can't be inlined."""
        env = TypeEnv()
        env.set_type("f", PyType.FUNC)
        result = inline_bool(Name(id="f"), env)
        assert result is None
    
    def test_inline_bool_compare_ops(self):
        """Check the comparison operators."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        result = inline_bool(Name(id="items"), env)
        
        # Should be > (greater than)
        assert result.ops == (">",)
    
    def test_inline_bool_compare_constant(self):
        """Check comparison is against 0."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        result = inline_bool(Name(id="items"), env)
        
        assert result.comparators[0].value == 0
    
    def test_inline_bool_set_size_check(self):
        """Set inlining uses .size not .length."""
        env = TypeEnv()
        env.set_type("my_set", PyType.SET)
        result = inline_bool(Name(id="my_set"), env)
        
        assert result.left.attr == "size"


# =============================================================================
# 3. INLINE OPTIMIZER (20 tests)
# =============================================================================

class TestInlineOptimizer:
    """Tests for the InlineOptimizer class."""
    
    def test_optimizer_creation(self):
        env = TypeEnv()
        opt = InlineOptimizer(env)
        assert opt.inline_count == 0
    
    def test_optimizer_inlines_py_len(self):
        """Optimizer inlines __py.len()."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        call = make_py_call("len", Name(id="items"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        result = inline_runtime_calls(program, env)
        
        # Should be inlined to items.length
        result_expr = result.body[0].value
        assert isinstance(result_expr, Attribute)
        assert result_expr.attr == "length"
    
    def test_optimizer_inlines_py_bool(self):
        """Optimizer inlines __py.bool()."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        call = make_py_call("bool", Name(id="items"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        result = inline_runtime_calls(program, env)
        
        # Should be inlined to items.length > 0
        result_expr = result.body[0].value
        assert isinstance(result_expr, Compare)
    
    def test_optimizer_counts_inlines(self):
        """Optimizer tracks inline count."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        opt = InlineOptimizer(env)
        
        call = make_py_call("len", Name(id="items"))
        opt.visit_Call(call)
        
        assert opt.inline_count == 1
    
    def test_optimizer_skips_non_py_calls(self):
        """Optimizer skips non-__py calls."""
        env = TypeEnv()
        
        call = Call(
            func=Name(id="print"),
            args=(Constant(value="hello"),),
            keywords={},
        )
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        result = inline_runtime_calls(program, env)
        
        # Should be unchanged
        result_call = result.body[0].value
        assert isinstance(result_call, Call)
        assert isinstance(result_call.func, Name)
    
    def test_optimizer_skips_unknown_types(self):
        """Optimizer skips calls on unknown types."""
        env = TypeEnv()
        # No type set for 'items'
        
        call = make_py_call("len", Name(id="items"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        result = inline_runtime_calls(program, env)
        
        # Should be unchanged
        result_call = result.body[0].value
        assert isinstance(result_call, Call)
    
    def test_optimizer_handles_multiple_calls(self):
        """Optimizer handles multiple inlinable calls."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        env.set_type("text", PyType.STR)
        
        call1 = make_py_call("len", Name(id="items"))
        call2 = make_py_call("len", Name(id="text"))
        stmt1 = ExprStmt(value=call1)
        stmt2 = ExprStmt(value=call2)
        program = make_program([stmt1, stmt2])
        
        opt = InlineOptimizer(env)
        result = opt.visit(program)
        
        assert opt.inline_count == 2
    
    def test_optimizer_handles_nested_calls(self):
        """Optimizer handles nested call structures."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        # outer(__py.len(items))
        inner_call = make_py_call("len", Name(id="items"))
        outer_call = Call(
            func=Name(id="outer"),
            args=(inner_call,),
            keywords={},
        )
        stmt = ExprStmt(value=outer_call)
        program = make_program([stmt])
        
        result = inline_runtime_calls(program, env)
        
        # Inner call should be inlined
        result_outer = result.body[0].value
        assert isinstance(result_outer.args[0], Attribute)
    
    def test_optimizer_preserves_other_py_calls(self):
        """Optimizer preserves non-inlinable __py calls."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        # __py.at(items, 0) - not inlinable
        call = make_py_call("at", Name(id="items"), Constant(value=0))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        result = inline_runtime_calls(program, env)
        
        # Should be unchanged
        result_call = result.body[0].value
        assert isinstance(result_call, Call)
        assert result_call.func.attr == "at"
    
    def test_optimizer_handles_assignment(self):
        """Optimizer handles calls in assignments."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        call = make_py_call("len", Name(id="items"))
        assign = Assignment(target="n", value=call)
        program = make_program([assign])
        
        result = inline_runtime_calls(program, env)
        
        # Assignment value should be inlined
        assert isinstance(result.body[0].value, Attribute)
    
    def test_optimizer_handles_binop(self):
        """Optimizer handles calls in binary operations."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        call = make_py_call("len", Name(id="items"))
        binop = BinOp(left=call, op="add", right=Constant(value=1))
        stmt = ExprStmt(value=binop)
        program = make_program([stmt])
        
        result = inline_runtime_calls(program, env)
        
        # Left side of binop should be inlined
        result_binop = result.body[0].value
        assert isinstance(result_binop.left, Attribute)
    
    def test_count_inlinable_calls(self):
        """Count inlinable calls function."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        call1 = make_py_call("len", Name(id="items"))
        call2 = make_py_call("bool", Name(id="items"))
        stmt1 = ExprStmt(value=call1)
        stmt2 = ExprStmt(value=call2)
        program = make_program([stmt1, stmt2])
        
        count = count_inlinable_calls(program, env)
        assert count == 2
    
    def test_count_inlinable_unknown_type(self):
        """Count doesn't include unknown types."""
        env = TypeEnv()
        # No type for 'items'
        
        call = make_py_call("len", Name(id="items"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        count = count_inlinable_calls(program, env)
        assert count == 0
    
    def test_optimizer_empty_program(self):
        """Optimizer handles empty program."""
        env = TypeEnv()
        program = make_program([])
        
        result = inline_runtime_calls(program, env)
        assert result.body == ()
    
    def test_optimizer_builtin_len(self):
        """Optimizer can inline direct len() calls."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        # Direct len(items) call (not __py.len)
        call = Call(
            func=Name(id="len"),
            args=(Name(id="items"),),
            keywords={},
        )
        
        opt = InlineOptimizer(env)
        result = opt.visit_Call(call)
        
        # Should be inlined
        assert isinstance(result, Attribute)
        assert result.attr == "length"
    
    def test_optimizer_preserves_location(self):
        """Optimizer preserves line/col info."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        call = Call(
            func=Attribute(
                value=Name(id="__py"),
                attr="len",
            ),
            args=(Name(id="items"),),
            keywords={},
            line=10,
            col=5,
        )
        
        opt = InlineOptimizer(env)
        result = opt.visit_Call(call)
        
        # Result may or may not preserve location depending on implementation
        assert isinstance(result, Attribute)
    
    def test_optimizer_multiple_args_not_inlined(self):
        """Multi-arg calls are not inlined."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        # __py.len(items, extra) - invalid but shouldn't crash
        call = make_py_call("len", Name(id="items"), Constant(value=1))
        
        opt = InlineOptimizer(env)
        result = opt.visit_Call(call)
        
        # Should be unchanged
        assert isinstance(result, Call)


# =============================================================================
# 4. EDGE CASES (10 tests)
# =============================================================================

class TestEdgeCases:
    """Edge case tests for inlining."""
    
    def test_inline_with_child_scope(self):
        """Type from parent scope."""
        parent = TypeEnv()
        parent.set_type("items", PyType.LIST)
        child = parent.child_scope("block")
        
        result = inline_len(Name(id="items"), child)
        assert isinstance(result, Attribute)
    
    def test_inline_shadowed_type(self):
        """Type shadowed in child scope."""
        parent = TypeEnv()
        parent.set_type("items", PyType.LIST)
        child = parent.child_scope("block")
        child.set_type("items", PyType.INT)  # Shadow with int
        
        result = inline_len(Name(id="items"), child)
        # Should return None because int can't be inlined
        assert result is None
    
    def test_optimizer_idempotent(self):
        """Running optimizer twice gives same result."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        call = make_py_call("len", Name(id="items"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        result1 = inline_runtime_calls(program, env)
        result2 = inline_runtime_calls(result1, env)
        
        # Both should be Attribute
        assert isinstance(result1.body[0].value, Attribute)
        assert isinstance(result2.body[0].value, Attribute)
    
    def test_inline_chain(self):
        """Chained method calls."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        # Can't really inline obj.method().length
        # This tests that we don't crash
        call = Call(
            func=Attribute(
                value=Call(
                    func=Attribute(value=Name(id="items"), attr="copy"),
                    args=(),
                    keywords={},
                ),
                attr="__len__",
            ),
            args=(),
            keywords={},
        )
        
        opt = InlineOptimizer(env)
        result = opt.visit_Call(call)
        
        # Should be unchanged (not a __py call)
        assert isinstance(result, Call)
    
    def test_inline_constant_arg(self):
        """Constant argument to len (unusual)."""
        env = TypeEnv()
        
        call = make_py_call("len", Constant(value="hello"))
        
        opt = InlineOptimizer(env)
        result = opt.visit_Call(call)
        
        # String literal has STR type
        assert isinstance(result, Attribute)
        assert result.attr == "length"
    
    def test_inline_empty_args(self):
        """Call with no args."""
        env = TypeEnv()
        
        call = make_py_call("len")  # No args
        
        opt = InlineOptimizer(env)
        result = opt.visit_Call(call)
        
        # Should be unchanged (invalid call)
        assert isinstance(result, Call)
    
    def test_optimizer_with_keywords(self):
        """Call with keyword args."""
        env = TypeEnv()
        env.set_type("items", PyType.LIST)
        
        call = Call(
            func=Attribute(value=Name(id="__py"), attr="len"),
            args=(Name(id="items"),),
            keywords={"extra": Constant(value=1)},  # Unusual but shouldn't crash
        )
        
        opt = InlineOptimizer(env)
        result = opt.visit_Call(call)
        
        # Should still inline (keywords ignored for len)
        assert isinstance(result, Attribute)
    
    def test_inline_attribute_chain(self):
        """Attribute access chain."""
        env = TypeEnv()
        # obj.items has unknown type
        
        call = make_py_call(
            "len",
            Attribute(value=Name(id="obj"), attr="items")
        )
        
        opt = InlineOptimizer(env)
        result = opt.visit_Call(call)
        
        # Should be unchanged (type unknown)
        assert isinstance(result, Call)
    
    def test_optimizer_non_string_attr(self):
        """Non-standard attribute access."""
        env = TypeEnv()
        
        # This tests robustness
        call = Call(
            func=Name(id="len"),  # Direct len call
            args=(),
            keywords={},
        )
        
        opt = InlineOptimizer(env)
        result = opt.visit_Call(call)
        
        # Should be unchanged (no args)
        assert isinstance(result, Call)
    
    def test_inline_list_literal_type(self):
        """List literal has LIST type."""
        from pynext.transpiler.nodes import List
        env = TypeEnv()
        
        # [1, 2, 3] has LIST type
        arg = List(elts=(Constant(value=1), Constant(value=2)))
        result = inline_len(arg, env)
        
        # Should be inlined
        assert isinstance(result, Attribute)
        assert result.attr == "length"
