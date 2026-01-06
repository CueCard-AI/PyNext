"""
Phase 18.7 - Stress Tests with Real-World Patterns

Tests with realistic code patterns to ensure optimizer handles real-world use cases.
"""

import pytest
from pynext.transpiler import parse
from pynext.transpiler.optimizer import optimize, get_optimization_stats


# =============================================================================
# 1. REALISTIC APPLICATION PATTERNS
# =============================================================================

class TestRealisticPatterns:
    """Tests based on realistic application code."""
    
    def test_form_validation(self):
        """Form validation pattern."""
        code = '''
def validate_form(name, email, password):
    errors = []
    if len(name) < 2:
        errors.append("Name too short")
    if "@" not in email:
        errors.append("Invalid email")
    if len(password) < 8:
        errors.append("Password too short")
    return len(errors) == 0
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
        assert len(optimized.body) > 0
    
    def test_list_filter_map(self):
        """Filter and map pattern."""
        code = '''
result = []
for item in items:
    if item.active:
        result.append(item.name.upper())
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_counter_aggregation(self):
        """Counter/aggregation pattern."""
        code = '''
counts = {}
for item in items:
    key = item.category
    if key not in counts:
        counts[key] = 0
    counts[key] = counts[key] + 1
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_event_handler_registration(self):
        """Event handler registration - the classic gotcha."""
        code = '''
handlers = []
for btn in buttons:
    handlers.append(btn.id)
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_api_response_processing(self):
        """API response processing pattern."""
        code = '''
def process_response(response):
    if response.status == 200:
        data = response.json()
        return data.items
    else:
        return []
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None


# =============================================================================
# 2. COMPLEX CONTROL FLOW
# =============================================================================

class TestComplexControlFlow:
    """Tests with complex control flow."""
    
    def test_state_machine(self):
        """State machine pattern."""
        code = '''
def process_state(state, event):
    if state == "idle":
        if event == "start":
            return "running"
        else:
            return "idle"
    elif state == "running":
        if event == "pause":
            return "paused"
        elif event == "stop":
            return "stopped"
        else:
            return "running"
    else:
        return state
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_early_return(self):
        """Early return pattern."""
        code = '''
def find_first(items, predicate):
    for item in items:
        if predicate(item):
            return item
    return None
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_nested_loops(self):
        """Nested loops pattern."""
        code = '''
result = []
for row in matrix:
    for cell in row:
        if cell > threshold:
            result.append(cell)
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None


# =============================================================================
# 3. DATA TRANSFORMATION
# =============================================================================

class TestDataTransformation:
    """Tests with data transformation patterns."""
    
    def test_list_to_dict(self):
        """List to dictionary conversion."""
        code = '''
result = {}
for item in items:
    result[item.id] = item.value
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_grouping(self):
        """Grouping pattern."""
        code = '''
groups = {}
for item in items:
    key = item.category
    if key not in groups:
        groups[key] = []
    groups[key].append(item)
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_string_building(self):
        """String building pattern."""
        code = '''
result = ""
for word in words:
    if len(result) > 0:
        result = result + " "
    result = result + word
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None


# =============================================================================
# 4. SCALE TESTS
# =============================================================================

class TestScaleTests:
    """Tests at scale to ensure optimizer handles large code."""
    
    def test_many_variables(self):
        """Many variable declarations."""
        lines = [f"x{i} = {i}" for i in range(100)]
        code = '\n'.join(lines)
        ir = parse(code)
        optimized = optimize(ir)
        assert len(optimized.body) == 100
    
    def test_long_function(self):
        """Long function body."""
        body_lines = [f"    step{i} = step{i-1} + 1" if i > 0 else "    step0 = 0" 
                     for i in range(50)]
        code = "def long_function():\n" + '\n'.join(body_lines)
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_deep_nesting(self):
        """Deeply nested code."""
        code = "x = 0\n"
        for i in range(10):
            code += "    " * i + "if True:\n"
            code += "    " * (i+1) + f"x = x + {i}\n"
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None


# =============================================================================
# 5. EDGE CASES FROM PRODUCTION
# =============================================================================

class TestProductionEdgeCases:
    """Edge cases that might appear in production code."""
    
    def test_empty_collections(self):
        """Empty collection handling."""
        code = '''
if items:
    first = items[0]
else:
    first = None
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_chained_method_calls(self):
        """Method chaining pattern."""
        code = '''
result = text.strip().lower().split(",")
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_conditional_assignment(self):
        """Conditional assignment pattern."""
        code = '''
value = default
if condition:
    value = computed
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_boolean_logic(self):
        """Complex boolean logic."""
        code = '''
is_valid = a > 0 and b > 0 and c > 0
is_special = x == 0 or y == 0
result = is_valid and not is_special
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
    
    def test_numeric_computation(self):
        """Numeric computation."""
        code = '''
x = a * b + c * d
y = x * x - 4 * a * c
z = (y + x) / 2
'''
        ir = parse(code)
        optimized = optimize(ir)
        assert optimized is not None
