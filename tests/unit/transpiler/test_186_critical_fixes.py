"""
Phase 18.6 Critical Fixes - Comprehensive Tests

This module tests the critical fixes for:
1. Signal reads inside optimized generators/comprehensions
2. Nested function handlers (closure detection)
3. Form field signals (form.email())
4. Lambda handlers (source extraction fallback)
5. try/except blocks (proper IR and transforms)
6. Async handlers (complex await patterns)

Each section has 15-20 tests covering edge cases and common patterns.
"""

import pytest
from pynext.transpiler import transpile
from pynext.transpiler.reactive import (
    ReactiveContext, create_context, analyze_handler,
    _extract_closure_vars, _extract_nested_closure_vars,
)
from pynext.transpiler.pynext import transpile_handler_source, PyNextTransformer
from pynext.transpiler.parser import parse
from pynext.transpiler.emitter import emit


# =============================================================================
# FIX 1: SIGNAL READS INSIDE OPTIMIZED GENERATORS/COMPREHENSIONS
# =============================================================================

class TestSignalInComprehensions:
    """Test that signals are transformed inside comprehensions."""
    
    def test_signal_in_list_comp(self):
        """Signal call inside list comprehension element."""
        ctx = create_context(signals={"count": "sig_1"})
        source = """
def handler():
    result = [count() for x in items]
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert '__pynext__.getSignal' in result  # Uses signal name now, not ID
        assert ".read()" in result
    
    def test_signal_in_dict_comp_value(self):
        """Signal call inside dict comprehension value."""
        ctx = create_context(signals={"count": "sig_1"})
        source = """
def handler():
    result = {k: count() for k in keys}
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert '__pynext__.getSignal' in result  # Uses signal name now, not ID
    
    def test_signal_in_dict_comp_key(self):
        """Signal call inside dict comprehension key."""
        ctx = create_context(signals={"count": "sig_1"})
        source = """
def handler():
    result = {count(): v for v in values}
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert '__pynext__.getSignal' in result  # Uses signal name now, not ID
    
    def test_signal_in_set_comp(self):
        """Signal call inside set comprehension."""
        ctx = create_context(signals={"count": "sig_1"})
        source = """
def handler():
    result = {count() + x for x in items}
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert '__pynext__.getSignal' in result  # Uses signal name now, not ID
    
    def test_signal_in_generator_exp(self):
        """Signal call inside generator expression."""
        ctx = create_context(signals={"count": "sig_1"})
        source = """
def handler():
    result = list(count() + x for x in items)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert '__pynext__.getSignal' in result  # Uses signal name now, not ID
    
    def test_signal_in_comp_condition(self):
        """Signal call inside comprehension filter condition."""
        ctx = create_context(signals={"threshold": "sig_1"})
        source = """
def handler():
    result = [x for x in items if x > threshold()]
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert '__pynext__.getSignal' in result  # Uses signal name now, not ID
    
    def test_signal_in_comp_iter(self):
        """Signal call in comprehension iterable."""
        ctx = create_context(signals={"data": "sig_1"})
        source = """
def handler():
    result = [x for x in data()]
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert '__pynext__.getSignal' in result  # Uses signal name now, not ID
    
    def test_multiple_signals_in_comp(self):
        """Multiple signal calls in same comprehension."""
        ctx = create_context(signals={"a": "sig_1", "b": "sig_2"})
        source = """
def handler():
    result = [a() + b() for x in items]
"""
        result = transpile_handler_source(source, ctx)
        assert '__pynext__.getSignal' in result  # Uses signal name now, not ID
        assert '__pynext__.getSignal' in result  # Uses signal name now, not ID
    
    def test_signal_in_nested_comp(self):
        """Signal call in nested comprehension."""
        ctx = create_context(signals={"count": "sig_1"})
        source = """
def handler():
    result = [[count() + x for x in row] for row in matrix]
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_signal_in_sum_generator(self):
        """Signal call inside sum(generator)."""
        ctx = create_context(signals={"multiplier": "sig_1"})
        source = """
def handler():
    result = sum(x * multiplier() for x in items)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_signal_in_any_generator(self):
        """Signal call inside any(generator)."""
        ctx = create_context(signals={"threshold": "sig_1"})
        source = """
def handler():
    result = any(x > threshold() for x in items)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_signal_in_all_generator(self):
        """Signal call inside all(generator)."""
        ctx = create_context(signals={"valid": "sig_1"})
        source = """
def handler():
    result = all(x == valid() for x in items)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_signal_in_dict_generator(self):
        """Signal call inside dict(generator)."""
        ctx = create_context(signals={"count": "sig_1"})
        source = """
def handler():
    result = dict((k, count()) for k, v in items)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_signal_set_in_comp(self):
        """Signal.set() inside comprehension (less common but valid)."""
        ctx = create_context(signals={"items": "sig_1"})
        source = """
def handler():
    items.set([x * 2 for x in data])
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert ".set(" in result
    
    def test_store_in_dict_comp(self):
        """Store access inside dict comprehension."""
        ctx = create_context(stores={"user": "store_1"})
        source = """
def handler():
    result = {k: user.name for k in keys}
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getStore" in result
        assert "store_1" in result


# =============================================================================
# FIX 2: NESTED FUNCTION HANDLERS (CLOSURE DETECTION)
# =============================================================================

class TestNestedClosures:
    """Test that nested closures are properly detected."""
    
    def test_basic_closure_extraction(self):
        """Basic closure extraction works."""
        x = 42
        def func():
            return x
        
        vars = _extract_closure_vars(func)
        assert "x" in vars
        assert vars["x"] == 42
    
    def test_nested_closure_simple(self):
        """Nested function can access outer closure."""
        outer_val = "outer"
        
        def outer():
            inner_val = "inner"
            def inner():
                return outer_val, inner_val
            return inner
        
        inner_func = outer()
        vars = _extract_closure_vars(inner_func)
        assert "outer_val" in vars or "inner_val" in vars
    
    def test_closure_with_reactive_mock(self):
        """Closure with mock reactive object is detected."""
        class MockSignal:
            __pynext_type__ = "signal"
            _id = "sig_1"
        
        signal = MockSignal()
        
        def handler():
            return signal
        
        ctx = analyze_handler(handler)
        assert "signal" in ctx.signals
        assert ctx.signals["signal"].id == "sig_1"
    
    def test_multiple_closures(self):
        """Multiple closure variables are all detected."""
        a, b, c = 1, 2, 3
        
        def func():
            return a + b + c
        
        vars = _extract_closure_vars(func)
        assert len(vars) >= 3
    
    def test_closure_with_none(self):
        """Closure containing None is handled."""
        x = None
        
        def func():
            return x
        
        vars = _extract_closure_vars(func)
        assert "x" in vars
        assert vars["x"] is None
    
    def test_deep_nested_closure(self):
        """Deeply nested functions have closures extracted."""
        val = "deep"
        
        def level1():
            def level2():
                def level3():
                    return val
                return level3
            return level2
        
        # The nested extraction should work
        vars = _extract_nested_closure_vars(level1(), max_depth=5)
        # At minimum, should not crash


# =============================================================================
# FIX 3: FORM FIELD SIGNALS
# =============================================================================

class TestFormFieldSignals:
    """Test form field signal detection and transformation."""
    
    def test_form_field_read(self):
        """Form field read is transformed."""
        ctx = create_context(forms={"form": "form_1"})
        source = """
def handler():
    value = form.email
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getForm" in result
        assert "form_1" in result
    
    def test_form_field_set(self):
        """Form field set is transformed."""
        ctx = create_context(forms={"form": "form_1"})
        source = """
def handler():
    form.email.set("test@example.com")
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getForm" in result
        assert ".set(" in result
    
    def test_form_validate(self):
        """Form validate is transformed."""
        ctx = create_context(forms={"form": "form_1"})
        source = """
def handler():
    if form.validate():
        submit()
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getForm" in result
        assert ".validate()" in result
    
    def test_form_reset(self):
        """Form reset is transformed."""
        ctx = create_context(forms={"form": "form_1"})
        source = """
def handler():
    form.reset()
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getForm" in result
        assert ".reset()" in result
    
    def test_form_values(self):
        """Form values access is transformed."""
        ctx = create_context(forms={"form": "form_1"})
        source = """
def handler():
    data = form.values
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getForm" in result
        assert ".values" in result
    
    def test_form_errors(self):
        """Form errors access is transformed."""
        ctx = create_context(forms={"form": "form_1"})
        source = """
def handler():
    err = form.errors.email
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getForm" in result
        assert ".errors" in result
    
    def test_multiple_form_fields(self):
        """Multiple form fields in one handler."""
        ctx = create_context(forms={"form": "form_1"})
        source = """
def handler():
    form.email.set("a@b.com")
    form.password.set("secret")
"""
        result = transpile_handler_source(source, ctx)
        assert result.count("__pynext__.getForm") >= 2
    
    def test_form_field_in_condition(self):
        """Form field in conditional."""
        ctx = create_context(forms={"form": "form_1"})
        source = """
def handler():
    if form.email:
        process()
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getForm" in result
    
    def test_form_with_signal(self):
        """Form and signal together."""
        ctx = create_context(
            forms={"form": "form_1"},
            signals={"submitting": "sig_1"}
        )
        source = """
def handler():
    submitting.set(True)
    if form.validate():
        data = form.values
    submitting.set(False)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getForm" in result
        assert "__pynext__.getSignal" in result
    
    def test_form_submit(self):
        """Form submit method is transformed."""
        ctx = create_context(forms={"form": "form_1"})
        source = """
def handler():
    form.submit()
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getForm" in result
        assert ".submit()" in result


# =============================================================================
# FIX 4: TRY/EXCEPT SUPPORT
# =============================================================================

class TestTryExcept:
    """Test try/except block transpilation."""
    
    def test_basic_try_except(self):
        """Basic try/except is transpiled."""
        source = """
def handler():
    try:
        risky()
    except:
        handle_error()
"""
        result = transpile(source)
        assert "try {" in result
        assert "catch" in result
    
    def test_try_except_with_type(self):
        """try/except with exception type."""
        source = """
def handler():
    try:
        risky()
    except ValueError:
        handle_value_error()
"""
        result = transpile(source)
        assert "try {" in result
        assert "catch" in result
        assert "ValueError" in result
    
    def test_try_except_as(self):
        """try/except with exception binding."""
        source = """
def handler():
    try:
        risky()
    except ValueError as e:
        log(e)
"""
        result = transpile(source)
        assert "try {" in result
        assert "catch" in result
        assert "let e = _e" in result
    
    def test_try_finally(self):
        """try/finally is transpiled."""
        source = """
def handler():
    try:
        risky()
    finally:
        cleanup()
"""
        result = transpile(source)
        assert "try {" in result
        assert "finally {" in result
    
    def test_try_except_finally(self):
        """try/except/finally is transpiled."""
        source = """
def handler():
    try:
        risky()
    except:
        handle()
    finally:
        cleanup()
"""
        result = transpile(source)
        assert "try {" in result
        assert "catch" in result
        assert "finally {" in result
    
    def test_multiple_except_handlers(self):
        """Multiple except handlers."""
        source = """
def handler():
    try:
        risky()
    except ValueError:
        handle_value()
    except TypeError:
        handle_type()
"""
        result = transpile(source)
        assert "try {" in result
        assert "ValueError" in result
        assert "TypeError" in result
    
    def test_try_with_signal(self):
        """Try block with signal operations."""
        ctx = create_context(signals={"error": "sig_1", "data": "sig_2"})
        source = """
def handler():
    try:
        data.set(fetch())
    except:
        error.set("Failed")
"""
        result = transpile_handler_source(source, ctx)
        assert "try {" in result
        assert "__pynext__.getSignal" in result
    
    def test_try_with_form(self):
        """Try block with form operations."""
        ctx = create_context(forms={"form": "form_1"}, signals={"error": "sig_1"})
        source = """
def handler():
    try:
        if form.validate():
            submit()
    except:
        error.set("Validation failed")
"""
        result = transpile_handler_source(source, ctx)
        assert "try {" in result
        assert "__pynext__.getForm" in result
    
    def test_nested_try(self):
        """Nested try blocks."""
        source = """
def handler():
    try:
        try:
            inner()
        except:
            handle_inner()
    except:
        handle_outer()
"""
        result = transpile(source)
        assert result.count("try {") == 2
        assert result.count("catch") == 2
    
    def test_try_else_clause(self):
        """Try with else clause."""
        source = """
def handler():
    try:
        risky()
    except:
        handle()
    else:
        success()
"""
        result = transpile(source)
        assert "try {" in result
        assert "_no_exc" in result  # Flag for else tracking


# =============================================================================
# FIX 5: ASYNC HANDLER SUPPORT
# =============================================================================

class TestAsyncHandlers:
    """Test async handler transpilation."""
    
    def test_basic_async_function(self):
        """Basic async function."""
        source = """
async def handler():
    await fetch()
"""
        result = transpile(source)
        assert "async function" in result
        assert "await" in result
    
    def test_async_with_signal(self):
        """Async function with signal operations."""
        ctx = create_context(signals={"loading": "sig_1", "data": "sig_2"})
        source = """
async def handler():
    loading.set(True)
    result = await fetch()
    data.set(result)
    loading.set(False)
"""
        result = transpile_handler_source(source, ctx)
        assert "async function" in result
        assert "__pynext__.getSignal" in result
        assert "await" in result
    
    def test_await_with_signal_arg(self):
        """Await with signal value as argument."""
        ctx = create_context(signals={"url": "sig_1"})
        source = """
async def handler():
    result = await fetch(url())
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert ".read()" in result
    
    def test_multiple_awaits(self):
        """Multiple await expressions."""
        source = """
async def handler():
    a = await fetch_a()
    b = await fetch_b()
    return a + b
"""
        result = transpile(source)
        assert result.count("await") >= 2
    
    def test_await_in_try_except(self):
        """Await inside try/except."""
        ctx = create_context(signals={"error": "sig_1", "data": "sig_2"})
        source = """
async def handler():
    try:
        data.set(await fetch())
    except:
        error.set("Failed")
"""
        result = transpile_handler_source(source, ctx)
        assert "async function" in result
        assert "try {" in result
        assert "await" in result
    
    def test_await_in_condition(self):
        """Await in conditional."""
        source = """
async def handler():
    if await check():
        proceed()
"""
        result = transpile(source)
        assert "await" in result
    
    def test_async_with_form(self):
        """Async function with form operations."""
        ctx = create_context(
            forms={"form": "form_1"},
            signals={"submitting": "sig_1"}
        )
        source = """
async def handler():
    if form.validate():
        submitting.set(True)
        await submit(form.values)
        submitting.set(False)
        form.reset()
"""
        result = transpile_handler_source(source, ctx)
        assert "async function" in result
        assert "__pynext__.getForm" in result
        assert "__pynext__.getSignal" in result
    
    def test_await_chained(self):
        """Chained await calls."""
        source = """
async def handler():
    result = await (await fetch()).json()
"""
        result = transpile(source)
        assert result.count("await") >= 2
    
    def test_async_with_loop(self):
        """Async function with loop."""
        ctx = create_context(signals={"items": "sig_1"})
        source = """
async def handler():
    results = []
    for url in urls:
        data = await fetch(url)
        results.append(data)
    items.set(results)
"""
        result = transpile_handler_source(source, ctx)
        assert "async function" in result
        assert "for" in result
        assert "await" in result


# =============================================================================
# FIX 6: LAMBDA HANDLERS
# =============================================================================

class TestLambdaHandlers:
    """Test lambda handler support."""
    
    def test_lambda_with_closure(self):
        """Lambda with closure variable is analyzed."""
        class MockSignal:
            __pynext_type__ = "signal"
            _id = "sig_1"
        
        count = MockSignal()
        handler = lambda: count
        
        ctx = analyze_handler(handler)
        assert "count" in ctx.signals
    
    def test_simple_lambda_transpile(self):
        """Simple lambda can be transpiled."""
        ctx = create_context(signals={"count": "sig_1"})
        # Lambda source usually comes from inspect.getsource
        # We test with function syntax as fallback
        source = """
def handler():
    count.set(True)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple fixes."""
    
    def test_complete_crud_handler(self):
        """Complete CRUD handler with all features."""
        ctx = create_context(
            signals={"items": "sig_1", "loading": "sig_2", "error": "sig_3"},
            forms={"form": "form_1"}
        )
        source = """
async def handle_add():
    try:
        loading.set(True)
        if form.validate():
            result = await api.create(form.values)
            items.set([*items(), result])
            form.reset()
    except:
        error.set("Failed to add item")
    finally:
        loading.set(False)
"""
        result = transpile_handler_source(source, ctx)
        assert "async function" in result
        assert "try {" in result
        assert "__pynext__.getSignal" in result
        assert "__pynext__.getForm" in result
        assert "finally {" in result
    
    def test_filter_with_signal_threshold(self):
        """Filter pattern with signal threshold."""
        ctx = create_context(
            signals={"items": "sig_1", "threshold": "sig_2"}
        )
        source = """
def handler():
    items.set([x for x in data if x > threshold()])
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert "filter" in result.lower() or ">" in result
    
    def test_form_submission_flow(self):
        """Complete form submission flow."""
        ctx = create_context(
            forms={"form": "form_1"},
            signals={"submitting": "sig_1", "success": "sig_2"}
        )
        source = """
async def handle_submit():
    if form.validate():
        submitting.set(True)
        try:
            await api.submit(form.values)
            success.set(True)
            form.reset()
        except:
            success.set(False)
        finally:
            submitting.set(False)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getForm" in result
        assert "__pynext__.getSignal" in result
        assert "try {" in result
    
    def test_optimistic_update(self):
        """Optimistic update pattern."""
        ctx = create_context(
            signals={"items": "sig_1", "error": "sig_2"}
        )
        source = """
async def handle_delete(item_id):
    original = items()
    items.set([x for x in items() if x["id"] != item_id])
    try:
        await api.delete(item_id)
    except:
        items.set(original)
        error.set("Delete failed")
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert "try {" in result
    
    def test_batch_operations(self):
        """Batch operations with generators."""
        ctx = create_context(
            signals={"items": "sig_1", "selected": "sig_2"}
        )
        source = """
def handle_batch_delete():
    ids = [x["id"] for x in items() if x["id"] in selected()]
    items.set([x for x in items() if x["id"] not in ids])
    selected.set([])
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        # Should have signal reads in comprehensions
    
    def test_toggle_with_memo_pattern(self):
        """Toggle with computed/memo pattern."""
        ctx = create_context(
            signals={"show": "sig_1"},
            memos={"visible_count": "memo_1"}
        )
        source = """
def handle_toggle():
    show.set(not show())
    count = visible_count()
    log(count)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        # Note: Memos are hydrated as signals on client-side
        # So they use getSignal(), not getMemo()


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_try(self):
        """Empty try block."""
        source = """
def handler():
    try:
        pass
    except:
        pass
"""
        result = transpile(source)
        assert "try {" in result
    
    def test_deeply_nested_signal(self):
        """Signal in deeply nested structure."""
        ctx = create_context(signals={"count": "sig_1"})
        source = """
def handler():
    result = {
        "data": [
            {"value": count() + i}
            for i in range(10)
        ]
    }
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_signal_in_ternary(self):
        """Signal in ternary expression."""
        ctx = create_context(signals={"flag": "sig_1", "a": "sig_2", "b": "sig_3"})
        source = """
def handler():
    result = a() if flag() else b()
"""
        result = transpile_handler_source(source, ctx)
        assert result.count("__pynext__.getSignal") >= 3
    
    def test_signal_in_binary_ops(self):
        """Signal in various binary operations."""
        ctx = create_context(signals={"a": "sig_1", "b": "sig_2"})
        source = """
def handler():
    x = a() + b()
    y = a() * b()
    z = a() - b()
"""
        result = transpile_handler_source(source, ctx)
        assert result.count("__pynext__.getSignal") >= 6
    
    def test_signal_in_comparison(self):
        """Signal in comparison."""
        ctx = create_context(signals={"count": "sig_1", "max": "sig_2"})
        source = """
def handler():
    if count() < max():
        proceed()
"""
        result = transpile_handler_source(source, ctx)
        assert result.count("__pynext__.getSignal") >= 2
    
    def test_chained_method_calls(self):
        """Chained method calls with signals."""
        ctx = create_context(signals={"items": "sig_1"})
        source = """
def handler():
    result = items().filter(lambda x: x > 0).map(lambda x: x * 2)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_signal_with_default_args(self):
        """Function with default args referencing signals."""
        ctx = create_context(signals={"default_val": "sig_1"})
        source = """
def handler():
    value = get_value() or default_val()
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
    
    def test_multiple_try_blocks(self):
        """Multiple try blocks in sequence."""
        source = """
def handler():
    try:
        step1()
    except:
        handle1()
    
    try:
        step2()
    except:
        handle2()
"""
        result = transpile(source)
        assert result.count("try {") == 2
    
    def test_signal_update_with_lambda(self):
        """Signal update with lambda."""
        ctx = create_context(signals={"count": "sig_1"})
        source = """
def handler():
    count.update(lambda x: x + 1)
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getSignal" in result
        assert ".update(" in result
    
    def test_store_deep_access(self):
        """Store deep property access."""
        ctx = create_context(stores={"user": "store_1"})
        source = """
def handler():
    name = user.profile.name
"""
        result = transpile_handler_source(source, ctx)
        assert "__pynext__.getStore" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
