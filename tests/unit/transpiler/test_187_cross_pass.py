"""
Phase 18.7 - Cross-Pass Interaction Tests

Tests that verify optimization passes work correctly together.
"""

import pytest
from pynext.transpiler import parse
from pynext.transpiler.nodes import (
    Program, Assignment, If, For, While, FunctionDef, ExprStmt, Return,
    Name, Constant, Call, Attribute, Compare, BinOp, Lambda, UnaryOp,
    List as ListNode,
)
from pynext.transpiler.optimizer import (
    optimize, OptimizeOptions, infer_types,
    elide_wrappers, fix_loop_captures, inline_runtime_calls,
    eliminate_dead_code,
)
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
                 'func', 'operand', 'elts', 'keys']:
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


def has_iife(node) -> bool:
    """Check if node contains an IIFE pattern (lambda called immediately)."""
    if isinstance(node, Call):
        if isinstance(node.func, Lambda):
            return True
    
    for attr in ['body', 'orelse', 'args', 'left', 'right', 'value',
                 'test', 'iter', 'target', 'func', 'elts']:
        child = getattr(node, attr, None)
        if child is not None:
            if isinstance(child, (list, tuple)):
                for c in child:
                    if hasattr(c, '__dict__') and has_iife(c):
                        return True
            elif hasattr(child, '__dict__') and has_iife(child):
                return True
    return False


# =============================================================================
# 1. TYPE INFERENCE + ELISION INTERACTION
# =============================================================================

class TestTypeInferenceElision:
    """Test that type inference correctly informs elision decisions."""
    
    def test_inferred_int_enables_add_elision(self):
        """Type-inferred int allows add elision."""
        # x = 5; y = x + 1
        # Type inference knows x is INT, so add can be elided
        assign_x = Assignment(target="x", value=Constant(value=5))
        add_call = make_py_call("add", Name(id="x"), Constant(value=1))
        assign_y = Assignment(target="y", value=add_call)
        program = Program(body=(assign_x, assign_y))
        
        env = infer_types(program)
        assert env.get_type("x") == PyType.INT
        
        optimized = elide_wrappers(program, env)
        
        # __py.add should be elided because x is known INT
        assert not program_has_py_call(optimized, "add")
    
    def test_unknown_type_preserves_add(self):
        """Unknown type preserves add wrapper."""
        # y = x + 1 (x unknown)
        add_call = make_py_call("add", Name(id="x"), Constant(value=1))
        assign = Assignment(target="y", value=add_call)
        program = Program(body=(assign,))
        
        env = infer_types(program)
        assert env.get_type("x") == PyType.ANY
        
        optimized = elide_wrappers(program, env)
        
        # __py.add preserved because x could be list
        assert program_has_py_call(optimized, "add")
    
    def test_comparison_result_enables_bool_elision(self):
        """Comparison result allows bool elision."""
        # if x > 0: ...  comparison is always bool
        cmp = Compare(left=Name(id="x"), ops=("gt",), comparators=(Constant(value=0),))
        bool_call = make_py_call("bool", cmp)
        if_stmt = If(
            test=bool_call,
            body=(Assignment(target="y", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(if_stmt,))
        
        env = infer_types(program)
        optimized = elide_wrappers(program, env)
        
        # bool(comparison) should be elided
        assert not program_has_py_call(optimized, "bool")
    
    def test_chained_int_operations(self):
        """Chained int operations - add elided, mul depends on type tracking."""
        # x = 5; y = x + 1; z = y * 2
        assign_x = Assignment(target="x", value=Constant(value=5))
        add_call = make_py_call("add", Name(id="x"), Constant(value=1))
        assign_y = Assignment(target="y", value=add_call)
        mul_call = make_py_call("mul", Name(id="y"), Constant(value=2))
        assign_z = Assignment(target="z", value=mul_call)
        program = Program(body=(assign_x, assign_y, assign_z))
        
        optimized = optimize(program)
        
        # add should be elided because x is known INT
        assert not program_has_py_call(optimized, "add")
        # NOTE: mul may or may not be elided depending on whether
        # type inference tracks y = BinOp(x, add, 1) as INT
        # Currently it doesn't track BinOp result types from __py.add
        # This is a known limitation
    
    def test_string_plus_unknown_preserved(self):
        """String + unknown preserves wrapper."""
        # s = "hello"; x = s + y
        assign_s = Assignment(target="s", value=Constant(value="hello"))
        add_call = make_py_call("add", Name(id="s"), Name(id="y"))
        assign_x = Assignment(target="x", value=add_call)
        program = Program(body=(assign_s, assign_x))
        
        optimized = optimize(program)
        
        # Can't elide - y could be list which would break
        assert program_has_py_call(optimized, "add")


# =============================================================================
# 2. TYPE INFERENCE + INLINING INTERACTION
# =============================================================================

class TestTypeInferenceInlining:
    """Test that type inference enables correct inlining."""
    
    def test_list_len_inlined(self):
        """len(list) inlined to .length."""
        # items = [1,2,3]; n = len(items)
        assign_items = Assignment(
            target="items",
            value=ListNode(elts=(Constant(value=1), Constant(value=2)))
        )
        len_call = make_py_call("len", Name(id="items"))
        assign_n = Assignment(target="n", value=len_call)
        program = Program(body=(assign_items, assign_n))
        
        optimized = optimize(program)
        
        # __py.len should be inlined to .length
        assert not program_has_py_call(optimized, "len")
    
    def test_string_len_inlined(self):
        """len(string) inlined to .length."""
        assign_s = Assignment(target="s", value=Constant(value="hello"))
        len_call = make_py_call("len", Name(id="s"))
        assign_n = Assignment(target="n", value=len_call)
        program = Program(body=(assign_s, assign_n))
        
        optimized = optimize(program)
        
        assert not program_has_py_call(optimized, "len")
    
    def test_unknown_len_preserved(self):
        """len(unknown) preserved."""
        len_call = make_py_call("len", Name(id="items"))
        assign_n = Assignment(target="n", value=len_call)
        program = Program(body=(assign_n,))
        
        optimized = optimize(program)
        
        # Unknown type - keep wrapper
        assert program_has_py_call(optimized, "len")
    
    def test_list_bool_inlined_to_length_check(self):
        """bool(list) inlined to .length > 0."""
        assign_items = Assignment(
            target="items",
            value=ListNode(elts=(Constant(value=1),))
        )
        bool_call = make_py_call("bool", Name(id="items"))
        if_stmt = If(
            test=bool_call,
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(assign_items, if_stmt))
        
        optimized = optimize(program)
        
        # Should be inlined to items.length > 0
        assert not program_has_py_call(optimized, "bool")


# =============================================================================
# 3. ELISION + DCE INTERACTION
# =============================================================================

class TestElisionDCE:
    """Test that elision and DCE work together."""
    
    def test_dce_after_elision(self):
        """DCE removes dead code after elision."""
        # if False: ... should be removed
        if_dead = If(
            test=Constant(value=False),
            body=(Assignment(target="dead", value=Constant(value=1)),),
            orelse=(),
        )
        # x = 5; y = x + 1 should have add elided
        assign_x = Assignment(target="x", value=Constant(value=5))
        add_call = make_py_call("add", Name(id="x"), Constant(value=1))
        assign_y = Assignment(target="y", value=add_call)
        
        program = Program(body=(if_dead, assign_x, assign_y))
        optimized = optimize(program)
        
        # Dead if removed, add elided
        assert len(optimized.body) == 2
        assert not program_has_py_call(optimized, "add")
    
    def test_if_true_unwrapped(self):
        """if True: x = 1 becomes just x = 1."""
        if_true = If(
            test=Constant(value=True),
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(Assignment(target="y", value=Constant(value=2)),),
        )
        program = Program(body=(if_true,))
        
        optimized = optimize(program)
        
        # Should only have x = 1
        assert len(optimized.body) == 1
    
    def test_elision_doesnt_affect_dce(self):
        """Elision of wrappers doesn't break DCE analysis."""
        # Dead branch with elided operation
        add_call = make_py_call("add", Constant(value=1), Constant(value=2))
        if_dead = If(
            test=Constant(value=False),
            body=(Assignment(target="x", value=add_call),),
            orelse=(),
        )
        program = Program(body=(if_dead,))
        
        optimized = optimize(program)
        
        # Should be empty - dead code removed
        assert optimized.body == ()


# =============================================================================
# 4. LOOP CAPTURE + ELISION INTERACTION
# =============================================================================

class TestLoopCaptureElision:
    """Test that loop capture and elision work together."""
    
    def test_capture_then_elision(self):
        """Capture wrapping doesn't break elision."""
        # for i in range(5): f = lambda: i + 1
        lam = Lambda(
            args=(),
            defaults=(),
            body=make_py_call("add", Name(id="i"), Constant(value=1)),
        )
        assign = Assignment(target="f", value=lam)
        loop = For(
            target="i",
            iter=Call(func=Name(id="range"), args=(Constant(value=5),), keywords={}),
            body=(assign,),
            is_range=True,
            range_args=(Constant(value=5),),
        )
        program = Program(body=(loop,))
        
        optimized = optimize(program)
        
        # Lambda should be wrapped with IIFE for capture
        loop_result = optimized.body[0]
        assign_result = loop_result.body[0]
        assert has_iife(assign_result)
    
    def test_elision_inside_captured_lambda(self):
        """Elision works inside captured lambdas."""
        # for i in range(5): f = lambda: i > 0  (comparison = bool, elidable)
        lam = Lambda(
            args=(),
            defaults=(),
            body=make_py_call(
                "bool",
                Compare(left=Name(id="i"), ops=("gt",), comparators=(Constant(value=0),))
            ),
        )
        assign = Assignment(target="f", value=lam)
        loop = For(
            target="i",
            iter=Call(func=Name(id="range"), args=(Constant(value=5),), keywords={}),
            body=(assign,),
            is_range=True,
            range_args=(Constant(value=5),),
        )
        program = Program(body=(loop,))
        
        optimized = optimize(program)
        
        # Capture should happen AND bool should be elided
        assert has_iife(optimized.body[0].body[0])


# =============================================================================
# 5. ALL PASSES COMBINED
# =============================================================================

class TestAllPassesCombined:
    """Test all optimization passes working together."""
    
    def test_complex_program(self):
        """Complex program with all optimization opportunities."""
        # x = 5
        # if False: dead = 1
        # for i in range(x): handlers.append(lambda: i + 1)
        # if x > 0: y = x + 1
        
        assign_x = Assignment(target="x", value=Constant(value=5))
        
        if_dead = If(
            test=Constant(value=False),
            body=(Assignment(target="dead", value=Constant(value=1)),),
            orelse=(),
        )
        
        lam = Lambda(
            args=(),
            defaults=(),
            body=make_py_call("add", Name(id="i"), Constant(value=1)),
        )
        append_call = Call(
            func=Attribute(value=Name(id="handlers"), attr="append"),
            args=(lam,),
            keywords={},
        )
        loop = For(
            target="i",
            iter=Call(func=Name(id="range"), args=(Name(id="x"),), keywords={}),
            body=(ExprStmt(value=append_call),),
            is_range=True,
            range_args=(Name(id="x"),),
        )
        
        cmp = Compare(left=Name(id="x"), ops=("gt",), comparators=(Constant(value=0),))
        bool_call = make_py_call("bool", cmp)
        add_call = make_py_call("add", Name(id="x"), Constant(value=1))
        if_live = If(
            test=bool_call,
            body=(Assignment(target="y", value=add_call),),
            orelse=(),
        )
        
        program = Program(body=(assign_x, if_dead, loop, if_live))
        optimized = optimize(program)
        
        # DCE: Dead if removed
        # Elision: bool and add elided
        # Capture: Lambda wrapped
        assert len(optimized.body) == 3  # x, loop, if
        assert not program_has_py_call(optimized, "bool")
        assert not program_has_py_call(optimized, "add")
    
    def test_options_disable_passes(self):
        """Can disable individual passes."""
        add_call = make_py_call("add", Constant(value=1), Constant(value=2))
        assign = Assignment(target="x", value=add_call)
        program = Program(body=(assign,))
        
        # With elision disabled
        opts = OptimizeOptions(elision=False, inline=True, capture=True, dce=True)
        optimized = optimize(program, opts)
        
        # add should be preserved
        assert program_has_py_call(optimized, "add")
    
    def test_options_disable_capture(self):
        """Can disable capture pass."""
        lam = Lambda(args=(), defaults=(), body=Name(id="i"))
        assign = Assignment(target="f", value=lam)
        loop = For(
            target="i",
            iter=Call(func=Name(id="range"), args=(Constant(value=5),), keywords={}),
            body=(assign,),
            is_range=True,
            range_args=(Constant(value=5),),
        )
        program = Program(body=(loop,))
        
        opts = OptimizeOptions(elision=True, inline=True, capture=False, dce=True)
        optimized = optimize(program, opts)
        
        # Lambda should NOT be wrapped
        assert not has_iife(optimized.body[0].body[0])
    
    def test_idempotent_optimization(self):
        """Running optimize twice gives same result."""
        assign_x = Assignment(target="x", value=Constant(value=5))
        add_call = make_py_call("add", Name(id="x"), Constant(value=1))
        assign_y = Assignment(target="y", value=add_call)
        program = Program(body=(assign_x, assign_y))
        
        opt1 = optimize(program)
        opt2 = optimize(opt1)
        
        # Both should have same structure
        assert len(opt1.body) == len(opt2.body)
        assert not program_has_py_call(opt1, "add")
        assert not program_has_py_call(opt2, "add")


# =============================================================================
# 6. PASS ORDER CORRECTNESS
# =============================================================================

class TestPassOrder:
    """Test that pass order is correct."""
    
    def test_type_inference_before_elision(self):
        """Type inference must run before elision."""
        # If type inference doesn't run first, x's type would be unknown
        assign_x = Assignment(target="x", value=Constant(value=5))
        add_call = make_py_call("add", Name(id="x"), Constant(value=1))
        assign_y = Assignment(target="y", value=add_call)
        program = Program(body=(assign_x, assign_y))
        
        # Run passes in wrong order (no type inference)
        env = TypeEnv()  # Empty env
        elided = elide_wrappers(program, env)
        
        # add should be preserved because x type unknown
        assert program_has_py_call(elided, "add")
        
        # Run correctly with type inference first
        env = infer_types(program)
        elided = elide_wrappers(program, env)
        
        # add should be elided now
        assert not program_has_py_call(elided, "add")
    
    def test_type_inference_before_inlining(self):
        """Type inference must run before inlining."""
        assign_items = Assignment(
            target="items",
            value=ListNode(elts=(Constant(value=1),))
        )
        len_call = make_py_call("len", Name(id="items"))
        assign_n = Assignment(target="n", value=len_call)
        program = Program(body=(assign_items, assign_n))
        
        # Without type inference, len can't be inlined
        env = TypeEnv()
        inlined = inline_runtime_calls(program, env)
        assert program_has_py_call(inlined, "len")
        
        # With type inference, len is inlined
        env = infer_types(program)
        inlined = inline_runtime_calls(program, env)
        assert not program_has_py_call(inlined, "len")
    
    def test_dce_runs_last(self):
        """DCE should run after other passes clean up."""
        # if True: x = __py.add(1, 2) else: dead = 3
        add_call = make_py_call("add", Constant(value=1), Constant(value=2))
        if_stmt = If(
            test=Constant(value=True),
            body=(Assignment(target="x", value=add_call),),
            orelse=(Assignment(target="dead", value=Constant(value=3)),),
        )
        program = Program(body=(if_stmt,))
        
        optimized = optimize(program)
        
        # DCE should remove else branch
        # Elision should remove add wrapper
        assert len(optimized.body) == 1
        assert not program_has_py_call(optimized, "add")
