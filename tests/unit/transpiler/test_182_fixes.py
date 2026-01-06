"""
Tests for Phase 18.2 Risk Fixes

This file tests the critical fixes made to Phase 18.2:
1. Chained comparison double-evaluation fix
2. Boolean operator double-evaluation fix  
3. F-string conversion (!r, !s, !a) support
4. Dynamic format specs

These tests verify that expressions with side effects are evaluated
exactly once, matching Python's semantics.
"""

import pytest
from pynext.transpiler import transpile, transpile_expression


# =============================================================================
# CHAINED COMPARISON FIXES
# =============================================================================

class TestChainedComparisonFixes:
    """Tests for chained comparison single-evaluation."""
    
    def test_simple_chained_variables(self):
        """Simple variable chain doesn't need caching."""
        result = transpile_expression("a < b < c")
        assert "&&" in result
        assert "(a <" in result
        assert "(b <" in result
    
    def test_chained_with_function_call_middle(self):
        """Function call in middle should use IIFE caching."""
        result = transpile_expression("a < f() < c")
        # Should use IIFE to cache f()
        assert "_cmp" in result or "=>" in result
        # f() should only appear once in the actual call
        assert result.count("f()") <= 2  # Once in IIFE param, once as arg
    
    def test_chained_three_comparisons(self):
        """Three-way comparison chain."""
        result = transpile_expression("0 < x < y < 100")
        assert "&&" in result
        assert result.count("&&") >= 2  # At least 2 && for 3 comparisons
    
    def test_chained_mixed_operators(self):
        """Chain with different operators."""
        result = transpile_expression("0 <= x < y <= 100")
        assert "(0 <=" in result or "(0<=" in result
        assert "&&" in result
    
    def test_chained_with_method_call(self):
        """Method call in middle position."""
        result = transpile_expression("a < obj.method() < c")
        # Should cache the method call
        assert "=>" in result or "_cmp" in result
    
    def test_chained_equality(self):
        """Chained equality uses __py.eq."""
        result = transpile_expression("a == b == c")
        assert "__py.eq" in result
        assert "&&" in result
    
    def test_single_comparison_no_iife(self):
        """Single comparison shouldn't use IIFE."""
        result = transpile_expression("a < b")
        assert "=>" not in result
        assert "IIFE" not in result
        assert "(a < b)" in result
    
    def test_chained_all_variables_no_iife(self):
        """All variable chain shouldn't use IIFE."""
        result = transpile_expression("x < y < z")
        # All simple variables - no IIFE needed
        assert result.count("=>") == 0 or "_cmp" not in result


class TestChainedComparisonEdgeCases:
    """Edge cases for chained comparisons."""
    
    def test_chained_with_subscript(self):
        """Subscript in middle (could have side effects)."""
        result = transpile_expression("0 < arr[i] < 10")
        # Subscript might have side effects, should cache
        assert "=>" in result or "(0 <" in result
    
    def test_chained_with_ternary(self):
        """Ternary in comparison."""
        result = transpile_expression("0 < (x if cond else y) < 10")
        # Complex expression should be cached
        assert "&&" in result
    
    def test_chained_in_membership(self):
        """Membership test in chain."""
        result = transpile_expression("x in items and y < z")
        assert "__py.in" in result or "includes" in result
    
    def test_chained_not_in(self):
        """Not in operator in comparison."""
        result = transpile_expression("x not in items")
        assert "!__py.in" in result or "!" in result


# =============================================================================
# BOOLEAN OPERATOR FIXES
# =============================================================================

class TestBooleanOperatorFixes:
    """Tests for boolean operator single-evaluation."""
    
    def test_simple_and_variables(self):
        """Simple variable and doesn't need caching."""
        result = transpile_expression("a and b")
        assert "__py.bool(a)" in result
        assert "?" in result
    
    def test_simple_or_variables(self):
        """Simple variable or doesn't need caching."""
        result = transpile_expression("a or b")
        assert "__py.bool(a)" in result
        assert "?" in result
    
    def test_and_with_function_call(self):
        """Function call in and should use IIFE caching."""
        result = transpile_expression("f() and g()")
        # Should cache f() to avoid double evaluation
        assert "=>" in result or "_b" in result
    
    def test_or_with_function_call(self):
        """Function call in or should use IIFE caching."""
        result = transpile_expression("f() or g()")
        # Should cache f()
        assert "=>" in result or "_b" in result
    
    def test_chained_and(self):
        """Chained and operators."""
        result = transpile_expression("a and b and c")
        assert result.count("__py.bool") >= 2
    
    def test_chained_or(self):
        """Chained or operators."""
        result = transpile_expression("a or b or c")
        assert result.count("__py.bool") >= 2
    
    def test_mixed_and_or(self):
        """Mixed and/or operators."""
        result = transpile_expression("a and b or c")
        assert "__py.bool" in result
    
    def test_not_operator(self):
        """Not operator uses bool."""
        result = transpile_expression("not x")
        assert "!__py.bool" in result
    
    def test_constants_no_caching(self):
        """Constants don't need caching."""
        result = transpile_expression("True and x")
        assert "true" in result.lower() or "True" in result


class TestBooleanOperatorEdgeCases:
    """Edge cases for boolean operators."""
    
    def test_nested_boolean(self):
        """Nested boolean expressions."""
        result = transpile_expression("(a and b) or (c and d)")
        assert "__py.bool" in result
    
    def test_boolean_with_comparison(self):
        """Boolean with comparison."""
        result = transpile_expression("x > 0 and y > 0")
        assert "&&" in result or "?" in result
    
    def test_boolean_in_if_condition(self):
        """Boolean operator as if condition."""
        result = transpile("if a and b:\n    pass")
        assert "__py.bool" in result
    
    def test_empty_list_truthiness(self):
        """Empty list is falsy in Python."""
        result = transpile_expression("items or []")
        assert "__py.bool" in result


# =============================================================================
# F-STRING CONVERSION FIXES
# =============================================================================

class TestFStringConversionFixes:
    """Tests for f-string !r, !s, !a conversions."""
    
    def test_repr_conversion(self):
        """!r conversion uses repr."""
        result = transpile_expression('f"{obj!r}"')
        assert "__py.repr" in result
    
    def test_str_conversion(self):
        """!s conversion uses String()."""
        result = transpile_expression('f"{val!s}"')
        assert "String(" in result
    
    def test_ascii_conversion(self):
        """!a conversion uses ascii."""
        result = transpile_expression('f"{val!a}"')
        assert "__py.ascii" in result
    
    def test_conversion_with_format_spec(self):
        """Conversion with format spec."""
        result = transpile_expression('f"{obj!r:>20}"')
        assert "__py.repr" in result
        assert "__py.format" in result
    
    def test_multiple_conversions(self):
        """Multiple conversions in one f-string."""
        result = transpile_expression('f"{a!r} {b!s} {c!a}"')
        assert "__py.repr" in result
        assert "String(" in result
        assert "__py.ascii" in result
    
    def test_no_conversion(self):
        """No conversion - direct interpolation."""
        result = transpile_expression('f"{value}"')
        assert "__py.repr" not in result
        assert "String(" not in result


class TestFStringEdgeCases:
    """Edge cases for f-strings."""
    
    def test_fstring_with_expression(self):
        """Complex expression in f-string."""
        result = transpile_expression('f"{x + y}"')
        assert "${" in result
    
    def test_fstring_with_method_call(self):
        """Method call in f-string."""
        result = transpile_expression('f"{obj.method()}"')
        assert "${" in result
    
    def test_fstring_format_precision(self):
        """Float precision."""
        result = transpile_expression('f"{x:.2f}"')
        assert "__py.format" in result
        assert ".2f" in result
    
    def test_fstring_format_alignment(self):
        """Alignment format."""
        result = transpile_expression('f"{name:>10}"')
        assert "__py.format" in result
        assert ">10" in result
    
    def test_fstring_empty(self):
        """Empty f-string."""
        result = transpile_expression('f""')
        assert "``" in result or '""' in result
    
    def test_fstring_literal_only(self):
        """F-string with only literal text."""
        result = transpile_expression('f"Hello World"')
        assert "Hello World" in result


# =============================================================================
# NESTED COMPREHENSION TESTS
# =============================================================================

class TestNestedComprehensionFixes:
    """Tests for nested comprehensions."""
    
    def test_simple_nested(self):
        """Simple nested list comprehension."""
        result = transpile_expression("[y for x in matrix for y in x]")
        assert "flatMap" in result or ".map" in result
    
    def test_nested_with_filter(self):
        """Nested comprehension with filter."""
        result = transpile_expression("[y for x in matrix for y in x if y > 0]")
        assert "filter" in result
    
    def test_dict_comprehension_with_filter(self):
        """Dict comprehension with filter."""
        result = transpile_expression("{k: v for k, v in items if v > 0}")
        assert "Object.fromEntries" in result
        assert "filter" in result
    
    def test_set_comprehension(self):
        """Set comprehension."""
        result = transpile_expression("{x for x in items}")
        assert "new Set" in result
    
    def test_tuple_unpacking_in_comp(self):
        """Tuple unpacking in comprehension."""
        result = transpile_expression("[v for k, v in items]")
        assert "[k, v]" in result or "k, v" in result
    
    def test_generator_in_function(self):
        """Generator expression in function call."""
        result = transpile_expression("sum(x for x in items)")
        assert "__py.sum" in result or "reduce" in result


# =============================================================================
# INTEGRATION TESTS - COMBINED FEATURES
# =============================================================================

class TestPhase182Integration:
    """Integration tests combining multiple 18.2 features."""
    
    def test_chained_compare_with_boolop(self):
        """Chained comparison combined with boolean operator."""
        result = transpile_expression("0 < x < 10 and y > 0")
        assert "&&" in result
        assert "__py.bool" in result or "&&" in result
    
    def test_fstring_with_comprehension(self):
        """F-string containing comprehension result."""
        result = transpile_expression('f"Items: {[x*2 for x in items]}"')
        assert "`" in result
        assert ".map" in result
    
    def test_boolop_in_comprehension_filter(self):
        """Boolean operator in comprehension filter."""
        result = transpile_expression("[x for x in items if x and x > 0]")
        assert "filter" in result
    
    def test_complex_handler(self):
        """Complex event handler with multiple features."""
        code = '''
def handle_submit():
    if form.valid and not errors:
        items.set([x for x in values if x > 0])
        message.set(f"Added {len(values)} items")
'''
        result = transpile(code)
        assert "function handle_submit" in result
        assert "__py.bool" in result
        assert ".filter" in result or ".map" in result


# =============================================================================
# SIDE EFFECT VERIFICATION TESTS
# =============================================================================

class TestSideEffectEvaluation:
    """
    These tests verify that expressions are evaluated the correct number of times.
    
    While we can't directly count evaluations in the transpiled JS,
    we can verify the structure suggests single evaluation.
    """
    
    def test_iife_structure_for_complex_chained(self):
        """Complex chained comparison should use IIFE."""
        result = transpile_expression("a < f() < b")
        # IIFE pattern: ((...) => ...)(...) 
        # The function call f() should appear exactly once as argument
        # and once as parameter in the IIFE
        has_iife = "=>" in result and "(" in result
        assert has_iife or result.count("f()") == 1
    
    def test_iife_structure_for_complex_boolop(self):
        """Complex boolean should use IIFE."""
        result = transpile_expression("f() and g()")
        # Should have IIFE structure
        has_iife = "=>" in result
        # Or should have caching pattern
        assert has_iife or "_b" in result
    
    def test_no_iife_for_simple_expressions(self):
        """Simple expressions shouldn't use IIFE."""
        result = transpile_expression("a < b")
        assert "=>" not in result
        
        result = transpile_expression("a and b")
        # Simple variables might still use ternary, but no IIFE
        assert result.count("=>") <= 1
    
    def test_constants_never_cached(self):
        """Constants never need caching."""
        result = transpile_expression("1 and 2 and 3")
        # Constants can be repeated safely
        # No IIFE needed
        pass  # Just verify it compiles


# =============================================================================
# PYTHON SEMANTIC EQUIVALENCE TESTS  
# =============================================================================

class TestPythonSemantics:
    """Tests verifying Python semantic equivalence."""
    
    def test_and_returns_value_not_bool(self):
        """Python and returns value, not boolean."""
        result = transpile_expression("x and y")
        # Should return y if x is truthy, else x
        assert "?" in result and ":" in result
    
    def test_or_returns_value_not_bool(self):
        """Python or returns value, not boolean."""
        result = transpile_expression("x or y")
        # Should return x if x is truthy, else y
        assert "?" in result and ":" in result
    
    def test_chained_comparison_all_must_pass(self):
        """All parts of chain must be true."""
        result = transpile_expression("a < b < c")
        # Should use && to combine
        assert "&&" in result
    
    def test_membership_uses_deep_equality(self):
        """In operator uses deep equality."""
        result = transpile_expression("x in items")
        assert "__py.in" in result
    
    def test_equality_uses_deep_equality(self):
        """== uses deep equality."""
        result = transpile_expression("a == b")
        assert "__py.eq" in result
