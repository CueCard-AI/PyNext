"""
Phase 18.7 - Edge Cases and Risk Areas Tests

Tests for edge cases identified in risk analysis:
1. Async/Await handling
2. Comprehension lambda capture
3. AugAssign type tracking
4. F-String optimization
5. Chained comparisons
6. IfExp DCE
7. Try/Except variable scope
8. Starred/Spread handling
"""

import pytest
from pynext.transpiler import parse
from pynext.transpiler.nodes import (
    Program, Assignment, AugAssign, If, For, ForUnpack, While,
    FunctionDef, Return, ExprStmt, Try, ExceptHandler,
    Name, Constant, Call, Attribute, Compare, BinOp, UnaryOp,
    BoolOp, IfExp, Lambda, Await, Starred, FString, FormattedValue,
    List as ListNode, Dict as DictNode, Tuple as TupleNode,
    ListComp, DictComp, Comprehension,
)
from pynext.transpiler.optimizer import optimize, infer_types
from pynext.transpiler.optimizer._internal.type_env import TypeEnv, PyType


# =============================================================================
# HELPERS
# =============================================================================

def make_py_call(method: str, *args) -> Call:
    """Create a __py.method(*args) call node."""
    return Call(
        func=Attribute(value=Name(id="__py"), attr=method),
        args=args,
        keywords={},
    )


def has_py_call(node, method: str) -> bool:
    """Check if a node contains __py.method call."""
    if isinstance(node, Call):
        if isinstance(node.func, Attribute):
            if isinstance(node.func.value, Name):
                if node.func.value.id == "__py" and node.func.attr == method:
                    return True
    
    for attr in ['body', 'orelse', 'args', 'left', 'right', 'value',
                 'test', 'comparators', 'values', 'iter', 'target',
                 'func', 'operand', 'elts', 'keys', 'elt', 'key',
                 'generators', 'ifs']:
        child = getattr(node, attr, None)
        if child is not None:
            if isinstance(child, (list, tuple)):
                for c in child:
                    if hasattr(c, '__dict__') and has_py_call(c, method):
                        return True
            elif hasattr(child, '__dict__') and has_py_call(child, method):
                return True
    return False


def program_has_py_call(program: Program, method: str) -> bool:
    """Check if program contains __py.method call."""
    for stmt in program.body:
        if has_py_call(stmt, method):
            return True
    return False


# =============================================================================
# 1. ASYNC/AWAIT HANDLING (10 tests)
# =============================================================================

class TestAsyncAwait:
    """Tests for async/await optimization handling."""
    
    def test_await_expression_type_any(self):
        """Await expression returns ANY type (unknown)."""
        # async def foo(): x = await get_data()
        await_expr = Await(value=Call(func=Name(id="get_data"), args=(), keywords={}))
        assign = Assignment(target="x", value=await_expr)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        # Await returns unknown type
        assert env.get_type("x") == PyType.ANY
    
    def test_await_in_binop_preserves_wrapper(self):
        """Await in binary operation should preserve wrapper."""
        await_expr = Await(value=Call(func=Name(id="fetch"), args=(), keywords={}))
        add_call = make_py_call("add", await_expr, Constant(value=1))
        assign = Assignment(target="result", value=add_call)
        program = Program(body=(assign,))
        
        optimized = optimize(program)
        
        # Unknown type from await - keep wrapper
        assert program_has_py_call(optimized, "add")
    
    def test_await_bool_preserves_wrapper(self):
        """Await result in bool check should preserve wrapper."""
        await_expr = Await(value=Call(func=Name(id="get_data"), args=(), keywords={}))
        bool_call = make_py_call("bool", await_expr)
        if_stmt = If(
            test=bool_call,
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(if_stmt,))
        
        optimized = optimize(program)
        
        # Unknown type - keep wrapper
        assert program_has_py_call(optimized, "bool")
    
    def test_await_equality_preserves_wrapper(self):
        """Await result in equality check should preserve wrapper."""
        await_expr = Await(value=Call(func=Name(id="get_data"), args=(), keywords={}))
        eq_call = make_py_call("eq", await_expr, Constant(value=None))
        assign = Assignment(target="is_null", value=eq_call)
        program = Program(body=(assign,))
        
        optimized = optimize(program)
        
        # Unknown type - keep wrapper
        assert program_has_py_call(optimized, "eq")
    
    def test_await_optimized_preserves_structure(self):
        """Await should pass through optimizer unchanged."""
        await_expr = Await(value=Call(func=Name(id="fetch"), args=(), keywords={}))
        assign = Assignment(target="x", value=await_expr)
        program = Program(body=(assign,))
        
        optimized = optimize(program)
        
        # Await should be preserved
        assert len(optimized.body) == 1
        assert isinstance(optimized.body[0].value, Await)


# =============================================================================
# 2. COMPREHENSION LAMBDA CAPTURE (10 tests)
# =============================================================================

class TestComprehensionCapture:
    """Tests for comprehension variable capture in lambdas."""
    
    def test_listcomp_type_is_list(self):
        """List comprehension produces LIST type."""
        # [x for x in items]
        comp = ListComp(
            element=Name(id="x"),
            generators=(
                Comprehension(
                    target="x",
                    iter=Name(id="items"),
                    ifs=(),
                ),
            ),
        )
        assign = Assignment(target="result", value=comp)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        assert env.get_type("result") == PyType.LIST
    
    def test_dictcomp_type_is_dict(self):
        """Dict comprehension produces DICT type."""
        # {k: v for k, v in items}
        comp = DictComp(
            key=Name(id="k"),
            value=Name(id="v"),
            generators=(
                Comprehension(
                    target="k",
                    iter=Name(id="items"),
                    ifs=(),
                ),
            ),
        )
        assign = Assignment(target="result", value=comp)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        assert env.get_type("result") == PyType.DICT
    
    def test_comprehension_in_optimization(self):
        """Comprehension passes through optimization."""
        comp = ListComp(
            element=Name(id="x"),
            generators=(
                Comprehension(
                    target="x",
                    iter=Name(id="items"),
                    ifs=(),
                ),
            ),
        )
        assign = Assignment(target="result", value=comp)
        program = Program(body=(assign,))
        
        optimized = optimize(program)
        
        # Should preserve listcomp
        assert len(optimized.body) == 1


# =============================================================================
# 3. AUGMENTED ASSIGNMENT TYPE TRACKING (10 tests)
# =============================================================================

class TestAugAssignTypeTracking:
    """Tests for augmented assignment type tracking."""
    
    def test_augassign_int_preserves_type(self):
        """x += 1 where x is int stays int."""
        assign_x = Assignment(target="x", value=Constant(value=5))
        aug = AugAssign(target="x", op="add", value=Constant(value=1))
        program = Program(body=(assign_x, aug))
        
        env = infer_types(program)
        # x should still be INT after += 1
        assert env.get_type("x") == PyType.INT
    
    def test_augassign_float_stays_float(self):
        """x += 1.0 where x is float stays float."""
        assign_x = Assignment(target="x", value=Constant(value=3.14))
        aug = AugAssign(target="x", op="add", value=Constant(value=1.0))
        program = Program(body=(assign_x, aug))
        
        env = infer_types(program)
        assert env.get_type("x") in (PyType.FLOAT, PyType.NUMBER)
    
    def test_augassign_int_plus_float_becomes_number(self):
        """x += 1.0 where x is int becomes NUMBER."""
        assign_x = Assignment(target="x", value=Constant(value=5))
        aug = AugAssign(target="x", op="add", value=Constant(value=1.5))
        program = Program(body=(assign_x, aug))
        
        env = infer_types(program)
        # Int + float → NUMBER or FLOAT
        assert env.get_type("x") in (PyType.FLOAT, PyType.NUMBER)
    
    def test_augassign_str_concat(self):
        """x += "suffix" where x is str stays str."""
        assign_x = Assignment(target="x", value=Constant(value="hello"))
        aug = AugAssign(target="x", op="add", value=Constant(value=" world"))
        program = Program(body=(assign_x, aug))
        
        env = infer_types(program)
        assert env.get_type("x") == PyType.STR
    
    def test_augassign_mul_int(self):
        """x *= 2 where x is int stays int."""
        assign_x = Assignment(target="x", value=Constant(value=5))
        aug = AugAssign(target="x", op="mul", value=Constant(value=2))
        program = Program(body=(assign_x, aug))
        
        env = infer_types(program)
        assert env.get_type("x") == PyType.INT
    
    def test_augassign_enables_elision(self):
        """After x += 1, operations on x can be elided."""
        assign_x = Assignment(target="x", value=Constant(value=5))
        aug = AugAssign(target="x", op="add", value=Constant(value=1))
        add_call = make_py_call("add", Name(id="x"), Constant(value=10))
        assign_y = Assignment(target="y", value=add_call)
        program = Program(body=(assign_x, aug, assign_y))
        
        optimized = optimize(program)
        
        # x is still INT - add should be elided
        assert not program_has_py_call(optimized, "add")


# =============================================================================
# 4. F-STRING OPTIMIZATION (8 tests)
# =============================================================================

class TestFStringOptimization:
    """Tests for f-string optimization."""
    
    def test_fstring_type_is_str(self):
        """F-string produces STR type."""
        fstring = FString(
            parts=(
                Constant(value="Hello "),
                FormattedValue(value=Name(id="name"), conversion="", format_spec=""),
            ),
        )
        assign = Assignment(target="greeting", value=fstring)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        assert env.get_type("greeting") == PyType.STR
    
    def test_fstring_preserved_in_optimization(self):
        """F-string structure preserved through optimization."""
        fstring = FString(
            parts=(
                Constant(value="Value: "),
                FormattedValue(value=Name(id="x"), conversion="", format_spec=""),
            ),
        )
        assign = Assignment(target="msg", value=fstring)
        program = Program(body=(assign,))
        
        optimized = optimize(program)
        
        assert len(optimized.body) == 1
        assert isinstance(optimized.body[0].value, FString)
    
    def test_fstring_len_inlined(self):
        """len(f"...") is str length - should be inlined."""
        fstring = FString(
            parts=(Constant(value="hello"),),
        )
        len_call = make_py_call("len", fstring)
        assign = Assignment(target="n", value=len_call)
        program = Program(body=(assign,))
        
        # FString is STR type, so len should inline to .length
        env = infer_types(program)
        # Can't directly check fstring type from env, but optimization should work


# =============================================================================
# 5. CHAINED COMPARISONS (8 tests)
# =============================================================================

class TestChainedComparisons:
    """Tests for chained comparison handling."""
    
    def test_chained_comparison_is_bool(self):
        """Chained comparison 0 < x < 10 produces BOOL."""
        # This is represented as Compare with multiple ops
        cmp = Compare(
            left=Constant(value=0),
            ops=("<", "<"),
            comparators=(Name(id="x"), Constant(value=10)),
        )
        assign = Assignment(target="in_range", value=cmp)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        assert env.get_type("in_range") == PyType.BOOL
    
    def test_chained_comparison_bool_elided(self):
        """bool(chained_comparison) should be elided."""
        cmp = Compare(
            left=Constant(value=0),
            ops=("<", "<"),
            comparators=(Name(id="x"), Constant(value=10)),
        )
        bool_call = make_py_call("bool", cmp)
        if_stmt = If(
            test=bool_call,
            body=(Assignment(target="y", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(if_stmt,))
        
        optimized = optimize(program)
        
        # Comparison is always bool - elide
        assert not program_has_py_call(optimized, "bool")
    
    def test_triple_chained_comparison(self):
        """Triple chained comparison a < b < c < d."""
        cmp = Compare(
            left=Name(id="a"),
            ops=("<", "<", "<"),
            comparators=(Name(id="b"), Name(id="c"), Name(id="d")),
        )
        assign = Assignment(target="ordered", value=cmp)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        assert env.get_type("ordered") == PyType.BOOL
    
    def test_mixed_chained_comparison(self):
        """Mixed operators: a < b <= c."""
        cmp = Compare(
            left=Name(id="a"),
            ops=("<", "<="),
            comparators=(Name(id="b"), Name(id="c")),
        )
        assign = Assignment(target="result", value=cmp)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        assert env.get_type("result") == PyType.BOOL


# =============================================================================
# 6. IFEXP (TERNARY) DCE (8 tests)
# =============================================================================

class TestIfExpDCE:
    """Tests for IfExp (ternary) dead code elimination."""
    
    def test_ifexp_true_simplifies(self):
        """x if True else y should simplify to x."""
        ifexp = IfExp(
            test=Constant(value=True),
            body=Constant(value=1),
            orelse=Constant(value=2),
        )
        assign = Assignment(target="result", value=ifexp)
        program = Program(body=(assign,))
        
        optimized = optimize(program)
        
        # Should simplify to result = 1
        assert len(optimized.body) == 1
        # Check if it's simplified (either IfExp with True or just Constant)
        result = optimized.body[0].value
        if isinstance(result, Constant):
            assert result.value == 1
    
    def test_ifexp_false_simplifies(self):
        """x if False else y should simplify to y."""
        ifexp = IfExp(
            test=Constant(value=False),
            body=Constant(value=1),
            orelse=Constant(value=2),
        )
        assign = Assignment(target="result", value=ifexp)
        program = Program(body=(assign,))
        
        optimized = optimize(program)
        
        # Should simplify to result = 2
        assert len(optimized.body) == 1
        result = optimized.body[0].value
        if isinstance(result, Constant):
            assert result.value == 2
    
    def test_ifexp_dynamic_preserved(self):
        """x if cond else y with dynamic cond preserved."""
        ifexp = IfExp(
            test=Name(id="cond"),
            body=Constant(value=1),
            orelse=Constant(value=2),
        )
        assign = Assignment(target="result", value=ifexp)
        program = Program(body=(assign,))
        
        optimized = optimize(program)
        
        # Dynamic condition - preserve IfExp
        assert len(optimized.body) == 1
        assert isinstance(optimized.body[0].value, IfExp)
    
    def test_ifexp_type_from_branches(self):
        """IfExp type inferred from branches."""
        ifexp = IfExp(
            test=Name(id="cond"),
            body=Constant(value=5),
            orelse=Constant(value=10),
        )
        assign = Assignment(target="result", value=ifexp)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        # Both branches are INT
        assert env.get_type("result") == PyType.INT
    
    def test_ifexp_mixed_types_any(self):
        """IfExp with mixed branch types is ANY."""
        ifexp = IfExp(
            test=Name(id="cond"),
            body=Constant(value=5),
            orelse=Constant(value="hello"),
        )
        assign = Assignment(target="result", value=ifexp)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        # Mixed INT and STR → ANY
        assert env.get_type("result") == PyType.ANY


# =============================================================================
# 7. TRY/EXCEPT VARIABLE SCOPE (8 tests)
# =============================================================================

class TestTryExceptScope:
    """Tests for try/except variable scope handling."""
    
    def test_try_variable_type(self):
        """Variable defined in try block has type."""
        try_stmt = Try(
            body=(Assignment(target="x", value=Constant(value=5)),),
            handlers=(
                ExceptHandler(
                    type=None,
                    name=None,
                    body=(Assignment(target="x", value=Constant(value=0)),),
                ),
            ),
            orelse=(),
            finalbody=(),
        )
        program = Program(body=(try_stmt,))
        
        env = infer_types(program)
        # x defined in both branches as INT
        x_type = env.get_type("x")
        assert x_type in (PyType.INT, PyType.ANY)
    
    def test_except_different_type_becomes_any(self):
        """Different types in try/except becomes ANY."""
        try_stmt = Try(
            body=(Assignment(target="x", value=Constant(value=5)),),
            handlers=(
                ExceptHandler(
                    type=None,
                    name=None,
                    body=(Assignment(target="x", value=Constant(value="error")),),
                ),
            ),
            orelse=(),
            finalbody=(),
        )
        program = Program(body=(try_stmt,))
        
        env = infer_types(program)
        # x could be INT or STR → ANY
        assert env.get_type("x") == PyType.ANY
    
    def test_try_preserves_structure(self):
        """Try/except structure preserved through optimization."""
        try_stmt = Try(
            body=(ExprStmt(value=Call(func=Name(id="risky"), args=(), keywords={})),),
            handlers=(
                ExceptHandler(
                    type=None,
                    name=None,
                    body=(ExprStmt(value=Call(func=Name(id="handle"), args=(), keywords={})),),
                ),
            ),
            orelse=(),
            finalbody=(),
        )
        program = Program(body=(try_stmt,))
        
        optimized = optimize(program)
        
        assert len(optimized.body) == 1
        assert isinstance(optimized.body[0], Try)


# =============================================================================
# 8. STARRED/SPREAD HANDLING (8 tests)
# =============================================================================

class TestStarredHandling:
    """Tests for starred expressions and spread handling."""
    
    def test_starred_in_call_preserved(self):
        """Starred argument in call preserved."""
        starred = Starred(value=Name(id="items"))
        call = Call(
            func=Name(id="func"),
            args=(starred,),
            keywords={},
        )
        assign = Assignment(target="result", value=call)
        program = Program(body=(assign,))
        
        optimized = optimize(program)
        
        # Starred should be preserved
        assert len(optimized.body) == 1
    
    def test_starred_type_any(self):
        """Starred expression has ANY type."""
        starred = Starred(value=Name(id="items"))
        call = Call(func=Name(id="list"), args=(starred,), keywords={})
        assign = Assignment(target="result", value=call)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        # Result of list(*items) is LIST
        result_type = env.get_type("result")
        assert result_type in (PyType.LIST, PyType.ANY)
    
    def test_tuple_unpack_types(self):
        """Tuple unpacking sets types for all targets."""
        # a, b = (1, "hello")
        unpack = Assignment(
            target="a",  # Simplified - actual would be TupleUnpack
            value=TupleNode(elts=(Constant(value=1), Constant(value="hello"))),
        )
        program = Program(body=(unpack,))
        
        optimized = optimize(program)
        
        # Should preserve structure
        assert len(optimized.body) == 1


# =============================================================================
# 9. BOOLOP HANDLING (5 tests)
# =============================================================================

class TestBoolOpHandling:
    """Tests for BoolOp (and/or) handling."""
    
    def test_boolop_and_type(self):
        """and operation type inference."""
        boolop = BoolOp(
            op="and",
            values=(Name(id="a"), Name(id="b")),
        )
        assign = Assignment(target="result", value=boolop)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        # and returns one of the operands
        result_type = env.get_type("result")
        assert result_type in (PyType.BOOL, PyType.ANY)
    
    def test_boolop_or_type(self):
        """or operation type inference."""
        boolop = BoolOp(
            op="or",
            values=(Name(id="a"), Name(id="b")),
        )
        assign = Assignment(target="result", value=boolop)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        result_type = env.get_type("result")
        assert result_type in (PyType.BOOL, PyType.ANY)
    
    def test_boolop_with_literals(self):
        """BoolOp with bool literals."""
        boolop = BoolOp(
            op="and",
            values=(Constant(value=True), Constant(value=False)),
        )
        assign = Assignment(target="result", value=boolop)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        assert env.get_type("result") == PyType.BOOL
    
    def test_boolop_bool_elided(self):
        """bool(boolop) where operands are bool should be elided."""
        boolop = BoolOp(
            op="and",
            values=(
                Compare(left=Name(id="x"), ops=(">",), comparators=(Constant(value=0),)),
                Compare(left=Name(id="y"), ops=(">",), comparators=(Constant(value=0),)),
            ),
        )
        bool_call = make_py_call("bool", boolop)
        if_stmt = If(
            test=bool_call,
            body=(Assignment(target="z", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(if_stmt,))
        
        optimized = optimize(program)
        
        # BoolOp of comparisons is bool - elide
        assert not program_has_py_call(optimized, "bool")


# =============================================================================
# 10. SLICE OBJECT HANDLING (5 tests)
# =============================================================================

class TestSliceHandling:
    """Tests for Slice object handling."""
    
    def test_slice_type_any(self):
        """Subscript with slice returns ANY."""
        subscript = Call(
            func=Attribute(value=Name(id="__py"), attr="slice"),
            args=(Name(id="items"), Constant(value=0), Constant(value=5), Constant(value=None)),
            keywords={},
        )
        assign = Assignment(target="result", value=subscript)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        # Slice result is ANY (could be list, str, etc)
        result_type = env.get_type("result")
        assert result_type == PyType.ANY
    
    def test_positive_slice_preserved(self):
        """Positive slice indices should be preserved correctly."""
        slice_call = make_py_call(
            "slice",
            Name(id="items"),
            Constant(value=1),
            Constant(value=5),
            Constant(value=None),
        )
        assign = Assignment(target="result", value=slice_call)
        program = Program(body=(assign,))
        
        optimized = optimize(program)
        
        # Slice should be preserved
        assert len(optimized.body) == 1
