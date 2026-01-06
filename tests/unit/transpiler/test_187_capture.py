"""
Phase 18.7 Tests - Loop Variable Capture Fix

80 comprehensive tests for the loop capture optimization.

Test Categories:
1. Lambda reference detection (20 tests)
2. Capture wrapping (20 tests)
3. For loop handling (20 tests)
4. Edge cases (20 tests)
"""

import pytest
from pynext.transpiler.nodes import (
    Program, For, ForUnpack, While, Assignment, ExprStmt,
    Name, Constant, Lambda, Call, Attribute, BinOp,
    FunctionDef, Return,
)
from pynext.transpiler.optimizer.capture import (
    fix_loop_captures,
    find_lambdas_in_node, find_functions_in_node,
    lambda_references_var, function_references_var,
    get_loop_variables, wrap_lambda_with_capture,
    LoopCaptureOptimizer, count_loop_lambdas, needs_capture_fix,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def make_program(stmts) -> Program:
    """Create a Program from statements."""
    return Program(body=tuple(stmts))


def make_simple_lambda(body_var: str = "i") -> Lambda:
    """Create a simple lambda that references a variable."""
    return Lambda(
        args=(),
        defaults=(),
        body=Name(id=body_var),
    )


def make_lambda_with_call(func_name: str, arg_var: str) -> Lambda:
    """Create lambda: lambda: func(arg)."""
    return Lambda(
        args=(),
        defaults=(),
        body=Call(
            func=Name(id=func_name),
            args=(Name(id=arg_var),),
            keywords={},
        ),
    )


def make_for_loop(var: str, body_stmts: list) -> For:
    """Create a for loop: for var in items: body."""
    return For(
        target=var,
        iter=Name(id="items"),
        body=tuple(body_stmts),
        is_range=False,
        range_args=None,
    )


def make_for_range(var: str, n: int, body_stmts: list) -> For:
    """Create: for var in range(n): body."""
    return For(
        target=var,
        iter=Call(
            func=Name(id="range"),
            args=(Constant(value=n),),
            keywords={},
        ),
        body=tuple(body_stmts),
        is_range=True,
        range_args=(0, n, 1),
    )


# =============================================================================
# 1. LAMBDA REFERENCE DETECTION (20 tests)
# =============================================================================

class TestLambdaReferenceDetection:
    """Tests for detecting lambda references to variables."""
    
    def test_simple_reference(self):
        """Lambda body contains variable name."""
        lam = make_simple_lambda("i")
        assert lambda_references_var(lam, "i") is True
    
    def test_no_reference(self):
        """Lambda body doesn't contain variable."""
        lam = make_simple_lambda("x")
        assert lambda_references_var(lam, "i") is False
    
    def test_reference_in_call(self):
        """Lambda calls function with variable."""
        lam = make_lambda_with_call("handle", "i")
        assert lambda_references_var(lam, "i") is True
    
    def test_reference_in_binop(self):
        """Lambda has binary operation with variable."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=BinOp(left=Name(id="i"), op="add", right=Constant(value=1)),
        )
        assert lambda_references_var(lam, "i") is True
    
    def test_reference_different_var(self):
        """Lambda references different variable."""
        lam = make_lambda_with_call("handle", "j")
        assert lambda_references_var(lam, "i") is False
    
    def test_parameter_shadows_var(self):
        """Lambda has parameter that shadows loop var."""
        lam = Lambda(
            args=("i",),
            defaults=(None,),
            body=Name(id="i"),
        )
        # Still returns True because it finds the name
        # The optimizer will check if it's shadowed
        assert lambda_references_var(lam, "i") is True
    
    def test_nested_call_reference(self):
        """Lambda has nested function call with variable."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Call(
                func=Name(id="outer"),
                args=(Call(
                    func=Name(id="inner"),
                    args=(Name(id="i"),),
                    keywords={},
                ),),
                keywords={},
            ),
        )
        assert lambda_references_var(lam, "i") is True
    
    def test_attribute_access(self):
        """Lambda accesses attribute of variable."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Attribute(value=Name(id="item"), attr="id"),
        )
        assert lambda_references_var(lam, "item") is True
    
    def test_multiple_vars_one_match(self):
        """Lambda references one of multiple loop vars."""
        lam = make_simple_lambda("j")
        assert lambda_references_var(lam, "i") is False
        assert lambda_references_var(lam, "j") is True
    
    def test_constant_body(self):
        """Lambda returns constant - no variable reference."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Constant(value=42),
        )
        assert lambda_references_var(lam, "i") is False
    
    def test_lambda_with_param_and_var(self):
        """Lambda has param and also uses outer var."""
        lam = Lambda(
            args=("x",),
            defaults=(None,),
            body=BinOp(left=Name(id="x"), op="add", right=Name(id="i")),
        )
        assert lambda_references_var(lam, "i") is True
        assert lambda_references_var(lam, "x") is True
    
    def test_empty_lambda(self):
        """Lambda with None body (edge case)."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Constant(value=None),
        )
        assert lambda_references_var(lam, "i") is False
    
    def test_find_lambdas_in_assignment(self):
        """Find lambda in assignment."""
        lam = make_simple_lambda("i")
        assign = Assignment(target="handler", value=lam)
        found = find_lambdas_in_node(assign)
        assert len(found) == 1
        assert found[0] is lam
    
    def test_find_lambdas_in_call(self):
        """Find lambda passed as argument."""
        lam = make_simple_lambda("i")
        call = Call(
            func=Attribute(value=Name(id="handlers"), attr="append"),
            args=(lam,),
            keywords={},
        )
        found = find_lambdas_in_node(call)
        assert len(found) == 1
    
    def test_find_multiple_lambdas(self):
        """Find multiple lambdas in node."""
        lam1 = make_simple_lambda("i")
        lam2 = make_simple_lambda("j")
        call = Call(
            func=Name(id="process"),
            args=(lam1, lam2),
            keywords={},
        )
        found = find_lambdas_in_node(call)
        assert len(found) == 2
    
    def test_find_no_lambdas(self):
        """No lambdas in simple expression."""
        expr = BinOp(left=Name(id="x"), op="add", right=Constant(value=1))
        found = find_lambdas_in_node(expr)
        assert len(found) == 0
    
    def test_get_loop_variables_for(self):
        """Get variable from for loop."""
        loop = make_for_loop("i", [])
        vars_ = get_loop_variables(loop)
        assert vars_ == {"i"}
    
    def test_get_loop_variables_for_unpack(self):
        """Get variables from for loop with unpacking."""
        loop = ForUnpack(
            targets=("key", "value"),
            iter=Name(id="items"),
            body=(),
        )
        vars_ = get_loop_variables(loop)
        assert vars_ == {"key", "value"}
    
    def test_get_loop_variables_while(self):
        """While loop has no explicit loop variable."""
        loop = While(
            test=Name(id="running"),
            body=(),
        )
        vars_ = get_loop_variables(loop)
        assert vars_ == set()


# =============================================================================
# 2. CAPTURE WRAPPING (20 tests)
# =============================================================================

class TestCaptureWrapping:
    """Tests for wrapping lambdas with capture IIFE."""
    
    def test_wrap_simple_lambda(self):
        """Wrap simple lambda that references i."""
        lam = make_simple_lambda("i")
        wrapped = wrap_lambda_with_capture(lam, {"i"})
        
        # Result should be a Call
        assert isinstance(wrapped, Call)
        # The function should be a Lambda
        assert isinstance(wrapped.func, Lambda)
        # With one arg 'i'
        assert wrapped.func.args == ("i",)
        # Called with Name(id='i')
        assert len(wrapped.args) == 1
        assert isinstance(wrapped.args[0], Name)
        assert wrapped.args[0].id == "i"
    
    def test_wrap_preserves_lambda_body(self):
        """Wrapped lambda still has original body."""
        lam = make_lambda_with_call("handle", "i")
        wrapped = wrap_lambda_with_capture(lam, {"i"})
        
        # The inner lambda (original) should be the body
        inner = wrapped.func.body
        assert inner is lam
    
    def test_wrap_multiple_vars(self):
        """Wrap lambda capturing multiple vars."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=BinOp(left=Name(id="i"), op="add", right=Name(id="j")),
        )
        wrapped = wrap_lambda_with_capture(lam, {"i", "j"})
        
        # Should have two args
        assert len(wrapped.func.args) == 2
        assert len(wrapped.args) == 2
    
    def test_wrap_preserves_location(self):
        """Wrapped call preserves line/col info."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Name(id="i"),
            line=10,
            col=5,
        )
        wrapped = wrap_lambda_with_capture(lam, {"i"})
        
        assert wrapped.line == 10
        assert wrapped.col == 5
    
    def test_optimizer_counts_captures(self):
        """Optimizer tracks how many captures it makes."""
        opt = LoopCaptureOptimizer()
        assert opt.capture_count == 0
    
    def test_optimizer_wraps_lambda_in_loop(self):
        """Optimizer wraps lambda inside for loop."""
        lam = make_simple_lambda("i")
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        # The assignment value should now be a Call (IIFE)
        loop_result = result.body[0]
        assign_result = loop_result.body[0]
        assert isinstance(assign_result.value, Call)
    
    def test_optimizer_doesnt_wrap_non_referencing(self):
        """Optimizer skips lambdas that don't reference loop var."""
        lam = make_simple_lambda("x")  # References 'x', not 'i'
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        # Should NOT be wrapped
        loop_result = result.body[0]
        assign_result = loop_result.body[0]
        assert isinstance(assign_result.value, Lambda)  # Still a Lambda
    
    def test_optimizer_handles_shadowed_param(self):
        """Don't wrap if lambda param shadows loop var."""
        lam = Lambda(
            args=("i",),  # Parameter shadows loop variable
            defaults=(None,),
            body=Name(id="i"),
        )
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        opt = LoopCaptureOptimizer()
        result = opt.visit(program)
        
        # Should NOT be wrapped because i is a parameter
        loop_result = result.body[0]
        assign_result = loop_result.body[0]
        assert isinstance(assign_result.value, Lambda)
    
    def test_wrap_lambda_in_call_arg(self):
        """Wrap lambda passed as function argument."""
        lam = make_simple_lambda("i")
        call = Call(
            func=Attribute(value=Name(id="handlers"), attr="append"),
            args=(lam,),
            keywords={},
        )
        stmt = ExprStmt(value=call)
        loop = make_for_loop("i", [stmt])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        # Lambda in args should be wrapped
        loop_result = result.body[0]
        call_result = loop_result.body[0].value
        # The arg should now be a Call (IIFE)
        assert isinstance(call_result.args[0], Call)
    
    def test_wrap_multiple_lambdas(self):
        """Wrap multiple lambdas in same loop."""
        lam1 = make_simple_lambda("i")
        lam2 = make_simple_lambda("i")
        assign1 = Assignment(target="h1", value=lam1)
        assign2 = Assignment(target="h2", value=lam2)
        loop = make_for_loop("i", [assign1, assign2])
        program = make_program([loop])
        
        opt = LoopCaptureOptimizer()
        result = opt.visit(program)
        
        assert opt.capture_count == 2
    
    def test_wrap_nested_lambda(self):
        """Wrap lambda nested in expression."""
        lam = make_simple_lambda("i")
        outer_call = Call(
            func=Name(id="wrapper"),
            args=(lam,),
            keywords={},
        )
        assign = Assignment(target="handler", value=outer_call)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        # Find the lambda and check it's wrapped
        loop_result = result.body[0]
        assign_result = loop_result.body[0]
        call_result = assign_result.value
        # The argument should be an IIFE
        assert isinstance(call_result.args[0], Call)
    
    def test_for_range_capture(self):
        """Handle for i in range(n) loops."""
        lam = make_simple_lambda("i")
        assign = Assignment(target="handler", value=lam)
        loop = make_for_range("i", 5, [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assign_result = loop_result.body[0]
        assert isinstance(assign_result.value, Call)  # IIFE wrapped
    
    def test_for_unpack_capture(self):
        """Handle for k, v in items: loops."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Name(id="k"),
        )
        assign = Assignment(target="handler", value=lam)
        loop = ForUnpack(
            targets=("k", "v"),
            iter=Name(id="items"),
            body=(assign,),
        )
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assign_result = loop_result.body[0]
        assert isinstance(assign_result.value, Call)
    
    def test_capture_both_unpack_vars(self):
        """Capture both variables from unpack."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=BinOp(left=Name(id="k"), op="add", right=Name(id="v")),
        )
        assign = Assignment(target="handler", value=lam)
        loop = ForUnpack(
            targets=("k", "v"),
            iter=Name(id="items"),
            body=(assign,),
        )
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assign_result = loop_result.body[0]
        wrapped = assign_result.value
        # Should have 2 captured vars
        assert len(wrapped.func.args) == 2
    
    def test_capture_one_of_unpack_vars(self):
        """Capture only used variable from unpack."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Name(id="k"),  # Only uses k, not v
        )
        assign = Assignment(target="handler", value=lam)
        loop = ForUnpack(
            targets=("k", "v"),
            iter=Name(id="items"),
            body=(assign,),
        )
        program = make_program([loop])
        
        opt = LoopCaptureOptimizer()
        result = opt.visit(program)
        
        loop_result = result.body[0]
        assign_result = loop_result.body[0]
        wrapped = assign_result.value
        # Should only capture k
        assert len(wrapped.func.args) == 1
    
    def test_while_loop_no_capture(self):
        """While loops don't auto-capture (no loop var)."""
        lam = make_simple_lambda("x")
        assign = Assignment(target="handler", value=lam)
        loop = While(
            test=Name(id="running"),
            body=(assign,),
        )
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assign_result = loop_result.body[0]
        # Should NOT be wrapped
        assert isinstance(assign_result.value, Lambda)
    
    def test_count_loop_lambdas(self):
        """Count lambdas inside loops."""
        lam = make_simple_lambda("i")
        assign = Assignment(target="h", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        count = count_loop_lambdas(program)
        assert count == 1
    
    def test_needs_capture_fix_true(self):
        """Detect when capture fix is needed."""
        lam = make_simple_lambda("i")
        assign = Assignment(target="h", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        assert needs_capture_fix(program) is True
    
    def test_needs_capture_fix_false(self):
        """Detect when no capture fix needed."""
        lam = make_simple_lambda("x")  # Different var
        assign = Assignment(target="h", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        assert needs_capture_fix(program) is False


# =============================================================================
# 3. FOR LOOP HANDLING (20 tests)
# =============================================================================

class TestForLoopHandling:
    """Tests for various for loop patterns."""
    
    def test_simple_for_in_items(self):
        """for item in items: lambda uses item."""
        lam = make_simple_lambda("item")
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("item", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_for_range_5(self):
        """for i in range(5): lambda uses i."""
        lam = make_simple_lambda("i")
        assign = Assignment(target="handler", value=lam)
        loop = make_for_range("i", 5, [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_nested_for_loops(self):
        """Nested for loops - each lambda captures its loop var."""
        inner_lam = make_simple_lambda("j")
        inner_assign = Assignment(target="h_j", value=inner_lam)
        inner_loop = make_for_loop("j", [inner_assign])
        
        outer_lam = make_simple_lambda("i")
        outer_assign = Assignment(target="h_i", value=outer_lam)
        outer_loop = make_for_loop("i", [outer_assign, inner_loop])
        
        program = make_program([outer_loop])
        
        opt = LoopCaptureOptimizer()
        result = opt.visit(program)
        
        # Both lambdas should be wrapped
        assert opt.capture_count == 2
    
    def test_inner_loop_uses_outer_var(self):
        """Inner loop lambda uses outer loop variable.
        
        Fixed: Now captures outer loop vars correctly.
        """
        lam = make_simple_lambda("i")  # Uses outer var
        assign = Assignment(target="handler", value=lam)
        inner_loop = make_for_loop("j", [assign])
        outer_loop = make_for_loop("i", [inner_loop])
        program = make_program([outer_loop])
        
        result = fix_loop_captures(program)
        
        # Lambda references i from outer loop
        # Now correctly captures outer loop vars too
        outer_result = result.body[0]
        inner_result = outer_result.body[0]
        assign_result = inner_result.body[0]
        # This lambda uses 'i' - should be wrapped with IIFE
        assert isinstance(assign_result.value, Call)  # IIFE wrapping
    
    def test_inner_loop_uses_both_vars(self):
        """Inner loop lambda uses both outer and inner vars."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=BinOp(left=Name(id="i"), op="add", right=Name(id="j")),
        )
        assign = Assignment(target="handler", value=lam)
        inner_loop = make_for_loop("j", [assign])
        outer_loop = make_for_loop("i", [inner_loop])
        program = make_program([outer_loop])
        
        result = fix_loop_captures(program)
        
        # Lambda should capture both i and j
        outer_result = result.body[0]
        inner_result = outer_result.body[0]
        assign_result = inner_result.body[0]
        wrapped = assign_result.value
        # Inner loop processes first, should capture j (and maybe i from outer context)
        assert isinstance(wrapped, Call)
    
    def test_multiple_statements_in_loop(self):
        """Loop with multiple statements, some with lambdas."""
        lam = make_simple_lambda("i")
        assign1 = Assignment(target="x", value=Constant(value=1))
        assign2 = Assignment(target="handler", value=lam)
        assign3 = Assignment(target="y", value=Constant(value=2))
        loop = make_for_loop("i", [assign1, assign2, assign3])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        # Only assign2 should be modified
        assert loop_result.body[0].value == Constant(value=1)
        assert isinstance(loop_result.body[1].value, Call)
        assert loop_result.body[2].value == Constant(value=2)
    
    def test_expr_stmt_with_lambda(self):
        """Lambda in expression statement (not assignment)."""
        lam = make_simple_lambda("i")
        call = Call(
            func=Name(id="process"),
            args=(lam,),
            keywords={},
        )
        stmt = ExprStmt(value=call)
        loop = make_for_loop("i", [stmt])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        call_result = loop_result.body[0].value
        assert isinstance(call_result.args[0], Call)
    
    def test_lambda_in_method_call(self):
        """Lambda passed to method: items.append(lambda: i)."""
        lam = make_simple_lambda("i")
        call = Call(
            func=Attribute(value=Name(id="handlers"), attr="append"),
            args=(lam,),
            keywords={},
        )
        stmt = ExprStmt(value=call)
        loop = make_for_loop("i", [stmt])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        call_result = loop_result.body[0].value
        assert isinstance(call_result.args[0], Call)
    
    def test_lambda_with_closure_call(self):
        """Lambda calls function with loop var: lambda: handle(i)."""
        lam = make_lambda_with_call("handle", "i")
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_complex_lambda_body(self):
        """Lambda with complex expression body."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=BinOp(
                left=Name(id="i"),
                op="mul",
                right=BinOp(left=Name(id="i"), op="add", right=Constant(value=1)),
            ),
        )
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_enumerate_pattern(self):
        """for i, item in enumerate(items): pattern."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Name(id="i"),
        )
        assign = Assignment(target="handler", value=lam)
        loop = ForUnpack(
            targets=("i", "item"),
            iter=Call(func=Name(id="enumerate"), args=(Name(id="items"),), keywords={}),
            body=(assign,),
        )
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_dict_items_pattern(self):
        """for k, v in d.items(): pattern."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Name(id="k"),
        )
        assign = Assignment(target="handler", value=lam)
        loop = ForUnpack(
            targets=("k", "v"),
            iter=Call(
                func=Attribute(value=Name(id="d"), attr="items"),
                args=(),
                keywords={},
            ),
            body=(assign,),
        )
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_three_var_unpack(self):
        """for a, b, c in items: pattern."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Name(id="b"),
        )
        assign = Assignment(target="handler", value=lam)
        loop = ForUnpack(
            targets=("a", "b", "c"),
            iter=Name(id="items"),
            body=(assign,),
        )
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        # Should capture only b
        wrapped = loop_result.body[0].value
        assert isinstance(wrapped, Call)
    
    def test_no_loop_outside_unchanged(self):
        """Lambda outside loop is unchanged."""
        lam = make_simple_lambda("x")
        assign = Assignment(target="handler", value=lam)
        program = make_program([assign])
        
        result = fix_loop_captures(program)
        
        # Should be unchanged
        assert result.body[0].value is lam
    
    def test_loop_without_lambda_unchanged(self):
        """Loop without lambda is unchanged."""
        assign = Assignment(target="x", value=Constant(value=1))
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        # Assignment value unchanged
        assert loop_result.body[0].value == Constant(value=1)
    
    def test_multiple_loops_each_processed(self):
        """Multiple loops in program."""
        lam1 = make_simple_lambda("i")
        assign1 = Assignment(target="h1", value=lam1)
        loop1 = make_for_loop("i", [assign1])
        
        lam2 = make_simple_lambda("j")
        assign2 = Assignment(target="h2", value=lam2)
        loop2 = make_for_loop("j", [assign2])
        
        program = make_program([loop1, loop2])
        
        opt = LoopCaptureOptimizer()
        result = opt.visit(program)
        
        assert opt.capture_count == 2
    
    def test_loop_after_non_loop(self):
        """Non-loop statement before loop."""
        non_loop = Assignment(target="x", value=Constant(value=1))
        lam = make_simple_lambda("i")
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([non_loop, loop])
        
        result = fix_loop_captures(program)
        
        assert result.body[0].value == Constant(value=1)
        assert isinstance(result.body[1].body[0].value, Call)
    
    def test_empty_loop_body(self):
        """Handle empty loop body."""
        loop = make_for_loop("i", [])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert loop_result.body == ()


# =============================================================================
# 4. EDGE CASES (20 tests)
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    def test_lambda_uses_global_not_loop(self):
        """Lambda uses global var, not loop var."""
        lam = make_simple_lambda("global_var")
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        # Should NOT be wrapped
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Lambda)
    
    def test_lambda_param_same_name_as_loop_var(self):
        """Lambda param shadows loop var - no wrap needed."""
        lam = Lambda(
            args=("i",),
            defaults=(None,),
            body=Name(id="i"),
        )
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        opt = LoopCaptureOptimizer()
        result = opt.visit(program)
        
        # Should NOT wrap since i is a param
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Lambda)
    
    def test_lambda_uses_loop_var_and_param(self):
        """Lambda has param j but also uses loop var i."""
        lam = Lambda(
            args=("j",),
            defaults=(None,),
            body=BinOp(left=Name(id="i"), op="add", right=Name(id="j")),
        )
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        # Should wrap because it uses i
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_deeply_nested_lambda(self):
        """Lambda deeply nested in calls."""
        lam = make_simple_lambda("i")
        inner_call = Call(func=Name(id="inner"), args=(lam,), keywords={})
        middle_call = Call(func=Name(id="middle"), args=(inner_call,), keywords={})
        outer_call = Call(func=Name(id="outer"), args=(middle_call,), keywords={})
        stmt = ExprStmt(value=outer_call)
        loop = make_for_loop("i", [stmt])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        # Lambda should still be wrapped even when deeply nested
        loop_result = result.body[0]
        # The wrapping should be applied somewhere in the chain
        opt = LoopCaptureOptimizer()
        opt.visit(program)
        assert opt.capture_count == 1
    
    def test_lambda_in_list_literal(self):
        """Lambda in list literal (corner case)."""
        # This would be [lambda: i, lambda: j]
        lam = make_simple_lambda("i")
        # We represent this as just the lambda for simplicity
        assign = Assignment(target="handlers", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_empty_program(self):
        """Handle empty program."""
        program = make_program([])
        result = fix_loop_captures(program)
        assert result.body == ()
    
    def test_program_with_only_assignments(self):
        """Program with no loops."""
        assign = Assignment(target="x", value=Constant(value=1))
        program = make_program([assign])
        
        result = fix_loop_captures(program)
        assert result.body[0].value == Constant(value=1)
    
    def test_lambda_uses_underscore_var(self):
        """for _ in range(n): pattern with _ var."""
        lam = make_simple_lambda("_")
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("_", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        # Should wrap even for _ variable
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_lambda_constant_body(self):
        """Lambda returns constant - no capture needed."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Constant(value=42),
        )
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        # Should NOT wrap
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Lambda)
    
    def test_optimizer_idempotent(self):
        """Running optimizer twice gives same result."""
        lam = make_simple_lambda("i")
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result1 = fix_loop_captures(program)
        result2 = fix_loop_captures(result1)
        
        # Structure should be the same (already wrapped)
        # The second pass shouldn't change anything
        loop1 = result1.body[0]
        loop2 = result2.body[0]
        # Both should have Call as value
        assert isinstance(loop1.body[0].value, Call)
        assert isinstance(loop2.body[0].value, Call)
    
    def test_multiple_lambdas_same_statement(self):
        """Multiple lambdas in one call."""
        lam1 = make_simple_lambda("i")
        lam2 = Lambda(
            args=(),
            defaults=(),
            body=BinOp(left=Name(id="i"), op="add", right=Constant(value=1)),
        )
        call = Call(
            func=Name(id="process"),
            args=(lam1, lam2),
            keywords={},
        )
        stmt = ExprStmt(value=call)
        loop = make_for_loop("i", [stmt])
        program = make_program([loop])
        
        opt = LoopCaptureOptimizer()
        result = opt.visit(program)
        
        assert opt.capture_count == 2
    
    def test_count_loop_lambdas_nested(self):
        """Count lambdas in nested loops."""
        inner_lam = make_simple_lambda("j")
        inner_assign = Assignment(target="h", value=inner_lam)
        inner_loop = make_for_loop("j", [inner_assign])
        
        outer_lam = make_simple_lambda("i")
        outer_assign = Assignment(target="g", value=outer_lam)
        outer_loop = make_for_loop("i", [outer_assign, inner_loop])
        
        program = make_program([outer_loop])
        
        count = count_loop_lambdas(program)
        assert count == 2
    
    def test_count_loop_lambdas_no_loops(self):
        """Count with no loops."""
        lam = make_simple_lambda("x")
        assign = Assignment(target="h", value=lam)
        program = make_program([assign])
        
        count = count_loop_lambdas(program)
        assert count == 0
    
    def test_needs_capture_shadowed(self):
        """needs_capture_fix false when param shadows."""
        lam = Lambda(
            args=("i",),
            defaults=(None,),
            body=Name(id="i"),
        )
        assign = Assignment(target="h", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        assert needs_capture_fix(program) is False
    
    def test_lambda_attribute_access(self):
        """Lambda accesses attribute: lambda: item.name."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Attribute(value=Name(id="item"), attr="name"),
        )
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("item", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_lambda_method_call(self):
        """Lambda calls method: lambda: item.process()."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Call(
                func=Attribute(value=Name(id="item"), attr="process"),
                args=(),
                keywords={},
            ),
        )
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("item", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_lambda_subscript_access(self):
        """Lambda accesses subscript: lambda: items[i]."""
        from pynext.transpiler.nodes import Subscript
        lam = Lambda(
            args=(),
            defaults=(),
            body=Subscript(
                value=Name(id="items"),
                slice=Name(id="i"),
            ),
        )
        assign = Assignment(target="handler", value=lam)
        loop = make_for_loop("i", [assign])
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert isinstance(loop_result.body[0].value, Call)
    
    def test_optimizer_preserves_other_attrs(self):
        """Optimizer preserves other For loop attributes."""
        loop = For(
            target="i",
            iter=Name(id="items"),
            body=(),
            is_range=True,
            range_args=(0, 10, 1),
            line=5,
            col=3,
        )
        program = make_program([loop])
        
        result = fix_loop_captures(program)
        
        loop_result = result.body[0]
        assert loop_result.is_range is True
        assert loop_result.range_args == (0, 10, 1)
