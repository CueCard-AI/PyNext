"""
Test Transpiler Fixes

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests for the risk fixes implemented in Phase 18.1:

1. Scope Tracking (let vs reassignment)
2. Tuple Unpacking in For Loops
3. List Concatenation with +
4. Dict Iteration with __py.iter
5. String/List Repetition with __py.mul
6. Improved Negative Index Detection
"""

import pytest
from pynext.transpiler import transpile, TranspileError
from tests.unit.transpiler.test_utils import assert_has_runtime_function, assert_has_function_call_with_args


# =============================================================================
# SCOPE TRACKING
# =============================================================================

class TestScopeTracking:
    """Test variable scope tracking (let vs reassignment)."""
    
    def test_first_assignment_uses_let(self):
        """First assignment should use let."""
        result = transpile("x = 5")
        assert "let x = 5;" in result
    
    def test_reassignment_no_let(self):
        """Reassignment should not use let."""
        result = transpile("x = 1\nx = 2")
        assert result.count("let x") == 1
        assert "let x = 1;" in result
        assert "\nx = 2;" in result
    
    def test_multiple_reassignments(self):
        """Multiple reassignments."""
        result = transpile("x = 1\nx = 2\nx = 3")
        assert result.count("let x") == 1
        assert "x = 2;" in result
        assert "x = 3;" in result
    
    def test_different_variables(self):
        """Different variables each get let."""
        result = transpile("x = 1\ny = 2\nz = 3")
        assert "let x = 1;" in result
        assert "let y = 2;" in result
        assert "let z = 3;" in result
    
    def test_function_scope_isolation(self):
        """Variables in function have separate scope."""
        result = transpile("x = 1\ndef foo():\n    x = 2")
        # Both should use let (different scopes)
        assert result.count("let x") == 2
    
    def test_parameter_not_redeclared(self):
        """Function parameters shouldn't be redeclared."""
        result = transpile("def foo(x):\n    x = 5")
        # x is a parameter, so assignment inside shouldn't use let
        assert "function foo(x)" in result
        # The reassignment should not have let
        assert "    x = 5;" in result
        assert "let x = 5" not in result


# =============================================================================
# TUPLE UNPACKING IN FOR LOOPS
# =============================================================================

class TestForTupleUnpacking:
    """Test tuple unpacking in for loops."""
    
    def test_enumerate(self):
        """for i, x in enumerate(items)"""
        result = transpile("for i, x in enumerate(items):\n    print(i, x)")
        assert "const [i, x]" in result
        assert "__py.iter" in result
    
    def test_dict_items(self):
        """for k, v in d.items()"""
        result = transpile("for k, v in d.items():\n    print(k, v)")
        assert "const [k, v]" in result
    
    def test_triple_unpack(self):
        """for a, b, c in triples"""
        result = transpile("for a, b, c in triples:\n    pass")
        assert "const [a, b, c]" in result
    
    def test_zip(self):
        """for a, b in zip(x, y)"""
        result = transpile("for a, b in zip(x, y):\n    pass")
        assert "const [a, b]" in result
        assert "__py.zip(x, y)" in result


# =============================================================================
# LIST CONCATENATION
# =============================================================================

class TestListConcatenation:
    """Test list concatenation with + using __py.add."""
    
    def test_variable_addition(self):
        """a + b uses dunder runtime for potential list concat."""
        result = transpile("x = a + b")
        assert_has_runtime_function(result, "add")
    
    def test_list_literal_addition(self):
        """[1,2] + [3,4]"""
        result = transpile("x = [1, 2] + [3, 4]")
        assert_has_runtime_function(result, "add")
    
    def test_numeric_addition_optimized(self):
        """5 + 3 should use plain + (known numbers)."""
        result = transpile("x = 5 + 3")
        assert "(5 + 3)" in result
        assert "__py.add" not in result
    
    def test_subtraction_unchanged(self):
        """a - b uses dunder runtime for unknown types."""
        result = transpile("x = a - b")
        assert_has_runtime_function(result, "sub")


# =============================================================================
# DICT ITERATION
# =============================================================================

class TestDictIteration:
    """Test dict iteration with __py.iter."""
    
    def test_for_in_variable(self):
        """for k in my_dict → uses __py.iter."""
        result = transpile("for k in my_dict:\n    print(k)")
        assert "__py.iter(my_dict)" in result
    
    def test_for_in_dict_keys(self):
        """for k in d.keys() → uses Object.keys directly."""
        result = transpile("for k in d.keys():\n    print(k)")
        assert "Object.keys(d)" in result
    
    def test_for_in_dict_values(self):
        """for v in d.values()"""
        result = transpile("for v in d.values():\n    print(v)")
        assert "Object.values(d)" in result
    
    def test_for_in_dict_items(self):
        """for item in d.items()"""
        result = transpile("for item in d.items():\n    print(item)")
        # Phase 33.2: Uses __py.dict.items() to preserve key types
        assert "__py.dict.items(d)" in result


# =============================================================================
# STRING/LIST REPETITION
# =============================================================================

class TestRepetition:
    """Test string and list repetition with * using __py.mul."""
    
    def test_string_literal_times_int(self):
        """"a" * 3 → uses .repeat() directly."""
        result = transpile('x = "a" * 3')
        assert '"a".repeat(3)' in result
    
    def test_int_times_string_literal(self):
        """3 * "a" → uses .repeat()."""
        result = transpile('x = 3 * "a"')
        assert '"a".repeat(3)' in result
    
    def test_variable_times_int(self):
        """s * 3 → uses dunder runtime (s could be string or list)."""
        result = transpile("x = s * 3")
        assert_has_runtime_function(result, "mul")
    
    def test_numeric_multiplication_optimized(self):
        """5 * 3 should use plain * (known numbers)."""
        result = transpile("x = 5 * 3")
        assert "(5 * 3)" in result
        assert "__py.mul" not in result


# =============================================================================
# NEGATIVE INDEX DETECTION
# =============================================================================

class TestNegativeIndexDetection:
    """Test improved negative index detection."""
    
    def test_positive_literal_no_runtime(self):
        """items[0] → __py.getitem(items, 0) for Phase 33.2 __getitem__ support"""
        result = transpile("x = items[0]")
        assert "__py.getitem(items, 0)" in result
    
    def test_negative_literal_uses_runtime(self):
        """items[-1] uses __py.at."""
        result = transpile("x = items[-1]")
        assert_has_function_call_with_args(result, "at", "items", "-1")
    
    def test_variable_index_uses_runtime(self):
        """items[i] uses __py.at (i could be negative)."""
        result = transpile("x = items[i]")
        assert "__py.at(items, i)" in result
    
    def test_function_call_index_uses_runtime(self):
        """items[get_index()] uses __py.at."""
        result = transpile("x = items[get_index()]")
        assert "__py.at(items, get_index())" in result
    
    def test_expression_index_uses_runtime(self):
        """items[len(items) - 1] uses __py.at."""
        result = transpile("x = items[len(items) - 1]")
        assert "__py.at" in result


# =============================================================================
# COMBINED SCENARIOS
# =============================================================================

class TestCombinedScenarios:
    """Test combinations of multiple fixes."""
    
    def test_reassignment_in_loop(self):
        """Variable reassigned in loop."""
        code = """
total = 0
for x in items:
    total = total + x
"""
        result = transpile(code)
        assert "let total = 0" in result
        assert_has_runtime_function(result, "add")
        assert result.count("let total") == 1
    
    def test_enumerate_with_accumulator(self):
        """Enumerate with variable reassignment."""
        code = """
result = []
for i, x in enumerate(items):
    result = result + [x * 2]
"""
        result = transpile(code)
        assert "const [i, x]" in result
        assert "let result = []" in result
    
    def test_dict_iteration_with_concat(self):
        """Iterate dict and concatenate."""
        code = """
keys = []
for k in d:
    keys = keys + [k]
"""
        result = transpile(code)
        assert "__py.iter(d)" in result
        assert_has_runtime_function(result, "add")
    
    def test_function_with_scope(self):
        """Function with proper scoping."""
        code = """
x = 1
def process(items):
    result = []
    for i, item in enumerate(items):
        result = result + [item]
    return result
x = 2
"""
        result = transpile(code)
        # x at module level
        assert "let x = 1" in result
        assert "\nx = 2" in result
        # result in function
        assert "let result = []" in result
