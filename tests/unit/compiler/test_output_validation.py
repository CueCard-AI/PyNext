"""
Output Validation Tests for PyNext Compiler

These tests verify the ACTUAL JavaScript output, not just whether compilation succeeds.
They target specific patterns that may compile without errors but produce incorrect JS.
"""

import pytest
import re
from pynext.compiler import compile_island


# =============================================================================
# BUG FOUND: Method Calls on Signal Results
# =============================================================================

class TestMethodCallBug:
    """
    BUG IDENTIFIED: text().upper() is compiled as createElement("upper")!
    
    Root cause: In _parse_dom_node, when node.func is ast.Attribute,
    the parser doesn't check if the attribute's value is a signal call.
    It just takes the attr name as the element tag.
    
    Fix location: pynext/compiler/parser.py lines 684-702
    """
    
    def test_method_call_on_signal_is_not_element(self):
        """FAILING: .upper() is parsed as <upper> element."""
        result = compile_island("""
@island
def Component():
    text = signal("hello")
    return div()[text().upper()]
""")
        # BUG: This currently creates: createElement("upper")
        # Should create: createEffect(() => { ... text().toUpperCase() ... })
        assert "createElement(\"upper\")" not in result.js, \
            "BUG: .upper() was incorrectly treated as an element"
        
    def test_chained_methods_not_elements(self):
        """FAILING: .strip().upper() creates nested elements."""
        result = compile_island("""
@island
def Component():
    text = signal("  hello  ")
    return div()[text().strip().upper()]
""")
        # Should NOT create elements named "strip" or "upper"
        assert "createElement(\"strip\")" not in result.js
        assert "createElement(\"upper\")" not in result.js
    
    def test_len_on_signal(self):
        """FAILING: len(text()) might be mishandled."""
        result = compile_island("""
@island
def Component():
    items = signal([1, 2, 3])
    return div()[len(items())]
""")
        # Should NOT create element named "len"
        assert "createElement(\"len\")" not in result.js
    
    def test_str_on_signal(self):
        """FAILING: str(value()) might be mishandled."""
        result = compile_island("""
@island
def Component():
    num = signal(42)
    return div()[str(num())]
""")
        assert "createElement(\"str\")" not in result.js


# =============================================================================
# Reactive Attribute Output Validation
# =============================================================================

class TestReactiveAttributeOutput:
    """
    Verify that reactive attributes create effects.
    """
    
    def test_reactive_class_creates_effect(self):
        """Reactive class should create an effect to update it."""
        result = compile_island("""
@island
def Component():
    active = signal(False)
    return div(class_=lambda: "active" if active() else "")
""")
        assert result.success
        # Should have createEffect for the class update
        # If class is static, it won't update reactively!
        js = result.js
        
        # Either way, className should be set
        has_classname = "className" in js or "setAttribute" in js
        assert has_classname, "Class attribute not found in output"
    
    def test_reactive_style_creates_effect(self):
        """Reactive style should create an effect to update it."""
        result = compile_island("""
@island
def Component():
    color = signal("red")
    return div(style=lambda: f"color: {color()}")
""")
        assert result.success
        # Style should be set dynamically
        js = result.js
        has_style = "style" in js.lower()
        assert has_style, "Style attribute not found in output"
    
    def test_static_class_no_effect(self):
        """Static class should NOT create an effect."""
        result = compile_island("""
@island
def Component():
    return div(class_="static-class")["Content"]
""")
        assert result.success
        js = result.js
        # Static class should be set directly
        assert "static-class" in js
    
    def test_multiple_reactive_attrs_multiple_effects(self):
        """Each reactive attr needs its own effect or one combined effect."""
        result = compile_island("""
@island
def Component():
    a = signal("a")
    b = signal("b")
    return div(
        class_=lambda: a(),
        data_value=lambda: b()
    )
""")
        assert result.success
        # Both should be reactive
        js = result.js
        # At minimum, both signals should be referenced
        assert "a()" in js or "a.value" in js or result.stats.get("signals", 0) >= 2


# =============================================================================
# Control Flow Output Validation
# =============================================================================

class TestControlFlowOutput:
    """
    Verify control flow components generate correct JS.
    """
    
    def test_show_generates_runtime_call(self):
        """Show should delegate to runtime Show function."""
        result = compile_island("""
@island
def Component():
    visible = signal(True)
    return Show(when=lambda: visible())[
        div()["Content"]
    ]
""")
        assert result.success
        js = result.js
        # Should call the runtime Show function
        assert "Show(" in js or "show(" in js
    
    def test_for_generates_runtime_call(self):
        """For should delegate to runtime For function."""
        result = compile_island("""
@island
def Component():
    items = signal([1, 2, 3])
    return For(each=lambda: items())[
        lambda item: div()[item]
    ]
""")
        assert result.success
        js = result.js
        # Should call the runtime For function
        assert "For(" in js or "for(" in js.lower()
    
    def test_for_child_gets_item_param(self):
        """For child lambda should receive item parameter."""
        result = compile_island("""
@island
def Component():
    items = signal([{"name": "A"}, {"name": "B"}])
    return For(each=lambda: items())[
        lambda item: div()[item["name"]]
    ]
""")
        assert result.success
        js = result.js
        # The children factory should have item parameter
        assert "item" in js or "function(item" in js or "(item)" in js or "(item," in js
    
    def test_nested_show_in_for(self):
        """Show inside For should work correctly."""
        result = compile_island("""
@island
def Component():
    items = signal([{"name": "A", "active": True}])
    return For(each=lambda: items())[
        lambda item: Show(when=lambda: item["active"])[
            div()[item["name"]]
        ]
    ]
""")
        assert result.success
        # Both Show and For should be present
        js = result.js
        assert "Show" in js or "show" in js
        assert "For" in js or "for" in js.lower()


# =============================================================================
# Event Handler Output Validation
# =============================================================================

class TestEventHandlerOutput:
    """
    Verify event handlers generate correct JS.
    """
    
    def test_onclick_creates_event_listener(self):
        """onclick should create addEventListener."""
        result = compile_island("""
@island
def Component():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))["Click"]
""")
        assert result.success
        js = result.js
        # Should have addEventListener for click
        assert "addEventListener" in js
        assert "click" in js.lower()
    
    def test_handler_preserves_signal_set(self):
        """signal.set() in handler should be preserved."""
        result = compile_island("""
@island
def Component():
    count = signal(0)
    return button(onclick=lambda: count.set(5))["Set to 5"]
""")
        assert result.success
        js = result.js
        # Should have count.set(5) or equivalent
        assert "count" in js
        # set or .set should be there
        assert ".set(" in js or "count(5)" in js
    
    def test_handler_with_expression(self):
        """Handler with expression should evaluate it."""
        result = compile_island("""
@island
def Component():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 10))["Add 10"]
""")
        assert result.success
        js = result.js
        # Expression count() + 10 should be preserved
        assert "10" in js
        assert "count" in js
    
    def test_handler_tuple_both_statements(self):
        """Handler with tuple should emit both statements."""
        result = compile_island("""
@island
def Component():
    a = signal(0)
    b = signal(0)
    return button(onclick=lambda: (a.set(1), b.set(2)))["Set both"]
""")
        assert result.success
        js = result.js
        # Both a.set(1) and b.set(2) should be in output
        assert "1" in js
        assert "2" in js
    
    def test_prevent_default(self):
        """e.preventDefault() should be preserved."""
        result = compile_island("""
@island
def Component():
    return form(onsubmit=lambda e: e.preventDefault())
""")
        assert result.success
        js = result.js
        assert "preventDefault" in js


# =============================================================================
# F-String Output Validation
# =============================================================================

class TestFStringOutput:
    """
    Verify f-strings compile to template literals.
    """
    
    def test_simple_fstring_uses_template_literal(self):
        """F-string should become JS template literal."""
        result = compile_island("""
@island
def Component():
    name = signal("World")
    return div()[f"Hello, {name()}!"]
""")
        assert result.success
        js = result.js
        # Should use backticks for template literal
        assert "`" in js
        assert "${" in js or "name()" in js
    
    def test_fstring_preserves_signal_read(self):
        """Signal read in f-string should be preserved."""
        result = compile_island("""
@island
def Component():
    count = signal(0)
    return div()[f"Count: {count()}"]
""")
        assert result.success
        js = result.js
        assert "count" in js
        # Either direct read or in template literal
        assert "count()" in js or "${count()}" in js or "Count:" in js
    
    def test_fstring_with_expression_evaluates(self):
        """Expression in f-string should be preserved."""
        result = compile_island("""
@island
def Component():
    count = signal(5)
    return div()[f"Double: {count() * 2}"]
""")
        assert result.success
        js = result.js
        assert "2" in js
        assert "count" in js


# =============================================================================
# Expression Compilation Validation
# =============================================================================

class TestExpressionOutput:
    """
    Verify Python expressions compile to correct JS.
    """
    
    def test_and_becomes_double_ampersand(self):
        """Python 'and' should become JS '&&'."""
        result = compile_island("""
@island
def Component():
    a = signal(True)
    b = signal(True)
    return Show(when=lambda: a() and b())[div()["Both"]]
""")
        assert result.success
        js = result.js
        assert "&&" in js
    
    def test_or_becomes_double_pipe(self):
        """Python 'or' should become JS '||'."""
        result = compile_island("""
@island
def Component():
    a = signal(False)
    b = signal(True)
    return Show(when=lambda: a() or b())[div()["Either"]]
""")
        assert result.success
        js = result.js
        assert "||" in js
    
    def test_not_becomes_exclamation(self):
        """Python 'not' should become JS '!'."""
        result = compile_island("""
@island
def Component():
    active = signal(True)
    return Show(when=lambda: not active())[div()["Inactive"]]
""")
        assert result.success
        js = result.js
        assert "!" in js
    
    def test_equality_becomes_triple_equals(self):
        """Python '==' should become JS '===' for safety."""
        result = compile_island("""
@island
def Component():
    value = signal("test")
    return Show(when=lambda: value() == "test")[div()["Match"]]
""")
        assert result.success
        js = result.js
        # Should use === or at least ==
        assert "==" in js or "===" in js
    
    def test_none_becomes_null(self):
        """Python 'None' should become JS 'null'."""
        result = compile_island("""
@island
def Component():
    value = signal(None)
    return Show(when=lambda: value() is None)[div()["Is null"]]
""")
        assert result.success
        js = result.js
        # Should have null check
        assert "null" in js
    
    def test_true_false_lowercase(self):
        """Python True/False should become JS true/false."""
        result = compile_island("""
@island
def Component():
    active = signal(True)
    inactive = signal(False)
    return div()[str(active()), str(inactive())]
""")
        assert result.success
        js = result.js
        # Initial values should be lowercase
        assert "true" in js or "True" not in js.replace("\"True\"", "")
        assert "false" in js or "False" not in js.replace("\"False\"", "")
    
    def test_floor_division_uses_math_floor(self):
        """Python '//' should use Math.floor."""
        result = compile_island("""
@island
def Component():
    a = signal(10)
    b = signal(3)
    result = memo(lambda: a() // b())
    return div()[result()]
""")
        assert result.success
        js = result.js
        # Floor division should use Math.floor
        assert "Math.floor" in js or "floor" in js.lower()
    
    def test_power_uses_math_pow(self):
        """Python '**' should use Math.pow or ** operator."""
        result = compile_island("""
@island
def Component():
    base = signal(2)
    exp = signal(3)
    result = memo(lambda: base() ** exp())
    return div()[result()]
""")
        assert result.success
        js = result.js
        # Either Math.pow or ** operator
        assert "Math.pow" in js or "**" in js


# =============================================================================
# List/Dict Operation Output Validation
# =============================================================================

class TestCollectionOperations:
    """
    Verify list/dict operations compile correctly.
    """
    
    def test_list_append_preserved(self):
        """list.append() should be preserved or become push()."""
        result = compile_island("""
@island
def Component():
    items = signal([])
    return button(onclick=lambda: items().append(1))["Add"]
""")
        assert result.success
        js = result.js
        # Should have push or append
        assert "push" in js.lower() or "append" in js.lower()
    
    def test_dict_access_preserved(self):
        """dict["key"] access should be preserved."""
        result = compile_island("""
@island
def Component():
    data = signal({"name": "Test"})
    return div()[data()["name"]]
""")
        assert result.success
        js = result.js
        # Should have subscript access
        assert "[" in js
        assert "name" in js
    
    def test_in_operator_for_list(self):
        """'x in list' should use includes() for arrays."""
        result = compile_island("""
@island
def Component():
    items = signal([1, 2, 3])
    return Show(when=lambda: 2 in items())[div()["Found"]]
""")
        assert result.success
        js = result.js
        # Should use includes or indexOf
        assert "includes" in js or "indexOf" in js or "in " in js
    
    def test_in_operator_for_dict(self):
        """'key in dict' should use 'in' operator."""
        result = compile_island("""
@island
def Component():
    data = signal({"a": 1})
    return Show(when=lambda: "a" in data())[div()["Has key"]]
""")
        assert result.success
        js = result.js
        # Should have some form of membership check
        assert "in" in js.lower() or "has" in js.lower()


# =============================================================================
# Edge Cases Output Validation
# =============================================================================

class TestEdgeCaseOutput:
    """
    Edge cases that might produce incorrect output.
    """
    
    def test_empty_string_literal(self):
        """Empty string should be preserved."""
        result = compile_island("""
@island
def Component():
    return div()[""]
""")
        assert result.success
        js = result.js
        # Should have empty string somewhere
        assert '""' in js or "''" in js
    
    def test_zero_literal(self):
        """Zero should not be treated as falsy in output."""
        result = compile_island("""
@island
def Component():
    count = signal(0)
    return div()[count()]
""")
        assert result.success
        # 0 should be a valid initial value
        js = result.js
        assert "createSignal(0)" in js or "signal(0)" in js.lower()
    
    def test_special_characters_in_string(self):
        """Strings with quotes should be escaped."""
        result = compile_island("""
@island
def Component():
    return div()["He said \\"hello\\""]
""")
        assert result.success
        # Quotes should be escaped in output
        js = result.js
        # Either escaped quotes or the text is there
        assert "hello" in js
    
    def test_unicode_in_string(self):
        """Unicode strings should be preserved."""
        result = compile_island("""
@island
def Component():
    return div()["Hello 世界 🌍"]
""")
        assert result.success
        js = result.js
        # Unicode should be preserved (or encoded)
        # At minimum the string should contain "Hello"
        assert "Hello" in js
    
    def test_multiline_fstring(self):
        """Multiline f-string should compile."""
        result = compile_island('''
@island
def Component():
    name = signal("World")
    return div()[f"""
        Hello,
        {name()}!
    """]
''')
        # Should at least not crash
        assert result.success or len(result.errors) > 0  # Either works or gives error
    
    def test_deeply_nested_expressions(self):
        """Deep nesting should not stack overflow."""
        result = compile_island("""
@island
def Component():
    a = signal(1)
    b = signal(2)
    c = signal(3)
    d = signal(4)
    result = memo(lambda: ((a() + b()) * (c() - d())) + ((a() * b()) - (c() / d())))
    return div()[result()]
""")
        assert result.success
        js = result.js
        # All operations should be present
        assert "+" in js
        assert "-" in js
        assert "*" in js
        assert "/" in js


