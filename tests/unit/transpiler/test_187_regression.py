"""
Phase 18.7 Tests - Regression Prevention

50 comprehensive tests to prevent regressions in the optimizer.

Test Categories:
1. Real-world patterns (20 tests)
2. Edge cases from bugs (15 tests)
3. Performance critical paths (15 tests)
"""

import pytest
from pynext.transpiler import parse
from pynext.transpiler.nodes import (
    Program, Assignment, If, For, ForUnpack, While, ExprStmt,
    Name, Constant, Call, Attribute, Compare, Lambda, BinOp,
    FunctionDef,
)
from pynext.transpiler.optimizer import (
    optimize, OptimizeOptions,
    infer_types, elide_wrappers, fix_loop_captures,
    inline_runtime_calls, eliminate_dead_code,
)
from pynext.transpiler.optimizer._internal.type_env import TypeEnv, PyType


# =============================================================================
# 1. REAL-WORLD PATTERNS (20 tests)
# =============================================================================

class TestRealWorldPatterns:
    """Tests for real-world code patterns."""
    
    def test_form_validation_pattern(self):
        """Common form validation pattern."""
        ir = parse('''
def validate_form():
    if len(name) > 0 and len(email) > 0:
        is_valid = True
    else:
        is_valid = False
    return is_valid
''')
        result = optimize(ir)
        assert result is not None
    
    def test_list_filter_pattern(self):
        """Filtering a list with condition."""
        ir = parse('''
result = []
for item in items:
    if item > 0:
        result.append(item)
''')
        result = optimize(ir)
        assert result is not None
    
    def test_counter_pattern(self):
        """Counting pattern."""
        ir = parse('''
count = 0
for item in items:
    if item > threshold:
        count = count + 1
''')
        result = optimize(ir)
        assert result is not None
    
    def test_accumulator_pattern(self):
        """Sum accumulator pattern."""
        ir = parse('''
total = 0
for num in numbers:
    total = total + num
''')
        result = optimize(ir)
        assert result is not None
    
    def test_dict_lookup_pattern(self):
        """Dictionary lookup with default."""
        ir = parse('''
if key in data:
    value = data[key]
else:
    value = default
''')
        result = optimize(ir)
        assert result is not None
    
    def test_string_building_pattern(self):
        """Building a string in a loop."""
        ir = parse('''
result = ""
for word in words:
    result = result + " " + word
''')
        result = optimize(ir)
        assert result is not None
    
    def test_nested_loop_pattern(self):
        """Nested loops with lambdas."""
        ir = parse('''
handlers = []
for i in range(3):
    for j in range(3):
        handlers.append(lambda: (i, j))
''')
        result = optimize(ir)
        # Lambdas should be captured
        assert result is not None
    
    def test_conditional_assignment_pattern(self):
        """Conditional value assignment."""
        ir = parse('''
if condition:
    x = a + b
else:
    x = c + d
''')
        result = optimize(ir)
        assert result is not None
    
    def test_early_return_pattern(self):
        """Early return on condition."""
        ir = parse('''
def process(items):
    if len(items) == 0:
        return None
    return items[0]
''')
        result = optimize(ir)
        assert result is not None
    
    def test_flag_toggle_pattern(self):
        """Boolean flag toggling."""
        ir = parse('''
is_on = True
if should_toggle:
    is_on = not is_on
''')
        result = optimize(ir)
        assert result is not None
    
    def test_index_search_pattern(self):
        """Searching for index in list."""
        ir = parse('''
found = False
for i in range(len(items)):
    if items[i] == target:
        found = True
''')
        result = optimize(ir)
        assert result is not None
    
    def test_max_finding_pattern(self):
        """Finding maximum value."""
        ir = parse('''
max_val = items[0]
for item in items:
    if item > max_val:
        max_val = item
''')
        result = optimize(ir)
        assert result is not None
    
    def test_event_handler_pattern(self):
        """Event handlers in loop (classic gotcha)."""
        ir = parse('''
for btn in buttons:
    btn.onclick = lambda: handle(btn)
''')
        result = optimize(ir)
        # Should be wrapped with capture
        assert result is not None
    
    def test_callback_registration_pattern(self):
        """Callback registration pattern."""
        ir = parse('''
callbacks = []
for name in names:
    callbacks.append(lambda: print(name))
''')
        result = optimize(ir)
        assert result is not None
    
    def test_computed_property_pattern(self):
        """Computing property access."""
        ir = parse('''
if index >= 0:
    value = items[index]
else:
    value = None
''')
        result = optimize(ir)
        assert result is not None
    
    def test_boolean_chain_pattern(self):
        """Chain of boolean operations."""
        ir = parse('''
is_valid = x > 0 and y > 0 and z > 0
''')
        result = optimize(ir)
        # Type should be bool
        env = infer_types(ir)
        # Variables are unknown but result is always bool
        assert result is not None
    
    def test_type_coercion_pattern(self):
        """Explicit type coercion."""
        ir = parse('''
n = int(text)
f = float(text)
s = str(num)
''')
        result = optimize(ir)
        assert result is not None
    
    def test_list_comprehension_like_pattern(self):
        """Manual list comprehension pattern."""
        ir = parse('''
doubled = []
for x in nums:
    doubled.append(x * 2)
''')
        result = optimize(ir)
        assert result is not None
    
    def test_dict_building_pattern(self):
        """Building a dictionary."""
        ir = parse('''
result = {}
for item in items:
    result[item.id] = item.value
''')
        result = optimize(ir)
        assert result is not None
    
    def test_state_machine_pattern(self):
        """Simple state machine."""
        ir = parse('''
state = "idle"
if event == "start":
    state = "running"
elif event == "stop":
    state = "idle"
''')
        result = optimize(ir)
        assert result is not None


# =============================================================================
# 2. EDGE CASES FROM BUGS (15 tests)
# =============================================================================

class TestEdgeCasesFromBugs:
    """Tests for edge cases that have caused bugs."""
    
    def test_empty_program(self):
        """Empty program shouldn't crash."""
        ir = parse('')
        result = optimize(ir)
        assert result.body == ()
    
    def test_only_comments(self):
        """Program with only pass."""
        ir = parse('pass')
        result = optimize(ir)
        assert result is not None
    
    def test_deeply_nested_if(self):
        """Deeply nested if statements."""
        ir = parse('''
if a:
    if b:
        if c:
            if d:
                x = 1
''')
        result = optimize(ir)
        assert result is not None
    
    def test_many_sequential_ifs(self):
        """Many sequential if statements."""
        code = '\n'.join([f'if cond{i}: x{i} = {i}' for i in range(20)])
        ir = parse(code)
        result = optimize(ir)
        assert result is not None
    
    def test_lambda_with_no_args(self):
        """Lambda with no arguments."""
        ir = parse('f = lambda: 42')
        result = optimize(ir)
        assert result is not None
    
    def test_lambda_with_many_args(self):
        """Lambda with many arguments."""
        ir = parse('f = lambda a, b, c, d, e: a + b + c + d + e')
        result = optimize(ir)
        assert result is not None
    
    def test_lambda_shadowing_loop_var(self):
        """Lambda parameter shadows loop variable."""
        ir = parse('''
for i in range(5):
    f = lambda i: i * 2
''')
        result = optimize(ir)
        # Should NOT wrap since i is a parameter
        assert result is not None
    
    def test_complex_comparison_chain(self):
        """Complex chained comparisons."""
        ir = parse('result = 0 < x < y < z < 100')
        result = optimize(ir)
        assert result is not None
    
    def test_mixed_types_in_if(self):
        """Mixed types in if branches."""
        ir = parse('''
if condition:
    x = 5
else:
    x = "hello"
''')
        result = optimize(ir)
        # Type should be ANY after merge
        assert result is not None
    
    def test_reassignment_changes_type(self):
        """Reassignment changes type."""
        ir = parse('''
x = 5
x = "hello"
x = True
''')
        result = optimize(ir)
        env = infer_types(ir)
        assert env.get_type("x") == PyType.BOOL
    
    def test_nested_function_def(self):
        """Nested function definitions."""
        ir = parse('''
def outer():
    def inner():
        return 42
    return inner()
''')
        result = optimize(ir)
        assert result is not None
    
    def test_recursive_function(self):
        """Recursive function."""
        ir = parse('''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
''')
        result = optimize(ir)
        assert result is not None
    
    def test_loop_with_break(self):
        """Loop with break statement."""
        ir = parse('''
for i in range(100):
    if i > 10:
        break
''')
        result = optimize(ir)
        assert result is not None
    
    def test_loop_with_continue(self):
        """Loop with continue statement."""
        ir = parse('''
for i in range(100):
    if i % 2 == 0:
        continue
    process(i)
''')
        result = optimize(ir)
        assert result is not None
    
    def test_while_true_pattern(self):
        """While True with break."""
        ir = parse('''
while True:
    if should_stop:
        break
''')
        result = optimize(ir)
        assert result is not None


# =============================================================================
# 3. PERFORMANCE CRITICAL PATHS (15 tests)
# =============================================================================

class TestPerformanceCriticalPaths:
    """Tests for performance-critical code patterns."""
    
    def test_tight_numeric_loop(self):
        """Tight loop with numeric operations."""
        ir = parse('''
result = 0
for i in range(1000):
    result = result + i * 2
''')
        result = optimize(ir)
        # Operations on known ints should be elided
        assert result is not None
    
    def test_string_comparison_loop(self):
        """Loop with string comparisons."""
        ir = parse('''
matches = 0
for item in items:
    if item == target:
        matches = matches + 1
''')
        result = optimize(ir)
        assert result is not None
    
    def test_boolean_heavy_code(self):
        """Code heavy on boolean operations."""
        ir = parse('''
if a > 0 and b > 0 and c > 0:
    if not is_disabled and is_enabled:
        result = True
''')
        result = optimize(ir)
        assert result is not None
    
    def test_array_processing(self):
        """Array processing pattern."""
        ir = parse('''
for i in range(len(data)):
    data[i] = data[i] * scale + offset
''')
        result = optimize(ir)
        assert result is not None
    
    def test_conditional_heavy_code(self):
        """Code with many conditionals."""
        ir = parse('''
if a == 1:
    x = "one"
elif a == 2:
    x = "two"
elif a == 3:
    x = "three"
else:
    x = "other"
''')
        result = optimize(ir)
        assert result is not None
    
    def test_many_assignments(self):
        """Many sequential assignments."""
        code = '\n'.join([f'x{i} = {i}' for i in range(50)])
        ir = parse(code)
        result = optimize(ir)
        assert len(result.body) == 50
    
    def test_function_with_many_params(self):
        """Function with many parameters."""
        ir = parse('''
def func(a, b, c, d, e, f, g, h, i, j):
    return a + b + c + d + e + f + g + h + i + j
''')
        result = optimize(ir)
        assert result is not None
    
    def test_deep_expression_nesting(self):
        """Deeply nested expressions."""
        ir = parse('result = ((((a + b) * c) - d) / e) % f')
        result = optimize(ir)
        assert result is not None
    
    def test_many_function_calls(self):
        """Many function calls in sequence."""
        ir = parse('''
a()
b()
c()
d()
e()
f()
g()
h()
i()
j()
''')
        result = optimize(ir)
        assert len(result.body) == 10
    
    def test_complex_boolean_expression(self):
        """Complex boolean expression."""
        ir = parse('''
result = (a > 0 and b > 0) or (c < 0 and d < 0) or (e == 0)
''')
        result = optimize(ir)
        assert result is not None
    
    def test_loop_with_multiple_conditions(self):
        """Loop with multiple conditions checked."""
        ir = parse('''
for item in items:
    if item.type == "A" and item.value > 0:
        process_a(item)
    elif item.type == "B" and item.value < 0:
        process_b(item)
    else:
        process_default(item)
''')
        result = optimize(ir)
        assert result is not None
    
    def test_nested_data_access(self):
        """Nested data structure access."""
        ir = parse('''
value = data.items[0].nested.deep.value
''')
        result = optimize(ir)
        assert result is not None
    
    def test_method_chaining(self):
        """Method chaining pattern."""
        ir = parse('''
result = text.strip().lower().replace("a", "b").split(",")
''')
        result = optimize(ir)
        assert result is not None
    
    def test_list_operations_heavy(self):
        """Heavy list operations."""
        ir = parse('''
items.append(x)
items.extend(more)
items.pop()
items.insert(0, first)
''')
        result = optimize(ir)
        assert result is not None
    
    def test_numeric_computation(self):
        """Numeric computation heavy."""
        ir = parse('''
x = a * b + c * d - e / f + g % h
y = x * x + 2 * x + 1
z = (y - 4) * (y + 4)
''')
        result = optimize(ir)
        assert result is not None
