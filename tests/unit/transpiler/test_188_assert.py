"""
Phase 18.8: Assert Statement Tests

Tests for assert statement parsing and emitting.

Tests: 40
"""

import pytest
from pynext.transpiler import parse, emit, transpile
from pynext.transpiler.nodes import Assert, Program, Constant, Compare, Name


class TestAssertParsing:
    """Tests for parsing assert statements."""
    
    def test_simple_assert(self):
        """Parse simple assert without message."""
        ir = parse("assert x > 0")
        assert isinstance(ir, Program)
        stmt = ir.body[0]
        assert isinstance(stmt, Assert)
        assert stmt.msg is None
    
    def test_assert_with_message(self):
        """Parse assert with message."""
        ir = parse('assert x > 0, "x must be positive"')
        stmt = ir.body[0]
        assert isinstance(stmt, Assert)
        assert stmt.msg is not None
        assert isinstance(stmt.msg, Constant)
    
    def test_assert_equality(self):
        """Parse assert with equality check."""
        ir = parse("assert x == 5")
        stmt = ir.body[0]
        assert isinstance(stmt, Assert)
        assert isinstance(stmt.test, Compare)
    
    def test_assert_not_equal(self):
        """Parse assert with not equal."""
        ir = parse("assert x != 0")
        stmt = ir.body[0]
        assert isinstance(stmt, Assert)
    
    def test_assert_less_than(self):
        """Parse assert with less than."""
        ir = parse("assert x < 100")
        stmt = ir.body[0]
        assert isinstance(stmt, Assert)
    
    def test_assert_greater_equal(self):
        """Parse assert with greater or equal."""
        ir = parse("assert x >= 0")
        stmt = ir.body[0]
        assert isinstance(stmt, Assert)
    
    def test_assert_with_name(self):
        """Parse assert with variable as test."""
        ir = parse("assert valid")
        stmt = ir.body[0]
        assert isinstance(stmt, Assert)
        assert isinstance(stmt.test, Name)
    
    def test_assert_complex_condition(self):
        """Parse assert with complex condition."""
        ir = parse("assert x > 0 and y > 0")
        stmt = ir.body[0]
        assert isinstance(stmt, Assert)
    
    def test_assert_with_expression_message(self):
        """Parse assert with expression as message."""
        ir = parse('assert x > 0, "x is " + str(x)')
        stmt = ir.body[0]
        assert isinstance(stmt, Assert)
        assert stmt.msg is not None
    
    def test_assert_in_function(self):
        """Parse assert inside a function."""
        code = '''
def validate(x):
    assert x > 0
    return x
'''
        ir = parse(code)
        assert isinstance(ir, Program)


class TestAssertEmitting:
    """Tests for emitting assert statements."""
    
    def test_emit_simple_assert(self):
        """Emit simple assert."""
        js = transpile("assert x > 0")
        assert "if (!" in js
        assert "(x > 0)" in js
        assert "throw new Error" in js
        assert "AssertionError" in js
    
    def test_emit_assert_with_message(self):
        """Emit assert with string message."""
        js = transpile('assert x > 0, "must be positive"')
        assert "if (!" in js
        assert "(x > 0)" in js
        assert "must be positive" in js
    
    def test_emit_assert_equality(self):
        """Emit assert with equality."""
        js = transpile("assert x == 5")
        assert "if (!(" in js
        assert "throw" in js
    
    def test_emit_assert_variable(self):
        """Emit assert with variable."""
        js = transpile("assert valid")
        assert "if (!(valid))" in js or "if (!valid)" in js
    
    def test_emit_assert_produces_throw(self):
        """Assert emits throw statement."""
        js = transpile("assert True")
        assert "throw" in js
    
    def test_emit_assert_uses_error(self):
        """Assert uses Error constructor."""
        js = transpile("assert x")
        assert "new Error" in js
    
    def test_emit_assert_with_and(self):
        """Emit assert with and condition."""
        js = transpile("assert x > 0 and y > 0")
        assert "if (!(" in js
        assert "throw" in js
    
    def test_emit_assert_with_or(self):
        """Emit assert with or condition."""
        js = transpile("assert x == 0 or y == 0")
        assert "throw" in js
    
    def test_emit_assert_not_condition(self):
        """Emit assert with not condition."""
        js = transpile("assert not invalid")
        assert "throw" in js
    
    def test_emit_assert_in_list(self):
        """Emit assert with in operator."""
        js = transpile("assert x in items")
        assert "throw" in js


class TestAssertNode:
    """Tests for Assert IR node."""
    
    def test_create_assert_node(self):
        """Create Assert node directly."""
        node = Assert(
            test=Compare(left=Name(id="x"), ops=("gt",), comparators=(Constant(0),)),
            msg=Constant("must be positive"),
        )
        assert node.test is not None
        assert node.msg is not None
    
    def test_assert_node_without_msg(self):
        """Create Assert node without message."""
        node = Assert(
            test=Name(id="valid"),
            msg=None,
        )
        assert node.msg is None
    
    def test_emit_assert_node_directly(self):
        """Emit Assert node directly."""
        node = Assert(
            test=Name(id="x"),
            msg=None,
            line=1,
            col=0,
        )
        prog = Program(body=(node,))
        js = emit(prog)
        assert "if (!(" in js
        assert "throw" in js


class TestAssertEdgeCases:
    """Edge cases for assert."""
    
    def test_assert_true(self):
        """Assert True (always passes)."""
        js = transpile("assert True")
        assert "if (!(true))" in js
    
    def test_assert_false(self):
        """Assert False (always fails)."""
        js = transpile("assert False")
        assert "if (!(false))" in js
    
    def test_assert_with_function_call(self):
        """Assert with function call as test."""
        js = transpile("assert is_valid(x)")
        assert "throw" in js
    
    def test_assert_with_method_call(self):
        """Assert with method call as test."""
        js = transpile("assert obj.validate()")
        assert "throw" in js
    
    def test_assert_with_list_expression(self):
        """Assert with list as test."""
        js = transpile("assert [1, 2, 3]")
        assert "throw" in js
    
    def test_assert_empty_string_message(self):
        """Assert with empty string message."""
        js = transpile('assert x, ""')
        assert "throw" in js
    
    def test_multiple_asserts(self):
        """Multiple assert statements."""
        code = '''
assert x > 0
assert y > 0
assert x != y
'''
        js = transpile(code)
        assert js.count("throw") == 3
    
    def test_assert_in_loop(self):
        """Assert inside a loop."""
        code = '''
for x in items:
    assert x > 0
'''
        js = transpile(code)
        assert "throw" in js
    
    def test_assert_in_condition(self):
        """Assert inside an if block."""
        code = '''
if condition:
    assert x > 0
'''
        js = transpile(code)
        assert "throw" in js

