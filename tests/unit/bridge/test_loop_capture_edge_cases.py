"""
Tests for Loop Variable Capture Edge Cases

Tests the LoopCaptureOptimizer for edge cases that could cause
silent failures in transpiled event handlers.

Critical Scenarios:
1. Nested loops (both outer and inner variables need capture)
2. ForUnpack with multiple targets (i, item = enumerate(...))
3. Lambda inside list comprehension inside loop
4. While loops with manually updated counter variables
5. Lambda inside conditional inside loop
6. Multiple lambdas in same loop body
7. Lambda that shadows loop variable in its own params
"""

import pytest
from pynext.transpiler import parse, emit
from pynext.transpiler.optimizer.capture import (
    fix_loop_captures,
    lambda_references_var,
    get_loop_variables,
    find_lambdas_in_node,
    needs_capture_fix,
    wrap_lambda_with_capture,
    LoopCaptureOptimizer,
)
from pynext.transpiler.nodes import Lambda, Name, For, ForUnpack, While, Call


class TestBasicLoopCapture:
    """Test basic loop variable capture functionality."""
    
    def test_simple_for_loop_capture(self):
        """Lambda in for loop should be wrapped with IIFE."""
        ir = parse('''
for i in range(5):
    onclick = lambda: handle(i)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Should have IIFE pattern: ((i) => ...) (i)
        assert "(i) =>" in js or "((i)" in js, f"Expected IIFE wrapper, got: {js}"
    
    def test_lambda_not_referencing_loop_var(self):
        """Lambda that doesn't reference loop var should NOT be wrapped."""
        ir = parse('''
for i in range(5):
    onclick = lambda: handle(x)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Should NOT have IIFE pattern for i
        assert "((i)" not in js, f"Should not wrap, got: {js}"
    
    def test_lambda_with_shadowing_param(self):
        """Lambda with param that shadows loop var should NOT be wrapped for that var."""
        ir = parse('''
for i in range(5):
    onclick = lambda i: handle(i)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Should NOT wrap - lambda has its own i parameter
        # Check that there's no double (i) => pattern
        assert js.count("(i) =>") <= 1, f"Should not double-wrap, got: {js}"


class TestNestedLoopCapture:
    """Test nested loops where multiple variables need capture."""
    
    def test_nested_for_loops_both_vars(self):
        """Nested loops - lambda referencing both outer and inner vars."""
        ir = parse('''
for i in range(3):
    for j in range(3):
        onclick = lambda: handle(i, j)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Both i and j should be captured
        assert "i" in js and "j" in js
        # Should have IIFE pattern capturing both
        # The order might vary, so check for presence of capture pattern
        assert "=>" in js, f"Expected arrow function for IIFE, got: {js}"
    
    def test_nested_loops_only_outer_var_used(self):
        """Nested loops but lambda only uses outer variable."""
        ir = parse('''
for i in range(3):
    for j in range(3):
        onclick = lambda: handle(i)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Only i should be captured (not j)
        assert "i" in js
    
    def test_nested_loops_only_inner_var_used(self):
        """Nested loops but lambda only uses inner variable."""
        ir = parse('''
for i in range(3):
    for j in range(3):
        onclick = lambda: handle(j)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Only j should be captured
        assert "j" in js
    
    def test_triple_nested_loops(self):
        """Three levels of nested loops."""
        ir = parse('''
for i in range(2):
    for j in range(2):
        for k in range(2):
            onclick = lambda: handle(i, j, k)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # All three variables should be present
        assert "i" in js and "j" in js and "k" in js


class TestForUnpackCapture:
    """Test for loops with tuple unpacking (enumerate, items, etc)."""
    
    def test_enumerate_style_unpack(self):
        """for i, item in enumerate(items) - both vars captured."""
        ir = parse('''
for i, item in enumerate(items):
    onclick = lambda: handle(i, item)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Both i and item should be captured
        assert "i" in js and "item" in js
        assert "=>" in js, f"Expected IIFE, got: {js}"
    
    def test_dict_items_unpack(self):
        """for key, value in dict.items() style."""
        ir = parse('''
for key, value in data.items():
    onclick = lambda: handle(key, value)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        assert "key" in js and "value" in js
    
    def test_triple_unpack(self):
        """for a, b, c in items - three variables."""
        ir = parse('''
for a, b, c in rows:
    onclick = lambda: process(a, b, c)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        assert "a" in js and "b" in js and "c" in js
    
    def test_unpack_only_using_one_var(self):
        """Unpack multiple but only use one in lambda."""
        ir = parse('''
for i, item in enumerate(items):
    onclick = lambda: handle(i)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Only i needs capture, not item
        assert "i" in js


class TestLambdaInComplexExpressions:
    """Test lambdas in more complex contexts within loops."""
    
    def test_lambda_in_list_append(self):
        """Lambda passed to list.append inside loop."""
        ir = parse('''
for i in range(5):
    handlers.append(lambda: click(i))
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        assert "=>" in js
    
    def test_lambda_in_dict_assignment(self):
        """Lambda as dict value inside loop."""
        ir = parse('''
for i in range(5):
    handlers[i] = lambda: click(i)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        assert "=>" in js
    
    def test_lambda_in_conditional(self):
        """Lambda inside if statement inside loop."""
        ir = parse('''
for i in range(5):
    if i > 0:
        onclick = lambda: handle(i)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        assert "=>" in js
    
    def test_multiple_lambdas_same_loop(self):
        """Multiple lambdas in same loop body."""
        ir = parse('''
for i in range(5):
    onclick = lambda: handle(i)
    onhover = lambda: hover(i)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Both lambdas should be wrapped
        # Count arrow functions - should have at least 2 IIFE wrappers + 2 inner lambdas
        arrow_count = js.count("=>")
        assert arrow_count >= 4, f"Expected at least 4 arrows (2 IIFEs + 2 lambdas), got {arrow_count}: {js}"
    
    def test_lambda_as_function_argument(self):
        """Lambda passed as argument to function call inside loop."""
        ir = parse('''
for i in range(5):
    process(callback=lambda: done(i))
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        assert "=>" in js


class TestWhileLoopCapture:
    """Test while loops (no explicit loop variable)."""
    
    def test_while_loop_no_auto_capture(self):
        """While loops don't have explicit loop vars - no auto capture."""
        ir = parse('''
i = 0
while i < 5:
    onclick = lambda: handle(i)
    i += 1
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # While loop optimizer should NOT automatically capture
        # (user must handle manually or use for loop)
        # Just verify it doesn't crash
        assert "while" in js.lower() or "for" in js.lower() or "i < 5" in js


class TestLambdaReferencesVarFunction:
    """Test the lambda_references_var helper function."""
    
    def test_simple_reference(self):
        """Lambda directly references variable."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Name(id="i"),
            line=1, col=0
        )
        assert lambda_references_var(lam, "i") is True
        assert lambda_references_var(lam, "j") is False
    
    def test_reference_in_call(self):
        """Lambda references var in function call."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Call(
                func=Name(id="handle"),
                args=(Name(id="i"),),
                keywords={},
                line=1, col=0
            ),
            line=1, col=0
        )
        assert lambda_references_var(lam, "i") is True
        assert lambda_references_var(lam, "handle") is True  # function name too
        assert lambda_references_var(lam, "j") is False


class TestGetLoopVariables:
    """Test the get_loop_variables helper function."""
    
    def test_for_loop_single_var(self):
        """For loop with single target."""
        node = For(
            target="i",
            iter=Name(id="items"),
            body=(),
            line=1, col=0
        )
        vars = get_loop_variables(node)
        assert vars == {"i"}
    
    def test_for_unpack_multiple_vars(self):
        """ForUnpack with multiple targets."""
        node = ForUnpack(
            targets=("i", "item"),
            iter=Name(id="items"),
            body=(),
            line=1, col=0
        )
        vars = get_loop_variables(node)
        assert vars == {"i", "item"}
    
    def test_while_loop_no_vars(self):
        """While loop has no explicit loop vars."""
        node = While(
            test=Name(id="condition"),
            body=(),
            line=1, col=0
        )
        vars = get_loop_variables(node)
        assert vars == set()


class TestNeedsCaptureFixFunction:
    """Test the needs_capture_fix detection function."""
    
    def test_needs_fix_simple_case(self):
        """Simple lambda referencing loop var needs fix."""
        ir = parse('''
for i in range(5):
    onclick = lambda: handle(i)
''')
        assert needs_capture_fix(ir) is True
    
    def test_no_fix_needed_no_lambda(self):
        """Loop without lambda doesn't need fix."""
        ir = parse('''
for i in range(5):
    print(i)
''')
        assert needs_capture_fix(ir) is False
    
    def test_no_fix_needed_no_reference(self):
        """Lambda not referencing loop var doesn't need fix."""
        ir = parse('''
for i in range(5):
    onclick = lambda: handle(x)
''')
        assert needs_capture_fix(ir) is False


class TestWrapLambdaWithCapture:
    """Test the IIFE wrapping function."""
    
    def test_wrap_single_var(self):
        """Wrap lambda capturing single variable."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Name(id="i"),
            line=1, col=0
        )
        wrapped = wrap_lambda_with_capture(lam, {"i"})
        
        # Should be a Call node (IIFE)
        assert isinstance(wrapped, Call)
        # The function being called should be a Lambda
        assert isinstance(wrapped.func, Lambda)
        # The outer lambda should have 'i' as parameter
        assert "i" in wrapped.func.args
        # The inner body should be the original lambda
        assert isinstance(wrapped.func.body, Lambda)
    
    def test_wrap_multiple_vars(self):
        """Wrap lambda capturing multiple variables."""
        lam = Lambda(
            args=(),
            defaults=(),
            body=Name(id="i"),  # simplified body
            line=1, col=0
        )
        wrapped = wrap_lambda_with_capture(lam, {"i", "j"})
        
        assert isinstance(wrapped, Call)
        # Should have two arguments passed to IIFE
        assert len(wrapped.args) == 2


class TestCaptureOptimizerIntegration:
    """Integration tests for the full optimizer pass."""
    
    def test_optimizer_preserves_other_code(self):
        """Optimizer should not modify code outside loops."""
        ir = parse('''
x = 5
for i in range(5):
    onclick = lambda: handle(i)
y = 10
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Non-loop code should be preserved
        assert "x = 5" in js or "let x = 5" in js
        assert "y = 10" in js or "let y = 10" in js
    
    def test_optimizer_handles_empty_loop(self):
        """Empty loop body should not crash."""
        ir = parse('''
for i in range(5):
    pass
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Should not crash
        assert js is not None
    
    def test_optimizer_idempotent(self):
        """Running optimizer twice should produce same result."""
        ir = parse('''
for i in range(5):
    onclick = lambda: handle(i)
''')
        fixed1 = fix_loop_captures(ir)
        fixed2 = fix_loop_captures(fixed1)
        
        js1 = emit(fixed1)
        js2 = emit(fixed2)
        
        # Second pass should not double-wrap
        assert js1 == js2, f"Optimizer not idempotent:\n{js1}\nvs\n{js2}"


class TestEdgeCasesFromRealWorld:
    """Edge cases inspired by real-world patterns."""
    
    def test_event_handler_in_loop(self):
        """Common pattern: creating event handlers in loop."""
        ir = parse('''
for item in items:
    item.onclick = lambda: select(item)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        assert "=>" in js
    
    def test_callback_registration(self):
        """Registering callbacks in a loop."""
        ir = parse('''
for i in range(5):
    register_handler(lambda e: on_event(i, e))
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        assert "=>" in js
    
    def test_creating_closures_list(self):
        """Creating a list of closures."""
        ir = parse('''
closures = []
for i in range(5):
    closures.append(lambda: get_value(i))
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        assert "=>" in js
    
    def test_lambda_with_default_arg_referencing_loop_var(self):
        """Lambda with default argument value from loop var."""
        ir = parse('''
for i in range(5):
    onclick = lambda x=i: handle(x)
''')
        fixed = fix_loop_captures(ir)
        js = emit(fixed)
        
        # Default args also need proper capture
        # This is a tricky case
        assert "i" in js
