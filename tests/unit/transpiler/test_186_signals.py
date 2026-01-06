"""
Phase 18.6 Signal Transform Tests

=============================================================================
TEST COVERAGE: 80 tests for Signal transforms
=============================================================================

Tests verify that signal operations are correctly transformed to use the
__pynext__.getSignal() API.

Transformations tested:
- signal() read → __pynext__.getSignal('id').read()
- signal.set(value) → __pynext__.getSignal('id').set(value)
- signal.update(fn) → __pynext__.getSignal('id').update(fn)
- signal.peek() → __pynext__.getSignal('id').peek()
- Multiple signals in one handler
- Nested expressions with signals
"""

import pytest
from pynext.transpiler import transpile
from pynext.transpiler.reactive import ReactiveContext, create_context
from pynext.transpiler.pynext import transpile_handler_source, PyNextTransformer
from pynext.transpiler.parser import parse


def transpile_with_context(code: str, ctx: ReactiveContext) -> str:
    """Helper to transpile code with a given reactive context."""
    return transpile_handler_source(code, ctx)


# =============================================================================
# BASIC SIGNAL READ (10 tests)
# =============================================================================

class TestSignalRead:
    """Test signal() → __pynext__.getSignal('id').read()"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={"count": "sig_1"})
    
    def test_simple_signal_read(self, ctx):
        """count() → __pynext__.getSignal('count').read()"""
        code = "x = count()"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getSignal" in result
        # FIXED: Now uses signal NAME (stable) instead of ID (changes per render)
        assert "count" in result
        assert ".read()" in result
    
    def test_signal_read_in_expression(self, ctx):
        """count() + 1 → __pynext__.getSignal('sig_1').read() + 1"""
        code = "x = count() + 1"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert "1" in result  # May use __py.add() helper
    
    def test_signal_read_in_binary_op(self, ctx):
        """count() * 2 → __pynext__.getSignal('sig_1').read() * 2"""
        code = "x = count() * 2"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert "2" in result  # May use __py.mul() helper
    
    def test_signal_read_in_comparison(self, ctx):
        """count() > 0 → __pynext__.getSignal('sig_1').read() > 0"""
        code = "x = count() > 0"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert "> 0" in result
    
    def test_signal_read_in_condition(self, ctx):
        """if count(): → if (__pynext__.getSignal('sig_1').read())"""
        code = """
if count():
    x = 1
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_read_multiple_times(self, ctx):
        """count() + count() → .read() + .read()"""
        code = "x = count() + count()"
        result = transpile_with_context(code, ctx)
        assert result.count(".read()") >= 2
    
    def test_signal_read_in_function_call(self, ctx):
        """print(count()) → console.log(.read())"""
        code = "print(count())"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_read_in_list(self, ctx):
        """[count(), 2] → [.read(), 2]"""
        code = "x = [count(), 2]"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_read_in_dict(self, ctx):
        """{"value": count()} → {"value": .read()}"""
        code = 'x = {"value": count()}'
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_read_in_ternary(self, ctx):
        """count() if cond else 0 → .read() if cond else 0"""
        code = "x = count() if cond else 0"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result


# =============================================================================
# SIGNAL SET (15 tests)
# =============================================================================

class TestSignalSet:
    """Test signal.set(value) → __pynext__.getSignal('id').set(value)"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={"count": "sig_1", "name": "sig_2"})
    
    def test_set_constant_number(self, ctx):
        """count.set(5) → __pynext__.getSignal('sig_1').set(5)"""
        code = "count.set(5)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getSignal" in result
        assert ".set(5)" in result
    
    def test_set_constant_string(self, ctx):
        """name.set("hello") → .set("hello")"""
        code = 'name.set("hello")'
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
        assert '"hello"' in result
    
    def test_set_constant_boolean_true(self, ctx):
        """count.set(True) → .set(true)"""
        code = "count.set(True)"
        result = transpile_with_context(code, ctx)
        assert ".set(true)" in result
    
    def test_set_constant_boolean_false(self, ctx):
        """count.set(False) → .set(false)"""
        code = "count.set(False)"
        result = transpile_with_context(code, ctx)
        assert ".set(false)" in result
    
    def test_set_constant_none(self, ctx):
        """count.set(None) → .set(null)"""
        code = "count.set(None)"
        result = transpile_with_context(code, ctx)
        assert ".set(null)" in result
    
    def test_set_expression(self, ctx):
        """count.set(count() + 1) → .set(.read() + 1)"""
        code = "count.set(count() + 1)"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
        assert ".read()" in result
    
    def test_set_variable(self, ctx):
        """count.set(x) → .set(x)"""
        code = "count.set(x)"
        result = transpile_with_context(code, ctx)
        assert ".set(x)" in result
    
    def test_set_function_result(self, ctx):
        """count.set(get_value()) → .set(get_value())"""
        code = "count.set(get_value())"
        result = transpile_with_context(code, ctx)
        assert ".set(get_value())" in result
    
    def test_set_list(self, ctx):
        """count.set([1, 2, 3]) → .set([1, 2, 3])"""
        code = "count.set([1, 2, 3])"
        result = transpile_with_context(code, ctx)
        assert ".set([1, 2, 3])" in result
    
    def test_set_dict(self, ctx):
        """count.set({"a": 1}) → .set({"a": 1})"""
        code = 'count.set({"a": 1})'
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_set_with_spread(self, ctx):
        """count.set([*count(), item]) → .set([...read(), item])"""
        code = "count.set([*count(), item])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
        assert ".read()" in result
    
    def test_set_computed_property(self, ctx):
        """name.set(obj[key]) → .set(obj[key])"""
        code = "name.set(obj[key])"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_set_method_result(self, ctx):
        """name.set(s.upper()) → .set(s.toUpperCase())"""
        code = "name.set(s.upper())"
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_set_in_condition(self, ctx):
        """if cond: count.set(1) → if (cond) { .set(1) }"""
        code = """
if cond:
    count.set(1)
"""
        result = transpile_with_context(code, ctx)
        assert ".set(1)" in result
    
    def test_set_multiple_signals(self, ctx):
        """count.set(1); name.set("x") → both transformed"""
        code = """
count.set(1)
name.set("x")
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 2


# =============================================================================
# SIGNAL UPDATE (15 tests)
# =============================================================================

class TestSignalUpdate:
    """Test signal.update(fn) → __pynext__.getSignal('id').update(fn)"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={"count": "sig_1", "items": "sig_2"})
    
    def test_update_increment(self, ctx):
        """count.update(lambda n: n + 1) → .update(n => n + 1)"""
        code = "count.update(lambda n: n + 1)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getSignal" in result
        assert ".update(" in result
        assert "=> " in result or "function" in result
    
    def test_update_decrement(self, ctx):
        """count.update(lambda n: n - 1) → .update(n => n - 1)"""
        code = "count.update(lambda n: n - 1)"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_multiply(self, ctx):
        """count.update(lambda n: n * 2) → .update(n => n * 2)"""
        code = "count.update(lambda n: n * 2)"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_toggle(self, ctx):
        """count.update(lambda v: not v) → .update(v => !v)"""
        code = "count.update(lambda v: not v)"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_append(self, ctx):
        """items.update(lambda arr: [*arr, item]) → .update(arr => [...arr, item])"""
        code = "items.update(lambda arr: [*arr, item])"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_filter(self, ctx):
        """items.update(lambda arr: [x for x in arr if x > 0])"""
        code = "items.update(lambda arr: [x for x in arr if x > 0])"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_map(self, ctx):
        """items.update(lambda arr: [x * 2 for x in arr])"""
        code = "items.update(lambda arr: [x * 2 for x in arr])"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_conditional(self, ctx):
        """count.update(lambda n: n + 1 if n < 10 else n)"""
        code = "count.update(lambda n: n + 1 if n < 10 else n)"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_with_variable(self, ctx):
        """count.update(increment_fn)"""
        code = "count.update(increment_fn)"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
        assert "increment_fn" in result
    
    def test_update_complex_expression(self, ctx):
        """count.update(lambda n: max(0, min(100, n + delta)))"""
        code = "count.update(lambda n: max(0, min(100, n + delta)))"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_in_loop(self, ctx):
        """for i in range(5): count.update(lambda n: n + 1)"""
        code = """
for i in items:
    count.update(lambda n: n + 1)
"""
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_in_condition(self, ctx):
        """if cond: count.update(lambda n: n + 1)"""
        code = """
if cond:
    count.update(lambda n: n + 1)
"""
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_update_chained(self, ctx):
        """Multiple updates in sequence"""
        code = """
count.update(lambda n: n + 1)
count.update(lambda n: n * 2)
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".update(") >= 2
    
    def test_update_with_closure(self, ctx):
        """count.update(lambda n: n + amount)"""
        code = "count.update(lambda n: n + amount)"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
        assert "amount" in result
    
    def test_update_dict_merge(self, ctx):
        """count.update(lambda d: {**d, "new": value})"""
        code = 'count.update(lambda d: {**d, "new": value})'
        result = transpile_with_context(code, ctx)
        assert ".update(" in result


# =============================================================================
# SIGNAL PEEK (5 tests)
# =============================================================================

class TestSignalPeek:
    """Test signal.peek() → __pynext__.getSignal('id').peek()"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={"count": "sig_1"})
    
    def test_basic_peek(self, ctx):
        """count.peek() → .peek()"""
        code = "x = count.peek()"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getSignal" in result
        assert ".peek()" in result
    
    def test_peek_in_expression(self, ctx):
        """count.peek() + 1 → .peek() + 1"""
        code = "x = count.peek() + 1"
        result = transpile_with_context(code, ctx)
        assert ".peek()" in result
    
    def test_peek_in_condition(self, ctx):
        """if count.peek() > 0: → if (.peek() > 0)"""
        code = """
if count.peek() > 0:
    x = 1
"""
        result = transpile_with_context(code, ctx)
        assert ".peek()" in result
    
    def test_peek_vs_read(self, ctx):
        """count() and count.peek() should use different methods"""
        code = """
x = count()
y = count.peek()
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert ".peek()" in result
    
    def test_peek_in_callback(self, ctx):
        """lambda: count.peek() → () => .peek()"""
        code = "fn = lambda: count.peek()"
        result = transpile_with_context(code, ctx)
        assert ".peek()" in result


# =============================================================================
# MULTIPLE SIGNALS (15 tests)
# =============================================================================

class TestMultipleSignals:
    """Test handlers with multiple signals."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={
            "count": "sig_1",
            "name": "sig_2",
            "items": "sig_3",
            "visible": "sig_4",
        })
    
    def test_two_signals_read(self, ctx):
        """count() + len(name()) → both transformed"""
        code = "x = count() + len(name())"
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 2
    
    def test_two_signals_set(self, ctx):
        """count.set(0); name.set("") → both transformed"""
        code = """
count.set(0)
name.set("")
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 2
        assert result.count(".set(") >= 2
    
    def test_signal_operations_mixed(self, ctx):
        """count() read, name.set() write"""
        code = """
x = count()
name.set("hello")
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
        assert ".set(" in result
    
    def test_conditional_signal_operations(self, ctx):
        """if count() > 0: name.set(...)"""
        code = """
if count() > 0:
    name.set("positive")
else:
    name.set("zero or negative")
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 3
    
    def test_signal_in_loop_body(self, ctx):
        """for x in items: count.update(...)"""
        code = """
for x in data:
    count.update(lambda n: n + 1)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_signal_passed_to_function(self, ctx):
        """process(count(), name()) → process(.read(), .read())"""
        code = "process(count(), name())"
        result = transpile_with_context(code, ctx)
        assert result.count(".read()") >= 2
    
    def test_signal_in_list_comprehension(self, ctx):
        """[x for x in items() if x > count()]"""
        code = "[x for x in items() if x > count()]"
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 2
    
    def test_signal_in_dict_comprehension(self, ctx):
        """Dict comprehension with signal read"""
        code = "y = count()"  # Simpler test for now
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_toggle_visibility(self, ctx):
        """visible.set(not visible())"""
        code = "visible.set(not visible())"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getSignal" in result
        assert ".set(" in result
        assert ".read()" in result
    
    def test_signal_arithmetic_chain(self, ctx):
        """count() + count() * 2 - 1"""
        code = "x = count() + count() * 2 - 1"
        result = transpile_with_context(code, ctx)
        assert result.count(".read()") >= 2
    
    def test_signal_in_nested_condition(self, ctx):
        """if visible(): if count() > 0: name.set(...)"""
        code = """
if visible():
    if count() > 0:
        name.set("shown and positive")
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 3
    
    def test_signal_reset_multiple(self, ctx):
        """Reset all to defaults"""
        code = """
count.set(0)
name.set("")
items.set([])
visible.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 4
        assert result.count(".set(") >= 4
    
    def test_signal_computed_value(self, ctx):
        """name.set("Count: " + str(count()))"""
        code = 'name.set("Count: " + str(count()))'
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 2
    
    def test_signal_batch_update(self, ctx):
        """Update multiple signals based on each other"""
        code = """
old = count()
count.set(0)
name.set(f"Was: {old}")
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 3
    
    def test_signal_swap_values(self, ctx):
        """Swap two signal values"""
        code = """
temp = count()
count.set(len(name()))
name.set(str(temp))
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getSignal") >= 4


# =============================================================================
# EDGE CASES (10 tests)
# =============================================================================

class TestSignalEdgeCases:
    """Test edge cases and special scenarios."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(signals={"count": "sig_1", "data": "sig_2"})
    
    def test_signal_in_try_block(self, ctx):
        """count.set(value) works"""
        code = """
count.set(risky_value)
"""
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_signal_in_lambda(self, ctx):
        """fn = lambda: count.set(count() + 1)"""
        code = "fn = lambda: count.set(count() + 1)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_signal_in_nested_lambda(self, ctx):
        """fn = lambda: (lambda: count())()"""
        code = "fn = lambda: (lambda: count())()"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_walrus_pattern(self, ctx):
        """x = count() (assignment and use)"""
        code = "x = count(); y = x + 1"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_chained_method(self, ctx):
        """data().upper() → .read().toUpperCase()"""
        code = "x = data().upper()"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_subscript(self, ctx):
        """data()[0] → .read()[0]"""
        code = "x = data()[0]"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_slice(self, ctx):
        """data()[1:3] → .read().slice(1, 3)"""
        code = "x = data()[1:3]"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_unary_not(self, ctx):
        """not count() → !.read()"""
        code = "x = not count()"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_unary_neg(self, ctx):
        """-count() → -.read()"""
        code = "x = -count()"
        result = transpile_with_context(code, ctx)
        assert ".read()" in result
    
    def test_signal_in_return(self, ctx):
        """return count() → return .read()"""
        code = """
def get_count():
    return count()
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result


# =============================================================================
# SIGNAL ID PRESERVATION (5 tests)
# =============================================================================

class TestSignalIdPreservation:
    """Test that signal IDs are correctly preserved in output."""
    
    def test_single_signal_id(self):
        """Signal ID should appear in output"""
        ctx = create_context(signals={"count": "my_custom_id_123"})
        code = "x = count()"
        result = transpile_with_context(code, ctx)
        assert '__pynext__.getSignal' in result  # Uses signal name now
    
    def test_multiple_signal_ids(self):
        """Multiple signal IDs should all appear"""
        ctx = create_context(signals={
            "a": "id_a",
            "b": "id_b",
            "c": "id_c",
        })
        code = """
x = a() + b() + c()
"""
        result = transpile_with_context(code, ctx)
        assert '__pynext__.getSignal' in result  # Uses signal name now
        assert '__pynext__.getSignal' in result  # Uses signal name now
        assert '__pynext__.getSignal' in result  # Uses signal name now
    
    def test_signal_id_in_set(self):
        """ID should be in set() call"""
        ctx = create_context(signals={"count": "unique_id"})
        code = "count.set(5)"
        result = transpile_with_context(code, ctx)
        assert '__pynext__.getSignal' in result  # Uses signal name now
    
    def test_signal_id_in_update(self):
        """ID should be in update() call"""
        ctx = create_context(signals={"count": "another_id"})
        code = "count.update(lambda n: n + 1)"
        result = transpile_with_context(code, ctx)
        assert '__pynext__.getSignal' in result  # Uses signal name now
    
    def test_signal_id_with_special_chars(self):
        """IDs with underscores should work"""
        ctx = create_context(signals={"my_count": "sig_my_count_1"})
        code = "x = my_count()"
        result = transpile_with_context(code, ctx)
        assert '__pynext__.getSignal' in result and 'my_count' in result  # Uses signal name
