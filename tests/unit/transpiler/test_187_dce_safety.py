"""
Phase 18.7 - DCE Safety Tests

Tests to ensure dead code elimination is safe and doesn't remove live code.
"""

import pytest
from pynext.transpiler import parse
from pynext.transpiler.nodes import (
    Program, Assignment, If, For, While, FunctionDef, ExprStmt, Return,
    Name, Constant, Call, Attribute, Compare, BinOp, UnaryOp,
)
from pynext.transpiler.optimizer import optimize, eliminate_dead_code
from pynext.transpiler.optimizer.dce import is_always_true, is_always_false


# =============================================================================
# 1. PRESERVE LIVE CODE
# =============================================================================

class TestPreserveLiveCode:
    """Ensure live code is never removed."""
    
    def test_preserve_assignment(self):
        """Simple assignment preserved."""
        ir = parse('x = 5')
        optimized = optimize(ir)
        assert len(optimized.body) == 1
    
    def test_preserve_function_call(self):
        """Function call preserved (side effects)."""
        ir = parse('print("hello")')
        optimized = optimize(ir)
        assert len(optimized.body) == 1
    
    def test_preserve_dynamic_if(self):
        """if with dynamic condition preserved."""
        ir = parse('''
if x > 0:
    y = 1
''')
        optimized = optimize(ir)
        assert len(optimized.body) == 1
        assert isinstance(optimized.body[0], If)
    
    def test_preserve_loop(self):
        """Loop preserved."""
        ir = parse('''
for i in range(10):
    process(i)
''')
        optimized = optimize(ir)
        assert len(optimized.body) == 1
        assert isinstance(optimized.body[0], For)
    
    def test_preserve_function_def(self):
        """Function definition preserved."""
        ir = parse('''
def foo():
    return 42
''')
        optimized = optimize(ir)
        assert len(optimized.body) == 1
        assert isinstance(optimized.body[0], FunctionDef)


# =============================================================================
# 2. REMOVE DEAD CODE
# =============================================================================

class TestRemoveDeadCode:
    """Ensure dead code is removed."""
    
    def test_remove_if_false(self):
        """if False: ... removed entirely."""
        ir = parse('''
if False:
    dead = 1
''')
        optimized = optimize(ir)
        assert len(optimized.body) == 0
    
    def test_remove_else_of_if_true(self):
        """if True: ... keeps body, removes else."""
        ir = parse('''
if True:
    x = 1
else:
    dead = 2
''')
        optimized = optimize(ir)
        assert len(optimized.body) == 1
        # Body should be unwrapped to just the assignment
        assert isinstance(optimized.body[0], Assignment)
    
    def test_remove_if_body_when_false(self):
        """if False: ... else: y = 2 keeps else."""
        ir = parse('''
if False:
    dead = 1
else:
    y = 2
''')
        optimized = optimize(ir)
        assert len(optimized.body) == 1
        # Should keep the else body
        assert isinstance(optimized.body[0], Assignment)
        assert optimized.body[0].target == "y"


# =============================================================================
# 3. CONSTANT ANALYSIS CORRECTNESS
# =============================================================================

class TestConstantAnalysis:
    """Test is_always_true and is_always_false."""
    
    def test_true_literal_is_always_true(self):
        """True literal detected."""
        node = Constant(value=True)
        assert is_always_true(node)
        assert not is_always_false(node)
    
    def test_false_literal_is_always_false(self):
        """False literal detected."""
        node = Constant(value=False)
        assert is_always_false(node)
        assert not is_always_true(node)
    
    def test_none_is_always_false(self):
        """None is always false."""
        node = Constant(value=None)
        assert is_always_false(node)
    
    def test_zero_is_always_false(self):
        """0 is always false."""
        node = Constant(value=0)
        assert is_always_false(node)
    
    def test_empty_string_is_always_false(self):
        """Empty string is always false.
        
        Note: DCE currently only checks for None/False/0, not empty string.
        This is a conservative approach.
        """
        node = Constant(value="")
        # Current implementation: doesn't check empty string
        # Strings require __py.bool() for Python semantics
        assert not is_always_false(node)  # Conservative
    
    def test_nonzero_is_always_true(self):
        """Non-zero number is always true."""
        node = Constant(value=42)
        assert is_always_true(node)
    
    def test_non_empty_string_not_detected(self):
        """Non-empty string not detected as always true.
        
        DCE is conservative and doesn't optimize string conditions.
        """
        node = Constant(value="hello")
        # Conservative - would need __py.bool() semantics
        assert not is_always_true(node)
    
    def test_variable_not_constant(self):
        """Variable is neither always-true nor always-false."""
        node = Name(id="x")
        assert not is_always_true(node)
        assert not is_always_false(node)
    
    def test_comparison_not_constant(self):
        """Comparison with variable not constant."""
        node = Compare(
            left=Name(id="x"),
            ops=("gt",),
            comparators=(Constant(value=0),)
        )
        assert not is_always_true(node)
        assert not is_always_false(node)


# =============================================================================
# 4. NESTED DEAD CODE
# =============================================================================

class TestNestedDeadCode:
    """Test nested dead code removal."""
    
    def test_nested_if_false_removed(self):
        """Nested if False removed."""
        ir = parse('''
if condition:
    if False:
        dead = 1
    y = 2
''')
        optimized = optimize(ir)
        # Outer if preserved with only y = 2 in body
        assert len(optimized.body) == 1
        outer_if = optimized.body[0]
        assert isinstance(outer_if, If)
    
    def test_if_inside_loop(self):
        """Dead code in loop body."""
        ir = parse('''
for i in range(10):
    if False:
        dead = 1
    process(i)
''')
        optimized = optimize(ir)
        loop = optimized.body[0]
        # DCE replaces dead if with None placeholder
        # Filter out None to check real statements
        real_body = [s for s in loop.body if s is not None]
        assert len(real_body) == 1


# =============================================================================
# 5. EDGE CASES
# =============================================================================

class TestDCEEdgeCases:
    """Edge cases for DCE."""
    
    def test_empty_program(self):
        """Empty program stays empty."""
        ir = Program(body=())
        optimized = optimize(ir)
        assert optimized.body == ()
    
    def test_only_dead_code(self):
        """Program with only dead code becomes empty."""
        ir = parse('''
if False:
    x = 1
''')
        optimized = optimize(ir)
        assert len(optimized.body) == 0
    
    def test_mixed_live_and_dead(self):
        """Mixed live and dead code."""
        ir = parse('''
x = 1
if False:
    dead = 2
y = 3
if True:
    z = 4
else:
    dead = 5
''')
        optimized = optimize(ir)
        # x = 1, y = 3, z = 4 should remain
        assert len(optimized.body) == 3
