"""
Test Integration - Multi-Feature Combinations

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Integration tests that combine multiple transpiler features together.
These represent realistic code patterns found in actual applications.

Covers:
- Event handlers with form validation
- Data processing pipelines
- Conditional logic with loops
- Nested data structure manipulation
- Signal operations (PyNext specific)
"""

import pytest
from pynext.transpiler import transpile, transpile_handler, TranspileError
from tests.unit.transpiler.test_utils import assert_has_assignment_with_operation


# =============================================================================
# EVENT HANDLERS
# =============================================================================

class TestEventHandlers:
    """Test complete event handler patterns."""
    
    def test_click_counter(self):
        """Simple click counter handler."""
        code = '''
def handle_click():
    count.set(count() + 1)
'''
        result = transpile(code)
        assert "function handle_click()" in result
        assert "count.set" in result
    
    def test_toggle_handler(self):
        """Toggle boolean state."""
        code = '''
def toggle_menu():
    is_open.set(not is_open())
'''
        result = transpile(code)
        assert "function toggle_menu()" in result
        assert "__py.bool" in result or "!" in result
    
    def test_form_validation(self):
        """Form validation handler - uses __py.bool for method call result."""
        code = '''
def handle_submit():
    if form.validate():
        submit_data(form.values)
        show_success.set(True)
    else:
        show_errors.set(True)
'''
        result = transpile(code)
        assert "function handle_submit()" in result
        # Method calls use __py.bool because result could be empty list/dict
        assert "__py.bool(form.validate())" in result
        assert "} else {" in result
    
    def test_add_item_handler(self):
        """Add item to list handler."""
        code = '''
def add_item():
    if input_value():
        items.set([*items(), input_value()])
        input_value.set("")
'''
        result = transpile(code)
        assert "function add_item()" in result
        assert "items.set" in result
    
    def test_remove_item_handler(self):
        """Remove item from list handler - uses index-based loop."""
        code = '''
def remove_item(index):
    new_items = []
    for i in range(len(items())):
        if i != index:
            new_items.append(items()[i])
    items.set(new_items)
'''
        # Using range loop since tuple unpacking in for not yet supported
        result = transpile(code)
        assert "function remove_item(index)" in result


# =============================================================================
# DATA PROCESSING
# =============================================================================

class TestDataProcessing:
    """Test data processing patterns."""
    
    def test_filter_and_map(self):
        """Filter then map pattern."""
        code = '''
def process_data(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result
'''
        result = transpile(code)
        assert "function process_data(items)" in result
        assert "for (const item of __py.iter(items))" in result
        assert "item > 0" in result  # May have extra parens
        assert "push" in result or "append" in result
        assert "return result" in result
    
    def test_find_first(self):
        """Find first matching item."""
        code = '''
def find_first(items, value):
    for item in items:
        if item == value:
            return item
    return None
'''
        result = transpile(code)
        assert "function find_first(items, value)" in result
        assert "return item" in result
        assert "return null" in result
    
    def test_count_occurrences(self):
        """Count occurrences pattern."""
        code = '''
def count_matches(items, target):
    count = 0
    for item in items:
        if item == target:
            count += 1
    return count
'''
        result = transpile(code)
        assert "function count_matches" in result
        assert "let count = 0" in result
        assert_has_assignment_with_operation(result, "count", "add")


# =============================================================================
# CONDITIONAL LOGIC
# =============================================================================

class TestConditionalLogic:
    """Test conditional logic patterns."""
    
    def test_early_return(self):
        """Guard clause pattern."""
        code = '''
def validate(value):
    if value is None:
        return False
    if value < 0:
        return False
    if value > 100:
        return False
    return True
'''
        result = transpile(code)
        assert "return false" in result.lower()
        assert "return true" in result.lower()
    
    def test_nested_conditions(self):
        """Nested if-else pattern."""
        code = '''
def categorize(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    else:
        return "F"
'''
        result = transpile(code)
        assert result.count('return "') == 4
    
    def test_complex_boolean(self):
        """Complex boolean expression."""
        code = '''
def is_valid(x, y, z):
    return (x > 0 and y > 0) or (z > 0 and not (x < 0 or y < 0))
'''
        result = transpile(code)
        assert "return" in result


# =============================================================================
# LOOPS WITH STATE
# =============================================================================

class TestLoopsWithState:
    """Test loops with state management."""
    
    def test_accumulator(self):
        """Accumulator pattern."""
        code = '''
def sum_list(items):
    total = 0
    for item in items:
        total += item
    return total
'''
        result = transpile(code)
        assert "let total = 0" in result
        assert_has_assignment_with_operation(result, "total", "add")
        assert "return total" in result
    
    def test_find_max(self):
        """Find maximum value."""
        code = '''
def find_max(items):
    if len(items) == 0:
        return None
    max_val = items[0]
    for item in items:
        if item > max_val:
            max_val = item
    return max_val
'''
        result = transpile(code)
        assert "items.length" in result or "__py.len(items)" in result
        assert "return max_val" in result
    
    def test_range_loop(self):
        """Range-based loop."""
        code = '''
def factorial(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
'''
        result = transpile(code)
        assert "for (let i = 1" in result
        assert_has_assignment_with_operation(result, "result", "mul")


# =============================================================================
# NESTED STRUCTURES
# =============================================================================

class TestNestedStructures:
    """Test nested data structure operations."""
    
    def test_matrix_traversal(self):
        """Traverse 2D matrix."""
        code = '''
def sum_matrix(matrix):
    total = 0
    for row in matrix:
        for cell in row:
            total += cell
    return total
'''
        result = transpile(code)
        assert result.count("for (const") == 2
        assert_has_assignment_with_operation(result, "total", "add")
    
    def test_nested_dict_access(self):
        """Access nested dictionary."""
        code = '''
def get_value(data):
    return data["outer"]["inner"]["value"]
'''
        result = transpile(code)
        assert '"outer"' in result
        assert '"inner"' in result
        assert '"value"' in result


# =============================================================================
# REAL-WORLD PATTERNS
# =============================================================================

class TestRealWorldPatterns:
    """Test patterns from real applications."""
    
    def test_modal_toggle(self):
        """Modal visibility toggle."""
        code = '''
def open_modal():
    is_modal_open.set(True)
    
def close_modal():
    is_modal_open.set(False)
    form.reset()
'''
        result = transpile(code)
        assert "function open_modal()" in result
        assert "function close_modal()" in result
        assert "is_modal_open.set(true)" in result
        assert "is_modal_open.set(false)" in result
    
    def test_search_filter(self):
        """Search/filter implementation."""
        code = '''
def filter_items():
    query = search_query().lower()
    if not query:
        filtered.set(all_items())
        return
    
    results = []
    for item in all_items():
        if query in item.name.lower():
            results.append(item)
    filtered.set(results)
'''
        result = transpile(code)
        assert "function filter_items()" in result
        assert "toLowerCase()" in result
        assert "for (const item of" in result


# =============================================================================
# ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """Test transpilation error handling."""
    
    def test_yield_supported(self):
        """yield is now supported (Phase 33.2)."""
        result = transpile("def gen(): yield 1")
        assert "yield" in result or "function*" in result
    
    def test_with_supported(self):
        """with statement is now supported (Phase 33.2)."""
        result = transpile("with open('f') as f: pass")
        assert "try" in result or "finally" in result
    
    def test_syntax_error_propagates(self):
        """Python syntax errors are caught."""
        with pytest.raises(TranspileError):
            transpile("def (bad syntax")


# =============================================================================
# TRANSPILE_HANDLER
# =============================================================================

class TestTranspileHandler:
    """Test transpile_handler function."""
    
    def test_full_handler(self):
        """Full function output."""
        result = transpile_handler('''
def handle_click():
    count.set(count() + 1)
''', extract_body=False)
        assert "function handle_click()" in result
    
    def test_body_only(self):
        """Body extraction."""
        result = transpile_handler('''
def handle_click():
    count.set(count() + 1)
''', extract_body=True)
        assert "function" not in result
        assert "count.set" in result
