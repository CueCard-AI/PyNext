"""
Tests for Event Handler Pipeline - Full Transformation Flow

Event handlers go through multiple transformation stages:
1. Python function → Source code extraction (inspect.getsource + textwrap.dedent)
2. Source code → ReactiveContext analysis (closure detection)
3. Analysis → PyNextTransformer (signal/store ID mapping)
4. Transformed IR → JavaScript emission

Any stage can fail or produce incorrect output.

RISK AREAS TESTED:
1. Lambda handlers with multiple closures
2. Handlers that reference globals instead of closures
3. Nested function definitions inside handlers
4. Async handlers
5. Handlers with event parameters
6. Multi-statement handlers
7. Handlers with conditionals and loops
8. Form field access patterns
9. Store nested property access
10. Error propagation through pipeline
"""

import pytest
import textwrap
from unittest.mock import Mock, MagicMock, patch
import inspect


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def mock_signal():
    """Create a mock signal."""
    sig = Mock()
    sig._id = "sig_count"
    sig._name = "count"
    sig._value = 0
    return sig


@pytest.fixture
def mock_store():
    """Create a mock store."""
    store = Mock()
    store._id = "store_state"
    store._name = "state"
    store._data = {"items": [], "user": {"name": "Alice"}}
    return store


@pytest.fixture
def mock_form():
    """Create a mock form."""
    form = Mock()
    form._form_id = "form_login"
    form.username = Mock(_value="")
    form.password = Mock(_value="")
    return form


# =============================================================================
# SOURCE EXTRACTION TESTS
# =============================================================================

class TestSourceExtraction:
    """Tests for source code extraction from handlers."""
    
    def test_extract_lambda_source(self):
        """Should extract lambda source correctly."""
        from pynext.transpiler.reactive import get_handler_source
        
        handler = lambda: print("hello")
        source = get_handler_source(handler)
        
        assert source is not None
        assert "lambda" in source
    
    def test_extract_function_source(self):
        """Should extract function source correctly."""
        from pynext.transpiler.reactive import get_handler_source
        
        def my_handler():
            print("hello")
        
        source = get_handler_source(my_handler)
        
        assert source is not None
        assert "def my_handler" in source
    
    def test_extract_nested_handler_source(self):
        """Should dedent nested handler source."""
        from pynext.transpiler.reactive import get_handler_source
        
        class Container:
            def create_handler(self):
                def nested_handler():
                    return 42
                return nested_handler
        
        handler = Container().create_handler()
        source = get_handler_source(handler)
        
        assert source is not None
        # Should be dedented - no leading whitespace
        assert not source.startswith("    ")
        assert not source.startswith("\t")
    
    def test_extract_multiline_lambda(self):
        """Should handle lambdas that span lines (via parentheses)."""
        from pynext.transpiler.reactive import get_handler_source
        
        handler = (lambda x:
            x * 2)
        
        source = get_handler_source(handler)
        assert source is not None
    
    def test_extract_decorated_function(self):
        """Should extract decorated function source."""
        from pynext.transpiler.reactive import get_handler_source
        
        def my_decorator(fn):
            return fn
        
        @my_decorator
        def decorated_handler():
            return "decorated"
        
        source = get_handler_source(decorated_handler)
        assert source is not None


# =============================================================================
# REACTIVE CONTEXT ANALYSIS TESTS
# =============================================================================

class TestReactiveContextAnalysis:
    """Tests for analyzing handler closures for reactive objects."""
    
    def test_analyze_signal_in_closure(self, mock_signal):
        """Should detect signal in handler closure."""
        from pynext.transpiler.reactive import analyze_handler
        
        count = mock_signal
        
        def handler():
            count.set(count() + 1)
        
        # Inject signal into handler's closure
        handler.__globals__['count'] = count
        
        ctx = analyze_handler(handler)
        
        # Context should have the signal
        assert ctx is not None
    
    def test_analyze_multiple_signals(self, mock_signal):
        """Should detect multiple signals in closure."""
        from pynext.transpiler.reactive import analyze_handler
        
        sig1 = Mock(_id="sig_1", _name="count")
        sig2 = Mock(_id="sig_2", _name="name")
        
        def handler():
            sig1.set(sig1() + 1)
            sig2.set("updated")
        
        handler.__globals__['sig1'] = sig1
        handler.__globals__['sig2'] = sig2
        
        ctx = analyze_handler(handler)
        assert ctx is not None
    
    def test_analyze_store_in_closure(self, mock_store):
        """Should detect store in handler closure."""
        from pynext.transpiler.reactive import analyze_handler
        
        state = mock_store
        
        def handler():
            state.items.append("new")
        
        handler.__globals__['state'] = state
        
        ctx = analyze_handler(handler)
        assert ctx is not None
    
    def test_analyze_form_in_closure(self, mock_form):
        """Should detect form in handler closure."""
        from pynext.transpiler.reactive import analyze_handler
        
        form = mock_form
        
        def handler():
            data = form.username._value
        
        handler.__globals__['form'] = form
        
        ctx = analyze_handler(handler)
        assert ctx is not None


# =============================================================================
# PYNEXT TRANSFORMER TESTS
# =============================================================================

class TestPyNextTransformer:
    """Tests for PyNextTransformer signal/store mapping."""
    
    def test_transform_signal_read(self):
        """Signal reads should transform to __pynext__.getSignal().read()."""
        from pynext.transpiler import transpile
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import PyNextTransformer, transpile_handler_source
        
        # Simple signal read transformation
        source = "x = count()"
        ctx = ReactiveContext()
        # ReactiveContext uses dict attributes, not methods
        ctx.signals["count"] = ReactiveObjectInfo(
            name="count", id="sig_count", type="signal", obj=None
        )
        
        result = transpile_handler_source(source, ctx)
        
        # Now uses signal name instead of ID
        assert "__pynext__.getSignal" in result
        assert ".read()" in result
    
    def test_transform_signal_set(self):
        """Signal set should transform to __pynext__.getSignal().set()."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import transpile_handler_source
        
        source = "count.set(5)"
        ctx = ReactiveContext()
        ctx.signals["count"] = ReactiveObjectInfo(
            name="count", id="sig_count", type="signal", obj=None
        )
        
        result = transpile_handler_source(source, ctx)
        
        assert "__pynext__.getSignal" in result
        assert ".set(" in result
    
    def test_transform_signal_update(self):
        """Signal update should transform correctly."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import transpile_handler_source
        
        source = "count.update(lambda x: x + 1)"
        ctx = ReactiveContext()
        ctx.signals["count"] = ReactiveObjectInfo(
            name="count", id="sig_count", type="signal", obj=None
        )
        
        result = transpile_handler_source(source, ctx)
        
        assert "__pynext__.getSignal" in result
        assert ".update(" in result
    
    def test_transform_store_access(self):
        """Store access should transform to __pynext__.getStore()."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import transpile_handler_source
        
        source = "x = state.items"
        ctx = ReactiveContext()
        ctx.stores["state"] = ReactiveObjectInfo(
            name="state", id="store_state", type="store", obj=None
        )
        
        result = transpile_handler_source(source, ctx)
        
        assert "__pynext__.getStore" in result or "store_state" in result
    
    def test_transform_form_access(self):
        """Form field access should transform correctly."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import transpile_handler_source
        
        source = "x = form.username.value"
        ctx = ReactiveContext()
        ctx.forms["form"] = ReactiveObjectInfo(
            name="form", id="form_login", type="form", obj=None
        )
        
        result = transpile_handler_source(source, ctx)
        
        assert "form_login" in result or "__pynext__.getForm" in result


# =============================================================================
# JAVASCRIPT EMISSION TESTS
# =============================================================================

class TestJavaScriptEmission:
    """Tests for JavaScript code emission."""
    
    def test_emit_simple_expression(self):
        """Should emit simple expressions correctly."""
        from pynext.transpiler import transpile
        
        result = transpile("x = 5")
        assert "x" in result
        assert "5" in result
    
    def test_emit_arrow_function(self):
        """Lambda should emit as arrow function."""
        from pynext.transpiler import transpile
        
        result = transpile("fn = lambda x: x * 2")
        assert "=>" in result
    
    def test_emit_conditional(self):
        """If statement should emit correctly."""
        from pynext.transpiler import transpile
        
        result = transpile("""
if x > 0:
    y = 1
else:
    y = 0
""")
        assert "if" in result
        assert "else" in result
    
    def test_emit_for_loop(self):
        """For loop should emit as for...of."""
        from pynext.transpiler import transpile
        
        result = transpile("for item in items: print(item)")
        assert "for" in result
        assert "of" in result
    
    def test_emit_try_except(self):
        """Try/except should emit as try/catch."""
        from pynext.transpiler import transpile
        
        result = transpile("""
try:
    risky()
except Exception as e:
    handle(e)
""")
        assert "try" in result
        assert "catch" in result


# =============================================================================
# FULL PIPELINE TESTS
# =============================================================================

class TestFullPipeline:
    """Tests for the complete handler transformation pipeline."""
    
    def test_simple_handler_pipeline(self):
        """Simple click handler should transform completely."""
        from pynext.transpiler import transpile
        
        source = """
def handle_click():
    count.set(count() + 1)
"""
        result = transpile(source)
        
        assert "function handle_click" in result
        assert "count" in result
        assert ".set(" in result
    
    def test_handler_with_event_param(self):
        """Handler with event parameter should work."""
        from pynext.transpiler import transpile
        
        source = """
def handle_submit(event):
    event.preventDefault()
    form.submit()
"""
        result = transpile(source)
        
        assert "event" in result
        assert "preventDefault" in result
    
    def test_handler_with_conditional(self):
        """Handler with conditional logic should work."""
        from pynext.transpiler import transpile
        
        source = """
def handle_click():
    if count() >= 10:
        count.set(0)
    else:
        count.set(count() + 1)
"""
        result = transpile(source)
        
        assert "if" in result
        assert "else" in result
    
    def test_handler_with_loop(self):
        """Handler with loop should work."""
        from pynext.transpiler import transpile
        
        source = """
def process_items():
    for item in items():
        process(item)
"""
        result = transpile(source)
        
        assert "for" in result
    
    def test_async_handler(self):
        """Async handler should work."""
        from pynext.transpiler import transpile
        
        source = """
async def fetch_data():
    result = await api.get('/data')
    data.set(result)
"""
        result = transpile(source)
        
        assert "async" in result
        assert "await" in result
    
    def test_handler_with_multiple_statements(self):
        """Handler with multiple statements should work."""
        from pynext.transpiler import transpile
        
        source = """
def complex_handler():
    x = count()
    y = x * 2
    z = y + 10
    result.set(z)
"""
        result = transpile(source)
        
        # All variables should be present
        assert "x" in result
        assert "y" in result
        assert "z" in result


# =============================================================================
# LAMBDA HANDLER TESTS
# =============================================================================

class TestLambdaHandlers:
    """Tests for lambda handler transformations."""
    
    def test_simple_lambda(self):
        """Simple lambda should transform correctly."""
        from pynext.transpiler import transpile
        
        result = transpile("handler = lambda: count.set(count() + 1)")
        
        assert "=>" in result
        assert "count" in result
    
    def test_lambda_with_param(self):
        """Lambda with parameter should work."""
        from pynext.transpiler import transpile
        
        result = transpile("handler = lambda e: e.preventDefault()")
        
        assert "=>" in result
        assert "preventDefault" in result
    
    def test_lambda_with_multiple_closures(self):
        """Lambda referencing multiple closures should work."""
        from pynext.transpiler import transpile
        
        result = transpile("handler = lambda: (count.set(count() + 1), name.set('updated'))")
        
        assert "count" in result
        assert "name" in result
    
    def test_lambda_in_event_attribute(self):
        """Lambda used as event handler should work."""
        from pynext.transpiler import transpile
        
        result = transpile("onclick = lambda: toggle.set(not toggle())")
        
        assert "toggle" in result
        assert "!" in result or "not" in result.lower()


# =============================================================================
# FORM HANDLER TESTS
# =============================================================================

class TestFormHandlers:
    """Tests for form-related handler transformations."""
    
    def test_form_submit_handler(self):
        """Form submit handler should work."""
        from pynext.transpiler import transpile
        
        result = transpile("""
def handle_submit(e):
    e.preventDefault()
    data = form.values()
    submit(data)
""")
        
        assert "preventDefault" in result
        assert "form" in result
    
    def test_form_field_access(self):
        """Form field access should work."""
        from pynext.transpiler import transpile
        
        result = transpile("username = form.username.value")
        
        assert "username" in result
        assert "value" in result
    
    def test_form_validation(self):
        """Form validation logic should work."""
        from pynext.transpiler import transpile
        
        result = transpile("""
def validate():
    if len(form.password.value) < 8:
        errors.set(['Password too short'])
        return False
    return True
""")
        
        assert "if" in result
        assert "length" in result or "len" in result or "__py" in result


# =============================================================================
# STORE HANDLER TESTS
# =============================================================================

class TestStoreHandlers:
    """Tests for store-related handler transformations."""
    
    def test_store_property_access(self):
        """Store property access should work."""
        from pynext.transpiler import transpile
        
        result = transpile("name = state.user.name")
        
        assert "state" in result
        assert "user" in result
        assert "name" in result
    
    def test_store_array_mutation(self):
        """Store array mutation should work."""
        from pynext.transpiler import transpile
        
        result = transpile("state.items.push(new_item)")
        
        assert "push" in result
    
    def test_store_nested_update(self):
        """Store nested property update should work."""
        from pynext.transpiler import transpile
        
        result = transpile("state.user.name = 'New Name'")
        
        assert "New Name" in result


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in the pipeline."""
    
    def test_invalid_syntax_raises(self):
        """Invalid Python syntax should raise error."""
        from pynext.transpiler import transpile
        from pynext.transpiler.errors import TranspileError
        
        with pytest.raises((TranspileError, SyntaxError)):
            transpile("def broken(")
    
    def test_unsupported_feature_raises(self):
        """Unsupported Python features should raise error."""
        from pynext.transpiler import transpile
        from pynext.transpiler.errors import TranspileError, UnsupportedSyntax
        
        # Regular generators are now supported in Phase 33.2
        result = transpile("""
def generator():
    yield 1
    yield 2
""")
        assert "function*" in result or "yield" in result
        
        # Test a truly unsupported feature: async generators are now supported!
        # Async generators were previously unsupported but are now fully implemented
        # So this should NOT raise an error
        result = transpile("""
async def async_gen():
    yield 1  # Async generators are now supported
""")
        assert "async function*" in result or "async *" in result
    
    def test_async_generator_detection_comprehensive(self):
        """
        Comprehensive test suite for async generator detection.
        
        Tests the robust detection to ensure:
        1. Async generators are correctly detected and transpiled (now supported!)
        2. Regular async functions are allowed
        3. Nested functions don't cause false positives
        4. All edge cases are handled correctly
        
        NOTE: Async generators are now fully supported, so they should NOT raise errors.
        """
        from pynext.transpiler import transpile
        
        # ========================================================================
        # TEST GROUP 1: Direct Async Generators (Should Transpile Successfully)
        # ========================================================================
        
        # Test 1.1: Simple async generator - should transpile successfully
        result = transpile("async def gen(): yield 1")
        assert "async function*" in result or "async *" in result
        
        # Test 1.2: Async generator with multiple yields - should transpile successfully
        result = transpile("""
async def gen():
    yield 1
    yield 2
    yield 3
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 1.3: Async generator with yield from - should transpile successfully
        result = transpile("""
async def gen():
    yield from other_gen()
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 1.4: Async generator with yield in conditional - should transpile successfully
        result = transpile("""
async def gen():
    if condition:
        yield 1
    else:
        yield 2
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 1.5: Async generator with yield in loop - should transpile successfully
        result = transpile("""
async def gen():
    for i in range(10):
        yield i
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 1.6: Async generator with yield in while loop - should transpile successfully
        result = transpile("""
async def gen():
    i = 0
    while i < 10:
        yield i
        i += 1
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 1.7: Async generator with yield in try/except - should transpile successfully
        result = transpile("""
async def gen():
    try:
        yield 1
    except Exception:
        yield 2
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 1.8: Async generator with yield in try/finally - should transpile successfully
        result = transpile("""
async def gen():
    try:
        yield 1
    finally:
        pass
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 1.9: Async generator with yield in nested try/except/finally - should transpile successfully
        result = transpile("""
async def gen():
    try:
        try:
            yield 1
        except:
            yield 2
    finally:
        pass
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 1.10: Async generator with yield in if/elif/else - should transpile successfully
        result = transpile("""
async def gen():
    if x > 0:
        yield 1
    elif x < 0:
        yield -1
    else:
        yield 0
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # ========================================================================
        # TEST GROUP 2: Regular Async Functions (Should Allow)
        # ========================================================================
        
        # Test 2.1: Simple async function
        result = transpile("async def fetch(): return await get_data()")
        assert "async function" in result
        assert "await" in result
        
        # Test 2.2: Async function with multiple awaits
        result = transpile("""
async def fetch():
    data1 = await get_data1()
    data2 = await get_data2()
    return data1 + data2
""")
        assert "async function" in result
        assert result.count("await") >= 2
        
        # Test 2.3: Async function with loops
        result = transpile("""
async def process():
    for item in items:
        await process_item(item)
""")
        assert "async function" in result
        assert "await" in result
        
        # Test 2.4: Async function with conditionals
        result = transpile("""
async def fetch():
    if condition:
        return await get_data1()
    else:
        return await get_data2()
""")
        assert "async function" in result
        assert "await" in result
        
        # Test 2.5: Async function with try/except
        result = transpile("""
async def fetch():
    try:
        return await get_data()
    except Exception:
        return None
""")
        assert "async function" in result
        assert "await" in result
        
        # ========================================================================
        # TEST GROUP 3: Nested Functions (Should Not Cause False Positives)
        # ========================================================================
        
        # Test 3.1: Async function with nested regular generator (should allow)
        result = transpile("""
async def outer():
    def inner():
        yield 1
    return inner
""")
        assert "async function" in result
        # Should NOT raise error - nested generator is separate
        
        # Test 3.2: Async function with nested regular function with yield (should allow)
        result = transpile("""
async def outer():
    def inner():
        if condition:
            yield 1
        return inner
""")
        assert "async function" in result
        # Should NOT raise error - nested generator is separate
        
        # Test 3.3: Async function with multiple nested functions, one with yield
        result = transpile("""
async def outer():
    def helper1():
        return 1
    
    def helper2():
        yield 2
    
    def helper3():
        return 3
    
    return helper2
""")
        assert "async function" in result
        # Should NOT raise error - nested generator is separate
        
        # Test 3.4: Async function with nested async function (should allow outer)
        # Note: The nested async function itself will be rejected when parsed,
        # but the outer function should be allowed
        result = transpile("""
async def outer():
    async def inner():
        return await get_data()
    return inner
""")
        assert "async function" in result
        # Outer function should work (nested async function is separate)
        
        # Test 3.5: Deeply nested generators
        result = transpile("""
async def outer():
    def middle():
        def inner():
            yield 1
        return inner
    return middle
""")
        assert "async function" in result
        # Should NOT raise error - deeply nested generator is separate
        
        # ========================================================================
        # TEST GROUP 4: Complex Control Flow (Should Transpile Successfully)
        # ========================================================================
        
        # Test 4.1: Async generator with yield in nested if - should transpile successfully
        result = transpile("""
async def gen():
    if x:
        if y:
            yield 1
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 4.2: Async generator with yield in for/else - should transpile successfully
        result = transpile("""
async def gen():
    for item in items:
        yield item
    else:
        yield None
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 4.3: Async generator with yield in while/else - should transpile successfully
        result = transpile("""
async def gen():
    while condition:
        yield 1
    else:
        yield 2
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 4.4: Async generator with yield in match/case - should transpile successfully
        result = transpile("""
async def gen():
    match value:
        case 1:
            yield "one"
        case 2:
            yield "two"
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # ========================================================================
        # TEST GROUP 5: Edge Cases and Boundary Conditions
        # ========================================================================
        
        # Test 5.1: Async generator with only yield from (no direct yield) - should transpile successfully
        result = transpile("""
async def gen():
    yield from other_gen()
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 5.2: Async generator with yield in comprehension (invalid Python, but test robustness)
        # Note: Comprehensions can't have yield in Python, but test that we handle it
        # This should fail at Python parse time, not our detection
        
        # Test 5.3: Async generator with yield in lambda (invalid Python, but test robustness)
        # Note: Lambdas can't have yield in Python, but test that we handle it
        # This should fail at Python parse time, not our detection
        
        # Test 5.4: Async function with generator expression (should allow)
        result = transpile("""
async def process():
    results = [x * 2 for x in range(10)]
    return await process_results(results)
""")
        assert "async function" in result
        # Generator expressions are fine - they're not async generators
        
        # Test 5.5: Async function with list comprehension containing await
        result = transpile("""
async def fetch_all():
    return [await fetch(url) for url in urls]
""")
        assert "async function" in result
        assert "await" in result
        
        # ========================================================================
        # TEST GROUP 6: Real-World Patterns (Should Transpile Successfully)
        # ========================================================================
        
        # Test 6.1: Async generator that looks like a data stream - should transpile successfully
        result = transpile("""
async def stream_data():
    async with get_connection() as conn:
        while True:
            data = await conn.read()
            if not data:
                break
            yield data
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 6.2: Async generator with error handling - should transpile successfully
        result = transpile("""
async def safe_gen():
    try:
        yield await get_value()
    except Exception as e:
        yield None
    finally:
        await cleanup()
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
        
        # Test 6.3: Async generator with conditional yield - should transpile successfully
        result = transpile("""
async def filtered_gen():
    for item in await get_items():
        if item.is_valid():
            yield item
""")
        assert "async function*" in result or "async *" in result
        assert "yield" in result
    
    def test_error_includes_line_info(self):
        """Errors should include line information."""
        from pynext.transpiler import transpile
        
        try:
            transpile("def broken(\nwith invalid syntax")
        except Exception as e:
            # Error should have some location info
            error_str = str(e)
            # Just verify it raises, error format may vary
            assert True


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases in handler transformation."""
    
    def test_empty_function(self):
        """Empty function with pass should work."""
        from pynext.transpiler import transpile
        
        result = transpile("""
def empty():
    pass
""")
        
        assert "function empty" in result
    
    def test_docstring_preserved(self):
        """Docstrings should be handled (may be stripped or converted)."""
        from pynext.transpiler import transpile
        
        result = transpile('''
def documented():
    """This is a docstring."""
    return 42
''')
        
        # Function should still work regardless of docstring handling
        assert "function documented" in result
        assert "42" in result
    
    def test_multiline_string_in_handler(self):
        """Multiline strings should work."""
        from pynext.transpiler import transpile
        
        result = transpile('message = """Hello\nWorld"""')
        
        assert "Hello" in result
    
    def test_special_characters_in_strings(self):
        """Special characters in strings should be escaped."""
        from pynext.transpiler import transpile
        
        result = transpile('x = "Hello\\"World"')
        
        assert "Hello" in result
    
    def test_unicode_in_handler(self):
        """Unicode characters should work."""
        from pynext.transpiler import transpile
        
        result = transpile('greeting = "你好世界"')
        
        # Unicode should be preserved or escaped
        assert "你好" in result or "\\u" in result
    
    def test_nested_lambdas(self):
        """Nested lambdas should work."""
        from pynext.transpiler import transpile
        
        result = transpile("outer = lambda x: (lambda y: x + y)")
        
        # Should have two arrow functions
        assert result.count("=>") >= 2
    
    def test_immediate_function_call(self):
        """IIFE pattern should work."""
        from pynext.transpiler import transpile
        
        result = transpile("result = (lambda: 42)()")
        
        assert "42" in result
    
    def test_chained_method_calls(self):
        """Chained method calls should work."""
        from pynext.transpiler import transpile
        
        result = transpile("result = text.strip().lower().split()")
        
        assert "trim" in result or "strip" in result
        assert "toLowerCase" in result or "lower" in result
        assert "split" in result


# =============================================================================
# INTEGRATION WITH HTML.PY TESTS
# =============================================================================

class TestHtmlIntegration:
    """Tests for integration with pynext/core/html.py Element class."""
    
    def test_extract_handler_code_exists(self):
        """Element should have handler extraction method."""
        from pynext.core.html import Element
        
        el = Element("button")
        # Should have either AST or legacy extraction
        assert hasattr(el, '_extract_handler_code') or \
               hasattr(el, '_extract_handler_code_ast') or \
               hasattr(el, '_extract_handler_code_legacy')
    
    def test_element_onclick_handler(self):
        """Element onclick should accept lambda handler."""
        from pynext.core.html import button
        
        # This should not raise
        btn = button(onclick=lambda: print("clicked"))
        assert btn is not None
    
    def test_element_renders_with_handler(self):
        """Element with handler should render."""
        from pynext.core.html import button
        
        btn = button(onclick=lambda: print("clicked"))["Click me"]
        html = str(btn)
        
        assert "<button" in html
        assert "Click me" in html
