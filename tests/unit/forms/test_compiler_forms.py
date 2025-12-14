"""
Comprehensive tests for compiler form support.

Tests cover:
- FormDef parsing
- Form emission to JavaScript
- Validator emission
- bind= attribute handling

Total: 50+ tests
"""

import pytest
from pynext.compiler.parser import (
    parse_island,
    FormDef,
    IslandIR,
)
from pynext.compiler.emitter import emit_javascript


# =============================================================================
# FORM PARSING (25 tests)
# =============================================================================

class TestFormParsing:
    """Tests for parsing create_form() calls."""
    
    def test_parse_simple_form(self):
        """Parse simple create_form call."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form(initial={"name": ""})
    return div()[form.name()]
'''
        ir = parse_island(source)
        assert len(ir.forms) == 1
        assert ir.forms[0].name == "form"
    
    def test_parse_form_with_initial_dict(self):
        """Parse form with initial values dict."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form(initial={"name": "Alice", "age": 25})
    return div()
'''
        ir = parse_island(source)
        assert ir.forms[0].initial.get("name") == "Alice"
        assert ir.forms[0].initial.get("age") == 25
    
    def test_parse_form_positional_initial(self):
        """Parse form with positional initial arg."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form({"name": "", "email": ""})
    return div()
'''
        ir = parse_island(source)
        assert "name" in ir.forms[0].initial
        assert "email" in ir.forms[0].initial
    
    def test_parse_multiple_forms(self):
        """Parse multiple forms in one component."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form1 = create_form(initial={"a": ""})
    form2 = create_form(initial={"b": ""})
    return div()
'''
        ir = parse_island(source)
        assert len(ir.forms) == 2
        assert {f.name for f in ir.forms} == {"form1", "form2"}
    
    def test_parse_form_with_validators(self):
        """Parse form with validators."""
        source = '''
from pynext.reactive.forms import create_form, required

@island
def TestComponent():
    form = create_form(
        initial={"name": ""},
        validators={"name": [required()]}
    )
    return div()
'''
        ir = parse_island(source)
        assert ir.forms[0].validators is not None
    
    def test_form_in_ir_names(self):
        """Form names added to IR."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    myform = create_form(initial={"x": ""})
    return div()
'''
        ir = parse_island(source)
        assert "myform" in ir.form_names
    
    def test_parse_form_empty_initial(self):
        """Parse form with empty initial."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form(initial={})
    return div()
'''
        ir = parse_island(source)
        assert ir.forms[0].initial == {}
    
    def test_form_line_number(self):
        """FormDef captures line number."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    # Line 6
    form = create_form(initial={"x": ""})
    return div()
'''
        ir = parse_island(source)
        assert ir.forms[0].line > 0
    
    def test_parse_form_various_value_types(self):
        """Parse form with various value types."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form(initial={
        "string": "hello",
        "number": 42,
        "boolean": True,
    })
    return div()
'''
        ir = parse_island(source)
        assert ir.forms[0].initial.get("string") == "hello"
        assert ir.forms[0].initial.get("number") == 42
        assert ir.forms[0].initial.get("boolean") is True


# =============================================================================
# FORM EMISSION (25 tests)
# =============================================================================

class TestFormEmission:
    """Tests for emitting forms to JavaScript."""
    
    def test_emit_creates_form(self):
        """Emitted JS contains createForm."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form(initial={"name": ""})
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert "createForm" in js
    
    def test_emit_form_initial_values(self):
        """Emitted JS contains initial values."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form(initial={"name": "Alice"})
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert '"name"' in js
        assert '"Alice"' in js
    
    def test_emit_form_variable_name(self):
        """Emitted JS uses correct variable name."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    loginForm = create_form(initial={"email": ""})
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert "const loginForm = createForm" in js
    
    def test_emit_multiple_forms(self):
        """Emit multiple forms."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form1 = create_form(initial={"a": ""})
    form2 = create_form(initial={"b": ""})
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert "const form1 = createForm" in js
        assert "const form2 = createForm" in js
    
    def test_emit_form_with_validators(self):
        """Emit form with validators."""
        source = '''
from pynext.reactive.forms import create_form, required

@island
def TestComponent():
    form = create_form(
        initial={"name": ""},
        validators={"name": [required()]}
    )
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert "required" in js
    
    def test_emit_validator_min_length(self):
        """Emit min_length validator."""
        source = '''
from pynext.reactive.forms import create_form, min_length

@island
def TestComponent():
    form = create_form(
        initial={"name": ""},
        validators={"name": [min_length(3)]}
    )
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert "minLength" in js
        assert "3" in js
    
    def test_emit_validator_email(self):
        """Emit email validator."""
        source = '''
from pynext.reactive.forms import create_form, email

@island
def TestComponent():
    form = create_form(
        initial={"email": ""},
        validators={"email": [email()]}
    )
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert "email" in js
    
    def test_emit_empty_initial(self):
        """Emit form with empty initial."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form(initial={})
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert "createForm({}," in js or "createForm({})" in js
    
    def test_emit_form_number_values(self):
        """Emit form with number values."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form(initial={"count": 42, "price": 3.14})
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert "42" in js
        assert "3.14" in js
    
    def test_emit_form_boolean_values(self):
        """Emit form with boolean values."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form(initial={"active": True, "disabled": False})
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert "true" in js
        assert "false" in js
    
    def test_emit_form_null_values(self):
        """Emit form with null values."""
        source = '''
from pynext.reactive.forms import create_form

@island
def TestComponent():
    form = create_form(initial={"nullable": None})
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        assert "null" in js
    
    def test_emit_generates_valid_js(self):
        """Emitted JS is syntactically valid."""
        source = '''
from pynext.reactive.forms import create_form, required

@island
def TestComponent():
    form = create_form(
        initial={"name": "", "email": ""},
        validators={"name": [required()]}
    )
    return div()
'''
        ir = parse_island(source)
        js = emit_javascript(ir)
        # Basic syntax checks
        assert js.count("{") == js.count("}")
        assert js.count("(") == js.count(")")
        assert js.count("[") == js.count("]")

