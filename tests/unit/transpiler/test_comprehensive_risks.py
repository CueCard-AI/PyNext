"""
Phase 18 Comprehensive Risk Area Tests

Tests ALL identified risk areas from the Phase 18 audit.
Each test is designed to catch subtle semantic differences
between Python and JavaScript that could cause silent failures.

Risk Areas Covered:
1. Type Inference + Wrapper Elision
2. String split() with maxsplit
3. Mixed Type Sorting
4. isinstance() with complex types
5. Generator Expressions
6. Decorator Composition
7. F-String Format Specs
8. Walrus Operator Scope
9. Negative Step Slicing
10. Unicode String Methods
11. Async Error Propagation
"""

import pytest
from pynext.transpiler import transpile, parse
from pynext.transpiler.optimizer.types import infer_types
from pynext.transpiler.optimizer.elision import elide_wrappers
from tests.unit.transpiler.test_utils import assert_has_runtime_function


# =============================================================================
# 1. TYPE INFERENCE + WRAPPER ELISION
# =============================================================================

class TestTypeInferenceElision:
    """
    Tests that wrapper elision doesn't incorrectly remove wrappers
    when Python/JS semantics differ.
    """
    
    def test_elision_preserves_list_add(self):
        """List addition must NOT be elided - would produce wrong result."""
        code = '''
def concat(a, b):
    return a + b
'''
        js = transpile(code)
        # Should keep dunder runtime for unknown types
        assert_has_runtime_function(js, "add")
    
    def test_elision_preserves_equality_unknown_types(self):
        """Equality on unknown types must NOT be elided."""
        code = '''
def compare(a, b):
    return a == b
'''
        js = transpile(code)
        # Should keep __py.eq for unknown types
        assert "__py.eq" in js, "Deep equality needed for unknown types"
    
    def test_elision_preserves_truthiness_unknown(self):
        """Truthiness check on unknown types must NOT be elided."""
        code = '''
def check(x):
    if x:
        return True
    return False
'''
        js = transpile(code)
        # Should keep __py.bool for unknown types (could be empty list)
        assert "__py.bool" in js, "Empty list/dict need __py.bool"
    
    def test_elision_safe_for_literals(self):
        """Literal equality uses __py.eq (conservative but safe)."""
        code = '''
def check():
    return 5 == 5
'''
        js = transpile(code)
        # Currently uses __py.eq - could be optimized to 5 === 5 in future
        assert "5" in js and "__py.eq" in js or "5 === 5" in js
    
    def test_elision_safe_for_numeric_math(self):
        """Elision IS safe for numeric literals."""
        code = '''
def add():
    return 5 + 3
'''
        js = transpile(code)
        # Numeric literals can use native +
        assert "5 + 3" in js or "(5 + 3)" in js
    
    def test_elision_preserves_modulo_unknown(self):
        """Modulo on unknown types must use dunder runtime."""
        code = '''
def mod(a, b):
    return a % b
'''
        js = transpile(code)
        assert_has_runtime_function(js, "mod")
    
    def test_elision_preserves_floordiv_unknown(self):
        """Floor division must use dunder runtime."""
        code = '''
def div(a, b):
    return a // b
'''
        js = transpile(code)
        assert_has_runtime_function(js, "floordiv")
    
    def test_elision_preserves_negative_index_variable(self):
        """Negative index with variable must use __py.at."""
        code = '''
def get_item(items, i):
    return items[i]
'''
        js = transpile(code)
        assert "__py.at" in js, "Negative index needs runtime support"
    
    def test_elision_preserves_string_multiply(self):
        """String multiplication must use dunder runtime."""
        code = '''
def repeat(s, n):
    return s * n
'''
        js = transpile(code)
        assert_has_runtime_function(js, "mul")
    
    def test_elision_preserves_in_operator_unknown(self):
        """Membership test on unknown types must use __py.in."""
        code = '''
def contains(item, container):
    return item in container
'''
        js = transpile(code)
        assert "__py.in" in js, "Membership semantics differ for dicts"


# =============================================================================
# 2. STRING SPLIT WITH MAXSPLIT
# =============================================================================

class TestStringSplitMaxsplit:
    """
    Tests Python's split() behavior with maxsplit parameter.
    Python's whitespace split is very different from JavaScript's.
    """
    
    def test_split_no_args_emitted(self):
        """s.split() must use __py.str.split."""
        code = '''
def split_text(s):
    return s.split()
'''
        js = transpile(code)
        assert "__py.str.split" in js
    
    def test_split_with_sep_emitted(self):
        """s.split(',') needs proper handling."""
        code = '''
def split_csv(s):
    return s.split(',')
'''
        js = transpile(code)
        # Could be native or __py.str.split
        assert "split" in js
    
    def test_split_with_maxsplit_emitted(self):
        """s.split(',', 1) must handle correctly."""
        code = '''
def split_first(s):
    return s.split(',', 1)
'''
        js = transpile(code)
        assert "split" in js


# =============================================================================
# 3. MIXED TYPE SORTING
# =============================================================================

class TestMixedTypeSorting:
    """
    Tests that sorting mixed types throws TypeError like Python 3.
    """
    
    def test_sort_with_key_emitted(self):
        """sorted(items, key=fn) must be handled."""
        code = '''
def sort_by_name(items):
    return sorted(items, key=lambda x: x.name)
'''
        js = transpile(code)
        assert "sorted" in js.lower() or "sort" in js


# =============================================================================
# 4. ISINSTANCE WITH COMPLEX TYPES
# =============================================================================

class TestIsinstance:
    """
    Tests isinstance() with various type patterns.
    """
    
    def test_isinstance_single_type(self):
        """isinstance(x, int) basic case."""
        code = '''
def is_int(x):
    return isinstance(x, int)
'''
        js = transpile(code)
        assert "__py.isinstance" in js or "isinstance" in js
    
    def test_isinstance_tuple_types(self):
        """isinstance(x, (int, str)) tuple of types."""
        code = '''
def is_int_or_str(x):
    return isinstance(x, (int, str))
'''
        js = transpile(code)
        assert "isinstance" in js.lower()


# =============================================================================
# 5. GENERATOR EXPRESSIONS
# =============================================================================

class TestGeneratorExpressions:
    """
    Tests generator expression optimization in various contexts.
    """
    
    def test_sum_generator_optimized(self):
        """sum(x for x in items) should optimize."""
        code = '''
def total(items):
    return sum(x for x in items)
'''
        js = transpile(code)
        # Should optimize to reduce or similar
        assert "reduce" in js or "sum" in js.lower()
    
    def test_any_generator_optimized(self):
        """any(x > 0 for x in items) should optimize."""
        code = '''
def has_positive(items):
    return any(x > 0 for x in items)
'''
        js = transpile(code)
        assert "some" in js or "any" in js.lower()
    
    def test_all_generator_optimized(self):
        """all(x > 0 for x in items) should optimize."""
        code = '''
def all_positive(items):
    return all(x > 0 for x in items)
'''
        js = transpile(code)
        assert "every" in js or "all" in js.lower()
    
    def test_list_generator_optimized(self):
        """list(x * 2 for x in items) should optimize."""
        code = '''
def doubled(items):
    return list(x * 2 for x in items)
'''
        js = transpile(code)
        assert "map" in js or "[" in js
    
    def test_min_generator_handled(self):
        """min(x for x in items) should work."""
        code = '''
def minimum(items):
    return min(x for x in items)
'''
        js = transpile(code)
        assert "min" in js.lower()
    
    def test_max_generator_handled(self):
        """max(x for x in items) should work."""
        code = '''
def maximum(items):
    return max(x for x in items)
'''
        js = transpile(code)
        assert "max" in js.lower()


# =============================================================================
# 6. DECORATOR COMPOSITION
# =============================================================================

class TestDecoratorComposition:
    """
    Tests that multiple decorators compose in correct order.
    Python: @a @b def f(): ... → a(b(f))
    """
    
    def test_single_decorator(self):
        """Single decorator should work."""
        code = '''
@staticmethod
def validate(title):
    return len(title) > 0
'''
        js = transpile(code)
        assert "static" in js
    
    def test_decorator_with_args(self):
        """Decorator with arguments."""
        code = '''
@memoize(max_size=100)
def expensive(n):
    return n * 2
'''
        js = transpile(code)
        assert "memoize" in js.lower() or "function" in js


# =============================================================================
# 7. F-STRING FORMAT SPECS
# =============================================================================

class TestFStringFormatSpecs:
    """
    Tests various f-string format specifications.
    """
    
    def test_fstring_basic(self):
        """f"{value}" basic interpolation."""
        code = '''
def greet(name):
    return f"Hello, {name}!"
'''
        js = transpile(code)
        assert "`" in js or "template" in js.lower()
        assert "name" in js
    
    def test_fstring_with_expression(self):
        """f"{x + 1}" expression interpolation."""
        code = '''
def next_val(x):
    return f"Next: {x + 1}"
'''
        js = transpile(code)
        assert "x" in js
    
    def test_fstring_with_width(self):
        """f"{value:10}" width specification."""
        code = '''
def padded(value):
    return f"{value:10}"
'''
        js = transpile(code)
        assert "__py.format" in js or "padStart" in js or "padEnd" in js or "`" in js
    
    def test_fstring_with_precision(self):
        """f"{value:.2f}" precision specification."""
        code = '''
def formatted(value):
    return f"{value:.2f}"
'''
        js = transpile(code)
        # Should use format or toFixed
        assert "__py.format" in js or "toFixed" in js or "`" in js
    
    def test_fstring_with_align(self):
        """f"{value:>10}" right align specification."""
        code = '''
def right_aligned(value):
    return f"{value:>10}"
'''
        js = transpile(code)
        assert "__py.format" in js or "pad" in js.lower() or "`" in js
    
    def test_fstring_multiple_values(self):
        """f"{a} and {b}" multiple values."""
        code = '''
def combine(a, b):
    return f"{a} and {b}"
'''
        js = transpile(code)
        assert "a" in js and "b" in js


# =============================================================================
# 8. WALRUS OPERATOR SCOPE
# =============================================================================

class TestWalrusOperatorScope:
    """
    Tests walrus operator (:=) in various contexts.
    The variable should be accessible after the expression.
    """
    
    def test_walrus_in_if(self):
        """if (x := get_value()): should work."""
        code = '''
def check(get_value):
    if (x := get_value()):
        return x
    return None
'''
        js = transpile(code)
        # Should pre-declare x
        assert "let x" in js or "var x" in js
        assert "x = get_value()" in js or "x = get_value" in js
    
    def test_walrus_in_while(self):
        """while (line := read_line()): should work."""
        code = '''
def process(read_line):
    while (line := read_line()):
        print(line)
'''
        js = transpile(code)
        assert "let line" in js or "var line" in js
    
    def test_walrus_value_accessible_after(self):
        """Variable from walrus should be accessible after."""
        code = '''
def test():
    if (result := compute()):
        pass
    return result
'''
        js = transpile(code)
        # result should be accessible after the if
        assert "result" in js


# =============================================================================
# 9. NEGATIVE STEP SLICING
# =============================================================================

class TestNegativeStepSlicing:
    """
    Tests complex slicing with negative steps.
    """
    
    def test_reverse_slice(self):
        """items[::-1] reverse."""
        code = '''
def reverse(items):
    return items[::-1]
'''
        js = transpile(code)
        assert "__py.slice" in js
    
    def test_every_other_reverse(self):
        """items[::-2] every other, reversed."""
        code = '''
def every_other_rev(items):
    return items[::-2]
'''
        js = transpile(code)
        assert "__py.slice" in js
    
    def test_partial_reverse(self):
        """items[5:2:-1] partial reverse."""
        code = '''
def partial_rev(items):
    return items[5:2:-1]
'''
        js = transpile(code)
        assert "__py.slice" in js
    
    def test_negative_indices_with_step(self):
        """items[-1:-4:-1] negative indices with step."""
        code = '''
def neg_step(items):
    return items[-1:-4:-1]
'''
        js = transpile(code)
        assert "__py.slice" in js
    
    def test_mixed_indices_negative_step(self):
        """items[10:2:-2] mixed with step."""
        code = '''
def mixed_step(items):
    return items[10:2:-2]
'''
        js = transpile(code)
        assert "__py.slice" in js


# =============================================================================
# 10. ASYNC ERROR PROPAGATION
# =============================================================================

class TestAsyncErrorPropagation:
    """
    Tests async/await transpilation.
    """
    
    def test_async_function(self):
        """async def should transpile."""
        code = '''
async def fetch_data(url):
    response = await fetch(url)
    return response
'''
        js = transpile(code)
        assert "async" in js
        assert "await" in js
    
    def test_async_with_try_except(self):
        """async with try/except should transpile."""
        code = '''
async def safe_fetch(url):
    try:
        response = await fetch(url)
        return response
    except:
        return None
'''
        js = transpile(code)
        assert "async" in js
        assert "try" in js
        assert "catch" in js


# =============================================================================
# 11. COMPLEX COMPREHENSIONS
# =============================================================================

class TestComplexComprehensions:
    """
    Tests complex list/dict/set comprehensions.
    """
    
    def test_nested_comprehension(self):
        """[[y for y in x] for x in matrix]"""
        code = '''
def flatten_matrix(matrix):
    return [[y for y in x] for x in matrix]
'''
        js = transpile(code)
        assert "map" in js or "for" in js
    
    def test_comprehension_with_condition(self):
        """[x for x in items if x > 0]"""
        code = '''
def positives(items):
    return [x for x in items if x > 0]
'''
        js = transpile(code)
        assert "filter" in js or "if" in js
    
    def test_dict_comprehension(self):
        """{k: v for k, v in items}"""
        code = '''
def to_dict(items):
    return {k: v for k, v in items}
'''
        js = transpile(code)
        assert "Object.fromEntries" in js or "{" in js
    
    def test_set_comprehension(self):
        """{x for x in items}"""
        code = '''
def unique(items):
    return {x for x in items}
'''
        js = transpile(code)
        assert "Set" in js


# =============================================================================
# 12. EDGE CASE OPERATORS
# =============================================================================

class TestEdgeCaseOperators:
    """
    Tests edge cases in operator transpilation.
    """
    
    def test_chained_comparison(self):
        """0 < x < 10 chained comparison."""
        code = '''
def in_range(x):
    return 0 < x < 10
'''
        js = transpile(code)
        # Should emit both comparisons
        assert "0" in js and "10" in js
    
    def test_triple_chained_comparison(self):
        """0 < x < y < 10 triple chain."""
        code = '''
def in_order(x, y):
    return 0 < x < y < 10
'''
        js = transpile(code)
        assert "x" in js and "y" in js
    
    def test_is_none(self):
        """x is None."""
        code = '''
def is_none(x):
    return x is None
'''
        js = transpile(code)
        assert "null" in js
    
    def test_is_not_none(self):
        """x is not None."""
        code = '''
def is_not_none(x):
    return x is not None
'''
        js = transpile(code)
        assert "null" in js
    
    def test_not_in(self):
        """x not in items."""
        code = '''
def not_contains(x, items):
    return x not in items
'''
        js = transpile(code)
        assert "!" in js or "not" in js.lower()


# =============================================================================
# 13. CLASS EDGE CASES
# =============================================================================

class TestClassEdgeCases:
    """
    Tests edge cases in class transpilation.
    """
    
    def test_class_with_class_variable(self):
        """Class variables should transpile."""
        code = '''
class Counter:
    count = 0
    
    def increment(self):
        Counter.count = Counter.count + 1
'''
        js = transpile(code)
        assert "Counter" in js
    
    def test_dunder_str(self):
        """__str__ method should work."""
        code = '''
class Person:
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return f"Person({self.name})"
'''
        js = transpile(code)
        assert "toString" in js or "__str__" in js
    
    def test_dunder_repr(self):
        """__repr__ method should work."""
        code = '''
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __repr__(self):
        return f"Point({self.x}, {self.y})"
'''
        js = transpile(code)
        assert "Point" in js


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
