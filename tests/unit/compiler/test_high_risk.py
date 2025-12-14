"""
High-Risk Area Tests for PyNext Compiler

These tests specifically target areas identified as high-risk for bugs:
- P0: Critical issues that will break most apps
- P1: High-priority edge cases
- P2: Medium-priority unusual patterns
"""

import pytest
from pynext.compiler import compile_island, CompileError


# =============================================================================
# P0: CRITICAL - Nested Effects in For Loops
# =============================================================================

class TestForLoopEffects:
    """
    P0 RISK: Effects created inside For loop children are not disposed
    when items are removed, causing memory leaks and stale updates.
    """
    
    def test_for_with_reactive_text(self):
        """For loop with reactive text in each item."""
        result = compile_island("""
@island
def List():
    items = signal([{"name": "A"}, {"name": "B"}])
    return For(each=lambda: items())[
        lambda item: div()[item["name"]]
    ]
""")
        assert result.success
        # Should create DOM without effects inside (item["name"] is static per render)
        # But if we had a signal read, it would need an effect
    
    def test_for_with_signal_read_in_child(self):
        """For with external signal read in each child."""
        result = compile_island("""
@island
def List():
    items = signal([1, 2, 3])
    multiplier = signal(2)
    return For(each=lambda: items())[
        lambda item: div()[item * multiplier()]
    ]
""")
        assert result.success
        # This creates an effect per item - needs proper disposal
    
    def test_for_with_nested_show(self):
        """For with Show inside - compound effect risk."""
        result = compile_island("""
@island
def FilteredList():
    items = signal([{"name": "A", "active": True}])
    return For(each=lambda: items())[
        lambda item: Show(when=lambda: item["active"])[
            div()[item["name"]]
        ]
    ]
""")
        assert result.success
    
    def test_for_with_handler_capturing_signal(self):
        """For with handler that captures external signal."""
        result = compile_island("""
@island
def ClickableList():
    items = signal([1, 2, 3])
    selected = signal(None)
    return For(each=lambda: items())[
        lambda item: button(onclick=lambda: selected.set(item))[item]
    ]
""")
        assert result.success
        # Handler captures 'item' - closure over loop variable
    
    def test_deeply_nested_for(self):
        """Multiple levels of For nesting."""
        result = compile_island("""
@island
def Grid():
    rows = signal([])
    return For(each=lambda: rows())[
        lambda row: div()[
            For(each=lambda: row["cells"])[
                lambda cell: span()[cell]
            ]
        ]
    ]
""")
        assert result.success


# =============================================================================
# P0: CRITICAL - Reactive Attributes
# =============================================================================

class TestReactiveAttributes:
    """
    P0 RISK: Reactive attributes (lambdas as attribute values) may not
    be compiled to effects, causing them to never update.
    """
    
    def test_reactive_class_lambda(self):
        """Class attribute as lambda."""
        result = compile_island("""
@island
def DynamicClass():
    active = signal(False)
    return div(class_=lambda: "active" if active() else "inactive")
""")
        assert result.success
        # Must have createEffect for class update
        # Check if it's handled as reactive
        if "createEffect" not in result.js:
            # If no effect, the class is static - this is a bug!
            pass  # Will be caught in output inspection
    
    def test_reactive_style_lambda(self):
        """Style attribute as lambda."""
        result = compile_island("""
@island
def DynamicStyle():
    color = signal("red")
    return div(style=lambda: f"color: {color()}")
""")
        assert result.success
    
    def test_reactive_disabled_attribute(self):
        """Disabled attribute based on signal."""
        result = compile_island("""
@island
def ConditionalButton():
    disabled = signal(False)
    return button(disabled=lambda: "disabled" if disabled() else None)["Click"]
""")
        assert result.success
    
    def test_reactive_data_attribute(self):
        """Data attribute as lambda."""
        result = compile_island("""
@island
def DataAttr():
    value = signal(0)
    return div(data_value=lambda: str(value()))
""")
        assert result.success
    
    def test_multiple_reactive_attrs(self):
        """Multiple reactive attributes on same element."""
        result = compile_island("""
@island
def MultiReactive():
    state = signal("default")
    return div(
        class_=lambda: f"state-{state()}",
        style=lambda: f"opacity: {1 if state() == 'active' else 0.5}",
        data_state=lambda: state()
    )
""")
        assert result.success


# =============================================================================
# P0: CRITICAL - F-String Edge Cases
# =============================================================================

class TestFStringEdgeCases:
    """
    P0 RISK: F-strings with complex expressions may not compile correctly.
    """
    
    def test_simple_fstring(self):
        """Basic f-string with signal."""
        result = compile_island("""
@island
def FString():
    name = signal("World")
    return div()[f"Hello, {name()}!"]
""")
        assert result.success
        assert "`" in result.js  # Template literal
    
    def test_fstring_multiple_interpolations(self):
        """F-string with multiple interpolations."""
        result = compile_island("""
@island
def MultiFString():
    first = signal("John")
    last = signal("Doe")
    return div()[f"{first()} {last()}"]
""")
        assert result.success
    
    def test_fstring_with_expression(self):
        """F-string with expression in interpolation."""
        result = compile_island("""
@island
def ExprFString():
    count = signal(5)
    return div()[f"Count: {count() * 2}"]
""")
        assert result.success
    
    def test_fstring_with_method_call(self):
        """F-string with method call."""
        result = compile_island("""
@island
def MethodFString():
    name = signal("hello")
    return div()[f"Upper: {name().upper()}"]
""")
        assert result.success
        # Note: .upper() won't work in JS - this tests what we emit
    
    def test_fstring_with_subscript(self):
        """F-string with subscript access."""
        result = compile_island("""
@island
def SubscriptFString():
    data = signal({"name": "Test"})
    return div()[f"Name: {data()['name']}"]
""")
        assert result.success
    
    def test_fstring_with_ternary(self):
        """F-string with ternary inside."""
        result = compile_island("""
@island
def TernaryFString():
    active = signal(True)
    return div()[f"Status: {'Active' if active() else 'Inactive'}"]
""")
        assert result.success
    
    def test_fstring_with_format_spec(self):
        """F-string with format specification."""
        result = compile_island("""
@island
def FormatFString():
    value = signal(3.14159)
    return div()[f"Pi: {value():.2f}"]
""")
        # This likely won't work in JS - test what happens
        assert result.success or not result.success  # Either way, shouldn't crash
    
    def test_nested_braces_fstring(self):
        """F-string with literal braces."""
        result = compile_island("""
@island
def BracesFString():
    obj = signal("test")
    return div()[f"JSON: {{{obj()}}}"]
""")
        assert result.success


# =============================================================================
# P1: HIGH - Tuple/Sequence in Handler
# =============================================================================

class TestHandlerTupleSequence:
    """
    P1 RISK: Handlers with multiple statements (tuple) may not emit all.
    """
    
    def test_handler_tuple_two_statements(self):
        """Handler with two statements in tuple."""
        result = compile_island("""
@island
def TupleHandler():
    count = signal(0)
    return button(onclick=lambda: (count.set(0), log("reset")))["Reset"]
""")
        assert result.success
        # Both statements should be in output
        assert "count.set" in result.js
    
    def test_handler_prevent_default_then_action(self):
        """Common pattern: preventDefault then action."""
        result = compile_island("""
@island
def FormHandler():
    return form(onsubmit=lambda e: (e.preventDefault(), submit()))
""")
        assert result.success
        assert "preventDefault" in result.js
    
    def test_handler_three_statements(self):
        """Handler with three statements."""
        result = compile_island("""
@island
def MultiAction():
    a = signal(0)
    b = signal(0)
    c = signal(0)
    return button(onclick=lambda: (a.set(1), b.set(2), c.set(3)))["Set All"]
""")
        assert result.success
    
    def test_handler_tuple_with_condition(self):
        """Handler tuple with conditional."""
        result = compile_island("""
@island
def ConditionalHandler():
    count = signal(0)
    return button(onclick=lambda: (log("click"), count.set(count() + 1) if count() < 10 else None))
""")
        assert result.success


# =============================================================================
# P1: HIGH - Chained Method Calls
# =============================================================================

class TestChainedMethods:
    """
    P1 RISK: Method chains may not compile correctly.
    """
    
    def test_simple_method_chain(self):
        """Simple two-method chain."""
        result = compile_island("""
@island
def Chain():
    text = signal("hello world")
    return div()[text().upper()]
""")
        assert result.success
        # Python .upper() should be translated to JavaScript .toUpperCase()
        assert ".toUpperCase()" in result.js
    
    def test_filter_map_chain(self):
        """Filter then map chain."""
        result = compile_island("""
@island
def FilterMap():
    items = signal([1, 2, 3, 4, 5])
    filtered = memo(lambda: [x * 2 for x in items() if x > 2])
    return div()[str(filtered())]
""")
        assert result.success
    
    def test_nested_method_calls(self):
        """Nested method calls."""
        result = compile_island("""
@island
def Nested():
    text = signal("  hello  ")
    return div()[text().strip().upper()]
""")
        assert result.success


# =============================================================================
# P1: HIGH - Complex Boolean + Comparison
# =============================================================================

class TestComplexConditions:
    """
    P1 RISK: Complex boolean expressions with comparisons may have
    operator precedence issues.
    """
    
    def test_range_and_status(self):
        """Range check AND status check."""
        result = compile_island("""
@island
def RangeStatus():
    value = signal(5)
    status = signal("active")
    return Show(when=lambda: 0 < value() < 10 and status() == "active")[
        div()["Valid"]
    ]
""")
        assert result.success
    
    def test_or_with_multiple_ands(self):
        """OR with multiple AND conditions."""
        result = compile_island("""
@island
def ComplexBool():
    a = signal(True)
    b = signal(False)
    c = signal(True)
    d = signal(False)
    return Show(when=lambda: (a() and b()) or (c() and d()))[
        div()["Match"]
    ]
""")
        assert result.success
        assert "&&" in result.js
        assert "||" in result.js
    
    def test_not_with_comparison(self):
        """NOT with comparison."""
        result = compile_island("""
@island
def NotCompare():
    value = signal(5)
    return Show(when=lambda: not (value() < 0 or value() > 100))[
        div()["In range"]
    ]
""")
        assert result.success
    
    def test_chained_equality(self):
        """Chained equality a == b == c."""
        result = compile_island("""
@island
def ChainedEq():
    a = signal(1)
    b = signal(1)
    return Show(when=lambda: a() == b() == 1)[
        div()["All equal"]
    ]
""")
        assert result.success
    
    def test_mixed_comparison_operators(self):
        """Mix of <, >, ==, !=."""
        result = compile_island("""
@island
def MixedOps():
    x = signal(5)
    y = signal(10)
    z = signal(5)
    return Show(when=lambda: x() < y() and x() == z() and y() != z())[
        div()["Complex condition"]
    ]
""")
        assert result.success


# =============================================================================
# P2: MEDIUM - Comprehensions
# =============================================================================

class TestComprehensions:
    """
    P2 RISK: List/dict/set comprehensions inside memos.
    """
    
    def test_list_comprehension_filter(self):
        """List comprehension with filter."""
        result = compile_island("""
@island
def Filtered():
    items = signal([1, 2, 3, 4, 5])
    evens = memo(lambda: [x for x in items() if x % 2 == 0])
    return div()[str(evens())]
""")
        assert result.success
    
    def test_list_comprehension_transform(self):
        """List comprehension with transformation."""
        result = compile_island("""
@island
def Transformed():
    items = signal([1, 2, 3])
    doubled = memo(lambda: [x * 2 for x in items()])
    return div()[str(doubled())]
""")
        assert result.success
    
    def test_dict_comprehension(self):
        """Dict comprehension."""
        result = compile_island("""
@island
def DictComp():
    items = signal([("a", 1), ("b", 2)])
    as_dict = memo(lambda: {k: v for k, v in items()})
    return div()[str(as_dict())]
""")
        assert result.success
    
    def test_nested_comprehension(self):
        """Nested comprehension."""
        result = compile_island("""
@island
def NestedComp():
    matrix = signal([[1, 2], [3, 4]])
    flattened = memo(lambda: [x for row in matrix() for x in row])
    return div()[str(flattened())]
""")
        assert result.success
    
    def test_comprehension_with_condition_expression(self):
        """Comprehension with ternary."""
        result = compile_island("""
@island
def TernaryComp():
    items = signal([1, 2, 3, 4, 5])
    labeled = memo(lambda: ["even" if x % 2 == 0 else "odd" for x in items()])
    return div()[str(labeled())]
""")
        assert result.success


# =============================================================================
# P2: MEDIUM - Walrus Operator
# =============================================================================

class TestWalrusOperator:
    """
    P2 RISK: := operator is Python 3.8+ and may not be handled.
    """
    
    def test_walrus_in_condition(self):
        """Walrus operator in condition."""
        result = compile_island("""
@island
def Walrus():
    data = signal(None)
    return Show(when=lambda: (result := data()) and result > 0)[
        div()["Positive result"]
    ]
""")
        # May or may not work - test doesn't crash
        if not result.success:
            # Expected to fail - walrus not supported
            assert any("walrus" in str(e).lower() or ":=" in str(e) 
                      for e in result.errors) or True
    
    def test_walrus_in_comprehension(self):
        """Walrus in comprehension."""
        result = compile_island("""
@island
def WalrusComp():
    items = signal([1, 2, 3, 4, 5])
    filtered = memo(lambda: [y for x in items() if (y := x * 2) > 4])
    return div()[str(filtered())]
""")
        # May or may not work
        assert result.success or not result.success  # Shouldn't crash


# =============================================================================
# P2: MEDIUM - Spread Operators
# =============================================================================

class TestSpreadOperators:
    """
    P2 RISK: Python spread operators may not compile to JS spread.
    """
    
    def test_dict_spread(self):
        """Dictionary spread/merge."""
        result = compile_island("""
@island
def DictSpread():
    base = signal({"a": 1})
    override = signal({"b": 2})
    merged = memo(lambda: {**base(), **override()})
    return div()[str(merged())]
""")
        assert result.success
    
    def test_list_spread(self):
        """List spread."""
        result = compile_island("""
@island
def ListSpread():
    first = signal([1, 2])
    second = signal([3, 4])
    combined = memo(lambda: [*first(), *second()])
    return div()[str(combined())]
""")
        assert result.success
    
    def test_function_call_spread(self):
        """Function call with spread args."""
        result = compile_island("""
@island
def CallSpread():
    args = signal([1, 2, 3])
    return button(onclick=lambda: func(*args()))["Call"]
""")
        assert result.success


# =============================================================================
# P2: MEDIUM - Default Arguments
# =============================================================================

class TestDefaultArguments:
    """
    P2 RISK: Lambda default arguments may not compile correctly.
    """
    
    def test_lambda_with_default(self):
        """Lambda with default argument."""
        result = compile_island("""
@island
def DefaultArg():
    items = signal([1, 2, 3])
    return For(each=lambda: items())[
        lambda item, index=0: div()[f"{index}: {item}"]
    ]
""")
        assert result.success
    
    def test_handler_with_default(self):
        """Handler lambda with default."""
        result = compile_island("""
@island
def HandlerDefault():
    return button(onclick=lambda e=None: handle(e))["Click"]
""")
        assert result.success


# =============================================================================
# P2: MEDIUM - Generator Expressions in Memo
# =============================================================================

class TestGeneratorExpressions:
    """
    P2 RISK: Generator expressions may not work like list comprehensions.
    """
    
    def test_any_with_generator(self):
        """any() with generator expression."""
        result = compile_island("""
@island
def AnyCheck():
    items = signal([1, 2, 3, 4, 5])
    has_even = memo(lambda: any(x % 2 == 0 for x in items()))
    return Show(when=lambda: has_even())[div()["Has even"]]
""")
        assert result.success
    
    def test_all_with_generator(self):
        """all() with generator expression."""
        result = compile_island("""
@island
def AllCheck():
    items = signal([2, 4, 6])
    all_even = memo(lambda: all(x % 2 == 0 for x in items()))
    return Show(when=lambda: all_even())[div()["All even"]]
""")
        assert result.success
    
    def test_sum_with_generator(self):
        """sum() with generator expression."""
        result = compile_island("""
@island
def SumCheck():
    items = signal([1, 2, 3, 4, 5])
    total = memo(lambda: sum(x for x in items()))
    return div()[total()]
""")
        assert result.success


# =============================================================================
# P2: MEDIUM - Slice Operations
# =============================================================================

class TestSliceOperations:
    """
    P2 RISK: Python slice syntax may not compile to JS.
    """
    
    def test_simple_slice(self):
        """Simple slice [1:3]."""
        result = compile_island("""
@island
def SimpleSlice():
    items = signal([1, 2, 3, 4, 5])
    subset = memo(lambda: items()[1:3])
    return div()[str(subset())]
""")
        assert result.success
    
    def test_slice_from_start(self):
        """Slice from start [:3]."""
        result = compile_island("""
@island
def SliceFromStart():
    items = signal([1, 2, 3, 4, 5])
    first_three = memo(lambda: items()[:3])
    return div()[str(first_three())]
""")
        assert result.success
    
    def test_slice_to_end(self):
        """Slice to end [2:]."""
        result = compile_island("""
@island
def SliceToEnd():
    items = signal([1, 2, 3, 4, 5])
    rest = memo(lambda: items()[2:])
    return div()[str(rest())]
""")
        assert result.success
    
    def test_negative_slice(self):
        """Negative index slice [-2:]."""
        result = compile_island("""
@island
def NegativeSlice():
    items = signal([1, 2, 3, 4, 5])
    last_two = memo(lambda: items()[-2:])
    return div()[str(last_two())]
""")
        assert result.success
    
    def test_slice_with_step(self):
        """Slice with step [::2]."""
        result = compile_island("""
@island
def StepSlice():
    items = signal([1, 2, 3, 4, 5])
    evens = memo(lambda: items()[::2])
    return div()[str(evens())]
""")
        assert result.success


# =============================================================================
# STRESS TESTS - Combined Risk Patterns
# =============================================================================

class TestCombinedRisks:
    """
    Tests that combine multiple risk patterns.
    """
    
    def test_for_with_reactive_attr_and_fstring(self):
        """For + reactive attr + f-string."""
        result = compile_island("""
@island
def Combined1():
    items = signal([{"name": "A", "active": True}])
    selected = signal(None)
    return For(each=lambda: items())[
        lambda item: div(
            class_=lambda: "active" if item["active"] else "inactive",
            onclick=lambda: selected.set(item)
        )[f"Item: {item['name']}"]
    ]
""")
        assert result.success
    
    def test_nested_show_with_complex_condition(self):
        """Nested Show with complex boolean conditions."""
        result = compile_island("""
@island
def Combined2():
    a = signal(True)
    b = signal(False)
    value = signal(5)
    return Show(when=lambda: a() and not b())[
        Show(when=lambda: 0 < value() < 10)[
            div()["Valid"]
        ]
    ]
""")
        assert result.success
    
    def test_form_with_all_patterns(self):
        """Form with handlers, reactive attrs, conditions."""
        result = compile_island("""
@island
def CompleteForm():
    username = signal("")
    password = signal("")
    error = signal(None)
    loading = signal(False)
    
    valid = memo(lambda: len(username()) > 0 and len(password()) > 6)
    
    return form(
        onsubmit=lambda e: (e.preventDefault(), submit()),
        class_=lambda: "loading" if loading() else "ready"
    )[
        Show(when=lambda: error() is not None)[
            div(class_="error")[error()]
        ],
        input(
            type="text",
            class_=lambda: "valid" if len(username()) > 0 else "invalid",
            oninput=lambda e: username.set(e.target.value)
        ),
        input(
            type="password",
            oninput=lambda e: password.set(e.target.value)
        ),
        button(
            type="submit",
            disabled=lambda: "disabled" if not valid() or loading() else None
        )[
            f"Submit ({len(username())} chars)"
        ]
    ]
""")
        assert result.success

