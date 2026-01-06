"""
Phase 18.7 Tests - Dead Code Elimination

70 comprehensive tests for the DCE optimization.

Test Categories:
1. Runtime dependency collection (25 tests)
2. Dead code elimination (25 tests)
3. Import generation (10 tests)
4. Statistics and utilities (10 tests)
"""

import pytest
from pynext.transpiler.nodes import (
    Program, Assignment, If, ExprStmt,
    Name, Constant, Call, Attribute, BinOp, Compare,
)
from pynext.transpiler.optimizer.dce import (
    collect_runtime_deps, eliminate_dead_code,
    generate_import, count_unreachable_blocks,
    is_always_true, is_always_false,
    RuntimeDepCollector, DCEOptimizer,
    get_dep_stats,
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


def make_if(test, body, orelse=None) -> If:
    """Create an If node."""
    return If(
        test=test,
        body=tuple(body),
        orelse=tuple(orelse) if orelse else (),
    )


# =============================================================================
# 1. RUNTIME DEPENDENCY COLLECTION (25 tests)
# =============================================================================

class TestRuntimeDeps:
    """Tests for runtime dependency collection."""
    
    def test_collect_single_dep(self):
        call = make_py_call("bool", Name(id="x"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"bool"}
    
    def test_collect_multiple_deps(self):
        call1 = make_py_call("bool", Name(id="x"))
        call2 = make_py_call("eq", Name(id="a"), Name(id="b"))
        stmt1 = ExprStmt(value=call1)
        stmt2 = ExprStmt(value=call2)
        program = make_program([stmt1, stmt2])
        
        deps = collect_runtime_deps(program)
        assert deps == {"bool", "eq"}
    
    def test_collect_duplicate_deps(self):
        call1 = make_py_call("bool", Name(id="x"))
        call2 = make_py_call("bool", Name(id="y"))
        stmt1 = ExprStmt(value=call1)
        stmt2 = ExprStmt(value=call2)
        program = make_program([stmt1, stmt2])
        
        deps = collect_runtime_deps(program)
        assert deps == {"bool"}
    
    def test_collect_no_deps(self):
        assign = Assignment(target="x", value=Constant(value=5))
        program = make_program([assign])
        
        deps = collect_runtime_deps(program)
        assert deps == set()
    
    def test_collect_at_dep(self):
        call = make_py_call("at", Name(id="items"), Constant(value=-1))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"at"}
    
    def test_collect_slice_dep(self):
        call = make_py_call("slice", Name(id="items"), Constant(value=0), Constant(value=5))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"slice"}
    
    def test_collect_add_dep(self):
        call = make_py_call("add", Name(id="a"), Name(id="b"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"add"}
    
    def test_collect_mul_dep(self):
        call = make_py_call("mul", Name(id="a"), Name(id="b"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"mul"}
    
    def test_collect_mod_dep(self):
        call = make_py_call("mod", Name(id="a"), Name(id="b"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"mod"}
    
    def test_collect_in_dep(self):
        call = make_py_call("in", Name(id="x"), Name(id="items"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"in"}
    
    def test_collect_contains_dep(self):
        call = make_py_call("contains", Name(id="x"), Name(id="items"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"contains"}
    
    def test_collect_nested_in_binop(self):
        call = make_py_call("add", Name(id="a"), Name(id="b"))
        binop = BinOp(left=call, op="mul", right=Constant(value=2))
        stmt = ExprStmt(value=binop)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"add"}
    
    def test_collect_in_assignment(self):
        call = make_py_call("at", Name(id="items"), Constant(value=0))
        assign = Assignment(target="x", value=call)
        program = make_program([assign])
        
        deps = collect_runtime_deps(program)
        assert deps == {"at"}
    
    def test_collect_in_if_test(self):
        call = make_py_call("bool", Name(id="x"))
        if_stmt = make_if(call, [Assignment(target="y", value=Constant(value=1))])
        program = make_program([if_stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"bool"}
    
    def test_collect_in_if_body(self):
        call = make_py_call("add", Name(id="a"), Name(id="b"))
        if_stmt = make_if(
            Constant(value=True),
            [ExprStmt(value=call)]
        )
        program = make_program([if_stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"add"}
    
    def test_collect_in_if_orelse(self):
        call = make_py_call("sub", Name(id="a"), Name(id="b"))
        if_stmt = make_if(
            Constant(value=True),
            [Assignment(target="x", value=Constant(value=1))],
            [ExprStmt(value=call)]
        )
        program = make_program([if_stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"sub"}
    
    def test_collector_class(self):
        collector = RuntimeDepCollector()
        assert collector.deps == set()
    
    def test_collector_visit_call(self):
        collector = RuntimeDepCollector()
        call = make_py_call("bool", Name(id="x"))
        collector.visit_Call(call)
        
        assert "bool" in collector.deps
    
    def test_collector_skips_non_py_calls(self):
        collector = RuntimeDepCollector()
        call = Call(
            func=Name(id="print"),
            args=(Constant(value="hello"),),
            keywords={},
        )
        collector.visit_Call(call)
        
        assert collector.deps == set()
    
    def test_collect_all_arithmetic(self):
        calls = [
            make_py_call("add", Name(id="a"), Name(id="b")),
            make_py_call("sub", Name(id="a"), Name(id="b")),
            make_py_call("mul", Name(id="a"), Name(id="b")),
            make_py_call("div", Name(id="a"), Name(id="b")),
            make_py_call("mod", Name(id="a"), Name(id="b")),
            make_py_call("floordiv", Name(id="a"), Name(id="b")),
        ]
        stmts = [ExprStmt(value=c) for c in calls]
        program = make_program(stmts)
        
        deps = collect_runtime_deps(program)
        assert deps == {"add", "sub", "mul", "div", "mod", "floordiv"}
    
    def test_collect_format_dep(self):
        call = make_py_call("format", Name(id="x"), Constant(value=".2f"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"format"}
    
    def test_collect_repr_dep(self):
        call = make_py_call("repr", Name(id="x"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"repr"}
    
    def test_empty_program(self):
        program = make_program([])
        deps = collect_runtime_deps(program)
        assert deps == set()
    
    def test_complex_nested_structure(self):
        # __py.add(__py.mul(a, b), __py.sub(c, d))
        inner1 = make_py_call("mul", Name(id="a"), Name(id="b"))
        inner2 = make_py_call("sub", Name(id="c"), Name(id="d"))
        outer = make_py_call("add", inner1, inner2)
        stmt = ExprStmt(value=outer)
        program = make_program([stmt])
        
        deps = collect_runtime_deps(program)
        assert deps == {"add", "mul", "sub"}


# =============================================================================
# 2. DEAD CODE ELIMINATION (25 tests)
# =============================================================================

class TestDeadCodeElimination:
    """Tests for dead code elimination."""
    
    def test_is_always_true_true(self):
        assert is_always_true(Constant(value=True)) is True
    
    def test_is_always_true_nonzero(self):
        assert is_always_true(Constant(value=1)) is True
    
    def test_is_always_true_false(self):
        assert is_always_true(Constant(value=False)) is False
    
    def test_is_always_true_zero(self):
        assert is_always_true(Constant(value=0)) is False
    
    def test_is_always_true_name(self):
        assert is_always_true(Name(id="x")) is False
    
    def test_is_always_false_false(self):
        assert is_always_false(Constant(value=False)) is True
    
    def test_is_always_false_zero(self):
        assert is_always_false(Constant(value=0)) is True
    
    def test_is_always_false_none(self):
        assert is_always_false(Constant(value=None)) is True
    
    def test_is_always_false_true(self):
        assert is_always_false(Constant(value=True)) is False
    
    def test_is_always_false_nonzero(self):
        assert is_always_false(Constant(value=1)) is False
    
    def test_is_always_false_name(self):
        assert is_always_false(Name(id="x")) is False
    
    def test_eliminate_if_false(self):
        """if False: x = 1 → eliminated."""
        if_stmt = make_if(
            Constant(value=False),
            [Assignment(target="x", value=Constant(value=1))]
        )
        program = make_program([if_stmt])
        
        result = eliminate_dead_code(program)
        
        # Body should be empty
        assert result.body == ()
    
    def test_eliminate_if_zero(self):
        """if 0: x = 1 → eliminated."""
        if_stmt = make_if(
            Constant(value=0),
            [Assignment(target="x", value=Constant(value=1))]
        )
        program = make_program([if_stmt])
        
        result = eliminate_dead_code(program)
        assert result.body == ()
    
    def test_eliminate_if_none(self):
        """if None: x = 1 → eliminated."""
        if_stmt = make_if(
            Constant(value=None),
            [Assignment(target="x", value=Constant(value=1))]
        )
        program = make_program([if_stmt])
        
        result = eliminate_dead_code(program)
        assert result.body == ()
    
    def test_keep_if_false_else(self):
        """if False: x = 1 else: y = 2 → y = 2."""
        if_stmt = make_if(
            Constant(value=False),
            [Assignment(target="x", value=Constant(value=1))],
            [Assignment(target="y", value=Constant(value=2))]
        )
        program = make_program([if_stmt])
        
        result = eliminate_dead_code(program)
        
        # Should have just the else body
        assert len(result.body) == 1
        assert result.body[0].target == "y"
    
    def test_eliminate_if_true_else(self):
        """if True: x = 1 else: y = 2 → x = 1."""
        if_stmt = make_if(
            Constant(value=True),
            [Assignment(target="x", value=Constant(value=1))],
            [Assignment(target="y", value=Constant(value=2))]
        )
        program = make_program([if_stmt])
        
        result = eliminate_dead_code(program)
        
        # Should have just the if body
        assert len(result.body) == 1
        assert result.body[0].target == "x"
    
    def test_keep_if_true_no_else(self):
        """if True: x = 1 → x = 1."""
        if_stmt = make_if(
            Constant(value=True),
            [Assignment(target="x", value=Constant(value=1))]
        )
        program = make_program([if_stmt])
        
        result = eliminate_dead_code(program)
        
        # Should have just x = 1
        assert len(result.body) == 1
        assert result.body[0].target == "x"
    
    def test_preserve_dynamic_if(self):
        """if x: y = 1 → unchanged."""
        if_stmt = make_if(
            Name(id="x"),
            [Assignment(target="y", value=Constant(value=1))]
        )
        program = make_program([if_stmt])
        
        result = eliminate_dead_code(program)
        
        # Should be unchanged
        assert len(result.body) == 1
        assert isinstance(result.body[0], If)
    
    def test_preserve_comparison_if(self):
        """if x > 0: y = 1 → unchanged."""
        if_stmt = make_if(
            Compare(left=Name(id="x"), ops=(">",), comparators=(Constant(value=0),)),
            [Assignment(target="y", value=Constant(value=1))]
        )
        program = make_program([if_stmt])
        
        result = eliminate_dead_code(program)
        
        # Should be unchanged
        assert len(result.body) == 1
        assert isinstance(result.body[0], If)
    
    def test_multiple_statements_if_true(self):
        """if True: x = 1; y = 2 → x = 1; y = 2."""
        if_stmt = make_if(
            Constant(value=True),
            [
                Assignment(target="x", value=Constant(value=1)),
                Assignment(target="y", value=Constant(value=2)),
            ]
        )
        program = make_program([if_stmt])
        
        result = eliminate_dead_code(program)
        
        # Should have both statements
        assert len(result.body) == 2
    
    def test_optimizer_counts_eliminations(self):
        opt = DCEOptimizer()
        if_stmt = make_if(
            Constant(value=False),
            [Assignment(target="x", value=Constant(value=1))]
        )
        program = make_program([if_stmt])
        
        opt.visit(program)
        
        assert opt.eliminated_count == 1
    
    def test_count_unreachable_blocks(self):
        if_stmt = make_if(
            Constant(value=False),
            [Assignment(target="x", value=Constant(value=1))]
        )
        program = make_program([if_stmt])
        
        count = count_unreachable_blocks(program)
        assert count == 1
    
    def test_count_unreachable_with_else(self):
        if_stmt = make_if(
            Constant(value=True),
            [Assignment(target="x", value=Constant(value=1))],
            [Assignment(target="y", value=Constant(value=2))]
        )
        program = make_program([if_stmt])
        
        count = count_unreachable_blocks(program)
        assert count == 1
    
    def test_count_unreachable_none(self):
        if_stmt = make_if(
            Name(id="x"),
            [Assignment(target="y", value=Constant(value=1))]
        )
        program = make_program([if_stmt])
        
        count = count_unreachable_blocks(program)
        assert count == 0
    
    def test_empty_program_dce(self):
        program = make_program([])
        result = eliminate_dead_code(program)
        assert result.body == ()


# =============================================================================
# 3. IMPORT GENERATION (10 tests)
# =============================================================================

class TestImportGeneration:
    """Tests for import statement generation."""
    
    def test_generate_single_import(self):
        result = generate_import({"bool"})
        assert result == "import { __py_bool } from 'pynext/runtime';"
    
    def test_generate_multiple_imports(self):
        result = generate_import({"bool", "eq"})
        # Should be sorted
        assert "__py_bool" in result
        assert "__py_eq" in result
    
    def test_generate_sorted_imports(self):
        result = generate_import({"mul", "add", "bool"})
        # Check order: add, bool, mul
        add_pos = result.find("__py_add")
        bool_pos = result.find("__py_bool")
        mul_pos = result.find("__py_mul")
        assert add_pos < bool_pos < mul_pos
    
    def test_generate_empty_imports(self):
        result = generate_import(set())
        assert result == ""
    
    def test_generate_arithmetic_imports(self):
        result = generate_import({"add", "sub", "mul", "div"})
        assert "__py_add" in result
        assert "__py_sub" in result
        assert "__py_mul" in result
        assert "__py_div" in result
    
    def test_generate_from_clause(self):
        result = generate_import({"bool"})
        assert "from 'pynext/runtime'" in result
    
    def test_generate_import_syntax(self):
        result = generate_import({"at"})
        assert result.startswith("import {")
        assert result.endswith(";")  # Ends with semicolon
    
    def test_generate_many_imports(self):
        deps = {"add", "sub", "mul", "div", "mod", "floordiv", "bool", "eq", "at", "slice"}
        result = generate_import(deps)
        
        for dep in deps:
            assert f"__py_{dep}" in result
    
    def test_generate_special_chars(self):
        """Ensure no special chars cause issues."""
        result = generate_import({"in"})
        assert "__py_in" in result
    
    def test_generate_contains(self):
        result = generate_import({"contains"})
        assert "__py_contains" in result


# =============================================================================
# 4. STATISTICS AND UTILITIES (10 tests)
# =============================================================================

class TestDCEUtilities:
    """Tests for DCE statistics and utilities."""
    
    def test_get_dep_stats_empty(self):
        program = make_program([])
        stats = get_dep_stats(program)
        
        assert stats["total_deps"] == 0
        assert stats["deps"] == []
    
    def test_get_dep_stats_single(self):
        call = make_py_call("bool", Name(id="x"))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        stats = get_dep_stats(program)
        
        assert stats["total_deps"] == 1
        assert stats["has_bool"] is True
        assert stats["has_eq"] is False
    
    def test_get_dep_stats_multiple(self):
        call1 = make_py_call("bool", Name(id="x"))
        call2 = make_py_call("eq", Name(id="a"), Name(id="b"))
        call3 = make_py_call("at", Name(id="items"), Constant(value=0))
        stmts = [ExprStmt(value=c) for c in [call1, call2, call3]]
        program = make_program(stmts)
        
        stats = get_dep_stats(program)
        
        assert stats["total_deps"] == 3
        assert stats["has_bool"] is True
        assert stats["has_eq"] is True
        assert stats["has_at"] is True
    
    def test_get_dep_stats_sorted(self):
        calls = [
            make_py_call("mul", Name(id="a"), Name(id="b")),
            make_py_call("add", Name(id="a"), Name(id="b")),
            make_py_call("sub", Name(id="a"), Name(id="b")),
        ]
        stmts = [ExprStmt(value=c) for c in calls]
        program = make_program(stmts)
        
        stats = get_dep_stats(program)
        
        # deps should be sorted
        assert stats["deps"] == ["add", "mul", "sub"]
    
    def test_get_dep_stats_has_flags(self):
        call = make_py_call("slice", Name(id="items"), Constant(value=0), Constant(value=5))
        stmt = ExprStmt(value=call)
        program = make_program([stmt])
        
        stats = get_dep_stats(program)
        
        assert stats["has_slice"] is True
        assert stats["has_add"] is False
        assert stats["has_mul"] is False
        assert stats["has_mod"] is False
    
    def test_dce_optimizer_init(self):
        opt = DCEOptimizer()
        assert opt.eliminated_count == 0
    
    def test_collector_generic_visit(self):
        collector = RuntimeDepCollector()
        
        # Should not crash on non-call nodes
        assign = Assignment(target="x", value=Constant(value=5))
        collector.generic_visit(assign)
        
        assert collector.deps == set()
    
    def test_is_always_true_string(self):
        """Non-empty string is truthy but we don't handle it."""
        assert is_always_true(Constant(value="hello")) is False
    
    def test_is_always_false_empty_string(self):
        """Empty string is falsy but we don't handle it."""
        assert is_always_false(Constant(value="")) is False
    
    def test_dce_preserves_other_statements(self):
        assign = Assignment(target="x", value=Constant(value=5))
        if_stmt = make_if(
            Constant(value=False),
            [Assignment(target="y", value=Constant(value=1))]
        )
        program = make_program([assign, if_stmt])
        
        result = eliminate_dead_code(program)
        
        # Should keep the assignment
        assert len(result.body) == 1
        assert result.body[0].target == "x"
