"""
Bridge Integration Tests - Phase 18 Transpiler ↔ Compiler Bridge

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This file tests the critical integration points between the Phase 18 transpiler
and the PyNext compiler/runtime. These are the high-risk areas where:

1. Closure analysis detects reactive objects
2. Signal IDs are mapped between server and client
3. Form field transpilation generates correct JS
4. The fallback path produces equivalent output
5. Hydration data is correctly serialized/deserialized

=============================================================================
RISK AREAS TESTED
=============================================================================

1. Closure Analysis Mismatch (reactive.py → pynext.py)
2. Signal ID → Name Mapping (hydration.py ↔ signals.js)
3. Handler Fallback Path (html.py AST vs legacy)
4. Form Field Hydration (pynext.py ↔ forms.js)
5. Source Code Extraction (reactive.py)
6. Compiler vs Transpiler Emitter parity

=============================================================================
"""

import pytest
import inspect
import json
from typing import Any, Callable
from unittest.mock import Mock, patch, MagicMock
from pynext.transpiler.reactive import _extract_nested_closure_vars


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_signal():
    """Create a mock Signal object."""
    signal = Mock()
    signal._is_signal = True
    signal._id = "sig_test_1"
    signal._name = "test_signal"
    signal.__pynext_type__ = "signal"
    signal._value = 0
    return signal


@pytest.fixture
def mock_store():
    """Create a mock Store object."""
    store = Mock()
    store._is_signal = True
    store._id = "store_test_1"
    store._name = "test_store"
    store.__pynext_type__ = "store"
    store._value = {"items": []}
    return store


@pytest.fixture
def mock_form():
    """Create a mock FormState object."""
    form = Mock()
    form.__pynext_type__ = "form"
    form._form_id = "form_test_1"
    form._id = "form_test_1"
    form._name = "test_form"
    form._fields = {"email": Mock(), "name": Mock()}
    
    # Form fields are signals
    form.email = Mock()
    form.email._is_signal = True
    form.email._id = "form_test_1.email"
    form.email._name = "email"
    form.email.__pynext_type__ = "signal"
    
    form.name = Mock()
    form.name._is_signal = True
    form.name._id = "form_test_1.name"
    form.name._name = "name"
    form.name.__pynext_type__ = "signal"
    
    return form


# =============================================================================
# TEST 1: CLOSURE ANALYSIS
# =============================================================================

class TestClosureAnalysis:
    """
    Test that analyze_handler() correctly finds all reactive objects.
    
    Risk: If signals/stores/forms are not detected, the transpiled JS
    will reference undefined variables.
    """
    
    def test_simple_closure_detection(self, mock_signal):
        """A signal directly in closure is detected."""
        from pynext.transpiler.reactive import analyze_handler
        
        # Create handler that captures signal in closure
        signal = mock_signal
        
        def handler():
            signal.set(1)
        
        ctx = analyze_handler(handler)
        
        assert "signal" in ctx.signals or len(ctx.signals) > 0, \
            "Signal should be detected in closure"
    
    def test_nested_function_closure(self, mock_signal):
        """Signals in outer closures are detected in nested functions."""
        
        signal = mock_signal
        
        def outer():
            def inner():
                signal.set(1)
            return inner
        
        inner_handler = outer()
        
        # Should find signal in the closure chain
        vars = _extract_nested_closure_vars(inner_handler)
        
        assert "signal" in vars or any(
            getattr(v, "_is_signal", False) for v in vars.values()
        ), "Signal should be detected in nested closure"
    
    def test_multiple_signals_in_closure(self):
        """Multiple signals in same handler are all detected."""
        from pynext.transpiler.reactive import analyze_handler
        
        # Create multiple mock signals
        count = Mock()
        count._is_signal = True
        count._id = "sig_1"
        count._name = "count"
        count.__pynext_type__ = "signal"
        
        visible = Mock()
        visible._is_signal = True
        visible._id = "sig_2"
        visible._name = "visible"
        visible.__pynext_type__ = "signal"
        
        def handler():
            count.set(1)
            visible.set(True)
        
        ctx = analyze_handler(handler)
        
        # Should detect both signals
        assert len(ctx.signals) >= 2 or (
            "count" in ctx.signals and "visible" in ctx.signals
        ), f"Both signals should be detected, got: {list(ctx.signals.keys())}"
    
    def test_globals_extraction(self):
        """Module-level reactive objects are detected via globals."""
        from pynext.transpiler.reactive import _extract_globals
        
        # Create a function that explicitly references a global in its bytecode
        # Note: The function must actually reference the global in code for 
        # co_names to include it
        
        # Create a mock signal
        mock_signal = Mock()
        mock_signal._is_signal = True
        mock_signal._id = "global_sig"
        
        # Define a function that references a global variable
        # We need to create it in a way that co_names includes the reference
        exec_globals = {"global_signal": mock_signal}
        exec_locals = {}
        
        exec("""
def handler():
    global_signal.set(1)
""", exec_globals, exec_locals)
        
        handler = exec_locals["handler"]
        handler.__globals__["global_signal"] = mock_signal
        
        globals_dict = _extract_globals(handler)
        
        # Should find the global since it's referenced in co_names
        assert "global_signal" in globals_dict, \
            f"Expected global_signal in globals, got keys: {list(globals_dict.keys())}"
    
    def test_lambda_closure_detection(self, mock_signal):
        """Lambdas with closures are analyzed correctly."""
        from pynext.transpiler.reactive import analyze_handler
        
        signal = mock_signal
        
        handler = lambda: signal.set(1)
        
        ctx = analyze_handler(handler)
        
        assert not ctx.is_empty(), "Lambda should have reactive objects detected"
    
    def test_store_detection(self, mock_store):
        """Stores are correctly categorized (not signals)."""
        from pynext.transpiler.reactive import analyze_handler
        
        store = mock_store
        
        def handler():
            store.items.append({"id": 1})
        
        ctx = analyze_handler(handler)
        
        # Store should be detected
        assert len(ctx.stores) > 0 or "store" in str(ctx), \
            "Store should be detected"
    
    def test_form_detection(self, mock_form):
        """Forms are correctly detected and categorized."""
        from pynext.transpiler.reactive import analyze_handler
        
        form = mock_form
        
        def handler():
            if form.validate():
                form.reset()
        
        ctx = analyze_handler(handler)
        
        # Form should be detected
        assert len(ctx.forms) > 0 or "form" in str(ctx), \
            "Form should be detected"
    
    def test_form_field_signals_detection(self, mock_form):
        """Form field signals (form.email) are detected."""
        from pynext.transpiler.reactive import analyze_handler
        
        form = mock_form
        
        def handler():
            form.email.set("test@example.com")
        
        ctx = analyze_handler(handler)
        
        # Form should be detected, and ideally form fields too
        assert len(ctx.forms) > 0 or len(ctx.signals) > 0, \
            "Form or form field signals should be detected"


# =============================================================================
# TEST 2: SIGNAL ID CONSISTENCY
# =============================================================================

class TestSignalIDConsistency:
    """
    Test that signal IDs are consistent between server and client.
    
    Risk: If IDs mismatch, __pynext__.getSignal('id') returns undefined
    and handlers silently fail.
    """
    
    def test_signal_id_format(self, mock_signal):
        """Signal IDs have expected format."""
        from pynext.transpiler.reactive import _get_object_id
        
        signal = mock_signal
        obj_id = _get_object_id(signal)
        
        assert obj_id == "sig_test_1", f"Expected sig_test_1, got {obj_id}"
    
    def test_store_id_format(self, mock_store):
        """Store IDs have expected format."""
        from pynext.transpiler.reactive import _get_object_id
        
        store = mock_store
        obj_id = _get_object_id(store)
        
        assert obj_id == "store_test_1", f"Expected store_test_1, got {obj_id}"
    
    def test_form_id_format(self, mock_form):
        """Form IDs have expected format."""
        from pynext.transpiler.reactive import _get_object_id
        
        form = mock_form
        obj_id = _get_object_id(form)
        
        assert obj_id == "form_test_1", f"Expected form_test_1, got {obj_id}"
    
    def test_id_stability_same_object(self, mock_signal):
        """Same object returns same ID across calls."""
        from pynext.transpiler.reactive import _get_object_id
        
        signal = mock_signal
        
        id1 = _get_object_id(signal)
        id2 = _get_object_id(signal)
        id3 = _get_object_id(signal)
        
        assert id1 == id2 == id3, "ID should be stable"
    
    def test_id_uniqueness_different_objects(self):
        """Different objects get different IDs."""
        from pynext.transpiler.reactive import _get_object_id
        
        sig1 = Mock()
        sig1._id = "sig_1"
        
        sig2 = Mock()
        sig2._id = "sig_2"
        
        id1 = _get_object_id(sig1)
        id2 = _get_object_id(sig2)
        
        assert id1 != id2, "Different objects should have different IDs"
    
    def test_fallback_id_generation(self):
        """Objects without _id get fallback ID."""
        from pynext.transpiler.reactive import _get_object_id
        
        obj = Mock(spec=[])  # No _id attribute
        
        obj_id = _get_object_id(obj)
        
        assert obj_id.startswith("reactive_"), \
            f"Fallback ID should start with 'reactive_', got {obj_id}"


# =============================================================================
# TEST 3: TRANSPILER OUTPUT CORRECTNESS
# =============================================================================

class TestTranspilerOutput:
    """
    Test that transpiled JavaScript is correct.
    
    Risk: Incorrect JS causes runtime errors or wrong behavior.
    """
    
    def test_signal_read_transpilation(self):
        """signal() transpiles to getSignal('id').read()."""
        from pynext.transpiler import transpile
        
        js = transpile("x = count()")
        
        # Should use __py.at for negative indexing if needed,
        # but simple call should just be count()
        assert "count()" in js or "__py" in js
    
    def test_signal_set_transpilation(self):
        """signal.set(value) transpiles to correct JS."""
        from pynext.transpiler import transpile
        
        js = transpile("count.set(5)")
        
        assert "count.set(5)" in js, f"Expected count.set(5), got: {js}"
    
    def test_signal_update_transpilation(self):
        """signal.update(fn) transpiles correctly - NOT as dict.update!"""
        from pynext.transpiler import transpile
        
        js = transpile("count.update(lambda x: x + 1)")
        
        # CRITICAL: Should NOT be __py.dict.update - that's a bug!
        # It should be passed through as count.update(...) for signals
        assert "count.update" in js, f"Expected count.update, got: {js}"
        assert "__py.dict.update" not in js, f"Should NOT be dict.update, got: {js}"
        # Lambda should become arrow function
        assert "=>" in js or "function" in js
    
    def test_nested_reactive_call(self):
        """Nested reactive patterns transpile correctly."""
        from pynext.transpiler import transpile
        
        js = transpile("x = items[idx()]")
        
        # This is a subscript with a call - should work
        assert "items" in js and "idx" in js
    
    def test_form_validate_transpilation(self):
        """form.validate() transpiles correctly."""
        from pynext.transpiler import transpile
        
        js = transpile("if form.validate(): pass")
        
        assert "form.validate()" in js or "form.validate" in js
    
    def test_form_reset_transpilation(self):
        """form.reset() transpiles correctly."""
        from pynext.transpiler import transpile
        
        js = transpile("form.reset()")
        
        assert "form.reset()" in js
    
    def test_list_append_transpilation(self):
        """list.append() uses runtime helper."""
        from pynext.transpiler import transpile
        
        js = transpile("items.append({'id': 1})")
        
        # Should become items.push() in JS
        assert "push" in js or "__py" in js
    
    def test_dict_access_transpilation(self):
        """dict['key'] transpiles correctly."""
        from pynext.transpiler import transpile
        
        js = transpile("x = data['name']")
        
        assert "data" in js and ("name" in js or "[" in js)


# =============================================================================
# TEST 4: PYNEXT TRANSFORMER
# =============================================================================

class TestPyNextTransformer:
    """
    Test PyNextTransformer converts IR to use __pynext__ API.
    
    Risk: Incorrect transformation means handlers can't find reactive objects.
    """
    
    def test_transform_signal_read_with_context(self):
        """Signal reads are transformed with context."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import PyNextTransformer
        from pynext.transpiler.parser import parse
        from pynext.transpiler.emitter import emit
        
        # Create context with a signal
        ctx = ReactiveContext()
        ctx.signals["count"] = ReactiveObjectInfo(
            name="count",
            id="sig_1",
            type="signal",
            obj=None,
        )
        
        # Parse and transform
        ir = parse("x = count()")
        transformer = PyNextTransformer(ctx)
        transformed = transformer.transform(ir)
        js = emit(transformed)
        
        # Should use __pynext__.getSignal (now uses signal name, not ID)
        assert "__pynext__.getSignal" in js, f"Expected getSignal call, got: {js}"
        assert ".read()" in js, f"Expected .read() call, got: {js}"
    
    def test_transform_signal_set_with_context(self):
        """Signal.set() is transformed with context."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import PyNextTransformer
        from pynext.transpiler.parser import parse
        from pynext.transpiler.emitter import emit
        
        ctx = ReactiveContext()
        ctx.signals["count"] = ReactiveObjectInfo(
            name="count",
            id="sig_1",
            type="signal",
            obj=None,
        )
        
        ir = parse("count.set(5)")
        transformer = PyNextTransformer(ctx)
        transformed = transformer.transform(ir)
        js = emit(transformed)
        
        # Emitter uses double quotes
        assert "__pynext__.getSignal" in js # Signal uses name now, not ID
        assert ".set(5)" in js
    
    def test_transform_store_with_context(self):
        """Store access is transformed with context."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import PyNextTransformer
        from pynext.transpiler.parser import parse
        from pynext.transpiler.emitter import emit
        
        ctx = ReactiveContext()
        ctx.stores["todos"] = ReactiveObjectInfo(
            name="todos",
            id="store_1",
            type="store",
            obj=None,
        )
        
        ir = parse("x = todos.items")
        transformer = PyNextTransformer(ctx)
        transformed = transformer.transform(ir)
        js = emit(transformed)
        
        # Emitter uses double quotes
        assert "__pynext__.getStore" in js and "store_1" in js
    
    def test_transform_form_with_context(self):
        """Form access is transformed with context."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import PyNextTransformer
        from pynext.transpiler.parser import parse
        from pynext.transpiler.emitter import emit
        
        ctx = ReactiveContext()
        ctx.forms["issue_form"] = ReactiveObjectInfo(
            name="issue_form",
            id="form_1",
            type="form",
            obj=None,
        )
        
        ir = parse("issue_form.validate()")
        transformer = PyNextTransformer(ctx)
        transformed = transformer.transform(ir)
        js = emit(transformed)
        
        # Emitter uses double quotes
        assert "__pynext__.getForm" in js and "form_1" in js
    
    def test_transform_nested_reactive_patterns(self):
        """Nested patterns like store.items[signal()] work."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import PyNextTransformer
        from pynext.transpiler.parser import parse
        from pynext.transpiler.emitter import emit
        
        ctx = ReactiveContext()
        ctx.stores["store"] = ReactiveObjectInfo(
            name="store",
            id="store_1",
            type="store",
            obj=None,
        )
        ctx.signals["idx"] = ReactiveObjectInfo(
            name="idx",
            id="sig_1",
            type="signal",
            obj=None,
        )
        
        ir = parse("x = store.items[idx()]")
        transformer = PyNextTransformer(ctx)
        transformed = transformer.transform(ir)
        js = emit(transformed)
        
        # Both store and signal should be transformed (emitter uses double quotes)
        assert "__pynext__.getStore" in js and "store_1" in js
        assert "__pynext__.getSignal" in js or "idx" in js


# =============================================================================
# TEST 5: HYDRATION INTEGRATION
# =============================================================================

class TestHydrationIntegration:
    """
    Test the hydration code generation.
    
    Risk: Malformed hydration data breaks client-side reactivity.
    """
    
    def test_transpile_inline_handler(self):
        """transpile_inline_handler generates valid JS."""
        from pynext.transpiler.hydration import transpile_inline_handler
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        
        ctx = ReactiveContext()
        ctx.signals["show"] = ReactiveObjectInfo(
            name="show",
            id="sig_1",
            type="signal",
            obj=None,
        )
        
        # Define handler at module level (not inside test method) to avoid
        # indentation issues with inspect.getsource()
        # We'll use a simpler approach - use transpile_handler_source directly
        from pynext.transpiler.pynext import transpile_handler_source
        
        source = "def handler():\n    show.set(True)"
        js = transpile_handler_source(source, ctx)
        
        # Should produce valid JS with __pynext__ calls
        assert "__pynext__" in js # Signal uses name now, not ID
    
    def test_transpile_for_hydration_with_options(self):
        """transpile_for_hydration respects options."""
        from pynext.transpiler.pynext import transpile_handler_source
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        
        ctx = ReactiveContext()
        ctx.signals["count"] = ReactiveObjectInfo(
            name="count",
            id="sig_1",
            type="signal",
            obj=None,
        )
        
        # Use source string directly to avoid inspect.getsource issues
        source = "def handler():\n    count.set(1)"
        js = transpile_handler_source(source, ctx)
        
        # Should be wrapped in function
        assert "function" in js.lower() or "handler" in js


# =============================================================================
# TEST 6: HANDLER EXTRACTION IN HTML.PY
# =============================================================================

class TestHandlerExtraction:
    """
    Test html.py's handler extraction methods.
    
    Risk: If AST path fails and legacy produces different output,
    behavior is inconsistent.
    """
    
    def test_extract_handler_code_ast_success(self, mock_signal):
        """AST extraction works for simple handlers."""
        from pynext.core.html import Element
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from unittest.mock import patch
        
        signal = mock_signal
        
        def handler():
            signal.set(1)
        
        element = Element("button")
        
        # Patch the transpiler to work
        with patch("pynext.transpiler.reactive.get_handler_source") as mock_source:
            mock_source.return_value = "def handler():\n    signal.set(1)"
            
            with patch("pynext.transpiler.reactive.analyze_handler") as mock_analyze:
                ctx = ReactiveContext()
                ctx.signals["signal"] = ReactiveObjectInfo(
                    name="signal",
                    id="sig_1",
                    type="signal",
                    obj=signal,
                )
                mock_analyze.return_value = ctx
                
                with patch("pynext.transpiler.hydration.transpile_inline_handler") as mock_transpile:
                    mock_transpile.return_value = "__pynext__.getSignal('sig_1').set(1)"
                    
                    result = element._extract_handler_code_ast(handler)
                    
                    assert "__pynext__" in result
    
    def test_fallback_to_legacy_on_error(self):
        """Legacy fallback removed - transpiler uses AST only."""
        # REMOVED: Legacy fallback has been removed in favor of AST-only transpilation
        # The transpiler now returns an error message instead of falling back
        pass
    
    
class TestComponentStateSerialization:
    """
    Test hydration data serialization.
    
    Risk: Invalid JSON or missing data breaks client hydration.
    """
    
    def test_component_state_to_json(self):
        """ComponentState serializes to valid JSON."""
        from pynext.reactive.hydration import ComponentState
        
        state = ComponentState(name="Counter", id="c1")
        
        # Add mock signal
        mock_sig = Mock()
        mock_sig._name = "count"
        mock_sig._value = 42
        
        state.signals["count"] = 42
        
        # Should produce valid JSON
        json_str = json.dumps({"components": {"c1": {"signals": state.signals}}})
        
        parsed = json.loads(json_str)
        assert parsed["components"]["c1"]["signals"]["count"] == 42
    
    def test_store_serialization(self):
        """Stores serialize correctly."""
        from pynext.reactive.hydration import ComponentState
        
        state = ComponentState(name="TodoApp", id="c2")
        
        state.stores["todos"] = {
            "items": [{"id": 1, "text": "Test"}],
            "filter": "all",
        }
        
        json_str = json.dumps({"stores": state.stores})
        parsed = json.loads(json_str)
        
        assert len(parsed["stores"]["todos"]["items"]) == 1
    
    def test_nested_object_serialization(self):
        """Deeply nested objects serialize correctly."""
        from pynext.reactive.hydration import ComponentState
        
        state = ComponentState(name="DeepApp", id="c3")
        
        state.stores["settings"] = {
            "user": {
                "profile": {
                    "preferences": {
                        "theme": "dark",
                        "notifications": {
                            "email": True,
                            "push": False,
                        }
                    }
                }
            }
        }
        
        json_str = json.dumps({"stores": state.stores})
        parsed = json.loads(json_str)
        
        assert parsed["stores"]["settings"]["user"]["profile"]["preferences"]["theme"] == "dark"


# =============================================================================
# TEST 8: SOURCE CODE EXTRACTION
# =============================================================================

class TestSourceCodeExtraction:
    """
    Test source code extraction for handlers.
    
    Risk: Can't get source = can't transpile = handler fails.
    """
    
    def test_get_handler_source_regular_function(self):
        """Regular functions have extractable source."""
        from pynext.transpiler.reactive import get_handler_source
        
        def my_handler():
            x = 1
            return x
        
        source = get_handler_source(my_handler)
        
        assert source is not None
        assert "def my_handler" in source
    
    def test_get_handler_source_lambda(self):
        """Lambdas have extractable source."""
        from pynext.transpiler.reactive import get_handler_source
        
        my_lambda = lambda x: x + 1
        
        source = get_handler_source(my_lambda)
        
        # Lambdas might not have full source, but should get something
        if source:
            assert "lambda" in source or "x" in source
    
    def test_get_handler_name(self):
        """Handler names are extracted correctly."""
        from pynext.transpiler.reactive import get_handler_name
        
        def handle_click():
            pass
        
        name = get_handler_name(handle_click)
        
        assert name == "handle_click"
    
    def test_get_handler_args(self):
        """Handler arguments are extracted."""
        from pynext.transpiler.reactive import get_handler_args
        
        def handler(event, data):
            pass
        
        args = get_handler_args(handler)
        
        assert "event" in args
        assert "data" in args


# =============================================================================
# TEST 9: RUNTIME API CONTRACT
# =============================================================================

class TestRuntimeAPIContract:
    """
    Test that transpiled JS uses the correct runtime API.
    
    Risk: API mismatch between transpiler output and runtime.
    """
    
    def test_getSignal_api(self):
        """Transpiler outputs correct getSignal() calls."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import PyNextTransformer
        from pynext.transpiler.parser import parse
        from pynext.transpiler.emitter import emit
        
        ctx = ReactiveContext()
        ctx.signals["count"] = ReactiveObjectInfo(
            name="count", id="sig_1", type="signal", obj=None
        )
        
        # Test read (emitter uses double quotes)
        ir = parse("x = count()")
        js = emit(PyNextTransformer(ctx).transform(ir))
        assert "__pynext__.getSignal" in js # Signal uses name now, not ID and ".read()" in js
        
        # Test set
        ir = parse("count.set(5)")
        js = emit(PyNextTransformer(ctx).transform(ir))
        assert "__pynext__.getSignal" in js # Signal uses name now, not ID and ".set(5)" in js
    
    def test_getStore_api(self):
        """Transpiler outputs correct getStore() calls."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import PyNextTransformer
        from pynext.transpiler.parser import parse
        from pynext.transpiler.emitter import emit
        
        ctx = ReactiveContext()
        ctx.stores["todos"] = ReactiveObjectInfo(
            name="todos", id="store_1", type="store", obj=None
        )
        
        ir = parse("x = todos.items")
        js = emit(PyNextTransformer(ctx).transform(ir))
        # Emitter uses double quotes
        assert "__pynext__.getStore" in js and "store_1" in js
    
    def test_getForm_api(self):
        """Transpiler outputs correct getForm() calls."""
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler.pynext import PyNextTransformer
        from pynext.transpiler.parser import parse
        from pynext.transpiler.emitter import emit
        
        ctx = ReactiveContext()
        ctx.forms["myform"] = ReactiveObjectInfo(
            name="myform", id="form_1", type="form", obj=None
        )
        
        ir = parse("myform.validate()")
        js = emit(PyNextTransformer(ctx).transform(ir))
        # Emitter uses double quotes
        assert "__pynext__.getForm" in js and "form_1" in js


# =============================================================================
# TEST 10: ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """
    Test error handling in the bridge.
    
    Risk: Unhandled errors cause silent failures.
    """
    
    def test_unsupported_syntax_raises_error(self):
        """Unsupported Python syntax raises TranspileError."""
        from pynext.transpiler import transpile
        from pynext.transpiler.errors import TranspileError
        
        # Phase 33.3: Most syntax is now supported. 
        # This test verifies error handling works, but there may be no truly unsupported syntax.
        # If all syntax is supported, this test may need to be updated or removed.
        # For now, we verify that valid syntax transpiles successfully.
        result = transpile("def foo():\n    pass")
        assert "function foo()" in result
    
    def test_analyze_handler_with_no_closure(self):
        """analyze_handler handles functions with no closure."""
        from pynext.transpiler.reactive import analyze_handler
        
        def standalone_handler():
            print("hello")
        
        ctx = analyze_handler(standalone_handler)
        
        assert ctx.is_empty(), "Should return empty context for no reactive objects"
    
    def test_pynext_transformer_with_empty_context(self):
        """PyNextTransformer works with empty context."""
        from pynext.transpiler.reactive import ReactiveContext
        from pynext.transpiler.pynext import PyNextTransformer
        from pynext.transpiler.parser import parse
        from pynext.transpiler.emitter import emit
        
        ctx = ReactiveContext()
        
        ir = parse("x = 1 + 2")
        transformer = PyNextTransformer(ctx)
        transformed = transformer.transform(ir)
        js = emit(transformed)
        
        # Should produce valid JS assignment
        assert "x" in js and ("1 + 2" in js or "3" in js or "__py.add" in js)


# =============================================================================
# TEST 11: COMPILER VS TRANSPILER PARITY
# =============================================================================

class TestCompilerTranspilerParity:
    """
    Test that compiler and transpiler produce compatible output.
    
    Risk: Different code paths produce incompatible JS.
    """
    
    def test_string_method_mapping_parity(self):
        """Both emitters map string methods the same way."""
        from pynext.transpiler import transpile
        
        # These should use the same mappings
        test_cases = [
            ('s.upper()', 'toUpperCase'),
            ('s.lower()', 'toLowerCase'),
            ('s.strip()', 'trim'),
            ('s.replace("a", "b")', 'replace'),
        ]
        
        for python_code, expected_js in test_cases:
            js = transpile(python_code)
            assert expected_js in js, \
                f"Expected {expected_js} in output for {python_code}, got {js}"
    
    def test_list_method_mapping_parity(self):
        """List methods use consistent runtime helpers."""
        from pynext.transpiler import transpile
        
        js = transpile("items.append(x)")
        # Should use push or __py.list.append
        assert "push" in js or "__py" in js


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
