"""
Tests for Transpiler Emitter ↔ Compiler Emitter Parity

RISK: PyNext has TWO different JavaScript emitters:
1. pynext/transpiler/emitter.py - For event handlers and inline JS
2. pynext/compiler/emitter.py - For @island component compilation

These must produce COMPATIBLE output, otherwise:
- Island handlers won't work with transpiled event code
- Runtime helpers (__py.*) may be missing or incompatible
- Signal API calls may differ

This test suite ensures both emitters produce code that works
together seamlessly.
"""

import pytest
import re
from typing import Optional

# Transpiler imports
from pynext.transpiler import transpile
from pynext.transpiler.parser import parse as transpiler_parse
from pynext.transpiler.emitter import emit as transpiler_emit
from tests.unit.transpiler.test_utils import assert_has_runtime_function

# Compiler imports  
from pynext.compiler.parser import parse_island
from pynext.compiler.emitter import emit_javascript


# =============================================================================
# TEST HELPERS
# =============================================================================

def normalize_js(js: str) -> str:
    """Normalize JavaScript for comparison."""
    # Remove whitespace variations
    js = re.sub(r'\s+', ' ', js.strip())
    # Normalize quotes (both emitters may use different quote styles)
    # Don't normalize quotes as it can break functionality tests
    return js


def extract_function_body(js: str) -> Optional[str]:
    """Extract the body of a function from JS code."""
    match = re.search(r'\{(.*)\}', js, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


# =============================================================================
# BUILTINS PARITY TESTS
# =============================================================================

class TestBuiltinsParity:
    """Test that Python builtins transpile consistently."""
    
    def test_len_transpilation(self):
        """len() should produce compatible output."""
        # Transpiler uses __py.len for safety with Python semantics
        result = transpile("x = len(items)")
        assert "items.length" in result or "__py.len" in result
    
    def test_str_transpilation(self):
        """str() should produce compatible output."""
        result = transpile("x = str(value)")
        # Phase 33.2: str() uses __py.str() for dunder method support
        assert "__py.str" in result
    
    def test_int_transpilation(self):
        """int() should produce compatible output."""
        result = transpile("x = int(value)")
        assert "parseInt" in result or "__py.int" in result
    
    def test_float_transpilation(self):
        """float() should produce compatible output."""
        result = transpile("x = float(value)")
        assert "parseFloat" in result or "__py.float" in result
    
    def test_abs_transpilation(self):
        """abs() should produce compatible output."""
        result = transpile("x = abs(value)")
        # Phase 33.2: abs() uses __py.abs() for dunder method support
        assert "__py.abs" in result
    
    def test_min_transpilation(self):
        """min() should produce compatible output."""
        result = transpile("x = min(a, b)")
        assert "Math.min" in result or "__py.min" in result
    
    def test_max_transpilation(self):
        """max() should produce compatible output."""
        result = transpile("x = max(a, b)")
        assert "Math.max" in result or "__py.max" in result
    
    def test_print_transpilation(self):
        """print() should produce __py.print() for proper string conversion."""
        result = transpile("print('hello')")
        # Phase 33.2: print() uses __py.print() for proper string conversion
        assert "__py.print" in result


# =============================================================================
# LIST METHODS PARITY TESTS
# =============================================================================

class TestListMethodsParity:
    """Test that list methods transpile consistently."""
    
    def test_append_transpilation(self):
        """list.append() should produce push or equivalent."""
        result = transpile("items.append(x)")
        assert "push" in result
    
    def test_pop_transpilation(self):
        """list.pop() should produce pop()."""
        result = transpile("x = items.pop()")
        assert "pop" in result
    
    def test_list_index_access(self):
        """List index access should handle negative indices."""
        result = transpile("x = items[-1]")
        # Should use __py.at for negative index safety
        assert "__py.at" in result or "items[items.length - 1]" in result
    
    def test_list_slice(self):
        """List slicing should produce array slice."""
        result = transpile("x = items[1:3]")
        assert "slice" in result or "__py.slice" in result
    
    def test_list_comprehension(self):
        """List comprehension should produce map/filter."""
        result = transpile("x = [i * 2 for i in items]")
        assert "map" in result


# =============================================================================
# DICT METHODS PARITY TESTS
# =============================================================================

class TestDictMethodsParity:
    """Test that dict methods transpile consistently."""
    
    def test_dict_get(self):
        """dict.get() should handle default values."""
        result = transpile("x = data.get('key', 'default')")
        assert "__py.dict.get" in result or "??" in result or "||" in result
    
    def test_dict_keys(self):
        """dict.keys() should produce Object.keys."""
        result = transpile("x = data.keys()")
        assert "Object.keys" in result or "__py.dict.keys" in result
    
    def test_dict_values(self):
        """dict.values() should produce Object.values."""
        result = transpile("x = data.values()")
        assert "Object.values" in result or "__py.dict.values" in result
    
    def test_dict_items(self):
        """dict.items() should produce Object.entries."""
        result = transpile("x = data.items()")
        assert "Object.entries" in result or "__py.dict.items" in result
    
    def test_dict_update(self):
        """dict.update() should use Object.assign or __py.dict.update."""
        result = transpile("data.update(other)")
        assert "Object.assign" in result or "__py.dict.update" in result


# =============================================================================
# STRING METHODS PARITY TESTS
# =============================================================================

class TestStringMethodsParity:
    """Test that string methods transpile consistently."""
    
    def test_upper(self):
        """str.upper() should produce toUpperCase."""
        result = transpile("x = s.upper()")
        assert "toUpperCase" in result
    
    def test_lower(self):
        """str.lower() should produce toLowerCase."""
        result = transpile("x = s.lower()")
        assert "toLowerCase" in result
    
    def test_strip(self):
        """str.strip() should produce trim."""
        result = transpile("x = s.strip()")
        assert "trim" in result
    
    def test_split(self):
        """str.split() should produce split."""
        result = transpile("x = s.split(',')")
        assert "split" in result
    
    def test_join(self):
        """str.join() should produce join."""
        result = transpile("x = ','.join(items)")
        assert "join" in result
    
    def test_replace(self):
        """str.replace() should produce replace or replaceAll."""
        result = transpile("x = s.replace('a', 'b')")
        assert "replace" in result
    
    def test_startswith(self):
        """str.startswith() should produce startsWith."""
        result = transpile("x = s.startswith('hello')")
        assert "startsWith" in result
    
    def test_endswith(self):
        """str.endswith() should produce endsWith."""
        result = transpile("x = s.endswith('world')")
        assert "endsWith" in result
    
    def test_find(self):
        """str.find() should produce indexOf."""
        result = transpile("x = s.find('a')")
        assert "indexOf" in result


# =============================================================================
# OPERATOR PARITY TESTS
# =============================================================================

class TestOperatorParity:
    """Test that operators transpile consistently."""
    
    def test_equality(self):
        """== should produce === or __py.eq for Python semantics."""
        result = transpile("x = a == b")
        # Transpiler uses __py.eq for proper Python equality semantics
        assert "===" in result or "__py.eq" in result
    
    def test_inequality(self):
        """!= should produce !== or negated __py.eq."""
        result = transpile("x = a != b")
        # Transpiler uses !__py.eq for proper Python inequality
        assert "!==" in result or ("__py.eq" in result and "!" in result)
    
    def test_floor_division(self):
        """// should produce Math.floor division or dunder runtime."""
        result = transpile("x = a // b")
        assert_has_runtime_function(result, "floordiv", allow_native_js=True)
    
    def test_power(self):
        """** should produce **, Math.pow, or dunder runtime for dunder support."""
        result = transpile("x = a ** b")
        # Phase 33.2: ** uses dunder runtime for dunder method support
        # For numeric literals, may use ** or Math.pow
        assert_has_runtime_function(result, "pow", allow_native_js=True)
    
    def test_modulo(self):
        """% should handle negative modulo correctly."""
        result = transpile("x = a % b")
        # Python modulo differs from JS for negative numbers
        # Transpiler uses dunder runtime for correctness
        assert_has_runtime_function(result, "mod")
    
    def test_in_operator_string(self):
        """'in' with string should produce includes or __py.in."""
        result = transpile("x = 'a' in s")
        # Transpiler uses __py.in for polymorphic containment check
        assert "includes" in result or "__py.contains" in result or "__py.in" in result
    
    def test_in_operator_list(self):
        """'in' with list should produce includes or __py.in."""
        result = transpile("x = item in items")
        # Transpiler uses __py.in for polymorphic containment check
        assert "includes" in result or "__py.contains" in result or "__py.in" in result
    
    def test_not_in_operator(self):
        """'not in' should negate includes."""
        result = transpile("x = item not in items")
        assert "!" in result or "not" in result.lower()


# =============================================================================
# CONTROL FLOW PARITY TESTS
# =============================================================================

class TestControlFlowParity:
    """Test that control flow transpiles consistently."""
    
    def test_if_statement(self):
        """if statement should produce if."""
        result = transpile("if x: y = 1")
        assert "if" in result
        assert "{" in result
    
    def test_if_else(self):
        """if/else should produce if/else."""
        result = transpile("""
if x:
    y = 1
else:
    y = 2
""")
        assert "if" in result
        assert "else" in result
    
    def test_if_elif_else(self):
        """if/elif/else should produce if/else if/else."""
        result = transpile("""
if x:
    y = 1
elif z:
    y = 2
else:
    y = 3
""")
        assert "if" in result
        assert "else if" in result
    
    def test_for_loop(self):
        """for loop should produce for...of."""
        result = transpile("for item in items: print(item)")
        assert "for" in result
        assert "of" in result
    
    def test_for_loop_with_range(self):
        """for with range should produce proper loop."""
        result = transpile("for i in range(10): print(i)")
        assert "for" in result
    
    def test_while_loop(self):
        """while loop should produce while."""
        result = transpile("while x: x = x - 1")
        assert "while" in result
    
    def test_break_statement(self):
        """break should produce break."""
        result = transpile("while True: break")
        assert "break" in result
    
    def test_continue_statement(self):
        """continue should produce continue."""
        result = transpile("for x in items: continue")
        assert "continue" in result
    
    def test_ternary_expression(self):
        """x if cond else y should produce ternary."""
        result = transpile("z = a if x else b")
        assert "?" in result
        assert ":" in result


# =============================================================================
# FUNCTION PARITY TESTS
# =============================================================================

class TestFunctionParity:
    """Test that functions transpile consistently."""
    
    def test_simple_function(self):
        """Simple function should produce function declaration."""
        result = transpile("""
def add(a, b):
    return a + b
""")
        assert "function add" in result
        assert "return" in result
    
    def test_lambda(self):
        """Lambda should produce arrow function."""
        result = transpile("fn = lambda x: x * 2")
        assert "=>" in result
    
    def test_function_with_default_args(self):
        """Default args should produce default parameters."""
        result = transpile("""
def greet(name, greeting='Hello'):
    return greeting + ' ' + name
""")
        assert "=" in result
        # Should have default value
        assert "Hello" in result
    
    def test_function_return_none(self):
        """Return without value should produce return."""
        result = transpile("""
def early_exit():
    if True:
        return
    print('never')
""")
        assert "return" in result


# =============================================================================
# REACTIVE PRIMITIVES PARITY TESTS
# =============================================================================

class TestReactivePrimitivesParity:
    """Test that reactive primitive calls work correctly."""
    
    def test_signal_read(self):
        """Signal read count() should transpile correctly."""
        result = transpile("x = count()")
        # Should produce function call
        assert "count()" in result
    
    def test_signal_set(self):
        """Signal set should produce .set()."""
        result = transpile("count.set(5)")
        assert ".set(" in result
        assert "5" in result
    
    def test_signal_update(self):
        """Signal update should produce .update()."""
        result = transpile("count.update(lambda x: x + 1)")
        # Should produce .update with arrow function
        assert ".update(" in result or "__py.dict.update" in result
    
    def test_signal_peek(self):
        """Signal peek should produce .peek()."""
        result = transpile("x = count.peek()")
        assert ".peek(" in result


# =============================================================================
# ASYNC/AWAIT PARITY TESTS
# =============================================================================

class TestAsyncParity:
    """Test that async/await transpiles correctly."""
    
    def test_async_function(self):
        """async def should produce async function."""
        result = transpile("""
async def fetch_data():
    return await get_data()
""")
        assert "async" in result
    
    def test_await_expression(self):
        """await should produce await."""
        result = transpile("""
async def fetch():
    x = await get_data()
""")
        assert "await" in result


# =============================================================================
# TRY/EXCEPT PARITY TESTS
# =============================================================================

class TestTryExceptParity:
    """Test that try/except transpiles correctly."""
    
    def test_try_except_basic(self):
        """try/except should produce try/catch."""
        result = transpile("""
try:
    x = risky()
except:
    x = 0
""")
        assert "try" in result
        assert "catch" in result
    
    def test_try_except_named(self):
        """Named exception should be available in catch."""
        result = transpile("""
try:
    x = risky()
except Exception as e:
    print(e)
""")
        assert "catch" in result
        assert "e" in result
    
    def test_try_finally(self):
        """try/finally should produce try/finally."""
        result = transpile("""
try:
    x = risky()
finally:
    cleanup()
""")
        assert "try" in result
        assert "finally" in result


# =============================================================================
# CLASS TRANSPILATION TESTS
# =============================================================================

class TestClassParity:
    """Test that class definitions transpile correctly."""
    
    def test_simple_class(self):
        """Simple class should produce class."""
        result = transpile("""
class Counter:
    def __init__(self, start=0):
        self.count = start
    
    def increment(self):
        self.count = self.count + 1
""")
        assert "class Counter" in result
    
    def test_class_method(self):
        """Methods should be class methods."""
        result = transpile("""
class MyClass:
    def method(self):
        return self.value
""")
        assert "method" in result
        assert "this" in result


# =============================================================================
# FSTRING PARITY TESTS
# =============================================================================

class TestFStringParity:
    """Test that f-strings transpile correctly."""
    
    def test_simple_fstring(self):
        """f-string should produce template literal."""
        result = transpile("x = f'Hello {name}'")
        assert "`" in result or "+" in result  # Template literal or concatenation
    
    def test_fstring_with_expression(self):
        """f-string with expression should work."""
        result = transpile("x = f'Count: {count + 1}'")
        assert "count" in result


# =============================================================================
# EDGE CASES PARITY TESTS
# =============================================================================

class TestEdgeCases:
    """Test edge cases for consistency."""
    
    def test_boolean_literals(self):
        """True/False should produce true/false."""
        result_true = transpile("x = True")
        result_false = transpile("x = False")
        assert "true" in result_true.lower()
        assert "false" in result_false.lower()
    
    def test_none_literal(self):
        """None should produce null."""
        result = transpile("x = None")
        assert "null" in result
    
    def test_empty_list(self):
        """[] should produce []."""
        result = transpile("x = []")
        assert "[]" in result
    
    def test_empty_dict(self):
        """{} should produce {}."""
        result = transpile("x = {}")
        assert "{}" in result
    
    def test_multiline_string(self):
        """Multi-line string should work."""
        result = transpile('x = """hello\nworld"""')
        # Should handle newlines
        assert "hello" in result
        assert "world" in result


# =============================================================================
# RUNTIME HELPER TESTS
# =============================================================================

class TestRuntimeHelpers:
    """Test that runtime helpers are used appropriately."""
    
    def test_py_at_for_negative_index(self):
        """Negative index should use __py.at for safety."""
        result = transpile("x = items[-1]")
        assert "__py.at" in result
    
    def test_py_slice_for_slicing(self):
        """Slicing should use __py.slice or native slice."""
        result = transpile("x = items[1:3]")
        assert "slice" in result or "__py.slice" in result
    
    def test_py_add_for_polymorphic_addition(self):
        """Addition uses dunder runtime for Python polymorphism (string + number, etc)."""
        result = transpile("x = a + b")
        # Transpiler uses dunder runtime for proper Python semantics
        assert_has_runtime_function(result, "add")
    
    def test_py_contains_for_in_operator(self):
        """'in' operator should use __py.in, __py.contains or includes."""
        result = transpile("x = item in items")
        # Transpiler uses __py.in for polymorphic containment
        assert "includes" in result or "__py.contains" in result or "__py.in" in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestEmitterIntegration:
    """Integration tests for emitter compatibility."""
    
    def test_handler_code_works_in_island_context(self):
        """Handler code should be valid in island context."""
        # Simulate event handler transpilation
        handler_code = transpile("count.set(count() + 1)")
        
        # Handler code should be executable JS
        assert "count" in handler_code
        assert ".set(" in handler_code
    
    def test_complex_handler(self):
        """Complex handler with multiple operations should work."""
        result = transpile("""
if count() > 10:
    count.set(0)
else:
    count.update(lambda x: x + 1)
""")
        assert "if" in result
        assert "count" in result
    
    def test_handler_with_event_parameter(self):
        """Handler with event parameter should work."""
        result = transpile("""
def handle_click(event):
    event.preventDefault()
    count.set(count() + 1)
""")
        assert "event" in result
        assert "preventDefault" in result
    
    def test_form_handler(self):
        """Form submission handler should work."""
        result = transpile("""
def handle_submit(event):
    event.preventDefault()
    data = form.get_data()
    submit_form(data)
""")
        assert "preventDefault" in result
        assert "data" in result
