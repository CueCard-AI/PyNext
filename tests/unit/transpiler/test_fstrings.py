"""
Test F-Strings

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests for Python f-strings transpiled to JavaScript template literals:
- Simple: f"Hello {name}" → `Hello ${name}`
- With format specs: f"{x:.2f}" → `${__py.format(x, '.2f')}`
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# SIMPLE F-STRINGS
# =============================================================================

class TestSimpleFStrings:
    """Test basic f-strings without format specs."""
    
    def test_single_interpolation(self):
        """f"Hello {name}" """
        result = transpile('x = f"Hello {name}"')
        # Phase 33.2: Uses __py.fstr() for unknown types to handle collections correctly
        assert "__py.fstr(name)" in result or "`Hello ${name}`" in result
    
    def test_multiple_interpolations(self):
        """f"{a} + {b} = {c}" """
        result = transpile('x = f"{a} + {b} = {c}"')
        # Phase 33.2: Variables may be wrapped with __py.fstr() for unknown types
        assert ("${a}" in result or "__py.fstr(a)" in result) and \
               ("${b}" in result or "__py.fstr(b)" in result) and \
               ("${c}" in result or "__py.fstr(c)" in result)
    
    def test_no_interpolation(self):
        """f"Just a string" """
        result = transpile('x = f"Just a string"')
        assert "`Just a string`" in result
    
    def test_interpolation_at_start(self):
        """f"{name} is here" """
        result = transpile('x = f"{name} is here"')
        # Phase 33.2: Variables may be wrapped with __py.fstr() for unknown types
        assert "${name}" in result or "__py.fstr(name)" in result
    
    def test_interpolation_at_end(self):
        """f"Hello {name}" """
        result = transpile('x = f"Hello {name}"')
        # Phase 33.2: Variables may be wrapped with __py.fstr() for unknown types
        assert "${name}" in result or "__py.fstr(name)" in result
    
    def test_only_interpolation(self):
        """f"{value}" """
        result = transpile('x = f"{value}"')
        # Phase 33.2: Variables may be wrapped with __py.fstr() for unknown types
        assert "${value}" in result or "__py.fstr(value)" in result
    
    def test_adjacent_interpolations(self):
        """f"{a}{b}" """
        result = transpile('x = f"{a}{b}"')
        # Phase 33.2: Variables may be wrapped with __py.fstr() for unknown types
        assert ("${a}${b}" in result or "${a}" in result and "${b}" in result) or \
               ("__py.fstr(a)" in result and "__py.fstr(b)" in result)


# =============================================================================
# WITH EXPRESSIONS
# =============================================================================

class TestWithExpressions:
    """Test f-strings with expressions."""
    
    def test_arithmetic(self):
        """f"{x + 1}" """
        result = transpile('x = f"{a + 1}"')
        assert "${" in result
    
    def test_comparison(self):
        """f"{x > 0}" """
        result = transpile('x = f"{a > 0}"')
        assert "${" in result
    
    def test_function_call(self):
        """f"{len(items)}" """
        result = transpile('x = f"{len(items)}"')
        assert "${" in result
    
    def test_method_call(self):
        """f"{name.upper()}" → toUpperCase() in JS"""
        result = transpile('x = f"{name.upper()}"')
        # Python .upper() becomes JS .toUpperCase()
        assert "name.toUpperCase()" in result or "name.upper()" in result
    
    def test_attribute(self):
        """f"{user.name}" """
        result = transpile('x = f"{user.name}"')
        assert "user.name" in result
    
    def test_subscript(self):
        """f"{items[0]}" """
        result = transpile('x = f"{items[0]}"')
        # Phase 33.2: Uses __py.getitem() for __getitem__ dunder support
        assert "__py.getitem(items, 0)" in result
    
    def test_ternary(self):
        """f"{a if cond else b}" """
        result = transpile('x = f"{a if cond else b}"')
        assert "${" in result


# =============================================================================
# FORMAT SPECS
# =============================================================================

class TestFormatSpecs:
    """Test f-strings with format specifications."""
    
    def test_float_precision(self):
        """f"{x:.2f}" """
        result = transpile('x = f"{value:.2f}"')
        assert "__py.format(value, '.2f')" in result
    
    def test_float_precision_1(self):
        """f"{x:.1f}" """
        result = transpile('x = f"{value:.1f}"')
        assert "__py.format(value, '.1f')" in result
    
    def test_thousands_separator(self):
        """f"{x:,}" """
        result = transpile('x = f"{value:,}"')
        assert "__py.format(value, ',')" in result
    
    def test_right_align(self):
        """f"{x:>10}" """
        result = transpile('x = f"{value:>10}"')
        assert "__py.format(value, '>10')" in result
    
    def test_left_align(self):
        """f"{x:<10}" """
        result = transpile('x = f"{value:<10}"')
        assert "__py.format(value, '<10')" in result
    
    def test_center_align(self):
        """f"{x:^10}" """
        result = transpile('x = f"{value:^10}"')
        assert "__py.format(value, '^10')" in result
    
    def test_zero_padding(self):
        """f"{x:05d}" """
        result = transpile('x = f"{value:05d}"')
        assert "__py.format(value, '05d')" in result
    
    def test_percentage(self):
        """f"{x:.1%}" """
        result = transpile('x = f"{value:.1%}"')
        assert "__py.format(value, '.1%')" in result
    
    def test_hex(self):
        """f"{x:x}" """
        result = transpile('x = f"{value:x}"')
        assert "__py.format(value, 'x')" in result
    
    def test_binary(self):
        """f"{x:b}" """
        result = transpile('x = f"{value:b}"')
        assert "__py.format(value, 'b')" in result


# =============================================================================
# MIXED CONTENT
# =============================================================================

class TestMixedContent:
    """Test f-strings with mixed format specs."""
    
    def test_mixed_with_and_without_spec(self):
        """f"{name}: {value:.2f}" """
        result = transpile('x = f"{name}: {value:.2f}"')
        # Phase 33.2: Variables may be wrapped with __py.fstr() for unknown types (when no format spec)
        assert ("${name}" in result or "__py.fstr(name)" in result)
        assert "__py.format(value, '.2f')" in result
    
    def test_multiple_format_specs(self):
        """f"{a:.2f} and {b:,}" """
        result = transpile('x = f"{a:.2f} and {b:,}"')
        assert "__py.format(a, '.2f')" in result
        assert "__py.format(b, ',')" in result


# =============================================================================
# SPECIAL CHARACTERS
# =============================================================================

class TestSpecialCharacters:
    """Test f-strings with special characters."""
    
    def test_newline_in_string(self):
        """f"Line 1\\nLine 2" """
        result = transpile('x = f"Line 1\\nLine 2"')
        assert "`" in result
    
    def test_quotes_in_string(self):
        """f"He said 'hi'" """
        result = transpile("x = f\"He said 'hi'\"")
        assert "hi" in result
    
    def test_curly_braces_escaped(self):
        """f"{{not interpolation}}" - becomes literal braces"""
        # Python's {{ becomes { in output
        result = transpile('x = f"{{literal}}"')
        # The {{ escapes are handled by Python parser
        assert "`" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestFStringEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_fstring(self):
        """f"" """
        result = transpile('x = f""')
        assert "``" in result
    
    def test_nested_quotes(self):
        """f'{x["key"]}' """
        result = transpile("x = f'{y[\"key\"]}'")
        assert "`" in result
    
    def test_in_function_call(self):
        """print(f"Hello {name}")"""
        result = transpile('print(f"Hello {name}")')
        # Phase 33.2: Unknown types (PyType.ANY) are wrapped with __py.fstr() for safety
        assert "`Hello ${name}`" in result or "__py.fstr(name)" in result
    
    def test_in_list(self):
        """[f"{x}" for x in items]"""
        result = transpile('[f"{x}" for x in items]')
        assert "`${" in result
    
    def test_in_dict_value(self):
        """{"key": f"{value}"}"""
        result = transpile('x = {"key": f"{value}"}')
        # Phase 33.2: Unknown types (PyType.ANY) are wrapped with __py.fstr() for safety
        assert "`${value}`" in result or "__py.fstr(value)" in result


# =============================================================================
# REAL-WORLD PATTERNS
# =============================================================================

class TestRealWorldPatterns:
    """Test common real-world f-string patterns."""
    
    def test_log_message(self):
        """f"User {user.name} logged in at {timestamp}" """
        result = transpile('msg = f"User {user.name} logged in"')
        assert "${user.name}" in result
    
    def test_error_message(self):
        """f"Error: {error.message}" """
        result = transpile('msg = f"Error: {error.message}"')
        assert "${error.message}" in result
    
    def test_url_building(self):
        """f"/api/users/{user_id}" """
        result = transpile('url = f"/api/users/{user_id}"')
        # Phase 33.2: Unknown types (PyType.ANY) are wrapped with __py.fstr() for safety
        # This ensures collections are handled correctly, even if it's conservative for primitives
        assert "${user_id}" in result or "__py.fstr(user_id)" in result
    
    def test_css_value(self):
        """f"{width}px" """
        result = transpile('style = f"{width}px"')
        # Phase 33.2: Unknown types (PyType.ANY) are wrapped with __py.fstr() for safety
        # This ensures collections are handled correctly, even if it's conservative for primitives
        assert "${width}" in result or "__py.fstr(width)" in result
    
    def test_money_format(self):
        """f"${amount:,.2f}" - note: $ is literal, not interpolation"""
        result = transpile('price = f"${amount:.2f}"')
        # The $ before { is tricky - should not confuse with JS interpolation
        assert "__py.format(amount, '.2f')" in result
    
    def test_percentage_display(self):
        """f"{percent:.1%}" """
        result = transpile('display = f"{percent:.1%}"')
        assert "__py.format(percent, '.1%')" in result


# =============================================================================
# IN HANDLERS
# =============================================================================

class TestInHandlers:
    """Test f-strings in event handlers."""
    
    def test_in_function(self):
        """def greet(): return f"Hello {name}" """
        code = """
def greet():
    return f"Hello {name}"
"""
        result = transpile(code)
        # Phase 33.2: Unknown types (PyType.ANY) are wrapped with __py.fstr() for safety
        assert "`Hello ${name}`" in result or "__py.fstr(name)" in result
    
    def test_in_conditional(self):
        """if x: msg = f"{x}" """
        code = """
if x:
    msg = f"Value: {x}"
"""
        result = transpile(code)
        # Phase 33.2: Unknown types (PyType.ANY) are wrapped with __py.fstr() for safety
        assert "`Value: ${x}`" in result or "__py.fstr(x)" in result
    
    def test_in_loop(self):
        """for x in items: print(f"{x}")"""
        code = """
for x in items:
    print(f"Item: {x}")
"""
        result = transpile(code)
        # Phase 33.2: Unknown types (PyType.ANY) are wrapped with __py.fstr() for safety
        assert "`Item: ${x}`" in result or "__py.fstr(x)" in result
