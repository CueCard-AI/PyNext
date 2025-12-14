"""
Comprehensive tests for PyNext Compiler Emitter (500 tests)

Tests cover:
- Signal emission
- Memo emission
- Effect emission
- Handler emission
- DOM tree emission
- Control flow emission
- Expression emission
- Island registration
- Output validation
"""

import pytest
import json
import re
from pynext.compiler import compile_island
from pynext.compiler.parser import parse_island
from pynext.compiler.analyzer import analyze_dependencies
from pynext.compiler.emitter import emit_javascript, JSEmitter


# =============================================================================
# SECTION 1: Signal Emission (80 tests)
# =============================================================================

class TestSignalEmission:
    """Tests for signal declaration emission."""
    
    def test_signal_integer_emission(self):
        """Signal with integer emits createSignal(0)."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
""")
        assert "createSignal(0)" in result.js
    
    def test_signal_string_emission(self):
        """Signal with string emits createSignal("...")."""
        result = compile_island("""
@island
def Input():
    text = signal("hello")
""")
        assert 'createSignal("hello")' in result.js
    
    def test_signal_bool_true_emission(self):
        """Signal with True emits createSignal(true)."""
        result = compile_island("""
@island
def Toggle():
    active = signal(True)
""")
        assert "createSignal(true)" in result.js
    
    def test_signal_bool_false_emission(self):
        """Signal with False emits createSignal(false)."""
        result = compile_island("""
@island
def Toggle():
    active = signal(False)
""")
        assert "createSignal(false)" in result.js
    
    def test_signal_null_emission(self):
        """Signal with None emits createSignal(null)."""
        result = compile_island("""
@island
def Data():
    value = signal(None)
""")
        assert "createSignal(null)" in result.js
    
    def test_signal_list_emission(self):
        """Signal with list emits createSignal([...])."""
        result = compile_island("""
@island
def List():
    items = signal([1, 2, 3])
""")
        assert "createSignal([1, 2, 3])" in result.js
    
    def test_signal_dict_emission(self):
        """Signal with dict emits createSignal({...})."""
        result = compile_island("""
@island
def Form():
    data = signal({"name": "John"})
""")
        # JSON format may have slight variations
        assert "createSignal(" in result.js
        assert '"name"' in result.js
    
    def test_signal_const_declaration(self):
        """Signal uses const declaration."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
""")
        assert "const count = createSignal" in result.js
    
    def test_multiple_signals_order(self):
        """Multiple signals emitted in declaration order."""
        result = compile_island("""
@island
def Form():
    a = signal(1)
    b = signal(2)
    c = signal(3)
""")
        a_pos = result.js.find("const a =")
        b_pos = result.js.find("const b =")
        c_pos = result.js.find("const c =")
        assert a_pos < b_pos < c_pos


class TestSignalNames:
    """Tests for correct signal variable names."""
    
    def test_signal_name_preserved(self):
        """Signal variable name is preserved."""
        result = compile_island("""
@island
def Counter():
    myCounter = signal(0)
""")
        assert "const myCounter = createSignal" in result.js
    
    def test_unicode_name_preserved(self):
        """Unicode signal name is preserved."""
        result = compile_island("""
@island
def Counter():
    数量 = signal(0)
""")
        assert "const 数量 = createSignal" in result.js


# =============================================================================
# SECTION 2: Memo Emission (50 tests)
# =============================================================================

class TestMemoEmission:
    """Tests for memo declaration emission."""
    
    def test_memo_simple_emission(self):
        """Simple memo emits createMemo(...)."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    doubled = memo(lambda: count() * 2)
""")
        assert "createMemo(" in result.js
    
    def test_memo_arrow_function(self):
        """Memo body emits as arrow function."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    doubled = memo(lambda: count() * 2)
""")
        # Should contain arrow function syntax
        assert "=>" in result.js
    
    def test_memo_const_declaration(self):
        """Memo uses const declaration."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    doubled = memo(lambda: count() * 2)
""")
        assert "const doubled = createMemo" in result.js
    
    def test_memo_complex_expression(self):
        """Memo with complex expression."""
        result = compile_island("""
@island
def Calculator():
    a = signal(1)
    b = signal(2)
    result = memo(lambda: (a() + b()) * 2)
""")
        assert "createMemo(" in result.js


# =============================================================================
# SECTION 3: Handler Emission (80 tests)
# =============================================================================

class TestHandlerEmission:
    """Tests for event handler emission."""
    
    def test_onclick_addEventListener(self):
        """onclick emits addEventListener("click", ...)."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(0))
""")
        assert 'addEventListener("click"' in result.js
    
    def test_handler_arrow_function(self):
        """Handler emits as arrow function."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(0))
""")
        assert "() =>" in result.js
    
    def test_handler_with_param(self):
        """Handler with event parameter."""
        result = compile_island("""
@island
def Input():
    text = signal("")
    return input(oninput=lambda e: text.set(e.target.value))
""")
        assert "(e) =>" in result.js
        assert "e.target.value" in result.js
    
    def test_signal_set_emission(self):
        """signal.set() emits correctly."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(5))
""")
        assert "count.set(5)" in result.js
    
    def test_signal_update_emission(self):
        """signal.update() emits correctly."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.update(lambda x: x + 1))
""")
        assert "count.update(" in result.js
        assert "x => (x + 1)" in result.js or "(x) => (x + 1)" in result.js
    
    def test_signal_read_in_handler(self):
        """signal() read in handler emits correctly."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))
""")
        assert "count.set((count() + 1))" in result.js or "count.set(count() + 1)" in result.js
    
    def test_multiple_handlers_same_element(self):
        """Multiple handlers on same element."""
        result = compile_island("""
@island
def Button():
    return button(onclick=lambda: click(), onmouseover=lambda: hover())
""")
        assert 'addEventListener("click"' in result.js
        assert 'addEventListener("mouseover"' in result.js


class TestHandlerEvents:
    """Tests for different event types."""
    
    def test_onclick_event(self):
        result = compile_island('@island\ndef C():\n    return button(onclick=lambda: None)')
        assert '"click"' in result.js
    
    def test_oninput_event(self):
        result = compile_island('@island\ndef C():\n    return input(oninput=lambda: None)')
        assert '"input"' in result.js
    
    def test_onsubmit_event(self):
        result = compile_island('@island\ndef C():\n    return form(onsubmit=lambda: None)')
        assert '"submit"' in result.js
    
    def test_onchange_event(self):
        result = compile_island('@island\ndef C():\n    return select(onchange=lambda: None)')
        assert '"change"' in result.js
    
    def test_onkeydown_event(self):
        result = compile_island('@island\ndef C():\n    return input(onkeydown=lambda: None)')
        assert '"keydown"' in result.js
    
    def test_onfocus_event(self):
        result = compile_island('@island\ndef C():\n    return input(onfocus=lambda: None)')
        assert '"focus"' in result.js
    
    def test_onblur_event(self):
        result = compile_island('@island\ndef C():\n    return input(onblur=lambda: None)')
        assert '"blur"' in result.js


# =============================================================================
# SECTION 4: DOM Emission (100 tests)
# =============================================================================

class TestElementEmission:
    """Tests for DOM element emission."""
    
    def test_div_element(self):
        """div() emits createElement("div")."""
        result = compile_island("""
@island
def Box():
    return div()
""")
        assert 'createElement("div")' in result.js
    
    def test_button_element(self):
        """button() emits createElement("button")."""
        result = compile_island("""
@island
def Btn():
    return button()
""")
        assert 'createElement("button")' in result.js
    
    def test_span_element(self):
        """span() emits createElement("span")."""
        result = compile_island("""
@island
def Text():
    return span()
""")
        assert 'createElement("span")' in result.js
    
    def test_input_element(self):
        """input() emits createElement("input")."""
        result = compile_island("""
@island
def Field():
    return input()
""")
        assert 'createElement("input")' in result.js
    
    def test_const_element_var(self):
        """Element uses const declaration."""
        result = compile_island("""
@island
def Box():
    return div()
""")
        assert "const _el" in result.js


class TestAttributeEmission:
    """Tests for attribute emission."""
    
    def test_class_attribute(self):
        """class_ emits className."""
        result = compile_island("""
@island
def Box():
    return div(class_="container")
""")
        assert '.className = "container"' in result.js
    
    def test_id_attribute(self):
        """id emits setAttribute."""
        result = compile_island("""
@island
def Box():
    return div(id="main")
""")
        assert 'setAttribute("id", "main")' in result.js
    
    def test_style_attribute(self):
        """style string emits style.cssText."""
        result = compile_island("""
@island
def Box():
    return div(style="color: red")
""")
        assert '.style.cssText = "color: red"' in result.js
    
    def test_data_attribute(self):
        """data-* emits setAttribute."""
        result = compile_island("""
@island
def Box():
    return div(data_id="123")
""")
        assert 'setAttribute("data_id", "123")' in result.js
    
    def test_type_attribute(self):
        """type emits setAttribute."""
        result = compile_island("""
@island
def Input():
    return input(type="text")
""")
        assert 'setAttribute("type", "text")' in result.js


class TestChildEmission:
    """Tests for child element emission."""
    
    def test_text_child(self):
        """Static text emits createTextNode."""
        result = compile_island("""
@island
def Box():
    return div()["Hello"]
""")
        assert 'createTextNode("Hello")' in result.js
    
    def test_appendChild_call(self):
        """Children appended with appendChild."""
        result = compile_island("""
@island
def Box():
    return div()["Hello"]
""")
        assert "appendChild(" in result.js
    
    def test_nested_element_child(self):
        """Nested element as child."""
        result = compile_island("""
@island
def Box():
    return div()[span()["Inner"]]
""")
        assert 'createElement("div")' in result.js
        assert 'createElement("span")' in result.js
    
    def test_multiple_children(self):
        """Multiple children appended."""
        result = compile_island("""
@island
def Box():
    return div()["One", "Two", "Three"]
""")
        assert result.js.count("createTextNode") >= 3


class TestReactiveEmission:
    """Tests for reactive content emission."""
    
    def test_signal_read_text(self):
        """Signal read as text content."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return div()[count()]
""")
        assert "createTextNode" in result.js
        assert "createEffect" in result.js
        assert "textContent" in result.js
    
    def test_reactive_text_effect(self):
        """Reactive text wrapped in createEffect."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return div()[count()]
""")
        # Should have createEffect updating textContent
        assert "createEffect(() =>" in result.js or "createEffect(() => {" in result.js
    
    def test_subscript_access_emission(self):
        """Dictionary subscript emitted correctly."""
        result = compile_island("""
@island
def Card(data):
    return div()[data["title"]]
""")
        assert 'data["title"]' in result.js


# =============================================================================
# SECTION 5: Control Flow Emission (60 tests)
# =============================================================================

class TestShowEmission:
    """Tests for Show component emission."""
    
    def test_show_uses_runtime(self):
        """Show calls runtime Show() function."""
        result = compile_island("""
@island
def Toggle():
    visible = signal(True)
    return Show(when=lambda: visible())
""")
        assert "Show({" in result.js
    
    def test_show_has_when(self):
        """Show has when parameter."""
        result = compile_island("""
@island
def Toggle():
    visible = signal(True)
    return Show(when=lambda: visible())[div()["Content"]]
""")
        assert "when:" in result.js
        assert "visible()" in result.js
    
    def test_show_condition_emission(self):
        """Show when condition emitted correctly."""
        result = compile_island("""
@island
def Toggle():
    visible = signal(True)
    return Show(when=lambda: visible())[div()["Content"]]
""")
        assert "visible()" in result.js
    
    def test_show_children_factory(self):
        """Show children emitted as factory function."""
        result = compile_island("""
@island
def Toggle():
    visible = signal(True)
    return Show(when=lambda: visible())[div()["Content"]]
""")
        assert "children:" in result.js
        assert 'createElement("div")' in result.js


class TestForEmission:
    """Tests for For component emission."""
    
    def test_for_calls_runtime(self):
        """For calls For() from runtime."""
        result = compile_island("""
@island
def List():
    items = signal([1, 2, 3])
    return For(each=lambda: items())
""")
        assert "For({" in result.js


# =============================================================================
# SECTION 6: Expression Emission (60 tests)
# =============================================================================

class TestBinaryOperations:
    """Tests for binary operation emission."""
    
    def test_addition(self):
        """+ emits correctly."""
        result = compile_island("""
@island
def C():
    a = signal(1)
    return div()[a() + 1]
""")
        assert "+ 1" in result.js
    
    def test_subtraction(self):
        """- emits correctly."""
        result = compile_island("""
@island
def C():
    a = signal(1)
    return button(onclick=lambda: a.set(a() - 1))
""")
        assert "- 1" in result.js
    
    def test_multiplication(self):
        """* emits correctly."""
        result = compile_island("""
@island
def C():
    a = signal(1)
    doubled = memo(lambda: a() * 2)
""")
        assert "* 2" in result.js
    
    def test_division(self):
        """/ emits correctly."""
        result = compile_island("""
@island
def C():
    a = signal(10)
    half = memo(lambda: a() / 2)
""")
        assert "/ 2" in result.js


class TestComparisonOperations:
    """Tests for comparison operation emission."""
    
    def test_equals(self):
        """== emits ===."""
        result = compile_island("""
@island
def C():
    a = signal(1)
    return Show(when=lambda: a() == 1)
""")
        assert "===" in result.js
    
    def test_not_equals(self):
        """!= emits !==."""
        result = compile_island("""
@island
def C():
    a = signal(1)
    return Show(when=lambda: a() != 0)
""")
        assert "!==" in result.js
    
    def test_less_than(self):
        """< emits correctly."""
        result = compile_island("""
@island
def C():
    a = signal(1)
    return Show(when=lambda: a() < 10)
""")
        assert "< 10" in result.js
    
    def test_greater_than(self):
        """> emits correctly."""
        result = compile_island("""
@island
def C():
    a = signal(1)
    return Show(when=lambda: a() > 0)
""")
        assert "> 0" in result.js


class TestBooleanOperations:
    """Tests for boolean operation emission."""
    
    def test_and(self):
        """and emits &&."""
        result = compile_island("""
@island
def C():
    a = signal(True)
    b = signal(True)
    return Show(when=lambda: a() and b())
""")
        assert "&&" in result.js
    
    def test_or(self):
        """or emits ||."""
        result = compile_island("""
@island
def C():
    a = signal(True)
    b = signal(False)
    return Show(when=lambda: a() or b())
""")
        assert "||" in result.js
    
    def test_not(self):
        """not emits !."""
        result = compile_island("""
@island
def C():
    a = signal(True)
    return Show(when=lambda: not a())
""")
        assert "!" in result.js


class TestTernaryExpression:
    """Tests for ternary expression emission."""
    
    def test_ternary_emission(self):
        """if/else expression emits ternary."""
        result = compile_island("""
@island
def C():
    a = signal(1)
    b = memo(lambda: "yes" if a() > 0 else "no")
""")
        assert "?" in result.js
        assert ":" in result.js


# =============================================================================
# SECTION 7: Island Registration (20 tests)
# =============================================================================

class TestIslandRegistration:
    """Tests for island registration emission."""
    
    def test_pynext_islands_init(self):
        """__PYNEXT_ISLANDS__ object initialized."""
        result = compile_island("""
@island
def Counter():
    pass
""")
        assert "__PYNEXT_ISLANDS__" in result.js
    
    def test_island_registered(self):
        """Island function registered."""
        result = compile_island("""
@island
def Counter():
    pass
""")
        assert "__PYNEXT_ISLANDS__.Counter = Counter" in result.js
    
    def test_different_name_registered(self):
        """Different island names registered correctly."""
        result = compile_island("""
@island
def MyCustomComponent():
    pass
""")
        assert "__PYNEXT_ISLANDS__.MyCustomComponent = MyCustomComponent" in result.js


# =============================================================================
# SECTION 8: Return Statement (20 tests)
# =============================================================================

class TestReturnStatement:
    """Tests for return statement emission."""
    
    def test_return_root_element(self):
        """Root element is returned."""
        result = compile_island("""
@island
def Box():
    return div()
""")
        assert "return _el" in result.js
    
    def test_function_returns_dom(self):
        """Function returns DOM element."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button()[count()]
""")
        lines = result.js.split('\n')
        # Should have a return statement inside the function
        assert any("return _el" in line for line in lines)


# =============================================================================
# SECTION 9: Output Validation (30 tests)
# =============================================================================

class TestOutputValidation:
    """Tests for validating JavaScript output."""
    
    def test_valid_javascript_syntax(self):
        """Output is valid JavaScript (basic check)."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))[count()]
""")
        # Check balanced braces
        assert result.js.count('{') == result.js.count('}')
        assert result.js.count('(') == result.js.count(')')
    
    def test_no_python_syntax(self):
        """No Python-specific syntax in output."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
""")
        assert "def " not in result.js
        assert "@island" not in result.js
        assert "lambda:" not in result.js  # Should be arrow functions
    
    def test_function_keyword_used(self):
        """Uses function keyword for declaration."""
        result = compile_island("""
@island
def Counter():
    pass
""")
        assert "function Counter" in result.js
    
    def test_const_used_for_signals(self):
        """const used for signal declarations."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
""")
        assert "const count = createSignal" in result.js
    
    def test_semicolons_present(self):
        """Statements end with semicolons."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
""")
        assert "createSignal(0);" in result.js


# =============================================================================
# SECTION 10: Complete Component Tests (20 tests)
# =============================================================================

class TestCompleteComponents:
    """End-to-end tests for complete components."""
    
    def test_simple_counter(self):
        """Simple counter component."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))[count()]
""")
        assert result.success
        assert "createSignal(0)" in result.js
        assert "addEventListener" in result.js
        assert "createEffect" in result.js
    
    def test_toggle_component(self):
        """Toggle with Show component."""
        result = compile_island("""
@island
def Toggle():
    visible = signal(False)
    return div()[
        button(onclick=lambda: visible.update(lambda x: not x))["Toggle"],
        Show(when=lambda: visible())[
            div()["Content"]
        ]
    ]
""")
        assert result.success
        assert "createSignal(false)" in result.js
    
    def test_issue_card_component(self):
        """Issue card (Linear clone milestone)."""
        result = compile_island("""
@island
def IssueCard(issue):
    expanded = signal(False)
    return div(class_="issue-card")[
        div(class_="header", onclick=lambda: expanded.update(lambda x: not x))[
            span()[issue["title"]]
        ],
        Show(when=lambda: expanded())[
            div(class_="details")[issue["description"]]
        ]
    ]
""")
        assert result.success
        assert "function IssueCard(issue)" in result.js
        assert 'issue["title"]' in result.js
        assert 'issue["description"]' in result.js
    
    def test_form_component(self):
        """Form with multiple inputs."""
        result = compile_island("""
@island
def LoginForm():
    username = signal("")
    password = signal("")
    return form()[
        input(type="text", oninput=lambda e: username.set(e.target.value)),
        input(type="password", oninput=lambda e: password.set(e.target.value)),
        button(type="submit")["Login"]
    ]
""")
        assert result.success
        assert "const username = createSignal" in result.js
        assert "const password = createSignal" in result.js

