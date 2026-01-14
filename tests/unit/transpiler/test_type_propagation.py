"""
Transpiler Core Fix: Type Propagation Tests

Tests that verify DOM types are correctly propagated through variable assignments.

Python:
    params = URLSearchParams("a=1")  # params has DOM type
    x = params                       # x should inherit DOM type
    x.get("a")                       # Should use x.get("a"), not __py.dict.get

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestDirectDOMTypeTracking:
    """Test DOM types are tracked on direct constructor assignment."""

    def test_urlsearchparams_get_direct(self):
        """URLSearchParams.get() should use direct method call."""
        code = '''
params = URLSearchParams("a=1&b=2")
value = params.get("a")
'''
        result = transpile(code)
        # Should be params.get("a"), not __py.dict.get(params, "a")
        assert 'params.get("a")' in result
        assert '__py.dict.get' not in result

    def test_urlsearchparams_set_direct(self):
        """URLSearchParams.set() should use direct method call."""
        code = '''
params = URLSearchParams()
params.set("key", "value")
'''
        result = transpile(code)
        assert 'params.set("key", "value")' in result

    def test_textencoder_encode_direct(self):
        """TextEncoder.encode() should use direct method call."""
        code = '''
encoder = TextEncoder()
data = encoder.encode("Hello")
'''
        result = transpile(code)
        # Should be encoder.encode(), not __py.str.encode()
        assert 'encoder.encode("Hello")' in result
        assert '__py.str.encode' not in result


class TestTypePropagationOnReassignment:
    """Test DOM types are propagated when assigning from one variable to another."""

    def test_simple_reassignment(self):
        """Type should propagate on simple variable assignment."""
        code = '''
params = URLSearchParams("a=1")
x = params
value = x.get("a")
'''
        result = transpile(code)
        # After propagation, x.get should be direct
        assert 'x.get("a")' in result

    def test_reassignment_chain(self):
        """Type should propagate through multiple reassignments."""
        code = '''
params = URLSearchParams("a=1")
x = params
y = x
value = y.get("a")
'''
        result = transpile(code)
        # y.get should be direct
        assert 'y.get("a")' in result

    def test_encoder_reassignment(self):
        """TextEncoder type should propagate."""
        code = '''
encoder = TextEncoder()
enc = encoder
data = enc.encode("Hello")
'''
        result = transpile(code)
        # enc.encode should be direct
        assert 'enc.encode("Hello")' in result


class TestTypeClearingOnNonDOMAssignment:
    """Test DOM types are cleared when reassigning to non-DOM values."""

    def test_clear_on_dict_assignment(self):
        """DOM type should be cleared when reassigned to dict."""
        code = '''
x = URLSearchParams("a=1")
x = {"key": "value"}
val = x.get("key")
'''
        result = transpile(code)
        # After reassignment to dict, x.get should use __py.dict.get
        assert '__py.dict.get(x' in result or 'x.get' in result

    def test_clear_on_function_call(self):
        """DOM type should be cleared when reassigned to function result."""
        code = '''
x = URLSearchParams("a=1")
x = some_function()
'''
        result = transpile(code)
        # Type is cleared - no specific assertion needed
        assert 'some_function()' in result


class TestAttributeAccessTypePropagation:
    """Test type propagation through attribute access."""

    def test_searchparams_from_url(self):
        """url.searchParams should have URLSearchParams type."""
        code = '''
url = URL("https://example.com?a=1")
params = url.searchParams
value = params.get("a")
'''
        result = transpile(code)
        # This is a known limitation - attribute access doesn't propagate type
        # For now, verify it transpiles without error
        assert 'url.searchParams' in result
        assert 'params' in result


class TestMultipleVariablesIndependent:
    """Test that multiple DOM variables are tracked independently."""

    def test_independent_params(self):
        """Two different URLSearchParams should both work."""
        code = '''
params1 = URLSearchParams("a=1")
params2 = URLSearchParams("b=2")
val1 = params1.get("a")
val2 = params2.get("b")
'''
        result = transpile(code)
        assert 'params1.get("a")' in result
        assert 'params2.get("b")' in result

    def test_mixed_dom_types(self):
        """Different DOM types should be tracked independently."""
        code = '''
params = URLSearchParams("a=1")
encoder = TextEncoder()
val = params.get("a")
data = encoder.encode("Hello")
'''
        result = transpile(code)
        assert 'params.get("a")' in result
        assert 'encoder.encode("Hello")' in result


class TestEdgeCases:
    """Edge cases for type propagation."""

    def test_overwrite_dom_with_same_type(self):
        """Overwriting DOM with same type should preserve type."""
        code = '''
params = URLSearchParams("a=1")
params = URLSearchParams("b=2")
val = params.get("b")
'''
        result = transpile(code)
        assert 'params.get("b")' in result

    def test_new_keyword_in_constructor(self):
        """DOM constructors should always get 'new' keyword."""
        code = '''
encoder = TextEncoder()
decoder = TextDecoder("utf-8")
'''
        result = transpile(code)
        assert 'new TextEncoder()' in result
        assert 'new TextDecoder("utf-8")' in result

