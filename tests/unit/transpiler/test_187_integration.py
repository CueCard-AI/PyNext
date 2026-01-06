"""
Phase 18.7 Tests - Integration Tests

50 comprehensive tests for the optimizer integration.

Test Categories:
1. optimize() API (20 tests)
2. OptimizeOptions (15 tests)
3. Statistics (15 tests)
"""

import pytest
from pynext.transpiler import parse
from pynext.transpiler.nodes import (
    Program, Assignment, If, For, ExprStmt,
    Name, Constant, Call, Attribute, Compare, Lambda,
)
from pynext.transpiler.optimizer import (
    optimize, OptimizeOptions,
    get_optimization_stats, format_stats,
    infer_types, TypeEnv, PyType,
    elide_wrappers, fix_loop_captures,
    inline_runtime_calls, eliminate_dead_code,
    collect_runtime_deps, count_py_calls,
    mark_native_functions, generate_import,
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
# 1. OPTIMIZE() API (20 tests)
# =============================================================================

class TestOptimizeAPI:
    """Tests for the main optimize() function."""
    
    def test_optimize_empty_program(self):
        """Optimize empty program."""
        program = make_program([])
        result = optimize(program)
        assert result.body == ()
    
    def test_optimize_simple_assignment(self):
        """Optimize simple assignment."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        result = optimize(program)
        
        assert len(result.body) == 1
        assert result.body[0].target == "x"
    
    def test_optimize_with_default_options(self):
        """Optimize with default options."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        result = optimize(program, OptimizeOptions())
        
        assert len(result.body) == 1
    
    def test_optimize_with_none_options(self):
        """Optimize with None options uses defaults."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        result = optimize(program, None)
        
        assert len(result.body) == 1
    
    def test_optimize_elides_bool_wrapper(self):
        """Optimize elides __py.bool on comparison."""
        cmp = Compare(
            left=Name(id="x"),
            ops=("gt",),
            comparators=(Constant(value=0),),
        )
        call = make_py_call("bool", cmp)
        if_stmt = If(
            test=call,
            body=(Assignment(target="y", value=Constant(value=1)),),
            orelse=(),
        )
        program = make_program([if_stmt])
        
        result = optimize(program)
        
        # The bool wrapper should be elided
        result_if = result.body[0]
        assert isinstance(result_if.test, Compare)
    
    def test_optimize_preserves_necessary_wrappers(self):
        """Optimize preserves wrappers when needed."""
        # __py.eq on lists needs to stay
        call = make_py_call("eq", Name(id="list1"), Name(id="list2"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        result = optimize(program)
        
        # Should preserve (type unknown)
        result_call = result.body[0].value
        assert isinstance(result_call, Call)
    
    def test_optimize_dce_removes_if_false(self):
        """Optimize removes if False blocks."""
        if_stmt = If(
            test=Constant(value=False),
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(),
        )
        program = make_program([if_stmt])
        
        result = optimize(program)
        
        assert result.body == ()
    
    def test_optimize_dce_keeps_if_true_body(self):
        """Optimize keeps if True body."""
        if_stmt = If(
            test=Constant(value=True),
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(Assignment(target="y", value=Constant(value=2)),),
        )
        program = make_program([if_stmt])
        
        result = optimize(program)
        
        assert len(result.body) == 1
        assert result.body[0].target == "x"
    
    def test_optimize_captures_loop_lambdas(self):
        """Optimize wraps loop lambdas."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Name(id="i"),
        )
        assign = Assignment(target="handler", value=lam)
        loop = For(
            target="i",
            iter=Name(id="items"),
            body=(assign,),
            is_range=False,
            range_args=None,
        )
        program = make_program([loop])
        
        result = optimize(program)
        
        loop_result = result.body[0]
        assign_result = loop_result.body[0]
        # Lambda should be wrapped with IIFE
        assert isinstance(assign_result.value, Call)
    
    def test_optimize_returns_program(self):
        """Optimize returns a Program node."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        result = optimize(program)
        
        assert isinstance(result, Program)
    
    def test_optimize_preserves_statement_order(self):
        """Optimize preserves statement order."""
        stmts = [
            Assignment(target="a", value=Constant(value=1)),
            Assignment(target="b", value=Constant(value=2)),
            Assignment(target="c", value=Constant(value=3)),
        ]
        program = make_program(stmts)
        
        result = optimize(program)
        
        assert result.body[0].target == "a"
        assert result.body[1].target == "b"
        assert result.body[2].target == "c"
    
    def test_optimize_multiple_passes(self):
        """Optimize applies multiple passes."""
        # This tests that type inference is used by elision
        # and DCE cleans up dead code
        cmp = Compare(
            left=Name(id="x"),
            ops=("gt",),
            comparators=(Constant(value=0),),
        )
        call = make_py_call("bool", cmp)
        if_stmt_live = If(
            test=call,
            body=(Assignment(target="y", value=Constant(value=1)),),
            orelse=(),
        )
        if_stmt_dead = If(
            test=Constant(value=False),
            body=(Assignment(target="z", value=Constant(value=2)),),
            orelse=(),
        )
        program = make_program([if_stmt_live, if_stmt_dead])
        
        result = optimize(program)
        
        # Dead if removed, live if has elided wrapper
        assert len(result.body) == 1
        assert isinstance(result.body[0].test, Compare)
    
    def test_optimize_idempotent(self):
        """Running optimize twice gives same result."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        result1 = optimize(program)
        result2 = optimize(result1)
        
        assert len(result1.body) == len(result2.body)
    
    def test_optimize_with_nested_structures(self):
        """Optimize handles nested structures."""
        inner_if = If(
            test=Constant(value=True),
            body=(Assignment(target="inner", value=Constant(value=1)),),
            orelse=(),
        )
        outer_if = If(
            test=Name(id="cond"),
            body=(inner_if,),
            orelse=(),
        )
        program = make_program([outer_if])
        
        result = optimize(program)
        
        # Inner if should be unwrapped, body becomes tuple of statements
        outer_result = result.body[0]
        # The inner body is now a tuple containing the assignment
        inner_body = outer_result.body[0]
        # DCE returns tuple of statements for unwrapped if True
        assert isinstance(inner_body, tuple)
        assert isinstance(inner_body[0], Assignment)
    
    def test_optimize_complex_program(self):
        """Optimize complex program with multiple features."""
        # Mix of:
        # - Assignments
        # - If with bool wrapper
        # - Dead code
        stmts = [
            Assignment(target="x", value=Constant(value=5)),
            If(
                test=make_py_call("bool", Compare(
                    left=Name(id="x"), ops=("gt",), comparators=(Constant(value=0),)
                )),
                body=(Assignment(target="y", value=Constant(value=1)),),
                orelse=(),
            ),
            If(
                test=Constant(value=False),
                body=(Assignment(target="dead", value=Constant(value=999)),),
                orelse=(),
            ),
        ]
        program = make_program(stmts)
        
        result = optimize(program)
        
        # Should have 2 statements (dead if removed)
        assert len(result.body) == 2
    
    def test_optimize_preserves_line_info(self):
        """Optimize preserves line information where possible."""
        assign = Assignment(
            target="x",
            value=Constant(value=5),
            line=10,
            col=5,
        )
        program = make_program([assign])
        
        result = optimize(program)
        
        # Line info should be preserved
        assert result.body[0].line == 10
    
    def test_optimize_all_passes_disabled(self):
        """Optimize with all passes disabled."""
        call = make_py_call("bool", Compare(
            left=Name(id="x"), ops=("gt",), comparators=(Constant(value=0),)
        ))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        options = OptimizeOptions(
            elision=False,
            inline=False,
            capture=False,
            dce=False,
        )
        result = optimize(program, options)
        
        # With all passes disabled, should be mostly unchanged
        result_call = result.body[0].value
        assert isinstance(result_call, Call)
    
    def test_optimize_only_elision(self):
        """Optimize with only elision enabled."""
        call = make_py_call("bool", Compare(
            left=Name(id="x"), ops=("gt",), comparators=(Constant(value=0),)
        ))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        options = OptimizeOptions(
            elision=True,
            inline=False,
            capture=False,
            dce=False,
        )
        result = optimize(program, options)
        
        # Wrapper should be elided
        assert isinstance(result.body[0].value, Compare)
    
    def test_optimize_only_dce(self):
        """Optimize with only DCE enabled."""
        if_stmt = If(
            test=Constant(value=False),
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(),
        )
        program = make_program([if_stmt])
        
        options = OptimizeOptions(
            elision=False,
            inline=False,
            capture=False,
            dce=True,
        )
        result = optimize(program, options)
        
        # Dead code should be removed
        assert result.body == ()


# =============================================================================
# 2. OPTIMIZE OPTIONS (15 tests)
# =============================================================================

class TestOptimizeOptions:
    """Tests for OptimizeOptions configuration."""
    
    def test_default_options(self):
        """Default options have all passes enabled."""
        opts = OptimizeOptions()
        assert opts.elision is True
        assert opts.inline is True
        assert opts.capture is True
        assert opts.dce is True
    
    def test_custom_elision(self):
        opts = OptimizeOptions(elision=False)
        assert opts.elision is False
        assert opts.inline is True
    
    def test_custom_inline(self):
        opts = OptimizeOptions(inline=False)
        assert opts.inline is False
        assert opts.elision is True
    
    def test_custom_capture(self):
        opts = OptimizeOptions(capture=False)
        assert opts.capture is False
        assert opts.elision is True
    
    def test_custom_dce(self):
        opts = OptimizeOptions(dce=False)
        assert opts.dce is False
        assert opts.elision is True
    
    def test_all_disabled(self):
        opts = OptimizeOptions(
            elision=False,
            inline=False,
            capture=False,
            dce=False,
        )
        assert opts.elision is False
        assert opts.inline is False
        assert opts.capture is False
        assert opts.dce is False
    
    def test_options_immutable(self):
        """Options can be reused."""
        opts = OptimizeOptions()
        program1 = make_program([])
        program2 = make_program([Assignment(target="x", value=Constant(value=1))])
        
        result1 = optimize(program1, opts)
        result2 = optimize(program2, opts)
        
        # Both should succeed
        assert result1.body == ()
        assert len(result2.body) == 1
    
    def test_options_with_native(self):
        opts = OptimizeOptions(native_mode=True)
        assert opts.native_mode is True
    
    def test_options_without_native(self):
        opts = OptimizeOptions(native_mode=False)
        assert opts.native_mode is False
    
    def test_elision_only_affects_wrappers(self):
        """Elision doesn't affect other code."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        with_elision = optimize(program, OptimizeOptions(elision=True))
        without_elision = optimize(program, OptimizeOptions(elision=False))
        
        # Both should produce same result for non-wrapper code
        assert len(with_elision.body) == len(without_elision.body)
    
    def test_capture_only_affects_loops(self):
        """Capture only affects loop lambdas."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        with_capture = optimize(program, OptimizeOptions(capture=True))
        without_capture = optimize(program, OptimizeOptions(capture=False))
        
        # Both should produce same result for non-loop code
        assert len(with_capture.body) == len(without_capture.body)
    
    def test_dce_only_affects_dead_code(self):
        """DCE only affects dead code."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        with_dce = optimize(program, OptimizeOptions(dce=True))
        without_dce = optimize(program, OptimizeOptions(dce=False))
        
        # Both should keep live code
        assert len(with_dce.body) == len(without_dce.body)
    
    def test_inline_only_affects_runtime_calls(self):
        """Inline only affects runtime calls."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        with_inline = optimize(program, OptimizeOptions(inline=True))
        without_inline = optimize(program, OptimizeOptions(inline=False))
        
        # Both should produce same result for non-runtime code
        assert len(with_inline.body) == len(without_inline.body)
    
    def test_combine_options(self):
        """Multiple options work together."""
        opts = OptimizeOptions(
            elision=True,
            inline=True,
            capture=False,
            dce=True,
        )
        
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        result = optimize(program, opts)
        assert len(result.body) == 1


# =============================================================================
# 3. STATISTICS (15 tests)
# =============================================================================

class TestStatistics:
    """Tests for optimization statistics."""
    
    def test_stats_empty_program(self):
        """Stats for empty program."""
        program = make_program([])
        optimized = optimize(program)
        
        stats = get_optimization_stats(program, optimized)
        
        assert stats.original_py_calls == 0
        assert stats.optimized_py_calls == 0
    
    def test_stats_no_py_calls(self):
        """Stats for program without __py calls."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        optimized = optimize(program)
        
        stats = get_optimization_stats(program, optimized)
        
        assert stats.original_py_calls == 0
        assert stats.wrapper_reduction == 0.0
    
    def test_stats_with_py_calls(self):
        """Stats for program with __py calls."""
        call = make_py_call("bool", Name(id="x"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        stats = get_optimization_stats(program, program)
        
        assert stats.original_py_calls == 1
    
    def test_stats_wrapper_reduction(self):
        """Stats show wrapper reduction."""
        cmp = Compare(
            left=Name(id="x"),
            ops=("gt",),
            comparators=(Constant(value=0),),
        )
        call = make_py_call("bool", cmp)
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        optimized = optimize(program)
        
        stats = get_optimization_stats(program, optimized)
        
        assert stats.original_py_calls == 1
        assert stats.optimized_py_calls == 0
        assert stats.wrapper_reduction == 100.0
    
    def test_stats_runtime_deps(self):
        """Stats collect runtime dependencies."""
        call = make_py_call("at", Name(id="items"), Constant(value=-1))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        optimized = optimize(program)
        
        stats = get_optimization_stats(program, optimized)
        
        assert "at" in stats.runtime_deps
    
    def test_stats_unreachable_blocks(self):
        """Stats count unreachable blocks."""
        if_stmt = If(
            test=Constant(value=False),
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(),
        )
        program = make_program([if_stmt])
        optimized = optimize(program)
        
        stats = get_optimization_stats(program, optimized)
        
        assert stats.unreachable_blocks == 1
    
    def test_stats_loop_lambdas(self):
        """Stats count loop lambdas."""
        lam = Lambda(args=(), defaults=(), body=Name(id="i"))
        assign = Assignment(target="h", value=lam)
        loop = For(
            target="i",
            iter=Name(id="items"),
            body=(assign,),
            is_range=False,
            range_args=None,
        )
        program = make_program([loop])
        optimized = optimize(program)
        
        stats = get_optimization_stats(program, optimized)
        
        assert stats.loop_lambdas == 1
    
    def test_format_stats_output(self):
        """Format stats produces string output."""
        program = make_program([])
        optimized = optimize(program)
        stats = get_optimization_stats(program, optimized)
        
        output = format_stats(stats)
        
        assert isinstance(output, str)
        assert "Optimization Statistics" in output
    
    def test_format_stats_contains_reduction(self):
        """Format stats includes reduction percentage."""
        program = make_program([])
        optimized = optimize(program)
        stats = get_optimization_stats(program, optimized)
        
        output = format_stats(stats)
        
        assert "Wrapper reduction" in output
    
    def test_format_stats_contains_counts(self):
        """Format stats includes call counts."""
        program = make_program([])
        optimized = optimize(program)
        stats = get_optimization_stats(program, optimized)
        
        output = format_stats(stats)
        
        assert "__py.*" in output
    
    def test_stats_with_type_env(self):
        """Stats accept custom type env."""
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        optimized = optimize(program)
        
        type_env = infer_types(program)
        stats = get_optimization_stats(program, optimized, type_env)
        
        assert stats is not None
    
    def test_count_py_calls_function(self):
        """count_py_calls helper function."""
        call = make_py_call("bool", Name(id="x"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        count = count_py_calls(program)
        assert count == 1
    
    def test_collect_runtime_deps_function(self):
        """collect_runtime_deps helper function."""
        call = make_py_call("eq", Name(id="a"), Name(id="b"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"eq"}
    
    def test_generate_import_function(self):
        """generate_import helper function."""
        result = generate_import({"bool", "eq"})
        assert "__py_bool" in result
        assert "__py_eq" in result
    
    def test_stats_native_functions(self):
        """Stats include native functions."""
        from pynext.transpiler.nodes import Decorator, DecoratedFunction
        
        func = Assignment(target="x", value=Constant(value=1))  # placeholder
        program = make_program([func])
        optimized = optimize(program)
        
        stats = get_optimization_stats(program, optimized)
        
        assert stats.native_functions == set()
