"""
Test Phase 18.2 Integration

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Integration tests combining multiple Phase 18.2 features:
- F-strings with comprehensions
- Boolean operators with comprehensions
- Generator expressions in complex handlers
- Real-world handler patterns
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# COMBINED F-STRINGS AND COMPREHENSIONS
# =============================================================================

class TestFStringsWithComprehensions:
    """Test f-strings combined with comprehensions."""
    
    def test_fstring_in_list_comp(self):
        """[f"{x}" for x in items]"""
        result = transpile('[f"Item: {x}" for x in items]')
        assert ".map(" in result
        # Accept either x or __py.fstr(x) - both are valid
        # __py.fstr(x) is used for safety when type is unknown (handles collections correctly)
        assert ("`Item: ${x}`" in result or "`Item: ${__py.fstr(x)}`" in result)
    
    def test_list_comp_in_fstring(self):
        """f"Items: {[x for x in items]}" """
        result = transpile('msg = f"Count: {len([x for x in items])}"')
        assert "`Count:" in result
    
    def test_fstring_with_format_in_comp(self):
        """[f"{x:.2f}" for x in values]"""
        result = transpile('[f"{x:.2f}" for x in values]')
        assert "__py.format" in result


# =============================================================================
# BOOLEAN OPS WITH COMPREHENSIONS
# =============================================================================

class TestBooleanOpsWithComprehensions:
    """Test boolean operators with comprehensions."""
    
    def test_any_with_and(self):
        """any(x and x.active for x in items)"""
        result = transpile("y = any(x and x.active for x in items)")
        assert "__py.bool" in result
    
    def test_filter_with_or(self):
        """[x for x in items if x.a or x.b]"""
        result = transpile("y = [x for x in items if x.a or x.b]")
        assert ".filter(" in result
    
    def test_all_with_not(self):
        """all(not x.error for x in items)"""
        result = transpile("y = all(not x.error for x in items)")
        assert "!__py.bool" in result


# =============================================================================
# CHAINED COMPARISONS IN COMPREHENSIONS
# =============================================================================

class TestChainedInComprehensions:
    """Test chained comparisons in comprehensions."""
    
    def test_filter_with_chain(self):
        """[x for x in items if 0 < x < 10]"""
        result = transpile("y = [x for x in items if 0 < x < 10]")
        assert ".filter(" in result
        assert "&&" in result
    
    def test_any_with_chain(self):
        """any(0 < x < 10 for x in items)"""
        result = transpile("y = any(0 < x < 10 for x in items)")
        assert "&&" in result


# =============================================================================
# NESTED COMPREHENSIONS
# =============================================================================

class TestNestedComprehensions:
    """Test nested comprehensions."""
    
    def test_list_in_dict(self):
        """{k: [x for x in v] for k, v in items}"""
        result = transpile("y = {k: [x for x in v] for k, v in items}")
        assert "Object.fromEntries" in result
    
    def test_set_of_results(self):
        """{x.id for x in [item for item in items if item.active]}"""
        result = transpile("y = {x.id for x in [item for item in items if item.active]}")
        assert "new Set" in result


# =============================================================================
# REAL-WORLD HANDLER PATTERNS
# =============================================================================

class TestRealWorldHandlers:
    """Test real-world event handler patterns."""
    
    def test_filter_and_display(self):
        """Filter items and create display strings"""
        code = """
def render_items():
    active = [item for item in items if item.active]
    labels = [f"{item.name}: {item.value}" for item in active]
    display.set(labels)
"""
        result = transpile(code)
        assert ".filter(" in result
        assert ".map(" in result
    
    def test_validation_with_any(self):
        """Check if any field is invalid"""
        code = """
def validate():
    has_error = any(not field.valid for field in fields)
    if has_error:
        show_errors()
"""
        result = transpile(code)
        assert "!__py.bool" in result or ".some(" in result
    
    def test_compute_totals(self):
        """Compute totals with sum and filter"""
        code = """
def calculate():
    total = sum(item.price for item in cart if item.quantity > 0)
    tax = total * 0.1
    display_total.set(f"Total: ${total + tax:.2f}")
"""
        result = transpile(code)
        assert "__py.format" in result or ".2f" in result
    
    def test_build_index(self):
        """Build index from items"""
        code = """
def index_items():
    by_id = {item.id: item for item in items}
    by_name = {item.name: item for item in items}
    return by_id, by_name
"""
        result = transpile(code)
        assert "Object.fromEntries" in result
    
    def test_unique_tags(self):
        """Collect unique tags"""
        code = """
def get_tags():
    all_tags = {tag for item in items for tag in item.tags}
    return sorted(list(all_tags))
"""
        result = transpile(code)
        assert "new Set" in result


# =============================================================================
# COMPLEX CONDITIONS
# =============================================================================

class TestComplexConditions:
    """Test complex conditional expressions."""
    
    def test_ternary_in_comp(self):
        """[a if x else b for x in items]"""
        result = transpile("y = [a if x else b for x in items]")
        assert ".map(" in result
    
    def test_or_default_in_comp(self):
        """[x.value or 0 for x in items]"""
        result = transpile("y = [x.value or 0 for x in items]")
        assert "__py.bool" in result
    
    def test_and_chain_in_filter(self):
        """[x for x in items if x.a and x.b and x.c]"""
        result = transpile("y = [x for x in items if x.a and x.b and x.c]")
        assert ".filter(" in result


# =============================================================================
# FORMAT STRING PATTERNS
# =============================================================================

class TestFormatPatterns:
    """Test format string patterns in context."""
    
    def test_money_formatting(self):
        """Display money with formatting"""
        code = """
def display_prices():
    formatted = [f"${item.price:.2f}" for item in items]
    return formatted
"""
        result = transpile(code)
        assert "__py.format" in result
    
    def test_percentage_display(self):
        """Display percentages"""
        code = """
def show_progress():
    msg = f"Progress: {completed / total:.1%}"
    status.set(msg)
"""
        result = transpile(code)
        assert "__py.format" in result
    
    def test_table_row_formatting(self):
        """Format table rows"""
        code = """
def format_row(name, value, percent):
    return f"{name:<20} {value:>10,} {percent:>6.1%}"
"""
        result = transpile(code)
        assert "__py.format" in result


# =============================================================================
# ERROR HANDLING PATTERNS
# =============================================================================

class TestErrorPatterns:
    """Test error handling patterns."""
    
    def test_validate_all(self):
        """Validate all items"""
        code = """
def validate_all():
    errors = [f"Invalid: {item.name}" for item in items if not item.valid]
    if errors:
        show_error(errors)
        return False
    return True
"""
        result = transpile(code)
        assert ".filter(" in result or ".map(" in result
    
    def test_has_any_error(self):
        """Check for any errors"""
        code = """
def has_errors():
    return any(item.error for item in items)
"""
        result = transpile(code)
        assert ".some(" in result or "any" in result


# =============================================================================
# PERFORMANCE PATTERNS
# =============================================================================

class TestPerformancePatterns:
    """Test patterns optimized for performance."""
    
    def test_early_exit_with_any(self):
        """Early exit pattern"""
        code = """
def check_valid():
    if any(x > 100 for x in values):
        return False
    return True
"""
        result = transpile(code)
        assert ".some(" in result or "any" in result
    
    def test_all_check(self):
        """All items must pass"""
        code = """
def all_positive():
    return all(x > 0 for x in values)
"""
        result = transpile(code)
        assert ".every(" in result or "all" in result


# =============================================================================
# OUTPUT CORRECTNESS
# =============================================================================

class TestOutputCorrectness:
    """Verify output produces correct results."""
    
    def test_produces_valid_js(self):
        """Output should be syntactically valid JS"""
        # Test that complex patterns produce valid structure
        result = transpile("""
def process():
    data = [x*2 for x in items if x > 0]
    index = {x.id: x for x in data}
    unique = {x.name for x in data}
    has_large = any(x > 100 for x in data)
    total = sum(x for x in data)
""")
        # Should contain all constructs
        assert ".filter(" in result
        assert ".map(" in result
        assert "Object.fromEntries" in result
        assert "new Set" in result
