"""
Phase 18.7 - Nested Loop Capture Tests

Tests for capturing outer loop variables in nested loops.
"""

import pytest
from pynext.transpiler import parse
from pynext.transpiler.nodes import (
    Program, Assignment, For, ForUnpack, ExprStmt,
    Name, Constant, Call, Attribute, Lambda,
)
from pynext.transpiler.optimizer import optimize, fix_loop_captures
from pynext.transpiler.optimizer.capture import (
    LoopCaptureOptimizer, get_loop_variables,
)


# =============================================================================
# HELPERS
# =============================================================================

def make_for_loop(var: str, body: list, range_val: int = 5) -> For:
    """Create a for loop."""
    return For(
        target=var,
        iter=Call(
            func=Name(id="range"),
            args=(Constant(value=range_val),),
            keywords={},
        ),
        body=tuple(body),
        is_range=True,
        range_args=(Constant(value=range_val),),
    )


def has_iife_capturing(node, *vars) -> bool:
    """Check if node contains an IIFE that captures the given variables."""
    if isinstance(node, Call):
        if isinstance(node.func, Lambda):
            # Check if the lambda captures the expected variables
            if set(node.func.args) == set(vars):
                return True
    
    for attr in ['body', 'orelse', 'args', 'left', 'right', 'value',
                 'test', 'iter', 'target', 'func', 'elts']:
        child = getattr(node, attr, None)
        if child is not None:
            if isinstance(child, (list, tuple)):
                for c in child:
                    if hasattr(c, '__dict__') and has_iife_capturing(c, *vars):
                        return True
            elif hasattr(child, '__dict__') and has_iife_capturing(child, *vars):
                return True
    return False


# =============================================================================
# 1. NESTED LOOP CAPTURE - INNER VAR ONLY
# =============================================================================

class TestNestedLoopInnerVar:
    """Test capturing inner loop variable only."""
    
    def test_inner_loop_var_captured(self):
        """Lambda in inner loop captures inner var."""
        # for i in range(5):
        #     for j in range(5):
        #         f = lambda: j
        lam = Lambda(args=(), defaults=(), body=Name(id="j"))
        assign = Assignment(target="f", value=lam)
        inner_loop = make_for_loop("j", [assign])
        outer_loop = make_for_loop("i", [inner_loop])
        program = Program(body=(outer_loop,))
        
        optimized = fix_loop_captures(program)
        
        # j should be captured
        inner_loop_result = optimized.body[0].body[0]
        assign_result = inner_loop_result.body[0]
        assert has_iife_capturing(assign_result, "j")
    
    def test_inner_loop_expression(self):
        """Lambda with expression using inner var."""
        # for i in range(5):
        #     for j in range(5):
        #         f = lambda: j * 2
        lam = Lambda(
            args=(),
            defaults=(),
            body=Call(
                func=Attribute(value=Name(id="__py"), attr="mul"),
                args=(Name(id="j"), Constant(value=2)),
                keywords={},
            )
        )
        assign = Assignment(target="f", value=lam)
        inner_loop = make_for_loop("j", [assign])
        outer_loop = make_for_loop("i", [inner_loop])
        program = Program(body=(outer_loop,))
        
        optimized = fix_loop_captures(program)
        
        inner_loop_result = optimized.body[0].body[0]
        assign_result = inner_loop_result.body[0]
        assert has_iife_capturing(assign_result, "j")


# =============================================================================
# 2. NESTED LOOP CAPTURE - OUTER VAR ONLY
# =============================================================================

class TestNestedLoopOuterVar:
    """Test capturing outer loop variable only."""
    
    def test_outer_loop_var_captured(self):
        """Lambda in inner loop captures outer var."""
        # for i in range(5):
        #     for j in range(5):
        #         f = lambda: i
        lam = Lambda(args=(), defaults=(), body=Name(id="i"))
        assign = Assignment(target="f", value=lam)
        inner_loop = make_for_loop("j", [assign])
        outer_loop = make_for_loop("i", [inner_loop])
        program = Program(body=(outer_loop,))
        
        optimized = fix_loop_captures(program)
        
        # i should be captured (outer loop var used in inner loop lambda)
        inner_loop_result = optimized.body[0].body[0]
        assign_result = inner_loop_result.body[0]
        assert has_iife_capturing(assign_result, "i")
    
    def test_outer_var_in_expression(self):
        """Lambda with expression using outer var."""
        # for i in range(5):
        #     for j in range(5):
        #         f = lambda: i + 1
        lam = Lambda(
            args=(),
            defaults=(),
            body=Call(
                func=Attribute(value=Name(id="__py"), attr="add"),
                args=(Name(id="i"), Constant(value=1)),
                keywords={},
            )
        )
        assign = Assignment(target="f", value=lam)
        inner_loop = make_for_loop("j", [assign])
        outer_loop = make_for_loop("i", [inner_loop])
        program = Program(body=(outer_loop,))
        
        optimized = fix_loop_captures(program)
        
        inner_loop_result = optimized.body[0].body[0]
        assign_result = inner_loop_result.body[0]
        assert has_iife_capturing(assign_result, "i")


# =============================================================================
# 3. NESTED LOOP CAPTURE - BOTH VARS
# =============================================================================

class TestNestedLoopBothVars:
    """Test capturing both inner and outer loop variables."""
    
    def test_both_vars_captured(self):
        """Lambda in inner loop captures both i and j."""
        # for i in range(5):
        #     for j in range(5):
        #         f = lambda: (i, j)
        lam = Lambda(
            args=(),
            defaults=(),
            body=Call(
                func=Name(id="tuple"),
                args=(Name(id="i"), Name(id="j")),
                keywords={},
            )
        )
        assign = Assignment(target="f", value=lam)
        inner_loop = make_for_loop("j", [assign])
        outer_loop = make_for_loop("i", [inner_loop])
        program = Program(body=(outer_loop,))
        
        optimized = fix_loop_captures(program)
        
        # Both i and j should be captured
        inner_loop_result = optimized.body[0].body[0]
        assign_result = inner_loop_result.body[0]
        # Check that IIFE captures both
        assert has_iife_capturing(assign_result, "i", "j")
    
    def test_both_vars_in_function_call(self):
        """Lambda calling function with both vars."""
        # for i in range(5):
        #     for j in range(5):
        #         f = lambda: handle(i, j)
        lam = Lambda(
            args=(),
            defaults=(),
            body=Call(
                func=Name(id="handle"),
                args=(Name(id="i"), Name(id="j")),
                keywords={},
            )
        )
        assign = Assignment(target="f", value=lam)
        inner_loop = make_for_loop("j", [assign])
        outer_loop = make_for_loop("i", [inner_loop])
        program = Program(body=(outer_loop,))
        
        optimized = fix_loop_captures(program)
        
        inner_loop_result = optimized.body[0].body[0]
        assign_result = inner_loop_result.body[0]
        assert has_iife_capturing(assign_result, "i", "j")


# =============================================================================
# 4. TRIPLE NESTED LOOPS
# =============================================================================

class TestTripleNestedLoops:
    """Test triple-nested loops."""
    
    def test_triple_nested_innermost_var(self):
        """Lambda in innermost loop captures innermost var."""
        # for i in range(3):
        #     for j in range(3):
        #         for k in range(3):
        #             f = lambda: k
        lam = Lambda(args=(), defaults=(), body=Name(id="k"))
        assign = Assignment(target="f", value=lam)
        inner_loop = make_for_loop("k", [assign], 3)
        mid_loop = make_for_loop("j", [inner_loop], 3)
        outer_loop = make_for_loop("i", [mid_loop], 3)
        program = Program(body=(outer_loop,))
        
        optimized = fix_loop_captures(program)
        
        inner_loop_result = optimized.body[0].body[0].body[0]
        assign_result = inner_loop_result.body[0]
        assert has_iife_capturing(assign_result, "k")
    
    def test_triple_nested_all_vars(self):
        """Lambda captures all three loop vars."""
        # for i in range(3):
        #     for j in range(3):
        #         for k in range(3):
        #             f = lambda: (i, j, k)
        lam = Lambda(
            args=(),
            defaults=(),
            body=Call(
                func=Name(id="triple"),
                args=(Name(id="i"), Name(id="j"), Name(id="k")),
                keywords={},
            )
        )
        assign = Assignment(target="f", value=lam)
        inner_loop = make_for_loop("k", [assign], 3)
        mid_loop = make_for_loop("j", [inner_loop], 3)
        outer_loop = make_for_loop("i", [mid_loop], 3)
        program = Program(body=(outer_loop,))
        
        optimized = fix_loop_captures(program)
        
        inner_loop_result = optimized.body[0].body[0].body[0]
        assign_result = inner_loop_result.body[0]
        assert has_iife_capturing(assign_result, "i", "j", "k")


# =============================================================================
# 5. EDGE CASES
# =============================================================================

class TestNestedLoopEdgeCases:
    """Edge cases for nested loop capture."""
    
    def test_lambda_no_loop_vars(self):
        """Lambda not referencing any loop vars - no capture needed."""
        # for i in range(5):
        #     for j in range(5):
        #         f = lambda: 42
        lam = Lambda(args=(), defaults=(), body=Constant(value=42))
        assign = Assignment(target="f", value=lam)
        inner_loop = make_for_loop("j", [assign])
        outer_loop = make_for_loop("i", [inner_loop])
        program = Program(body=(outer_loop,))
        
        optimized = fix_loop_captures(program)
        
        # No capture needed - lambda should NOT be wrapped
        inner_loop_result = optimized.body[0].body[0]
        assign_result = inner_loop_result.body[0]
        # Should be plain Lambda, not IIFE
        assert isinstance(assign_result.value, Lambda)
    
    def test_lambda_references_non_loop_var(self):
        """Lambda referencing non-loop variable - no capture."""
        # x = 5
        # for i in range(5):
        #     f = lambda: x
        assign_x = Assignment(target="x", value=Constant(value=5))
        lam = Lambda(args=(), defaults=(), body=Name(id="x"))
        assign_f = Assignment(target="f", value=lam)
        loop = make_for_loop("i", [assign_f])
        program = Program(body=(assign_x, loop))
        
        optimized = fix_loop_captures(program)
        
        # x is not a loop var - no capture needed
        loop_result = optimized.body[1]
        assign_result = loop_result.body[0]
        assert isinstance(assign_result.value, Lambda)
    
    def test_shadowed_variable(self):
        """Lambda parameter shadows loop var - no capture for that."""
        # for i in range(5):
        #     f = lambda i: i * 2  # i is parameter, not captured
        lam = Lambda(
            args=("i",),
            defaults=(None,),
            body=Call(
                func=Attribute(value=Name(id="__py"), attr="mul"),
                args=(Name(id="i"), Constant(value=2)),
                keywords={},
            )
        )
        assign = Assignment(target="f", value=lam)
        loop = make_for_loop("i", [assign])
        program = Program(body=(loop,))
        
        optimized = fix_loop_captures(program)
        
        # i is shadowed by lambda parameter - no capture
        loop_result = optimized.body[0]
        assign_result = loop_result.body[0]
        # Should be plain Lambda, not IIFE
        assert isinstance(assign_result.value, Lambda)
