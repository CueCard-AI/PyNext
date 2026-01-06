"""
Phase 18.7 - Elision Safety Regression Tests

These tests ensure that dangerous Python/JS semantic differences are NEVER elided.
Each test verifies that __py.* wrappers are PRESERVED when elision would be unsafe.

CRITICAL: If any of these tests fail, the optimizer would produce INCORRECT code.
"""

import pytest
from pynext.transpiler import parse
from pynext.transpiler.nodes import (
    Program, Assignment, If, For, ExprStmt, Return,
    Name, Constant, Call, Attribute, Compare, BinOp, UnaryOp,
    List as ListNode, Dict as DictNode,
)
from pynext.transpiler.optimizer import optimize, infer_types, elide_wrappers
from pynext.transpiler.optimizer._internal.type_env import TypeEnv, PyType


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def make_py_call(method: str, *args) -> Call:
    """Create a __py.method(*args) call node."""
    return Call(
        func=Attribute(value=Name(id="__py"), attr=method),
        args=args,
        keywords={},
    )


def has_py_call(node, method: str) -> bool:
    """Check if a node or its descendants contain __py.method call."""
    if isinstance(node, Call):
        if isinstance(node.func, Attribute):
            if isinstance(node.func.value, Name):
                if node.func.value.id == "__py" and node.func.attr == method:
                    return True
    
    # Recursively check all attributes
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


# =============================================================================
# 1. EMPTY COLLECTION TRUTHINESS (MUST NEVER ELIDE)
# =============================================================================

class TestEmptyCollectionTruthiness:
    """
    Python: [] is falsy, {} is falsy
    JavaScript: [] is truthy, {} is truthy
    
    __py.bool() MUST be preserved for collections.
    """
    
    def test_bool_unknown_variable_preserved(self):
        """Unknown variable could be list/dict - must keep wrapper."""
        call = make_py_call("bool", Name(id="items"))
        if_stmt = If(
            test=call,
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(if_stmt,))
        
        optimized = optimize(program)
        
        # Must preserve __py.bool for unknown type
        assert program_has_py_call(optimized, "bool")
    
    def test_bool_list_literal_correctly_transformed(self):
        """Empty list literal - transformed to .length > 0 (correct JS semantics)."""
        call = make_py_call("bool", ListNode(elts=()))
        if_stmt = If(
            test=call,
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(if_stmt,))
        
        optimized = optimize(program)
        
        # Inliner transforms __py.bool(list) to list.length > 0
        # This is CORRECT - empty list becomes (length > 0) = false
        # Verify __py.bool is removed (replaced with correct JS)
        assert not program_has_py_call(optimized, "bool")
    
    def test_bool_dict_literal_correctly_transformed(self):
        """Empty dict literal - transformed to Object.keys().length > 0."""
        call = make_py_call("bool", DictNode(keys=(), values=()))
        if_stmt = If(
            test=call,
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(if_stmt,))
        
        optimized = optimize(program)
        
        # Inliner transforms __py.bool(dict) to Object.keys(dict).length > 0
        # This is CORRECT - empty dict becomes (length > 0) = false
        assert not program_has_py_call(optimized, "bool")
    
    def test_bool_nonempty_list_correctly_transformed(self):
        """Non-empty list - transformed to .length > 0."""
        call = make_py_call("bool", ListNode(elts=(Constant(value=1),)))
        if_stmt = If(
            test=call,
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(if_stmt,))
        
        optimized = optimize(program)
        
        # Non-empty list -> (length > 0) = true - correct!
        assert not program_has_py_call(optimized, "bool")
    
    def test_bool_function_call_result_preserved(self):
        """Function call result - could be collection."""
        call = make_py_call(
            "bool",
            Call(func=Name(id="get_items"), args=(), keywords={})
        )
        if_stmt = If(
            test=call,
            body=(Assignment(target="x", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(if_stmt,))
        
        optimized = optimize(program)
        
        # Function return could be list/dict
        assert program_has_py_call(optimized, "bool")


# =============================================================================
# 2. COLLECTION EQUALITY (MUST NEVER ELIDE)
# =============================================================================

class TestCollectionEquality:
    """
    Python: [1,2] == [1,2] is True (deep equality)
    JavaScript: [1,2] === [1,2] is false (reference equality)
    
    __py.eq() MUST be preserved for collections.
    """
    
    def test_eq_unknown_variables_preserved(self):
        """Unknown variables could be lists - must keep wrapper."""
        call = make_py_call("eq", Name(id="a"), Name(id="b"))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "eq")
    
    def test_eq_list_literals_preserved(self):
        """List literals - must keep wrapper."""
        call = make_py_call(
            "eq",
            ListNode(elts=(Constant(value=1),)),
            ListNode(elts=(Constant(value=1),))
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "eq")
    
    def test_eq_dict_literals_preserved(self):
        """Dict literals - must keep wrapper."""
        call = make_py_call(
            "eq",
            DictNode(keys=(Constant(value="a"),), values=(Constant(value=1),)),
            DictNode(keys=(Constant(value="a"),), values=(Constant(value=1),))
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "eq")
    
    def test_eq_mixed_types_preserved(self):
        """Mixed types - could have collection on one side."""
        call = make_py_call("eq", Name(id="items"), Constant(value=None))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "eq")


# =============================================================================
# 3. NEGATIVE INDEXING (MUST NEVER ELIDE)
# =============================================================================

class TestNegativeIndexing:
    """
    Python: items[-1] returns last element
    JavaScript: items[-1] returns undefined
    
    __py.at() MUST be preserved for negative or unknown indices.
    """
    
    def test_at_negative_literal_preserved(self):
        """Negative literal index - must keep wrapper."""
        call = make_py_call(
            "at",
            Name(id="items"),
            UnaryOp(op="neg", operand=Constant(value=1))  # -1
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "at")
    
    def test_at_variable_index_preserved(self):
        """Variable index - could be negative."""
        call = make_py_call("at", Name(id="items"), Name(id="idx"))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "at")
    
    def test_at_expression_index_preserved(self):
        """Expression index - could be negative."""
        call = make_py_call(
            "at",
            Name(id="items"),
            BinOp(left=Name(id="i"), op="sub", right=Constant(value=1))
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "at")
    
    def test_at_function_result_preserved(self):
        """Function result as index - could be negative."""
        call = make_py_call(
            "at",
            Name(id="items"),
            Call(func=Name(id="get_index"), args=(), keywords={})
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "at")


# =============================================================================
# 4. NEGATIVE MODULO (MUST NEVER ELIDE)
# =============================================================================

class TestNegativeModulo:
    """
    Python: -7 % 3 = 2 (always positive result)
    JavaScript: -7 % 3 = -1 (follows dividend sign)
    
    __py.mod() MUST be preserved for negative or unknown operands.
    """
    
    def test_mod_negative_dividend_preserved(self):
        """Negative dividend - must keep wrapper."""
        call = make_py_call(
            "mod",
            UnaryOp(op="neg", operand=Constant(value=7)),
            Constant(value=3)
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "mod")
    
    def test_mod_negative_divisor_preserved(self):
        """Negative divisor - must keep wrapper."""
        call = make_py_call(
            "mod",
            Constant(value=7),
            UnaryOp(op="neg", operand=Constant(value=3))
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "mod")
    
    def test_mod_unknown_operands_preserved(self):
        """Unknown operands - could be negative."""
        call = make_py_call("mod", Name(id="a"), Name(id="b"))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "mod")


# =============================================================================
# 5. STRING/LIST MULTIPLICATION (MUST NEVER ELIDE)
# =============================================================================

class TestStringListMultiplication:
    """
    Python: "a" * 3 = "aaa", [1] * 3 = [1,1,1]
    JavaScript: "a" * 3 = NaN, [1] * 3 = NaN
    
    __py.mul() MUST be preserved when string/list is involved.
    """
    
    def test_mul_string_int_preserved(self):
        """String * int - must keep wrapper."""
        call = make_py_call("mul", Constant(value="a"), Constant(value=3))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "mul")
    
    def test_mul_int_string_preserved(self):
        """Int * string - must keep wrapper."""
        call = make_py_call("mul", Constant(value=3), Constant(value="a"))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "mul")
    
    def test_mul_list_int_preserved(self):
        """List * int - must keep wrapper."""
        call = make_py_call(
            "mul",
            ListNode(elts=(Constant(value=1),)),
            Constant(value=3)
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "mul")
    
    def test_mul_unknown_types_preserved(self):
        """Unknown types - could be string/list."""
        call = make_py_call("mul", Name(id="a"), Name(id="b"))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "mul")


# =============================================================================
# 6. LIST CONCATENATION (MUST NEVER ELIDE)
# =============================================================================

class TestListConcatenation:
    """
    Python: [1] + [2] = [1, 2]
    JavaScript: [1] + [2] = "1,2" (string concatenation!)
    
    __py.add() MUST be preserved for lists.
    """
    
    def test_add_list_literals_preserved(self):
        """List + list - must keep wrapper."""
        call = make_py_call(
            "add",
            ListNode(elts=(Constant(value=1),)),
            ListNode(elts=(Constant(value=2),))
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "add")
    
    def test_add_unknown_could_be_list(self):
        """Unknown + unknown - could be lists."""
        call = make_py_call("add", Name(id="a"), Name(id="b"))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "add")
    
    def test_add_list_and_unknown_preserved(self):
        """List + unknown - must keep wrapper."""
        call = make_py_call(
            "add",
            ListNode(elts=(Constant(value=1),)),
            Name(id="other")
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "add")


# =============================================================================
# 7. FLOOR DIVISION (ALWAYS KEEP WRAPPER)
# =============================================================================

class TestFloorDivision:
    """
    Python: 7 // 3 = 2 (integer division)
    JavaScript: No native equivalent, needs Math.floor(7/3)
    
    __py.floordiv() MUST always be preserved.
    """
    
    def test_floordiv_positive_ints_preserved(self):
        """Positive ints - still need wrapper."""
        call = make_py_call("floordiv", Constant(value=7), Constant(value=3))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "floordiv")
    
    def test_floordiv_negatives_preserved(self):
        """Negative operands - must keep wrapper."""
        call = make_py_call(
            "floordiv",
            UnaryOp(op="neg", operand=Constant(value=7)),
            Constant(value=3)
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "floordiv")


# =============================================================================
# 8. SLICE WITH NEGATIVE INDICES (MUST NEVER ELIDE)
# =============================================================================

class TestSliceNegativeIndices:
    """
    Python: items[-2:] returns last 2 elements
    JavaScript: items.slice(-2) works, but complex cases differ
    
    __py.slice() MUST be preserved for negative indices.
    """
    
    def test_slice_negative_start_preserved(self):
        """Negative start index - must keep wrapper."""
        call = make_py_call(
            "slice",
            Name(id="items"),
            UnaryOp(op="neg", operand=Constant(value=2)),
            Constant(value=None),
            Constant(value=None)
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "slice")
    
    def test_slice_negative_stop_preserved(self):
        """Negative stop index - must keep wrapper."""
        call = make_py_call(
            "slice",
            Name(id="items"),
            Constant(value=0),
            UnaryOp(op="neg", operand=Constant(value=1)),
            Constant(value=None)
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "slice")
    
    def test_slice_step_preserved(self):
        """Step != 1 - must keep wrapper."""
        call = make_py_call(
            "slice",
            Name(id="items"),
            Constant(value=0),
            Constant(value=10),
            Constant(value=2)
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "slice")


# =============================================================================
# 9. MEMBERSHIP TESTS ON LISTS (MUST NEVER ELIDE)
# =============================================================================

class TestMembershipTests:
    """
    Python: [1,2] in [[1,2], [3,4]] uses deep equality
    JavaScript: .includes() uses reference equality
    
    __py.in() MUST be preserved for lists.
    """
    
    def test_in_list_preserved(self):
        """Item in list - must keep wrapper for deep equality."""
        call = make_py_call(
            "in",
            Name(id="item"),
            ListNode(elts=(Constant(value=1), Constant(value=2)))
        )
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "in")
    
    def test_in_unknown_container_preserved(self):
        """Unknown container - could be list."""
        call = make_py_call("in", Name(id="item"), Name(id="container"))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        assert program_has_py_call(optimized, "in")


# =============================================================================
# 10. CONFIRMED SAFE ELISIONS (POSITIVE TESTS)
# =============================================================================

class TestSafeElisions:
    """
    These ARE safe to elide - verify they're actually elided.
    """
    
    def test_bool_comparison_elided(self):
        """Comparison is always bool - safe to elide."""
        cmp = Compare(
            left=Name(id="x"),
            ops=("gt",),
            comparators=(Constant(value=0),)
        )
        call = make_py_call("bool", cmp)
        if_stmt = If(
            test=call,
            body=(Assignment(target="y", value=Constant(value=1)),),
            orelse=(),
        )
        program = Program(body=(if_stmt,))
        
        optimized = optimize(program)
        
        # Comparison result is always bool - safe to elide
        assert not program_has_py_call(optimized, "bool")
    
    def test_eq_int_literals_elided(self):
        """Int == int is safe to elide."""
        call = make_py_call("eq", Constant(value=5), Constant(value=5))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        # Int === int works the same
        assert not program_has_py_call(optimized, "eq")
    
    def test_at_positive_literal_elided(self):
        """Positive literal index is safe to elide."""
        call = make_py_call("at", Name(id="items"), Constant(value=0))
        stmt = ExprStmt(value=call)
        program = Program(body=(stmt,))
        
        optimized = optimize(program)
        
        # items[0] works the same in JS
        assert not program_has_py_call(optimized, "at")
